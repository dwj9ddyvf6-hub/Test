/* GrokBot design shell for the Master edition (R2 + R2-CURE 2026-11-02).
   Injected by the mirror's publish step (mirror_master.py), the lane
   that produces the master/ pages. Presentation only, from the app's
   OWN rendered DOM: kickers copy each card's own heading, sentences
   and heroes copy the card's own text, the stat strip counts the
   view's own cards and table rows. No data is read from anywhere
   else and no number is invented. */
(function () { "use strict";
function ready(f) { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", f); else f(); }
function el(tag, cls, txt) { var n = document.createElement(tag); if (cls) n.className = cls; if (txt != null) n.textContent = txt; return n; }
var VIEWS = [["market", "Market"], ["desk", "Desk"], ["engine", "Engine"], ["lineup", "Lineup"], ["record", "Record"], ["brief", "Brief"], ["hub", "Hub"], ["how", "How it works"]];
function viewOf() { var h = (location.hash || "").replace(/^#\/?/, "").split("/")[0]; return h || "market"; }
ready(function () {
  if (!document.querySelector(".gb-mbar")) {
    var b = el("div", "gb-mbar");
    b.appendChild(el("span", "gb-dot"));
    b.appendChild(el("span", null, "Master Terminal"));
    var a1 = el("a", null, "Combined terminal"); a1.href = "../"; b.appendChild(a1);
    var a2 = el("a", null, "Engines and Tools"); a2.href = "../terminal-lineup/site/"; b.appendChild(a2);
    var fb = el("button", "gb-mfind-btn", "Find ( / )"); fb.type = "button"; b.appendChild(fb);
    document.body.insertBefore(b, document.body.firstChild);
    fb.addEventListener("click", openFinder);
  }
  /* C12 pill tabs: one per app view, active follows the hash. */
  if (!document.querySelector(".gb-mtabs")) {
    var tabs = el("nav", "gb-mtabs");
    VIEWS.forEach(function (v) { var a = el("a", "gb-mtab", v[1]); a.href = "#" + v[0]; a.setAttribute("data-view", v[0]); tabs.appendChild(a); });
    var bar = document.querySelector(".gb-mbar"); if (bar && bar.parentNode) bar.parentNode.insertBefore(tabs, bar.nextSibling);
  }
  /* C13 jump pills: built from the current view's own section headings. */
  function jumpPills() {
    var old = document.querySelector(".gb-mjump"); if (old) old.remove();
    var heads = document.querySelectorAll("main h2, .view h2, section h2, h2");
    if (heads.length < 3) return;
    var row = el("div", "gb-mjump");
    Array.prototype.forEach.call(heads, function (h, i) {
      var host = h.closest("section,article,div"); if (!host) return;
      if (!host.id) host.id = "gb-sec-" + viewOf() + "-" + i;
      var a = el("a", "gb-mpill", (h.textContent || "").trim().slice(0, 28)); a.href = "#" + host.id; row.appendChild(a);
    });
    if (!row.children.length) return;
    var tabs = document.querySelector(".gb-mtabs"); if (tabs && tabs.parentNode) tabs.parentNode.insertBefore(row, tabs.nextSibling);
  }
  /* C2 hero strip for the view: counts of the view's own cards and
     table rows, plus its first big figure, all read from the DOM. */
  function statsStrip() {
    var old = document.querySelector(".gb-mstats"); if (old) old.remove();
    var cards = document.querySelectorAll(".card,.panel,.tile,.read,section");
    var rows = document.querySelectorAll("table tbody tr");
    if (!cards.length && !rows.length) return;
    var strip = el("div", "gb-mstats");
    function stat(label, value, sub, dark) {
      var d = el("div", "gb-mstat" + (dark ? " dark" : ""));
      d.appendChild(el("p", "gb-mslabel", label)); d.appendChild(el("p", "gb-msvalue", value)); if (sub) d.appendChild(el("p", "gb-mssub", sub));
      strip.appendChild(d);
    }
    stat("View", viewOf().slice(0, 18), "Master Terminal", true);
    stat("Cards on this view", String(cards.length), "Counted from the rendered view");
    stat("Table rows", String(rows.length), "Counted from the rendered view");
    var big = document.querySelector(".bignum,.vvalue,.fig,.big");
    if (big && (big.textContent || "").trim()) stat("Lead figure", (big.textContent || "").trim().slice(0, 24), "The view's own first big figure");
    var tabs = document.querySelector(".gb-mjump") || document.querySelector(".gb-mtabs") || document.querySelector(".gb-mbar");
    if (tabs && tabs.parentNode) tabs.parentNode.insertBefore(strip, tabs.nextSibling);
  }
  /* C1 grammar per card: kicker = the card's OWN heading (never the
     page title), sentence = its own first paragraph, hero = its own
     first big figure, footnote names the source. data-gb-full is
     stamped only when all three parts are really on the card. */
  function grammar() {
    Array.prototype.forEach.call(document.querySelectorAll(".card,.panel,.tile,.read,.view section,section.card"), function (c) {
      if (c.closest(".gb-mbar,.gb-mtabs,.gb-mstats,.gb-fdlg") || c.hasAttribute("data-gb-full")) return;
      var h = c.querySelector("h1,h2,h3,h4"); if (!h) return;
      if (!c.querySelector(":scope > .gb-kicker")) { var k = el("p", "gb-kicker", (h.textContent || "").trim().slice(0, 60)); c.insertBefore(k, c.firstChild); }
      if (!c.querySelector(":scope > .gb-sentence")) {
        var p = c.querySelector("p:not(.gb-kicker)");
        if (p && (p.textContent || "").trim().length > 12) { var s = el("p", "gb-sentence", (p.textContent || "").trim().replace(/\s+/g, " ").slice(0, 220)); if (h.nextSibling) c.insertBefore(s, h.nextSibling); }
      }
      if (!c.querySelector(":scope > .gb-hero")) {
        var hv = c.querySelector(".bignum,.vvalue,.fig,.big,strong,b");
        if (hv && /\d/.test(hv.textContent || "") && (hv.textContent || "").trim().length <= 32) { var he = el("p", "gb-hero", (hv.textContent || "").trim().slice(0, 40)); var se = c.querySelector(":scope > .gb-sentence"); if (se && se.nextSibling) c.insertBefore(he, se.nextSibling); }
      }
      if (!c.querySelector(":scope > .gb-foot")) c.appendChild(el("p", "gb-foot", "From this view's own data. The table or chart in this card is the record."));
      if (c.querySelector(":scope > .gb-sentence") && c.querySelector(":scope > .gb-hero") && c.querySelector(":scope > .gb-foot")) c.setAttribute("data-gb-full", "1"); else c.setAttribute("data-gb-partial", "1");
    });
    Array.prototype.forEach.call(document.querySelectorAll(".gb-mtab"), function (t) { t.classList.toggle("on", t.getAttribute("data-view") === viewOf()); });
  }
  /* C18 finder: dialog over the app's own views and section headings. */
  function openFinder() {
    var old = document.querySelector(".gb-fdlg"); if (old) { old.remove(); return; }
    var dlg = el("div", "gb-fdlg gb-mfinder");
    var panel = el("div", "gb-fpanel");
    var inp = el("input", "gb-finput"); inp.type = "search"; inp.placeholder = "Search views and sections"; panel.appendChild(inp);
    var list = el("div", "gb-flist"); panel.appendChild(list);
    dlg.appendChild(panel); document.body.appendChild(dlg);
    var items = [];
    VIEWS.forEach(function (v) { items.push({ label: v[1] + " view", href: "#" + v[0] }); });
    Array.prototype.forEach.call(document.querySelectorAll("h2,h3"), function (h) { var host = h.closest("section,article,div"); if (host && host.id) items.push({ label: (h.textContent || "").trim().slice(0, 60), href: "#" + host.id }); });
    function draw(q) {
      list.innerHTML = "";
      items.filter(function (it) { return !q || it.label.toLowerCase().indexOf(q.toLowerCase()) >= 0; }).slice(0, 30).forEach(function (it) { var a = el("a", "gb-fit", it.label); a.href = it.href; a.addEventListener("click", function () { dlg.remove(); }); list.appendChild(a); });
      if (!list.children.length) list.appendChild(el("p", "gb-fempty", "Nothing on this terminal matches that search."));
    }
    inp.addEventListener("input", function () { draw(inp.value); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.remove(); });
    draw(""); inp.focus();
  }
  document.addEventListener("keydown", function (e) { if (e.key === "/" && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); openFinder(); } if (e.key === "Escape") { var d = document.querySelector(".gb-fdlg"); if (d) d.remove(); } });
  function enhance() { grammar(); jumpPills(); statsStrip(); }
  enhance();
  [1200, 3000, 6000].forEach(function (ms) { setTimeout(enhance, ms); });
  var pending = null;
  new MutationObserver(function () { if (pending) return; pending = setTimeout(function () { pending = null; grammar(); }, 400); }).observe(document.body, { childList: true, subtree: true });
  window.addEventListener("hashchange", function () { setTimeout(enhance, 350); });
});
})();
