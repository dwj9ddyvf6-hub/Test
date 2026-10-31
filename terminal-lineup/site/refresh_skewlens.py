#!/usr/bin/env python3
"""Refresh the Skew Lens data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: one recorded ledger of per-strike implied
volatility readings for 20 large names, 12 dated readings each
from 2026-10-02 to 2026-10-14, each reading carrying 4 to 5 strike
rows at one expiry about three to four weeks out, and a second,
separate set of 8 dated daily files carrying one precomputed
skew number per name with no per-strike records behind it and no
statement of how that number was built. The index funds SPY, QQQ
and IWM have no per-strike volatility records in any source, and
the recorded options chain archive holds no snapshot yet.

The skew construction, stated exactly:
  - Matched distances: for one name on one day, the put side is
    the recorded put strike closest to 10 percent below that
    day's recorded stock price, and the call side is the recorded
    call strike closest to 10 percent above it. A strike counts
    as matched only when it sits between 9 and 11 percent away
    from the price on its side.
  - Side must be on record: a strike row counts as a put reading
    or a call reading only when the row itself carries that side.
    Which side a strike is on is never worked out from where the
    strike sits next to the price; that would be an estimate.
  - Expiry: both sides must be for the same expiry. The per-strike
    ledger records an expiry only as a count of days to expiry,
    so both rows must carry the same day and the same days-to-
    expiry count; where a record carries a calendar expiry date,
    the two dates must match exactly.
  - Comparison: the figure is the put side's volatility reading
    minus the call side's volatility reading, in percentage
    points. A positive figure means the downside puts are priced
    richer than the upside calls by that many points; a negative
    figure means the upside calls are priced richer.

Reconstruction choices (stated as this build's own choices):
  - The 9-to-11 percent matched band around the 10 percent
    distance is this build's stated choice, fixed in advance.
  - Duplicate readings in the per-strike ledger are handled by
    that ledger's own documented rule: keep the last occurrence
    per (date, name, strike), and the number collapsed is counted
    and published.
  - The precomputed skew numbers in the second set of files are
    never published as figures: they carry no per-strike records
    and no construction statement, so they cannot be checked
    against the construction above. They are counted only.
  - Every date published comes from the records themselves,
    never from the clock.

Non-claims: this build does not claim a skew figure for any name
whose record does not carry both sides at matched distances for
the same day and expiry, does not estimate a missing side, and
does not cover SPY, QQQ or IWM, which have no per-strike
volatility records on record.

Fail-closed rules: the per-strike ledger missing or unreadable;
a row with a missing or unreadable date, name, strike or reading;
rows in one reading that disagree on the stock price, target
strike, average range or days to expiry recorded with them; a
daily file in the second set whose inside date disagrees with
its file name, or a name in it carrying neither a reading nor a
skipped marker; a duplicate reading in the second set, which has
no documented dedupe rule. Any of these stops the refresh and
publishes nothing.

Usage: python3 refresh_skewlens.py
"""

import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
DESK = os.path.join(WORKSPACE, "alpaca-swing-desk", "desk")
LEDGER1_PATH = os.path.join(DESK, "research", "bilbo-options",
                            "iv_snapshots.jsonl")
LEDGER2_DIR = os.path.join(DESK, "context", "sentiment", "options",
                           "iv_skew")
OUT_PATH = os.path.join(HERE, "skew-lens", "data.json")

TARGET_DISTANCE = 0.10
BAND_LOW = 0.09
BAND_HIGH = 0.11

SOURCE_WORDS = ("Per-strike volatility readings recorded day by "
                "day from the prices of stock options")

CONSTRUCTION_WORDS = (
    "How a figure is worked out: for one name on one day, take "
    "the put reading at the strike closest to 10 percent below "
    "that day's recorded stock price and the call reading at the "
    "strike closest to 10 percent above it. A strike only counts "
    "when it sits between 9 and 11 percent away from the price on "
    "its side, both readings must be for the same expiry, and a "
    "reading only counts as a put or a call reading when the "
    "record itself says which side it is. The figure is the put "
    "reading minus the call reading, in points: a positive figure "
    "means downside puts are priced richer than upside calls by "
    "that many points.")

