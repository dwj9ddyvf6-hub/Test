// Public read-only daily bars. Credentials stay in the Site runtime; this
// adapter never calls Alpaca Trading API account, order, or position routes.
const alpacaBarsCache = new Map();
const alpacaCalendarCache = new Map();
const alpacaRequestWindows = new Map();
const alpacaBrainCache = new Map();
const ALPACA_CACHE_MS = 30000;
const ALPACA_CALENDAR_CACHE_MS = 6 * 60 * 60 * 1000;
const ALPACA_BRAIN_CACHE_MS = 30000;
const ALPACA_OPTION_QUOTE_MAX_AGE_SECONDS = 90;

function newYorkDate(value) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(value);
  const date = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${date.year}-${date.month}-${date.day}`;
}

async function alpacaIexSessionCalendar(date, keyId, secret) {
  const now = Date.now();
  const cached = alpacaCalendarCache.get(date);
  if (cached && now < cached.until) return cached.value;
  const query = new URLSearchParams({ start: date, end: date, timezone: "UTC" });
  try {
    const response = await fetch(`https://paper-api.alpaca.markets/v3/calendar/IEX?${query}`, {
      method: "GET",
      headers: {
        "APCA-API-KEY-ID": keyId,
        "APCA-API-SECRET-KEY": secret,
        accept: "application/json",
      },
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) return null;
    const payload = JSON.parse(await readBoundedBody(response, 65536));
    if (!Array.isArray(payload?.calendar)) return null;
    const entry = payload.calendar.find((item) => item?.date === date);
    const value = entry
      ? (() => {
        const coreStart = timestamp(entry.core_start);
        const coreEnd = timestamp(entry.core_end);
        return coreStart && coreEnd ? { market: "IEX", date, status: "open", core_start: coreStart, core_end: coreEnd, source: "alpaca_iex_calendar_v3", received_at: new Date().toISOString() } : null;
      })()
      : { market: "IEX", date, status: "closed", core_start: null, core_end: null, source: "alpaca_iex_calendar_v3", received_at: new Date().toISOString() };
    if (!value) return null;
    if (alpacaCalendarCache.size > 64) alpacaCalendarCache.clear();
    alpacaCalendarCache.set(date, { value, until: now + ALPACA_CALENDAR_CACHE_MS });
    return value;
  } catch {
    return null;
  }
}

function alpacaRateAllowed(request, now) {
  const key = request.headers.get("cf-connecting-ip") || "anonymous";
  const prior = alpacaRequestWindows.get(key);
  const window = !prior || now - prior.started >= 60000 ? { started: now, count: 0 } : prior;
  window.count += 1;
  alpacaRequestWindows.set(key, window);
  if (alpacaRequestWindows.size > 512) {
    for (const [ip, item] of alpacaRequestWindows) {
      if (now - item.started >= 60000 || alpacaRequestWindows.size > 512) alpacaRequestWindows.delete(ip);
    }
  }
  return window.count <= 20;
}

function alpacaBrainRateAllowed(request, now) {
  const key = request.headers.get("cf-connecting-ip") || "anonymous";
  const prior = alpacaRequestWindows.get(`brain:${key}`);
  const window = !prior || now - prior.started >= 60000 ? { started: now, count: 0 } : prior;
  window.count += 1;
  alpacaRequestWindows.set(`brain:${key}`, window);
  return window.count <= 5;
}

async function alpacaJson(url, keyId, secret, timeoutMs = 8000) {
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "APCA-API-KEY-ID": keyId,
        "APCA-API-SECRET-KEY": secret,
        accept: "application/json",
      },
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!response.ok) return { ok: false, status: response.status, value: null };
    const value = JSON.parse(await readBoundedBody(response, 1024 * 1024));
    return { ok: true, status: response.status, value };
  } catch {
    return { ok: false, status: 0, value: null };
  }
}

function alpacaQuote(raw) {
  const at = timestamp(raw?.t);
  const bid = finite(raw?.bp), ask = finite(raw?.ap);
  const bidSize = finite(raw?.bs), askSize = finite(raw?.as);
  if (!at || bid === null || ask === null || bid <= 0 || ask < bid || askSize === null || bidSize === null) return null;
  return { at, bid, ask, bid_size: bidSize, ask_size: askSize };
}

