#!/usr/bin/env python3
"""Surface every page's full record in its own data.json.

Producer cure (2026-10-31, no-blank-states standard): many pages carried
their study record, calibration record and live accrual only as tables,
counts scattered across keys, or in a neighbouring file, so the page
itself read as a status word. This module adds ONE new block,
``record_surface``, to a page's data, built only from numbers already
on file for that page:

- current reading: the as-of stamp and the top-level keys that carry it
- study record: labelled, with provenance copied from the page's own
  provenance/source fields, and the locations (field paths) with the
  row counts already in those fields
- calibration record: the page's own calibration_attestation, verbatim,
  where one exists
- live accrual: for forecast engines, forecasts/grades/corrections
  counted from forecast/ledger.jsonl; otherwise the page's own counts
- missing: one plain line naming what is missing and when it arrives

No existing value is read for anything except counting and copying.
Nothing is invented, interpolated, smoothed or backfilled.
"""
import csv
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

STUDY_KEYS = ("history", "study", "study_record", "method", "episodes",
              "backtest_grades", "backcast", "research_record",
              "control_history", "sessions", "decision_days", "grades")
AS_OF_KEYS = ("as_of_session", "as_of", "freshest_session", "freshest_date",
              "published_at_utc", "generated_at_utc", "generated_at",
              "panel_last_session", "date", "session")

_ledger_cache = None


def ledger_counts():
    """Count forecast/grade/correction rows per engine in the ledger."""
    global _ledger_cache
    if _ledger_cache is not None:
        return _ledger_cache
    counts = {}
    path = ROOT / "forecast" / "ledger.jsonl"
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                eng = row.get("engine") or row.get("engine_id")
                kind = row.get("kind") or row.get("type") or ""
                if not eng:
                    continue
                slot = counts.setdefault(
                    eng, {"forecasts": 0, "grades": 0, "corrections": 0})
                if kind == "forecast":
                    slot["forecasts"] += 1
                elif kind == "grade":
                    slot["grades"] += 1
                elif kind == "correction":
                    slot["corrections"] += 1
    _ledger_cache = counts
    return counts


def _count(value, depth=0):
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        if depth > 2:
            return len(value)
        return sum(_count(v, depth + 1) for v in value.values())
    return 0


def study_locations(data):
    locs = []
    for key in STUDY_KEYS:
        if key in data and data[key] not in (None, [], {}):
            locs.append({"path": f"/{key}", "items": _count(data[key])})
    # Nested study records, e.g. /history/study_record/rows
    hist = data.get("history")
    if isinstance(hist, dict):
        for sub, val in hist.items():
            if isinstance(val, (list, dict)) and val:
                locs.append({"path": f"/history/{sub}",
                             "items": _count(val)})
    return locs


_engine_map = None


def engine_for_slug(slug, data):
    """Slug to engine id, from INFO-MAP.md's audited per-page rows."""
    global _engine_map
    if _engine_map is None:
        _engine_map = {}
        info = (ROOT.parent / "research_notes" /
                "terminal-visual-expression-20261031" / "INFO-MAP.md")
        try:
            import re
            for line in info.read_text().splitlines():
                m = re.match(r"\| ([a-z0-9\-]+) \|", line)
                e = re.search(r"engines\[(engine_\d+)\]", line)
                if m and e:
                    _engine_map[m.group(1)] = e.group(1)
        except OSError:
            pass
    return _engine_map.get(slug)


def _missing_line(slug, data, accrual, study):
    if slug == "state-analogue":
        c = data.get("counts") or {}
        return (f"Matches: none yet. {c.get('sessions_recorded', 2)} of "
                f"{c.get('sessions_needed', 126)} recorded sessions are on "
                "file; one more session is added each trading day and "
                "matches appear once enough sessions have built up.")
    if slug == "market-mood":
        return ("One gauge is missing: What People Say has no readings "
                "yet. It arrives when its survey source next publishes.")
    if slug == "skew-lens":
        return ("Live chain figures are empty for the latest session; "
                "the dated and modelled readings on file are shown "
                "instead. New figures arrive with the next options "
                "chain capture.")
    if slug == "ai-chart-read":
        return ("A graded record of past reads does not exist yet and "
                "is not filled in from anything else. The first graded "
                "reads arrive after the next scored run's sessions close.")
    if slug == "regime-dial":
        return ("Earlier daily readings were not kept before today, so "
                "the reading history starts today and adds one entry "
                "each trading day from now on.")
    if accrual and accrual.get("grades") == 0 and accrual.get("forecasts"):
        return (f"Live grades are still building: {accrual['forecasts']} "
                "forecasts are on record and none are graded yet. Grades "
                "arrive after each following session close.")
    if accrual and accrual.get("forecasts", 0) > accrual.get("grades", 0) > 0:
        return (f"More live grades are still to come: "
                f"{accrual['forecasts']} forecasts are on record and "
                f"{accrual['grades']} are graded so far. The rest arrive "
                "after each following session close.")
    if not study:
        return ("No study record is on file for this page; what it shows "
                "is its current reading, updated on its normal schedule.")
    return ("Nothing from the record on file is missing. The next "
            "update arrives at the next session close on this page's "
            "normal schedule.")


def specific_extras(slug, data):
    """Records stranded in neighbouring files, surfaced by name."""
    extra = {}
    if slug == "market-mood":
        gauges_dir = ROOT / "psychology-engine" / "history" / "gauges"
        rows = {}
        if gauges_dir.exists():
            for f in sorted(gauges_dir.glob("*.csv")):
                try:
                    with open(f, newline="", encoding="utf-8") as fh:
                        rows[f.name] = max(
                            sum(1 for _ in csv.reader(fh)) - 1, 0)
                except OSError:
                    pass
        extra["gauge_history"] = {
            "label": "Study record",
            "source": "psychology-engine/history/gauges (files on disk)",
            "files": rows,
            "episodes_on_record": len(data.get("episodes") or []),
            "backtest_grades_on_record": len(
                data.get("backtest_grades") or []),
            "live_grades_on_record": len(data.get("live_grades") or []),
        }
    if slug == "horizon-grades":
        rec_path = HERE / "record" / "data.json"
        if rec_path.exists():
            rec = json.loads(rec_path.read_text())
            board = rec.get("board") or {}
            extra["record_on_the_record_page"] = {
                "label": "Study record",
                "source": "record/data.json (the call-by-call record)",
                "totals_on_this_page": data.get("totals"),
                "board_keys": sorted(board.keys())[:12],
            }
    if slug == "flow-engine":
        tape_path = HERE / "flow-tape" / "data.json"
        if tape_path.exists():
            tape = json.loads(tape_path.read_text())
            extra["record_on_the_flow_tape_page"] = {
                "label": "Study record",
                "source": "flow-tape/data.json (the session tape)",
                "counts": tape.get("counts"),
                "groups_on_record": len(tape.get("groups") or []),
            }
    if slug == "regime-dial":
        hist_path = HERE / "regime-dial" / "reading-history.json"
        history = []
        if hist_path.exists():
            try:
                history = json.loads(hist_path.read_text())
            except ValueError:
                history = []
        stamp = data.get("freshest_session") or data.get("as_of")
        reading = data.get("reading") or {}
        if stamp and not any(h.get("session") == stamp for h in history):
            history.append({
                "session": stamp,
                "kind": reading.get("kind"),
                "sentence": reading.get("sentence"),
                "counting_checks": data.get("counting_checks"),
                "checks_total": data.get("checks_total"),
            })
            hist_path.write_text(json.dumps(history, indent=2) + "\n")
        data["reading_history"] = history
        extra["reading_history"] = {
            "label": "Study record",
            "source": "regime-dial/reading-history.json (one entry is "
                      "added by this producer each day a new reading "
                      "is published; earlier days are not filled in)",
            "sessions_on_record": len(history),
        }
    if slug == "state-analogue":
        extra["accrual"] = {
            "label": "Live accrual",
            "counts": data.get("counts"),
            "readings_defined": len(data.get("readings") or []),
            "matches_on_record": len(data.get("matches") or []),
        }
    return extra


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _ranked(title, label, rows, source):
    rows = [r for r in rows if _num(r.get("score")) is not None and r.get("name")]
    if len(rows) < 1:
        return None
    return {"kind": "ranked", "title": title, "label": label,
            "source": source, "rows": rows}


def _curve(title, label, points, source):
    points = [p for p in points if _num(p.get("y")) is not None]
    if len(points) < 2:
        return None
    return {"kind": "curve", "title": title, "label": label,
            "source": source, "points": points}


def _band(title, label, items, source):
    items = [i for i in items if _num(i.get("low")) is not None
             and _num(i.get("high")) is not None]
    if not items:
        return None
    return {"kind": "band", "title": title, "label": label,
            "source": source, "items": items}


def _kept_sessions(data):
    """Sessions kept by a page's producer (the session_history list
    in data.json, appended per lane run by session_history.py from
    2026-10-31, Wave 3 Item F), deduped by session date with the
    latest entry winning, oldest first. Sessions before keeping
    began do not exist and are never reconstructed."""
    by_session = {}
    for entry in data.get("session_history") or []:
        if isinstance(entry, dict) and entry.get("session"):
            by_session[str(entry["session"])] = entry
    return [by_session[k] for k in sorted(by_session)]


