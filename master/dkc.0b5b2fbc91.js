/* The Desk tab's charts (owner, 2026-11-02: "EVERY SINGLE ENGINE AND TOOL NEEDS A GRAPH ... I need to be able to LOOK
   AT IT AND UNDERSTAND VISUALLY WHAT IS GOING ON"). Each chart draws trading data only: equity, drawdown, P&L, exposure,
   trade outcomes, risk against its caps; never the engine's own workings. desk.js and My Book leave an empty box
   (<div data-vz="kind">) and call VZD.paint(root, data), which draws every box to its own width as an inline SVG. */
(() => {
'use strict';
const isN = v => typeof v === 'number' && isFinite(v);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[c]);
const f1 = v => (Math.round(v * 10) / 10).toString();
const pc = v => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 10 ? 1 : 2) + '%' : '—';
const usd = v => {
  if (!isN(v)) return '—';
  const a = Math.abs(v), s = v < 0 ? '−' : v > 0 ? '+' : '';
  return s + '$' + (a >= 1e9 ? (a / 1e9).toFixed(2) + 'B' : a >= 1e6 ? (a / 1e6).toFixed(2) + 'M' : a >= 1e4 ? (a / 1e3).toFixed(1) + 'K' : a >= 1e3 ? (a / 1e3).toFixed(2) + 'K' : a.toFixed(0));
};
const fit = (s, px) => { s = String(s || ''); const n = Math.max(4, Math.floor(px / 6.6)); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
const amt = v => usd(v).replace(/^\+/, '');
const tn = v => isN(v) ? (v > 0 ? 'p' : v < 0 ? 'n' : 'z') : 'z';
const PAL = 8;                  // categorical slots in desk.css (.vz-c0 … .vz-c7), the rest muted
const svg = (W, H, body, label) => '<svg class="vz" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="' + esc(label) + '">' + body + '</svg>';
const txt = (x, y, s, c, a) => '<text class="' + (c || 'vz-t') + '" x="' + f1(x) + '" y="' + f1(y) + '"' + (a ? ' text-anchor="' + a + '"' : '') + '>' + esc(s) + '</text>';
const empty = t => '<p class="vz-e">' + esc(t) + '</p>';
const ticks = (lo, hi, n) => {
  const span = hi - lo || 1, raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw))), st = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) || raw;
  const out = [];
  for (let v = Math.ceil(lo / st) * st; v <= hi + 1e-9; v += st) out.push(Math.round(v / st) * st);
  return out;
};

