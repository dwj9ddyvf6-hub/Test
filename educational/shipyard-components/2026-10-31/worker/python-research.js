// Fixed-origin bridge to the private, research-only Python calculator.
// Provider credentials remain in the Site Worker. The calculator receives
// only bounded market observations and never connects to a market provider.
const SHIPYARD_PYTHON_SERVICE_ORIGIN = "__RESEARCH_SERVICE_ORIGIN__";
const SHIPYARD_PYTHON_SERVICE_BUILD = "educational-component-unpinned";
const SHIPYARD_PYTHON_ADAPTER_CONTRACT = "SHIPYARD_PYTHON_ADAPTER_V2";
// Alpaca allows up to 10,000 bars per page. Keep a 4,000-bar page comfortably
// below the Worker's 1 MiB response bound and permit at most 56,000 raw bars.
// The separate request-rate guard still caps one job's provider calls.
const SHIPYARD_PYTHON_MAX_PAGES = 14;
const SHIPYARD_PYTHON_PAGE_SIZE = 4000;
const SHIPYARD_PYTHON_INTRADAY_LOOKBACK_DAYS = 300;
const SHIPYARD_PYTHON_BAR_MS = 10 * 60 * 1000;

function shipyardPythonError(message, status = 503, details = {}) {
  return json({ schema: "SHIPYARD_PYTHON_RESEARCH_V1", status: "blocked", error: message,
    blockers: [String(message).toUpperCase()], ...details }, status);
}

class ShipyardPythonClosedSession extends Error {
  constructor(targetDate, previous, calendarData, phase = "non_session_date", current = null) {
    super("market_closed");
    const lastClosed = phase === "after_close" ? current : previous;
    this.session = { phase, target_session: targetDate,
      last_closed_session: lastClosed.date, last_closed_session_close: lastClosed.close,
      session_open: current?.open || null, session_close: current?.close || null,
      calendar_received_at: calendarData.received_at };
  }
}

function shipyardPythonServiceToken(env) {
  return typeof env.SHIPYARD_RESEARCH_SERVICE_TOKEN === "string"
    && env.SHIPYARD_RESEARCH_SERVICE_TOKEN.length >= 40
    ? env.SHIPYARD_RESEARCH_SERVICE_TOKEN : null;
}

function shipyardPythonSameOrigin(request) {
  try { return request.headers.get("origin") === new URL(request.url).origin; }
  catch { return false; }
}

async function shipyardPythonReadJson(request, maximum = 4096) {
  if (request.headers.get("content-type")?.split(";")[0].trim().toLowerCase() !== "application/json") throw new Error("application_json_required");
  const declared = Number(request.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > maximum) throw new Error("request_too_large");
  return JSON.parse(await readBoundedBody(request, maximum));
}

function shipyardPythonSafeError(error) {
  const value = typeof error?.message === "string" ? error.message : "";
  const known = new Set(["market_data_credentials_unavailable", "provider_page_limit_exceeded", "provider_rate_limited",
    "provider_unavailable", "provider_response_unreadable", "provider_history_bound_exceeded", "invalid_provider_payload",
    "invalid_pagination_token", "invalid_or_duplicate_provider_bars", "official_calendar_unavailable",
    "official_calendar_invalid",
    "invalid_market_data",
    "current_or_previous_session_unavailable", "preopen_reference_unavailable", "preopen_reference_time_invalid",
    "invalid_daily_reference_bars", "daily_reference_history_incomplete", "duplicate_daily_reference_date",
    "daily_reference_session_gap", "daily_reference_atr_unavailable", "invalid_official_session_duration",
    "intraday_bar_not_session_aligned", "historical_session_missing", "historical_intraday_grid_gap",
    "current_session_intraday_gap", "hour_bucket_incomplete", "warmup_incomplete", "preopen_capture_missing",
    "prior_session_reference_unavailable", "prior_session_grid_incomplete", "current_session_bars_unavailable",
    "rate_limited"]);
  return known.has(value) ? value : "research_inputs_unavailable";
}

async function shipyardPythonServiceRequest(path, token, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("accept", "application/json");
  if (token) headers.set("authorization", `Bearer ${token}`);
  const response = await fetch(`${SHIPYARD_PYTHON_SERVICE_ORIGIN}${path}`, {
    ...options, headers, redirect: "manual",
    signal: options.signal || AbortSignal.timeout(10000),
  });
  let value;
  try { value = JSON.parse(await readBoundedBody(response, 1024 * 1024)); }
  catch { throw new Error(response.ok ? "service_response_invalid" : `service_http_${response.status}`); }
  if (!response.ok) throw new Error(`service_http_${response.status}`);
  return value;
}

function shipyardPythonValidateStatus(value) {
  if (!value || value.schema !== "SHIPYARD_PYTHON_SERVICE_STATUS_V1" || value.status !== "ok"
      || value.adapter_contract !== SHIPYARD_PYTHON_ADAPTER_CONTRACT || value.build_id !== SHIPYARD_PYTHON_SERVICE_BUILD
      || value.engines?.saty !== "0.3.0" || value.engines?.rre !== "0.2.0"
      || !value.queue || ["queued", "running", "complete", "failed"].some(key => !Number.isSafeInteger(value.queue[key]) || value.queue[key] < 0)) {
    throw new Error("service_contract_mismatch");
  }
  return { build_id: value.build_id, adapter_contract: value.adapter_contract,
    engines: { saty: "0.3.0", rre: "0.2.0" },
    queue: Object.fromEntries(["queued", "running", "complete", "failed"].map(key => [key, value.queue[key]])) };
}

