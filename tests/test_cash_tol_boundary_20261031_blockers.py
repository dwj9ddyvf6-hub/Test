"""CASH-TOL-BOUNDARY-20261031 blockers.

Live proof (night inspection 2026-10-31): after the CASH-RECONCILE
cure landed, the desk re-halted desk-wide on a cash discrepancy of
exactly one cent: state/reconcile_last.json at 2026-10-31T04:06Z
reads broker_cash_usd 1077786.01 vs expected_cash_usd 1077786.0,
cash_halt true, halted_sleeves [], and every entry intent in the
03:41Z to 04:06Z cycles was rejected with reason reconcile_halt
carrying that single cash row. The CASH-RECONCILE-20261030 BUGLOG
entry itself calls a 0.01 residue "inside the existing one-cent
tolerance exactly as designed": the decimal difference IS the
tolerance. It halts anyway because the comparison is done in
binary floating point, where 1077786.01 - 1077786.0 is
0.010000000009313226, strictly greater than 0.01. At smaller
magnitudes the same subtraction lands below 0.01, which is why
the fixtures must use the live amounts.

Fail direction: on the pre-fix comparison the exactly-one-cent
test below reports cash_halt True; on the fixed comparison
(rounded to cents before comparing, tolerance unchanged at
0.01) it reports OK, and a two-cent difference still halts.

AMENDED 2026-11-03 (HALT-MATERIALITY-20261103, owner ruling:
a minor discrepancy must not block the entire desk): the halt
half of the two-cent case is superseded. Two cents on this
$1,077,786 fixture book is the definition of minor; it is still
detected and reported as a cash DISCREPANCY at the unchanged
one-cent tolerance (the boundary this file exists to protect),
but the desk-wide halt now trips only above the materiality
bound (0.1% of expected cash, $1,077.79 here), blocked in
test_halt_materiality_20261103_blockers.py. On the pre-amendment
halt rule the amended test fails (cash_halt True), which is the
fail direction for the supersession.
"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.reconcile import reconcile


def _root():
    return tempfile.mkdtemp(prefix="cashtol_")


class TestCashTolBoundary(unittest.TestCase):

    def _state(self):
        root = _root()
        state = os.path.join(root, "state")
        os.makedirs(state, exist_ok=True)
        open(os.path.join(state, "dispatcher.jsonl"), "w").close()
        rep = reconcile(state, {}, broker_cash=1077786.0,
                        slice_capital={"s1": 1077786.0},
                        record_baseline=True)
        self.assertEqual(rep["status"], "BASELINE_RECORDED")
        return state

    def test_exactly_one_cent_at_live_magnitude_does_not_halt(self):
        state = self._state()
        rep = reconcile(state, {}, broker_cash=1077786.01,
                        slice_capital={"s1": 1077786.0})
        self.assertEqual(rep["status"], "OK", rep)
        self.assertFalse(rep["cash_halt"])

    def test_two_cents_discrepancy_reported_but_does_not_halt(self):
        # HALT-MATERIALITY-20261103: detection at the one-cent
        # tolerance is unchanged (the discrepancy is reported),
        # but two cents is minor on a $1,077,786 book and cannot
        # halt the desk.
        state = self._state()
        rep = reconcile(state, {}, broker_cash=1077786.02,
                        slice_capital={"s1": 1077786.0})
        self.assertEqual(rep["status"], "DISCREPANCY", rep)
        self.assertFalse(rep["cash_halt"])
        self.assertTrue(rep["below_halt_materiality"])
        self.assertEqual(rep["unexplained_cash_usd"], 0.02)
        self.assertEqual(
            [d["kind"] for d in rep["discrepancies"]], ["cash"])


if __name__ == "__main__":
    unittest.main()
