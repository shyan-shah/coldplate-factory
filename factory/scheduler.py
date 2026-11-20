"""Deterministic finite-capacity scheduler for the test lab.

Rigs run unattended around the clock. The cobot loads, connects, disconnects and unloads parts only inside
the supervised window (06:00 to 22:00 Monday to Friday, optionally Saturday). A part that finishes overnight
waits on its rig until the cobot can unload it. Each sample's tests run in sequence; different samples run
in parallel. Partner-lab tests add shipping both ways. University metrology runs 09:00 to 17:00 on weekdays.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

SUPERVISED = (6, 22)
METROLOGY = (9, 17)
RELEASE_LAG_H = 4.0                 # kit prep after the engineer releases the campaign
REPORT_WORKING_DAYS = 5             # report within 5 working days of the last test (pilot promise)


def _working(d: datetime, saturday: bool) -> bool:
    return d.weekday() < 5 or (d.weekday() == 5 and saturday)


def _window(t: datetime, hours: tuple[int, int], saturday: bool) -> tuple[datetime, datetime]:
    day = t.replace(hour=0, minute=0, second=0, microsecond=0)
    while True:
        if _working(day, saturday):
            ws, we = day.replace(hour=hours[0]), day.replace(hour=hours[1])
            if t < we:
                return max(ws, t), we
        day += timedelta(days=1)
        t = day


def windowed_slot(busy: list[tuple[datetime, datetime]], ready: datetime, minutes: float,
                  hours: tuple[int, int], saturday: bool) -> datetime:
    """Earliest start >= ready that fits in one working window and avoids `busy`."""
    if minutes > (hours[1] - hours[0]) * 60:
        raise ValueError(f"{minutes:.0f} min cannot fit in one {hours} window")
    dur, t = timedelta(minutes=minutes), ready
    for _ in range(20000):
        start, wend = _window(t, hours, saturday)
        end = start + dur
        if end > wend:
            t = wend
            continue
        clash = next(((s, e) for s, e in busy if s < end and e > start), None)
        if clash:
            t = clash[1]
            continue
        return start
    raise RuntimeError("no slot found")


def free_from(busy: list[tuple[datetime, datetime]], start: datetime, end: datetime) -> datetime | None:
    """None if [start, end) is free, else the end of the first clash."""
    clash = next(((s, e) for s, e in busy if s < end and e > start), None)
    return None if clash is None else clash[1]


def add_working_days(t: datetime, n: int) -> datetime:
    d = t
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def schedule(operations: list[dict], resources: list[dict], bookings: list[dict], now: datetime, deadline: date,
             allow_saturday: bool = False) -> dict:
    busy: dict[str, list[tuple[datetime, datetime]]] = {r["id"]: [] for r in resources}
    for b in bookings:
        if b["machine_id"] in busy:
            busy[b["machine_id"]].append((datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])))
    for v in busy.values():
        v.sort()

    release = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1 + RELEASE_LAG_H)
    queues: dict[str, list[dict]] = {}
    for op in operations:
        queues.setdefault(op["sample_id"], []).append(op)
    ready = {sid: release for sid in queues}
    booked: list[dict] = []
    unattended_min = 0.0

    def put(res: str, s: datetime, e: datetime, op: dict, label: str, step: str) -> None:
        busy[res].append((s, e))
        busy[res].sort()
        booked.append({"machine_id": res, "step_id": op["step_id"], "sample_id": op["sample_id"], "step": step,
                       "label": label, "start": s.isoformat(), "end": e.isoformat(),
                       "minutes": round((e - s).total_seconds() / 60, 1)})

    while any(queues.values()):
        sid = min((k for k, q in queues.items() if q), key=lambda k: (ready[k], k))
        op = queues[sid].pop(0)
        res, t0 = op["resource"], ready[sid]
        tag = f"{op['step_id']} {op['sample_id']} {op['name']}"
        if op["kind"] in ("bench", "hired"):
            hin, hout, run = op["handling_in_min"], op["handling_out_min"], op["run_min"]
            t = t0
            for _ in range(5000):
                s = windowed_slot(busy["COBOT-1"], t, hin, SUPERVISED, allow_saturday)
                run_end = s + timedelta(minutes=hin + run)
                u = windowed_slot(busy["COBOT-1"], run_end, hout, SUPERVISED, allow_saturday)
                end = u + timedelta(minutes=hout)
                clash = free_from(busy[res], s, end)
                if clash is None:
                    break
                t = clash
            else:
                raise RuntimeError(f"cannot place {op['step_id']}")
            put("COBOT-1", s, s + timedelta(minutes=hin), op, f"{op['step_id']} load + connect {op['sample_id']}", "handling")
            put(res, s, end, op, tag, "test")
            put("COBOT-1", u, end, op, f"{op['step_id']} disconnect + unload {op['sample_id']}", "handling")
            # unattended rig time outside the supervised window
            cur = s + timedelta(minutes=hin)
            while cur < run_end:
                nxt = min(run_end, cur + timedelta(minutes=30))
                if not (_working(cur, allow_saturday) and SUPERVISED[0] <= cur.hour < SUPERVISED[1]):
                    unattended_min += (nxt - cur).total_seconds() / 60
                cur = nxt
            ready[sid] = end
        elif op["kind"] == "metrology":
            s = windowed_slot(busy[res], t0, op["run_min"], METROLOGY, False)
            end = s + timedelta(minutes=op["run_min"])
            put(res, s, end, op, tag, "test")
            ready[sid] = end
        else:  # partner: ship out, run continuously, ship back
            t = add_working_days(t0, op["transit_working_days"]).replace(hour=9, minute=0, second=0, microsecond=0)
            dur = timedelta(minutes=op["run_min"])
            while (c := free_from(busy[res], t, t + dur)) is not None:
                t = c
            put(res, t, t + dur, op, tag + " (partner)", "partner")
            ready[sid] = add_working_days(t + dur, op["transit_working_days"]).replace(hour=9, minute=0)

    last = max(datetime.fromisoformat(b["end"]) for b in booked)
    report_due = add_working_days(last, REPORT_WORKING_DAYS).date()
    slack = (deadline - report_due).days
    load = {}
    for r in busy:
        mins = sum(b["minutes"] for b in booked if b["machine_id"] == r)
        if mins:
            load[r] = round(mins / 60, 1)
    return {
        "release": release.isoformat(), "last_test_end": last.isoformat(), "report_due": report_due.isoformat(),
        "deadline": deadline.isoformat(), "slack_days": slack, "on_time": slack >= 0,
        "allow_saturday_handling": allow_saturday, "makespan_days": round((last - release).total_seconds() / 86400, 1),
        "unattended_rig_hours": round(unattended_min / 60, 1),
        "operations": booked, "resource_hours": load,
    }
