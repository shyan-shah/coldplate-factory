"""Cold plate design parameter sets and full performance evaluation.

A design is a parameter set (no CAD).  Units at this boundary are mm / L/min / degC;
everything inside is SI.  Flow runs along the field length.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict, fields

from . import convection as cv
from . import pressure_drop as pd
from .materials import coolant_props, solid, lpm_to_m3s
from .thermal_network import build_network, case_temperature

TOPOLOGIES = ("straight_microchannel", "pin_fin", "serpentine")
MM = 1e-3


@dataclass
class DesignParams:
    topology: str
    material: str = "C110"
    plate_length_mm: float = 90.0
    plate_width_mm: float = 80.0
    lid_thickness_mm: float = 3.0
    field_length_mm: float = 60.0      # flow direction
    field_width_mm: float = 55.0
    base_thickness_mm: float = 1.5
    channel_depth_mm: float = 3.0      # also fin / pin height
    # straight microchannel + serpentine
    channel_width_mm: float | None = None
    fin_thickness_mm: float | None = None   # wall between channels (serpentine: rib)
    # serpentine
    parallel_paths: int | None = None
    # pin fin (staggered)
    pin_diameter_mm: float | None = None
    pin_pitch_transverse_mm: float | None = None
    pin_pitch_longitudinal_mm: float | None = None
    port_diameter_mm: float = 8.0

    @classmethod
    def from_dict(cls, d: dict) -> "DesignParams":
        names = {f.name for f in fields(cls)}
        unknown = set(d) - names
        if unknown:
            raise ValueError(f"Unknown design parameters: {sorted(unknown)}")
        return cls(**d)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def validate(self) -> None:
        if self.topology not in TOPOLOGIES:
            raise ValueError(f"topology must be one of {TOPOLOGIES}")
        solid(self.material)
        for name in ("plate_length_mm", "plate_width_mm", "field_length_mm", "field_width_mm",
                     "base_thickness_mm", "channel_depth_mm", "lid_thickness_mm", "port_diameter_mm"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be > 0")
        if self.topology in ("straight_microchannel", "serpentine"):
            if not self.channel_width_mm or not self.fin_thickness_mm:
                raise ValueError(f"{self.topology} needs channel_width_mm and fin_thickness_mm")
            if self.channel_width_mm <= 0 or self.fin_thickness_mm <= 0:
                raise ValueError("channel_width_mm and fin_thickness_mm must be > 0")
        if self.topology == "serpentine":
            self.parallel_paths = self.parallel_paths or 1
            if not 1 <= self.parallel_paths <= 8:
                raise ValueError("parallel_paths must be 1..8")
        if self.topology == "pin_fin":
            d, st, sl = self.pin_diameter_mm, self.pin_pitch_transverse_mm, self.pin_pitch_longitudinal_mm
            if not (d and st and sl):
                raise ValueError("pin_fin needs pin_diameter_mm, pin_pitch_transverse_mm, pin_pitch_longitudinal_mm")
            if st <= d or sl <= 0.5 * d:
                raise ValueError("pin pitches too small for the pin diameter (pins would overlap)")

    @property
    def plate_thickness_mm(self) -> float:
        return self.base_thickness_mm + self.channel_depth_mm + self.lid_thickness_mm


@dataclass
class OperatingPoint:
    power_w: float
    source_length_mm: float
    source_width_mm: float
    inlet_c: float
    coolant: str
    flow_lpm: float
    tim_r_cm2k_w: float = 0.08     # TIM2 (high-performance paste); spec may override
    fouling_m2k_w: float = 0.0      # wetted-side fouling resistance

    @property
    def source_area_m2(self) -> float:
        return self.source_length_mm * self.source_width_mm * MM * MM


def _geometry_and_flow(d: DesignParams, op: OperatingPoint, rho: float, mu: float, k_f: float,
                       pr: float, k_s: float, q_m3s: float) -> dict:
    """Topology-specific geometry, hydraulics and convective conductance."""
    H = d.channel_depth_mm * MM
    Lf = d.field_length_mm * MM
    Wf = d.field_width_mm * MM
    A_field = Lf * Wf
    out: dict = {}

    def wall_h(h_raw: float) -> float:
        return 1.0 / (1.0 / h_raw + op.fouling_m2k_w) if op.fouling_m2k_w > 0 else h_raw

    if d.topology == "straight_microchannel":
        w = d.channel_width_mm * MM
        t = d.fin_thickness_mm * MM
        n = int((Wf + t) // (w + t))
        if n < 1:
            raise ValueError("field too narrow for one channel")
        dh = cv.hydraulic_diameter(w, H)
        alpha = cv.aspect_ratio(w, H)
        v = q_m3s / (n * w * H)
        re = cv.reynolds(rho, v, dh, mu)
        nu = cv.nusselt_rect_duct(re, pr, alpha)
        h = wall_h(cv.heat_transfer_coefficient(nu, k_f, dh))
        eta = cv.fin_efficiency_straight(h, k_s, t, H)
        n_fins = n - 1
        a_base = n * w * Lf
        a_fin = 2 * n_fins * H * Lf + 2 * H * Lf * 0.5  # outer walls count as half fins
        f = cv.friction_factor_rect_duct(re, alpha)
        sigma = n * w / Wf
        dp_major = pd.darcy_weisbach(f, Lf, dh, rho, v)
        dp_contr = pd.minor_loss(pd.K_CONTRACTION, rho, v)
        dp_exp = pd.minor_loss(pd.expansion_k(sigma), rho, v)
        out.update(channel_count=n, pitch_mm=(w + t) / MM, flow_length_mm=Lf / MM, n_bends=0,
                   dp_parts={"channel_friction": dp_major, "manifold_contraction": dp_contr,
                             "manifold_expansion": dp_exp})
    elif d.topology == "serpentine":
        w = d.channel_width_mm * MM
        t = d.fin_thickness_mm * MM
        p = d.parallel_paths or 1
        passes_total = int((Wf + t) // (w + t))
        passes = passes_total // p
        if passes < 1:
            raise ValueError("field too narrow for the requested serpentine passes")
        passes_total = passes * p
        L_path = passes * Lf
        n_bends = passes - 1
        dh = cv.hydraulic_diameter(w, H)
        alpha = cv.aspect_ratio(w, H)
        v = q_m3s / (p * w * H)
        re = cv.reynolds(rho, v, dh, mu)
        nu = cv.nusselt_rect_duct(re, pr, alpha)
        h = wall_h(cv.heat_transfer_coefficient(nu, k_f, dh))
        eta = cv.fin_efficiency_straight(h, k_s, t, H)
        a_base = passes_total * w * Lf
        a_fin = 2 * passes_total * H * Lf
        f = cv.friction_factor_rect_duct(re, alpha)
        dp_major = pd.darcy_weisbach(f, L_path, dh, rho, v)
        dp_bends = n_bends * pd.minor_loss(pd.K_BEND_180, rho, v)
        dp_io = pd.minor_loss(pd.K_CONTRACTION + 1.0, rho, v)
        out.update(channel_count=passes_total, passes_per_path=passes, parallel_paths=p,
                   pitch_mm=(w + t) / MM, flow_length_mm=L_path / MM, n_bends=n_bends,
                   dp_parts={"channel_friction": dp_major, "bends_180deg": dp_bends,
                             "path_entry_exit": dp_io})
    else:  # pin_fin
        D = d.pin_diameter_mm * MM
        st = d.pin_pitch_transverse_mm * MM
        sl = d.pin_pitch_longitudinal_mm * MM
        n_rows = max(1, int(Lf // sl))
        n_pins = int(round(n_rows * Wf / st))
        v_app = q_m3s / (Wf * H)
        v = v_app * cv.pin_bank_vmax_factor(st, sl, D)
        re = cv.reynolds(rho, v, D, mu)
        nu = cv.nu_zukauskas_staggered(re, pr, st, sl, n_rows)
        h = wall_h(cv.heat_transfer_coefficient(nu, k_f, D))
        eta = cv.fin_efficiency_pin(h, k_s, D, H)
        a_base = A_field - n_pins * math.pi * D**2 / 4
        a_fin = n_pins * math.pi * D * H
        dp_bank = pd.pin_bank_pressure_drop(re, st / D, sl / D, n_rows, rho, v)
        dp_io = pd.minor_loss(pd.K_CONTRACTION + 1.0, rho, v_app)
        dh = D
        out.update(pin_count=n_pins, pin_rows=n_rows, flow_length_mm=Lf / MM, n_bends=0,
                   approach_velocity_m_s=v_app,
                   dp_parts={"pin_bank": dp_bank, "field_entry_exit": dp_io})

    h_eff = h * (a_base + eta * a_fin) / A_field
    out.update(dh=dh, velocity=v, re=re, nu=nu, h=h, fin_efficiency=eta, h_eff=h_eff,
               a_wetted=a_base + a_fin, a_field=A_field, regime=cv.flow_regime(re))
    return out


def evaluate_design(design: DesignParams | dict, op: OperatingPoint | dict) -> dict:
    """Full deterministic evaluation: geometry, hydraulics, heat transfer, case temperature."""
    d = DesignParams.from_dict(design) if isinstance(design, dict) else design
    op = OperatingPoint(**op) if isinstance(op, dict) else op
    d.validate()
    s = solid(d.material)
    q = lpm_to_m3s(op.flow_lpm)

    # Evaluate properties at the bulk-mean temperature (two fixed-point passes).
    t_bulk = op.inlet_c
    for _ in range(3):
        fp = coolant_props(op.coolant, t_bulk)
        m_dot = fp.rho * q
        t_bulk = op.inlet_c + op.power_w / (2 * m_dot * fp.cp)

    g = _geometry_and_flow(d, op, fp.rho, fp.mu, fp.k, fp.pr, s.k, q)
    dp_ports, v_port = pd.port_losses(fp.rho, q, d.port_diameter_mm * MM)
    g["dp_parts"]["ports_and_plenums"] = dp_ports
    dp_total = sum(g["dp_parts"].values())

    net = build_network(op.power_w, m_dot, fp.cp, g["h_eff"], g["a_field"], s.k,
                        d.base_thickness_mm * MM, op.source_area_m2, op.tim_r_cm2k_w)
    t_case = case_temperature(op.inlet_c, op.power_w, net)
    t_out = op.inlet_c + op.power_w / (m_dot * fp.cp)

    plate_vol = d.plate_length_mm * d.plate_width_mm * d.plate_thickness_mm * MM**3
    geometry = {
        "topology": d.topology,
        "material": d.material,
        "plate_mm": [d.plate_length_mm, d.plate_width_mm, round(d.plate_thickness_mm, 3)],
        "field_mm": [d.field_length_mm, d.field_width_mm],
        "hydraulic_diameter_mm": g["dh"] / MM,
        "flow_length_mm": g["flow_length_mm"],
        "wetted_area_cm2": g["a_wetted"] * 1e4,
        "area_enhancement": g["a_wetted"] / g["a_field"],
    }
    for key in ("channel_count", "pitch_mm", "passes_per_path", "parallel_paths", "pin_count", "pin_rows"):
        if key in g:
            geometry[key] = g[key]
    if d.channel_width_mm:
        geometry["channel_aspect_ratio"] = d.channel_depth_mm / d.channel_width_mm
        geometry["fin_aspect_ratio"] = d.channel_depth_mm / d.fin_thickness_mm

    return {
        "design": d.to_dict(),
        "operating_point": asdict(op),
        "geometry": geometry,
        "coolant": {"bulk_mean_c": t_bulk, "rho": fp.rho, "cp": fp.cp, "mu_mpa_s": fp.mu * 1e3,
                    "k": fp.k, "pr": fp.pr, "mass_flow_kg_s": m_dot},
        "hydraulics": {
            "velocity_m_s": g["velocity"],
            "port_velocity_m_s": v_port,
            "reynolds": g["re"],
            "regime": g["regime"],
            "dp_kpa": dp_total / 1e3,
            "dp_breakdown_kpa": {k: v / 1e3 for k, v in g["dp_parts"].items()},
            "pumping_power_w": pd.pumping_power(dp_total, q),
        },
        "heat_transfer": {
            "nusselt": g["nu"],
            "h_w_m2k": g["h"],
            "fin_efficiency": g["fin_efficiency"],
            "h_eff_footprint_w_m2k": g["h_eff"],
        },
        "thermal": {
            "t_case_c": t_case,
            "t_outlet_c": t_out,
            "coolant_rise_c": t_out - op.inlet_c,
            "r_case_to_inlet_k_w": net.total,
            "r_breakdown_k_w": net.as_dict(),
            "dt_breakdown_c": {k: v * op.power_w for k, v in net.as_dict().items() if k != "total"},
        },
        "mass_kg": plate_vol * s.rho * 0.85,  # ~15% material removed (channels, ports)
    }


def check_against_limits(result: dict, max_case_c: float, max_dp_kpa: float) -> dict:
    t = result["thermal"]["t_case_c"]
    dp = result["hydraulics"]["dp_kpa"]
    return {
        "t_case_c": t, "max_case_c": max_case_c, "thermal_margin_c": max_case_c - t,
        "dp_kpa": dp, "max_dp_kpa": max_dp_kpa, "dp_margin_kpa": max_dp_kpa - dp,
        "meets_thermal": t <= max_case_c, "meets_pressure": dp <= max_dp_kpa,
        "meets_all": t <= max_case_c and dp <= max_dp_kpa,
    }


__all__ = ["DesignParams", "OperatingPoint", "evaluate_design", "check_against_limits", "TOPOLOGIES"]
