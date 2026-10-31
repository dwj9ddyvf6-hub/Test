#!/usr/bin/env python3
"""Refresh the Strat Combos Board data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the Strat Scanner's own published record (its
data file beside this script's output): one scanned session,
1,817 names labelled out of 1,833 on record, each labelled name
carrying its labels for the last 5 sessions and any completed
multi-bar pattern the Scanner's rule copy itself named on the
scanned day. This refresh reads that record only; it labels
nothing itself.

Reconstruction choices (the exact construction):
- A combination is read as a sequence: names are grouped by the
  exact run of 5 labels the Scanner's record carries for them,
  oldest first. Each group is named by its last two labels, in
  the Scanner's own words, and the page says plainly that
  combinations are read as sequences.
- Groups are ordered largest first; ties break on the sequence
  itself so the order is stable.
- The plain-words meaning of each label is printed once per
  label, copied from the Scanner's published group words, never
  rewritten here.
- The Scanner's own named completed patterns are carried
  verbatim: the 8 pattern strings the record defines, with the
  names that carry each one. A name can carry two completed
  patterns, so those counts are pattern entries, not names.
- No percentage is computed anywhere: almost every sequence
  group holds fewer than 30 names, so every group shows its
  count only.
- Labels only: no direction, no suggestion, nothing about what
  follows a label. The Scanner's proving state and its note
  travel with this page word for word.

Non-claims: this board groups the Strat Scanner's labels and
adds no labels of its own. It does not claim any combination
beyond the sequences and the completed patterns the record
itself carries.

Fail-closed rules:
- If the Scanner's record is missing, not in the published
  state, or its receipt session disagrees with its session,
  the refresh stops.
- If any labelled name does not carry exactly 5 sequence
  entries, if a sequence's last label is not the name's own
  label, or if the sequence dates differ between names, the
  refresh stops.
- If the sequence group counts do not add up to the Scanner's
  published labelled count, or the completed-pattern entries
  do not add up to the Scanner's published completed count,
  the refresh stops.
- If any published string carries a direction word from the
  Scanner refresh's forbidden list, the refresh stops.

Honesty rules:
- Dates are read off the Scanner's record, never from the
  clock, so running this script twice produces the same file,
  byte for byte.
- Absence is not zero: the 16 names the Scanner did not label
  show nothing here either.

Usage: python3 refresh_stratcombos.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(HERE, "strat-scanner", "data.json")
OUT_PATH = os.path.join(HERE, "strat-combos", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

FORBIDDEN = ("bullish", "bearish", "trigger", "level_of_reclaim",
             "failure_level")

NOTE = ("This board groups the Strat Scanner's labels and adds "
        "no labels of its own. Combinations are read as "
        "sequences: each group below is the exact run of labels "
        "a name showed over the last 5 sessions, named by its "
        "last two labels.")


def fail(message):
    print(f"Strat Combos refresh: {message}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build():
    if not os.path.exists(SRC_PATH):
        return fail("the Strat Scanner's published record was "
                    "not found; refusing to publish.")
    src = load_json(SRC_PATH)
    if src.get("state") != "published" or not src.get("session"):
        return fail("the Strat Scanner's record is not in the "
                    "published state; refusing to publish.")
    session = src["session"]
    receipt = src.get("receipt") or {}
    if receipt.get("session") != session:
        return fail(f"the Scanner record's receipt session "
                    f"({receipt.get('session')}) disagrees with "
                    f"its session ({session}); refusing to "
                    "publish.")
    seq_sessions = src.get("sequence_sessions")
    groups_in = src.get("groups") or []
    if not groups_in:
        return fail("the Scanner record carries no groups; "
                    "refusing to publish.")

    label_words = []
    for g in groups_in:
        label_words.append({
            "key": g["key"],
            "label": "2-up" if g["key"] == "2u"
                     else "2-down" if g["key"] == "2d"
                     else g["label"],
            "name": g["name"],
            "meaning": g["meaning"],
        })
    word = {w["key"]: w["label"] for w in label_words}

    seq_groups = {}
    completed = {}
    dates = None
    labelled = 0
    for g in groups_in:
        for n in g.get("names") or []:
            seq = n.get("sequence") or []
            if len(seq) != seq_sessions:
                return fail(f"{n.get('symbol')} carries "
                            f"{len(seq)} sequence entries, not "
                            f"{seq_sessions}; refusing to "
                            "publish.")
            if seq[-1]["label"] != n.get("label"):
                return fail(f"{n.get('symbol')}'s sequence ends "
                            f"in {seq[-1]['label']} but its label "
                            f"is {n.get('label')}; refusing to "
                            "publish.")
            these_dates = [s["date"] for s in seq]
            if dates is None:
                dates = these_dates
            elif these_dates != dates:
                return fail("the sequence dates differ between "
                            "names; refusing to publish.")
            if seq[-1]["date"] != session:
                return fail("a sequence does not end on the "
                            "scanned session; refusing to "
                            "publish.")
            key = "-".join(s["label"] for s in seq)
            bucket = seq_groups.setdefault(key, {
                "sequence": [s["label"] for s in seq],
                "names": [],
            })
            bucket["names"].append(n["symbol"])
            labelled += 1
            for pat in n.get("completed") or []:
                completed.setdefault(pat, []).append(n["symbol"])
    if labelled != src.get("names_labelled"):
        return fail(f"the names read from the Scanner record "
                    f"({labelled}) do not match its published "
                    f"labelled count ({src.get('names_labelled')}); "
                    "refusing to publish.")
    if sum(len(b["names"]) for b in seq_groups.values()) != labelled:
        return fail("the sequence group counts do not add up to "
                    "the Scanner's published labelled count; "
                    "refusing to publish.")
    completed_entries = sum(len(v) for v in completed.values())
    if completed_entries != src.get("completed_patterns_count"):
        return fail(f"the completed patterns read "
                    f"({completed_entries}) do not match the "
                    f"Scanner's published completed count "
                    f"({src.get('completed_patterns_count')}); "
                    "refusing to publish.")

    out_groups = []
    for key, bucket in seq_groups.items():
        labels = bucket["sequence"]
        names = sorted(bucket["names"])
        out_groups.append({
            "key": key,
            "sequence": labels,
            "sequence_words": [word.get(l, l) for l in labels],
            "name": (f"{word.get(labels[-2], labels[-2])} then "
                     f"{word.get(labels[-1], labels[-1])}"),
            "count": len(names),
            "names": names,
        })
    out_groups.sort(key=lambda b: (-b["count"], b["key"]))

    completed_groups = []
    completed_names = set()
    for pat in sorted(completed, key=lambda p: (-len(completed[p]), p)):
        names = sorted(completed[pat])
        completed_names.update(names)
        completed_groups.append({
            "pattern": pat,
            "count": len(names),
            "names": names,
        })

    coverage = (
        f"{labelled:,} of the {src['names_on_record']:,} names "
        f"in the Strat Scanner's record were labelled for "
        f"{session} and are grouped here into "
        f"{len(out_groups)} combinations; "
        f"{src['names_not_labelled']} had no bar that day and "
        f"show nothing")

    data = {
        "tool": "Strat Combos Board",
        "state": "published",
        "session": session,
        "source": src["source"],
        "proving_state": src["proving_state"],
        "proving_note": src["proving_note"],
        "names_on_record": src["names_on_record"],
        "names_labelled": labelled,
        "names_not_labelled": src["names_not_labelled"],
        "sequence_sessions": seq_sessions,
        "sequence_dates": dates,
        "combination_count": len(out_groups),
        "largest_group_count": out_groups[0]["count"] if out_groups else 0,
        "label_words": label_words,
        "note": NOTE,
        "completed_words": src["words"]["completed"],
        "completed_patterns_count": completed_entries,
        "completed_names_count": len(completed_names),
        "completed_groups": completed_groups,
        "groups": out_groups,
        "coverage": coverage,
        "receipt": {
            "session": session,
            "source": src["source"],
            "coverage": coverage,
        },
    }

    data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
    blob = json.dumps(data, indent=2, sort_keys=True)
    for w in FORBIDDEN:
        if w in blob:
            return fail(f"a direction or setup word ({w}) reached "
                        "the output; refusing to publish anything "
                        "but labels.")
    if "%" in blob:
        return fail("a percentage sign reached the output; this "
                    "board shows counts only; refusing to "
                    "publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(blob)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {session}, {labelled:,} "
          f"labelled in {len(out_groups)} combinations, "
          f"{completed_entries} completed patterns over "
          f"{len(completed_names)} names)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
