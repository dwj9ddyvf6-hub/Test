/* Master Desk terminal, the Record tab's audit (s4): the edition's `record` block (desk/terminal/record.py). One row per
   call, losers included: how it ended, the targets it hit, its result in R, what it gave back from its best, and its
   close-to-close grades 1, 5 and 21 sessions after its read. A small sample says so; months, setup types, the market it
   was listed in, a seeded random baseline and each type's incubation follow. CSV of every row. viz.js loads this file
   on the tab's first open. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id);
const host = el('r-audit');
if (!host || !M) return;
const esc = M.esc, isN = M.isN, num = M.num, pct = M.pct;
const R = v => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(2) + 'R' : '—';
const P = v => isN(v) ? pct(v, 1) : '—';
const HR = s => !isN(s.hit_rate) ? '—' : s.closed < 30 ? s.won + ' of ' + (s.won + s.lost) : Math.round(s.hit_rate * 100) + '%';   // a % only from 30 closed
const CODE = {target: 'Target', trail: 'Stop after T1', stop: 'Stop', time: 'Time', expired: 'Expired', missed: 'Missed',
  void: 'Void', open: 'Open', waiting: 'Waiting'};
const tone = x => x.verdict === 'won' ? 'up' : x.verdict === 'lost' ? 'dn' : '';
let shown = 25;
function tiles(r) {
  const s = r.summary, small = s.small_n ? '<p class="ra-n">' + s.closed + ' closed · too few to judge · first read at ' + r.small_n + '</p>' : '';
  return '<div class="ra-h"><b>' + esc(r.header) + '</b><span>since ' + esc(r.since || '—') + ' · ' + s.calls + ' calls · even band ±' +
    r.even_band + 'R kept out of the hit rate</span></div>' + small +
    '<dl class="ra-t">' + [['Won', HR(s), s.won + ' won · ' + s.lost + ' lost' + (s.even ? ' · ' + s.even + ' even' : '')],
      ['Avg per call', R(s.avg_r), 'losers in · total ' + R(s.total_r)], ['Gave back', R(s.avg_give_back), 'from each call’s best, avg'],
      ['Random entries', R(r.random.avg_r), r.random.n ? r.random.n + ' draws · same names, earlier days' : 'not enough history'],
      ['Edge over random', R(r.random.edge_r), isN(r.random.edge_r) ? 'avg per call less random entries' + (s.small_n ? ' · too few to judge' : '') : 'needs a closed call and random draws']]
      .map(t => '<div><dt>' + t[0] + '</dt><dd>' + t[1] + '</dd><small>' + t[2] + '</small></div>').join('') + '</dl>';
}
function excluded(r) {
  const x = r.excluded_why || [];
  return x.length ? '<ul class="ra-i ra-x">' + x.map(e => '<li><b>' + e.n + ' ' + esc(CODE[e.code] || e.code).toLowerCase() + '</b> kept out of the hit rate · ' + esc(e.why) + '</li>').join('') + '</ul>' : '';
}
function typeLines(r) {
  const x = r.type_lines || [];
  return x.length ? '<ul class="ra-i ra-y">' + x.map(e => '<li>' + esc(e.text) + '</li>').join('') + '</ul>' : '';
}
function horizons(r) {
  return '<div class="ra-z">' + Object.keys(r.horizons).map(k => { const h = r.horizons[k];
    return '<span><i>' + k + ' after the read</i><b>' + (h.n ? P(h.mean) : '—') + '</b><small>' + (h.n ? h.up + ' of ' + h.n + ' up' : 'not yet graded') + '</small></span>'; }).join('') + '</div>';
}
function rows(r) {
  const xs = r.rows.slice(0, shown);
  const tr = x => '<tr class="' + tone(x) + '"><th scope="row">' + esc(x.symbol) + '<small>' + esc(x.form || '') + ' · ' + esc(x.listed) + '</small></th><td>' +
    esc(CODE[x.code] || x.code) + (x.targets ? ' <small>' + x.targets + '</small>' : '') + (x.why ? '<small class="ra-w">' + esc(x.why) + '</small>' : '') +
    (x.corrections ? ' <small>corrected</small>' : '') + '</td><td class="r">' + R(x.r) + '</td><td class="r">' + (isN(x.give_back) ? R(-x.give_back) : '—') +
    '</td><td class="r">' + P(x.h1) + '</td><td class="r">' + P(x.h5) + '</td><td class="r">' + P(x.h21) + '</td></tr>';
  return '<div class="tw"><table class="t ra-r"><caption>Every call · newest first · ' + r.rows_total + ' in all</caption><thead><tr><th>Call</th><th>Ended</th>' +
    '<th class="r">Result</th><th class="r">Gave back</th><th class="r">1d</th><th class="r">5d</th><th class="r">21d</th></tr></thead><tbody>' +
    xs.map(tr).join('') + '</tbody></table></div>' + (r.rows.length > shown ? '<button class="tg ra-m" type="button">Show more</button>' : '') +
    '<button class="tg ra-c" type="button">Download every row (CSV)</button>';
}
function group(cap, g) {
  const ks = Object.keys(g || {});
  if (!ks.length) return '';
  return '<div class="tw"><table class="t"><caption>' + cap + '</caption><thead><tr><th></th><th class="r">Closed</th><th class="r">Hit</th><th class="r">Avg</th></tr></thead><tbody>' +
    ks.map(k => { const s = g[k]; return '<tr><th scope="row">' + esc(k) + '</th><td class="r">' + s.closed + ' of ' + s.calls + '</td><td class="r">' +
      (s.closed ? HR(s) : '—') + '</td><td class="r">' + R(s.avg_r) + '</td></tr>'; }).join('') + '</tbody></table></div>';
}
function months(r) {
  return r.months.length ? group('By month closed', Object.fromEntries(r.months.map(m => [m.month, m]))) : '';
}
function incubation(r) {
  const ks = Object.keys(r.incubation || {});
  return ks.length ? '<ul class="ra-i">' + ks.map(k => { const s = r.incubation[k];
    return '<li><b>' + esc(k) + '</b> ' + (s.state === 'proven' ? 'proven' : 'incubating · ' + s.sessions + ' of ' + s.need_sessions + ' sessions, ' +
      s.closed + ' of ' + s.need_closed + ' closed' + (s.rule_changed ? ' · rule changed since frozen' : '')) + '</li>'; }).join('') + '</ul>' : '';
}
function csv(r) {
  const cols = ['id', 'symbol', 'form', 'listed', 'status', 'code', 'targets', 'pct', 'r', 'verdict', 'give_back', 'closed', 'regime', 'h1', 'h5', 'h21', 'why', 'corrections'];
  const q = v => v == null ? '' : /[",\n]/.test(String(v)) ? '"' + String(v).replace(/"/g, '""') + '"' : String(v);
  const b = new Blob([[cols.join(',')].concat(r.rows.map(x => cols.map(c => q(x[c])).join(','))).join('\n')], {type: 'text/csv'});
  const a = D.createElement('a');
  a.href = URL.createObjectURL(b); a.download = 'master-desk-record.csv'; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1e4);
}
function draw() {
  const r = (M.ed || {}).record;
  if (!r) { host.hidden = true; return; }
  host.hidden = false;
  el('r-audit-body').innerHTML = tiles(r) + horizons(r) + excluded(r) + rows(r) + group('By setup type', r.by_type.form) + typeLines(r) +
    group('By the market it was listed in', r.by_type.regime) + months(r) + incubation(r);
  const m = host.querySelector('.ra-m'), c = host.querySelector('.ra-c');
  if (m) m.onclick = () => { shown += 50; draw(); };
  if (c) c.onclick = () => csv(r);
}
draw();
D.addEventListener('md:edition', draw);
})();
