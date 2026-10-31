#!/usr/bin/env python3
"""Refresh The Record data file.

Reads the real published grading summary and the permanent log of
published calls, and writes site/record/data.json in the shape The
Record page renders.

What the sources carry (and what this script therefore shows):
- Every Board call ever logged, paired with the trading day it was
  published for, identical republications counted once.
- Every Morning Map card of record (the last card per index per day).
- Grades exactly as the published grading summary records them at
  cohort level (1, 5 and 21 trading days). The summary carries no
  per-day breakdown, so per-group grades are computed here from the
  permanent log and the shipped price panel (each call's return to
  the horizon session), and are published only while they reconcile
  exactly with the summary's cohort totals: groups attach in session
  order until the summary's matured count is reached, the rose sum
  must equal the summary's, and any disagreement fails closed. A
  group the summary has not reached yet stays "not yet graded".
- Horizons with no matured grades stay "not yet graded" with the
  date grading arrives. Nothing is recomputed and nothing is dropped:
  losing calls stay on the page.

Honesty rules:
- All timestamps and figures come from the source files, never from
  the clock, so running this script twice produces the same file.
- If the log and the grading summary disagree on the counts, the
  script fails instead of publishing a mismatched page.

Usage: python3 refresh_record.py
"""

import json
import os
import sys
from datetime import date, timedelta

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
SUMMARY_PATH = os.path.join(SOURCE_DIR, "scorecard.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
OUT_PATH = os.path.join(HERE, "record", "data.json")

HORIZONS = (1, 5, 21)


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def nth_weekday_after(day_iso, n):
    """Date of the nth trading day (Mon-Fri) strictly after day_iso.

    This is the same counting the grading summary itself declares:
    grades land at fixed session horizons counted in trading days.
    """
    d = date.fromisoformat(day_iso)
    left = n
    while left > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d.isoformat()


def board_groups(rows):
    """Pair Board calls with their publishing day; count copies once."""
    summaries = sorted(
        (r for r in rows if r.get("component") == "board-summary"),
        key=lambda r: r["ts_utc"])
    paired = []
    for r in rows:
        if r.get("component") != "board-row":
            continue
        as_of = None
        for s in summaries:
            if s["ts_utc"] <= r["ts_utc"]:
                as_of = s["value"]["as_of_session"]
            else:
                break
        if as_of:
            paired.append((r, as_of))
    seen, deduped = set(), []
    for r, as_of in paired:
        key = (as_of, r.get("inputs_hash"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append((r, as_of))
    groups = {}
    for r, as_of in deduped:
        v = r["value"]
        groups.setdefault(as_of, []).append({
            "symbol": v.get("symbol") or r.get("name"),
            "sector": v.get("sector"),
            "close": v.get("close"),
            "score": v.get("score"),
            "passed_every_check": bool(v.get("qualified")),
            "logged_at_utc": r["ts_utc"],
        })
    return [{"session": s, "calls": groups[s]} for s in sorted(groups)]


def map_groups(rows):
    """Cards of record: the last Map card per index per day."""
    of_record = {}
    for r in rows:
        if r.get("component") == "gex_static_v1":
            of_record[(r["underlying"], r["ts_utc"][:10])] = r
    groups = {}
    for (symbol, _day), r in sorted(of_record.items(),
                                    key=lambda kv: kv[1]["ts_utc"]):
        # Grading session by the declared rule: a card written before
        # the 8pm UTC close is graded on its own day's session; one
        # written after, on the next trading day.
        ts = r["ts_utc"]
        card_day = ts[:10]
        if int(ts[11:13]) < 20:
            grading_session = card_day
        else:
            grading_session = nth_weekday_after(card_day, 1)
        groups.setdefault(ts[:10], []).append({
            "index": symbol,
            "published_at_utc": ts,
            "grading_session": grading_session,
            "price_then": r.get("spot"),
            "call_wall": r.get("call_wall"),
            "put_wall": r.get("put_wall"),
            "flip_level": (None if r.get("zero_gamma") is None
                           else round(r["zero_gamma"], 2)),
        })
    return [{"session": s, "cards": groups[s]} for s in sorted(groups)]


def abstention_audit_block():
    """Abstention coverage audit for the forecast engines, computed
    from the forecast ledger through grading.abstention_coverage_audit
    (the audit role in forecast/grading.py). Read-only over the
    ledger: refused outcomes are resolved from the same price source
    the grading runner uses and never enter any engine's grade.
    If the forecast record cannot be read, the block says so with
    the reason instead of the panel going silently missing."""
    try:
        sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))
        from forecast import grading as grading_mod
        from forecast import ledger as ledger_mod
        from forecast import registry as registry_mod
        led = ledger_mod.Ledger(os.path.expanduser(
            "~/workspace/terminal-lineup/forecast/ledger.jsonl"))
        audit = grading_mod.abstention_coverage_audit(
            led.rows(), grading_mod.PriceSource())
        names = {eid: e["name"]
                 for eid, e in registry_mod.load().engines.items()}
        engines = []
        for engine_id, eng in sorted(audit["engines"].items()):
            engines.append({"engine_id": engine_id,
                            "name": names.get(engine_id, engine_id),
                            **eng})
        return {"state": "computed", "engines": engines,
                "totals": audit["totals"],
                "thin_cell_min": grading_mod.AUDIT_THIN_CELL_MIN}
    except Exception as exc:  # named, never silent
        return {"state": "unavailable",
                "reason": f"{type(exc).__name__}: {exc}"}


def horizon_block(summary_h, graded_n):
    """One horizon of the published grading summary, in public words."""
    if summary_h.get("state") == "graded":
        n = summary_h["n_mature"]
        up = round(summary_h["hit_rate"] * n)
        return {
            "state": "graded",
            "graded_count": n,
            "rose_count": up,
            "did_not_rise_count": n - up,
            "average_pct": round(summary_h["mean"] * 100, 2),
            "middle_pct": round(summary_h["median"] * 100, 2),
        }
    # "not yet graded — first grades land after the YYYY-MM-DD close"
    line = summary_h.get("line") or ""
    first_date = None
    for token in line.replace("—", " ").split():
        if len(token) == 10 and token[4] == "-" and token[7] == "-":
            first_date = token
    return {"state": "not_yet_graded", "first_grade_date": first_date}


def build():
    for path in (SUMMARY_PATH, LOG_PATH):
        if not os.path.exists(path):
            print(f"The Record refresh: source not found: {path}",
                  file=sys.stderr)
            return 1

    summary = load_json(SUMMARY_PATH)
    rows = load_log(LOG_PATH)
    counters = summary.get("counters", {})

    groups = board_groups(rows)
    n_board = sum(len(g["calls"]) for g in groups)
    if n_board != counters.get("board_rows_logged"):
        print(f"The Record refresh: log holds {n_board} Board calls but "
              f"the grading summary says {counters.get('board_rows_logged')}; "
              "refusing to publish a mismatched page.", file=sys.stderr)
        return 1

    cards = map_groups(rows)
    n_map = sum(len(g["cards"]) for g in cards)
    if n_map != counters.get("map_cards_of_record"):
        print(f"The Record refresh: log holds {n_map} Map cards but the "
              f"grading summary says {counters.get('map_cards_of_record')}; "
              "refusing to publish a mismatched page.", file=sys.stderr)
        return 1

    published = summary["board"]["published"]
    qualified = summary["board"]["qualified"]

    # Per-group grades (cure G17, 2026-10-29): the old attach put the
    # cohort block on the first group only when its matured count fit
    # inside that group, so once a second day matured no group carried
    # grades at all while the totals still published them, and every
    # consumer that recounts groups against totals (Streak Trap's
    # extract_record) failed closed forever. Compute each group's
    # grades from the log plus the price panel and reconcile against
    # the summary's cohort totals, in session order.
    panel_path = os.path.expanduser(
        "~/workspace/morgue/data_cache/board_bt_bars.json")
    panel = load_json(panel_path) if os.path.exists(panel_path) else {}
    calendar = [r[0] for r in panel.get("SPY", [])]
    closes = {}
    for g in groups:
        for c in g["calls"]:
            sym = c["symbol"]
            if sym not in closes:
                closes[sym] = {r[0]: float(r[4])
                               for r in panel.get(sym, [])}

    def group_returns(g, h):
        if g["session"] not in calendar:
            return []
        i = calendar.index(g["session"]) + h
        if i >= len(calendar):
            return []
        target = calendar[i]
        out = []
        for c in g["calls"]:
            series = closes.get(c["symbol"], {})
            base, final = series.get(g["session"]), series.get(target)
            if base and final:
                out.append(final / base - 1.0)
        return out

    for g in groups:
        g["grades"] = {}
    for h in HORIZONS:
        key = f"{h}d"
        block = published["horizons"][key]
        if block.get("state") != "graded":
            for g in groups:
                g["grades"][key] = {
                    "state": "not_yet_graded",
                    "first_grade_date": nth_weekday_after(g["session"], h)}
            continue
        budget = int(block["n_mature"])
        rose_budget = round(block["hit_rate"] * budget)
        used = rose_used = 0
        for g in groups:
            rets = group_returns(g, h)
            if rets and used + len(rets) <= budget:
                import statistics as _st
                rose = sum(1 for r in rets if r > 0)
                g["grades"][key] = {
                    "state": "graded",
                    "graded_count": len(rets),
                    "rose_count": rose,
                    "did_not_rise_count": len(rets) - rose,
                    "average_pct": round(sum(rets) / len(rets) * 100, 2),
                    "middle_pct": round(_st.median(rets) * 100, 2),
                    "graded_of_group": len(g["calls"])}
                used += len(rets)
                rose_used += rose
            else:
                g["grades"][key] = {
                    "state": "not_yet_graded",
                    "first_grade_date": nth_weekday_after(g["session"], h)}
        if used != budget or rose_used != rose_budget:
            print(f"The Record refresh: per-group {key} grades "
                  f"({used} graded, {rose_used} rose) do not reconcile "
                  f"with the summary cohort ({budget} graded, "
                  f"{rose_budget} rose); refusing to publish.",
                  file=sys.stderr)
            return 1

    qualified_block = {
        "calls": qualified["n_logged"],
        "horizons": {f"{h}d": horizon_block(qualified["horizons"][f"{h}d"],
                                            qualified["horizons"][f"{h}d"]
                                            .get("n_mature", 0))
                     for h in HORIZONS},
    }

    map_summary = summary.get("map", {})
    graded_so_far = counters.get("units_graded")
    board_1d = published["horizons"]["1d"]
    outcomes = None
    if board_1d.get("state") == "graded":
        n = board_1d["n_mature"]
        up = round(board_1d["hit_rate"] * n)
        outcomes = {"graded_count": n, "rose_count": up,
                    "did_not_rise_count": n - up, "horizon_days": 1}

    data = {
        "tool": "The Record",
        "generated_at_utc": summary.get("generated_at"),
        "source": "Every call the Morning Map and the Board published, "
                  "kept in a permanent log that is only ever added to, "
                  "and graded against what prices actually did next",
        "totals": {
            "calls_published": n_board + n_map,
            "board_calls": n_board,
            "map_calls": n_map,
            "calls_graded_so_far": graded_so_far,
            "outcomes_so_far": outcomes,
        },
        "board": {
            "name": "The Board",
            "cohort": {f"{h}d": horizon_block(published["horizons"][f"{h}d"],
                                              published["horizons"][f"{h}d"]
                                              .get("n_mature", 0))
                       for h in HORIZONS},
            "what_it_publishes": "A daily list of stock calls. Each call "
                                 "shows the closing price and a combined "
                                 "checklist score on the day it was "
                                 "published; calls marked as passing every "
                                 "check are its strongest calls.",
            "groups": groups,
            "strongest": qualified_block,
        },
        "abstention_audit": abstention_audit_block(),
        "map": {
            "name": "The Morning Map",
            "what_it_publishes": "A daily card for each index with the "
                                 "price at the time, the call wall above, "
                                 "the put wall below, and the flip level.",
            "state": map_summary.get("state"),
            "cards_graded": map_summary.get("cards_graded"),
            # The scorecard carries no pending count; waiting is the
            # cards of record not yet graded (cure G17, 2026-10-29:
            # publishing None here crashed Horizon Grades' totals
            # check with int + NoneType).
            "cards_waiting": (map_summary.get("cards_pending")
                              if map_summary.get("cards_pending")
                              is not None else
                              n_map - (map_summary.get("cards_graded")
                                       or 0)),
            "groups": cards,
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({n_board} Board calls, {n_map} Map cards, "
          f"summary generated {summary.get('generated_at')})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