function alpacaBrainIndicators(rawBars, sessionDate) {
  const bars = rawBars.flatMap((raw) => {
    const at = timestamp(raw?.t);
    const utcDate = at?.slice(0, 10);
    const open = finite(raw?.o), high = finite(raw?.h), low = finite(raw?.l), close = finite(raw?.c);
    if (!at || !utcDate || utcDate >= sessionDate || open === null || high === null || low === null || close === null || low <= 0 || high < Math.max(open, close, low) || low > Math.min(open, close, high)) return [];
    return [{ at, open, high, low, close }];
  }).slice(-120);
  const closes = bars.map((bar) => bar.close);
  if (bars.length < 51) return { bars, value: null };
  const sma = (values, length) => values.length < length ? null : values.slice(-length).reduce((sum, value) => sum + value, 0) / length;
  const sma20 = sma(closes, 20), sma50 = sma(closes, 50);
  const changes = closes.slice(-15).slice(1).map((value, index) => value - closes.slice(-15)[index]);
  const gains = changes.map((value) => Math.max(value, 0));
  const losses = changes.map((value) => Math.max(-value, 0));
  const averageGain = gains.reduce((sum, value) => sum + value, 0) / 14;
  const averageLoss = losses.reduce((sum, value) => sum + value, 0) / 14;
  const rsi14 = averageLoss === 0 ? 100 : 100 - 100 / (1 + averageGain / averageLoss);
  const ranges = bars.slice(-14).map((bar, index) => {
    const previousClose = bars[Math.max(0, bars.length - 15 + index)]?.close ?? bar.close;
    return Math.max(bar.high - bar.low, Math.abs(bar.high - previousClose), Math.abs(bar.low - previousClose));
  });
  const atr14 = ranges.reduce((sum, value) => sum + value, 0) / ranges.length;
  const last = bars.at(-1);
  if (![sma20, sma50, rsi14, atr14, last?.close].every(Number.isFinite) || atr14 <= 0) return { bars, value: null };
  return { bars, value: { sma20, sma50, rsi14, atr14, latest_close: last.close, as_of: last.at } };
}

function alpacaBrainDirection(indicators, underlyingMid) {
  const value = indicators;
  if (!value) return { direction: null, reason: "At least 51 completed daily bars are required." };
  if (value.latest_close > value.sma20 && value.sma20 > value.sma50 && underlyingMid > value.sma20 && value.rsi14 >= 50 && value.rsi14 <= 70) {
    return { direction: "bullish", option_type: "call", reason: "Completed daily close and live price are above the 20-day average, which is above the 50-day average; RSI is between 50 and 70." };
  }
  if (value.latest_close < value.sma20 && value.sma20 < value.sma50 && underlyingMid < value.sma20 && value.rsi14 >= 30 && value.rsi14 <= 50) {
    return { direction: "bearish", option_type: "put", reason: "Completed daily close and live price are below the 20-day average, which is below the 50-day average; RSI is between 30 and 50." };
  }
  return { direction: null, reason: "The live price, 20/50-day trend, and RSI do not align." };
}

function alpacaStandardDeliverable(contract, symbol) {
  const deliverables = Array.isArray(contract?.deliverables) ? contract.deliverables : [];
  return contract?.status === "active" && contract?.tradable === true
    && Number(contract?.multiplier) === 100
    && deliverables.length === 1
    && deliverables[0]?.type === "equity"
    && String(deliverables[0]?.symbol || "").toUpperCase() === symbol
    && Number(deliverables[0]?.amount) === 100
    && deliverables[0]?.delayed_settlement !== true;
}

async function alpacaPagedJson(url, keyId, secret, key, maxPages = 8) {
  const results = [];
  let pageToken = "";
  for (let page = 0; page < maxPages; page += 1) {
    const target = new URL(url);
    if (pageToken) target.searchParams.set("page_token", pageToken);
    const result = await alpacaJson(target.toString(), keyId, secret, 10000);
    if (!result.ok) return { ok: false, status: result.status, results: [] };
    const rows = Array.isArray(result.value?.[key]) ? result.value[key]
      : key === "snapshots" && result.value?.snapshots && typeof result.value.snapshots === "object" && !Array.isArray(result.value.snapshots)
        ? Object.entries(result.value.snapshots).map(([symbol, snapshot]) => ({ symbol, ...snapshot })) : null;
    if (!rows) return { ok: false, status: 0, results: [] };
    results.push(...rows);
    pageToken = typeof result.value?.next_page_token === "string" ? result.value.next_page_token
      : typeof result.value?.page_token === "string" ? result.value.page_token : "";
    if (!pageToken) return { ok: true, status: 200, results };
  }
  return { ok: false, status: 0, results: [] };
}

