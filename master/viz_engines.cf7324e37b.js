/* Master Desk terminal, the engines' and tools' charts (owner 2026-11-02: every engine and tool shows its trading output
   as a graph, never its internal workings). One chart per panel, drawn from the same data the panel reads: the Morning
   Map (price against the dealer levels), the Qualified Board (each name's buy / stop / target ladder), the Golden Sweep
   Wire (premium by name, calls against puts), the Engine (momentum against loser risk), Forecasts, every desk lineup
   tool, Gap-Fill, the Correlation Web, Options data (each symbol's expected range), the Chart Read Engine and the
   ChartsLector and lens ranks. Inline SVG, no library; colours from app.css tokens. A panel with no data draws nothing. */
(() => {
const D = document, M = window.MD;
if (!M) return;
const isN = v => typeof v === 'number' && isFinite(v);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const f1 = v => (Math.round(v * 10) / 10).toString();
const pc = (v, d = 0) => isN(v) ? (+v).toFixed(d) + '%' : '—';
const sp = (v, d = 1) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: false}) + '%' : '—';   // Intl rounding, as every % (T-186)
const px = v => isN(v) ? (Math.abs(v) >= 1000 ? Math.round(v).toLocaleString('en-US') : (+v).toFixed(2)) : '—';
const usd = v => !isN(v) ? '—' : v >= 1e9 ? '$' + (v / 1e9).toFixed(1) + 'B' : v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M' : v >= 1e3 ? '$' + Math.round(v / 1e3) + 'K' : '$' + Math.round(v);
const width = id => { const n = D.getElementById(id); const w = n ? n.clientWidth : 0; return Math.max(300, Math.min(760, (w || 360) - 34)); };
const svg = (W, H, body, label) => '<svg class="vz-s" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="' + esc(label) + '">' + body + '</svg>';
const T = (x, y, s, cls, anchor) => '<text class="' + (cls || 'vz-t') + '" x="' + f1(x) + '" y="' + f1(y) + '"' + (anchor ? ' text-anchor="' + anchor + '"' : '') + '>' + esc(s) + '</text>';
const R = (x, y, w, h, cls) => '<rect class="' + cls + '" x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(Math.max(0, w)) + '" height="' + f1(Math.max(0, h)) + '" rx="2"/>';
const L = (x1, y1, x2, y2, cls) => '<line class="' + cls + '" x1="' + f1(x1) + '" y1="' + f1(y1) + '" x2="' + f1(x2) + '" y2="' + f1(y2) + '"/>';
const C = (x, y, r, cls) => '<circle class="' + cls + '" cx="' + f1(x) + '" cy="' + f1(y) + '" r="' + f1(r) + '"/>';
const RD = t => '<p class="vz-r">' + esc(t) + '</p>';
const fit = (t, px0) => { t = String(t); const n = Math.max(4, Math.floor(px0 / 6.6)); return t.length > n ? t.slice(0, n - 1) + '…' : t; };
const fig = (title, chart, note) => '<p class="vz-h">' + esc(title) + '</p>' + chart + (note ? '<p class="vz-nt">' + esc(note) + '</p>' : '');

// a legend that wraps to a new line instead of running off the right edge -> [svg, height]
function legend(keys, x0, y0, W) {
  let x = x0, y = y0, out = '';
  keys.forEach(([k, cls]) => { const w = 22 + k.length * 6.2; if (x + w > W - 4 && x > x0) { x = x0; y += 16; } out += R(x, y, 10, 10, cls) + T(x + 14, y + 9, k, 'vz-k'); x += w; });
  return [out, keys.length ? y - y0 + 16 : 0];
}
// ---- primitives ------------------------------------------------------------------------------------------------------
// horizontal bars: rows [{label, value, cls, text}], value on a 0..max (or signed) scale
function hbars(W, rows, o = {}) {
  if (!rows.length) return '';
  // o.above: when a label would be cut short at this width, each label takes its own line above its bar (phone widths)
  if (o.above && rows.some(r => fit(r.label, Math.min(o.lw || 110, W * 0.36) - 8) !== String(r.label))) return hbarsAbove(W, rows, o);
  const lw = Math.min(o.lw || 110, W * 0.36), rh = o.rh || 22, H = rows.length * rh + 6, tw = Math.max(48, ...rows.map(r => String(r.text != null ? r.text : r.value).length * 6.4 + 10)), vw = W - lw - tw;
  const vals = rows.map(r => r.value).filter(isN), signed = o.signed || vals.some(v => v < 0);
  const mx = o.max || Math.max(1e-9, ...vals.map(Math.abs)), z = signed ? lw + vw / 2 : lw, sc = signed ? vw / 2 / mx : vw / mx;
  return svg(W, H, rows.map((r, i) => {
    const y = 3 + i * rh, v = isN(r.value) ? r.value : 0, w = Math.abs(v) * sc, x = v >= 0 ? z : z - w;
    return T(lw - 6, y + rh * 0.62, fit(r.label, lw - 8), 'vz-t', 'end') + R(x, y + 3, Math.max(1, w), rh - 8, r.cls || (v >= 0 ? 'vz-u' : 'vz-d')) +
      T((v >= 0 ? x + w : z) + 5 + (signed && v < 0 ? 0 : 0), y + rh * 0.62, r.text != null ? r.text : String(v), 'vz-v');
  }).join('') + (signed ? L(z, 0, z, H, 'vz-z') : ''), o.label || 'bars');
}
function hbarsAbove(W, rows, o) {
  const rh = 38, H = rows.length * rh + 4, a = 4, tw = Math.max(48, ...rows.map(r => String(r.text != null ? r.text : r.value).length * 6.4 + 10)), vw = W - a - tw;
  const vals = rows.map(r => r.value).filter(isN), signed = o.signed || vals.some(v => v < 0);
  const mx = o.max || Math.max(1e-9, ...vals.map(Math.abs)), z = signed ? a + vw / 2 : a, sc = signed ? vw / 2 / mx : vw / mx;
  return svg(W, H, rows.map((r, i) => {
    const y = 2 + i * rh, v = isN(r.value) ? r.value : 0, w = Math.abs(v) * sc, x = v >= 0 ? z : z - w;
    return T(a, y + 12, fit(r.label, W - a), 'vz-t') + R(x, y + 17, Math.max(1, w), 14, r.cls || (v >= 0 ? 'vz-u' : 'vz-d')) +
      T((v >= 0 ? x + w : z) + 5, y + 28, r.text != null ? r.text : String(v), 'vz-v');
  }).join('') + (signed ? rows.map((r, i) => L(z, 17 + i * rh, z, 35 + i * rh, 'vz-z')).join('') : ''), o.label || 'bars');   // T-250: the zero mark beside each bar, never a stroke through the names above them
}
// stacked horizontal bars: rows [{label, parts: [{v, cls, k}]}], each row to 100% of its total (o.pct) or a shared scale
function stack(W, rows, keys, o = {}) {
  if (!rows.length) return '';
  const lw = Math.min(o.lw || 110, W * 0.34), rh = o.rh || 24, lg = legend(keys, lw, rows.length * rh + 10, W), H = rows.length * rh + 10 + lg[1], vw = W - lw - 12;
  const mx = Math.max(1e-9, ...rows.map(r => r.parts.reduce((a, p) => a + (p.v || 0), 0)));
  let b = rows.map((r, i) => {
    const y = 3 + i * rh, tot = r.parts.reduce((a, p) => a + (p.v || 0), 0) || 1, sc = o.pct ? vw / tot : vw / mx;
    let x = lw;
    return T(lw - 6, y + rh * 0.6, fit(r.label, lw - 8), 'vz-t', 'end') + r.parts.map(p => {
      const w = (p.v || 0) * sc, s = R(x, y + 3, w, rh - 8, p.cls) + (w > 30 ? T(x + w / 2, y + rh * 0.6, o.pct ? pc(100 * (p.v || 0) / tot) : String(p.v), 'vz-in', 'middle') : '');
      x += w; return s;
    }).join('');
  }).join('');
  return svg(W, H, b + lg[0], o.label || 'stacked bars');
}
// vertical grouped bars: groups [{label, bars: [{v, cls}]}]
function vbars(W, groups, keys, o = {}) {
  if (!groups.length) return '';
  const lg = legend(keys || [], 12, 0, W), H0 = o.h || 170, top = 16, bot = 26, ph = H0 - top - bot - 14, H = H0 + lg[1], n = groups[0].bars.length;
  const mx = o.max || Math.max(1e-9, ...groups.flatMap(g => g.bars.map(b => Math.abs(b.v || 0))));
  const gw = (W - 20) / groups.length, bw = Math.min(28, (gw - 10) / n);
  let s = L(10, top + ph, W - 10, top + ph, 'vz-z') + groups.map((g, i) => {
    const gx = 10 + i * gw + (gw - bw * n) / 2;
    return g.bars.map((b, j) => {
      const h = Math.abs(b.v || 0) / mx * ph, x = gx + j * bw;
      return R(x + 1, top + ph - h, bw - 2, h, b.cls) + (bw > 14 ? T(x + bw / 2, top + ph - h - 3, b.t != null ? b.t : String(b.v), 'vz-v', 'middle') : '');
    }).join('') + T(10 + i * gw + gw / 2, top + ph + 14, g.label, 'vz-t', 'middle');
  }).join('');
  s += legend(keys || [], 12, top + ph + 22, W)[0];
  return svg(W, H, s, o.label || 'bars');
}
// a price axis with marks: [{v, k: label, cls, side: 'up'|'dn'}], plus an optional shaded zone
function levels(W, title, lo, hi, marks, zones) {
  const a = 14, b = W - 14, X = v => a + (v - lo) / (hi - lo || 1) * (b - a), est = m => (m.k.length + 9) * 6.8;
  // labels never overlap: each side's labels take the first free line above (or below) the axis
  const place = side => { const lines = []; return marks.filter(m => (m.side !== 'dn') === (side === 'up')).sort((p, q) => X(p.v) - X(q.v)).map(m => {
    const x = X(m.v), w = est(m), x0 = Math.min(b - w, Math.max(a, x - w / 2));
    let i = 0; while (lines[i] != null && lines[i] > x0 - 4) i++;
    lines[i] = x0 + w; return {m, x, x0, i};
  }); };
  const up = place('up'), dn = place('dn'), nu = Math.max(1, ...up.map(p => p.i + 1)), nd = Math.max(1, ...dn.map(p => p.i + 1));
  const y = 34 + nu * 14, H = y + 14 + nd * 14;     // the title's line, then each label line (PNC 2026-11-04: Close met the title)
  let s = T(a, 12, title, 'vz-h3') + (zones || []).map(z => R(X(Math.min(z.a, z.b)), y - 7, Math.abs(X(z.b) - X(z.a)), 14, z.cls)).join('') + L(a, y, b, y, 'vz-z');
  [...up, ...dn].forEach(p => { s += p.m.dot ? C(p.x, y, 6, p.m.cls) : L(p.x, y - 10, p.x, y + 10, p.m.cls); });
  up.forEach(p => { s += T(p.x0, y - 12 - p.i * 14, p.m.k + ' ' + px(p.m.v), 'vz-k'); });
  dn.forEach(p => { s += T(p.x0, y + 22 + p.i * 14, p.m.k + ' ' + px(p.m.v), 'vz-k'); });
  return svg(W, H + 6, s, title);
}

