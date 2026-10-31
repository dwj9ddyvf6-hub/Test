"""Regression blockers for DEEP-PASS 3.2 items 10, 11 and 14
(2026-10-29): FE12 as a session quality guard (one sided form
only, his intercept and weights not imported), FE20's panel
reliability form as the standard discount for panel derived
inputs (first on the 13F holder counts and the dark print
aggregates), and FE08 as a QLIKE graded HAR control under
Engines 1 and 7.

Fail direction: the FE12 and FE20 functions did not exist in
site/engine_adaptations.py before this item, neither panel
refresher carried a panel_reliability block or a panel history,
refresh_correctedband's bands_for took no guard, and
forecast/grading.py carried no QLIKE or HAR control, so this
file fails on the pre-fix tree at import or attribute access.
"""

import importlib.util
import json
import math
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


ad = _load("engine_adaptations_guard",
           os.path.join(SITE, "engine_adaptations.py"))
cb = _load("refresh_correctedband_guard",
           os.path.join(SITE, "refresh_correctedband.py"))
tf = _load("refresh_13ftracker_panel",
           os.path.join(SITE, "refresh_13ftracker.py"))
dp = _load("refresh_darkprints_panel",
           os.path.join(SITE, "refresh_darkprints.py"))
import grading as G  # noqa: E402


# ---- FE12: one sided form ------------------------------------

def test_fe12_improvement_never_raises_flag():
    g = ad.fe12_session_quality_guard(
        spread_z=-3.0, depth_drop_z=-2.0, volume_concentration=0.0,
        realised_vol_z=-1.0)
    assert g["state"] == "recorded"
    assert g["deterioration"] == 0.0
    assert g["band_widen_factor"] == 1.0
    assert g["tripped"] is False


def test_fe12_deterioration_is_graded_not_sigmoid():
    g = ad.fe12_session_quality_guard(
        spread_z=4.0, depth_drop_z=4.0, volume_concentration=1.0,
        realised_vol_z=4.0)
    # Graded linear scale: a worse session scores strictly worse,
    # with no saturation ceiling of the sigmoid form.
    worse = ad.fe12_session_quality_guard(
        spread_z=8.0, depth_drop_z=8.0, volume_concentration=1.0,
        realised_vol_z=8.0)
    assert worse["deterioration"] > g["deterioration"] > 1.0
    assert g["tripped"] is True


def test_fe12_missing_inputs_named_never_zero_filled():
    g = ad.fe12_session_quality_guard(spread_z=2.0)
    assert g["state"] == "partial"
    assert g["deterioration"] == 2.0  # mean over supplied only
    assert sorted(g["missing"]) == [
        "depth_drop_z", "realised_vol_z", "volume_concentration"]
    none = ad.fe12_session_quality_guard()
    assert none["state"] == "not_recorded"
    assert none["deterioration"] is None
    assert none["band_widen_factor"] == 1.0


def test_fe12_band_widening_and_abstention_raise():
    g = ad.fe12_session_quality_guard(
        spread_z=2.0, depth_drop_z=2.0, volume_concentration=0.0,
        realised_vol_z=2.0)
    lo, hi = ad.fe12_widen_band(90.0, 110.0, g)
    assert hi - lo > 20.0
    raised = ad.fe12_abstention_threshold(0.5, g)
    assert raised["threshold"] > 0.5 and raised["raised"] is True
    none = ad.fe12_session_quality_guard()
    assert ad.fe12_widen_band(90.0, 110.0, none) == (90.0, 110.0)
    assert ad.fe12_abstention_threshold(0.5, none)["threshold"] == 0.5


def test_fe12_concentration_range_refused():
    with pytest.raises(ValueError):
        ad.fe12_session_quality_guard(volume_concentration=1.5)


def test_correctedband_bands_guard_wiring():
    plain = cb.bands_for(100.0, 0.20, 5, False)
    not_recorded = cb.session_quality_guard()
    assert not_recorded["state"] == "not_recorded"
    assert cb.bands_for(100.0, 0.20, 5, False,
                        guard=not_recorded) == plain
    g = ad.fe12_session_quality_guard(
        spread_z=2.0, depth_drop_z=2.0, volume_concentration=0.0,
        realised_vol_z=2.0)
    widened = cb.bands_for(100.0, 0.20, 5, False, guard=g)
    for level in plain:
        assert widened[level][1] - widened[level][0] \
            > plain[level][1] - plain[level][0]


