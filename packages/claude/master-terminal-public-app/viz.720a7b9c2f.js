/* Master Desk terminal, the visual layer (deferred after app.js). Navigation copied from GrokBot Desk (tabs, jump chips
   with scroll-spy, back to top, "/" for Look up) and the glance strip: the market in one badge and one line, the record
   in one picture. Every label uses app.js's own formatters (window.MD); nothing the edition words is recomputed. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id), $$ = (s, r) => [...(r || D).querySelectorAll(s)];
const esc = M.esc, isN = M.isN, TABS = ['setups', 'market', 'desk', 'record', 'engine', 'how'], TONE = {up: 'up', warn: 'wn', down: 'dn'};
const quiet = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
let tab = '', keys = true;

// ---- tabs: a tab shows only once its panel has content (Desk and Engine are filled by their own builders) --------------
function show(t) {
  if (!TABS.includes(t) || el('t-' + t).hidden) t = 'setups';
  if (t === tab) return;
  tab = t;
  load(el('p-' + t));
  TABS.forEach(x => {
    const b = el('t-' + x), on = x === t;
    b.setAttribute('aria-selected', on);
    b.tabIndex = on ? 0 : -1;
    el('p-' + x).hidden = !on;
  });
  jump();
  D.dispatchEvent(new CustomEvent('md:tab', {detail: t}));   // a tab's own script (market.js, desk.js) loads on its first open
}
// a panel's own files (data-css, data-js: ui2's market and engine, ui3's desk) load on its first open, once
function load(p) {
  if (p.dataset.ld) return;
  p.dataset.ld = 1;
  if (p.dataset.css) { const l = D.createElement('link'); l.rel = 'stylesheet'; l.href = p.dataset.css; D.head.appendChild(l); }
  if (p.dataset.js) { const s = D.createElement('script'); s.src = p.dataset.js; D.head.appendChild(s); }
}
// the hash keeps the tab and the open card: #market, #record, a section's id, #bs-SYM (GrokBot's route), #s=ID, or
// #e=SYM, a name on the engine screen (the Engine tab reads it)
function route() {
  const h = decodeURIComponent(location.hash.slice(1)), n = h && !h.includes('=') && !h.startsWith('bs-') && el(h);
  if (TABS.includes(h)) { show(h); return scrollTo(0, 0); }
  if (h.startsWith('e=')) return show('engine');
  const p = n && n.closest('.panel');
  show(p ? p.id.slice(2) : 'setups');
  if (p && !TABS.includes(h)) { jmp = n; n.scrollIntoView(); }
  if (h.startsWith('bs-') || h.startsWith('s=')) M.deep();
}
addEventListener('hashchange', route);
el('nav').querySelector('.tabs').addEventListener('keydown', e => {          // the tabs pattern: arrows move between tabs
  const on = $$('.tab:not([hidden])', el('nav')), i = on.indexOf(D.activeElement), k = {ArrowRight: 1, ArrowLeft: -1}[e.key];
  if (i < 0 || !k) return;
  e.preventDefault();
  const b = on[(i + k + on.length) % on.length];
  b.focus();
  b.click();
});

// ---- jump chips: one per section of the open tab; the spy marks the section under the sticky bars, the last at the end ---
function secs() { return $$('[data-jump]', el('p-' + tab)).filter(s => !s.hidden); }
function jump() {
  const j = el('jump'), s = secs();
  j.replaceChildren(...s.map(x => {
    const a = D.createElement('a');
    a.href = '#' + x.id;
    a.textContent = x.dataset.jump;
    return a;
  }));
  spy();
}
let jmp = null;                                   // the section last jumped to: at the page end it stays lit while in view
function spy() {
  const s = secs(), lim = el('nav').getBoundingClientRect().bottom + 12, end = innerHeight + scrollY >= D.documentElement.scrollHeight - 4;
  let k = 0;
  s.forEach((x, i) => { if (x.getBoundingClientRect().top <= lim) k = i; });
  if (end && s.length) k = s.includes(jmp) && jmp.getBoundingClientRect().top < innerHeight ? s.indexOf(jmp) : s.length - 1;
  $$('a', el('jump')).forEach((a, i) => {
    if (a.classList.toggle('on', i === k) && a.offsetLeft + a.offsetWidth > a.parentNode.scrollLeft + a.parentNode.clientWidth) a.parentNode.scrollLeft = a.offsetLeft - 8;
    else if (i === k && a.offsetLeft < a.parentNode.scrollLeft) a.parentNode.scrollLeft = a.offsetLeft - 8;
  });
  el('totop').hidden = scrollY < innerHeight;
}
let raf = 0;
addEventListener('scroll', () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; spy(); }); }, {passive: true});
el('jump').addEventListener('click', e => {
  const a = e.target.closest('a'), n = a && el(a.hash.slice(1));
  if (!n) return;
  e.preventDefault();
  history.replaceState(null, '', a.hash);
  jmp = n;
  n.scrollIntoView({behavior: quiet() ? 'auto' : 'smooth'});
  $$('a', el('jump')).forEach(x => x.classList.toggle('on', x === a));
});
el('totop').addEventListener('click', () => scrollTo({top: 0, behavior: quiet() ? 'auto' : 'smooth'}));

// ---- Look up: the header button, and "/" anywhere but a text field (switched off in About) --------------------------------
function look() {
  if (el('look').hidden) return;
  show('setups');
  el('look').scrollIntoView();
  el('lq').focus({preventScroll: true});
}
el('lookb').addEventListener('click', look);
D.addEventListener('keydown', e => {
  if (e.key !== '/' || !keys || e.ctrlKey || e.metaKey || e.altKey || e.target.closest('input,textarea,select,[contenteditable]')) return;
  e.preventDefault();
  look();
});
el('keys').addEventListener('click', e => { keys = !keys; e.currentTarget.textContent = keys ? 'Turn it off' : 'Turn it on'; });

// ---- a panel's title opens its explanation (the details.wh after its header): the surface stays the same, the title is the link
$$('details.wh').forEach(w => { const h = w.previousElementSibling && w.previousElementSibling.querySelector('h2'); if (!h) return;
  h.classList.add('whh'); h.tabIndex = 0; h.setAttribute('role', 'button'); h.setAttribute('aria-expanded', 'false');
  const t = () => { w.open = !w.open; h.setAttribute('aria-expanded', w.open); };
  h.addEventListener('click', t); h.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); t(); } }); });
// ---- the glance strip -----------------------------------------------------------------------------------------------------
function glance(d) {
  const m = d.market || {}, b = m.badge, ch = {};
  (m.chips || []).forEach(c => { ch[c.id] = c; });
  let mk = '';
  if (b && b.word) mk = '<button class="gl" type="button" aria-expanded="false" aria-controls="glc"><span class="st ' + (TONE[b.tone] || 'wn') + '">' + esc(b.word) +
    '</span><span class="gd" aria-label="' + (b.checks || []).filter(c => c.ok).length + ' of ' + (b.checks || []).length + ' trend checks pass">' + (b.checks || []).map(c => '<i class="' + (c.ok ? 'ok' : 'no') + '"></i>').join('') +
    '</span><span class="gt">' + esc(b.line) + '</span><span class="go" aria-hidden="true">›</span></button><ul class="glc" id="glc" hidden>' +
    (b.checks || []).map(c => '<li class="' + (c.ok ? 'ok' : 'no') + '"><span class="sr">' + (c.ok ? 'Yes: ' : 'No: ') + '</span>' + esc(c.label) + '</li>').join('') + '</ul>';
  else if (ch.participation) {                    // until the badge is published: the participation chip, as published
    const c = ch.participation, t = ch.trend;
    mk = '<a class="gl" href="#market"><span class="st ' + (c.tone === 'up' ? 'up' : 'dn') + '">' + esc(c.value) + '</span><span class="gt">' +
      esc('of stocks above their 50-day' + (t ? ' · ' + t.label + ' ' + t.value : '')) + '</span><span class="go" aria-hidden="true">›</span></a>';
  }
  // the record: a square per read call, the last 25, oldest first, coloured by how it stands (GrokBot's closed-trade
  // colours); a tap on one writes its call in the summary's place, a second tap puts the summary back
  const rc = (d.calls || []).filter(c => c.kind === 'read').sort((x, y) => Date.parse(x.opened) - Date.parse(y.opened) || (x.id > y.id ? 1 : -1)).slice(-25);
  const n = {won: 0, lost: 0, open: 0, waiting: 0, missed: 0, ended: 0}, sc = d.scorecard || {};
  const sq = rc.map(c => {
    const k = kind(c);
    n[k]++;
    return '<button class="q ' + k + '" type="button" aria-label="' + esc(said(c)) + '"></button>';
  });
  const won = !sc.closed ? '' : sc.closed < 30 ? sc.hits + ' of ' + sc.closed + ' won' : M.num(sc.hit_rate * 100, 0) + '% won';
  words = [won, isN(sc.mean_r) ? 'mean ' + M.num(sc.mean_r, 2, 1) + 'R' : '', sc.closed && sc.closed < 30 ? 'too few to judge' : ''].filter(Boolean).join(' · ');
  const lab = 'The last ' + rc.length + ' calls: ' + Object.keys(n).filter(k => n[k]).map(k => n[k] + ' ' + k).join(', ');
  const rec = rc.length ? '<div class="gl gr"><a class="grh" href="#record"><span class="gk">Record</span><span class="gt" id="grt" aria-live="polite">' + esc(words) +
    '</span><span class="go" aria-hidden="true">›</span></a><div class="qs" role="group" aria-label="' + esc(lab) + '">' + sq.join('') + '</div></div>' : '';
  const g = el('glance');
  g.innerHTML = mk + rec;
  g.hidden = !(mk || rec);
}
let words = '';
const kind = c => c.status === 'closed' ? (c.outcome_r > 0 ? 'won' : 'lost') : ['open', 'waiting', 'missed'].includes(c.status) ? c.status : 'ended';
const ST = {open: 'bought', closed: 'closed', waiting: 'waiting to buy', missed: 'missed', expired: 'expired', void: 'void'};
// a call in words, from its own fields, as the record table words it: "RMD · closed · target · +4.1% · +1.54R · listed Wed, Oct 21"
const said = c => [c.symbol, ST[c.status] || c.status, c.status === 'closed' && c.exit, isN(c.outcome_pct) && M.pct(c.outcome_pct, 1),
  isN(c.outcome_r) && M.num(c.outcome_r, 2, 1) + 'R', 'listed ' + M.day(c.opened)].filter(Boolean).join(' · ');
el('glance').addEventListener('click', e => {
  const q = e.target.closest('.q');
  if (q) {
    const on = !q.classList.contains('sel');
    $$('.q', el('glance')).forEach(x => x.classList.remove('sel'));
    q.classList.toggle('sel', on);
    el('grt').textContent = on ? q.getAttribute('aria-label') : words;
    return;
  }
  const b = e.target.closest('button.gl');
  if (!b) return;
  const on = b.getAttribute('aria-expanded') !== 'true';
  b.setAttribute('aria-expanded', on);
  el('glc').hidden = !on;
});

// ---- charts.json: the desk's own bars (mkt1), fetched once the first edition is drawn (owner ruling 2026-10-26) ----------
let CH = null, chP = null;
const isA = Array.isArray, nums = a => isA(a) && a.every(v => v === null || isN(v));
function charts() {
  return chP || (chP = fetch('charts.json', {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(j => { if (j && typeof j.syms === 'object' && typeof j.spark === 'object') CH = j; return CH; }).catch(() => { chP = null; }));
}
const bars = b => b && isA(b.d) && b.d.length > 9 && ['o', 'h', 'l', 'c'].every(k => nums(b[k]) && b[k].length === b.d.length) ? b : null;
const usd = v => M.px(v, 0), bare = t => t.replace('$', '');
const lvls = s => { const p = s.plan, c = s.close, at = v => c * (1 + v / 100);   // the plan in dollars, as the cells word it
  return isN(c) && p && isN(p.out) && isN(p.t1) ? {zlo: at(p.zone_lo), zhi: at(p.zone_hi), trg: p.trigger != null ? at(p.trigger) : null, out: at(p.out),
    t1: at(p.t1), t2: p.trim && isN(p.t2) ? at(p.t2) : null, Lzlo: M.px(c, p.zone_lo, -1), Lzhi: M.px(c, p.zone_hi, -1), Lout: M.px(c, p.out, 1),
    Lt1: M.px(c, p.t1, -1), Lt2: p.trim && isN(p.t2) ? M.px(c, p.t2, -1) : '', Pt1: M.pl(p.t1), Pt2: p.trim && isN(p.t2) ? M.pl(p.t2) : ''} : null; };

// the card's sparkline: Muse's (30 closes, up teal or down red, a dashed gold entry line, an end dot) with the plan drawn
// in the space to its right as GrokBot draws it: the buy box, the stop line, the target and the arrow to it
function spark(box, s) {
  const cs = CH && CH.spark && CH.spark[s.symbol], P = lvls(s);
  if (!nums(cs) || cs.length < 10 || !P) return;
  const W = Math.max(200, box.clientWidth), H = 64, F = Math.round(W * .22), PW = W - F, n = cs.length, ent = P.trg != null ? P.trg : P.zhi;
  let lo = Math.min(...cs, P.out, P.zlo), hi = Math.max(...cs, P.zhi);       // the closes and the buy: a far target waits at the top
  if (P.t1 <= hi + .6 * (hi - lo)) hi = Math.max(hi, P.t1);
  const pad = (hi - lo) * .08 || 1; lo -= pad; hi += pad;
  const X = i => (2 + i * (PW - 8) / (n - 1)).toFixed(1), Y = v => Math.max(2, 2 + (hi - v) * (H - 4) / (hi - lo)).toFixed(1), up = cs[n - 1] >= cs[0];
  const bx = PW + 4, bw = F * .36, tx = PW + F * .62, last = cs[n - 1];
  const ch = (cs[n - 1] / cs[0] - 1) * 100;
  const lab = s.symbol + ': the last ' + n + ' closes, ' + (up ? 'up ' : 'down ') + M.num(Math.abs(ch), 1) + '% from ' + usd(cs[0]) + ' to ' + usd(last) + '; buy ' +
    P.Lzlo + ' to ' + bare(P.Lzhi) + ', stop ' + P.Lout + ', target ' + P.Lt1 + (P.t2 ? ' and ' + P.Lt2 : '');
  box.innerHTML = '<svg class="spk" viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" role="img" aria-label="' + esc(lab) + '">' +
    '<rect class="zb" x="0" y="' + Y(P.zhi) + '" width="' + W + '" height="' + Math.max(2, Y(P.zlo) - Y(P.zhi)).toFixed(1) + '"/>' +
    '<line class="so" x1="0" x2="' + W + '" y1="' + Y(P.out) + '" y2="' + Y(P.out) + '"/>' +
    '<line class="en" x1="0" x2="' + PW + '" y1="' + Y(ent) + '" y2="' + Y(ent) + '"/>' +
    '<rect class="bx" x="' + bx + '" y="' + Y(P.zhi) + '" width="' + bw.toFixed(1) + '" height="' + Math.max(3, Y(P.zlo) - Y(P.zhi)).toFixed(1) + '" rx="2"/>' +
    '<line class="t1" x1="' + (tx - 6).toFixed(1) + '" x2="' + W + '" y1="' + Y(P.t1) + '" y2="' + Y(P.t1) + '"/>' +
    (P.t2 ? '<line class="t1 t2" x1="' + (tx + 6).toFixed(1) + '" x2="' + W + '" y1="' + Y(P.t2) + '" y2="' + Y(P.t2) + '"/>' : '') +
    '<line class="ar" x1="' + (bx + bw).toFixed(1) + '" y1="' + Y((P.zlo + P.zhi) / 2) + '" x2="' + tx.toFixed(1) + '" y2="' + (+Y(P.t1) + 3).toFixed(1) + '"/>' +
    '<polyline class="cl ' + (up ? 'u' : 'd') + '" points="' + cs.map((v, i) => X(i) + ',' + Y(v)).join(' ') + '"/>' +
    '<circle class="ed" cx="' + X(n - 1) + '" cy="' + Y(last) + '" r="3"/></svg>';
}

// ---- the plan chart (GrokBot's bsCVChart, copied): candles, the averages labelled at their right ends, the bars the read
// cites circled, its lines dashed, the buy box, "wrong below", the target arrow, right-axis tags, Daily / Weekly ---------
const COL = {up: '#26a69a', dn: '#ef5350', m20: '#26c6da', m50: '#ff9800', m200: '#ab47bc', mk: '#fdd835', pat: '#ffeb3b', sup: '#00bcd4', res: '#ff8a80', wav: '#b39ddb'};
const MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
const md = iso => MON[+iso.slice(5, 7) - 1] + ' ' + +iso.slice(8, 10);
function sma(c, k) { let t = 0; return c.map((v, i) => { t += v; if (i >= k) t -= c[i - k]; return i >= k - 1 ? t / k : null; }); }
function plan(host, s, wk) {
  const g0 = CH && CH.syms && CH.syms[s.symbol], B = bars(wk ? g0 && g0.w : g0), P = lvls(s);
  if (!B || !P) return false;
  const n = B.d.length, DT = B.d, O = B.o, Hh = B.h, Lw = B.l, C = B.c, nar = innerWidth < 600;
  const W = Math.max(300, Math.round(host.clientWidth || 600)), L = 4, T = 10, FS = nar ? 10 : 10.5, CW = nar ? 5.9 : 6.3;
  const last = C[n - 1];
  const TG = [{k: 'last', v: last, t: bare(usd(last)), bg: last >= O[n - 1] ? COL.up : COL.dn, pr: 0}, {k: 'stop', v: P.out, t: bare(P.Lout), bg: '#c62828', pr: 1},
    {k: 'buy', v: (P.zlo + P.zhi) / 2, t: bare(P.Lzlo) + '–' + bare(P.Lzhi), bg: '#1d7f75', pr: 2}, {k: 't1', v: P.t1, t: bare(P.Lt1), bg: '#2962ff', pr: 3}]
    .concat(P.t2 ? [{k: 't2', v: P.t2, t: bare(P.Lt2), bg: '#1e3a8a', pr: 4, opt: 1}] : []);
  const R = Math.max(nar ? 52 : 60, Math.ceil(Math.max(...TG.map(t => t.t.length)) * CW + 10)), PW = W - L - R, FUT = Math.round(PW * (nar ? .18 : .25)), BWD = PW - FUT;
  // the averages: the ones the read publishes (avgs), or the three; weekly: 10- and 40-week, from the weekly closes
  const av = s.avgs || {sma20: 1, sma50: 1, sma200: 1}, MA = [];
  if (wk) [[10, COL.m50, '10-week'], [40, COL.m200, '40-week']].forEach(m => MA.push({a: sma(C, m[0]), c: m[1], lab: m[2]}));
  else [['sma20', COL.m20, '20-day'], ['sma50', COL.m50, '50-day'], ['sma200', COL.m200, '200-day']].forEach(m => {
    const a = g0[m[0]];
    if (av[m[0]] != null && nums(a) && a.length === n) MA.push({a, c: m[1], lab: m[2] + ' ' + usd(isN(s.avgs && s.avgs[m[0]]) ? s.avgs[m[0]] : a[n - 1])});
  });
  const PH = nar ? 230 : 380, AX = 20, Ht = T + PH + AX;
  let lo = Math.min(...Lw), hi = Math.max(...Hh);
  const s0 = hi - lo;
  [P.zlo, P.zhi, P.out, P.t1].forEach(v => { lo = Math.min(lo, v); hi = Math.max(hi, v); });
  const t2in = P.t2 && P.t2 <= hi + .45 * s0;
  if (t2in) hi = Math.max(hi, P.t2);
  const pad = (hi - lo) * .06; lo -= pad; hi += pad;
  const X = i => L + (i + .5) * BWD / n, Y = v => T + (hi - v) * PH / (hi - lo), xN = X(n - 1), x9 = W - R - 4, bw = Math.max(1.2, BWD / n * .66);
  const cl = (v, a, b) => Math.max(a, Math.min(b, v)), f1 = v => v.toFixed(1);
  // a date's bar: daily, the bar of that date; weekly, the week (dated by its first session) that holds it
  const bi = iso => { if (!iso) return -1; if (!wk) return DT.indexOf(iso); let k = -1; for (let i = 0; i < n && DT[i] <= iso; i++) k = i; return k; };
  const BX = [], ovl = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
  const hitsC = q => { let h = 0; for (let i = 0; i < n; i++) { const cx = X(i); if (cx < q.x0 - bw || cx > q.x1 + bw) continue; if (Y(Hh[i]) < q.y1 && Y(Lw[i]) > q.y0) h++; } return h; };
  const lab = (x, y, txt, col, anc, o) => {       // GrokBot's label placement: the free spot nearest its mark, a leader line when moved
    o = o || {};
    const w = txt.length * CW * .95 + 8, h = 15, Cs = o.cands || [[x, y]];
    let best = null;
    Cs.forEach(([cx, cy], ci) => {
      for (const d of (o.cands ? [0, -1, 1] : [0, -1, 1, -2, 2, -3, 3, -4, 4, -6, 6])) {
        const x0 = cl(anc === 'end' ? cx - w : anc === 'mid' ? cx - w / 2 : cx, L + 2, W - R - w - 2), y0 = cl(cy - 11 + d * (h + 1), T + 1, T + PH - h - 1), q = {x0, y0, x1: x0 + w, y1: y0 + h};
        const sc = BX.filter(b => ovl(b, q)).length * 1e3 + hitsC(q) * 5 + Math.abs(d) * 3 + ci * (o.step || 4);
        if (!best || sc < best.sc) best = {sc, q};
      }
    });
    BX.push(best.q);
    const b = best.q;
    let ld = '';
    if (o.from) {
      const [fx, fy] = o.from, nx = cl(fx, b.x0, b.x1), ny = cl(fy, b.y0, b.y1);
      if (Math.hypot(nx - fx, ny - fy) > (o.r || 10) + 4) ld = '<line x1="' + f1(fx) + '" y1="' + f1(fy) + '" x2="' + f1(nx) + '" y2="' + f1(ny) + '" stroke="' + col + '" stroke-width="1" opacity=".7"/>';
    }
    return ld + '<g class="cvl"><rect x="' + f1(b.x0) + '" y="' + f1(b.y0) + '" width="' + f1(w) + '" height="' + h + '" rx="3" fill="#131722" opacity=".88"/><text x="' + f1(b.x0 + 4) +
      '" y="' + f1(b.y0 + 11) + '" font-size="' + FS + '" font-weight="700" fill="' + col + '">' + esc(txt) + '</text></g>';
  };
  const arr = (id, col) => '<marker id="' + id + '" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="' + col + '"/></marker>';
  const cid = 'cv' + s.symbol.replace(/\W/g, '') + (wk ? 'w' : 'd');
  let g = '<defs><clipPath id="' + cid + 'p"><rect x="' + L + '" y="' + T + '" width="' + PW + '" height="' + PH + '"/></clipPath>' + arr(cid + 'g', COL.up) + arr(cid + 'b', '#5c8dff') + '</defs><rect width="' + W + '" height="' + Ht + '" fill="#131722"/>';
  // round-number gridlines, their labels on the right axis where no tag sits; month ticks along the bottom
  const sp = hi - lo, raw = sp / 5, mag = Math.pow(10, Math.floor(Math.log10(raw))), step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(q => q >= raw) || 10 * mag, GR = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) { const y = Y(v); g += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + f1(y) + '" y2="' + f1(y) + '" stroke="#262a35"/>'; GR.push([y, usd(v).replace(/\.00$/, '')]); }
  let lm = '', lx = -99;
  DT.forEach((d, i) => {
    const m = d.slice(0, 7), mo = +d.slice(5, 7);
    if (m === lm) return;
    lm = m;
    if (wk && mo % 3 !== 1) return;
    const mt = MON[mo - 1] + (mo === 1 || (wk && i < 3) ? ' ’' + d.slice(2, 4) : '');
    if (X(i) < lx) return;
    lx = X(i) + mt.length * 6.2 + 8;
    g += '<line x1="' + f1(X(i)) + '" x2="' + f1(X(i)) + '" y1="' + T + '" y2="' + (Ht - AX) + '" stroke="#1c2029"/><text x="' + f1(X(i) + 2) + '" y="' + (Ht - 6) + '" font-size="10.5" fill="#787b86">' + mt + '</text>';
  });
  g += '<line x1="' + f1(xN + bw) + '" x2="' + f1(xN + bw) + '" y1="' + T + '" y2="' + (T + PH) + '" stroke="#363a45" stroke-dasharray="2 4"/><g clip-path="url(#' + cid + 'p)">';
  if (nums(B.v) && B.v.length === n) { const mx = Math.max(...B.v) || 1, VH = PH * .16; B.v.forEach((v, i) => { const h = v / mx * VH; g += '<rect x="' + f1(X(i) - bw / 2) + '" y="' + f1(T + PH - h) + '" width="' + f1(bw) + '" height="' + f1(h) + '" fill="' + (C[i] >= O[i] ? COL.up : COL.dn) + '" opacity=".22"/>'; }); }
  // the read's lines (int1): patterns dashed yellow, trendlines, the wave legs; weekly waves only on the weekly chart
  const LBL = [];
  (s.lines || []).forEach(q => {
    if (!q || !isN(q.p1) || !isN(q.p2) || (q.kind === 'weekly_wave') !== !!wk && (q.kind === 'weekly_wave' || q.kind === 'wave') || nar && /wave/.test(q.kind)) return;
    const i1 = bi(q.d1), i2 = bi(q.d2);
    if (i1 < 0 || i2 < 0) return;
    const col = q.kind === 'pattern' ? COL.pat : q.kind === 'trendline' ? (/resist/i.test(q.label) ? COL.res : COL.sup) : COL.wav;
    g += '<line x1="' + f1(X(i1)) + '" y1="' + f1(Y(q.p1)) + '" x2="' + f1(X(i2)) + '" y2="' + f1(Y(q.p2)) + '" stroke="' + col + '" stroke-width="' + (q.kind === 'pattern' ? 1.5 : 1.3) + '"' + (q.kind === 'pattern' ? ' stroke-dasharray="6 4" opacity=".85"' : q.kind === 'trendline' ? ' opacity=".9"' : ' opacity=".8"') + '/>';
    if (/wave/.test(q.kind)) { if (Y(q.p2) > T + 8 && Y(q.p2) < T + PH - 8) LBL.push([X(i2), Y(q.p2) + (q.p2 >= q.p1 ? -6 : 15), q.label.replace('Wave ', ''), col, 'mid']); }
    else if (Y(q.p1) > T + 8 && Y(q.p1) < T + PH - 8 && !(nar && LBL.length)) LBL.push([cl(X(i1), L + 4, xN - 60), Y(q.p1) - 6, q.label, col, '']);   // a phone names one line
  });
  for (let i = 0; i < n; i++) {
    const col = C[i] >= O[i] ? COL.up : COL.dn;
    g += '<line x1="' + f1(X(i)) + '" x2="' + f1(X(i)) + '" y1="' + f1(Y(Hh[i])) + '" y2="' + f1(Y(Lw[i])) + '" stroke="' + col + '"/><rect x="' + f1(X(i) - bw / 2) + '" y="' + f1(Y(Math.max(O[i], C[i]))) +
      '" width="' + f1(bw) + '" height="' + f1(Math.max(1, Math.abs(Y(O[i]) - Y(C[i])))) + '" fill="' + col + '"/>';
  }
  MA.forEach(m => { const pt = m.a.map((v, i) => v == null ? null : f1(X(i)) + ',' + f1(Y(v))).filter(Boolean); if (pt.length > 1) g += '<polyline points="' + pt.join(' ') + '" fill="none" stroke="' + m.c + '" stroke-width="1.6" opacity=".95"/>'; });
  g += '</g>';
  // the plan, in the empty space to the right of the last bar
  const yL = Y(last), fx = q => xN + bw + FUT * q, bx0 = fx(.04), bx1 = fx(.36), ym = Y((P.zlo + P.zhi) / 2), xs = X(Math.max(0, n - (wk ? 6 : 14)));
  g += '<line x1="' + f1(xs) + '" x2="' + x9 + '" y1="' + f1(Y(P.out)) + '" y2="' + f1(Y(P.out)) + '" stroke="#ef5350" stroke-width="1.6" stroke-dasharray="6 4"/>' +
    '<line x1="' + f1(fx(.55)) + '" x2="' + x9 + '" y1="' + f1(Y(P.t1)) + '" y2="' + f1(Y(P.t1)) + '" stroke="#5c8dff" stroke-width="1.5"/>' +
    (t2in ? '<line x1="' + f1(fx(.75)) + '" x2="' + x9 + '" y1="' + f1(Y(P.t2)) + '" y2="' + f1(Y(P.t2)) + '" stroke="#5c8dff" stroke-width="1.2" stroke-dasharray="2 3"/>' : '') +
    '<rect x="' + f1(bx0) + '" y="' + f1(Y(P.zhi)) + '" width="' + f1(bx1 - bx0) + '" height="' + f1(Math.max(4, Y(P.zlo) - Y(P.zhi))) + '" rx="2" fill="#26a69a" opacity=".3" stroke="#26a69a" stroke-width="1.4"/>' +
    (Math.abs(yL - ym) > 6 ? '<line x1="' + f1(xN + bw) + '" y1="' + f1(yL) + '" x2="' + f1((bx0 + bx1) / 2) + '" y2="' + f1(ym) + '" stroke="#26a69a" stroke-width="1.6" marker-end="url(#' + cid + 'g)"/>' : '') +
    '<line x1="' + f1(bx1) + '" y1="' + f1(ym) + '" x2="' + f1(fx(.62)) + '" y2="' + f1(Y(P.t1) + 3) + '" stroke="#5c8dff" stroke-width="1.8" marker-end="url(#' + cid + 'b)"/>' +
    (t2in ? '<line x1="' + f1(fx(.62)) + '" y1="' + f1(Y(P.t1)) + '" x2="' + f1(fx(.86)) + '" y2="' + f1(Y(P.t2) + 3) + '" stroke="#5c8dff" stroke-width="1.6" stroke-dasharray="3 3" marker-end="url(#' + cid + 'b)"/>' : '');
  BX.push({x0: bx0, y0: Y(P.zhi), x1: bx1, y1: Y(P.zlo)});
  const EM = s.engine, LD = s.lod, XL = [], XR = [], KY = [];   // the typical move by its date (the engine), the low-of-day zone (ChartsLector)
  if (EM && isN(EM.em) && EM.em > 0 && !wk) { const y1 = Y(last * (1 + EM.em / 100)), y2 = Y(last * (1 - EM.em / 100)), by = EM.em_by ? ' by ' + md(EM.em_by) : '';
    g += '<rect x="' + f1(xN + bw) + '" y="' + f1(y1) + '" width="' + f1(x9 - xN - bw) + '" height="' + f1(y2 - y1) + '" fill="#9aa3b8" opacity=".1"/>';
    XL.push([x9, y1 - 4, (nar ? '' : 'typical move ') + '±' + M.num(EM.em, 1) + '%' + by, '#9aa3b8', 'end', {cands: [[x9, y1 - 4], [x9, y2 + 15]], step: 2}]);
    XR.push(['Typical move', by.trim(), '±' + M.num(EM.em, 1) + '%, ' + usd(last * (1 - EM.em / 100)) + ' to ' + usd(last * (1 + EM.em / 100))]); KY.push('Grey band: the typical move by its date'); }
  if (LD && isN(LD.zone_low) && isN(LD.zone_high) && isN(LD.stop)) { const lc = {blue: '#5c8dff', orange: '#ff9800', red: '#ef5350'}[LD.state] || '#b39ddb', zt = usd(LD.zone_low) + '–' + bare(usd(LD.zone_high));
    g += '<rect x="' + f1(fx(.4)) + '" y="' + f1(Y(LD.zone_high)) + '" width="' + f1(fx(.52) - fx(.4)) + '" height="' + f1(Math.max(3, Y(LD.zone_low) - Y(LD.zone_high))) + '" fill="' + lc + '" opacity=".25" stroke="' + lc + '"/>' +
      '<line x1="' + f1(fx(.38)) + '" x2="' + f1(fx(.54)) + '" y1="' + f1(Y(LD.stop)) + '" y2="' + f1(Y(LD.stop)) + '" stroke="' + lc + '" stroke-width="1.4" stroke-dasharray="3 2"/>';
    // a phone's plot has no room for this label: the key and the Chart values row name the box there
    if (!nar) XL.push([fx(.46), Y(LD.stop) + 15, 'low of day ' + zt, lc, 'mid', {cands: [[fx(.46), Y(LD.stop) + 15], [fx(.46), Y(LD.zone_high) - 6], [fx(.3), Y(LD.stop) + 15], [fx(.3), Y(LD.zone_high) - 6]],
      from: [fx(.46), (Y(LD.zone_low) + Y(LD.zone_high)) / 2], r: 8, step: 2}]);
    XR.push(['Low-of-day zone', 'ChartsLector’s rule', zt + ', his stop ' + usd(LD.stop)]); KY.push('Small box: ChartsLector’s low-of-day zone and his stop'); }
  // the bars the read cites: its most recent marks inside the window, circled (GrokBot: three; ours: four)
  const MK = (s.marks || []).filter(m => m && m.d && (m.kind === 'weekly_wave') === !!wk).map(m => Object.assign({i: bi(m.d)}, m)).filter(m => m.i >= 0).slice(nar ? -2 : -4);
  let EV = '';
  MK.forEach(m => {
    const x = X(m.i), yl = Y(Lw[m.i]), yh = Y(Hh[m.i]), cy = (yl + yh) / 2, r = Math.max(9, (yl - yh) / 2 + 5);
    EV += '<ellipse cx="' + f1(x) + '" cy="' + f1(cy) + '" rx="' + f1(Math.max(8, bw * 1.6)) + '" ry="' + f1(r) + '" fill="none" stroke="' + COL.mk + '" stroke-width="1.8"/>';
    BX.push({x0: x - 8, y0: cy - r, x1: x + 8, y1: cy + r});
    const upm = /high|top|peak|resist/i.test(m.label), yA = cy - r - 6, yB = cy + r + 15, Cs = [];
    for (const dx of [0, -40, 40, -80, 80, -120, 120]) for (const yy of (upm ? [yA, yB] : [yB, yA])) Cs.push([x + dx, yy]);
    m._l = [x, yB, m.label + ' · ' + md(m.d), Cs, [x, cy, r]];
  });
  let LB = lab(bx0, Y(P.zhi) - 4, 'buy ' + P.Lzlo + '–' + bare(P.Lzhi), '#4dd0b5', '') + lab(xs, Y(P.out) + 15, 'wrong below ' + P.Lout, '#ff6f6b', '') +
    lab(fx(.62), Y(P.t1) - 6, 'T1 ' + P.Lt1 + ' ' + P.Pt1, '#8fb0ff', 'mid') + (P.t2 ? lab(x9, t2in ? Y(P.t2) - 6 : T + 14, 'T2 ' + P.Lt2 + (t2in ? '' : ' ↑') + ' ' + P.Pt2, '#8fb0ff', 'end') : '');
  MK.forEach(m => { const [x, y, t, Cs, c3] = m._l; LB += lab(x, y, t, COL.mk, 'mid', {cands: Cs, from: [c3[0], y < c3[1] ? c3[1] - c3[2] : c3[1] + c3[2]], r: 2, step: 3}); });
  MA.forEach(m => { const Cs = []; for (let i = n - 1; i >= Math.floor(n * .45); i -= Math.max(1, Math.round(n / 30))) { if (m.a[i] == null) continue; const ab = m.a[i] > C[i]; Cs.push([X(i), Y(m.a[i]) + (ab ? -5 : 15)], [X(i), Y(m.a[i]) + (ab ? 15 : -5)]); }
    if (Cs.length) LB += lab(Cs[0][0], Cs[0][1], m.lab, m.c, 'end', {cands: Cs, step: 2}); });
  LBL.concat(XL).forEach(q => { LB += lab(q[0], q[1], q[2], q[3], q[4], q[5]); });
  g += EV + LB;
  // the right axis: priority placement 17 px apart; T2 dropped if it would have to move; a leader line when a tag moves
  const TH = 16, GP = 17, yMin = T + 8, yMax = T + PH - 8, placed = [];
  TG.forEach(t => { t.y0 = Y(t.v); t.off = t.y0 < T || t.y0 > T + PH; t.y = cl(t.y0, yMin, yMax); });
  TG.slice().sort((a, b) => a.pr - b.pr).forEach(t => {
    const free = y => placed.every(q => Math.abs(q.y - y) >= GP) && y >= yMin && y <= yMax;
    let y = t.y;
    if (!free(y)) { y = null; for (let d = 1; d <= 400 && y == null; d++) for (const sg of [1, -1]) if (free(t.y + sg * d)) { y = t.y + sg * d; break; } }
    if (y == null || (t.opt && Math.abs(y - t.y) > 4)) { t.drop = 1; return; }
    t.y = y;
    placed.push(t);
  });
  const TQ = TG.filter(t => !t.drop);
  GR.forEach(([y, t]) => { if (TQ.every(q => Math.abs(y - q.y) >= 14) && y > T + 6 && y < T + PH - 2) g += '<text x="' + (W - R + 5) + '" y="' + f1(y + 3.5) + '" font-size="10" fill="#6b6f7b">' + t + '</text>'; });
  TQ.forEach(q => {
    if (Math.abs(q.y - q.y0) > 3 && !q.off) g += '<path d="M' + (W - R - 6) + ' ' + f1(q.y0) + 'L' + (W - R + 2) + ' ' + f1(q.y) + '" stroke="' + q.bg + '" stroke-width="1.2" fill="none"/>';
    g += '<rect x="' + (W - R + 2) + '" y="' + f1(q.y - TH / 2) + '" width="' + (R - 4) + '" height="' + TH + '" rx="3" fill="' + q.bg + '"/><text x="' + (W - R + 5) + '" y="' + f1(q.y + 3.8) +
      '" font-size="' + FS + '" font-weight="700" fill="#fff">' + esc(q.t) + (q.off ? (q.y0 < T ? ' ↑' : ' ↓') : '') + '</text>';
  });
  g += '<line class="xh" y1="' + T + '" y2="' + (T + PH) + '"/>';
  const aria = s.symbol + (wk ? ' weekly' : ' daily') + ' chart, ' + md(DT[0]) + ' to ' + md(DT[n - 1]) + ': last close ' + usd(last) + '; buy ' + P.Lzlo + ' to ' + bare(P.Lzhi) +
    '; wrong below ' + P.Lout + '; target ' + P.Lt1 + (P.t2 ? ', then ' + P.Lt2 : '') + (MA.length ? '; ' + MA.map(m => m.lab).join(', ') : '') + (MK.length ? '; marked: ' + MK.map(m => m.label + ' ' + md(m.d)).join(', ') : '');
  // the Values table (Codex's "Chart values"): what the picture shows, as text
  const rows = [['Last close', md(DT[n - 1]), usd(last)], ['Buy', '', P.Lzlo + '–' + bare(P.Lzhi)], ['Wrong below', 'a daily close', P.Lout], ['Target', '', P.Lt1 + ' ' + P.Pt1]]
    .concat(P.t2 ? [['Second target', '', P.Lt2 + ' ' + P.Pt2]] : []).concat(MA.map(m => [m.lab.split(' ')[0], 'average', m.lab.split(' ')[1] || ''])).concat(MK.map(m => [m.label, md(m.d), usd(C[m.i])]))
    .concat((s.lines || []).filter(q => q && isN(q.p1) && (q.kind === 'weekly_wave') === !!wk).slice(0, 12).map(q => [q.label, md(q.d1) + ' to ' + md(q.d2), usd(q.p1) + ' to ' + usd(q.p2)])).concat(XR);
  host.innerHTML = '<div class="pcv"><svg class="pcs" viewBox="0 0 ' + W + ' ' + Ht + '" width="100%" height="' + Ht + '" role="img" aria-label="' + esc(aria) + '">' + g + '</svg></div>' +
    '<p class="cap" aria-live="polite">Tap the chart for a day’s prices.</p><p class="cvk"><span class="tg" role="group" aria-label="Bars"><button type="button" data-wk="0" aria-pressed="' + !wk + '">Daily</button>' +
    '<button type="button" data-wk="1" aria-pressed="' + !!wk + '">Weekly</button></span> ' + (wk ? 'Weekly bars, about 2 years.' : 'Daily bars, about 6 months.') +
    '</p><details class="vt"><summary>Chart values</summary><p class="ckey">' + ['Green box: buy zone', 'Red: wrong below', 'Blue: targets'].concat(MK.length ? ['Yellow circles: the bars the read mentions'] : [], KY).join(' · ') +
    '.</p><table class="t"><thead><tr><th>What</th><th>When</th><th class="r">Price</th></tr></thead><tbody>' +
    rows.map(r => '<tr><th scope="row">' + esc(r[0]) + '</th><td>' + esc(r[1]) + '</td><td class="r">' + esc(r[2]) + '</td></tr>').join('') + '</tbody></table></details>';
  // a tap (or a pointer) on the chart writes that day's prices under it, with a crosshair: nothing is hover-only
  const svg = host.querySelector('svg'), cap = host.querySelector('.cap'), xh = svg.querySelector('.xh');
  const at = e => {
    const r = svg.getBoundingClientRect(), i = Math.round(cl(((e.clientX - r.left) * W / r.width - L) / (BWD / n) - .5, 0, n - 1));
    xh.setAttribute('x1', f1(X(i)));
    xh.setAttribute('x2', f1(X(i)));
    xh.classList.add('on');
    cap.textContent = (wk ? 'Week of ' : '') + M.day(DT[i]) + ' · open ' + usd(O[i]) + ' · high ' + usd(Hh[i]) + ' · low ' + usd(Lw[i]) + ' · close ' + usd(C[i]);
  };
  svg.addEventListener('pointerdown', at);
  svg.addEventListener('pointermove', e => { if (e.pointerType === 'mouse') at(e); });
  return true;
}
function plans(c) {                               // an open card's chart, in the box app.js reserves; no bars: the box closes
  const h = c.ch && c.ch.querySelector('.pc');
  if (!h || !c.s || h.dataset.k === c.sg + (h.dataset.wk || '')) return;
  if (plan(h, c.s, h.dataset.wk === '1')) h.dataset.k = c.sg + (h.dataset.wk || '');
  else h.hidden = true;
}
D.addEventListener('click', e => {
  const b = e.target.closest('.cvk button'), h = b && b.closest('.pc');
  if (!h) return;
  h.dataset.wk = b.dataset.wk;
  const c = Object.values(M.cards).find(x => x.ch && x.ch.contains(h)) || {s: null};
  if (c.s && plan(h, c.s, b.dataset.wk === '1')) h.dataset.k = c.sg + h.dataset.wk;
});
function draw() {
  Object.values(M.cards).forEach(c => {
    if (!c.s) return;
    const box = c.bd.querySelector('.mc');
    if (box && CH && !box.querySelector('.spk')) spark(box, c.s);
    if (CH && !c.det.hidden) plans(c);
  });
}
// the open card's time strip: its window, its horizon and the events inside them. A Fed day falls in every card's window
// alike, so it is drawn in each strip and never repeated as a tag on every face (no duplicated language)
function times(d) {
  const cal = (d.market || {}).calendar || [];
  Object.values(M.cards).forEach(c => {
    if (!c.s || c.db.querySelector('.tlg')) return;
    const t = timeline(c.s, cal);
    if (t) c.db.insertAdjacentHTML('afterbegin', '<div class="dg tlg"><h4>The plan’s time</h4>' + t + '</div>');
  });
}

// ---- ChartsLector's Opportunity Score (replica, `lector`): rank, symbol, score bar on 0-100, the source's date and credit
function clrank(d) {
  const L = d.lector, r = (L && L.rows) || [], box = el('clrankc');
  el('clrank').hidden = !r.length;
  if (!r.length) return;
  const P = ['Breakout', 'Expansion', 'Risk'], W = [40, 35, 25];
  box.innerHTML = '<div class="rk">' + r.map(x => '<details class="rkd"><summary class="rkr"><span class="n">' + x.rank + '</span><b>' + esc(x.symbol) + '</b><span class="rkbar"><i data-v="' + M.num(x.score, 1) +
    '"></i></span><span class="v">' + M.num(x.score, 1) + '</span></summary><div class="why">' + (x.band ? '<p class="mu">' + esc(x.band) + ' of ' + L.n + '</p>' : '') +
    (x.parts || []).map((v, i) => '<span><span>' + P[i] + ' <small class="mu">' + W[i] + '%</small></span><span class="cb"><i data-v="' + M.num(v, 1) + '"></i></span><b>' + M.num(v, 0) + '</b></span>').join('') +
    '</div></details>').join('') + '</div><p class="cap">Tap a name for its parts. ' + esc(L.credit) + '</p>';
  $$('[data-v]', box).forEach(e => { e.style.width = e.dataset.v + '%'; });
  el('clrank-meta').textContent = M.et(L.as_of + 'T16:00:00-04:00').md + ' close · ' + L.n + ' names';
}
// ---- Conviction 8's order beside it: the board and watching names by Conviction 8, its ready count and stage (context)
function lrank(d) {
  const r = [...(d.setups || []), ...(d.watching || [])].filter(x => x.lens && isN(x.lens.c8)).sort((a, b) => b.lens.c8 - a.lens.c8).slice(0, 10), box = el('lrankc');
  el('lrank').hidden = !r.length;
  if (!r.length) return;
  const cat = L => C8N.map((n, i) => '<span><span>' + n + '</span><span class="cb' + (isN(L.cats && L.cats[i]) ? ((L.c8st || '')[i] === 'C' ? ' ok' : '') + '"><i data-v="' + L.cats[i] + '"></i></span><b>' +
    L.cats[i] + ((L.c8st || '')[i] === 'C' ? ' ✓' : '') : ' nd"></span><b class="mu">no data') + '</b></span>').join('');
  box.innerHTML = '<div class="rk">' + r.map((x, i) => '<details class="rkd"><summary class="rkr"><span class="n">' + (i + 1) + '</span><b>' + esc(x.symbol) + '</b><span class="rkbar"><i data-v="' + x.lens.c8 +
    '"></i></span><span class="v">' + x.lens.c8 + '</span></summary><div class="why">' + (x.lens.stage ? '<p class="mu">' + esc(SN(x.lens.stage) + (x.lens.word ? ' · ' + x.lens.word : '')) + ' · ✓ confirmed</p>' : '') + cat(x.lens) +
    '</div></details>').join('') + '</div><p class="cap">Tap a name for its eight categories.</p>';
  $$('[data-v]', box).forEach(e => { e.style.width = e.dataset.v + '%'; });
}
const parts = x => (x.parts || []).filter(p => p && isN(p.value)).map(p => p.label + ' ' + M.num(p.value, 1, 1)).join(' · ');

// ---- the record's pictures (GrokBot's Main desk forms, for our public calls): every read call as a square; the closed
// calls as diverging bars in R (a dot for a result under 0.1R); the open calls' time left, from their own dates ---------
let rbAll = false;
function recviz(d) {
  const rc = (d.calls || []).filter(c => c.kind === 'read'), sc = d.scorecard || {};
  // the outcome strip: all read calls, oldest first, with the counts as the legend
  const old = rc.slice().sort((x, y) => Date.parse(x.opened) - Date.parse(y.opened) || (x.id > y.id ? 1 : -1)), n = {};
  old.forEach(c => { const k = kind(c); n[k] = (n[k] || 0) + 1; });
  const leg = ['won', 'lost', 'open', 'waiting', 'missed', 'ended'].filter(k => n[k]).map(k => n[k] + ' ' + k);
  el('rstrip').hidden = !rc.length;
  el('rsq').innerHTML = '<div class="qs" role="group" aria-label="' + esc(rc.length + ' read calls: ' + leg.join(', ')) + '">' + old.map(c => '<button class="q ' + kind(c) +
    '" type="button" aria-label="' + esc(said(c)) + '"></button>').join('') + '</div><p class="cap" id="rsc" aria-live="polite">' + esc(leg.join(' · ')) + '</p>';
  // closed calls in R, newest first: GrokBot's closed-trade bars, from zero
  const cl = rc.filter(c => c.status === 'closed' && isN(c.outcome_r)).sort((x, y) => Date.parse(y.opened) - Date.parse(x.opened) || (y.id > x.id ? 1 : -1));
  el('rbars').hidden = !cl.length;
  if (cl.length) {
    const mx = Math.max(2, ...cl.map(c => Math.abs(c.outcome_r))), show = rbAll ? cl : cl.slice(0, 10);
    el('rbl').innerHTML = '<p class="rbs">' + esc([sc.closed ? sc.hits + ' of ' + sc.closed + ' closed calls won' : '', isN(sc.mean_r) ? 'mean ' + M.num(sc.mean_r, 2, 1) + 'R' : ''].filter(Boolean).join(' · ')) +
      '</p>' + total(cl) + '<div class="rb" role="img" aria-label="' + esc('Closed calls in R, newest first: ' + cl.map(c => c.symbol + ' ' + M.num(c.outcome_r, 2, 1) + 'R').join(', ')) + '">' +
      show.map(c => { const r = c.outcome_r, w = M.num(Math.abs(r) / mx * 50, 1);
        return '<div class="rbr"><span class="rbn"><b>' + esc(c.symbol) + '</b><small>' + esc(c.exit || '') + '</small></span><span class="rbt"><i class="' +
          (Math.abs(r) < .1 ? 'dot' : r > 0 ? 'p' : 'n') + '" data-v="' + w + '"></i></span><span class="rbv ' + (r > 0 ? 'up' : r < 0 ? 'dn' : '') + '">' + M.num(r, 2, 1) +
          'R</span><span class="rbp">' + (isN(c.outcome_pct) ? M.pct(c.outcome_pct, 1) : '') + '</span></div>'; }).join('') + '</div>' +
      (cl.length > 10 ? '<button class="more" type="button" id="rball" aria-expanded="' + rbAll + '">' + (rbAll ? 'Show fewer' : 'Show all ' + cl.length) + '</button>' : '');
    $$('.rbt i', el('rbl')).forEach(e => { if (!e.classList.contains('dot')) e.style.width = e.dataset.v + '%'; });
  }
  // open calls: the time left, GrokBot's time-exit bar, from the call's own dates (int1: filled, stop_by); no session
  // count is worked out here
  const op = rc.filter(c => c.status === 'open' && c.filled && c.stop_by);
  el('ropen').hidden = !op.length;
  if (op.length) {
    const now = Date.now();
    el('rol').innerHTML = op.map(c => { const a = Date.parse(c.filled), b = Date.parse(c.stop_by), f = Math.max(0, Math.min(1, (now - a) / (b - a || 1)));
      return '<div class="rol"><span><b>' + esc(c.symbol) + '</b> bought ' + M.day(c.filled) + '</span><span class="hold"><i data-v="' + M.num(f * 100, 1) + '"></i></span><small>time stop ' +
        M.day(c.stop_by) + '</small></div>'; }).join('');
    $$('.hold i', el('rol')).forEach(e => { e.style.width = e.dataset.v + '%'; });
  }
}
// the running total in R (GrokBot's equity line, for calls): one step per closed call, by the day it closed
function total(cl) {
  const t = c => Date.parse(c.closed || c.opened), o = cl.slice().sort((x, y) => t(x) - t(y) || (x.id > y.id ? 1 : -1)), pts = [0];
  o.forEach(c => pts.push(pts[pts.length - 1] + c.outcome_r));
  if (o.length < 2) return '';
  const lo = Math.min(0, ...pts), hi = Math.max(0, ...pts), sp = hi - lo || 1, X = i => M.num(i / o.length * 100, 2), Y = v => M.num(46 - (v - lo) / sp * 42, 2), end = pts[pts.length - 1];
  return '<div class="rrt"><svg viewBox="0 0 100 50" preserveAspectRatio="none" role="img" aria-label="' + esc('Running total in R, by the day each call closed: ' +
    o.map((c, i) => c.symbol + ' ' + M.num(pts[i + 1], 2, 1) + 'R').join(', ')) + '"><line class="z" x1="0" x2="100" y1="' + Y(0) + '" y2="' + Y(0) + '"/><polyline class="' +
    (end >= 0 ? 'u' : 'd') + '" points="' + pts.map((v, i) => X(i) + ',' + Y(v)).join(' ') + '"/></svg><b class="' + (end > 0 ? 'up' : end < 0 ? 'dn' : '') + '">' + M.num(end, 2, 1) +
    'R</b><small>running total</small></div>';
}
D.addEventListener('click', e => {
  if (e.target.closest('#rball')) { rbAll = !rbAll; if (M.ed) recviz(M.ed); return; }
  const q = e.target.closest('#rsq .q');
  if (!q) return;
  const on = !q.classList.contains('sel');
  $$('#rsq .q').forEach(x => x.classList.remove('sel'));
  q.classList.toggle('sel', on);
  el('rsc').textContent = on ? q.getAttribute('aria-label') : '';
  if (!on && M.ed) recviz(M.ed);
});

// ---- Watching: a mini ladder per row and "trigger +x% away" (the review's Rank 3; GrokBot's level chips) ----------------
// drawn from the row's own % levels (from its last close), labelled with the page's px(); the row's words stay under it

// ---- the card's time: the buy window and the plan's horizon on a calendar axis, today's tick, and the scheduled events
// that fall inside (market.calendar; earnings when int1 publishes the date). Labels are the published dates only --------
function timeline(s, cal) {
  const p = s.plan || {}, a = Date.parse(s.listed_at || s.as_of), e1 = t => Date.parse(t) + 864e5, w = e1(p.window), b = e1(p.by);   // a date's end
  if (!(a < w && b > 0)) return '';                // a date that does not parse is NaN, which isN() lets through
  const z = Math.max(w, b, s.earnings ? e1(s.earnings) || 0 : 0), X = t => M.num(Math.max(0, Math.min(100, (t - a) / (z - a) * 100)), 2) + '%', now = Date.now();
  const ev = (cal || []).filter(e => e && e.at && Date.parse(e.at) >= a && Date.parse(e.at) <= z).concat(s.earnings ? [{what: 'Earnings', at: s.earnings, e: 1}] : []);
  const lab = 'Listed ' + M.day(s.listed_at || s.as_of) + '; buy through ' + M.day(p.window) + (b > w ? '; typically by ' + M.day(p.by) : '') + (ev.length ? '; ' + ev.map(e => e.what + ' ' + M.day(e.at)).join(', ') : '');
  return '<div class="tl"><svg class="tls" width="100%" height="22" role="img" aria-label="' + esc(lab) + '"><rect class="ta" x="0" y="6" width="' + X(w) + '" height="8" rx="3"/>' +
    (b > w ? '<rect class="tb" x="' + X(w) + '" y="6" width="' + M.num(100 - parseFloat(X(w)), 2) + '%" height="8" rx="3"/>' : '') +
    (now > a && now < z ? '<line class="tn" x1="' + X(now) + '" x2="' + X(now) + '" y1="2" y2="18"/>' : '') +
    ev.map(e => '<circle class="' + (e.e ? 'te' : 'tc') + '" cx="' + X(Date.parse(e.at)) + '" cy="10" r="5"/>').join('') + '</svg>' +
    '<p class="tll"><span>Buy to ' + esc(M.day(p.window)) + '</span>' + (b > w ? '<span>typically by ' + esc(M.day(p.by)) + '</span>' : '') + '</p>' +
    (ev.length ? '<p class="tle">' + ev.map(e => '<span class="tag ' + (e.e ? 'fd on' : 'w') + '">' + esc(e.what + ' ' + M.day(e.at)) + '</span>').join('') + '</p>' : '') + '</div>';
}

// ---- the engine on the card (int1: engine {as_of, mom, risk, em, em_by}), its cautions, the desk's holding, and the
// evidence behind the conviction (the card's own `ranked` entry): GrokBot's ranker bars and status chips, small ------------
const bul = (v, cls, lab) => '<span class="eb ' + cls + '"><span class="ebl">' + lab + ' <b>' + M.num(v, 0) + '</b></span><span class="ebt"><i data-v="' + M.num(Math.max(0, Math.min(100, v)), 1) + '"></i></span></span>';
const eng = s => { const e = s.engine;           // a card's or a watching row's engine, linked to its row on the Engine tab
  return e && isN(e.mom) && isN(e.risk) ? '<a class="eng" href="#e=' + encodeURIComponent(s.symbol) + '" aria-label="' + esc(['Engine: momentum rank ' + M.num(e.mom, 0),
    'loser-risk rank ' + M.num(e.risk, 0) + ' (higher is riskier)', e.note, e.status].filter(Boolean).join(', ')) + '">' + bul(e.mom, 'mom', 'Momentum') + bul(e.risk, 'rsk', 'Loser risk') +
    (e.note ? '<span class="eas">' + esc(e.note) + '</span>' : '') + '</a>' : ''; };
function faceviz(c, d) {
  const s = c.s, row = c.bd.querySelector('.ex');
  if (row) row.remove();
  const chips = [eng(s)].filter(Boolean);
  if (s.held) chips.push('<span class="tag hd">Held</span>');
  (s.cautions || []).forEach(k => { if (k && k.text) chips.push('<span class="tag w ct" title="' + esc(k.credit || '') + '">⚠ ' + esc(k.text) + '</span>'); });
  const l = lx(s);
  if (l) chips.push(l);
  if (!chips.length) return;
  const tg = c.bd.querySelector('.tags'), h = '<div class="ex">' + chips.join('') + '</div>';
  if (tg) tg.insertAdjacentHTML('beforebegin', h); else c.bd.insertAdjacentHTML('beforeend', h);
  $$('.ebt i', c.bd).forEach(i => { i.style.width = i.dataset.v + '%'; });
}
function whyviz(c, d) {                           // the open card: what the evidence is made of, and the cautions in full
  const s = c.s, x = (d.ranked || []).find(r => r && r.symbol === s.symbol), g = c.db.querySelector('.evg');
  if (g) g.remove();
  const ps = x && (x.parts || []).filter(p => p && isN(p.value));
  let h = '';
  if (ps && ps.length) {
    const mx = Math.max(1, ...ps.map(p => Math.abs(p.value)));
    h += '<div class="evm" role="img" aria-label="' + esc('Evidence ' + M.num(x.evidence, 1) + ': ' + parts(x)) + '">' + ps.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).map(p =>
      '<div class="evr"><span>' + esc(p.label) + '</span><span class="evt"><i class="' + (p.value < 0 ? 'n' : 'p') + '" data-v="' + M.num(Math.abs(p.value) / mx * 50, 1) + '"></i></span><b class="' +
      (p.value < 0 ? 'dn' : 'up') + '">' + M.num(p.value, 1, 1) + '</b></div>').join('') + '<p class="evn">' + esc(['Evidence ' + M.num(x.evidence, 1), (s.conviction || {}).word].filter(Boolean).join(' · ')) + '</p></div>';
  }
  const ks = (s.cautions || []).filter(k => k && k.text);
  if (ks.length) h += '<ul class="fx cts">' + ks.map(k => '<li><b>⚠ ' + esc(k.text) + '</b>' + (k.credit ? '<span class="learn">' + esc(k.credit) + '</span>' : '') + '</li>').join('') + '</ul>';
  if (!h) return;
  const t = c.db.querySelector('.tlg'), x2 = '<div class="dg evg"><h4>Why this conviction</h4>' + h + '</div>';
  if (t) t.insertAdjacentHTML('afterend', x2); else c.db.insertAdjacentHTML('afterbegin', x2);
  $$('.evt i', c.db).forEach(i => { i.style.width = i.dataset.v + '%'; });
}

// ---- "Everything the desk considered" with Muse's lens-by-lens verdict badges, once int1 publishes each found line's
// side (sheet_side: 1 for, -1 against, 0 neutral); a line the read did not find reads "No read". Four badge words only ----
const VB = {'1': ['up', 'For'], '-1': ['dn', 'Against'], '0': ['mu', 'Neutral']};
function lens(c, d) {
  const s = c.s, sd = s.sheet_side, F = d.factors, box = c.db.querySelector('details.mo');
  if (!sd || !isA(F) || !s.sheet || !box || box.dataset.lens === c.sg) return;
  box.dataset.lens = c.sg;
  const n = {For: 0, Against: 0, Neutral: 0, 'No read': 0}, gs = [];
  F.forEach(l => {
    const got = s.sheet[l.id], v = got ? VB[String(sd[l.id])] || VB['0'] : ['nr', 'No read'];
    n[v[1]]++;
    let g = gs.find(x => x.name === l.group);
    if (!g) gs.push(g = {name: l.group, rows: []});
    g.rows.push('<li class="lr"><b>' + esc(l.label) + '</b><span class="bdg ' + v[0] + '">' + v[1] + '</span>' + (got ? '<span>' + esc(got) + '</span>' : '<span class="mu">' + esc(l.none) + '</span>') + '</li>');
  });
  box.innerHTML = '<summary><h4>Everything the desk considered (' + Object.keys(n).filter(k => n[k]).map(k => n[k] + ' ' + k.toLowerCase()).join(' · ') + ')</h4></summary>' +
    gs.map(g => '<h5 class="sg">' + esc(g.name) + '</h5><ul class="lens">' + g.rows.join('') + '</ul>').join('');
}

// ---- the eight lenses and Conviction 8 (ldr1, LDR-1): the stage a name reached, the ring of the eight lenses, how many are
// confirmed, its red flags and Conviction 8 with its check; in the open card, Conviction 8's categories after line 20 ----
const LN = ['Strength', 'Shape', 'Volume', 'Trend', 'Levels', 'Group', 'Supply', 'Market'];
const C8N = ['Relative strength', 'Price action', 'Participation', 'Trend alignment', 'Support and resistance', 'Sector leadership', 'Positioning', 'Market context'];
const arc = k => { const P = a => (8 * Math.sin(a * Math.PI / 180)).toFixed(2) + ' ' + (-8 * Math.cos(a * Math.PI / 180)).toFixed(2); return 'M' + P(k * 45 + 4) + 'A8 8 0 0 1 ' + P(k * 45 + 41); };   // ASCII minus: SVG path data
const SN = t => t === 'Conviction' ? 'Confirming' : t;   // the lens stage, never the card's conviction word
function lx(s) {
  const L = s.lens, K3 = x => x.filter(i => (L.c8st || '')[i] === 'C').length + '/3';
  if (!L || !L.states || L.states.length !== 8) return '';
  const st = L.states.split(''), r = L.red || [], by = k => LN.filter((_, i) => st[i] === k).join(', ');
  const lab = [SN(L.stage) + ': ' + L.word, 'Lenses: ' + L.n + ' of 8 confirmed' + (by('C') ? ' (' + by('C') + ')' : ''),
    r.length ? r.length + ' red flag' + (r.length > 1 ? 's' : '') + ': ' + r.join(', ') : '', by('I') ? 'No data: ' + by('I') : '',
    isN(L.c8) ? 'Conviction 8: ' + L.c8 + (L.ok ? ', qualifies' : '') : ''].filter(Boolean).join('. ');
  return '<span class="lx" role="img" aria-label="' + esc(lab) + '" title="' + esc(lab) + '"><span class="st ' + (TONE[L.tone] || 'mu') + '">' + esc(SN(L.stage)) + '</span><svg class="rg" viewBox="-10 -10 20 20" width="20" height="20">' +
    st.map((x, k) => '<path class="' + x + '" d="' + arc(k) + '"/>').join('') + '</svg><b>' + L.n + '/8</b>' + (r.length ? '<i class="rd">▲' + r.length + '</i>' : '') +
    (isN(L.c8) ? '<i>C8 ' + M.num(L.c8, 0) + (L.ok ? ' ✓' : '') + '</i><i>Strength ' + K3([0, 1, 2]) + '</i><i>Timing ' + K3([3, 4, 7]) + '</i>' : '') + '</span>';
}
function c8row(c, d) {
  const L = c.s.lens, box = c.db.querySelector('details.mo'), f = (d.factors || []).find(l => l.id === 'trend.stages');
  if (!box || !f) return;
  $$('.c8r', box).forEach(x => x.remove());
  const li = $$('li', box).find(x => x.querySelector('b') && x.querySelector('b').textContent.replace(/\.$/, '') === f.label);
  if (!li || !L || !L.cats || L.cats.length !== 8) return;
  const n = L.cats.filter(isN).length, k = (L.c8st || '').split('C').length - 1, w = L.ok ? ['up', 'For'] : n < 5 ? ['nr', 'No read'] : k <= 2 ? ['dn', 'Against'] : ['mu', 'Neutral'];
  const g = C8N.map((x, i) => '<span><span>' + x + '</span><span class="cb' + (isN(L.cats[i]) ? ((L.c8st || '')[i] === 'C' ? ' ok' : '') + '"><i data-v="' + L.cats[i] + '"></i></span><b>' + L.cats[i] : ' nd"></span><b class="mu">no data') + '</b></span>').join('');
  li.insertAdjacentHTML('afterend', '<li class="c8r' + (li.classList.contains('lr') ? ' lr' : '') + '"><b>Conviction 8' + (li.classList.contains('lr') ? '' : '.') + '</b><span class="bdg ' + w[0] + '">' + w[1] + '</span><span>' +
    (isN(L.c8) ? M.num(L.c8, 0) + ' · ' : '') + 'after Leadr’s 8-category design<span class="c8g" role="img" aria-label="' + esc('Conviction 8 by category: ' + C8N.map((x, i) => x + ' ' + (isN(L.cats[i]) ? L.cats[i] : 'no data')).join(', ')) + '">' + g + '</span></span></li>');
  $$('.c8g i', box).forEach(i => { i.style.width = i.dataset.v + '%'; });
}

// ---- after each edition app.js draws ---------------------------------------------------------------------------------------
function after(d) {
  const run = f => { try { f(); } catch (e) { console.error(e); } };   // app.js calls this inside its render: one broken picture
  run(() => glance(d));                                                 // stops neither the others nor the page
  run(() => clrank(d));
  run(() => lrank(d));
  run(() => recviz(d));
  Object.values(M.cards).forEach(c => { if (c.s) run(() => { faceviz(c, d); whyviz(c, d); lens(c, d); c8row(c, d); }); });
  run(() => times(d));
  run(jump);                                      // after the sections this edition shows or hides (Ranking, the record's)
  if (CH) run(draw); else charts().then(() => { if (CH) draw(); else $$('.pc').forEach(h => { h.hidden = true; }); });
  D.dispatchEvent(new CustomEvent('md:edition', {detail: d}));
}
window.MDV = {after, jump, charts, tab: () => tab, open: c => { if (CH) plans(c); }};  // jump(): rebuild the chips after a tab adds sections;
// charts(): the page's one charts.json fetch (a promise of the file, or of nothing), shared with the Market tab's index charts
route();
if (M.ed) after(M.ed);
})();
