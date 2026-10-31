"""Regression blockers for DEEP-PASS 3.2 item 2: the Aperture
per name historical proof gate, hardened.

Covered: the frozen episode rule in the registry (per engine,
validated, provisional language only, BH over the scanned
universe), episode extraction (non overlapping, friction,
chronological split), the raw proof states, the BH downgrade
refusing SUPPORTED across a universe, the provisional display
language on the gate and on the scanner policy surface, and
the forward ledger record graded against what the name
actually did.

Fail direction: pre-cure there is no proof_gate module, no
proof_gate_rule in the registry and no proof display in the
scanner policy, so this file fails at import and at the
registry assertions.
"""
import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "site"))
import proof_gate as PG  # noqa: E402
import registry as R  # noqa: E402
from ledger import Ledger  # noqa: E402
import aperture_policy as AP  # noqa: E402


def _rule():
    return R.Registry().proof_gate_rule("engine_19")


def _cycle_series(cycles=14):
    """A repeating dip then rise pattern: the frozen entry
    condition fires once per cycle and the 10 session forward
    return is positive every time (proven in the build pass:
    12 episodes, every net return about +1.1 percent)."""
    closes, price = [], 100.0
    pattern = [-0.01, -0.012, -0.01, -0.008, -0.005, 0.004,
               0.012, 0.015, 0.015, 0.012, 0.01, 0.008]
    for _ in range(cycles):
        for r in pattern:
            price *= (1 + r)
            closes.append(round(price, 4))
    return closes


# ---- the frozen rule ------------------------------------------------

def test_rule_frozen_identical_for_engines_19_and_20():
    reg = R.Registry()
    r19, r20 = reg.proof_gate_rule("engine_19"), reg.proof_gate_rule("engine_20")
    assert r19 == r20
    assert r19["id"] == "aperture_episode_rule_v1"
    assert r19["state_language"] == "provisional"
    assert r19["episode"]["friction"] == 0.0035
    assert r19["episode"]["forward_sessions"] == 10
    assert r19["multiple_testing"]["method"] == "benjamini_hochberg"
    assert r19["multiple_testing"]["scope"] == "scanned_universe"
    assert r19["forward_check"]["ledger_engine_id"] == "engine_19"


def test_registry_refuses_non_provisional_or_uncorrected_rule(tmp_path):
    data = copy.deepcopy(R.Registry().data)
    for eng in data["engines"]:
        if eng["id"] == "engine_19":
            eng["proof_gate_rule"]["state_language"] = "proven"
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(data))
    with pytest.raises(R.RegistryError):
        R.Registry(str(path))
    data = copy.deepcopy(R.Registry().data)
    for eng in data["engines"]:
        if eng["id"] == "engine_20":
            eng["proof_gate_rule"]["multiple_testing"]["method"] = "none"
    path.write_text(json.dumps(data))
    with pytest.raises(R.RegistryError):
        R.Registry(str(path))


# ---- episodes and raw states -----------------------------------------

def test_episodes_non_overlapping_and_friction_applied():
    rule = _rule()
    closes = _cycle_series()
    starts = PG.find_episodes(closes, rule)
    assert len(starts) >= 10
    for a, b in zip(starts, starts[1:]):
        assert b - a >= 10
    rets = PG.episode_returns(closes, starts, rule)
    raw = [closes[s + 10] / closes[s] - 1.0 for s in starts]
    for net, gross in zip(rets, raw):
        assert abs(net - (gross - 0.0035)) < 1e-12


def test_strong_name_raw_supported_and_provisional():
    res = PG.compute_name_proof("TEST", _cycle_series(), _rule())
    assert res["proof_state"] == "SUPPORTED"
    assert res["provisional"] is True
    assert res["display_state"] == "PROVISIONAL SUPPORTED"
    assert res["train"]["episodes"] + res["holdout"]["episodes"] \
        == res["episodes"]
    # chronological split: train is the larger, earlier part
    assert res["train"]["episodes"] > res["holdout"]["episodes"]


def test_flat_name_observing_never_filled_in():
    res = PG.compute_name_proof("FLAT", [100.0] * 200, _rule())
    assert res["proof_state"] == "OBSERVING"
    assert res["episodes"] == 0
    assert res["display_state"] == "PROVISIONAL OBSERVING"


def test_binomial_one_sided_p():
    assert PG.binomial_one_sided_p(0, 0) == 1.0
    assert abs(PG.binomial_one_sided_p(12, 12) - 0.5 ** 12) < 1e-12
    assert PG.binomial_one_sided_p(6, 12) > 0.5


# ---- BH across the universe ------------------------------------------

def test_bh_keeps_genuinely_strong_name_supported():
    universe = {"STRONG": _cycle_series()}
    for i in range(40):
        universe[f"FLAT{i}"] = [100.0] * 200
    results = PG.compute_proof_universe(universe, _rule())
    assert results["STRONG"]["proof_state"] == "SUPPORTED"
    assert results["STRONG"]["bh_q_value"] <= 0.05
    assert results["STRONG"]["bh_applied"] is True


