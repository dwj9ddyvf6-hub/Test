/* Master Desk terminal, the Hub's Systems section (loaded on the Hub tab's first open: #p-hub data-js): one card
   per system from mind.json (desk/terminal/mind.py), drawn
   generically: title, when it was read, one sentence, its rows (numeric rows that share a stated unit get bars on one
   scale), and a small table (a column of numbers gets bars on the column's scale). Every string is the system's own, printed as written; a card past its own age limit on
   this reader's clock is not drawn. Nothing recomputed. */
(() => {
const D = document, el = id => D.getElementById(id), sec = el('h-mind'), box = el('mind-body');
if (!sec || !box) return;
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const ago = t => { const s = Math.max(0, (Date.now() - t) / 1e3); return 'read ' + (s < 90 ? 'just now' : s < 5400 ? Math.round(s / 60) + ' min ago' : s < 172800 ? Math.round(s / 3600) + ' h ago' : Math.round(s / 86400) + ' d ago'); };
// a formatted value as a number, or null: an optional sign (hyphen or the minus sign), an optional currency sign,
// digits with thousands commas, an optional percent sign; anything else (a time, a word) is not a number
const num = v => { const m = /^([+\-−]?)[$£€]?(\d[\d,]*(?:\.\d+)?)%?$/.exec(String(v).trim()); return m ? (m[1] === '-' || m[1] === '−' ? -1 : 1) * +m[2].replace(/,/g, '') : null; };
// the scale a row may share: its stated unit, or percent; a bare count has none (two counts of different things are not one scale)
const unitOf = r => r.unit || (/%$/.test(String(r.value).trim()) ? '%' : null);
const fresh = p => { const t = Date.parse(p.as_of); return isFinite(t) && Date.now() <= t + p.max_age_minutes * 6e4; };
// one bar on a 100-wide track: from the left when the group has no negative, from the middle when it has
const bar = (v, mx, neg) => { const w = v ? Math.max(1.5, Math.abs(v) / mx * (neg ? 50 : 100)) : 0, x = neg ? (v < 0 ? 50 - w : 50) : 0;   // a zero draws its track only
  return '<svg class="mi-b" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><rect class="mi-tr" width="100" height="8" rx="2"/><rect class="mi-f ' + (v < 0 ? 'dn' : 'up') + '" x="' + x.toFixed(1) + '" width="' + w.toFixed(1) + '" height="8" rx="2"/>' + (neg ? '<rect class="mi-z" x="49.6" width=".8" height="8"/>' : '') + '</svg>'; };
function rows(rs) {
  const g = {};                                         // unit -> the numeric rows that share it
  rs.forEach(r => { const v = num(r.value), u = unitOf(r); if (v != null && u) (g[u] = g[u] || []).push(v); });
  let bars = 0;
  const h = rs.map(r => { const v = num(r.value), vs = (v != null && g[unitOf(r)]) || [], on = vs.length > 1;
    if (on) bars++;
    return '<div class="mi-r' + (on ? '' : ' mi-nb') + '"><span class="mi-l">' + esc(r.label) + '</span>' + (on ? bar(v, Math.max(...vs.map(Math.abs), 1e-9), vs.some(x => x < 0)) : '') +
      '<b class="mi-v">' + esc(r.value) + (r.unit ? ' <i>' + esc(r.unit) + '</i>' : '') + '</b>' + (r.note ? '<span class="mi-n">' + esc(r.note) + '</span>' : '') + '</div>'; }).join('');
  return h ? '<div class="mi-rows"' + (bars > 1 ? ' data-viz' : '') + '>' + h + '</div>' : '';   // the values stay text: no image role over them
}
// a table column whose every cell is a number of one kind (all percent, or none) is one quantity down the column: its
// cells get bars on the column's own scale. One row, or a column of zeros, compares nothing and draws none.
function table(t) {
  if (!t || !t.columns) return '';
  const rs = t.rows || [];
  const cols = t.columns.map((c, i) => { if (!i || rs.length < 2) return null;
    const vs = rs.map(r => num(r[i])), pc = rs.map(r => /%$/.test(String(r[i]).trim()));
    return vs.every(v => v != null) && vs.some(v => v) && pc.every(p => p === pc[0]) ? {mx: Math.max(...vs.map(Math.abs)), neg: vs.some(v => v < 0)} : null; });
  const on = cols.some(Boolean);
  return '<table class="mi-t"' + (on ? ' data-viz' : '') + '><thead><tr>' + t.columns.map((c, i) => '<th' + (i ? ' class="r"' : '') + '>' + esc(c) + '</th>').join('') + '</tr></thead><tbody>' +
    rs.map(r => '<tr>' + r.map((c, i) => '<td' + (i ? ' class="r" data-l="' + esc(t.columns[i]) + '"' : '') + '>' + (cols[i] ? bar(num(c), cols[i].mx, cols[i].neg) + '<span class="mi-cv">' + esc(c) + '</span>' : esc(c)) + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
}
const card = p => '<article class="gk mi-c"><div class="gk-h"><b>' + esc(p.title) + '</b><span>' + esc(ago(Date.parse(p.as_of))) + '</span></div><p class="mi-sum">' + esc(p.summary) + '</p>' + rows(p.rows || []) + table(p.table) + '</article>';
let doc = null, busy = 0, shown = null;
function draw() {
  const ps = ((doc && doc.panels) || []).filter(fresh), h = ps.map(card).join('');
  sec.hidden = !ps.length;
  if (shown !== h) { shown = h; box.innerHTML = '<div class="mi-g">' + h + '</div>'; }
}
function load() {
  if (busy) return;
  busy = 1;
  fetch('mind.json', {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(j => { doc = j; }, () => {}).then(() => { busy = 0; draw(); });
}
D.addEventListener('md:edition', load);
D.addEventListener('md:tab', e => { if (e.detail === 'hub') load(); });
setInterval(draw, 6e4);                                 // the ages and each card's own limit follow the reader's clock
load();
})();
