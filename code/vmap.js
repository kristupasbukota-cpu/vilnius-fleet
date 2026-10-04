/* vmap.js: the project's default map. A zoomable SVG map on a vector basemap made by
   code/basemap.py, with an overlay layer for each page's own data.

   Inline it in a page after the basemap JSON, then:

     const map = VMap.create(document.getElementById("map"), BASE, {
       labels: (add, ctx) => { ... },   // optional: the page's labels, placed before the basemap's
       onView: ctx => { ... },          // optional: called on every pan or zoom (ctx.u = metres per pixel)
     });
     const [x, y] = map.proj([lon, lat]);   // metres in the basemap's frame
     map.overlay                            // <g> to draw the page's paths and markers into
     map.fit(points)                        // frame a list of [x, y] points
     map.fit(points, true)                  // ... and make it the view the ⤢ button returns to
     map.redraw()                           // re-place labels after the overlay changes

   Overlay strokes: use vector-effect="non-scaling-stroke" so widths stay in screen pixels.
   Markers drawn in metres: resize them in onView with ctx.u.
   add(x, y, text, px, cls, angle, anchor, dx, dy, force) places a label of px screen pixels,
   offset dx, dy pixels; it is skipped if it would overlap one already placed, unless force.

   Theme tokens the page must define on :root and in both dark blocks:
     --m-land --m-water --m-green --m-road --m-road2 --m-road3 --m-rail --m-label --m-halo
   and it uses --surface --rule --chip --ink --bg --muted --s1 --f-body --f-mono.
   Default values, as on the first page that used it:
     light  --m-land:#eceee9 --m-water:#a9cbe3 --m-green:#d5e4cc --m-road:#ffffff --m-road2:#fdfdfb
            --m-road3:#f7d98a --m-rail:#9a9d97 --m-label:#5d625c --m-halo:#eceee9
     dark   --m-land:#1b1e1c --m-water:#1d3a4e --m-green:#1f2b21 --m-road:#2f3431 --m-road2:#3c423e
            --m-road3:#6b5a2c --m-rail:#575b56 --m-label:#a3a89f --m-halo:#1b1e1c
   A dark casing under coloured overlay lines (#3b4046 light, #050606 dark) keeps pale colours readable.
   Map data © OpenStreetMap contributors (ODbL); the credit is drawn in the corner. */
