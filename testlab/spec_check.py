"""Intake validation for a test request: completeness, plausibility and whether the standard can be planned."""
from __future__ import annotations

import math
from datetime import date

from .standards import STANDARDS

COMPONENT_TYPES = ["cold_plate", "quick_disconnect", "cdu", "manifold"]
COOLANTS = ["PG25", "water"]

REQUIRED = {
    "customer": "Customer", "part_name": "Part name / number", "component_type": "Component type",
    "target_standards": "Target standard(s)", "max_operating_pressure_bar": "Maximum operating pressure (bar)",
    "rated_flow_lpm": "Rated flow (L/min)", "coolant": "Coolant", "samples": "Samples supplied",
    "deadline": "Report needed by (YYYY-MM-DD)",
}
REQUIRED_BY_TYPE = {"cold_plate": {"design_heat_load_w": "Design heat load (W)",
                                   "port_inner_diameter_mm": "Port inner diameter (mm)"}}
RANGES = {  # (error range, warning range)
    "max_operating_pressure_bar": ((0.5, 20), (1, 10)),
    "rated_flow_lpm": ((0.1, 30), (0.5, 10)),
    "samples": ((1, 50), (2, 12)),
    "design_heat_load_w": ((10, 4000), (100, 2500)),
    "port_inner_diameter_mm": ((2, 30), (3, 15)),
    "claimed_r_th_k_w": ((0.002, 1.0), (0.005, 0.2)),
    "claimed_dp_kpa_at_rated": ((0.1, 300), (1, 80)),
}
MIN_SAMPLES_FULL_OCP = 5     # destructive burst needs its own sample; partner tests run in parallel lanes
LONGEST_TEST_DAYS = 21       # fluid compatibility estimate (testlab.methods)


def _issue(field: str, severity: str, message: str) -> dict:
    return {"field": field, "severity": severity, "message": message}


def velocity_m_s(flow_lpm: float, port_id_mm: float) -> float:
    area = math.pi * (port_id_mm / 1000) ** 2 / 4
    return flow_lpm / 60000 / area


def normalise_standards(v) -> list[str]:
    if isinstance(v, str):
        v = [x.strip() for x in v.replace(";", ",").split(",")]
    return [x for x in (v or []) if x]


def validate_spec(spec: dict, today: date | None = None) -> dict:
    today = today or date.today()
    issues: list[dict] = []
    norm = {k: v for k, v in spec.items() if v not in (None, "")}
    ctype = norm.get("component_type")

    for f, label in {**REQUIRED, **REQUIRED_BY_TYPE.get(ctype, {})}.items():
        if f not in norm:
            issues.append(_issue(f, "error", f"Missing required input: {label}"))

    for f, ((lo, hi), (wlo, whi)) in RANGES.items():
        if f not in norm:
            continue
        try:
            v = float(norm[f])
        except (TypeError, ValueError):
            issues.append(_issue(f, "error", f"Not a number: {norm[f]!r}"))
            continue
        norm[f] = int(v) if f == "samples" else v
        if not lo <= v <= hi:
            issues.append(_issue(f, "error", f"{v:g} is outside the plausible range {lo} to {hi}"))
        elif not wlo <= v <= whi:
            issues.append(_issue(f, "warning", f"{v:g} is unusual (typical {wlo} to {whi}); please confirm"))

    if ctype is not None and ctype not in COMPONENT_TYPES:
        issues.append(_issue("component_type", "error", f"Unknown component type '{ctype}'. Known: {COMPONENT_TYPES}"))
    if "coolant" in norm and norm["coolant"] not in COOLANTS:
        issues.append(_issue("coolant", "error", f"Coolant '{norm['coolant']}' is not run on the v0 loop. "
                                                 f"Supported: {COOLANTS}"))

    stds = normalise_standards(norm.get("target_standards"))
    norm["target_standards"] = stds
    plannable = []
    for sid in stds:
        st = STANDARDS.get(sid)
        if st is None:
            issues.append(_issue("target_standards", "error", f"Unknown standard '{sid}'. Known: {sorted(STANDARDS)}"))
        elif not st["available"]:
            issues.append(_issue("target_standards", "error", f"{sid}: {st['note']}"))
        elif ctype and ctype not in st["applies_to"]:
            issues.append(_issue("target_standards", "error", f"{sid} covers {st['applies_to']}, not {ctype}"))
        else:
            plannable.append(sid)
    if "target_standards" in norm and stds and not plannable:
        issues.append(_issue("target_standards", "error", "No plannable standard in the request"))

    if "deadline" in norm:
        try:
            days = (date.fromisoformat(str(norm["deadline"])) - today).days
            if days <= 0:
                issues.append(_issue("deadline", "error", "Deadline is not in the future"))
            elif days < LONGEST_TEST_DAYS + 7 and "OCP-CP-1.0" in stds:
                issues.append(_issue("deadline", "warning", f"Only {days} days: the full OCP list includes about "
                                                            f"{LONGEST_TEST_DAYS} days of fluid compatibility testing"))
        except ValueError:
            issues.append(_issue("deadline", "error", f"Unparseable date {norm['deadline']!r}"))

    derived: dict = {}
    bad = {i["field"] for i in issues if i["severity"] == "error"}
    if "max_operating_pressure_bar" in norm and "max_operating_pressure_bar" not in bad:
        mop = float(norm["max_operating_pressure_bar"])
        derived["hydrostatic_stage2_bar"] = 3 * mop
    if "rated_flow_lpm" in norm and "rated_flow_lpm" not in bad:
        q = float(norm["rated_flow_lpm"])
        derived["dp_flow_span_lpm"] = [round(0.25 * q, 3), round(1.5 * q, 3)]
        if "port_inner_diameter_mm" in norm and "port_inner_diameter_mm" not in bad:
            v = velocity_m_s(1.5 * q, float(norm["port_inner_diameter_mm"]))
            derived["port_velocity_at_150pct_m_s"] = v
            if v >= 1.5:
                issues.append(_issue("rated_flow_lpm", "warning", f"Port velocity at 150 % flow is {v:.2f} m/s, at or "
                                                                  "over the 1.5 m/s erosion limit"))
    if "samples" in norm and "samples" not in bad and plannable:
        derived["samples_recommended"] = MIN_SAMPLES_FULL_OCP
        if int(norm["samples"]) < 2:
            issues.append(_issue("samples", "error", "At least 2 samples are needed: the burst test destroys one"))
        elif int(norm["samples"]) < MIN_SAMPLES_FULL_OCP:
            issues.append(_issue("samples", "warning", f"{norm['samples']} samples: the full OCP list needs about "
                                                       f"{MIN_SAMPLES_FULL_OCP} to run without serialising every test"))
    blocking = any(i["severity"] == "error" for i in issues)
    return {"accepted": not blocking, "issues": issues, "normalized_spec": norm, "derived": derived,
            "plannable_standards": plannable}
