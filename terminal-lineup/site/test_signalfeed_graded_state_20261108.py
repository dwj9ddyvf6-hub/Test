#!/usr/bin/env python3
"""Regression blocker for the Signal Feed graded-state refusal
(SIGNALFEED-GRADED-STATE-20261108).

Failure class: on 2026-11-08 refresh_signalfeed.py refused a
sound Record because it derived each map card's graded state
from grading sessions (graded when a card's grading session was
older than the freshest on record). The 2026-11-05 group
(grading session 2026-11-06) still carried no grade rows while
the 2026-11-06 group existed (grading session 2026-11-09), so
the derivation counted 30 graded against the Record's own
published 27 and the feed refused. The cure: the Record stamps
each map card with its own graded state from the grading
summary's grade rows (refresh_record.py), and the feed reads
the state as published and fails closed on any card carrying
no state of its own.

This blocker drives refresh_record.build() on fixture inputs
and proves: (1) the producer stamps exactly the grade rows'
cards, no more (the 2026-11-05-group card DDD is stamped
ungraded even though its grading session is older than the
freshest group's); (2) the published file ties: stamped
graded count == map cards_graded; (3) a scorecard whose
cards_graded disagrees with its grade rows is refused at the
source. Pre-cure, refresh_record.py carries no stamp and
checks (1) and (2) fail. Run standalone:
python3 test_signalfeed_graded_state_20261108.py (exit 0 = pass).
"""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent


def load_record_module():
    spec = importlib.util.spec_from_file_location(
        "refresh_record_graded_test", SITE / "refresh_record.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def card_row(underlying, ts, spot):
    return {"component": "gex_static_v1", "underlying": underlying,
            "ts_utc": ts, "spot": spot, "call_wall": spot + 10,
            "put_wall": spot - 10, "zero_gamma": spot + 1}


def fixture_inputs(cards_graded=2):
    """(summary, log rows) shaped like the real inputs: the
    producer builds its map cards from log rows, never from the
    summary. Four cards; two grade rows. DDD carries the exact
    shape that broke the session derivation on 2026-11-08: its
    grading session (2026-11-06, derived from its 2026-11-05
    14:00 UTC timestamp) is older than the freshest group's
    (2026-11-09) yet no grade row names it, so the derivation
    counted it graded while the summary counted it waiting."""
    summary = {
        "generated_at": "2026-11-08T20:00:00Z",
        "counters": {"board_rows_logged": 0,
                     "map_cards_of_record": 4,
                     "units_graded": 2},
        "board": {
            "published": {"horizons": {
                h: {"state": "not_yet_graded"}
                for h in ("1d", "5d", "21d")}},
            "qualified": {"n_logged": 0, "horizons": {
                h: {"state": "not_yet_graded"}
                for h in ("1d", "5d", "21d")}},
        },
        "map": {
            "state": "graded",
            "cards_graded": cards_graded,
            "cards_pending": 4 - cards_graded,
            "grades": [
                {"card_ts": "2026-11-03T14:00:00Z",
                 "session_graded": "2026-11-03"},
                {"card_ts": "2026-11-03T15:00:00Z",
                 "session_graded": "2026-11-03"},
            ],
        },
    }
    rows = [
        card_row("AAA", "2026-11-03T14:00:00Z", 100.0),
        card_row("BBB", "2026-11-03T15:00:00Z", 200.0),
        card_row("DDD", "2026-11-05T14:00:00Z", 250.0),
        card_row("CCC", "2026-11-06T14:00:00Z", 300.0),
    ]
    return summary, rows


def run_build(mod, tmp, summary, rows):
    summary_path = tmp / "scorecard.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    log_path = tmp / "ledger.jsonl"
    log_path.write_text("".join(json.dumps(r) + "\n" for r in rows),
                        encoding="utf-8")
    out_path = tmp / "record_data.json"
    orig = (mod.SUMMARY_PATH, mod.LOG_PATH, mod.OUT_PATH,
            mod.abstention_audit_block)
    mod.SUMMARY_PATH = str(summary_path)
    mod.LOG_PATH = str(log_path)
    mod.OUT_PATH = str(out_path)
    # The abstention audit reads the forecast ledger, a separate
    # input with its own blockers; neutralise it here so this
    # blocker tests only the graded stamp.
    mod.abstention_audit_block = lambda: {"state": "fixture"}
    try:
        rc = mod.build()
    finally:
        (mod.SUMMARY_PATH, mod.LOG_PATH, mod.OUT_PATH,
         mod.abstention_audit_block) = orig
    return rc, out_path


def main() -> int:
    fails = []
    mod = load_record_module()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # (1)+(2): the stamp ties to the grade rows exactly.
        summary, rows = fixture_inputs()
        rc, out_path = run_build(mod, tmp, summary, rows)
        if rc != 0:
            fails.append("build on a sound fixture returned %d" % rc)
        else:
            data = json.loads(out_path.read_text(encoding="utf-8"))
            cards = [c for g in data["map"]["groups"]
                     for c in g["cards"]]
            stamped = {c["index"]: c.get("graded") for c in cards}
            if stamped != {"AAA": True, "BBB": True, "DDD": False,
                           "CCC": False}:
                fails.append("stamps wrong: %r" % (stamped,))
            # DDD is the point: its grading session (2026-11-06)
            # is older than the freshest group's (2026-11-09),
            # so the session derivation would call it graded,
            # but no grade row names it and the stamp says so.
            # The stamp keys on the grade row alone, whatever
            # sessions say.
            if sum(1 for v in stamped.values() if v) \
                    != data["map"]["cards_graded"]:
                fails.append("stamped count disagrees with "
                             "cards_graded")
        # (3): cards_graded lying about the grade rows refuses.
        summary, rows = fixture_inputs(cards_graded=4)
        rc, _ = run_build(mod, tmp, summary, rows)
        if rc == 0:
            fails.append("build accepted cards_graded=4 with 2 "
                         "grade rows")
    for f in fails:
        print("FAIL: " + f)
    print("signalfeed graded state tests: %s (%d failures)"
          % ("PASS" if not fails else "FAIL", len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
