import math

import pytest

from engineering import convection as cv
from engineering import pressure_drop as pd
from engineering.design import DesignParams, OperatingPoint, evaluate_design
from engineering.dfm import check_manufacturability
from engineering.materials import coolant_props, mass_flow
from engineering.process import plan_process, _round_up_stock
from engineering.qa import qa_requirements, sample_size
from engineering.thermal_network import spreading_resistance, build_network, case_temperature
from engineering.verification import verify_design

OP = dict(power_w=1000, source_length_mm=50, source_width_mm=40, inlet_c=35, coolant="water", flow_lpm=1.5)
MICRO = dict(topology="straight_microchannel", channel_width_mm=0.3, fin_thickness_mm=0.25,
             channel_depth_mm=3.0, field_length_mm=60, field_width_mm=55)


# --- properties -------------------------------------------------------------

def test_water_properties_25c():
    p = coolant_props("water", 25.0)
    assert p.rho == pytest.approx(997.0, abs=1.0)
    assert p.mu == pytest.approx(0.890e-3, rel=0.03)
    assert p.k == pytest.approx(0.607, rel=0.02)
    assert p.pr == pytest.approx(6.1, rel=0.05)


def test_pg25_more_viscous_less_conductive_than_water():
    w, g = coolant_props("water", 40), coolant_props("PG25", 40)
    assert g.mu > 1.8 * w.mu and g.k < w.k and g.cp < w.cp


def test_unknown_coolant_rejected():
    with pytest.raises(ValueError):
        coolant_props("mercury", 30)


# --- convection ---------------------------------------------------------------

def test_hydraulic_diameter():
    assert cv.hydraulic_diameter(2.0, 2.0) == pytest.approx(2.0)
    assert cv.hydraulic_diameter(1000.0, 1.0) == pytest.approx(2.0, rel=0.01)  # parallel plates -> 2h


def test_shah_london_limits():
    assert cv.nu_laminar_rect_h1(1.0) == pytest.approx(3.61, abs=0.01)
    assert cv.nu_laminar_rect_h1(0.0) == pytest.approx(8.235)
    assert cv.f_darcy_laminar_rect(1000, 1.0) * 1000 == pytest.approx(56.9, abs=0.1)
    assert cv.f_darcy_laminar_rect(1000, 0.0) * 1000 == pytest.approx(96.0)


def test_gnielinski_close_to_dittus_boelter():
    nu = cv.nu_gnielinski(1e4, 0.7)
    db = 0.023 * 1e4**0.8 * 0.7**0.4
    assert nu == pytest.approx(db, rel=0.10)


def test_petukhov_close_to_blasius():
    assert cv.f_darcy_petukhov(1e4) == pytest.approx(0.316 * 1e4**-0.25, rel=0.03)


@pytest.mark.parametrize("re_edge", [cv.RE_LAMINAR_MAX, cv.RE_TURBULENT_MIN])
def test_transition_is_continuous(re_edge):
    for fn in (lambda r: cv.nusselt_rect_duct(r, 5.0, 0.2), lambda r: cv.friction_factor_rect_duct(r, 0.2)):
        assert fn(re_edge - 1e-6) == pytest.approx(fn(re_edge + 1e-6), rel=1e-4)


def test_regimes():
    assert cv.flow_regime(500) == "laminar"
    assert cv.flow_regime(2600) == "transitional"
    assert cv.flow_regime(1e4) == "turbulent"


def test_fin_efficiency():
    # mL = 1 -> tanh(1)/1
    h, k, t = 1000.0, 400.0, 0.001
    m = math.sqrt(2 * h / (k * t))
    assert cv.fin_efficiency_straight(h, k, t, 1.0 / m) == pytest.approx(math.tanh(1.0))
    assert cv.fin_efficiency_straight(1e-6, 400.0, 0.001, 0.001) == pytest.approx(1.0, abs=1e-6)


def test_pin_bank_velocity_factor_and_continuity():
    assert cv.pin_bank_vmax_factor(3.0, 2.6, 1.5) == pytest.approx(2.0)
    # tight longitudinal pitch -> diagonal section governs
    assert cv.pin_bank_vmax_factor(3.0, 1.0, 1.5) > 2.0
    for edge in (100.0, 1000.0):
        lo = cv.nu_zukauskas_staggered(edge * 0.9999, 5.0, 3.0, 2.6, 20)
        hi = cv.nu_zukauskas_staggered(edge * 1.0001, 5.0, 3.0, 2.6, 20)
        assert lo == pytest.approx(hi, rel=1e-3)


