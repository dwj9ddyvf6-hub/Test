/* Master Desk terminal, the Market tab: mkt1's market.json drawn as GrokBot Desk's ChartsLector tab (the Mood Ring, the
   Market Pulse, breadth, risk appetite, the theme and sector heatmap and rotation; his code copied: clGauge, clLine,
   clBars, clHeatColor's scale, the state strips, clRotation), and the S&P 500 and Nasdaq 100 from charts.json (Muse's
   index charts, in our SVG). viz.js loads this file on the tab's first open. Labels use the page's own formatters
   (window.MD); no number the files give is recomputed. */
(() => {
const D = document, M = window.MD, V = window.MDV, el = id => D.getElementById(id), esc = M.esc, isN = M.isN, num = M.num;
const host = el('p-market');
if (!host || !el('m-idx') || !M || !V) return;
const isA = Array.isArray, f1 = v => (+v).toFixed(1), cl = (v, a, b) => Math.max(a, Math.min(b, v)), md = d => M.et(d).md;
const P1 = v => isN(v) ? M.pct(v, 1) : '—', P2 = v => isN(v) ? M.pct(v, 2) : '—', SH = v => isN(v) ? num(v * 100, 0) + '%' : '—';
const N = (v, dp) => isN(v) ? num(v, dp || 0) : '—', last = a => a[a.length - 1];
const CLC = {GREEN: '#2bb07f', BLUE: '#4a8fe0', YELLOW: '#e2bf3f', AMBER: '#e0913a', PURPLE: '#9467d0', RED: '#d4504a'};
const QC = {Leading: '#2bb07f', Improving: '#4a8fe0', Weakening: '#e2bf3f', Lagging: '#d4504a'}, QO = ['Leading', 'Improving', 'Weakening', 'Lagging'];
const PER = {d1: ['1D', '1-day', 3], w1: ['1W', '1-week', 6], m1: ['1M', '1-month', 12], m3: ['3M', '3-month', 25]};
const L1 = '#7ee0c3', L2 = '#f2d68a', L3 = '#b9a7f0';               // GrokBot's chart lines: teal, yellow, lavender
const st = {grp: 'theme', per: 'm1', all: 0, hs: null, rot: 'sector', sel: null};
const G = {};                                                      // each drawn chart: its geometry and its tap caption
let mk = null, ch = null, jobs = [], busy = 0, w0 = 0, done = 0;
// charts.json comes through viz.js: the page's one fetch of it, for the cards and these charts
const charts = () => V.charts ? V.charts() : null;

const iso = t => new Date(t * 1e3).toISOString();
const pvl = (d, t) => md(d) + ' close' + (isN(t) ? ' · updated ' + M.wd(iso(t)) + ' ET' : '');
const pick = n => { const k = Math.ceil(n / 30), o = []; for (let i = n - 1; i >= 0; i -= k) o.unshift(i); return o; };   // ≤ 30 rows
const back = (a, f) => pick(a.length).reverse().map(i => f(a[i], i));                       // a table's rows, the newest first
const vt = (cap, head, rows) => '<details class="vt"><summary>Chart values</summary><div class="tw"><table class="t"><caption>' + esc(cap) + '</caption><thead><tr>' +
  head.map((h, i) => '<th' + (i ? ' class="r"' : '') + '>' + h + '</th>').join('') + '</tr></thead><tbody>' + rows.map(r => '<tr>' +
  r.map((c, i) => i ? '<td class="r">' + c + '</td>' : '<th scope="row">' + c + '</th>').join('') + '</tr>').join('') + '</tbody></table></div></details>';
// GrokBot's dark chart panel: a teal title, a tag at the right, the drawing, a legend, the tap caption
const panel = (id, title, tag, legend, cap) => '<figure class="cp"><figcaption class="cpt"><span class="cpn">' + title + '</span><span class="cpb">' + tag +
  '</span></figcaption><div class="cbx" id="' + id + '"></div>' + (legend ? '<p class="cpl">' + legend + '</p>' : '') + '<p class="cpc" id="' + id + '-c" aria-live="polite">' + esc(cap) + '</p></figure>';
const key = (c, t, dash) => '<span><i class="' + (dash ? 'kd' : '') + '" data-c="' + c + '"></i>' + t + '</span>';
// a section in the design system's markup (DESIGN_COPY §4): kicker, title, one line, provenance at the right; the empty
// <section> shells are index.html's, so a deep link to one (#m-heat) opens the tab before this file loads
const sec = (id, kick, title, sub, pv, body) => '<div class="shd"><div class="sht"><p class="kick">' + esc(kick) + '</p><h2 id="h-' + id + '">' + title + '</h2>' +
  (sub ? '<p class="sub">' + sub + '</p>' : '') + '</div><span class="pv">' + esc(pv) + '</span></div><div class="card">' + body + '</div>';
const tile = (l, v, s, c, x) => '<div class="tile' + (c ? ' ' + c : '') + '"><div class="l">' + l + '</div><div class="v">' + v + '</div>' + (s ? '<div class="s">' + s + '</div>' : '') + (x ? '<p class="tsd">' + x + '</p>' : '') + '</div>';
const ln = (x1, y1, x2, y2, a) => '<line x1="' + f1(x1) + '" y1="' + f1(y1) + '" x2="' + f1(x2) + '" y2="' + f1(y2) + '"' + (a || '') + '/>';
const tx = (x, y, t, a) => '<text x="' + f1(x) + '" y="' + f1(y) + '"' + (a || '') + '>' + t + '</text>';
const rc = (x, y, w, h, a) => '<rect x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(w) + '" height="' + f1(h) + '"' + (a || '') + '/>';
const xh = (t, b) => '<line class="xh" y1="' + t + '" y2="' + b + '"/>', END = ' text-anchor="end"';
const svg = (W, H, lab, g, c) => '<svg class="' + (c || 'cps') + '" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="' + esc(lab) + '">' + g + '</svg>';

// right-axis tags, GrokBot's placement: by priority, 17 px apart inside [a, b]; a tag with no room is dropped
function place(T, a, b, gap) {
  const done = [];
  T.slice().sort((p, q) => p.pr - q.pr).forEach(t => {
    const free = y => y >= a && y <= b && done.every(q => Math.abs(q.y - y) >= gap);
    let y = cl(t.y0, a, b);
    if (!free(y)) { y = null; for (let k = 1; k < 300 && y === null; k++) y = free(t.y0 + k) ? t.y0 + k : free(t.y0 - k) ? t.y0 - k : null; }
    if (y !== null) { t.y = y; done.push(t); }
  });
  return done;
}
const tag = (t, x, w, ink) => (Math.abs(t.y - t.y0) > 3 ? ln(x - 8, t.y0, x, t.y, ' stroke="' + t.c + '" stroke-width="1.2"') : '') + rc(x, t.y - 8, w, 16, ' rx="3" fill="' + t.c + '"') +
  tx(x + 3, t.y + 4, esc(t.t), ' class="tgt' + (ink ? ' ' + ink : '') + '"');

// ---- GrokBot's clLine: lines over shaded bands, gridlines labelled at the right, three dates, an end dot per line; ours
// adds Codex's end-value pills and a dashed reference line ------------------------------------------------------------------
function line(W, o) {
  const H = o.H || 200, pl = 8, pr = 46, pt = 10, pb = 24, n = o.d.length, lo = o.lo, hi = o.hi, f = o.f || (z => num(z, 0)), fp = o.fp || f;
  const x = i => pl + (W - pl - pr) * i / (n - 1), y = v => pt + (H - pt - pb) * (hi - v) / (hi - lo);
  let g = '';
  (o.bands || []).forEach(([a, b, c]) => { const ya = y(Math.max(a, lo)), yb = y(Math.min(b, hi)); if (ya > yb) g += rc(pl, yb, W - pl - pr, ya - yb, ' fill="' + c + '" opacity=".2"'); });
  const T = o.pills ? place(o.s.map((s, k) => { const v = s.v[n - 1]; return isN(v) ? {y0: y(v), c: s.c, t: fp(v), pr: k} : null; }).filter(Boolean), pt + 8, H - pb - 8, 17) : [];
  for (let k = 0; k <= o.t; k++) {
    const v = lo + (hi - lo) * k / o.t, yy = y(v);
    g += ln(pl, yy, W - pr, yy, ' class="gd"') + (T.every(q => Math.abs(q.y - yy) > 12) ? tx(W - pr + 6, yy + 4, f(v)) : '');
  }
  if (isN(o.ref)) g += ln(pl, y(o.ref), W - pr, y(o.ref), ' class="rf"');
  o.s.forEach(s => {
    let p = '', on = 0;
    s.v.forEach((z, i) => { if (!isN(z)) { on = 0; return; } p += (on ? 'L' : 'M') + f1(x(i)) + ' ' + f1(y(z)); on = 1; });
    g += '<path d="' + p + '" fill="none" stroke="' + s.c + '" stroke-width="' + (s.w || 2.2) + '"' + (s.dash ? ' stroke-dasharray="' + s.dash + '"' : '') + '/>';
    if (isN(s.v[n - 1])) g += '<circle cx="' + f1(x(n - 1)) + '" cy="' + f1(y(s.v[n - 1])) + '" r="3.2" fill="' + s.c + '"/>';
  });
  g += [...new Set([0, Math.floor((n - 1) / 2), n - 1])].map(i => tx(x(i), H - 6, md(o.d[i]), i ? i === n - 1 ? END : ' text-anchor="middle"' : '')).join('');
  g += T.map(t => tag(t, W - pr + 3, pr - 5, 'k')).join('') + xh(pt, H - pb);
  return {s: svg(W, H, o.label, g), x0: pl, x1: W - pl - pr, n, X: x};
}
// GrokBot's clBars: a diverging bar a day, up above the zero line and down below it, on one scale
function bars(W, o) {
  const H = 170, pl = 8, pr = 46, pt = 10, pb = 24, n = o.d.length, mx = Math.max(1, ...o.up, ...o.dn), mid = pt + (H - pt - pb) / 2, hh = (H - pt - pb) / 2, bw = (W - pl - pr) / n;
  let g = '';
  for (let i = 0; i < n; i++) {
    const x = pl + i * bw, w = Math.max(1, bw - 1), hu = hh * o.up[i] / mx, hd = hh * o.dn[i] / mx;
    g += rc(x, mid - hu, w, hu, ' class="b1"') + rc(x, mid, w, hd, ' class="b2"');
  }
  g += ln(pl, mid, W - pr, mid, ' class="zl"') + tx(W - pr + 6, pt + 10, mx) + tx(W - pr + 6, mid + 4, 0) + tx(W - pr + 6, H - pb, mx) + tx(pl, H - 6, md(o.d[0])) + tx(W - pr, H - 6, md(o.d[n - 1]), END) + xh(pt, H - pb);
  return {s: svg(W, H, o.label, g), x0: pl, x1: W - pl - pr, n, X: i => pl + (i + .5) * bw};
}
// GrokBot's .clstrip: one cell a session, coloured by the Pulse's state (runs of a state drawn as one rect)
function strip(W, days, states) {
  const n = days.length, w = W / n;
  let g = '', a = 0;
  for (let i = 1; i <= n; i++) if (i === n || days[i].sc !== days[a].sc) { g += rc(a * w, 0, (i - a) * w + .4, 22, ' fill="' + (CLC[states[days[a].sc]] || '#5f667a') + '"'); a = i; }
  return {s: g + xh(0, 22), x0: 0, x1: W, n, X: i => (i + .5) * w};
}
// GrokBot's clGauge: the semicircle in his bands, the band the needle sits in at full strength, the others at .55
function gauge(v, bands) {
  const cx = 150, cy = 154, R = 130, r0 = 96, a = p => Math.PI * (1 - p / 100), Pt = (p, r) => [f1(cx + r * Math.cos(a(p))), f1(cy - r * Math.sin(a(p)))];
  const B = bands.slice().sort((p, q) => p.lo - q.lo);
  let s = '';
  B.forEach((b, i) => {
    const lo = b.lo, hi = i + 1 < B.length ? B[i + 1].lo : 100, [x1, y1] = Pt(lo, R), [x2, y2] = Pt(hi, R), [x3, y3] = Pt(hi, r0), [x4, y4] = Pt(lo, r0);
    s += '<path d="M' + x1 + ' ' + y1 + 'A' + R + ' ' + R + ' 0 0 1 ' + x2 + ' ' + y2 + 'L' + x3 + ' ' + y3 + 'A' + r0 + ' ' + r0 + ' 0 0 0 ' + x4 + ' ' + y4 + 'Z" fill="' + (CLC[b.band] || '#5f667a') +
      '" opacity="' + (v >= lo && (v < hi || hi === 100) ? 1 : .55) + '"/>';
    if (lo > 0) { const [px, py] = Pt(lo, R + 10); s += tx(+px, +py, lo, ' text-anchor="middle"'); }
  });
  const [nx, ny] = Pt(cl(v, 0, 100), R - 4);
  return s + ln(cx, cy, +nx, +ny, ' stroke="#fff" stroke-width="4" stroke-linecap="round"') + '<circle cx="' + cx + '" cy="' + cy + '" r="7" fill="#fff"/>';
}

// ---- the sections ------------------------------------------------------------------------------------------------------
// the S&P 500 and Nasdaq 100: Muse's index charts (daily candles, the 20-session high and low, the 50- and 200-day
// averages, the last close), drawn as GrokBot's chart panel with his right-axis tags
const IDX = [['SPY', 'S&P 500'], ['QQQ', 'Nasdaq 100']], MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
const okBars = b => b && isA(b.d) && b.d.length > 20 && ['o', 'h', 'l', 'c'].every(k => isA(b[k]) && b[k].length === b.d.length && b[k].every(isN));
function lv(b) {                                   // the levels the chart labels, each one of the file's own numbers
  const n = b.d.length, k = n - 20, H = b.h.slice(k), Lw = b.l.slice(k), hi = Math.max(...H), lo = Math.min(...Lw), a = (s, i) => isA(b[s]) && isN(b[s][i]) ? b[s][i] : null;
  return {n, last: b.c[n - 1], up: b.c[n - 1] >= b.o[n - 1], hi, hiD: b.d[k + H.indexOf(hi)], lo, loD: b.d[k + Lw.indexOf(lo)], m50: a('sma50', n - 1), m200: a('sma200', n - 1)};
}
function candles(W, b, sym, name) {
  const nar = W < 520, L = lv(b), n = L.n, $ = v => M.px(v, 0), T = 10, AX = 20, PH = nar ? 210 : 260, H = T + PH + AX, R = nar ? 84 : 92, PW = W - 4 - R;
  const pts = [...b.h, ...b.l, ...['sma50', 'sma200'].flatMap(s => isA(b[s]) ? b[s].filter(isN) : [])];
  let lo = Math.min(...pts), hi = Math.max(...pts);
  const pad = (hi - lo) * .06; lo -= pad; hi += pad;
  const X = i => 4 + (i + .5) * PW / n, Y = v => T + (hi - v) * PH / (hi - lo), bw = Math.max(1.2, PW / n * .66);
  let g = rc(0, 0, W, H, ' fill="#131722"');
  const sp = hi - lo, raw = sp / 5, mag = Math.pow(10, Math.floor(Math.log10(raw))), step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(q => q >= raw) || 10 * mag, GR = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) { g += ln(4, Y(v), W - R, Y(v), ' class="gd"'); GR.push([Y(v), $(v).replace(/\.00$/, '')]); }
  let lm = '', lx = -99;
  b.d.forEach((d, i) => {
    const m = d.slice(0, 7), mo = +d.slice(5, 7);
    if (m === lm) return;
    lm = m;
    if (X(i) < lx || i < 2) return;
    lx = X(i) + 34;
    g += ln(X(i), T, X(i), T + PH, ' stroke="#1c2029"') + tx(X(i) + 2, H - 6, MON[mo - 1]);
  });
  for (let i = 0; i < n; i++) {
    const c = b.c[i] >= b.o[i] ? '#26a69a' : '#ef5350';
    g += ln(X(i), Y(b.h[i]), X(i), Y(b.l[i]), ' stroke="' + c + '"') + rc(X(i) - bw / 2, Y(Math.max(b.o[i], b.c[i])), bw, Math.max(1, Math.abs(Y(b.o[i]) - Y(b.c[i]))), ' fill="' + c + '"');
  }
  [['sma50', '#ff9800'], ['sma200', '#ab47bc']].forEach(([s, c]) => {
    if (!isA(b[s])) return;
    const p = b[s].map((v, i) => isN(v) ? f1(X(i)) + ',' + f1(Y(v)) : null).filter(Boolean);
    if (p.length > 1) g += '<polyline points="' + p.join(' ') + '" fill="none" stroke="' + c + '" stroke-width="1.6"/>';
  });
  g += ln(4, Y(L.hi), W - R, Y(L.hi), ' stroke="#ef9a9a" stroke-width="1.2" stroke-dasharray="5 4"') + ln(4, Y(L.lo), W - R, Y(L.lo), ' stroke="#4dd0b5" stroke-width="1.2" stroke-dasharray="5 4"');
  const TG = place([{y0: Y(L.last), c: L.up ? '#26a69a' : '#ef5350', t: $(L.last).slice(1), pr: 0}, {y0: Y(L.hi), c: '#c62828', t: 'High ' + $(L.hi).slice(1), pr: 1},
    {y0: Y(L.lo), c: '#1d7f75', t: 'Low ' + $(L.lo).slice(1), pr: 2}].concat(isN(L.m50) ? [{y0: Y(L.m50), c: '#ff9800', t: '50d ' + $(L.m50).slice(1), pr: 3}] : [])
    .concat(isN(L.m200) ? [{y0: Y(L.m200), c: '#ab47bc', t: '200d ' + $(L.m200).slice(1), pr: 4}] : []), T + 8, T + PH - 8, 17);
  GR.forEach(([y, t]) => { if (TG.every(q => Math.abs(y - q.y) >= 14) && y > T + 6 && y < T + PH - 2) g += tx(W - R + 5, y + 3.5, t); });
  g += TG.map(t => tag(t, W - R + 2, R - 4, t.c === '#ff9800' ? 'k' : '')).join('') + xh(T, T + PH);
  const lab = name + ' (' + sym + ') daily, ' + md(b.d[0]) + ' to ' + md(b.d[n - 1]) + ': last close ' + $(L.last) + '; 20-session high ' + $(L.hi) + ' on ' + md(L.hiD) + ', low ' + $(L.lo) + ' on ' + md(L.loD) +
    (isN(L.m50) ? '; 50-day average ' + $(L.m50) : '') + (isN(L.m200) ? '; 200-day average ' + $(L.m200) : '');
  return {s: svg(W, H, lab, g, 'cps cpx'), x0: 4, x1: PW, n, X};
}
function idx() {
  const S = IDX.filter(([s]) => ch && okBars(ch.syms[s]));
  if (!S.length) return '';
  const body = S.map(([s, name]) => {
    const b = ch.syms[s], L = lv(b), $ = v => M.px(v, 0), id = 'mc-' + s.toLowerCase(), n = L.n;
    jobs.push({id, draw: W => candles(W, b, s, name), cap: i => M.day(b.d[i]) + ' · open ' + $(b.o[i]) + ' · high ' + $(b.h[i]) + ' · low ' + $(b.l[i]) + ' · close ' + $(b.c[i])});
    const rows = [['Last close', md(b.d[n - 1]), $(L.last)], ['20-session high', md(L.hiD), $(L.hi)], ['20-session low', md(L.loD), $(L.lo)]]
      .concat(isN(L.m50) ? [['50-day average', md(b.d[n - 1]), $(L.m50)]] : []).concat(isN(L.m200) ? [['200-day average', md(b.d[n - 1]), $(L.m200)]] : [])
      .concat(pick(n).reverse().map(i => ['Close', md(b.d[i]), $(b.c[i])]));
    return '<div>' + panel(id, s + ' · ' + name, 'daily · <b>6 months</b>', key('5', 'last 20 sessions’ high and low', 1) + key('6', '50-day') + key('7', '200-day'),
      'Tap the chart for a day’s prices.') + vt(name + ' (' + s + ')', ['What', 'When', 'Price'], rows) + '</div>';
  }).join('');
  return sec('m-idx', 'Index charts', 'S&P 500 and Nasdaq 100', '', pvl(ch.as_of, ch.generated_at), '<div class="ixg">' + body + '</div>');
}

// the Mood Ring (mkt1's mood block, Cboe's VIX family): gauge, number, word and date; the four parts; the term structure
// in the divergence chip's place (his divergence names are not published); the year over his bands
const PARTS = [['vix', 'VIX level', 'vix', 2], ['term', 'VIX vs 3-month VIX', 'term', 3], ['skew', 'SKEW (tail-risk demand)', 'skew', 2], ['vvix', 'VVIX (volatility of VIX)', 'vvix', 2]];
function mood(m) {
  if (!m || !isN(m.score) || !isA(m.bands) || !isA(m.days)) return '';
  const I = m.inputs || {}, Pp = m.parts || {}, Wt = m.weights || {}, d = m.days.filter(x => isN(x.v)), B = m.bands.slice().sort((p, q) => p.lo - q.lo);
  const tone = /bigger/.test(m.word) ? 'dn' : /smaller/.test(m.word) ? 'up' : 'wn';
  const parts = PARTS.map(([k, name, ik, dp]) => isN(Pp[k]) ? '<div class="gpr"><p class="gph"><span>' + name + ' <small>· weight&nbsp;' + num(Wt[k], 0) + '%</small></span><span>' +
    N(I[ik], dp) + ' → ' + num(Pp[k], 1) + '/100</span></p><p class="gpb"><i data-pw="' + cl(Pp[k], 0, 100) + '"></i></p></div>' : '').join('');
  const bw = m.backwardation ? '<span class="mp n">Backwardation: VIX ' + num(I.vix, 2) + ' at or above VIX3M ' + num(I.vix3m, 2) + '</span>'
    : isN(I.term) ? '<span class="mp y">No backwardation: VIX ' + num(I.term, 3) + '× VIX3M</span>' : '';
  if (d.length > 1) {
    const v = d.map(x => x.v);
    jobs.push({id: 'mc-mood', draw: W => line(W, {d: d.map(x => x.d), s: [{v, c: L1}], lo: 0, hi: 100, t: 4, pills: 1, fp: z => num(z, 1), bands: B.map((b, i) => [b.lo, i + 1 < B.length ? B[i + 1].lo : 100, CLC[b.band]]),
      label: 'Mood Ring score, ' + md(d[0].d) + ' to ' + md(last(d).d) + ': now ' + num(m.score, 1) + ', ' + m.word + '; low ' + num(Math.min(...v), 1) + ', high ' + num(Math.max(...v), 1)}),
      cap: i => M.day(d[i].d) + ' · Mood Ring ' + num(d[i].v, 1)});
  }
  const body = '<div class="gw"><div class="gg" role="img" aria-label="' + esc('Mood Ring ' + num(m.score, 1) + ' of 100: ' + m.word + ', close ' + md(m.as_of)) + '"><svg viewBox="0 0 300 168" aria-hidden="true">' +
    gauge(m.score, B) + '</svg><p class="gn">' + num(m.score, 1) + '</p><p class="gb"><span class="bdg ' + tone + '">' + esc(m.word) + '</span><span>close ' + md(m.as_of) + '</span></p></div>' +
    '<div><div class="gp">' + parts + '</div>' + (bw ? '<p class="mps">' + bw + '</p>' : '') + '</div></div>' +
    (d.length > 1 ? panel('mc-mood', 'Mood Ring', 'daily · <b>last 12 months</b>', key('1', 'Mood Ring score (0-100)') + '<span>shaded: his GREEN → RED bands</span>', 'Tap the chart for a day’s score.') +
      vt('Mood Ring score', ['Session', 'Score'], back(d, x => [md(x.d), num(x.v, 1)])) : '');
  return sec('m-mood', m.credit || 'VIX Mood Ring', 'Mood Ring', esc(m.basis || ''), md(m.as_of) + ' close · ' + (m.source || 'Cboe'), body);
}

// the Market Pulse and his risk model on QQQE and RSP: state badges, risk scores, 130-session strips, the checks, the history
const CHK = [['above_rising_5ema', 'Above a rising 5-day EMA'], ['daily_buy', 'Daily buy'], ['weekly_buy', 'Weekly buy'], ['breadth_uptrend', 'Breadth uptrend']];
function pulse(p) {
  const S = p && isA(p.states) ? p.states : [], F = (p && isA(p.funds) ? p.funds : []).filter(f => f && isA(f.days) && f.days.length > 1);
  if (!F.length) return '';
  const badge = s => '<span class="ps ' + esc(s) + '">' + esc(s) + '</span>';
  let body = '<div class="t4">' + F.map(f => tile('Pulse · ' + esc(f.sym), badge(f.state), 'score ' + num(f.score, 0) + ' of ' + (S.length - 1))).join('') +
    F.map(f => tile('Risk model · ' + esc(f.sym), N(f.ram, 1), esc(String(f.ram_level || '').toLowerCase()))).join('') + '</div>';
  F.forEach(f => {
    const id = 'mc-ps-' + f.sym.toLowerCase(), d = f.days;
    jobs.push({id, draw: W => { const r = strip(W, d, S); r.s = svg(W, 22, f.sym + ' Pulse, last ' + d.length + ' sessions: ' + d.length + ' cells from ' + md(d[0].d) + ' (' + S[d[0].sc] + ') to ' + md(last(d).d) + ' (' + S[last(d).sc] + ')', r.s, 'cps sp'); return r; },
      cap: i => M.day(d[i].d) + ' · ' + f.sym + ' ' + S[d[i].sc] + ' (score ' + d[i].sc + ' of ' + (S.length - 1) + ')' + (isN(d[i].ram) ? ' · risk ' + num(d[i].ram, 1) : '')});
    body += '<p class="rl"><span><b>' + esc(f.sym) + '</b> · last ' + d.length + ' sessions</span><span>' + md(d[0].d) + ' → ' + md(last(d).d) + '</span></p><div class="spw" id="' + id + '" data-cap="mc-ps-c"></div>';
  });
  body += '<p class="cpc" id="mc-ps-c" aria-live="polite">Tap a strip for a day’s state.</p>';
  body += '<p class="mps">' + S.slice().reverse().map(s => '<span class="mp"><i class="sw" data-c="' + esc(s) + '"></i>' + esc(s) + '</span>').join('') + '</p>';
  const yn = (c, k) => c[k] ? '<td class="y">✓<span class="sr"> yes</span></td>' : k === 'breadth_uptrend' && c.breadth_attempt ? '<td class="m">~<span class="sr"> attempt</span></td>' : '<td class="n">✗<span class="sr"> no</span></td>';
  body += '<table class="ck"><thead><tr><th>Checks</th>' + F.map(f => '<th>' + esc(f.sym) + '</th>').join('') + '</tr></thead><tbody>' + CHK.map(([k, l]) => '<tr><th scope="row">' + l + '</th>' +
    F.map(f => yn(f.checks || {}, k)).join('') + '</tr>').join('') + '</tbody></table>';
  const d0 = F[0].days, C = [L1, L2];
  jobs.push({id: 'mc-ram', draw: W => line(W, {d: d0.map(x => x.d), s: F.slice(0, 2).map((f, k) => ({v: f.days.map(x => x.ram), c: C[k], dash: k ? '5 3' : ''})), lo: 0, hi: 100, t: 4, pills: 1, fp: z => num(z, 1),
    bands: [[0, 20, '#2bb07f'], [60, 80, '#e0913a'], [80, 100, '#d4504a']], label: 'Risk model, ' + md(d0[0].d) + ' to ' + md(last(d0).d) + ': ' + F.map(f => f.sym + ' ' + num(f.ram, 1)).join(', ')}),
    cap: i => M.day(d0[i].d) + ' · ' + F.slice(0, 2).map(f => f.sym + ' ' + N((f.days[i] || {}).ram, 1)).join(' · ')});
  body += panel('mc-ram', 'Risk model', '0 low · 100 extreme · <b>daily</b>', F.slice(0, 2).map((f, k) => key(k ? '2' : '1', esc(f.sym), k)).join(''), 'Tap the chart for a day’s risk.') +
    vt('Pulse and risk model', ['Session'].concat(F.flatMap(f => [esc(f.sym), 'Risk'])), back(d0, (y, i) => [md(y.d)].concat(F.flatMap(f => { const x = f.days[i] || {}; return [esc(S[x.sc] || '—'), N(x.ram, 1)]; }))));
  return sec('m-pulse', p.credit || 'Market Action Pulse', 'Market Pulse', 'His read: GREEN when everything confirms, RED when nothing does', pvl(last(F[0].days).d, mk.generated_at), body);
}

// breadth: his score tiles, the share above the 20-, 50- and 200-day averages (participation), and the big movers
function breadth(b, pa, mv) {
  const pd = pa && isA(pa.days) ? pa.days : [], vd = mv && isA(mv.days) ? mv.days : [];
  if (!b && pd.length < 2 && vd.length < 2) return '';
  const lp = last(pd), n = (lp || last(vd) || {}).n, cmp = (u, d) => u > d ? 'up' : u < d ? 'dn' : '';
  let body = '';
  if (b) body += '<div class="t6">' + tile('Breadth score', num(b.score, 0) + '/' + num(b.of, 0), 'up/down counts vs their 5/10/21-day averages', b.score * 2 > b.of ? 'up' : 'dn') +
    tile('Up 4%+ / down 4%+', num(b.up4, 0) + ' / ' + num(b.dn4, 0), 'today', cmp(b.up4, b.dn4)) + tile('Up 13%+ / down 13%+', num(b.up13, 0) + ' / ' + num(b.dn13, 0), 'over 34 days', cmp(b.up13, b.dn13)) +
    tile('Up 25%+ / down 25%+', num(b.up25, 0) + ' / ' + num(b.dn25, 0), 'over 63 days · ' + (b.up25_ma20 ? 'above' : 'below') + ' its 20-day average', cmp(b.up25, b.dn25)) +
    (lp ? tile('Above 20 / 50 / 200-day', SH(lp.a20).slice(0, -1) + ' / ' + SH(lp.a50).slice(0, -1) + ' / ' + SH(lp.a200), 'share of stocks') : '') +
    tile('Advancers / decliners', num(b.adv, 0) + ' / ' + num(b.dec, 0), 'today', cmp(b.adv, b.dec)) + '</div>';
  if (pd.length > 1) {
    const S = [['a20', L1, '20-day'], ['a50', L2, '50-day'], ['a200', L3, '200-day']];
    jobs.push({id: 'mc-part', draw: W => line(W, {d: pd.map(x => x.d), s: S.map(([k, c]) => ({v: pd.map(x => isN(x[k]) ? x[k] * 100 : null), c})), lo: 0, hi: 100, t: 4, ref: 50, pills: 1, f: z => num(z, 0) + '%',
      label: 'Share of ' + num(n, 0) + ' stocks above their averages, ' + md(pd[0].d) + ' to ' + md(lp.d) + ': ' + S.map(([k, , w]) => w + ' ' + SH(lp[k])).join(', ')}),
      cap: i => M.day(pd[i].d) + ' · ' + S.map(([k, , w]) => w + ' ' + SH(pd[i][k])).join(' · ')});
    body += panel('mc-part', '% above averages', '20 / 50 / 200 day · <b>daily</b>', S.map(([, , w], k) => key('128'[k], w)).join('') + key('4', '50%', 1), 'Tap the chart for a day’s shares.') +
      vt('Share of stocks above their averages', ['Session', '20-day', '50-day', '200-day'], back(pd, x => [md(x.d), SH(x.a20), SH(x.a50), SH(x.a200)]));
  }
  if (vd.length > 1) {
    const lv_ = last(vd);
    jobs.push({id: 'mc-mov', draw: W => bars(W, {d: vd.map(x => x.d), up: vd.map(x => x.up4 || 0), dn: vd.map(x => x.dn4 || 0),
      label: 'Stocks up 4% or more against down 4% or more a day, ' + md(vd[0].d) + ' to ' + md(lv_.d) + ': last session ' + lv_.up4 + ' up, ' + lv_.dn4 + ' down'}),
      cap: i => M.day(vd[i].d) + ' · ' + num(vd[i].up4, 0) + ' up 4%+ · ' + num(vd[i].dn4, 0) + ' down 4%+'});
    body += panel('mc-mov', 'Big movers', 'stocks up 4%+ vs down 4%+ · <b>daily</b>', key('1', 'up 4% or more') + key('3', 'down 4% or more'), 'Tap the chart for a day’s counts.') +
      vt('Stocks up or down 4% or more', ['Session', 'Up 4%+', 'Down 4%+'], back(vd, x => [md(x.d), N(x.up4), N(x.dn4)]));
  }
  return sec('m-breadth', b && b.credit || 'Breadth', 'Breadth', isN(n) ? 'of ' + num(n, 0) + ' stocks' : '', pvl((lp || last(vd)).d, mk.generated_at), body);
}

// risk appetite: his six ratios, each against its 20-day average, and how many read risk-on each day
function risk(r) {
  if (!r || !isA(r.pairs) || !r.pairs.length) return '';
  const d = isA(r.days) ? r.days : [];
  let body = '<div class="t3">' + r.pairs.map(x => tile(esc(x.pair), '<span class="mp ' + (x.on ? 'y">risk-on' : 'n">risk-off') + '</span>', P2(x.chg_1m) + ' over 1 month', '',
    'rising = risk-' + esc(x.rising) + ' · ' + (x.above ? 'above' : 'below') + ' its 20-day average')).join('') + '</div>';
  if (d.length > 1) {
    jobs.push({id: 'mc-risk', draw: W => line(W, {H: 150, d: d.map(x => x.d), s: [{v: d.map(x => x.n), c: L1}], lo: 0, hi: r.of, t: r.of, pills: 1,
      label: 'Ratios reading risk-on, of ' + r.of + ', ' + md(d[0].d) + ' to ' + md(last(d).d) + ': now ' + r.on}), cap: i => M.day(d[i].d) + ' · ' + d[i].n + ' of ' + r.of + ' risk-on'});
    body += panel('mc-risk', 'Risk-on count', 'ratios reading risk-on · <b>of ' + r.of + '</b>', '', 'Tap the chart for a day’s count.') +
      vt('Ratios reading risk-on', ['Session', 'Risk-on'], back(d, x => [md(x.d), x.n + ' of ' + r.of]));
  }
  return sec('m-risk', r.credit || 'Risk appetite', 'Risk appetite', '<b>' + r.on + ' of ' + r.of + '</b> ratios lean risk-on', pvl(d.length ? last(d).d : mk.as_of, mk.generated_at), body);
}

// the theme and sector heatmap: GrokBot's tiles (his scale, in five steps), Codex's highlights first (the 6 strongest and
// the 6 weakest), Themes / Sectors and 1D / 1W / 1M / 3M
const hcls = (p, sc) => !isN(p) || !p ? 'z' : (p > 0 ? 'u' : 'd') + Math.max(1, Math.ceil(Math.min(1, Math.abs(p) / sc) * 5));
const tg = (k, opts, on) => '<span class="tg" role="group" aria-label="' + k + '">' + opts.map(([v, t]) => '<button type="button" data-' + k.toLowerCase() + '="' + v + '" aria-pressed="' + (v === on) + '">' + t + '</button>').join('') + '</span>';
function heatTiles() {
  const H = (mk.heat || []).filter(h => h && h.group === st.grp), per = st.per, [, word, sc] = PER[per];
  const R = H.slice().sort((a, b) => (isN(b.ret[per]) ? b.ret[per] : -1e9) - (isN(a.ret[per]) ? a.ret[per] : -1e9));
  const hl = !st.all && R.length > 12, shown = hl ? R.slice(0, 6).concat(R.slice(-6)) : R;
  const t = h => '<button class="hx ' + hcls(h.ret[per], sc) + '" type="button" data-h="' + esc(h.sym) + '" aria-pressed="' + (h.sym === st.hs) + '"><b>' + esc(h.sym) + '</b><em>' + esc(h.name) +
    '</em><span>' + P1(h.ret[per]) + '</span><small>RS ' + N(h.rs) + ' · RV ' + (isN(h.rvol) ? num(h.rvol, 2) + '×' : '—') + '</small></button>';
  const lab = R.length + ' ' + st.grp + ' funds by ' + word + ' return: strongest ' + R.slice(0, 3).map(h => h.sym + ' ' + P1(h.ret[per])).join(', ') + '; weakest ' + R.slice(-3).map(h => h.sym + ' ' + P1(h.ret[per])).join(', ');
  return '<div class="hg" role="group" aria-label="' + esc(lab) + '">' + (hl ? shown.slice(0, 6).map(t).join('') + '<i class="hsp" aria-hidden="true"></i>' + shown.slice(6).map(t).join('') : shown.map(t).join('')) + '</div>' +
    (R.length > 12 ? '<button class="more" type="button" data-all="1">' + (st.all ? 'Show the 6 strongest and 6 weakest' : 'Show all ' + R.length) + '</button>' : '') +
    '<p class="cpc hc" id="mh-c" aria-live="polite">' + esc(st.hs ? heatCap(st.hs) : 'Tap a tile for its returns.') + '</p>' +
    vt(word + ' return, ' + st.grp + ' funds', ['Fund', '1D', '1W', '1M', '3M', 'RS', 'RVol'], shown.map(h => [esc(h.sym) + ' <span class="mu">' + esc(h.name) + '</span>', P2(h.ret.d1), P2(h.ret.w1), P2(h.ret.m1), P2(h.ret.m3),
      N(h.rs), isN(h.rvol) ? num(h.rvol, 2) + '×' : '—']));
}
function heatCap(s) {
  const h = (mk.heat || []).find(x => x.sym === s);
  return h ? h.sym + ' · ' + h.name + (isN(h.close) ? ' · ' + M.px(h.close, 0) : '') + ' · 1D ' + P2(h.ret.d1) + ' · 1W ' + P2(h.ret.w1) + ' · 1M ' + P2(h.ret.m1) + ' · 3M ' + P2(h.ret.m3) +
    ' · RS ' + N(h.rs) + ' of 100 against SPY over 21 sessions · volume ' + (isN(h.rvol) ? num(h.rvol, 2) + '×' : '—') + ' its 50-day average' : '';
}
function heat() {
  const H = isA(mk.heat) ? mk.heat.filter(h => h && h.ret) : [];
  if (!H.length) return '';
  if (!H.some(h => h.group === st.grp)) st.grp = H[0].group;
  const cr = (H.find(h => h.group === st.grp) || H[0]).credit;
  return sec('m-heat', cr || 'Heatmap', 'Themes and sectors', '', pvl(mk.as_of, mk.generated_at), '<div class="tgs">' + tg('Group', [['theme', 'Themes'], ['sector', 'Sectors']], st.grp) +
    tg('Period', Object.keys(PER).map(k => [k, PER[k][0]]), st.per) + '</div>' + heatTiles());
}

// rotation: GrokBot's four quadrant lists (every width) and his RRG scatter with the 5-week tails (desktop only)
const arrow = f => { const t = f.tail || [], a = t[0]; if (!a || !isN(a.ratio)) return ''; const k = Math.round(Math.atan2(f.mom - a.mom, f.ratio - a.ratio) / (Math.PI / 4)); return '→↗↑↖←↙↓↘'[(k + 8) % 8]; };
function rotCap() {
  const R = rotFunds(), f = R.find(x => x.sym === st.sel);
  if (!f) { const t = ((R[0] || {}).tail || [])[0]; return R.length + ' ' + st.rot + ' funds' + (t ? ' · arrows: the move since ' + md(t.d) : '') + '. Tap ' + (host.clientWidth - 38 >= 600 ? 'a dot or a name for its tail.' : 'a name for its numbers.'); }
  const t = (f.tail || [])[0];
  return f.sym + ' · ' + f.quad + ' · ratio ' + num(f.ratio, 2) + ' · momentum ' + num(f.mom, 2) + (t ? ' · ' + md(t.d) + ': ' + num(t.ratio, 2) + ' / ' + num(t.mom, 2) : '') + '. Tap it again to clear.';
}
const rotFunds = () => (mk.rotation.funds || []).filter(f => f && f.group === st.rot && isN(f.ratio) && isN(f.mom));
function rotLists() {
  const R = rotFunds(), grp = {};
  (mk.heat || []).forEach(h => { grp[h.sym] = h.group; });
  const out = (mk.rotation.left_out || []).filter(x => x && (grp[x.sym] || st.rot) === st.rot);
  return '<div class="qg">' + QO.map(q => {
    const L = R.filter(f => f.quad === q).sort((a, b) => b.ratio - a.ratio);
    return '<div class="qb"><h3 data-q="' + q + '"><i data-c="' + q + '"></i>' + q + ' <span class="mu">' + L.length + '</span></h3>' + (L.length ? '<p class="qh"><span>Fund</span><span>Ratio</span><span>Mom.</span></p>' +
      L.map(f => '<button class="qr" type="button" data-s="' + esc(f.sym) + '" aria-pressed="' + (f.sym === st.sel) + '"><b>' + esc(f.sym) + ' <i aria-hidden="true">' + arrow(f) + '</i></b><span>' + num(f.ratio, 2) +
        '</span><span>' + num(f.mom, 2) + '</span></button>').join('') : '<p class="mu qn">none</p>') + '</div>';
  }).join('') + '</div><p class="cpc rc" id="mr-c" aria-live="polite">' + esc(rotCap()) + '</p>' +
    (out.length ? '<details class="lft"><summary>Not shown: ' + out.map(x => esc(x.sym)).join(', ') + '</summary><ul>' + out.map(x => '<li><b>' + esc(x.sym) + '</b> · ' + esc(x.why) + '</li>').join('') + '</ul></details>' : '') +
    vt('Rotation, ' + st.rot + ' funds', ['Fund', 'Quadrant', 'Ratio', 'Momentum', 'Tail start'], R.slice().sort((a, b) => QO.indexOf(a.quad) - QO.indexOf(b.quad) || b.ratio - a.ratio).map(f => {
      const t = (f.tail || [])[0]; return [esc(f.sym), f.quad, num(f.ratio, 2), num(f.mom, 2), t ? md(t.d) + ': ' + num(t.ratio, 2) + ' / ' + num(t.mom, 2) : '—']; }));
}
function scatter(W) {
  const R = rotFunds(), sel = st.sel, H = Math.round(cl(W * .5, 320, 420)), X0 = 30, X1 = W - 14, Y0 = 26, Y1 = H - 26, tl = f => (f.tail || []).filter(p => isN(p.ratio) && isN(p.mom));
  const sp = a => Math.max(0, ...a.map(v => Math.abs(v - 100))), dx = sp(R.map(f => f.ratio)), dy = sp(R.map(f => f.mom)), sx = sp(R.flatMap(f => tl(f).map(p => p.ratio))), sy = sp(R.flatMap(f => tl(f).map(p => p.mom)));
  const ex = Math.max(dx * 1.18, Math.min(sx, dx * 1.6) * 1.05, .5), ey = Math.max(dy * 1.18, Math.min(sy, dy * 1.6) * 1.05, .3);
  const x = v => X0 + (X1 - X0) * (v - (100 - ex)) / (2 * ex), y = v => Y0 + (Y1 - Y0) * ((100 + ey) - v) / (2 * ey), xc = x(100), yc = y(100);
  const q = (x_, y_, w, h, c) => rc(x_, y_, w, h, ' fill="' + c + '" opacity=".08"');
  let s = rc(0, 0, W, H, ' fill="#131722"') + q(xc, Y0, X1 - xc, yc - Y0, '#2bb07f') + q(X0, Y0, xc - X0, yc - Y0, '#4a8fe0') + q(X0, yc, xc - X0, Y1 - yc, '#d4504a') + q(xc, yc, X1 - xc, Y1 - yc, '#e2bf3f') +
    ln(X0, yc, X1, yc, ' class="zl"') + ln(xc, Y0, xc, Y1, ' class="zl"') + tx(X1, Y0 - 9, 'LEADING', ' class="qL"' + END) + tx(X0, Y0 - 9, 'IMPROVING', ' class="qI"') + tx(X0, H - 8, 'LAGGING', ' class="qG"') +
    tx(X1, H - 8, 'WEAKENING', ' class="qW"' + END) + tx(X0 - 4, yc + 4, 100, END) + tx(X1 - 4, yc - 6, 'RS-Ratio →', END) + tx(xc + 6, Y0 + 12, '↑ RS-Momentum');
  const Pp = R.map(f => ({f, cx: x(f.ratio), cy: y(f.mom)})), tails = st.rot === 'sector';
  let tg_ = '';
  Pp.forEach(p => {
    const T = tl(p.f), me = p.f.sym === sel, pts = T.map(q => f1(x(q.ratio)) + ',' + f1(y(q.mom))).join(' ');
    if (T.length < 2) return;
    if (me) tg_ += '<polyline points="' + pts + '" fill="none" stroke="#fff" stroke-width="2.4"/>' + T.slice(0, -1).map(q => '<circle cx="' + f1(x(q.ratio)) + '" cy="' + f1(y(q.mom)) + '" r="2.6" fill="#fff"/>').join('');
    else if (tails) tg_ += '<polyline points="' + pts + '" fill="none" stroke="' + QC[p.f.quad] + '" stroke-width="1" opacity="' + (sel ? .12 : .32) + '"/>';
  });
  s += '<clipPath id="mrclip">' + rc(X0, Y0, X1 - X0, Y1 - Y0) + '</clipPath><g clip-path="url(#mrclip)">' + tg_ + '</g>';
  Pp.forEach(p => { const me = p.f.sym === sel; s += '<circle cx="' + f1(p.cx) + '" cy="' + f1(p.cy) + '" r="' + (me ? 6.5 : 4.5) + '" fill="' + QC[p.f.quad] + '" stroke="' + (me ? '#fff' : '#1d2131') + '" stroke-width="' + (me ? 2 : 1) + '" opacity="' + (sel && !me ? .35 : 1) + '"/>'; });
  // labels: GrokBot's candidate spots around each dot, the free one nearest; a label with no free spot is hidden (few labels)
  const box = [[xc + 5, Y0 + 3, xc + 90, Y0 + 15], [X1 - 70, yc - 15, X1, yc - 3]].concat(Pp.map(p => [p.cx - 5, p.cy - 5, p.cx + 5, p.cy + 5, p.f.sym]));
  const hit = (b, own) => box.some(o => o[4] !== own && b[0] < o[2] && b[2] > o[0] && b[1] < o[3] && b[3] > o[1]);
  const C = [[7, -3, 0], [7, 9, 0], [-7, -3, 1], [-7, 9, 1], [0, -8, 2], [0, 17, 2]];
  Pp.slice().sort((a, b) => (b.f.sym === sel) - (a.f.sym === sel) || Math.hypot(b.cx - xc, b.cy - yc) - Math.hypot(a.cx - xc, a.cy - yc)).forEach(p => {
    const me = p.f.sym === sel, w = p.f.sym.length * 6.6;
    for (const c of C) {
      const ax = p.cx + c[0], ay = p.cy + c[1], l = c[2] === 0 ? ax : c[2] === 1 ? ax - w : ax - w / 2, b = [l - 1, ay - 11, l + w + 1, ay + 4];
      if (b[0] < X0 + 1 || b[2] > X1 - 1 || b[1] < Y0 + 1 || b[3] > Y1 - 1 || hit(b, p.f.sym)) continue;
      box.push(b);
      s += (me ? rc(b[0] - 2, b[1] - 1, b[2] - b[0] + 4, b[3] - b[1] + 2, ' rx="3" fill="#fff"') : '') + tx(b[0] + 1, b[3] - 4, esc(p.f.sym), ' class="' + (me ? 'rs1' : 'rs0') + '" opacity="' + (sel && !me ? .45 : 1) + '"');
      break;
    }
  });
  G['mc-rot'] = {pts: Pp.map(p => [p.cx, p.cy, p.f.sym]), W};
  return {s: svg(W, H, 'Rotation map of ' + R.length + ' ' + st.rot + ' funds against SPY, weekly: ' + QO.map(q => q + ' ' + R.filter(f => f.quad === q).map(f => f.sym).join(' ')).join('; '), s)};
}
function rot(re) {
  const r = mk.rotation;
  if (!r || !isA(r.funds) || !r.funds.length) return '';
  if (!r.funds.some(f => f.group === st.rot)) st.rot = r.funds[0].group;
  if (!re) jobs.push({id: 'mc-rot', draw: W => W >= 600 ? scatter(W) : {s: ''}});
  return sec('m-rot', r.credit || 'Rotation', 'Rotation', 'weekly, against SPY', pvl(mk.as_of, mk.generated_at), tg('Rot', [['sector', 'Sectors'], ['theme', 'Themes']], st.rot) +
    '<div class="rmap" id="mc-rot"></div>' + rotLists());
}

// ---- positioning and range: the edition's strip block (desk/terminal/strip.py) in this tab's words; a block without data
// says No read with its reason, never a number ----------------------------------------------------------------------------
const GWHY = 'Needs open interest and an implied volatility on the same contracts; the last options read had none.';
function posRows(s) {
  if (!s || s.error) return [];
  const ok = b => b && (b.status === 'ok' || b.status === 'stale'), why = b => b && b.reason ? b.reason : 'not read';
  const sg = v => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), 2) + '%' : '—';
  const tone = {Dampening: 'up', Amplifying: 'dn', Calm: 'up', Stressed: 'dn', Volatile: 'dn'}, out = [], G = s.gex || {}, F = Object.keys(G);
  const up = (l, b, line) => out.push({label: l, word: ok(b) ? b.word : 'No read', tone: ok(b) ? tone[b.word] || '' : '', line: ok(b) ? line : why(b)});
  if (F.length && !F.some(f => ok(G[f]))) out.push({label: 'Dealer gamma · ' + F.join(', '), word: 'No read', tone: '', line: /open interest/.test(why(G[F[0]])) ? GWHY : why(G[F[0]])});
  else F.forEach(f => { const g = G[f];
    up(f + ' gamma', g, ok(g) ? (isN(g.flip_sigma) ? 'flip ' + num(Math.abs(g.flip_sigma), 1) + 'σ ' + (g.flip_sigma < 0 ? 'below' : 'above') : 'no flip within 10%') +
      ' · put wall ' + sg(g.put_wall_pct) + ' · call wall ' + sg(g.call_wall_pct) + (isN(g.net) ? ' · ' + (g.net < 0 ? '−' : '') + '$' + num(Math.abs(g.net), 2) + 'B per 1% move' : '') : ''); });
  const m = s.move;
  out.push({label: 'Expected move', word: ok(m) ? '±' + num(m.em_pct, 2) + '%' : 'No read', tone: '', line: ok(m) ? (isN(m.funded_pct) && m.em_pct ? num(m.funded_pct / m.em_pct * 100, 0) + '% funded by now' : 'one day, from the VIX') : why(m)});
  up('Day type', s.day, ok(s.day) ? 'gap ' + sg(s.day.gap_pct) + ' · range ' + (isN(s.day.range_pct) ? num(s.day.range_pct, 2) + '%' : '—') : '');
  up('Fear', s.fear && Object.assign({}, s.fear, {word: s.fear.stress || s.fear.word}), ok(s.fear) ? (s.fear.fear_day ? 'fear day ' + (s.fear.fear_day_date || '') : 'no fear day') + (isN(s.fear.vix_vs_forecast) ? ' · VIX ' + num(s.fear.vix_vs_forecast, 2) + '× the forecast' : '') : '');
  up('SPX / NQ', s.agree, ok(s.agree) ? 'SPY ' + sg(s.agree.spy_pct) + ' · QQQ ' + sg(s.agree.qqq_pct) : '');
  return out;
}
function pos() {
  const s = M.ed && M.ed.strip, r = posRows(s);
  if (!r.length) return '';
  return sec('m-pos', 'Dealers, range and fear', 'Positioning and range', 'what the option chains and the VIX say about today', s.as_of ? 'as of ' + s.as_of : '',
    '<div class="t3">' + r.map(x => tile(esc(x.label), esc(x.word), esc(x.line), x.tone)).join('') + '</div>' +
    '<p class="tsd">Gamma convention: dealers long the calls, short the puts.</p>');
}

