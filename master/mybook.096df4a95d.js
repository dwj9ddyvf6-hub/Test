/* Master Desk terminal, the front page's My Book (deferred after viz.js): Claude's own book above the market tiles, drawn
   from the edition's book.live (desk/book/live.py) alone. State and NAV, each open position and waiting order on a price
   ladder (stop, entry, last, targets), the recent decisions with their one-line reasons, and under every item the full
   analysis the decision rested on (thesis, bull and bear, quant, forecast against its base rate, alternatives, countercase,
   pre-mortem, regime, sources, the trader's own technicals and chart reading). A flat book says what it waits for. Items
   the reader opened stay open when the next edition replaces the block. Pure string builders: window.MDBK. */
(() => {
const D = document, M = window.MD, el = id => D.getElementById(id);
if (!M || !el('mybook')) return;
const esc = M.esc, isN = v => typeof v === 'number' && isFinite(v);
const OPEN = new Set();
const KIND = {plan: ['Plan', 'pl'], enter: ['Entry', 'en'], trigger: ['Triggered', 'en'], target: ['Target', 'en'], exit: ['Exit', 'ex'],
  closed: ['Closed', 'ex'], done: ['Done', 'ex'], pass: ['Pass', 'ps'], hold: ['Hold', 'ps'], cancel: ['Cancel', 'cx'], expire: ['Expired', 'cx'],
  refused: ['Refused', 'rf'], trigger_refused: ['Refused', 'rf'], note: ['Note', 'nt']};
// refusal codes in plain English (desk/book/charter.py CODES and the inbox's own); an unknown code reads as words, never raw
const REASON = {OFF_SLOT: 'outside a decision slot', NO_INVALIDATION: 'no stop stated', BAD_INVALIDATION: 'stop on the wrong side of the price',
  RISK_TIER: 'risk size not allowed', NO_COMMITTEE: 'committee note missing', NO_THESIS: 'no thesis', INBOX_MALFORMED: 'decision file failed its checks',
  INBOX_LATE: 'arrived after its fill time', ZERO_SIZE: 'size rounds to zero', NAME_CAP: 'over the per-name cap', GROSS_CAP: 'over the gross exposure cap',
  HEAT_CAP: 'over the open-risk cap', DAILY_LOSS: 'daily loss limit reached', LADDER_STOP: 'drawdown stop: paused for review', AVERAGE_DOWN: 'adding to a loser',
  NAKED_OPTION: 'option risk not defined', BAD_LEGS: 'option legs malformed', NO_POSITION: 'nothing to exit', BOOK_CORRUPT: 'journal check failed',
  PENDING: 'an order on this name is already waiting', CARD_INCOMPLETE: 'decision card incomplete', BAD_FORECAST: 'forecast incomplete',
  STATE_CHECK: 'trader-state check failed', NO_RISK_SHEET: 'no risk sheet filed for the day', POD_UNKNOWN: 'pod not in the charter', POD_BENCHED: 'pod benched',
  SETUP_PROBE: 'setup not promoted: probe size only', PROBE_CAPACITY: 'two setups already in probe', COUNTERPARTY_UNKNOWN: 'counterparty unknown',
  SHORT_FIELDS: 'short card missing borrow facts', SLOT_BUDGET: 'quarter’s slot budget spent', STALE_MARKS: 'marks stale: no new risk',
  BOOK_DEFENSE: 'drawdown 15%: entries paused for review', PLAN_NOT_ACTIVE: 'plan no longer active', PLAN_INVALID: 'plan failed its checks', FORCED_STOP: 'forced stop', UNFILLED: 'not filled'};
const reason = c => REASON[c] || String(c || '').toLowerCase().replace(/_/g, ' ');
const kind = k => KIND[k] || [String(k || '').replace(/_/g, ' ').replace(/^./, c => c.toUpperCase()), 'nt'];
const num = (v, d = 2) => isN(v) ? v.toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d}) : '—';
const sg = (v, d) => isN(v) ? (+Math.abs(v).toFixed(d) === 0 ? '' : v > 0 ? '+' : '−') : '';
const usd = v => isN(v) ? (v < 0 ? '−' : '') + '$' + num(Math.abs(v)) : '—';
const sUsd = v => isN(v) ? sg(v, 2) + '$' + num(Math.abs(v)) : '—';
const pct = (v, d = 2) => isN(v) ? sg(v, d) + num(Math.abs(v), d) + '%' : '—';
const rr = v => isN(v) ? sg(v, 2) + num(Math.abs(v)) + 'R' : '—';
const tone = v => isN(v) && +Math.abs(v).toFixed(2) !== 0 ? (v > 0 ? 'u' : 'd') : '';
const parts = ts => isN(ts) ? M.et(ts) : null;
const hm = ts => { const p = parts(ts); return p ? p.hm : ''; };
const day = ts => { const p = parts(ts); return p ? p.key : ''; };
const when = ts => { const p = parts(ts); return !p ? '' : (p.key === M.et(Date.now()).key ? '' : p.weekday + ' ') + p.hm; };
const side = s => s ? '<span class="mb-sd ' + (s === 'short' ? 'dn' : 'up') + '">' + esc(s) + '</span>' : '';

