"""FLATTEN-BURST-7-FILLS-WATERMARK-SKIP blockers (2026-11-10).

Defect: sweep_unjournaled_fills skipped any coid in the
watermark's resolved_coids on a batch miss, trusting the
SWEEP-BATCH-20261104 invariant that a resolved coid was seen
terminal with its full filled qty journaled. Seven flatten-burst
orders (2026-11-02, recovered submission rows) sat in
resolved_coids with journaled qty 0.0: they were marked resolved
on a terminal read whose filled delta was never journaled. The
batch is anchored at the watermark (closed_after minus 1h), so
Nov 2 orders can never appear in it, the skip fired every cycle,
and the per-order fallback was never reached: no import event
existed for them, ever (B2 evidence, BTC-EVIDENCE.md Part 3).

Cure: the resolved-skip applies only when the coid's filled qty
is actually journaled (journaled_qty > QTY_TOL). A resolved coid
with nothing journaled falls through to the per-order read,
which imports the delta through the proven path, or verifies
the order genuinely unfilled. A resolved coid whose fills ARE
journaled keeps the batch-era skip exactly (preservation).

Fail direction on the pre-cure tree: the resolved-but-unjournaled
filled order is skipped (per-order read never happens,
imported_rows 0, no fill row).
"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.reconcile import sweep_unjournaled_fills  # noqa: E402

FILLED_AT = "2026-11-02T14:48:00Z"
BURST_COID = "v3-aster_etf_core25_c098-20261102T143637-1"


def _order(coid, qty, status="filled", sym="ABCL", side="sell"):
    return {"id": "ord-" + coid, "client_order_id": coid,
            "symbol": sym, "side": side, "status": status,
            "filled_qty": qty, "filled_avg_price": 10.0,
            "position_intent": "sell_to_close",
            "filled_at": FILLED_AT if qty else None,
            "submitted_at": "2026-11-02T14:36:37Z"}


class StubBroker:
    """Batch-capable stub whose batch never contains the old
    orders (the watermark anchor shape), recording per-order
    reads."""

    def __init__(self, legacy_orders):
        self._legacy = legacy_orders
        self.per_order_reads = []

    def list_orders(self, after_iso=None):
        return {"open": [], "closed": []}

    def get_order_by_client_id(self, coid):
        self.per_order_reads.append(coid)
        return self._legacy[coid]

    def get_positions(self):
        return {}


def _state(coid=BURST_COID, resolved=(BURST_COID,), journaled_qty=0.0):
    root = tempfile.mkdtemp(prefix="burst-test-")
    state = os.path.join(root, "state")
    os.makedirs(state)
    rows = [{"event": "order_submitted",
             "intent_id": "20261102T143637-1",
             "sleeve": "aster_etf_core25_c098",
             "client_order_id": coid, "symbol": "ABCL"}]
    if journaled_qty:
        rows.append({"event": "fill",
                     "intent_id": "20261102T143637-1",
                     "sleeve": "aster_etf_core25_c098",
                     "client_order_id": coid, "symbol": "ABCL",
                     "side": "sell", "qty": journaled_qty,
                     "price": 10.0, "ts": FILLED_AT})
    with open(os.path.join(state, "dispatcher.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    with open(os.path.join(state, "sweep_watermark.json"), "w") as fh:
        json.dump({"closed_after": "2026-11-09T14:44:59.763238Z",
                   "resolved_coids": list(resolved)}, fh)
    return state


def _fills(state):
    out = []
    with open(os.path.join(state, "dispatcher.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("event") == "fill":
                out.append(r)
    return out


class ResolvedUnjournaledTests(unittest.TestCase):
    def test_resolved_unjournaled_filled_order_is_imported(self):
        # THE defect shape, the ABCL burst row in miniature.
        state = _state()
        broker = StubBroker({BURST_COID: _order(BURST_COID, 164.0)})
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(broker.per_order_reads, [BURST_COID])
        self.assertEqual(out["imported_rows"], 1, out)
        self.assertEqual(out["errors"], [], out)
        fills = _fills(state)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["qty"], 164.0)
        self.assertEqual(fills[0]["sleeve"], "aster_etf_core25_c098")
        self.assertEqual(fills[0]["symbol"], "ABCL")
        self.assertTrue(fills[0]["imported"])
        self.assertEqual(fills[0]["broker_order_id"],
                         "ord-" + BURST_COID)

    def test_import_is_idempotent_on_second_sweep(self):
        state = _state()
        broker = StubBroker({BURST_COID: _order(BURST_COID, 164.0)})
        sweep_unjournaled_fills(state, broker)
        out2 = sweep_unjournaled_fills(state, broker)
        self.assertEqual(out2["imported_rows"], 0, out2)
        self.assertEqual(len(_fills(state)), 1)

    def test_resolved_unjournaled_unfilled_order_is_verified(self):
        # A genuinely unfilled terminal order: the fallback read
        # happens (the skip no longer certifies it blind), nothing
        # is imported, nothing errors.
        state = _state()
        broker = StubBroker({BURST_COID: _order(
            BURST_COID, 0.0, status="canceled")})
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(broker.per_order_reads, [BURST_COID])
        self.assertEqual(out["imported_rows"], 0, out)
        self.assertEqual(out["errors"], [], out)
        self.assertEqual(_fills(state), [])

    def test_resolved_fully_journaled_still_skips(self):
        # Preservation: SWEEP-BATCH-20261104's actual invariant
        # (terminal AND fully journaled) keeps the skip.
        state = _state(journaled_qty=164.0)
        broker = StubBroker({BURST_COID: _order(BURST_COID, 164.0)})
        out = sweep_unjournaled_fills(state, broker)
        self.assertEqual(broker.per_order_reads, [])
        self.assertEqual(out["imported_rows"], 0, out)
        self.assertEqual(len(_fills(state)), 1)  # the original only


if __name__ == "__main__":
    unittest.main()
