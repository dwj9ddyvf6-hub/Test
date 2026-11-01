#!/usr/bin/env python3
"""Refresh the Graveyard data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the Replication Wire's published verdict record,
read exactly as it stands. The Wire is the source of record for
every claim this site has re-tested: it carries each claim in plain
words, who made it, the study that checked it, the study's sample,
its headline numbers, the verdict, and when the study was done.
Every burial on this page is one of the Wire's finished "did not
hold up" entries, copied from the Wire word for word; no number on
this page exists anywhere except on the Wire first.

Reconstruction choices, stated as ours: (1) A claim is buried here
only when the Wire's verdict for it is "did not hold up", which the
Wire gives only to a finished study with numbers. Claims the Wire
marks partly held up, held up, or not yet tested are never buried;
they are named in the not-buried lists with their verdict, and
their full record stays on the Replication Wire, which this page
points to. (2) The first buried entry is an aggregate: the forecast
program's rerun found 564 recipes that did not reproduce, and the
Wire does not name them one by one, so this page buries that one
claim as a single entry and invents no individual entries for the
564. (3) Counts are counted from the Wire's entries themselves and
checked against the counts the Wire itself publishes; the buried
count at the top of the page is the count of buried entries in
this file, never typed in separately. (4) Every time on this page
comes from the Wire's record, never from the clock, so running
this script twice produces the same file.

Non-claims: this page does not re-test anything, does not grade
anything the Wire has not graded, does not bury a claim the Wire
has not finished testing, and does not publish any number beyond
what the Wire's published record itself states.

Fail-closed rules: if the Wire's published record is missing or
not in the published state, if the counts the Wire publishes
disagree with the counts recomputed from its own entries, if any
buried entry is missing a field or its verdict words are not the
Wire's, if any not-buried entry carries a buried verdict, or if
any words assembled here carry an internal file name or desk
wording, the refresh stops and publishes nothing.

Usage: python3 refresh_graveyard.py
"""

import json
import os

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
WIRE_PATH = os.path.join(HERE, "replication-wire", "data.json")
OUT_PATH = os.path.join(HERE, "graveyard", "data.json")

SOURCE_WORDS = ("The Replication Wire's published verdict record: every trading "
                "claim we have re-tested, with its study, its sample and its numbers")

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "morgue", "Femto", "Midna",
             "Codex", "ledger", "Spearman", "INCONCLUSIVE", "CONFIRMED DEAD",
             "PARK", "KILL", " bp", "bp/", "IC ", "MAR ", "CAGR")

ENTRY_FIELDS = ("claim", "maker", "study", "sample", "result", "when")


def fail(msg):
    raise SystemExit("refresh_graveyard: FAIL: " + msg)


def build():
    if not os.path.exists(WIRE_PATH):
        fail("the Replication Wire's published record is missing")
    with open(WIRE_PATH, encoding="utf-8") as f:
        wire = json.load(f)

    if wire.get("state") != "published":
        fail("the Replication Wire's record is not in the published state")
    claims = wire.get("claims") or []
    published_counts = wire.get("counts") or {}
    if not claims:
        fail("the Replication Wire's record carries no claims")

    recomputed = {"total": len(claims), "held": 0, "partly": 0,
                  "did_not": 0, "not_yet": 0, "untestable": 0}
    for c in claims:
        v = c.get("verdict")
        if v not in recomputed:
            fail(f"a claim on the Wire carries an unknown verdict: {v!r}")
        recomputed[v] += 1
    for key, value in recomputed.items():
        if published_counts.get(key) != value:
            fail(f"the Wire's published count for {key!r} is "
                 f"{published_counts.get(key)!r} but its own entries "
                 f"count to {value}")

    buried = []
    not_buried = {"partly": [], "held": [], "not_yet": [],
                  "untestable": []}
    for c in claims:
        for field in ENTRY_FIELDS:
            if not c.get(field):
                fail(f"a claim on the Wire is missing its {field!r}: "
                     f"{c.get('claim')!r}")
        if c["verdict"] == "did_not":
            if c.get("verdict_words") != "Did not hold up":
                fail("a buried entry's verdict words are not the Wire's: "
                     f"{c['claim']!r}")
            entry = {field: c[field] for field in ENTRY_FIELDS}
            entry["verdict_words"] = c["verdict_words"]
            entry["note"] = c.get("note")
            buried.append(entry)
        else:
            not_buried[c["verdict"]].append({
                "claim": c["claim"],
                "maker": c["maker"],
                "verdict_words": c["verdict_words"],
                "when": c["when"],
            })

    if not buried:
        fail("the Wire carries no finished did-not-hold-up entries to bury")

    out = {
        "tool": "The Graveyard",
        "source": SOURCE_WORDS,
        "state": "published",
        "wire_grading_run_at": wire.get("grading_run_at"),
        "counts": {
            "buried": len(buried),
            "checked_total": recomputed["total"],
            "partly": recomputed["partly"],
            "held": recomputed["held"],
            "not_yet": recomputed["not_yet"],
            "untestable": recomputed["untestable"],
        },
        "buried": buried,
        "not_buried": not_buried,
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
    print(f"refresh_graveyard: wrote {OUT_PATH} with {len(buried)} buried "
          f"entries of {recomputed['total']} checked claims "
          f"(partly {recomputed['partly']}, held {recomputed['held']}, "
          f"not yet {recomputed['not_yet']}, "
          f"untestable {recomputed['untestable']})")


if __name__ == "__main__":
    build()
