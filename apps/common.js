// A Pannon tankönyvsorozat interaktív alkalmazásainak közös segédfüggvényei (függőségek nélkül).
const PE = {
  pal: ["#2E6DB4", "#C8711E", "#7A4EAB", "#1F9077", "#B23A48"],
  ink: "#1F2933", muted: "#6B7785", grid: "#E6EAEE", blue: "#285780",
  // reprodukálható véletlenszám-generátor (mulberry32)
  rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; },
  normal(r) { let u = 0, v = 0; while (u === 0) u = r(); while (v === 0) v = r();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); },
  fmt(x, d = 2) { return (Math.round(x * 10 ** d) / 10 ** d).toFixed(d).replace(".", ","); },
  el(tag, attrs = {}, parent = null) { const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; },
  clear(svg) { while (svg.firstChild) svg.removeChild(svg.firstChild); },
  // lineáris skála
  scale(d0, d1, r0, r1) { const f = x => r0 + (x - d0) / (d1 - d0) * (r1 - r0); f.inv = y => d0 + (y - r0) / (r1 - r0) * (d1 - d0); return f; },
  // koordinátarendszer rajzolása; visszaadja az x, y skálát
  axes(svg, xd, yd, opt = {}) {
    const W = +svg.getAttribute("width"), H = +svg.getAttribute("height");
    const m = Object.assign({ l: 40, r: 10, t: 10, b: 30 }, opt.margin || {});
    const x = PE.scale(xd[0], xd[1], m.l, W - m.r), y = PE.scale(yd[0], yd[1], H - m.b, m.t);
    const g = PE.el("g", { class: "axis" }, svg);
    PE.el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b }, g);
    PE.el("line", { x1: m.l, x2: m.l, y1: m.t, y2: H - m.b }, g);
    const ticks = (a, b, n) => { const s = (b - a) / n; return Array.from({ length: n + 1 }, (_, i) => a + i * s); };
    for (const v of ticks(xd[0], xd[1], opt.nx || 5)) { PE.el("line", { x1: x(v), x2: x(v), y1: H - m.b, y2: H - m.b + 4 }, g);
      const t = PE.el("text", { x: x(v), y: H - m.b + 15, "text-anchor": "middle" }, g); t.textContent = PE.fmt(v, opt.dx ?? 1); }
    for (const v of ticks(yd[0], yd[1], opt.ny || 4)) { PE.el("line", { x1: m.l - 4, x2: m.l, y1: y(v), y2: y(v) }, g);
      const t = PE.el("text", { x: m.l - 6, y: y(v) + 3, "text-anchor": "end" }, g); t.textContent = PE.fmt(v, opt.dy ?? 1); }
    if (opt.xlab) { const t = PE.el("text", { x: (m.l + W - m.r) / 2, y: H - 2, "text-anchor": "middle", style: "font-size:11px;fill:#1F2933" }, g); t.textContent = opt.xlab; }
    if (opt.ylab) { const t = PE.el("text", { x: 11, y: (m.t + H - m.b) / 2, "text-anchor": "middle", transform: `rotate(-90 11 ${(m.t + H - m.b) / 2})`, style: "font-size:11px;fill:#1F2933" }, g); t.textContent = opt.ylab; }
    return { x, y, W, H, m };
  },
  path(pts, x, y) { return pts.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1)).join(""); },
  // csúszka összekötése egy értékkijelzővel és egy frissítő függvénnyel
  bind(id, cb, fmt = v => v) { const e = document.getElementById(id), o = document.getElementById(id + "-v");
    const f = () => { if (o) o.textContent = fmt(+e.value); cb(); }; e.addEventListener("input", f); if (o) o.textContent = fmt(+e.value); return e; },
  v(id) { return +document.getElementById(id).value; },
  // színskála 0..1 → fehér..kék
  heat(t, c = [46, 109, 180]) { t = Math.max(0, Math.min(1, t)); const r = Math.round(255 + (c[0] - 255) * t), g = Math.round(255 + (c[1] - 255) * t), b = Math.round(255 + (c[2] - 255) * t); return `rgb(${r},${g},${b})`; },
};
