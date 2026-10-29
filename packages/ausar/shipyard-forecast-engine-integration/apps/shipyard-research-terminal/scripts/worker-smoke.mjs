import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { runInNewContext } from "node:vm";
import worker from "../dist/server/index.js";

const origin = "https://shipyard-smoke.invalid";
const env = {};

async function request(path, init = {}) {
  return worker.fetch(new Request(new URL(path, origin), init), env);
}

const home = await request("/");
assert.equal(home.status, 200, "the browser entry point is served");
assert.match(home.headers.get("content-type") ?? "", /text\/html/);
const homeHtml = await home.text();

const favicon = await request("/favicon.ico");
const svg = await request("/favicon.svg");
assert.equal(favicon.status, 200, "the conventional favicon path resolves");
assert.equal(favicon.headers.get("content-type"), "image/svg+xml");
assert.equal(svg.status, 200);
const faviconBytes = Buffer.from(await favicon.arrayBuffer());
const svgBytes = Buffer.from(await svg.arrayBuffer());
assert.deepEqual(
  faviconBytes,
  svgBytes,
  "favicon.ico serves the reviewed SVG asset",
);

const appResponse = await request("/app.js");
assert.equal(appResponse.status, 200);
const appSource = await appResponse.text();
assert.match(appSource, /refreshes every five minutes while open/i);
assert.match(appSource, /LATEST COMPLETED CLOSE/);
assert.match(appSource, /LIVE_BARS_REFRESH_MS = 5 \* 60 \* 1000/);
const overviewShortcut = appSource.match(/<button class="overview-shortcut"[\s\S]*?<\/button>/)?.[0] ?? "";
assert.match(overviewShortcut, /Home/);
assert.doesNotMatch(overviewShortcut, /Market overview/, "the home shortcut label is distinct from the Markets navigation item");
assert.doesNotMatch(appSource, /Not investment advice|Confirm data rights|Research tool only\./i);
assert.doesNotMatch(appSource, /<b>(?:Interpretation boundary|Runtime boundary|Clean-room implementation boundary|Contract boundary|Method boundary|Public-site boundary)<\/b>/i, "visible method and scope notes use concise labels");
const overviewRenderer = appSource.match(/function renderOverview\(\) \{[\s\S]*?\n\}/)?.[0] ?? "";
assert.match(overviewRenderer, /selectCompletedDailyBars/);
assert.match(overviewRenderer, /overview-table/);
assert.doesNotMatch(overviewRenderer, /flowTrades|const indexes|const sectors|synthetic/i, "the landing page uses provider bars rather than generated fixtures");
const overviewResponse = await request("/market-overview.mjs");
assert.equal(overviewResponse.status, 200, "the numerical summary used by the live overview is served");
const overviewSource = await overviewResponse.text();
assert.ok(overviewSource.includes("export function summarizeDailyBars"));
assert.ok(overviewSource.includes("export function formatSessionDate"), "market date formatting is served from the shared helper");
assert.ok(overviewSource.includes("timeZone: 'America/New_York'"), "market dates use the exchange timezone");
assert.ok(appSource.includes("marketSessionDate"), "all market views use the shared exchange-date formatter");
assert.ok(!appSource.includes("new Date(bar.at).toLocaleDateString("), "bar dates are not formatted in visitor-local time");
const adapterResponse = await request("/research-adapters.mjs");
assert.equal(adapterResponse.status, 200, "the calendar-aware research adapter is served");
const adapterSource = await adapterResponse.text();
assert.ok(adapterSource.includes("NYSE_EARLY_CLOSES"), "the NYSE schedule remains available as a fallback");
assert.ok(adapterSource.includes("export function simpleRsi14"), "market views share one indicator implementation");
assert.ok(adapterSource.includes("alpaca_iex"), "the Alpaca IEX session calendar governs when present");
assert.ok(adapterSource.includes("2028-07-03"), "the published July 2028 early close is embedded for fallback");
assert.ok(adapterSource.includes("nonTradingDateBarExcluded"), "non-session bars are excluded from calculations");
assert.ok(adapterSource.includes("Historical session coverage and point-in-time availability are not verified"), "current-date calendar coverage is distinguished from historical completeness");
assert.ok(appSource.includes("simpleRsi14"), "the chart and engine use the shared RSI calculation");
assert.ok(appSource.includes("function renderConvergenceEngine"), "the convergence capability view is present");
assert.ok(appSource.includes("importConvergenceEvidenceCsv"), "the local evidence intake handler is present");
const convergenceResponse = await request("/convergence-engine.mjs");
assert.equal(convergenceResponse.status, 200, "the survivor catalog and local CSV contract are served");
const convergenceSource = await convergenceResponse.text();
assert.match(convergenceSource, /export const SURVIVOR_CATALOG/);
assert.match(convergenceSource, /export const FAMILY_CROSSWALK/);
assert.match(convergenceSource, /export function parseEvidenceCsv/);
assert.ok(!appSource.includes("losses === 0 ? 100"), "flat-series RSI cannot diverge in the chart view");
const styleResponse = await request("/styles.css");
assert.equal(styleResponse.status, 200);
const styleSource = await styleResponse.text();
const cssVersion = homeHtml.match(/href="(?:\.\/)?styles\.css\?v=([a-f0-9]{16})"/)?.[1];
assert.ok(cssVersion, "the stylesheet URL carries a content version");
assert.equal(createHash("sha256").update(styleSource, "utf8").digest("hex").slice(0, 16), cssVersion,
  "the stylesheet version matches the normalized bytes served by the Worker");
