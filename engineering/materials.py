"""Solid and coolant property data.

All values SI. Coolant properties are evaluated at a film/bulk temperature in degC.
Water: standard engineering fits (density: Tanaka 2001, viscosity: Vogel equation,
conductivity: IAPWS-style quadratic). PG25 (25 wt% propylene glycol): fits to
manufacturer tables, within ~5% over 10-70 degC.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Solid:
    key: str
    name: str
    k: float            # thermal conductivity, W/m-K
    rho: float          # density, kg/m3
    cost_per_kg: float  # plate stock cost, USD/kg
    machinability: float  # relative MRR factor (Al6061 = 1.0)
    fsw_traverse_mm_min: float  # friction-stir-weld traverse speed


SOLIDS: dict[str, Solid] = {
    "C110": Solid("C110", "Copper C11000 (ETP)", k=388.0, rho=8940.0, cost_per_kg=16.0,
                  machinability=0.45, fsw_traverse_mm_min=150.0),
    "Al6061": Solid("Al6061", "Aluminium 6061-T6", k=167.0, rho=2700.0, cost_per_kg=7.0,
                    machinability=1.0, fsw_traverse_mm_min=400.0),
}


@dataclass(frozen=True)
class FluidProps:
    rho: float  # kg/m3
    cp: float   # J/kg-K
    mu: float   # Pa-s
    k: float    # W/m-K

    @property
    def pr(self) -> float:
        return self.cp * self.mu / self.k


def _water(t_c: float) -> FluidProps:
    rho = 1000.0 * (1.0 - (t_c + 288.9414) / (508929.2 * (t_c + 68.12963)) * (t_c - 3.9863) ** 2)
    t_k = t_c + 273.15
    mu = 2.414e-5 * 10.0 ** (247.8 / (t_k - 140.0))
    tr = t_k / 298.15
    k = 0.6065 * (-1.48445 + 4.12292 * tr - 1.63866 * tr ** 2)
    cp = 4180.0  # varies < 0.5% over 15-70 degC
    return FluidProps(rho=rho, cp=cp, mu=mu, k=k)


def _pg25(t_c: float) -> FluidProps:
    w = _water(t_c)
    return FluidProps(rho=1027.0 - 0.40 * t_c, cp=3860.0 + 2.0 * t_c, mu=2.05 * w.mu, k=0.78 * w.k)


COOLANTS = {
    "water": ("Water (treated, inhibited)", _water),
    "PG25": ("25% propylene glycol / water", _pg25),
}


def coolant_props(coolant: str, t_c: float) -> FluidProps:
    if coolant not in COOLANTS:
        raise ValueError(f"Unknown coolant '{coolant}'. Known: {sorted(COOLANTS)}")
    if not (0.0 <= t_c <= 90.0):
        raise ValueError(f"Coolant temperature {t_c} degC outside property-fit range 0-90 degC")
    return COOLANTS[coolant][1](t_c)


def solid(key: str) -> Solid:
    if key not in SOLIDS:
        raise ValueError(f"Unknown material '{key}'. Known: {sorted(SOLIDS)}")
    return SOLIDS[key]


def lpm_to_m3s(lpm: float) -> float:
    return lpm / 1000.0 / 60.0


def mass_flow(coolant: str, t_c: float, lpm: float) -> float:
    return coolant_props(coolant, t_c).rho * lpm_to_m3s(lpm)


__all__ = ["Solid", "SOLIDS", "FluidProps", "COOLANTS", "coolant_props", "solid",
           "lpm_to_m3s", "mass_flow"]