// ---- primitives ------------------------------------------------------------------------------------------------------
// horizontal bars, centred on zero when values have both signs: rows [{l, v, s (sub label), c (class)}]
function hbars(W, rows, o = {}) {
  if (!rows.length) return empty(o.none || 'Nothing to show yet');
  const lw = Math.min(o.lw || 150, Math.round(W * 0.38)), vw = 64, bh = o.bh || 20, gap = 6, H = rows.length * (bh + gap) + 4;
  const bars = rows.filter(r => !r.sep), mx = Math.max(...bars.map(r => Math.abs(r.v)), 1e-9), neg = bars.some(r => r.v < 0), pos = bars.some(r => r.v > 0);
  const x0 = lw + 8, x1 = W - vw - 6, zero = neg && pos ? (x0 + x1) / 2 : neg ? x1 : x0, half = neg && pos ? (x1 - x0) / 2 : x1 - x0;
  let b = '<line class="vz-z" x1="' + f1(zero) + '" x2="' + f1(zero) + '" y1="0" y2="' + H + '"/>';
  rows.forEach((r, i) => {
    const y = i * (bh + gap) + 2, w = Math.max(1.5, Math.abs(r.v) / mx * half), x = r.v < 0 ? zero - w : zero;
    if (r.sep) { b += txt(2, y + bh * 0.68, r.sep, 'vz-a'); return; }   // a divider row: words, no bar
    b += txt(lw, y + bh * 0.68, fit(r.l, lw - 4), 'vz-l', 'end') + '<rect class="vz-b ' + (r.c || tn(r.v)) + '" x="' + f1(x) + '" y="' + y + '" width="' + f1(w) + '" height="' + bh + '" rx="3"><title>' + esc(r.l + ': ' + (r.s || (o.fmt || usd)(r.v))) + '</title></rect>' +
      txt(W - 2, y + bh * 0.68, (o.fmt || usd)(r.v), 'vz-v ' + tn(r.v), 'end');
  });
  return svg(W, H, b, o.label || '');
}
// lines over shared dates: series [{name, v: [..], c}], a zero line, the last value labelled
function lines(W, H, dates, series, o = {}) {
  const all = series.flatMap(s => s.v).filter(isN);
  if (dates.length < 2 || !all.length) return empty(o.none || 'The curve starts with the second session');
  const pl = 50, pr = 10, pt = 10, pb = 22, lo = Math.min(0, ...all), hi = Math.max(0, ...all), r = hi - lo || 1;
  const X = i => pl + i / (dates.length - 1) * (W - pl - pr), Y = v => pt + (hi - v) / r * (H - pt - pb);
  let b = ticks(lo, hi, 4).map(t => '<line class="vz-g" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f1(Y(t)) + '" y2="' + f1(Y(t)) + '"/>' + txt(pl - 6, Y(t) + 4, pc(t), 'vz-a', 'end')).join('');
  b += '<line class="vz-z" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"/>';
  b += txt(pl, H - 6, md(dates[0]), 'vz-a') + txt(W - pr, H - 6, md(dates[dates.length - 1]), 'vz-a', 'end');
  const ends = [];
  series.slice().reverse().forEach(s => {
    const pts = s.v.map((v, i) => isN(v) ? f1(X(i)) + ',' + f1(Y(v)) : null).filter(Boolean);
    if (pts.length < 2) return;
    b += '<polyline class="vz-ln ' + s.c + '" points="' + pts.join(' ') + '"><title>' + esc(s.name + ' ' + pc(lastN(s.v))) + '</title></polyline>';
    ends.push({t: s.name, v: lastN(s.v), c: s.c});
  });
  ends.sort((a, c) => (c.v ?? -1e9) - (a.v ?? -1e9));
  return svg(W, H, b, o.label || '') + '<p class="vz-lg">' + ends.map(e => '<span><i class="' + e.c + '"></i>' + esc(e.t) + ' <b class="' + tn(e.v) + '">' + pc(e.v) + '</b></span>').join('') + '</p>';
}
// an area below zero (the underwater curve)
function under(W, H, dates, v, o = {}) {
  const ok = v.filter(isN);
  if (dates.length < 2 || !ok.length) return empty('The drawdown starts with the second session');
  const pl = 44, pr = 12, pt = 8, pb = 22, lo = Math.min(-0.5, ...ok), X = i => pl + i / (dates.length - 1) * (W - pl - pr), Y = x => pt + (0 - x) / (0 - lo) * (H - pt - pb);
  const pts = v.map((x, i) => isN(x) ? [X(i), Y(x)] : null).filter(Boolean);
  let b = ticks(lo, 0, 3).map(t => '<line class="vz-g" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f1(Y(t)) + '" y2="' + f1(Y(t)) + '"/>' + txt(pl - 6, Y(t) + 4, pc(t), 'vz-a', 'end')).join('');
  b += '<path class="vz-uw" d="M' + f1(pts[0][0]) + ',' + f1(Y(0)) + ' L' + pts.map(p => f1(p[0]) + ',' + f1(p[1])).join(' L') + ' L' + f1(pts[pts.length - 1][0]) + ',' + f1(Y(0)) + 'Z"/>';
  b += '<polyline class="vz-uwl" points="' + pts.map(p => f1(p[0]) + ',' + f1(p[1])).join(' ') + '"/>';
  const m = Math.min(...ok), mi = v.indexOf(m);
  if (m < 0) { const rt = X(mi) > W - 110, ly = Y(m) - 8 > pt + 10 ? Y(m) - 8 : Y(m) + 16;
    b += '<circle class="vz-dot n" cx="' + f1(X(mi)) + '" cy="' + f1(Y(m)) + '" r="3.5"/>' + txt(rt ? X(mi) - 8 : X(mi) + 8, ly, 'Worst ' + pc(m), 'vz-v n', rt ? 'end' : 'start'); }
  b += txt(pl, H - 6, md(dates[0]), 'vz-a') + txt(W - pr, H - 6, md(dates[dates.length - 1]), 'vz-a', 'end');
  return svg(W, H, b, o.label || '');
}
// stacked long / short bars per row: rows [{l, long, short}]
function lsbars(W, rows, o = {}) {
  if (!rows.length) return empty('No open exposure');
  const lw = Math.min(o.lw || 130, Math.round(W * 0.30)), vw = Math.min(150, Math.round(W * 0.36)), bh = 18, gap = 7, H = rows.length * (bh + gap) + 4;
  const mx = Math.max(...rows.map(r => r.long + r.short), 1e-9), x0 = lw + 8, ww = W - x0 - vw - 6;
  let b = '';
  rows.forEach((r, i) => {
    const y = i * (bh + gap) + 2, a = r.long / mx * ww, s = r.short / mx * ww;
    b += txt(lw, y + bh * 0.7, fit(r.l, lw - 4), 'vz-l', 'end') + '<rect class="vz-b lg" x="' + f1(x0) + '" y="' + y + '" width="' + f1(Math.max(a, 0.8)) + '" height="' + bh + '" rx="3"><title>' + esc(r.l + ' long ' + amt(r.long)) + '</title></rect>' +
      (s > 0.4 ? '<rect class="vz-b sh" x="' + f1(x0 + a) + '" y="' + y + '" width="' + f1(s) + '" height="' + bh + '" rx="3"><title>' + esc(r.l + ' short ' + amt(r.short)) + '</title></rect>' : '') +
      txt(W - 2, y + bh * 0.7, amt(r.long) + (r.short > 0 ? ' / ' + amt(r.short) : ''), 'vz-v', 'end');
  });
  return svg(W, H, b, o.label || '');
}
function md(d) { const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(d || ''); return m ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m[2] - 1] + ' ' + (+m[3]) : String(d || ''); }
function lastN(a) { for (let i = a.length - 1; i >= 0; i--) if (isN(a[i])) return a[i]; return null; }

// ---- the charts ------------------------------------------------------------------------------------------------------
const K = {};
K.dd = (W, d) => {
  const c = d.curve || {}, x = (d.charts || {}).dd || [];
  return under(W, 150, c.dates || [], x, {label: 'Desk drawdown from its peak, daily'});
};
K.fam = (W, d) => {
  const f = (d.charts || {}).families || {}, A = f.series || [], c = d.curve || {};
  const byEnd = A.filter(s => isN(lastN(s.pct))).sort((a, b) => lastN(b.pct) - lastN(a.pct)), pick = A.slice(0, PAL - 2);
  [byEnd[0], byEnd[byEnd.length - 1]].forEach(s => { if (s && !pick.includes(s)) pick.push(s); });
  const S = pick.slice(0, PAL);
  const ser = S.map((s, i) => ({name: s.name, v: s.pct, c: 'vz-c' + i})).concat([{name: 'Desk', v: c.desk || [], c: 'vz-dk'}]);
  return lines(W, Math.max(200, Math.min(300, Math.round(W * 0.45))), f.dates || [], ser, {label: 'Return by family since the desk began, % of each family’s capital'});
};
K.pnl = (W, d) => {
  const p = (d.charts || {}).pnl || {}, A = (p.top || []).concat((p.bottom || []).slice().reverse());
  return hbars(W, A.map(r => ({l: r.name, v: r.pnl, s: usd(r.pnl) + ' · ' + pc(r.ret)})), {label: 'Dollar P&L of the best and worst sleeves', lw: 190, none: 'No sleeve has P&L yet'});
};
K.expo = (W, d) => {
  const e = (d.charts || {}).exposure || {}, mk = a => a.map(r => ({l: r.name, long: r.long || 0, short: r.short || 0}));
  return '<div class="vz-2"><div><p class="vz-h">By asset class</p>' + lsbars(W2(W), mk(e.cls || []), {label: 'Long and short exposure by asset class'}) +
    '</div><div><p class="vz-h">By family</p>' + lsbars(W2(W), mk((e.family || []).slice(0, 12)), {label: 'Long and short exposure by family'}) + '</div></div>' +
    '<p class="vz-k"><span><i class="lg"></i>Long</span><span><i class="sh"></i>Short</span></p>';
};
const W2 = W => W >= 760 ? Math.floor((W - 24) / 2) : W;
K.unreal = (W, d) => {
  const U = (d.charts || {}).unreal || [];
  return hbars(W, U.map(r => ({l: r.sym, v: r.pnl, s: usd(r.pnl) + ' · ' + pc(r.pct)})), {label: 'Largest unrealized gains and losses on open positions', lw: 110, bh: 18, none: 'No open positions'});
};
K.flow = (W, d) => {
  // a funnel on a log scale, so a handful of fills still shows beside hundreds of signals; each step names its count
  // and what share of the step before it went through
  // a fill is one book's share of an order's fill (an order netted across sleeves fills into each of their books, and a
  // partial fill counts again), so fills can pass orders: that step reads per order, never as a share (audit D5-10)
  const t = (d.engine || {}).today || {}, R = [['Signals', t.signals], ['Orders', t.orders], ['Book fills', t.fills]].filter(r => isN(r[1]));
  if (!R.length) return empty('No signals yet today');
  const lw = 74, vw = Math.min(190, Math.round(W * 0.42)), bh = 26, gap = 10, H = R.length * (bh + gap), mx = Math.max(...R.map(r => r[1]), 1), x0 = lw + 8, ww = W - x0 - vw - 8;
  const L = v => v > 0 ? Math.max(0.06, Math.log10(v + 1) / Math.log10(mx + 1)) : 0;
  let b = '';
  R.forEach((r, i) => {
    const y = i * (bh + gap), w = L(r[1]) * ww, cx = x0 + (ww - w) / 2, prev = i ? R[i - 1][1] : null;
    const conv = r[0] === 'Book fills' && R[i - 1] && R[i - 1][0] === 'Orders' ? (prev > 0 ? (r[1] / prev).toFixed(2) + ' per order' : '') : prev ? (prev > 0 ? (r[1] / prev * 100).toFixed(r[1] / prev < 0.1 ? 1 : 0) + '% of ' + R[i - 1][0].toLowerCase() : '') : '';
    b += txt(lw, y + bh * 0.66, r[0], 'vz-l', 'end') + '<rect class="vz-b fl" x="' + f1(cx) + '" y="' + y + '" width="' + f1(Math.max(w, 2)) + '" height="' + bh + '" rx="4"/>' +
      txt(W - 2, y + bh * 0.66, r[1].toLocaleString('en-US') + (conv ? ' · ' + conv : ''), 'vz-v', 'end');
  });
  return svg(W, H, b, 'Today: signals, orders sent and fills, as a funnel on a log scale');
};
K.hist = (W, d) => {
  const h = (d.charts || {}).hist || {}, E = h.edges || [], Wn = h.win || [], L = h.loss || [];
  const n = Math.max(Wn.length, L.length);
  if (!n || !Wn.concat(L).some(v => v > 0)) return empty('No closed trades yet');
  const H = 190, pl = 34, pb = 34, pt = 8, mx = Math.max(...Wn.map((w, i) => w + (L[i] || 0)), 1), bw = (W - pl - 6) / n;
  const mn = v => String(v).replace(/^-/, '−');   // T-229: the page's − sign on the bucket edges ('-10…-5' read with hyphens)
  const lab = i => i === 0 ? '<' + mn(E[0]) : i === n - 1 ? '>' + mn(E[E.length - 1]) : mn(E[i - 1]) + '…' + mn(E[i]);
  let b = ticks(0, mx, 3).map(t => '<line class="vz-g" x1="' + pl + '" x2="' + W + '" y1="' + f1(pt + (1 - t / mx) * (H - pt - pb)) + '" y2="' + f1(pt + (1 - t / mx) * (H - pt - pb)) + '"/>' + txt(pl - 4, pt + (1 - t / mx) * (H - pt - pb) + 4, String(t), 'vz-a', 'end')).join('');
  for (let i = 0; i < n; i++) {
    const l = L[i] || 0, w = Wn[i] || 0, x = pl + i * bw + 1.5, hl = l / mx * (H - pt - pb), hw = w / mx * (H - pt - pb), y0 = H - pb;
    b += '<rect class="vz-b n" x="' + f1(x) + '" y="' + f1(y0 - hl) + '" width="' + f1(bw - 3) + '" height="' + f1(hl) + '"><title>' + esc(lab(i) + '%: ' + l + ' losers') + '</title></rect>' +
      '<rect class="vz-b p" x="' + f1(x) + '" y="' + f1(y0 - hl - hw) + '" width="' + f1(bw - 3) + '" height="' + f1(hw) + '"><title>' + esc(lab(i) + '%: ' + w + ' winners') + '</title></rect>';
    if (W >= 520 || i % 2 === 0) b += txt(x + (bw - 3) / 2, H - pb + 14, lab(i), 'vz-a', 'middle');
  }
  b += txt(pl, H - 4, 'Return per trade, %', 'vz-a');
  return svg(W, H, b, 'Closed trades by return, winners and losers');
};
K.famwin = (W, d) => {
  // every family (the headline names the lowest, audit D5-07); those under 30 trades sit below a divider, unranked, as
  // the headline says (MASTER-LIST T-180)
  const F = ((d.charts || {}).fam_win || []).filter(r => r.n > 0), big = F.filter(r => r.n >= 30), small = F.filter(r => r.n < 30);
  const bar = r => ({l: W < 520 && r.n >= 30 ? r.name : r.name + ' · ' + r.n.toLocaleString('en-US'), v: r.win - 50, s: r.win.toFixed(1) + '% won · avg ' + pc(r.avg) + ' · ' + r.n + ' trades'});
  return hbars(W, big.map(bar).concat(small.length ? [{sep: 'Under 30 trades: too few to rank'}] : [], small.map(bar)),
    {fmt: v => (v + 50).toFixed(0) + '%', label: 'Win rate by family, centred on 50%', lw: 170, none: 'No closed trades yet'});
};
K.sc = (W, d) => {
  const R = ((d.scorecards || {}).rows || []).filter(r => isN(r.win) && isN(r.avg_ret));
  if (!R.length) return empty('No sleeve has a closed trade yet');
  // T-252: the tick row sits 16 px above the axis title ("100%" touched "Win rate" 11 px below it), on a floor 4 px higher
  const H = Math.max(240, Math.min(340, Math.round(W * 0.5))), pl = 46, pb = 34, pt = 10, pr = 10;
  const q = (a, f) => { const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.max(0, Math.round(f * (s.length - 1))))]; };
  const ys = R.map(r => r.avg_ret), lo = Math.min(-1, Math.max(q(ys, 0.05) * 1.3, -15)), hi = Math.max(1, Math.min(q(ys, 0.95) * 1.3, 15)), X = w => pl + w / 100 * (W - pl - pr), Y = v => pt + (hi - v) / (hi - lo) * (H - pt - pb);
  const mxT = Math.max(...R.map(r => r.trades), 1), rad = t => 2.5 + 7 * Math.sqrt(t / mxT), VC = {propose: 'ok', review: 'bad', below_bar: 'wn'};
  let b = ticks(lo, hi, 4).map(t => '<line class="vz-g" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f1(Y(t)) + '" y2="' + f1(Y(t)) + '"/>' + txt(pl - 6, Y(t) + 4, pc(t), 'vz-a', 'end')).join('');
  b += [0, 25, 50, 75, 100].map(w => txt(X(w), H - 17, w + '%', 'vz-a', 'middle')).join('') + txt(W - pr, H - 1, 'Win rate', 'vz-a', 'end');
  b += '<line class="vz-z" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"/><line class="vz-z" x1="' + f1(X(50)) + '" x2="' + f1(X(50)) + '" y1="' + pt + '" y2="' + (H - pb) + '"/>';
  R.slice().sort((a, c) => c.trades - a.trades).forEach(r => {
    const out = r.avg_ret < lo ? -1 : r.avg_ret > hi ? 1 : 0, cy = Y(Math.max(lo, Math.min(hi, r.avg_ret))), cx = X(r.win), cl = 'vz-sc ' + (VC[r.verdict] || tn(r.avg_ret));
    const tt = '<title>' + esc(r.name + ': ' + r.win.toFixed(1) + '% won, avg ' + pc(r.avg_ret) + ', ' + r.trades + ' trades') + '</title>';
    b += out ? '<path class="' + cl + '" d="M' + f1(cx - 5) + ',' + f1(cy + out * 5) + ' L' + f1(cx + 5) + ',' + f1(cy + out * 5) + ' L' + f1(cx) + ',' + f1(cy - out * 3) + 'Z">' + tt + '</path>'
      : '<circle class="' + cl + '" cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="' + f1(rad(r.trades)) + '">' + tt + '</circle>';
  });
  return svg(W, H, b, 'Every sleeve with a closed trade: win rate against average return per trade; dot size = trades') +
    '<p class="vz-k"><span><i class="ok"></i>Proposed</span><span><i class="wn"></i>Below bar</span><span><i class="bad"></i>Review</span><span><i class="p"></i>Accumulating</span><span>▲▼ off the scale</span></p>';
};
// My Book: open risk and exposure against the charter's caps, and every closed trade in R
K.risk = (W, d) => {
  const s = d.score || {}, c = d.caps || {};
  const G = [['Open risk (heat)', s.heat_pct, c.heat_pct], ['Gross exposure', s.gross_pct, c.gross_pct], ['Drawdown', isN(s.drawdown_pct) ? Math.abs(s.drawdown_pct) : null, null]];
  const lw = Math.min(140, Math.round(W * 0.36)), bh = 18, gap = 14, H = G.length * (bh + gap) + 6, x0 = lw + 8, x1 = W - 90;
  let b = '';
  G.forEach((g, i) => {
    const y = i * (bh + gap) + 4, cap = isN(g[2]) ? g[2] : Math.max(10, (g[1] || 0) * 1.5), v = isN(g[1]) ? g[1] : 0, w = Math.min(1, v / cap) * (x1 - x0), hot = isN(g[2]) && v >= 0.8 * g[2];
    b += txt(lw, y + bh * 0.7, g[0], 'vz-l', 'end') + '<rect class="vz-tr" x="' + x0 + '" y="' + y + '" width="' + f1(x1 - x0) + '" height="' + bh + '" rx="4"/>' +
      '<rect class="vz-b ' + (hot ? 'n' : i === 2 && v > 0 ? 'n' : 'fl') + '" x="' + x0 + '" y="' + y + '" width="' + f1(Math.max(w, 1)) + '" height="' + bh + '" rx="4"/>' +
      (isN(g[2]) ? '<line class="vz-cap" x1="' + f1(x1) + '" x2="' + f1(x1) + '" y1="' + (y - 3) + '" y2="' + (y + bh + 3) + '"/>' : '') +
      txt(W - 2, y + bh * 0.7, v.toFixed(2).replace(/\.?0+$/, '') + '%' + (isN(g[2]) ? ' of ' + g[2] + '%' : ''), 'vz-v', 'end');
  });
  return svg(W, H, b, 'Open risk and gross exposure against the book’s caps, and drawdown');
};
const sR = v => { const a = Math.abs(v).toFixed(2); return (+a === 0 ? '' : v > 0 ? '+' : '−') + a + 'R'; };   // T-222: the page's − sign
K.rled = (W, d) => {
  const R = (d.r_ledger || []).filter(r => isN(r.r));
  if (!R.length) return empty('No closed trades yet: each will show here in R');
  // T-223: the running total's label gets its own right gutter; at 390 a lone bar ran under it, red on red
  const H = 170, pl = 34, pb = 20, pt = 10, tot = 'Total ' + sR(R.reduce((a, r) => a + r.r, 0)), pr = Math.ceil(tot.length * 7.5) + 6, mx = Math.max(1, ...R.map(r => Math.abs(r.r)), ...R.map(r => Math.abs(r.r_avail || 0)));
  let cum = 0;
  const cumv = R.map(r => (cum += r.r)), cm = Math.max(mx, ...cumv.map(Math.abs)), Y = v => pt + (cm - v) / (2 * cm) * (H - pt - pb), bw = (W - pl - 4 - pr) / R.length;
  let b = '<line class="vz-z" x1="' + pl + '" x2="' + W + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"/>' + [cm, -cm].map(t => txt(pl - 4, Y(t) + 4, (t > 0 ? '+' : '−') + Math.abs(t).toFixed(1) + 'R', 'vz-a', 'end')).join('');
  R.forEach((r, i) => {
    const x = pl + i * bw + 1, y = Math.min(Y(0), Y(r.r)), h = Math.abs(Y(r.r) - Y(0));
    b += '<rect class="vz-b ' + tn(r.r) + '" x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(Math.max(1, bw - 2)) + '" height="' + f1(Math.max(1, h)) + '"><title>' + esc((r.name || '') + ' ' + sR(r.r) + (isN(r.r_avail) ? ' of ' + sR(r.r_avail) + ' available' : '')) + '</title></rect>';   // p21: the page's − sign on ticks and titles; T-225: the closing tags sat inside that comment, so the total line and label fell into the <title>
  });
  b += '<polyline class="vz-ln vz-dk" points="' + cumv.map((v, i) => f1(pl + i * bw + bw / 2) + ',' + f1(Y(v))).join(' ') + '"/>' + txt(W - 2, Y(cumv[cumv.length - 1]) + 4, tot, 'vz-v ' + tn(cum), 'end');
  return svg(W, H, b, 'Each closed trade in R, with the running total');
};

