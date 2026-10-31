#!/usr/bin/env python3
"""Refresh the Decay Watch data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the forecast program's own records, read exactly as
they stand: the frozen book of promoted entries (whose file hash
matches the pin printed in the second search's written report), the
two search records from the day the book was graded, and the
Promoted Book page's published counts, which the frozen book must
agree with before anything is published. The proving-state words
are read from the Proving Ground's published record.

Reconstruction choices, stated as ours: (1) A movement is published
only when the record itself carries it: an entry's standing
recorded at two or more times, or a dated promotion, demotion, or
probation entry or exit event. This page never re-grades an entry
and never derives a movement from a single snapshot. (2) The record
today holds exactly one grading of the book, made on October 27,
2026 from two searches run that same day on two different sets of
years; those two searches are the making of the one grading, not
two gradings over time, and their one-time outcome is the Grade-A
Board's record, not a movement here. (3) The grading history lists
that one grading with its date and headline counts; the movements
section states plainly that no entry has been re-graded yet, with
the recorded movement counts (all zero, shown as counts only, never
percentages). (4) No time on this page comes from the clock: every
date comes from the records, so running this script twice produces
the same file.

Non-claims: this page does not re-grade anything, does not change
any entry's standing, does not turn the two searches that built the
book into a trend, and does not publish any movement the record
does not itself carry.

Fail-closed rules: if the book record is missing, if its hash does
not match the pin in the written report, if it is not the single
book version on record (a later book version would carry movements
this refresh cannot yet re-read, so it stops rather than publish
the old picture), if its standings disagree with the Promoted
Book's published counts, if either search record cannot be re-read
or was not run on the book's grading date, if the book carries any
field beyond the ones the record is known to hold (a new field
could carry a movement this refresh cannot re-read), if the
Proving Ground's measuring-state words are missing, or if any words
assembled here carry an internal file name or desk wording, the
refresh stops and publishes nothing.

Usage: python3 refresh_decaywatch.py
"""

import hashlib
import json
import os

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD_DIR = os.path.abspath(os.path.join(
    HERE, "..", "records", "forecast-search-2026-10-27"))
FROZEN_DIR = os.path.abspath(os.path.join(
    HERE, "..", "..", "peer-execute-20261027", "sources", "a_factory",
    "desk", "forecast", "frozen"))
BOOK_PATH = os.path.join(FROZEN_DIR, "promoted-book-1.json")
RUN1_JSON = os.path.join(RECORD_DIR, "forecast-search-2026-10-27.json")
RUN2_JSON = os.path.join(RECORD_DIR, "forecast-search-rerun-2026-10-27.json")
RUN2_MD = os.path.join(RECORD_DIR, "forecast-search-rerun-2026-10-27.md")
PROMOTED_PATH = os.path.join(HERE, "promoted-book", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "decay-watch", "data.json")
HISTORY_PATH = os.path.join(HERE, "decay-watch",
                            "standings-history.json")


def compute_movements(prev, new, from_date, to_date):
    """Standing transitions between two recorded standings maps
    (entry id to standing). An entry present in only one map is
    recorded as entering or leaving the book. Pure: the caller
    supplies both maps and both grading dates from the records."""
    moves = []
    for entry_id in sorted(set(prev) | set(new)):
        before = prev.get(entry_id)
        after = new.get(entry_id)
        if before == after:
            continue
        moves.append({
            "name": entry_id,
            "from": before if before is not None
                    else "not in the book",
            "to": after if after is not None else "left the book",
            "date": to_date,
            "from_date": from_date,
        })
    return moves


def movement_counts_for(moves):
    counts = {"total": len(moves), "promotions": 0, "demotions": 0,
              "probation_entries": 0, "probation_exits": 0,
              "entries_regraded": 0}
    for m in moves:
        if m["from"] == "probation" and m["to"] == "promoted":
            counts["promotions"] += 1
        elif m["from"] == "promoted" and m["to"] == "probation":
            counts["demotions"] += 1
        elif m["from"] == "not in the book" and m["to"] == "probation":
            counts["probation_entries"] += 1
        elif m["from"] == "probation" and m["to"] == "left the book":
            counts["probation_exits"] += 1
    counts["entries_regraded"] = (counts["promotions"]
                                  + counts["demotions"])
    return counts

