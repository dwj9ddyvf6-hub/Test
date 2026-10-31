"""Regression blockers for DEEP-PASS 3.2 items 6 and 7
(2026-10-29): FE17's blend as Engine 12's centre, FE18 as a
ledgered sub forecast inside Engine 12, FE23's plan adjusted
insider flow into Engine 10, and the FE04 fair gap residual
named as an open remainder (no model fabricated).

Fail direction: site/engine_adaptations.py did not exist
before this item, and neither refresher carried the functions
or blocks named here, so this file fails on the pre-fix tree
at import.
"""

import importlib.util
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "site"))
FORECAST = os.path.normpath(os.path.join(HERE, ".."))
for p in (SITE, FORECAST):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ad = _load("engine_adaptations_test",
           os.path.join(SITE, "engine_adaptations.py"))
e12 = _load("refresh_earningsdistribution_adapt",
            os.path.join(SITE, "refresh_earningsdistribution.py"))
e10 = _load("refresh_insiderdivergence_adapt",
            os.path.join(SITE, "refresh_insiderdivergence.py"))
L = _load("forecast_ledger_adapt",
          os.path.join(FORECAST, "ledger.py"))
R = _load("forecast_registry_adapt",
          os.path.join(FORECAST, "registry.py"))
REG = R.Registry()

LINEAGE = {"source_artifacts": [], "note": "test",
           "clocks": {"event_time": "2026-11-10",
                      "publication_time": "2026-11-10",
                      "first_available_time": "2026-11-10",
                      "ingestion_time": "2026-11-10",
                      "decision_as_of": "2026-11-10"}}


# ---- FE17 centre -------------------------------------------------------

def test_fe17_centre_arithmetic():
    out = ad.fe17_centre(4.0, 2.0, 1.0, 0.5)
    # (0.6*4 + 0.4*2) * (1 + 0.08) * 0.5 = 3.2 * 1.08 * 0.5
    assert out["state"] == "recorded"
    assert out["centre_pct"] == pytest.approx(1.728)
    assert out["dispersion_adjustment"] == pytest.approx(0.08)
    # normalised model score is the forecast itself, not the
    # dispersion adjustment minus 1 from the source package
    assert out["model_score_normalised"] == out["centre_pct"]


def test_fe17_dispersion_clipped_at_two():
    out = ad.fe17_centre(5.0, 5.0, 9.0, 1.0)
    assert out["dispersion_adjustment"] == pytest.approx(0.16)
    assert out["centre_pct"] == pytest.approx(5.8)


def test_fe17_missing_inputs_named_never_zeroed():
    out = ad.fe17_centre(None, 2.0, None, None)
    assert out["state"] == "not_recorded"
    assert out["centre_pct"] is None
    assert out["missing"] == ["implied_move",
                              "forecast_error_dispersion_z",
                              "timing_quality"]


def test_fe17_negative_move_refused_not_floored():
    with pytest.raises(ValueError):
        ad.fe17_centre(-1.0, 2.0, 0.0, 1.0)
    with pytest.raises(ValueError):
        ad.fe17_centre(2.0, 2.0, 0.0, 0.0)


def test_engine12_centre_not_recorded_today():
    view = {"state": "recorded", "typical_pct": 2.4555}
    out = e12.fe17_for_view(view, None)
    assert out["state"] == "not_recorded"
    assert "implied_move" in out["missing"]


# ---- FE18 sub forecast -------------------------------------------------

def test_fe18_score_arithmetic_and_breadth_floor():
    out = ad.fe18_score(2.0, 1.0, -1.0, 0.0)
    # (1.0 + 0.3 - 0.2) * 0.5 = 0.55: zero breadth keeps half
    assert out["score"] == pytest.approx(0.55)
    out = ad.fe18_score(2.0, 1.0, -1.0, 1.0)
    assert out["score"] == pytest.approx(1.1)


def test_fe18_missing_named_and_clip():
    out = ad.fe18_score(None, 1.0, 0.0, None)
    assert out["state"] == "not_recorded"
    assert out["missing"] == ["standardized_surprise_z",
                              "revision_breadth"]
    assert ad.fe18_score(100.0, 0.0, 0.0, 1.0)["score"] == 8.0
    with pytest.raises(ValueError):
        ad.fe18_score(1.0, 1.0, 1.0, 1.5)


def test_fe18_state_for_upcoming_reporter():
    out = e12.fe18_state_for_view("2026-10-30", "2026-10-29")
    assert out["state"] == "awaiting_drift_window"
    assert "revision_breadth" in out["missing"]


def _fe18_call(led, **kw):
    base = dict(symbol="TEST", issued_ts="2026-11-10T00:00:00Z",
                drift_close="2026-11-06",
                horizon_open="2026-11-09",
                horizon_close="2026-11-13",
                inputs={"standardized_surprise_z": 2.0,
                        "observed_post_event_drift_z": 1.0,
                        "sector_residual_z": -1.0,
                        "revision_breadth": 1.0},
                lineage=LINEAGE)
    base.update(kw)
    return e12.ledger_fe18_sub_forecast(led, **base)


