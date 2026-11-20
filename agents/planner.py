"""Campaign Planner agent: turns a component spec and target standard into a test campaign."""
from __future__ import annotations

import json

from testlab.campaign import build_campaign, known_tests
from testlab.methods import describe_methods
from testlab.standards import get_standard

from .common import GROUND_RULES, get_campaign, standard_id
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Campaign Planner Agent at Loopwerks, an autonomous test lab for liquid cooling
components. You turn a validated component spec and its target standard into a test campaign: which tests,
on which sample, in what order, with what parameters. A campaign is a list of steps; each step names a
sample_id (S1, S2, ...), a test and its parameters. Step order within a sample is the test sequence.
Different samples run in parallel.

Process:
1. Call get_standard for the target standard and list_test_methods to see where each test runs
   (bench rig, hired instrument, university metrology, or a partner lab that is not yet contracted).
2. Draft the campaign with draft_campaign. Cover every mandatory requirement. Choose parameters inside the
   standard's ranges. Respect the sequence rules. Spread long partner tests across samples so they run in
   parallel, and keep within the number of samples the customer supplies.
3. Call submit_campaign with the campaign_id and your rationale.

The Verification Agent independently checks your campaign against the standard and will reject it with
reasons if it falls short. You do not have its tool. If it rejects, its findings will be in your task:
address every finding explicitly in response_to_verification.

