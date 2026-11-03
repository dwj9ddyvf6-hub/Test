#!/usr/bin/env python3
"""Refresh the Correlation Web data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no disclaimer-style copy on any reader surface of any tool, in pages or generated data, ever.

Evidence class: the real daily price history behind the daily
scoring run (daily closing prices for every scored stock, 399
trading sessions from March 25, 2025 to October 23, 2026),
cross-checked against the scored run's own published counts for
its session (the board card's summary and the full scored list:
1,838 stocks checked, 1,833 scored, 5 with too little data to
score). The figures on the page are computed directly from the
closing prices in that history, deterministically: the same
history always produces the same file.

Reconstruction choices (the exact construction): the correlation
measure is the Pearson correlation of daily returns. A name's
daily return on a session is its closing price that session
divided by its own previous traded closing price, minus one.
The window is the most recent 126 sessions of the history
(sessions April 27, 2026 to October 23, 2026 on the current
history). A pair is published only when the two names share at
least 40 overlapping return days inside that window, and the
overlap count is printed beside every pair; a pair under that
floor is shown as not enough shared history, with its shared-day
count, and no number or label. Returns ship rounded to the
nearest hundredth of a percent (whole numbers in the data file,
in hundredths of a percent) so the page stays small; the page
computes each picked pair's correlation in the reader's browser
from those returns, on shared days only. On top of that, this
refresh precomputes each name's three closest matches across the
whole list: the three other names with the highest correlation
to it under the same construction and the same 40-day floor,
each with its overlap count. The reader picks up to 10 names, so
the page computes at most 45 pairs among the picks. A pair's
plain-words label is read off its correlation as printed (two
decimals), so the words beside a printed number always match
that number: the printed scale's bands meet at the two-decimal
boundaries.

Scope: the counted universe is the stocks in the daily scoring
run, stated as such on the page. Those are stocks listed today,
so a stock that stopped trading earlier is not in the count;
the page says so in plain words. The count is never presented
as the whole market.

What the sources carry (and what this script therefore shows):
- The price history: per stock, dated daily bars with closing
  prices. Its freshest session (October 23, 2026) ends the
  window this page uses; all timestamps come from the history,
  never from the clock.
- The scored run's published counts: checked, scored, and too
  little data, for the run's own session (October 27, 2026).
  The refresh recomputes each from the full scored list and
  proves the history holds exactly the scored names: every
  scored stock present, every too-little-data stock absent.

Honesty rules:
- If the card, the full list and the price history disagree
  with each other in any of those checks, the script fails
  instead of publishing a mismatched page.
- A name with no bar on a session has no return that session;
  its absence lowers a pair's shared-day count, never a figure.
- Running this script twice on the same history produces the
  same file, byte for byte.

Usage: python3 refresh_correlation.py
"""

import json
import os
import sys

import numpy as np

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
OUT_PATH = os.path.join(HERE, "correlation-web", "data.json")

WINDOW_SESSIONS = 126
MIN_OVERLAP = 40
MAX_PICKS = 10
TWINS_PER_NAME = 3

SOURCE_WORDS = ("Daily closing prices for the stocks in the daily "
                "scoring run, over the price history on record")

SCALE = [
    {"low": 0.70, "high": 1.00, "label": "moves together closely"},
    {"low": 0.40, "high": 0.69, "label": "moves together somewhat"},
    {"low": 0.15, "high": 0.39, "label": "barely moves together"},
    {"low": -0.14, "high": 0.14, "label": "no clear link"},
    {"low": -0.39, "high": -0.15,
     "label": "tends to move opposite, a little"},
    {"low": -0.69, "high": -0.40, "label": "tends to move opposite"},
    {"low": -1.00, "high": -0.70, "label": "moves opposite closely"},
]

