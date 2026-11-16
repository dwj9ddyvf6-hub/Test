"""D-01-REJECT-PAYLOAD-20261115 blockers (W5D spec, Wave 6 Lane D).

Defect (Wave 4 V3 census): 29,360 intent_rejected rows, only the
7,023 reconcile_halt rows carry a symbol at all, and no reject row
of any class carries side, kind, quantity, or reference price:
76.1 percent of the reject book is ungradeable by construction.

Cure (spec W5D-REJECT-PAYLOAD-SPEC.md sections 3 to 5): every
intent_rejected row written after landing carries the full stamp
from one helper, Dispatcher._reject_stamp(intent): ts_utc, symbol,
side, kind, qty, reference_price with its named source (precedence
price_hint, then limit_price, then stop_price, then a dispatcher
held quote mid, then the explicit string "unavailable"),
missing_fields plus missing_reason under the never-silent-omission
rule (a genuinely unavailable value is an explicit null plus a
reason, never an absent key), and stamp_version 1. Both reject
sites carry it: _reject() and the inline
insufficient_options_bp_csp site.

Fail direction: on the pre-change code _reject_stamp does not
exist and no stamped key is written, so every test here fails.
Wiring: the gate (run_regression_blockers.sh) discovers
tests/test_*_blockers.py, so this file is in the gate by name.
"""
import copy, os, re, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.broker import FakeBroker  # noqa: E402
from desk3.dispatcher import Dispatcher  # noqa: E402

STAMP_KEYS = ("ts_utc", "symbol", "side", "kind", "qty",
              "reference_price", "reference_price_source",
              "missing_fields", "missing_reason", "stamp_version")
GRADED = ("symbol", "side", "kind", "qty", "reference_price")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CSP_SYM = "QQQ261204P00500000"  # strike 500.000


def _disp(slices=None, prices=None, obp=None):
    broker = FakeBroker(prices=prices or {})
    if obp is not None:
        broker.options_buying_power = obp
    root = tempfile.mkdtemp(prefix="d01-test-")
    disp = Dispatcher(root, broker, slices=slices or {
        "sleeve_a": {"capital_usd": 100000.0, "cash_usd": 100000.0}})
    return disp, broker


def _rows(disp, reason=None):
    rows = [r for r in disp.journal_events()
            if r.get("event") == "intent_rejected"]
    if reason is not None:
        rows = [r for r in rows if r.get("reason") == reason]
    return rows


def assert_stamp(tc, row):
    for k in STAMP_KEYS:
        tc.assertIn(k, row, f"stamped key absent: {k} in {row}")
    tc.assertEqual(row["stamp_version"], 1)
    tc.assertIsInstance(row["ts_utc"], str)
    tc.assertTrue(TS_RE.match(row["ts_utc"]), row["ts_utc"])
    tc.assertIsInstance(row["missing_fields"], list)
    # Never-silent omission: every null graded field is named in
    # missing_fields with a non-null reason; no null hides.
    for f in GRADED:
        if row[f] is None:
            tc.assertIn(f, row["missing_fields"],
                        f"{f} null but not named missing: {row}")
        else:
            tc.assertNotIn(f, row["missing_fields"],
                           f"{f} present but named missing: {row}")
    if row["missing_fields"]:
        tc.assertIsInstance(row["missing_reason"], str)
        tc.assertTrue(row["missing_reason"])
    else:
        tc.assertIsNone(row["missing_reason"])
    # The price source always names itself; null price is exactly
    # the "unavailable" source, never a silent gap.
    if row["reference_price"] is None:
        tc.assertEqual(row["reference_price_source"], "unavailable")
    else:
        tc.assertIn(row["reference_price_source"],
                    ("intent_price_hint", "intent_limit_price",
                     "intent_stop_price",
                     "dispatcher_quote_mid_at_reject"))


