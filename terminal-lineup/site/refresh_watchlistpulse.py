#!/usr/bin/env python3
"""Refresh the Watchlist Pulse data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the Second Opinion's published per-name record: for
each of the 1,838 names on record, how many of the six evidence
families speak for it, the plain direction each family that carries
one points (positive, mixed or cautious), the price family's score,
checks and closing price, the options prints and modelled
positioning readings for the three index funds, and the filings
lines for the names that carry them, all stamped with the scored
trading day behind the record and the older date on the filings
lines. This tool publishes a slim copy of that record only; it
adds no record of its own.

Reconstruction choices, stated as ours: (1) A pulse line is one
name at a glance: the count of speaking families out of six, what
each speaking family says in the record's own plain words, and the
session behind the record. The deep per-family tables of the
Second Opinion page are not repeated here. (2) The filings family
speaks in facts, not a direction, exactly as the source record
states it, and is never counted in any agreement count. (3) The
reader's own list of names is not part of this data file at all:
it lives only in the reader's browser, on their own machine, and
is never sent anywhere; this refresh neither reads nor writes it.
(4) A name the reader adds that is not among the names on record
is handled on the page with a plain not-on-record line; no entry
is invented for it here.

Fail-closed rules: if the source record is not in its published
state, if its name count disagrees with the coverage counts it
publishes for itself, if the census of names by how many families
speak (none, one, two, three) recomputed from its own rows
disagrees with the coverage it publishes, if the scored and
too-little-data counts disagree, if any name's speaking count does
not match the families actually present in its row, if any name's
direction list does not match the families that carry a direction,
if a direction word is outside the record's own three plain words,
if the six families are not the six the source record names, or
if the record carries no session date, the refresh stops and
publishes nothing. All dates and times come from the source
record, never the clock, so running this script twice produces
the same file.

Usage: python3 refresh_watchlistpulse.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_PATH = os.path.join(HERE, "second-opinion", "data.json")
OUT_PATH = os.path.join(HERE, "watchlist-pulse", "data.json")

EXPECTED_FAMILIES = [
    ("price", "Price and trading history"),
    ("prints", "Options prints"),
    ("positioning", "Modelled options positioning"),
    ("filings", "Filings and positioning"),
    ("facts", "Company facts"),
    ("news", "News and events"),
]
DIRECTIONAL = ("price", "prints", "positioning")
# All six families the producer counts as speaking (hookup cure,
# 2026-10-30: this set predated the facts and news families
# landing in the Second Opinion record, so the count check below
# demanded a four-family count against the producer's six-family
# count and refused every coherent run once those families spoke).
PRESENTABLE = ("price", "prints", "positioning", "filings",
               "facts", "news")
STANCES = ("positive", "mixed", "cautious")


def fail(message):
    print(f"Watchlist Pulse refresh: {message}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build():
    if not os.path.exists(SOURCE_PATH):
        return fail("the source record is not on file; refusing "
                    "to publish.")
    src = load_json(SOURCE_PATH)

    if src.get("state") != "published":
        return fail("the source record is not in its published "
                    "state; refusing to publish.")
    if src.get("tool") != "The Second Opinion":
        return fail("the source record does not name itself as "
                    "expected; refusing to publish.")
    session = src.get("session")
    if not session:
        return fail("the source record carries no session date; "
                    "refusing to publish.")
    families = [(f.get("id"), f.get("name"))
                for f in src.get("families") or []]
    if families != EXPECTED_FAMILIES:
        return fail("the source record's families are not the six "
                    "it is expected to name; refusing to publish.")

    names = src.get("names") or []
    cov = src.get("coverage") or {}
    if len(names) != cov.get("names_on_record"):
        return fail("the source record's name count disagrees "
                    "with the coverage it publishes for itself; "
                    "refusing to publish.")
    symbols = [n.get("symbol") for n in names]
    if any(not s for s in symbols) or len(set(symbols)) != len(symbols):
        return fail("the source record carries a missing or "
                    "repeated name; refusing to publish.")

    census = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    scored = 0
    filings_names = 0
    out_names = []
    for n in names:
        present = [k for k in PRESENTABLE if n.get(k)]
        if n.get("families_speaking") != len(present):
            return fail(f"{n['symbol']}: the speaking count does "
                        "not match the families present in its "
                        "row; refusing to publish.")
        if n["families_speaking"] not in census:
            return fail(f"{n['symbol']}: more families speak than "
                        "the record's own census allows; refusing "
                        "to publish.")
        census[n["families_speaking"]] += 1
        # A family can speak without carrying a direction word
        # (the producer's prints entries carry stance None when
        # they speak without a direction); the producer's own
        # directional list appends only present stances, and this
        # recomputation must match that construction.
        directional = [n[k]["stance"] for k in DIRECTIONAL
                       if n.get(k) and n[k].get("stance")]
        if n.get("directional") != directional:
            return fail(f"{n['symbol']}: the direction list does "
                        "not match the families that carry a "
                        "direction; refusing to publish.")
        for stance in directional:
            if stance not in STANCES:
                return fail(f"{n['symbol']}: a direction word is "
                            "outside the record's own plain "
                            "words; refusing to publish.")
        if n.get("price"):
            scored += 1
            p = n["price"]
            for key in ("close", "score", "confirming",
                        "checks_total", "qualified", "stance"):
                if key not in p:
                    return fail(f"{n['symbol']}: the price record "
                                f"is missing {key}; refusing to "
                                "publish.")
        if n.get("filings"):
            filings_names += 1

        entry = {
            "symbol": n["symbol"],
            "families_speaking": n["families_speaking"],
            "directional": directional,
            "price": None,
            "prints": None,
            "positioning": None,
            "filings": None,
            "facts": None,
            "news": None,
        }
        if n.get("price"):
            p = n["price"]
            entry["price"] = {
                "close": p["close"],
                "score": p["score"],
                "confirming": p["confirming"],
                "checks_total": p["checks_total"],
                "qualified": p["qualified"],
                "stance": p["stance"],
            }
        else:
            entry["price_silent_reason"] = n.get(
                "price_silent_reason",
                "No scored record is on file for this name.")
        if n.get("prints"):
            t = n["prints"]
            entry["prints"] = {
                "prints": t["prints"],
                "total_premium": t["total_premium"],
                "net_premium": t["net_premium"],
                "stance": t["stance"],
            }
        if n.get("positioning"):
            g = n["positioning"]
            entry["positioning"] = {
                "spot": g["spot"],
                "flip": g["flip"],
                "below_flip": g["below_flip"],
                "stance": g["stance"],
            }
        if n.get("filings"):
            f = n["filings"]
            entry["filings"] = {
                "readings": f.get("readings") or {},
                "insider_transactions": f.get(
                    "insider_transactions"),
                "insider_latest": f.get("insider_latest"),
                "si_pct": f.get("si_pct"),
                "days_to_cover": f.get("days_to_cover"),
                "si_settlement": f.get("si_settlement"),
            }
        if n.get("facts"):
            entry["facts"] = n["facts"]
        if n.get("news"):
            entry["news"] = n["news"]
        out_names.append(entry)

    if census[0] != cov.get("no_family") or \
            census[1] != cov.get("one_family") or \
            census[2] != cov.get("two_families") or \
            census[3] != cov.get("three_families") or \
            census[4] != cov.get("four_families") or \
            census[5] != cov.get("five_families") or \
            census[6] != cov.get("six_families"):
        return fail("the census recomputed from the source "
                    "record's own rows disagrees with the "
                    "coverage it publishes; refusing to publish.")
    if scored != cov.get("scored"):
        return fail("the scored count recomputed from the source "
                    "record disagrees with the coverage it "
                    "publishes; refusing to publish.")
    if census[0] != cov.get("too_little_data"):
        return fail("the too-little-data count recomputed from "
                    "the source record disagrees with the "
                    "coverage it publishes; refusing to publish.")
    # No cross-record filings equality is demanded: the
    # producer's filings_names_on_file counts the gathering
    # record's names (50), not the names whose assembled rows
    # carry a filings line (38), and the old identity this check
    # replaced (filings names equal the two-family count) died
    # with the four-family record. filings_names is published
    # below as computed from the rows themselves, whose speaking
    # counts were each verified against their present families
    # above and whose census ties to the published coverage.

    out = {
        "tool": "Watchlist Pulse",
        "state": "published",
        "session": session,
        "filings_as_of": src.get("filings_as_of"),
        "source": src.get("source"),
        "board_published_at_utc": src.get(
            "board_published_at_utc"),
        "families": [{"id": fid, "name": name}
                     for fid, name in EXPECTED_FAMILIES],
        "families_total": len(EXPECTED_FAMILIES),
        "coverage": {
            "names_on_record": len(out_names),
            "no_family": census[0],
            "one_family": census[1],
            "two_families": census[2],
            "three_families": census[3],
            "four_families": census[4],
            "five_families": census[5],
            "six_families": census[6],
            "filings_names": filings_names,
        },
        "examples": [s for s in ("SPY", "QQQ", "AAPL")
                     if s in set(symbols)],
        "names": out_names,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"Watchlist Pulse refresh: published {len(out_names)} "
          f"names for session {session}.")
    return 0


if __name__ == "__main__":
    sys.exit(build())
