"""READINESS-DSP2-20261112 blockers (DEFECT-HUNT DSP-2, High).

Defect: options entries were buying-power checked and cash-booked
at price x qty with no x100 multiplier — 1/100 of true cost — while
reconcile and the CSP branch of the same function both apply the
multiplier. Short entries were also booked as long quantity with a
cash debit, so the in-cycle slice mirror misstated both legs of a
sell_to_open.

Cure: the entry cost, the reservation, and the fill cash and
position updates all run through the one multiplier rule reconcile
documents (OPTIONS-MULTIPLIER-SPEND: OCC cash moves qty x price x
100; equity/crypto stay x1), with side-aware signs: a buy debits, a
sell_to_open credits premium and books a NEGATIVE position, a
buy_to_close debits and closes the short toward zero.

Fail direction: proven on a worktree at the pre-cure HEAD — the
$2,500 OCC entry is admitted against $1,000 of slice cash (booked
cost $25), the fill debits $25 not $2,500, and the sell_to_open
books +10 long with a debit instead of -10 short with a credit.
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OCC = "SPY261218C00500000"


def _disp(cash, prices):
    from desk3.broker import FakeBroker
    from desk3.dispatcher import Dispatcher
    broker = FakeBroker(prices=prices)
    disp = Dispatcher(tempfile.mkdtemp(), broker,
                      slices={"s1": {"capital_usd": cash,
                                     "cash_usd": cash}})
    return disp, broker


def _occ_intent(iid, side, qty, position_intent, kind="entry"):
    return {"intent_id": iid, "kind": kind, "symbol": OCC,
            "side": side, "qty": qty, "order_type": "market",
            "time_in_force": "day", "price_hint": 2.50,
            "position_intent": position_intent}


class TestOptionsMultiplier(unittest.TestCase):
    def test_occ_entry_bp_charges_times_100(self):
        disp, broker = _disp(1000.0, {OCC: 2.50})
        r = disp.process_intent(
            _occ_intent("o1", "buy", 10, "buy_to_open"), "s1")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "insufficient_slice_bp")
        self.assertEqual(broker.submit_count, 0)

    def test_occ_buy_fill_debits_times_100(self):
        disp, broker = _disp(10000.0, {OCC: 2.50})
        r = disp.process_intent(
            _occ_intent("o2", "buy", 10, "buy_to_open"), "s1")
        self.assertEqual(r["status"], "filled", r)
        sl = disp.slice_for("s1")
        self.assertAlmostEqual(sl["cash_usd"], 7500.0)
        self.assertAlmostEqual(sl["reserved_usd"], 0.0)
        self.assertEqual(sl["positions"][OCC]["qty"], 10)
        self.assertAlmostEqual(sl["positions"][OCC]["avg_price"], 2.50)

    def test_occ_sell_to_open_credits_and_books_short(self):
        disp, broker = _disp(10000.0, {OCC: 2.50})
        r = disp.process_intent(
            _occ_intent("o3", "sell", 10, "sell_to_open"), "s1")
        self.assertEqual(r["status"], "filled", r)
        sl = disp.slice_for("s1")
        self.assertAlmostEqual(sl["cash_usd"], 12500.0)
        self.assertEqual(sl["positions"][OCC]["qty"], -10)

    def test_occ_buy_to_close_debits_and_flattens_short(self):
        disp, broker = _disp(10000.0, {OCC: 2.50})
        disp.process_intent(_occ_intent("o4", "sell", 10, "sell_to_open"),
                            "s1")
        mid = disp.slice_for("s1")
        self.assertAlmostEqual(mid["cash_usd"], 12500.0)
        self.assertEqual(mid["positions"][OCC]["qty"], -10)
        r = disp.process_intent(
            _occ_intent("o5", "buy", 10, "buy_to_close", kind="exit"),
            "s1")
        self.assertEqual(r["status"], "filled", r)
        sl = disp.slice_for("s1")
        self.assertAlmostEqual(sl["cash_usd"], 10000.0)
        self.assertNotIn(OCC, sl["positions"])

    def test_equity_fill_unchanged_times_1(self):
        disp, broker = _disp(1000.0, {"SPY": 100.0})
        r = disp.process_intent(
            {"intent_id": "e1", "kind": "entry", "symbol": "SPY",
             "side": "buy", "qty": 10, "limit_price": 100.0,
             "order_type": "limit"}, "s1")
        self.assertEqual(r["status"], "filled", r)
        sl = disp.slice_for("s1")
        self.assertAlmostEqual(sl["cash_usd"], 0.0)
        self.assertEqual(sl["positions"]["SPY"]["qty"], 10)


if __name__ == "__main__":
    unittest.main()
