"""Independent verification against the customer spec: nominal, worst-case, DFM, erosion.

Worst-case conditions (the factory's verification standard):
  thermal:   flow -5% (CDU tolerance), TIM2 resistance +25% (pump-out / ageing),
             wetted-side fouling 2e-5 m2K/W (filtered closed loop)
  hydraulic: flow +5%, channel width -0.02 mm (fin +0.02 mm, pitch fixed),
             channel depth -0.05 mm; pin fins: diameter +0.02 mm
"""
from __future__ import annotations

from dataclasses import replace

from .design import DesignParams, OperatingPoint, evaluate_design
from .dfm import check_manufacturability, MAX_CHANNEL_VELOCITY

TOL_WIDTH_MM = 0.02
TOL_DEPTH_MM = 0.05
FLOW_TOL = 0.05
TIM_DEGRADATION = 1.25
FOULING_M2K_W = 2e-5


def worst_case_hydraulic_design(d: DesignParams) -> DesignParams:
    if d.topology == "pin_fin":
        return replace(d, pin_diameter_mm=d.pin_diameter_mm + TOL_WIDTH_MM,
                       channel_depth_mm=d.channel_depth_mm - TOL_DEPTH_MM)
    return replace(d, channel_width_mm=d.channel_width_mm - TOL_WIDTH_MM,
                   fin_thickness_mm=d.fin_thickness_mm + TOL_WIDTH_MM,
                   channel_depth_mm=d.channel_depth_mm - TOL_DEPTH_MM)


def _check(name: str, value: float, limit: float, ok: bool, unit: str, detail: str = "") -> dict:
    return {"check": name, "value": round(value, 3), "limit": round(limit, 3), "unit": unit,
            "pass": bool(ok), "detail": detail}


def verify_design(design: DesignParams | dict, op: OperatingPoint | dict, max_case_c: float,
                  max_dp_kpa: float) -> dict:
    d = DesignParams.from_dict(design) if isinstance(design, dict) else design
    op = OperatingPoint(**op) if isinstance(op, dict) else op
    d.validate()

    nominal = evaluate_design(d, op)
    op_thermal = replace(op, flow_lpm=op.flow_lpm * (1 - FLOW_TOL), tim_r_cm2k_w=op.tim_r_cm2k_w * TIM_DEGRADATION,
                         fouling_m2k_w=FOULING_M2K_W)
    wc_thermal = evaluate_design(d, op_thermal)
    op_hyd = replace(op, flow_lpm=op.flow_lpm * (1 + FLOW_TOL))
    wc_hyd = evaluate_design(worst_case_hydraulic_design(d), op_hyd)
    dfm = check_manufacturability(d)

    v_lim = MAX_CHANNEL_VELOCITY[d.material]
    v_wc = wc_hyd["hydraulics"]["velocity_m_s"]
    checks = [
        _check("Case temperature, nominal", nominal["thermal"]["t_case_c"], max_case_c,
               nominal["thermal"]["t_case_c"] <= max_case_c, "degC"),
        _check("Case temperature, worst case", wc_thermal["thermal"]["t_case_c"], max_case_c,
               wc_thermal["thermal"]["t_case_c"] <= max_case_c, "degC",
               "flow -5%, TIM2 +25%, fouling 2e-5 m2K/W"),
        _check("Pressure drop, nominal", nominal["hydraulics"]["dp_kpa"], max_dp_kpa,
               nominal["hydraulics"]["dp_kpa"] <= max_dp_kpa, "kPa"),
        _check("Pressure drop, worst case", wc_hyd["hydraulics"]["dp_kpa"], max_dp_kpa,
               wc_hyd["hydraulics"]["dp_kpa"] <= max_dp_kpa, "kPa",
               "flow +5%, channel width -0.02 mm, depth -0.05 mm"),
        _check("Coolant velocity (erosion), worst case", v_wc, v_lim, v_wc <= v_lim, "m/s",
               f"{d.material} erosion-corrosion guideline"),
        _check("Channel field covers heat source (length)", d.field_length_mm, op.source_length_mm,
               d.field_length_mm >= op.source_length_mm, "mm"),
        _check("Channel field covers heat source (width)", d.field_width_mm, op.source_width_mm,
               d.field_width_mm >= op.source_width_mm, "mm"),
    ]
    for c in dfm["checks"]:
        checks.append(_check(f"DFM: {c['rule']}", c["value"], c["limit"], c["pass"], c["unit"], c["note"]))

    failures = [c for c in checks if not c["pass"]]
    return {
        "verdict": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
        "nominal": {"t_case_c": nominal["thermal"]["t_case_c"], "dp_kpa": nominal["hydraulics"]["dp_kpa"]},
        "worst_case": {"t_case_c": wc_thermal["thermal"]["t_case_c"], "dp_kpa": wc_hyd["hydraulics"]["dp_kpa"],
                       "velocity_m_s": v_wc},
        "standard": "Flow +/-5%, TIM2 +25%, fouling 2e-5 m2K/W, width -0.02 mm, depth -0.05 mm",
    }
