"""Lab scheduler invariants: capacity, sample sequence, supervised cobot handling, partner transit."""
from datetime import date, datetime, timedelta

import pytest

from agents.planner import first_plan, revise
from app.demo_specs import demo_specs
from factory.scheduler import SUPERVISED, METROLOGY, schedule, windowed_slot
from testlab.campaign import build_campaign
from testlab.methods import RESOURCES
from testlab.procedure import plan_procedure
from testlab.spec_check import validate_spec
from testlab.verify import verify_campaign

RES = [{"id": r[0], "station": r[2]} for r in RESOURCES]
MONDAY = datetime(2026, 11, 16, 9, 0)


def _ops():
    spec = validate_spec(demo_specs()["cp1400"]["spec"])["normalized_spec"]
    c1 = build_campaign({"steps": first_plan(spec)}, spec, "OCP-CP-1.0")
    steps, _ = revise(first_plan(spec), verify_campaign(c1, spec)["failures"], spec)
    return plan_procedure(build_campaign({"steps": steps}, spec, "OCP-CP-1.0"))["operations"]


def _iv(b):
    return datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])


def test_windowed_slot_skips_busy_night_and_weekend():
    busy = [(MONDAY.replace(hour=6), MONDAY.replace(hour=21, minute=50))]
    assert windowed_slot(busy, MONDAY, 12, SUPERVISED, False) == datetime(2026, 11, 17, 6)
    fri_late = datetime(2026, 11, 20, 21, 55)
    assert windowed_slot([], fri_late, 12, SUPERVISED, False).weekday() == 0
    assert windowed_slot([], fri_late, 12, SUPERVISED, True).weekday() == 5


def test_schedule_invariants():
    existing = [{"machine_id": "FLOW-1", "start": MONDAY.replace(hour=14).isoformat(),
                 "end": (MONDAY + timedelta(days=1)).replace(hour=10).isoformat()}]
    ops = _ops()
    r = schedule(ops, RES, existing, MONDAY, date(2027, 3, 1))
    bk = r["operations"]
    # no overlaps on any resource, including the existing booking
    for res in {b["machine_id"] for b in bk}:
        iv = sorted([_iv(b) for b in bk if b["machine_id"] == res] + [_iv(b) for b in existing if b["machine_id"] == res])
        for (s0, e0), (s1, e1) in zip(iv, iv[1:]):
            assert e0 <= s1, res
    # cobot handling always inside the supervised window on a weekday
    for b in bk:
        if b["machine_id"] == "COBOT-1":
            s, e = _iv(b)
            assert s.weekday() < 5 and SUPERVISED[0] <= s.hour and e <= s.replace(hour=SUPERVISED[1], minute=0)
        if b["machine_id"] == "CMM-UNI":
            s, e = _iv(b)
            assert s.weekday() < 5 and s.hour >= METROLOGY[0] and e <= s.replace(hour=METROLOGY[1], minute=0)
    # each sample's tests run in order and never overlap
    tests = [b for b in bk if b["step"] in ("test", "partner")]
    for sid in {b["sample_id"] for b in tests}:
        seq = [o["step_id"] for o in ops if o["sample_id"] == sid]
        got = sorted((b for b in tests if b["sample_id"] == sid), key=lambda b: b["start"])
        assert [b["step_id"] for b in got] == seq
        for a, b in zip(got, got[1:]):
            assert a["end"] <= b["start"]
    # partner work leaves at least 2 working days of transit before it starts
    first_partner = min(datetime.fromisoformat(b["start"]) for b in bk if b["step"] == "partner")
    assert (first_partner - MONDAY).days >= 2
    assert r["on_time"] and date.fromisoformat(r["report_due"]).weekday() < 5


def test_late_deadline_flagged():
    r = schedule(_ops(), RES, [], MONDAY, date(2026, 11, 30))
    assert not r["on_time"] and r["slack_days"] < 0


def test_saturday_handling_never_later():
    a = schedule(_ops(), RES, [], MONDAY, date(2027, 3, 1))
    b = schedule(_ops(), RES, [], MONDAY, date(2027, 3, 1), allow_saturday=True)
    assert b["last_test_end"] <= a["last_test_end"]


def test_db_roundtrip(tmp_path, monkeypatch):
    import factory.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(db, "_conn", None)
    db.init()
    assert {m["id"] for m in db.machines()} == {r["id"] for r in RES}
    assert all("demo data" in b["label"] or b["kind"] == "downtime" for b in db.bookings())
    db.create_job("J1", "t", {"a": 1}, "scripted")
    db.add_event("J1", "x", "intake", {"k": 2})
    assert db.get_events("J1")[0]["payload"] == {"k": 2}
    db.replace_tentative("J1", [{"machine_id": "LEAK-1", "label": "x", "start": "2026-01-01T06:00:00",
                                 "end": "2026-01-01T07:00:00"}])
    assert any(b["kind"] == "tentative" for b in db.bookings(include_tentative_for="J1"))
    assert db.commit_tentative("J1") == 1


@pytest.mark.parametrize("h", range(0, 14 * 24, 7))
def test_demo_schedule_robust_to_wall_clock(tmp_path, monkeypatch, h):
    """The demo runs on an unknown day and time: every start over two weeks must meet the demo deadline."""
    import factory.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "w.db")
    monkeypatch.setattr(db, "_conn", None)
    db.init(reseed=False)
    now = datetime(2026, 11, 16) + timedelta(hours=h)
    db.seed_factory(now)
    deadline = (now + timedelta(days=56)).date()
    r = schedule(_ops(), db.machines(), db.busy_for("X"), now, deadline)
    assert r["on_time"], (now, r["report_due"])
