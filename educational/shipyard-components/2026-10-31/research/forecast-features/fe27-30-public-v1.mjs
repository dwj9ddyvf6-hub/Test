// Explicit NEW public-source transforms for FE27–FE30.
// These are bounded pure transforms over caller-supplied, normalized captures.
// They do not acquire data, attest rights/quality, invoke the pinned scorers, or
// make any path decision-eligible. Missing native inputs remain missing.

const ISO_INSTANT = /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,3})?Z$/;
const SHA256 = /^[0-9a-f]{64}$/i;
const fail = code => { throw Error(code); };
const isFinite = value => typeof value === 'number' && Number.isFinite(value);
const isInstant = value => typeof value === 'string' && ISO_INSTANT.test(value)
  && Number.isFinite(Date.parse(value)) && new Date(Date.parse(value)).toISOString().slice(0, 19) === value.slice(0, 19);
const isDate = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
  && Number.isFinite(Date.parse(value + 'T00:00:00Z'))
  && new Date(value + 'T00:00:00Z').toISOString().slice(0, 10) === value;
const ageSeconds = (at, now) => (Date.parse(now) - Date.parse(at)) / 1000;

export const FE27_PUBLIC_POLICY = Object.freeze({
  id: 'FE27_PUBLIC_RELEASE_SURPRISE_Z_V1', version: 1, origin: 'NEW_FEATURE_POLICY', engine_id: 'FE27',
  release_value: 'same measure, target period and unit; actual is the first published release value, never a revised value substituted as first print',
  expectation: 'Use a dated public survey expectation proxy (e.g. Philadelphia Fed SPF) only when it forecasts the exact target measure/period/unit and was published before the event; otherwise require a separately authorized, dated consensus vintage. Never substitute the prior actual.',
  standardization: 'current (first_release_actual - pre_release_expectation) against exactly the 40 most recent prior same-measure, same-period-type, same expectation-source-kind first-release errors; population standard deviation (ddof=0); current excluded; no shorter-window fallback.',
  freshness_max_age_seconds: 172800,
  source_clocks: 'target-period/economic-observation, scheduled/actual event, expectation public-availability, actual first-release public-availability, raw-capture receipt, and evaluation clocks remain separate',
  not_implemented: ['cycle_reaction_sign', 'market_pricing_z', 'regime_confidence'],
  interpretation: 'Partial research feature only. A public quarterly survey is not a release-day consensus poll; no calibrated probability or decision eligibility.',
});

export const FE28_PUBLIC_POLICY = Object.freeze({
  id: 'FE28_TREASURY_BIS_CREDIT_ACCELERATION_V1', version: 1, origin: 'NEW_FEATURE_POLICY', engine_id: 'FE28',
  treasury: {
    publisher: 'U.S. Treasury', dataset: 'Daily Treasury Par Yield Curve Rates',
    slope: '10-year par yield minus 2-year par yield, percentage points',
    slope_z: 'current slope against exactly the prior 252 official yield-curve sessions; population standard deviation; no current-row inclusion',
    inversion_change: 'previous session slope minus current session slope; positive means deeper inversion',
    change_z: 'current inversion change against exactly the preceding 252 session changes; population standard deviation; current excluded',
    source_max_age_seconds: 172800, required_calendar_rows: 254,
  },
  credit: {
    publisher: 'BIS Data Portal WS_TC (US series Q.US.P.A.M.XDC.A) + BEA NIPA T10105-Q',
    credit_series: 'Total credit to U.S. private non-financial sector, market value, local currency (USD) billions; BIS UNIT_MULT=9',
    gdp_series: 'BEA GDP (current-dollar nominal GDP), seasonally adjusted annual rate (SAAR), USD billions; T10105-Q raw millions converted by /1000',
    flow: 'quarterly_net_new_credit_share_pct = 100 * (C_t - C_(t-1)) / GDP_SAAR_t; no factor-of-four annualization',
    impulse: 'current quarterly_net_new_credit_share_pct minus the previous quarter value; percentage-point acceleration per quarter, not the BIS credit-to-GDP gap or a canonical credit-impulse series',
    z: 'current impulse against exactly the prior 40 quarterly impulses; population standard deviation; current excluded; no shorter-window fallback',
    source_max_age_seconds: 7776000, required_quarter_rows: 43,
    revisions: 'Must disclose source snapshot/vintage. A latest-revised BIS/BEA download can support current revised research only; it cannot be relabeled as first-release history or historical point-in-time evidence.',
  },
  transition_risk: {
    origin: 'NEW explicit transform; original FE28 starter builder unrecovered and unchanged',
    formula: 'macro_transition_score = 0.5 + 0.5 * tanh((-curve_slope_z + curve_change_z - credit_impulse_z) / 3)',
    components: 'Equal one-third weights on the three already standardized, same-evaluation-cutoff primitives; negative slope means flatter/more inverted, positive curve change means deepening inversion, negative credit impulse means deteriorating credit conditions.',
    output: 'bounded heuristic index in [0,1]; a transparent rank/index, not a ratio measurement, probability, fitted forecast, or performance claim',
    missingness: 'No score unless all three primitive features are present, finite, source-valid and aligned to the same evaluation cutoff.',
  },
  interpretation: 'Partial research features only; fixed original scorer and eligibility remain unchanged. The NEW macro-transition index is not the lost original feature builder.',
});

export const FE29_PUBLIC_POLICY = Object.freeze({
  id: 'FE29_CFTC_EIA_EXCHANGE_CURVE_V1', version: 1, origin: 'NEW_FEATURE_POLICY', engine_id: 'FE29',
  cot: {
    publisher: 'CFTC', report: 'Disaggregated Futures Only', category: 'Managed Money',
    positioning: '100 * (managed_money_long - managed_money_short) / total_open_interest; exact contract-market key; report-week observation and public release/receipt time are distinct',
    z: 'current positioning fraction against exactly the prior 156 available weekly reports; population standard deviation; no current-row inclusion',
    freshness_max_age_seconds: 1209600,
  },
  inventory: {
    publisher: 'EIA', series: 'WCESTUS1 (U.S. crude oil ending stocks excluding SPR)', unit: 'thousand barrels',
    deviation: 'current inventory minus the mean of the exactly five prior ISO-week-of-year observations, divided by their population standard deviation; no missing-year fill',
    freshness_max_age_seconds: 691200,
  },
  futures_curve: {
    source: 'Same exchange, root, quote currency, and unit; actual dated contract settlement prices (no ETF/NAV/spot proxy)',
    annualized_curve_slope: '100 * ln(front_settle / next_settle) * 365 / calendar_days_between_contract_expiries; percentage points per annum; positive is backwardation',
    z: 'current contract-pair curve slope against exactly 252 prior official sessions for the same root/exchange/unit; population standard deviation',
    freshness_max_age_seconds: 172800,
    meaning: 'Term-structure slope proxy, not an ETF roll return or realized portfolio roll yield.',
  },
  not_implemented: ['supply_shock_score'],
  interpretation: 'Partial research features only. Unknown supply-shock coverage is not zero.',
});

export const FE30_PUBLIC_POLICY = Object.freeze({
  id: 'FE30_DERIBIT_PERPETUAL_CAPTURE_V1', version: 1, origin: 'NEW_FEATURE_POLICY', engine_id: 'FE30',
  venue: 'Deribit public market-data endpoints, only where locally authorized; never route around country restrictions or endpoint denials',
  instrument_scope: 'one exact instrument per calculation; do not pool venues, perpetuals, expiries, spot books or collateral currencies',
  funding: 'Deribit public/get_funding_rate_history interest_1h, decimal fractional 1-hour rate; current value standardized against exactly 720 prior hourly observations',
  open_interest: 'percentage change in the same venue-native open-interest unit for a fixed inverse perpetual instrument; Deribit reports inverse/perpetual open interest in USD; exact current 1-hour change standardized against exactly 168 prior hourly changes',
  depth: 'sum same-instrument bid and ask amounts within 50 bp of midpoint, only when the source explicitly identifies amount units as USD; current depth drop is (prior-288-snapshot mean - current depth) / prior-288-snapshot population SD; snapshots exactly 5 minutes apart',
  freshness_max_age_seconds: { funding: 3600, open_interest: 3600, depth: 300, onchain: 86400 },
  onchain: 'Requires publisher-labeled exchange-flow records with explicit asset, network, custody/entity-label version/method, amount unit, publication/observation/receipt clocks and use-rights evidence. Raw transactions, addresses, or inferred wallet labels are not substitutes.',
  not_implemented: ['onchain_flow_z'],
  interpretation: 'Partial venue-specific research features only. Historical OI/depth requires prospectively captured immutable snapshots; the current public order-book endpoint is not a historical snapshot archive.',
});

