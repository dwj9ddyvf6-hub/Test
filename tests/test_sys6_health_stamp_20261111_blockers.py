"""SYS-6 health stamp blockers (NO-PARTIALS DRIVE, 2026-11-11).

The defect (diagnosed by the fix-all wave, cause proven): cycle.py
stamped health.json with the cycle START time but wrote it at cycle
END, so every health file was born ~642s old against the supervision
guardian's 900s staleness threshold (writer median interval 9.9 min):
55.8% of guardian polls (2,197 of 3,936) read stale and logged a
full heal on a healthy desk, and the guardian's healed_enough never
re-tested freshness inside a stale window.

The cure: health.json is stamped at WRITE time; the cycle start is
preserved on the record as cycle_generated_at, and terminal.json
keeps the cycle time as its generated_at, exactly as before.

Fail direction: on the pre-cure tree a cycle pinned to a past clock
writes health.json generated_at == that past clock (born old); the
cured tree writes the real write instant.
"""

import json
import os
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from desk3.broker import FakeBroker  # noqa: E402
from desk3.cycle import Desk  # noqa: E402


class TestHealthStampAtWrite(unittest.TestCase):
    def test_health_generated_at_is_the_write_instant(self):
        root = tempfile.mkdtemp(prefix="sys6-")
        fixdir = os.path.join(root, "fix")
        os.makedirs(fixdir)
        with open(os.path.join(fixdir, "good.py"), "w") as fh:
            fh.write(textwrap.dedent('''
                def evaluate(view, ctx):
                    return []
            '''))
        desk = Desk(root, broker=FakeBroker(prices={"SPY": 100.0}),
                    sleeve_path=fixdir, timeout_s=10.0)
        desk.add_producer(
            "bars",
            lambda ctx: {"bars": {"SPY": [
                {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
            outputs=("bars",), freshness_sla_s=3600)
        desk.add_sleeve("fed1", "good", inputs=("bars",), cadence_s=60,
                        slice_usd=10000.0)
        cycle_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        desk.run_cycle(now=cycle_now)
        health = json.load(
            open(os.path.join(root, "state", "health.json")))
        written = datetime.fromisoformat(health["generated_at"])
        # The write instant is the real clock (2026-11-11 or later in
        # this estate), never the pinned cycle start of 2026-01-01.
        self.assertGreater(written, datetime(2026, 6, 1,
                                             tzinfo=timezone.utc))
        self.assertEqual(health["cycle_generated_at"],
                         cycle_now.isoformat())
        term = json.load(
            open(os.path.join(root, "state", "terminal.json")))
        self.assertEqual(term["generated_at"], cycle_now.isoformat())


if __name__ == "__main__":
    unittest.main()
