"""Thermal design agent: proposes candidate topologies, evaluates, iterates parameters, selects one."""
from __future__ import annotations

import itertools
import json

from engineering.design import DesignParams, evaluate_design, check_against_limits

from .common import GROUND_RULES, default_geometry, op_point, get_design
from .core import AgentDef, JobContext, ScriptedSession, Tool, ToolError

SYSTEM = f"""You are the Thermal Design Agent at an autonomous cold plate factory. You turn a validated
chip spec into a cold plate design, represented purely as a parameter set (no CAD; a human engineer
models the CAD from your parameters).

Topologies available (all CNC-machined copper or aluminium base with a friction-stir-welded lid):
- straight_microchannel: parallel channels cut with a gang slitting saw. Params: channel_width_mm,
  fin_thickness_mm, channel_depth_mm. Typical: width 0.2-0.5, fin 0.2-0.4, depth 1.5-4.
- pin_fin: staggered pin array, end-milled. Params: pin_diameter_mm, pin_pitch_transverse_mm,
  pin_pitch_longitudinal_mm, channel_depth_mm (pin height). Typical D 1-2, pitch 2-3.5.
- serpentine: one or more serpentine paths, end-milled. Params: channel_width_mm, fin_thickness_mm (rib),
  parallel_paths, channel_depth_mm. Typical width 1-3.
Shared params (defaults are given in the task): material (C110 copper or Al6061), base_thickness_mm,
field_length_mm / field_width_mm (finned area; must cover the heat source), plate_length_mm / plate_width_mm,
lid_thickness_mm, port_diameter_mm.

Process:
1. Propose 2-3 candidate designs spanning different topologies and evaluate each with evaluate_design.
2. Use parametric_sweep to explore the most promising topology, then evaluate_design on the designs you
   are seriously considering (only evaluated designs get a design_id).
3. Pick one design that meets the spec limits and explain the trade-off against the alternatives
   (thermal margin, pressure-drop margin, flow regime, manufacturability, cost).
4. Call submit_design with the selected design_id and the candidate ids you compared.

The Verification Agent will independently re-check your design against the spec under the factory's
worst-case standard (flow and manufacturing tolerances, TIM ageing, fouling) and the cell's DFM limits.
You do not have those tools. If it rejects your design, its reasons will be in your task; address every
reason explicitly in response_to_verification.

{GROUND_RULES}"""

DESIGN_PROPS = {
    "label": {"type": "string", "description": "Short human label, e.g. 'Microchannel 0.25/0.20'"},
    "topology": {"type": "string", "enum": ["straight_microchannel", "pin_fin", "serpentine"]},
    "material": {"type": "string", "enum": ["C110", "Al6061"]},
    "channel_width_mm": {"type": "number"}, "fin_thickness_mm": {"type": "number"},
    "channel_depth_mm": {"type": "number"}, "parallel_paths": {"type": "integer"},
    "pin_diameter_mm": {"type": "number"}, "pin_pitch_transverse_mm": {"type": "number"},
    "pin_pitch_longitudinal_mm": {"type": "number"},
    "base_thickness_mm": {"type": "number"}, "field_length_mm": {"type": "number"},
    "field_width_mm": {"type": "number"}, "plate_length_mm": {"type": "number"},
    "plate_width_mm": {"type": "number"}, "lid_thickness_mm": {"type": "number"},
    "port_diameter_mm": {"type": "number"},
}
SWEEPABLE = ["channel_width_mm", "fin_thickness_mm", "channel_depth_mm", "parallel_paths", "pin_diameter_mm",
             "pin_pitch_transverse_mm", "pin_pitch_longitudinal_mm", "base_thickness_mm"]
MAX_COMBOS = 400


def _params(ctx: JobContext, inp: dict) -> dict:
    p = {**default_geometry(ctx), **{k: v for k, v in inp.items() if k != "label" and v is not None}}
    return DesignParams.from_dict(p).to_dict()


