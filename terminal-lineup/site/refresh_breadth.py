#!/usr/bin/env python3
"""Refresh the Breadth Meter data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no disclaimer-style copy on any reader surface of any tool, in pages or generated data, ever.

Evidence class: the real daily price history behind the daily
scoring run (daily closing prices for every scored stock, 399
trading sessions from March 25, 2025 to October 23, 2026),
cross-checked against the scored run's own published counts for
its session (the board card's summary and the full scored list:
1,838 stocks checked, 1,833 scored, 5 with too little data to
score). The breadth figures themselves are counted directly from
the closing prices in that history, deterministically: the same
history always produces the same file.

Reconstruction choices: each average is the plain average of a
stock's closing prices over the last 50 (or 200) trading sessions
including the session itself. A stock is counted for a session
only if it traded that session, and counted for an average only
if it has at least that many sessions of history behind it, so
each figure's own denominator is printed beside it. A stock
advances when its close is higher than its own previous traded
close and declines when it is lower; an unchanged close is
counted separately. Percentages are shares of their own counted
denominator, rounded to one decimal; the counts behind them are
exact. The recent history shows the last 10 sessions the price
history holds, no more, because those are the sessions this page
chooses to display; every one of the 399 sessions is computable
the same way. The scored run's summary carries its own vendor
style breadth sub-figure; this page does not use it, because it
cannot be recomputed from the closes and its recipe is not ours
to state.

Scope: the counted universe is the stocks in the daily scoring
run, stated as such on the page. Those are stocks listed today,
so a stock that stopped trading earlier is not in the count;
the page says so in plain words. The count is never presented
as the whole market.

What the sources carry (and what this script therefore shows):
- The price history: per stock, dated daily bars with closing
  prices. Its freshest session (October 23, 2026) is the
  session this page headlines; all timestamps come from the
  history, never from the clock.
- The scored run's published counts: checked, scored, and too
  little data, for the run's own session (October 27, 2026).
  The refresh recomputes each from the full scored list and
  proves the history holds exactly the scored names: every
  scored stock present, every too-little-data stock absent.

Honesty rules:
- If the card, the full list and the price history disagree
  with each other in any of those checks, the script fails
  instead of publishing a mismatched page.
- A stock with no bar on a session is not counted that session;
  its absence lowers the traded count, never a figure.
- Running this script twice on the same history produces the
  same file, byte for byte.

Usage: python3 refresh_breadth.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "board_card.json")
FULL_PATH = os.path.join(SOURCE_DIR, "board_full.json")
BARS_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "breadth-meter", "data.json")

HISTORY_SESSIONS_SHOWN = 10

SOURCE_WORDS = ("Daily closing prices for the stocks in the daily "
                "scoring run, over the price history on record")

DEFINITIONS = {
    "above_50": ("A stock is above its 50-session average when "
                 "its closing price is higher than the average of "
                 "its closing prices over the last 50 trading "
                 "sessions, today included."),
    "above_200": ("A stock is above its 200-session average when "
                  "its closing price is higher than the average "
                  "of its closing prices over the last 200 trading "
                  "sessions, today included."),
    "advancing": ("A stock advanced when it closed higher than "
                  "it closed on its previous trading day, and "
                  "declined when it closed lower."),
    "universe": ("The count covers the stocks in the daily "
                 "scoring run, which are stocks listed today, so "
                 "stocks that stopped trading earlier are not in "
                 "it."),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Breadth Meter refresh: {message}", file=sys.stderr)
    return 1


def pct(part, whole):
    return round(100.0 * part / whole, 1)


def build():
    for path in (CARD_PATH, FULL_PATH, BARS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    bars = load_json(BARS_PATH)

    summary = card["summary"]
    run_session = summary["as_of_session"]
    if full.get("as_of_session") != run_session:
        return fail(f"the full scored list is for "
                    f"{full.get('as_of_session')} but the board "
                    f"card is for {run_session}; refusing to "
                    "publish a mismatched page.")

    # --- Recompute the scored run's published counts from its
    # full list; the card must agree with its own list. ---
    rows = full["rows"]
    scored = [r for r in rows if not r.get("insufficient_data")]
    short = [r for r in rows if r.get("insufficient_data")]
    recomputed = {
        "universe": len(rows),
        "scored": len(scored),
        "insufficient_data": len(short),
        "qualified": sum(1 for r in scored if r["qualified"]),
    }
    for key, value in recomputed.items():
        if summary.get(key) != value:
            return fail(f"the card summary says {key}="
                        f"{summary.get(key)} but the full list "
                        f"holds {value}; refusing to publish a "
                        "mismatched page.")

    # --- The price history must hold exactly the scored names:
    # every scored stock present, every too-little-data stock
    # absent. That is the history agreeing with the scored run's
    # own published counts. ---
    scored_names = {r["symbol"] for r in scored}
    short_names = {r["symbol"] for r in short}
    bar_names = set(bars)
    if bar_names != scored_names:
        return fail(f"the price history holds {len(bar_names)} "
                    f"stocks but the scored run scored "
                    f"{len(scored_names)}; the names differ "
                    f"(history only: "
                    f"{sorted(bar_names - scored_names)[:5]}, "
                    f"run only: "
                    f"{sorted(scored_names - bar_names)[:5]}); "
                    "refusing to publish a mismatched page.")
    if bar_names & short_names:
        return fail("the price history holds stocks the scored "
                    "run set aside for too little data: "
                    f"{sorted(bar_names & short_names)}; refusing "
                    "to publish a mismatched page.")
    if not bars:
        return fail("the price history is empty; refusing to "
                    "publish.")

    # --- Per-stock closing series, dates strictly increasing. ---
    series = {}
    calendar = set()
    for symbol, stock_rows in bars.items():
        dates = []
        closes = []
        prev = None
        for row in stock_rows:
            date, close = row[0], row[4]
            if prev is not None and date <= prev:
                return fail(f"{symbol} has a repeated or "
                            f"out-of-order session {date}; "
                            "refusing to publish.")
            if not isinstance(close, (int, float)):
                return fail(f"{symbol} has a closing price that "
                            f"is not a number on {date}; refusing "
                            "to publish.")
            prev = date
            dates.append(date)
            closes.append(float(close))
            calendar.add(date)
        series[symbol] = (dates, closes,
                          {d: i for i, d in enumerate(dates)})
    if not calendar:
        return fail("the price history holds no dated bars; "
                    "refusing to publish.")
    calendar = sorted(calendar)
    freshest = calendar[-1]

    def compute(session):
        out = {"session": session, "traded": 0,
               "above_50": 0, "counted_50": 0,
               "above_200": 0, "counted_200": 0,
               "advancers": 0, "decliners": 0, "unchanged": 0}
        for dates, closes, pos in series.values():
            i = pos.get(session)
            if i is None:
                continue
            out["traded"] += 1
            if i > 0:
                if closes[i] > closes[i - 1]:
                    out["advancers"] += 1
                elif closes[i] < closes[i - 1]:
                    out["decliners"] += 1
                else:
                    out["unchanged"] += 1
            if i + 1 >= 50:
                out["counted_50"] += 1
                if closes[i] > sum(closes[i - 49:i + 1]) / 50.0:
                    out["above_50"] += 1
            if i + 1 >= 200:
                out["counted_200"] += 1
                if closes[i] > sum(closes[i - 199:i + 1]) / 200.0:
                    out["above_200"] += 1
        for key in ("above_50", "above_200"):
            counted = out["counted_" + key.split("_")[1]]
            out[key + "_pct"] = pct(out[key], counted) \
                if counted else None
        moved = out["advancers"] + out["decliners"] \
            + out["unchanged"]
        out["advancers_pct"] = pct(out["advancers"], moved) \
            if moved else None
        return out

    headline = compute(freshest)
    if headline["traded"] == 0 or headline["counted_50"] == 0 \
            or headline["counted_200"] == 0:
        return fail(f"the freshest session {freshest} counts "
                    "nothing for one of the measures; refusing "
                    "to publish an empty dial.")
    history = [compute(s)
               for s in calendar[-HISTORY_SESSIONS_SHOWN:]]

    universe_words = (
        f"Counted from the {len(scored_names):,} stocks in the "
        f"daily scoring run (the run checked "
        f"{summary['universe']:,} stocks for {run_session} and "
        f"scored {summary['scored']:,}; "
        f"{summary['insufficient_data']} had too little data to "
        "score and are not counted)")

    data = {
        "tool": "Breadth Meter",
        "session": freshest,
        "scored_run_session": run_session,
        "source": SOURCE_WORDS,
        "history_sessions_on_record": len(calendar),
        "history_from": calendar[0],
        "history_to": freshest,
        "universe": {
            "names_in_run": summary["universe"],
            "names_scored": summary["scored"],
            "names_too_little_data": summary["insufficient_data"],
            "names_in_history": len(bar_names),
            "words": universe_words,
        },
        "headline": headline,
        "history": history,
        "definitions": DEFINITIONS,
        "coverage": (
            f"{universe_words}; on {freshest}, "
            f"{headline['traded']:,} of them traded, "
            f"{headline['counted_50']:,} had the 50 sessions "
            f"behind them for the shorter average and "
            f"{headline['counted_200']:,} had the 200 sessions "
            "for the longer one"),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {freshest}, "
          f"above 50-session average "
          f"{headline['above_50']} of {headline['counted_50']} "
          f"({headline['above_50_pct']}%), above 200-session "
          f"average {headline['above_200']} of "
          f"{headline['counted_200']} "
          f"({headline['above_200_pct']}%), advancers "
          f"{headline['advancers']} vs decliners "
          f"{headline['decliners']}, scored run {run_session})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
