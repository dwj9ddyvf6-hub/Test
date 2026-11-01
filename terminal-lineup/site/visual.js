/* Visual kit for the whole lineup. Loaded after shared.js.
   One renderer per primitive (DESIGN section 4). Every renderer reads only
   its own page data, checks its named fields first, and fails closed to a
   plainly labelled real state visual when the data is waiting, accruing or
   missing. No figure is invented, interpolated or borrowed from another page.
   In the browser the renderers return HTML strings and bind to containers
   carrying a data-vk attribute. Under Node they are exported for tests. */
(function (root) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function num(v) {
    return typeof v === "number" && isFinite(v) ? v : null;
  }
  function fmt(v) {
    var n = num(v);
    if (n == null) return esc(v);
    return String(Math.round(n * 100) / 100);
  }
  function sessionOf(data) {
    // Canonical reading date (freshness cure 2026-10-31): mirrors
    // freshness.py exactly, so the kit stamp, live.js and the hub
    // can never again print different dates for the same page.
    if (!data || typeof data !== "object") return null;
    var rs = data.record_surface && data.record_surface.current_reading;
    if (rs && rs.as_of) return String(rs.as_of);
    var keys = ["as_of_session", "session", "as_of", "freshest_session", "freshest_date", "freshest_day", "freshest_filed", "freshest_snapshot", "modelled_freshest_date", "precomputed_freshest_date", "scored_run_session", "assembled_on", "replay_date", "grading_run_at", "wire_grading_run_at", "second_search_finished", "first_search_finished", "date", "panel_last_session", "readings_through", "newest_source_time", "published_date", "generated_at", "generated_at_utc", "published_at_utc", "recorded_on"];
    for (var i = 0; i < keys.length; i++) if (data[keys[i]]) return String(data[keys[i]]);
    if (Array.isArray(data.names)) {
      var snaps = data.names.map(function (n) { return n && n.snapshot_day ? String(n.snapshot_day) : null; }).filter(Boolean).sort();
      if (snaps.length) return snaps[snaps.length - 1];
    }
    var blocks = [data.state, data.wire];
    for (var b = 0; b < blocks.length; b++) {
      if (!blocks[b]) continue;
      var bk = ["date", "as_of", "grading_run_at"];
      for (var j = 0; j < bk.length; j++) if (blocks[b][bk[j]]) return String(blocks[b][bk[j]]);
    }
    return null;
  }
  /* Titles are claims (repair 2026-10-31, spec 14.1.5, cure class
     C7): a chart heading states the takeaway its own numbers support,
     computed here from the rows being drawn, never written by hand
     per page and never beyond what the data carries. The caller's
     descriptive title stays as the first half; the claim follows. */
  function claimTitle(title, claim) {
    if (!claim) return title || null;
    return title ? title + ": " + claim : claim;
  }
  function topClaim(rows) {
    var best = null;
    (rows || []).forEach(function (r) {
      var s = num(r && r.score);
      if (s != null && (best == null || s > best.score)) best = { name: r.name, score: s };
    });
    return best ? String(best.name) + " is highest at " + fmt(best.score) : null;
  }
  function moveClaim(first, last) {
    var a = num(first), b = num(last);
    if (a == null || b == null) return null;
    if (b > a) return "rose from " + fmt(a) + " to " + fmt(b);
    if (b < a) return "fell from " + fmt(a) + " to " + fmt(b);
    return "ended where it started, at " + fmt(a);
  }
  function receipt(session, drawn, unit, extra) {
    var bits = [];
    if (session) bits.push("Session " + esc(String(session).slice(0, 10)) + ".");
    bits.push(drawn + " " + unit + " drawn.");
    if (extra) bits.push(extra);
    return '<p class="creceipt">' + bits.join(" ") + "</p>";
  }
  function stateCard(words, session, drawn, unit) {
    var w = words || "Nothing is on record yet for this view.";
    return '<div class="statecard vk-state"><p class="vk-statewords">' + esc(w) + "</p></div>" +
      receipt(session, drawn || 0, unit || "items");
  }
  function frame(title, means, body, session, drawn, unit, extra) {
    var h = "";
    if (title) h += "<h3 class='vk-title'>" + esc(title) + "</h3>";
    h += body;
    if (means) h += '<p class="cmeans">' + esc(means) + "</p>";
    h += receipt(session, drawn, unit, extra);
    return h;
  }
  function svgOpen(w, h, label) {
    /* Encoding cure (spec 14.1.6): never stretch a chart to the
       container. preserveAspectRatio="none" distorted every slope
       and arc after the fact; meet keeps the drawn geometry true. */
    return '<svg class="vk-svg" viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + esc(label || "chart") + '" preserveAspectRatio="xMidYMid meet">';
  }

  /* Bullet (2026-10-31, spec 14.2 current-state row + 14.5.1/14.5.2):
     the shared current-state-vs-range component. One linear track:
     named zone bands along a common scale, the value as a length bar,
     an optional benchmark/target tick, the exact value printed as
     digits, the zone named in words (colour is never the only code),
     and a sparkline of the reading's own history when the caller
     hands one in (analog shape + digital value, redundant). Fails
     closed to the state card when value or scale is not on record. */
  function bullet(input) {
    input = input || {};
    var v = num(input.value), lo = num(input.low), hi = num(input.high);
    if (v == null || lo == null || hi == null || hi <= lo) {
      if (input.have != null && input.need != null) return accrual(input);
      if (v != null) return stateCard("A reading is on record (" + fmt(v) + ") but its scale is not stated, so no bullet can be drawn honestly.", input.session, 1, "reading");
      return stateCard(input.words || "No reading with a stated scale is on record yet.", input.session, 0, "readings");
    }
    var zones = (Array.isArray(input.zones) && input.zones.length) ? input.zones : [{ to: hi, label: "" }];
    var frac = Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
    var segs = "", prev = lo, zoneName = "";
    zones.forEach(function (z, i) {
      var to = Math.min(z.to, hi);
      if (to > prev) segs += '<span class="vk-bullet-seg vk-zone-bg-' + (i % 4) + '" style="left:' + (100 * (prev - lo) / (hi - lo)) + "%;width:" + (100 * (to - prev) / (hi - lo)) + '%"></span>';
      if (v >= prev && v <= to && !zoneName) zoneName = z.label || "";
      prev = to;
    });
    var bench = num(input.benchmark != null ? input.benchmark : input.target);
    var tick = bench != null && bench >= lo && bench <= hi
      ? '<span class="vk-bench-mark" style="left:' + (100 * (bench - lo) / (hi - lo)) + '%"></span>' : "";
    var hist = Array.isArray(input.history) ? input.history.filter(function (h) { return num(h && (h.value != null ? h.value : h.y)) != null; }) : [];
    var spark = "";
    if (hist.length >= 2) {
      spark = '<span class="vk-bullet-spark">' + sparkline({ series: hist.map(function (h) { return { date: h.date || "", value: h.value != null ? h.value : h.y }; }), raw: true, width: 220, height: 40 }) + "</span>";
    }
    var inner = '<div class="vk-bullet"><div class="vk-bullet-track">' + segs +
      '<span class="vk-bullet-fill" style="width:' + (Math.round(10000 * frac) / 100) + '%"></span>' + tick + "</div>" +
      '<div class="vk-bullet-scale"><span>' + esc(zones[0].label || "") + " " + fmt(lo) + '</span>' +
      '<span class="vk-bullet-value">' + fmt(v) + (zoneName ? " · " + esc(zoneName) : "") + "</span>" +
      "<span>" + fmt(hi) + " " + esc(zones[zones.length - 1].label || "") + "</span></div>" + spark + "</div>";
    if (input.raw) return inner;
    return frame(claimTitle(input.title, fmt(v) + (zoneName ? ", in the " + zoneName + " zone" : "")), input.label || "The bar shows where the reading sits in its range. The exact value and its zone are printed under the bar.",
      inner, input.session, 1, "reading");
  }

  /* P10 Accrual: the honest state visual, also used standalone. */
  function accrual(input) {
    input = input || {};
    var session = input.session || null;
    if (input.mode === "calendar") return accrualCalendar(input);
    if (input.mode === "timeline") return accrualTimeline(input);
    var have = num(input.have), need = num(input.need);
    if (have == null || need == null || need <= 0) {
      return stateCard(input.words || "The count for this view is not on record yet.", session, 0, "items");
    }
    var unit = input.unit || "items";
    var pct = Math.max(0, Math.min(100, 100 * have / need));
    var ticks = "";
    if (have <= 60 && need <= 60) {
      for (var i = 0; i < need; i++) {
        ticks += '<span class="vk-tick' + (i < have ? " on" : "") + '"></span>';
      }
      ticks = '<div class="vk-ticks">' + ticks + "</div>";
    }
    var body = '<div class="meter vk-accrual"><div class="track"><div class="fill" style="width:' +
      Math.max(have > 0 ? 1 : 0, pct) + '%"></div></div>' +
      '<div class="mlabels"><span class="mvalue">' + fmt(have) + " " + esc(unit) + " on record</span>" +
      "<span>" + fmt(need) + " needed</span></div></div>" + ticks;
    var label = input.label || (fmt(have) + " of " + fmt(need) + " " + unit + " so far");
    return frame(input.title || null, label, body, session, have, unit);
  }
  function accrualCalendar(input) {
    var days = Array.isArray(input.days) ? input.days : [];
    var real = days.filter(function (d) { return d && d.date; });
    if (!real.length) return stateCard(input.words || "No dated days are on record yet.", input.session, 0, "days");
    var max = 0;
    real.forEach(function (d) { var c = num(d.count) || 0; if (c > max) max = c; });
    var cells = real.map(function (d) {
      var c = num(d.count) || 0;
      var cls = c > 0 ? (c >= max * 0.66 ? " vk-cal-hot" : " vk-cal-mid") : "";
      /* Encoding cure (14.1.7/14.5.10): the count itself is printed
         in the cell, not carried by tint or a hover title. */
      return '<span class="vk-cal-cell' + cls + '" title="' + esc(d.date) + '">' + esc(String(d.date).slice(8, 10)) + " · " + fmt(c) + "</span>";
    }).join("");
    var body = '<div class="vk-cal">' + cells + "</div>";
    return frame(input.title || null, input.label || "One cell per day in the window on record. Each cell prints its day and its count; tint only repeats the count.",
      body, input.session, real.length, "days");
  }
  function accrualTimeline(input) {
    var events = (Array.isArray(input.events) ? input.events : []).filter(function (e) { return e && e.date; });
    if (!events.length) return stateCard(input.words || "No dated events are on record yet.", input.session, 0, "events");
    var marks = events.map(function (e) {
      return '<div class="vk-tl-row"><span class="vk-tl-dot"></span><span class="vk-tl-date">' + esc(e.date) +
        '</span><span class="vk-tl-label">' + esc(e.label || "") + (e.value != null ? " " + fmt(e.value) : "") + "</span></div>";
    }).join("");
    return frame(input.title || null, input.label || "One marker per dated event on record, in date order.",
      '<div class="vk-timeline">' + marks + "</div>", input.session, events.length, "events");
  }

  /* P1 Ladder */
  function ladder(input) {
    input = input || {};
    var levels = (Array.isArray(input.levels) ? input.levels : []).filter(function (l) { return l && num(l.price) != null; });
    var current = num(input.current);
    if (!levels.length) {
      if (current != null) {
        var only = '<div class="ladder vk-ladder"><div class="lrow price-row"><span>Current price</span><span>' + fmt(current) + "</span></div></div>";
        return frame(input.title || null, "Levels are not yet published. The current price on record is shown on its own.",
          '<div class="statecard vk-state">' + only + "</div>", input.session, 1, "price marker");
      }
      return stateCard(input.words || "No levels are on record yet.", input.session, 0, "levels");
    }
    var maxSize = 0;
    levels.forEach(function (l) { var s = num(l.size); if (s != null && s > maxSize) maxSize = s; });
    var rows = levels.slice().sort(function (a, b) { return b.price - a.price; });
    var html = '<div class="ladder vk-ladder">', inserted = false;
    function priceRow() {
      return '<div class="lrow price-row"><span>Current price</span><span class="bar"></span><span>' + fmt(current) + "</span></div>";
    }
    rows.forEach(function (l) {
      if (current != null && !inserted && l.price < current) { html += priceRow(); inserted = true; }
      var s = num(l.size);
      var bar = s != null && maxSize > 0
        ? '<span class="bar"><i style="width:' + Math.max(2, Math.round(100 * s / maxSize)) + '%"></i></span><span>' + fmt(s) + "</span>"
        : '<span class="bar"></span><span>size not published</span>';
      html += '<div class="lrow"><span>' + esc(l.name || "Level") + "</span>" + bar + "<span>" + fmt(l.price) + "</span></div>";
    });
    if (current != null && !inserted) html += priceRow();
    html += "</div>";
    return frame(input.title || null, input.label || "Levels on record, highest at the top. The longest bar is the biggest level.",
      html, input.session, rows.length, "levels");
  }

  /* P2 Band */
  function band(input) {
    input = input || {};
    var items = (Array.isArray(input.items) ? input.items : []).filter(function (b) { return b && num(b.low) != null && num(b.high) != null; });
    if (!items.length) {
      if (input.have != null && input.need != null) return accrual(input);
      return stateCard(input.words || "No range is on record yet.", input.session, 0, "ranges");
    }
    var lo = Infinity, hi = -Infinity;
    items.forEach(function (b) {
      lo = Math.min(lo, b.low); hi = Math.max(hi, b.high);
      [b.mid, b.current].forEach(function (v) { var n = num(v); if (n != null) { lo = Math.min(lo, n); hi = Math.max(hi, n); } });
    });
    if (hi === lo) hi = lo + 1;
    var W = 640, rowH = 34, H = items.length * rowH + 24;
    var plotL = 185, plotR = 470;
    function X(v) { return plotL + (v - lo) / (hi - lo) * (plotR - plotL); }
    function shortLabel(s) { s = String(s == null ? "" : s); return s.length > 26 ? s.slice(0, 25) + "\u2026" : s; }
    var s = svgOpen(W, H, "range bands");
    items.forEach(function (b, i) {
      var y = 12 + i * rowH;
      s += '<text x="0" y="' + (y + 15) + '" class="vk-axis"><title>' + esc(b.label || "") + '</title>' + esc(shortLabel(b.label || "")) + "</text>";
      if (b.high === b.low) {
        s += '<circle cx="' + X(b.low) + '" cy="' + (y + 10) + '" r="5" class="vk-pt"></circle>';
      } else {
        s += '<rect x="' + X(b.low) + '" y="' + (y + 3) + '" width="' + Math.max(2, X(b.high) - X(b.low)) + '" height="14" class="vk-bandrect"></rect>';
      }
      if (num(b.mid) != null) s += '<line x1="' + X(b.mid) + '" y1="' + y + '" x2="' + X(b.mid) + '" y2="' + (y + 20) + '" class="vk-mark"></line>';
      if (num(b.current) != null) s += '<circle cx="' + X(b.current) + '" cy="' + (y + 10) + '" r="4" class="vk-cur"></circle>';
      s += '<text x="' + (W - 4) + '" y="' + (y + 15) + '" text-anchor="end" class="vk-axis">' + fmt(b.low) + " to " + fmt(b.high) + "</text>";
    });
    s += "</svg>";
    return frame(input.title || null, input.label || "Each band is a range on record. The dot is where price or the outcome sits.",
      s, input.session, items.length, "bands");
  }

  /* P3 Curve */
  function curve(input) {
    input = input || {};
    var pts = (Array.isArray(input.points) ? input.points : []).filter(function (p) { return p && num(p.y) != null; });
    if (pts.length < 2) {
      if (input.have != null && input.need != null) return accrual(input);
      return stateCard(input.words || ("Only " + pts.length + " point is on record, so no shape can be drawn yet."), input.session, pts.length, "points");
    }
    var W = 640, H = 180, pad = 28;
    var ys = pts.map(function (p) { return p.y; });
    var yLo = Math.min.apply(null, ys), yHi = Math.max.apply(null, ys);
    if (yHi === yLo) yHi = yLo + 1;
    function X(i) { return pad + i / (pts.length - 1) * (W - pad * 2); }
    function Y(v) { return H - pad - (v - yLo) / (yHi - yLo) * (H - pad * 2); }
    var s = svgOpen(W, H, "shape");
    var d = "", i, x, y;
    if (input.step) {
      d = "M" + X(0) + " " + Y(pts[0].y);
      for (i = 1; i < pts.length; i++) d += " L" + X(i) + " " + Y(pts[i - 1].y) + " L" + X(i) + " " + Y(pts[i].y);
    } else {
      var solid = [], dashed = [], cur = solid;
      pts.forEach(function (p, j) {
        if (p.modelled && cur !== dashed) { dashed.push({ x: X(j - 1 >= 0 ? j - 1 : j), y: Y(pts[Math.max(0, j - 1)].y) }); cur = dashed; }
        if (!p.modelled && cur !== solid && j > 0) { cur = solid; }
        cur.push({ x: X(j), y: Y(p.y) });
      });
      function path(arr) { return arr.map(function (p, j) { return (j ? "L" : "M") + p.x + " " + p.y; }).join(" "); }
      if (solid.length > 1) s += '<path d="' + path(solid) + '" class="vk-line-path"></path>';
      if (dashed.length > 1) s += '<path d="' + path(dashed) + '" class="vk-line-path vk-dashed"></path>';
      d = null;
    }
    if (d) s += '<path d="' + d + '" class="vk-line-path"></path>';
    if (Array.isArray(input.benchmark) && input.benchmark.length > 1) {
      var bYs = input.benchmark.map(function (p) { return num(p && p.y); }).filter(function (v) { return v != null; });
      if (bYs.length > 1) {
        var bd = input.benchmark.map(function (p, j) {
          return (j ? "L" : "M") + (pad + j / (input.benchmark.length - 1) * (W - pad * 2)) + " " + Y(Math.max(yLo, Math.min(yHi, p.y)));
        }).join(" ");
        s += '<path d="' + bd + '" class="vk-line-path vk-bench"></path>';
      }
    }
    /* Encoding cure (14.1.3/14.1.7): both ends of the value scale
       are printed, and a scale that does not include zero says so. */
    s = gridH(s, W, pad, yLo, yHi, Y);
    if (yLo > 0 || yHi < 0) s += '<text x="' + pad + '" y="' + (H - 18) + '" class="vk-axis">Scale runs ' + fmt(yLo) + " to " + fmt(yHi) + "; zero is outside it.</text>";
    var top = pts.reduce(function (a, p, j) { return p.y > pts[a].y ? j : a; }, 0);
    s += '<circle cx="' + X(top) + '" cy="' + Y(pts[top].y) + '" r="4" class="vk-cur"></circle>';
    /* Point notes (2026-10-31, Wave 3 Item E): a point carrying a
       note string gets a marker dot and the note drawn at the point,
       alternating above and below so neighbouring notes stay
       readable. Points without a note draw exactly as before. */
    pts.forEach(function (p, j) {
      if (p.note == null || p.note === "") return;
      s += '<circle cx="' + X(j) + '" cy="' + Y(p.y) + '" r="3.5" class="vk-pt"></circle>';
      s += '<text x="' + X(j) + '" y="' + (Y(p.y) + (j % 2 ? 16 : -8)) + '" text-anchor="middle" class="vk-note">' + esc(p.note) + "</text>";
    });
    s += '<text x="' + pad + '" y="' + (H - 6) + '" class="vk-axis">' + esc(pts[0].x != null ? pts[0].x : "") + "</text>";
    s += '<text x="' + (W - pad - 40) + '" y="' + (H - 6) + '" class="vk-axis">' + esc(pts[pts.length - 1].x != null ? pts[pts.length - 1].x : "") + "</text>";
    s += '<text x="' + pad + '" y="14" class="vk-axis">' + fmt(yHi) + "</text></svg>";
    x = y = null;
    return frame(input.title || null, input.label || "The shape on record, drawn from the points in this page data.",
      s, input.session, pts.length, "points");
  }

  /* P4 Dial (cured 2026-10-31, spec 14.2): the name is kept for
     existing callers; the form is now the bullet, not a radial arc.
     Value rides length on a common scale, exact digits printed, and
     a history passed in draws as the bullet's sparkline. */
  function dial(input) {
    input = input || {};
    if (num(input.value) == null) {
      if (input.have != null && input.need != null) return accrual(input);
      return stateCard(input.words || "No reading is on record yet.", input.session, 0, "readings");
    }
    return bullet({ value: input.value, low: input.low, high: input.high, zones: input.zones,
      benchmark: input.benchmark, history: input.history, session: input.session,
      title: input.title, label: input.label || "The headline reading, drawn as a bar on its stated scale." });
  }

  /* P5 MeterBench */
  function meterBench(input) {
    input = input || {};
    var v = num(input.value), bench = num(input.benchmark);
    var graded = num(input.graded), needed = num(input.needed);
    if (v == null || bench == null || !graded) {
      var words = graded === 0 ? "Not yet graded. " + (input.haveWords || "No graded items are on record yet.")
        : "The figure or its benchmark is not on record yet.";
      if (graded != null && needed != null) {
        return accrual({ have: graded, need: needed, unit: "graded", session: input.session, title: input.title, label: words });
      }
      return stateCard(words, input.session, 0, "graded items");
    }
    var scaleMax = Math.max(v, bench) * 1.25 || 1;
    var pct = Math.max(1, Math.min(100, 100 * v / scaleMax));
    var bpct = Math.max(0, Math.min(100, 100 * bench / scaleMax));
    var body = '<div class="meter vk-meterbench"><div class="track"><div class="fill" style="width:' + pct + '%"></div>' +
      '<span class="vk-bench-mark" style="left:' + bpct + '%"></span></div>' +
      '<div class="mlabels"><span class="mvalue">' + fmt(v) + '</span><span>Simple benchmark ' + fmt(bench) + "</span></div></div>";
    if (graded != null && needed != null) body += '<p class="vk-coverage">' + fmt(graded) + " graded, " + fmt(needed) + " needed for a first full set</p>";
    return frame(input.title || null, input.label || "The figure against the benchmark it must beat, with the count behind it.",
      body, input.session, graded != null ? graded : 1, "graded items");
  }

  /* P6 RankedBars */
  function ranked(input) {
    input = input || {};
    var rows = (Array.isArray(input.rows) ? input.rows : []).filter(function (r) { return r && r.name != null; });
    if (!rows.length) return stateCard(input.words || "No rows are on record yet.", input.session, 0, "rows");
    var max = 0;
    rows.forEach(function (r) { var s = num(r.score); if (s != null && Math.abs(s) > max) max = Math.abs(s); });
    var html = '<div class="vk-ranked">';
    var drawn = 0;
    rows.forEach(function (r) {
      var s = num(r.score);
      html += '<div class="vk-rrow"><span class="vk-rname">' + esc(r.name) + "</span>";
      if (s != null && max > 0) {
        /* Encoding cure (14.2 comparison): a negative score draws in
           the down colour, so sign rides the bar itself, not only the
           printed number. Width still runs from zero by length. */
        html += '<span class="bar"><i style="width:' + Math.max(2, Math.round(100 * Math.abs(s) / max)) + '%' + (s < 0 ? ";background:var(--down)" : "") + '"></i></span><span class="vk-rscore">' + fmt(s) + "</span>";
        drawn++;
      } else {
        html += '<span class="bar"></span><span class="vk-rscore">no score on record</span>';
      }
      if (r.coverage != null) html += '<span class="vk-rcov">' + esc(r.coverage) + "</span>";
      if (r.status) html += '<span class="chip waiting">' + esc(r.status) + "</span>";
      html += "</div>";
    });
    html += "</div>";
    return frame(claimTitle(input.title, topClaim(rows)), input.label || "Rows on record, best first. Bar length is set by the biggest score on this page.",
      html, input.session, rows.length, "rows", drawn + " rows carry a score.");
  }

  /* P7 Tiles and HeatStrip */
  function tiles(input) {
    input = input || {};
    if (input.mode === "strip") return heatStrip(input);
    var items = (Array.isArray(input.items) ? input.items : []).filter(function (t) { return t && t.label != null; });
    var withData = items.filter(function (t) { return num(t.value) != null; });
    if (!withData.length) return stateCard(input.words || "No readings are on record yet.", input.session, 0, "tiles");
    var max = 0;
    withData.forEach(function (t) { if (Math.abs(t.value) > max) max = Math.abs(t.value); });
    var html = '<div class="tiles vk-tiles">';
    items.forEach(function (t) {
      var v = num(t.value);
      if (v == null) { html += '<div class="tile nodata"><span class="sym">' + esc(t.label) + "</span><br>no data on record</div>"; return; }
      var cls = v > 0 ? "up" : (v < 0 ? "down" : "nodata");
      /* Encoding cure (14.1.1/14.5.1): every tile also carries a
         length bar from zero on the page's common scale, so the
         quantity rides length, not tint alone. */
      var barPct = max > 0 ? Math.max(2, Math.round(100 * Math.abs(v) / max)) : 0;
      html += '<div class="tile ' + cls + '"><span class="sym">' + esc(t.label) + '</span><br><span class="vk-tval">' + fmt(v) + "</span>" +
        '<span class="bar" style="display:block;height:6px;background:var(--nodata-bg);border-radius:3px;margin-top:5px;position:relative"><i style="position:absolute;left:0;top:0;bottom:0;width:' + barPct + "%;background:" + (v < 0 ? "var(--down)" : "var(--accent)") + ';border-radius:3px"></i></span>' +
        (t.word ? "<br>" + esc(t.word) : "") + "</div>";
    });
    html += "</div>";
    var tileTop = null;
    withData.forEach(function (t) { if (tileTop == null || t.value > tileTop.value) tileTop = t; });
    return frame(claimTitle(input.title, tileTop ? String(tileTop.label) + " is highest at " + fmt(tileTop.value) : null), input.label || "One tile per name on record. Colour follows the reading in this page data.",
      html, input.session, withData.length, "tiles");
  }
  function heatStrip(input) {
    var buckets = (Array.isArray(input.buckets) ? input.buckets : []).filter(function (b) { return b && b.label != null; });
    var withData = buckets.filter(function (b) { return num(b.count != null ? b.count : b.value) != null; });
    if (!withData.length) return stateCard(input.words || "Nothing is on record for this strip yet.", input.session, 0, "buckets");
    var max = 0;
    withData.forEach(function (b) { var c = num(b.count != null ? b.count : b.value); if (c > max) max = c; });
    var cells = buckets.map(function (b) {
      var c = num(b.count != null ? b.count : b.value);
      var cls = c == null || c === 0 ? "" : (c >= max * 0.66 ? " vk-heat-hot" : " vk-heat-mid");
      return '<span class="vk-heat-cell' + cls + '" title="' + esc(b.label) + '">' + esc(b.label) + (c != null ? " " + fmt(c) : "") + "</span>";
    }).join("");
    return '<div class="vk-heatstrip">' + cells + "</div>" + receipt(input.session, withData.length, "buckets");
  }

  /* P8 Tape */
  function tape(input) {
    input = input || {};
    var events = (Array.isArray(input.events) ? input.events : []).filter(function (e) { return e && (e.label != null || e.desc != null); });
    if (!events.length) return stateCard(input.words || "A quiet tape: no events are on record.", input.session, 0, "events");
    var counts = {};
    events.forEach(function (e) { var k = e.stripKey || (e.time ? String(e.time).slice(0, 13) : "on record"); counts[k] = (counts[k] || 0) + 1; });
    var buckets = Object.keys(counts).sort().map(function (k) { return { label: k, count: counts[k] }; });
    var strip = heatStrip({ buckets: buckets, session: null }).replace(/<p class="creceipt">.*?<\/p>/, "");
    var rows = events.map(function (e) {
      var tags = (Array.isArray(e.tags) ? e.tags : []).map(function (t) { return '<span class="chip waiting">' + esc(t) + "</span>"; }).join(" ");
      return '<div class="trow"><span class="ttime">' + esc(e.time || "") + '</span><span class="tsym">' + esc(e.label || "") +
        "</span><span>" + esc(e.desc || "") + "</span>" + tags + "</div>";
    }).join("");
    var body = strip + '<div class="tape vk-tape">' + rows + "</div>";
    return frame(input.title || null, input.label || "Newest first. The strip counts the same rows by time.",
      body, input.session, events.length, "events");
  }

  /* P9 Line */
  function line(input) {
    input = input || {};
    var series = (Array.isArray(input.series) ? input.series : []);
    var valid = series.filter(function (p) { return p && num(p.value) != null; });
    if (valid.length < 2) {
      if (input.have != null && input.need != null) return accrual(input);
      return stateCard(input.words || ("Only " + valid.length + " dated value is on record, so no line can be drawn yet."), input.session, valid.length, "dated values");
    }
    var W = input.spark ? 220 : 640, H = input.spark ? 44 : 180, pad = input.spark ? 2 : 28;
    var vs = valid.map(function (p) { return p.value; });
    var lo = Math.min.apply(null, vs), hi = Math.max.apply(null, vs);
    if (hi === lo) hi = lo + 1;
    function X(i) { return pad + i / (series.length - 1) * (W - pad * 2); }
    function Y(v) { return H - pad - (v - lo) / (hi - lo) * (H - pad * 2); }
    var s = svgOpen(W, H, "history line");
    /* Encoding cure (14.1.3/14.1.7): a full line chart carries a
       labelled value axis (grid + tick values), a zero line when
       zero is in range, and a printed note when the scale is
       truncated. Spark variants stay axis-free by design. */
    if (!input.spark) {
      s = gridH(s, W, pad, lo, hi, Y);
      if (lo <= 0 && hi >= 0) s += '<line x1="' + pad + '" y1="' + Y(0) + '" x2="' + (W - pad) + '" y2="' + Y(0) + '" class="vk-zero"></line>';
    }
    var seg = [];
    function flush() { if (seg.length > 1) s += '<path d="' + seg.map(function (p, j) { return (j ? "L" : "M") + p[0] + " " + p[1]; }).join(" ") + '" class="vk-line-path"></path>'; seg = []; }
    series.forEach(function (p, i) {
      if (!p || num(p.value) == null) { flush(); return; }
      if (p.projected && seg.length) { flush(); }
      seg.push([X(i), Y(p.value)]);
      if (p.projected) flush();
    });
    flush();
    var lastIdx = series.map(function (p, i) { return num(p && p.value) != null ? i : -1; }).filter(function (i) { return i >= 0; }).pop();
    s += '<circle cx="' + X(lastIdx) + '" cy="' + Y(series[lastIdx].value) + '" r="4" class="vk-cur"></circle>';
    if (!input.spark) {
      s += '<text x="' + pad + '" y="' + (H - 6) + '" class="vk-axis">' + esc(series[0].date || "") + " " + fmt(series[0].value) + "</text>";
      s += '<text x="' + (W - pad - 90) + '" y="' + (H - 6) + '" class="vk-axis">' + esc(series[lastIdx].date || "") + " " + fmt(series[lastIdx].value) + "</text>";
    }
    s += "</svg>";
    var lineLabel = input.label || "How the headline figure moved, from the dated values on record. A gap means a missing session.";
    if (!input.spark && (lo > 0 || hi < 0)) lineLabel += " The scale runs " + fmt(lo) + " to " + fmt(hi) + "; zero is outside it, so heights compare positions, not amounts from zero.";
    return frame(input.spark ? null : claimTitle(input.title, moveClaim(valid.length ? valid[0].value : null, valid.length ? valid[valid.length - 1].value : null)), input.spark ? null : lineLabel,
      s, input.session, valid.length, "dated values");
  }

  /* P11 Scatter */
  function scatter(input) {
    input = input || {};
    var rows = (Array.isArray(input.rows) ? input.rows : []);
    var pairs = rows.filter(function (r) { return r && num(r.x) != null && num(r.y) != null; });
    if (pairs.length < 3) {
      var scored = rows.filter(function (r) { return r && num(r.x) != null; });
      if (scored.length) {
        return ranked({ rows: scored.map(function (r) { return { name: r.label || r.name || "Row", score: r.x }; }), session: input.session, title: input.title,
          label: "Too few complete pairs for a scatter, so the main figure is shown as bars." });
      }
      return stateCard(input.words || "Too few complete pairs are on record for a scatter.", input.session, pairs.length, "pairs");
    }
    var W = 640, H = 220, pad = 34;
    var xs = pairs.map(function (p) { return p.x; }), ys = pairs.map(function (p) { return p.y; });
    var xLo = Math.min.apply(null, xs), xHi = Math.max.apply(null, xs), yLo = Math.min.apply(null, ys), yHi = Math.max.apply(null, ys);
    if (xHi === xLo) xHi = xLo + 1; if (yHi === yLo) yHi = yLo + 1;
    function X(v) { return pad + (v - xLo) / (xHi - xLo) * (W - pad * 2); }
    function Y(v) { return H - pad - (v - yLo) / (yHi - yLo) * (H - pad * 2); }
    var s = svgOpen(W, H, "paired figures");
    if (Array.isArray(input.fitLine) && input.fitLine.length === 2) {
      s += '<line x1="' + X(input.fitLine[0][0]) + '" y1="' + Y(input.fitLine[0][1]) + '" x2="' + X(input.fitLine[1][0]) + '" y2="' + Y(input.fitLine[1][1]) + '" class="vk-fit"></line>';
    }
    /* Encoding cure (14.1.7): points are directly labelled with
       their name and both exact values, not left unlabelled. */
    pairs.forEach(function (p) {
      s += '<circle cx="' + X(p.x) + '" cy="' + Y(p.y) + '" r="4" class="vk-dot"></circle>';
      var lbl = p.label || p.name || "";
      if (lbl) s += '<text x="' + (X(p.x) + 6) + '" y="' + (Y(p.y) + 3) + '" class="vk-axis">' + esc(String(lbl).slice(0, 14)) + " " + fmt(p.x) + ", " + fmt(p.y) + "</text>";
    });
    s += '<text x="' + pad + '" y="' + (H - 8) + '" class="vk-axis">' + esc(input.xLabel || "first figure") + ": " + fmt(xLo) + " to " + fmt(xHi) + "</text>";
    s += '<text x="' + pad + '" y="14" class="vk-axis">' + esc(input.yLabel || "second figure") + ": " + fmt(yLo) + " to " + fmt(yHi) + "</text></svg>";
    var lacking = rows.length - pairs.length;
    return frame(input.title || null, input.label || "One dot per row that carries both figures.",
      s, input.session, pairs.length, "pairs", lacking ? lacking + " rows lacked a pair." : null);
  }


  /* Slope: change between two points (repair 2026-10-31, spec 14.2).
     One line per row from its first reading to its second, on one
     common scale, both exact values printed at the line ends. Colour
     follows the direction of the change; a caller whose lower value
     is the better one passes lowerIsBetter so the colour follows the
     meaning, and its label says which way is better. Fails closed to
     the state card when fewer than two complete pairs are on record.
     Categorical from/to standings (decay-watch) are not pairs and are
     never drawn here. */
  function slope(input) {
    input = input || {};
    var pairs = (Array.isArray(input.pairs) ? input.pairs : []).filter(function (p) { return p && p.name != null && num(p.from) != null && num(p.to) != null; });
    if (pairs.length < 2) return stateCard(input.words || "Too few two-point changes are on record for a slope chart.", input.session, pairs.length, "pairs");
    var lo = Infinity, hi = -Infinity;
    pairs.forEach(function (p) { lo = Math.min(lo, p.from, p.to); hi = Math.max(hi, p.from, p.to); });
    if (hi === lo) hi = lo + 1;
    var W = 640, padT = 28, rowH = 30, plotH = pairs.length * rowH;
    var H = padT + plotH + 10;
    var xL = 218, xR = 498;
    function Y(v) { return padT + (hi - v) / (hi - lo) * (plotH - 14) + 7; }
    var s = svgOpen(W, H, "change between two points");
    s += '<text x="' + xL + '" y="15" text-anchor="middle" class="vk-axis">' + esc(input.fromLabel || "first reading") + '</text>';
    s += '<text x="' + xR + '" y="15" text-anchor="middle" class="vk-axis">' + esc(input.toLabel || "second reading") + '</text>';
    pairs.forEach(function (p) {
      var better = input.lowerIsBetter ? p.to < p.from : p.to > p.from;
      var worse = input.lowerIsBetter ? p.to > p.from : p.to < p.from;
      var stroke = better ? "var(--accent)" : (worse ? "var(--down)" : "var(--faint)");
      var y1 = Y(p.from), y2 = Y(p.to), ym = (y1 + y2) / 2;
      s += '<text x="0" y="' + (ym + 4) + '" class="vk-axis vk-barlabel"><title>' + esc(p.name) + '</title>' + esc(String(p.name).slice(0, 30)) + '</text>';
      s += '<line x1="' + xL + '" y1="' + y1.toFixed(1) + '" x2="' + xR + '" y2="' + y2.toFixed(1) + '" style="stroke:' + stroke + ';stroke-width:2"></line>';
      s += '<circle cx="' + xL + '" cy="' + y1.toFixed(1) + '" r="4" class="vk-dot"></circle><circle cx="' + xR + '" cy="' + y2.toFixed(1) + '" r="4" class="vk-dot"></circle>';
      s += '<text x="' + (xL - 10) + '" y="' + (y1 + 4) + '" text-anchor="end" class="vk-axis">' + fmt(p.from) + '</text>';
      s += '<text x="' + (xR + 10) + '" y="' + (y2 + 4) + '" class="vk-axis">' + fmt(p.to) + '</text>';
    });
    s += "</svg>";
    return frame(input.title || null, input.label || "One line per row, from its first reading to its second. Both exact values are printed at the line ends.", s, input.session, pairs.length, "pairs");
  }

  /* ---- Charts-IA extension (2026-10-31): the INFO-MAP vocabulary in
     FolioTend style. Navy ink, teal accent/up, muted red down, mint
     gridlines. Every renderer draws only the numbers it is handed,
     to scale, and fails closed to the plain state card. ---- */
  function gridH(s, W, pad, yLo, yHi, Y, n) {
    n = n || 4;
    for (var i = 0; i <= n; i++) {
      var v = yLo + (yHi - yLo) * i / n, y = Y(v);
      s += '<line x1="' + pad + '" y1="' + y + '" x2="' + (W - pad) + '" y2="' + y + '" class="vk-grid"></line>';
      s += '<text x="' + (pad - 4) + '" y="' + (y + 3) + '" text-anchor="end" class="vk-axis">' + fmt(v) + "</text>";
    }
    return s;
  }
  function seriesXY(series, W, H, pad) {
    var valid = series.filter(function (p) { return p && num(p.value) != null; });
    var vs = valid.map(function (p) { return p.value; });
    var lo = Math.min.apply(null, vs), hi = Math.max.apply(null, vs);
    if (hi === lo) hi = lo + 1;
    return { valid: valid, lo: lo, hi: hi,
      X: function (i) { return pad + i / Math.max(1, series.length - 1) * (W - pad * 2); },
      Y: function (v) { return H - pad - (v - lo) / (hi - lo) * (H - pad * 2); } };
  }
  /* Area: a dated line with the space under it filled. */
  function area(input) {
    input = input || {};
    var series = Array.isArray(input.series) ? input.series : [];
    var valid = series.filter(function (p) { return p && num(p.value) != null; });
    if (valid.length < 2) return stateCard(input.words || "Only " + valid.length + " dated value is on record, so no area can be drawn yet.", input.session, valid.length, "dated values");
    var W = 640, H = 190, pad = 34;
    var xy = seriesXY(series, W, H, pad);
    var s = svgOpen(W, H, "area chart");
    s = gridH(s, W, pad, xy.lo, xy.hi, xy.Y);
    var lineD = "", started = false;
    series.forEach(function (p, i) { if (num(p && p.value) == null) return; lineD += (started ? " L" : "M") + xy.X(i) + " " + xy.Y(p.value); started = true; });
    var firstI = series.findIndex(function (p) { return num(p && p.value) != null; });
    var lastI = series.length - 1; while (lastI > 0 && num(series[lastI].value) == null) lastI--;
    s += '<path d="' + lineD + " L" + xy.X(lastI) + " " + (H - pad) + " L" + xy.X(firstI) + " " + (H - pad) + ' Z" class="vk-area-fill"></path>';
    s += '<path d="' + lineD + '" class="vk-line-path"></path>';
    s += '<circle cx="' + xy.X(lastI) + '" cy="' + xy.Y(series[lastI].value) + '" r="4" class="vk-cur"></circle>';
    s += '<text x="' + pad + '" y="' + (H - 6) + '" class="vk-axis">' + esc(series[firstI].date || "") + "</text>";
    if (xy.lo <= 0 && xy.hi >= 0) s += '<line x1="' + pad + '" y1="' + xy.Y(0) + '" x2="' + (W - pad) + '" y2="' + xy.Y(0) + '" class="vk-zero"></line>';
    s += '<text x="' + (W - pad) + '" y="' + (H - 6) + '" text-anchor="end" class="vk-axis">' + esc(series[lastI].date || "") + " " + fmt(series[lastI].value) + "</text></svg>";
    /* Encoding cure (14.1.1/14.1.3): the line's position carries the
       value; the fill is shading only and is never captioned as the
       size of the move. A truncated scale says so in the label. */
    var areaLabel = input.label || "The dated values on record. The line's height carries each value; the shading under it is decoration only.";
    if (xy.lo > 0 || xy.hi < 0) areaLabel += " The scale runs " + fmt(xy.lo) + " to " + fmt(xy.hi) + "; zero is outside it.";
    return frame(claimTitle(input.title, moveClaim(valid[0].value, valid[valid.length - 1].value)), areaLabel, s, input.session, valid.length, "dated values");
  }
  /* Sparkline: the same dated line, small, for cards and strips. */
  function sparkline(input) {
    input = input || {};
    var series = Array.isArray(input.series) ? input.series : [];
    var valid = series.filter(function (p) { return p && num(p.value) != null; });
    if (valid.length < 2) return input.raw ? "" : stateCard(input.words || "Too few dated values are on record for a small chart yet.", input.session, valid.length, "dated values");
    var W = input.width || 220, H = input.height || 48, pad = 3;
    var xy = seriesXY(series, W, H, pad);
    var d = "";
    series.forEach(function (p, i) { if (num(p && p.value) == null) return; d += (d ? " L" : "M") + xy.X(i).toFixed(1) + " " + xy.Y(p.value).toFixed(1); });
    var last = valid[valid.length - 1];
    var down = valid.length > 1 && last.value < valid[0].value;
    var s = svgOpen(W, H, "small chart") + '<path d="' + d + '" class="vk-line-path' + (down ? " vk-down-stroke" : "") + '"></path></svg>';
    if (input.raw) return s;
    return frame(input.title || null, input.label || null, s, input.session, valid.length, "dated values");
  }
  /* Fan: nested range bands widening over steps (horizons). */
  function fan(input) {
    input = input || {};
    var steps = (Array.isArray(input.steps) ? input.steps : []).filter(function (st) { return st && num(st.low) != null && num(st.high) != null; });
    if (steps.length < 1) return stateCard(input.words || "No range steps are on record yet.", input.session, 0, "steps");
    var W = 640, H = 200, padL = 44, padR = 16, padT = 14, padB = 26;
    var lo = Infinity, hi = -Infinity;
    steps.forEach(function (st) { lo = Math.min(lo, st.low, st.low2 != null ? st.low2 : st.low); hi = Math.max(hi, st.high, st.high2 != null ? st.high2 : st.high); if (num(st.mid) != null) { lo = Math.min(lo, st.mid); hi = Math.max(hi, st.mid); } });
    if (hi === lo) hi = lo + 1;
    function X(i) { return padL + (steps.length === 1 ? 0.5 : i / (steps.length - 1)) * (W - padL - padR); }
    function Y(v) { return padT + (hi - v) / (hi - lo) * (H - padT - padB); }
    var s = svgOpen(W, H, "range fan");
    s = gridH(s, W, padL, lo, hi, Y);
    function bandPath(lk, hk, cls) {
      var top = steps.map(function (st, i) { return (i ? "L" : "M") + X(i) + " " + Y(st[hk]); }).join(" ");
      var bot = steps.slice().reverse().map(function (st, j) { var i = steps.length - 1 - j; return "L" + X(i) + " " + Y(st[lk]); }).join(" ");
      return '<path d="' + top + " " + bot + ' Z" class="' + cls + '"></path>';
    }
    var hasOuter = steps.some(function (st) { return st.low2 != null && st.high2 != null; });
    if (hasOuter) s += bandPath("low2", "high2", "vk-fan-outer");
    s += bandPath("low", "high", "vk-fan-inner");
    /* Encoding cure (14.2 uncertainty): the bands are named on the
       chart itself. No probability is invented: the kit only knows
       a narrower and a wider published range, and says exactly that. */
    s += '<text x="' + padL + '" y="' + (padT + 10) + '" class="vk-axis">Inner band: the narrower published range</text>';
    if (hasOuter) s += '<text x="' + padL + '" y="' + (padT + 24) + '" class="vk-axis">Outer band: the wider published range</text>';
    if (steps.some(function (st) { return num(st.mid) != null; })) {
      s += '<path d="' + steps.map(function (st, i) { return (i ? "L" : "M") + X(i) + " " + Y(num(st.mid) != null ? st.mid : (st.low + st.high) / 2); }).join(" ") + '" class="vk-line-path"></path>';
    }
    steps.forEach(function (st, i) { s += '<text x="' + X(i) + '" y="' + (H - 6) + '" text-anchor="middle" class="vk-axis">' + esc(st.label || ("step " + (i + 1))) + "</text>"; });
    s += "</svg>";
    return frame(input.title || null, input.label || "Each step is a range on record. The wider band holds the narrower one, the way the ranges were published.", s, input.session, steps.length, "steps");
  }
  /* Distribution: vertical bars, one per bucket, heights to scale. */
  function distribution(input) {
    input = input || {};
    var buckets = (Array.isArray(input.buckets) ? input.buckets : []).filter(function (b) { return b && num(b.value) != null; });
    if (!buckets.length) return stateCard(input.words || "No buckets are on record yet.", input.session, 0, "buckets");
    var W = 640, H = 200, padL = 40, padR = 10, padT = 16, padB = 30;
    var lo = Math.min(0, Math.min.apply(null, buckets.map(function (b) { return b.value; })));
    var hi = Math.max.apply(null, buckets.map(function (b) { return b.value; })); if (hi === lo) hi = lo + 1;
    function Y(v) { return padT + (hi - v) / (hi - lo) * (H - padT - padB); }
    var bw = (W - padL - padR) / buckets.length;
    var s = svgOpen(W, H, "distribution bars");
    s = gridH(s, W, padL, lo, hi, Y);
    s += '<line x1="' + padL + '" y1="' + Y(0) + '" x2="' + (W - padR) + '" y2="' + Y(0) + '" class="vk-zero"></line>';
    buckets.forEach(function (b, i) {
      var x = padL + i * bw + bw * 0.15, w = bw * 0.7;
      var y0 = Y(Math.max(0, b.value)), y1 = Y(Math.min(0, b.value));
      s += '<rect x="' + x + '" y="' + y0 + '" width="' + w + '" height="' + Math.max(1.5, y1 - y0) + '" class="' + (b.value < 0 ? "vk-bar-down" : "vk-bar-up") + '"></rect>';
      s += '<text x="' + (x + w / 2) + '" y="' + (b.value < 0 ? y1 + 13 : y0 - 4) + '" text-anchor="middle" class="vk-axis">' + fmt(b.value) + "</text>";
      s += '<text x="' + (x + w / 2) + '" y="' + (H - 8) + '" text-anchor="middle" class="vk-axis">' + esc(String(b.label || "").slice(0, 12)) + "</text>";
    });
    s += "</svg>";
    var dTotal = buckets.reduce(function (a, b) { return a + b.value; }, 0);
    var dTop = buckets.slice().sort(function (a, b) { return b.value - a.value; })[0];
    return frame(claimTitle(input.title, dTop && dTotal > 0 ? String(dTop.label || "the fullest bucket") + " is the fullest bucket at " + fmt(dTop.value) + " of " + fmt(dTotal) : null), input.label || "One bar per bucket on record, heights on one scale. Red bars sit below zero.", s, input.session, buckets.length, "buckets");
  }
  /* CountBars: horizontal SVG bars for counts, values printed at the end. */
  function countBars(input) {
    input = input || {};
    var rows = (Array.isArray(input.rows) ? input.rows : []).filter(function (r) { return r && r.name != null && num(r.score) != null; });
    if (!rows.length) return stateCard(input.words || "No counts are on record yet.", input.session, 0, "counts");
    var W = 640, rowH = 26, H = rows.length * rowH + 10, labelW = 210, valW = 64;
    var max = Math.max.apply(null, rows.map(function (r) { return Math.abs(r.score); }).concat([1]));
    var s = svgOpen(W, H, "count bars");
    rows.forEach(function (r, i) {
      var y = 6 + i * rowH;
      s += '<text x="0" y="' + (y + 14) + '" class="vk-axis vk-barlabel"><title>' + esc(r.name) + "</title>" + esc(String(r.name).slice(0, 30)) + "</text>";
      s += '<rect x="' + labelW + '" y="' + (y + 3) + '" width="' + Math.max(1.5, (W - labelW - valW) * Math.abs(r.score) / max) + '" height="13" class="' + (r.score < 0 ? "vk-bar-down" : "vk-bar-up") + '"></rect>';
      s += '<text x="' + (W - 4) + '" y="' + (y + 14) + '" text-anchor="end" class="vk-axis">' + fmt(r.score) + "</text>";
    });
    s += "</svg>";
    return frame(claimTitle(input.title, topClaim(rows)), input.label || "Counts on record, drawn on one scale so the big and small counts can be compared at a glance.", s, input.session, rows.length, "counts");
  }
  /* Heatmap: a grid of cells coloured by value. */
  function heatmap(input) {
    input = input || {};
    var cells = Array.isArray(input.cells) ? input.cells : [];
    var flat = [];
    cells.forEach(function (row) { (Array.isArray(row) ? row : []).forEach(function (v) { if (num(v) != null) flat.push(v); }); });
    if (!cells.length || !flat.length) return stateCard(input.words || "No grid values are on record yet.", input.session, 0, "cells");
    var ncols = Math.max.apply(null, cells.map(function (r) { return (r || []).length; }));
    var W = 640, padL = 92, padT = 8, padB = 22, cellW = (W - padL - 8) / ncols, cellH = 20;
    var H = padT + cells.length * cellH + padB;
    var maxAbs = Math.max.apply(null, flat.map(function (v) { return Math.abs(v); }).concat([0.0001]));
    var s = svgOpen(W, H, "heat grid");
    cells.forEach(function (row, ri) {
      s += '<text x="0" y="' + (padT + ri * cellH + 14) + '" class="vk-axis">' + esc(String((input.rowLabels || [])[ri] || ("row " + (ri + 1))).slice(0, 15)) + "</text>";
      (row || []).forEach(function (v, ci) {
        var n = num(v); if (n == null) return;
        var cls = n < 0 ? "vk-heat-neg" : "vk-heat-pos";
        /* Encoding cure (14.1.4/14.1.7/14.5.10): magnitude no longer
           rides opacity/saturation (the last-ranked channel, and
           hover-only). Hue marks sign only; the exact value is
           printed in the cell, readable on touch. */
        s += '<rect x="' + (padL + ci * cellW + 1) + '" y="' + (padT + ri * cellH + 1) + '" width="' + (cellW - 2) + '" height="' + (cellH - 2) + '" rx="3" class="' + cls + '"></rect>';
        s += '<text x="' + (padL + ci * cellW + cellW / 2) + '" y="' + (padT + ri * cellH + cellH / 2 + 4) + '" text-anchor="middle" class="vk-axis">' + fmt(n) + "</text>";
      });
    });
    (input.colLabels || []).forEach(function (c, ci) { s += '<text x="' + (padL + ci * cellW + cellW / 2) + '" y="' + (H - 6) + '" text-anchor="middle" class="vk-axis">' + esc(String(c).slice(0, 8)) + "</text>"; });
    s += "</svg>";
    return frame(input.title || null, input.label || "One cell per pair on record. Each cell prints its exact value; teal means at or above zero and red means below zero.", s, input.session, flat.length, "cells");
  }
  /* GaugeZones (cured 2026-10-31, spec 14.2): the name is kept for
     existing callers and hub minis; the form is now the bullet with
     the page's own named zones as bands, not a half-round dial. */
  function gaugeZones(input) { return bullet(input || {}); }
  /* Timeline: dated events on one line, oldest first. */
  function timeline(input) {
    input = input || {};
    var events = (Array.isArray(input.events) ? input.events : []).filter(function (e) { return e && e.date; })
      .slice().sort(function (a, b) { return String(a.date) < String(b.date) ? -1 : 1; });
    if (!events.length) return stateCard(input.words || "No dated events are on record yet.", input.session, 0, "events");
    var shown = events.slice(-14);
    var W = 640, H = 84, pad = 30, y = 34;
    var s = svgOpen(W, H, "timeline");
    s += '<line x1="' + pad + '" y1="' + y + '" x2="' + (W - pad) + '" y2="' + y + '" class="vk-tl-line"></line>';
    shown.forEach(function (e, i) {
      var x = shown.length === 1 ? W / 2 : pad + i / (shown.length - 1) * (W - pad * 2);
      s += '<circle cx="' + x + '" cy="' + y + '" r="5" class="vk-cur"><title>' + esc(e.date + " " + (e.label || "")) + "</title></circle>";
      s += '<text x="' + x + '" y="' + (y + 26) + '" text-anchor="middle" class="vk-axis">' + esc(String(e.date).slice(5, 10) || e.date) + "</text>";
    });
    s += '<text x="' + pad + '" y="14" class="vk-axis">' + esc(shown[0].date) + "</text>";
    s += '<text x="' + (W - pad) + '" y="14" text-anchor="end" class="vk-axis">' + esc(shown[shown.length - 1].date) + "</text></svg>";
    var last = events[events.length - 1];
    return frame(input.title || null, input.label || ("One dot per dated event on record, oldest first. The latest: " + last.date + (last.label ? " " + last.label : "") + "."), s, input.session, events.length, "events");
  }
  /* StackedBar: shares of a whole as lengths on one axis
     (spec 14.2 composition: stacked bar, not pie/donut). */
  function stackedBar(input) {
    input = input || {};
    var slices = (Array.isArray(input.slices) ? input.slices : []).filter(function (sl) { return sl && num(sl.value) != null && sl.value > 0; });
    var total = slices.reduce(function (a, sl) { return a + sl.value; }, 0);
    if (!slices.length || total <= 0) return stateCard(input.words || "No shares are on record yet.", input.session, 0, "shares");
    var W = 640, padL = 8, padR = 8, barY = 18, barH = 26;
    var H = barY + barH + 14 + slices.length * 19 + 8;
    var s = svgOpen(W, H, "shares as a stacked bar");
    var x = padL, usable = W - padL - padR;
    slices.forEach(function (sl, i) {
      var w = usable * sl.value / total;
      s += '<rect x="' + x.toFixed(1) + '" y="' + barY + '" width="' + Math.max(1, w - 1).toFixed(1) + '" height="' + barH + '" class="vk-slice vk-slice-' + (i % 5) + '"></rect>';
      x += w;
    });
    slices.forEach(function (sl, i) {
      var y = barY + barH + 26 + i * 19;
      s += '<rect x="' + padL + '" y="' + (y - 10) + '" width="10" height="10" class="vk-slice vk-slice-' + (i % 5) + '"></rect>';
      s += '<text x="' + (padL + 16) + '" y="' + y + '" class="vk-axis vk-legend">' + esc(String(sl.label).slice(0, 34)) + " " + fmt(sl.value) + " (" + Math.round(100 * sl.value / total) + "%)</text>";
    });
    s += "</svg>";
    var sTop = slices.slice().sort(function (a, b) { return b.value - a.value; })[0];
    return frame(claimTitle(input.title, sTop ? String(sTop.label) + " is the biggest part at " + Math.round(100 * sTop.value / total) + "%" : null), input.label || "Each part is one share of the whole on record, drawn as a length on one bar. Longer means a bigger share; every share also prints its value and percent.", s, input.session, slices.length, "shares");
  }
  /* Donut kept as a name only: it now draws the stacked bar above.
     Encoding cure (14.1.1/14.2): shares no longer ride angle/area. */
  function donut(input) { return stackedBar(input); }

  var VK = {
    ladder: ladder, band: band, curve: curve, dial: dial, meterBench: meterBench,
    ranked: ranked, tiles: tiles, heatStrip: heatStrip, tape: tape, line: line,
    accrual: accrual, scatter: scatter, slope: slope, sessionOf: sessionOf, _esc: esc,
    area: area, sparkline: sparkline, fan: fan, distribution: distribution,
    heatmap: heatmap, gaugeZones: gaugeZones, bullet: bullet, timeline: timeline,
    countBars: countBars, donut: donut, stackedBar: stackedBar
  };
  root.VisualKit = VK;
  if (typeof module !== "undefined" && module.exports) module.exports = VK;

  /* Browser binding: one container per page, fed only by that page data.json.
     Container attributes: data-vk (primitive name), data-vk-source (dot path
     into data.json, optional), plus field hints data-vk-x, data-vk-y and
     friends. Re-checks the same file on the live grammar in DESIGN section 5
     and re-renders only when the content changed. */
  if (typeof document !== "undefined" && typeof fetch !== "undefined") {
    var lastJson = null;
    function getPath(obj, path) {
      if (!path) return obj;
      return path.split(".").reduce(function (o, k) { return o == null ? o : o[k]; }, obj);
    }
    function bindSpec(host, data) {
      var src = getPath(data, host.getAttribute("data-vk-source"));
      var session = sessionOf(data);
      var prim = host.getAttribute("data-vk");
      var a = host.dataset || {};
      function rowsToSeries(rows) {
        return (rows || []).map(function (r) { return { date: r[a.vkX || "date"] || r.date || "", value: r[a.vkY || "value"] }; });
      }
      switch (prim) {
        case "ladder": return { levels: src, current: a.vkCurrent ? getPath(data, a.vkCurrent) : data.current, session: session };
        case "band": return { items: src, session: session };
        case "curve": return { points: (src || []).map(function (r, i) { return { x: r[a.vkX || "label"] != null ? r[a.vkX || "label"] : i, y: r[a.vkY || "value"] }; }), step: host.hasAttribute("data-vk-step"), session: session };
        case "dial": return { value: src && src.value != null ? src.value : src, low: src && src.low, high: src && src.high, zones: src && src.zones, history: src && src.history, session: session };
        case "bullet": return { value: src && src.value != null ? src.value : src, low: src && src.low, high: src && src.high, zones: src && src.zones, benchmark: src && (src.benchmark != null ? src.benchmark : src.target), history: src && src.history, session: session };
        case "meterbench": return { value: src && src.value, benchmark: src && src.benchmark, graded: src && src.graded, needed: src && src.needed, session: session };
        case "ranked": return { rows: src, session: session };
        case "tiles": return { items: src, session: session };
        case "tape": return { events: src, session: session };
        case "line": return { series: rowsToSeries(src), session: session };
        case "accrual": return { have: src && src.have, need: src && src.need, unit: a.vkUnit || "items", session: session };
        case "scatter": return { rows: (src || []).map(function (r) { return { x: r[a.vkX], y: r[a.vkY], label: r.label || r.name }; }), session: session };
        case "slope": return { pairs: (src || []).map(function (r) { return { name: r.name || r.label, from: r[a.vkFrom || "from"], to: r[a.vkTo || "to"] }; }), session: session };
        case "area": return { series: rowsToSeries(src), session: session };
        case "sparkline": return { series: rowsToSeries(src), session: session };
        case "fan": return { steps: src, session: session };
        case "distribution": return { buckets: (src || []).map(function (r) { return { label: r.label || r.name || "", value: r[a.vkY || "value"] }; }), session: session };
        case "heatmap": return { cells: src, session: session };
        case "gaugezones": return { value: src && src.value != null ? src.value : src, low: src && src.low, high: src && src.high, zones: src && src.zones, history: src && src.history, session: session };
        case "timeline": return { events: src, session: session };
        case "countbars": return { rows: src, session: session };
        case "donut": return { slices: (src || []).map(function (r) { return { label: r.label || r.name || "", value: r[a.vkY || "value"] }; }), session: session };
        case "stackedbar": return { slices: (src || []).map(function (r) { return { label: r.label || r.name || "", value: r[a.vkY || "value"] }; }), session: session };
        default: return { session: session };
      }
    }
    function renderAll(data) {
      var hosts = document.querySelectorAll("[data-vk]");
      hosts.forEach(function (host) {
        var prim = host.getAttribute("data-vk");
        var fn = VK[prim === "meterbench" ? "meterBench" : (prim === "gaugezones" ? "gaugeZones" : (prim === "countbars" ? "countBars" : (prim === "stackedbar" ? "stackedBar" : prim)))];
        if (!fn) return;
        host.innerHTML = fn(bindSpec(host, data));
        host.classList.add("vk-done");
      });
      var stamp = document.querySelector(".topbar .updated");
      var session = sessionOf(data);
      if (stamp && session && !/Data as of/.test(stamp.textContent)) {
        stamp.textContent = stamp.textContent + " Data as of " + String(session).slice(0, 10) + ".";
      }
    }
    function load(first) {
      fetch("data.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.text() : null; }).then(function (txt) {
        if (txt == null || txt === lastJson) return;
        lastJson = txt;
        var data;
        try { data = JSON.parse(txt); } catch (e) { return; }
        renderAll(data);
        if (!first) document.querySelectorAll("[data-vk]").forEach(function (h) { h.classList.add("vk-fade"); });
      }).catch(function () { /* The page existing content stays as it is. */ });
    }
    document.addEventListener("DOMContentLoaded", function () {
      if (!document.querySelector("[data-vk]")) return;
      load(true);
      var tapePage = !!document.querySelector('[data-vk="tape"]');
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (!reduce) setInterval(function () { load(false); }, (tapePage ? 5 : 15) * 60 * 1000);
      document.addEventListener("visibilitychange", function () { if (!document.hidden) load(false); });
    });
  }
})(typeof window !== "undefined" ? window : globalThis);