// ---- the one-line reading above each chart, computed from the same data ----------------------------------------------
const HL = {};
HL.dd = d => {
  const x = ((d.charts || {}).dd || []).filter(isN), now = lastN(x), worst = x.length ? Math.min(...x) : null;
  if (!x.length) return '';
  return now >= -0.05 ? 'At a new high: no drawdown' : 'Now ' + pc(now) + ' below its peak · worst so far ' + pc(worst);
};
HL.fam = d => {
  const S = ((d.charts || {}).families || {}).series || [], L = S.map(s => [s.name, lastN(s.pct)]).filter(r => isN(r[1])).sort((a, b) => b[1] - a[1]);
  if (!L.length) return '';
  const up = L.filter(r => r[1] > 0).length;
  return 'Best ' + L[0][0] + ' ' + pc(L[0][1]) + ' · worst ' + L[L.length - 1][0] + ' ' + pc(L[L.length - 1][1]) + ' · ' + up + ' of ' + L.length + ' families up';
};
HL.pnl = d => {
  const p = (d.charts || {}).pnl || {}, a = (p.top || [])[0], b = (p.bottom || [])[0];
  return [a ? 'Top earner ' + a.name + ' ' + usd(a.pnl) : '', b ? 'biggest loser ' + b.name + ' ' + usd(b.pnl) : ''].filter(Boolean).join(' · ');
};
HL.expo = d => {
  const e = ((d.charts || {}).exposure || {}).cls || [], o = d.overview || {}, tot = e.reduce((s, r) => s + (r.long || 0) + (r.short || 0), 0);
  if (!e.length || !tot) return '';
  const t = e[0];
  return 'Net ' + (isN(o.invested) && o.invested >= 0 ? 'long ' : 'short ') + amt(Math.abs(o.invested || 0)) + ' · ' + t.name + ' is ' + Math.round(((t.long || 0) + (t.short || 0)) / tot * 100) + '% of gross';
};
HL.unreal = d => {
  const U = (d.charts || {}).unreal || [], o = d.overview || {};
  if (!U.length) return '';
  const g = U.filter(r => r.pnl > 0).sort((a, b) => b.pnl - a.pnl)[0], l = U.filter(r => r.pnl < 0).sort((a, b) => a.pnl - b.pnl)[0];
  return 'Open P&L ' + usd(o.unrealized) + [g ? ' · best ' + g.sym + ' ' + usd(g.pnl) : '', l ? ' · worst ' + l.sym + ' ' + usd(l.pnl) : ''].join('');
};
HL.flow = d => {
  const t = (d.engine || {}).today || {};
  if (!isN(t.signals)) return '';
  return (t.signals || 0).toLocaleString('en-US') + ' signals today became ' + (t.orders || 0).toLocaleString('en-US') + ' order' + (t.orders === 1 ? '' : 's') + ' and ' + (t.fills || 0).toLocaleString('en-US') + ' book fill' + (t.fills === 1 ? '' : 's');
};
HL.hist = d => {
  const c = d.closed || {}, h = (d.charts || {}).hist || {}, w = (h.win || []).reduce((a, b) => a + b, 0), l = (h.loss || []).reduce((a, b) => a + b, 0);
  if (!(w + l)) return '';
  return Math.round(w / (w + l) * 100) + '% of closed trades won · realized ' + usd(c.realized);
};
HL.famwin = d => {
  const A = (d.charts || {}).fam_win || [], F = A.filter(r => r.n >= 30).sort((a, b) => b.win - a.win), k = A.filter(r => r.n > 0 && r.n < 30).length;
  return F.length ? 'Highest win rate ' + F[0].name + ' ' + F[0].win.toFixed(0) + '% · lowest ' + F[F.length - 1].name + ' ' + F[F.length - 1].win.toFixed(0) + '% (30+ trades)' + (k ? ' · ' + k + ' famil' + (k === 1 ? 'y' : 'ies') + ' under 30 trades not ranked' : '') : '';
};
HL.sc = d => {
  const R = ((d.scorecards || {}).rows || []).filter(r => isN(r.avg_ret) && !r.small), pos = R.filter(r => r.avg_ret > 0).length;
  return R.length ? pos + ' of ' + R.length + ' full-sample sleeves make money per trade on average' : '';
};
HL.risk = d => {
  const s = d.score || {}, c = d.caps || {};
  return 'Open risk ' + (isN(s.heat_pct) ? s.heat_pct : 0) + '% of a ' + (c.heat_pct || 3) + '% cap · gross ' + (isN(s.gross_pct) ? s.gross_pct : 0) + '% of ' + (c.gross_pct || 100) + '%';
};
HL.rled = d => {
  const R = (d.r_ledger || []).filter(r => isN(r.r)), t = R.reduce((a, r) => a + r.r, 0);
  return R.length ? R.length + ' closed trade' + (R.length === 1 ? '' : 's') + ' · ' + sR(t) + ' in total' : 'Flat: the first closed trade starts the ledger';   // T-222
};

