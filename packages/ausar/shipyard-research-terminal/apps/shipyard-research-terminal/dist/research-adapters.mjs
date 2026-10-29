import {
  EVIDENCE_CONTRACT_VERSION,
  SOURCE_REGISTRY_VERSION,
  SOURCE_REGISTRY,
  stableObservationId,
  sha256Hex,
  validateObservation,
  validateFeatureRecord,
  assessFeatureLineage,
} from './evidence-contract.mjs';

export const RESEARCH_ADAPTER_VERSION = '1.1.0';
export const ALPACA_DAILY_SOURCE_ID = 'alpaca.iex.daily-bars';
const SOURCE = SOURCE_REGISTRY.find((item) => item.sourceId === ALPACA_DAILY_SOURCE_ID);
// Used only when Alpaca's IEX market calendar is unavailable. NYSE publishes
// scheduled holidays and early closes through 2028; later dates use a weekday fallback.
const NYSE_CLOSED_DATES = new Set([
  '2026-01-01', '2026-01-19', '2026-02-16', '2026-04-03', '2026-05-25',
  '2026-06-19', '2026-07-03', '2026-09-07', '2026-11-26', '2026-12-25',
  '2027-01-01', '2027-01-18', '2027-02-15', '2027-03-26', '2027-05-31',
  '2027-06-18', '2027-07-05', '2027-09-06', '2027-11-25', '2027-12-24',
  '2028-01-17', '2028-02-21', '2028-04-14', '2028-05-29', '2028-06-19',
  '2028-07-04', '2028-09-04', '2028-11-23', '2028-12-25',
]);
const NYSE_EARLY_CLOSES = new Set([
  '2026-11-27', '2026-12-24',
  '2027-11-26',
  '2028-07-03', '2028-11-24',
]);

if (!SOURCE || SOURCE.rightsStatus !== 'entitlement_unverified') {
  throw new Error('The Alpaca evidence adapter requires its reviewed read-only source registry entry.');
}

function validTimestamp(value) {
  return typeof value === 'string'
    && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)
    && Number.isFinite(Date.parse(value));
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function newYorkClockParts(value) {
  const date = value instanceof Date ? value : new Date(value);
  if (!Number.isFinite(date.getTime())) return null;
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date);
  const clock = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return {
    date: `${clock.year}-${clock.month}-${clock.day}`,
    weekday: clock.weekday,
    minuteOfDay: Number(clock.hour) * 60 + Number(clock.minute),
  };
}

export function calendarAgeDaysInNewYork(asOf, now = new Date()) {
  if (typeof asOf !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(asOf)) return null;
  const asOfMs = Date.parse(`${asOf}T00:00:00.000Z`);
  if (!Number.isFinite(asOfMs) || new Date(asOfMs).toISOString().slice(0, 10) !== asOf) return null;
  const localDate = newYorkClockParts(now)?.date;
  if (!localDate) return null;
  const [year, month, day] = localDate.split('-').map(Number);
  const localMidnightMs = Date.UTC(year, month - 1, day);
  return Number.isFinite(localMidnightMs) ? Math.floor((localMidnightMs - asOfMs) / 86400000) : null;
}

