"""Regression blocker for PANEL-LAGGARD-DEADNAMES-20261104.

The PANEL-LAGGARD-GAP-20261104 cure made the price panel advance lane
merge interior gaps, but its success criterion required at least one
appended bar on every run. The panel permanently contains names that
stopped trading (MAG last bar 2025-09-03, CYBR 2026-02-10, 21 such
symbols at the 2026-11-04 census), whose last dates never advance, so
once every fillable gap was filled the lane failed fatally on every
run and blocked the refresh spine (grading, engines, Record, smoke,
publish). The verdict must distinguish a broken fetch (nothing served
at all: still a failure) from a healthy no-op (source served bars,
none new: success, laggards named).

On the pre-cure code these tests fail: classify_advance does not
exist (ImportError), which is the fail direction.
"""
import importlib.util
import os

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
spec = importlib.util.spec_from_file_location(
    "advance_price_panel", os.path.join(SITE, "advance_price_panel.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_broken_fetch_still_fails():
    assert mod.classify_advance({}, {}) == "fail"
    assert mod.classify_advance({}, {"SPY": {}}) == "fail"


def test_healthy_noop_when_source_serves_but_nothing_new():
    fetched = {"SPY": {"2026-11-03": ["2026-11-03", 1, 1, 1, 1, 10]},
               "MAG": {}}
    assert mod.classify_advance({}, fetched) == "noop"


def test_advanced_when_a_gap_was_filled():
    appended = {"SUPN": ["2026-11-02"]}
    fetched = {"SUPN": {"2026-11-02": ["2026-11-02", 1, 1, 1, 1, 10]}}
    assert mod.classify_advance(appended, fetched) == "advanced"
