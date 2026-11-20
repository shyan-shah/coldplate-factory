"""Test Procedure agent: rig operations, fixtures, cobot handling tasks and a cost estimate."""
from __future__ import annotations

import json

from testlab.procedure import plan_procedure

from .common import GROUND_RULES, campaign_brief, get_campaign
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Test Procedure Agent at Loopwerks. The v0 lab has bench rigs (LEAK-1, HYDRO-1, FLOW-1,
THERM-1, JIG-1), a hired helium leak detector (HE-1), a loaned or rented cobot (COBOT-1) that loads parts and
makes and breaks the fluid connections, a university CMM, and partner labs that are planned but not contracted.

Call plan_procedure to turn the verified campaign into rig operations: fixture, cobot handling tasks,
run time, and a cost estimate at the lab's planning rates. Review it like a test engineer: name the bottleneck
resource, the main risks to valid results (contamination, trapped air, fixture leaks, handling damage) and
how the procedure controls them. Then call submit_procedure.

{GROUND_RULES}"""


def _plan(ctx: JobContext, inp: dict) -> dict:
    c = get_campaign(ctx, inp["campaign_id"])
    p = plan_procedure(c)
    p["campaign_id"] = inp["campaign_id"]
    ctx.outputs["procedure_result"] = p
    return p


def _submit(ctx: JobContext, inp: dict) -> dict:
    if "procedure_result" not in ctx.outputs:
        raise ToolError("Call plan_procedure before submitting.")
    ctx.outputs["procedure"] = inp
    return {"recorded": True}


TOOLS = [
    Tool("plan_procedure", "Generate rig operations for a campaign_id: resource, fixture, cobot tasks, run and handling "
         "minutes, partner shipping, totals and a cost estimate (planning rates, not quotes).",
         {"type": "object", "additionalProperties": False, "required": ["campaign_id"],
          "properties": {"campaign_id": {"type": "string"}}}, _plan),
    Tool("submit_procedure", "Submit the reviewed procedure. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["summary", "bottleneck", "risks_and_controls"],
          "properties": {"summary": {"type": "string"}, "bottleneck": {"type": "string"},
                         "risks_and_controls": {"type": "array", "items": {"type": "string"}}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    cid = ctx.outputs["planner"]["campaign_id"]
    return (f"Verified campaign {cid}:\n{json.dumps(campaign_brief(ctx, cid))}\n"
            f"Verification: {ctx.outputs['verification']['summary']}\nPlan the procedure.")


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    cid = ctx.outputs["planner"]["campaign_id"]
    await s.say(f"Turning {cid} into rig operations: fixture per rig, cobot load and connect before each bench test, "
                "disconnect and drain after.")
    p = await s.tool("plan_procedure", {"campaign_id": cid})
    t, c = p["totals"], p["cost_estimate_gbp"]
    by_res: dict = {}
    for o in p["operations"]:
        if o["kind"] in ("bench", "hired"):
            by_res[o["resource"]] = by_res.get(o["resource"], 0) + o["run_min"]
    neck = max(by_res, key=by_res.get)
    await s.say(f"{t['operations']} operations. Bench and hired instrument {t['bench_hours']} h, university CMM "
                f"{t['metrology_hours']} h, partner labs {t['partner_hours']} h over {t['partner_steps']} steps. The cobot "
                f"handles {t['cobot_handling_events']} load/connect cycles, {t['cobot_hours']} h in total. Busiest bench "
                f"resource is {neck} at {by_res[neck] / 60:.1f} h. Internal cost excluding partner labs is GBP "
                f"{c['total_excl_partner']:,.0f} at planning rates, not quotes. Partner work needs quotes before release.")
    await s.tool("submit_procedure", {
        "summary": f"{t['operations']} ops; {t['bench_hours']} h bench; {t['cobot_handling_events']} cobot handlings; "
                   f"GBP {c['total_excl_partner']:,.0f} excl. partner labs (planning rates).",
        "bottleneck": f"{neck} ({by_res[neck] / 60:.1f} h); partner labs are the schedule driver.",
        "risks_and_controls": [
            "Trapped air skews pressure decay and dP -> bleed at the high point, 10 min stabilisation before each hold",
            "Fixture leak read as part leak -> blank-fixture reference run each day on LEAK-1",
            "Contamination between samples -> cleanliness flush first on S1, filtered PG25, sealed QDs between rigs",
            "Handling damage -> cobot force limit on connect, seal confirmed by force signature before pressurising",
            "Partner labs not contracted -> quotes and slots confirmed before the campaign is released"]})


AGENT = AgentDef("procedure", "Test Procedure Agent", "Rig ops and cobot tasks", SYSTEM, TOOLS, build_task, scripted)