const bootstrapVersion = homeHtml.match(/src="(?:\.\/)?app-bootstrap\.mjs\?v=([a-f0-9]{16})"/)?.[1];
assert.ok(bootstrapVersion, "the bootstrap URL carries a content version");
const bootstrapResponse = await request("/app-bootstrap.mjs");
assert.equal(bootstrapResponse.status, 200);
const bootstrapSource = await bootstrapResponse.text();
const appVersion = createHash("sha256").update(appSource).digest("hex").slice(0, 16);
assert.ok(bootstrapSource.includes(`app.js?v=${appVersion}`), "the bootstrap cache-busts the exact application bundle");
assert.equal(createHash("sha256").update(bootstrapSource, "utf8").digest("hex").slice(0, 16), bootstrapVersion,
  "the bootstrap version matches the normalized bytes served by the Worker");
const moduleVersions = new Map();
const moduleSources = new Map();
for (const moduleName of ["evidence-contract.mjs", "research-adapters.mjs", "market-overview.mjs", "convergence-engine.mjs"]) {
  const moduleResponse = await request("/" + moduleName);
  assert.equal(moduleResponse.status, 200, moduleName + " is served");
  const moduleSource = await moduleResponse.text();
  const moduleVersion = createHash("sha256").update(moduleSource, "utf8").digest("hex").slice(0, 16);
  moduleVersions.set(moduleName, moduleVersion);
  moduleSources.set(moduleName, moduleSource);
  assert.ok(bootstrapSource.includes("./" + moduleName + "?v=" + moduleVersion),
    moduleName + " import is pinned to its content hash");
}
assert.ok(moduleSources.get("research-adapters.mjs").includes(
  "./evidence-contract.mjs?v=" + moduleVersions.get("evidence-contract.mjs"),
), "the research adapter import is pinned to its content hash");
const vendorCoverageResponse = await request("/vendor-coverage.json");
assert.equal(vendorCoverageResponse.status, 200);
const vendorCoverageSource = await vendorCoverageResponse.text();
const vendorCoverageVersion = createHash("sha256").update(vendorCoverageSource, "utf8").digest("hex").slice(0, 16);
assert.ok(appSource.includes("vendor-coverage.json?v=" + vendorCoverageVersion),
  "the vendor catalog fetch is pinned to its content hash");
const faviconVersion = homeHtml.match(/href="(?:\.\/)?favicon\.svg\?v=([a-f0-9]{16})"/)?.[1];
assert.ok(faviconVersion, "the favicon URL carries a content version");
assert.equal(createHash("sha256").update(svgBytes).digest("hex").slice(0, 16), faviconVersion,
  "the favicon version matches the served SVG");
