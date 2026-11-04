"""Regression blocker for SUPN-VOID-REISSUE-20261104: the one-time
void of the defective-panel SUPN exceedance triple (engine_06),
executed 2026-11-04 under the Q1 gap-destiny precedent
(DECISIONS-20261103 Q1) as applied to SUPN by Midna's 2026-11-04
ruling.

Fail direction: on the ledger before the execution, engine_06
carried zero voided SUPN rows (the EXCEEDANCE-RERUN-COUNT-20261104
BUGLOG entry records "no ledger row was voided"), so every test
below fails; after the execution they pass. The void is a pin:
these exact row ids, voided exactly once each, pointing at the
exact reissue rows recorded from the cured panel.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ledger as L  # noqa: E402

LEDGER_PATH = os.path.join(os.path.dirname(__file__), "..", "ledger.jsonl")

ORIGINALS = {
    "f2ea08b671614b51": "d05ee4b021d32647",
    "31933ef32e3a08f9": "c9766cdefa5c86d9",
    "953099c482908880": "7c9f29d827a39ef7",
}
REISSUES = set(ORIGINALS.values())


def _rows():
    return L.Ledger(LEDGER_PATH).rows()


def test_supn_originals_voided_exactly_once_pointing_at_reissue():
    rows = _rows()
    corrections = [r for r in rows if r.get("type") == "correction"
                   and r.get("corrects_row_id") in ORIGINALS]
    assert len(corrections) == 3, (
        f"expected exactly 3 corrections voiding the SUPN originals, "
        f"found {len(corrections)}")
    for row in corrections:
        target = row["corrects_row_id"]
        assert (row.get("payload") or {}).get("superseded_by") == \
            ORIGINALS[target], (
                f"correction {row['row_id']} for {target} does not "
                f"name its reissue row")


def test_supn_reissue_rows_stand_unvoided():
    rows = _rows()
    voided = {r["corrects_row_id"] for r in rows
              if r.get("type") == "correction"}
    assert not (REISSUES & voided), (
        f"reissue rows must stand valid; voided: {REISSUES & voided}")
    present = {r["row_id"] for r in rows if r.get("type") == "forecast"}
    assert REISSUES <= present, "reissue rows missing from the ledger"


def test_engine06_void_aware_recount():
    figures = L.recompute_figures(_rows())
    eng = figures["engine_06"]
    assert eng["forecasts_voided"] == 3, eng
    assert eng["forecasts_valid"] == eng["forecasts"] - 3, eng
