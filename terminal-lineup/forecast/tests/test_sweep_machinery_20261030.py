"""Regression blockers for the sweep machinery pass (2026-10-30):
(a) refresh_hub.py provenance stamps (the R-09 residual named in
the wave 2 verification), (c) the Touch Surface and Exceedance
republication refusal on Engine 1's guard widened bands, and
(d) the XBPEW depth inf figure on the Pullback Norm page.

Fail directions, verified by construction against the pre-cure
tree: refresh_hub.py carried no stamp_for_script call and no
PROVENANCE_BY_SCRIPT entry; both band consumers recomputed the
unwidened recipe and compared it directly with Engine 1's
published (guard widened) edges, so their helper functions did
not exist and the demonstrated SPY figures disagreed to the
cent; pullback_study.depth_ranks divided by a zero median true
range and returned inf as a depth.
"""

import importlib.util
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "site"))
for p in (SITE,):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tc = _load("terminal_common_sweep", "terminal_common.py")
touch = _load("refresh_touchsurface_sweep", "refresh_touchsurface.py")
exceed = _load("refresh_exceedance_sweep", "refresh_exceedance.py")
pullback = _load("pullback_study_sweep", "pullback_study.py")


# ---- (a) refresh_hub provenance stamps ------------------------------

def test_refresh_hub_wired_to_stamp_like_other_refreshers():
    src = open(os.path.join(SITE, "refresh_hub.py"),
               encoding="utf-8").read()
    assert "import terminal_common as _tc" in src
    assert "stamp_for_script" in src
    assert "refresh_hub.py" in tc.PROVENANCE_BY_SCRIPT
    assert tc.provenance_for_script("refresh_hub.py") == (
        "filed_records", "session_record")


def test_no_refresh_script_unwired_on_final_tree():
    import glob
    unwired = [os.path.basename(p) for p in
               sorted(glob.glob(os.path.join(SITE, "refresh_*.py")))
               if "stamp_for_script" not in
               open(p, encoding="utf-8").read()]
    assert unwired == []


# ---- (c) Engine 1 guard widened band check --------------------------

# The demonstrated disagreement (2026-10-30 republication
# refusal): SPY close 769.36, unwidened h=1 half-width 0.4412
# percent, Engine 1 guard factor 1.2838, published (765.0,
# 773.72); SPY h=5 published (759.5, 779.22).
SPY_CLOSE = 769.36
GUARD = 1.2838


def _band_data(guard):
    return {"live": {"session_quality_guard": guard}}


def test_guard_factor_reads_engine1_published_factor():
    band = _band_data({"deterioration": 1.1353,
                       "band_widen_factor": GUARD,
                       "state": "partial"})
    assert touch.engine1_guard_factor(band) == GUARD
    assert exceed.engine1_guard_factor(band) == GUARD


def test_guard_factor_is_one_when_no_widening_recorded():
    assert touch.engine1_guard_factor(_band_data(
        {"deterioration": None, "band_widen_factor": 1.0})) == 1.0
    assert exceed.engine1_guard_factor({"live": {}}) == 1.0
    assert touch.engine1_guard_factor({}) == 1.0


def test_expected_edges_reproduce_published_widened_bands():
    half1 = 0.004412  # SPY h=1 unwidened half-width, demonstrated
    assert touch.expected_published_edges(
        SPY_CLOSE, half1, GUARD) == (765.0, 773.72)
    assert exceed.expected_published_edges(
        SPY_CLOSE, half1, GUARD) == (765.0, 773.72)
    half5 = 0.009978  # SPY h=5 unwidened half-width, demonstrated
    assert touch.expected_published_edges(
        SPY_CLOSE, half5, GUARD) == (759.5, 779.22)
    # No guard: the unwidened edges the old check expected.
    assert touch.expected_published_edges(
        SPY_CLOSE, half1, 1.0) == (765.97, 772.75)


def test_band_consumers_apply_guard_factor_in_check():
    for name in ("refresh_touchsurface.py", "refresh_exceedance.py"):
        src = open(os.path.join(SITE, name), encoding="utf-8").read()
        assert "engine1_guard_factor(band_data)" in src, name
        assert "expected_published_edges" in src, name
        assert "engine1_band_check" in src, name


def test_published_pages_carry_band_check_and_no_band_refusal():
    for slug in ("touch-surface", "exceedance"):
        data = json.load(open(os.path.join(
            SITE, slug, "data.json"), encoding="utf-8"))
        check = data["live"]["engine1_band_check"]
        assert check["guard_widen_factor"] == GUARD, slug


# ---- (d) Pullback depth bound ---------------------------------------

def test_depth_ranks_zero_median_true_range_is_not_computable():
    closes = np.array([100.0] * 150 + [90.0] * 50)
    trs = np.zeros(200)
    depths, ranks = pullback.depth_ranks(closes, trs, 5, 5)
    assert all(math.isnan(d) or math.isfinite(d) for d in depths)
    # The drop sessions divided by a zero median true range
    # before the cure and published inf; now not computable.
    assert math.isnan(depths[150])
    assert math.isnan(ranks[150])


def test_depth_ranks_finite_depths_still_rank():
    closes = np.array([100.0] * 150 + [95.0] * 50)
    trs = np.ones(200)
    depths, ranks = pullback.depth_ranks(closes, trs, 5, 5)
    assert depths[150] == 5.0
    assert ranks[150] == 100.0


def test_pullback_page_and_record_publish_no_inf():
    for rel in (os.path.join("pullback-norm", "data.json"),
                os.path.join("pullback-norm", "study_record.json")):
        text = open(os.path.join(SITE, rel), encoding="utf-8").read()
        assert "Infinity" not in text, rel
        data = json.loads(text)
        study = data.get("study")
        signals = ((study.get("latest_signals")
                    if isinstance(study, dict) else None)
                   or data.get("latest_signals") or [])
        for sig in signals:
            assert math.isfinite(sig["depth"]), sig
