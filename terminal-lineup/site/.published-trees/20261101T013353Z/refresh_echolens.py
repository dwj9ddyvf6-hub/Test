#!/usr/bin/env python3
"""Refresh the Echo Lens data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (2026-10-28): no disclaimer-style
copy on any reader surface of any tool, in pages or generated data,
ever.

Evidence class: the Second Opinion's published record (six named
families of readings over 1,838 names for the session on record),
cross-checked against the Replication Wire's published gradings and
the Proving Ground's published vocabulary.

Inspect ground truth (2026-10-28, the stop signal this build obeys):
the Second Opinion's record carries exactly six families, and none
of them is the tracked newsletter method this lens belongs to (the
EchoAnalysis method named in the lineup design for tool 69). No
per-name reading from that method exists in that record, or in any
other published record on this site. The Replication Wire carries
no entry for that method either: the only headline figure on its
record ruled an agreement measure rather than a forecast is a
different method's, the chart ranker's 0.736 ranking agreement.
Presenting any of the six families, or that ruling, as this
method's own would invent an attribution the record does not carry.

Reconstruction choices: this page is therefore built as the honest
state of that lens. It names the lens in the design's own public
words (one analyst's published newsletter method), states its true
coverage on its face (0 of the names on record), lists exactly the
names it covers (none), carries a search index of the names on
record so a reader can check any name and be told plainly the lens
has no reading for it, and carries the agreement ruling correctly
attributed to the chart-ranking method it belongs to, with a plain
statement that no headline figure for this newsletter method is on
record as ruled on. Its proving state is the Proving Ground's
waiting state, whose own definition is that a built page shows
nothing, or only its definition, until its records arrive.

Fail-closed rules:
- If any of the three published records read here is missing, the
  refresh stops and publishes nothing.
- If the coverage counts recomputed from the Second Opinion's
  per-name family counts disagree with the coverage counts it
  publishes, the refresh stops.
- If the set of families on the record is no longer exactly the
  six the inspect phase counted, the refresh stops: a new or
  renamed family could be this lens's method, and the zero
  coverage assembled here would need a fresh inspection first.
- If any family on the record names a newsletter method or this
  lens's method, the refresh stops for the same reason.
- If the Replication Wire's record gains any entry naming this
  lens's method, or loses the chart ranker's 0.736 agreement
  claim graded "Did not hold up" with its ruling text, the
  refresh stops.
- If the Proving Ground's vocabulary does not carry the waiting
  state this page labels itself with, the refresh stops.
- If any assembled string carries internal wording (file names
  or record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- No other family's reading, no agreement count presented as a
  forecast, and no combined score appears anywhere in the output.

Usage: python3 refresh_echolens.py
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
SECOND_PATH = os.path.join(HERE, "second-opinion", "data.json")
WIRE_PATH = os.path.join(HERE, "replication-wire", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "echo-lens", "data.json")
ECHO_STORE_DIR = os.path.expanduser(
    "~/workspace/morgue/state/morgue/echo")

VERDICT_WORDS = {"SETUP", "WATCH", "TRAP", "NO TRADE"}

EXPECTED_FAMILIES = {"price", "prints", "positioning", "filings",
                     "facts", "news"}

METHOD_WORDS = ("Whose lens this is: one analyst's published "
                "newsletter method. A reading from this lens is "
                "that method's own levels, reads and conditions "
                "for a name, shown in its own published words, "
                "and nothing else: no other family's reading is "
                "shown in its place, and no reading is blended "
                "with another's.")

AGREEMENT_WORDS = ("Agreement is not a forecast. Readings pointing "
                   "the same way say only that they agree with "
                   "each other; that says nothing by itself about "
                   "what a price does next.")

FORBIDDEN = ("morgue", ".json", ".py", "ledger", "sleeve",
             "data file", "dataset", "scorecard", "echoanalysis")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Echo Lens refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def num(x):
    return f"{int(round(float(x))):,}"


def load_echo_store():
    """The Echo readings store (hookup stream 1): one file per
    panel session, published by the morgue Echo lane running the
    method's own algorithm. Returns (store, None) or
    (None, error). A missing store is not an error for this page:
    the lens is then honestly not on record, as before."""
    try:
        files = sorted(f for f in os.listdir(ECHO_STORE_DIR)
                       if f.endswith(".json") and f != "manifest.jsonl")
    except OSError:
        return None, None
    if not files:
        return None, None
    path = os.path.join(ECHO_STORE_DIR, files[-1])
    try:
        store = load_json(path)
    except (OSError, ValueError) as exc:
        return None, f"the Echo readings store could not be read: {exc}"
    if store.get("date") != files[-1][:-5]:
        return None, ("the Echo readings store's inside date "
                      "disagrees with its file name; refusing to "
                      "publish a mismatched page.")
    readings = store.get("readings") or {}
    if not readings:
        return None, ("the Echo readings store carries no readings; "
                      "refusing to publish.")
    if store.get("names") != len(readings):
        return None, ("the Echo readings store's name count "
                      "disagrees with its readings; refusing to "
                      "publish.")
    return store, None


def reading_words(r):
    """Plain words for one reading, built only from the fields
    the method's own algorithm recorded for it."""
    parts = [f"The method's verdict: {r['verdict']}."]
    if r.get("reason"):
        parts.append(str(r["reason"]).rstrip(".") + ".")
    if r.get("structure"):
        parts.append(f"Structure: {r['structure']}.")
    if r.get("zone") is not None:
        parts.append(f"Zone at {r['zone']:g}.")
    if r.get("invalidation") is not None:
        parts.append(f"Invalidation at {r['invalidation']:g}.")
    targets = r.get("targets") or {}
    if targets.get("objective_1.618") is not None:
        parts.append(f"Objective at {targets['objective_1.618']:g}.")
    return " ".join(parts)