// ---- the price ladder: stop, entry, last and targets on one axis, the risk and reward zones tinted; labels never overlap -----
function ladder(o, W) {
  const pts = [];
  if (isN(o.stop)) pts.push({v: o.stop, c: 'st', t: 'Stop'});
  if (isN(o.entry)) pts.push({v: o.entry, c: 'en', t: o.label || 'Entry'});
  (o.targets || []).forEach((t, i) => { if (isN(t.price)) pts.push({v: t.price, c: t.hit ? 'th' : 'tg', t: 'T' + (i + 1)}); });
  if (isN(o.last)) pts.push({v: o.last, c: 'lt', t: 'Last'});
  if (pts.length < 2) return '';
  W = Math.max(260, W || 340);
  const lo = Math.min(...pts.map(p => p.v)), hi = Math.max(...pts.map(p => p.v)), span = hi - lo || 1, pad = 44, Y = 40;
  const X = v => pad + (v - lo) / span * (W - 2 * pad);
  const rows = [{y: Y - 12, at: []}, {y: Y + 22, at: []}, {y: Y - 26, at: []}, {y: Y + 36, at: []}];   // label rows, nearest first
  let lab = '', mk = '';
  pts.slice().sort((a, b) => a.v - b.v).forEach(p => {
    const t = p.t + ' ' + num(p.v), w = t.length * 6.4 + 8, x = X(p.v), l = Math.max(w / 2, Math.min(W - w / 2, x));
    const r = rows.find(q => q.at.every(s => Math.abs(s.x - l) >= (s.w + w) / 2)) || rows[0];
    r.at.push({x: l, w});
    lab += '<text class="mb-lb ' + p.c + '" x="' + l.toFixed(1) + '" y="' + r.y + '" text-anchor="middle">' + esc(t) + '</text>';
    mk += p.c === 'lt' ? '<circle class="mb-dot lt" cx="' + x.toFixed(1) + '" cy="' + Y + '" r="5"/>' :
      '<rect class="mb-dot ' + p.c + '" x="' + (x - 3.5).toFixed(1) + '" y="' + (Y - 3.5) + '" width="7" height="7" rx="1.5" transform="rotate(45 ' + x.toFixed(1) + ' ' + Y + ')"/>';
  });
  let z = '';
  if (isN(o.stop) && isN(o.entry)) z += '<rect class="mb-zr" x="' + X(Math.min(o.stop, o.entry)).toFixed(1) + '" y="' + (Y - 5) + '" width="' + Math.abs(X(o.entry) - X(o.stop)).toFixed(1) + '" height="10" rx="2"/>';
  const far = (o.targets || []).filter(t => isN(t.price));
  if (isN(o.entry) && far.length) { const e = far.reduce((a, t) => Math.abs(t.price - o.entry) > Math.abs(a - o.entry) ? t.price : a, far[0].price);
    z += '<rect class="mb-zg" x="' + X(Math.min(o.entry, e)).toFixed(1) + '" y="' + (Y - 5) + '" width="' + Math.abs(X(e) - X(o.entry)).toFixed(1) + '" height="10" rx="2"/>'; }
  const name = pts.map(p => p.t + ' ' + num(p.v)).join(', ');
  return '<svg class="mb-lad" viewBox="0 0 ' + W + ' 84" width="100%" height="84" role="img" aria-label="' + esc(o.sym + ' price ladder: ' + name) + '">' +
    '<line class="mb-ax" x1="' + pad + '" x2="' + (W - pad) + '" y1="' + Y + '" y2="' + Y + '"/>' + z + mk + lab + '</svg>';
}

