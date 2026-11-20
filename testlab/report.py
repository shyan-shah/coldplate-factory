"""Qualification report: traceability to the standard, plus a dry run on simulated rigs.

SIMULATED DATA. The v0 rigs are not built. `simulate_results` produces deterministic stand-in values from
the maker's claimed figures so the customer can see the report format and the failure-flagging logic
before any parts ship. Nothing here is a measurement.
"""
from __future__ import annotations

from .spec_check import velocity_m_s
from .standards import get_standard

SIM_BANNER = ("SIMULATED DRY RUN: values come from mock rigs driven by the maker's claimed figures. "
              "They are not measurements. Real results replace them when the campaign runs.")

# Deterministic offsets applied by the mock rigs (fraction of the claimed value).
SIM_DP_OFFSET = 0.04
SIM_RTH_OFFSET = 0.12        # set above the +10 % criterion so the dry run shows a flagged failure


def _r(v, d=3):
    return round(float(v), d)


def simulate_results(campaign: dict, spec: dict) -> list[dict]:
    mop = float(spec["max_operating_pressure_bar"])
    rated = float(spec["rated_flow_lpm"])
    out = []
    for s in campaign["steps"]:
        t, p = s["test"], s["params"]
        base = {"step_id": s["step_id"], "sample_id": s["sample_id"], "test": t, "name": s["name"],
                "requirement": s["requirement"], "acceptance": s["acceptance"], "simulated": True}
        if s["where"] == "partner":
            out.append({**base, "status": "PENDING", "value": None,
                        "note": f"Planned at partner lab {s['resource']} (not contracted). No simulated value."})
            continue
        if t == "pressure_decay":
            out.append({**base, "status": "PASS", "value": f"{_r(0.08 + 0.002 * p.get('hold_min', 15), 3)} % loss"})
        elif t == "helium_leak":
            out.append({**base, "status": "PASS", "value": "below detector threshold (simulated)"})
        elif t == "hydrostatic":
            out.append({**base, "status": "PASS", "value": f"held {3 * mop:g} bar, residual deformation 0.01 mm"})
        elif t == "burst":
            out.append({**base, "status": "REPORT", "value": f"no rupture at {p.get('target_bar')} bar (bench pump limit)",
                        "note": "Acceptance pressure to be confirmed against the specification text."})
        elif t == "pressure_drop":
            claim = spec.get("claimed_dp_kpa_at_rated")
            k = float(claim or 10.0) * (1 + SIM_DP_OFFSET)
            curve = [{"flow_lpm": _r(q, 3), "dp_kpa": _r(k * (float(q) / rated) ** 1.8, 2)} for q in p.get("flows_lpm", [])]
            at_rated = k
            ok = claim is None or abs(at_rated / float(claim) - 1) <= 0.10
            out.append({**base, "status": "PASS" if ok else "FAIL", "value": f"{_r(at_rated, 2)} kPa at rated flow",
                        "curve": curve})
        elif t == "flow_rate":
            qmax = max([float(q) for x in campaign["steps"] if x["test"] == "pressure_drop"
                        for q in x["params"].get("flows_lpm", [])] or [1.5 * rated])
            v = velocity_m_s(qmax, float(spec.get("port_inner_diameter_mm", 8)))
            out.append({**base, "status": "PASS" if v < 1.5 else "FAIL", "value": f"{_r(v, 2)} m/s at {_r(qmax, 2)} L/min"})
        elif t == "thermal_resistance":
            claim = spec.get("claimed_r_th_k_w")
            r = float(claim or 0.02) * (1 + SIM_RTH_OFFSET)
            ok = claim is None or r <= 1.10 * float(claim)
            out.append({**base, "status": "PASS" if ok else "FAIL", "value": f"{_r(r, 4)} K/W at {spec.get('design_heat_load_w')} W",
                        "note": "" if ok else "Above the maker's claim +10 %. Check heater block contact and bond line, "
                                              "then repeat on a second sample before reporting a failure."})
        elif t == "retention_force":
            out.append({**base, "status": "PASS", "value": f"{p.get('force_n')} N held {p.get('hold_s')} s, slip 0.02 mm"})
        elif t == "flatness":
            lim = spec.get("flatness_limit_mm")
            out.append({**base, "status": "PASS" if lim is None or 0.021 <= float(lim) else "FAIL", "value": "0.021 mm"})
        elif t == "stiffness":
            out.append({**base, "status": "REPORT", "value": "0.006 mm deflection at mounting load"})
        elif t == "cleanliness":
            out.append({**base, "status": "PASS", "value": "largest particle 32 um"})
        else:
            out.append({**base, "status": "REPORT", "value": "simulated"})
    return out


