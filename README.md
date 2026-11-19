# Cold Plate Agent Factory (demo)

> AI designs and manufactures the cooling for AI. Weeks become days.

A customer submits a chip thermal spec. Six agents take it from spec to a manufacturing-ready job, handing off to each other on screen: intake, thermal design, verification (which can reject back to design), process planning, scheduling on a mock factory cell, and QA planning. The job then stops at an **engineer approval gate**. Designs are parameter sets only (no CAD); the released parameter set is what you model in Inventor.

**Agents decide; tools compute.** Every number on screen comes from deterministic Python in `engineering/` and `factory/`. The verification agent recomputes from the parameter set rather than trusting the design agent. Submit tools reject inconsistent decisions, for example approving a design whose checks failed.

## Run it

```
run.bat            # Windows: creates .venv, installs, opens http://localhost:8077
./run.sh           # macOS / Linux
```

Or by hand: `py -3.12 -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt`, `.venv\Scripts\python -m uvicorn app.main:app --port 8077`.

### Modes

| Mode | When | What runs |
|---|---|---|
| **Live** | `ANTHROPIC_API_KEY` set in `.env` | Each agent is a Claude tool-use loop (model from `CLAUDE_MODEL`, default `claude-opus-5-5`). Reasoning summaries and text stream into the feed. |
| **Scripted replay** | no key, or chosen in the UI | Same orchestrator, same tools and physics. Only the agents' choices and prose are scripted. Works offline with no API cost. The header badge says which mode is on. |

The mode drop-down next to *Submit* overrides the default per job. **Use scripted mode as the fallback for the call if Wi-Fi or the API misbehaves.**

Settings in `.env` (see `.env.example`):

| Variable | Purpose |
|---|---|
| `CLAUDE_MODEL` | Model ID for all agents |
| `AGENT_EFFORT` | `low` / `medium` / `high` for most agents (default `low`, keeps a live run short) |
| `DESIGN_AGENT_EFFORT` | Effort for the thermal design agent (default `medium`) |
| `ENABLE_FALLBACKS` | `1` sends server-side refusal fallbacks (`fallbacks: "default"`) on models that support them; `0` disables. If the API rejects it, the runner retries without it. |
| `SCRIPTED_STEP_DELAY` | Pacing of scripted mode in seconds (default 0.6; a full run takes about 1 minute) |

## Demo walkthrough (about 3 minutes)

1. The **HX-1200** request is pre-loaded: 1.2 kW accelerator, 55 x 45 mm lid, max case 60 °C, PG25 at 40 °C, 1.8 L/min, ΔP ≤ 15 kPa, 40 pcs. Click **Submit to factory**.
2. **Intake** checks the spec. Coolant rise and TIM alone fix a case-temperature floor of 48.9 °C, which leaves 11 °C for the plate.
3. **Thermal design** evaluates a microchannel, a pin fin and a serpentine. Pin fin and serpentine miss the limits. It then sweeps 24 microchannel variants (watch the *Design* tab scatter) and picks the coolest.
4. **Verification rejects it**, twice, for real reasons:
   - Round 1: channel depth/width is 15:1, beyond the 12:1 limit of the gang slitting saw (DFM).
   - Round 2: worst-case ΔP is 16.0 kPa against the 15 kPa limit. The -0.02 mm cutter tolerance matters on 0.20 mm channels.
   - The design agent turns each finding into a sweep constraint and lands on 0.25/0.20 x 3.0 mm channels: 56.7 °C nominal (58.5 worst case), 5.3 kPa.
5. **Process planning** builds a 9-op routing: gang-saw channels, FSW lid, post-weld skim, leak test. It runs 64 min/part at about $109/part.
6. **Scheduling** books lots around the existing jobs and planned downtime (spindle service, FSW calibration, leak rig calibration). Delivery lands a few days before the deadline (business-day shipping; exact slack depends on the day you run it).
7. **QA** sets the inspection plan: 100% contact-face flatness on CMM, 6 bar proof test, pressure-decay hold time derived from internal volume, and flow and thermal (TTV) acceptance limits taken from the predictions.
8. **Approve & release to cell.** The tentative bookings become real ones on the Gantt.

The *Incomplete / infeasible request* demo shows intake stopping a job. Quantity is missing, and 0.6 L/min at 45 °C inlet cannot hold 52 °C even with a perfect plate.

