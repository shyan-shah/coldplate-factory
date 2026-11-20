"""Build a test campaign from planner input: steps, resources, durations and acceptance criteria."""
from __future__ import annotations

from .methods import METHODS, RESOURCE_KIND, method
from .spec_check import velocity_m_s
from .standards import get_standard, requirement_for_test


def acceptance(test: str, params: dict, spec: dict) -> str:
    mop = float(spec.get("max_operating_pressure_bar", 0) or 0)
    if test == "helium_leak":
        lim = spec.get("leak_rate_limit")
        return f"Leak rate below {lim}" if lim else "Leak rate below the customer limit (to be confirmed in the plan)"
    if test == "pressure_decay":
        return f"Pressure loss < 0.5 % over {params.get('hold_min')} min (example limit; confirm with customer)"
    if test == "hydrostatic":
        f = params.get("stage2_factor", 3.0)
        return (f"No leak or permanent deformation after {params.get('stage1_min')} min at {mop:g} bar and "
                f"{params.get('stage2_min')} min at {f * mop:g} bar")
    if test == "burst":
        return (f"No rupture below {3 * mop:g} bar (3x MOP); ramp {params.get('ramp_bar_min')} bar/min to rupture or "
                f"{params.get('target_bar')} bar (bench limit)")
    if test == "thermal_resistance":
        lim = spec.get("claimed_r_th_k_w")
        return (f"R_th <= {1.1 * float(lim):.4f} K/W (maker's claim +10 %, customer criterion)" if lim
                else "Report R_th; acceptance limit from customer") + f" at inlet {params.get('inlet_c')} degC"
    if test == "pressure_drop":
        lim = spec.get("claimed_dp_kpa_at_rated")
        return (f"dP at rated flow within +/-10 % of the maker's {lim} kPa (customer criterion)" if lim
                else "Report dP curve") + f"; {len(params.get('flows_lpm', []))} points"
    if test == "flow_rate":
        return "Port velocity < 1.5 m/s at the highest test flow"
    if test == "retention_force":
        return f"Holds {params.get('force_n')} N for {params.get('hold_s')} s with no slip"
    if test == "flatness":
        lim = spec.get("flatness_limit_mm")
        return f"Contact face flatness <= {lim} mm (ISO 12781-2)" if lim else "Report flatness (ISO 12781-2)"
    if test in ("op_temp_cycling", "non_op_temp_cycling"):
        return f"Two {params.get('dwell_h')} h dwells completed; leak test passes afterwards"
    if test == "salt_spray":
        return f"{params.get('hours')} h ASTM B117; no corrosion that affects function"
    if test == "humidity":
        return f"Two {params.get('hours_each')} h dwells; no corrosion or leak"
    if test == "cleanliness":
        return "No particulate over 50 um in the flush"
    if test == "fluid_compatibility":
        return "Fluid chemistry and material changes within the method limits"
    return "Report result"


def build_campaign(inp: dict, spec: dict, standard_id: str) -> dict:
    """inp: {label, steps: [{sample_id, test, params}]}. Step order within a sample is the test sequence."""
    std = get_standard(standard_id)
    steps_in = inp.get("steps") or []
    if not steps_in:
        raise ValueError("A campaign needs at least one step")
    steps, samples = [], []
    for i, s in enumerate(steps_in, 1):
        test = s.get("test")
        m = method(test)
        sid = str(s.get("sample_id", "")).strip()
        if not sid:
            raise ValueError(f"step {i}: sample_id is required")
        if sid not in samples:
            samples.append(sid)
        params = {**m["defaults"], **(s.get("params") or {})}
        req = requirement_for_test(std, test)
        minutes = float(m["minutes"](params, spec))
        step = {"step_id": f"T{i:02d}", "sample_id": sid, "test": test, "name": m["name"], "params": params,
                "requirement": req["id"] if req else None, "resource": m["resource"],
                "where": RESOURCE_KIND[m["resource"]], "destructive": m["destructive"],
                "run_minutes": round(minutes, 1), "acceptance": acceptance(test, params, spec)}
        if test in ("pressure_drop", "flow_rate") and spec.get("port_inner_diameter_mm"):
            flows = params.get("flows_lpm") or [1.5 * float(spec["rated_flow_lpm"])]
            step["max_velocity_m_s"] = round(velocity_m_s(max(flows), float(spec["port_inner_diameter_mm"])), 3)
        steps.append(step)
    seq = {sid: [s["step_id"] for s in steps if s["sample_id"] == sid] for sid in samples}
    hours = lambda kind: round(sum(s["run_minutes"] for s in steps if s["where"] in kind) / 60, 1)  # noqa: E731
    covered = sorted({s["requirement"] for s in steps if s["requirement"]})
    return {
        "label": inp.get("label") or "Campaign", "standard": standard_id, "samples": samples,
        "sample_sequences": seq, "steps": steps,
        "totals": {"steps": len(steps), "samples_used": len(samples), "bench_hours": hours(("bench", "hired")),
                   "metrology_hours": hours(("metrology",)), "partner_hours": hours(("partner",)),
                   "requirements_covered": len(covered), "requirements_total": len(std["requirements"])},
        "requirements_covered": covered,
    }


def known_tests() -> list[str]:
    return sorted(METHODS)
