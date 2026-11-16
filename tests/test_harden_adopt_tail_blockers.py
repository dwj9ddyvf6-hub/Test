"""HARDEN tail-adoption blockers (2026-10-25): the two desk3/cycle.py
cures whose code rode the shared tree uncommitted behind their
BUGLOG entries (HARDEN-CURE3 bars merge, HARDEN-B4 now_iso).

1. HARDEN-CURE3 bars merge: the snapshot bars map is a shared product
   — warm equities and the kraken producer contribute DISJOINT symbol
   keys. Pre-cure, Desk.run_cycle did data.update(out) per producer,
   so a later producer's bars map REPLACED the earlier one wholesale:
   whichever family produced last silently starved the other family's
   sleeves of bars while they still read FED. The pre-existing
   batch-3 wiring test asserted only the FED state, which is keyed on
   produced KEYS, not bar contents — it passed on the broken code.
   This blocker asserts on the saved snapshot artifact itself: BOTH
   producers' bar keys must survive into the one snapshot sleeves
   read.

2. HARDEN-B4 now_iso: desk3/port4_context.py reads view["now_iso"],
   but the Desk snapshot set only "now" — every port4 sleeve
   (fwd_*, gate_1h, leader_*, legends_ema, iron_condor,
   leaps_momentum) raised KeyError in a live cycle the moment its
   inputs were produced. (Behavioral cover also exists via
   test_harden_batch4_blockers' coinbase E2E; this is the direct
   snapshot-level assertion.)

Fail direction: with desk3/cycle.py reverted to HEAD 220644f, both
tests fail (bars key missing / now_iso missing); with the adopted
hunks, both pass. Proven at adoption time (HARDEN-PROGRESS
2026-10-25 tail-adoption entry).
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc)  # Thu


def _cycle_snapshot_data():
    from desk3.cycle import Desk
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state"), exist_ok=True)
    desk = Desk(root, sleeve_path=ROOT)
    desk.add_producer("bars", lambda c: {"bars": {"SPY|1Day": [
        {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
        ["bars"], 3600)
    desk.add_producer("kraken", lambda c: {"bars": {"PF_ADAUSD|240Min": [
        {"t": "t", "o": 1, "h": 1, "l": 1, "c": 1.0, "v": 1}]},
        "kraken": {}}, ["kraken"], 3600)
    desk.add_producer("account", lambda c: {"positions": {}},
                      ["positions"], 3600)
    roll = desk.run_cycle(now=NOW)
    desk.close()
    assert roll["status"] == "ok", roll
    snap_dir = os.path.join(root, "state", "snapshots")
    names = [n for n in os.listdir(snap_dir) if n.endswith(".json")]
    assert len(names) == 1, names
    with open(os.path.join(snap_dir, names[0])) as fh:
        return json.load(fh)["data"]


class TestCycleTailCures(unittest.TestCase):
    def test_bars_merged_across_producers_in_snapshot(self):
        data = _cycle_snapshot_data()
        self.assertIn("SPY|1Day", data["bars"])
        self.assertIn("PF_ADAUSD|240Min", data["bars"])

    def test_snapshot_carries_now_iso_for_port4(self):
        data = _cycle_snapshot_data()
        self.assertEqual(data["now_iso"], NOW.isoformat())
        self.assertEqual(data["now"], NOW.isoformat())


if __name__ == "__main__":
    unittest.main()
