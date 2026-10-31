"""Regression blockers for the 2026-10-29 adoptions in this item:
the Greeks freshness gate and IV ceiling (DEEP-PASS 3.1 item 3),
FE04's failed gap sign flip in Engine 28 (3.1 item 8), and the
Azrael expected move increment (sqrt time funding curve, wall
classification, regime bands).

Fail direction: every module and function named here is new in
this item (site/options_gate.py did not exist, Engine 28 carried
no sign flip leg, the expected move refresh carried no regime,
walls or funded curve fields), so these tests fail on the
pre-fix tree at import or attribute lookup.
"""

import gzip
import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "site"))
if SITE not in sys.path:
    sys.path.insert(0, SITE)


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


og = _load("options_gate", "options_gate.py")
cc = _load("collect_chains_gate", "collect_chains.py")
hp = _load("refresh_honestpop_gate", "refresh_honestpop.py")
rc = _load("refresh_chain_gate", "refresh_chain.py")
gt = _load("refresh_gammaearningstrap_gate",
           "refresh_gammaearningstrap.py")
gd = _load("refresh_gapdestiny_flip", "refresh_gapdestiny.py")
emr = _load("refresh_expected_move_azrael",
            "refresh_expected_move.py")

NOW = 1_800_000_000  # a fixed epoch; the gate never reads a clock


# ---- the gate itself ---------------------------------------------------
def test_greek_freshness_boundaries():
    assert og.greek_freshness(NOW - 3600, NOW) == "fresh"
    assert og.greek_freshness(NOW - 4500, NOW) == "fresh"
    assert og.greek_freshness(NOW - 4501, NOW) == "stale"
    assert og.greek_freshness(NOW + 5, NOW) == "fresh"
    assert og.greek_freshness(NOW + 6, NOW) == "future"


def test_greek_undated_where_no_timestamp():
    assert og.greek_freshness(None, NOW) == "undated"
    assert og.greek_freshness("not a date", NOW) == "undated"
    v = og.gate_candidate({"greek_ts": None, "iv": 0.2}, NOW)
    assert v["admitted"] and v["greek_state"] == "undated"


def test_iv_ceiling_and_validity():
    assert og.iv_state(4.99) == "ok"
    assert og.iv_state(5.0) == "over_ceiling"
    assert og.iv_state(7.5) == "over_ceiling"
    assert og.iv_state(None) == "absent"
    assert og.iv_state(0) == "invalid"
    assert og.iv_state(float("nan")) == "invalid"
    v = og.gate_candidate({"greek_ts": NOW, "iv": 5.0}, NOW)
    assert not v["admitted"] and "iv_at_or_over_ceiling" in v["reasons"]


def test_stale_greek_refuses_even_with_good_iv():
    v = og.gate_candidate({"greek_ts": NOW - 7200, "iv": 0.2}, NOW)
    assert not v["admitted"] and v["greek_state"] == "stale"


def test_gate_summary_counts_sum():
    s = og.gate_summary(
        [{"greek_ts": NOW - 60, "iv": 0.2},
         {"greek_ts": None, "iv": None},
         {"greek_ts": NOW - 99999, "iv": 0.2},
         {"greek_ts": NOW, "iv": 6.0}], NOW)
    assert s["total"] == 4 and s["admitted"] == 2 and s["refused"] == 2
    assert s["greek_states"]["fresh"] == 2
    assert s["greek_states"]["undated"] == 1
    assert s["greek_states"]["stale"] == 1
    assert s["iv_states"]["over_ceiling"] == 1
    assert s["greek_max_age_seconds"] == 4500 and s["iv_ceiling"] == 5.0


# ---- collector and chain explorer surfaces ------------------------------
def test_collector_snapshot_labels_undated():
    doc = cc.build_snapshot_doc(
        "SPY", "2026-10-29", 700.0, "src",
        ["SPY261030C00700000", "SPY261030P00700000"], "u", "e")
    gate = doc["options_gate"]
    assert gate["greek_states"]["undated"] == 2
    assert gate["iv_states"]["absent"] == 2
    assert gate["admitted"] == 2 and gate["refused"] == 0


def _write_snapshot(tmp_path, symbol, doc):
    d = tmp_path / symbol
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{doc['day']}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return path


def test_chain_explorer_snapshot_gate_undated(tmp_path):
    doc = {"underlying": "SPY", "day": "2026-10-29", "spot": 700.0,
           "captured_at_utc": "2026-10-29T15:00:00+00:00",
           "columns": ["occ", "oi", "volume", "iv"],
           "oi_date": None,
           "rows": [["SPY261030C00700000", None, None, 0.2],
                    ["SPY261030P00700000", None, None, 6.0]]}
    _write_snapshot(tmp_path, "SPY", doc)
    rc.CHAINS_DIR = str(tmp_path)
    snap, err = rc.read_snapshot("SPY", "2026-10-29")
    assert err is None
    gate = snap["options_gate"]
    assert gate["greek_states"]["undated"] == 2
    assert gate["iv_states"]["over_ceiling"] == 1
    assert gate["refused"] == 1


def test_engine11_gate_summary_over_store(tmp_path):
    doc = {"underlying": "SPY", "day": "2026-10-29", "spot": 700.0,
           "captured_at_utc": "2026-10-29T15:00:00+00:00",
           "columns": ["occ", "oi", "volume", "iv"],
           "rows": [["SPY261030C00700000", None, None, None],
                    ["SPY261030P00700000", None, None, None]]}
    _write_snapshot(tmp_path, "SPY", doc)
    gt.CHAINS_DIR = str(tmp_path)
    s = gt.chain_gate_summary()
    assert s["snapshots_scanned"] == 1 and s["total"] == 2
    assert s["greek_states"]["undated"] == 2
    assert s["iv_states"]["absent"] == 2


