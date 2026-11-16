"""Blockers: BROKER-PENDING-DRAIN-20261026 — intents that exhaust the
dispatcher’s bounded in-call retry must PERSIST and DRAIN, not die
with the per-cycle Dispatcher.

Pre-cure defect (proven by LIVE-REMAINDERS-20261026 diagnosis): the
retry_pending queue lived only in Dispatcher memory; cycle.py builds
a fresh Dispatcher every cycle, so every queued intent was discarded
at cycle end.

Cure: desk3/dispatcher.py PendingStore (state/broker_pending.jsonl
append + state/broker_pending.json snapshot, flock-guarded) as the
single source of truth; drain_pending() at the start of each dispatch
cycle (desk3/cycle.py) re-runs the same dispatch path for
current-session entries ONLY, under the ORIGINAL client_order_id;
stale-session entries are expired_unsent and never submitted;
DRAIN_CAP=20 bounds per-cycle drain work.

Fail direction: on the pre-cure tree there is no pending store and no
drain_pending — (a) finds no store file, (b)/(c)/(d)/(e) fail/error;
see BUGLOG_2026-10-26.md.
"""
import hashlib, json, os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
TODAY = "2026-10-26"
YESTERDAY = "2026-10-25"


def _intent(iid="drain-1"):
    return {"intent_id": iid, "kind": "entry", "symbol": "SPY",
            "side": "buy", "qty": 1, "order_type": "market",
            "limit_price": None, "price_hint": 100.0,
            "time_in_force": "day"}


def _disp(root, broker, session=TODAY):
    from desk3.dispatcher import Dispatcher
    return Dispatcher(root, broker,
                      slices={"s": {"capital_usd": 10000.0,
                                    "cash_usd": 10000.0}},
                      price_lookup=lambda s: 100.0,
                      session_date=session)


class _Down:
    """Broker whose submit always fails transiently (503)."""

    def __init__(self):
        self.attempts = 0

    def submit_order(self, *a, **k):
        from desk3.netfetch import FetchError
        self.attempts += 1
        raise FetchError(503, "https://paper-api.alpaca.markets/v2/orders")

    def get_order_by_client_id(self, coid):  # pragma: no cover
        raise AssertionError("no order may exist while the door is down")


class _Bad422:
    def __init__(self):
        self.attempts = 0

    def submit_order(self, *a, **k):
        from desk3.netfetch import FetchError
        self.attempts += 1
        raise FetchError(422, "https://paper-api.alpaca.markets/v2/orders")

    def get_order_by_client_id(self, coid):  # pragma: no cover
        raise AssertionError("no order may exist on a 422")


class TestPersistNotLost(unittest.TestCase):
    def test_a_exhausted_intent_persisted_to_store(self):
        from desk3.broker import FakeBroker  # noqa: F401 (parity import)
        root = tempfile.mkdtemp()
        broker = _Down()
        d = _disp(root, broker)
        r = d.process_intent(_intent(), "s")
        self.assertEqual(r["status"], "queued")
        self.assertEqual(broker.attempts, 3)  # bounded in-call retry first
        jsonl = os.path.join(root, "state", "broker_pending.jsonl")
        snap = os.path.join(root, "state", "broker_pending.json")
        self.assertTrue(os.path.exists(jsonl), "pending JSONL missing")
        self.assertTrue(os.path.exists(snap), "pending snapshot missing")
        entries = d.pending_store.load()
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["intent"], _intent())
        self.assertEqual(e["sleeve_id"], "s")
        self.assertEqual(e["client_order_id"], "v3-s-drain-1")  # ORIGINAL id
        self.assertEqual(e["session_date"], TODAY)
        self.assertEqual(e["attempts"], 3)
        self.assertIn("503", e["last_error"])
        with open(snap) as fh:
            self.assertEqual(json.load(fh), entries)


class TestFreshDispatcherDrains(unittest.TestCase):
    def test_b_fresh_dispatcher_drains_same_client_order_id(self):
        from desk3.broker import FakeBroker
        root = tempfile.mkdtemp()
        d1 = _disp(root, _Down())
        self.assertEqual(d1.process_intent(_intent(), "s")["status"],
                         "queued")
        broker = FakeBroker(prices={"SPY": 100.0})
        d2 = _disp(root, broker)  # simulates the NEXT cycle’s Dispatcher
        out = d2.drain_pending()
        self.assertEqual([x["status"] for x in out], ["filled"])
        self.assertEqual(list(broker.orders), ["v3-s-drain-1"])
        self.assertEqual(broker.submit_count, 1)
        self.assertEqual(d2.pending_store.load(), [])
        events = [e["event"] for e in d2.journal_events()]
        self.assertIn("drained", events)

    def test_f_terminal_reject_on_drain_removes_and_journals(self):
        # READINESS-DSP1-20261112 supersession, named: the fresh
        # path no longer persists a 422 (the verdict is consumed
        # terminally in process_intent; persisting it was DSP-1).
        # The drain contract this test exists for — a stored entry
        # whose drain-time answer is terminal is removed and
        # journaled drained_terminal — is exercised by seeding the
        # store directly, in the store's own shape, as entries
        # written by older code arrive. The fresh-path half pins
        # the new contract beside it.
        root = tempfile.mkdtemp()
        broker = _Bad422()
        d1 = _disp(root, broker)
        self.assertEqual(d1.process_intent(_intent(), "s")["status"],
                         "rejected")
        self.assertEqual(d1.pending_store.load(), [])
        from desk3.models import client_order_id
        intent = _intent("drain-stored")
        d1.pending_store.add({
            "intent": intent, "sleeve_id": "s",
            "client_order_id": client_order_id(
                "s", intent["intent_id"]),
            "session_date": TODAY, "attempts": 1,
            "last_error": "FetchError:HTTP 422",
            "queued_at": "2026-10-26T00:00:00+00:00"})
        self.assertEqual(len(d1.pending_store.load()), 1)
        d2 = _disp(root, broker)
        out = d2.drain_pending()
        self.assertEqual([x["status"] for x in out], ["drained_terminal"])
        self.assertEqual(d2.pending_store.load(), [])
        rows = [e for e in d2.journal_events()
                if e["event"] == "drained_terminal"]
        self.assertEqual(len(rows), 1)
        self.assertIn("broker_rejected_terminal", rows[0]["reason"])