function time(value, code) { if (!isInstant(value)) fail(code); return Date.parse(value); }
function validEvidence(row, evaluationAt, expectedSourceId) {
  if (!row || typeof row !== 'object' || Array.isArray(row) || typeof row.source_id !== 'string'
      || !row.source_id || (expectedSourceId && row.source_id !== expectedSourceId)
      || typeof row.record_id !== 'string' || !row.record_id
      || typeof row.source_url !== 'string' || !row.source_url.startsWith('https://')
      || typeof row.source_sha256 !== 'string' || !SHA256.test(row.source_sha256)
      || !isInstant(row.available_at) || !isInstant(row.received_at)
      || Date.parse(row.available_at) > Date.parse(row.received_at)
      || Date.parse(row.received_at) > Date.parse(evaluationAt)) fail('invalid_source_lineage');
  return row;
}
function exactRows(rows, count, code) {
  if (!Array.isArray(rows) || rows.length !== count) fail(code);
}
function popStats(values) {
  if (!Array.isArray(values) || !values.length || !values.every(isFinite)) fail('invalid_normalization_window');
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
  const sd = Math.sqrt(variance);
  if (!Number.isFinite(sd) || sd <= 1e-12) fail('degenerate_normalization_window');
  return { mean, sd, observations: values.length, ddof: 0 };
}
function zScore(current, prior, direction = 1) {
  if (!isFinite(current) || !isFinite(direction)) fail('invalid_feature_value');
  const stats = popStats(prior);
  return { value: direction * (current - stats.mean) / stats.sd, ...stats };
}
function quarterlyIndex(quarter) {
  const match = /^(\d{4})-Q([1-4])$/.exec(quarter || '');
  if (!match) fail('invalid_quarter');
  return Number(match[1]) * 4 + Number(match[2]) - 1;
}
function weekOfYear(date) {
  const d = new Date(date + 'T00:00:00Z');
  const day = (d.getUTCDay() + 6) % 7;
  d.setUTCDate(d.getUTCDate() - day + 3);
  const firstThursday = new Date(Date.UTC(d.getUTCFullYear(), 0, 4));
  const firstDay = (firstThursday.getUTCDay() + 6) % 7;
  firstThursday.setUTCDate(firstThursday.getUTCDate() - firstDay + 3);
  return 1 + Math.round((d - firstThursday) / (7 * 86400000));
}
function envelope(engine, policy) {
  return {
    schema: 'SHIPYARD_FE27_30_PUBLIC_FEATURES_V1', engine_id: engine,
    feature_origin: 'new_public_source_policy', feature_policy: policy,
    status: 'unavailable', features: {}, missing_features: [], blockers: [],
    scorer_invoked: false,
    restrictions: { research_only: true, decision_eligible: false, order_submission_enabled: false,
      account_data_returned: false, calibrated_probability: null, historical_point_in_time_claim: false,
      quality_score: null, rights_attestation: null },
  };
}

// FE27: exact-measure, exact-period, pre-event expectation -> first-release actual.
// A public survey remains explicitly distinct from a same-day market consensus feed.
export function computeFE27ReleaseSurprise(input) {
  const out = envelope('FE27', FE27_PUBLIC_POLICY);
  try {
    const evaluationAt = input?.evaluation_at;
    time(evaluationAt, 'invalid_evaluation_clock');
    const event = input?.event, actual = input?.actual, expected = input?.expectation;
    if (!event || !isInstant(event.release_at) || !isInstant(event.scheduled_at)
        || Date.parse(event.scheduled_at) > Date.parse(evaluationAt)
        || Date.parse(event.release_at) > Date.parse(evaluationAt)) fail('invalid_release_event');
    validEvidence(actual, evaluationAt);
    validEvidence(expected, evaluationAt);
    if (actual.is_first_release !== true || actual.value_kind !== 'first_release') fail('actual_vintage_not_first_release');
    if (!isFinite(actual.value) || !isFinite(expected.value) || !actual.unit || !expected.unit
        || actual.unit !== expected.unit || actual.measure_id !== expected.measure_id
        || actual.target_period !== expected.target_period || actual.release_series_id !== expected.release_series_id
        || actual.target_period !== event.target_period || actual.measure_id !== event.measure_id) fail('release_expectation_identity_mismatch');
    if (Date.parse(expected.available_at) >= Date.parse(event.release_at)) fail('expectation_not_pre_release');
    if (Date.parse(actual.available_at) < Date.parse(event.release_at)) fail('actual_precedes_release');
    if (!['public_survey_proxy', 'authorized_consensus'].includes(expected.expectation_kind)) fail('unknown_expectation_method');
    if (expected.expectation_kind === 'public_survey_proxy'
        && (!/Philadelphia/i.test(expected.publisher || '') || !expected.survey_release_id
          || !['mean', 'median'].includes(expected.statistic) || !Number.isInteger(expected.respondent_count)
          || expected.respondent_count < 1)) fail('invalid_public_survey_expectation');
    const history = input?.prior_release_history;
    if (!Array.isArray(history) || history.length < 40 || history.length > 120) fail('insufficient_prior_release_history');
    const ordered = [...history].sort((a, b) => Date.parse(a?.event?.release_at || 0) - Date.parse(b?.event?.release_at || 0));
    if (ordered.some((row, i) => i && row.event.release_at <= ordered[i - 1].event.release_at)) fail('duplicate_or_unordered_prior_release');
    const prior = ordered.slice(-40), errors = [];
    for (const row of prior) {
      const histEvent = row?.event, histActual = row?.actual, histExpectation = row?.expectation;
      if (!histEvent || !isInstant(histEvent.release_at) || Date.parse(histEvent.release_at) >= Date.parse(event.release_at)
          || histEvent.measure_id !== event.measure_id || histEvent.release_series_id !== event.release_series_id
          || histEvent.target_period === event.target_period) fail('prior_event_identity_mismatch');
      validEvidence(histActual, evaluationAt);
      validEvidence(histExpectation, evaluationAt);
      if (histActual.is_first_release !== true || histActual.value_kind !== 'first_release'
          || histActual.unit !== actual.unit || histExpectation.unit !== expected.unit
          || histActual.measure_id !== actual.measure_id || histExpectation.measure_id !== expected.measure_id
          || histActual.target_period !== histExpectation.target_period
          || histExpectation.target_period !== histEvent.target_period
          || histExpectation.release_series_id !== event.release_series_id
          || histExpectation.expectation_kind !== expected.expectation_kind
          || histExpectation.publisher !== expected.publisher
          || histExpectation.statistic !== expected.statistic
          || Date.parse(histExpectation.available_at) >= Date.parse(histEvent.release_at)
          || Date.parse(histActual.available_at) < Date.parse(histEvent.release_at)) fail('prior_vintage_or_unit_mismatch');
      const error = histActual.value - histExpectation.value;
      if (!isFinite(error)) fail('invalid_prior_release_error');
      errors.push(error);
    }
    const surprise = actual.value - expected.value, standardized = zScore(surprise, errors);
    if (ageSeconds(actual.available_at, evaluationAt) < 0
        || ageSeconds(actual.available_at, evaluationAt) > FE27_PUBLIC_POLICY.freshness_max_age_seconds) fail('stale_actual_release');
    out.status = 'partial';
    out.features.release_surprise_z = standardized.value;
    out.feature_measurements = {
      raw_surprise: surprise, unit: actual.unit, expectation_kind: expected.expectation_kind,
      expectation_publisher: expected.publisher, expectation_statistic: expected.statistic || null,
      prior_error_mean: standardized.mean, prior_error_population_sd: standardized.sd,
      prior_events: standardized.observations, current_event_release_at: event.release_at,
      current_expectation_available_at: expected.available_at, actual_available_at: actual.available_at,
      target_period: actual.target_period, target_measure_id: actual.measure_id,
      historical_vintage_status: 'first_release and public-survey publication clocks supplied, but source-native historical capture/rights are not independently attested',
    };
    out.missing_features = ['cycle_reaction_sign', 'market_pricing_z', 'regime_confidence'];
    out.blockers = [...out.missing_features, 'source quality/rights attestations unavailable', 'no full Python FeatureObservation validation'];
    return out;
  } catch (error) {
    out.blockers = [error?.message || 'feature_construction_failed'];
    out.missing_features = ['release_surprise_z', 'cycle_reaction_sign', 'market_pricing_z', 'regime_confidence'];
    return out;
  }
}

