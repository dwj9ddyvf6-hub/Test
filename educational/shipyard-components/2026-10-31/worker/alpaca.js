// Public read-only daily bars. Credentials stay in the Site runtime; this
// adapter never calls Alpaca Trading API account, order, or position routes.
const alpacaBarsCache = new Map();
const alpacaCalendarCache = new Map();
const alpacaRequestWindows = new Map();
const alpacaBrainCache = new Map();
const alpacaNewsCache = new Map();
const alpacaOptionsTradesCache = new Map();
const alpacaMoverCache = new Map();
const ALPACA_CACHE_MS = 30000;
const ALPACA_CALENDAR_CACHE_MS = 6 * 60 * 60 * 1000;
const ALPACA_BRAIN_CACHE_MS = 30000;
const ALPACA_OPTION_QUOTE_MAX_AGE_SECONDS = 90;
const ALPACA_OPTIONS_TRADES_CACHE_MS = 15000;
const ALPACA_MOVERS_CACHE_MS = 15000;
const ALPACA_RATE_WINDOW_MAX_ENTRIES = 512;
const ALPACA_NEWS_CACHE_MS = 15000;
const ALPACA_NEWS_MAX_SYMBOLS_PER_ARTICLE = 100;

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
      signal: AbortSignal.timeout(5000), redirect: "manual",
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

function pruneAlpacaRateWindows(now) {
  for (const [key, item] of alpacaRequestWindows) {
    if (now < item.started || now - item.started >= 60000) alpacaRequestWindows.delete(key);
  }
  while (alpacaRequestWindows.size > ALPACA_RATE_WINDOW_MAX_ENTRIES) {
    const oldestKey = alpacaRequestWindows.keys().next().value;
    if (oldestKey === undefined) break;
    alpacaRequestWindows.delete(oldestKey);
  }
}

function alpacaRateAllowed(request, now) {
  const key = request.headers.get("cf-connecting-ip") || "anonymous";
  const prior = alpacaRequestWindows.get(key);
  const window = !prior || now < prior.started || now - prior.started >= 60000 ? { started: now, count: 0 } : prior;
  window.count += 1;
  alpacaRequestWindows.delete(key);
  alpacaRequestWindows.set(key, window);
  pruneAlpacaRateWindows(now);
  return window.count <= 20;
}

function alpacaBrainRateAllowed(request, now) {
  const key = request.headers.get("cf-connecting-ip") || "anonymous";
  const prior = alpacaRequestWindows.get(`brain:${key}`);
  const window = !prior || now < prior.started || now - prior.started >= 60000 ? { started: now, count: 0 } : prior;
  window.count += 1;
  const windowKey = `brain:${key}`;
  alpacaRequestWindows.delete(windowKey);
  alpacaRequestWindows.set(windowKey, window);
  pruneAlpacaRateWindows(now);
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
      signal: AbortSignal.timeout(timeoutMs), redirect: "manual",
    });
    if (!response.ok) return { ok: false, status: response.status, value: null };
    const value = JSON.parse(await readBoundedBody(response, 1024 * 1024));
    return { ok: true, status: response.status, value };
  } catch {
    return { ok: false, status: 0, value: null };
  }
}

