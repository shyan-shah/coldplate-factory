"""Verification agent: independently re-checks the selected design; rejects with reasons if it fails."""
from __future__ import annotations

import json

from engineering.verification import verify_design

from .common import GROUND_RULES, get_design, op_point, design_brief
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Verification Agent at an autonomous cold plate factory. You are independent of the
Thermal Design Agent: you do not trust its reported numbers. You re-run the analysis yourself with
verify_design, which applies the factory verification standard:
- nominal case temperature and pressure drop against the customer limits
- worst case thermal: flow -5%, TIM2 resistance +25%, wetted-side fouling 2e-5 m2K/W
- worst case hydraulic: flow +5%, channel width -0.02 mm, channel depth -0.05 mm
- coolant velocity erosion limit, heat-source coverage, and the cell's DFM rules.

Decide "approve" only if every check passes. Otherwise "reject" and give the design agent specific,
actionable required changes (what limit was exceeded, by how much, and what direction to move).
You may also reject for an engineering concern the checks do not capture, but explain it.

{GROUND_RULES}"""


def _verify(ctx: JobContext, inp: dict) -> dict:
    d = get_design(ctx, inp["design_id"])
    s = ctx.spec
    v = verify_design(d["params"], op_point(ctx), float(s["max_case_temp_c"]), float(s["max_pressure_drop_kpa"]))
    v["design_id"] = inp["design_id"]
    ctx.outputs["last_verification"] = v
    return v


def _submit(ctx: JobContext, inp: dict) -> dict:
    v = ctx.outputs.get("last_verification")
    if v is None:
        raise ToolError("Call verify_design before submitting.")
    selected = ctx.outputs["thermal_design"]["selected_design_id"]
    if v["design_id"] != selected:
        raise ToolError(f"You verified {v['design_id']} but the design under review is {selected}.")
    if inp["verdict"] == "approve" and v["verdict"] != "PASS":
        raise ToolError(f"Cannot approve: {len(v['failures'])} verification checks failed.")
    if inp["verdict"] == "reject" and not inp["required_changes"]:
        raise ToolError("A rejection must list required changes.")
    ctx.outputs["verification"] = inp
    return {"recorded": True}


TOOLS = [
    Tool("verify_design", "Re-run the full nominal + worst-case + DFM verification on a design_id. "
         "Returns every check with value, limit and pass/fail.",
         {"type": "object", "additionalProperties": False, "required": ["design_id"],
          "properties": {"design_id": {"type": "string"}}}, _verify),
    Tool("submit_verification", "Submit the verdict. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["verdict", "summary", "required_changes"],
          "properties": {
              "verdict": {"type": "string", "enum": ["approve", "reject"]},
              "summary": {"type": "string"},
              "required_changes": {"type": "array", "items": {"type": "string"},
                                   "description": "Empty if approved"}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    td = ctx.outputs["thermal_design"]
    sel = td["selected_design_id"]
    return (f"Design under review: {sel} (round {len(ctx.verification_feedback) + 1}).\n"
            f"Customer limits: max case {ctx.spec['max_case_temp_c']} degC, max dP {ctx.spec['max_pressure_drop_kpa']} kPa "
            f"at {ctx.spec['flow_rate_lpm']} L/min {ctx.spec['coolant']}, inlet {ctx.spec['inlet_temp_c']} degC.\n"
            f"Design agent's claim (do not trust the numbers, re-check):\n{json.dumps(design_brief(ctx, sel), default=str)}\n"
            f"Design agent rationale: {td['rationale']}\n"
            + (f"Response to previous findings: {td['response_to_verification']}\n" if td['response_to_verification'] else ""))


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    sel = ctx.outputs["thermal_design"]["selected_design_id"]
    await s.say(f"Reviewing {sel}. I'm re-running the models from the parameter set rather than taking the design "
                "agent's figures, then applying the worst-case standard and the cell's DFM rules.")
    v = await s.tool("verify_design", {"design_id": sel})
    n_pass = sum(c["pass"] for c in v["checks"])
    wc = v["worst_case"]
    if v["verdict"] == "PASS":
        await s.say(f"All {n_pass} checks pass. Worst case: {wc['t_case_c']:.1f} degC against the {ctx.spec['max_case_temp_c']} degC "
                    f"limit, {wc['dp_kpa']:.1f} kPa against {ctx.spec['max_pressure_drop_kpa']} kPa, velocity "
                    f"{wc['velocity_m_s']:.2f} m/s. Nominal numbers match the design agent's. Approved for process planning.")
        await s.tool("submit_verification", {"verdict": "approve", "summary":
                                             f"PASS {n_pass}/{len(v['checks'])}. Worst case {wc['t_case_c']:.1f} degC, "
                                             f"{wc['dp_kpa']:.1f} kPa.", "required_changes": []})
        return
    changes = []
    for f in v["failures"]:
        if f["check"].startswith("Pressure drop, worst case"):
            changes.append(f"Worst-case dP {f['value']:.1f} kPa exceeds {f['limit']:.0f} kPa "
                           f"({(f['value'] / f['limit'] - 1):.0%} over). Narrow channels are too sensitive to the "
                           "-0.02 mm cutter tolerance; widen the channels or reduce nominal dP to about 65% of the limit.")
        elif f["check"].startswith("DFM"):
            changes.append(f"{f['check'][5:]}: {f['value']} exceeds the cell limit {f['limit']} ({f['detail']}). "
                           "Rebalance channel geometry within the limit.")
        elif f["check"].startswith("Case temperature"):
            changes.append(f"{f['check']}: {f['value']:.1f} degC > {f['limit']:.1f} degC. Needs about "
                           f"{f['value'] - f['limit']:.1f} degC more margin.")
        else:
            changes.append(f"{f['check']}: {f['value']} vs limit {f['limit']} {f['unit']}.")
    await s.say(f"REJECTED. {len(v['failures'])} of {len(v['checks'])} checks fail, although nominal performance passes "
                f"({v['nominal']['t_case_c']:.1f} degC, {v['nominal']['dp_kpa']:.1f} kPa): " + " ".join(changes)
                + " Sending it back to the Thermal Design Agent.")
    await s.tool("submit_verification", {"verdict": "reject", "summary": f"FAIL: " + "; ".join(
        f"{f['check']} {f['value']} > {f['limit']}" for f in v["failures"]), "required_changes": changes})


AGENT = AgentDef("verification", "Verification Agent", "Independently re-checks against spec", SYSTEM, TOOLS,
                 build_task, scripted)