# ---- Engine 5 surface ----------------------------------------------------
def test_honestpop_over_ceiling_iv_is_skipped_not_used(tmp_path):
    doc = {"underlying": "SPY", "day": "2026-10-29", "spot": 700.0,
           "captured_at_utc": "2026-10-29T15:00:00+00:00",
           "columns": ["occ", "oi", "volume", "iv"],
           "rows": [["SPY261106C00700000", None, None, 0.20],
                    ["SPY261106C00710000", None, None, 6.0],
                    ["SPY261106P00700000", None, None, 0.20]]}
    _write_snapshot(tmp_path, "SPY", doc)
    hp.CHAINS_DIR = str(tmp_path)
    snap, err = hp.read_snapshot("SPY", "2026-10-29")
    assert err is None
    expiry = snap["expiries"]["2026-11-06"]
    assert expiry[700.0] == pytest.approx(0.20)
    assert expiry[710.0] is None  # over ceiling IV never reaches it
    assert snap["options_gate"]["iv_states"]["over_ceiling"] == 1
    assert snap["options_gate"]["greek_states"]["undated"] == 3


def test_honestpop_stale_greek_iv_is_skipped(tmp_path):
    doc = {"underlying": "SPY", "day": "2026-10-29", "spot": 700.0,
           "captured_at_utc": 1800000000,
           "columns": ["occ", "oi", "volume", "iv", "greek_ts"],
           "rows": [["SPY261106C00700000", None, None, 0.20,
                     1800000000 - 7200],
                    ["SPY261106C00710000", None, None, 0.25,
                     1800000000 - 60]]}
    _write_snapshot(tmp_path, "SPY", doc)
    hp.CHAINS_DIR = str(tmp_path)
    snap, err = hp.read_snapshot("SPY", "2026-10-29")
    assert err is None
    expiry = snap["expiries"]["2026-11-06"]
    assert expiry[700.0] is None       # stale Greeks: IV skipped
    assert expiry[710.0] == pytest.approx(0.25)
    assert snap["options_gate"]["greek_states"]["stale"] == 1
    assert snap["options_gate"]["greek_states"]["fresh"] == 1


# ---- Engine 28 FE04 sign flip ---------------------------------------------
def test_acceptance_proxy_direction():
    assert gd.acceptance_proxy(True, 110, 100, 110) == 1.0
    assert gd.acceptance_proxy(True, 110, 100, 100) == 0.0
    assert gd.acceptance_proxy(False, 110, 100, 100) == 1.0
    assert gd.acceptance_proxy(False, 110, 100, 110) == 0.0
    assert gd.acceptance_proxy(True, 100, 100, 100) == 0.5


def test_fe04_sign_flip_is_a_flip_not_a_weakening():
    held = gd.fe04_sign_flip(0.01, 0.9)
    assert held["predicted_close_sign"] == 1
    assert held["claim"] == "gap_accepted_continuation"
    failed = gd.fe04_sign_flip(0.01, 0.1)
    assert failed["predicted_close_sign"] == -1
    assert failed["claim"] == "failed_gap_reversal"
    failed_down = gd.fe04_sign_flip(-0.01, 0.1)
    assert failed_down["predicted_close_sign"] == 1
    neutral = gd.fe04_sign_flip(0.01, 0.5)
    assert neutral["predicted_close_sign"] == 0


def test_sub_claim_has_its_own_quantity():
    assert gd.SUB_QUANTITY != gd.QUANTITY
    assert "sign flip" in gd.SUB_QUANTITY


# ---- Azrael expected move increment ---------------------------------------
def test_azrael_regime_bands():
    assert emr.regime_label(14.99) == "CALM"
    assert emr.regime_label(15.0) == "MIXED"
    assert emr.regime_label(18.5) == "MIXED"
    assert emr.regime_label(18.51) == "FAST"


def test_azrael_sqrt_time_funding_curve():
    assert emr.funded_move(10.0, 0) == 0.0
    assert emr.funded_move(10.0, 390) == pytest.approx(10.0)
    assert emr.funded_move(10.0, 97.5) == pytest.approx(5.0)
    assert emr.funded_move(10.0, 9999) == pytest.approx(10.0)
    curve = emr.funded_curve(700.0, 9.1)
    assert curve[-1]["funded_points"] == pytest.approx(9.1)
    assert curve[-1]["upper"] == pytest.approx(709.1)
    assert curve[0]["funded_points"] == 0.0


def test_azrael_wall_classification():
    assert emr.classify_target(711, 700, 10) == "beyond_upper_wall"
    assert emr.classify_target(710, 700, 10) == "at_upper_wall"
    assert emr.classify_target(707, 700, 10) == "upper_half_inside"
    assert emr.classify_target(702, 700, 10) == "central"
    assert emr.classify_target(693, 700, 10) == "lower_half_inside"
    assert emr.classify_target(690, 700, 10) == "at_lower_wall"
    assert emr.classify_target(689, 700, 10) == "beyond_lower_wall"
    assert emr.classify_target(0, 700, 10) == "no_classification"
    w = emr.walls_for(700.0, 10.0)
    assert w["upper_wall"] == 710.0 and w["lower_half"] == 695.0
