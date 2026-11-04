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
    /* Code links (2026-11-04): the three public repositories behind this
       terminal, in the master bar beside the terminal links. */
    [["InfinityBlade", "https://github.com/dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine"],
     ["Edge", "https://github.com/dwj9ddyvf6-hub/Edge"],
     ["Test", "https://github.com/dwj9ddyvf6-hub/Test"]].forEach(function (pair) {
      var a = el("a", null, pair[0]); a.href = pair[1];
      a.target = "_blank"; a.rel = "noopener"; b.appendChild(a);
    });
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
  /* R3-AUDIT cure (row 1): insertAfterChildR3 inserts a node into the
     card c after the card-level child that contains anchor. The old
     code used c.insertBefore(node, h.nextSibling) with h NESTED
     inside the card (read cards: h3.tk inside .top), which throws
     "not a child of this node", aborted the whole grammar pass, and
     left every later card (including lookup read cards) unstamped. */
  function insertAfterChildR3(c, node, anchor) {
    var a = anchor;
    while (a && a.parentNode !== c) a = a.parentNode;
    if (a && a.nextSibling) c.insertBefore(node, a.nextSibling);
    else if (a) c.appendChild(node);
    else if (c.firstChild) c.insertBefore(node, c.firstChild);
    else c.appendChild(node);
  }
  function grammarCardR3(c) {
    try {
      if (c.closest(".gb-mbar,.gb-mtabs,.gb-mstats,.gb-fdlg") || c.hasAttribute("data-gb-full")) return;
      var h = c.querySelector("h1,h2,h3,h4");
      var titleEl = h || c.querySelector(".tk,.tog,.t,.name,.hd,summary,caption");
      var titleTxt = titleEl ? (titleEl.textContent || "").trim().replace(/\s+/g, " ").slice(0, 60) : "";
      if (!titleTxt) { var own0 = (c.textContent || "").replace(/\s+/g, " ").trim(); titleTxt = own0.slice(0, 60); }
      if (!titleTxt) return;
      if (!c.querySelector(":scope > .gb-kicker")) { var k = el("p", "gb-kicker", titleTxt); c.insertBefore(k, c.firstChild); }
      if (!c.querySelector(":scope > .gb-sentence")) {
        var p = c.querySelector("p:not(.gb-kicker):not(.gb-foot)");
        var st = p ? (p.textContent || "").trim().replace(/\s+/g, " ") : "";
        if (st.length <= 12) { var own = (c.textContent || "").replace(/\s+/g, " ").trim(); if (own.indexOf(titleTxt) === 0) own = own.slice(titleTxt.length).trim(); st = own.slice(0, 220); }
        if (st.length > 12) { var s = el("p", "gb-sentence", st.slice(0, 220)); insertAfterChildR3(c, s, h || titleEl); }
      }
      if (!c.querySelector(":scope > .gb-hero")) {
        var hv = c.querySelector(".bignum,.vvalue,.fig,.big,strong,b");
        var heroTxt = "";
        if (hv && /\d/.test(hv.textContent || "") && (hv.textContent || "").trim().length <= 32) heroTxt = (hv.textContent || "").trim().slice(0, 40);
        if (!heroTxt) { var all = (c.textContent || "").replace(/\s+/g, " "); var fm = all.match(/-?\$[\d,]+(\.\d+)?|-?\d[\d,]*\.\d+\s?%|-?\d[\d,]*\.\d+|-?\d[\d,]*\s?%/); if (fm) heroTxt = fm[0].trim().slice(0, 40); }
        if (!heroTxt) { var im = (c.textContent || "").replace(/\s+/g, " ").replace(/\d{4}-\d{2}-\d{2}/g, " ").match(/(?<![\d.,/-])\d{1,6}(?![\d./-])/); if (im) heroTxt = im[0]; }
        if (heroTxt) { var he = el("p", "gb-hero", heroTxt); var se = c.querySelector(":scope > .gb-sentence"); insertAfterChildR3(c, he, se || h || titleEl); }
      }
      if (!c.querySelector(":scope > .gb-foot")) c.appendChild(el("p", "gb-foot", "From this view's own data. The table or chart in this card is the record."));
      /* Exclusive stamps: an upgraded card must not keep its old
         partial stamp (censuses double-counted dual-stamped cards). */
      if (c.querySelector(":scope > .gb-sentence") && c.querySelector(":scope > .gb-hero") && c.querySelector(":scope > .gb-foot")) { c.setAttribute("data-gb-full", "1"); c.removeAttribute("data-gb-partial"); } else { c.setAttribute("data-gb-partial", "1"); c.removeAttribute("data-gb-full"); }
    } catch (e) { /* one bad card never kills the pass for the rest */ }
  }
  function grammar() {
    Array.prototype.forEach.call(document.querySelectorAll(".card,.panel,.tile,.read,.view section,section.card"), grammarCardR3);
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
  /* Withdrawal tombstones (MASTER-TOMBSTONE-RENDER-20261104): on this
     public mirror the desk and reads data files are deliberate
     withdrawal tombstones (schema "withdrawal-tombstone/1"), not data,
     and the app reads each one as a failure: the Desk view ends at
     "The desk's numbers could not be loaded." with a retry that can
     never work, the header status repeats the can't-reach line, the
     Chart Read Engine ends at "No roster reads on file yet.", and the
     Look up donut draws "0 stocks". A deliberate removal rendered as
     a load failure reads as a broken product. This pass probes a file
     ONLY when its broken state is on screen, and only when the
     payload really is a tombstone replaces that state with a plain
     withdrawal note carrying the payload's own date. A live payload
     or a failed probe changes nothing: real load failures keep the
     app's own error states. */
  var TB = {};        /* key -> "tombstone" | "clear" | "probing" */
  var TB_REASON = {}; /* key -> the payload's own reason text */
  var TB_FILE = { edition: "edition.json", desk: "deskview.json", reads: "reads-index.json" };
  var TB_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  function tbWhen(key) {
    var m = /(\d{4})-(\d{2})-(\d{2})/.exec(TB_REASON[key] || "");
    return m ? TB_MONTHS[Number(m[2]) - 1] + " " + Number(m[3]) + ", " + m[1] : "";
  }
  function tbProbe(key) {
    if (TB[key] || typeof fetch !== "function") return;
    TB[key] = "probing";
    fetch(TB_FILE[key], { cache: "no-cache" }).then(function (r) { return r.json(); }).then(function (j) {
      if (j && j.schema === "withdrawal-tombstone/1" && j.withdrawn === true) { TB[key] = "tombstone"; TB_REASON[key] = String(j.reason || ""); }
      else TB[key] = "clear";
      tbApply();
    }).catch(function () { TB[key] = "clear"; });
  }
  function tbNote(lead, body) {
    var box = el("div", "gb-tomb");
    box.appendChild(el("p", "gb-tomb-lead", lead));
    box.appendChild(el("p", "gb-tomb-body", body));
    return box;
  }
  function tbApply() {
    /* Guarded like the grammar pass: this pass never breaks the shell. */
    try { tbApplyInner(); } catch (e) { /* presentation only */ }
  }
  function tbApplyInner() {
    /* Header: while its edition never loads, the app repaints its
       can't-reach line into #st1 and #load on a 15 s cycle; correct
       the text each time it reappears and retire the banner. */
    var st1 = document.getElementById("st1"), load = document.getElementById("load");
    function cantReach(n) { return !!n && /reach the desk/.test(n.textContent || ""); }
    if (TB.edition === "tombstone") {
      var whenE = tbWhen("edition");
      if (cantReach(st1)) st1.textContent = "Desk data removed from this public site" + (whenE ? " on " + whenE : "") + ".";
      if (load && !load.hidden) load.hidden = true;
    } else if (cantReach(st1) || cantReach(load)) tbProbe("edition");
    /* Desk view: #d-wait is the app's loading and error card inside
       #p-desk; while deskview.json is a tombstone it can only ever
       end at the error text, so the card carries the withdrawal note
       instead, with no retry button: there is nothing to retry. */
    var dw = document.getElementById("d-wait"), dp = document.getElementById("p-desk");
    if (dw && TB.desk === "tombstone") {
      if (!dw.querySelector(".gb-tomb")) {
        var whenD = tbWhen("desk");
        dw.innerHTML = "";
        dw.appendChild(tbNote("This view's data was withdrawn.", "The desk's account data was removed from the public site" + (whenD ? " on " + whenD : "") + ". A cleaned-up edition may be published here later."));
        dw.setAttribute("data-gb-full", "1");
      }
    } else if (dw && dp && (!dp.hidden || /could not be loaded/.test(dw.textContent || ""))) tbProbe("desk");
    /* The Chart Read Engine card and the Look up donut both read
       reads-index.json; a tombstone leaves one at its no-reads note
       and the other at a "0 stocks" donut. */
    var lr = document.getElementById("lu-read"), lv = document.getElementById("lviz");
    if (TB.reads === "tombstone") {
      var whenR = tbWhen("reads");
      var readsBody = "The reads were removed from the public site" + (whenR ? " on " + whenR : "") + ", along with the desk's account data. A cleaned-up edition may be published here later.";
      if (lr && !lr.querySelector(".gb-tomb")) { lr.innerHTML = ""; lr.appendChild(tbNote("The roster reads were withdrawn.", readsBody)); lr.setAttribute("data-gb-full", "1"); }
      if (lv && lv.children.length && !lv.querySelector(".gb-tomb")) { lv.innerHTML = ""; lv.appendChild(tbNote("The roster reads were withdrawn.", readsBody)); }
    } else if ((lr && /No roster reads on file yet/.test(lr.textContent || "")) || (lv && lv.children.length)) tbProbe("reads");
  }
  function enhance() { grammar(); jumpPills(); statsStrip(); tbApply(); }
  enhance();
  [1200, 3000, 6000].forEach(function (ms) { setTimeout(enhance, ms); });
  var pending = null;
  new MutationObserver(function () { if (pending) return; pending = setTimeout(function () { pending = null; enhance(); }, 400); }).observe(document.body, { childList: true, subtree: true });
  window.addEventListener("hashchange", function () { setTimeout(enhance, 350); });
});
})();