# ---- FE20: panel reliability discount -------------------------

def test_fe20_reliability_form_and_quartering():
    r = ad.fe20_panel_reliability(0.9, 0.99, 0.0)
    assert r["reliability"] == round(0.9 * 0.99, 4)
    drifted = ad.fe20_panel_reliability(0.9, 0.99, 3.0)
    assert drifted["reliability"] == round(0.9 * 0.99 / 4.0, 4)
    neg = ad.fe20_panel_reliability(0.9, 0.99, -3.0)
    assert neg["reliability"] == drifted["reliability"]


def test_fe20_missing_named_and_no_discount():
    r = ad.fe20_panel_reliability(0.9, None, 0.5)
    assert r["state"] == "not_recorded"
    assert r["missing"] == ["coverage"]
    d = ad.fe20_discounted(2.0, r)
    assert d["state"] == "not_recorded" and d["value"] is None
    ok = ad.fe20_discounted(2.0, ad.fe20_panel_reliability(1.0, 0.5, 0.0))
    assert ok["value"] == 1.0


def test_fe20_range_refused():
    with pytest.raises(ValueError):
        ad.fe20_panel_reliability(1.2, 0.5, 0.0)


def test_fe20_composition_stability():
    s = ad.fe20_composition_stability({"a", "b", "c"}, {"b", "c", "d"})
    assert s["stability"] == 0.5
    empty = ad.fe20_composition_stability(set(), {"a"})
    assert empty["state"] == "not_recorded"


def test_13f_panel_block_honest_state():
    cur = {str(i): {} for i in range(100)}
    pri = {str(i): {} for i in range(50, 150)}
    block, snapshot = tf.panel_reliability_block(
        cur, pri, "2026-06-30", "2026-03-31")
    assert block["panel_stability"] == round(50 / 150, 4)
    # Coverage basis: current filers over the larger period count.
    assert block["coverage"] == round(100 / max(100, 100), 4)
    # Two periods on record: no drift series, no discount.
    assert block["state"] == "not_recorded"
    assert block["missing"] == ["panel_drift_z"]
    assert snapshot["members_both"] == 50


def test_darkprints_panel_block_honest_state():
    history = [
        {"session": "2026-10-23", "index_used": 501,
         "index_total": 503},
        {"session": "2026-10-26", "index_used": 501,
         "index_total": 503},
        {"session": "2026-10-27", "index_used": 501,
         "index_total": 503},
        {"session": "2026-10-28", "index_used": 499,
         "index_total": 503},
    ]
    block, snapshot = dp.panel_reliability_block(history, 499, 503)
    assert block["coverage"] == round(499 / 503, 4)
    assert block["panel_stability"] is not None
    # Earlier coverages are identical, so a drift z is undefined.
    assert block["panel_drift_z"] is None
    assert block["state"] == "not_recorded"
    assert "zero" in block["panel_drift_state"]
    assert snapshot["session"] == "2026-10-28"


def test_darkprints_panel_block_recorded_when_drift_exists():
    history = [
        {"session": "2026-10-23", "index_used": 400,
         "index_total": 500},
        {"session": "2026-10-24", "index_used": 450,
         "index_total": 500},
        {"session": "2026-10-25", "index_used": 425,
         "index_total": 500},
        {"session": "2026-10-26", "index_used": 440,
         "index_total": 500},
    ]
    block, _snap = dp.panel_reliability_block(history, 440, 500)
    assert block["panel_drift_z"] is not None
    assert block["state"] == "recorded"
    assert 0.0 < block["reliability"] <= 1.0


# ---- FE08: QLIKE graded HAR control ----------------------------

