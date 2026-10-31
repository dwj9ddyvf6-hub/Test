#!/usr/bin/env python3
"""Refresh the Survivors Wire data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: an assembly view over three published records, read
exactly as they stand and never forked: the Replication Wire's
verdict record (27 claims), the Promoted Book's standings (388
entries), and the Graveyard's burials (11). The Graveyard's lists
are the Wire's own verdicts restated, so they are checked set for
set against the Wire and counted zero times: every item on this
page is counted once, in the record that owns it.

Reconstruction choices, stated as ours: (1) The survivor set
follows the Slate Three design text for this tool, not a looser
reading: a survivor here is a cross-check survivor candidate, an
unproven candidate in a forward feed, labelled unproven on its
face. Exactly one item in the three records carries that
identification (the pullback-depth ranking, maker "Our own
cross-check: a new candidate ranking found by the research
program"), so the candidate list has exactly that one entry, with
its own record's standing words ("Partly held up") and its study
numbers word for word. No per-candidate calls or forward grades
exist in any of the three records, so the feed state is stated as
empty and no call or grade is invented. (2) Items that are still
standing under their own records in the proven sense (the Wire's
held-up claims and the Book's entries at the top standing) are
listed in their own section under their own records' words, never
merged into the candidate and never called proven survivors of
this wire. The Book's top-standing entries carry no titles of
their own, so they are listed by their titled groups, with the
group counts summed and checked against the standing count.
(3) Partly-held claims other than the candidate are shown in
their own partly-standing section; the candidate is counted in
the partly total in the headline arithmetic and shown once, as
the candidate, so the sections add up to the headline. (4) Not
standing is counted, not listed: the 11 burials point to the
Graveyard and the 325 probation entries point to the Promoted
Book, whose lists are the lists of record. (5) The headline
arithmetic presents each record's own line beside the combined
counts, because the combined counts mix two units (tested claims
and book entries). (6) No percentage is computed anywhere on this
page: every group drawn from these records except the Book's own
totals has fewer than 30 items, so all standings are shown as
counts only. Percentages inside a study's own result text are the
record's words about that study's large sample, copied verbatim.
(7) The proving state label is the Proving Ground's own
vocabulary ("Still being proven"), read from its published record
and checked, not paraphrased. (8) Every time on this page comes
from the source records, never from the clock, so running this
script twice produces the same file.

Non-claims: this page does not re-test anything, does not grade
anything the records have not graded, does not promote the
candidate beyond its record's words, and does not publish any
number beyond what the three records themselves state.

Fail-closed rules: if any of the three records is missing or not
in the published state, if any record's published counts disagree
with the counts recomputed from its own entries, if the
Graveyard's lists are not set-identical to the Wire's verdicts, if
the candidate cannot be identified exactly once, if the combined
arithmetic does not add up, if the Proving Ground's vocabulary
does not carry the proving state used here, or if any assembled
words carry an internal file name or desk wording, the refresh
stops and publishes nothing.

Usage: python3 refresh_survivorswire.py
"""

import json
import os

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    from verdict_vocabulary import VERDICT_WORDS
except ImportError:  # refresh stays runnable standalone
    VERDICT_WORDS = {
        "held": "Held up",
        "partly": "Partly held up",
        "did_not": "Did not hold up",
        "not_yet": "Not yet tested",
        "untestable": "Cannot be tested on the records on hand",
    }

HERE = os.path.dirname(os.path.abspath(__file__))
WIRE_PATH = os.path.join(HERE, "replication-wire", "data.json")
BOOK_PATH = os.path.join(HERE, "promoted-book", "data.json")
GRAVE_PATH = os.path.join(HERE, "graveyard", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "survivors-wire", "data.json")

SOURCE_WORDS = ("Three published records, read as they stand: the Replication "
                "Wire's verdicts on re-tested claims, the Promoted Book's "
                "standings for its forecast entries, and the Graveyard's "
                "burials, which restate the Wire's own verdicts and are "
                "counted zero times here")

CANDIDATE_MARK = "a new candidate ranking"

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "morgue", "Femto", "Midna",
             "Codex", "ledger", "Spearman", "INCONCLUSIVE", "CONFIRMED DEAD",
             "PARK", "KILL", "IC ", " bp", "bp/")


def fail(msg):
    raise SystemExit("refresh_survivorswire: FAIL: " + msg)


def load(path, name):
    if not os.path.exists(path):
        fail(f"the {name} published record is missing")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("state") != "published":
        fail(f"the {name} record is not in the published state")
    return data


