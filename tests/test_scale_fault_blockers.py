"""Blockers SCALE-1: synthetic sleeves never dispatch; broker-down
queue/retry with fills only from read-back. Fail on pre-cure tree."""
import os, sys, tempfile, textwrap, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

INTENT = {"intent_id": "i1", "kind": "entry", "symbol": "SPY", "side": "buy",
          "qty": 1, "order_type": "market", "price_hint": 100.0}


class DownThenUpBroker:
    def __init__(self):
        self.down = True
        self.orders = {}
        self.submit_count = 0
    def submit_order(self, coid, symbol, side, qty, otype, limit_price=None,
                     time_in_force="day", position_intent=None,
                     stop_price=None):
        if self.down:
            raise ConnectionError("door_down")
        if coid in self.orders:
            return self.orders[coid]
        self.submit_count += 1
        o = {"id": f"b{self.submit_count}", "client_order_id": coid,
             "symbol": symbol, "side": side, "qty": qty, "status": "accepted"}
        self.orders[coid] = o
        return o
    def get_order_by_client_id(self, coid):
        o = dict(self.orders[coid]); o["status"] = "filled"
        o["filled_qty"] = o["qty"]; o["filled_avg_price"] = 100.0
        return o


class TestBrokerDownQueue(unittest.TestCase):
    def test_down_queues_then_retry_fills_once_from_readback(self):
        from desk3.dispatcher import Dispatcher
        tmp = tempfile.mkdtemp()
        broker = DownThenUpBroker()
        d = Dispatcher(tmp, broker, slices={"s1": {"capital_usd": 10000,
                                                   "cash_usd": 10000}},
                       price_lookup=lambda s: 100.0)
        r = d.process_intent(dict(INTENT), "s1")
        self.assertEqual(r["status"], "queued")
        self.assertEqual(broker.submit_count, 0)
        self.assertFalse(any(e.get("event") == "fill"
                             for e in d.journal_events()))
        broker.down = False
        out = d.retry_pending()
        self.assertEqual([x["status"] for x in out], ["filled"])
        self.assertEqual(broker.submit_count, 1)
        self.assertEqual(d.retry_pending(), [])  # nothing left to retry
        r2 = d.process_intent(dict(INTENT), "s1")  # idempotent replay
        self.assertEqual(r2["status"], "duplicate")
        self.assertEqual(broker.submit_count, 1)


class TestSyntheticNeverDispatches(unittest.TestCase):
    def test_synthetic_intents_suppressed_real_ones_dispatch(self):
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        tmp = tempfile.mkdtemp()
        fix = os.path.join(tmp, "fix"); os.makedirs(fix)
        with open(os.path.join(fix, "emit.py"), "w") as fh:
            fh.write(textwrap.dedent('''
                def evaluate(view, ctx):
                    return [{"intent_id": ctx["cycle_id"] + "-" + ctx["sleeve_id"],
                             "kind": "entry", "symbol": "SPY", "side": "buy",
                             "qty": 1, "order_type": "market",
                             "price_hint": 100.0}]
            '''))
        broker = FakeBroker(prices={"SPY": 100.0})
        desk = Desk(os.path.join(tmp, "desk"), broker=broker,
                    sleeve_path=fix, timeout_s=10.0)
        desk.add_producer("p", lambda c: {"bars": {"SPY": [
            {"t": "t", "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
            ["bars"], 3600)
        desk.add_sleeve("synth1", "emit", ["bars"], 300, 10000, synthetic=True)
        desk.add_sleeve("real1", "emit", ["bars"], 300, 10000)
        roll = desk.run_cycle()
        desk.close()
        self.assertEqual(roll["sleeves"]["synth1"].get("intents_suppressed"), 1)
        self.assertEqual(broker.submit_count, 1)  # only real1 dispatched
        self.assertTrue(all("synth1" not in c for c in broker.orders))


if __name__ == "__main__":
    unittest.main()
