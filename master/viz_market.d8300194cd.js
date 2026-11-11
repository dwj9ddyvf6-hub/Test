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
const sgn = (v, d = 1) => { if (!isN(v)) return '—'; const a = Math.abs(v).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: false}); return (+a === 0 ? '' : v > 0 ? '+' : '−') + a; };   // no −0.0
const pct = (v, d = 1) => isN(v) ? sgn(v, d) + '%' : '—';
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
  const sc = nice(isN(o.lo) ? o.lo : Math.min(...vals), isN(o.hi) ? o.hi : Math.max(...vals), o.ticks || 4), f0 = o.f || (v => String(v)), fm = v => String(f0(v)).replace(/^-/, '−');   // T-242: a negative tick takes the minus sign, never a hyphen
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
  const st = W < 480 && rows.some(r => String(r.label).length > 12);    // phone width: each label on its own line above its bar
  const lw = st ? 0 : Math.min(150, Math.max(70, W * .3)), vw = 64, rh = st ? 36 : (o.rh || 24), T = 4, H = rows.length * rh + T + (o.axis ? 18 : 4);
  const vs = rows.map(r => r.v).filter(isN), lo = isN(o.lo) ? o.lo : Math.min(0, ...vs), hi = isN(o.hi) ? o.hi : Math.max(0, ...vs);
  const x0 = lw + 6, x1 = W - vw, X = v => x0 + (x1 - x0) * (cl(v, lo, hi) - lo) / (hi - lo || 1), z = X(isN(o.ref) ? o.ref : cl(0, lo, hi));
  let g = '';
  rows.forEach((r, i) => {
    const y = T + i * rh;
    const by = st ? y + 16 : y + 4, bh = st ? 14 : rh - 9;
    g += st ? tx(0, y + 11, r.label, 'vz-lb') : tx(lw, y + rh / 2 + 4, r.label, 'vz-lb', 'end');
    if (isN(r.v)) { const a = X(r.v); g += rc(Math.min(a, z), by, Math.abs(a - z) || 1.5, bh, r.c || (r.v >= (o.ref || 0) ? 'vz-up' : 'vz-dn'), 2); }
    else g += rc(x0, by + bh / 2 - 1, x1 - x0, 2, 'vz-mu');
    g += tx(W - 4, by + bh / 2 + 4, r.t, 'vz-axb', 'end');
  });
  g += ln(z, T, z, T + rows.length * rh, 'vz-z');
  if (o.axis) o.axis.forEach(v => { g += tx(X(v), H - 4, (o.af || String)(v), 'vz-ax', 'middle'); });
  return svg(W, H, o.label || '', g);
}
// dealer levels on a % from spot axis: the expected-move band, put wall, flip, call wall, spot at zero
function levels(W, rows, em) {
  const lw = 44, rh = 56, T = 14, H = rows.length * rh + T + 20, ext = Math.max(2, ...rows.flatMap(r => [r.put, r.call, r.flip].filter(isN).map(Math.abs)), isN(em) ? em * 1.4 : 0);
  const sc = nice(-ext * 1.08, ext * 1.08, 6), x0 = lw + 6, x1 = W - 10, X = v => x0 + (x1 - x0) * (v - sc.lo) / (sc.hi - sc.lo);
  let g = '';
  sc.t.forEach(v => { g += ln(X(v), T, X(v), T + rows.length * rh, 'vz-gd') + tx(X(v), H - 5, (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%', 'vz-ax', 'middle'); });
  rows.forEach((r, i) => {
    const y = T + i * rh, m = y + rh / 2;
    g += tx(lw, m + 4, r.sym, 'vz-axb', 'end');
    if (isN(em)) g += rc(X(-em), y + 8, X(em) - X(-em), rh - 16, 'vz-band', 3);
    if (isN(r.put) && isN(r.call)) g += ln(X(r.put), m, X(r.call), m, 'vz-gd');
    // labels never overlap (audit 5 M19: "flip +0.3%" on "call +0.3%"; the spot line through "call +0.1%"): a wall
    // within NEAR px of the flip shares the flip's label, and the spot line stops short of the label rows
    const NEAR = 64, near = v => isN(v) && isN(r.flip) && Math.abs(X(v) - X(r.flip)) < NEAR;
    const mark = (v, c, lab) => isN(v) ? rc(X(v) - 3, m - 9, 6, 18, c, 1) + (near(v) ? '' : tx(X(v), m + 21, lab, 'vz-ax', 'middle')) : '';
    g += ln(X(0), m - 9, X(0), m + 9, 'vz-spot');
    g += mark(r.put, 'vz-up', 'put ' + pct(r.put)) + mark(r.call, 'vz-dn', 'call ' + pct(r.call));
    if (isN(r.put) && isN(r.call) && !near(r.put) && !near(r.call) && Math.abs(X(r.call) - X(r.put)) < NEAR)
      g = g.replace(tx(X(r.call), m + 21, 'call ' + pct(r.call), 'vz-ax', 'middle'), tx(X(r.call), m + 33, 'call ' + pct(r.call), 'vz-ax', 'middle'));
    if (isN(r.flip)) g += '<path d="M' + f1(X(r.flip)) + ' ' + f1(m - 8) + 'l6 8-6 8-6-8z" class="vz-wn"/>' +
      tx(X(r.flip), m - 12, ['flip ' + pct(r.flip)].concat(near(r.put) ? ['put ' + pct(r.put)] : [], near(r.call) ? ['call ' + pct(r.call)] : []).join(' · '), 'vz-ax', 'middle');
  });
  return svg(W, H, 'Dealer levels as % from spot', g);
}

// ---- readings and charts per panel -------------------------------------------------------------------------------------
const P = {};
const fundsUp = () => pul && pul.lines ? Object.entries(pul.lines).map(([s, l]) => ({s, p: isA(l.c) && l.c.length && isN(l.prev) ? (last(l.c) / l.prev - 1) * 100 : null})).filter(x => isN(x.p)) : [];
P['m-live'] = () => {
  const f = fundsUp().sort((a, b) => a.p - b.p);
  if (!f.length) return null;
  // a move that prints as 0.0 is flat, not up: the word follows the numbers the reader sees
  const up = f.filter(x => x.p >= .05).length, dn = f.filter(x => x.p <= -.05).length;
  const word = !up && dn ? 'Risk-off session' : !dn && up ? 'Risk-on session' : !up && !dn ? 'Flat session' : 'Mixed session';
  return {h: word + ': ' + f.map(x => x.s + ' ' + pct(x.p, 1)).join(' · '), tone: !up && dn ? 'd' : !dn && up ? 'u' : 'w'};
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
  const m = pul && pul.movers, d = m && mk && mk.movers && isA(mk.movers.days) ? mk.movers.days.find(x => x.d === m.as_of) || null : null;   // the movers' own session, never a later forming day
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
  const g = Object.keys(m.gauges).sort((a, b) => (+a.slice(1)) - (+b.slice(1))).map(k => Object.assign({key: k}, m.gauges[k]));
  const rd = g.filter(x => isN(x.percentile) && x.state !== 'absent'), lo = rd.filter(x => x.percentile < 30), hi = rd.filter(x => x.percentile > 70);
  // the engine's own regime is the headline's word, so the headline and the card agree (audit 2026-11-04: "Mood Cautious"
  // above "Contested: Fearful")
  const cmp = isN(m.composite) ? m.composite : null, word = typeof m.regime === 'string' && m.regime ? m.regime : cmp === null ? (lo.length > hi.length ? 'Fear leaning' : hi.length > lo.length ? 'Greed leaning' : 'Mixed') : cmp < 30 ? 'Fear' : cmp > 70 ? 'Greed' : cmp < 45 ? 'Cautious' : cmp > 55 ? 'Confident' : 'Neutral';
  // a score names exactly the gauges its median takes (core_used), and Leverage and Fragility only as the overlay its
  // words come from (T-054/T-131, live 11-06: "(15.6/100): … Crypto Mood Overnight 27 in fear; Leverage and Fragility 92",
  // neither in the score, Where Money Sits 50 omitted)
  const nm = x => x.name + ' ' + Math.round(x.percentile), cu = rd.filter(x => (m.core_used || []).includes(x.key)).sort((a, b) => a.percentile - b.percentile), g4 = rd.find(x => x.key === 'G4');
  let ov;
  const h = cmp !== null && cu.length ? 'Mood ' + word + ' (' + f1(cmp) + '/100, the median of ' + cu.map(nm).join(', ') + ')' + (g4 && (ov = /(Complacent fragility|fragile|forced flow active)$/.exec(word)) ? '; ' + nm(g4) + ' adds “' + ov[1] + '”' : '') :
    'Mood ' + word + ': ' + (lo.length ? lo.map(nm).join(', ') + ' in fear' : 'no gauge in fear') + (hi.length ? '; ' + hi.map(nm).join(', ') + ' stretched high' : '');
  const rows = psyRows(g, m.as_of, m.core_used);
  return {h, tone: lo.length > hi.length ? 'd' : hi.length > lo.length ? 'u' : 'w',
    c: card('Each gauge as a percentile of its own history · 0 fear · 100 greed', hbars(W, rows, {lo: 0, hi: 100, ref: 50, axis: [0, 25, 50, 75, 100], label: 'Market mood gauges'}),
      k('dn', 'fear (under 30)') + k('wn', 'neutral') + k('up', 'greed (over 70)') + k('mu', 'not in the score: stale (dated) or unranked (raw reading, off the axis); dropped after ' + PSY_MAX_DAYS + ' days'))};
};
// a row per gauge with a value: ranked ones by their percentile, unranked ones at their latest reading in a muted tone with
// its date; a gauge with no value at all (or event odds, which are no mood score) is left out, never drawn empty
// an unranked or stale reading never weighs in silently (audit 2026-11-04: "What People Say 30 · Jul 29" beside a 34.1
// score it was not part of): it is labelled "not scored", and past PSY_MAX_DAYS before the mood's as_of it is dropped
const PSY_MAX_DAYS = 45;
function psyRows(g, asOf, core) {
  const ref = Date.parse(String(asOf || '').slice(0, 10) + 'T12:00:00Z');
  const old = x => x.as_of && isFinite(ref) && (ref - Date.parse(String(x.as_of).slice(0, 10) + 'T12:00:00Z')) / 864e5 > PSY_MAX_DAYS;
  // a gauge past its allowed age (state stale, the edition's freshness contract) is never dropped and never reads as
  // current: its row says stale and not current in plain words, off the axis when it has no percentile (p2b 2026-11-05)
  const st = x => x.state === 'stale' ? ' · stale since ' + (x.as_of ? mdd(x.as_of) : 'unknown') + ', not current' : '';
  return g.filter(x => x && x.state !== 'absent').map(x => {
    if (x.state === 'stale') return isN(x.percentile) ? {label: x.name, v: x.percentile, t: Math.round(x.percentile) + st(x), c: 'vz-mu'}
      : isN(x.value) ? {label: x.name, v: null, t: 'raw ' + f1(x.value) + st(x), c: 'vz-mu'} : null;
    if (isN(x.percentile) && Array.isArray(core) && x.key && !core.includes(x.key)) return old(x) ? null : {label: x.name, v: x.percentile, t: Math.round(x.percentile) + ' · ' + mdd(x.as_of) + ' · not scored', c: 'vz-mu'};
    if (isN(x.percentile)) { const p = x.percentile; return {label: x.name, v: p, t: String(Math.round(p)), c: p < 30 ? 'vz-dn' : p > 70 ? 'vz-up' : 'vz-wn'}; }
    // a raw reading is no percentile: its row and date stay, but it is never placed on the percentile axis (audit 5 M12:
    // NAAIM 29.77 and G3 71.6 drawn as 30 and 72)
    if (isN(x.value)) return old(x) ? null : {label: x.name, v: null, t: 'raw ' + f1(x.value) + (x.as_of ? ' · ' + mdd(x.as_of) : '') + ' · not ranked, not scored', c: 'vz-mu'};
    return null;
  }).filter(Boolean);
}
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
  // T-252 (live 2026-11-10, 1400 and 390: "flip 686.08" printed over the "+0.76B" axis label): a line's label sits right
  // of its line unless it would run into the axis labels' column, then left of it. The charts on the page share no
  // label helper (this file's tx, ascend.js's inline text, dkc.js's txt), so each chart keeps its own labels apart;
  // route not taken: one collision step shared by all of them, which would be a new layer across three files.
  const lab = (x, y, t, c) => x + 4 + t.length * 6.2 > W - R ? tx(x - 4, y, t, c, 'end') : tx(x + 4, y, t, c);
  if (c.spot >= lo && c.spot <= hi) g += ln(X(c.spot), T, X(c.spot), H - B, 'vz-spot') + lab(X(c.spot), T + 2, 'spot ' + c.spot.toFixed(2), 'vz-axb');
  if (isN(c.flip) && c.flip >= lo && c.flip <= hi) g += ln(X(c.flip), T + 14, X(c.flip), H - B, 'vz-ref') + lab(X(c.flip), T + 16, 'flip ' + c.flip.toFixed(2));
  return svg(W, H, 'Net dealer gamma by strike', g);
}
P['m-ladder'] = W => {
  const cs = cards().filter(([, c]) => isA(c.ladder) && c.ladder.length >= 2);
  if (!cs.length) return null;
  const big = cs.map(([s, c]) => { const t = c.ladder.slice().sort((a, b) => Math.abs(b.net_gex_b) - Math.abs(a.net_gex_b))[0]; return {s, c, t}; });
  const neg = cs.filter(([, c]) => isN(c.net_gex_b) && c.net_gex_b < 0).length;
  // the chain snapshot's own spot, stamped: never read as the close (audit 5 M8)
  const bt = cs.map(([, c]) => c.built_at).filter(isN), at = bt.length ? (() => { try { return M.et(Math.max(...bt)).hm + ' ET '; } catch (e) { return ''; } })() : '';
  const h = 'At the ' + at + 'chain snapshot (' + cs.map(([s, c]) => s + ' ' + (isN(c.spot) ? c.spot.toFixed(2) : '?')).join(', ') + '): ' + (neg === cs.length ? 'Dealers short gamma in all ' + cs.length + ': moves tend to run. ' : neg === 0 ? 'Dealers long gamma: moves tend to be damped. ' : 'Mixed dealer gamma. ') +
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
// an expiry before today's ET date, or today's after the 16:00 ET close, has expired: never a "nearest expiry"
// (audit 5 M9: Nov 4 still listed that evening)
const expiryLive = (e, now) => { const t = (now || new Date()).toLocaleString('sv-SE', {timeZone: 'America/New_York'}); return !!e && (String(e) > t.slice(0, 10) || (String(e) === t.slice(0, 10) && t.slice(11, 16) < '16:00')); };
const livePins = c => (c.pins || []).filter(x => expiryLive(x.expiry));
P['m-pins'] = W => {
  const cs = cards().map(([s, c]) => [s, Object.assign({}, c, {pins: livePins(c)})]).filter(([, c]) => c.pins.length >= 2);
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
  // the funds' own option-chain gamma and SqueezeMetrics' SPX GEX are different measures: each is named with its sign's
  // meaning, so "amplifying" beside "GEX +3.1B" cannot read as a contradiction (audit 2026-11-04)
  const h = (neg === r.length ? 'All ' + r.length + ' funds’ chains amplifying (dealer gamma below zero): ' : neg === 0 ? 'All funds’ chains damped: ' : '') + spy.sym + ' room ' + pct(spy.put, 1) + ' to the put wall, ' + pct(spy.call, 1) + ' to the call wall' +
    (isN(spy.flip) ? ', flip ' + pct(spy.flip, 1) : '');
  let c = card('Dealer levels, % from spot', levels(W, r, em), k('up', 'put wall') + k('dn', 'call wall') + k('wn', 'gamma flip') + k('bl', 'expected move'));
  const sq = mk && mk.squeeze && isA(mk.squeeze.days) ? mk.squeeze.days : null;
  if (sq && sq.length > 10) {
    const d = sq.map(x => x.d), dix = sq.map(x => x.dix * 100), gx = sq.map(x => x.gex_b), ld = last(dix), rank = Math.round(100 * dix.filter(v => v <= ld).length / dix.length);
    c += card('DIX · dark-pool buying, % of volume (SqueezeMetrics)', lines(W, 160, d, [{v: dix, c: 'vz-sbl'}], {f: v => v.toFixed(0) + '%', ref: 45, refL: '45% · heavy buying', label: 'DIX history'})) +
      card('SPX dealer gamma, $B per 1% move (SqueezeMetrics)', lines(W, 160, d, [{v: gx, c: 'vz-sin'}], {f: v => v.toFixed(0), ref: 0, refL: '0 · flip', label: 'GEX history'}));
    return {h: h + '. SqueezeMetrics DIX ' + ld.toFixed(1) + '% (' + rank + 'th pct of 6 months); SqueezeMetrics SPX GEX ' + sgn(last(gx), 1) + 'B (' + ((last(gx) >= 0) === (neg === r.length) && (neg === r.length || neg === 0) ? 'index-wide, the opposite sign to the funds’ own chains' : last(gx) >= 0 ? 'positive: damping' : 'negative: amplifying') + ')', tone: neg === r.length ? 'd' : 'w', c};
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
  return {h: 'At VIX ' + (M.num ? M.num(t.vix, 1) : t.vix.toFixed(1)) + ' SPY usually moves ±' + t.d1_pct.toFixed(2) + '% a day and ±' + (isN(t.d5_pct) ? t.d5_pct.toFixed(2) : '—') + '% a week' +
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
// one level said once when the funds share it ("level 3 of 5, level 3 of 5" read as a stutter, T-044 p17)
const lvl = f => f.every(x => x.score === f[0].score) ? 'level ' + f[0].score + ' of 5' + (f.length > 1 ? (f.length === 2 ? ' on both' : ' on all ' + f.length) : '')
  : f.map(x => x.sym + ' level ' + x.score).join(', ') + ' of 5';
P['m-pulse'] = () => {
  const f = mk && mk.pulse && isA(mk.pulse.funds) ? mk.pulse.funds : [];
  if (!f.length) return null;
  const st = f.map(x => x.state), same = st.every(s => s === st[0]);
  return {h: (same ? 'Pulse ' + st[0] + ' on ' + f.map(x => x.sym).join(' and ') : f.map(x => x.sym + ' ' + x.state).join(' · ')) + ' (' + lvl(f) + ' on his state ladder, not a count of the checks)' +   /* audit 5 M18 */
    (isN(f[0].ram) ? '; ' + f[0].sym + ' risk ' + Math.round(f[0].ram) + '/100, ' + String(f[0].ram_level || '').toLowerCase() : ''), tone: /RED|PURPLE/.test(st[0]) ? 'd' : /GREEN|BLUE/.test(st[0]) ? 'u' : 'w'};
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
  // every name counted, and the horizon named: a weekly rotation reading, not the 20-session Sector strength (audit 5 M20)
  const some = a => a.slice(0, 4).join(', ') + (a.length > 4 ? ' +' + (a.length - 4) + ' more' : '');
  return {h: 'Weekly rotation vs SPY · ' + (L.length ? 'Leading: ' + some(L) : 'No sector leading') + (G.length ? ' · Lagging (' + G.length + '): ' + some(G) : ''), tone: 'w',
    c: W < 600 ? card('Sectors vs SPY · strength (across) and momentum (up)', quad(W, f), k('up', 'Leading') + k('bl', 'Improving') + k('wn', 'Weakening') + k('dn', 'Lagging')) : ''};
};
function quad(W, f) {
  const H = Math.round(W * .9), L = 8, R = 8, T = 8, B = 20, xs = f.map(x => x.ratio), ys = f.map(x => x.mom);
  const ex = Math.max(1.5, ...xs.map(v => Math.abs(v - 100))) * 1.15, ey = Math.max(1.5, ...ys.map(v => Math.abs(v - 100))) * 1.15;
  const X = v => L + (W - L - R) * (v - 100 + ex) / (2 * ex), Y = v => T + (H - T - B) * (100 + ey - v) / (2 * ey), QC = {Leading: 'vz-up', Improving: 'vz-bl', Weakening: 'vz-wn', Lagging: 'vz-dn'};
  let g = ln(X(100), T, X(100), H - B, 'vz-z') + ln(L, Y(100), W - R, Y(100), 'vz-z') + tx(W - R - 2, T + 12, 'Leading', 'vz-ax', 'end') + tx(L + 2, T + 12, 'Improving') +
    tx(W - R - 2, H - B - 6, 'Weakening', 'vz-ax', 'end') + tx(L + 2, H - B - 6, 'Lagging') + tx(W / 2, H - 4, 'weaker ← relative strength → stronger', 'vz-ax', 'middle');
  // T-252 (390 px, live 2026-11-10: "XLF" printed over "XLP", two funds a few px apart): a fund's label takes the first
  // free side of its dot (right, left, above, below), clear of the labels already placed, the corner words and the
  // other dots; a box is [x0, y0, x1, y1] from the text's anchor, 7.4 px a character
  const box = (x, y, t, a) => { const w = t.length * 7.4, x0 = a === 'end' ? x - w : a === 'middle' ? x - w / 2 : x; return [x0, y - 11, x0 + w, y + 3]; };
  const used = [box(W - R - 2, T + 12, 'Leading', 'end'), box(L + 2, T + 12, 'Improving'), box(W - R - 2, H - B - 6, 'Weakening', 'end'), box(L + 2, H - B - 6, 'Lagging')]
    .concat(f.map(x => [X(x.ratio) - 5, Y(x.mom) - 5, X(x.ratio) + 5, Y(x.mom) + 5]));
  const free = b => b[0] >= L && b[2] <= W - R && b[1] >= T && !used.some(u => b[0] < u[2] && u[0] < b[2] && b[1] < u[3] && u[1] < b[3]);
  f.forEach(x => {
    const cx = X(x.ratio), cy = Y(x.mom), at = [[cx + 7, cy + 4, ''], [cx - 7, cy + 4, 'end'], [cx, cy - 8, 'middle'], [cx, cy + 16, 'middle']];
    const o = at.find(p => free(box(p[0], p[1], x.sym, p[2]))) || at[0];
    used.push(box(o[0], o[1], x.sym, o[2]));
    g += '<circle cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="5" class="' + (QC[x.quad] || 'vz-mu') + '"/>' + tx(o[0], o[1], x.sym, 'vz-axb', o[2]);
  });
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
window.MDVM = {psyRows, levels, lines, readings: () => AREA.map(id => { try { const r = P[id](800); return [id, r && r.h]; } catch (e) { return [id, null]; } }), refresh: load};
load();
})();
