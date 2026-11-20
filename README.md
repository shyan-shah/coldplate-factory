# Loopwerks test lab (demo)

> Autonomous test labs for hardware that has to be qualified before it ships. Agents plan the work, robots execute it, results feed back.

This is the `test-lab` branch. It repurposes the six-agent cold plate factory demo (still on `master`) into the pipeline for a robot-run test and qualification lab for liquid cooling components.

A component maker submits a test request: the component spec, the target standard, the samples they will send and the date the report is needed. Six agents take it from request to a campaign ready for release, handing off to each other on screen:

1. **Intake** checks the request.
2. **Campaign Planner** turns spec plus standard into a test campaign: tests, sample sequences, parameters, durations and acceptance criteria.
3. **Verification** checks the plan against the standard's requirements and can reject it back to the planner.
4. **Test Procedure** turns the campaign into rig operations and cobot handling tasks.
5. **Scheduling** books it onto mock rigs, a cobot and partner labs.
6. **Report (QA)** writes the qualification report.

The job then stops at an **engineer release gate**. Nothing runs until an engineer releases it.

**Honest status.** The rigs and the robot cell are not built. Every rig, booking and partner lab in this demo is mock data, labelled as such. The report is a **simulated dry run**: values come from mock rigs driven by the maker's claimed figures, so the customer sees the report format and the failure-flagging logic before parts ship. Loopwerks is not a certification body and holds no accreditation.

**Agents decide; tools compute.** Every number on screen comes from deterministic Python in `testlab/` and `factory/`. The verifier recomputes from the step list rather than trusting the planner. Submit tools reject inconsistent decisions, for example approving a campaign whose checks failed.

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
| **Scripted** | no key, or chosen in the UI | Same orchestrator, same tools, same numbers. Only the agents' choices and prose are scripted. Works offline with no API cost. **Use this on the call if Wi-Fi or the API misbehaves.** |