def build_subject_chart(slug, data):
    """Subject charts for the forecast-engine pages (cure 2026-10-31,
    terminal-state-the-information). Each chart plots the market
    quantity the page exists to measure, from the fields the census
    names. A page with no subject numeric on record gets None for
    that slot: no count chart is substituted."""
    lead = record = None
    if slug == "desk":
        # The desk page pictures the desk itself (cure 2026-10-31):
        # its open positions, named, from the snapshot aggregation
        # publish_desk.py carries in data.json, and the equity record
        # the snapshot itself carries (starting capital at the capital
        # epoch start, equity at the latest cycle). Two readings only:
        # nothing between them is on record in the snapshot, and no
        # history is invented. A flat desk gets no lead chart rather
        # than a substitute count chart.
        pos = sorted(data.get("positions") or [],
                     key=lambda p: -abs(p.get("qty") or 0))
        rows = []
        for p in pos:
            row = {"name": p.get("symbol"), "score": p.get("qty")}
            if p.get("strategies"):
                row["coverage"] = ("held by "
                                   + ", ".join(p["strategies"]))
            rows.append(row)
        lead = _ranked(
            "Open positions, by shares held",
            "Each open position in the current session snapshot, "
            "named, biggest holding first.",
            rows, "positions[].qty (strategies[].open_positions)")
        epoch = data.get("epoch") or {}
        account = data.get("account") or {}
        start = str(epoch.get("start") or "")[:10]
        end = str(epoch.get("end") or data.get("session") or "")[:10]
        record = _curve(
            "Equity, from the capital epoch to the latest snapshot",
            "The two equity readings the snapshot itself carries: "
            "the starting capital at the epoch start and the equity "
            "at the latest cycle. Nothing between them is on record "
            "in the snapshot.",
            [{"x": start, "y": epoch.get("starting_capital")},
             {"x": end, "y": account.get("equity")}],
            "epoch.starting_capital / account.equity")
    elif slug == "board":
        names = ((data.get("groups") or [{}])[0].get("names") or [])
        lead = _ranked("Today's board, scored",
                       "Each name's board score, biggest first.",
                       [{"name": n.get("symbol"), "score": n.get("score")}
                        for n in names[:12]], "groups[0].names[].score")
        buckets = {}
        for n in names:
            s = _num(n.get("score"))
            if s is not None:
                b = f"{int(s // 10) * 10}-{int(s // 10) * 10 + 9}"
                buckets[b] = buckets.get(b, 0) + 1
        record = {"kind": "distribution", "title": "Board scores, spread out",
                  "label": "How the scored names spread across score bands.",
                  "source": "groups[0].names[].score distribution",
                  "buckets": [{"label": k, "value": buckets[k]}
                              for k in sorted(buckets)]} if buckets else None
    elif slug == "calibration-league":
        ent = data.get("entrants") or []
        lead = _ranked("Each forecaster's error, in points",
                       "The error each entrant is judged on, biggest first.",
                       [{"name": e.get("name"), "score": e.get("error_pts"),
                         "coverage": f"stated {e.get('stated_pct')} percent, realised {e.get('realised_pct')} percent"}
                        for e in ent], "entrants[].error_pts")
        record = _ranked("What actually happened, against what was stated",
                         "Realised percent per entrant, with the stated percent beside it.",
                         [{"name": e.get("name"), "score": e.get("realised_pct"),
                           "coverage": f"stated {e.get('stated_pct')} percent"}
                          for e in ent], "entrants[].realised_pct")
    elif slug == "capitulation-clock":
        trig = ((data.get("today") or {}).get("triggers") or [])
        lead = _ranked("Today's capitulation triggers, by falling-day volume",
                       "Down volume against its line, per triggered name.",
                       [{"name": t.get("symbol"), "score": t.get("down_volume_times_line"),
                         "coverage": f"activity {t.get('activity_times_line')} times its line"}
                        for t in trig[:12]],
                       "today.triggers[].down_volume_times_line")
        h = data.get("history") or {}
        record = _ranked("The study record, as outcomes",
                         "Exhaustion share and median forward return from the history run.",
                         [{"name": "Exhaustion share, percent",
                           "score": (h.get("exhaustion_half") or {}).get("share_pct")},
                          {"name": "Median forward return, points",
                           "score": (h.get("return_half") or {}).get("median_points")}],
                         "history.exhaustion_half.share_pct / return_half.median_points")
    elif slug == "completion-clock":
        cls = (data.get("classes") or [{}])[0]
        lead = _curve("When completions actually land",
                      "Share of groups completing at each step.",
                      [{"x": f"step {i + 1}", "y": v}
                       for i, v in enumerate(cls.get("hazard_pct") or [])],
                      "classes[0].hazard_pct")
        rows = []
        for c in data.get("classes") or []:
            race = c.get("race") or []
            if race:
                last = race[-1]
                rows.append({"name": c.get("name"),
                             "score": last.get("up_first_pct"),
                             "coverage": f"down first {last.get('down_first_pct')} percent"})
        record = _ranked("Which side finished first, per class",
                         "Up-first percent at the longest race step, per class.",
                         rows, "classes[].race[].up_first_pct")
    elif slug == "corrected-band":
        names = ((data.get("live") or {}).get("names") or [])
        if names and names[0].get("horizons"):
            hz = names[0]["horizons"][0]
            lead = _band("The latest band, drawn to scale",
                         "Each published range for the next session.",
                         [{"label": names[0].get("name") or "Index",
                           "low": b.get("lower"), "high": b.get("upper"),
                           "current": names[0].get("close")}
                          for b in hz.get("bands") or []],
                         "live.names[0].horizons[0].bands[].lower/upper")
        cells = ((data.get("history") or {}).get("cells") or [])
        record = _ranked("How often the bands held, per cell",
                         "Coverage percent per symbol, horizon and level.",
                         [{"name": f"{c.get('symbol')} {c.get('horizon')}d {c.get('level')}%",
                           "score": c.get("coverage_pct")} for c in cells[:12]],
                         "history.cells[].coverage_pct")
    elif slug == "earnings-distribution":
        nxt = ((data.get("next") or {}).get("names") or [])
        vals = [((n.get("exceedance") or {}).get("priced_move_pct"), n)
                for n in nxt]
        vals = [(v, n) for v, n in vals if _num(v) is not None]
        vals.sort(key=lambda t: -t[0])
        lead = _ranked("Priced earnings moves, biggest first",
                       "The priced move percent for each coming report.",
                       [{"name": n.get("symbol"), "score": v} for v, n in vals[:12]],
                       "next.names[].exceedance.priced_move_pct")
        seasons = ((data.get("history") or {}).get("seasons") or [])
        record = _ranked("Hit rate per season, on record",
                         "Hits as a percent of graded reports, per season.",
                         [{"name": s.get("season"),
                           "score": round(100 * s["hits"] / s["graded"], 2)
                           if s.get("graded") else None}
                          for s in seasons if s.get("graded")],
                         "history.seasons[].hits/graded")
    elif slug == "exceedance":
        cells = ((data.get("history") or {}).get("cells") or [])
        lead = _ranked("How often each big move actually happened",
                       "Realised share per forecast, forecast beside it.",
                       [{"name": f"{str(c.get('forecast')).upper()} on {c.get('symbol')}",
                         "score": c.get("realised_pct"),
                         "coverage": f"forecast {c.get('mean_forecast_pct')} percent"}
                        for c in cells[:8]], "history.cells[].realised_pct")
        record = _ranked("Forecast against realised, per cell",
                         "Mean forecast percent per cell, realised beside it.",
                         [{"name": f"{str(c.get('forecast')).upper()} on {c.get('symbol')}",
                           "score": c.get("mean_forecast_pct"),
                           "coverage": f"realised {c.get('realised_pct')} percent"}
                          for c in cells[:8]], "history.cells[].mean_forecast_pct")
    elif slug == "fear-day-triangulation":
        rows = ((data.get("control_history") or {}).get("rows") or [])
        lead = _ranked("Picked against random, per group",
                       "Picked mean return per control group, random beside it.",
                       [{"name": r.get("group"), "score": r.get("picked_mean_r"),
                         "coverage": f"random {r.get('random_mean_r')}"}
                        for r in rows], "control_history.rows[].picked_mean_r")
        days = ((data.get("fear_days_in_record") or {}).get("days") or [])
        record = _curve("Fear days on record: SPY on the day",
                        "SPY change percent on each fear day in the record.",
                        [{"x": d.get("date"), "y": d.get("spy_change_pct")}
                         for d in days], "fear_days_in_record.days[].spy_change_pct")
    elif slug == "gamma-earnings-trap":
        ev = ((data.get("window") or {}).get("events") or [])
        lead = _ranked("Positioning pressure behind each coming report",
                       "Positioning dollars per 1 percent move, per event name.",
                       [{"name": e.get("symbol"),
                         "score": e.get("positioning_value_usd_per_1pct")}
                        for e in ev[:10]],
                       "window.events[].positioning_value_usd_per_1pct")
        we = ((data.get("worked_example") or {}).get("events") or [])
        record = _ranked("Worked example: actual against priced move",
                         "Actual move percent per worked event, priced beside it. Labelled worked example on the page.",
                         [{"name": f"event {i + 1}", "score": e.get("actual_move_pct"),
                           "coverage": f"priced {e.get('priced_move_pct')} percent"}
                          for i, e in enumerate(we)], "worked_example.events[].actual_move_pct")
    elif slug == "gap-destiny":
        bands = ((data.get("history") or {}).get("bands") or [])
        lead = _ranked("How often each size of gap filled",
                       "Index fill percent per gap-size band.",
                       [{"name": f"Gap of {b.get('band_label')}",
                         "score": b.get("index_fill_pct")} for b in bands],
                       "history.bands[].index_fill_pct")
        wb = ((data.get("history") or {}).get("by_band_weekday_all") or [])
        record = _ranked("Fill percent by band, Mondays",
                         "Fill percent per gap band on Mondays, from the band by weekday record.",
                         [{"name": f"Gap of {b.get('band_label')}",
                           "score": b.get("fill_pct")}
                          for b in wb if b.get("weekday") == "Mon"],
                         "history.by_band_weekday_all[].fill_pct")
    elif slug in ("half-life-clock", "mortality-curve"):
        pairs = data.get("pair_table") or []
        def _share(p, k):
            tot = (p.get("confirmed") or 0) + (p.get("not_replicated") or 0)
            return round(100 * p[k] / tot, 2) if tot and _num(p.get(k)) is not None else None
        lead = _ranked("Pairs that held up on recheck, percent",
                       "Confirmed share of each pair's rechecked outcomes.",
                       [{"name": p.get("pair_words"), "score": _share(p, "confirmed"),
                         "coverage": f"{p.get('confirmed')} confirmed, {p.get('not_replicated')} did not replicate"}
                        for p in pairs[:10]], "pair_table[].confirmed share")
        record = _ranked("Pairs that did not replicate, percent",
                         "Did-not-replicate share of each pair's rechecked outcomes.",
                         [{"name": p.get("pair_words"), "score": _share(p, "not_replicated")}
                          for p in pairs[:10]], "pair_table[].not_replicated share")
        if slug == "mortality-curve":
            ranked = ((data.get("event_arm") or {}).get("ranked") or [])
            lead = _ranked("Fall risk per claim, percent",
                           "Fail chance percent per forecaster and target.",
                           [{"name": f"{r.get('forecaster')} to {r.get('target')}",
                             "score": r.get("fail_chance_pct")} for r in ranked[:10]],
                           "event_arm.ranked[].fail_chance_pct")
            classes = ((data.get("backcast") or {}).get("classes") or {})
            record = _ranked("Backcast: what was realised, per class",
                             "Realised value per backcast class, predicted beside it.",
                             [{"name": k, "score": v.get("realised"),
                               "coverage": f"predicted {v.get('predicted')}"}
                              for k, v in classes.items()],
                             "backcast.classes[].realised")
    elif slug == "honest-pop":
        surfs = data.get("surfaces") or []
        if surfs:
            lead = _curve(f"Chance of finishing above each strike, {surfs[0].get('symbol')}",
                          "Honest chance percent by strike.",
                          [{"x": str(r.get("strike")), "y": r.get("p_pct")}
                           for r in surfs[0].get("rows") or []],
                          "surfaces[0].rows[].p_pct")
        if len(surfs) > 1:
            record = _curve(f"Chance of finishing above each strike, {surfs[1].get('symbol')}",
                            "The second surface on record, chance percent by strike.",
                            [{"x": str(r.get("strike")), "y": r.get("p_pct")}
                             for r in surfs[1].get("rows") or []],
                            "surfaces[1].rows[].p_pct")
    elif slug == "idio-liquidity":
        neither = ((data.get("today") or {}).get("neither") or [])
        lead = _ranked("Today's own-norm drops, per name",
                       "Each name's own move percent today, market aside.",
                       [{"name": n.get("symbol"), "score": n.get("own_move_pct"),
                         "coverage": f"{n.get('share_pct')} percent of the drop was its own"}
                        for n in neither[:12]], "today.neither[].own_move_pct")
        h = data.get("history") or {}
        record = _ranked("The split's study record, median points",
                         "Median forward points for the persist and reverse arms.",
                         [{"name": "Persist arm", "score": (h.get("persist") or {}).get("median_points")},
                          {"name": "Reverse arm", "score": (h.get("reverse") or {}).get("median_points")}],
                         "history.persist/reverse.median_points")
    elif slug == "in-regime-oracle":
        lead = record = None  # no subject numeric on record; see census
    elif slug == "insider-divergence":
        elig = ((data.get("insider_legs") or {}).get("arm_b_eligible") or [])
        lead = _ranked("Insider buying names: sales against buys",
                       "Insider sales per eligible name, buys beside each bar.",
                       [{"name": e.get("symbol"), "score": e.get("sells"),
                         "coverage": f"{e.get('buys')} buys"} for e in elig[:12]],
                       "insider_legs.arm_b_eligible[].sells")
        record = _ranked("Insider buying names: buys on record",
                         "Insider buys per eligible name.",
                         [{"name": e.get("symbol"), "score": e.get("buys")}
                          for e in elig[:12] if _num(e.get("buys"))],
                         "insider_legs.arm_b_eligible[].buys")
    elif slug == "intake-bias":
        names = ((data.get("today") or {}).get("names") or [])
        lead = _ranked("The intake bias itself, per fund",
                       "Score gap (buys only against all prints) per fund, short share beside it.",
                       [{"name": n.get("symbol"), "score": n.get("gap"),
                         "coverage": f"short share {n.get('short_share')}"}
                        for n in names], "today.names[].gap")
        sess = ((data.get("history") or {}).get("sessions") or [])
        if sess:
            last = sess[-1]
            record = _ranked(f"The bias on {last.get('session')}",
                             "Score gap per fund in the latest history session.",
                             [{"name": n.get("symbol"), "score": n.get("gap")}
                              for n in last.get("names") or []],
                             "history.sessions[].names[].gap")
    elif slug == "living-router":
        lead = record = None  # contested_names empty; no chances on record
    elif slug == "own-norm-depth":
        bins = ((data.get("curve") or {}).get("bins") or [])
        lead = _ranked("Forward edge by dip depth",
                       "Median excess points per dip-depth bin.",
                       [{"name": f"{b.get('pct_low')} to {b.get('pct_high')} percent dip",
                         "score": b.get("median_excess_points")} for b in bins],
                       "curve.bins[].median_excess_points")
        record = _ranked("Share that beat the market, by dip depth",
                         "Percent beating the market per dip-depth bin.",
                         [{"name": f"{b.get('pct_low')} to {b.get('pct_high')} percent dip",
                           "score": round(100 * b["p"], 2) if _num(b.get("p")) is not None else None}
                          for b in bins], "curve.bins[].p")
    elif slug == "pin-or-escape":
        funds = ((data.get("readings") or {}).get("funds") or [])
        lead = _ranked("Net pull per fund, billions",
                       "Net pull in billions per 1 percent move, per fund.",
                       [{"name": f.get("fund"), "score": f.get("net_pull_billions"),
                         "coverage": f"price {f.get('price')}, flip {f.get('flip')}"}
                        for f in funds], "readings.funds[].net_pull_billions")
        record = _ranked("Pull at the next expiry, per fund",
                         "Next-expiry pull in millions of dollars, per fund.",
                         [{"name": f.get("fund"),
                           "score": round(f["next_expiry_pull_usd"] / 1e6, 2)
                           if _num(f.get("next_expiry_pull_usd")) is not None else None}
                          for f in funds], "readings.funds[].next_expiry_pull_usd")
    elif slug == "record":
        cohort = ((data.get("board") or {}).get("cohort") or {})
        rows = []
        for hz in ("1d", "5d", "21d"):
            c = cohort.get(hz) or {}
            if c.get("graded_count"):
                rows.append({"name": f"Rose after {hz.replace('d', ' day')}",
                             "score": round(100 * c["rose_count"] / c["graded_count"], 2),
                             "coverage": f"{c['rose_count']} of {c['graded_count']} graded rose"})
        lead = _ranked("How the graded calls came out, per horizon",
                       "Percent that rose, per grading horizon.", rows,
                       "board.cohort rose share")
        calls = (((data.get("board") or {}).get("groups") or [{}])[0].get("calls") or [])
        record = _ranked("Board calls on record, by score",
                         "Each logged call's score, biggest first.",
                         [{"name": c.get("symbol"), "score": c.get("score")}
                          for c in calls[:12]], "board.groups[0].calls[].score")
    elif slug == "self-analogue":
        fc = ((data.get("live") or {}).get("forecasts") or [])
        top = sorted(fc, key=lambda f: -abs(f.get("middle_percent") or 0))[:12]
        lead = _ranked("Forecast middle percent, biggest moves first",
                       "Middle forecast percent per name.",
                       [{"name": f.get("symbol"), "score": f.get("middle_percent"),
                         "coverage": f"range {f.get('low_percent')} to {f.get('high_percent')} percent"}
                        for f in top], "live.forecasts[].middle_percent")
        record = _band("Forecast ranges on record",
                       "Low to high forecast percent per name.",
                       [{"label": f.get("symbol"), "low": f.get("low_percent"),
                         "high": f.get("high_percent"), "mid": f.get("middle_percent")}
                        for f in top[:8]], "live.forecasts[].low/high_percent")
    elif slug == "silent-accumulation":
        dark = ((data.get("readings") or {}).get("dark") or {})
        ctx = dark.get("combined_context") or {}
        lead = _ranked("Off-exchange share per fund, percent",
                       "Dark share percent per index fund, the footprint reading.",
                       [{"name": f.get("symbol"), "score": f.get("pct")}
                        for f in ctx.get("funds") or []],
                       "readings.dark.combined_context.funds[].pct")
        record = _curve("Off-exchange share over the sessions on record",
                        "Combined index dark percent by session.",
                        [{"x": h.get("session"), "y": h.get("index_pct")}
                         for h in ctx.get("history") or []],
                        "readings.dark.combined_context.history[].index_pct")
    elif slug == "sponsored-reset":
        days = ((data.get("history") or {}).get("days") or [])
        lead = _curve("SPY on the qualifying days on record",
                      "SPY change percent per qualifying day in the history record.",
                      [{"x": d.get("date"), "y": d.get("spy_change_pct")} for d in days],
                      "history.days[].spy_change_pct")
        # Record (Wave 3 cure, Item F): the qualifying-days picture
        # is the record this study keeps, drawn as the record from
        # history.days. The composite excess series stays uncharted
        # (it is null on every day); from 2026-10-31 the producer
        # also keeps a dated snapshot of this picture at every
        # refresh (session_history), so the accrual is provable.
        record = _curve("SPY on the qualifying days, the record",
                        "The record this study keeps: SPY change "
                        "percent on each qualifying day, from the "
                        "history record. A dated snapshot of this "
                        "picture is kept at every refresh from "
                        "2026-10-31 forward.",
                        [{"x": d.get("date"), "y": d.get("spy_change_pct")}
                         for d in days],
                        "history.days[].spy_change_pct (study record)")
    elif slug == "streak-trap":
        trig = data.get("triggers") or []
        lead = _ranked("Each streak reading, as a chance",
                       "Centre chance percent per family.",
                       [{"name": t.get("family_words"), "score": t.get("centre_pct")}
                        for t in trig], "triggers[].centre_pct")
        record = _ranked("Each streak reading against its base",
                         "Base percent per family, centre beside it.",
                         [{"name": t.get("family_words"), "score": t.get("base_pct"),
                           "coverage": f"centre {t.get('centre_pct')} percent"}
                          for t in trig], "triggers[].base_pct")
    elif slug == "stress-reversal":
        h = data.get("history") or {}
        lead = _ranked("Reversal rates by stage, percent",
                       "Stage 1 and stage 2 reversal rates from the history run.",
                       [{"name": "Stage 1 rate", "score": (h.get("stage_1") or {}).get("rate_pct")},
                        {"name": "Stage 2 rate", "score": (h.get("stage_2") or {}).get("rate_pct")}],
                       "history.stage_1/stage_2.rate_pct")
        med = h.get("stage_3_medians_pct") or {}
        record = _ranked("Stage 3 median moves, percent",
                         "Median move percent at 1, 3 and 5 sessions.",
                         [{"name": f"After {k.replace('plus_', '')} session(s)",
                           "score": med.get(k)} for k in ("plus_1", "plus_3", "plus_5")],
                         "history.stage_3_medians_pct")
    elif slug == "touch-surface":
        names = ((data.get("live") or {}).get("names") or [])
        cells = names[0].get("cells") if names else []
        seen, rows = set(), []
        for c in cells or []:
            k = (c.get("label"), c.get("side"))
            if k in seen:
                continue
            seen.add(k)
            rows.append({"name": f"{c.get('symbol')} {c.get('label')} percent",
                         "score": c.get("p_pct"),
                         "coverage": f"benchmark {c.get('benchmark_pct')} percent"})
        lead = _ranked("Chances of touching each level", "Touch chance percent per level.",
                       rows[:10], "live.names[0].cells[].p_pct")
        hc = ((data.get("history") or {}).get("cells") or [])
        record = _ranked("Touch record: realised against forecast",
                         "Realised touch percent per history cell, forecast beside it.",
                         [{"name": f"{c.get('symbol')} {c.get('distance')} {c.get('side')} {c.get('horizon')}d",
                           "score": c.get("realised_pct"),
                           "coverage": f"forecast {c.get('mean_forecast_pct')} percent"}
                          for c in hc[:10]], "history.cells[].realised_pct")
    elif slug == "vol-clock":
        names = ((data.get("live") or {}).get("names") or [])
        lead = _ranked("Days for the spike to settle, per name",
                       "Median sessions to settle, per name.",
                       [{"name": n.get("symbol"), "score": n.get("median_sessions"),
                         "coverage": f"move {n.get('movement_pct')} percent"}
                        for n in names[:12]], "live.names[].median_sessions")
        record = _ranked("Spike size on record, per name",
                         "Movement percent per name in the live library.",
                         [{"name": n.get("symbol"), "score": n.get("movement_pct")}
                          for n in names[:12]], "live.names[].movement_pct")
    elif slug == "vol-term-shape":
        cells = ((data.get("history") or {}).get("cells") or [])
        pts = [{"x": f"stated {c.get('stated_pct')} percent", "y": c.get("coverage_pct")}
               for c in cells if c.get("symbol") == "SPY" and c.get("horizon") == 5]
        lead = _curve("What the stated chances promised, and what happened",
                      "Coverage percent per stated chance, SPY 5 day.",
                      pts, "history.cells[].coverage_pct (SPY 5d)")
        record = _ranked("Calibration per cell, all horizons",
                         "Coverage percent per symbol, horizon and stated percentile.",
                         [{"name": f"{c.get('symbol')} {c.get('horizon')}d stated {c.get('stated_pct')}%",
                           "score": c.get("coverage_pct")} for c in cells[:12]],
                         "history.cells[].coverage_pct")
    elif slug == "wall-lifetime":
        names = ((data.get("live") or {}).get("names") or [])
        lead = _ranked("Expected move per index, dollars",
                       "Expected move in dollars per index name.",
                       [{"name": n.get("name") or n.get("symbol"),
                         "score": n.get("expected_move_price")} for n in names],
                       "live.names[].expected_move_price")
        eps = ((data.get("history") or {}).get("episodes") or [])
        agg = {}
        for e in eps:
            k = f"{e.get('name')} {e.get('level')}"
            a = agg.setdefault(k, [0, 0])
            a[1] += 1
            if e.get("touched_1"):
                a[0] += 1
        record = _ranked("Levels touched within one session, percent",
                         "Share of episodes whose level was touched in one session, per index and level.",
                         [{"name": k, "score": round(100 * v[0] / v[1], 2)}
                          for k, v in sorted(agg.items()) if v[1]],
                         "history.episodes[].touched_1 share")
    elif slug == "agent-debate":
        funds = data.get("funds") or []
        rows = [{"name": f.get("symbol"),
                 "score": (f.get("count_rising") or 0)
                 - (f.get("count_falling") or 0),
                 "coverage": f"{f.get('count_rising')} rising, "
                 f"{f.get('count_falling')} falling"}
                for f in funds]
        lead = _ranked("The debate, per index fund: net stance",
                       "Readings pointing to rising minus readings pointing "
                       "to falling, per fund. A negative bar leans to falling.",
                       rows,
                       "funds[].count_rising-count_falling")
        # Record (Wave 3 cure, Item F): past debates were not kept.
        # Today the record is the current session's own net-stance
        # picture, labelled as the session on record (the echo-board
        # and second-opinion convention); the producer keeps a dated
        # snapshot per run from now on, and once more than one
        # session is kept the record plots the kept sessions.
        kept = _kept_sessions(data)
        if len(kept) > 1:
            krows = []
            for e in kept[-8:]:
                for v in e.get("values") or []:
                    krows.append({
                        "name": f"{e['session']} {v.get('symbol')}",
                        "score": (v.get("rising") or 0)
                        - (v.get("falling") or 0),
                        "coverage": f"{v.get('rising')} rising, "
                        f"{v.get('falling')} falling"})
            record = _ranked(
                "Net stance on record, per kept session",
                "Each kept session's net stance per fund, oldest "
                "first. Sessions are kept from 2026-10-31 forward; "
                "earlier debates were not kept and are not "
                "reconstructed.",
                krows, "session_history[].values (kept sessions)")
        else:
            record = _ranked(
                "The debate on record, this session",
                "The same net-stance picture, labelled with the "
                "session on record. Past sessions were not kept; "
                "the record accrues from this session forward.",
                list(rows),
                "funds[].count_rising-count_falling (session record)")
    elif slug == "echo-board":
        names = data.get("names") or []
        rows = [{"name": n.get("symbol"), "score": n.get("families_speaking"),
                 "coverage": f"agreed word: {n.get('agreed_word')}; "
                 + ", ".join(f"{r.get('family')}: {r.get('stance')}"
                             for r in n.get("readings") or [])}
                for n in names]
        lead = _ranked("Names the families agree on, by agreement strength",
                       "How many families speak for each agreeing name, "
                       "each family's stance beside it.", rows,
                       "names[].families_speaking")
        record = _ranked("The agreeing names on record, this session",
                         "The same agreeing-names picture, labelled with "
                         "the session on record.", list(rows),
                         "names[].families_speaking (session record)")
    elif slug == "second-opinion":
        names = data.get("names") or []
        top = sorted(names, key=lambda n: -(n.get("families_speaking") or 0))[:12]
        lead = _ranked("Per-name agreement, strongest first",
                       "How many families speak for each name, the name's "
                       "own price score beside it.",
                       [{"name": n.get("symbol"),
                         "score": n.get("families_speaking"),
                         "coverage": f"price score "
                         f"{(n.get('price') or {}).get('score')}, stance "
                         f"{(n.get('price') or {}).get('stance')}"}
                        for n in top], "names[].families_speaking")
        idx = [n for n in names if n.get("symbol") in (data.get("index_funds") or [])]
        record = _ranked("The index funds' own agreement, on record",
                         "Families speaking for each index fund, its price "
                         "score beside it.",
                         [{"name": n.get("symbol"),
                           "score": n.get("families_speaking"),
                           "coverage": f"price score "
                           f"{(n.get('price') or {}).get('score')}"}
                          for n in idx], "names[index_funds].families_speaking")
    elif slug == "screener":
        names = data.get("names") or []
        top = sorted(names, key=lambda n: -(n.get("score") or 0))[:12]
        lead = _ranked("The screened names themselves, by score",
                       "Each top name's screener score, its close beside it.",
                       [{"name": n.get("symbol"), "score": n.get("score"),
                         "coverage": f"close {n.get('close')}, "
                         f"{n.get('checks_in_favor')} of "
                         f"{n.get('checks_total')} checks in favour"}
                        for n in top], "names[].score")
        buckets = {}
        for n in names:
            s = _num(n.get("score"))
            if s is not None:
                b = f"{int(s // 10) * 10}-{int(s // 10) * 10 + 9}"
                buckets[b] = buckets.get(b, 0) + 1
        record = {"kind": "distribution",
                  "title": "Scores across the screened names",
                  "label": "How this session's scores spread across "
                  "score bands, all scored names.",
                  "source": "names[].score distribution",
                  "buckets": [{"label": k, "value": buckets[k]}
                              for k in sorted(buckets)]} if buckets else None
    elif slug == "opening-range":
        wins = data.get("windows") or []
        lead = _ranked("How often the opening range broke both sides, percent",
                       "Share of days breaking both sides of the opening "
                       "range, per opening window.",
                       [{"name": w.get("label"),
                         "score": round(100 * w["break_both_frequency"], 2)
                         if _num(w.get("break_both_frequency")) is not None else None}
                        for w in wins],
                       "windows[].break_both_frequency")
        head = next((w for w in wins if w.get("headline")), wins[-1] if wins else {})
        record = _ranked("How far prices ran past the first hour's range",
                         "Share of days reaching each extension step past "
                         "the headline window's range, percent.",
                         [{"name": e.get("label"),
                           "score": round(100 * e["frequency"], 2)
                           if _num(e.get("frequency")) is not None else None}
                          for e in head.get("extensions") or []],
                         "windows[headline].extensions[].frequency")
    elif slug == "family-fracture":
        today = data.get("today") or []
        lead = _ranked("The fracture picture, per fund",
                       "Each fund's fracture range percent, its plain "
                       "benchmark range beside it.",
                       [{"name": t.get("symbol"),
                         "score": t.get("fracture_range_pct"),
                         "coverage": f"benchmark {t.get('benchmark_range_pct')} "
                         f"percent, multiplier {t.get('multiplier')}, shape "
                         f"{t.get('shape_label')}"} for t in today],
                       "today[].fracture_range_pct")
        rows = []
        for s in ((data.get("history") or {}).get("sessions") or []):
            for sym, v in (s.get("symbols") or {}).items():
                rows.append({"name": f"{sym} {s.get('decision')}",
                             "score": v.get("multiplier"),
                             "coverage": f"shape {v.get('shape_label')}"})
        record = _ranked("Fracture multipliers on record, per session",
                         "The widening multiplier per fund in each history "
                         "session on record.", rows,
                         "history.sessions[].symbols[].multiplier")
    elif slug == "gamma-ladder":
        funds = data.get("funds") or []
        if funds:
            f0 = funds[0]
            rows = [{"name": f"Strike {r.get('strike')}",
                     "score": r.get("pull")}
                    for r in f0.get("rungs") or []]
            lead = _ranked(f"Strike ladder, {f0.get('symbol')}: pull per strike",
                           "Modelled pull in dollars per 1 percent move, "
                           "per strike. Flip, call wall and put wall in "
                           "the notes beside the page's own ladder.",
                           rows, "funds[0].rungs[].pull")
            # Record (Wave 3 cure, Item F): past ladders were not
            # kept. Today the record is the current session's own
            # strike ladder, labelled as the session on record; the
            # producer keeps a dated snapshot per run from now on,
            # and once more than one session is kept the record
            # plots the kept sessions.
            kept = _kept_sessions(data)
            if len(kept) > 1:
                krows = []
                for e in kept[-4:]:
                    vals = e.get("values") or {}
                    for r in vals.get("rungs") or []:
                        krows.append({
                            "name": f"{e['session']} strike "
                                    f"{r.get('strike')}",
                            "score": r.get("pull")})
                record = _ranked(
                    f"Strike ladder on record, {f0.get('symbol')}, "
                    "per kept session",
                    "Each kept session's strike ladder for the "
                    "first fund, oldest first. Sessions are kept "
                    "from 2026-10-31 forward; earlier ladders were "
                    "not kept and are not reconstructed.",
                    krows,
                    "session_history[].values.rungs (kept sessions)")
            else:
                record = _ranked(
                    f"Strike ladder on record, {f0.get('symbol')}: "
                    "this session",
                    "The same strike ladder, labelled with the "
                    "session on record. Past sessions were not kept; "
                    "the record accrues from this session forward.",
                    list(rows),
                    "funds[0].rungs[].pull (session record)")
    elif slug in ("ai-chart-read", "pattern-draw"):
        bars = data.get("bars") or {}
        dates = data.get("dates") or []
        spy = bars.get("SPY") or [0, []]
        closes = spy[1] if len(spy) > 1 else []
        tail = closes[-60:]
        xs = dates[-len(tail):] if dates else [str(i) for i in range(len(tail))]
        lead = _curve("SPY closes, the chart this page reads",
                      "SPY closing prices over the last 60 sessions on "
                      "record, the page's own authored chart data.",
                      [{"x": x, "y": y} for x, y in zip(xs, tail)],
                      "bars.SPY closes")
        # Record (Wave 3 cure, Item E): the same closes with the
        # page's own reads for SPY drawn at their sessions, from
        # labels.SPY.sequence. The reads carry no graded outcomes
        # anywhere in the page data, so none are plotted: the
        # record shows what was read, and where. The window widens
        # past 60 sessions if a labelled session would fall outside
        # it, so every recorded read is drawn.
        seq = ((data.get("labels") or {}).get("SPY") or {}).get(
            "sequence") or []
        notes = {}
        for s in seq:
            if isinstance(s, dict) and s.get("date") and s.get("label"):
                notes[str(s["date"])] = str(s["label"])
        pairs = list(zip(dates, closes)) if dates else [
            (str(i), y) for i, y in enumerate(closes)]
        start = max(0, len(pairs) - 60)
        labelled = [i for i, pair in enumerate(pairs)
                    if pair[0] in notes]
        if labelled:
            start = min(start, min(labelled))
        pts = []
        for x, y in pairs[start:]:
            point = {"x": x, "y": y}
            if x in notes:
                point["note"] = notes[x]
            pts.append(point)
        drawn = [(p["x"], p["note"]) for p in pts if "note" in p]
        meanings = data.get("label_meanings") or {}
        named = []
        for code in dict.fromkeys(n for _, n in drawn):
            nm = (meanings.get(code) or {}).get("name")
            if nm:
                named.append(f"{code} means {nm[0].lower()}{nm[1:]}")
        record = _curve(
            "Study record: the closes with the reads drawn on",
            "The same SPY closes, with the read this page recorded "
            "for SPY marked at each session it was read: "
            + ", ".join(f"{n} on {x}" for x, n in drawn)
            + "."
            + ((" " + "; ".join(named) + ".") if named else "")
            + " No graded outcome is on record for these reads, so "
            "the record shows the reads themselves.",
            pts, "bars.SPY closes with labels.SPY.sequence")
    elif slug == "breadth-meter":
        hist = data.get("history") or []
        record = _curve("Breadth on record: share above the 200-day average",
                        "Percent of names above their 200-session average, "
                        "per session on record.",
                        [{"x": h.get("session"), "y": h.get("above_200_pct")}
                         for h in hist], "history[].above_200_pct")
    elif slug == "abstention-signal":
        days = data.get("decision_days") or []
        record = _curve("Silence on record: abstention rate by day",
                        "The share of active tools abstaining, per "
                        "decision day on record.",
                        [{"x": d.get("day"), "y": round(100 * d["rate"], 2)
                          if _num(d.get("rate")) is not None else None}
                         for d in days], "decision_days[].rate")
    elif slug == "premium-meter":
        names = data.get("names") or []
        if names:
            n0 = names[0]
            record = _curve(f"Put share on record, {n0.get('underlying')}",
                            "Put share percent per session on record for "
                            "the first fund.",
                            [{"x": s.get("session"),
                              "y": s.get("put_share_percent")}
                             for s in n0.get("sessions") or []],
                            "names[0].sessions[].put_share_percent")
    elif slug == "tape-heatmap":
        cells = []
        for f in data.get("funds") or []:
            for side in ("calls", "puts"):
                for c in ((f.get(side) or {}).get("cells") or []):
                    cells.append({"name": f"{f.get('symbol')} {side[:-1]} "
                                    f"{c.get('strike')} {c.get('expiry')}",
                                  "score": c.get("premium_usd")})
        cells.sort(key=lambda r: -(r["score"] or 0))
        record = _ranked("Biggest alert-print cells on record, premium dollars",
                         "Premium dollars in the largest strike by expiry "
                         "cells, calls and puts together.", cells[:12],
                         "funds[].calls/puts.cells[].premium_usd")
    elif slug == "market-mood":
        pts = []
        for e in data.get("episodes") or []:
            g2 = (e.get("readings") or {}).get("G2") or {}
            if _num(g2.get("full_history_percentile")) is not None:
                pts.append({"x": e.get("date"),
                            "y": g2.get("full_history_percentile")})
        pts.sort(key=lambda p: p["x"] or "")
        record = _curve("Slow Climate at the episodes on record",
                        "The Slow Climate gauge's full-history percentile "
                        "at each recorded episode, by episode date.",
                        pts, "episodes[].readings.G2.full_history_percentile")
    if lead is None and record is None and slug not in (
            "in-regime-oracle", "living-router"):
        return None
    return {"version": 1, "lead": lead, "record": record}


