"""READINESS-DSP1-20261112 blockers (DEFECT-HUNT DSP-1, High).

Defect: a non-mismatch HTTP 422 was classified non-transient, yet
process_intent still wrote the intent to the durable pending store
before returning. The duplicate index never learned the verdict,
because broker_rejected_terminal was not in its indexed event set.
Next cycle the drain re-ran process_intent on the stored copy,
submitted the identical payload a second time, drew the identical
422, and only then removed the entry as drained_terminal. Live
proof counted 2026-11-12: 445 broker_rejected_terminal rows over
301 distinct intent ids, 144 carrying exactly 2 — the
fresh-plus-drain signature.

Cure: a non-transient submit failure (a deterministic verdict:
422 validation, a terminal 403 subclass) is consumed terminally in
process_intent — journaled broker_rejected_terminal, never
persisted to the pending store — and broker_rejected_terminal is
in the duplicate index event set, so the verdict spends the intent
id permanently. The broker-unavailable class (403 transient / 429
/ 5xx / network) still queues for the drain exactly as before.

Fail direction: proven on a worktree at the pre-cure HEAD — the
422 intent is queued, the store holds it, and the rebuilt
Dispatcher's drain submits it a second time (submit_count 2).
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.broker import FakeBroker


class HttpError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


class RejectingBroker(FakeBroker):
    def __init__(self, error):
        super().__init__(prices={"TEST": 10.0})
        self._error = error

    def submit_order(self, *a, **kw):
        self.submit_count += 1
        raise self._error


def _intent(iid="d1"):
    return {"intent_id": iid, "kind": "entry", "symbol": "TEST",
            "side": "buy", "qty": 1, "order_type": "market",
            "time_in_force": "day", "price_hint": 10.0}


def _disp(root, broker):
    from desk3.dispatcher import Dispatcher
    return Dispatcher(root, broker,
                      slices={"s1": {"capital_usd": 10000.0,
                                     "cash_usd": 10000.0}})


class TestDeterministicVerdictIsTerminal(unittest.TestCase):
    def test_422_never_queued_never_resubmitted(self):
        root = tempfile.mkdtemp()
        broker = RejectingBroker(HttpError(
            422, json.dumps({"code": 42210000,
                             "message": "asset not found"})))
        disp = _disp(root, broker)
        r = disp.process_intent(_intent(), "s1")
        self.assertEqual(r["status"], "rejected", r)
        self.assertEqual(broker.submit_count, 1)
        self.assertEqual(disp.pending_entries(), [])
        # Rebuilt dispatcher (next cycle): the verdict is spent.
        disp2 = _disp(root, broker)
        self.assertEqual(disp2.pending_entries(), [])
        self.assertEqual(disp2.drain_pending(), [])
        r2 = disp2.process_intent(_intent(), "s1")
        self.assertEqual(r2["status"], "duplicate", r2)
        self.assertEqual(broker.submit_count, 1)
        rows = disp2.journal_events()
        terms = [x for x in rows
                 if x.get("event") == "broker_rejected_terminal"
                 and x.get("intent_id") == "d1"]
        self.assertEqual(len(terms), 1, rows)

    def test_terminal_403_never_queued(self):
        root = tempfile.mkdtemp()
        broker = RejectingBroker(HttpError(
            403, json.dumps({"code": 40310000,
                             "message": "potential wash trade"})))
        disp = _disp(root, broker)
        r = disp.process_intent(_intent("d2"), "s1")
        self.assertEqual(r["status"], "rejected", r)
        self.assertEqual(disp.pending_entries(), [])
        disp2 = _disp(root, broker)
        self.assertEqual(disp2.drain_pending(), [])
        self.assertEqual(broker.submit_count, 1)

    def test_transient_failure_still_queues(self):
        root = tempfile.mkdtemp()
        broker = RejectingBroker(HttpError(503, "door down"))
        disp = _disp(root, broker)
        r = disp.process_intent(_intent("d3"), "s1")
        self.assertEqual(r["status"], "queued", r)
        self.assertTrue(r.get("transient"), r)
        self.assertEqual(len(disp.pending_entries()), 1)


if __name__ == "__main__":
    unittest.main()
