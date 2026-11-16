"""DRAIN-HOLD-20261104 blockers.

Live failure class, 2026-11-03/04: options exits queued in the
pending store after transient submit failures were attempted at
the pre-open drain, where the door's market-hours verdict (422,
not in the broker-unavailable class) classified them
drained_terminal and dropped them. They survived only because
sleeves re-emit exits every cycle while holding the position.

Cures: (1) drain_pending holds any pending OCC market order
while the options market is closed: the door's answer in that
window is deterministic, so the entry is deferred by name
(options_market_closed_hold), kept in the store, and not charged
to the drain cap. (2) Entries that exhaust MAX_DRAIN_ATTEMPTS
drain attempts end drained_terminal (attempts_exhausted) instead
of retrying forever. (3) PendingStore.add enforces the long
declared but unenforced MAX_PENDING_ENTRIES cap by dropping the
oldest entries.

Fail direction: pre-cure there is no hold (the pre-open drain
attempts the exit and the entry leaves the store), no attempts
cap, and the store grows past MAX_PENDING_ENTRIES.
"""
import os, sys, tempfile, unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import desk3.dispatcher as disp_mod  # noqa: E402
from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher, PendingStore  # noqa: E402

ET = ZoneInfo("America/New_York")
SYM = "SPY261204P00752000"
PREOPEN = datetime(2026, 11, 4, 3, 0, tzinfo=ET)
INHOURS = datetime(2026, 11, 4, 10, 0, tzinfo=ET)


def _exit_intent(iid="exit-1"):
    return {"intent_id": iid, "kind": "exit", "symbol": SYM,
            "side": "sell", "qty": 6, "position_intent": "sell_to_close",
            "order_type": "market"}


def _disp(now):
    root = tempfile.mkdtemp(prefix="drain-test-")
    broker = FakeBroker(prices={SYM: 12.0})
    disp = Dispatcher(root, broker, session_date="2026-11-04",
                      now_fn=lambda: now)
    return disp, broker


def _seed(disp, attempts=0, iid="exit-1"):
    intent = _exit_intent(iid)
    coid = "coid-" + iid
    disp.pending_store.add(
        {"intent": intent, "sleeve_id": "saty_day",
         "client_order_id": coid, "session_date": "2026-11-04",
         "attempts": attempts,
         "last_error": "FetchError:422 options market orders are "
                       "only allowed during market hours",
         "queued_at": "2026-11-04T07:00:00+00:00"})
    return coid


class DrainHoldTests(unittest.TestCase):
    def test_preopen_drain_holds_options_market_exit(self):
        disp, broker = _disp(PREOPEN)
        coid = _seed(disp)
        results = disp.drain_pending()
        self.assertEqual(broker.submit_count, 0)
        self.assertEqual([e["client_order_id"]
                          for e in disp.pending_store.load()], [coid])
        self.assertEqual(results[0]["status"], "deferred")
        self.assertEqual(results[0]["reason"],
                         "options_market_closed_hold")
        rows = [r for r in disp.journal_events()
                if r.get("event") == "pending_drain_deferred"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason"], "options_market_closed_hold")

    def test_inhours_drain_submits_the_held_exit(self):
        disp, broker = _disp(INHOURS)
        _seed(disp)
        disp.drain_pending()
        self.assertEqual(broker.submit_count, 1)
        self.assertEqual(disp.pending_store.load(), [])

    def test_attempts_exhausted_drains_terminal(self):
        disp, broker = _disp(INHOURS)
        _seed(disp, attempts=disp_mod.MAX_DRAIN_ATTEMPTS)
        results = disp.drain_pending()
        self.assertEqual(broker.submit_count, 0)
        self.assertEqual(disp.pending_store.load(), [])
        self.assertEqual(results[0]["status"], "drained_terminal")
        self.assertEqual(results[0]["reason"], "attempts_exhausted")


class PendingCapTests(unittest.TestCase):
    def test_add_enforces_max_pending_entries(self):
        old = disp_mod.MAX_PENDING_ENTRIES
        disp_mod.MAX_PENDING_ENTRIES = 5
        self.addCleanup(setattr, disp_mod, "MAX_PENDING_ENTRIES", old)
        root = tempfile.mkdtemp(prefix="pending-cap-")
        store = PendingStore(os.path.join(root, "state"))
        for i in range(7):
            store.add({"intent": {"intent_id": f"i-{i}"},
                       "sleeve_id": "s", "client_order_id": f"c-{i}",
                       "session_date": "2026-11-04", "attempts": 0,
                       "last_error": None, "queued_at": "t"})
        kept = [e["client_order_id"] for e in store.load()]
        self.assertEqual(kept, ["c-2", "c-3", "c-4", "c-5", "c-6"])


if __name__ == "__main__":
    unittest.main()
