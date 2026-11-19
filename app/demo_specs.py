"""Demo customer requests. Deadlines are relative to today so the demo never goes stale."""
from __future__ import annotations

from datetime import date, timedelta


def demo_specs() -> dict[str, dict]:
    today = date.today()
    return {
        "hx1200": {
            "title": "HX-1200 accelerator, 1.2 kW (demo case)",
            "spec": {
                "customer": "Helios Compute (fictional)",
                "part_name": "HX-1200 accelerator cold plate",
                "tdp_w": 1200, "heat_source_length_mm": 55, "heat_source_width_mm": 45,
                "max_case_temp_c": 60, "coolant": "PG25", "inlet_temp_c": 40, "flow_rate_lpm": 1.8,
                "max_pressure_drop_kpa": 15, "quantity": 40,
                "deadline": (today + timedelta(days=14)).isoformat(),
                "tim_resistance_cm2k_w": 0.08, "max_operating_pressure_bar": 4.0, "material_preference": "copper",
                "notes": "Rack loop has 8 plates in parallel per CDU branch, so the pressure-drop limit is firm. "
                         "Plate must fit a 95 x 85 mm keep-out.",
            },
        },
        "bad": {
            "title": "Incomplete / infeasible request",
            "spec": {
                "customer": "Contoso AI (fictional)", "part_name": "CX-1500 training module",
                "tdp_w": 1500, "heat_source_length_mm": 60, "heat_source_width_mm": 50,
                "max_case_temp_c": 52, "coolant": "PG25", "inlet_temp_c": 45, "flow_rate_lpm": 0.6,
                "max_pressure_drop_kpa": 10,
                "deadline": (today + timedelta(days=5)).isoformat(),
                "notes": "Need ASAP. Quantity TBD.",
            },
        },
    }
