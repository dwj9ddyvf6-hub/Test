#!/usr/bin/env python3
"""Refresh the Grade My Call data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no disclaimer-style copy on any reader surface of any tool, in pages or generated data, ever.

Evidence class: the real daily price history behind the daily
scoring run (daily closing prices for every scored stock, 399
trading sessions from March 25, 2025 to October 23, 2026),
cross-checked against the scored run's own published counts for
its session (the board card's summary and the full scored list:
1,838 stocks checked, 1,833 scored, 5 with too little data to
score). The page ships that history's closing prices so the
grading happens in the reader's own browser; nothing the reader
enters is sent anywhere.

Reconstruction choices: the grading rule is the public
scoreboard's own. A call is graded from the name's closing price
on the call date; if that date is not a trading day for the name,
the next closing price the name has is the starting price, and
the page says so. The horizons are 1, 5 and 21 trading days
counted in the name's own trading days after the starting close.
The percent move is the change from the starting close to the
horizon close, divided by the starting close. A call that the
price would go up is right only when the move is above zero; a
call that it would go down is right only when the move is below
zero; an unchanged price makes neither call right. A call date
before the first session on record or after the last one is not
gradable, and the page says why instead of estimating. A horizon
the history has not reached yet is not gradable yet; the page
shows the weekday-counted date it becomes gradable, the same
counting the public scoreboard uses for its own first-grade
dates.

Shipped shape: one shared list of the 399 session dates, and per
name a pair of the index of its first session in that list and
its closing prices in order (every name's sessions are a
continuous run of the shared list, which this script verifies
before publishing). Only closing prices are shipped, because
closing prices are all the grading uses.

Scope: the names on record are the stocks in the daily scoring
run, stated as such on the page. A name that is not in that run
is shown as not on record, never graded from a guess.

Honesty rules:
- If the card, the full list and the price history disagree
  with each other in any of the checks the Breadth Meter refresh
  makes (the card's counts against its own list, and the history
  holding exactly the scored names), the script fails instead
  of publishing a mismatched page.
- Dates per name must be strictly increasing, closes must be
  numbers, and each name's sessions must be a continuous run of
  the shared calendar; any break fails the refresh.
- Running this script twice on the same history produces the
  same file, byte for byte. All dates come from the history,
  never from the clock.

Usage: python3 refresh_grademycall.py
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
OUT_PATH = os.path.join(HERE, "grade-my-call", "data.json")

SOURCE_WORDS = ("Daily closing prices for the stocks in the daily "
                "scoring run, over the price history on record")

METHOD = {
    "start": ("Your call is graded from the stock's closing price "
              "on the date you called it. If that date was not a "
              "trading day for the stock, the next closing price "
              "it has is the starting price, and your result "
              "says so."),
    "horizons": ("The grade is read at 1, 5 and 21 trading days "
                 "after the starting close, counted in the "
                 "stock's own trading days: the price then, the "
                 "percent move from the starting price, and "
                 "whether your call was right at that point."),
    "right": ("A call that the price would go up is right only "
              "when the price is higher at the grading point. A "
              "call that it would go down is right only when the "
              "price is lower. An unchanged price makes neither "
              "call right."),
    "not_yet": ("If a grading point has not happened yet in the "
                "price history on record, the result says not "
                "gradable yet and shows the date it becomes "
                "gradable. Nothing is estimated."),
    "outside": ("A call dated before the first day on record or "
                "after the last day on record cannot be graded "
                "from this history, and the result says so."),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Grade My Call refresh: {message}", file=sys.stderr)
    return 1


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

    calendar = sorted({row[0] for stock_rows in bars.values()
                       for row in stock_rows})
    if not calendar:
        return fail("the price history holds no dated bars; "
                    "refusing to publish.")
    cal_pos = {d: i for i, d in enumerate(calendar)}

    prices = {}
    for symbol in sorted(bars):
        dates = []
        closes = []
        prev = None
        for row in bars[symbol]:
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
        idx = [cal_pos[d] for d in dates]
        if idx != list(range(idx[0], idx[0] + len(idx))):
            return fail(f"{symbol}'s sessions are not a "
                        "continuous run of the shared calendar; "
                        "refusing to publish.")
        prices[symbol] = [idx[0], closes]

    data = {
        "tool": "Grade My Call",
        "source": SOURCE_WORDS,
        "history_from": calendar[0],
        "history_to": calendar[-1],
        "history_sessions": len(calendar),
        "names_on_record": len(prices),
        "scored_run_session": run_session,
        "coverage": (
            f"Grades are worked out in your browser from the "
            f"daily closing prices on record for the "
            f"{len(prices):,} stocks in the daily scoring run, "
            f"{len(calendar)} trading days from {calendar[0]} to "
            f"{calendar[-1]}. Stocks that stopped trading "
            "earlier are not in that run and are not on record "
            "here."),
        "method": METHOD,
        "dates": calendar,
        "prices": prices,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, separators=(",", ":"), sort_keys=True)
        fh.write("\n")
    size = os.path.getsize(OUT_PATH)
    print(f"Wrote {OUT_PATH} ({size:,} bytes, "
          f"{len(prices):,} names, {len(calendar)} sessions "
          f"{calendar[0]} to {calendar[-1]}, scored run "
          f"{run_session})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
