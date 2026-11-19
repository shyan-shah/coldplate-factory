"""End-to-end scripted pipeline: the demo case must reach the approval gate after a real rejection loop."""
import asyncio

import pytest

from agents.core import JobContext
from agents.orchestrator import Orchestrator
from app.demo_specs import demo_specs


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    import factory.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "p.db")
    monkeypatch.setattr(db, "_conn", None)
    monkeypatch.setenv("SCRIPTED_STEP_DELAY", "0")
    db.init()
    return db


def _run(db, key):
    events = []

    async def emit(t, a, p, persist=True):
        events.append((t, a, p))
    spec = demo_specs()[key]["spec"]
    db.create_job("JT", "t", spec, "scripted")
    ctx = JobContext(job_id="JT", raw_spec=spec, emit_fn=emit, mode="scripted")
    asyncio.run(Orchestrator(ctx).run())
    return ctx, events


def test_demo_case_reaches_gate_with_rejection(fresh_db):
    ctx, events = _run(fresh_db, "hx1200")
    types = [e[0] for e in events]
    assert "error" not in types, [e for e in events if e[0] == "error"]
    assert types[-1] == "gate"
    assert types.count("rejection") >= 1
    pkg = events[-1][2]["package"]
    assert pkg["t_case_c"] <= pkg["limits"]["max_case_c"]
    assert pkg["worst_case"]["t_case_c"] <= pkg["limits"]["max_case_c"]
    assert pkg["worst_case"]["dp_kpa"] <= pkg["limits"]["max_dp_kpa"]
    assert pkg["slack_days"] >= 0
    # every agent ran, in order
    started = [e[1] for e in events if e[0] == "agent_started"]
    assert started[0] == "intake" and started[-1] == "qa"
    assert {"thermal_design", "verification", "process_planning", "scheduling"} <= set(started)
    assert any(b["kind"] == "tentative" for b in fresh_db.bookings(include_tentative_for="JT"))


def test_bad_spec_stops_at_intake(fresh_db):
    ctx, events = _run(fresh_db, "bad")
    assert events[-1][0] == "job_status" and events[-1][2]["status"] == "needs_clarification"
    assert not any(e[0] == "agent_started" and e[1] == "thermal_design" for e in events)