function alpacaNewsDisplayField(value,max){
  if(value===undefined||value===null)return {value:"",valid:true,truncated:false};
  if(typeof value!=="string"||/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(value))return {value:"",valid:false,truncated:false};
  const text=value.trim();return {value:text.slice(0,max),valid:true,truncated:text.length>max};
}
function alpacaNewsTimestamp(value){
  if(typeof value!=="string")return null;
  const match=value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|([+-])(\d{2}):(\d{2}))$/);
  if(!match)return null;
  const year=Number(match[1]),month=Number(match[2]),day=Number(match[3]);
  const hour=Number(match[4]),minute=Number(match[5]),second=Number(match[6]);
  const offsetHour=match[9]===undefined?0:Number(match[9]),offsetMinute=match[10]===undefined?0:Number(match[10]);
  const leapYear=year%4===0&&(year%100!==0||year%400===0),daysInMonth=[31,leapYear?29:28,31,30,31,30,31,31,30,31,30,31][month-1];
  if(month<1||month>12||day<1||day>daysInMonth||hour>23||minute>59||second>59||offsetHour>23||offsetMinute>59)return null;
  const milliseconds=Date.parse(value);return Number.isFinite(milliseconds)?new Date(milliseconds).toISOString():null;
}
function alpacaNewsAgeState(seconds){return !Number.isFinite(seconds)?"unknown":seconds<0?"future_dated":seconds<=90?"current":seconds<=900?"recent":"stale";}
async function alpacaNewsRoute(request,env){
  const url=new URL(request.url);if(url.pathname!=="/api/research/news")return null;
  if(request.method!=="GET")return json({error:"method_not_allowed"},405);
  const allowed=new Set(["symbols","limit"]),keys=[...url.searchParams.keys()];
  if(keys.some(key=>!allowed.has(key))||new Set(keys).size!==keys.length)return json({schema:"SHIPYARD_ALPACA_NEWS_V1",status:"invalid",error:"invalid_request"},400);
  const rawSymbols=url.searchParams.get("symbols"),symbols=rawSymbols===null?[]:rawSymbols.split(",").map(value=>value.trim().toUpperCase());
  if(symbols.length>10||symbols.some(symbol=>! /^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(symbol))||new Set(symbols).size!==symbols.length)return json({schema:"SHIPYARD_ALPACA_NEWS_V1",status:"invalid",error:"invalid_symbols"},400);
  const limit=Number(url.searchParams.get("limit")||"50");if(!Number.isInteger(limit)||limit<1||limit>50)return json({schema:"SHIPYARD_ALPACA_NEWS_V1",status:"invalid",error:"invalid_limit"},400);
  const base={schema:"SHIPYARD_ALPACA_NEWS_V1",source:"Alpaca Market Data News",feed:"alpaca_news",symbols,requested_limit:limit,
    restrictions:{order_submission_enabled:false,account_data_returned:false,provider_timestamps_preserved:true,continuous_stream:false,
      note:"Latest provider articles only. Each article keeps Alpaca's created and updated clocks; REST retrieval does not establish streaming delivery or a real-time news entitlement."}};
  const now=Date.now();
  const keyId=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
  const credentialsConfigured=typeof keyId==="string"&&!!keyId&&typeof secret==="string"&&!!secret;
  const cacheKey=`${symbols.join(",")||"*"}:${limit}`,cached=alpacaNewsCache.get(cacheKey);
  if(credentialsConfigured&&cached&&now<cached.until){const servedAt=new Date(now).toISOString(),articles=cached.value.articles.map(article=>{const ageSeconds=(now-Date.parse(article.created_at))/1000;return {...article,age_seconds:ageSeconds,age_status:alpacaNewsAgeState(ageSeconds)};});return json({...cached.value,served_at:servedAt,cache_hit:true,articles,latest_article_age_seconds:articles.length?articles.reduce((latest,item)=>Math.min(latest,item.age_seconds),Infinity):null});}
  if(!alpacaRateAllowed(request,now))return json({...base,status:"unavailable",error:"rate_limited",retry_after_seconds:60},429);
  if(!credentialsConfigured)return json({...base,status:"unavailable",error:"market_data_credentials_unavailable"},503);
  if(request.signal.aborted)return json({...base,status:"cancelled"},408);
  const query=new URLSearchParams({limit:String(limit),sort:"desc",include_content:"false"});if(symbols.length)query.set("symbols",symbols.join(","));
  const response=await alpacaJson(`https://data.alpaca.markets/v1beta1/news?${query}`,keyId,secret,8000),retrieved=Date.now();
  if(request.signal.aborted)return json({...base,status:"cancelled"},408);
  if(!response.ok){const error=response.status===401?"market_data_authentication_failed":response.status===403?"news_feed_not_entitled":response.status===429?"provider_rate_limited":"news_provider_unavailable";
    return json({...base,status:"unavailable",error,retrieved_at:new Date(retrieved).toISOString()},response.status===429?429:502);}
  const raw=response.value;if(!raw||typeof raw!=="object"||Array.isArray(raw)||!Array.isArray(raw.news)||raw.news.length>limit)return json({...base,status:"invalid",error:"invalid_provider_payload",retrieved_at:new Date(retrieved).toISOString()},502);
  const seen=new Set(),articles=[],validationIssues=Object.create(null);let invalidArticleCount=0,partialArticleCount=0;
  const issue=(issues,code)=>{issues.push(code);validationIssues[code]=(validationIssues[code]||0)+1;};
  for(const item of raw.news){
    const issues=[];
    if(!item||typeof item!=="object"||Array.isArray(item)){invalidArticleCount++;issue(issues,"invalid_article_shape");continue;}
    if(!Number.isSafeInteger(item.id)||item.id<1){invalidArticleCount++;issue(issues,"invalid_article_id");continue;}
    if(seen.has(item.id)){invalidArticleCount++;issue(issues,"duplicate_article_id");continue;}
    const headline=alpacaNewsDisplayField(item.headline,500),createdAt=alpacaNewsTimestamp(item.created_at),updatedAt=alpacaNewsTimestamp(item.updated_at);
    if(!headline.valid||!headline.value){invalidArticleCount++;issue(issues,"invalid_headline");continue;}
    if(!createdAt){invalidArticleCount++;issue(issues,"invalid_created_at");continue;}
    if(!updatedAt){invalidArticleCount++;issue(issues,"invalid_updated_at");continue;}
    if(headline.truncated)issue(issues,"headline_truncated");
    const summaryField=alpacaNewsDisplayField(item.summary,3000),authorField=alpacaNewsDisplayField(item.author,160),sourceField=alpacaNewsDisplayField(item.source,120);
    if(!summaryField.valid)issue(issues,"invalid_summary");else if(summaryField.truncated)issue(issues,"summary_truncated");
    if(!authorField.valid)issue(issues,"invalid_author");else if(authorField.truncated)issue(issues,"author_truncated");
    if(!sourceField.valid)issue(issues,"invalid_source");else if(sourceField.truncated)issue(issues,"source_truncated");
    const summary=summaryField.value,author=authorField.value,sourceName=sourceField.value;
    let articleUrl=null;
    if(item.url!==undefined&&item.url!==null){
      if(typeof item.url==="string"&&item.url.length<=2048){try{const parsed=new URL(item.url);if(parsed.protocol==="https:"&&!parsed.username&&!parsed.password)articleUrl=parsed.href;else issue(issues,"unsafe_article_url");}catch{issue(issues,"invalid_article_url");}}
      else issue(issues,"invalid_article_url");
    }
    const articleSymbols=[];
    if(item.symbols!==undefined){
      if(!Array.isArray(item.symbols))issue(issues,"invalid_symbols_shape");
      else {
        if(item.symbols.length>ALPACA_NEWS_MAX_SYMBOLS_PER_ARTICLE)issue(issues,"symbols_truncated");
        for(const value of item.symbols.slice(0,ALPACA_NEWS_MAX_SYMBOLS_PER_ARTICLE)){
          if(typeof value!=="string"||! /^[A-Za-z0-9][A-Za-z0-9./-]{0,19}$/.test(value)){issue(issues,"invalid_symbol");continue;}
          const normalized=value.toUpperCase();if(!articleSymbols.includes(normalized))articleSymbols.push(normalized);
        }
      }
    }
    seen.add(item.id);
    const ageSeconds=(retrieved-Date.parse(createdAt))/1000;
    const uniqueIssues=[...new Set(issues)];if(uniqueIssues.length)partialArticleCount++;
    articles.push({id:item.id,headline:headline.value,summary,author,source:sourceName,created_at:createdAt,updated_at:updatedAt,url:articleUrl,symbols:articleSymbols,
      age_seconds:ageSeconds,age_status:alpacaNewsAgeState(ageSeconds),data_quality:uniqueIssues.length?"partial":"complete",quality_issues:uniqueIssues});
  }
  articles.sort((a,b)=>Date.parse(b.updated_at)-Date.parse(a.updated_at)||a.id-b.id);
  const hasValidationIssues=invalidArticleCount>0||partialArticleCount>0;
  const status=articles.length?(hasValidationIssues?"partial":"connected"):(raw.news.length?"invalid":"no_articles");
  const value={...base,status,...(status==="invalid"?{error:"provider_articles_rejected"}:{}),retrieved_at:new Date(retrieved).toISOString(),served_at:new Date(retrieved).toISOString(),cache_hit:false,
    source_article_count:raw.news.length,invalid_article_count:invalidArticleCount,partial_article_count:partialArticleCount,validation_issues:validationIssues,
    article_count:articles.length,articles,latest_article_age_seconds:articles.length?articles.reduce((latest,item)=>Math.min(latest,item.age_seconds),Infinity):null,
    next_page_available:typeof raw.next_page_token==="string"&&raw.next_page_token.length>0};
  if(alpacaNewsCache.size>100)alpacaNewsCache.clear();alpacaNewsCache.set(cacheKey,{value,until:retrieved+ALPACA_NEWS_CACHE_MS});return json(value);
}

