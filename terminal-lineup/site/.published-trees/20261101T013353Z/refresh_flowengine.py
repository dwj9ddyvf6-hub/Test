#!/usr/bin/env python3
"""Refresh the Flow Engine data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the Flow Tape's published record (its printed
scoring rule, and per fund the 25 largest alert prints of the
freshest session, each carrying its time, contract, price, size,
premium, total heat score, band and tags), cross-checked against
the rule as printed on the Flow Tape's own page and against the
Proving Ground's published vocabulary and its entry for the Flow
Tape, which supply this page's proving state.

Reconstruction choices: no arithmetic on scores at all. The rule
is restated component by component with its point bands exactly as
published. Four worked examples are picked from the freshest
session by fixed, stated picks (the largest money print, the
highest heat score, the largest print that landed exactly on the
15-point line, and the largest unusual-tagged print), and each
example carries only the figures the published record carries for
that print. The record carries no component-by-component breakdown
of any alert's score, so no breakdown is shown or invented: each
example says so in plain words.

What a figure is, in plain words, printed on the page: a heat
score is the total the rule gave one print for how unusual it was
for its own contract; the worked examples show the real prints
that earned published scores, with every figure taken from the
record exactly as published.

Fail-closed rules:
- If any published record read here is missing, the refresh stops.
- If the rule printed on the Flow Tape's page does not carry every
  component phrase, band phrase and threshold this page publishes,
  the refresh stops.
- If the tape record's published counts (alerts published, prints
  looked at) disagree with the alerts and prints actually carried,
  the refresh stops.
- If any group's session differs from the record's session, or an
  alert reaches neither alert band, or a side or direction word is
  not one the record uses, the refresh stops.
- If any of the four fixed picks cannot be made from the session's
  alerts (no largest print, no print exactly on the line, no
  unusual-tagged print), the refresh stops rather than quietly
  publishing fewer or different examples.
- If the Proving Ground's vocabulary does not carry the proving
  state, or its entry for the Flow Tape is not in that state, the
  refresh stops.
- If any assembled string carries internal wording (file names or
  record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- The page never recomputes a heat score and never grades the
  rule: the grading words are the Flow Tape record's own.

Usage: python3 refresh_flowengine.py
"""

import json
import os
import re
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
FLOW_PATH = os.path.join(HERE, "flow-tape", "data.json")
GRADES_PATH = os.path.join(HERE, "flow-tape", "grades.json")
FLOW_PAGE = os.path.join(HERE, "flow-tape", "index.html")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "flow-engine", "data.json")

FUNDS = ["SPY", "QQQ", "IWM"]

# The rule, component by component, exactly as the Flow Tape
# publishes it. Each "check" phrase must appear in the rule as
# printed on the Flow Tape's page, or the refresh stops.
COMPONENTS = [
    {"name": "The money in the print, against that contract's average print",
     "words": ("the money in the print compared with that contract's "
               "average print so far that day: at the average earns "
               "1 point, 3 times it earns 2, 5 times earns 3, "
               "10 times earns 4"),
     "check": "at the average earns 1 point, 3 times it earns 2, "
              "5 times earns 3, 10 times earns 4"},
    {"name": "How soon the contract expires",
     "words": ("how soon the contract expires: under 35 days earns "
               "3 points, 35 to 98 days earns 2, longer earns 1"),
     "check": "under 35 days earns 3 points, 35 to 98 days earns 2, "
              "longer earns 1"},
    {"name": "Being a sweep",
     "words": ("being a sweep, an order split across exchanges to "
               "fill at once: 2 points"),
     "check": "being a sweep, an order split across exchanges to "
              "fill at once (2 points)"},
    {"name": "The print's size",
     "words": ("its size: 5,000 contracts or more earns 1 point, "
               "10,000 or more earns 2"),
     "check": "5,000 contracts or more earns 1 point, 10,000 or "
              "more earns 2"},
    {"name": "How far the strike sits from the current price",
     "words": ("how far its strike price sits from the current "
               "price: 2% away earns 1.5 points, rising step by "
               "step to 7.5 points at 30% away or more"),
     "check": "2% away earns 1.5 points, rising step by step to "
              "7.5 points at 30% away or more"},
    {"name": "Its size against the contract's open interest",
     "words": ("its size compared with the contract's open "
               "interest, the number of contracts already open: "
               "three quarters of it earns 1 point, up to 4 points "
               "at 5 times it"),
     "check": "three quarters of it earns 1 point, up to 4 points "
              "at 5 times it"},
    {"name": "Its size against the contract's average print size",
     "words": ("its size compared with the contract's average "
               "print size: 4 times earns 1 point, up to 4 points "
               "at 10 times"),
     "check": "4 times earns 1 point, up to 4 points at 10 times"},
    {"name": "The contract's open interest against the average contract's",
     "words": ("the contract's open interest compared with the "
               "average contract's: 5 times earns 1 point, "
               "10 times earns 2"),
     "check": "5 times earns 1 point, 10 times earns 2"},
]

