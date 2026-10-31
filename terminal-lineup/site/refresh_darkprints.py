#!/usr/bin/env python3
"""Refresh the Dark Prints data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the published index dark-pool record itself: the
daily index card and the published daily summary, which carry, for
one trading session, the combined dark reading across the S&P 500
stocks (each stock's off-exchange short-sale share, weighted by
that stock's dollar trading volume that day) and each of the three
index funds' own off-exchange short-sale shares; plus the permanent
trading-day log, which carries the same funds' shares and the same
combined reading for the earlier sessions. The per-stock readings
behind the combined figure are stored per stock per session in the
daily short-volume store (the same published off-exchange file,
kept per name since the 2026-10-29 cure of gap G8); this page
publishes that store's real day count and its freshest session's
per-stock shares. No record anywhere carries individual large
off-exchange prints for a single stock: the daily file carries one
total per stock per day, not individual prints.

Reconstruction choices: the only figures computed here are
percentages: each stored share is shown as a percentage of that
session's own off-exchange volume, rounded to one decimal place,
next to the session it measures. The combined reading is the
record's own published figure with its own coverage (the stocks
that had data out of the index's stocks), never recomputed here
and never dressed up as a per-stock figure. The three index funds'
own shares are a different, simpler measure (each fund's own
off-exchange short-sale share) and are labelled as such, never
substituted for the combined reading. Earlier sessions come from
the permanent log's freshest entry for each session. Timestamps
come from the records (the card's build time, the summary's
publication time), never from the clock.

Non-claims: this tool publishes no per-stock dark reading, because
none is on record, and no list of large off-exchange prints for any
stock, because no record carries individual stock prints. The dark
reading is a short-sale share of off-exchange volume; it is not a
gauge of buying or selling pressure, and nothing on this page
treats it as one. The older whole-market per-stock short-sale
store kept by a different, retired system is a different measure
from a different file and is never substituted for this record.

Fail-closed rules: if the card and the published summary disagree
on any session, fund share, combined reading or its coverage; if
the permanent log's freshest entries for the freshest session
disagree with the card; if any fund or the combined reading is
missing from the card; or if the per-stock collection's state
stamps disagree with each other or with the days actually stored
(a live stamp whose day count, first or last day differs from the
store, or an empty stamp while days are stored), the refresh stops
and publishes nothing.

Honesty rules:
- Dates are read off the sources, never from the clock, so running
  this script twice produces the same file.
- Absence is not zero: a name with no reading on record is shown
  as not on record, never as a zero reading, and a session with no
  combined reading in the log is left out, never filled in.

Usage: python3 refresh_darkprints.py
"""

import gzip
import json
import math
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
CARD_PATH = os.path.join(MORGUE, "output", "map_card.json")
FEED_PATH = os.path.join(MORGUE, "output", "morgue-feed.json")
LEDGER_PATH = os.path.join(MORGUE, "output", "ledger.jsonl")
EXT_PATH = os.path.join(MORGUE, "state", "morgue", "ext.json")
SHORTVOL_DIR = os.path.join(MORGUE, "state", "morgue", "shortvol")
OUT_PATH = os.path.join(HERE, "dark-prints", "data.json")

FUNDS = ("SPY", "QQQ", "IWM")

SOURCE_WORDS = ("The published daily off-exchange trading file: "
                "for each stock, the shares sold short off the "
                "public exchanges that day and that stock's total "
                "shares traded that day, combined across the "
                "stocks of the S&P 500 and weighted by each "
                "stock's dollar trading volume")
MEASURE_WORDS = ("The dark reading measures the share of a "
                 "session's off-exchange trading volume that was "
                 "sold short that session.")
PER_NAME_EMPTY_COVERAGE = (
                     "Per-stock dark readings are not on record: "
                     "the daily per-stock collection has not "
                     "started: 0 stocks on record, 0 sessions on "
                     "record. No stock is shown with a reading of "
                     "its own because there is no stored reading "
                     "to show")
