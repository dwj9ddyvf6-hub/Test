"""Regression blockers for the 2026-11-10 forecast cure pair:
CALIBRATION-GENERATION-GENERAL-20261110 and
LEDGER-STREAM-CLOCKS-20261110.

Failures of record (manual full refresh, 2026-11-10 01:50 ET log):
- calibration-league failed closed: "engine_06 live count
  disagrees with its own page: 41323 vs 38659". Root cause: the
  runner refreshes engines alphabetically, so calibration-league
  runs second, before exceedance appends its day's forecasts;
  strict equality bound the league to the entrant's stale page
  from the previous cycle. Engine 15 already had the
  page-generation cure (CALIBRATION-GENERATION-20261107): bind at
  the page's own ledger checkpoint and count the engine's
  appends after it as expected accrual. The other five strict
  entrants never got it.
- capitulation-clock and completion-clock were SIGKILLed
  (exit -9) under the refresh's combined load. Both parsed the
  whole 660 MB ledger into lists twice (rows_before/rows_after)
  and hash-verified the parsed lists twice, holding two full
  parsed copies on a 6 GB box.

Cures pinned here:
- expected_page_count (the shared helper) keeps its semantics
  for every entrant: no checkpoint means strict equality; with a
  checkpoint the expected count is the page count plus the
  engine's own forecast rows after the checkpoint slice.
- The five strict entrants in refresh_calibrationleague.py now
  carry ledger_checkpoint_src from their pages and their main()
  binding runs through expected_page_count, with the mismatch
  message naming live count, page count, checkpoint and expected.
- Neither clock refresher calls led.rows(); both verify through
  verify_chain_streaming() and take figures through
  recompute_figures(led.iter_rows()); their row collections are
  engine-filtered iter_rows() streams.
"""
import ast
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "..", "site"))


def _load_calibrationleague():
    path = os.path.join(SITE, "refresh_calibrationleague.py")
    spec = importlib.util.spec_from_file_location(
        "refresh_calibrationleague_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_expected_page_count_applies_to_any_engine():
    mod = _load_calibrationleague()
    rows = (
        [{"type": "forecast", "engine_id": "engine_06"}
         for _ in range(5)]
        + [{"type": "forecast", "engine_id": "engine_12"}]
        + [{"type": "grade", "engine_id": "engine_06"}]
        + [{"type": "forecast", "engine_id": "engine_06"}
           for _ in range(3)])
    # No checkpoint: strict equality, the page count itself.
    assert mod.expected_page_count(100, None, rows, "engine_06") == 100
    # Checkpoint at index 5 of 10 rows: engine_06's 3 forecast
    # rows after it are expected accrual; engine_12's single
    # forecast row sits AT index 5, inside rows[5:], so it counts
    # as that engine's own accrual too; grade rows never count.
    assert mod.expected_page_count(100, 5, rows, "engine_06") == 103
    assert mod.expected_page_count(100, 5, rows, "engine_12") == 101


def test_main_binds_all_six_entrants_at_page_generation():
    src = open(os.path.join(
        SITE, "refresh_calibrationleague.py"), encoding="utf-8").read()
    assert src.count("expected_page_count(") >= 3, (
        "main() must route the five strict entrants and engine_15 "
        "through expected_page_count")
    assert "CALIBRATION-GENERATION-GENERAL-20261110" in src
    # Every entrant's measure entry carries the checkpoint field.
    assert src.count('"ledger_checkpoint_src"') >= 6, (
        "engine_01/02/05/06/12 measures plus engine_15 must all "
        "carry ledger_checkpoint_src")


def test_clock_refreshers_never_parse_the_whole_ledger():
    for name in ("refresh_capitulationclock.py",
                 "refresh_completionclock.py"):
        path = os.path.join(SITE, name)
        tree = ast.parse(open(path, encoding="utf-8").read())
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(
                    node.func, ast.Attribute) and node.func.attr == "rows":
                offenders.append(node.lineno)
        assert not offenders, (
            f"{name} still calls .rows() at lines {offenders}; "
            "the clocks must stream (LEDGER-STREAM-CLOCKS-20261110)")
        src = open(path, encoding="utf-8").read()
        assert "verify_chain_streaming()" in src, name
        assert "LEDGER-STREAM-CLOCKS-20261110" in src, name
    cap = open(os.path.join(
        SITE, "refresh_capitulationclock.py"), encoding="utf-8").read()
    assert "recompute_figures(led.iter_rows())" in cap