def test_bh_downgrades_chance_passes_across_universe(monkeypatch):
    """Five names in a 100 name scan pass raw thresholds with
    a marginal p-value: individually plausible, collectively
    exactly the chance passes a universe scan manufactures.
    BH must refuse every one of those SUPPORTED prints."""
    rule = _rule()

    def fake(symbol, closes, _rule):
        marginal = int(symbol[1:]) < 5
        return {"symbol": symbol, "rule_id": rule["id"],
                "provisional": True,
                "proof_state": "SUPPORTED" if marginal else "OBSERVING",
                "display_state": "PROVISIONAL SUPPORTED" if marginal
                    else "PROVISIONAL OBSERVING",
                "episodes": 12, "hits": 9, "episode_starts": [],
                "train": {"episodes": 8, "hit_rate": 0.75, "median": 0.02},
                "holdout": {"episodes": 4, "hit_rate": 0.75, "median": 0.02},
                "p_value": 0.04 if marginal else 0.9,
                "bh_q_value": None,
                "bh_significant": False, "bh_applied": False,
                "downgrade_reason": None}

    monkeypatch.setattr(PG, "compute_name_proof", fake)
    universe = {f"N{i}": [100.0] * 50 for i in range(100)}
    results = PG.compute_proof_universe(universe, rule)
    marginal = [r for s, r in sorted(results.items()) if int(s[1:]) < 5]
    assert all(r["proof_state"] == "MIXED" for r in marginal)
    assert all(r["downgrade_reason"] for r in marginal)
    assert all(r["display_state"] == "PROVISIONAL MIXED" for r in marginal)
    assert all(r["bh_q_value"] > 0.05 for r in marginal)


# ---- forward ledger record -------------------------------------------

def _lineage():
    clocks = {c: "2026-10-29" for c in (
        "event_time", "publication_time", "first_available_time",
        "ingestion_time", "decision_as_of")}
    return {"clocks": clocks, "source_artifacts": [
        {"path": "test", "sha256": "0" * 64}]}


def test_forward_record_ledgers_and_grades_against_reality(tmp_path):
    rule = _rule()
    reg = R.Registry()
    led = Ledger(str(tmp_path / "ledger.jsonl"), registry=reg)
    led.append_genesis("proof gate test")
    results = PG.compute_proof_universe(
        {"STRONG": _cycle_series(), "FLAT": [100.0] * 200}, rule)
    created, dup = PG.record_forward_records(
        led, results=results, issued_ts="2026-10-29",
        horizon_open="2026-10-29", horizon_close="2026-11-12",
        lineage=_lineage(), rule=rule)
    assert (created, dup) == (2, 0)
    created2, dup2 = PG.record_forward_records(
        led, results=results, issued_ts="2026-10-29",
        horizon_open="2026-10-29", horizon_close="2026-11-12",
        lineage=_lineage(), rule=rule)
    assert (created2, dup2) == (0, 2)  # dedupe: republication writes nothing
    rows = [r for r in led.rows() if r.get("type") == "forecast"
            and r.get("quantity") == PG.FORWARD_QUANTITY]
    assert {r["subject"] for r in rows} == {"STRONG", "FLAT"}
    strong = next(r for r in rows if r["subject"] == "STRONG")
    assert strong["engine_id"] == "engine_19"
    assert strong["value"]["provisional"] is True
    assert strong["value"]["proof_state"] == "SUPPORTED"
    # Grade it against what the name actually did next.
    grade = PG.grade_forward_record(led, strong, 0.021)
    assert grade["grade"]["scores"]["forward_hit"] == 1.0
    assert grade["grade"]["proof_state_at_issue"] == "SUPPORTED"
    assert led.verify_chain()


def test_forward_return_none_until_horizon_trades():
    rule = _rule()
    closes = [100.0] * 20
    assert PG.forward_return(closes, 15, rule) is None
    closes = [100.0] * 10 + [110.0] * 10
    assert abs(PG.forward_return(closes, 0, rule)
               - (0.10 - 0.0035)) < 1e-9


# ---- the streaming panel loader ---------------------------------------

def test_panel_loader_slices_symbols_without_loading_rows(tmp_path):
    import refresh_proofgate as RPG
    panel = {"A": [["2026-01-01", 1, 1, 1, 10.0, 5],
                   ["2026-01-02", 1, 1, 1, 11.0, 5]],
             "AA": [["2026-01-01", 1, 1, 1, 20.0, 5]]}
    path = tmp_path / "panel.json"
    # The real panel's separators are not uniform: the first
    # symbol boundary is `]],"AA":` with no space, later ones
    # carry a space. The loader must survive both forms.
    path.write_text(json.dumps(panel).replace(']], "AA"', ']],"AA"'))
    closes, freshest = RPG.load_panel_closes(str(path))
    assert closes == {"A": [10.0, 11.0], "AA": [20.0]}
    assert freshest == "2026-01-02"
    path.write_text(json.dumps(panel))
    closes, freshest = RPG.load_panel_closes(str(path))
    assert closes == {"A": [10.0, 11.0], "AA": [20.0]}


# ---- scanner surface display ------------------------------------------

def test_scanner_policy_displays_proof_as_provisional():
    cand = {"symbol": "XYZ", "provider_eligible": True,
            "daily_bar_count": 100, "intraday_bar_count": 5,
            "series_valid": True,
            "last_intraday_bar_matches_expected": True,
            "proof_state": "SUPPORTED", "proof_bh_q_value": 0.01,
            "proof_episodes": 12,
            "price": 10.0, "support": 9.8, "atr": 0.5,
            "resistance": 12.0, "median_dollar_volume": 9_000_000,
            "session": "regular",
            "trigger": {"family": "sweep_reclaim",
                        "state": "CONFIRMED", "age_bars": 0}}
    out = AP.classify_candidate(cand, current_bar=10)
    assert out["proof"]["display"] == "PROVISIONAL SUPPORTED"
    assert out["proof"]["provisional"] is True
    assert "SUPPORTED" != out["proof"]["display"]