// ---- the forecast against its base rate -----------------------------------------------------------------------------------------
function meter(f) {
  if (!isN(f.p)) return '';
  const X = v => 6 + Math.max(0, Math.min(100, v)) / 100 * 228;
  return '<svg class="mb-fm" viewBox="0 0 240 30" width="240" height="30" role="img" aria-label="Forecast ' + f.p + ' percent' + (isN(f.base_rate) ? ', base rate ' + Math.round(f.base_rate * 100) + ' percent' : '') + '">' +
    '<rect class="mb-ft" x="6" y="9" width="228" height="8" rx="4"/><rect class="mb-fp" x="6" y="9" width="' + (X(f.p) - 6).toFixed(1) + '" height="8" rx="4"/>' +
    (isN(f.base_rate) ? '<line class="mb-fb" x1="' + X(f.base_rate * 100).toFixed(1) + '" x2="' + X(f.base_rate * 100).toFixed(1) + '" y1="4" y2="22"/><text class="mb-ftx" x="' + X(f.base_rate * 100).toFixed(1) + '" y="30" text-anchor="middle">base ' + Math.round(f.base_rate * 100) + '%</text>' : '') +
    '<text class="mb-ftx p" x="' + Math.min(X(f.p) + 4, 200).toFixed(1) + '" y="7">' + f.p + '%</text></svg>';
}