async function alpacaBrainScanRoute(request, env) {
  const url = new URL(request.url);
  if (url.pathname !== "/api/alpaca/brain/scan") return null;
  if (request.method !== "GET") return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "method_not_allowed" }, 405);
  const now = Date.now();
  if (!alpacaBrainRateAllowed(request, now)) return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "rate_limited", retry_after_seconds: 60 }, 429);
  const symbol = (url.searchParams.get("symbol") || "").trim().toUpperCase();
  if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(symbol)) return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "invalid_symbol" }, 400);
  const keyId = env.ALPACA_API_KEY_ID;
  const secret = env.ALPACA_API_SECRET_KEY;
  if (typeof keyId !== "string" || !keyId || typeof secret !== "string" || !secret) {
    return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "market_data_credentials_unavailable", symbol }, 503);
  }
  const cacheKey = `brain:${symbol}`;
  const cached = alpacaBrainCache.get(cacheKey);
  if (cached && now < cached.until) return json(cached.value);

  const sessionDate = newYorkDate(new Date(now));
  const session = await alpacaIexSessionCalendar(sessionDate, keyId, secret);
  if (!session) {
    return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "session_calendar_unavailable", symbol, source: "Alpaca IEX calendar" }, 503);
  }
  if (session.status === "closed" || !session.core_start || !session.core_end || now < Date.parse(session.core_start) || now >= Date.parse(session.core_end)) {
    const value = { schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "market_closed", symbol, received_at: new Date(now).toISOString(), session_calendar: session, setups: [], options: { status: "not_scanned", reason: "The regular session is closed." } };
    alpacaBrainCache.set(cacheKey, { value, until: now + 30000 });
    return json(value);
  }

  let underlyingFeed = "sip";
  let quoteResult = await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/quotes/latest?feed=sip`, keyId, secret);
  if (!quoteResult.ok && quoteResult.status === 403) {
    underlyingFeed = "iex";
    quoteResult = await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/quotes/latest?feed=iex`, keyId, secret);
  }
  if (!quoteResult.ok) {
    const error = quoteResult.status === 401 ? "market_data_authentication_failed"
      : quoteResult.status === 403 ? "underlying_iex_entitlement_unavailable"
        : quoteResult.status === 429 ? "provider_rate_limited" : "underlying_quote_unavailable";
    return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error, symbol, feed: underlyingFeed, source: "Alpaca Market Data" }, 503);
  }
  const underlyingQuote = alpacaQuote(quoteResult.value?.quote);
  const quoteAge = underlyingQuote ? now - Date.parse(underlyingQuote.at) : Number.POSITIVE_INFINITY;
  if (!underlyingQuote || quoteAge < -5000 || quoteAge > 90000 || underlyingQuote.ask <= 0 || underlyingQuote.bid <= 0 || underlyingQuote.ask < underlyingQuote.bid) {
    return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "stale", error: "underlying_quote_stale_or_invalid", symbol, feed: underlyingFeed, source: "Alpaca Market Data", received_at: new Date(now).toISOString(), setups: [] }, 200);
  }
  const underlyingMid = (underlyingQuote.bid + underlyingQuote.ask) / 2;
  const stockSpreadRatio = (underlyingQuote.ask - underlyingQuote.bid) / underlyingMid;
  if (stockSpreadRatio > 0.01) return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "no_setup", error: "underlying_spread_too_wide", symbol, feed: underlyingFeed, underlying_quote: underlyingQuote, setups: [] }, 200);

  const days = 180;
  const start = new Date(now - days * 86400000);
  const barsQuery = new URLSearchParams({
    timeframe: "1Day", start: start.toISOString(), end: new Date(now).toISOString(),
    limit: "1000", adjustment: "split", feed: "iex", sort: "asc",
  });
  const barsResult = await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/bars?${barsQuery}`, keyId, secret);
  if (!barsResult.ok) {
    const error = barsResult.status === 401 || barsResult.status === 403 ? "daily_bar_feed_unavailable"
      : barsResult.status === 429 ? "provider_rate_limited" : "daily_bars_unavailable";
    return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error, symbol, feed: "iex", source: "Alpaca Market Data", setups: [] }, 503);
  }
  const rawBars = Array.isArray(barsResult.value?.bars?.[symbol]) ? barsResult.value.bars[symbol]
    : Array.isArray(barsResult.value?.bars) ? barsResult.value.bars : [];
  const calculated = alpacaBrainIndicators(rawBars, sessionDate);
  const indicators = calculated.value;
  let direction = alpacaBrainDirection(indicators, underlyingMid);
  const barAgeDays = indicators?.as_of
    ? Math.floor((Date.parse(`${sessionDate}T00:00:00Z`) - Date.parse(`${indicators.as_of.slice(0, 10)}T00:00:00Z`)) / 86400000)
    : null;
  if (indicators && (!Number.isFinite(barAgeDays) || barAgeDays < 0 || barAgeDays > 4)) direction = { direction: null, reason: "The latest completed daily bar is stale or future-dated." };
  const underlyingEntry = Math.round(underlyingMid * 100) / 100;
  const riskDistance = indicators ? indicators.atr14 * 1.5 : null;
  const objectiveDistance = indicators ? indicators.atr14 * 3 : null;
  const bearish = direction.direction === "bearish";
  const underlyingInvalidation = indicators && riskDistance > 0 ? Math.round((underlyingEntry + (bearish ? riskDistance : -riskDistance)) * 100) / 100 : null;
  const underlyingObjective = indicators && objectiveDistance > 0 ? Math.round((underlyingEntry + (bearish ? -objectiveDistance : objectiveDistance)) * 100) / 100 : null;
  const equitySetup = direction.direction === "bullish" && riskDistance > 0 ? {
    instrument: "equity", symbol, side: "long", bias: direction.direction,
    entry_limit_reference: underlyingEntry,
    invalidation: underlyingInvalidation,
    objective: underlyingObjective,
    max_loss_per_share_to_invalidation: Math.round(riskDistance * 100) / 100,
    quote_at: underlyingQuote.at, quote_feed: underlyingFeed,
    rationale: direction.reason,
  } : null;

  const today = sessionDate;
  const expiryFrom = new Date(`${today}T00:00:00.000Z`); expiryFrom.setUTCDate(expiryFrom.getUTCDate() + 21);
  const expiryTo = new Date(`${today}T00:00:00.000Z`); expiryTo.setUTCDate(expiryTo.getUTCDate() + 45);
  const dateString = (date) => date.toISOString().slice(0, 10);
  const contractQuery = new URLSearchParams({
    underlying_symbols: symbol, status: "active", type: direction.option_type || "call",
    expiration_date_gte: dateString(expiryFrom), expiration_date_lte: dateString(expiryTo),
    strike_price_gte: String(Math.max(0.01, underlyingMid * 0.8)), strike_price_lte: String(underlyingMid * 1.2),
    show_deliverables: "true", limit: "1000",
  });
  let optionsStatus = "not_scanned";
  let optionsError = direction.direction ? "" : direction.reason;
  let optionSetup = null;
  if (direction.direction) {
    const contractsResult = await alpacaPagedJson(`https://paper-api.alpaca.markets/v2/options/contracts?${contractQuery}`, keyId, secret, "option_contracts");
    if (!contractsResult.ok) {
      optionsStatus = "unavailable";
      optionsError = contractsResult.status === 401 || contractsResult.status === 403 ? "option_contract_metadata_unavailable" : contractsResult.status === 429 ? "provider_rate_limited" : "option_contract_metadata_unavailable";
    } else {
      const chainQuery = new URLSearchParams({
        feed: "indicative", limit: "1000", type: direction.option_type,
        expiration_date_gte: dateString(expiryFrom), expiration_date_lte: dateString(expiryTo),
        strike_price_gte: String(Math.max(0.01, underlyingMid * 0.8)), strike_price_lte: String(underlyingMid * 1.2),
      });
      const chainResult = await alpacaPagedJson(`https://data.alpaca.markets/v1beta1/options/snapshots/${encodeURIComponent(symbol)}?${chainQuery}`, keyId, secret, "snapshots");
      if (!chainResult.ok) {
        optionsStatus = "unavailable";
        optionsError = chainResult.status === 401 || chainResult.status === 403 ? "indicative_options_unavailable" : chainResult.status === 429 ? "provider_rate_limited" : "indicative_options_request_failed";
      } else {
        const metadataBySymbol = new Map(contractsResult.results.map((contract) => [contract.symbol, contract]));
        const candidates = [];
        for (const snapshot of chainResult.results) {
          const contractSymbol = snapshot?.symbol;
          const contract = metadataBySymbol.get(contractSymbol);
          const quote = alpacaQuote(snapshot?.latestQuote);
          const tradeAt = timestamp(snapshot?.latestTrade?.t);
          const delta = finite(snapshot?.greeks?.delta);
          const iv = finite(snapshot?.impliedVolatility);
          const occ = typeof contractSymbol === "string" ? contractSymbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/) : null;
          const encodedExpiration = occ ? `20${occ[2].slice(0, 2)}-${occ[2].slice(2, 4)}-${occ[2].slice(4, 6)}` : null;
          const encodedStrike = occ ? Number(occ[4]) / 1000 : NaN;
          if (!contract || !quote || !alpacaStandardDeliverable(contract, symbol) || contract.type !== direction.option_type
            || String(contract.underlying_symbol || "").toUpperCase() !== symbol
            || !occ || occ[1] !== symbol || occ[3] !== (direction.option_type === "call" ? "C" : "P")
            || encodedExpiration !== contract.expiration_date || encodedStrike !== Number(contract.strike_price)
            || delta === null || iv === null || iv <= 0
            || (direction.option_type === "call" && delta <= 0) || (direction.option_type === "put" && delta >= 0)) continue;
          const quoteTimestamp = Date.parse(quote.at), tradeTimestamp = Date.parse(tradeAt);
          const quoteAgeSeconds = (now - quoteTimestamp) / 1000;
          const tradeAgeSeconds = (now - tradeTimestamp) / 1000;
          if (quoteAgeSeconds < -5 || quoteAgeSeconds > ALPACA_OPTION_QUOTE_MAX_AGE_SECONDS) continue;
          if (quote.bid_size <= 0 || quote.ask_size <= 0 || quote.ask < quote.bid) continue;
          const mid = (quote.bid + quote.ask) / 2;
          const spreadRatio = (quote.ask - quote.bid) / mid;
          if (!(mid > 0) || spreadRatio > 0.10) continue;
          const optionDelta = direction.option_type === "call" ? delta : Math.abs(delta);
          if (optionDelta < 0.45 || optionDelta > 0.65) continue;
          const openInterest = Number(contract.open_interest);
          const oiDate = typeof contract.open_interest_date === "string" ? contract.open_interest_date : null;
          const oiAgeDays = oiDate ? Math.floor((Date.parse(`${today}T00:00:00Z`) - Date.parse(`${oiDate}T00:00:00Z`)) / 86400000) : Infinity;
          if (!Number.isFinite(openInterest) || openInterest < 100 || !Number.isFinite(oiAgeDays) || oiAgeDays < 0 || oiAgeDays > 7) continue;
          const strike = Number(contract.strike_price);
          const expiration = contract.expiration_date;
          const dte = Math.floor((Date.parse(`${expiration}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86400000);
          if (!Number.isFinite(strike) || !expiration || dte < 21 || dte > 45) continue;
          candidates.push({ contract, quote, tradeAt, tradeAgeSeconds, delta, iv, spreadRatio, mid, dte, openInterest, oiDate, optionDelta });
        }
        candidates.sort((a, b) => Math.abs(a.optionDelta - 0.55) - Math.abs(b.optionDelta - 0.55) || a.spreadRatio - b.spreadRatio || b.openInterest - a.openInterest);
        const picked = candidates[0];
        if (picked) {
          const ask = picked.quote.ask;
          const indicativeMidpoint = Math.round(picked.mid * 100) / 100;
          optionSetup = {
            instrument: direction.option_type, symbol: picked.contract.symbol, underlying: symbol,
            expiration: picked.contract.expiration_date, dte: picked.dte,
            strike: Number(picked.contract.strike_price), multiplier: Number(picked.contract.multiplier),
            indicative_midpoint_reference: indicativeMidpoint, indicative_bid: picked.quote.bid, indicative_ask: ask,
            estimated_max_loss_per_contract_at_indicative_ask: Math.round(ask * Number(picked.contract.multiplier) * 100) / 100,
            indicative_bid_size: picked.quote.bid_size, indicative_ask_size: picked.quote.ask_size,
            indicative_spread_percent: Math.round(picked.spreadRatio * 10000) / 100,
            delta: picked.delta, implied_volatility: picked.iv,
            greeks_method: "Alpaca Black-Scholes model",
            open_interest: picked.openInterest, open_interest_as_of: picked.oiDate,
            quote_at: picked.quote.at,
            quote_age_seconds: Math.round((now - Date.parse(picked.quote.at)) / 1000),
            delayed_trade_at: picked.tradeAt,
            delayed_trade_age_seconds: Number.isFinite(picked.tradeAgeSeconds) ? Math.round(picked.tradeAgeSeconds) : null,
            trade_delay_minutes: 15,
            feed: "indicative", price_basis: "modified_indicative_quote",
            execution_status: "broker_quote_required",
            invalidation: underlyingInvalidation,
            underlying_objective: underlyingObjective,
            rationale: `${direction.reason} Research candidate selected from Alpaca's modified indicative quotes, with 21–45 days to expiration, 0.45–0.65 absolute delta, indicative spread at or below 10%, open interest of at least 100, and a standard 100-share deliverable. Indicative prices are reference values; confirm a current broker quote before considering an order.`,
          };
          optionsStatus = "connected";
          optionsError = "";
        } else {
          optionsStatus = "no_contract";
          optionsError = "No contract passed quote-freshness, indicative-spread, Greek, open-interest, and standard-deliverable gates.";
        }
      }
    }
  }

  const setups = [];
  if (equitySetup) setups.push(equitySetup);
  if (optionSetup) setups.push(optionSetup);
  const optionsFeed = optionsStatus === "not_scanned" ? null : "indicative";
  const value = {
    schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2",
    status: setups.length ? "connected" : direction.direction ? "no_option_setup" : "no_setup",
    symbol, received_at: new Date(now).toISOString(),
    feeds: { underlying: `Alpaca ${underlyingFeed.toUpperCase()}`, history: "Alpaca IEX daily bars", options: optionsFeed ? "Alpaca Indicative (modified quotes; trades delayed 15 minutes)" : null },
    session_calendar: session,
    underlying_quote: { ...underlyingQuote, mid: underlyingMid, spread_percent: Math.round(stockSpreadRatio * 10000) / 100, feed: underlyingFeed },
    indicators,
    options: { status: optionsStatus, feed: optionsFeed, quote_basis: optionsFeed ? "modified" : null, trade_delay_minutes: optionsFeed ? 15 : null, execution_pricing: false, error: optionsError || null },
    setups,
  };
  if (alpacaBrainCache.size > 80) alpacaBrainCache.clear();
  alpacaBrainCache.set(cacheKey, { value, until: now + ALPACA_BRAIN_CACHE_MS });
  return json(value);
}

