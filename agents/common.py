"""Shared helpers for agent modules."""
from __future__ import annotations

import json

from .core import JobContext, ToolError

GROUND_RULES = """
Ground rules (non-negotiable):
- Every number you state (pressures, durations, flows, dates, costs) must come from a tool result in this
  conversation. Never estimate, extrapolate or invent a figure yourself.
- The standard catalogue is a planning summary, not the specification text. Say so when it matters, and never
  claim certification, accreditation or compliance. Loopwerks is not a certification body.
- The rigs are not built yet. Results in this demo are simulated and must be called simulated.
- Be concise and specific, like a test engineer writing in a lab log: short paragraphs, units always,
  no marketing language.
- Finish by calling your submit tool exactly once.
""".strip()


def get_campaign(ctx: JobContext, campaign_id: str) -> dict:
    if campaign_id not in ctx.campaigns:
        raise ToolError(f"Unknown campaign_id '{campaign_id}'. Known: {sorted(ctx.campaigns)}")
    return ctx.campaigns[campaign_id]


def spec_json(ctx: JobContext) -> str:
    return json.dumps(ctx.spec, indent=1, default=str)


def standard_id(ctx: JobContext) -> str:
    return ctx.outputs["intake_check"]["plannable_standards"][0]


def campaign_brief(ctx: JobContext, campaign_id: str) -> dict:
    c = get_campaign(ctx, campaign_id)
    return {"campaign_id": campaign_id, "label": c["label"], "standard": c["standard"], "totals": c["totals"],
            "sample_sequences": {sid: [f"{s} {next(x['test'] for x in c['steps'] if x['step_id'] == s)}" for s in seq]
                                 for sid, seq in c["sample_sequences"].items()}}
