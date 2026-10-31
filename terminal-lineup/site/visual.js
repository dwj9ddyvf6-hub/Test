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
    if (!data || typeof data !== "object") return null;
    var keys = ["as_of_session", "session", "as_of", "recorded_on", "published_at_utc", "generated_at_utc"];
    for (var i = 0; i < keys.length; i++) if (data[keys[i]]) return String(data[keys[i]]);
    return null;
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
    return '<svg class="vk-svg" viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + esc(label || "chart") + '" preserveAspectRatio="none">';
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
      return '<span class="vk-cal-cell' + cls + '" title="' + esc(d.date) + '">' + esc(String(d.date).slice(8, 10)) + "</span>";
    }).join("");
    var body = '<div class="vk-cal">' + cells + "</div>";
    return frame(input.title || null, input.label || "One cell per day in the window on record. Darker means more on that day.",
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

  /* P4 Dial: SVG arc so the geometry is inspectable in the DOM. */
  function dial(input) {
    input = input || {};
    var v = num(input.value), lo = num(input.low), hi = num(input.high);
    if (v == null) {
      if (input.have != null && input.need != null) return accrual(input);
      return stateCard(input.words || "No reading is on record yet.", input.session, 0, "readings");
    }
    if (lo == null || hi == null || hi <= lo) {
      return stateCard("A reading is on record (" + fmt(v) + ") but its scale is not stated, so no dial can be drawn honestly.", input.session, 1, "reading");
    }
    var frac = Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
    var cx = 110, cy = 105, r = 84;
    function polar(f) { var a = Math.PI * (1 - f); return [cx + r * Math.cos(a), cy - r * Math.sin(a)]; }
    var p0 = polar(0), p1 = polar(frac), pn = polar(frac);
    var s = svgOpen(220, 128, "reading dial");
    s += '<path d="M' + p0[0] + " " + p0[1] + " A" + r + " " + r + " 0 0 1 " + polar(1)[0] + " " + polar(1)[1] + '" class="vk-dial-track"></path>';
    if (frac > 0) s += '<path d="M' + p0[0] + " " + p0[1] + " A" + r + " " + r + " 0 0 1 " + p1[0] + " " + p1[1] + '" class="vk-dial-fill"></path>';
    s += '<line x1="' + cx + '" y1="' + cy + '" x2="' + pn[0] + '" y2="' + pn[1] + '" class="vk-dial-needle"></line>';
    s += '<text x="' + cx + '" y="' + (cy + 20) + '" text-anchor="middle" class="vk-dial-value">' + fmt(v) + "</text></svg>";
    var hist = Array.isArray(input.history) ? input.history.filter(function (h) { return num(h && (h.value != null ? h.value : h.y)) != null; }) : [];
    var extra = "";
    if (hist.length >= 2) {
      extra = line({ series: hist.map(function (h) { return { date: h.date || "", value: h.value != null ? h.value : h.y }; }), spark: true, session: input.session });
    }
    return frame(input.title || null, (input.label || "The headline reading") + ", on a scale of " + fmt(lo) + " to " + fmt(hi) + ".",
      '<div class="vk-dial">' + s + "</div>" + extra, input.session, 1, "reading");
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
        html += '<span class="bar"><i style="width:' + Math.max(2, Math.round(100 * Math.abs(s) / max)) + '%"></i></span><span class="vk-rscore">' + fmt(s) + "</span>";
        drawn++;
      } else {
        html += '<span class="bar"></span><span class="vk-rscore">no score on record</span>';
      }
      if (r.coverage != null) html += '<span class="vk-rcov">' + esc(r.coverage) + "</span>";
      if (r.status) html += '<span class="chip waiting">' + esc(r.status) + "</span>";
      html += "</div>";
    });
    html += "</div>";
    return frame(input.title || null, input.label || "Rows on record, best first. Bar length is set by the biggest score on this page.",
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
      html += '<div class="tile ' + cls + '"><span class="sym">' + esc(t.label) + '</span><br><span class="vk-tval">' + fmt(v) + "</span>" +
        (t.word ? "<br>" + esc(t.word) : "") + "</div>";
    });
    html += "</div>";
    return frame(input.title || null, input.label || "One tile per name on record. Colour follows the reading in this page data.",
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
    return frame(input.spark ? null : (input.title || null), input.spark ? null : (input.label || "How the headline figure moved, from the dated values on record. A gap means a missing session."),
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
    pairs.forEach(function (p) { s += '<circle cx="' + X(p.x) + '" cy="' + Y(p.y) + '" r="4" class="vk-dot"></circle>'; });
    s += '<text x="' + pad + '" y="' + (H - 8) + '" class="vk-axis">' + esc(input.xLabel || "first figure") + ": " + fmt(xLo) + " to " + fmt(xHi) + "</text>";
    s += '<text x="' + pad + '" y="14" class="vk-axis">' + esc(input.yLabel || "second figure") + ": " + fmt(yLo) + " to " + fmt(yHi) + "</text></svg>";
    var lacking = rows.length - pairs.length;
    return frame(input.title || null, input.label || "One dot per row that carries both figures.",
      s, input.session, pairs.length, "pairs", lacking ? lacking + " rows lacked a pair." : null);
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
    s += '<text x="' + (W - pad) + '" y="' + (H - 6) + '" text-anchor="end" class="vk-axis">' + esc(series[lastI].date || "") + " " + fmt(series[lastI].value) + "</text></svg>";
    return frame(input.title || null, input.label || "The dated values on record, with the space under the line filled so the size of the move is easy to see.", s, input.session, valid.length, "dated values");
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
    if (steps.some(function (st) { return st.low2 != null && st.high2 != null; })) s += bandPath("low2", "high2", "vk-fan-outer");
    s += bandPath("low", "high", "vk-fan-inner");
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
    return frame(input.title || null, input.label || "One bar per bucket on record, heights on one scale. Red bars sit below zero.", s, input.session, buckets.length, "buckets");
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
    return frame(input.title || null, input.label || "Counts on record, drawn on one scale so the big and small counts can be compared at a glance.", s, input.session, rows.length, "counts");
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
        var op = (0.15 + 0.85 * Math.abs(n) / maxAbs).toFixed(2);
        s += '<rect x="' + (padL + ci * cellW + 1) + '" y="' + (padT + ri * cellH + 1) + '" width="' + (cellW - 2) + '" height="' + (cellH - 2) + '" rx="3" class="' + cls + '" opacity="' + op + '"><title>' + esc(((input.rowLabels || [])[ri] || "") + " " + ((input.colLabels || [])[ci] || "") + ": " + fmt(n)) + "</title></rect>";
      });
    });
    (input.colLabels || []).forEach(function (c, ci) { s += '<text x="' + (padL + ci * cellW + cellW / 2) + '" y="' + (H - 6) + '" text-anchor="middle" class="vk-axis">' + esc(String(c).slice(0, 8)) + "</text>"; });
    s += "</svg>";
    return frame(input.title || null, input.label || "One cell per pair on record. Darker teal means a bigger value; red means below zero.", s, input.session, flat.length, "cells");
  }
  /* GaugeZones: a half-round dial whose rim is split into named zones. */
  function gaugeZones(input) {
    input = input || {};
    var v = num(input.value), lo = num(input.low), hi = num(input.high);
    if (v == null || lo == null || hi == null || hi <= lo) {
      if (input.have != null && input.need != null) return accrual(input);
      return stateCard(input.words || "No reading with a stated scale is on record yet.", input.session, 0, "readings");
    }
    var zones = (Array.isArray(input.zones) && input.zones.length) ? input.zones : [{ to: hi, label: "" }];
    var cx = 130, cy = 118, r = 96;
    function polar(f) { var a = Math.PI * (1 - Math.max(0, Math.min(1, f))); return [cx + r * Math.cos(a), cy - r * Math.sin(a)]; }
    function arc(f0, f1) { var a = polar(f0), b = polar(f1); return "M" + a[0].toFixed(1) + " " + a[1].toFixed(1) + " A" + r + " " + r + " 0 0 1 " + b[0].toFixed(1) + " " + b[1].toFixed(1); }
    var s = svgOpen(260, 140, "gauge");
    var prev = lo;
    zones.forEach(function (z, i) {
      var f0 = (prev - lo) / (hi - lo), f1 = (Math.min(z.to, hi) - lo) / (hi - lo);
      if (f1 > f0) s += '<path d="' + arc(f0, f1) + '" class="vk-zone vk-zone-' + (i % 4) + '"></path>';
      prev = z.to;
    });
    var frac = (v - lo) / (hi - lo), np = polar(frac);
    s += '<line x1="' + cx + '" y1="' + cy + '" x2="' + np[0].toFixed(1) + '" y2="' + np[1].toFixed(1) + '" class="vk-dial-needle"></line>';
    s += '<circle cx="' + cx + '" cy="' + cy + '" r="5" class="vk-cur"></circle>';
    s += '<text x="' + cx + '" y="' + (cy + 22) + '" text-anchor="middle" class="vk-dial-value">' + fmt(v) + "</text>";
    s += '<text x="8" y="' + (cy + 12) + '" class="vk-axis">' + esc(zones[0].label || fmt(lo)) + "</text>";
    s += '<text x="252" y="' + (cy + 12) + '" text-anchor="end" class="vk-axis">' + esc(zones[zones.length - 1].label || fmt(hi)) + "</text></svg>";
    return frame(input.title || null, input.label || "The needle sits in the zone the reading falls in. The zones are the ones this page itself names.", '<div class="vk-dial vk-gauge">' + s + "</div>", input.session, 1, "reading");
  }
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
  /* Donut: shares of a whole, slices to scale. */
  function donut(input) {
    input = input || {};
    var slices = (Array.isArray(input.slices) ? input.slices : []).filter(function (sl) { return sl && num(sl.value) != null && sl.value > 0; });
    var total = slices.reduce(function (a, sl) { return a + sl.value; }, 0);
    if (!slices.length || total <= 0) return stateCard(input.words || "No shares are on record yet.", input.session, 0, "shares");
    var cx = 80, cy = 80, r = 62, ir = 36;
    function pt(f, rad) { var a = Math.PI * 2 * f - Math.PI / 2; return [cx + rad * Math.cos(a), cy + rad * Math.sin(a)]; }
    var s = svgOpen(340, 160, "shares");
    var f = 0;
    slices.forEach(function (sl, i) {
      var f1 = f + sl.value / total, large = (f1 - f) > 0.5 ? 1 : 0;
      var a = pt(f, r), b = pt(f1, r), c = pt(f1, ir), dpt = pt(f, ir);
      s += '<path d="M' + a[0].toFixed(1) + " " + a[1].toFixed(1) + " A" + r + " " + r + " 0 " + large + " 1 " + b[0].toFixed(1) + " " + b[1].toFixed(1) + " L" + c[0].toFixed(1) + " " + c[1].toFixed(1) + " A" + ir + " " + ir + " 0 " + large + " 0 " + dpt[0].toFixed(1) + " " + dpt[1].toFixed(1) + ' Z" class="vk-slice vk-slice-' + (i % 5) + '"><title>' + esc(sl.label + ": " + fmt(sl.value)) + "</title></path>";
      f = f1;
    });
    var lx = 165;
    slices.forEach(function (sl, i) {
      var y = 24 + i * 19;
      s += '<rect x="' + lx + '" y="' + (y - 10) + '" width="10" height="10" class="vk-slice vk-slice-' + (i % 5) + '"></rect>';
      s += '<text x="' + (lx + 16) + '" y="' + y + '" class="vk-axis vk-legend">' + esc(String(sl.label).slice(0, 20)) + " " + fmt(sl.value) + " (" + Math.round(100 * sl.value / total) + "%)</text>";
    });
    s += "</svg>";
    return frame(input.title || null, input.label || "Each slice is one share of the whole on record, sized by its value.", s, input.session, slices.length, "shares");
  }

  var VK = {
    ladder: ladder, band: band, curve: curve, dial: dial, meterBench: meterBench,
    ranked: ranked, tiles: tiles, heatStrip: heatStrip, tape: tape, line: line,
    accrual: accrual, scatter: scatter, sessionOf: sessionOf, _esc: esc,
    area: area, sparkline: sparkline, fan: fan, distribution: distribution,
    heatmap: heatmap, gaugeZones: gaugeZones, timeline: timeline,
    countBars: countBars, donut: donut
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
        case "dial": return { value: src && src.value != null ? src.value : src, low: src && src.low, high: src && src.high, session: session };
        case "meterbench": return { value: src && src.value, benchmark: src && src.benchmark, graded: src && src.graded, needed: src && src.needed, session: session };
        case "ranked": return { rows: src, session: session };
        case "tiles": return { items: src, session: session };
        case "tape": return { events: src, session: session };
        case "line": return { series: rowsToSeries(src), session: session };
        case "accrual": return { have: src && src.have, need: src && src.need, unit: a.vkUnit || "items", session: session };
        case "scatter": return { rows: (src || []).map(function (r) { return { x: r[a.vkX], y: r[a.vkY], label: r.label || r.name }; }), session: session };
        case "area": return { series: rowsToSeries(src), session: session };
        case "sparkline": return { series: rowsToSeries(src), session: session };
        case "fan": return { steps: src, session: session };
        case "distribution": return { buckets: (src || []).map(function (r) { return { label: r.label || r.name || "", value: r[a.vkY || "value"] }; }), session: session };
        case "heatmap": return { cells: src, session: session };
        case "gaugezones": return { value: src && src.value != null ? src.value : src, low: src && src.low, high: src && src.high, zones: src && src.zones, session: session };
        case "timeline": return { events: src, session: session };
        case "countbars": return { rows: src, session: session };
        case "donut": return { slices: (src || []).map(function (r) { return { label: r.label || r.name || "", value: r[a.vkY || "value"] }; }), session: session };
        default: return { session: session };
      }
    }
    function renderAll(data) {
      var hosts = document.querySelectorAll("[data-vk]");
      hosts.forEach(function (host) {
        var prim = host.getAttribute("data-vk");
        var fn = VK[prim === "meterbench" ? "meterBench" : (prim === "gaugezones" ? "gaugeZones" : (prim === "countbars" ? "countBars" : prim))];
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