def _entry(iid, **kw):
    intent = {"intent_id": iid, "kind": "entry", "symbol": "AAPL",
              "side": "buy", "qty": 12, "price_hint": 148.20}
    intent.update(kw)
    return intent


class RejectPathStampTests(unittest.TestCase):
    def test_insufficient_slice_bp_row_is_stamped(self):
        disp, _ = _disp(slices={"sleeve_a": {
            "capital_usd": 100.0, "cash_usd": 100.0}})
        r = disp.process_intent(_entry("d01-slice-1"), "sleeve_a")
        self.assertEqual(r["reason"], "insufficient_slice_bp")
        rows = _rows(disp, "insufficient_slice_bp")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        assert_stamp(self, row)
        self.assertEqual(row["symbol"], "AAPL")
        self.assertEqual(row["side"], "buy")
        self.assertEqual(row["kind"], "entry")
        self.assertEqual(row["qty"], 12)
        self.assertEqual(row["reference_price"], 148.20)
        self.assertEqual(row["reference_price_source"],
                         "intent_price_hint")
        self.assertEqual(row["missing_fields"], [])
        self.assertEqual(row["sleeve"], "sleeve_a")

    def test_reconcile_halt_row_is_stamped_and_extras_kept(self):
        disp, _ = _disp()
        disp.halted_sleeves = {"sleeve_a"}
        r = disp.process_intent(_entry("d01-halt-1"), "sleeve_a")
        self.assertEqual(r["reason"], "reconcile_halt")
        rows = _rows(disp, "reconcile_halt")
        self.assertEqual(len(rows), 1)
        assert_stamp(self, rows[0])
        self.assertEqual(rows[0]["symbol"], "AAPL")
        self.assertIn("discrepancies", rows[0])
        self.assertIn("cash_halt", rows[0])

    def test_bad_qty_row_stamps_qty_null_with_reason(self):
        disp, _ = _disp()
        r = disp.process_intent(_entry("d01-badqty-1", qty=-3),
                                "sleeve_a")
        self.assertEqual(r["reason"], "bad_qty")
        rows = _rows(disp, "bad_qty")
        self.assertEqual(len(rows), 1)
        assert_stamp(self, rows[0])
        self.assertIsNone(rows[0]["qty"])
        self.assertIn("qty", rows[0]["missing_fields"])
        self.assertIn("qty", rows[0]["missing_reason"])


class InlineCspStampTests(unittest.TestCase):
    def test_insufficient_options_bp_csp_row_is_stamped(self):
        disp, broker = _disp(
            slices={"qqq_put_ladder": {"capital_usd": 100000.0,
                                       "cash_usd": 100000.0}},
            prices={CSP_SYM: 3.0}, obp=10_000.0)
        intent = {"intent_id": "d01-csp-1", "kind": "entry",
                  "symbol": CSP_SYM, "side": "sell", "qty": 1,
                  "position_intent": "sell_to_open",
                  "price_hint": 3.0}
        r = disp.process_intent(intent, "qqq_put_ladder")
        self.assertEqual(r["reason"], "insufficient_options_bp_csp")
        self.assertEqual(broker.submit_count, 0)
        rows = _rows(disp, "insufficient_options_bp_csp")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        assert_stamp(self, row)
        self.assertEqual(row["symbol"], CSP_SYM)
        self.assertEqual(row["side"], "sell")
        self.assertEqual(row["kind"], "entry")
        self.assertEqual(row["qty"], 1)
        self.assertEqual(row["reference_price"], 3.0)
        self.assertEqual(row["reference_price_source"],
                         "intent_price_hint")
        # Class-specific extras retained unchanged.
        self.assertEqual(row["required_collateral_usd"], 49700.0)
        self.assertEqual(row["options_buying_power_usd"], 10000.0)