def build_report(job_id: str, spec: dict, campaign: dict, verification: dict, schedule: dict, results: list[dict]) -> dict:
    std = get_standard(campaign["standard"])
    by_req = {}
    for r in results:
        if r["requirement"]:
            by_req.setdefault(r["requirement"], []).append(r)
    trace = []
    for req in std["requirements"]:
        rs = by_req.get(req["id"], [])
        statuses = {r["status"] for r in rs}
        overall = ("NOT PLANNED" if not rs else "FAIL" if "FAIL" in statuses else "PENDING" if "PENDING" in statuses
                   else "PASS" if statuses <= {"PASS", "REPORT"} else "REPORT")
        trace.append({"requirement": req["id"], "name": req["name"], "rule": req["rule"],
                      "steps": [r["step_id"] for r in rs], "status": overall})
    counts = {k: sum(1 for r in results if r["status"] == k) for k in ("PASS", "FAIL", "PENDING", "REPORT")}
    flagged = [r for r in results if r["status"] == "FAIL"]
    return {
        "title": f"Qualification test report (draft): {spec.get('part_name')}",
        "banner": SIM_BANNER,
        "job_id": job_id, "customer": spec.get("customer"), "component_type": spec.get("component_type"),
        "standard": f"{std['id']}: {std['title']}", "standard_url": std["url"], "provenance": std["provenance"],
        "standard_note": std["note"],
        "samples": campaign["samples"], "sample_sequences": campaign["sample_sequences"],
        "verification": {"verdict": verification["verdict"], "checks": len(verification["checks"])},
        "schedule": {"release": schedule["release"], "last_test_end": schedule["last_test_end"],
                     "report_due": schedule["report_due"]},
        "traceability": trace, "results": results, "counts": counts,
        "flagged": [{"step_id": r["step_id"], "name": r["name"], "value": r["value"], "note": r.get("note", "")}
                    for r in flagged],
        "statement": ("Loopwerks is not a certification body and holds no ISO/IEC 17025 accreditation. This report "
                      "records the methods followed and the results measured. It is not a certificate of conformity."),
    }


def report_markdown(rep: dict) -> str:
    L = [f"# {rep['title']}", "", f"> {rep['banner']}", "",
         f"- Job: {rep['job_id']}", f"- Customer: {rep['customer']}", f"- Component type: {rep['component_type']}",
         f"- Standard: {rep['standard']} ({rep['standard_url']})", f"- Samples: {', '.join(rep['samples'])}",
         f"- Campaign verification: {rep['verification']['verdict']} ({rep['verification']['checks']} checks)",
         f"- Testing window: {rep['schedule']['release'][:10]} to {rep['schedule']['last_test_end'][:10]}; "
         f"report due {rep['schedule']['report_due']}", "",
         f"Planning basis: {rep['provenance']}", "", rep["standard_note"], "",
         "## Summary (simulated)", "",
         ", ".join(f"{k}: {v}" for k, v in rep["counts"].items()), ""]
    if rep["flagged"]:
        L += ["## Flagged results", ""] + [f"- **{f['step_id']} {f['name']}**: {f['value']}. {f['note']}" for f in rep["flagged"]] + [""]
    L += ["## Traceability to the standard", "", "| Req | Test | Steps | Status |", "|---|---|---|---|"]
    L += [f"| {t['requirement']} | {t['name']} | {', '.join(t['steps']) or 'none'} | {t['status']} |" for t in rep["traceability"]]
    L += ["", "## Results by step (simulated)", "", "| Step | Sample | Test | Acceptance | Value | Status |", "|---|---|---|---|---|---|"]
    L += [f"| {r['step_id']} | {r['sample_id']} | {r['name']} | {r['acceptance']} | {r['value'] or '-'} | {r['status']} |"
          for r in rep["results"]]
    L += ["", "## Statement", "", rep["statement"], "", "Engineer sign-off: ____________________  Date: __________", ""]
    return "\n".join(L)
