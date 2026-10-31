/* Tool visual binding (build stream 2, the tools). Uses the shared
   VisualKit primitives in visual.js; this file only maps each tool
   page's own data.json fields onto a primitive. It reads no other
   page's data, invents no figure, and fails closed to the kit's plain
   state visual when the named fields are absent. Loaded after
   visual.js on tool pages. */
(function () {
  "use strict";
  function isNum(v) { return typeof v === "number" && isFinite(v); }
  function ranked(rows, s, title, label, unit) {
    rows = (rows || []).filter(function (r) { return r && isNum(r.score); });
    if (!rows.length) return null;
    return VisualKit.ranked({ rows: rows, session: s, title: title, label: label });
  }
  function tiles(items, s, title, label) {
    items = (items || []).filter(function (t) { return t && t.label != null; });
    if (!items.some(function (t) { return isNum(t.value); })) return null;
    return VisualKit.tiles({ items: items, session: s, title: title, label: label });
  }
  function groupCounts(rows, keyFn) {
    var counts = {}, order = [];
    (rows || []).forEach(function (r) {
      var k = keyFn(r); if (k == null || k === "") return;
      if (!(k in counts)) { counts[k] = 0; order.push(k); }
      counts[k]++;
    });
    return order.map(function (k) { return { name: k, score: counts[k] }; })
      .sort(function (a, b) { return b.score - a.score; });
  }
  function hourStrip(events, s, title, label) {
    var rows = groupCounts(events, function (e) {
      return e.time_utc ? String(e.time_utc).slice(11, 13) + ":00" : null;
    });
    return ranked(rows, s, title, label);
  }
  function closesLine(d, s, title, label) {
    var src = d.bars || d.prices || {};
    var entry = src.SPY;
    if (!Array.isArray(entry) || !Array.isArray(entry[1]) || !Array.isArray(d.dates)) return null;
    var closes = entry[1];
    var series = closes.map(function (v, i) { return { date: d.dates[i] || "", value: v }; });
    if (series.filter(function (p) { return isNum(p.value); }).length < 2) return null;
    return VisualKit.line({ series: series, session: s, title: title, label: label });
  }
  function windowChange(d, s, title, label, sessionsBack) {
    var src = d.bars || d.prices || {};
    var rows = [];
    Object.keys(src).forEach(function (sym) {
      var e = src[sym];
      if (!Array.isArray(e) || !Array.isArray(e[1])) return;
      var c = e[1].filter(isNum);
      if (c.length <= sessionsBack) return;
      var then = c[c.length - 1 - sessionsBack], now = c[c.length - 1];
      if (!then) return;
      rows.push({ name: sym, score: Math.round(1000 * (now / then - 1)) / 10 });
    });
    rows.sort(function (a, b) { return b.score - a.score; });
    return ranked(rows.slice(0, 12), s, title, label);
  }

  var ADAPTERS = {
    "13f-tracker": function (d, s) {
      return ranked((d.holders || []).slice(0, 12).map(function (h) {
        return { name: h.holder, score: h.total_value, coverage: (h.positions_count || 0) + " positions" };
      }), s, "The biggest holders on record", "Total value of the holdings each holder reported, biggest first.");
    },
    "activity-profile": function (d, s) {
      return ranked((d.sessions || []).map(function (x) {
        return { name: x.session, score: x.total_premium_usd };
      }), s, "Money that changed hands, by session", "Total premium across the options prints examined in each session on record.");
    },
    "alert-tape": function (d, s) {
      return hourStrip(d.alerts || [], s, "Alerts by hour of the day", "How many of the alerts on record landed in each hour, counted from the same alerts listed below.");
    },
    "breakout-scanner": function (d, s) {
      var src = d.bars || {}, w = d.high_window || 252, rows = [];
      Object.keys(src).forEach(function (sym) {
        var e = src[sym];
        if (!Array.isArray(e) || !Array.isArray(e[1])) return;
        var c = e[1].filter(isNum);
        if (c.length < 10) return;
        var win = c.slice(-w), hi = Math.max.apply(null, win), now = c[c.length - 1];
        if (!hi) return;
        rows.push({ name: sym, score: Math.round(100 * now / hi * 10) / 10 });
      });
      rows.sort(function (a, b) { return b.score - a.score; });
      return ranked(rows.slice(0, 12), s, "Closest to their own high", "Each name's last close as a percent of its highest close in the window this page uses. 100 would mean a new high.");
    },
    "chain-explorer": function (d, s) {
      var u = (d.underlyings || [])[0];
      if (!u || !u.snapshots || !u.snapshots.length) return null;
      var snap = u.snapshots[u.snapshots.length - 1];
      var byStrike = {};
      (snap.expiries || []).forEach(function (ex) {
        (ex.strikes || []).forEach(function (st) {
          var oi = (st.call && isNum(st.call.oi) ? st.call.oi : 0) + (st.put && isNum(st.put.oi) ? st.put.oi : 0);
          if (oi > 0) byStrike[st.strike] = (byStrike[st.strike] || 0) + oi;
        });
      });
      var levels = Object.keys(byStrike).map(function (k) { return { name: "Strike " + k, price: Number(k), size: byStrike[k] }; });
      levels.sort(function (a, b) { return b.size - a.size; });
      levels = levels.slice(0, 16);
      if (!levels.length) return null;
      return VisualKit.ladder({ levels: levels, current: snap.spot, session: s, title: "Where the open contracts sit, by strike",
        label: "Open interest summed at each strike in the freshest snapshot on record, biggest 16 strikes drawn. The marker is the price the snapshot was taken at." });
    },
    "correlation-web": function (d, s) {
      var syms = d.symbols || [], rets = d.returns_bp || [];
      var items = [];
      for (var i = 0; i < Math.min(24, syms.length, rets.length); i++) {
        var r = rets[i];
        if (Array.isArray(r) && r.length && isNum(r[r.length - 1])) items.push({ label: syms[i], value: r[r.length - 1] / 100 });
      }
      return tiles(items, s, "The latest session, name by name", "Each tile is one name's move in the latest session on record, in percent. Colour follows the move.");
    },
    "dark-prints": function (d, s) {
      return tiles((d.funds || []).map(function (f) { return { label: f.symbol, value: f.pct }; }),
        s, "The dark share, by index fund", "The share of trading that happened away from the public exchanges, for each fund on record, in percent.");
    },
    "decay-watch": function (d, s) {
      var c = d.current_counts || {};
      return ranked([{ name: "Promoted", score: c.promoted }, { name: "On probation", score: c.probation }, { name: "All entries", score: c.total }],
        s, "The book right now, in counts", "Entries on the promoted book by their current standing, from this page's own counts.");
    },
    "earnings-calendar": function (d, s) {
      var days = groupCounts(d.names || [], function (n) { return n.date; })
        .map(function (r) { return { date: r.name, count: r.score }; })
        .sort(function (a, b) { return a.date < b.date ? -1 : 1; });
      if (!days.length) return null;
      return VisualKit.accrual({ mode: "calendar", days: days, session: s, title: "Reporting days ahead, at a glance",
        label: "One cell per reporting day on record. Darker means more names report that day." });
    },
    "earnings-drift": function (d, s) {
      var total = Number(d.events), notPos = Number(d.not_positive);
      if (!isFinite(total) || !isFinite(notPos) || total <= 0) return null;
      return ranked([{ name: "Rose after reporting", score: total - notPos }, { name: "Did not rise after reporting", score: notPos }],
        s, "What happened after the reports on record", "Across the " + total + " earnings events on record for the three names this page follows.");
    },
    "echo-lens": function (d, s) {
      return ranked(groupCounts(d.readings || [], function (r) { return r.verdict; }).slice(0, 10),
        s, "How the lens called the names on record", "Names on record grouped by the reading this lens gave them, counted from the same readings listed below.");
    },
    "expected-move": function (d, s) {
      var items = (d.names || []).filter(function (n) { return n.session_band; }).map(function (n) {
        return { label: n.symbol || n.name, low: n.session_band.lower, high: n.session_band.upper, current: n.close };
      });
      if (!items.length) return null;
      return VisualKit.band({ items: items, session: s, title: "The expected range for one session", label: "The range each name was expected to stay inside for a session, with its closing price marked." });
    },
    "expiry-pin-watch": function (d, s) {
      var n0 = (d.names || [])[0];
      if (!n0) return null;
      return ranked((n0.expiries || []).map(function (e) {
        return { name: (n0.symbol || "") + " expiring " + e.expiry, score: e.total_oi };
      }), s, "Open contracts by expiry", "Open interest for the first name on record, by the expiry dates this page lists.");
    },
    "fear-day": function (d, s) {
      return ranked((d.qualifying_days || []).map(function (q) {
        return { name: q.date, score: q.fear_gauge_change_pct, coverage: "fear gauge closed at " + q.fear_gauge_close };
      }), s, "Fear days on record", "The rise in the fear gauge on each qualifying day on record, in percent. The full list is short because qualifying days are rare.");
    },
    "fear-day-forecaster": function (d, s) {
      var loc = d.local_record || {};
      return ranked([{ name: "Fear gauge readings on record", score: loc.fear_gauge_readings },
        { name: "Sessions checked", score: loc.sessions_checked }, { name: "Qualifying fear days", score: loc.events }],
        s, "The record this forecast rests on", "What the local record holds so far. No forecast is graded yet, and this picture shows the build up, not a result.");
    },
    "filings-wire": function (d, s) {
      var c0 = (d.companies || [])[0];
      if (!c0 || !c0.figures || !c0.figures.length) return null;
      var f = c0.figures[0];
      var series = (f.readings || []).filter(function (r) { return isNum(r.value); })
        .map(function (r) { return { date: r.period_end || r.filed || "", value: r.value }; });
      if (series.length < 2) return null;
      return VisualKit.line({ series: series, session: s, title: (c0.symbol || c0.company_name) + ": " + f.label + " on record",
        label: "The yearly " + String(f.label).toLowerCase() + " figures this company filed, in the order of the years they cover." });
    },
    "flow-board": function (d, s) {
      return ranked((d.sessions || []).map(function (x) {
        return { name: x.session, score: x.total_premium_usd };
      }), s, "Money that changed hands, by session", "Total premium in each session on record, from the same sessions this board is built from.");
    },
    "flow-engine": function (d, s) {
      return hourStrip(d.examples || [], s, "Example alerts by hour", "The worked examples on this page, counted by the hour they landed.");
    },
    "flow-tape": function (d, s) {
      var all = [];
      (d.groups || []).forEach(function (g) { (g.alerts || []).forEach(function (a) { all.push(a); }); });
      return hourStrip(all, s, "Alerts by hour of the day", "How many of the alerts on record landed in each hour, counted from the same alerts listed below.");
    },
    "gap-fill": function (d, s) {
      return ranked((d.by_weekday || []).map(function (b) {
        return { name: b.label, score: isNum(b.frequency) ? Math.round(b.frequency * 1000) / 10 : null, coverage: "of " + b.n + " gaps" };
      }), s, "How often gaps filled, by weekday", "The share of overnight gaps that filled on the day, in percent, for each weekday on record.");
    },
    "golden-sweep-wire": function (d, s) {
      return ranked((d.sessions || []).map(function (x) {
        return { name: x.session, score: x.prints_looked_at, coverage: (x.golden_prints || 0) + " golden prints" };
      }), s, "Prints examined, by session", "How many prints were examined in each session on record, with the golden prints found printed beside each bar.");
    },
    "grade-a-board": function (d, s) {
      var v = (d.first_search && d.first_search.verdicts) || [];
      return ranked(v.map(function (p) { return { name: p[0], score: p[1] }; }).slice(0, 9),
        s, "How the first search came out", "Recipes in the first finished search, grouped by the verdict they earned.");
    },
    "grade-my-call": function (d, s) {
      return closesLine(d, s, "The S and P 500 fund, closing prices on record", "The closing price history this page grades calls from, session by session.");
    },
    "graveyard": function (d, s) {
      var events = (d.buried || []).filter(function (b) { return b.when; })
        .map(function (b) { return { date: b.when, label: b.maker || b.study || "Buried claim" }; });
      if (!events.length) return null;
      return VisualKit.accrual({ mode: "timeline", events: events, session: s, title: "Buried claims, in order",
        label: "One marker per buried claim on record, in the order this page lists them." });
    },
    "holly-ideas": function (d, s) {
      return ranked((d.ideas || []).slice(0, 12).map(function (i) {
        return { name: i.symbol, score: i.score, coverage: (i.checks_in_favor || 0) + " of " + (i.checks_total || 0) + " checks in favour" };
      }), s, "The ideas, scored", "Each idea on record with its score, and how many of its checks came out in its favour.");
    },
    "horizon-grades": function (d, s) {
      return ranked((d.horizons || []).map(function (h) {
        return { name: h.days + " day grade", score: h.graded_count, coverage: h.state === "graded" ? (h.rose_count + " rose, " + h.did_not_rise_count + " did not") : "not yet graded" };
      }), s, "Grades on record, by waiting time", "How many calls have been graded at each waiting time. The 5 day and 21 day rows are still waiting for their first grades.");
    },
    "insider-wire": function (d, s) {
      return tiles((d.names || []).filter(function (n) { return n.summary && isNum(n.summary.reading_out_of_100); }).slice(0, 24)
        .map(function (n) { return { label: n.symbol, value: n.summary.reading_out_of_100 }; }),
        s, "Insider readings, name by name", "Each tile is one name's insider reading out of 100, from the filings on record. Higher means heavier buying by the people inside the company.");
    },
    "iv-weather": function (d, s) {
      var items = [];
      (d.groups || []).forEach(function (g) { (g.names || []).forEach(function (n) { items.push({ label: n.symbol, value: n.iv_percent }); }); });
      return tiles(items.slice(0, 24), s, "Volatility weather, name by name", "Each tile is one name's current volatility reading, in percent, from the readings on record.");
    },
    "momentum-clock": function (d, s) {
      return windowChange(d, s, "Biggest rises over the last 21 sessions", "Each name's last close against its close 21 sessions earlier, in percent. This is the shortest window this page itself offers.", 21);
    },
    "morning-map": function (d, s) {
      var idx = (d.indexes || [])[0];
      if (!idx) return null;
      function val(o) { return o && isNum(o.value) ? o.value : null; }
      var levels = [
        { name: (idx.symbol || "") + " call wall", price: val(idx.call_wall) },
        { name: (idx.symbol || "") + " flip level", price: val(idx.flip) },
        { name: (idx.symbol || "") + " put wall", price: val(idx.put_wall) }
      ].filter(function (l) { return isNum(l.price); });
      if (!levels.length) return null;
      return VisualKit.ladder({ levels: levels, current: idx.spot, session: s, title: "Where the price sits among the levels",
        label: "The call wall, the flip level and the put wall for the first index on the map, with its price marked in place. Sizes are not published on this page, so no bars are drawn." });
    },
    "odds-cards": function (d, s) {
      return ranked((d.families || []).map(function (f) {
        return { name: f.name, score: isNum(f.rate) ? Math.round(f.rate * 1000) / 10 : null, coverage: "from " + f.n + " cases" };
      }), s, "How often each family paid off", "The share of cases that reached the target, in percent, for each family on record.");
    },
    "one-page-report": function (d, s) {
      var cov = d.coverage_distribution || {};
      var rows = Object.keys(cov).map(function (k) { return { name: "Names with " + k + " of 9 sections covered", score: cov[k] }; });
      rows.sort(function (a, b) { return b.score - a.score; });
      return ranked(rows, s, "How complete the reports are", "Names on record grouped by how many of the nine report sections carry a reading for them.");
    },
    "portfolio-builder": function (d, s) {
      return ranked((d.members || []).slice(0, 14).map(function (m) {
        return { name: m.symbol, score: m.weight_pct, coverage: m.sector || "" };
      }), s, "What the portfolio holds, by weight", "Each member's share of the portfolio, in percent, biggest first.");
    },
    "promoted-book": function (d, s) {
      var rows = [];
      (d.standings || []).forEach(function (st) { (st.groups || []).forEach(function (g) { rows.push({ name: g.title, score: g.count }); }); });
      rows.sort(function (a, b) { return b.score - a.score; });
      return ranked(rows.slice(0, 12), s, "Entries on the book, by group", "How many entries sit in each group on the promoted book.");
    },
    "proving-ground": function (d, s) {
      return ranked(groupCounts(d.tools || [], function (t) { return t.state_words || t.state; }).slice(0, 10),
        s, "Tools by their proving state", "The tools on record grouped by the state this page gives them.");
    },
    "pullback-norm": function (d, s) {
      var res = (d.research_record && d.research_record.results) || [];
      return ranked(res.map(function (r) { return { name: r.era + ", " + r.window_sessions + " sessions", score: r.strength }; }),
        s, "The study results behind this page", "The strength found in each finished study run on record. No live signals are published yet, so this picture is the study record, not a live reading.");
    },
    "receipts": function (d, s) {
      var events = (d.receipts || []).map(function (r) {
        return { date: r.session || (r.made_at ? String(r.made_at).slice(0, 10) : null), label: r.tool || r.slug };
      }).filter(function (e) { return e.date; });
      if (!events.length) return null;
      return VisualKit.accrual({ mode: "timeline", events: events, session: s, title: "Receipts on file, by the session they cover",
        label: "One marker per receipt that carries a session date. Receipts without a session date on record are listed below and are not placed on this line." });
    },
    "regime-dial": function (d, s) {
      return ranked((d.checks || []).map(function (c) {
        return { name: c.name, score: isNum(c.value) ? c.value : null, coverage: isNum(c.value) ? "" : String(c.value || "") };
      }), s, "The checks behind the reading", "The numeric checks this page counts. The reading itself is printed above: the checks do not line up behind one kind of market right now.");
    },
    "replication-wire": function (d, s) {
      return ranked(groupCounts(d.claims || [], function (c) { return c.verdict_words || c.verdict; }).slice(0, 10),
        s, "Claims by their verdict", "The claims on this wire grouped by the verdict the recheck gave them.");
    },
    "reversal-wire": function (d, s) {
      var entries = ((d.sessions || [])[0] || {}).entries || [];
      return ranked(groupCounts(entries, function (e) { return e.label || e.kind; }).slice(0, 10),
        s, "Labels in the latest session on record", "Names in the session this wire carries, grouped by the label the scanner gave them.");
    },
    "router": function (d, s) {
      var rec = (d.session_record || [])[0] || {};
      return ranked([{ name: "Names checked", score: rec.checked }, { name: "No call", score: rec.no_call }, { name: "Avoid", score: rec.avoid }],
        s, "The latest session, in counts", "What the router did with the names it checked in the latest session on record.");
    },
    "sector-rotation": function (d, s) {
      return tiles((d.sectors || []).map(function (x) { return { label: x.sector, value: x.avg_change_5_pct, word: x.label || "" }; }),
        s, "Sectors over the last 5 sessions", "Each tile is one sector's average move over the last 5 sessions on record, in percent.");
    },
    "short-volume": function (d, s) {
      var t0 = (d.tickers || [])[0];
      if (!t0 || !Array.isArray(t0.days)) return null;
      var series = t0.days.filter(function (x) { return isNum(x.short_share_pct); })
        .map(function (x) { return { date: x.date, value: x.short_share_pct }; });
      if (series.length < 2) return null;
      return VisualKit.line({ series: series, session: s, title: (t0.symbol || "First name") + ": share of trading sold short, by day",
        label: "The daily share of this name's trading that was sold short, in percent, over the days this page shows." });
    },
    "signal-feed": function (d, s) {
      return ranked(groupCounts(d.entries || [], function (e) { return e.kind_words; }).slice(0, 10),
        s, "Entries by kind", "The newest entries on this feed grouped by kind, counted from the same entries listed below.");
    },
    "skew-lens": function (d, s) {
      function usable(f) { return f && isNum(f.put_percent) && isNum(f.call_percent) && isNum(f.put_strike) && isNum(f.call_strike); }
      var modelled = (d.modelled_figures || []).filter(usable);
      var recorded = (d.figures || []).filter(usable);
      var isModelled = modelled.length > 0;
      var figs = isModelled ? modelled : recorded;
      if (!figs.length) return null;
      var freshest = figs.map(function (f) { return f.date || ""; }).sort().pop();
      figs = figs.filter(function (f) { return (f.date || "") === freshest; });
      var pts = [];
      figs.forEach(function (f) {
        pts.push({ x: (f.symbol || "") + " put strike " + f.put_strike, y: f.put_percent, modelled: isModelled });
        pts.push({ x: (f.symbol || "") + " call strike " + f.call_strike, y: f.call_percent, modelled: isModelled });
      });
      if (pts.length < 2) return null;
      var f0 = figs[0];
      var label = "For " + (f0.symbol || "the freshest name") + " on " + (f0.date || freshest) +
        ", the line joins the put reading at the strike below the price to the call reading at the strike above it. " +
        (f0.sentence || "") + "." +
        (isModelled ? " Modelled figures, drawn dashed, kept separate from the recorded ledger on this page." : " Recorded figures.");
      return VisualKit.curve({ points: pts, session: freshest || s, title: "The skew shape, " + (f0.symbol || "") + ", " + (f0.date || ""),
        label: label });
    },
    "smart-money-tracker": function (d, s) {
      return ranked((d.holders || []).slice(0, 12).map(function (h) {
        return { name: h.holder, score: h.total_value, coverage: (h.positions_count || 0) + " positions" };
      }), s, "The biggest holders being tracked", "Total value of the holdings each tracked holder reported, biggest first.");
    },
    "squeeze-watch": function (d, s) {
      return tiles((d.names || []).slice(0, 20).map(function (n) { return { label: n.symbol, value: n.si_pct_of_float }; }),
        s, "Borrowed shares, name by name", "Each tile is one name's borrowed shares as a percent of the shares available to trade, from the latest settlement on record.");
    },
    "state-analogue": function (d, s) {
      var c = d.counts || {};
      if (!isNum(c.sessions_recorded) || !isNum(c.sessions_needed)) return null;
      return VisualKit.accrual({ have: c.sessions_recorded, need: c.sessions_needed, unit: "sessions", session: s,
        title: "Sessions on record against the history it needs",
        label: c.sessions_recorded + " session of state readings is on record. This page needs " + c.sessions_needed + " before a past match can be trusted, so the build up is the honest picture today." });
    },
    "static-gex": function (d, s) {
      var f = (d.funds || [])[0];
      if (!f || !Array.isArray(f.strongest)) return null;
      return ranked(f.strongest.map(function (x) { return { name: "Strike " + x.strike, score: x.net_gex }; }),
        s, "Strongest strikes for " + (f.underlying || "the first fund"), "Net dealer positioning at each of the strongest strikes in the freshest snapshot, with the price at " + f.spot + ".");
    },
    "strat-combos": function (d, s) {
      return ranked((d.groups || []).slice(0, 12).map(function (g) { return { name: g.name, score: g.count }; }),
        s, "The biggest pattern groups", "Names carrying each completed pattern combination, biggest groups first.");
    },
    "strat-scanner": function (d, s) {
      return ranked((d.groups || []).map(function (g) { return { name: g.name || g.label, score: g.count }; }),
        s, "Names by pattern group", "How many names the scanner placed in each pattern group on record.");
    },
    "survivors-wire": function (d, s) {
      return ranked((d.per_record || []).map(function (r) {
        return { name: r.name, score: r.tested, coverage: (r.standing || 0) + " standing, " + (r.partly || 0) + " partly" };
      }), s, "Claims tested, by record", "How many claims from each record were tested, and how they stand.");
    },
    "unusual-volume": function (d, s) {
      return tiles((d.names || []).slice(0, 24).map(function (n) { return { label: n.symbol, value: n.multiple }; }),
        s, "Trading volume against the usual", "Each tile is one name's trading volume as a multiple of its usual volume. Every name here traded at least twice its usual.");
    },
    "wall-check": function (d, s) {
      var w = (d.waiting || [])[0];
      if (!w) return null;
      var levels = [
        { name: (w.name || "") + " call wall", price: w.call_wall },
        { name: (w.name || "") + " flip level", price: w.flip },
        { name: (w.name || "") + " put wall", price: w.put_wall }
      ].filter(function (l) { return isNum(l.price); });
      if (!levels.length) return null;
      return VisualKit.ladder({ levels: levels, current: w.spot, session: s, title: "The next card waiting to be graded",
        label: "The levels on the freshest ungraded card on record, with its price marked in place. Sizes are not published on this page, so no bars are drawn." });
    },
    "week-ahead": function (d, s) {
      var days = groupCounts(d.events || [], function (e) { return e.date; })
        .map(function (r) { return { date: r.name, count: r.score }; })
        .sort(function (a, b) { return a.date < b.date ? -1 : 1; }).slice(0, 35);
      if (!days.length) return null;
      return VisualKit.accrual({ mode: "calendar", days: days, session: s, title: "Events on record, day by day",
        label: "One cell per day that carries an event on record. Darker means more events that day." });
    },
    "watchlist-pulse": function (d, s) {
      return tiles((d.names || []).slice(0, 24).map(function (n) { return { label: n.symbol, value: n.families_speaking }; }),
        s, "How many voices speak on each name", "Each tile counts how many of the six reading families carry a reading for that name, from the record below.");
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    var host = document.getElementById("vkHost");
    if (!host || typeof VisualKit === "undefined") return;
    var parts = window.location.pathname.split("/").filter(Boolean);
    var si = parts.lastIndexOf("site"); if (si >= 0) parts = parts.slice(si + 1);
    if (parts.length && parts[parts.length - 1] === "index.html") parts.pop();
    var slug = parts[parts.length - 1] || "";
    fetch("data.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      if (!d) return;
      var session = VisualKit.sessionOf(d);
      var html = null;
      try { html = ADAPTERS[slug] ? ADAPTERS[slug](d, session) : null; } catch (e) { html = null; }
      if (!html) {
        html = VisualKit.accrual({ session: session, words: "Not enough of this page's own data is in the shape a picture needs yet. The full record is in the detail below." });
      }
      host.innerHTML = html;
    }).catch(function () { /* The page's own content stays as it is. */ });
  });
})();
