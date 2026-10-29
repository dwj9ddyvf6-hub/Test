/* Master Desk terminal: the market strip (positioning, range, day type, fear, SPX/NQ) above the board, and each listed
   long's options drawer ("Express it") inside its open card. Every number comes from the edition's strip and options
   blocks (desk/terminal/strip.py); nothing is recomputed. A block without data says No read and shows its reason. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id);
if (!M) return;
const esc = M.esc, isN = M.isN, num = M.num;
const P = (v, d) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), d == null ? 1 : d) + '%' : '—';
const U = v => isN(v) ? '$' + num(v, 2) : '—';
const ok = b => b && (b.status === 'ok' || b.status === 'stale');
const why = b => b && b.reason ? b.reason : '';
const TONE = {Dampening: 'up', Amplifying: 'dn', Calm: 'up', Normal: 'mu', Stressed: 'dn', Pin: 'mu', Grind: 'mu',
  Volatile: 'dn', Yes: 'dn', No: 'up', 'both up': 'up', 'both down': 'dn', split: 'wn', quiet: 'mu'};

function tile(label, word, line, b, method) {
  const t = word ? TONE[word] || 'mu' : 'mu', tip = [method, b && b.as_of ? 'as of ' + b.as_of : '', b && b.status === 'stale' ? 'stale' : '',
    why(b)].filter(Boolean).join(' · ');
  return '<div class="sx" title="' + esc(tip) + '" tabindex="0"><span class="sl">' + esc(label) + '</span><b class="sw ' + t + '">' +
    esc(word || 'No read') + '</b><span class="sd">' + esc(line || why(b)) + '</span></div>';
}

function strip(d) {
  const host = el('strip'), s = d && d.strip;
  if (!host) return;
  if (!s || s.error) { host.hidden = true; return; }
  const g = (s.gex || {}).SPY, mv = s.move, f = s.fear, a = s.agree, dy = s.day, out = [];
  if (ok(g)) {
    const flip = isN(g.flip_sigma) ? 'flip ' + num(Math.abs(g.flip_sigma), 1) + 'σ ' + (g.flip_sigma < 0 ? 'below' : 'above')
      : 'no flip near';
    const sq = g.source && !isN(g.flip_sigma) && !isN(g.call_wall_pct) && !isN(g.put_wall_pct);   // SqueezeMetrics' SPX read: no strikes, so no flip or walls
    out.push(tile('SPY gamma', g.word, sq ? (g.label || 'SPX gamma · ' + g.source) + (isN(g.dix) ? ' · DIX ' + num(g.dix * 100, 1) + '%' : '')
      : flip + ' · walls ' + P(g.put_wall_pct) + ' and ' + P(g.call_wall_pct), g,
      g.method + ' · ' + (g.net < 0 ? '−' : '') + '$' + num(Math.abs(g.net), 1) + 'B per 1% move'));
  } else out.push(tile('SPY gamma', null, '', g));
  out.push(ok(mv) ? tile('Range', '±' + num(mv.em_pct, 2) + '%', (isN(mv.em_inside_pct) ? 'about ' + num(mv.em_inside_pct, 0) + '% of days stay inside' : 'one-day move from the VIX') +
    (isN(mv.band68_pct) ? ' · 68% band ±' + num(mv.band68_pct, 2) + '%' : '') +
    (isN(mv.funded_pct) ? ' · ' + num(mv.funded_pct / mv.em_pct * 100, 0) + '% funded by now' : ''), mv, mv.method) : tile('Range', null, '', mv));
  out.push(ok(dy) ? tile('Day', dy.word, 'gap ' + P(dy.gap_pct, 2) + ' · range ' + num(dy.range_pct, 2) + '%', dy, dy.method)
    : tile('Day', null, '', dy));
  out.push(ok(f) ? tile('Fear day', f.fear_day ? 'Yes' : 'No', (f.fear_day ? 'SPY ' + (f.fear_why || []).map(w => ({spy_drop: 'fell 1% or more', below_50d: 'under its 50-day', vol_spike: 'volatility spike', vix_spike: 'VIX spike'}[w] || w)).join(' · ') :
    'SPY above its 50-day, no 1% drop') + (f.as_of_session ? ' · ' + f.as_of_session : '') + ' · VIX ' + String(f.stress || '').toLowerCase() +
    (isN(f.vix_vs_forecast) ? ' (' + num(f.vix_vs_forecast, 2) + '× forecast)' : ''), f, f.method) : tile('Fear day', null, '', f));
  out.push(ok(a) ? tile('SPX / NQ', a.word, 'SPY ' + P(a.spy_pct, 2) + ' · QQQ ' + P(a.qqq_pct, 2), a, 'today against the last close')
    : tile('SPX / NQ', null, '', a));
  host.innerHTML = out.join('');
  host.hidden = false;
}

function drawer(o) {
  if (!o) return '';
  if (o.status !== 'ok') return '<details class="xp"><summary>Express it</summary><p class="mu">' + esc(why(o) || 'No options read') + '</p></details>';
  const facts = [['IV 30d', isN(o.iv30) ? num(o.iv30 * 100, 0) + '%' : '—'],
    ['IV rank', isN(o.iv_rank) ? num(o.iv_rank * 100, 0) + '%' : '—'],
    ['IV / RV20', isN(o.iv_rv) ? num(o.iv_rv, 2) + '×' : '—'],
    ['Put/call OI', isN(o.pc_oi) ? num(o.pc_oi, 2) + (isN(o.pc_oi_change) ? ' (' + (o.pc_oi_change >= 0 ? '+' : '−') + num(Math.abs(o.pc_oi_change), 2) + ')' : '') : '—'],
    ['Spread', isN(o.spread_pct) ? num(o.spread_pct, 1) + '%' : '—']];
  const rows = (o.express || []).map(x => '<tr><th scope="row">' + esc(x.kind) + '<small>' + x.legs.map(l => esc(l[0]) + ' ' + num(l[1], 2)).join(' / ') +
    '</small></th><td class="r">' + U(x.debit) + '</td><td class="r">' + U(x.max_gain) +
    '</td><td class="r">' + U(x.breakeven) + '</td><td class="r">' + (x.touch_t1 && isN(x.touch_t1.rate) ? num(x.touch_t1.rate * 100, 0) + '% <small>of ' + x.touch_t1.n + '</small>' : '<small>not measured</small>') + '</td></tr>').join('');
  return '<details class="xp"><summary>Express it' + (o.t1_beyond_2em ? ' <span class="bdg wn">Target past 2 expected moves (81% band)</span>' : '') +
    '</summary><dl class="xf">' + facts.map(f => '<div><dt>' + f[0] + '</dt><dd>' + esc(f[1]) + '</dd></div>').join('') + '</dl>' +
    (rows ? '<div class="tw"><table class="t xt"><caption>' + esc((o.expiry ? 'Expiry ' + o.expiry + ' · ' : '') +
      'per share · the debit is the most it can lose · reached T1 before: the share of this name\'s own past windows of the same length that touched that distance') + '</caption><thead><tr><th>Structure</th><th class="r">Debit</th>' +
      '<th class="r">Max gain</th><th class="r">Breakeven</th><th class="r">Reached T1 before</th></tr></thead><tbody>' +
      rows + '</tbody></table></div>' : '<p class="mu">' + esc(o.express_reason || '') + '</p>') + '</details>';
}

function cards(d) {
  (d && d.setups || []).forEach(s => {
    const c = M.cards[s.id];
    if (!c || !c.db) return;
    const old = c.db.querySelector('.xp'), h = drawer(s.options);
    if (old) old.remove();
    if (h) c.db.insertAdjacentHTML('afterbegin', h);
  });
}

function all(d) { strip(d); cards(d); }
D.addEventListener('md:edition', e => all(e.detail));
if (M.ed) all(M.ed);
})();