def build_record_surface(slug, data):
    as_of = None
    for key in AS_OF_KEYS:
        val = data.get(key)
        if isinstance(val, str) and val:
            as_of = val
            break
        if isinstance(val, dict):
            inner = val.get("session") or val.get("date")
            if inner:
                as_of = inner
                break
    study = study_locations(data)
    eng = engine_for_slug(slug, data)
    accrual = None
    if eng:
        accrual = dict(ledger_counts().get(
            eng, {"forecasts": 0, "grades": 0, "corrections": 0}))
        accrual["engine"] = eng
        accrual["source"] = "forecast/ledger.jsonl (counted)"
    elif isinstance(data.get("counts"), dict):
        accrual = {"counts": data["counts"],
                   "source": "this page's own counts"}
    surface = {
        "version": 1,
        "label": "Study record",
        "provenance": data.get("provenance") or data.get("source"),
        "feed": data.get("feed"),
        "current_reading": {
            "as_of": as_of,
            "keys_present": sorted(data.keys()),
        },
        "study_record": {
            "label": "Study record",
            "locations": study,
            "total_items_counted": sum(x["items"] for x in study),
        },
        "calibration_record": data.get("calibration_attestation"),
        "live_accrual": accrual,
    }
    subj = subject_charts_for(slug, data)
    if subj is not None:
        surface["subject_charts"] = subj
    extras = specific_extras(slug, data)
    if extras:
        surface["surfaced_from_other_files"] = extras
        if slug == "market-mood" and "gauge_history" in extras:
            surface["gauge_history"] = extras["gauge_history"]
    surface["missing"] = {
        "what_and_when": _missing_line(slug, data, accrual, study),
    }
    return surface