def _limits(ctx: JobContext) -> tuple[float, float]:
    return float(ctx.spec["max_case_temp_c"]), float(ctx.spec["max_pressure_drop_kpa"])


def _summary(design_id: str, label: str, r: dict, lim: dict) -> dict:
    g, h, t, ht = r["geometry"], r["hydraulics"], r["thermal"], r["heat_transfer"]
    out = {
        "design_id": design_id, "label": label, "params": r["design"],
        "meets_nominal_limits": lim["meets_all"],
        "t_case_c": t["t_case_c"], "thermal_margin_c": lim["thermal_margin_c"],
        "dp_kpa": h["dp_kpa"], "dp_margin_kpa": lim["dp_margin_kpa"],
        "r_case_to_inlet_k_w": t["r_case_to_inlet_k_w"],
        "dt_breakdown_c": t["dt_breakdown_c"], "dp_breakdown_kpa": h["dp_breakdown_kpa"],
        "velocity_m_s": h["velocity_m_s"], "reynolds": h["reynolds"], "regime": h["regime"],
        "h_w_m2k": ht["h_w_m2k"], "fin_efficiency": ht["fin_efficiency"],
        "area_enhancement": g["area_enhancement"], "outlet_c": t["t_outlet_c"], "mass_kg": r["mass_kg"],
    }
    for k in ("channel_count", "pitch_mm", "pin_count", "passes_per_path"):
        if k in g:
            out[k] = g[k]
    return out


def _evaluate(ctx: JobContext, inp: dict) -> dict:
    params = _params(ctx, inp)
    r = evaluate_design(params, op_point(ctx))
    lim = check_against_limits(r, *_limits(ctx))
    did = ctx.next_id("D")
    label = inp.get("label") or f"{params['topology']} {did}"
    ctx.designs[did] = {"params": params, "result": r, "label": label, "limits": lim}
    summary = _summary(did, label, r, lim)
    ctx.artifacts.setdefault("design_candidates", [])
    ctx.artifacts["design_candidates"].append({**summary, "full": r})
    return summary


def _sweep(ctx: JobContext, inp: dict) -> dict:
    topo = inp.get("topology")
    sweep = inp.get("sweep") or {}
    if not sweep:
        raise ToolError("sweep must map at least one parameter to a list of values")
    for k, vals in sweep.items():
        if k not in SWEEPABLE:
            raise ToolError(f"cannot sweep '{k}'. Sweepable: {SWEEPABLE}")
        if not isinstance(vals, list) or not vals:
            raise ToolError(f"sweep['{k}'] must be a non-empty list")
    keys = list(sweep)
    combos = list(itertools.product(*(sweep[k] for k in keys)))
    if len(combos) > MAX_COMBOS:
        raise ToolError(f"{len(combos)} combinations exceeds the limit of {MAX_COMBOS}")
    fixed = {k: v for k, v in (inp.get("fixed") or {}).items() if k in DESIGN_PROPS and k != "label"}
    cons = inp.get("constraints") or {}
    t_max, dp_max = _limits(ctx)
    dp_cap = dp_max * float(cons.get("max_dp_fraction", 1.0))
    op = op_point(ctx)
    points, feasible, skipped = [], [], 0
    for combo in combos:
        p = {"topology": topo, **fixed, **dict(zip(keys, combo))}
        H = p.get("channel_depth_mm", default_geometry(ctx).get("channel_depth_mm", 3.0)) or 3.0
        if "max_depth_to_width" in cons and p.get("channel_width_mm") and H / p["channel_width_mm"] > cons["max_depth_to_width"]:
            skipped += 1
            continue
        if ("max_fin_height_to_thickness" in cons and p.get("fin_thickness_mm")
                and H / p["fin_thickness_mm"] > cons["max_fin_height_to_thickness"]):
            skipped += 1
            continue
        try:
            params = _params(ctx, p)
            r = evaluate_design(params, op)
        except ValueError:
            skipped += 1
            continue
        t, dp = r["thermal"]["t_case_c"], r["hydraulics"]["dp_kpa"]
        ok = dp <= dp_cap and t <= t_max - float(cons.get("min_thermal_margin_c", 0.0))
        point = {"params": {k: params[k] for k in keys}, "t_case_c": t, "dp_kpa": dp,
                 "velocity_m_s": r["hydraulics"]["velocity_m_s"], "meets_constraints": ok}
        points.append(point)
        if ok:
            feasible.append(point)
    feasible.sort(key=lambda x: x["t_case_c"])
    top_n = int(inp.get("top_n", 6))
    sweep_id = ctx.next_id("S")
    ctx.artifacts.setdefault("sweeps", []).append({"sweep_id": sweep_id, "topology": topo, "swept": keys,
                                                   "constraints": cons, "t_max": t_max, "dp_cap": dp_cap,
                                                   "points": points})
    return {"sweep_id": sweep_id, "evaluated": len(points), "skipped_by_constraints_or_invalid": skipped,
            "meeting_constraints": len(feasible), "best_by_case_temperature": feasible[:top_n],
            "note": "Sweep results are not design_ids; call evaluate_design on a design before selecting it."}


