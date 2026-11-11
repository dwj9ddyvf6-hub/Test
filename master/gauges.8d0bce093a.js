/* Master Desk terminal: small visual instruments drawn from edition numbers only (no recomputed reads).
   planChart  an open plan on its instrument's daily bars: entry, stop, targets, the expiry, the last price and the
              distance to the trigger (My Book; the edition's book.plans[] with its bars from the book's pack).
   gamma / range / day / fear / agree  the market strip's tiles as marker-on-axis gauges (strip.js).
   Pure string builders: window.MDG, testable under node (tests/test_term_gauges.py). */
(() => {
const G = typeof window !== 'undefined' ? window : globalThis;
const isN = v => typeof v === 'number' && isFinite(v);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const f1 = v => (Math.round(v * 10) / 10).toString();
// one rounding for every % on the page (T-186: toFixed read 0.15 as 0.1 where Intl read 0.2)
const dec = (v, d) => v.toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: false});
const pc = (v, d) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + dec(Math.abs(v), d == null ? 1 : d) + '%' : '—';
const px = v => isN(v) ? v.toFixed(2) : '—';
const T = (x, y, s, cl, a) => '<text class="' + cl + '" x="' + f1(x) + '" y="' + f1(y) + '"' + (a ? ' text-anchor="' + a + '"' : '') + '>' + esc(s) + '</text>';
const svg = (W, H, body, label, cl) => '<svg class="' + (cl || 'g-s') + '" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="' + esc(label) + '">' + body + '</svg>';
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const dlab = iso => { const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(iso || ''); return m ? MON[+m[2] - 1] + ' ' + (+m[3]) : ''; };
const isoOf = t => new Date(t * 1e3).toISOString().slice(0, 10);
function weekdays(a, b) {                       // sessions after day a up to and including day b (weekdays; holidays not known here)
  let n = 0; const d = new Date(a + 'T12:00:00Z'), e = new Date(b + 'T12:00:00Z');
  while (d < e && n < 60) { d.setUTCDate(d.getUTCDate() + 1); if (d.getUTCDay() % 6) n++; }
  return n;
}
// labels on one vertical axis, nudged apart so no two overlap (min gap px), kept inside [lo, hi]
function spread(items, gap, lo, hi) {
  const s = items.slice().sort((a, b) => a.y - b.y);
  for (let i = 1; i < s.length; i++) if (s[i].y - s[i - 1].y < gap) s[i].y = s[i - 1].y + gap;
  if (s.length && s[s.length - 1].y > hi) { s[s.length - 1].y = hi; for (let i = s.length - 2; i >= 0; i--) if (s[i + 1].y - s[i].y < gap) s[i].y = s[i + 1].y - gap; }
  s.forEach(o => { o.y = Math.max(lo, o.y); });
  return s;
}