function shipyardPythonValidateJob(value, expected = {}) {
  if (!value || value.schema !== "SHIPYARD_PYTHON_JOB_V1" || value.adapter_contract !== SHIPYARD_PYTHON_ADAPTER_CONTRACT
      || !/^[a-f0-9]{32}$/.test(value.id) || (expected.id && value.id !== expected.id)
      || !["SPY", "QQQ"].includes(value.symbol) || (expected.symbol && value.symbol !== expected.symbol)
      || !["saty", "rre"].includes(value.engine) || (expected.engine && value.engine !== expected.engine)
      || !["queued", "running", "complete", "failed"].includes(value.status)
      || (value.build_id !== SHIPYARD_PYTHON_SERVICE_BUILD && !(!expected.submitted && value.status === "failed" && ["RESEARCH_BUILD_CHANGED", "RESEARCH_BUILD_UNKNOWN"].includes(value.error_code) && (value.build_id === null || (typeof value.build_id === "string" && value.build_id.length <= 160))))
      || !timestamp(value.created_at) || !timestamp(value.updated_at)
      || !Number.isSafeInteger(value.attempts) || value.attempts < 0) throw new Error("service_contract_mismatch");
  const output = { id: value.id, engine: value.engine, symbol: value.symbol, status: value.status, build_id: value.build_id,
    created_at: value.created_at, updated_at: value.updated_at, attempts: value.attempts };
  if (value.status === "failed") {
    output.error_code = ["RESEARCH_CALCULATION_FAILED", "RESEARCH_BUILD_CHANGED", "RESEARCH_BUILD_UNKNOWN"].includes(value.error_code)
      ? value.error_code : "RESEARCH_CALCULATION_FAILED";
  }
  if (value.status === "complete") {
    const result = value.result;
    if (!result || !["complete", "blocked"].includes(result.status) || !Array.isArray(result.blockers)
        || result.blockers.length > 128 || result.blockers.some(item => typeof item !== "string" || !/^[A-Z0-9_:/. -]{1,160}$/.test(item))
        || result.job_id !== value.id || result.build_id !== value.build_id || !timestamp(result.completed_at)
        || (result.status === "complete" && (result.blockers.length || !result.engine || !Array.isArray(result[value.engine === "saty" ? "signals" : "intents"])))
        || (result.status === "blocked" && (!result.blockers.length || result.signals?.length || result.intents?.length))) throw new Error("service_contract_mismatch");
    // Service results contain market observations only. Never spread a remote envelope,
    // error, debug/trace field, or arbitrary top-level field into a browser response.
    const allowed = ["status", "blockers", "signals", "intents", "bar_counts", "engine", "input_timestamps",
      "coverage", "event_coverage", "diagnostics", "policy_status", "job_id", "completed_at", "build_id"];
    output.result = Object.fromEntries(allowed.filter(key => Object.hasOwn(result, key)).map(key => [key, result[key]]));
    const safeAtom = item => item === null || typeof item === "boolean" || (typeof item === "number" && Number.isFinite(item))
      || (typeof item === "string" && item.length <= 512);
    const safeField = item => safeAtom(item) || (Array.isArray(item) && item.length <= 4096 && item.every(safeAtom));
    const pick = (object, keys) => object && typeof object === "object" && !Array.isArray(object)
      ? Object.fromEntries(keys.filter(key => Object.hasOwn(object, key) && safeField(object[key])).map(key => [key, object[key]])) : {};
    if (result.engine) {
      if (result.engine.version !== (value.engine === "saty" ? "0.3.0" : "0.2.0")
          || result.engine.source_commit !== SHIPYARD_PYTHON_SERVICE_BUILD.slice("silicon-".length)) throw new Error("service_contract_mismatch");
      output.result.engine = pick(result.engine, ["name", "version", "source_commit"]);
    }
    if (result.coverage) output.result.coverage = pick(result.coverage, ["status", "captured_at", "provider_received_at", "provider_page_count",
      "provider_raw_bar_count", "ten_minute_count", "session_hour_count", "current_session_5m_count", "prior_session_5m_count",
      "pagination_complete", "interval_grid_complete", "excluded_partial_session_dates", "historical_publication_availability"]);
    if (result.input_timestamps) output.result.input_timestamps = pick(result.input_timestamps,
      ["latest_bar_end", "latest_available_at", "latest_bar_available_at", "source_capture_at"]);
    if (result.event_coverage) output.result.event_coverage = pick(result.event_coverage,
      ["source", "version", "captured_at", "covered_from", "covered_until", "status", "scope_complete", "exclusions"]);
    if (result.policy_status) output.result.policy_status = pick(result.policy_status,
      ["variant", "base_variant", "session_id", "generation", "ready", "reference_id"]);
    if (result.bar_counts) output.result.bar_counts = pick(result.bar_counts, ["10m", "1H"]);
    if (result.diagnostics) output.result.diagnostics = Object.fromEntries(["events", "lane_events", "reasons"].map(group => [group,
      Object.fromEntries(Object.entries(result.diagnostics[group] || {}).filter(([key, count]) =>
        /^[A-Za-z0-9_:./ -]{1,160}$/.test(key) && Number.isSafeInteger(count) && count >= 0).slice(0, 512))]));
    if (Array.isArray(result.signals)) output.result.signals = result.signals.map(item => pick(item,
      ["signal_id", "symbol", "timeframe", "setup", "direction", "bar_end", "available_at", "expires_at", "reference_entry",
       "stop", "targets", "atr", "anchor", "reference_horizon", "risk_multiplier"]));
    if (Array.isArray(result.intents)) output.result.intents = result.intents.map(item => pick(item,
      ["source_id", "variant", "setup", "symbol", "direction", "signal_at", "available_at", "expires_at", "entry_reference",
       "trigger", "stop", "target", "atr14", "session_id", "generation", "episode_id", "session_close", "series_id",
       "calendar_version", "reference_id", "max_hold_seconds"]));
    if ([...(output.result.signals || []), ...(output.result.intents || [])].some(item => item.symbol !== value.symbol)) throw new Error("service_contract_mismatch");
    if (new TextEncoder().encode(JSON.stringify(output.result)).byteLength > 512 * 1024
        || (result.signals !== undefined && (!Array.isArray(result.signals) || result.signals.length > 12000))
        || (result.intents !== undefined && (!Array.isArray(result.intents) || result.intents.length > 12000))) throw new Error("service_contract_mismatch");
  }
  return output;
}

