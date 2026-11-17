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


def _stream():
    # Streamed read (LEDGER-MATERIALIZE-KILL-20261117): this
    # blocker used to materialise the whole ledger through
    # Ledger.rows() once per test. The ledger passed ~480k rows
    # / 968 MB on disk, the parsed whole is ~3 GB resident, and
    # the suite runner began OOM-killing this file (morning and
    # evening runs, 2026-11-17) as the box's other residents
    # grew. Ledger.iter_rows() is the library's own streaming
    # read (GRADING-STREAM-20261106: same parse, same
    # LedgerError, one row resident), and recompute_figures
    # accepts it directly (LEDGER-STREAM-FIGURES-20261109).
    # Every assertion below is unchanged; only the read form
    # moved, and each test now retains only the rows its claim
    # is about.
    return L.Ledger(LEDGER_PATH).iter_rows()


def test_supn_originals_voided_exactly_once_pointing_at_reissue():
    corrections = [r for r in _stream()
                   if r.get("type") == "correction"
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
    voided = set()
    present = set()
    for r in _stream():
        if r.get("type") == "correction" \
                and r.get("corrects_row_id") in REISSUES:
            voided.add(r["corrects_row_id"])
        elif r.get("type") == "forecast" \
                and r.get("row_id") in REISSUES:
            present.add(r["row_id"])
    assert not (REISSUES & voided), (
        f"reissue rows must stand valid; voided: {REISSUES & voided}")
    assert REISSUES <= present, "reissue rows missing from the ledger"


def test_engine06_void_aware_recount():
    figures = L.recompute_figures(_stream())
    eng = figures["engine_06"]
    assert eng["forecasts_voided"] == 3, eng
    assert eng["forecasts_valid"] == eng["forecasts"] - 3, eng