class TestStaleSessionSafety(unittest.TestCase):
    def test_c_stale_entry_expired_unsent_never_submitted(self):
        from desk3.broker import FakeBroker
        root = tempfile.mkdtemp()
        d1 = _disp(root, _Down(), session=YESTERDAY)
        self.assertEqual(d1.process_intent(_intent(), "s")["status"],
                         "queued")
        broker = FakeBroker(prices={"SPY": 100.0})
        d2 = _disp(root, broker, session=TODAY)
        out = d2.drain_pending()
        self.assertEqual([x["status"] for x in out], ["expired_unsent"])
        self.assertEqual(broker.submit_count, 0)  # NEVER reaches the broker
        self.assertEqual(d2.pending_store.load(), [])
        self.assertIn("expired_unsent",
                      [e["event"] for e in d2.journal_events()])


class TestHaltGateOnDrain(unittest.TestCase):
    def test_d_halted_sleeve_pending_not_submitted_while_halted(self):
        from desk3.broker import FakeBroker
        root = tempfile.mkdtemp()
        d1 = _disp(root, _Down())
        d1.process_intent(_intent(), "s")
        broker = FakeBroker(prices={"SPY": 100.0})
        d2 = _disp(root, broker)
        d2.halted_sleeves = {"s"}  # A15 reconcile halt
        out = d2.drain_pending()
        self.assertEqual([x["status"] for x in out], ["deferred"])
        self.assertEqual(broker.submit_count, 0)
        self.assertEqual(len(d2.pending_store.load()), 1)  # stays pending
        d2.halted_sleeves = set()  # halt lifts, same session: it drains
        out2 = d2.drain_pending()
        self.assertEqual([x["status"] for x in out2], ["filled"])
        self.assertEqual(d2.pending_store.load(), [])


class TestDuplicateDrainSafety(unittest.TestCase):
    def test_e_draining_twice_submits_once_and_empties_store(self):
        from desk3.broker import FakeBroker
        root = tempfile.mkdtemp()
        d1 = _disp(root, _Down())
        d1.process_intent(_intent(), "s")
        broker = FakeBroker(prices={"SPY": 100.0})
        d2 = _disp(root, broker)
        self.assertEqual([x["status"] for x in d2.drain_pending()],
                         ["filled"])
        self.assertEqual(d2.drain_pending(), [])  # second drain: nothing
        self.assertEqual(broker.submit_count, 1)  # broker idempotence held
        self.assertEqual(len(broker.orders), 1)
        self.assertEqual(d2.pending_store.load(), [])

    def test_g_drain_cap_bounds_per_cycle_work(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import DRAIN_CAP
        from desk3.models import client_order_id
        root = tempfile.mkdtemp()
        broker = FakeBroker(prices={"SPY": 100.0})
        d = _disp(root, broker)
        total = DRAIN_CAP + 5
        for n in range(total):
            iid = f"cap-{n}"
            d.pending_store.add(
                {"intent": _intent(iid), "sleeve_id": "s",
                 "client_order_id": client_order_id("s", iid),
                 "session_date": TODAY, "attempts": 3,
                 "last_error": "FetchError:503", "queued_at": "t"})
        out = d.drain_pending()
        self.assertEqual(len(out), DRAIN_CAP)  # bounded per cycle
        self.assertEqual(len(d.pending_store.load()), 5)  # rest stay queued
        out2 = d.drain_pending()
        self.assertEqual(len(out2), 5)
        self.assertEqual(d.pending_store.load(), [])
        self.assertEqual(broker.submit_count, total)


class TestRailsUntouched(unittest.TestCase):
    def test_saty_sol_byte_identical(self):
        h = hashlib.sha256(open(os.path.join(
            ROOT, "sleeves", "saty_sol.py"), "rb").read()).hexdigest()
        self.assertTrue(h.startswith("36e306c6"), h)


if __name__ == "__main__":
    unittest.main()