async function alpacaOptionsTradesRoute(request, env) {
  const url = new URL(request.url);
  if (url.pathname !== "/api/alpaca/options/trades/latest") return null;
  const base = { schema: "SHIPYARD_ALPACA_OPTIONS_TRADES_V1", status: "unavailable", source: "Alpaca Indicative options trades", feed: "indicative", delay_minutes: 15, requested_at: new Date().toISOString(), retrieved_at: null, symbols: [], trades: [], restrictions: { market_data_only: true, opra: false, whole_market_flow: false, aggressor_side_inferred: false, account_data: false, orders: false } };
  if (request.method !== "GET") return json({ ...base, status: "invalid", error: "method_not_allowed" }, 405);
  const keys = [...url.searchParams.keys()];
  const raw = url.searchParams.get("symbols");
  if (keys.length !== 1 || keys[0] !== "symbols" || !raw || raw.length > 2200) return json({ ...base, status: "invalid", error: "invalid_symbols" }, 400);
  const symbols = raw.split(",").map(value => value.trim().toUpperCase());
  const pattern = /^[A-Z]{1,6}\d{6}[CP]\d{8}$/;
  if (!symbols.length || symbols.length > 100 || symbols.some(value => !pattern.test(value)) || new Set(symbols).size !== symbols.length) return json({ ...base, status: "invalid", error: "invalid_symbols" }, 400);
  base.symbols = symbols;
  const now = Date.now();
  const keyId = env?.ALPACA_API_KEY_ID, secret = env?.ALPACA_API_SECRET_KEY;
  const credentialsConfigured = typeof keyId === "string" && !!keyId && typeof secret === "string" && !!secret;
  const cacheKey = symbols.join(","), cached = alpacaOptionsTradesCache.get(cacheKey);
  if (credentialsConfigured && cached && now < cached.until) return json({ ...cached.value, served_at: new Date(now).toISOString(), cache_hit: true });
  if (!alpacaRateAllowed(request, now)) return json({ ...base, status: "unavailable", error: "rate_limited", retry_after_seconds: 60 }, 429);
  if (!credentialsConfigured) return json({ ...base, status: "unavailable", error: "market_data_credentials_unavailable" }, 503);
  const query = new URLSearchParams({ symbols: symbols.join(","), feed: "indicative" });
  const result = await alpacaJson(`https://data.alpaca.markets/v1beta1/options/trades/latest?${query}`, keyId, secret, 8000);
  if (!result.ok) {
    const error = result.status === 401 ? "market_data_authentication_failed" : result.status === 403 ? "indicative_options_not_entitled" : result.status === 429 ? "provider_rate_limited" : "provider_unavailable";
    return json({ ...base, status: "unavailable", error, provider_status: result.status }, result.status === 429 ? 429 : 502);
  }
  const payload = result.value;
  if (!payload || typeof payload !== "object" || !payload.trades || typeof payload.trades !== "object" || Array.isArray(payload.trades)) return json({ ...base, status: "unavailable", error: "invalid_provider_payload" }, 502);
  const received = new Date().toISOString(), trades = [];
  for (const symbol of symbols) {
    const rawTrade = payload.trades[symbol];
    if (rawTrade === undefined) continue;
    const at = timestamp(rawTrade?.t), price = finite(rawTrade?.p), size = whole(rawTrade?.s);
    const exchange = bounded(rawTrade?.x, 8, /^[A-Za-z0-9]+$/), condition = bounded(rawTrade?.c, 32, /^[A-Za-z0-9 ,_-]*$/);
    if (!at || price === null || price <= 0 || size === null || size < 1 || !exchange) continue;
    const ageSeconds = (Date.parse(received) - Date.parse(at)) / 1000;
    if (!Number.isFinite(ageSeconds) || ageSeconds < -5) continue;
    trades.push({ symbol, at, price, size, exchange, condition: condition || null, age_seconds: ageSeconds, age_status: ageSeconds <= 900 ? "within_indicative_delay_window" : "older", premium_usd: price * size * 100 });
  }
  trades.sort((a,b) => Date.parse(b.at) - Date.parse(a.at));
  const value = { ...base, status: trades.length ? trades.length === symbols.length ? "connected" : "partial" : "no_trades", retrieved_at: received, received_at: received, served_at: received, cache_hit: false, requested_count: symbols.length, returned_count: trades.length, trades, coverage: { requested_contracts: symbols.length, contracts_with_latest_trade: trades.length, complete_market_tape: false, omitted_contracts: symbols.filter(symbol => !trades.some(trade => trade.symbol === symbol)) } };
  if (alpacaOptionsTradesCache.size > 100) alpacaOptionsTradesCache.clear();
  alpacaOptionsTradesCache.set(cacheKey, { value, until: now + ALPACA_OPTIONS_TRADES_CACHE_MS });
  return json(value);
}