// FE28 curve leg. `expected_session_dates` must be the complete official date
// grid returned by the dated source/calendar capture; the transform never fills.
export function computeFE28TreasuryCurve(input) {
  const evaluationAt = input?.evaluation_at;
  time(evaluationAt, 'invalid_evaluation_clock');
  const rows = input?.observations, sessions = input?.expected_session_dates;
  exactRows(rows, FE28_PUBLIC_POLICY.treasury.required_calendar_rows, 'treasury_curve_history_not_exact');
  exactRows(sessions, FE28_PUBLIC_POLICY.treasury.required_calendar_rows, 'treasury_calendar_history_not_exact');
  if (input?.coverage_complete !== true || !input.snapshot_id || input.vintage_mode !== 'current_latest_snapshot') fail('only_current_treasury_snapshot_supported');
  if (!sessions.every(isDate) || sessions.some((date, i) => i && date <= sessions[i - 1])) fail('invalid_treasury_calendar');
  if (rows.some((row, i) => !row || row.date !== sessions[i] || row.snapshot_id !== input.snapshot_id)) fail('treasury_calendar_gap_or_mixed_snapshot');
  const sourceIds = new Set();
  const slopes = rows.map(row => {
    validEvidence(row, evaluationAt, 'US_TREASURY_PAR_YIELD_CURVE');
    sourceIds.add(row.source_id);
    if (!isDate(row.date) || row.unit !== 'percentage_point' || !isFinite(row.two_year_pct)
        || !isFinite(row.ten_year_pct) || !row.record_id || row.snapshot_id !== input.snapshot_id) fail('invalid_treasury_curve_record');
    return row.ten_year_pct - row.two_year_pct;
  });
  if (sourceIds.size !== 1) fail('mixed_treasury_sources');
  const current = rows.at(-1), freshness = ageSeconds(current.available_at, evaluationAt);
  if (freshness < 0 || freshness > FE28_PUBLIC_POLICY.treasury.source_max_age_seconds) fail('stale_treasury_curve');
  const currentSlope = slopes.at(-1), priorSlope = slopes.slice(-253, -1).slice(-252);
  const slopeZ = zScore(currentSlope, priorSlope);
  // Rows are 254 long: 253 past slopes let us form 252 past changes, then the current change.
  const priorInversionChanges = [];
  for (let i = rows.length - 253; i < rows.length - 1; i++) priorInversionChanges.push(slopes[i - 1] - slopes[i]);
  if (priorInversionChanges.length !== 252) fail('treasury_change_window_not_exact');
  const currentInversionChange = slopes.at(-2) - slopes.at(-1);
  const changeZ = zScore(currentInversionChange, priorInversionChanges);
  return {
    features: { curve_slope_z: slopeZ.value, curve_change_z: changeZ.value },
    measurements: {
      slope_percentage_points: currentSlope, slope_z_prior_mean: slopeZ.mean,
      slope_z_prior_population_sd: slopeZ.sd, slope_prior_sessions: slopeZ.observations,
      inversion_change_percentage_points_per_session: currentInversionChange,
      inversion_change_z_prior_mean: changeZ.mean, inversion_change_z_prior_population_sd: changeZ.sd,
      inversion_change_prior_sessions: changeZ.observations,
      slope_definition: '10Y minus 2Y par yield, percentage points',
      change_sign: 'previous slope minus current slope; positive means deeper inversion',
    },
    source: {
      source_id: current.source_id, source_url: current.source_url, source_record_id: current.record_id,
      snapshot_id: input.snapshot_id, response_sha256: current.source_sha256,
      observed_as_of: current.date, available_at: current.available_at, received_at: current.received_at,
      vintage_mode: input.vintage_mode,
      historical_availability: 'current snapshot may revise historical rows; not point-in-time replay',
      rights_status: 'not_attested', quality_score: null,
    },
    freshness: { age_seconds: freshness, max_age_seconds: FE28_PUBLIC_POLICY.treasury.source_max_age_seconds },
  };
}

// Source-adapter diagnostic only. The dated Treasury XML itself has no
// independent session calendar or per-row availability clock here, so this
// returns descriptive calculations separately from scorer-ready `features`.
export function computeFE28TreasuryCurveDiagnostic(input) {
  const evaluationAt = input?.evaluation_at, rows = input?.observations;
  time(evaluationAt, 'invalid_evaluation_clock');
  exactRows(rows, FE28_PUBLIC_POLICY.treasury.required_calendar_rows, 'treasury_curve_history_not_exact');
  if (!input.snapshot_id || input.vintage_mode !== 'current_latest_snapshot') fail('only_current_treasury_snapshot_supported');
  let priorDate = null, snapshotHash = null;
  const slopes = rows.map(row => {
    if (!row || row.source_id !== 'US_TREASURY_PAR_YIELD_CURVE' || !isDate(row.date)
        || row.unit !== 'percentage_point' || !isFinite(row.two_year_pct) || !isFinite(row.ten_year_pct)
        || row.snapshot_id !== input.snapshot_id || !row.record_id || !row.source_url?.startsWith('https://')
        || !SHA256.test(row.source_sha256 || '') || !isInstant(row.received_at)
        || Date.parse(row.received_at) > Date.parse(evaluationAt)
        || !(row.available_at === null || row.available_at === undefined)
        || !(row.publication_at === null || row.publication_at === undefined)
        || row.date > evaluationAt.slice(0, 10) || (priorDate && row.date <= priorDate)) fail('invalid_treasury_diagnostic_record');
    if (snapshotHash && snapshotHash !== row.snapshot_id) fail('mixed_treasury_snapshot');
    snapshotHash = row.snapshot_id; priorDate = row.date;
    return row.ten_year_pct - row.two_year_pct;
  });
  const slopeStats = popStats(slopes.slice(-253, -1));
  const priorChanges = [];
  for (let i = rows.length - 253; i < rows.length - 1; i++) priorChanges.push(slopes[i - 1] - slopes[i]);
  exactRows(priorChanges, 252, 'treasury_change_window_not_exact');
  const latest = rows.at(-1), slopeZ = (slopes.at(-1) - slopeStats.mean) / slopeStats.sd;
  const currentChange = slopes.at(-2) - slopes.at(-1), changeStats = popStats(priorChanges);
  const changeZ = (currentChange - changeStats.mean) / changeStats.sd;
  const dateLowerBound = Date.parse(latest.date + 'T00:00:00.000Z');
  const ageUpperBound = (Date.parse(evaluationAt) - dateLowerBound) / 1000;
  if (!Number.isFinite(ageUpperBound) || ageUpperBound < 0) fail('invalid_treasury_observation_age_bound');
  return {
    diagnostic_features: { curve_slope_z: slopeZ, curve_change_z: changeZ },
    measurements: { slope_percentage_points: slopes.at(-1), slope_z_prior_mean: slopeStats.mean,
      slope_z_prior_population_sd: slopeStats.sd, slope_prior_observations: 252,
      inversion_change_percentage_points_per_observation: currentChange,
      inversion_change_z_prior_mean: changeStats.mean, inversion_change_z_prior_population_sd: changeStats.sd,
      inversion_change_prior_observations: 252,
      slope_definition: '10Y minus 2Y par yield, percentage points',
      change_sign: 'previous slope minus current slope; positive means deeper inversion' },
    source: { source_id: latest.source_id, source_url: latest.source_url, source_record_id: latest.record_id,
      snapshot_id: latest.snapshot_id, response_sha256: latest.source_sha256, observed_date: latest.date,
      observed_date_age_upper_bound_seconds: ageUpperBound, publication_at: null, available_at: null,
      received_at: latest.received_at, vintage_mode: 'current_latest_snapshot',
      availability_clock_semantics: 'publication clock unknown; receipt is retained separately and never resets source age',
      observation_clock_semantics: 'date-only observation; age upper bound starts at 00:00Z on the observation date',
      calendar_completeness: 'unverified: no independent Treasury publishing-session calendar was supplied',
      historical_availability: 'current snapshot may revise historical rows; not point-in-time replay',
      rights_status: 'not_attested', quality_score: null },
    freshness: { age_upper_bound_seconds: ageUpperBound,
      max_age_seconds: FE28_PUBLIC_POLICY.treasury.source_max_age_seconds,
      within_max_age_by_bound: ageUpperBound <= FE28_PUBLIC_POLICY.treasury.source_max_age_seconds,
      gate_status: 'closed_for_scorer_input_until_independent_calendar_and_availability_validation' },
  };
}

