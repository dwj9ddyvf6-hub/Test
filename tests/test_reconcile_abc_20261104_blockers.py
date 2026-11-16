"""RECONCILE-ABC-20261104 blockers: the three machinery defects
exposed by the 2026-11-04 machinery-clean accounting
(RECONCILE-CASH-ROW, section 5 of the pass report).

Defect A: the halt/materiality comparisons in reconcile() were
SIGNED (unexplained > bound), so a negative unexplained remainder
of any magnitude could neither trip the cash halt nor set
below_halt_materiality (the 05:14Z read: unexplained -517.13 with
below_halt_materiality false). Cure: the comparisons are
magnitude-aware via _cash_halt_flags, against the UNCHANGED
HALT-MATERIALITY-20261103 bound (0.1% of expected cash, floor the
one-cent tolerance; the policy did not change, only its correct
application to the negative half of the range).

Defect B: derive_cfee_known_item's estimate was SUBTRACTED from
the raw cash discrepancy (unexplained = diff - known items). The
desk's own FEE-WALK-20261103 proof established that crypto sell
fills reach the journal NET of the CFEE leg, so the subtraction
double-counts and manufactures negative "unexplained" figures in
proportion to pending crypto sells (live: raw diff 7.99, item
184.84, headline -176.85). Cure: the D1-CFEE item is still
derived and reported on known_items as INFORMATION, but it no
longer enters the unexplained arithmetic: unexplained_cash_usd
is the raw cash discrepancy itself.

Defect C: cycle.py persisted each cycle's reconcile report to
the single-slot state/reconcile_last.json, overwriting the prior
report, so no earlier cycle's report could ever be re-read (the
05:14Z $10.11 inconsistency is permanently unverifiable for
exactly this reason). Cure: every persisted report is also
appended to state/reconcile_history.jsonl through
append_reconcile_history, an append-only history bounded to the
most recent RECONCILE_HISTORY_MAX_RECORDS records.

Fail direction on the pre-cure tree: _cash_halt_flags and
append_reconcile_history do not exist (ImportError), the
over-offset case computes unexplained -17.01 with
below_halt_materiality False, and cycle.py never mentions a
reconcile history.
"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.reconcile import reconcile

CAP = 100000.0


def _state():
    root = tempfile.mkdtemp(prefix="recabc_")
    state = os.path.join(root, "state")
    os.makedirs(state, exist_ok=True)
    open(os.path.join(state, "dispatcher.jsonl"), "w").close()
    rep = reconcile(state, {}, broker_cash=CAP,
                    slice_capital={"s1": CAP}, record_baseline=True)
    assert rep["status"] == "BASELINE_RECORDED", rep
    return state


def _fill(fid, tt, qty, price):
    return {"activity_type": "FILL", "id": fid,
            "transaction_time": tt, "symbol": "BTC/USD",
            "side": "sell", "qty": str(qty), "price": str(price),
            "order_id": "ord-" + fid}


def _cfee(cid, created, net):
    return {"activity_type": "CFEE", "id": cid,
            "created_at": created, "net_amount": str(net),
            "description": "Coin Pair Transaction Fee (USD)"}


def _evidence_item25():
    """One matched sell (qp 10000, posted fee 25.00 -> observed
    rate 0.0025) and one pending sell (qp 10000): the derived
    D1-CFEE item is exactly 25.00."""
    fills = [_fill("f-match", "2026-10-31T03:04:36Z", 1.0, 10000.0),
             _fill("f-pend", "2026-10-31T08:14:39Z", 1.0, 10000.0)]
    cfee = [_cfee("c-1", "2026-10-31T03:04:38Z", -25.00)]
    return {"fills": fills, "cfee": cfee}


def _rep(state, broker_cash, evidence=None):
    return reconcile(state, {}, broker_cash=broker_cash,
                     slice_capital={"s1": CAP}, broker_fees_usd=0.0,
                     cfee_evidence=evidence)


class TestMagnitudeAwareFlags(unittest.TestCase):
    """Defect A at the comparison itself: positive, negative and
    over-offset remainders against the unchanged bound."""

    def _flags(self, unexplained, materiality):
        from desk3.reconcile import _cash_halt_flags
        return _cash_halt_flags(unexplained, materiality)

    def test_positive_over_materiality_halts(self):
        self.assertEqual(self._flags(150.0, 100.0), (True, False))

    def test_negative_over_materiality_halts(self):
        # THE over-offset negative case: pre-cure the signed
        # comparison made this (False, False) at any magnitude.
        self.assertEqual(self._flags(-150.0, 100.0), (True, False))

    def test_negative_below_materiality_is_named_not_halted(self):
        self.assertEqual(self._flags(-50.0, 100.0), (False, True))

    def test_positive_below_materiality_is_named_not_halted(self):
        self.assertEqual(self._flags(50.0, 100.0), (False, True))

    def test_exactly_at_materiality_does_not_halt_either_sign(self):
        self.assertEqual(self._flags(100.0, 100.0), (False, True))
        self.assertEqual(self._flags(-100.0, 100.0), (False, True))

    def test_within_one_cent_tolerance_no_flags_either_sign(self):
        self.assertEqual(self._flags(0.01, 100.0), (False, False))
        self.assertEqual(self._flags(-0.01, 100.0), (False, False))
        self.assertEqual(self._flags(0.0, 100.0), (False, False))


class TestHonestUnexplained(unittest.TestCase):
    """Defect B: the D1-CFEE item annotates; it never offsets."""

    def test_over_offset_item_cannot_manufacture_negative(self):
        # The 2026-11-04 live shape, scaled: raw diff 7.99 with a
        # pending-CFEE item LARGER than the diff. Pre-cure this
        # reported unexplained -17.01 and below_halt_materiality
        # False; the honest report is the 7.99 itself, named
        # below materiality.
        rep = _rep(_state(), CAP - 7.99, _evidence_item25())
        self.assertEqual(rep["status"], "DISCREPANCY", rep)
        self.assertEqual(rep["unexplained_cash_usd"], 7.99, rep)
        self.assertEqual(rep["cash_halt_materiality_usd"], 100.0, rep)
        self.assertFalse(rep["cash_halt"], rep)
        self.assertTrue(rep["below_halt_materiality"], rep)

    def test_item_still_derived_and_reported_as_information(self):
        rep = _rep(_state(), CAP - 7.99, _evidence_item25())
        items = rep["known_items"]
        self.assertEqual(len(items), 1, rep)
        self.assertEqual(items[0]["id"], "D1-CFEE")
        self.assertEqual(items[0]["amount_usd"], 25.00)

    def test_item_does_not_offset_even_one_cent(self):
        # Pre-cure this was unexplained 0.01; the item must not
        # reduce the raw discrepancy by anything at all.
        rep = _rep(_state(), CAP - 25.01, _evidence_item25())
        self.assertEqual(rep["unexplained_cash_usd"], 25.01, rep)
        self.assertFalse(rep["cash_halt"], rep)
        self.assertTrue(rep["below_halt_materiality"], rep)

    def test_material_raw_diff_halts_despite_pending_item(self):
        rep = _rep(_state(), CAP - 125.02, _evidence_item25())
        self.assertEqual(rep["unexplained_cash_usd"], 125.02, rep)
        self.assertTrue(rep["cash_halt"], rep)
        self.assertFalse(rep["below_halt_materiality"], rep)

    def test_broker_excess_direction_also_halts_when_material(self):
        # The other sign of raw discrepancy: broker holds MORE
        # than expected by a material amount. The halt guards the
        # magnitude of the disagreement, not one direction.
        rep = _rep(_state(), CAP + 250.00, None)
        self.assertEqual(rep["unexplained_cash_usd"], 250.00, rep)
        self.assertTrue(rep["cash_halt"], rep)

    def test_one_cent_tolerance_preserved(self):
        rep = _rep(_state(), CAP - 0.01, _evidence_item25())
        self.assertEqual(rep["status"], "OK", rep)
        self.assertIsNone(rep["unexplained_cash_usd"], rep)
        rep2 = _rep(_state(), CAP - 0.02, _evidence_item25())
        self.assertEqual(rep2["status"], "DISCREPANCY", rep2)
        self.assertEqual(rep2["unexplained_cash_usd"], 0.02, rep2)
        self.assertTrue(rep2["below_halt_materiality"], rep2)


class TestReconcileHistory(unittest.TestCase):
    """Defect C: bounded append-only history of cycle reports."""

    def _record(self, n):
        return {"generated_at": f"2026-11-04T00:{n:02d}:00+00:00",
                "cycle_id": f"cycle-{n}", "fill_sweep": None,
                "report": {"status": "OK", "n": n}}

    def test_appends_every_record_in_order(self):
        from desk3.reconcile import append_reconcile_history
        state = tempfile.mkdtemp(prefix="rechist_")
        for n in range(3):
            append_reconcile_history(state, self._record(n))
        path = os.path.join(state, "reconcile_history.jsonl")
        with open(path) as fh:
            rows = [json.loads(ln) for ln in fh if ln.strip()]
        self.assertEqual([r["cycle_id"] for r in rows],
                         ["cycle-0", "cycle-1", "cycle-2"])

    def test_history_is_bounded_to_the_most_recent_records(self):
        from desk3.reconcile import append_reconcile_history
        state = tempfile.mkdtemp(prefix="rechist_")
        for n in range(12):
            append_reconcile_history(state, self._record(n),
                                     max_records=10)
        path = os.path.join(state, "reconcile_history.jsonl")
        with open(path) as fh:
            rows = [json.loads(ln) for ln in fh if ln.strip()]
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["cycle_id"], "cycle-2")
        self.assertEqual(rows[-1]["cycle_id"], "cycle-11")

    def test_cycle_persists_history_beside_the_single_slot(self):
        with open(os.path.join(os.path.dirname(__file__), "..",
                               "desk3", "cycle.py")) as fh:
            src = fh.read()
        self.assertIn("append_reconcile_history", src)
        self.assertIn("reconcile_last.json", src)


if __name__ == "__main__":
    unittest.main()
