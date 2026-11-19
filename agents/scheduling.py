"""Scheduling agent: books the job onto the factory cell around existing work and downtime."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from factory import db
from factory.scheduler import schedule

from .common import GROUND_RULES
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Scheduling Agent at an autonomous cold plate factory. The cell: CNC-1, CNC-2,
FSW-1, LEAK-1, running two shifts (06:00-22:00) Monday-Friday; CNCs can run Saturday on overtime.
The cell already has customer jobs and planned downtime booked.

1. Call get_factory_state to see machine bookings and downtime.
2. Call schedule_job to generate schedule options (finite capacity, non-preemptive, lot-based flow
   CNC -> FSW -> CNC post-weld -> leak test). Options can vary transfer lot size and Saturday overtime.
3. Pick the option that meets the customer deadline at the lowest disruption/cost (overtime only if
   needed), and hold it with submit_schedule. Bookings stay tentative until the engineer approves the job.

{GROUND_RULES}"""


def _factory_state(ctx: JobContext, _inp: dict) -> dict:
    bk = db.bookings()
    by_m: dict = defaultdict(list)
    for b in bk:
        by_m[b["machine_id"]].append({"label": b["label"], "kind": b["kind"], "start": b["start"], "end": b["end"]})
    return {"now": datetime.now().replace(microsecond=0).isoformat(), "machines": db.machines(),
            "bookings": dict(by_m), "shift": "06:00-22:00 Mon-Fri; CNC Saturday overtime optional"}


def _schedule(ctx: JobContext, inp: dict) -> dict:
    plan = ctx.outputs.get("process_plan_result")
    if not plan:
        raise ToolError("No process plan available")
    lot = int(inp.get("lot_size", 10))
    if not 1 <= lot <= 100:
        raise ToolError("lot_size must be 1-100")
    r = schedule(plan["operations"], int(ctx.spec["quantity"]), db.machines(), db.bookings(), datetime.now(),
                 date.fromisoformat(str(ctx.spec["deadline"])), lot_size=lot,
                 allow_saturday=bool(inp.get("allow_saturday_overtime", False)))
    oid = ctx.next_id("O")
    ctx.schedule_options[oid] = r
    return {"option_id": oid, **{k: v for k, v in r.items() if k != "operations"},
            "operations_count": len(r["operations"]),
            "first_operation": r["operations"][0], "last_operation": r["operations"][-1]}


def _submit(ctx: JobContext, inp: dict) -> dict:
    oid = inp["option_id"]
    if oid not in ctx.schedule_options:
        raise ToolError(f"Unknown option_id {oid}. Known: {sorted(ctx.schedule_options)}")
    r = ctx.schedule_options[oid]
    db.replace_tentative(ctx.job_id, [{"machine_id": o["machine_id"], "label": f"{ctx.job_id} {o['label']}",
                                       "start": o["start"], "end": o["end"]} for o in r["operations"]])
    ctx.outputs["scheduling"] = inp
    ctx.outputs["schedule_result"] = r
    return {"held": True, "bookings": len(r["operations"]), "delivery_date": r["delivery_date"]}


TOOLS = [
    Tool("get_factory_state", "List machines and all current bookings and downtime on the cell.",
         {"type": "object", "properties": {}, "additionalProperties": False}, _factory_state),
    Tool("schedule_job", "Compute a finite-capacity schedule option for this job (does not book it). "
         "Returns option_id, delivery date vs deadline, slack, makespan and machine load.",
         {"type": "object", "additionalProperties": False, "required": ["lot_size", "allow_saturday_overtime"],
          "properties": {"lot_size": {"type": "integer", "description": "Transfer lot size (pieces), e.g. 10"},
                         "allow_saturday_overtime": {"type": "boolean"}}}, _schedule),
    Tool("submit_schedule", "Hold the chosen option as tentative bookings on the cell. Ends your turn.",
         {"type": "object", "additionalProperties": False, "required": ["option_id", "summary"],
          "properties": {"option_id": {"type": "string"}, "summary": {"type": "string"}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    p = ctx.outputs["process_plan_result"]
    return (f"Job {ctx.job_id}: {ctx.spec['quantity']} pcs, customer deadline {ctx.spec['deadline']}.\n"
            f"Per-part minutes by station: {p['minutes_per_part_by_station']}. Schedule it.")


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    await s.say(f"Loading the cell board. {ctx.spec['quantity']} pcs due {ctx.spec['deadline']}.")
    st = await s.tool("get_factory_state", {})
    down = [f"{m}: {b['label']}" for m, bl in st["bookings"].items() for b in bl if b["kind"] == "downtime"]
    jobs = sum(1 for bl in st["bookings"].values() for b in bl if b["kind"] == "job")
    await s.say(f"{jobs} existing job bookings and {len(down)} downtime windows on the cell ({'; '.join(down)}). "
                "Trying lots of 10 on standard shifts first.")
    a = await s.tool("schedule_job", {"lot_size": 10, "allow_saturday_overtime": False})
    chosen = a
    if not a["on_time"]:
        await s.say(f"Option {a['option_id']} delivers {a['delivery_date']}, {-a['slack_days']} days late. Trying "
                    "Saturday CNC overtime with smaller lots to pull it in.")
        b = await s.tool("schedule_job", {"lot_size": 5, "allow_saturday_overtime": True})
        chosen = b if b["delivery_date"] < a["delivery_date"] else a
    else:
        b = await s.tool("schedule_job", {"lot_size": 5, "allow_saturday_overtime": False})
        if b["delivery_date"] < a["delivery_date"]:
            chosen = b
        await s.say(f"{a['option_id']} (lots of 10): delivery {a['delivery_date']}; {b['option_id']} (lots of 5): "
                    f"{b['delivery_date']}. Smaller lots mean more setups but get the FSW and leak rig started sooner. "
                    f"No overtime needed.")
    await s.say(f"Holding {chosen['option_id']}: release {chosen['release'][:16].replace('T', ' ')}, production complete "
                f"{chosen['production_complete'][:16].replace('T', ' ')}, ships {chosen['ship_date']}, delivered "
                f"{chosen['delivery_date']}: {chosen['slack_days']} days of slack against the {chosen['deadline']} deadline. "
                "Bookings are tentative until engineer sign-off.")
    await s.tool("submit_schedule", {"option_id": chosen["option_id"],
                                     "summary": f"Delivery {chosen['delivery_date']} vs deadline {chosen['deadline']} "
                                                f"({chosen['slack_days']:+d} days), lots of {chosen['lot_size']}."})


AGENT = AgentDef("scheduling", "Scheduling Agent", "Books the factory cell", SYSTEM, TOOLS, build_task, scripted)
