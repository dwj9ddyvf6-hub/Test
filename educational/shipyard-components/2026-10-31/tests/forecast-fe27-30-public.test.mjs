import test from 'node:test';
import assert from 'node:assert/strict';
import {
  computeFE27ReleaseSurprise,
  computeFE28TreasuryCurve,
  computeFE28TreasuryCurveDiagnostic,
  computeFE28CreditImpulse,
  computeFE28CreditImpulseDiagnostic,
  computeFE28TransitionRisk,
  buildFE28SourceFeatures,
  computeFE29CotPositioning,
  computeFE29InventoryDeviation,
  computeFE29FuturesCurve,
  buildFE29SourceFeatures,
  computeFE30DeribitFunding,
  computeFE30DeribitOpenInterest,
  computeFE30DeribitDepthDrop,
  computeFE30LabeledOnchainFlow,
  buildFE30SourceFeatures,
} from '../research/forecast-features/fe27-30-public-v1.mjs';
import {
  EVAL, fe27Fixture, fe28CurveFixture, fe28CreditFixture,
  fe29CotFixture, fe29InventoryFixture, fe29FuturesFixture,
  fe30FundingFixture, fe30OiFixture, fe30DepthFixture, fe30OnchainFixture,
} from './fixtures/fe27-30-public-v1.mjs';