assert.match(styleSource, /font-size: 10px; line-height: 1\.45/);
assert.match(styleSource, /\.overview-table th:nth-child\(2\).*display: none/s);
const freshnessHelper = appSource.match(/function marketContextFreshness\(asOf, now = new Date\(\)\) \{[\s\S]*?\n\}/);
assert.ok(freshnessHelper, "the terminal exposes a shared market-context freshness calculation");
const marketContextFreshness = runInNewContext(`(${freshnessHelper[0]})`, { Date, Intl, Number });
const freshnessAt = (asOf, now) => JSON.parse(JSON.stringify(marketContextFreshness(asOf, new Date(now))));
assert.deepEqual(freshnessAt("2026-10-22", "2026-10-29T00:30:00.000Z"), {
  state: "stale", ageDays: 6, label: "STALE · 6 DAYS OLD",
}, "market age follows the New York calendar across UTC midnight");
assert.deepEqual(freshnessAt("2026-10-25", "2026-10-28T21:00:00.000Z"), {
  state: "fresh", ageDays: 3, label: "FRESH · 3 DAYS OLD",
}, "the three-day freshness boundary is inclusive");
assert.deepEqual(freshnessAt("2026-10-24", "2026-10-28T21:00:00.000Z"), {
  state: "stale", ageDays: 4, label: "STALE · 4 DAYS OLD",
}, "the day beyond the freshness boundary is stale");
assert.equal(freshnessAt("2026-10-29", "2026-10-28T21:00:00.000Z").state, "future");
assert.equal(freshnessAt("2026-02-30", "2026-10-28T21:00:00.000Z").state, "unknown");
assert.match(appSource, /aria-label="Chartlector data freshness"/);
assert.match(appSource, /\$\{esc\(freshness\.label\)\}/);
assert.match(appSource, /DATA LOADED · FUTURE-DATED CONTEXT/);
assert.match(appSource, /DATA LOADED · CONTEXT FRESHNESS UNKNOWN/);
assert.match(appSource, /OpenMarket, VolSignals, and TheStrat as three post-index additions outside the active 86-family \/ 100-pass scope/);
const pageMap = appSource.match(/const pages = \{([\s\S]*?)\};/);
assert.ok(pageMap, "the terminal view registry is present");
const views = [...pageMap[1].matchAll(/(?:^|,\s*)([A-Za-z][\w]*):/g)].map((m) => m[1]);
assert.equal(views.length, 30, "all 30 terminal views are registered");
assert.equal(new Set(views).size, 30, "terminal view keys are unique");
assert.match(appSource, /view: location\.hash\.slice\(1\) \|\| 'brain'/, "Trade Brain is the default terminal view");
assert.doesNotMatch(appSource, /Load synthetic sample/, "the terminal UI does not offer synthetic sample loaders");
assert.doesNotMatch(appSource, /Demo headline:|Synthetic sample feed|function create\w*(?:Demo|Sample)Rows/, "synthetic market fixtures are not shipped in the browser bundle");
assert.match(appSource, /function renderCharts\(\) \{ return renderLiveTicker\(\); \}/, "the chart workspace renders provider-backed bars");
assert.match(appSource, /\['overview', 'alpaca', 'charts'\]/, "the chart workspace refreshes live bars while visible");
assert.match(appSource, /messages\[data\?\.error\] \|\| messages\[data\?\.status\]/, "the UI distinguishes a verified closed market from a missing setup");
assert.ok(views.includes("convergence"), "the convergence view is registered");

const statusResponse = await request("/api/status");
assert.equal(statusResponse.status, 200);
const status = await statusResponse.json();
assert.equal(status.mode, "unconfigured", "the smoke environment has no provider credentials");
assert.equal(status.accountData, false);
assert.equal(status.orderAccess, false);
assert.ok(status.allowedReads.includes("alpaca-stock-quotes"));
assert.ok(status.allowedReads.includes("alpaca-stock-stream"));
assert.ok(!status.allowedReads.includes("alpaca-sip-stream"));

const badSymbol = await request("/api/alpaca/bars?symbol=SPY%2FABC&days=20");
assert.equal(badSymbol.status, 400, "invalid symbols fail before provider access");
const badWindow = await request("/api/alpaca/bars?symbol=SPY&days=30");
assert.equal(badWindow.status, 400, "unsupported windows fail before provider access");
const barsWithoutCredentials = await request("/api/alpaca/bars?symbol=SPY&days=20");
assert.equal(barsWithoutCredentials.status, 503, "missing provider credentials fail closed");
const barsWrite = await request("/api/alpaca/bars?symbol=SPY&days=20", { method: "POST" });
assert.equal(barsWrite.status, 405, "the market-data route remains read-only");
const brainMissingCredentials = await worker.fetch(new Request(new URL("/api/alpaca/brain/scan?symbol=SPY", origin), { headers: { "cf-connecting-ip": "192.0.2.10" } }), env);
assert.equal(brainMissingCredentials.status, 503, "live scans fail closed without provider credentials");
assert.equal((await brainMissingCredentials.json()).error, "market_data_credentials_unavailable");
const brainBadSymbol = await worker.fetch(new Request(new URL("/api/alpaca/brain/scan?symbol=SPY%2FABC", origin), { headers: { "cf-connecting-ip": "192.0.2.11" } }), { ALPACA_API_KEY_ID: "smoke-key-id", ALPACA_API_SECRET_KEY: "smoke-secret" });
assert.equal(brainBadSymbol.status, 400);
assert.equal((await brainBadSymbol.json()).schema, "SHIPYARD_TRADE_BRAIN_SCAN_V2");
const brainWrite = await worker.fetch(new Request(new URL("/api/alpaca/brain/scan?symbol=SPY", origin), { method: "POST", headers: { "cf-connecting-ip": "192.0.2.12" } }), { ALPACA_API_KEY_ID: "smoke-key-id", ALPACA_API_SECRET_KEY: "smoke-secret" });
assert.equal(brainWrite.status, 405, "Trade Brain remains read-only");
assert.equal((await brainWrite.json()).schema, "SHIPYARD_TRADE_BRAIN_SCAN_V2");

