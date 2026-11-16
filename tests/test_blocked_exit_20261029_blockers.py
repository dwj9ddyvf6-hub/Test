"""BLOCKED-EXIT-20261029 regression blockers.

The defect (diagnosis: state/blocked_exit_diagnosis_20261029.md):
826 queued exit intents failed HTTP 403 code 40310000 forever and
2 failed 422 on ADAUSDT, because
  1. desk3/broker.py PaperDoor.submit_order never sent
     position_intent (or stop_price): the broker inferred intent
     from side + the real position, so sell_to_close exits against
     a short/flat netted book were inferred sell_to_open and
     margin-refused as NEW shorts;
  2. the dispatcher never reconciled an exit against the broker
     book: exits for positions that do not exist at the broker, or
     are already fully reserved by resting closes, were submitted
     and refused instead of terminating;
  3. ALL 403s were classified transient (DRAIN-CLASS-20261026),
     including the terminal subclasses (wash trade, insufficient
     qty held_for_orders), so phantom exits retried without bound;
  4. desk3/aster_crypto emitted perp-namespace symbols (ADAUSDT)
     verbatim and stamped them on exits for EVERY position in its
     view, not just its own symbol.

These blockers pin the cure in desk3/dispatcher.py,
desk3/broker.py and desk3/aster_crypto.py. Fail direction proven
2026-10-29 by running this file against the pre-cure tree: every
test below failed there (see BUGLOG_2026-10-29.md,
BLOCKED-EXIT-20261029 cure section).
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desk3.broker import FakeBroker, PaperDoor  # noqa: E402
from desk3.dispatcher import Dispatcher, _normalize_broker_symbol, \
    _terminal_broker_answer  # noqa: E402
from desk3.netfetch import FetchError  # noqa: E402


class LiveFakeBroker(FakeBroker):
    """FakeBroker modelling the live book (opts into pre-flight)."""
    live_book = True


def _disp(broker, slices=None):
    root = tempfile.mkdtemp(prefix="blocked-exit-")
    return Dispatcher(root, broker, slices=slices or {})


def _exit(iid, symbol, side, qty, pintent, sleeve_qty_tif="day"):
    return {"intent_id": iid, "kind": "exit", "symbol": symbol,
            "side": side, "qty": qty, "order_type": "market",
            "position_intent": pintent, "time_in_force": sleeve_qty_tif,
            "limit_price": None, "stop_price": None, "price_hint": None}


class TestPositionIntentOnTheWire(unittest.TestCase):
    def test_paperdoor_body_carries_position_intent_and_stop_price(self):
        import desk3.netfetch as nf
        captured = {}
        orig = nf.fetch_json

        def fake_fetch(url, headers=None, timeout=None, method=None,
                       body=None):
            captured["url"] = url
            captured["body"] = json.loads(body.decode())
            return {"id": "x", "status": "accepted"}

        nf.fetch_json = fake_fetch
        try:
            door = PaperDoor(env={"ALPACA_KEY_ID": "k",
                                  "ALPACA_SECRET_KEY": "s"})
            door.submit_order("coid-1", "AXTI", "buy", 10, "market",
                              position_intent="buy_to_close")
            self.assertEqual(captured["body"].get("position_intent"),
                             "buy_to_close")
            door.submit_order("coid-2", "AXTI", "buy", 10, "stop",
                              stop_price="55.5",
                              position_intent="buy_to_close")
            self.assertEqual(captured["body"].get("stop_price"), "55.5")
        finally:
            nf.fetch_json = orig


class TestCancelOrderEmptyBody(unittest.TestCase):
    def test_cancel_order_tolerates_204_empty_body(self):
        import desk3.netfetch as nf
        orig = nf.fetch_bytes
        nf.fetch_bytes = lambda *a, **k: b""
        try:
            door = PaperDoor(env={"ALPACA_KEY_ID": "k",
                                  "ALPACA_SECRET_KEY": "s"})
            out = door.cancel_order("some-order-id")
            self.assertEqual(out["status"], "canceled")
        finally:
            nf.fetch_bytes = orig


class TestExitPreflight(unittest.TestCase):
    def test_exit_with_no_broker_position_is_never_submitted(self):
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"FFIV": -796.0}  # a book exists; TSEM is not in it
        d = _disp(b)
        r = d.process_intent(
            _exit("e1", "TSEM", "sell", 3762, "sell_to_close"), "s_mn_vwap")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "exit_satisfied_no_broker_position")
        self.assertEqual(b.submit_count, 0)

    def test_exit_against_short_is_reconciled_to_buy_to_close(self):
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"AXTI": -13414.0}
        d = _disp(b)
        r = d.process_intent(
            _exit("e2", "AXTI", "sell", 7011, "sell_to_close"),
            "aster_trader_donchian55")
        self.assertEqual(r["status"], "submitted")
        (order,) = list(b.orders.values())
        self.assertEqual(order["side"], "buy")
        self.assertEqual(order["position_intent"], "buy_to_close")
        self.assertEqual(float(order["qty"]), 7011.0)

    def test_exit_already_resting_at_broker_is_terminal(self):
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"TWST": -7.0}
        b.orders["seed"] = {"id": "seed-1", "client_order_id": "seed",
                            "symbol": "TWST", "side": "buy", "qty": 7,
                            "filled_qty": 0, "status": "accepted",
                            "position_intent": "buy_to_close"}
        d = _disp(b)
        r = d.process_intent(
            _exit("e3", "TWST", "buy", 7, "buy_to_close"),
            "aster_saty_research")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "exit_already_resting_at_broker")
        self.assertEqual(b.submit_count, 0)

    def test_exit_qty_clamped_to_uncovered_remainder(self):
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"CORZ": -9234.0}
        b.orders["seed"] = {"id": "seed-1", "client_order_id": "seed",
                            "symbol": "CORZ", "side": "buy", "qty": 4000,
                            "filled_qty": 0, "status": "accepted",
                            "position_intent": "buy_to_close"}
        d = _disp(b)
        r = d.process_intent(
            _exit("e4", "CORZ", "buy", 9234, "buy_to_close"), "sleeve_x")
        self.assertEqual(r["status"], "submitted")
        order = b.orders[r["client_order_id"]]
        self.assertEqual(float(order["qty"]), 5234.0)

    def test_drain_removes_terminal_exit_from_pending_store(self):
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"FFIV": -796.0}
        d = _disp(b)
        intent = _exit("e5", "TSEM", "sell", 3762, "sell_to_close")
        d.pending_store.add(
            {"intent": intent, "sleeve_id": "s_mn_vwap",
             "client_order_id": "v3-s_mn_vwap-e5",
             "session_date": d.session_date, "attempts": 3,
             "last_error": "FetchError:HTTP 403", "queued_at": "t"})
        results = d.drain_pending(cap=10)
        self.assertEqual(d.pending_store.load(), [])
        self.assertEqual(results[0]["status"], "drained_terminal")
        self.assertEqual(b.submit_count, 0)


class TestSymbolDialect(unittest.TestCase):
    def test_normalize_broker_symbol(self):
        self.assertEqual(_normalize_broker_symbol("ADAUSDT"), "ADA/USD")
        self.assertEqual(_normalize_broker_symbol("ENJUSDT"), "ENJ/USD")
        self.assertEqual(_normalize_broker_symbol("ADAUSD"), "ADA/USD")
        self.assertEqual(_normalize_broker_symbol("ADA/USD"), "ADA/USD")
        self.assertEqual(_normalize_broker_symbol("AXTI"), "AXTI")
        self.assertEqual(_normalize_broker_symbol("SPY"), "SPY")

    def test_adausdt_exit_normalized_then_terminal_without_position(self):
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"FFIV": -796.0}
        d = _disp(b)
        r = d.process_intent(
            _exit("e6", "ADAUSDT", "sell", 27, "sell_to_close"),
            "aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"], "exit_satisfied_no_broker_position")
        self.assertEqual(b.submit_count, 0)
        events = d.journal_events()
        self.assertTrue(any(
            e.get("event") == "symbol_normalized"
            and e.get("from_symbol") == "ADAUSDT"
            and e.get("to_symbol") == "ADA/USD" for e in events))

    def test_adausdt_exit_with_position_submits_as_ada_usd(self):
        b = LiveFakeBroker(fill_mode="pending")
        b.positions = {"ADA/USD": 27.0}
        d = _disp(b)
        r = d.process_intent(
            _exit("e7", "ADAUSDT", "sell", 27, "sell_to_close"),
            "aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash")
        self.assertEqual(r["status"], "submitted")
        (order,) = list(b.orders.values())
        self.assertEqual(order["symbol"], "ADA/USD")
        self.assertEqual(order["position_intent"], "sell_to_close")


class _RaisingBroker(LiveFakeBroker):
    def __init__(self, body):
        super().__init__(fill_mode="pending")
        self._body = body
        self.attempts = 0

    def submit_order(self, *a, **k):
        self.attempts += 1
        raise FetchError(403, "https://paper-api.alpaca.markets/v2/orders",
                         body=self._body)


class TestTerminal403Subclasses(unittest.TestCase):
    def _entry(self):
        return {"intent_id": "n1", "kind": "entry", "symbol": "AXTI",
                "side": "buy", "qty": 1, "order_type": "market",
                "position_intent": "buy_to_open", "time_in_force": "day",
                "limit_price": None, "stop_price": None,
                "price_hint": 10.0}

    _SLICES = {"s1": {"capital_usd": 100000.0, "cash_usd": 100000.0}}

    def test_wash_trade_403_is_terminal_single_attempt(self):
        b = _RaisingBroker('{"code":40310000,"message":'
                           '"potential wash trade detected. '
                           'use complex orders"}')
        d = _disp(b, slices=dict(self._SLICES))
        r = d.process_intent(self._entry(), "s1")
        # READINESS-DSP1-20261112 supersession, named: the terminal
        # verdict is consumed in process_intent (status "rejected",
        # never persisted) instead of "queued" into the pending
        # store, whose drain used to submit the identical payload
        # again. Terminal and single-attempt are unchanged.
        self.assertEqual(r["status"], "rejected")
        self.assertFalse(r["transient"])
        self.assertEqual(b.attempts, 1)

    def test_insufficient_bp_403_stays_transient_and_retries(self):
        b = _RaisingBroker('{"buying_power":"0","code":40310000,'
                           '"message":"insufficient buying power"}')
        d = _disp(b, slices=dict(self._SLICES))
        r = d.process_intent(self._entry(), "s1")
        self.assertEqual(r["status"], "queued")
        self.assertTrue(r["transient"])
        self.assertEqual(b.attempts, 3)

    def test_terminal_classifier_markers(self):
        self.assertTrue(_terminal_broker_answer(
            403, '{"message":"insufficient qty available for order '
                 '(requested: 1, available: 0)","held_for_orders":"7"}'))
        self.assertTrue(_terminal_broker_answer(
            403, '{"message":"insufficient balance for ADA"}'))
        self.assertFalse(_terminal_broker_answer(
            403, '{"message":"insufficient buying power"}'))
        self.assertFalse(_terminal_broker_answer(500, "wash trade"))


class TestAsterCryptoEmission(unittest.TestCase):
    SID = "aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct"

    def _view(self, positions):
        return {"positions": positions, "bars": {}, "funding": None,
                "now": "2026-10-29T00:00:00+00:00"}

    def test_foreign_positions_produce_no_exits(self):
        from desk3 import aster_crypto
        view = self._view([
            {"symbol": "FFIV", "qty": -796, "age_hours": 100},
            {"symbol": "SOXL", "qty": -6156, "age_hours": 100},
            {"symbol": "TWST", "qty": -7, "age_hours": 100}])
        self.assertEqual(aster_crypto.evaluate(self.SID, view), [])

    def test_own_position_exit_carries_broker_symbol(self):
        from desk3 import aster_crypto
        view = self._view([
            {"symbol": "ADA/USD", "qty": 27, "age_hours": 100},
            {"symbol": "FFIV", "qty": -796, "age_hours": 100}])
        out = aster_crypto.evaluate(self.SID, view)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].symbol, "ADA/USD")
        self.assertEqual(float(out[0].qty), 27.0)


if __name__ == "__main__":
    unittest.main()
