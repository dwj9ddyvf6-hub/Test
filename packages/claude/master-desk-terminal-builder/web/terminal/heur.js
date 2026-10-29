// The Heuristics panel (desk/picker/heur.py, the edition's `heur`) and the per-ticker chips on cards and Look up
// (heur-names.json, fetched once). The page only draws what the desk graded: grades, numbers and "not measured" come
// from the edition; nothing here decides a flag.
(function () {
  'use strict';
  let H = null, names = null, pending = null;
  const M = () => window.MD || {}, E = s => (M().esc ? M().esc(s) : String(s));
  const sg = (v, d = 1) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d);
  const ST = s => (s.on === true ? 'up' : s.on === false ? 'mu' : 'wn');
  const money = v => (v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M' : v >= 1e3 ? '$' + Math.round(v / 1e3) + 'k' : '$' + v);
  const EVW = {A: 'replicated out of sample', B: 'held out of sample once', C: 'in-sample only', V: 'volatility only', X: 'refuted', P: 'forward test running'};
  const EV = g => EVW[g] || '';
  const reason = k => (H.avoid.reasons.find(r => r.key === k) || {label: k, grade: '', number: ''});
  function tile(x) {
    return '<li class="hzt"><div class="hzh"><b>' + E(x.title) + '</b><span class="bdg ' + ST(x) + '">' + E(x.state) + '</span><span class="hzg">' +
      E(EV(x.ev_grade)) + '</span></div><p>' + E(x.reading) + '</p><p class="mu"><b>Changes:</b> ' + E(x.changes) + '</p><details><summary>Evidence</summary><p class="mu">' + E(x.evidence) + '</p></details></li>';
  }
  function lane(open) {
    const a = H.avoided || [], n = H.n || {}, shown = open ? a : a.slice(0, 8);
    const rows = shown.map(r => '<li><b>' + E(r.symbol) + '</b><span class="mu">' + E(r.tier_word || '') + '</span><span class="hzr">' +
      r.flags.map(k => '<span class="bdg ' + (r.off ? 'wn' : 'dn') + '" title="' + E(reason(k).number) + '">' + E(reason(k).label) + ' · ' + E(EV(reason(k).ev_grade)) +
        '</span>').join('') + '</span><span class="mu hzc2">capacity ' + money(r.capacity_usd) + '</span></li>').join('');
    return '<h3>Avoided today <span class="mu">' + n.flagged + ' flagged of ' + n.universe + ' names screened' + (H.avoid.on === false ? ' · veto off' : '') + '</span></h3><p>' + E(H.avoid.text) +
      '</p><p class="mu">' + E(H.avoid.veto_value) + '</p>' + (rows ? '<ul class="hzl">' + rows + '</ul>' : '<p class="mu">No name carries a flag today.</p>') +
      (a.length > 8 ? '<button type="button" class="more" id="hzmore" aria-expanded="' + !!open + '">' + (open ? 'Show fewer' : 'Show all ' + a.length) + '</button>' : '') +
      '<details><summary>What each flag is worth (graded study numbers, holdout 2023+)</summary><ul class="hzk">' + H.avoid.reasons.map(r => '<li><b>' + E(r.label) + '</b> · ' + E(EV(r.ev_grade)) + ' · ' +
        E(r.number) + '</li>').join('') +
      '</ul></details>';
  }
  let all = false;
  function panel() {
    const box = document.getElementById('heur');
    if (!box) return;
    if (!H) { box.hidden = true; return; }
    box.innerHTML = '<div class="shd"><div class="sht"><p class="kick">Graded rules · point in time</p><h2>Heuristics</h2></div><span class="pv">as of ' + E(H.as_of || '') + '</span></div>' +
      '<div class="card hz"><p class="hzs">' + E(H.market.tape) + '</p><ul class="hzm">' + H.market.items.map(tile).join('') + '</ul>' +
      '<div id="hzlane">' + lane(all) + '</div>' +
      '<h3>What to buy <span class="mu">chips on every card and Look up</span></h3><p>' + E(H.buy.text) + '</p>' +
      '<details><summary>The buy-side features, with today’s median</summary><ul class="hzk">' + H.chips.map(c => '<li><b>' + E(c.label) + '</b> · ' + E(EV(c.ev_grade)) + ' · ' +
        (c.median == null ? '' : 'median today ' + sg(c.median, 2) + ' · ') + E(c.applies === 'ALL' ? 'all names' : c.applies === 'UP' ? 'uptrend names' : 'deep resets') +
        '<br><span class="mu">' + E(c.evidence) + '</span></li>').join('') + '</ul></details>' +
      '<h3>Exit</h3><p>' + E(H.exit.text) + '</p>' +
      '<h3>Not used (refuted) <span class="mu">' + H.refuted.length + ' ideas the evidence rejected</span></h3><ul class="hzk hzx">' + H.refuted.map(r => '<li><b>' + E(r.label) + '</b> — ' + E(r.why) +
        ' <span class="mu">(' + E(r.source) + ')</span></li>').join('') + '</ul>' +
      '</div>';
    box.hidden = false;
    const b = document.getElementById('hzmore');
    if (b) b.onclick = () => { all = !all; document.getElementById('hzlane').innerHTML = lane(all); const n = document.getElementById('hzmore'); if (n) n.onclick = b.onclick; };
  }
  // ---- per-ticker chips ----
  const FMT = {
    F3: v => 'Pullback ' + sg(v, 1) + ' vs its usual', N1: v => 'Bystander ' + sg(v, 1), N7: v => 'Gaps bought ' + v,
    F7: v => '10-day vs SPY ' + sg(v, 1) + ' pts', F6: v => 'Selling volume ' + v.toFixed(1) + 'x', MOM: v => '6-month ' + sg(v, 0) + '%',
    NVI: v => 'NVI ' + sg(v, 1) + '% vs 1-yr avg', YD: v => 'Last session ' + sg(v, 1) + '%',
    SP: v => (v === true ? 'S&P 500 member' : v === false ? 'Not in the S&P 500' : 'S&P 500: not measured'), DIP: v => (v ? 'Momentum dip' : '')
  };
  function chips(sym) {
    const r = names && names.names[sym], leg = {};
    if (!r || !H) return '';
    H.chips.forEach(c => { leg[c.key] = c; });
    const out = [];
    if (r.a.length) r.a.forEach(k => out.push('<button type="button" class="hzc bdg ' + (r.ao ? 'wn' : 'dn') + '" data-t="' + E(reason(k).label + ' · ' + EV(reason(k).ev_grade) + '. ' + reason(k).number +
      (r.ao ? '. Veto off: SPY is under its 200-day, where the edge reverses.' : '.')) + '">Avoid: ' + E(reason(k).label) + '</button>'));
    else if (H.n.universe) out.push('<button type="button" class="hzc bdg up" data-t="No avoid flag fired on the last closed session.">No avoid flag</button>');
    r.c.forEach(([k, v, g]) => {
      if (v === null || v === undefined || (k === 'DIP' && !v) || !FMT[k]) return;
      const c = leg[k] || {}, med = c.median != null && typeof v === 'number' ? ' (median ' + sg(c.median, 1) + ')' : '';
      out.push('<button type="button" class="hzc bdg ' + (g === true ? 'up' : g === false ? 'mu' : 'mu') + '" data-t="' + E((c.label || k) + ' · ' + EV(c.ev_grade) + '. ' + (c.evidence || '')) + '">' +
        E(FMT[k](v) + med) + '</button>');
    });
    return '<div class="hzrow" aria-label="Heuristics for ' + E(sym) + '">' + out.join('') + '<p class="mu hzn" hidden></p></div>';
  }
  function decorate() {
    if (!names || !H) return;
    document.querySelectorAll('#cards .setup, #lres .setup').forEach(card => {
      const t = card.querySelector('.tog'), sym = t && t.textContent.trim();
      if (!sym || card.querySelector(':scope > .hzrow')) return;
      const h = chips(sym), det = card.querySelector(':scope > .det');
      if (h && det) det.insertAdjacentHTML('beforebegin', h);
    });
  }
  function load() {
    if (names || pending || !H) return;
    pending = fetch('heur-names.json', {cache: 'no-cache'}).then(r => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(j => { if (j && j.as_of === H.as_of) { names = j; decorate(); } }).catch(() => {}).finally(() => { pending = null; });
  }
  let queued = false;
  new MutationObserver(() => { if (queued) return; queued = true; requestAnimationFrame(() => { queued = false; decorate(); }); })
    .observe(document.getElementById('main') || document.body, {childList: true, subtree: true});
  document.addEventListener('click', e => {
    const c = e.target.closest('.hzc');
    if (!c) return;
    const n = c.parentNode.querySelector('.hzn');
    if (n) { n.textContent = c.dataset.t || ''; n.hidden = !n.textContent || (n.hidden === false && n.dataset.k === c.dataset.t); n.dataset.k = n.hidden ? '' : c.dataset.t; }
    e.stopPropagation();
  }, true);
  window.MDH = {render: d => { const had = H && H.as_of; H = d && d.heur || null; if (H && had !== H.as_of) names = null; panel(); load(); decorate(); }};
})();
