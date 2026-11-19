/* Cold Plate Agent Factory - single-page UI. Renders the event stream; all numbers come from tool outputs. */
(function () {
  const { esc } = window.Charts;
  const $ = s => document.querySelector(s);

  const AGENTS = {
    intake: { n: "Intake", i: "IN", c: "#3987e5" },
    thermal_design: { n: "Thermal Design", i: "TD", c: "#d95926" },
    verification: { n: "Verification", i: "VE", c: "#199e70" },
    process_planning: { n: "Process Planning", i: "PP", c: "#c98500" },
    scheduling: { n: "Scheduling", i: "SC", c: "#d55181" },
    qa: { n: "QA", i: "QA", c: "#9085e9" },
    engineer: { n: "Engineer", i: "EN", c: "#6b6a63" },
  };
  const ORDER = ["intake", "thermal_design", "verification", "process_planning", "scheduling", "qa", "engineer"];
  const TABS = [["spec", "Spec"], ["design", "Design"], ["verification", "Verification"], ["process", "Process"],
    ["schedule", "Schedule"], ["qa", "QA plan"], ["package", "Job package"]];
  const ART_TAB = { spec_check: "spec", design_space: "design", design_selection: "design", verification: "verification",
    process_plan: "process", schedule: "schedule", qa_plan: "qa", job_package: "package" };

  const SPEC_FIELDS = [
    ["customer", "Customer", "text", true], ["part_name", "Part", "text", true],
    ["tdp_w", "TDP (W)", "number"], ["max_case_temp_c", "Max case temp (°C)", "number"],
    ["heat_source_length_mm", "Heat source L (mm)", "number"], ["heat_source_width_mm", "Heat source W (mm)", "number"],
    ["coolant", "Coolant", "select:PG25,water"], ["inlet_temp_c", "Inlet temp (°C)", "number"],
    ["flow_rate_lpm", "Flow rate (L/min)", "number"], ["max_pressure_drop_kpa", "Max ΔP (kPa)", "number"],
    ["quantity", "Quantity", "number"], ["deadline", "Deadline", "date"],
    ["tim_resistance_cm2k_w", "TIM2 (cm²·K/W)", "number"], ["max_operating_pressure_bar", "Max op. pressure (bar)", "number"],
    ["notes", "Customer notes", "textarea", true],
  ];

  let S = fresh(null);
  let CONFIG = null;
  let userTabAt = 0;

  function fresh(jobId) {
    return { jobId, status: "idle", nodes: {}, loops: 0, art: {}, verifs: [], cur: null, tools: {}, lastId: 0,
      tab: "spec", committed: false, decision: null, mode: null };
  }

  /* ---------------- formatting ---------------- */
  function fmtText(s) {
    return esc(s || "")
      .replace(/degC/g, "°C").replace(/\bdP\b/g, "ΔP").replace(/cm2K\/W/g, "cm²·K/W").replace(/m2K\/W/g, "m²K/W")
      .replace(/W\/cm2/g, "W/cm²").replace(/mbar\.L\/s/g, "mbar·L/s");
  }
  const f = (v, d = 1) => (v === undefined || v === null || isNaN(v)) ? "–" : Number(v).toFixed(d);
  const money = v => "$" + Number(v).toLocaleString(undefined, { maximumFractionDigits: v < 1000 ? 2 : 0 });
  const day = s => s ? new Date(s.length <= 10 ? s + "T12:00:00" : s).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" }) : "–";
  const dt = s => s ? new Date(s).toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "–";
  const clock = ts => ts ? new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "";
  const pretty = k => k.replace(/_mm$/, " (mm)").replace(/_c$/, " (°C)").replace(/_kpa$/, " (kPa)").replace(/_/g, " ");

  /* ---------------- pipeline ---------------- */
  function renderPipeline() {
    const p = $("#pipeline");
    p.innerHTML = ORDER.map((k, i) => {
      const a = AGENTS[k], st = S.nodes[k] || {};
      const label = st.label || (k === "engineer" ? "approval gate" : "idle");
      return `<div class="node ${st.state || ""}" data-k="${k}">
        <div class="av" style="background:${a.c}">${a.i}</div><div class="nm">${a.n}</div><div class="st">${esc(label)}</div>
        ${i < ORDER.length - 1 ? `<span class="arrow ${st.state === "done" ? "lit" : ""}"></span>` : ""}</div>`;
    }).join("") + `<svg class="loop ${S.loops ? "hot" : ""}" viewBox="0 0 200 22" preserveAspectRatio="none">
        <path d="M190 2 C190 20, 10 20, 10 2" vector-effect="non-scaling-stroke"/></svg>`;
    if (S.loops) {
      const t = document.createElement("div");
      t.style.cssText = "position:absolute;bottom:-2px;left:calc(100%/7*2);transform:translateX(-50%);font:600 10px var(--mono);color:var(--serious);background:var(--surface);padding:0 4px";
      t.textContent = `↺ ${S.loops} rejection${S.loops > 1 ? "s" : ""}`;
      p.appendChild(t);
    }
  }
  function setNode(k, state, label) { S.nodes[k] = { state, label }; renderPipeline(); }

  function renderKpis() {
    const sel = S.art.design_selection, v = S.verifs[S.verifs.length - 1], sch = S.art.schedule, pp = S.art.process_plan, ds = S.art.design_space;
    const spec = S.art.spec_check && S.art.spec_check.normalized_spec;
    const k = [];
    if (sel) {
      const r = sel.selected_full;
      k.push(["Case temp · " + sel.selected, f(r.thermal.t_case_c) + " °C", `limit ${spec ? spec.max_case_temp_c : "–"} °C` + (v && v.design_id === sel.selected ? ` · worst ${f(v.worst_case.t_case_c)}` : "")]);
      k.push(["Pressure drop", f(r.hydraulics.dp_kpa) + " kPa", `limit ${spec ? spec.max_pressure_drop_kpa : "–"} kPa`]);
    } else { k.push(["Case temp", "–", ""], ["Pressure drop", "–", ""]); }
    k.push(["Design space", ds ? `${ds.candidates.length + ds.points.length}` : "–", ds ? `${ds.candidates.length} evaluated · ${ds.points.length} swept` : "variants"]);
    k.push(["Delivery", sch ? day(sch.delivery_date) : "–", sch ? `${sch.slack_days >= 0 ? "+" : ""}${sch.slack_days} d vs deadline` : ""]);
    k.push(["Unit cost", pp ? money(pp.cost_per_part_usd.total) : "–", pp ? `${f(pp.cycle_time_min_per_part, 0)} min/part` : ""]);
    $("#kpis").innerHTML = k.map(([a, b, c]) => `<div class="kpi"><div class="k">${esc(a)}</div><div class="v">${esc(b)}</div><div class="s">${esc(c)}</div></div>`).join("");
  }

  function setStatus(st) {
    S.status = st;
    const el = $("#job-status"); el.className = "status-pill " + st; el.textContent = st.replace(/_/g, " ");
    if (st === "awaiting_approval") showGate(); else if (st !== "released") $("#gate").classList.add("hidden");
    document.body.classList.toggle("gated", st === "awaiting_approval");
    if (S.tab === "package" && S.art.job_package) renderTab();
  }

  /* ---------------- feed ---------------- */
  const feed = () => $("#feed");
  function scroll() { if ($("#autoscroll").checked) feed().scrollTop = feed().scrollHeight; }
  function entry(agent, ts) {
    const a = AGENTS[agent] || { n: agent, i: "?", c: "#555" };
    const e = document.createElement("div"); e.className = "entry";
    e.innerHTML = `<div class="av" style="background:${a.c}">${a.i}</div><div><div class="who">${a.n} Agent<time>${clock(ts)}</time></div><div class="body"></div></div>`;
    feed().appendChild(e);
    S.cur = { agent, el: e, body: e.querySelector(".body"), typing: null, thinking: null };
    return S.cur;
  }
  function curFor(agent, ts) { return (S.cur && S.cur.agent === agent) ? S.cur : entry(agent, ts); }
  function sys(cls, html) {
    const d = document.createElement("div"); d.className = "sys " + cls; d.innerHTML = html; feed().appendChild(d);
    S.cur = null; scroll();
  }

  function toolSummary(tool, o) {
    if (o.error) return o.error.slice(0, 90);
    switch (tool) {
      case "check_spec": return `${o.accepted ? "feasible" : "blocking errors"} · ${o.issues.length} notes`;
      case "evaluate_design": return `${o.design_id} · ${f(o.t_case_c)} °C · ${f(o.dp_kpa)} kPa · ${o.meets_nominal_limits ? "meets nominal" : "misses spec"}`;
      case "parametric_sweep": return `${o.evaluated} variants · ${o.meeting_constraints} meet constraints`;
      case "verify_design": return `${o.verdict} ${o.checks.filter(c => c.pass).length}/${o.checks.length} checks`;
      case "plan_process": return `${o.operations.length} ops · ${f(o.cycle_time_min_per_part, 0)} min/part · ${money(o.cost_per_part_usd.total)}/part`;
      case "get_factory_state": return `${o.machines.length} machines · ${Object.values(o.bookings).flat().length} bookings`;
      case "schedule_job": return `${o.option_id} · delivery ${o.delivery_date} · ${o.slack_days >= 0 ? "+" : ""}${o.slack_days} d`;
      case "generate_qa_requirements": return `proof ${o.leak_test.proof_pressure_bar} bar · decay hold ${o.leak_test.decay_hold_s} s`;
      default: return tool.startsWith("submit") ? "submitted" : "done";
    }
  }
  function inputSummary(inp) {
    const s = JSON.stringify(inp); return s === "{}" ? "" : s.slice(1, -1).replace(/"/g, "").slice(0, 140);
  }

  function apply(ev, live) {
    const p = ev.payload || {}, a = ev.agent;
    if (ev.id) S.lastId = Math.max(S.lastId, ev.id);
    switch (ev.type) {
      case "job_started":
        S.mode = p.mode;
        sys("handoff", `<b>Job ${esc(ev.job_id)}</b> received · ${p.mode === "live" ? "live agents · " + esc(p.model) : "scripted replay (deterministic policies, same tools)"}`);
        setStatus("running"); break;
      case "agent_started":
        setNode(a, "active", "working…"); S.cur = null; break;
      case "agent_delta": {
        const c = curFor(a, ev.ts);
        if (!c.typing) { c.typing = document.createElement("div"); c.typing.className = "msg typing"; c.body.appendChild(c.typing); c.raw = ""; }
        c.raw += p.text; c.typing.innerHTML = fmtText(c.raw); scroll(); break;
      }
      case "thinking_delta": {
        const c = curFor(a, ev.ts);
        if (!c.thinking) { c.thinking = document.createElement("div"); c.thinking.className = "thinking"; c.body.appendChild(c.thinking); c.traw = ""; }
        c.traw += p.text; c.thinking.innerHTML = fmtText(c.traw); scroll(); break;
      }
      case "agent_thinking": {
        const c = curFor(a, ev.ts);
        if (!c.thinking) { c.thinking = document.createElement("div"); c.thinking.className = "thinking"; c.body.appendChild(c.thinking); }
        c.thinking.innerHTML = fmtText(p.text); scroll(); break;
      }
      case "agent_message": {
        const c = curFor(a, ev.ts);
        if (!c.typing) { c.typing = document.createElement("div"); c.body.appendChild(c.typing); }
        c.typing.className = "msg"; c.typing.innerHTML = fmtText(p.text);
        c.typing = null; c.thinking = null; scroll(); break;
      }
      case "tool_call": {
        const c = curFor(a, ev.ts);
        c.typing = null;
        const d = document.createElement("details"); d.className = "tool";
        d.innerHTML = `<summary><span class="tn">${esc(p.tool)}</span><span class="ti">${esc(inputSummary(p.input))}</span><span class="tr pending">running</span></summary><pre>${esc(JSON.stringify(p.input, null, 1))}</pre>`;
        d._input = p.input; c.body.appendChild(d); S.tools[p.call_id] = d; scroll(); break;
      }
      case "tool_result": {
        const d = S.tools[p.call_id]; if (!d) break;
        const tr = d.querySelector(".tr"); tr.className = "tr " + (p.is_error ? "err" : "ok"); tr.textContent = toolSummary(p.tool, p.output);
        d.querySelector("pre").textContent = "input:\n" + JSON.stringify(d._input, null, 1).slice(0, 4000)
          + "\n\noutput:\n" + JSON.stringify(p.output, null, 1).slice(0, 12000);
        break;
      }
      case "agent_finished": {
        if (a === "verification") {
          const ok = p.output && p.output.verdict === "approve";
          setNode(a, ok ? "done" : "rejected", ok ? "approved" : "rejected");
        } else setNode(a, "done", "done ✓");
        break;
      }
      case "handoff":
        sys("handoff", `<b>${AGENTS[p.from].n} → ${AGENTS[p.to].n}</b> · ${fmtText(p.note)}`); break;
      case "rejection":
        S.loops += 1; setNode("thermal_design", "rejected", "rework #" + S.loops); renderPipeline();
        sys("reject", `<b>↺ Verification rejected ${esc(p.design_id)}, back to Thermal Design (round ${p.round})</b><ul class="plain">`
          + p.required_changes.map(c => `<li>${fmtText(c)}</li>`).join("") + "</ul>");
        break;
      case "artifact": onArtifact(p.kind, p.data, live); break;
      case "gate":
        setNode("engineer", "waiting", "awaiting you");
        sys("gate", `<b>All agents done. Job package ready for engineer approval.</b> Factory bookings are held as tentative.`);
        setStatus("awaiting_approval"); break;
      case "approved":
        S.committed = true; S.decision = p; setNode("engineer", "done", "approved ✓");
        sys("ok", `<b>Approved by ${esc(p.engineer)}</b>. ${p.bookings_committed} operations booked on the cell${p.comment ? " · “" + esc(p.comment) + "”" : ""}`);
        setStatus("released"); refreshFactory(); break;
      case "returned":
        S.decision = p; setNode("engineer", "rejected", "returned");
        sys("reject", `<b>Returned by ${esc(p.engineer)}</b>${p.comment ? ": " + esc(p.comment) : ""}. Tentative bookings released.`);
        setStatus("returned"); break;
      case "job_status":
        sys(p.status === "needs_clarification" ? "reject" : "err", `<b>${esc(p.status.replace(/_/g, " "))}</b> · ${esc(p.message)}`);
        if (p.status === "needs_clarification") setNode("intake", "rejected", "needs info");
        setStatus(p.status); break;
      case "error":
        sys("err", `<b>Pipeline error:</b> ${esc(p.message)}`); setStatus("error"); break;
    }
  }

  /* ---------------- artifacts & tabs ---------------- */
  function onArtifact(kind, data, live) {
    if (kind === "verification") S.verifs.push(data);
    S.art[kind] = data;
    const tab = ART_TAB[kind];
    if (tab) {
      S.fresh = S.fresh || {}; if (live) S.fresh[tab] = true;
      if (live && Date.now() - userTabAt > 15000) S.tab = tab;
    }
    renderKpis(); renderTabs();
    if (!live) return;
    renderTab();
  }
  function renderTabs() {
    $("#tabs").innerHTML = TABS.map(([k, n]) => {
      const has = Object.entries(ART_TAB).some(([ak, t]) => t === k && S.art[ak]);
      return `<button class="tab ${has ? "has" : ""} ${S.tab === k ? "active" : ""}" data-t="${k}" role="tab">${n}${S.fresh && S.fresh[k] && S.tab !== k ? '<span class="n"></span>' : ""}</button>`;
    }).join("");
  }
  function renderTab() {
    if (S.fresh) S.fresh[S.tab] = false;
    renderTabs();
    const b = $("#tab-body");
    const fn = { spec: tabSpec, design: tabDesign, verification: tabVerif, process: tabProcess, schedule: tabSchedule, qa: tabQA, package: tabPackage }[S.tab];
    if (S.renderedTab !== S.tab) b.scrollTop = 0;
    S.renderedTab = S.tab;
    b.innerHTML = ""; fn(b);
  }
  const emptyMsg = (b, m) => { b.innerHTML = `<div class="empty">${m}</div>`; };
  const card = (k, v, s = "") => `<div class="card"><div class="k">${esc(k)}</div><div class="v">${v}</div><div class="s">${s}</div></div>`;
  const sev = s => ({ error: "fail", warning: "warn", info: "info" }[s] || "info");

  function tabSpec(b) {
    const a = S.art.spec_check; if (!a) return emptyMsg(b, "The Intake Agent will validate the customer spec here.");
    const d = a.derived || {}, s = a.normalized_spec;
    let h = `<div class="round-h"><span>Intake decision</span><span class="${a.decision === "accept" ? "pass" : "fail"}">${a.decision === "accept" ? "Accepted" : "Needs clarification"}</span></div>
      <div class="note">${fmtText(a.summary)}</div>`;
    if (d.heat_flux_w_cm2 !== undefined) h += `<h3>Thermal budget (deterministic)</h3><div class="cards">
      ${card("Heat flux", f(d.heat_flux_w_cm2) + " W/cm²")}${card("Coolant rise", f(d.coolant_temp_rise_c) + " °C", "inlet → outlet")}
      ${card("Case-temp floor", f(d.case_temp_floor_c) + " °C", "coolant + TIM alone")}${card("Left for the plate", f(d.budget_left_for_plate_c) + " °C")}
      ${card("Required R", f(d.required_r_case_to_inlet_k_w, 4) + " K/W", "case → inlet")}</div>`;
    h += `<h3>Checks</h3><table class="dt"><tr><th>Field</th><th>Finding</th><th></th></tr>` + (a.issues.length ? a.issues.map(i =>
      `<tr><td class="mono">${esc(i.field)}</td><td>${fmtText(i.message)}</td><td class="${sev(i.severity)}">${i.severity}</td></tr>`).join("") : `<tr><td colspan=3 class="pass">No issues</td></tr>`) + "</table>";
    if (a.customer_questions && a.customer_questions.length) h += `<h3>Questions for the customer</h3><ul class="plain">${a.customer_questions.map(q => `<li>${fmtText(q)}</li>`).join("")}</ul>`;
    h += `<h3>Normalized spec</h3><div class="params">${Object.entries(s).filter(([k]) => k !== "notes").map(([k, v]) => `<div><span>${esc(pretty(k))}</span><span>${esc(v)}</span></div>`).join("")}</div>`;
    if (s.notes) h += `<div class="note">${esc(s.notes)}</div>`;
    b.innerHTML = h;
  }

  function tabDesign(b) {
    const ds = S.art.design_space, sel = S.art.design_selection;
    if (!ds) return emptyMsg(b, "The Thermal Design Agent's candidates and design-space sweeps will appear here.");
    const rejected = S.verifs.filter(v => v.verdict !== "PASS").map(v => v.design_id);
    const selected = sel ? sel.selected : null;
    b.innerHTML = `<h3 style="margin-top:0">Design space explored · case temperature vs pressure drop</h3>
      <div class="legend"><span><i style="background:#3987e5"></i>Sweep variant meeting constraints</span><span><i style="background:#5f5e58"></i>Sweep variant outside constraints</span>
      <span><i class="ring"></i>Evaluated design</span><span><i class="ring" style="border-color:#ec835a"></i>Rejected by verification</span><span><i style="background:rgba(57,135,229,.25)"></i>Spec window</span></div>
      <div id="scatter"></div><h3>Candidates</h3><div id="cand"></div><div id="seldetail"></div>`;
    Charts.designSpace($("#scatter"), { points: ds.points, candidates: ds.candidates, selected, rejected, tMax: ds.t_max, dpMax: ds.dp_max });
    $("#cand").innerHTML = `<table class="dt"><tr><th>ID</th><th>Design</th><th class="num">Case °C</th><th class="num">Margin</th><th class="num">ΔP kPa</th><th class="num">Re</th><th>Status</th></tr>`
      + ds.candidates.map(c => {
        const st = c.design_id === selected ? '<span class="pass">selected</span>' : rejected.includes(c.design_id) ? '<span class="fail">rejected</span>'
          : c.meets_nominal_limits ? '<span class="info">meets nominal</span>' : `<span class="fail">${c.thermal_margin_c < 0 ? "too hot" : "ΔP over"}</span>`;
        return `<tr class="${c.design_id === selected ? "sel" : ""}"><td class="mono">${c.design_id}</td><td>${esc(c.label)}</td><td class="num">${f(c.t_case_c)}</td>
          <td class="num">${c.thermal_margin_c >= 0 ? "+" : ""}${f(c.thermal_margin_c)}</td><td class="num">${f(c.dp_kpa, 2)}</td><td class="num">${Math.round(c.reynolds)}</td><td>${st}</td></tr>`;
      }).join("") + "</table>";
    if (!sel) return;
    const r = sel.selected_full, g = r.geometry, h = r.hydraulics, ht = r.heat_transfer;
    const v = S.verifs.filter(x => x.design_id === selected).pop();
    const params = Object.entries(r.design).map(([k, val]) => `<div><span>${esc(pretty(k))}</span><span>${esc(val)}</span></div>`).join("");
    const derived = [["channel count", g.channel_count], ["pin count", g.pin_count], ["pitch (mm)", g.pitch_mm && f(g.pitch_mm, 3)],
      ["plate thickness (mm)", g.plate_mm[2]], ["hydraulic diameter (mm)", f(g.hydraulic_diameter_mm, 3)], ["wetted area (cm²)", f(g.wetted_area_cm2, 0)],
      ["area enhancement", f(g.area_enhancement, 1) + "×"], ["mass (kg)", f(r.mass_kg, 3)]].filter(x => x[1] !== undefined && x[1] !== null)
      .map(([k, val]) => `<div><span>${k}</span><span>${val}</span></div>`).join("");
    $("#seldetail").innerHTML = `<h3>Selected design ${selected} · round ${sel.round}</h3><div class="note">${fmtText(sel.rationale)}${sel.response_to_verification ? "\n\nResponse to verification: " + fmtText(sel.response_to_verification) : ""}</div>
      <h3>Temperature stack, inlet → case</h3><div id="stack"></div>
      <div class="cards">${card("Flow", `${h.regime}`, `Re ${Math.round(h.reynolds)} · ${f(h.velocity_m_s, 2)} m/s`)}${card("h (wall)", f(ht.h_w_m2k, 0) + " W/m²K", `Nu ${f(ht.nusselt, 2)}`)}
        ${card("Fin efficiency", f(ht.fin_efficiency * 100, 0) + "%", `h_eff ${f(ht.h_eff_footprint_w_m2k / 1000, 1)} kW/m²K on footprint`)}${card("R case→inlet", f(r.thermal.r_case_to_inlet_k_w, 4) + " K/W", `outlet ${f(r.thermal.t_outlet_c)} °C`)}</div>
      <h3>Pressure drop breakdown</h3><table class="dt">${Object.entries(h.dp_breakdown_kpa).map(([k, val]) => `<tr><td>${esc(k.replace(/_/g, " "))}</td><td class="num">${f(val, 2)} kPa</td></tr>`).join("")}
        <tr><td><b>Total</b></td><td class="num"><b>${f(h.dp_kpa, 2)} kPa</b></td></tr></table>
      <h3>Parameter set for CAD (Autodesk Inventor) <button class="btn small ghost" id="copy-params" type="button">Copy JSON</button></h3>
      <div class="params">${params}</div><h3>Derived geometry</h3><div class="params">${derived}</div>`;
    const spec = S.art.spec_check.normalized_spec;
    Charts.thermalStack($("#stack"), { inlet: spec.inlet_temp_c, dt: r.thermal.dt_breakdown_c, tMax: spec.max_case_temp_c, worst: v ? v.worst_case.t_case_c : null });
    $("#copy-params").onclick = () => { navigator.clipboard.writeText(JSON.stringify(r.design, null, 2)); $("#copy-params").textContent = "Copied"; };
  }

  function tabVerif(b) {
    if (!S.verifs.length) return emptyMsg(b, "The Verification Agent's independent checks will appear here.");
    b.innerHTML = `<div class="note">Standard: ${fmtText(S.verifs[0].standard)}. The verifier re-runs every model from the parameter set and does not use the design agent's numbers.</div>`
      + S.verifs.slice().reverse().map(v => `<div class="round ${v.verdict === "PASS" ? "" : "failed"}">
      <div class="round-h"><span>Round ${v.round} · ${esc(v.design_id)}</span><span class="${v.verdict === "PASS" ? "pass" : "fail"}">${v.verdict === "PASS" ? "Approved" : "Rejected"}</span></div>
      <div class="cards">${card("Nominal", `${f(v.nominal.t_case_c)} °C`, `${f(v.nominal.dp_kpa, 2)} kPa`)}${card("Worst case", `${f(v.worst_case.t_case_c)} °C`, `${f(v.worst_case.dp_kpa, 2)} kPa · ${f(v.worst_case.velocity_m_s, 2)} m/s`)}</div>
      <table class="dt" style="margin-top:6px"><tr><th>Check</th><th class="num">Value</th><th class="num">Limit</th><th></th></tr>${v.checks.map(c =>
        `<tr class="${c.pass ? "" : "bad"}"><td>${fmtText(c.check)}${c.detail && !c.pass ? `<div style="color:var(--muted);font-size:11px">${fmtText(c.detail)}</div>` : ""}</td><td class="num">${c.value} ${fmtText(c.unit)}</td><td class="num">${c.limit}</td><td class="${c.pass ? "pass" : "fail"}">${c.pass ? "pass" : "fail"}</td></tr>`).join("")}</table>
      ${v.required_changes && v.required_changes.length ? `<h3>Required changes</h3><ul class="plain">${v.required_changes.map(c => `<li>${fmtText(c)}</li>`).join("")}</ul>` : ""}</div>`).join("");
  }

  function tabProcess(b) {
    const a = S.art.process_plan; if (!a) return emptyMsg(b, "The Process Planning Agent's routing will appear here.");
    const c = a.cost_per_part_usd, st = a.minutes_per_part_by_station;
    b.innerHTML = `<div class="cards">${card("Cycle time", f(a.cycle_time_min_per_part, 0) + " min", Object.entries(st).map(([k, v]) => `${k} ${f(v, 0)}`).join(" · "))}
      ${card("Cost / part", money(c.total), `material ${money(c.material)} · machine ${money(c.machine_and_labour)}`)}${card("Batch", money(a.batch_cost_usd), `${a.quantity} pcs`)}
      ${card("Stock", a.stock.base_blank_mm.join(" × ") + " mm", `+ lid ${a.stock.lid_blank_mm.join(" × ")} · ${esc(a.stock.material)}`)}</div>
      <h3>Routing</h3><table class="dt"><tr><th>Op</th><th>Station</th><th>Operation / tooling</th><th class="num">min/part</th></tr>${a.operations.map(o =>
        `<tr><td class="mono">${o.seq}</td><td class="mono">${o.station}</td><td>${esc(o.operation)}<div style="color:var(--muted);font-size:11px">${esc(o.tools.join(" · "))}${o.notes ? " · " + esc(o.notes) : ""}</div></td><td class="num">${f(o.minutes, 1)}</td></tr>`).join("")}</table>
      ${a.review ? `<h3>Agent review</h3><div class="note">${fmtText(a.review.summary)}\nBottleneck: ${fmtText(a.review.bottleneck)}</div><h3>Risks &amp; controls</h3><ul class="plain">${a.review.risks_and_controls.map(r => `<li>${fmtText(r)}</li>`).join("")}</ul>` : ""}`;
  }

  function tabSchedule(b) {
    const a = S.art.schedule; if (!a) return emptyMsg(b, "The Scheduling Agent's booking on the factory cell will appear here.");
    b.innerHTML = `<div class="cards">${card("Release to cell", dt(a.release))}${card("Production complete", dt(a.production_complete))}
      ${card("Delivery", day(a.delivery_date), `ships ${day(a.ship_date)}`)}${card("vs deadline", `<span class="${a.on_time ? "pass" : "fail"}">${a.slack_days >= 0 ? "+" : ""}${a.slack_days} days</span>`, `deadline ${day(a.deadline)}`)}
      ${card("Lots", `${a.lots} × ${a.lot_size}`, a.allow_saturday_overtime ? "Saturday overtime" : "standard shifts")}</div>
      <h3>Cell schedule ${S.committed ? "(booked)" : "(tentative hold until approval)"}</h3><div id="gantt"></div>
      <div class="note">${fmtText(a.summary)}</div>`;
    Charts.gantt($("#gantt"), { machines: a.machines, bookings: S.board || a.board, jobId: S.jobId, deadline: a.deadline, delivery: a.delivery_date, committed: S.committed });
  }

  function tabQA(b) {
    const a = S.art.qa_plan; if (!a) return emptyMsg(b, "The QA Agent's inspection and test plan will appear here.");
    const l = a.leak_test, fl = a.flow_test, th = a.thermal_test;
    b.innerHTML = `<div class="cards">${card("Proof test", `${l.proof_pressure_bar} bar`, `${l.proof_hold_s} s hold · ${esc(l.test_medium)}`)}
      ${card("Leak (pressure decay)", `${l.decay_test_pressure_bar} bar · ${l.decay_hold_s} s`, `≤ ${l.max_pressure_decay_mbar} mbar decay · ${l.sampling}`)}
      ${card("Flow / ΔP", `${fl.predicted_dp_kpa} kPa`, fmtText(fl.acceptance))}${card("Thermal (TTV)", `${th.power_w} W`, fmtText(th.acceptance))}
      ${card("Internal volume", `${a.internal_volume_ml} ml`, `lot sample ${a.lot_sample_size}`)}</div>
      <h3>Dimensional &amp; visual inspection</h3><table class="dt"><tr><th>Characteristic</th><th>Spec</th><th>Method</th><th>Sampling</th></tr>${a.dimensional.map(d =>
        `<tr><td>${d.critical ? '<b style="color:var(--warning)">◆</b> ' : ""}${esc(d.feature)}</td><td class="mono">${esc(d.spec)}</td><td>${esc(d.method)}</td><td>${esc(d.sampling)}</td></tr>`).join("")}</table>
      <div style="font-size:11px;color:var(--muted);margin-top:4px">◆ critical to function</div>
      ${a.review ? `<h3>Agent notes</h3><div class="note">${fmtText(a.review.summary)}</div><ul class="plain">${a.review.notes.map(n => `<li>${fmtText(n)}</li>`).join("")}</ul>` : ""}`;
  }

  function tabPackage(b) {
    const p = S.art.job_package; if (!p) return emptyMsg(b, "The complete job package for engineer sign-off will appear here.");
    const dp = p.design_params;
    b.innerHTML = `<div class="round-h"><span>${esc(p.job_id)} · ${esc(p.customer)} · ${esc(p.part_name)}</span><span class="status-pill ${S.status}">${S.status.replace(/_/g, " ")}</span></div>
      <div class="cards">${card("Design", `${esc(p.design_id)}`, esc(p.label))}${card("Case temp", f(p.t_case_c) + " °C", `worst ${f(p.worst_case.t_case_c)} · limit ${p.limits.max_case_c}`)}
      ${card("Pressure drop", f(p.dp_kpa, 2) + " kPa", `worst ${f(p.worst_case.dp_kpa, 2)} · limit ${p.limits.max_dp_kpa}`)}${card("R case→inlet", f(p.r_case_to_inlet_k_w, 4) + " K/W")}
      ${card("Unit / batch cost", money(p.cost_per_part_usd), `${money(p.batch_cost_usd)} for ${p.quantity}`)}${card("Delivery", day(p.delivery_date), `${p.slack_days >= 0 ? "+" : ""}${p.slack_days} d vs ${day(p.deadline)}`)}
      ${card("Design effort", `${p.designs_evaluated + p.sweep_variants} variants`, `${p.verification_rounds} verification round(s)`)}${card("Cycle time", f(p.cycle_time_min, 0) + " min/part")}</div>
      <h3>Released parameter set → CAD (Inventor)</h3><div class="params">${Object.entries(dp).map(([k, v]) => `<div><span>${esc(pretty(k))}</span><span>${esc(v)}</span></div>`).join("")}</div>
      ${S.decision ? `<div class="note">Engineer decision: ${esc(S.decision.engineer)}${S.decision.comment ? " · " + esc(S.decision.comment) : ""}</div>` : ""}`;
  }

  /* ---------------- gate ---------------- */
  function showGate() {
    const p = S.art.job_package; if (!p) return;
    $("#gate").classList.remove("hidden", "done");
    $("#gate-summary").innerHTML = `${esc(p.design_id)} · ${esc(p.label)} · ${f(p.t_case_c)} °C (worst ${f(p.worst_case.t_case_c)}) / ${f(p.dp_kpa, 1)} kPa · `
      + `${money(p.cost_per_part_usd)}/part · delivery ${day(p.delivery_date)} (${p.slack_days >= 0 ? "+" : ""}${p.slack_days} d) · ${p.verification_rounds} verification rounds`;
    $("#btn-approve").disabled = false; $("#btn-return").disabled = false;
  }
  async function decide(kind) {
    $("#btn-approve").disabled = true; $("#btn-return").disabled = true;
    const r = await fetch(`/api/jobs/${S.jobId}/${kind}`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engineer: "Lead engineer", comment: $("#gate-comment").value }) });
    if (!r.ok) { alertBox((await r.json()).detail); return; }
    if (kind === "approve") {
      $("#gate").classList.add("done"); $(".gate-title").innerHTML = "✓ Released to the factory cell";
      setTimeout(() => { $("#gate").classList.add("hidden"); $(".gate-title").innerHTML = '<span class="dot pulse"></span> Engineer approval required'; }, 2500);
    } else $("#gate").classList.add("hidden");
    loadJobs();
  }
  function alertBox(msg) { sys("err", esc(msg)); }

  async function refreshFactory() {
    const r = await (await fetch("/api/factory")).json();
    S.board = r.bookings; if (S.tab === "schedule") renderTab();
  }

  /* ---------------- jobs ---------------- */
  async function loadJobs() {
    const jobs = await (await fetch("/api/jobs")).json();
    $("#job-list").innerHTML = jobs.map(j => `<li data-id="${j.id}" class="${j.id === S.jobId ? "active" : ""}"><span class="jid">${j.id}</span>
      <span class="status-pill ${j.status}">${j.status.replace(/_/g, " ")}</span><span class="jt">${esc(j.title || "")} · ${j.mode} · ${new Date(j.created_at).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span></li>`).join("")
      || `<li class="jt">No jobs yet. Submit a request.</li>`;
    return jobs;
  }
  async function openJob(id) {
    S = fresh(id);
    feed().innerHTML = ""; renderPipeline(); renderKpis();
    const j = await (await fetch(`/api/jobs/${id}`)).json();
    if (S.jobId !== id) return;  // another job was opened/submitted while this one loaded
    $("#job-title").textContent = `${j.id} · ${j.title || ""}`;
    j.events.forEach(ev => apply(ev, false));
    setStatus(j.status);
    if (j.status === "released") { S.committed = true; await refreshFactory(); if (S.jobId !== id) return; }
    const lastArt = [...j.events].reverse().find(e => e.type === "artifact");
    if (lastArt) S.tab = ART_TAB[lastArt.payload.kind] || "spec";
    renderTab(); renderPipeline(); feed().scrollTop = feed().scrollHeight;
    loadJobs();
  }

  /* ---------------- form ---------------- */
  function buildForm() {
    $("#spec-form").innerHTML = SPEC_FIELDS.map(([k, label, type, wide]) => {
      let input;
      if (type.startsWith("select:")) input = `<select name="${k}">${type.slice(7).split(",").map(o => `<option>${o}</option>`).join("")}</select>`;
      else if (type === "textarea") input = `<textarea name="${k}" rows="2"></textarea>`;
      else input = `<input name="${k}" type="${type}" ${type === "number" ? 'step="any"' : ""}>`;
      return `<label class="${wide ? "wide" : ""}">${label}${input}</label>`;
    }).join("");
  }
  function fillForm(spec) {
    SPEC_FIELDS.forEach(([k]) => { const e = $(`#spec-form [name="${k}"]`); e.value = spec[k] === undefined ? "" : spec[k]; });
  }
  function readForm() {
    const out = {};
    SPEC_FIELDS.forEach(([k, , type]) => {
      const v = $(`#spec-form [name="${k}"]`).value.trim();
      if (v === "") return;
      out[k] = type === "number" ? Number(v) : v;
    });
    return out;
  }
  async function submit() {
    const btn = $("#submit-btn"); btn.disabled = true;
    try {
      const r = await fetch("/api/jobs", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spec: readForm(), mode: $("#mode-select").value || null }) });
      const j = await r.json();
      if (!r.ok) { alert(j.detail); return; }
      S = fresh(j.job_id); userTabAt = 0;
      $("#gate").classList.add("hidden"); document.body.classList.remove("gated");
      feed().innerHTML = ""; $("#job-title").textContent = `${j.job_id} · ${readForm().part_name || ""}`;
      renderPipeline(); renderKpis(); renderTab(); setStatus("running"); loadJobs();
    } finally { setTimeout(() => { btn.disabled = false; }, 1500); }
  }

  /* ---------------- websocket ---------------- */
  function connect() {
    const ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");
    ws.onmessage = m => {
      const ev = JSON.parse(m.data);
      if (ev.job_id !== S.jobId) { if (ev.type === "gate" || ev.type === "job_started") loadJobs(); return; }
      if (ev.id && ev.id <= S.lastId) return;
      apply(ev, true);
      if (["gate", "error", "job_status"].includes(ev.type)) loadJobs();
    };
    ws.onclose = () => setTimeout(connect, 1500);
  }

  /* ---------------- init ---------------- */
  async function init() {
    CONFIG = await (await fetch("/api/config")).json();
    const b = $("#mode-badge");
    if (CONFIG.mode === "live") { b.textContent = `LIVE · ${CONFIG.model}`; b.classList.add("live"); }
    else { b.textContent = "SCRIPTED REPLAY · real tools, scripted agent choices"; }
    if (!CONFIG.has_key) $('#mode-select option[value="live"]').disabled = true;
    buildForm();
    const ds = $("#demo-select");
    ds.innerHTML = Object.entries(CONFIG.demo_specs).map(([k, v]) => `<option value="${k}">${esc(v.title)}</option>`).join("");
    ds.onchange = () => fillForm(CONFIG.demo_specs[ds.value].spec);
    fillForm(CONFIG.demo_specs[ds.value].spec);
    $("#submit-btn").onclick = submit;
    $("#refresh-jobs").onclick = loadJobs;
    $("#job-list").onclick = e => { const li = e.target.closest("li[data-id]"); if (li) openJob(li.dataset.id); };
    $("#tabs").onclick = e => { const t = e.target.closest(".tab"); if (!t) return; S.tab = t.dataset.t; userTabAt = Date.now(); renderTab(); };
    $("#btn-approve").onclick = () => decide("approve");
    $("#btn-return").onclick = () => decide("reject");
    $("#show-thinking").onchange = e => document.body.classList.toggle("hide-thinking", !e.target.checked);
    setInterval(() => { $("#clock").textContent = new Date().toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }); }, 1000);
    let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(renderTab, 150); });
    renderPipeline(); renderKpis(); renderTab();
    connect();
    const jobs = await loadJobs();
    if (jobs.length) openJob(jobs[0].id);
  }
  init();
})();
