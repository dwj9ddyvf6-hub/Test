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
  function grid(rows, s, title, label) {
    rows = (rows || []).filter(function (r) { return r && r.name != null && r.name !== ""; });
    if (!rows.length) return null;
    return VisualKit.ranked({ rows: rows, session: s, title: title, label: label });
  }
  function tapeOf(events, s, title, label) {
    events = (events || []).filter(function (e) { return e && (e.label || e.desc); });
    if (!events.length) return null;
    return VisualKit.tape({ events: events, session: s, title: title, label: label });
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
      var rows = (d.alerts || []).filter(function (a) { return isNum(a.premium_usd); }).map(function (a) {
        return { name: (a.underlying || "") + " " + (a.contract_code || ""), score: a.premium_usd, coverage: (a.direction || "") + ", heat " + a.heat_score };
      }).sort(function (a, b) { return b.score - a.score; }).slice(0, 12);
      return ranked(rows, s, "The biggest alerts on record, by premium", "Each alert on record with the premium it carried, biggest first. Colour words beside each bar say which way it pointed.");
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
      var mv = (d.movements || []).map(function (m) {
        return { name: (m.name || m.symbol || m.title || "Entry"), status: (m.from || "?") + " to " + (m.to || "?"), coverage: m.date || m.session || "" };
      });
      if (mv.length) return grid(mv.slice(0, 14), s, "How entries moved at the last grading", "Each movement on record, from its old standing to its new one.");
      var g = ((d.gradings || [])[((d.gradings || []).length - 1)] || {});
      if (!isNum(g.total) || !g.total) return null;
      return tiles([{ label: "Promoted at the last grading", value: Math.round(100 * g.promoted / g.total * 10) / 10 },
        { label: "On probation at the last grading", value: Math.round(100 * g.probation / g.total * 10) / 10 }],
        s, "The book's standing at its only grading", "The share of the book standing promoted and on probation at the grading on record (" + (g.date || "") + "), in percent. The book has been graded once, so no movement between standings is on record yet.");
    },
    "earnings-calendar": function (d, s) {
      var rows = [];
      (d.names || []).forEach(function (n) {
        var em = n.expected_move;
        if (typeof em === "string" && em.charAt(em.length - 1) === "%") {
          var v = parseFloat(em);
          if (isFinite(v)) rows.push({ name: (n.symbol || "") + " " + (n.date || ""), score: v });
        }
      });
      rows.sort(function (a, b) { return b.score - a.score; });
      if (rows.length >= 2) return ranked(rows.slice(0, 12), s, "The biggest expected moves ahead", "The expected move priced for each reporting name on record, in percent, biggest first. Every name and its day are listed below.");
      var ev = (d.names || []).slice(0, 20).map(function (n) { return { label: n.symbol, desc: "reports " + (n.date || ""), time: n.date || "" }; });
      return tapeOf(ev, s, "Who reports, and when", "The reporting names on record placed on their own dates.");
    },
    "earnings-drift": function (d, s) {
      var rows = (d.event_rows || []).filter(function (r) { return isNum(r.drift_pct); }).map(function (r) {
        return { name: (r.symbol || "") + " " + (r.report_date || ""), score: r.drift_pct };
      });
      rows.sort(function (a, b) { return b.score - a.score; });
      if (rows.length >= 2) return ranked(rows.slice(0, 14), s, "Each report, and what the name did on it", "Every earnings event in the study, named and dated, with its own post-report move in percent. Across all " + (d.events || rows.length) + " events the average move was " + (isNum(d.mean) ? Math.round(d.mean * 10000) / 100 : "?") + " percent, the middle move " + (isNum(d.median) ? Math.round(d.median * 10000) / 100 : "?") + " percent, and the share of reports that rose (share_positive) was " + (isNum(d.share_positive) ? Math.round(d.share_positive * 1000) / 10 : "?") + " percent.");
      var items = [];
      if (isNum(d.mean)) items.push({ label: "Average move after reporting", value: Math.round(d.mean * 10000) / 100 });
      if (isNum(d.median)) items.push({ label: "Middle move after reporting", value: Math.round(d.median * 10000) / 100 });
      if (isNum(d.share_positive)) items.push({ label: "Share of reports that rose", value: Math.round(d.share_positive * 1000) / 10 });
      return tiles(items, s, "What the names did after reporting", "Across the " + (d.events || "") + " earnings events on record for the three names this page follows: the average and middle post-report move, and the share that rose, in percent.");
    },
    "echo-lens": function (d, s) {
      var rows = (d.readings || []).slice(0, 24).map(function (r) {
        return { name: r.symbol, status: r.verdict, coverage: String(r.words || "").slice(0, 90) };
      });
      return grid(rows, s, "The lens's readings, name by name", "Each name on record with the verdict this lens gave it. The full readings are listed below.");
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
      var res = ((d.study || {}).results || []).map(function (r) {
        return { name: r.era + ", " + r.window_sessions + " sessions", score: r.strength, coverage: "rank correlation " + r.rank_correlation };
      });
      if (res.length) return ranked(res, s, "The study result this forecast rests on", "The strength found in each finished study run on record, by era and window. The local fear days are charted under The record.");
      var loc = d.local_record || {};
      var rows = (loc.qualifying_days || []).map(function (q) {
        return { name: q.date, score: q.fear_gauge_change_pct, coverage: "SPY " + q.spy_change_pct + "% that day" };
      });
      return ranked(rows, s, "Fear days in the local record", "The rise in the fear gauge on each qualifying day in the local record, in percent.");
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
      var rows = (d.examples || []).filter(function (e) { return isNum(e.premium_usd); }).map(function (e) {
        return { name: (e.underlying || "") + " " + (e.contract_code || ""), score: e.premium_usd, coverage: (e.direction || "") + ", heat " + e.heat_score };
      }).sort(function (a, b) { return b.score - a.score; }).slice(0, 12);
      return ranked(rows, s, "The worked examples, by premium", "Each worked example on this page with the premium it carried, biggest first. These are the rule's own worked examples, shown as themselves.");
    },
    "flow-tape": function (d, s) {
      var all = [];
      (d.groups || []).forEach(function (g) { (g.alerts || []).forEach(function (a) { all.push(a); }); });
      var rows = all.filter(function (a) { return isNum(a.premium_usd); }).map(function (a) {
        return { name: (a.underlying || "") + " " + (a.contract_code || ""), score: a.premium_usd, coverage: (a.direction || "") + ", heat " + a.heat_score };
      }).sort(function (a, b) { return b.score - a.score; }).slice(0, 12);
      return ranked(rows, s, "The biggest prints on the tape, by premium", "Each alert on the tape with the premium it carried, biggest first.");
    },
    "gap-fill": function (d, s) {
      return ranked((d.by_weekday || []).map(function (b) {
        return { name: b.label, score: isNum(b.frequency) ? Math.round(b.frequency * 1000) / 10 : null, coverage: "of " + b.n + " gaps" };
      }), s, "How often gaps filled, by weekday", "The share of overnight gaps that filled on the day, in percent, for each weekday on record.");
    },
    "golden-sweep-wire": function (d, s) {
      var rows = (d.prints || []).filter(function (x) { return isNum(x.premium_usd); }).map(function (x) {
        return { name: x.contract_code || "Golden print", score: x.premium_usd, coverage: (x.direction || "") + ", heat " + x.heat_score + ", " + x.contracts + " contracts" };
      }).sort(function (a, b) { return b.score - a.score; }).slice(0, 12);
      if (rows.length) return ranked(rows, s, "The golden prints themselves, by premium", "Each golden print on record with the premium it carried, biggest first.");
      return ranked((d.sessions || []).map(function (x) {
        return { name: x.session, score: x.golden_prints, coverage: "golden prints found this session" };
      }), s, "Golden prints found, by session", "Golden prints found in each session on record. Sessions are charted only because no golden print itself is on record yet.");
    },
    "grade-a-board": function (d, s) {
      var rows = [];
      (d.groups || []).forEach(function (g) {
        var c = (g.cells || [])[0];
        if (c && isNum(c.net_second)) rows.push({ name: String(g.title || "").slice(0, 44), score: c.net_second, coverage: "held " + c.hold_second + " on the second look" });
      });
      return ranked(rows.slice(0, 12), s, "The recipes' own graded numbers", "Each graded recipe group on the board with the net figure it earned on the second search, from the cells on this page.");
    },
    "grade-my-call": function (d, s) {
      return closesLine(d, s, "The S and P 500 fund, closing prices on record", "The closing price history this page grades calls from, session by session.");
    },
    "graveyard": function (d, s) {
      var rows = (d.buried || []).slice(0, 12).map(function (b) {
        return { name: String(b.maker || "Buried claim").slice(0, 44), status: b.verdict_words, coverage: String(b.result || "").slice(0, 90) };
      });
      return grid(rows, s, "Buried claims and what the record showed", "Each buried claim on record with the verdict its recheck earned. The claims themselves are listed in full below.");
    },
    "holly-ideas": function (d, s) {
      return ranked((d.ideas || []).slice(0, 12).map(function (i) {
        return { name: i.symbol, score: i.score, coverage: (i.checks_in_favor || 0) + " of " + (i.checks_total || 0) + " checks in favour" };
      }), s, "The ideas, scored", "Each idea on record with its score, and how many of its checks came out in its favour.");
    },
    "horizon-grades": function (d, s) {
      var rows = (d.horizons || []).filter(function (h) { return isNum(h.average_pct); }).map(function (h) {
        return { name: h.days + " day grade", score: h.average_pct, coverage: (h.rose_count + " rose, " + h.did_not_rise_count + " did not, of " + h.graded_count + " graded") };
      });
      return ranked(rows, s, "What graded calls did, by waiting time", "The average move of the calls graded at each waiting time, in percent, with the rose and did-not split beside each bar.");
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
      var nm = d.default_name, rec = ((d.names || {})[nm]) || {};
      var items = [];
      if (rec.scored && isNum(rec.scored.score)) items.push({ label: nm + " board score, out of 100", value: rec.scored.score });
      if (rec.chart && isNum(rec.chart.last_close)) items.push({ label: nm + " last close", value: rec.chart.last_close });
      if (rec.volume && isNum(rec.volume.multiple)) items.push({ label: nm + " volume against its usual", value: rec.volume.multiple });
      if (rec.families && isNum(rec.families.families_speaking)) items.push({ label: "Families speaking on " + nm, value: rec.families.families_speaking });
      return tiles(items, s, "The default name's own readings: " + nm, "The readings this page carries for its default name, one tile per reading, from the name's own sections below.");
    },
    "portfolio-builder": function (d, s) {
      return ranked((d.members || []).slice(0, 14).map(function (m) {
        return { name: m.symbol, score: m.weight_pct, coverage: m.sector || "" };
      }), s, "What the portfolio holds, by weight", "Each member's share of the portfolio, in percent, biggest first.");
    },
    "promoted-book": function (d, s) {
      var rows = [];
      (d.standings || []).forEach(function (st) { (st.groups || []).forEach(function (g) {
        (g.entries || []).forEach(function (e) {
          var w = (e.windows || [])[0];
          if (w && isNum(w.gap_points)) rows.push({ name: "Grade " + e.grade + " entry, " + e.days_ahead + " days ahead", score: w.gap_points, coverage: String(e.where || "").slice(0, 60) });
        });
      }); });
      rows.sort(function (a, b) { return Math.abs(b.score) - Math.abs(a.score); });
      return ranked(rows.slice(0, 12), s, "Book entries by their own graded gap", "Each promoted entry's graded gap in points from its first recorded window, biggest first.");
    },
    "proving-ground": function (d, s) {
      var rows = (d.tools || []).slice(0, 24).map(function (t) {
        return { name: t.name, status: t.state_words || t.state, coverage: String(t.reason || "").slice(0, 90) };
      });
      return grid(rows, s, "Every tool, with its own proving state", "The grid is the subject: each tool on record with the state this page gives it and why.");
    },
    "pullback-norm": function (d, s) {
      var res = (d.research_record && d.research_record.results) || [];
      return ranked(res.map(function (r) { return { name: r.era + ", " + r.window_sessions + " sessions", score: r.strength }; }),
        s, "The study results behind this page", "The strength found in each finished study run on record. No live signals are published yet, so this picture is the study record, not a live reading.");
    },
    "receipts": function (d, s) {
      var rows = (d.receipts || []).slice(0, 24).map(function (r) {
        return { name: r.tool || r.slug, status: r.grade, coverage: String(r.completeness || "").slice(0, 80) };
      });
      return grid(rows, s, "The receipts, tool by tool", "Each tool's receipt on file with its grade. This page's subject is the site's own bookkeeping, drawn as a grid, never as a tally.");
    },
    "regime-dial": function (d, s) {
      return ranked((d.checks || []).map(function (c) {
        return { name: c.name, score: isNum(c.value) ? c.value : null, coverage: isNum(c.value) ? "" : String(c.value || "") };
      }), s, "The checks behind the reading", "The numeric checks this page counts. The reading itself is printed above: the checks do not line up behind one kind of market right now.");
    },
    "replication-wire": function (d, s) {
      var rows = (d.claims || []).slice(0, 16).map(function (c) {
        return { name: String(c.maker || "Claim").slice(0, 44), status: c.verdict_words, coverage: String(c.result || "").slice(0, 90) };
      });
      return grid(rows, s, "Claims and what the recheck showed", "Each claim on the wire with the verdict its recheck earned, claim by claim.");
    },
    "reversal-wire": function (d, s) {
      var entries = ((d.sessions || [])[0] || {}).entries || [];
      var rows = entries.slice(0, 24).map(function (e) { return { name: e.symbol, status: e.label || e.kind }; });
      return grid(rows, s, "Names and their labels, latest session", "Names in the freshest session on record with the pattern label the scanner gave each one. The full session is listed below.");
    },
    "router": function (d, s) {
      var rec = (d.session_record || [])[0] || {};
      var rows = (rec.avoid_names || []).map(function (a) {
        return { name: a.name, status: "Avoid", coverage: String(a.why || "").slice(0, 110) };
      });
      return grid(rows, s, "The names the router said to avoid, and why", "The per-name verdicts in the latest session on record, with the reason for each. Every other name in that session drew no call or an abstention, as the page states.");
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
      var ev = (d.entries || []).slice(0, 20).map(function (e) {
        return { label: e.name, desc: String(e.detail || "").slice(0, 120), time: e.session || "", tags: [e.grading_words || e.kind_words || ""] };
      });
      return tapeOf(ev, s, "The feed itself, newest entries first", "The newest entries on this feed, each with what it said and its grading state.");
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
      var vals = ((d.today || {}).values) || [];
      var items = (d.readings || []).map(function (r, i) {
        return { label: r.name, value: i < vals.length ? vals[i] : null };
      }).filter(function (it) { return isNum(it.value); });
      if (!items.length) return null;
      return tiles(items, s, "Today's five market readings", "The five readings that describe today, each with its own value on record. Past matches appear once enough sessions have built up, as the page states.");
    },
    "static-gex": function (d, s) {
      var f = (d.funds || [])[0];
      if (!f || !Array.isArray(f.strongest)) return null;
      return ranked(f.strongest.map(function (x) { return { name: "Strike " + x.strike, score: x.net_gex }; }),
        s, "Strongest strikes for " + (f.underlying || "the first fund"), "Net dealer positioning at each of the strongest strikes in the freshest snapshot, with the price at " + f.spot + ".");
    },
    "strat-combos": function (d, s) {
      var gs = (d.groups || []).slice().sort(function (a, b) { return (b.count || 0) - (a.count || 0); });
      var g = gs[0];
      if (!g || !g.names || !g.names.length) return null;
      var rows = g.names.slice(0, 24).map(function (sym) { return { name: sym, status: g.name }; });
      return grid(rows, s, "Names carrying: " + g.name, "The names in the largest completed pattern combination on record, each labelled with the combination it completed. Every combination is listed below.");
    },
    "strat-scanner": function (d, s) {
      var rows = [];
      (d.groups || []).forEach(function (g) {
        (g.names || []).slice(0, 6).forEach(function (n) {
          if (n && n.symbol) rows.push({ name: n.symbol, status: n.label || g.name });
        });
      });
      return grid(rows.slice(0, 24), s, "Names and the pattern each one showed", "Names on record with the bar pattern label the scanner gave each one. Every group is listed below.");
    },
    "survivors-wire": function (d, s) {
      var items = [];
      (d.per_record || []).forEach(function (r) {
        if (!r.tested) return;
        items.push({ label: String(r.name || "").slice(0, 40) + ": standing", value: Math.round(100 * r.standing / r.tested * 10) / 10 });
        items.push({ label: String(r.name || "").slice(0, 40) + ": partly standing", value: Math.round(100 * r.partly / r.tested * 10) / 10 });
      });
      return tiles(items, s, "How the tested claims stand, by record", "Of the claims tested from each record on file, the share standing and partly standing, in percent. The claims themselves are listed below.");
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
      var ev = (d.events || []).slice(0, 20).map(function (e) {
        return { label: e.name, desc: (e.date || "") + " " + (e.time_label || "") + ", " + (e.kind || ""), time: e.date || "" };
      });
      return tapeOf(ev, s, "The events themselves, on their dates", "The macro events on record, each placed on its own date with its time.");
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
