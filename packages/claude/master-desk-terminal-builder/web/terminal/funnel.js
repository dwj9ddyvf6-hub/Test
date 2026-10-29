/* Master Desk terminal: the Funnel (funnel.js). Muse's three free services, drawn from the edition's `funnel` block
   (desk/terminal/funnel.py) and nothing else: The Morning Map and The Qualified Board and The Golden Sweep Wire sit on the
   Market tab; a three-line summary sits on Setups. Every missing figure says why; no number is made up or recomputed here. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id);
if (!M) return;
const esc = M.esc, isN = M.isN, num = M.num;
const usd = (v, d) => isN(v) ? '$' + num(v, d == null ? 2 : d) : 'no data';
const mil = v => !isN(v) ? 'no data' : v >= 1e6 ? '$' + num(v / 1e6, 1) + 'M' : v >= 1e3 ? '$' + num(v / 1e3, 0) + 'K' : '$' + num(v, 0);
const sg = (v, d) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), d == null ? 1 : d) : '';
const TONE = {TRADE: 'up', CONTEXT: 'mu', STRETCH: 'wn'};

function note(sec) {
  return sec && sec.reason && sec.status !== 'no_data' ? '<p class="fnt ' + (sec.status === 'stale' ? 'wn' : 'mu') + '">' + esc(sec.reason) + '</p>' : '';
}
function head(id, kick, title, meta) {
  return '<div class="shd"><div class="sht"><p class="kick">' + esc(kick) + '</p><h2 id="h-f-' + id + '">' + esc(title) +
    '</h2></div><span class="pv">' + esc(meta || '') + '</span></div>';
}
function empty(id, kick, title, sec, extra) {
  return head(id, kick, title, '') + '<div class="card"><p class="fe">' + esc(sec && sec.reason || 'no data: this service has not published') + '</p>' + (extra || '') + '</div>';
}
function tile(l, v, s, t) {
  return '<div class="ft"><span class="fl">' + esc(l) + '</span><b class="fv ' + (t || '') + '">' + esc(v) + '</b><span class="fs">' + esc(s || '') + '</span></div>';
}
function grade(line) { return '<p class="fgr"><b>Record</b> ' + esc(line || 'no data: no grading line') + '</p>'; }

function mapCard(c, same) {
  const fl = isN(c.flip) ? usd(c.flip) : 'none near spot';
  const fs = isN(c.flip_pct) ? num(Math.abs(c.flip_pct), 1) + '% ' + (c.flip_pct > 0 ? 'above' : 'below') + ' spot' : 'no zero-gamma crossing within 20% of spot';
  const dix = isN(c.dix) ? num(c.dix, 3) : 'no data';
  const di = c.dix_index && c.dix_index.status === 'ok' ? ' · constituent DIX ' + num(c.dix_index.value, 3) : '';
  return '<article class="fmc"><h3>' + esc(c.symbol) + ' <span class="bdg ' + c.tone + '">' + esc(c.regime) + '</span> <span class="fl">' + usd(c.spot) + '</span></h3>' +
    '<div class="fgrid">' + tile('Flip', fl, fs, c.tone) +
    tile('Put wall', isN(c.put_wall) ? usd(c.put_wall, 0) : 'no data', isN(c.put_wall_pct) ? sg(c.put_wall_pct) + '%' : 'wall not found') +
    tile('Call wall', isN(c.call_wall) ? usd(c.call_wall, 0) : 'no data', isN(c.call_wall_pct) ? sg(c.call_wall_pct) + '%' : 'wall not found') +
    tile('Net gamma', (c.net_gex_b < 0 ? '−' : '') + '$' + num(Math.abs(c.net_gex_b), 2) + 'B', 'per 1% move') +
    tile('DIX', dix, (c.dix_date ? 'file ' + c.dix_date + ', one-day lag' : 'file date not stated') + di) +
    tile('Coverage', isN(c.coverage_pct) ? num(c.coverage_pct, 0) + '%' : 'no data', isN(c.coverage_pct) ? 'of open-interest contracts priced' : 'coverage not stated') + '</div>' +
    (same ? '' : '<p class="fag">' + esc(c.agree_line) + '</p>') + '<p class="frd">' + esc(c.read) + '</p></article>';
}
function mapHtml(s) {
  const k = 'Free service 1 · ' + (s && s.label || 'CONTEXT');
  if (!s || !s.cards || !s.cards.length) return empty('map', k, 'The Morning Map', s);
  const same = s.cards.every(c => c.agree_line === s.cards[0].agree_line);
  return head('map', k, 'The Morning Map', s.as_of ? 'as of ' + s.as_of + ' close' : '') + '<div class="card">' + note(s) +
    '<p class="fbig">' + esc(s.read) + '</p>' + s.cards.map(c => mapCard(c, same)).join('') +
    (same ? '<p class="fag"><b>Sources</b> ' + esc(s.cards[0].agree_line) + '</p>' : '') +
    (s.yesterday && s.yesterday !== s.grade_line ? '<p class="fgr"><b>Yesterday</b> ' + esc(s.yesterday) + '</p>' : '') + grade(s.grade_line) +
    '<p class="fnt mu">' + esc(s.measures) + ' Vintage: ' + esc(s.vintage) + '. ' + esc(s.delay) + '.</p></div>';
}

function lad(l) {
  if (!l || l.status !== 'ok') return '<p class="fe">' + esc(l && l.reason || 'no data: no ladder') + '</p>';
  const st = [['Wrong below', l.support, 'dn'], ['Buy above', l.trigger, ''], ['Target 1', l.t1, 'up'], ['Target 2', l.t2, 'up']];
  return '<ol class="fld">' + st.map(x => '<li class="' + x[2] + '"><span class="fl">' + x[0] + '</span><b>' + (isN(x[1]) ? usd(x[1]) : 'no data') + '</b></li>').join('') + '</ol>';
}
function chip(c) {
  return '<span class="fch" title="' + esc(c.vintage) + '"><span class="fl">' + esc(c.label) + '</span><b>' + num(c.value, 0) + '</b><small>' + esc(c.vintage) + '</small></span>';
}
function chips(cs) {
  const ok = (cs || []).filter(c => c.status === 'ok'), off = (cs || []).filter(c => c.status !== 'ok');
  return '<div class="fchs">' + ok.map(chip).join('') + '</div>' + (off.length ? '<details class="fnt mu"><summary>' + off.length +
    ' of ' + (cs || []).length + ' institutional chips have no data</summary><ul>' + off.map(c => '<li>' + esc(c.label) + ': ' + esc(c.reason) + '</li>').join('') + '</ul></details>' : '');
}
function boardRow(r) {
  const tr = r.triggers && r.triggers.length ? r.triggers.map(t => esc(t.name) + (t.validated === true ? ' (validated)' : t.validated === false ? ' (not validated)' : '')).join(' · ') : 'no trigger has fired';
  const lc = r.lector && r.lector.status === 'ok' ? 'Chart-review rank ' + r.lector.rank : esc(r.lector && r.lector.reason || 'no data');
  return '<article class="fbr"><h3>' + esc(r.symbol) + ' <span class="bdg ' + (TONE[r.label] || 'mu') + '" title="' + esc(r.label_why) + '">' + esc(r.label) +
    '</span> <span class="fl">' + (isN(r.close) ? usd(r.close) : 'no data') + (r.sector ? ' · ' + esc(r.sector) : '') + '</span></h3>' +
    '<p class="fln"><b>' + esc(r.line) + '</b></p><p class="fnt mu">' + tr + '</p>' + lad(r.ladder) + (r.label === 'TRADE' ? '' : '<p class="fnt mu">' + esc(r.label_why) + '</p>') +
    (r.cats && r.cats.length ? '<p class="fnt mu">Confirming: ' + r.cats.map(esc).join(', ') + '</p>' : '') +
    chips(r.chips) + '<p class="fnt mu">' + lc + ' (a separate judgement, never blended)</p></article>';
}
function boardHtml(s) {
  const k = 'Free service 2 · ' + (s && s.label || '');
  if (!s || s.status === 'no_data') return empty('board', k, 'The Qualified Board', s);
  return head('board', k, 'The Qualified Board', s.as_of ? 'as of ' + s.as_of + ' close' : '') + '<div class="card">' + note(s) +
    '<p class="fbig">' + esc(s.headline) + '</p>' + grade(s.grade_line) +
    '<details class="fnt"><summary>The gate, verbatim</summary><p>' + esc(s.gate) + '</p></details>' +
    (s.refused ? '<p class="fnt wn">' + esc(s.refused.line) + '</p>' : '') +
    '<p class="fnt mu">' + esc(s.shown_line) + '. ' + esc(s.base_rate) + '. ' + esc(s.lector_line) + '.</p>' +
    (s.rows || []).slice(0, 6).map(boardRow).join('') + ((s.rows || []).length > 6 ? '<details class="fmore"><summary>Show the other ' + (s.rows.length - 6) + ' qualified names</summary>' + s.rows.slice(6).map(boardRow).join('') + '</details>' : '') + '<p class="fnt mu">Vintage: ' + esc(s.vintage) + '. ' + esc(s.delay[0].toUpperCase() + s.delay.slice(1)) + '.</p></div>';
}

function pr(p, h) {
  const o = p.outcome || {}, side = p.sentiment ? p.side_word + ', ' + p.sentiment : p.side_word;
  return '<article class="fwp"><h3>' + esc(p.symbol) + ' ' + (p.strike != null ? usd(p.strike, 0).replace(/\.00$/, '') : '') + ' ' + esc(p.kind || '') +
    ' <span class="fl">' + esc(p.ts || 'time not stated') + '</span></h3>' +
    '<p class="fln"><b>' + mil(p.premium) + '</b> \u00b7 ' + esc(side) + (isN(p.dte) ? ' \u00b7 ' + p.dte + ' days to expiry' : '') +
    (isN(p.size) ? ' \u00b7 ' + num(p.size, 0) + ' contracts' : '') + '</p>' +
    '<p class="fnt mu">' + (p.tags || []).filter(t => t !== 'Heat 15+' || !isN(p.heat)).map(esc).join(' \u00b7 ') + (isN(p.heat) ? ' \u00b7 Heat ' + num(p.heat, 1) : '') + '</p>' +
    (h.op ? '' : '<p class="fnt">' + esc(p.opening && (p.opening.word || p.opening.reason) || 'no data') + '</p>') +
    (h.w52 ? '' : '<p class="fnt mu">' + esc(p.week52 && (p.week52.word || p.week52.reason) || 'no data') + '</p>') +
    '<p class="fnt ' + (o.state === 'graded' ? '' : 'mu') + '">' + (o.state === 'graded' || o.state === 'partial' ? esc(o.line) : 'Grade pending (+1h, +1d)') + '</p></article>';
}
function wireHtml(s) {
  const k = 'Free service 3 · ' + (s && s.label || 'CONTEXT');
  const rule = s ? '<details class="fnt"><summary>The rule that picks the prints</summary><p>' + esc(s.rule) + '</p></details>' : '';
  const cov = s ? '<p class="fnt mu">' + esc(s.coverage) + '.</p>' + (s.bias ? '<details class="fnt mu"><summary>How sides and scores are judged</summary><p>' + esc(s.bias) + '.</p></details>' : '') : '';
  if (!s || !s.prints || !s.prints.length) return empty('wire', k, 'The Golden Sweep Wire', s, rule + cov + (s ? grade(s.grade_line) : ''));
  const c = s.counts || {}, ps = s.prints, bad = k => ps.every(p => !p[k] || p[k].status !== 'ok');
  const h = {op: bad('opening'), w52: bad('week52')};
  const hoist = (h.op ? '<p class="fnt mu"><b>Opening or closing:</b> ' + esc(ps[0].opening.reason) + '.</p>' : '') +
    (h.w52 ? '<p class="fnt mu"><b>52-week context:</b> ' + esc(ps[0].week52.reason) + '.</p>' : '') +
    (ps.every(p => !p.outcome || p.outcome.state === 'pending') ? '<p class="fnt mu"><b>Later grade:</b> ' + esc(ps[0].outcome.line) + '.</p>' : '');
  return head('wire', k, 'The Golden Sweep Wire', s.as_of ? 'session ' + s.as_of : '') + '<div class="card">' + note(s) +
    '<p class="fbig">' + (c.golden || 0) + (c.golden === 1 ? ' Golden Sweep and ' : ' Golden Sweeps and ') + (c.qualified || 0) + ' prints met the rule, out of ' + num(c.prints_total || 0, 0) + ' prints</p>' +
    grade(s.grade_line) + rule + cov + (s.buys_only && s.buys_only.line ? '<p class="fnt mu">' + esc(s.buys_only.line) + '.</p>' : '') +
    hoist + s.prints.slice(0, 8).map(p => pr(p, h)).join('') + (s.prints.length > 8 ? '<details class="fmore"><summary>Show the other ' + (s.prints.length - 8) + ' prints</summary>' + s.prints.slice(8).map(p => pr(p, h)).join('') + '</details>' : '') + '<p class="fnt mu">' + esc(s.measures) + ' Vintage: ' + esc(s.vintage) + '. ' + esc(s.delay) + '.</p></div>';
}

function sumHtml(f) {
  const r = [['Morning Map', f.summary.map, f.map], ['Qualified Board', f.summary.board, f.board], ['Golden Sweeps', f.summary.wire, f.wire]];
  return r.map(x => '<a class="fsr ' + (x[2].status === 'no_data' ? 'off' : '') + '" href="#market"><b>' + x[0] + '</b><span>' + esc(x[1]) + '</span></a>').join('');
}

function all(d) {
  const f = d && d.funnel, put = (id, h) => { const e = el(id); if (e) { e.innerHTML = h; e.hidden = false; } };
  if (!f) {
    ['f-map', 'f-board', 'f-wire', 'f-sum'].forEach(i => { const e = el(i); if (e) e.hidden = true; });
    return;
  }
  put('f-map', mapHtml(f.map)); put('f-board', boardHtml(f.board)); put('f-wire', wireHtml(f.wire)); put('f-sum', sumHtml(f));
}
D.addEventListener('md:edition', e => all(e.detail));
if (M.ed) all(M.ed);
})();
