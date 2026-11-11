"""Regression blocker for LEDGER-STREAM-REFRESH-20261110
(EARNINGS-MEMORY-CONTENTION-20261108, third recurrence).

Failure of record: refresh_earningsdistribution.py,
refresh_insiderdivergence.py and refresh_gammaearningstrap.py
each verified the forecast ledger with Ledger.verify_chain()
and counted their rows from Ledger.rows(). Both forms parse
the WHOLE ledger (~707 MB on disk, ~3 GB parsed at the
2026-11-10 size) and rows() retains the parse in the Ledger's
cache, so each refresher held ~2.4 to 3.0 GB resident. Run
standalone on an idle box they survived; inside the 19:00
full tools run, beside everything else the evening runs,
the kernel OOM-killed all three (exit -9) on 2026-11-08,
2026-11-09 and again on 2026-11-10.

Cure pinned here: the three refreshers use the ledger's own
streaming forms, verify_chain_streaming() (identical verdicts
by ledger.py's contract) and iter_rows() (identical rows, one
parsed row resident), at exactly the sites that used the
materializing pair. Measured on the cured tree:
earningsdistribution peak RSS 3,009 MB -> ~191 MB class,
insiderdivergence 2,579 MB -> ~365 MB class,
gammaearningstrap's 2,368 MB spike removed; published
outputs byte-identical to the pre-cure standalone outputs.

These are source assertions: the defect is which ledger API
the refresher calls, and a behavioural RSS harness for three
multi-minute refreshers does not belong in the gate. The
fail direction is exact: the pre-cure files contain the
materializing calls and fail every assertion below.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FILES = ("refresh_earningsdistribution.py",
         "refresh_insiderdivergence.py",
         "refresh_gammaearningstrap.py")


def _src(name):
    with open(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), name),
            encoding="utf-8") as fh:
        return fh.read()


def test_no_materializing_ledger_calls():
    for name in FILES:
        src = _src(name)
        assert "ledger.verify_chain()" not in src, name
        assert "ledger.rows()" not in src, name


def test_streaming_forms_in_use():
    for name in FILES:
        src = _src(name)
        assert src.count("ledger.verify_chain_streaming()") >= 2, \
            name
        assert "for row in ledger.iter_rows():" in src, name
