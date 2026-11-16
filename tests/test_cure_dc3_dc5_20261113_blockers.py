"""CURE-DC3-DC5-20261113 blockers (BUGLOG DC-3, High; DC-5, Low).

DC-3: every exit protection keys on the exit classification
(kind == "exit" or a closing position_intent). A close-shaped
intent that arrives WITHOUT either — Friday 2026-11-13:
leaps_momentum's QQQ sells, kind entry, no position_intent, sell
of exactly the 14 QQQ the broker book held — took the ENTRY path:
no _reconcile_exit, no storm check, no virtual-book read, and
burned a deterministic terminal 403 per cycle (69 rows) while the
position sat fully reserved by another sleeve's resting close,
which the pre-flight intercepted for every properly classified
exit the same session. The broker itself infers a close for an
undeclared sell against a long book: position_intent reaches the
wire, and an absent one leaves the inference to the broker.

Cure: at intent intake, an intent that declares NO position_intent
and whose side+qty closes a position the broker book of record
actually holds (closing side, qty <= |position|) is reclassified
to the matching closing position_intent and takes the exit path,
with the reclassification journaled (intent_reclassified_close_
shape). A declared intent (any of the four position_intents) is
never rewritten; a non-live book reclassifies nothing.

DC-5: the submit-failure journal rows (broker_unavailable,
broker_rejected_terminal) omitted kind and position_intent, so a
failure whose mechanism turns on classification (DC-3 itself)
could not be attributed from the record. Both rows now carry both
fields; journal-only, no behaviour change.
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
    live_book = True

    def __init__(self, positions=None, resting=None):
        super().__init__(prices={"QQQ": 687.0, "MSFT": 500.0},
                         fill_mode="pending")
        self.positions = dict(positions or {})
        self.orders = {}
        for i, (sym, side, qty) in enumerate(resting or []):
            self.orders[f"r{i}"] = {
                "id": f"r{i}", "client_order_id": f"r{i}",
                "symbol": sym, "side": side, "qty": qty,
                "filled_qty": 0, "status": "accepted",
                "position_intent": "sell_to_close"}
        self.submits = 0

    def get_positions(self):
        return dict(self.positions)

    def get_open_orders(self):
        return [dict(o) for o in self.orders.values()]

    def submit_order(self, *a, **kw):
        self.submits += 1
        return super().submit_order(*a, **kw)


class RaisingBroker(BookBroker):
    def __init__(self, error, **kw):
        super().__init__(**kw)
        self._error = error

    def submit_order(self, *a, **kw):
        self.submits += 1
        raise self._error


def _disp(broker, slices=None):
    root = tempfile.mkdtemp(prefix="dc3-")
    return Dispatcher(root, broker,
                      slices=slices if slices is not None else {
                          "leaps_momentum": {
                              "capital_usd": 100000.0,
                              "cash_usd": 100000.0}},
                      price_lookup=lambda s: 687.0,
                      session_date="2026-11-13")


def _undeclared_sell(iid, qty=14, symbol="QQQ"):
    # the leaps_momentum Friday shape: an economic close with
    # neither kind == "exit" nor a closing position_intent
    return {"intent_id": iid, "kind": "entry", "symbol": symbol,
            "side": "sell", "qty": qty, "order_type": "market",
            "time_in_force": "day", "limit_price": None,
            "stop_price": None, "price_hint": 687.0}


def _rows(disp, event):
    return [x for x in read_lines(disp.djournal)
            if x.get("event") == event]


class TestCloseShapeReclassification(unittest.TestCase):
    def test_undeclared_close_takes_the_exit_path(self):
        b = BookBroker(positions={"QQQ": 14.0},
                       resting=[("QQQ", "sell", 14.0)])
        d = _disp(b)
        r = d.process_intent(_undeclared_sell("c1"), "leaps_momentum")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "exit_already_resting_at_broker")
        self.assertEqual(b.submits, 0)
        rows = _rows(d, "intent_reclassified_close_shape")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["to_position_intent"], "sell_to_close")
        self.assertEqual(rows[0]["broker_position"], 14.0)

    def test_partial_close_shape_is_reclassified(self):
        b = BookBroker(positions={"QQQ": 14.0},
                       resting=[("QQQ", "sell", 14.0)])
        d = _disp(b)
        r = d.process_intent(_undeclared_sell("c2", qty=10),
                             "leaps_momentum")
        self.assertEqual(r["reason"], "exit_already_resting_at_broker")
        self.assertEqual(b.submits, 0)

    def test_oversize_undeclared_sell_is_not_reclassified(self):
        b = BookBroker(positions={"QQQ": 14.0})
        d = _disp(b)
        r = d.process_intent(_undeclared_sell("c3", qty=20),
                             "leaps_momentum")
        self.assertNotEqual(r.get("reason"),
                            "exit_already_resting_at_broker")
        self.assertEqual(_rows(d, "intent_reclassified_close_shape"),
                         [])
        self.assertEqual(b.submits, 1)

    def test_declared_open_is_never_rewritten(self):
        b = BookBroker(positions={"QQQ": 14.0})
        d = _disp(b)
        intent = _undeclared_sell("c4", qty=5)
        intent["position_intent"] = "sell_to_open"
        r = d.process_intent(intent, "leaps_momentum")
        self.assertEqual(_rows(d, "intent_reclassified_close_shape"),
                         [])
        self.assertEqual(b.submits, 1)

    def test_undeclared_sell_without_a_position_is_untouched(self):
        b = BookBroker()
        d = _disp(b)
        r = d.process_intent(_undeclared_sell("c5", qty=5,
                                              symbol="MSFT"),
                             "leaps_momentum")
        self.assertEqual(_rows(d, "intent_reclassified_close_shape"),
                         [])
        self.assertEqual(b.submits, 1)


class TestFailureRowsCarryClassification(unittest.TestCase):
    def _intent(self, iid, **kw):
        base = {"intent_id": iid, "kind": "entry", "symbol": "MSFT",
                "side": "sell", "qty": 5, "order_type": "market",
                "time_in_force": "day", "limit_price": None,
                "stop_price": None, "price_hint": 500.0}
        base.update(kw)
        return base

    def test_terminal_403_rows_carry_kind_and_position_intent(self):
        err = HttpError(403, '{"code":40310000,"message":'
                             '"potential wash trade detected"}')
        b = RaisingBroker(err)
        d = _disp(b)
        d.process_intent(self._intent("f1"), "leaps_momentum")
        un = _rows(d, "broker_unavailable")
        term = _rows(d, "broker_rejected_terminal")
        self.assertEqual(len(un), 1)
        self.assertEqual(len(term), 1)
        for row in (un[0], term[0]):
            self.assertIn("kind", row)
            self.assertIn("position_intent", row)
            self.assertEqual(row["kind"], "entry")
            self.assertIsNone(row["position_intent"])

    def test_422_terminal_row_carries_the_declared_classification(self):
        err = HttpError(422, '{"code":42210000,"message":"bad field"}')
        b = RaisingBroker(err)
        d = _disp(b)
        d.process_intent(
            self._intent("f2", position_intent="sell_to_open"),
            "leaps_momentum")
        term = _rows(d, "broker_rejected_terminal")
        self.assertEqual(len(term), 1)
        self.assertEqual(term[0]["kind"], "entry")
        self.assertEqual(term[0]["position_intent"], "sell_to_open")


if __name__ == "__main__":
    unittest.main()
