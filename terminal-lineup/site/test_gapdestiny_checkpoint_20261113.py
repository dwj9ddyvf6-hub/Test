#!/usr/bin/env python3
"""Regression blocker for GAPDESTINY-CHECKPOINT-20261113 (PR-1).

Defect: the Gap Destiny walk-forward sweep (110+ CPU-minutes
over the shipped panel) held its entire loop state in process
memory, so every VM restart discarded the leg whole; the
session 2026-11-12 forecast refresh died inside this leg
eight times and the checkpoint file never advanced.

Cure: the sweep checkpoints its loop state (cells, score
accumulators, live entries) every five sessions to a file
keyed by the source files' content hashes, and a later run
over the same sources resumes after the last completed
session. These tests prove the state layer the cure stands
on: an exact round trip, resume equivalence (a run split at
a checkpoint boundary finishes with state identical to an
uninterrupted run), and fingerprint gating (a foreign or
corrupt checkpoint is ignored, never trusted).

Fail direction: against the pre-cure module none of the
checkpoint functions exist and every test errors.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refresh_gapdestiny as gd


def _ev(fill, above, below, range_mult):
    return {"fill": fill, "above": above, "below": below,
            "range_mult": range_mult}


def _score(n=0, brier_fill=0.0):
    return {"n": n, "brier_fill": brier_fill,
            "brier_fill_base": 0.0, "brier_above": 0.0,
            "brier_below": 0.0, "range_in_steps": 0, "skipped": 0}


KEYS = [("all",), ("band", "b05"), ("bw", "b05", "Mon"),
        ("fear", "b1", "Tue", True), ("vol", "b2", "Fri", False)]

EVENTS = [_ev(True, True, False, 1.2345678901234567),
          _ev(False, False, True, 0.5),
          _ev(True, False, False, 2.75),
          _ev(False, True, False, 0.987654321),
          _ev(True, True, False, 3.141592653589793),
          _ev(False, False, True, 1.0 / 3.0)]


def _cells_with(events):
    cells = {}
    for key in KEYS:
        c = gd.Cell()
        for ev in events:
            c.add(ev)
        cells[key] = c
    return cells


def _state(cells, last_date="2026-10-20"):
    wf_all = _score(17, 4.31830988618379)
    wf_index = _score(3, 0.7178306918239076)
    wf_by_band = {"b05": _score(9, 2.5), "b1": _score(5, 1.25),
                  "b2": _score(3, 0.56030988618379)}
    live_entries = [{"symbol": "SPY", "p_fill": 0.5713,
                     "range_deciles": [0.5, 1.0, 1.5]}]
    live_states = {"prior_session": "2026-10-19",
                   "fear": True, "vol": None}
    return gd.dump_loop_state(cells, wf_all, wf_index, wf_by_band,
                              last_date, live_entries, live_states)


class CheckpointStateTests(unittest.TestCase):

    def test_round_trip_is_exact(self):
        cells = _cells_with(EVENTS)
        state = _state(cells)
        blob = json.loads(json.dumps(state))
        (cells2, wf_all, wf_index, wf_by_band, last_date,
         live_entries, live_states) = gd.load_loop_state(blob)
        self.assertEqual(last_date, "2026-10-20")
        self.assertEqual(wf_all["brier_fill"], 4.31830988618379)
        self.assertEqual(wf_by_band["b2"]["brier_fill"],
                         0.56030988618379)
        self.assertEqual(live_entries[0]["p_fill"], 0.5713)
        self.assertEqual(live_states,
                         {"prior_session": "2026-10-19",
                          "fear": True, "vol": None})
        self.assertEqual(set(cells2), set(cells))
        for key in KEYS:
            a, b = cells[key], cells2[key]
            self.assertEqual((b.n, b.fills, b.above, b.below),
                             (a.n, a.fills, a.above, a.below))
            self.assertEqual(b.ranges, a.ranges)
            self.assertEqual(b.rates(), a.rates())
        # bool cell keys survive the round trip as bools
        self.assertIn(("fear", "b1", "Tue", True), cells2)
        self.assertIn(("vol", "b2", "Fri", False), cells2)

    def test_resume_matches_uninterrupted(self):
        whole = _cells_with(EVENTS)
        part = _cells_with(EVENTS[:3])
        blob = json.loads(json.dumps(_state(part, "2026-10-13")))
        cells2 = gd.load_loop_state(blob)[0]
        for key in KEYS:
            for ev in EVENTS[3:]:
                cells2[key].add(ev)
        for key in KEYS:
            self.assertEqual(cells2[key].ranges, whole[key].ranges)
            self.assertEqual(cells2[key].rates(), whole[key].rates())

    def test_fingerprint_gates_the_checkpoint(self):
        tmp = tempfile.mkdtemp(prefix="gd-checkpoint-test-")
        path = os.path.join(tmp, "checkpoint.json")
        gd.write_checkpoint(path, "fp-A", _state(_cells_with(EVENTS)))
        self.assertIsNotNone(gd.read_checkpoint(path, "fp-A"))
        self.assertIsNone(gd.read_checkpoint(path, "fp-B"))
        self.assertIsNone(gd.read_checkpoint(
            os.path.join(tmp, "missing.json"), "fp-A"))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertIsNone(gd.read_checkpoint(path, "fp-A"))

    def test_write_is_atomic_and_versioned(self):
        tmp = tempfile.mkdtemp(prefix="gd-checkpoint-test-")
        path = os.path.join(tmp, "checkpoint.json")
        gd.write_checkpoint(path, "fp-A", _state(_cells_with(EVENTS)))
        self.assertFalse(os.path.exists(path + ".tmp"))
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertEqual(payload["fingerprint"], "fp-A")
        self.assertEqual(payload["state"]["version"],
                         gd.CHECKPOINT_VERSION)


if __name__ == "__main__":
    unittest.main()
