"""HEALTH-ORDERS-PLACED-20261116 regression blockers (Lane E,
desk full audit 2026-11-16).

Defect: desk3/cycle.py incremented orders_placed for every
intent handed to Dispatcher.process_intent regardless of the
returned status, so a rejected intent counted as an order; and
the roll is per-cycle and overwritten, so health showed only
the latest cycle (a sleeve that filled in an earlier cycle read
0, a sleeve whose current intents were all rejected read 1).

Cure: orders_placed counts only dispatcher results with status
submitted/filled; sibling counters intents_total and
intents_rejected keep refusals visible; and a journal-derived
session-cumulative orders_placed_session per sleeve (counted
from the dispatcher journal's order_submitted rows across all
journal generations, the same generations the fill-ledger build
reads) rides the roll into health alongside the per-cycle figure.

Fail direction: pre-cure the fixture cycle below reads
orders_placed == 3 in cycle 1 (the rejected intent counted),
there are no intents_* counters and no orders_placed_session
anywhere, and the session-derivation helper does not exist.
"""
import json
import os
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.broker import FakeBroker  # noqa: E402
from desk3.cycle import Desk  # noqa: E402

FIXTURE = """
from datetime import datetime

def evaluate(view, ctx):
    now = datetime.fromisoformat(str(view["now"]).replace("Z", "+00:00"))
    if (now.hour, now.minute) != (15, 0):
        return []
    base = {"kind": "entry", "side": "buy", "order_type": "market",
            "time_in_force": "day", "price_hint": 100.0}
    return [
        dict(base, intent_id="healthfix-20261116T150000-1",
             symbol="FILL", qty=1),
        dict(base, intent_id="healthfix-20261116T150000-2",
             symbol="PEND", qty=1),
        dict(base, intent_id="healthfix-20261116T150000-3",
             symbol="REJ", qty=100000),
    ]
"""


class _MixedBroker(FakeBroker):
    """FILL fills on read-back; PEND stays accepted (submitted,
    never filled); everything else follows FakeBroker."""

    def get_order_by_client_id(self, client_order_id):
        order = self.orders[client_order_id]
        if order["symbol"] == "PEND":
            return dict(order, status="accepted")
        return super().get_order_by_client_id(client_order_id)


def _desk(tmp):
    with open(os.path.join(tmp, "healthfix.py"), "w") as fh:
        fh.write(textwrap.dedent(FIXTURE))
    broker = _MixedBroker(prices={"FILL": 100.0, "PEND": 100.0,
                                  "REJ": 100.0})
    desk = Desk(tmp, broker=broker, sleeve_path=tmp, timeout_s=10.0)
    desk.add_producer("warm", lambda c: {"bars": {}}, ["bars"],
                      10 ** 9)
    desk.add_sleeve("healthfix", "healthfix", ["bars"], 300, 10000.0)
    return desk


def _at(hh, mm):
    return datetime(2026, 11, 16, hh, mm, tzinfo=timezone.utc)


class TestFixtureCycleCounts(unittest.TestCase):
    def test_counts_and_session_accumulation(self):
        tmp = tempfile.mkdtemp()
        desk = _desk(tmp)
        roll1 = desk.run_cycle(now=_at(15, 0))
        e1 = roll1["sleeves"]["healthfix"]
        self.assertEqual(e1["intents_total"], 3)
        self.assertEqual(e1["orders_placed"], 2)      # submitted+filled
        self.assertEqual(e1["intents_rejected"], 1)
        self.assertEqual(e1["orders_placed_session"], 2)
        roll2 = desk.run_cycle(now=_at(15, 20))
        e2 = roll2["sleeves"]["healthfix"]
        # per-cycle figure reflects the latest cycle only...
        self.assertEqual(e2["orders_placed"], 0)
        self.assertEqual(e2["intents_total"], 0)
        self.assertEqual(e2["intents_rejected"], 0)
        # ...while the session figure accumulates across cycles
        self.assertEqual(e2["orders_placed_session"], 2)
        health = json.load(open(os.path.join(tmp, "state",
                                             "health.json")))
        he = health["sleeves"]["healthfix"]
        self.assertEqual(he["orders_placed"], 0)
        self.assertEqual(he["orders_placed_session"], 2)
        self.assertEqual(he["intents_rejected"], 0)


class TestSessionDerivation(unittest.TestCase):
    def _write_journal(self, tmp, rows, suffix=""):
        path = os.path.join(tmp, "dispatcher.jsonl" + suffix)
        with open(path, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        return os.path.join(tmp, "dispatcher.jsonl")

    def test_recorded_six_sleeve_counts(self):
        from desk3.cycle import orders_placed_session_by_sleeve
        tmp = tempfile.mkdtemp()

        def sub(sid, n, day="20261116"):
            return {"event": "order_submitted",
                    "intent_id": f"{sid}-{day}T180438-{n}",
                    "sleeve": sid, "client_order_id": f"v3-{sid}-{n}",
                    "symbol": "SPY"}

        rows = [sub("aster_etf_qld_buy_hold", 1),
                sub("aster_etf_qqq_buy_hold", 1),
                sub("aster_etf_qqq_qld_buy_hold", 1),
                sub("aster_etf_smh_hold_c098", 1),
                sub("aster_etf_spy_buy_hold", 1),
                # a prior-session row must not count
                sub("aster_etf_spy_buy_hold", 9, day="20261115"),
                # a duplicate journaling of one intent counts once
                sub("aster_etf_qld_buy_hold", 1),
                # m150: rejected only today -> zero submitted
                {"event": "intent_rejected",
                 "intent_id": "aster_etf_smh_hold_m150-20261116T180438-1",
                 "sleeve": "aster_etf_smh_hold_m150",
                 "reason": "insufficient_slice_bp"}]
        path = self._write_journal(tmp, rows)
        # the second qqq_qld submission lives in a rotated
        # generation: all generations are read, oldest first
        self._write_journal(
            tmp, [sub("aster_etf_qqq_qld_buy_hold", 2)], suffix=".1")
        got = orders_placed_session_by_sleeve(path, "2026-11-16")
        self.assertEqual(got.get("aster_etf_qld_buy_hold"), 1)
        self.assertEqual(got.get("aster_etf_qqq_buy_hold"), 1)
        self.assertEqual(got.get("aster_etf_qqq_qld_buy_hold"), 2)
        self.assertEqual(got.get("aster_etf_smh_hold_c098"), 1)
        self.assertEqual(got.get("aster_etf_spy_buy_hold"), 1)
        self.assertEqual(got.get("aster_etf_smh_hold_m150", 0), 0)

    def test_missing_journal_yields_empty(self):
        from desk3.cycle import orders_placed_session_by_sleeve
        got = orders_placed_session_by_sleeve(
            os.path.join(tempfile.mkdtemp(), "dispatcher.jsonl"),
            "2026-11-16")
        self.assertEqual(got, {})


if __name__ == "__main__":
    unittest.main()
