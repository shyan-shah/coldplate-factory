"""Inspection and test requirements derived from the design and its predicted performance."""
from __future__ import annotations

import math

from .design import DesignParams
from .dfm import PLENUM_MM

DEFAULT_MAX_OPERATING_PRESSURE_BAR = 4.0   # secondary loop (CDU) design pressure
PROOF_FACTOR = 1.5
LEAK_SPEC_MBAR_L_S = 1e-4                  # allowed leak rate (pressure-decay equivalent)
DECAY_RESOLUTION_MBAR = 0.5                # tester resolution x margin
CONTACT_FLATNESS_MM = 0.030                # keeps TIM2 bond line <= ~50 um
CONTACT_RA_UM = 0.8

# ISO 2859-1 general inspection level II: (max lot size, sample size)
_SAMPLE_TABLE = [(8, 2), (15, 3), (25, 5), (50, 8), (90, 13), (150, 20), (280, 32), (500, 50), (1200, 80),
                 (3200, 125)]


def sample_size(lot: int) -> int:
    for max_lot, n in _SAMPLE_TABLE:
        if lot <= max_lot:
            return min(n, lot)
    return 200


def internal_volume_ml(d: DesignParams) -> float:
    H = d.channel_depth_mm
    Lf, Wf = d.field_length_mm, d.field_width_mm
    if d.topology == "pin_fin":
        n_rows = max(1, int(Lf // d.pin_pitch_longitudinal_mm))
        n_pins = round(n_rows * Wf / d.pin_pitch_transverse_mm)
        field = Lf * Wf * H - n_pins * math.pi * d.pin_diameter_mm**2 / 4 * H
    else:
        pitch = d.channel_width_mm + d.fin_thickness_mm
        n = int((Wf + d.fin_thickness_mm) // pitch)
        field = n * d.channel_width_mm * H * Lf
    plenums = 2 * PLENUM_MM * Wf * H
    ports = 2 * math.pi * d.port_diameter_mm**2 / 4 * (d.lid_thickness_mm + 10)
    return (field + plenums + ports) / 1000.0


def qa_requirements(design: DesignParams | dict, predicted: dict, quantity: int,
                    max_operating_pressure_bar: float = DEFAULT_MAX_OPERATING_PRESSURE_BAR) -> dict:
    """Derive inspection/test parameters. `predicted` is an evaluate_design() result."""
    d = DesignParams.from_dict(design) if isinstance(design, dict) else design
    d.validate()
    vol_ml = internal_volume_ml(d)
    vol_l = vol_ml / 1000.0
    hold_s = max(60.0, math.ceil(DECAY_RESOLUTION_MBAR * vol_l / LEAK_SPEC_MBAR_L_S / 10) * 10)
    allowed_decay = LEAK_SPEC_MBAR_L_S * hold_s / vol_l
    n = sample_size(quantity)
    dp = predicted["hydraulics"]["dp_kpa"]
    r_th = predicted["thermal"]["r_case_to_inlet_k_w"]
    op = predicted["operating_point"]

    dims = [
        {"feature": "Contact face flatness (over chip footprint)", "spec": f"<= {CONTACT_FLATNESS_MM:.3f} mm",
         "method": "CMM, 25-point grid", "sampling": "100%", "critical": True},
        {"feature": "Contact face roughness", "spec": f"Ra <= {CONTACT_RA_UM} um", "method": "Profilometer",
         "sampling": f"{n} per lot", "critical": True},
        {"feature": "Base thickness under channels", "spec": f"{d.base_thickness_mm:.2f} +0.10/-0.05 mm",
         "method": "Ultrasonic thickness gauge, 5 points", "sampling": "100%", "critical": True},
        {"feature": "Mounting hole true position (4x M3)", "spec": "dia 0.05 mm to datum A|B|C",
         "method": "CMM", "sampling": f"{n} per lot", "critical": True},
        {"feature": "Overall plate L x W x T",
         "spec": f"{d.plate_length_mm:.1f} x {d.plate_width_mm:.1f} x {d.plate_thickness_mm:.2f} mm +/-0.10",
         "method": "CMM", "sampling": f"{n} per lot", "critical": False},
        {"feature": "Port position and bore", "spec": f"dia {d.port_diameter_mm:.1f} H7, position dia 0.1 mm",
         "method": "CMM + bore gauge", "sampling": f"{n} per lot", "critical": False},
    ]
    if d.topology in ("straight_microchannel", "serpentine"):
        dims.append({"feature": "Channel width / fin thickness (first article)",
                     "spec": f"{d.channel_width_mm:.2f} / {d.fin_thickness_mm:.2f} mm +/-0.02",
                     "method": "Optical CMM before lid weld", "sampling": "First article + first part each shift",
                     "critical": True})
    else:
        dims.append({"feature": "Pin diameter / pitch (first article)",
                     "spec": f"{d.pin_diameter_mm:.2f} mm +/-0.02, pitch +/-0.03",
                     "method": "Optical CMM before lid weld", "sampling": "First article", "critical": True})
    dims.append({"feature": "FSW seam", "spec": "No surface voids, flash removed, no tunnel defect",
                 "method": "Visual 100%; macro-section on first article", "sampling": "100% visual", "critical": True})

    return {
        "internal_volume_ml": round(vol_ml, 2),
        "dimensional": dims,
        "leak_test": {
            "proof_pressure_bar": round(PROOF_FACTOR * max_operating_pressure_bar, 2),
            "proof_hold_s": 120,
            "test_medium": "Dry nitrogen",
            "decay_test_pressure_bar": max_operating_pressure_bar,
            "decay_hold_s": hold_s,
            "allowed_leak_rate_mbar_l_s": LEAK_SPEC_MBAR_L_S,
            "max_pressure_decay_mbar": round(allowed_decay, 2),
            "sampling": "100%",
            "post_proof_check": "Re-measure contact flatness on first article after proof (no bulge)",
        },
        "flow_test": {
            "flow_lpm": op["flow_lpm"], "coolant": op["coolant"], "inlet_c": op["inlet_c"],
            "predicted_dp_kpa": round(dp, 2),
            "acceptance": f"dP within +/-10% of prediction ({0.9 * dp:.2f}-{1.1 * dp:.2f} kPa)",
            "sampling": f"{n} per lot",
        },
        "thermal_test": {
            "method": "Thermal test vehicle (TTV) at TDP, case temperature by embedded thermocouple",
            "power_w": op["power_w"], "inlet_c": op["inlet_c"],
            "predicted_r_k_w": round(r_th, 5),
            "acceptance": f"R_case-inlet <= {1.10 * r_th:.5f} K/W (prediction +10%)",
            "sampling": "First article + 1 per lot",
        },
        "lot_sample_size": n,
    }
