"""Internal-flow and pin-bank convection correlations.

Rectangular ducts:
  - Laminar, hydrodynamically and thermally fully developed, H1 boundary condition:
    Shah & London (1978) polynomial in aspect ratio.  Square duct -> Nu = 3.61,
    parallel plates -> Nu = 8.235.  (Fully developed is conservative for short
    microchannels, where the entrance region raises h.)
  - Turbulent: Gnielinski (1976) with Petukhov friction factor, 3000 <= Re <= 5e6.
  - 2300 < Re < 3000: linear blend between the two, so Nu(Re) is continuous.
Pin-fin banks (staggered): Zukauskas (1972) with row-number correction.
Fins: straight/pin fin efficiency with adiabatic tip, eta = tanh(mL)/(mL).
"""
from __future__ import annotations

import math

RE_LAMINAR_MAX = 2300.0
RE_TURBULENT_MIN = 3000.0


def hydraulic_diameter(width: float, height: float) -> float:
    """Dh = 4A/P for a rectangular duct (any consistent length unit)."""
    if width <= 0 or height <= 0:
        raise ValueError("duct width and height must be positive")
    return 2.0 * width * height / (width + height)


def aspect_ratio(width: float, height: float) -> float:
    """Short side / long side, 0 < alpha <= 1."""
    return min(width, height) / max(width, height)


def reynolds(rho: float, velocity: float, length: float, mu: float) -> float:
    return rho * velocity * length / mu


def flow_regime(re: float) -> str:
    if re <= RE_LAMINAR_MAX:
        return "laminar"
    if re < RE_TURBULENT_MIN:
        return "transitional"
    return "turbulent"


def nu_laminar_rect_h1(alpha: float) -> float:
    """Shah & London fully developed laminar Nu (H1) for a rectangular duct."""
    a = alpha
    return 8.235 * (1 - 2.0421 * a + 3.0853 * a**2 - 2.4765 * a**3 + 1.0578 * a**4 - 0.1861 * a**5)


def f_darcy_laminar_rect(re: float, alpha: float) -> float:
    """Darcy friction factor, fully developed laminar flow, rectangular duct (Shah & London)."""
    a = alpha
    f_re = 96.0 * (1 - 1.3553 * a + 1.9467 * a**2 - 1.7012 * a**3 + 0.9564 * a**4 - 0.2537 * a**5)
    return f_re / re


def f_darcy_petukhov(re: float) -> float:
    """Petukhov smooth-tube Darcy friction factor (3000 <= Re <= 5e6)."""
    return (0.790 * math.log(re) - 1.64) ** -2


def nu_gnielinski(re: float, pr: float) -> float:
    f = f_darcy_petukhov(re)
    return (f / 8.0) * (re - 1000.0) * pr / (1.0 + 12.7 * math.sqrt(f / 8.0) * (pr ** (2.0 / 3.0) - 1.0))


def _blend_weight(re: float) -> float:
    return (re - RE_LAMINAR_MAX) / (RE_TURBULENT_MIN - RE_LAMINAR_MAX)


def nusselt_rect_duct(re: float, pr: float, alpha: float) -> float:
    if re <= RE_LAMINAR_MAX:
        return nu_laminar_rect_h1(alpha)
    if re >= RE_TURBULENT_MIN:
        return nu_gnielinski(re, pr)
    w = _blend_weight(re)
    return (1 - w) * nu_laminar_rect_h1(alpha) + w * nu_gnielinski(RE_TURBULENT_MIN, pr)


def friction_factor_rect_duct(re: float, alpha: float) -> float:
    """Darcy friction factor with the same laminar/transition/turbulent treatment as Nu."""
    if re <= RE_LAMINAR_MAX:
        return f_darcy_laminar_rect(re, alpha)
    if re >= RE_TURBULENT_MIN:
        return f_darcy_petukhov(re)
    w = _blend_weight(re)
    return (1 - w) * f_darcy_laminar_rect(RE_LAMINAR_MAX, alpha) + w * f_darcy_petukhov(RE_TURBULENT_MIN)


# --- fins ------------------------------------------------------------------

def fin_efficiency_straight(h: float, k_solid: float, thickness: float, height: float) -> float:
    """Straight rectangular fin (channel wall), adiabatic tip. m = sqrt(2h / (k t))."""
    m = math.sqrt(2.0 * h / (k_solid * thickness))
    ml = m * height
    return 1.0 if ml < 1e-9 else math.tanh(ml) / ml


def fin_efficiency_pin(h: float, k_solid: float, diameter: float, height: float) -> float:
    """Cylindrical pin fin, adiabatic tip. m = sqrt(4h / (k D))."""
    m = math.sqrt(4.0 * h / (k_solid * diameter))
    ml = m * height
    return 1.0 if ml < 1e-9 else math.tanh(ml) / ml


# --- staggered pin-fin bank ------------------------------------------------

_ROW_CORR_STAGGERED = [(1, 0.64), (2, 0.76), (3, 0.84), (4, 0.89), (5, 0.92), (7, 0.95),
                       (10, 0.97), (13, 0.98), (16, 0.99), (20, 1.0)]


def zukauskas_row_correction(n_rows: int) -> float:
    if n_rows >= 20:
        return 1.0
    if n_rows <= 1:
        return 0.64
    for (n0, c0), (n1, c1) in zip(_ROW_CORR_STAGGERED, _ROW_CORR_STAGGERED[1:]):
        if n0 <= n_rows <= n1:
            return c0 + (c1 - c0) * (n_rows - n0) / (n1 - n0)
    return 1.0


def pin_bank_vmax_factor(st: float, sl: float, d: float) -> float:
    """Ratio V_max / V_approach for a staggered bank (Incropera eq. 7.60/7.61)."""
    sd = math.sqrt(sl**2 + (st / 2.0) ** 2)
    if 2.0 * (sd - d) < (st - d):
        return st / (2.0 * (sd - d))
    return st / (st - d)


def nu_zukauskas_staggered(re_dmax: float, pr: float, st: float, sl: float, n_rows: int) -> float:
    """Average Nu_D for a staggered pin bank.

    Zukauskas: 10-100: C=0.90, m=0.40; 1e3-2e5: C=0.35 (ST/SL)^0.2, m=0.60.
    100-1000 (the 'isolated cylinder' band in the original tables) is bridged by
    log-linear interpolation so the result is continuous.
    """
    def band_low(re):
        return 0.90 * re**0.40

    def band_high(re):
        return 0.35 * (st / sl) ** 0.2 * re**0.60

    if re_dmax <= 100.0:
        nu = band_low(max(re_dmax, 1.0))
    elif re_dmax >= 1000.0:
        nu = band_high(re_dmax)
    else:
        x = (math.log10(re_dmax) - 2.0)
        nu = 10 ** ((1 - x) * math.log10(band_low(100.0)) + x * math.log10(band_high(1000.0)))
    return nu * pr**0.36 * zukauskas_row_correction(n_rows)


def heat_transfer_coefficient(nu: float, k_fluid: float, length: float) -> float:
    return nu * k_fluid / length
