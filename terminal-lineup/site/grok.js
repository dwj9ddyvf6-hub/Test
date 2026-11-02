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
    ["as_of", "published_at_utc", "generated_at", "session_date", "date"].forEach(function (k) { if (data[k]) cands.push(data[k]); });
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
    if (asOf && !bar.querySelector(".gb-asof")) {
      var ageDays = Math.max(0, Math.round((Date.now() - new Date(asOf + "T12:00:00Z").getTime()) / 864e5));
      var cls = ageDays <= 3 ? "live" : (ageDays > 14 ? "stale" : "");
      var s = el("span", "gb-asof");
      var dot = el("span", "gb-dot " + cls); s.appendChild(dot);
      s.appendChild(document.createTextNode("Data as of " + asOf + (cls === "stale" ? " (stale)" : "")));
      s.style.cssText = "color:#c9cfdd;font-size:13px";
      bar.appendChild(s);
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
  function jumpPills() {
    var wrap = document.querySelector(".wrap") || document.body;
    var heads = Array.prototype.slice.call(wrap.querySelectorAll("h2")).filter(function (h) { return !h.closest(".related,.gb-fdlg"); });
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

  whenReady(function () {
    loadData(function (data) {
      try { shell(data); } catch (e) {}
      try { jumpPills(); } catch (e) {}
      try { if (onHub) hubHero(); } catch (e) {}
      try { if (slug === "desk") deskHero(data); } catch (e) {}
      try { if (slug === "market-mood") moodRecipe(data); } catch (e) {}
      try { if (slug === "sector-rotation") rotationScatter(data); } catch (e) {}
    });
  });
})();