def build():
    wire = load(WIRE_PATH, "Replication Wire")
    book = load(BOOK_PATH, "Promoted Book")
    grave = load(GRAVE_PATH, "Graveyard")
    if not os.path.exists(PROVING_PATH):
        fail("the Proving Ground published record is missing")
    with open(PROVING_PATH, encoding="utf-8") as f:
        proving = json.load(f)

    # Proving Ground vocabulary for this tool's state.
    states = {s.get("key"): s for s in proving.get("states") or []}
    if "proving" not in states:
        fail("the Proving Ground's vocabulary carries no proving state")
    proving_words = states["proving"].get("words")
    proving_def = states["proving"].get("definition")
    if proving_words != "Still being proven" or not proving_def:
        fail("the Proving Ground's proving state words are not as expected")

    # --- Wire: recompute counts from its own claims. ---
    claims = wire.get("claims") or []
    if not claims:
        fail("the Replication Wire's record carries no claims")
    wc = {"total": len(claims)}
    for verdict in VERDICT_WORDS:
        wc[verdict] = 0
    for c in claims:
        v = c.get("verdict")
        if v not in wc:
            fail(f"a claim on the Wire carries an unknown verdict: {v!r}")
        wc[v] += 1
        for field in ("claim", "maker", "study", "sample", "result", "when",
                      "verdict_words"):
            if not c.get(field):
                fail(f"a claim on the Wire is missing its {field!r}")
    for key, value in wc.items():
        if (wire.get("counts") or {}).get(key) != value:
            fail(f"the Wire's published count for {key!r} disagrees with "
                 f"its own entries ({value})")

    # --- Graveyard: must be the Wire restated, set for set. ---
    gc = grave.get("counts") or {}
    if gc.get("checked_total") != wc["total"] or gc.get("buried") != wc["did_not"] \
            or gc.get("held") != wc["held"] or gc.get("partly") != wc["partly"] \
            or gc.get("not_yet") != wc["not_yet"] \
            or gc.get("untestable") != wc["untestable"]:
        fail("the Graveyard's published counts disagree with the Wire's")
    if grave.get("wire_grading_run_at") != wire.get("grading_run_at"):
        fail("the Graveyard's grading time is not the Wire's")

    def claim_set(entries):
        return sorted(e["claim"] for e in entries)

    wire_by = {}
    for v in VERDICT_WORDS:
        wire_by[v] = claim_set([c for c in claims if c["verdict"] == v])
    if claim_set(grave.get("buried") or []) != wire_by["did_not"]:
        fail("the Graveyard's buried list is not the Wire's did-not list")
    nb = grave.get("not_buried") or {}
    for v in ("held", "partly", "not_yet", "untestable"):
        if claim_set(nb.get(v) or []) != wire_by[v]:
            fail(f"the Graveyard's not-buried {v} list is not the Wire's")

    # --- Book: recompute standings from its own groups. ---
    standings = {s.get("key"): s for s in book.get("standings") or []}
    if set(standings) != {"promoted", "probation"}:
        fail("the Promoted Book's standings are not the two expected ones")
    bc = book.get("counts") or {}
    if bc.get("total") != standings["promoted"].get("count") \
            + standings["probation"].get("count"):
        fail("the Book's published total is not its two standings added")
    if bc.get("promoted") != standings["promoted"].get("count") \
            or bc.get("probation") != standings["probation"].get("count"):
        fail("the Book's published counts disagree with its standings")
    top_groups = []
    top_entries = 0
    for g in standings["promoted"].get("groups") or []:
        n = len(g.get("entries") or [])
        if g.get("count") != n:
            fail("a top-standing group's count is not its entry count")
        top_entries += n
        days = {}
        for e in g["entries"]:
            days[e.get("days_ahead")] = days.get(e.get("days_ahead"), 0) + 1
        top_groups.append({
            "title": g["title"],
            "kind": g["kind"],
            "count": n,
            "watches": g["watches"],
            "expects": g["expects"],
            "days_ahead": [
                {"days": d, "count": days[d]} for d in sorted(days)],
        })
    if top_entries != standings["promoted"]["count"]:
        fail("the Book's top-standing entries do not add to its count")
    probation_entries = sum(len(g.get("entries") or [])
                            for g in standings["probation"].get("groups") or [])
    if probation_entries != standings["probation"]["count"]:
        fail("the Book's probation entries do not add to its count")

    # --- The candidate: identified exactly once, by its record's words. ---
    candidates = [c for c in claims if CANDIDATE_MARK in (c.get("maker") or "")]
    if len(candidates) != 1:
        fail(f"the cross-check candidate is identified {len(candidates)} "
             f"times in the records, not exactly once")
    cand = candidates[0]
    if cand["verdict"] != "partly" or "unproven candidate" not in cand["result"]:
        fail("the candidate's record does not carry it as an unproven, "
             "partly held up candidate")
    candidate = {f: cand[f] for f in
                 ("claim", "maker", "study", "sample", "result", "when",
                  "verdict_words")}
    candidate["note"] = cand.get("note")

    def brief(c):
        return {f: c[f] for f in
                ("claim", "maker", "study", "sample", "result", "when",
                 "verdict_words")}

    held = [brief(c) for c in claims if c["verdict"] == "held"]
    partly_others = [brief(c) for c in claims
                     if c["verdict"] == "partly" and c is not cand]

    # --- Headline arithmetic, per record and combined. ---
    wire_line = {
        "name": "Claims re-tested (the Replication Wire)",
        "examined": wc["total"],
        "tested": wc["held"] + wc["partly"] + wc["did_not"],
        "standing": wc["held"],
        "partly": wc["partly"],
        "not_standing": wc["did_not"],
        "not_yet": wc["not_yet"],
        "untestable": wc["untestable"],
    }
    book_line = {
        "name": "Forecast entries in the book (the Promoted Book)",
        "examined": bc["total"],
        "tested": bc["total"],
        "standing": bc["promoted"],
        "partly": 0,
        "not_standing": bc["probation"],
        "not_yet": 0,
        "untestable": 0,
    }
    combined = {
        "examined": wire_line["examined"] + book_line["examined"],
        "tested": wire_line["tested"] + book_line["tested"],
        "standing": wire_line["standing"] + book_line["standing"],
        "partly": wire_line["partly"],
        "not_standing": wire_line["not_standing"] + book_line["not_standing"],
        "not_yet": wire_line["not_yet"],
        "untestable": wire_line["untestable"],
    }
    if combined["standing"] + combined["partly"] + combined["not_standing"] \
            + combined["not_yet"] + combined["untestable"] \
            != combined["examined"]:
        fail("the combined headline arithmetic does not add up")
    if combined["tested"] != combined["examined"] - combined["not_yet"] \
            - combined["untestable"]:
        fail("the combined tested count is not examined minus not yet "
             "tested minus cannot be tested")

    out = {
        "tool": "Survivors Wire",
        "source": SOURCE_WORDS,
        "state": "published",
        "grading_run_at": wire.get("grading_run_at"),
        "proving_state": proving_words,
        "proving_definition": proving_def,
        "counts": combined,
        "per_record": [wire_line, book_line],
        "graveyard_note": (f"The Graveyard buries the same "
                           f"{wc['did_not']} claims the Wire marked did not "
                           f"hold up. They are counted once, in the Wire's "
                           f"line above, and zero times for the Graveyard."),
        "candidate_count": 1,
        "candidate": candidate,
        "feed_note": ("No forward calls from this candidate are on record "
                      "yet: none of the three records this page reads "
                      "carries a call, a call date, or a forward grade for "
                      "it. Its feed starts empty, and each call it "
                      "publishes from here will be graded in public, so "
                      "it either earns promotion or is buried where "
                      "everyone can read it."),
        "held_up": held,
        "book_top": {
            "standing_words": standings["promoted"]["words"],
            "standing_meaning": standings["promoted"]["meaning"],
            "count": standings["promoted"]["count"],
            "groups": top_groups,
        },
        "partly_others": partly_others,
        "partly_total": wc["partly"],
        "not_standing": {
            "total": combined["not_standing"],
            "buried": wc["did_not"],
            "probation": bc["probation"],
            "probation_words": standings["probation"]["words"],
            "probation_meaning": standings["probation"]["meaning"],
        },
        "not_yet_total": wc["not_yet"],
        "untestable_total": wc["untestable"],
    }

    blob = json.dumps(out, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in blob:
            fail(f"assembled output carries forbidden wording: {bad!r}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"refresh_survivorswire: wrote {OUT_PATH} with 1 candidate, "
          f"{len(held)} held up, {top_entries} at the top standing in "
          f"{len(top_groups)} groups, {len(partly_others)} other partly, "
          f"combined examined {combined['examined']}")


if __name__ == "__main__":
    build()