PRINTS_COVERAGE = ("Large off-exchange prints for a single stock "
                   "are not on record: the daily off-exchange file "
                   "carries one total per stock per day, not "
                   "individual prints, and no record kept here "
                   "lists individual stock prints. The options "
                   "prints kept for the three index funds are a "
                   "different record and are not shown as stock "
                   "prints")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Dark Prints refresh: {message}", file=sys.stderr)
    return 1


def pct(ratio):
    return round(ratio * 100.0, 1)


def lane_stamp(doc):
    lanes = (doc.get("lanes") or {}).get("lanes") or {}
    return lanes.get("short_volume")


try:
    import engine_adaptations as _ea
except ImportError:  # pragma: no cover
    _ea = None

PANEL_HISTORY_PATH = os.path.join(HERE, "dark-prints",
                                  "panel-history.json")


def panel_reliability_block(history, used, total):
    """FE20 panel reliability for the combined dark print
    aggregate (DEEP-PASS 3.2 item 11, second application). The
    panel is the index constituent set behind the combined
    reading. Coverage is the freshest session's used over total
    count, as published. Stability is one minus the coverage
    range across the sessions on record. Drift is the z of the
    freshest coverage against the earlier sessions' coverages:
    the earlier coverages on record are identical (501 of 503
    on every earlier session), so their variance is zero and a
    drift z is undefined, not large; the reliability is
    honestly not_recorded and the aggregate is not discounted.
    The per session coverage snapshot is recorded from this
    refresh on so a drift series can be built."""
    coverages = []
    for entry in history:
        u, t = entry.get("index_used"), entry.get("index_total")
        if u and t:
            coverages.append(u / t)
    coverage = used / total if used and total else None
    stability = None
    if len(coverages) >= 2:
        stability = 1.0 - (max(coverages) - min(coverages))
    drift_z = None
    drift_state = "undefined: fewer than two earlier sessions"
    if len(coverages) >= 3:
        prior = coverages[:-1]
        mean = sum(prior) / len(prior)
        var = sum((c - mean) ** 2 for c in prior) / len(prior)
        if var > 1e-12:
            drift_z = (coverages[-1] - mean) / math.sqrt(var)
            drift_state = "recorded"
        else:
            drift_state = ("undefined: the earlier sessions' "
                           "coverages are identical, so their "
                           "variance is zero and no drift z "
                           "exists")
    reliability = (_ea.fe20_panel_reliability(
        round(stability, 4) if stability is not None else None,
        round(coverage, 4) if coverage is not None else None,
        drift_z)
        if _ea is not None else
        {"state": "not_recorded", "reliability": None,
         "missing": ["panel_drift_z"]})
    block = {
        "form": ("reliability = panel_stability * coverage / "
                 "(1 + abs(panel_drift_z)); panel derived inputs "
                 "are discounted by the reliability"),
        "state": reliability["state"],
        "reliability": reliability["reliability"],
        "missing": reliability["missing"],
        "panel_stability": (round(stability, 4)
                            if stability is not None else None),
        "stability_basis": ("one minus the coverage range "
                            "across the sessions on record"),
        "coverage": (round(coverage, 4)
                     if coverage is not None else None),
        "coverage_basis": ("freshest session stocks used over "
                           "stocks total, as published"),
        "panel_drift_z": (round(drift_z, 4)
                          if drift_z is not None else None),
        "panel_drift_state": drift_state,
        "note": ("The combined aggregate is published raw, not "
                 "discounted, while its panel reliability is "
                 "not recorded. Per session coverage snapshots "
                 "are recorded in panel-history.json from this "
                 "refresh on, so the drift series the form "
                 "needs can be built."),
    }
    snapshot = {"session": history[-1]["session"],
                "stocks_used": used, "stocks_total": total,
                "coverage": block["coverage"],
                "panel_stability": block["panel_stability"]}
    return block, snapshot


