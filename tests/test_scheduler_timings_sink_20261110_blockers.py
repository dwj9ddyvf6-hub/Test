"""SCHEDULER-TIMINGS-SINK-20261110 regression blockers (TOTAL
APPLICATION W4; census DSK-7 MEDIUM).

The stranded cure: the GLORY registry lane added an optional
`timings_sink` to desk3/scheduler.py (a callable receiving one
{"job_id", "seconds"} stage record per due job per tick; default
None preserves byte-identical behavior) and proved it on a fixture
(GREEN as fixture in the lane's REPORT), but no blocker test
landed in this tree and no live caller exists: the change sat
uncommitted with zero gate protection.

This file IS the blocker, following the lane's fixture exactly:
due-job stage records carry the job id and the cadence-as-stage
duration, and with timings_sink=None the tick return and the
persisted state are unchanged. Fail direction: on the pre-cure
scheduler.py (no timings_sink parameter) the sink tests error
(TypeError: unexpected keyword), which is the regression shape.

REG-1 note: live per-cycle desk stage stamps remain the registry
lane's standing design row REG-1 (owner: desk lane): wiring the
sink through the live runner requires cycle.py / run_live
heartbeat-seam edits to the live dispatch path, which W4 is
fenced from; this blocker protects the scheduler-level mechanism
only, and live cycle stamps stay UNPROVEN until REG-1 lands.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.scheduler import Scheduler  # noqa: E402

ET = timezone.utc
ENTRIES = [{"id": "fast", "cadence_s": 60, "session": "24h"},
           {"id": "slow", "cadence_s": 3600, "session": "24h"}]


def at(ts):
    return datetime.fromtimestamp(ts, tz=ET)


class TestTimingsSink(unittest.TestCase):
    def test_sink_receives_one_stage_record_per_firing_tick(self):
        tmp = tempfile.mkdtemp()
        records = []
        s = Scheduler(tmp, ENTRIES, timings_sink=records.append)
        due = s.tick(at(10000))
        self.assertEqual(set(due), {"fast", "slow"})
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["runner"], "desk3/scheduler.py:tick")
        self.assertEqual(rec["exit_code"], 0)
        stages = {st["stage"]: st for st in rec["stages"]}
        self.assertIn("tick_scan", stages)
        self.assertIn("state_save", stages)
        self.assertIn("fired=2", stages["tick_scan"]["outcome"])
        self.assertGreaterEqual(rec["total_s"], 0)

    def test_sink_fires_even_when_nothing_due(self):
        # The record is per TICK, not per job: an empty tick still
        # stamps its scan (that is what makes a silent scheduler
        # visible in the timings stream).
        tmp = tempfile.mkdtemp()
        records = []
        s = Scheduler(tmp, ENTRIES, timings_sink=records.append)
        s.tick(at(10000))
        records.clear()
        self.assertEqual(s.tick(at(10030)), [])
        self.assertEqual(len(records), 1)
        stages = {st["stage"]: st for st in records[0]["stages"]}
        self.assertIn("fired=0", stages["tick_scan"]["outcome"])
        self.assertEqual(stages["state_save"]["outcome"],
                         "skipped_no_fire")

    def test_default_sink_none_behavior_unchanged(self):
        tmp = tempfile.mkdtemp()
        s = Scheduler(tmp, ENTRIES)
        self.assertIsNone(s.timings_sink)
        self.assertEqual(set(s.tick(at(10000))), {"fast", "slow"})
        state = json.load(open(s.state_path))
        self.assertEqual(set(state["next_fire"]), {"fast", "slow"})

    def test_sink_exception_never_breaks_the_tick(self):
        # The sink is instrumentation: a raising sink is swallowed
        # by _emit_timings and must not fail scheduling (the lane's
        # design contract: a stamp failure can never fail the run
        # it measures).
        tmp = tempfile.mkdtemp()

        def boom(rec):
            raise RuntimeError("sink down")

        s = Scheduler(tmp, ENTRIES, timings_sink=boom)
        self.assertEqual(set(s.tick(at(10000))), {"fast", "slow"})


if __name__ == "__main__":
    unittest.main()
