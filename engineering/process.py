"""Machining / joining process plan: stock, operation sequence, cycle time and cost.

Cycle times come from path length / feed and volume / MRR with the cell's standard
feeds and speeds, plus fixed load/unload and tool-change allowances.
"""
from __future__ import annotations

import math

from .design import DesignParams
from .materials import solid
from .dfm import PLENUM_MM

STOCK_THICKNESSES_MM = [3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30]
XY_ALLOWANCE_MM = 3.0        # per side, saw-cut blank
FACE_ALLOWANCE_MM = 1.0      # per face
LOAD_UNLOAD_MIN = 3.0
TOOL_CHANGE_MIN = 0.3

RATES_USD_H = {"CNC": 95.0, "FSW": 120.0, "LEAK": 60.0, "BENCH": 45.0}

# Feeds per material (mm/min) and depth-per-pass limits.
FEEDS = {
    "C110": {"face": 600.0, "saw": 120.0, "slot_per_mm_dia": 90.0, "drill": 80.0, "saw_depth": 3.5},
    "Al6061": {"face": 1500.0, "saw": 300.0, "slot_per_mm_dia": 250.0, "drill": 200.0, "saw_depth": 5.0},
}
SAW_GANG_BLADES = 12
SAW_DIAMETER_MM = 50.0
FACE_MILL_STEPOVER_MM = 35.0


def _round_up_stock(t_mm: float) -> float:
    for s in STOCK_THICKNESSES_MM:
        if s >= t_mm:
            return float(s)
    return float(math.ceil(t_mm))


def stock_size(design: DesignParams) -> dict:
    s = solid(design.material)
    L = design.plate_length_mm + 2 * XY_ALLOWANCE_MM
    W = design.plate_width_mm + 2 * XY_ALLOWANCE_MM
    base_t = _round_up_stock(design.base_thickness_mm + design.channel_depth_mm + 2 * FACE_ALLOWANCE_MM)
    lid_t = _round_up_stock(design.lid_thickness_mm + 2 * FACE_ALLOWANCE_MM)
    vol_m3 = L * W * (base_t + lid_t) * 1e-9
    mass = vol_m3 * s.rho
    return {"base_blank_mm": [L, W, base_t], "lid_blank_mm": [L, W, lid_t], "material": s.name,
            "stock_mass_kg": mass, "material_cost_usd": mass * s.cost_per_kg}


def _face_minutes(length: float, width: float, feed: float) -> float:
    passes = math.ceil(width / FACE_MILL_STEPOVER_MM)
    return passes * (length + 60.0) / feed


def _op(seq: int, station: str, name: str, tools: list[str], minutes: float, notes: str = "") -> dict:
    return {"seq": seq, "station": station, "operation": name, "tools": tools,
            "minutes": round(minutes, 2), "notes": notes}


