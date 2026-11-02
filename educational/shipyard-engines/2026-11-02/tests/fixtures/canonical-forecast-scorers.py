"""Transparent first-pass transforms for the 30 forecast hypotheses.

Coefficients are deliberately simple, explicit starting points. They are not fitted
weights and must be estimated only inside a point-in-time training window.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite
from typing import Callable, Mapping


@dataclass(frozen=True)
class Signal:
    value: float
    model_score: float
    drivers: Mapping[str, float]


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _sigmoid(value: float) -> float:
    value = _clip(value, -30.0, 30.0)
    return 1.0 / (1.0 + exp(-value))


def _signed(value: float, **drivers: float) -> Signal:
    value = _clip(value, -8.0, 8.0)
    return Signal(value=value, model_score=value, drivers={k: float(v) for k, v in drivers.items()})


def _risk(logit: float, **drivers: float) -> Signal:
    value = _sigmoid(logit)
    return Signal(value=value, model_score=logit, drivers={k: float(v) for k, v in drivers.items()})


def f_trend(x: Mapping[str, float]) -> Signal:
    agreement = 0.45 * x["ret_21d_z"] + 0.35 * x["ret_63d_z"] + 0.20 * x["ret_252d_z"]
    path_quality = _clip(x["trend_efficiency"], 0.0, 1.0)
    vol_damp = 1.0 / (1.0 + 0.20 * abs(x["vol_regime"]))
    return _signed(agreement * (0.35 + 0.65 * path_quality) * vol_damp,
                   horizon_agreement=agreement, path_quality=path_quality, vol_damp=vol_damp)


def f_mean_reversion(x: Mapping[str, float]) -> Signal:
    chop = _clip((0.58 - x["hurst"]) / 0.25, 0.0, 1.0)
    trend_gate = _clip(1.0 - abs(x["trend_z"]) / 3.0, 0.0, 1.0)
    score = -x["residual_z"] * chop * trend_gate / (1.0 + 0.15 * abs(x["vol_regime"]))
    return _signed(score, chop_gate=chop, trend_gate=trend_gate, residual_z=x["residual_z"])


def f_breakout(x: Mapping[str, float]) -> Signal:
    acceptance = _clip(x["acceptance"], 0.0, 1.0)
    false_break = _clip(x["false_break_rate"], 0.0, 1.0)
    volume_confirm = _clip(1.0 + 0.12 * x["volume_surprise_z"], 0.5, 1.5)
    score = x["break_distance_z"] * acceptance * volume_confirm * (1.0 - false_break)
    return _signed(score, acceptance=acceptance, volume_confirm=volume_confirm, false_break_rate=false_break)


def f_gap(x: Mapping[str, float]) -> Signal:
    residual = x["gap_z"] - x["fair_gap_z"]
    acceptance = _clip(x["open_acceptance"], 0.0, 1.0)
    acceptance_state = 2.0 * acceptance - 1.0
    liquidity = _clip(x["premarket_liquidity"], 0.0, 1.0)
    score = residual * acceptance_state * (0.4 + 0.6 * liquidity)
    return _signed(score, gap_residual_z=residual, open_acceptance=acceptance,
                   acceptance_state=acceptance_state, liquidity=liquidity)


def f_breadth(x: Mapping[str, float]) -> Signal:
    participation = _clip(x["breadth_delta"], -1.0, 1.0)
    score = 0.50 * participation * 3.0 + 0.25 * x["advance_decline_z"] + 0.15 * x["new_high_low_z"] + 0.10 * x["index_trend_z"]
    return _signed(score, breadth_delta=participation, advance_decline_z=x["advance_decline_z"], new_high_low_z=x["new_high_low_z"])


def f_sector(x: Mapping[str, float]) -> Signal:
    breadth = _clip(x["leadership_breadth"], 0.0, 1.0)
    dispersion = _clip(x["sector_dispersion_z"], 0.0, 3.0)
    concentration_penalty = 1.0 / (1.0 + 0.20 * dispersion)
    score = (0.55 * x["sector_momentum_rank_z"] + 0.25 * x["sector_flow_z"] + 0.20 * (2.0 * breadth - 1.0)) * concentration_penalty
    return _signed(score, breadth=breadth, dispersion=dispersion, concentration_penalty=concentration_penalty)


def f_leadlag(x: Mapping[str, float]) -> Signal:
    stability = _clip(x["lag_stability"], 0.0, 1.0)
    r2 = _clip(x["relationship_r2"], 0.0, 1.0)
    score = x["leader_return_z"] * x["lag_beta"] * stability * _clip((r2 - 0.15) / 0.65, 0.0, 1.0)
    return _signed(score, lag_stability=stability, relationship_r2=r2, lag_beta=x["lag_beta"])


def f_har(x: Mapping[str, float]) -> Signal:
    log_forecast = 0.50 * x["log_rv_1"] + 0.30 * x["log_rv_5"] + 0.20 * x["log_rv_22"]
    clipped_forecast = _clip(log_forecast, -40.0, 10.0)
    clipped_baseline = _clip(x["log_rv_baseline"], -40.0, 10.0)
    forecast_variance = exp(clipped_forecast)
    baseline = exp(clipped_baseline)
    ratio_log = clipped_forecast - clipped_baseline
    return Signal(forecast_variance, ratio_log, {"log_variance_ratio": ratio_log, "baseline_variance": baseline})


def f_tail(x: Mapping[str, float]) -> Signal:
    risk = _risk(-0.15 + 0.48 * x["jump_intensity_z"] + 0.36 * abs(x["overnight_gap_z"]) + 0.30 * x["left_tail_asymmetry_z"] + 0.45 * _clip(x["event_density"], 0.0, 1.0),
                 jump_intensity_z=x["jump_intensity_z"], overnight_gap_z=abs(x["overnight_gap_z"]), event_density=x["event_density"])
    return risk


def f_regime(x: Mapping[str, float]) -> Signal:
    logit = -0.40 + 1.10 * _clip(x["change_point_score"], 0.0, 1.0) + 0.30 * abs(x["vol_of_vol_z"]) + 0.25 * abs(x["cross_asset_dispersion_z"]) + 0.30 * abs(x["correlation_shift_z"])
    return _risk(logit, change_point_score=x["change_point_score"], vol_of_vol_z=x["vol_of_vol_z"], correlation_shift_z=x["correlation_shift_z"])


def f_auction(x: Mapping[str, float]) -> Signal:
    reliability = _clip(x["auction_imbalance_reliability"], 0.0, 1.0)
    depth_damp = 1.0 / (1.0 + max(0.0, x["close_depth_z"]) * 0.20)
    score = (x["auction_imbalance_z"] + 0.20 * x["index_rebalance_flow_z"]) * reliability * depth_damp
    return _signed(score, imbalance_reliability=reliability, depth_damp=depth_damp)


def f_liquidity(x: Mapping[str, float]) -> Signal:
    logit = -1.00 + 0.50 * max(0.0, x["spread_z"]) + 0.50 * max(0.0, x["depth_drop_z"]) + 0.35 * max(0.0, x["realized_vol_z"]) + 0.30 * _clip(x["volume_concentration"], 0.0, 1.0)
    return _risk(logit, spread_z=x["spread_z"], depth_drop_z=x["depth_drop_z"], realized_vol_z=x["realized_vol_z"])


def f_ofi(x: Mapping[str, float]) -> Signal:
    quality = _clip(x["trade_condition_quality"], 0.0, 1.0)
    depth = max(0.0, x["depth_z"])
    replenishment = _clip(x["depth_replenishment_ratio"], 0.0, 1.0)
    replenishment_damp = 1.0 - 0.65 * replenishment
    score = ((0.65 * x["ofi_z"] + 0.35 * x["historical_post_fill_drift_z"])
             * quality * replenishment_damp / (1.0 + 0.25 * depth))
    return _signed(score, quality=quality, normalized_depth=depth,
                   replenishment=replenishment, replenishment_damp=replenishment_damp,
                   historical_post_fill_drift_z=x["historical_post_fill_drift_z"])


def f_option_tail(x: Mapping[str, float]) -> Signal:
    surface_quality = _clip(x["surface_quality"], 0.0, 1.0)
    logit = -0.50 + surface_quality * (0.55 * x["put_skew_z"] + 0.35 * x["term_inversion_z"] + 0.35 * x["downside_var_z"])
    return _risk(logit, surface_quality=surface_quality, put_skew_z=x["put_skew_z"], term_inversion_z=x["term_inversion_z"])


def f_gamma(x: Mapping[str, float]) -> Signal:
    quality = _clip(x["gamma_input_quality"], 0.0, 1.0)
    # Positive assumed dealer gamma implies counter-trend delta hedging.
    score = -x["gamma_assumption_z"] * x["spot_move_z"] * (1.0 + 0.20 * abs(x["oi_concentration_z"])) * quality
    return _signed(score, gamma_assumption_z=x["gamma_assumption_z"], spot_move_z=x["spot_move_z"], inferred_input_quality=quality)


def f_options_flow(x: Mapping[str, float]) -> Signal:
    sweep = _clip(x["sweep_quality"], 0.0, 1.0)
    intent = _clip(x["open_close_confidence"], 0.0, 1.0)
    aggressor = _clip(x["aggressor_side_confidence"], 0.0, 1.0)
    quote_quality = _clip(x["quote_condition_quality"], 0.0, 1.0)
    score = x["customer_signed_delta_flow_z"] * sweep * intent * aggressor * quote_quality
    return _signed(score, sweep_quality=sweep, open_close_confidence=intent,
                   aggressor_side_confidence=aggressor, quote_quality=quote_quality)


def f_earnings(x: Mapping[str, float]) -> Signal:
    implied = max(0.0, x["implied_move"])
    historical = max(0.0, x["historical_event_move"])
    dispersion_adjustment = 1.0 + 0.08 * max(-2.0, min(2.0, x["estimate_dispersion_z"]))
    timing = _clip(x["earnings_timing_quality"], 0.0, 1.0)
    value = (0.60 * implied + 0.40 * historical) * dispersion_adjustment * timing
    return Signal(value, dispersion_adjustment - 1.0, {"implied_move": implied, "historical_event_move": historical, "dispersion_adjustment": dispersion_adjustment})


def f_pead(x: Mapping[str, float]) -> Signal:
    persistence = _clip(x["revision_breadth"], 0.0, 1.0)
    score = (0.50 * x["standardized_surprise_z"] + 0.30 * x["post_event_drift_z"] + 0.20 * x["sector_residual_z"]) * (0.5 + 0.5 * persistence)
    return _signed(score, revision_breadth=persistence, surprise_z=x["standardized_surprise_z"])


def f_revision(x: Mapping[str, float]) -> Signal:
    breadth = _clip(x["analyst_breadth"], 0.0, 1.0)
    recency = _clip(x["revision_recency"], 0.0, 1.0)
    dispersion_penalty = 1.0 / (1.0 + 0.20 * abs(x["revision_dispersion_z"]))
    return _signed(x["revision_momentum_z"] * breadth * recency * dispersion_penalty,
                   breadth=breadth, recency=recency, dispersion_penalty=dispersion_penalty)


def f_altdata(x: Mapping[str, float]) -> Signal:
    stability = _clip(x["panel_stability"], 0.0, 1.0)
    coverage = _clip(x["panel_coverage"], 0.0, 1.0)
    reliability = stability * coverage / (1.0 + abs(x["panel_drift_z"]))
    return _signed(x["panel_surprise_z"] * reliability,
                   panel_reliability=reliability, panel_drift_z=x["panel_drift_z"])


def f_xbrl(x: Mapping[str, float]) -> Signal:
    acceleration = 0.35 * x["cash_conversion_z"] + 0.20 * x["fcf_acceleration_z"] + 0.25 * x["deferred_revenue_change_z"] - 0.20 * x["receivables_growth_gap_z"]
    return _signed(acceleration, cash_conversion_z=x["cash_conversion_z"], receivables_growth_gap_z=x["receivables_growth_gap_z"], fcf_acceleration_z=x["fcf_acceleration_z"])


def f_filing_nlp(x: Mapping[str, float]) -> Signal:
    parser = _clip(x["parser_confidence"], 0.0, 1.0)
    novelty = _clip(x["novelty_score"], 0.0, 1.0)
    relevance = _clip(x["section_relevance"], 0.0, 1.0)
    return _signed(x["semantic_delta_z"] * parser * novelty * relevance,
                   parser_confidence=parser, novelty=novelty, relevance=relevance)


def f_insider(x: Mapping[str, float]) -> Signal:
    plan_conf = _clip(x["non_10b5_1_confidence"], 0.0, 1.0)
    recency = _clip(x["insider_recency"], 0.0, 1.0)
    liquidity = 1.0 / (1.0 + max(0.0, x["issuer_illiquidity_z"]) * 0.2)
    return _signed(x["discretionary_net_flow_z"] * plan_conf * recency * liquidity,
                   non_10b5_1_confidence=plan_conf, recency=recency, liquidity_factor=liquidity)


def f_13f(x: Mapping[str, float]) -> Signal:
    staleness = _clip(x["filing_staleness"], 0.0, 1.0)
    crowding = max(0.0, x["ownership_crowding_z"])
    crowding_freshness = 1.0 - staleness
    logit = (-0.25 + 0.40 * crowding * crowding_freshness
             + 0.40 * max(0.0, x["fundamental_deterioration_z"])
             + 0.35 * max(0.0, x["liquidity_stress_z"]))
    return _risk(logit, staleness=staleness, crowding_freshness=crowding_freshness,
                 crowding_z=x["ownership_crowding_z"],
                 fundamental_deterioration_z=x["fundamental_deterioration_z"])


def f_buyback(x: Mapping[str, float]) -> Signal:
    execution = _clip(x["execution_confidence"], 0.0, 1.0)
    blackout = _clip(x["blackout_risk"], 0.0, 1.0)
    liquidity = 1.0 / (1.0 + 0.15 * abs(x["liquidity_anomaly_z"]))
    return _signed(x["buyback_pace_float_z"] * execution * (1.0 - blackout) * liquidity,
                   execution_confidence=execution, blackout_risk=blackout, liquidity_factor=liquidity)


def f_index_flow(x: Mapping[str, float]) -> Signal:
    confidence = _clip(x["flow_model_confidence"], 0.0, 1.0)
    if x["days_to_effective"] < 0.0:
        return _signed(0.0, flow_confidence=confidence, time_weight=0.0,
                       crowding=_clip(x["crowding_z"], 0.0, 4.0), event_passed=1.0)
    days = x["days_to_effective"]
    time_weight = exp(-days / 10.0)
    crowding = _clip(x["crowding_z"], 0.0, 4.0)
    return _signed(x["flow_estimate_z"] * confidence * time_weight / (1.0 + 0.15 * crowding),
                   flow_confidence=confidence, time_weight=time_weight, crowding=crowding, event_passed=0.0)


def f_macro(x: Mapping[str, float]) -> Signal:
    regime = _clip(x["regime_confidence"], 0.0, 1.0)
    surprise = x["release_surprise_z"] - 0.35 * x["market_pricing_z"]
    reaction_sign = _clip(x["cycle_reaction_sign"], -1.0, 1.0)
    return _signed(surprise * reaction_sign * regime,
                   unpriced_surprise=surprise, cycle_reaction_sign=reaction_sign, regime_confidence=regime)


def f_rates_credit(x: Mapping[str, float]) -> Signal:
    transition = _clip(x["macro_transition_score"], 0.0, 1.0)
    curve_signal = _clip((-x["curve_slope_z"] + 0.25 * x["curve_change_z"]), -4.0, 4.0)
    credit_stress = max(0.0, -x["credit_impulse_z"])
    return _risk(-0.70 + 0.55 * curve_signal + 0.60 * credit_stress + 0.65 * transition,
                 curve_signal=curve_signal, credit_stress=credit_stress, transition=transition)


def f_cot(x: Mapping[str, float]) -> Signal:
    supply_shock = _clip(x["supply_shock_score"], 0.0, 1.0)
    crowding_fade = -x["cot_positioning_z"] * _clip(abs(x["cot_positioning_z"]) / 2.0, 0.0, 1.5)
    inventory = -0.60 * x["inventory_deviation_z"] + 0.25 * x["roll_yield_z"]
    return _signed((0.60 * crowding_fade + 0.40 * inventory) * (1.0 - supply_shock),
                   crowding_fade=crowding_fade, inventory_carry=inventory, supply_shock=supply_shock)


def f_crypto(x: Mapping[str, float]) -> Signal:
    funding = abs(x["funding_z"])
    oi = abs(x["open_interest_change_z"])
    depth = max(0.0, x["depth_drop_z"])
    onchain = abs(x["onchain_flow_z"])
    logit = -0.65 + 0.35 * funding + 0.30 * oi + 0.45 * depth + 0.15 * onchain
    return _risk(logit, funding_extreme=funding, open_interest_change=oi, depth_drop=depth, onchain_flow=onchain)


_FORMULAS: dict[str, Callable[[Mapping[str, float]], Signal]] = {
    "trend": f_trend,
    "mean_reversion": f_mean_reversion,
    "breakout": f_breakout,
    "gap": f_gap,
    "breadth": f_breadth,
    "sector": f_sector,
    "leadlag": f_leadlag,
    "har": f_har,
    "tail": f_tail,
    "regime": f_regime,
    "auction": f_auction,
    "liquidity": f_liquidity,
    "ofi": f_ofi,
    "option_tail": f_option_tail,
    "gamma": f_gamma,
    "options_flow": f_options_flow,
    "earnings": f_earnings,
    "pead": f_pead,
    "revision": f_revision,
    "altdata": f_altdata,
    "xbrl": f_xbrl,
    "filing_nlp": f_filing_nlp,
    "insider": f_insider,
    "13f": f_13f,
    "buyback": f_buyback,
    "index_flow": f_index_flow,
    "macro": f_macro,
    "rates_credit": f_rates_credit,
    "cot": f_cot,
    "crypto": f_crypto,
}


def score(formula: str, features: Mapping[str, float]) -> Signal:
    try:
        scorer = _FORMULAS[formula]
    except KeyError as exc:
        raise KeyError(f"no scoring function for {formula}") from exc
    for name, value in features.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"feature {name!r} must be a finite numeric value")
    result = scorer(features)
    if (not isfinite(result.value) or not isfinite(result.model_score)
            or any(not isfinite(value) for value in result.drivers.values())):
        raise ValueError("formula produced non-finite output")
    return result
