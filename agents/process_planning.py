"""Process planning agent: machining plan, stock, cycle time, cost, joining and leak test steps."""
from __future__ import annotations

import json

from engineering.process import plan_process

from .common import GROUND_RULES, get_design, design_brief
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Process Planning Agent at an autonomous cold plate factory. The cell has two CNC
mills (3-axis Haas, 5-axis DMG Mori), a friction-stir welding (FSW) station and a pressure-decay leak test
rig. You turn the verified design parameter set into a manufacturing routing.

Call plan_process to generate the routing (stock size, operation sequence, tools, cycle time per part,
material and machine cost, FSW lid joining, leak test). Review it like a manufacturing engineer:
identify the bottleneck operation, the main quality risks (e.g. fin damage, weld distortion of the
contact face, burrs in channels) and how the routing controls them. Then submit_process_plan.

{GROUND_RULES}"""


def _plan(ctx: JobContext, inp: dict) -> dict:
    d = get_design(ctx, inp["design_id"])
    plan = plan_process(d["params"], int(ctx.spec["quantity"]))
    plan["design_id"] = inp["design_id"]
    ctx.outputs["process_plan_result"] = plan
    return plan


def _submit(ctx: JobContext, inp: dict) -> dict:
    if "process_plan_result" not in ctx.outputs:
        raise ToolError("Call plan_process before submitting.")
    ctx.outputs["process_planning"] = inp
    return {"recorded": True}


TOOLS = [
    Tool("plan_process", "Generate the deterministic routing for a design_id at the order quantity: stock "
         "blanks, operations with stations/tools/minutes, cycle time, cost per part and batch cost.",
         {"type": "object", "additionalProperties": False, "required": ["design_id"],
          "properties": {"design_id": {"type": "string"}}}, _plan),
    Tool("submit_process_plan", "Submit the reviewed process plan. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["summary", "bottleneck", "risks_and_controls"],
          "properties": {"summary": {"type": "string"}, "bottleneck": {"type": "string"},
                         "risks_and_controls": {"type": "array", "items": {"type": "string"}}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    sel = ctx.outputs["thermal_design"]["selected_design_id"]
    return (f"Verified design {sel}, quantity {ctx.spec['quantity']}:\n"
            + json.dumps(design_brief(ctx, sel), default=str)
            + f"\nVerification summary: {ctx.outputs['verification']['summary']}\nPlan the process.")


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    sel = ctx.outputs["thermal_design"]["selected_design_id"]
    await s.say(f"Routing {sel} for {ctx.spec['quantity']} pcs: base and lid machined from plate, channels cut "
                "before welding, FSW lid, post-weld skim of the contact face, then proof and leak test.")
    p = await s.tool("plan_process", {"design_id": sel})
    ops = p["operations"]
    slow = max(ops, key=lambda o: o["minutes"])
    st = p["minutes_per_part_by_station"]
    n_machines = {"CNC": 2, "FSW": 1, "LEAK": 1}
    load = {k: st.get(k, 0) / n for k, n in n_machines.items()}
    neck = max(load, key=load.get)
    c = p["cost_per_part_usd"]
    await s.say(f"Cycle time {p['cycle_time_min_per_part']:.0f} min/part ({st.get('CNC', 0):.0f} CNC, {st.get('FSW', 0):.0f} FSW, "
                f"{st.get('LEAK', 0):.0f} leak test). The longest single operation is op {slow['seq']} ({slow['operation'].split(':')[0]}, "
                f"{slow['minutes']:.1f} min). Per machine, {neck} carries the most load ({load[neck]:.1f} min/part"
                f"{' split across 2 mills' if neck == 'CNC' else ''}), so {neck} is the bottleneck station. Cost "
                f"${c['total']:.2f}/part (${c['material']:.2f} material), ${p['batch_cost_usd']:,.0f} for the batch. "
                f"Stock: base blank {' x '.join(f'{v:g}' for v in p['stock']['base_blank_mm'])} mm. "
                "FSW heat input can bow the contact face, so the post-weld skim (op 70) is sequenced after welding "
                "on a vacuum fixture.")
    await s.tool("submit_process_plan", {
        "summary": f"{len(ops)} operations, {p['cycle_time_min_per_part']:.0f} min/part, ${c['total']:.2f}/part.",
        "bottleneck": f"{neck} ({load[neck]:.1f} min/part per machine); op {slow['seq']} is the longest single op.",
        "risks_and_controls": [
            "Fin lean/chatter during gang sawing -> climb cut, flood coolant, first-channel pin-gauge check",
            "Contact-face distortion from FSW -> weld before final skim (op 70), vacuum fixture, 100% flatness CMM",
            "Burrs/chips trapped in channels -> ultrasonic clean before lid weld, borescope on first article",
            "Weld tunnel defects -> macro-section first article, 100% proof + leak test"]})


AGENT = AgentDef("process_planning", "Process Planning Agent", "Machining & joining routing", SYSTEM, TOOLS,
                 build_task, scripted)
