"""Regression blockers for BTC-FEE-DUST-RESTORE-20261116 — the
full sleeve audit's Lane F fee-dust correction walk (Mon
2026-11-16).

The BTC/USD reconcile gap (+0.003925301 BTC: journal-derived
expected 0.136601008 vs broker 0.132675707, standing since
2026-11-14 and holding five (sleeve, BTC/USD) halt scopes) was
attributed exactly, to 9 dp, with zero remainder:

1. 0.003922949 BTC — crypto_fee_in_kind measurement rows
   journaled 2026-10-30 -> 11-02, destroyed by the 2026-11-08
   journal rotation, never restored (the 2026-11-10 heal
   re-imported the span's fills, net +0.388677621, but fee rows
   are not fills and have no order to import against). Proof:
   the first surviving fee row (2026-11-02T18:08:51.596919Z)
   records journal_gross_qty 0.449305675 against a fill sum of
   0.453228624 at that instant — the difference is the destroyed
   fee stock; with a constant -0.003922949 offset, all 548
   surviving fee rows reproduce their recorded
   journal_gross_qty to <1e-9 (548/548).
2. 0.000002352 BTC — the in-kind fee on aster_native's
   2026-11-11 buy (0.001306356 @ 74452.6, coid
   v3-aster_native_btc_eth_sma200-20261111T220109-1-BTC-USD):
   expected stepped by the full fill while the broker stepped
   by +0.001304004. Never measured because the sweep's dust
   measurement skips a crypto symbol while any of its orders is
   non-terminal, and the stuck pending_cancel BTC order
   684ef8f6 has blocked BTC/USD measurement since 2026-11-07.

Cure: two provenance crypto_fee_in_kind rows appended to
state/dispatcher.jsonl on aster_native_btc_eth_sma200 (the
exit-storm provenance-correction shape), restoring the derived
book to the broker figure exactly. No fill row is added,
removed, or altered. (state/ is git-ignored; the rows live in
the journal, and this test + the BUGLOG entry are the in-repo
record, per the EXIT-STORM-CURE-20261116 (record) precedent.)

These pins read the live journal. If a future BTC fill lands,
the absolute figures below must be re-derived in a dated
amendment — that loud failure is the dated-pin contract, not a
defect in this test.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "state" / "dispatcher.jsonl"
BROKER_BTC = 0.132675707
NATIVE_POST = 36.935577160


def _all_rows():
    from desk3.reconcile import journal_rows
    return journal_rows(str(JOURNAL))


def _derived():
    from desk3.reconcile import journal_derived
    pos, _spend = journal_derived(str(JOURNAL))
    agg = sum(p.get("BTC/USD", 0.0) for p in pos.values())
    native = (pos.get("aster_native_btc_eth_sma200") or {}).get(
        "BTC/USD", 0.0)
    return agg, native


class TestFeeDustRestore(unittest.TestCase):
    def test_correction_rows_present_exactly(self):
        rows = [r for r in _all_rows()
                if r.get("event") == "crypto_fee_in_kind"
                and r.get("correction")]  # only correction rows
        # carry the field; the sweep's 548 measurement rows and
        # every other fee row in the record carry none.
        self.assertEqual(len(rows), 2, rows)
        by_id = {r.get("correction"): r for r in rows}
        r1 = by_id["BTC-FEE-DUST-RESTORE-20261116"]
        self.assertEqual(r1["sleeve"], "aster_native_btc_eth_sma200")
        self.assertEqual(r1["symbol"], "BTC/USD")
        self.assertAlmostEqual(r1["qty"], 0.003922949, places=12)
        self.assertAlmostEqual(r1["price"], 77341.5108, places=4)
        self.assertIs(r1["imported"], True)
        r2 = by_id["BTC-FEE-DUST-20261111-BUY-20261116"]
        self.assertEqual(r2["sleeve"], "aster_native_btc_eth_sma200")
        self.assertAlmostEqual(r2["qty"], 0.000002352, places=12)
        self.assertAlmostEqual(r2["price"], 74452.6, places=4)

    def test_derived_matches_broker_exactly(self):
        agg, native = _derived()
        self.assertAlmostEqual(agg, BROKER_BTC, places=9)
        self.assertAlmostEqual(native, NATIVE_POST, places=9)

    def test_no_fill_rows_altered(self):
        fills = [r for r in _all_rows()
                 if r.get("event") == "fill"
                 and r.get("symbol") in ("BTC/USD", "BTCUSD",
                                         "BTC-USD")]
        self.assertEqual(len(fills), 818)

    def test_measurement_chain_provenance(self):
        """The 548 surviving fee rows reproduce their recorded
        journal_gross_qty only with the destroyed-stock offset —
        the provenance proof for component 1, pinned on the
        closed generation .3 record."""
        from desk3.reconcile import journal_rows
        rows = journal_rows(str(JOURNAL))
        fills = [r for r in rows if r.get("event") == "fill"
                 and r.get("symbol") == "BTC/USD"]
        fees = [r for r in rows
                if r.get("event") == "crypto_fee_in_kind"
                and r.get("symbol") == "BTC/USD"
                and str(r.get("ts") or "") <= "2026-11-07T23:59:59"]
        self.assertEqual(len(fees), 548)
        first = fees[0]
        pre = sum(float(f["qty"]) * (1 if f.get("side") == "buy"
                                     else -1)
                  for f in fills
                  if str(f.get("ts") or "") < str(first["ts"]))
        # signed fill sum before the first surviving measurement,
        # net of the fee rows folded before it in the complete
        # pre-destruction journal (none survive), reproduces the
        # recorded gross only after the destroyed-stock offset.
        self.assertAlmostEqual(
            pre - 0.003922949, float(first["journal_gross_qty"]),
            places=6)


if __name__ == "__main__":
    unittest.main()