def test_fe18_ledger_refuses_issue_before_drift_close(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    with pytest.raises(ValueError):
        _fe18_call(led, issued_ts="2026-11-06T00:00:00Z")
    assert led.rows() == []


def test_fe18_ledger_records_after_drift_close(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    row, created = _fe18_call(led)
    assert created
    assert row["value"]["leg"] == "fe18_pead"
    assert row["value"]["score"] == pytest.approx(1.1)
    assert row["outcome"]["base_date"] == "2026-11-06"
    assert led.verify_chain()


def test_fe18_ledger_abstains_with_reasons_when_inputs_absent(
        tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    row, created = _fe18_call(
        led, inputs={"observed_post_event_drift_z": 1.0,
                     "sector_residual_z": 0.5})
    assert created
    assert row["absence_state"] == "no_data"
    reasons = row.get("abstain_reasons") or []
    assert any("standardized_surprise_z" in r for r in reasons)
    assert any("revision_breadth" in r for r in reasons)


# ---- FE23 classifier and adjusted flow ---------------------------------

def test_plan_classifier_reads_footnotes():
    plan = ("The sale was effected pursuant to a Rule 10b5-1 "
            "trading plan adopted on March 3, 2026.")
    out = ad.classify_plan_status(plan)
    assert out["label"] == "plan_10b5_1"
    assert out["confidence"] > 0.9
    plain = "The reporting person sold shares on the open market."
    assert ad.classify_plan_status(plain)["label"] == \
        "discretionary"
    assert ad.classify_plan_status("")["label"] == "unknown"
    assert ad.classify_plan_status(None)["confidence"] is None


def test_classifier_precision_and_kill_floor():
    labelled = ([("Sale under a 10b5-1 plan.", "plan_10b5_1")] * 19
                + [("Open market sale.", "plan_10b5_1")])
    rep = ad.classifier_precision(labelled)
    assert rep["precision"] == pytest.approx(1.0)
    assert ad.classifier_kill_state(rep) == "standing"
    bad = ([("Sale under a 10b5-1 plan.", "discretionary")] * 10
           + [("Sale under a 10b5-1 plan.", "plan_10b5_1")] * 10)
    rep2 = ad.classifier_precision(bad)
    assert rep2["precision"] == pytest.approx(0.5)
    assert ad.classifier_kill_state(rep2) == "retired"
    thin = ad.classifier_precision(labelled[:3])
    assert ad.classifier_kill_state(thin) == "unmeasured"


def test_fe23_adjusted_flow_form():
    out = ad.fe23_adjusted_flow(2.0, 0.8, 0.5, 1.0)
    # 2.0 * 0.8 * 0.5 / (1 + 1.0) = 0.4
    assert out["score"] == pytest.approx(0.4)
    # liquid issuers (negative illiquidity z) get no boost
    out = ad.fe23_adjusted_flow(2.0, 1.0, 1.0, -3.0)
    assert out["score"] == pytest.approx(2.0)
    out = ad.fe23_adjusted_flow(None, 1.0, 1.0, 0.0)
    assert out["state"] == "not_recorded"
    with pytest.raises(ValueError):
        ad.fe23_adjusted_flow(1.0, 1.5, 1.0, 0.0)


def test_engine10_plan_block_honest_state():
    # Cured truth (FE23 cure, 2026-10-30; expectation updated in
    # the sweep machinery pass the same day, noted in the
    # terminal BUGLOG): the Form 4 footnote record now exists on
    # disk, so the block reads recorded, not the pre-cure
    # not_recorded wording this test was written against. The
    # counts are pinned to the record the block itself publishes
    # (43 names classified, precision 1.0 on 645 labelled
    # footnotes at the cure's publication).
    block = e10.plan_adjustment_block({"AAA": {}, "BBB": {}})
    assert block["state"] == "recorded"
    assert block["classifier_state"] == "standing"
    assert block["names_classified"] == 43
    assert block["names_classified"] == len(block["classified"])
    assert block["names_with_summaries"] == 2
    assert block["precision_kill_floor"] == \
        ad.PLAN_CLASSIFIER_PRECISION_FLOOR
    assert block["precision"]["precision"] == pytest.approx(1.0)
    assert block["precision"]["labelled"] == 645
    assert block["footnote_record"]["filings_on_record"] > 0


def test_engine10_plan_block_not_recorded_without_footnote_record(
        monkeypatch):
    # The honest fallback stands: with no footnote record on
    # disk the block is not_recorded and classifies nothing.
    monkeypatch.setattr(e10, "_footnote_record", lambda: {})
    block = e10.plan_adjustment_block({"AAA": {}, "BBB": {}})
    assert block["state"] == "not_recorded"
    assert block["names_classified"] == 0
    assert block["classifier_state"] == "unmeasured"
    assert block["precision_kill_floor"] == \
        ad.PLAN_CLASSIFIER_PRECISION_FLOOR
    assert block["precision"]["precision"] is None