def build():
    for path in (SECOND_PATH, WIRE_PATH, PROVING_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    second = load_json(SECOND_PATH)
    wire = load_json(WIRE_PATH)
    proving = load_json(PROVING_PATH)

    echo_store, echo_err = load_echo_store()
    if echo_err:
        return fail(echo_err)
    states_by_key = {s.get("key"): s for s in proving.get("states") or []}
    state_key = "proving" if echo_store else "waiting"
    state_entry = states_by_key.get(state_key)
    if state_entry is None:
        return fail("the Proving Ground's vocabulary does not "
                    f"carry the {state_key} state; refusing to "
                    "publish a state label of our own.")

    names = second.get("names") or []
    coverage = second.get("coverage") or {}
    if not names:
        return fail("the record checked carries no names; "
                    "refusing to publish.")

    families = second.get("families") or []
    family_ids = {f.get("id") for f in families}
    if family_ids != EXPECTED_FAMILIES:
        return fail("the set of families on the record is no "
                    "longer exactly the six counted at inspection; "
                    "a fresh inspection is needed before this "
                    "lens's coverage can be stated, refusing to "
                    "publish.")
    for f in families:
        text = ((f.get("name") or "") + " " +
                (f.get("about") or "")).lower()
        if "newsletter" in text or "echo" in text:
            return fail("a family on the record now names this "
                        "lens's method; a fresh inspection is "
                        "needed before this lens's coverage can "
                        "be stated, refusing to publish.")

    # Generic distribution (hookup cure, 2026-10-30): the record
    # now counts up to six speaking families per name.
    COUNT_KEYS = {0: "no_family", 1: "one_family", 2: "two_families",
                  3: "three_families", 4: "four_families",
                  5: "five_families", 6: "six_families"}
    recomputed = {}
    for n in names:
        speaking = n.get("families_speaking")
        if speaking not in COUNT_KEYS:
            return fail(f"{n.get('symbol')} carries a family "
                        f"count this page cannot place "
                        f"({speaking}); refusing to publish.")
        recomputed[speaking] = recomputed.get(speaking, 0) + 1
    published_counts = {k: coverage.get(v)
                        for k, v in COUNT_KEYS.items()
                        if coverage.get(v) is not None}
    if {k: recomputed.get(k, 0) for k in published_counts} \
            != published_counts \
            or coverage.get("names_on_record") != len(names):
        return fail("the coverage counts recomputed from the "
                    "record's names disagree with the coverage "
                    "counts the record publishes; refusing to "
                    "publish a mismatched page.")

    ruling = None
    for claim in wire.get("claims") or []:
        maker = (claim.get("maker") or "").lower()
        text = (claim.get("claim") or "").lower()
        if "echoanalysis" in maker or "echoanalysis" in text \
                or "echo analysis" in maker \
                or "echo analysis" in text \
                or "newsletter" in maker or "newsletter" in text:
            return fail("the research record now carries an entry "
                        "naming this lens's method; a fresh "
                        "inspection is needed before its ruling "
                        "can be stated, refusing to publish.")
        if "0.736" in (claim.get("claim") or ""):
            ruling = claim
    if ruling is None:
        return fail("the research record no longer carries the "
                    "0.736 agreement claim; refusing to publish "
                    "without the ruling this page reports.")
    if ruling.get("verdict_words") != "Did not hold up" \
            or "not a prediction" not in (ruling.get("result") or "") \
            or "agreement" not in (ruling.get("result") or ""):
        return fail("the grading of the 0.736 agreement claim no "
                    "longer reads as it did; refusing to publish "
                    "a ruling of our own.")

    session = second.get("session")
    total = coverage["names_on_record"]

    readings = []
    lens_session = None
    if echo_store:
        lens_session = echo_store["date"]
        known = {n["symbol"] for n in names}
        for sym in sorted(echo_store["readings"]):
            r = echo_store["readings"][sym]
            if sym not in known:
                return fail(f"the Echo readings store names "
                            f"{sym}, which the record checked "
                            "does not carry; refusing to publish.")
            if r.get("verdict") not in VERDICT_WORDS:
                return fail(f"the Echo reading for {sym} carries "
                            f"a verdict this page cannot say "
                            f"({r.get('verdict')}); refusing to "
                            "publish.")
            readings.append({
                "symbol": sym,
                "verdict": r["verdict"],
                "words": reading_words(r),
                "session": lens_session,
                "session_long": long_date(lens_session),
            })

    if readings:
        verdict_counts = {}
        for r in readings:
            verdict_counts[r["verdict"]] = \
                verdict_counts.get(r["verdict"], 0) + 1
        tally = ", ".join(
            f"{num(verdict_counts[k])} {k.lower()}"
            for k in ("SETUP", "WATCH", "TRAP", "NO TRADE")
            if k in verdict_counts)
        coverage_words = (
            f"This lens covers {num(len(readings))} of the "
            f"{num(total)} names on record, with readings from "
            f"the trading day of {long_date(lens_session)}: "
            f"{tally}. Each reading below is this method's own, "
            "shown in its own words and nothing else.")
    else:
        coverage_words = (
            f"This lens covers 0 of the {num(total)} names on record "
            f"for {long_date(session)}. The record checked carries "
            "six separate families of readings, and none of them is "
            "this newsletter method, so this lens has no reading for "
            "any name yet. The names this lens covers are listed "
            "below: there are none yet.")
    ruling_words = (
        f"The research record has ruled on a claim like this "
        f"one, for a different method. The claim: "
        f"\"{ruling['claim']}\" The grading: "
        f"{ruling['verdict_words']}. {ruling['result']} "
        f"Checked against: {ruling['sample']}. That ruling "
        "belongs to the chart-ranking method it names, not to "
        "this newsletter method. No headline figure for this "
        "newsletter method is on record as ruled on, so this "
        "page shows no figure for it.")

    data = {
        "tool": "Echo Lens",
        "state": "on_record" if readings else "not_on_record",
        "record_session": session,
        "record_session_long": long_date(session),
        "published_at_utc": second.get("board_published_at_utc"),
        "source": second.get("source"),
        "method_words": METHOD_WORDS,
        "agreement_words": AGREEMENT_WORDS,
        "covered_count": len(readings),
        "names_on_record": total,
        "coverage_words": coverage_words,
        "ruling_words": ruling_words,
        "lens_session": lens_session,
        "readings": readings,
        "all_names": [n["symbol"] for n in names],
        "proving_state": state_entry["words"],
        "proving_note": state_entry["definition"],
        "receipt": {
            "session": session,
            "published_at_utc": second.get("board_published_at_utc"),
            "source": second.get("source"),
            "coverage": (second.get("receipt") or {}).get("coverage"),
        },
    }

    blob = json.dumps(data, sort_keys=True)
    for bad in FORBIDDEN:
        if bad in blob.lower():
            return fail(f"assembled data carries internal wording "
                        f"({bad}); refusing to publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (record session {session}, "
          f"{len(readings)} lens readings, {total} names on record)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
