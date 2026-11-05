/* gk: the galath chart forms (owner, 2026-11-03: "styled like galath-desk-terminal"): a dark chart card inside the
   light page, segmented gauges with a needle, a big number and a status pill, weighted component bars, donuts and a
   session column strip. Every primitive returns an HTML string; every mark carries a <title> for hover. */
(function () {
  'use strict';
  const C = {u: '#7ee0c3', d: '#ff8a80', y: '#f2d68a', p: '#b9a7f0', b: '#7fb2ff', n: '#6f7690', t: '#5ad1e8'};
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const isN = v => typeof v === 'number' && isFinite(v), r1 = v => (+v).toFixed(1);
  const width = () => { const m = document.getElementById('main'); return Math.max(280, Math.min(1100, Math.round(((m && m.clientWidth) || 360) - 70))); };
  const svg = (W, H, label, body) => '<svg class="gk-s" data-viz viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + esc(label) + '">' + body + '</svg>';
  const tx = (x, y, s, o = {}) => '<text x="' + r1(x) + '" y="' + r1(y) + '"' + (o.a ? ' text-anchor="' + o.a + '"' : '') + ' class="' + (o.c || 'gk-ax') + '">' + esc(s) + '</text>';
  const tip = s => '<title>' + esc(s) + '</title>';
  // the dark card: a mint caps title, a quiet meta line on the right
  function card(title, meta, body) {
    return '<div class="gk"><div class="gk-h"><b>' + esc(title) + '</b>' + (meta ? '<span>' + esc(meta) + '</span>' : '') + '</div>' + body + '</div>';
  }
  const pill = (word, c) => '<span class="gk-pill gk-' + (C[c] ? c : 'n') + '">' + esc(word) + '</span>';
  // horizontal bars, one row per item: label left, value right; o.log draws log10(1+v) lengths (funnels spanning decades)
  function bars(rows, o = {}) {
    rows = rows.filter(r => isN(r.v));
    if (!rows.length) return '';
    const W = o.W || width(), L = Math.min(Math.round(W * 0.45), 16 + 7.4 * Math.max(...rows.map(r => String(r.k).length))), R = 86, rh = 26, H = rows.length * rh + 6;
    const len = v => o.log ? Math.log10(1 + Math.abs(v)) : Math.abs(v), mx = Math.max(...rows.map(r => len(r.v)), 1e-9);
    const neg = rows.some(r => r.v < 0), span = (W - L - R) / (neg ? 2 : 1), z = L + (neg ? span : 0);
    return svg(W, H, o.label || 'bars', rows.map((r, i) => {
      const w = len(r.v) / mx * span, y = 4 + i * rh, c = C[r.c] || r.c || (r.v < 0 ? C.d : C.u);
      return '<rect x="' + L + '" y="' + (y + 4) + '" width="' + (W - L - R) + '" height="12" rx="6" class="gk-tr"/>' +
        '<rect x="' + r1(r.v < 0 ? z - w : z) + '" y="' + (y + 4) + '" width="' + r1(Math.max(3, w)) + '" height="12" rx="6" fill="' + c + '">' + tip(r.k + ': ' + (r.t != null ? r.t : r.v)) + '</rect>' +
        tx(4, y + 14, r.k, {c: 'gk-lb'}) + tx(W - 4, y + 14, r.t != null ? r.t : String(r.v), {a: 'end', c: 'gk-v'});
    }).join('') + (neg ? '<line x1="' + z + '" x2="' + z + '" y1="0" y2="' + H + '" class="gk-z"/>' : ''));
  }
  // the segmented gauge: coloured arc zones, a needle at the value, the big number and a status pill under it
  function gauge(o) {
    const W = 260, H = 172, cx = 130, cy = 132, R = 100, lo = o.min, hi = o.max;
    if (!isN(o.value) || !(hi > lo)) return '';
    const a = v => Math.PI * (1 - (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo));
    const pt = (v, r) => [cx + r * Math.cos(a(v)), cy - r * Math.sin(a(v))];
    const arc = (v0, v1, col, word) => { const p = pt(v0, R), q = pt(v1, R);
      return '<path d="M' + r1(p[0]) + ' ' + r1(p[1]) + ' A' + R + ' ' + R + ' 0 0 1 ' + r1(q[0]) + ' ' + r1(q[1]) + '" stroke="' + (C[col] || col) + '" stroke-width="22" fill="none">' + tip(word + ': ' + v0 + ' to ' + v1) + '</path>'; };
    const n = pt(o.value, R - 18), z = o.zones.find(z => o.value >= z[0] && o.value <= z[1]) || o.zones[o.zones.length - 1];
    return '<div class="gk-g">' + svg(W, H, o.label || 'gauge', o.zones.map(z => arc(z[0], z[1], z[2], z[3])).join('') +
      '<line x1="' + cx + '" y1="' + cy + '" x2="' + r1(n[0]) + '" y2="' + r1(n[1]) + '" class="gk-nd"/><circle cx="' + cx + '" cy="' + cy + '" r="6" fill="#f4f7fc"/>' +
      tx(cx, cy + 34, o.text != null ? o.text : String(o.value), {a: 'middle', c: 'gk-big'})) + '<p>' + pill(z[3], z[2]) + (o.sub ? ' <span>' + esc(o.sub) + '</span>' : '') + '</p></div>';
  }
  // a donut of shares with the total in the middle and a legend beside it
  function donut(parts, centre, sub, label) {
    parts = parts.filter(p => p.v > 0);
    if (parts.length === 1) parts = [Object.assign({}, parts[0], {v: parts[0].v / 2}), Object.assign({}, parts[0], {v: parts[0].v / 2, half: 1})];
    const T = parts.reduce((s, p) => s + p.v, 0);
    if (!T) return '';
    let a0 = -Math.PI / 2, b = '';
    parts.forEach(p => { const a1 = a0 + p.v / T * Math.PI * 2 - 0.02, big = a1 - a0 > Math.PI ? 1 : 0;
      const P = (a, r) => r1(80 + r * Math.cos(a)) + ' ' + r1(80 + r * Math.sin(a));
      b += '<path d="M' + P(a0, 70) + ' A70 70 0 ' + big + ' 1 ' + P(a1, 70) + ' L' + P(a1, 46) + ' A46 46 0 ' + big + ' 0 ' + P(a0, 46) + 'Z" fill="' + p.c + '">' + tip(p.k + ': ' + (p.half ? p.v * 2 : p.v) + ' (' + Math.round(p.v / T * 100) * (p.half ? 2 : 1) + '%)') + '</path>';
      a0 = a1 + 0.02; });
    return '<div class="gk-dn">' + svg(160, 160, label || 'donut', b + tx(80, 84, centre, {a: 'middle', c: 'gk-big gk-mid'}) + tx(80, 102, sub || '', {a: 'middle'})) +
      '<ul>' + parts.filter(p => !p.half).map(p => '<li><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="5" fill="' + p.c + '"/></svg>' + esc(p.k) + '<b>' + (parts.length === 2 && parts[1].half ? p.v * 2 : p.v).toLocaleString('en-US') + '</b></li>').join('') + '</ul></div>';
  }
  // a column per session: height is the hours the exchange trades, dots above it are the scheduled releases
  function sessions(days, label) {
    if (!days.length) return '';
    const W = width(), H = 150, base = 112, cw = (W - 8) / days.length, top = 34;
    return svg(W, H, label || 'sessions', days.map((d, i) => {
      const x = 4 + i * cw, h = d.hours / 6.5 * (base - top), c = d.hours >= 6.5 ? C.u : d.hours > 0 ? C.y : C.n;
      return '<rect x="' + r1(x + cw * 0.18) + '" y="' + r1(base - Math.max(3, h)) + '" width="' + r1(cw * 0.64) + '" height="' + r1(Math.max(3, h)) + '" rx="5" fill="' + c + '">' + tip(d.day + ' ' + d.md + ': ' + d.word) + '</rect>' +
        d.ev.map((e, j) => '<circle cx="' + r1(x + cw / 2) + '" cy="' + (top - 10 - j * 11) + '" r="4.5" fill="' + C.p + '">' + tip(e) + '</circle>').join('') +
        tx(x + cw / 2, base + 16, d.day, {a: 'middle', c: 'gk-lb'}) + tx(x + cw / 2, base + 31, cw < 64 ? String(d.md).split(' ').pop() : d.md, {a: 'middle'});
    }).join(''));
  }
  // a compact share strip (the ticker's tone): one rounded bar split by share
  function strip(parts, label, W = 140) {
    const T = parts.reduce((s, p) => s + p.v, 0);
    if (!T) return '';
    let x = 0;
    return '<svg class="gk-st" data-viz viewBox="0 0 ' + W + ' 14" width="' + W + '" height="14" role="img" aria-label="' + esc(label) + '"><rect width="' + W + '" height="14" rx="7" class="gk-tr"/>' +
      parts.map(p => { const w = p.v / T * W, s = '<rect x="' + r1(x) + '" width="' + r1(w) + '" height="14" fill="' + p.c + '">' + tip(p.k + ': ' + p.v) + '</rect>'; x += w; return s; }).join('') + '</svg>';
  }
  // Look up: the whole roster's current take, as a donut, drawn once the section is near the screen
  function lookViz() {
    const host = document.getElementById('lviz'), sec = document.getElementById('look');
    if (!host || !sec || host.dataset.on) return;
    host.dataset.on = '1';
    const draw = () => fetch('reads-index.json', {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(j => {
      const n = {}, names = j && j.names || {};
      Object.keys(names).forEach(k => { const a = (names[k] || [])[0] || 'Other', t = a === 'Buy' ? 'Buy now' : a; n[t] = (n[t] || 0) + 1; });
      const order = Object.keys(n).sort((a, b) => n[b] - n[a]), pal = [C.u, C.b, C.y, C.p, C.t, C.d, C.n];
      const parts = order.slice(0, 6).map((k, i) => ({k, v: n[k], c: pal[i]}));
      const rest = order.slice(6).reduce((s, k) => s + n[k], 0);
      if (rest) parts.push({k: 'Other takes', v: rest, c: C.n});
      const nr = Object.keys(names).length;   // T-158: the names with a read, of the roster's count
      host.innerHTML = card('The roster today', 'as of ' + (j.as_of || '') + (j.roster ? ' · ' + nr.toLocaleString('en-US') + ' of ' + j.roster.toLocaleString('en-US') + ' roster names on record' : ''), donut(parts, nr.toLocaleString('en-US'), 'stocks read', 'The desk\u2019s take across the roster'));
    }).catch(() => { host.dataset.on = ''; });
    if ('IntersectionObserver' in window) { const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); draw(); } }, {rootMargin: '400px'}); io.observe(sec); } else draw();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', lookViz); else lookViz();
  window.GK = {width, C, card, pill, bars, gauge, donut, sessions, strip, esc};
})();