// FE28 credit leg. Inputs use 43 consecutive quarters: 40 prior impulses, one
// prior flow, and the current flow. Quarterly flow/GDP is deliberately NOT
// multiplied by four; that would define a materially different annualized series.
export function computeFE28CreditImpulse(input) {
  const evaluationAt = input?.evaluation_at;
  time(evaluationAt, 'invalid_evaluation_clock');
  const rows = input?.quarters;
  exactRows(rows, FE28_PUBLIC_POLICY.credit.required_quarter_rows, 'credit_history_not_exact');
  if (input.vintage_mode !== 'current_latest_snapshot'
      || !input.credit_snapshot_id || !input.gdp_snapshot_id) fail('only_current_revised_snapshot_supported');
  const creditImpulses = [];
  let previousQuarter = null, currency = null;
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    if (!row || quarterlyIndex(row.quarter) !== (i ? previousQuarter + 1 : quarterlyIndex(row.quarter))
        || row.credit_snapshot_id !== input.credit_snapshot_id || row.gdp_snapshot_id !== input.gdp_snapshot_id
        || row.credit_source_id !== 'BIS:F2.3' || row.gdp_source_id !== 'BEA:GDP'
        || row.credit_unit !== 'local_currency_billions' || row.gdp_unit !== 'local_currency_billions_SAAR'
        || row.measure !== 'private_nonfinancial_credit' || !isFinite(row.credit_stock)
        || !isFinite(row.gdp_saar) || row.credit_stock <= 0 || row.gdp_saar <= 0
        || row.currency !== 'USD' || !isInstant(row.credit_available_at) || !isInstant(row.gdp_available_at)
        || !isInstant(row.credit_received_at) || !isInstant(row.gdp_received_at)
        || !(row.credit_publication_at === null || row.credit_publication_at === undefined || isInstant(row.credit_publication_at))
        || !(row.gdp_publication_at === null || row.gdp_publication_at === undefined || isInstant(row.gdp_publication_at))
        || !(row.credit_revision_at === null || row.credit_revision_at === undefined || isInstant(row.credit_revision_at))
        || !(row.gdp_revision_at === null || row.gdp_revision_at === undefined || isInstant(row.gdp_revision_at))
        || !row.credit_record_id || !row.gdp_record_id
        || !SHA256.test(row.credit_source_sha256 || '') || !SHA256.test(row.gdp_source_sha256 || '')
        || Date.parse(row.credit_available_at) > Date.parse(row.credit_received_at)
        || Date.parse(row.gdp_available_at) > Date.parse(row.gdp_received_at)
        || Date.parse(row.credit_received_at) > Date.parse(evaluationAt)
        || Date.parse(row.gdp_received_at) > Date.parse(evaluationAt)
        || (row.credit_publication_at && (Date.parse(row.credit_publication_at) > Date.parse(row.credit_received_at)
          || Date.parse(row.credit_publication_at) > Date.parse(evaluationAt)))
        || (row.gdp_publication_at && (Date.parse(row.gdp_publication_at) > Date.parse(row.gdp_received_at)
          || Date.parse(row.gdp_publication_at) > Date.parse(evaluationAt)))
        || (row.credit_revision_at && (Date.parse(row.credit_revision_at) > Date.parse(row.credit_received_at)
          || Date.parse(row.credit_revision_at) > Date.parse(evaluationAt)))
        || (row.gdp_revision_at && (Date.parse(row.gdp_revision_at) > Date.parse(row.gdp_received_at)
          || Date.parse(row.gdp_revision_at) > Date.parse(evaluationAt)))) fail('invalid_credit_quarter_or_lineage');
    if (currency && row.currency !== currency) fail('credit_currency_mismatch');
    currency = row.currency;
    previousQuarter = quarterlyIndex(row.quarter);
    if (i >= 2) {
      const prev = rows[i - 1], prev2 = rows[i - 2];
      // GDP_SAAR is an annualized level; use the published quarterly debt-stock
      // flow against it as-is. Do not multiply by 4 and do not substitute an ETF.
      const flowSharePct = 100 * (row.credit_stock - prev.credit_stock) / row.gdp_saar;
      const priorFlowSharePct = 100 * (prev.credit_stock - prev2.credit_stock) / prev.gdp_saar;
      creditImpulses.push(flowSharePct - priorFlowSharePct);
    }
  }
  const current = rows.at(-1), latestAvailable = [current.credit_available_at, current.gdp_available_at].sort().at(-1);
  const freshness = ageSeconds(latestAvailable, evaluationAt);
  if (freshness < 0 || freshness > FE28_PUBLIC_POLICY.credit.source_max_age_seconds) fail('stale_credit_observation');
  if (creditImpulses.length !== 41) fail('credit_impulse_history_not_exact');
  const impulse = creditImpulses.at(-1), normalized = zScore(impulse, creditImpulses.slice(0, -1));
  return {
    feature: normalized.value,
    measurement: {
      credit_impulse_quarterly_pp_of_gdp_saar: impulse, unit: 'percentage_points_per_quarter_of_annualized_GDP',
      formula: '100 * ((C_t-C_(t-1))/GDP_SAAR_t - (C_(t-1)-C_(t-2))/GDP_SAAR_(t-1)); no factor-of-four annualization',
      z_prior_mean: normalized.mean, z_prior_population_sd: normalized.sd,
      prior_impulses: normalized.observations, standardization_ddof: 0,
      economic_period: current.quarter, currency, vintage_mode: input.vintage_mode,
      historical_availability: 'latest revised snapshot; current revised research only, not historical point-in-time evidence',
    },
    source: {
      credit_source: 'BIS F2.3 total credit to private non-financial sector', credit_source_id: current.credit_source_id,
      credit_record_id: current.credit_record_id, credit_sha256: current.credit_source_sha256,
      credit_available_at: current.credit_available_at, credit_received_at: current.credit_received_at,
      gdp_source: 'BEA nominal GDP SAAR', gdp_source_id: current.gdp_source_id,
      gdp_record_id: current.gdp_record_id, gdp_sha256: current.gdp_source_sha256,
      gdp_available_at: current.gdp_available_at, gdp_received_at: current.gdp_received_at,
      credit_snapshot_id: input.credit_snapshot_id, gdp_snapshot_id: input.gdp_snapshot_id,
      quarter_clock_audit: rows.map(row => ({ economic_period: row.quarter,
        credit_publication_at: row.credit_publication_at ?? null,
        credit_capture_availability_at: row.credit_available_at,
        credit_revision_at: row.credit_revision_at ?? null,
        credit_raw_capture_received_at: row.credit_received_at,
        gdp_publication_at: row.gdp_publication_at ?? null,
        gdp_capture_availability_at: row.gdp_available_at,
        gdp_revision_at: row.gdp_revision_at ?? null,
        gdp_raw_capture_received_at: row.gdp_received_at,
        credit_clock_semantics: row.credit_clock_semantics || 'capture availability clock supplied; publication clock not independently identified',
        gdp_clock_semantics: row.gdp_clock_semantics || 'capture availability clock supplied; publication clock not independently identified',
        credit_vintage_status: row.credit_revision_at ? 'revision_timestamp_supplied_but_value_is_current_snapshot' : 'revision_timestamp_unknown_current_snapshot',
        gdp_vintage_status: row.gdp_revision_at ? 'revision_timestamp_supplied_but_value_is_current_snapshot' : 'revision_timestamp_unknown_current_snapshot' })),
      rights_status: 'not_attested', quality_score: null,
    },
    freshness: { age_seconds: freshness, max_age_seconds: FE28_PUBLIC_POLICY.credit.source_max_age_seconds },
  };
}

