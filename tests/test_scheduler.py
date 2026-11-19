from datetime import date, datetime, timedelta

import pytest

from engineering.process import plan_process
from factory.scheduler import earliest_slot, schedule, SHIFT_START_H, SHIFT_END_H

MACHINES = [
    {"id": "CNC-1", "station": "CNC", "saturday": 1},
    {"id": "CNC-2", "station": "CNC", "saturday": 1},
    {"id": "FSW-1", "station": "FSW", "saturday": 0},
    {"id": "LEAK-1", "station": "LEAK", "saturday": 0},
]
MICRO = dict(topology="straight_microchannel", channel_width_mm=0.25, fin_thickness_mm=0.2, channel_depth_mm=3.0)
MONDAY = datetime(2026, 11, 16, 9, 0)


def _plan(qty=40):
    return plan_process(MICRO, qty)["operations"]


def test_earliest_slot_skips_busy_and_night():
    busy = [(MONDAY.replace(hour=6), MONDAY.replace(hour=20))]
    s = earliest_slot(busy, MONDAY, 180, saturday=False)
    assert s == datetime(2026, 11, 17, SHIFT_START_H)  # 20:00 + 3 h overruns 22:00 -> next morning


def test_earliest_slot_skips_weekend():
    fri_late = datetime(2026, 11, 20, 21, 0)
    assert earliest_slot([], fri_late, 120, saturday=False).weekday() == 0
    assert earliest_slot([], fri_late, 120, saturday=True).weekday() == 5


def test_schedule_respects_capacity_shifts_and_routing():
    existing = [{"machine_id": "FSW-1", "start": (MONDAY + timedelta(days=1)).replace(hour=6).isoformat(),
                 "end": (MONDAY + timedelta(days=1)).replace(hour=18).isoformat()}]
    r = schedule(_plan(), 40, MACHINES, existing, MONDAY, date(2026, 12, 18))
    ops = r["operations"]
    # no overlaps on any machine, including the existing booking
    for mid in {o["machine_id"] for o in ops}:
        iv = sorted([(datetime.fromisoformat(o["start"]), datetime.fromisoformat(o["end"])) for o in ops
                     if o["machine_id"] == mid]
                    + [(datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])) for b in existing
                       if b["machine_id"] == mid])
        for (s0, e0), (s1, e1) in zip(iv, iv[1:]):
            assert e0 <= s1
    for o in ops:
        s, e = datetime.fromisoformat(o["start"]), datetime.fromisoformat(o["end"])
        assert s.hour >= SHIFT_START_H and (e.hour < SHIFT_END_H or (e.hour == SHIFT_END_H and e.minute == 0))
        assert s.date() == e.date()
    order = ["machining", "fsw", "post_weld", "leak_test"]
    for lot in range(1, r["lots"] + 1):
        steps = sorted((o for o in ops if o["lot"] == lot), key=lambda o: o["start"])
        assert [o["step"] for o in steps] == order
        for a, b in zip(steps, steps[1:]):
            assert a["end"] <= b["start"]
    assert {o["machine_id"] for o in ops if o["step"] == "machining"} == {"CNC-1", "CNC-2"}
    assert r["on_time"] and r["slack_days"] >= 0


def test_late_deadline_flagged():
    r = schedule(_plan(), 40, MACHINES, [], MONDAY, date(2026, 11, 18))
    assert not r["on_time"] and r["slack_days"] < 0


def test_saturday_overtime_never_later():
    a = schedule(_plan(200), 200, MACHINES, [], MONDAY, date(2027, 1, 30))
    b = schedule(_plan(200), 200, MACHINES, [], MONDAY, date(2027, 1, 30), allow_saturday=True)
    assert b["production_complete"] <= a["production_complete"]


def test_db_roundtrip(tmp_path, monkeypatch):
    import factory.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(db, "_conn", None)
    db.init()
    assert len(db.machines()) == 4
    assert any(b["kind"] == "downtime" for b in db.bookings())
    db.create_job("J1", "t", {"a": 1}, "scripted")
    db.add_event("J1", "x", "intake", {"k": 2})
    assert db.get_events("J1")[0]["payload"] == {"k": 2}
    db.replace_tentative("J1", [{"machine_id": "CNC-1", "label": "x", "start": "2026-01-01T06:00:00",
                                 "end": "2026-01-01T07:00:00"}])
    assert any(b["kind"] == "tentative" for b in db.bookings(include_tentative_for="J1"))
    assert not any(b["kind"] == "tentative" for b in db.bookings())
    assert db.commit_tentative("J1") == 1


def test_demo_schedule_robust_to_wall_clock(tmp_path, monkeypatch):
    """The demo is run on an unknown day/time: every start time over two weeks must deliver on time."""
    import factory.db as db
    from app.demo_specs import demo_specs
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "w.db")
    monkeypatch.setattr(db, "_conn", None)
    db.init(reseed=False)
    spec = demo_specs()["hx1200"]["spec"]
    ops = plan_process(dict(MICRO), spec["quantity"])["operations"]
    start = datetime(2026, 11, 16, 0, 0)
    for h in range(0, 14 * 24, 5):
        now = start + timedelta(hours=h)
        db.seed_factory(now)
        r = schedule(ops, spec["quantity"], db.machines(), db.busy_for("X"), now, (now + timedelta(days=14)).date())
        assert r["on_time"], (now, r["delivery_date"])
        assert date.fromisoformat(r["delivery_date"]).weekday() < 5
