/* Midna's Book strip: renders the book's own record, written by
   refresh_book_strip.py into book-strip/data.json, into the hub's
   first section. Presentation only: every word and figure comes
   from that data file, which comes from the book's ledger and
   journal. If the data file cannot be loaded, the section says so
   plainly instead of showing nothing or something old. */
(function () {
  "use strict";
  var sec = document.getElementById("book-strip");
  if (!sec) return;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function showUnavailable(words) {
    sec.textContent = "";
    sec.appendChild(el("p", "bs-title", "Midna's Book"));
    sec.appendChild(el("p", "bs-note", words));
  }

  fetch("book-strip/data.json", { cache: "no-store" })
    .then(function (r) {
      if (!r.ok) throw new Error("http " + r.status);
      return r.json();
    })
    .then(function (d) {
      if (d.state === "unavailable") {
        showUnavailable(d.unavailable_line ||
          "Book data unavailable. No figures are shown rather than old ones.");
        return;
      }
      sec.textContent = "";
      sec.appendChild(el("p", "bs-title", d.title || "Midna's Book"));
      sec.appendChild(el("p", "bs-note", d.simulated_note || ""));
      sec.appendChild(el("p", "bs-stats", d.equity_line || ""));
      sec.appendChild(el("p", "bs-perf", d.performance_line || ""));

      sec.appendChild(el("p", "bs-h", "Open positions"));
      if (d.positions && d.positions.length) {
        var ul = el("ul");
        d.positions.forEach(function (p) {
          ul.appendChild(el("li", null, p.line));
        });
        sec.appendChild(ul);
      } else {
        sec.appendChild(el("p", null, d.positions_line ||
          "No open positions."));
      }

      sec.appendChild(el("p", "bs-h", "Live cards: waiting on a price"));
      if (d.cards && d.cards.length) {
        var ul2 = el("ul");
        d.cards.forEach(function (c) {
          ul2.appendChild(el("li", null, c.line));
        });
        sec.appendChild(ul2);
      } else {
        sec.appendChild(el("p", null, d.cards_line ||
          "No live cards right now."));
      }

      sec.appendChild(el("p", "bs-h", "Latest actions"));
      if (d.actions && d.actions.length) {
        var ul3 = el("ul");
        d.actions.forEach(function (a) {
          ul3.appendChild(el("li", null, a.when + ": " + a.line));
        });
        sec.appendChild(ul3);
      } else {
        sec.appendChild(el("p", null, d.actions_line ||
          "No fills or exits yet."));
      }

      sec.appendChild(el("p", "bs-src", d.source_line || ""));
    })
    .catch(function () {
      showUnavailable("Book data unavailable: the book's record " +
        "could not be loaded just now. No figures are shown rather " +
        "than old ones.");
    });
})();
