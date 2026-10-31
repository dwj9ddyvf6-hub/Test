"""Regression blockers for fix stream A, 2026-10-30: R-09
provenance stamps on the two runners, RC-21 shared label
declaration at issue time, RC-22 attestation sweep, RC-20
Engine 28 voided recount.

Fail directions: on the pre-cure tree, refresh_engines.py and
refresh_tools.py contain no stamp_for_script call; append_forecast
without an explicit identity stores no label_context;
registry.json carries calibration_attestation null on all 30
engines and no site module routes through grading.render_
probability; refresh_gapdestiny.py publishes mine["forecasts"]
(raw, voided rows included) as forecasts_recorded.
"""
import glob
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import grading as G  # noqa: E402
import ledger as L  # noqa: E402
import registry as R  # noqa: E402

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
REG = R.load()
CLOCKS = {c: "2026-10-20T13:00:00Z" for c in L.CLOCK_FIELDS}
LINEAGE = {"source_artifacts": [{"path": "fixture.json",
                                 "sha256": "ab" * 32}],
           "clocks": CLOCKS}


def forecast_kwargs(**over):
    kw = dict(engine_id="engine_01", issued_ts="2026-10-20T13:00:00Z",
              subject="SPY", quantity="close_band_5s",
              value={"lower": 100.0, "upper": 110.0},
              horizon_open="2026-10-21", horizon_close="2026-10-27",
              lineage=LINEAGE, families=["distributional_volatility"],
              outcome={"symbol": "SPY", "kind": "close",
                       "at_date": "2026-10-27"})
    kw.update(over)
    return kw


# ---- R-09: both runners carry the shipyard stamp --------------------

def test_both_runners_wired_to_stamp():
    for name in ("refresh_engines.py", "refresh_tools.py"):
        src = open(os.path.join(SITE, name), encoding="utf-8").read()
        assert "stamp_for_script" in src, name
        assert "import terminal_common as _tc" in src, name


def test_no_refresh_script_unwired():
    # refresh_hub.py was created by a sibling lane at 16:42 UTC on
    # 2026-10-30 (cure D-HUB) and was the one exclusion here until
    # the sweep machinery pass wired it the same day; no refresh
    # script is excluded now.
    unwired = [os.path.basename(p) for p in
               sorted(glob.glob(os.path.join(SITE, "refresh_*.py")))
               if "stamp_for_script" not in
               open(p, encoding="utf-8").read()]
    assert unwired == []


def test_runner_provenance_registered():
    sys.path.insert(0, SITE)
    import terminal_common as tc
    for name in ("refresh_engines.py", "refresh_tools.py",
                 "refresh_hub.py"):
        assert name in tc.PROVENANCE_BY_SCRIPT


# ---- RC-21: shared label declaration at issue time ------------------