def _submit(ctx: JobContext, inp: dict) -> dict:
    sel = get_design(ctx, inp["selected_design_id"])
    for c in inp["candidate_design_ids"]:
        get_design(ctx, c)
    if not sel["limits"]["meets_all"]:
        raise ToolError("Selected design does not meet the nominal spec limits per evaluate_design.")
    topologies = {ctx.designs[c]["params"]["topology"] for c in inp["candidate_design_ids"] + [inp["selected_design_id"]]}
    if not ctx.verification_feedback and len(topologies) < 2:
        raise ToolError("First submission must compare candidates from at least 2 topologies.")
    ctx.outputs["thermal_design"] = inp
    return {"recorded": True, "selected": inp["selected_design_id"]}


def design_space_artifact(ctx: JobContext) -> tuple[str, dict]:
    t_max, dp_max = _limits(ctx)
    return "design_space", {
        "t_max": t_max, "dp_max": dp_max,
        "candidates": [{k: v for k, v in c.items() if k != "full"} for c in ctx.artifacts.get("design_candidates", [])],
        "points": [p for sw in ctx.artifacts.get("sweeps", []) for p in sw["points"]],
        "sweeps": [{k: v for k, v in sw.items() if k != "points"} | {"n": len(sw["points"])}
                   for sw in ctx.artifacts.get("sweeps", [])],
    }


TOOLS = [
    Tool("evaluate_design",
         "Evaluate one cold plate parameter set with the deterministic thermal/hydraulic models "
         "(Shah-London laminar / Gnielinski turbulent convection, fin efficiency, Zukauskas pin banks, "
         "Darcy-Weisbach + minor losses, Lee spreading resistance, 1-D resistance network incl. TIM2 and "
         "coolant temperature rise). Unspecified shared parameters use the defaults from the task. "
         "Returns a design_id plus case temperature, pressure drop, margins and breakdowns.",
         {"type": "object", "properties": DESIGN_PROPS, "required": ["label", "topology"],
          "additionalProperties": False}, _evaluate, artifact=design_space_artifact),
    Tool("parametric_sweep",
         "Evaluate a grid of parameter combinations for one topology (max 400 combos) and return the best "
         "designs by case temperature that satisfy the constraints. Constraints are optional: "
         "max_dp_fraction (fraction of the spec dP limit, default 1.0), min_thermal_margin_c, "
         "max_depth_to_width, max_fin_height_to_thickness.",
         {"type": "object", "additionalProperties": False, "required": ["topology", "sweep"],
          "properties": {
              "topology": {"type": "string", "enum": ["straight_microchannel", "pin_fin", "serpentine"]},
              "fixed": {"type": "object", "description": "Parameters held constant (same names as evaluate_design)"},
              "sweep": {"type": "object", "description": "Parameter name -> list of values"},
              "constraints": {"type": "object", "properties": {
                  "max_dp_fraction": {"type": "number"}, "min_thermal_margin_c": {"type": "number"},
                  "max_depth_to_width": {"type": "number"}, "max_fin_height_to_thickness": {"type": "number"}}},
              "top_n": {"type": "integer"}}}, _sweep, artifact=design_space_artifact),
    Tool("submit_design", "Submit the selected design for verification. Ends your turn.",
         {"type": "object", "additionalProperties": False,
          "required": ["selected_design_id", "candidate_design_ids", "rationale", "response_to_verification"],
          "properties": {
              "selected_design_id": {"type": "string"},
              "candidate_design_ids": {"type": "array", "items": {"type": "string"},
                                       "description": "All design_ids you compared, including rejected ones"},
              "rationale": {"type": "string", "description": "Why this design over the alternatives (cite tool numbers)"},
              "response_to_verification": {"type": "string",
                                           "description": "How each verification finding was addressed; empty string on first submission"}}},
         _submit, terminal=True),
]


