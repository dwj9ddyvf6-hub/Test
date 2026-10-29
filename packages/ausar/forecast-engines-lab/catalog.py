"""Forecast catalog. Parameters are starter hypotheses, not fitted estimates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InputRequirement:
    name: str
    unit: str
    max_age_seconds: int
    min_quality: float = 0.2
    value_range: tuple[float, float] | None = None


@dataclass(frozen=True)
class EngineSpec:
    engine_id: str
    name: str
    family: str
    target: str
    target_unit: str
    horizon: str
    forecast_unit: str
    score_kind: str
    score_semantics: str
    maturity: str
    formula: str
    inputs: tuple[InputRequirement, ...]
    assumptions: tuple[str, ...]
    kill_conditions: tuple[str, ...]
    rea_trace: str


def _i(name: str, unit: str = "z", age: int = 172800, quality: float = 0.2) -> InputRequirement:
    value_range = (0.0, 1.0) if unit == "ratio" else (-1.0, 1.0) if unit == "signed_ratio" else None
    return InputRequirement(name, unit, age, quality, value_range)


_raw = [
    ("trend_persistence", "Multi-horizon trend persistence", "Price/technical", "forward excess return", "5-20 sessions", "signed_score", "CORE-RESEARCH", "trend", [_i("ret_21d_z"), _i("ret_63d_z"), _i("ret_252d_z"), _i("trend_efficiency", "ratio"), _i("vol_regime", "z")], "Combine non-overlapping horizons; attenuate noisy paths.", "Signal disagreement, corporate-action/data break, or volatility shock."),
    ("regime_mean_reversion", "Regime-gated residual reversion", "Price/technical", "residual return", "1-5 sessions", "signed_score", "CORE-RESEARCH", "mean_reversion", [_i("residual_z"), _i("hurst", "ratio"), _i("trend_z"), _i("vol_regime", "z")], "Fade only when supplied Hurst and trend features indicate a range.", "Hurst/trend gate invalidates; residual exceeds the historical support window."),
    ("breakout_acceptance", "Breakout acceptance and survival", "Price/technical", "breakout continuation", "1-5 sessions", "signed_score", "CORE-RESEARCH", "breakout", [_i("break_distance_z"), _i("acceptance", "ratio"), _i("volume_surprise_z"), _i("false_break_rate", "ratio")], "Break level is defined from data available before the forecast cutoff.", "No executable liquidity, unconfirmed bar, or high false-break rate."),
    ("gap_decomposition", "Overnight gap decomposition", "Price/events", "gap continuation vs fade", "intraday-2 sessions", "signed_score", "CONDITIONAL-DATA", "gap", [_i("gap_z"), _i("fair_gap_z"), _i("open_acceptance", "ratio"), _i("premarket_liquidity", "ratio", 21600)], "Fair-gap estimate uses only information published by as_of. open_acceptance is bounded [0, 1]: 0 means rejected, 0.5 indeterminate, and 1 accepted; the score fades rejected residual gaps and follows accepted ones.", "News revision, halt, or unresolved daily-open/kicking-open trigger."),
    ("breadth_impulse", "Breadth participation impulse", "Breadth/rotation", "index/market direction", "1-5 sessions", "signed_score", "CORE-RESEARCH", "breadth", [_i("breadth_delta", "signed_ratio"), _i("advance_decline_z"), _i("new_high_low_z"), _i("index_trend_z")], "Constituent set and breadth timestamps are point-in-time; breadth_delta is bounded [-1, 1], and positive breadth_delta and advance-decline/new-high-low z-scores mean broader positive participation.", "Constituent coverage falls below its declared threshold."),
    ("sector_diffusion", "Sector leadership diffusion", "Breadth/rotation", "relative sector return", "5-20 sessions", "signed_score", "CORE-RESEARCH", "sector", [_i("sector_momentum_rank_z"), _i("leadership_breadth", "ratio"), _i("sector_dispersion_z"), _i("sector_flow_z")], "Sector ranks use contemporaneous membership and neutralization.", "Membership/survivorship uncertainty or sector dispersion regime break."),
    ("lead_lag_graph", "Cross-asset lead-lag graph", "Cross-asset", "follower residual return", "intraday-5 sessions", "signed_score", "EXPERIMENTAL", "leadlag", [_i("leader_return_z"), _i("lag_beta", "beta"), _i("lag_stability", "ratio"), _i("relationship_r2", "ratio")], "Graph edges must be trained only on prior windows and revalidated; lag_beta is a signed, unbounded regression coefficient.", "Rolling fit deterioration, clock mismatch, or relationship sign flip."),
    ("har_volatility", "HAR-style realized-volatility forecast", "Volatility", "realized variance", "1-5 sessions", "variance", "CORE-RESEARCH", "har", [_i("log_rv_1", "log_variance"), _i("log_rv_5", "log_variance"), _i("log_rv_22", "log_variance"), _i("log_rv_baseline", "log_variance")], "Forecast variance, not direction; variance inputs share a consistent sampling scheme.", "Bad print, stale bar window, or sampling-definition change."),
    ("jump_tail_hazard", "Jump and overnight-tail hazard", "Volatility", "large-move event risk", "1-5 sessions", "risk_score_heuristic", "CONDITIONAL-DATA", "tail", [_i("jump_intensity_z"), _i("overnight_gap_z"), _i("left_tail_asymmetry_z"), _i("event_density", "ratio")], "Score is a ranking heuristic until event labels are calibrated OOS.", "Corporate action/event calendar missing or tail labels leak future data."),
    ("regime_transition", "Volatility and correlation regime transition", "Regime", "regime-change risk", "5-20 sessions", "risk_score_heuristic", "EXPERIMENTAL", "regime", [_i("change_point_score", "ratio"), _i("vol_of_vol_z"), _i("cross_asset_dispersion_z"), _i("correlation_shift_z")], "Transition score is not a calibrated probability.", "Feature revisions or repeated regime flips make transition state indeterminate."),
    ("auction_pressure", "Closing-auction imbalance pressure", "Microstructure", "close-to-next-open pressure", "closing auction", "signed_score", "CONDITIONAL-DATA", "auction", [_i("auction_imbalance_z", "z", 60), _i("auction_imbalance_reliability", "ratio", 60), _i("close_depth_z", "z", 60), _i("index_rebalance_flow_z", "z", 3600)], "Requires entitled exchange auction data with actual timestamps; positive imbalance and rebalance flow mean net buying, and positive score means a higher next-open return relative to the auction close.", "Auction feed gap, stale imbalance, or venue-specific rules change."),
    ("liquidity_fragility", "Liquidity fragility / halt hazard", "Microstructure", "liquidity deterioration", "intraday-1 session", "risk_score_heuristic", "CONDITIONAL-DATA", "liquidity", [_i("spread_z", "z", 300), _i("depth_drop_z", "z", 300), _i("realized_vol_z", "z", 300), _i("volume_concentration", "ratio", 300)], "Hazard score is a triage rank; venue/halt definitions must be fixed.", "Feed outage, trading halt, or spread/depth units inconsistent across venues."),
    ("ofi_adverse_selection", "Order-flow-imbalance adverse selection", "Microstructure", "short-horizon price pressure", "seconds-30 minutes", "signed_score", "CONDITIONAL-DATA", "ofi", [_i("ofi_z", "z", 30), _i("depth_z", "z", 30), _i("depth_replenishment_ratio", "ratio", 30), _i("historical_post_fill_drift_z", "z", 30), _i("trade_condition_quality", "ratio", 30)], "Positive OFI and historical markout mean upward pressure; visible depth replenishment is a [0, 1] fraction and attenuates that pressure. Historical post-fill drift must use only fills completed and markouts available before as_of; never use the candidate signal's future fill/markout.", "Quote/trade clock misalignment, low condition coverage, or markout timestamp after as_of."),
    ("options_tail_surface", "Options-implied downside tail state", "Options", "physical left-tail event", "1-20 sessions", "risk_score_heuristic", "CONDITIONAL-DATA", "option_tail", [_i("put_skew_z"), _i("term_inversion_z"), _i("downside_var_z"), _i("surface_quality", "ratio")], "Risk-neutral surface is not a physical probability forecast.", "Stale/missing quotes, crossed market, or no-arbitrage surface failure."),
    ("dealer_gamma_scenario", "Dealer-gamma scenario map", "Options", "scenario sensitivity", "intraday-5 sessions", "signed_score", "EXPERIMENTAL", "gamma", [_i("gamma_assumption_z"), _i("spot_move_z"), _i("oi_concentration_z"), _i("gamma_input_quality", "ratio")], "Dealer position sign is an explicit scenario assumption: positive means dealers are modeled long gamma and therefore hedge counter-trend; negative means short gamma and hedge with trend. The score is conditional hedge-flow sensitivity, never observed positioning.", "Open-interest age or sign assumption changes; inferred inputs never become observed facts."),
    ("options_flow_response", "Options-flow response with intent uncertainty", "Options", "underlying response conditional on flow", "intraday-5 sessions", "signed_score", "EXPERIMENTAL", "options_flow", [_i("customer_signed_delta_flow_z", "z", 3600), _i("sweep_quality", "ratio", 3600), _i("open_close_confidence", "ratio", 3600), _i("aggressor_side_confidence", "ratio", 3600), _i("quote_condition_quality", "ratio", 3600)], "customer_signed_delta_flow_z is signed by aggressor-initiated customer delta-equivalent flow (positive means net bullish delta demand); call/put volume imbalance alone cannot establish buyer/seller initiation or direction. Open/close, aggressor-side, sweep, and quote-quality confidences each lie in [0, 1].", "Intent classifier drift, weak aggressor-side confidence, quote condition ambiguity, or non-independent confirmation."),
    ("earnings_abs_move", "Earnings absolute-move forecast", "Events", "absolute event return", "event to next session", "absolute_return", "CONDITIONAL-DATA", "earnings", [_i("implied_move", "return", 259200), _i("historical_event_move", "return", 31536000), _i("estimate_dispersion_z", "z", 259200), _i("earnings_timing_quality", "ratio", 259200)], "Estimate event-time labels without using post-event marks.", "Event time/announcement type uncertain or option surface quality fails."),
    ("post_earnings_drift", "Post-earnings drift after controls", "Events/fundamentals", "sector-adjusted drift", "5-20 sessions", "signed_score", "CORE-RESEARCH", "pead", [_i("standardized_surprise_z"), _i("revision_breadth", "ratio"), _i("post_event_drift_z"), _i("sector_residual_z")], "Surprise and consensus vintages are locked as available before release.", "Restatement, stale consensus, confounded event, or reversal kill condition."),
    ("revision_diffusion", "Consensus revision diffusion", "Fundamentals", "forward residual return", "20-60 sessions", "signed_score", "CONDITIONAL-DATA", "revision", [_i("revision_momentum_z"), _i("analyst_breadth", "ratio"), _i("revision_dispersion_z"), _i("revision_recency", "ratio")], "Analyst estimates are timestamped and point-in-time; coverage is explicit.", "Estimate history is revised/backfilled or analyst panel coverage changes."),
    # Age caps reflect the measurement/publication cadence of each input family.
    # available_at remains the point-in-time gate; these caps do not backdate data.
    ("alt_data_nowcast", "Alternative-data nowcast with panel-drift control", "Alternative data", "fundamental surprise", "1-3 months", "signed_score", "EXPERIMENTAL", "altdata", [_i("panel_surprise_z", "z", 35 * 86400), _i("panel_stability", "ratio", 35 * 86400), _i("panel_coverage", "ratio", 35 * 86400), _i("panel_drift_z", "z", 35 * 86400)], "Source labels and use rights are approved; panel drift is measurable; source-specific release cadence is documented.", "Coverage/selection drift, unclear rights, or source/model revision."),
    ("xbrl_cash_conversion", "XBRL cash-conversion inflection", "Fundamentals", "cash-conversion change", "1-4 quarters", "signed_score", "CONDITIONAL-DATA", "xbrl", [_i("cash_conversion_z", "z", 180 * 86400), _i("receivables_growth_gap_z", "z", 180 * 86400), _i("deferred_revenue_change_z", "z", 180 * 86400), _i("fcf_acceleration_z", "z", 180 * 86400)], "Use filing acceptance/available timestamps, accession IDs, period-end timestamps, and restatement handling.", "Amendment/restatement ambiguity, taxonomy mapping break, or non-comparable period."),
    ("filing_semantic_delta", "Filing and guidance semantic delta", "Fundamentals/NLP", "disclosure inflection", "1-4 quarters", "signed_score", "CONDITIONAL-DATA", "filing_nlp", [_i("semantic_delta_z", "z", 180 * 86400), _i("parser_confidence", "ratio", 180 * 86400), _i("novelty_score", "ratio", 180 * 86400), _i("section_relevance", "ratio", 180 * 86400)], "Compare same document sections/types and preserve parser/model version and filing-availability timestamps.", "Low parser confidence, document type mismatch, or model drift."),
    ("insider_discretionary_flow", "Insider activity adjusted for plan status", "Ownership/events", "forward residual return", "20-60 sessions", "signed_score", "CONDITIONAL-DATA", "insider", [_i("discretionary_net_flow_z", "z", 30 * 86400), _i("non_10b5_1_confidence", "ratio", 30 * 86400), _i("insider_recency", "ratio", 30 * 86400), _i("issuer_illiquidity_z")], "Distinguish discretionary transactions, plans, grants, gifts, and tax sales; use filing-availability time rather than transaction time for point-in-time replay. Positive issuer_illiquidity_z means worse exit liquidity and attenuates the flow score.", "Transaction coding or filing date is ambiguous."),
    ("13f_crowding_unwind", "13F crowding-unwind hazard", "Ownership", "crowded-position unwind risk", "1-3 quarters", "risk_score_heuristic", "CONDITIONAL-DATA", "13f", [_i("ownership_crowding_z", "z", 150 * 86400), _i("fundamental_deterioration_z", "z", 90 * 86400), _i("liquidity_stress_z"), _i("filing_staleness", "ratio", 150 * 86400)], "13F is delayed and incomplete; holdings are not current position truth. Filing staleness is an uncertainty haircut on reported crowding, not evidence of an unwind; preserve report-period and filing-availability timestamps.", "Filing vintage too stale or position/issuer mapping changes."),
    ("executed_buyback_support", "Executed buyback support", "Corporate actions", "forward issuer residual return after executed buyback activity", "5-20 sessions", "signed_score", "CONDITIONAL-DATA", "buyback", [_i("buyback_pace_float_z", "z", 180 * 86400), _i("execution_confidence", "ratio", 180 * 86400), _i("blackout_risk", "ratio", 7 * 86400), _i("liquidity_anomaly_z")], "Measure actual executed pace from reported repurchases; announcements alone are not flow. Preserve reporting-period and filing-availability timestamps. liquidity_anomaly_z is distance from normal liquidity in either direction, so its magnitude attenuates the score.", "Pace unavailable, authorization suspended, or issuer report lag unresolved."),
    ("index_flow_pressure", "Index rebalance and basket flow pressure", "Flows/events", "event-window relative return", "1-10 sessions", "signed_score", "CONDITIONAL-DATA", "index_flow", [_i("flow_estimate_z"), _i("flow_model_confidence", "ratio"), _i("days_to_effective", "days"), _i("crowding_z")], "Separate announced index rules from inferred pre-announcement flow; positive flow_estimate_z means net expected buying. A passed effective date produces a zero score.", "Rule change, stale constituent set, or crowded estimate."),
    ("macro_vintage_reaction", "Macro surprise reaction function by vintage", "Macro/rates", "cross-asset response", "intraday-5 sessions", "signed_score", "CONDITIONAL-DATA", "macro", [_i("release_surprise_z"), _i("cycle_reaction_sign", "signed_ratio"), _i("market_pricing_z"), _i("regime_confidence", "ratio")], "Use ALFRED/release vintages and market pricing before the release. cycle_reaction_sign is bounded [-1, 1]: positive means a positive unpriced surprise lifts the target instrument, negative means it lowers it, and zero means no directional response is asserted.", "Revision/vintage mismatch, event-feed delay, or reaction function whipsaw."),
    ("rates_credit_transition", "Yield-curve and credit regime transition", "Macro/rates", "market stress transition risk", "1-4 quarters", "risk_score_heuristic", "CORE-RESEARCH", "rates_credit", [_i("curve_slope_z"), _i("curve_change_z"), _i("credit_impulse_z", "z", 90 * 86400), _i("macro_transition_score", "ratio", 90 * 86400)], "Macro observations use their historical availability dates and vintages; no revised-data leakage. Positive curve_slope_z means a steeper/less inverted curve; positive curve_change_z means a move toward deeper inversion; positive credit_impulse_z means easing credit conditions (negative values mean deterioration).", "Vintage history missing or abrupt policy/market-structure break."),
    ("cot_inventory_supply", "Commodity positioning, inventory, and supply shock", "Commodities", "commodity excess return", "1-8 weeks", "signed_score", "CONDITIONAL-DATA", "cot", [_i("cot_positioning_z", "z", 14 * 86400), _i("inventory_deviation_z", "z", 8 * 86400), _i("roll_yield_z"), _i("supply_shock_score", "ratio")], "COT and inventory freshness use source-specific measurement and publication times. Positive COT positioning means crowded long exposure (faded); positive inventory deviation means above-normal supply (bearish); positive roll yield means backwardation (bullish). supply_shock_score is bounded [0, 1] and suppresses the signal. Apply only the release schedule effective on each date.", "Supply shock, delayed release, benchmark/contract roll discontinuity."),
    ("crypto_squeeze_risk", "Crypto liquidity/crowding squeeze risk", "Crypto", "liquidation/squeeze risk", "intraday-5 sessions", "risk_score_heuristic", "CONDITIONAL-DATA", "crypto", [_i("funding_z", "z", 3600), _i("open_interest_change_z", "z", 3600), _i("depth_drop_z", "z", 300), _i("onchain_flow_z", "z", 86400)], "Venue, custody, chain labels, and timestamps are distinct evidence fields.", "Venue outage, depeg, liquidation-data gap, or on-chain label uncertainty."),
]


_RISK_FORMULAS = {"tail", "regime", "liquidity", "option_tail", "13f", "rates_credit", "crypto"}
_CONTINUOUS_FORMULAS = {"har", "earnings"}
_SCORE_SEMANTICS = {
    "signed": "uncalibrated_signed_score_orientation",
    "risk": "uncalibrated_risk_rank_only",
    "continuous": "continuous_point_estimate_not_directional",
}
_TARGET_UNITS = {
    "har": "variance_fraction_squared",
    "earnings": "absolute_return_fraction",
    "tail": "binary_large_move_event",
    "regime": "binary_regime_change",
    "liquidity": "binary_liquidity_event",
    "option_tail": "binary_left_tail_event",
    "13f": "binary_unwind_event",
    "rates_credit": "binary_stress_event",
    "crypto": "binary_squeeze_event",
    "altdata": "fundamental_surprise_z",
    "xbrl": "cash_flow_quality_change_z",
    "filing_nlp": "disclosure_delta_z",
}

ENGINES: tuple[EngineSpec, ...] = tuple(
    EngineSpec(
        engine_id=f"FE{i:02d}",
        name=row[1],
        family=row[2],
        target=row[3],
        target_unit=_TARGET_UNITS.get(row[7], "forward_return_fraction"),
        horizon=row[4],
        forecast_unit=row[5],
        score_kind=("risk" if row[7] in _RISK_FORMULAS else "continuous" if row[7] in _CONTINUOUS_FORMULAS else "signed"),
        score_semantics=_SCORE_SEMANTICS[
            "risk" if row[7] in _RISK_FORMULAS else "continuous" if row[7] in _CONTINUOUS_FORMULAS else "signed"
        ],
        maturity=row[6],
        formula=row[7],
        inputs=tuple(row[8]),
        assumptions=(row[9], "Output is a research estimate, not a calibrated probability or trade instruction."),
        kill_conditions=(row[10], "Any point-in-time, quality, rights, or provenance failure forces abstention."),
        rea_trace=f"REA synthesis: {row[2]} / {row[7]} family; vendor report inventory is traceability, not validation.",
    )
    for i, row in enumerate(_raw, start=1)
)

_BY_ID = {spec.engine_id: spec for spec in ENGINES}
_BY_FORMULA = {spec.formula: spec for spec in ENGINES}


def get_engine(engine_id: str) -> EngineSpec:
    try:
        return _BY_ID[engine_id]
    except KeyError as exc:
        raise KeyError(f"unknown forecast engine: {engine_id}") from exc


def get_engine_by_formula(formula: str) -> EngineSpec:
    try:
        return _BY_FORMULA[formula]
    except KeyError as exc:
        raise KeyError(f"unknown forecast formula: {formula}") from exc
