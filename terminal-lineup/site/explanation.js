/* Collapsed explanation block (2026-10-31, final form). Loaded by
   shared.js on every page. One job: under the page title, add exactly
   one details block, closed by default, with no heading, title or
   label on it. The visible line is the page's own plain sentence
   stating what the thing is (data.json "explanation", built by
   explanation.py from the page's own job line and record; for the
   forecast engines the fuller text comes from the forecast registry).
   The two calculator pages carry no data.json, so their sentences are
   built here from their own pages' job lines, word for word. The
   chart still leads: this block sits under the title, above nothing
   else, and never replaces a chart. */
(function () {
  "use strict";
  var FALLBACK = {
    "greeks-sketch": {
      summary: "Set up one option and see what it is worth, and the four measures that say how its price moves.",
      body: "Change the option set up on this page and the value and the four measures are worked out again from the figures you put in. The drawn curves on this page are the record: they show the worked example as it stands, and they move when the set up moves."
    },
    "payoff-sketch": {
      summary: "Build any options position of up to four parts and see what it makes or loses at every stock price when it expires.",
      body: "Add up to four parts to the position on this page and the drawn payoff shows what the whole position makes or loses at each stock price at expiry. The drawing is the record: it is worked out from the parts you put in, and it changes when they change."
    }
  };
  function slugOf() {
    var parts = window.location.pathname.split("/").filter(Boolean);
    var si = parts.lastIndexOf("site"); if (si >= 0) parts = parts.slice(si + 1);
    if (parts.length && parts[parts.length - 1] === "index.html") parts.pop();
    return parts.length ? parts[parts.length - 1] : "";
  }
  function render(block) {
    if (!block || !block.summary || !block.body) return;
    if (document.getElementById("explBlock")) return;
    var header = document.querySelector("header");
    var h1 = document.querySelector("h1");
    var anchor = header || h1;
    if (!anchor || !anchor.parentNode) return;
    var det = document.createElement("details");
    det.className = "explblock";
    det.id = "explBlock";
    var sum = document.createElement("summary");
    sum.textContent = block.summary;
    det.appendChild(sum);
    var p = document.createElement("p");
    p.className = "explbody";
    p.textContent = block.body;
    det.appendChild(p);
    anchor.parentNode.insertBefore(det, anchor.nextSibling);
  }
  function whenReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }
  function load() {
    var slug = slugOf();
    if (!slug) return; // the hub is not a tool page
    if (FALLBACK[slug]) { render(FALLBACK[slug]); return; }
    fetch("data.json", { cache: "no-store" }).then(function (r) {
      return r.ok ? r.json() : null;
    }).then(function (data) {
      if (data) render(data.explanation);
    }).catch(function () { /* no block rather than a wrong one */ });
  }
  /* Liveness (2026-10-31): live.js data changes also refresh this
     block in place; the one-block invariant is kept by removing the
     old block first (render() also guards on the id). */
  window.__explanationRerender = function () {
    var old = document.getElementById("explBlock");
    if (old) old.remove();
    load();
  };
  whenReady(load);
})();