def test_row_correction():
    assert cv.zukauskas_row_correction(1) == 0.64
    assert cv.zukauskas_row_correction(30) == 1.0
    assert cv.zukauskas_row_correction(6) == pytest.approx(0.935)


# --- pressure drop -------------------------------------------------------------

def test_darcy_weisbach_hand_calc():
    # f=0.02, L/D=100, rho=1000, V=2 -> 0.02*100*2000 = 4000 Pa
    assert pd.darcy_weisbach(0.02, 1.0, 0.01, 1000.0, 2.0) == pytest.approx(4000.0)


def test_expansion_k():
    assert pd.expansion_k(0.0) == 1.0 and pd.expansion_k(1.0) == 0.0


def test_pin_bank_drag_decreases_with_re():
    assert pd.pin_bank_drag_coefficient(100, 2.0, 1.73) > pd.pin_bank_drag_coefficient(1000, 2.0, 1.73)


# --- thermal network ------------------------------------------------------------

def test_spreading_zero_when_source_covers_plate():
    assert spreading_resistance(1e-3, 1e-3, 0.002, 390, 20000) == 0.0


def test_spreading_grows_as_source_shrinks():
    big = spreading_resistance(20e-4, 30e-4, 0.0015, 390, 30000)
    small = spreading_resistance(5e-4, 30e-4, 0.0015, 390, 30000)
    assert small > big > 0


def test_network_sums_and_caloric_term():
    net = build_network(1000, 0.025, 4180, 30000, 33e-4, 390, 0.0015, 20e-4, 0.08)
    assert net.caloric == pytest.approx(1 / (2 * 0.025 * 4180))
    assert case_temperature(35, 1000, net) == pytest.approx(35 + 1000 * net.total)


# --- full evaluation ---------------------------------------------------------------