// ---- drawing: the sections' markup, then each chart at its box's width (redrawn when the width changes) ----------------
function draw() {
  jobs.forEach(j => {
    const b = el(j.id);
    if (!b) return;
    const c = b.parentElement, W = Math.max(280, Math.round(b.clientWidth || c.clientWidth - parseFloat(getComputedStyle(c).paddingLeft) * 2)), r = j.draw(W);
    b.innerHTML = r.s;
    if (j.cap) G[j.id] = Object.assign({cap: j.cap}, r);
  });
  host.querySelectorAll('[data-pw]').forEach(e => { e.style.width = e.dataset.pw + '%'; });    // CSSOM: the CSP bars style attributes
  w0 = host.clientWidth;
}
D.addEventListener('md:edition', () => { const n = el('m-pos'); if (done && n) { const h = pos(); n.innerHTML = h; n.hidden = !h; } });
const refit = () => { if (mk && host.clientWidth && host.clientWidth !== w0) draw(); };   // drawn hidden or at another width
const SECS = ['m-pos', 'm-idx', 'm-mood', 'm-pulse', 'm-breadth', 'm-risk', 'm-heat', 'm-rot'];
function render() {
  jobs = [];
  const at = location.hash.slice(1), first = !done;
  [pos(), idx(), mood(mk.mood), pulse(mk.pulse), breadth(mk.breadth, mk.participation, mk.movers), risk(mk.risk), heat(), rot()].forEach((h, i) => {
    const n = el(SECS[i]);
    n.innerHTML = h;
    n.hidden = !h;
  });
  done = 1;
  draw();
  V.jump();
  if (first && SECS.includes(at) && !el(at).hidden) el(at).scrollIntoView();
}
// market.css arrives with this file (viz.js loads both on the tab's first open): draw once its rules apply, so nothing moves;
// and once the first edition is drawn (a deep link can get here first, while the page is still hidden and has no width)
const css = () => new Promise(r => { let k = 0; const t = () => getComputedStyle(host).getPropertyValue('--mx') || ++k > 60 ? r() : setTimeout(t, 50); t(); });
const ed = () => M.ed ? 0 : new Promise(r => { D.addEventListener('md:edition', r, {once: true}); setTimeout(r, 4e3); });
function load() {
  if (busy) return;
  busy = 1;
  const was = mk && mk.generated_at;
  Promise.all([fetch('market.json', {cache: 'no-cache'}).then(r => r.ok ? r.json() : null).catch(() => null), Promise.resolve(charts()).catch(() => null), css(), ed()]).then(([m, c]) => {
    busy = 0;
    if (c && typeof c.syms === 'object') ch = c;
    if (m && m.v === 1 && isA(m.heat)) { if (!mk || !mk.v || m.generated_at !== was) { mk = m; render(); } }
    else if (!mk && ch) { mk = {heat: [], as_of: ch.as_of}; render(); }
  });
}