def test_new_forecast_without_explicit_identity_is_frozen(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    row, created = led.append_forecast_declared(**forecast_kwargs())
    assert created is True
    assert row["label_context"]["reference_series"] == \
        "the forecast subject's own daily bar series"
    assert row["label_context"]["calendar"] == "NYSE sessions"
    assert row["label_context_fingerprint"] == \
        L.label_context_fingerprint(row["label_context"])
    assert row["label_transform_id"] == "outcome_close_v1"
    assert led.verify_chain() is True


def test_legacy_republication_returns_legacy_row(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    # A pre-cure legacy row (plain append, no identity) republished
    # through the declared path returns the legacy row itself:
    # history is not rewritten and the record does not double.
    legacy, c0 = led.append_forecast(**forecast_kwargs())
    assert c0 is True and "label_context" not in legacy
    again, c1 = led.append_forecast_declared(**forecast_kwargs())
    assert c1 is False and again["row_id"] == legacy["row_id"]
    row, c1 = led.append_forecast_declared(
        **forecast_kwargs(subject="QQQ"))
    row2, c2 = led.append_forecast_declared(
        **forecast_kwargs(subject="QQQ"))
    assert c1 is True and c2 is False and row2["row_id"] == row["row_id"]
    assert len(led.rows()) == 3  # genesis + legacy + one frozen


def test_all_issuing_refreshers_use_declared_path():
    import re
    bad = []
    for path in sorted(glob.glob(os.path.join(SITE, "refresh_*.py"))):
        src = open(path, encoding="utf-8").read()
        for m in re.finditer(r"\b(?:led|ledger|scratch)\.append_forecast\(", src):
            bad.append(os.path.basename(path))
    assert bad == [], f"issuers bypassing the declared path: {bad}"


def test_recompute_shows_frozen_group_beside_legacy(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    row, _ = led.append_forecast_declared(**forecast_kwargs())
    figs = L.recompute_figures(led.rows())
    groups = figs["engine_01"]["by_label_fingerprint"]
    assert L.label_context_fingerprint(row["label_context"]) in groups


def test_same_definition_other_subject_shares_fingerprint(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    a, _ = led.append_forecast_declared(**forecast_kwargs())
    b, _ = led.append_forecast_declared(
        **forecast_kwargs(subject="QQQ",
                          outcome={"symbol": "QQQ", "kind": "close",
                                   "at_date": "2026-10-27"}))
    assert a["label_context_fingerprint"] == \
        b["label_context_fingerprint"]


def test_grade_of_frozen_row_repeats_identity(tmp_path):
    led = L.Ledger(str(tmp_path / "ledger.jsonl"), registry=REG)
    led.append_genesis("test")
    row, _ = led.append_forecast_declared(**forecast_kwargs())
    grade = led.append_grade(
        forecast_row=row, grade={"scores": {"pinball@0.5": 1.0}},
        **L.frozen_label_identity(row))
    assert grade["label_context_fingerprint"] == \
        row["label_context_fingerprint"]


# ---- RC-22: attestation sweep ---------------------------------------

def test_every_engine_registry_attestation_populated():
    for eng in REG.data["engines"]:
        att = eng["calibration_attestation"]
        assert isinstance(att, dict), eng["id"]
        assert att["status"] == "not_attested", eng["id"]
        # recorded_on is the regeneration date, not a pinned
        # snapshot date (cure ATTESTATION-RECOUNT-20261031: the
        # 2026-10-30 pin was the stale snapshot this cure removes;
        # attestations regenerate at every refresh).
        assert att["basis"].strip() and att["recorded_on"] >= "2026-10-31"
        # the gate stays closed: no engine may render probabilities
        assert G.calibration_attestation(eng) is None, eng["id"]
        decision = G.probability_render_decision(eng)
        assert decision["render_as_probability"] is False, eng["id"]


def test_attestation_record_states_graded_counts_honestly():
    rec = G.attestation_record(
        {"id": "engine_x"}, {"forecasts": 10, "graded": 0,
                             "mean_scores": {}}, "2026-10-30")
    assert "no graded forecasts on record yet" in rec["basis"]
    rec = G.attestation_record(
        {"id": "engine_x"}, {"forecasts": 10, "graded": 4,
                             "mean_scores": {"brier": 0.2}}, "2026-10-30")
    assert "4 graded forecasts of 10" in rec["basis"]
    assert "brier" in rec["basis"]


def test_engine_refreshers_route_through_shared_attestation_block():
    import glob as _g
    missing = []
    for path in sorted(_g.glob(os.path.join(SITE, "refresh_*.py"))):
        src = open(path, encoding="utf-8").read()
        if 'ENGINE_ID = ' in src and "attestation_block" not in src:
            missing.append(os.path.basename(path))
    assert missing == [], f"engine refreshers without block: {missing}"
    block = open(os.path.join(SITE, "attestation_block.py"),
                 encoding="utf-8").read()
    assert "render_probability" in block
    assert "probability_render_decision" in block


# ---- RC-20: gap destiny recorded excludes voided --------------------

def test_gapdestiny_recount_excludes_voided():
    src = open(os.path.join(SITE, "refresh_gapdestiny.py"),
               encoding="utf-8").read()
    assert '"forecasts_voided"' in src
    assert '"forecasts_recorded": mine["forecasts"],' not in src


def test_gapdestiny_load_vix_skips_null_closes():
    # The cured VIX capture file carries sessions with no close;
    # the pre-cure loader crashed on float(None).
    src = open(os.path.join(SITE, "refresh_gapdestiny.py"),
               encoding="utf-8").read()
    assert "if c is None:" in src


def test_gapdestiny_main_duplicate_reissues_voided():
    src = open(os.path.join(SITE, "refresh_gapdestiny.py"),
               encoding="utf-8").read()
    assert "Void duplicate main set re-issues" in src
    assert 'and r["row_id"] not in voided_ids\n              and r["lineage"]' in src


def test_gapdestiny_fear_register_matches_extended_gauge():
    # 65 was measured on the 504 close gauge record and confirmed
    # by an independent recount in the cure pass; 22 was the
    # 23 close record's count and can never match again.
    src = open(os.path.join(SITE, "refresh_gapdestiny.py"),
               encoding="utf-8").read()
    assert '"fear_days": 65,' in src
