// The Fear-Day Buy List page (desk/picker/fearday.py via the edition's `picker`), with the market gate on its face. The retired v2 morning sheet is gone.
(function () {
  'use strict';
  // the Fear-Day Buy List (desk/picker/fearday.py, the edition's `picker`): three lanes, each name with its why-lines,
  // its vetoes and its plan (next open, a 60-session hold, a disaster stop as a level, an equal-risk weight)
  const LANES = [['buy', 'Buy list · uptrend pullbacks'], ['watch', 'Watch lane · deep resets'], ['small', 'Micro/Nano lane']];
  // the market gate on the face (desk/terminal/gates.py, the owner's rule): Risk-on full size; Mixed full size for an uptrend
  // pullback, else smaller; Risk-off lets only a fear-day pullback in an uptrend buy, at the smaller size, everything else
  // watches; no market read is never full size. The Buy List only exists on a fear day, so its uptrend lane is that pullback.
  function gate(key, badge) {
    const w = badge && badge.word, up = key === 'buy';
    if (w === 'Risk-on') return {size: 'Full size', cls: 'up'};
    if (w === 'Mixed') return up ? {size: 'Full size', cls: 'up'} : {size: 'Smaller size', cls: 'wn'};
    if (w === 'Risk-off') return up ? {size: 'Smaller size', cls: 'wn', note: 'Market Risk-off, but a fear-day pullback qualifies: smaller size.'} :
      {size: 'Watch', cls: 'mu', note: 'Market Risk-off: only a fear-day pullback in an uptrend buys, so this lane watches.'};
    return {size: 'Smaller size', cls: 'wn', note: 'Market read unavailable: never full size.'};
  }
  const cap = n => !isFinite(n) ? '' : n >= 1e9 ? '$' + (n / 1e9).toFixed(1) + 'B' : n >= 1e6 ? '$' + Math.round(n / 1e6) + 'M' : n >= 1e3 ? '$' + Math.round(n / 1e3) + 'K' : '$' + Math.round(n);
  const ROLE = {zone_lo: -1, zone_hi: -1, t1: -1, t2: -1, stop: 1};
  function card(c, M, g, hid) {
    const p = c.plan || {}, x = c.context || {}, v = (c.vetoes || []).filter(y => y.status === 'warning' || y.status === 'penalty'),
      rows = x.ladder && x.ladder.status === 'ok' ? x.ladder.rows : [], at = r => (rows.find(y => y.role === r) || {}).at,
      P = (r, k) => M.isN(c.close) && M.isN(at(r)) ? M.px(c.close, at(r), ROLE[k || r]) : '—',
      stop = M.isN(at('stop')) ? P('stop') : M.isN(p.stop) ? '$' + M.num(p.stop, 2) : p.stop_atr == null ? (p.exit_by ? 'None · time exit ' + p.exit_by : 'None') : '—',
      buy = M.isN(at('zone_lo')) ? P('zone_lo') + '–' + P('zone_hi').slice(1) : 'Next open',
      tg = M.isN(at('t1')) ? P('t1') + (M.isN(at('t2')) ? ' · ' + P('t2') : '') : 'No real level above',
      s = {symbol: c.symbol, close: c.close, context: x, plan: {out: M.isN(at('stop')) ? at('stop') : p.stop_pct}},
      o = x.odds && x.odds.text, cat = x.catalyst && (x.catalyst.text || (x.catalyst.filing && x.catalyst.filing.status === 'ok' ?
        'Latest filing ' + x.catalyst.filing.form + ' on ' + x.catalyst.filing.date : '')),
      det = window.MDC && x.ladder ? window.MDC.html(s) : '';
    return '<li class="br pk"' + (hid ? ' hidden' : '') + ' data-sym="' + M.esc(c.symbol) + '"><div class="bh"><b>' + M.esc(c.symbol) + '</b><span class="bdg ' + g.cls + '">' + g.size + '</span><span class="bdg mu">' + M.esc(c.tier_word || '') +
      '</span><span class="mu">#' + c.rank + ' · score ' + M.num(c.score, 2) + '</span>' +
      (c.lens && M.isN(c.lens.c8) ? '<span class="bdg ' + (c.lens.ok ? 'up' : 'mu') + '">C8 ' + M.num(c.lens.c8, 0) + (c.lens.ok ? ' ✓' : '') + '</span>' : '') + '<button type="button" class="pkb">Full read ›</button></div>' +
      '<dl class="bm"><div><dt>' + (g.size === 'Watch' ? 'Watch zone' : 'Buy') + '</dt><dd>' + buy + '</dd><small>next open, not above ' + P('zone_hi') + '</small></div><div><dt>Stop</dt><dd>' + stop +
      '</dd></div><div><dt>Targets</dt><dd>' + tg + '</dd></div><div><dt>Weight</dt><dd>' + M.num(p.weight_pct, 1) + '%</dd>' +
      (M.isN(p.max_usd) ? '<small>' + cap(p.max_usd) + '/day capacity</small>' : '') + '</div><div><dt>Exit by</dt><dd>' +
      (p.exit_by ? M.esc(M.day(p.exit_by)) : '—') + '</dd></div></dl>' +
      (c.why || []).map(w => '<p class="bi">' + M.esc(w) + '</p>').join('') +
      (o ? '<p class="bi"><b>Odds.</b> ' + M.esc(o) + '</p>' : '') + (cat ? '<p class="bi"><b>Catalyst.</b> ' + M.esc(cat) + '</p>' : '') +
      '<p class="bi">Cost about ' + (M.isN(p.cost_pct) ? M.num(p.cost_pct, 2) + '%' : '—') +
      (v.length ? ' · ' + v.map(y => M.esc(y.why) + ' (' + y.status + ')').join(' · ') : '') + '</p>' +
      (det ? '<details class="dg pkd"><summary>Ladder, why, levels</summary>' + det + '</details>' : '') + '</li>';
  }
  // each lane shows its first SHOW names; the control shows the rest (the edition carries the top 20). The open lanes survive a re-render
  const SHOW = 5, open = new Set();
  function lanes(k, M, badge) {
    return LANES.filter(([key]) => (k[key] || []).length).map(([key, t]) => {
      const g = gate(key, badge), cs = k[key], more = cs.length > SHOW, on = open.has(key);
      return '<h3 class="ba">' + t + (g.size === 'Watch' ? '' : ' · ' + g.size.toLowerCase()) + '</h3>' + (g.note ? '<p class="mu gn">' + g.note + '</p>' : '') +
        '<ul class="bl" id="pkl-' + key + '">' + cs.map((c, i) => card(c, M, g, i >= SHOW && !on)).join('') + '</ul>' +
        (more ? '<button type="button" class="pkm" data-lane="' + key + '" aria-expanded="' + on + '" aria-controls="pkl-' + key + '">' +
          (on ? 'Show ' + SHOW : 'Show ' + cs.length) + '</button>' : '');
    }).join('');
  }
  function picker(d) {
    const box = document.getElementById('fdb'), M = window.MD, k = d && d.picker;
    if (!box || !M) return;
    if (!k) { box.hidden = true; return; }
    const ln = lanes(k, M, d.market && d.market.badge);
    box.innerHTML = '<div class="shd"><div class="sht"><p class="kick">Best Setups · ' + M.esc(k.as_of || '') + '</p><h2>Fear-Day Buy List</h2></div>' +
      '<span class="pv">' + M.esc(k.label) + '</span></div><div class="card bsheet">' + (ln || '<p class="ba">' + M.esc(k.text) + '</p>') + '</div>';
    box.hidden = false;
    box.onclick = e => {
      const b = e.target.closest('.pkm');
      if (b) { const key = b.dataset.lane; open.has(key) ? open.delete(key) : open.add(key); picker(d); const nb = box.querySelector('.pkm[data-lane="' + key + '"]'); nb && nb.focus(); return; }
      const li = e.target.closest('.pk');   // a tap opens the board card, or Look up's read, as the rest of the page does
      if (!li || e.target.closest('a,summary,.pkd') || String(getSelection())) return;
      M.look && M.look(li.dataset.sym);
      const t = document.getElementById('lres'), on = Object.values(M.cards || {}).some(y => y.s && y.s.symbol === li.dataset.sym);
      if (t && !on) t.scrollIntoView({block: 'start'}); };
  }
  window.MDB = {render: picker, cards: lanes};
})();
