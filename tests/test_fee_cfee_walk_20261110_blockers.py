"""FEE-CFEE-WALK-20261110 regression blockers (TOTAL APPLICATION
W4; census DSK-3 HIGH, DSK-4 MEDIUM, DSK-5 MEDIUM).

The defects: (DSK-3) the desk's expected-cash model never counted
CFEE (Coin Pair Transaction Fee) activities: 836 nonzero USD rows
Oct 31 to Nov 9 totalling -$5,352.33 were invisible to expected
cash, manufacturing the -$5,489.15 suspense and the desk-wide cash
halt whose blast radius was 8,676 rejected intents in 48 h. The
model rested on the FEE-WALK-20261103 premise that crypto sell
fills reach the journal net of their CFEE leg; the 2026-11-10
exhaustive 14,317-row activity walk REFUTED it (journal fill
prices equal gross execution prices, proven per-order against all
335 heal imports at $0.00; the cash identity closes only with CFEE
counted as a drain). (DSK-4) get_fees_total and get_cfee_evidence
each capped their page_token walk at 60 pages (6,000 activities):
the fee walk stopped at activity 6,000 of 14,317, undercounting
FEE by $104.19, and the first-6,000 CFEE sum (-$2,146.87) inherited
the truncation.

The cure (desk3/broker.py, desk3/cycle.py): both walks share
PaperDoor._walk_activities, which pages to EXHAUSTION (termination
proven by a short/empty page or a non-advancing id cursor, never
a page cap); get_fees_total returns the signed sum over every
cash-moving type in COUNTED_CASH_ACTIVITY_TYPES (FEE and CFEE
included) via activity_type_audit; and the audit names every
activity type the enumeration does not know, so the NEXT omitted
type is caught by this gate (the enumeration-totality test) and
by the cycle record, not by a halt.

Fail direction: against the pre-cure broker.py (preserved copy),
the CFEE-inclusion tests fail (CFEE returns 0), the >60-page
fixture returns the truncated first-6,000 sum, and the audit /
enumeration API does not exist (ImportError). The suspense
discharge case fails on pre-cure reconcile() arithmetic for the
same fixture because the fee term it is handed models the
truncated, CFEE-free read.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3.broker import (PaperDoor, activity_type_audit,  # noqa: E402
                          COUNTED_CASH_ACTIVITY_TYPES,
                          AUDITED_ZERO_ACTIVITY_TYPES,
                          KNOWN_ACTIVITY_TYPES)
from desk3.reconcile import reconcile  # noqa: E402


def _row(rid, t, net):
    return {"id": str(rid), "activity_type": t, "net_amount": net}


def _door_with_rows(rows):
    """A PaperDoor whose _get serves `rows` through the REAL
    page_token protocol (100 per page, token = last id of the
    previous page; a request past the end returns the empty list),
    so the walk under test is the production walk, not a stub of
    it."""
    door = PaperDoor(env={"ALPACA_KEY_ID": "k",
                          "ALPACA_SECRET_KEY": "s"})
    by_token = {None: rows[0:100]}
    for i in range(100, len(rows), 100):
        by_token[str(rows[i - 1]["id"])] = rows[i:i + 100]

    def fake_get(path):
        import urllib.parse
        q = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        tok = (q.get("page_token") or [None])[0]
        return [dict(r) for r in by_token.get(tok, [])]

    door._get = fake_get
    return door


class TestFeeWalkExhaustion(unittest.TestCase):
    """DSK-4: the walk must exhaust pages; a >60-page fixture is
    the regression shape (6,000 activities was the old cap)."""

    def test_fees_total_walks_past_6000_activities(self):
        rows = [_row(i, "FILL", 0.0) for i in range(6500)]
        rows[6000] = _row(6000, "FEE", -104.19)  # past the old cap
        rows[6100] = _row(6100, "CFEE", -10.00)  # past the old cap
        door = _door_with_rows(rows)
        total = door.get_fees_total("2026-10-26T20:14:30Z")
        self.assertAlmostEqual(total, -114.19, places=2)
        self.assertEqual(
            door.last_activity_type_audit["rows_walked"], 6500)
        self.assertEqual(
            door.last_activity_type_audit["unknown_types"], [])

    def test_cfee_evidence_walks_past_6000_activities(self):
        rows = [_row(i, "FILL", 0.0) for i in range(6300)]
        rows[6200] = _row(6200, "CFEE", -3.25)
        door = _door_with_rows(rows)
        ev = door.get_cfee_evidence("2026-10-26T20:14:30Z")
        self.assertEqual(len(ev["cfee"]), 1)
        self.assertEqual(float(ev["cfee"][0]["net_amount"]), -3.25)
        self.assertEqual(len(ev["fills"]), 6299)


class TestCfeeCountedInExpectedCash(unittest.TestCase):
    """DSK-3: CFEE USD rows are a cash drain in the fee term, and
    the term feeds reconcile()'s expected cash unchanged."""

    def test_audit_counts_cfee_and_fee_and_names_unknown(self):
        rows = [_row(1, "FEE", -386.31), _row(2, "CFEE", -5352.33),
                _row(3, "CFEE", 0.0),  # in-kind leg: no cash
                _row(4, "FILL", 999.0),  # journalled, never counted
                _row(5, "NEWX", -50.0)]  # unknown: named, not counted
        total, unknown = activity_type_audit(rows)
        self.assertAlmostEqual(total, -5738.64, places=2)
        self.assertEqual(unknown, ["NEWX"])

    def test_audit_dedupes_by_activity_id(self):
        rows = [_row(1, "FEE", -10.0), _row(1, "FEE", -10.0)]
        total, _ = activity_type_audit(rows)
        self.assertAlmostEqual(total, -10.0, places=2)

    def test_fees_total_includes_cfee(self):
        rows = [_row(1, "FEE", -386.31), _row(2, "CFEE", -5352.33),
                _row(3, "DIV", 12.00)]
        door = _door_with_rows(rows)
        self.assertAlmostEqual(
            door.get_fees_total("2026-10-26T20:14:30Z"),
            -5726.64, places=2)


