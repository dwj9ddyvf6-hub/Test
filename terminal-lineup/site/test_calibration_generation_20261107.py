"""Regression blocker for CALIBRATION-GENERATION-20261107.

The calibration league demanded the live ledger count of
engine_15 forecasts equal the count its own page publishes.
The page is written by the engine's own refresher at the end of
the run's longest leg, after its appends; two runs killed inside
that leg banked appends the page never caught up with, and the
check then reported the same frozen 6,606-row gap across four
consecutive runs on a healthy record (a completed run leaves
both sides agreeing to the row).

The cure stamps the page with its generation
(ledger_rows_at_write, written by refresh_selfanalogue) and
binds the comparison at that generation: the engine's appends
after the page's checkpoint are expected accrual; a page wrong
at its own generation still fails. These tests pin the
arithmetic and the producer's stamp. Set LEG_MODULE_DIR to a
directory holding pre-cure copies of the refreshers to watch
them fail.
"""
import importlib.util
import os

import pytest

MODULE_DIR = os.environ.get(
    "LEG_MODULE_DIR", os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(MODULE_DIR, "refresh_calibrationleague.py")
PRODUCER_PATH = os.path.join(MODULE_DIR, "refresh_selfanalogue.py")

spec = importlib.util.spec_from_file_location("refresh_calibrationleague", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(kind, engine):
    return {"type": kind, "engine_id": engine}


def ledger(prefix_rows, appended):
    return [row("forecast", "engine_15")] * prefix_rows + appended


def test_banked_appends_after_a_kill_are_expected_accrual():
    # The live failure shape: the page published 63,669 at its
    # checkpoint; killed runs banked 6,606 more engine_15
    # forecasts; the live count is 70,275 and must pass.
    rows = ledger(1000, [row("forecast", "engine_15")] * 6606
                  + [row("grade", "engine_15")] * 40
                  + [row("forecast", "engine_02")] * 90)
    assert mod.expected_page_count(63669, 1000, rows, "engine_15") \
        == 70275


def test_a_page_wrong_at_its_own_generation_still_fails():
    # 1,000 ledger rows at the page's checkpoint (all engine_15
    # forecasts here), then 10 more appends: the live count is
    # 1,010. A page that published the true count for its
    # generation matches; a page that was wrong at its own
    # generation (990 for the same checkpoint) still fails.
    rows = ledger(1000, [row("forecast", "engine_15")] * 10)
    live = 1010
    assert mod.expected_page_count(1000, 1000, rows, "engine_15") == live
    assert mod.expected_page_count(990, 1000, rows, "engine_15") != live


def test_checkpoint_counts_only_that_engines_forecasts():
    rows = ledger(50, [row("forecast", "engine_02"),
                       row("grade", "engine_15"),
                       row("correction", "engine_15"),
                       row("forecast", "engine_15")])
    assert mod.expected_page_count(50, 50, rows, "engine_15") == 51


def test_no_checkpoint_falls_back_to_strict_equality():
    rows = ledger(10, [row("forecast", "engine_15")] * 3)
    assert mod.expected_page_count(10, None, rows, "engine_15") == 10


def test_producer_stamps_its_generation():
    with open(PRODUCER_PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert '"ledger_rows_at_write": len(rows)' in src


def test_checker_reads_the_checkpoint():
    with open(PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert "ledger_checkpoint_src" in src
    assert "expected_page_count" in src


if __name__ == "__main__":
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
