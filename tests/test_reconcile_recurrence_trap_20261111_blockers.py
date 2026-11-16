"""EC-U1 RECURRENCE TRAP blockers (NO-PARTIALS DRIVE 2026-11-11).

EC-U1: on 2026-11-01 cycle 1, reconcile flagged unexplained cash
+$0.45 (broker 1,077,380.75 vs expected 1,077,380.30) on an
otherwise flat book. The origin is unprovable from surviving
evidence (the graded sample's filings cover a different window;
the 2026-11-01 baseline was multiply overwritten). The register's
proof can now only be met by a recurrence: the next sub-$1
unexplained cash delta gets an intraday forensic capture instead
of renewing this row.

The trap is therefore the cure mechanism: when reconcile computes
a sub-$1 nonzero unexplained NEW cash delta whose signed amount
already appears in the reconcile history, the recurrence is named
on the report as recurrence_trap (id
EC-U1-recurring-sub-dollar-unexplained-cash) with its occurrence
count and first-seen stamp, plus a cash_recurrence_trap
discrepancy row. It never sets cash_halt: sub-$1 is below
materiality by construction. cycle.py carries recurrence_trap
through the roll's fixed key tuple so the row survives to the
terminal surfaces.

Fail direction on the pre-cure tree: the report has no
recurrence_trap key at all.
"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.reconcile import reconcile
from desk3.journal import append_line

CAP = 100000.0
STOCK = 5000.0


def _state():
    root = tempfile.mkdtemp(prefix="ecu1_")
    state = os.path.join(root, "state")
    os.makedirs(state, exist_ok=True)
    open(os.path.join(state, "dispatcher.jsonl"), "w").close()
    rep = reconcile(state, {}, broker_cash=CAP,
                    slice_capital={"s1": CAP}, record_baseline=True)
    assert rep["status"] == "BASELINE_RECORDED", rep
    path = os.path.join(state, "reconcile_baseline.json")
    base = json.load(open(path))
    base["suspense"] = {
        "id": "FIXTURE-SUSPENSE", "amount_usd": STOCK,
        "signed_amount_usd": STOCK,
        "direction": "broker_cash_excess_over_expected",
        "ruled_date": "2026-11-08", "ruling": "fixture",
        "composition": "fixture"}
    with open(path, "w") as fh:
        json.dump(base, fh, sort_keys=True)
    return state


def _seed_prior(state, amount, when="2026-11-01T05:00:00+00:00"):
    append_line(os.path.join(state, "reconcile_history.jsonl"), {
        "generated_at": when,
        "report": {"status": "OK",
                   "unexplained_new_cash_usd": amount}})


def _rep(state, broker_cash):
    return reconcile(state, {}, broker_cash=broker_cash,
                     slice_capital={"s1": CAP}, broker_fees_usd=0.0)


class TestRecurrenceTrap(unittest.TestCase):

    def test_recurring_sub_dollar_delta_is_named(self):
        state = _state()
        _seed_prior(state, -0.29)
        # signed diff = STOCK - 0.29; new movement = -0.29 exactly.
        rep = _rep(state, CAP + STOCK - 0.29)
        self.assertEqual(rep["unexplained_new_cash_usd"], -0.29, rep)
        trap = rep.get("recurrence_trap")
        self.assertIsNotNone(trap, rep)
        self.assertEqual(
            trap["id"], "EC-U1-recurring-sub-dollar-unexplained-cash")
        self.assertEqual(trap["amount_usd"], -0.29)
        self.assertEqual(trap["occurrences_incl_current"], 2)
        self.assertEqual(trap["first_seen"],
                         "2026-11-01T05:00:00+00:00")
        kinds = [d.get("kind") for d in rep["discrepancies"]]
        self.assertIn("cash_recurrence_trap", kinds)
        self.assertFalse(rep["cash_halt"], rep)

    def test_first_occurrence_is_not_a_recurrence(self):
        state = _state()
        rep = _rep(state, CAP + STOCK - 0.29)
        self.assertEqual(rep["unexplained_new_cash_usd"], -0.29, rep)
        self.assertIsNone(rep.get("recurrence_trap"), rep)

    def test_material_recurrence_is_not_trapped(self):
        state = _state()
        _seed_prior(state, -150.00)
        rep = _rep(state, CAP + STOCK - 150.00)
        self.assertEqual(rep["unexplained_new_cash_usd"], -150.00, rep)
        self.assertIsNone(rep.get("recurrence_trap"), rep)

    def test_zero_delta_is_not_trapped(self):
        state = _state()
        _seed_prior(state, 0.0)
        rep = _rep(state, CAP + STOCK)
        self.assertIsNone(rep.get("recurrence_trap"), rep)


if __name__ == "__main__":
    unittest.main()
