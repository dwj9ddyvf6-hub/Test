"""Blockers: TERMINAL-POSITIONS-SHAPE-20261027 — the ivskew class in
v3's own terminal feed. The live account producer serves positions in
the canonical POS-SHAPE-20261026 shape: a flat LIST of
{symbol, qty, avg_price} records (PaperDoor.get_positions_snapshot).
desk3/cycle._write_terminal discarded any non-dict positions value,
and desk3/terminal.build_feed only understood the per-sleeve dict
shape served by test fixtures, so the live feed reported
open_positions = 0 and "0 position(s) open" every cycle no matter
what the account held — ok status, no effect. Cure: build_feed
accepts the canonical list shape (account-level records, counted and
carried as account_positions, never fabricated into per-sleeve
attribution) and _write_terminal passes the snapshot value through.
The dict shape keeps its exact prior behavior."""
import json, os, sys, tempfile, textwrap, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

GOOD = '''
def evaluate(view, ctx):
    return []
'''

CANONICAL_LIST = [{"symbol": "SPY", "qty": 2.0, "avg_price": 100.0},
                  {"symbol": "QQQ", "qty": 5.0, "avg_price": 500.0}]


def at(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _desk(tmp, positions_value):
    from desk3.cycle import Desk
    from desk3.broker import FakeBroker
    fixdir = os.path.join(tmp, "fix"); os.makedirs(fixdir)
    with open(os.path.join(fixdir, "good.py"), "w") as fh:
        fh.write(textwrap.dedent(GOOD))
    desk = Desk(tmp, broker=FakeBroker(prices={"SPY": 100.0}),
                sleeve_path=fixdir, timeout_s=10.0)
    desk.add_producer(
        "account", lambda ctx: {"positions": positions_value},
        outputs=("positions",), freshness_sla_s=3600)
    desk.add_producer(
        "bars", lambda ctx: {"bars": {"SPY": [
            {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
        outputs=("bars",), freshness_sla_s=3600)
    desk.add_sleeve("fed1", "good", inputs=("bars", "positions"),
                    cadence_s=60, slice_usd=10000.0)
    return desk


class TestCanonicalListShape(unittest.TestCase):
    def test_live_list_shape_is_counted_and_carried(self):
        tmp = tempfile.mkdtemp()
        _desk(tmp, list(CANONICAL_LIST)).run_cycle(now=at(20000))
        feed = json.load(open(os.path.join(tmp, "state",
                                           "terminal_feed.json")))
        self.assertEqual(feed["summary"]["open_positions"], 2)
        self.assertIn("2 position(s) open", feed["headline"])
        acct = {p["symbol"]: p for p in feed["account_positions"]}
        self.assertEqual(acct["SPY"]["qty"], 2.0)
        self.assertEqual(acct["QQQ"]["qty"], 5.0)

    def test_empty_list_stays_zero(self):
        tmp = tempfile.mkdtemp()
        _desk(tmp, []).run_cycle(now=at(20000))
        feed = json.load(open(os.path.join(tmp, "state",
                                           "terminal_feed.json")))
        self.assertEqual(feed["summary"]["open_positions"], 0)
        self.assertEqual(feed["account_positions"], [])

    def test_build_feed_list_shape_directly(self):
        from desk3.terminal import build_feed
        roll = {"generated_at": "t", "cycle_id": "c", "status": "ok",
                "sleeves": {"fed1": {"state": "FED", "status": "ok",
                                     "orders_placed": 0}}}
        feed = build_feed(roll, {"fed1": {"slice_usd": 100.0}},
                          positions=list(CANONICAL_LIST))
        self.assertEqual(feed["summary"]["open_positions"], 2)
        self.assertEqual(len(feed["account_positions"]), 2)


class TestDictShapePreserved(unittest.TestCase):
    def test_dict_shape_per_sleeve_attribution_unchanged(self):
        from desk3.terminal import build_feed
        roll = {"generated_at": "t", "cycle_id": "c", "status": "ok",
                "sleeves": {"fed1": {"state": "FED", "status": "ok",
                                     "orders_placed": 0}}}
        feed = build_feed(roll, {"fed1": {"slice_usd": 100.0}},
                          positions={"fed1": [{"symbol": "SPY",
                                               "qty": 2}]})
        rows = {r["name"]: r for r in feed["strategies"]}
        self.assertEqual(rows["fed1"]["open_positions"][0]["symbol"],
                         "SPY")
        self.assertEqual(feed["summary"]["open_positions"], 1)
        self.assertEqual(feed["account_positions"], [])


if __name__ == "__main__":
    unittest.main()
