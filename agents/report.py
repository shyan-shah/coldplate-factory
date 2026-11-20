"""Report agent (QA): writes the qualification report, with a dry run on simulated rigs."""
from __future__ import annotations

from testlab.report import build_report, simulate_results

from .common import GROUND_RULES, get_campaign
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Report Agent (QA) at Loopwerks. You write the qualification report for the campaign:
traceability from every requirement in the standard to the steps that test it, the acceptance criterion
for each step, results, flagged failures and open items, and the statement that Loopwerks is not a
certification body.

The rigs are not built yet. Call run_dry_run to fill the report from the mock rigs: it is a SIMULATED dry
run driven by the maker's claimed figures, so the customer sees the exact report and how failures are
flagged before parts ship. Partner-lab tests have no simulated value and stay PENDING. Review the draft:
say what each flagged result would mean if it were real and what you would do next, and list the open
items (acceptance limits to confirm, partner contracts, engineer sign-off). Then call submit_report.
Always call the data simulated.

{GROUND_RULES}"""


def _dry_run(ctx: JobContext, _inp: dict) -> dict:
    cid = ctx.outputs["planner"]["campaign_id"]
    c = get_campaign(ctx, cid)
    results = simulate_results(c, ctx.spec)
    rep = build_report(ctx.job_id, ctx.spec, c, ctx.outputs["last_verification"], ctx.outputs["schedule_result"], results)
    ctx.outputs["report_result"] = rep
    return {k: rep[k] for k in ("banner", "counts", "flagged", "traceability", "statement")}


def _submit(ctx: JobContext, inp: dict) -> dict:
    if "report_result" not in ctx.outputs:
        raise ToolError("Call run_dry_run before submitting.")
    ctx.outputs["report"] = inp
    return {"recorded": True}


TOOLS = [
    Tool("run_dry_run", "Fill the qualification report from the mock rigs (SIMULATED, from the maker's claimed "
         "figures). Returns counts by status, flagged failures and the traceability matrix.",
         {"type": "object", "properties": {}, "additionalProperties": False}, _dry_run),
    Tool("submit_report", "Submit the reviewed report draft. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["summary", "flagged_findings", "open_items"],
          "properties": {"summary": {"type": "string"},
                         "flagged_findings": {"type": "array", "items": {"type": "string"}},
                         "open_items": {"type": "array", "items": {"type": "string"}}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    q = ctx.outputs["intake"]["customer_questions"]
    return (f"Campaign {ctx.outputs['planner']['campaign_id']} is verified and scheduled "
            f"({ctx.outputs['scheduling']['summary']}). Open customer questions from intake: {q}. Write the report.")


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    await s.say("Building the report: traceability from each requirement to its steps, acceptance criteria, then a dry "
                "run on the mock rigs so the customer sees the format. The values are simulated, not measured.")
    r = await s.tool("run_dry_run", {})
    c = r["counts"]
    flagged = [f"{f['step_id']} {f['name']}: {f['value']} (simulated). {f['note']}" for f in r["flagged"]]
    await s.say(f"Dry run: {c['PASS']} pass, {c['FAIL']} flagged, {c['PENDING']} pending at partner labs, "
                f"{c['REPORT']} report-only. "
                + (f"Flagged: {flagged[0]} If that were real, I'd hold the report, repeat on a second sample and check the "
                   "rig against a reference plate before calling it a part failure. " if flagged else "")
                + "Every requirement traces to at least one step. The report carries the not-a-certificate statement "
                  "and an engineer sign-off line.")
    opens = [*ctx.outputs["intake"]["customer_questions"],
             "Contract partner labs for cycling, shock, vibration, salt spray, humidity and fluid compatibility",
             "Engineer sign-off of the final report after real results replace the simulated ones"]
    await s.tool("submit_report", {"summary": f"Draft report: {c['PASS']} pass / {c['FAIL']} flagged / {c['PENDING']} "
                                              "pending (simulated dry run).",
                                   "flagged_findings": flagged, "open_items": opens})


AGENT = AgentDef("report", "Report Agent", "Writes the qualification report", SYSTEM, TOOLS, build_task, scripted)