// ---- the full analysis behind an item -------------------------------------------------------------------------------------------
function analysis(c, plan, W, why) {
  if (!c) return '';
  const S = (t, v, cl) => v ? '<div class="mb-s ' + (cl || '') + '"><h4>' + t + '</h4><p>' + esc(v) + '</p></div>' : '';
  const L = (t, a, cl) => a && a.length ? '<div class="mb-s ' + (cl || '') + '"><h4>' + t + '</h4><ul>' + a.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul></div>' : '';
  const f = c.forecast || {}, g = c.game || {};
  const gk = [['counterparty', 'Against'], ['crowding', 'Crowding'], ['crowd_state', 'Crowd'], ['crowding_evidence', 'Evidence'], ['flow_read', 'Flow'], ['adverse_selection', 'Adverse selection'], ['focal_map', 'Focal levels']];
  const chart = plan && window.MDG ? '<div class="mb-s w mb-ch">' + window.MDG.planCard(plan, W) + '</div>' : '';
  const fc = (f.statement || isN(f.p) || f.reference_class) ? '<div class="mb-s w"><h4>Forecast</h4><div class="mb-fx">' + meter(f) + '<p>' + esc(f.statement || '') +
    (f.reference_class ? '<span class="mu"> Reference class: ' + esc(f.reference_class) + '.</span>' : '') + (f.resolve_by ? '<span class="mu"> Resolves ' + esc(M.day(f.resolve_by)) + '.</span>' : '') + '</p></div></div>' : '';
  const gm = gk.filter(([k]) => g[k]);
  const cp = c.computed || {}, tc = cp.tech || {}, sd = cp.side || {};
  const sg = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%';
  const tx = [isN(tc.atr) && 'ATR(14) ' + tc.atr + ' (' + tc.atr_pct + '%)', isN(tc.rsi) && 'RSI(14) ' + tc.rsi,
    isN(tc.vs21) && sg(tc.vs21) + ' vs 21-day', isN(tc.vs50) && sg(tc.vs50) + ' vs 50-day', isN(tc.vs200) && sg(tc.vs200) + ' vs 200-day',
    isN(tc.atr200) && tc.atr200 + ' ATR from the 200-day'].filter(Boolean);
  const sx = [isN(sd.rs20) && sg(sd.rs20) + ' vs SPY over 20 sessions', isN(sd.vol50) && 'volume ' + sd.vol50 + '× its 50-day',
    isN(sd.from_hi20) && sg(sd.from_hi20) + ' from the 20-session high', isN(sd.from_lo20) && sg(sd.from_lo20) + ' from the low'].filter(Boolean);
  const comp = (cp.regime || cp.vix || tx.length || sx.length || (cp.checks || []).length) ? '<div class="mb-s w mb-cp"><h4>From the data</h4>' +
    (cp.checks || []).map(x => '<p class="mb-ck">' + esc(x) + '</p>').join('') + (cp.regime ? '<p>Market: ' + esc(cp.regime) + '</p>' : '') + (cp.vix && isN(cp.vix.close) ? '<p>VIX ' + cp.vix.close + ' at the ' + esc(M.day(cp.vix.as_of)) + ' close (Cboe)</p>' : '') +
    (tx.length ? '<p>Bars: ' + esc(tx.join(' · ')) + '</p>' : '') + (sx.length ? '<p>This name: ' + esc(sx.join(' · ')) + '</p>' : '') + '</div>' : '';
  return '<div class="mb-body">' + chart + S(why || 'Thesis', c.thesis, 'w mb-th') + S('Bull', c.bull, 'bu') + S('Bear', c.bear, 'be') + S('Quant', c.quant) + S('Risk', c.risk) + fc +
    L('Alternatives weighed', c.alternatives) + S('Countercase', c.countercase) + S('Pre-mortem', c.premortem) + S('What decides it', c.decisive) + S('Regime', c.regime, 'w') + comp +
    (c.analysis ? '<div class="mb-s w"><h4>Technicals, chart reading and tools</h4><p class="mb-an">' + esc(c.analysis) + '</p></div>' : '') +
    (gm.length ? '<div class="mb-s w"><h4>The other side</h4><dl class="mb-g">' + gm.map(([k, t]) => '<dt>' + t + '</dt><dd>' + esc(g[k]) + '</dd>').join('') + '</dl></div>' : '') +
    L('Sources', c.sources, 'w mb-src') + ((c.setup || c.pod || c.grade) ? '<p class="mb-tags w">' + [c.setup && 'Setup ' + c.setup.replace(/_/g, ' '), c.pod && 'Pod ' + c.pod, c.grade && 'Grade ' + c.grade].filter(Boolean).map(esc).join(' · ') + '</p>' : '') + '</div>';
}

const item = (id, cls, sum, body) => '<details class="mb-it ' + cls + '" data-id="' + esc(id) + '"' + (OPEN.has(id) ? ' open' : '') + '><summary>' + sum + '</summary>' + body + '</details>';
const one = (c, at) => c && c.thesis ? '<span class="mb-th1">' + (at ? esc(at) + ': ' : '') + esc(c.thesis) + '</span>' : '';
// T-150: a thesis is the read at entry, dated, so "a risk-off tape" is never taken for today's market
const atEntry = p => isN(p.since) ? M.day(new Date(p.since * 1e3 - 5 * 3.6e6).toISOString().slice(0, 10)) : '';