function shipyardPythonStrictBar(raw, timeframe, expectedStart = null) {
  const start = timestamp(raw?.t);
  const open = finite(raw?.o), high = finite(raw?.h), low = finite(raw?.l), close = finite(raw?.c), volume = finite(raw?.v);
  const duration = timeframe === "10Min" ? 600000 : timeframe === "5Min" ? 300000 : null;
  if (!start || !duration || [open, high, low, close, volume].some(value => value === null)
      || open <= 0 || high <= 0 || low <= 0 || close <= 0 || volume < 0
      || low > Math.min(open, close) || high < Math.max(open, close)
      || (expectedStart !== null && Date.parse(start) !== expectedStart)) {
    throw new Error("invalid_market_data");
  }
  return { start, end: new Date(Date.parse(start) + duration).toISOString(), open, high, low, close, volume };
}

async function shipyardPythonFetchBars(request, env, symbol, timeframe, start, end) {
  const keyId = env.ALPACA_API_KEY_ID, secret = env.ALPACA_API_SECRET_KEY;
  if (typeof keyId !== "string" || !keyId || typeof secret !== "string" || !secret) throw new Error("market_data_credentials_unavailable");
  const output = [], pageTokens = new Set();
  let pageToken = null, pages = 0;
  for (;;) {
    if (!alpacaRateAllowed(request, Date.now())) throw new Error("rate_limited");
    if (++pages > SHIPYARD_PYTHON_MAX_PAGES) throw new Error("provider_page_limit_exceeded");
    const url = new URL("https://data.alpaca.markets/v2/stocks/bars");
    for (const [key, value] of Object.entries({ symbols: symbol, timeframe, start, end,
      limit: String(SHIPYARD_PYTHON_PAGE_SIZE), adjustment: "raw", feed: "iex", sort: "asc" })) url.searchParams.set(key, value);
    if (pageToken) url.searchParams.set("page_token", pageToken);
    const response = await fetch(url, { method: "GET", headers: {
      "APCA-API-KEY-ID": keyId, "APCA-API-SECRET-KEY": secret, accept: "application/json",
    }, redirect: "manual", signal: AbortSignal.any([request.signal, AbortSignal.timeout(8000)]) });
    if (!response.ok) throw new Error(response.status === 429 ? "provider_rate_limited" : "provider_unavailable");
    let payload;
    try { payload = JSON.parse(await readBoundedBody(response, 1024 * 1024)); }
    catch { throw new Error("provider_response_unreadable"); }
    if (!payload || !payload.bars || typeof payload.bars !== "object" || Array.isArray(payload.bars)
        || Object.keys(payload.bars).some(key => key !== symbol) || !Array.isArray(payload.bars[symbol])) {
      throw new Error("invalid_provider_payload");
    }
    if (payload.bars[symbol].length > SHIPYARD_PYTHON_PAGE_SIZE
        || output.length + payload.bars[symbol].length > SHIPYARD_PYTHON_MAX_PAGES * SHIPYARD_PYTHON_PAGE_SIZE) {
      throw new Error("provider_history_bound_exceeded");
    }
    output.push(...payload.bars[symbol]);
    if (!payload.next_page_token) break;
    if (typeof payload.next_page_token !== "string" || payload.next_page_token.length > 512 || pageTokens.has(payload.next_page_token)) {
      throw new Error("invalid_pagination_token");
    }
    pageTokens.add(payload.next_page_token);
    pageToken = payload.next_page_token;
  }
  const receipt = new Date().toISOString();
  const bars = output.map(raw => shipyardPythonStrictBar(raw, timeframe));
  if (bars.some((bar, index) => Date.parse(bar.start) < Date.parse(start)
      || Date.parse(bar.start) >= Date.parse(end)
      || (index > 0 && Date.parse(bar.start) <= Date.parse(bars[index - 1].start)))) {
    throw new Error("invalid_or_duplicate_provider_bars");
  }
  return { bars, received_at: receipt, pages, raw_count: output.length, start, end, feed: "iex", adjustment: "raw" };
}

function shipyardPythonDailyReference(input, targetSession, previousSession, symbol) {
  if (!input || input.schema !== "SHIPYARD_FROZEN_PREOPEN_INPUT_V1" || input.diagnostic === true
      || input.preopen_receipt_eligible !== true || input.symbol !== symbol || input.target_session !== targetSession.date
      || input.provider !== "Alpaca" || input.feed !== "iex" || input.adjustment !== "raw"
      || !Array.isArray(input.daily_bars) || !input.source_receipts?.daily) throw new Error("preopen_reference_unavailable");
  if (!timestamp(input.source_receipts.daily) || input.target_open !== targetSession.open || Date.parse(input.source_receipts.daily) > Date.parse(targetSession.open)
      || Date.parse(input.source_receipts.daily) < Date.parse(previousSession.close)) throw new Error("preopen_reference_time_invalid");
  const daily = input.daily_bars.map(row => {
    const start = timestamp(row?.t), open = finite(row?.o), high = finite(row?.h), low = finite(row?.l), close = finite(row?.c), volume = finite(row?.v);
    if (!start || [open, high, low, close, volume].some(value => value === null) || open <= 0 || high <= 0
        || low <= 0 || close <= 0 || volume < 0 || high < Math.max(open, close) || low > Math.min(open, close)) return null;
    return { date: newYorkDate(new Date(row.t)), high, low, close };
  });
  if (daily.some(row => !row || row.high === null || row.low === null || row.close === null
      || row.low <= 0 || row.close <= 0 || row.high < row.low)) throw new Error("invalid_daily_reference_bars");
  if (daily.length < 14 || daily.at(-1).date !== previousSession.date) throw new Error("daily_reference_history_incomplete");
  const dailyByDate = new Map(daily.map(row => [row.date, row]));
  if (dailyByDate.size !== daily.length) throw new Error("duplicate_daily_reference_date");
  const expectedDates = input.calendar.filter(row => row.date <= previousSession.date).slice(-daily.length).map(row => row.date);
  if (expectedDates.length !== daily.length || daily.some((row, index) => row.date !== expectedDates[index])) {
    throw new Error("daily_reference_session_gap");
  }
  let previousClose = null, atr = null, seed = [];
  for (const row of daily) {
    const tr = previousClose === null ? row.high - row.low
      : Math.max(row.high - row.low, Math.abs(row.high - previousClose), Math.abs(row.low - previousClose));
    if (atr === null) {
      seed.push(tr);
      if (seed.length === 14) atr = seed.reduce((sum, value) => sum + value, 0) / 14;
    } else atr = (13 * atr + tr) / 14;
    previousClose = row.close;
  }
  if (!Number.isFinite(atr) || atr <= 0 || previousClose <= 0) throw new Error("daily_reference_atr_unavailable");
  const availableAt = input.source_receipts.daily;
  return {
    references: [{ horizon: "1D", period_end: previousSession.close, available_at: availableAt,
      close: previousClose, atr, valid_from: targetSession.open, valid_until: targetSession.close,
      period_id: `${symbol}:${previousSession.date}` }],
    reference_windows: [{ symbol, horizon: "1D", valid_from: targetSession.open,
      valid_until: targetSession.close, previous_period_end: previousSession.close, known_at: availableAt }],
  };
}