def plan_process(design: DesignParams | dict, quantity: int = 1) -> dict:
    d = DesignParams.from_dict(design) if isinstance(design, dict) else design
    d.validate()
    f = FEEDS[d.material]
    s = solid(d.material)
    L, W = d.plate_length_mm, d.plate_width_mm
    Lf, Wf, H = d.field_length_mm, d.field_width_mm, d.channel_depth_mm
    stock = stock_size(d)
    ops: list[dict] = []

    ops.append(_op(10, "CNC", "Base OP1: face contact side (rough), square blank to size",
                   ["Face mill D50 5-insert", "End mill D10 4F"],
                   LOAD_UNLOAD_MIN + _face_minutes(L, W, f["face"]) + 2 * (L + W) * 2 / (f["face"] / 2)))

    plenum_vol = 2 * PLENUM_MM * Wf * H
    dc6 = 6.0
    plenum_mrr = (f["slot_per_mm_dia"] * dc6) * (0.5 * dc6) * min(H, dc6)  # feed x ae x ap, mm3/min
    plenum_min = plenum_vol / plenum_mrr
    ops.append(_op(20, "CNC", "Base OP2: face channel side, pocket inlet/outlet plenums",
                   ["Face mill D50", "End mill D6 3F (plenums)"],
                   LOAD_UNLOAD_MIN + _face_minutes(L, W, f["face"]) + plenum_min + TOOL_CHANGE_MIN * 2))

    if d.topology == "straight_microchannel":
        n = int((Wf + d.fin_thickness_mm) // (d.channel_width_mm + d.fin_thickness_mm))
        gangs = math.ceil(n / SAW_GANG_BLADES)
        depth_passes = math.ceil(H / f["saw_depth"])
        minutes = gangs * depth_passes * (Lf + SAW_DIAMETER_MM) / f["saw"] + TOOL_CHANGE_MIN
        ops.append(_op(30, "CNC", f"Cut {n} microchannels: gang slitting saw, {gangs} gang passes x {depth_passes} depth",
                       [f"Gang slitting saw D{SAW_DIAMETER_MM:.0f} x {SAW_GANG_BLADES} blades, "
                        f"{d.channel_width_mm:.2f} mm blades / {d.fin_thickness_mm:.2f} mm spacers"],
                       minutes, "Flood coolant; check first channel width with pin gauge"))
    elif d.topology == "serpentine":
        passes_total = int((Wf + d.fin_thickness_mm) // (d.channel_width_mm + d.fin_thickness_mm))
        dc = d.channel_width_mm
        ap = 0.5 * dc
        length = passes_total * Lf + passes_total * dc * 2
        minutes = length * math.ceil(H / ap) / (f["slot_per_mm_dia"] * dc) + TOOL_CHANGE_MIN
        ops.append(_op(30, "CNC", f"Slot serpentine ({passes_total} passes), full-width slotting",
                       [f"End mill D{dc:.2f} 2F, ap {ap:.2f} mm"], minutes))
    else:
        D, st, sl = d.pin_diameter_mm, d.pin_pitch_transverse_mm, d.pin_pitch_longitudinal_mm
        gap = min(st - D, math.sqrt(sl**2 + (st / 2) ** 2) - D)
        dc = min(round(gap * 0.95, 2), 3.0)
        n_rows = max(1, int(Lf // sl))
        n_pins = round(n_rows * Wf / st)
        vol = Lf * Wf * H - n_pins * math.pi * D**2 / 4 * H
        mrr = (0.4 * dc) * min(H, 1.0 * dc) * f["slot_per_mm_dia"] * dc
        minutes = vol / mrr + 2 * TOOL_CHANGE_MIN
        ops.append(_op(30, "CNC", f"Pocket pin-fin array ({n_pins} pins) - trochoidal",
                       [f"End mill D{dc:.2f} 3F long-reach"], minutes,
                       "Slow: small cutter, low MRR"))

    ops.append(_op(40, "BENCH", "Deburr channels, ultrasonic clean, dry", ["Ultrasonic tank", "Nylon brush"], 6.0))
    port_depth = d.lid_thickness_mm + 2.0
    lid_min = (LOAD_UNLOAD_MIN + 2 * _face_minutes(L, W, f["face"]) + 2 * 2 * port_depth / f["drill"]
               + 3 * TOOL_CHANGE_MIN)
    ops.append(_op(50, "CNC", "Lid: face both sides, drill/ream 2x coolant ports, chamfer",
                   ["Face mill D50", f"Drill D{d.port_diameter_mm - 0.2:.1f}", f"Reamer D{d.port_diameter_mm:.1f}H7"],
                   lid_min))
    perimeter = 2 * (L - 2 * 3 + W - 2 * 3)
    fsw_min = 5.0 + perimeter / s.fsw_traverse_mm_min + 2.0
    ops.append(_op(60, "FSW", "Friction-stir weld lid, full perimeter (lap/butt), exit-hole run-off",
                   ["FSW tool: H13 shoulder D12, threaded pin" if d.material == "Al6061"
                    else "FSW tool: W-Re shoulder D12, pin 2.5 mm (copper)"],
                   fsw_min, f"Traverse {s.fsw_traverse_mm_min:.0f} mm/min, perimeter {perimeter:.0f} mm"))
    ops.append(_op(70, "CNC", "Post-weld: skim contact face to flatness, drill/tap 4x M3 mounting, finish profile",
                   ["Face mill D50 finishing (wiper insert)", "Drill D2.5", "Tap M3", "End mill D10 profile"],
                   LOAD_UNLOAD_MIN + _face_minutes(L, W, f["face"] / 2) + 4 * 0.4 + 2 * (L + W) / f["face"] * 2
                   + 3 * TOOL_CHANGE_MIN, "Light cut 0.1 mm, vacuum fixture to hold flatness"))
    ops.append(_op(80, "BENCH", "Clean, passivate" + (" (benzotriazole anti-tarnish)" if d.material == "C110"
                                                       else " (chromate-free conversion coat)"),
                   ["Passivation line"], 8.0))
    ops.append(_op(90, "LEAK", "Proof pressure + pressure-decay leak test (see QA plan)", ["Leak test rig"], 6.0))

    by_station: dict[str, float] = {}
    for o in ops:
        by_station[o["station"]] = by_station.get(o["station"], 0.0) + o["minutes"]
    labour_cost = sum(RATES_USD_H[k] * m / 60 for k, m in by_station.items())
    consumables = 4.0 if d.topology == "straight_microchannel" else 2.5
    unit_cost = stock["material_cost_usd"] + labour_cost + consumables
    return {
        "stock": stock,
        "operations": ops,
        "minutes_per_part_by_station": {k: round(v, 2) for k, v in by_station.items()},
        "cycle_time_min_per_part": round(sum(by_station.values()), 2),
        "cost_per_part_usd": {"material": round(stock["material_cost_usd"], 2),
                              "machine_and_labour": round(labour_cost, 2),
                              "consumables": consumables, "total": round(unit_cost, 2)},
        "quantity": quantity,
        "batch_cost_usd": round(unit_cost * quantity, 2),
        "joining": "Friction-stir welded lid (full perimeter)",
    }
