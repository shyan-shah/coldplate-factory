"""Scheduling agent: books the campaign onto the mock rigs, the cobot and partner labs."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from factory import db
from factory.scheduler import schedule

from .common import GROUND_RULES
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Scheduling Agent at Loopwerks. Rigs run unattended around the clock; the cobot loads,
connects, disconnects and unloads parts only in the supervised window (06:00 to 22:00 Monday to Friday,
optionally Saturday). Partner labs add shipping both ways. The lab already has mock work and planned
downtime booked.

1. Call get_lab_state to see resources, bookings and downtime.
2. Call schedule_campaign to generate options (Saturday cobot handling on or off). Each option gives the
   report due date (5 working days after the last test) against the customer's deadline.
3. Pick the option that meets the deadline with the least extra supervision, and hold it with
   submit_schedule. Bookings stay tentative until the engineer releases the campaign.

{GROUND_RULES}"""


def _state(ctx: JobContext, _inp: dict) -> dict:
    by: dict = defaultdict(list)
    for b in db.busy_for(ctx.job_id):
        by[b["machine_id"]].append({"label": b["label"], "kind": b["kind"], "start": b["start"], "end": b["end"]})
    return {"now": datetime.now().replace(microsecond=0).isoformat(), "resources": db.machines(), "bookings": dict(by),
            "rules": "Rigs 24/7 unattended; cobot handling 06:00-22:00 Mon-Fri (Saturday optional); CMM 09:00-17:00 "
                     "weekdays; partner shipping 2 working days each way"}


def _schedule(ctx: JobContext, inp: dict) -> dict:
    p = ctx.outputs.get("procedure_result")
    if not p:
        raise ToolError("No procedure available")
    r = schedule(p["operations"], db.machines(), db.busy_for(ctx.job_id), datetime.now(),
                 date.fromisoformat(str(ctx.spec["deadline"])), allow_saturday=bool(inp.get("allow_saturday_handling")))
    oid = ctx.next_id("O")
    ctx.schedule_options[oid] = r
    return {"option_id": oid, **{k: v for k, v in r.items() if k != "operations"}, "bookings": len(r["operations"])}


def _submit(ctx: JobContext, inp: dict) -> dict:
    oid = inp["option_id"]
    if oid not in ctx.schedule_options:
        raise ToolError(f"Unknown option_id {oid}. Known: {sorted(ctx.schedule_options)}")
    r = ctx.schedule_options[oid]
    db.replace_tentative(ctx.job_id, [{"machine_id": o["machine_id"], "label": f"{ctx.job_id} {o['label']}",
                                       "start": o["start"], "end": o["end"]} for o in r["operations"]])
    ctx.outputs["scheduling"] = inp
    ctx.outputs["schedule_result"] = r
    return {"held": True, "bookings": len(r["operations"]), "report_due": r["report_due"]}


TOOLS = [
    Tool("get_lab_state", "List lab resources and all current bookings and downtime.",
         {"type": "object", "properties": {}, "additionalProperties": False}, _state),
    Tool("schedule_campaign", "Compute a finite-capacity schedule option (does not book it). Returns option_id, last "
         "test end, report due date vs deadline, slack, unattended rig hours and resource load.",
         {"type": "object", "additionalProperties": False, "required": ["allow_saturday_handling"],
          "properties": {"allow_saturday_handling": {"type": "boolean"}}}, _schedule),
    Tool("submit_schedule", "Hold the chosen option as tentative bookings. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["option_id", "summary"],
          "properties": {"option_id": {"type": "string"}, "summary": {"type": "string"}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    t = ctx.outputs["procedure_result"]["totals"]
    return (f"Job {ctx.job_id}: report needed by {ctx.spec['deadline']}. Procedure totals: {t}. Schedule it.")


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    await s.say(f"Loading the lab board. Report needed by {ctx.spec['deadline']}.")
    st = await s.tool("get_lab_state", {})
    down = [f"{m}: {b['label']}" for m, bl in st["bookings"].items() for b in bl if b["kind"] == "downtime"]
    jobs = sum(1 for bl in st["bookings"].values() for b in bl if b["kind"] == "job")
    await s.say(f"{jobs} mock bookings and {len(down)} downtime windows ({'; '.join(down)}). Trying weekday cobot "
                "handling only first.")
    a = await s.tool("schedule_campaign", {"allow_saturday_handling": False})
    chosen = a
    b = await s.tool("schedule_campaign", {"allow_saturday_handling": True})
    gain = (date.fromisoformat(a["report_due"]) - date.fromisoformat(b["report_due"])).days
    if not a["on_time"] and b["report_due"] < a["report_due"]:
        chosen = b
    await s.say(f"{a['option_id']} (weekdays): last test {a['last_test_end'][:16].replace('T', ' ')}, report due "
                f"{a['report_due']}. {b['option_id']} (with Saturday handling) saves {gain} day(s). "
                + ("Saturday handling isn't needed to make the deadline, so I'm holding the weekday option. "
                   if chosen is a else "Saturday handling is needed to make the deadline. ")
                + f"{chosen['unattended_rig_hours']} h of bench rig time falls outside the supervised window and runs "
                  f"unattended; the cobot unloads at the next window. Makespan {chosen['makespan_days']} days, "
                  f"{chosen['slack_days']} days of slack against the {chosen['deadline']} deadline. Partner labs drive the "
                  "critical path. Bookings stay tentative until the engineer releases the campaign.")
    await s.tool("submit_schedule", {"option_id": chosen["option_id"],
                                     "summary": f"Report due {chosen['report_due']} vs deadline {chosen['deadline']} "
                                                f"({chosen['slack_days']:+d} days); {chosen['unattended_rig_hours']} h unattended."})


AGENT = AgentDef("scheduling", "Scheduling Agent", "Books rigs and the cobot", SYSTEM, TOOLS, build_task, scripted)
