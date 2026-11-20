"""Verification agent: independently checks the campaign against the standard; rejects with reasons."""
from __future__ import annotations

import json

from testlab.verify import verify_campaign

from .common import GROUND_RULES, campaign_brief, get_campaign
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Verification Agent at Loopwerks. You are independent of the Campaign Planner and do
not trust its totals. You re-check the campaign with verify_campaign, which tests it against the standard:
- every mandatory requirement has at least one step
- parameters are inside the standard's ranges (dwell and hold times, hydrostatic stages, burst ramp,
  thermal inlet temperature, pressure-drop flow points and span, port velocity, cycling and exposure times)
- sequence rules: tracer-gas leak before and after shipping cycling on the same sample, destructive tests
  last on their sample, no more samples than the customer supplies.

Approve only if every check passes. Otherwise reject and give the planner specific, actionable required
changes (which check, by how much, which step and sample). Note partner-lab dependencies, but they are not
grounds for rejection.

{GROUND_RULES}"""


def _verify(ctx: JobContext, inp: dict) -> dict:
    c = get_campaign(ctx, inp["campaign_id"])
    v = verify_campaign(c, ctx.spec)
    v["campaign_id"] = inp["campaign_id"]
    ctx.outputs["last_verification"] = v
    return v


def _submit(ctx: JobContext, inp: dict) -> dict:
    v = ctx.outputs.get("last_verification")
    if v is None:
        raise ToolError("Call verify_campaign before submitting.")
    sel = ctx.outputs["planner"]["campaign_id"]
    if v["campaign_id"] != sel:
        raise ToolError(f"You verified {v['campaign_id']} but the campaign under review is {sel}.")
    if inp["verdict"] == "approve" and v["verdict"] != "PASS":
        raise ToolError(f"Cannot approve: {len(v['failures'])} checks failed.")
    if inp["verdict"] == "reject" and not inp["required_changes"]:
        raise ToolError("A rejection must list required changes.")
    ctx.outputs["verification"] = inp
    return {"recorded": True}


TOOLS = [
    Tool("verify_campaign", "Check a campaign_id against the standard: coverage, parameters and sequence rules. "
         "Returns every check with value, limit and pass/fail.",
         {"type": "object", "additionalProperties": False, "required": ["campaign_id"],
          "properties": {"campaign_id": {"type": "string"}}}, _verify),
    Tool("submit_verification", "Submit the verdict. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["verdict", "summary", "required_changes"],
          "properties": {"verdict": {"type": "string", "enum": ["approve", "reject"]}, "summary": {"type": "string"},
                         "required_changes": {"type": "array", "items": {"type": "string"}}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    p = ctx.outputs["planner"]
    cid = p["campaign_id"]
    return (f"Campaign under review: {cid} (round {len(ctx.verification_feedback) + 1}). Samples supplied: "
            f"{ctx.spec['samples']}.\nPlanner's claim (re-check it):\n{json.dumps(campaign_brief(ctx, cid))}\n"
            f"Rationale: {p['rationale']}\n"
            + (f"Response to previous findings: {p['response_to_verification']}\n" if p["response_to_verification"] else ""))


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    cid = ctx.outputs["planner"]["campaign_id"]
    await s.say(f"Checking {cid} against the standard from its step list, not from the planner's totals.")
    v = await s.tool("verify_campaign", {"campaign_id": cid})
    n_pass = sum(c["pass"] for c in v["checks"])
    if v["verdict"] == "PASS":
        await s.say(f"All {n_pass} checks pass. Coverage {v['coverage']['covered']}/{v['coverage']['total']}, every "
                    "parameter inside its range, sequence rules met. " + " ".join(v["notes"])
                    + " Approved for procedure planning.")
        await s.tool("submit_verification", {"verdict": "approve", "required_changes": [],
                                             "summary": f"PASS {n_pass}/{len(v['checks'])}. Coverage "
                                                        f"{v['coverage']['covered']}/{v['coverage']['total']}."})
        return
    changes = []
    for f in v["failures"]:
        if f["check"].startswith("R06 Pressure drop flow points"):
            changes.append(f"{f['check']}: {f['value']} points, the standard needs at least 6.")
        elif f["check"].startswith("R06 Pressure drop span"):
            changes.append(f"{f['check']}: covers {f['value']} % of rated flow; it must reach 25 % and 150 %.")
        elif f["detail"]:
            changes.append(f"{f['check']}: {f['detail']}.")
        else:
            changes.append(f"{f['check']}: {f['value']} {f['unit']} vs {f['limit']}.")
    await s.say(f"REJECTED. {len(v['failures'])} of {len(v['checks'])} checks fail although coverage is "
                f"{v['coverage']['covered']}/{v['coverage']['total']}: " + " ".join(changes)
                + " A report built on this plan would not stand up against the standard. Back to the planner.")
    await s.tool("submit_verification", {"verdict": "reject", "required_changes": changes,
                                         "summary": "FAIL: " + "; ".join(f["check"] for f in v["failures"])})


AGENT = AgentDef("verification", "Verification Agent", "Checks the plan against the standard", SYSTEM, TOOLS,
                 build_task, scripted)