class TestEnumerationTotality(unittest.TestCase):
    """The enumeration must stay total against the broker's
    published activity-type list: a type added by the broker (or
    dropped from this table) fails here first, not in production
    as a halt."""

    # Alpaca account-activity types (Trading API docs, "Account
    # Activities" enumeration) as of 2026-11-10.
    BROKER_PUBLISHED_TYPES = {
        "ACATC", "ACATS", "CFEE", "CSD", "CSW", "DIV", "DIVCGL",
        "DIVCGS", "DIVNRA", "DIVROC", "DIVTXW", "FEE", "FEEB",
        "FILL", "INT", "INTP", "JNLC", "JNLS", "MACT", "NTC",
        "OCT", "OPASN", "OPEXC", "OPTRD", "OPXPL", "PTR", "RIGHTS",
        "SPLIT", "SPIN", "MERGER", "WARRANTS"}

    def test_every_published_type_is_classified(self):
        self.assertEqual(self.BROKER_PUBLISHED_TYPES
                         - KNOWN_ACTIVITY_TYPES, set())

    def test_classes_are_disjoint_and_cover_known(self):
        self.assertFalse(COUNTED_CASH_ACTIVITY_TYPES
                         & AUDITED_ZERO_ACTIVITY_TYPES)
        self.assertEqual(KNOWN_ACTIVITY_TYPES,
                         COUNTED_CASH_ACTIVITY_TYPES
                         | AUDITED_ZERO_ACTIVITY_TYPES)


