"""READINESS-REC1-20261112 blockers (DEFECT-HUNT REC-1, High).

Defect: load_baseline returned None for a missing file and equally
for an unparseable one, and reconcile with record_baseline=True
then recorded the broker's current positions as a fresh baseline,
recomputed the cash offset, and returned ok with status
BASELINE_RECORDED. A corrupted, truncated, or lost baseline after
months of history silently reset the truth anchor to whatever the
broker held that cycle; every accumulated discrepancy vanished by
construction and nothing distinguished a re-baseline after loss
from a first-ever baseline.

Cure: reconcile refuses to record when the state carries history —
a baseline file that exists but does not parse, or journal fills
inside the current capital epoch (any fill when no epoch exists).
It names the state BASELINE_LOST_AFTER_HISTORY, halts entries
(cash_halt), and writes nothing. The explicit re-baseline action is
force_record_baseline(), a deliberate operator call cycle.py never
makes. A genuine first baseline still records, and a NEW capital
epoch's first reconcile still records (the dated epoch file is
itself the explicit re-baseline action; the epoch blockers' flow).

Fail direction: proven on a worktree at the pre-cure HEAD — the
corrupt-baseline fixture returns BASELINE_RECORDED and the file is
silently rewritten.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.reconcile import reconcile


def _state(fills=(), epoch=None, baseline_bytes=None):
    state = tempfile.mkdtemp()
    if epoch is not None:
        with open(os.path.join(state, "capital_epoch.json"), "w") as fh:
            json.dump({"epoch_start_utc": epoch}, fh)
    if fills:
        with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
            for i, (ts, qty) in enumerate(fills):
                fh.write(json.dumps(
                    {"event": "fill", "intent_id": f"f{i}",
                     "sleeve": "s1", "symbol": "TEST", "side": "buy",
                     "qty": qty, "price": 100.0, "ts": ts}) + "\n")
    if baseline_bytes is not None:
        with open(os.path.join(state, "reconcile_baseline.json"),
                  "wb") as fh:
            fh.write(baseline_bytes)
    return state


CAPS = {"s1": 10000.0}


class TestBaselineLossRefused(unittest.TestCase):
    def test_corrupt_baseline_with_history_is_named_not_rewritten(self):
        state = _state(
            fills=[("2026-11-10T15:00:00+00:00", 5)],
            epoch="2026-11-01T00:00:00+00:00",
            baseline_bytes=b'{"positions": {"TEST": ')
        before = open(os.path.join(
            state, "reconcile_baseline.json"), "rb").read()
        rep = reconcile(state, {"TEST": 5.0}, broker_cash=9500.0,
                        slice_capital=CAPS, record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_LOST_AFTER_HISTORY",
                         rep)
        self.assertFalse(rep["ok"])
        self.assertTrue(rep["cash_halt"])
        after = open(os.path.join(
            state, "reconcile_baseline.json"), "rb").read()
        self.assertEqual(after, before)  # nothing rewritten

    def test_missing_baseline_with_fills_is_refused(self):
        state = _state(fills=[("2026-11-10T15:00:00+00:00", 5)])
        rep = reconcile(state, {"TEST": 5.0}, broker_cash=9500.0,
                        slice_capital=CAPS, record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_LOST_AFTER_HISTORY",
                         rep)
        self.assertFalse(os.path.exists(
            os.path.join(state, "reconcile_baseline.json")))

    def test_fresh_state_records_first_baseline(self):
        state = _state()
        rep = reconcile(state, {}, broker_cash=10000.0,
                        slice_capital=CAPS, record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_RECORDED", rep)
        self.assertTrue(os.path.exists(
            os.path.join(state, "reconcile_baseline.json")))

    def test_new_epoch_first_reconcile_still_records(self):
        # The epoch contract (RECONCILE-EPOCH-20261026): a dated
        # capital epoch is the explicit re-baseline action; fills
        # from BEFORE the epoch do not block its first baseline.
        state = _state(
            fills=[("2026-10-20T15:00:00+00:00", 5)],
            epoch="2026-11-01T00:00:00+00:00")
        rep = reconcile(state, {}, broker_cash=10000.0,
                        slice_capital=CAPS, record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_RECORDED", rep)

    def test_explicit_rebaseline_action_recovers(self):
        state = _state(
            fills=[("2026-11-10T15:00:00+00:00", 5)],
            epoch="2026-11-01T00:00:00+00:00",
            baseline_bytes=b'{"positions": {"TEST": ')
        from desk3.reconcile import force_record_baseline
        base = force_record_baseline(state, {"TEST": 5.0},
                                     broker_cash=9500.0,
                                     slice_capital=CAPS)
        written = json.load(open(os.path.join(
            state, "reconcile_baseline.json")))
        self.assertEqual(written["positions"], {"TEST": 5.0})
        rep = reconcile(state, {"TEST": 5.0}, broker_cash=9500.0,
                        slice_capital=CAPS, record_baseline=True)
        self.assertNotEqual(rep["status"],
                            "BASELINE_LOST_AFTER_HISTORY", rep)


if __name__ == "__main__":
    unittest.main()
