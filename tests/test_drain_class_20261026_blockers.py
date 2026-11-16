"""Blockers: DRAIN-CLASS-20261026 — a broker_unavailable-class
failure at pending-drain time is NEVER a terminal broker answer.

Pre-cure defect (parent-proven live 2026-10-26): the dispatcher's
submit classification treated only status None / 429 / 5xx as
transient, so an HTTP 403 fell into `queued + not transient` and
drain_pending() removed the entry as `drained_terminal` — 40 pending
intents were discarded with reason 'FetchError:HTTP 403' while the
broker account was merely buying-power exhausted (ORDER-403).

Cure: desk3/dispatcher.py classifies 403 alongside 429 / 5xx /
network (status None) as the broker-unavailable class EVERYWHERE
the two classes are distinguished (the bounded in-call retry and
the drain); at drain time such outcomes leave the entry IN the
store and are journaled `drained_deferred` with the error. Only a
genuine terminal broker rejection (a parsed error outside that
class, e.g. 422 validation) may drain_terminal.

Fail direction: on the pre-cure classifier the 403 cases fail
(attempts=1, transient=False, drain -> drained_terminal, store
emptied); 429/5xx/network already deferred and 422 already drained
terminal, and those rows pin that the cure does not over-broaden.
See BUGLOG_2026-10-26.md.
"""
import hashlib, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
TODAY = "2026-10-26"


def _intent(iid="dclass-1"):
    return {"intent_id": iid, "kind": "entry", "symbol": "SPY",
            "side": "buy", "qty": 1, "order_type": "market",
            "limit_price": None, "price_hint": 100.0,
            "time_in_force": "day"}


def _disp(root, broker):
    from desk3.dispatcher import Dispatcher
    return Dispatcher(root, broker,
                      slices={"s": {"capital_usd": 10000.0,
                                    "cash_usd": 10000.0}},
                      price_lookup=lambda s: 100.0,
                      session_date=TODAY)


class _Fail:
    """Broker whose submit always raises the given failure."""

    def __init__(self, exc_factory):
        self.exc_factory = exc_factory
        self.attempts = 0

    def submit_order(self, *a, **k):
        self.attempts += 1
        raise self.exc_factory()

    def get_order_by_client_id(self, coid):  # pragma: no cover
        raise AssertionError("no order may exist while submit fails")


def _http(status):
    from desk3.netfetch import FetchError
    return lambda: FetchError(
        status, "https://paper-api.alpaca.markets/v2/orders")


class TestUnavailableClassAtDrain(unittest.TestCase):
    def _run_case(self, exc_factory, marker):
        root = tempfile.mkdtemp()
        broker = _Fail(exc_factory)
        d1 = _disp(root, broker)
        r = d1.process_intent(_intent(), "s")
        self.assertEqual(r["status"], "queued")
        self.assertTrue(r["transient"],
                        f"{marker}: submit must classify unavailable")
        self.assertEqual(len(d1.pending_store.load()), 1)
        d2 = _disp(root, broker)  # next cycle's fresh Dispatcher
        out = d2.drain_pending()
        self.assertEqual([x["status"] for x in out], ["drained_deferred"],
                         f"{marker}: drain must defer, never terminate")
        self.assertEqual(len(d2.pending_store.load()), 1,
                         f"{marker}: entry must STAY in the store")
        events = d2.journal_events()
        self.assertFalse([e for e in events
                          if e["event"] == "drained_terminal"], marker)
        deferred = [e for e in events if e["event"] == "drained_deferred"]
        self.assertEqual(len(deferred), 1, marker)
        self.assertIn(marker, str(deferred[0].get("error")
                                  or deferred[0].get("reason")))

    def test_403_at_drain_defers_and_entry_stays(self):
        self._run_case(_http(403), "403")

    def test_429_at_drain_defers_and_entry_stays(self):
        self._run_case(_http(429), "429")

    def test_5xx_at_drain_defers_and_entry_stays(self):
        self._run_case(_http(503), "503")

    def test_network_error_at_drain_defers_and_entry_stays(self):
        self._run_case(lambda: ConnectionError("door_down"), "door_down")


class TestTerminalClassAtDrain(unittest.TestCase):
    def test_422_at_drain_is_terminal_and_removed(self):
        # READINESS-DSP1-20261112 supersession, named: the fresh
        # path no longer persists a 422 at all (the verdict is
        # consumed terminally in process_intent — persisting it
        # was DSP-1: the drain submitted the identical payload a
        # second time). The pre-cure form of this test queued the
        # intent fresh, then drained it. The drain half still has
        # a live contract — entries the store already holds (from
        # older code, or queued while transient) whose drain-time
        # answer is a 422 must end drained_terminal and be removed
        # — so the entry is seeded into the store directly, in the
        # store's own shape, and drained. The fresh-path half pins
        # the new contract beside it.
        root = tempfile.mkdtemp()
        broker = _Fail(_http(422))
        d1 = _disp(root, broker)
        r = d1.process_intent(_intent(), "s")
        self.assertEqual(r["status"], "rejected")
        self.assertFalse(r["transient"])
        self.assertEqual(broker.attempts, 1)  # 422 is never retried
        self.assertEqual(d1.pending_store.load(), [])
        from desk3.models import client_order_id
        # A distinct intent id: the stored entry models one queued
        # while transient, with no terminal verdict on record yet
        # (seeding the fresh case's own id would make the drain
        # answer it as a duplicate of the spent verdict — also a
        # removal, but not this test's path).
        intent = _intent("dclass-stored")
        d1.pending_store.add({
            "intent": intent, "sleeve_id": "s",
            "client_order_id": client_order_id(
                "s", intent["intent_id"]),
            "session_date": TODAY, "attempts": 1,
            "last_error": "FetchError:HTTP 422",
            "queued_at": "2026-10-26T00:00:00+00:00"})
        d2 = _disp(root, broker)
        out = d2.drain_pending()
        self.assertEqual([x["status"] for x in out], ["drained_terminal"])
        self.assertEqual(d2.pending_store.load(), [])
        self.assertEqual(broker.attempts, 2)  # one drain presentation
        rows = [e for e in d2.journal_events()
                if e["event"] == "drained_terminal"]
        self.assertEqual(len(rows), 1)
        self.assertIn("broker_rejected_terminal", rows[0]["reason"])


class TestRailsUntouched(unittest.TestCase):
    def test_saty_sol_byte_identical(self):
        h = hashlib.sha256(open(os.path.join(
            ROOT, "sleeves", "saty_sol.py"), "rb").read()).hexdigest()
        self.assertTrue(h.startswith("36e306c6"), h)


if __name__ == "__main__":
    unittest.main()
