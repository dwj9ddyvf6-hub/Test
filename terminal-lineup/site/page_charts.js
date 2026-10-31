/* Universal chart layout (2026-10-31, charts-IA phase). Loaded by
   shared.js on every page. One job: every page leads with a chart,
   carries its record charted under "The record", keeps its status as
   a small chip by the title, and names what is missing in one small
   line at the foot. It reads only the page's own data.json (on the
   hub, each tile and card reads its own tool's data.json), draws
   only numbers found there, and leaves the page's own content and
   the adapter visuals (engine-visual.js, tool-visual.js) untouched. */
(function () {
  "use strict";
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function isNum(v) { return typeof v === "number" && isFinite(v); }
  function plain(key) { var s = String(key).replace(/_/g, " "); return s.charAt(0).toUpperCase() + s.slice(1); }
  function slugOf() {
    var parts = window.location.pathname.split("/").filter(Boolean);
    var si = parts.lastIndexOf("site"); if (si >= 0) parts = parts.slice(si + 1);
    if (parts.length && parts[parts.length - 1] === "index.html") parts.pop();
    return { slug: parts.length ? parts[parts.length - 1] : "", depth: parts.length };
  }
  function whenReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }
  function waitKit(fn, tries) {
    if (typeof VisualKit !== "undefined") return fn();
    if ((tries || 0) > 40) return;
    setTimeout(function () { waitKit(fn, (tries || 0) + 1); }, 150);
  }
  function fetchJson(url) {
    return fetch(url, { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  }

  /* ---- generic extraction: the best honest picture in one data file ---- */
  function datedSeries(data) {
    var best = null;
    function walk(obj, path, depth) {
      if (!obj || depth > 3 || best) return;
      if (Array.isArray(obj)) {
        if (obj.length >= 3 && obj.every(function (r) { return r && typeof r === "object" && !Array.isArray(r); })) {
          var keys = Object.keys(obj[0]);
          var dateKey = keys.filter(function (k) { return /date|session|day|when|period/.test(k); })[0];
          var numKeys = keys.filter(function (k) { return obj.some(function (r) { return isNum(r[k]); }); });
          if (dateKey && numKeys.length) {
            var nk = numKeys.filter(function (k) { return /pct|value|close|count|score|rate|share/.test(k); })[0] || numKeys[0];
            var series = obj.map(function (r) { return { date: String(r[dateKey] || ""), value: r[nk] }; }).filter(function (p) { return isNum(p.value); });
            if (series.length >= 3) { best = { series: series, field: nk, path: path }; return; }
          }
        }
        obj.slice(0, 4).forEach(function (v, i) { walk(v, path + "/" + i, depth + 1); });
        return;
      }
      Object.keys(obj).forEach(function (k) { if (k !== "record_surface") walk(obj[k], path + "/" + k, depth + 1); });
    }
    walk(data, "", 0);
    return best;
  }
  function countRows(data, limit) {
    var rows = [];
    function add(name, v) { if (isNum(v) && v > 0) rows.push({ name: name, score: v }); }
    ["counts", "totals"].forEach(function (k) {
      if (data[k] && typeof data[k] === "object") Object.keys(data[k]).forEach(function (k2) { add(plain(k2), data[k][k2]); });
    });
    if (data.live && typeof data.live === "object") Object.keys(data.live).forEach(function (k) { add(plain(k), data.live[k]); });
    Object.keys(data).forEach(function (k) { if (["counts", "totals", "live", "record_surface"].indexOf(k) < 0) add(plain(k), data[k]); });
    rows.sort(function (a, b) { return b.score - a.score; });
    return rows.slice(0, limit || 8);
  }
  function genericLead(data, session) {
    var ds = datedSeries(data);
    if (ds) return VisualKit.area({ series: ds.series.slice(-60), session: session, title: "How it has moved", label: "The dated " + plain(ds.field).toLowerCase() + " values on this page's own record, most recent last." });
    var rows = countRows(data, 10);
    if (rows.length >= 2) return VisualKit.countBars({ rows: rows, session: session, title: "The reading, in counts", label: "The counts this page publishes, drawn on one scale." });
    if (rows.length === 1) return VisualKit.accrual({ have: rows[0].score, need: null, session: session, words: rows[0].name + ": " + rows[0].score + " on record. The detail below carries the full reading." });
    return null;
  }

  /* ---- the record section, from the record_surface block ---- */
  function subjectChartHtml(chart, session) {
    if (!chart || !chart.kind) return null;
    try {
      if (chart.kind === "ranked") return VisualKit.ranked({ rows: chart.rows || [], session: session, title: chart.title, label: chart.label });
      if (chart.kind === "curve") return VisualKit.curve({ points: chart.points || [], session: session, title: chart.title, label: chart.label });
      if (chart.kind === "band") return VisualKit.band({ items: chart.items || [], session: session, title: chart.title, label: chart.label });
      if (chart.kind === "distribution") return VisualKit.distribution({ buckets: chart.buckets || [], session: session, title: chart.title, label: chart.label });
      if (chart.kind === "line") return VisualKit.line({ series: chart.series || [], session: session, title: chart.title, label: chart.label });
      if (chart.kind === "tiles") return VisualKit.tiles({ items: chart.items || [], session: session, title: chart.title, label: chart.label });
      if (chart.kind === "tape") return VisualKit.tape({ events: chart.events || [], session: session, title: chart.title, label: chart.label });
    } catch (e) { return null; }
    return null;
  }
  function recordSection(data) {
    var rs = data.record_surface;
    if (!rs) return null;
    var session = VisualKit.sessionOf(data);
    /* Subject record first (cure 2026-10-31): pages carrying a
       subject_chart record it alone; the internal count parts below
       are suppressed for those pages, never drawn beside it. A page
       whose subject record is null draws no record chart. */
    if (data.subject_chart) {
      var subj = subjectChartHtml(data.subject_chart.record, session);
      var calib2 = "";
      if (typeof rs.calibration_record === "string" && rs.calibration_record) calib2 = '<p class="cmeans">' + esc(rs.calibration_record) + "</p>";
      else if (rs.calibration_record && typeof rs.calibration_record === "object") {
        var ct2 = rs.calibration_record.words || rs.calibration_record.text || rs.calibration_record.summary;
        if (ct2) calib2 = '<p class="cmeans">' + esc(ct2) + "</p>";
      }
      if (!subj && !calib2) return null;
      var html2 = '<section class="chartbox recordchart" id="recordChart"><h2>The record</h2><p class="studyword">Study record</p>' + (subj || "") + calib2 + "</section>";
      var sec2 = document.createElement("div");
      sec2.innerHTML = html2;
      return sec2.firstChild;
    }
    /* Market-tool subject record charts (cure 2026-10-31): when the
       producer built record_surface.subject_charts for a page, those
       charts alone are its record visual; an empty list draws none
       and no count part is substituted. */
    if (Object.prototype.hasOwnProperty.call(rs, "subject_charts")) {
      var mparts = [];
      (rs.subject_charts || []).forEach(function (c) { var h = subjectChartHtml(c, session); if (h) mparts.push(h); });
      var mcal = "";
      if (typeof rs.calibration_record === "string" && rs.calibration_record) mcal = '<p class="cmeans">' + esc(rs.calibration_record) + "</p>";
      else if (rs.calibration_record && typeof rs.calibration_record === "object") {
        var mct = rs.calibration_record.words || rs.calibration_record.text || rs.calibration_record.summary;
        if (mct) mcal = '<p class="cmeans">' + esc(mct) + "</p>";
      }
      if (!mparts.length && !mcal) return null;
      var mhtml = '<section class="chartbox recordchart" id="recordChart"><h2>The record</h2><p class="studyword">Study record</p>' + mparts.join("") + mcal + "</section>";
      var msec = document.createElement("div");
      msec.innerHTML = mhtml;
      return msec.firstChild;
    }
    var parts = [];
    var locs = (rs.study_record && rs.study_record.locations) || [];
    var locRows = locs.filter(function (l) { return isNum(l.items) && l.items > 0; })
      .map(function (l) { return { name: plain(String(l.path).replace(/^\//, "").replace(/\//g, ": ")), score: l.items }; })
      .sort(function (a, b) { return b.score - a.score; }).slice(0, 10);
    if (locRows.length >= 2) parts.push(VisualKit.countBars({ rows: locRows, session: session, title: "What the record holds, by part", label: "How much sits in each part of the record on file. The study record is the history this page was built and checked on." }));
    else if (locRows.length === 1) parts.push(VisualKit.accrual({ have: locRows[0].score, need: null, session: session, words: locRows[0].score + " items sit in the record on file (" + locRows[0].name.toLowerCase() + ")." }));
    var acc = rs.live_accrual;
    if (acc && acc.counts && typeof acc.counts === "object") {
      var crows = Object.keys(acc.counts).filter(function (k) { return isNum(acc.counts[k]) && acc.counts[k] > 0; }).map(function (k) { return { name: plain(k), score: acc.counts[k] }; }).sort(function (a, b) { return b.score - a.score; }).slice(0, 8);
      if (crows.length >= 2) parts.push(VisualKit.countBars({ rows: crows, session: session, title: "The record, in counts", label: "The counts on this page's own record, drawn on one scale." }));
    }
    if (acc && isNum(acc.forecasts)) {
      parts.push(VisualKit.countBars({ rows: [{ name: "Forecasts on record", score: acc.forecasts }, { name: "Graded so far", score: acc.grades || 0 }, { name: "Corrections", score: acc.corrections || 0 }].filter(function (r) { return r.score > 0; }), session: session, title: "The live record so far", label: "Forecasts this page has published since it went live, and how many have been graded. Grades arrive after each following session close." }));
    }
    if (rs.gauge_history && rs.gauge_history.files) {
      var grows = Object.keys(rs.gauge_history.files).map(function (f) { return { name: f.replace(/\.csv$/, "").replace(/_/g, " "), score: rs.gauge_history.files[f] }; }).filter(function (r) { return r.score > 0; });
      if (grows.length >= 2) parts.push(VisualKit.countBars({ rows: grows, session: session, title: "Gauge history on file, by gauge", label: "How many past readings sit behind each gauge, counted from the history files on disk." }));
    }
    if (!parts.length) {
      var frows = countRows(data, 8);
      if (frows.length >= 2) parts.push(VisualKit.countBars({ rows: frows, session: session, title: "The record, in counts", label: "The counts on this page's own record, drawn on one scale." }));
    }
    var calib = "";
    if (typeof rs.calibration_record === "string" && rs.calibration_record) calib = '<p class="cmeans">' + esc(rs.calibration_record) + "</p>";
    else if (rs.calibration_record && typeof rs.calibration_record === "object") {
      var ct = rs.calibration_record.words || rs.calibration_record.text || rs.calibration_record.summary;
      if (ct) calib = '<p class="cmeans">' + esc(ct) + "</p>";
    }
    if (!parts.length && !calib) return null;
    var html = '<section class="chartbox recordchart" id="recordChart"><h2>The record</h2><p class="studyword">Study record</p>' + parts.join("") + calib + "</section>";
    var sec = document.createElement("div");
    sec.innerHTML = html;
    return sec.firstChild;
  }
  function missingLine(data) {
    var rs = data.record_surface;
    if (!rs || !rs.missing || !rs.missing.what_and_when) return null;
    var p = document.createElement("p");
    p.className = "missingline";
    p.id = "missingLine";
    p.textContent = rs.missing.what_and_when;
    return p;
  }
  function titleChip(data) {
    var h1 = document.querySelector("h1");
    if (!h1 || document.querySelector(".titlechip")) return;
    var rs = data.record_surface || {};
    var asOf = (rs.current_reading && rs.current_reading.as_of) || VisualKit.sessionOf(data);
    if (!asOf) return;
    var span = document.createElement("span");
    span.className = "titlechip";
    var chip = document.createElement("span");
    chip.className = "chip waiting";
    chip.textContent = "Reading as of " + String(asOf).slice(0, 10);
    span.appendChild(chip);
    h1.appendChild(span);
  }

  function toolPage() {
    var info = slugOf();
    if (!info.slug) return;
    fetchJson("data.json").then(function (data) {
      if (!data) return;
      waitKit(function () {
        var wrap = document.querySelector(".wrap") || document.body;
        titleChip(data);
        var hasAdapter = !!document.querySelector('script[src*="tool-visual"], script[src*="engine-visual"]');
        var host = document.getElementById("vkHost");
        if (!host && !hasAdapter && info.slug !== "market-mood") {
          var lead = document.createElement("div");
          lead.className = "chartbox leadchart";
          lead.id = "chartLead";
          var header = document.querySelector("header") || wrap.querySelector("h1");
          var anchor = header && header.parentNode === wrap ? header : (wrap.querySelector("h1") || wrap.firstChild);
          if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(lead, anchor.nextSibling);
          else wrap.insertBefore(lead, wrap.firstChild);
          var html = null;
          try {
            /* Subject lead first (cure 2026-10-31, modules/record
               batch): pages carrying a subject_chart lead draw it
               instead of the generic datedSeries/countBars pick. A
               null lead keeps the generic path, which is the subject
               area chart for the pages that already lead with one. */
            if (data.subject_chart && data.subject_chart.lead) html = subjectChartHtml(data.subject_chart.lead, VisualKit.sessionOf(data));
            if (!html) html = genericLead(data, VisualKit.sessionOf(data));
          } catch (e) { html = null; }
          if (html) lead.innerHTML = html; else lead.remove();
        }
        var verdict = document.querySelector(".verdict");
        var leadEl = document.getElementById("vkHost") || document.getElementById("chartLead");
        if (verdict && leadEl && leadEl.parentNode === verdict.parentNode && verdict.compareDocumentPosition(leadEl) & 4) {
          leadEl.parentNode.insertBefore(verdict, leadEl.nextSibling);
        }
        var rec = null, miss = null;
        try { rec = recordSection(data); } catch (e) { rec = null; }
        try { miss = missingLine(data); } catch (e) { miss = null; }
        var footAnchor = document.querySelector(".related") || document.querySelector("footer");
        if (rec) { if (footAnchor) wrap.insertBefore(rec, footAnchor); else wrap.appendChild(rec); }
        if (miss) { if (footAnchor) wrap.insertBefore(miss, footAnchor); else wrap.appendChild(miss); }
      });
    });
  }

  /* ---- hub: visual front tiles + card minis ---- */
  function miniBars(rows) {
    if (!rows.length) return "";
    var max = Math.max.apply(null, rows.map(function (r) { return r.score; }).concat([1]));
    return '<div class="vk-ranked">' + rows.slice(0, 4).map(function (r) {
      return '<div class="vk-rrow"><span class="vk-rname">' + esc(String(r.name).slice(0, 22)) + '</span><span class="bar"><i style="width:' + Math.max(2, Math.round(100 * r.score / max)) + '%"></i></span><span class="vk-rscore">' + r.score + "</span></div>";
    }).join("") + "</div>";
  }
  function miniFor(type, data) {
    if (!data) return "";
    var ds = datedSeries(data);
    if ((type === "sparkline" || type === "line" || type === "timeline" || type === "fan") && ds) {
      var raw = VisualKit.sparkline({ series: ds.series.slice(-40), raw: true });
      if (raw) return raw;
    }
    if (type === "gauge") {
      var comp = data.state && data.state.composite_percentile;
      if (isNum(comp)) {
        var g = VisualKit.gaugeZones({ value: comp, low: 0, high: 100, zones: [{ to: 25, label: "Extreme fear" }, { to: 50, label: "Fearful" }, { to: 75, label: "Neutral" }, { to: 100, label: "Greed" }] });
        var m = g.match(/<svg[\s\S]*?<\/svg>/);
        if (m) return m[0];
      }
    }
    if (type === "donut") {
      var rows = countRows(data, 5);
      if (rows.length >= 2) {
        var d = VisualKit.donut({ slices: rows.map(function (r) { return { label: r.name, value: r.score }; }) });
        var dm = d.match(/<svg[\s\S]*?<\/svg>/);
        if (dm) return dm[0];
      }
    }
    var locs = data.record_surface && data.record_surface.study_record && data.record_surface.study_record.locations || [];
    var locRows = locs.filter(function (l) { return isNum(l.items) && l.items > 0; }).map(function (l) { return { name: plain(String(l.path).replace(/^\//, "").replace(/\//g, ": ")), score: l.items }; }).sort(function (a, b) { return b.score - a.score; });
    if (locRows.length >= 1) return miniBars(locRows);
    var acc2 = data.record_surface && data.record_surface.live_accrual;
    if (acc2 && isNum(acc2.forecasts)) {
      var arows = [{ name: "Forecasts", score: acc2.forecasts }, { name: "Graded", score: acc2.grades || 0 }].filter(function (r) { return r.score > 0; });
      if (arows.length) return miniBars(arows);
    }
    var rows2 = countRows(data, 4);
    if (rows2.length >= 1) return miniBars(rows2);
    if (ds) return VisualKit.sparkline({ series: ds.series.slice(-40), raw: true });
    return "";
  }
  function hubPage() {
    waitKit(function () {
      document.querySelectorAll(".vftile[data-vf]").forEach(function (tile) {
        var slug = tile.getAttribute("data-vf");
        fetchJson(slug + "/data.json").then(function (data) {
          if (!data) return;
          var host = tile.querySelector(".vfchart");
          if (!host) return;
          var html = null;
          try {
            if (slug === "market-mood" && data.state && isNum(data.state.composite_percentile)) {
              html = VisualKit.gaugeZones({ value: data.state.composite_percentile, low: 0, high: 100, session: VisualKit.sessionOf(data), title: null, label: "Composite percentile " + data.state.composite_percentile + ". Regime: " + (data.state.regime || "") + "." , zones: [{ to: 25, label: "Extreme fear" }, { to: 50, label: "Fearful" }, { to: 75, label: "Neutral" }, { to: 100, label: "Greed" }] });
            } else if (slug === "corrected-band") {
              var names = data.live && data.live.names || [];
              if (names.length && names[0].horizons) {
                var steps = names[0].horizons.map(function (hz) {
                  var lows = (hz.bands || []).map(function (b) { return b.lower; }), highs = (hz.bands || []).map(function (b) { return b.upper; });
                  var days = hz.sessions || hz.days || hz.horizon;
                  return { label: days ? (days + (Number(days) === 1 ? " day" : " days")) : (hz.horizon_close || ""), low: Math.min.apply(null, lows), high: Math.max.apply(null, highs), mid: names[0].close };
                }).filter(function (st) { return isNum(st.low) && isNum(st.high); });
                if (steps.length) html = VisualKit.fan({ steps: steps, session: VisualKit.sessionOf(data), title: null, label: "The published ranges for " + (names[0].name || "the index") + ", one step per horizon. Study record: 2,238 graded study forecasts." });
              }
            }
            if (!html) html = genericLead(data, VisualKit.sessionOf(data));
          } catch (e) { html = null; }
          if (html) host.innerHTML = html;
        });
      });
      document.querySelectorAll(".hubcard .mini[data-mini]").forEach(function (mini) {
        var slug = mini.getAttribute("data-slug"), type = mini.getAttribute("data-mini");
        fetchJson(slug + "/data.json").then(function (data) {
          var html = "";
          try { html = miniFor(type, data); } catch (e) { html = ""; }
          if (html) mini.innerHTML = html;
        });
      });
    });
  }

  /* Liveness (2026-10-31): live.js calls this when the page's own data
     file changes on the server. Everything this module inserted is
     removed and rebuilt from the fresh file, in place. */
  window.__pageChartsRerender = function () {
    ["chartLead", "recordChart", "missingLine"].forEach(function (id) {
      var n = document.getElementById(id); if (n) n.remove();
    });
    document.querySelectorAll(".titlechip").forEach(function (n) { n.remove(); });
    var info = slugOf();
    if (info.depth === 0) hubPage(); else toolPage();
  };

  whenReady(function () {
    var info = slugOf();
    if (info.depth === 0) hubPage(); else toolPage();
  });
})();
