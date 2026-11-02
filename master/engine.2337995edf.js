/* Master Desk terminal, the Engine tab: int1's engine.json, the analysis engine's screen (a momentum rank, a loser-risk rank
   and a typical move for every name it scores), in GrokBot Desk's Opportunity Ranker form (g-d-v-ranker-top): a main
   bar, a thin sub-bar, the numbers and the change. The board's and Watching's names are pinned on top and link to their
   cards. viz.js loads this file on the tab's first open; #e=SYM opens the tab and this file finds the name. */
(() => {
const D = document, M = window.MD, V = window.MDV, el = id => D.getElementById(id);
const host = el('e-rank');
if (!host || !M || !V) return;
const esc = M.esc, isN = M.isN, num = M.num, STEP = 60, TIERS = ['liquid', 'small', 'micro', 'nano'];
const st = {scope: 'all', tier: '', veto: 0, sort: 'mom', q: '', n: STEP};
let E = null, R = [], ED = M.ed, busy = 0, raf = 0, said = '';

// engine.json: {as_of, n, cols, rows}; a row's fields by their column names, so a new column changes nothing here
function rows(j) {
  const ix = {};
  j.cols.forEach((c, i) => { ix[c] = i; });
  const g = (r, k) => ix[k] == null ? null : r[ix[k]];
  return j.rows.filter(r => Array.isArray(r) && typeof g(r, 'sym') === 'string').map(r => ({sym: g(r, 'sym'), mom: g(r, 'mom'), risk: g(r, 'risk'), em: g(r, 'em'),
    dmom: g(r, 'dmom'), drisk: g(r, 'drisk'), tier: g(r, 'tier'), veto: g(r, 'veto') === true}));
}
// the board's names link to their cards (#bs-SYM), Watching's to its list; the words are the edition's own
function pins() {
  const d = ED || M.ed || {}, out = [];
  (d.setups || []).slice(0, 5).forEach(s => out.push({sym: s.symbol, act: s.action, href: '#bs-' + encodeURIComponent(s.symbol), k: 'board'}));
  (d.watching || []).forEach(w => { if (!out.some(p => p.sym === w.symbol)) out.push({sym: w.symbol, act: w.action, href: '#watch', k: 'watch'}); });
  return out;
}
// the forward test's status, stated once: the edition's own short field (int1)
function status() {
  const d = ED || M.ed || {}, s = [...(d.setups || []), ...(d.watching || [])].map(x => x.engine && x.engine.status).find(Boolean);
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}
const dl = v => !isN(v) || !v ? '' : '<small class="' + (v > 0 ? 'up">▲' : 'dn">▼') + num(Math.abs(v), 0) + '</small>';
const mv = v => isN(v) ? '±' + num(v, 1) + '%' : '—';
function row(r, i, p) {          // the symbol, its chips and a link are read as they are; the bars and numbers as one sentence
  const sr = 'momentum rank ' + (isN(r.mom) ? r.mom : 'none') + (isN(r.dmom) && r.dmom ? ' (' + num(r.dmom, 0, 1) + ')' : '') + ', loser-risk rank ' + (isN(r.risk) ? r.risk : 'none') +
    (isN(r.drisk) && r.drisk ? ' (' + num(r.drisk, 0, 1) + ')' : '') + ', typical move ' + mv(r.em) + ' over 20 sessions';
  return '<li class="er' + (p ? ' ep' : '') + '" id="e-' + esc(r.sym) + '"><span class="en" aria-hidden="true">' + (p ? '' : i) + '</span><span class="es">' +
    (p ? '<a href="' + p.href + '"><b>' + esc(r.sym) + '</b></a>' : '<b>' + esc(r.sym) + '</b>') + (r.tier ? '<i class="et">' + esc(r.tier) + '</i>' : '') + (r.veto ? '<i class="ev">veto</i>' : '') +
    (p ? '<i class="ea' + (p.k === 'watch' ? ' w' : '') + '">' + esc(p.act) + '</i>' : '') + '<span class="sr">: ' + sr + '</span></span><span class="eb" aria-hidden="true"><span class="e1"><i data-pw="' + (isN(r.mom) ? r.mom : 0) +
    '"></i></span><span class="e2"><i data-pw="' + (isN(r.risk) ? r.risk : 0) + '"></i></span></span><span class="eu" aria-hidden="true"><b>' + (isN(r.mom) ? r.mom : '—') + '</b>' + dl(r.dmom) +
    '</span><span class="ex" aria-hidden="true"><span>risk <b>' + (isN(r.risk) ? r.risk : '—') + '</b></span><span>' + mv(r.em) + '</span></span></li>';
}
const by = {mom: (a, b) => (b.mom ?? -1) - (a.mom ?? -1) || (a.risk ?? 101) - (b.risk ?? 101) || (a.sym < b.sym ? -1 : 1),
  risk: (a, b) => (a.risk ?? 101) - (b.risk ?? 101) || (b.mom ?? -1) - (a.mom ?? -1) || (a.sym < b.sym ? -1 : 1)};
function list() {
  const P = pins(), pin = {}, q = st.q;
  P.forEach(p => { pin[p.sym] = p; });
  const ok = r => (!st.tier || r.tier === st.tier) && (!st.veto || r.veto) && (!q || r.sym.startsWith(q)) &&
    (st.scope === 'all' || pin[r.sym] && pin[r.sym].k === st.scope);
  const S = R.filter(ok).sort(by[st.sort]), top = st.scope === 'all' && !q ? S.filter(r => pin[r.sym]) : [], rest = top.length ? S.filter(r => !pin[r.sym]) : S;
  const shown = rest.slice(0, st.n);
  let h = top.length ? '<li class="eh">On the board and Watching</li>' + top.map(r => row(r, 0, pin[r.sym])).join('') + '<li class="eh">' + (st.sort === 'risk' ? 'Lowest loser risk' : 'Top momentum') + '</li>' : '';
  h += shown.map((r, i) => row(r, i + 1, st.scope !== 'all' || q ? pin[r.sym] : null)).join('');
  if (!S.length) h = '<li class="eh">' + (q ? 'No name starting ' + esc(q) + ' on the engine’s screen.' : 'No name in this view.') + '</li>';
  el('e-list').innerHTML = h;
  el('e-list').querySelectorAll('[data-pw]').forEach(e => { e.style.width = e.dataset.pw + '%'; });    // CSSOM: the CSP bars style attributes
  const more = el('e-more'), left = rest.length - shown.length;
  more.hidden = left <= 0;
  more.textContent = 'Show ' + Math.min(STEP, left) + ' more of ' + num(left, 0);
  const t = num(S.length, 0) + (S.length === 1 ? ' name scored' : ' names scored');
  if (t !== said) { said = t; el('e-n').textContent = t; }
}
const chip = (k, v, t, on, n) => '<button type="button" data-' + k + '="' + v + '" aria-pressed="' + on + '">' + t + (isN(n) ? ' <span class="mu">' + num(n, 0) + '</span>' : '') + '</button>';
function render() {
  const f = D.activeElement && D.activeElement.id === 'e-q', P = pins(), cnt = k => P.filter(p => p.k === k && R.some(r => r.sym === p.sym)).length, nv = R.filter(r => r.veto).length, tiers = TIERS.filter(t => R.some(r => r.tier === t)), s = status();
  host.innerHTML = '<div class="shd"><div class="sht"><p class="kick">The analysis engine</p><h2 id="h-e-rank">Engine</h2><p class="sub">Momentum rank · loser-risk rank · typical move</p></div><span class="pv">' +
    esc(M.et(E.as_of).md + ' close · ' + num(R.length, 0) + ' names scored') + '</span></div><div class="card">' + (s ? '<p class="es0"><span class="bdg">' + esc(s) + '</span></p>' : '') +
    '<div class="ef"><span class="tg" role="group" aria-label="Show">' + chip('scope', 'all', 'All', st.scope === 'all') + (cnt('board') ? chip('scope', 'board', 'On the board', st.scope === 'board', cnt('board')) : '') +
    (cnt('watch') ? chip('scope', 'watch', 'Watching', st.scope === 'watch', cnt('watch')) : '') + '</span><span class="tg" role="group" aria-label="Order">' + chip('sort', 'mom', 'Top momentum', st.sort === 'mom') +
    chip('sort', 'risk', 'Lowest risk', st.sort === 'risk') + '</span>' + (tiers.length > 1 ? '<span class="tg" role="group" aria-label="Tier">' + tiers.map(t => chip('tier', t, t.charAt(0).toUpperCase() + t.slice(1), st.tier === t)).join('') + '</span>' : '') +
    (nv ? '<span class="tg" role="group" aria-label="Veto">' + chip('veto', '1', 'Veto', !!st.veto, nv) + '</span>' : '') + '</div><form class="lf" role="search" id="e-f"><label class="sr" for="e-q">Find a name</label><input id="e-q" class="lq" type="search" inputmode="search" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="Symbol, e.g. AAPL" maxlength="12" value="' + esc(st.q) +
    '"></form><p class="mu en0" id="e-n" aria-live="polite"></p><ol class="el" id="e-list"></ol><button class="more" type="button" id="e-more" hidden></button>' +
    '<p class="lg0"><span><i class="k1"></i>Momentum rank, 0-100</span><span><i class="k2"></i>Loser-risk rank, higher = riskier</span><span>±: typical move over 20 sessions · ▲▼ change since the session before' + (nv ? ' · veto: its loser-risk veto applies' : '') + '</span></p></div>';
  host.hidden = false;
  said = '';
  list();
  V.jump();
  if (f) el('e-q').focus({preventScroll: true});
}
// #e=SYM: the name, found (the search narrows to it), scrolled to and tinted
function find() {
  const h = decodeURIComponent(location.hash.slice(1));
  if (!h.startsWith('e=') || !E) return;
  const s = h.slice(2).toUpperCase();
  if (!R.some(r => r.sym === s)) return;
  st.q = s;
  st.scope = 'all';
  render();
  const n = el('e-' + s);
  if (n) { n.scrollIntoView({block: 'center'}); n.classList.add('tint'); }
}
// the edition: at hand, or (a deep link to #e=SYM) the first one drawn; a page that never gets one draws without its pins
const ed = () => ED || M.ed ? Promise.resolve() : new Promise(r => { D.addEventListener('md:edition', r, {once: true}); setTimeout(r, 4e3); });
function load() {
  if (busy) return;
  busy = 1;
  Promise.all([fetch('engine.json', {cache: 'no-cache'}).then(r => r.ok ? r.json() : null).catch(() => null), ed()]).then(([j]) => {
    busy = 0;
    if (!j || !Array.isArray(j.cols) || !Array.isArray(j.rows) || typeof j.as_of !== 'string') {
      if (!E) { host.innerHTML = '<div class="card"><p class="mu">The engine’s first screen runs after the close (7:35 PM ET) and appears here.</p></div>'; host.hidden = false; }
      return;
    }
    if (E && E.as_of === j.as_of && E.n === j.n) return;
    E = j;
    R = rows(j);
    render();
    find();
  });
}
host.addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b || !E) return;
  const d = b.dataset;
  if (b.id === 'e-more') { st.n += STEP; return list(); }
  if (d.scope) st.scope = d.scope;
  else if (d.sort) st.sort = d.sort;
  else if (d.tier) st.tier = st.tier === d.tier ? '' : d.tier;
  else if (d.veto) st.veto = !st.veto;
  else return;
  st.n = STEP;
  const k = Object.keys(d)[0];
  host.querySelectorAll('[data-' + k + ']').forEach(x => x.setAttribute('aria-pressed', k === 'tier' ? x.dataset.tier === st.tier : k === 'veto' ? !!st.veto : x.dataset[k] === st[k]));
  list();
});
host.addEventListener('input', e => {
  if (e.target.id !== 'e-q') return;
  st.q = e.target.value.trim().toUpperCase();
  st.n = STEP;
  if (!raf) raf = requestAnimationFrame(() => { raf = 0; list(); });
});
host.addEventListener('submit', e => { e.preventDefault(); });
addEventListener('hashchange', find);
D.addEventListener('md:tab', e => { if (e.detail === 'engine' && !E) load(); });
D.addEventListener('md:edition', e => { ED = e.detail; if (E) { render(); load(); } });     // the pins and the status follow the edition
// (app.js names its edition only after this event: the event's own is the new one)
if (V.tab() === 'engine') load();
})();
