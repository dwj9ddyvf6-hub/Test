"""Regression blocker for EXCEEDANCE-RERUN-COUNT-20261104.

Exceedance's post-write check demanded the ledger hold exactly this
run's forecast set for the as-of session, counted in rows. The
ledger is append-only, so a legitimate same-session re-run failed
forever: the 2026-11-03 session was published by the scheduled run
from a price panel that still had the SUPN hole, then re-run after
the PANEL-LAGGARD-GAP cure filled it. One subject qualified in the
first run only; SUPN itself was appended a second time because its
declared thresholds moved by about a hundred-thousandth when its
own missing bar was filled (the declared identity carries the
outcome spec, so the moved threshold is a new row, not a reuse).
The check now proves this run's declared (subject, quantity) pairs
landed, and names the earlier run's rows as superseded (subject no
longer qualifying) or parallel (same pair, moved outcome) instead
of failing on them.

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

QS = ("ex1", "ex2", "dd")


def row(subject, quantity):
    return {"type": "forecast", "subject": subject, "quantity": quantity}


def rows_for(*subjects):
    out = []
    for s in subjects:
        for q in QS:
            out.append(row(s, q))
    return out


def test_exact_declared_set_passes_clean():
    ok, n, sup, par = mod.count_check(rows_for("SPY", "AAPL"),
                                      {"SPY", "AAPL"})
    assert ok and n == 6 and sup == [] and par == []


def test_dropped_subject_is_named_not_fatal():
    rows = rows_for("SPY", "AAPL") + rows_for("OLD")
    ok, n, sup, par = mod.count_check(rows, {"SPY", "AAPL"})
    assert ok and n == 6 and sup == ["OLD"] and par == []


def test_parallel_publication_is_named_not_fatal():
    rows = rows_for("SPY", "AAPL") + rows_for("SUPN") + rows_for("SUPN")
    ok, n, sup, par = mod.count_check(rows, {"SPY", "AAPL", "SUPN"})
    assert ok and n == 9 and sup == [] and par == ["SUPN"]


def test_a_missing_declared_pair_still_fails():
    rows = rows_for("SPY", "AAPL")[:-1]
    ok, n, sup, par = mod.count_check(rows, {"SPY", "AAPL"})
    assert not ok and n == 5


def test_a_declared_subject_with_no_rows_still_fails():
    ok, n, sup, par = mod.count_check(rows_for("SPY"), {"SPY", "AAPL"})
    assert not ok and n == 3