// Unverified latest-revised source capture: compute only a descriptive
// diagnostic, with no false age based on retrieval and no scorer-ready value.
export function computeFE28CreditImpulseDiagnostic(input) {
  const evaluationAt = input?.evaluation_at, rows = input?.quarters;
  time(evaluationAt, 'invalid_evaluation_clock');
  exactRows(rows, FE28_PUBLIC_POLICY.credit.required_quarter_rows, 'credit_history_not_exact');
  if (input.vintage_mode !== 'current_latest_snapshot' || !input.credit_snapshot_id || !input.gdp_snapshot_id) fail('only_current_revised_snapshot_supported');
  let previousIndex = null;
  for (const row of rows) {
    const index = quarterlyIndex(row?.quarter);
    const match = /^(\d{4})-Q([1-4])$/.exec(row.quarter);
    const qEnd = new Date(Date.UTC(Number(match[1]), Number(match[2]) * 3, 0)).toISOString().slice(0, 10);
    const periodStart = `${qEnd}T00:00:00.000Z`;
    if (!row || (previousIndex !== null && index !== previousIndex + 1)
        || row.credit_snapshot_id !== input.credit_snapshot_id || row.gdp_snapshot_id !== input.gdp_snapshot_id
        || row.credit_source_id !== 'BIS:F2.3' || row.gdp_source_id !== 'BEA:GDP'
        || row.credit_unit !== 'local_currency_billions' || row.gdp_unit !== 'local_currency_billions_SAAR'
        || row.measure !== 'private_nonfinancial_credit' || !isFinite(row.credit_stock) || !isFinite(row.gdp_saar)
        || row.credit_stock <= 0 || row.gdp_saar <= 0 || row.currency !== 'USD'
        || row.credit_observed_at !== periodStart || row.gdp_observed_at !== periodStart
        || !isInstant(row.credit_received_at) || !isInstant(row.gdp_received_at)
        || Date.parse(row.credit_received_at) > Date.parse(evaluationAt) || Date.parse(row.gdp_received_at) > Date.parse(evaluationAt)
        || !(row.credit_available_at === null || row.credit_available_at === undefined)
        || !(row.gdp_available_at === null || row.gdp_available_at === undefined)
        || !(row.credit_publication_at === null || row.credit_publication_at === undefined)
        || !(row.gdp_publication_at === null || row.gdp_publication_at === undefined)
        || !(row.credit_revision_at === null || row.credit_revision_at === undefined)
        || !(row.gdp_revision_at === null || row.gdp_revision_at === undefined)
        || !SHA256.test(row.credit_source_sha256 || '') || !SHA256.test(row.gdp_source_sha256 || '')
        || !row.credit_record_id || !row.gdp_record_id) fail('invalid_credit_diagnostic_quarter');
    previousIndex = index;
  }
  // Quarterly net new credit divided by annualized GDP; no ×4. Because the
  // denominator is the current quarter SAAR, use each quarter's own GDP value.
  const flowShares = rows.slice(1).map((row, i) => 100 * (row.credit_stock - rows[i].credit_stock) / row.gdp_saar);
  const impulses = flowShares.slice(1).map((value, i) => value - flowShares[i]);
  exactRows(impulses, 41, 'credit_impulse_history_not_exact');
  const prior = impulses.slice(0, -1), stats = popStats(prior), current = impulses.at(-1);
  const age = null;
  return {
    diagnostic_feature: (current - stats.mean) / stats.sd,
    measurement: { credit_impulse_quarterly_pp_of_gdp_saar: current, unit: 'percentage_points_per_quarter_of_annualized_GDP',
      formula: '100 * ((C_t-C_(t-1))/GDP_SAAR_t - (C_(t-1)-C_(t-2))/GDP_SAAR_(t-1)); no factor-of-four annualization',
      z_prior_mean: stats.mean, z_prior_population_sd: stats.sd, prior_impulses: 40,
      economic_period: rows.at(-1).quarter, currency: 'USD', vintage_mode: input.vintage_mode,
      historical_availability: 'latest revised snapshot; current revised research only, not historical point-in-time evidence' },
    source: { credit_source: 'BIS F2.3 total credit to private non-financial sector', gdp_source: 'BEA NIPA Table 1.1.5 current-dollar GDP',
      credit_snapshot_id: input.credit_snapshot_id, gdp_snapshot_id: input.gdp_snapshot_id,
      credit_publication_at: null, gdp_publication_at: null, credit_revision_at: null, gdp_revision_at: null,
      publication_clock_status: 'unknown', first_seen_receipt_at: rows.at(-1).credit_received_at,
      gdp_first_seen_receipt_at: rows.at(-1).gdp_received_at, source_age_seconds: age,
      source_age_status: 'unknown; publication/release clock is not independently joined; receipt does not reset age',
      quarter_clock_audit: rows.map(row => ({ economic_period: row.quarter,
        credit_observation_period_lower_bound: row.credit_observed_at, credit_publication_at: null,
        credit_available_at: null, credit_revision_at: null, credit_raw_capture_received_at: row.credit_received_at,
        gdp_observation_period_lower_bound: row.gdp_observed_at, gdp_publication_at: null,
        gdp_available_at: null, gdp_revision_at: null, gdp_raw_capture_received_at: row.gdp_received_at,
        credit_clock_semantics: 'economic period end at 00:00Z is a lower bound only, not publication/availability',
        gdp_clock_semantics: 'economic period end at 00:00Z is a lower bound only, not publication/availability' })),
      rights_status: 'not_attested', quality_score: null },
    freshness: { age_seconds: null, max_age_seconds: FE28_PUBLIC_POLICY.credit.source_max_age_seconds,
      gate_status: 'closed_unknown_publication_clock' },
  };
}

// NEW FE28 transition index. It operates only on three already normalized
// features from the same evaluation cutoff; this is not a fitted probability.
export function computeFE28TransitionRisk(input) {
  const values = [input?.curve_slope_z, input?.curve_change_z, input?.credit_impulse_z];
  if (!values.every(isFinite)) fail('transition_risk_requires_three_finite_primitives');
  const stress = (-values[0] + values[1] - values[2]) / 3;
  const score = 0.5 + 0.5 * Math.tanh(stress);
  if (!Number.isFinite(score) || score < 0 || score > 1) fail('transition_risk_out_of_range');
  return {
    feature: score,
    measurement: { stress_index: stress, stress_index_unit: 'dimensionless_linear_composite_of_standardized_z_scores',
      score_feature: 'macro_transition_score', score_unit: 'bounded_heuristic_index_0_1', formula: FE28_PUBLIC_POLICY.transition_risk.formula,
      curve_slope_z: values[0], curve_change_z: values[1], credit_impulse_z: values[2],
      interpretation: 'higher indicates the selected flat/inversion-deepening/credit-deterioration combination; not a calibrated probability' },
  };
}

