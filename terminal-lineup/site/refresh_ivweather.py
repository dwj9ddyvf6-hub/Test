#!/usr/bin/env python3
"""Refresh the IV Weather data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: three separate recorded ledgers of implied
volatility readings, all ending on 2026-10-14, none of them for
SPY, QQQ or IWM, and none carrying more than one expiry for a name
on the same day:
  1. A daily snapshot ledger of per-strike implied volatility for
     20 large names, 12 dated readings each from 2026-10-02 to
     2026-10-14, each reading carrying 4 to 5 strikes at one expiry
     about three to four weeks out.
  2. A set of 8 dated daily files of blended 30-day implied
     volatility for 41 names (40 with readings, 1 skipped every
     day for having no option contracts), 2026-10-05 to 2026-10-14,
     each reading a single blended number with the one or two
     expiry dates it was blended from, but no per-expiry values.
  3. A short ledger of single implied volatility numbers for 13
     small names, exactly 2 dated readings each (2026-10-13 and
     2026-10-14), with a separate summary file stating its row
     count and first and last dates.
The three ledgers measure volatility in different ways, so they
are published as three separate groups and never merged into one
number for a name. A name can appear in more than one group, once
per way it was measured.

Hookup addition (2026-10-30): a fourth group, kept separate for
the same reason. The chain snapshot cure (stream B) landed a
modelled per-strike volatility ledger for SPY, QQQ and IWM
(iv_ledger_modelled.jsonl in the chain store, every row labelled
MODELLED with its model stated). Those three index names had no
volatility readings on record before; their modelled readings
are published as group four, never merged with the recorded
ledgers, and the group's own words say they are modelled.

Reconstruction choices (stated as this build's own choices):
  - Ledger 1 carries several strikes per reading, not one number.
    A reading's published number is the implied volatility of the
    strike closest to the stock's recorded price that day; when
    two strikes are equally close, their two readings are
    averaged. This reduction is this build's stated choice.
  - Duplicate readings in ledger 1 are handled by that ledger's
    own documented dedupe rule: keep the last occurrence per
    (date, name, strike). The other two ledgers have no documented
    dedupe rule, so a duplicate reading in either of them stops
    this refresh rather than being silently handled.
  - Where a reading sits in its own history is stated in plain
    words from the recorded range only: high means the current
    reading is in the top quarter of its own recorded low-to-high
    range, low means the bottom quarter, and middle means between
    those quarters. The counts of readings below and above the
    current one are printed beside it.
  - No history percentile is published for any name. A percentile
    needs at least 30 dated readings (this build's stated floor);
    the fullest history on record has 12, so every name is shown
    with its reading count and its recorded range only.
  - No term structure shape is published: no ledger carries
    readings for more than one expiry for a name on the same day
    as separate values, so there is no shape on record to show.
  - Every date and time published comes from the records
    themselves, never from the clock.

Non-claims: this build does not claim any reading is current (the
newest reading on record is dated 2026-10-14), does not claim a
percentile or a term structure for any name, does not merge the
three ways of measuring into one figure, and does not cover SPY,
QQQ or IWM, which have no volatility readings on record.

Fail-closed rules: a ledger missing or unreadable; a row with a
missing or unreadable date, name, strike or volatility; rows in
one ledger-1 reading that disagree on the stock price, target
strike, average range or days to expiry recorded with them; a
ledger-2 file whose inside date disagrees with its file name, or
a name in it carrying neither a reading nor a skipped marker; a
duplicate reading in ledger 2 or 3; or ledger 3's summary file
disagreeing with its ledger on row count or first or last date.
Any of these stops the refresh and publishes nothing.

Usage: python3 refresh_ivweather.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
DESK = os.path.join(WORKSPACE, "alpaca-swing-desk", "desk")
LEDGER1_PATH = os.path.join(DESK, "research", "bilbo-options",
                            "iv_snapshots.jsonl")
LEDGER2_DIR = os.path.join(DESK, "context", "sentiment", "options",
                           "iv_skew")
LEDGER3_PATH = os.path.join(DESK, "hidden_state",
                            "iron_condor_iv_history.jsonl")
LEDGER3_SUMMARY_PATH = os.path.join(DESK, "hidden_state",
                                    "iron_condor_iv_baseline.json")
OUT_PATH = os.path.join(HERE, "iv-weather", "data.json")

PERCENTILE_FLOOR = 30

SOURCE_WORDS = ("Implied volatility readings recorded day by day "
                "from the prices of stock options")

GROUP1_HEADING = "Readings from options expiring a few weeks out"
GROUP1_KIND = ("Each reading is the volatility priced into the "
               "option strike closest to the stock's price that "
               "day, from options expiring in the number of days "
               "shown with the latest reading.")
GROUP2_HEADING = "Blended 30-day readings"
GROUP2_KIND = ("Each reading is one blended 30-day volatility "
               "number, worked out from the one or two expiry "
               "dates nearest 30 days out.")
GROUP3_HEADING = "Single recorded readings"
GROUP3_KIND = ("Each reading is a single volatility number "
               "recorded for the name, with no strike or expiry "
               "recorded beside it.")

TERM_NOTE = ("No term structure shape is shown: none of the first "
             "three records carries volatility readings for more "
             "than one expiry for the same name on the same day as "
             "separate values, so there is no shape on record to "
             "show from them. The modelled chain record does carry "
             "several expiries for its three index names; no shape "
             "is drawn from it on this page yet.")

GROUP4_HEADING = "Modelled readings from the chain snapshots"
GROUP4_KIND = ("Each reading is a modelled volatility number for "
               "the three index funds, worked out from the prices "
               "of options in the stored chain snapshots (the "
               "model is stated in that record). The reading shown "
               "is the strike closest to the fund's price that day, "
               "with the call and put readings at that strike "
               "averaged. Modelled, not recorded from a trade.")
MODELLED_LEDGER_PATH = os.path.join(
    WORKSPACE, "morgue", "state", "morgue", "chains",
    "iv_ledger_modelled.jsonl")
PERCENTILE_NOTE = ("No percentile is shown for any name: a "
                   "percentile needs at least 30 dated readings, "
                   "and the fullest history on record has 12. "
                   "Each name shows its reading count and the "
                   "low-to-high range of its own readings instead.")


def fail(message):
    print(f"IV Weather refresh: {message}", file=sys.stderr)
    return None


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def read_date(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def position(series, current):
    low = min(series)
    high = max(series)
    below = sum(1 for v in series if v < current - 1e-12)
    above = sum(1 for v in series if v > current + 1e-12)
    if high - low < 1e-12:
        word = "the same at every reading"
    else:
        frac = (current - low) / (high - low)
        if frac >= 0.75:
            word = "high in its own history"
        elif frac <= 0.25:
            word = "low in its own history"
        else:
            word = "in the middle of its own history"
    return {
        "iv_percent": round(current * 100, 2),
        "low_percent": round(low * 100, 2),
        "high_percent": round(high * 100, 2),
        "readings": len(series),
        "readings_below": below,
        "readings_above": above,
        "position": word,
    }


def name_entry(symbol, dated_series, latest_extra):
    """dated_series: list of (date, value) sorted by date."""
    series = [v for _, v in dated_series]
    entry = {"symbol": symbol, "date": dated_series[-1][0]}
    entry.update(position(series, series[-1]))
    entry["first_date"] = dated_series[0][0]
    entry.update(latest_extra)
    return entry


def load_ledger1():
    if not os.path.exists(LEDGER1_PATH):
        return None, "the daily snapshot ledger was not found"
    rows = []
    try:
        with open(LEDGER1_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except (OSError, ValueError) as exc:
        return None, f"the daily snapshot ledger could not be read: {exc}"
    if not rows:
        return None, "the daily snapshot ledger carries no rows"
    # The ledger's own documented dedupe rule: keep the last
    # occurrence per (date, name, strike).
    deduped = {}
    duplicates = 0
    for row in rows:
        if not isinstance(row, dict):
            return None, "a row in the daily snapshot ledger is not a record"
        day = read_date(row.get("date"))
        symbol = row.get("symbol")
        if day is None or not isinstance(symbol, str) or not symbol:
            return None, "a row in the daily snapshot ledger has no date or name"
        if not is_number(row.get("strike")) or not is_number(row.get("iv")):
            return None, f"a row for {symbol} on {day} has no strike or reading"
        key = (day, symbol, row["strike"])
        if key in deduped:
            duplicates += 1
        deduped[key] = row
    readings = {}
    for (day, symbol, _strike), row in deduped.items():
        readings.setdefault((day, symbol), []).append(row)
    per_symbol = {}
    for (day, symbol), group in sorted(readings.items()):
        for field in ("underlying", "target_strike", "atr14", "expiry_dte"):
            if len({r.get(field) for r in group}) != 1:
                return None, (f"the rows for {symbol} on {day} disagree "
                              f"on the {field} recorded with them")
            if not is_number(group[0].get(field)):
                return None, (f"the rows for {symbol} on {day} carry no "
                              f"readable {field}")
        underlying = group[0]["underlying"]
        nearest = min(abs(r["strike"] - underlying) for r in group)
        tied = [r["iv"] for r in group
                if abs(abs(r["strike"] - underlying) - nearest) < 1e-9]
        value = sum(tied) / len(tied)
        per_symbol.setdefault(symbol, []).append(
            (day, value, group[0]["expiry_dte"]))
    names = []
    for symbol in sorted(per_symbol):
        dated = sorted(per_symbol[symbol])
        entry = name_entry(symbol, [(d, v) for d, v, _ in dated],
                           {"expiry_days": dated[-1][2]})
        names.append(entry)
    return {"heading": GROUP1_HEADING, "kind": GROUP1_KIND,
            "names": names, "duplicates_collapsed": duplicates}, None


def _no_dup_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate key {key!r}")
        obj[key] = value
    return obj


def load_ledger2():
    if not os.path.isdir(LEDGER2_DIR):
        return None, "the folder of daily blended readings was not found"
    files = sorted(f for f in os.listdir(LEDGER2_DIR)
                   if f.endswith(".json"))
    if not files:
        return None, "the folder of daily blended readings is empty"
    per_symbol = {}
    skipped = set()
    generated = []
    seen = set()
    for fname in files:
        path = os.path.join(LEDGER2_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh, object_pairs_hook=_no_dup_object)
        except (OSError, ValueError) as exc:
            return None, f"a daily blended reading file could not be read: {exc}"
        if not isinstance(doc, dict):
            return None, "a daily blended reading file is not a record"
        day = read_date(doc.get("date"))
        if day is None or day != fname[:-5]:
            return None, (f"the date inside {fname} disagrees with "
                          f"its file name")
        stamp = doc.get("generated_at")
        if not isinstance(stamp, str) or "T" not in stamp:
            return None, f"the blended readings for {day} carry no recorded time"
        generated.append(stamp)
        symbols = doc.get("symbols")
        if not isinstance(symbols, dict) or not symbols:
            return None, f"the blended readings for {day} carry no names"
        for symbol, value in symbols.items():
            if not isinstance(value, dict):
                return None, f"the blended reading for {symbol} on {day} is not a record"
            if "iv30" in value:
                if not is_number(value["iv30"]):
                    return None, f"the blended reading for {symbol} on {day} is not a number"
                key = (day, symbol)
                if key in seen:
                    return None, f"a duplicate blended reading for {symbol} on {day}"
                seen.add(key)
                per_symbol.setdefault(symbol, []).append((day, value["iv30"]))
            elif "skipped" in value:
                skipped.add(symbol)
            else:
                return None, (f"the entry for {symbol} on {day} carries "
                              f"neither a reading nor a skipped marker")
    names = []
    for symbol in sorted(per_symbol):
        dated = sorted(per_symbol[symbol])
        names.append(name_entry(symbol, dated, {}))
    return {"heading": GROUP2_HEADING, "kind": GROUP2_KIND,
            "names": names, "recorded_at": max(generated),
            "names_skipped": sorted(skipped - set(per_symbol))}, None


def load_ledger3():
    for path, label in ((LEDGER3_PATH, "the short ledger of single readings"),
                        (LEDGER3_SUMMARY_PATH, "its summary file")):
        if not os.path.exists(path):
            return None, f"{label} was not found"
    rows = []
    try:
        with open(LEDGER3_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        with open(LEDGER3_SUMMARY_PATH, "r", encoding="utf-8") as fh:
            summary = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, f"the short ledger of single readings could not be read: {exc}"
    if not rows:
        return None, "the short ledger of single readings carries no rows"
    per_symbol = {}
    seen = set()
    days = []
    for row in rows:
        if not isinstance(row, dict):
            return None, "a row in the short ledger is not a record"
        day = read_date(row.get("date"))
        symbol = row.get("symbol")
        if day is None or not isinstance(symbol, str) or not symbol \
                or not is_number(row.get("iv")):
            return None, "a row in the short ledger has no date, name or reading"
        key = (day, symbol)
        if key in seen:
            return None, f"a duplicate single reading for {symbol} on {day}"
        seen.add(key)
        days.append(day)
        per_symbol.setdefault(symbol, []).append((day, row["iv"]))
    if not isinstance(summary, dict) \
            or summary.get("rows") != len(rows) \
            or summary.get("min_date") != min(days) \
            or summary.get("max_date") != max(days):
        return None, ("the summary file disagrees with the short "
                      "ledger on its row count or its first or "
                      "last date")
    recorded = summary.get("recorded_at")
    if not isinstance(recorded, str) or "T" not in recorded:
        return None, "the summary file carries no readable recorded time"
    names = []
    for symbol in sorted(per_symbol):
        dated = sorted(per_symbol[symbol])
        names.append(name_entry(symbol, dated, {}))
    return {"heading": GROUP3_HEADING, "kind": GROUP3_KIND,
            "names": names, "recorded_at": recorded}, None


def load_ledger4_modelled():
    """The modelled per-strike IV ledger from the chain snapshots
    (cure stream B's IV source of record). One source, kept as its
    own group: modelled numbers are never merged with the recorded
    ledgers above. Dedupe: keep the last row per
    (date, name, contract), the ledger's own republication rule."""
    if not os.path.exists(MODELLED_LEDGER_PATH):
        return None, "the modelled chain volatility ledger was not found"
    rows = []
    try:
        with open(MODELLED_LEDGER_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except (OSError, ValueError) as exc:
        return None, (f"the modelled chain volatility ledger could "
                      f"not be read: {exc}")
    if not rows:
        return None, "the modelled chain volatility ledger carries no rows"
    deduped = {}
    for row in rows:
        if not isinstance(row, dict):
            return None, "a row in the modelled ledger is not a record"
        day = read_date(row.get("date"))
        symbol = row.get("underlying")
        if day is None or not isinstance(symbol, str) or not symbol:
            return None, "a row in the modelled ledger has no date or name"
        if not is_number(row.get("strike")) or not is_number(row.get("iv")) \
                or not is_number(row.get("spot")):
            return None, (f"a modelled row for {symbol} on {day} has "
                          "no strike, reading or price")
        if row.get("iv_basis") != "MODELLED":
            return None, (f"a row for {symbol} on {day} is not labelled "
                          "MODELLED; refusing to publish it as modelled")
        deduped[(day, symbol, row.get("occ"))] = row
    per_day = {}
    for (day, symbol, _occ), row in deduped.items():
        per_day.setdefault((day, symbol), []).append(row)
    per_symbol = {}
    for (day, symbol), group in sorted(per_day.items()):
        spots = {r["spot"] for r in group}
        if len(spots) != 1:
            return None, (f"the modelled rows for {symbol} on {day} "
                          "disagree on the price recorded with them")
        spot = group[0]["spot"]
        nearest = min(abs(r["strike"] - spot) for r in group)
        tied = [r for r in group
                if abs(abs(r["strike"] - spot) - nearest) < 1e-9]
        value = sum(r["iv"] for r in tied) / len(tied)
        expiry = min(r["expiry"] for r in tied)
        days = (date.fromisoformat(expiry) - date.fromisoformat(day)).days
        per_symbol.setdefault(symbol, []).append((day, value, days))
    names = []
    for symbol in sorted(per_symbol):
        dated = sorted(per_symbol[symbol])
        entry = name_entry(symbol, [(d, v) for d, v, _ in dated],
                           {"expiry_days": dated[-1][2]})
        names.append(entry)
    return {"heading": GROUP4_HEADING, "kind": GROUP4_KIND,
            "names": names}, None


def build():
    groups = []
    for loader in (load_ledger1, load_ledger2, load_ledger3,
                   load_ledger4_modelled):
        group, err = loader()
        if err:
            return fail(err)
        groups.append(group)
    all_dates = [n["date"] for g in groups for n in g["names"]]
    if not all_dates:
        return fail("the records carry no volatility readings at all")
    distinct = {n["symbol"] for g in groups for n in g["names"]}
    fullest = max(n["readings"] for g in groups for n in g["names"])
    return {
        "tool": "IV Weather",
        "source": SOURCE_WORDS,
        "freshest_date": max(all_dates),
        "oldest_date": min(n["first_date"] for g in groups
                           for n in g["names"]),
        "distinct_names": len(distinct),
        "percentile_floor": PERCENTILE_FLOOR,
        "fullest_history": fullest,
        "percentile_note": PERCENTILE_NOTE,
        "term_structure_note": TERM_NOTE,
        "term_structure": None,
        "groups": groups,
    }


def main():
    doc = build()
    if doc is None:
        return 1
    doc = _tc.stamp_for_script(doc, __file__) if _tc is not None else doc
    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, OUT_PATH)
    counts = ", ".join(f"{len(g['names'])} names in group {i + 1}"
                       for i, g in enumerate(doc["groups"]))
    print(f"IV Weather refresh: wrote {OUT_PATH} ({counts}; "
          f"{doc['distinct_names']} distinct names; freshest reading "
          f"{doc['freshest_date']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
