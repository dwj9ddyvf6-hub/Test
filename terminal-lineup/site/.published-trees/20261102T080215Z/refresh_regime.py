#!/usr/bin/env python3
"""Refresh the Regime Dial data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the other tools' own published data files on this
site, read read-only: the breadth counts (share of stocks above
their 50-session and 200-session averages, and how many rose or
fell), the sector ranking (average price change over 21 sessions),
the morning index map (the big S&P 500 fund's price against its
flip level), and the expected-move record (the fear gauge close it
carries). Every figure on the dial must match its source tool's
published figure exactly, or this refresh stops and publishes
nothing.

The fixed rule (stated here before any build, and printed on the
page in plain words before its result; it may not be tuned to
today's answer): six checks.
  1. Long trend: the share of stocks above their 200-session
     average, against half.
  2. Short trend: the share above their 50-session average,
     against half.
  3. Day direction: how many stocks rose against how many fell.
  4. Leadership: the top three sectors over 21 sessions. Defensive
     sectors are Utilities, Consumer Staples and Health Care;
     growth sectors are Information Technology, Consumer
     Discretionary and Communication Services. The check points
     defensive-led when the top three hold more defensive than
     growth sectors, growth-led when they hold more growth than
     defensive, and neither otherwise.
  5. Position: the big S&P 500 fund's price above or below its
     flip level.
  6. Fear: the fear gauge close; under 20 is calm, 20 to under 25
     is uneasy, 25 or more is stressed. (20 and 25 are the Fear
     Day List's own published levels.)
Sessions and staleness: each check carries its own session, read
from its source. A check more than 2 trading sessions (weekdays,
not counting weekends) behind the freshest check's session is
shown with its figure but does not count toward the reading. If
fewer than 4 of the 6 checks count, no single reading is
published: the page shows the checks and says so.
The kinds, in the order they are tried:
  - Stressed: a counting fear check at 25 or more, whatever the
    rest say.
  - Trending up: both counting trend checks above half and the
    counting position check above the flip.
  - Trending down: both counting trend checks below half and the
    counting position check below the flip.
  - Range-bound: a counting fear check under 20, neither trending
    condition met, and the day check not strongly one-sided
    (strongly one-sided means more than two thirds of the stocks
    that traded moved the same way).
  - Mixed / no clear reading: anything else, including a trending
    condition whose checks do not all count.
Measurement vs interpretation: the six checks are measurements,
each shown with its figure and its session. The one-sentence
reading is an interpretation built from them by the rule above,
and it is labelled as the dial's reading everywhere it appears.
The dial describes what kind of market this is; it never
forecasts.

Fail-closed rules: a source file missing or unreadable; a figure
missing from its source; a breadth percentage that does not match
its own counts; a sector list whose top three over 21 sessions
cannot be read; a fund price or flip level missing; a fear gauge
close missing from the expected-move record. Any of these stops
the refresh and publishes nothing. Dates are read off the
sources, never from the clock, so running this script twice on
the same sources produces the same file, byte for byte.

Usage: python3 refresh_regime.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
BREADTH_PATH = os.path.join(HERE, "breadth-meter", "data.json")
ROTATION_PATH = os.path.join(HERE, "sector-rotation", "data.json")
MAP_PATH = os.path.join(HERE, "morning-map", "data.json")
EXPECTED_PATH = os.path.join(HERE, "expected-move", "data.json")
OUT_PATH = os.path.join(HERE, "regime-dial", "data.json")

DEFENSIVE = {"Utilities", "Consumer Staples", "Health Care"}
GROWTH = {"Information Technology", "Consumer Discretionary",
          "Communication Services"}
STALE_AFTER = 2
MIN_COUNTING = 4

SOURCE_WORDS = ("The published figures of the other tools on this "
                "site: the breadth counts, the sector ranking, "
                "the morning index map and the expected-move "
                "record, each read exactly as published there")

RULE_LINES = [
    "A check more than 2 trading sessions behind the freshest "
    "check is shown with its figure but does not count toward "
    "the reading. If fewer than 4 of the 6 checks count, no "
    "single reading is published.",
    "Stressed: a counting fear check at 25 or more, whatever "
    "the rest say.",
    "Trending up: both trend checks above half, and the S&P 500 "
    "fund above its flip level, with all three checks counting.",
    "Trending down: both trend checks below half, and the S&P "
    "500 fund below its flip level, with all three checks "
    "counting.",
    "Range-bound: a counting fear check under 20, neither "
    "trending reading met, and the day's moves not strongly "
    "one-sided (more than two thirds of stocks moving the same "
    "way would be strongly one-sided).",
    "Anything else reads as mixed: no clear reading.",
]


def fail(message):
    print(f"Regime Dial refresh: {message}", file=sys.stderr)
    return None


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sessions_behind(earlier, later):
    """Trading sessions (weekdays) from earlier up to later."""
    d0 = date.fromisoformat(earlier)
    d1 = date.fromisoformat(later)
    n = 0
    d = d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def build():
    for path in (BREADTH_PATH, ROTATION_PATH, MAP_PATH,
                 EXPECTED_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    try:
        breadth = load_json(BREADTH_PATH)
        rotation = load_json(ROTATION_PATH)
        morning = load_json(MAP_PATH)
        expected = load_json(EXPECTED_PATH)
    except (OSError, ValueError) as exc:
        return fail(f"a source file could not be read: {exc}")

    head = breadth.get("headline") or {}
    b_session = head.get("session")
    try:
        a200 = head["above_200_pct"]; a50 = head["above_50_pct"]
        n200 = head["above_200"]; c200 = head["counted_200"]
        n50 = head["above_50"]; c50 = head["counted_50"]
        adv = head["advancers"]; dec = head["decliners"]
        unc = head["unchanged"]; traded = head["traded"]
        adv_pct = head["advancers_pct"]
    except KeyError as exc:
        return fail(f"the breadth record is missing {exc}")
    if not b_session:
        return fail("the breadth record carries no session")
    if round(100.0 * n200 / c200, 1) != a200:
        return fail("the breadth long-trend percentage disagrees "
                    "with its own counts")
    if round(100.0 * n50 / c50, 1) != a50:
        return fail("the breadth short-trend percentage disagrees "
                    "with its own counts")
    if round(100.0 * adv / traded, 1) != adv_pct:
        return fail("the breadth day percentage disagrees with "
                    "its own counts")
    if adv + dec + unc != traded:
        return fail("the breadth day counts do not add up to "
                    "the number traded")

    sectors = [s for s in (rotation.get("sectors") or [])
               if not s.get("thin")]
    top3 = sorted(sectors, key=lambda s: s["rank_21"])[:3]
    if len(top3) < 3:
        return fail("the sector ranking has no top three")
    r_session = rotation.get("history_to")
    if not r_session:
        return fail("the sector ranking carries no last session")
    n_def = sum(1 for s in top3 if s["sector"] in DEFENSIVE)
    n_gro = sum(1 for s in top3 if s["sector"] in GROWTH)
    lead_names = ", ".join(
        f"{s['sector']} {s['avg_change_21_pct']:+.2f}%"
        for s in top3)
    if n_def > n_gro:
        lead_points = "defensive-led"
    elif n_gro > n_def:
        lead_points = "growth-led"
    else:
        lead_points = "neither defensive-led nor growth-led"

    m_session = morning.get("session")
    spy = next((i for i in (morning.get("indexes") or [])
                if i.get("symbol") == "SPY"), None)
    if not spy or not m_session:
        return fail("the morning index map carries no S&P 500 "
                    "fund entry or no session")
    spot = spy.get("spot")
    flip = (spy.get("flip") or {}).get("value")
    if spot is None or flip is None:
        return fail("the morning index map is missing the fund "
                    "price or its flip level")
    below = spot < flip
    dist = round(abs(spot - flip) / spot * 100, 2)
    pos_points = "below its flip level" if below else \
        "above its flip level"

    spy_em = next((n for n in (expected.get("names") or [])
                   if n.get("symbol") == "SPY"
                   and n.get("state") == "ok"), None)
    if not spy_em or spy_em.get("vix_close") is None:
        return fail("the expected-move record carries no fear "
                    "gauge close for the S&P 500 fund")
    fear = spy_em["vix_close"]
    fear_session = spy_em.get("close_date")
    if not fear_session:
        return fail("the expected-move record carries no date "
                    "for its fear gauge close")
    # Chain guard (REGIME-FEAR-CHAIN-20261031): the fear figure
    # is the gauge close the newest expected-move map was
    # measured from, so it must sit exactly one session behind
    # the record's own session (its measured-from close). If it
    # falls further behind, the entry this dial read is no
    # longer the record's newest measurement and the dial would
    # stand on a superseded input: fail closed instead of
    # republishing the stale exclusion.
    em_session = expected.get("session")
    if not em_session:
        return fail("the expected-move record carries no session")
    if sessions_behind(fear_session, em_session) > 1:
        return fail("the fear gauge close read here is from "
                    f"{fear_session}, more than one session "
                    f"behind the expected-move record's session "
                    f"{em_session}; refusing to publish a "
                    "reading on a superseded input")
    if fear >= 25:
        fear_points = "stressed (25 or more)"
    elif fear >= 20:
        fear_points = "uneasy (20 to under 25)"
    else:
        fear_points = "calm (under 20)"

    checks = [
        {"id": "long_trend", "name": "Long trend",
         "figure": f"{a200:.1f}% of stocks above their "
                   f"200-session average",
         "detail": f"{n200:,} of {c200:,} stocks counted",
         "session": b_session,
         "points": "above half" if a200 > 50 else
                   ("below half" if a200 < 50 else "at half"),
         "value": a200},
        {"id": "short_trend", "name": "Short trend",
         "figure": f"{a50:.1f}% of stocks above their "
                   f"50-session average",
         "detail": f"{n50:,} of {c50:,} stocks counted",
         "session": b_session,
         "points": "above half" if a50 > 50 else
                   ("below half" if a50 < 50 else "at half"),
         "value": a50},
        {"id": "day_direction", "name": "Day direction",
         "figure": f"{adv:,} stocks rose, {dec:,} fell, "
                   f"{unc:,} unchanged",
         "detail": f"{adv_pct:.1f}% of the {traded:,} stocks "
                   f"that traded rose",
         "session": b_session,
         "points": "more rose than fell" if adv > dec else
                   ("more fell than rose" if dec > adv else
                    "as many rose as fell"),
         "value": adv_pct},
        {"id": "leadership", "name": "Leadership",
         "figure": "Top three sectors over 21 sessions: "
                   + lead_names,
         "detail": "Ranked by their average price change over "
                   "21 sessions",
         "session": r_session,
         "points": lead_points,
         "value": lead_points},
        {"id": "position", "name": "Position",
         "figure": f"The S&P 500 fund closed at {spot:,.2f} "
                   f"against a flip level of {flip:,.2f}",
         "detail": f"{dist:.2f}% {'below' if below else 'above'} "
                   f"the flip level",
         "session": m_session,
         "points": pos_points,
         "value": "below" if below else "above"},
        {"id": "fear", "name": "Fear",
         "figure": f"Fear gauge closed at {fear:.2f}",
         "detail": "The gauge close the expected-move record "
                   "was measured from",
         "session": fear_session,
         "points": fear_points,
         "value": fear},
    ]

    freshest = max(c["session"] for c in checks)
    for c in checks:
        behind = sessions_behind(c["session"], freshest)
        c["sessions_behind"] = behind
        c["counts"] = behind <= STALE_AFTER
        if not c["counts"]:
            c["points"] += " (shown, but too old to count)"

    counting = {c["id"]: c for c in checks if c["counts"]}
    n_counting = len(counting)
    reading = None
    if n_counting >= MIN_COUNTING:
        fear_c = counting.get("fear")
        lt = counting.get("long_trend")
        st = counting.get("short_trend")
        pos = counting.get("position")
        day = counting.get("day_direction")
        strongly = False
        if day:
            strongly = adv * 3 > traded * 2 or \
                dec * 3 > traded * 2
        if fear_c and fear_c["value"] >= 25:
            kind = "Stressed"
            sentence = ("Stressed: the fear gauge is at 25 or "
                        "more, and that alone sets this reading, "
                        "whatever the other checks say.")
        elif lt and st and pos and lt["value"] > 50 and \
                st["value"] > 50 and pos["value"] == "above":
            kind = "Trending up"
            sentence = ("Trending up: most stocks sit above "
                        "both of their averages, and the S&P 500 "
                        "fund sits above its flip level.")
        elif lt and st and pos and lt["value"] < 50 and \
                st["value"] < 50 and pos["value"] == "below":
            kind = "Trending down"
            sentence = ("Trending down: most stocks sit below "
                        "both of their averages, and the S&P 500 "
                        "fund sits below its flip level.")
        elif fear_c and fear_c["value"] < 20 and not strongly:
            kind = "Range-bound"
            sentence = ("Range-bound: the fear gauge is calm "
                        "and no trending reading is met, so the "
                        "market reads as moving sideways rather "
                        "than in one direction.")
        else:
            kind = "Mixed / no clear reading"
            sentence = ("Mixed: the checks that count do not "
                        "line up behind any single kind of "
                        "market, so the dial publishes no clear "
                        "reading.")
        reading = {"kind": kind, "sentence": sentence}

    return {
        "tool": "Regime Dial",
        "source": SOURCE_WORDS,
        "freshest_session": freshest,
        "counting_checks": n_counting,
        "checks_total": len(checks),
        "rule": RULE_LINES,
        "checks": checks,
        "reading": reading,
        "no_reading_note": None if reading else
            (f"Only {n_counting} of the {len(checks)} checks are "
             f"fresh enough to count, and the rule needs at "
             f"least {MIN_COUNTING}, so no single reading is "
             f"published. The checks themselves are shown "
             f"below, each with its own session."),
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
    kind = doc["reading"]["kind"] if doc["reading"] else \
        "no single reading"
    print(f"Regime Dial refresh: wrote {OUT_PATH} "
          f"({doc['counting_checks']} of {doc['checks_total']} "
          f"checks count; reading: {kind})")
    # Record-surface cure (2026-10-31): surface this page's full
    # record in its own data.json, from numbers already on file.
    try:
        import record_surface as _rs
        _rs.enrich_slug("regime-dial")
    except Exception as _exc:
        print(f"record-surface enrich failed: {_exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
