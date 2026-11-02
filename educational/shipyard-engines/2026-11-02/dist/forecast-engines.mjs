import { FORECAST_ENGINE_CATALOG, SILICON_FORECAST_SOURCE } from './forecast-engine-catalog.mjs?v=045398d692d988aa';
export { SILICON_FORECAST_SOURCE };

const MAX_ABSOLUTE_INPUT = 1e18;
const clip = (value, low, high) => Math.max(low, Math.min(high, value));

function signed(value, drivers = {}) {
  const score = clip(value, -8, 8);
  return { value: score, model_score: score, drivers };
}

function risk(logit, drivers = {}) {
  const bounded = clip(logit, -30, 30);
  return { value: 1 / (1 + Math.exp(-bounded)), model_score: logit, drivers };
}

const scorers = Object.freeze({
  trend: x => {
    const agreement = 0.45 * x.ret_21d_z + 0.35 * x.ret_63d_z + 0.20 * x.ret_252d_z;
    const pathQuality = clip(x.trend_efficiency, 0, 1);
    const volDamp = 1 / (1 + 0.20 * Math.abs(x.vol_regime));
    return signed(agreement * (0.35 + 0.65 * pathQuality) * volDamp,
      { horizon_agreement: agreement, path_quality: pathQuality, vol_damp: volDamp });
  },
  mean_reversion: x => {
    const chop = clip((0.58 - x.hurst) / 0.25, 0, 1);
    const trendGate = clip(1 - Math.abs(x.trend_z) / 3, 0, 1);
    const score = -x.residual_z * chop * trendGate / (1 + 0.15 * Math.abs(x.vol_regime));
    return signed(score, { chop_gate: chop, trend_gate: trendGate, residual_z: x.residual_z });
  },
  breakout: x => {
    const acceptance = clip(x.acceptance, 0, 1);
    const falseBreak = clip(x.false_break_rate, 0, 1);
    const volumeConfirm = clip(1 + 0.12 * x.volume_surprise_z, 0.5, 1.5);
    const score = x.break_distance_z * acceptance * volumeConfirm * (1 - falseBreak);
    return signed(score, { acceptance, volume_confirm: volumeConfirm, false_break_rate: falseBreak });
  },
  gap: x => {
    const residual = x.gap_z - x.fair_gap_z;
    const acceptance = clip(x.open_acceptance, 0, 1);
    const acceptanceState = 2 * acceptance - 1;
    const liquidity = clip(x.premarket_liquidity, 0, 1);
    const score = residual * acceptanceState * (0.4 + 0.6 * liquidity);
    return signed(score, { gap_residual_z: residual, open_acceptance: acceptance,
      acceptance_state: acceptanceState, liquidity });
  },
  breadth: x => {
    const participation = clip(x.breadth_delta, -1, 1);
    const score = 0.50 * participation * 3 + 0.25 * x.advance_decline_z
      + 0.15 * x.new_high_low_z + 0.10 * x.index_trend_z;
    return signed(score, { breadth_delta: participation, advance_decline_z: x.advance_decline_z,
      new_high_low_z: x.new_high_low_z });
  },
  sector: x => {
    const breadth = clip(x.leadership_breadth, 0, 1);
    const dispersion = clip(x.sector_dispersion_z, 0, 3);
    const concentrationPenalty = 1 / (1 + 0.20 * dispersion);
    const score = (0.55 * x.sector_momentum_rank_z + 0.25 * x.sector_flow_z
      + 0.20 * (2 * breadth - 1)) * concentrationPenalty;
    return signed(score, { breadth, dispersion, concentration_penalty: concentrationPenalty });
  },
  leadlag: x => {
    const stability = clip(x.lag_stability, 0, 1);
    const r2 = clip(x.relationship_r2, 0, 1);
    const score = x.leader_return_z * x.lag_beta * stability * clip((r2 - 0.15) / 0.65, 0, 1);
    return signed(score, { lag_stability: stability, relationship_r2: r2, lag_beta: x.lag_beta });
  },
  har: x => {
    const logForecast = 0.50 * x.log_rv_1 + 0.30 * x.log_rv_5 + 0.20 * x.log_rv_22;
    const clippedForecast = clip(logForecast, -40, 10);
    const clippedBaseline = clip(x.log_rv_baseline, -40, 10);
    const value = Math.exp(clippedForecast);
    const modelScore = clippedForecast - clippedBaseline;
    return { value, model_score: modelScore,
      drivers: { log_variance_ratio: modelScore, baseline_variance: Math.exp(clippedBaseline) } };
  },
  tail: x => risk(-0.15 + 0.48 * x.jump_intensity_z + 0.36 * Math.abs(x.overnight_gap_z)
    + 0.30 * x.left_tail_asymmetry_z + 0.45 * clip(x.event_density, 0, 1),
  { jump_intensity_z: x.jump_intensity_z, overnight_gap_z: Math.abs(x.overnight_gap_z), event_density: x.event_density }),
  regime: x => risk(-0.40 + 1.10 * clip(x.change_point_score, 0, 1)
    + 0.30 * Math.abs(x.vol_of_vol_z) + 0.25 * Math.abs(x.cross_asset_dispersion_z)
    + 0.30 * Math.abs(x.correlation_shift_z),
  { change_point_score: x.change_point_score, vol_of_vol_z: x.vol_of_vol_z,
    correlation_shift_z: x.correlation_shift_z }),
  auction: x => {
    const reliability = clip(x.auction_imbalance_reliability, 0, 1);
    const depthDamp = 1 / (1 + Math.max(0, x.close_depth_z) * 0.20);
    const score = (x.auction_imbalance_z + 0.20 * x.index_rebalance_flow_z) * reliability * depthDamp;
    return signed(score, { imbalance_reliability: reliability, depth_damp: depthDamp });
  },
  liquidity: x => {
    const logit = -1 + 0.50 * Math.max(0, x.spread_z) + 0.50 * Math.max(0, x.depth_drop_z)
      + 0.35 * Math.max(0, x.realized_vol_z) + 0.30 * clip(x.volume_concentration, 0, 1);
    return risk(logit, { spread_z: x.spread_z, depth_drop_z: x.depth_drop_z,
      realized_vol_z: x.realized_vol_z });
  },
  ofi: x => {
    const quality = clip(x.trade_condition_quality, 0, 1);
    const depth = Math.max(0, x.depth_z);
    const replenishment = clip(x.depth_replenishment_ratio, 0, 1);
    const replenishmentDamp = 1 - 0.65 * replenishment;
    const score = (0.65 * x.ofi_z + 0.35 * x.historical_post_fill_drift_z)
      * quality * replenishmentDamp / (1 + 0.25 * depth);
    return signed(score, { quality, normalized_depth: depth, replenishment,
      replenishment_damp: replenishmentDamp, historical_post_fill_drift_z: x.historical_post_fill_drift_z });
  },
  option_tail: x => {
    const surfaceQuality = clip(x.surface_quality, 0, 1);
    const logit = -0.50 + surfaceQuality * (0.55 * x.put_skew_z
      + 0.35 * x.term_inversion_z + 0.35 * x.downside_var_z);
    return risk(logit, { surface_quality: surfaceQuality, put_skew_z: x.put_skew_z,
      term_inversion_z: x.term_inversion_z });
  },
  gamma: x => {
    const quality = clip(x.gamma_input_quality, 0, 1);
    const score = -x.gamma_assumption_z * x.spot_move_z
      * (1 + 0.20 * Math.abs(x.oi_concentration_z)) * quality;
    return signed(score, { gamma_assumption_z: x.gamma_assumption_z, spot_move_z: x.spot_move_z,
      inferred_input_quality: quality });
  },
  options_flow: x => {
    const sweep = clip(x.sweep_quality, 0, 1);
    const intent = clip(x.open_close_confidence, 0, 1);
    const aggressor = clip(x.aggressor_side_confidence, 0, 1);
    const quoteQuality = clip(x.quote_condition_quality, 0, 1);
    const score = x.customer_signed_delta_flow_z * sweep * intent * aggressor * quoteQuality;
    return signed(score, { sweep_quality: sweep, open_close_confidence: intent,
      aggressor_side_confidence: aggressor, quote_quality: quoteQuality });
  },
  earnings: x => {
    const implied = Math.max(0, x.implied_move);
    const historical = Math.max(0, x.historical_event_move);
    const dispersionAdjustment = 1 + 0.08 * Math.max(-2, Math.min(2, x.estimate_dispersion_z));
    const timing = clip(x.earnings_timing_quality, 0, 1);
    const value = (0.60 * implied + 0.40 * historical) * dispersionAdjustment * timing;
    return { value, model_score: dispersionAdjustment - 1,
      drivers: { implied_move: implied, historical_event_move: historical,
        dispersion_adjustment: dispersionAdjustment } };
  },
  pead: x => {
    const persistence = clip(x.revision_breadth, 0, 1);
    const score = (0.50 * x.standardized_surprise_z + 0.30 * x.post_event_drift_z
      + 0.20 * x.sector_residual_z) * (0.5 + 0.5 * persistence);
    return signed(score, { revision_breadth: persistence, surprise_z: x.standardized_surprise_z });
  },
  revision: x => {
    const breadth = clip(x.analyst_breadth, 0, 1);
    const recency = clip(x.revision_recency, 0, 1);
    const dispersionPenalty = 1 / (1 + 0.20 * Math.abs(x.revision_dispersion_z));
    return signed(x.revision_momentum_z * breadth * recency * dispersionPenalty,
      { breadth, recency, dispersion_penalty: dispersionPenalty });
  },
  altdata: x => {
    const stability = clip(x.panel_stability, 0, 1);
    const coverage = clip(x.panel_coverage, 0, 1);
    const reliability = stability * coverage / (1 + Math.abs(x.panel_drift_z));
    return signed(x.panel_surprise_z * reliability,
      { panel_reliability: reliability, panel_drift_z: x.panel_drift_z });
  },
  xbrl: x => {
    const acceleration = 0.35 * x.cash_conversion_z + 0.20 * x.fcf_acceleration_z
      + 0.25 * x.deferred_revenue_change_z - 0.20 * x.receivables_growth_gap_z;
    return signed(acceleration, { cash_conversion_z: x.cash_conversion_z,
      receivables_growth_gap_z: x.receivables_growth_gap_z,
      fcf_acceleration_z: x.fcf_acceleration_z });
  },
  filing_nlp: x => {
    const parser = clip(x.parser_confidence, 0, 1);
    const novelty = clip(x.novelty_score, 0, 1);
    const relevance = clip(x.section_relevance, 0, 1);
    return signed(x.semantic_delta_z * parser * novelty * relevance,
      { parser_confidence: parser, novelty, relevance });
  },
  insider: x => {
    const planConfidence = clip(x.non_10b5_1_confidence, 0, 1);
    const recency = clip(x.insider_recency, 0, 1);
    const liquidity = 1 / (1 + Math.max(0, x.issuer_illiquidity_z) * 0.2);
    return signed(x.discretionary_net_flow_z * planConfidence * recency * liquidity,
      { non_10b5_1_confidence: planConfidence, recency, liquidity_factor: liquidity });
  },
  '13f': x => {
    const staleness = clip(x.filing_staleness, 0, 1);
    const crowding = Math.max(0, x.ownership_crowding_z);
    const crowdingFreshness = 1 - staleness;
    const logit = -0.25 + 0.40 * crowding * crowdingFreshness
      + 0.40 * Math.max(0, x.fundamental_deterioration_z)
      + 0.35 * Math.max(0, x.liquidity_stress_z);
    return risk(logit, { staleness, crowding_freshness: crowdingFreshness,
      crowding_z: x.ownership_crowding_z,
      fundamental_deterioration_z: x.fundamental_deterioration_z });
  },
  buyback: x => {
    const execution = clip(x.execution_confidence, 0, 1);
    const blackout = clip(x.blackout_risk, 0, 1);
    const liquidity = 1 / (1 + 0.15 * Math.abs(x.liquidity_anomaly_z));
    return signed(x.buyback_pace_float_z * execution * (1 - blackout) * liquidity,
      { execution_confidence: execution, blackout_risk: blackout, liquidity_factor: liquidity });
  },
  index_flow: x => {
    const confidence = clip(x.flow_model_confidence, 0, 1);
    const crowding = clip(x.crowding_z, 0, 4);
    if (x.days_to_effective < 0) {
      return signed(0, { flow_confidence: confidence, time_weight: 0,
        crowding, event_passed: 1 });
    }
    const timeWeight = Math.exp(-x.days_to_effective / 10);
    return signed(x.flow_estimate_z * confidence * timeWeight / (1 + 0.15 * crowding),
      { flow_confidence: confidence, time_weight: timeWeight, crowding, event_passed: 0 });
  },
  macro: x => {
    const regime = clip(x.regime_confidence, 0, 1);
    const surprise = x.release_surprise_z - 0.35 * x.market_pricing_z;
    const reactionSign = clip(x.cycle_reaction_sign, -1, 1);
    return signed(surprise * reactionSign * regime,
      { unpriced_surprise: surprise, cycle_reaction_sign: reactionSign, regime_confidence: regime });
  },
  rates_credit: x => {
    const transition = clip(x.macro_transition_score, 0, 1);
    const curveSignal = clip(-x.curve_slope_z + 0.25 * x.curve_change_z, -4, 4);
    const creditStress = Math.max(0, -x.credit_impulse_z);
    return risk(-0.70 + 0.55 * curveSignal + 0.60 * creditStress + 0.65 * transition,
      { curve_signal: curveSignal, credit_stress: creditStress, transition });
  },
  cot: x => {
    const supplyShock = clip(x.supply_shock_score, 0, 1);
    const crowdingFade = -x.cot_positioning_z * clip(Math.abs(x.cot_positioning_z) / 2, 0, 1.5);
    const inventory = -0.60 * x.inventory_deviation_z + 0.25 * x.roll_yield_z;
    return signed((0.60 * crowdingFade + 0.40 * inventory) * (1 - supplyShock),
      { crowding_fade: crowdingFade, inventory_carry: inventory, supply_shock: supplyShock });
  },
  crypto: x => {
    const funding = Math.abs(x.funding_z);
    const oi = Math.abs(x.open_interest_change_z);
    const depth = Math.max(0, x.depth_drop_z);
    const onchain = Math.abs(x.onchain_flow_z);
    const logit = -0.65 + 0.35 * funding + 0.30 * oi + 0.45 * depth + 0.15 * onchain;
    return risk(logit, { funding_extreme: funding, open_interest_change: oi,
      depth_drop: depth, onchain_flow: onchain });
  },
});

