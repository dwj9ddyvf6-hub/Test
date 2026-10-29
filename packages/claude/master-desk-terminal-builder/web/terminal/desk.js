/* Master Desk terminal, the Desk tab: the desk's own books, copied from GrokBot's "Main desk" (overview, the curve
   against SPY, open positions, the heatmap, the engine, closed trades, scorecards), and the owner's leaderboard and
   sleeves explorer. Loaded on the tab's first open (#p-desk data-js); data from deskview.json and sleeves.json,
   positions.json only when asked (desk/terminal/deskview.py). Labels use the page's own formatters (window.MD) and the
   data's own words (labels{}); no number the data gives is recomputed. */
(() => {
const D = document, M = window.MD, P = D.getElementById('p-desk'), el = id => D.getElementById(id);
const esc = M.esc, num = M.num, isN = v => typeof v === 'number' && isFinite(v);
const SCH = {d: 'master-desk-deskview/1', s: 'master-desk-sleeves/1', p: 'master-desk-positions/1'};
const KEY = 'md.desk', LIM = 30, GKEY = {family: 'families', cls: 'classes', style: 'styles'};
const CRIT = [['edge', 'Edge'], ['sharpe', 'Sharpe'], ['drawdown', 'Drawdown'], ['beats_spy', 'Beats SPY'], ['regimes', 'Regimes'], ['days30', '30 days']];
let dv = null, sl = null, pj = null, pjP = null, busy = 0, stale = 0, byId = {}, sel = '', cw = 0, hw = 0;
const ui = Object.assign({g: 'family', f: 'all', s: 'ret', o: {}, m: 'both', lv: 'best', pf: 'all', pn: 10, cn: 15, sn: 12, gn: {}}, saved());

// ---- formatters: the page's own (app.js), composed ------------------------------------------------------------------
const pc = (v, dp = 2) => isN(v) ? M.pct(v, dp) : '—';
const tn = v => !isN(v) ? '' : v > 0 ? 'up' : v < 0 ? 'dn' : '';
const n0 = v => isN(v) ? num(v, 0) : '—';
const md = d => d ? M.et(d).md : '';
const nb = s => String(s).replace(/ /g, '\u00a0').replace(/([−+])\$/g, (m, g) => g + '\u2060$');   // a number keeps its unit and sign on a phone's wrapped line
const glue = s => String(s).replace(/(\d) (?=[a-z])/g, '$1\u00a0');   // in prose: "52 weeks" stays on one line
const AMP = ' &amp; ';
// money: cents under $100, whole dollars under $10K, then K, M and B; signed when asked
function usd(v, sign) {
  if (!isN(v)) return '—';
  const a = Math.abs(v), s = v < 0 ? '−' : sign && v > 0 ? '+' : '';
  if (!a) return '$0';
  return s + '$' + (a >= 1e9 ? num(a / 1e9, 2) + 'B' : a >= 1e6 ? num(a / 1e6, 2) + 'M' : a >= 1e4 ? num(a / 1e3, 1) + 'K' : num(a, a >= 100 ? 0 : 2));
}
const price = v => isN(v) ? M.px(v, 0) : '—';
const lab = (k, c) => (dv && dv.labels && dv.labels[k] && dv.labels[k][c]) || c || '';
const nm = id => (byId[id] && byId[id].name) || id;
function saved() {
  try {
    const j = JSON.parse(localStorage.getItem(KEY) || '{}'), o = {};
    for (const k in GKEY) if (j.o && Array.isArray(j.o[k])) o[k] = j.o[k].filter(x => typeof x === 'string').slice(0, 40);
    return {g: GKEY[j.g] ? j.g : 'family', o};
  } catch (e) { return {}; }
}
function keep() { try { localStorage.setItem(KEY, JSON.stringify({g: ui.g, o: ui.o})); } catch (e) {} }
const sz = r => r.querySelectorAll('[data-w]').forEach(e => { e.style.width = e.dataset.w + '%'; }); // CSSOM: the CSP bars style attributes
const pw = (v, m) => Math.min(50, 50 * Math.abs(v) / (m || 1)).toFixed(1);

// ---- sparks: GrokBot's kpiDeco line and Muse's card spark; a dashed zero line or entry, green or red by sign -----------
function spark(v, w, h, o) {
  o = o || {};
  const a = (v || []).filter(isN), t = 'last' in o ? o.last : a[a.length - 1];
  let s = '<svg class="dk-sk ' + tn(t) + '" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" aria-hidden="true">';
  if (a.length < 2) return s + '</svg>';
  let lo = Math.min(...a), hi = Math.max(...a);
  if (o.zero) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
  if (isN(o.ref)) { lo = Math.min(lo, o.ref); hi = Math.max(hi, o.ref); }
  if (hi - lo < 1e-9) { lo -= 1; hi += 1; }
  const p = 2.5, n = v.length - 1, X = i => (p + (w - 2 * p) * i / n).toFixed(1), Y = y => (p + (h - 2 * p) * (hi - y) / (hi - lo)).toFixed(1);
  let d = '', on = 0, li = -1;
  v.forEach((y, i) => { if (!isN(y)) { on = 0; return; } d += (on ? 'L' : 'M') + X(i) + ' ' + Y(y); on = 1; li = i; });
  if (o.zero) s += '<line class="z" x1="0" x2="' + w + '" y1="' + Y(0) + '" y2="' + Y(0) + '"/>';
  if (isN(o.ref)) s += '<line class="en" x1="0" x2="' + w + '" y1="' + Y(o.ref) + '" y2="' + Y(o.ref) + '"/>';
  s += '<path class="k" d="' + d + '"/>';
  if (o.dot && li >= 0) s += '<circle class="e" cx="' + X(li) + '" cy="' + Y(v[li]) + '" r="2.6"/>';
  return s + '</svg>';
}

// ---- the curve: GrokBot's drawChart, the desk against SPY in % since start; a gap where SPY has no close -------------
function curve(W, H, c, both) {
  const pl = 8, pr = 62, pt = 14, pb = 26, d = c.desk || [], sp = both ? c.spy || [] : [], n = d.length;
  const vals = d.concat(sp).filter(isN);
  if (n < 2 || !vals.length) return {svg: '', x: () => 0};
  let lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
  const pad = Math.max(0.1, (hi - lo) * 0.15);
  lo -= pad; hi += pad;
  const x = i => pl + (W - pl - pr) * i / (n - 1), y = v => pt + (H - pt - pb) * (hi - v) / (hi - lo), f = v => v.toFixed(1);
  const runs = a => { const r = []; let cur = null; a.forEach((v, i) => { if (!isN(v)) { cur = null; return; } if (!cur) r.push(cur = []); cur.push([x(i), y(v)]); }); return r; };
  const path = r => r.map(q => q.map((p, i) => (i ? 'L' : 'M') + f(p[0]) + ' ' + f(p[1])).join('')).join('');
  const last = a => { for (let i = a.length - 1; i >= 0; i--) if (isN(a[i])) return a[i]; return null; };
  const dl = last(d), sl_ = last(sp), tags = [];
  if (isN(dl)) tags.push({v: dl, c: dl < 0 ? 'pd' : 'pu'});
  if (isN(sl_)) tags.push({v: sl_, c: 'ps'});
  tags.forEach(t => { t.y = y(t.v); });
  if (tags.length === 2 && Math.abs(tags[0].y - tags[1].y) < 22) {        // two end pills never overlap: pushed apart
    const [a, b] = tags[0].y <= tags[1].y ? tags : [tags[1], tags[0]], m = (a.y + b.y) / 2;
    a.y = m - 11; b.y = m + 11;
  }
  let s = '<defs><linearGradient id="dk-ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7ee0c3" stop-opacity=".28"/><stop offset="1" stop-color="#7ee0c3" stop-opacity="0"/></linearGradient></defs>';
  for (let k = 0; k <= 4; k++) {
    const v = lo + (hi - lo) * k / 4, yy = y(v);
    s += '<line class="g" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f(yy) + '" y2="' + f(yy) + '"/>';
    if (!tags.some(t => Math.abs(t.y - yy) < 18)) s += '<text x="' + (W - pr + 8) + '" y="' + f(yy + 4) + '">' + M.pct(v, 2) + '</text>';
  }
  s += '<line class="z" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f(y(0)) + '" y2="' + f(y(0)) + '"/>';
  const dr = runs(d);
  s += dr.map(r => '<path class="ar" d="' + path([r]) + 'L' + f(r[r.length - 1][0]) + ' ' + f(y(lo)) + 'L' + f(r[0][0]) + ' ' + f(y(lo)) + 'Z"/>').join('');
  if (sp.length) s += '<path class="s" d="' + path(runs(sp)) + '"/>';
  s += '<path class="d" d="' + path(dr) + '"/>' + dr.flat().map(p => '<circle class="dd" cx="' + f(p[0]) + '" cy="' + f(p[1]) + '" r="2.6"/>').join('');
  const ds = c.dates || [], lx = [...new Set([0, Math.floor((n - 1) / 2), n - 1])];
  s += lx.map(i => '<text x="' + f(x(i)) + '" y="' + (H - 8) + '" text-anchor="' + (i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle') + '">' + esc(md(ds[i])) + '</text>').join('');
  s += tags.map(t => '<rect class="' + t.c + '" x="' + (W - pr + 2) + '" y="' + f(t.y - 10) + '" width="' + (pr - 4) + '" height="20" rx="5"/><text class="pt" x="' + (W - pr / 2) + '" y="' + f(t.y + 4) + '" text-anchor="middle">' + M.pct(t.v, 2) + '</text>').join('');
  s += '<g class="dk-xh" visibility="hidden"><line class="x" y1="' + pt + '" y2="' + (H - pb) + '"/>' + (sp.length ? '<circle class="ps" r="4.5"/>' : '') + '<circle class="dd" r="5"/></g>';
  return {svg: s, x, y};
}

// ---- the heatmap: GrokBot's squarify, heatColor and inkTile (text colour at 4.5:1 or better) ---------------------------
function squarify(items, x, y, w, h) {
  const out = [], total = items.reduce((s, v) => s + v.v, 0);
  if (!total || w <= 0 || h <= 0) return out;
  const sc = w * h / total, q = items.map(v => Object.assign({}, v, {a: v.v * sc}));
  let row = [];
  const worst = (r, len) => { const s = r.reduce((a, b) => a + b.a, 0), mx = Math.max(...r.map(z => z.a)), mn = Math.min(...r.map(z => z.a)); return Math.max(len * len * mx / (s * s), (s * s) / (len * len * mn)); };
  const lay = r => {
    const s = r.reduce((a, b) => a + b.a, 0);
    if (w >= h) { const cw_ = s / h; let cy = y; r.forEach(z => { const rh = z.a / cw_; out.push(Object.assign(z, {x, y: cy, w: cw_, h: rh})); cy += rh; }); x += cw_; w -= cw_; }
    else { const rh = s / w; let cx = x; r.forEach(z => { const rw = z.a / rh; out.push(Object.assign(z, {x: cx, y, w: rw, h: rh})); cx += rw; }); y += rh; h -= rh; }
  };
  while (q.length) {
    const len = Math.min(w, h), c = q[0];
    if (!row.length || worst(row.concat([c]), len) <= worst(row, len)) { row.push(c); q.shift(); } else { lay(row); row = []; }
  }
  if (row.length) lay(row);
  return out;
}
function hsl(h, s, l) { s /= 100; l /= 100; const k = n => (n + h / 30) % 12, a = s * Math.min(l, 1 - l), f = n => l - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1)); return [f(0), f(8), f(4)]; }
function lum(c) { const g = x => x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); return 0.2126 * g(c[0]) + 0.7152 * g(c[1]) + 0.0722 * g(c[2]); }
function ink(h, s, L) {
  const N = lum([16 / 255, 40 / 255, 58 / 255]), c = () => 'hsl(' + h + ',' + s.toFixed(1) + '%,' + L.toFixed(1) + '%)';
  for (let i = 0; i < 40; i++) {
    const Y = lum(hsl(h, s, L));
    if ((Y + 0.05) / (N + 0.05) >= 4.5) return [c(), '#10283a'];
    if (1.05 / (Y + 0.05) >= 4.5) return [c(), '#fff'];
    L -= 1.5;
  }
  return [c(), '#fff'];
}
function heatColor(p) {
  if (!isN(p)) return ['#e9eef0', '#1c2b39'];
  const k = Math.min(1, Math.abs(p) / 8), L = 88 - k * 56;
  return p >= 0 ? ink(152, 45 + k * 15, L) : ink(4, 55 + k * 12, L);
}
// a tile's labels only where they fit whole: the symbol, then its %, then its value; else none (a tap names it)
function fits(t) {
  const sym = t.sym.length * 9 + 14, p = 7 * 7.4 + 14;
  const b = t.w >= sym && t.h >= 26, q = b && t.w >= p && t.h >= 42;
  return {b, p: q, m: q && t.w >= 76 && t.h >= 58};
}

// ---- the panel ---------------------------------------------------------------------------------------------------------
function head(id, kick, title, sub) {
  return '<div class="shd"><div class="sht"><p class="kick">' + kick + '</p><h2 id="h-d' + id + '">' + title + '</h2>' +
    (sub ? '<p class="sub">' + sub + '</p>' : '') + '</div></div>';
}
const sec = (id, jump, body) => '<section id="d-' + id + '" aria-labelledby="h-d' + id + '" data-anchor data-jump="' + jump + '">' + body + '</section>';
const tg = (label, k, cur, opts) => '<div class="tg" role="group" aria-label="' + label + '">' + opts.map(o => '<button type="button" data-' + k + '="' + o[0] +
  '" aria-pressed="' + (o[0] === cur) + '">' + o[1] + (o.length > 2 ? '<span class="n">' + o[2] + '</span>' : '') + '</button>').join('') + '</div>';

function over() {
  const o = dv.overview || {}, e = dv.engine || {}, d = o.day || {}, ds = (dv.curve || {}).dates || [], eq = o.equity, ST = {ok: 'up', warn: 'wn'};
  const tile = (c, l, v, s, x) => '<div class="tile' + (c ? ' ' + c : '') + '"><div class="l">' + l + '</div><div class="v">' + v + '</div>' + (s ? '<div class="s">' + s + '</div>' : '') + (x || '') + '</div>';
  const sp = o.spark || [], up = sp.length > 1 && sp[sp.length - 1] >= sp[0];
  let k = '';
  if (sp.length > 1) {
    const lo = Math.min(...sp), r = (Math.max(...sp) - lo) || 1, n = sp.length - 1, pts = sp.map((q, i) => (100 * i / n).toFixed(2) + ',' + (30 - 26 * (q - lo) / r).toFixed(2));
    k = '<svg class="dk-tsp ' + (up ? 'up' : 'dn') + '" viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true"><path class="a" d="M0,32 L' + pts.join(' L') + ' L100,32Z"/><polyline class="k" points="' +
      pts.join(' ') + '" vector-effect="non-scaling-stroke"/></svg><div class="dk-tl">' + esc(md(ds[0]) + ' → ' + md(ds[ds.length - 1])) + '</div>';
  }
  const m = Math.max(Math.abs(o.pct || 0), Math.abs(o.spy_pct || 0), 0.01);
  const vs = (l, v, c) => isN(v) ? '<div class="dk-vr"><span>' + l + '</span><span class="dk-vb"><i class="' + (v < 0 ? 'n' : 'p') + c + '" data-w="' + pw(v, m) + '"></i></span><b class="dk-' + tn(v) + '">' + pc(v) + '</b></div>' : '';
  const cash = isN(o.cash) && eq ? o.cash / eq : null, inv = isN(o.invested) && eq ? o.invested / eq : null;
  const T = [
    tile('dk-eq', 'Equity', usd(eq), 'from ' + usd(o.capital), k),
    tile('', 'Cash', usd(o.cash), isN(cash) ? num(cash * 100, 0) + '% of equity' : '', isN(cash) ? '<div class="dk-kb"><i data-w="' + Math.max(0, Math.min(100, cash * 100)).toFixed(1) + '"></i></div>' : ''),
    tile(tn(d.pnl), 'Day P' + AMP.trim() + 'L', usd(d.pnl, 1), [pc(d.pct), d.date ? M.day(d.date) : ''].filter(Boolean).join(' · ')),
    tile(tn(o.pnl), 'Total P' + AMP.trim() + 'L', usd(o.pnl, 1), pc(o.pct), '<div class="dk-vs" role="img" aria-label="' + esc('Since ' + md(dv.start) + ': desk ' + pc(o.pct) + ', SPY ' + pc(o.spy_pct)) + '">' + vs('Desk', o.pct, '') + vs('SPY', o.spy_pct, ' s') + '</div>'),
    tile('', 'Holdings', n0(o.positions), n0(o.symbols) + ' symbols held · ' + n0((dv.positions || {}).waiting) + ' waiting to buy')];
  const split = isN(inv) && isN(cash) && inv >= 0 ? '<div class="dk-ab" role="img" aria-label="' + esc('Invested ' + usd(o.invested) + ', cash ' + usd(o.cash)) + '"><i data-w="' + (inv * 100).toFixed(1) + '"></i><i class="c"></i></div><p class="dk-ak"><span>Invested ' +
    usd(o.invested) + ' · ' + num(inv * 100, 0) + '%</span><span class="c">Cash ' + usd(o.cash) + ' · ' + num(cash * 100, 0) + '%</span><em>Long ' + usd(o.long) + ' · short ' + usd(o.short) + '</em></p>' : '';
  return head('over', 'Since ' + esc(md(dv.start)), 'Desk', '') + '<div class="card dk-hl"><p class="dk-h">' + esc(o.headline) + '</p><p class="dk-en"><span class="st ' + (ST[e.state] || 'dn') + '">' +
    esc(e.label || '') + '</span>' + (e.last_pass ? '<span>Last pass ' + M.wd(e.last_pass) + ' ET</span>' : '') + '</p></div><div class="dk-ts">' + T.join('') + '</div>' + split;
}

function curveSec() {
  const c = dv.curve || {}, ds = c.dates || [], spy = c.spy || [];
  const rows = ds.map((x, i) => '<tr><th scope="row">' + esc(M.day(x)) + '</th><td class="r">' + pc((c.desk || [])[i]) + '</td><td class="r">' + pc(spy[i]) + '</td></tr>').join('');
  return '<div class="dk-cv"><div class="dk-ch"><h3 id="h-dcurve">Desk vs SPY <span>% since ' + esc(md(dv.start)) + '</span></h3>' +
    tg('Lines', 'cm', ui.m, [['both', 'Desk + SPY'], ['desk', 'Desk only']]) + '</div><div class="dk-cw" id="d-cw" role="img"></div><p class="dk-cg"><span><i></i>Desk</span><span id="d-cgs"><i class="s"></i>SPY</span><span class="dk-cap" id="d-cap" aria-live="polite"></span></p>' +
    '<details class="dk-vt"><summary>Values</summary><div class="tw"><table class="t"><thead><tr><th>Day</th><th class="r">Desk</th><th class="r">SPY</th></tr></thead><tbody>' + rows + '</tbody></table></div></details></div>';
}
function drawCurve() {
  const w = el('d-cw');
  if (!w || !w.clientWidth) return;
  const W = Math.max(300, Math.round(w.clientWidth)), H = Math.round(w.clientHeight) || 262, c = dv.curve || {}, both = ui.m === 'both', g = curve(W, H, c, both), ds = c.dates || [];
  cw = W;
  w.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" aria-hidden="true">' + g.svg + '</svg>';
  const o = dv.overview || {}, i0 = ds.length - 1;
  w.setAttribute('aria-label', 'Desk ' + pc(o.pct) + (both ? ', SPY ' + pc(o.spy_pct) : '') + ' since ' + md(dv.start) + ', daily');
  el('d-cgs').hidden = !both;
  const cap = i => { text(el('d-cap'), md(ds[i]) + ' · Desk ' + pc((c.desk || [])[i]) + (both ? ' · SPY ' + pc((c.spy || [])[i]) : '')); };
  cap(i0);
  const svg = w.firstChild, xh = svg.querySelector('.dk-xh');
  const at = ev => {
    const r = svg.getBoundingClientRect(), cx = (ev.clientX - r.left) * W / r.width, n = ds.length;
    let i = Math.round((cx - g.x(0)) / ((g.x(n - 1) - g.x(0)) / (n - 1) || 1));
    i = Math.max(0, Math.min(n - 1, i));
    const X = g.x(i).toFixed(1), dvv = (c.desk || [])[i], sv = (c.spy || [])[i], [ln, a, b] = [xh.querySelector('line'), xh.querySelector('.ps'), xh.querySelector('circle.dd')];
    ln.setAttribute('x1', X); ln.setAttribute('x2', X);
    if (isN(dvv)) { b.setAttribute('cx', X); b.setAttribute('cy', g.y(dvv).toFixed(1)); }
    if (a) { a.setAttribute('visibility', isN(sv) ? 'visible' : 'hidden'); if (isN(sv)) { a.setAttribute('cx', X); a.setAttribute('cy', g.y(sv).toFixed(1)); } }
    xh.setAttribute('visibility', 'visible');
    cap(i);
  };
  svg.addEventListener('pointermove', at);
  svg.addEventListener('pointerdown', at);
  svg.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') { xh.setAttribute('visibility', 'hidden'); cap(i0); } });
}
const text = (e, t) => { if (e && e.textContent !== t) e.textContent = t; };

function lead() {
  const s = dv.sleeves || {}, A = s.leaders || [], B = s.laggards || [], C = s.movers || [];
  const m = Math.max(0.01, ...A.concat(B).map(r => Math.abs(r.ret || 0))), m1 = Math.max(0.01, ...C.map(r => Math.abs(r.ret_1d || 0)));
  const row = (r, i, k, mx) => { const v = r[k]; return '<button type="button" class="dk-li" data-id="' + esc(r.id) + '"><span class="k">' + (i + 1) + '</span><span class="nm">' + esc(r.name) +
    '</span><span class="v dk-' + tn(v) + '">' + pc(v) + '</span><span class="dk-lsb">' + spark(r.spark, 72, 22, {zero: 1}) + '<span>' + esc(lab('family', r.family)) + (k === 'ret_1d' ? '\u00a0· ' + nb(pc(r.ret) + ' total') : '') +
    '</span></span><span class="dk-db"><i class="' + (v < 0 ? 'n' : 'p') + '" data-w="' + pw(v || 0, mx) + '"></i></span></button>'; };
  const col = (c, t, a, k, mx) => '<div class="dk-lc ' + c + '"><h3><span>' + t + '</span><span>' + a.length + '</span></h3>' + (a.length ? a.map((r, i) => row(r, i, k, mx)).join('') : '<p class="dk-none">None yet</p>') + '</div>';
  return head('lead', 'Best and worst', 'Leaderboard', 'Return since ' + esc(md(dv.start)) + ' · ' + n0(s.min_trades) + '+ closed trades') +
    '<div class="card">' + tg('List', 'lv', ui.lv, [['best', 'Leaders'], ['worst', 'Laggards'], ['today', 'Today']]).replace('class="tg"', 'class="tg dk-lt"') +
    '<div class="dk-lb" data-v="' + ui.lv + '">' + col('best', 'Leaders', A, 'ret', m) + col('worst', 'Laggards', B, 'ret', m) + col('today', 'Today’s movers', C, 'ret_1d', m1) + '</div></div>';
}

// ---- the sleeves explorer ------------------------------------------------------------------------------------------------
const FILT = {all: () => true, win: r => r.ret > 0, lose: r => r.ret < 0, fire: r => r.state === 'firing', off: r => r.state === 'off' || r.state === 'blocked'};
const SORT = {ret: (a, b) => (b.ret ?? -1e9) - (a.ret ?? -1e9), d1: (a, b) => (b.ret_1d ?? -1e9) - (a.ret_1d ?? -1e9),
  dd: (a, b) => (b.dd ?? -1) - (a.dd ?? -1), name: (a, b) => a.name.localeCompare(b.name)};
const tfk = t => /h$|m$/.test(t || '') ? ' h' : /w$|mo$/.test(t || '') ? ' w' : ' d';
const VERD = {below_bar: 'wn', review: 'bad', propose: 'ok'};
function money() {
  const F = (dv.sleeves || {}).families || [], P_ = F.filter(g => g.in_use > 0), top = P_.slice(0, 6), rest = P_.slice(6), tot = P_.reduce((s, g) => s + g.in_use, 0);
  const parts = top.map((g, i) => ({l: g.name, v: g.in_use, c: 'c' + i})).concat(rest.length ? [{l: rest.length + ' more', v: rest.reduce((s, g) => s + g.in_use, 0), c: 'c6'}] : []);
  let a = -Math.PI / 2, arcs = '';
  const R = 60, r = 40, P2 = (rad, t) => (75 + rad * Math.cos(t)).toFixed(2) + ' ' + (75 + rad * Math.sin(t)).toFixed(2);
  if (tot > 0) parts.forEach(p => { const f = p.v / tot, a2 = a + f * 2 * Math.PI * 0.9999, lg = f > 0.5 ? 1 : 0;
    arcs += '<path class="' + p.c + '" d="M' + P2(R, a) + ' A' + R + ' ' + R + ' 0 ' + lg + ' 1 ' + P2(R, a2) + ' L' + P2(r, a2) + ' A' + r + ' ' + r + ' 0 ' + lg + ' 0 ' + P2(r, a) + ' Z"/>'; a = a2; });
  else arcs = '<circle class="r" cx="75" cy="75" r="50" stroke-width="20"/>';
  const o = dv.overview || {}, s = dv.sleeves || {}, c = s.counts || {};
  const st = ['firing', 'waiting', 'off', 'blocked'].filter(k => c[k]);
  const big = v => '$' + (v >= 1e6 ? num(v / 1e6, 1) + 'M' : v >= 1e3 ? num(v / 1e3, 1) + 'K' : num(v, 0));
  return '<div class="dk-xt"><svg class="dk-dn2" viewBox="0 0 150 150" role="img" aria-label="' + esc('Money in use ' + usd(tot) + ' of ' + usd(o.capital) + ': ' + parts.map(p => p.l + ' ' + usd(p.v)).join(', ')) + '">' + arcs +
    '<text class="c" x="75" y="73" text-anchor="middle">' + big(tot) + '</text><text class="u" x="75" y="91" text-anchor="middle">in use</text></svg><div class="dk-al"><p class="dk-alh">Money in use by family</p>' +
    parts.map(p => '<p><span><i class="' + p.c + '"></i>' + esc(p.l) + '</span><b>' + usd(p.v) + '</b></p>').join('') + '</div><div class="dk-sb"><p class="dk-alh">State</p>' +
    '<div class="dk-st" role="img" aria-label="' + esc(st.map(k => c[k] + ' ' + lab('state', k).toLowerCase()).join(', ')) + '">' + st.map(k => '<i class="' + k + '" data-w="' + (100 * c[k] / (s.n || 1)).toFixed(1) + '"></i>').join('') + '</div>' +
    '<p class="dk-sg">' + st.map(k => '<span class="' + k + '"><b>' + n0(c[k]) + '</b> ' + esc(lab('state', k).toLowerCase()) + '</span>').join('') + '</p></div></div>';
}
function controls() {
  const R = sl ? sl.rows : [], cnt = k => R.filter(FILT[k]).length;
  return '<div class="dk-xc"><div class="dk-xl"><span>Group</span>' + tg('Group by', 'gb', ui.g, [['family', 'Family'], ['cls', 'Asset class'], ['style', 'Style']]) + '</div>' +
    '<div class="dk-xl"><span>Show</span>' + tg('Show', 'f', ui.f, [['all', 'All', cnt('all')], ['win', 'Winning', cnt('win')], ['lose', 'Losing', cnt('lose')], ['fire', esc(lab('state', 'firing')), cnt('fire')], ['off', esc(lab('state', 'off') + '/' + lab('state', 'blocked')), cnt('off')]]) + '</div>' +
    '<div class="dk-xl"><span>Sort</span>' + tg('Sort', 's', ui.s, [['ret', 'Return'], ['d1', 'Today'], ['dd', 'Drawdown'], ['name', 'Name']]) + '</div>' +
    '<button class="dk-fb" id="d-fb" type="button" aria-keyshortcuts="/" aria-haspopup="dialog"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>Find a sleeve<kbd aria-hidden="true">/</kbd></button></div>';
}
function slSec() {
  return head('sl', 'Explorer', 'Sleeves', 'All ' + n0((dv.sleeves || {}).n) + ', by family, asset class or style') + '<div class="card">' + money() + '<div id="d-xc">' + controls() + '</div><div class="dk-gs" id="d-gs"></div></div>';
}
function members() {
  const out = {};
  (sl ? sl.rows : []).forEach(r => { (out[r[ui.g]] = out[r[ui.g]] || []).push(r); });
  return out;
}
// a group's money in use against its capital, its best and its worst (the header's second line; on a phone, the open
// section's first)
function gline(g) {
  const b = g.best, w = g.worst, cap = g.capital, over = isN(g.in_use) && cap > 0 && g.in_use > cap;
  return (cap > 0 ? '<span class="bu' + (over ? ' ov' : '') + '"><i><b data-w="' + Math.min(100, 100 * (g.in_use || 0) / cap).toFixed(1) + '"></b></i>' + usd(g.in_use) + ' of ' + usd(cap) + (over ? ' · over budget' : '') + '</span>' : '') +
    (b && isN(b.ret) && b.ret > 0 ? '<span>Best <em>' + esc(b.name) + '</em> <b class="dk-up">' + pc(b.ret) + '</b></span>' : '') +
    (w && isN(w.ret) && w.ret < 0 ? '<span>Worst <em>' + esc(w.name) + '</em> <b class="dk-dn">' + pc(w.ret) + '</b></span>' : '');
}
function ghead(g, hit, n) {
  const t = (g.up || 0) + (g.down || 0);
  return '<span class="dk-gn">' + esc(g.name) + '<small>' + n0(g.n) + (hit !== n ? ' · <b class="mt">' + n0(hit) + ' shown</b>' : '') + '</small></span><span class="dk-gu"><span class="ud" aria-hidden="true">' +
    (t ? '<i data-w="' + (100 * g.up / g.n).toFixed(1) + '"></i><i class="d" data-w="' + (100 * g.down / g.n).toFixed(1) + '"></i>' : '') + '</span><span><b class="dk-up">' + n0(g.up) + '</b> up · <b class="dk-dn">' + n0(g.down) + '</b> down</span></span>' +
    spark(g.spark, 88, 26, {zero: 1}) + '<span class="dk-gm dk-' + tn(g.median) + '"><span class="sr">median </span>' + pc(g.median) + '</span><span class="dk-gb">' + gline(g) + '</span>';
}
function groups() {
  const box = el('d-gs');
  if (!box) return;
  if (!sl) { box.innerHTML = '<p class="dk-none">The sleeve list could not be loaded.</p>'; return; }
  const G = (dv.sleeves || {})[GKEY[ui.g]] || [], by = members(), open = new Set(ui.o[ui.g] || []), f = FILT[ui.f];
  box.innerHTML = '<p class="dk-gh" aria-hidden="true"><span>' + {family: 'Family', cls: 'Asset class', style: 'Style'}[ui.g] + '</span><span>Up · down</span><span>Since ' + esc(md(dv.start)) + '</span><span>Median</span></p>' + G.map(g => {
    const mem = by[g.id] || [], hit = mem.filter(f).length;
    if (!hit && ui.f !== 'all') return '';
    return '<details class="dk-g" data-g="' + esc(g.id) + '"' + (open.has(g.id) ? ' open' : '') + '><summary>' + ghead(g, hit, mem.length) + '</summary><div class="dk-rs"></div></details>';
  }).join('') || '<p class="dk-none">No sleeve matches.</p>';
  sz(box);
  box.querySelectorAll('.dk-g[open]').forEach(fill);
}
function rowHTML(r) {
  const st = r.state || 'off', v = r.verdict;
  return '<div class="dk-r" data-id="' + esc(r.id) + '"><button type="button" class="dk-rb" aria-expanded="false"><span class="dk-rst"><i class="dk-dot ' + st + '"></i><span>' + esc(lab('state', st)) + '</span></span>' +
    '<span class="dk-rn">' + esc(r.name) + (r.tf ? ' <span class="dk-k' + tfk(r.tf) + '">' + esc(lab('tf', r.tf)) + '</span>' : '') + '</span><span class="dk-rd">' + esc(glue(r.desc)) + '</span>' +
    spark(r.spark, 88, 26, {zero: 1, last: r.ret}) + '<span class="dk-rr dk-' + tn(r.ret) + '">' + pc(r.ret) + '</span><span class="dk-r1">' + (isN(r.ret_1d) ? '<span class="dk-c ' + tn(r.ret_1d) + ' dk-' + tn(r.ret_1d) + '">' + pc(r.ret_1d) + ' 1d</span>' : '') + '</span>' +
    '<span class="dk-rv">' + (v ? '<span class="dk-c ' + (VERD[v] || '') + '">' + esc(lab('verdict', v)) + '</span>' : '') + (r.small ? '<span class="dk-c sm">small sample</span>' : '') + '</span></button></div>';
}
// a group's rows: each row's markup is parsed once and its element reused, so a filter, a sort or a regroup only moves
// elements (the cache empties with new data)
let rowc = {};
function fill(d) {
  const box = d.querySelector('.dk-rs'), gid = d.dataset.g, mem = (members()[gid] || []).filter(FILT[ui.f]).sort(SORT[ui.s]), n = ui.gn[gid] || LIM, A = mem.slice(0, n);
  const g = ((dv.sleeves || {})[GKEY[ui.g]] || []).find(x => x.id === gid), gl = g ? gline(g) : '', miss = A.filter(r => !rowc[r.id]), t = D.createElement('div');
  if (miss.length) { t.innerHTML = miss.map(rowHTML).join(''); [...t.children].forEach((e, i) => { rowc[miss[i].id] = e; }); }
  t.innerHTML = (gl ? '<p class="dk-gx">' + gl + '</p>' : '') + (!A.length ? '<p class="dk-none">No sleeve matches.</p>' : '') + (mem.length > n ? '<button type="button" class="dk-more" data-more="g">Show all ' + n0(mem.length) + '</button>' : '');
  const ex = [...t.children], more = ex.find(e => e.tagName === 'BUTTON');
  box.replaceChildren(...ex.filter(e => e !== more), ...A.map(r => rowc[r.id]), ...(more ? [more] : []));
  sz(box);
  A.forEach(r => { const e = rowc[r.id]; if (e.classList.contains('on') !== (r.id === sel)) strip(e, r.id === sel); });
}
function strip(r, on) {
  const b = r.querySelector('.dk-rb'), x = r.querySelector('.dk-rx'), s = byId[r.dataset.id];
  if (x) x.remove();
  r.classList.toggle('on', on);
  b.setAttribute('aria-expanded', on);
  if (!on || !s) return;
  const kv = (l, v) => '<div><dt>' + l + '</dt><dd>' + v + '</dd></div>', top = ((dv.positions || {}).top || []).filter(p => p.sleeve === s.id);
  const d = D.createElement('div');
  d.className = 'dk-rx';
  // the row shows its return, timeframe, state and verdict; the strip adds the rest (a phone's row keeps only the first two)
  d.innerHTML = '<dl class="dk-kv">' + kv('Trades', n0(s.trades)) + kv('Win rate', isN(s.win) ? num(s.win, 1) + '%' : '—') + kv('Drawdown', isN(s.dd) ? num(s.dd, 2) + '%' : '—') +
    kv('5 days', pc(s.ret_5d)) + kv('Capital', usd(s.capital)) + kv('In use', usd(s.in_use)) + '</dl>' +
    '<p class="dk-xm"><span class="dk-c dk-xo">' + esc(lab('state', s.state)) + '</span>' + (s.verdict ? '<span class="dk-c dk-xo ' + (VERD[s.verdict] || '') + '">' + esc(lab('verdict', s.verdict)) + '</span>' : '') +
    (s.small ? '<span class="dk-c dk-xo sm">small sample</span>' : '') + '<span class="dk-c">' + esc(lab('cls', s.cls)) + '</span><span class="dk-c">' + esc(lab('style', s.style)) + '</span><span class="dk-c">' + esc(lab('family', s.family)) + '</span></p>' +
    (s.pos ? '<ul class="dk-pm" data-sp="' + esc(s.id) + '">' + plist(pj ? pj.rows.filter(p => p.sleeve === s.id) : top, s.pos) + '</ul>' : '');
  r.appendChild(d);
}
function plist(a, n) {
  const m = pj ? 30 : 12;
  return a.slice(0, m).map(p => '<li><span><b>' + esc(p.sym) + '</b> ' + (p.side === 'short' ? 'short · ' : '') + usd(p.value) + '</span><span class="dk-' + tn(p.pct) + '">' + pc(p.pct) + '</span></li>').join('') +
    (!pj && n > a.length ? '<li><button type="button" class="lk" data-sp-all>All ' + n0(n) + ' positions</button></li>' : pj && a.length > m ? '<li class="mu">' + n0(a.length - m) + ' more, smaller</li>' : '');
}

// ---- Find a sleeve: GrokBot's finder (search by name or idea, family chips), a bottom sheet on phones -------------------
let fam = '', fmax = 60, fraf = 0;
function finder() {
  let d = el('d-fd');
  if (d) return d;
  d = D.createElement('dialog');
  d.id = 'd-fd';
  d.className = 'dk-fd';
  d.setAttribute('aria-labelledby', 'd-fdt');
  d.innerHTML = '<div class="dk-fh"><h2 id="d-fdt">Find a sleeve</h2><button class="dk-fx" type="button" aria-label="Close" data-fx>×</button></div><div class="dk-fs"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
    '<label class="sr" for="d-fq">Search sleeves</label><input id="d-fq" type="search" placeholder="Search by name or idea" autocomplete="off" spellcheck="false" enterkeyhint="go"></div><div class="dk-ft" id="d-ft" role="group" aria-label="Family"></div><p class="dk-fc" id="d-fn" role="status"></p><div class="dk-fl" id="d-fl"></div>';
  D.body.appendChild(d);
  el('d-fq').addEventListener('input', () => { fmax = 60; if (!fraf) fraf = requestAnimationFrame(() => { fraf = 0; frender(); }); });
  el('d-fq').addEventListener('keydown', e => { if (e.key === 'Enter') { const b = el('d-fl').querySelector('.dk-fi'); if (b) { e.preventDefault(); pick(b.dataset.id); } } });
  d.addEventListener('click', e => {
    const t = e.target, b = t.closest('[data-fam]'), it = t.closest('.dk-fi');
    if (t === d || t.closest('[data-fx]')) d.close();
    else if (b) { fam = b.dataset.fam === fam ? '' : b.dataset.fam; frender(); }
    else if (it) pick(it.dataset.id);
    else if (t.closest('[data-fmore]')) { fmax = 1e9; frender(); }
  });
  return d;
}
function frender() {
  const q = el('d-fq').value.trim().toLowerCase(), words = q.split(/\s+/).filter(Boolean), R = sl ? sl.rows : [];
  const hit = R.filter(r => words.every(w => r._h.includes(w))), F = (dv.sleeves || {}).families || [];
  if (fam && !hit.some(r => r.family === fam)) fam = '';
  el('d-ft').innerHTML = '<button type="button" data-fam="" aria-pressed="' + !fam + '">All<span class="n">' + n0(hit.length) + '</span></button>' + F.map(g => {
    const n = hit.filter(r => r.family === g.id).length;
    return n ? '<button type="button" data-fam="' + esc(g.id) + '" aria-pressed="' + (fam === g.id) + '">' + esc(g.name) + '<span class="n">' + n + '</span></button>' : '';
  }).join('');
  el('d-ft').className = 'dk-ft tg';
  const S = hit.filter(r => !fam || r.family === fam);
  text(el('d-fn'), n0(S.length) + ' of ' + n0(R.length) + ' sleeves' + (q ? ' matching “' + el('d-fq').value.trim() + '”' : ''));
  let k = 0, h = '';
  for (const g of F) {
    if (k >= fmax) break;
    const G = S.filter(r => r.family === g.id).sort(SORT.ret).slice(0, fmax - k);
    if (!G.length) continue;
    k += G.length;
    h += '<div role="group" aria-label="' + esc(g.name) + '"><h3>' + esc(g.name) + '<span>' + S.filter(r => r.family === g.id).length + '</span></h3>' + G.map(r => '<button type="button" class="dk-fi" data-id="' + esc(r.id) + '"><span><b>' + esc(r.name) +
      '</b><small>' + esc([r.tf ? lab('tf', r.tf) : '', lab('state', r.state), glue(r.desc)].filter(Boolean).join('\u00a0· ')) + '</small></span><span class="dk-c ' + tn(r.ret) + ' dk-' + tn(r.ret) + '">' + pc(r.ret) + '</span></button>').join('') + '</div>';
  }
  el('d-fl').innerHTML = h + (S.length > k ? '<button type="button" class="dk-more" data-fmore>Show all ' + n0(S.length) + '</button>' : '') || '<p class="dk-none">No sleeve matches. Try a broader word, such as “weekly”, “options” or “breakout”.</p>';
}
function find() {
  if (!sl) return;
  const d = finder();
  if (d.open) return el('d-fq').focus();
  frender();
  d.showModal();
  el('d-fq').focus();
}
function pick(id) {
  const d = el('d-fd');
  if (d && d.open) d.close();
  reveal(id);
}
// open a sleeve in the explorer: its group, its row and its detail strip
function reveal(id) {
  const r = byId[id];
  if (!r) return;
  if (!FILT[ui.f](r)) { ui.f = 'all'; el('d-xc').innerHTML = controls(); }
  const gid = r[ui.g], o = ui.o[ui.g] = ui.o[ui.g] || [];
  if (!o.includes(gid)) { o.push(gid); keep(); }
  sel = id;
  const mem = (members()[gid] || []).filter(FILT[ui.f]).sort(SORT[ui.s]), i = mem.findIndex(x => x.id === id);
  if (i >= (ui.gn[gid] || LIM)) ui.gn[gid] = mem.length;
  groups();
  const row = P.querySelector('.dk-g[data-g="' + CSS.escape(gid) + '"] .dk-r[data-id="' + CSS.escape(id) + '"]');
  if (!row) return;
  row.scrollIntoView({block: 'center'});
  row.classList.remove('dk-tint');
  void row.offsetWidth;
  row.classList.add('dk-tint');
  row.querySelector('.dk-rb').focus({preventScroll: true});
}

// ---- positions: GrokBot's open positions with the owner's 30-close spark, entry line and time-left bar ------------------
function prow(p, sk) {
  const t = tn(p.pct), q = isN(p.qty) ? num(p.qty, p.qty % 1 ? 2 : 0) : '';
  const hold = isN(p.left) && isN(p.hold) && p.hold > 0 ? '<div class="dk-ho" role="img" aria-label="' + esc(n0(p.days) + ' of ' + n0(p.hold) + ' days held') + '"><i data-w="' + Math.min(100, 100 * (p.days || 0) / p.hold).toFixed(1) + '"></i></div><p class="dk-pd">Exit ' + esc(nb(md(p.due))) + '\u00a0· ' + nb(n0(p.left) + ' days left') + '</p>' : '';
  return '<div class="dk-p ' + t + '"><div class="dk-pa"><p class="dk-py"><b>' + esc(p.sym) + '</b>' + (p.side === 'short' ? '<small>short</small>' : '') + '<span class="dk-pt">' + esc(nm(p.sleeve)) + '</span></p><p class="dk-pd">' +
    (p.side === 'short' ? 'Shorted at ' : 'Bought at ') + price(p.entry) + '\u00a0· ' + esc(nb(md(p.opened))) + (q ? '\u00a0· ' + nb(q + (p.cls === 'stocks' || p.cls === 'etf_macro' ? ' sh' : '')) : '') + (hold ? '' : '\u00a0· ' + nb(n0(p.days) + (p.days === 1 ? ' day' : ' days'))) + '</p>' + hold + '</div>' +
    spark(sk, 140, 40, {ref: p.entry, dot: 1, last: p.pct}) + '<div class="dk-pr"><div class="dk-px">' + price(p.last) + '</div><div class="dk-pp dk-' + t + '">' + pc(p.pct) + '</div><small>' + usd(p.pnl, 1) + '</small></div></div>';
}
function posSec() {
  const p = dv.positions || {};
  return head('pos', 'Holdings', 'Open positions', 'Largest first · ' + n0(p.n) + ' positions in ' + n0(p.symbols) + ' symbols') + '<div class="card"><div id="d-pl"></div></div>';
}
function positions() {
  const box = el('d-pl'), all = !!pj, R = all ? pj.rows : (dv.positions || {}).top || [], S = all ? pj.sparks || {} : (dv.positions || {}).sparks || {}, F = (dv.sleeves || {}).families || [];
  if (ui.pf !== 'all' && !R.some(p => p.family === ui.pf)) ui.pf = 'all';
  const by = {};
  R.forEach(p => { by[p.family] = (by[p.family] || 0) + 1; });
  const fams = F.filter(g => by[g.id]).map(g => [g.id, g.name, n0(by[g.id])]);
  const A = R.filter(p => ui.pf === 'all' || p.family === ui.pf), n = (dv.positions || {}).n || 0;
  box.innerHTML = tg('Family', 'pf', ui.pf, [['all', all ? 'All' : 'Largest', n0(R.length)]].concat(fams)).replace('class="tg"', 'class="tg dk-pc"') + '<div class="dk-pls">' + A.slice(0, ui.pn).map(p => prow(p, S[p.sym])).join('') + '</div>' +
    '<p class="dk-mb">' + (A.length > ui.pn ? '<button type="button" class="dk-more" data-more="p">Show ' + n0(Math.min(ui.pn < 40 ? 40 - ui.pn : 40, A.length - ui.pn)) + ' more' + (all ? ' of ' + n0(A.length) : '') + '</button>' : '') +
    (!all && n > R.length ? '<button type="button" class="dk-more" data-pall>Show all ' + n0(n) + '</button>' : '') + '</p>';
  sz(box);
}
function loadPos() {
  return pjP || (pjP = fetch('positions.json', {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(j => {
    if (!j || j.schema !== SCH.p || !Array.isArray(j.rows)) throw new Error('schema');
    pj = j;
    return j;
  }).catch(e => { pjP = null; throw e; }));
}

// ---- the heatmap ---------------------------------------------------------------------------------------------------------
function heatSec() {
  const H = (dv.positions || {}).heat || [], p = dv.positions || {};
  const rows = H.slice(0, 30).map(h => '<tr><th scope="row">' + esc(h.sym) + '</th><td class="r">' + usd(h.gross) + '</td><td class="r">' + pc(h.pct) + '</td><td class="r">' + n0(h.n) + '</td></tr>').join('');
  return head('heat', 'By symbol', 'Heatmap', 'The ' + n0(H.length) + ' largest · tile size = value · colour = gain or loss') +
    '<div class="card"><svg class="dk-hm" id="d-hm" role="img"></svg><div class="dk-hd" id="d-hd" aria-live="polite"></div><p class="dk-hg"><span>Loss</span><i></i><span>Gain</span></p>' +
    '<details class="dk-vt"><summary>Values</summary><div class="tw"><table class="t"><thead><tr><th>Symbol</th><th class="r">Value</th><th class="r">Gain</th><th class="r">Positions</th></tr></thead><tbody>' + rows + '</tbody></table></div></details></div>';
}
let tiles = [];
function drawHeat() {
  const s = el('d-hm');
  if (!s || !s.clientWidth) return;
  const W = Math.round(s.clientWidth), H = Math.round(s.clientHeight) || 380, A = ((dv.positions || {}).heat || []).filter(h => h.gross > 0);
  hw = W;
  s.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
  tiles = squarify(A.map(h => Object.assign({}, h, {v: h.gross})), 0, 0, W, H);
  s.setAttribute('aria-label', 'Heatmap of the ' + A.length + ' largest symbols by value, coloured by gain or loss; the values table follows');
  s.innerHTML = tiles.map((t, i) => {
    const [bg, fg] = heatColor(t.pct), f = fits(t), X = (t.x + 7).toFixed(1);
    return '<rect data-i="' + i + '" x="' + (t.x + 1).toFixed(1) + '" y="' + (t.y + 1).toFixed(1) + '" width="' + Math.max(0, t.w - 2).toFixed(1) + '" height="' + Math.max(0, t.h - 2).toFixed(1) + '" rx="7" fill="' + bg + '"/>' +
      (f.b ? '<text class="b" x="' + X + '" y="' + (t.y + 19).toFixed(1) + '" fill="' + fg + '">' + esc(t.sym) + '</text>' : '') + (f.p ? '<text class="p" x="' + X + '" y="' + (t.y + 35).toFixed(1) + '" fill="' + fg + '">' + pc(t.pct) + '</text>' : '') +
      (f.m ? '<text class="m" x="' + X + '" y="' + (t.y + 51).toFixed(1) + '" fill="' + fg + '">' + usd(t.gross) + '</text>' : '');
  }).join('');
  hdet(tiles.find(t => t.sym === hsel) || tiles[0]);
}
let hsel = '';
function hdet(t) {
  const d = el('d-hd');
  if (!t || !d) return;
  hsel = t.sym;
  el('d-hm').querySelectorAll('rect').forEach(r => r.classList.toggle('sel', tiles[+r.dataset.i] === t));
  const ss = (t.sleeves || []).map(nm);
  d.innerHTML = '<b>' + esc(t.sym) + '</b> · ' + esc(lab('cls', t.cls)) + '<br>' + usd(t.value) + (Math.abs((t.gross || 0) - Math.abs(t.value || 0)) > 1 ? nb(' net (' + usd(t.gross) + ' gross)') : '') + '\u00a0· <span class="dk-' + tn(t.pct) + '">' + nb(pc(t.pct) + ' (' + usd(t.pnl, 1) + ')') + '</span>\u00a0· ' +
    nb(n0(t.n) + (t.n === 1 ? ' position' : ' positions')) + (ss.length ? '<br><span class="mu">' + esc(ss.join('\u00a0· ')) + '</span>' : '');
}

// ---- the engine, closed trades, the trade log and scorecards -------------------------------------------------------------
function engSec() {
  const e = dv.engine || {}, t = e.today || {}, ST = {ok: 'up', warn: 'wn'}, kv = (a, b) => b ? '<dt>' + a + '</dt><dd>' + b + '</dd>' : '';
  const f = (l, v) => '<dl><dt>' + l + '</dt><dd>' + n0(v) + '</dd></dl>';
  return head('eng', 'Automation', 'Desk engine') + '<div class="card dk-eg"><div><span class="st ' + (ST[e.state] || 'dn') + '">' + esc(e.label || '') + '</span><dl class="dk-ek">' +
    kv('Last pass', e.last_pass ? M.wd(e.last_pass) + ' ET' : '') + kv('Next open', e.next_open ? M.wd(e.next_open) + ' ET' : '') +
    kv('Every', isN(e.every_s) ? num(e.every_s, 0) + ' s' : '') + kv('Passes', isN(e.passes) ? n0(e.passes) + ' · ' + n0(e.errors) + (e.errors === 1 ? ' error' : ' errors') : '') +
    kv('Health', esc(e.health || '')) + kv('Live orders', n0(e.live_orders)) + '</dl></div>' +
    (t.date ? '<div><p class="dk-alh">' + esc(M.day(t.date)) + '</p><div class="dk-ef">' + f('Signals', t.signals) + '<span aria-hidden="true">→</span>' + f('Orders', t.orders) + '<span aria-hidden="true">→</span>' + f('Fills', t.fills) + '</div></div>' : '') + '</div>';
}
// a table that stays one for a screen reader when a phone lays its rows out as lines (explicit roles; each cell names its
// column for the eye)
function tbl(cap, H, R) {
  const at = (c, i) => (c[1] ? ' class="' + c[1] + '"' : '') + (i ? ' data-l="' + H[i][0] + '"' : '');
  return '<div class="tw"><table class="t dk-tb" role="table">' + (cap ? '<caption>' + cap + '</caption>' : '') + '<thead role="rowgroup"><tr role="row">' +
    H.map(h => '<th role="columnheader"' + (h[1] ? ' class="' + h[1] + '"' : '') + '>' + h[0] + '</th>').join('') + '</tr></thead><tbody role="rowgroup">' +
    R.map(r => '<tr role="row">' + r.map((c, i) => i ? '<td role="cell"' + at(c, i) + '>' + c[0] + '</td>' : '<th role="rowheader" scope="row"' + at(c, 0) + '>' + c[0] + '</th>').join('') + '</tr>').join('') + '</tbody></table></div>';
}
function closedSec() {
  const c = dv.closed || {}, R = c.rows || [], mx = Math.max(0.01, ...R.map(r => Math.abs(r.pct || 0)));
  const bar = v => { const w = Math.min(50, 50 * Math.abs(v) / mx), k = v < 0 ? 'n' : 'p'; return w < 1.2 ? '<i class="o ' + k + '"></i>' : '<i class="' + k + '" data-w="' + w.toFixed(1) + '"></i>'; };
  const log = tbl('', [['Symbol'], ['Sleeve'], ['Opened'], ['Closed'], ['Hold', 'r'], ['P' + AMP.trim() + 'L', 'r'], ['%', 'r'], ['Why']], R.map(r => [
    [esc(r.sym) + (r.side === 'short' ? ' <small>short</small>' : '')], [esc(nm(r.sleeve)), 'nm'], [esc(md(r.opened)) + ' <small>' + price(r.entry) + '</small>'], [esc(md(r.closed)) + ' <small>' + price(r.exit) + '</small>'],
    [isN(r.days) ? num(r.days, 1) + ' d' : '—', 'r'], [usd(r.pnl, 1), 'r dk-' + tn(r.pnl)], [pc(r.pct), 'r dk-' + tn(r.pct)], [esc(lab('why', r.why))]]));
  return head('closed', 'Track record', 'Closed trades', n0(c.n) + ' closed · ' + n0(c.wins) + ' won' + (isN(c.win) ? ' (' + num(c.win, 1) + '%)' : '') + ' · realized ' + usd(c.realized, 1)) + '<div class="card"><div class="dk-crs">' +
    R.slice(0, ui.cn).map(r => '<div class="dk-cr"><div><div class="y">' + esc(r.sym) + '</div><div class="w">' + esc(nm(r.sleeve)) + '</div></div><div class="dk-cb" aria-hidden="true">' + bar(r.pct || 0) + '</div><div class="r dk-' + tn(r.pct) + '">' + pc(r.pct) +
      '</div><div class="r s dk-' + tn(r.pnl) + '">' + usd(r.pnl, 1) + '</div></div>').join('') + '</div>' + (R.length > ui.cn ? '<button type="button" class="dk-more" data-more="c">Show all ' + R.length + '</button>' : '') +
    '<details class="dk-vt"><summary>Trade log · newest ' + R.length + '</summary>' + log + '</details></div>';
}
function scSec() {
  const s = dv.scorecards || {}, R = s.rows || [], C = {PASS: 'p', FAIL: 'f'};
  const cr = r => '<span class="dk-cri" role="img" aria-label="' + esc(CRIT.map(c => c[1] + ' ' + String((r.crit || {})[c[0]] || 'pending').toLowerCase()).join(', ')) + '">' + CRIT.map(c => '<i class="' + (C[(r.crit || {})[c[0]]] || '') + '"></i>').join('') + '</span>';
  const rows = R.slice(0, ui.sn).map(r => [[esc(r.name) + '<small>' + esc(lab('family', r.family)) + (r.research ? ' · research ' + esc(r.research.grade) + ': ' + esc(r.research.why) : '') + '</small>', 'nm'],
    [n0(r.trades) + (r.small ? ' <span class="dk-c sm">small sample</span>' : ''), 'r'], [isN(r.win) ? num(r.win, 1) + '%' : '—', 'r'], [pc(r.avg_ret), 'r dk-' + tn(r.avg_ret)],
    [isN(r.avg_hold) ? num(r.avg_hold, 1) + ' d' : '—', 'r'], [usd(r.realized, 1), 'r dk-' + tn(r.realized)],
    [r.verdict ? '<span class="dk-c ' + (VERD[r.verdict] || '') + '">' + esc(lab('verdict', r.verdict)) + '</span>' : '—'], [cr(r)]]);
  const key = 'Checks, in order: ' + CRIT.map(c => c[1]).join(', ') + ' · <span class="dk-cri"><i class="p"></i></span> pass <span class="dk-cri"><i class="f"></i></span> fail <span class="dk-cri"><i></i></span> pending';
  return head('sc', 'Per sleeve', 'Scorecards', n0(R.length) + ' sleeves with a closed trade · ' + n0(s.min_trades) + ' trades make a full sample') + '<div class="card">' +
    tbl(key, [['Sleeve'], ['Trades', 'r'], ['Win', 'r'], ['Avg', 'r'], ['Hold', 'r'], ['Realized', 'r'], ['Verdict'], ['Checks']], rows) + (R.length > ui.sn ? '<button type="button" class="dk-more" data-more="s">Show all ' + R.length + '</button>' : '') + '</div>';
}

// ---- drawing ---------------------------------------------------------------------------------------------------------------
// what Find a sleeve searches: the name, the line, the id and every label the row carries
function hay(r) {
  return [r.name, r.desc, r.id, lab('family', r.family), lab('cls', r.cls), lab('style', r.style), r.tf ? lab('tf', r.tf) : '', lab('state', r.state), r.verdict ? lab('verdict', r.verdict) : ''].join(' ').toLowerCase();
}
function draw() {
  byId = {};
  rowc = {};
  (sl ? sl.rows : []).forEach(r => { byId[r.id] = r; r._h = hay(r); });
  P.innerHTML = sec('over', 'Overview', over()) + sec('curve', 'Chart', curveSec()) + sec('lead', 'Leaders', lead()) + sec('sl', 'Sleeves', slSec()) + sec('pos', 'Positions', posSec()) +
    sec('heat', 'Heatmap', heatSec()) + sec('eng', 'Engine', engSec()) + sec('closed', 'Closed', closedSec()) + sec('sc', 'Scorecards', scSec());
  cw = hw = 0;
  groups();
  positions();
  sz(P);
  const V = window.MDV, h = decodeURIComponent(location.hash.slice(1));
  if (V && V.jump) V.jump();
  deep = h.startsWith('d-') ? h : '';
  wide();
}
// the curve and the heatmap are drawn to their box's width: again when it changes, or once the panel shows (a deep link
// draws while the page still waits for its first edition)
let deep = '';
function wide() {
  if (!dv || !P.offsetWidth) return;
  const c = el('d-cw'), h = el('d-hm');
  if (c && Math.round(c.clientWidth) !== cw) drawCurve();
  if (h && Math.round(h.clientWidth) !== hw) drawHeat();
  const n = deep && el(deep);
  deep = '';
  if (n) n.scrollIntoView();
}
// draw only once desk.css applies, so nothing is laid out twice (it loads beside this file)
function styled(f, n = 0) { if (getComputedStyle(P).getPropertyValue('--dk').trim() === '1' || n > 100) f(); else setTimeout(() => styled(f, n + 1), 50); }
function wait(t, retry) {
  P.innerHTML = '<div class="card dk-none" id="d-wait"><p>' + esc(t) + '</p>' + (retry ? '<button type="button" class="dk-more" data-retry>Try again</button>' : '') + '</div>';
}
function load() {
  if (busy) return;
  busy = 1;
  const get = u => fetch(u, {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  Promise.all([get('deskview.json'), get('sleeves.json').catch(() => null)]).then(([d, s]) => {
    busy = 0;
    stale = 0;
    if (!d || d.schema !== SCH.d || !d.overview || !d.labels) throw new Error('schema');
    if (dv && d.generated_at === dv.generated_at && (!s || !sl || s.generated_at === sl.generated_at)) return;
    dv = d;
    sl = s && s.schema === SCH.s && Array.isArray(s.rows) ? s : null;
    pj = null;
    pjP = null;
    styled(draw);
  }).catch(() => { busy = 0; if (!dv) wait('The desk’s numbers could not be loaded.', 1); });
}

// ---- events ------------------------------------------------------------------------------------------------------------------
P.addEventListener('click', e => {
  const t = e.target, b = t.closest('button, rect'), ds = b ? b.dataset : {};
  if ('retry' in ds) { wait('Loading the desk…'); return load(); }
  if (!b || !dv) return;
  if (ds.cm) { ui.m = ds.cm; P.querySelectorAll('[data-cm]').forEach(x => x.setAttribute('aria-pressed', x === b)); drawCurve(); }
  else if (ds.lv) { ui.lv = ds.lv; P.querySelector('.dk-lb').dataset.v = ds.lv; P.querySelectorAll('[data-lv]').forEach(x => x.setAttribute('aria-pressed', x === b)); }
  else if (b.classList.contains('dk-li')) reveal(ds.id);
  else if (ds.gb || ds.f || ds.s) {
    if (ds.gb) ui.g = ds.gb; else if (ds.f) ui.f = ds.f; else ui.s = ds.s;
    if (ds.gb) keep();
    ui.gn = {};
    el('d-xc').innerHTML = controls();
    groups();
  }
  else if (b.id === 'd-fb') find();
  else if (b.classList.contains('dk-rb')) { const r = b.closest('.dk-r'), on = b.getAttribute('aria-expanded') !== 'true'; sel = on ? r.dataset.id : ''; P.querySelectorAll('.dk-r.on').forEach(x => { if (x !== r) strip(x, false); }); strip(r, on); }
  else if (ds.more === 'g') { const d = b.closest('.dk-g'); ui.gn[d.dataset.g] = 1e9; fill(d); }
  else if (ds.more === 'p') { ui.pn = ui.pn < 40 ? 40 : ui.pn + 40; positions(); }
  else if (ds.more === 'c') { ui.cn = 1e9; redo('closed', closedSec); }
  else if (ds.more === 's') { ui.sn = 1e9; redo('sc', scSec); }
  else if (ds.pf) { ui.pf = ds.pf; ui.pn = 10; positions(); }
  else if ('pall' in ds || 'spAll' in ds) {
    b.disabled = true;
    b.textContent = 'Loading…';
    const r = b.closest('.dk-r');
    loadPos().then(() => { if (r) strip(r, true); else { ui.pn = 10; positions(); } }).catch(() => { b.disabled = false; b.textContent = 'Could not load. Try again'; });
  }
  else if (b.tagName === 'rect') hdet(tiles[+b.dataset.i]);
});
function redo(id, f) { const s = el('d-' + id); s.innerHTML = f(); sz(s); }
P.addEventListener('toggle', e => {
  const d = e.target;
  if (!d.classList || !d.classList.contains('dk-g')) return;
  const o = new Set(ui.o[ui.g] || []), n = o.size, g = d.dataset.g;
  if (d.open) { o.add(g); if (!d.querySelector('.dk-rs').firstChild) fill(d); } else o.delete(g);
  if (o.size === n) return;
  ui.o[ui.g] = [...o];
  keep();
}, true);
// "/" on the Desk tab opens Find a sleeve (it runs first; Look up keeps "/" on every other tab)
D.addEventListener('keydown', e => {
  const V = window.MDV, k = el('keys');
  if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey || !V || V.tab() !== 'desk' || !sl || (k && /on$/.test(k.textContent))) return;
  if (e.target.closest && e.target.closest('input,textarea,select,[contenteditable],dialog')) return;
  e.preventDefault();
  e.stopImmediatePropagation();
  find();
}, true);
let rz = 0;
addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(wide, 150); });
D.addEventListener('md:tab', e => { if (e.detail === 'desk') { if (!dv || stale) load(); else wide(); } });
D.addEventListener('md:edition', () => { if (!dv) return; if (window.MDV && window.MDV.tab() === 'desk') { wide(); load(); } else stale = 1; });
if (window.MDV && window.MDV.tab() === 'desk') load();
})();
