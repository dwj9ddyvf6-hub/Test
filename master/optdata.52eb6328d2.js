/* Master Desk terminal, the Hub's Options data panel: each options source's state, age and the Tradier rate budget,
   and a decision memo per symbol (chain source, ATM IV, straddle expected move, ATM Greeks), from edition.options_data
   (desk/data/options_hub.py). Nothing recomputed; a fact older than its max age reads stale, never live. */
(() => {
const D = document, el = id => D.getElementById(id), M = window.MD;
if (!M || !el('h-optdata')) return;
const esc = M.esc, isN = v => typeof v === 'number' && isFinite(v);
const f = (v, d) => isN(v) ? (+v).toFixed(d).replace('-', '\u2212') : '—';
const age = s => !isN(s) ? '—' : s < 90 ? Math.round(s) + ' s' : s < 5400 ? Math.round(s / 60) + ' min' : Math.round(s / 3600) + ' h';
const tag = w => '<span class="lu-mu">' + esc(w || 'unknown') + '</span>';
let last = null;
function draw() {
  const o = M.ed && M.ed.options_data, box = el('od-body');
  if (!box || o === last) return;
  last = o;
  if (!o) { box.innerHTML = '<p class="lu-mu">No options data in this edition.</p>'; return; }
  const b = o.budget || {};
  let h = '';   // the sources' states, ages and the rate budget are the desk's plumbing, not the panel's reading (owner 2026-11-02)
  const ms = o.memos || [];
  h += ms.length ? '<div class="lu-tw"><table class="lu-t"><thead><tr><th>Symbol</th><th class="r">Spot</th><th>Expiry</th><th class="r">ATM IV</th><th class="r">Move</th><th class="r">Range</th><th class="r">Δ</th><th class="r">Γ</th><th class="r">Θ/day</th><th class="r">Vega</th></tr></thead><tbody>' +
    ms.map(m => { const g = m.greeks || {};
      // a memo with no reading on its expiry is said so in one cell, never a row of dashes (round 2b: IWM)
      if (!isN(m.atm_iv) && !isN(m.move)) return '<tr><td><b>' + esc(m.symbol) + '</b></td><td colspan="9" class="lu-mu">' + (isN(m.spot) ? 'Spot ' + f(m.spot, 2) + ' · no at-the-money quote on its chain yet' : 'No quote on its chain yet') + (m.as_of ? ' (chain as of ' + esc(String(m.as_of).slice(0, 16).replace('T', ' ')) + ' UTC)' : '') + '</td></tr>';
      return '<tr><td><b>' + esc(m.symbol) + '</b></td><td class="r">' + f(m.spot, 2) + '</td><td>' + esc(m.expiry || '—') +
      '</td><td class="r">' + (isN(m.atm_iv) ? f(m.atm_iv * 100, 1) + '%' : '—') + '</td><td class="r">' + f(m.move, 2) + (isN(m.move_pct) ? ' (' + f(m.move_pct, 2) + '%)' : '') +
      '</td><td class="r">' + f(m.lower, 2) + '–' + f(m.upper, 2) + '</td><td class="r">' + f(g.delta, 2) + '</td><td class="r">' + f(g.gamma, 4) + '</td><td class="r">' + f(g.theta, 3) +
      '</td><td class="r">' + f(g.vega, 3) + '</td></tr>'; }).join('') + '</tbody></table></div>'
    : (o.memos_why ? '<p class="lu-mu">' + esc(o.memos_why) + '</p>' : '');   // no memo: its producer's reason; no memo yet: the chart above carries the last archived chain, dated (viz_engines.js); no second sentence
  box.innerHTML = h;
}
draw();
setInterval(draw, 2000);
})();