def build_task(ctx: JobContext) -> str:
    s = ctx.spec
    intake = ctx.outputs.get("intake_check", {}).get("derived", {})
    parts = [
        "Validated spec:\n```json\n" + json.dumps(s, indent=1, default=str) + "\n```",
        "Derived by intake tools: " + json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                                                  for k, v in intake.items()}),
        "Default shared parameters: " + json.dumps(default_geometry(ctx)),
    ]
    if ctx.verification_feedback:
        last = ctx.verification_feedback[-1]
        prior = ctx.outputs.get("thermal_design", {})
        parts.append(f"REWORK REQUEST #{len(ctx.verification_feedback)} from the Verification Agent. Your previous "
                     f"selection {prior.get('selected_design_id')} was REJECTED.\nFindings: "
                     + json.dumps(last["failures"]) + "\nVerifier summary: " + last["summary"]
                     + "\nRequired changes: " + json.dumps(last["required_changes"])
                     + f"\nDesigns evaluated so far: {sorted(ctx.designs)}. Revise the design to clear every finding "
                       "with margin, then submit again.")
    else:
        parts.append("Produce and submit a design.")
    return "\n\n".join(parts)


# --- scripted policy ----------------------------------------------------------------------

BASELINES = [
    {"label": "A: Straight microchannel 0.30/0.25 x 3.0", "topology": "straight_microchannel",
     "channel_width_mm": 0.30, "fin_thickness_mm": 0.25, "channel_depth_mm": 3.0},
    {"label": "B: Pin fin D1.5 staggered 3.0/2.6", "topology": "pin_fin", "pin_diameter_mm": 1.5,
     "pin_pitch_transverse_mm": 3.0, "pin_pitch_longitudinal_mm": 2.6, "channel_depth_mm": 3.0},
    {"label": "C: Serpentine 4-path 1.2 x 3.0", "topology": "serpentine", "channel_width_mm": 1.2,
     "fin_thickness_mm": 0.8, "parallel_paths": 4, "channel_depth_mm": 3.0},
]
MICRO_SWEEP = {"channel_width_mm": [0.20, 0.25, 0.30, 0.35], "fin_thickness_mm": [0.20, 0.25],
               "channel_depth_mm": [2.0, 2.5, 3.0]}


def _cons_text(cons: dict) -> str:
    parts = []
    if cons.get("max_dp_fraction", 1.0) < 1.0:
        parts.append(f"nominal dP <= {cons['max_dp_fraction']:.0%} of the limit")
    if "max_depth_to_width" in cons:
        parts.append(f"depth/width <= {cons['max_depth_to_width']:g}:1")
    if "max_fin_height_to_thickness" in cons:
        parts.append(f"fin height/thickness <= {cons['max_fin_height_to_thickness']:g}:1")
    if "min_thermal_margin_c" in cons:
        parts.append(f"nominal thermal margin >= {cons['min_thermal_margin_c']:g} degC")
    return ", ".join(parts) or "nominal limits only"


