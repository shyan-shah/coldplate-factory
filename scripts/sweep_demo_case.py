"""Sweep candidate designs against the demo spec to pick a case with a genuine verification rejection."""
from engineering.design import evaluate_design
from engineering.verification import verify_design
from engineering.dfm import check_manufacturability

OP = dict(power_w=1200, source_length_mm=55, source_width_mm=45, inlet_c=40, coolant="PG25", flow_lpm=1.8)
BASE = dict(field_length_mm=60, field_width_mm=55, plate_length_mm=90, plate_width_mm=80, base_thickness_mm=1.5)
cands = []
for w in (0.2, 0.25, 0.3, 0.35, 0.4, 0.5):
    for t in (0.15, 0.2, 0.25, 0.3):
        for H in (2.0, 2.5, 3.0, 3.5, 4.0):
            cands.append(dict(topology="straight_microchannel", channel_width_mm=w, fin_thickness_mm=t, channel_depth_mm=H, **BASE))
for D, st, sl in ((1.0, 2.0, 1.75), (1.2, 2.2, 1.9), (1.5, 2.6, 2.25), (1.5, 3.0, 2.6), (2.0, 3.0, 2.6)):
    for H in (2.0, 3.0, 4.0):
        cands.append(dict(topology="pin_fin", pin_diameter_mm=D, pin_pitch_transverse_mm=st, pin_pitch_longitudinal_mm=sl, channel_depth_mm=H, **BASE))
for w, t, p in ((1.0, 0.8, 1), (1.5, 1.0, 2), (2.0, 1.0, 2), (2.0, 1.0, 4), (3.0, 1.0, 4)):
    for H in (2.0, 3.0, 4.0):
        cands.append(dict(topology="serpentine", channel_width_mm=w, fin_thickness_mm=t, parallel_paths=p, channel_depth_mm=H, **BASE))
import sys
TMAX = float(sys.argv[1]) if len(sys.argv) > 1 else 58
DPMAX = float(sys.argv[2]) if len(sys.argv) > 2 else 25
rows = []
for d in cands:
    try:
        r = evaluate_design(d, OP)
    except ValueError as e:
        continue
    v = verify_design(d, OP, TMAX, DPMAX)
    fails = [f["check"] for f in v["failures"]]
    key = d["topology"][:5], d.get("channel_width_mm") or d.get("pin_diameter_mm"), d.get("fin_thickness_mm") or d.get("pin_pitch_transverse_mm"), d.get("parallel_paths", ""), d["channel_depth_mm"]
    rows.append((r["thermal"]["t_case_c"], key, round(r["hydraulics"]["dp_kpa"],1), round(v["worst_case"]["t_case_c"],2), round(v["worst_case"]["dp_kpa"],1), round(r["hydraulics"]["velocity_m_s"],2), fails))
rows.sort()
for row in rows: print(round(row[0],2), *row[1:])