def test_microchannel_matches_hand_calculation():
    r = evaluate_design(MICRO, OP)
    p = coolant_props("water", r["coolant"]["bulk_mean_c"])
    n = r["geometry"]["channel_count"]
    assert n == int((55 + 0.25) // 0.55)
    q = 1.5 / 60000
    v = q / (n * 0.3e-3 * 3e-3)
    dh = 2 * 0.3 * 3 / 3.3 * 1e-3
    re = p.rho * v * dh / p.mu
    assert r["hydraulics"]["velocity_m_s"] == pytest.approx(v)
    assert r["hydraulics"]["reynolds"] == pytest.approx(re)
    f = cv.f_darcy_laminar_rect(re, 0.1)
    assert r["hydraulics"]["dp_breakdown_kpa"]["channel_friction"] == pytest.approx(
        f * (0.06 / dh) * 0.5 * p.rho * v**2 / 1e3)
    h = cv.nu_laminar_rect_h1(0.1) * p.k / dh
    assert r["heat_transfer"]["h_w_m2k"] == pytest.approx(h)


def test_energy_balance_and_case_temperature_includes_coolant_rise():
    r = evaluate_design(MICRO, OP)
    m = r["coolant"]["mass_flow_kg_s"]
    cp = r["coolant"]["cp"]
    assert r["thermal"]["coolant_rise_c"] == pytest.approx(1000 / (m * cp))
    assert r["thermal"]["dt_breakdown_c"]["caloric"] == pytest.approx(0.5 * r["thermal"]["coolant_rise_c"])
    assert r["thermal"]["t_case_c"] > r["coolant"]["bulk_mean_c"]


def test_more_flow_cooler_but_higher_dp():
    lo = evaluate_design(MICRO, OP)
    hi = evaluate_design(MICRO, {**OP, "flow_lpm": 3.0})
    assert hi["thermal"]["t_case_c"] < lo["thermal"]["t_case_c"]
    assert hi["hydraulics"]["dp_kpa"] > lo["hydraulics"]["dp_kpa"]


def test_copper_beats_aluminium():
    cu = evaluate_design(MICRO, OP)
    al = evaluate_design({**MICRO, "material": "Al6061"}, OP)
    assert cu["thermal"]["t_case_c"] < al["thermal"]["t_case_c"]


def test_all_topologies_evaluate():
    for d in (MICRO,
              dict(topology="pin_fin", pin_diameter_mm=1.5, pin_pitch_transverse_mm=3.0, pin_pitch_longitudinal_mm=2.6),
              dict(topology="serpentine", channel_width_mm=1.5, fin_thickness_mm=1.0, parallel_paths=2)):
        r = evaluate_design(d, OP)
        assert 35 < r["thermal"]["t_case_c"] < 150
        assert r["hydraulics"]["dp_kpa"] > 0


def test_invalid_designs_rejected():
    with pytest.raises(ValueError):
        evaluate_design({"topology": "vortex"}, OP)
    with pytest.raises(ValueError):
        evaluate_design(dict(topology="pin_fin", pin_diameter_mm=2, pin_pitch_transverse_mm=1.5,
                             pin_pitch_longitudinal_mm=2), OP)
    with pytest.raises(ValueError):
        DesignParams.from_dict({"topology": "pin_fin", "bogus": 1})


# --- DFM / process / QA / verification ---------------------------------------------

def test_dfm_flags_tall_thin_fins():
    res = check_manufacturability({**MICRO, "fin_thickness_mm": 0.15, "channel_depth_mm": 3.0})
    failed = {c["rule"] for c in res["checks"] if not c["pass"]}
    assert not res["manufacturable"]
    assert "Fin thickness" in failed and "Fin height / thickness" in failed


def test_dfm_passes_reasonable_design():
    assert check_manufacturability(MICRO)["manufacturable"]


def test_process_plan():
    assert _round_up_stock(6.5) == 8.0
    p = plan_process(MICRO, quantity=10)
    assert p["cycle_time_min_per_part"] > 0
    assert p["batch_cost_usd"] == pytest.approx(p["cost_per_part_usd"]["total"] * 10, rel=1e-3)
    assert [o["seq"] for o in p["operations"]] == sorted(o["seq"] for o in p["operations"])
    assert {"CNC", "FSW", "LEAK"} <= set(p["minutes_per_part_by_station"])


def test_qa_requirements():
    assert sample_size(5) == 2 and sample_size(40) == 8 and sample_size(100) == 20
    r = evaluate_design(MICRO, OP)
    q = qa_requirements(MICRO, r, 40)
    assert q["leak_test"]["proof_pressure_bar"] == pytest.approx(6.0)
    assert q["leak_test"]["decay_hold_s"] >= 60
    assert q["internal_volume_ml"] > 0


def test_verification_detects_failures():
    v = verify_design(MICRO, OP, max_case_c=80, max_dp_kpa=50)
    assert v["verdict"] == "PASS", v["failures"]
    v2 = verify_design(MICRO, OP, max_case_c=40, max_dp_kpa=50)
    assert v2["verdict"] == "FAIL"
    assert any(f["check"].startswith("Case temperature") for f in v2["failures"])
    assert v["worst_case"]["dp_kpa"] > v["nominal"]["dp_kpa"]
    assert v["worst_case"]["t_case_c"] > v["nominal"]["t_case_c"]


def test_mass_flow():
    assert mass_flow("water", 25, 60.0) == pytest.approx(0.997, rel=0.01)


# --- spec check ---------------------------------------------------------------------

from datetime import date as _date  # noqa: E402

from engineering.spec_check import validate_spec  # noqa: E402

GOOD_SPEC = dict(tdp_w=1200, heat_source_length_mm=55, heat_source_width_mm=45, max_case_temp_c=60,
                 coolant="PG25", inlet_temp_c=40, flow_rate_lpm=1.8, max_pressure_drop_kpa=15,
                 quantity=40, deadline="2030-01-01")


def test_spec_accepted_with_defaults_noted():
    r = validate_spec(GOOD_SPEC, today=_date(2029, 12, 1))
    assert r["accepted"]
    assert r["normalized_spec"]["tim_resistance_cm2k_w"] == 0.08
    assert r["derived"]["case_temp_floor_c"] < 60
    assert any(i["severity"] == "info" for i in r["issues"])


def test_spec_missing_and_infeasible():
    s = {k: v for k, v in GOOD_SPEC.items() if k != "quantity"}
    r = validate_spec(s, today=_date(2029, 12, 1))
    assert not r["accepted"] and any(i["field"] == "quantity" for i in r["issues"])
    r2 = validate_spec({**GOOD_SPEC, "flow_rate_lpm": 0.3, "max_case_temp_c": 55}, today=_date(2029, 12, 1))
    assert not r2["accepted"]
    assert any("Infeasible" in i["message"] for i in r2["issues"])


def test_spec_bad_values():
    r = validate_spec({**GOOD_SPEC, "coolant": "R134a", "deadline": "2020-01-01"}, today=_date(2029, 12, 1))
    fields = {i["field"] for i in r["issues"] if i["severity"] == "error"}
    assert {"coolant", "deadline"} <= fields
