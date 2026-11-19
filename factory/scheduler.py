"""Deterministic finite-capacity scheduler for the cold plate cell.

Each transfer lot flows: CNC (base + lid) -> deburr -> FSW lid weld -> CNC post-weld skim
-> passivate -> leak test.  Operations are non-preemptive, must fit inside a staffed
shift window, and may not overlap existing bookings or downtime on the machine.
Lots are dispatched in order; the CNC step picks whichever mill finishes it first.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

SHIFT_START_H = 6
SHIFT_END_H = 22
SETUP_MIN = {"CNC": 30.0, "FSW": 20.0, "LEAK": 10.0}
FIRST_ARTICLE_MIN = 45.0          # extra on the first CNC lot (first-article inspection)
RELEASE_LAG_H = 4.0               # CAM post + stock saw-cut after engineer release
FINAL_INSPECTION_WORKING_DAYS = 1
SHIPPING_DAYS = 2                 # business days in transit (ground)
WINDOW_MIN = (SHIFT_END_H - SHIFT_START_H) * 60


def _is_working_day(d: datetime, saturday: bool) -> bool:
    wd = d.weekday()
    return wd < 5 or (wd == 5 and saturday)


def _window(t: datetime, saturday: bool) -> tuple[datetime, datetime]:
    """Working window containing t, or the next one after t."""
    day = t.replace(hour=0, minute=0, second=0, microsecond=0)
    while True:
        if _is_working_day(day, saturday):
            ws, we = day.replace(hour=SHIFT_START_H), day.replace(hour=SHIFT_END_H)
            if t < we:
                return max(ws, t), we
        day += timedelta(days=1)
        t = day


def earliest_slot(busy: list[tuple[datetime, datetime]], ready: datetime, minutes: float,
                  saturday: bool) -> datetime:
    if minutes > WINDOW_MIN:
        raise ValueError(f"operation of {minutes:.0f} min cannot fit in one {WINDOW_MIN} min shift window")
    dur = timedelta(minutes=minutes)
    t = ready
    for _ in range(10000):
        start, wend = _window(t, saturday)
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


def _add_working_days(t: datetime, n: int, saturday: bool = False) -> datetime:
    d = t
    while n > 0:
        d += timedelta(days=1)
        if _is_working_day(d, saturday):
            n -= 1
    return d.replace(hour=SHIFT_END_H, minute=0, second=0, microsecond=0)


def split_minutes(operations: list[dict]) -> dict:
    """Per-part minutes for each routed step from a process plan's operation list."""
    pre = sum(o["minutes"] for o in operations if o["station"] == "CNC" and o["seq"] < 60)
    post = sum(o["minutes"] for o in operations if o["station"] == "CNC" and o["seq"] > 60)
    fsw = sum(o["minutes"] for o in operations if o["station"] == "FSW")
    leak = sum(o["minutes"] for o in operations if o["station"] == "LEAK")
    bench_pre = sum(o["minutes"] for o in operations if o["station"] == "BENCH" and o["seq"] < 60)
    bench_post = sum(o["minutes"] for o in operations if o["station"] == "BENCH" and o["seq"] > 60)
    return {"cnc_pre": pre, "cnc_post": post, "fsw": fsw, "leak": leak,
            "bench_pre": bench_pre, "bench_post": bench_post}


def schedule(operations: list[dict], quantity: int, machines: list[dict], bookings: list[dict],
             now: datetime, deadline: date, lot_size: int = 10, allow_saturday: bool = False) -> dict:
    m = split_minutes(operations)
    # Keep every lot inside one shift window on the longest step.
    max_per_part = max(m["cnc_pre"], m["cnc_post"], m["fsw"], m["leak"])
    max_lot = max(1, int((WINDOW_MIN - SETUP_MIN["CNC"] - FIRST_ARTICLE_MIN) // max_per_part))
    lot_size = max(1, min(lot_size, max_lot, quantity))
    n_lots = math.ceil(quantity / lot_size)

    by_station: dict[str, list[dict]] = {}
    for mc in machines:
        by_station.setdefault(mc["station"], []).append(mc)
    busy: dict[str, list[tuple[datetime, datetime]]] = {mc["id"]: [] for mc in machines}
    for b in bookings:
        if b["machine_id"] in busy:
            busy[b["machine_id"]].append((datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])))
    for v in busy.values():
        v.sort()

    release = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1 + RELEASE_LAG_H))
    ops: list[dict] = []

    def book(station: str, ready: datetime, minutes: float, label: str, lot: int, step: str) -> datetime:
        best = None
        for mc in by_station[station]:
            sat = allow_saturday and bool(mc["saturday"])
            s = earliest_slot(busy[mc["id"]], ready, minutes, sat)
            e = s + timedelta(minutes=minutes)
            if best is None or e < best[2]:
                best = (mc["id"], s, e)
        mid, s, e = best
        busy[mid].append((s, e))
        busy[mid].sort()
        ops.append({"machine_id": mid, "lot": lot, "step": step, "label": label,
                    "start": s.isoformat(), "end": e.isoformat(), "minutes": round(minutes, 1)})
        return e

    lots_done: list[datetime] = []
    for i in range(n_lots):
        q = min(lot_size, quantity - i * lot_size)
        lot = i + 1
        fa = FIRST_ARTICLE_MIN if i == 0 else 0.0
        t = book("CNC", release, SETUP_MIN["CNC"] + fa + q * m["cnc_pre"],
                 f"Lot {lot} ({q} pcs) base + lid machining", lot, "machining")
        t += timedelta(minutes=q * m["bench_pre"])
        t = book("FSW", t, SETUP_MIN["FSW"] + q * m["fsw"], f"Lot {lot} lid FSW", lot, "fsw")
        t = book("CNC", t, SETUP_MIN["CNC"] + q * m["cnc_post"], f"Lot {lot} post-weld skim + holes", lot, "post_weld")
        t += timedelta(minutes=q * m["bench_post"])
        t = book("LEAK", t, SETUP_MIN["LEAK"] + q * m["leak"], f"Lot {lot} proof + leak test", lot, "leak_test")
        lots_done.append(t)

    complete = max(lots_done)
    ship = _add_working_days(complete, FINAL_INSPECTION_WORKING_DAYS)
    delivery = _add_working_days(ship, SHIPPING_DAYS).date()
    slack = (deadline - delivery).days
    util = {}
    span_h = (complete - release).total_seconds() / 3600
    for mid in busy:
        mins = sum(o["minutes"] for o in ops if o["machine_id"] == mid)
        util[mid] = {"job_hours": round(mins / 60, 2)}
    return {
        "release": release.isoformat(),
        "production_complete": complete.isoformat(),
        "ship_date": ship.date().isoformat(),
        "delivery_date": delivery.isoformat(),
        "deadline": deadline.isoformat(),
        "slack_days": slack,
        "on_time": slack >= 0,
        "lot_size": lot_size,
        "lots": n_lots,
        "allow_saturday_overtime": allow_saturday,
        "makespan_hours": round(span_h, 1),
        "per_part_minutes": {k: round(v, 2) for k, v in m.items()},
        "operations": ops,
        "machine_load": util,
    }