async function alpacaMoversRoute(request, env) {
  const url = new URL(request.url);
  if (url.pathname !== "/api/alpaca/screener/movers") return null;
  const base = { schema: "SHIPYARD_ALPACA_MOVERS_V1", status: "unavailable", source: "Alpaca Market Data", feed: "sip", market_type: "stocks", requested_at: new Date().toISOString(), received_at: null, last_updated: null, gainers: [], losers: [], restrictions: { data_scope: "provider top movers", whole_market_fundamentals: false, account_data: false, orders: false } };
  if (request.method !== "GET") return json({ ...base, status: "invalid", error: "method_not_allowed" }, 405);
  const keys = [...url.searchParams.keys()], rawTop = url.searchParams.get("top") || "20";
  if (keys.some(key => key !== "top") || keys.length > 1 || !/^(?:[1-9]|[1-4]\d|50)$/.test(rawTop)) return json({ ...base, status: "invalid", error: "invalid_request" }, 400);
  const now = Date.now();
  const keyId = env?.ALPACA_API_KEY_ID, secret = env?.ALPACA_API_SECRET_KEY;
  const credentialsConfigured = typeof keyId === "string" && !!keyId && typeof secret === "string" && !!secret;
  const cacheKey = rawTop, cached = alpacaMoverCache.get(cacheKey);
  if (credentialsConfigured && cached && now < cached.until) return json({ ...cached.value, served_at: new Date(now).toISOString(), cache_hit: true });
  if (!alpacaRateAllowed(request, now)) return json({ ...base, status: "unavailable", error: "rate_limited", retry_after_seconds: 60 }, 429);
  if (!credentialsConfigured) return json({ ...base, error: "market_data_credentials_unavailable" }, 503);
  const result = await alpacaJson(`https://data.alpaca.markets/v1beta1/screener/stocks/movers?top=${rawTop}`, keyId, secret, 8000);
  if (!result.ok) {
    const error = result.status === 401 ? "market_data_authentication_failed" : result.status === 403 ? "sip_screener_not_entitled" : result.status === 429 ? "provider_rate_limited" : "provider_unavailable";
    return json({ ...base, error, provider_status: result.status }, result.status === 429 ? 429 : 502);
  }
  const payload = result.value;
  const row = value => value && typeof value === "object" && !Array.isArray(value) && typeof value.symbol === "string" && /^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(value.symbol)
    && finite(value.price) !== null && finite(value.change) !== null && finite(value.percent_change) !== null
    ? { symbol: value.symbol, price: finite(value.price), change: finite(value.change), percent_change: finite(value.percent_change) } : null;
  const parseRows = rows => {
    if (!Array.isArray(rows) || rows.length > 50) return null;
    const parsed = rows.map(row);
    if (parsed.some(value => !value) || new Set(parsed.map(value => value.symbol)).size !== parsed.length) return null;
    return parsed;
  };
  const gainers = parseRows(payload?.gainers), losers = parseRows(payload?.losers), lastUpdated = timestamp(payload?.last_updated);
  if (payload?.market_type !== "stocks" || !gainers || !losers || !lastUpdated || gainers.length > Number(rawTop) || losers.length > Number(rawTop)) return json({ ...base, error: "invalid_provider_payload" }, 502);
  const received = new Date().toISOString(), age = (Date.parse(received) - Date.parse(lastUpdated)) / 1000;
  const value = { ...base, status: "connected", received_at: received, served_at: received, cache_hit: false, last_updated: lastUpdated, age_seconds: age, age_status: age < -5 ? "future_dated" : age <= 90 ? "current" : "stale", gainers, losers, returned_count: gainers.length + losers.length };
  if (alpacaMoverCache.size > 10) alpacaMoverCache.clear();
  alpacaMoverCache.set(cacheKey, { value, until: now + ALPACA_MOVERS_CACHE_MS });
  return json(value);
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

function alpacaBrainDelivery(value, at) {
  const session=value.session_calendar;
  const base={...value,evaluated_at:new Date(at).toISOString()};
  if(!session || session.status!=='open' || at<Date.parse(session.core_start) || at>=Date.parse(session.core_end)) return {...base,status:'market_closed',setups:[],options:{...value.options,status:'not_scanned',error:'regular_session_closed_at_delivery'}};
  const age=(at-Date.parse(value.underlying_quote?.at))/1000;
  if(!Number.isFinite(age)||age < -5||age>90)return {...base,status:'stale',error:'underlying_quote_stale_at_delivery',setups:[],options:{...value.options,status:'not_scanned',error:'underlying_quote_stale_at_delivery'}};
  let dropped=false, dropReason=null;
  const setups=(value.setups||[]).flatMap(setup=>{
    if(setup.instrument==='equity')return [setup];
    const quoteAge=(at-Date.parse(setup.quote_at))/1000;
    if(!Number.isFinite(quoteAge)||quoteAge < -5||quoteAge>ALPACA_OPTION_QUOTE_MAX_AGE_SECONDS
      || (setup.feed==='tradier'&&!brokerTradierQuoteFresh(setup,at))){dropped=true;dropReason='option_quote_stale_at_delivery';return [];}
    const greekAge=(at-Date.parse(setup.greeks_as_of || ''))/1000;
    if(setup.feed==='tradier'&&(!Number.isFinite(greekAge)||greekAge < -5||greekAge>75*60)){dropped=true;dropReason='option_greeks_stale_at_delivery';return [];}
    const tradeAge=(at-Date.parse(setup.delayed_trade_at))/1000;
    return [{...setup,quote_age_seconds:Math.round(quoteAge),...(setup.feed==='tradier'?{greeks_age_minutes:Math.round(greekAge/60)}:{}),delayed_trade_age_seconds:Number.isFinite(tradeAge)?Math.round(tradeAge):null}];
  });
  return {...base,underlying_quote_age_seconds:age,setups,status:dropped?(setups.length?'connected':'no_option_setup'):value.status,options:dropped?{...value.options,status:'stale',error:dropReason}:value.options};
}

async function alpacaBrainScanRoute(request, env) {
  const url = new URL(request.url);
  if (url.pathname !== "/api/alpaca/brain/scan") return null;
  if (request.method !== "GET") return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "method_not_allowed" }, 405);
  const now = Date.now();
  const symbol = (url.searchParams.get("symbol") || "").trim().toUpperCase();
  if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(symbol)) return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "invalid_symbol" }, 400);
  const keyId = env.ALPACA_API_KEY_ID;
  const secret = env.ALPACA_API_SECRET_KEY;
  const credentialsConfigured = typeof keyId === "string" && !!keyId && typeof secret === "string" && !!secret;
  const cacheKey = `brain:${symbol}`;
  const cached = alpacaBrainCache.get(cacheKey);
  if (credentialsConfigured && cached && now < cached.until) {
    const delivered=alpacaBrainDelivery(cached.value,now);
    if(delivered.status!=="stale")return json({...delivered,served_at:new Date(now).toISOString(),cache_hit:true});
    alpacaBrainCache.delete(cacheKey);
  }
  if (!alpacaBrainRateAllowed(request, now)) return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "rate_limited", retry_after_seconds: 60 }, 429);
  if (!credentialsConfigured) return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "market_data_credentials_unavailable", symbol }, 503);

  const sessionDate = newYorkDate(new Date(now));
  const session = await alpacaIexSessionCalendar(sessionDate, keyId, secret);
  if (!session) {
    return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: "session_calendar_unavailable", symbol, source: "Alpaca IEX calendar" }, 503);
  }
  const sessionCheckedAt=Date.now();
  if (session.status === "closed" || !session.core_start || !session.core_end || sessionCheckedAt < Date.parse(session.core_start) || sessionCheckedAt >= Date.parse(session.core_end)) {
    const value = { schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "market_closed", symbol, received_at: new Date(sessionCheckedAt).toISOString(), served_at:new Date(sessionCheckedAt).toISOString(),cache_hit:false,evaluated_at:new Date(sessionCheckedAt).toISOString(), session_calendar: session, setups: [], options: { status: "not_scanned", reason: "The regular session is closed." } };
    alpacaBrainCache.set(cacheKey, { value, until: sessionCheckedAt + 30000 });
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
  const quoteAge = underlyingQuote ? Date.now() - Date.parse(underlyingQuote.at) : Number.POSITIVE_INFINITY;
  if (!underlyingQuote || quoteAge < -5000 || quoteAge > 90000 || underlyingQuote.ask <= 0 || underlyingQuote.bid <= 0 || underlyingQuote.ask < underlyingQuote.bid) {
    return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "stale", error: "underlying_quote_stale_or_invalid", symbol, feed: underlyingFeed, source: "Alpaca Market Data", received_at: new Date(Date.now()).toISOString(), evaluated_at:new Date(Date.now()).toISOString(), setups: [] }, 200);
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
  if(barsResult.value?.next_page_token || (barsResult.value?.symbol && barsResult.value.symbol!==symbol) || rawBars.length>1000 || rawBars.some((b,i)=>{
    const t=Date.parse(b?.t),values=[b?.o,b?.h,b?.l,b?.c];
    return !shipyardProviderInstant(b?.t)||t<start.getTime()||t>now||!values.every(x=>Number.isFinite(x)&&x>0)||b.h<Math.max(b.o,b.c,b.l)||b.l>Math.min(b.o,b.c,b.h)||(i>0&&(t<=Date.parse(rawBars[i-1].t)||newYorkDate(new Date(t))<=newYorkDate(new Date(rawBars[i-1].t))));
  }))return json({schema:"SHIPYARD_TRADE_BRAIN_SCAN_V2",status:"unavailable",error:"daily_history_invalid_or_incomplete",symbol,setups:[]},503);
  let expectedCompletedDate=null;
  for(let back=1;back<=8;back++){
    const date=new Date(Date.parse(sessionDate+'T12:00:00Z')-back*86400000).toISOString().slice(0,10);
    const prior=await alpacaIexSessionCalendar(date,keyId,secret);
    if(!prior)return json({schema:"SHIPYARD_TRADE_BRAIN_SCAN_V2",status:"unavailable",error:"prior_session_calendar_unavailable",symbol,setups:[]},503);
    if(prior.status==='open'){expectedCompletedDate=date;break;}
  }
  const completed=rawBars.filter(b=>newYorkDate(new Date(b.t))<sessionDate);
  if(!expectedCompletedDate || !completed.length || newYorkDate(new Date(completed.at(-1).t))!==expectedCompletedDate)return json({schema:"SHIPYARD_TRADE_BRAIN_SCAN_V2",status:"unavailable",error:"latest_completed_daily_session_missing",symbol,setups:[]},503);
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
  let optionsFeed = null;
  if (direction.direction) {
    let tradierCredentials;
    try { tradierCredentials = await brokerCredentials(env, "tradier"); }
    catch (error) {
      return json({ schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2", status: "unavailable", error: brokerCredentialError(error), symbol, setups: [] }, 503);
    }
    if (tradierCredentials?.token) {
      const tradierResult = await brokerTradierOptionSetup(tradierCredentials, symbol, direction.option_type, underlyingMid, sessionDate, underlyingInvalidation, underlyingObjective);
      optionsStatus = tradierResult.status;
      optionsError = tradierResult.error || "";
      optionSetup = tradierResult.setup;
      optionsFeed = "tradier";
    } else {
      optionsFeed = "indicative";
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
          const candidateNow=Date.now();
          const quoteAgeSeconds = (candidateNow - quoteTimestamp) / 1000;
          const tradeAgeSeconds = (candidateNow - tradeTimestamp) / 1000;
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
  }

  const setups = [];
  if (equitySetup) setups.push(equitySetup);
  if (optionSetup) setups.push(optionSetup);
  if (optionsStatus === "not_scanned") optionsFeed = null;
  if (optionsStatus !== "not_scanned" && !optionsFeed) optionsFeed = "indicative";
  const completedAt=Date.now();
  const value = {
    schema: "SHIPYARD_TRADE_BRAIN_SCAN_V2",
    status: setups.length ? "connected" : direction.direction ? "no_option_setup" : "no_setup",
    symbol, received_at: new Date(completedAt).toISOString(),
    daily_history_quality:{complete_provider_response:true,latest_completed_session:expectedCompletedDate,provider_revisions_possible:true},
    feeds: { underlying: `Alpaca ${underlyingFeed.toUpperCase()}`, history: "Alpaca IEX daily bars", options: optionsFeed === "tradier" ? "Tradier real-time option quotes; hourly provider Greeks" : optionsFeed === "indicative" ? "Alpaca Indicative (modified quotes; trades delayed 15 minutes)" : null },
    session_calendar: session,
    underlying_quote: { ...underlyingQuote, mid: underlyingMid, spread_percent: Math.round(stockSpreadRatio * 10000) / 100, feed: underlyingFeed },
    indicators,
    options: { status: optionsStatus, feed: optionsFeed, quote_basis: optionsFeed === "tradier" ? "live_bid_ask" : optionsFeed === "indicative" ? "modified" : null, trade_delay_minutes: optionsFeed === "indicative" ? 15 : optionsFeed === "tradier" ? 0 : null, execution_pricing: optionsFeed === "tradier", error: optionsError || null },
    setups,
  };
  if (alpacaBrainCache.size > 80) alpacaBrainCache.clear();
  const delivered=alpacaBrainDelivery(value,completedAt);
  if(!["stale","market_closed"].includes(delivered.status))alpacaBrainCache.set(cacheKey, { value, until: Math.min(completedAt + ALPACA_BRAIN_CACHE_MS,Date.parse(session.core_end)) });
    return json({...delivered,served_at:new Date(completedAt).toISOString(),cache_hit:false});
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
  const news = await alpacaNewsRoute(request, env);
  if (news) return news;
  const optionTrades = await alpacaOptionsTradesRoute(request, env);
  if (optionTrades) return optionTrades;
  const movers = await alpacaMoversRoute(request, env);
  if (movers) return movers;
  const brainScan = await alpacaBrainScanRoute(request, env);
  if (brainScan) return brainScan;
  if (url.pathname !== "/api/alpaca/bars") return null;
  if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);

  const now = Date.now();
  const symbol = (url.searchParams.get("symbol") || "SPY").trim().toUpperCase();
  if (!/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(symbol)) return json({ error: "invalid_symbol" }, 400);
  const days = Number(url.searchParams.get("days") || "90");
  if (![20, 60, 90, 180, 370].includes(days)) return json({ error: "invalid_range" }, 400);

  const adjustment = url.searchParams.get("adjustment") || "split";
  if (!["raw", "split", "all"].includes(adjustment)) return json({ error: "invalid_adjustment" }, 400);

  const keyId = env.ALPACA_API_KEY_ID;
  const secret = env.ALPACA_API_SECRET_KEY;
  const credentialsConfigured = typeof keyId === "string" && !!keyId && typeof secret === "string" && !!secret;

  const cacheKey = `${symbol}:${days}:${adjustment}`;
  const cached = alpacaBarsCache.get(cacheKey);
  if (credentialsConfigured && cached && now < cached.until) return json({ ...cached.value, served_at: new Date(now).toISOString(), cache_hit: true });
  if (!alpacaRateAllowed(request, now)) return json({ error: "rate_limited", retry_after_seconds: 60 }, 429);
  if (!credentialsConfigured) return json({ schema: "SHIPYARD_ALPACA_BARS_V1", status: "unconfigured", error: "market_data_credentials_unavailable", source: "Alpaca Market Data", feed: "iex" }, 503);

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
    adjustment,
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
      signal: AbortSignal.timeout(8000), redirect: "manual",
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
    if (payload?.next_page_token) return json({schema:"SHIPYARD_ALPACA_BARS_V1",status:"unavailable",error:"provider_history_incomplete",source:"Alpaca Market Data",feed:"iex",adjustment},502);
    if (!Array.isArray(payload?.bars?.[symbol])) return json({schema:"SHIPYARD_ALPACA_BARS_V1",status:"unavailable",error:"invalid_daily_history_schema",feed:"iex",adjustment},502);
    const rawBars = Array.isArray(payload?.bars?.[symbol]) ? payload.bars[symbol] : [];
    if (rawBars.length > 500) return json({schema:"SHIPYARD_ALPACA_BARS_V1",status:"unavailable",error:"provider_history_bound_exceeded"},502);
    const bars = rawBars.flatMap((raw) => {
      const at = timestamp(raw?.t);
      const open = finite(raw?.o), high = finite(raw?.h), low = finite(raw?.l), close = finite(raw?.c), volume = whole(raw?.v);
      if (!at || open === null || high === null || low === null || close === null || volume === null || low <= 0 || volume < 0 || high < Math.max(open, close, low) || low > Math.min(open, close, high)) return [];
      return [{ at, open, high, low, close, volume, trades: whole(raw?.n), vwap: finite(raw?.vw) }];
    });
    if (rawBars.some(raw=>!shipyardProviderInstant(raw?.t) || Date.parse(raw.t)<start.getTime() || Date.parse(raw.t)>end.getTime()) || bars.length !== rawBars.length || bars.some((bar,index)=>index>0 && (bar.at<=bars[index-1].at || newYorkDate(new Date(bar.at))<=newYorkDate(new Date(bars[index-1].at))))) return json({schema:"SHIPYARD_ALPACA_BARS_V1",status:"unavailable",error:"invalid_daily_history",feed:"iex",adjustment},502);
    const sessionCalendar = await sessionCalendarPromise;
    const receivedAt = new Date().toISOString();
    const value = {
      schema: "SHIPYARD_ALPACA_BARS_V1",
      status: bars.length ? "connected" : "no_data",
      source: "Alpaca Market Data",
      feed: "iex",
      timeframe: "1Day",
      adjustment,
      symbol,
      requested_days: days,
      request_window: {start:start.toISOString(),end:end.toISOString()},
      complete_response: bars.length === rawBars.length,
      excluded_invalid_rows: rawBars.length-bars.length,
      historical_availability_known: false,
      missing_intervals_filled: false,
      received_at: receivedAt,
      served_at: receivedAt,
      cache_hit: false,
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