// ---- taps: the toggles, a tile or a fund, and a day on any chart (a crosshair and a caption under it) ------------------
// a re-drawn part keeps the keyboard's place: the pressed control is focused again
function swap(n, h, b) {
  const k = b && [...b.attributes].find(a => a.name.startsWith('data-'));
  n.innerHTML = h;
  const f = k && host.querySelector('[' + k.name + '="' + k.value + '"]');
  if (f && b === D.activeElement) f.focus({preventScroll: true});
}
host.addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b || !mk) return;
  const ds = b.dataset;
  if (ds.group || ds.period || ds.all || ds.h) {
    if (ds.group) { st.grp = ds.group; st.all = 0; st.hs = null; }
    if (ds.period) st.per = ds.period;
    if (ds.all) st.all = !st.all;
    if (ds.h) st.hs = st.hs === ds.h ? null : ds.h;
    swap(el('m-heat'), heat(), b);
  } else if (ds.rot || ds.s) {
    if (ds.rot) { st.rot = ds.rot; st.sel = null; } else st.sel = st.sel === ds.s ? null : ds.s;
    rotDraw(b);
  }
});
function rotDraw(b) {
  swap(el('m-rot'), rot(1), b);
  const r = el('mc-rot');
  const c = r && r.parentElement, W = c ? Math.round(c.clientWidth - parseFloat(getComputedStyle(c).paddingLeft) * 2) : 0;
  if (W >= 600) r.innerHTML = scatter(W).s;
}
function at(e) {
  const b = e.target.closest('.cbx,.spw,.rmap'), g = b && G[b.id], s = b && b.querySelector('svg');
  if (!g || !s) return;
  const r = s.getBoundingClientRect(), u = (e.clientX - r.left) * (s.viewBox.baseVal.width / r.width), v = (e.clientY - r.top) * (s.viewBox.baseVal.height / r.height);
  if (g.pts) {                                     // the rotation map: the nearest dot within 16 px selects its fund
    let k = null, bd = 16;
    g.pts.forEach(q => { const d = Math.hypot(q[0] - u, q[1] - v); if (d < bd) { bd = d; k = q[2]; } });
    if (e.type === 'pointerdown') { st.sel = k && st.sel !== k ? k : null; rotDraw(); }
    return;
  }
  let i = 0, bd = 1e9;
  for (let j = 0; j < g.n; j++) { const d = Math.abs(g.X(j) - u); if (d < bd) { bd = d; i = j; } }
  const h = s.querySelector('.xh'), c = el(b.dataset.cap || b.id + '-c');
  if (h) { h.setAttribute('x1', f1(g.X(i))); h.setAttribute('x2', f1(g.X(i))); h.classList.add('on'); }
  if (c) c.textContent = g.cap(i);
}
host.addEventListener('pointerdown', at);
host.addEventListener('pointermove', e => { if (e.pointerType === 'mouse') at(e); });
let rz = 0;
addEventListener('resize', () => { if (!rz) rz = requestAnimationFrame(() => { rz = 0; refit(); }); });
D.addEventListener('md:tab', e => { if (e.detail === 'market') { if (!mk) load(); else refit(); } });
D.addEventListener('md:edition', () => { if (mk) { refit(); load(); } });     // a new edition: market.json again (an unchanged file is not redrawn)
if (V.tab() === 'market') load();
})();
