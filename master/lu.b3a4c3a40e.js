/* Look up: every desk engine on the name (desk/analysis/anyname.py; owner 2026-11-04: "The engine should cover any name
   we want them to"). engines-index.json names every stored read; engines-<L>.json carries them. One tile per engine:
   its words and numbers, or why it could not apply. The gamma tile draws the put wall, the price, the flip and the call
   wall on one axis. A name with no read yet says when the desk reads it. */
(() => {
'use strict';
const D = document, $ = id => D.getElementById(id), isN = v => typeof v === 'number' && isFinite(v);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const fq = new URLSearchParams(location.search).get('fixture'), DIR = ['empty', 'first', 'closed', 'full'].includes(fq) ? 'fixtures/' : '';
const get = u => fetch(DIR + u, {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
const M = '\u2212', sg = (v, k) => (v > 0 ? '+' : v < 0 ? M : '') + Math.abs(v).toFixed(k);   // a true minus sign (T-193)
const shard = s => /^[A-Z]/.test(s) ? s.charAt(0) : '0', pc = v => isN(v) ? sg(v, 2) + '%' : '–';
const MO = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const day = s => { const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(s || ''); return m ? MO[+m[2] - 1] + ' ' + (+m[3]) : esc(s); };
const bn = v => isN(v) ? (v < 0 ? M : '') + '$' + Math.abs(v).toFixed(2) + 'B' : '–';   // "$0.18B", "−$0.18B"
let ix = null;
const index = () => ix ? Promise.resolve(ix) : get('engines-index.json').then(j => (ix = j));
function axis(g) {
  const p = [['put wall', g.put_wall, 'dn'], ['chain price', g.spot, ''], ['flip', g.flip, 'wn'], ['call wall', g.call_wall, 'up']].filter(x => isN(x[1]));
  if (p.length < 2) return '';
  const v = p.map(x => x[1]), lo = Math.min(...v), hi = Math.max(...v), w = 300, X = x => 50 + (hi > lo ? (x - lo) / (hi - lo) : 0.5) * (w - 100), A = x => X(x) < 70 ? 'start' : X(x) > w - 70 ? 'end' : 'middle';
  return '<svg class="lua" viewBox="0 0 ' + w + ' 44" width="100%" role="img" aria-label="' + esc(p.map(x => x[0] + ' ' + x[1]).join(', ')) +
    '"><line x1="10" x2="' + (w - 10) + '" y1="22" y2="22" stroke="currentColor" opacity=".3"/>' + p.map((x, i) =>
    '<circle cx="' + X(x[1]) + '" cy="22" r="4" class="' + x[2] + '" fill="currentColor"/><text x="' + (A(x[1]) === 'start' ? X(x[1]) - 6 : A(x[1]) === 'end' ? X(x[1]) + 6 : X(x[1])) + '" y="' + (i % 2 ? 40 : 12) +
    '" text-anchor="' + A(x[1]) + '" font-size="10" fill="currentColor">' + esc(x[0] + ' ' + x[1]) + '</text>').join('') + '</svg>';
}
const line = {
  chart: b => esc(b.action) + ' · ' + esc(b.conviction) + ' · gut ' + esc(b.gut) + (b.plan ? '<br>' + esc(b.plan) : ''),
  har: b => 'next-day vol ' + b.har_vol_pct + '% · 68% day band ±' + b.band68_pct + '%',
  gamma: b => '<b>' + esc(b.regime) + '</b> ' + bn(b.net_gex_b) + ' per 1% move · flip ' + esc(b.flip) + ' (' + pc(b.flip_distance_pct) + ') · walls ' +
    esc(b.put_wall) + ' / ' + esc(b.call_wall) + (isN(b.spot) ? '<br><span class="mu">computed at price ' + b.spot.toFixed(2) +
    (b.spot_at ? ', ' + esc(b.spot_at) : '') + ' (option chain quote)</span>' : '') + axis(b),
  ladder: b => (b.strongest || []).map(r => esc(r.strike) + ' ' + esc(r.kind)).join(' · '),
  pins: b => (b.expiries || []).slice(0, 3).map(p => day(p.expiry) + ' pin ' + esc(p.pin_strike) + ' (' + pc(p.distance_pct) + ')').join('<br>'),
  walls: b => esc(b.grade),
  move: b => (isN(b.em_1d_pct) ? 'day ±' + b.em_1d_pct + '% · week ±' + b.em_5d_pct + '%' : '') +
    (isN(b.straddle_pct) ? '<br>straddle ' + day(b.straddle_expiry) + ' ±' + b.straddle_pct + '%' : ''),
  options: b => 'IV ' + esc(b.iv30_pct) + '% · RV20 ' + esc(b.rv20_pct) + '% · put/call OI ' + esc(b.pc_oi) + (isN(b.iv_rank) ? ' · IV rank ' + b.iv_rank : ''),
  earnings: b => 'next ' + (b.next_date ? day(b.next_date) : '–') + ' · last ' + (b.last_report ? day(b.last_report) : '–'),
  short: b => esc(b.si_pct_float) + '% of shares short',
  insider: b => esc(b.buys) + ' buys · ' + esc(b.sells) + ' sells' + (b.cluster === 'cluster_buying' ? ' · cluster buying' : ''),
  news: b => (b.headlines || []).map(h => esc(h.headline)).join('<br>'),
};
function paint(box, sym, r, ix) {
  const t = ix.titles || {}, e = r.engines || {};
  box.innerHTML = '<h3>' + esc(sym) + ': every engine <span class="mu">' + esc(r.built || '') + '</span></h3>' + (ix.engines || Object.keys(e)).map(k => {
    const b = e[k] || {status: 'no_data', reason: 'not in this read'}, ok = b.status === 'ok' || b.status === 'stale';
    let body;
    try { body = ok ? (line[k] ? line[k](b) : '') : '<span class="mu">' + esc(b.reason) + '</span>'; } catch (_) { body = ''; }
    return '<div class="lue1"><b>' + esc(t[k] || k) + '</b> <span class="bdg ' + (ok ? (b.status === 'ok' ? 'up' : 'wn') : 'mu') + '">' +
      esc(ok ? (b.freshness || b.status) : 'could not apply') + '</span><div>' + body + '</div></div>';
  }).join('');
}
function show(q) {
  const res = $('lres');
  if (!res || !q) return;
  let box = $('lue');
  if (!box) { box = D.createElement('div'); box.id = 'lue'; box.className = 'lue'; res.after(box); }
  box.innerHTML = '<p class="mu">Reading every engine on ' + esc(q) + '…</p>';
  index().then(j => {
    if (!j.names || !j.names[q]) {
      box.innerHTML = '<p class="mu">No engine read of ' + esc(q) + ' yet. The desk reads every engine on the roster and the funds once a session, ' +
        'and a name on its request list in the next hourly run; the edition after that run shows it.</p>';
      return;
    }
    return get('engines-' + shard(q) + '.json').then(s => { if (!s[q]) throw new Error('missing'); paint(box, q, s[q], j); });
  }).catch(() => { box.innerHTML = '<p class="mu">The engine reads could not be loaded. Try again.</p>'; });
}
const f = $('lf');
if (f) f.addEventListener('submit', () => show($('lq').value.trim().toUpperCase()));
const ls = $('ls');
if (ls) ls.addEventListener('click', e => { const b = e.target.closest('.lsb'); if (b) show(b.dataset.s); });
window.LUE = {show, paint, axis};
})();
