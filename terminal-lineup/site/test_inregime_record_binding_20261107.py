"""Regression blocker for INREGIME-RECORD-BINDING-20261107.

The Board gate series builder was cross-checked against Horizon
Grades' published qualified aggregates. Horizon Grades computes
nothing: it republishes the Record's strongest block, and no
step in the daily run rebuilds it, so the check compared a live
recomputation against a frozen snapshot two Record generations
old (built 141 graded / 65 rose against the frozen 94 / 50) and
failed identically on every run while the current Record agreed
with the builder to the call.

The cure binds the gate to the source the republication copies:
the current Record's own strongest 1-day block, the same
generation as the groups the builder iterates. These tests pin
that binding with synthetic records: a stale Horizon page no
longer gates the series, and a Record that genuinely disagrees
with the builder still fails closed. Set LEG_MODULE_DIR to a
directory holding a pre-cure copy of the refresher to watch
them fail.
"""
import importlib.util
import os

import pytest

MODULE_DIR = os.environ.get(
    "LEG_MODULE_DIR", os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(MODULE_DIR, "refresh_inregimeoracle.py")

spec = importlib.util.spec_from_file_location("refresh_inregimeoracle", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

PANEL = {
    "SPY": [["2026-11-04", 0, 0, 0, 100.0, 0],
            ["2026-11-05", 0, 0, 0, 101.0, 0],
            ["2026-11-06", 0, 0, 0, 102.0, 0]],
    "AAA": [["2026-11-04", 0, 0, 0, 50.0, 0],
            ["2026-11-05", 0, 0, 0, 55.0, 0],
            ["2026-11-06", 0, 0, 0, 56.0, 0]],
    "BBB": [["2026-11-04", 0, 0, 0, 50.0, 0],
            ["2026-11-05", 0, 0, 0, 45.0, 0],
            ["2026-11-06", 0, 0, 0, 44.0, 0]],
}

STALE_HORIZON = {"horizons": [
    {"days": 1, "qualified": {"graded_count": 94, "rose_count": 50}}]}


def make_record(graded_count, rose_count):
    # One graded group on 2026-11-05, graded on 2026-11-06:
    # AAA rose (50 -> 56), BBB fell (50 -> 44). A third call did
    # not pass every check and never enters the series.
    return {"board": {
        "groups": [{
            "session": "2026-11-05",
            "grades": {"1d": {"state": "graded"}},
            "calls": [
                {"symbol": "AAA", "close": 50.0, "score": 1.0,
                 "passed_every_check": True},
                {"symbol": "BBB", "close": 50.0, "score": 2.0,
                 "passed_every_check": True},
                {"symbol": "AAA", "close": 50.0, "score": 3.0,
                 "passed_every_check": False},
            ]}],
        "strongest": {"calls": 2, "horizons": {"1d": {
            "state": "graded", "graded_count": graded_count,
            "rose_count": rose_count}}}}}


def test_stale_horizon_page_no_longer_gates_the_series():
    # The live failure shape: the builder and the Record agree
    # (2 graded, 1 rose); only the frozen republication differs.
    series, _dates = mod.board_gate_series(
        make_record(2, 1), STALE_HORIZON, PANEL)
    assert len(series) == 2
    assert sum(c["hit"] for c in series) == 1


def test_a_record_that_disagrees_still_fails_closed():
    with pytest.raises(SystemExit):
        mod.board_gate_series(make_record(3, 1), STALE_HORIZON, PANEL)
    with pytest.raises(SystemExit):
        mod.board_gate_series(make_record(2, 2), STALE_HORIZON, PANEL)


def test_an_ungraded_record_block_fails_closed():
    record = make_record(2, 1)
    record["board"]["strongest"]["horizons"]["1d"] = {"state": "waiting"}
    with pytest.raises(SystemExit):
        mod.board_gate_series(record, STALE_HORIZON, PANEL)


def test_source_binds_to_the_record_not_the_republication():
    with open(PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert 'record["board"]["strongest"]["horizons"]["1d"]' in src
    assert 'hz1 = {h["days"]: h for h in horizon["horizons"]}[1]' not in src


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
