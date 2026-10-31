"""Regression blockers for DEEP-PASS 3.2 items 4 and 5: horizon
overlap measurement on the Record, BH correction and paired loss
deltas in the grading runner, and the calibration attestation as a
publishing rule.

Fail direction: on the pre-fix machinery these tests fail because
grading.py has no session interval geometry, no benjamini_hochberg,
no paired loss delta or cell family report, and no attestation
gate, and registry.json carries no calibration_attestation field
on any engine.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import grading as G  # noqa: E402
import registry as R  # noqa: E402


# ---- session interval geometry (item 4) -------------------------------

def test_geometry_disjoint_intervals():
    geo = G.session_interval_geometry([(0, 20), (21, 41), (42, 62)])
    assert geo == {"windows": 3, "overlapping_pairs": 0,
                   "max_concurrency": 1, "largest_component": 1,
                   "independent_windows": 3}


def test_geometry_overlapping_chain():
    # (0,20) and (10,30) share sessions; (10,30) and (25,45) share
    # sessions; (0,20) and (25,45) do not. One component of 3, and
    # the maximum non overlapping subset is 2.
    geo = G.session_interval_geometry([(0, 20), (10, 30), (25, 45)])
    assert geo["windows"] == 3
    assert geo["overlapping_pairs"] == 2
    assert geo["max_concurrency"] == 2
    assert geo["largest_component"] == 3
    assert geo["independent_windows"] == 2


def test_geometry_nested_intervals():
    geo = G.session_interval_geometry([(0, 40), (5, 10), (12, 18)])
    assert geo["overlapping_pairs"] == 2
    assert geo["max_concurrency"] == 2
    assert geo["largest_component"] == 3
    assert geo["independent_windows"] == 2


def test_geometry_empty():
    geo = G.session_interval_geometry([])
    assert geo["windows"] == 0
    assert geo["independent_windows"] == 0


def _cal(n=80):
    # Synthetic session calendar: consecutive real weekdays from
    # Monday 2026-01-05, so the derived weekday axis and an
    # explicitly supplied calendar agree exactly.
    from datetime import date, timedelta
    out = []
    d = date(2026, 1, 5)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _frow(engine, open_i, close_i, cal, symbol="SPY"):
    return {"type": "forecast", "engine_id": engine,
            "absence_state": "present", "subject": symbol,
            "horizon_open": cal[open_i], "horizon_close": cal[close_i],
            "outcome": {"kind": "close", "symbol": symbol},
            "value": {"p": 0.5}, "quantity": "q"}


def test_record_overlap_counts_independent_windows_beside_rows():
    cal = _cal()
    rows = [
        _frow("engine_10", 0, 20, cal),    # 21 sessions, overlaps next
        _frow("engine_10", 5, 25, cal),    # 21 sessions
        _frow("engine_10", 30, 50, cal),   # 21 sessions, disjoint
        _frow("engine_09", 0, 4, cal),     # 5 sessions: not measured
    ]
    rep = G.record_horizon_overlap(rows, calendars={"SPY": cal})
    cell = rep["by_engine"]["engine_10"][21]
    assert cell["rows"] == 3
    assert cell["independent_windows"] == 2
    assert cell["overlapping_pairs"] == 1
    assert "engine_09" not in rep["by_engine"]
    assert rep["basis"].startswith("session intervals")


def test_record_overlap_unplaced_rows_are_named_not_dropped():
    cal = _cal(10)
    rows = [_frow("engine_10", 0, 20, _cal(40))]  # close not in cal
    rep = G.record_horizon_overlap(rows, calendars={"SPY": cal})
    assert rep["unplaced"] == 1
    assert rep["by_engine"] == {}


def test_record_overlap_derives_the_records_weekday_axis():
    # No calendar supplied: the axis is the weekday calendar the
    # record's horizon dates were issued under, so rows place and
    # the stated session count is the measured span.
    cal = _cal()
    rows = [_frow("engine_10", 0, 20, cal),
            _frow("engine_10", 30, 50, cal)]
    rep = G.record_horizon_overlap(rows)
    cell = rep["by_engine"]["engine_10"][21]
    assert cell["rows"] == 2
    assert cell["independent_windows"] == 2
    assert rep["unplaced"] == 0
    assert "weekday" in rep["basis"]


# ---- BH correction (item 5) -------------------------------------------

def test_bh_known_values():
    q = G.benjamini_hochberg([0.005, 0.01, 0.03, 0.04])
    assert q == pytest.approx([0.02, 0.02, 0.04, 0.04])


def test_bh_preserves_input_order_and_enforces_monotonicity():
    q = G.benjamini_hochberg([0.04, 0.05])
    assert q == pytest.approx([0.05, 0.05])
    q2 = G.benjamini_hochberg([0.04, 0.005])
    assert q2 == pytest.approx([0.04, 0.01])


def test_bh_edge_cases():
    assert G.benjamini_hochberg([]) == []
    assert G.benjamini_hochberg([0.5]) == pytest.approx([0.5])
    assert G.benjamini_hochberg([1.0, 1.0]) == pytest.approx([1.0, 1.0])


def test_binomial_two_sided_known_value():
    # 9 heads in 10 fair flips: two sided p = 22/1024.
    p = G.binomial_two_sided_p(9, 10, 0.5)
    assert p == pytest.approx(22 / 1024)


# ---- paired loss deltas (item 5) ---------------------------------------

def test_paired_loss_deltas_all_engine_better():
    pairs = [(0.10, 0.30)] * 8
    out = G.paired_loss_deltas(pairs)
    assert out["n"] == 8
    assert out["mean_delta"] == pytest.approx(0.20)
    assert out["engine_better_share"] == 1.0
    # Sign test: 8 of 8 nonzero deltas in one direction.
    assert out["p_value"] == pytest.approx(2 * 0.5 ** 8)


def test_paired_loss_deltas_ties_carry_no_sign():
    out = G.paired_loss_deltas([(0.2, 0.2), (0.1, 0.3)])
    assert out["n"] == 2
    assert out["ties"] == 1
    assert out["p_value"] == pytest.approx(1.0)


def _grade(row_id, scores, binary=1.0):
    return {"type": "grade", "forecast_row_id": row_id,
            "grade": {"scores": scores, "binary_outcome": binary}}


def test_paired_baseline_report_engine30_control():
    rows = []
    for i in range(6):
        fid = f"f{i}"
        rows.append({"type": "forecast", "row_id": fid,
                     "engine_id": "engine_30", "quantity": "chance",
                     "subject": "SPY", "absence_state": "present",
                     "value": {"p": 0.9, "p_control_vix_only": 0.5},
                     "outcome": {"kind": "realised_vol", "symbol": "SPY"}})
        rows.append(_grade(fid, {"brier": 0.01}))
    rep = G.paired_baseline_report(rows)
    cell = rep["engine_30"]
    assert cell["pairs"] == 6
    assert cell["baseline"].startswith("declared baseline")
    # Engine brier 0.01 vs control (0.5-1)^2 = 0.25 every time.
    assert cell["mean_delta"] == pytest.approx(0.24)
    assert cell["p_value"] == pytest.approx(2 * 0.5 ** 6)


def test_paired_baseline_report_engine17_benchmark_rows():
    rows = []
    for i, sym in enumerate(("AAA", "BBB", "CCC", "DDD")):
        cal = _cal()
        base = {"type": "forecast", "engine_id": "engine_17",
                "subject": sym, "absence_state": "present",
                "horizon_open": cal[0], "horizon_close": cal[4],
                "outcome": {"kind": "realised_range_5s", "symbol": sym}}
        main = dict(base, row_id=f"m{i}",
                    quantity="Predicted 5-session realised range",
                    value={"estimate": 3.0})
        bench = dict(base, row_id=f"b{i}",
                     quantity="Benchmark: predicted 5-session range",
                     value={"estimate": 5.0})
        rows += [main, bench,
                 _grade(f"m{i}", {"abs_error": 1.0}, binary=None),
                 _grade(f"b{i}", {"abs_error": 2.5}, binary=None)]
    rep = G.paired_baseline_report(rows)
    cell = rep["engine_17"]
    assert cell["pairs"] == 4
    assert cell["mean_delta"] == pytest.approx(1.5)


def test_paired_baseline_report_names_engines_with_no_pairs():
    rep = G.paired_baseline_report([])
    assert rep["engine_30"]["pairs"] == 0
    assert rep["engine_30"]["p_value"] is None
    assert "no graded pairs" in rep["engine_30"]["state"]


# ---- published cell family with BH (item 5) ----------------------------

def test_cell_family_coverage_cell_gets_binomial_p_and_bh_q():
    rows = []
    for i in range(10):
        fid = f"c{i}"
        hit = 1.0 if i < 9 else 0.0
        rows.append({"type": "forecast", "row_id": fid,
                     "engine_id": "engine_21", "quantity": "band",
                     "subject": "SPY", "absence_state": "present",
                     "value": {"lower": 0.0, "upper": 1.0,
                               "stated_coverage": 0.5},
                     "outcome": {"kind": "close", "symbol": "SPY"}})
        rows.append(_grade(fid, {"coverage_hit": hit}, binary=None))
    fam = G.engine_cell_family(rows)["engine_21"]
    assert len(fam["cells"]) == 1
    cell = fam["cells"][0]
    assert cell["n"] == 10
    assert cell["mean"] == pytest.approx(0.9)
    assert cell["p_value"] == pytest.approx(22 / 1024)
    assert cell["q_value"] == pytest.approx(22 / 1024)
    assert fam["tested_cells"] == 1


def test_cell_family_untested_cell_carries_reason_not_a_number():
    rows = [{"type": "forecast", "row_id": "x1", "engine_id": "engine_02",
             "quantity": "touch", "subject": "SPY",
             "absence_state": "present", "value": {"p": 0.5},
             "outcome": {"kind": "touch", "symbol": "SPY"}},
            _grade("x1", {"brier": 0.25, "log_loss": 0.69})]
    fam = G.engine_cell_family(rows)["engine_02"]
    by_score = {c["score"]: c for c in fam["cells"]}
    assert by_score["brier"]["p_value"] is None
    assert by_score["brier"]["q_value"] is None
    assert "no declared baseline" in by_score["brier"]["p_reason"]
    assert fam["tested_cells"] == 0


def test_cell_family_quantile_band_coverage_uses_stated_080():
    rows = []
    for i in range(10):
        fid = f"q{i}"
        rows.append({"type": "forecast", "row_id": fid,
                     "engine_id": "engine_12", "quantity": "dist",
                     "subject": "SPY", "absence_state": "present",
                     "value": {"quantiles": {"0.1": 1.0, "0.9": 2.0}},
                     "outcome": {"kind": "close", "symbol": "SPY"}})
        rows.append(_grade(fid, {"coverage_hit": 1.0}, binary=None))
    cell = G.engine_cell_family(rows)["engine_12"]["cells"][0]
    assert cell["p_value"] is not None
    assert cell["p_reason"].startswith("binomial")


# ---- calibration attestation gate (item 5) -----------------------------

def test_live_registry_no_engine_is_attested():
    reg = R.load()
    assert len(reg.engines) == 30
    for eng in reg.engines.values():
        assert "calibration_attestation" in eng
        decision = G.probability_render_decision(eng)
        assert decision["render_as_probability"] is False
        assert "attestation" in decision["reason"]


def test_attestation_gate_opens_only_for_calibrated_oos_attestation():
    eng = {"id": "engine_x", "calibration_attestation": {
        "status": "calibrated_out_of_sample",
        "basis": "Brier reliability on 212 graded out of sample rows",
        "attested_on": "2026-10-29"}}
    decision = G.probability_render_decision(eng)
    assert decision["render_as_probability"] is True
    out = G.render_probability(eng, 0.42)
    assert out["rendered_as"] == "probability"
    assert out["value"] == 0.42


def test_render_probability_unattested_is_labelled_a_score():
    eng = {"id": "engine_x", "calibration_attestation": None}
    out = G.render_probability(eng, 0.42)
    assert out["rendered_as"] == "uncalibrated_score"
    with pytest.raises(G.GradingError):
        G.assert_probability_renderable(eng)


def test_malformed_attestation_fails_closed():
    eng = {"id": "engine_x", "calibration_attestation": {
        "status": "calibrated_out_of_sample", "basis": "",
        "attested_on": "2026-10-29"}}
    decision = G.probability_render_decision(eng)
    assert decision["render_as_probability"] is False
