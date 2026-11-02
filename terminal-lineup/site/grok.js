/* GrokBot design-system behaviour (2026-11-02 replication).
   Loaded on every page by shared.js from this one shared source.
   Presentation only: every number below is read from the page's own
   DOM or its own data.json at render time. Nothing is invented; a
   component with no honest data on a page is omitted there. The
   timestamp shown beside a metric is that data's own as_of. */
(function () {
  "use strict";
  var parts = window.location.pathname.split("/").filter(Boolean);
  var si = parts.lastIndexOf("site"); if (si >= 0) parts = parts.slice(si + 1);
  if (parts.length && parts[parts.length - 1] === "index.html") parts.pop();
  var depth = parts.length;
  var root = depth >= 1 ? "../" : "";
  var slug = depth >= 1 ? parts[parts.length - 1] : "";
  var onHub = depth === 0;
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function fmt(n, d) { return n == null || isNaN(n) ? "no data" : Number(n).toLocaleString("en-US", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function money(n) { return n == null ? "no data" : "$" + fmt(Math.round(n)); }
  function whenReady(fn) { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn); else fn(); }

  /* grok.css from the same shared source */
  (function () {
    if (!document.querySelector('link[href$="grok.css"]')) {
      var link = document.createElement("link"); link.rel = "stylesheet"; link.href = root + "grok.css";
      (document.head || document.documentElement).appendChild(link);
    }
  })();

  function asOfOf(data) {
    if (!data) return null;
    var cands = [];
    if (data.state && data.state.date) cands.push(data.state.date);
    if (data.record_surface && data.record_surface.current_reading && data.record_surface.current_reading.as_of) cands.push(data.record_surface.current_reading.as_of);
    ["as_of", "published_at_utc", "generated_at", "session_date", "date", "current_filed_last", "current_period", "scored_run_session", "session", "history_to"].forEach(function (k) { if (data[k]) cands.push(data[k]); });
    for (var i = 0; i < cands.length; i++) { var m = String(cands[i]).match(/20\d\d-\d\d-\d\d/); if (m) return m[0]; }
    return null;
  }
  function loadData(cb) {
    if (onHub) { cb(null); return; }
    fetch("data.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(cb).catch(function () { cb(null); });
  }

  /* Header status dot + finder button (C2/C18 shell) */
  function shell(data) {
    var bar = document.querySelector(".topbar"); if (!bar) return;
    var asOf = asOfOf(data);
    if (asOf) {
      /* F4 cure: stale is visibly stale from 4 days old (SPEC non-neg. 1),
         not the old 14-day threshold that left 4-14 day data unlabelled. */
      var ageDays = Math.max(0, Math.round((Date.now() - new Date(asOf + "T12:00:00Z").getTime()) / 864e5));
      var cls = ageDays <= 3 ? "live" : (ageDays >= 4 ? "stale" : "");
      var txt = "Data as of " + asOf + (cls === "stale" ? " (stale, " + ageDays + " days old)" : "");
      var s = bar.querySelector(".gb-asof");
      if (!s) {
        s = el("span", "gb-asof");
        s.appendChild(el("span", "gb-dot " + cls));
        s.appendChild(document.createTextNode(txt));
        s.style.cssText = "color:#c9cfdd;font-size:13px";
        bar.appendChild(s);
      } else { s.lastChild.textContent = txt; var d0 = s.querySelector(".gb-dot"); if (d0) d0.className = "gb-dot " + cls; }
    }
    if (!bar.querySelector(".gb-findbtn")) {
      var b = el("button", "gb-findbtn gb-chip", "Find a tool"); b.type = "button";
      b.addEventListener("click", openFinder); bar.appendChild(b);
    }
  }

  /* C18 finder dialog over the generated index of our real pages */
  var finderIndex = null;
  function openFinder() {
    var dlg = document.querySelector(".gb-fdlg");
    if (!dlg) {
      dlg = el("div", "gb-fdlg");
      var panel = el("div", "gb-fpanel");
      var inp = el("input"); inp.type = "search"; inp.placeholder = "Type to find a tool by name or job"; inp.setAttribute("aria-label", "Find a tool");
      var out = el("div", "gb-fout"); out.appendChild(el("p", "gb-fempty", "Loading the latest data\u2026"));
      panel.appendChild(inp); panel.appendChild(out); dlg.appendChild(panel);
      dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.classList.remove("open"); });
      inp.addEventListener("input", function () { renderFinder(out, inp.value); });
      document.body.appendChild(dlg);
      fetch(root + "grok-index.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (idx) {
        finderIndex = idx;
        if (!idx) { out.innerHTML = ""; out.appendChild(el("p", "gb-fempty", "Data not available yet")); return; }
        renderFinder(out, "");
      }).catch(function () { out.innerHTML = ""; out.appendChild(el("p", "gb-fempty", "Data not available yet")); });
    }
    dlg.classList.add("open");
    var i2 = dlg.querySelector("input"); if (i2) i2.focus();
  }
  function renderFinder(out, q) {
    if (!finderIndex) return;
    out.innerHTML = "";
    q = (q || "").toLowerCase();
    var groups = {};
    finderIndex.forEach(function (it) {
      if (q && (it.name + " " + it.desc).toLowerCase().indexOf(q) < 0) return;
      (groups[it.group] = groups[it.group] || []).push(it);
    });
    var names = Object.keys(groups);
    if (!names.length) { out.appendChild(el("p", "gb-fempty", "Nothing matches that search.")); return; }
    names.forEach(function (g) {
      out.appendChild(el("p", "gb-fgrp", g));
      groups[g].forEach(function (it) {
        var a = el("a", "gb-fit"); a.href = root + it.href;
        a.appendChild(el("span", "n", it.name));
        a.appendChild(el("span", "d", it.desc || ""));
        if (it.is_new) a.appendChild(el("span", "gb-badge new", "NEW"));
        out.appendChild(a);
      });
    });
  }

  /* C13 anchor pill row from the page's own section headings */
  var MAXPILLS = 12; /* desk cure: 53-pill wall becomes a bounded anchor row */
  function jumpPills() {
    var wrap = document.querySelector(".wrap") || document.body;
    var heads = Array.prototype.slice.call(wrap.querySelectorAll("h2")).filter(function (h) { return !h.closest(".related,.gb-fdlg,.gb-disc"); }).slice(0, MAXPILLS);
    if (heads.length < 3 || document.querySelector(".gb-jump")) return;
    var row = el("nav", "gb-jump"); row.setAttribute("aria-label", "On this page");
    heads.forEach(function (h, i) {
      if (!h.id) h.id = "gb-sec-" + i;
      var a = el("a", "gb-jpill", (h.textContent || "").trim().slice(0, 42)); a.href = "#" + h.id;
      row.appendChild(a);
    });
    var anchor = document.querySelector(".topbar") || wrap.firstChild;
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(row, anchor.nextSibling);
  }

  /* C2 hero strip on the hub, from the hub's own published counts */
  function hubHero() {
    var c = document.querySelector(".hubcount"); if (!c) return;
    var m = c.textContent.match(/(\d+) tools in the lineup: (\d+) live, (\d+) waiting, (\d+) not yet graded, (\d+) stale/);
    if (!m || document.querySelector(".gb-stats")) return;
    var stats = [
      { label: "Tools in the lineup", value: m[1], sub: "Each with one clear job", dark: true },
      { label: "Live today", value: m[2], sub: "Reading is current", sign: "up" },
      { label: "Waiting", value: m[3], sub: "Honestly dated, not hidden" },
      { label: "Not yet graded", value: m[4], sub: "Still being proven" },
      { label: "Stale", value: m[5], sub: "Named on their cards below", sign: m[5] === "0" ? "" : "down" }
    ];
    var grid = el("div", "gb-stats");
    stats.forEach(function (s) {
      var d = el("div", "gb-stat" + (s.dark ? " dark" : "") + (s.sign ? " " + s.sign : ""));
      d.appendChild(el("p", "gb-slabel", s.label));
      d.appendChild(el("p", "gb-svalue", s.value));
      d.appendChild(el("p", "gb-ssub", s.sub));
      grid.appendChild(d);
    });
    c.parentNode.insertBefore(grid, c.nextSibling);
  }

  /* Desk page (P1/P9): C2 hero strip from the desk's own data.json.
     C9 donut OMITTED: positions carry quantity only, no prices, so no
     honest weights exist to draw. */
  function deskHero(data) {
    if (!data || !data.account || document.querySelector(".gb-stats")) return;
    var a = data.account, ep = data.epoch || {};
    var day = (a.equity != null && a.last_equity != null) ? a.equity - a.last_equity : null;
    var since = (a.equity != null && ep.starting_capital) ? (a.equity / ep.starting_capital - 1) * 100 : null;
    var stats = [
      { label: "Account value", value: money(a.equity), sub: "Paper account, all sleeves", dark: true },
      { label: "Cash", value: money(a.cash), sub: "Buying power " + money(a.buying_power) },
      { label: "Since last reading", value: day == null ? "no data" : (day >= 0 ? "+" : "\u2212") + money(Math.abs(day)).slice(0), sub: "Against the prior cycle's equity", sign: day == null ? "" : (day >= 0 ? "up" : "down") },
      { label: "Since the $1M start", value: since == null ? "no data" : (since >= 0 ? "+" : "") + since.toFixed(2) + "%", sub: "Graded against SPY and QQQ on the desk record", sign: since == null ? "" : (since >= 0 ? "up" : "down") },
      { label: "Open positions", value: String((data.positions || []).length), sub: (data.positions || []).length ? (data.positions || []).map(function (p) { return p.symbol; }).join(", ") : "No open positions" }
    ];
    var grid = el("div", "gb-stats");
    stats.forEach(function (s) {
      var d = el("div", "gb-stat" + (s.dark ? " dark" : "") + (s.sign ? " " + s.sign : ""));
      d.appendChild(el("p", "gb-slabel", s.label));
      d.appendChild(el("p", "gb-svalue", s.value));
      d.appendChild(el("p", "gb-ssub", s.sub));
      grid.appendChild(d);
    });
    var h1 = document.querySelector("h1");
    var anchor = document.querySelector(".explblock") || h1;
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(grid, anchor.nextSibling);
    else document.body.insertBefore(grid, document.body.firstChild);
  }

  /* Market Mood (P2): C3 gauge + printed recipe. The composite is the
     median of the 4 core gauges (the page's own stated method); the
     recipe rows are those gauges with raw value, percentile and the
     gauge's own as_of. Gauges with no percentile are listed as such. */
  function moodRecipe(data) {
    if (!data || !data.state || !data.state.gauges || document.querySelector(".gb-gaugewrap")) return;
    var st = data.state, core = ["G2", "G3", "G5", "G6"];
    var wrapG = el("section", "gb-gaugewrap");
    wrapG.style.cssText = "background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px;margin:0 0 16px";
    var panel = el("div", "gb-gauge");
    panel.appendChild(el("p", "gb-kicker", "Composite, with its recipe"));
    var pct = st.composite_percentile;
    var arc = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    arc.setAttribute("viewBox", "0 0 200 110"); arc.style.width = "100%";
    var frac = Math.max(0, Math.min(1, (pct || 0) / 100));
    var bg = document.createElementNS("http://www.w3.org/2000/svg", "path");
    bg.setAttribute("d", "M 15 100 A 85 85 0 0 1 185 100"); bg.setAttribute("fill", "none"); bg.setAttribute("stroke", "#454a5e"); bg.setAttribute("stroke-width", "13");
    var fg = document.createElementNS("http://www.w3.org/2000/svg", "path");
    var ang = Math.PI * (1 - frac), ex = 100 + 85 * Math.cos(ang), ey = 100 - 85 * Math.sin(ang);
    fg.setAttribute("d", "M 15 100 A 85 85 0 0 1 " + ex.toFixed(1) + " " + ey.toFixed(1));
    fg.setAttribute("fill", "none"); fg.setAttribute("stroke", "#7ee0c3"); fg.setAttribute("stroke-width", "13");
    arc.appendChild(bg); arc.appendChild(fg); panel.appendChild(arc);
    panel.appendChild(el("div", "gb-big", pct == null ? "no data" : String(pct)));
    panel.appendChild(el("p", "gb-glabel", "Composite percentile, 0 (extreme fear) to 100 (greed). " + (st.disagreement || "") + " Reading date " + (st.date || "not dated") + "."));
    wrapG.appendChild(panel);
    var side = el("div");
    side.appendChild(el("p", "gb-kicker", "How the composite is built"));
    side.appendChild(el("p", "gb-sentence", "The composite is the median of the four core gauges below. Every ingredient prints its raw value, its percentile and its own reading date, so the headline number can be checked by hand."));
    var t = el("table", "gb-parts");
    t.innerHTML = "<thead><tr><th>Gauge</th><th>Raw value</th><th>Percentile</th><th></th><th>As of</th></tr></thead>";
    var tb = document.createElement("tbody");
    core.forEach(function (id) {
      var g = st.gauges[id]; if (!g) return;
      var tr = document.createElement("tr");
      [id + " " + (g.name || ""), g.value == null ? "no data" : String(g.value),
       g.percentile == null ? "no percentile yet" : String(g.percentile)].forEach(function (v) { tr.appendChild(el("td", null, v)); });
      var bc = el("td"); var bar = el("div", "gb-bar"); var fill = document.createElement("i");
      fill.style.width = (g.percentile == null ? 0 : g.percentile) + "%"; bar.appendChild(fill); bc.appendChild(bar); tr.appendChild(bc);
      tr.appendChild(el("td", null, g.as_of || "absent"));
      tb.appendChild(tr);
    });
    t.appendChild(tb); side.appendChild(t);
    side.appendChild(el("p", "gb-foot", "Median check: the middle two core percentiles averaged give the composite above. Gauges outside the core four stand on their own cards on this page and never enter the composite."));
    wrapG.appendChild(side);
    var h1 = document.querySelector("h1");
    var anchor = document.querySelector(".explblock") || h1;
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(wrapG, anchor.nextSibling);
  }

  /* Sector Rotation (P5): C6 scatter from the page's own two change
     windows, plus quadrant tables whose counts are computed from the
     sectors array, never typed. */
  function rotationScatter(data) {
    if (!data || !Array.isArray(data.sectors) || document.querySelector(".gb-quad")) return;
    var pts = data.sectors.filter(function (s) { return typeof s.avg_change_21_pct === "number" && typeof s.avg_change_5_pct === "number"; });
    if (pts.length < 4) return;
    var card = el("section", "gb-quad");
    card.style.cssText = "background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px;margin:0 0 16px";
    card.appendChild(el("p", "gb-kicker", "Rotation map"));
    card.appendChild(el("p", "gb-sentence", "Each dot is one sector: right means it gained over the last 21 sessions, up means it gained over the last 5. The tables under the map count the sectors in each corner."));
    var maxX = Math.max.apply(null, pts.map(function (p) { return Math.abs(p.avg_change_21_pct); }).concat([1]));
    var maxY = Math.max.apply(null, pts.map(function (p) { return Math.abs(p.avg_change_5_pct); }).concat([1]));
    var W = 640, H = 300, cx = W / 2, cy = H / 2;
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.style.width = "100%"; svg.style.background = "#2a2d3a"; svg.style.borderRadius = "16px";
    function line(x1, y1, x2, y2) { var l = document.createElementNS("http://www.w3.org/2000/svg", "line"); l.setAttribute("x1", x1); l.setAttribute("y1", y1); l.setAttribute("x2", x2); l.setAttribute("y2", y2); l.setAttribute("stroke", "#454a5e"); svg.appendChild(l); }
    line(cx, 8, cx, H - 8); line(8, cy, W - 8, cy);
    [["LEADING", W - 90, 24], ["IMPROVING", 14, 24], ["WEAKENING", W - 104, H - 14], ["LAGGING", 14, H - 14]].forEach(function (q) {
      var tx = document.createElementNS("http://www.w3.org/2000/svg", "text");
      tx.setAttribute("x", q[1]); tx.setAttribute("y", q[2]); tx.setAttribute("fill", "#9aa3b8"); tx.setAttribute("font-size", "12"); tx.setAttribute("font-weight", "700"); tx.textContent = q[0]; svg.appendChild(tx);
    });
    pts.forEach(function (p) {
      var c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      c.setAttribute("cx", cx + (p.avg_change_21_pct / maxX) * (cx - 20)); c.setAttribute("cy", cy - (p.avg_change_5_pct / maxY) * (cy - 20));
      c.setAttribute("r", 6); c.setAttribute("fill", "#7ee0c3");
      var ti = document.createElementNS("http://www.w3.org/2000/svg", "title"); ti.textContent = p.sector + ": 21 sessions " + p.avg_change_21_pct + "%, 5 sessions " + p.avg_change_5_pct + "%"; c.appendChild(ti);
      svg.appendChild(c);
    });
    card.appendChild(svg);
    var groups = { Leading: [], Improving: [], Weakening: [], Lagging: [] };
    pts.forEach(function (p) { var k = p.avg_change_21_pct >= 0 ? (p.avg_change_5_pct >= 0 ? "Leading" : "Weakening") : (p.avg_change_5_pct >= 0 ? "Improving" : "Lagging"); groups[k].push(p); });
    var q = el("div", "gb-q");
    Object.keys(groups).forEach(function (k) {
      var box = el("div", "gb-qbox");
      box.appendChild(el("h4", null, k.toUpperCase() + " " + groups[k].length));
      var t = document.createElement("table");
      groups[k].slice().sort(function (a, b) { return b.avg_change_21_pct - a.avg_change_21_pct; }).forEach(function (p) {
        var tr = document.createElement("tr");
        tr.appendChild(el("td", null, p.sector)); tr.appendChild(el("td", null, p.avg_change_21_pct + "%")); tr.appendChild(el("td", null, p.avg_change_5_pct + "%"));
        t.appendChild(tr);
      });
      if (!groups[k].length) box.appendChild(el("p", "gb-empty", "No sectors in this corner today."));
      else box.appendChild(t);
      q.appendChild(box);
    });
    card.appendChild(q);
    card.appendChild(el("p", "gb-foot", "Columns: sector, change over 21 sessions, change over 5 sessions, from this page's own data (" + ((data.windows && data.windows.sessions_21) ? data.windows.sessions_21.from + " to " + data.windows.sessions_21.to : "window on the page") + "). Counts are counted from the dots, not typed."));
    var h1 = document.querySelector("h1");
    var anchor = document.querySelector(".explblock") || h1;
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(card, anchor.nextSibling);
  }

  /* ============ CURE SECTION (AUDIT 2026-11-02, F1-F9) ============ */
  var P3 = ["breadth-meter","regime-dial","state-analogue","in-regime-oracle","capitulation-clock","fear-day","fear-day-forecaster","fear-day-triangulation","stress-reversal","half-life-clock","mortality-curve","completion-clock"];
  var P2 = ["corrected-band","vol-term-shape","vol-clock","iv-weather","skew-lens","premium-meter","expected-move","market-mood"];
  var P4 = ["tape-heatmap","flow-board","flow-tape","golden-sweep-wire","dark-prints","short-volume","unusual-volume","activity-profile","signal-feed","echo-board","alert-tape","correlation-web","chain-explorer"];
  var P8 = ["greeks-sketch","payoff-sketch"];
  function pageName() { var h = document.querySelector("h1"); return h ? (h.textContent || "").trim() : (document.title || slug); }
  function firstText(sel) { var n = document.querySelector(sel); return n ? (n.textContent || "").trim().replace(/\s+/g, " ") : ""; }

  /* F5 cure: one header date only. The live layer's "Reading as of"
     stamp duplicates (and on market-mood disagreed with) the data's
     own as_of; strip its date, keep its status suffix (Stale/closed). */
  function dedupeLiveStamp() {
    var lt = document.querySelector(".liveind .livetext"); if (!lt) return;
    if (!document.querySelector(".gb-asof")) return;
    var t = lt.textContent || "";
    if (/^Reading as of/.test(t)) lt.textContent = t.replace(/^Reading as of \d{4}-\d{2}-\d{2}\s*/, "").replace(/^·\s*/, "") || "Live status";
    if (/^Updated /.test(t) && !onHub) lt.textContent = "";
  }

  /* F2 cure: C1 eyebrow on every legacy card. Kicker text is the
     card's own section or page name, never invented content. */
  function applyGrammar() {
    var cards = document.querySelectorAll(".card,.chartbox,.verdict,.hubcard,.panel,.sc");
    Array.prototype.forEach.call(cards, function (c) {
      if (c.closest(".gb-fdlg,.gb-disc") || c.querySelector(":scope > .kicker, :scope > .gb-kicker")) return;
      var head = c.querySelector("h2,h3,h4,.t,.name");
      if (!head && !c.classList.contains("hubcard") && !c.classList.contains("card")) return;
      var kick = pageName();
      var sec = c.closest("section"); if (sec) { var sh = sec.querySelector("h2"); if (sh && sh !== head) kick = (sh.textContent || kick).trim(); }
      var k = el("p", "kicker", kick.slice(0, 60)); c.insertBefore(k, c.firstChild);
    });
  }

  /* F2/F1 cure for pages with no .card at all: a C1 lead card built
     only from the page's own heading, explainer sentence and hero. */
  function leadCard(data) {
    if (document.querySelector(".card,.gb-lead") || P8.indexOf(slug) >= 0) return;
    var card = el("section", "card gb-lead");
    card.appendChild(el("p", "kicker", pageName().slice(0, 60)));
    card.appendChild(el("h2", null, pageName()));
    var s = firstText(".explblock p") || firstText(".explblock") || firstText(".sub") || firstText("main p, .wrap p");
    if (s) card.appendChild(el("p", "gb-sentence", s.slice(0, 240)));
    var hero = firstText(".bignum") || firstText(".vvalue") || firstText(".fig");
    if (hero) { var hv = el("p", "gb-hero", hero); card.appendChild(hv); }
    var asOf = asOfOf(data);
    if (asOf) card.appendChild(el("span", "gb-badge " + (isStale(asOf) ? "warn" : "good"), "Data as of " + asOf + (isStale(asOf) ? " (stale)" : "")));
    card.appendChild(el("p", "gb-foot", "Reading built from this page's own data file. The sections below carry the full detail."));
    var anchor = document.querySelector(".gb-jump") || document.querySelector(".topbar");
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(card, anchor.nextSibling);
  }
  function isStale(dstr) { return Math.round((Date.now() - new Date(dstr + "T12:00:00Z").getTime()) / 864e5) >= 4; }

  function numOf(txt) { var m = String(txt == null ? "" : txt).replace(/,/g, "").match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : null; }
  function tableRows() {
    var out = [];
    Array.prototype.forEach.call(document.querySelectorAll("table"), function (t) {
      if (t.closest(".gb-quad,.gb-gaugewrap,.gb-comp,.gb-fdlg")) return;
      var rows = [];
      Array.prototype.forEach.call(t.querySelectorAll("tbody tr, tr"), function (tr) {
        var cells = Array.prototype.map.call(tr.querySelectorAll("td"), function (td) { return (td.textContent || "").trim(); });
        if (cells.length >= 2) rows.push(cells);
      });
      if (rows.length >= 3) out.push(rows);
    });
    return out;
  }
  function compCard(title, sentence) {
    var card = el("section", "card gb-comp");
    card.style.cssText = "background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px;margin:0 0 16px";
    card.appendChild(el("p", "kicker", pageName().slice(0, 60)));
    card.appendChild(el("h2", null, title));
    card.appendChild(el("p", "gb-sentence", sentence));
    return card;
  }
  function placeComp(card) {
    var lead = document.querySelector(".gb-lead") || document.querySelector(".gb-stats") || document.querySelector(".gb-jump") || document.querySelector(".topbar");
    if (lead && lead.parentNode) lead.parentNode.insertBefore(card, lead.nextSibling); else document.body.appendChild(card);
  }
  /* Generic class components (F1) bound from the page's OWN rendered
     tables / data series: ranker rows (C7), heat tiles (C5b), state
     strip (C4), band gauge (C8), agreement bar (C10). One card per
     page, chosen by the SPEC page class; nothing is fabricated: every
     row below is copied from a table or series already on the page. */
  function findRankedArray(data) {
    if (!data || typeof data !== "object") return null;
    var pools = [];
    Object.keys(data).forEach(function (k) { var v = data[k]; if (Array.isArray(v)) pools.push(v); else if (v && typeof v === "object") Object.keys(v).forEach(function (k2) { if (Array.isArray(v[k2])) pools.push(v[k2]); }); });
    var best = null;
    pools.forEach(function (a) {
      if (a.length < 3) return;
      var items = [];
      a.forEach(function (r) {
        if (!r || typeof r !== "object" || Array.isArray(r)) return;
        var label = null; ["symbol", "name", "id", "title", "sector", "holder", "ticker", "label", "session", "date"].forEach(function (k) { if (label == null && r[k] != null && typeof r[k] !== "object") label = String(r[k]); });
        var nums = Object.keys(r).map(function (k) { return r[k]; }).filter(function (v) { return typeof v === "number" && isFinite(v); });
        if (label && nums.length) items.push({ label: label, raw: [label], nums: nums, v: nums[nums.length - 1] });
      });
      if (items.length >= 3 && (!best || items.length > best.length)) best = items;
    });
    return best;
  }
  function buildClassComponent(data) {
    if (document.querySelector(".gb-maincomp") || slug === "sector-rotation") return;
    if (P3.indexOf(slug) >= 0) {
      var series = findSeries(data);
      if (series && series.length >= 5) {
        var vals = series.map(function (p) { return p.v; });
        var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
        var cardS = compCard("History as states", "Each block is one session from this page's own history, coloured from low (pale) to high (dark teal). The current reading is named beside the strip.");
        var strip = el("div", "gb-strip");
        series.slice(-130).forEach(function (p) {
          var q = hi > lo ? (p.v - lo) / (hi - lo) : 0.5;
          var seg = document.createElement("span");
          seg.style.background = ["#dcebe5", "#9fd3c3", "#3d9a84", "#0b3b46"][Math.min(3, Math.floor(q * 4))];
          seg.title = p.d + ": " + p.v; strip.appendChild(seg);
        });
        cardS.classList.add("gb-maincomp"); cardS.appendChild(strip);
        var ax = el("div", "gb-strip-axis"); ax.appendChild(el("span", null, series[0].d)); ax.appendChild(el("span", null, "Current: " + series[series.length - 1].v + " on " + series[series.length - 1].d)); cardS.appendChild(ax);
        cardS.appendChild(el("p", "gb-foot", "Four shades only, low to high; green and red are reserved for returns and are not used here."));
        placeComp(cardS); return;
      }
    }
    var tables = tableRows();
    var parsed = [];
    if (tables.length) {
      parsed = tables[0].map(function (r) {
        var nums = r.map(numOf).filter(function (n) { return n != null; });
        return { label: r[0], raw: r, nums: nums, v: nums.length ? nums[nums.length - 1] : null };
      }).filter(function (r) { return r.v != null && r.label; });
    }
    if (parsed.length < 3) { var fromData = findRankedArray(data); if (fromData) parsed = fromData; }
    if (parsed.length < 3) return;
    var sorted = parsed.slice().sort(function (a, b) { return Math.abs(b.v) - Math.abs(a.v); });
    if (P4.indexOf(slug) >= 0 && parsed.length >= 8) {
      var cardH = compCard("Tile view", "The same rows as the table below, as tiles: the label, the headline value, and the reading it came from.");
      var heat = el("div", "gb-heat gb-tile-wrap");
      var mx = Math.max.apply(null, parsed.map(function (r) { return Math.abs(r.v); }).concat([1]));
      parsed.slice(0, 24).forEach(function (r) {
        var t = el("div", "gb-tile");
        var q = r.v / mx; t.style.background = q >= 0 ? "hsl(152,45%," + (92 - Math.abs(q) * 34) + "%)" : "hsl(4,55%," + (94 - Math.abs(q) * 30) + "%)";
        t.appendChild(el("p", "s", r.label.slice(0, 14))); t.appendChild(el("p", "v", String(r.v))); t.appendChild(el("p", "u", (r.raw[1] || "").slice(0, 18)));
        heat.appendChild(t);
      });
      cardH.classList.add("gb-maincomp"); cardH.appendChild(heat); placeComp(cardH); return;
    }
    /* C10 agreement bar when a row set is percentages summing to ~100 */
    var pctRows = parsed.filter(function (r) { return r.v >= 0 && r.v <= 100; });
    if (pctRows.length >= 2) {
      var sum = pctRows.reduce(function (a, r) { return a + r.v; }, 0);
      if (sum >= 90 && sum <= 110 && (slug === "living-router" || slug === "portfolio-builder" || slug === "router")) {
        var cardA = compCard("Shares at a glance", "One bar, split by the shares in the table below. The key names every part and its value.");
        var bar = el("div", "gb-allocbar"); var key = el("div", "gb-key");
        var cols = ["#177366", "#3d3a8c", "#d9a441", "#7ee0c3", "#b0342e", "#5b6b75"];
        pctRows.slice(0, 6).forEach(function (r, i) {
          var seg = document.createElement("i"); seg.style.width = (r.v / sum * 100) + "%"; seg.style.background = cols[i % cols.length]; bar.appendChild(seg);
          var k = el("span"); var sw = el("span", "sw"); sw.style.background = cols[i % cols.length]; k.appendChild(sw); k.appendChild(document.createTextNode(r.label + " " + r.v)); key.appendChild(k);
        });
        cardA.classList.add("gb-maincomp"); cardA.appendChild(bar); cardA.appendChild(key); placeComp(cardA); return;
      }
    }
    var cardR = compCard("Ranked rows, with their working", "The top rows from this page's own table, ranked by the headline value. The bar is that value against the largest on the page; the small bars are the row's other numbers.");
    var maxV = Math.max.apply(null, sorted.map(function (r) { return Math.abs(r.v); }).concat([1]));
    sorted.slice(0, 8).forEach(function (r, i) {
      var row = el("div", "gb-rkrow");
      row.appendChild(el("span", "r", String(i + 1)));
      var mid = el("div"); mid.appendChild(el("span", "id", r.label.slice(0, 28)));
      var bar = el("div", "gb-rkbar"); var fill = document.createElement("i"); fill.style.width = Math.max(2, Math.abs(r.v) / maxV * 100) + "%"; bar.appendChild(fill); mid.appendChild(bar);
      if (r.nums.length > 1) { var mini = el("div", "gb-rkmini"); r.nums.slice(0, 3).forEach(function (n) { var mi = document.createElement("i"); mi.style.width = Math.max(4, Math.min(60, Math.abs(n) / maxV * 60)) + "px"; mini.appendChild(mi); }); mid.appendChild(mini); }
      row.appendChild(mid);
      row.appendChild(el("span", "val", String(r.v)));
      row.appendChild(el("span", "d", r.nums.length > 1 ? String(r.nums[0]) : ""));
      cardR.appendChild(row);
    });
    cardR.classList.add("gb-maincomp"); cardR.appendChild(el("p", "gb-foot", "Copied from the table on this page at render time; the table below stays the record."));
    placeComp(cardR);
    if (P2.indexOf(slug) >= 0) bandGauge(cardR);
  }
  function bandGauge(after) {
    var hero = numOf(firstText(".bignum") || firstText(".vvalue") || firstText(".fig") || firstText(".gb-big"));
    if (hero == null || hero < 0 || hero > 100 || document.querySelector(".gb-band")) return;
    var wrap = el("div");
    var band = el("div", "gb-band");
    band.style.background = "linear-gradient(90deg,#18744f 0%,#a8d8c0 33%,#f2c14e 66%,#b0342e 100%)";
    var peg = el("span", "peg"); peg.style.left = "calc(" + hero + "% - 2px)"; band.appendChild(peg); wrap.appendChild(band);
    var ticks = el("div", "gb-band-ticks"); ["0", "25", "50", "75", "100"].forEach(function (t) { ticks.appendChild(el("span", null, t)); }); wrap.appendChild(ticks);
    var word = hero < 25 ? "Calm" : hero < 50 ? "Normal" : hero < 75 ? "Elevated" : "Stressed";
    wrap.appendChild(el("p", "gb-verdict", word + " · " + hero));
    wrap.appendChild(el("p", "gb-foot", "The word is the reading's place on its own 0 to 100 scale: under 25 calm, under 50 normal, under 75 elevated, above that stressed."));
    after.appendChild(wrap);
  }
  function findSeries(data) {
    if (!data) return null;
    var cands = [data.history, data.series, data.state && data.state.history, data.record_surface && data.record_surface.series];
    Object.keys(data).forEach(function (k) { var v = data[k]; if (Array.isArray(v)) cands.push(v); else if (v && typeof v === "object") Object.keys(v).forEach(function (k2) { if (Array.isArray(v[k2])) cands.push(v[k2]); }); });
    for (var i = 0; i < cands.length; i++) {
      var a = cands[i]; if (!Array.isArray(a) || a.length < 5) continue;
      var pts = [];
      a.forEach(function (r) {
        if (!r || typeof r !== "object") return;
        var d = r.session || r.date || r.x; if (!d) return;
        var v = null; ["above_200_pct", "value", "v", "y", "pct", "percentile", "close"].forEach(function (k) { if (v == null && typeof r[k] === "number") v = r[k]; });
        if (v != null) pts.push({ d: String(d).slice(0, 10), v: v });
      });
      if (pts.length >= 5) return pts;
    }
    return null;
  }
  /* F3 cure: universal atoms. Disclosure on every page (honest,
     generic, dated from the page's own as_of), empty states where a
     table genuinely has no rows, tabs on the two calculators. */
  function universalAtoms(data) {
    var wrap = document.querySelector(".wrap") || document.querySelector("main") || document.body;
    if (!document.querySelector(".gb-disc")) {
      var asOf = asOfOf(data);
      var disc = el("section", "gb-disc");
      var b = el("b", null, "What this leaves out. "); disc.appendChild(b);
      disc.appendChild(document.createTextNode("This page shows only what its own data file publishes" + (asOf ? ", as of " + asOf : "") + ". Anything that file does not carry is not shown here, and no number is borrowed from another page or from the reference terminal."));
      wrap.appendChild(disc);
    }
    Array.prototype.forEach.call(document.querySelectorAll("table"), function (t) {
      if (t.closest(".gb-comp,.gb-disc")) return;
      var body = t.querySelector("tbody") || t;
      if (!body.querySelector("tr td") && !t.querySelector(".gb-empty")) { var e = el("p", "gb-empty", "No rows in this reading."); t.parentNode.insertBefore(e, t.nextSibling); }
    });
    if (P8.indexOf(slug) >= 0 && !document.querySelector(".gb-tabs")) {
      var tabs = el("div", "gb-tabs");
      var discEl = document.querySelector(".gb-disc");
      [["Inputs", true], ["What this leaves out", false]].forEach(function (pair) {
        var tb = el("button", "gb-tab" + (pair[1] ? " on" : ""), pair[0]); tb.type = "button";
        tb.addEventListener("click", function () {
          Array.prototype.forEach.call(tabs.querySelectorAll(".gb-tab"), function (x) { x.classList.remove("on"); }); tb.classList.add("on");
          if (discEl) discEl.style.display = pair[1] ? "none" : "";
          if (!pair[1] && discEl) discEl.scrollIntoView({ block: "nearest" });
        });
        tabs.appendChild(tb);
      });
      if (discEl) discEl.style.display = "none";
      var h1 = document.querySelector("h1"); if (h1 && h1.parentNode) h1.parentNode.insertBefore(tabs, h1.nextSibling);
      if (!document.querySelector(".gb-empty")) { var pe = el("p", "gb-empty", "You supply the inputs: this tool has no stored reading, so there is no date to show and nothing is pre-filled."); tabs.parentNode.insertBefore(pe, tabs.nextSibling); }
    }
  }
  /* market-mood extras (AUDIT row): C8 band for the VIX input, named
     beside the recipe; the oldest ingredient is flagged in the card. */
  function moodExtras(data) {
    if (!data || !data.state || document.querySelector(".gb-moodband")) return;
    var vix = data.state.vix_close_latest; if (typeof vix !== "number") return;
    var card = compCard("Volatility band", "The latest VIX close on its own scale, with the word for where it sits.");
    card.classList.add("gb-moodband");
    var band = el("div", "gb-band"); band.style.background = "linear-gradient(90deg,#18744f 0%,#a8d8c0 40%,#f2c14e 70%,#b0342e 100%)";
    var peg = el("span", "peg"); peg.style.left = "calc(" + Math.max(0, Math.min(100, (vix - 10) / 30 * 100)) + "% - 2px)"; band.appendChild(peg); card.appendChild(band);
    var word = vix < 17 ? "Calm" : vix < 25 ? "Normal" : vix < 32 ? "Elevated" : "Stressed";
    card.appendChild(el("p", "gb-verdict", word + " · VIX " + vix));
    var dates = Object.keys(data.state.gauges || {}).map(function (k) { return data.state.gauges[k].as_of; }).filter(Boolean).sort();
    if (dates.length) card.appendChild(el("p", "gb-foot", "Scale 10 to 40. Oldest ingredient in the composite: " + dates[0] + " (named here because the header carries the composite's own date, " + (data.state.date || "") + ")."));
    placeComp(card);
  }
  /* breadth-meter F9 cure: name both series on the lead card so the
     hero (above-50 share) and the chart (above-200 share) can never
     read as a disagreement. */
  function breadthNote(data) {
    if (!data || !data.headline || document.querySelector(".gb-breadth-note")) return;
    var h = data.headline; if (typeof h.above_50_pct !== "number" || typeof h.above_200_pct !== "number") return;
    var card = compCard("Two averages, two numbers", "This page tracks two different shares, and they are not supposed to match: the share above the 50-session average and the share above the 200-session average.");
    card.classList.add("gb-breadth-note");
    card.appendChild(el("p", "gb-hero", h.above_200_pct + "%"));
    card.appendChild(el("p", "gb-hero-sub", "Above the 200-session average on " + (h.session || data.session || "") + ": this is the series the history chart plots. Above the 50-session average: " + h.above_50_pct + "%."));
    placeComp(card);
  }
  /* desk C7 cure: ranker rows of the open positions by quantity
     (the only honest ranking the desk data publishes). */
  function deskRanker(data) {
    if (!data || !Array.isArray(data.positions) || !data.positions.length || document.querySelector(".gb-comp")) return;
    var card = compCard("Open positions, ranked by quantity", "Every open position on the desk, largest quantity first. Quantity is the only size the desk feed publishes, so no weights are drawn.");
    var mx = Math.max.apply(null, data.positions.map(function (p) { return Math.abs(p.qty || 0); }).concat([1]));
    data.positions.slice().sort(function (a, b) { return Math.abs(b.qty) - Math.abs(a.qty); }).forEach(function (p, i) {
      var row = el("div", "gb-rkrow");
      row.appendChild(el("span", "r", String(i + 1))); row.appendChild(el("span", "id", p.symbol || ""));
      var bar = el("div", "gb-rkbar"); var f = document.createElement("i"); f.style.width = Math.max(2, Math.abs(p.qty || 0) / mx * 100) + "%"; bar.appendChild(f); row.appendChild(bar);
      row.appendChild(el("span", "val", String(p.qty)));
      card.appendChild(row);
    });
    placeComp(card);
  }
  /* hub cure: date the hero stats from the newest dated card on the
     hub itself, and give hub cards their family eyebrow (in grammar). */
  function hubDates() {
    var grid = document.querySelector(".gb-stats"); if (!grid || grid.querySelector(".gb-asofline")) return;
    var dates = (document.body.textContent.match(/20\d\d-\d\d-\d\d/g) || []).sort();
    if (!dates.length) return;
    var line = el("p", "gb-asofline gb-foot", "Counts read from the hub's own cards; the newest card on this page is dated " + dates[dates.length - 1] + ", and every card below carries its own date.");
    grid.parentNode.insertBefore(line, grid.nextSibling);
  }

  whenReady(function () {
    /* F6 cure: the shell (topbar, finder, pills) renders immediately;
       the data fetch now only fills the as_of stamp and components,
       so a 35 MB data.json can no longer delay the chrome. */
    try { shell(null); } catch (e) {}
    try { jumpPills(); } catch (e) {}
    try { applyGrammar(); } catch (e) {}
    loadData(function (data) {
      try { shell(data); } catch (e) {}
      try { dedupeLiveStamp(); } catch (e) {}
      try { if (onHub) { hubHero(); hubDates(); } } catch (e) {}
      try { if (slug === "desk") { deskHero(data); deskRanker(data); } } catch (e) {}
      try { if (slug === "market-mood") { moodRecipe(data); moodExtras(data); } } catch (e) {}
      try { if (slug === "sector-rotation") rotationScatter(data); } catch (e) {}
      try { if (slug === "breadth-meter") breadthNote(data); } catch (e) {}
      try { leadCard(data); } catch (e) {}
      try { buildClassComponent(data); } catch (e) {}
      try { universalAtoms(data); } catch (e) {}
      try { applyGrammar(); } catch (e) {}
      /* pages render their own tables async; re-run the DOM-bound
         cures twice so late cards/tables get the same treatment */
      [1200, 3000].forEach(function (ms) { setTimeout(function () {
        try { applyGrammar(); } catch (e) {}
        try { buildClassComponent(data); } catch (e) {}
        try { universalAtoms(data); } catch (e) {}
        try { dedupeLiveStamp(); } catch (e) {}
      }, ms); });
    });
  });
})();
