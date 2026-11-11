"""Regression blocker for LEDGER-STREAM-W1-20261110 (TOTAL
APPLICATION cure wave W1; census row TRM-1).

Failure of record: the 2026-11-10 17:46 forecast refresh was
OOM-killed during self-analogue (7 OOM kills on the run record)
with 14 legs failed or killed. The nine refreshers below still
read the shared forecast ledger through its materializing pair,
Ledger.rows() / Ledger.verify_chain() with no argument, which
parse and cache the whole ledger (~675 MB on disk, ~349k rows,
a measured 2.4 to 3.0 GB parsed per process in the
LEDGER-STREAM-REFRESH-20261110 record; the wave's own fixture
measured refresh_correctedband's pre-conversion peak at
2,909,880 KB). Several such peaks inside one refresh, beside
everything else the evening runs, exceed the 6 GB machine.

Cure pinned here: on each refresher's LIVE-ledger path the
materializing pair is replaced by the ledger's own streaming
forms, verify_chain_streaming() (identical verdicts by
ledger.py's contract) and iter_rows() (identical rows, one
parsed row resident), following the pattern the capitulation
clock, completion clock and exceedance already run, and the
three refreshers cured as LEDGER-STREAM-REFRESH-20261110.

Named exceptions, by design and not defects:
- refresh_calibrationleague.py keeps led.rows() inside
  self_test() only, on its throwaway ledger of ~122 synthetic
  rows (the bounded-fixture class the census excludes); its
  self-test grading call passes led.iter_rows() like the live
  path.
- refresh_feardaytriangulation.py and refresh_honestpop.py
  keep scratch.rows() / scratch.verify_chain() inside their
  self-tests on throwaway ledgers (a handful of rows), the
  same class the GLORY registry lane cleared.
- refresh_selfanalogue.py's converted sites sit inside its
  self-test on a throwaway ledger; its live path already
  streamed before this wave.

These are source assertions: the defect is which ledger API
the refresher calls, and a behavioural RSS harness for nine
multi-minute refreshers does not belong in the gate. The fail
direction is exact: the pre-cure files contain the
materializing calls on the live object and fail the
assertions below (verified against the preserved pre-cure
copies at the wave's fixture home).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# name -> substrings that must NOT appear (materializing calls
# on that file's live-ledger object)
FORBIDDEN = {
    "refresh_abstentionsignal.py": ("led.rows()", "led.verify_chain()"),
    "refresh_correctedband.py": ("led.rows()", "led.verify_chain()"),
    "refresh_familyfracture.py": ("ledger.rows()",
                                  "ledger.verify_chain()"),
    "refresh_gapdestiny.py": ("led.rows()", "led.verify_chain()"),
    "refresh_ownnormdepth.py": ("led.rows()", "led.verify_chain()"),
    "refresh_selfanalogue.py": ("led.rows()", "led.verify_chain()"),
    "refresh_feardaytriangulation.py": ("led.rows()",
                                        "led.verify_chain()"),
    "refresh_honestpop.py": ("led.rows()", "led.verify_chain()"),
}

STREAMING_REQUIRED = (
    "verify_chain_streaming()",
    "iter_rows()",
)


def _src(name):
    with open(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), name),
            encoding="utf-8") as fh:
        return fh.read()


def test_no_materializing_live_ledger_calls():
    for name, bad_forms in FORBIDDEN.items():
        src = _src(name)
        for bad in bad_forms:
            assert bad not in src, (name, bad)


def test_streaming_forms_in_use():
    for name in FORBIDDEN:
        src = _src(name)
        for form in STREAMING_REQUIRED:
            assert form in src, (name, form)


def test_calibrationleague_live_path_streams():
    src = _src("refresh_calibrationleague.py")
    assert "led.verify_chain_streaming()" in src
    assert "led.verify_chain(" not in src.replace(
        "led.verify_chain_streaming(", "")
    # main() and grade_rounds consume streams, never a
    # materialized live snapshot: the only led.rows() left in
    # the file is the self-test's throwaway-ledger read.
    assert src.count("led.rows()") == 1
    assert "grade_rounds(led, led.iter_rows())" in src
    assert "grade_rounds(led, led.rows())" not in src


def test_calibrationleague_checkpoint_slice_streams():
    # expected_page_count's checkpoint is a row index; the
    # streaming form enumerates instead of slicing a list.
    src = _src("refresh_calibrationleague.py")
    assert "rows[checkpoint:]" not in src
    assert "enumerate(rows)" in src