SOURCE_WORDS = ("Our own forecast program's book of promoted entries, "
                "frozen as the program recorded it, and the two search "
                "records from the day the book was graded")

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "Femto", "Midna", "Codex",
             "forecast-search", "promoted-book", "holdout", "discovery",
             "not financial advice", "for informational purposes",
             "for educational purposes", "do your own research",
             "past performance", "no guarantee", "at your own risk",
             "Slate", "ledger", "fid", "%")

KNOWN_ENTRY_FIELDS = {"id", "fid", "target", "cell", "dims", "sign",
                      "direction", "binary", "h", "grade", "status",
                      "windows"}


def fail(msg):
    raise SystemExit("refresh_decaywatch: FAIL: " + msg)


def build():
    for path in (BOOK_PATH, RUN1_JSON, RUN2_JSON, RUN2_MD,
                 PROMOTED_PATH, PROVING_PATH):
        if not os.path.exists(path):
            fail("a record this page reads is missing: %s"
                 % os.path.basename(path))

    # Only one book version may be on record; a later version would
    # carry movements this refresh cannot yet re-read.
    versions = sorted(f for f in os.listdir(FROZEN_DIR)
                      if f.startswith("promoted-book-"))
    if versions != ["promoted-book-1.json"]:
        fail("the frozen record holds book files this refresh cannot "
             "re-read as movements: %r" % (versions,))

    with open(BOOK_PATH, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    with open(RUN2_MD, encoding="utf-8") as f:
        md2 = f.read()
    if digest not in md2:
        fail("the book's contents do not match the pin printed in the "
             "written report")
    book = json.loads(raw.decode("utf-8"))
    if book.get("version") != "promoted-book-1":
        fail("the book record is not the version this page is built on")
    if set(book.keys()) != {"version", "entries"}:
        fail("the book record carries fields this refresh cannot "
             "re-read: %r" % (sorted(book.keys()),))

    entries = book.get("entries")
    if not isinstance(entries, list):
        fail("the book does not carry its entries")
    counts = {"promoted": 0, "probation": 0}
    seen = set()
    for e in entries:
        if set(e.keys()) != KNOWN_ENTRY_FIELDS:
            fail("an entry carries fields this refresh cannot re-read "
                 "as movements: %r" % (sorted(e.keys()),))
        if e["id"] in seen:
            fail("the book carries a duplicate entry: %r" % e["id"])
        seen.add(e["id"])
        pair = (e["status"], e["grade"])
        if pair == ("promoted", "A"):
            counts["promoted"] += 1
        elif pair == ("probation", "B"):
            counts["probation"] += 1
        else:
            fail("an entry carries a standing this page does not know: "
                 "%r / %r" % (e["status"], e["grade"]))
    total = len(entries)

    # The current standings must agree with the Promoted Book's
    # published counts, exactly.
    with open(PROMOTED_PATH, encoding="utf-8") as f:
        promoted = json.load(f)
    pc = promoted.get("counts") or {}
    published = {"total": pc.get("total"), "promoted": pc.get("promoted"),
                 "probation": pc.get("probation")}
    recounted = {"total": total, "promoted": counts["promoted"],
                 "probation": counts["probation"]}
    if published != recounted:
        fail("the book's standings disagree with the Promoted Book's "
             "published counts: book %r, published %r"
             % (recounted, published))
    if recounted != {"total": 388, "promoted": 63, "probation": 325}:
        fail("the book's standings are not the counts this page is "
             "built around: %r" % (recounted,))

    # The two searches that made the one grading, re-read from their
    # own records. Both must carry the book's grading date.
    runs = []
    for path, label in ((RUN1_JSON, "the first search"),
                        (RUN2_JSON, "the second search")):
        with open(path, encoding="utf-8") as f:
            r = json.load(f)
        generated = r.get("generated") or ""
        if not generated.startswith("2026-10-27"):
            fail("%s was not run on the book's grading date: %r"
                 % (label, generated))
        for num in ("split", "cells_total"):
            if num not in r:
                fail("%s cannot be re-read from its record: %s"
                     % (label, num))
        runs.append({"label": label, "generated": generated,
                     "split": r["split"],
                     "cells_total": int(r["cells_total"])})
    if runs[0]["generated"] >= runs[1]["generated"]:
        fail("the two searches are not in the order their records give")

    with open(PROVING_PATH, encoding="utf-8") as f:
        proving = json.load(f)
    measuring = None
    for s in proving.get("states") or []:
        if s.get("key") == "measuring":
            measuring = s
    if not measuring or not measuring.get("words"):
        fail("the proving ground's measuring-state words are missing")

    # Movements the record itself carries: none yet, and that is
    # now proven on every run rather than assumed. No entry carries
    # a standing at more than one time (the book is one snapshot
    # and holds no date, age or history field per entry, checked
    # above), and no later book version or dated standing-change
    # event is on record (checked above). From this run forward
    # (cure 2026-10-31) the producer also keeps a standings
    # snapshot on every run: when a later grading changes any
    # entry's standing in the records this page reads, the
    # transition is computed from the two snapshots and published
    # here, labelled with both grading dates. Today the history
    # holds the one grading's snapshot, so the movements list is
    # empty and every movement count is 0, published as counts.
    standings = {e["id"]: e["status"] for e in entries}
    history = {"snapshots": []}
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)
    snapshots = history.get("snapshots") or []
    if not snapshots or snapshots[-1].get("standings") != standings:
        snapshots.append({"grading_date": "2026-10-27",
                          "standings": standings})
        history = {"snapshots": snapshots}
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=1, sort_keys=True)
            f.write("\n")
    movements = []
    for prev_snap, next_snap in zip(snapshots, snapshots[1:]):
        movements.extend(compute_movements(
            prev_snap["standings"], next_snap["standings"],
            prev_snap["grading_date"], next_snap["grading_date"]))
    live_counts = movement_counts_for(movements)
    out = {
        "tool": "Decay Watch",
        "source": SOURCE_WORDS,
        "state": "published",
        "proving_state": measuring["words"],
        "proving_words": measuring["definition"],
        "gradings_count": 1,
        "gradings": [
            {
                "date": "2026-10-27",
                "date_words": "Tuesday, October 27, 2026",
                "total": total,
                "promoted": counts["promoted"],
                "probation": counts["probation"],
                "detail": (
                    "The book was graded once, in one act, from two "
                    "searches run that same day: the first search "
                    "(started 6:06 in the morning, counting %s "
                    "combinations for testing across the years from "
                    "its January 1, 2023 split) and the second search "
                    "(started 4:34 in the afternoon, counting %s "
                    "combinations for testing across the years from "
                    "its July 1, 2025 split). "
                    "The two searches are two sets of years graded on "
                    "one day, not two gradings of the book over time."
                    % (format(runs[0]["cells_total"], ","),
                       format(runs[1]["cells_total"], ","))),
            }
        ],
        "current_counts": {
            "total": total,
            "promoted": counts["promoted"],
            "probation": counts["probation"],
        },
        "movements": movements,
        "movement_counts": live_counts,
        "movements_note": (
            "No entry has been re-graded yet. The book has been graded "
            "once, so no entry has a standing recorded at two "
            "different times, and no promotion, demotion, or probation "
            "entry or exit is on record. Movements recorded so far: "
            "0 in total: 0 promotions, 0 demotions, 0 entries into "
            "probation, 0 exits from probation."),
        "watch_note": (
            "The watch starts from the grading of Tuesday, October "
            "27, 2026. When the program grades the book again, this "
            "page will show each entry whose standing changed, with "
            "the standing it had, the standing it has, and the two "
            "grading dates, plus the counts of promotions, demotions, "
            "and probation entries and exits that the new grading "
            "records. Until a second grading exists, there is no "
            "movement to show, and none is invented here."),
        "book_note": (
            "The standings themselves, entry by entry, are on the "
            "Promoted Book page. This page does not grade anything: "
            "it only reports how the standings the program recorded "
            "change from one grading to the next."),
    }

    blob = json.dumps(out, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in blob:
            fail("assembled output carries forbidden wording: %r" % bad)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print("refresh_decaywatch: wrote %s with %d grading on record "
          "(%s: %d entries, %d at the top grade, %d on probation) and "
          "0 movements recorded"
          % (OUT_PATH, out["gradings_count"], out["gradings"][0]["date"],
             total, counts["promoted"], counts["probation"]))


if __name__ == "__main__":
    build()
