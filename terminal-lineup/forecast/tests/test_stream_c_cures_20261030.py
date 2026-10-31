"""Regression blockers for fix stream C, 2026-10-30.

Covers RC-25 (pullback study), RC-13 (replication wire
untestable verdicts), RC-09 (FE04 news leg evidence), RC-23
(13F readings and FE12 guard inputs) and RC-30 (FE07, FE21,
FE19 routes, FE06 waiting state). Each test fails on the
pre-cure tree: the study record and the published state did
not exist, the wire counted not_yet 6 with no untestable
verdict, the fair gap record carried no news evidence and its
reader could not see the news store's shape, the guard stood
not_recorded with all four inputs missing, the 13F block
carried no panel readings, and the registry routes stood
absent.
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(LINEUP, "site")
sys.path.insert(0, os.path.join(LINEUP, "forecast"))

import leadlag  # noqa: E402


def load(rel):
    with open(os.path.join(SITE, rel), encoding="utf-8") as fh:
        return json.load(fh)


# ---- RC-30 FE07 estimation ------------------------------------

def test_leadlag_soft_threshold_zeroes_weak_edges():
    assert leadlag.soft_threshold(0.004) == 0.0
    assert leadlag.soft_threshold(0.005) == 0.0
    assert leadlag.soft_threshold(0.03) == 1.0
    assert leadlag.soft_threshold(None) == 0.0


def test_leadlag_estimate_edge_finds_a_real_lag():
    # follower return = 0.8 * leader's prior return + small noise
    import random
    from datetime import date, timedelta
    rng = random.Random(7)
    leader = {}
    follower = {}
    prev = 0.0
    day = date(2023, 1, 2)
    for i in range(600):
        d = (day + timedelta(days=i)).isoformat()
        cur = rng.gauss(0, 0.01)
        leader[d] = cur
        follower[d] = 0.8 * prev + rng.gauss(0, 0.002)
        prev = cur
    est = leadlag.estimate_edge(leader, follower)
    assert est is not None
    assert est["lag_beta"] > 0.5
    assert est["selected"] is True
    assert est["aligned_sessions"] >= leadlag.MIN_ALIGNED


def test_leadlag_estimate_edge_too_short_is_none():
    assert leadlag.estimate_edge({"a": 0.01}, {"a": 0.01}) is None


def test_registry_routes_cured():
    with open(os.path.join(LINEUP, "forecast", "registry.json"),
              encoding="utf-8") as fh:
        reg = json.load(fh)
    qs = {q["id"]: q for q in reg["research_questions"]}
    fe07 = {r["name"]: r["status"] for r in qs["fe07"]["data_routes"]}
    assert any(s == "existing" and "pair selection" in n
               for n, s in fe07.items())
    assert qs["fe07"]["estimation_frozen"]["pairs_selected"] > 0
    fe21 = {r["name"]: r["status"] for r in qs["fe21"]["data_routes"]}
    assert any(s == "partial" and "XBRL" in n
               for n, s in fe21.items())
    assert "accession" in qs["fe21"]["route_evidence"]["missing"]
    fe19 = {r["name"]: r["status"] for r in qs["fe19"]["data_routes"]}
    assert any(s == "partial" and "vintages" in n
               for n, s in fe19.items())
    assert "waiting_on" in qs["fe06_sector_diffusion"]
    assert "335" in qs["fe06_sector_diffusion"]["waiting_on"]


def test_leadlag_record_frozen_pairs():
    rec = load("leadlag-record.json")
    assert rec["pairs_estimated"] == 600
    assert rec["pairs_selected"] > 0
    assert rec["proxies_missing_from_panel"] == []
    for p in rec["selected_pairs"]:
        assert p["edge"] != 0.0
        assert p["aligned_sessions"] >= leadlag.MIN_ALIGNED


def test_xbrl_route_record():
    rec = load(os.path.join("filings-wire", "xbrl_record.json"))
    assert rec["filers"] == 43
    assert rec["facts_with_filed_date"] > 40000
    # Updated 2026-10-30 by sweep stream 4: acceptance
    # timestamps landed at filing level from the submissions
    # fetch, superseding the partial state pinned here.
    assert rec["acceptance_timestamps"]["state"] == \
        "recorded_at_filing_level"
    assert rec["acceptance_timestamps"][
        "filers_with_acceptance"] == 43
    assert "accession" in rec["acceptance_timestamps"]["missing"]
    assert rec["restatement_handling"]["restated_concept_periods"] > 0


# ---- RC-09 FE04 news leg --------------------------------------

def test_fair_gap_news_evidence():
    rec = load(os.path.join("gap-destiny", "fair_gap_record.json"))
    ev = rec["news_leg_evidence"]
    assert ev["state"] == "not_estimable_on_records_on_hand"
    assert ev["signed_direction_field_present"] is False
    assert "sentiment" not in ev["news_store_fields"]
    assert rec["counts"]["news_leg"] == 0
    assert rec["counts"]["full_residual"] == 0
    assert rec["counts"]["news_on_record"] == \
        ev["gap_names_with_overnight_news"] > 0
    assert len(ev["missing_inputs"]) == 2


def test_earnings_page_publishes_news_evidence():
    data = load(os.path.join("earnings-distribution", "data.json"))
    block = data["fe04_fair_gap_remainder"]
    assert block["news_leg_evidence"]["state"] == \
        "not_estimable_on_records_on_hand"
    assert block["counts"]["news_on_record"] > 0


# ---- RC-13 replication wire -----------------------------------

def test_wire_untestable_verdicts():
    wire = load(os.path.join("replication-wire", "data.json"))
    assert wire["counts"]["not_yet"] == 0
    assert wire["counts"]["untestable"] == 6
    untestable = [c for c in wire["claims"]
                  if c["verdict"] == "untestable"]
    assert len(untestable) == 6
    for c in untestable:
        assert c["verdict_words"] == \
            "Cannot be tested on the records on hand"
        assert "missing record" in c["result"].lower()


def test_graveyard_recounts_untestable():
    grave = load(os.path.join("graveyard", "data.json"))
    wire = load(os.path.join("replication-wire", "data.json"))
    assert grave["counts"]["untestable"] == 6
    assert grave["counts"]["not_yet"] == 0
    assert grave["counts"]["buried"] == wire["counts"]["did_not"]
    assert len(grave["not_buried"]["untestable"]) == 6


# ---- RC-23 residuals ------------------------------------------

def test_session_quality_record():
    rec = load(os.path.join("corrected-band",
                            "session_quality_record.json"))
    assert rec["sessions_on_record"] >= 60
    inputs = rec["freshest_inputs"]
    assert 0.0 <= inputs["volume_concentration"] <= 1.0
    assert inputs["realised_vol_z"] is not None
    assert inputs["spread_z"] is None
    # Updated 2026-10-30 by sweep stream 4: the absent text now
    # names the live quote capture accrual instead of the old
    # no store statement, which the capture record superseded.
    assert "live quote" in rec["absent_inputs"]["spread_z"]
    assert "live quote" in rec["absent_inputs"]["depth_drop_z"]
    assert rec["live_quote_capture"]["sessions_on_record"] >= 1


def test_corrected_band_guard_partial_and_counts():
    data = load(os.path.join("corrected-band", "data.json"))
    guard = data["live"]["session_quality_guard"]
    assert guard["state"] == "partial"
    assert guard["inputs_used"] == ["realised_vol_z",
                                    "volume_concentration"]
    assert guard["missing"] == ["spread_z", "depth_drop_z"]
    assert guard["band_widen_factor"] > 1.0
    live = data["live"]
    assert live["forecasts_recorded"] == 6 * live["issue_days"]
    assert live["forecasts_recorded"] + \
        live["superseded_duplicate_rows"] == \
        live["ledger_rows_total"]


def test_13f_panel_readings_recorded():
    data = load(os.path.join("13f-tracker", "data.json"))
    block = data["panel_reliability"]
    assert len(block["panel_readings"]) == 2
    assert block["panel_drift_state"].startswith("undefined")
    assert "third full filing period" in block["missing_input"]
    assert block["panel_drift_z"] is None


# ---- RC-25 pullback study -------------------------------------

def test_pullback_study_record_and_page():
    study = load(os.path.join("pullback-norm", "study_record.json"))
    assert study["events"] > 0
    assert study["engine_24_depth_leg"]["state"] == "recorded"
    assert study["engine_24_depth_leg"]["cohort_events"] > 0
    assert study["engine_29_depth_leg"]["state"] == "recorded"
    assert study["engine_29_depth_leg"]["cohort_events"] > 0
    page = load(os.path.join("pullback-norm", "data.json"))
    assert page["state"] == "published"
    assert page["events"] == study["events"]
    assert page["distribution"]["state"] == "counted"
    assert page["recovery"]["state"] == "counted"


def test_engine_pages_carry_depth_legs():
    e24 = load(os.path.join("fear-day-triangulation", "data.json"))
    assert e24["depth_leg_deep_panel"]["state"] == "recorded"
    e29 = load(os.path.join("completion-clock", "data.json"))
    assert e29["depth_cohort_timing_deep_panel"]["state"] == \
        "recorded"


def test_no_em_dash_in_new_modules():
    for rel in ("pullback_study.py", "build_session_quality.py",
                "build_leadlag_record.py", "build_xbrl_route.py",
                "fair_gap_model.py"):
        with open(os.path.join(SITE, rel), encoding="utf-8") as fh:
            assert "—" not in fh.read(), rel
    with open(os.path.join(LINEUP, "forecast", "leadlag.py"),
              encoding="utf-8") as fh:
        assert "—" not in fh.read()
