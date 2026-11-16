"""DSK-7 stage_timings blockers (NO-PARTIALS DRIVE 2026-11-11):
the REG-1 remainder. GLORY item 2b's proof form, restated by the
register, is "a live cycle roll carrying stage_timings". The
Scheduler's timings sink existed and its unit tests passed, but no
live caller ever constructed a Scheduler: the live path is
run_live -> Desk.run_cycle, which never touches Scheduler at all.
The desk-wide stage picture (warm vs reconcile vs dispatch shares,
min and max per stage across cycles) therefore never existed.

Cure: the cycle measures its own four seams (warm_producers,
snapshot_integrity, reconcile, evaluate_dispatch) in the
Scheduler's record shape, rides the roll, emits to a stage_sink
(Desk kwarg, same contract as the Scheduler's sink), and
_run_live.build_desk wires state/stage_timings.jsonl.

Fail direction on the pre-cure tree: Desk() rejects the stage_sink
kwarg (TypeError) and no roll carries stage_timings.
"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.cycle import Desk
from desk3.broker import FakeBroker


def _root():
    return tempfile.mkdtemp(prefix="stagetimings_")


class TestCycleStageTimings(unittest.TestCase):

    def test_roll_carries_the_four_stage_record(self):
        records = []
        desk = Desk(_root(), broker=FakeBroker(),
                    stage_sink=records.append)
        roll = desk.run_cycle()
        st = roll.get("stage_timings")
        self.assertIsNotNone(st, roll.keys())
        self.assertEqual(
            [s["stage"] for s in st["stages"]],
            ["warm_producers", "snapshot_integrity", "reconcile",
             "evaluate_dispatch"])
        self.assertEqual(st["runner"], "desk3/cycle.py:run_cycle")
        self.assertEqual(st["run_id"], roll["cycle_id"])
        total = sum(s["duration_s"] for s in st["stages"])
        self.assertAlmostEqual(total + st["unattributed_s"],
                               st["total_s"], places=3)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], st)

    def test_no_sink_means_no_record(self):
        desk = Desk(_root(), broker=FakeBroker())
        roll = desk.run_cycle()
        self.assertNotIn("stage_timings", roll)

    def test_raising_sink_never_breaks_the_cycle(self):
        def boom(_record):
            raise RuntimeError("sink down")
        desk = Desk(_root(), broker=FakeBroker(), stage_sink=boom)
        roll = desk.run_cycle()
        self.assertEqual(roll["status"], "ok")
        self.assertIn("stage_timings", roll)

    def test_path_sink_appends_jsonl(self):
        root = _root()
        sink = os.path.join(root, "state", "stage_timings.jsonl")
        desk = Desk(root, broker=FakeBroker(), stage_sink=sink)
        desk.run_cycle()
        lines = open(sink).read().strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["runner"], "desk3/cycle.py:run_cycle")


if __name__ == "__main__":
    unittest.main()
