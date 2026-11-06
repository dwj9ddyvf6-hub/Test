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
const C = {SPY: '#3fcf9a', QQQ: '#5c9dff', IWM: '#f0a040', SMH: '#c08bff'};   // the pulse lines' own colours (viz_market.css)
const st = {range: '1D', sect: 'map', q: '', f: 'all'};
let pan = null, pul = null, busy = 0;

// a section shown or hidden after its data arrives: rebuild the tab's chips once, so its view's chip appears (or goes)
let rq = 0;
function rechip() { if (rq) return; rq = setTimeout(() => { rq = 0; if (window.MDV && MDV.jump) MDV.jump(); }, 0); }

// a fetch whose one deadline covers the headers and the whole body (Codex's timed-fetch)
function get(url) {
  const ac = new AbortController(), t = setTimeout(() => ac.abort(), DEADLINE);
  return fetch(url, {cache: 'no-cache', signal: ac.signal}).then(r => r.ok ? r.json() : null)
    .catch(() => null).finally(() => clearTimeout(t));
}
// T-177: the header counts what the chart ranks and what the composite uses (live 11-05: '7 of 9 gauges ranked' over a 5-gauge score)
const moodHead = m => { const all = Object.values(m.gauges || {}), on = all.filter(x => x && x.percentile != null && x.state !== 'absent').length, k = (m.core_used || []).length;
  return on + ' of ' + all.length + ' gauges ranked' + (k ? ' · composite from ' + k + ' core' : '') + ' · percentile of their own history'; };
const sess = () => (M.ed && M.sessNow(M.ed.session, Date.now())) || '';
const clock = v => !v ? '' : v.length === 10 ? M.day(v) : M.wd(v) + ' ET';
// the chip's words: Updated (live, market open), Market closed (live, out of the session), Stale, Waiting
function chipOf(v) {
  if (!v) return null;
  // a date-only as_of is a completed session's product (lineup, engine, mood, movers): said so, never "Updated" mid-session
  // (visual audit 2026-11-04: "Updated Tue, Nov 3" all of Nov 4's session)
  // pass 17 (live Fri 11-06 09:33 ET): a reading dated today is for today's session, whose close has not happened
  const today = String(v.as_of || '').length === 10 && sess() !== 'closed' && M.et(v.as_of).key === M.et(Date.now()).key;
  if (v.state === 'live' && sess() === 'open' && String(v.as_of || '').length === 10) return ['ok', today ? 'For the ' + M.day(v.as_of) + ' session' : 'As of the ' + M.day(v.as_of) + ' close'];
  // pass 16 (live Fri 11-06 07:06 ET): "Pre-market · Thu, Nov 5" read as if Thursday were the pre-market day; a date-only
  // as_of outside the session names the close it comes from
  // pass 17 (live Fri 11-06 09:13 ET): a reading dated today, before the open, is built for today's session; its close has
  // not happened ("Pre-market · as of the Fri, Nov 6 close")
  const done = today ? 'for the ' + M.day(v.as_of) + ' session' : String(v.as_of || '').length === 10 ? 'as of the ' + M.day(v.as_of) + ' close' : clock(v.as_of);
  if (v.state === 'live') return sess() === 'open' ? ['ok', 'Updated ' + clock(v.as_of)] : ['cl', (sess() === 'pre' ? 'Pre-market · ' : 'Market closed · ') + done];
  if (v.state === 'stale') return ['st', 'Stale · as of ' + (clock(v.as_of) || 'unknown')];
  if (v.state === 'ungraded') return ['ug', 'Ungraded · ' + clock(v.as_of)];
  // a panel whose producer has never run: awaiting its first reading, with the producer's next window (panels.py)
  if (v.state === 'waiting' && v.next_run) return ['wt', 'Awaiting first reading · next run ' + v.next_run];
  return ['wt', v.state === 'waiting' ? 'Waiting' : 'Unavailable'];
}
const whyHtml = w => '<p class="vsw">' + esc(w) + '</p>';
const chipHtml = (c, why) => '<span class="vsc vs-' + c[0] + '"' + (why ? ' title="' + esc(why) + '"' : '') + '><i aria-hidden="true"></i>' + esc(c[1]) + '</span>';