def _prices(tmp_path, closes, start="2026-01-01"):
    from datetime import date, timedelta
    rows = []
    d = date.fromisoformat(start)
    i = 0
    while len(rows) < len(closes):
        if d.weekday() < 5:
            c = closes[i]
            rows.append([d.isoformat(), c, c, c, c, 1000])
            i += 1
        d += timedelta(days=1)
    path = tmp_path / "bars.json"
    path.write_text(json.dumps({"SPY": rows}))
    return G.PriceSource(str(path)), [r[0] for r in rows]


def test_qlike_minimum_and_asymmetry():
    assert G.qlike_loss(0.04, 0.04) == pytest.approx(0.0)
    assert G.qlike_loss(0.01, 0.04) > G.qlike_loss(0.04, 0.04)
    with pytest.raises(G.GradingError):
        G.qlike_loss(0.0, 0.04)


def test_fe08_har_weights_are_the_control():
    v = G.fe08_har_variance(math.log(0.02), math.log(0.03),
                            math.log(0.05))
    expect = math.exp(0.5 * math.log(0.02) + 0.3 * math.log(0.03)
                      + 0.2 * math.log(0.05))
    assert v == pytest.approx(expect)


def test_har_control_report_grades_engine07(tmp_path):
    # Volatile then calm series: the trailing HAR control and the
    # engine median are both reconstructed from the same bars.
    closes = [100.0]
    for i in range(60):
        closes.append(closes[-1] * (1.0 + (0.02 if i % 2 else -0.02)))
    for i in range(10):
        closes.append(closes[-1] * (1.0 + (0.001 if i % 2 else -0.001)))
    prices, dates = _prices(tmp_path, closes)
    base = dates[58]
    row = {"type": "forecast", "engine_id": "engine_07",
           "absence_state": "present",
           "horizon_open": dates[59], "horizon_close": dates[63],
           "value": {"quantiles": {"0.25": 0.05, "0.5": 0.10,
                                   "0.75": 0.15}},
           "outcome": {"symbol": "SPY", "kind": "realised_vol",
                       "base_date": base, "sessions": 5}}
    report = G.har_control_report([row], prices)
    entry = report["engine_07"]
    assert entry["pairs"] == 1
    assert entry["mean_engine_loss"] is not None
    assert entry["mean_baseline_loss"] is not None
    assert entry["state"] == "graded pairs on record"
    assert report["engine_01"]["pairs"] == 0


def test_har_control_report_grades_engine01_band_keys(tmp_path):
    # The live ledger keys Engine 1 quantiles at three decimals
    # ("0.160", "0.840"); the control must read them by value.
    closes = [100.0]
    for i in range(60):
        closes.append(closes[-1] * (1.0 + (0.015 if i % 2 else -0.015)))
    for i in range(10):
        closes.append(closes[-1] * (1.0 + (0.001 if i % 2 else -0.001)))
    prices, dates = _prices(tmp_path, closes)
    base_close = closes[58]
    row = {"type": "forecast", "engine_id": "engine_01",
           "absence_state": "present",
           "horizon_open": dates[59], "horizon_close": dates[63],
           "value": {"quantiles": {"0.160": base_close * 0.98,
                                   "0.840": base_close * 1.02}},
           "outcome": {"symbol": "SPY", "kind": "close",
                       "at_date": dates[63]}}
    report = G.har_control_report([row], prices)
    entry = report["engine_01"]
    assert entry["pairs"] == 1
    assert entry["skipped"] == []
    assert entry["mean_baseline_loss"] is not None


def test_har_control_report_unmatured_counted_not_skipped(tmp_path):
    closes = [100.0 + i * 0.1 for i in range(40)]
    prices, dates = _prices(tmp_path, closes)
    row = {"type": "forecast", "engine_id": "engine_07",
           "absence_state": "present",
           "horizon_open": dates[-1], "horizon_close": "2027-01-01",
           "value": {"quantiles": {"0.5": 0.1}},
           "outcome": {"symbol": "SPY", "kind": "realised_vol",
                       "base_date": dates[-2], "sessions": 5}}
    report = G.har_control_report([row], prices)
    assert report["engine_07"]["pairs"] == 0
    assert report["engine_07"]["unmatured"] == 1