function nyseSessionFor(date, weekday) {
  const inPublishedCalendar = /^202[6-8]-/.test(date);
  if (!['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].includes(weekday)) {
    return { tradingDay: false, closeMinute: null, calendar: 'nyse_reference' };
  }
  if (NYSE_CLOSED_DATES.has(date)) {
    return { tradingDay: false, closeMinute: null, calendar: 'nyse_reference' };
  }
  return {
    tradingDay: true,
    closeMinute: NYSE_EARLY_CLOSES.has(date) ? 13 * 60 : 16 * 60,
    calendar: inPublishedCalendar ? 'nyse_reference_2026_2028' : 'weekday_fallback',
  };
}

function alpacaIexSessionFor(date, calendar) {
  if (calendar?.market !== 'IEX' || calendar.date !== date) return null;
  if (calendar.status === 'closed') return { tradingDay: false, closeMinute: null, closeAtMs: null, calendar: 'alpaca_iex' };
  if (calendar.status !== 'open') return null;
  const closeAtMs = Date.parse(calendar.core_end || '');
  if (!Number.isFinite(closeAtMs)) return null;
  const closeClock = newYorkClockParts(new Date(closeAtMs));
  if (!closeClock) return null;
  return { tradingDay: true, closeMinute: closeClock.minuteOfDay, closeAtMs, calendar: 'alpaca_iex' };
}

export function selectCompletedDailyBars(rows, now = new Date(), providerCalendar = null) {
  const bars = Array.isArray(rows) ? rows : [];
  const latest = bars.at(-1);
  const nowEt = newYorkClockParts(now);
  const latestEt = latest ? newYorkClockParts(latest.at) : null;
  const sameDateBar = Boolean(nowEt?.date && nowEt.date === latestEt?.date);
  const session = nowEt
    ? alpacaIexSessionFor(nowEt.date, providerCalendar) || nyseSessionFor(nowEt.date, nowEt.weekday)
    : null;
  const nonTradingDateBarExcluded = Boolean(sameDateBar && session && !session.tradingDay);
  const currentSessionBarExcluded = Boolean(
    sameDateBar && session?.tradingDay && (
      session.closeAtMs !== null && session.closeAtMs !== undefined
        ? new Date(now).getTime() < session.closeAtMs + 15 * 60 * 1000
        : nowEt.minuteOfDay < session.closeMinute + 15
    ),
  );
  const latestDateBarExcluded = nonTradingDateBarExcluded || currentSessionBarExcluded;
  const calculationBars = latestDateBarExcluded ? bars.slice(0, -1) : bars;
  const closeTime = session?.closeMinute === null || session?.closeMinute === undefined
    ? null
    : `${String(Math.floor(session.closeMinute / 60)).padStart(2, '0')}:${String(session.closeMinute % 60).padStart(2, '0')}`;
  const cutoffTime = session?.closeMinute === null || session?.closeMinute === undefined
    ? null
    : `${String(Math.floor((session.closeMinute + 15) / 60)).padStart(2, '0')}:${String((session.closeMinute + 15) % 60).padStart(2, '0')}`;
  return {
    bars: calculationBars,
    currentSessionBarExcluded,
    nonTradingDateBarExcluded,
    latestDateBarExcluded,
    latestReturnedBarAsOf: latest?.at || null,
    calculationAsOfTime: calculationBars.at(-1)?.at || null,
    scheduledCloseEt: closeTime,
    calculationCutoffEt: cutoffTime,
    sessionCalendar: session?.calendar || 'not_needed',
    cutoffRule: session?.calendar === 'alpaca_iex'
      ? 'Exclude today’s bar until 15 minutes after Alpaca’s IEX core close; exclude a same-day bar when IEX reports no session.'
      : 'Fallback: use the published NYSE schedule through 2028, then a 16:15 ET weekday cutoff; exclude weekends and listed NYSE holidays.',
  };
}

function normalizeBars(rows, receivedAt) {
  const receivedMs = Date.parse(receivedAt);
  const cutoffMs = Math.min(receivedMs, Date.now());
  const accepted = [];
  let rejectedCount = 0;
  let duplicateCount = 0;
  let futureDatedCount = 0;
  const seen = new Set();

  for (const row of Array.isArray(rows) ? rows.slice(0, 500) : []) {
    const parsedAt = typeof row?.at === 'string' ? Date.parse(row.at) : NaN;
    const at = Number.isFinite(parsedAt) ? new Date(parsedAt).toISOString() : null;
    const values = [row?.open, row?.high, row?.low, row?.close, row?.volume];
    if (!at || !values.every((value) => typeof value === 'number' && Number.isFinite(value))
      || row.low <= 0 || row.volume < 0 || row.high < Math.max(row.open, row.close, row.low)
      || row.low > Math.min(row.open, row.close, row.high)) {
      rejectedCount += 1;
      continue;
    }
    if (Date.parse(at) > cutoffMs + 1000) {
      futureDatedCount += 1;
      continue;
    }
    if (seen.has(at)) {
      duplicateCount += 1;
      continue;
    }
    seen.add(at);
    accepted.push({
      at,
      open: row.open,
      high: row.high,
      low: row.low,
      close: row.close,
      volume: row.volume,
      trades: Number.isSafeInteger(row.trades) && row.trades >= 0 ? row.trades : null,
      vwap: typeof row.vwap === 'number' && Number.isFinite(row.vwap) ? row.vwap : null,
    });
  }
  accepted.sort((left, right) => left.at.localeCompare(right.at));
  return { bars: accepted, rejectedCount, duplicateCount, futureDatedCount };
}

function arithmeticMean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

export function simpleMovingAverage(values, period) {
  if (values.length < period) return null;
  return arithmeticMean(values.slice(-period));
}

export function simpleRsi14(closes) {
  if (closes.length < 15) return null;
  const tail = closes.slice(-15);
  const changes = tail.slice(1).map((close, index) => close - tail[index]);
  const gains = changes.map((value) => Math.max(0, value));
  const losses = changes.map((value) => Math.max(0, -value));
  const averageGain = arithmeticMean(gains);
  const averageLoss = arithmeticMean(losses);
  if (averageGain === 0 && averageLoss === 0) return 50;
  if (averageLoss === 0) return 100;
  return 100 - (100 / (1 + averageGain / averageLoss));
}

export function simpleAtr14(bars) {
  if (bars.length < 15) return null;
  const tail = bars.slice(-15);
  const ranges = tail.slice(1).map((bar, index) => Math.max(
    bar.high - bar.low,
    Math.abs(bar.high - tail[index].close),
    Math.abs(bar.low - tail[index].close),
  ));
  return arithmeticMean(ranges);
}

function trendRelation(lastClose, sma20, sma50) {
  if (![lastClose, sma20, sma50].every(Number.isFinite)) return 'unknown';
  if (lastClose > sma20 && sma20 > sma50) return 'close_above_sma20_above_sma50';
  if (lastClose < sma20 && sma20 < sma50) return 'close_below_sma20_below_sma50';
  return 'mixed_moving_average_state';
}

const METHOD_IMPLEMENTATION = [
  arithmeticMean,
  simpleMovingAverage,
  simpleRsi14,
  simpleAtr14,
  trendRelation,
].map((method) => method.toString()).join('\n');

async function makeFeature({ symbol, bars, observations, label, methodId, methodVersion, value, unit, parameters, lookback }) {
  const computedAt = new Date().toISOString();
  const parents = observations.slice(-lookback);
  if (!parents.length) return null;
  const method = {
    methodId,
    version: methodVersion,
    methodRef: 'dist/research-adapters.mjs#market-indicators',
    implementationSha256: await sha256Hex(METHOD_IMPLEMENTATION),
    parametersSha256: await sha256Hex(canonicalJson(parameters)),
  };
  const featureId = `feature_${await sha256Hex(`${ALPACA_DAILY_SOURCE_ID}\0${symbol}\0${bars.at(-1).at}\0${methodId}\0${canonicalJson(parameters)}`)}`;
  const record = {
    featureId,
    value,
    unit,
    method,
    parentObservationIds: parents.map((item) => item.observationId),
    sourceFamilyIds: ['alpaca-market-data-iex-daily'],
    asOfTime: bars.at(-1).at,
    computedAt,
    evidenceStatus: 'reproduced',
    coverageStatus: 'unknown',
    resultSha256: await sha256Hex(canonicalJson(value)),
  };
  const validation = validateFeatureRecord(record);
  if (!validation.valid) throw new Error(`Feature ${methodId} failed evidence validation: ${validation.issues.map((item) => item.path).join(', ')}`);
  const lineageEligibility = assessFeatureLineage(record, observations, { purpose: 'paper_research' });
  return { label, record, parameters, validation, lineageEligibility };
}

export async function buildAlpacaResearchEvidence({ symbol, bars, receivedAt, requestedDays, context, sessionCalendar = null } = {}) {
  const normalizedSymbol = typeof symbol === 'string' ? symbol.trim().toUpperCase() : '';
  if (!/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(normalizedSymbol)) throw new TypeError('A valid equity symbol is required.');
  if (!validTimestamp(receivedAt)) throw new TypeError('The source receipt timestamp must include a timezone.');
  if (![20, 60, 90, 180].includes(Number(requestedDays))) throw new TypeError('Requested history must be one of the supported ranges.');

  const normalized = normalizeBars(bars, receivedAt);
  if (!normalized.bars.length) throw new Error('No valid Alpaca daily bars were available to adapt.');
  const capture = {
    schema: 'SHIPYARD_ALPACA_BARS_V1',
    sourceId: ALPACA_DAILY_SOURCE_ID,
    sourceVersion: 'SHIPYARD_ALPACA_BARS_V1',
    feed: 'iex',
    timeframe: '1Day',
    adjustment: 'split',
    symbol: normalizedSymbol,
    requestedDays: Number(requestedDays),
    receivedAt,
    sessionCalendar,
    bars: normalized.bars,
  };
  const captureSha256 = await sha256Hex(canonicalJson(capture));
  const captureId = `capture_${captureSha256.slice(0, 32)}`;
  const observations = [];

  for (const bar of normalized.bars) {
    const observation = {
      observationId: await stableObservationId({
        sourceId: ALPACA_DAILY_SOURCE_ID,
        sourceKey: `${normalizedSymbol}|${bar.at}|1Day|split|iex`,
      }),
      entity: { kind: 'equity', id: `US_EQUITY:${normalizedSymbol}`, symbol: normalizedSymbol, venue: null, currency: 'USD', contract: null },
      measure: {
        key: 'daily_ohlcv',
        value: { open: bar.open, high: bar.high, low: bar.low, close: bar.close, volume: bar.volume, trades: bar.trades, vwap: bar.vwap },
        unit: 'USD_PER_SHARE_AND_SHARES',
        adjustment: 'split_adjusted',
      },
      clocks: {
        eventAt: bar.at,
        publishedAt: null,
        availableAt: null,
        availabilityEvidence: 'unknown',
        availabilityEvidenceRef: null,
        ingestedAt: receivedAt,
        decisionAt: null,
        missingReasons: {
          publishedAt: 'The Site response does not include a source publication timestamp.',
          availableAt: 'Historical availability by a past decision time is not independently verified.',
          decisionAt: 'This is an informational research snapshot, not a recorded trade decision.',
        },
      },
      state: 'observed',
      stateReason: null,
      source: {
        sourceId: ALPACA_DAILY_SOURCE_ID,
        sourceVersion: 'SHIPYARD_ALPACA_BARS_V1',
        uri: 'https://data.alpaca.markets/v2/stocks/bars',
        artifactSha256: captureSha256,
        captureId,
      },
      rights: {
        status: SOURCE.rightsStatus,
        evidenceRef: null,
        entitlementId: null,
        allowedPurposes: [...SOURCE.allowedPurposes],
        redistribution: SOURCE.redistribution,
        retentionUntil: null,
      },
      coverage: { status: 'not_applicable', observedCount: 1, expectedCount: 1, missingReasons: [] },
      revision: { number: 1, supersedesObservationId: null },
    };
    const validation = validateObservation(observation);
    if (!validation.valid) throw new Error(`Bar observation failed evidence validation: ${validation.issues.map((item) => item.path).join(', ')}`);
    observations.push(observation);
  }

  const selection = selectCompletedDailyBars(normalized.bars, receivedAt, sessionCalendar);
  const analysisBars = selection.bars;
  const analysisTimestamps = new Set(analysisBars.map((bar) => bar.at));
  const analysisObservations = observations.filter((observation) => analysisTimestamps.has(observation.clocks.eventAt));
  const closes = analysisBars.map((bar) => bar.close);
  const sma20 = simpleMovingAverage(closes, 20);
  const sma50 = simpleMovingAverage(closes, 50);
  const dailyReturnPct = analysisBars.length > 1
    ? (analysisBars.at(-1).close / analysisBars.at(-2).close - 1) * 100
    : null;
  const rsi14 = simpleRsi14(closes);
  const atr14 = simpleAtr14(analysisBars);
  const featureInputs = [
    dailyReturnPct === null ? null : { label: 'Daily return', methodId: 'shipyard.daily-return-percent', methodVersion: '1.0.0', value: dailyReturnPct, unit: 'percent', lookback: 2, parameters: { formula: '(latest_close / previous_close - 1) * 100', bars: 2 } },
    sma20 === null ? null : { label: 'SMA20', methodId: 'shipyard.sma', methodVersion: '1.0.0', value: sma20, unit: 'USD_PER_SHARE', lookback: 20, parameters: { period: 20, source: 'close', formula: 'simple_arithmetic_mean' } },
    sma50 === null ? null : { label: 'SMA50', methodId: 'shipyard.sma', methodVersion: '1.0.0', value: sma50, unit: 'USD_PER_SHARE', lookback: 50, parameters: { period: 50, source: 'close', formula: 'simple_arithmetic_mean' } },
    rsi14 === null ? null : { label: 'RSI14', methodId: 'shipyard.rsi14.simple-average', methodVersion: '1.0.0', value: rsi14, unit: 'index_0_to_100', lookback: 15, parameters: { period: 14, gainLossAverage: 'simple_arithmetic_mean', flatSeriesValue: 50 } },
    atr14 === null ? null : { label: 'ATR14', methodId: 'shipyard.atr14.simple-average', methodVersion: '1.0.0', value: atr14, unit: 'USD_PER_SHARE', lookback: 15, parameters: { period: 14, trueRange: 'max(high-low,abs(high-prior-close),abs(low-prior-close))', smoothing: 'simple_arithmetic_mean' } },
    atr14 === null || !analysisBars.at(-1)?.close ? null : { label: 'ATR14 / close', methodId: 'shipyard.atr14-percent', methodVersion: '1.0.0', value: atr14 / analysisBars.at(-1).close * 100, unit: 'percent', lookback: 15, parameters: { period: 14, formula: 'simple_atr14 / latest_close * 100' } },
    sma20 === null || sma50 === null ? null : { label: 'Trend structure', methodId: 'shipyard.moving-average-structure', methodVersion: '1.0.0', value: trendRelation(analysisBars.at(-1).close, sma20, sma50), unit: 'categorical_state', lookback: 50, parameters: { averages: [20, 50], comparisons: 'strict_close_sma_ordering' } },
  ].filter(Boolean);
  const features = [];
  for (const item of featureInputs) {
    features.push(await makeFeature({ symbol: normalizedSymbol, bars: analysisBars, observations: analysisObservations, ...item }));
  }

  const allObservationValidationPassed = observations.every((observation) => validateObservation(observation).valid);
  const featureValidationFailures = features.filter((feature) => !feature.validation.valid).length;
  const contextValue = context && typeof context === 'object' ? context : null;
  const now = new Date();
  return {
    schema: 'SHIPYARD_RESEARCH_EVIDENCE_BUNDLE_V1',
    createdAt: new Date().toISOString(),
    evidenceContractVersion: EVIDENCE_CONTRACT_VERSION,
    sourceRegistryVersion: SOURCE_REGISTRY_VERSION,
    adapterVersion: RESEARCH_ADAPTER_VERSION,
    purpose: 'local_analysis',
    storage: 'browser_memory_until_download; no server persistence or upload',
    sourceCapture: {
      sourceId: ALPACA_DAILY_SOURCE_ID,
      sourceVersion: 'SHIPYARD_ALPACA_BARS_V1',
      uri: 'https://data.alpaca.markets/v2/stocks/bars',
      feed: 'iex',
      timeframe: '1Day',
      adjustment: 'split',
      symbol: normalizedSymbol,
      requestedDays: Number(requestedDays),
      receivedAt,
      asOfTime: normalized.bars.at(-1).at,
      sessionCalendar,
      latestReturnedBarAsOf: selection.latestReturnedBarAsOf,
      captureId,
      captureSha256,
      captureHashDescription: 'SHA-256 of the normalized response fields consumed by this browser adapter; not a provider-signed artifact.',
      completeness: sessionCalendar?.market === 'IEX' && ['open', 'closed'].includes(sessionCalendar.status)
        ? 'current_session_calendar_verified; historical_coverage_unknown'
        : 'unknown_session_calendar',
    },
    contextReference: contextValue ? {
      sourceId: 'chartlector.public-eod-context',
      uri: contextValue.source_url || null,
      asOf: contextValue.as_of || null,
      receivedAt: contextValue.received_at || null,
      ageCalendarDays: calendarAgeDaysInNewYork(contextValue?.as_of, now),
      includedValues: false,
      note: 'Reference only. Context values are not copied into this bundle; publication rights and point-in-time availability have not been independently verified.',
    } : { status: 'not_loaded' },
    quality: {
      inputBarCount: Array.isArray(bars) ? bars.length : 0,
      acceptedBarCount: normalized.bars.length,
      rejectedBarCount: normalized.rejectedCount,
      duplicateBarCount: normalized.duplicateCount,
      futureDatedBarCount: normalized.futureDatedCount,
      expectedSessionCount: null,
      coverageStatus: 'unknown',
      allObservationRecordsValid: allObservationValidationPassed,
      featureValidationFailures,
      decisionEligibleFeatureCount: features.filter((feature) => feature.lineageEligibility.eligible).length,
    },
    analysis: {
      barsUsedCount: analysisBars.length,
      calculationAsOfTime: selection.calculationAsOfTime,
      currentSessionBarExcluded: selection.currentSessionBarExcluded,
      nonTradingDateBarExcluded: selection.nonTradingDateBarExcluded,
      latestDateBarExcluded: selection.latestDateBarExcluded,
      scheduledCloseEt: selection.scheduledCloseEt,
      calculationCutoffEt: selection.calculationCutoffEt,
      sessionCalendar: selection.sessionCalendar,
      cutoffRule: selection.cutoffRule,
    },
    limitations: [
      'The Site Worker exposes read-only IEX market bars. This adapter does not access account, position, or order endpoints.',
      'The adapter validates records and indicator lineage; it does not verify historical point-in-time availability or provider display/redistribution entitlement.',
      'The current-session cutoff uses Alpaca’s IEX calendar when available. If unavailable, it falls back to the published NYSE schedule through 2028 and a 16:15 ET weekday cutoff.',
      'RSI14 and ATR14 use simple arithmetic averaging as named in each method record; they are not Wilder-smoothed indicators.',
      'Historical session coverage and point-in-time availability are not verified by the current-date calendar lookup.',
      'No feature is a recommendation, probability estimate, calibrated signal, performance claim, or trading instruction.',
    ],
    observations,
    features,
  };
}

