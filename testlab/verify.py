"""Independent check of a campaign against the standard's requirements and sequence rules.

The verifier recomputes from the step list and the spec. It does not trust the planner's totals.
"""
from __future__ import annotations

from .spec_check import velocity_m_s
from .standards import get_standard


def _chk(check: str, value, limit, unit: str, ok: bool, req: str | None = None, detail: str = "") -> dict:
    return {"check": check, "value": value, "limit": limit, "unit": unit, "pass": bool(ok), "requirement": req,
            "detail": detail}


def _in(v, rng) -> bool:
    return rng[0] <= float(v) <= rng[1]


def verify_campaign(campaign: dict, spec: dict) -> dict:
    std = get_standard(campaign["standard"])
    steps = campaign["steps"]
    by_test: dict[str, list[dict]] = {}
    for s in steps:
        by_test.setdefault(s["test"], []).append(s)
    checks: list[dict] = []
    mop = float(spec["max_operating_pressure_bar"])
    rated = float(spec["rated_flow_lpm"])

    # 1. coverage: every mandatory requirement has at least one step
    for r in std["requirements"]:
        n = len(by_test.get(r["test"], []))
        checks.append(_chk(f"{r['id']} {r['name']}: planned", n, ">= 1", "steps", n >= 1, r["id"],
                           "" if n else f"No step runs '{r['test']}'"))

    # 2. parameters
    rq = {r["test"]: r for r in std["requirements"]}
    for s in by_test.get("helium_leak", []):
        d = s["params"].get("dwell_min")
        checks.append(_chk(f"R01 Helium dwell ({s['step_id']})", d, "5 to 10", "min", _in(d, rq["helium_leak"]["params"]["dwell_min"]), "R01"))
    for s in by_test.get("pressure_decay", []):
        h = s["params"].get("hold_min")
        checks.append(_chk(f"R02 Pressure decay hold ({s['step_id']})", h, "5 to 30", "min", _in(h, rq["pressure_decay"]["params"]["hold_min"]), "R02"))
    for s in by_test.get("hydrostatic", []):
        p = s["params"]
        ok = p.get("stage1_min", 0) >= 5 and p.get("stage2_min", 0) >= 2 and float(p.get("stage2_factor", 0)) >= 3.0
        checks.append(_chk(f"R03 Hydrostatic stages ({s['step_id']})",
                           f"{p.get('stage1_min')} min @ {mop:g} / {p.get('stage2_min')} min @ {float(p.get('stage2_factor', 0)) * mop:g}",
                           f"5 min @ {mop:g} / 2 min @ {3 * mop:g}", "bar", ok, "R03"))
    for s in by_test.get("burst", []):
        p = s["params"]
        checks.append(_chk(f"R04 Burst ramp rate ({s['step_id']})", p.get("ramp_bar_min"), "1 to 5", "bar/min",
                           _in(p.get("ramp_bar_min", 0), rq["burst"]["params"]["ramp_bar_min"]), "R04"))
    for s in by_test.get("thermal_resistance", []):
        t = s["params"].get("inlet_c")
        checks.append(_chk(f"R05 Thermal inlet temperature ({s['step_id']})", t, "45 +/- 2", "degC",
                           _in(t, rq["thermal_resistance"]["params"]["inlet_c"]), "R05"))
    for s in by_test.get("pressure_drop", []):
        flows = sorted(float(q) for q in s["params"].get("flows_lpm", []))
        checks.append(_chk(f"R06 Pressure drop flow points ({s['step_id']})", len(flows), ">= 6", "points",
                           len(flows) >= 6, "R06"))
        lo = round(100 * flows[0] / rated) if flows else None
        hi = round(100 * flows[-1] / rated) if flows else None
        checks.append(_chk(f"R06 Pressure drop span ({s['step_id']})", f"{lo} to {hi}", "25 to 150", "% rated",
                           bool(flows) and lo <= 25 and hi >= 150, "R06",
                           "" if (flows and lo <= 25 and hi >= 150) else "Span must reach both 25 % and 150 % of rated flow"))
    if "port_inner_diameter_mm" in spec:
        qmax = max([float(q) for s in by_test.get("pressure_drop", []) for q in s["params"].get("flows_lpm", [])]
                   or [1.5 * rated])
        v = velocity_m_s(qmax, float(spec["port_inner_diameter_mm"]))
        checks.append(_chk("R07 Port velocity at highest test flow", round(v, 2), "< 1.5", "m/s", v < 1.5, "R07"))
    for t, rid in (("op_temp_cycling", "R11"), ("non_op_temp_cycling", "R12")):
        for s in by_test.get(t, []):
            d = float(s["params"].get("dwell_h", 0))
            checks.append(_chk(f"{rid} Cycling dwell ({s['step_id']})", d, ">= 72", "h each", d >= 72, rid))
    for s in by_test.get("salt_spray", []):
        h = float(s["params"].get("hours", 0))
        checks.append(_chk(f"R15 Salt spray duration ({s['step_id']})", h, ">= 8", "h", h >= 8, "R15"))
    for s in by_test.get("humidity", []):
        h = float(s["params"].get("hours_each", 0))
        checks.append(_chk(f"R17 Humidity dwells ({s['step_id']})", h, ">= 16", "h each", h >= 16, "R17"))

    # 3. sequence rules
    seq = campaign["sample_sequences"]
    step_by_id = {s["step_id"]: s for s in steps}
    for s in by_test.get("non_op_temp_cycling", []):
        order = [step_by_id[i]["test"] for i in seq[s["sample_id"]]]
        k = seq[s["sample_id"]].index(s["step_id"])
        before, after = "helium_leak" in order[:k], "helium_leak" in order[k + 1:]
        missing = [w for w, ok in (("before", before), ("after", after)) if not ok]
        checks.append(_chk(f"SEQ-1 Helium leak brackets shipping cycling on {s['sample_id']}",
                           "both" if not missing else "missing " + " and ".join(missing), "before and after", "",
                           not missing, "R12", "" if not missing else
                           f"Add a helium leak test {' and '.join(missing)} {s['step_id']} on {s['sample_id']}"))
    for s in steps:
        if s["destructive"]:
            later = seq[s["sample_id"]][seq[s["sample_id"]].index(s["step_id"]) + 1:]
            checks.append(_chk(f"SEQ-2 (lab rule) {s['name']} is last on {s['sample_id']}", len(later), "0", "tests after",
                               not later, s["requirement"], "" if not later else
                               f"{s['step_id']} destroys {s['sample_id']} but {', '.join(later)} follow it"))
    supplied = int(spec["samples"])
    checks.append(_chk("SEQ-3 (lab rule) Samples used", len(seq), f"<= {supplied}", "samples", len(seq) <= supplied))

    failures = [c for c in checks if not c["pass"]]
    partner = [s for s in steps if s["where"] == "partner"]
    return {
        "standard": f"{std['id']}: {std['title']}",
        "provenance": std["provenance"],
        "checks": checks, "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
        "coverage": {"covered": len({s['requirement'] for s in steps if s['requirement']}),
                     "total": len(std["requirements"])},
        "notes": [f"{len(partner)} steps need partner labs that are not yet contracted: "
                  + ", ".join(sorted({s['resource'] for s in partner}))] if partner else [],
    }
