"""Pressure drop: Darcy-Weisbach major losses, minor-loss coefficients, pin-bank losses.

Channel friction uses the Darcy friction factor from convection.friction_factor_rect_duct.
Minor losses (K-factors, Idelchik / Crane TP-410 typical values):
  - inlet port + 90 deg turn into plenum ......... K = 1.0 (at port velocity)
  - outlet plenum + 90 deg turn into port ........ K = 1.5 (at port velocity)
  - plenum -> channels sudden contraction ........ K_c = 0.5 (at channel velocity)
  - channels -> plenum sudden expansion .......... K_e = (1 - sigma)^2 (at channel velocity)
  - sharp 180 deg bend in a rectangular channel .. K = 2.2 (serpentine)
Pin banks: Gaddis & Gnielinski (VDI Heat Atlas) staggered-bank drag coefficient.
"""
from __future__ import annotations

import math

K_PORT_IN = 1.0
K_PORT_OUT = 1.5
K_CONTRACTION = 0.5
K_BEND_180 = 2.2


def dynamic_pressure(rho: float, velocity: float) -> float:
    return 0.5 * rho * velocity**2


def darcy_weisbach(f_darcy: float, length: float, dh: float, rho: float, velocity: float) -> float:
    """Major loss, Pa.  dP = f (L/Dh) rho V^2 / 2."""
    return f_darcy * (length / dh) * dynamic_pressure(rho, velocity)


def minor_loss(k: float, rho: float, velocity: float) -> float:
    return k * dynamic_pressure(rho, velocity)


def expansion_k(area_ratio: float) -> float:
    """Borda-Carnot sudden expansion, sigma = small/large flow area."""
    return (1.0 - area_ratio) ** 2


def port_losses(rho: float, flow_m3s: float, port_d: float) -> tuple[float, float]:
    """Inlet and outlet port/plenum losses (Pa), and the port velocity (m/s)."""
    v = flow_m3s / (math.pi * port_d**2 / 4.0)
    return minor_loss(K_PORT_IN + K_PORT_OUT, rho, v), v


def pin_bank_drag_coefficient(re: float, a: float, b: float) -> float:
    """Gaddis-Gnielinski staggered bank drag coefficient xi (per row), Re on D and V_max.

    a = ST/D (transverse pitch ratio), b = SL/D (longitudinal pitch ratio).
    """
    if b >= 0.5 * math.sqrt(2 * a + 1):
        c = a
    else:
        c = math.sqrt((a / 2.0) ** 2 + b**2)
    xi_lam = 280.0 * math.pi * ((b**0.5 - 0.6) ** 2 + 0.75) / ((4 * a * b - math.pi) * c**1.6) / re
    xi_turb = (2.5 + 1.2 / (a - 0.85) ** 1.08 + 0.4 * (b / a - 1) ** 3 - 0.01 * (a / b - 1) ** 3) * re**-0.25
    return xi_lam + xi_turb * (1.0 - math.exp(-(re + 1000.0) / 2000.0))


def pin_bank_pressure_drop(re: float, a: float, b: float, n_rows: int, rho: float, v_max: float) -> float:
    return pin_bank_drag_coefficient(re, a, b) * n_rows * dynamic_pressure(rho, v_max)


def pumping_power(dp: float, flow_m3s: float) -> float:
    return dp * flow_m3s