function deepFreeze(value) {
  if (!value || typeof value !== 'object') return value;
  if (!Object.isFrozen(value)) Object.freeze(value);
  for (const child of Object.values(value)) deepFreeze(child);
  return value;
}

const forecastCatalog = deepFreeze(FORECAST_ENGINE_CATALOG);
const forecastSource = deepFreeze(SILICON_FORECAST_SOURCE);
const engineById = new Map(forecastCatalog.map(engine => [engine.engine_id, engine]));

export function listForecastEngines() {
  return forecastCatalog;
}

export function evaluateForecastEngine(engineId, features) {
  const spec = engineById.get(engineId);
  if (!spec) return { status: 'abstained', engine_id: engineId, errors: ['Unknown forecast engine.'] };
  if (!features || typeof features !== 'object') {
    return { status: 'abstained', engine_id: engineId, errors: ['Feature values must be a plain object.'] };
  }

  const inputNames = new Set(spec.inputs.map(input => input.name));
  const errors = [];
  const checked = Object.create(null);
  try {
    if (Array.isArray(features)) {
      return { status: 'abstained', engine_id: engineId, errors: ['Feature values must be a plain object.'] };
    }
    const prototype = Object.getPrototypeOf(features);
    if (prototype !== Object.prototype && prototype !== null) {
      errors.push('Feature values must not inherit inputs from a custom prototype.');
    }
    for (const name of Reflect.ownKeys(features)) {
      if (typeof name !== 'string') {
        errors.push('Feature keys must be strings.');
        continue;
      }
      if (!inputNames.has(name)) {
        errors.push(`${name}: not part of ${spec.engine_id}'s input contract.`);
      }
      const descriptor = Object.getOwnPropertyDescriptor(features, name);
      if (!descriptor || !Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
        errors.push(`${name}: accessor properties are not accepted.`);
      }
    }
    for (const input of spec.inputs) {
      const descriptor = Object.getOwnPropertyDescriptor(features, input.name);
      if (!descriptor) {
        errors.push(`${input.name}: required input is missing.`);
        continue;
      }
      if (!Object.prototype.hasOwnProperty.call(descriptor, 'value')) continue;
      const value = descriptor.value;
      if (value === undefined || value === null || value === '') {
        errors.push(`${input.name}: required input is missing.`);
        continue;
      }
      if (typeof value !== 'number' || !Number.isFinite(value) || Math.abs(value) > MAX_ABSOLUTE_INPUT) {
        errors.push(`${input.name}: must be a finite number with absolute value no greater than ${MAX_ABSOLUTE_INPUT}.`);
        continue;
      }
      if (input.value_range && (value < input.value_range[0] || value > input.value_range[1])) {
        errors.push(`${input.name}: must be within the registered range ${input.value_range[0]} to ${input.value_range[1]}.`);
        continue;
      }
      checked[input.name] = value;
    }
  } catch {
    return { status: 'abstained', engine_id: engineId, errors: ['Feature object could not be safely inspected.'] };
  }
  if (errors.length) return { status: 'abstained', engine_id: engineId, errors };

  let signal;
  try {
    signal = scorers[spec.formula]?.(checked);
  } catch {
    signal = null;
  }
  if (!signal || !Number.isFinite(signal.value) || !Number.isFinite(signal.model_score)
    || !signal.drivers || Object.values(signal.drivers).some(value => !Number.isFinite(value))) {
    return { status: 'abstained', engine_id: engineId, errors: ['The scorer did not produce finite outputs.'] };
  }

  const direction = spec.score_kind !== 'signed' ? 'not_directional'
    : signal.value > 0 ? 'positive' : signal.value < 0 ? 'negative' : 'neutral';
  return {
    status: 'research_only_score',
    engine_id: spec.engine_id,
    engine_name: spec.name,
    source: forecastSource,
    target: spec.target,
    target_unit: spec.target_unit,
    horizon: spec.horizon,
    forecast_unit: spec.forecast_unit,
    score_kind: spec.score_kind,
    forecast_value: signal.value,
    model_score: signal.model_score,
    direction,
    drivers: signal.drivers,
    decision_eligible: false,
    calibrated_probability: null,
    input_provenance: 'manual_unverified',
    eligibility_blockers: [
      'Manual feature values have no verified source, vintage, rights, age, quality, or independence evidence.',
      'The first-pass coefficients are hypotheses; no fitted or calibrated performance claim is attached.',
    ],
  };
}