EMPTY_WORDS = (
    "In the recorded per-strike ledger, no name carries put-side "
    "and call-side readings at matched distances for the same day "
    "and the same expiry, so no figure is shown from that ledger "
    "for any name. That ledger holds strikes at and above each "
    "stock's price, with no side recorded for any strike, and no "
    "strike anywhere near 10 percent below the price. A figure "
    "from it will appear here only when it carries both sides.")

MODELLED_LEDGER_PATH = os.path.join(
    WORKSPACE, "morgue", "state", "morgue", "chains",
    "iv_ledger_modelled.jsonl")
MODELLED_WORDS = (
    "Modelled figures, kept separate from the recorded ledger "
    "above: the stored chain snapshots carry a modelled "
    "volatility reading for every strike of SPY, QQQ and IWM, "
    "with the side on each row and the model stated in that "
    "record. The same matched-distance construction is applied "
    "to the nearest expiry at least 7 days out. Modelled, not "
    "recorded from a trade.")


def fail(message):
    print(f"Skew Lens refresh: {message}", file=sys.stderr)
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


def side_of(row):
    """The side a row is on record as, or None when not recorded."""
    for field in ("side", "kind", "option_type", "type"):
        value = row.get(field)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in ("put", "p"):
                return "put"
            if lowered in ("call", "c"):
                return "call"
    return None


