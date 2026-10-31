"""Blockers for DEEP-PASS 3.2 items 8, 9 and 12 (2026-10-29).

Source clock interval suppression, boundary sweep parity standard,
and confluence renormalisation floors on weight, not count.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import diagnostics_patterns as dp  # noqa: E402


def hist(source, n, successes, family="terminal_refresh"):
    return [{"source": source, "family": family,
             "on_time": i < successes} for i in range(n)]


# --- 3.2.8 source clock ------------------------------------------------

def test_source_clock_exact_pool_laplace_and_wilson():
    out = dp.estimate_source_clock(hist("chain", 30, 15), "chain")
    assert out["state"] == "exact"
    assert out["estimate"] == pytest.approx(16 / 32)
    assert out["wilson_interval"] is not None
    lo, hi = out["wilson_interval"]
    assert 0 <= lo < out["estimate"] < hi <= 1
    assert out["kind"] == "data_arrival_diagnostic_not_a_forecast"


def test_source_clock_insufficient_suppresses_interval():
    # His flaw: an interval was returned even when the estimate was
    # refused. Here both must be None together.
    out = dp.estimate_source_clock(hist("chain", 3, 2), "chain")
    assert out["state"] == "insufficient_history"
    assert out["estimate"] is None
    assert out["wilson_interval"] is None


def test_source_clock_family_fallback_is_labelled():
    rows = hist("a", 20, 10) + hist("b", 20, 10)
    out = dp.estimate_source_clock(rows, "a", family="terminal_refresh")
    assert out["state"] == "family" and out["pool"] == "family"
    assert out["n"] == 40


def test_source_clock_label_timing_contradiction_raises():
    rows = hist("a", 30, 15)
    rows[0].update({"horizon_seconds": 100, "label_start": 0,
                    "label_end": 500})
    with pytest.raises(ValueError):
        dp.estimate_source_clock(rows, "a")


def test_parse_refresh_log_and_age_bands():
    text = ("start x (refresh_x.py)\n"
            "done x in 3s exit 0\n"
            "done y in 1s exit 1\n"
            "start z (refresh_z.py)\n")
    rows = dp.parse_refresh_proof_log(text)
    assert [(r["source"], r["on_time"]) for r in rows] == [
        ("x", True), ("y", False)]
    assert dp.age_band(0.25) == 0 and dp.age_band(1.5) == 2
    assert dp.age_band(9.0) == 5 and dp.age_band(-1) is None


def test_diagnostic_over_logs_labels_not_forecast():
    text = "\n".join(f"done s{i%3} in 1s exit {i%2}" for i in range(40))
    out = dp.diagnostic_over_refresh_logs([text], min_samples=30)
    assert out["kind"] == "data_arrival_diagnostic_not_a_forecast"
    assert "Not a market forecast" in out["label"]


# --- 3.2.9 boundary sweeps ----------------------------------------------

def mult(point):
    return point["a"] * point["b"]


def test_boundary_sweep_corners_and_range():
    out = dp.boundary_sweep(mult, {"a": 2.0, "b": 3.0},
                            {"a": (0.0, 4.0), "b": (0.0, 5.0)})
    assert out["status"] == "ok" and out["baseline"] == 6.0
    assert out["score_max"] == 20.0 and out["score_min"] == 0.0
    kinds = {c["kind"] for c in out["cases"]}
    assert kinds == {"one_feature", "pairwise", "joint_corner"}


def test_boundary_sweep_abstained_baseline_no_map():
    out = dp.boundary_sweep(lambda p: None, {"a": 1.0},
                            {"a": (0.0, 2.0)})
    assert out["status"] == "unavailable_baseline_abstained"
    assert out["cases"] == []


def test_boundary_sweep_rejects_baseline_outside_range():
    with pytest.raises(ValueError):
        dp.boundary_sweep(mult, {"a": 9.0, "b": 1.0},
                          {"a": (0.0, 4.0), "b": (0.0, 5.0)})


def test_parity_sweep_catches_mirror_bug_in_corner_only():
    def broken(point):  # agrees in the interior, wrong at a corner
        if point["a"] == 0.0:
            return 999.0
        return mult(point)
    out = dp.parity_sweep(mult, broken, {"a": 2.0, "b": 3.0},
                          {"a": (0.0, 4.0), "b": (0.0, 5.0)})
    assert out["status"] == "mismatch" and out["mismatches"]
    ok = dp.parity_sweep(mult, mult, {"a": 2.0, "b": 3.0},
                         {"a": (0.0, 4.0), "b": (0.0, 5.0)})
    assert ok["status"] == "ok" and ok["cases_checked"] > 1


# --- 3.2.12 confluence renormalisation -----------------------------------

def test_weight_floor_not_count_floor():
    # Seven light metrics present, the heavy one blank: count coverage
    # is 7/8 (passes a count floor), weight coverage is 0.07 (fails).
    items = [{"value": 90.0, "weight": 0.01, "present": True}
             for _ in range(7)]
    items.append({"value": None, "weight": 0.93, "present": False})
    out = dp.renormalised_composite(items, floor=0.60)
    assert out["coverage_count"] == pytest.approx(7 / 8)
    assert out["coverage_weight"] == pytest.approx(0.07)
    assert out["passes_weight_floor"] is False
    assert out["score"] == pytest.approx(90.0)  # renormalised, flagged


def test_renormalised_composite_and_format_carry_coverage():
    items = [{"value": 80.0, "weight": 3.0, "present": True},
             {"value": 60.0, "weight": 1.0, "present": True},
             {"value": None, "weight": 1.0, "present": False}]
    out = dp.renormalised_composite(items)
    assert out["score"] == pytest.approx(75.0)
    assert out["coverage_weight"] == pytest.approx(0.8)
    text = dp.format_score_with_coverage(out)
    assert "Score: 75.0" in text and "Coverage: 80% of weight" in text


def test_board_and_router_carry_coverage_beside_score():
    site = os.path.expanduser("~/workspace/terminal-lineup/site")
    board_html = open(os.path.join(site, "board", "index.html")).read()
    assert "Coverage <strong>" in board_html
    assert "data_behind_score_pct" in board_html or \
        "coverage_pct" in board_html
    router_html = open(os.path.join(
        site, "living-router", "index.html")).read()
    assert "coverage_weight" in router_html
    router_src = open(os.path.join(site, "refresh_livingrouter.py")).read()
    assert "coverage_weight" in router_src