class TestSuspenseDischargesOnCuredModel(unittest.TestCase):
    """DSK-5: with the cured fee term (FEE + CFEE + the >60-page
    remainder), the booked -$5,489.15 suspense's current residual
    derives to its decomposed closure ($0.29 scale) instead of the
    parked stock, so the name can discharge through the
    SUSPENSE-DISCHARGED mechanism."""

    CAP = 100000.0
    # The decomposition's legs at fixture scale: CFEE -5352.33,
    # FEE beyond the truncation -104.19, executions-vs-journal
    # basis -32.91, tail +0.28; closure $0.29.
    FEE_TERM = -386.31 - 5352.33  # true FEE total + full CFEE total

    def _state_with_residual_suspense(self):
        root = tempfile.mkdtemp(prefix="feecfee_")
        state = os.path.join(root, "state")
        os.makedirs(state, exist_ok=True)
        open(os.path.join(state, "dispatcher.jsonl"), "w").close()
        rep = reconcile(state, {}, broker_cash=self.CAP,
                        slice_capital={"s1": self.CAP},
                        record_baseline=True)
        assert rep["status"] == "BASELINE_RECORDED", rep
        path = os.path.join(state, "reconcile_baseline.json")
        base = json.load(open(path))
        base["suspense"] = {
            "id": "RECONCILE-CASH-SUSPENSE-20261110-RESIDUAL",
            "amount_usd": 5489.15,
            "signed_amount_usd": -5489.15,
            "direction": "broker_cash_shortfall_vs_expected",
            "ruled_date": "2026-11-10",
            "ruling": "decomposed stock; discharges when the cured "
                      "model derives the residual away.",
            "composition": "CFEE -5352.33; FEE truncation -104.19; "
                           "basis -32.91; tail +0.28; closure 0.29."}
        with open(path, "w") as fh:
            json.dump(base, fh, sort_keys=True)
        return state

    def test_residual_derives_to_closure_under_cured_fees(self):
        state = self._state_with_residual_suspense()
        # Broker cash = capital + counted fee term + the journal
        # basis the model cannot see (-32.91) + the rounding tail
        # (+0.28): the broker-side truth of the decomposition.
        broker_cash = self.CAP + self.FEE_TERM - 32.91 + 0.28
        rep = reconcile(state, {}, broker_cash=broker_cash,
                        slice_capital={"s1": self.CAP},
                        broker_fees_usd=self.FEE_TERM)
        # Expected = CAP + FEE_TERM; signed residual = -32.63;
        # beyond the booked -5,489.15 stock the NEW movement is
        # +5,456.52 in the discharge direction: the parked stock
        # no longer exists in the discrepancy, which is exactly
        # the fact the discharge records.
        self.assertAlmostEqual(rep["unexplained_cash_usd"], 32.63,
                               places=2)
        self.assertGreater(rep["unexplained_new_cash_usd"], 5000.0)
        self.assertEqual(rep["suspense"]["id"],
                         "RECONCILE-CASH-SUSPENSE-20261110-RESIDUAL")

    def test_cure_marked_suspense_never_halts_on_its_own_cure(self):
        # FEE-CFEE-DERIVED-AWAY-20261110: with the component
        # carrying its cure marker, the halt keys on the CURRENT
        # signed discrepancy (the closure), not on the stock's
        # absence; without the marker the legacy stock-keyed
        # behavior stands (the control case below).
        state = self._state_with_residual_suspense()
        path_ = os.path.join(state, "reconcile_baseline.json")
        base = json.load(open(path_))
        base["suspense"]["cure"] = "FEE-CFEE-WALK-20261110"
        with open(path_, "w") as fh:
            json.dump(base, fh, sort_keys=True)
        broker_cash = self.CAP + self.FEE_TERM - 32.91 + 0.28
        rep = reconcile(state, {}, broker_cash=broker_cash,
                        slice_capital={"s1": self.CAP},
                        broker_fees_usd=self.FEE_TERM)
        # The signed closure at this scale: broker comparable
        # minus expected = -32.63, the decomposition's closure
        # magnitude; the derive-away leg keys the halt on exactly
        # this current figure.
        self.assertAlmostEqual(rep["unexplained_new_cash_usd"],
                               -32.63, places=2)
        self.assertFalse(rep["cash_halt"])

    def test_unmarked_suspense_keeps_stock_keyed_halt(self):
        # Control: the same fixture WITHOUT the cure marker keeps
        # the pre-cure halt keying (the stock's absence reads as
        # new movement and halts), proving the marker is what the
        # derive-away leg keys on.
        state = self._state_with_residual_suspense()
        broker_cash = self.CAP + self.FEE_TERM - 32.91 + 0.28
        rep = reconcile(state, {}, broker_cash=broker_cash,
                        slice_capital={"s1": self.CAP},
                        broker_fees_usd=self.FEE_TERM)
        self.assertTrue(rep["cash_halt"])


if __name__ == "__main__":
    unittest.main()