def write_panel_history(snapshot):
    """Upsert one session coverage snapshot into
    panel-history.json, keyed by session. Deterministic:
    rerunning on the same record rewrites the same file."""
    history = {}
    if os.path.exists(PANEL_HISTORY_PATH):
        try:
            with open(PANEL_HISTORY_PATH, "r", encoding="utf-8") as fh:
                history = json.load(fh)
        except (ValueError, OSError):
            history = {}
    entries = history.get("snapshots", {})
    entries[snapshot["session"]] = snapshot
    history = {"panel": "index constituents behind the combined "
                        "dark reading",
               "snapshots": {k: entries[k] for k in sorted(entries)}}
    with open(PANEL_HISTORY_PATH, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2, sort_keys=True)
        fh.write("\n")


def build():
    for path in (CARD_PATH, FEED_PATH, LEDGER_PATH, EXT_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card_doc = load_json(CARD_PATH)
    feed_doc = load_json(FEED_PATH)
    cards = {c.get("underlying"): c for c in card_doc.get("cards") or []}
    if sorted(cards) != sorted(FUNDS):
        return fail("the index card does not carry exactly the "
                    "three index funds; refusing to publish a "
                    "partial picture.")
    session = None
    for sym in FUNDS:
        c = cards[sym]
        if c.get("dix_ratio") is None or not c.get("dix_date"):
            return fail(f"{sym} carries no dark reading on the "
                        "index card; refusing to publish.")
        if session is None:
            session = c["dix_date"]
        elif c["dix_date"] != session:
            return fail("the index card's funds carry different "
                        "dark reading sessions; refusing to "
                        "publish a mixed picture.")
    spy = cards["SPY"]
    dix_index = spy.get("dix_index")
    if not dix_index or dix_index.get("date") != session \
            or dix_index.get("value") is None:
        return fail("the combined dark reading is missing from "
                    "the index card; refusing to publish.")
    used = dix_index.get("constituents_used")
    total = dix_index.get("constituents_total")
    if not used or not total:
        return fail("the combined dark reading carries no "
                    "coverage count; a reading without its "
                    "coverage stated is not publishable.")

    if feed_doc.get("as_of_session") != session:
        return fail("the published daily summary belongs to a "
                    "different session than the index card; "
                    "refusing to publish until they agree.")
    feed_map = {e.get("symbol"): e for e in feed_doc.get("map") or []}
    if sorted(feed_map) != sorted(FUNDS):
        return fail("the published daily summary does not carry "
                    "exactly the three index funds.")
    for sym in FUNDS:
        entry = feed_map[sym]
        if entry.get("dix_date") != session:
            return fail(f"the summary's {sym} dark reading "
                        "belongs to a different session.")
        if entry.get("dix") is None \
                or round(cards[sym]["dix_ratio"], 3) != entry["dix"]:
            return fail(f"the summary's {sym} dark share "
                        f"({entry.get('dix')}) disagrees with the "
                        f"index card's "
                        f"({round(cards[sym]['dix_ratio'], 3)}); "
                        "refusing to publish.")
    if feed_map["SPY"].get("dix_index") != dix_index:
        return fail("the summary's combined dark reading "
                    "disagrees with the index card's; refusing "
                    "to publish.")

    # Permanent log: freshest entry per (session, fund), and the
    # combined reading per session from the SPY entries.
    fund_best = {}
    index_best = {}
    with open(LEDGER_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("component") != "gex_static_v1":
                continue
            if row.get("dix_ratio") is not None and row.get("dix_date"):
                key = (row["dix_date"], row.get("underlying"))
                if key not in fund_best \
                        or row["ts_utc"] > fund_best[key][0]:
                    fund_best[key] = (row["ts_utc"], row["dix_ratio"])
            di = row.get("dix_index")
            if di and di.get("date") and di.get("value") is not None:
                if di["date"] not in index_best \
                        or row["ts_utc"] > index_best[di["date"]][0]:
                    index_best[di["date"]] = (row["ts_utc"], di)
    for sym in FUNDS:
        got = fund_best.get((session, sym))
        if got is None or got[1] != cards[sym]["dix_ratio"]:
            return fail(f"the permanent log's freshest {sym} dark "
                        "share for the session disagrees with "
                        "the index card; refusing to publish.")
    got_index = index_best.get(session)
    if got_index is None or got_index[1] != dix_index:
        return fail("the permanent log's combined dark reading "
                    "for the session disagrees with the index "
                    "card; refusing to publish.")

    history = []
    for day in sorted(index_best):
        funds = {}
        complete = True
        for sym in FUNDS:
            got = fund_best.get((day, sym))
            if got is None:
                complete = False
                break
            funds[sym] = pct(got[1])
        if not complete:
            continue
        di = index_best[day][1]
        history.append({
            "session": day,
            "index_pct": pct(di["value"]),
            "index_used": di.get("constituents_used"),
            "index_total": di.get("constituents_total"),
            "funds": funds,
        })
    if not history or history[-1]["session"] != session:
        return fail("the permanent log carries no complete "
                    "history ending at the card's session; "
                    "refusing to publish.")

    # Per-stock collection state: stamps must agree with each
    # other and with the days actually stored in the store.
    ext_stamp = lane_stamp(load_json(EXT_PATH))
    feed_stamp = lane_stamp(feed_doc)
    if not ext_stamp or not feed_stamp:
        return fail("one of the records carries no per-stock "
                    "collection state stamp; refusing to guess.")
    if ext_stamp != feed_stamp:
        return fail("the two records stamp the per-stock "
                    "collection differently; refusing to publish "
                    "until they agree.")
    try:
        stored_days = sorted(n[:-8] for n in os.listdir(SHORTVOL_DIR)
                             if n.endswith(".json.gz"))
    except OSError:
        stored_days = []
    per_name = None
    if not stored_days:
        if ext_stamp.get("status") != "no_data" \
                or ext_stamp.get("reason") != "no FINRA day stored yet":
            return fail("no per-stock day is stored, but the state "
                        "stamp does not say the collection is empty; "
                        "refusing to publish a state the records do "
                        "not agree on.")
        per_name = {
            "state": "not_on_record",
            "names_on_record": 0,
            "sessions_on_record": 0,
            "coverage": PER_NAME_EMPTY_COVERAGE,
        }
    else:
        if ext_stamp.get("status") != "ok" \
                or ext_stamp.get("days") != len(stored_days) \
                or ext_stamp.get("first_date") != stored_days[0] \
                or ext_stamp.get("last_date") != stored_days[-1]:
            return fail("per-stock days are stored, but the state "
                        "stamp does not describe the store (its "
                        "day count or its first or last day "
                        "differs); refusing to publish a state the "
                        "records do not agree on.")
        latest = stored_days[-1]
        try:
            with gzip.open(os.path.join(
                    SHORTVOL_DIR, f"{latest}.json.gz"),
                    "rt", encoding="utf-8") as fh:
                latest_doc = json.load(fh)
        except (OSError, ValueError, EOFError):
            return fail(f"the stored per-stock day {latest} "
                        "cannot be read; refusing to publish a "
                        "partial per-stock picture.")
        if latest_doc.get("date") != latest:
            return fail(f"the stored per-stock day filed as "
                        f"{latest} calls itself "
                        f"{latest_doc.get('date')}; refusing to "
                        "publish a mismatched day.")
        latest_pct = {}
        for sym, pair in (latest_doc.get("names") or {}).items():
            if isinstance(pair, (list, tuple)) and len(pair) == 2 \
                    and pair[1] and pair[1] > 0:
                latest_pct[sym] = pct(pair[0] / pair[1])
        if not latest_pct:
            return fail(f"the stored per-stock day {latest} "
                        "carries no usable per-stock reading; "
                        "refusing to publish an empty store as "
                        "live.")
        per_name_coverage = (
            f"Per-stock dark readings are on record: the daily "
            f"per-stock collection holds {len(stored_days)} "
            f"sessions, from {stored_days[0]} to {stored_days[-1]}. "
            f"The freshest session ({latest}) carries a reading "
            f"for {len(latest_pct)} stocks; look a stock up to see "
            f"its share for that session. A stock missing from a "
            f"session's file carries no reading for that session, "
            f"never a zero")
        per_name = {
            "state": "collecting",
            "names_on_record": len(latest_pct),
            "sessions_on_record": len(stored_days),
            "first_session": stored_days[0],
            "latest_session": latest,
            "latest": latest_pct,
            # The readings list is the shape the Silent
            # Accumulation engine (Engine 26) reads its dark leg
            # from: one row per stock for the freshest stored
            # session, pct as a percentage of that session's
            # off-exchange volume.
            "readings": [{"session": latest, "symbol": sym,
                          "pct": latest_pct[sym]}
                         for sym in sorted(latest_pct)],
            "coverage": per_name_coverage,
        }

    published_at = card_doc.get("built_utc")
    feed_at = feed_doc.get("generated_at_utc")
    if not published_at or not feed_at:
        return fail("a source carries no build time; refusing to "
                    "guess one.")

    coverage_pct = pct(dix_index["coverage"]) \
        if dix_index.get("coverage") is not None else None
    index_coverage = (f"Built from {used} of the {total} stocks "
                      f"in the index for the session of "
                      f"{session}: {used} stocks had the data "
                      "the reading needs"
                      + (f" ({coverage_pct}% of the index)"
                         if coverage_pct is not None else ""))
    if per_name["state"] == "collecting":
        per_name_words = (
            f"{per_name['names_on_record']} stocks on the freshest "
            f"stored session ({per_name['latest_session']}), "
            f"{per_name['sessions_on_record']} sessions on record "
            f"({per_name['first_session']} to "
            f"{per_name['latest_session']})")
    else:
        per_name_words = "0 stocks, 0 sessions on record"
    coverage = (f"Combined reading and the three index funds: "
                f"session {session}, {index_coverage}. Earlier "
                f"sessions on record: {len(history)} "
                f"({history[0]['session']} to "
                f"{history[-1]['session']}). Per-stock readings: "
                f"{per_name_words}. Large "
                "off-exchange prints per stock: none on record")

    panel_block, panel_snapshot = panel_reliability_block(
        history, used, total)

    data = {
        "tool": "Dark Prints",
        "state": "index_only" if per_name["state"] != "collecting"
                 else "index_and_per_name",
        "session": session,
        "published_at_utc": published_at,
        "summary_published_at_utc": feed_at,
        "measure": MEASURE_WORDS,
        "source": SOURCE_WORDS,
        "index_reading": {
            "name": "S&P 500 stocks combined",
            "pct": pct(dix_index["value"]),
            "session": session,
            "stocks_used": used,
            "stocks_total": total,
            "coverage": index_coverage,
        },
        "funds": [{
            "symbol": sym,
            "pct": pct(cards[sym]["dix_ratio"]),
            "session": session,
        } for sym in FUNDS],
        "history": history,
        "panel_reliability": panel_block,
        "per_name": per_name,
        "large_prints": {
            "state": "not_on_record",
            "coverage": PRINTS_COVERAGE,
        },
        "coverage": coverage,
        "receipt": {
            "session": session,
            "published": published_at,
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    write_panel_history(panel_snapshot)
    print(f"Wrote {OUT_PATH} (session {session}, combined "
          f"{data['index_reading']['pct']}%, {used} of {total} "
          f"stocks, per-stock {per_name['sessions_on_record']} "
          "sessions on record)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