// round price gridlines (T-153, p17: the scale read 579.56 / 664.28 / 749.00, the padded range split in thirds): a step of
// 1, 2, 2.5 or 5 x 10^k (Heckbert's nice numbers), every multiple of it inside [lo, hi]
function niceTicks(lo, hi, want) {
  if (!(hi > lo)) return [];
  const raw = (hi - lo) / Math.max(1, want), p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
  const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p, out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(Math.round(v / step) * step);
  return out;
}
// ---- an open plan on its chart -----------------------------------------------------------------------------------------
function trigger(p) {                            // distance from the last price to the entry, in % of the last price
  if (!isN(p.last) || !isN(p.level)) return null;
  return (p.level - p.last) / p.last * 100;
}
function planLine(p) {
  const d = trigger(p), tg = (p.targets || []).filter(t => isN(t.price)), long = p.side !== 'short';
  const rr = isN(p.level) && isN(p.stop) && tg.length && p.level !== p.stop ? Math.abs(tg[tg.length - 1].price - p.level) / Math.abs(p.level - p.stop) : null;
  const trig = p.status === 'triggered' ? 'Triggered' : isN(d) ? (Math.abs(d) < 0.05 ? 'At the trigger' : Math.abs(d).toFixed(1) + '%' + (d > 0 ? ' below' : ' above') + ' the trigger') : 'Waiting for its trigger';
  return [trig, isN(p.level) && isN(p.stop) ? 'stop ' + pc(Math.abs(p.level - p.stop) / p.level * 100, 1).replace('+', '') + ' from entry' : '',
    isN(rr) ? rr.toFixed(1) + ' R to the last target' : '', long ? '' : 'short'].filter(Boolean).join(' · ');
}
function planChart(p, W) {
  W = Math.max(280, W || 560);
  const bars = (p.bars || []).filter(b => isN(b.h) && isN(b.l) && isN(b.c) && isN(b.t));
  const tg = (p.targets || []).filter(t => isN(t.price));
  const H = 230, pt = 12, pb = 22, pl = 6, lab = 96, x1 = W - lab;
  const lastDay = bars.length ? isoOf(bars[bars.length - 1].t) : null;
  const fut = lastDay && p.expires ? Math.max(1, weekdays(lastDay, p.expires)) : 0, n = bars.length + fut + 1;
  const lv = [p.level, p.stop, p.last, ...tg.map(t => t.price)].filter(isN);
  const all = bars.flatMap(b => [b.h, b.l]).concat(lv);
  if (!all.length) return '';
  let lo = Math.min(...all), hi = Math.max(...all); const pad = (hi - lo) * 0.06 || hi * 0.01; lo -= pad; hi += pad;
  const X = i => pl + (i + 0.5) / n * (x1 - pl), Y = v => pt + (hi - v) / (hi - lo) * (H - pt - pb), bw = Math.max(1.5, (x1 - pl) / n * 0.62);
  const long = p.side !== 'short';
  let b = '';
  // zones: the risk (entry to stop) and the reward (entry to the last target), drawn from today to the expiry
  const zx0 = X(bars.length - 1), zx1 = X(n - 1);
  if (isN(p.level) && isN(p.stop)) b += '<rect class="g-zr" x="' + f1(zx0) + '" y="' + f1(Math.min(Y(p.level), Y(p.stop))) + '" width="' + f1(zx1 - zx0) + '" height="' + f1(Math.abs(Y(p.level) - Y(p.stop))) + '"><title>Risk: entry to stop</title></rect>';
  if (isN(p.level) && tg.length) b += '<rect class="g-zg" x="' + f1(zx0) + '" y="' + f1(Math.min(Y(p.level), Y(tg[tg.length - 1].price))) + '" width="' + f1(zx1 - zx0) + '" height="' + f1(Math.abs(Y(p.level) - Y(tg[tg.length - 1].price))) + '"><title>Reward: entry to the last target</title></rect>';
  // expiry
  if (fut) b += '<line class="g-ex" x1="' + f1(zx1) + '" x2="' + f1(zx1) + '" y1="' + pt + '" y2="' + (H - pb) + '"/>' + T(zx1, H - 6, 'Expires ' + dlab(p.expires), 'g-ax', 'end');
  // candles
  bars.forEach((r, i) => {
    const up = r.c >= (isN(r.o) ? r.o : r.c), x = X(i), yo = Y(isN(r.o) ? r.o : r.c), yc = Y(r.c);
    b += '<g class="g-c ' + (up ? 'u' : 'd') + '"><title>' + esc(dlab(isoOf(r.t)) + ' · open ' + px(r.o) + ' · high ' + px(r.h) + ' · low ' + px(r.l) + ' · close ' + px(r.c)) + '</title>' +
      '<line x1="' + f1(x) + '" x2="' + f1(x) + '" y1="' + f1(Y(r.h)) + '" y2="' + f1(Y(r.l)) + '"/>' +
      '<rect x="' + f1(x - bw / 2) + '" y="' + f1(Math.min(yo, yc)) + '" width="' + f1(bw) + '" height="' + f1(Math.max(1, Math.abs(yo - yc))) + '" rx="1"/></g>';
  });
  if (bars.length) b += T(pl, H - 6, dlab(isoOf(bars[0].t)), 'g-ax');
  // a price scale (audit 2026-11-04 HM-10: the chart had no price axis and two dates): three gridlines with their price
  // at the left, and the middle bar's date
  niceTicks(lo, hi, 4).forEach(v => { b += '<line class="g-gr" x1="' + pl + '" x2="' + f1(x1) + '" y1="' + f1(Y(v)) + '" y2="' + f1(Y(v)) + '"/>' + T(pl + 2, Y(v) - 3, String(+v.toFixed(2)), 'g-ax g-py'); });
  // the middle date only where it clears the first date and the expiry (T-240: 'Sep 29' over 'Expires Nov 12' at 390 px);
  // widths at the 11 px label floor, 0.6 em a character in the monospace face
  if (bars.length > 8) {
    const m = Math.floor(bars.length / 2), t = dlab(isoOf(bars[m].t)), cw = 6.6, xm = X(m), hw = t.length * cw / 2;
    const left = pl + dlab(isoOf(bars[0].t)).length * cw + 8, right = fut ? zx1 - ('Expires ' + dlab(p.expires)).length * cw - 8 : W;
    if (xm - hw >= left && xm + hw <= right) b += T(xm, H - 6, t, 'g-ax', 'middle');
  }
  // price lines and their labels at the right
  const L = [];
  const line = (v, cl, name) => { if (!isN(v)) return; b += '<line class="g-l ' + cl + '" x1="' + pl + '" x2="' + f1(x1) + '" y1="' + f1(Y(v)) + '" y2="' + f1(Y(v)) + '"/>'; L.push({y: Y(v), t: name + ' ' + px(v), cl}); };
  line(p.stop, 'st', 'Stop');
  tg.forEach((t, i) => line(t.price, 'tg', 'T' + (i + 1)));
  line(p.level, 'en', 'Entry');
  if (isN(p.last) && bars.length) {
    const yl = Y(p.last), xl = X(bars.length - 1);
    if (isN(p.level)) b += '<line class="g-gap" x1="' + f1(xl) + '" x2="' + f1(xl) + '" y1="' + f1(yl) + '" y2="' + f1(Y(p.level)) + '"/>';
    b += '<circle class="g-last" cx="' + f1(xl) + '" cy="' + f1(yl) + '" r="4"/>';
    L.push({y: yl, t: 'Last ' + px(p.last), cl: 'lt'});
  }
  spread(L, 13, pt + 4, H - pb).forEach(o => { b += '<text class="g-lb ' + o.cl + '" x="' + f1(x1 + 6) + '" y="' + f1(o.y + 4) + '">' + esc(o.t) + '</text>'; });
  return svg(W, H, b, p.symbol + ' daily bars with the plan: entry ' + px(p.level) + ', stop ' + px(p.stop) + (tg.length ? ', targets ' + tg.map(t => px(t.price)).join(', ') : '') + (p.expires ? ', expires ' + p.expires : ''), 'g-plan');
}
function planCard(p, W) {
  const head = '<div class="g-ph"><b>' + esc(p.symbol) + '</b><span class="g-sd ' + (p.side === 'short' ? 'dn' : 'up') + '">' + esc(p.side || '') + '</span>' +
    '<span class="mu">' + esc(p.entry_type === 'limit' ? 'limit' : p.entry_type === 'cross_below' ? 'on a close below' : 'on a close above') + ' ' + px(p.level) + '</span></div>';
  const ch = (p.bars || []).length ? planChart(p, W) : '<p class="mu">No bars on file for ' + esc(p.symbol) + ' yet.</p>';
  return '<div class="g-pc">' + head + '<p class="g-pl">' + esc(planLine(p)) + '</p>' + ch + '</div>';
}


