/* Master Desk terminal: the market strip (positioning, range, day type, fear, SPX/NQ) above the board, and each listed
   long's options drawer ("Express it") inside its open card. Every number comes from the edition's strip and options
   blocks (desk/terminal/strip.py); nothing is recomputed. A block without data says No read and shows its reason. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id);
const PG = (t, f) => (window.MD && window.MD.guard ? window.MD.guard(t, f) : f());   // app.js's panel guard
if (!M) return;
const esc = M.esc, isN = M.isN, num = M.num;
const P = (v, d) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), d == null ? 1 : d) + '%' : '—';
const U = v => isN(v) ? '$' + num(v, 2) : '—';
const ok = b => b && (b.status === 'ok' || b.status === 'stale');
const why = b => b && b.reason ? b.reason : '';
const TONE = {Dampening: 'up', Amplifying: 'dn', Calm: 'up', Normal: 'mu', Stressed: 'dn', Pin: 'mu', Grind: 'mu',
  Volatile: 'dn', Yes: 'dn', No: 'up', 'both up': 'up', 'both down': 'dn', split: 'wn', quiet: 'mu'};

const V = window.MDG || {};
function tile(label, word, line, b, method, vis) {
  const t = word ? TONE[word] || 'mu' : 'mu', tip = [method, b && b.as_of ? 'as of ' + b.as_of : '', b && b.status === 'stale' ? 'stale' : '',
    why(b)].filter(Boolean).join(' · ');
  return '<div class="sx kc" title="' + esc(tip) + '" tabindex="0"><span class="sl">' + esc(label) + '</span><b class="sw ' + t + '">' +
    esc(word || 'No read') + '</b>' + (word && vis ? '<div class="sg">' + vis + '</div>' : '') + '<span class="sd">' + esc(line || why(b)) + '</span></div>';
}

// each tile: the headline word, one instrument drawn from its numbers (gauges.js), one short line
function strip(d) {
  const host = el('strip'), s = d && d.strip;
  if (!host) return;
  if (!s || s.error) { host.hidden = true; return; }
  const g = (s.gex || {}).SPY, mv = s.move, f = s.fear, a = s.agree, dy = s.day, out = [];
  const em = ok(mv) ? mv.em_pct : null, spy = ok(a) ? a.spy_pct : null, A = V.arc || (() => '');
  const pill = w => ({up: 'g', dn: 'r', wn: 'y'})[TONE[w]] || 'n';
  if (ok(g)) {
    const sq = g.source && !isN(g.flip_sigma) && !isN(g.call_wall_pct) && !isN(g.put_wall_pct);   // SqueezeMetrics' SPX read: no strikes, so no flip or walls
    out.push(tile('SPY gamma', g.word, (g.stale_line ? g.stale_line + ' · ' : '') + (sq ? (g.label || 'SPX gamma · ' + g.source) + (isN(g.dix) ? ' · DIX ' + num(g.dix * 100, 1) + '%' : '')
      : 'per 1% move, dealer gamma'), g,
      g.method + (isN(g.flip_sigma) ? ' · flip ' + num(Math.abs(g.flip_sigma), 1) + 'σ ' + (g.flip_sigma < 0 ? 'below' : 'above') : ''), (isN(g.net) ? A([[-10, 'r', 'Amplifying: dealers short gamma'], [0, 'o', 'Amplifying'], [10, 'gl', 'Dampening'], [20, 'g', 'Dampening: dealers long gamma']], g.net, -20, 20,
        (g.net < 0 ? '−' : '+') + '$' + num(Math.abs(g.net), 1) + 'B', g.stale_line ? 'STALE' : g.net < 0 ? 'SHORT GAMMA' : 'LONG GAMMA', g.stale_line ? 'n' : pill(g.word), [[-20, '−20'], [0, '0'], [20, '+20']]) : '') + (sq ? '' : V.gamma && V.gamma(g))));
  } else out.push(tile('SPY gamma', null, '', g));
  out.push(ok(mv) ? tile('Range', '±' + num(mv.em_pct, 2) + '%', (isN(spy) ? 'SPY ' + P(spy, 2) + ' today · ' : '') + (isN(mv.em_inside_pct) ? num(mv.em_inside_pct, 0) + '% of days' + (mv.em_inside_since ? ' since ' + mv.em_inside_since : '') + ' stay inside' : 'one-day move from the VIX'),
    mv, mv.method + (isN(mv.funded_pct) ? ' · ' + num(mv.funded_pct / mv.em_pct * 100, 0) + '% funded by now' : ''), (V.range ? V.range(mv, spy) : '') + (isN(spy) ? '<span class="kc-pill ' + (Math.abs(spy) > mv.em_pct ? 'r' : 'g') + '">' + (Math.abs(spy) > mv.em_pct ? 'OUTSIDE' : 'INSIDE') + '</span>' : '')) : tile('Range', null, '', mv));
  out.push(ok(dy) ? tile('Day', dy.word, 'range so far over the expected move', dy, dy.method, (isN(em) && isN(dy.range_pct) ? A([[0.5, 'b', 'Pin'], [1, 'g', 'Grind'], [1.5, 'y', 'Active'], [2.5, 'r', 'Volatile']], dy.range_pct / em, 0, 2.5,
      num(dy.range_pct / em, 2) + '×', dy.range_pct > em ? 'PAST THE MOVE' : 'INSIDE THE MOVE', pill(dy.word), [[0, '0'], [1, '1×'], [2.5, '2.5×']]) : '') + (V.day && V.day(dy, em)))
    : tile('Day', null, '', dy));
  out.push(ok(f) ? tile('Picker fear day', f.fear_day ? 'Yes' : 'No', [(f.fear_words || []).join(' · '), f.spy_day, f.qqq_day].filter(Boolean).join(' · ') + ' · VIX against its forecast' + (f.as_of_session ? ' · ' + window.MD.et(f.as_of_session).md + ' close' : '') + (f.as_of && f.as_of !== f.as_of_session ? ' · VIX of ' + window.MD.et(f.as_of).md : '')   /* the VIX's own close, never the session's label (audit 5 M4) */, f, f.method + (f.as_of_session ? ' · ' + f.as_of_session : ''), (isN(f.vix_vs_forecast) ? A([[0.9, 'g', 'VIX under its forecast'], [1.1, 'y', 'VIX near its forecast'], [1.5, 'o', 'VIX over its forecast'], [2, 'r', 'VIX far over its forecast']], f.vix_vs_forecast, 0.5, 2,
      num(f.vix_vs_forecast, 2) + '×', 'VIX ' + String(f.stress || '').toUpperCase(), ({Stressed: 'r', Normal: 'y', Calm: 'g'})[f.stress] || 'n', [[0.5, '.5×'], [1, '1×'], [2, '2×']]) : '') + (V.fear && V.fear(f))) : tile('Picker fear day', null, '', f));
  out.push(ok(a) ? tile('SPX / NQ', a.word, 'SPY ' + P(a.spy_pct, 2) + ' · QQQ ' + P(a.qqq_pct, 2) + ' from the last close', a, '5-minute paths from the prior close', V.paths && V.paths(pulse && pulse.lines, a))
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

// the SPX / NQ tile's session paths: pulse.json (Market Pulse's 1D series), fetched once per edition
let pulse = null, last = null;
function all(d) {
  last = d; PG('strip', () => strip(last)); cards(d);
  fetch('pulse.json', {cache: 'no-cache'}).then(r => r.ok ? r.json() : null).then(p => { if (p && p.lines) { pulse = p; PG('strip', () => strip(last)); } }).catch(() => {});
}
D.addEventListener('md:edition', e => all(e.detail));
if (M.ed) all(M.ed);
})();
