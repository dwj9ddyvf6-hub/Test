// Public read-only daily bars. Credentials stay in the Site runtime; this
// adapter never calls Alpaca Trading API account, order, or position routes.
const alpacaBarsCache = new Map();
const alpacaCalendarCache = new Map();
const alpacaRequestWindows = new Map();
const ALPACA_CACHE_MS = 30000;
const ALPACA_CALENDAR_CACHE_MS = 6 * 60 * 60 * 1000;

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
        const coreEnd = timestamp(entry.core_end);
        return coreEnd ? { market: "IEX", date, status: "open", core_end: coreEnd, source: "alpaca_iex_calendar_v3", received_at: new Date().toISOString() } : null;
      })()
      : { market: "IEX", date, status: "closed", core_end: null, source: "alpaca_iex_calendar_v3", received_at: new Date().toISOString() };
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

async function alpacaRoute(request, env) {
  const url = new URL(request.url);
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