def _fmt(r: dict) -> str:
    return f"{r['t_case_c']:.1f} degC case / {r['dp_kpa']:.1f} kPa"


async def scripted(s: ScriptedSession) -> None:
    ctx = s.ctx
    t_max, dp_max = _limits(ctx)
    fb = ctx.verification_feedback
    if not fb:
        await s.say(f"Budget: case <= {t_max:g} degC and dP <= {dp_max:g} kPa at {ctx.spec['flow_rate_lpm']} L/min "
                    f"{ctx.spec['coolant']}. Starting with three topologies to see where each one lands: a fine-pitch "
                    "straight microchannel, a staggered pin-fin array and a 4-path serpentine.")
        res = [await s.tool("evaluate_design", b) for b in BASELINES]
        a, b, c = res
        lines = []
        for r in res:
            verdict = "meets nominal limits" if r["meets_nominal_limits"] else (
                "too hot" if r["thermal_margin_c"] < 0 else "") + (
                " and " if r["thermal_margin_c"] < 0 and r["dp_margin_kpa"] < 0 else "") + (
                "over the dP limit" if r["dp_margin_kpa"] < 0 else "")
            lines.append(f"{r['design_id']} {r['label'].split(':')[0]}: {_fmt(r)}, {r['regime']} Re {r['reynolds']:.0f} - {verdict}")
        await s.say("Results: " + "; ".join(lines) + ". "
                    f"The pin fin gets only {b['area_enhancement']:.1f}x area enhancement against "
                    f"{a['area_enhancement']:.1f}x for the microchannels, so convection dominates its stack. The serpentine runs "
                    f"{c['regime']} at {c['velocity_m_s']:.1f} m/s and spends {c['dp_breakdown_kpa'].get('bends_180deg', 0):.1f} kPa "
                    f"in the 180-degree bends alone, yet with only {c['area_enhancement']:.1f}x area it is still "
                    f"{'too hot' if c['thermal_margin_c'] < 0 else 'marginal'}. The microchannel is the only "
                    "topology near budget, so I'm sweeping its geometry.")
        sw = await s.tool("parametric_sweep", {"topology": "straight_microchannel", "sweep": MICRO_SWEEP,
                                               "constraints": {"max_dp_fraction": 1.0}})
        best = sw["best_by_case_temperature"][0]["params"]
        await s.say(f"Sweep {sw['sweep_id']}: {sw['evaluated']} variants, {sw['meeting_constraints']} within the dP limit. "
                    f"Coolest is {best['channel_width_mm']:.2f} mm channels / {best['fin_thickness_mm']:.2f} mm fins / "
                    f"{best['channel_depth_mm']:.1f} mm deep. Narrower channels raise h faster than they raise dP while "
                    "the flow stays laminar. Evaluating it formally.")
        chosen = await s.tool("evaluate_design", {"label": f"A2: Microchannel {best['channel_width_mm']:.2f}/"
                                                           f"{best['fin_thickness_mm']:.2f} x {best['channel_depth_mm']:.1f}",
                                                  "topology": "straight_microchannel", **best})
        await s.tool("submit_design", {
            "selected_design_id": chosen["design_id"],
            "candidate_design_ids": [r["design_id"] for r in res],
            "rationale": f"{chosen['design_id']} gives the best thermal margin ({chosen['thermal_margin_c']:.1f} degC) with "
                         f"dP {chosen['dp_kpa']:.1f} kPa inside the {dp_max:g} kPa limit. Pin fin misses the temperature "
                         f"limit; serpentine misses dP by a wide margin.",
            "response_to_verification": ""})
        await s.say(f"Submitting {chosen['design_id']} ({_fmt(chosen)}, {chosen.get('channel_count')} channels) "
                    "to the Verification Agent.")
        return

    # Rework: translate each verification finding into a sweep constraint.
    cons: dict = {"max_dp_fraction": 1.0}
    for f in fb:  # accumulate everything learned across all rejections
        for item in f["failures"]:
            name = item["check"]
            if "Channel depth / width" in name:
                cons["max_depth_to_width"] = item["limit"]
            elif "Fin height / thickness" in name:
                cons["max_fin_height_to_thickness"] = item["limit"]
            elif name.startswith("Pressure drop, worst case"):
                cons["max_dp_fraction"] = min(cons["max_dp_fraction"], 0.65)
            elif name.startswith("Case temperature, worst case"):
                cons["min_thermal_margin_c"] = max(cons.get("min_thermal_margin_c", 0), 2.5)
            elif "velocity" in name.lower():
                cons["max_dp_fraction"] = min(cons["max_dp_fraction"], 0.5)
    last = fb[-1]
    reasons = "; ".join(f"{i['check']} = {i['value']} vs limit {i['limit']}" for i in last["failures"])
    await s.say(f"Verification rejected the design: {reasons}. Fair. I optimised on nominal performance and left "
                "no margin for what they check. Re-running the sweep with those findings turned into hard constraints: "
                + _cons_text(cons) + ".")
    sweep = {**MICRO_SWEEP, "channel_depth_mm": [2.0, 2.4, 2.5, 3.0, 3.5]}
    sw = await s.tool("parametric_sweep", {"topology": "straight_microchannel", "sweep": sweep, "constraints": cons})
    if not sw["best_by_case_temperature"]:
        raise RuntimeError("no design satisfies the verification constraints")
    best = sw["best_by_case_temperature"][0]["params"]
    chosen = await s.tool("evaluate_design", {"label": f"A{len(fb) + 2}: Microchannel {best['channel_width_mm']:.2f}/"
                                                       f"{best['fin_thickness_mm']:.2f} x {best['channel_depth_mm']:.1f}",
                                              "topology": "straight_microchannel", **best})
    prev = get_design(ctx, ctx.outputs["thermal_design"]["selected_design_id"])
    pp, pr = prev["params"], prev["result"]
    d_t = chosen["t_case_c"] - pr["thermal"]["t_case_c"]
    why = []
    if best["channel_width_mm"] > pp["channel_width_mm"]:
        why.append(f"widening the channels from {pp['channel_width_mm']:.2f} to {best['channel_width_mm']:.2f} mm makes "
                   "the -0.02 mm cutter tolerance a much smaller fraction of the gap, so worst-case dP stops running away")
    if "max_depth_to_width" in cons:
        why.append(f"depth/width is now {best['channel_depth_mm'] / best['channel_width_mm']:.1f}:1, inside the "
                   f"{cons['max_depth_to_width']:g}:1 saw limit")
    await s.say(f"{chosen['design_id']}: {best['channel_width_mm']:.2f} mm channels, {best['fin_thickness_mm']:.2f} mm fins, "
                f"{best['channel_depth_mm']:.1f} mm deep: {_fmt(chosen)}. Against the rejected design that's {d_t:+.1f} degC "
                f"nominal and dP {pr['hydraulics']['dp_kpa']:.1f} -> {chosen['dp_kpa']:.1f} kPa. "
                + ("; ".join(why)[:1].upper() + "; ".join(why)[1:] + "." if why else ""))
    await s.tool("submit_design", {
        "selected_design_id": chosen["design_id"],
        "candidate_design_ids": sorted(ctx.designs),
        "rationale": f"Coolest design ({_fmt(chosen)}) among the "
                     f"variants that satisfy every verification-derived constraint: {_cons_text(cons)}.",
        "response_to_verification": "Findings: " + reasons + f". Re-swept with {_cons_text(cons)}; "
                                    f"{chosen['design_id']} is the best design inside those constraints."})


AGENT = AgentDef("thermal_design", "Thermal Design Agent", "Proposes and optimises the cold plate", SYSTEM, TOOLS,
                 build_task, scripted, effort_env="DESIGN_AGENT_EFFORT")
