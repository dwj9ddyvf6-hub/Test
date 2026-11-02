/* Master Desk terminal, the Hub's Options data panel: each options source's state, age and the Tradier rate budget,
   and a decision memo per symbol (chain source, ATM IV, straddle expected move, ATM Greeks), from edition.options_data
   (desk/data/options_hub.py). Nothing recomputed; a fact older than its max age reads stale, never live. */
(() => {
const D = document, el = id => D.getElementById(id), M = window.MD;
if (!M || !el('h-optdata')) return;
const esc = M.esc, isN = v => typeof v === 'number' && isFinite(v);
const f = (v, d) => isN(v) ? (+v).toFixed(d) : '—';
const age = s => !isN(s) ? '—' : s < 90 ? Math.round(s) + ' s' : s < 5400 ? Math.round(s / 60) + ' min' : Math.round(s / 3600) + ' h';
const tag = w => '<span class="lu-mu">' + esc(w || 'unknown') + '</span>';
let last = null;
function draw() {
  const o = M.ed && M.ed.options_data, box = el('od-body');
  if (!box || o === last) return;
  last = o;
  if (!o) { box.innerHTML = '<p class="lu-mu">No options data in this edition.</p>'; return; }
  const b = o.budget || {};
  let h = '<div class="lu-tw"><table class="lu-t"><thead><tr><th>Source</th><th>State</th><th class="r">Age</th><th>Freshness</th></tr></thead><tbody>' +
    (o.sources || []).map(s => '<tr><td><b>' + esc(s.name) + '</b></td><td>' + esc(s.state) + '</td><td class="r">' + age(s.age_s) + '</td><td>' + tag(s.freshness) + '</td></tr>').join('') +
    '</tbody></table></div><p class="lu-mu">Tradier budget ' + (isN(b.sent_last_min) ? b.sent_last_min : '—') + ' of ' + (isN(b.target_per_min) ? b.target_per_min : '—') +
    '/min' + (isN(b.available) ? ' · ' + b.available + ' left' : '') + (b.blocked_for_s ? ' · paused ' + age(b.blocked_for_s) : '') + ' · stream ' + esc(o.stream || 'off') + '</p>';
  const ms = o.memos || [];
  h += ms.length ? '<div class="lu-tw"><table class="lu-t"><thead><tr><th>Symbol</th><th class="r">Spot</th><th>Expiry</th><th class="r">ATM IV</th><th class="r">Move</th><th class="r">Range</th><th class="r">Δ</th><th class="r">Γ</th><th class="r">Θ/day</th><th class="r">Vega</th><th>Source</th></tr></thead><tbody>' +
    ms.map(m => { const g = m.greeks || {}; return '<tr><td><b>' + esc(m.symbol) + '</b></td><td class="r">' + f(m.spot, 2) + '</td><td>' + esc(m.expiry || '—') +
      '</td><td class="r">' + (isN(m.atm_iv) ? f(m.atm_iv * 100, 1) + '%' : '—') + '</td><td class="r">' + f(m.move, 2) + (isN(m.move_pct) ? ' (' + f(m.move_pct, 2) + '%)' : '') +
      '</td><td class="r">' + f(m.lower, 2) + '–' + f(m.upper, 2) + '</td><td class="r">' + f(g.delta, 2) + '</td><td class="r">' + f(g.gamma, 4) + '</td><td class="r">' + f(g.theta, 3) +
      '</td><td class="r">' + f(g.vega, 3) + '</td><td>' + esc(m.source) + ' ' + tag(m.freshness) + (m.orats_flag ? ' ⚑' : '') + '</td></tr>'; }).join('') + '</tbody></table></div>'
    : '<p class="lu-mu">No chain yet for the memo symbols.</p>';
  box.innerHTML = h;
}
draw();
setInterval(draw, 2000);
})();
