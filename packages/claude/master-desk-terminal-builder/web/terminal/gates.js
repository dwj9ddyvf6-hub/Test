// REUSABLE renderers (not wired into the retired board; for the new Best Setups picker): a verdict line a reader acts on
// at a glance, and a generic check list [{tag, sentence, value, pass, need}] (desk/terminal/gates.py). Needs the page's
// isN, esc and px (order-tick price rounding) globals.
const GW = {Buy: 'b', 'Watch only': 'w', 'No trade': 'x'};
function gateVerdict(g, close) {
  if (!g || !GW[g.verdict]) return '';
  const n = g.need, need = n && isN(n.pct) && isN(close) ? ' · ' + n.words + ' ' + px(close, n.pct, n.role) : '';
  const head = g.verdict === 'Buy' ? 'Buy · ' + g.size : g.verdict === 'No trade' ? 'No trade' : 'Watch';
  return '<div class="gv ' + GW[g.verdict] + '"><b>' + esc(head) + '</b>' + (g.missing ? '<span>' + esc(g.missing + need) + '</span>' : '') + '</div>';
}
function gateList(rows) {
  if (!rows || !rows.length) return '';
  const req = rows.filter(r => r.need), ok = req.filter(r => r.pass === true).length;
  return '<details class="grl"><summary>Checks · ' + ok + ' of ' + req.length + ' pass</summary><ul>' + rows.map(r =>
    '<li class="' + (r.pass === true ? 'ok' : r.pass === false ? 'no' : 'nd') + (r.need ? '' : ' cx') + '"><i aria-hidden="true">' +
    (r.pass === true ? '✓' : r.pass === false ? '✗' : '—') + '</i><em>' + esc(r.tag) + '</em>' + esc(r.sentence) + (r.need ? '' : ' (context)') + '</li>').join('') + '</ul></details>';
}