function shipyardPythonBuildSessions(calendar, usedStart) {
  return calendar.filter(session => Date.parse(session.close) > usedStart).map(session => ({
    session_id: session.date, open: session.open, entry_start: session.open,
    entry_cutoff: session.close, flat_at: session.close, close: session.close,
  }));
}

function shipyardPythonResample(bars, sessions, receiptAt, requestStart) {
  const sessionMap = new Map(sessions.map(session => [session.session_id, session]));
  const grouped = new Map(sessions.map(session => [session.session_id, []]));
  for (const bar of bars) {
    const day = newYorkDate(new Date(bar.start)), session = sessionMap.get(day);
    if (!session) continue;
    const start = Date.parse(bar.start), open = Date.parse(session.open), close = Date.parse(session.close);
    if (start < open || Date.parse(bar.end) > close) continue;
    const offset = start - open;
    if (offset % SHIPYARD_PYTHON_BAR_MS !== 0) throw new Error("intraday_bar_not_session_aligned");
    grouped.get(day).push(bar);
  }
  const completedBars = [], hourly = [], partialSessions = [];
  for (const session of sessions) {
    const day = session.session_id, open = Date.parse(session.open), close = Date.parse(session.close);
    const expectedFull = (close - open) / SHIPYARD_PYTHON_BAR_MS;
    if (!Number.isInteger(expectedFull) || expectedFull < 1) throw new Error("invalid_official_session_duration");
    const isCurrent = Date.parse(receiptAt) >= open && Date.parse(receiptAt) < close;
    const expected = isCurrent ? Math.min(expectedFull, Math.floor((Date.parse(receiptAt) - open) / SHIPYARD_PYTHON_BAR_MS)) : expectedFull;
    const rows = (grouped.get(day) || []).filter(bar => Date.parse(bar.end) <= Date.parse(receiptAt));
    if (rows.length === 0 && expected === 0) continue;
    const firstIsOpen = rows.length > 0 && Date.parse(rows[0].start) === open;
    // The first request date can cut through an old session. Keep that date in
    // provenance and exclude the whole partial prefix from warmup.
    if (!firstIsOpen && rows.length && Date.parse(session.open) < requestStart && rows[0].start > session.open) {
      partialSessions.push(day);
      continue;
    }
    if (rows.length !== expected || rows.some((bar, index) => Date.parse(bar.start) !== open + index * SHIPYARD_PYTHON_BAR_MS)) {
      if (isCurrent && expected > rows.length && rows.at(-1) && Date.parse(rows.at(-1).end) <= Date.parse(receiptAt)) {
        throw new Error("current_session_intraday_gap");
      }
      if (!isCurrent && Date.parse(session.open) < requestStart && rows.length < expectedFull && rows.length > 0 && !firstIsOpen) {
        partialSessions.push(day);
        continue;
      }
      if (!isCurrent && expectedFull > 0 && rows.length === 0) throw new Error("historical_session_missing");
      if (rows.length !== expected || rows.some((bar, index) => Date.parse(bar.start) !== open + index * SHIPYARD_PYTHON_BAR_MS)) {
        throw new Error(isCurrent ? "current_session_intraday_gap" : "historical_intraday_grid_gap");
      }
    }
    completedBars.push(...rows);
    const fullHours = Math.floor(expectedFull / 6), tail = expectedFull % 6;
    for (let bucket = 0; bucket < fullHours; bucket += 1) {
      const rowsForHour = rows.slice(bucket * 6, bucket * 6 + 6);
      if (rowsForHour.length === 6) hourly.push(shipyardPythonAggregateHour(rowsForHour, day));
    }
    if (tail && !isCurrent && rows.length === expectedFull) {
      const tailRows = rows.slice(fullHours * 6);
      if (tailRows.length === tail) hourly.push(shipyardPythonAggregateHour(tailRows, day));
    }
  }
  return { tenMinute: completedBars.slice(-1000), oneHour: hourly.slice(-1000),
    total_ten_minute: completedBars.length, total_session_hour: hourly.length,
    partial_session_dates_excluded: partialSessions };
}

function shipyardPythonAggregateHour(rows, day) {
  if (!rows.length || rows.some((row, index) => index > 0 && Date.parse(row.start) !== Date.parse(rows[index - 1].end))) {
    throw new Error("hour_bucket_incomplete");
  }
  return { symbol: rows[0].symbol, timeframe: "1H", session_id: day,
    bar: { start: rows[0].start, end: rows.at(-1).end, open: rows[0].open,
      high: Math.max(...rows.map(row => row.high)), low: Math.min(...rows.map(row => row.low)),
      close: rows.at(-1).close, volume: rows.reduce((sum, row) => sum + row.volume, 0) } };
}

