/* Hand-rolled SVG charts: design-space scatter, thermal stack, factory Gantt. */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const tipEl = () => document.getElementById("tooltip");

  function el(tag, attrs = {}, parent) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (parent) parent.appendChild(e);
    return e;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function showTip(html, ev) {
    const t = tipEl(); t.innerHTML = html; t.classList.remove("hidden");
    const w = t.offsetWidth, h = t.offsetHeight;
    let x = ev.clientX + 14, y = ev.clientY + 14;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - 14;
    if (y + h > window.innerHeight - 8) y = ev.clientY - h - 14;
    t.style.left = x + "px"; t.style.top = y + "px";
  }
  function hideTip() { tipEl().classList.add("hidden"); }
  const row = (k, v) => `<div class="r"><span>${esc(k)}</span><span>${esc(v)}</span></div>`;

  function niceTicks(lo, hi, n = 5) {
    const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => span / s <= n) || 10 * mag;
    const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }

  /* ---------- design space scatter: case temperature vs pressure drop ---------- */
  function designSpace(container, { points, candidates, selected, rejected, tMax, dpMax }) {
    container.innerHTML = "";
    const W = Math.max(container.clientWidth, 360), H = 300, m = { l: 46, r: 14, t: 14, b: 38 };
    const svg = el("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img",
      "aria-label": "Case temperature versus pressure drop for every evaluated design" }, container);
    const all = points.concat(candidates);
    if (!all.length) return;
    const xs = all.map(p => p.dp_kpa).concat([dpMax]), ys = all.map(p => p.t_case_c).concat([tMax]);
    const useLog = Math.max(...xs) / Math.max(Math.min(...xs), 0.1) > 25;
    let x0 = Math.min(...xs), x1 = Math.max(...xs);
    const y0 = Math.floor(Math.min(...ys) - 1), y1 = Math.ceil(Math.max(...ys) + 1);
    let fx;
    if (useLog) {
      x0 = Math.pow(10, Math.floor(Math.log10(Math.max(x0 * 0.8, 0.1)) * 2) / 2);
      x1 = Math.pow(10, Math.ceil(Math.log10(x1 * 1.2) * 2) / 2);
      fx = v => m.l + (Math.log10(v) - Math.log10(x0)) / (Math.log10(x1) - Math.log10(x0)) * (W - m.l - m.r);
    } else {
      x0 = 0; x1 = x1 * 1.12;
      fx = v => m.l + (v - x0) / (x1 - x0) * (W - m.l - m.r);
    }
    const fy = v => H - m.b - (v - y0) / (y1 - y0) * (H - m.t - m.b);
    // spec window
    el("rect", { x: m.l, y: fy(Math.min(tMax, y1)), width: Math.max(0, fx(Math.min(dpMax, x1)) - m.l),
      height: Math.max(0, fy(y0) - fy(Math.min(tMax, y1))), fill: "rgba(57,135,229,0.07)" }, svg);
    // grid + axes
    const g = el("g", { class: "grid" }, svg);
    const yt = niceTicks(y0, y1, 5);
    yt.forEach(v => { el("line", { x1: m.l, x2: W - m.r, y1: fy(v), y2: fy(v) }, g);
      el("text", { x: m.l - 6, y: fy(v) + 3, "text-anchor": "end" }, svg).textContent = v; });
    const xt = useLog ? [0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000].filter(v => v >= x0 && v <= x1) : niceTicks(x0, x1, 6);
    xt.forEach(v => { el("line", { x1: fx(v), x2: fx(v), y1: m.t, y2: H - m.b }, g);
      el("text", { x: fx(v), y: H - m.b + 14, "text-anchor": "middle" }, svg).textContent = v; });
    el("text", { x: (m.l + W - m.r) / 2, y: H - 4, "text-anchor": "middle", class: "ttl" }, svg).textContent =
      `Pressure drop, kPa${useLog ? " (log scale)" : ""}`;
    const yl = el("text", { x: 12, y: (m.t + H - m.b) / 2, "text-anchor": "middle", class: "ttl",
      transform: `rotate(-90 12 ${(m.t + H - m.b) / 2})` }, svg); yl.textContent = "Case temperature, °C";
    // limits
    if (tMax <= y1) { el("line", { class: "lim", x1: m.l, x2: W - m.r, y1: fy(tMax), y2: fy(tMax) }, svg);
      el("text", { x: W - m.r - 2, y: fy(tMax) - 4, "text-anchor": "end" }, svg).textContent = `max case ${tMax} °C`; }
    if (dpMax <= x1) { el("line", { class: "lim", x1: fx(dpMax), x2: fx(dpMax), y1: m.t, y2: H - m.b }, svg);
      el("text", { x: fx(dpMax) + 4, y: m.t + 10 }, svg).textContent = `max ΔP ${dpMax} kPa`; }
    // sweep points
    const hit = [];
    points.forEach(p => {
      const cx = fx(p.dp_kpa), cy = fy(p.t_case_c);
      el("circle", { cx, cy, r: 4, fill: p.meets_constraints ? "#3987e5" : "#5f5e58", stroke: "#1a1a19", "stroke-width": 2, opacity: 0.9 }, svg);
      hit.push({ cx, cy, html: `<b>Sweep variant</b>` + Object.entries(p.params).map(([k, v]) => row(k.replace(/_mm$/, " (mm)").replace(/_/g, " "), v)).join("")
        + row("Case temp", p.t_case_c.toFixed(2) + " °C") + row("ΔP", p.dp_kpa.toFixed(2) + " kPa")
        + row("Meets sweep constraints", p.meets_constraints ? "yes" : "no") });
    });
    // evaluated candidates (labelled)
    candidates.forEach(c => {
      const cx = fx(c.dp_kpa), cy = fy(c.t_case_c);
      const isSel = c.design_id === selected, isRej = rejected.includes(c.design_id);
      el("circle", { cx, cy, r: isSel ? 8 : 6.5, fill: isSel ? "#3987e5" : "#1a1a19",
        stroke: isRej ? "#ec835a" : "#f0efec", "stroke-width": 2 }, svg);
      const t = el("text", { x: cx + 10, y: cy - 7, "font-weight": 600 }, svg);
      t.textContent = c.design_id + (isRej ? " ✕" : isSel ? " ✓" : "");
      t.setAttribute("fill", isRej ? "#ec835a" : "#f0efec");
      hit.push({ cx, cy, r: 10, html: `<b>${esc(c.design_id)} · ${esc(c.label)}</b>` + row("Case temp", c.t_case_c.toFixed(2) + " °C")
        + row("ΔP", c.dp_kpa.toFixed(2) + " kPa") + row("Regime", `${c.regime}, Re ${Math.round(c.reynolds)}`)
        + row("Status", isRej ? "rejected by verification" : isSel ? "selected" : c.meets_nominal_limits ? "meets nominal" : "misses spec") });
    });
    const overlay = el("rect", { x: 0, y: 0, width: W, height: H, fill: "transparent" }, svg);
    overlay.addEventListener("mousemove", ev => {
      const r = svg.getBoundingClientRect(), sx = (ev.clientX - r.left) * W / r.width, sy = (ev.clientY - r.top) * H / r.height;
      let best = null, bd = 14;
      hit.forEach(h => { const d = Math.hypot(h.cx - sx, h.cy - sy); if (d < Math.max(bd, h.r || 0) && (!best || d < best.d)) best = { ...h, d }; });
      best ? showTip(best.html, ev) : hideTip();
    });
    overlay.addEventListener("mouseleave", hideTip);
  }

  /* ---------- thermal stack: inlet -> case temperature contributions ---------- */
  const STACK = [["caloric", "Coolant rise to bulk mean", "#3987e5"], ["convection", "Convection (h·A·η)", "#d95926"],
    ["base_conduction", "Base conduction", "#199e70"], ["spreading", "Spreading", "#c98500"], ["tim", "TIM2", "#d55181"]];
  function thermalStack(container, { inlet, dt, tMax, worst }) {
    container.innerHTML = "";
    const W = Math.max(container.clientWidth, 360), H = 92, m = { l: 8, r: 12, t: 22, b: 26 };
    const svg = el("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Temperature rise contributions from coolant inlet to case" }, container);
    const total = STACK.reduce((s, [k]) => s + (dt[k] || 0), 0);
    const hi = Math.max(inlet + total, tMax, worst || 0) + 1, lo = inlet;
    const fx = v => m.l + (v - lo) / (hi - lo) * (W - m.l - m.r);
    let cur = inlet;
    STACK.forEach(([k, name, col]) => {
      const v = dt[k] || 0; if (v <= 0) return;
      const x = fx(cur), w = Math.max(fx(cur + v) - x - 2, 1);
      const r = el("rect", { x, y: m.t, width: w, height: 24, rx: 3, fill: col }, svg);
      if (w > 34) { const t = el("text", { x: x + w / 2, y: m.t + 16, "text-anchor": "middle", "font-weight": 600 }, svg); t.textContent = "+" + v.toFixed(1); t.setAttribute("fill", "#fff"); }
      const c0 = cur;
      r.addEventListener("mousemove", ev => showTip(`<b>${name}</b>` + row("ΔT", v.toFixed(2) + " °C") + row("Range", `${c0.toFixed(1)} → ${(c0 + v).toFixed(1)} °C`), ev));
      r.addEventListener("mouseleave", hideTip);
      cur += v;
    });
    el("line", { class: "lim", x1: fx(tMax), x2: fx(tMax), y1: m.t - 8, y2: m.t + 32 }, svg);
    el("text", { x: fx(tMax), y: m.t - 11, "text-anchor": "middle" }, svg).textContent = `limit ${tMax} °C`;
    if (worst) {
      el("path", { d: `M${fx(worst)} ${m.t + 27} l-4 7 h8 z`, fill: "#ec835a" }, svg);
      el("text", { x: fx(worst), y: H - 2, "text-anchor": "middle" }, svg).textContent = `worst case ${worst.toFixed(1)}`;
    }
    el("text", { x: m.l, y: m.t - 11 }, svg).textContent = `inlet ${inlet} °C`;
    el("text", { x: fx(cur), y: m.t + 42, "text-anchor": "middle", "font-weight": 600 }, svg).textContent = `case ${cur.toFixed(1)} °C`;
    const leg = document.createElement("div"); leg.className = "legend";
    leg.innerHTML = STACK.map(([, n, c]) => `<span><i style="background:${c}"></i>${n}</span>`).join("");
    container.appendChild(leg);
  }

  /* ---------- factory Gantt ---------- */
  function gantt(container, { machines, bookings, jobId, deadline, delivery, committed }) {
    container.innerHTML = "";
    const W = Math.max(container.clientWidth, 420), rowH = 42, m = { l: 74, r: 12, t: 30, b: 10 };
    const H = m.t + machines.length * rowH + m.b;
    const svg = el("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Lab schedule" }, container);
    const defs = el("defs", {}, svg);
    const pat = el("pattern", { id: "hatch", width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
    el("rect", { width: 6, height: 6, fill: "#2a1c16" }, pat); el("line", { x1: 0, y1: 0, x2: 0, y2: 6, stroke: "#E59A2E", "stroke-width": 2 }, pat);
    const t0 = new Date(); t0.setHours(0, 0, 0, 0);
    const ends = bookings.map(b => new Date(b.end).getTime());
    const dl = deadline ? new Date(deadline + "T23:59:59").getTime() : 0;
    const t1 = Math.max(...ends, dl, t0.getTime() + 7 * 864e5) + 864e5;
    const fx = t => m.l + (t - t0.getTime()) / (t1 - t0.getTime()) * (W - m.l - m.r);
    // days
    for (let d = new Date(t0); d.getTime() < t1; d.setDate(d.getDate() + 1)) {
      const x = fx(d.getTime()), x2 = fx(d.getTime() + 864e5);
      if (d.getDay() === 0 || d.getDay() === 6) el("rect", { x, y: m.t, width: x2 - x, height: H - m.t - m.b, fill: "rgba(255,255,255,0.025)" }, svg);
      el("line", { x1: x, x2: x, y1: m.t - 4, y2: H - m.b, stroke: "rgba(255,255,255,0.06)" }, svg);
      if (x2 - x > 16) { const t = el("text", { x: (x + x2) / 2, y: m.t - 16, "text-anchor": "middle" }, svg);
        t.textContent = d.toLocaleDateString(undefined, { weekday: "narrow" });
        const t2 = el("text", { x: (x + x2) / 2, y: m.t - 5, "text-anchor": "middle" }, svg); t2.textContent = d.getDate(); }
    }
    const now = Date.now();
    el("line", { x1: fx(now), x2: fx(now), y1: m.t - 2, y2: H - m.b, stroke: "#f0efec", "stroke-width": 1 }, svg);
    machines.forEach((mc, i) => {
      const y = m.t + i * rowH;
      el("text", { x: 4, y: y + rowH / 2 + 4, "font-weight": 600 }, svg).textContent = mc.id;
      el("line", { x1: m.l, x2: W - m.r, y1: y + rowH, y2: y + rowH, stroke: "rgba(255,255,255,0.05)" }, svg);
      bookings.filter(b => b.machine_id === mc.id).forEach(b => {
        const s = new Date(b.start).getTime(), e = new Date(b.end).getTime();
        const x = fx(Math.max(s, t0.getTime())), w = Math.max(fx(e) - x - 1, 2);
        const mine = b.job_id === jobId && (b.kind === "tentative" || b.kind === "job");
        const fill = b.kind === "downtime" ? "url(#hatch)" : mine ? "#5CC6D6" : "#2E4B5A";
        const r = el("rect", { x, y: y + 7, width: w, height: rowH - 14, rx: 2, fill, opacity: mine && !committed ? 0.85 : 1 }, svg);
        const kind = b.kind === "downtime" ? "Downtime" : mine ? (committed ? "This job (booked)" : "This job (tentative hold)") : "Other work (demo data)";
        r.addEventListener("mousemove", ev => showTip(`<b>${esc(b.label)}</b>` + row("Type", kind) + row("Machine", mc.id)
          + row("Start", new Date(s).toLocaleString([], { weekday: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }))
          + row("End", new Date(e).toLocaleString([], { weekday: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })), ev));
        r.addEventListener("mouseleave", hideTip);
      });
    });
    const mark = (date, label, color) => {
      if (!date) return; const x = fx(new Date(date + "T12:00:00").getTime());
      el("line", { x1: x, x2: x, y1: m.t - 2, y2: H - m.b, stroke: color, "stroke-width": 2, "stroke-dasharray": "4 3" }, svg);
      const t = el("text", { x: x + 3, y: H - m.b - 4, "font-weight": 600 }, svg); t.textContent = label; t.setAttribute("fill", color);
    };
    mark(delivery, "report due", "#3FA66B");
    mark(deadline, "deadline", "#E59A2E");
    const leg = document.createElement("div"); leg.className = "legend";
    leg.innerHTML = `<span><i style="background:#5CC6D6"></i>This campaign</span><span><i style="background:#2E4B5A"></i>Other work (demo data)</span>
      <span><i style="background:repeating-linear-gradient(45deg,#ec835a 0 2px,#2a1c16 2px 5px)"></i>Planned downtime</span><span>Rigs 24/7 · cobot 06:00 to 22:00 Monday to Friday · partner labs not contracted</span>`;
    container.appendChild(leg);
  }

  window.Charts = { designSpace, thermalStack, gantt, esc, showTip, hideTip };
})();
