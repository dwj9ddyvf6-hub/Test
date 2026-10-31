"""Regression blocker for defect (8), 2026-10-30: grades on voided
forecasts pooled into published graded counts and means.

Fail direction: on the pre-cure code, recompute_figures counts a
grade on a correction-voided forecast in graded and in the mean,
append_grade happily grades a voided forecast, run_grading never
names a voided skip, and verify_grade_rows does not exist. Each
test below fails on that code and passes after the cure.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402
import ledger as L  # noqa: E402
import registry as R  # noqa: E402
import verify_grade_rows as V  # noqa: E402

REG = R.load()
CLOCKS = {c: "2026-10-20T13:00:00Z" for c in L.CLOCK_FIELDS}
LINEAGE = {"source_artifacts": [{"path": "fixture.json",
                                 "sha256": "ab" * 32}],
           "clocks": CLOCKS}


def make_ledger(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    return led


def forecast_kwargs(**over):
    kw = dict(engine_id="engine_01", issued_ts="2026-10-20T13:00:00Z",
              subject="SPY", quantity="close_band_5s",
              value={"lower": 100.0, "upper": 110.0,
                     "stated_coverage": 0.68},
              horizon_open="2026-10-21", horizon_close="2026-10-27",
              lineage=LINEAGE, families=["distributional_volatility"],
              outcome={"symbol": "SPY", "kind": "close",
                       "at_date": "2026-10-27"})
    kw.update(over)
    return kw


def test_recompute_excludes_grades_on_voided(tmp_path):
    led = make_ledger(tmp_path)
    bad, _ = led.append_forecast(**forecast_kwargs(subject="BAD"))
    good, _ = led.append_forecast(**forecast_kwargs(subject="GOOD"))
    led.append_grade(forecast_row=bad,
                     grade={"scores": {"brier": 10.0}})
    led.append_grade(forecast_row=good,
                     grade={"scores": {"brier": 2.0}})
    led.append_correction(
        corrects_row_id=bad["row_id"], note="Void: test",
        payload={"engine_id": "engine_01", "reason": "test void"})
    eng = L.recompute_figures(led.rows())["engine_01"]
    assert eng["forecasts"] == 2
    assert eng["forecasts_voided"] == 1
    assert eng["forecasts_valid"] == 1
    assert eng["graded_raw"] == 2
    assert eng["grades_on_voided"] == 1
    assert eng["graded"] == 1
    assert eng["mean_scores"]["brier"] == 2.0


def test_append_grade_refuses_voided_forecast(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs())
    led.append_correction(
        corrects_row_id=row["row_id"], note="Void: test",
        payload={"engine_id": "engine_01", "reason": "test void"})
    with pytest.raises(L.LedgerError, match="voided by correction"):
        led.append_grade(forecast_row=row,
                         grade={"scores": {"brier": 1.0}})


def test_run_grading_skips_voided_with_named_reason(tmp_path):
    led = make_ledger(tmp_path)
    row, _ = led.append_forecast(**forecast_kwargs())
    led.append_correction(
        corrects_row_id=row["row_id"], note="Void: test",
        payload={"engine_id": "engine_01", "reason": "test void"})
    skipped = []
    grades = G.run_grading(led, prices=None, registry=REG,
                           skipped=skipped)
    assert grades == []
    assert len(skipped) == 1
    assert "voided by correction" in skipped[0]["reason"]


def test_verifier_recount_names_voided_population(tmp_path):
    led = make_ledger(tmp_path)
    bad, _ = led.append_forecast(**forecast_kwargs(subject="BAD"))
    good, _ = led.append_forecast(**forecast_kwargs(subject="GOOD"))
    led.append_grade(forecast_row=bad,
                     grade={"scores": {"brier": 10.0}})
    led.append_grade(forecast_row=good,
                     grade={"scores": {"brier": 2.0}})
    led.append_correction(
        corrects_row_id=bad["row_id"], note="Void: test",
        payload={"engine_id": "engine_01", "reason": "test void"})
    result = V.recount(led.path)
    assert result["first_break"] is None
    eng = result["per_engine"]["engine_01"]
    assert eng["forecasts_valid"] == 1
    assert eng["grades_on_voided"] == 1
    assert eng["grades_valid"] == 1
    assert eng["orphan_grades"] == 0
    assert eng["double_grades"] == 0
    assert eng["mean_scores_valid"]["brier"] == 2.0
