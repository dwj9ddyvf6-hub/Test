#!/usr/bin/env python3
"""Build the Reversal Wire's data file from the Strat Scanner's published record.

The wire carries only the reversal-shaped labels on that record: hammer
shapes, shooter shapes, and failed 2 labels, each as a dated entry for the
one session the record names those shapes for. The labels are pattern
names from a published rule system, kept and shown as labels only.

Reads only the Scanner's published record and the Proving Ground's
published vocabulary. Fails closed: if any entry or count recomputed here
disagrees with the Scanner's published counts, or any output string
carries a file name or desk wording, the refresh stops and publishes
nothing.

Usage: python3 refresh_reversalwire.py
"""

import json
import os

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SCANNER_PATH = os.path.join(HERE, "strat-scanner", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "reversal-wire", "data.json")

SOURCE_WORDS = ("The Strat Scanner's published labels for the stocks in "
                "the daily scoring run, labelled by a working copy of the "
                "published TheStrat bar-pattern rules")

FAILED_KINDS = {
    "2u red: failed 2u, potential 3": ("failed_2u", "Failed 2-up"),
    "2d green: failed 2d, potential 3": ("failed_2d", "Failed 2-down"),
}

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "morgue", "Femto", "Midna",
             "Codex", "ledger", "buy", "sell", "signal", "strat-scanner",
             "proving-ground", "reversal-wire")


def fail(msg):
    raise SystemExit("refresh_reversalwire: FAIL: " + msg)


def load(path, name):
    if not os.path.exists(path):
        fail(f"the {name} published record is missing")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build():
    scanner = load(SCANNER_PATH, "Strat Scanner")
    if scanner.get("state") != "published":
        fail("the Strat Scanner record is not in the published state")
    proving = load(PROVING_PATH, "Proving Ground")

    states = {s.get("key"): s for s in proving.get("states") or []}
    if "proving" not in states:
        fail("the Proving Ground's vocabulary carries no proving state")
    proving_words = states["proving"].get("words")
    if scanner.get("proving_state") != proving_words:
        fail("the Scanner's proving state is not the Proving Ground's "
             "proving state")
    proving_note = scanner.get("proving_note") or ""
    if not proving_note.startswith(proving_words + ":"):
        fail("the Scanner's proving note does not open with its proving "
             "state words")

    session = scanner.get("session")
    if not session:
        fail("the Scanner record carries no session")
    words = scanner.get("words") or {}
    for key in ("hammer", "shooter", "failed_2u", "failed_2d"):
        if not words.get(key):
            fail(f"the Scanner record carries no plain words for {key!r}")

    # One entry per name: the Scanner groups repeat each name once per
    # label group, so dedupe by symbol and fail if two copies disagree.
    by_symbol = {}
    for group in scanner.get("groups") or []:
        for name in group.get("names") or []:
            sym = name.get("symbol")
            if not sym:
                fail("a name on the Scanner record carries no symbol")
            tag = (name.get("shape"), name.get("failed_2"))
            if sym in by_symbol and by_symbol[sym] != tag:
                fail(f"the Scanner record disagrees with itself on {sym}")
            by_symbol[sym] = tag
    if len(by_symbol) != scanner.get("names_labelled"):
        fail("the names gathered from the Scanner's groups do not add "
             "to its published labelled count")

    entries = []
    counts = {"hammer": 0, "shooter": 0, "failed_2u": 0, "failed_2d": 0}
    for sym in sorted(by_symbol):
        shape, failed = by_symbol[sym]
        if shape in ("hammer", "shooter"):
            counts[shape] += 1
            entries.append({
                "symbol": sym,
                "kind": shape,
                "label": "Hammer shape" if shape == "hammer"
                         else "Shooter shape",
            })
        elif shape is not None:
            fail(f"a name carries an unknown shape: {shape!r}")
        if failed is not None:
            if failed not in FAILED_KINDS:
                fail(f"a name carries an unknown failed label: {failed!r}")
            kind, _ = FAILED_KINDS[failed]
            counts[kind] += 1
            entries.append({"symbol": sym, "kind": kind, "label": failed})

    shape_counts = scanner.get("shape_counts") or {}
    if counts["hammer"] != shape_counts.get("hammer") \
            or counts["shooter"] != shape_counts.get("shooter"):
        fail("the recomputed shape counts disagree with the Scanner's "
             "published shape counts")
    failed_total = counts["failed_2u"] + counts["failed_2d"]
    if failed_total != scanner.get("failed_2_count"):
        fail("the recomputed failed count disagrees with the Scanner's "
             "published failed count")
    distinct = len({e["symbol"] for e in entries})
    total = len(entries)
    if total != counts["hammer"] + counts["shooter"] + failed_total:
        fail("the wire's entry total does not add up from its kinds")

    kind_words = [
        {"kind": "hammer", "label": "Hammer shape",
         "words": words["hammer"]},
        {"kind": "shooter", "label": "Shooter shape",
         "words": words["shooter"]},
        {"kind": "failed_2u", "label": "Failed 2-up",
         "words": words["failed_2u"]},
        {"kind": "failed_2d", "label": "Failed 2-down",
         "words": words["failed_2d"]},
    ]
    counts_out = {
        "total_entries": total,
        "distinct_names": distinct,
        "hammer": counts["hammer"],
        "shooter": counts["shooter"],
        "failed_2u": counts["failed_2u"],
        "failed_2d": counts["failed_2d"],
        "failed_total": failed_total,
    }
    session_block = {
        "date": session,
        "counts": dict(counts_out),
        "entries": entries,
    }
    out = {
        "tool": "Reversal Wire",
        "state": "published",
        "source": SOURCE_WORDS,
        "session": session,
        "sessions_carried": 1,
        "sequence_sessions_on_record": scanner.get("sequence_sessions"),
        "sessions_note": (
            "This wire carries 1 session. The record names hammer, "
            "shooter and failed shapes only for its freshest session, "
            f"{session}, even though it carries plain labels for the "
            f"last {scanner.get('sequence_sessions')} sessions, so every "
            "entry here is dated to that one session."),
        "proving_state": proving_words,
        "proving_note": proving_note,
        "coverage": scanner.get("coverage"),
        "counts": counts_out,
        "kind_words": kind_words,
        "sessions": [session_block],
    }

    blob = json.dumps(out, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in blob:
            fail(f"an output string carries forbidden wording: {bad!r}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"reversal-wire: {total} entries across {distinct} names for "
          f"{session} (hammer {counts['hammer']}, shooter "
          f"{counts['shooter']}, failed 2-up {counts['failed_2u']}, "
          f"failed 2-down {counts['failed_2d']})")


if __name__ == "__main__":
    build()
