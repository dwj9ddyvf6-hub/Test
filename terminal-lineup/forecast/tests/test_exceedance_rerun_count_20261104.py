"""Regression blocker for EXCEEDANCE-RERUN-COUNT-20261104.

Exceedance's post-write check demanded the ledger hold exactly this
run's forecast set for the as-of session. The ledger is append-only
and declared appends are idempotent, so a legitimate same-session
re-run with a smaller qualifying set failed forever: the 2026-11-03
session was published by the scheduled run from a price panel that
still had the SUPN hole (1,798 subjects on record), then the
supervised re-run after the PANEL-LAGGARD-GAP cure qualified 1,797
and the check failed at 5,394 rows vs 5,391 expected. The check now
proves this run's declared rows landed (exactly 3 per declared
subject) and names same-session rows from an earlier run as
superseded instead of failing on them.

On the pre-cure code these tests fail: count_check does not exist
(ImportError), which is the fail direction.
"""
import importlib.util
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "refresh_exceedance", os.path.join(SITE, "refresh_exceedance.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(subject, quantity):
    return {"type": "forecast", "subject": subject, "quantity": quantity}


def rows_for(*subjects):
    out = []
    for s in subjects:
        for q in ("ex1", "ex2", "dd"):
            out.append(row(s, q))
    return out


def test_exact_declared_set_passes_with_no_superseded():
    ok, n, sup = mod.count_check(rows_for("SPY", "AAPL"),
                                 {"SPY", "AAPL"})
    assert ok and n == 6 and sup == []


def test_earlier_run_rows_are_named_not_fatal():
    rows = rows_for("SPY", "AAPL") + rows_for("SUPN")
    ok, n, sup = mod.count_check(rows, {"SPY", "AAPL"})
    assert ok and n == 6 and sup == ["SUPN"]


def test_a_missing_declared_row_still_fails():
    rows = rows_for("SPY", "AAPL")[:-1]
    ok, n, sup = mod.count_check(rows, {"SPY", "AAPL"})
    assert not ok and n == 5


def test_a_declared_subject_with_no_rows_still_fails():
    ok, n, sup = mod.count_check(rows_for("SPY"), {"SPY", "AAPL"})
    assert not ok and n == 3
