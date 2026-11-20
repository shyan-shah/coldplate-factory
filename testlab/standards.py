"""Standard requirement catalogues used to plan and verify test campaigns.

Provenance matters here. The OCP entry is a planning summary of the OCP Single-Phase Direct-to-Chip
Cold Plate Test Specification v1.0.0 (effective 2026-09-03), taken from the research notes in
research/notes/cold_plate_bottlenecks_qualification_capital.md and the spec PDF. It is not a copy of
the specification. Every value must be checked against the specification text before a real campaign.
No clause numbers are given because they were not extracted reliably.
"""
from __future__ import annotations

OCP_URL = "https://www.opencompute.org/documents/ocp-cold-plate-test-specification-v1-0-0-pdf-1/"
UL_URL = "https://www.ul.com/news/ul-solutions-launches-certification-direct-chip-liquid-cooling-equipment-used-ai-data-centers"

OCP_CP = {
    "id": "OCP-CP-1.0",
    "title": "OCP Single-Phase Direct-to-Chip Cold Plate Test Specification v1.0.0",
    "url": OCP_URL,
    "available": True,
    "applies_to": ["cold_plate"],
    "provenance": ("Planning summary from Loopwerks research notes, not the specification text. Check every "
                   "value against the published specification before testing. The helium leak-rate exponent "
                   "could not be recovered from the PDF, so the leak-rate limit comes from the customer spec."),
    "note": "Conformance to the specification does not constitute production acceptance.",
    "requirements": [
        {"id": "R01", "name": "Helium (tracer gas) leak", "test": "helium_leak",
         "rule": "Dwell 5 to 10 min. Leak-rate limit from the customer spec (water-tight example < 0.6 SCCM).",
         "params": {"dwell_min": [5, 10]}},
        {"id": "R02", "name": "Gas pressure decay", "test": "pressure_decay",
         "rule": "Hold 5 to 30 min. Example limit < 0.5 % pressure loss.", "params": {"hold_min": [5, 30]}},
        {"id": "R03", "name": "Hydrostatic pressure", "test": "hydrostatic",
         "rule": "5 min at maximum operating pressure, then 2 min at 3x maximum operating pressure. "
                 "No permanent deformation.",
         "params": {"stage1_min": 5, "stage2_min": 2, "stage2_factor": 3.0}},
        {"id": "R04", "name": "Burst (destructive)", "test": "burst",
         "rule": "Until rupture or 3x minimum proof pressure; pressure rise 1 to 5 bar/min (ISO 18869). The acceptance "
                 "pressure is report-only here until checked against the specification text.",
         "params": {"ramp_bar_min": [1, 5]}},
        {"id": "R05", "name": "Thermal resistance", "test": "thermal_resistance",
         "rule": "On a TTV or processor stack with inlet at 45 +/- 2 degC.", "params": {"inlet_c": [43, 47]}},
        {"id": "R06", "name": "Pressure drop", "test": "pressure_drop",
         "rule": "At 6 or more flow points spanning 25 % to 150 % of rated flow.",
         "params": {"min_points": 6, "span_pct": [25, 150]}},
        {"id": "R07", "name": "Flow rate (erosion limit)", "test": "flow_rate",
         "rule": "Coolant velocity below 1.5 m/s at the highest test flow.", "params": {"max_velocity_m_s": 1.5}},
        {"id": "R08", "name": "Retention force", "test": "retention_force",
         "rule": "30 N +/- 10 % held for 5 s.", "params": {"force_n": [27, 33], "hold_s": 5}},
        {"id": "R09", "name": "Flatness", "test": "flatness", "rule": "Measured per ISO 12781-2.", "params": {}},
        {"id": "R10", "name": "Stiffness", "test": "stiffness", "rule": "Measured under the customer's mounting load.",
         "params": {}},
        {"id": "R11", "name": "Operational temperature cycling", "test": "op_temp_cycling",
         "rule": "10 degC for 72 h, then 65 degC for 72 h, under pressure in a loop.", "params": {"dwell_h": 72}},
        {"id": "R12", "name": "Non-operational (shipping) temperature cycling", "test": "non_op_temp_cycling",
         "rule": "-40 degC for 72 h, then +70 degC for 72 h, with a helium leak test before and after.",
         "params": {"dwell_h": 72}},
        {"id": "R13", "name": "Shock", "test": "shock", "rule": "On a representative board.", "params": {}},
        {"id": "R14", "name": "Vibration", "test": "vibration", "rule": "On a representative board.", "params": {}},
        {"id": "R15", "name": "Salt spray", "test": "salt_spray", "rule": "ASTM B117, 5 % NaCl, 35 degC, 8 h.",
         "params": {"hours": 8}},
        {"id": "R16", "name": "Fluid compatibility and corrosion", "test": "fluid_compatibility",
         "rule": "ASTM D8040 with ICP, pH and reserve alkalinity analysis; elastomers ASTM D471, plastics D543, "
                 "braze materials D7933.", "params": {}},
        {"id": "R17", "name": "Humidity", "test": "humidity", "rule": "40 degC / 93 % RH for 16 h, then 40 degC / "
                                                                     "10 % RH for 16 h.", "params": {"hours_each": 16}},
        {"id": "R18", "name": "Flush and cleanliness", "test": "cleanliness",
         "rule": "Ultrasonic flush; no particulate over 50 um.", "params": {}},
    ],
    "sequence_rules": [
        {"id": "SEQ-1", "rule": "From the specification summary: helium leak test on the same sample before and after "
                                "non-operational temperature cycling (R12)."},
        {"id": "SEQ-2", "rule": "Loopwerks lab rule (not from the specification): a destructive test must be the last "
                                "test on its sample."},
        {"id": "SEQ-3", "rule": "Loopwerks lab rule (not from the specification): the campaign may not use more samples "
                                "than the customer supplies."},
    ],
}

UL_4501 = {
    "id": "UL-4501",
    "title": "UL 4501 Outline of Investigation for liquid-filled components and assemblies",
    "url": UL_URL,
    "available": False,
    "applies_to": ["cold_plate", "manifold", "quick_disconnect"],
    "provenance": ("Announced by UL Solutions on 29 Sep 2026. The test methods are not public, and certification "
                   "requires UL's own testing and a factory audit."),
    "note": ("Loopwerks cannot plan a UL 4501 campaign or certify to it. Pre-compliance tests can only be run to "
             "methods the customer supplies in writing."),
    "requirements": [],
    "sequence_rules": [],
}

STANDARDS = {s["id"]: s for s in (OCP_CP, UL_4501)}


def get_standard(standard_id: str) -> dict:
    if standard_id not in STANDARDS:
        raise KeyError(f"Unknown standard '{standard_id}'. Known: {sorted(STANDARDS)}")
    return STANDARDS[standard_id]


def requirement_for_test(standard: dict, test: str) -> dict | None:
    return next((r for r in standard["requirements"] if r["test"] == test), None)
