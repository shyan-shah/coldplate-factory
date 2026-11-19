"""Intake agent: validates the customer chip spec and flags missing or unrealistic inputs."""
from __future__ import annotations

import json

from engineering.spec_check import validate_spec

from .common import GROUND_RULES
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Intake Agent at an autonomous factory that designs and manufactures custom
liquid cooling cold plates for AI accelerators. You receive a customer request (a chip thermal spec)
and decide whether it is complete, plausible and physically feasible enough to hand to the Thermal
Design Agent.

Process:
1. Call check_spec to run the deterministic completeness, range and feasibility checks.
2. Read the customer's free-text notes yourself. Flag anything a cold plate engineer would want
   confirmed (conflicting requirements, missing mechanical constraints, unusual coolant chemistry, etc.).
3. Decide: "accept" if there are no blocking errors (warnings and defaults can be accepted with a note),
   or "needs_clarification" if the job cannot sensibly proceed. Any error-severity issue from the tool
   is blocking.
4. Call submit_intake with your decision, a short summary for the design team (state the derived
   thermal budget from the tool), and any questions for the customer.

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
    Tool("check_spec", "Run deterministic validation of the customer spec: required fields, plausible "
         "ranges, coolant support, deadline, and physical feasibility (case-temperature floor from coolant "
         "rise and TIM alone). Returns issues, the normalized spec with defaults, and derived thermal budget.",
         {"type": "object", "properties": {}, "additionalProperties": False}, _check_spec),
    Tool("submit_intake", "Submit the intake decision. Ends your turn.",
         {"type": "object", "additionalProperties": False,
          "required": ["decision", "summary", "customer_questions"],
          "properties": {
              "decision": {"type": "string", "enum": ["accept", "needs_clarification"]},
              "summary": {"type": "string", "description": "2-4 sentences for the design team"},
              "customer_questions": {"type": "array", "items": {"type": "string"},
                                     "description": "Questions to send back to the customer (may be empty)"}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    return ("New customer request. Raw spec as submitted:\n```json\n"
            + json.dumps(ctx.raw_spec, indent=1) + "\n```\nValidate it and submit your intake decision.")


async def scripted(s: ScriptedSession) -> None:
    raw = s.ctx.raw_spec
    await s.say(f"New request from {raw.get('customer', 'customer')}: {raw.get('part_name', 'cold plate')}. "
                "Running completeness, range and feasibility checks on the spec.")
    res = await s.tool("check_spec", {})
    errors = [i for i in res["issues"] if i["severity"] == "error"]
    warns = [i for i in res["issues"] if i["severity"] == "warning"]
    infos = [i for i in res["issues"] if i["severity"] == "info"]
    questions = [f"{i['field']}: {i['message']}" for i in errors + warns]
    if errors:
        await s.say(f"{len(errors)} blocking issue(s): " + "; ".join(i["message"].rstrip(".") for i in errors)
                    + ". This can't go to design as submitted. Sending questions back to the customer.")
        await s.tool("submit_intake", {"decision": "needs_clarification",
                                       "summary": "Spec has blocking errors; returned to customer.",
                                       "customer_questions": questions})
        return
    d = res["derived"]
    notes = str(raw.get("notes", "")).strip()
    msg = (f"Spec is complete and feasible. Heat flux {d['heat_flux_w_cm2']:.1f} W/cm2, coolant rise "
           f"{d['coolant_temp_rise_c']:.1f} degC at the stated flow. The coolant and TIM alone set a case-temperature "
           f"floor of {d['case_temp_floor_c']:.1f} degC, which leaves {d['budget_left_for_plate_c']:.1f} degC for the "
           f"plate itself: required case-to-inlet resistance {d['required_r_case_to_inlet_k_w']:.4f} K/W. "
           "That's a tight budget; it points to a fine-pitch microchannel plate in copper.")
    if infos:
        msg += " Defaults applied: " + "; ".join(i["field"] for i in infos) + "."
    if notes:
        msg += f" Customer notes noted for design: \"{notes}\""
        questions.append("Please confirm the TIM2 material and bond line; we assumed "
                         f"{res['normalized_spec']['tim_resistance_cm2k_w']} cm2K/W.")
    await s.say(msg)
    await s.tool("submit_intake", {"decision": "accept",
                                   "summary": f"Accepted. Plate budget {d['budget_left_for_plate_c']:.1f} degC; "
                                              f"required R {d['required_r_case_to_inlet_k_w']:.4f} K/W.",
                                   "customer_questions": questions})


AGENT = AgentDef("intake", "Intake Agent", "Validates the customer spec", SYSTEM, TOOLS, build_task, scripted)