function alpacaStreamRoute(request, env) {
  const url = new URL(request.url);
  if (url.pathname !== "/api/alpaca/stream") return null;
  if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
  if (request.headers.get("Upgrade")?.toLowerCase() !== "websocket") {
    return json({ error: "websocket_upgrade_required" }, 426);
  }
  const origin = request.headers.get("Origin");
  try {
    if (!origin || new URL(origin).origin !== url.origin) return json({ error: "origin_not_allowed" }, 403);
  } catch {
    return json({ error: "origin_not_allowed" }, 403);
  }
  const keyId = env.ALPACA_API_KEY_ID;
  const secret = env.ALPACA_API_SECRET_KEY;
  if (typeof keyId !== "string" || !keyId || typeof secret !== "string" || !secret) {
    return json({ error: "market_data_credentials_unavailable" }, 503);
  }
  if (!alpacaRateAllowed(request, Date.now())) return json({ error: "rate_limited", retry_after_seconds: 60 }, 429);

  let pair;
  try { pair = new WebSocketPair(); }
  catch { return json({ error: "websocket_unavailable" }, 503); }
  const [client, server] = Object.values(pair);
  server.accept();
  let upstream = null;
  let symbols = null;
  let subscribed = false;
  let feed = "sip";
  let attemptedIexFallback = false;
  let closed = false;
  let failureReported = false;
  const send = (value) => {
    if (closed || server.readyState !== WebSocket.OPEN) return;
    try { server.send(JSON.stringify(value)); } catch { closeUpstream(); }
  };
  function closeUpstream(code = 1000, reason = "Client disconnected") {
    if (closed) return;
    closed = true;
    if (upstream && upstream.readyState < WebSocket.CLOSING) {
      try { upstream.close(code, reason); } catch { /* socket already closed */ }
    }
    if (server.readyState < WebSocket.CLOSING) {
      try { server.close(code, reason); } catch { /* socket already closed */ }
    }
  }
  const reportFailure = (error) => {
    if (failureReported || closed) return;
    failureReported = true;
    send({ type: "status", status: "unavailable", feed, error });
  };

  const openFeed = (nextFeed) => {
    if (closed) return;
    feed = nextFeed;
    subscribed = false;
    send({ type: "status", status: "connecting", feed, symbols });
    const socket = new WebSocket(`wss://stream.data.alpaca.markets/v2/${feed}`);
    upstream = socket;
    socket.addEventListener("open", () => {
      if (closed || upstream !== socket) return;
      try { socket.send(JSON.stringify({ action: "auth", key: keyId, secret })); }
      catch { reportFailure("provider_stream_unavailable"); closeUpstream(1011, "Provider connection failed"); }
    });
    socket.addEventListener("message", (providerEvent) => {
      if (closed || upstream !== socket) return;
      let payload;
      try {
        const raw = providerEvent.data;
        const text = typeof raw === "string" ? raw : raw instanceof ArrayBuffer ? new TextDecoder().decode(raw) : "";
        payload = JSON.parse(text);
      } catch { reportFailure("invalid_provider_message"); closeUpstream(1011, "Invalid provider message"); return; }
      const events = Array.isArray(payload) ? payload : [payload];
      for (const item of events) {
        if (item?.T === "success" && item.msg === "authenticated" && !subscribed) {
          subscribed = true;
          send({ type: "status", status: "authenticated", feed, symbols });
          try { socket.send(JSON.stringify({ action: "subscribe", quotes: symbols })); }
          catch { reportFailure("provider_stream_unavailable"); closeUpstream(1011, "Subscription failed"); }
        } else if (item?.T === "subscription" && Array.isArray(item.quotes)) {
          send({ type: "status", status: "subscribed", feed, symbols: item.quotes.filter((symbol) => symbols.includes(symbol)) });
        } else if (item?.T === "error") {
          const detail = String(item.msg || "");
          const invalidCredentials = /invalid (api )?key|invalid credentials|authentication failed|unauthenticated/i.test(detail);
          const entitlement = /subscription|permission|not permitted|not entitled|does not have access|not authorized|unauthorized/i.test(detail);
          if (feed === "sip" && entitlement && !invalidCredentials && !attemptedIexFallback) {
            attemptedIexFallback = true;
            send({ type: "status", status: "fallback", feed: "iex", error: "sip_entitlement_unavailable" });
            try { if (socket.readyState < WebSocket.CLOSING) socket.close(1000, "Use available IEX feed"); } catch { /* socket already closed */ }
            try { openFeed("iex"); }
            catch { reportFailure("provider_stream_unavailable"); closeUpstream(1011, "Provider connection failed"); }
            return;
          }
          const reason = invalidCredentials ? "market_data_authentication_failed"
            : feed === "iex" && entitlement ? "iex_entitlement_unavailable" : "provider_stream_unavailable";
          reportFailure(reason);
          closeUpstream(1011, "Provider rejected stream");
          return;
        } else if (item?.T === "q" && typeof item.S === "string" && symbols.includes(item.S)) {
          const quote = alpacaQuote(item);
          if (quote) send({ type: "quote", symbol: item.S, quote, feed, received_at: new Date().toISOString() });
        }
      }
    });
    socket.addEventListener("error", () => {
      if (upstream !== socket) return;
      reportFailure(feed === "iex" ? "iex_stream_unavailable" : "provider_stream_unavailable");
      closeUpstream(1011, "Provider connection failed");
    });
    socket.addEventListener("close", () => {
      if (!closed && upstream === socket) {
        if (!failureReported) send({ type: "status", status: "disconnected", feed });
        closeUpstream(1011, "Provider disconnected");
      }
    });
  };

  server.addEventListener("message", (event) => {
    if (symbols) {
      send({ type: "status", status: "unavailable", error: "subscription_already_set" });
      return;
    }
    let message;
    try { message = JSON.parse(typeof event.data === "string" ? event.data : ""); }
    catch { message = null; }
    const requested = message?.action === "subscribe" && Array.isArray(message.symbols) ? message.symbols : null;
    const normalized = requested?.map((symbol) => typeof symbol === "string" ? symbol.trim().toUpperCase() : "");
    if (!normalized || normalized.length < 1 || normalized.length > 5
      || normalized.some((symbol) => !/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(symbol))) {
      send({ type: "status", status: "unavailable", error: "invalid_subscription" });
      closeUpstream(1008, "Invalid subscription");
      return;
    }
    symbols = [...new Set(normalized)];
    try {
      openFeed("sip");
    } catch {
      reportFailure("provider_stream_unavailable");
      closeUpstream(1011, "Provider connection failed");
    }
  });
  server.addEventListener("close", () => closeUpstream());
  server.addEventListener("error", () => closeUpstream(1011, "Client connection failed"));
  send({ type: "status", status: "awaiting_subscription", feed: "sip" });
  return new Response(null, { status: 101, webSocket: client });
}

