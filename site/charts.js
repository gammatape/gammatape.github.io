// Small SVG chart kit for the Gammatape market section (draft). No dependencies.
export const NS = "http://www.w3.org/2000/svg";
export const nf = (n, d = 2) => new Intl.NumberFormat("vi-VN", { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
export const sg = (n, d = 2) => (n > 0 ? "+" : n < 0 ? "−" : "") + nf(Math.abs(n), d);
export const dm = iso => iso.slice(8, 10) + "/" + iso.slice(5, 7);
export function svg(w, h) { const s = document.createElementNS(NS, "svg"); s.setAttribute("viewBox", `0 0 ${w} ${h}`); return s; }
export function add(p, tag, attrs, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = text;
  p.append(e); return e;
}
export function niceTicks(lo, hi, n = 4) {
  const span = hi - lo || 1, step0 = span / n, mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= step0);
  const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6)); return out;
}
export function tipFor(box) {
  const t = document.createElement("div"); t.className = "tip"; box.append(t);
  return {
    show(x, y, html) { t.innerHTML = html; t.style.left = Math.max(60, Math.min(box.clientWidth - 60, x)) + "px"; t.style.top = y + "px"; t.style.opacity = 1; },
    hide() { t.style.opacity = 0; },
  };
}
export function fresh(box, h, minW = 280) {
  box.querySelector("svg")?.remove(); box.querySelector(".tip")?.remove();
  const W = Math.max(minW, box.clientWidth), s = svg(W, h); box.prepend(s); return [s, W];
}
// bar with a rounded free end, anchored on the baseline
export function barPath(x, w, y0, y1, r = 3) {
  const up = y1 < y0, h = Math.abs(y1 - y0); r = Math.min(r, h, w / 2);
  if (h < 0.5) return `M${x},${y0}h${w}`;
  return up ? `M${x},${y0}V${y1 + r}q0,-${r} ${r},-${r}h${w - 2 * r}q${r},0 ${r},${r}V${y0}Z`
            : `M${x},${y0}V${y1 - r}q0,${r} ${r},${r}h${w - 2 * r}q${r},0 ${r},-${r}V${y0}Z`;
}

// Diverging bars: polarity by position + colour + sign on labels
export function divergingBars(box, pts, { unit = "", digits = 2, labelAll = false, h = 210 } = {}) {
  const [s, W] = fresh(box, h), H = h, L = 40, R = 8, T = 18, B = 24;
  const vals = pts.map(p => p.v), lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
  const ticks = niceTicks(lo, hi), y0v = Math.min(lo, ticks[0]), y1v = Math.max(hi, ticks.at(-1));
  // room under the lowest bar for its value label, so it never sits on the date labels
  const padB = lo < 0 ? 16 : 0, y = v => T + (y1v - v) / (y1v - y0v || 1) * (H - T - B - padB);
  const g = add(s, "g", { class: "axis" });
  ticks.forEach(t => {
    add(g, "line", { x1: L, x2: W - R, y1: y(t), y2: y(t), stroke: t === 0 ? "var(--zero)" : "var(--grid)" });
    add(g, "text", { x: L - 6, y: y(t) + 4, "text-anchor": "end" }, nf(t, t % 1 ? 1 : 0));
  });
  const n = pts.length, slot = (W - L - R) / n, bw = Math.max(2, slot - Math.min(6, slot * .25));
  const maxI = vals.indexOf(Math.max(...vals)), minI = vals.indexOf(Math.min(...vals)), mixed = lo < 0 && hi > 0;
  const tip = tipFor(box);
  pts.forEach((p, i) => {
    const x = L + i * slot + (slot - bw) / 2;
    add(s, "path", { d: barPath(x, bw, y(0), y(p.v)), fill: p.v >= 0 ? "var(--green)" : "var(--red)", opacity: .9 });
    if ((labelAll && slot >= 34) || i === n - 1 || (mixed && (i === maxI || i === minI)))
      add(s, "text", { class: "lbl", x: x + bw / 2, y: p.v >= 0 ? y(p.v) - 5 : y(p.v) + 13, "text-anchor": "middle" }, sg(p.v, digits));
    const hit = add(s, "rect", { x: L + i * slot, y: T, width: slot, height: H - T - B, fill: "transparent" });
    hit.addEventListener("pointerenter", () => tip.show((x + bw / 2) / W * box.clientWidth, y(Math.max(p.v, 0)) / H * box.clientHeight,
      `${p.label}<br><b class="${p.v >= 0 ? "up" : "down"}">${sg(p.v, digits)} ${unit}</b>`));
    hit.addEventListener("pointerleave", () => tip.hide());
  });
  [0, Math.floor(n / 2), n - 1].forEach(i => add(g, "text", { x: L + i * slot + slot / 2, y: H - 6, "text-anchor": i === 0 ? "start" : i === n - 1 ? "end" : "middle" }, pts[i].short));
}