export function buildFE28SourceFeatures(input) {
  const out = envelope('FE28', FE28_PUBLIC_POLICY);
  out.missing_features = ['curve_slope_z', 'curve_change_z', 'credit_impulse_z', 'macro_transition_score'];
  if (!isInstant(input?.evaluation_at)) { out.blockers = ['invalid_evaluation_clock']; return out; }
  try {
    const curve = computeFE28TreasuryCurve({ ...input.treasury, evaluation_at: input.evaluation_at });
    Object.assign(out.features, curve.features); out.treasury_source = curve.source; out.treasury_measurements = curve.measurements;
    out.missing_features = out.missing_features.filter(key => !(key in curve.features));
  } catch (error) { out.blockers.push(`treasury:${error?.message || 'unavailable'}`); }
  try {
    const credit = computeFE28CreditImpulse({ ...input.credit, evaluation_at: input.evaluation_at });
    out.features.credit_impulse_z = credit.feature; out.credit_source = credit.source;
    out.credit_measurement = credit.measurement; out.missing_features = out.missing_features.filter(key => key !== 'credit_impulse_z');
  } catch (error) { out.blockers.push(`credit:${error?.message || 'unavailable'}`); }
  if (['curve_slope_z', 'curve_change_z', 'credit_impulse_z'].every(key => isFinite(out.features[key]))) {
    try {
      const transition = computeFE28TransitionRisk(out.features);
      out.features.macro_transition_score = transition.feature;
      out.transition_risk_measurement = transition.measurement;
      out.missing_features = out.missing_features.filter(key => key !== 'macro_transition_score');
    } catch (error) { out.blockers.push(`transition_risk:${error?.message || 'unavailable'}`); }
  } else out.blockers.push('macro_transition_score_requires_three_verified_same_cutoff_primitives');
  out.blockers.push('NEW transition index is not the lost original builder or a calibrated probability', 'source quality/rights attestations unavailable', 'no full Python FeatureObservation validation');
  out.status = Object.keys(out.features).length ? 'partial' : 'unavailable';
  return out;
}

// FE29 CFTC: exact contract/report category; public report-as-of date is not the
// public-availability clock. Standardization uses only the previous 156 reports.
export function computeFE29CotPositioning(input) {
  const evaluationAt = input?.evaluation_at;
  time(evaluationAt, 'invalid_evaluation_clock');
  const rows = input?.reports;
  if (!Array.isArray(rows) || rows.length !== 157 || !input.contract_key) fail('cot_history_not_exact');
  let previous = null;
  const fractions = rows.map(row => {
    validEvidence(row, evaluationAt, 'CFTC:COT:DCOT_FUTURES_ONLY');
    const asOf = row?.report_as_of_date;
    if (!isDate(asOf) || !row.market_key || row.market_key !== input.contract_key
        || row.report_type !== 'disaggregated_futures_only' || row.category !== 'managed_money'
        || ![row.managed_money_long, row.managed_money_short, row.open_interest].every(isFinite)
        || row.managed_money_long < 0 || row.managed_money_short < 0 || row.open_interest <= 0
        || (previous && asOf <= previous)) fail('invalid_cot_report');
    previous = asOf;
    return 100 * (row.managed_money_long - row.managed_money_short) / row.open_interest;
  });
  const current = rows.at(-1), freshness = ageSeconds(current.available_at, evaluationAt);
  if (freshness < 0 || freshness > FE29_PUBLIC_POLICY.cot.freshness_max_age_seconds) fail('stale_cot_release');
  const normalized = zScore(fractions.at(-1), fractions.slice(0, -1));
  return {
    feature: normalized.value, measurement: { managed_money_net_oi_pct: fractions.at(-1), unit: 'percent_of_open_interest',
      z_prior_mean: normalized.mean, z_prior_population_sd: normalized.sd, prior_reports: normalized.observations,
      report_as_of_date: current.report_as_of_date, public_available_at: current.available_at,
      market_key: current.market_key, report_type: current.report_type, category: current.category },
    source: { source_id: current.source_id, record_id: current.record_id, source_url: current.source_url,
      source_sha256: current.source_sha256, received_at: current.received_at, rights_status: 'not_attested', quality_score: null },
    freshness: { age_seconds: freshness, max_age_seconds: FE29_PUBLIC_POLICY.cot.freshness_max_age_seconds },
  };
}

// FE29 EIA weekly stock: same ISO week from exactly five prior observations;
// inventory is a stock, not a flow/production estimate.
export function computeFE29InventoryDeviation(input) {
  const evaluationAt = input?.evaluation_at;
  time(evaluationAt, 'invalid_evaluation_clock');
  const rows = input?.observations;
  if (!Array.isArray(rows) || rows.length < 6 || rows.length > 400) fail('inventory_history_not_exact');
  const current = rows.at(-1);
  validEvidence(current, evaluationAt, 'EIA:WPSR:WCESTUS1');
  if (current.series_id !== 'WCESTUS1' || current.unit !== 'thousand_barrels'
      || !isDate(current.week_ending) || !isFinite(current.value) || current.value < 0) fail('invalid_eia_inventory');
  let previousDate = null;
  for (const row of rows) {
    validEvidence(row, evaluationAt, 'EIA:WPSR:WCESTUS1');
    if (!row || row.series_id !== current.series_id || row.unit !== current.unit
        || !isDate(row.week_ending) || !isFinite(row.value) || row.value < 0
        || (previousDate !== null && row.week_ending <= previousDate)) fail('invalid_inventory_history');
    previousDate = row.week_ending;
  }
  const season = weekOfYear(current.week_ending);
  const prior = rows.slice(0, -1).filter(row => weekOfYear(row.week_ending) === season).slice(-5);
  exactRows(prior, 5, 'inventory_same_week_five_years_missing');
  if (new Set(prior.map(row => row.week_ending.slice(0, 4))).size !== 5) fail('inventory_prior_years_not_distinct');
  const stats = popStats(prior.map(row => row.value));
  const freshness = ageSeconds(current.available_at, evaluationAt);
  if (freshness < 0 || freshness > FE29_PUBLIC_POLICY.inventory.freshness_max_age_seconds) fail('stale_eia_inventory');
  return {
    feature: (current.value - stats.mean) / stats.sd,
    measurement: { current_inventory: current.value, seasonal_mean: stats.mean, seasonal_population_sd: stats.sd,
      unit: current.unit, seasonal_week: season, matched_years: prior.length, week_ending: current.week_ending,
      public_available_at: current.available_at, series_id: current.series_id },
    source: { source_id: current.source_id, record_id: current.record_id, source_url: current.source_url,
      source_sha256: current.source_sha256, received_at: current.received_at, rights_status: 'not_attested', quality_score: null },
    freshness: { age_seconds: freshness, max_age_seconds: FE29_PUBLIC_POLICY.inventory.freshness_max_age_seconds },
  };
}

