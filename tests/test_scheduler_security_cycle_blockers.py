"""Blockers: scheduler restart-safety / cursor (CORE-6), paper-only security
posture (CORE-7), end-to-end cycle with UNFED exclusion (CORE-8),
batched append-only journals (CORE-9)."""
import os, re, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = timezone.utc


def at(ts):
    return datetime.fromtimestamp(ts, tz=ET)


class TestScheduler(unittest.TestCase):
    ENTRIES = [{"id": "fast", "cadence_s": 60, "session": "24h"},
               {"id": "slow", "cadence_s": 3600, "session": "24h"}]

    def test_cadence_and_restart_no_refire(self):
        from desk3.scheduler import Scheduler
        tmp = tempfile.mkdtemp()
        s1 = Scheduler(tmp, self.ENTRIES)
        self.assertEqual(set(s1.tick(at(10000))), {"fast", "slow"})
        self.assertEqual(s1.tick(at(10030)), [])
        # restart: new instance over same state must not re-fire consumed bars
        s2 = Scheduler(tmp, self.ENTRIES)
        self.assertEqual(s2.tick(at(10030)), [])
        self.assertEqual(set(s2.tick(at(10100))), {"fast"})
        self.assertEqual(set(s2.tick(at(14000))), {"fast", "slow"})

    def test_cursor_consumed_bar_not_refired_after_restart(self):
        from desk3.scheduler import Scheduler
        tmp = tempfile.mkdtemp()
        s1 = Scheduler(tmp, self.ENTRIES)
        s1.tick(at(10000))
        s1.mark_consumed("fast", bar_ts=10000)
        s2 = Scheduler(tmp, self.ENTRIES)
        self.assertNotIn("fast", s2.tick(at(10059)))


class TestSecurity(unittest.TestCase):
    def test_live_env_refused(self):
        from desk3.security import assert_paper_only, LiveTradingRefused
        with self.assertRaises(LiveTradingRefused):
            assert_paper_only(env={"ALPACA_ENV": "live"})
        assert_paper_only(env={"ALPACA_ENV": "paper"})
        assert_paper_only(env={})

    def test_no_real_money_endpoint_in_tree(self):
        pat = re.compile(r"(?<!paper-)api\.alpaca\.markets")
        hits = []
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for f in files:
                if f.endswith((".py", ".sh", ".md", ".json")):
                    p = os.path.join(base, f)
                    with open(p, errors="replace") as fh:
                        for i, line in enumerate(fh, 1):
                            if pat.search(line):
                                hits.append(f"{p}:{i}")
        self.assertEqual(hits, [])

    def test_door_refuses_live_base_url(self):
        from desk3.broker import PaperDoor
        live_url = "https://" + "api.alpaca" + ".markets"  # split: scan must not self-match
        with self.assertRaises(Exception):
            PaperDoor(base_url=live_url)


class TestJournal(unittest.TestCase):
    def test_batched_flush_append_only(self):
        from desk3.journal import BatchedJournal, read_lines
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "s1", "journal.jsonl")
        j = BatchedJournal(batch_size=3)
        for i in range(7):
            j.append(path, {"event": "eval", "n": i})
        self.assertEqual(len(read_lines(path)), 6)  # 2 full batches flushed
        j.flush()
        rows = read_lines(path)
        self.assertEqual([r["n"] for r in rows], list(range(7)))


GOOD = '''
def evaluate(view, ctx):
    return [{"intent_id": ctx["cycle_id"] + "-e1", "kind": "entry",
             "symbol": "SPY", "side": "buy", "qty": 1,
             "limit_price": 100.0, "order_type": "limit"}]
'''


class TestCycle(unittest.TestCase):
    def test_cycle_dispatches_fed_excludes_unfed(self):
        import json, textwrap
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        tmp = tempfile.mkdtemp()
        fixdir = os.path.join(tmp, "fix")
        os.makedirs(fixdir)
        with open(os.path.join(fixdir, "good.py"), "w") as fh:
            fh.write(textwrap.dedent(GOOD))
        desk = Desk(tmp, broker=FakeBroker(prices={"SPY": 100.0}),
                    sleeve_path=fixdir, timeout_s=10.0)
        desk.add_producer("bars", lambda ctx: {"bars": {"SPY": [{"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
                          outputs=("bars",), freshness_sla_s=3600)
        desk.add_sleeve("fed1", "good", inputs=("bars",), cadence_s=60,
                        slice_usd=10000.0)
        desk.add_sleeve("ghost", "good", inputs=("bars", "phantom"), cadence_s=60,
                        slice_usd=10000.0)
        roll = desk.run_cycle(now=at(20000))
        self.assertEqual(roll["sleeves"]["fed1"]["status"], "ok")
        self.assertEqual(roll["sleeves"]["ghost"]["state"], "UNFED")
        self.assertEqual(roll["dispatched"], 1)
        term = json.load(open(os.path.join(tmp, "state", "terminal.json")))
        self.assertEqual(term["snapshot_hash"], roll["snapshot_hash"])
        self.assertIn("ghost", term["unfed"])
        self.assertTrue(term["generated_at"])


if __name__ == "__main__":
    unittest.main()
