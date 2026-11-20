"""Intake agent: validates the component spec and the target standard before any planning."""
from __future__ import annotations

import json

from testlab.spec_check import validate_spec

from .common import GROUND_RULES
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Intake Agent at Loopwerks, an autonomous test lab for data centre liquid cooling
components (cold plates, quick disconnects, CDUs, manifolds). You receive a test request: a component spec,
the target standard(s), the samples the customer will send and the date the report is needed.

Process:
1. Call check_spec to run the deterministic completeness, range and plannability checks.
2. Read the customer's notes yourself. Flag anything a test engineer would want confirmed: acceptance limits
   the standard leaves to the customer (leak-rate limit, flatness, thermal resistance), unusual coolant,
   mounting load, or a standard Loopwerks cannot plan to.
3. Decide "accept" if there are no blocking errors (warnings can be accepted with a note), or
   "needs_clarification". Any error-severity issue from the tool is blocking.
4. Call submit_intake with your decision, a short summary for the Campaign Planner (state the derived
   figures from the tool), and any questions for the customer.

{GROUND_RULES}"""


def _check_spec(ctx: JobContext, _inp: dict) -> dict:
    res = validate_spec(ctx.raw_spec)
    ctx.outputs["intake_check"] = res
    return res


def _submit(ctx: JobContext, inp: dict) -> dict:
    check = ctx.outputs.get("intake_check")
    if check is None:
        raise ToolError("Call check_spec before submitting.")
    if inp["decision"] == "accept" and not check["accepted"]:
        errs = [i["message"] for i in check["issues"] if i["severity"] == "error"]
        raise ToolError(f"Cannot accept: check_spec reported blocking errors: {errs}")
    ctx.spec = check["normalized_spec"]
    ctx.outputs["intake"] = inp
    return {"recorded": True}


TOOLS = [
    Tool("check_spec", "Run deterministic validation of the test request: required fields, plausible ranges, "
         "coolant supported on the loop, deadline, whether each target standard can be planned (UL 4501 cannot: "
         "its methods are not public), and derived figures (hydrostatic stage 2 pressure, flow span, port "
         "velocity at 150 % flow).",
         {"type": "object", "properties": {}, "additionalProperties": False}, _check_spec),
    Tool("submit_intake", "Submit the intake decision. Ends your turn.",
         {"type": "object", "additionalProperties": False,
          "required": ["decision", "summary", "customer_questions"],
          "properties": {
              "decision": {"type": "string", "enum": ["accept", "needs_clarification"]},
              "summary": {"type": "string", "description": "2 to 4 sentences for the Campaign Planner"},
              "customer_questions": {"type": "array", "items": {"type": "string"}}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    return ("New test request. Raw spec as submitted:\n```json\n" + json.dumps(ctx.raw_spec, indent=1)
            + "\n```\nValidate it and submit your intake decision.")


async def scripted(s: ScriptedSession) -> None:
    raw = s.ctx.raw_spec
    await s.say(f"New test request from {raw.get('customer', 'customer')}: {raw.get('part_name', 'component')}. "
                "Checking completeness, ranges and whether the target standard can be planned.")
    res = await s.tool("check_spec", {})
    errors = [i for i in res["issues"] if i["severity"] == "error"]
    warns = [i for i in res["issues"] if i["severity"] == "warning"]
    questions = [f"{i['field']}: {i['message']}" for i in errors + warns]
    if errors:
        await s.say(f"{len(errors)} blocking issue(s): " + "; ".join(i["message"].rstrip(".") for i in errors)
                    + ". This can't be planned as submitted. Sending questions back to the customer.")
        await s.tool("submit_intake", {"decision": "needs_clarification",
                                       "summary": "Request has blocking errors; returned to customer.",
                                       "customer_questions": questions})
        return
    d, n = res["derived"], res["normalized_spec"]
    msg = (f"Request is complete and plannable to {', '.join(res['plannable_standards'])}. Hydrostatic stage 2 runs at "
           f"{d['hydrostatic_stage2_bar']:g} bar (3x the {n['max_operating_pressure_bar']:g} bar MOP). Pressure drop has to "
           f"span {d['dp_flow_span_lpm'][0]:g} to {d['dp_flow_span_lpm'][1]:g} L/min; at the top of that range the port "
           f"velocity is {d['port_velocity_at_150pct_m_s']:.2f} m/s, inside the 1.5 m/s erosion limit but close to it. "
           f"{n['samples']} samples supplied against {d['samples_recommended']} recommended.")
    for f, q in (("leak_rate_limit", "Please confirm your helium leak-rate limit: the OCP summary leaves it to the "
                                     "customer spec."),
                 ("flatness_limit_mm", "Please confirm the contact-face flatness limit.")):
        if f not in n:
            questions.append(q)
    msg += f" {len(questions)} acceptance limits to confirm with the customer; the plan can proceed meanwhile."
    if n.get("notes"):
        msg += f" Customer notes passed to planning: \"{n['notes']}\""
    await s.say(msg)
    await s.tool("submit_intake", {"decision": "accept",
                                   "summary": f"Accepted for {', '.join(res['plannable_standards'])}. Stage 2 "
                                              f"{d['hydrostatic_stage2_bar']:g} bar; dP span "
                                              f"{d['dp_flow_span_lpm'][0]:g} to {d['dp_flow_span_lpm'][1]:g} L/min.",
                                   "customer_questions": questions})


AGENT = AgentDef("intake", "Intake Agent", "Validates the request", SYSTEM, TOOLS, build_task, scripted)