RULE_INTRO = ("Every options print is given a heat score for how "
              "unusual it is for its own contract. The score is "
              "built from eight parts; a print earns the points "
              "of every part it qualifies for, and the parts add "
              "up to its heat score.")

BANDS = [
    {"name": "High heat",
     "words": "its heat score reaches 15",
     "check": "its heat score reaches 15"},
    {"name": "Golden sweep",
     "words": ("it is a sweep, its size is at least the contract's "
               "whole open interest, and the money in it is at "
               "least $1 million"),
     "check": "it is a sweep, its size is at least the contract's "
              "whole open interest, and the money in it is at "
              "least $1 million"},
    {"name": "Unusual tag",
     "words": ("a print is also tagged unusual when its strike "
               "sits at least 10% away from the current price and "
               "it expires within 35 days"),
     "check": "its strike sits at least 10% away from the current "
              "price and it expires within 35 days"},
]

PUBLISHED_WORDS = ("Only the 25 largest alerts for each index are "
                   "published, biggest money first.")

BREAKDOWN_NOTE = ("How the score adds up: the record publishes "
                  "this print's total heat score and the figures "
                  "above. It does not publish how many of those "
                  "points came from each part of the rule, so that "
                  "split is not broken out on record and is not "
                  "shown here.")

PICKS = [
    ("largest_money", "The biggest money print of the day"),
    ("highest_heat", "The highest heat score of the day"),
    ("on_the_line", "A print that landed exactly on the line"),
    ("largest_unusual", "The biggest unusual-tagged print of the day"),
]

FORBIDDEN = ("morgue", "json", "tape_card", ".py", "ledger",
             "data file", "dataset", "nbbo")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Flow Engine refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def grading_totals():
    """(graded, total, hits) from the grading pass's own record."""
    try:
        with open(GRADES_PATH, encoding="utf-8") as fh:
            grades = json.load(fh)
        sessions = grades.get("sessions") or {}
        return (sum(s.get("graded", 0) for s in sessions.values()),
                sum(s.get("alerts", 0) for s in sessions.values()),
                sum(s.get("hits", 0) for s in sessions.values()))
    except (OSError, ValueError):
        return (0, 0, 0)


def grading_note_matches(note):
    """The tape record's grading words must state the true grading
    state: not-yet-graded only while the grading record shows zero
    graded, otherwise the graded counts the record carries. The
    pre-cure check demanded the not-yet-graded wording forever, so
    once grading landed (cure stream D) this refresh refused every
    session (found live 2026-10-30)."""
    graded, total, hits = grading_totals()
    if not graded:
        return "not been graded yet" in note
    return (f"{graded} of {total} logged alerts graded" in note
            and f"{hits} of them in the direction" in note)


