"""SWEEP-BATCH-20261104 blockers.

Live failure, 2026-11-04: the fill sweep made ONE broker GET per
submitted client_order_id: 1,108 reads in the 11:47Z cycle (151
still unfilled), the serial bottleneck inside every cycle.

Cure: when the broker exposes list_orders, the sweep fetches the
batch once (open orders plus closed orders after a watermark,
defaulting to the capital epoch, with a one-hour overlap;
journaling is idempotent so overlap is harmless) and resolves
each submitted coid from the batch. A batch miss falls back to
the legacy per-order read UNLESS the sweep has already seen the
order terminal and fully journaled (the resolved set persisted
in state/sweep_watermark.json), in which case it is skipped.
Brokers without list_orders keep the legacy path byte-for-byte.

Fail direction: pre-cure the sweep ignores list_orders entirely
and reads every coid per-order.
"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.reconcile import sweep_unjournaled_fills  # noqa: E402

FILLED_AT = "2026-11-04T10:00:00Z"


def _order(coid, qty, px=10.0):
    return {"id": "ord-" + coid, "client_order_id": coid,
            "symbol": "SPY", "side": "buy", "status": "filled",
            "filled_qty": qty, "filled_avg_price": px,
            "position_intent": "buy_to_open", "filled_at": FILLED_AT,
            "submitted_at": "2026-11-04T09:59:00Z"}


class StubBroker:
    """Batch-capable stub: records every per-order read."""

    def __init__(self, batch_orders, legacy_orders):
        self._batch = batch_orders
        self._legacy = legacy_orders
        self.per_order_reads = []
        self.list_calls = []

    def list_orders(self, after_iso=None):
        self.list_calls.append(after_iso)
        return {"open": [], "closed": list(self._batch)}

    def get_order_by_client_id(self, coid):
        self.per_order_reads.append(coid)
        return self._legacy[coid]

    def get_positions(self):
        return {}


class LegacyBroker:
    """No list_orders: the pre-cure door shape."""

    def __init__(self, orders):
        self._orders = orders
        self.per_order_reads = []

    def get_order_by_client_id(self, coid):
        self.per_order_reads.append(coid)
        return self._orders[coid]

    def get_positions(self):
        return {}


def _state(coids, resolved=()):
    root = tempfile.mkdtemp(prefix="sweep-test-")
    state = os.path.join(root, "state")
    os.makedirs(state)
    with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
        for c in coids:
            fh.write(json.dumps(
                {"event": "order_submitted", "intent_id": "i-" + c,
                 "sleeve": "s1", "client_order_id": c,
                 "symbol": "SPY"}) + "\n")
    if resolved:
        with open(os.path.join(state, "sweep_watermark.json"), "w") as fh:
            json.dump({"closed_after": "2026-11-04T09:00:00Z",
                       "resolved_coids": list(resolved)}, fh)
    return state


def _fills(state):
    rows = []
    with open(os.path.join(state, "dispatcher.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("event") == "fill":
                rows.append(r)
    return rows


class SweepBatchTests(unittest.TestCase):
    def test_batch_hit_avoids_per_order_read(self):
        state = _state(["A"])
        broker = StubBroker([_order("A", 5)], {})
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(broker.per_order_reads, [])
        self.assertEqual(len(broker.list_calls), 1)
        self.assertEqual(out["imported_rows"], 1)
        fills = _fills(state)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["qty"], 5.0)

    def test_batch_miss_unresolved_falls_back_to_legacy_read(self):
        state = _state(["B"])
        broker = StubBroker([], {"B": _order("B", 2)})
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(broker.per_order_reads, ["B"])
        self.assertEqual(out["imported_rows"], 1)

    def test_batch_miss_resolved_is_skipped(self):
        # AMENDED 2026-11-10 (FLATTEN-BURST-7-FILLS-WATERMARK-SKIP):
        # the original fixture (resolved, journaled 0, broker
        # filled 9, skip expected) encoded the defect itself: seven
        # live burst orders sat in resolved_coids with nothing
        # journaled and were skipped forever. The skip's true
        # invariant is terminal AND fully journaled, so the
        # fixture now journals the fill first; the skip assertion
        # is unchanged for that shape. The unjournaled shape is
        # covered by
        # test_sweep_resolved_unjournaled_20261110_blockers.py.
        state = _state(["C"], resolved=["C"])
        with open(os.path.join(state, "dispatcher.jsonl"), "a") as fh:
            fh.write(json.dumps(
                {"event": "fill", "intent_id": "i-C", "sleeve": "s1",
                 "client_order_id": "C", "symbol": "SPY",
                 "side": "buy", "qty": 9.0, "price": 10.0,
                 "ts": FILLED_AT}) + "\n")
        broker = StubBroker([], {"C": _order("C", 9)})
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(broker.per_order_reads, [])
        self.assertEqual(out["imported_rows"], 0)
        self.assertEqual(len(_fills(state)), 1)  # the journaled one

    def test_watermark_advances_to_newest_closed(self):
        state = _state(["A"])
        broker = StubBroker([_order("A", 1)], {})
        sweep_unjournaled_fills(state, broker)
        with open(os.path.join(state, "sweep_watermark.json")) as fh:
            wm = json.load(fh)
        self.assertEqual(wm["closed_after"], FILLED_AT)
        self.assertIn("A", wm["resolved_coids"])

    def test_legacy_broker_keeps_per_order_path(self):
        state = _state(["D"])
        broker = LegacyBroker({"D": _order("D", 3)})
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(broker.per_order_reads, ["D"])
        self.assertEqual(out["imported_rows"], 1)


if __name__ == "__main__":
    unittest.main()
