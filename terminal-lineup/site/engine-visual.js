/* Engine visual binding (build stream 3). Uses the shared VisualKit
   primitives in visual.js; this file only maps each forecast engine
   page's own data.json fields onto a primitive. It reads no other
   page's data, invents no figure, and fails closed to the kit's plain
   state visual when the named fields are absent. Loaded after
   visual.js on engine pages plus the Board and the Record. */
(function () {
  "use strict";
  function plain(key) {
    var s = String(key).replace(/_/g, " ");
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function isCount(v) { return typeof v === "number" && isFinite(v) && v >= 0 && Math.floor(v) === v; }
  function liveCounts(d) {
    var live = (d && typeof d.live === "object" && d.live) || {};
    var rows = [];
    Object.keys(live).forEach(function (k) {
      var v = live[k];
      if (isCount(v)) rows.push({ name: plain(k), score: v });
      else if (v && typeof v === "object" && !Array.isArray(v)) {
        Object.keys(v).forEach(function (k2) {
          if (isCount(v[k2])) rows.push({ name: plain(k) + ": " + plain(k2).toLowerCase(), score: v[k2] });
        });
      }
    });
    rows.sort(function (a, b) { return b.score - a.score; });
    return rows;
  }
  function targetPair(d) {
    var live = (d && d.live) || {};
    var needKey = Object.keys(live).filter(function (k) { return /target/.test(k) && isCount(live[k]) && live[k] > 0; })[0];
    if (!needKey) return null;
    var haveKey = Object.keys(live).filter(function (k) {
      return !/target/.test(k) && /recorded|written|graded|formed/.test(k) && isCount(live[k]);
    }).sort(function (a, b) { return live[b] - live[a]; })[0];
    if (!haveKey) return null;
    return { have: live[haveKey], need: live[needKey], unit: plain(haveKey).toLowerCase() };
  }
  function generic(d, session) {
    var rows = liveCounts(d);
    if (!rows.length) {
      Object.keys(d).forEach(function (k) {
        if (isCount(d[k])) rows.push({ name: plain(k), score: d[k] });
        else if (d[k] && typeof d[k] === "object" && !Array.isArray(d[k]) && (k === "totals" || k === "counts")) {
          Object.keys(d[k]).forEach(function (k2) { if (isCount(d[k][k2])) rows.push({ name: plain(k2), score: d[k][k2] }); });
        }
      });
      rows.sort(function (a, b) { return b.score - a.score; });
    }
    rows = rows.slice(0, 8);
    var positive = rows.filter(function (r) { return r.score > 0; });
    if (positive.length >= 2) {
      return VisualKit.ranked({ rows: positive, session: session, title: "The record so far, in counts",
        label: "Every count on this page's own record, on one scale. A target count, where this page states one, sits in the same list." });
    }
    var pair = targetPair(d);
    if (pair) {
      return VisualKit.accrual({ have: pair.have, need: pair.need, unit: pair.unit, session: session,
        title: "Still building its record", label: pair.have + " " + pair.unit + " so far, against the " + pair.need + " this page set out to prove itself on." });
    }
    if (rows.length) {
      return VisualKit.ranked({ rows: rows, session: session, title: "The record so far, in counts",
        label: "Every count on this page's own record, on one scale." });
    }
    return VisualKit.accrual({ have: null, need: null, session: session,
      words: "Nothing has been graded yet on this page's own record. The counts will appear here as they accrue." });
  }
  var ADAPTERS = {
    "corrected-band": function (d, s) {
      var names = d.live && d.live.names;
      if (!Array.isArray(names) || !names.length || !names[0].horizons) return null;
      var hz = names[0].horizons[0];
      var items = (hz.bands || []).map(function (b) {
        return { label: names[0].name || "Index", low: b.lower, high: b.upper, current: names[0].close };
      });
      if (!items.length) return null;
      return VisualKit.band({ items: items, session: s, title: "The latest band, drawn to scale",
        label: "Each band is a range this engine published for the next session. The dot is the closing price the band was built from." });
    },
    "touch-surface": function (d, s) {
      var names = d.live && d.live.names;
      if (!Array.isArray(names) || !names.length || !Array.isArray(names[0].cells)) return null;
      var seen = {}, rows = [];
      names[0].cells.forEach(function (c) {
        var key = c.label + "|" + c.side;
        if (seen[key]) return; seen[key] = 1;
        rows.push({ name: (c.symbol || "") + " " + c.label + " percent", score: c.p_pct,
          coverage: "simple benchmark " + c.benchmark_pct + " percent" });
      });
      rows = rows.slice(0, 10);
      if (!rows.length) return null;
      return VisualKit.ranked({ rows: rows, session: s, title: "Chances of touching each level",
        label: "The chance this engine gives each price level being touched, with the simple benchmark printed beside it." });
    },
    "calibration-league": function (d, s) {
      var rows = (d.entrants || []).slice().sort(function (a, b) { return (a.rank || 99) - (b.rank || 99); }).map(function (e) {
        return { name: e.name, score: e.graded_count, coverage: typeof e.error_pts === "number" ? "error " + e.error_pts + " points" : "no error figure on record yet" };
      }).filter(function (r) { return r.name; });
      if (!rows.length) return null;
      return VisualKit.ranked({ rows: rows, session: s, title: "How much grading sits behind each forecaster",
        label: "Graded forecasts per entrant, biggest first. The error figure each entrant is judged on is printed beside its bar." });
    },
    "board": function (d, s) {
      var g = (d.groups || [])[0];
      if (!g || !Array.isArray(g.names)) return null;
      var rows = g.names.slice(0, 12).map(function (n) {
        return { name: n.symbol, score: n.score, coverage: n.coverage_pct + " percent of checks had data" };
      });
      return VisualKit.ranked({ rows: rows, session: s, title: "Today's board, scored",
        label: "The top names on the board with their scores, and how much data sits behind each score printed at the same size." });
    },
    "record": function (d, s) {
      var t = d.totals || {}, c = (d.board && d.board.cohort && d.board.cohort["1d"]) || {};
      var rows = [
        { name: "Calls published", score: t.calls_published },
        { name: "Board calls", score: t.board_calls },
        { name: "Map calls", score: t.map_calls },
        { name: "Graded so far", score: t.calls_graded_so_far },
        { name: "Rose after one day", score: c.rose_count },
        { name: "Did not rise after one day", score: c.did_not_rise_count }
      ].filter(function (r) { return typeof r.score === "number"; });
      if (!rows.length) return null;
      var extra = "The 5 day and 21 day grades are not yet graded.";
      return VisualKit.ranked({ rows: rows, session: s, title: "The Record, in counts",
        label: "Every call kept, and how the graded ones came out after one day. " + extra });
    },
    "vol-term-shape": function (d, s) {
      var cells = (d.history && d.history.cells) || [];
      var pts = cells.filter(function (c) { return c.symbol === "SPY" && c.horizon === 5; })
        .map(function (c) { return { x: "stated " + c.stated_pct + " percent", y: c.coverage_pct }; });
      if (pts.length < 2) return null;
      return VisualKit.curve({ points: pts, session: s, title: "What the stated chances promised, and what happened",
        label: "For each stated chance, the share of past cases that actually landed inside. Points on the level would mean a perfect match." });
    },
    "earnings-distribution": function (d, s) {
      var rows = (d.tiers || []).map(function (t) {
        return { name: t.label, score: t.abs_events, coverage: t.signed_events + " with a signed move record" };
      }).filter(function (r) { return typeof r.score === "number"; });
      if (!rows.length) return null;
      return VisualKit.ranked({ rows: rows, session: d.decision_as_of || s, title: "Earnings moves on record, by company size",
        label: "How many earnings moves sit behind this page's distribution, for each size group." });
    },
    "exceedance": function (d, s) {
      var cells = (d.history && d.history.cells) || [];
      var rows = cells.slice(0, 8).map(function (c) {
        return { name: String(c.forecast || "").toUpperCase() + " on " + c.symbol, score: c.realised_pct,
          coverage: "forecast " + c.mean_forecast_pct + " percent, " + c.graded + " graded" };
      }).filter(function (r) { return typeof r.score === "number"; });
      if (!rows.length) return null;
      return VisualKit.ranked({ rows: rows, session: s, title: "How often each big move actually happened",
        label: "The realised share for each forecast, with the forecast itself and the graded count printed beside it." });
    },
    "gap-destiny": function (d, s) {
      var bands = (d.history && d.history.bands) || [];
      var rows = bands.map(function (b) {
        return { name: "Gap of " + b.band_label, score: b.index_fill_pct, coverage: "of " + b.index_n + " index gaps" };
      }).filter(function (r) { return typeof r.score === "number"; });
      if (!rows.length) return null;
      return VisualKit.ranked({ rows: rows, session: s, title: "How often each size of gap filled, for the index funds",
        label: "The share of gaps that filled on the day, by gap size, from this page's own history." });
    },
    "mortality-curve": pairTable,
    "half-life-clock": pairTable,
    "streak-trap": function (d, s) {
      var rows = (d.triggers || []).map(function (t) {
        return { name: t.family_words, score: t.centre_pct, coverage: "from " + t.current_n + " cases on record" };
      }).filter(function (r) { return typeof r.score === "number"; });
      if (!rows.length) return null;
      return VisualKit.ranked({ rows: rows, session: s, title: "Each streak reading, as a chance",
        label: "The centre chance this page publishes for each family, with the cases behind it." });
    },
    "completion-clock": function (d, s) {
      var cls = (d.classes || [])[0];
      if (!cls || !Array.isArray(cls.hazard_pct) || cls.hazard_pct.length < 2) return null;
      var pts = cls.hazard_pct.map(function (v, i) { return { x: "step " + (i + 1), y: v }; });
      return VisualKit.curve({ points: pts, step: true, session: s, title: "When completions actually land",
        label: "The share of groups completing at each step, from this page's own record. A flat stretch means nothing completed there." });
    },
    "wall-lifetime": function (d, s) {
      var cards = d.live && d.live.cards_counted_toward_target;
      if (!cards) return null;
      var rows = Object.keys(cards).map(function (k) { return { name: k, score: cards[k] }; });
      if (!rows.length) return null;
      return VisualKit.ranked({ rows: rows, session: s, title: "Wall cards counted so far, per index",
        label: "Cards graded toward this page's target for each index, on the same scale. The live counts below carry the full record." });
    },
    "honest-pop": function (d, s) {
      var live = d.live || {};
      if (typeof live.expiries_graded !== "number" || typeof live.proving_target_expiries !== "number") return null;
      return VisualKit.accrual({ have: live.expiries_graded, need: live.proving_target_expiries, unit: "expiries graded", session: s,
        title: "Waiting on the options snapshots it grades from",
        label: live.records_written + " records written so far. No snapshot, no grade: this page grades only what the snapshots actually show." });
    },
    "own-norm-depth": function (d, s) {
      var live = d.live || {};
      if (typeof live.proving_target_matured !== "number") return null;
      return VisualKit.accrual({ have: live.forecasts_graded || 0, need: live.proving_target_matured, unit: "matured forecasts graded", session: s,
        title: "Still building the history it needs",
        label: live.names_checked + " names checked. The longest history on record runs " + live.longest_history_on_record + " sessions, and this page needs " + live.sessions_needed_per_name + " per name before a single name qualifies." });
    },
    "pin-or-escape": function (d, s) {
      var live = d.live || {};
      if (typeof live.proving_target_weeks !== "number") return null;
      return VisualKit.accrual({ have: live.records_written || 0, need: live.proving_target_weeks, unit: "weekly records", session: s,
        title: "Weeks on record against the proving target",
        label: (live.weeks_counted || 0) + " week counted so far, " + (live.records_graded || 0) + " records graded." });
    }
  };
  function renderSubjectChart(chart, session) {
    if (!chart || !chart.kind) return null;
    if (chart.kind === "ranked") return VisualKit.ranked({ rows: chart.rows || [], session: session, title: chart.title, label: chart.label });
    if (chart.kind === "curve") return VisualKit.curve({ points: chart.points || [], session: session, title: chart.title, label: chart.label });
    if (chart.kind === "band") return VisualKit.band({ items: chart.items || [], session: session, title: chart.title, label: chart.label });
    if (chart.kind === "distribution") return VisualKit.distribution({ buckets: chart.buckets || [], session: session, title: chart.title, label: chart.label });
    return null;
  }
  function pairTable(d, s) {
    var rows = (d.pair_table || []).slice().sort(function (a, b) { return (b.promoted || 0) - (a.promoted || 0); }).slice(0, 10).map(function (p) {
      return { name: p.pair_words, score: p.promoted, coverage: (p.confirmed || 0) + " confirmed, " + (p.not_replicated || 0) + " did not replicate" };
    }).filter(function (r) { return typeof r.score === "number"; });
    if (!rows.length) return null;
    return VisualKit.ranked({ rows: rows, session: s, title: "Promoted pairs on record",
      label: "How many combinations each pair promoted, with how they fared on recheck printed beside the bar." });
  }
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
      /* Subject chart first (cure 2026-10-31): the producer's
         subject_chart.lead plots the page's own subject values.
         Pages carrying one never fall through to the count generic. */
      if (d.subject_chart) {
        try { html = renderSubjectChart(d.subject_chart.lead, session); } catch (e) { html = null; }
        if (!html) {
          html = VisualKit.accrual({ have: null, need: null, session: session,
            words: "No subject reading is on record for this page yet, so no chart is drawn. The reading appears here when its own data lands." });
        }
      }
      if (!html && !d.subject_chart) {
        try { html = ADAPTERS[slug] ? ADAPTERS[slug](d, session) : null; } catch (e) { html = null; }
        if (!html) html = generic(d, session);
      }
      host.innerHTML = html;
    }).catch(function () { /* The page's own content stays as it is. */ });
  });
})();
