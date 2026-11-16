"""Blockers: FEED-EQUITY-20261031. The terminal feed carried
account_positions and a headline but no account equity, so the
Friday weekly grading could not certify the desk week versus SPY
and QQQ from any feed (audit defect, terminal total audit round 1,
automations sector). The broker's get_account discarded the equity
fields Alpaca returns, build_feed had no account block, and the
cycle only read the account on the reconcile path. Cure: PaperDoor
and FakeBroker get_account both return equity, last_equity,
buying_power and portfolio_value (None when the source carries
none, never fabricated); build_feed carries an account block and
names a failed read in account_error; the cycle reads the account
every cycle for the feed. Fail direction: every test here fails on
the pre-cure tree (no equity key, no account block, no
account_error)."""
import json, os, sys, tempfile, textwrap, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

GOOD = '''
def evaluate(view, ctx):
    return []
'''


def at(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _roll():
    return {"generated_at": "t", "cycle_id": "c", "status": "ok",
            "sleeves": {"fed1": {"state": "FED", "status": "ok",
                                 "orders_placed": 0}}}


class TestBuildFeedAccountBlock(unittest.TestCase):
    def test_account_block_carries_equity(self):
        from desk3.terminal import build_feed
        acct = {"cash": 500.0, "equity": 948382.12,
                "last_equity": 950000.0, "buying_power": 2000.0,
                "portfolio_value": 948382.12, "status": "ACTIVE"}
        feed = build_feed(_roll(), {"fed1": {"slice_usd": 100.0}},
                          positions=[], account=acct)
        self.assertEqual(feed["account"]["equity"], 948382.12)
        self.assertEqual(feed["account"]["cash"], 500.0)
        self.assertNotIn("account_error", feed)

    def test_failed_read_is_named_not_fabricated(self):
        from desk3.terminal import build_feed
        feed = build_feed(_roll(), {"fed1": {"slice_usd": 100.0}},
                          positions=[], account=None,
                          account_error="AlpacaError: down")
        self.assertIsNone(feed["account"])
        self.assertEqual(feed["account_error"], "AlpacaError: down")


class TestBrokerAccountEquity(unittest.TestCase):
    def test_fake_broker_returns_equity_fields(self):
        from desk3.broker import FakeBroker
        b = FakeBroker()
        b.cash = 123.0
        acct = b.get_account()
        self.assertEqual(acct["equity"], 123.0)
        self.assertIn("buying_power", acct)
        self.assertIn("last_equity", acct)

    def test_paperdoor_maps_equity_fields(self):
        src = open(os.path.join(ROOT, "desk3", "broker.py")).read()
        for field in ('"equity"', '"last_equity"', '"buying_power"',
                      '"portfolio_value"'):
            self.assertIn(field, src)


class TestCycleWritesAccountToFeed(unittest.TestCase):
    def test_cycle_feed_carries_account_equity(self):
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        tmp = tempfile.mkdtemp()
        fixdir = os.path.join(tmp, "fix"); os.makedirs(fixdir)
        with open(os.path.join(fixdir, "good.py"), "w") as fh:
            fh.write(textwrap.dedent(GOOD))
        broker = FakeBroker(prices={"SPY": 100.0})
        broker.cash = 777.0
        desk = Desk(tmp, broker=broker, sleeve_path=fixdir,
                    timeout_s=10.0)
        desk.add_producer(
            "account", lambda ctx: {"positions": []},
            outputs=("positions",), freshness_sla_s=3600)
        desk.add_producer(
            "bars", lambda ctx: {"bars": {"SPY": [
                {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0,
                 "v": 1}]}},
            outputs=("bars",), freshness_sla_s=3600)
        desk.add_sleeve("fed1", "good", inputs=("bars", "positions"),
                        cadence_s=60, slice_usd=10000.0)
        desk.run_cycle(now=at(20000))
        feed = json.load(open(os.path.join(tmp, "state",
                                           "terminal_feed.json")))
        self.assertEqual(feed["account"]["equity"], 777.0)
        self.assertEqual(feed["account"]["cash"], 777.0)


if __name__ == "__main__":
    unittest.main()