**Replay:** every event is stored in SQLite (`lab.db` on this branch, kept apart from `master`'s `factory.db`). Click any job in the Jobs list, or reload the page, and the whole run replays: feed, pipeline, artifacts and the gate.

Settings in `.env` (see `.env.example`): `CLAUDE_MODEL`, `AGENT_EFFORT` (default `low`), `PLANNER_AGENT_EFFORT` (default `medium`), `ENABLE_FALLBACKS`, `AGENT_MODE`, and `SCRIPTED_STEP_DELAY` (default 0.6 s; a full scripted run takes about a minute).

## Demo script (about 3 minutes)

1. **Set up.** The **CP-1400** request is pre-loaded. It is a fictional maker's single-phase cold plate: 5 bar maximum operating pressure, 1.5 L/min rated flow in PG25, 1,400 W, 6 mm ports, 5 samples, and the report needed in 8 weeks. The target is `OCP-CP-1.0`. Say: "A component maker wants its own qualification data before paying for certification." Click **Submit to lab**.
2. **Intake** derives the test conditions:
   - hydrostatic stage 2 at 15 bar (3x MOP);
   - a pressure-drop span of 0.375 to 2.25 L/min;
   - port velocity of 1.33 m/s at 150 % flow, close to the 1.5 m/s erosion limit.

   It also raises two acceptance limits the standard leaves to the customer (leak rate and flatness).
3. **Campaign Planner** pulls the 18 OCP requirements and the methods list. It puts the bench work on one sample so the cobot can chain it, and spreads the long partner tests (temperature cycling, salt spray, humidity, fluid chemistry) across samples so they run in parallel. To save a sample, it plans on 4 of the 5 (*Campaign* tab shows the lanes).
4. **Verification rejects it**, for real reasons, even though coverage is 18/18:
   - pressure drop at only 4 flow points, spanning 33 % to 133 % of rated flow (the standard needs 6 or more points from 25 % to 150 %);
   - no helium leak test after the shipping temperature cycle (the cycle must be bracketed);
   - the destructive burst test sits mid-sequence on S3, with two more tests after it.

   Point out: "The verifier checks the step list itself. It doesn't trust the planner's summary."
5. **The planner fixes all three.** It adds six points from 25 % to 150 %, a helium test after cycling, and moves burst to its own sample. Verification then passes 34/34.
6. **Test Procedure** lists every rig operation with its fixture and the cobot tasks: pick, connect, confirm seal by force signature, disconnect, drain. That comes to 9.7 h of bench time and 10 cobot handlings, plus a cost estimate at planning rates (not quotes). Partner labs are flagged as not contracted.
7. **Scheduling** books the rigs and the cobot around mock work and planned downtime: cobot service, the helium detector not yet on site, a reference-plate check. Rigs run unattended; the cobot only loads and unloads between 06:00 and 22:00 on weekdays. Partner labs drive the critical path. The report lands before the deadline (exact dates depend on the day you run it).
8. **Report** builds traceability from all 18 requirements to their steps, then runs a **simulated** dry run. It flags thermal resistance at the maker's claim +12 %, over the +10 % criterion, and says what it would do if this were real: repeat on a second sample and check the rig against a reference plate. Partner tests stay *pending*. **Download .md** gives the report file.
9. **Release campaign to lab.** The tentative bookings become real on the Gantt. Say: "That's the loop: plan from the standard, check it, book robots and rigs, report. Next step is the physical bench."

The second demo request (*QD to UL 4501 only, incomplete*) shows intake stopping a job:
- UL 4501 methods are not public, so it can't be planned;
- the maximum operating pressure is missing;
- only one sample is supplied.

## Architecture

```
app/        FastAPI (REST, /ws event stream, /api/jobs/{id}/report.md), single-page UI (plain JS, SVG Gantt)
agents/     core.py          tool runtime, LiveRunner (Anthropic Messages API, streaming, manual tool loop),
                             ScriptedSession (scripted choices, same tool executor)
            intake.py, planner.py, verification.py, procedure.py, scheduling.py, report.py
                             one module per agent: system prompt, tools, task builder, scripted policy
            orchestrator.py  pipeline, planner <-> verification rework loop (max 3), release gate
testlab/    standards.py     requirement catalogues (OCP cold plate summary; UL 4501 marked not plannable)
            methods.py       test methods, resources (bench, hired, university CMM, partner), durations
            spec_check.py    intake validation and derived test conditions
            campaign.py      campaign builder: steps, sample sequences, acceptance criteria
            verify.py        coverage, parameter and sequence-rule checks
            procedure.py     rig operations, cobot tasks, cost at planning rates
            report.py        traceability, simulated dry run, Markdown report
factory/    db.py            SQLite: jobs, event log, lab resources, bookings (re-seeded relative to today on start)
            scheduler.py     finite-capacity lab scheduler: rigs 24/7, cobot handling in a supervised window,
                             sample sequences, partner transit, university CMM hours
engineering/                 cold plate thermal/hydraulic models from the master branch (kept, still tested)
tests/                       108 tests
```

## Where the numbers come from

- **The OCP requirement catalogue** is a planning summary from the research notes (`research/notes/cold_plate_bottlenecks_qualification_capital.md`) and the published PDF. It is not the specification text. Every value must be checked against the specification before a real campaign. The helium leak-rate exponent could not be recovered from the PDF, so that limit comes from the customer.
- **UL 4501 test methods are not public.** The catalogue marks it as not plannable.
- **Burst** is report-only. The research summary reads "rupture or 3x minimum proof pressure", which has not been checked against the specification text, so the demo reports the pressure reached rather than a pass/fail. SEQ-2 (destructive test last) and SEQ-3 (samples used) are Loopwerks lab rules, not specification rules, and are labelled as such.
- **Durations** are planning estimates for the v0 bench. Fluid compatibility is set at 21 days because the ASTM methods run for days to weeks.
- **Cost rates** (bench £12/h, hired helium detector £20/h, cobot £15/h, CMM £60/h, engineer £40/h) are planning assumptions, not quotes.
- **Simulated results** use fixed offsets from the maker's claims: pressure drop +4 %, and thermal resistance +12 %, which is chosen to show a flagged failure.

## Tests

```
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m scripts.run_pipeline          # headless scripted run of the CP-1400 case
.venv\Scripts\python -m scripts.run_pipeline bad      # the request intake stops
```

The tests cover:
- intake rules;
- the planner's first draft failing for exactly the three intended reasons, and the revision clearing them;
- every verification rule;
- procedure invariants;
- scheduler invariants: no overlaps, sample order, cobot handling inside the supervised window, CMM hours, partner transit, and wall-clock robustness over two weeks of start times;
- the live tool loop against a fake client;
- the full pipeline to the gate.

## Not yet done

- **The live (Claude) path has never run against the real API.** It is tested against a fake client only. Before the call, put a key in `.env` and do one full live run. Live agents plan their own campaigns, so a rejection is likely but not guaranteed. Scripted mode always shows it.
- Physical rigs, the cobot integration and partner contracts do not exist yet. The scheduler and the report are built so that real rig data can replace the mock layer.
