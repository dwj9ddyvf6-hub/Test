"""CURE-DC2-20261113 blockers (BUGLOG DC-2, High).

Defect: the exit pre-flight (_reconcile_exit) sums resting orders
only on the close side. A close submitted while an OPPOSITE-side
order rests on the same symbol draws Alpaca's deterministic
40310000 "potential wash trade detected" every cycle (live Friday
2026-11-13: 93 rows, aster_native_btc_eth_sma200 70 +
aster_saty_research 23, every one a BTC/USD sell against the stuck
BTC buy order 684ef8f6). The verdict is terminal so the intent is
consumed and the sleeve re-emits it next cycle, forever; and the
storm dedupe cannot learn it: _storm_check knows only two verdict
classes and the submit-error note fires only on held_for_orders /
insufficient-qty text, which wash-trade text never contains.

Cure: _reconcile_exit terminates locally with the named reason
exit_blocked_opposite_side_resting when an opposite-side order
rests on the symbol, and storm-notes it under a third verdict
class whose check re-reads the current book (suppressed while the
opposite order rests, released the cycle it clears). A terminal
wash-trade answer on an exit submit storm-notes the same class,
so a race the pre-flight could not see becomes learnable too.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402
from desk3.journal import read_lines  # noqa: E402


class HttpError(Exception):
    def __init__(self, status, body):
        super().__init__(body)
        self.status = status
        self.body = body


class BookBroker(FakeBroker):
    """Live-book double with a mutable book (storm-test shape)."""

    live_book = True

    def __init__(self, positions=None, resting=None):
        super().__init__(prices={"BTC/USD": 90000.0}, fill_mode="pending")
        self.positions = dict(positions or {})
        self.orders = {}
        for i, (sym, side, qty) in enumerate(resting or []):
            self.orders[f"r{i}"] = {
                "id": f"r{i}", "client_order_id": f"r{i}",
                "symbol": sym, "side": side, "qty": qty,
                "filled_qty": 0, "status": "accepted",
                "position_intent": "buy_to_open"}
        self.submits = 0

    def get_positions(self):
        return dict(self.positions)

    def get_open_orders(self):
        return [dict(o) for o in self.orders.values()]

    def submit_order(self, *a, **kw):
        self.submits += 1
        return super().submit_order(*a, **kw)


class WashBroker(BookBroker):
    """Book passes pre-flight (no opposite order visible) but the
    submit draws the deterministic wash-trade 403 (the race)."""

    def submit_order(self, *a, **kw):
        self.submits += 1
        raise HttpError(403, '{"code":40310000,"message":'
                             '"potential wash trade detected"}')


def _disp(broker):
    root = tempfile.mkdtemp(prefix="dc2-")
    return Dispatcher(root, broker, slices={},
                      session_date="2026-11-13")


def _exit(iid, symbol="BTC/USD", qty=0.132675707):
    return {"intent_id": iid, "kind": "exit", "symbol": symbol,
            "side": "sell", "qty": qty, "order_type": "market",
            "position_intent": "sell_to_close",
            "time_in_force": "gtc", "limit_price": None,
            "stop_price": None, "price_hint": None}


def _rows(disp, event, reason=None):
    out = []
    for x in read_lines(disp.djournal):
        if x.get("event") != event:
            continue
        if reason is not None and x.get("reason") != reason:
            continue
        out.append(x)
    return out


class TestOppositeSideResting(unittest.TestCase):
    def test_close_facing_resting_opposite_order_terminates_locally(self):
        b = BookBroker(positions={"BTC/USD": 0.132675707},
                       resting=[("BTC/USD", "buy", 0.0565)])
        d = _disp(b)
        r = d.process_intent(_exit("w1"), "aster_native_btc_eth_sma200")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "exit_blocked_opposite_side_resting")
        self.assertEqual(b.submits, 0)
        self.assertEqual(len(_rows(
            d, "intent_rejected",
            "exit_blocked_opposite_side_resting")), 1)

    def test_reemission_suppressed_while_opposite_order_rests(self):
        b = BookBroker(positions={"BTC/USD": 0.132675707},
                       resting=[("BTC/USD", "buy", 0.0565)])
        d = _disp(b)
        d.process_intent(_exit("w1"), "aster_native_btc_eth_sma200")
        r2 = d.process_intent(_exit("w2"), "aster_native_btc_eth_sma200")
        self.assertEqual(r2["reason"], "exit_storm_suppressed")
        self.assertEqual(r2["suppressed_reason"],
                         "exit_blocked_opposite_side_resting")
        self.assertEqual(b.submits, 0)
        # one terminal row + one suppression row, however many repeats
        self.assertEqual(len(_rows(
            d, "intent_rejected",
            "exit_blocked_opposite_side_resting")), 1)
        self.assertEqual(len(_rows(d, "exit_storm_suppressed")), 1)

    def test_suppression_releases_when_opposite_order_clears(self):
        b = BookBroker(positions={"BTC/USD": 0.132675707},
                       resting=[("BTC/USD", "buy", 0.0565)])
        d = _disp(b)
        d.process_intent(_exit("w1"), "aster_native_btc_eth_sma200")
        b.orders = {}  # the stuck order clears
        d._book_cache = None  # next cycle's dispatcher re-reads the book
        r = d.process_intent(_exit("w2"), "aster_native_btc_eth_sma200")
        self.assertNotEqual(r.get("reason"),
                            "exit_blocked_opposite_side_resting")
        self.assertNotEqual(r.get("reason"), "exit_storm_suppressed")
        self.assertEqual(b.submits, 1)

    def test_same_side_resting_still_uses_the_existing_verdict(self):
        b = BookBroker(positions={"BTC/USD": 0.132675707},
                       resting=[("BTC/USD", "sell", 0.132675707)])
        d = _disp(b)
        r = d.process_intent(_exit("w1"), "aster_native_btc_eth_sma200")
        self.assertEqual(r["reason"], "exit_already_resting_at_broker")
        self.assertEqual(b.submits, 0)


class TestWashAnswerBecomesLearnable(unittest.TestCase):
    def test_terminal_wash_answer_on_exit_notes_the_storm_key(self):
        b = WashBroker(positions={"BTC/USD": 0.132675707})
        d = _disp(b)
        d.process_intent(_exit("w1"), "aster_native_btc_eth_sma200")
        keys = d._storm_load()
        rec = keys.get("aster_native_btc_eth_sma200|BTC/USD")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["reason"],
                         "exit_blocked_opposite_side_resting")


if __name__ == "__main__":
    unittest.main()