{GROUND_RULES}"""

STEP_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["sample_id", "test"],
               "properties": {"sample_id": {"type": "string"}, "test": {"type": "string", "enum": known_tests()},
                              "params": {"type": "object"}}}


def _get_standard(ctx: JobContext, inp: dict) -> dict:
    try:
        return get_standard(inp["standard_id"])
    except KeyError as e:
        raise ToolError(str(e)) from e


def _methods(ctx: JobContext, _inp: dict) -> dict:
    return {"methods": describe_methods(),
            "notes": "Bench and hired tests are loaded and connected by the cobot. Partner labs are planned, not "
                     "contracted, and add 2 working days of shipping each way."}


def _draft(ctx: JobContext, inp: dict) -> dict:
    try:
        c = build_campaign(inp, ctx.spec, standard_id(ctx))
    except (KeyError, ValueError) as e:
        raise ToolError(str(e)) from e
    cid = ctx.next_id("C")
    c["campaign_id"] = cid
    ctx.campaigns[cid] = c
    return {"campaign_id": cid, "label": c["label"], "totals": c["totals"], "sample_sequences": c["sample_sequences"],
            "steps": [{k: s[k] for k in ("step_id", "sample_id", "test", "params", "resource", "where", "run_minutes",
                                         "acceptance")} for s in c["steps"]]}


def _submit(ctx: JobContext, inp: dict) -> dict:
    get_campaign(ctx, inp["campaign_id"])
    ctx.outputs["planner"] = inp
    return {"recorded": True, "selected": inp["campaign_id"]}


def campaign_artifact(ctx: JobContext) -> tuple[str, dict]:
    return "campaigns", {"campaigns": list(ctx.campaigns.values()), "standard": get_standard(standard_id(ctx))}


TOOLS = [
    Tool("get_standard", "Return the requirement catalogue for a standard: requirement ids, the test each maps to, "
         "the rule, machine-checkable parameter ranges, and the sequence rules. It is a planning summary, not the "
         "specification text.",
         {"type": "object", "additionalProperties": False, "required": ["standard_id"],
          "properties": {"standard_id": {"type": "string"}}}, _get_standard),
    Tool("list_test_methods", "List every test method: resource, where it runs, whether it is destructive, default "
         "parameters and nominal duration.",
         {"type": "object", "properties": {}, "additionalProperties": False}, _methods),
    Tool("draft_campaign", "Build a campaign from steps. Returns a campaign_id, per-step resource, duration and "
         "acceptance criterion, and totals. Does not check it against the standard.",
         {"type": "object", "additionalProperties": False, "required": ["label", "steps"],
          "properties": {"label": {"type": "string"}, "steps": {"type": "array", "items": STEP_SCHEMA}}},
         _draft, artifact=campaign_artifact),
    Tool("submit_campaign", "Submit a campaign for verification. Ends your turn.",
         {"type": "object", "additionalProperties": False,
          "required": ["campaign_id", "rationale", "response_to_verification"],
          "properties": {"campaign_id": {"type": "string"}, "rationale": {"type": "string"},
                         "response_to_verification": {"type": "string",
                                                      "description": "How each finding was addressed; empty on first submission"}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    parts = ["Validated spec:\n```json\n" + json.dumps(ctx.spec, indent=1, default=str) + "\n```",
             "Derived by intake: " + json.dumps(ctx.outputs["intake_check"]["derived"], default=str),
             f"Target standard: {standard_id(ctx)}. Intake summary: {ctx.outputs['intake']['summary']}"]
    if ctx.verification_feedback:
        last = ctx.verification_feedback[-1]
        parts.append(f"REWORK REQUEST #{len(ctx.verification_feedback)} from the Verification Agent. Campaign "
                     f"{last['campaign_id']} was REJECTED.\nFindings: " + json.dumps(last["failures"])
                     + "\nRequired changes: " + json.dumps(last["required_changes"])
                     + "\nDraft a revised campaign that clears every finding, then submit it.")
    else:
        parts.append("Plan and submit the campaign.")
    return "\n\n".join(parts)


# --- scripted policy ----------------------------------------------------------------------------

def first_plan(spec: dict) -> list[dict]:
    """A plausible first draft that saves a sample and rig time, with three real mistakes in it."""
    q = float(spec["rated_flow_lpm"])
    return [
        {"sample_id": "S1", "test": "cleanliness"},
        {"sample_id": "S1", "test": "pressure_decay", "params": {"hold_min": 15}},
        {"sample_id": "S1", "test": "hydrostatic"},
        {"sample_id": "S1", "test": "pressure_drop", "params": {"flows_lpm": [round(q * f, 3) for f in (1/3, 2/3, 1.0, 4/3)]}},
        {"sample_id": "S1", "test": "flow_rate"},
        {"sample_id": "S1", "test": "thermal_resistance", "params": {"inlet_c": 45, "power_levels": 3}},
        {"sample_id": "S1", "test": "flatness"},
        {"sample_id": "S2", "test": "helium_leak", "params": {"dwell_min": 10}},
        {"sample_id": "S2", "test": "non_op_temp_cycling", "params": {"dwell_h": 72}},
        {"sample_id": "S2", "test": "shock"},
        {"sample_id": "S2", "test": "vibration"},
        {"sample_id": "S3", "test": "op_temp_cycling", "params": {"dwell_h": 72}},
        {"sample_id": "S3", "test": "burst", "params": {"ramp_bar_min": 2, "target_bar": 40}},
        {"sample_id": "S3", "test": "retention_force"},
        {"sample_id": "S3", "test": "stiffness"},
        {"sample_id": "S4", "test": "salt_spray", "params": {"hours": 8}},
        {"sample_id": "S4", "test": "humidity", "params": {"hours_each": 16}},
        {"sample_id": "S4", "test": "fluid_compatibility"},
    ]


def revise(steps: list[dict], failures: list[dict], spec: dict) -> tuple[list[dict], list[str]]:
    steps = [dict(s, params=dict(s.get("params") or {})) for s in steps]
    done = []
    q = float(spec["rated_flow_lpm"])
    for f in failures:
        name = f["check"]
        if name.startswith("R06"):
            for s in steps:
                if s["test"] == "pressure_drop":
                    s["params"]["flows_lpm"] = [round(q * p / 100, 3) for p in (25, 50, 75, 100, 125, 150)]
            if "R06" not in done:
                done.append("R06")
        elif name.startswith("SEQ-1"):
            sid = name.split(" on ")[-1]
            k = next(i for i, s in enumerate(steps) if s["sample_id"] == sid and s["test"] == "non_op_temp_cycling")
            steps.insert(k + 1, {"sample_id": sid, "test": "helium_leak", "params": {"dwell_min": 10}})
            done.append("SEQ-1")
        elif name.startswith("SEQ-2"):
            used = sorted({s["sample_id"] for s in steps})
            new = f"S{len(used) + 1}"
            for s in steps:
                if s["test"] == "burst":
                    s["sample_id"] = new
            steps = [s for s in steps if s["test"] != "burst"] + [s for s in steps if s["test"] == "burst"]
            done.append("SEQ-2")
        elif name.startswith(("R02", "R01")):
            for s in steps:
                if s["test"] == "pressure_decay":
                    s["params"]["hold_min"] = 15
                if s["test"] == "helium_leak":
                    s["params"]["dwell_min"] = 10
            done.append(name[:3])
    return steps, done


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    sid = standard_id(ctx)
    fb = ctx.verification_feedback
    if not fb:
        await s.say(f"Planning to {sid}. Pulling the requirement catalogue and the methods list first.")
        std = await s.tool("get_standard", {"standard_id": sid})
        await s.tool("list_test_methods", {})
        await s.say(f"{len(std['requirements'])} mandatory requirements and {len(std['sequence_rules'])} sequence rules. "
                    "Bench work (leak, hydrostatic, flow, thermal) goes on one sample so the cobot can chain it. The long "
                    "partner tests (temperature cycling, salt spray, humidity, fluid chemistry) get their own samples so "
                    "they run in parallel. I'm trying to keep to four samples to leave the customer a spare.")
        c = await s.tool("draft_campaign", {"label": "Campaign v1 (4 samples)", "steps": first_plan(ctx.spec)})
        t = c["totals"]
        await s.say(f"{c['campaign_id']}: {t['steps']} steps on {t['samples_used']} samples, {t['requirements_covered']}/"
                    f"{t['requirements_total']} requirements covered, {t['bench_hours']} h of bench time and "
                    f"{t['partner_hours']} h at partner labs. Burst shares S3 with the in-loop cycling to save a sample.")
        await s.tool("submit_campaign", {"campaign_id": c["campaign_id"], "response_to_verification": "",
                                         "rationale": f"Covers {t['requirements_covered']} of {t['requirements_total']} "
                                                      f"requirements on {t['samples_used']} samples; partner tests in "
                                                      "parallel lanes."})
        return

    last = fb[-1]
    prev = get_campaign(ctx, last["campaign_id"])
    prev_steps = [{"sample_id": x["sample_id"], "test": x["test"], "params": x["params"]} for x in prev["steps"]]
    steps, fixed = revise(prev_steps, last["failures"], ctx.spec)
    reasons = "; ".join(f"{f['check']}: {f['value']} vs {f['limit']}" for f in last["failures"])
    await s.say(f"Rejected for: {reasons}. Each finding is fair. Fixes: pressure drop now runs six points from 25 % to "
                "150 % of rated flow; S2 gets a second helium leak test after the shipping cycle so the cycle is "
                "bracketed; burst moves to its own sample, which uses the fifth sample the customer is sending.")
    c = await s.tool("draft_campaign", {"label": f"Campaign v{len(fb) + 1}", "steps": steps})
    t = c["totals"]
    await s.say(f"{c['campaign_id']}: {t['steps']} steps on {t['samples_used']} samples, {t['requirements_covered']}/"
                f"{t['requirements_total']} requirements, {t['bench_hours']} h bench. Submitting for re-check.")
    await s.tool("submit_campaign", {"campaign_id": c["campaign_id"],
                                     "rationale": f"v{len(fb) + 1}: same coverage, findings {', '.join(fixed)} cleared.",
                                     "response_to_verification": f"Findings: {reasons}. Changes: "
                                     + "; ".join({"R06": "six dP points at 25 to 150 % of rated flow",
                                                  "SEQ-1": "helium leak added after shipping cycling on S2",
                                                  "SEQ-2": "burst moved to a dedicated last sample",
                                                  "R01": "helium dwell set to 10 min",
                                                  "R02": "decay hold set to 15 min"}.get(x, x) for x in fixed) + "."})


AGENT = AgentDef("planner", "Campaign Planner Agent", "Plans the test campaign", SYSTEM, TOOLS, build_task,
                 scripted, effort_env="PLANNER_AGENT_EFFORT")
