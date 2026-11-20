"""Test methods the lab can run, where they run, and how long they take.

Durations are planning estimates for the v0 bench (plan/LAB_V0.md in the company repo), not measured
cycle times. Partner-lab work is planned but not contracted.
"""
from __future__ import annotations

# Resources. kind: bench (Loopwerks rig, cobot handles the part), hired (rented instrument on the bench),
# metrology (university CMM, human-handled, weekday office hours), partner (external lab, shipped out).
RESOURCES = [
    ("LEAK-1", "LEAK-1  Pressure decay rig", "bench", "Dry N2, 0 to 6 bar precision transducer"),
    ("HYDRO-1", "HYDRO-1  Hydrostatic and burst rig", "bench", "Hand/air pump to 40 bar, polycarbonate shield"),
    ("FLOW-1", "FLOW-1  Flow and pressure-drop loop", "bench", "D5 pump, turbine + ultrasonic flow, wet/wet dP, PG25"),
    ("THERM-1", "THERM-1  Thermal block on flow loop", "bench", "Copper heater block (TTV stand-in), 60 V / 10 A DC"),
    ("JIG-1", "JIG-1  Force jig", "bench", "Linear actuator + force gauge (retention, QD cycling)"),
    ("HE-1", "HE-1  Helium leak detector (hired)", "hired", "Hired mass spectrometer leak detector"),
    ("COBOT-1", "COBOT-1  Cobot (loaned or rented)", "cobot", "Loads parts, makes and breaks fluid connections"),
    ("CMM-UNI", "CMM-UNI  University CMM", "metrology", "Flatness and stiffness, weekday 09:00 to 17:00"),
    ("ENV-P", "ENV-P  Partner climatic chamber", "partner", "Temperature cycling (not contracted)"),
    ("MECH-P", "MECH-P  Partner shock and vibration", "partner", "Shock and vibration tables (not contracted)"),
    ("SALT-P", "SALT-P  Partner salt spray and humidity", "partner", "ASTM B117 cabinet, humidity (not contracted)"),
    ("CHEM-P", "CHEM-P  Partner chemistry lab", "partner", "ASTM D8040 and ICP analysis (not contracted)"),
]
RESOURCE_KIND = {r[0]: r[2] for r in RESOURCES}

HANDLING_IN_MIN = 12.0     # cobot: load onto fixture, connect inlet and outlet
HANDLING_OUT_MIN = 10.0    # cobot: disconnect, drain, unload
PARTNER_TRANSIT_WORKING_DAYS = 2


def _hydro(p: dict, s: dict) -> float:
    return 20 + p.get("stage1_min", 5) + p.get("stage2_min", 2) + 10


def _burst(p: dict, s: dict) -> float:
    return 20 + float(p.get("target_bar", 40)) / max(float(p.get("ramp_bar_min", 2)), 0.1) + 10


def _dp(p: dict, s: dict) -> float:
    return 30 + 12 * len(p.get("flows_lpm", []))


def _cycling(p: dict, s: dict) -> float:
    return 2 * float(p.get("dwell_h", 72)) * 60 + 240


METHODS: dict[str, dict] = {
    "cleanliness": {"name": "Flush and cleanliness", "resource": "FLOW-1", "destructive": False,
                    "minutes": lambda p, s: 90.0, "defaults": {}},
    "pressure_decay": {"name": "Gas pressure decay", "resource": "LEAK-1", "destructive": False,
                       "minutes": lambda p, s: 25 + float(p.get("hold_min", 15)), "defaults": {"hold_min": 15}},
    "helium_leak": {"name": "Helium leak", "resource": "HE-1", "destructive": False,
                    "minutes": lambda p, s: 20 + float(p.get("dwell_min", 10)), "defaults": {"dwell_min": 10}},
    "hydrostatic": {"name": "Hydrostatic pressure", "resource": "HYDRO-1", "destructive": False,
                    "minutes": _hydro, "defaults": {"stage1_min": 5, "stage2_min": 2, "stage2_factor": 3.0}},
    "burst": {"name": "Burst", "resource": "HYDRO-1", "destructive": True, "minutes": _burst,
              "defaults": {"ramp_bar_min": 2, "target_bar": 40}},
    "pressure_drop": {"name": "Pressure drop", "resource": "FLOW-1", "destructive": False, "minutes": _dp,
                      "defaults": {}},
    "flow_rate": {"name": "Flow rate (velocity check)", "resource": "FLOW-1", "destructive": False,
                  "minutes": lambda p, s: 30.0, "defaults": {}},
    "thermal_resistance": {"name": "Thermal resistance", "resource": "THERM-1", "destructive": False,
                           "minutes": lambda p, s: 30 + 40 * int(p.get("power_levels", 3)),
                           "defaults": {"inlet_c": 45, "power_levels": 3}},
    "retention_force": {"name": "Retention force", "resource": "JIG-1", "destructive": False,
                        "minutes": lambda p, s: 20.0, "defaults": {"force_n": 30, "hold_s": 5}},
    "flatness": {"name": "Flatness", "resource": "CMM-UNI", "destructive": False, "minutes": lambda p, s: 60.0,
                 "defaults": {}},
    "stiffness": {"name": "Stiffness", "resource": "CMM-UNI", "destructive": False, "minutes": lambda p, s: 60.0,
                  "defaults": {}},
    "op_temp_cycling": {"name": "Operational temperature cycling", "resource": "ENV-P", "destructive": False,
                        "minutes": _cycling, "defaults": {"dwell_h": 72}},
    "non_op_temp_cycling": {"name": "Non-operational temperature cycling", "resource": "ENV-P",
                            "destructive": False, "minutes": _cycling, "defaults": {"dwell_h": 72}},
    "shock": {"name": "Shock", "resource": "MECH-P", "destructive": False, "minutes": lambda p, s: 240.0,
              "defaults": {}},
    "vibration": {"name": "Vibration", "resource": "MECH-P", "destructive": False, "minutes": lambda p, s: 480.0,
                  "defaults": {}},
    "salt_spray": {"name": "Salt spray", "resource": "SALT-P", "destructive": False,
                   "minutes": lambda p, s: float(p.get("hours", 8)) * 60 + 24 * 60, "defaults": {"hours": 8}},
    "humidity": {"name": "Humidity", "resource": "SALT-P", "destructive": False,
                 "minutes": lambda p, s: 2 * float(p.get("hours_each", 16)) * 60 + 240,
                 "defaults": {"hours_each": 16}},
    "fluid_compatibility": {"name": "Fluid compatibility", "resource": "CHEM-P", "destructive": False,
                            "minutes": lambda p, s: 21 * 24 * 60.0, "defaults": {},
                            "note": "21 days is an estimate: the ASTM methods run multi-day to multi-week."},
}


def method(test: str) -> dict:
    if test not in METHODS:
        raise KeyError(f"Unknown test '{test}'. Known: {sorted(METHODS)}")
    return METHODS[test]


def describe_methods() -> list[dict]:
    out = []
    for k, m in METHODS.items():
        out.append({"test": k, "name": m["name"], "resource": m["resource"], "where": RESOURCE_KIND[m["resource"]],
                    "destructive": m["destructive"], "default_params": m["defaults"],
                    "nominal_minutes": round(m["minutes"](m["defaults"], {}), 1), **({"note": m["note"]} if "note" in m else {})})
    return out
