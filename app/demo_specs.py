"""Demo test requests. All companies are fictional. Deadlines are relative to today so the demo never goes stale."""
from __future__ import annotations

from datetime import date, timedelta


def demo_specs() -> dict[str, dict]:
    today = date.today()
    return {
        "cp1400": {
            "title": "CP-1400 cold plate to OCP methods (demo case)",
            "spec": {
                "customer": "Northwind Thermal (fictional)",
                "part_name": "CP-1400 single-phase cold plate",
                "component_type": "cold_plate",
                "target_standards": "OCP-CP-1.0",
                "max_operating_pressure_bar": 5.0, "rated_flow_lpm": 1.5, "coolant": "PG25",
                "design_heat_load_w": 1400, "port_inner_diameter_mm": 6.0,
                "claimed_r_th_k_w": 0.020, "claimed_dp_kpa_at_rated": 12.0,
                "samples": 5,
                "deadline": (today + timedelta(days=56)).isoformat(),
                "notes": "Second-source qualification for an integrator. Copper plate with skived fins, G1/4 ports. "
                         "We want our own data before we pay for certification.",
            },
        },
        "bad": {
            "title": "QD to UL 4501 only, incomplete (demo)",
            "spec": {
                "customer": "Contoso Fluidics (fictional)", "part_name": "QD-08 quick disconnect pair",
                "component_type": "quick_disconnect", "target_standards": "UL-4501",
                "rated_flow_lpm": 8, "coolant": "PG25", "samples": 1,
                "deadline": (today + timedelta(days=10)).isoformat(),
                "notes": "Need a UL 4501 pass for a customer audit next month.",
            },
        },
    }
