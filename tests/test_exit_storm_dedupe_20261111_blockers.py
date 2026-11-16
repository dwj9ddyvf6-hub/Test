"""EXIT-STORM DEDUPE blockers (CR-3, 2026-11-11; DIAGNOSIS.md S4).

The defect: eleven sleeves emit exit intents for lots the broker
book does not hold for them (or holds fully reserved by a resting
close). Every cycle the sleeve re-emits the same exit under a fresh
intent id, and the dispatcher journals a fresh terminal rejection
every time (lifetime intent_rejected counts of 83-91 per sleeve in
the S4 census; 532 intent_rejected rows in one 200 KB tail of the
live dispatcher journal on 2026-11-11). The rejection verdicts are
correct; the STORM is the defect: journal spam, per-cycle broker
book reads spent re-deciding a settled question, and for the
broker-side variant (leaps_momentum) a real wire submit every cycle
drawing the same held_for_orders 403.

The cure (desk3/dispatcher.py, EXIT-STORM-DEDUPE-20261111): the
first terminal exit verdict of the two storm classes
(exit_satisfied_no_broker_position, exit_already_resting_at_broker)
is journaled exactly as before and RECORDED in a per-session
suppression store keyed by (sleeve, symbol). A later same-session
exit for the same sleeve+symbol is answered from the CURRENT
broker book: if the book state behind the verdict is unchanged
(still no position, or still fully covered by resting closes) the
intent is consumed as exit_storm_suppressed with ONE journal row
per key per session; if the book has changed (a position appeared,
or coverage opened) the suppression clears and the exit is decided
on its merits, so a real exit can never be swallowed. A terminal
broker held_for_orders / insufficient-qty answer on an exit records
the same key. Suppression never crosses a session boundary.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402
from desk3.journal import read_lines  # noqa: E402


class BookBroker(FakeBroker):
    """Live-book double with a mutable book."""

    live_book = True

    def __init__(self, positions=None, resting=None):
        super().__init__(prices={"SPY": 100.0}, fill_mode="pending")
        self.positions = dict(positions or {})
        self.orders = {}
        for i, (sym, side, qty) in enumerate(resting or []):
            self.orders[f"r{i}"] = {
                "id": f"r{i}", "client_order_id": f"r{i}",
                "symbol": sym, "side": side, "qty": qty,
                "filled_qty": 0, "status": "accepted",
                "position_intent": "sell_to_close"}
        self.submits = 0

    def submit_order(self, *a, **kw):
        self.submits += 1
        return super().submit_order(*a, **kw)


def _disp(broker):
    root = tempfile.mkdtemp(prefix="storm-")
    return Dispatcher(root, broker, slices={},
                      session_date="2026-11-11")


def _exit(iid, symbol="SPY", qty=13.0):
    return {"intent_id": iid, "kind": "exit", "symbol": symbol,
            "side": "sell", "qty": qty, "order_type": "market",
            "position_intent": "sell_to_close",
            "time_in_force": "day", "limit_price": None,
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


class TestNoPositionStorm(unittest.TestCase):
    def test_repeat_exits_suppressed_after_first_verdict(self):
        b = BookBroker()
        d = _disp(b)
        r1 = d.process_intent(_exit("s1"), "grok_sr_spy")
        self.assertEqual(r1["status"], "rejected")
        self.assertEqual(r1["reason"],
                         "exit_satisfied_no_broker_position")
        r2 = d.process_intent(_exit("s2"), "grok_sr_spy")
        r3 = d.process_intent(_exit("s3"), "grok_sr_spy")
        self.assertEqual(r2["reason"], "exit_storm_suppressed")
        self.assertEqual(r3["reason"], "exit_storm_suppressed")
        # Exactly one terminal rejection row and one suppression
        # row for the key, however many repeats arrive.
        self.assertEqual(len(_rows(
            d, "intent_rejected",
            "exit_satisfied_no_broker_position")), 1)
        self.assertEqual(len(_rows(d, "exit_storm_suppressed")), 1)
        self.assertEqual(b.submits, 0)

    def test_position_appearing_clears_suppression(self):
        b = BookBroker()
        d = _disp(b)
        d.process_intent(_exit("s1"), "grok_sr_spy")
        r = d.process_intent(_exit("s2"), "grok_sr_spy")
        self.assertEqual(r["reason"], "exit_storm_suppressed")
        # The sleeve now actually holds a position (its entry
        # filled): the next exit must be decided on its merits.
        b.positions["SPY"] = 13.0
        # Next cycle: a fresh Dispatcher over the same root.
        d2 = Dispatcher(d.root, b, slices={},
                        session_date="2026-11-11")
        r = d2.process_intent(_exit("s3"), "grok_sr_spy")
        self.assertNotEqual(r.get("reason"), "exit_storm_suppressed")
        self.assertEqual(r["status"], "submitted")
        self.assertEqual(b.submits, 1)


class TestRestingStorm(unittest.TestCase):
    def test_fully_covered_exit_suppressed_until_coverage_opens(self):
        b = BookBroker(positions={"SPY": 13.0},
                       resting=[("SPY", "sell", 13.0)])
        d = _disp(b)
        r1 = d.process_intent(_exit("t1"), "teddy_orb_spy")
        self.assertEqual(r1["reason"], "exit_already_resting_at_broker")
        r2 = d.process_intent(_exit("t2"), "teddy_orb_spy")
        self.assertEqual(r2["reason"], "exit_storm_suppressed")
        self.assertEqual(len(_rows(
            d, "intent_rejected",
            "exit_already_resting_at_broker")), 1)
        # Coverage opens (the resting close filled/cancelled):
        # the exit is decided on its merits again.
        b.orders = {}
        d._book_cache = None
        r3 = d.process_intent(_exit("t3"), "teddy_orb_spy")
        self.assertNotEqual(r3.get("reason"), "exit_storm_suppressed")
        self.assertEqual(r3["status"], "submitted")

    def test_suppression_is_per_sleeve(self):
        b = BookBroker()
        d = _disp(b)
        d.process_intent(_exit("u1"), "grok_sr_spy")
        r = d.process_intent(_exit("u2"), "teddy_orb_spy")
        self.assertEqual(r["reason"],
                         "exit_satisfied_no_broker_position")


if __name__ == "__main__":
    unittest.main()
