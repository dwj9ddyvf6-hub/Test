/* The card's context (edition setups[].context, desk/terminal/context.py): where price sits on the plan, why the read
   leans the way it does, trend quality, a reclaim, the supports under price and what is coming. A block the desk could
   not measure is left out; nothing is drawn from a guess. */
(() => {
  const M = () => window.MD || {}, E = s => M().esc ? M().esc(s) : String(s);
  const sg = (v, d = 1) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d);
  const ok = b => b && b.status === 'ok';
  const ord = n => n + ((n % 100 - n % 10 === 10) ? 'th' : ['th', 'st', 'nd', 'rd'][n % 10] || 'th');
  const fromNow = (c, at) => { const n = ok(c.ladder) ? (c.ladder.rows.find(r => r.role === 'now') || {at: 0}).at : 0; return 100 * ((1 + at / 100) / (1 + n / 100) - 1); };
  const grp = (h, inner) => inner ? '<div class="dg cx"><h4>' + h + '</h4>' + inner + '</div>' : '';
  // prices as the card shows them: the page's own role-safe rounding (stop up, buys and targets down: app.js px)
  const R = {t2: -1, t1: -1, zone_hi: -1, zone_lo: -1, stop: 1, now: 0};
  const $ = (s, at, r) => M().px && s.close ? M().px(s.close, at, r) : '';
  function ladder(b, s) {
    if (!ok(b) || !s.close) return '';
    const now = (b.rows.find(r => r.role === 'now') || {at: 0}).at, d = at => 100 * ((1 + at / 100) / (1 + now / 100) - 1);
    return '<ol class="cxl">' + b.rows.map(r => '<li class="' + r.role + '"><span>' + E(r.label) + '</span><b>' + $(s, r.at, R[r.role]) +
      '</b><small>' + (r.role === 'now' ? 'now' : sg(d(r.at)) + '%') + '</small></li>').join('') + '</ol>';
  }
  function why(b) {
    if (!ok(b)) return '';
    const mx = Math.max(...b.rows.map(r => Math.abs(r.diff)), 0.01);
    return '<ul class="cxw">' + b.rows.map(r => { const w = (48 * Math.abs(r.diff) / mx).toFixed(1), x = r.diff >= 0 ? 50 : 50 - w;
      return '<li><span>' + E(r.label) + '</span><svg viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><line x1="50" x2="50" y1="0" y2="8"/>' +
        '<rect class="' + (r.diff >= 0 ? 'up' : 'dn') + '" x="' + x + '" y="1" width="' + w + '" height="6"/></svg><small>' + sg(r.diff) +
        ' vs typical · ' + ord(r.pct) + ' percentile</small></li>'; }).join('') + '</ul><p class="mu">' + E(b.basis) + '.</p>';
  }
  function facts(c, s) {
    const a = [];
    if (ok(c.chop)) a.push('<b>Trend quality ' + c.chop.score.toFixed(2) + '</b> ' + E(c.chop.word));
    if (ok(c.reclaim) && c.reclaim.kind !== 'none') a.push('<b>Reclaim.</b> ' + E(c.reclaim.text) + '; wrong on a close under ' + $(s, c.reclaim.stop_at, 1) + '.');
    const st = s.plan && typeof s.plan.out === 'number' ? s.plan.out : -Infinity,
      sup = ok(c.levels) ? c.levels.rows.filter(r => r.at > st) : [];   // supports inside the trade's risk only
    if (sup.length) a.push('<b>Support above the stop.</b> ' + sup.map(r => $(s, r.at, -1) + ' (' + sg(fromNow(c, r.at)) + '%, ' + r.age + ')').join(' · '));
    if (c.catalyst && c.catalyst.text) a.push('<b>' + (c.catalyst.offering ? 'Offering' : 'Ahead') + '.</b> ' + E(c.catalyst.text));
    else if (c.catalyst && c.catalyst.filing && ok(c.catalyst.filing)) a.push('<b>Latest filing.</b> ' + E(c.catalyst.filing.form) + ' on ' + E(c.catalyst.filing.date));
    return a.length ? '<ul class="cxf">' + a.map(x => '<li>' + x + '</li>').join('') + '</ul>' : '';
  }
  window.MDC = {html: s => { const c = s && s.context; if (!c) return '';
    return grp('Where price sits', ladder(c.ladder, s)) + grp('Why the read leans this way', why(c.why)) + grp('Around the setup', facts(c, s)); }};
})();