const configuredEnv = { ALPACA_API_KEY_ID: "smoke-key-id", ALPACA_API_SECRET_KEY: "smoke-secret" };
const streamWithoutUpgrade = await worker.fetch(new Request(new URL("/api/alpaca/stream", origin), { headers: { "cf-connecting-ip": "192.0.2.13" } }), configuredEnv);
assert.equal(streamWithoutUpgrade.status, 426, "the quote stream requires a WebSocket handshake");
const streamBadOrigin = await worker.fetch(new Request(new URL("/api/alpaca/stream", origin), { headers: { Upgrade: "websocket", Origin: "https://example.invalid", "cf-connecting-ip": "192.0.2.14" } }), configuredEnv);
assert.equal(streamBadOrigin.status, 403, "the quote stream rejects cross-origin WebSocket connections");
const streamMissingCredentials = await worker.fetch(new Request(new URL("/api/alpaca/stream", origin), { headers: { Upgrade: "websocket", Origin: origin, "cf-connecting-ip": "192.0.2.15" } }), env);
assert.equal(streamMissingCredentials.status, 503, "the quote stream fails closed without server credentials");
const originalFetch = globalThis.fetch;
let providerCalls = 0;
let calendarCalls = 0;
try {
  globalThis.fetch = async (input, init) => {
    const providerUrl = new URL(input);
    if (providerUrl.hostname === "paper-api.alpaca.markets") {
      calendarCalls += 1;
      assert.equal(providerUrl.pathname, "/v3/calendar/IEX");
      assert.equal(providerUrl.searchParams.get("start"), providerUrl.searchParams.get("end"));
      assert.equal(providerUrl.searchParams.get("timezone"), "UTC");
      assert.equal(init.headers["APCA-API-KEY-ID"], configuredEnv.ALPACA_API_KEY_ID);
      assert.equal(init.headers["APCA-API-SECRET-KEY"], configuredEnv.ALPACA_API_SECRET_KEY);
      const date = providerUrl.searchParams.get("start");
      return new Response(JSON.stringify({ calendar: [{ date, core_start: `${date}T13:30:00Z`, core_end: `${date}T20:00:00Z` }] }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }
    providerCalls += 1;
    assert.equal(providerUrl.hostname, "data.alpaca.markets");
    assert.equal(providerUrl.searchParams.get("feed"), "iex");
    assert.equal(providerUrl.searchParams.get("timeframe"), "1Day");
    assert.equal(providerUrl.searchParams.get("adjustment"), "split");
    assert.equal(init.headers["APCA-API-KEY-ID"], configuredEnv.ALPACA_API_KEY_ID);
    assert.equal(init.headers["APCA-API-SECRET-KEY"], configuredEnv.ALPACA_API_SECRET_KEY);
    return new Response(JSON.stringify({ bars: { SPY: [{ t: "2026-10-27T00:00:00Z", o: 100, h: 103, l: 99, c: 102, v: 1234, n: 17, vw: 101, ignored: "not forwarded" }] } }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };
  const configuredBarsResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=SPY&days=20", origin)), configuredEnv);
  assert.equal(configuredBarsResponse.status, 200);
  const configuredBars = await configuredBarsResponse.json();
  assert.equal(configuredBars.status, "connected");
  assert.equal(configuredBars.feed, "iex");
  assert.equal(configuredBars.session_calendar.market, "IEX");
  assert.equal(configuredBars.session_calendar.status, "open");
  assert.equal(configuredBars.session_calendar.source, "alpaca_iex_calendar_v3");
  assert.ok(Number.isFinite(Date.parse(configuredBars.session_calendar.received_at)));
  assert.deepEqual(Object.keys(configuredBars.bars[0]), ["at", "open", "high", "low", "close", "volume", "trades", "vwap"]);
  const cachedBarsResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=SPY&days=20", origin)), configuredEnv);
  assert.equal(cachedBarsResponse.status, 200);
  assert.equal(providerCalls, 1, "market-data responses are cached within the Worker isolate");
  assert.equal(calendarCalls, 1, "IEX session calendars are cached and joined to the bar response");

  globalThis.fetch = async () => new Response(JSON.stringify({ bars: { QQQ: [{ t: "2026-10-27T00:00:00Z", o: 100, h: 103, l: 99, c: 102, v: 12.5 }] } }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
  const fractionalVolumeResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=QQQ&days=20", origin)), configuredEnv);
  assert.equal(fractionalVolumeResponse.status, 200);
  assert.equal((await fractionalVolumeResponse.json()).status, "no_data", "fractional share volume is not forwarded as a precise bar");

  globalThis.fetch = async () => new Response(new ReadableStream({
    start(controller) {
      controller.enqueue(new Uint8Array(1024 * 1024 + 1));
      controller.close();
    },
  }), { status: 200 });
  const oversizedResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=DIA&days=20", origin)), configuredEnv);
  assert.equal(oversizedResponse.status, 502);
  assert.equal((await oversizedResponse.json()).error, "provider_response_too_large");

  globalThis.fetch = async () => new Response("not-json", { status: 200 });
  const malformedResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=IWM&days=20", origin)), configuredEnv);
  assert.equal(malformedResponse.status, 502);
  assert.equal((await malformedResponse.json()).error, "invalid_provider_payload");

  globalThis.fetch = async () => new Response("provider detail must not escape", { status: 429 });
  const providerLimitedResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=DIA&days=20", origin)), configuredEnv);
  assert.equal(providerLimitedResponse.status, 429);
  const providerLimited = await providerLimitedResponse.json();
  assert.equal(providerLimited.error, "provider_rate_limited");
  assert.ok(!JSON.stringify(providerLimited).includes("provider detail"));

  globalThis.fetch = async () => new Response("private provider authorization detail", { status: 401 });
  const rejectedResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=XLF&days=20", origin)), configuredEnv);
  assert.equal(rejectedResponse.status, 502);
  const rejected = await rejectedResponse.json();
  assert.equal(rejected.error, "credentials_or_feed_rejected");
  assert.ok(!JSON.stringify(rejected).includes("private provider authorization detail"));
  assert.ok(!JSON.stringify(rejected).includes(configuredEnv.ALPACA_API_SECRET_KEY));
} finally {
  globalThis.fetch = originalFetch;
}

const originalDateNow = Date.now;
try {
  // Use a date not touched by the successful-calendar case above so this
  // provider-outage assertion tests a true cache miss, not a valid cached read.
  Date.now = () => Date.parse("2026-10-30T15:00:00.000Z");
  globalThis.fetch = async (input) => {
    const providerUrl = new URL(input);
    if (providerUrl.hostname === "paper-api.alpaca.markets") return new Response("calendar unavailable", { status: 503 });
    return new Response(JSON.stringify({ bars: { XLF: [{ t: "2026-10-28T00:00:00Z", o: 100, h: 103, l: 99, c: 102, v: 1234, n: 17, vw: 101 }] } }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };
  const calendarFallbackResponse = await worker.fetch(new Request(new URL("/api/alpaca/bars?symbol=XLF&days=20", origin)), configuredEnv);
  assert.equal(calendarFallbackResponse.status, 200, "a calendar outage does not block a valid bar response");
  const calendarFallbackBars = await calendarFallbackResponse.json();
  assert.equal(calendarFallbackBars.status, "connected");
  assert.equal(calendarFallbackBars.session_calendar, null, "unverified calendar data is not presented as authoritative");
} finally {
  Date.now = originalDateNow;
  globalThis.fetch = originalFetch;
}

const originalBrainDateNow = Date.now;
try {
  const scanTime = Date.parse("2026-11-20T15:00:00.000Z");
  Date.now = () => scanTime;
  const closes = [];
  let close = 100;
  const changes = [0.4, -0.3, 0.4, -0.3, 0.2];
  for (let index = 0; index < 65; index += 1) {
    if (index > 0) close += changes[(index - 1) % changes.length];
    const at = new Date(scanTime - (65 - index) * 86400000).toISOString().slice(0, 10);
    closes.push({ t: `${at}T00:00:00Z`, o: close - 0.1, h: close + 0.4, l: close - 0.4, c: close, v: 10000 });
  }
  const optionSymbol = "SPY261218C00105000";
  const contract = {
    symbol: optionSymbol, underlying_symbol: "SPY", type: "call", status: "active", tradable: true,
    expiration_date: "2026-12-18", strike_price: "105", multiplier: "100", open_interest: "500",
    open_interest_date: "2026-11-19",
    deliverables: [{ type: "equity", symbol: "SPY", amount: 100, delayed_settlement: false }],
  };
  const providerPaths = [];
  globalThis.fetch = async (input, init) => {
    const providerUrl = new URL(input);
    providerPaths.push(providerUrl.pathname);
    assert.equal(init.headers["APCA-API-KEY-ID"], configuredEnv.ALPACA_API_KEY_ID);
    assert.equal(init.headers["APCA-API-SECRET-KEY"], configuredEnv.ALPACA_API_SECRET_KEY);
    if (providerUrl.hostname === "paper-api.alpaca.markets" && providerUrl.pathname === "/v3/calendar/IEX") {
      const date = providerUrl.searchParams.get("start");
      return new Response(JSON.stringify({ calendar: [{ date, core_start: `${date}T13:30:00Z`, core_end: `${date}T20:00:00Z` }] }), { status: 200 });
    }
    if (providerUrl.hostname === "paper-api.alpaca.markets" && providerUrl.pathname === "/v2/options/contracts") {
      assert.equal(providerUrl.searchParams.get("show_deliverables"), "true");
      return new Response(JSON.stringify({ option_contracts: [contract], next_page_token: null }), { status: 200 });
    }
    if (providerUrl.hostname === "data.alpaca.markets" && providerUrl.pathname === "/v2/stocks/SPY/quotes/latest") {
      assert.equal(providerUrl.searchParams.get("feed"), "sip");
      return new Response(JSON.stringify({ quote: { t: "2026-11-20T14:59:30.000Z", bp: 105.5, ap: 105.6, bs: 10, as: 12 } }), { status: 200 });
    }
    if (providerUrl.hostname === "data.alpaca.markets" && providerUrl.pathname === "/v2/stocks/SPY/bars") {
      assert.equal(providerUrl.searchParams.get("feed"), "iex");
      return new Response(JSON.stringify({ bars: { SPY: closes } }), { status: 200 });
    }
    if (providerUrl.hostname === "data.alpaca.markets" && providerUrl.pathname === "/v1beta1/options/snapshots/SPY") {
      assert.equal(providerUrl.searchParams.get("feed"), "indicative");
      return new Response(JSON.stringify({ snapshots: { [optionSymbol]: {
        latestQuote: { t: "2026-11-20T14:59:45.000Z", bp: 0.98, ap: 1.02, bs: 20, as: 18 },
        latestTrade: { t: "2026-11-20T14:45:00.000Z", p: 1, s: 1 },
        greeks: { delta: 0.55 }, impliedVolatility: 0.25,
      } } }), { status: 200 });
    }
    throw new Error(`Unexpected provider request: ${providerUrl.hostname}${providerUrl.pathname}`);
  };
  const scanResponse = await worker.fetch(new Request(new URL("/api/alpaca/brain/scan?symbol=SPY", origin), { headers: { "cf-connecting-ip": "192.0.2.20" } }), configuredEnv);
  assert.equal(scanResponse.status, 200);
  const scan = await scanResponse.json();
  assert.equal(scan.schema, "SHIPYARD_TRADE_BRAIN_SCAN_V2");
  assert.equal(scan.status, "connected");
  assert.equal(scan.session_calendar.source, "alpaca_iex_calendar_v3");
  assert.equal(scan.underlying_quote.feed, "sip");
  assert.equal(scan.feeds.underlying, "Alpaca SIP");
  assert.deepEqual(scan.setups.map((setup) => setup.instrument), ["equity", "call"]);
  assert.equal(scan.setups[1].feed, "indicative");
  assert.equal(scan.setups[1].price_basis, "modified_indicative_quote");
  assert.equal(scan.setups[1].execution_status, "broker_quote_required");
  assert.equal(scan.setups[1].symbol, optionSymbol);
  assert.equal(scan.setups[1].estimated_max_loss_per_contract_at_indicative_ask, 102);
  assert.equal(scan.setups[1].quote_age_seconds, 15);
  assert.equal(scan.setups[1].delayed_trade_age_seconds, 900, "the expected 15-minute indicative-feed trade delay does not reject a current quote");
  assert.equal(scan.options.trade_delay_minutes, 15);
  assert.equal(scan.options.execution_pricing, false);
  assert.equal(scan.setups[1].greeks_method, "Alpaca Black-Scholes model");
  assert.ok(providerPaths.includes("/v2/stocks/SPY/quotes/latest"));
  assert.ok(providerPaths.includes("/v2/stocks/SPY/bars"));
  assert.ok(providerPaths.includes("/v1beta1/options/snapshots/SPY"));
} finally {
  Date.now = originalBrainDateNow;
  globalThis.fetch = originalFetch;
}

const staleOptionScanNow = Date.parse("2026-11-20T15:00:00.000Z");
try {
  Date.now = () => staleOptionScanNow;
  const symbol = "NVDA";
  const staleCloses = [];
  let staleClose = 100;
  const staleChanges = [0.4, -0.3, 0.4, -0.3, 0.2];
  for (let index = 0; index < 65; index += 1) {
    if (index > 0) staleClose += staleChanges[(index - 1) % staleChanges.length];
    const at = new Date(staleOptionScanNow - (65 - index) * 86400000).toISOString().slice(0, 10);
    staleCloses.push({ t: `${at}T00:00:00Z`, o: staleClose - 0.1, h: staleClose + 0.4, l: staleClose - 0.4, c: staleClose, v: 10000 });
  }
  const optionSymbol = "NVDA261218C00105000";
  const contract = {
    symbol: optionSymbol, underlying_symbol: symbol, type: "call", status: "active", tradable: true,
    expiration_date: "2026-12-18", strike_price: "105", multiplier: "100", open_interest: "500",
    open_interest_date: "2026-11-19",
    deliverables: [{ type: "equity", symbol, amount: 100, delayed_settlement: false }],
  };
  globalThis.fetch = async (input) => {
    const providerUrl = new URL(input);
    if (providerUrl.hostname === "paper-api.alpaca.markets" && providerUrl.pathname === "/v3/calendar/IEX") {
      const date = providerUrl.searchParams.get("start");
      return new Response(JSON.stringify({ calendar: [{ date, core_start: `${date}T13:30:00Z`, core_end: `${date}T20:00:00Z` }] }), { status: 200 });
    }
    if (providerUrl.hostname === "paper-api.alpaca.markets" && providerUrl.pathname === "/v2/options/contracts") {
      return new Response(JSON.stringify({ option_contracts: [contract], next_page_token: null }), { status: 200 });
    }
    if (providerUrl.hostname === "data.alpaca.markets" && providerUrl.pathname === `/v2/stocks/${symbol}/quotes/latest`) {
      return new Response(JSON.stringify({ quote: { t: "2026-11-20T14:59:30.000Z", bp: 105.5, ap: 105.6, bs: 10, as: 12 } }), { status: 200 });
    }
    if (providerUrl.hostname === "data.alpaca.markets" && providerUrl.pathname === `/v2/stocks/${symbol}/bars`) {
      return new Response(JSON.stringify({ bars: { [symbol]: staleCloses } }), { status: 200 });
    }
    if (providerUrl.hostname === "data.alpaca.markets" && providerUrl.pathname === `/v1beta1/options/snapshots/${symbol}`) {
      assert.equal(providerUrl.searchParams.get("feed"), "indicative");
      return new Response(JSON.stringify({ snapshots: { [optionSymbol]: {
        latestQuote: { t: "2026-11-20T14:50:00.000Z", bp: 0.98, ap: 1.02, bs: 20, as: 18 },
        latestTrade: { t: "2026-11-20T14:59:50.000Z", p: 1, s: 1 },
        greeks: { delta: 0.55 }, impliedVolatility: 0.25,
      } } }), { status: 200 });
    }
    throw new Error(`Unexpected stale-option provider request: ${providerUrl.hostname}${providerUrl.pathname}`);
  };
  const response = await worker.fetch(new Request(new URL(`/api/alpaca/brain/scan?symbol=${symbol}`, origin), { headers: { "cf-connecting-ip": "192.0.2.22" } }), configuredEnv);
  assert.equal(response.status, 200);
  const scan = await response.json();
  assert.deepEqual(scan.setups.map((setup) => setup.instrument), ["equity"], "a stale indicative option quote is rejected regardless of the delayed trade timestamp");
  assert.equal(scan.options.status, "no_contract");
} finally {
  Date.now = originalBrainDateNow;
  globalThis.fetch = originalFetch;
}

const fallbackScanNow = Date.parse("2026-11-20T15:00:00.000Z");
try {
  Date.now = () => fallbackScanNow;
  const requestedFeeds = [];
  globalThis.fetch = async (input) => {
    const providerUrl = new URL(input);
    if (providerUrl.hostname === "paper-api.alpaca.markets") {
      const date = providerUrl.searchParams.get("start");
      return new Response(JSON.stringify({ calendar: [{ date, core_start: `${date}T13:30:00Z`, core_end: `${date}T20:00:00Z` }] }), { status: 200 });
    }
    if (providerUrl.pathname === "/v2/stocks/QQQ/quotes/latest") {
      const feed = providerUrl.searchParams.get("feed");
      requestedFeeds.push(feed);
      if (feed === "sip") return new Response("SIP subscription unavailable", { status: 403 });
      return new Response(JSON.stringify({ quote: { t: "2026-11-20T14:59:30.000Z", bp: 105.5, ap: 105.6, bs: 10, as: 12 } }), { status: 200 });
    }
    if (providerUrl.pathname === "/v2/stocks/QQQ/bars") {
      assert.equal(providerUrl.searchParams.get("feed"), "iex");
      return new Response(JSON.stringify({ bars: { QQQ: [
        { t: "2026-11-16T00:00:00Z", o: 105, h: 106, l: 104, c: 105, v: 1000 },
        { t: "2026-11-17T00:00:00Z", o: 105, h: 106, l: 104, c: 105, v: 1000 },
        { t: "2026-11-18T00:00:00Z", o: 105, h: 106, l: 104, c: 105, v: 1000 },
        { t: "2026-11-19T00:00:00Z", o: 105, h: 106, l: 104, c: 105, v: 1000 },
      ] } }), { status: 200 });
    }
    throw new Error(`Unexpected fallback provider request: ${providerUrl.hostname}${providerUrl.pathname}`);
  };
  const fallbackResponse = await worker.fetch(new Request(new URL("/api/alpaca/brain/scan?symbol=QQQ", origin), { headers: { "cf-connecting-ip": "192.0.2.21" } }), configuredEnv);
  assert.equal(fallbackResponse.status, 200);
  const fallbackScan = await fallbackResponse.json();
  assert.equal(fallbackScan.status, "no_setup", "insufficient history does not create an idea from the live quote alone");
  assert.equal(fallbackScan.underlying_quote.feed, "iex");
  assert.equal(fallbackScan.feeds.underlying, "Alpaca IEX");
  assert.deepEqual(fallbackScan.setups, []);
  assert.deepEqual(requestedFeeds, ["sip", "iex"], "IEX is tried only after SIP access is denied");
} finally {
  Date.now = originalBrainDateNow;
  globalThis.fetch = originalFetch;
}

const morgueResponse = await request("/api/research/morgue/readiness");
assert.equal(morgueResponse.status, 200);
const morgue = await morgueResponse.json();
assert.equal(morgue.status, "available", "availability denotes manifest presence");
assert.equal(morgue.freshness.status, "unknown");
assert.equal(morgue.gates.values_returned, false);
assert.equal(morgue.gates.decision_eligible, false);
assert.equal(morgue.gates.order_submission_enabled, false);

const mcpResponse = await request("/mcp", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }),
});
assert.equal(mcpResponse.status, 200);
const mcp = await mcpResponse.json();
const tools = mcp.result?.tools ?? [];
assert.deepEqual(
  tools.map((tool) => tool.name),
  ["shipyard_market_context", "shipyard_alpaca_daily_bars", "shipyard_trade_brain_scan", "shipyard_morgue_readiness", "shipyard_research_capabilities", "shipyard_lector_output", "shipyard_aperture_output", "shipyard_stock_quote", "shipyard_research_catalog", "shipyard_research_snapshot"],
);
assert.ok(tools.every((tool) => tool.annotations?.readOnlyHint === true));
assert.ok(tools.every((tool) => tool.annotations?.destructiveHint === false));

for (const path of ["/operations.html", "/api/ausar/snapshot", "/api/terminal/history"]) {
  const response = await request(path);
  assert.equal(response.status, 410, `${path} stays retired`);
}
for (const path of ["/api/account", "/api/orders"]) {
  const response = await request(path);
  assert.equal(response.status, 404, `${path} is not an exposed API`);
}

console.log(JSON.stringify({
  result: "PASS",
  views: views.length,
  checks: [
    "static entry, content-versioned scripts/modules/data/assets, and icon alias",
    "30 registered UI views and live Trade Brain as default",
    "convergence catalog and local evidence intake",
    "New York-calendar context freshness and boundary states",
    "legacy-only additions disclosed outside the active family count",
    "read-only status and Alpaca validation",
    "fail-closed provider configuration, SIP-first stock quotes with real IEX fallback, and IEX calendar lookup",
    "server-side 90-second indicative quote freshness gate, delayed-trade handling, and explicit Alpaca Black-Scholes Greek provenance",
    "Alpaca IEX normalization, isolate cache, body-size limit, provider-error mapping, and secret redaction",
    "metadata-only Morgue gates",
    "ten read-only MCP tools",
    "retired paper-desk routes",
    "no account/order API routes",
  ],
}));
