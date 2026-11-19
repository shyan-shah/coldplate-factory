"""1-D thermal resistance network from coolant inlet to chip case.

  T_case = T_in + Q * (R_caloric + R_conv + R_base + R_spread + R_TIM)

  R_caloric = 1 / (2 m_dot cp)        coolant temperature rise to the bulk mean
  R_conv    = 1 / (h_eff A_field)     h_eff includes fin area x fin efficiency
  R_base    = t_base / (k A_field)    1-D conduction through the base
  R_spread  = psi / (k r_s sqrt(pi))  Lee, Song, Au & Moran (1995) closed form,
                                      area-averaged source temperature
  R_TIM     = R''_TIM / A_source      TIM2 between chip lid and cold plate

Using the bulk-mean coolant temperature gives the area-averaged case temperature.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict


def spreading_resistance(source_area: float, plate_area: float, thickness: float,
                         k_solid: float, h_eff: float) -> float:
    """Average spreading resistance (K/W) of a centred source on a plate (Lee et al. 1995).

    Areas in m2, thickness in m, h_eff in W/m2K referenced to plate_area.
    Returns 0 when the source covers the whole cooled area.
    """
    if source_area >= plate_area:
        return 0.0
    r_s = math.sqrt(source_area / math.pi)
    r_p = math.sqrt(plate_area / math.pi)
    eps = r_s / r_p
    tau = thickness / r_p
    bi = h_eff * r_p / k_solid
    lam = math.pi + 1.0 / (math.sqrt(math.pi) * eps)
    th = math.tanh(lam * tau)
    phi = (th + lam / bi) / (1.0 + (lam / bi) * th)
    psi_avg = 0.5 * (1.0 - eps) ** 1.5 * phi
    return psi_avg / (k_solid * r_s * math.sqrt(math.pi))


@dataclass
class ResistanceNetwork:
    caloric: float
    convection: float
    base_conduction: float
    spreading: float
    tim: float

    @property
    def total(self) -> float:
        return self.caloric + self.convection + self.base_conduction + self.spreading + self.tim

    def as_dict(self) -> dict:
        d = asdict(self)
        d["total"] = self.total
        return d


def build_network(power_w: float, m_dot: float, cp: float, h_eff: float, field_area: float,
                  k_solid: float, base_thickness: float, source_area: float,
                  tim_r_cm2k_w: float) -> ResistanceNetwork:
    if m_dot <= 0:
        raise ValueError("mass flow must be positive")
    return ResistanceNetwork(
        caloric=1.0 / (2.0 * m_dot * cp),
        convection=1.0 / (h_eff * field_area),
        base_conduction=base_thickness / (k_solid * field_area),
        spreading=spreading_resistance(source_area, field_area, base_thickness, k_solid, h_eff),
        tim=(tim_r_cm2k_w * 1e-4) / source_area,
    )


def case_temperature(inlet_c: float, power_w: float, net: ResistanceNetwork) -> float:
    return inlet_c + power_w * net.total
