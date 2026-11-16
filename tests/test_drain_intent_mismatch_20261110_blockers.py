"""DRAIN-INTENT-MISMATCH-20261110 regression blockers (TOTAL
APPLICATION W4; census DSK-12 MEDIUM).

The defect (diagnosed 2026-11-10 from the dispatcher journal and
the broker book): exits specified sell_to_close drew 27 broker
rejections in 48 h, all HTTP 422 code 42210000 "position intent
mismatch, inferred: sell_to_open, specified: sell_to_close" (106
rows all-time in the current journal generation). EVERY event is
duplicated per unique intent: the same client_order_id carries
TWO broker_unavailable rows, TWO broker_rejected_terminal rows
and then a drained_terminal(exit_satisfied_no_broker_position).

Mechanism, proven from the journal pairs and the code path:
a close intent whose submit draws the mismatch 422 was treated as
a broker-unavailable failure and QUEUED to the durable pending
store even though the exit pre-flight (BLOCKED-EXIT-20261029) had
already consumed the intent against the broker book; the drain
then re-presented the ORIGINAL intent, where (a) the by-then-flat
book made the re-check terminate it locally as satisfied (the
drained_terminal rows), while the duplicate wire pair came from
the drain re-presenting against the first attempt's warm book
cache / a remainder the broker had reserved. A deterministic
verdict was being retried as if it were a transient outage, and
each retry journaled a second, contradictory terminal record for
one consumption.

The cure (desk3/dispatcher.py): a submit error whose body carries
"position intent mismatch" returns TERMINALLY from process_intent
(reason position_intent_mismatch_terminal, one terminal journal
row, nothing queued); and the drain HOLDS any legacy pending entry
whose last_error carries the mismatch (pending_drain_deferred /
position_intent_mismatch_hold, never submitted, not charged to
the cap), so a queued copy can never be re-presented as-is.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402
from desk3.journal import read_lines  # noqa: E402
from desk3.netfetch import FetchError  # noqa: E402


class MismatchBroker(FakeBroker):
    """Live-book double: the broker holds SPY long, fully reserved
    by a resting sell, so the pre-flight clamps the exit to the
    uncovered remainder and submits it; the broker answers the
    submit with the deterministic mismatch 422 (its reserve view
    disagrees), exactly the live DSK-12 shape."""
    live_book = True

    def __init__(self):
        super().__init__(prices={"SPY": 100.0}, fill_mode="pending")
        self.positions = {"SPY": 13.0}
        self.mismatch_submits = 0
        self.orders["resting"] = {
            "id": "r1", "client_order_id": "resting", "symbol": "SPY",
            "side": "sell", "qty": 12, "filled_qty": 0,
            "status": "accepted", "position_intent": "sell_to_close"}

    def submit_order(self, *a, **kw):
        self.mismatch_submits += 1
        body = json.dumps({
            "code": 42210000,
            "message": "position intent mismatch, inferred: "
                       "sell_to_open, specified: sell_to_close"})
        raise FetchError(422, "https://paper-api.alpaca.markets"
                              "/v2/orders", body=body)


def _disp(broker):
    root = tempfile.mkdtemp(prefix="mismatch-")
    return Dispatcher(root, broker, slices={})


def _exit(iid, symbol="SPY", qty=13.0):
    return {"intent_id": iid, "kind": "exit", "symbol": symbol,
            "side": "sell", "qty": qty, "order_type": "market",
            "position_intent": "sell_to_close",
            "time_in_force": "day", "limit_price": None,
            "stop_price": None, "price_hint": None}


def _journal(disp):
    return read_lines(disp.djournal)


class TestMismatchIsTerminalAtFirstAnswer(unittest.TestCase):
    def test_mismatch_exit_is_consumed_not_queued(self):
        b = MismatchBroker()
        d = _disp(b)
        r = d.process_intent(_exit("m1"), "ema_vwap")
        self.assertEqual(r["status"], "rejected")
        self.assertEqual(r["reason"],
                         "position_intent_mismatch_terminal")
        # Nothing queued: the pending store and the in-memory
        # queue stay empty (pre-cure: the entry was persisted).
        self.assertEqual(d.pending_store.load(), [])
        self.assertEqual(d._pending, [])
        rows = _journal(d)
        terms = [x for x in rows
                 if x.get("event") == "broker_rejected_terminal"]
        self.assertEqual(len(terms), 1, rows)
        self.assertEqual(terms[0]["broker_code"], 42210000)
        unavail = [x for x in rows
                   if x.get("event") == "broker_unavailable"]
        self.assertEqual(unavail, [], rows)

    def test_mismatch_submit_attempted_once(self):
        b = MismatchBroker()
        d = _disp(b)
        d.process_intent(_exit("m2"), "ema_vwap")
        self.assertEqual(b.mismatch_submits, 1)


class TestMismatchPendingEntryIsHeld(unittest.TestCase):
    def test_queued_mismatch_entry_is_never_represented(self):
        b = MismatchBroker()
        d = _disp(b)
        intent = _exit("m3")
        d.pending_store.add({
            "intent": intent, "sleeve_id": "ema_vwap",
            "client_order_id": "v3-ema_vwap-m3",
            "session_date": d.session_date, "attempts": 1,
            "last_error": "FetchError:HTTP 422",
            "queued_at": "t"})
        # The legacy entry's real last_error (what process_intent
        # persisted) carries the broker body class in its text via
        # the error string; seed it exactly as the pre-cure path
        # stored a mismatch failure.
        entry = d.pending_store.load()[0]
        entry["last_error"] = (
            'FetchError:{"code":42210000,"message":"position intent '
            'mismatch, inferred: sell_to_open, specified: '
            'sell_to_close"}')
        d.pending_store.update(entry)
        results = d.drain_pending(cap=10)
        self.assertEqual(b.mismatch_submits, 0)
        self.assertEqual(len(d.pending_store.load()), 1)
        self.assertEqual(results[0]["status"], "deferred")
        self.assertEqual(results[0]["reason"],
                         "position_intent_mismatch_hold")
        rows = _journal(d)
        holds = [x for x in rows
                 if x.get("event") == "pending_drain_deferred"
                 and x.get("reason")
                 == "position_intent_mismatch_hold"]
        self.assertEqual(len(holds), 1, rows)


if __name__ == "__main__":
    unittest.main()