def load_ledger1():
    if not os.path.exists(LEDGER1_PATH):
        return None, "the per-strike ledger was not found"
    rows = []
    try:
        with open(LEDGER1_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except (OSError, ValueError) as exc:
        return None, f"the per-strike ledger could not be read: {exc}"
    if not rows:
        return None, "the per-strike ledger carries no rows"
    # The ledger's own documented dedupe rule: keep the last
    # occurrence per (date, name, strike).
    deduped = {}
    duplicates = 0
    for row in rows:
        if not isinstance(row, dict):
            return None, "a row in the per-strike ledger is not a record"
        day = read_date(row.get("date"))
        symbol = row.get("symbol")
        if day is None or not isinstance(symbol, str) or not symbol:
            return None, "a row in the per-strike ledger has no date or name"
        if not is_number(row.get("strike")) or not is_number(row.get("iv")):
            return None, f"a row for {symbol} on {day} has no strike or reading"
        key = (day, symbol, row["strike"])
        if key in deduped:
            duplicates += 1
        deduped[key] = row
    groups = {}
    for (day, symbol, _strike), row in deduped.items():
        groups.setdefault((day, symbol), []).append(row)
    figures = []
    no_figure = {}
    groups_without_side = 0
    groups_without_matched = 0
    for (day, symbol), group in sorted(groups.items()):
        for field in ("underlying", "target_strike", "atr14", "expiry_dte"):
            if len({r.get(field) for r in group}) != 1:
                return None, (f"the rows for {symbol} on {day} disagree "
                              f"on the {field} recorded with them")
            if not is_number(group[0].get(field)):
                return None, (f"the rows for {symbol} on {day} carry no "
                              f"readable {field}")
        price = group[0]["underlying"]
        puts = [r for r in group if side_of(r) == "put"]
        calls = [r for r in group if side_of(r) == "call"]
        entry = no_figure.setdefault(symbol, {"symbol": symbol,
                                              "date": day})
        entry["date"] = max(entry["date"], day)
        if not puts or not calls:
            groups_without_side += 1
            continue
        put_target = price * (1 - TARGET_DISTANCE)
        call_target = price * (1 + TARGET_DISTANCE)
        put = min(puts, key=lambda r: abs(r["strike"] - put_target))
        call = min(calls, key=lambda r: abs(r["strike"] - call_target))
        put_dist = (price - put["strike"]) / price
        call_dist = (call["strike"] - price) / price
        if not (BAND_LOW <= put_dist <= BAND_HIGH
                and BAND_LOW <= call_dist <= BAND_HIGH):
            groups_without_matched += 1
            continue
        diff = round((put["iv"] - call["iv"]) * 100, 2)
        if diff > 0:
            sentence = (f"Downside puts priced richer than upside "
                        f"calls by {diff:g} points")
        elif diff < 0:
            sentence = (f"Upside calls priced richer than downside "
                        f"puts by {abs(diff):g} points")
        else:
            sentence = ("Downside puts and upside calls priced the "
                        "same")
        figures.append({
            "symbol": symbol,
            "date": day,
            "expiry_days": group[0]["expiry_dte"],
            "put_strike": put["strike"],
            "call_strike": call["strike"],
            "put_percent": round(put["iv"] * 100, 2),
            "call_percent": round(call["iv"] * 100, 2),
            "points": diff,
            "sentence": sentence,
        })
    names = sorted(no_figure.values(), key=lambda e: e["symbol"])
    days = sorted({day for day, _ in groups})
    return {
        "strike_rows": len(deduped),
        "duplicates_collapsed": duplicates,
        "dated_readings": len(groups),
        "names": names,
        "figures": figures,
        "groups_without_side": groups_without_side,
        "groups_without_matched": groups_without_matched,
        "oldest_date": days[0],
        "freshest_date": days[-1],
    }, None


def _no_dup_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate key {key!r}")
        obj[key] = value
    return obj


def load_ledger2_counts():
    """Count the precomputed numbers only; they are never figures."""
    if not os.path.isdir(LEDGER2_DIR):
        return None, "the folder of daily blended readings was not found"
    files = sorted(f for f in os.listdir(LEDGER2_DIR)
                   if f.endswith(".json"))
    if not files:
        return None, "the folder of daily blended readings is empty"
    freshest_day = None
    freshest_with_number = 0
    names_seen = set()
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
        symbols = doc.get("symbols")
        if not isinstance(symbols, dict) or not symbols:
            return None, f"the blended readings for {day} carry no names"
        with_number = 0
        for symbol, value in symbols.items():
            if not isinstance(value, dict):
                return None, f"the blended reading for {symbol} on {day} is not a record"
            if is_number(value.get("skew25")):
                with_number += 1
                names_seen.add(symbol)
            elif value.get("skew25") is None and "iv30" in value:
                pass  # the number is recorded as absent that day
            elif "skipped" in value:
                pass
            else:
                return None, (f"the entry for {symbol} on {day} carries "
                              f"neither a reading nor a skipped marker")
        if freshest_day is None or day > freshest_day:
            freshest_day = day
            freshest_with_number = with_number
    return {"files": len(files), "freshest_date": freshest_day,
            "freshest_names_with_number": freshest_with_number,
            "names_with_number": len(names_seen)}, None


def load_modelled_figures():
    """Skew figures from the modelled chain ledger (cure stream
    B's IV source of record), under this page's own construction:
    side read from the row itself, same expiry both sides, put
    closest to 10 percent below the recorded price and call
    closest to 10 percent above, each inside the 9 to 11 percent
    band. Expiry choice: the nearest expiry at least 7 days out,
    the basis the chain cure used when it proved skew computes
    from this store. Dedupe: keep the last row per
    (date, name, contract)."""
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
        expiry = read_date(row.get("expiry"))
        if day is None or expiry is None \
                or not isinstance(symbol, str) or not symbol:
            return None, "a modelled row has no date, expiry or name"
        if not is_number(row.get("strike")) or not is_number(row.get("iv")) \
                or not is_number(row.get("spot")):
            return None, (f"a modelled row for {symbol} on {day} has "
                          "no strike, reading or price")
        if row.get("iv_basis") != "MODELLED":
            return None, (f"a row for {symbol} on {day} is not labelled "
                          "MODELLED; refusing to publish it as modelled")
        if side_of(row) is None:
            return None, (f"a modelled row for {symbol} on {day} "
                          "carries no side on record")
        deduped[(day, symbol, row.get("occ"))] = row
    groups = {}
    for (day, symbol, _occ), row in deduped.items():
        groups.setdefault((day, symbol), []).append(row)
    figures = []
    freshest = None
    for (day, symbol), group in sorted(groups.items()):
        spots = {r["spot"] for r in group}
        if len(spots) != 1:
            return None, (f"the modelled rows for {symbol} on {day} "
                          "disagree on the price recorded with them")
        price = group[0]["spot"]
        expiries = sorted({r["expiry"] for r in group
                           if (date.fromisoformat(r["expiry"])
                               - date.fromisoformat(day)).days >= 7})
        if not expiries:
            continue
        expiry = expiries[0]
        rows_e = [r for r in group if r["expiry"] == expiry]
        puts = [r for r in rows_e if side_of(r) == "put"]
        calls = [r for r in rows_e if side_of(r) == "call"]
        if not puts or not calls:
            continue
        put_target = price * (1 - TARGET_DISTANCE)
        call_target = price * (1 + TARGET_DISTANCE)
        put = min(puts, key=lambda r: abs(r["strike"] - put_target))
        call = min(calls, key=lambda r: abs(r["strike"] - call_target))
        put_dist = (price - put["strike"]) / price
        call_dist = (call["strike"] - price) / price
        if not (BAND_LOW <= put_dist <= BAND_HIGH
                and BAND_LOW <= call_dist <= BAND_HIGH):
            continue
        diff = round((put["iv"] - call["iv"]) * 100, 2)
        if diff > 0:
            sentence = (f"Downside puts priced richer than upside "
                        f"calls by {diff:g} points")
        elif diff < 0:
            sentence = (f"Upside calls priced richer than downside "
                        f"puts by {abs(diff):g} points")
        else:
            sentence = ("Downside puts and upside calls priced the "
                        "same")
        figures.append({
            "symbol": symbol,
            "date": day,
            "expiry": expiry,
            "expiry_days": (date.fromisoformat(expiry)
                            - date.fromisoformat(day)).days,
            "put_strike": put["strike"],
            "call_strike": call["strike"],
            "put_percent": round(put["iv"] * 100, 2),
            "call_percent": round(call["iv"] * 100, 2),
            "points": diff,
            "sentence": sentence,
            "basis": "modelled",
        })
        freshest = day if freshest is None or day > freshest else freshest
    # One figure per name: the freshest day on record for it.
    latest = {}
    for f in figures:
        if f["symbol"] not in latest or f["date"] > latest[f["symbol"]]["date"]:
            latest[f["symbol"]] = f
    checked = sorted({symbol for (_day, symbol) in groups})
    return {"figures": sorted(latest.values(),
                              key=lambda f: f["symbol"]),
            "no_figure": [s for s in checked if s not in latest],
            "freshest_date": freshest}, None


def build():
    ledger1, err = load_ledger1()
    if err:
        return fail(err)
    counts2, err = load_ledger2_counts()
    if err:
        return fail(err)
    modelled, err = load_modelled_figures()
    if err:
        return fail(err)
    return {
        "tool": "Skew Lens",
        "source": SOURCE_WORDS,
        "construction": CONSTRUCTION_WORDS,
        "empty_note": EMPTY_WORDS,
        "freshest_date": ledger1["freshest_date"],
        "oldest_date": ledger1["oldest_date"],
        "names_on_record": len(ledger1["names"]),
        "dated_readings": ledger1["dated_readings"],
        "strike_rows": ledger1["strike_rows"],
        "duplicates_collapsed": ledger1["duplicates_collapsed"],
        "readings_without_side": ledger1["groups_without_side"],
        "readings_without_matched_pair": ledger1["groups_without_matched"],
        "precomputed_files": counts2["files"],
        "precomputed_freshest_date": counts2["freshest_date"],
        "precomputed_freshest_names": counts2["freshest_names_with_number"],
        "figures": ledger1["figures"],
        "names": ledger1["names"],
        "modelled_words": MODELLED_WORDS,
        "modelled_figures": modelled["figures"],
        "modelled_no_figure": modelled["no_figure"],
        "modelled_freshest_date": modelled["freshest_date"],
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
    print(f"Skew Lens refresh: wrote {OUT_PATH} "
          f"({doc['names_on_record']} names on record, "
          f"{len(doc['figures'])} figures, freshest record "
          f"{doc['freshest_date']}, duplicates collapsed "
          f"{doc['duplicates_collapsed']})")
    # Record-surface cure (2026-10-31): surface this page's full
    # record in its own data.json, from numbers already on file.
    try:
        import record_surface as _rs
        _rs.enrich_slug("skew-lens")
    except Exception as _exc:
        print(f"record-surface enrich failed: {_exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
