#!/usr/bin/env python3
"""Refresh the Morning Map data file.

Reads the real Morgue output (output/map_card.json, cross-checked against
output/morgue-feed.json) and writes site/morning-map/data.json in the shape
the Morning Map page renders.

Honesty rules:
- A figure the source does not carry is written as state "no_data" with a
  plain reason. It is never written as zero and never invented.
- All timestamps in data.json come from the source files, never from the
  clock, so running this script twice produces the same file.

Usage: python3 refresh_morning_map.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import session_history as _sh
except ImportError:  # refresh stays runnable standalone
    _sh = None

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(HERE, "morning-map", "session-history.json")
MORGUE_OUTPUT = os.path.expanduser("~/workspace/morgue/output")
MAP_CARD_PATH = os.path.join(MORGUE_OUTPUT, "map_card.json")
FEED_PATH = os.path.join(MORGUE_OUTPUT, "morgue-feed.json")
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "morning-map", "data.json")

SYMBOLS = ["SPY", "QQQ", "IWM"]

SPOT_BASIS_WORDS = ("session close from the price panel on record "
                    "(board_bt_bars.json), the same close every "
                    "panel tool publishes for the session")


def panel_session_close(panel, symbol, session):
    """The session close for one fund from the price panel, or
    None when the panel carries no bar for that session."""
    for row in panel.get(symbol) or []:
        if row[0] == session:
            return float(row[4])
    return None


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def is_missing(value):
    return value is None or value == "no_data"


def figure(value, receipt, missing_reason=None):
    """Wrap one figure: a real value with its receipt, or an honest no_data."""
    if is_missing(value):
        return {"state": "no_data", "value": None, "reason": missing_reason or
                "This reading was not in the latest published data."}
    return {"state": "ok", "value": value, "receipt": receipt}


VERIFIED_AVAILABILITY_REFS = []  # Empty by design: no source reviewed yet.


def clock_entry(value, source, absent_reason):
    """One contract clock: a source-carried value, or an explicit absence."""
    if value is None:
        return {"state": "absent", "value": None, "source": source,
                "missing_reason": absent_reason}
    return {"state": "present", "value": value, "source": source,
            "missing_reason": None}


def last_completed_session_before(day):
    """Most recent Mon-Fri date strictly before `day` (a date)."""
    d = day - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def build_contract(card_doc, feed_doc, session, built_utc, indexes):
    """Evidence-contract block (adopted contract v1.0.0, evaluation S7.4).

    Fail-closed: eligible only if every required field is present and
    fresh and a verified availability reference exists. Every value here
    is copied from the source files; a clock the sources do not carry
    is an explicit absence, never an invented timestamp.
    """
    feed_clocks = feed_doc.get("clocks") or {}

    def feed_clock(name):
        entry = feed_clocks.get(name) or {}
        return entry.get("value"), entry.get("missing_reason")

    event_value, event_reason = feed_clock("event_time")
    pub_value, _ = feed_clock("publication_time")
    avail_value, avail_reason = feed_clock("first_available_time")
    ing_value, _ = feed_clock("ingestion_time")
    decision_value, decision_reason = feed_clock("decision_as_of")
    if pub_value is None:
        pub_value = feed_doc.get("generated_at_utc")
    if ing_value is None:
        ing_value = feed_doc.get("generated_at_utc")

    clocks = {
        # Canonical contract clock names (eventAt/publishedAt/
        # availableAt/ingestedAt/decisionAt in the contract module).
        "eventAt": clock_entry(
            event_value, "morgue-feed.json clocks.event_time",
            event_reason or "The sources carry the session as a date, "
                            "not a recorded event instant."),
        "publishedAt": clock_entry(
            pub_value, "morgue-feed.json clocks.publication_time",
            "No publication timestamp was carried by the sources."),
        "availableAt": clock_entry(
            avail_value, "morgue-feed.json clocks.first_available_time",
            avail_reason or "First availability is not carried at the "
                            "aggregate feed level."),
        "ingestedAt": clock_entry(
            ing_value, "morgue-feed.json clocks.ingestion_time",
            "No ingestion timestamp was carried by the sources."),
        "decisionAt": clock_entry(
            decision_value, "morgue-feed.json clocks.decision_as_of",
            decision_reason or "The sources carry a session date, not a "
                               "timezone-qualified decision instant."),
    }

    # Task-named clock views of the same source-carried times.
    source_session = {"state": "present" if session else "absent",
                      "value": session,
                      "source": "morgue-feed.json as_of_session, "
                                "cross-checked map_card.json dix_date",
                      "missing_reason": None if session else
                      "No source session was carried by the sources."}
    computed_at = clock_entry(
        built_utc, "map_card.json built_utc",
        "No computation timestamp was carried by the sources.")
    data_as_of = {"state": source_session["state"], "value": session,
                  "source": "map_card.json dix_date / feed as_of_session "
                            "(a session date, not an instant)",
                  "missing_reason": source_session["missing_reason"]}

    grading = {}
    cards = {c.get("underlying"): c for c in card_doc.get("cards", [])}
    for symbol in SYMBOLS:
        dix_index = (cards.get(symbol) or {}).get("dix_index")
        if dix_index and dix_index.get("state"):
            grading[symbol] = {"state": dix_index["state"],
                               "date": dix_index.get("date") or session,
                               "value": dix_index.get("value")}
        else:
            grading[symbol] = {
                "state": "absent", "date": None, "value": None,
                "missing_reason": "No constituent grading state was "
                                  "carried for this index."}
    grading_states = {g["state"] for g in grading.values()}
    grading_horizon = {
        "state": "present" if grading_states == {"graded"} else
                 "partial" if "graded" in grading_states else "absent",
        "per_index": grading,
    }

    constituents = {}
    for ix in indexes:
        dc = ix.get("dark_pool_constituents") or {}
        if dc.get("state") == "ok":
            constituents[ix["symbol"]] = {"state": "present",
                                          "value": dc.get("value")}
        else:
            constituents[ix["symbol"]] = {
                "state": "absent", "value": None,
                "reason": dc.get("reason") or
                "The constituent reading was not in the latest data."}

    # Freshness, judged only from source-carried times: the session
    # must be the last completed session before the publication date
    # (America/New_York), the same rule the page's stale banner uses.
    fresh = False
    fresh_detail = "Freshness could not be judged: a required clock " \
                   "is absent."
    if session and pub_value:
        try:
            pub_day = datetime.fromisoformat(pub_value) \
                .astimezone(ZoneInfo("America/New_York")).date()
            session_day = datetime.strptime(session, "%Y-%m-%d").date()
            expected = last_completed_session_before(pub_day)
            fresh = session_day == expected
            fresh_detail = (
                f"session {session} vs last completed session "
                f"{expected.isoformat()} before publication date "
                f"{pub_day.isoformat()} (America/New_York)")
        except ValueError:
            fresh_detail = "Freshness could not be judged: a source " \
                           "timestamp did not parse."

    blockers = []
    for name, entry in clocks.items():
        if entry["state"] == "absent":
            blockers.append(f"clocks.{name}: absent ({entry['missing_reason']})")
    if computed_at["state"] == "absent":
        blockers.append("computed_at: absent (no computation timestamp "
                        "in the sources)")
    if not fresh:
        blockers.append(f"freshness: not fresh ({fresh_detail})")
    for symbol, entry in constituents.items():
        if entry["state"] == "absent":
            blockers.append(f"dark_pool_constituents.{symbol}: absent, "
                            f"not zero ({entry['reason']})")
    if grading_horizon["state"] != "present":
        blockers.append(f"grading_horizon: {grading_horizon['state']} "
                        "(constituent grading state is not present for "
                        "every index)")
    required_figures = ("positioning", "call_wall", "put_wall", "flip",
                        "dark_pool_etf")
    for ix in indexes:
        if ix.get("state") != "ok":
            blockers.append(f"indexes.{ix.get('symbol')}: absent")
            continue
        for field in required_figures:
            if (ix.get(field) or {}).get("state") != "ok":
                blockers.append(f"indexes.{ix['symbol']}.{field}: absent")
    if not VERIFIED_AVAILABILITY_REFS:
        blockers.append("verified_registry: empty by design; no source "
                        "has been reviewed into the verified "
                        "availability registry, so availability is not "
                        "verified")
    feed_eligibility = feed_doc.get("decision_eligibility") or {}
    if feed_eligibility.get("eligible") is False and \
            feed_eligibility.get("reason"):
        blockers.append("source_feed_decision_eligibility: "
                        + feed_eligibility["reason"])

    return {
        "contract": "evidence-contract",
        "contract_version": "1.0.0",
        "emitter": "Morning Map",
        "clocks": clocks,
        "source_session": source_session,
        "computed_at": computed_at,
        "published_at": clocks["publishedAt"],
        "data_as_of": data_as_of,
        "grading_horizon": grading_horizon,
        "constituent_readings": constituents,
        "availability_evidence": "unknown",
        "verified_availability_refs": VERIFIED_AVAILABILITY_REFS,
        "freshness": {"state": "fresh" if fresh else "stale",
                      "detail": fresh_detail},
        "decision_eligibility": {
            "eligible": not blockers,
            "rule": "fail-closed: eligible only if every required "
                    "field is present and fresh and a verified "
                    "availability reference exists",
            "blockers": blockers,
        },
    }


def build():
    if not os.path.exists(MAP_CARD_PATH):
        print(f"Morning Map refresh: source not found: {MAP_CARD_PATH}",
              file=sys.stderr)
        return 1

    card_doc = load_json(MAP_CARD_PATH)
    built_utc = card_doc.get("built_utc")
    cards = {c.get("underlying"): c for c in card_doc.get("cards", [])}

    feed_doc = {}
    if os.path.exists(FEED_PATH):
        feed_doc = load_json(FEED_PATH)
    feed_map = {e.get("symbol"): e for e in feed_doc.get("map", [])}
    session = feed_doc.get("as_of_session") or card_doc.get("dix_date")

    # Spot basis cure (MAP-SPOT-BASIS-20261031): the card's spot
    # is a live quote taken at build time (a pre-open build mixes
    # premarket trades for two funds with the prior close for the
    # third), while this record is labelled with the session and
    # a close price basis and its consumers describe the figure
    # as the session close. The published spot for every fund is
    # therefore the session close from the one price panel, the
    # card's own spot is kept beside it as snapshot_spot for
    # provenance, and the flip distance is recomputed from the
    # published spot. A fund whose session close is not on the
    # panel stops the refresh: a mixed-basis record is never
    # published.
    if not session or not os.path.exists(PANEL_PATH):
        print("Morning Map refresh: no session or no price panel "
              "on record; refusing to publish a spot whose basis "
              "cannot be named", file=sys.stderr)
        return 1
    panel = load_json(PANEL_PATH)
    panel_closes = {}
    for symbol in SYMBOLS:
        close = panel_session_close(panel, symbol, session)
        if close is None:
            print(f"Morning Map refresh: the price panel carries "
                  f"no {symbol} close for session {session}; "
                  f"refusing to publish a mixed-basis spot",
                  file=sys.stderr)
            return 1
        panel_closes[symbol] = close

    indexes = []
    for symbol in SYMBOLS:
        card = cards.get(symbol)
        feed_entry = feed_map.get(symbol)

        if card is None and feed_entry is None:
            indexes.append({
                "symbol": symbol,
                "state": "no_data",
                "reason": "No map was published for this index in the "
                          "latest data.",
            })
            continue

        # Prefer the full-precision map card; fall back to the feed entry.
        snapshot_spot = (card or {}).get(
            "spot", (feed_entry or {}).get("spot"))
        spot = panel_closes[symbol]
        contracts_used = (card or {}).get("contracts_used")
        chain_total = (card or {}).get("chain_total")
        if contracts_used is None and feed_entry and feed_entry.get("coverage"):
            used, _, total = feed_entry["coverage"].partition("/")
            contracts_used, chain_total = int(used), int(total)
        coverage_text = None
        if contracts_used is not None and chain_total is not None:
            coverage_text = f"{contracts_used:,} of {chain_total:,} contracts counted"

        gex_receipt = {
            "source": "Options open interest (Alpaca) with the published "
                      "gamma exposure formula; modelled from dealer "
                      "positioning, not directly observed",
            "as_of": built_utc,
            "session": session,
            "coverage": coverage_text,
        }
        dix_receipt = {
            "source": "FINRA dark pool (OTC) file, published DIX construction",
            "as_of": built_utc,
            "session": (card or {}).get("dix_date") or session,
            "coverage": None,
        }

        net_gex = (card or {}).get("net_gex_usd_per_1pct")
        if net_gex is None and feed_entry and feed_entry.get("net_gex_b") is not None:
            net_gex = feed_entry["net_gex_b"] * 1_000_000_000
        positioning = figure(net_gex, gex_receipt,
                             "The positioning total was not in the latest "
                             "published data.")
        if positioning["state"] == "ok":
            positioning["mode"] = ("amplifying" if net_gex < 0 else
                                   "dampening" if net_gex > 0 else "flat")

        flip_value = (card or {}).get("zero_gamma",
                                      (feed_entry or {}).get("flip"))
        flip = figure(flip_value, gex_receipt,
                      "The flip level was not in the latest published data.")
        if flip["state"] == "ok":
            # Distance is always recomputed from the published
            # (panel close) spot: the card's own distance was
            # measured from its build-time snapshot spot.
            dist = (flip_value - spot) / spot * 100.0
            flip["distance_pct"] = round(dist, 2)
            if spot is not None:
                flip["side"] = ("above" if flip_value >= spot else "below")

        dix_ratio = (card or {}).get("dix_ratio",
                                     (feed_entry or {}).get("dix"))
        dark_etf = figure(
            None if dix_ratio is None else round(dix_ratio * 100, 1),
            dix_receipt,
            "The dark pool reading was not in the latest published data.")

        dix_index = (card or {}).get("dix_index") or \
            (feed_entry or {}).get("dix_index")
        if not dix_index or is_missing(dix_index.get("value")) or \
                dix_index.get("state") == "no_data":
            dark_constituents = {
                "state": "no_data",
                "value": None,
                "reason": "The combined reading across the stocks inside "
                          "this index is only calculated for SPY right "
                          "now, so there is no figure to show here yet.",
            }
        else:
            used = dix_index.get("constituents_used")
            total = dix_index.get("constituents_total")
            dark_constituents = {
                "state": "ok",
                "value": round(dix_index["value"] * 100, 1),
                "receipt": {
                    "source": "FINRA dark pool (OTC) file for each stock in "
                              "the index, combined into one weighted average",
                    "as_of": built_utc,
                    "session": dix_index.get("date") or session,
                    "coverage": (f"{used:,} of {total:,} stocks counted"
                                 if used is not None and total is not None
                                 else None),
                },
            }

        indexes.append({
            "symbol": symbol,
            "state": "ok",
            "spot": spot,
            "spot_basis": SPOT_BASIS_WORDS,
            "snapshot_spot": snapshot_spot,
            "positioning": positioning,
            "call_wall": figure((card or {}).get("call_wall",
                                (feed_entry or {}).get("call_wall")),
                                gex_receipt,
                                "The call wall was not in the latest "
                                "published data."),
            "put_wall": figure((card or {}).get("put_wall",
                               (feed_entry or {}).get("put_wall")),
                               gex_receipt,
                               "The put wall was not in the latest "
                               "published data."),
            "flip": flip,
            "dark_pool_etf": dark_etf,
            "dark_pool_constituents": dark_constituents,
        })

    data = {
        "tool": "Morning Map",
        "generated_at_utc": built_utc,
        "feed_generated_at_utc": feed_doc.get("generated_at_utc"),
        "session": session,
        "source": "Morning map published from the options chain and the "
                  "FINRA dark pool file",
        "indexes": indexes,
        "contract": build_contract(card_doc, feed_doc, session, built_utc,
                                   indexes),
    }

    # Session keeping (2026-10-31, Wave 3 Item F): past maps were
    # not kept, so the record chart had nothing to draw. From this
    # run forward, each refresh appends a dated snapshot of the
    # charted subject values (each index's spot, put wall, flip
    # and call wall) to the page's session-history store and
    # carries the kept list on the page data. Nothing before this
    # run is reconstructed.
    if _sh is not None:
        data["session_history"] = _sh.append_session(
            HISTORY_PATH, session,
            [{"symbol": ix.get("symbol"), "spot": ix.get("spot"),
              "put_wall": (ix.get("put_wall") or {}).get("value"),
              "flip": (ix.get("flip") or {}).get("value"),
              "call_wall": (ix.get("call_wall") or {}).get("value")}
             for ix in indexes])

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {session}, built {built_utc})")
    return 0


def main():
    rc = build()
    if rc != 0:
        return rc
    # Chain cure (MAP-LADDER-CHAIN-20261031): the Gamma Ladder
    # reads this record as its named source, and Static GEX
    # republishes the ladder figures as its modelled comparison
    # leg. Every republication of this record therefore re-runs
    # the ladder, then Static GEX, in the same process, so a
    # standalone rebuild of this page can never again leave the
    # ladder (and, through it, Static GEX) standing on a
    # superseded session (the ladder also runs in its normal
    # slot in the tools chain). A chained failure fails this
    # refresh loudly rather than leaving the chain out of sync.
    import subprocess
    for script, label in (
            ("refresh_gammaladder.py", "Gamma Ladder"),
            ("refresh_staticgex.py", "Static GEX")):
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, script)],
            capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stderr or r.stdout or "").strip().splitlines()
            print(f"Morning Map refresh: chained {label} re-run "
                  "failed"
                  + (f": {tail[-1]}" if tail else ""),
                  file=sys.stderr)
            return 1
        print(f"Morning Map refresh: {label} re-run chained to "
              "this republication succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