class ReferencePricePrecedenceTests(unittest.TestCase):
    def _stamp_row(self, disp, iid, **kw):
        intent = {"intent_id": iid, "kind": "entry",
                  "symbol": "MSFT", "side": "buy", "qty": 5}
        intent.update(kw)
        disp._reject(intent, "sleeve_a", "insufficient_slice_bp")
        rows = [r for r in _rows(disp)
                if r.get("intent_id") == iid]
        self.assertEqual(len(rows), 1)
        assert_stamp(self, rows[0])
        return rows[0]

    def test_hint_beats_limit_and_stop(self):
        disp, _ = _disp()
        row = self._stamp_row(disp, "d01-prec-1", price_hint=10.0,
                              limit_price=11.0, stop_price=12.0)
        self.assertEqual(row["reference_price"], 10.0)
        self.assertEqual(row["reference_price_source"],
                         "intent_price_hint")

    def test_limit_when_no_hint(self):
        disp, _ = _disp()
        row = self._stamp_row(disp, "d01-prec-2", limit_price=11.0,
                              stop_price=12.0)
        self.assertEqual(row["reference_price"], 11.0)
        self.assertEqual(row["reference_price_source"],
                         "intent_limit_price")

    def test_stop_when_no_hint_or_limit(self):
        disp, _ = _disp()
        row = self._stamp_row(disp, "d01-prec-3", stop_price=12.0)
        self.assertEqual(row["reference_price"], 12.0)
        self.assertEqual(row["reference_price_source"],
                         "intent_stop_price")

    def test_nonpositive_hint_falls_through_to_limit(self):
        disp, _ = _disp()
        row = self._stamp_row(disp, "d01-prec-4", price_hint=0,
                              limit_price=11.0)
        self.assertEqual(row["reference_price"], 11.0)
        self.assertEqual(row["reference_price_source"],
                         "intent_limit_price")

    def test_held_quote_mid_when_no_intent_price(self):
        disp, _ = _disp()
        disp._quote_mids = {"MSFT": 210.5}
        row = self._stamp_row(disp, "d01-prec-5")
        self.assertEqual(row["reference_price"], 210.5)
        self.assertEqual(row["reference_price_source"],
                         "dispatcher_quote_mid_at_reject")

    def test_unavailable_is_explicit_never_silent(self):
        disp, _ = _disp()
        row = self._stamp_row(disp, "d01-prec-6")
        self.assertIsNone(row["reference_price"])
        self.assertEqual(row["reference_price_source"],
                         "unavailable")
        self.assertIn("reference_price", row["missing_fields"])
        self.assertIn("price", row["missing_reason"])


class NeverSilentOmissionTests(unittest.TestCase):
    def test_missing_everything_still_carries_every_key(self):
        disp, _ = _disp()
        disp._reject({"intent_id": "d01-bare-1"}, "sleeve_a",
                     "insufficient_slice_bp")
        rows = [r for r in _rows(disp)
                if r.get("intent_id") == "d01-bare-1"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        assert_stamp(self, row)
        for f in GRADED:
            self.assertIsNone(row[f], f)
            self.assertIn(f, row["missing_fields"], f)

    def test_bad_kind_stamps_kind_null_with_reason(self):
        disp, _ = _disp()
        disp._reject({"intent_id": "d01-badkind-1", "kind": "bogus",
                      "symbol": "AAPL", "side": "buy", "qty": 3,
                      "price_hint": 10.0},
                     "sleeve_a", "bad_kind")
        rows = [r for r in _rows(disp)
                if r.get("intent_id") == "d01-badkind-1"]
        self.assertEqual(len(rows), 1)
        assert_stamp(self, rows[0])
        self.assertIsNone(rows[0]["kind"])
        self.assertIn("kind", rows[0]["missing_fields"])

    def test_stamp_does_not_mutate_intent(self):
        disp, _ = _disp()
        intent = _entry("d01-pure-1")
        before = copy.deepcopy(intent)
        disp._reject(intent, "sleeve_a", "insufficient_slice_bp")
        self.assertEqual(intent, before)


if __name__ == "__main__":
    unittest.main()