async function alpacaRoute(request, env) {
  const url = new URL(request.url);
  const stream = alpacaStreamRoute(request, env);
  if (stream) return stream;
  const brainScan = await alpacaBrainScanRoute(request, env);
  if (brainScan) return brainScan;
  if (url.pathname !== "/api/alpaca/bars") return null;
  if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);

  const now = Date.now();
  if (!alpacaRateAllowed(request, now)) return json({ error: "rate_limited", retry_after_seconds: 60 }, 429);
  const symbol = (url.searchParams.get("symbol") || "SPY").trim().toUpperCase();
  if (!/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(symbol)) return json({ error: "invalid_symbol" }, 400);
  const days = Number(url.searchParams.get("days") || "90");
  if (![20, 60, 90, 180].includes(days)) return json({ error: "invalid_range" }, 400);

  const keyId = env.ALPACA_API_KEY_ID;
  const secret = env.ALPACA_API_SECRET_KEY;
  if (typeof keyId !== "string" || !keyId || typeof secret !== "string" || !secret) {
    return json({ schema: "SHIPYARD_ALPACA_BARS_V1", status: "unconfigured", error: "market_data_credentials_unavailable", source: "Alpaca Market Data", feed: "iex" }, 503);
  }

  const cacheKey = `${symbol}:${days}`;
  const cached = alpacaBarsCache.get(cacheKey);
  if (cached && now < cached.until) return json(cached.value);

  const sessionDate = newYorkDate(new Date(now));
  const sessionCalendarPromise = alpacaIexSessionCalendar(sessionDate, keyId, secret);
  const end = new Date(now);
  const start = new Date(now - days * 24 * 60 * 60 * 1000);
  const query = new URLSearchParams({
    symbols: symbol,
    timeframe: "1Day",
    start: start.toISOString(),
    end: end.toISOString(),
    limit: "5000",
    adjustment: "split",
    feed: "iex",
    sort: "asc",
  });
  try {
    const response = await fetch(`https://data.alpaca.markets/v2/stocks/bars?${query.toString()}`, {
      method: "GET",
      headers: {
        "APCA-API-KEY-ID": keyId,
        "APCA-API-SECRET-KEY": secret,
        accept: "application/json",
      },
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) {
      const status = response.status === 401 || response.status === 403 ? "credentials_or_feed_rejected"
        : response.status === 429 ? "provider_rate_limited" : "provider_unavailable";
      return json({ schema: "SHIPYARD_ALPACA_BARS_V1", status: "unavailable", error: status, http_status: response.status, source: "Alpaca Market Data", feed: "iex" }, response.status === 429 ? 429 : 502);
    }
    let text;
    try {
      text = await readBoundedBody(response);
    } catch (error) {
      const code = error instanceof Error && error.message === "response too large"
        ? "provider_response_too_large" : "provider_response_unreadable";
      return json({ schema: "SHIPYARD_ALPACA_BARS_V1", status: "unavailable", error: code, source: "Alpaca Market Data", feed: "iex" }, 502);
    }
    let payload;
    try {
      payload = JSON.parse(text);
    } catch {
      return json({ schema: "SHIPYARD_ALPACA_BARS_V1", status: "unavailable", error: "invalid_provider_payload", source: "Alpaca Market Data", feed: "iex" }, 502);
    }
    const rawBars = Array.isArray(payload?.bars?.[symbol]) ? payload.bars[symbol].slice(-500) : [];
    const bars = rawBars.flatMap((raw) => {
      const at = timestamp(raw?.t);
      const open = finite(raw?.o), high = finite(raw?.h), low = finite(raw?.l), close = finite(raw?.c), volume = whole(raw?.v);
      if (!at || open === null || high === null || low === null || close === null || volume === null || low <= 0 || volume < 0 || high < Math.max(open, close, low) || low > Math.min(open, close, high)) return [];
      return [{ at, open, high, low, close, volume, trades: whole(raw?.n), vwap: finite(raw?.vw) }];
    });
    const sessionCalendar = await sessionCalendarPromise;
    const value = {
      schema: "SHIPYARD_ALPACA_BARS_V1",
      status: bars.length ? "connected" : "no_data",
      source: "Alpaca Market Data",
      feed: "iex",
      timeframe: "1Day",
      adjustment: "split",
      symbol,
      requested_days: days,
      received_at: new Date().toISOString(),
      as_of: bars.at(-1)?.at || null,
      session_calendar: sessionCalendar,
      bars,
      authority: "Read-only market data. No account, position, order, or execution data is exposed.",
    };
    if (alpacaBarsCache.size > 80) alpacaBarsCache.clear();
    alpacaBarsCache.set(cacheKey, { value, until: now + ALPACA_CACHE_MS });
    return json(value);
  } catch {
    return json({ schema: "SHIPYARD_ALPACA_BARS_V1", status: "unavailable", error: "provider_request_failed", source: "Alpaca Market Data", feed: "iex" }, 502);
  }
}
