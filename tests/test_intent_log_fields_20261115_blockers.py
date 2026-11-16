"""INTENT-LOG-FIELDS-20261115 regression blockers.

Defect (proven 2026-11-15 by the Chaos Lab Lane 3 census over the
estate's own logs): dispatcher intent_rejected records and per-sleeve
journal intent records carried only event, intent_id, reason/result
and sleeve — no symbol, no side, no reference price. The rejected
population (2,354 dispatcher rejections, 773 of them the economic
near-miss class insufficient_slice_bp) could therefore never be
graded as a shadow portfolio, and the 71,495-row journal intent
history yielded no (sleeve, symbol, timestamp) triples for
conjunction or lead-lag analysis.

Cure: desk3/dispatcher.py _reject (the single funnel for
intent_rejected rows) stamps symbol, side and ref_price on every
row — ref_price from the caller's authoritative price when one was
computed (the buying-power gate passes its own price at the
insufficient_slice_bp call site), else the intent's limit_price,
else its price_hint; the inline insufficient_options_bp_csp row
carries the same contract; desk3/cycle.py stamps symbol, side and
ref_price (limit_price else price_hint) on the journal intent
record at emission.

Fail direction: on the pre-cure writers every assertion below on
symbol/side/ref_price fails — the keys do not exist on the rows.
Proven on a preserved pre-cure copy of desk3/dispatcher.py and
desk3/cycle.py in /tmp (see BUGLOG_2026-11-15.md).
"""
import json
import os
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.broker import FakeBroker  # noqa: E402
from desk3.cycle import Desk  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402
from desk3.journal import read_lines  # noqa: E402

PRICE = 100.0
SLICES = {"sA": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


def _disp(tmp, halted=()):
    broker = FakeBroker(prices={"QQQ": PRICE})
    d = Dispatcher(tmp, broker, slices=dict(SLICES),
                   price_lookup=lambda s: PRICE)
    d.halted_sleeves = set(halted)
    return d


def _rejected_rows(disp, intent_id):
    return [r for r in read_lines(disp.djournal)
            if r.get("event") == "intent_rejected"
            and r.get("intent_id") == intent_id]


class TestDispatcherRejectionFields(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_slice_bp_rejection_carries_gate_price(self):
        # Market entry with NO limit_price and NO price_hint: the
        # only price in the building is the dispatcher's own lookup,
        # and that is the price the BP gate refused on. The record
        # must carry it, or the near-miss stays unmarkable.
        d = _disp(self.tmp)
        intent = {"intent_id": "ilf1", "kind": "entry",
                  "symbol": "QQQ", "side": "buy", "qty": 200,
                  "order_type": "market",
                  "position_intent": "buy_to_open"}
        r = d.process_intent(intent, "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "insufficient_slice_bp"))
        rows = _rejected_rows(d, "ilf1")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "QQQ")
        self.assertEqual(rows[0]["side"], "buy")
        self.assertEqual(rows[0]["ref_price"], PRICE)

    def test_validation_rejection_carries_intent_fields(self):
        # A rejection at the validate gate (before any price lookup)
        # still names what was refused: the intent's own fields,
        # with its limit_price as the reference price.
        d = _disp(self.tmp)
        intent = {"intent_id": "ilf2", "kind": "entry",
                  "symbol": "QQQ", "side": "sell", "qty": 0,
                  "order_type": "limit", "limit_price": 55.5,
                  "position_intent": "sell_to_open"}
        r = d.process_intent(intent, "sA")
        self.assertEqual(r["status"], "rejected")
        rows = _rejected_rows(d, "ilf2")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "QQQ")
        self.assertEqual(rows[0]["side"], "sell")
        self.assertEqual(rows[0]["ref_price"], 55.5)

    def test_reconcile_halt_rejection_carries_fields(self):
        d = _disp(self.tmp, halted={"sA"})
        intent = {"intent_id": "ilf3", "kind": "entry",
                  "symbol": "QQQ", "side": "buy", "qty": 10,
                  "order_type": "market", "price_hint": 42.25,
                  "position_intent": "buy_to_open"}
        r = d.process_intent(intent, "sA")
        self.assertEqual((r["status"], r["reason"]),
                         ("rejected", "reconcile_halt"))
        rows = _rejected_rows(d, "ilf3")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "QQQ")
        self.assertEqual(rows[0]["side"], "buy")
        self.assertEqual(rows[0]["ref_price"], 42.25)


class TestJournalIntentRecordFields(unittest.TestCase):
    def _desk(self, tmp, intent):
        mod = os.path.join(tmp, "ilf_sleeve.py")
        with open(mod, "w") as fh:
            fh.write(textwrap.dedent("""
                INTENT = %r
                def evaluate(view, ctx):
                    return [dict(INTENT)]
            """) % (intent,))
        broker = FakeBroker(prices={"TEST": PRICE})
        desk = Desk(tmp, broker=broker, sleeve_path=tmp)
        desk.add_producer("warm", lambda c: {"bars": {}}, ["bars"],
                          10 ** 9)
        desk.add_sleeve("ilf", "ilf_sleeve", ["bars"], 300, 1000.0)
        return desk

    def _journal_intent_rows(self, tmp, sid="ilf"):
        path = os.path.join(tmp, "state", sid, "journal.jsonl")
        return [json.loads(l) for l in open(path)
                if json.loads(l).get("event") == "intent"]

    def test_filled_intent_record_carries_fields(self):
        tmp = tempfile.mkdtemp()
        intent = {"intent_id": "ilf-fill", "kind": "entry",
                  "symbol": "TEST", "side": "buy", "qty": 3,
                  "order_type": "market", "time_in_force": "day",
                  "price_hint": PRICE}
        desk = self._desk(tmp, intent)
        desk.run_cycle()
        rows = self._journal_intent_rows(tmp)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["result"], "filled")
        self.assertEqual(rows[0]["symbol"], "TEST")
        self.assertEqual(rows[0]["side"], "buy")
        self.assertEqual(rows[0]["ref_price"], PRICE)

    def test_rejected_intent_record_and_dispatcher_row_carry_fields(self):
        tmp = tempfile.mkdtemp()
        # 30 x 100 = 3000 against a 1000 slice: refused at the gate.
        intent = {"intent_id": "ilf-rej", "kind": "entry",
                  "symbol": "TEST", "side": "buy", "qty": 30,
                  "order_type": "market", "time_in_force": "day",
                  "price_hint": PRICE}
        desk = self._desk(tmp, intent)
        desk.run_cycle()
        rows = self._journal_intent_rows(tmp)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["result"], "rejected")
        self.assertEqual(rows[0]["symbol"], "TEST")
        self.assertEqual(rows[0]["side"], "buy")
        self.assertEqual(rows[0]["ref_price"], PRICE)
        drows = [json.loads(l) for l in open(
            os.path.join(tmp, "state", "dispatcher.jsonl"))]
        rej = [r for r in drows if r.get("event") == "intent_rejected"
               and r.get("intent_id") == "ilf-rej"]
        self.assertEqual(len(rej), 1, drows)
        self.assertEqual(rej[0]["reason"], "insufficient_slice_bp")
        self.assertEqual(rej[0]["symbol"], "TEST")
        self.assertEqual(rej[0]["side"], "buy")
        self.assertEqual(rej[0]["ref_price"], PRICE)


if __name__ == "__main__":
    unittest.main()
