"""Test-lab engine: intake checks, campaign building, verification rules, procedure and report."""
from datetime import date, timedelta

import pytest

from agents.planner import first_plan, revise
from app.demo_specs import demo_specs
from testlab.campaign import build_campaign
from testlab.procedure import plan_procedure
from testlab.report import build_report, report_markdown, simulate_results, SIM_BANNER
from testlab.spec_check import validate_spec, velocity_m_s
from testlab.standards import OCP_CP, STANDARDS
from testlab.verify import verify_campaign


@pytest.fixture
def spec():
    return validate_spec(demo_specs()["cp1400"]["spec"])["normalized_spec"]


def failing(v):
    return {c["check"].split(" (")[0] for c in v["failures"]}


def test_demo_spec_accepted_with_derived_figures():
    r = validate_spec(demo_specs()["cp1400"]["spec"])
    assert r["accepted"] and r["plannable_standards"] == ["OCP-CP-1.0"]
    assert r["derived"]["hydrostatic_stage2_bar"] == 15.0
    assert r["derived"]["dp_flow_span_lpm"] == [0.375, 2.25]
    assert r["derived"]["port_velocity_at_150pct_m_s"] == pytest.approx(1.326, abs=1e-3)


def test_bad_request_blocked_for_real_reasons():
    r = validate_spec(demo_specs()["bad"]["spec"])
    msgs = " ".join(i["message"] for i in r["issues"] if i["severity"] == "error")
    assert not r["accepted"]
    assert "UL-4501" in msgs and "cannot plan" in msgs.lower()
    assert "Maximum operating pressure" in msgs
    assert "At least 2 samples" not in msgs  # no plannable standard, so no sample recommendation is made


def test_past_deadline_and_unknown_standard_are_errors():
    s = {**demo_specs()["cp1400"]["spec"], "deadline": (date.today() - timedelta(days=1)).isoformat(),
         "target_standards": "ISO-9999"}
    fields = {i["field"] for i in validate_spec(s)["issues"] if i["severity"] == "error"}
    assert {"deadline", "target_standards"} <= fields


def test_velocity_hand_calc():
    # 2.25 L/min through a 6 mm bore: 3.75e-5 m3/s / 2.827e-5 m2 = 1.326 m/s
    assert velocity_m_s(2.25, 6.0) == pytest.approx(1.3263, abs=1e-4)


def test_ocp_catalogue_shape():
    assert len(OCP_CP["requirements"]) == 18
    assert {r["id"] for r in OCP_CP["requirements"]} == {f"R{i:02d}" for i in range(1, 19)}
    assert not STANDARDS["UL-4501"]["available"]


def test_first_plan_fails_for_three_real_reasons(spec):
    c = build_campaign({"label": "v1", "steps": first_plan(spec)}, spec, "OCP-CP-1.0")
    v = verify_campaign(c, spec)
    assert v["verdict"] == "FAIL" and v["coverage"] == {"covered": 18, "total": 18}
    assert failing(v) == {"R06 Pressure drop flow points", "R06 Pressure drop span",
                          "SEQ-1 Helium leak brackets shipping cycling on S2", "SEQ-2 Burst is last on S3"}


def test_revision_clears_every_finding(spec):
    c1 = build_campaign({"label": "v1", "steps": first_plan(spec)}, spec, "OCP-CP-1.0")
    steps, fixed = revise(first_plan(spec), verify_campaign(c1, spec)["failures"], spec)
    c2 = build_campaign({"label": "v2", "steps": steps}, spec, "OCP-CP-1.0")
    v2 = verify_campaign(c2, spec)
    assert v2["verdict"] == "PASS", failing(v2)
    assert set(fixed) == {"R06", "SEQ-1", "SEQ-2"}
    seq = c2["sample_sequences"]
    burst = next(s for s in c2["steps"] if s["test"] == "burst")
    assert seq[burst["sample_id"]] == [burst["step_id"]]          # dedicated sample
    assert len(seq) == spec["samples"]


def test_parameter_and_sample_rules(spec):
    steps = [{"sample_id": "S1", "test": "pressure_decay", "params": {"hold_min": 2}},
             {"sample_id": "S2", "test": "helium_leak", "params": {"dwell_min": 20}},
             {"sample_id": "S3", "test": "hydrostatic", "params": {"stage2_factor": 1.5}},
             {"sample_id": "S4", "test": "burst", "params": {"ramp_bar_min": 10, "target_bar": 12}},
             {"sample_id": "S5", "test": "thermal_resistance", "params": {"inlet_c": 25}},
             {"sample_id": "S6", "test": "salt_spray", "params": {"hours": 4}}]
    v = verify_campaign(build_campaign({"steps": steps}, spec, "OCP-CP-1.0"), spec)
    f = failing(v)
    for name in ("R02 Pressure decay hold", "R01 Helium dwell", "R03 Hydrostatic stages", "R04 Burst ramp rate",
                 "R04 Burst target above 3x MOP", "R05 Thermal inlet temperature", "R15 Salt spray duration",
                 "SEQ-3 Samples used", "R06 Pressure drop: planned"):
        assert name in f, name


def test_unknown_test_rejected(spec):
    with pytest.raises(KeyError):
        build_campaign({"steps": [{"sample_id": "S1", "test": "levitation"}]}, spec, "OCP-CP-1.0")


def test_procedure_cobot_only_on_bench(spec):
    c1 = build_campaign({"steps": first_plan(spec)}, spec, "OCP-CP-1.0")
    p = plan_procedure(c1)
    for o in p["operations"]:
        if o["kind"] in ("bench", "hired"):
            assert o["handling_in_min"] > 0 and o["cobot_tasks"]
        else:
            assert o["handling_in_min"] == 0 and not o["cobot_tasks"]
        if o["kind"] == "partner":
            assert o["transit_working_days"] == 2
    assert p["cost_estimate_gbp"]["total_excl_partner"] == pytest.approx(
        sum(v for k, v in p["cost_estimate_gbp"].items() if k != "total_excl_partner"), abs=0.05)


def test_report_flags_simulated_failure_and_traces_everything(spec):
    c1 = build_campaign({"steps": first_plan(spec)}, spec, "OCP-CP-1.0")
    steps, _ = revise(first_plan(spec), verify_campaign(c1, spec)["failures"], spec)
    c = build_campaign({"steps": steps}, spec, "OCP-CP-1.0")
    res = simulate_results(c, spec)
    assert all(r["simulated"] for r in res)
    assert all(r["status"] == "PENDING" and r["value"] is None for r in res if r["test"] in
               ("shock", "vibration", "salt_spray", "humidity", "fluid_compatibility", "op_temp_cycling"))
    rep = build_report("J", spec, c, verify_campaign(c, spec),
                       {"release": "2026-01-01T09:00", "last_test_end": "2026-02-01T09:00", "report_due": "2026-02-06"}, res)
    assert [f["step_id"] for f in rep["flagged"]] == [next(s["step_id"] for s in c["steps"] if s["test"] == "thermal_resistance")]
    assert all(t["status"] != "NOT PLANNED" for t in rep["traceability"])
    md = report_markdown(rep)
    assert SIM_BANNER in md and "not a certification body" in md and "—" not in md
