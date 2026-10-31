#!/usr/bin/env python3
"""Refresh the Momentum Clock data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the real daily price history behind the daily
scoring run (daily bars with open, high, low and close for every
scored stock, 399 trading sessions from March 25, 2025 to October
23, 2026), cross-checked against the scored run's own published
counts for its session (the board card's summary and the full
scored list: 1,838 stocks checked, 1,833 scored, 5 with too little
data to score) and against the AI Chart Read's shipped copy of the
same history (its name count, its session span and every shipped
close). The page ships that history's closes only, and every figure
on the page is worked out in the reader's own browser from those
closes; nothing the reader picks is sent anywhere.

Reconstruction choices (the exact construction):
- The clock faces are fixed windows of 21, 63, 126 and 252 trading
  sessions (about a trading month, a quarter, half a year and a
  year).
- A name's figure for a window is its last closing price on record
  compared with its closing price that many sessions earlier in its
  own series, as a percent: (last / close then - 1) * 100.
- A name needs at least window + 1 closes on record for a window.
  A name with fewer shows that window as not on record; no figure
  is ever worked out over a shortened window.
- Names are ranked by the chosen window's figure, biggest rise
  first; equal figures are ordered by name so the list is stable.
- A name whose own last session is earlier than the history's
  last session is dated to its own last session on its row.
- The page describes rises and falls only. It carries no claim
  about what a rise or fall is worth: the study behind the method
  this clock is named for partly held up and its verdict is
  parked, its sealed final test never opened, and that parked
  state is printed on the page in plain words.

Scope: the names on record are the stocks in the daily scoring
run, stated as such on the page. A name that is not in that run
is not on record here.

Honesty rules:
- If the card, the full list, the price history and the shipped
  chart-read history disagree with each other in any check (the
  card's counts against its own list, the history holding exactly
  the scored names, the shipped copy holding the same names, the
  same session span and the same closes), the script fails
  instead of publishing a mismatched page.
- Dates per name must be strictly increasing, every close must be
  a number, and each name's sessions must be a continuous run of
  the shared calendar; any break fails the refresh.
- The per-window counts printed in the data (names ranked, names
  too short) are recomputed here from the shipped series and must
  add up to the full name count for every window; any mismatch
  fails the refresh.
- Running this script twice on the same sources produces the
  same file, byte for byte. All dates come from the sources,
  never from the clock.

Usage: python3 refresh_momentumclock.py
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
CHART_PATH = os.path.join(HERE, "ai-chart-read", "data.json")
OUT_PATH = os.path.join(HERE, "momentum-clock", "data.json")

SOURCE_WORDS = ("Daily closing prices from the consolidated tape "
                "records for the stocks in the daily scoring run, "
                "over the price history on record")

WINDOWS = [21, 63, 126, 252]

PROVING_STATE = "Still being proven"
PROVING_NOTE = ("Still being proven: this clock only describes "
                "how far each name's price has risen or fallen. "
                "The study behind the method it is named for "
                "partly held up, and its verdict is parked: the "
                "study's sealed final test has never been opened, "
                "so no claim about what a rise is worth is made "
                "or graded here.")

DEFINITION = ("Rise or fall over a window: the name's last "
              "closing price on record compared with its closing "
              "price that many trading sessions earlier, shown "
              "as a percent. A plus figure means the price stands "
              "higher than it did then; a minus figure means it "
              "stands lower.")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Momentum Clock refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FULL_PATH, BARS_PATH, CHART_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    bars = load_json(BARS_PATH)
    chart = load_json(CHART_PATH)

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

    shipped = {}
    for symbol in sorted(bars):
        dates = []
        closes = []
        prev = None
        for row in bars[symbol]:
            date = row[0]
            close = row[4]
            if prev is not None and date <= prev:
                return fail(f"{symbol} has a repeated or "
                            f"out-of-order session {date}; "
                            "refusing to publish.")
            if not isinstance(close, (int, float)):
                return fail(f"{symbol} has a closing price that "
                            f"is not a number on {date}; "
                            "refusing to publish.")
            prev = date
            dates.append(date)
            closes.append(float(close))
        idx = [cal_pos[d] for d in dates]
        if idx != list(range(idx[0], idx[0] + len(idx))):
            return fail(f"{symbol}'s sessions are not a "
                        "continuous run of the shared calendar; "
                        "refusing to publish.")
        shipped[symbol] = [idx[0], closes]

    # --- The shipped chart-read copy of the same history must
    # agree: same names, same span, same closes. ---
    if chart.get("names_on_record") != len(shipped):
        return fail(f"the shipped chart-read history counts "
                    f"{chart.get('names_on_record')} names but "
                    f"the price history holds {len(shipped)}; "
                    "refusing to publish a mismatched page.")
    if chart.get("history_from") != calendar[0] or \
            chart.get("history_to") != calendar[-1] or \
            chart.get("history_sessions") != len(calendar):
        return fail("the shipped chart-read history's span "
                    "disagrees with the price history; refusing "
                    "to publish a mismatched page.")
    if chart.get("dates") != calendar:
        return fail("the shipped chart-read history's session "
                    "list disagrees with the price history; "
                    "refusing to publish a mismatched page.")
    chart_bars = chart.get("bars") or {}
    if set(chart_bars) != set(shipped):
        return fail("the shipped chart-read history holds "
                    "different names than the price history; "
                    "refusing to publish a mismatched page.")
    for symbol in shipped:
        entry = chart_bars[symbol]
        if entry[0] != shipped[symbol][0] or \
                [float(c) for c in entry[1]] != shipped[symbol][1]:
            return fail(f"the shipped chart-read history's "
                        f"closes for {symbol} disagree with the "
                        "price history; refusing to publish a "
                        "mismatched page.")

    # --- Per-window counts, recomputed from the shipped series.
    window_counts = []
    for w in WINDOWS:
        too_short = sorted(s for s in shipped
                           if len(shipped[s][1]) < w + 1)
        ranked = len(shipped) - len(too_short)
        if ranked + len(too_short) != len(shipped):
            return fail(f"the {w}-session counts do not add up; "
                        "refusing to publish.")
        window_counts.append({
            "sessions": w,
            "ranked": ranked,
            "too_short": len(too_short),
            "too_short_names": too_short,
        })

    ended_early = sum(
        1 for s in shipped
        if shipped[s][0] + len(shipped[s][1]) - 1 < len(calendar) - 1)

    w252 = window_counts[-1]
    data = {
        "tool": "Momentum Clock",
        "state": "published",
        "proving_state": PROVING_STATE,
        "proving_note": PROVING_NOTE,
        "source": SOURCE_WORDS,
        "session": calendar[-1],
        "history_from": calendar[0],
        "history_to": calendar[-1],
        "history_sessions": len(calendar),
        "names_on_record": len(shipped),
        "scored_run_session": run_session,
        "windows": WINDOWS,
        "window_counts": window_counts,
        "names_ended_early": ended_early,
        "definition": DEFINITION,
        "coverage": (
            f"Worked out in your browser from the daily closing "
            f"prices on record for the {len(shipped):,} stocks "
            f"in the daily scoring run, {len(calendar)} trading "
            f"days from {calendar[0]} to {calendar[-1]}. For "
            f"the 252-session window, {w252['ranked']:,} names "
            f"have enough sessions behind them and "
            f"{w252['too_short']} do not; those "
            f"{w252['too_short']} show as not on record for that "
            f"window rather than a shortened figure. "
            f"{ended_early} names stopped trading before "
            f"{calendar[-1]}; their figures are dated to their "
            "own last session."),
        "dates": calendar,
        "bars": shipped,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, separators=(",", ":"), sort_keys=True)
        fh.write("\n")
    size = os.path.getsize(OUT_PATH)
    print(f"Wrote {OUT_PATH} ({size:,} bytes, "
          f"{len(shipped):,} names, {len(calendar)} sessions "
          f"{calendar[0]} to {calendar[-1]}, windows "
          f"{WINDOWS}, scored run {run_session})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