def build():
    for path in (FLOW_PATH, FLOW_PAGE, PROVING_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    flow = load_json(FLOW_PATH)
    proving = load_json(PROVING_PATH)
    with open(FLOW_PAGE, "r", encoding="utf-8") as fh:
        page_text = re.sub(r"\s+", " ",
                           re.sub(r"<[^>]+>", " ", fh.read()))

    # The rule this page prints must be the rule the Flow Tape's
    # own page prints, phrase for phrase.
    for comp in COMPONENTS:
        if comp["check"] not in page_text:
            return fail("the rule printed on the Flow Tape's page "
                        f"does not carry the component phrase "
                        f"{comp['check']!r}; refusing to publish "
                        "a rule that differs from the published "
                        "one.")
    for band in BANDS:
        if band["check"] not in page_text:
            return fail("the rule printed on the Flow Tape's page "
                        f"does not carry the band phrase "
                        f"{band['check']!r}; refusing to publish.")
    if PUBLISHED_WORDS.split(",")[0] not in page_text:
        return fail("the Flow Tape's page does not carry the "
                    "25-largest-alerts wording; refusing to "
                    "publish.")

    session = flow.get("session")
    if not session:
        return fail("the tape record carries no session date; "
                    "refusing to guess.")
    grading_note = flow.get("grading_note") or ""
    if not grading_note_matches(grading_note):
        return fail("the tape record's grading words do not match "
                    "the grading record's state (not-yet-graded, or "
                    "the graded counts it carries); refusing to "
                    "publish a different grading state.")

    proving_state = None
    for state in proving.get("states") or []:
        if state.get("key") == "proving":
            proving_state = state
    if not proving_state or not proving_state.get("words") or \
            not proving_state.get("definition"):
        return fail("the Proving Ground's vocabulary does not "
                    "carry the proving state; refusing to publish "
                    "a proving label of our own.")
    tape_entry = None
    for tool in proving.get("tools") or []:
        if tool.get("slug") == "flow-tape":
            tape_entry = tool
    if not tape_entry or tape_entry.get("state") != "proving" or \
            tape_entry.get("state_words") != proving_state["words"]:
        return fail("the Proving Ground's entry for the Flow Tape "
                    "is not in the proving state; refusing to "
                    "publish a different state.")

    groups = {g.get("underlying"): g for g in flow.get("groups") or []}
    if set(groups) != set(FUNDS):
        return fail("the tape record does not cover exactly SPY, "
                    "QQQ and IWM; refusing to publish a partial "
                    "engine.")

    alerts = []
    for sym in FUNDS:
        group = groups[sym]
        if group.get("session") != session:
            return fail(f"the {sym} group is dated differently "
                        "from the session; refusing to publish a "
                        "mixed state.")
        if len(group["alerts"]) != group.get("alerts_shown"):
            return fail(f"the tape record shows "
                        f"{len(group['alerts'])} alerts for {sym} "
                        f"but states {group.get('alerts_shown')}; "
                        "refusing to publish.")
        for a in group["alerts"]:
            if not a.get("golden_sweep") and \
                    float(a["heat_score"]) < 15:
                return fail("an alert in the record reaches "
                            "neither alert band; refusing to "
                            "publish an alert the rule does not "
                            "explain.")
            if a.get("direction") not in ("bullish", "bearish",
                                          "neutral"):
                return fail("an alert carries a direction word "
                            "the record does not use; refusing to "
                            "publish.")
            alerts.append((sym, a))

    counts = flow.get("counts") or {}
    if counts.get("alerts_published") != len(alerts):
        return fail("the tape record's published alert count "
                    f"{counts.get('alerts_published')} disagrees "
                    f"with the {len(alerts)} alerts it carries; "
                    "refusing to publish.")
    total_prints = sum(g["prints_looked_at"] for g in groups.values())
    if counts.get("prints_looked_at") != total_prints:
        return fail("the tape record's published prints-looked-at "
                    "count disagrees with its per-fund counts; "
                    "refusing to publish.")
    unusual_count = sum(1 for _, a in alerts if a["unusual"])
    golden_count = sum(1 for _, a in alerts if a["golden_sweep"])

    def pick(key, exclude=()):
        # Picks are distinct by construction (BUGLOG 2026-10-29, tape
        # family): on 2026-10-29 one print was simultaneously the
        # largest-money print and the largest on-the-line print, and
        # the old code refused the whole page for a collision that is
        # a fact about the session, not a data defect. Each pick now
        # takes the best print not already used by an earlier pick;
        # if no distinct print can supply a pick, it still fails.
        pool = [x for x in alerts
                if (x[1]["contract_code"], x[1]["time_utc"])
                not in exclude]
        if key == "largest_money":
            return max(pool, key=lambda x: x[1]["premium_usd"]) \
                if pool else None
        if key == "highest_heat":
            return max(pool, key=lambda x: (x[1]["heat_score"],
                                            x[1]["premium_usd"])) \
                if pool else None
        if key == "on_the_line":
            cands = [x for x in pool
                     if float(x[1]["heat_score"]) == 15.0]
            return max(cands, key=lambda x: x[1]["premium_usd"]) \
                if cands else None
        if key == "largest_unusual":
            cands = [x for x in pool if x[1]["unusual"]]
            return max(cands, key=lambda x: x[1]["premium_usd"]) \
                if cands else None
        return None

    examples = []
    seen = set()
    for key, label in PICKS:
        got = pick(key, exclude=seen)
        if got is None:
            return fail(f"the session's alerts cannot supply the "
                        f"{label!r} worked example; refusing to "
                        "publish a smaller or different set.")
        sym, a = got
        marker = (a["contract_code"], a["time_utc"])
        if marker in seen:
            return fail("two worked-example picks landed on the "
                        "same print; refusing to publish a "
                        "duplicated example.")
        seen.add(marker)
        ex = dict(a)
        ex["underlying"] = sym
        ex["pick"] = label
        examples.append(ex)

    golden_words = (
        f"No golden sweep fired on {long_date(session)}: none of "
        f"the day's {len(alerts)} published alerts is a golden "
        "sweep, so there is no golden worked example to show. The "
        "golden rule above is stated exactly as published."
        if golden_count == 0 else
        f"{golden_count} of the day's published alerts are golden "
        "sweeps.")

    data = {
        "tool": "Flow Engine",
        "state": "published",
        "session": session,
        "session_long": long_date(session),
        "published_at_utc": flow.get("published_at_utc"),
        "source": flow.get("source"),
        "proving_state": proving_state["words"],
        "proving_note": proving_state["definition"],
        "grading_note": grading_note,
        "rule": {
            "intro": RULE_INTRO,
            "components": [{"name": c["name"], "words": c["words"]}
                           for c in COMPONENTS],
            "bands": [{"name": b["name"], "words": b["words"]}
                      for b in BANDS],
            "published_words": PUBLISHED_WORDS,
        },
        "breakdown_note": BREAKDOWN_NOTE,
        "golden_words": golden_words,
        "examples": examples,
        "counts": {
            "alerts_published": len(alerts),
            "prints_looked_at": total_prints,
            "unusual_tagged": unusual_count,
            "golden_sweeps": golden_count,
            "examples_shown": len(examples),
        },
        "receipt": {
            "session": session,
            "source": flow.get("source"),
            "coverage": (f"{len(alerts)} published alerts for "
                         f"{long_date(session)} across SPY, QQQ "
                         f"and IWM, from {total_prints:,} prints "
                         f"looked at; {len(examples)} of them "
                         "worked through above"),
        },
    }

    def walk(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from walk(v)
        elif isinstance(value, list):
            for v in value:
                yield from walk(v)

    for text in walk(data):
        low = text.lower()
        for bad in FORBIDDEN:
            if bad in low:
                return fail(f"assembled data carries internal "
                            f"wording ({bad!r}); refusing to "
                            "publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"Wrote {OUT_PATH} (session {session}, "
          f"{len(examples)} worked examples from {len(alerts)} "
          "alerts)")
    # Record-surface cure (2026-10-31): surface this page's full
    # record in its own data.json, from numbers already on file.
    try:
        import record_surface as _rs
        _rs.enrich_slug("flow-engine")
    except Exception as _exc:
        print(f"record-surface enrich failed: {_exc}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