// sections whose own visual is already on the page get the verdict line alone
K.vlead = K.vsl = K.vheat = () => '';
HL.vlead = d => {
  const s = d.sleeves || {}, A = s.leaders || [], B = s.laggards || [];
  return A.length && B.length ? A[0].name + ' leads at ' + pc(A[0].ret) + '; ' + B[0].name + ' trails at ' + pc(B[0].ret) : '';
};
HL.vsl = d => {
  const F = (d.sleeves || {}).families || [], up = F.reduce((a, f) => a + (f.up || 0), 0), dn = F.reduce((a, f) => a + (f.down || 0), 0), c = (d.sleeves || {}).counts || {};
  return up + dn ? up + ' sleeves up, ' + dn + ' down · ' + (c.firing || 0).toLocaleString('en-US') + ' holding positions' : '';
};
HL.vheat = d => {
  const H = ((d.positions || {}).heat || []).filter(h => h.gross > 0), tot = H.reduce((a, h) => a + h.gross, 0), top = H.slice(0, 3);
  return tot ? top.map(h => h.sym).join(', ') + ' are ' + Math.round(top.reduce((a, h) => a + h.gross, 0) / tot * 100) + '% of the largest ' + H.length + ' holdings' + (H[0] && isN(H[0].pct) ? ' · ' + H[0].sym + ' ' + pc(H[0].pct) : '') : '';
};

