"""Blockers D-GATE-20261025: the dispatcher's is_exit predicate derives
from kind + position_intent ONLY. A sell_to_open ENTRY is not an exit:
it faces the slice buying-power gate and the A15 reconcile halt exactly
like a buy_to_open entry. Exits (kind 'exit', or buy_to_close /
sell_to_close) are never BP-gated and never reconcile-halted.

Fail direction: on the pre-cure predicate (is_exit = kind exit OR side
sell) the sell_to_open tests fail — the short entry is submitted/filled
instead of refused, and the reconcile halt never fires for it.
"""
import os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PRICE = 100.0
SLICES = {"sA": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


def _disp(tmp, halted=(), cash_halt=False):
    from desk3.broker import FakeBroker
    from desk3.dispatcher import Dispatcher
    broker = FakeBroker(prices={"QQQ": PRICE})
    d = Dispatcher(tmp, broker, slices=dict(SLICES),
                   price_lookup=lambda s: PRICE)
    d.halted_sleeves = set(halted)
    d.cash_halt = cash_halt
    return d


def _intent(iid, kind, side, pi, qty):
    return {"intent_id": iid, "kind": kind, "symbol": "QQQ", "side": side,
            "qty": qty, "order_type": "market", "price_hint": PRICE,
            "position_intent": pi}


class TestDGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_sell_to_open_over_slice_refused(self):
        d = _disp(self.tmp)
        r = d.process_intent(
            _intent("so1", "entry", "sell", "sell_to_open", 200), "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "insufficient_slice_bp"))

    def test_sell_to_open_within_slice_passes(self):
        d = _disp(self.tmp)
        r = d.process_intent(
            _intent("so2", "entry", "sell", "sell_to_open", 50), "sA")
        self.assertEqual(r["status"], "filled", r)

    def test_sell_entry_without_position_intent_still_gated(self):
        # Bridge fallback can yield an entry with no position_intent;
        # side alone must not exempt it either.
        d = _disp(self.tmp)
        i = _intent("so3", "entry", "sell", None, 200)
        del i["position_intent"]
        r = d.process_intent(i, "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "insufficient_slice_bp"))

    def test_reconcile_halt_applies_to_sell_to_open(self):
        d = _disp(self.tmp, halted={"sA"})
        r = d.process_intent(
            _intent("so4", "entry", "sell", "sell_to_open", 10), "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "reconcile_halt"))
        d2 = _disp(self.tmp, cash_halt=True)
        r = d2.process_intent(
            _intent("so5", "entry", "sell", "sell_to_open", 10), "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "reconcile_halt"))

    def test_exits_never_bp_gated_even_over_slice(self):
        d = _disp(self.tmp)
        for iid, kind, side, pi in (
                ("x1", "exit", "sell", "sell_to_close"),
                ("x2", "exit", "buy", "buy_to_close"),
                ("x3", "entry", "sell", "sell_to_close"),
                ("x4", "entry", "buy", "buy_to_close")):
            r = d.process_intent(_intent(iid, kind, side, pi, 500), "sA")
            self.assertEqual(r["status"], "filled", (iid, r))

    def test_exits_pass_reconcile_halt(self):
        d = _disp(self.tmp, halted={"sA"})
        r = d.process_intent(
            _intent("x5", "exit", "sell", "sell_to_close", 10), "sA")
        self.assertEqual(r["status"], "filled", r)
        r = d.process_intent(
            _intent("x6", "exit", "buy", "buy_to_close", 10), "sA")
        self.assertEqual(r["status"], "filled", r)

    def test_long_side_behavior_unchanged(self):
        d = _disp(self.tmp)
        r = d.process_intent(
            _intent("lo1", "entry", "buy", "buy_to_open", 200), "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "insufficient_slice_bp"))
        r = d.process_intent(
            _intent("lo2", "entry", "buy", "buy_to_open", 50), "sA")
        self.assertEqual(r["status"], "filled", r)
        d2 = _disp(self.tmp, halted={"sA"})
        r = d2.process_intent(
            _intent("lo3", "entry", "buy", "buy_to_open", 10), "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "reconcile_halt"))


if __name__ == "__main__":
    unittest.main()