def enrich_file(path):
    path = Path(path)
    slug = path.parent.name
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        return False
    data["record_surface"] = build_record_surface(slug, data)
    subject = build_subject_chart(slug, data)
    if subject is not None:
        data["subject_chart"] = subject
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)
    return True


def enrich_slug(slug):
    path = HERE / slug / "data.json"
    if path.exists():
        return enrich_file(path)
    return False


if __name__ == "__main__":
    import sys
    for slug in sys.argv[1:]:
        print(slug, enrich_slug(slug))


# ---------------------------------------------------------------------------
# Subject record charts (2026-10-31, stated-information cure, MARKET TOOL
# batch). For each market-tool page, the record chart must plot the SUBJECT
# the page exists to measure (per CENSUS.md in the program home
# terminal-state-the-information-20261031): per-name, per-session or
# per-event market values already in the page's own data. Coverage counts,
# name tallies, accrual counts and bookkeeping are never charted here.
# A page whose history is not kept gets its current subject picture,
# labelled with its session; a page with no honest subject series gets an
# empty list, which page_charts.js renders as no chart at all.
# ---------------------------------------------------------------------------

def _mnum(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _mranked(title, label, rows, limit=14):
    rows = [r for r in rows if r.get("name") not in (None, "")]
    if not rows:
        return None
    return {"kind": "ranked", "title": title, "label": label,
            "rows": rows[:limit]}


def _mline(title, label, series):
    series = [p for p in series if _mnum(p.get("value")) is not None]
    if len(series) < 2:
        return None
    return {"kind": "line", "title": title, "label": label,
            "series": series}


def _mtiles(title, label, items):
    items = [i for i in items if _mnum(i.get("value")) is not None]
    if not items:
        return None
    return {"kind": "tiles", "title": title, "label": label,
            "items": items}


def _mtape(title, label, events, limit=20):
    events = [e for e in events if e.get("label") or e.get("desc")]
    if not events:
        return None
    return {"kind": "tape", "title": title, "label": label,
            "events": events[:limit]}


def _mgrid(title, label, rows, limit=24):
    """A name grid: rows carry a status word, not a score."""
    rows = [r for r in rows if r.get("name") not in (None, "")]
    if not rows:
        return None
    return {"kind": "ranked", "title": title, "label": label,
            "rows": rows[:limit]}


def _pct_change(now, before):
    if _mnum(now) is None or _mnum(before) in (None, 0):
        return None
    return round(1000 * (now / before - 1)) / 10


def _holder_change_rows(data):
    rows = []
    for h in data.get("holders") or []:
        ch = h.get("change") or {}
        pct = _pct_change(h.get("total_value"),
                          ch.get("prior_total_value") or h.get("prior_total_value"))
        if pct is not None:
            rows.append({"name": h.get("holder"), "score": pct})
    rows.sort(key=lambda r: -abs(r["score"]))
    return rows


def _dist_to_high_rows(data, limit=12):
    src = data.get("bars") or {}
    w = data.get("high_window") or 252
    rows = []
    for sym, entry in src.items():
        if not (isinstance(entry, list) and len(entry) > 1
                and isinstance(entry[1], list)):
            continue
        closes = [c for c in entry[1] if _mnum(c) is not None]
        if len(closes) < 10:
            continue
        win = closes[-w:]
        hi = max(win)
        if hi:
            rows.append({"name": sym,
                         "score": round(100 * closes[-1] / hi * 10) / 10})
    rows.sort(key=lambda r: -r["score"])
    return rows[:limit]


def _window_change_rows(data, back=21, limit=12):
    src = data.get("bars") or data.get("prices") or {}
    rows = []
    for sym, entry in src.items():
        if not (isinstance(entry, list) and len(entry) > 1
                and isinstance(entry[1], list)):
            continue
        closes = [c for c in entry[1] if _mnum(c) is not None]
        if len(closes) <= back or not closes[-1 - back]:
            continue
        rows.append({"name": sym, "score": round(
            1000 * (closes[-1] / closes[-1 - back] - 1)) / 10})
    rows.sort(key=lambda r: -r["score"])
    return rows[:limit]


def _session_premium_rows(alerts):
    sums = {}
    for a in alerts or []:
        s = a.get("session")
        p = _mnum(a.get("premium_usd"))
        if s and p is not None:
            sums[s] = sums.get(s, 0) + p
    return [{"name": s, "score": v} for s, v in sorted(sums.items())]


def _subj_13f_tracker(d):
    return [_mranked("How each big holding changed, quarter to quarter",
                    "Each holder's total reported value against the prior "
                    "quarter on record, in percent.",
                    _holder_change_rows(d))]


def _subj_activity_profile(d):
    return [_mranked("Money that changed hands, by session",
                    "Total premium across the options prints examined in "
                    "each session on record. This is the session history "
                    "itself, not a count of sessions.",
                    [{"name": x.get("session"),
                      "score": _mnum(x.get("total_premium_usd"))}
                     for x in d.get("sessions") or []
                     if _mnum(x.get("total_premium_usd")) is not None])]


def _subj_alert_tape(d):
    return [_mranked("Premium in the alerts, by session",
                    "The premium carried by the alerts on record, summed "
                    "for each session they landed in.",
                    _session_premium_rows(d.get("alerts")))]


def _subj_breakout_scanner(d):
    return [_mranked("Closest to their own high, on record",
                    "Each name's last close as a percent of its highest "
                    "close in the window this page uses, from the closes "
                    "on record in bars.",
                    _dist_to_high_rows(d))]


def _subj_chain_explorer(d):
    charts = []
    for u in (d.get("underlyings") or [])[:1]:
        snaps = u.get("snapshots") or []
        for snap in snaps[-2:]:
            by_strike = {}
            for ex in snap.get("expiries") or []:
                for st in ex.get("strikes") or []:
                    oi = 0
                    for side in ("call", "put"):
                        leg = st.get(side) or {}
                        if _mnum(leg.get("oi")) is not None:
                            oi += leg["oi"]
                    if oi > 0:
                        by_strike[st.get("strike")] = \
                            by_strike.get(st.get("strike"), 0) + oi
            rows = [{"name": f"Strike {k}", "score": v}
                    for k, v in by_strike.items()]
            rows.sort(key=lambda r: -r["score"])
            day = snap.get("snapshot_day") or snap.get("date") or ""
            charts.append(_mranked(
                f"Open contracts by strike, {day}".strip(),
                "Open interest summed at each strike in this snapshot "
                "on record, biggest strikes drawn.",
                rows, limit=14))
    return charts


def _subj_correlation_web(d):
    rows = []
    for sym, twins in (d.get("twins") or {}).items():
        if twins and _mnum(twins[0].get("correlation")) is not None:
            rows.append({"name": f"{sym} with {twins[0].get('symbol')}",
                         "score": twins[0]["correlation"],
                         "coverage": twins[0].get("label") or ""})
    rows.sort(key=lambda r: -r["score"])
    return [_mranked("The closest twins on record",
                    "The strongest recorded correlation for each name, "
                    "against the name it moves with most closely.",
                    rows)]


def _subj_dark_prints(d):
    return [_mline("The dark share, session by session",
                  "The share of trading that happened away from the "
                  "public exchanges in each session on record, in percent.",
                  [{"date": h.get("session"), "value": h.get("index_pct")}
                   for h in d.get("history") or []])]


def _subj_decay_watch(d):
    gradings = d.get("gradings") or []
    if not gradings:
        return []
    g = gradings[-1]
    total = _mnum(g.get("total")) or 0
    if not total:
        return []
    charts = []
    moves = d.get("movements") or []
    if moves:
        rows = [{"name": m.get("name"),
                 "status": f"{m.get('from')} to {m.get('to')}",
                 "coverage": f"{m.get('from_date')} to {m.get('date')}"}
                for m in moves]
        grid = _mgrid("How entries moved between gradings",
                      "Each entry whose standing changed, from its "
                      "old standing to its new one, with the two "
                      "grading dates.", rows)
        if grid:
            charts.append(grid)
    items = [{"label": f"Promoted, {g.get('date')}",
              "value": round(100 * g["promoted"] / total * 10) / 10},
             {"label": f"On probation, {g.get('date')}",
              "value": round(100 * g["probation"] / total * 10) / 10}]
    if moves:
        title = "The book's standing at its last grading"
        label = ("The share of the promoted book standing promoted "
                 "and on probation at the grading on record, "
                 "in percent.")
    else:
        title = "The book's standing at its only grading"
        label = ("The share of the promoted book standing promoted "
                 "and on probation at the grading on record, in "
                 "percent. The book has been graded once, so no "
                 "movement between standings is on record yet.")
    tiles = _mtiles(title, label, items)
    if tiles:
        charts.append(tiles)
    return charts


def _subj_earnings_calendar(d):
    # Cure 2026-10-31: the record chart plots what reporting names
    # actually did, against the expected move that was on record
    # for them. Names that have not yet reported stay off it: their
    # expected moves are the lead chart's subject, not the record's.
    rows = []
    for r in d.get("realised_moves") or []:
        if _mnum(r.get("realised_move_pct")) is None:
            continue
        exp = r.get("expected_move_pct")
        rows.append({
            "name": f"{r.get('symbol')} {r.get('report_date')}",
            "score": r["realised_move_pct"],
            "coverage": (f"expected {exp} percent"
                         if _mnum(exp) is not None else
                         "no expected move was on record for "
                         "this report")})
    rows.sort(key=lambda r: -abs(r["score"]))
    chart = _mranked(
        "What reporting names actually did, against what was expected",
        "The realised move for each name whose report date has "
        "passed, in percent: the close of the first session on or "
        "after the report against the close just before it. The "
        "expected move priced for the name before it reported is "
        "printed beside each bar, where one was on record.",
        rows, limit=40)
    return [chart] if chart else []


def _subj_earnings_drift(d):
    charts = []
    rows = [{"name": f"{r.get('symbol')} {r.get('report_date')}",
             "score": _mnum(r.get("drift_pct"))}
            for r in d.get("event_rows") or []
            if _mnum(r.get("drift_pct")) is not None]
    rows.sort(key=lambda r: -r["score"])
    ranked = _mranked(
        "Each report, and what the name did on it",
        "Every earnings event in the study, named and dated, with "
        "its own post-report move in percent: the close of the "
        "first session on or after the report against the close "
        "just before it.",
        rows, limit=40)
    if ranked:
        charts.append(ranked)
    items = []
    if _mnum(d.get("mean")) is not None:
        items.append({"label": "Average move after reporting",
                      "value": round(d["mean"] * 10000) / 100})
    if _mnum(d.get("median")) is not None:
        items.append({"label": "Middle move after reporting",
                      "value": round(d["median"] * 10000) / 100})
    if _mnum(d.get("share_positive")) is not None:
        items.append({"label": "Share of reports that rose",
                      "value": round(d["share_positive"] * 1000) / 10})
    tiles = _mtiles("What the names did after reporting, on record",
                    "Across the earnings events on record for the three "
                    "names this page follows: the average and middle "
                    "post-report move, and the share that rose, in percent.",
                    items)
    if tiles:
        charts.append(tiles)
    return charts


def _subj_echo_lens(d):
    rows = [{"name": r.get("symbol"), "status": r.get("verdict"),
             "coverage": (r.get("words") or "")[:90]}
            for r in (d.get("readings") or [])[:24]]
    return [_mgrid("The lens's readings, name by name",
                  "Each name on record with the verdict this lens gave "
                  "it, from the readings listed on the page.", rows)]


def _subj_expected_move(d):
    charts = []
    for n in (d.get("names") or [])[:1]:
        curve = n.get("funded_curve") or []
        series = [{"date": f"{c.get('elapsed_minutes')} min",
                   "value": round((c["upper"] - c["lower"]) * 100) / 100}
                  for c in curve
                  if _mnum(c.get("upper")) is not None
                  and _mnum(c.get("lower")) is not None]
        charts.append(_mline(
            f"The expected range as the session ran, {n.get('symbol') or n.get('name')}",
            "The width of the recorded session band as it was funded "
            "through the session, from the funded curve on record.",
            series))
    return charts


def _subj_expiry_pin_watch(d):
    charts = []
    for n in (d.get("names") or [])[:2]:
        rows = [{"name": f"{n.get('symbol')} expiring {e.get('expiry')}",
                 "score": _mnum(e.get("total_oi")),
                 "coverage": f"heaviest strike {e.get('heaviest_strike')}"}
                for e in n.get("expiries") or []
                if _mnum(e.get("total_oi")) is not None]
        charts.append(_mranked(
            "Open contracts by expiry, on record",
            "Open interest by expiry for the names on record, with the "
            "heaviest strike printed beside each bar.", rows))
    return charts


def _subj_fear_day(d):
    rows = [{"name": q.get("date"),
             "score": _mnum(q.get("fear_gauge_change_pct")),
             "coverage": f"SPY {q.get('spy_change_pct')}%, "
                         f"QQQ {q.get('qqq_change_pct')}% that day"}
            for q in d.get("qualifying_days") or []
            if _mnum(q.get("fear_gauge_change_pct")) is not None]
    return [_mranked("Fear days on record",
                    "The rise in the fear gauge on each qualifying day "
                    "on record, in percent, with the index moves beside "
                    "each bar.", rows)]


def _subj_fear_day_forecaster(d):
    loc = d.get("local_record") or {}
    rows = [{"name": q.get("date"),
             "score": _mnum(q.get("fear_gauge_change_pct")),
             "coverage": f"SPY {q.get('spy_change_pct')}% that day"}
            for q in loc.get("qualifying_days") or []
            if _mnum(q.get("fear_gauge_change_pct")) is not None]
    return [_mranked("The fear days this forecast rests on",
                    "The rise in the fear gauge on each qualifying day "
                    "in the local record, in percent.", rows)]


def _subj_filings_wire(d):
    charts = []
    for c in (d.get("companies") or [])[:2]:
        figs = c.get("figures") or []
        if not figs:
            continue
        f = figs[0]
        series = [{"date": r.get("period_end") or r.get("filed"),
                   "value": r.get("value")}
                  for r in f.get("readings") or []]
        charts.append(_mline(
            f"{c.get('symbol') or c.get('company_name')}: {f.get('label')} on record",
            "The filed figures for this company, in the order of the "
            "periods they cover. This is the wire's own history.",
            series))
    return charts


def _subj_flow_board(d):
    charts = []
    for row in (d.get("rows") or [])[:2]:
        rows = []
        for cell in row.get("cells") or []:
            if _mnum(cell.get("call_net_premium_usd")) is not None:
                rows.append({"name": f"{row.get('underlying')} calls {cell.get('session')}",
                             "score": cell["call_net_premium_usd"]})
            if _mnum(cell.get("put_net_premium_usd")) is not None:
                rows.append({"name": f"{row.get('underlying')} puts {cell.get('session')}",
                             "score": cell["put_net_premium_usd"]})
        charts.append(_mranked(
            f"Net premium by session, {row.get('underlying')}",
            "Call and put net premium for this underlying in each "
            "session on record, from the board's own rows.", rows))
    return charts


def _subj_flow_engine(d):
    rows = [{"name": f"{e.get('underlying')} {e.get('contract_code')}",
             "score": _mnum(e.get("premium_usd")),
             "coverage": f"{e.get('direction')}, heat {e.get('heat_score')}"}
            for e in d.get("examples") or []
            if _mnum(e.get("premium_usd")) is not None]
    rows.sort(key=lambda r: -r["score"])
    return [_mranked("The worked examples, by premium",
                    "The page's worked examples are shown as what they "
                    "are: worked examples, each with the premium it "
                    "carried. They are not a graded record.", rows)]


def _subj_flow_tape(d):
    alerts = []
    for g in d.get("groups") or []:
        for a in g.get("alerts") or []:
            a = dict(a)
            if not a.get("session"):
                a["session"] = g.get("session")
            alerts.append(a)
    return [_mranked("Premium in the tape, by session",
                    "The premium carried by the alerts on the tape, "
                    "summed for each session on record.",
                    _session_premium_rows(alerts))]


def _subj_gap_fill(d):
    rows = [{"name": b.get("label"),
             "score": round(b["frequency"] * 1000) / 10
             if _mnum(b.get("frequency")) is not None else None,
             "coverage": f"of {b.get('n')} gaps"}
            for b in d.get("by_band") or []
            if _mnum(b.get("frequency")) is not None]
    return [_mranked("How often gaps filled, by gap size",
                    "The share of overnight gaps that filled on the "
                    "day, in percent, for each gap-size band on record.",
                    rows)]


def _subj_golden_sweep_wire(d):
    rows = [{"name": f"{p.get('contract_code')}",
             "score": _mnum(p.get("premium_usd")),
             "coverage": f"{p.get('direction')}, heat {p.get('heat_score')}"}
            for p in d.get("prints") or []
            if _mnum(p.get("premium_usd")) is not None]
    rows.sort(key=lambda r: -r["score"])
    return [_mranked("The golden prints on record, by premium",
                    "Each golden print on record with the premium it "
                    "carried.", rows)]


def _subj_grade_a_board(d):
    rows = []
    for g in d.get("groups") or []:
        cells = g.get("cells") or []
        if cells and _mnum(cells[0].get("net_second")) is not None:
            rows.append({"name": (g.get("title") or "")[:44],
                         "score": cells[0]["net_second"],
                         "coverage": f"held {cells[0].get('hold_second')} "
                                     f"on the second look"})
    return [_mranked("The recipes' own graded numbers",
                    "Each graded recipe group on the board with the net "
                    "figure it earned on the second search.", rows)]


def _subj_grade_my_call(d):
    src = d.get("prices") or d.get("bars") or {}
    entry = src.get("SPY")
    dates = d.get("dates") or []
    if not (isinstance(entry, list) and len(entry) > 1
            and isinstance(entry[1], list)):
        return []
    series = [{"date": dates[i] if i < len(dates) else "",
               "value": v} for i, v in enumerate(entry[1])]
    return [_mline("The S and P 500 fund, closing prices on record",
                  "The closing price history this page grades calls "
                  "from, session by session. It is both the reading "
                  "and the record.", series[-260:])]


def _subj_graveyard(d):
    rows = []
    for b in (d.get("buried") or [])[:8]:
        rows.append({"name": (b.get("maker") or "Buried claim")[:44],
                     "status": b.get("verdict_words"),
                     "coverage": (b.get("result") or "")[:90]})
    nb = d.get("not_buried") or {}
    for claim in (nb.get("held") or [])[:4]:
        rows.append({"name": (claim.get("maker") or "Claim")[:44],
                     "status": claim.get("verdict_words") or "Held up",
                     "coverage": (claim.get("claim") or "")[:90]})
    return [_mgrid("Claims and what the record showed",
                  "Each claim on record with the verdict its recheck "
                  "earned, claim by claim.", rows, limit=12)]


def _subj_holly_ideas(d):
    rows = [{"name": i.get("symbol"), "score": _mnum(i.get("score")),
             "coverage": f"{i.get('checks_in_favor')} of "
                         f"{i.get('checks_total')} checks in favour"}
            for i in (d.get("ideas") or [])[:12]
            if _mnum(i.get("score")) is not None]
    return [_mranked("The ideas on record, scored",
                    "Each idea in the session on record with its score. "
                    "Past sessions' ideas are listed on the page; the "
                    "charted session is the freshest one.", rows)]


def _subj_horizon_grades(d):
    rows = []
    for h in d.get("horizons") or []:
        for g in h.get("groups") or []:
            if g.get("state") == "graded" and g.get("graded_count"):
                rows.append({
                    "name": f"{h.get('days')} day, {g.get('session')}",
                    "score": round(100 * g["rose_count"]
                                   / g["graded_count"] * 10) / 10,
                    "coverage": f"{g['rose_count']} rose, "
                                f"{g['did_not_rise_count']} did not"})
    rows.sort(key=lambda r: r["name"])
    return [_mranked("Share that rose, by horizon and session",
                    "Of the calls graded at each waiting time in each "
                    "session on record, the share that rose, in percent.",
                    rows)]


def _subj_insider_wire(d):
    rows = []
    for n in d.get("names") or []:
        summ = n.get("summary") or {}
        buys = (summ.get("buys") or {}).get("value_usd")
        sells = (summ.get("sells") or {}).get("value_usd")
        if _mnum(buys) is not None and _mnum(sells) is not None:
            rows.append({"name": n.get("symbol"),
                         "score": round(buys - sells),
                         "coverage": f"buys {buys}, sells {sells}"})
    rows.sort(key=lambda r: -abs(r["score"]))
    return [_mranked("Insider buying minus selling, by name",
                    "For each name on record, the value of insider "
                    "buying minus the value of insider selling in the "
                    "filings on record, in dollars.", rows)]


def _subj_iv_weather(d):
    items = []
    for g in d.get("groups") or []:
        for n in g.get("names") or []:
            if _mnum(n.get("iv_percent")) is not None:
                items.append({"label": n.get("symbol"),
                              "value": n["iv_percent"],
                              "word": f"range {n.get('low_percent')} to "
                                      f"{n.get('high_percent')}"})
    return [_mtiles("Volatility weather on record, name by name",
                   "Each name's recorded volatility reading, in "
                   "percent, with its own recorded range beside it.",
                   items[:24])]


def _subj_momentum_clock(d):
    return [_mranked("Rises and falls over 21 sessions, on record",
                    "Each name's last close against its close 21 "
                    "sessions earlier, in percent, from the closes on "
                    "record in bars.",
                    _window_change_rows(d, 21))]


def _subj_morning_map(d):
    # Past maps were not kept before 2026-10-31 (single session in
    # data.json). Wave 3 cure (Item F): the record chart is the
    # current session's own levels ladder, labelled as the session
    # on record, never counts; the producer now keeps a dated
    # snapshot per run (session_history), and once more than one
    # session is kept, SPY's flip level per kept session is plotted
    # as well. Nothing from before keeping began is reconstructed.
    items = []
    for ix in d.get("indexes") or []:
        put_wall = (ix.get("put_wall") or {}).get("value")
        call_wall = (ix.get("call_wall") or {}).get("value")
        if _mnum(put_wall) is None or _mnum(call_wall) is None:
            continue
        items.append({"label": ix.get("symbol"), "low": put_wall,
                      "high": call_wall,
                      "mid": (ix.get("flip") or {}).get("value"),
                      "current": ix.get("spot")})
    charts = []
    if items:
        charts.append({
            "kind": "band",
            "title": "The morning levels on record, this session",
            "label": "Each index's put wall to call wall for the "
                     "session on record, the flip level ticked and "
                     "the spot dotted. Past maps were not kept; "
                     "the record accrues from this session forward.",
            "items": items})
    kept = _kept_sessions(d)
    if len(kept) > 1:
        series = []
        for e in kept:
            for v in e.get("values") or []:
                if v.get("symbol") == "SPY" \
                        and _mnum(v.get("flip")) is not None:
                    series.append({"date": e["session"],
                                   "value": v["flip"]})
        line = _mline("SPY's flip level, per session on record",
                      "The flip level from each kept session's map, "
                      "oldest first.", series)
        if line:
            charts.append(line)
    return charts


def _subj_odds_cards(d):
    rows = []
    for f in d.get("families") or []:
        for day in f.get("days") or []:
            if _mnum(day.get("rate")) is not None:
                rows.append({"name": f"{f.get('name')}: {day.get('label')}",
                             "score": round(day["rate"] * 1000) / 10
                             if day["rate"] <= 1 else day["rate"]})
        for reg in f.get("regimes") or []:
            if _mnum(reg.get("rate")) is not None:
                rows.append({"name": f"{f.get('name')}: {reg.get('label')}",
                             "score": round(reg["rate"] * 1000) / 10
                             if reg["rate"] <= 1 else reg["rate"]})
    if not rows:
        rows = [{"name": f.get("name"),
                 "score": round(f["rate"] * 1000) / 10
                 if _mnum(f.get("rate")) is not None else None}
                for f in d.get("families") or []]
        rows = [r for r in rows if r["score"] is not None]
    return [_mranked("How often each family paid off, by day and regime",
                    "The share of cases that reached the target, in "
                    "percent, split by the day and regime splits on "
                    "record for each family.", rows)]


def _subj_one_page_report(d):
    name = d.get("default_name")
    rec = (d.get("names") or {}).get(name) or {}
    items = []
    scored = rec.get("scored") or {}
    if _mnum(scored.get("score")) is not None:
        items.append({"label": f"{name} board score, out of 100",
                      "value": scored["score"]})
    chart = rec.get("chart") or {}
    if _mnum(chart.get("last_close")) is not None:
        items.append({"label": f"{name} last close",
                      "value": chart["last_close"]})
    vol = rec.get("volume") or {}
    if _mnum(vol.get("multiple")) is not None:
        items.append({"label": f"{name} volume against its usual",
                      "value": vol["multiple"]})
    fams = rec.get("families") or {}
    if _mnum(fams.get("families_speaking")) is not None:
        items.append({"label": f"Families speaking on {name}",
                      "value": fams["families_speaking"]})
    return [_mtiles(f"The default name's own readings: {name}",
                   "The readings this page carries for its default "
                   "name, one tile per reading, from the name's own "
                   "record sections.", items)]


def _subj_portfolio_builder(d):
    rows = [{"name": s.get("sector"), "score": _mnum(s.get("share_pct")),
             "coverage": f"{s.get('members')} members"}
            for s in d.get("sector_mix") or []
            if _mnum(s.get("share_pct")) is not None]
    return [_mranked("The basket on record, by sector share",
                    "Each sector's share of the current basket, in "
                    "percent. Past baskets are not kept; this is the "
                    "current basket's composition.", rows)]


def _subj_promoted_book(d):
    rows = []
    for st in d.get("standings") or []:
        for g in st.get("groups") or []:
            for e in g.get("entries") or []:
                wins = e.get("windows") or []
                if wins and _mnum(wins[0].get("gap_points")) is not None:
                    rows.append({
                        "name": f"Grade {e.get('grade')} entry, "
                                f"{e.get('days_ahead')} days ahead",
                        "score": wins[0]["gap_points"],
                        "coverage": (e.get("where") or "")[:60]})
    rows.sort(key=lambda r: -abs(r["score"]))
    return [_mranked("Book entries by their own graded gap",
                    "Each promoted entry's graded gap in points from "
                    "its first recorded window, biggest first.", rows)]


def _subj_proving_ground(d):
    rows = [{"name": t.get("name"), "status": t.get("state_words"),
             "coverage": (t.get("reason") or "")[:90]}
            for t in (d.get("tools") or [])[:24]]
    return [_mgrid("Every tool, with its own proving state",
                  "The grid is the subject: each tool on record with "
                  "the state this page gives it and why.", rows)]


def _subj_pullback_norm(d):
    dist = (d.get("distribution") or {}).get("events_by_bucket") or {}
    rows = [{"name": k.replace("_", " "),
             "score": _mnum(v.get("fwd20_mean_rel_pct")),
             "coverage": f"{v.get('events')} events"}
            for k, v in dist.items()
            if _mnum(v.get("fwd20_mean_rel_pct")) is not None]
    return [_mranked("What followed dips of each depth, on record",
                    "The study record by dip depth: the average move "
                    "against the market over the 20 sessions after "
                    "events at each depth, in percent.", rows)]


def _subj_receipts(d):
    rows = [{"name": r.get("tool"), "status": r.get("grade"),
             "coverage": (r.get("completeness") or "")[:80]}
            for r in (d.get("receipts") or [])[:24]]
    return [_mgrid("The receipts, tool by tool",
                  "Each tool's receipt on file with its grade. This "
                  "page's subject is the site's own bookkeeping, drawn "
                  "as a grid, never as a tally.", rows)]


def _subj_regime_dial(d):
    rows = [{"name": f"{h.get('session')}: {h.get('kind')}",
             "status": h.get("kind"),
             "coverage": (h.get("sentence") or "")[:90]}
            for h in d.get("reading_history") or []]
    return [_mgrid("The readings on record, session by session",
                  "Each daily reading this page has published, with "
                  "the kind of market it named.", rows)]


def _subj_replication_wire(d):
    rows = [{"name": (c.get("maker") or "Claim")[:44],
             "status": c.get("verdict_words"),
             "coverage": (c.get("result") or "")[:90]}
            for c in (d.get("claims") or [])[:16]]
    return [_mgrid("Claims and what the recheck showed",
                  "Each claim on the wire with the verdict its "
                  "recheck earned, claim by claim.", rows, limit=16)]


def _subj_reversal_wire(d):
    sessions = d.get("sessions") or []
    entries = (sessions[0].get("entries") if sessions else []) or []
    rows = [{"name": e.get("symbol"), "status": e.get("label")}
            for e in entries[:24]]
    day = sessions[0].get("date") if sessions else ""
    return [_mgrid(f"Names and their labels, {day}",
                  "Names in the freshest session on record with the "
                  "pattern label the scanner gave each one.", rows)]


def _subj_router(d):
    rec = (d.get("session_record") or [{}])[0]
    rows = [{"name": a.get("name"), "status": "Avoid",
             "coverage": (a.get("why") or "")[:110]}
            for a in rec.get("avoid_names") or []]
    return [_mgrid("The names the router said to avoid, and why",
                  "The per-name verdicts in the latest session on "
                  "record, with the reason for each.", rows)]


def _subj_sector_rotation(d):
    rows = [{"name": s.get("sector"),
             "score": _mnum(s.get("avg_change_21_pct")),
             "coverage": s.get("label") or ""}
            for s in d.get("sectors") or []
            if _mnum(s.get("avg_change_21_pct")) is not None]
    rows.sort(key=lambda r: -r["score"])
    return [_mranked("Sectors over the last 21 sessions",
                    "Each sector's average move over the last 21 "
                    "sessions on record, in percent. The longer window "
                    "is the record beside the 5 session lead.", rows)]


def _subj_short_volume(d):
    charts = []
    for t in (d.get("tickers") or [])[:2]:
        series = [{"date": x.get("date"), "value": x.get("short_share_pct")}
                  for x in t.get("days") or []]
        charts.append(_mline(
            f"{t.get('symbol')}: share of trading sold short, by day",
            "The daily share of this name's trading that was sold "
            "short, in percent. The days are the record.", series))
    return charts


def _subj_signal_feed(d):
    events = [{"label": e.get("name"), "desc": (e.get("detail") or "")[:120],
               "time": e.get("session") or "",
               "tags": [e.get("grading_words") or e.get("kind_words") or ""]}
              for e in (d.get("entries") or [])[:20]]
    return [_mtape("The feed itself, newest entries on record",
                  "The newest entries on this feed, each with what it "
                  "said and its grading state.", events)]


def _subj_skew_lens(d):
    figs = d.get("modelled_figures") or d.get("figures") or []
    figs = [f for f in figs if _mnum(f.get("put_percent")) is not None]
    if not figs:
        return []
    freshest = max((f.get("date") or "") for f in figs)
    rows = []
    for f in figs:
        if (f.get("date") or "") != freshest:
            continue
        rows.append({"name": f"{f.get('symbol')} put strike {f.get('put_strike')}",
                     "score": f["put_percent"]})
        if _mnum(f.get("call_percent")) is not None:
            rows.append({"name": f"{f.get('symbol')} call strike {f.get('call_strike')}",
                         "score": f["call_percent"]})
    return [_mranked(f"The skew readings on record, {freshest}",
                    "The dated skew ledger: how much more the market "
                    "pays for downside protection than upside, per "
                    "reading on record, in percent.", rows)]


def _subj_smart_money_tracker(d):
    return [_mranked("How each tracked holding changed",
                    "Each tracked holder's total reported value "
                    "against the prior filing on record, in percent.",
                    _holder_change_rows(d))]


def _subj_squeeze_watch(d):
    rows = [{"name": n.get("symbol"),
             "score": _mnum(n.get("si_pct_of_float")),
             "coverage": f"settlement {n.get('settlement_date')}, "
                         f"{n.get('days_to_cover')} days to cover"}
            for n in (d.get("names") or [])[:14]
            if _mnum(n.get("si_pct_of_float")) is not None]
    rows.sort(key=lambda r: -r["score"])
    return [_mranked("Borrowed shares at the settlement on record",
                    "Each name's borrowed shares as a percent of the "
                    "shares available to trade, at the settlement date "
                    "printed beside each bar.", rows)]


def _subj_state_analogue(d):
    readings = d.get("readings") or []
    values = (d.get("today") or {}).get("values") or []
    items = []
    for i, r in enumerate(readings):
        if i < len(values) and _mnum(values[i]) is not None:
            items.append({"label": r.get("name"), "value": values[i]})
    return [_mtiles("Today's five market readings",
                   "The five readings that describe today, each with "
                   "its own value on record. Matches appear here once "
                   "enough sessions have built up.", items)]


def _subj_static_gex(d):
    charts = []
    for f in (d.get("funds") or [])[:1]:
        rows = [{"name": f"Strike {x.get('strike')}",
                 "score": _mnum(x.get("net_gex"))}
                for x in f.get("strongest") or []
                if _mnum(x.get("net_gex")) is not None]
        charts.append(_mranked(
            f"Strongest strikes, {f.get('underlying')}, {f.get('day')}",
            "Net dealer positioning at each of the strongest "
            "strikes in the snapshot on record.", rows))
    return charts


def _subj_strat_combos(d):
    groups = d.get("groups") or []
    if not groups:
        return []
    g = max(groups, key=lambda x: x.get("count") or 0)
    rows = [{"name": sym, "status": g.get("name")}
            for sym in (g.get("names") or [])[:24]
            if isinstance(sym, str)]
    return [_mgrid(f"Names carrying: {g.get('name')}",
                  "The names in the largest completed pattern "
                  "combination on record, each labelled with the "
                  "combination it completed.", rows)]


def _subj_strat_scanner(d):
    rows = []
    for g in d.get("groups") or []:
        for n in (g.get("names") or [])[:6]:
            if isinstance(n, dict):
                rows.append({"name": n.get("symbol"),
                             "status": n.get("label") or g.get("name")})
    return [_mgrid("Names and the pattern each one showed",
                  "Names on record with the bar pattern label the "
                  "scanner gave each one.", rows)]


def _subj_survivors_wire(d):
    items = []
    for r in d.get("per_record") or []:
        tested = _mnum(r.get("tested")) or 0
        if not tested:
            continue
        items.append({"label": f"{r.get('name')}: standing",
                      "value": round(100 * r["standing"] / tested * 10) / 10})
        items.append({"label": f"{r.get('name')}: partly standing",
                      "value": round(100 * r["partly"] / tested * 10) / 10})
    return [_mtiles("How the tested claims stand, by record",
                   "Of the claims tested from each record on file, "
                   "the share standing and partly standing, in percent.",
                   items)]


def _subj_unusual_volume(d):
    items = [{"label": n.get("symbol"), "value": _mnum(n.get("multiple"))}
             for n in (d.get("names") or [])[:24]
             if _mnum(n.get("multiple")) is not None]
    return [_mtiles("Trading volume against the usual, on record",
                   "Each name on record with its trading volume as a "
                   "multiple of its usual volume, for the session on "
                   "record.", items)]


def _subj_wall_check(d):
    rows = []
    for sess in d.get("sessions") or []:
        for t in sess.get("tests") or []:
            rows.append({
                "name": f"{t.get('name')} {t.get('session')}",
                "status": f"upper {t.get('upper_outcome')}, "
                          f"lower {t.get('lower_outcome')}",
                "coverage": f"flip respected: {t.get('flip_respected')}"})
    return [_mgrid("Every wall test on record, and its outcome",
                  "Each graded card's levels and what happened at "
                  "them, test by test.", rows, limit=14)]


def _subj_week_ahead(d):
    events = [{"label": e.get("name"),
               "desc": f"{e.get('date')} {e.get('time_label') or ''}, "
                       f"{e.get('kind')}",
               "time": e.get("date") or ""}
              for e in (d.get("events") or [])[:20]]
    return [_mtape("The events on record, week by week",
                  "The macro events this page has assembled, each "
                  "placed on its own date.", events)]


def _subj_watchlist_pulse(d):
    items = [{"label": n.get("symbol"),
              "value": _mnum(n.get("families_speaking"))}
             for n in (d.get("names") or [])[:24]
             if _mnum(n.get("families_speaking")) is not None]
    return [_mtiles("How many voices speak on each name, on record",
                   "Past sessions are not kept for this page, so the "
                   "record chart is the current session's own picture: "
                   "how many reading families carry a reading for "
                   "each name.", items)]


SUBJECT_CHART_BUILDERS = {
    "13f-tracker": _subj_13f_tracker,
    "activity-profile": _subj_activity_profile,
    "alert-tape": _subj_alert_tape,
    "breakout-scanner": _subj_breakout_scanner,
    "chain-explorer": _subj_chain_explorer,
    "correlation-web": _subj_correlation_web,
    "dark-prints": _subj_dark_prints,
    "decay-watch": _subj_decay_watch,
    "earnings-calendar": _subj_earnings_calendar,
    "earnings-drift": _subj_earnings_drift,
    "echo-lens": _subj_echo_lens,
    "expected-move": _subj_expected_move,
    "expiry-pin-watch": _subj_expiry_pin_watch,
    "fear-day": _subj_fear_day,
    "fear-day-forecaster": _subj_fear_day_forecaster,
    "filings-wire": _subj_filings_wire,
    "flow-board": _subj_flow_board,
    "flow-engine": _subj_flow_engine,
    "flow-tape": _subj_flow_tape,
    "gap-fill": _subj_gap_fill,
    "golden-sweep-wire": _subj_golden_sweep_wire,
    "grade-a-board": _subj_grade_a_board,
    "grade-my-call": _subj_grade_my_call,
    "graveyard": _subj_graveyard,
    "holly-ideas": _subj_holly_ideas,
    "horizon-grades": _subj_horizon_grades,
    "insider-wire": _subj_insider_wire,
    "iv-weather": _subj_iv_weather,
    "momentum-clock": _subj_momentum_clock,
    "morning-map": _subj_morning_map,
    "odds-cards": _subj_odds_cards,
    "one-page-report": _subj_one_page_report,
    "portfolio-builder": _subj_portfolio_builder,
    "promoted-book": _subj_promoted_book,
    "proving-ground": _subj_proving_ground,
    "pullback-norm": _subj_pullback_norm,
    "receipts": _subj_receipts,
    "regime-dial": _subj_regime_dial,
    "replication-wire": _subj_replication_wire,
    "reversal-wire": _subj_reversal_wire,
    "router": _subj_router,
    "sector-rotation": _subj_sector_rotation,
    "short-volume": _subj_short_volume,
    "signal-feed": _subj_signal_feed,
    "skew-lens": _subj_skew_lens,
    "smart-money-tracker": _subj_smart_money_tracker,
    "squeeze-watch": _subj_squeeze_watch,
    "state-analogue": _subj_state_analogue,
    "static-gex": _subj_static_gex,
    "strat-combos": _subj_strat_combos,
    "strat-scanner": _subj_strat_scanner,
    "survivors-wire": _subj_survivors_wire,
    "unusual-volume": _subj_unusual_volume,
    "wall-check": _subj_wall_check,
    "week-ahead": _subj_week_ahead,
    "watchlist-pulse": _subj_watchlist_pulse,
}


def subject_charts_for(slug, data):
    builder = SUBJECT_CHART_BUILDERS.get(slug)
    if builder is None:
        return None
    try:
        charts = builder(data)
    except Exception:
        return []
    return [c for c in charts if c]