DEFINITIONS = {
    "construction": (
        "Each day's move for a name is its closing price that day "
        "divided by its own closing price on its previous trading "
        "day, minus one. How closely two names move together is "
        "measured from those daily moves over the window printed "
        "on the page, counting only the days both names traded."),
    "window": (
        f"The window is the most recent {WINDOW_SESSIONS} trading "
        "sessions in the price history on record."),
    "floor": (
        f"A pair is shown with a number only when the two names "
        f"share at least {MIN_OVERLAP} trading days inside the "
        "window. The shared-day count is printed beside every "
        "pair."),
    "universe": ("The names are the stocks in the daily scoring "
                 "run, which are stocks listed today, so stocks "
                 "that stopped trading earlier are not in it."),
    "newness": ("This way of putting daily price moves together "
                "is a new construction of ours and is still being "
                "proven."),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Correlation Web refresh: {message}", file=sys.stderr)
    return 1


def label_for(r):
    # The label is read off the number as printed (two decimals),
    # so the words beside a printed number always match it: the
    # printed bands meet at the two-decimal boundaries.
    r = round(float(r), 2)
    for band in SCALE:
        if band["low"] <= r <= band["high"]:
            return band["label"]
    return SCALE[0]["label"] if r > 1 else SCALE[-1]["label"]


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
        series[symbol] = (dates, closes)
    if not calendar:
        return fail("the price history holds no dated bars; "
                    "refusing to publish.")
    calendar = sorted(calendar)
    if len(calendar) < WINDOW_SESSIONS:
        return fail(f"the price history holds {len(calendar)} "
                    f"sessions, fewer than the "
                    f"{WINDOW_SESSIONS}-session window; refusing "
                    "to publish.")
    # Session agreement guard (CORR-RUN-DATE-20261031): this
    # page's session is the price history's last session, while
    # its coverage words name the scored run's session. When the
    # panel has advanced past the scored run (or the reverse),
    # publishing would state a run date one session behind the
    # data on the same page, the state the audit caught. Fail
    # closed instead: the two records must name the same session
    # before any figure is published.
    if run_session != calendar[-1]:
        return fail(f"the scored run is for {run_session} but "
                    f"the price history ends {calendar[-1]}; "
                    "refusing to publish a page whose coverage "
                    "names a different session than its data.")
    window_dates = calendar[-WINDOW_SESSIONS:]
    window_pos = {d: i for i, d in enumerate(window_dates)}

    symbols = sorted(series)
    n = len(symbols)
    w = len(window_dates)
    # Daily returns in hundredths of a percent, aligned to the
    # window; None where the name did not trade that session or
    # has no previous traded close.
    returns_bp = []
    raw = np.full((n, w), np.nan)
    days_in_window = []
    for si, symbol in enumerate(symbols):
        dates, closes = series[symbol]
        row = [None] * w
        count = 0
        for i, date in enumerate(dates):
            j = window_pos.get(date)
            if j is None:
                continue
            count += 1
            if i > 0:
                r = closes[i] / closes[i - 1] - 1.0
                bp = int(round(r * 10000.0))
                row[j] = bp
                raw[si, j] = bp
        returns_bp.append(row)
        days_in_window.append(count)
    covered = sum(1 for c in days_in_window if c >= MIN_OVERLAP)
    full_cov = sum(1 for c in days_in_window if c == w)
    if covered == 0:
        return fail("no name has enough sessions in the window; "
                    "refusing to publish an empty page.")

    # --- Closest matches (twins) for every name: Pearson
    # correlation on shared days only, same floor, ranked by the
    # correlation itself, highest first. Computed pairwise from
    # masked sums so short histories are handled the same way the
    # page handles them. ---
    present = ~np.isnan(raw)
    filled = np.where(present, raw, 0.0)
    cnt = present.astype(float) @ present.astype(float).T
    sx = filled @ present.astype(float).T
    sxx = (filled * filled) @ present.astype(float).T
    sxy = filled @ filled.T
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = sxy - sx * sx.T / cnt
        varx = sxx - sx * sx / cnt
        vary = sxx.T - sx.T * sx.T / cnt
        denom = np.sqrt(varx * vary)
        corr = np.where((cnt >= MIN_OVERLAP) & (denom > 0),
                        cov / denom, np.nan)
    np.fill_diagonal(corr, np.nan)
    twins = {}
    for si, symbol in enumerate(symbols):
        row = corr[si]
        ok = np.where(~np.isnan(row))[0]
        if ok.size == 0:
            twins[symbol] = []
            continue
        order = ok[np.argsort(-row[ok])][:TWINS_PER_NAME]
        twins[symbol] = [
            {"symbol": symbols[int(k)],
             "correlation": round(float(row[k]), 2),
             "label": label_for(float(row[k])),
             "shared_days": int(cnt[si, k])}
            for k in order
        ]

    universe_words = (
        f"Counted from the {len(scored_names):,} stocks in the "
        f"daily scoring run (the run checked "
        f"{summary['universe']:,} stocks for {run_session} and "
        f"scored {summary['scored']:,}; "
        f"{summary['insufficient_data']} had too little data to "
        "score and are not counted)")

    data = {
        "tool": "Correlation Web",
        "state": "published",
        "session": calendar[-1],
        "scored_run_session": run_session,
        "source": SOURCE_WORDS,
        "history_sessions_on_record": len(calendar),
        "history_from": calendar[0],
        "history_to": calendar[-1],
        "window_sessions": w,
        "window_from": window_dates[0],
        "window_to": window_dates[-1],
        "window_dates": window_dates,
        "min_overlap": MIN_OVERLAP,
        "max_picks": MAX_PICKS,
        "returns_unit": ("hundredths of a percent: a value of 123 "
                         "means the name rose 1.23% that day"),
        "symbols": symbols,
        "returns_bp": returns_bp,
        "twins": twins,
        "examples": [s for s in ("SPY", "QQQ", "AAPL")
                     if s in scored_names],
        "scale": SCALE,
        "definitions": DEFINITIONS,
        "coverage": {
            "names_on_record": len(symbols),
            "names_with_enough_days": covered,
            "names_with_full_window": full_cov,
            "words": universe_words,
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, separators=(",", ":"), sort_keys=True)
        fh.write("\n")
    size = os.path.getsize(OUT_PATH)
    spy = symbols.index("SPY")
    qqq = symbols.index("QQQ")
    print(f"Wrote {OUT_PATH} ({size:,} bytes, window "
          f"{window_dates[0]} to {window_dates[-1]}, "
          f"{len(symbols):,} names, {covered:,} with at least "
          f"{MIN_OVERLAP} days in window, {full_cov:,} with the "
          f"full window, SPY and QQQ correlation "
          f"{corr[spy, qqq]:.4f} on {int(cnt[spy, qqq])} shared "
          f"days, scored run {run_session})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
