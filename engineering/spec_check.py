"""Customer spec validation: completeness, plausibility, and physical feasibility bounds."""
from __future__ import annotations

from datetime import date

from .materials import COOLANTS, coolant_props, lpm_to_m3s

REQUIRED = {
    "tdp_w": "Thermal design power (W)",
    "heat_source_length_mm": "Heat source (lid contact) length (mm)",
    "heat_source_width_mm": "Heat source (lid contact) width (mm)",
    "max_case_temp_c": "Maximum case temperature (degC)",
    "coolant": "Coolant type",
    "inlet_temp_c": "Coolant inlet temperature (degC)",
    "flow_rate_lpm": "Available flow rate per plate (L/min)",
    "max_pressure_drop_kpa": "Maximum pressure drop (kPa)",
    "quantity": "Quantity",
    "deadline": "Delivery deadline (YYYY-MM-DD)",
}
DEFAULTS = {"tim_resistance_cm2k_w": 0.08, "max_operating_pressure_bar": 4.0, "material_preference": "copper"}

# (min, max) -> error outside; (warn_lo, warn_hi) -> warning outside
RANGES = {
    "tdp_w": ((10, 3000), (50, 2000)),
    "heat_source_length_mm": ((5, 150), (10, 100)),
    "heat_source_width_mm": ((5, 150), (10, 100)),
    "max_case_temp_c": ((25, 110), (45, 95)),
    "inlet_temp_c": ((5, 65), (5, 50)),  # low-inlet condensation warning handled below
    "flow_rate_lpm": ((0.1, 20), (0.5, 6)),
    "max_pressure_drop_kpa": ((1, 300), (5, 100)),
    "quantity": ((1, 10000), (1, 2000)),
    "tim_resistance_cm2k_w": ((0.005, 1.0), (0.02, 0.3)),
}


def _issue(field: str, severity: str, message: str) -> dict:
    return {"field": field, "severity": severity, "message": message}


def validate_spec(spec: dict, today: date | None = None) -> dict:
    today = today or date.today()
    issues: list[dict] = []
    norm = {**DEFAULTS, **{k: v for k, v in spec.items() if v not in (None, "")}}

    for f, label in REQUIRED.items():
        if f not in norm:
            issues.append(_issue(f, "error", f"Missing required input: {label}"))
    for k in DEFAULTS:
        if k not in spec or spec.get(k) in (None, ""):
            issues.append(_issue(k, "info", f"Not specified; using factory default {DEFAULTS[k]}"))

    for f, ((lo, hi), (wlo, whi)) in RANGES.items():
        if f not in norm:
            continue
        try:
            v = float(norm[f])
        except (TypeError, ValueError):
            issues.append(_issue(f, "error", f"Not a number: {norm[f]!r}"))
            continue
        norm[f] = int(v) if f == "quantity" else v
        if not lo <= v <= hi:
            issues.append(_issue(f, "error", f"{v:g} is outside the physically plausible range {lo}-{hi}"))
        elif not wlo <= v <= whi:
            issues.append(_issue(f, "warning", f"{v:g} is unusual (typical {wlo}-{whi}); please confirm"))

    if "coolant" in norm and norm["coolant"] not in COOLANTS:
        issues.append(_issue("coolant", "error", f"Unsupported coolant '{norm['coolant']}'. Supported: {sorted(COOLANTS)}"))

    if "deadline" in norm:
        try:
            dl = date.fromisoformat(str(norm["deadline"]))
            days = (dl - today).days
            if days <= 0:
                issues.append(_issue("deadline", "error", "Deadline is not in the future"))
            elif days < 7:
                issues.append(_issue("deadline", "warning", f"Only {days} days to deadline; expedite likely needed"))
        except ValueError:
            issues.append(_issue("deadline", "error", f"Unparseable date {norm['deadline']!r}"))

    if "inlet_temp_c" in norm and isinstance(norm.get("inlet_temp_c"), float) and norm["inlet_temp_c"] < 18:
        issues.append(_issue("inlet_temp_c", "warning", "Inlet below typical data-hall dew point; condensation risk"))

    derived: dict = {}
    thermal_fields = ["tdp_w", "heat_source_length_mm", "heat_source_width_mm", "max_case_temp_c", "coolant",
                      "inlet_temp_c", "flow_rate_lpm", "tim_resistance_cm2k_w"]
    bad_fields = {i["field"] for i in issues if i["severity"] == "error"}
    if all(f in norm for f in thermal_fields) and not bad_fields & set(thermal_fields):
        q = norm["tdp_w"]
        a_src_cm2 = norm["heat_source_length_mm"] * norm["heat_source_width_mm"] / 100.0
        fp = coolant_props(norm["coolant"], norm["inlet_temp_c"])
        m_dot = fp.rho * lpm_to_m3s(norm["flow_rate_lpm"])
        rise = q / (m_dot * fp.cp)
        r_cal = 1 / (2 * m_dot * fp.cp)
        r_tim = norm["tim_resistance_cm2k_w"] / a_src_cm2
        floor = norm["inlet_temp_c"] + q * (r_cal + r_tim)
        budget = norm["max_case_temp_c"] - norm["inlet_temp_c"]
        derived = {
            "heat_flux_w_cm2": q / a_src_cm2,
            "coolant_temp_rise_c": rise,
            "required_r_case_to_inlet_k_w": budget / q,
            "case_temp_floor_c": floor,
            "floor_note": "Inlet + coolant rise to bulk mean + TIM2 drop: no plate can beat this",
            "budget_left_for_plate_c": norm["max_case_temp_c"] - floor,
        }
        if derived["heat_flux_w_cm2"] > 150:
            issues.append(_issue("tdp_w", "warning", f"Heat flux {derived['heat_flux_w_cm2']:.0f} W/cm2 is at the "
                                                     "limit of single-phase cold plates"))
        if rise > 15:
            issues.append(_issue("flow_rate_lpm", "warning", f"Coolant rise {rise:.1f} degC is high; more flow advised"))
        if floor >= norm["max_case_temp_c"]:
            issues.append(_issue("max_case_temp_c", "error",
                                 f"Infeasible: case temperature floor {floor:.1f} degC (coolant + TIM alone) "
                                 f">= limit {norm['max_case_temp_c']:g} degC. Increase flow, lower inlet "
                                 "temperature or improve TIM."))
        elif derived["budget_left_for_plate_c"] < 4:
            issues.append(_issue("max_case_temp_c", "warning",
                                 f"Only {derived['budget_left_for_plate_c']:.1f} degC left for the plate itself; "
                                 "very aggressive"))

    blocking = any(i["severity"] == "error" for i in issues)
    return {"accepted": not blocking, "issues": issues, "normalized_spec": norm, "derived": derived}
