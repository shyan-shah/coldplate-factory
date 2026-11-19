"""Design-for-manufacture rules for the factory cell (CNC + FSW lid).

Limits reflect the cell's tooling: gang slitting saws for straight microchannels,
end mills for pin fins and serpentines, friction-stir-welded lids.
"""
from __future__ import annotations

import math

from .design import DesignParams

MIN_BASE_MM = 1.0             # below this the contact face bows under FSW clamping / pressure
FSW_LAND_MM = 6.0             # weld land each side (12 mm shoulder tool)
PLENUM_MM = 6.0               # inlet/outlet plenum length each end (flow direction)
MAX_CHANNEL_VELOCITY = {"C110": 2.0, "Al6061": 2.0}  # m/s, erosion-corrosion guideline

SAW = {"min_width_mm": 0.20, "max_depth_to_width": 12.0, "min_fin_mm": {"C110": 0.20, "Al6061": 0.25},
       "max_fin_height_to_thickness": 15.0}
END_MILL = {"min_width_mm": 1.0, "max_depth_to_width": 4.0, "min_rib_mm": 0.8}
PIN = {"min_diameter_mm": 1.0, "min_gap_mm": 0.8, "max_depth_to_gap": 5.0, "max_height_to_diameter": 4.0}


def _rule(rule: str, value: float, limit: float, ok: bool, unit: str = "", note: str = "") -> dict:
    return {"rule": rule, "value": round(value, 3), "limit": limit, "unit": unit, "pass": bool(ok), "note": note}


def check_manufacturability(design: DesignParams | dict) -> dict:
    d = DesignParams.from_dict(design) if isinstance(design, dict) else design
    d.validate()
    checks: list[dict] = []
    checks.append(_rule("Base thickness under channels", d.base_thickness_mm, MIN_BASE_MM,
                        d.base_thickness_mm >= MIN_BASE_MM, "mm", "min, flatness under FSW clamping"))
    land_len = (d.plate_length_mm - d.field_length_mm) / 2 - PLENUM_MM
    land_wid = (d.plate_width_mm - d.field_width_mm) / 2
    checks.append(_rule("FSW land, flow ends (after plenum)", land_len, FSW_LAND_MM, land_len >= FSW_LAND_MM, "mm"))
    checks.append(_rule("FSW land, sides", land_wid, FSW_LAND_MM, land_wid >= FSW_LAND_MM, "mm"))

    if d.topology == "straight_microchannel":
        w, t, H = d.channel_width_mm, d.fin_thickness_mm, d.channel_depth_mm
        checks.append(_rule("Channel width (slitting saw)", w, SAW["min_width_mm"], w >= SAW["min_width_mm"], "mm", "min"))
        min_fin = SAW["min_fin_mm"][d.material]
        checks.append(_rule("Fin thickness", t, min_fin, t >= min_fin, "mm", "min"))
        checks.append(_rule("Channel depth / width", H / w, SAW["max_depth_to_width"],
                            H / w <= SAW["max_depth_to_width"], "", "max"))
        checks.append(_rule("Fin height / thickness", H / t, SAW["max_fin_height_to_thickness"],
                            H / t <= SAW["max_fin_height_to_thickness"], "",
                            "max, thin tall fins chatter and lean during cutting and lid welding"))
    elif d.topology == "serpentine":
        w, t, H = d.channel_width_mm, d.fin_thickness_mm, d.channel_depth_mm
        checks.append(_rule("Channel width (end mill)", w, END_MILL["min_width_mm"], w >= END_MILL["min_width_mm"], "mm", "min"))
        checks.append(_rule("Rib thickness", t, END_MILL["min_rib_mm"], t >= END_MILL["min_rib_mm"], "mm", "min"))
        checks.append(_rule("Channel depth / width", H / w, END_MILL["max_depth_to_width"],
                            H / w <= END_MILL["max_depth_to_width"], "", "max end-mill reach"))
    else:
        D, st, sl, H = d.pin_diameter_mm, d.pin_pitch_transverse_mm, d.pin_pitch_longitudinal_mm, d.channel_depth_mm
        gap = min(st - D, math.sqrt(sl**2 + (st / 2) ** 2) - D)
        checks.append(_rule("Pin diameter", D, PIN["min_diameter_mm"], D >= PIN["min_diameter_mm"], "mm", "min"))
        checks.append(_rule("Gap between pins (cutter access)", gap, PIN["min_gap_mm"], gap >= PIN["min_gap_mm"], "mm", "min"))
        checks.append(_rule("Pocket depth / gap", H / gap, PIN["max_depth_to_gap"], H / gap <= PIN["max_depth_to_gap"], "", "max cutter L/D"))
        checks.append(_rule("Pin height / diameter", H / D, PIN["max_height_to_diameter"],
                            H / D <= PIN["max_height_to_diameter"], "", "max"))
    return {"manufacturable": all(c["pass"] for c in checks), "checks": checks}