// ---- the galath arc gauge: a segmented multi-colour half ring, a needle, the big number and a status pill -----------
// segs: [[upTo, cls, label]...] ascending over [lo, hi]; v: the needle's value
function arc(segs, v, lo, hi, big, pill, pcl, ticks) {
  const W = 220, cx = 110, cy = 92, R = 78, r0 = 56, ang = x => Math.PI * (1 - (Math.max(lo, Math.min(hi, x)) - lo) / (hi - lo));
  const P = (a, r) => f1(cx + r * Math.cos(a)) + ',' + f1(cy - r * Math.sin(a));
  let b = '', from = lo;
  segs.forEach(([to, cl, name]) => {
    const a0 = ang(from), a1 = ang(to), lg = 0;
    b += '<path class="kc-sg ' + cl + '" d="M' + P(a0, R) + ' A' + R + ',' + R + ' 0 ' + lg + ' 1 ' + P(a1, R) + ' L' + P(a1, r0) + ' A' + r0 + ',' + r0 + ' 0 ' + lg + ' 0 ' + P(a0, r0) + 'Z"><title>' + esc(name) + '</title></path>';
    from = to;
  });
  (ticks || []).forEach(t => { const a = ang(t[0]); b += T(cx + (R + 9) * Math.cos(a), cy - (R + 9) * Math.sin(a) + 3, t[1], 'kc-tk', 'middle'); });
  if (isN(v)) { const a = ang(v); b += '<line class="kc-nd" x1="' + cx + '" y1="' + cy + '" x2="' + P(a, R - 4).split(',')[0] + '" y2="' + P(a, R - 4).split(',')[1] + '"/><circle class="kc-hub" cx="' + cx + '" cy="' + cy + '" r="5"/>'; }
  b += T(cx, cy + 30, big, 'kc-big', 'middle');
  return '<div class="kc-g">' + svg(W, 128, b, big + ' ' + (pill || ''), 'kc-arc') + (pill ? '<span class="kc-pill ' + (pcl || '') + '">' + esc(pill) + '</span>' : '') + '</div>';
}

