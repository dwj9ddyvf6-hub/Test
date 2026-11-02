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
const sp = (v, d = 1) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d) + '%' : '—';
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
  const lw = Math.min(o.lw || 110, W * 0.36), rh = o.rh || 22, H = rows.length * rh + 6, tw = Math.max(48, ...rows.map(r => String(r.text != null ? r.text : r.value).length * 6.4 + 10)), vw = W - lw - tw;
  const vals = rows.map(r => r.value).filter(isN), signed = o.signed || vals.some(v => v < 0);
  const mx = o.max || Math.max(1e-9, ...vals.map(Math.abs)), z = signed ? lw + vw / 2 : lw, sc = signed ? vw / 2 / mx : vw / mx;
  return svg(W, H, rows.map((r, i) => {
    const y = 3 + i * rh, v = isN(r.value) ? r.value : 0, w = Math.abs(v) * sc, x = v >= 0 ? z : z - w;
    return T(lw - 6, y + rh * 0.62, fit(r.label, lw - 8), 'vz-t', 'end') + R(x, y + 3, Math.max(1, w), rh - 8, r.cls || (v >= 0 ? 'vz-u' : 'vz-d')) +
      T((v >= 0 ? x + w : z) + 5 + (signed && v < 0 ? 0 : 0), y + rh * 0.62, r.text != null ? r.text : String(v), 'vz-v');
  }).join('') + (signed ? L(z, 0, z, H, 'vz-z') : ''), o.label || 'bars');
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
  const a = 14, b = W - 14, X = v => a + (v - lo) / (hi - lo || 1) * (b - a), est = m => (m.k.length + 8) * 6.2;
  // labels never overlap: each side's labels take the first free line above (or below) the axis
  const place = side => { const lines = []; return marks.filter(m => (m.side !== 'dn') === (side === 'up')).sort((p, q) => X(p.v) - X(q.v)).map(m => {
    const x = X(m.v), w = est(m), x0 = Math.min(b - w, Math.max(a, x - w / 2));
    let i = 0; while (lines[i] != null && lines[i] > x0 - 4) i++;
    lines[i] = x0 + w; return {m, x, x0, i};
  }); };
  const up = place('up'), dn = place('dn'), nu = Math.max(1, ...up.map(p => p.i + 1)), nd = Math.max(1, ...dn.map(p => p.i + 1));
  const y = 24 + nu * 13, H = y + 12 + nd * 13;
  let s = T(a, 12, title, 'vz-h3') + (zones || []).map(z => R(X(Math.min(z.a, z.b)), y - 7, Math.abs(X(z.b) - X(z.a)), 14, z.cls)).join('') + L(a, y, b, y, 'vz-z');
  [...up, ...dn].forEach(p => { s += p.m.dot ? C(p.x, y, 6, p.m.cls) : L(p.x, y - 10, p.x, y + 10, p.m.cls); });
  up.forEach(p => { s += T(p.x0, y - 12 - p.i * 13, p.m.k + ' ' + px(p.m.v), 'vz-k'); });
  dn.forEach(p => { s += T(p.x0, y + 22 + p.i * 13, p.m.k + ' ' + px(p.m.v), 'vz-k'); });
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
    return levels(W, c.symbol + ' · ' + (c.regime || '') + (isN(c.net_gex_b) ? ' · net gamma ' + c.net_gex_b.toFixed(1) + 'B' : ''), lo, hi, [
      isN(c.put_wall) && {v: c.put_wall, k: 'Put wall', cls: 'vz-md', side: 'dn'}, isN(c.call_wall) && {v: c.call_wall, k: 'Call wall', cls: 'vz-mu', side: 'dn'},
      isN(c.flip) && {v: c.flip, k: 'Flip', cls: 'vz-mf', side: 'up'}, {v: c.spot, k: 'Spot', cls: 'vz-sp', side: 'up', dot: 1}].filter(Boolean), amp);
  }).join(''), 'Red: below the gamma flip, moves tend to speed up. Green: above it, moves tend to calm. The walls are where dealers defend.');
};
P['f-board'] = () => {
  const b = (ED().funnel || {}).board || {}, rows = (b.rows || []).filter(r => r.ladder);
  const W = width('f-board');
  if (rows.length) return RD(rows.length + (rows.length === 1 ? ' name qualifies' : ' names qualify') + ' today: ' + rows.slice(0, 4).map(r => r.symbol).join(', ') + '.') + fig('Each qualified name: buy, stop and targets', rows.slice(0, 8).map(r => {
    const l = r.ladder || {}, pts = [l.stop, l.entry_low, l.entry_high, l.entry, ...(l.targets || []).map(t => isN(t) ? t : t && t.price)].filter(isN);
    if (!pts.length) return '';
    const lo = Math.min(...pts, r.close || Infinity) * 0.99, hi = Math.max(...pts, r.close || 0) * 1.01;
    return levels(W, r.symbol + ' · ' + (r.label || ''), lo, hi, [isN(l.stop) && {v: l.stop, k: 'Stop', cls: 'vz-md', side: 'dn'},
      isN(l.entry || l.entry_low) && {v: l.entry || l.entry_low, k: 'Buy', cls: 'vz-mf', side: 'up'},
      ...(l.targets || []).map((t, i) => ({v: isN(t) ? t : t && t.price, k: 'T' + (i + 1), cls: 'vz-mu', side: 'dn'})).filter(m => isN(m.v)),
      isN(r.close) && {v: r.close, k: 'Now', cls: 'vz-sp', side: 'up', dot: 1}].filter(Boolean),
      isN(l.stop) && isN(l.entry || l.entry_low) ? [{a: l.stop, b: l.entry || l.entry_low, cls: 'vz-zd'}] : []);
  }).join(''));
  const hz = ((ED().funnel || {}).scoring || {}).horizons || [], g = hz.map(h => { const m = /([\d.]+)% positive, average ([+−-]?[\d.]+)%/.exec(h.line || ''); return m ? {h: h.h, pos: +m[1], avg: +m[2].replace('−', '-')} : null; }).filter(Boolean);
  if (!g.length) return '';
  const g1 = g[0];
  return RD('No name qualifies today. Past board names rose ' + pc(g1.pos) + ' of the time a day later, ' + sp(g1.avg, 2) + ' on average.') + fig('Past board names: rose or fell afterwards', stack(W, g.map(x => ({label: x.h.replace('d', ' day') + ' later', parts: [{v: x.pos, cls: 'vz-u'}, {v: 100 - x.pos, cls: 'vz-d'}]})),
    [['Rose', 'vz-u'], ['Fell', 'vz-d']], {pct: 1, lw: 90}), 'Average move afterwards: ' + g.map(x => x.h + ' ' + sp(x.avg, 2)).join(' · ') + '.');
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
    'Each bar is the premium paid in sweeps that met the rule. Green: calls (a bet on higher). Red: puts (a bet on lower).');
};
let ENG = null, LU = null;
P['e-rank'] = () => {
  if (!ENG || !ENG.rows) return '';
  const ix = {}; ENG.cols.forEach((c, i) => { ix[c] = i; });
  const pts = ENG.rows.map(r => ({s: r[ix.sym], m: r[ix.mom], k: r[ix.risk], t: r[ix.tier], v: r[ix.veto]})).filter(p => isN(p.m) && isN(p.k));
  if (!pts.length) return '';
  const W = width('e-rank'), H = Math.round(Math.min(360, W * 0.7)), a = 34, b = W - 10, t = 10, bt = H - 30;
  const X = m => a + m / 100 * (b - a), Y = k => t + k / 100 * (bt - t);
  const best = pts.filter(p => !p.v).sort((p, q) => (q.m - q.k) - (p.m - p.k)).slice(0, 8);
  let s = R(X(70), Y(0), X(100) - X(70), Y(30) - Y(0), 'vz-zu') + R(X(0), Y(70), X(30) - X(0), Y(100) - Y(70), 'vz-zd') +
    L(a, bt, b, bt, 'vz-z') + L(a, t, a, bt, 'vz-z') + T((a + b) / 2, H - 6, 'Momentum rank → stronger', 'vz-k', 'middle') +
    '<text class="vz-k" transform="rotate(-90)" x="' + f1(-(t + bt) / 2) + '" y="12" text-anchor="middle">Loser risk ↓ riskier</text>' +
    T(X(85), Y(4) + 8, 'Strong and safe', 'vz-kb', 'middle') + T(X(15), Y(96) - 2, 'Weak and risky', 'vz-kb', 'middle');
  s += pts.map(p => C(X(p.m), Y(p.k), 1.6, p.v ? 'vz-pd' : 'vz-p')).join('');
  s += best.map(p => C(X(p.m), Y(p.k), 4, 'vz-sp')).join('');
  const ss = pts.filter(p => p.m >= 70 && p.k <= 30).length;
  return RD(ss + ' names are strong and low-risk (momentum 70+, loser risk 30 or less). Leaders: ' + best.slice(0, 4).map(p => p.s).join(', ') + '.') + fig('Every name: momentum against loser risk', svg(W, H, s, 'momentum against loser risk'), 'Top right is where the best long candidates sit; the dark dots are the leaders below.') +
    fig('Leaders: momentum rank (bar) and loser risk', hbars(W, best.map(p => ({label: p.s, value: p.m, text: 'momentum ' + p.m + ' · risk ' + p.k, cls: 'vz-u'})), {lw: 60, max: 100}));
};
P['e-fc'] = () => {
  const es = ((ED().forecasts || {}).engines || []).filter(e => e.latest && isN(+e.latest.value));
  if (!es.length) return '';
  const W = width('e-fc'), q = e => String(e.latest.quantity || ''), hz = e => { const m = /(\d+)\s*d/.exec(q(e)); return m ? m[1] + (m[1] === '1' ? ' day' : ' days') : 'the horizon'; };
  const isP = e => /prob|chance|p_up|up_/.test(q(e)) && +e.latest.value <= 1, sub = e => e.latest.subject || e.name;
  const P0 = es.filter(isP), V0 = es.filter(e => !isP(e));
  const say = e => isP(e) ? sub(e) + ': ' + pc(100 * e.latest.value) + ' chance higher over ' + hz(e) : sub(e) + ': ' + sp(+e.latest.value) + ' expected over ' + hz(e);
  return RD(es.slice(0, 3).map(say).join(' · ') + '.') +
    (P0.length ? fig('Chance of finishing higher (50% = a coin flip)', hbars(W, P0.map(e => ({label: sub(e) + ' · ' + hz(e), value: 100 * e.latest.value - 50, text: pc(100 * e.latest.value), cls: e.latest.value >= 0.5 ? 'vz-u' : 'vz-d'})), {lw: 120, max: 50, signed: 1})) : '') +
    (V0.length ? fig('Expected move', hbars(W, V0.map(e => ({label: sub(e) + ' · ' + hz(e), value: +e.latest.value, text: sp(+e.latest.value)})), {lw: 120})) : '');
};
// the desk lineup: one chart per tool, the tool chosen on the panel
const LT = {
  or(W) {
    const w = (LU.opening_range || {}).windows || [];
    const h = w[w.length - 1] || {};
    return RD(h.label ? h.label + ': only the high broke ' + pc(h.up_only_pct) + ', only the low ' + pc(h.down_only_pct) + ', both ' + pc(h.both_pct) + ' of days.' : '') + fig('After the first minutes: which side broke', stack(W, w.map(x => ({label: x.label.replace('First ', ''), parts: [{v: x.up_only, cls: 'vz-u'}, {v: x.down_only, cls: 'vz-d'}, {v: x.both, cls: 'vz-n'}, {v: x.neither, cls: 'vz-q'}]})),
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
    const z = lv[0];
    return RD(z.symbol + ' next session: two days in three between ' + px(z.bands['68'][0]) + ' and ' + px(z.bands['68'][1]) + ' (close ' + px(z.close) + ').') + fig('Where price should land: the corrected bands', lv.map(x => {
      const b = x.bands, lo = b['95'][0], hi = b['95'][1];
      return levels(W, x.symbol + ' · ' + x.h + (x.h === 1 ? ' session' : ' sessions') + ' ahead', lo * 0.998, hi * 1.002, [{v: b['68'][0], k: '68% low', cls: 'vz-md', side: 'dn'}, {v: b['68'][1], k: '68% high', cls: 'vz-mu', side: 'dn'},
        {v: x.close, k: 'Close', cls: 'vz-sp', side: 'up', dot: 1}], [{a: b['95'][0], b: b['95'][1], cls: 'vz-zq'}, {a: b['68'][0], b: b['68'][1], cls: 'vz-zn'}]);
    }).join(''), 'Inner band: two days in three. Outer band: 19 days in 20.');
  },
  sc(W) {
    const c = (LU.strat_combos || {}).completed || [];
    return RD(c[0] ? 'Most common completed pattern: ' + c[0].pattern + ' on ' + c[0].count + ' names.' : '') + fig('Strat patterns that completed on the last session', hbars(W, c.slice(0, 10).map(x => ({label: x.pattern.slice(0, 22), value: x.count, cls: /2d|2D|down/.test(x.pattern.split(' ').pop()) ? 'vz-d' : 'vz-u'})), {lw: 160}));
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
    return RD((f.latest && f.latest.fear ? 'Today is a fear day. ' : 'Not a fear day. ') + 'After past fear days SPY rose ' + pc(a21.positive_pct) + ' of the time ' + a21.h + ' days later, median ' + sp(a21.median_pct) + '.') + fig('After a fear day: how often SPY was higher', stack(W, a.map(x => ({label: x.h + 'd later', parts: [{v: x.positive_pct, cls: 'vz-u'}, {v: 100 - x.positive_pct, cls: 'vz-d'}]})),
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
  wl(W) { return uni(W, 'The roster: 3-month move against distance from the high'); },
};
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
    'Top right: names up the most over three months and still at their highs. The dark dots are the leaders below.') +
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
  const W = width('h-corr'), H = Math.round(Math.min(380, W * 0.75)), cx = W / 2, cy = H / 2, rad = Math.min(cx, cy) - 40;
  const ps = w.pairs.filter(p => p.r < 0.99).slice(0, 14), ns = [...new Set(ps.flatMap(p => [p.a, p.b]))], pos = {};
  ns.forEach((n, i) => { const t = i / ns.length * 2 * Math.PI - Math.PI / 2; pos[n] = [cx + rad * Math.cos(t), cy + rad * Math.sin(t)]; });
  let s = ps.map(p => '<line class="vz-ed" x1="' + f1(pos[p.a][0]) + '" y1="' + f1(pos[p.a][1]) + '" x2="' + f1(pos[p.b][0]) + '" y2="' + f1(pos[p.b][1]) + '" stroke-width="' + f1(1 + (p.r - 0.8) * 15) + '"/>').join('');
  s += ns.map(n => C(pos[n][0], pos[n][1], 5, 'vz-sp') + T(pos[n][0] + (pos[n][0] < cx ? -8 : 8), pos[n][1] + 4, n, 'vz-lb', pos[n][0] < cx ? 'end' : 'start')).join('');
  const cl = w.clusters || [];
  const big = cl.slice().sort((a, b) => b.size - a.size)[0];
  return RD('Tightest pair: ' + ps[0].a + ' and ' + ps[0].b + ' (r ' + (+ps[0].r).toFixed(2) + ').' + (big ? ' Biggest group: ' + big.size + ' names led by ' + big.members.slice(0, 3).join(', ') + ' — treat them as one bet.' : '')) + fig('Names that move together (thicker line = tighter link)', svg(W, H, s, 'correlation network')) +
    (cl.length ? fig('Groups that trade as one', hbars(W, cl.map(c => ({label: c.members.slice(0, 3).join(' '), value: c.size, text: c.size + ' names', cls: 'vz-n'})), {lw: 150})) : '');
};
P['h-optdata'] = () => {
  const ms = ((ED().options_data || {}).memos || []).filter(m => isN(m.spot) && isN(m.lower) && isN(m.upper));
  if (!ms.length) return '';
  const W = width('h-optdata');
  return RD(ms.map(m => m.symbol + ' ' + px(m.lower) + '–' + px(m.upper) + (isN(m.move_pct) ? ' (±' + m.move_pct.toFixed(1) + '%)' : '')).slice(0, 3).join(' · ')) + fig('Options-implied range to the next expiry', ms.map(m => levels(W, m.symbol + (isN(m.move_pct) ? ' · ±' + m.move_pct.toFixed(2) + '%' : '') + (isN(m.atm_iv) ? ' · IV ' + (m.atm_iv * 100).toFixed(0) + '%' : ''),
    m.lower * 0.995, m.upper * 1.005, [{v: m.lower, k: 'Low', cls: 'vz-md', side: 'dn'}, {v: m.upper, k: 'High', cls: 'vz-mu', side: 'dn'}, {v: m.spot, k: 'Spot', cls: 'vz-sp', side: 'up', dot: 1}], [{a: m.lower, b: m.upper, cls: 'vz-zn'}])).join(''),
    'The band the at-the-money straddle prices in: where the options market expects price by that expiry.');
};
P['h-read'] = () => {
  const r = (ED().ranked || []).filter(x => isN(x.evidence)).slice(0, 12), W = width('h-read'), txt = (D.getElementById('lu-read') || {}).textContent || '';
  const cnt = {}; (txt.match(/(Against|Leaning|For|Strong) · ([\d,]+)/g) || []).forEach(m => { const [w, n] = m.split(' · '); cnt[w] = +n.replace(/,/g, ''); });
  const dist = Object.keys(cnt).length ? fig('The roster’s charts today: evidence against or for', stack(W, [{label: 'Roster', parts: [{v: cnt.Against || 0, cls: 'vz-d'}, {v: cnt.Leaning || 0, cls: 'vz-q'}, {v: cnt.For || 0, cls: 'vz-u2'}, {v: cnt.Strong || 0, cls: 'vz-u'}]}],
    [['Against', 'vz-d'], ['Leaning', 'vz-q'], ['For', 'vz-u2'], ['Strong', 'vz-u']], {pct: 1, lw: 60})) : '';
  const tot = Object.values(cnt).reduce((a, b) => a + b, 0);
  return (tot ? RD(pc(100 * ((cnt.For || 0) + (cnt.Strong || 0)) / tot) + ' of charts read for, ' + pc(100 * (cnt.Against || 0) / tot) + ' against.' + (r.length ? ' Strongest: ' + r.slice(0, 4).map(x => x.symbol).join(', ') + '.' : '')) : '') + dist + (r.length ? fig('Strongest chart evidence today', hbars(W, r.map(x => ({label: x.symbol, value: x.evidence, text: x.evidence.toFixed(1) + ' · ' + (x.take || ''), cls: x.take === 'Strong' ? 'vz-u' : 'vz-u2'})), {lw: 60})) : '');
};
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
  const W = width('hub'), lw = 64, rw = 92, vw = W - lw - rw, rh = 30, H = r.length * rh + 8;
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
P['lrank'] = () => {
  const r = [...(ED().setups || []), ...(ED().watching || [])].filter(x => x.lens && isN(x.lens.c8)).sort((a, b) => b.lens.c8 - a.lens.c8).slice(0, 10);
  return r.length ? RD('Highest conviction: ' + r.slice(0, 3).map(x => x.symbol + ' ' + x.lens.c8).join(', ') + '.') + fig('Conviction across the eight lenses', hbars(width('lrank'), r.map(x => ({label: x.symbol, value: x.lens.c8, text: String(x.lens.c8), cls: 'vz-u'})), {lw: 60})) : '';
};

// ---- mounting: one figure per panel, redrawn when its data or width changes ----------------------------------------------
const HOST = {'f-map': '.card', 'f-board': '.card', 'f-wire': '.card', 'e-rank': '.card', 'e-fc': null, 'h-lineup': '#lu-body', 'h-gaps': '#lu-gap', 'h-corr': '#lu-corr',
  'h-optdata': '#od-body', 'h-read': '#lu-read', 'hub': '#hub-rank', 'clrank': '#clrankc', 'lrank': '#lrankc'};
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
      h = keep(id, h);
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