async function shipyardPythonCalendarSnapshot(request, env) {
  const targetDate = newYorkDate(new Date());
  const targetSessionResponse = await shipyardExchangeCalendar(request, {
    start_date: new Date(Date.now() - 360 * 86400000).toISOString().slice(0, 10), end_date: targetDate,
  }, env);
  const calendarData = await targetSessionResponse.json();
  if (!targetSessionResponse.ok || calendarData.status !== "available" || !calendarData.complete_provider_response) {
    if (calendarData.error === "invalid_calendar") throw new Error("official_calendar_invalid");
    if (calendarData.error === "rate_limited") throw new Error("rate_limited");
    if (calendarData.error === "provider_not_configured") throw new Error("market_data_credentials_unavailable");
    throw new Error("official_calendar_unavailable");
  }
  const today = calendarData.calendar.find(session => session.date === targetDate);
  const previous = [...calendarData.calendar].reverse().find(session => session.date < targetDate);
  // Only a validated, complete calendar with prior-session evidence can prove
  // a non-session date. Unavailable/empty calendars must not become "closed".
  if (!previous) throw new Error("current_or_previous_session_unavailable");
  if (!today) throw new ShipyardPythonClosedSession(targetDate, previous, calendarData);
  // Keep the adapter's existing inclusive close boundary; do not backdate or
  // substitute a prior session to make an out-of-session snapshot eligible.
  if (Date.now() < Date.parse(today.open)) throw new ShipyardPythonClosedSession(targetDate, previous, calendarData, "before_open", today);
  if (Date.now() > Date.parse(today.close)) throw new ShipyardPythonClosedSession(targetDate, previous, calendarData, "after_close", today);
  return { calendarData, targetDate, today, previous };
}

async function shipyardPythonSatyPayload(request, env, symbol, progress = async () => {}) {
  const capturedAt = new Date().toISOString();
  await progress("calendar");
  const { calendarData, targetDate, today, previous } = await shipyardPythonCalendarSnapshot(request, env);
  await progress("preopen", { calendar: calendarData.received_at });
  const preopenResponse = await shipyardPreopenTool(request, { symbol, target_session: targetDate }, env, "read");
  const preopenResult = await preopenResponse.json();
  if (!preopenResponse.ok || preopenResult.status !== "captured_inputs" || !preopenResult.inputs) {
    throw new Error(preopenResult.error || "preopen_capture_missing");
  }
  const reference = shipyardPythonDailyReference(preopenResult.inputs, today, previous, symbol);
  const start = new Date(Date.now() - SHIPYARD_PYTHON_INTRADAY_LOOKBACK_DAYS * 86400000).toISOString();
  const end = new Date().toISOString();
  await progress("market_bars", { preopen_daily: preopenResult.inputs.source_receipts.daily,
    preopen_prior_5m: preopenResult.inputs.source_receipts.prior_5m, preopen_captured_at: preopenResult.metadata.source_received_at });
  const barRead = await shipyardPythonFetchBars(request, env, symbol, "10Min", start, end);
  const calendarRows = calendarData.calendar.filter(session => Date.parse(session.close) > Date.parse(start));
  const sessions = shipyardPythonBuildSessions(calendarRows, Date.parse(start));
  const normalized = barRead.bars.map(bar => ({ ...bar, symbol }));
  const bars = shipyardPythonResample(normalized, sessions, barRead.end, Date.parse(start));
  if (bars.tenMinute.length < 1000 || bars.oneHour.length < 1000) throw new Error("warmup_incomplete");
  const providerReceivedAt = barRead.received_at;
  const observations = [
    ...bars.tenMinute.map(({ symbol: _symbol, ...bar }) => ({ symbol, timeframe: "10m", bar, available_at: providerReceivedAt,
      provider: "alpaca", venue: "IEX", session_policy: "regular", adjustment: "raw", revision: "snapshot" })),
    ...bars.oneHour.map(({ symbol: _symbol, timeframe: _timeframe, session_id: _session, bar }) => ({ symbol,
      timeframe: "1H", bar, available_at: providerReceivedAt, provider: "alpaca", venue: "IEX",
      session_policy: "regular", adjustment: "raw", revision: "snapshot" })),
  ];
  const source = { provider: "alpaca", feed: "iex", adjustment: "raw", venue: "IEX" };
  return {
    symbol, source, coverage: { status: "complete", captured_at: capturedAt,
      provider_received_at: providerReceivedAt, provider_page_count: barRead.pages,
      provider_raw_bar_count: barRead.raw_count, ten_minute_count: bars.tenMinute.length,
      session_hour_count: bars.oneHour.length, pagination_complete: true,
      interval_grid_complete: true, excluded_partial_session_dates: bars.partial_session_dates_excluded,
      historical_publication_availability: "unknown; historical bars warm present-time features only" },
    calendar: { version: `Alpaca calendar v2 · ${calendarData.requested_range.start_date}:${calendarData.requested_range.end_date}`,
      provider: "alpaca-market-calendar-v2", retrieved_at: calendarData.received_at },
    sessions, observations, ...reference,
    source_receipts: { intraday: providerReceivedAt, calendar: calendarData.received_at,
      preopen_daily: preopenResult.inputs.source_receipts.daily,
      preopen_prior_5m: preopenResult.inputs.source_receipts.prior_5m,
      preopen_captured_at: preopenResult.metadata.source_received_at },
    research_schedule: "official-session-open-to-close-v1",
  };
}