// ---- the market strip's instruments ------------------------------------------------------------------------------------
const GW = 220;
function axis(lo, hi, W) { const a = 8, b = W - 8; return v => a + (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo) * (b - a); }
// SPY gamma: spot at 0, the put and call walls and the flip as markers on a % axis; the short-gamma side shaded
function gamma(g) {
  if (!g || ![g.put_wall_pct, g.call_wall_pct, g.flip_pct].some(isN)) return '';
  const m = Math.max(1.5, ...[g.put_wall_pct, g.call_wall_pct, g.flip_pct].filter(isN).map(Math.abs)) * 1.12, X = axis(-m, m, GW), y = 22;
  let b = '';
  if (isN(g.flip_pct)) {                         // below the flip dealers are short gamma (moves amplify)
    const xf = X(g.flip_pct);
    b += '<rect class="g-neg" x="8" y="' + (y - 7) + '" width="' + f1(xf - 8) + '" height="14" rx="3"><title>Short gamma: moves amplify</title></rect>' +
      '<rect class="g-pos" x="' + f1(xf) + '" y="' + (y - 7) + '" width="' + f1(GW - 8 - xf) + '" height="14" rx="3"><title>Long gamma: moves dampen</title></rect>';
  } else b += '<rect class="g-trk" x="8" y="' + (y - 7) + '" width="' + (GW - 16) + '" height="14" rx="3"/>';
  const mk = (v, cl, name, up) => isN(v) ? '<line class="g-mk ' + cl + '" x1="' + f1(X(v)) + '" x2="' + f1(X(v)) + '" y1="' + (y - 10) + '" y2="' + (y + 10) + '"><title>' + esc(name + ' ' + pc(v, 1)) + '</title></line>' +
    T(X(v), up ? y - 13 : y + 21, name + ' ' + pc(v, 1), 'g-tk', X(v) < 40 ? 'start' : X(v) > GW - 40 ? 'end' : both ? (v === lo ? 'end' : 'start') : 'middle') : '';
  // T-235: with both walls the lower one's label ends at its marker and the higher one's starts at its own; centred,
  // live 11-08 'Put +0.8%' ran into 'Call +8.9%' (both above the band)
  const both = isN(g.put_wall_pct) && isN(g.call_wall_pct), lo = both ? Math.min(g.put_wall_pct, g.call_wall_pct) : null;
  b += mk(g.put_wall_pct, 'pw', 'Put', true) + mk(g.call_wall_pct, 'cw', 'Call', true);
  // below the band: the flip and spot labels lean away from each other so they never overlap
  const fr = isN(g.flip_pct) && g.flip_pct > 0;
  if (isN(g.flip_pct)) b += '<line class="g-mk fl" x1="' + f1(X(g.flip_pct)) + '" x2="' + f1(X(g.flip_pct)) + '" y1="' + (y - 10) + '" y2="' + (y + 10) + '"><title>Flip ' + pc(g.flip_pct, 1) + '</title></line>' +
    T(X(g.flip_pct) + (fr ? -2 : 2), y + 21, 'Flip ' + pc(g.flip_pct, 1), 'g-tk', fr ? 'start' : 'end');
  b += '<circle class="g-spot" cx="' + f1(X(0)) + '" cy="' + y + '" r="4"><title>Spot</title></circle>' + T(X(0) + (fr ? -4 : 4), y + 21, 'Spot', 'g-tk', fr ? 'end' : 'start');
  return svg(GW, 46, b, 'SPY spot against its put wall ' + pc(g.put_wall_pct) + ', call wall ' + pc(g.call_wall_pct) + ' and gamma flip ' + pc(g.flip_pct));
}
// Range: the expected one-day move as a band around 0 (the 68% band inside it), today's SPY move as the marker
function range(mv, today) {
  if (!mv || !isN(mv.em_pct)) return '';
  const m = Math.max(mv.em_pct * 1.35, isN(today) ? Math.abs(today) * 1.15 : 0), X = axis(-m, m, GW), y = 20;
  let b = '<rect class="g-trk" x="8" y="' + (y - 6) + '" width="' + (GW - 16) + '" height="12" rx="3"/>' +
    '<rect class="g-em" x="' + f1(X(-mv.em_pct)) + '" y="' + (y - 6) + '" width="' + f1(X(mv.em_pct) - X(-mv.em_pct)) + '" height="12" rx="3"><title>Expected move ±' + mv.em_pct.toFixed(2) + '%</title></rect>';
  if (isN(mv.band68_pct)) b += '<rect class="g-68" x="' + f1(X(-mv.band68_pct)) + '" y="' + (y - 6) + '" width="' + f1(X(mv.band68_pct) - X(-mv.band68_pct)) + '" height="12" rx="3"><title>68% band ±' + mv.band68_pct.toFixed(2) + '%</title></rect>';
  b += '<line class="g-z" x1="' + f1(X(0)) + '" x2="' + f1(X(0)) + '" y1="' + (y - 8) + '" y2="' + (y + 8) + '"/>' +
    T(X(-mv.em_pct), y + 20, pc(-mv.em_pct, 2), 'g-tk', 'middle') + T(X(mv.em_pct), y + 20, pc(mv.em_pct, 2), 'g-tk', 'middle');
  if (isN(today)) {
    const out = Math.abs(today) > mv.em_pct;
    b += '<path class="g-pt ' + (out ? 'dn' : '') + '" d="M' + f1(X(today) - 5) + ',' + (y - 13) + ' L' + f1(X(today) + 5) + ',' + (y - 13) + ' L' + f1(X(today)) + ',' + (y - 5) + 'Z"><title>SPY today ' + pc(today, 2) + '</title></path>';
  }
  return svg(GW, 44, b, 'Expected one-day move ±' + mv.em_pct.toFixed(2) + '%' + (isN(today) ? ', SPY today ' + pc(today, 2) : ''));
}
// Day: the gap and the range so far, each a bar against the expected move (tick at 1 expected move)
function day(dy, em) {
  if (!dy || !isN(em) || em <= 0) return '';
  const rows = [['Gap', Math.abs(dy.gap_pct || 0), pc(dy.gap_pct, 2)], ['Range', dy.range_pct || 0, (dy.range_pct || 0).toFixed(2) + '%']];
  const lw = 40, vw = 46, x0 = lw, x1 = GW - vw, sc = v => Math.min(1, v / (2 * em)) * (x1 - x0);
  let b = '';
  rows.forEach((r, i) => {
    const y = 4 + i * 18, hot = r[1] > em;
    b += T(lw - 6, y + 10, r[0], 'g-tk', 'end') + '<rect class="g-trk" x="' + x0 + '" y="' + y + '" width="' + (x1 - x0) + '" height="11" rx="3"/>' +
      '<rect class="g-bar ' + (hot ? 'dn' : '') + '" x="' + x0 + '" y="' + y + '" width="' + f1(Math.max(2, sc(r[1]))) + '" height="11" rx="3"/>' + T(GW - 2, y + 10, r[2], 'g-tk', 'end');
  });
  const xe = x0 + (x1 - x0) / 2;
  b += '<line class="g-z" x1="' + f1(xe) + '" x2="' + f1(xe) + '" y1="1" y2="37"><title>1 expected move</title></line>';
  return svg(GW, 40, b, 'Gap ' + pc(dy.gap_pct, 2) + ' and range ' + (dy.range_pct || 0).toFixed(2) + '% against the ±' + em.toFixed(2) + '% expected move');
}
// Fear day: the Buy List's four conditions as a checklist of dots (filled = met)
const FEAR = [['spy_drop', '1% drop'], ['below_50d', 'Under 50d'], ['vol_spike', 'Vol spike'], ['vix_spike', 'VIX spike']];
function fear(f) {
  if (!f) return '';
  const w = f.fear_why || [];
  return '<ul class="g-ck">' + FEAR.map(([k, n]) => '<li class="' + (w.includes(k) ? 'on' : '') + '"><i aria-hidden="true"></i>' + esc(n) + '<span class="sr">' + (w.includes(k) ? ' met' : ' not met') + '</span></li>').join('') + '</ul>';
}
// SPX / NQ: today's SPY and QQQ moves as bars from zero
function agree(a) {
  if (!a || !isN(a.spy_pct) || !isN(a.qqq_pct)) return '';
  const m = Math.max(0.5, Math.abs(a.spy_pct), Math.abs(a.qqq_pct)) * 1.1, lw = 38, vw = 50, x0 = lw, x1 = GW - vw, zx = (x0 + x1) / 2, sc = v => v / m * (x1 - x0) / 2;
  let b = '<line class="g-z" x1="' + f1(zx) + '" x2="' + f1(zx) + '" y1="1" y2="37"/>';
  [['SPY', a.spy_pct], ['QQQ', a.qqq_pct]].forEach((r, i) => {
    const y = 4 + i * 18, w = sc(r[1]);
    b += T(lw - 6, y + 10, r[0], 'g-tk', 'end') + '<rect class="g-bar ' + (r[1] < 0 ? 'dn' : 'up') + '" x="' + f1(w < 0 ? zx + w : zx) + '" y="' + y + '" width="' + f1(Math.max(2, Math.abs(w))) + '" height="11" rx="3"/>' + T(GW - 2, y + 10, pc(r[1], 2), 'g-tk', 'end');
  });
  return svg(GW, 40, b, 'SPY ' + pc(a.spy_pct, 2) + ' and QQQ ' + pc(a.qqq_pct, 2) + ' today');
}

