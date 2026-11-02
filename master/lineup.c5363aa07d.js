/* Master Desk terminal, the desk lineup (Hub tab): twelve tools, Gap-Fill, Correlation Web and the Chart Read Engine,
   from lineup.json (desk/terminal/lineup.py) and the roster's reads. Stated readings only. Ported from master-desk
   8298bec engines/ui/lineup_ui.js and galath-desk-terminal 37706a7 / acfc8f8. */
(() => {
const D = document, el = id => D.getElementById(id), M = window.MD;
if (!M || !el('h-lineup')) return;
const esc = M.esc, isN = v => typeof v === 'number' && isFinite(v);
const P = (v, d = 1) => isN(v) ? (+v).toFixed(d) + '%' : '—';
const S = (v, d = 1) => isN(v) ? (v > 0 ? '+' : '') + (+v).toFixed(d) + '%' : '—';
const N = v => isN(v) ? (+v).toLocaleString('en-US') : '—';
const X = v => isN(v) ? String(v) : '—';
const dd = s => { if (!s) return '—'; const d = new Date(s + 'T12:00:00Z'); return isNaN(d) ? esc(s) : d.toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric', timeZone: 'UTC'}); };
const NC = (n, p) => p == null ? N(n) : N(n) + ' <span class="lu-mu">' + P(p) + '</span>';
const T = (h, rows, num) => '<div class="lu-tw"><table class="lu-t"><thead><tr>' + h.map((x, i) => '<th' + (num && num.includes(i) ? ' class="r"' : '') + '>' + x + '</th>').join('') +
  '</tr></thead><tbody>' + rows.map(r => '<tr>' + r.map((c, i) => '<td' + (num && num.includes(i) ? ' class="r"' : '') + '>' + (i ? c : '<b>' + c + '</b>') + '</td>').join('') + '</tr>').join('') + '</tbody></table></div>';
const tiles = a => '<div class="lu-tiles">' + a.map(([l, v, s]) => '<div class="lu-tile"><div class="lu-l">' + esc(l) + '</div><div class="lu-v">' + v + '</div>' + (s ? '<div class="lu-mu">' + s + '</div>' : '') + '</div>').join('') + '</div>';
const H3 = t => '<h3 class="lu-h">' + esc(t) + '</h3>';
const none = t => '<p class="lu-mu">' + esc(t) + '</p>';
const TOOLS = [['or', 'Opening Range'], ['em', 'Expected Move'], ['cb', 'Corrected Band'], ['sc', 'Strat Combos'], ['rw', 'Reversal Wire'],
  ['fd', 'Fear Days'], ['pn', 'Pullback Norm'], ['ch', 'Changes'], ['scr', 'Screener'], ['wl', 'Watchlist'], ['rp', 'Report'], ['po', 'Payoff'], ['rc', 'Receipts']];
const st = {k: 'or', f: {min: '', max: '', m63: '', hi: '', vx: '', v200: 'any', lab: 'any', sort: 'dvol_m', q: ''}, lim: 40, rq: '', wl: [], po: null};
try { st.wl = JSON.parse(localStorage.getItem('md_watch') || '[]').filter(x => typeof x === 'string').slice(0, 40); } catch (e) { st.wl = []; }
let d = null, ix = {}, pend = false;   // pend: lineup.json is the placeholder before the job's first run (lineup.placeholder)

function get(u) { return fetch(u, {cache: 'no-cache'}).then(r => r.ok ? r.json() : null).catch(() => null); }

// ---- the tools ----------------------------------------------------------------------------------------------------------
const tool = {
  or() {
    const o = d.opening_range || {}, W = o.windows || [], h = W[W.length - 1];
    if (!h || !o.sessions) return none('No complete sessions of 5-minute bars on file yet.');
    return '<p class="lu-sub">' + N(o.sessions) + ' sessions of SPY, QQQ and IWM, ' + dd(o.first) + ' to ' + dd(o.last) + '.</p>' +
      tiles([['First hour broke a side', P(h.broke_any_pct), N(h.broke_any) + ' of ' + N(h.days) + ' fund-days'], ['Both sides', P(h.both_pct), N(h.both) + ' fund-days'],
        ['Ran half a range past', P(h.extension[0].pct_of_breaks, 0), 'of breaks'], ['Ran a full range past', P(h.extension[1].pct_of_breaks, 0), 'of breaks']]) +
      H3('By opening window') + T(['Window', 'Days', 'Up only', 'Down only', 'Both', 'Neither', '½ range+', '1 range+', '1½ range+'],
        W.map(w => [esc(w.label), N(w.days), NC(w.up_only, w.up_only_pct), NC(w.down_only, w.down_only_pct), NC(w.both, w.both_pct), NC(w.neither, w.neither_pct),
          P(w.extension[0].pct_of_breaks, 0), P(w.extension[1].pct_of_breaks, 0), P(w.extension[2].pct_of_breaks, 0)]), [1, 2, 3, 4, 5, 6, 7, 8]) +
      H3('Latest session') + T(['Fund', 'Session', 'First-hour high', 'Low', 'Range', 'After'], Object.entries(o.latest || {}).map(([s, r]) =>
        [esc(s), dd(r.session), X(r.high), X(r.low), P(r.range_pct, 2), esc(r.after)]), [2, 3, 4]);
  },
  em() {
    const e = d.expected_move || {}, Mp = e.maps || [];
    if (!Mp.length) return none('No VIX close for the latest session on file.');
    return '<p class="lu-sub">Priced move for ' + dd(e.next_session) + ', around each close.</p>' +
      tiles(Mp.map(m => [m.name, '±' + m.move, m.lower + ' – ' + m.upper + ' · VIX ' + m.vix + ' ' + esc(m.regime)])) +
      T(['Fund', 'Close', 'Move', 'Lower', 'Lower half', 'Upper half', 'Upper', 'Week'], Mp.map(m => [esc(m.name), X(m.close), '±' + m.move + ' (' + (+m.move_pct).toFixed(2) + '%)',
        X(m.lower), X(m.lower_half), X(m.upper_half), X(m.upper), '±' + m.week_move + ' · ' + m.week_lower + ' – ' + m.week_upper]), [1, 2, 3, 4, 5, 6]) +
      H3(Mp[0].name + ' funding curve') + T(['Minutes in', 'Points', 'Lower', 'Upper'], Mp[0].curve.map(c => [X(c.minutes), X(c.points), X(c.lower), X(c.upper)]), [0, 1, 2, 3]) +
      H3('Close inside the priced move') + T(['Fund', 'Sessions', 'Inside', 'Last 250', 'Recent'], Object.entries(e.record || {}).map(([s, r]) =>
        [esc(s), N(r.sessions), P(r.inside_pct), P(r.last250_pct), (r.recent || []).map(x => '<span class="lu-pip ' + (x.inside ? 'up' : 'dn') + '" title="' + esc(x.session + ': ' + x.close + ' vs ' + x.lower + ' – ' + x.upper) + '">' + (x.inside ? '✓' : '✗') + '</span>').join('')]), [1, 2, 3]);
  },
  cb() {
    const c = d.corrected_band || {}, L = ['50', '68', '81', '95'], live = c.live || [], R = c.record || {};
    if (!live.length) return none('SPY and QQQ need 300 sessions of daily bars.');
    const g = Object.entries(R.graded || {});
    return T(['Fund', 'Horizon', 'Close', 'Movement (annual)', '50%', '68%', '81%', '95%'], live.map(x => [esc(x.symbol), x.h + 'd', X(x.close), P(x.vol_pct), ...L.map(k => x.bands[k][0] + ' – ' + x.bands[k][1])]), [2, 3]) +
      '<p class="lu-mu">Base ' + dd(live[0].base_session) + ' · VIX ' + X(live[0].vix) + ' · VIX3M ' + X(live[0].vix3m) + (live[0].backwardation ? ' · 95% band widened 25%' : '') + '</p>' +
      H3('Measured coverage') + T(['Fund', 'Horizon', 'Days', '50%', '68%', '81%', '95%'], Object.entries(c.history || {}).flatMap(([s, hh]) => Object.entries(hh).map(([h, r]) =>
        [esc(s), h + 'd', N(r.days), ...L.map(k => P(r.coverage[k], 0) + ' <span class="lu-mu">' + P(r.last250[k], 0) + '</span>')])), [2, 3, 4, 5, 6]) +
      H3('Ledger') + '<p class="lu-mu">' + N(R.issued) + ' bands since ' + dd(R.first_base) + (g.length ? ' · ' + g.map(([h, x]) => h + 'd: ' + x.graded + ' graded, 68% held ' + P(x.coverage['68'], 0)).join(' · ') : ' · 0 graded') + '</p>';
  },
  sc() {
    const s = d.strat_combos || {};
    return '<p class="lu-sub">' + N(s.names) + ' names · ' + dd(s.session) + ' · 1 inside · 2U prior high · 2D prior low · 3 outside</p><div class="lu-pills">' +
      (s.pairs || []).slice(0, 10).map(p => '<span class="lu-pill" title="' + esc(p.sample.join(', ')) + '">' + esc(p.seq) + ' · ' + p.count + '</span>').join('') + '</div>' +
      H3('Completed today') + T(['Pattern', 'Names', 'Some of them'], (s.completed || []).map(c => [esc(c.pattern), N(c.count), esc(c.names.slice(0, 12).join(', '))]), [1]) +
      H3('Three-bar runs') + T(['Labels', 'Names', 'Samples'], (s.triples || []).slice(0, 8).map(c => [esc(c.seq), N(c.count), esc(c.sample.slice(0, 6).join(', '))]), [1]);
  },
  rw() {
    const w = d.reversal_wire || {};
    return T(['Session', 'Label', 'Names', 'Latest session'], (w.entries || []).map(e => [dd(e.date), esc(e.label), N(e.count), esc(e.names.slice(0, 24).join(', ') + (e.names.length > 24 ? ' …' : ''))]), [2]);
  },
  fd() {
    const f = d.fear_days || {}, l = f.latest || {};
    if (f.state !== 'ok') return none(f.reason || 'No reading.');
    const a5 = (f.after || [])[1] || {};
    return '<p class="lu-sub">A fear day: SPY fell more than 1.5%, the VIX rose more than 15%, the VIX closed at 25+, or at 20+ on a down day for SPY or QQQ.</p>' +
      tiles([['Latest session', l.fear ? 'Fear day' : 'Not a fear day', dd(l.date) + ' · SPY ' + S(l.spy_pct, 2) + ' · VIX ' + X(l.vix)],
        ['Fear days', N(f.fear_days), P(f.fear_pct, 0) + ' of ' + N(f.sessions) + ' since ' + dd(f.first)], ['SPY 5 sessions after', S(a5.median_pct, 2), 'median · ' + P(a5.positive_pct, 0) + ' up · n ' + N(a5.n)]]) +
      H3('Rules that fired') + T(['Rule', 'Days'], Object.entries(f.arm_counts || {}).map(([k, v]) => [esc(k), N(v)]), [1]) +
      H3('SPY after') + T(['After', 'Days', 'Median', 'Up'], (f.after || []).map(a => [a.h + 'd', N(a.n), S(a.median_pct, 2), P(a.positive_pct, 0)]), [1, 2, 3]) +
      H3('Recent fear days') + T(['Date', 'SPY', 'VIX', 'Rules'], (f.recent || []).map(r => [dd(r.date), S(r.spy_pct, 2), X(r.vix), esc(r.arms.join('; '))]), [1, 2]);
  },
  pn() {
    const p = d.pullback_norm || {}, b = p.buckets || [];
    return '<p class="lu-sub">Depth under the 63-session high in its own median true ranges, as a percentile of its own history: 0 shallowest, 100 deepest.</p>' +
      tiles([['Names measured', N(p.measured), '$2M+ a day'], ['Above the 200-day', N(p.uptrend), ''], ['Unusually deep (95+)', N((b[4] || {}).uptrend), 'of those above']]) +
      T(['Depth', 'Above 200-day', 'All'], b.map(x => [esc(x.label), N(x.uptrend), N(x.all)]), [1, 2]) +
      ((p.desk || []).length ? H3('Roster reads, deepest first') + T(['Name', 'Percentile', 'vs 200-day', 'Below high'], p.desk.slice(0, 25).map(r => [esc(r.s), X(r.pctile), S(r.vs200), P(r.below_high)]), [1, 2, 3]) : '');
  },
  ch() {
    const c = d.changes || {};
    return '<p class="lu-sub">' + dd(c.session) + ' · names trading $2M+ a day</p>' + ((c.flips || []).length ? '<div class="lu-pills">' + c.flips.map(x => '<span class="lu-pill wn">' + esc(x) + '</span>').join('') + '</div>' : '') +
      T(['Change', 'Names', 'Which'], (c.rows || []).map(r => [esc(r.label), N(r.count), esc(r.names.slice(0, 20).join(', ') + (r.names.length > 20 ? ' …' : ''))]), [1]);
  },
  scr() {
    const f = st.f, inp = (k, ph) => '<input class="lu-in" data-f="' + k + '" inputmode="decimal" placeholder="' + ph + '" value="' + esc(f[k]) + '" aria-label="' + ph + '">',
      sel = (k, o) => '<select class="lu-in" data-f="' + k + '" aria-label="' + k + '">' + o.map(([v, l]) => '<option value="' + v + '"' + (f[k] === v ? ' selected' : '') + '>' + l + '</option>').join('') + '</select>';
    return '<div class="lu-form">' + inp('min', 'Min price') + inp('max', 'Max price') + inp('m63', '3-mo ≥ %') + inp('hi', 'Within % of high') + inp('vx', 'Volume × ≥') +
      sel('v200', [['any', '200-day: any'], ['above', 'Above 200-day'], ['below', 'Below 200-day']]) + sel('lab', [['any', 'Label: any'], ['1', '1'], ['2U', '2U'], ['2D', '2D'], ['3', '3']]) +
      sel('sort', [['dvol_m', 'Sort: $ volume'], ['d63', 'Sort: 3-mo'], ['d126', 'Sort: 6-mo'], ['d21', 'Sort: 1-mo'], ['volx', 'Sort: volume ×'], ['s', 'Sort: name']]) +
      '<input class="lu-in" data-f="q" type="search" placeholder="Symbol" autocapitalize="characters" value="' + esc(f.q) + '" aria-label="Symbol"></div><div id="lu-scr"></div>';
  },
  wl() {
    return '<div class="lu-form"><input class="lu-in" id="lu-wlq" placeholder="Add symbol" autocapitalize="characters" aria-label="Add symbol"><button class="lu-b" data-a="wladd">Add</button>' +
      (st.wl.length ? '' : ['SPY', 'QQQ', 'AAPL'].map(s => '<button class="lu-b" data-a="wl1" data-s="' + s + '">' + s + '</button>').join('')) + '</div>' +
      (st.wl.length ? T(['Name', 'Close', 'Day', '3 mo', 'vs 200-day', 'Volume ×', 'Labels', ''], st.wl.map(s => { const r = ix[s], x = '<button class="lu-x" data-a="wlx" data-s="' + esc(s) + '" aria-label="Remove ' + esc(s) + '">×</button>';
        return r ? [esc(s), X(r.close), S(r.d1), S(r.d63, 0), S(r.vs200, 0), r.volx == null ? '—' : r.volx + '×', esc(r.strat5), x] : [esc(s), 'not on the roster', '', '', '', '', '', x]; }), [1, 2, 3, 4, 5]) : '');
  },
  rp() { return '<div class="lu-form"><input class="lu-in" id="lu-rq" placeholder="Symbol" autocapitalize="characters" value="' + esc(st.rq) + '" aria-label="Symbol"></div><div id="lu-rp"></div>'; },
  po() {
    if (!st.po) { const sp = (ix.SPY || {}).close || 100; st.po = {spot: sp, legs: [{k: 'call', s: 'long', K: Math.round(sp), p: +(sp * 0.015).toFixed(2), q: 1}]}; }
    return '<div class="lu-form"><label class="lu-mu">Price <input class="lu-in" id="lu-spot" inputmode="decimal" value="' + st.po.spot + '"></label><button class="lu-b" data-a="poadd">Add a leg</button></div><div id="lu-legs"></div><div id="lu-pay"></div>';
  },
  rc() {
    return T(['Tool', 'Built from', 'As of', 'Coverage', ''], (d.receipts || []).map(r => [esc(r.tool), esc(r.source), dd(r.as_of), esc(r.coverage), '<span class="lu-pill ' + (r.complete ? 'up' : 'wn') + '">' + (r.complete ? 'complete' : 'partial') + '</span>']));
  }
};

function rows() {
  const f = st.f, n = v => v === '' ? null : +v, mn = n(f.min), mx = n(f.max), m63 = n(f.m63), hi = n(f.hi), vx = n(f.vx), q = f.q.trim().toUpperCase();
  const R = Object.values(ix).filter(r => (mn == null || r.close >= mn) && (mx == null || r.close <= mx) && (m63 == null || (r.d63 != null && r.d63 >= m63)) &&
    (hi == null || (r.below_high != null && r.below_high <= hi)) && (vx == null || (r.volx != null && r.volx >= vx)) &&
    (f.v200 === 'any' || (r.vs200 != null && (f.v200 === 'above' ? r.vs200 > 0 : r.vs200 < 0))) && (f.lab === 'any' || String(r.strat5).split('-').pop() === f.lab) && (!q || r.s.includes(q)));
  const k = f.sort;
  return R.sort((a, b) => k === 's' ? (a.s < b.s ? -1 : 1) : ((b[k] == null ? -1e18 : b[k]) - (a[k] == null ? -1e18 : a[k])));
}
function scr() {
  const e = el('lu-scr'); if (!e) return;
  const R = rows();
  e.innerHTML = '<p class="lu-mu">' + N(R.length) + ' match</p>' + T(['Name', 'Close', 'Day', '3 mo', '6 mo', 'Below high', 'vs 200-day', 'RSI', 'Volume ×', '$M a day', 'Label'],
    R.slice(0, st.lim).map(r => [esc(r.s), X(r.close), S(r.d1), S(r.d63, 0), S(r.d126, 0), P(r.below_high, 0), S(r.vs200, 0), X(r.rsi), r.volx == null ? '—' : r.volx + '×', X(r.dvol_m), esc(String(r.strat5).split('-').pop())]),
    [1, 2, 3, 4, 5, 6, 7, 8, 9]) + (R.length > st.lim ? '<button class="lu-b" data-a="more">Show more</button>' : '');
}
function report() {
  const e = el('lu-rp'); if (!e) return;
  const s = st.rq.trim().toUpperCase();
  if (!s) { e.innerHTML = ''; return; }
  const r = ix[s], sec = [];
  sec.push(['Price and trend', r ? 'Close ' + r.close + ' · day ' + S(r.d1) + ' · 1 mo ' + S(r.d21) + ' · 3 mo ' + S(r.d63) + ' · 6 mo ' + S(r.d126) + ' · ' + P(r.below_high) + ' under its 52-week high · ' + S(r.vs50) + ' vs 50-day · ' + S(r.vs200) + ' vs 200-day · RSI ' + X(r.rsi) : null]);
  const cp = ((d.strat_combos || {}).completed || []).filter(c => c.names.includes(s)).map(c => c.pattern);
  sec.push(['Strat labels', r ? esc(r.strat5) + (cp.length ? ' · completed ' + esc(cp.join('; ')) : '') : null]);
  sec.push(['Volume', r && r.volx != null ? r.volx + '× its 50-day average · $' + X(r.dvol_m) + 'M a day' : null]);
  sec.push(['Pullback depth', r && r.depth_pctile != null ? r.depth_pctile + 'th percentile of its own history' : null]);
  const tw = ((d.correlation_web || {}).pairs || []).filter(p => p.a === s || p.b === s).map(p => esc(p.a === s ? p.b : p.a) + ' ' + p.r);
  sec.push(['Moves with', tw.length ? tw.join(', ') : null]);
  const m = ((d.expected_move || {}).maps || []).find(x => x.name === s);
  if (m) sec.push(['Expected move', '±' + m.move + ' (' + m.lower + ' – ' + m.upper + ') · week ±' + m.week_move]);
  const o = ((d.opening_range || {}).latest || {})[s];
  if (o) sec.push(['Opening range', dd(o.session) + ': ' + o.low + ' – ' + o.high + ', ' + esc(o.after)]);
  e.innerHTML = '<p class="lu-sub"><b>' + esc(s) + '</b> · ' + sec.filter(x => x[1]).length + ' of ' + sec.length + ' sections</p>' +
    sec.map(([h, b]) => '<div class="lu-sec"><h4>' + esc(h) + '</h4><p>' + (b || '<span class="lu-mu">Not on record.</span>') + '</p></div>').join('');
}
// ---- Payoff: the morgue's payoff.py arithmetic, in the browser ----------------------------------------------------------
function legs() {
  const e = el('lu-legs'); if (!e) return;
  e.innerHTML = st.po.legs.map((l, i) => '<div class="lu-leg">' +
    '<select class="lu-in" data-i="' + i + '" data-l="s" aria-label="Side"><option' + (l.s === 'long' ? ' selected' : '') + '>long</option><option' + (l.s === 'short' ? ' selected' : '') + '>short</option></select>' +
    '<select class="lu-in" data-i="' + i + '" data-l="k" aria-label="Type"><option' + (l.k === 'call' ? ' selected' : '') + '>call</option><option' + (l.k === 'put' ? ' selected' : '') + '>put</option></select>' +
    '<input class="lu-in" data-i="' + i + '" data-l="K" inputmode="decimal" value="' + l.K + '" aria-label="Strike" title="Strike">' +
    '<input class="lu-in" data-i="' + i + '" data-l="p" inputmode="decimal" value="' + l.p + '" aria-label="Premium" title="Premium">' +
    '<input class="lu-in" data-i="' + i + '" data-l="q" inputmode="numeric" value="' + l.q + '" aria-label="Contracts" title="Contracts">' +
    '<button class="lu-x" data-a="porm" data-i="' + i + '" aria-label="Remove leg">×</button></div>').join('');
}
function pay() {
  const e = el('lu-pay'); if (!e) return;
  const L = st.po.legs.map(l => ({k: l.k, g: l.s === 'long' ? 1 : -1, K: +l.K, p: +l.p || 0, q: +l.q || 0})).filter(l => l.q > 0 && l.K > 0), spot = +st.po.spot;
  if (!L.length || !(spot > 0)) { e.innerHTML = ''; return; }
  const f = S0 => L.reduce((a, l) => a + l.g * l.q * 100 * ((l.k === 'call' ? Math.max(S0 - l.K, 0) : Math.max(l.K - S0, 0)) - l.p), 0);
  const ks = [...new Set([0, ...L.map(l => l.K)])].sort((a, b) => a - b), top = ks[ks.length - 1];
  const slope = L.reduce((a, l) => a + (l.k === 'call' ? l.g * l.q * 100 : 0), 0), atK = ks.map(f);
  const mx = slope > 0 ? 'unlimited' : '$' + Math.round(Math.max(...atK)).toLocaleString('en-US'), mn = slope < 0 ? 'unlimited' : '$' + Math.round(-Math.min(...atK)).toLocaleString('en-US');
  const pts = [...ks.map((k, i) => [k, atK[i]]), [top * 1.5 || 100, f(top * 1.5 || 100)]], be = [];
  for (let i = 1; i < pts.length; i++) { const [x0, y0] = pts[i - 1], [x1, y1] = pts[i]; if (y0 === 0) be.push(x0); else if (y0 * y1 < 0) be.push(x0 - y0 * (x1 - x0) / (y1 - y0)); }
  const lo = Math.max(0.01, Math.min(spot, ...L.map(l => l.K)) * 0.7), hi = Math.max(spot, ...L.map(l => l.K)) * 1.3, n = 160, xs = [], ys = [];
  for (let i = 0; i <= n; i++) { const x = lo + (hi - lo) * i / n; xs.push(x); ys.push(f(x)); }
  const W = 600, Hh = 200, y0 = Math.min(0, ...ys), y1 = Math.max(0, ...ys), sp = y1 - y0 || 1, PX = x => 8 + (W - 60) * (x - lo) / (hi - lo), PY = v => 10 + (Hh - 34) * (y1 - v) / sp;
  const k = v => Math.abs(v) >= 1e3 ? (v / 1e3).toFixed(1) + 'k' : v.toFixed(0);
  e.innerHTML = tiles([['Max gain', mx, ''], ['Max loss', mn, ''], ['Breakevens', [...new Set(be.map(b => b.toFixed(2)))].join(', ') || 'none', 'at expiration']]) +
    '<svg class="lu-svg" viewBox="0 0 ' + W + ' ' + Hh + '" role="img" aria-label="Profit and loss at expiration"><line class="lu-z" x1="8" x2="' + (W - 52) + '" y1="' + PY(0).toFixed(1) + '" y2="' + PY(0).toFixed(1) + '"/>' +
    '<line class="lu-sp" x1="' + PX(spot).toFixed(1) + '" x2="' + PX(spot).toFixed(1) + '" y1="10" y2="' + (Hh - 24) + '"/><path class="lu-pl" d="' + ys.map((v, i) => (i ? 'L' : 'M') + PX(xs[i]).toFixed(1) + ' ' + PY(v).toFixed(1)).join('') + '"/>' +
    '<text class="lu-ax" x="' + (W - 46) + '" y="' + (PY(y1) + 10).toFixed(1) + '">' + k(y1) + '</text><text class="lu-ax" x="' + (W - 46) + '" y="' + (PY(y0) - 2).toFixed(1) + '">' + k(y0) + '</text>' +
    '<text class="lu-ax" x="8" y="' + (Hh - 6) + '">' + lo.toFixed(0) + '</text><text class="lu-ax" x="' + (W - 52) + '" y="' + (Hh - 6) + '" text-anchor="end">' + hi.toFixed(0) + '</text></svg>';
}

function draw() {
  const b = el('lu-body'), c = el('lu-chips');
  b.parentNode.hidden = pend;                     // the section's chip says when the first reading arrives
  if (pend) return;
  c.innerHTML = TOOLS.map(([k, l]) => '<button type="button" data-k="' + k + '" aria-pressed="' + (st.k === k) + '">' + esc(l) + '</button>').join('');
  if (!d) { b.innerHTML = none('No lineup reading on file yet.'); return; }
  try { b.innerHTML = tool[st.k](); } catch (e) { b.innerHTML = none('This tool has no reading.'); }
  if (st.k === 'scr') scr(); if (st.k === 'rp') report(); if (st.k === 'po') { legs(); pay(); }
  el('lu-asof').textContent = d.as_of ? 'Daily bars through ' + dd(d.as_of) : '';
}

// ---- Gap-Fill and Correlation Web -----------------------------------------------------------------------------------------
function panes() {
  const g = (d || {}).gap_fill, w = (d || {}).correlation_web;
  el('lu-gap').hidden = el('lu-corr').hidden = pend;
  if (pend) return;
  el('lu-gap').innerHTML = g && g.gaps ? '<p class="lu-sub">' + N(g.gaps) + ' gaps of 0.5%+ over ' + g.sessions + ' sessions</p>' +
    T(['Gap', 'Up gaps filled', 'Down gaps filled'], g.by_size.map(r => [esc(r.size), NC(r.up.n, null) + ' · ' + P(r.up.filled_pct, 0), NC(r.down.n, null) + ' · ' + P(r.down.filled_pct, 0)]), [1, 2]) +
    T(['Weekday', 'Gaps', 'Filled'], g.by_weekday.map(r => [esc(r.day), N(r.n), P(r.filled_pct, 0)]), [1, 2]) : none('No gaps on file yet.');
  el('lu-corr').innerHTML = w && (w.pairs || []).length ? '<p class="lu-sub">' + N(w.names) + ' names · ' + w.window + ' sessions</p>' +
    T(['Pair', 'r'], w.pairs.slice(0, 10).map(p => [esc(p.a + ' / ' + p.b), (+p.r).toFixed(2)]), [1]) +
    '<div class="lu-pills">' + (w.clusters || []).map(c => '<span class="lu-pill" title="' + esc(c.members.join(', ')) + '">' + c.size + ' · ' + esc(c.members.slice(0, 4).join(', ')) + (c.size > 4 ? ' …' : '') + '</span>').join('') + '</div>' : none('No correlation reading on file yet.');
}

// ---- Chart Read Engine: the roster's published reads, evidence only -------------------------------------------------------
let ri = null, rq = '';
const shard = s => /^[A-Z]/.test(s) ? s.charAt(0) : '0';
function readIndex() {
  const e = el('lu-read');
  if (!ri || !ri.names) { e.innerHTML = none('No roster reads on file yet.'); return; }
  const cnt = {};
  Object.values(ri.names).forEach(v => { const w = (v && v[2]) || '—'; cnt[w] = (cnt[w] || 0) + 1; });
  e.innerHTML = '<p class="lu-sub">' + N(Object.keys(ri.names).length) + ' names read · ' + dd(ri.as_of) + '</p><div class="lu-pills">' +
    Object.entries(cnt).sort((a, b) => b[1] - a[1]).map(([w, n]) => '<span class="lu-pill">' + esc(w) + ' · ' + n + '</span>').join('') + '</div>' +
    '<div class="lu-form"><input class="lu-in" id="lu-crq" placeholder="Symbol" autocapitalize="characters" aria-label="Symbol" value="' + esc(rq) + '"></div><div id="lu-cr"></div>';
  readOne();
}
function readOne() {
  const e = el('lu-cr'), s = rq.trim().toUpperCase();
  if (!e) return;
  if (!s) { e.innerHTML = ''; return; }
  if (!ri.names[s]) { e.innerHTML = none(s + ' is not on the roster.'); return; }
  get('reads-' + shard(s) + '.json').then(j => {
    const r = j && j[s];
    if (!r || rq.trim().toUpperCase() !== s) return;
    const li = a => (a || []).length ? '<ul class="lu-ul">' + a.map(x => '<li><b>' + esc(x.head) + '</b> ' + esc(x.text || '') + '</li>').join('') + '</ul>' : none('None.');
    e.innerHTML = '<p class="lu-sub"><b>' + esc(s) + '</b> · ' + esc((r.gut || {}).word || '') + ' · ' + dd(r.as_of) + '</p><p>' + esc(r.gist || '') + '</p>' +
      '<div class="lu-two"><div><h4>For</h4>' + li((r.standouts || []).concat(r.material || [])) + '</div><div><h4>Against</h4>' + li(r.against) + '</div></div>' +
      ((r.considered || []).length ? '<h4>Read sheet</h4><div class="lu-pills">' + r.considered.map(x => '<span class="lu-pill">' + esc(x) + '</span>').join('') + '</div>' : '');
  });
}

// ---- events ---------------------------------------------------------------------------------------------------------------------
const save = () => { try { localStorage.setItem('md_watch', JSON.stringify(st.wl)); } catch (e) { /* this browser only */ } };
D.addEventListener('click', e => {
  const c = e.target.closest('#lu-chips button');
  if (c) { st.k = c.dataset.k; st.lim = 40; draw(); return; }
  const a = e.target.closest('[data-a]'); if (!a || !a.closest('#h-lineup')) return;
  const k = a.dataset.a;
  if (k === 'more') { st.lim += 60; scr(); }
  else if (k === 'wladd' || k === 'wl1') { const q = (k === 'wl1' ? a.dataset.s : (el('lu-wlq').value || '')).trim().toUpperCase(); if (/^[A-Z0-9.\-]{1,8}$/.test(q) && !st.wl.includes(q) && st.wl.length < 40) { st.wl.push(q); save(); draw(); } }
  else if (k === 'wlx') { st.wl = st.wl.filter(x => x !== a.dataset.s); save(); draw(); }
  else if (k === 'poadd' && st.po.legs.length < 8) { st.po.legs.push({k: 'call', s: 'long', K: Math.round(+st.po.spot || 100), p: 1, q: 1}); legs(); pay(); }
  else if (k === 'porm') { st.po.legs.splice(+a.dataset.i, 1); legs(); pay(); }
});
const onIn = e => {
  const t = e.target;
  if (t.dataset.f) { st.f[t.dataset.f] = t.value; st.lim = 40; scr(); }
  else if (t.dataset.l) { const l = st.po.legs[+t.dataset.i]; if (l) { l[t.dataset.l] = t.value; pay(); } }
  else if (t.id === 'lu-spot') { st.po.spot = t.value; pay(); }
  else if (t.id === 'lu-rq') { st.rq = t.value; report(); }
  else if (t.id === 'lu-crq') { rq = t.value; readOne(); }
};
D.addEventListener('input', onIn);
D.addEventListener('change', onIn);

Promise.all([get('lineup.json'), get('reads-index.json')]).then(([a, b]) => {
  d = a && a.universe ? a : null; ri = b; pend = !d && !!(a && a.pending);
  ix = {};
  if (d) d.universe.rows.forEach(r => { const o = {}; d.universe.cols.forEach((k, i) => { o[k] = r[i]; }); ix[o.s] = o; });
  draw(); panes(); readIndex();
});
})();