// ---- the panels --------------------------------------------------------------------------------------------------------
const ED = () => M.ed || {};
const P = {};
P['f-map'] = () => {
  const cards = (((ED().funnel || {}).map || {}).cards || []).filter(c => isN(c.spot));
  if (!cards.length) return '';
  const W = width('f-map');
  const sx = cards.find(c => c.symbol === 'SPY') || cards[0], amp = cards.filter(c => isN(c.flip) && c.spot < c.flip).length;
  return RD(amp === cards.length ? 'All ' + cards.length + ' indexes trade below their gamma flip: expect bigger, faster moves.' : amp ? amp + ' of ' + cards.length + ' indexes trade below their gamma flip: moves speed up there.' : 'Every index trades above its gamma flip: moves tend to calm.') +
    RD(sx.symbol + ' ' + px(sx.spot) + ': put wall ' + px(sx.put_wall) + ' (' + sp(sx.put_wall_pct) + '), flip ' + px(sx.flip) + ', call wall ' + px(sx.call_wall) + ' (' + sp(sx.call_wall_pct) + ').') +
    fig('Where price sits against the dealer levels', cards.map(c => {
    const vs = [c.spot, c.put_wall, c.call_wall, c.flip].filter(isN), lo = Math.min(...vs) * 0.995, hi = Math.max(...vs) * 1.005;
    const amp = isN(c.flip) ? (c.flip > c.spot ? [{a: lo, b: c.flip, cls: 'vz-zd'}, {a: c.flip, b: hi, cls: 'vz-zu'}] : [{a: lo, b: c.flip, cls: 'vz-zd'}, {a: c.flip, b: hi, cls: 'vz-zu'}]) : [];
    return levels(W, c.symbol + ' · ' + (c.regime || '') + (isN(c.net_gex_b) ? ' · net gamma ' + c.net_gex_b.toFixed(1).replace('-', '\u2212') + 'B' : ''), lo, hi, [
      isN(c.put_wall) && {v: c.put_wall, k: 'Put wall', cls: 'vz-md', side: 'dn'}, isN(c.call_wall) && {v: c.call_wall, k: 'Call wall', cls: 'vz-mu', side: 'dn'},
      isN(c.flip) && {v: c.flip, k: 'Flip', cls: 'vz-mf', side: 'up'}, {v: c.spot, k: 'Spot', cls: 'vz-sp', side: 'up', dot: 1}].filter(Boolean), amp);
  }).join(''), 'Red: below the gamma flip, moves tend to speed up. Green: above it, moves tend to calm. The walls are where dealers defend.');
};
P['f-wire'] = () => {
  const ps = ((ED().funnel || {}).wire || {}).prints || [];
  if (!ps.length) return '';
  const by = {};
  ps.forEach(p => { const s = by[p.symbol] = by[p.symbol] || {c: 0, p: 0}; s[p.kind === 'put' ? 'p' : 'c'] += p.premium || 0; });
  const rows = Object.entries(by).sort((a, b) => (b[1].c + b[1].p) - (a[1].c + a[1].p)).slice(0, 10);
  const W = width('f-wire'), bull = ps.filter(p => p.sentiment === 'bullish').reduce((a, p) => a + (p.premium || 0), 0), bear = ps.filter(p => p.sentiment === 'bearish').reduce((a, p) => a + (p.premium || 0), 0);
  const top = rows[0];
  return RD((bull >= bear ? 'Bullish' : 'Bearish') + ' tilt: ' + usd(bull) + ' in bullish bets against ' + usd(bear) + ' bearish. Biggest: ' + top[0] + ' ' + usd(top[1].c + top[1].p) + (top[1].p > top[1].c ? ' mostly puts.' : ' mostly calls.')) + fig('Big-money options bets by name', stack(W, rows.map(([s, v]) => ({label: s, parts: [{v: Math.round(v.c / 1e5) / 10, cls: 'vz-u'}, {v: Math.round(v.p / 1e5) / 10, cls: 'vz-d'}]})),
    [['Calls, $M', 'vz-u'], ['Puts, $M', 'vz-d']], {label: 'premium by name'}) + hbars(W, [{label: 'Bullish bets', value: bull, cls: 'vz-u', text: usd(bull)}, {label: 'Bearish bets', value: bear, cls: 'vz-d', text: usd(bear)}], {lw: 100}),
    'Each bar is the premium in sweeps that met the rule. Green: call premium. Red: put premium. The tilt counts each print by its side: a put sold at or below the bid is a bullish bet, a call sold there a bearish one.');
};
let ENG = null, LU = null;
P['e-rank'] = () => {
  if (!ENG || !ENG.rows) return '';
  const ix = {}; ENG.cols.forEach((c, i) => { ix[c] = i; });
  const pts = ENG.rows.map(r => ({s: r[ix.sym], m: r[ix.mom], k: r[ix.risk], t: r[ix.tier], v: r[ix.veto]})).filter(p => isN(p.m) && isN(p.k));
  if (!pts.length) return '';
  const W = width('e-rank'), H = Math.round(Math.min(360, W * 0.7)) + 14, a = 34, b = W - 10, t = 24, bt = H - 30;   // t: room above the plot for its corner label
  const X = m => a + m / 100 * (b - a), Y = k => t + k / 100 * (bt - t);
  const best = pts.filter(p => !p.v).sort((p, q) => (q.m - q.k) - (p.m - p.k)).slice(0, 8);
  let s = R(X(70), Y(0), X(100) - X(70), Y(30) - Y(0), 'vz-zu') + R(X(0), Y(70), X(30) - X(0), Y(100) - Y(70), 'vz-zd') +
    L(a, bt, b, bt, 'vz-z') + L(a, t, a, bt, 'vz-z') + T((a + b) / 2, H - 6, 'Momentum rank → stronger', 'vz-k', 'middle') +
    '<text class="vz-k" transform="rotate(-90)" x="' + f1(-(t + bt) / 2) + '" y="12" text-anchor="middle">Loser risk ↓ riskier</text>' +
    '';
  s += pts.map(p => C(X(p.m), Y(p.k), 1.6, p.v ? 'vz-pd' : 'vz-p')).join('');
  s += best.map(p => C(X(p.m), Y(p.k), 4, 'vz-sp')).join('');
  // the corner labels sit outside the dots (audit 2026-11-04: "Strong and safe" over the leader dots at 390 px): the
  // strong corner above the plot, the weak one drawn last on a halo
  s += T(Math.min(b, X(85)), t - 8, 'Strong and safe', 'vz-kb', 'middle') + T(X(15), Y(96) - 2, 'Weak and risky', 'vz-kb vz-halo', 'middle');
  const ss = pts.filter(p => p.m >= 70 && p.k <= 30).length;
  return RD(ss + ' names are strong and low-risk (momentum 70+, loser risk 30 or less). Leaders: ' + best.slice(0, 4).map(p => p.s).join(', ') + '.') + fig('Every name: momentum against loser risk', svg(W, H, s, 'momentum against loser risk'), 'Top right is where the best long candidates sit; the dark dots are the leaders below.') +
    fig('Leaders: momentum rank (bar) and loser risk', hbars(W, best.map(p => ({label: p.s, value: p.m, text: 'momentum ' + p.m + ' · risk ' + p.k, cls: 'vz-u'})), {lw: 60, max: 100}));
};
const fcUp = e => /prob_up|p_up|chance_up|finish_higher/.test(String(e.latest.quantity || '')) && +e.latest.value >= 0 && +e.latest.value <= 1;
P['e-fc'] = () => {
  // an engine's value means what its quantity names: only an up-probability reads as "chance higher" and only a percent
  // move as "expected"; every other score is that engine's own 0-100% reading of the event it names (audit 2026-11-03:
  // a touch probability of 0.28 was drawn as "+0.3% expected", a volume-clock chance as "chance of finishing higher")
  const es = ((ED().forecasts || {}).engines || []).filter(e => e.latest && isN(+e.latest.value));
  if (!es.length) return '';
  const W = width('e-fc'), q = e => String(e.latest.quantity || ''), v = e => +e.latest.value;
  const hz = e => { const m = /(\d+)\s*d\b|_(\d+)d(?:_|$)/.exec(q(e)), n = m && (m[1] || m[2]), s = /_(\d+)s(?:_|$)/.exec(q(e));
    return n ? n + (n === '1' ? ' day' : ' days') : s ? s[1] + ' sessions' : e.latest.horizon_close ? 'to ' + day(e.latest.horizon_close) : 'the horizon'; };
  const isP = fcUp;
  const isV = e => !isP(e) && /move_pct|ret(?:urn)?\d*_pct/.test(q(e)) && e.latest.shown_as !== 'score';
  // T-250 (live 2026-11-10): signed signal scores were drawn as percentages beside true chances ("96% · SPY" for a +0.96
  // breadth score, "0% · ZWS" for 0.00) and the negative ones left off, because every "score" in [0, 1] was taken as a
  // chance. The edition marks an unattested chance and a signed score alike (shown_as "score"), so the bars tell them
  // apart as the card does (ascend.js fcv, the same rule; tests/test_forecast_bars_1110c.py holds the two together): a
  // chance is a percent bar, a signed score a signed bar with its sign. Route not taken: a kind flag written by the
  // producer (desk/forecast/engines/edition.py _latest); it needs a new edition key and the page would still need
  // this rule for an edition written before it.
  const FC_PROB = /(^|_)(touch|finish|chance|prob|flip)|_gt_|^rv\d+_gt|^mdd\d+_gt|^moves_third_toward_base$/;
  const isC = e => !isP(e) && !isV(e) && (e.latest.shown_as === 'probability' || (e.latest.shown_as === 'score' && FC_PROB.test(q(e)))) && v(e) >= 0 && v(e) <= 1;
  const isG = e => !isP(e) && !isV(e) && e.latest.shown_as === 'score' && !FC_PROB.test(q(e));
  const sg = x => (x > 0 ? '+' : x < 0 ? '−' : '') + Math.abs(x).toFixed(2), ch = x => Math.round(100 * x) + '%';
  const who = s => { const m = /^figure:(\w+)$/.exec(String(s || '')), o = m && ((ED().forecasts || {}).engines || []).find(x => x.id === m[1]);   // T-246: an engine by its name, never its id
    return o && o.name ? o.name : String(s || '').replace(/^(cohort|figure):/, ''); };
  const sub = e => who(e.latest.subject) || e.name, P0 = es.filter(isP), V0 = es.filter(isV), S0 = es.filter(isC), G0 = es.filter(isG);
  const say = e => isP(e) ? sub(e) + ': ' + pc(100 * v(e)) + ' chance higher over ' + hz(e) : isV(e) ? sub(e) + ': ' + sp(v(e)) + ' expected over ' + hz(e)
    : e.name + ' on ' + sub(e) + ': ' + (isG(e) ? sg(v(e)) + ' signed score' : ch(v(e))) + (/^to /.test(hz(e)) ? ' ' : ' over ') + hz(e);
  const lw = Math.min(240, Math.round(W * 0.45));
  return RD([...P0, ...V0, ...S0, ...G0].slice(0, 3).map(say).join(' · ') + '.') +
    (P0.length ? fig('Chance of finishing higher (50% = a coin flip)', hbars(W, P0.map(e => ({label: sub(e) + ' · ' + hz(e), value: 100 * v(e) - 50, text: pc(100 * v(e)), cls: v(e) >= 0.5 ? 'vz-u' : 'vz-d'})), {lw, max: 50, signed: 1, above: 1})) : '') +
    (V0.length ? fig('Expected move', hbars(W, V0.map(e => ({label: sub(e) + ' · ' + hz(e), value: v(e), text: sp(v(e))})), {lw, above: 1})) : '') +
    (S0.length ? fig('Each engine’s own score for the event it names', hbars(W, S0.map(e => ({label: e.name, value: 100 * v(e), text: ch(v(e)) + ' · ' + sub(e), cls: 'vz-n'})), {lw, max: 100, above: 1}), 'Resolves on the engine’s horizon date; graded when it closes.') : '') +
    (G0.length ? fig('Signed signal scores: zero is neutral, the sign is the side the engine leans to', hbars(W, G0.map(e => ({label: e.name, value: v(e), text: sg(v(e)) + ' · ' + sub(e)})), {lw, max: Math.max(1, ...G0.map(e => Math.abs(v(e)))), signed: 1, above: 1})) : '');
};
// the desk lineup: one chart per tool, the tool chosen on the panel
const LT = {
  or(W) {
    const w = (LU.opening_range || {}).windows || [];
    const h = w[w.length - 1] || {};
    // from the counts, as the bars are (T-217 p17: 60 of 156 was published as 38.5 and read "39%" beside the bar's 38%)
    const sh = k => isN(h[k]) && h.days > 0 ? pc(100 * h[k] / h.days) : pc(h[k + '_pct']);
    return RD(h.label ? h.label + ': only the high broke ' + sh('up_only') + ', only the low ' + sh('down_only') + ', both ' + sh('both') + ' of days.' : '') + fig('After the first minutes: which side broke', stack(W, w.map(x => ({label: x.label.replace('First ', ''), parts: [{v: x.up_only, cls: 'vz-u'}, {v: x.down_only, cls: 'vz-d'}, {v: x.both, cls: 'vz-n'}, {v: x.neither, cls: 'vz-q'}]})),
      [['High only', 'vz-u'], ['Low only', 'vz-d'], ['Both', 'vz-n'], ['Neither', 'vz-q']], {pct: 1}));
  },
  em(W) {
    const r = (LU.expected_move || {}).record || {}, k = Object.keys(r);
    if (!k.length) return '';
    const rec = (r.SPY || r[k[0]]).recent || [];
    return RD(k.map(s => s + ' closed inside its expected move ' + pc(r[s].last250_pct)).join(', ') + ' of the last 250 sessions.') + fig('How often the close stayed inside the expected move', hbars(W, k.map(s => ({label: s, value: r[s].last250_pct, text: pc(r[s].last250_pct), cls: 'vz-u'})), {max: 100})) +
      (rec.length ? fig((r.SPY ? 'SPY' : k[0]) + ': close against the expected range, recent sessions', rangeSeries(W, rec.map(x => ({d: x.session.slice(5), lo: x.lower, hi: x.upper, c: x.close, ok: x.inside})))) : '');
  },
  cb(W) {
    const lv = ((LU.corrected_band || {}).live || []).filter(x => x.bands);
    if (!lv.length) return '';
    const z = lv[0], hist = (LU.corrected_band || {}).history || {}, cov = (s, h, b) => (((hist[s] || {})[String(h)] || {}).coverage || {})[b];
    const c68 = cov(z.symbol, z.h, '68'), c95 = cov(z.symbol, z.h, '95');
    // the measured coverage, never the nominal odds (audit 2026-11-04: "two days in three" while the 68% band held 55-61%)
    return RD(z.symbol + ' next session: the inner band' + (isN(c68) ? ', which has held ' + pc(c68) + ' of past sessions,' : '') + ' runs ' + px(z.bands['68'][0]) + ' to ' + px(z.bands['68'][1]) + ' (close ' + px(z.close) + ').') + fig('Where price should land: the corrected bands', lv.map(x => {
      const b = x.bands, lo = b['95'][0], hi = b['95'][1];
      return levels(W, x.symbol + ' · ' + x.h + (x.h === 1 ? ' session' : ' sessions') + ' ahead', lo * 0.998, hi * 1.002, [{v: b['68'][0], k: '68% low', cls: 'vz-md', side: 'dn'}, {v: b['68'][1], k: '68% high', cls: 'vz-mu', side: 'dn'},
        {v: x.close, k: 'Close', cls: 'vz-sp', side: 'up', dot: 1}], [{a: b['95'][0], b: b['95'][1], cls: 'vz-zq'}, {a: b['68'][0], b: b['68'][1], cls: 'vz-zn'}]);
    }).join(''), 'Inner band (68% nominal)' + (isN(c68) ? ': held ' + pc(c68) + ' of past sessions' : '') + '. Outer band (95% nominal)' + (isN(c95) ? ': held ' + pc(c95) : '') + '.');
  },
  sc(W) {
    const c = (LU.strat_combos || {}).completed || [];
    return RD(c[0] ? 'Most common completed pattern: ' + c[0].pattern + ' on ' + c[0].count + ' names.' : '') + fig('Strat patterns that completed on the last session', hbars(W, c.slice(0, 10).map(x => ({label: x.pattern.slice(0, Math.max(10, Math.floor(Math.min(160, W * 0.4) / 6.2))), value: x.count, cls: /^(2d|2D|down)$/.test(String(x.pattern).split(/[\s-]+/).pop()) ? 'vz-d' : 'vz-u'})), {lw: Math.round(Math.min(160, W * 0.4))}));
  },
  rw(W) {
    const e = (LU.reversal_wire || {}).entries || [], ds = [...new Set(e.map(x => x.date))].sort(), fl = [...new Set(e.map(x => x.flag))];
    const word = f => { const l = (e.find(x => x.flag === f) || {}).label || f; return l.split(':')[0]; };
    const bull = f => /hammer|f2d|bull/i.test(f), cls = fl.map(f => bull(f) ? (/hammer/i.test(f) ? 'vz-u' : 'vz-u2') : (/shoot/i.test(f) ? 'vz-d' : 'vz-q'));
    const last = e.filter(x => x.date === ds[ds.length - 1]).sort((a, b) => b.count - a.count)[0];
    return RD(last ? 'Last session: ' + last.count + ' names printed a ' + word(last.flag).toLowerCase() + '.' : '') + fig('Reversal candles across the roster, by day', stack(W, ds.map(d => ({label: d.slice(5), parts: fl.map((f, i) => ({v: (e.find(x => x.date === d && x.flag === f) || {}).count || 0, cls: cls[i]}))})),
      fl.map((f, i) => [word(f) + (bull(f) ? ' (bullish)' : ' (bearish)'), cls[i]]), {lw: 60}));
  },
  fd(W) {
    const f = LU.fear_days || {}, a = f.after || [], r = (f.recent || []).slice().reverse();
    const a21 = a[a.length - 1] || {};
    const gd = new Date(ED().generated_at || NaN), today = isNaN(gd) ? '' : gd.toLocaleDateString('en-CA', {timeZone: 'America/New_York'}), ld = f.latest && f.latest.date ? String(f.latest.date).slice(0, 10) : '';
    const lead = !f.latest ? '' : ld && ld !== today ? (f.latest.fear ? 'The last session read, ' + day(ld) + ', was a fear day. ' : day(ld) + ' was not a fear day. ') : f.latest.fear ? 'Today is a fear day. ' : 'Not a fear day. ';
    return RD(lead + 'After past fear days SPY rose ' + pc(a21.positive_pct) + ' of the time ' + a21.h + ' days later, median ' + sp(a21.median_pct) + '.') + fig('After a fear day: how often SPY was higher', stack(W, a.map(x => ({label: x.h + 'd later', parts: [{v: x.positive_pct, cls: 'vz-u'}, {v: 100 - x.positive_pct, cls: 'vz-d'}]})),
      [['Higher', 'vz-u'], ['Lower', 'vz-d']], {pct: 1, lw: 90}), 'Median move: ' + a.map(x => x.h + 'd ' + sp(x.median_pct)).join(' · ') + '.') +
      (r.length ? fig('Recent fear days: SPY that day', hbars(W, r.map(x => ({label: x.date.slice(5), value: x.spy_pct, text: sp(x.spy_pct, 2) + (isN(x.vix) ? ' · VIX ' + x.vix.toFixed(1) : '')})), {lw: 60})) : '');
  },
  pn(W) {
    const b = (LU.pullback_norm || {}).buckets || [];
    const sh = b.slice(0, 2).reduce((x, y) => x + y.uptrend, 0), ut = b.reduce((x, y) => x + y.uptrend, 0);
    return RD(pc(100 * sh / (ut || 1)) + ' of names in uptrends sit in a shallow or normal pullback; the deep ones are the rarer buys.') + fig('How deep each name has pulled back, against its own history', vbars(W, b.map(x => ({label: x.label.split(' (')[0], bars: [{v: x.uptrend, cls: 'vz-u'}, {v: x.all - x.uptrend, cls: 'vz-q'}]})), [['In an uptrend', 'vz-u'], ['Not in an uptrend', 'vz-q']]));
  },
  ch(W) {
    const r = (LU.changes || {}).rows || [];
    return RD(r.slice(0, 3).map(x => x.count + ' ' + x.label.toLowerCase()).join(' · ') + '.') + fig('What changed on the last session', hbars(W, r.map(x => ({label: x.label.replace(/ \(.*$/, '').replace('50-day average', '50-day'), value: x.count, cls: /low|below|lost/i.test(x.label) ? 'vz-d' : /high|above/i.test(x.label) ? 'vz-u' : 'vz-n'})), {lw: Math.min(230, W * 0.5)}));
  },
  scr(W) { return uni(W, 'The roster: 3-month move against distance from the high'); },
  wl(W) {   // the viewer's own list (lineup.js, md_watch); none: no chart (it drew the Screener's roster, audit 2026-11-04)
    let wl = []; try { wl = JSON.parse(localStorage.getItem('md_watch') || '[]').filter(x => typeof x === 'string'); } catch (e) { wl = []; }
    const rows = wl.map(uniRow).filter(r => r && isN(r.d63));
    if (!rows.length) return '';
    return RD('Your list: ' + rows.slice(0, 4).map(r => r.s + ' ' + sp(r.d63, 0)).join(', ') + ' over three months.') + fig('Your watchlist: 3-month move', hbars(W, rows.map(r => ({label: r.s, value: r.d63, text: sp(r.d63, 0)})), {lw: 60, signed: 1}));
  },
  rp(W) {
    const q = String((D.getElementById('lu-rq') || {}).value || '').trim().toUpperCase(), r = uniRow(q) || uniRow('SPY');
    if (!r) return '';
    const b = [['Day', r.d1], ['1 mo', r.d21], ['3 mo', r.d63], ['6 mo', r.d126], ['vs 50-day', r.vs50], ['vs 200-day', r.vs200], ['From 52-wk high', isN(r.below_high) ? -Math.abs(r.below_high) : null]].filter(x => isN(x[1]));
    return RD(r.s + ' closed ' + px(r.close) + ': ' + sp(r.d63, 1) + ' over three months, ' + sp(r.vs200, 1) + ' against its 200-day.') +
      fig(r.s + ': moves and distance from its averages', hbars(W, b.map(([k, v]) => ({label: k, value: v, text: sp(v, 1)})), {lw: 110, signed: 1}));
  },
};
function uniRow(s) {
  const u = (LU && LU.universe) || {}, c = u.cols || [], i = c.indexOf('s');
  const row = s && i >= 0 && (u.rows || []).find(r => r[i] === s);
  if (!row) return null;
  const o = {}; c.forEach((k, j) => { o[k] = row[j]; }); return o;
}
const day = s => { const d = new Date(String(s).slice(0, 10) + 'T12:00:00Z'); return isNaN(d) ? String(s) : d.toLocaleDateString('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'}); };
function rangeSeries(W, rs) {
  const H = 150, a = 40, b = W - 8, t = 8, bt = H - 22, vs = rs.flatMap(r => [r.lo, r.hi, r.c]).filter(isN), lo = Math.min(...vs), hi = Math.max(...vs);
  const Y = v => bt - (v - lo) / (hi - lo || 1) * (bt - t), bw = (b - a) / rs.length;
  return svg(W, H, rs.map((r, i) => { const x = a + i * bw + bw / 2; return L(x, Y(r.lo), x, Y(r.hi), 'vz-rg') + C(x, Y(r.c), 3.5, r.ok ? 'vz-pu' : 'vz-pdd') + (i % Math.ceil(rs.length / 6) === 0 ? T(x, H - 6, r.d, 'vz-k', 'middle') : ''); }).join('') +
    T(a - 4, Y(hi) + 4, px(hi), 'vz-k', 'end') + T(a - 4, Y(lo), px(lo), 'vz-k', 'end'), 'close against range');
}
function uni(W, title) {
  const u = LU.universe || {}, c = u.cols || [], i3 = c.indexOf('d63'), ib = c.indexOf('below_high'), is = c.indexOf('s');
  if (i3 < 0 || ib < 0) return '';
  const pts = (u.rows || []).map(r => ({s: r[is], x: -Math.abs(r[ib]), y: r[i3]})).filter(p => isN(p.x) && isN(p.y));
  if (!pts.length) return '';
  const H = Math.round(Math.min(320, W * 0.62)), a = 36, b = W - 8, t = 8, bt = H - 26, xl = Math.max(-60, Math.min(...pts.map(p => p.x))), yl = Math.max(-60, Math.min(...pts.map(p => p.y))), yh = Math.min(150, Math.max(...pts.map(p => p.y)));
  const X = v => a + (Math.max(xl, v) - xl) / (0 - xl || 1) * (b - a), Y = v => bt - (Math.min(yh, Math.max(yl, v)) - yl) / (yh - yl || 1) * (bt - t);
  const lead = pts.filter(p => p.x > -3).sort((p, q) => q.y - p.y).slice(0, 6);
  return RD(lead.length ? 'Leaders at their highs: ' + lead.slice(0, 4).map(p => p.s + ' ' + sp(p.y, 0)).join(', ') + ' over three months.' : '') + fig(title, svg(W, H, L(a, Y(0), b, Y(0), 'vz-z') + pts.map(p => C(X(p.x), Y(p.y), 1.6, p.y >= 0 ? 'vz-p' : 'vz-pd')).join('') + lead.map(p => C(X(p.x), Y(p.y), 4, 'vz-sp')).join('') +
    T((a + b) / 2, H - 6, 'Distance below the 52-week high → at the high', 'vz-k', 'middle') + T(a - 4, Y(yh) + 8, sp(yh, 0), 'vz-k', 'end') + T(a - 4, Y(0) + 4, '0%', 'vz-k', 'end') + T(a - 4, Y(yl), sp(yl, 0), 'vz-k', 'end'), 'roster scatter'),
    'Top right: names up the most over three months and still at their highs. The large white dots are the leaders listed below.') +
    fig('Leaders within 3% of their high: 3-month move', hbars(W, lead.map(p => ({label: p.s, value: p.y, text: sp(p.y, 0)})), {lw: 60}));
}
P['h-lineup'] = () => {
  if (!LU) return '';
  const k = (D.querySelector('#h-lineup [data-k][aria-pressed="true"]') || {}).dataset;
  const t = LT[(k && k.k) || 'or'];
  return t ? t(width('h-lineup')) : '';
};
P['h-gaps'] = () => {
  const g = LU && LU.gap_fill;
  if (!g || !g.by_size) return '';
  const W = width('h-gaps');
  const s0 = g.by_size[0], sN = g.by_size[g.by_size.length - 1];
  return RD('Small gaps (' + s0.size + ') fill the same day ' + pc(s0.up.filled_pct) + ' (up) and ' + pc(s0.down.filled_pct) + ' (down); gaps ' + sN.size + ' fill only ' + pc(sN.up.filled_pct) + '. Fade small gaps, respect big ones.') + fig('Odds a gap fills the same day, by gap size', vbars(W, g.by_size.map(r => ({label: r.size, bars: [{v: r.up.filled_pct, cls: 'vz-u', t: pc(r.up.filled_pct)}, {v: r.down.filled_pct, cls: 'vz-d', t: pc(r.down.filled_pct)}]})),
    [['Gap up filled', 'vz-u'], ['Gap down filled', 'vz-d']], {max: 100})) +
    fig('By weekday', vbars(W, g.by_weekday.map(r => ({label: r.day, bars: [{v: r.filled_pct, cls: 'vz-n', t: pc(r.filled_pct)}]})), [], {h: 120, max: 100}));
};
P['h-corr'] = () => {
  const w = LU && LU.correlation_web;
  if (!w || !(w.pairs || []).filter(p => p.r < 0.99).length) return '';
  if (w.matrix && (w.matrix.names || []).length >= 3) return corrMatrix(w);
  const W = width('h-corr'), ps = w.pairs.filter(p => p.r < 0.99).sort((p, q) => q.r - p.r).slice(0, 16), ns = [...new Set(ps.flatMap(p => [p.a, p.b]))];
  const rr = {}; ps.forEach(p => { rr[p.a + '|' + p.b] = rr[p.b + '|' + p.a] = p.r; });
  const lo = Math.min(...ps.map(p => p.r)), lw = 44, n = ns.length, cs = Math.min(34, (W - lw - 6) / n), top = 44;
  // a matrix of r, one tile per linked pair (both halves); deeper blue = tighter; an empty cell is not linked
  let s = ns.map((a, i) => T(lw - 5, top + i * cs + cs * 0.62, a, 'vz-k', 'end') +
    '<text class="vz-k" transform="translate(' + f1(lw + i * cs + cs * 0.62) + ' ' + (top - 5) + ') rotate(-55)">' + esc(a) + '</text>' +
    ns.map((b, j) => {
      const x = lw + j * cs, y = top + i * cs, v = rr[a + '|' + b];
      if (i === j) return R(x + 1, y + 1, cs - 2, cs - 2, 'vz-tr');
      if (!isN(v)) return '<rect class="vz-hm0" x="' + f1(x + 1) + '" y="' + f1(y + 1) + '" width="' + f1(cs - 2) + '" height="' + f1(cs - 2) + '" rx="2"/>';
      const o = 0.35 + 0.65 * (v - lo) / ((0.99 - lo) || 1);
      return '<rect class="vz-hm" x="' + f1(x + 1) + '" y="' + f1(y + 1) + '" width="' + f1(cs - 2) + '" height="' + f1(cs - 2) + '" rx="2" fill-opacity="' + o.toFixed(2) + '"><title>' + esc(a + ' / ' + b + ': r ' + v.toFixed(2).replace(/^-/, '−')) + '</title></rect>' +
        (cs >= 26 ? T(x + cs / 2, y + cs * 0.62, v.toFixed(2), 'vz-in', 'middle') : '');
    }).join('')).join('');
  const H = top + n * cs + 6, cl = w.clusters || [], big = cl.slice().sort((a, b) => b.size - a.size)[0];
  return RD('Tightest pair: ' + ps[0].a + ' and ' + ps[0].b + ' (r ' + (+ps[0].r).toFixed(2) + ').' + (big ? ' Biggest group: ' + big.size + ' names led by ' + big.members.slice(0, 3).join(', ') + ' — treat them as one bet.' : '')) +
    fig('Correlation matrix: the most tightly linked names', svg(W, H, s, 'correlation matrix'), 'Deeper blue = tighter link (r ' + lo.toFixed(2) + ' to 0.99). Hover a tile for its r.') +
    (cl.length ? fig('Groups that trade as one', hbars(W, cl.map(c => ({label: c.members.slice(0, 3).join(' '), value: c.size, text: c.size + ' names', cls: 'vz-n'})), {lw: 150})) : '');
};