// SPX / NQ: SPY's and QQQ's 5-minute paths for the last session, % from the prior close, as two lines from 0
function lastSession(L) {
  if (!L || !Array.isArray(L.t) || !Array.isArray(L.c) || !isN(L.prev) || !L.t.length) return null;
  const day = isoOf(L.t[L.t.length - 1]), t = [], v = [];
  L.t.forEach((x, i) => { if (isoOf(x) === day && isN(L.c[i])) { t.push(x); v.push((L.c[i] / L.prev - 1) * 100); } });
  return v.length >= 2 ? {t, v} : null;
}
function spreadPill(a) {
  if (!a || !isN(a.spy_pct) || !isN(a.qqq_pct)) return '';
  const d = a.qqq_pct - a.spy_pct, s = (d > 0 ? '+' : d < 0 ? '−' : '') + Math.abs(d).toFixed(2) + ' PTS';
  return Math.abs(d) < 0.1 ? '<span class="kc-pill n">IN STEP ' + s + '</span>'
    : '<span class="kc-pill ' + (d < 0 ? 'r' : 'g') + '">NQ ' + (d < 0 ? 'LAGGING ' : 'LEADING ') + s + '</span>';
}
function paths(lines, a) {
  const S = lastSession(lines && lines.SPY), Q = lastSession(lines && lines.QQQ);
  if (!S || !Q) return agree(a) + spreadPill(a);
  const W = GW, H = 92, pl = 4, pr = 44, pt = 8, pb = 8, all = S.v.concat(Q.v, [0]);
  let lo = Math.min(...all), hi = Math.max(...all); const pd = (hi - lo) * 0.08 || 0.1; lo -= pd; hi += pd;
  const t0 = Math.min(S.t[0], Q.t[0]), t1 = Math.max(S.t[S.t.length - 1], Q.t[Q.t.length - 1]) || t0 + 1;
  const X = t => pl + (t - t0) / ((t1 - t0) || 1) * (W - pl - pr), Y = v => pt + (hi - v) / (hi - lo) * (H - pt - pb);
  const ln = (o, cl) => '<polyline class="kc-ln ' + cl + '" points="' + o.t.map((t, i) => f1(X(t)) + ',' + f1(Y(o.v[i]))).join(' ') + '"/>';
  const ends = spread([{y: Y(S.v[S.v.length - 1]), t: 'SPY ' + pc(S.v[S.v.length - 1], 2), cl: 's'}, {y: Y(Q.v[Q.v.length - 1]), t: 'QQQ ' + pc(Q.v[Q.v.length - 1], 2), cl: 'q'}], 12, 6, H - 2);
  let b = '<line class="g-z" x1="' + pl + '" x2="' + (W - pr) + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"/>' + ln(S, 's') + ln(Q, 'q');
  ends.forEach(e => { b += '<text class="kc-el ' + e.cl + '" x="' + (W - pr + 3) + '" y="' + f1(e.y + 3) + '">' + esc(e.t.split(' ')[0]) + '</text>'; });
  return svg(W, H, b, 'SPY ' + pc(S.v[S.v.length - 1], 2) + ' and QQQ ' + pc(Q.v[Q.v.length - 1], 2) + ' through the session, from the prior close') + spreadPill(a);
}

G.MDG = {paths, lastSession, spreadPill, arc, planChart, planCard, planLine, trigger, gamma, range, day, fear, agree, weekdays, spread};
})();