const assertClose = (actual, expected, tolerance = 1e-10) => {
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} ≠ ${expected}`);
};
const mean = xs => xs.reduce((sum, x) => sum + x, 0) / xs.length;
const sd0 = xs => Math.sqrt(mean(xs.map(x => (x - mean(xs)) ** 2)));
const z = (value, prior) => (value - mean(prior)) / sd0(prior);

test('FE27 uses a dated pre-release survey proxy and first-print errors, never substitutes a prior actual', () => {
  const input = fe27Fixture();
  const result = computeFE27ReleaseSurprise(input);
  const errors = input.prior_release_history.map(row => row.actual.value - row.expectation.value).slice(-40);
  assert.equal(result.status, 'partial');
  assert.equal(result.features.release_surprise_z, z(input.actual.value - input.expectation.value, errors));
  assert.deepEqual(result.missing_features, ['cycle_reaction_sign', 'market_pricing_z', 'regime_confidence']);
  assert.equal(result.restrictions.decision_eligible, false);
  assert.equal(result.scorer_invoked, false);
  const lateSurvey = structuredClone(input);
  lateSurvey.expectation.available_at = lateSurvey.event.release_at;
  assert.match(computeFE27ReleaseSurprise(lateSurvey).blockers[0], /expectation_not_pre_release/);
  const revisedActual = structuredClone(input);
  revisedActual.actual.is_first_release = false;
  revisedActual.actual.value_kind = 'revised';
  assert.match(computeFE27ReleaseSurprise(revisedActual).blockers[0], /actual_vintage_not_first_release/);
  const mismatchedUnit = structuredClone(input);
  mismatchedUnit.expectation.unit = 'percentage_points';
  assert.match(computeFE27ReleaseSurprise(mismatchedUnit).blockers[0], /release_expectation_identity_mismatch/);
});

test('FE28 Treasury curve uses exact 252-row prior windows and an explicit complete session grid', () => {
  const input = fe28CurveFixture();
  const result = computeFE28TreasuryCurve(input);
  const slopes = input.observations.map(row => row.ten_year_pct - row.two_year_pct);
  const slopeZ = z(slopes.at(-1), slopes.slice(-253, -1));
  const changes = slopes.slice(1).map((value, index) => slopes[index] - value);
  assertClose(result.features.curve_slope_z, slopeZ);
  assertClose(result.features.curve_change_z, z(changes.at(-1), changes.slice(0, -1)));
  assert.equal(result.measurements.slope_prior_sessions, 252);
  assert.equal(result.measurements.inversion_change_prior_sessions, 252);
  const truncated = structuredClone(input);
  truncated.observations.shift(); truncated.expected_session_dates.shift();
  assert.throws(() => computeFE28TreasuryCurve(truncated), /treasury_curve_history_not_exact/);
  const calendarGap = structuredClone(input);
  calendarGap.expected_session_dates[50] = '2026-01-01';
  assert.throws(() => computeFE28TreasuryCurve(calendarGap), /invalid_treasury_calendar|treasury_calendar_gap_or_mixed_snapshot/);
});

test('FE28 NEW credit impulse has frozen quarterly GDP denominator, no ×4, 40 prior impulses, and clocks', () => {
  const input = fe28CreditFixture();
  const result = computeFE28CreditImpulse(input);
  const flowShares = input.quarters.slice(1).map((row, i) =>
    100 * (row.credit_stock - input.quarters[i].credit_stock) / row.gdp_saar);
  const impulses = flowShares.slice(1).map((share, i) => share - flowShares[i]);
  assertClose(result.feature, z(impulses.at(-1), impulses.slice(0, -1)));
  assert.equal(result.measurement.unit, 'percentage_points_per_quarter_of_annualized_GDP');
  assert.match(result.measurement.formula, /no factor-of-four/);
  assert.equal(result.measurement.prior_impulses, 40);
  assert.equal(result.measurement.historical_availability, 'latest revised snapshot; current revised research only, not historical point-in-time evidence');
  assert.equal(result.source.quarter_clock_audit.length, 43);
  assert.equal(result.source.quarter_clock_audit.at(-1).economic_period, '2026-Q2');
  assert.equal(result.source.quarter_clock_audit.at(-1).credit_revision_at, null);
  assert.equal(result.source.quarter_clock_audit.at(-1).gdp_raw_capture_received_at, EVAL);
  const quarterlyGDP = structuredClone(input);
  quarterlyGDP.quarters[10].gdp_unit = 'quarterly_billions';
  assert.throws(() => computeFE28CreditImpulse(quarterlyGDP), /invalid_credit_quarter_or_lineage/);
  const unsupportedVintage = structuredClone(input);
  unsupportedVintage.vintage_mode = 'release_archives_as_published';
  assert.throws(() => computeFE28CreditImpulse(unsupportedVintage), /only_current_revised_snapshot_supported/);
  const missingOldest = structuredClone(input);
  missingOldest.quarters.shift();
  assert.throws(() => computeFE28CreditImpulse(missingOldest), /credit_history_not_exact/);
  const bundle = buildFE28SourceFeatures({ treasury: fe28CurveFixture(), credit: input, evaluation_at: EVAL });
  assert.deepEqual(bundle.missing_features, []);
  assert.equal(bundle.features.macro_transition_score, computeFE28TransitionRisk({
    curve_slope_z: bundle.features.curve_slope_z,
    curve_change_z: bundle.features.curve_change_z,
    credit_impulse_z: bundle.features.credit_impulse_z,
  }).feature);
  assert.match(bundle.transition_risk_measurement.formula, /tanh/);
  assert.equal(bundle.status, 'partial');
  assert.equal(bundle.scorer_invoked, false);
  assert.equal(bundle.restrictions.decision_eligible, false);
});

test('FE28 NEW transition heuristic has independent oracle, risk signs, bounds, missingness and causal clocks', () => {
  const x = { curve_slope_z: -2.25, curve_change_z: 1.5, credit_impulse_z: -0.75 };
  const result = computeFE28TransitionRisk(x);
  const oracle = 0.5 + 0.5 * Math.tanh((-x.curve_slope_z + x.curve_change_z - x.credit_impulse_z) / 3);
  assertClose(result.feature, oracle);
  assert.equal(result.measurement.stress_index, 1.5);
  assert.equal(result.measurement.stress_index_unit, 'dimensionless_linear_composite_of_standardized_z_scores');
  assert.equal(result.measurement.score_feature, 'macro_transition_score');
  assert.equal(result.measurement.score_unit, 'bounded_heuristic_index_0_1');
  assert.ok(result.feature > 0.5);
  assert.equal(computeFE28TransitionRisk({ curve_slope_z: 0, curve_change_z: 0, credit_impulse_z: 0 }).feature, 0.5);
  assert.equal(computeFE28TransitionRisk({ curve_slope_z: 1e9, curve_change_z: -1e9, credit_impulse_z: 1e9 }).feature, 0);
  assert.equal(computeFE28TransitionRisk({ curve_slope_z: -1e9, curve_change_z: 1e9, credit_impulse_z: -1e9 }).feature, 1);
  for (const bad of [
    { curve_slope_z: 1, curve_change_z: 0 },
    { curve_slope_z: NaN, curve_change_z: 0, credit_impulse_z: 0 },
    { curve_slope_z: 0, curve_change_z: Infinity, credit_impulse_z: 0 },
  ]) assert.throws(() => computeFE28TransitionRisk(bad), /transition_risk_requires_three_finite_primitives/);

  const credit = fe28CreditFixture(), curve = fe28CurveFixture();
  credit.quarters.at(-1).credit_received_at = '2026-11-01T13:00:00.000Z';
  const noFuture = buildFE28SourceFeatures({ treasury: curve, credit, evaluation_at: EVAL });
  assert.ok(noFuture.missing_features.includes('credit_impulse_z'));
  assert.ok(noFuture.missing_features.includes('macro_transition_score'));
  assert.ok(!('macro_transition_score' in noFuture.features));
});

test('FE28 unverified public source diagnostics remain separate, use age bounds, and preserve unknown clocks', () => {
  const curve = fe28CurveFixture(), diagnosticRows = structuredClone(curve.observations).map(row => {
    row.available_at = null; row.publication_at = null; return row;
  });
  const curveResult = computeFE28TreasuryCurveDiagnostic({ evaluation_at: EVAL, observations: diagnosticRows,
    snapshot_id: curve.snapshot_id, vintage_mode: 'current_latest_snapshot' });
  const slopes = diagnosticRows.map(row => row.ten_year_pct - row.two_year_pct);
  const changes = slopes.slice(1).map((value, i) => slopes[i] - value);
  assertClose(curveResult.diagnostic_features.curve_slope_z, z(slopes.at(-1), slopes.slice(-253, -1)));
  assertClose(curveResult.diagnostic_features.curve_change_z, z(changes.at(-1), changes.slice(0, -1)));
  assert.equal(curveResult.source.publication_at, null);
  assert.equal(curveResult.source.available_at, null);
  assert.equal(curveResult.source.calendar_completeness, 'unverified: no independent Treasury publishing-session calendar was supplied');
  assert.equal(curveResult.freshness.gate_status, 'closed_for_scorer_input_until_independent_calendar_and_availability_validation');
  assert.ok(curveResult.source.observed_date_age_upper_bound_seconds > 0);

  const credit = structuredClone(fe28CreditFixture());
  for (const row of credit.quarters) {
    row.credit_available_at = null; row.gdp_available_at = null;
    row.credit_publication_at = null; row.gdp_publication_at = null;
    row.credit_revision_at = null; row.gdp_revision_at = null;
    const m = /^(\d{4})-Q([1-4])$/.exec(row.quarter);
    const qEndLowerBound = new Date(Date.UTC(Number(m[1]), Number(m[2]) * 3, 0)).toISOString().slice(0, 10) + 'T00:00:00.000Z';
    row.credit_observed_at = qEndLowerBound; row.gdp_observed_at = qEndLowerBound;
  }
  const creditResult = computeFE28CreditImpulseDiagnostic(credit);
  const flowShares = credit.quarters.slice(1).map((row, i) => 100 * (row.credit_stock - credit.quarters[i].credit_stock) / row.gdp_saar);
  const impulses = flowShares.slice(1).map((share, i) => share - flowShares[i]);
  assertClose(creditResult.diagnostic_feature, z(impulses.at(-1), impulses.slice(0, -1)));
  assert.equal(creditResult.source.source_age_seconds, null);
  assert.equal(creditResult.source.publication_clock_status, 'unknown');
  assert.equal(creditResult.freshness.gate_status, 'closed_unknown_publication_clock');
  assert.equal(creditResult.measurement.prior_impulses, 40);
  const futureReceipt = structuredClone(credit);
  futureReceipt.quarters.at(-1).credit_received_at = '2026-11-01T13:00:00.000Z';
  assert.throws(() => computeFE28CreditImpulseDiagnostic(futureReceipt), /invalid_credit_diagnostic_quarter/);
});

test('FE29 CFTC managed-money positioning uses one exact futures-only contract and report/publication clocks', () => {
  const input = fe29CotFixture();
  const result = computeFE29CotPositioning(input);
  const values = input.reports.map(row => 100 * (row.managed_money_long - row.managed_money_short) / row.open_interest);
  assertClose(result.feature, z(values.at(-1), values.slice(0, -1)));
  assert.equal(result.measurement.prior_reports, 156);
  assert.equal(result.measurement.report_as_of_date, input.reports.at(-1).report_as_of_date);
  assert.equal(result.measurement.public_available_at, input.reports.at(-1).available_at);
  assert.throws(() => computeFE29CotPositioning({ ...input, contract_key: 'NYMEX:HO' }), /invalid_cot_report/);
});

test('FE29 EIA stock seasonal deviation requires five distinct, ordered ISO-week years', () => {
  const input = fe29InventoryFixture();
  const result = computeFE29InventoryDeviation(input);
  assertClose(result.feature, 2);
  assert.equal(result.measurement.matched_years, 5);
  assert.equal(result.measurement.unit, 'thousand_barrels');
  const duplicateYear = structuredClone(input);
  duplicateYear.observations[1].week_ending = '2021-11-05';
  assert.throws(() => computeFE29InventoryDeviation(duplicateYear), /invalid_inventory_history|inventory_prior_years_not_distinct|inventory_same_week_five_years_missing/);
  const outOfOrder = structuredClone(input);
  [outOfOrder.observations[0], outOfOrder.observations[1]] = [outOfOrder.observations[1], outOfOrder.observations[0]];
  assert.throws(() => computeFE29InventoryDeviation(outOfOrder), /invalid_inventory_history/);
});

test('FE29 actual settlement curve is not an ETF proxy and must match the exact session grid', () => {
  const input = fe29FuturesFixture();
  const result = computeFE29FuturesCurve(input);
  const slopes = input.observations.map(row => 100 * Math.log(row.front_settlement / row.next_settlement)
    * 365 / ((Date.parse(row.next_expiry) - Date.parse(row.front_expiry)) / 86400000));
  assertClose(result.feature, z(slopes.at(-1), slopes.slice(0, -1)));
  assert.match(result.measurement.curve_interpretation, /not ETF roll return/);
  assert.equal(result.measurement.prior_sessions, 252);
  const altered = structuredClone(input);
  altered.observations[20].session_date = '2020-01-02';
  assert.throws(() => computeFE29FuturesCurve(altered), /invalid_actual_futures_curve/);
  assert.equal(buildFE29SourceFeatures({ cot: fe29CotFixture(), inventory: fe29InventoryFixture(), futures_curve: input, evaluation_at: EVAL }).missing_features.includes('supply_shock_score'), true);
});

test('FE30 Deribit features stay venue/instrument-local and use exact independent reference math', () => {
  const fundingInput = fe30FundingFixture();
  const funding = computeFE30DeribitFunding({ ...fundingInput, evaluation_at: EVAL });
  const fundingValues = fundingInput.funding_history.map(row => row.interest_1h);
  assertClose(funding.feature, z(fundingValues.at(-1), fundingValues.slice(0, -1)));
  assert.equal(funding.measurement.prior_hours, 720);
  const oiInput = fe30OiFixture();
  const oi = computeFE30DeribitOpenInterest({ ...oiInput, evaluation_at: EVAL });
  const changes = oiInput.oi_snapshots.slice(1).map((row, i) => 100 * (row.open_interest / oiInput.oi_snapshots[i].open_interest - 1));
  assertClose(oi.feature, z(changes.at(-1), changes.slice(0, -1)));
  assert.equal(oi.measurement.prior_hourly_changes, 168);
  const depthInput = fe30DepthFixture();
  const depth = computeFE30DeribitDepthDrop({ ...depthInput, evaluation_at: EVAL });
  const depthSeries = depthInput.book_snapshots.map(book => {
    const mid = (book.bids[0][0] + book.asks[0][0]) / 2;
    return book.bids.filter(([p]) => p >= mid * 0.995).reduce((n, [, a]) => n + a, 0)
      + book.asks.filter(([p]) => p <= mid * 1.005).reduce((n, [, a]) => n + a, 0);
  });
  assertClose(depth.feature, (mean(depthSeries.slice(0, -1)) - depthSeries.at(-1)) / sd0(depthSeries.slice(0, -1)));
  assert.equal(depth.measurement.prior_snapshots, 288);
  const onchainInput = fe30OnchainFixture();
  const onchain = computeFE30LabeledOnchainFlow({ ...onchainInput, evaluation_at: EVAL });
  const flows = onchainInput.observations.map(row => row.net_flow);
  assertClose(onchain.feature, z(flows.at(-1), flows.slice(0, -1)));
  const wrongUnit = structuredClone(fundingInput);
  wrongUnit.funding_history.at(-1).unit = 'percent_per_hour';
  assert.throws(() => computeFE30DeribitFunding({ ...wrongUnit, evaluation_at: EVAL }), /deribit_funding_identity_or_unit_mismatch/);
  const venueMix = structuredClone(oiInput);
  venueMix.oi_snapshots.at(-1).instrument = 'ETH-PERPETUAL';
  assert.throws(() => computeFE30DeribitOpenInterest({ ...venueMix, evaluation_at: EVAL }), /deribit_oi_identity_or_unit_mismatch/);
  const output = buildFE30SourceFeatures({ funding: fundingInput, open_interest: oiInput, depth: depthInput, onchain: onchainInput, evaluation_at: EVAL });
  assert.equal(output.scorer_invoked, false);
  assert.equal(output.restrictions.decision_eligible, false);
  assert.ok(output.blockers.some(blocker => /prospectively captured/.test(blocker)));
});