// FE29 futures curve: same listed market/root; exact pair expiries and contract
// settlements, never ETF prices or continuous back-adjusted/roll-adjusted bars.
export function computeFE29FuturesCurve(input) {
  const evaluationAt = input?.evaluation_at;
  time(evaluationAt, 'invalid_evaluation_clock');
  const rows = input?.observations;
  exactRows(rows, 253, 'futures_curve_history_not_exact');
  const sessions = input?.expected_session_dates;
  exactRows(sessions, 253, 'futures_curve_calendar_not_exact');
  if (input.coverage_complete !== true || !sessions.every(isDate)
      || sessions.some((date, index) => index && date <= sessions[index - 1])) fail('futures_curve_calendar_incomplete');
  let priorDate = null, identity = null;
  const slopes = rows.map((row, index) => {
    validEvidence(row, evaluationAt);
    if (row.data_kind !== 'official_exchange_settlement' || !isDate(row.session_date)
        || row.session_date !== sessions[index]
        || !row.exchange || !row.root || !row.quote_currency || !row.price_unit
        || !row.front_contract || !row.next_contract || !isDate(row.front_expiry) || !isDate(row.next_expiry)
        || !isFinite(row.front_settlement) || !isFinite(row.next_settlement)
        || row.front_settlement <= 0 || row.next_settlement <= 0
        || Date.parse(row.front_expiry) >= Date.parse(row.next_expiry)
        || (priorDate && row.session_date <= priorDate)) fail('invalid_actual_futures_curve');
    const key = [row.source_id, row.exchange, row.root, row.quote_currency, row.price_unit].join('|');
    if (identity && key !== identity) fail('futures_curve_identity_changed');
    identity = key; priorDate = row.session_date;
    const days = (Date.parse(row.next_expiry) - Date.parse(row.front_expiry)) / 86400000;
    return 100 * Math.log(row.front_settlement / row.next_settlement) * 365 / days;
  });
  const current = rows.at(-1), freshness = ageSeconds(current.available_at, evaluationAt);
  if (freshness < 0 || freshness > FE29_PUBLIC_POLICY.futures_curve.freshness_max_age_seconds) fail('stale_futures_curve');
  const normalized = zScore(slopes.at(-1), slopes.slice(0, -1));
  return {
    feature: normalized.value, measurement: { annualized_log_curve_slope_pct: slopes.at(-1), unit: 'percent_per_annum',
      z_prior_mean: normalized.mean, z_prior_population_sd: normalized.sd, prior_sessions: normalized.observations,
      front_contract: current.front_contract, next_contract: current.next_contract,
      front_expiry: current.front_expiry, next_expiry: current.next_expiry,
      session_date: current.session_date, curve_interpretation: 'positive is backwardation; curve-slope proxy, not ETF roll return or realized portfolio roll yield' },
    source: { source_id: current.source_id, source_url: current.source_url, record_id: current.record_id,
      source_sha256: current.source_sha256, received_at: current.received_at,
      rights_status: 'not_attested; exchange redistribution/reuse terms must be reviewed separately', quality_score: null },
    freshness: { age_seconds: freshness, max_age_seconds: FE29_PUBLIC_POLICY.futures_curve.freshness_max_age_seconds },
  };
}

export function buildFE29SourceFeatures(input) {
  const out = envelope('FE29', FE29_PUBLIC_POLICY);
  out.missing_features = ['cot_positioning_z', 'inventory_deviation_z', 'roll_yield_z', 'supply_shock_score'];
  if (!isInstant(input?.evaluation_at)) { out.blockers = ['invalid_evaluation_clock']; return out; }
  for (const [key, fn, field] of [
    ['cot_positioning_z', computeFE29CotPositioning, 'cot'],
    ['inventory_deviation_z', computeFE29InventoryDeviation, 'inventory'],
    ['roll_yield_z', computeFE29FuturesCurve, 'futures_curve'],
  ]) {
    try {
      const result = fn({ ...input[field], evaluation_at: input.evaluation_at });
      out.features[key] = result.feature; out[`${field}_source`] = result.source;
      out[`${field}_measurement`] = result.measurement;
      out[`${field}_freshness`] = result.freshness;
      out.missing_features = out.missing_features.filter(name => name !== key);
    } catch (error) { out.blockers.push(`${field}:${error?.message || 'unavailable'}`); }
  }
  out.blockers.push('supply_shock_score_not_defined_or_bound', 'source quality/rights attestations unavailable', 'no full Python FeatureObservation validation');
  out.status = Object.keys(out.features).length ? 'partial' : 'unavailable';
  return out;
}

function deribitInstrument(input) {
  if (input?.venue !== 'Deribit' || input?.instrument !== 'BTC-PERPETUAL'
      || input?.contract_type !== 'inverse_perpetual' || input?.oi_unit !== 'USD') fail('deribit_instrument_identity_or_unit_mismatch');
}
function hourlyRows(rows, count, evaluationAt, valueField) {
  exactRows(rows, count, 'deribit_history_not_exact');
  let previous = null;
  for (const row of rows) {
    validEvidence(row, evaluationAt, 'DERIBIT:PUBLIC_MARKET_DATA');
    if (!isInstant(row.observed_at) || !isFinite(row[valueField])
        || (previous !== null && Date.parse(row.observed_at) - previous !== 3600000)) fail('deribit_hourly_clock_or_unit_invalid');
    previous = Date.parse(row.observed_at);
  }
  return rows;
}
export function computeFE30DeribitFunding(input) {
  time(input?.evaluation_at, 'invalid_evaluation_clock'); deribitInstrument(input);
  const rows = hourlyRows(input.funding_history, 721, input.evaluation_at, 'interest_1h');
  if (rows.some(row => row.instrument !== input.instrument || row.unit !== 'fraction_per_hour')) fail('deribit_funding_identity_or_unit_mismatch');
  const current = rows.at(-1), freshness = ageSeconds(current.observed_at, input.evaluation_at);
  const availabilityAge = ageSeconds(current.available_at, input.evaluation_at);
  if (freshness < 0 || freshness > FE30_PUBLIC_POLICY.freshness_max_age_seconds.funding
      || availabilityAge < 0 || availabilityAge > FE30_PUBLIC_POLICY.freshness_max_age_seconds.funding) fail('stale_deribit_funding');
  const normalized = zScore(current.interest_1h, rows.slice(0, -1).map(row => row.interest_1h));
  return { feature: normalized.value, measurement: { interest_1h_fraction: current.interest_1h, unit: 'fraction_per_hour',
    z_prior_mean: normalized.mean, z_prior_population_sd: normalized.sd, prior_hours: normalized.observations,
    observed_at: current.observed_at, available_at: current.available_at }, freshness: { age_seconds: freshness,
      availability_age_seconds: availabilityAge, max_age_seconds: 3600 },
    source: { source_id: current.source_id, record_id: current.record_id, source_url: current.source_url,
      source_sha256: current.source_sha256, received_at: current.received_at, rights_status: 'not_attested', quality_score: null } };
}

export function computeFE30DeribitOpenInterest(input) {
  time(input?.evaluation_at, 'invalid_evaluation_clock'); deribitInstrument(input);
  const rows = hourlyRows(input.oi_snapshots, 170, input.evaluation_at, 'open_interest');
  if (rows.some(row => row.instrument !== input.instrument || row.unit !== input.oi_unit || row.open_interest <= 0)) fail('deribit_oi_identity_or_unit_mismatch');
  const changes = rows.slice(1).map((row, index) => 100 * (row.open_interest / rows[index].open_interest - 1));
  const current = changes.at(-1), baseline = changes.slice(-169, -1);
  exactRows(baseline, 168, 'deribit_oi_baseline_not_exact');
  const currentRow = rows.at(-1), freshness = ageSeconds(currentRow.observed_at, input.evaluation_at);
  const availabilityAge = ageSeconds(currentRow.available_at, input.evaluation_at);
  if (freshness < 0 || freshness > FE30_PUBLIC_POLICY.freshness_max_age_seconds.open_interest
      || availabilityAge < 0 || availabilityAge > FE30_PUBLIC_POLICY.freshness_max_age_seconds.open_interest) fail('stale_deribit_oi');
  const normalized = zScore(current, baseline);
  return { feature: normalized.value, measurement: { open_interest: currentRow.open_interest, unit: input.oi_unit,
    one_hour_change_pct: current, z_prior_mean: normalized.mean, z_prior_population_sd: normalized.sd,
    prior_hourly_changes: normalized.observations, observed_at: currentRow.observed_at, available_at: currentRow.available_at,
    note: 'Notional OI percentage change for this fixed inverse perpetual; price/notional effects are not removed.' },
    freshness: { age_seconds: freshness, availability_age_seconds: availabilityAge, max_age_seconds: 3600 },
    source: { source_id: currentRow.source_id, record_id: currentRow.record_id, source_url: currentRow.source_url,
      source_sha256: currentRow.source_sha256, received_at: currentRow.received_at, rights_status: 'not_attested', quality_score: null } };
}

