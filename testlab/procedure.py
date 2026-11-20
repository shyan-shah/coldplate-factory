"""Turn a verified campaign into rig operations: fixtures, cobot handling tasks, durations and a cost estimate.

All rates are planning assumptions for the v0 lab (labelled as such in the output), not quotes.
"""
from __future__ import annotations

from .methods import HANDLING_IN_MIN, HANDLING_OUT_MIN, PARTNER_TRANSIT_WORKING_DAYS

RATES_GBP_PER_H = {"bench": 12.0, "hired": 20.0, "cobot": 15.0, "metrology": 60.0, "engineer": 40.0}
RATE_NOTE = ("Planning assumptions, not quotes: bench rig GBP 12/h (core bench over about 750 h/yr), hired helium "
             "detector GBP 20/h, cobot GBP 15/h (rental), university CMM GBP 60/h, engineer GBP 40/h. Partner-lab "
             "work needs quotes.")
REPORT_ENGINEER_H = 4.0

FIXTURE = {
    "LEAK-1": "Port blanking plugs + N2 manifold", "HYDRO-1": "Shielded clamp fixture, bleed at high point",
    "FLOW-1": "Loop fixture with QD inlet/outlet", "THERM-1": "Heater block clamp at stated mounting load",
    "JIG-1": "Retention fixture on linear actuator", "HE-1": "Vacuum fixture to detector port",
}


def plan_procedure(campaign: dict) -> dict:
    ops, cobot_tasks = [], 0
    for s in campaign["steps"]:
        kind = s["where"]
        op = {"step_id": s["step_id"], "sample_id": s["sample_id"], "test": s["test"], "name": s["name"],
              "resource": s["resource"], "kind": kind, "run_min": s["run_minutes"], "handling_in_min": 0.0,
              "handling_out_min": 0.0, "transit_working_days": 0, "cobot_tasks": [], "fixture": FIXTURE.get(s["resource"], "")}
        if kind in ("bench", "hired"):
            op["handling_in_min"], op["handling_out_min"] = HANDLING_IN_MIN, HANDLING_OUT_MIN
            op["cobot_tasks"] = [f"Pick {s['sample_id']} from rack, place on {s['resource']} fixture",
                                 "Connect inlet and outlet", "Confirm seal by force signature",
                                 "Disconnect, drain, return to rack"]
            cobot_tasks += 1
        elif kind == "partner":
            op["transit_working_days"] = PARTNER_TRANSIT_WORKING_DAYS
            op["fixture"] = "Packed and shipped to partner lab (not contracted)"
        elif kind == "metrology":
            op["fixture"] = "Hand-carried to university CMM"
        ops.append(op)

    def h(k):
        return sum(o["run_min"] for o in ops if o["kind"] == k) / 60
    cobot_h = sum(o["handling_in_min"] + o["handling_out_min"] for o in ops) / 60
    cost = {"bench_rigs": h("bench") * RATES_GBP_PER_H["bench"], "hired_instrument": h("hired") * RATES_GBP_PER_H["hired"],
            "cobot_handling": cobot_h * RATES_GBP_PER_H["cobot"], "metrology": h("metrology") * RATES_GBP_PER_H["metrology"],
            "engineer_review_and_report": REPORT_ENGINEER_H * RATES_GBP_PER_H["engineer"]}
    cost = {k: round(v, 2) for k, v in cost.items()}
    return {
        "operations": ops,
        "totals": {"operations": len(ops), "bench_hours": round(h("bench") + h("hired"), 1),
                   "metrology_hours": round(h("metrology"), 1), "partner_hours": round(h("partner"), 1),
                   "cobot_handling_events": cobot_tasks, "cobot_hours": round(cobot_h, 2),
                   "partner_steps": sum(1 for o in ops if o["kind"] == "partner")},
        "cost_estimate_gbp": {**cost, "total_excl_partner": round(sum(cost.values()), 2)},
        "rate_note": RATE_NOTE,
    }