const VMap = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
  const CSS = `
.vmap{position:relative;aspect-ratio:1/1.08;max-width:100%;border:1px solid var(--rule);border-radius:4px;overflow:hidden;background:var(--m-land);touch-action:none;cursor:grab;user-select:none;-webkit-user-select:none}
.vmap.drag{cursor:grabbing}
.vmap>svg{width:100%;height:100%;display:block}
.vmap .vlab text{paint-order:stroke;stroke:var(--m-halo);stroke-linejoin:round;pointer-events:none}
.vmap .m-street{font-family:var(--f-body);fill:var(--m-label);font-style:italic}
.vmap .m-place{font-family:var(--f-mono);fill:var(--m-label);letter-spacing:.08em;opacity:.85}
.vmap .m-stop{font-family:var(--f-body);fill:var(--ink);font-weight:500}
.vmap .m-stop.strong{font-weight:600}
.vmap .vctl{position:absolute;top:8px;right:8px;display:flex;flex-direction:column;border:1px solid var(--rule);border-radius:5px;overflow:hidden;background:var(--surface)}
.vmap .vctl button{width:32px;height:32px;border:0;background:var(--surface);color:var(--ink);font:500 17px var(--f-body);cursor:pointer;line-height:1}
.vmap .vctl button+button{border-top:1px solid var(--rule)}
.vmap .vctl button:hover{background:var(--chip)}
.vmap .vctl button:focus-visible{outline:2px solid var(--s1);outline-offset:-2px}
.vmap .vatt{position:absolute;right:0;bottom:0;font-size:10.5px;padding:1px 6px;background:var(--surface);color:var(--muted);opacity:.9;border-top-left-radius:4px}
.vmap .vhint{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:var(--ink);color:var(--bg);font-size:13px;padding:8px 12px;border-radius:5px;pointer-events:none}`;
  let styled = false;

  function create(host, BASE, opts = {}) {
    if (!styled) { const s = document.createElement("style"); s.textContent = CSS; document.head.appendChild(s); styled = true; }
    host.classList.add("vmap"); host.textContent = "";
    const proj = c => [(c[0] - BASE.origin[0]) * BASE.k[0], -(c[1] - BASE.origin[1]) * BASE.k[1]];
    const svg = el("svg", { role: "img", "aria-label": opts.label || "Map" }, host);
    const L = BASE.layers, ns = { "vector-effect": "non-scaling-stroke", fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" };
    el("rect", { x: -1e6, y: -1e6, width: 2e6, height: 2e6, fill: "var(--m-land)" }, svg);
    el("path", { d: L.green, fill: "var(--m-green)" }, svg);
    el("path", { d: L.water, fill: "var(--m-water)" }, svg);
    el("path", { ...ns, d: L.river, stroke: "var(--m-water)", "stroke-width": 3 }, svg);
    el("path", { ...ns, d: L.rail, stroke: "var(--m-rail)", "stroke-width": 1.2, "stroke-dasharray": "5 3" }, svg);
    [["minor", 1, "--m-road"], ["link", 1.4, "--m-road2"], ["mid", 2, "--m-road2"], ["major", 3.2, "--m-road3"]].forEach(([k, w, c]) =>
      L[k] && el("path", { ...ns, d: L[k], stroke: `var(${c})`, "stroke-width": w }, svg));
    const overlay = el("g", {}, svg), lab = el("g", { class: "vlab" }, svg);

    const size = () => { const r = host.getBoundingClientRect(); return [Math.max(1, r.width), Math.max(1, r.height)]; };
    let vb = null, raf = 0;
    const upp = () => vb[2] / size()[0];
    const set = v => { const [w, h] = size(); v[3] = v[2] * h / w; vb = v; svg.setAttribute("viewBox", v.map(x => x.toFixed(1)).join(" ")); redraw(); };
    const redraw = () => { if (raf || !vb) return; raf = requestAnimationFrame(() => { raf = 0; place(); }); };
    const zoomAt = (fx, fy, f) => { if (!vb) return; const v = vb.slice(); const w = Math.min(opts.maxWidth || 40000, Math.max(opts.minWidth || 400, v[2] * f)); const k = w / v[2];
      const px = v[0] + fx * v[2], py = v[1] + fy * v[3]; v[0] = px - (px - v[0]) * k; v[1] = py - (py - v[1]) * k; v[2] = w; set(v); };
    let last = [], homePts = null;
    const fit = (pts, home) => { if (pts) last = pts; if (home) homePts = pts; if (!last.length) return;
      const xs = last.map(p => p[0]), ys = last.map(p => p[1]); const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
      const [w, h] = size(); const pl = 34, pr = 52, pt = 30, pb = 34; const aw = w - pl - pr, ah = h - pt - pb;
      const k = Math.max((x1 - x0) / aw, (y1 - y0) / ah, 1);
      set([x0 - pl * k - (aw * k - (x1 - x0)) / 2, y0 - pt * k - (ah * k - (y1 - y0)) / 2, w * k, h * k]); };

    function place() {
      const u = upp(); lab.textContent = ""; const boxes = [];
      const inView = (x, y) => x > vb[0] && x < vb[0] + vb[2] && y > vb[1] && y < vb[1] + vb[3];
      const fits = b => { for (const q of boxes) if (b[0] < q[2] && b[2] > q[0] && b[1] < q[3] && b[3] > q[1]) return false; boxes.push(b); return true; };
      const add = (x, y, txt, px, cls, ang = 0, anchor = "middle", dx = 0, dy = 0, force = false) => {
        const w = txt.length * px * 0.56 * u, h = px * 1.25 * u, cx = x + dx * u, cy = y + dy * u;
        const r = Math.abs(ang) > 20 ? Math.max(w, h) : 0, x0 = anchor === "start" ? cx : anchor === "end" ? cx - w : cx - w / 2;
        const b = r ? [cx - r / 2, cy - r / 2, cx + r / 2, cy + r / 2] : [x0, cy - h * 0.8, x0 + w, cy + h * 0.3];
        if (force) boxes.push(b); else if (!fits(b)) return;
        const t = el("text", { x: cx, y: cy, "font-size": (px * u).toFixed(1), "stroke-width": (3 * u).toFixed(1), "text-anchor": anchor, class: cls,
          transform: ang ? `rotate(${ang} ${cx} ${cy})` : "" }, lab); t.textContent = txt; };
      const ctx = { u, vb, inView, add, reserve: b => boxes.push(b) };
      if (opts.onView) opts.onView(ctx);
      if (opts.labels) opts.labels(add, ctx);
      BASE.places.filter(p => inView(p.x, p.y) && (p.k === 1 || u < 14)).forEach(p => add(p.x, p.y, p.n.toUpperCase(), p.k === 1 ? 11.5 : 10.5, "m-place"));
      if (u < 12) BASE.streets.slice().sort((a, b) => b.L - a.L).filter(p => inView(p.x, p.y)).forEach(p => add(p.x, p.y + 3.5 * u, p.n, 10.5, "m-street", p.a));
    }

    // controls, credit, hint
    const ctl = document.createElement("div"); ctl.className = "vctl";
    [["+", "Zoom in", () => zoomAt(.5, .5, 1 / 1.6)], ["−", "Zoom out", () => zoomAt(.5, .5, 1.6)], ["⤢", "Fit to view", () => fit(homePts || last)]].forEach(([t, a, f]) => {
      const b = document.createElement("button"); b.type = "button"; b.textContent = t; b.title = a; b.setAttribute("aria-label", a); b.onclick = f; ctl.appendChild(b); });
    host.appendChild(ctl);
    const att = document.createElement("div"); att.className = "vatt"; att.textContent = BASE.credit || "© OpenStreetMap contributors"; host.appendChild(att);
    const hint = document.createElement("div"); hint.className = "vhint"; hint.hidden = true; hint.textContent = "Use Ctrl or ⌘ with scroll to zoom the map"; host.appendChild(hint);

    // drag to pan, pinch and double-click to zoom, Ctrl/⌘ + wheel to zoom
    const ptrs = new Map(); let pinch = null;
    svg.addEventListener("pointerdown", ev => { if (ev.pointerType === "mouse" && ev.button !== 0) return; ptrs.set(ev.pointerId, [ev.clientX, ev.clientY]); svg.setPointerCapture(ev.pointerId); pinch = null; host.classList.add("drag"); });
    svg.addEventListener("pointermove", ev => { if (!ptrs.has(ev.pointerId) || !vb) return; const prev = ptrs.get(ev.pointerId); ptrs.set(ev.pointerId, [ev.clientX, ev.clientY]);
      if (opts.onDrag) opts.onDrag();
      if (ptrs.size === 1) { const u = upp(), v = vb.slice(); v[0] -= (ev.clientX - prev[0]) * u; v[1] -= (ev.clientY - prev[1]) * u; set(v); }
      else if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; const d = Math.hypot(a[0] - b[0], a[1] - b[1]); const r = host.getBoundingClientRect();
        if (pinch) zoomAt(((a[0] + b[0]) / 2 - r.left) / r.width, ((a[1] + b[1]) / 2 - r.top) / r.height, pinch / d); pinch = d; } });
    const up = ev => { ptrs.delete(ev.pointerId); pinch = null; if (!ptrs.size) host.classList.remove("drag"); };
    svg.addEventListener("pointerup", up); svg.addEventListener("pointercancel", up);
    svg.addEventListener("dblclick", ev => { const r = host.getBoundingClientRect(); zoomAt((ev.clientX - r.left) / r.width, (ev.clientY - r.top) / r.height, ev.shiftKey ? 1.8 : 1 / 1.8); });
    let ht = 0;
    svg.addEventListener("wheel", ev => { if (!(ev.ctrlKey || ev.metaKey)) { hint.hidden = false; clearTimeout(ht); ht = setTimeout(() => hint.hidden = true, 1200); return; }
      ev.preventDefault(); const r = host.getBoundingClientRect(); zoomAt((ev.clientX - r.left) / r.width, (ev.clientY - r.top) / r.height, Math.exp(ev.deltaY * 0.0022)); }, { passive: false });
    new ResizeObserver(() => { if (vb) set(vb.slice()); }).observe(host);

    return { proj, overlay, fit, redraw, svg, host, upp: () => (vb ? upp() : null), el };
  }
  return { create };
})();
