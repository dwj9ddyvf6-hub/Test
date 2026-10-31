// Public research adapters for official market/disclosure sources.
// All requests are bounded, read-only, source-dated, and return provider errors without payloads.
const FINRA_WEEKLY_CACHE = new Map();
const FINRA_PARTITION_CACHE = new Map();
const FINRA_WEEKLY_RATE = new Map();
const FINRA_WEEKLY_POLICY = Object.freeze({
  max_response_bytes: 768 * 1024,
  max_rows: 500,
  max_partitions: 5000,
  cache_ms: 300000,
  partition_cache_ms: 300000,
});

function finraDate(value) {
  return typeof value === 'string' && /^20\d{2}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value + 'T00:00:00Z'))
    && new Date(value + 'T00:00:00Z').toISOString().slice(0, 10) === value;
}
function finraMonday(value) {
  return finraDate(value) && new Date(value + 'T00:00:00Z').getUTCDay() === 1;
}
function finraCount(target, key) { target[key] = (target[key] || 0) + 1; }
function finraSymbol(value) { return typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$/.test(value); }
function finraProviderTier(tier) { return tier === 'OTC' ? 'OTCE' : tier; }
function finraRateAllowed(request, now) {
  const key = request.headers.get('cf-connecting-ip') || 'anonymous';
  const previous = FINRA_WEEKLY_RATE.get(key);
  const window = !previous || now < previous.started || now - previous.started >= 60000 ? { started: now, count: 0 } : previous;
  window.count += 1;
  FINRA_WEEKLY_RATE.set(key, window);
  while (FINRA_WEEKLY_RATE.size > 128) FINRA_WEEKLY_RATE.delete(FINRA_WEEKLY_RATE.keys().next().value);
  return window.count <= 6;
}
async function finraAvailableWeeks(request, tier, now) {
  const providerTier = finraProviderTier(tier), cached = FINRA_PARTITION_CACHE.get(providerTier);
  if (cached && now < cached.until) return cached.value;
  const response = await fetch('https://api.finra.org/partitions/group/otcMarket/name/weeklySummary', {
    method: 'GET',
    headers: { accept: 'application/json', 'data-api-version': '1' },
    redirect: 'manual',
    signal: AbortSignal.any([request.signal, AbortSignal.timeout(8000)]),
  });
  if (response.status >= 300 && response.status < 400) throw new Error('partition_redirect_rejected');
  if (!response.ok) throw new Error(response.status === 429 ? 'provider_rate_limited' : 'partition_provider_unavailable');
  const text = await readBoundedBody(response, FINRA_WEEKLY_POLICY.max_response_bytes);
  let payload;
  try { payload = JSON.parse(text); } catch { throw new Error('invalid_partition_payload'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
      || String(payload.datasetGroup).toLowerCase() !== 'otcmarket'
      || String(payload.datasetName).toLowerCase() !== 'weeklysummary'
      || !Array.isArray(payload.availablePartitions)
      || payload.availablePartitions.length > FINRA_WEEKLY_POLICY.max_partitions) {
    throw new Error('invalid_partition_payload');
  }
  const weeks = new Set();
  for (const entry of payload.availablePartitions) {
    const pair = entry?.partitions;
    if (!Array.isArray(pair) || pair.length !== 2 || !finraMonday(pair[0])
        || typeof pair[1] !== 'string' || !/^[A-Z][A-Z0-9]{0,7}$/.test(pair[1])) {
      throw new Error('invalid_partition_payload');
    }
    if (pair[1] === providerTier) weeks.add(pair[0]);
  }
  const value = { weeks: [...weeks].sort((a, b) => b.localeCompare(a)), received_at: new Date().toISOString() };
  if (FINRA_PARTITION_CACHE.size > 16) FINRA_PARTITION_CACHE.clear();
  FINRA_PARTITION_CACHE.set(providerTier, { value, until: now + FINRA_WEEKLY_POLICY.partition_cache_ms });
  return value;
}
function finraWeekRow(raw, symbol, week, tier, providerTier) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) || raw.issueSymbolIdentifier !== symbol
      || !finraMonday(raw.weekStartDate) || raw.weekStartDate !== week || raw.tierIdentifier !== providerTier) {
    return { kind: 'rejected' };
  }
  const code = raw.summaryTypeCode;
  if (['ATS_W_SMBL', 'OTC_W_SMBL'].includes(code)) return { kind: 'excluded_aggregate' };
  if (!['ATS_W_SMBL_FIRM', 'OTC_W_SMBL_FIRM'].includes(code)) return { kind: 'rejected' };
  const shares = finite(raw.totalWeeklyShareQuantity), trades = whole(raw.totalWeeklyTradeCount), notional = finite(raw.totalNotionalSum);
  if (shares === null || shares < 0 || trades === null || notional === null || notional < 0) return { kind: 'rejected' };
  return { kind: 'record', record: {
    symbol, week_start: week, tier, source_tier: providerTier,
    market: code === 'ATS_W_SMBL_FIRM' ? 'ATS' : 'Off-exchange non-ATS',
    participant: bounded(raw.marketParticipantName, 160),
    participant_id: bounded(raw.MPID, 16, /^[A-Za-z0-9]+$/),
    shares, trades, notional_usd: notional,
    last_reported_date: finraDate(raw.lastReportedDate) ? raw.lastReportedDate : null,
    last_updated_date: finraDate(raw.lastUpdateDate) ? raw.lastUpdateDate : null,
    initially_published_date: finraDate(raw.initialPublishedDate) ? raw.initialPublishedDate : null,
    source_record_type: code,
  } };
}
function finraResponseCoverage(response, payloadLength) {
  const rawTotal = response.headers.get('Record-Total');
  if (rawTotal === null) {
    return { known: false, total: null, complete: false, limit_reached: payloadLength >= FINRA_WEEKLY_POLICY.max_rows };
  }
  if (!/^\d{1,9}$/.test(rawTotal)) throw new Error('invalid_provider_payload');
  const total = Number(rawTotal);
  if (!Number.isSafeInteger(total) || total < payloadLength) throw new Error('invalid_provider_payload');
  return {
    known: true,
    total,
    complete: total === payloadLength,
    limit_reached: total > payloadLength || payloadLength >= FINRA_WEEKLY_POLICY.max_rows,
  };
}
async function finraWeeklySummary(request) {
  const url = new URL(request.url);
  if (url.pathname !== '/api/research/finra/weekly-ats') return null;
  const base = {
    schema: 'SHIPYARD_FINRA_WEEKLY_ATS_V1',
    status: 'unavailable',
    source: 'FINRA OTC Transparency',
    source_url: 'https://developer.finra.org/docs/api-explorer/query_api-equity-weekly_summary',
    partitions_url: 'https://api.finra.org/partitions/group/otcMarket/name/weeklySummary',
    market_data_type: 'published weekly aggregates',
    requested_at: new Date().toISOString(),
    received_at: null,
    partition_received_at: null,
    symbol: null,
    requested_week: null,
    week_start: null,
    tier: 'T1',
    source_tier: 'T1',
    available_weeks: [],
    records: [],
    coverage: {
      returned_rows: 0, rejected_rows: 0, excluded_aggregate_rows: 0,
      response_complete: false, response_completeness_known: false, response_total: null,
      limit_reached: false, provider_partition_available: null,
      intraday_prints: false, live_feed: false, records_are_aggregated: true,
    },
  };
  if (request.method !== 'GET') return json({ ...base, status: 'invalid', error: 'method_not_allowed' }, 405);
  const keys = [...url.searchParams.keys()], symbolValue = url.searchParams.get('symbol');
  const requestedWeek = url.searchParams.get('week') || 'latest', tier = url.searchParams.get('tier') || 'T1';
  if (keys.some(key => !['symbol', 'week', 'tier'].includes(key)) || new Set(keys).size !== keys.length
      || !finraSymbol(symbolValue) || !(requestedWeek === 'latest' || finraMonday(requestedWeek))
      || !['T1', 'T2', 'OTC'].includes(tier)) {
    return json({ ...base, status: 'invalid', error: 'invalid_request' }, 400);
  }
  const symbol = symbolValue.toUpperCase(), providerTier = finraProviderTier(tier), now = Date.now();
  base.symbol = symbol;
  base.requested_week = requestedWeek;
  base.tier = tier;
  base.source_tier = providerTier;
  if (!finraRateAllowed(request, now)) return json({ ...base, error: 'rate_limited', retry_after_seconds: 60 }, 429);
  try {
    const partitions = await finraAvailableWeeks(request, tier, now);
    const weeks = partitions.weeks;
    base.available_weeks = weeks.slice(0, 52);
    base.partition_received_at = partitions.received_at;
    base.coverage.provider_partition_available = null;
    const week = requestedWeek === 'latest' ? weeks[0] : requestedWeek;
    base.week_start = week || null;
    if (!week) return json({ ...base, error: 'partition_unavailable' }, 502);
    if (!weeks.includes(week)) {
      const oldest = weeks.at(-1);
      const status = oldest && week < oldest ? 'outside_provider_window' : 'not_published';
      return json({
        ...base, status, received_at: partitions.received_at, retrieved_at: partitions.received_at,
        coverage: { ...base.coverage, provider_partition_available: false },
      });
    }
    base.coverage.provider_partition_available = true;
    const cacheKey = [symbol, week, tier].join(':');
    const cached = FINRA_WEEKLY_CACHE.get(cacheKey);
    if (cached && now < cached.until) {
      return json({ ...cached.value, requested_week: requestedWeek, served_at: new Date(now).toISOString(), cache_hit: true });
    }
    const filters = [
      { compareType: 'equal', fieldName: 'weekStartDate', fieldValue: week },
      { compareType: 'equal', fieldName: 'tierIdentifier', fieldValue: providerTier },
      { compareType: 'equal', fieldName: 'issueSymbolIdentifier', fieldValue: symbol },
    ];
    const body = JSON.stringify({
      fields: ['issueSymbolIdentifier', 'weekStartDate', 'tierIdentifier', 'summaryTypeCode',
        'totalWeeklyShareQuantity', 'totalWeeklyTradeCount', 'totalNotionalSum', 'lastReportedDate',
        'lastUpdateDate', 'initialPublishedDate', 'MPID', 'marketParticipantName'],
      compareFilters: filters,
      limit: FINRA_WEEKLY_POLICY.max_rows,
      sortFields: [{ fieldName: 'totalWeeklyShareQuantity', sortType: 'desc' }],
    });
    const started = Date.now();
    const response = await fetch('https://api.finra.org/data/group/otcMarket/name/weeklySummary', {
      method: 'POST',
      headers: { 'content-type': 'application/json', accept: 'application/json', 'data-api-version': '1' },
      body,
      redirect: 'manual',
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(10000)]),
    });
    if (response.status >= 300 && response.status < 400) return json({ ...base, error: 'provider_redirect_rejected' }, 502);
    if (response.status === 204) {
      const received = new Date().toISOString();
      const value = { ...base, status: 'no_records', received_at: received, retrieved_at: received,
        response_ms: Math.max(0, Date.now() - started),
        coverage: { ...base.coverage, response_complete: true, response_completeness_known: true,
          response_total: 0 } };
      if (FINRA_WEEKLY_CACHE.size > 200) FINRA_WEEKLY_CACHE.clear();
      FINRA_WEEKLY_CACHE.set(cacheKey, { value, until: now + FINRA_WEEKLY_POLICY.cache_ms });
      return json(value);
    }
    if (!response.ok) {
      return json({ ...base, error: response.status === 429 ? 'provider_rate_limited' : 'provider_unavailable',
        provider_status: response.status }, response.status === 429 ? 429 : 502);
    }
    const text = await readBoundedBody(response, FINRA_WEEKLY_POLICY.max_response_bytes);
    let payload;
    try { payload = JSON.parse(text); } catch { return json({ ...base, error: 'invalid_provider_payload' }, 502); }
    if (!Array.isArray(payload) || payload.length > FINRA_WEEKLY_POLICY.max_rows) {
      return json({ ...base, error: 'invalid_provider_payload' }, 502);
    }
    const responseCoverage = finraResponseCoverage(response, payload.length), records = [];
    const counts = { rejected_rows: 0, excluded_aggregate_rows: 0 };
    for (const row of payload) {
      const parsed = finraWeekRow(row, symbol, week, tier, providerTier);
      if (parsed.kind === 'record') records.push(parsed.record);
      else finraCount(counts, parsed.kind === 'excluded_aggregate' ? 'excluded_aggregate_rows' : 'rejected_rows');
    }
    records.sort((a, b) => b.shares - a.shares || String(a.participant || '').localeCompare(String(b.participant || '')));
    const received = new Date().toISOString();
    const lastUpdated = records.map(row => row.last_updated_date).filter(Boolean).sort().at(-1) || null;
    const status = records.length
      ? responseCoverage.complete ? 'connected' : 'partial'
      : payload.length === 0 && responseCoverage.complete ? 'no_records'
      : payload.length > 0 && counts.rejected_rows === 0 && counts.excluded_aggregate_rows > 0 ? 'aggregate_only'
      : 'partial';
    const value = {
      ...base,
      status,
      received_at: received,
      retrieved_at: received,
      last_updated_date: lastUpdated,
      response_ms: Math.max(0, Date.now() - started),
      records,
      coverage: { ...base.coverage, returned_rows: records.length, ...counts,
        response_complete: responseCoverage.complete,
        response_completeness_known: responseCoverage.known,
        response_total: responseCoverage.total,
        limit_reached: responseCoverage.limit_reached },
    };
    if (FINRA_WEEKLY_CACHE.size > 200) FINRA_WEEKLY_CACHE.clear();
    FINRA_WEEKLY_CACHE.set(cacheKey, { value, until: now + FINRA_WEEKLY_POLICY.cache_ms });
    return json(value);
  } catch (error) {
    const code = request.signal.aborted ? 'cancelled'
      : error?.name === 'TimeoutError' ? 'source_request_timeout'
      : error?.message === 'response too large' ? 'provider_response_bound_exceeded'
      : ['partition_redirect_rejected', 'partition_provider_unavailable', 'invalid_partition_payload',
        'provider_rate_limited'].includes(error?.message) ? error.message
      : 'provider_request_failed';
    return json({ ...base, error: code }, code === 'cancelled' ? 408 : 502);
  }
}

async function connectedResearchRoute(request, env) {
  return await finraWeeklySummary(request, env);
}
