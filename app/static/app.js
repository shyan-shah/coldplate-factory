/* Loopwerks autonomous test lab - single-page UI. Renders the event stream; all numbers come from tool outputs. */
(function () {
  const { esc } = window.Charts;
  const $ = s => document.querySelector(s);

  const AGENTS = {
    intake: { n: "Intake", i: "IN", c: "#5CC6D6" },
    planner: { n: "Campaign Planner", i: "CP", c: "#E59A2E" },
    verification: { n: "Verification", i: "VE", c: "#3FA66B" },
    procedure: { n: "Test Procedure", i: "TP", c: "#8FB8C9" },
    scheduling: { n: "Scheduling", i: "SC", c: "#C98BB9" },
    report: { n: "Report", i: "RP", c: "#9A9CEB" },
    engineer: { n: "Engineer", i: "EN", c: "#8A969D" },
  };
  const ORDER = ["intake", "planner", "verification", "procedure", "scheduling", "report", "engineer"];
  const TABS = [["spec", "Request"], ["campaign", "Campaign"], ["verification", "Verification"], ["procedure", "Procedure"],
    ["schedule", "Schedule"], ["report", "Report"], ["package", "Package"]];
  const ART_TAB = { spec_check: "spec", campaigns: "campaign", campaign_selection: "campaign", verification: "verification",
    procedure: "procedure", schedule: "schedule", report: "report", job_package: "package" };

  const SPEC_FIELDS = [
    ["customer", "Customer", "text", true], ["part_name", "Part", "text", true],
    ["component_type", "Component", "select:cold_plate,quick_disconnect,cdu,manifold"], ["target_standards", "Standard(s)", "text"],
    ["max_operating_pressure_bar", "Max op. pressure (bar)", "number"], ["rated_flow_lpm", "Rated flow (L/min)", "number"],
    ["coolant", "Coolant", "select:PG25,water"], ["design_heat_load_w", "Design heat load (W)", "number"],
    ["port_inner_diameter_mm", "Port ID (mm)", "number"], ["samples", "Samples supplied", "number"],
    ["claimed_r_th_k_w", "Claimed R_th (K/W)", "number"], ["claimed_dp_kpa_at_rated", "Claimed ΔP at rated (kPa)", "number"],
    ["deadline", "Report needed by", "date"],
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
  const money = v => "£" + Number(v).toLocaleString("en-GB", { maximumFractionDigits: 0 });
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
    const sel = S.art.campaign_selection, v = S.verifs[S.verifs.length - 1], sch = S.art.schedule, pr = S.art.procedure, rp = S.art.report;
    const k = [];
    if (sel) {
      const t = sel.campaign.totals;
      k.push(["Coverage · " + sel.selected, `${t.requirements_covered}/${t.requirements_total}`, v ? `checks ${v.checks.filter(c => c.pass).length}/${v.checks.length}` : "requirements"]);
      k.push(["Campaign", `${t.steps} tests`, `${t.samples_used} samples`]);
    } else { k.push(["Coverage", "–", ""], ["Campaign", "–", ""]); }
    k.push(["Rig time", pr ? f(pr.totals.bench_hours) + " h" : "–", pr ? `${pr.totals.cobot_handling_events} cobot handlings` : "bench"]);
    k.push(["Report due", sch ? day(sch.report_due) : "–", sch ? `${sch.slack_days >= 0 ? "+" : ""}${sch.slack_days} d vs deadline` : ""]);
    k.push(["Dry run", rp ? `${rp.counts.PASS}/${rp.counts.FAIL}/${rp.counts.PENDING}` : "–", rp ? "pass / flagged / pending · simulated" : "simulated"]);
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
      case "check_spec": return `${o.accepted ? "plannable" : "blocking errors"} · ${o.issues.length} notes`;
      case "get_standard": return `${o.requirements.length} requirements · ${o.sequence_rules.length} sequence rules`;
      case "list_test_methods": return `${o.methods.length} methods`;
      case "draft_campaign": return `${o.campaign_id} · ${o.totals.steps} tests · ${o.totals.samples_used} samples · ${o.totals.requirements_covered}/${o.totals.requirements_total} covered`;
      case "verify_campaign": return `${o.verdict} ${o.checks.filter(c => c.pass).length}/${o.checks.length} checks`;
      case "plan_procedure": return `${o.operations.length} ops · ${f(o.totals.bench_hours)} h bench · ${o.totals.cobot_handling_events} cobot handlings`;
      case "get_lab_state": return `${o.resources.length} resources · ${Object.values(o.bookings).flat().length} bookings`;
      case "schedule_campaign": return `${o.option_id} · report ${o.report_due} · ${o.slack_days >= 0 ? "+" : ""}${o.slack_days} d`;
      case "run_dry_run": return `SIMULATED · ${o.counts.PASS} pass · ${o.counts.FAIL} flagged · ${o.counts.PENDING} pending`;
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
        sys("handoff", `<b>${(AGENTS[p.from] || { n: p.from }).n} → ${(AGENTS[p.to] || { n: p.to }).n}</b> · ${fmtText(p.note)}`); break;
      case "rejection":
        S.loops += 1; setNode("planner", "rejected", "rework #" + S.loops); renderPipeline();
        sys("reject", `<b>↺ Verification rejected ${esc(p.campaign_id)}, back to the Campaign Planner (round ${p.round})</b><ul class="plain">`
          + p.required_changes.map(c => `<li>${fmtText(c)}</li>`).join("") + "</ul>");
        break;
      case "artifact": onArtifact(p.kind, p.data, live); break;
      case "gate":
        setNode("engineer", "waiting", "awaiting you");
        sys("gate", `<b>All agents done. Campaign package ready for engineer release.</b> Rig and cobot bookings are held as tentative.`);
        setStatus("awaiting_approval"); break;
      case "approved":
        S.committed = true; S.decision = p; setNode("engineer", "done", "approved ✓");
        sys("ok", `<b>Approved by ${esc(p.engineer)}</b>. ${p.bookings_committed} bookings committed on rigs, cobot and partners${p.comment ? " · “" + esc(p.comment) + "”" : ""}`);
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
    const fn = { spec: tabSpec, campaign: tabCampaign, verification: tabVerif, procedure: tabProcedure, schedule: tabSchedule, report: tabReport, package: tabPackage }[S.tab];
    if (S.renderedTab !== S.tab) b.scrollTop = 0;
    S.renderedTab = S.tab;
    b.innerHTML = ""; fn(b);
  }
  const emptyMsg = (b, m) => { b.innerHTML = `<div class="empty">${m}</div>`; };
  const card = (k, v, s = "") => `<div class="card"><div class="k">${esc(k)}</div><div class="v">${v}</div><div class="s">${s}</div></div>`;
  const sev = s => ({ error: "fail", warning: "warn", info: "info" }[s] || "info");

  function tabSpec(b) {
    const a = S.art.spec_check; if (!a) return emptyMsg(b, "The Intake Agent will validate the test request here.");
    const d = a.derived || {}, s = a.normalized_spec;
    let h = `<div class="round-h"><span>Intake decision</span><span class="${a.decision === "accept" ? "pass" : "fail"}">${a.decision === "accept" ? "Accepted" : "Needs clarification"}</span></div>
      <div class="note">${fmtText(a.summary)}</div>`;
    if (d.hydrostatic_stage2_bar !== undefined) h += `<h3>Derived test conditions (deterministic)</h3><div class="cards">
      ${card("Hydrostatic stage 2", f(d.hydrostatic_stage2_bar, 1) + " bar", "3× max operating pressure")}
      ${d.dp_flow_span_lpm ? card("ΔP flow span", `${d.dp_flow_span_lpm[0]} to ${d.dp_flow_span_lpm[1]} L/min`, "25 % to 150 % of rated") : ""}
      ${d.port_velocity_at_150pct_m_s !== undefined ? card("Port velocity", f(d.port_velocity_at_150pct_m_s, 2) + " m/s", "at 150 % flow · limit 1.5") : ""}
      ${d.samples_recommended ? card("Samples", `${s.samples} supplied`, `${d.samples_recommended} recommended`) : ""}</div>`;
    h += `<h3>Checks</h3><table class="dt"><tr><th>Field</th><th>Finding</th><th></th></tr>` + (a.issues.length ? a.issues.map(i =>
      `<tr><td class="mono">${esc(i.field)}</td><td>${fmtText(i.message)}</td><td class="${sev(i.severity)}">${i.severity}</td></tr>`).join("") : `<tr><td colspan=3 class="pass">No issues</td></tr>`) + "</table>";
    if (a.customer_questions && a.customer_questions.length) h += `<h3>Questions for the customer</h3><ul class="plain">${a.customer_questions.map(q => `<li>${fmtText(q)}</li>`).join("")}</ul>`;
    h += `<h3>Normalised request</h3><div class="params">${Object.entries(s).filter(([k]) => k !== "notes").map(([k, v]) => `<div><span>${esc(pretty(k))}</span><span>${esc(v)}</span></div>`).join("")}</div>`;
    if (s.notes) h += `<div class="note">${esc(s.notes)}</div>`;
    b.innerHTML = h;
  }

  const WHERE = { bench: "bench", hired: "hired", metrology: "univ. CMM", partner: "partner (not contracted)" };
  function stepsTable(c) {
    return `<table class="dt"><tr><th>Step</th><th>Sample</th><th>Test</th><th>Parameters</th><th>Where</th><th class="num">h</th><th>Req</th></tr>` + c.steps.map(s =>
      `<tr><td class="mono">${s.step_id}</td><td class="mono">${s.sample_id}</td><td>${esc(s.name)}${s.destructive ? ' <span class="fail">destructive</span>' : ""}
        <div style="color:var(--muted);font-size:11px">${fmtText(s.acceptance)}</div></td>
        <td class="mono" style="font-size:11px">${esc(Object.entries(s.params).map(([k, v]) => `${k}=${Array.isArray(v) ? v.join("/") : v}`).join(" "))}</td>
        <td>${esc(s.resource)}<div style="color:var(--muted);font-size:11px">${WHERE[s.where]}</div></td><td class="num">${f(s.run_minutes / 60, 1)}</td><td class="mono">${s.requirement || "–"}</td></tr>`).join("") + "</table>";
  }
  function tabCampaign(b) {
    const cs = S.art.campaigns, sel = S.art.campaign_selection;
    if (!cs) return emptyMsg(b, "The Campaign Planner's draft campaigns will appear here.");
    const rejected = S.verifs.filter(v => v.agent_verdict !== "approve").map(v => v.campaign_id);
    const selected = sel ? sel.selected : null;
    const c = (sel && sel.campaign) || cs.campaigns[cs.campaigns.length - 1];
    const lanes = Object.entries(c.sample_sequences).map(([sid, seq]) => `<div class="lane"><span class="mono">${sid}</span>${seq.map(id => {
      const s = c.steps.find(x => x.step_id === id);
      return `<span class="chip ${s.where}${s.destructive ? " destr" : ""}" title="${esc(s.name)}">${id} ${esc(s.name)}</span>`; }).join('<span class="arr">→</span>')}</div>`).join("");
    b.innerHTML = `<h3 style="margin-top:0">Drafts</h3><table class="dt"><tr><th>ID</th><th>Label</th><th class="num">Tests</th><th class="num">Samples</th><th class="num">Covered</th><th class="num">Bench h</th><th>Status</th></tr>`
      + cs.campaigns.map(x => `<tr class="${x.campaign_id === selected ? "sel" : ""}"><td class="mono">${x.campaign_id}</td><td>${esc(x.label)}</td><td class="num">${x.totals.steps}</td>
        <td class="num">${x.totals.samples_used}</td><td class="num">${x.totals.requirements_covered}/${x.totals.requirements_total}</td><td class="num">${f(x.totals.bench_hours)}</td>
        <td>${rejected.includes(x.campaign_id) ? '<span class="fail">rejected</span>' : x.campaign_id === selected ? '<span class="pass">submitted</span>' : "draft"}</td></tr>`).join("") + "</table>"
      + `<h3>${esc(c.campaign_id)} · test sequence by sample</h3><div class="lanes">${lanes}</div>
      <div class="legend"><span><i style="background:var(--accent)"></i>Bench (cobot-handled)</span><span><i style="background:#9A9CEB"></i>Hired instrument</span><span><i style="background:#8A969D"></i>University CMM</span><span><i style="background:var(--warning)"></i>Partner lab (not contracted)</span></div>
      ${sel ? `<div class="note">${fmtText(sel.rationale)}${sel.response_to_verification ? "\n\nResponse to verification: " + fmtText(sel.response_to_verification) : ""}</div>` : ""}
      <h3>Steps</h3>${stepsTable(c)}
      <h3>Standard · ${esc(cs.standard.id)}</h3><div class="note">${esc(cs.standard.provenance)} <a href="${esc(cs.standard.url)}" target="_blank" rel="noopener">Source</a></div>
      <table class="dt"><tr><th>Req</th><th>Requirement</th><th>Rule (planning summary)</th><th>Steps</th></tr>${cs.standard.requirements.map(r => {
        const st = c.steps.filter(s => s.requirement === r.id).map(s => s.step_id);
        return `<tr class="${st.length ? "" : "bad"}"><td class="mono">${r.id}</td><td>${esc(r.name)}</td><td style="font-size:12px">${fmtText(r.rule)}</td><td class="mono">${st.join(", ") || '<span class="fail">none</span>'}</td></tr>`; }).join("")}</table>`;
  }

  function tabVerif(b) {
    if (!S.verifs.length) return emptyMsg(b, "The Verification Agent's independent checks will appear here.");
    b.innerHTML = `<div class="note">Checked against ${fmtText(S.verifs[0].standard)}. The verifier recomputes from the step list and does not use the planner's totals.</div>`
      + S.verifs.slice().reverse().map(v => `<div class="round ${v.agent_verdict === "approve" ? "" : "failed"}">
      <div class="round-h"><span>Round ${v.round} · ${esc(v.campaign_id)} · checks ${v.checks.filter(c => c.pass).length}/${v.checks.length} · coverage ${v.coverage.covered}/${v.coverage.total}</span><span class="${v.agent_verdict === "approve" ? "pass" : "fail"}">${v.agent_verdict === "approve" ? "Approved" : "Rejected"}</span></div>
      ${v.notes && v.notes.length ? `<div class="note">${fmtText(v.notes.join(" "))}</div>` : ""}
      <table class="dt" style="margin-top:6px"><tr><th>Check</th><th class="num">Value</th><th class="num">Limit</th><th></th></tr>${v.checks.slice().sort((a, b) => a.pass - b.pass).map(c =>
        `<tr class="${c.pass ? "" : "bad"}"><td>${fmtText(c.check)}${c.detail && !c.pass ? `<div style="color:var(--muted);font-size:11px">${fmtText(c.detail)}</div>` : ""}</td><td class="num">${esc(c.value)} ${fmtText(c.unit)}</td><td class="num">${esc(c.limit)}</td><td class="${c.pass ? "pass" : "fail"}">${c.pass ? "pass" : "fail"}</td></tr>`).join("")}</table>
      ${v.required_changes && v.required_changes.length ? `<h3>Required changes</h3><ul class="plain">${v.required_changes.map(c => `<li>${fmtText(c)}</li>`).join("")}</ul>` : ""}</div>`).join("");
  }

  function tabProcedure(b) {
    const a = S.art.procedure; if (!a) return emptyMsg(b, "The Test Procedure Agent's rig operations will appear here.");
    const t = a.totals, c = a.cost_estimate_gbp;
    b.innerHTML = `<div class="cards">${card("Bench + hired", f(t.bench_hours) + " h", `CMM ${f(t.metrology_hours)} h`)}${card("Cobot", `${t.cobot_handling_events} handlings`, `${f(t.cobot_hours, 2)} h load / connect / unload`)}
      ${card("Partner labs", f(t.partner_hours, 0) + " h", `${t.partner_steps} steps · not contracted`)}${card("Cost excl. partners", money(c.total_excl_partner), "planning rates, not quotes")}</div>
      <h3>Operations</h3><table class="dt"><tr><th>Step</th><th>Resource</th><th>Fixture / cobot tasks</th><th class="num">run h</th></tr>${a.operations.map(o =>
        `<tr><td class="mono">${o.step_id} ${o.sample_id}</td><td class="mono">${o.resource}</td><td>${esc(o.name)}<div style="color:var(--muted);font-size:11px">${esc(o.fixture)}${o.cobot_tasks.length ? " · " + esc(o.cobot_tasks.join(" → ")) : ""}${o.transit_working_days ? ` · ${o.transit_working_days} working days shipping each way` : ""}</div></td><td class="num">${f(o.run_min / 60, 1)}</td></tr>`).join("")}</table>
      <div class="note">${esc(a.rate_note)}</div>
      ${a.review ? `<h3>Agent review</h3><div class="note">${fmtText(a.review.summary)}\nBottleneck: ${fmtText(a.review.bottleneck)}</div><h3>Risks &amp; controls</h3><ul class="plain">${a.review.risks_and_controls.map(r => `<li>${fmtText(r)}</li>`).join("")}</ul>` : ""}`;
  }

  function tabSchedule(b) {
    const a = S.art.schedule; if (!a) return emptyMsg(b, "The Scheduling Agent's booking on the rigs and cobot will appear here.");
    b.innerHTML = `<div class="cards">${card("Release", dt(a.release))}${card("Last test ends", dt(a.last_test_end), `makespan ${f(a.makespan_days)} d`)}
      ${card("Report due", day(a.report_due), "5 working days after last test")}${card("vs deadline", `<span class="${a.on_time ? "pass" : "fail"}">${a.slack_days >= 0 ? "+" : ""}${a.slack_days} days</span>`, `deadline ${day(a.deadline)}`)}
      ${card("Unattended rig time", f(a.unattended_rig_hours) + " h", a.allow_saturday_handling ? "Saturday handling on" : "cobot weekdays 06:00 to 22:00")}</div>
      <h3>Lab schedule ${S.committed ? "(booked)" : "(tentative hold until release)"}</h3><div id="gantt"></div>
      <div class="note">${fmtText(a.summary)}</div>`;
    Charts.gantt($("#gantt"), { machines: a.machines, bookings: S.board || a.board, jobId: S.jobId, deadline: a.deadline, delivery: a.report_due, committed: S.committed });
  }

  function tabReport(b) {
    const a = S.art.report; if (!a) return emptyMsg(b, "The Report Agent's qualification report draft will appear here.");
    const st = s => `<span class="${{ PASS: "pass", FAIL: "fail", PENDING: "warn", REPORT: "info", "NOT PLANNED": "fail" }[s] || "info"}">${s}</span>`;
    b.innerHTML = `<div class="sim-banner">${esc(a.banner)}</div>
      <div class="round-h"><span>${esc(a.title)}</span><a class="btn small ghost" href="/api/jobs/${S.jobId}/report.md" download>Download .md</a></div>
      <div class="cards">${card("Pass", a.counts.PASS, "simulated")}${card("Flagged", `<span class="${a.counts.FAIL ? "fail" : "pass"}">${a.counts.FAIL}</span>`, "simulated")}
      ${card("Pending", a.counts.PENDING, "partner labs")}${card("Report only", a.counts.REPORT)}</div>
      ${a.flagged.length ? `<h3>Flagged</h3><ul class="plain">${a.flagged.map(x => `<li><b>${esc(x.step_id)} ${esc(x.name)}</b>: ${fmtText(x.value)}. ${fmtText(x.note)}</li>`).join("")}</ul>` : ""}
      <h3>Traceability to ${esc(a.standard.split(":")[0])}</h3><table class="dt"><tr><th>Req</th><th>Requirement</th><th>Steps</th><th></th></tr>${a.traceability.map(t =>
        `<tr><td class="mono">${t.requirement}</td><td>${esc(t.name)}</td><td class="mono">${t.steps.join(", ") || "–"}</td><td>${st(t.status)}</td></tr>`).join("")}</table>
      <h3>Results by step (simulated)</h3><table class="dt"><tr><th>Step</th><th>Test</th><th>Value</th><th></th></tr>${a.results.map(r =>
        `<tr class="${r.status === "FAIL" ? "bad" : ""}"><td class="mono">${r.step_id} ${r.sample_id}</td><td>${esc(r.name)}<div style="color:var(--muted);font-size:11px">${fmtText(r.acceptance)}</div></td><td>${fmtText(r.value || r.note || "–")}</td><td>${st(r.status)}</td></tr>`).join("")}</table>
      ${a.review ? `<h3>Open items</h3><ul class="plain">${a.review.open_items.map(n => `<li>${fmtText(n)}</li>`).join("")}</ul>` : ""}
      <div class="note">${esc(a.statement)}</div>`;
  }

  function tabPackage(b) {
    const p = S.art.job_package; if (!p) return emptyMsg(b, "The campaign package for engineer release will appear here.");
    const c = p.dry_run_counts;
    b.innerHTML = `<div class="round-h"><span>${esc(p.job_id)} · ${esc(p.customer)} · ${esc(p.part_name)}</span><span class="status-pill ${S.status}">${S.status.replace(/_/g, " ")}</span></div>
      <div class="cards">${card("Campaign", esc(p.campaign_id), `${esc(p.standard)} · ${p.campaigns_drafted} drafts`)}${card("Coverage", `${p.coverage.covered}/${p.coverage.total}`, `checks ${p.checks_passed} · ${p.verification_rounds} rounds`)}
      ${card("Tests", p.steps, `${p.samples_used} of ${p.samples_supplied} samples`)}${card("Rig time", f(p.bench_hours) + " h", `${p.cobot_handling_events} cobot handlings · ${f(p.unattended_rig_hours)} h unattended`)}
      ${card("Partner labs", f(p.partner_hours, 0) + " h", "not contracted")}${card("Cost excl. partners", money(p.cost_excl_partner_gbp), "planning rates")}
      ${card("Report due", day(p.report_due), `${p.slack_days >= 0 ? "+" : ""}${p.slack_days} d vs ${day(p.deadline)}`)}${card("Dry run (simulated)", `${c.PASS}/${c.FAIL}/${c.PENDING}`, "pass / flagged / pending")}</div>
      <div class="note">Releasing commits the rig, cobot and partner bookings. The engineer signs the final report after real results replace the simulated dry run.</div>
      ${S.decision ? `<div class="note">Engineer decision: ${esc(S.decision.engineer)}${S.decision.comment ? " · " + esc(S.decision.comment) : ""}</div>` : ""}`;
  }

  /* ---------------- gate ---------------- */
  function showGate() {
    const p = S.art.job_package; if (!p) return;
    $("#gate").classList.remove("hidden", "done");
    $("#gate-summary").innerHTML = `${esc(p.campaign_id)} · ${esc(p.standard)} · coverage ${p.coverage.covered}/${p.coverage.total} · ${p.steps} tests on ${p.samples_used} samples · `
      + `${f(p.bench_hours)} h rig time · report due ${day(p.report_due)} (${p.slack_days >= 0 ? "+" : ""}${p.slack_days} d) · ${p.verification_rounds} verification rounds`;
    $("#btn-approve").disabled = false; $("#btn-return").disabled = false;
  }
  async function decide(kind) {
    $("#btn-approve").disabled = true; $("#btn-return").disabled = true;
    const r = await fetch(`/api/jobs/${S.jobId}/${kind}`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engineer: "Lead engineer", comment: $("#gate-comment").value }) });
    if (!r.ok) { alertBox((await r.json()).detail); return; }
    if (kind === "approve") {
      $("#gate").classList.add("done"); $(".gate-title").innerHTML = "✓ Campaign released to the lab";
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
    else { b.textContent = "SCRIPTED · real tools, scripted agent choices"; }
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
