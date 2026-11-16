"""Blockers: producer-registry UNFED contract (CORE-4), dispatcher slice BP /
idempotency / fills-only-from-readback (CORE-5)."""
import os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestRegistryContract(unittest.TestCase):
    def test_phantom_input_is_unfed(self):
        from desk3.registry import Registry
        reg = Registry()
        reg.register_producer("bars", outputs=("bars",), freshness_sla_s=600)
        reg.register_sleeve("s1", inputs=("bars",))
        reg.register_sleeve("ghost", inputs=("bars", "phantom_feed"))
        reg.mark_produced("bars", ts=1000.0)
        fed = reg.fed_states(now=1100.0)
        self.assertEqual(fed["s1"]["state"], "FED")
        self.assertEqual(fed["ghost"]["state"], "UNFED")
        self.assertIn("phantom_feed", fed["ghost"]["missing"])

    def test_stale_input_is_unfed(self):
        from desk3.registry import Registry
        reg = Registry()
        reg.register_producer("bars", outputs=("bars",), freshness_sla_s=60)
        reg.register_sleeve("s1", inputs=("bars",))
        reg.mark_produced("bars", ts=1000.0)
        self.assertEqual(reg.fed_states(now=2000.0)["s1"]["state"], "UNFED")

    def test_unproduced_input_is_unfed_not_silent(self):
        from desk3.registry import Registry
        reg = Registry()
        reg.register_producer("bars", outputs=("bars",), freshness_sla_s=600)
        reg.register_sleeve("s1", inputs=("bars",))
        fed = reg.fed_states(now=1000.0)
        self.assertEqual(fed["s1"]["state"], "UNFED")


def intent(iid="i1", qty=10, price=100.0):
    return {"intent_id": iid, "kind": "entry", "symbol": "SPY", "side": "buy",
            "qty": qty, "limit_price": price, "order_type": "limit"}


class TestDispatcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        from desk3.broker import FakeBroker
        self.broker = FakeBroker(prices={"SPY": 100.0})
        from desk3.dispatcher import Dispatcher
        self.disp = Dispatcher(self.tmp, self.broker,
                               slices={"s1": {"capital_usd": 1000.0, "cash_usd": 1000.0}})

    def test_client_order_id_namespaced_v3(self):
        from desk3.models import client_order_id
        self.assertEqual(client_order_id("s1", "i1"), "v3-s1-i1")

    def test_bp_check_rejects_overslice_entry(self):
        r = self.disp.process_intent(intent(qty=50), "s1")  # 50*100 = 5000 > 1000
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(self.broker.submit_count, 0)

    def test_idempotent_duplicate_never_resubmits(self):
        r1 = self.disp.process_intent(intent(), "s1")
        r2 = self.disp.process_intent(intent(), "s1")
        self.assertEqual(r1["status"], "filled")
        self.assertEqual(r2["status"], "duplicate")
        self.assertEqual(self.broker.submit_count, 1)

    def test_fill_updates_slice_from_readback(self):
        self.disp.process_intent(intent(), "s1")
        sl = self.disp.slice_for("s1")
        self.assertEqual(sl["positions"]["SPY"]["qty"], 10)
        self.assertAlmostEqual(sl["cash_usd"], 0.0)

    def test_no_fill_when_broker_readback_pending(self):
        """Broker submit ACK must never be treated as a fill: only a
        read-back reporting filled creates a fill/position."""
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        broker = FakeBroker(prices={"SPY": 100.0}, fill_mode="pending")
        disp = Dispatcher(tempfile.mkdtemp(), broker,
                          slices={"s1": {"capital_usd": 1000.0, "cash_usd": 1000.0}})
        r = disp.process_intent(intent(qty=1), "s1")
        self.assertEqual(r["status"], "submitted")
        self.assertEqual(disp.slice_for("s1")["positions"], {})
        fills = [e for e in disp.journal_events() if e.get("event") == "fill"]
        self.assertEqual(fills, [])


if __name__ == "__main__":
    unittest.main()