// Level line with soft area and crosshair (axis not forced to zero)
export function levelLine(box, pts, { unit = "", digits = 2, h = 160, color = "var(--gold)" } = {}) {
  const [s, W] = fresh(box, h), H = h, L = 46, R = 10, T = 14, B = 24;
  const vals = pts.map(p => p.v), ticks = niceTicks(Math.min(...vals), Math.max(...vals));
  const lo = Math.min(ticks[0], ...vals), hi = Math.max(ticks.at(-1), ...vals);
  const x = i => L + i / (pts.length - 1) * (W - L - R), y = v => T + (hi - v) / (hi - lo || 1) * (H - T - B);
  const g = add(s, "g", { class: "axis" });
  ticks.forEach(t => { add(g, "line", { x1: L, x2: W - R, y1: y(t), y2: y(t), stroke: "var(--grid)" }); add(g, "text", { x: L - 6, y: y(t) + 4, "text-anchor": "end" }, nf(t, 0)); });
  const d = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
  const id = "ga" + Math.random().toString(36).slice(2, 7), lg = add(add(s, "defs", {}), "linearGradient", { id, x1: 0, x2: 0, y1: 0, y2: 1 });
  add(lg, "stop", { offset: "0", "stop-color": "#f5b301", "stop-opacity": ".25" }); add(lg, "stop", { offset: "1", "stop-color": "#f5b301", "stop-opacity": "0" });
  add(s, "path", { d: d + `L${x(pts.length - 1)},${H - B}L${x(0)},${H - B}Z`, fill: `url(#${id})` });
  add(s, "path", { d, fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round" });
  const last = pts.at(-1);
  add(s, "circle", { cx: x(pts.length - 1), cy: y(last.v), r: 4, fill: color, stroke: "var(--panel)", "stroke-width": 2 });
  add(s, "text", { class: "lbl", x: x(pts.length - 1) - 6, y: y(last.v) - 9, "text-anchor": "end" }, nf(last.v, digits) + " " + unit);
  [0, Math.floor((pts.length - 1) / 2), pts.length - 1].forEach(i => add(g, "text", { x: x(i), y: H - 6, "text-anchor": i === 0 ? "start" : i === pts.length - 1 ? "end" : "middle" }, pts[i].short));
  crosshair(box, s, W, H, T, B, L, R, pts.length, i => [x(i), y(pts[i].v), `${pts[i].label}<br><b>${nf(pts[i].v, digits)} ${unit}</b>`]);
}
function crosshair(box, s, W, H, T, B, L, R, n, at) {
  const tip = tipFor(box), cross = add(s, "line", { y1: T, y2: H - B, stroke: "var(--muted)", "stroke-dasharray": "3 3", opacity: 0 });
  const hit = add(s, "rect", { x: L, y: T, width: W - L - R, height: H - T - B, fill: "transparent" });
  hit.addEventListener("pointermove", e => {
    const r = s.getBoundingClientRect(), px = (e.clientX - r.left) / r.width * W;
    const i = Math.max(0, Math.min(n - 1, Math.round((px - L) / (W - L - R) * (n - 1)))), [cx, cy, html] = at(i);
    cross.setAttribute("x1", cx); cross.setAttribute("x2", cx); cross.setAttribute("opacity", 1);
    tip.show(cx / W * box.clientWidth, cy / H * box.clientHeight, html);
  });
  hit.addEventListener("pointerleave", () => { cross.setAttribute("opacity", 0); tip.hide(); });
}

// Tiny area sparkline around zero for a small-multiple card
export function miniArea(box, vals, { h = 64 } = {}) {
  const [s, W] = fresh(box, h, 120), lo = Math.min(0, ...vals), hi = Math.max(0, ...vals), P = 3;
  const x = i => i / (vals.length - 1) * W, y = v => P + (hi - v) / (hi - lo || 1) * (h - 2 * P);
  const d = vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const pos = vals.at(-1) >= 0, c = pos ? "var(--green)" : "var(--red)";
  add(s, "path", { d: d + `L${W},${y(0)}L0,${y(0)}Z`, fill: c, opacity: .14 });
  add(s, "line", { x1: 0, x2: W, y1: y(0), y2: y(0), stroke: "var(--zero)", "stroke-dasharray": "3 3" });
  add(s, "path", { d, fill: "none", stroke: c, "stroke-width": 2, "stroke-linejoin": "round" });
  add(s, "circle", { cx: x(vals.length - 1) - 3, cy: y(vals.at(-1)), r: 3.5, fill: c, stroke: "var(--panel2)", "stroke-width": 2 });
}

// Tiny min-max line (price or rate trend), last point marked
export function miniLine(box, vals, { h = 40, color = "var(--gold)", fill = true } = {}) {
  const [s, W] = fresh(box, h, 80), P = 4, lo = Math.min(...vals), hi = Math.max(...vals);
  const x = i => i / (vals.length - 1) * (W - 6), y = v => P + (hi - v) / (hi - lo || 1) * (h - 2 * P);
  const d = vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  if (fill) add(s, "path", { d: d + `L${x(vals.length - 1)},${h}L0,${h}Z`, fill: color, opacity: .10 });
  add(s, "path", { d, fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" });
  add(s, "circle", { cx: x(vals.length - 1), cy: y(vals.at(-1)), r: 3, fill: color });
}

// Half-circle gauge 0..100 with labelled zones; needle at value
export function halfGauge(box, value, zones, { h = 120 } = {}) {
  const [s, W] = fresh(box, h, 200), cx = W / 2, r = Math.min(W / 2 - 10, h - 22), cy = r + 8, sw = 16;
  const pt = (v, rr) => { const a = Math.PI * (1 - v / 100); return [cx + rr * Math.cos(a), cy - rr * Math.sin(a)]; };
  zones.forEach(z => {
    const [x0, y0] = pt(z.from + .6, r), [x1, y1] = pt(z.to - .6, r);
    add(s, "path", { d: `M${x0},${y0}A${r},${r} 0 0 1 ${x1},${y1}`, fill: "none", stroke: z.color, "stroke-width": sw, opacity: value >= z.from && value < z.to + (z.to === 100) ? 1 : .35 });
  });
  const [nx, ny] = pt(value, r - sw / 2 - 6);
  add(s, "line", { x1: cx, y1: cy, x2: nx, y2: ny, stroke: "var(--text)", "stroke-width": 3, "stroke-linecap": "round" });
  add(s, "circle", { cx, cy, r: 6, fill: "var(--text)" });
  const g = add(s, "g", { class: "axis" });
  [[0, "0"], [100, "100"]].forEach(([v, t]) => { const [tx, ty] = pt(v, r); add(g, "text", { x: tx, y: ty + 16, "text-anchor": "middle" }, t); });
}

// Multi-line chart over a categorical x axis (yield curve)
export function curveChart(box, labels, series, { h = 230 } = {}) {
  const [s, W] = fresh(box, h), H = h, L = 40, R = 70, T = 14, B = 26;
  const all = series.flatMap(se => se.v.filter(v => v != null)), ticks = niceTicks(Math.min(...all), Math.max(...all));
  const lo = Math.min(ticks[0], ...all), hi = Math.max(ticks.at(-1), ...all);
  const x = i => L + i / (labels.length - 1) * (W - L - R), y = v => T + (hi - v) / (hi - lo || 1) * (H - T - B);
  const g = add(s, "g", { class: "axis" });
  ticks.forEach(t => { add(g, "line", { x1: L, x2: W - R, y1: y(t), y2: y(t), stroke: "var(--grid)" }); add(g, "text", { x: L - 6, y: y(t) + 4, "text-anchor": "end" }, nf(t, 1) + "%"); });
  const narrow = W < 520;
  labels.forEach((l, i) => { if (!narrow || i % 2 === 0 || i === labels.length - 1) add(g, "text", { x: x(i), y: H - 6, "text-anchor": "middle" }, l); });
  // drawn back to front so "today" sits on top; direct label at the right end of each line
  const style = [{ stroke: "var(--gold)", w: 2.5, dash: "" }, { stroke: "var(--muted)", w: 2, dash: "5 4" }, { stroke: "var(--faint)", w: 1.5, dash: "2 4" }];
  const ends = [];
  [...series.keys()].reverse().forEach(k => {
    const se = series[k], st = style[k], d = se.v.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
    add(s, "path", { d, fill: "none", stroke: st.stroke, "stroke-width": st.w, "stroke-dasharray": st.dash, "stroke-linejoin": "round" });
    ends.push({ y: y(se.v.at(-1)), text: se.name, color: st.stroke });
  });
  ends.sort((a, b) => a.y - b.y).forEach((e, i, arr) => { if (i && e.y - arr[i - 1].y < 13) e.y = arr[i - 1].y + 13; add(s, "text", { x: W - R + 6, y: e.y + 4, fill: e.color, "font-size": 11, "font-weight": 700 }, e.text); });
  series[0].v.forEach((v, i) => add(s, "circle", { cx: x(i), cy: y(v), r: 3, fill: "var(--gold)" }));
  crosshair(box, s, W, H, T, B, L, R, labels.length, i => [x(i), y(series[0].v[i]),
    // change vs older curves is shown neutral: a higher yield is neither good nor bad by itself
    `<b>${labels[i]}</b><br>` + series.map((se, k) => `${se.name}: <b>${nf(se.v[i])}%</b>` + (k ? ` <span class="muted">(hôm nay ${sg(series[0].v[i] - se.v[i])})</span>` : "")).join("<br>")]);
}