async function shipyardPythonRrePayload(request, env, symbol, progress = async () => {}) {
  const capturedAt = new Date().toISOString();
  await progress("calendar");
  const { calendarData, targetDate, today, previous } = await shipyardPythonCalendarSnapshot(request, env);
  await progress("preopen", { calendar: calendarData.received_at });
  const preopenResponse = await shipyardPreopenTool(request, { symbol, target_session: targetDate }, env, "read");
  const preopenResult = await preopenResponse.json();
  if (!preopenResponse.ok || preopenResult.status !== "captured_inputs" || !preopenResult.inputs) throw new Error("preopen_capture_missing");
  const input = preopenResult.inputs;
  const priorRows = input.prior_5m_bars;
  const priorReceipt = input.source_receipts?.prior_5m;
  if (input.schema !== "SHIPYARD_FROZEN_PREOPEN_INPUT_V1" || input.diagnostic === true || input.provider !== "Alpaca"
      || input.target_open !== today.open || input.symbol !== symbol || input.target_session !== targetDate
      || input.preopen_receipt_eligible !== true || input.feed !== "iex" || input.adjustment !== "raw"
      || !Array.isArray(priorRows) || !timestamp(priorReceipt) || Date.parse(priorReceipt) < Date.parse(previous.close)
      || Date.parse(priorReceipt) > Date.parse(today.open) || !Array.isArray(input.calendar)) {
    throw new Error("prior_session_reference_unavailable");
  }
  const priorExpected = (Date.parse(previous.close) - Date.parse(previous.open)) / 300000;
  const priorBars = priorRows.map((row, index) => shipyardPythonStrictBar(row, "5Min", Date.parse(previous.open) + index * 300000));
  if (!Number.isInteger(priorExpected) || priorBars.length !== priorExpected
      || priorBars.at(-1)?.end !== previous.close) throw new Error("prior_session_grid_incomplete");
  await progress("market_bars", { preopen_prior_5m: priorReceipt, preopen_capture: preopenResult.metadata?.source_received_at });
  const currentRead = await shipyardPythonFetchBars(request, env, symbol, "5Min", today.open, new Date().toISOString());
  const currentExpectedFull = (Date.parse(today.close) - Date.parse(today.open)) / 300000;
  if (!Number.isInteger(currentExpectedFull) || currentExpectedFull < 1) throw new Error("invalid_official_session_duration");
  // A bar unfinished at request end is not made complete by a slow response.
  const completedThrough = Math.min(Date.parse(currentRead.end), Date.parse(currentRead.received_at));
  const currentExpected = completedThrough < Date.parse(today.close)
    ? Math.max(0, Math.floor((completedThrough - Date.parse(today.open)) / 300000)) : currentExpectedFull;
  const currentBars = currentRead.bars.filter(bar => Date.parse(bar.start) >= Date.parse(today.open)
    && Date.parse(bar.end) <= Date.parse(today.close) && Date.parse(bar.end) <= completedThrough);
  if (currentBars.length !== currentExpected || currentBars.some((bar, index) => Date.parse(bar.start) !== Date.parse(today.open) + index * 300000)) {
    throw new Error(currentExpected === 0 ? "current_session_bars_unavailable" : "current_session_intraday_gap");
  }
  await progress("event_schedule", { current_intraday: currentRead.received_at });
  const eventResponse = await shipyardOfficialEvents(request, {});
  const eventData = await eventResponse.json();
  const eventVersion = eventData.snapshot_hash || eventData.policy || "event-source-receipt-unavailable";
  const eventRows = Array.isArray(eventData.events) ? eventData.events : [];
  const eventReceipts = Array.isArray(eventData.sources) ? eventData.sources : [];
  // RRE consumes five-minute bars. Timed releases suppress their containing
  // bar. A date-only item suppresses the full session rather than being silently
  // treated as a clear window. These official schedule feeds do not cover every
  // market event, so RRE's full-session event-coverage gate remains closed.
  const eventWindows = eventRows.flatMap(event => {
    if (!event || typeof event !== "object" || event.cancelled === true) return [];
    if (typeof event.scheduled_at !== "string") {
      if (event.scheduled_date !== targetDate || event.time_status !== 'time_unknown') return [];
      return [{ event_id: typeof event.event_id === "string" ? event.event_id : null,
        source: typeof event.source === "string" ? event.source : null,
        title: typeof event.title === "string" ? event.title : null, scheduled_at: null,
        start: today.open, end: today.close, available_at: typeof event.available_at === "string" ? event.available_at : null,
        time_status: 'time_unknown', blackout_scope: 'entire_session' }];
    }
    const scheduledAt = Date.parse(event.scheduled_at);
    if (!Number.isFinite(scheduledAt) || scheduledAt < Date.parse(today.open)
        || scheduledAt >= Date.parse(today.close)) return [];
    const start = Math.floor(scheduledAt / 300000) * 300000;
    const end = start + 300000;
    if (start < Date.parse(today.open) || end > Date.parse(today.close)) return [];
    return [{
      event_id: typeof event.event_id === "string" ? event.event_id : null,
      source: typeof event.source === "string" ? event.source : null,
      title: typeof event.title === "string" ? event.title : null,
      scheduled_at: new Date(scheduledAt).toISOString(),
      start: new Date(start).toISOString(),
      end: new Date(end).toISOString(),
      available_at: typeof event.available_at === "string" ? event.available_at : null,
      time_status: 'scheduled',
    }];
  });
  const older = [...calendarData.calendar].reverse().find(session => session.date < previous.date);
  return {
    symbol,
    source: { provider: "alpaca", feed: "iex", adjustment: "raw", venue: "IEX" },
    coverage: { status: "complete", captured_at: capturedAt, provider_received_at: currentRead.received_at,
      provider_page_count: currentRead.pages, provider_raw_bar_count: currentRead.raw_count,
      current_session_5m_count: currentBars.length, prior_session_5m_count: priorBars.length,
      pagination_complete: true, interval_grid_complete: true,
      historical_publication_availability: "unknown; present snapshot only" },
    calendar: { version: `Alpaca calendar v2 · ${calendarData.requested_range.start_date}:${calendarData.requested_range.end_date}`,
      provider: "alpaca-market-calendar-v2", retrieved_at: calendarData.received_at },
    sessions: [
      { id: targetDate, open: today.open, close: today.close, previous_id: previous.date },
      { id: previous.date, open: previous.open, close: previous.close, previous_id: older?.date || null },
    ],
    prior_session_reference: { session_id: targetDate, previous_session_id: previous.date, complete: true,
      high: Math.max(...priorBars.map(bar => bar.high)), low: Math.min(...priorBars.map(bar => bar.low)),
      close: priorBars.at(-1).close, available_at: priorReceipt,
      series_id: `${symbol}:Alpaca-IEX-raw-5m:${previous.date}`,
      calendar_version: `Alpaca calendar v2 · ${calendarData.requested_range.start_date}:${calendarData.requested_range.end_date}` },
    bars: currentBars.map(bar => ({ symbol, session_id: targetDate, ...bar, available_at: currentRead.received_at })),
    tick_size: 0.01, variant: "RRE2", cost_reserve_price: 0,
    event_coverage: { source: "Shipyard scoped official release calendars", version: eventVersion,
      captured_at: eventData.received_at || new Date().toISOString(), covered_from: today.open, covered_until: today.close,
      status: "partial", events: eventWindows, scope_complete: false,
      exclusions: eventData.restrictions?.exclusions || ["company earnings", "unscheduled news", "Treasury auctions", "Census", "DOL weekly claims"] },
    event_source_status: eventData.status || "unavailable",
    event_source_receipts: eventReceipts.map(source => ({ source: source.source,
      status: source.status, received_at: source.received_at, scope_complete: source.scope_complete === true })),
    source_receipts: { current_intraday: currentRead.received_at, calendar: calendarData.received_at,
      preopen_prior_5m: priorReceipt, preopen_capture: preopenResult.metadata?.source_received_at,
      event_schedule: eventData.received_at || null },
  };
}

