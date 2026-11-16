"""PURGE-1 regression blockers: snapshot store retention.

Pre-cure, desk3.cycle saved one content-hashed snapshot file per cycle
into state/snapshots and NOTHING ever removed one: 196 files / 1.3 GB
accumulated in the desk's first day, growing ~15 MB per cycle forever.
No consumer reads any snapshot except the current cycle's (cycle.py's
integrity re-read and that cycle's workers, by exact path). Cure:
save_snapshot prunes the directory to the newest SNAPSHOT_KEEP files
on every save. These tests FAIL on the pre-cure code (unbounded files)
and PASS after.
"""
import os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import desk3.snapshot as _snap
from desk3.snapshot import build_snapshot, save_snapshot

SNAPSHOT_KEEP = getattr(_snap, "SNAPSHOT_KEEP", 3)


class TestSnapshotRetention(unittest.TestCase):
    def test_save_prunes_to_keep_newest(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "snapshots")
            paths = []
            for i in range(6):
                snap = build_snapshot({"i": i}, asof=f"2026-10-24T00:0{i}:00Z")
                paths.append(save_snapshot(snap, d))
            files = sorted(os.listdir(d))
            self.assertEqual(len(files), SNAPSHOT_KEEP)
            # the newest saves survive; the oldest are gone
            for p in paths[-SNAPSHOT_KEEP:]:
                self.assertTrue(os.path.exists(p), p)
            for p in paths[:-SNAPSHOT_KEEP]:
                self.assertFalse(os.path.exists(p), p)

    def test_repeated_cycles_bound_the_store(self):
        from desk3.cycle import Desk
        with tempfile.TemporaryDirectory() as tmp:
            desk = Desk(tmp)
            base = datetime(2026, 10, 24, tzinfo=timezone.utc)
            for i in range(5):
                desk.run_cycle(now=base + timedelta(minutes=i))
            desk.close()
            d = os.path.join(tmp, "state", "snapshots")
            self.assertLessEqual(len(os.listdir(d)), SNAPSHOT_KEEP)


if __name__ == "__main__":
    unittest.main()
