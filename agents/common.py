"""Shared helpers for agent modules."""
from __future__ import annotations

import json

from engineering.design import OperatingPoint

from .core import JobContext, ToolError

GROUND_RULES = """
Ground rules (non-negotiable):
- Every number you state (temperatures, pressures, times, costs, dates) must come from a tool result
  in this conversation. Never estimate, extrapolate or invent a figure yourself.
- Tools are deterministic engineering models; trust them over intuition, but say so when an
  assumption in a tool matters for the decision.
- Be concise and specific, like an experienced engineer writing in a design review log:
  short paragraphs, units always, no marketing language.
- Finish by calling your submit tool exactly once.
""".strip()


def op_point(ctx: JobContext, **overrides) -> OperatingPoint:
    s = ctx.spec
    kw = dict(power_w=float(s["tdp_w"]), source_length_mm=float(s["heat_source_length_mm"]),
              source_width_mm=float(s["heat_source_width_mm"]), inlet_c=float(s["inlet_temp_c"]),
              coolant=s["coolant"], flow_lpm=float(s["flow_rate_lpm"]),
              tim_r_cm2k_w=float(s.get("tim_resistance_cm2k_w", 0.08)))
    kw.update(overrides)
    return OperatingPoint(**kw)


def default_geometry(ctx: JobContext) -> dict:
    """Default plate envelope sized around the heat source (field covers the source)."""
    s = ctx.spec
    field_l = round(float(s["heat_source_length_mm"]) + 5)
    field_w = round(float(s["heat_source_width_mm"]) + 10)
    return {"field_length_mm": field_l, "field_width_mm": field_w,
            "plate_length_mm": field_l + 30, "plate_width_mm": field_w + 25,
            "base_thickness_mm": 1.5, "lid_thickness_mm": 3.0, "port_diameter_mm": 8.0,
            "material": "Al6061" if str(s.get("material_preference", "copper")).lower().startswith("al") else "C110"}


def get_design(ctx: JobContext, design_id: str) -> dict:
    if design_id not in ctx.designs:
        raise ToolError(f"Unknown design_id '{design_id}'. Known: {sorted(ctx.designs)}")
    return ctx.designs[design_id]


def spec_json(ctx: JobContext) -> str:
    return json.dumps(ctx.spec, indent=1, default=str)


def design_brief(ctx: JobContext, design_id: str) -> dict:
    d = get_design(ctx, design_id)
    r = d["result"]
    return {"design_id": design_id, "label": d.get("label"), "params": d["params"],
            "t_case_c": r["thermal"]["t_case_c"], "dp_kpa": r["hydraulics"]["dp_kpa"],
            "r_case_to_inlet_k_w": r["thermal"]["r_case_to_inlet_k_w"], "geometry": r["geometry"]}
