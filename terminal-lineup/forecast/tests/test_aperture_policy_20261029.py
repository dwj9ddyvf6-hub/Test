"""APERTURE-POLICY-20261029 blockers: DEEP-PASS 3.2 item 1.

Aperture policy architecture rebuilt on our candidate surfaces:
ordinal deterministic stages (data integrity stop, proof gate,
hard vetoes, trigger lifecycle, tier qualification; no blended
score), fail closed operational defaults (shadow only when
omitted, explicit ORDER_AUTHORIZED authority for anything
stronger), out of hours verdict degradation, and the structure
bounded target rule. Two fixes his version needs: per name
exclusion reasons ledgered (never a silent drop), and trigger
freshness computed from trigger age against registry TTLs
(3, 4 and 6 bars), never from a window flag.

Fail direction: site/aperture_policy.py does not exist on the
pre-cure tree, so every test fails pre-cure at import.
"""
import importlib.util
import os
import sys

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "site")
_spec = importlib.util.spec_from_file_location(
    "aperture_policy", os.path.join(SITE, "aperture_policy.py"))
ap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ap)


def good(**over):
    cand = {
        "symbol": "AAA", "price": 100.0, "support": 99.0,
        "atr": 2.0, "resistance": 110.0,
        "daily_bar_count": 120, "intraday_bar_count": 10,
        "median_dollar_volume": 20_000_000,
        "session": "regular",
        "trigger": {"family": "sweep_reclaim", "state": "CONFIRMED",
                    "fired_bar": 10},
    }
    cand.update(over)
    return cand


def test_structure_bounded_target_uses_overhead_resistance():
    # price + 3.2 ATR = 106.4, resistance 104 is lower: target is
    # bounded by structure, never manufactured from a multiple.
    assert ap.structure_bounded_target(100.0, 104.0, 2.0) == 104.0
    assert ap.structure_bounded_target(100.0, 120.0, 2.0) == 106.4


def test_trigger_freshness_uses_age_against_registry_ttl():
    trig = {"family": "sweep_reclaim", "state": "CONFIRMED",
            "fired_bar": 10}
    assert ap.trigger_freshness(trig, current_bar=13)["state"] == "fresh"
    assert ap.trigger_freshness(trig, current_bar=14)["state"] == "expired"
    hold = {"family": "structural_hold", "state": "CONFIRMED",
            "fired_bar": 10}
    assert ap.trigger_freshness(hold, current_bar=14)["state"] == "fresh"
    assert ap.trigger_freshness(hold, current_bar=15)["state"] == "expired"
    rot = {"family": "rotation_ignition", "state": "CONFIRMED",
           "fired_bar": 10}
    assert ap.trigger_freshness(rot, current_bar=16)["state"] == "fresh"
    assert ap.trigger_freshness(rot, current_bar=17)["state"] == "expired"


def test_trigger_freshness_ignores_window_flag():
    # His defect: a window flag made any in window trigger fresh.
    trig = {"family": "sweep_reclaim", "state": "CONFIRMED",
            "fired_bar": 1, "in_window": True}
    out = ap.trigger_freshness(trig, current_bar=50)
    assert out["state"] == "expired" and out["age_bars"] == 49
    no_age = {"family": "sweep_reclaim", "state": "CONFIRMED",
              "in_window": True}
    assert ap.trigger_freshness(no_age, current_bar=50)["state"] == "unknown"


def test_good_candidate_qualifies_s_tier_with_no_blended_score():
    out = ap.classify_candidate(good(), current_bar=11)
    assert out["tier"] == "S" and out["verdict"] == "BUY_NOW"
    assert out["stage"] == "tier_qualification"
    assert "score" not in out
    assert out["geometry"]["target"] == 106.4
    assert out["geometry"]["reward_to_risk"] >= 2.0


def test_shadow_only_is_the_default_when_omitted():
    out = ap.classify_candidate(good(), current_bar=11)
    assert out["shadow_only"] is True
    assert out["execution_eligible"] is False


def test_execution_requires_explicit_authority():
    cand = good(shadow_only=False)
    out = ap.classify_candidate(cand, current_bar=11)
    assert out["shadow_only"] is True  # forced back: no authority
    assert out["execution_eligible"] is False
    cand2 = good(shadow_only=False, authority="ORDER_AUTHORIZED")
    out2 = ap.classify_candidate(cand2, current_bar=11)
    assert out2["shadow_only"] is False
    assert out2["execution_eligible"] is True


def test_out_of_hours_degrades_verdict():
    out = ap.classify_candidate(good(session="premarket"),
                                current_bar=11)
    assert out["tier"] == "S"           # qualification is unchanged
    assert out["display_tier"] == "A"   # S displays as A out of hours
    assert out["verdict"] == "WAIT"     # BUY NOW degrades to WAIT
    assert out["owner_action"] == "NO_VIEW"
    assert out["degraded"] is True


def test_data_integrity_stop_wins_first_and_is_ledgered():
    cand = good(daily_bar_count=10, quality_flags=["stale_feed"],
                price=0.5)
    out = ap.classify_candidate(cand, current_bar=11)
    assert out["stage"] == "exclusion"
    assert out["tier"] == "NO_VIEW" and out["verdict"] == "NO_VIEW"
    assert "insufficient_daily_bars" in out["reasons"]
    assert "quality_flag:stale_feed" in out["reasons"]


def test_hard_veto_beats_tier_qualification():
    out = ap.classify_candidate(good(price=0.5), current_bar=11)
    assert out["stage"] == "hard_veto" and out["tier"] == "AVOID"
    assert "price_below_one_dollar" in out["reasons"]
    low_rr = ap.classify_candidate(
        good(resistance=100.5), current_bar=11)
    assert low_rr["tier"] == "AVOID"
    assert "reward_to_risk_below_1_25" in low_rr["reasons"]


def test_expired_trigger_is_a_hard_veto_not_fresh():
    out = ap.classify_candidate(good(), current_bar=99)
    assert out["tier"] == "AVOID"
    assert "trigger_expired" in out["reasons"]


def test_unconfirmed_trigger_stays_forming():
    cand = good(trigger={"family": "sweep_reclaim",
                         "state": "APPROACH", "fired_bar": 10})
    out = ap.classify_candidate(cand, current_bar=11)
    assert out["tier"] == "FORMING" and out["verdict"] == "WAIT"
    assert out["stage"] == "lifecycle"


def test_classify_candidates_never_drops_a_name():
    cands = [good(), good(symbol="BBB", daily_bar_count=3),
             good(symbol="CCC", provider_eligible=False)]
    out = ap.classify_candidates(cands, current_bar=11)
    assert out["counts"]["total"] == 3
    assert len(out["decisions"]) == 3
    assert len(out["exclusions"]) == 2
    by_symbol = {e["symbol"]: e for e in out["exclusions"]}
    assert "insufficient_daily_bars" in by_symbol["BBB"]["reasons"]
    assert "provider_ineligible" in by_symbol["CCC"]["reasons"]
    total = sum(out["counts"]["by_tier"].values())
    assert total == 3


def test_exclusion_record_shape():
    rec = ap.exclusion_record("ZZZ", ["no_bar_on_session",
                                      "no_bar_on_session"])
    assert rec["symbol"] == "ZZZ"
    assert rec["reasons"] == ["no_bar_on_session"]
    assert rec["tier"] == "NO_VIEW"
    assert rec["execution_eligible"] is False