// ---- every section: its state chip, one "What is this?", the chart first ------------------------------------------------
function tidy() {
  D.querySelectorAll('#grid section').forEach(s => {
    const wh = [...s.children].filter(x => x.matches('details.wh'));
    wh.slice(1).forEach(x => x.remove());
    const w = wh[0], cards = [...s.children].filter(x => x.matches('.card,.cp'));
    const lastCard = cards[cards.length - 1];
    if (w && lastCard && w.compareDocumentPosition(lastCard) & Node.DOCUMENT_POSITION_FOLLOWING) lastCard.after(w);
    const row = pan && (pan.byId[s.id] || pan.byId[(pan.alias || {})[s.id]]), c = row && chipOf(row), head = s.querySelector(':scope > .shd');
    let chip = s.querySelector(':scope > .shd > .vsc, :scope > .vsl > .vsc');
    if (!c) return;
    if (s.hasAttribute('data-vz-last')) {               // viz_market.js shows the last session's chart with its age instead
      s.querySelectorAll(':scope > .vsw, :scope > .shd > .vsc, :scope > .vsl').forEach(x => x.remove());
      return;
    }
    s.classList.toggle('vs-stale', row.state === 'stale');
    // the reason a value is not live is printed, never carried by hover alone (phone readers have no hover)
    const quiet = s.closest('#p-market');            // owner, 2026-11-02: market panels show their data, never freshness rules
    const wy = !quiet && row.state !== 'live' && row.why && row.state !== 'waiting' ? row.why : '', wp = s.querySelector(':scope > .vsw');
    if (wp && wp.textContent !== wy) wp.remove();
    if (wy && !s.querySelector(':scope > .vsw')) (head || s).insertAdjacentHTML(head ? 'afterend' : 'afterbegin', whyHtml(wy));
    const h = chipHtml(c, row.why);
    if (chip && chip.outerHTML === h) return;
    if (chip) chip.outerHTML = h;
    else if (head) head.insertAdjacentHTML('beforeend', h);
    else s.insertAdjacentHTML('afterbegin', '<p class="vsl">' + h + '</p>');
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
  const sv = M.ed && M.ed.health && M.ed.health.served, svt = !sv || sv.status === 'none' ? '' : sv.status === 'equal'
    ? ' · served as published, ' + sv.equal + ' of ' + sv.checked + ' files' : sv.status === 'propagating' ? ' · the site is still taking the last publish' : ' · served differs: ' + sv.equal + ' of ' + sv.checked + ' files match';
  el('hubn').textContent = c[1] + ' published · ' + c[0] + ' awaiting · as of ' + M.wd(pan.generated_at) + ' ET' + svt;
  el('hubn').classList.toggle('vs-differ', !!sv && sv.status === 'differ');
  n.innerHTML = rows.length ? rows.map(r => '<li class="a-hc"><a href="#' + esc(r.id) + '"><span class="a-ht">' + esc(r.title) + '</span>' +
    chipHtml(chipOf(r), r.why) + '<span class="a-hs">' + esc(r.source) + '</span><span class="a-hl">' + esc(r.limitation) + '</span>' +
    (r.state === 'stale' && r.why ? '<span class="a-hw">' + esc(r.why) + '</span>' : '') + '</a></li>').join('') : '<li class="mu">No panel matches.</li>';
  D.querySelectorAll('#hubf button').forEach(b => b.setAttribute('aria-pressed', b.dataset.f === st.f));
}
// ---- the freshness SLA board: each panel's max age, current age and pass/fail, and what is missing ----------------
const age = s => s == null ? '—' : s < 120 ? s + ' s' : s < 7200 ? Math.round(s / 60) + ' min' : s < 172800 ? Math.round(s / 3600) + ' h' : Math.round(s / 86400) + ' d';
function slaBoard() {
  const n = el('hubsla');
  if (!n || !pan || !pan.sla) return;
  const t = Object.entries(pan.sla).map(([c, v]) => '<span' + (v.fail ? ' class="f"' : '') + '>' + esc(c) + ' ' + v.pass + '/' + v.n + '</span>').join('');
  const rows = pan.panels.filter(r => r.sla === 'fail').concat(pan.panels.filter(r => r.sla !== 'fail'));
  n.innerHTML = '<div class="a-slat">' + t + '</div><table class="a-slab"><tbody>' + rows.map(r => '<tr><td>' + esc(r.title) +
    (r.missing ? '<div class="m">' + esc(r.missing) + '</div>' : '') + '</td><td class="ag">' + age(r.age_s) + ' / ' + age(r.max_age_s) +
    '</td><td class="' + (r.sla === 'pass' ? 'p">Pass' : 'x">Fail') + '</td></tr>').join('') + '</tbody></table>';
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
    '<path class="a-gz a-gz-u" d="' + arc(60, 62, 46, Math.PI * 1.6, Math.PI * 2) + '"/><line class="a-gh" x1="60" y1="62" x2="' + f1(nx) + '" y2="' + f1(ny) + '"/><line class="a-gn" x1="60" y1="62" x2="' + f1(nx) + '" y2="' + f1(ny) + '"/>' +
    '<circle class="a-gc" cx="60" cy="62" r="4"/><text class="a-gv" x="60" y="78" text-anchor="middle">' + esc(val) + '</text></svg>';
}
function donut(parts, label) {           // parts: [[value, class, name]]; nothing drawn without a positive total
  const tot = parts.reduce((a, p) => a + p[0], 0);
  if (!(tot > 0)) return '';
  let a = -Math.PI / 2, g = '';
  parts.forEach(p => { if (!p[0]) return; const b = a + 2 * Math.PI * p[0] / tot - 1e-4; g += '<path class="a-dn a-' + p[1] + '" d="' + arc(50, 50, 38, a, b) + '"/>'; a = b; });
  return '<svg class="a-dnt" viewBox="0 0 100 100" role="img" aria-label="' + esc(label) + '">' + g +
    // one value per line inside the hole (owner audit 2026-11-04: "23.65 / 6.1" on one line touched the ring)
    parts.map((p, i) => '<text x="50" y="' + (50 + (i - (parts.length - 1) / 2) * 15 + 5).toFixed(1) + '" text-anchor="middle" class="a-dv a-' + p[1] + '">' +
      (+p[0].toFixed(p[0] >= 10 ? 1 : 2)) + '</text>').join('') + '</svg>';
}
window.MDA = {gauge, donut};

// ---- Market Pulse ------------------------------------------------------------------------------------------------------
const etDay = t => M.et(t * 1e3).key;
// the series a range shows: 1D against the prior session's close (the dials' basis, so the line's end and its dial agree;
// owner audit 2026-11-04: SMH's line ended near -1% under a -2.81% dial), 5D against its first displayed close
function indexed(s, range) {
  if (!s || !s.t || s.t.length < 2) return null;
  let i0 = 0;
  if (range === '1D') { const d = etDay(s.t[s.t.length - 1]); while (etDay(s.t[i0]) !== d) i0++; }
  const t = s.t.slice(i0), c = s.c.slice(i0), b = range === '1D' && isN(s.prev) && s.prev > 0 ? s.prev : c[0];
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
    g += '<path class="a-pl a-k' + k + '" d="' + d + '"/><circle cx="' + f1(X(ix.get(e[0]))) + '" cy="' + f1(Y(e[1])) + '" r="3" fill="' + C[k] + '"/>';
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
    '<div class="a-plw" id="m-live-c">' + lines(W) + '</div><p class="a-lg"><span class="mu">' + (st.range === '1D' ? 'vs prior close' : 'vs first close shown') + '</span>' + keys.map(k => '<span><i data-c="' + C[k] + '"></i>' + k + '</span>').join('') + '</p>' +
    (gg ? '<div class="a-gw">' + gg + '</div>' : '') + '</div>' +
    what('Each fund’s 5-minute closes: 1D against the prior session’s close (the same basis as the dials), 5D indexed to the first close shown. The dials are each fund against the prior session’s close. Regular hours only; the line breaks across the overnight gap.');
  n.querySelectorAll('i[data-c]').forEach(e => { e.style.background = e.dataset.c; });
  n.hidden = false;
}
const tone = p => p >= 0 ? 'u' : 'd', lvl = p => Math.min(4, Math.ceil(Math.abs(p) / .5));
function pulseSect() {
  const n = el('m-sect'), s = pul.sectors || [];
  if (!n) return;
  if (!s.length) { n.hidden = true; return; }
  const r2 = v => Math.round(v * 100) / 100, up = r2(s.reduce((a, x) => a + Math.max(0, x.pct), 0)), dn = r2(s.reduce((a, x) => a - Math.min(0, x.pct), 0)), mx = Math.max(...s.map(x => Math.abs(x.pct)), .01);
  const body = st.sect === 'map' ? '<div class="a-smap" data-viz>' + s.map(x => '<div class="a-stl t' + tone(x.pct) + lvl(x.pct) + '"><b>' + esc(x.name) + '</b><span>' + M.pct(x.pct, 2) + '</span></div>').join('') + '</div>'
    : '<ol class="a-sbars" data-viz>' + s.map(x => '<li><span class="a-sn">' + esc(x.name) + '</span><span class="a-sb"><i class="' + tone(x.pct) + '" data-w="' + f1(Math.abs(x.pct) / mx * 50) + '"></i></span><span class="a-sv">' + M.pct(x.pct, 2) + '</span></li>').join('') + '</ol>';
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
  n.innerHTML = head('m-movers', esc(M.day(m.as_of)), 'Movers') + (li ? '' : '') +
    what('The roster’s biggest closes on the latest completed session, names priced at $5 or more.');
  n.hidden = false;
}

// ---- Market Mood (the edition's `mood`: the nine-gauge engine) ---------------------------------------------------------
function psych() {
  const n = el('m-psy'), m = M.ed && M.ed.mood;
  if (!n) return;
  if (!m || !m.gauges) { n.hidden = true; return; }
  const c = isN(m.composite) ? m.composite : null;
  n.innerHTML = head('m-psy', moodHead(m), 'Market Mood')   /* the count the chart draws (audit 5 M12) */ + (c !== null ? '<div class="card"><div class="a-mh">' +
    gauge(c, 0, 100, 'Composite', f1(c)) + '<p class="a-rw">' + esc(m.regime || '') + '</p></div></div>' : '') +
    what('The market-psychology gauges, each read as a percentile of its own history (0 fear, 100 greed). The composite combines the core gauges that report.');
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
  sub('f-map-x', 'f-map', (cards.length && d ? '' : '') +
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
  const set = (id, h) => { const n = el(id); if (!n) return; if (n._h !== h) { n.innerHTML = h; n._h = h; } if (n.hidden !== !h) { n.hidden = !h; rechip(); } };
  const W = Math.max(280, Math.round((el('main').clientWidth || 360) - 34));
  const lad = cards.filter(([, c]) => c.ladder && c.ladder.length >= 2);
  set('m-ladder', lad.length ? head('m-ladder', 'Dealer gamma by strike', 'Gamma Ladder') + (W && ladderSvg ? '' : '') +
    what('Modelled dealer gamma at each strike within 5% of the spot, in billions per 1% move: right of the line adds stability, left accelerates moves. The share is the strike’s pull on the band.') : '');
  // expired expiries drop, today's included once the 16:00 ET close has passed (audit 5 M9)
  const et = new Date().toLocaleString('sv-SE', {timeZone: 'America/New_York'}), live = e => !!e && (String(e) > et.slice(0, 10) || (String(e) === et.slice(0, 10) && et.slice(11, 16) < '16:00'));
  const pins = cards.map(([k, c]) => [k, Object.assign({}, c, {pins: (c.pins || []).filter(p => live(p.expiry))})]).filter(([, c]) => c.pins.length);
  set('m-pins', pins.length ? head('m-pins', 'Six nearest expiries', 'Expiry Pin Watch') + pins.map(([k, c]) => '<details class="card"><summary class="a-h3">' + esc(k) + ' pin table</summary><div class="tw"><table class="t a-pt"><thead><tr><th>Expiry</th><th class="r">Pin</th><th class="r">From spot</th><th class="r">Call max</th><th class="r">Put max</th></tr></thead><tbody>' +
    c.pins.map(p => '<tr><th scope="row">' + esc(M.et(p.expiry).md) + '</th><td class="r">' + esc(String(p.pin_strike ?? '—')) + '</td><td class="r">' + (isN(p.distance_pct) ? M.pct(p.distance_pct, 1) : '—') + '</td><td class="r">' + esc(String(p.call_strike ?? '—')) + '</td><td class="r">' + esc(String(p.put_strike ?? '—')) + '</td></tr>').join('') + '</tbody></table></div></details>').join('') +
    what('For each of the six nearest expiries, the strike with the most open interest (where price tends to be pulled into expiry), and the largest call and put strikes, from the prior close.') : '');
  const iw = m && m.insider_wire, cl = ok(iw) ? (iw.clusters || []) : [];
  set('m-insider', ok(iw) ? head('m-insider', 'SEC Form 4 · cluster buying', 'Insider Wire') + insiderViz(iw, cl) + '<div class="card">' + (cl.length ? '<ul class="a-iw">' + cl.map(c => '<li><b>' + esc(c.symbol) + '</b><span>' + c.insiders + ' insiders · ' + c.purchases + ' buys · ' + usd(c.value_usd) + '</span><span class="mu">' + esc(M.et(c.window_start).md) + '–' + esc(M.et(c.window_end).md) + '</span></li>').join('') + '</ul>'
    : (iw.totals || {}).names_with_record ? '<p class="mu">No cluster buying in the last 30 days.</p>'
      : '<p class="mu">The Form 4 filings have not been read yet: 0 of the ' + ((iw.totals || {}).names_checked || 0).toLocaleString('en-US') + ' roster names have a record, so no cluster can be called.</p>')   /* unread is not "none" (audit 5 M11) */ + '</div>' + what('Names where three or more insiders bought on the open market within 30 days, from their Form 4 filings.') : '');
  const nw = m && m.news, hl = ok(nw) ? (nw.headlines || []).slice(0, 12) : [];
  set('m-news', hl.length ? head('m-news', 'Alpaca News · headline direction', 'News') + newsViz(nw) + '<div class="card"><ul class="a-nw">' + hl.map(h => '<li><span class="a-nd ' + (h.direction > 0 || h.direction === 'positive' ? 'u' : h.direction < 0 || h.direction === 'negative' ? 'd' : 'mu') + '">' + (h.direction > 0 || h.direction === 'positive' ? '▲' : h.direction < 0 || h.direction === 'negative' ? '▼' : '•') + '</span><b>' + esc(h.symbol) + '</b><span>' + esc(h.headline) + '</span><time class="mu">' + esc(M.wd(h.created_at)) + '</time></li>').join('') + '</ul></div>' +
    what('Recent headlines for the desk’s names, each marked up or down by fixed word lists on the headline alone.') : '');
  mapX(); boardX();
}
// the galath forms for the text panels (w21 chart coverage, owner 2026-11-03)
function insiderViz(iw, cl) {
  const G = window.GK, t = iw.totals || {};
  if (!G) return '';
  const on = t.names_with_record || 0, off = t.names_not_on_record || 0;
  const N = (t.names_checked || 0).toLocaleString('en-US');   // T-066: read, of the roster's names, never "checked" while 0 are read
  return G.card('Form 4 coverage', on.toLocaleString('en-US') + ' of ' + N + ' roster names on record', '<div class="gk-row">' +
    (G.donut([{k: 'With a Form 4 record', v: on, c: G.C.u}, {k: 'Form 4 not read yet', v: off, c: G.C.n}], (on + off).toLocaleString('en-US'), 'names', 'Names with and without a Form 4 record') || '') +
    G.bars([{k: 'Open-market buys', v: t.open_market_buys || 0, c: 'u'}, {k: 'Open-market sells', v: t.open_market_sells || 0, c: 'd'},
      {k: 'Clusters flagged', v: t.clusters_flagged != null ? t.clusters_flagged : cl.length, c: 'y'}], {label: 'Insider buys, sells and clusters, last 30 days', W: Math.max(280, G.width() - 300)}) + '</div>');
}
function newsViz(nw) {
  const G = window.GK, n = (nw.names || []).filter(x => x.articles > 0).sort((a, b) => b.articles - a.articles).slice(0, 10);
  if (!G || !n.length) return '';
  const tone = x => x.net_direction > 0 ? 'u' : x.net_direction < 0 ? 'd' : 'n';
  return G.card('Headlines by name', 'colour = net direction', G.bars(n.map(x => ({k: x.symbol, v: x.articles, c: tone(x),
    t: x.articles + ' · ▲' + (x.positive || 0) + ' ▼' + (x.negative || 0)})), {label: 'Headline count by name, coloured by net direction'}));
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
const sgn = (v, d = 2) => { if (!isN(v)) return '—'; const a = Math.abs(v).toFixed(d); return (+a === 0 ? '' : v > 0 ? '+' : '−') + a + '%'; };   // a value that rounds to zero carries no sign
const money = v => isN(v) ? (v < 0 ? '−' : '') + '$' + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '—';
const ud = v => isN(v) ? (v > 0 ? 'u' : v < 0 ? 'd' : 'mu') : 'mu';
const tile = (k, v, c) => '<div class="a-bt"><span class="mu">' + esc(k) + '</span><b class="' + (c || '') + '">' + v + '</b></div>';
const EVK = {ISM_SVC: 'ISM', ISM_MFG: 'ISM', NFP: 'Jobs', CPI: 'CPI', FOMC: 'Fed', PPI: 'PPI', GDP: 'GDP'};
const evk = k => EVK[k] || String(k || '').replace(/_/g, ' ');   // a release reads as words, never a feed code
function calStrip() {
  const c = M.ed && M.ed.calendar;
  if (!c || !c.sessions || !c.sessions.length) return tx('m-cal', '');
  const ev = {};
  (c.events || []).forEach(e => { (ev[e.date] = ev[e.date] || []).push(e); });
  const word = s => s.state === 'closed' ? 'Closed' : s.state === 'early' ? 'Closes ' + esc(s.close_et) : 'Open';
  const G = window.GK, cv = G ? G.card('Trading hours ahead', 'next ' + c.sessions.length + ' weekdays', G.sessions(c.sessions.map(s => { const p = M.et(s.date);
    return {day: p.weekday, md: p.md, hours: s.state === 'closed' ? 0 : s.state === 'early' ? 3.5 : 6.5, word: s.state === 'closed' ? 'closed' : s.state === 'early' ? 'early close ' + (s.close_et || '') : 'full session',
      ev: (ev[s.date] || []).map(e => evk(e.kind) + (e.time_et ? ' ' + e.time_et : ''))}; }), 'Trading hours per session with scheduled releases')) : '';
  const evLine = () => { const r = c.sessions.filter(s => (ev[s.date] || []).length).map(s => { const p = M.et(s.date);
    return '<li><b>' + esc(p.weekday) + ' ' + esc(p.md) + '</b> ' + ev[s.date].map(e => '<span title="' + esc(e.label) + '">' + esc(evk(e.kind)) + (e.time_et ? ' ' + esc(e.time_et) : '') + '</span>').join(' · ') + '</li>'; });
    return r.length ? '<ul class="a-cev">' + r.join('') + '</ul>' : ''; };
  // the chart already carries each day, its hours and its releases: the day cards repeated the same ten days below it
  // (audit 2026-11-03), so they are drawn only when the chart cannot be
  tx('m-cal', head('m-cal', esc(c.source), 'Calendar') + cv + (cv ? evLine() + (c.coverage ? '' : '<p class="mu">The release schedule on file does not cover this whole span.</p>') : '<div class="card"><ol class="a-cal">' + c.sessions.map(s => {
    const p = M.et(s.date);
    return '<li class="a-cd a-c-' + esc(s.state) + '"><span class="a-cw">' + esc(p.weekday) + '</span><b>' + esc(p.md) + '</b><span class="a-cs">' + word(s) + '</span>' +
      (ev[s.date] || []).map(e => '<span class="a-ce" title="' + esc(e.label) + '">' + esc(evk(e.kind)) + (e.time_et ? ' ' + esc(e.time_et) : '') + '</span>').join('') + '</li>';
  }).join('') + '</ol>' + (c.coverage ? '' : '<p class="mu">The release schedule on file does not cover this whole span.</p>') + '</div>') +
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
  const dir = h => h.direction > 0 || h.direction === 'positive' ? 1 : h.direction < 0 || h.direction === 'negative' ? -1 : 0, G = window.GK;
  const tone = G ? G.strip([{k: 'Up', v: hl.filter(h => dir(h) > 0).length, c: G.C.u}, {k: 'Flat', v: hl.filter(h => !dir(h)).length, c: G.C.n}, {k: 'Down', v: hl.filter(h => dir(h) < 0).length, c: G.C.d}], 'Headline tone: up, flat and down', 96) : '';
  tx('m-tick', '<div class="a-tk" aria-label="Headlines">' + tone + '<span class="a-tks">' + src + '</span><div class="a-tkv"><ul class="a-tkr">' + hl.map(item).join('') + '</ul><ul class="a-tkr" aria-hidden="true">' + hl.map(item).join('') + '</ul></div></div>');
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
    n.id = 'd-book'; n.setAttribute('aria-labelledby', 'h-d-book'); n.dataset.anchor = ''; n.dataset.jump = 'Book performance'; n.hidden = true;
    P.prepend(n);
  }
  const w = b.window || {}, sc = b.score || {}, W = Math.max(260, Math.min(560, Math.round((el('main').clientWidth || 360) - 60)));
  const pos = b.positions || [], dec = b.decisions || [], pl = b.plans || [];
  const plans = pl.length && window.MDG ? '<div class="g-plans"><h3 class="a-h3">' + (pos.length ? 'Open' : 'Flat') + ' · ' + pl.length + ' open plan' + (pl.length > 1 ? 's' : '') + '</h3>' +
    pl.map(p => window.MDG.planCard(p, Math.max(300, Math.min(1100, Math.round((el('main').clientWidth || 360) - 60))))).join('') + '</div>' : '';
  const curve = (b.curve || []).filter(r => isN(r.book_pct) && isN(r.spy_pct) && isN(r.qqq_pct));
  let ch = '';
  if (curve.length >= 2) {
    const CW = Math.max(260, Math.round((el('main').clientWidth || 360) - 60)), n = curve.length;    // the card's own width: never letterboxed
    const all = curve.flatMap(r => [r.book_pct, r.spy_pct, r.qqq_pct]), lo = Math.min(0, ...all), hi = Math.max(0, ...all), H = 140, r0 = hi - lo || 1, L0 = 8, R0 = 64;
    const X = i => L0 + i / (n - 1) * (CW - L0 - R0), Y = v => 8 + (hi - v) / r0 * (H - 30);
    const ln = (k, c) => '<polyline class="a-bl ' + c + '" points="' + curve.map((r, i) => f1(X(i)) + ',' + f1(Y(r[k]))).join(' ') + '"/>' +
      (n <= 30 ? curve.map((r, i) => '<circle class="a-bd ' + c + '" cx="' + f1(X(i)) + '" cy="' + f1(Y(r[k])) + '" r="3"/>').join('') : '');
    const ends = [['qqq_pct', 'a-bq'], ['spy_pct', 'a-bs'], ['book_pct', 'a-bb']].map(([k, c]) => ({c, v: curve[n - 1][k], y: Y(curve[n - 1][k])})).sort((a, b) => a.y - b.y);
    ends.forEach((e, i) => { if (i && e.y - ends[i - 1].y < 12) e.y = ends[i - 1].y + 12; });
    ch = '<svg class="a-bc" viewBox="0 0 ' + CW + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="Book, SPY and QQQ since inception, percent">' +
      '<line class="a-z0" x1="' + L0 + '" x2="' + (CW - R0) + '" y1="' + f1(Y(0)) + '" y2="' + f1(Y(0)) + '"/>' + ln('qqq_pct', 'a-bq') + ln('spy_pct', 'a-bs') + ln('book_pct', 'a-bb') +
      ends.map(e => '<text class="a-ax ' + e.c + '" x="' + (CW - R0 + 6) + '" y="' + f1(e.y + 4) + '">' + sgn(e.v) + '</text>').join('') +
      '<text class="a-ax" x="' + L0 + '" y="' + (H - 4) + '">' + esc(M.day(curve[0].session)) + '</text><text class="a-ax" x="' + (CW - R0) + '" y="' + (H - 4) + '" text-anchor="end">' + esc(M.day(curve[n - 1].session)) + '</text></svg>' +
      '<p class="a-lg"><span class="a-bb">Book</span><span class="a-bs">SPY</span><span class="a-bq">QQQ</span></p>';
  }
  const ptab = pos.length ? '<div class="tw"><table class="t a-pt"><thead><tr><th>Name</th><th>Kind</th><th class="r">Qty</th><th class="r">Entry</th><th class="r">Mark</th><th class="r">P&amp;L</th><th class="r">Risk</th></tr></thead><tbody>' +
    pos.map(p => '<tr><th scope="row">' + esc(p.name) + '</th><td>' + esc(p.kind) + (p.kind === 'stock' ? ' ' + esc(p.side) : '') + '</td><td class="r">' + esc(String(p.qty)) + '</td><td class="r">' + (isN(p.entry) ? p.entry.toFixed(2) : '—') + '</td><td class="r">' + (isN(p.mark) ? p.mark.toFixed(2) : '—') + '</td><td class="r ' + ud(p.pnl) + '">' + money(p.pnl) + (isN(p.pnl_pct) ? ' (' + sgn(p.pnl_pct, 1) + ')' : '') + '</td><td class="r">' + money(p.risk) + '</td></tr>').join('') + '</tbody></table></div>' +
    pos.filter(p => p.legs && p.legs.length).map(p => { const g = payoff(p.legs, p.entry, W); return g ? '<h3 class="a-h3">' + esc(p.name) + ' ' + esc(p.kind) + ' · payoff at expiry</h3>' + g : ''; }).join('')
    : '<p class="mu">Flat: no open positions.</p>';
  const dl = dec.length ? '<ul class="a-dl">' + dec.map(d => '<li><div class="a-dh"><span class="a-st a-s-' + esc(d.status) + '">' + esc(d.status) + '</span>' + (d.action || d.name ? '<b>' + esc([d.action, d.name].filter(Boolean).join(' ')) + '</b>' : '') + (d.side ? '<span>' + esc(d.side) + '</span>' : '') + (isN(d.qty) ? '<span>' + d.qty + '</span>' : '') +
    (isN(d.price) ? '<span>at ' + d.price.toFixed(2) + '</span>' : '') + (d.grade ? '<span class="a-gd">' + esc(d.grade) + '</span>' : '') + (d.forced ? '<span class="d">forced exit</span>' : '') + '<time class="mu">' + esc(M.wd(new Date(d.at * 1e3).toISOString())) + '</time></div>' +
    (d.why ? '<p>' + esc(d.why) + '</p>' : '') + (codesLine(d) ? '<p class="d">' + esc(codesLine(d)) + '</p>' : '') +
    (d.committee ? '<details class="a-cm"><summary>Committee note</summary><dl>' + ['bull', 'bear', 'quant', 'risk'].map(k => d.committee[k] ? '<dt>' + k + '</dt><dd>' + esc(d.committee[k]) + '</dd>' : '').join('') + '</dl></details>' : '') + '</li>').join('') + '</ul>'
    : '<p class="mu">No decisions yet.</p>';
  tx('d-book', head('d-book', 'Claude\u2019s own book', 'Book performance') +
    (plans ? '<div class="card g-hero">' + plans + '</div>' : '') +
    '<div class="card"><div class="a-bts">' + tile('Equity', money(b.nav)) + tile('Since inception', sgn(b.ret_pct), ud(b.ret_pct)) +
    tile('vs SPY', sgn(w.vs_spy), ud(w.vs_spy)) + tile('vs QQQ', sgn(w.vs_qqq), ud(w.vs_qqq)) + tile('Cash', money(b.cash)) + tile('Ladder', esc(b.ladder || '—')) + '</div>' +
    (w.from ? '<p class="mu">Window from ' + esc(M.day(w.from)) + ': book ' + sgn(w.book_pct) + ', SPY ' + sgn(w.spy_pct) + ', QQQ ' + sgn(w.qqq_pct) + '.</p>' : '<p class="mu">Starts at ' + money(b.start) + '; the comparison window opens with the first mark.</p>') + ch + '</div>' +
    (pos.length || dec.length ? '<div class="card"><h3 class="a-h3">Positions</h3>' + ptab + '</div>' +
    '<div class="card"><h3 class="a-h3">Last decisions</h3>' + dl + '</div>' : '') +
    '<div class="card"><h3 class="a-h3">Risk against the caps</h3><div class="vz-box" data-vz="risk"></div><h3 class="a-h3">Every closed trade in R</h3><div class="vz-box" data-vz="rled"></div></div>' +
    '<div class="card"><h3 class="a-h3">Grade</h3><p>' + (sc.closed ? sc.closed + ' closed · ' + sc.won + ' won · ' + sc.lost + ' lost' : 'No closed trades yet') +
    (isN(sc.capture) ? ' · capture ' + Math.round(sc.capture * 100) + '%' : '') + (sc.closed && isN(sc.adherence) ? ' · rules kept ' + Math.round(sc.adherence * 100) + '%' : '') + '</p>' +
    '<p class="mu">Heat ' + sgn(sc.heat_pct, 1).replace('+', '') + ' · gross ' + sgn(sc.gross_pct, 1).replace('+', '') + ' · drawdown ' + sgn(sc.drawdown_pct, 1).replace('+', '') + (sc.review_due ? ' · review due' : '') + '</p></div>' +
    what('Claude’s own book, started at ' + money(b.start) + ': every decision is journaled with its committee note (bull, bear, quant, risk) before it can fill, then filled at the next Alpaca 5-minute open or option quote. The book is compared with SPY and QQQ over the same window; options show their payoff at expiry.'));
  bookCharts();
}
function bookCharts() { const b = M.ed && M.ed.book, n = el('d-book'); if (b && n && window.VZD) window.VZD.paint(n, b); }
// a forecast's value as a reader reads it (owner 2026-11-03: "QQQ close band 21s: 599.4171-773.8912" printed raw floats):
// prices to cents, a range as "lo – hi", a 0-1 score as a percent, a tiny variance in two significant figures
function fcv(l) {
  const FC_PROB = /(^|_)(touch|finish|chance|prob|flip)|_gt_|^rv\d+_gt|^mdd\d+_gt/;
  const q = String(l.quantity || ''), price = /(^|_)(close_band|band|price|level)s?(_|$)/.test(q) && !/pct|ratio|_over_/.test(q);
  const pctq = /_pct\b|pct_|_pct$/.test(q), num = x => typeof x === 'number' && isFinite(x);
  const one = x => { if (!num(x)) return '—'; const a = Math.abs(x), sg = x < 0 ? '\u2212' : '';
    const t = price ? a.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})
      : a !== 0 && a < 0.01 ? String(+a.toPrecision(2)) : a >= 1000 ? a.toLocaleString('en-US', {maximumFractionDigits: 0}) : String(+a.toFixed(2));
    return (t === '0' || t === '0.00' ? '' : sg) + t + (pctq ? '%' : ''); };
  const v = l.value;
  if (v == null || v === '') return '—';
  if (typeof v === 'string') { const m = /^\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)\s*-\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)\s*$/i.exec(v);
    if (m) return one(+m[1]) + ' \u2013 ' + one(+m[2]);
    return num(+v) && v.trim() !== '' ? fcv({quantity: q, value: +v, shown_as: l.shown_as}) : v; }
  // only a probability reads as a percent; a signed signal score (trend, breakout, lead-lag; codex_scorers clips at +-8) stays a number, so
  // 0.002 is never printed "0%" (audit 2026-11-04); a variance reads as its daily volatility
  if (/(^|_)har$/.test(q) && l.shown_as === 'variance' && v >= 0) return (Math.sqrt(v) * 100).toFixed(2) + '% a day';
  if (l.shown_as === 'score' && v >= 0 && v <= 1 && !price && FC_PROB.test(q)) return Math.round(v * 100) + '%';
  if (l.shown_as === 'score' && !FC_PROB.test(q)) return (v > 0 ? '+' : v < 0 ? '\u2212' : '') + Math.abs(+v).toFixed(2);
  return one(+v);
}
// a forecast's quantity in plain English (audit 2026-11-04: "mdd21 gt 1.5em", "iv uncorrected" on the public page)
function fcq(l) {
  const q = String(l.quantity || '');
  let m;
  if ((m = /^close_band_(\d+)s$/.exec(q))) return m[1] + '-session closing range';
  if ((m = /^touch_either_([\d.]+)em_(\d+)s$/.exec(q))) return 'chance of moving ' + m[1] + ' expected moves either way within ' + m[2] + ' sessions';
  if ((m = /^finish_above_([\d.]+)_(\d{4}-\d\d-\d\d)/.exec(q))) return 'chance of closing above ' + m[1] + ' on ' + M.day(m[2]);
  if ((m = /^mdd(\d+)_gt_([\d.]+)em$/.exec(q))) return 'chance of a ' + m[1] + '-session drawdown deeper than ' + m[2] + ' expected moves';
  if ((m = /^flip_through_(\d+)s$/.exec(q))) return 'chance of crossing the gamma flip within ' + m[1] + ' sessions';
  if ((m = /^rv(\d+)_gt_trailing(\d+)_median$/.exec(q))) return 'chance ' + m[1] + '-day realised volatility runs above its ' + m[2] + '-day median';
  if ((m = /^cohort_excess(\d+)_points/.exec(q))) return m[1] + '-session return against its peers, points';
  if ((m = /^excess(\d+)_points_persist$/.exec(q))) return m[1] + '-session excess return that persists, points';
  if ((m = /^return(\d+)_pct$/.exec(q))) return m[1] + '-session return range';
  if (q === 'sessions_to_normal') return 'sessions until back to normal';
  if ((m = /^gap_down_([\d.]+)\+_range_over_gap$/.exec(q))) return 'after a ' + Math.round(+m[1] * 100) + '%+ gap down: day range as a multiple of the gap';
  if (q === 'har') return 'next-day volatility (HAR model)';
  if (/^(trend|mean_reversion|breakout|breadth|sector|leadlag)$/.test(q)) return ({leadlag: 'lead-lag', mean_reversion: 'mean-reversion'}[q] || q) + ' signal (signed score, 0 is neutral)';
  return q.replace(/:.*$/, '').replace(/_/g, ' ');
}
// a forecast engine's grade in plain words (MASTER-LIST T-132: "brier 0.0167 over 18" was unexplained jargon)
const GRADE = {brier: ['Brier score', 3, 'the squared miss of each probability: 0 is perfect, 0.25 is a coin flip'],
  crps_approx: ['average miss', 2, 'how far the forecast range sat from the outcome, in the forecast’s own units: 0 is perfect, lower is better']};
