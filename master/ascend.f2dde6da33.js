/* Master Desk terminal, the ascension layer (deferred after viz.js). The view contract on the page: a state chip per
   section (Updated / Stale / Market closed / Waiting) from panels.json, never a stale value shown as current; one
   collapsed "What is this?" per section, after the chart; the Hub (every panel's state, source and limitation,
   searchable, all / published / awaiting); Market Pulse from pulse.json (SPY QQQ IWM SMH 5-minute lines indexed to the
   first displayed close, 1D / 5D; sectors Map / Bars; movers) with Galath-style SVG gauges and donuts. Every fetch has a
   20 s deadline that includes reading the body. Charts picture the subject from real data: no honest series, no chart. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id), isN = v => typeof v === 'number' && isFinite(v);
if (!M) return;
const esc = M.esc, f1 = v => (+v).toFixed(1), DEADLINE = 2e4, GAP = 900;
const C = {SPY: '#2bb07f', QQQ: '#4a8fe0', IWM: '#e0913a', SMH: '#9467d0'};
const st = {range: '1D', sect: 'map', q: '', f: 'all'};
let pan = null, pul = null, busy = 0;

// a fetch whose one deadline covers the headers and the whole body (Codex's timed-fetch)
function get(url) {
  const ac = new AbortController(), t = setTimeout(() => ac.abort(), DEADLINE);
  return fetch(url, {cache: 'no-cache', signal: ac.signal}).then(r => r.ok ? r.json() : null)
    .catch(() => null).finally(() => clearTimeout(t));
}
const sess = () => (M.ed && M.ed.session && M.ed.session.state) || '';
const clock = v => !v ? '' : v.length === 10 ? M.day(v) : M.wd(v) + ' ET';
// the chip's words: Updated (live, market open), Market closed (live, out of the session), Stale, Waiting
function chipOf(v) {
  if (!v) return null;
  if (v.state === 'live') return sess() === 'open' ? ['ok', 'Updated ' + clock(v.as_of)] : ['cl', 'Market closed · ' + clock(v.as_of)];
  if (v.state === 'stale') return ['st', 'Stale · as of ' + (clock(v.as_of) || 'unknown')];
  if (v.state === 'ungraded') return ['ug', 'Ungraded · ' + clock(v.as_of)];
  return ['wt', v.state === 'waiting' ? 'Waiting' : 'Unavailable'];
}
const chipHtml = (c, why) => '<span class="vsc vs-' + c[0] + '"' + (why ? ' title="' + esc(why) + '"' : '') + '><i aria-hidden="true"></i>' + esc(c[1]) + '</span>';

// ---- every section: its state chip, one "What is this?", the chart first ------------------------------------------------
function tidy() {
  D.querySelectorAll('#grid section').forEach(s => {
    const wh = [...s.children].filter(x => x.matches('details.wh'));
    wh.slice(1).forEach(x => x.remove());
    const w = wh[0], cards = [...s.children].filter(x => x.matches('.card,.cp'));
    const lastCard = cards[cards.length - 1];
    if (w && lastCard && w.compareDocumentPosition(lastCard) & Node.DOCUMENT_POSITION_FOLLOWING) lastCard.after(w);
    const row = pan && pan.byId[s.id], c = row && chipOf(row), head = s.querySelector(':scope > .shd');
    let chip = s.querySelector(':scope > .shd > .vsc, :scope > .vsl > .vsc');
    if (!c) return;
    const h = chipHtml(c, row.why);
    if (chip && chip.outerHTML === h) return;
    if (chip) chip.outerHTML = h;
    else if (head) head.insertAdjacentHTML('beforeend', h);
    else s.insertAdjacentHTML('afterbegin', '<p class="vsl">' + h + '</p>');
    s.classList.toggle('vs-stale', row.state === 'stale');
  });
}
let tq = 0;
new MutationObserver(() => { if (!tq) tq = requestAnimationFrame(() => { tq = 0; if (typeof mapX === 'function' && M.ed) { mapX(); boardX(); if (!el('d-book') && M.ed.book) book(); } tidy(); }); }).observe(el('grid'), {childList: true, subtree: true});

// ---- the Hub: the panel census, as the producer wrote it ------------------------------------------------------------------
const PUB = s => s === 'live' || s === 'stale' || s === 'ungraded';
function hub() {
  const n = el('hubl');
  if (!n || !pan) return;
  const q = st.q.trim().toLowerCase(), rows = pan.panels.filter(r => (st.f === 'all' || (st.f === 'published') === PUB(r.state)) &&
    (!q || (r.title + ' ' + r.source + ' ' + r.limitation + ' ' + r.tab).toLowerCase().includes(q)));
  const c = pan.panels.reduce((a, r) => { a[PUB(r.state) ? 1 : 0]++; return a; }, [0, 0]);
  el('hubn').textContent = c[1] + ' published · ' + c[0] + ' awaiting · as of ' + M.wd(pan.generated_at) + ' ET';
  n.innerHTML = rows.length ? rows.map(r => '<li class="a-hc"><a href="#' + esc(r.id) + '"><span class="a-ht">' + esc(r.title) + '</span>' +
    chipHtml(chipOf(r), r.why) + '<span class="a-hs">' + esc(r.source) + '</span><span class="a-hl">' + esc(r.limitation) + '</span>' +
    (r.state === 'stale' && r.why ? '<span class="a-hw">' + esc(r.why) + '</span>' : '') + '</a></li>').join('') : '<li class="mu">No panel matches.</li>';
  D.querySelectorAll('#hubf button').forEach(b => b.setAttribute('aria-pressed', b.dataset.f === st.f));
}
const hf = el('hubq');
if (hf) hf.addEventListener('input', () => { st.q = hf.value; hub(); });
const hb = el('hubf');
if (hb) hb.addEventListener('click', e => { const b = e.target.closest('button'); if (b) { st.f = b.dataset.f; hub(); } });

// ---- Galath-style SVG helpers: gauge (a half dial with zones), donut ----------------------------------------------------
const arc = (cx, cy, r, a0, a1) => { const p = a => [cx + r * Math.cos(a), cy + r * Math.sin(a)], [x0, y0] = p(a0), [x1, y1] = p(a1);
  return 'M' + f1(x0) + ' ' + f1(y0) + 'A' + r + ' ' + r + ' 0 ' + (a1 - a0 > Math.PI ? 1 : 0) + ' 1 ' + f1(x1) + ' ' + f1(y1); };
function gauge(v, lo, hi, label, val) {
  const t = Math.max(0, Math.min(1, (v - lo) / (hi - lo))), a = Math.PI + t * Math.PI, nx = 60 + 40 * Math.cos(a), ny = 62 + 40 * Math.sin(a);
  return '<svg class="a-gg" viewBox="0 0 120 80" role="img" aria-label="' + esc(label + ' ' + val) + '">' +
    '<path class="a-gz a-gz-d" d="' + arc(60, 62, 46, Math.PI, Math.PI * 1.4) + '"/><path class="a-gz a-gz-n" d="' + arc(60, 62, 46, Math.PI * 1.4, Math.PI * 1.6) + '"/>' +
    '<path class="a-gz a-gz-u" d="' + arc(60, 62, 46, Math.PI * 1.6, Math.PI * 2) + '"/><line class="a-gn" x1="60" y1="62" x2="' + f1(nx) + '" y2="' + f1(ny) + '"/>' +
    '<circle class="a-gc" cx="60" cy="62" r="4"/><text class="a-gv" x="60" y="78" text-anchor="middle">' + esc(val) + '</text></svg>';
}
function donut(parts, label) {           // parts: [[value, class, name]]; nothing drawn without a positive total
  const tot = parts.reduce((a, p) => a + p[0], 0);
  if (!(tot > 0)) return '';
  let a = -Math.PI / 2, g = '';
  parts.forEach(p => { if (!p[0]) return; const b = a + 2 * Math.PI * p[0] / tot - 1e-4; g += '<path class="a-dn a-' + p[1] + '" d="' + arc(50, 50, 38, a, b) + '"/>'; a = b; });
  return '<svg class="a-dnt" viewBox="0 0 100 100" role="img" aria-label="' + esc(label) + '">' + g +
    '<text x="50" y="55" text-anchor="middle" class="a-dv">' + parts.map(p => p[0]).join(' / ') + '</text></svg>';
}
window.MDA = {gauge, donut};

// ---- Market Pulse ------------------------------------------------------------------------------------------------------
const etDay = t => M.et(t * 1e3).key;
// the series a range shows, each indexed to its first displayed close: [[t, %] ...] (null breaks the line at a gap)
function indexed(s, range) {
  if (!s || !s.t || s.t.length < 2) return null;
  let i0 = 0;
  if (range === '1D') { const d = etDay(s.t[s.t.length - 1]); while (etDay(s.t[i0]) !== d) i0++; }
  const t = s.t.slice(i0), c = s.c.slice(i0), b = c[0];
  return t.length >= 2 && b > 0 ? t.map((x, i) => [x, (c[i] / b - 1) * 100]) : null;
}
function lines(W) {
  const ser = Object.keys(C).map(k => [k, indexed(pul.lines[k], st.range)]).filter(x => x[1]);
  if (!ser.length) return '';
  const ts = [...new Set(ser.flatMap(x => x[1].map(p => p[0])))].sort((a, b) => a - b), ix = new Map(ts.map((t, i) => [t, i]));
  const ys = ser.flatMap(x => x[1].map(p => p[1])), lo = Math.min(0, ...ys), hi = Math.max(0, ...ys), pad = (hi - lo) * .08 || .5;
  const H = 210, L = 8, R = 52, T = 10, B = 24, X = i => L + (W - L - R) * i / Math.max(1, ts.length - 1), Y = v => T + (H - T - B) * (hi + pad - v) / (hi - lo + 2 * pad);
  let g = '<line class="a-z0" x1="' + L + '" x2="' + (W - R) + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"/>';
  [lo, hi].forEach(v => { g += '<text class="a-ax" x="' + (W - R + 6) + '" y="' + f1(Y(v) + 4) + '">' + M.pct(v, 1) + '</text>'; });
  const days = []; ts.forEach((t, i) => { if (!i || etDay(t) !== etDay(ts[i - 1])) days.push(i); });
  if (st.range === '5D') days.forEach(i => { g += '<text class="a-ax" x="' + f1(X(i) + 2) + '" y="' + (H - 6) + '">' + esc(M.et(ts[i] * 1e3).md) + '</text>'; });
  else g += '<text class="a-ax" x="' + L + '" y="' + (H - 6) + '">' + esc(M.et(ts[0] * 1e3).hm) + '</text><text class="a-ax" x="' + (W - R) + '" y="' + (H - 6) + '" text-anchor="end">' + esc(M.et(ts[ts.length - 1] * 1e3).hm) + ' ET</text>';
  ser.forEach(([k, p]) => {
    let d = '';
    p.forEach((q, i) => { d += (i && q[0] - p[i - 1][0] <= GAP ? 'L' : 'M') + f1(X(ix.get(q[0]))) + ' ' + f1(Y(q[1])); });
    const e = p[p.length - 1];
    g += '<path class="a-pl" stroke="' + C[k] + '" d="' + d + '"/><circle cx="' + f1(X(ix.get(e[0]))) + '" cy="' + f1(Y(e[1])) + '" r="3" fill="' + C[k] + '"/>';
  });
  return '<svg class="a-pls" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="' +
    esc(ser.map(([k, p]) => k + ' ' + M.pct(p[p.length - 1][1], 2)).join(', ') + ', ' + st.range) + '">' + g + '</svg>';
}
const tog = (k, opts) => '<div class="a-tg" role="group">' + opts.map(o => '<button type="button" data-' + k + '="' + o[0] + '" aria-pressed="' + (st[k] === o[0]) + '">' + o[1] + '</button>').join('') + '</div>';
const head = (id, kick, title) => '<div class="shd"><div class="sht"><p class="kick">' + kick + '</p><h2 id="h-' + id + '">' + title + '</h2></div></div>';
const what = t => '<details class="wh"><summary>What is this?</summary><p>' + t + '</p></details>';
function pulseLive() {
  const n = el('m-live');
  if (!n) return;
  const keys = Object.keys(pul.lines || {});
  if (!keys.length) { n.innerHTML = head('m-live', 'Intraday', 'Market Pulse') + '<div class="card"><p class="mu">Waiting for the session’s 5-minute bars.</p></div>'; n.hidden = false; return; }
  const W = Math.max(300, Math.round((n.clientWidth || el('main').clientWidth) - 34));
  const gg = keys.map(k => { const s = pul.lines[k], p = isN(s.prev) && s.prev > 0 ? (s.c[s.c.length - 1] / s.prev - 1) * 100 : null;
    return p === null ? '' : '<div class="a-gi">' + gauge(p, -3, 3, k + ' on the session', M.pct(p, 2)) + '<b>' + k + '</b></div>'; }).join('');
  n.innerHTML = head('m-live', 'SPY · QQQ · IWM · SMH', 'Market Pulse') + '<div class="card">' + tog('range', [['1D', '1D'], ['5D', '5D']]) +
    '<div class="a-plw" id="m-live-c">' + lines(W) + '</div><p class="a-lg">' + keys.map(k => '<span><i data-c="' + C[k] + '"></i>' + k + '</span>').join('') + '</p>' +
    (gg ? '<div class="a-gw">' + gg + '</div>' : '') + '</div>' +
    what('Each fund’s 5-minute closes, indexed to the first close shown: 1D is the latest session, 5D the last five. The dials are each fund against the prior session’s close. Regular hours only; the line breaks across the overnight gap.');
  n.querySelectorAll('i[data-c]').forEach(e => { e.style.background = e.dataset.c; });
  n.hidden = false;
}
const tone = p => p >= 0 ? 'u' : 'd', lvl = p => Math.min(4, Math.ceil(Math.abs(p) / .5));
function pulseSect() {
  const n = el('m-sect'), s = pul.sectors || [];
  if (!n) return;
  if (!s.length) { n.hidden = true; return; }
  const r2 = v => Math.round(v * 100) / 100, up = r2(s.reduce((a, x) => a + Math.max(0, x.pct), 0)), dn = r2(s.reduce((a, x) => a - Math.min(0, x.pct), 0)), mx = Math.max(...s.map(x => Math.abs(x.pct)), .01);
  const body = st.sect === 'map' ? '<div class="a-smap">' + s.map(x => '<div class="a-stl t' + tone(x.pct) + lvl(x.pct) + '"><b>' + esc(x.name) + '</b><span>' + M.pct(x.pct, 2) + '</span></div>').join('') + '</div>'
    : '<ol class="a-sbars">' + s.map(x => '<li><span class="a-sn">' + esc(x.name) + '</span><span class="a-sb"><i class="' + tone(x.pct) + '" data-w="' + f1(Math.abs(x.pct) / mx * 50) + '"></i></span><span class="a-sv">' + M.pct(x.pct, 2) + '</span></li>').join('') + '</ol>';
  n.innerHTML = head('m-sect', 'Sector funds on the session', 'Sectors today') + '<div class="card">' + tog('sect', [['map', 'Map'], ['bars', 'Bars']]) +
    '<div class="a-sw">' + body + '<div class="a-sdn">' + donut([[up, 'du', 'up'], [dn, 'dd', 'down']], 'Points of sector moves: ' + up + ' up, ' + dn + ' down') + '<p class="mu">points up / down</p></div></div></div>' +
    what('Each sector fund’s latest 5-minute close against its prior session’s close. Map colours by size of the move; Bars rank them.');
  n.querySelectorAll('[data-w]').forEach(e => { e.style.marginLeft = e.classList.contains('u') ? '50%' : (50 - e.dataset.w) + '%'; e.style.width = e.dataset.w + '%'; });
  n.hidden = false;
}
function pulseMovers() {
  const n = el('m-movers'), m = pul.movers;
  if (!n) return;
  if (!m || !(m.up.length || m.down.length)) { n.hidden = true; return; }
  const li = a => a.map(x => '<li><b>' + esc(x.sym) + '</b><span class="' + tone(x.pct) + '">' + M.pct(x.pct, 2) + '</span></li>').join('');
  n.innerHTML = head('m-movers', 'Roster · ' + esc(M.day(m.as_of)), 'Movers') + '<div class="card a-mvr"><div><h3>Up</h3><ol>' + li(m.up) + '</ol></div><div><h3>Down</h3><ol>' + li(m.down) + '</ol></div></div>' +
    what('The roster’s biggest closes on the latest completed session, names priced at $5 or more.');
  n.hidden = false;
}

// ---- Market Mood (the edition's `mood`: the nine-gauge engine) ---------------------------------------------------------
function psych() {
  const n = el('m-psy'), m = M.ed && M.ed.mood;
  if (!n) return;
  if (!m || !m.gauges) { n.hidden = true; return; }
  const ks = Object.keys(m.gauges).sort((a, b) => (+a.slice(1)) - (+b.slice(1)));
  const row = k => { const g = m.gauges[k], p = isN(g.percentile) ? Math.max(0, Math.min(100, g.percentile)) : null, live = g.state === 'live';
    const why = live ? '' : (g.flags && g.flags.length ? g.flags.join(', ') : g.state === 'stale' ? 'older than two of its cadence periods' : 'no reading');
    return '<li class="a-mg' + (live ? '' : ' a-off') + '"><span class="a-mn">' + esc(g.name || k) + '</span><span class="a-sb">' + (p !== null && g.state !== 'absent' ? '<i class="a-pb" data-w="' + f1(p) + '"></i>' : '') + '</span>' +
      '<span class="a-mv">' + (p !== null && g.state !== 'absent' ? f1(p) : '—') + '</span><span class="a-mb">' + esc(g.band || 'NO BAND') + '</span>' +
      chipHtml(chipOf({state: g.state === 'absent' ? 'unavailable' : g.state, as_of: g.as_of}), why) +
      (why ? '<span class="a-mw">' + esc(why) + '</span>' : '') + '</li>'; };
  const c = isN(m.composite) ? m.composite : null;
  n.innerHTML = head('m-psy', 'Nine gauges · percentile of their own history', 'Market Mood') + '<div class="card"><div class="a-mh">' +
    (c !== null ? gauge(c, 0, 100, 'Composite', f1(c)) : '') + '<p class="a-rw">' + esc(m.regime || '') + '</p></div><ol class="a-ml">' + ks.map(row).join('') + '</ol></div>' +
    what('Nine market-psychology gauges, each read as a percentile of its own history (0 fear, 100 greed); a gauge with fewer than 250 observations has no band. The composite combines the core gauges that report. Absent gauges are named with their reason.');
  n.querySelectorAll('.a-pb[data-w]').forEach(e => { e.style.width = e.dataset.w + '%'; });
  n.hidden = false;
}

// ---- the Morgue Engine's catch-up keys: the Map's label, coverage, DIX lag and Wall Check; the Board's gate reasons and
// refusals; Gamma Ladder, Pin Watch, Insider Wire and News. Each section's chip is its own status and as-of. -------------
const mg = () => (M.ed && M.ed.morgue) || null, ok = b => b && (b.status === 'ok' || b.status === 'stale');
const usd = v => isN(v) ? (v >= 1e6 ? '$' + f1(v / 1e6) + 'M' : '$' + Math.round(v / 1e3) + 'K') : '—';
function sub(id, after, h) {         // an addition inside an existing section (funnel.js owns the rest), kept once
  const s = el(after);
  if (!s) return;
  let n = el(id);
  if (!h) { if (n) n.remove(); return; }
  if (!n) { n = D.createElement('div'); n.id = id; n.className = 'card a-x'; }
  if (n._h !== h) { n.innerHTML = h; n._h = h; }
  const w = s.querySelector(':scope > details.wh');
  if (n.parentElement !== s) w ? w.before(n) : s.appendChild(n);
}
function mapX() {
  const m = mg() && mg().map;
  if (!ok(m)) return sub('f-map-x', 'f-map', '');
  const cards = Object.entries(m.cards || {}).filter(([, c]) => c && c.coverage);
  const wc = Object.entries(m.wall_check || {}).filter(([, w]) => w && w.graded_session);
  const d = m.dix || {};
  sub('f-map-x', 'f-map', '<p class="a-lab">' + esc(m.label_short || 'modelled, not observed') + '</p>' +
    (cards.length ? '<p class="mu">' + cards.map(([k, c]) => '<b>' + esc(k) + '</b> ' + esc(c.coverage)).join(' · ') + '</p>' : '') +
    (d.lag_label ? '<p class="mu">DIX: ' + esc(d.lag_label) + '</p>' : '') +
    (wc.length ? '<h3 class="a-h3">Wall Check · ' + esc(M.day(wc[0][1].graded_session)) + '</h3><ul class="a-wc">' + wc.map(([k, w]) => '<li><b>' + esc(k) + '</b>' +
      [['Call wall', w.call_wall_held], ['Put wall', w.put_wall_held], ['Above flip', w.closed_above_flip]].map(x => '<span class="' + (x[1] === true ? 'u' : x[1] === false ? 'd' : 'mu') + '">' + x[0] + (x[1] === true ? ' held' : x[1] === false ? ' broke' : ' —') + '</span>').join('') +
      (w.grade ? '<em>' + esc(w.grade) + '</em>' : '') + '</li>').join('') + '</ul>' : ''));
}
function boardX() {
  const b = mg() && mg().board;
  if (!ok(b)) return sub('f-board-x', 'f-board', '');
  const fc = Object.entries(b.fail_counts || {}).filter(x => isN(x[1]) && x[1] > 0).sort((x, y) => y[1] - x[1]);
  const rows = (b.top || []).filter(r => r.gate_reason).slice(0, 8);
  sub('f-board-x', 'f-board', (rows.length ? '<h3 class="a-h3">Why each passed or failed</h3><ul class="a-gr">' + rows.map(r => '<li><b>' + esc(r.symbol) + '</b><span class="' + (r.qualified ? 'u' : 'mu') + '">' + esc(r.gate_reason) + '</span></li>').join('') + '</ul>' : '') +
    (fc.length ? '<p class="mu">Refusals: ' + fc.map(x => esc(x[0].replace(/_/g, ' ')) + ' ' + x[1]).join(' · ') + '</p>' : ''));
}
function ladderSvg(L, W) {          // net gamma per strike, the subject itself; no strikes, no chart
  const r = (L || []).filter(x => isN(x.strike) && isN(x.net_gex_b)).sort((a, b) => b.strike - a.strike);
  if (r.length < 2) return '';
  const mx = Math.max(...r.map(x => Math.abs(x.net_gex_b)), 1e-9), rh = 18, H = r.length * rh + 6, c = W / 2, half = W / 2 - 105;
  return '<svg class="a-lad" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="Net gamma by strike">' + r.map((x, i) => {
    const w = Math.abs(x.net_gex_b) / mx * half, y = 3 + i * rh;
    return '<rect class="' + (x.net_gex_b >= 0 ? 'a-lu' : 'a-ld') + '" x="' + f1(x.net_gex_b >= 0 ? c : c - w) + '" y="' + y + '" width="' + f1(Math.max(1, w)) + '" height="' + (rh - 5) + '" rx="2"/>' +
      '<text class="a-ax" x="4" y="' + (y + 11) + '">' + esc(String(x.strike)) + '</text><text class="a-ax" x="' + (W - 4) + '" y="' + (y + 11) + '" text-anchor="end">' + num(x.net_gex_b) + 'B' + (isN(x.pull) ? ' · ' + Math.round(x.pull * 100) + '%' : '') + '</text>';
  }).join('') + '<line class="a-z0" x1="' + c + '" x2="' + c + '" y1="0" y2="' + H + '"/></svg>';
}
const num = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(2);
function morgueSecs() {
  const m = mg(), map = m && m.map, cards = map && ok(map) ? Object.entries(map.cards || {}) : [];
  const set = (id, h) => { const n = el(id); if (!n) return; if (n._h !== h) { n.innerHTML = h; n._h = h; } n.hidden = !h; };
  const W = Math.max(280, Math.round((el('main').clientWidth || 360) - 34));
  const lad = cards.filter(([, c]) => c.ladder && c.ladder.length >= 2);
  set('m-ladder', lad.length ? head('m-ladder', esc(map.label_short || 'modelled, not observed'), 'Gamma Ladder') + lad.map(([k, c]) => '<div class="card"><h3 class="a-h3">' + esc(k) +
    (isN(c.spot) ? ' · spot ' + c.spot.toFixed(2) : '') + '</h3>' + ladderSvg(c.ladder, Math.min(W, 640)) + '</div>').join('') +
    what('Modelled dealer gamma at each strike within 5% of the spot, in billions per 1% move: right of the line adds stability, left accelerates moves. The share is the strike’s pull on the band.') : '');
  const pins = cards.filter(([, c]) => c.pins && c.pins.length);
  set('m-pins', pins.length ? head('m-pins', 'Six nearest expiries', 'Expiry Pin Watch') + pins.map(([k, c]) => '<div class="card"><h3 class="a-h3">' + esc(k) + '</h3><div class="tw"><table class="t a-pt"><thead><tr><th>Expiry</th><th class="r">Pin</th><th class="r">From spot</th><th class="r">Call max</th><th class="r">Put max</th></tr></thead><tbody>' +
    c.pins.map(p => '<tr><th scope="row">' + esc(M.et(p.expiry).md) + '</th><td class="r">' + esc(String(p.pin_strike ?? '—')) + '</td><td class="r">' + (isN(p.distance_pct) ? M.pct(p.distance_pct, 1) : '—') + '</td><td class="r">' + esc(String(p.call_strike ?? '—')) + '</td><td class="r">' + esc(String(p.put_strike ?? '—')) + '</td></tr>').join('') + '</tbody></table></div></div>').join('') +
    what('For each of the six nearest expiries, the strike with the most open interest (where price tends to be pulled into expiry), and the largest call and put strikes, from the prior close.') : '');
  const iw = m && m.insider_wire, cl = ok(iw) ? (iw.clusters || []) : [];
  set('m-insider', ok(iw) ? head('m-insider', 'SEC Form 4 · cluster buying', 'Insider Wire') + '<div class="card">' + (cl.length ? '<ul class="a-iw">' + cl.map(c => '<li><b>' + esc(c.symbol) + '</b><span>' + c.insiders + ' insiders · ' + c.purchases + ' buys · ' + usd(c.value_usd) + '</span><span class="mu">' + esc(M.et(c.window_start).md) + '–' + esc(M.et(c.window_end).md) + '</span></li>').join('') + '</ul>'
    : '<p class="mu">No cluster buying in the last 30 days.</p>') + '</div>' + what('Names where three or more insiders bought on the open market within 30 days, from their Form 4 filings.') : '');
  const nw = m && m.news, hl = ok(nw) ? (nw.headlines || []).slice(0, 12) : [];
  set('m-news', hl.length ? head('m-news', 'Alpaca News · headline direction', 'News') + '<div class="card"><ul class="a-nw">' + hl.map(h => '<li><span class="a-nd ' + (h.direction > 0 || h.direction === 'positive' ? 'u' : h.direction < 0 || h.direction === 'negative' ? 'd' : 'mu') + '">' + (h.direction > 0 || h.direction === 'positive' ? '▲' : h.direction < 0 || h.direction === 'negative' ? '▼' : '•') + '</span><b>' + esc(h.symbol) + '</b><span>' + esc(h.headline) + '</span><time class="mu">' + esc(M.wd(h.created_at)) + '</time></li>').join('') + '</ul></div>' +
    what('Recent headlines for the desk’s names, each marked up or down by fixed word lists on the headline alone.') : '');
  mapX(); boardX();
}
function pulseAll() { if (pul) { pulseLive(); pulseSect(); pulseMovers(); } }
D.addEventListener('click', e => {
  const b = e.target.closest('button[data-range],button[data-sect]');
  if (!b || !pul) return;
  if (b.dataset.range) { st.range = b.dataset.range; pulseLive(); } else { st.sect = b.dataset.sect; pulseSect(); }
  const f = D.querySelector('button[data-' + (b.dataset.range ? 'range="' + st.range : 'sect="' + st.sect) + '"]');
  if (f) f.focus({preventScroll: true});
});
let rw = 0;
addEventListener('resize', () => { clearTimeout(rw); rw = setTimeout(pulseLive, 150); });

// ---- the finishing layer: calendar strip, news ticker, Forecasts, My Book, the expiry payoff chart --------------------------
const tx = (id, h) => { const n = el(id); if (!n) return; if (n._h !== h) { n.innerHTML = h; n._h = h; } n.hidden = !h; };
const sgn = (v, d = 2) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d) + '%' : '—';
const money = v => isN(v) ? (v < 0 ? '−' : '') + '$' + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '—';
const ud = v => isN(v) ? (v > 0 ? 'u' : v < 0 ? 'd' : 'mu') : 'mu';
const tile = (k, v, c) => '<div class="a-bt"><span class="mu">' + esc(k) + '</span><b class="' + (c || '') + '">' + v + '</b></div>';
function calStrip() {
  const c = M.ed && M.ed.calendar;
  if (!c || !c.sessions || !c.sessions.length) return tx('m-cal', '');
  const ev = {};
  (c.events || []).forEach(e => { (ev[e.date] = ev[e.date] || []).push(e); });
  const word = s => s.state === 'closed' ? 'Closed' : s.state === 'early' ? 'Closes ' + esc(s.close_et) : 'Open';
  tx('m-cal', head('m-cal', esc(c.source), 'Calendar') + '<div class="card"><ol class="a-cal">' + c.sessions.map(s => {
    const p = M.et(s.date);
    return '<li class="a-cd a-c-' + esc(s.state) + '"><span class="a-cw">' + esc(p.weekday) + '</span><b>' + esc(p.md) + '</b><span class="a-cs">' + word(s) + '</span>' +
      (ev[s.date] || []).map(e => '<span class="a-ce" title="' + esc(e.label) + '">' + esc(e.kind) + (e.time_et ? ' ' + esc(e.time_et) : '') + '</span>').join('') + '</li>';
  }).join('') + '</ol>' + (c.coverage ? '' : '<p class="mu">The release schedule on file does not cover this whole span.</p>') + '</div>' +
    what('The next ten weekdays: open, an early 1 PM close, or closed for an exchange holiday, with the scheduled Fed decisions (FOMC), inflation (CPI) and payrolls (NFP) releases at their agency times in ET.'));
}
// a headline names its symbol when the symbol stands in the headline itself; otherwise the feed tagged it
function named(sym, h) { return !!sym && new RegExp('(^|[^A-Za-z0-9$])\\$?' + sym.replace(/[.^$*+?()[\]{}|\\]/g, '\\$&') + '([^A-Za-z0-9]|$)').test(h || ''); }
function ticker() {
  const nw = mg() && mg().news, hl = ok(nw) ? (nw.headlines || []).slice(0, 16) : [];
  if (!hl.length) return tx('m-tick', '');
  const src = nw.source ? esc(nw.source) : 'Alpaca News';
  const item = h => '<li><span class="a-nd ' + (h.direction > 0 || h.direction === 'positive' ? 'u">▲' : h.direction < 0 || h.direction === 'negative' ? 'd">▼' : 'mu">•') + '</span><b>' + esc(h.symbol) + '</b>' +
    '<span class="a-ta">' + (named(h.symbol, h.headline) ? 'named' : 'tagged') + '</span><span>' + esc(h.headline) + '</span><time class="mu">' + esc(M.wd(h.created_at)) + '</time></li>';
  tx('m-tick', '<div class="a-tk" aria-label="Headlines"><span class="a-tks">' + src + '</span><div class="a-tkv"><ul class="a-tkr">' + hl.map(item).join('') + '</ul><ul class="a-tkr" aria-hidden="true">' + hl.map(item).join('') + '</ul></div></div>');
}
// the expiry payoff of a single-expiry structure: P/L per contract at the knots (0, every strike, beyond the top), exact
// because the payoff is linear between strikes. legs: [{type, side, strike, ratio}]; debit: net paid per unit (points).
function payoffPts(legs, debit) {
  const ks = [...new Set(legs.map(l => l.strike))].sort((a, b) => a - b);
  const lo = Math.max(0, ks[0] * 0.9), hi = ks[ks.length - 1] * 1.1, xs = [lo, ...ks, hi];
  const v = s => 100 * (legs.reduce((a, l) => a + (l.type === 'call' ? Math.max(0, s - l.strike) : Math.max(0, l.strike - s)) * (l.ratio || 1) * (l.side === 'buy' ? 1 : -1), 0) - debit);
  return xs.map(x => [x, v(x)]);
}
function payoff(legs, debit, W, spot) {
  const L = (legs || []).filter(l => isN(l.strike) && (l.type === 'call' || l.type === 'put'));
  if (!L.length || !isN(debit) || new Set(L.map(l => l.expiration)).size > 1) return '';
  const P = payoffPts(L, debit), H = 150, pad = 30;
  const x0 = P[0][0], x1 = P[P.length - 1][0], ys = P.map(p => p[1]), y0 = Math.min(0, ...ys), y1 = Math.max(0, ...ys);
  if (!(x1 > x0) || !(y1 > y0)) return '';
  const X = x => pad + (x - x0) / (x1 - x0) * (W - 2 * pad), Y = y => 8 + (y1 - y) / (y1 - y0) * (H - 30);
  const be = [];
  for (let i = 1; i < P.length; i++) { const [a, u] = P[i - 1], [b, w] = P[i]; if ((u < 0) !== (w < 0) && u !== w) be.push(a + (b - a) * (-u) / (w - u)); }
  return '<svg class="a-po" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="Profit or loss at expiry by underlying price">' +
    '<line class="a-z0" x1="' + pad + '" x2="' + (W - pad) + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"/>' +
    '<polyline class="a-pl" points="' + P.map(p => f1(X(p[0])) + ',' + f1(Y(p[1]))).join(' ') + '"/>' +
    [...new Set(L.map(l => l.strike))].filter((k, i, a) => i === 0 || X(k) - X(a[i - 1]) >= 30).map(k => '<text class="a-ax" x="' + f1(X(k)) + '" y="' + (H - 6) + '" text-anchor="middle">' + esc(String(k)) + '</text>').join('') +
    be.map(b => '<circle class="a-be" cx="' + f1(X(b)) + '" cy="' + f1(Y(0)) + '" r="3"/>').join('') +
    (isN(spot) && spot > x0 && spot < x1 ? '<line class="a-sp" x1="' + f1(X(spot)) + '" x2="' + f1(X(spot)) + '" y1="4" y2="' + (H - 20) + '"/>' : '') +
    '<text class="a-ax" x="' + pad + '" y="' + f1(Y(y1) + 10) + '">' + money(y1) + '</text><text class="a-ax" x="' + pad + '" y="' + f1(Y(y0) - 3) + '">' + money(y0) + '</text></svg>' +
    (be.length ? '<p class="mu">Breakeven ' + be.map(b => b.toFixed(2)).join(' and ') + ' at expiry, per contract.</p>' : '');
}
M.payoff = payoff;
function book() {
  const b = M.ed && M.ed.book, P = el('p-desk');
  if (!b) return tx('d-book', '');
  if (!el('d-book') && P) {           // desk.js rewrites its panel: My Book is put back at its top
    const n = D.createElement('section');
    n.id = 'd-book'; n.setAttribute('aria-labelledby', 'h-d-book'); n.dataset.anchor = ''; n.dataset.jump = 'My Book'; n.hidden = true;
    P.prepend(n);
  }
  const w = b.window || {}, sc = b.score || {}, W = Math.max(260, Math.min(560, Math.round((el('main').clientWidth || 360) - 60)));
  const pos = b.positions || [], dec = b.decisions || [];
  const curve = (b.curve || []).filter(r => isN(r.book_pct) && isN(r.spy_pct) && isN(r.qqq_pct));
  let ch = '';
  if (curve.length >= 2) {
    const all = curve.flatMap(r => [r.book_pct, r.spy_pct, r.qqq_pct]), lo = Math.min(0, ...all), hi = Math.max(0, ...all), H = 120, r0 = hi - lo || 1;
    const ln = (k, c) => '<polyline class="a-bl ' + c + '" points="' + curve.map((r, i) => f1(4 + i / (curve.length - 1) * (W - 8)) + ',' + f1(6 + (hi - r[k]) / r0 * (H - 12))).join(' ') + '"/>';
    ch = '<svg class="a-bc" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="Book, SPY and QQQ since inception, percent">' + ln('qqq_pct', 'a-bq') + ln('spy_pct', 'a-bs') + ln('book_pct', 'a-bb') + '</svg>' +
      '<p class="a-lg"><span class="a-bb">Book</span><span class="a-bs">SPY</span><span class="a-bq">QQQ</span></p>';
  }
  const ptab = pos.length ? '<div class="tw"><table class="t a-pt"><thead><tr><th>Name</th><th>Kind</th><th class="r">Qty</th><th class="r">Entry</th><th class="r">Mark</th><th class="r">P&amp;L</th><th class="r">Risk</th></tr></thead><tbody>' +
    pos.map(p => '<tr><th scope="row">' + esc(p.name) + '</th><td>' + esc(p.kind) + (p.kind === 'stock' ? ' ' + esc(p.side) : '') + '</td><td class="r">' + esc(String(p.qty)) + '</td><td class="r">' + (isN(p.entry) ? p.entry.toFixed(2) : '—') + '</td><td class="r">' + (isN(p.mark) ? p.mark.toFixed(2) : '—') + '</td><td class="r ' + ud(p.pnl) + '">' + money(p.pnl) + (isN(p.pnl_pct) ? ' (' + sgn(p.pnl_pct, 1) + ')' : '') + '</td><td class="r">' + money(p.risk) + '</td></tr>').join('') + '</tbody></table></div>' +
    pos.filter(p => p.legs && p.legs.length).map(p => { const g = payoff(p.legs, p.entry, W); return g ? '<h3 class="a-h3">' + esc(p.name) + ' ' + esc(p.kind) + ' · payoff at expiry</h3>' + g : ''; }).join('')
    : '<p class="mu">Flat: no open positions.</p>';
  const dl = dec.length ? '<ul class="a-dl">' + dec.map(d => '<li><div class="a-dh"><span class="a-st a-s-' + esc(d.status) + '">' + esc(d.status) + '</span><b>' + esc(d.action) + ' ' + esc(d.name || '') + '</b>' + (d.side ? '<span>' + esc(d.side) + '</span>' : '') + (isN(d.qty) ? '<span>' + d.qty + '</span>' : '') +
    (isN(d.price) ? '<span>at ' + d.price.toFixed(2) + '</span>' : '') + (d.grade ? '<span class="a-gd">' + esc(d.grade) + '</span>' : '') + (d.forced ? '<span class="d">forced exit</span>' : '') + '<time class="mu">' + esc(M.wd(new Date(d.at * 1e3).toISOString())) + '</time></div>' +
    (d.why ? '<p>' + esc(d.why) + '</p>' : '') + (d.codes && d.codes.length ? '<p class="d">' + d.codes.map(esc).join(' · ') + '</p>' : '') +
    (d.committee ? '<details class="a-cm"><summary>Committee note</summary><dl>' + ['bull', 'bear', 'quant', 'risk'].map(k => d.committee[k] ? '<dt>' + k + '</dt><dd>' + esc(d.committee[k]) + '</dd>' : '').join('') + '</dl></details>' : '') + '</li>').join('') + '</ul>'
    : '<p class="mu">No decisions yet.</p>';
  tx('d-book', head('d-book', esc(b.source), 'My Book') +
    '<div class="card"><div class="a-bts">' + tile('Equity', money(b.nav)) + tile('Since inception', sgn(b.ret_pct), ud(b.ret_pct)) +
    tile('vs SPY', sgn(w.vs_spy), ud(w.vs_spy)) + tile('vs QQQ', sgn(w.vs_qqq), ud(w.vs_qqq)) + tile('Cash', money(b.cash)) + tile('Ladder', esc(b.ladder || '—')) + '</div>' +
    (w.from ? '<p class="mu">Window from ' + esc(M.day(w.from)) + ': book ' + sgn(w.book_pct) + ', SPY ' + sgn(w.spy_pct) + ', QQQ ' + sgn(w.qqq_pct) + '.</p>' : '<p class="mu">Starts at ' + money(b.start) + '; the comparison window opens with the first mark.</p>') + ch + '</div>' +
    '<div class="card"><h3 class="a-h3">Positions</h3>' + ptab + '</div>' +
    '<div class="card"><h3 class="a-h3">Last decisions</h3>' + dl + '</div>' +
    '<div class="card"><h3 class="a-h3">Grade</h3><p>' + (sc.closed ? sc.closed + ' closed · ' + sc.won + ' won · ' + sc.lost + ' lost' : 'No closed trades yet') +
    (isN(sc.capture) ? ' · capture ' + Math.round(sc.capture * 100) + '%' : '') + (isN(sc.adherence) ? ' · rules kept ' + Math.round(sc.adherence * 100) + '%' : '') + '</p>' +
    '<p class="mu">Heat ' + sgn(sc.heat_pct, 1).replace('+', '') + ' · gross ' + sgn(sc.gross_pct, 1).replace('+', '') + ' · drawdown ' + sgn(sc.drawdown_pct, 1).replace('+', '') + (sc.review_due ? ' · review due' : '') + '</p></div>' +
    what('Claude’s own simulated book, started at ' + money(b.start) + ': every decision is journaled with its committee note (bull, bear, quant, risk) before it can fill, then filled at the next Alpaca 5-minute open or option quote. The book is compared with SPY and QQQ over the same window; options show their payoff at expiry.'));
}
function forecasts() {
  const f = M.ed && M.ed.forecasts, es = f && f.engines || [];
  if (!es.length) return tx('e-fc', '');
  const lt = l => !l ? '<p class="mu">No forecast yet.</p>' : '<p><b>' + esc(l.subject) + '</b> ' + esc(String(l.quantity).replace(/_/g, ' ')) + ': ' + esc(String(l.value ?? '—')) +
    ' <span class="a-lab">' + esc(l.shown_as) + '</span></p><p class="mu">Issued ' + esc(clock(l.as_of)) + (l.horizon_close ? ' · resolves ' + esc(clock(l.horizon_close)) : '') + '</p>';
  tx('e-fc', head('e-fc', 'Forecast engines · ' + (f.chain_ok ? 'ledger chain verified' : 'ledger chain not verified'), 'Forecasts') + '<div class="a-fcl">' + es.map(e =>
    '<div class="card a-fc"><div class="a-fh"><b>' + esc(e.name) + '</b><span class="a-fs a-f-' + esc(e.state) + '">' + esc(e.state) + '</span></div><p class="mu">' + esc(e.track || '') + '</p>' +
    '<p class="a-fn">' + e.issued + ' issued · ' + e.abstained + ' abstained · ' + e.graded + ' graded</p>' + lt(e.latest) +
    '<p>' + (e.grade ? 'Grade: ' + esc(String(e.grade.metric).replace(/_/g, ' ')) + ' ' + e.grade.value + ' over ' + e.grade.n : 'Not graded yet') + '</p>' +
    (e.kill && e.kill.status ? '<p class="' + (e.kill.status === 'killed' ? 'd' : 'mu') + '">Kill rule: ' + esc(e.kill.status) + (e.kill.why ? ' · ' + esc(e.kill.why) : '') + '</p>' : '') + '</div>').join('') + '</div>' +
    what('Each engine issues forecasts before the outcome, abstains when its inputs are thin, and is graded when the horizon closes; an engine that fails its kill rule stops. A probability reads as a score until the engine’s calibration is attested.'));
}
function finish() { try { calStrip(); ticker(); book(); forecasts(); } catch (e) { console.warn(e); } }
D.addEventListener('md:edition', finish);
D.addEventListener('md:tab', finish);

function load() {
  if (busy) return;
  busy = 1;
  Promise.all([get('panels.json'), get('pulse.json')]).then(([p, q]) => {
    busy = 0;
    if (p && Array.isArray(p.panels)) { pan = p; pan.byId = Object.fromEntries(p.panels.map(r => [r.id, r])); el('t-hub').hidden = false; }
    if (q && q.v === 1 && q.lines) pul = q;
    pulseAll(); psych(); morgueSecs(); finish(); hub(); tidy();
  });
}
D.addEventListener('md:edition', load);
D.addEventListener('md:tab', load);
load();
})();
