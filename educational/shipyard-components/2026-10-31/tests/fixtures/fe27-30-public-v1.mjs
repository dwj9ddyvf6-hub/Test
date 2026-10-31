// Synthetic-only fixtures. No provider calls or real market observations.
import { createHash } from 'node:crypto';

export const EVAL = '2026-11-01T12:00:00.000Z';
const hash = value => createHash('sha256').update(String(value)).digest('hex');
const iso = ms => new Date(ms).toISOString();
const evidence = (sourceId, recordId, availableAt, sourceUrl = 'https://example.org/synthetic-capture') => ({
  source_id: sourceId, record_id: recordId, source_url: sourceUrl,
  source_sha256: hash(`${sourceId}|${recordId}`), available_at: availableAt, received_at: EVAL,
});

function quarterString(index) {
  const year = Math.floor(index / 4), q = index % 4 + 1;
  return `${year}-Q${q}`;
}
const qindex = q => { const [, y, n] = /^(\d{4})-Q([1-4])$/.exec(q); return Number(y) * 4 + Number(n) - 1; };

export function fe27Fixture() {
  const currentEvent = { release_series_id: 'BEA:GDP:ADVANCE', measure_id: 'real_gdp_qoq_saar', target_period: '2026-Q3',
    scheduled_at: '2026-10-30T13:30:00.000Z', release_at: '2026-10-30T14:00:00.000Z' };
  const expectation = { ...evidence('PHILADELPHIA_SPF', 'SPF-2026Q3-RGDP', '2026-10-29T12:00:00.000Z', 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters'),
    publisher: 'Federal Reserve Bank of Philadelphia', expectation_kind: 'public_survey_proxy', survey_release_id: 'SPF-2026-Q3',
    statistic: 'median', respondent_count: 24, release_series_id: currentEvent.release_series_id,
    measure_id: currentEvent.measure_id, target_period: currentEvent.target_period, unit: 'annualized_percentage_points', value: 2.1 };
  const actual = { ...evidence('BEA:GDP:ADVANCE', 'GDP-2026Q3-FIRST', currentEvent.release_at, 'https://www.bea.gov/data/gdp/gross-domestic-product'),
    is_first_release: true, value_kind: 'first_release', release_series_id: currentEvent.release_series_id,
    measure_id: currentEvent.measure_id, target_period: currentEvent.target_period,
    unit: 'annualized_percentage_points', value: 2.4 };
  const currentIndex = qindex(currentEvent.target_period);
  const prior_release_history = Array.from({ length: 40 }, (_, i) => {
    const target_period = quarterString(currentIndex - 40 + i), year = Number(target_period.slice(0, 4));
    const quarter = Number(target_period.slice(-1)), month = (quarter - 1) * 3 + 2;
    const releaseAt = iso(Date.UTC(year, month, 25, 14, 0, 0));
    const priorEvent = { release_series_id: currentEvent.release_series_id, measure_id: currentEvent.measure_id,
      target_period, scheduled_at: iso(Date.parse(releaseAt) - 1800000), release_at: releaseAt };
    const error = i; // 0..39: mean 19.5, population SD sqrt(133.25).
    const priorExpectation = { ...evidence('PHILADELPHIA_SPF', `SPF-${target_period}`, iso(Date.parse(releaseAt) - 86400000), 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters'),
      publisher: 'Federal Reserve Bank of Philadelphia', expectation_kind: 'public_survey_proxy', survey_release_id: `SPF-${target_period}`,
      statistic: 'median', respondent_count: 20, release_series_id: currentEvent.release_series_id,
      measure_id: currentEvent.measure_id, target_period, unit: 'annualized_percentage_points', value: 1.0 };
    const priorActual = { ...evidence('BEA:GDP:ADVANCE', `GDP-${target_period}-FIRST`, iso(Date.parse(releaseAt) + 1000), 'https://www.bea.gov/data/gdp/gross-domestic-product'),
      is_first_release: true, value_kind: 'first_release', release_series_id: currentEvent.release_series_id,
      measure_id: currentEvent.measure_id, target_period, unit: 'annualized_percentage_points', value: 1.0 + error };
    return { event: priorEvent, actual: priorActual, expectation: priorExpectation };
  });
  return { evaluation_at: EVAL, event: currentEvent, actual, expectation, prior_release_history };
}

export function fe28CurveFixture() {
  const dates = [];
  let d = Date.parse('2026-10-30T00:00:00.000Z');
  while (dates.length < 254) {
    const day = new Date(d).getUTCDay();
    if (day !== 0 && day !== 6) dates.push(new Date(d).toISOString().slice(0, 10));
    d -= 86400000;
  }
  dates.reverse();
  const observations = dates.map((date, i) => {
    const slope = 0.25 + i * 0.002 + 0.12 * Math.sin(i * 0.17) + 0.03 * Math.cos(i * 0.29);
    return { ...evidence('US_TREASURY_PAR_YIELD_CURVE', `YIELD-${date}`, `${date}T18:00:00.000Z`, 'https://home.treasury.gov/treasury-daily-interest-rate-xml-feed'),
      date, two_year_pct: 3.4, ten_year_pct: 3.4 + slope, unit: 'percentage_point', snapshot_id: 'TREASURY-SNAPSHOT-2026-10-30' };
  });
  return { evaluation_at: EVAL, observations, expected_session_dates: dates, coverage_complete: true,
    snapshot_id: 'TREASURY-SNAPSHOT-2026-10-30', vintage_mode: 'current_latest_snapshot' };
}

export function fe28CreditFixture() {
  const latest = qindex('2026-Q2');
  const quarters = Array.from({ length: 43 }, (_, i) => {
    const q = quarterString(latest - 42 + i), creditStock = 21000 + i * 270 + 55 * Math.sin(i * 0.31) + 20 * Math.cos(i * 0.13);
    const gdpSaar = 19000 + i * 240 + 40 * Math.sin(i * 0.18);
    return { quarter: q, credit_stock: creditStock, gdp_saar: gdpSaar, currency: 'USD',
      credit_source_id: 'BIS:F2.3', gdp_source_id: 'BEA:GDP', measure: 'private_nonfinancial_credit',
      credit_unit: 'local_currency_billions', gdp_unit: 'local_currency_billions_SAAR',
      credit_snapshot_id: 'BIS-CURRENT-REVISED-2026-09', gdp_snapshot_id: 'BEA-CURRENT-REVISED-2026-09',
      credit_record_id: `BIS-${q}`, gdp_record_id: `GDP-${q}`,
      credit_source_sha256: hash(`BIS|${q}`), gdp_source_sha256: hash(`GDP|${q}`),
      credit_available_at: '2026-09-14T12:00:00.000Z', gdp_available_at: '2026-09-25T12:00:00.000Z',
      credit_received_at: EVAL, gdp_received_at: EVAL };
  });
  return { evaluation_at: EVAL, quarters, credit_snapshot_id: 'BIS-CURRENT-REVISED-2026-09',
    gdp_snapshot_id: 'BEA-CURRENT-REVISED-2026-09', vintage_mode: 'current_latest_snapshot' };
}

export function fe29CotFixture() {
  const currentAsOf = Date.parse('2026-10-27T00:00:00.000Z');
  const reports = Array.from({ length: 157 }, (_, i) => {
    const asOf = iso(currentAsOf - (156 - i) * 7 * 86400000).slice(0, 10), available = iso(Date.parse(asOf + 'T00:00:00.000Z') + 3 * 86400000 + 19 * 3600000 + 30 * 60000);
    return { ...evidence('CFTC:COT:DCOT_FUTURES_ONLY', `COT-${asOf}`, available, 'https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm'),
      report_as_of_date: asOf, market_key: 'NYMEX:CL', report_type: 'disaggregated_futures_only', category: 'managed_money',
      managed_money_long: 300000 + i * 110 + 2000 * Math.sin(i * 0.19),
      managed_money_short: 230000 + i * 30 + 1400 * Math.cos(i * 0.15), open_interest: 1500000 + 12000 * Math.sin(i * 0.07) };
  });
  return { evaluation_at: EVAL, contract_key: 'NYMEX:CL', reports };
}

export function fe29InventoryFixture() {
  const weeks = ['2021-10-29', '2022-10-28', '2023-10-27', '2024-10-25', '2025-10-24'];
  const values = [420000, 430000, 410000, 440000, 425000];
  const observations = weeks.map((week, i) => ({
    ...evidence('EIA:WPSR:WCESTUS1', `EIA-${week}`, iso(Date.parse(`${week}T00:00:00.000Z`) + 5 * 86400000).slice(0, 10) + 'T14:30:00.000Z', 'https://www.eia.gov/petroleum/supply/weekly/'),
    series_id: 'WCESTUS1', week_ending: week, unit: 'thousand_barrels', value: values[i],
  }));
  observations.push({ ...evidence('EIA:WPSR:WCESTUS1', 'EIA-2026-10-23', '2026-10-28T14:30:00.000Z', 'https://www.eia.gov/petroleum/supply/weekly/'),
    series_id: 'WCESTUS1', week_ending: '2026-10-23', unit: 'thousand_barrels', value: 445000 });
  return { evaluation_at: EVAL, observations };
}

export function fe29FuturesFixture() {
  const sessionDates = [];
  let day = Date.parse('2026-10-30T00:00:00.000Z');
  while (sessionDates.length < 253) {
    const weekday = new Date(day).getUTCDay();
    if (weekday !== 0 && weekday !== 6) sessionDates.push(new Date(day).toISOString().slice(0, 10));
    day -= 86400000;
  }
  sessionDates.reverse();
  const observations = sessionDates.map((date, i) => {
    const frontExpiry = new Date(Date.parse(date + 'T00:00:00Z') + 30 * 86400000).toISOString().slice(0, 10);
    const nextExpiry = new Date(Date.parse(date + 'T00:00:00Z') + 60 * 86400000).toISOString().slice(0, 10);
    const annualizedSlope = 1.2 + 0.4 * Math.sin(i * 0.07) + 0.15 * Math.cos(i * 0.31);
    const front = 80 + 0.2 * Math.sin(i * 0.11), next = front / Math.exp(annualizedSlope * ((Date.parse(nextExpiry) - Date.parse(frontExpiry)) / 86400000) / 36500);
    return { ...evidence('NYMEX:OFFICIAL_SETTLEMENT', `CL-CURVE-${date}`, `${date}T19:00:00.000Z`, 'https://www.cmegroup.com/market-data/browse-data/delayed-quotes.html'),
      data_kind: 'official_exchange_settlement', session_date: date, exchange: 'NYMEX', root: 'CL',
      quote_currency: 'USD', price_unit: 'USD_per_barrel', front_contract: `CL-FRONT-${i}`, next_contract: `CL-NEXT-${i}`,
      front_expiry: frontExpiry, next_expiry: nextExpiry, front_settlement: front, next_settlement: next };
  });
  return { evaluation_at: EVAL, observations, expected_session_dates: sessionDates, coverage_complete: true };
}

export function fe30FundingFixture() {
  const end = Date.parse('2026-11-01T11:00:00.000Z');
  const funding_history = Array.from({ length: 721 }, (_, i) => {
    const observed_at = iso(end - (720 - i) * 3600000), interest_1h = 0.000002 * Math.sin(i * 0.041) + i * 1e-9;
    return { ...evidence('DERIBIT:PUBLIC_MARKET_DATA', `FUNDING-${i}`, observed_at, 'https://docs.deribit.com/api-reference/market-data/public-get_funding_rate_history'),
      instrument: 'BTC-PERPETUAL', observed_at, interest_1h, unit: 'fraction_per_hour' };
  });
  return { venue: 'Deribit', instrument: 'BTC-PERPETUAL', contract_type: 'inverse_perpetual', oi_unit: 'USD', funding_history };
}

export function fe30OiFixture() {
  const end = Date.parse('2026-11-01T11:00:00.000Z');
  const oi_snapshots = Array.from({ length: 170 }, (_, i) => {
    const observed_at = iso(end - (169 - i) * 3600000), open_interest = 500000000 + i * 180000 + 2e6 * Math.sin(i * 0.13) + 1e6 * Math.cos(i * 0.031);
    return { ...evidence('DERIBIT:PUBLIC_MARKET_DATA', `OI-${i}`, observed_at, 'https://docs.deribit.com/api-reference/market-data/public-get_order_book'),
      instrument: 'BTC-PERPETUAL', observed_at, open_interest, unit: 'USD' };
  });
  return { venue: 'Deribit', instrument: 'BTC-PERPETUAL', contract_type: 'inverse_perpetual', oi_unit: 'USD', oi_snapshots };
}

export function fe30DepthFixture() {
  const end = Date.parse('2026-11-01T11:55:00.000Z');
  const book_snapshots = Array.from({ length: 289 }, (_, i) => {
    const observed_at = iso(end - (288 - i) * 300000);
    let depth = 2500 + 320 * Math.sin(i * 0.17) + 110 * Math.cos(i * 0.37);
    if (i === 288) depth = 1000;
    return { ...evidence('DERIBIT:PUBLIC_MARKET_DATA', `BOOK-${i}`, observed_at, 'https://docs.deribit.com/api-reference/market-data/public-get_order_book'),
      instrument: 'BTC-PERPETUAL', observed_at, amount_unit: 'USD',
      bids: [[999, depth / 2], [990, 100000]], asks: [[1001, depth / 2], [1010, 100000]] };
  });
  return { venue: 'Deribit', instrument: 'BTC-PERPETUAL', contract_type: 'inverse_perpetual', oi_unit: 'USD',
    depth_amount_unit: 'USD', book_snapshots };
}

export function fe30OnchainFixture() {
  const end = Date.parse('2026-11-01T11:00:00.000Z');
  const observations = Array.from({ length: 31 }, (_, i) => {
    const observed_at = iso(end - (30 - i) * 86400000), net_flow = 4 * Math.sin(i * 0.23) + 0.1 * i;
    const available_at = iso(Date.parse(observed_at) + 1800000);
    return { ...evidence('SYNTHETIC:LABELED_FLOW', `FLOW-${i}`, available_at), observed_at,
      label_origin: 'publisher_labeled_entity_flow', publisher_label_version: 'fixture-label-v1',
      label_method: 'fixture-labeled; not live entity labeling', asset: 'BTC', network: 'Bitcoin', custody_scope: 'fixture exchange wallets',
      unit: 'native_asset', net_flow, sign_convention: 'positive_is_net_inflow' };
  });
  return { observations, rights_attestation: 'documented_for_internal_research' };
}
