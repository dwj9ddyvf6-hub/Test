/* Master Desk terminal: the vendor package (desk/terminal/vendor_ext.py). Three places, all drawn from the edition and
   nothing recomputed here: each card's context gets the plan's "voided if" line, the chart signals (range ring, Heikin-Ashi,
   Stochastic RSI) and the next session's pivot points; each listed long's options drawer gets expected value and the P&L
   grid; the Market tab gets the empirical move, the clock, Zweig breadth thrust, the straddle verdict and the regime. A block
   without data says why in one line. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id);
if (!M) return;
const esc = M.esc, isN = M.isN, num = M.num;
const ok = b => b && b.status === 'ok';
const sg = (v, d) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), d == null ? 1 : d) : '—';
const pc = (v, d) => isN(v) ? num(v, d == null ? 0 : d) + '%' : '—';
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
const why = b => '<p class="mu">' + esc(b && b.reason || 'No data') + '</p>';
const grp = (h, inner) => inner ? '<div class="dg cx vxg"><h4>' + esc(h) + '</h4>' + inner + '</div>' : '';

// a KPI ring: frac 0..1 filled, marks at fractions, the value in the middle, what it counts underneath
function ring(frac, tone, mid, sub, marks) {
  const f = Math.max(0, Math.min(1, isN(frac) ? frac : 0)), R = 15.9155;
  const tick = m => { const a = (m * 360 - 90) * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
    return '<line class="vk" x1="' + (18 + c * (R - 2.6)).toFixed(2) + '" y1="' + (18 + s * (R - 2.6)).toFixed(2) + '" x2="' + (18 + c * (R + 2.6)).toFixed(2) + '" y2="' + (18 + s * (R + 2.6)).toFixed(2) + '"/>'; };
  return '<figure class="vr"><svg viewBox="0 0 36 36" role="img" aria-label="' + esc(mid + ' ' + sub) + '"><circle class="vb" cx="18" cy="18" r="' + R + '"/>' +
    '<circle class="vf ' + tone + '" cx="18" cy="18" r="' + R + '" pathLength="100" stroke-dasharray="' + (f * 100).toFixed(1) + ' 100" transform="rotate(-90 18 18)"/>' +
    (marks || []).map(tick).join('') + '<text x="18" y="20.6" text-anchor="middle">' + esc(mid) + '</text></svg><figcaption>' + esc(sub) + '</figcaption></figure>';
}

// ---- the card -------------------------------------------------------------------------------------------------------
const CLOUD = {'above both clouds': 'up', 'below both clouds': 'dn', 'between the clouds': 'wn'}, BAND = {low: 'up', mid: 'wn', high: 'dn'};
function voided(f, s) {
  if (!ok(f) || !s.close) return '';
  let t = f.text.replace('the stop', 'the stop (' + M.px(s.close, f.at, 1) + ')');
  if (isN(f.trigger_at)) t = t.replace('the trigger', 'the trigger (' + M.px(s.close, f.trigger_at, 1) + ')');
  return '<p class="vv">' + esc(cap(t)) + '.' + (f.valid_through ? ' <span class="mu">The read stands through the ' + esc(M.day ? M.day(f.valid_through) : f.valid_through) + ' session.</span>' : '') + '</p>';
}
function signals(c) {
  const out = [], r = c.range, h = c.heikin, k = c.stoch;
  if (ok(h)) out.push('<li><b>Heikin-Ashi.</b> ' + h.run + (h.run === 1 ? ' ' + h.color + ' candle' : ' ' + h.color + ' candles in a row') +
    (h.flat_bottom ? ', the last with no ' + (h.color === 'up' ? 'lower' : 'upper') + ' wick' : '') + '</li>');
  if (ok(k)) out.push('<li><b>Stochastic RSI.</b> %K ' + num(k.k, 1) + ', %D ' + num(k.d, 1) + ' (' + esc(k.zone) + ')' + (k.cross ? '; %K just crossed ' + k.cross + ' through %D' : '') + (isN(k.rsi) ? '; RSI(14) ' + num(k.rsi, 0) : '') + '</li>');
  const g = ok(r) ? ring(r.pct / 100, BAND[r.band] || 'wn', num(r.pct, 0) + '%', 'of ATR(14) the last range covered', [0.7, 0.9]) : '';
  const tr = ok(r) ? '<li><b>Trend.</b> Price is ' + esc(r.trend) + ' (5–12 and 34–50 day EMAs)</li>' : '';
  return (g || out.length || tr) ? '<div class="vsg">' + g + '<ul class="cxf">' + out.join('') + tr + '</ul></div>' : '';
}
const LV = {classic: ['Classic', ['R3', 'R2', 'R1', 'P', 'S1', 'S2', 'S3']], fibonacci: ['Fibonacci', ['R3', 'R2', 'R1', 'P', 'S1', 'S2', 'S3']],
  woodie: ['Woodie', ['R2', 'R1', 'P', 'S1', 'S2']], camarilla: ['Camarilla', ['R4', 'R3', 'R2', 'R1', 'S1', 'S2', 'S3', 'S4']]};
function pivots(p, s) {
  if (!ok(p) || !s.close) return '';
  const keys = ['R4', 'R3', 'R2', 'R1', 'P', 'S1', 'S2', 'S3', 'S4'], kinds = Object.keys(LV);
  const rows = keys.filter(k => kinds.some(n => isN((p[n] || {})[k]))).map(k => '<tr><th scope="row">' + k + '</th>' + kinds.map(n => {
    const v = (p[n] || {})[k]; return '<td class="r">' + (isN(v) ? M.px(s.close, v, 0) + ' <small>' + sg(v, 1) + '%</small>' : '') + '</td>'; }).join('') + '</tr>').join('');
  return '<details class="vpv"><summary>Pivot points for ' + esc(M.day ? M.day(p.for) : p.for) + '</summary><p class="mu">From the ' + esc(M.day ? M.day(p.from) : p.from) + ' high, low and close; small figures are % from that close.</p><div class="tw"><table class="t"><thead><tr><th></th>' + kinds.map(n => '<th class="r">' + LV[n][0] + '</th>').join('') + '</tr></thead><tbody>' + rows + '</tbody></table></div></details>';
}
function card(s) {
  const c = s && s.context;
  if (!c) return '';
  return grp('Voided if', voided(c.falsifier, s)) + grp('Chart signals', signals(c)) + grp('Pivot points', pivots(c.pivots, s));
}
const prev = window.MDC && window.MDC.html;
if (prev) window.MDC.html = s => prev(s) + card(s);

// ---- the options drawer ------------------------------------------------------------------------------------------------
const level = (v, top) => Math.min(4, Math.max(1, Math.ceil(Math.abs(v) / top * 4)));
function heat(x, s) {
  const g = x.pnl;
  if (!ok(g)) return '';
  const cols = g.cols.map(c => '<th class="r">' + (c.left ? c.left : 'End') + '</th>').join('');
  const rows = g.rows.slice().reverse().map(r => '<tr><th scope="row">' + (s.close ? M.px(s.close, r.move, 0) + ' ' : '') + '<small>' + sg(r.move, 1) + '%</small></th>' + r.cells.map(v =>
    '<td class="r hc ' + (v > 0.005 ? 'p' + level(v, 2) : v < -0.005 ? 'n' + level(v, 1) : 'z') + '">' + (Math.abs(v) < 0.005 ? '0.00' : sg(v, 2)) + '</td>').join('') + '</tr>').join('');
  return '<details class="vpv"><summary>' + esc(x.kind) + ': profit or loss by price and date</summary><p class="mu">Multiples of the ' + num(g.risked, 2) + ' per share risked (0 breaks even, −1 loses it all) by sessions left to the expiry (End: the payoff at expiry). Each leg is priced by Black-Scholes at its quoted IV, held flat.</p><div class="tw"><table class="t vhm"><thead><tr><th>Price (move)</th>' + cols + '</tr></thead><tbody>' + rows + '</tbody></table></div></details>';
}
function drawer(s) {
  const ex = ((s.options || {}).express || []).filter(x => x.ev != null || x.pnl);
  if (!ex.length) return '';
  const ranked = ex.filter(x => x.ev != null).sort((a, b) => a.ev_rank - b.ev_rank);
  const rows = ranked.map(x => '<tr><th scope="row">' + esc(x.kind) + '</th><td class="r">' + sg(x.ev, 2) + '</td><td class="r">' + sg(x.ev_ratio * 100, 0) + '%</td><td class="r">' +
    pc(x.ev_win * 100) + ' <small>of ' + x.ev_n + '</small></td></tr>').join('');
  const none = ex.filter(x => x.ev == null && x.ev_reason).map(x => esc(x.kind) + ': ' + esc(x.ev_reason)).join('; ');
  return '<div class="xv"><div class="tw">' + (rows ? '<p class="mu">Expected value per share over this name’s own past windows of the same length, best first.</p><table class="t"><thead><tr><th>Structure</th>' +
    '<th class="r">EV</th><th class="r">EV / risked</th><th class="r">Paid in</th></tr></thead><tbody>' + rows + '</tbody></table>' : '') + '</div>' +
    (none ? '<p class="mu">' + none + '.</p>' : '') + ex.map(x => heat(x, s)).join('') + '</div>';
}
function drawers(d) {
  (d && d.setups || []).forEach(s => {
    const c = M.cards[s.id], x = c && c.db && c.db.querySelector('.xp');
    if (!x) return;
    const old = x.querySelector('.xv');
    if (old) old.remove();
    const h = drawer(s);
    if (h) x.insertAdjacentHTML('beforeend', h);
  });
}

// ---- the Market tab ------------------------------------------------------------------------------------------------------
const VIXR = {low: b => 'under ' + num(b.hi, 1), mid: b => num(b.lo, 1) + ' to ' + num(b.hi, 1), high: b => 'over ' + num(b.lo, 1)};
function emp(e) {
  if (!ok(e)) return '<div class="vt"><h3>Expected move from SPY’s history</h3>' + why(e) + '</div>';
  const t = e.today, h = e.holdout;
  const rows = e.buckets.map(b => '<tr' + (t && t.bucket === b.name ? ' class="now"' : '') + '><th scope="row">VIX ' + VIXR[b.name](b) + '</th><td class="r">±' + num(b.d1_pct, 2) + '%</td><td class="r">±' + num(b.d5_pct, 2) +
    '%</td><td class="r">' + num(b.n, 0) + '</td></tr>').join('');
  return '<div class="vt"><h3>Expected move from SPY’s history</h3>' + (t ? '<p>At VIX ' + num(t.vix, 1) + ' the VIX formula gives ±' + num(t.vix_em_pct, 2) + '% a day; SPY’s own history gives <b>±' + num(t.d1_pct, 2) +
    '% a day</b> and <b>±' + num(t.d5_pct, 2) + '% over five sessions</b>.</p>' : '') + '<p class="mu">The ' + e.target_pct + '% quantile of SPY’s absolute move by VIX tercile, since ' + esc(e.since) + '.</p><div class="tw"><table class="t">' +
    '<thead><tr><th>VIX at the start</th><th class="r">1 day</th><th class="r">5 days</th><th class="r">Sessions</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
    (h ? '<p class="mu">Held out, ' + esc(h.from) + ' to ' + esc(h.to) + ' (' + h.n + ' sessions): ' + num(h.cover1_pct, 1) + '% of one-day moves and ' + num(h.cover5_pct, 1) + '% of five-session moves stayed inside the band, against ' + h.target_pct + '% by construction.</p>' : '') + '</div>';
}
function clock(c) {
  if (!ok(c)) return '<div class="vt"><h3>Move still to come today</h3>' + why(c) + '</div>';
  const rings = c.rows.map(r => ring(r.left_pct / c.em_pct, 'ac', pc(r.left_pct / c.em_pct * 100), r.at + ' ET')).join('') + (c.now ? ring(c.now.left_pct / c.em_pct, 'up', pc(c.now.left_pct / c.em_pct * 100), 'now') : '');
  return '<div class="vt"><h3>Move still to come today</h3><div class="vrs">' + rings + '</div><p>Share of the day’s expected move (±' + num(c.em_pct, 2) + '%) left at each hour: it decays with the square root of the time left. The week’s range is <b>±' +
    num(c.week_pct, 2) + '%</b> (five sessions).</p></div>';
}
function zweig(z) {
  if (!ok(z)) return '<div class="vt"><h3>Zweig breadth thrust</h3>' + why(z) + '</div>';
  const tone = z.word === 'Thrust' ? 'up' : z.word === 'Washed out' ? 'dn' : z.word === 'Recovering' ? 'wn' : 'mu';
  return '<div class="vt"><h3>Zweig breadth thrust</h3><div class="vsg">' + ring(z.ema10, tone, num(z.ema10 * 100, 1) + '%', '10-day average of the advancing share', [0.4, 0.615]) +
    '<div><p><span class="bdg ' + (tone === 'mu' ? 'mu' : tone) + '">' + esc(z.word) + '</span></p><p>' + (z.fired ? 'Fired ' + esc(z.fired) + ', ' + z.since + ' sessions ago.' : 'No thrust in the sessions counted.') +
    '</p><p class="mu">' + num(z.n, 0) + ' sessions of the roster’s advancers and decliners, through ' + esc(z.as_of) + '. A thrust is the average climbing from under 40% to over 61.5% within 10 sessions.</p></div></div></div>';
}
function straddle(z) {
  if (!ok(z)) return '<div class="vt"><h3>Straddle: rich or cheap</h3>' + why(z) + '</div>';
  const tone = /RICH/.test(z.verdict) ? 'dn' : /CHEAP/.test(z.verdict) ? 'up' : 'mu';
  return '<div class="vt"><h3>Straddle: rich or cheap</h3><div class="vsg">' + ring(z.f, tone, num(z.f * 100, 0) + '%', 'of stored sessions it is richer than', [0.3, 0.7]) +
    '<div><p><span class="bdg ' + tone + '">' + esc(z.verdict) + '</span></p><p>The 30-day straddle costs ' + num(z.today_pct, 2) + '% of the price; band ' + num(z.lo * 100, 0) + '% to ' + num(z.hi * 100, 0) + '% over ' + num(z.n, 0) + ' stored sessions.</p>' +
    (isN(z.k) ? '<p class="mu">After ' + z.k + ' similar readings the next 21 sessions stayed inside the expected move ' + num(z.inside_pct, 0) + '% of the time (median ' + num(z.median_ratio, 2) + ' times it).</p>' : '') + '</div></div></div>';
}
function regime(r) {
  if (!ok(r)) return '<div class="vt"><h3>Intraday regime</h3>' + why(r) + '</div>';
  const h = r.hold, tone = {Pin: 'mu', Grind: 'up', Hostile: 'dn', Transition: 'wn'}[r.word] || 'mu';
  const rows = ok(h) ? h.rows.map(x => '<tr><th scope="row">' + (x.minutes === 'close' ? 'At the close' : '+' + x.minutes + ' min') + '</th><td class="r">' + num(x.hold * 100, 0) + '%</td><td class="r">' + num(x.lo * 100, 0) + '–' + num(x.hi * 100, 0) +
    '%</td><td class="r">' + x.n + (x.low_sample ? ' <small>few</small>' : '') + '</td></tr>').join('') : '';
  return '<div class="vt"><h3>Intraday regime</h3><p><span class="bdg ' + tone + '">' + esc(r.word) + '</span> <span class="mu">minute ' + r.minute + ' of 390</span></p>' +
    (rows ? '<p class="mu">Sessions that read ' + esc(r.word) + ' at minute ' + r.read + ', and how many were still ' + esc(r.word) + ' later.</p><div class="tw"><table class="t"><thead><tr><th>Later</th><th class="r">Share</th><th class="r">90% band</th><th class="r">Sessions</th></tr></thead><tbody>' + rows + '</tbody></table></div>' : why(h)) + '</div>';
}
function market(d) {
  const box = el('m-vendor'), v = d && d.vendor;
  if (!box) return;
  if (!v) { box.hidden = true; return; }
  box.innerHTML = '<div class="shd"><div class="sht"><p class="kick">Measured on this desk’s own history</p><h2 id="h-m-vendor">Move, breadth and regime</h2></div><span class="pv">as of ' + esc(v.as_of) + '</span></div>' +
    '<div class="card"><div class="vg">' + emp(v.emp) + clock(v.clock) + zweig(v.zweig) + straddle(v.straddle) + regime(v.regime) + '</div></div>';
  box.hidden = false;
}

function all(d) { drawers(d); market(d); }
window.MDVX = {card, drawer, market};
D.addEventListener('md:edition', e => all(e.detail));
if (M.ed) all(M.ed);
})();
