"""READINESS-CYC3-20261112 blockers (DEFECT-HUNT CYC-3, High).

Defect: each cycle built every slice as cash equal to full slice
capital with empty positions, and constructed a fresh Dispatcher.
The buying-power gate therefore charged only entries inside one
cycle; a sleeve that filled 90 percent of its slice in prior cycles
faced the next cycle with its full capital again. The
journal-derived book existed in the same Dispatcher but was
consulted only for exits, never to seed entry slices.

Cure: cycle.py seeds each slice at Dispatcher construction from
the journal-derived book — cash = capital minus the sleeve's net
journal spend (journal_derived, the one shared derivation), open
positions with their FIFO average cost (journal_open_costs) — and
the Dispatcher honors a positions seed in the slice spec.

Fail direction: proven on a worktree at the pre-cure HEAD — the
two-cycle fixture's second entry (30 percent after an 80 percent
fill) is ADMITTED pre-cure because cycle 2 re-faces full capital.
"""
import json
import os
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.cycle import Desk
from desk3.broker import FakeBroker


def _fill(sid, sym, side, qty, px, iid):
    return {"event": "fill", "intent_id": iid, "sleeve": sid,
            "symbol": sym, "side": side, "qty": qty, "price": px,
            "ts": "2026-11-12T15:00:00+00:00"}


class TestJournalOpenCosts(unittest.TestCase):
    def test_fifo_average_cost_of_open_lots(self):
        from desk3.reconcile import journal_open_costs
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "dispatcher.jsonl")
        rows = [_fill("s1", "TEST", "buy", 10, 100.0, "a"),
                _fill("s1", "TEST", "buy", 10, 120.0, "b"),
                _fill("s1", "TEST", "sell", 5, 130.0, "c"),
                _fill("s1", "SPY261218C00500000", "buy", 2, 2.50, "d")]
        with open(path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        costs = journal_open_costs(path)
        self.assertAlmostEqual(costs["s1"]["TEST"],
                               (5 * 100.0 + 10 * 120.0) / 15.0)
        # OCC avg cost is the per-share premium (the x100 applies
        # to cash, never to the premium itself).
        self.assertAlmostEqual(costs["s1"]["SPY261218C00500000"], 2.50)


class TestDispatcherSeed(unittest.TestCase):
    def test_positions_seed_is_honored(self):
        from desk3.dispatcher import Dispatcher
        broker = FakeBroker(prices={"TEST": 100.0})
        disp = Dispatcher(
            tempfile.mkdtemp(), broker,
            slices={"s1": {"capital_usd": 1000.0, "cash_usd": 200.0,
                           "positions": {"TEST": {
                               "symbol": "TEST", "qty": 8.0,
                               "avg_price": 100.0}}}})
        sl = disp.slice_for("s1")
        self.assertEqual(sl["positions"]["TEST"]["qty"], 8.0)
        r = disp.process_intent(
            {"intent_id": "x1", "kind": "exit", "symbol": "TEST",
             "side": "sell", "qty": 8, "order_type": "market",
             "time_in_force": "day", "price_hint": 100.0,
             "position_intent": "sell_to_close"}, "s1")
        self.assertEqual(r["status"], "filled", r)
        sl = disp.slice_for("s1")
        self.assertNotIn("TEST", sl["positions"])
        self.assertAlmostEqual(sl["cash_usd"], 1000.0)


class TestTwoCycleCumulativeBP(unittest.TestCase):
    def test_second_cycle_charges_prior_fills(self):
        tmp = tempfile.mkdtemp()
        mod = os.path.join(tmp, "c3_sleeve.py")
        with open(mod, "w") as fh:
            fh.write(textwrap.dedent("""
                import os
                def evaluate(view, ctx):
                    marker = os.path.join(ctx["state_dir"],
                                          "cycle2.marker")
                    if os.path.exists(marker):
                        return [{"intent_id": "c3-second",
                                 "kind": "entry", "symbol": "TEST",
                                 "side": "buy", "qty": 3,
                                 "order_type": "market",
                                 "time_in_force": "day",
                                 "price_hint": 100.0}]
                    os.makedirs(ctx["state_dir"], exist_ok=True)
                    with open(marker, "w") as mfh:
                        mfh.write("1")
                    return [{"intent_id": "c3-first",
                             "kind": "entry", "symbol": "TEST",
                             "side": "buy", "qty": 8,
                             "order_type": "market",
                             "time_in_force": "day",
                             "price_hint": 100.0}]
            """))
        broker = FakeBroker(prices={"TEST": 100.0})
        desk = Desk(tmp, broker=broker, sleeve_path=tmp)
        desk.add_producer("warm", lambda c: {"bars": {}}, ["bars"],
                          10 ** 9)
        desk.add_sleeve("c3", "c3_sleeve", ["bars"], 300, 1000.0)
        desk.run_cycle()
        self.assertEqual(broker.submit_count, 1)  # 80% filled
        desk.run_cycle()
        # Cycle 2 faces 200 of remaining slice cash: the 300 entry
        # is refused at the gate, never submitted.
        self.assertEqual(broker.submit_count, 1)
        rows = [json.loads(l) for l in open(
            os.path.join(tmp, "state", "dispatcher.jsonl"))]
        rej = [r for r in rows if r.get("event") == "intent_rejected"
               and r.get("intent_id") == "c3-second"]
        self.assertEqual(len(rej), 1, rows)
        self.assertEqual(rej[0]["reason"], "insufficient_slice_bp")


if __name__ == "__main__":
    unittest.main()