async function shipyardPythonResearchRoute(request, env) {
  const url = new URL(request.url), path = url.pathname;
  if (!path.startsWith("/api/research/python/")) return null;
  if (path === "/api/research/python/status") {
    if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
    const token = shipyardPythonServiceToken(env);
    if (!token) return json({ schema: "SHIPYARD_PYTHON_SERVICE_STATUS_V1", status: "unconfigured",
      provider: "DigitalOcean private research service", error: "service_token_not_configured", engines: { saty: "0.3.0", rre: "0.2.0" } }, 503);
    try {
      const status = shipyardPythonValidateStatus(await shipyardPythonServiceRequest("/v1/status", token, { signal: AbortSignal.any([request.signal, AbortSignal.timeout(7000)]) }));
      return json({ schema: "SHIPYARD_PYTHON_SERVICE_STATUS_V1", status: "connected", provider: "DigitalOcean private research service",
        checked_at: new Date().toISOString(), build_id: status.build_id, adapter_contract: status.adapter_contract,
        queue: status.queue, engines: status.engines, calculation_mode: "on-demand", order_submission_enabled: false });
    } catch (error) {
      return json({ schema: "SHIPYARD_PYTHON_SERVICE_STATUS_V1", status: "unavailable",
        provider: "DigitalOcean private research service", error: error?.message === "service_contract_mismatch" ? "service_contract_mismatch" : "service_unreachable_or_auth_rejected",
        checked_at: new Date().toISOString(), order_submission_enabled: false }, 503);
    }
  }
  if (path === "/api/research/python/preopen-status") {
    if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
    const keys = [...url.searchParams.keys()], symbol = url.searchParams.get("symbol");
    if (keys.length !== 1 || keys[0] !== "symbol" || !["SPY", "QQQ"].includes(symbol)) return json({ error: "invalid_request" }, 400);
    const targetSession = newYorkDate(new Date());
    const response = await shipyardPreopenTool(request, { symbol, target_session: targetSession }, env, "read");
    let value;
    try { value = await response.json(); } catch { return json({ status: "unavailable", error: "preopen_status_unavailable" }, 503); }
    return json({ schema: value.schema, status: value.status, provider: value.provider, feed: value.feed,
      adjustment: value.adjustment, symbol, target_session: targetSession, metadata: value.metadata || null,
      error: value.error || null, preopen_receipt_eligible: value.preopen_receipt_eligible === true,
      restrictions: value.restrictions, note: value.note }, response.status);
  }
  if (path === "/api/research/python/preopen-capture") {
    if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
    let body;
    if (!shipyardPythonSameOrigin(request)) return json({ error: "same_origin_required" }, 403);
    try { body = await shipyardPythonReadJson(request); } catch { return json({ error: "invalid_json_or_size" }, 400); }
    if (!body || typeof body !== "object" || Array.isArray(body) || Object.keys(body).length !== 0) return json({ error: "invalid_request" }, 400);
    return shipyardPreopenTool(request, { mode: "capture" }, env, "write");
  }
  if (path === "/api/research/python/attempts") {
    if (request.method !== "GET") return json({error:"method_not_allowed"},405);
    const keys=[...url.searchParams.keys()],args=Object.fromEntries(url.searchParams);
    if (new Set(keys).size!==keys.length || keys.some(key=>!['engine','symbol','limit','before'].includes(key))
        || ['limit','before'].some(key=>args[key]!==undefined && !/^[1-9][0-9]{0,15}$/.test(args[key]))) return json({error:"invalid_request"},400);
    for (const key of ['limit','before']) if (args[key]!==undefined) args[key]=Number(args[key]);
    if (!shipyardPythonAttemptQuery(args)) return json({error:"invalid_request"},400);
    return shipyardPythonAttemptRead(env,args);
  }
  const attemptMatch=/^\/api\/research\/python\/attempts\/([a-f0-9]{32})$/.exec(path);
  if (attemptMatch) {
    if (request.method!=="GET") return json({error:"method_not_allowed"},405);
    if ([...url.searchParams].length) return json({error:"invalid_request"},400);
    return shipyardPythonAttemptRead(env,{},attemptMatch[1]);
  }
  if (path === "/api/research/python/run") {
    if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
    let body;
    if (!shipyardPythonSameOrigin(request)) return json({ error: "same_origin_required" }, 403);
    try { body = await shipyardPythonReadJson(request); } catch { return json({ error: "invalid_json_or_size" }, 400); }
    if (!body || typeof body !== "object" || Array.isArray(body) || ![2,3].includes(Object.keys(body).length)
        || Object.keys(body).some(key=>!['engine','symbol','attempt_id'].includes(key))
        || !["saty", "rre"].includes(body.engine) || !["SPY", "QQQ"].includes(body.symbol)
        || (body.attempt_id!==undefined && !shipyardPythonAttemptId(body.attempt_id))) return json({ error: "invalid_request" }, 400);
    const attemptId=body.attempt_id || crypto.randomUUID().replaceAll('-',''), requestId=crypto.randomUUID().replaceAll('-','');
    const identity={engine:body.engine,symbol:body.symbol,attempt_id:attemptId,request_id:requestId,order_submission_enabled:false};
    let attempt;
    try { attempt=await shipyardPythonAttemptStart(env,attemptId,requestId,body.engine,body.symbol); }
    catch (error) {
      const conflict=error?.message==='attempt_identity_conflict';
      return shipyardPythonError(conflict?'attempt_identity_conflict':'receipt_storage_unavailable',conflict?409:503,
        {...identity,submission_outcome:!conflict && error?.attempt_created===true?'not_submitted':'unknown',
          invocation_submission_outcome:'not_submitted',receipt_persisted:false,stage:'receipt_initialization'});
    }
    if (!attempt.created) return json({schema:'SHIPYARD_PYTHON_RESEARCH_V1',status:'already_recorded',
      engine:body.engine,symbol:body.symbol,attempt_id:attemptId,request_id:attempt.receipt.request_id,
      submission_outcome:attempt.receipt.terminal && attempt.receipt.submission_outcome==='not_submitted'?'not_submitted'
        :attempt.receipt.submission_outcome==='accepted'?'submitted':'unknown',
      job_id:attempt.receipt.job_id,attempt_receipt:attempt.receipt,receipt_persisted:true,replay_performed:false,replay_supported:false,
      retrieval_freshness:'stored_attempt_not_requalified',decision_eligible:false,order_submission_enabled:false});
    const beforeSubmitFailure=async(message,extra={})=>shipyardPythonError(message,503,{...identity,submission_outcome:'not_submitted',
      input_timestamps:{failed_at:new Date().toISOString()},...extra,...await shipyardPythonAttemptFinish(env,attempt,message)});
    const progress=async(stage,source_receipts={})=>shipyardPythonAttemptUpdate(env,attempt,{stage,source_receipts});
    let payload,submissionBody;
    try {
      await progress('service_check');
      const token=shipyardPythonServiceToken(env);
      if (!token) return beforeSubmitFailure('service_token_not_configured');
      try { shipyardPythonValidateStatus(await shipyardPythonServiceRequest('/v1/status',token,
        {signal:AbortSignal.any([request.signal,AbortSignal.timeout(7000)])})); }
      catch { return beforeSubmitFailure('service_unreachable_or_contract_mismatch'); }
      payload=body.engine==='saty'?await shipyardPythonSatyPayload(request,env,body.symbol,progress):await shipyardPythonRrePayload(request,env,body.symbol,progress);
      submissionBody=JSON.stringify({engine:body.engine,payload});
      const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(submissionBody)))].map(byte=>byte.toString(16).padStart(2,'0')).join('');
      await shipyardPythonAttemptUpdate(env,attempt,{stage:'inputs_ready',input_hash:hash,source_receipts:payload.source_receipts});
      if (request.signal.aborted) return beforeSubmitFailure('request_cancelled_before_submit');
      // Durable intent before POST. Any interruption after this boundary remains
      // unknown, never evidence that no remote job was created.
      await progress('submitting');
    } catch (error) {
      if (error instanceof ShipyardPythonClosedSession) return json({schema:'SHIPYARD_PYTHON_RESEARCH_V1',status:'abstained',
        reason_class:'market_closed',blockers:['MARKET_CLOSED'],...identity,submission_outcome:'not_submitted',
        checked_at:new Date().toISOString(),session:error.session,research_only:true,decision_eligible:false,
        ...await shipyardPythonAttemptFinish(env,attempt,'market_closed',{calendar:error.session.calendar_received_at})});
      return beforeSubmitFailure(['receipt_write_failed','receipt_storage_unavailable'].includes(error?.message)?error.message:shipyardPythonSafeError(error));
    }
    let record;
    try {
      record=shipyardPythonValidateJob(await shipyardPythonServiceRequest('/v1/jobs',shipyardPythonServiceToken(env),{
        method:'POST',headers:{'content-type':'application/json','idempotency-key':attempt.row.idempotency_key},
        body:submissionBody,signal:AbortSignal.any([request.signal,AbortSignal.timeout(15000)]),
      }),{engine:body.engine,symbol:body.symbol,submitted:true});
    } catch {
      let receiptPersisted=false;
      try { await shipyardPythonAttemptUpdate(env,attempt,{terminal:1,submission_outcome:'unknown',failure_code:'research_job_submission_failed'}); receiptPersisted=true; } catch {}
      return shipyardPythonError('research_job_submission_failed',503,{...identity,submission_outcome:'unknown',coverage:payload.coverage,
        receipt_persisted:receiptPersisted,...(receiptPersisted?{attempt_receipt:attempt.receipt}:{receipt_error:'receipt_write_failed'})});
    }
    try { await shipyardPythonAttemptUpdate(env,attempt,{stage:'accepted',terminal:1,submission_outcome:'accepted',failure_code:null,
      job_id:record.id,job_created_at:record.created_at,build_id:record.build_id}); }
    catch {
      // Acceptance and its exact ID are known. Only Site receipt durability is
      // uncertain; preserve this distinction and never replay the POST.
      return shipyardPythonError('receipt_write_failed',503,{...identity,submission_outcome:'accepted_not_recorded',
        job_id:record.id,build_id:record.build_id,created_at:record.created_at,receipt_persisted:false,
        acceptance_known:true,replay_supported:false,input_timestamps:shipyardPythonAttemptClocks(payload.source_receipts)});
    }
    return json({schema:'SHIPYARD_PYTHON_RESEARCH_V1',status:record.status,...identity,submission_outcome:'submitted',
      engine_version:body.engine==='saty'?'0.3.0':'0.2.0',job_id:record.id,build_id:record.build_id,created_at:record.created_at,
      input_timestamps:shipyardPythonAttemptClocks(payload.source_receipts),coverage:payload.coverage,calendar:payload.calendar,
      receipt_persisted:true,attempt_receipt:attempt.receipt},202);
  }
  const match = /^\/api\/research\/python\/jobs\/([a-f0-9]{32})$/.exec(path);
  if (match) {
    if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
    const token = shipyardPythonServiceToken(env);
    if (!token) return shipyardPythonError("service_token_not_configured");
    try {
      const record = shipyardPythonValidateJob(await shipyardPythonServiceRequest(`/v1/jobs/${match[1]}`, token,
        { signal: AbortSignal.any([request.signal, AbortSignal.timeout(7000)]) }), { id: match[1] });
      const linkage=await shipyardPythonAttemptLink(env,record);
      if (linkage.attempt_linkage==='identity_mismatch') return shipyardPythonError('research_job_receipt_mismatch');
      return json({ schema: "SHIPYARD_PYTHON_RESEARCH_V1", ...record, ...linkage, research_only: true, decision_eligible: false,
        retrieval_freshness: "stored_result_not_requalified", order_submission_enabled: false });
    } catch {
      return shipyardPythonError("research_job_unavailable");
    }
  }
  return json({ error: "not_found" }, 404);
}