## Architecture

```
app/        FastAPI (REST + /ws event stream), single-page UI (plain JS + hand-rolled SVG charts)
agents/     core.py          tool runtime, LiveRunner (Anthropic Messages API, streaming, manual tool loop),
                             ScriptedSession (scripted choices, same tool executor)
            intake.py, thermal_design.py, verification.py, process_planning.py, scheduling.py, qa.py
                             one module per agent: system prompt, tools, task builder, scripted policy
            orchestrator.py  pipeline, design<->verification rework loop (max 3), approval gate
engineering/                 deterministic models (unit-tested)
factory/    db.py            SQLite: jobs, event log, machines, bookings (re-seeded relative to today on start)
            scheduler.py     finite-capacity, shift-aware, lot-based cell scheduler
tests/                       47 tests: correlations vs hand calcs, scheduler invariants, live loop vs a fake client,
                             end-to-end pipeline
```

Every event is persisted, so reloading the page replays the job. Jobs, approval state and bookings survive in `factory.db`. The factory board is re-seeded on each server start so its dates are always current.

## Engineering models (`engineering/`)

- **Thermal network** (`thermal_network.py`): T_case = T_in + Q·(R_caloric + R_conv + R_base + R_spreading + R_TIM).
  - R_caloric = 1/(2·m·cp) adds the coolant rise to the bulk mean.
  - Spreading uses the Lee, Song, Au & Moran (1995) closed form.
  - TIM2 is R''/A_source.
- **Convection** (`convection.py`):
  - Laminar flow uses Shah & London fully developed rectangular-duct Nu (H1) and fRe.
  - Turbulent flow uses Gnielinski with the Petukhov friction factor.
  - Between Re 2300 and 3000 the two are blended linearly, so Nu and f are continuous.
  - Fin efficiency is tanh(mL)/mL.
  - Pin fins use Zukauskas staggered banks with a row correction.
- **Pressure drop** (`pressure_drop.py`):
  - Darcy-Weisbach for channel friction.
  - Minor losses: ports and plenums, contraction, Borda-Carnot expansion, 180° bends (K = 2.2).
  - Pin banks use the Gaddis-Gnielinski drag coefficient.
- **Verification standard** (`verification.py`):
  - Thermal worst case: flow -5%, TIM2 +25%, fouling 2e-5 m²K/W.
  - Hydraulic worst case: flow +5%, channel width -0.02 mm, depth -0.05 mm.
  - Also checked: erosion velocity limit, heat-source coverage, DFM.
- **DFM** (`dfm.py`):
  - Slitting saw: channel ≥ 0.20 mm, depth/width ≤ 12, fin height/thickness ≤ 15.
  - End-mill limits for pin fins and serpentines.
  - FSW land ≥ 6 mm; base ≥ 1.0 mm.
- **Process, QA and spec check** (`process.py`, `qa.py`, `spec_check.py`):
  - Cycle times come from path length / feed and volume / MRR, with load and tool-change allowances.
  - QA covers ISO 2859-1 sample sizes and pressure-decay hold time from internal volume and leak spec.
  - The spec check covers completeness, plausibility and the feasibility floor.

### Known simplifications (be ready for these questions)

- Fully developed laminar Nu ignores entrance-region enhancement, which is conservative for short microchannels. The 4-wall H1 boundary condition is used even though the lid side is nearly adiabatic.
- The network is 1-D with bulk-mean coolant temperature, so it gives the average case temperature, not a hot-spot map. Next step: a conjugate CFD/FEA check before release.
- PG25 properties are fits, within about 5% over 10-70 °C. Feeds, rates and stock prices are representative figures, not quotes.
- Scheduling is non-preemptive per shift window with greedy lot dispatch. It is not an optimiser.

## Tests

```
.venv\Scripts\python -m pytest -q
```

## Status / not yet done

- **The live (Claude) path has not been run against the real API.** No key was available while building. It is tested against a fake client that emits thinking, text, `tool_use`, refusal and fallback-rejection responses. Before the call, put a key in `.env` and do one full live run. Live agents choose their own designs, so the rejection loop is likely but not guaranteed. Scripted mode always shows it.
- `scripts/sweep_demo_case.py` is the sweep used to pick the demo spec. `scripts/run_pipeline.py [hx1200|bad]` runs the pipeline headless in the terminal.