const gradeText = g => { if (!g || !isN(g.value)) return 'Not graded yet'; const k = GRADE[g.metric] || [String(g.metric || 'score').replace(/_/g, ' '), 3, ''];
  return 'Grade: ' + k[0] + ' ' + (+g.value.toFixed(k[1])) + ' over ' + g.n + ' graded forecast' + (g.n === 1 ? '' : 's') + (k[2] ? ' (' + k[2] + ')' : ''); };
// a decision's refusal codes in words, leaving out any its own text already says (MASTER-LIST T-181: "the plan is no
// longer active" beside "plan no longer active"); the rule is mybook.js's MDBK.said
const codesLine = d => (d.codes || []).map(c => window.MDBK ? window.MDBK.reason(c) : String(c).toLowerCase().replace(/_/g, ' '))
  .filter(w => !(window.MDBK && window.MDBK.said && window.MDBK.said(d.why, w))).join(' · ');
function forecasts() {
  const f = M.ed && M.ed.forecasts, es = f && f.engines || [];
  if (!es.length) return tx('e-fc', '');
  const lt = l => !l ? '<p class="mu">No forecast yet.</p>' : '<p><b>' + esc(String(l.subject).replace(/^cohort:/, '')) + '</b> ' + esc(fcq(l)) + ': ' + esc(fcv(l)) +
    ' <span class="a-lab">' + esc(l.shown_as) + '</span></p><p class="mu">Issued ' + esc(clock(l.as_of)) + (l.horizon_close ? ' · resolves ' + esc(clock(l.horizon_close)) : '') + '</p>';
  // abstaining engines are one line, not a card each (audit 2026-11-04: 32 of 51 cards said "No forecast yet")
  const ab = es.filter(e => e.state === 'abstaining' && !e.latest), on = es.filter(e => !(e.state === 'abstaining' && !e.latest));
  tx('e-fc', head('e-fc', 'Forecast engines', 'Forecasts') + (ab.length ? '<p class="mu">Abstaining today (' + ab.length + '): ' + esc(ab.map(e => e.name).join(', ')) + '</p>' : '') + '<div class="a-fcl">' + on.map(e =>
    '<div class="card a-fc"><div class="a-fh"><b>' + esc(e.name) + '</b><span class="a-fs a-f-' + esc(e.state) + '">' + esc(e.state) + '</span></div>' +
    lt(e.latest) +
    '<p>' + esc(gradeText(e.grade)) + '</p>' +
    (e.kill && e.kill.status ? '<p class="' + (e.kill.status === 'killed' ? 'd' : 'mu') + '">Kill rule: ' + esc(e.kill.status) + (e.kill.why ? ' · ' + esc(e.kill.why) : '') + '</p>' : '') + '</div>').join('') + '</div>' +
    what('Each engine issues forecasts before the outcome, abstains when its inputs are thin, and is graded when the horizon closes; an engine that fails its kill rule stops. A probability reads as a score until the engine’s calibration is attested.'));
}
const PG = (t, f) => (window.MD && window.MD.guard ? window.MD.guard(t, f) : f());   // app.js's panel guard
function finish() { PG('m-cal', calStrip); PG('m-tick', ticker); PG('d-book', book); PG('d-book', bookCharts); PG('e-fc', forecasts); }
addEventListener('resize', () => setTimeout(bookCharts, 160));
D.addEventListener('md:edition', finish);
D.addEventListener('md:tab', finish);

function load() {
  if (busy) return;
  busy = 1;
  Promise.all([get('panels.json'), get('pulse.json')]).then(([p, q]) => {
    busy = 0;
    if (p && Array.isArray(p.panels)) { pan = p; pan.byId = Object.fromEntries(p.panels.map(r => [r.id, r])); el('t-hub').hidden = false; }
    if (q && q.v === 1 && q.lines) pul = q;
    PG('p-market', pulseAll); PG('m-psy', psych); PG('p-market', morgueSecs); finish(); PG('hubl', hub); PG('hubsla', slaBoard); PG('main', tidy);
  });
}
D.addEventListener('md:edition', load);
D.addEventListener('md:tab', load);
load();
})();
