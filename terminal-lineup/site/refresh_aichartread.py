#!/usr/bin/env python3
"""Refresh the AI Chart Read data file.

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
data to score), plus the Strat Scanner's published label record
for its freshest session (October 23, 2026), read exactly as
published there. The page ships that history's closes, highs and
lows so the read is worked out in the reader's own browser;
nothing the reader picks is sent anywhere.

Reconstruction choices (the exact construction):
- Averages: the 50-session average is the mean of the name's last
  50 closing prices, the last session included; the 200-session
  average is the same over 200. A name with fewer sessions on
  record than an average needs shows no figure for that average
  and no trend word that needs it.
- Trend words, by the fixed rule printed on the page (the same
  above/below form the Regime Dial prints for its trend checks,
  applied to one name against its own averages): the close above
  both averages reads "Trending up"; below both reads "Trending
  down"; above one and below (or at) the other reads "Mixed: no
  clear reading". A close exactly at an average counts as not
  above it and not below it, so it reads mixed unless it is below
  both or above both by the stated comparisons.
- Key levels: the highest high and the lowest low over the
  name's last 20 sessions, and the same over its last 126
  sessions, each with the session it fell on. A name with fewer
  sessions than a window shows no levels for that window.
- Pattern labels: the Strat Scanner's published labels only,
  carried as labels: the freshest session's label with its plain
  name and meaning, the labels for the last 5 sessions, and the
  shape, failed-2 flag and completed patterns where the record
  carries them. A name the record does not cover says so plainly.
- The read describes the chart as it stands on the last session
  in the shipped history. It contains no statement about any
  later session.

Scope: the names on record are the stocks in the daily scoring
run, stated as such on the page. A name that is not in that run
is shown as not on record, never read from a guess.

Honesty rules:
- If the card, the full list, the price history and the label
  record disagree with each other in any check (the card's counts
  against its own list, the history holding exactly the scored
  names, the label record covering only names in the history and
  naming the history's own last session and session count), the
  script fails instead of publishing a mismatched page.
- Dates per name must be strictly increasing, every bar's high,
  low and close must be numbers with the high at least the low,
  and each name's sessions must be a continuous run of the shared
  calendar; any break fails the refresh.
- Running this script twice on the same sources produces the
  same file, byte for byte. All dates come from the sources,
  never from the clock.

Usage: python3 refresh_aichartread.py
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
STRAT_PATH = os.path.join(HERE, "strat-scanner", "data.json")
OUT_PATH = os.path.join(HERE, "ai-chart-read", "data.json")

SOURCE_WORDS = ("Daily prices from the consolidated tape records "
                "for the stocks in the daily scoring run, over "
                "the price history on record")

PROVING_STATE = "Still being proven"
PROVING_NOTE = ("Still being proven: this read has no graded "
                "record of its own yet. Every sentence in the "
                "read is worked out on the page from the numbers "
                "printed beside it, by the rules printed on the "
                "page.")

RULE = {
    "trend": ("Trend words, by a fixed rule: the close above "
              "both of its averages reads trending up; the close "
              "below both reads trending down; any other mix "
              "reads mixed, no clear reading."),
    "averages": ("The 50-session average is the average of the "
                 "name's last 50 closing prices, the last "
                 "session included. The 200-session average is "
                 "the same count over 200 closing prices."),
    "levels": ("Key levels are the highest high price and the "
               "lowest low price over the last 20 sessions, and "
               "the same pair over the last 126 sessions, each "
               "with the session it fell on."),
    "labels": ("Pattern labels are the published bar-pattern "
               "labels for the name's freshest sessions, carried "
               "as labels only, with the meaning printed for "
               "each label."),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"AI Chart Read refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FULL_PATH, BARS_PATH, STRAT_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    bars = load_json(BARS_PATH)
    strat = load_json(STRAT_PATH)

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
        highs = []
        lows = []
        prev = None
        for row in bars[symbol]:
            date = row[0]
            high, low, close = row[2], row[3], row[4]
            if prev is not None and date <= prev:
                return fail(f"{symbol} has a repeated or "
                            f"out-of-order session {date}; "
                            "refusing to publish.")
            for value in (high, low, close):
                if not isinstance(value, (int, float)):
                    return fail(f"{symbol} has a price that is "
                                f"not a number on {date}; "
                                "refusing to publish.")
            if high < low:
                return fail(f"{symbol} has a high below its low "
                            f"on {date}; refusing to publish.")
            prev = date
            dates.append(date)
            closes.append(float(close))
            highs.append(float(high))
            lows.append(float(low))
        idx = [cal_pos[d] for d in dates]
        if idx != list(range(idx[0], idx[0] + len(idx))):
            return fail(f"{symbol}'s sessions are not a "
                        "continuous run of the shared calendar; "
                        "refusing to publish.")
        shipped[symbol] = [idx[0], closes, highs, lows]

    # --- The Strat Scanner's published label record. ---
    if strat.get("history_to") != calendar[-1]:
        return fail(f"the label record's last session is "
                    f"{strat.get('history_to')} but the price "
                    f"history ends {calendar[-1]}; refusing to "
                    "publish a mismatched page.")
    if strat.get("history_from") != calendar[0] or \
            strat.get("history_sessions_on_record") != len(calendar):
        return fail("the label record's history span disagrees "
                    "with the price history; refusing to publish "
                    "a mismatched page.")
    if strat.get("names_on_record") != len(shipped):
        return fail(f"the label record counts "
                    f"{strat.get('names_on_record')} names on "
                    f"record but the price history holds "
                    f"{len(shipped)}; refusing to publish a "
                    "mismatched page.")
    meanings = {}
    labels = {}
    for group in strat.get("groups") or []:
        meanings[group["key"]] = {
            "name": group["name"], "meaning": group["meaning"]}
        for entry in group.get("names") or []:
            symbol = entry["symbol"]
            if symbol not in shipped:
                return fail(f"the label record labels {symbol}, "
                            "which is not in the price history; "
                            "refusing to publish a mismatched "
                            "page.")
            if symbol in labels:
                return fail(f"the label record labels {symbol} "
                            "twice; refusing to publish.")
            if entry["label"] != group["key"]:
                return fail(f"{symbol}'s label {entry['label']} "
                            f"is filed under {group['key']}; "
                            "refusing to publish.")
            labels[symbol] = {
                "label": entry["label"],
                "name": group["name"],
                "meaning": group["meaning"],
                "colour": entry.get("colour"),
                "shape": entry.get("shape"),
                "failed_2": entry.get("failed_2"),
                "completed": entry.get("completed") or [],
                "sequence": entry.get("sequence") or [],
            }
    if len(labels) != strat.get("names_labelled"):
        return fail(f"the label record says "
                    f"{strat.get('names_labelled')} names were "
                    f"labelled but its groups hold {len(labels)}; "
                    "refusing to publish a mismatched page.")
    unlabelled = sorted(set(shipped) - set(labels))
    if len(unlabelled) != strat.get("names_not_labelled"):
        return fail("the label record's unlabelled count "
                    "disagrees with the price history; refusing "
                    "to publish a mismatched page.")

    data = {
        "tool": "AI Chart Read",
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
        "labels_session": strat.get("session"),
        "labels_on_record": len(labels),
        "labels_not_on_record": len(unlabelled),
        "coverage": (
            f"Reads are worked out in your browser from the "
            f"daily prices on record for the {len(shipped):,} "
            f"stocks in the daily scoring run, {len(calendar)} "
            f"trading days from {calendar[0]} to "
            f"{calendar[-1]}. Pattern labels are on record for "
            f"{len(labels):,} of those names for "
            f"{strat.get('session')}; {len(unlabelled)} names "
            f"carry no label for that day and the read says so. "
            "Stocks that stopped trading earlier are not in "
            "that run and are not on record here."),
        "rule": RULE,
        "label_meanings": meanings,
        "dates": calendar,
        "bars": shipped,
        "labels": labels,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, separators=(",", ":"), sort_keys=True)
        fh.write("\n")
    size = os.path.getsize(OUT_PATH)
    print(f"Wrote {OUT_PATH} ({size:,} bytes, "
          f"{len(shipped):,} names, {len(calendar)} sessions "
          f"{calendar[0]} to {calendar[-1]}, "
          f"{len(labels):,} labelled, scored run {run_session})")
    # Record-surface cure (2026-10-31): surface this page's full
    # record in its own data.json, from numbers already on file.
    try:
        import record_surface as _rs
        _rs.enrich_slug("ai-chart-read")
    except Exception as _exc:
        print(f"record-surface enrich failed: {_exc}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
