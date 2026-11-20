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
    ctx, events = _run(fresh_db, "cp1400")
    types = [e[0] for e in events]
    assert "error" not in types, [e for e in events if e[0] == "error"]
    assert types[-1] == "gate"
    assert types.count("rejection") == 1
    pkg = events[-1][2]["package"]
    assert pkg["coverage"] == {"covered": 18, "total": 18}
    assert pkg["verification_rounds"] == 2 and pkg["campaigns_drafted"] == 2
    assert pkg["samples_used"] <= pkg["samples_supplied"]
    assert pkg["slack_days"] >= 0
    assert pkg["dry_run_counts"]["FAIL"] == 1 and pkg["dry_run_counts"]["PENDING"] >= 1
    started = [e[1] for e in events if e[0] == "agent_started"]
    assert started[0] == "intake" and started[-1] == "report"
    assert {"planner", "verification", "procedure", "scheduling"} <= set(started)
    kinds = {e[2]["kind"] for e in events if e[0] == "artifact"}
    assert {"spec_check", "campaigns", "campaign_selection", "verification", "procedure", "schedule", "report",
            "job_package"} <= kinds
    rep = next(e[2]["data"] for e in events if e[0] == "artifact" and e[2]["kind"] == "report")
    assert "SIMULATED" in rep["markdown"]
    held = fresh_db.bookings(include_tentative_for="JT")
    assert any(b["kind"] == "tentative" and b["machine_id"] == "COBOT-1" for b in held)


def test_bad_request_stops_at_intake(fresh_db):
    ctx, events = _run(fresh_db, "bad")
    assert events[-1][0] == "job_status" and events[-1][2]["status"] == "needs_clarification"
    assert not any(e[0] == "agent_started" and e[1] == "planner" for e in events)