// the full matrix: every cell coloured by its r on a diverging scale (red = opposite, grey = unrelated, blue = together),
// the diagonal marked, names ordered cluster by cluster so each group reads as a block
function corrMatrix(w) {
  const ns = w.matrix.names, M0 = w.matrix.r, n = ns.length, W = width('h-corr'), lw = 46, cs = Math.max(12, Math.min(40, (W - lw - 8) / n)), top = 46;
  const cl = (w.clusters || []).map(c => new Set(c.members)), grp = s => cl.findIndex(g => g.has(s));
  let s = '';
  ns.forEach((a, i) => {
    s += T(lw - 5, top + i * cs + cs * 0.62, a, 'vz-k', 'end') + '<text class="vz-k" transform="translate(' + f1(lw + i * cs + cs * 0.62) + ' ' + (top - 5) + ') rotate(-55)">' + esc(a) + '</text>';
    ns.forEach((b, j) => {
      const x = lw + j * cs + 1, y = top + i * cs + 1, v = (M0[i] || [])[j];
      if (i === j) { s += '<rect class="vz-hmd" x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(cs - 2) + '" height="' + f1(cs - 2) + '" rx="2"/>'; return; }
      if (!isN(v)) { s += '<rect class="vz-hm0" x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(cs - 2) + '" height="' + f1(cs - 2) + '" rx="2"/>'; return; }
      s += '<rect class="' + (v >= 0 ? 'vz-hmp' : 'vz-hmn') + '" x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(cs - 2) + '" height="' + f1(cs - 2) + '" rx="2" fill-opacity="' + (0.12 + 0.88 * Math.min(1, Math.abs(v))).toFixed(2) + '"><title>' + esc(a + ' / ' + b + ': r ' + v.toFixed(2).replace(/^-/, '−')) + '</title></rect>' +
        (cs >= 30 ? T(x + cs / 2 - 1, y + cs * 0.6, (v < 0 ? '−' : '') + Math.abs(v).toFixed(2).replace(/^0/, ''), Math.abs(v) > 0.5 ? 'vz-in' : 'vz-k', 'middle') : '');
    });
  });
  // a frame around each cluster's block
  let i0 = 0;
  for (let i = 1; i <= n; i++) if (i === n || grp(ns[i]) !== grp(ns[i0])) { if (grp(ns[i0]) >= 0 && i - i0 > 1) s += '<rect class="vz-hmb" x="' + f1(lw + i0 * cs) + '" y="' + f1(top + i0 * cs) + '" width="' + f1((i - i0) * cs) + '" height="' + f1((i - i0) * cs) + '" rx="3"/>'; i0 = i; }
  const H = top + n * cs + 8, lgW = Math.min(260, W - 40), lx = (W - lgW) / 2;
  let lg = '';
  for (let k = 0; k < 20; k++) { const v = -1 + k / 9.5; lg += '<rect class="' + (v >= 0 ? 'vz-hmp' : 'vz-hmn') + '" x="' + f1(lx + k * lgW / 20) + '" y="4" width="' + f1(lgW / 20 + 0.5) + '" height="10" fill-opacity="' + (0.12 + 0.88 * Math.min(1, Math.abs(v))).toFixed(2) + '"/>'; }
  lg += T(lx, 28, 'Moves opposite −1', 'vz-k') + T(lx + lgW / 2, 28, '0', 'vz-k', 'middle') + T(lx + lgW, 28, '+1 Moves together', 'vz-k', 'end');
  const off = []; ns.forEach((a, i) => ns.forEach((b, j) => { const v = (M0[i] || [])[j]; if (j > i && isN(v)) off.push([a, b, v]); }));
  const hi = off.slice().sort((p, q) => q[2] - p[2])[0], lo = off.slice().sort((p, q) => p[2] - q[2])[0], big = (w.clusters || [])[0];
  return RD('Tightest among the ' + n + ' shown: ' + hi[0] + ' and ' + hi[1] + ' (r ' + hi[2].toFixed(2).replace(/^-/, '−') + '); most opposite: ' + lo[0] + ' and ' + lo[1] + ' (r ' + lo[2].toFixed(2).replace(/^-/, '−') + ').'   /* T-229: 'r -0.63' */ + (big ? ' Biggest group: ' + big.size + ' names — treat them as one bet.' : '')) +
    fig('Correlation of daily returns, ' + (w.window || 120) + ' sessions', svg(W, H, s, 'correlation matrix') + svg(W, 34, lg, 'scale'), 'Framed blocks are groups that trade as one. Hover a tile for its r.') +
    ((w.clusters || []).length ? fig('Groups that trade as one', hbars(W, w.clusters.map(c => ({label: c.members.slice(0, 3).join(' '), value: c.size, text: c.size + ' names', cls: 'vz-n'})), {lw: 150})) : '');
}
P['h-optdata'] = () => {
  const ms = ((ED().options_data || {}).memos || []).filter(m => isN(m.spot) && isN(m.lower) && isN(m.upper));
  if (!ms.length) return chainCharts();
  const W = width('h-optdata');
  return RD(ms.map(m => m.symbol + ' ' + px(m.lower) + '–' + px(m.upper) + (isN(m.move_pct) ? ' (±' + m.move_pct.toFixed(1) + '%)' : '')).slice(0, 3).join(' · ')) + fig('Options-implied range to the next expiry', ms.map(m => levels(W, m.symbol + (isN(m.move_pct) ? ' · ±' + m.move_pct.toFixed(2) + '%' : '') + (isN(m.atm_iv) ? ' · IV ' + (m.atm_iv * 100).toFixed(0) + '%' : ''),
    m.lower * 0.995, m.upper * 1.005, [{v: m.lower, k: 'Low', cls: 'vz-md', side: 'dn'}, {v: m.upper, k: 'High', cls: 'vz-mu', side: 'dn'}, {v: m.spot, k: /close/i.test(m.spot_source || '') ? 'Close' : 'Spot', cls: 'vz-sp', side: 'up', dot: 1}], [{a: m.lower, b: m.upper, cls: 'vz-zn'}])).join(''),
    'The band the at-the-money straddle prices in: where the options market expects price by that expiry.');
};
// no memo yet today: the last options chain the desk archived, dated: the ATM IV term structure and dealer gamma by strike
function chainCharts() {
  const mg = ED().morgue || {}, ch = (mg.chain || {}).cards || {}, mp = (mg.map || {}).cards || {}, W = width('h-optdata');
  const syms = ['SPY', 'QQQ', 'IWM', ...Object.keys(ch)].filter((k, i, A) => A.indexOf(k) === i && ch[k]).filter(k => (ch[k].atm_by_expiry || []).length).slice(0, 3);
  if (!syms.length) return '';
  const cls = ['vz-u', 'vz-n', 'vz-a'], st = ['vz-lu', 'vz-ln', 'vz-la'], all = syms.flatMap(k => ch[k].atm_by_expiry.filter(r => isN(r.days) && isN(r.atm_iv)));
  const H = 180, a = 40, b = W - 10, t = 10, bt = H - 24, dx = Math.max(...all.map(r => r.days)), ylo = Math.min(...all.map(r => r.atm_iv)), yhi = Math.max(...all.map(r => r.atm_iv));
  const X = d => a + Math.sqrt(d) / Math.sqrt(dx || 1) * (b - a), Y = v => bt - (v - ylo) / ((yhi - ylo) || 1) * (bt - t);
  let s = L(a, bt, b, bt, 'vz-z') + T(a - 4, Y(yhi) + 4, pc(yhi * 100), 'vz-k', 'end') + T(a - 4, Y(ylo) + 4, pc(ylo * 100), 'vz-k', 'end');
  [1, 7, 30, 90].filter(d => d <= dx).forEach(d => { s += T(X(d), H - 6, d + 'd', 'vz-k', 'middle'); });
  syms.forEach((k, i) => { const r = ch[k].atm_by_expiry.filter(x => isN(x.days) && isN(x.atm_iv)); s += '<path class="' + st[i] + '" d="' + r.map((x, j) => (j ? 'L' : 'M') + f1(X(x.days)) + ' ' + f1(Y(x.atm_iv))).join('') + '"/>' + r.map(x => C(X(x.days), Y(x.atm_iv), 3, cls[i]) .replace('/>', '><title>' + esc(k + ' ' + x.days + 'd: IV ' + pc(x.atm_iv * 100, 1)) + '</title></circle>')).join(''); });
  const lg = legend(syms.map((k, i) => [k + '  ', cls[i]]), a, 0, W);
  // the headline skips 0-1 day expiries: their IV, on a time floored at an hour, is not the term (audit 2026-11-04:
  // "50% at 1d" beside a 16.2% gauge); the chart still draws them
  const k0 = syms[0], rall = ch[k0].atm_by_expiry.filter(x => isN(x.days) && isN(x.atm_iv)), r1 = rall.filter(x => x.days >= 2), r0 = r1.length ? r1 : rall, asof = ch[k0].as_of;
  const gd = new Date(ED().generated_at || NaN), edDay = isNaN(gd) ? '' : gd.toLocaleDateString('en-CA', {timeZone: 'America/New_York'}), isToday = edDay && String(asof).slice(0, 10) === edDay;
  const m = mp[k0] || mp.SPY || {}, lad = (m.ladder || []).filter(x => isN(x.strike) && isN(x.net_gex_b)).sort((p, q) => q.strike - p.strike);
  const lad2 = lad.length > 16 ? lad.slice().sort((p, q) => Math.abs(q.net_gex_b) - Math.abs(p.net_gex_b)).slice(0, 16).sort((p, q) => q.strike - p.strike) : lad;
  return RD((isToday ? 'Today\u2019s chain: ' : 'No chain yet today. Last chain, ' + day(asof) + ': ') + k0 + ' implied vol ' + pc(r0[0].atm_iv * 100) + ' at ' + r0[0].days + 'd, ' + pc(r0[r0.length - 1].atm_iv * 100) + ' at ' + r0[r0.length - 1].days + 'd.') +
    fig('At-the-money implied vol by days to expiry · ' + day(asof), svg(W, lg[1] + 4, lg[0], 'legend') + svg(W, H, s, 'implied vol term structure'), 'A curve falling from left to right prices more movement now than later.') +
    (lad2.length ? fig(k0 + ' dealer gamma by strike, $B · ' + day(m.as_of || asof), hbars(W, lad2.map(x => ({label: (Number.isInteger(x.strike) ? String(x.strike) : x.strike.toFixed(1)) + (isN(m.spot) && Math.abs(x.strike - m.spot) / m.spot < 0.003 ? ' ◂' : ''), value: x.net_gex_b, text: (x.net_gex_b > 0 ? '+' : '') + x.net_gex_b.toFixed(2)})), {lw: 70, signed: 1, rh: 18}),
      'Green strikes damp moves (dealers sell rallies, buy dips); red strikes speed them up.') : '');
}
// the Chart Read counts, one pill at a time: the pills' joined text ran the last count into the "1,789 of the 1,838" line
// below them ("Strong · 1031,789"), so the gauge read 100% for (T-212)
function readCnt() {
  const c = {}, e = D.getElementById('lu-read'); (e && e.querySelectorAll ? e.querySelectorAll('.lu-pill') : []).forEach(p => { const m = (p.textContent || '').trim().match(/^(Against|Leaning|For|Strong) · ([\d,]+)$/); if (m) c[m[1]] = +m[2].replace(/,/g, ''); });
  return c;
}
P['h-read'] = () => {
  const r = (ED().ranked || []).filter(x => isN(x.evidence)).slice(0, 12), W = width('h-read'), cnt = readCnt();
  const dist = Object.keys(cnt).length ? fig('The roster’s charts today: evidence against or for', stack(W, [{label: 'Roster', parts: [{v: cnt.Against || 0, cls: 'vz-d'}, {v: cnt.Leaning || 0, cls: 'vz-q'}, {v: cnt.For || 0, cls: 'vz-u2'}, {v: cnt.Strong || 0, cls: 'vz-u'}]}],
    [['Against', 'vz-d'], ['Leaning', 'vz-q'], ['For', 'vz-u2'], ['Strong', 'vz-u']], {pct: 1, lw: 60})) : '';
  const tot = Object.values(cnt).reduce((a, b) => a + b, 0);
  const un = ((D.getElementById('lu-unread') || {}).textContent || '').match(/^([\d,]+) of the ([\d,]+) roster/);   /* audit 5 F9: the shares are of the read charts, not of the roster */
  return (tot ? RD(pc(100 * ((cnt.For || 0) + (cnt.Strong || 0)) / tot) + ' of charts read for, ' + pc(100 * (cnt.Against || 0) / tot) + ' against' + (un ? ' (' + un[1] + ' of the ' + un[2] + ' roster names have a read)' : '') + '.' + (r.length ? ' Strongest: ' + r.slice(0, 4).map(x => x.symbol).join(', ') + '.' : '')) : '') + dist + (r.length ? fig('Strongest chart evidence today', hbars(W, r.map(x => ({label: x.symbol, value: x.evidence, text: x.evidence.toFixed(1) + ' · ' + (x.take || ''), cls: x.take === 'Strong' ? 'vz-u' : 'vz-u2'})), {lw: 60})) : '') + readLevels(r, W);
};
// each of the strongest names: today's close against its 50-day, 200-day and 52-week high
function readLevels(r, W) {
  const rows = r.map(x => [x, uniRow(x.symbol)]).filter(([, u]) => u && isN(u.close)).slice(0, 6);
  if (!rows.length) return '';
  return fig('The strongest charts: close against their levels', rows.map(([x, u]) => {
    const c = u.close, hi = isN(u.below_high) ? c / (1 - Math.abs(u.below_high) / 100) : null, m50 = isN(u.vs50) ? c / (1 + u.vs50 / 100) : null, m200 = isN(u.vs200) ? c / (1 + u.vs200 / 100) : null;
    const vs = [c, hi, m50, m200].filter(isN), lo = Math.min(...vs), top = Math.max(...vs), pad = (top - lo) * 0.06 || c * 0.02;
    return levels(W, x.symbol + ' · ' + (x.take || '') + ' ' + (isN(x.evidence) ? x.evidence.toFixed(1) : ''), lo - pad, top + pad,
      [{v: c, k: 'Close', cls: 'vz-sp', side: 'up', dot: 1}, ...(isN(hi) ? [{v: hi, k: '52-wk high', cls: 'vz-mu', side: 'dn'}] : []),
       ...(isN(m50) ? [{v: m50, k: '50-day', cls: 'vz-mf', side: 'dn'}] : []), ...(isN(m200) ? [{v: m200, k: '200-day', cls: 'vz-md', side: 'dn'}] : [])]);
  }).join(''), 'Where each close sits against its 50-day, 200-day and 52-week high; the rating weighs every lens, so a Strong name can sit below an average.');
}
P['clrank'] = () => {
  const L0 = ED().lector, r = (L0 && L0.rows) || [];
  if (!r.length) return '';
  return RD('Top Opportunity Scores: ' + r.slice(0, 4).map(x => x.symbol + ' ' + x.score).join(', ') + '.') + fig('ChartsLector Opportunity Score, top names', stack(width('clrank'), r.slice(0, 12).map(x => ({label: x.symbol, parts: (x.parts || []).map((v, i) => ({v: Math.round(v / 3), cls: ['vz-u', 'vz-n', 'vz-u2'][i]}))})),
    [['Breakout', 'vz-u'], ['Expansion', 'vz-n'], ['Risk', 'vz-u2']], {lw: 60}));
};
// the Opportunity Ranker (GrokBot's ranker, ChartsLector's score): one row per name, the score bar with its three parts
// below it and the change since the prior session
P['hub'] = () => {
  const L0 = ED().lector, r = ((L0 && L0.rows) || []).filter(x => isN(x.score)).slice(0, 15);
  if (!r.length) return '';
  // the ranker's rows stretch to the card (audit 5 F14): at the 760 cap the 1400 page letterboxed it into a narrow centred block
  const W = Math.max(300, Math.min(1400, ((D.getElementById('hub') || {}).clientWidth || 360) - 34)), lw = 64, rw = 92, vw = W - lw - rw, rh = 30, H = r.length * rh + 8;
  let s = r.map((x, i) => {
    const y = 4 + i * rh, p = x.parts || [], d = x.delta;
    const sub = [[p[0], 'vz-u'], [p[1], 'vz-a'], [p[2], 'vz-n']].map(([v, c], k) => isN(v) ? R(lw + k * vw / 3, y + 19, Math.max(1, v / 100 * (vw / 3 - 6)), 4, c) : '').join('');
    return T(lw - 8, y + 14, x.symbol, 'vz-lb', 'end') + R(lw, y + 4, vw, 12, 'vz-tr') + R(lw, y + 4, x.score / 100 * vw, 12, 'vz-sc') + sub +
      T(lw + vw + 8, y + 15, x.score.toFixed(1), 'vz-v') + (isN(d) ? T(W - 4, y + 15, (d > 0 ? '+' : d < 0 ? '−' : '') + Math.abs(d).toFixed(1), d > 0 ? 'vz-vu' : d < 0 ? 'vz-vd' : 'vz-k', 'end') : '');
  }).join('');
  const up = r.filter(x => isN(x.delta) && x.delta > 0).sort((a, b) => b.delta - a.delta)[0];
  return RD('Top opportunity: ' + r.slice(0, 3).map(x => x.symbol + ' ' + x.score.toFixed(0)).join(', ') + '.' + (up ? ' Biggest riser: ' + up.symbol + ' +' + up.delta.toFixed(1) + '.' : '')) +
    fig('Opportunity score 0–100, with its breakout, expansion and risk parts', svg(W, H, s, 'opportunity ranker') +
      (lg => svg(W, lg[1] + 8, lg[0], 'legend'))(legend([['Score', 'vz-sc'], ['Breakout', 'vz-u'], ['Expansion', 'vz-a'], ['Risk (higher = cleaner)', 'vz-n']], 4, 4, W)),
      'Right column: change in score since the prior session.');
};

// ---- the headline gauge (after the GrokBot desk's Mood Ring): a segmented arc, a needle, the big number and its word ------
function gauge(g) {
  if (!g || !isN(g.v)) return '';
  const W = 260, H = 176, cx = W / 2, cy = 138, ro = 104, ri = 74, lo = g.min, hi = g.max, A = v => Math.PI * (1 - (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo));
  const pt = (a, r) => f1(cx + r * Math.cos(a)) + ' ' + f1(cy - r * Math.sin(a));
  let s = g.zones.map(([a, b, c]) => { const a0 = A(a) - 0.012, a1 = A(b) + 0.012;
    return '<path class="' + c + '" d="M' + pt(a0, ro) + ' A' + ro + ' ' + ro + ' 0 0 1 ' + pt(a1, ro) + ' L' + pt(a1, ri) + ' A' + ri + ' ' + ri + ' 0 0 0 ' + pt(a0, ri) + 'Z"/>'; }).join('');
  s += g.zones.slice(1).map(([a]) => T(cx + (ro + 10) * Math.cos(A(a)), cy - (ro + 10) * Math.sin(A(a)) + 3, String(a) + (g.unit || ''), 'vz-k', 'middle')).join('');
  const av = A(g.v);
  s += '<line class="vz-nd" x1="' + cx + '" y1="' + cy + '" x2="' + pt(av, ro - 6).replace(' ', '" y2="') + '"/>' + C(cx, cy, 6, 'vz-ndc');
  const z = g.zones.find(([a, b]) => g.v >= a && g.v <= b) || g.zones[g.v < lo ? 0 : g.zones.length - 1];
  return '<div class="vz-g">' + svg(W, H, s + T(cx, cy + 34, g.big, 'vz-gbig', 'middle'), g.label + ' ' + g.big) +
    '<div class="vz-gl"><span class="vz-pill ' + z[2] + '">' + esc(z[3]) + '</span><p class="vz-gk">' + esc(g.label) + '</p>' + (g.sub ? '<p class="vz-nt">' + esc(g.sub) + '</p>' : '') +
    (g.parts || []).map(([k, v, t, pc0]) => '<div class="vz-wb"><div class="vz-wbh"><span>' + esc(k) + '</span><b>' + esc(t) + '</b></div><svg class="vz-wbt" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true"><rect class="vz-tr" width="100" height="6" rx="3"/><rect class="' + (pc0 || 'vz-u') + '" width="' + Math.max(1, Math.min(100, isN(v) ? v : 0)).toFixed(1) + '" height="6" rx="3"/></svg></div>').join('') + '</div></div>';
}
const Z4 = (a, b, c, d, e, w) => [[a, b, 'vz-g1', w[0]], [b, c, 'vz-g2', w[1]], [c, d, 'vz-g3', w[2]], [d, e, 'vz-g4', w[3]]];
const GZ = {
  'h-gaps': () => { const g = LU && LU.gap_fill, r = g && g.by_size && g.by_size[0]; if (!r) return null; const v = (r.up.filled_pct + r.down.filled_pct) / 2;
    return {v, min: 0, max: 100, big: pc(v), label: 'Same-day fill odds, ' + r.size + ' gaps', zones: Z4(0, 30, 50, 70, 100, ['respect', 'lean respect', 'lean fade', 'fade']),
      parts: g.by_size.map(x => [x.size + ' gaps', (x.up.filled_pct + x.down.filled_pct) / 2, pc((x.up.filled_pct + x.down.filled_pct) / 2)])}; },
  'h-corr': () => { const w = LU && LU.correlation_web, ps = w && (w.pairs || []).filter(p => p.r < 0.99); if (!ps || !ps.length) return null; const cl = (w.clusters || []).slice().sort((a, b) => b.size - a.size);
    const n = cl.reduce((a, c) => a + c.size, 0), v = n ? 100 * cl[0].size / n : 0;
    return {v, min: 0, max: 100, big: pc(v), label: 'Share of linked names in the biggest group', zones: Z4(0, 25, 40, 60, 100, ['spread', 'mixed', 'crowded', 'one bet']).map(z => [z[0], z[1], ['vz-g4', 'vz-g3', 'vz-g2', 'vz-g1'][['vz-g1', 'vz-g2', 'vz-g3', 'vz-g4'].indexOf(z[2])], z[3]]),
      parts: cl.slice(0, 4).map(c => [c.members.slice(0, 3).join(' '), 100 * c.size / (n || 1), c.size + ' names'])}; },
  'h-optdata': () => { const ms = ((ED().options_data || {}).memos || []).filter(m => isN(m.atm_iv)), ch = ((ED().morgue || {}).chain || {}).cards || {};
    const row = ms.length ? ms.map(m => [m.symbol, m.atm_iv]) : ['SPY', 'QQQ', 'IWM'].filter(k => ch[k] && isN(ch[k].iv30)).map(k => [k, ch[k].iv30]);
    if (!row.length) return null; const v = 100 * row[0][1];
    return {v, min: 5, max: 45, big: pc(v, 1), label: row[0][0] + (ms.length ? ' at-the-money implied vol' + (ms[0].expiry ? ', ' + day(ms[0].expiry) + ' expiry' : '') : ' 30-day implied vol'), zones: Z4(5, 15, 20, 30, 45, ['calm', 'normal', 'elevated', 'stressed']).map(z => [z[0], z[1], ['vz-g4', 'vz-g3', 'vz-g2', 'vz-g1'][['vz-g1', 'vz-g2', 'vz-g3', 'vz-g4'].indexOf(z[2])], z[3]]),
      parts: row.map(([k, iv]) => [k, iv * 100 / 0.45, pc(iv * 100, 1)])}; },
  'h-read': () => { const c = readCnt();
    const tot = Object.values(c).reduce((a, b) => a + b, 0); if (!tot) return null; const v = 100 * ((c.For || 0) + (c.Strong || 0)) / tot;
    return {v, min: 0, max: 100, big: pc(v), label: 'Charts reading for', zones: Z4(0, 35, 50, 65, 100, ['weak tape', 'mixed', 'constructive', 'strong tape']),
      parts: [['Strong', 100 * (c.Strong || 0) / tot, String(c.Strong || 0)], ['For', 100 * (c.For || 0) / tot, String(c.For || 0)], ['Leaning', 100 * (c.Leaning || 0) / tot, String(c.Leaning || 0)], ['Against', 100 * (c.Against || 0) / tot, String(c.Against || 0), 'vz-d']]}; },
  'h-lineup': () => { const r = LU && (LU.expected_move || {}).record; if (!r || !r.SPY || !isN(r.SPY.last250_pct)) return null; const v = r.SPY.last250_pct;
    return {v, min: 40, max: 100, big: pc(v), label: 'SPY closes inside its expected move, last 250 sessions', zones: Z4(40, 60, 68, 80, 100, ['too narrow', 'narrow', 'on target', 'wide']),
      parts: Object.keys(r).map(k => [k, r[k].last250_pct, pc(r[k].last250_pct)])}; },
  'hub': () => { const r = ((ED().lector || {}).rows || []).filter(x => isN(x.score)); if (!r.length) return null; const p = r[0].parts || [];
    return {v: r[0].score, min: 0, max: 100, big: r[0].score.toFixed(0), label: r[0].symbol + ' score and its parts', zones: Z4(0, 25, 45, 65, 100, ['thin', 'building', 'good', 'prime']),
      parts: [['Breakout', p[0], f1(p[0] || 0)], ['Expansion', p[1], f1(p[1] || 0)], ['Risk (higher = cleaner)', p[2], f1(p[2] || 0)]].filter(x => isN(x[1]))}; },
  'e-rank': () => { if (!ENG || !ENG.rows) return null; const ix = {}; ENG.cols.forEach((c, i) => { ix[c] = i; });
    const R0 = ENG.rows.filter(r => isN(r[ix.mom]) && isN(r[ix.risk])); if (!R0.length) return null; const n = R0.length, ok = R0.filter(r => r[ix.mom] >= 70 && r[ix.risk] <= 30).length, wk = R0.filter(r => r[ix.mom] <= 30 && r[ix.risk] >= 70).length, v = 100 * ok / n;
    return {v, min: 0, max: 20, unit: '%', big: pc(v, 1), label: 'Names strong and low-risk', sub: ok + ' of ' + n.toLocaleString('en-US') + ' names the engine screens', zones: Z4(0, 3, 6, 10, 20, ['scarce', 'thin', 'healthy', 'broad']),
      parts: [['Strong and safe', 100 * ok / n * 5, String(ok)], ['Weak and risky', 100 * wk / n * 5, String(wk), 'vz-d']]}; },
  'e-fc': () => { const es = ((ED().forecasts || {}).engines || []).filter(e => e.latest && fcUp(e)); if (!es.length) return null; const v = 100 * es[0].latest.value;
    return {v, min: 0, max: 100, big: pc(v), label: (es[0].latest.subject || es[0].name) + ' chance of finishing higher', zones: Z4(0, 40, 50, 60, 100, ['bearish', 'lean lower', 'lean higher', 'bullish']),
      parts: es.map(e => [(e.latest.subject || e.name) + ' · ' + e.name, 100 * e.latest.value, pc(100 * e.latest.value)])}; },
};
Object.keys(GZ).forEach(id => { const f0 = P[id]; P[id] = () => { const h = f0(); if (!h) return h; let g = ''; try { g = gauge(GZ[id]()); } catch (e) { g = ''; }
  const i = h.indexOf('</p>'); return g && h.startsWith('<p class="vz-r">') ? h.slice(0, i + 4) + g + h.slice(i + 4) : g + h; }; });

// ---- mounting: one figure per panel, redrawn when its data or width changes ----------------------------------------------
const HOST = {'f-map': '.card', 'f-wire': '.card', 'e-rank': '.card', 'e-fc': null, 'h-lineup': '#lu-body', 'h-gaps': '#lu-gap', 'h-corr': '#lu-corr',
  'h-optdata': '#od-body', 'h-read': '#lu-read', 'hub': '#hub-rank', 'clrank': '#clrankc'};
// a panel whose data is missing now shows its last real chart, stamped with its age, never a blank (per viewer, localStorage)
const ago = t => { const m = Math.round((Date.now() - t) / 6e4); return m < 90 ? m + ' min ago' : m < 2880 ? Math.round(m / 60) + ' h ago' : Math.round(m / 1440) + ' days ago'; };
function keep(id, h) {
  try {
    if (h) { localStorage.setItem('vze:' + id, JSON.stringify({t: Date.now(), h})); return h; }
    const c = JSON.parse(localStorage.getItem('vze:' + id) || 'null');
    return c && c.h ? '<p class="vz-age">Last reading, ' + esc(ago(c.t)) + '</p>' + c.h : '';
  } catch (e) { return h; }
}
let busy = false;
function mount() {
  engNeed();
  busy = true;
  try {
    Object.keys(P).forEach(id => {
      const sec = D.getElementById(id);
      if (!sec || sec.hidden) return;
      let h = '';
      try { h = P[id](); } catch (e) { console.warn('vz', id, e); h = ''; }
      h = keep(id === 'h-lineup' ? 'h-lineup:' + ((D.querySelector('#h-lineup [data-k][aria-pressed="true"]') || {dataset: {}}).dataset.k || 'or') : id, h);
      let f = sec.querySelector(':scope figure.vze');
      if (!h) { if (f) f.remove(); return; }
      if (f && f._h === h) return;
      if (!f) {
        f = D.createElement('figure');
        f.className = 'vze';
        f.dataset.vze = id;
        const host = HOST[id] && sec.querySelector(HOST[id]);
        if (host && HOST[id].startsWith('#')) host.parentNode.insertBefore(f, host);
        else if (host) host.insertBefore(f, host.firstChild);
        else { const hd = sec.querySelector('.shd'); hd ? hd.after(f) : sec.prepend(f); }
      }
      f.innerHTML = h;
      f._h = h;
    });
  } finally { setTimeout(() => { busy = false; }, 0); }
}
let tm = 0;
const soon = () => { if (!tm) tm = setTimeout(() => { tm = 0; mount(); }, 150); };   // a throttle: the page's own timers mutate the DOM every second
const get = u => fetch(u, {cache: 'no-cache'}).then(r => r.ok ? r.json() : null).catch(() => null);
// the lineup arrives with lineup.js (loaded when the Hub opens); the engine screen when the Engine tab first shows
D.addEventListener('md:lineup', e => { const j = e.detail; LU = j && j.schema ? j : null; soon(); });
let eng0 = false;
const engNeed = () => { const s = D.getElementById('e-rank'); if (eng0 || !s || s.offsetParent === null) return; eng0 = true; get('engine.json').then(j => { ENG = j && Array.isArray(j.cols) ? j : null; soon(); }); };
D.addEventListener('md:edition', soon);
D.addEventListener('md:tab', soon);
D.addEventListener('click', e => { if (e.target.closest('#h-lineup [data-k]')) soon(); });
addEventListener('resize', soon);
new MutationObserver(ms => { if (!busy && ms.some(m => !(m.target.closest && m.target.closest('figure.vze')))) soon(); })
  .observe(D.getElementById('main') || D.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['hidden']});
window.VZE = {panels: Object.keys(P), tools: Object.keys(LT), mount, render: id => P[id](), tool: (k, w) => LT[k](w || 600), data: (lu, eng) => { LU = lu; ENG = eng; }};
soon();
})();