function position(p, b, W) {
  const pl = (b.plans || []).find(x => x.symbol === p.symbol && x.status === 'triggered'), plan = pl && Object.assign({}, pl, {last: p.last});   // the chart's last is the book's own mark
  const sum = '<span class="mb-l1"><b class="mb-sym">' + esc(p.symbol) + '</b>' + side(p.side) + (p.kind !== 'stock' ? '<span class="mb-kd">' + esc(p.kind) + '</span>' : '') +
    '<span class="mb-big ' + tone(p.r) + '">' + rr(p.r) + '</span></span>' +
    '<span class="mb-l2"><span>' + num(p.qty, 0) + (p.kind === 'stock' ? ' sh' : '') + ' @ ' + num(p.entry) + '</span><span>last ' + num(p.last) + (p.last_at ? ' · ' + when(p.last_at) : '') + '</span>' +
    '<span class="' + tone(p.pnl) + '">' + sUsd(p.pnl) + ' · ' + pct(p.pnl_pct) + '</span>' + (isN(p.risk) ? '<span class="mu">risk ' + usd(p.risk) + '</span>' : '') + '</span>' +
    '<span class="mb-lw">' + ladder({sym: p.symbol, stop: p.stop, entry: p.entry, last: p.last, targets: p.targets, label: 'Entry'}, W) + '</span>' + one(p.card, atEntry(p) && 'At entry, ' + atEntry(p));
  return item(p.id, 'pos', sum, analysis(p.card, plan, W, atEntry(p) && 'Thesis at entry, ' + atEntry(p)));
}

const TYPE = {limit: 'Limit', cross_above: 'On a close above', cross_below: 'On a close below'};
function order(o, b, W) {
  const pl = o.kind === 'plan' ? (b.plans || []).find(x => x.symbol === o.symbol && x.level === o.level) : null, plan = pl && Object.assign({}, pl, isN(o.last) ? {last: o.last} : {});
  const d = o.dist_pct, away = isN(d) ? (Math.abs(d) < 0.05 ? 'at the trigger' : num(Math.abs(d)) + '% ' + (d < 0 ? 'below' : 'above') + ' last') : '';
  const sum = '<span class="mb-l1"><b class="mb-sym">' + esc(o.symbol) + '</b>' + side(o.side) + '<span class="mb-kd">' + esc(o.status === 'triggered' ? 'Triggered' : o.kind === 'order' ? 'Fills next bar' : (TYPE[o.entry_type] || 'Order') + ' ' + num(o.level)) + '</span>' +
    (away ? '<span class="mb-big mb-away">' + esc(away) + '</span>' : '') + '</span>' +
    '<span class="mb-l2">' + (isN(o.last) ? '<span>last ' + num(o.last) + (o.last_at ? ' · ' + when(o.last_at) : '') + '</span>' : '') + (o.expires ? '<span>expires ' + esc(M.day(o.expires)) + '</span>' : '') + (isN(o.qty) ? '<span>' + num(o.qty, 0) + ' sh</span>' : '') +
    (isN(o.risk_pct) ? '<span class="mu">risk ' + num(o.risk_pct) + '% of NAV</span>' : '') + '<span class="mu">filed ' + esc(when(o.filed)) + '</span></span>' +
    '<span class="mb-lw">' + ladder({sym: o.symbol, stop: o.stop, entry: o.level, last: o.last, targets: o.targets, label: o.entry_type === 'limit' ? 'Limit' : 'Trigger'}, W) + '</span>' + one(o.card);
  return item(o.id, 'ord', sum, analysis(o.card, plan, W));
}

