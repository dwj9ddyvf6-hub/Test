// Read-only projections of existing provider paths and exact browser calculations.
// No local CSV/manual input, persistence, options requests, or strategy changes.
const SHIPYARD_RESEARCH_BUILD = __SHIPYARD_RESEARCH_BUILD__;
// A page retains its actual read (fresh or cached), not a promised replay of the
// first acquisition.
// Keep the browser's genuine capture IDs/clocks intact in returned records. Only
// the continuation identity omits reviewed acquisition/computation metadata.
function shipyardSnapshotContentIdentity(bundle, context, build = SHIPYARD_RESEARCH_BUILD) {
  const content = structuredClone(bundle);
  delete content.createdAt;
  delete content.sourceCapture.receivedAt;
  delete content.sourceCapture.captureId;
  delete content.sourceCapture.captureSha256;
  if (content.sourceCapture.sessionCalendar) delete content.sourceCapture.sessionCalendar.received_at;
  delete content.contextReference.receivedAt;
  for (const observation of content.observations) {
    delete observation.clocks.ingestedAt;
    delete observation.source.captureId;
    delete observation.source.artifactSha256;
  }
  for (const feature of content.features) delete feature.record.computedAt;
  const contextContent = context ? structuredClone(context) : null;
  // Exact receipt-clock paths produced by safeContext/contextRoute. Do not
  // recursively drop timestamp-named fields: event/publication clocks matter.
  if (contextContent) {
    delete contextContent.received_at;
    for (const name of ['chartlector','treasury_nominal','treasury_real','fed_dollar','VIX','VIX3M','VVIX','SKEW']) {
      if (contextContent.components?.[name]) delete contextContent.components[name].received_at;
    }
    const macro = contextContent.context?.macro;
    if (macro) {
      delete macro.received_at;
      if (macro.dollar_index) delete macro.dollar_index.received_at;
    }
    const volatility = contextContent.context?.market_volatility;
    if (volatility) {
      delete volatility.received_at;
      for (const name of ["VIX", "VIX3M", "VVIX", "SKEW"]) {
        if (volatility.indices?.[name]) delete volatility.indices[name].received_at;
      }
    }
  }
  return { identity_schema: "SHIPYARD_RESEARCH_CONTENT_IDENTITY_V2", content, context: contextContent, build };
}
function shipyardCanonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(shipyardCanonicalJson).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${shipyardCanonicalJson(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
async function shipyardStockQuote(request, args, env) {
  const symbol = args.symbol.toUpperCase();
  const base = { schema: "SHIPYARD_STOCK_QUOTE_V1", symbol, source: "Alpaca Market Data", transport: "REST latest-quote snapshot",
    restrictions: { decision_eligible: false, order_submission_enabled: false, account_data_returned: false, continuous_stream: false,
      note: "Snapshot access to the same SIP/IEX quote fields; not every streaming tick. No competing provider WebSocket is opened. No option scanner or trading action is invoked." } };
  if (!alpacaRateAllowed(request, Date.now())) return json({ ...base, status: "unavailable", error: "rate_limited", retry_after_seconds: 60 }, 429);
  const key = env?.ALPACA_API_KEY_ID, secret = env?.ALPACA_API_SECRET_KEY;
  if (typeof key !== "string" || !key || typeof secret !== "string" || !secret) return json({ ...base, status: "unavailable", error: "market_data_credentials_unavailable" }, 503);
  if (request.signal.aborted) return json({ ...base, status: "cancelled" }, 408);
  let feed = "sip", result = await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/quotes/latest?feed=sip`, key, secret);
  if (!result.ok && result.status === 403 && !request.signal.aborted) {
    feed = "iex";
    result = await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/quotes/latest?feed=iex`, key, secret);
  }
  const retrieved = Date.now();
  if (request.signal.aborted) return json({ ...base, status: "cancelled" }, 408);
  if (!result.ok) return json({ ...base, status: "unavailable", feed, retrieved_at: new Date(retrieved).toISOString(),
    error: result.status === 401 ? "market_data_authentication_failed" : result.status === 403 ? "underlying_iex_entitlement_unavailable" : result.status === 429 ? "provider_rate_limited" : "underlying_quote_unavailable" }, 503);
  if (result.value?.symbol !== undefined && result.value.symbol !== symbol) return json({ ...base, status: "invalid", error: "provider_symbol_mismatch", feed, retrieved_at: new Date(retrieved).toISOString() }, 502);
  const quote = alpacaQuote(result.value?.quote);
  const age = quote ? (retrieved - Date.parse(quote.at)) / 1000 : null;
  const status = !quote ? "invalid" : age < 0 ? "future_dated" : age > 90 ? "stale" : "observed";
  return json({ ...base, status, feed, quote, retrieved_at: new Date(retrieved).toISOString(),
    freshness: { status, age_seconds: age, display_maximum_age_seconds: 90 },
    completeness: { symbols: 1, quotes: quote ? 1 : 0, sip_consolidated: feed === "sip", iex_single_exchange: feed === "iex",
      request_bound: "At most two existing 8-second / 1-MiB helper reads; SIP falls back to IEX only on HTTP 403." } });
}

