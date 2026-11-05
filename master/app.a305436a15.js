/* Master Desk terminal. Card faces give the plan in dollars; the open card keeps the technical read. */
(() => {
const SCHEMA = 'master-desk-terminal/2', TZ = 'America/New_York', POLL = 6e4, BASE = 1e4, CAP = 3e5, LATE = 12e5, RATED = 30;
const D = document, fq = new URLSearchParams(location.search).get('f');
const DIR = ['empty', 'first', 'closed', 'full'].includes(fq) ? 'fixtures/' : '', SRC = DIR ? DIR + 'edition.' + fq + '.json' : 'edition.json';
const el = id => D.getElementById(id), ET = ' ET', AH = ' aria-hidden="true"', isA = Array.isArray, box = n => n.getBoundingClientRect();

// 'x?' optional, 'a|b' enum, [type, item] array, {_:1} optional object
const STR = ['a', 's'], FACT = ['a', {head: 's', text: 's', learn: 's?'}];
const READ = {symbol: 's', as_of: 's', action: 's', form: 'now|pullback|breakout|turn|wait', conviction: {level: 'n', word: 's'},
  gut: {word: 'Strong|For|Leaning|Against', why: STR}, plan: {zone_lo: 'n?', zone_hi: 'n?', trigger: 'n?', out: 'n?', t1: 'n?', t2: 'n?',
    r: 'n?', by: 's?', window: 's?', sessions: 'n?', sentence: 's', why_zone: 's?', why_out: 's?', why_t1: 's?', breakeven: 'n?',
    mode: 's?', trim: 'n?', r2: 'n?', why_t2: 's?', time_stop: 'n?'},
  gist: 's', standouts: FACT, against: FACT, take: 's', change: 's', considered: STR,
  material: ['a?', {head: 's', text: 's', learn: 's?'}], sheet: 'o?', news: ['a?', {headline: 's', source: 's', at: 'd', url: 's?'}],
  fear: {_: 1, state: 's', label: 's', text: 's'}};
const SPEC = {
  seq: 'n', edition: 'd', generated_at: 'd', next_at: 'd', cadence_min: 'n?', session: {state: 's', label: 's'},
  market: {as_of: 's?', live_at: 'n?', as_of_at: 'n?', sentence: 's', chips: ['a?', {label: 's', value: 's', tone: 's?', detail: 's?', bar: 'n?'}],
    sectors: ['a?', {name: 's', rs: 'n', pts: 'n?'}], calendar: ['a?', {what: 's', at: 'd'}]},
  setups: ['a?', Object.assign({id: 's', listed_at: 'd?', new: 'b?', status: 's?', now_pct: 'n?', flags: STR, close: 'n?'}, READ)],
  watching: ['a?', {symbol: 's', action: 's', conviction: 's', gut: 's', line: 's', by: 's', close: 'n?', trigger: 'n?', zone_hi: 'n?', t1: 'n?', out: 'n?', spike: 'n?', zone_lo: 'n?', mode: 's?', now_pct: 'n?'}], lookup: {_: 1, as_of: 's?', count: 'n'},
  departures: ['a?', {symbol: 's', reason: 's', at: 'd?'}],
  scorecard: {since: 's?', calls: 'n', filled: 'n?', closed: 'n', hits: 'n?', hit_rate: 'n?', mean_r: 'n?', open: 'n?',
    waiting: 'n?', by_conviction: 'o?', by_take: 'o?', note: 's?'},
  calls: ['a', {id: 's', symbol: 's', opened: 'd', status: 's', exit: 's?', outcome_pct: 'n?', outcome_r: 'n?'}],
  notes: STR, fear: {_: 1, both: 'b', text: 's'},
  factors: ['a?', {n: 'n', id: 's', group: 's', label: 's', none: 's', mark: 's?'}]
};
function chk(v, s, p) {
  let e;
  if (isA(s)) {
    if (v == null) return s[0] === 'a?' ? '' : p;
    if (!isA(v)) return p;
    for (let i = 0; i < v.length; i++) if ((e = chk(v[i], s[1], p + '.' + i))) return e;
    return '';
  }
  if (typeof s === 'object') {
    if (v == null && s._) return '';
    if (!v || typeof v !== 'object' || isA(v)) return p;
    for (const k in s) if (k !== '_' && (e = chk(v[k], s[k], p + '.' + k))) return e;
    return '';
  }
  const o = s.endsWith('?'), t = o ? s.slice(0, -1) : s;
  if (v == null) return o ? '' : p;
  return (t === 's' ? typeof v === 'string' : t === 'n' ? typeof v === 'number' && isFinite(v) : t === 'b' ? typeof v === 'boolean' :
    t === 'o' ? typeof v === 'object' && !isA(v) : t === 'd' ? typeof v === 'string' && !isNaN(Date.parse(v)) :
    t.split('|').includes(v)) ? '' : p;
}
const CUR = new RegExp('[' + String.fromCharCode(36, 162, 163, 165, 8364) + ']'); // no prices, ever
const invalid = d => !d || typeof d !== 'object' ? 'type' : d.schema !== SCHEMA ? 'schema' :
  chk(d, SPEC, 'edition') || (CUR.test(JSON.stringify(d)) ? 'currency sign' : '');

const dtf = new Intl.DateTimeFormat('en-US', {timeZone: TZ, year: 'numeric', month: 'short', day: 'numeric', weekday: 'short',
  hour: '2-digit', minute: '2-digit', hourCycle: 'h23'});
const rtf = new Intl.RelativeTimeFormat('en', {style: 'short'}), nfs = {};
function et(v) {   // pure and called for every stamp on the page: formatToParts once per distinct value (et.c, bounded)
  if (typeof v === 'number' && v > 0 && v < 1e11) v *= 1e3;   // epoch seconds (the record's `ts`), never 1970
  const C = et.c || (et.c = new Map()), k = typeof v + ':' + v, hit = C.get(k);
  if (hit) return Object.assign({}, hit);
  const o = {};
  dtf.formatToParts(typeof v === 'string' && v.length === 10 ? new Date(v + 'T12:00:00Z') : new Date(v)).forEach(x => { o[x.type] = x.value; });
  o.hm = o.hour + ':' + o.minute;
  o.md = o.month + ' ' + o.day;
  o.key = o.year + o.md;
  if (C.size > 4000) C.clear();
  C.set(k, o);
  return Object.assign({}, o);
}
const wd = v => { const p = et(v); return (Math.abs(Date.now() - Date.parse(v)) < 5184e5 ? p.weekday + ' ' : p.md + ', ') + p.hm; };
const when = v => et(v).key === et(Date.now()).key ? et(v).hm : wd(v);
const day = v => { const p = et(v); return p.weekday + ', ' + p.md; };
const h12 = p => (p.hour % 12 || 12) + ':' + p.minute + (p.hour < 12 ? ' am' : ' pm');
function ago(t) {
  const s = (Date.now() - t) / 1e3, u = s < 3600 ? ['minute', 60] : s < 864e2 ? ['hour', 3600] : ['day', 864e2];
  return s < 60 ? 'just now' : rtf.format(-Math.floor(s / u[1]), u[0]).replace(/\./g, '');
}
function num(v, dp, sign) {
  const k = dp + '' + !!sign, f = nfs[k] || (nfs[k] = new Intl.NumberFormat('en-US',
    {minimumFractionDigits: dp, maximumFractionDigits: dp, signDisplay: sign ? 'exceptZero' : 'auto'}));
  return f.format(v).replace('-', '−');
}
const pct = (v, dp = 2) => num(v, dp, 1) + '%';
const pl = v => Math.abs(v) >= 10 ? pct(v, 0) : pct(v, 1).replace('.0%', '%');
const isN = v => typeof v === 'number';
const n0 = v => isN(v) ? num(v, 0) : '—';
const plural = (n, w) => n0(n) + ' ' + w + (n === 1 ? '' : 's');
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => '&#' + c.charCodeAt(0) + ';').replace(/ · /g, ' · ');
const bold = s => esc(s).replace(/[+−]?\d+(\.\d+)?%(?! retracement)/g, m => '<b>' + m + '</b>');
const html = (e, h) => { if (e._h !== h) { e.innerHTML = h; e._h = h; } };
const text = (e, t) => { if (e.textContent !== t) e.textContent = t; };

let ed = null, latest = null, fac = null;
let fails = 0, failing = false, busy = false, last = 0, due = 0, timer = 0, paused = false;
const cards = {}, live = el('live'), TONE = {up: '↑', down: '↓'};
let said = [];
const say = t => {
  if (!said.length) { live.textContent = ''; setTimeout(() => { live.textContent = said.join(' '); said = []; }, 50); }
  said.push(t);
};
const hb = () => box(el('mast')).bottom;

function keep(fn, ok) {
  const top = hb();
  let a = null, y = 1e9, r;
  if (scrollY > 0) D.querySelectorAll('[data-anchor]').forEach(n => {
    const id = n.getAttribute('data-id'), b = box(n);
    if (b.height && b.top >= top && b.top < y && (!id || ok[id])) { a = n; y = b.top; }
  });
  fn();
  if (a && a.isConnected && Math.abs(r = box(a).top - y) > 0.5) scrollBy(0, r);
}

function chip(c) {
  const t = TONE[c.tone], b = isN(c.bar) ? Math.max(0, Math.min(1, c.bar)) : -1;
  return '<div class="chip"><div class="cl">' + esc(c.label) + '</div><div class="cv">' + esc(c.value) +
    (t ? ' <span class="tn">' + t + '</span>' : '') + '</div><div class="cb' + (b < 0 ? ' no">' : '"><i data-w="' +
    (b * 100).toFixed(1) + '"></i>') + '</div>' + (c.detail ? '<div class="cd">' + esc(c.detail) + '</div>' : '') + '</div>';
}
function calLine(a) {
  const up = (a || []).filter(x => Date.parse(x.at) > Date.now()).sort((x, y) => Date.parse(x.at) - Date.parse(y.at));
  return up.length ? 'Scheduled: ' + up.map((x, i) => {
    const p = et(x.at);
    return x.what + ' ' + (i ? p.md : p.weekday + ' ' + p.md + ', ' + h12(p) + ET);
  }).join(' · ') : '';
}
const widths = () => D.querySelectorAll('[data-w]').forEach(e => { e.style.width = e.dataset.w + '%'; }); // CSSOM: the CSP bars style attributes
// Live only while the session is open on today's data (desk/terminal/market.py settle_live); else an as-of time
function asofLabel(m) {
  const t = v => new Date(v * 1e3).toLocaleTimeString('en-US', {timeStyle: 'short', timeZone: 'America/New_York'});
  return m.live_at ? 'Live ' + t(m.live_at) : m.as_of_at ? 'As of ' + t(m.as_of_at) + ' ' +
    new Date(m.as_of_at * 1e3).toLocaleDateString('en-US', {weekday: 'short', timeZone: 'America/New_York'}) : m.as_of ? 'As of ' + day(m.as_of) : '';
}
function market(d) {
  const m = d.market, ch = (m.chips || []).slice(0, 4), cal = calLine(m.calendar), s = (m.sectors || []).slice().sort((x, y) => y.rs - x.rs);
  el('market').hidden = false;
  text(el('asof'), asofLabel(m));
  text(el('sent'), m.sentence);
  el('sent').hidden = !m.sentence;
  html(el('chips'), ch.map(chip).join(''));
  el('chips').hidden = !ch.length;
  text(el('cal'), cal);
  el('cal').hidden = !cal;
  el('sectors').hidden = !s.length;
  el('sec-meta').hidden = !s.some(x => isN(x.pts));
  html(el('secl'), s.map(x => {
    const r = Math.max(-1, Math.min(1, x.rs));
    return '<li><span class="sn">' + esc(x.name) + '</span><span class="sb"><i class="' + (r < 0 ? 'n' : 'p') + '" data-w="' +
      (Math.abs(r) * 50).toFixed(1) + '"></i></span><span class="sv">' + (isN(x.pts) ? num(x.pts, 1, 1) + ' pts' : '') +
      '</span></li>';
  }).join(''));
  widths();
}

// the plan ladder: drawn from the plan's own numbers (% from the last close), so the picture and the words agree
function ladder(p, now) {
  const L = (v, r) => isN(p.close) ? px(p.close, v, r) : pl(v);
  const ps = [p.out, p.zone_lo, p.zone_hi, p.t1, isN(now) ? now : 0].concat(p.trim && isN(p.t2) ? [p.t2] : []);
  const lo = Math.min(...ps), hi = Math.max(...ps), sp = hi - lo || 1, X = v => 3 + 94 * (v - lo) / sp, f = v => X(v).toFixed(2) + '%';
  const nx = isN(now) ? now : 0, zl = X(p.zone_lo), zw = Math.max(1.2, X(p.zone_hi) - zl), inz = nx >= p.zone_lo && nx <= p.zone_hi;
  const at = (x, t, y, c) => '<text x="' + x.toFixed(2) + '%" y="' + y + '" class="' + c + '" text-anchor="' + (x < 12 ? 'start' : x > 88 ? 'end' : 'middle') +
    '">' + t + '</text>', zc = zl + zw / 2, ztxt = p.trigger != null ? 'buy above' : p.zone_lo > 0 || p.zone_hi < 0 ? 'buy zone' : 'buy here';
  const sp_ = (x, t) => { const w = t.length * 2.2 + 2; return x < 12 ? [x, x + w] : x > 88 ? [x - w, x] : [x - w / 2, x + w / 2]; },
    clash = (a, b) => a[0] < b[1] && b[0] < a[1];
  let s = '<svg class="lad" width="100%" height="64" role="img" aria-label="Plan: out at ' + pl(p.out) + ', buy ' + pl(p.zone_lo) + ' to ' +
    pl(p.zone_hi) + ', target ' + pl(p.t1) + '"><line class="ax" x1="' + f(lo) + '" x2="' + f(hi) + '" y1="30" y2="30"/>' +
    '<line class="rk" x1="' + f(p.out) + '" x2="' + zl.toFixed(2) + '%" y1="30" y2="30"/><line class="rw" x1="' + (zl + zw).toFixed(2) +
    '%" x2="' + f(p.t1) + '" y1="30" y2="30"/><rect class="zn" x="' + zl.toFixed(2) + '%" y="22" width="' + zw.toFixed(2) + '%" height="16" rx="3"/>' +
    '<line class="ot" x1="' + f(p.out) + '" x2="' + f(p.out) + '" y1="21" y2="39"/><line class="tt" x1="' + f(p.t1) + '" x2="' + f(p.t1) + '" y1="21" y2="39"/>';
  if (p.trim && isN(p.t2)) s += '<line class="tt t2" x1="' + f(p.t2) + '" x2="' + f(p.t2) + '" y1="24" y2="36"/>';
  s += '<circle class="nw" cx="' + f(nx) + '" cy="30" r="4.5"/>' + at(zc, ztxt, 13, 'lz');
  const nw = sp_(X(nx), 'now'); // "now" over the line, else under it, else the dot alone
  if (!inz && !clash(nw, sp_(zc, ztxt))) s += at(X(nx), 'now', 13, 'lt');
  else if (!inz && !clash(nw, sp_(X(p.out), L(p.out, 1) + ' out')) && !clash(nw, sp_(X(p.t1), L(p.t1, -1) + ' target'))) s += at(X(nx), 'now', 58, 'lt');
  s += at(X(p.out), L(p.out, 1) + ' out', 58, 'lo') + at(X(p.t1), L(p.t1, -1) + (p.trim ? ' trim' : ' target'), 58, 'lw');
  if (p.trim && isN(p.t2) && X(p.t2) - X(p.t1) > 8 && X(p.t2) - Math.max(zc, X(nx)) > 22) s += at(X(p.t2), 'target ' + L(p.t2, -1), 13, 'lw');
  return s + '</svg>';
}
// a plan's % level in dollars from its close, on the order tick, rounded safe by role r (desk/terminal/prices.py)
const USD = '$';
const px = (c, v, r) => { const x = c * (1 + v / 100), k = x >= 1000 ? 1 : x < 1 ? 1e4 : 100, y = x * k,
  n = (r < 0 ? Math.floor(y + 1e-7) : r > 0 ? Math.ceil(y - 1e-7) : Math.round(y)) / k;
  return USD + (n >= 1000 ? n.toLocaleString('en-US') : n.toFixed(n < 1 ? 4 : 2)); };
// now: the last price in % from that close, for a buy still waiting; over the buy range the face waits, as the record
// fills only at the range's top or under it (desk/terminal/calls.py)
function order(p, c, trig, now) {
  if (!isN(c) || !isN(p.out) || !isN(p.t1)) return null;
  const lo = px(c, p.zone_lo, -1), hi = px(c, p.zone_hi, -1);
  const t = trig != null ? 'Buy if it closes above ' + px(c, trig, 1) + ' (no higher than ' + hi + ').'
    : isN(now) && now > p.zone_hi ? 'Above the buy range — wait for a pullback to ' + lo + '–' + hi + '.'
    : (p.mode === 'reaction' ? 'Buy on an up day between ' : 'Buy between ') + lo + ' and ' + hi + '.';
  const tp = p.trim && isN(p.t2) ? 'Sell some at ' + px(c, p.t1, -1) + ', the rest at ' + px(c, p.t2, -1) + '.' : 'Sell at ' + px(c, p.t1, -1) + ' to take profit.';
  return t + ' ' + tp + ' Sell if it closes below ' + px(c, p.out, 1) + '.';
}
const dots = n => '<span class="dots"' + AH + '>' + [1, 2, 3].map(i => '<i' + (i <= n ? ' class="on"' : '') + '></i>').join('') + '</span>';
const STATUS = {open: 'Bought', closed: 'Closed', expired: 'Expired', missed: 'Missed', void: 'Void'};
function status(s) {
  const p = s.plan, a = s.status === 'waiting' ? (p.trigger != null ? 'Waiting for a daily close above ' + pl(p.trigger) :
    (p.mode === 'reaction' ? 'Waiting for a daily close up in the zone, through ' : 'Buy open through ') + day(p.window)) : STATUS[s.status] || '';
  return [a, isN(s.now_pct) && Math.abs(s.now_pct) >= 0.05 ? 'now ' + pl(s.now_pct) + ' from the ' + et(s.as_of).md + ' close' : '']
    .filter(Boolean).join(' · ');
}
// the order as cells (buy, stop, target): dollars, and the plan's own % from the close; the sentence labels them
function cells(p, ord) {
  const L = (v, r) => px(p.close, v, r), tr = p.trigger != null, two = p.trim && isN(p.t2), wait = /^Above/.test(ord);
  return '<div class="lv" role="group" aria-label="' + esc(ord) + '"><div><i>' + (tr ? 'Buy above' : 'Buy') + '</i><b>' +
    (tr ? L(p.trigger, 1) : L(p.zone_lo, -1) + '–' + L(p.zone_hi, -1).slice(1)) + '</b><small>' + (wait ? 'wait for a pullback' : tr ? 'up to ' +
    L(p.zone_hi, -1) : pl(p.zone_lo) + ' to ' + pl(p.zone_hi)) + '</small></div><div class="s"><i>Stop</i><b>' + L(p.out, 1) + '</b><small>' +
    (tr ? pl(((100 + p.out) / (100 + p.trigger) - 1) * 100) + ' from the buy' : pl(p.out)) + '</small></div><div class="t"><i>Target' + (two ? 's' : '') + '</i><b>' + L(p.t1, -1) + '</b><small>' + pl(p.t1) + (two ? ' · ' + pl(p.t2) : '') +
    '</small></div></div>';
}
function face(s, listed) {
  const p = Object.assign({}, s.plan, {close: s.close}), tags = [];
  if (listed && s.new) tags.push('<span class="tag nw">New</span>');
  // face tags: only what changes what to do now (conviction is already shown; a waiting fear day is not news)
  (s.flags || []).forEach(f => tags.push('<span class="tag w">' + esc(f) + '</span>'));
  if (s.fear && s.fear.state === 'came') tags.push('<span class="tag fd on">' + esc(s.fear.label) + '</span>');
  const st = [isN(s.close) ? 'Last close ' + px(s.close, 0) + ' · ' + et(s.as_of).md : '', listed && status(s)].filter(Boolean).join(' · ');
  const ord = order(p, s.close, p.trigger, !listed ? 0 : s.status === 'waiting' ? s.now_pct : null);
  return (isN(p.out) ? '<div class="mc" data-s="' + esc(s.symbol) + '">' + ladder(p, listed ? s.now_pct : 0) + '</div>' : '') +
    (ord ? cells(p, ord) : '<p class="pln">' + bold(p.sentence) + '</p>') + '<p class="gist">' + esc(s.gist) + '</p>' +
    (st ? '<p class="mu stl">' + esc(st) + '</p>' : '') + '<p class="tags">' + tags.join('') + '</p>';
}
const grp = (h, inner) => inner ? '<div class="dg"><h4>' + h + '</h4>' + inner + '</div>' : '';
const facts = a => a.length ? '<ul class="fx">' + a.map(f => '<li><b>' + esc(f.head) + '.</b> ' + esc(f.text) +
  (f.learn ? '<span class="learn">' + esc(f.learn) + '</span>' : '') + '</li>').join('') + '</ul>' : '';
function read(s) {
  const p = s.plan, rows = [], P = (v, r) => isN(s.close) && isN(v) ? px(s.close, v, r) + ' (' + pl(v) + ')' : pl(v); // a read that stands aside has no plan to lay out
  if (isN(p.out)) rows.push(['Buy', p.trigger != null ? 'on a daily close above ' + P(p.trigger, 1) + ', up to ' + P(p.zone_hi, -1) :
    (p.mode === 'reaction' ? 'on a daily close up between ' : 'between ') + P(p.zone_lo, -1) + ' and ' + P(p.zone_hi, -1) + (p.why_zone ? ', at ' + p.why_zone : '')]);
  if (isN(p.out)) rows.push(['Buy window', 'open through ' + day(p.window)]);
  if (isN(p.out)) rows.push(['Out', (p.trigger != null ? 'once in, ' : '') + 'a daily close below ' + P(p.out, 1) + (p.why_out ? ', under ' + p.why_out : '')]);
  if (isN(p.out)) rows.push(p.trim ? ['Targets', 'a fifth off at ' + P(p.t1, -1) + (p.why_t1 ? ', ' + p.why_t1 : '') + '; the rest at ' + P(p.t2, -1) + (p.why_t2 ? ', ' + p.why_t2 : '') + (isN(p.time_stop) ? ', for at most ' + p.time_stop + ' sessions' : '')] :
    ['Target', P(p.t1, -1) + (p.why_t1 ? ', at ' + p.why_t1 : '')]);
  if (isN(p.out)) rows.push(['Reward to risk', num(p.r, 1) + ' to 1' + (p.trim ? ' at the first target, ' + num(p.r2, 1) + ' to 1 at the second' : '') + (isN(p.breakeven) ? '; it breaks even if it ' + (p.trim ? 'reaches the second target ' : 'works ') + num(p.breakeven * 100, 0) + '% of the time' : '')]);
  if (isN(p.out)) rows.push(['Horizon', 'if it works, typically by ' + day(p.by) + ' (' + plural(p.sessions, 'session') + ')']);
  const top = s.material || [], seen = new Set(top.map(f => f.head)), rest = a => a.filter(f => !seen.has(f.head));
  return grp('What matters most', facts(top)) + grp('What stands out', facts(rest(s.standouts))) +
    grp('What argues against it', facts(rest(s.against))) +
    grp('The desk’s take', '<p><b class="gk g' + s.gut.word.charAt(0) + '">' + esc(s.gut.word) + '.</b> ' + esc(s.take) + '</p>') +
    grp('What would change the desk’s mind', s.change ? '<p>' + esc(s.change) + '</p>' : '') +
    (rows.length ? grp('The plan', '<dl class="pdl">' + rows.map(r => '<div><dt>' + r[0] + '</dt><dd>' + bold(r[1]) + '</dd></div>').join('') + '</dl>') : '') +
    (typeof MDC == 'object' ? MDC.html(s) : '') +
    (s.news && s.news.length ? grp('In the news', '<ul class="cons sh nws"></ul>') : '') +
    (fac && s.sheet ? sheet(fac, s.sheet) : s.considered.length ? '<details class="dg mo"><summary><h4>Everything else the desk checked (' +
      s.considered.length + ')</h4></summary><ul class="cons">' + s.considered.map(t => '<li>' + esc(t) + '</li>').join('') + '</ul></details>' : '');
}
// every line of the owner's list the desk measures, under its heading: what the read found, or checked and none
function sheet(lines, got) {
  const groups = [];
  lines.forEach(l => { const g = groups.find(x => x.name === l.group) || (groups.push({name: l.group, rows: []}), groups[groups.length - 1]); g.rows.push(l); });
  const n = lines.filter(l => got[l.id]).length;
  return '<details class="dg mo"><summary><h4>Everything the desk considered (' + n + ' found of ' + lines.length + ')</h4></summary>' +
    groups.map(g => '<h5 class="sg">' + esc(g.name) + '</h5><ul class="cons sh">' + g.rows.map(l => '<li><b>' + esc(l.label) + '.</b> ' +
      (got[l.id] ? esc(got[l.id]) : '<span class="mu">' + esc(l.none) + '</span>') + '</li>').join('') + '</ul>').join('') + '</details>';
}
// headlines are untrusted: set as text, never as markup; a link only to http(s)
function news(u, a) {
  u.replaceChildren(...a.map(n => {
    const li = D.createElement('li');
    let ok = 0;
    try { ok = /^https?:/.test(new URL(n.url).protocol); } catch (e) {}
    const h = D.createElement(ok ? 'a' : 'span');
    h.textContent = n.headline;
    if (ok) Object.assign(h, {href: n.url, target: '_blank', rel: 'noopener noreferrer'});
    li.append(h, ' · ' + n.source + ' · ' + wd(n.at) + ET);
    return li;
  }));
}
function make(s, host) {
  const k = String(s.id || s.symbol).replace(/[^A-Za-z0-9_-]/g, '_'), e = el('tcard').content.firstElementChild.cloneNode(true),
    c = {id: s.id || s.symbol, el: e, host};
  e.setAttribute('data-id', c.id);
  'tog act cvn bd det db ch rkn'.split(' ').forEach(x => { c[x] = e.querySelector('.' + x); });
  c.tog.setAttribute('aria-controls', c.det.id = (host ? 'l-' : 'd-') + k);
  return c;
}
// the market gate on a read's face (the owner's fear rule): under Risk-off a Buy reads Smaller size when the name is on the
// Fear-Day Buy List's uptrend lane and Watch otherwise; with no market read it is never a plain Buy
function gated(s) {
  const d = ed || {}, w = d.market && d.market.badge && d.market.badge.word;
  if (!/^Buy/.test(s.action || '') || w === 'Risk-on' || w === 'Mixed') return s.action;
  return w === 'Risk-off' && !((d.picker || {}).buy || []).some(x => x.symbol === s.symbol) ? 'Watch' : 'Smaller size';
}
function fill(c, s, listed) {
  c.s = s;
  text(c.tog, s.symbol);
  text(c.act, gated(s));
  c.act.className = 'act ' + s.form;
  c.el.setAttribute('data-f', s.form);
  html(c.cvn, dots(s.conviction.level) + '<span>' + esc(s.conviction.word) + '</span>');
  html(c.bd, face(s, listed));
  html(c.db, read(s));
  const u = c.db.querySelector('.nws');
  if (u) news(u, s.news);
  if (c.sym !== s.symbol) html(c.ch, chartControls(c.sym = s.symbol));
}
const tint = e => { e.classList.remove('tint'); void e.offsetWidth; e.classList.add('tint'); };
function open(c, on = c.det.hidden, quiet) {
  c.det.hidden = !on;
  c.tog.setAttribute('aria-expanded', on);
  c.el.classList.toggle('open', on);
  if (on) V('open', c);
  if (!quiet && !c.host) history.replaceState(null, '', on ? '#bs-' + encodeURIComponent(c.s.symbol) : location.pathname + location.search);
}
const cword = w => /conviction/.test(w) ? w : w + ' conviction'; // the read's own word: "High conviction", "Solid"
function misc(d) {
  html(el('notes'), d.notes.length ? d.notes.map(t => '<li>' + esc(t) + '</li>').join('') : (d.notes_why ? '<li class="lu-mu">' + esc(d.notes_why) + '</li>' : ''));
  el('notes').hidden = !d.notes.length && !d.notes_why;
  text(el('cad'), '' + (d.cadence_min ?? 30));
  const L = d.lookup;
  el('look').hidden = el('lookb').hidden = !(L && L.count);   // no roster to read: no button that does nothing
  if (L && L.count) text(el('look-meta'), plural(L.count, 'stock') + ' with a read' + (L.as_of ? ' · as of the ' + et(L.as_of).md + ' close' : ''));
}

// until the first edition (or the first failure) only the masthead and the loading line show: nothing on screen moves
// after the page's own content: the window's load event, then an idle moment (or 2 s), then a further 1.5 s
function later(fn) {
  const go = () => setTimeout(() => (window.requestIdleCallback || (f => setTimeout(f, 1)))(fn, {timeout: 2e3}), 1500);
  if (D.readyState === 'complete') go(); else addEventListener('load', go, {once: true});
}
function shown() { el('grid').hidden = el('foot').hidden = false; }
function render(d, allow) {
  const first = !ed, ok = {};
  fac = d.factors; // before any card is filled: read() lays out the sheet from it
  if (first) shown();
  (d.setups || []).forEach(s => { ok[s.id] = 1; });
  keep(() => { market(d); misc(d); V('after', d); V('jump'); }, ok);
  ed = d;
  if (first) { el('load').hidden = true; deep(); later(tape); }
  paint();
}
// viz.js (deferred) draws the charts with the page's own formatters, into boxes this file sizes first
const V = (f, ...a) => { const v = window.MDV; return v && v[f] && v[f](...a); };
const rdy = new Promise(r => D.addEventListener('DOMContentLoaded', r));  // viz.js has run
window.MD = {freshness, sessNow, staleWords, sessLabel, dayWord, look: s => look(s), px, pl, pct, num, day, et, esc, isN, wd, cards, deep: () => deep(), get ed() { return ed; }};
// masthead state: one function of edition and clock (SH-02). In session stale past two cadences (owner, 11-05); out of
// it, past next_at or generated_at + cadence, plus LATE.
// past session.at, a pre/closed edition is in session (T-002, T-206)
function sessNow(s, now) { return s && s.at && now >= Date.parse(s.at) ? (s.state === 'open' ? 'closed' : 'open') : (s && s.state) || ''; }
function freshness(e, now, fail) {
  const cad = (e.cadence_min || 10) * 6e4, gen = Date.parse(e.generated_at) || 0;
  return fail ? 'stale' : sessNow(e.session, now) === 'open' ? (now - gen > 2 * cad ? 'stale' : 'fresh') : now > Math.max(Date.parse(e.next_at) || 0, gen + cad) + LATE ? 'stale' : 'closed';
}
function staleWords(e, now, fail) {
  const m = Math.max(0, Math.round((now - Date.parse(e.generated_at)) / 6e4)) + ' min old';
  return 'Stale: ' + (fail ? 'the desk could not be reached; showing the edition of ' + when(e.edition) + ET + ', ' + m : 'the newest edition is ' + m + '; one is due every ' + (e.cadence_min || 10) + ' min');
}
// every tab says so when the edition cannot be read (round 4 #2), not only the
// masthead; the notice leaves once an edition is drawn
function nofeed(on) {
  D.querySelectorAll('.panel').forEach(p => {
    let n = p.querySelector(':scope > .nofeed');
    if (!n && on) { n = D.createElement('p'); n.className = 'card mu nofeed'; n.setAttribute('role', 'status'); p.prepend(n); }
    if (n) { n.textContent = 'The desk’s latest edition could not be loaded. Retrying every minute.'; n.hidden = !on; }
  });
}
D.addEventListener('md:tab', () => setTimeout(() => { if (!ed) nofeed(failing); }, 800));
// the session's words against the reader's clock: the edition states the moment ("at"), the page names its day, so a
// label read after midnight or over a weekend never says "tomorrow" for today (round 4 #3)
function dayWord(at, now) {
  const a = et(at), n = et(now), tm = et(now + 864e5);
  return a.key === n.key ? 'today' : a.key === tm.key ? 'tomorrow' : a.weekday;
}
function sessLabel(s, now) {
  if (!s || !s.at) return s ? s.label : '';
  const a = Date.parse(s.at), hm = et(a).hm;
  if (now >= a) return s.state === 'open' ? 'Market closed' : 'Market open';
  return s.state === 'open' ? 'Market open · closes ' + hm + ' ET' : (s.state === 'pre' ? 'Pre-market' : 'Market closed') + ' · opens ' + dayWord(a, now) + ' ' + hm + ' ET';
}
function paint() {
  const dot = el('dot');
  el('ew').hidden = !ed;
  if (!ed) {
    dot.className = 'dot' + (failing ? ' stale' : '');
    if (failing) { ['st1', 'load'].forEach(i => text(el(i), 'Can’t reach the desk · retrying…')); shown(); }
    nofeed(failing);
    return;
  }
  nofeed(false);
  const st = freshness(ed, Date.now(), failing),
    g = ed.generated_at, e = when(g);
  dot.className = 'dot ' + st;
  const sw = st === 'stale' && !paused;
  text(el('dotl'), sw ? '' : cap(st) + ': ');
  el('ew').hidden = sw;
  text(el('st1'), sw ? staleWords(ed, Date.now(), failing) : e + ET + ' · ' + (paused ? 'paused' : ago(Date.parse(g))));
  ['st2', 'sess'].forEach(i => text(el(i), sessLabel(ed.session, Date.now())));
  el('sess').hidden = ed.session.state === 'open';
  const nx = Date.now() > Date.parse(ed.next_at) ? '' : 'Next edition ' + when(ed.next_at) + ET;
}
function plan(ms) {
  clearTimeout(timer);
  due = Date.now() + ms;
  if (!paused && !D.hidden) timer = setTimeout(check, ms);
}
function check() {
  if (busy || paused) return;
  busy = true;
  last = Date.now();
  fetch(SRC, {cache: 'no-cache'}).then(r => {
    if (r.ok) return rdy.then(() => r.json());
    throw new Error('HTTP ' + r.status);
  }).then(d => {
    const why = invalid(d);
    if (why) throw new Error('refused: ' + why);
    busy = failing = false;
    fails = 0;
    latest = d;
    if (!ed || d.seq > ed.seq) render(d, false); else paint(); // only a higher seq replaces the view
    plan(POLL);   // fetched no-cache (publish.early_load)
  }).catch(() => {
    busy = false;
    failing = true;
    fails++;
    paint();
    // keep the last good edition; x2 backoff, full jitter, 10 s base, 5 min cap
    plan(Math.max(1e3, Math.random() * Math.min(CAP, BASE * 2 ** (fails - 1))));
  });
}
function deep() {
  const h = location.hash, id = new URLSearchParams(h.slice(1)).get('s'), c = id ? cards[id] :
    h.startsWith('#bs-') && Object.values(cards).find(x => x.s.symbol === decodeURIComponent(h.slice(4)));
  if (!c) return;
  open(c, true, true);
  c.el.scrollIntoView({block: 'start'});
  c.tog.focus({preventScroll: true});
}

// Look up: the roster's reads of the last session, fetched only when asked for
let idx = null, idxP = null, lookC = null;
const shard = s => /^[A-Z]/.test(s) ? s.charAt(0) : '0', okRead = r => r && !chk(r, READ, 'read') && !CUR.test(JSON.stringify(r));
const getJ = u => fetch(DIR + u, {cache: 'no-cache'}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
function index() { return idxP || (idxP = getJ('reads-index.json').then(j => (idx = j)).catch(e => { idxP = null; throw e; })); }
function suggest() {
  const q = el('lq').value.trim().toUpperCase(), out = el('ls');
  if (!q || !idx) return html(out, '');
  const names = Object.keys(idx.names), hit = names.filter(n => n.startsWith(q)).slice(0, 8);
  html(out, hit.map(n => '<li><button type="button" class="lsb" data-s="' + esc(n) + '"><b>' + esc(n) + '</b> <span class="mu">' +
    esc(idx.names[n].join(' · ')) + '</span></button></li>').join('') || '<li class="mu">No stock by that name on the desk’s list.</li>');
}
function look(sym) {
  const res = el('lres'), on = Object.values(cards).find(c => c.s && c.s.symbol === sym);
  html(el('ls'), '');
  if (on) { // a listed name has one read: its card on the board
    html(res, '<p class="mu">' + esc(sym) + ' is on the board: its card is open above.</p>');
    open(on, true);
    on.el.scrollIntoView({block: 'start'});
    return tint(on.el);
  }
  html(res, '<p class="mu">Reading ' + esc(sym) + '…</p>');
  getJ('reads-' + shard(sym) + '.json').then(j => {
    const r = j[sym];
    if (!okRead(r)) throw new Error('bad read');
    lookC = make(r, 1);
    fill(lookC, r, false);
    open(lookC, true, true);
    res.textContent = '';
    const bk = bookPlan(sym);
    if (bk) res.insertAdjacentHTML('beforeend', '<p class="lbk">' + esc(bk) + '</p>');
    res.appendChild(lookC.el);
  }).catch(() => html(res, '<p class="mu">That read could not be loaded. Try again.</p>'));
}
// HM-06: the book's own plan beside the desk's read
function bookPlan(sym) {
  const L = (ed && ed.book && ed.book.live) || {}, f = v => isN(v) ? v.toFixed(2) : '', h = x => x.symbol === sym;
  const p = (L.positions || []).find(h), o = (L.orders || []).find(h), r = p || o;
  if (!r) return '';
  const t = (r.targets || []).map(x => f(x.price)).filter(Boolean).join(' / ');
  return 'Claude\u2019s book ' + (p ? 'holds ' + sym + ' from ' + f(p.entry) : 'is working a ' + (o.entry_type === 'limit' ? 'limit buy at ' : 'buy above ') + f(o.level) + ' on ' + sym) +
    (isN(r.stop) ? ', stop ' + f(r.stop) : '') + (t ? ', targets ' + t : '') + '. That plan is the trader\u2019s own; the read below is the desk\u2019s chart read of the last close, so their levels differ.';
}
el('lq').addEventListener('focus', () => index().then(suggest).catch(() => {}));
el('lq').addEventListener('input', () => (idx ? suggest() : index().then(suggest).catch(() => {})));
el('lf').addEventListener('submit', e => {
  e.preventDefault();
  const q = el('lq').value.trim().toUpperCase();
  // an unknown name clears the last card (MK-50)
  if (q) index().then(() => { if (idx.names[q]) return look(q); lookC = null; html(el('lres'), ''); suggest(); })
    .catch(() => html(el('lres'), '<p class="mu">The list of stocks could not be loaded. Try again.</p>'));
});
el('ls').addEventListener('click', e => { const b = e.target.closest('.lsb'); if (b) { el('lq').value = b.dataset.s; look(b.dataset.s); } });

function onCard(e, c) {
  const t = e.target;
  if (t.closest('a') || t.closest('summary') || (t.closest('.det') && !t.closest('.tog')) || String(getSelection())) return;
  open(c);
}
el('lres').addEventListener('click', e => { if (lookC && e.target.closest('.setup')) onCard(e, lookC); });
D.addEventListener('click', e => { e.target.closest('.chip')?.classList.toggle('on'); });
el('refresh').addEventListener('click', () => { clearTimeout(timer); check(); });
el('pause').addEventListener('click', e => {
  const b = e.currentTarget;
  paused = !paused;
  b.classList.toggle('on', paused);
  text(b.querySelector('.pl'), paused ? 'Resume' : 'Pause');
  if (paused) clearTimeout(timer); else check();
  paint();
});
addEventListener('hashchange', deep);
D.addEventListener('visibilitychange', () => {
  if (D.hidden) return clearTimeout(timer);
  if (paused) return;
  if (Date.now() - last > POLL) check(); else plan(Math.max(0, due - Date.now()));
  paint();
});
const dlg = el('about');
el('aboutb').addEventListener('click', () => dlg.showModal());
el('aboutx').addEventListener('click', () => dlg.close());
dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
setInterval(() => { if (!paused && !D.hidden) paint(); }, 15e3);


// ---- a legibility floor for chart labels (round 4 #7): an SVG drawn on a fixed viewBox shrinks its text with the box,
// to 6-9 px on a phone. After any redraw, a label rendering under 11 px is set to the size that renders 11 px
const MINPX = 11;
function floorText(root) {
  (root || D).querySelectorAll('svg text').forEach(t => {
    const svg = t.ownerSVGElement, m = svg && svg.getScreenCTM();
    if (!m || !m.a || !t.textContent.trim()) return;
    const base = parseFloat(t.dataset.fs || getComputedStyle(t).fontSize);
    if (!t.dataset.fs) t.dataset.fs = base;
    const px = base * m.a;
    t.style.fontSize = px < MINPX ? (MINPX / m.a).toFixed(2) + 'px' : '';
  });
}
let floorQ = 0;
const floorSoon = () => { if (!floorQ) floorQ = requestAnimationFrame(() => { floorQ = 0; floorText(); }); };
new MutationObserver(floorSoon).observe(D.documentElement, {childList: true, subtree: true});
addEventListener('resize', floorSoon);

/* chart-begin: TradingView, named only here: a link on each card, and its ticker tape once the first edition is drawn */
const tvUrl = s => 'https://www.tradingview.com/symbols/' + encodeURIComponent(s) + '/';
const chartControls = s => s.length > 15 || /[^A-Za-z0-9.:_-]/.test(s) ? '' : '<div class="pc"></div><a class="ext" href="' + esc(tvUrl(s)) +
  '" target="_blank" rel="noopener noreferrer">Open on TradingView ↗</a>';
// the tape is TradingView's own widget page in a frame (what its embed script would build), so no third-party script
// runs in this page and none of its calls meet this page's CSP; it loads after the page is drawn and idle
function tape() {
  const t = el('tape');
  if (t.firstChild) return;
  const cfg = {symbols: 'AMEX:SPY SPY,NASDAQ:QQQ QQQ,AMEX:IWM IWM,AMEX:DIA DIA,COINBASE:BTCUSD Bitcoin,COINBASE:ETHUSD Ether'
    .split(',').map(x => ({proName: x.split(' ')[0], title: x.slice(x.indexOf(' ') + 1)})), showSymbolLogo: true, isTransparent: true,
    displayMode: 'regular', colorTheme: 'light', locale: 'en', width: '100%', height: 46};
  const f = D.createElement('iframe');
  f.title = 'Market tape';
  f.setAttribute('scrolling', 'no');
  f.src = 'https://www.tradingview-widget.com/embed-widget/ticker-tape/?locale=en#' + encodeURIComponent(JSON.stringify(cfg));
  f.tabIndex = -1;                 // the tape's nine links are not keyboard stops (audit 2026-11-04, round 4 #9)
  t.appendChild(f);
}
/* chart-end */

paint();
check();
})();
