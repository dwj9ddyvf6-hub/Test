/* Master Desk terminal, market-context charts (owner, 2026-11-02: every engine and tool a graph of its trading data, never
   its internals). For each Market-tab panel this file writes one plain-words reading computed from the data and the chart
   that answers the panel's question, into a block right under the panel's heading. It reads only published files:
   edition.json (window.MD.ed), market.json, pulse.json and charts.json. A panel with no fresh data keeps its last chart
   with its age. Colours are the page's own (--up green, --dn red), so both themes read. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id);
if (!M) return;
const isN = v => typeof v === 'number' && isFinite(v), isA = Array.isArray, esc = M.esc || (s => String(s));
const f1 = v => (+v).toFixed(1), cl = (v, a, b) => Math.max(a, Math.min(b, v)), last = a => a[a.length - 1];
const pct = (v, d = 1) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d) + '%' : '—';
const sgn = (v, d = 1) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d) : '—';
const md = d => { try { return M.et(d).md; } catch (e) { return String(d).slice(5); } };
const MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
const mdd = d => { const s = String(d); return MON[+s.slice(5, 7) - 1] + ' ' + (+s.slice(8, 10)); };
const age = d => { const t = Date.parse(String(d).length === 10 ? d + 'T21:00:00Z' : d); if (!isN(t)) return ''; const h = (Date.now() - t) / 36e5;
  return h < 30 ? '' : 'last read ' + mdd(new Date(t).toISOString().slice(0, 10)); };
let mk = null, pul = null, ch = null, busy = 0;

// ---- primitives -------------------------------------------------------------------------------------------------------
const svg = (W, H, lab, g) => '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="' + esc(lab) + '">' + g + '</svg>';
const ln = (x1, y1, x2, y2, c) => '<line x1="' + f1(x1) + '" y1="' + f1(y1) + '" x2="' + f1(x2) + '" y2="' + f1(y2) + '" class="' + c + '"/>';
const tx = (x, y, t, c, a) => '<text x="' + f1(x) + '" y="' + f1(y) + '" class="' + (c || 'vz-ax') + '"' + (a ? ' text-anchor="' + a + '"' : '') + '>' + esc(t) + '</text>';
const rc = (x, y, w, h, c, rx) => '<rect x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(Math.max(0, w)) + '" height="' + f1(Math.max(0, h)) + '" class="' + c + '"' + (rx ? ' rx="' + rx + '"' : '') + '/>';
const card = (title, body, key) => '<div class="vzc">' + (title ? '<h3>' + title + '</h3>' : '') + body + (key ? '<p class="vzk">' + key + '</p>' : '') + '</div>';
const k = (c, t, dash) => '<span><i class="' + (dash ? 'd' : 'k-' + c) + '"></i>' + esc(t) + '</span>';
const nice = (lo, hi, n) => { const raw = (hi - lo) / n || 1, mag = Math.pow(10, Math.floor(Math.log10(raw))), st = [1, 2, 2.5, 5, 10].map(m => m * mag).find(q => q >= raw) || 10 * mag;
  const a = Math.floor(lo / st) * st, b = Math.ceil(hi / st) * st, t = []; for (let v = a; v <= b + st / 2; v += st) t.push(+v.toFixed(6)); return {lo: a, hi: b, t}; };

// a dated line chart: grid and labelled ticks at the right, three dates, an end dot and value per line, a reference line
function lines(W, H, d, S, o) {
  o = o || {};
  const L = 6, R = 56, T = 8, B = 22, n = d.length, vals = S.flatMap(s => s.v.filter(isN)).concat(isN(o.ref) ? [o.ref] : []);
  if (n < 2 || !vals.length) return '';
  const sc = nice(isN(o.lo) ? o.lo : Math.min(...vals), isN(o.hi) ? o.hi : Math.max(...vals), o.ticks || 4), fm = o.f || (v => String(v));
  const X = i => L + (W - L - R) * i / (n - 1), Y = v => T + (H - T - B) * (sc.hi - v) / (sc.hi - sc.lo || 1);
  let g = '';
  (o.bands || []).forEach(b => { const ya = Y(cl(b[0], sc.lo, sc.hi)), yb = Y(cl(b[1], sc.lo, sc.hi)); if (ya > yb) g += rc(L, yb, W - L - R, ya - yb, b[2]); });
  (o.shade || []).forEach(([i0, i1, c]) => { g += rc(X(i0) - 1, T, Math.max(2, X(i1) - X(i0) + 2), H - T - B, c); });
  sc.t.forEach(v => { g += ln(L, Y(v), W - R, Y(v), 'vz-gd') + tx(W - R + 6, Y(v) + 4, fm(v)); });
  if (isN(o.ref)) g += ln(L, Y(o.ref), W - R, Y(o.ref), 'vz-ref') + (o.refL ? tx(L + 4, Y(o.ref) - 4, o.refL) : '');
  const ends = [];
  S.forEach(s => {
    let p = '', on = 0;
    s.v.forEach((v, i) => { if (!isN(v)) { on = 0; return; } p += (on ? 'L' : 'M') + f1(X(i)) + ' ' + f1(Y(v)); on = 1; });
    g += '<path d="' + p + '" class="vz-ln ' + s.c + '"' + (s.dash ? ' stroke-dasharray="' + s.dash + '"' : '') + '/>';
    const lv = last(s.v);
    if (isN(lv)) { g += '<circle cx="' + f1(X(n - 1)) + '" cy="' + f1(Y(lv)) + '" r="3.4" class="' + s.c.replace('vz-s', 'vz-') + '"/>'; ends.push(Y(lv)); }
  });
  [0, Math.floor((n - 1) / 2), n - 1].forEach((i, j) => { g += tx(X(i), H - 6, mdd(d[i]), 'vz-ax', j ? j === 2 ? 'end' : 'middle' : 'start'); });
  return svg(W, H, o.label || '', g);
}
// columns a session each: one count up from the middle line, the other down from it, on one scale
function cols(W, dd) {
  const L = 6, R = 50, T = 8, B = 22, H = 170, n = dd.length, mx = Math.max(1, ...dd.map(x => Math.max(x.up4, x.dn4))), mid = T + (H - T - B) / 2, hh = (H - T - B) / 2, bw = (W - L - R) / n;
  let g = ln(L, mid, W - R, mid, 'vz-z') + tx(W - R + 6, T + 8, String(mx)) + tx(W - R + 6, mid + 4, '0') + tx(W - R + 6, H - B, String(mx));
  dd.forEach((x, i) => { const a = L + i * bw, w = Math.max(1, bw - 1.5); g += rc(a, mid - hh * x.up4 / mx, w, hh * x.up4 / mx, 'vz-up') + rc(a, mid, w, hh * x.dn4 / mx, 'vz-dn'); });
  [0, Math.floor((n - 1) / 2), n - 1].forEach((i, j) => { g += tx(L + (i + .5) * bw, H - 6, mdd(dd[i].d), 'vz-ax', j ? j === 2 ? 'end' : 'middle' : 'start'); });
  return svg(W, H, 'Stocks up and down 4% or more per session', g);
}
// a band gauge: the coloured bands, a needle at the reading, the value and the band's word on the right
function band(W, title, v, lo, hi, B, f) {
  if (!isN(v)) return '';
  const L = 4, R = 4, H = 34, X = x => L + (W - L - R) * (cl(x, lo, hi) - lo) / (hi - lo), cur = B.find(b => v >= b[0] && v < b[1]) || (v >= hi ? last(B) : B[0]);
  let g = '';
  B.forEach(b => { g += rc(X(b[0]), 6, X(b[1]) - X(b[0]), 12, b[3]) + tx((X(b[0]) + X(b[1])) / 2, 15.5, b[2], 'vz-bw', 'middle'); });
  g += '<path d="M' + f1(X(v) - 6) + ' 1h12l-6 8z" class="vz-nd"/>' + ln(X(v), 4, X(v), 20, 'vz-ndl') + tx(L, H - 2, f(lo)) + tx(W - R, H - 2, f(hi), 'vz-ax', 'end');
  return '<div class="vzb"><b>' + esc(title) + '</b><span class="' + cur[3].replace('vz-', 'vt-') + '">' + esc(f(v) + ' · ' + cur[2]) + '</span>' + svg(W, H, title + ' ' + f(v) + ', ' + cur[2], g) + '</div>';
}
// horizontal bars, a row each: the label at the left, the value at the right, zero (or a reference) marked
function hbars(W, rows, o) {
  o = o || {};
  const lw = Math.min(150, Math.max(70, W * .3)), vw = 64, rh = o.rh || 24, T = 4, H = rows.length * rh + T + (o.axis ? 18 : 4);
  const vs = rows.map(r => r.v).filter(isN), lo = isN(o.lo) ? o.lo : Math.min(0, ...vs), hi = isN(o.hi) ? o.hi : Math.max(0, ...vs);
  const x0 = lw + 6, x1 = W - vw, X = v => x0 + (x1 - x0) * (cl(v, lo, hi) - lo) / (hi - lo || 1), z = X(isN(o.ref) ? o.ref : cl(0, lo, hi));
  let g = '';
  rows.forEach((r, i) => {
    const y = T + i * rh;
    g += tx(lw, y + rh / 2 + 4, r.label, 'vz-lb', 'end');
    if (isN(r.v)) { const a = X(r.v); g += rc(Math.min(a, z), y + 4, Math.abs(a - z) || 1.5, rh - 9, r.c || (r.v >= (o.ref || 0) ? 'vz-up' : 'vz-dn'), 2); }
    else g += rc(x0, y + rh / 2 - 1, x1 - x0, 2, 'vz-mu');
    g += tx(W - 4, y + rh / 2 + 4, r.t, 'vz-axb', 'end');
  });
  g += ln(z, T, z, T + rows.length * rh, 'vz-z');
  if (o.axis) o.axis.forEach(v => { g += tx(X(v), H - 4, (o.af || String)(v), 'vz-ax', 'middle'); });
  return svg(W, H, o.label || '', g);
}
// dealer levels on a % from spot axis: the expected-move band, put wall, flip, call wall, spot at zero
function levels(W, rows, em) {
  const lw = 44, rh = 46, T = 6, H = rows.length * rh + T + 20, ext = Math.max(2, ...rows.flatMap(r => [r.put, r.call, r.flip].filter(isN).map(Math.abs)), isN(em) ? em * 1.4 : 0);
  const sc = nice(-ext * 1.08, ext * 1.08, 6), x0 = lw + 6, x1 = W - 10, X = v => x0 + (x1 - x0) * (v - sc.lo) / (sc.hi - sc.lo);
  let g = '';
  sc.t.forEach(v => { g += ln(X(v), T, X(v), T + rows.length * rh, 'vz-gd') + tx(X(v), H - 5, (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%', 'vz-ax', 'middle'); });
  rows.forEach((r, i) => {
    const y = T + i * rh, m = y + rh / 2;
    g += tx(lw, m + 4, r.sym, 'vz-axb', 'end');
    if (isN(em)) g += rc(X(-em), y + 8, X(em) - X(-em), rh - 16, 'vz-band', 3);
    if (isN(r.put) && isN(r.call)) g += ln(X(r.put), m, X(r.call), m, 'vz-gd');
    const mark = (v, c, lab, up) => isN(v) ? rc(X(v) - 3, m - 9, 6, 18, c, 1) + tx(X(v), up ? m - 12 : m + 21, lab, 'vz-ax', 'middle') : '';
    g += mark(r.put, 'vz-up', 'put ' + pct(r.put), 0) + mark(r.call, 'vz-dn', 'call ' + pct(r.call), 0);
    if (isN(r.flip)) g += '<path d="M' + f1(X(r.flip)) + ' ' + f1(m - 8) + 'l6 8-6 8-6-8z" class="vz-wn"/>' + tx(X(r.flip), m - 12, 'flip ' + pct(r.flip), 'vz-ax', 'middle');
    g += ln(X(0), y + 6, X(0), y + rh - 6, 'vz-spot');
  });
  return svg(W, H, 'Dealer levels as % from spot', g);
}

// ---- readings and charts per panel -------------------------------------------------------------------------------------
const P = {};
const fundsUp = () => pul && pul.lines ? Object.entries(pul.lines).map(([s, l]) => ({s, p: isA(l.c) && l.c.length && isN(l.prev) ? (last(l.c) / l.prev - 1) * 100 : null})).filter(x => isN(x.p)) : [];
P['m-live'] = () => {
  const f = fundsUp().sort((a, b) => a.p - b.p);
  if (!f.length) return null;
  const dn = f.filter(x => x.p < 0).length, word = dn === f.length ? 'Risk-off session' : dn === 0 ? 'Risk-on session' : 'Mixed session';
  return {h: word + ': ' + f.map(x => x.s + ' ' + pct(x.p, 1)).join(' · '), tone: dn === f.length ? 'd' : dn === 0 ? 'u' : 'w'};
};
const sectors = () => {                                  // the session's sector moves; before the open, the last session's
  const s = pul && isA(pul.sectors) && pul.sectors.length ? pul.sectors.map(x => ({n: x.name, v: x.pct})) : null;
  if (s) return {rows: s, when: ''};
  const h = mk && isA(mk.heat) ? mk.heat.filter(x => x.group === 'sector' && x.ret && isN(x.ret.d1)) : [];
  return h.length ? {rows: h.map(x => ({n: x.name, v: x.ret.d1})), when: mk.as_of} : null;
};
P['m-sect'] = W => {
  const s = sectors();
  if (!s) return null;
  const r = s.rows.slice().sort((a, b) => b.v - a.v), up = r.filter(x => x.v > 0).length;
  return {h: up + ' of ' + r.length + ' sectors up' + (s.when ? ' on ' + mdd(s.when) : '') + ': ' + r[0].n + ' ' + pct(r[0].v, 2) + ' leads, ' + last(r).n + ' ' + pct(last(r).v, 2) + ' lags',
    tone: up > r.length / 2 ? 'u' : up < r.length / 2 ? 'd' : 'w', age: s.when ? age(s.when) : '', force: !!s.when,
    c: s.when ? card('Sector funds · % change on ' + mdd(s.when), hbars(W, r.map(x => ({label: x.n, v: x.v, t: pct(x.v, 2)})), {label: 'Sector moves'})) : ''};
};
P['m-movers'] = W => {
  const m = pul && pul.movers, d = mk && mk.movers && isA(mk.movers.days) ? last(mk.movers.days) : null;
  if (!m || !(m.up.length || m.down.length)) return null;
  const rows = m.up.map(x => ({label: x.sym, v: x.pct, t: pct(x.pct, 1)})).concat(m.down.slice().reverse().map(x => ({label: x.sym, v: x.pct, t: pct(x.pct, 1)})));
  const h = d ? (d.dn4 > d.up4 * 2 ? 'Heavy selling: ' : d.up4 > d.dn4 * 2 ? 'Broad buying: ' : 'Two-way tape: ') + d.up4 + ' stocks rose 4%+ and ' + d.dn4 + ' fell 4%+ on ' + mdd(d.d)
    : 'Biggest moves on ' + mdd(m.as_of);
  const tone = d ? (d.dn4 > d.up4 ? 'd' : 'u') : 'w';
  let c = card('Biggest closes · % change', hbars(W, rows, {label: 'Biggest movers', rh: 22}));
  if (mk && mk.movers && isA(mk.movers.days) && mk.movers.days.length > 20) {
    const dd = mk.movers.days.slice(-60);
    c += card('Stocks up 4%+ (above) vs down 4%+ (below) · last 60 sessions', cols(W, dd), k('up', 'up 4% or more') + k('dn', 'down 4% or more'));
  }
  return {h, tone, c};
};
P['m-psy'] = W => {
  const m = M.ed && M.ed.mood;
  if (!m || !m.gauges) return null;
  const g = Object.keys(m.gauges).sort((a, b) => (+a.slice(1)) - (+b.slice(1))).map(k => m.gauges[k]);
  const rd = g.filter(x => isN(x.percentile) && x.state !== 'absent'), lo = rd.filter(x => x.percentile < 30), hi = rd.filter(x => x.percentile > 70);
  const cmp = isN(m.composite) ? m.composite : null, word = cmp === null ? (lo.length > hi.length ? 'Fear leaning' : hi.length > lo.length ? 'Greed leaning' : 'Mixed') : cmp < 30 ? 'Fear' : cmp > 70 ? 'Greed' : cmp < 45 ? 'Cautious' : cmp > 55 ? 'Confident' : 'Neutral';
  const h = 'Mood ' + word + (cmp !== null ? ' (' + f1(cmp) + '/100)' : '') + ': ' + (lo.length ? lo.map(x => x.name + ' ' + Math.round(x.percentile)).join(', ') + ' in fear' : 'no gauge in fear') +
    (hi.length ? '; ' + hi.map(x => x.name + ' ' + Math.round(x.percentile)).join(', ') + ' stretched high' : '');
  const rows = g.map(x => { const p = isN(x.percentile) && x.state !== 'absent' ? x.percentile : null; return {label: x.name, v: p, t: p === null ? '—' : String(Math.round(p)), c: p === null ? '' : p < 30 ? 'vz-dn' : p > 70 ? 'vz-up' : 'vz-wn'}; });
  return {h, tone: lo.length > hi.length ? 'd' : hi.length > lo.length ? 'u' : 'w',
    c: card('Each gauge as a percentile of its own history · 0 fear · 100 greed', hbars(W, rows, {lo: 0, hi: 100, ref: 50, axis: [0, 25, 50, 75, 100], label: 'Market mood gauges'}),
      k('dn', 'fear (under 30)') + k('wn', 'neutral') + k('up', 'greed (over 70)') + k('mu', 'no reading'))};
};
const cards = () => { const m = M.ed && M.ed.morgue && M.ed.morgue.map; return m && m.cards ? Object.entries(m.cards).filter(([, c]) => c && isN(c.spot)) : []; };
function ladder(W, c) {
  const r = (c.ladder || []).filter(x => isN(x.strike) && isN(x.net_gex_b)).sort((a, b) => a.strike - b.strike);
  if (r.length < 2) return '';
  const L = 6, R = 54, T = 12, B = 24, H = 210, mx = Math.max(...r.map(x => Math.abs(x.net_gex_b)), 1e-9), lo = r[0].strike, hi = last(r).strike;
  const X = s => L + (W - L - R) * (s - lo) / (hi - lo || 1), mid = T + (H - T - B) / 2, Y = v => mid - (H - T - B) / 2 * v / mx, bw = Math.max(2, (W - L - R) / r.length - 2);
  let g = ln(L, mid, W - R, mid, 'vz-z') + tx(W - R + 6, T + 8, '+' + mx.toFixed(2) + 'B') + tx(W - R + 6, mid + 4, '0') + tx(W - R + 6, H - B, '−' + mx.toFixed(2) + 'B');
  r.forEach(x => { const y = Y(x.net_gex_b); g += rc(X(x.strike) - bw / 2, Math.min(y, mid), bw, Math.abs(y - mid), x.net_gex_b >= 0 ? 'vz-up' : 'vz-dn', 1); });
  const tick = [lo, r[Math.floor(r.length / 2)].strike, hi];
  tick.forEach((s, j) => { g += tx(X(s), H - 6, String(s), 'vz-ax', j ? j === 2 ? 'end' : 'middle' : 'start'); });
  if (c.spot >= lo && c.spot <= hi) g += ln(X(c.spot), T, X(c.spot), H - B, 'vz-spot') + tx(X(c.spot) + 4, T + 2, 'spot ' + c.spot.toFixed(2), 'vz-axb');
  if (isN(c.flip) && c.flip >= lo && c.flip <= hi) g += ln(X(c.flip), T + 14, X(c.flip), H - B, 'vz-ref') + tx(X(c.flip) + 4, T + 16, 'flip ' + c.flip.toFixed(2));
  return svg(W, H, 'Net dealer gamma by strike', g);
}
P['m-ladder'] = W => {
  const cs = cards().filter(([, c]) => isA(c.ladder) && c.ladder.length >= 2);
  if (!cs.length) return null;
  const big = cs.map(([s, c]) => { const t = c.ladder.slice().sort((a, b) => Math.abs(b.net_gex_b) - Math.abs(a.net_gex_b))[0]; return {s, c, t}; });
  const neg = cs.filter(([, c]) => isN(c.net_gex_b) && c.net_gex_b < 0).length;
  const h = (neg === cs.length ? 'Dealers short gamma in all ' + cs.length + ': moves tend to run. ' : neg === 0 ? 'Dealers long gamma: moves tend to be damped. ' : 'Mixed dealer gamma. ') +
    big.map(b => b.s + ' biggest at ' + b.t.strike + ' (' + (b.t.strike >= b.c.spot ? 'above' : 'below') + ' spot)').join(' · ');
  return {h, tone: neg === cs.length ? 'd' : neg === 0 ? 'u' : 'w',
    c: '<div class="vzg c' + Math.min(3, cs.length) + '">' + cs.map(([s, c]) => card(esc(s) + ' · net gamma by strike, $B per 1% move', ladder(W / Math.min(3, cs.length) > 300 && innerWidth >= 900 ? Math.floor(W / Math.min(3, cs.length) - 14) : W, c))).join('') + '</div>' +
      '<p class="vzk">' + k('up', 'dealers long: damps moves') + k('dn', 'dealers short: speeds moves') + '</p>'};
};
function pinsSvg(W, c) {
  const p = (c.pins || []).filter(x => x.expiry).slice(0, 6), sp = c.spot;
  if (p.length < 2 || !isN(sp)) return '';
  const toP = v => isN(+v) && +v ? (+v / sp - 1) * 100 : null, rows = p.map(x => ({e: md(x.expiry), pin: toP(x.pin_strike), call: toP(x.call_strike), put: toP(x.put_strike), ps: x.pin_strike}));
  const vs = rows.flatMap(r => [r.pin, r.call, r.put]).filter(isN), ext = Math.min(20, Math.max(3, ...vs.map(Math.abs))), sc = nice(-ext, ext, 4);
  const L = 6, R = 50, T = 10, B = 22, H = 190, X = i => L + (W - L - R) * (i + .5) / rows.length, Y = v => T + (H - T - B) * (sc.hi - cl(v, sc.lo, sc.hi)) / (sc.hi - sc.lo);
  let g = '';
  sc.t.forEach(v => { g += ln(L, Y(v), W - R, Y(v), 'vz-gd') + (v ? tx(W - R + 6, Y(v) + 4, (v > 0 ? '+' : '−') + Math.abs(v) + '%') : ''); });
  g += ln(L, Y(0), W - R, Y(0), 'vz-spot') + tx(W - R + 6, Y(0) + 4, 'spot', 'vz-axb');
  rows.forEach((r, i) => {
    if (isN(r.put) && isN(r.call)) g += ln(X(i), Y(r.put), X(i), Y(r.call), 'vz-gd');
    if (isN(r.call)) g += rc(X(i) - 6, Y(r.call) - 1.5, 12, 3, 'vz-dn');
    if (isN(r.put)) g += rc(X(i) - 6, Y(r.put) - 1.5, 12, 3, 'vz-up');
    if (isN(r.pin)) g += '<circle cx="' + f1(X(i)) + '" cy="' + f1(Y(r.pin)) + '" r="6" class="vz-bl"/>' + tx(X(i), Y(r.pin) + (r.pin >= 0 ? -10 : 18), String(r.ps), 'vz-axb', 'middle');
    g += tx(X(i), H - 6, r.e, 'vz-ax', 'middle');
  });
  return svg(W, H, 'Expiry pins as % from spot', g);
}
P['m-pins'] = W => {
  const cs = cards().filter(([, c]) => isA(c.pins) && c.pins.length >= 2);
  if (!cs.length) return null;
  const h = 'Nearest expiry pulls ' + cs.map(([s, c]) => { const p = c.pins[0], d = isN(p.distance_pct) ? p.distance_pct : (p.pin_strike / c.spot - 1) * 100; return s + ' toward ' + p.pin_strike + ' (' + pct(d, 1) + ')'; }).join(' · ');
  const w = cs.length > 1 && innerWidth >= 900 ? Math.floor(W / Math.min(3, cs.length) - 14) : W;
  return {h, tone: 'w', c: '<div class="vzg c' + Math.min(3, cs.length) + '">' + cs.map(([s, c]) => card(esc(s) + ' · six nearest expiries', pinsSvg(w, c))).join('') + '</div>' +
    '<p class="vzk">' + k('bl', 'pin: strike with the most open interest') + k('up', 'largest put strike') + k('dn', 'largest call strike') + '</p>'};
};
const gexRows = () => { const G = M.ed && M.ed.strip && M.ed.strip.gex || {}; return Object.entries(G).filter(([, g]) => g && (g.status === 'ok' || g.status === 'stale'))
  .map(([s, g]) => ({sym: s, put: g.put_wall_pct, call: g.call_wall_pct, flip: g.flip_pct, net: g.net, word: g.word})); };
P['m-pos'] = W => {
  const r = gexRows(), mv = M.ed && M.ed.strip && M.ed.strip.move, em = mv && isN(mv.em_pct) ? mv.em_pct : null;
  if (!r.length) return null;
  const amp = r.filter(x => x.word === 'Amplifying').map(x => x.sym), damp = r.filter(x => x.word === 'Dampening').map(x => x.sym);
  const h = (amp.length === r.length ? 'Dealers short gamma in ' + amp.join(', ') + ': moves can run' : damp.length === r.length ? 'Dealers long gamma in ' + damp.join(', ') + ': moves get damped' :
    (amp.length ? amp.join(', ') + ' amplifying' : '') + (damp.length ? '; ' + damp.join(', ') + ' damped' : '')) + (em !== null ? '; expected move ±' + em.toFixed(2) + '% today' : '');
  return {h, tone: amp.length === r.length ? 'd' : damp.length === r.length ? 'u' : 'w', age: age(M.ed.strip.as_of),
    c: card('Where the dealer levels sit, % from spot', levels(W, r, em), k('up', 'put wall (support)') + k('dn', 'call wall (resistance)') + k('wn', 'gamma flip') + k('bl', 'expected move today'))};
};
P['f-map'] = W => {
  const cs = cards();
  if (!cs.length) return null;
  const r = cs.map(([s, c]) => ({sym: s, put: c.put_wall_pct, call: c.call_wall_pct, flip: c.flip_distance_pct, net: c.net_gex_b}));
  const mv = M.ed && M.ed.strip && M.ed.strip.move, em = mv && isN(mv.em_pct) ? mv.em_pct : null, neg = r.filter(x => isN(x.net) && x.net < 0).length;
  const spy = r.find(x => x.sym === 'SPY') || r[0];
  const h = (neg === r.length ? 'All ' + r.length + ' amplifying: ' : neg === 0 ? 'All damped: ' : '') + spy.sym + ' room ' + pct(spy.put, 1) + ' to the put wall, ' + pct(spy.call, 1) + ' to the call wall' +
    (isN(spy.flip) ? ', flip ' + pct(spy.flip, 1) : '');
  let c = card('Dealer levels, % from spot', levels(W, r, em), k('up', 'put wall') + k('dn', 'call wall') + k('wn', 'gamma flip') + k('bl', 'expected move'));
  const sq = mk && mk.squeeze && isA(mk.squeeze.days) ? mk.squeeze.days : null;
  if (sq && sq.length > 10) {
    const d = sq.map(x => x.d), dix = sq.map(x => x.dix * 100), gx = sq.map(x => x.gex_b), ld = last(dix), rank = Math.round(100 * dix.filter(v => v <= ld).length / dix.length);
    c += card('DIX · dark-pool buying, % of volume (SqueezeMetrics)', lines(W, 160, d, [{v: dix, c: 'vz-sbl'}], {f: v => v.toFixed(0) + '%', ref: 45, refL: '45% · heavy buying', label: 'DIX history'})) +
      card('SPX dealer gamma, $B per 1% move (SqueezeMetrics)', lines(W, 160, d, [{v: gx, c: 'vz-sin'}], {f: v => v.toFixed(0), ref: 0, refL: '0 · flip', label: 'GEX history'}));
    return {h: h + '. DIX ' + ld.toFixed(1) + '% (' + rank + 'th pct of 6 months), GEX ' + sgn(last(gx), 1) + 'B', tone: neg === r.length ? 'd' : 'w', c};
  }
  return {h, tone: neg === r.length ? 'd' : 'w', c};
};
P['market'] = W => {
  const pd = mk && mk.participation && isA(mk.participation.days) ? mk.participation.days.slice(-90) : null;
  if (!pd || pd.length < 10) return null;
  const a50 = pd.map(x => x.a50 * 100), a200 = pd.map(x => x.a200 * 100), now = last(a50), mo = a50[Math.max(0, a50.length - 22)];
  const h = Math.round(now) + '% of stocks above their 50-day, ' + (now < mo - 3 ? 'down from ' : now > mo + 3 ? 'up from ' : 'flat vs ') + Math.round(mo) + '% a month ago' +
    (now >= 60 ? ': broad participation' : now < 40 ? ': a narrow market' : now > mo + 3 ? ': breadth repairing, still near half' : now < mo - 3 ? ': breadth thinning' : ': middling breadth');
  return {h, tone: now < 40 ? 'd' : now > 60 ? 'u' : 'w', c: card('% of stocks above their 50-day and 200-day averages', lines(W, 180, pd.map(x => x.d), [{v: a50, c: 'vz-sbl'}, {v: a200, c: 'vz-sin', dash: '5 4'}],
    {lo: 0, hi: 100, ref: 50, refL: '50%', f: v => v + '%', label: 'Participation'}), k('bl', '50-day') + k('in', '200-day'))};
};
P['sectors'] = W => {
  const s = M.ed && M.ed.market && isA(M.ed.market.sectors) ? M.ed.market.sectors.filter(x => isN(x.pts)).slice().sort((a, b) => b.pts - a.pts) : [];
  if (!s.length) return null;
  const lead = s.slice(0, 3).map(x => x.name), lag = s.slice(-3).reverse().map(x => x.name);
  return {h: lead.join(', ') + ' lead; ' + lag.join(', ') + ' lag (20-session strength vs the S&P 500)', tone: 'w'};
};
P['m-vendor'] = () => {
  const v = M.ed && M.ed.vendor, t = v && v.emp && v.emp.today;
  if (!t || !isN(t.vix) || !isN(t.d1_pct)) return null;
  return {h: 'At VIX ' + t.vix.toFixed(1) + ' SPY usually moves ±' + t.d1_pct.toFixed(2) + '% a day and ±' + (isN(t.d5_pct) ? t.d5_pct.toFixed(2) : '—') + '% a week' +
    (isN(t.vix_em_pct) ? ' (the VIX formula says ±' + t.vix_em_pct.toFixed(2) + '% a day)' : ''), tone: 'w'};
};
P['m-idx'] = () => {
  const c = ch && ch.syms;
  if (!c) return null;
  const one = s => { const b = c[s]; if (!b || !isA(b.c) || b.c.length < 21) return null; const n = b.c.length, x = b.c[n - 1], m50 = isA(b.sma50) ? b.sma50[n - 1] : null, m200 = isA(b.sma200) ? b.sma200[n - 1] : null;
    return s + ' ' + x.toFixed(2) + (isN(m50) ? (x >= m50 ? ' above' : ' below') + ' its 50-day (' + pct((x / m50 - 1) * 100, 1) + ')' : '') + (isN(m200) ? ', ' + (x >= m200 ? 'above' : 'below') + ' its 200-day (' + pct((x / m200 - 1) * 100, 1) + ')' : ''); };
  const t = ['SPY', 'QQQ'].map(one).filter(Boolean);
  if (!t.length) return null;
  const b = c.SPY, dn = b && isA(b.sma50) && b.c[b.c.length - 1] < b.sma50[b.c.length - 1];
  return {h: t.join(' · '), tone: dn ? 'd' : 'u'};
};
P['m-mood'] = W => {
  const m = mk && mk.mood, vf = mk && mk.vixfam && isA(mk.vixfam.days) ? mk.vixfam.days : null;
  if (!m && !vf) return null;
  let h = '', tone = 'w', c = '';
  if (vf && vf.length > 10) {
    const d = vf.map(x => x.d), r = vf.map(x => x.vix / x.vix3m), lr = last(r), lv = last(vf), wk = vf[Math.max(0, vf.length - 6)];
    const bk = []; let a = -1; r.forEach((v, i) => { if (v >= 1 && a < 0) a = i; if ((v < 1 || i === r.length - 1) && a >= 0) { bk.push([a, v >= 1 ? i : i - 1, 'vz-bandd']); a = -1; } });
    h = (lr >= 1 ? 'VIX curve inverted: near-term fear above 3-month (' : 'VIX curve in contango: no panic (') + 'VIX ' + lv.vix.toFixed(1) + ' vs VIX3M ' + lv.vix3m.toFixed(1) + '), ' +
      (lv.vix > wk.vix + 1 ? 'up from ' : lv.vix < wk.vix - 1 ? 'down from ' : 'steady vs ') + wk.vix.toFixed(1) + ' a week ago';
    tone = lr >= 1 ? 'd' : lr > .95 ? 'w' : 'u';
    const bands = [
      ['Stress · VIX', lv.vix, 10, 40, [[10, 15, 'calm', 'vz-up'], [15, 20, 'normal', 'vz-bl'], [20, 30, 'elevated', 'vz-wn'], [30, 40, 'stressed', 'vz-dn']], v => v.toFixed(1)],
      ['Curve · VIX vs 3-month VIX', lr, .8, 1.2, [[.8, .95, 'upward-sloping', 'vz-up'], [.95, 1, 'flat', 'vz-wn'], [1, 1.2, 'inverted', 'vz-dn']], v => v.toFixed(2)],
      ['Volatility of volatility · VVIX', lv.vvix, 70, 140, [[70, 85, 'quiet', 'vz-up'], [85, 110, 'normal', 'vz-bl'], [110, 125, 'elevated', 'vz-wn'], [125, 140, 'jumpy', 'vz-dn']], v => v.toFixed(0)],
      ['Tail-risk pricing · SKEW', lv.skew, 100, 170, [[100, 130, 'low', 'vz-up'], [130, 145, 'normal', 'vz-bl'], [145, 170, 'high', 'vz-dn']], v => v.toFixed(0)]];
    c = card('Stress dashboard', bands.map(([t, v, lo, hi, B, f]) => band(W, t, v, lo, hi, B, f)).join('')) +
      card('VIX vs 3-month VIX · shaded red where the curve inverted', lines(W, 190, d, [{v: vf.map(x => x.vix), c: 'vz-sdn'}, {v: vf.map(x => x.vix3m), c: 'vz-sbl', dash: '5 4'}], {f: v => String(v), shade: bk, label: 'VIX term structure'}), k('dn', 'VIX (30-day)') + k('bl', 'VIX3M (3-month)')) +
      '<div class="vzg c2">' + card('VVIX · volatility of the VIX', lines(W > 700 && innerWidth >= 900 ? Math.floor(W / 2 - 14) : W, 140, d, [{v: vf.map(x => x.vvix), c: 'vz-sin'}], {f: v => String(v), ref: 100, refL: '100', label: 'VVIX'})) +
      card('SKEW · demand for crash protection', lines(W > 700 && innerWidth >= 900 ? Math.floor(W / 2 - 14) : W, 140, d, [{v: vf.map(x => x.skew), c: 'vz-swn'}], {f: v => String(v), ref: 145, refL: '145 · rich tails', label: 'SKEW'})) + '</div>';
  } else if (m && isN(m.score)) h = 'Mood Ring ' + m.score.toFixed(0) + ': ' + m.word;
  return {h, tone, age: vf && vf.length ? age(last(vf).d) : m ? age(m.as_of) : '', c};
};
P['m-pulse'] = () => {
  const f = mk && mk.pulse && isA(mk.pulse.funds) ? mk.pulse.funds : [];
  if (!f.length) return null;
  const st = f.map(x => x.state), same = st.every(s => s === st[0]);
  return {h: (same ? 'Pulse ' + st[0] + ' on ' + f.map(x => x.sym).join(' and ') : f.map(x => x.sym + ' ' + x.state).join(' · ')) + ' (' + f.map(x => x.score + '/5').join(', ') + ')' +
    (isN(f[0].ram) ? '; risk ' + Math.round(f[0].ram) + '/100, ' + String(f[0].ram_level || '').toLowerCase() : ''), tone: /RED|PURPLE/.test(st[0]) ? 'd' : /GREEN|BLUE/.test(st[0]) ? 'u' : 'w'};
};
P['m-breadth'] = () => {
  const b = mk && mk.breadth;
  if (!b || !isN(b.score)) return null;
  return {h: 'Breadth ' + b.score + ' of ' + b.of + ': ' + b.adv + ' advanced vs ' + b.dec + ' declined; ' + b.up4 + ' up 4%+ vs ' + b.dn4 + ' down 4%+', tone: b.dec > b.adv ? 'd' : 'u'};
};
P['m-risk'] = () => {
  const r = mk && mk.risk;
  if (!r || !isN(r.on)) return null;
  const off = (r.pairs || []).filter(p => !p.on).map(p => p.pair);
  return {h: r.on + ' of ' + r.of + ' risk ratios lean risk-on' + (r.on <= r.of / 3 ? ': defensive tape' : r.on >= r.of * 2 / 3 ? ': risk appetite strong' : '') + (off.length && off.length < r.of ? ' (off: ' + off.join(', ') + ')' : ''),
    tone: r.on <= r.of / 3 ? 'd' : r.on >= r.of * 2 / 3 ? 'u' : 'w'};
};
P['m-heat'] = () => {
  const h = mk && isA(mk.heat) ? mk.heat.filter(x => x.group === 'theme' && x.ret && isN(x.ret.m1)).sort((a, b) => b.ret.m1 - a.ret.m1) : [];
  if (h.length < 4) return null;
  return {h: 'One month: ' + h.slice(0, 3).map(x => x.name + ' ' + pct(x.ret.m1, 1)).join(', ') + ' lead; ' + h.slice(-2).reverse().map(x => x.name + ' ' + pct(x.ret.m1, 1)).join(', ') + ' lag', tone: 'w'};
};
P['m-rot'] = W => {
  const f = mk && mk.rotation && isA(mk.rotation.funds) ? mk.rotation.funds.filter(x => x.group === 'sector') : [];
  if (!f.length) return null;
  const q = n => f.filter(x => x.quad === n).map(x => x.name);
  const L = q('Leading'), G = q('Lagging');
  return {h: (L.length ? 'Leading: ' + L.slice(0, 4).join(', ') : 'No sector leading') + (G.length ? ' · Lagging: ' + G.slice(0, 4).join(', ') : ''), tone: 'w',
    c: W < 600 ? card('Sectors vs SPY · strength (across) and momentum (up)', quad(W, f), k('up', 'Leading') + k('bl', 'Improving') + k('wn', 'Weakening') + k('dn', 'Lagging')) : ''};
};
function quad(W, f) {
  const H = Math.round(W * .9), L = 8, R = 8, T = 8, B = 20, xs = f.map(x => x.ratio), ys = f.map(x => x.mom);
  const ex = Math.max(1.5, ...xs.map(v => Math.abs(v - 100))) * 1.15, ey = Math.max(1.5, ...ys.map(v => Math.abs(v - 100))) * 1.15;
  const X = v => L + (W - L - R) * (v - 100 + ex) / (2 * ex), Y = v => T + (H - T - B) * (100 + ey - v) / (2 * ey), QC = {Leading: 'vz-up', Improving: 'vz-bl', Weakening: 'vz-wn', Lagging: 'vz-dn'};
  let g = ln(X(100), T, X(100), H - B, 'vz-z') + ln(L, Y(100), W - R, Y(100), 'vz-z') + tx(W - R - 2, T + 12, 'Leading', 'vz-ax', 'end') + tx(L + 2, T + 12, 'Improving') +
    tx(W - R - 2, H - B - 6, 'Weakening', 'vz-ax', 'end') + tx(L + 2, H - B - 6, 'Lagging') + tx(W / 2, H - 4, 'weaker ← relative strength → stronger', 'vz-ax', 'middle');
  f.forEach(x => { g += '<circle cx="' + f1(X(x.ratio)) + '" cy="' + f1(Y(x.mom)) + '" r="5" class="' + (QC[x.quad] || 'vz-mu') + '"/>' + tx(X(x.ratio) + 7, Y(x.mom) + 4, x.sym, 'vz-axb'); });
  return svg(W, H, 'Sector rotation quadrants', g);
};
const AREA = Object.keys(P);

// ---- placement: one block under each panel's heading; redrawn when its data or width changes -----------------------------
let q = 0, w0 = 0;
function place() {
  q = 0;
  const host = el('p-market') || D.body, W = Math.max(300, Math.min(1100, Math.round((host.clientWidth || innerWidth) - 40)));
  AREA.forEach(id => {
    const s = el(id);
    if (!s) return;
    let r = null;
    try { r = P[id](W); } catch (e) { r = null; }
    let b = s.querySelector(':scope > .vz');
    if (!r || !r.h) { if (b) b.remove(); return; }
    if (r.force) s.setAttribute('data-vz-last', ''); else s.removeAttribute('data-vz-last');
    if (r.force) s.querySelectorAll(':scope > .vsw, :scope > .shd > .vsc, :scope > .vsl').forEach(x => x.remove());
    if (r.force && s.hidden && !s.querySelector('.shd')) {                    // a panel with no session data yet: its last session
      s.innerHTML = '<div class="shd"><div class="sht"><h2 id="h-' + id + '">' + (id === 'm-sect' ? 'Sectors today' : '') + '</h2></div></div>';
      s.hidden = false;
    }
    const h = '<p class="vzh vz-' + (r.tone || 'w') + '">' + esc(r.h) + (r.age ? '<span class="vzage">' + esc(r.age) + '</span>' : '') + '</p>' + (r.c || '');
    if (b && b._h === h) return;
    if (!b) { b = D.createElement('div'); b.className = 'vz'; const hd = s.querySelector(':scope > .shd, :scope > h2, :scope > header'); hd ? hd.after(b) : s.prepend(b); }
    b.innerHTML = h; b._h = h;
  });
  w0 = W;
}
const soon = () => { if (!q) q = requestAnimationFrame(place); };
const getJ = u => fetch(u, {cache: 'no-cache'}).then(r => r.ok ? r.json() : null).catch(() => null);
function load() {
  if (busy) return;
  busy = 1;
  Promise.all([getJ('market.json'), getJ('pulse.json'), window.MDV && window.MDV.charts ? Promise.resolve(window.MDV.charts()).catch(() => null) : getJ('charts.json')]).then(([m, p, c]) => {
    busy = 0;
    if (m && m.v === 1) mk = m;
    if (p) pul = p;
    if (c && c.syms) ch = c;
    soon();
  });
}
const grid = el('grid') || D.body;
new MutationObserver(ms => { if (ms.some(m => !(m.target.closest && m.target.closest('.vz')))) soon(); }).observe(grid, {childList: true, subtree: true});
D.addEventListener('md:edition', () => { load(); soon(); });
addEventListener('resize', () => { const host = el('p-market'); if (host && Math.abs(host.clientWidth - 40 - w0) > 24) soon(); });
window.MDVM = {readings: () => AREA.map(id => { try { const r = P[id](800); return [id, r && r.h]; } catch (e) { return [id, null]; } }), refresh: load};
load();
})();