// the text already says a reason when every word of it longer than two letters is in the text ("longer" aside, so the
// inbox's "no active plan" counts): one refusal is said once, never twice (MASTER-LIST T-181)
const said = (tx, w) => { const t = ' ' + String(tx || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ') + ' ';
  const ws = String(w || '').toLowerCase().split(/[^a-z0-9]+/).filter(x => x.length > 2 && x !== 'longer');
  return ws.length > 0 && ws.every(x => t.includes(' ' + x + ' ')); };
const sym = n => n && n !== 'book' ? n : '';   // desk/book/live.py names a book-level line "book": no ticker to show
function line(r) {
  const [k, c] = kind(r.kind);
  let tx = r.text || '';
  if (r.kind === 'closed') tx = [r.qty && num(r.qty, 0), r.side, isN(r.entry) && isN(r.exit) ? num(r.entry) + ' → ' + num(r.exit) : '', rr(r.r), sUsd(r.pnl)].filter(Boolean).join(' · ');
  else if ((r.kind === 'enter' || r.kind === 'exit') && r.status) tx = (r.status === 'filled' ? 'Filled' + (isN(r.price) ? ' at ' + num(r.price) : '') : r.status[0].toUpperCase() + r.status.slice(1)) + (tx ? ' · ' + tx : '');
  else if (r.kind === 'refused' && r.codes && r.codes.length) {   // a code's reason is added only when the text does not already say it (T-181)
    const add = r.codes.map(reason).filter(w => !said(tx, w));
    if (add.length) tx = (tx ? tx + ' · ' : '') + add.join(', ');
  }
  const lv = [isN(r.level) && 'at ' + num(r.level), isN(r.stop) && 'stop ' + num(r.stop), (r.tp || []).length && 'to ' + r.tp.map(v => num(v)).join(', ')].filter(Boolean).join(' · ');
  return '<span class="mb-t">' + esc(hm(r.at)) + '</span><span class="mb-k ' + c + '">' + esc(k) + '</span><b class="mb-sym">' + esc(sym(r.name)) + '</b>' + (r.kind === 'closed' ? side(r.side) : '') + '<span class="mb-x">' + esc(tx) + '</span>' + (lv ? '<span class="mb-lv">' + esc(lv) + '</span>' : '');
}

const SHOWN = 5;           // decisions in the block itself; the rest sit under one "earlier" line so the market tiles stay in reach
function feed(rows, b, W) {
  const ok = rows.filter(r => r.kind !== 'refused'), bad = rows.filter(r => r.kind === 'refused');
  // one day header per day across the shown rows and the "earlier" list, and the earlier list in time order with its
  // refusals in place (audit 2026-11-04 HM-11: a second "Today" opened the list and 16:00 refusals sat under 12:58)
  let last = '';
  const list = a => { let out = '';
    a.forEach(r => {
      const dk = day(r.at);
      if (dk !== last) { out += '<li class="mb-day">' + esc(dk === M.et(Date.now()).key ? 'Today' : parts(r.at).weekday + ', ' + parts(r.at).md) + '</li>'; last = dk; }
      out += '<li>' + (r.kind === 'refused' ? '<div class="mb-it fd flat mb-bad"><div class="mb-sm">' + line(r) + '</div></div>' :
        r.card ? item('f' + r.at + r.kind + r.name, 'fd', line(r), analysis(r.card, null, W, r.kind === 'plan' ? 'Thesis' : 'Why')) : '<div class="mb-it fd flat"><div class="mb-sm">' + line(r) + '</div></div>') + '</li>';
    });
    return out; };
  // "earlier" holds only what is older than the last row shown: a refusal newer than it stands in place among the shown
  // rows (T-154, live 11-05: 16:00 refusals sat under "earlier", below the 12:58 COST cancel shown above it)
  const by = (x, y) => y.at - x.at, top = ok.slice().sort(by).slice(0, SHOWN), cut = top.length ? top[top.length - 1].at : Infinity;
  const head_ = top.concat(bad.filter(r => r.at >= cut)).sort(by), more = ok.slice().sort(by).slice(SHOWN).concat(bad.filter(r => r.at < cut)).sort(by), n = more.length, nb = more.filter(r => r.kind === 'refused').length;
  const shown = list(head_);
  const rest = n ? '<li><details class="mb-ref" data-id="earlier"' + (OPEN.has('earlier') ? ' open' : '') + '><summary>' + n + ' earlier' + (nb ? ' (' + nb + ' refused)' : '') + '</summary><ul class="mb-feed">' + list(more) + '</ul></details></li>' : '';
  const out = shown + rest;
  return out ? '<ul class="mb-feed">' + out + '</ul>' : '';
}

// ---- a flat book: the day's decision slots, what has happened in them and what is next --------------------------------------
function slots(w, rows, W) {
  const S = (w.slots || []).map(s => { const [h, m] = s.split(':'); return {s, m: +h * 60 + +m}; });
  if (!S.length) return '';
  W = Math.max(260, W || 340);
  const a = S[0].m - 40, z = S[S.length - 1].m + 40, X = m => 18 + (m - a) / (z - a) * (W - 36), n = parts(Date.now()), nm = n ? +n.hm.slice(0, 2) * 60 + +n.hm.slice(3) : 0, today = n && n.key;
  const done = S.filter(s => s.m + (w.slot_min || 20) <= nm).length, nxt = S.find(s => s.m > nm);
  let g = '<line class="mb-ax" x1="18" x2="' + (W - 18) + '" y1="28" y2="28"/><line class="mb-ax on" x1="18" x2="' + X(Math.max(a, Math.min(z, nm))).toFixed(1) + '" y1="28" y2="28"/>';
  S.forEach(s => { const c = s.m + (w.slot_min || 20) <= nm ? 'dn' : nxt && s.m === nxt.m ? 'nx' : ''; g += '<circle class="mb-sl ' + c + '" cx="' + X(s.m).toFixed(1) + '" cy="28" r="6"/><text class="mb-lb" x="' + X(s.m).toFixed(1) + '" y="54" text-anchor="middle">' + s.s + '</text>'; });
  rows.filter(r => day(r.at) === today && r.kind !== 'refused').forEach(r => { const p = parts(r.at), m = +p.hm.slice(0, 2) * 60 + +p.hm.slice(3);
    if (m >= a && m <= z) g += '<rect class="mb-ev ' + kind(r.kind)[1] + '" x="' + (X(m) - 4).toFixed(1) + '" y="8" width="8" height="8" rx="1.5" transform="rotate(45 ' + X(m).toFixed(1) + ' 12)"><title>' + esc((kind(r.kind)[0] + ' ' + sym(r.name)).trim()) + '</title></rect>'; });
  return '<svg class="mb-slots" viewBox="0 0 ' + W + ' 62" width="100%" height="62" role="img" aria-label="Decision slots today: ' + done + ' of ' + S.length + ' passed' + (nxt ? ', next ' + nxt.s + ' ET' : '') + '">' + g + '</svg>';
}

// the next slot worded against the reader's clock from its moment (round 4 #3), the edition's words only without one
const slotWord = w => isN(w.next_slot_at) && M.dayWord ? M.dayWord(w.next_slot_at * 1e3, Date.now()) + ' ' + M.et(w.next_slot_at * 1e3).hm : w.next_slot;
let cur = null;            // the edition being drawn: M.ed still holds the previous one while md:edition is dispatched
function render(d) {
  if (d) cur = d;
  const sec = el('mybook'), b = cur && cur.book, L = b && b.live;
  if (!L) { if (sec._h) { sec._h = ''; sec.innerHTML = ''; } sec.hidden = true; return; }
  const W = Math.max(280, Math.min(720, Math.round((sec.clientWidth || el('main').clientWidth || 360) - 60)));
  const pos = L.positions || [], ord = L.orders || [], fd = L.feed || [], w = L.waiting || {};
  const stale = Date.now() / 1e3 - L.built > 2700, st = {open: 'Open', working: 'Working', flat: 'Flat'}[L.state] || 'Flat';
  const tile = (k, v, c) => '<div class="mb-tile"><span>' + k + '</span><b class="' + (c || '') + '">' + v + '</b></div>';
  const risk = pos.reduce((s, p) => s + (isN(p.risk) ? p.risk : 0), 0);
  let h = '<div class="shd"><div class="sht"><p class="kick">Claude’s own book</p><h2 id="h-mybook">My Book <span class="mb-st ' + esc(L.state) + '">' + st + '</span></h2></div>' +
    // one stamp: the panel's chip states the book's time; this line speaks only when the block itself is stale
    // (audit 2026-11-04 HM-12: "As of 17:53 ET" beside "Market closed · Wed 17:47 ET", neither labelled)
    (stale ? '<span class="pv mb-asof stale">Stale · built ' + esc(when(L.built)) + ' ET</span>' : '') + '</div>' +
    '<div class="card mb-card"><div class="mb-tiles">' + tile('NAV', usd(L.nav)) + tile('Day', sUsd(L.day_pnl) + ' <small>' + pct(L.day_pct) + '</small>', tone(L.day_pnl)) +
    tile('Cash', usd(L.cash)) + tile(pos.length ? 'At risk' : 'Orders', pos.length ? usd(risk) : String(ord.length)) + '</div>';
  if (pos.length) h += '<h3 class="mb-h">Positions</h3><div class="mb-list">' + pos.map(p => position(p, b, W)).join('') + '</div>';
  if (ord.length) h += '<h3 class="mb-h">Waiting orders</h3><div class="mb-list">' + ord.map(o => order(o, b, W)).join('') + '</div>';
  if (!pos.length && !ord.length) {
    const dec = w.decisive ? '<p class="mb-wait"><b>Waiting for</b> ' + (w.decisive_name ? esc(w.decisive_name) + ': ' : '') + esc(w.decisive) + (w.decisive_at ? ' <span class="mu">' + esc(when(w.decisive_at)) + '</span>' : '') + '</p>' : '';
    h += '<div class="mb-flat"><p class="mb-empty"><b>Flat.</b> No open positions and no waiting orders' + (fd.length ? '' : '; no decision on file yet') + '.</p>' + dec +
      slots(w, fd, W) + '<p class="mb-meta">' + [w.next_slot && 'Next decision slot ' + esc(slotWord(w)) + ' ET', w.sheet === true && 'risk sheet filed', w.sheet === false && 'risk sheet not filed yet', w.watching ? 'watching ' + w.watching + ' names' : ''].filter(Boolean).join(' · ') + '</p></div>';
  } else if (w.next_slot) h += '<p class="mb-meta">Next decision slot ' + esc(slotWord(w)) + ' ET</p>';
  const fh = feed(fd, b, W);
  if (fh) h += '<h3 class="mb-h">Decisions</h3>' + fh;
  h += '</div>';
  if (sec._h !== h) { sec.innerHTML = h; sec._h = h; }
  sec.hidden = false;
}
el('mybook').addEventListener('toggle', e => { const id = e.target.dataset && e.target.dataset.id; if (id) e.target.open ? OPEN.add(id) : OPEN.delete(id); }, true);
let rq = 0;
const PG = (t, f) => (window.MD && window.MD.guard ? window.MD.guard(t, f) : f());   // app.js's panel guard
const again = () => { if (!rq) rq = setTimeout(() => { rq = 0; PG('mybook', () => render()); }, 160); };
addEventListener('resize', again);
D.addEventListener('md:edition', e => { cur = e.detail || cur; PG('mybook', () => render()); });
window.MDBK = {reason, REASON, ladder, meter, analysis, slots, kind, render, line, said, feed};
if (M.ed) { cur = M.ed; PG('mybook', () => render()); }
})();