function depthWithinFiftyBps(book) {
  const bids = book?.bids, asks = book?.asks;
  if (!Array.isArray(bids) || !Array.isArray(asks) || !bids.length || !asks.length) fail('empty_deribit_book_side');
  const validSide = (side, direction) => {
    let prev = null;
    for (const level of side) {
      if (!Array.isArray(level) || level.length !== 2 || !level.every(isFinite) || level[0] <= 0 || level[1] < 0
          || (prev !== null && direction * level[0] >= direction * prev)) fail('invalid_deribit_book_level');
      prev = level[0];
    }
  };
  validSide(bids, 1); validSide(asks, -1);
  const bestBid = bids[0][0], bestAsk = asks[0][0];
  if (bestBid >= bestAsk) fail('crossed_deribit_book');
  const mid = (bestBid + bestAsk) / 2, low = mid * (1 - 0.005), high = mid * (1 + 0.005);
  const bidDepth = bids.filter(([price]) => price >= low && price <= mid).reduce((sum, [, amount]) => sum + amount, 0);
  const askDepth = asks.filter(([price]) => price <= high && price >= mid).reduce((sum, [, amount]) => sum + amount, 0);
  return { mid, bidDepth, askDepth, total: bidDepth + askDepth };
}
export function computeFE30DeribitDepthDrop(input) {
  time(input?.evaluation_at, 'invalid_evaluation_clock'); deribitInstrument(input);
  exactRows(input.book_snapshots, 289, 'deribit_depth_history_not_exact');
  if (input.depth_amount_unit !== 'USD') fail('deribit_depth_unit_unverified');
  let previous = null;
  const depths = input.book_snapshots.map(snapshot => {
    validEvidence(snapshot, input.evaluation_at, 'DERIBIT:PUBLIC_MARKET_DATA');
    if (!isInstant(snapshot.observed_at) || snapshot.instrument !== input.instrument
        || snapshot.amount_unit !== 'USD'
        || (previous !== null && Date.parse(snapshot.observed_at) - previous !== 300000)) fail('deribit_depth_clock_or_identity_mismatch');
    previous = Date.parse(snapshot.observed_at);
    return depthWithinFiftyBps(snapshot);
  });
  const latest = input.book_snapshots.at(-1), currentDepth = depths.at(-1).total;
  const freshness = ageSeconds(latest.observed_at, input.evaluation_at);
  const availabilityAge = ageSeconds(latest.available_at, input.evaluation_at);
  if (freshness < 0 || freshness > FE30_PUBLIC_POLICY.freshness_max_age_seconds.depth
      || availabilityAge < 0 || availabilityAge > FE30_PUBLIC_POLICY.freshness_max_age_seconds.depth) fail('stale_deribit_depth');
  const stats = popStats(depths.slice(0, -1).map(depth => depth.total));
  const dropZ = (stats.mean - currentDepth) / stats.sd;
  return { feature: dropZ, measurement: { depth_within_mid_50bp_usd: currentDepth, prior_mean_usd: stats.mean,
    prior_population_sd_usd: stats.sd, unit: 'USD of displayed resting book amount within +/-50 bp',
    prior_snapshots: stats.observations, observed_at: latest.observed_at, available_at: latest.available_at,
    bid_depth_usd: depths.at(-1).bidDepth, ask_depth_usd: depths.at(-1).askDepth,
    note: 'Venue-local displayed depth; not consolidated crypto liquidity.' },
    freshness: { age_seconds: freshness, availability_age_seconds: availabilityAge, max_age_seconds: 300 },
    source: { source_id: latest.source_id, record_id: latest.record_id, source_url: latest.source_url,
      source_sha256: latest.source_sha256, received_at: latest.received_at, rights_status: 'not_attested', quality_score: null } };
}

// Labeled-flow adapter deliberately accepts publisher-defined entity data only;
// it cannot convert raw addresses/transactions into exchange labels.
export function computeFE30LabeledOnchainFlow(input) {
  time(input?.evaluation_at, 'invalid_evaluation_clock');
  const rows = input?.observations;
  if (!Array.isArray(rows) || rows.length !== 31) fail('onchain_flow_history_not_exact');
  const current = rows.at(-1);
  for (const row of rows) {
    validEvidence(row, input.evaluation_at);
    if (row.label_origin !== 'publisher_labeled_entity_flow' || !row.publisher_label_version
        || !row.label_method || !row.asset || !row.network || !row.custody_scope
        || row.unit !== 'native_asset' || !isInstant(row.observed_at) || !isFinite(row.net_flow)
        || !['negative_is_net_outflow', 'positive_is_net_inflow'].includes(row.sign_convention)
        || row.sign_convention !== current.sign_convention) fail('onchain_labels_or_units_not_verified');
  }
  if (rows.some((row, index) => index && Date.parse(row.observed_at) - Date.parse(rows[index - 1].observed_at) !== 86400000)) fail('onchain_daily_history_gap');
  const identity = row => [row.source_id, row.asset, row.network, row.custody_scope,
    row.publisher_label_version, row.label_method, row.unit, row.sign_convention].join('|');
  if (rows.some(row => identity(row) !== identity(current))) fail('onchain_flow_identity_changed');
  if (input.rights_attestation !== 'documented_for_internal_research') fail('onchain_use_rights_unverified');
  const freshness = ageSeconds(current.observed_at, input.evaluation_at);
  const availabilityAge = ageSeconds(current.available_at, input.evaluation_at);
  if (freshness < 0 || freshness > FE30_PUBLIC_POLICY.freshness_max_age_seconds.onchain
      || availabilityAge < 0 || availabilityAge > FE30_PUBLIC_POLICY.freshness_max_age_seconds.onchain) fail('stale_onchain_flow');
  const normalized = zScore(current.net_flow, rows.slice(0, -1).map(row => row.net_flow));
  return { feature: normalized.value, measurement: { net_flow_native_asset: current.net_flow, unit: 'native_asset',
    asset: current.asset, network: current.network, custody_scope: current.custody_scope,
    publisher_label_version: current.publisher_label_version, label_method: current.label_method,
    sign_convention: current.sign_convention, z_prior_mean: normalized.mean,
    z_prior_population_sd: normalized.sd, prior_days: normalized.observations, observed_at: current.observed_at,
    available_at: current.available_at }, freshness: { age_seconds: freshness,
      availability_age_seconds: availabilityAge, max_age_seconds: 86400 },
    source: { source_id: current.source_id, record_id: current.record_id, source_url: current.source_url,
      source_sha256: current.source_sha256, received_at: current.received_at,
      rights_status: 'caller_asserted_documented_for_internal_research; not independently reviewed', quality_score: null } };
}

export function buildFE30SourceFeatures(input) {
  const out = envelope('FE30', FE30_PUBLIC_POLICY);
  out.missing_features = ['funding_z', 'open_interest_change_z', 'depth_drop_z', 'onchain_flow_z'];
  if (!isInstant(input?.evaluation_at)) { out.blockers = ['invalid_evaluation_clock']; return out; }
  for (const [key, fn, field] of [
    ['funding_z', computeFE30DeribitFunding, 'funding'],
    ['open_interest_change_z', computeFE30DeribitOpenInterest, 'open_interest'],
    ['depth_drop_z', computeFE30DeribitDepthDrop, 'depth'],
    ['onchain_flow_z', computeFE30LabeledOnchainFlow, 'onchain'],
  ]) {
    try {
      const result = fn({ ...input[field], evaluation_at: input.evaluation_at });
      out.features[key] = result.feature; out[`${field}_source`] = result.source;
      out[`${field}_measurement`] = result.measurement; out[`${field}_freshness`] = result.freshness || null;
      out.missing_features = out.missing_features.filter(name => name !== key);
    } catch (error) { out.blockers.push(`${field}:${error?.message || 'unavailable'}`); }
  }
  out.blockers.push('historical OI/depth require prospectively captured immutable snapshots',
    'on-chain provider labels/use rights require independent verification',
    'venue availability is jurisdiction-specific; no restriction bypass', 'source quality attestations unavailable', 'no full Python FeatureObservation validation');
  out.status = Object.keys(out.features).length ? 'partial' : 'unavailable';
  return out;
}
