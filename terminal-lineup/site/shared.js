/* Shared shell for the whole lineup: top bar, related tools footer,
   verdict strip and progress meter built only from values the page
   itself already publishes. Presentation only. No new data. */
(function () {
  "use strict";
  var path = window.location.pathname;
  // The site is served from its own root: the hub is / or /index.html and
  // each tool is one folder down, /<tool>/ or /<tool>/index.html.
  var parts = path.split("/").filter(Boolean);
  var si = parts.lastIndexOf("site");
  if (si >= 0) parts = parts.slice(si + 1);
  if (parts.length && parts[parts.length - 1] === "index.html") parts.pop();
  var depth = parts.length;
  var root = depth >= 1 ? "../" : "";
  var onHub = depth === 0;

  var wrap = document.querySelector(".wrap") || document.body;

  // Charts-IA (2026-10-31): every page carries the shared chart layer.
  // Pages authored before it load visual.css / visual.js / page_charts.js
  // from here, the one shared source, so a refresh never has to re-add
  // them page by page. Desk stays last in the nav above.
  (function ensureChartAssets() {
    var head = document.head || document.documentElement;
    if (!document.querySelector('link[href$="visual.css"]')) {
      var link = document.createElement("link");
      link.rel = "stylesheet"; link.href = root + "visual.css";
      head.appendChild(link);
    }
    [["visual.js"], ["page_charts.js"], ["explanation.js"], ["live.js"]].forEach(function (pair) {
      var name = pair[0];
      if (!document.querySelector('script[src$="' + name + '"]')) {
        var sc = document.createElement("script");
        sc.src = root + name; sc.async = false;
        head.appendChild(sc);
      }
    });
  })();

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  // Top bar (element 5)
  if (wrap && !document.querySelector(".topbar")) {
    var bar = el("div", "topbar");
    var brand = el("a", "brand", "Free Market Tools");
    brand.href = root + "index.html";
    bar.appendChild(brand);
    var nav = el("nav");
    [["Forecast Engines", root + "index.html#forecast-engines"],
     ["Market Tools", root + "index.html#ready-to-use"],
     ["Modules", root + "index.html#modules"],
     ["The Record", root + "record/"],
     ["Desk", root + "desk/"]].forEach(function (pair) {
      var a = el("a", null, pair[0]); a.href = pair[1]; nav.appendChild(a);
    });
    bar.appendChild(nav);
    var meta = document.querySelector(".meta");
    if (meta && meta.textContent && /20\d\d/.test(meta.textContent)) {
      var m = meta.textContent.match(/[A-Z][a-z]+ \d{1,2}, 20\d\d/);
      if (m) bar.appendChild(el("span", "updated", "Updated " + m[0]));
    }
    wrap.insertBefore(bar, wrap.firstChild);
  }

  // Related tools footer (element 5)
  var RELATED = {
    "morning-map": [["Gamma Ladder", "gamma-ladder/"], ["The Record", "record/"], ["Expected Move Map", "expected-move/"]],
    "gamma-ladder": [["Morning Map", "morning-map/"], ["The Record", "record/"], ["Static GEX Cross-Check", "static-gex/"]],
    "board": [["The Record", "record/"], ["Screener", "screener/"], ["Morning Map", "morning-map/"]],
    "record": [["Qualified Board", "board/"], ["Horizon Grades", "horizon-grades/"], ["Calibration League", "calibration-league/"]],
    "corrected-band": [["Touch Surface", "touch-surface/"], ["The Record", "record/"], ["Exceedance Forecaster", "exceedance/"]],
    "pattern-draw": [["AI Chart Read", "ai-chart-read/"], ["Payoff Sketch", "payoff-sketch/"], ["The Record", "record/"]],
    "payoff-sketch": [["Pattern Draw", "pattern-draw/"], ["Greeks Sketch", "greeks-sketch/"], ["Odds Cards", "odds-cards/"]],
    "tape-heatmap": [["Breadth Meter", "breadth-meter/"], ["Correlation Web", "correlation-web/"], ["Morning Map", "morning-map/"]]
  };
  var slug = depth >= 1 ? parts[parts.length - 1] : "";
  if (!onHub && wrap && !document.querySelector(".related")) {
    var rel = el("div", "related");
    rel.appendChild(el("p", "rlabel", "Related tools"));
    var links = RELATED[slug] || [["Morning Map", "morning-map/"], ["Qualified Board", "board/"], ["The Record", "record/"]];
    links.forEach(function (pair) {
      var a = el("a", null, pair[0]); a.href = root + pair[1]; rel.appendChild(a);
    });
    var back = el("a", null, "All tools"); back.href = root + "index.html"; rel.appendChild(back);
    wrap.appendChild(rel);
  }

  // Verdict strip and progress meter (elements 2 and 3), built after the
  // page's own script has rendered, from values already on the page.
  function normText(e) {
    // innerText keeps the line break between a block-level figure and the
    // words after it; textContent glues them ("4names covered").
    return ((e.innerText != null ? e.innerText : e.textContent) || "").replace(/\s+/g, " ").trim();
  }
  function findValue() {
    var fig = document.querySelector(".fig .value, .grade .big, .summary strong, .card .value, .level .v, .stat .value, .big");
    if (fig && normText(fig) && normText(fig).length <= 80 && /\d/.test(normText(fig))) return normText(fig);
    var alt = document.querySelector(".summary strong, .count, .claim");
    if (alt && normText(alt) && normText(alt).length <= 140 && /\d/.test(normText(alt))) return normText(alt);
    // Generic fallback: the first large, bold, short figure the page itself
    // renders below its header. Presentation of an existing value only.
    var nodes = document.querySelectorAll(".wrap *");
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.closest("header, .verdict, .topbar, .related, .banner, footer")) continue;
      if (n.children.length > 2) continue;
      var t = normText(n);
      if (!t || t.length > 60 || !/\d/.test(t)) continue;
      var cs = window.getComputedStyle(n);
      if (parseFloat(cs.fontSize) >= 17 && parseInt(cs.fontWeight, 10) >= 600) return t;
    }
    return null;
  }
  function addVerdict() {
    if (onHub) return;
    var existing = document.querySelector(".verdict");
    if (existing) {
      if (!existing.querySelector(".vvalue")) {
        var late = findValue();
        if (late) {
          var vv = el("p", "vvalue", late);
          existing.insertBefore(vv, existing.children[1] || null);
        }
      }
      if (!existing.querySelector(".meter")) addMeter(existing);
      return;
    }
    var header = document.querySelector("header");
    if (!header || !wrap.contains(header)) return;
    var job = header.querySelector(".job");
    var value = findValue(), means = job ? job.textContent.trim() : "";
    if (!value) return; // A verdict without the page's own figure would only repeat the job line.
    var v = el("section", "verdict");
    v.appendChild(el("p", "vlabel", "The short answer"));
    v.appendChild(el("p", "vvalue", value));
    if (means) v.appendChild(el("p", "vmeans", means.length > 220 ? means.slice(0, 217).trim() + "." : means));
    header.parentNode.insertBefore(v, header.nextSibling);
    addMeter(v);
  }
  // Progress meter: first "N of M" count the page itself states.
  function addMeter(v) {
    var text = document.body.textContent || "";
    var pm = text.match(/(\d[\d,]*)\s+of\s+(?:its first |the first |a first )?(\d[\d,]*)\s+(forecast days|trading days|days|forecasts|checks|names)/);
    if (pm) {
      var have = parseFloat(pm[1].replace(/,/g, "")), need = parseFloat(pm[2].replace(/,/g, ""));
      if (need > have && need <= 100000) {
        var meter = el("div", "meter");
        var track = el("div", "track");
        var fill = el("div", "fill");
        fill.style.width = Math.max(1, Math.round(100 * have / need)) + "%";
        track.appendChild(fill); meter.appendChild(track);
        var labels = el("div", "mlabels");
        labels.appendChild(el("span", "mvalue", pm[1] + " of " + pm[2] + " " + pm[3] + " so far"));
        labels.appendChild(el("span", null, "Full set: " + pm[2]));
        meter.appendChild(labels);
        v.appendChild(meter);
      }
    }
  }
  // Wide-table cue: any box that scrolls sideways to a table gets a plain
  // hint line above it, unless the page already prints one nearby.
  function addScrollHints() {
    var boxes = document.querySelectorAll("div, section");
    for (var i = 0; i < boxes.length; i++) {
      var b = boxes[i];
      var cs = window.getComputedStyle(b);
      if (cs.overflowX !== "auto" && cs.overflowX !== "scroll") continue;
      if (b.scrollWidth <= b.clientWidth + 4) continue;
      if (!b.querySelector("table")) continue;
      var near = "", sib = b.previousElementSibling, hops = 0;
      while (sib && hops < 3) { near += " " + (sib.textContent || ""); sib = sib.previousElementSibling; hops++; }
      if (/scroll sideways/i.test(near)) continue;
      var walker = document.createTreeWalker(b, NodeFilter.SHOW_TEXT), pre = "";
      while (walker.nextNode()) {
        if (walker.currentNode.parentElement.closest("table")) break;
        pre += " " + walker.currentNode.textContent;
      }
      if (/scroll sideways/i.test(pre)) continue;
      if (b.previousElementSibling && b.previousElementSibling.className === "scrollhint") continue;
      var hint = el("p", "scrollhint", "This table is wide: scroll sideways inside it to see it in full.");
      b.parentNode.insertBefore(hint, b);
    }
  }
  window.addEventListener("load", function () {
    setTimeout(addVerdict, 900); setTimeout(addVerdict, 2400); setTimeout(addVerdict, 4500);
    setTimeout(addScrollHints, 900); setTimeout(addScrollHints, 2400); setTimeout(addScrollHints, 4500);
    setTimeout(addScrollHints, 8000); setTimeout(addScrollHints, 13000);
    // Pages render their figures from data after load, at their own pace.
    // Keep trying while the page is still changing, for up to 20 seconds.
    var deadline = Date.now() + 20000, pending = null;
    var obs = new MutationObserver(function () {
      if (document.querySelector(".verdict .vvalue")) { obs.disconnect(); return; }
      if (Date.now() > deadline) { obs.disconnect(); return; }
      if (pending) return;
      pending = setTimeout(function () { pending = null; addVerdict(); addScrollHints(); }, 400);
    });
    obs.observe(document.body, { childList: true, subtree: true, characterData: true });
    setTimeout(function () { obs.disconnect(); }, 21000);
  });
})();
