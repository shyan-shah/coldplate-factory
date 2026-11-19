"""QA agent: inspection and test plan (CMM, flatness, leak test, flow and thermal acceptance)."""
from __future__ import annotations

from engineering.qa import qa_requirements

from .common import GROUND_RULES, get_design
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the QA Agent at an autonomous cold plate factory. Produce the inspection and test plan
for the job: CMM checks on critical dimensions, contact-face flatness, proof and leak test pressure and
hold time, flow/pressure-drop acceptance and thermal acceptance against the predicted performance.

Call generate_qa_requirements for the derived parameters (they follow from the design, its predicted
performance, the order quantity and the system pressure). Review them: say which characteristics are
critical to function and why, and add any job-specific notes (e.g. first-article requirements).
Then call submit_qa_plan.

{GROUND_RULES}"""


def _gen(ctx: JobContext, inp: dict) -> dict:
    d = get_design(ctx, inp["design_id"])
    q = qa_requirements(d["params"], d["result"], int(ctx.spec["quantity"]),
                        float(ctx.spec.get("max_operating_pressure_bar", 4.0)))
    ctx.outputs["qa_result"] = q
    return q


def _submit(ctx: JobContext, inp: dict) -> dict:
    if "qa_result" not in ctx.outputs:
        raise ToolError("Call generate_qa_requirements before submitting.")
    ctx.outputs["qa"] = inp
    return {"recorded": True}


TOOLS = [
    Tool("generate_qa_requirements", "Derive inspection/test parameters for a design_id: dimensional checks "
         "with specs and sampling, proof/leak test pressures and hold time from internal volume, flow test and "
         "thermal acceptance limits from the predicted performance.",
         {"type": "object", "additionalProperties": False, "required": ["design_id"],
          "properties": {"design_id": {"type": "string"}}}, _gen),
    Tool("submit_qa_plan", "Submit the QA plan. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["summary", "critical_characteristics", "notes"],
          "properties": {"summary": {"type": "string"},
                         "critical_characteristics": {"type": "array", "items": {"type": "string"}},
                         "notes": {"type": "array", "items": {"type": "string"}}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    sel = ctx.outputs["thermal_design"]["selected_design_id"]
    return (f"Design {sel}, quantity {ctx.spec['quantity']}, system max operating pressure "
            f"{ctx.spec.get('max_operating_pressure_bar', 4.0)} bar. Process plan risks: "
            f"{ctx.outputs['process_planning']['risks_and_controls']}. Produce the QA plan.")


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    sel = ctx.outputs["thermal_design"]["selected_design_id"]
    await s.say("Deriving inspection and test requirements from the verified design and its predicted performance.")
    q = await s.tool("generate_qa_requirements", {"design_id": sel})
    lt, ft, tt = q["leak_test"], q["flow_test"], q["thermal_test"]
    await s.say(f"Leak: proof {lt['proof_pressure_bar']:g} bar for {lt['proof_hold_s']} s, then pressure decay at "
                f"{lt['decay_test_pressure_bar']:g} bar. With {q['internal_volume_ml']:.1f} ml internal volume, a "
                f"{lt['allowed_leak_rate_mbar_l_s']:g} mbar.L/s limit gives a {lt['decay_hold_s']:.0f} s hold with at most "
                f"{lt['max_pressure_decay_mbar']:.2f} mbar decay, 100% of parts. Flow: {ft['acceptance']} at "
                f"{ft['flow_lpm']} L/min. Thermal: {tt['acceptance']} on a TTV at {tt['power_w']:g} W. Lot sample size "
                f"{q['lot_sample_size']}. Contact-face flatness gets 100% CMM because it sets the TIM2 bond line "
                "and is the characteristic most likely to drift after welding.")
    crit = [d["feature"] for d in q["dimensional"] if d["critical"]]
    await s.tool("submit_qa_plan", {
        "summary": f"{len(q['dimensional'])} dimensional checks ({len(crit)} critical), 100% proof + leak, "
                   f"flow and thermal acceptance sampled.",
        "critical_characteristics": crit,
        "notes": ["First article: full CMM, channel optical check before welding, FSW macro-section, TTV test",
                  "Re-check flatness on first article after proof test (no bulging)",
                  "Any leak failure quarantines the lot pending FSW parameter review"]})


AGENT = AgentDef("qa", "QA Agent", "Inspection & test plan", SYSTEM, TOOLS, build_task, scripted)