// ---- painting --------------------------------------------------------------------------------------------------------
// draw every empty or stale box under root to its width; data(kind) returns the document the kind reads
function paint(root, data) {
  if (!root) return;
  root.querySelectorAll('[data-vz]').forEach(box => {
    const k = box.dataset.vz, f = K[k], W = Math.round(box.clientWidth);
    if (!f || !W || (box.dataset.vzw === String(W) && box.firstChild)) return;
    const d = typeof data === 'function' ? data(k) : data;
    if (!d) return;
    try { const h = HL[k] ? HL[k](d) : ''; box.innerHTML = (h ? '<p class="vz-hl">' + esc(h) + '</p>' : '') + f(Math.max(260, W), d); box.dataset.vzw = String(W); } catch (e) { box.innerHTML = empty('This chart could not be drawn'); console.warn(e); }
  });
}
// the charts' own styles, scoped to the Desk tab (desk.css keeps its budget)
{ const st = document.createElement('style'); st.textContent = '#p-desk .t td .dk-db{display:inline-block;position:relative;width:64px;height:8px;margin-left:8px;vertical-align:middle;border-radius:99px;background:var(--tr)}#p-desk .vz-box{width:100%;min-height:40px;margin:4px 0 14px}#p-desk .vz-box svg.vz{display:block;width:100%;height:auto;overflow:visible}#p-desk .vz-hl{margin:0 0 8px;font-size:15px;font-weight:700;color:var(--hd);line-height:1.35}#p-desk .vz-ht{margin:14px 0 2px;font-size:13px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;color:var(--mu)}#p-desk .vz-ht span{margin-left:6px;font-weight:500;letter-spacing:0;text-transform:none}#p-desk .vz-h{margin:0 0 6px;font-size:12px;font-weight:700;color:var(--mu)}#p-desk .vz-e{margin:6px 0;color:var(--mu);font-size:14px}#p-desk .vz-2{display:grid;gap:24px}@media(min-width:760px){#p-desk .vz-2{grid-template-columns:1fr 1fr}}#p-desk .vz text{font-family:var(--fs);font-size:12px}#p-desk .vz .vz-t,#p-desk .vz .vz-l{fill:var(--tx)}#p-desk .vz .vz-a{fill:var(--mu);font-size:11px}#p-desk .vz .vz-v{fill:var(--tx);font-weight:700;font-variant-numeric:tabular-nums}#p-desk .vz .vz-v.p{fill:var(--up)}#p-desk .vz .vz-v.n{fill:var(--dn)}#p-desk .vz .vz-g{stroke:var(--ln2);stroke-width:1}#p-desk .vz .vz-z{stroke:var(--ln);stroke-width:1.4}#p-desk .vz .vz-cap{stroke:var(--wn);stroke-width:2.5}#p-desk .vz .vz-b.p{fill:var(--up)}#p-desk .vz .vz-b.n{fill:var(--dn)}#p-desk .vz .vz-b.z{fill:var(--mu)}#p-desk .vz .vz-b.fl{fill:var(--bl)}#p-desk .vz .vz-b.lg{fill:var(--up)}#p-desk .vz .vz-b.sh{fill:var(--dn)}#p-desk .vz .vz-tr{fill:var(--tr)}#p-desk .vz .vz-uw{fill:var(--dnb)}#p-desk .vz .vz-uwl{fill:none;stroke:var(--dn);stroke-width:2}#p-desk .vz .vz-dot.n{fill:var(--dn)}#p-desk .vz .vz-ln{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}#p-desk .vz .vz-ln.vz-dk{stroke:var(--hd);stroke-width:3}#p-desk .vz .vz-el{font-size:11.5px;font-weight:700}#p-desk .vz .vz-el.vz-dk{fill:var(--hd)}#p-desk .vz .vz-c0{stroke:#4e9cf5;fill:#4e9cf5}#p-desk .vz .vz-c1{stroke:#e8a33d;fill:#e8a33d}#p-desk .vz .vz-c2{stroke:#3fc1a5;fill:#3fc1a5}#p-desk .vz .vz-c3{stroke:#c774e8;fill:#c774e8}#p-desk .vz .vz-c4{stroke:#e8675f;fill:#e8675f}#p-desk .vz .vz-c5{stroke:#9bc53d;fill:#9bc53d}#p-desk .vz .vz-c6{stroke:#f2c94c;fill:#f2c94c}#p-desk .vz .vz-c7{stroke:#8f9bb3;fill:#8f9bb3}#p-desk .vz polyline.vz-ln[class*=vz-c]{fill:none}#p-desk .vz .vz-sc{fill-opacity:.55;stroke-width:1.2}#p-desk .vz .vz-sc.ok{fill:var(--up);stroke:var(--up)}#p-desk .vz .vz-sc.wn{fill:var(--wn);stroke:var(--wn)}#p-desk .vz .vz-sc.bad{fill:var(--dn);stroke:var(--dn)}#p-desk .vz .vz-sc.p,#p-desk .vz .vz-sc.z{fill:var(--bl);stroke:var(--bl)}#p-desk .vz .vz-sc.n{fill:var(--dn);stroke:var(--dn)}#p-desk .vz-k{display:flex;flex-wrap:wrap;gap:6px 16px;margin:2px 0 0;font-size:12px;color:var(--mu)}#p-desk .vz-k i{display:inline-block;width:10px;height:10px;margin-right:6px;border-radius:3px;vertical-align:-1px}#p-desk .vz-k .lg,#p-desk .vz-k .ok{background:var(--up)}#p-desk .vz-k .sh,#p-desk .vz-k .bad{background:var(--dn)}#p-desk .vz-k .wn{background:var(--wn)}#p-desk .vz-k .p{background:var(--bl)}#p-desk .vz-fd{display:inline-block;width:9px;height:9px;margin-right:6px;border-radius:50%;vertical-align:0}#p-desk .vz-fd.up{background:var(--up)}#p-desk .vz-fd.wn{background:var(--wn)}#p-desk .vz-fd.dn{background:var(--dn)}#p-desk .vz-lg{display:flex;flex-wrap:wrap;gap:4px 14px;margin:6px 0 0;font-size:12.5px;color:var(--tx)}#p-desk .vz-lg i{display:inline-block;width:12px;height:4px;margin-right:6px;border-radius:2px;vertical-align:3px}#p-desk .vz-lg b{font-weight:700}#p-desk .vz-lg b.p{color:var(--up)}#p-desk .vz-lg b.n{color:var(--dn)}#p-desk .vz-lg .vz-c0{background:#4e9cf5}#p-desk .vz-lg .vz-c1{background:#e8a33d}#p-desk .vz-lg .vz-c2{background:#3fc1a5}#p-desk .vz-lg .vz-c3{background:#c774e8}#p-desk .vz-lg .vz-c4{background:#e8675f}#p-desk .vz-lg .vz-c5{background:#9bc53d}#p-desk .vz-lg .vz-c6{background:#f2c94c}#p-desk .vz-lg .vz-c7{background:#8f9bb3}#p-desk .vz-lg .vz-dk{background:var(--hd);height:5px}'; document.head.appendChild(st); }
window.VZD = {paint, kinds: Object.keys(K), headlines: HL, _k: K};
})();