async function shipyardResearchSnapshot(request, args, env) {
  const symbol = (args.symbol || "SPY").toUpperCase(), days = args.days || 90;
  const target = new URL("/api/alpaca/bars", request.url); target.searchParams.set("symbol", symbol); target.searchParams.set("days", String(days));
  try {
    const [barsResponse, contextResponse] = await Promise.all([
      alpacaRoute(new Request(target, { headers: { "cf-connecting-ip": request.headers.get("cf-connecting-ip") || "mcp" } }), env),
      contextRoute(new Request(new URL("/api/terminal/context", request.url))),
    ]);
    const bars = await barsResponse.json(), context = contextResponse.ok ? await contextResponse.json() : null;
    if (!barsResponse.ok || bars.status !== "connected") return json({ schema: "SHIPYARD_RESEARCH_SNAPSHOT_V1", status: "unavailable", symbol, source_status: bars.status, error: bars.error || "daily_bars_unavailable", python_producers_executed: false }, 503);
    const bundle = await SHIPYARD_RESEARCH_LOGIC.buildAlpacaResearchEvidence({ symbol, bars: bars.bars, receivedAt: bars.received_at, requestedDays: days, context, sessionCalendar: bars.session_calendar });
    const snapshotHash = await SHIPYARD_RESEARCH_LOGIC_HASH(shipyardCanonicalJson(shipyardSnapshotContentIdentity(bundle, context)));
    if (args.snapshot_hash && args.snapshot_hash !== snapshotHash) return json({ schema: "SHIPYARD_RESEARCH_SNAPSHOT_V1", status: "snapshot_changed", message: "Source content, selection/quality/eligibility, or implementation changed. Restart at offset zero; no mixed-content page returned." }, 409);
    const { observations, features, storage, ...metadata } = bundle;
    const section = args.section || "summary", offset = args.offset || 0, limit = args.limit || (section === "features" ? 1 : 5);
    const data = { schema: "SHIPYARD_RESEARCH_SNAPSHOT_V1", status: context ? "available" : "partial", symbol, snapshot_sha256: snapshotHash,
      retrieved_at: new Date().toISOString(), algorithm_bundle: metadata, source_algorithm_storage_contract: storage,
      pagination_identity: { schema: "SHIPYARD_RESEARCH_CONTENT_IDENTITY_V2", scope: "normalized_content_not_acquisition",
        note: "The hash pins normalized observations, feature results/lineage, source identities, event/publication clocks, context content, calendar/selection/quality/eligibility and implementation. Acquisition/computation clocks and their capture hashes can differ per page and remain genuine in each returned record. Do not treat different pages as one original acquisition." },
      implementation: { ...SHIPYARD_RESEARCH_BUILD, note: "Current browser source is bundled on every build. Numerical formulas/parameters/eligibility are shared; method implementationSha256 fingerprints the compiled function text and can differ from the browser module's unbundled function text." },
      storage: "request_memory_only; no persistence or local-user-input upload", python_producers_executed: false,
      restrictions: { decision_eligible: false, order_submission_enabled: false, local_csv_or_manual_inputs_accepted: false,
        note: "The same browser research-adapter module computes these features, with unchanged completed-session, provenance, rights and eligibility checks. This is not a Saty/RRE/Morgue run or a reconstruction of another browser's saved session." }, section };
    if (section === "summary") data.feature_summary = features.map(f => ({ label: f.label, value: f.record.value, unit: f.record.unit, as_of: f.record.asOfTime,
      method: f.record.method, evidence_status: f.record.evidenceStatus, lineage_eligibility: { eligible: f.lineageEligibility.eligible, purpose: f.lineageEligibility.purpose,
        blocker_count: f.lineageEligibility.blockers.length, blocker_examples: f.lineageEligibility.blockers.slice(0, 1), full_blockers: "Available in the one-feature-per-page features section." } }));
    else {
      const rows = section === "features" ? features : observations;
      data.rows = rows.slice(offset, offset + limit);
      data.pagination = { offset, limit, total: rows.length, next_offset: offset + limit < rows.length ? offset + limit : null,
        note: "Pass snapshot_sha256 as snapshot_hash for content-consistent continuation. Receipt clocks can differ per page; actual content/selection/quality/eligibility/build changes require restarting." };
    }
    return researchResponse(data);
  } catch { return json({ schema: "SHIPYARD_RESEARCH_SNAPSHOT_V1", status: "unavailable", error: "research_snapshot_unavailable", symbol, python_producers_executed: false }, 503); }
}
async function SHIPYARD_RESEARCH_LOGIC_HASH(value) {
  return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value))), b => b.toString(16).padStart(2, "0")).join("");
}
