"""READINESS-EB24-20261112 blockers (grand-reconciliation EB-24).

Defect: reconcile.py's money decisions ran in binary floats.
The cash discrepancy test rounded the float difference to cents
before comparing against the one-cent tolerance: a true $0.015
difference is stored as 0.01499999... and rounds DOWN to $0.01,
so a real one-and-a-half-cent discrepancy on a ~$1M book raised
no row at all — the tolerance the desk believes it enforces is
not the tolerance the floats implement. The same float arithmetic
fed the halt materiality and the suspense new-movement figures.

Cure: the decision arithmetic runs in Decimal (quantized to
cents, ROUND_HALF_UP, via str() of the inputs): the discrepancy
difference, the tolerance comparison, the halt-materiality bound,
the _cash_halt_flags comparisons, and the signed new-movement
figures. Report values remain floats of the Decimal results, so
the report's shape and figures are unchanged wherever the float
path happened to agree. QTY_TOL (1e-9) is a quantity epsilon, not
a money comparison, and is out of this cure's scope by name.

Fail direction: proven on a worktree at the pre-cure HEAD — with
broker cash $0.015 under expected, reconcile reports no cash row
(float path); the cured tree raises the cash discrepancy.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.reconcile import reconcile


def _state():
    state = tempfile.mkdtemp()
    base = {"positions": {}, "cash_offset_usd": 0.0,
            "slice_capital_total_usd": 100000.0}
    with open(os.path.join(state, "reconcile_baseline.json"),
              "w") as fh:
        json.dump(base, fh)
    return state


CAPS = {"s1": 100000.0}


class TestDecimalMoneyComparison(unittest.TestCase):
    def test_one_and_a_half_cents_is_a_discrepancy(self):
        rep = reconcile(_state(), {}, broker_cash=99999.985,
                        slice_capital=CAPS)
        cash_rows = [d for d in rep["discrepancies"]
                     if d.get("kind") == "cash"]
        self.assertEqual(len(cash_rows), 1, rep)
        self.assertEqual(rep["status"], "DISCREPANCY", rep)

    def test_exactly_one_cent_is_within_tolerance(self):
        rep = reconcile(_state(), {}, broker_cash=99999.99,
                        slice_capital=CAPS)
        cash_rows = [d for d in rep["discrepancies"]
                     if d.get("kind") == "cash"]
        self.assertEqual(cash_rows, [], rep)
        self.assertEqual(rep["status"], "OK", rep)

    def test_two_cents_still_a_discrepancy(self):
        rep = reconcile(_state(), {}, broker_cash=99999.98,
                        slice_capital=CAPS)
        self.assertEqual(
            len([d for d in rep["discrepancies"]
                 if d.get("kind") == "cash"]), 1, rep)


if __name__ == "__main__":
    unittest.main()
