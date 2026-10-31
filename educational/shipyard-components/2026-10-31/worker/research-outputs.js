// Owner-authenticated MCP projections of already stored research. No producer,
// provider request, write, account read, or retired desk route is invoked here.
const RESEARCH_OUTPUT_SCHEMA = "SHIPYARD_RESEARCH_OUTPUT_V1";
const RESEARCH_OUTPUT_VERSION = "1.0.0";
const RESEARCH_STORED_MAX_BYTES = 65536;
const RESEARCH_RESPONSE_MAX_BYTES = 49152;
const LECTOR_STUDY_ID = "terminal-desk-read-v2";
const SHIPYARD_RESEARCH_CATALOG = __SHIPYARD_RESEARCH_CATALOG__;
const SHIPYARD_RESEARCH_SURFACES = __SHIPYARD_RESEARCH_SURFACES__;

function researchText(value, max = 256) {
  return typeof value === "string" && value.length <= max ? value : null;
}
function researchFields(value, fields, max = 1000) {
  const input = record(value), output = {};
  for (const key of fields) {
    const v = input[key];
    if (v === null || typeof v === "boolean" || (typeof v === "number" && Number.isFinite(v))) output[key] = v;
    else if (typeof v === "string") output[key] = v.length <= max ? v : null;
  }
  return output;
}
function researchBooleans(value, fields) {
  return Object.fromEntries(fields.filter(key => typeof value?.[key] === "boolean").map(key => [key, value[key]]));
}
function researchJson(value) {
  if (typeof value !== "string" || new TextEncoder().encode(value).length > RESEARCH_STORED_MAX_BYTES) return null;
  try { const parsed = JSON.parse(value); return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null; } catch { return null; }
}
function researchClock(value, now) {
  const original = researchText(value, 64), strict = original !== null && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(original);
  const day = strict ? original.slice(0, 10) : null;
  const validDay = day !== null && Number.isFinite(Date.parse(day)) && new Date(day).toISOString().slice(0, 10) === day;
  const parsed = strict && validDay ? Date.parse(original) : NaN;
  return { at: Number.isFinite(parsed) ? original : null, age_seconds: Number.isFinite(parsed) ? Math.floor((now - parsed) / 1000) : null };
}
function researchFreshness(clocks, expires, now) {
  const times = Object.values(clocks).map(x => x.age_seconds).filter(x => x !== null);
  if (times.some(age => age < 0)) return { status: "future_dated", reason: "A stored source clock is ahead of retrieval; not current evidence." };
  const expiry = researchClock(expires, now);
  if (expiry.at !== null && Date.parse(expiry.at) <= now) return { status: "expired", reason: "The stored source expiry has elapsed; retrieval does not refresh it." };
  return { status: "unknown", reason: "No verified source-specific freshness budget or running producer is established by this read. A source expiry alone does not establish live eligibility." };
}
function researchEnvelope(engine, now, status, extra = {}) {
  return { schema: RESEARCH_OUTPUT_SCHEMA, adapter_version: RESEARCH_OUTPUT_VERSION, engine, status,
    retrieved_at: new Date(now).toISOString(),
    restrictions: { research_only: true, decision_eligible: false, performance_claim_eligible: false, order_submission_enabled: false,
      producer_executed: false, source_rights_revalidated: false, account_data_returned: false,
      note: "Stored research is not a live recommendation, fill, account state, or evidence that its producer is still running." }, ...extra };
}
function researchResponse(data) {
  if (new TextEncoder().encode(JSON.stringify(data)).length > RESEARCH_RESPONSE_MAX_BYTES) {
    return json({ schema: RESEARCH_OUTPUT_SCHEMA, status: "payload_too_large", message: "The bounded projection exceeded 48 KiB. For a paged section request a smaller page; otherwise this summary is unavailable. No source payload was returned." }, 413);
  }
  return json(data);
}

// Fixed table, study and type. Values are bound, never SQL/table/URL input.
async function researchLectorRow(env, args) {
  if (!env?.DB) throw new Error("research_database_unavailable");
  const clauses = ["observation_type = ?", "study_id = ?"], values = ["desk_read", LECTOR_STUDY_ID];
  if (args.symbol) { clauses.push("symbol = ?"); values.push(args.symbol.toUpperCase()); }
  if (args.observation_id) { clauses.push("observation_id = ?"); values.push(args.observation_id); }
  return env.DB.prepare(`SELECT observation_id, revision, created_at, computed_at, effective_at, input_watermark_at, expires_at,
    formula_version, parameter_hash, input_hash, code_commit, provider, symbol, timeframe, direction, status,
    length(CAST(payload_json AS BLOB)) AS payload_bytes,
    CASE WHEN length(CAST(payload_json AS BLOB)) <= 65536 THEN payload_json ELSE NULL END AS payload_json,
    CASE WHEN length(CAST(quality_json AS BLOB)) <= 65536 THEN quality_json ELSE NULL END AS quality_json
    FROM observatory_observations WHERE ${clauses.join(" AND ")} ORDER BY julianday(computed_at) DESC, observation_id DESC LIMIT 1`).bind(...values).first();
}
function researchLectorProjection(row, args, now, metadataOnly = false) {
  if (!row) return researchEnvelope("lector", now, "missing", { reason: "No matching stored Lector research observation. No producer was run." });
  const clocks = { input_watermark: researchClock(row.input_watermark_at, now), computed: researchClock(row.computed_at, now),
    effective: researchClock(row.effective_at, now), stored: researchClock(row.created_at, now), published: { at: null, age_seconds: null } };
  const source = { observation_id: researchText(row.observation_id, 64), revision: whole(row.revision), study_id: LECTOR_STUDY_ID,
    provider: researchText(row.provider), formula_version: researchText(row.formula_version), code_commit: researchText(row.code_commit),
    input_hash: researchText(row.input_hash), parameter_hash: researchText(row.parameter_hash),
    symbol: researchText(row.symbol, 10), timeframe: researchText(row.timeframe, 20), integrity: "identity_consistency_only", authenticity_established: false };
  const freshness = researchFreshness(clocks, row.expires_at, now);
  const base = researchEnvelope("lector", now, freshness.status === "expired" ? "stale" : "stored_unverified", {
    source, clocks, expires_at: researchClock(row.expires_at, now).at, freshness,
    completeness: { scope: "one stored observation; not all symbols or a live universe", projection: "allowlisted_research_fields", full_source_payload_returned: false },
    source_claims: { status: researchText(row.status, 80), direction: researchText(row.direction, 30) } });
  const body = researchJson(row.payload_json);
  const reviewedFormula = { CODEX_DESK_READ_RECORD_V2: "desk-read-14", CODEX_DESK_READ_RECORD_V3: "desk-read-16" };
  if (!/^[a-f0-9]{64}$/.test(row.observation_id || "") || !/^[A-Z][A-Z0-9.-]{0,9}$/.test(row.symbol || "")
      || !body || reviewedFormula[body.schema] !== row.formula_version
      || body.symbol !== row.symbol || body.read?.method !== row.formula_version
      || (body.identity_hash !== undefined && body.identity_hash !== row.observation_id)) {
    return { ...base, status: row.payload_bytes > RESEARCH_STORED_MAX_BYTES ? "payload_too_large" : "invalid", reason: "Stored payload is oversized, malformed, unsupported, or inconsistent with its indexed source identity. No values returned." };
  }
  base.source.schema = body.schema;
  if (metadataOnly) return base;
  const read = record(body.read), direction = record(read.direction_resolution), quality = researchJson(row.quality_json);
  const section = args.section || "summary";
  const output = { method: researchText(read.method), call: researchText(read.call, 50),
    score: { value: finite(read.score?.value), max: finite(read.score?.max), ...researchFields(read.score, ["label", "basis", "display"]) },
    direction_resolution: { ...researchFields(direction, ["direction", "source_direction", "rule", "strength", "tie_break"]),
      ...researchBooleans(direction, ["contrary_to_source"]), paper_order_authority: direction.paper_order_authority === "none" ? "none" : null },
    quality: { ...researchFields(quality, ["call_role", "time_basis", "adjustment", "hypothesis_suite"]),
      ...researchBooleans(quality, ["orders", "rank_changes", "missing_baseline", "call_is_directional", "direction_recorded_separately"]) } };
  base.source_claims.direction_freshness_at_publication = researchText(direction.freshness, 50);
  if (section === "factors") {
    const allFactors = Array.isArray(read.factor_checks) ? read.factor_checks : [], factors = allFactors.slice(0, 1000), offset = args.offset || 0, limit = args.limit || 10;
    output.factor_checks = factors.slice(offset, offset + limit).map((row, i) => ({ source_index: offset + i,
      // Compact numeric identifiers are preserved, never relabeled using a different catalog.
      cells: Array.isArray(row) && row.length <= 12 && row.every(cell => cell === null || typeof cell === "boolean" ||
        (typeof cell === "number" && Number.isFinite(cell)) || (typeof cell === "string" && cell.length <= 4000)) ? row : null }));
    base.pagination = { section, offset, limit, total: allFactors.length, accessible_total: factors.length, omitted_by_bound: allFactors.length - factors.length, next_offset: offset + limit < factors.length ? offset + limit : null,
      observation_id: source.observation_id, note: "Use this observation_id for subsequent pages to pin the same stored output. Numeric factor IDs require the matching producer catalog; no mapping is inferred." };
    base.completeness.omitted_invalid_factor_rows = output.factor_checks.filter(x => x.cells === null).length;
  } else {
    const salient = Array.isArray(read.salient) ? read.salient : [];
    output.salient = salient.slice(0, 10).map(item => researchFields(item, ["id", "label", "text", "tone", "category", "source", "evidence_group"], 2000));
    output.direction_resolution.evidence = (Array.isArray(direction.evidence) ? direction.evidence : []).slice(0, 10).map(x => researchText(x, 2000));
    base.completeness.omitted_salient_rows = Math.max(0, salient.length - 10);
  }
  base.completeness.excluded_sections = ["plan", "primary", "baseline", "outcome", "paper/account lifecycle", "unreviewed fields"];
  return { ...base, section, output };
}
async function researchApertureRow(env) {
  if (!env?.DB) throw new Error("research_database_unavailable");
  return env.DB.prepare(`SELECT scan_id, bar_end_at, generated_at, provider, freshness, universe_covered, decision_count, created_at,
    length(CAST(body_json AS BLOB)) AS payload_bytes,
    CASE WHEN length(CAST(body_json AS BLOB)) <= 65536 THEN body_json ELSE NULL END AS body_json
    FROM aperture_scan_history ORDER BY julianday(generated_at) DESC, scan_id DESC LIMIT 1`).first();
}
function researchApertureProjection(row, now, metadataOnly = false) {
  if (!row) return researchEnvelope("aperture", now, "missing", { reason: "No stored Aperture scan. No producer was run." });
  const body = researchJson(row.body_json);
  const explicitSourceAsOf = body?.source_as_of ?? body?.source?.source_as_of ?? null;
  const hasSourceClock = Object.hasOwn(body?.source || {}, "source_as_of") || Object.hasOwn(body || {}, "source_as_of");
  const sourceClockValid = explicitSourceAsOf === null
    ? !hasSourceClock || body?.source?.source_age_ms === null
    : researchClock(explicitSourceAsOf, now).at === explicitSourceAsOf
      && body?.source?.source_as_of === explicitSourceAsOf
      && researchClock(body?.source_as_of, now).at === explicitSourceAsOf;
  const sourceAgeValid = explicitSourceAsOf === null
    ? !hasSourceClock || body?.source?.source_age_ms === null
    : Number.isSafeInteger(body?.source?.source_age_ms) && body.source.source_age_ms >= 0
      && Math.abs(body.source.source_age_ms - (Date.parse(body.generatedAt) - Date.parse(explicitSourceAsOf))) <= 1;
  const inputWatermarkAt = explicitSourceAsOf ?? body?.barEndAt ?? null;
  const inputWatermark = researchClock(inputWatermarkAt, now);
  const evaluationBucket = researchClock(body?.expected_bar_end_at ?? body?.source?.evaluation_bucket_end_at ?? body?.barEndAt, now);
  const sourceAvailableAt = body?.source?.available_at ?? body?.source?.captures?.find(capture => capture?.operation === "latest_1m")?.received_at ?? null;
  const sourceAvailable = researchClock(sourceAvailableAt, now);
  const decisionAt = body?.decision_at ?? body?.generatedAt ?? null;
  const decision = researchClock(decisionAt, now);
  const clocks = { bar_end: researchClock(row.bar_end_at, now), input_watermark: inputWatermark, evaluation_bucket: evaluationBucket,
    source_available: sourceAvailable, decision, computed: researchClock(row.generated_at, now), stored: researchClock(row.created_at, now), published: { at: null, age_seconds: null } };
  const freshness = researchFreshness(clocks, body?.validUntil, now);
  const sourceAvailableValid = sourceAvailableAt === null || sourceAvailable.at === sourceAvailableAt
    && body?.source?.captures?.some(capture => capture?.operation === "latest_1m" && capture?.received_at === sourceAvailableAt)
    && (body?.source?.available_at === undefined || body.source.available_at === sourceAvailableAt);
  const decisionValid = decision.at === body?.generatedAt && decision.at === row.generated_at;
  const base = researchEnvelope("aperture", now, freshness.status === "expired" ? "stale" : "stored_unverified", {
    source: { scan_id: researchText(row.scan_id), provider: researchText(row.provider), schema: researchText(body?.schema), as_of: inputWatermark.at,
      available_at: sourceAvailable.at, decision_at: decision.at,
      source_age_at_retrieval_ms: inputWatermark.at === null ? null : now - Date.parse(inputWatermark.at) },
    clocks,
    expires_at: researchClock(body?.validUntil, now).at, freshness,
    source_claims: { freshness_at_publication: researchText(row.freshness, 50), data_mode_at_publication: researchText(body?.dataMode, 30) },
    completeness: { scope: "latest stored scan only; not a running scanner", universe_covered: whole(row.universe_covered), decision_count: whole(row.decision_count), full_source_payload_returned: false, decisions_returned: false } });
  if (!body || body.schema !== "aperture-live-view.v1" || body.generatedAt !== row.generated_at || body.provider !== row.provider
    || body.etag !== row.scan_id || body.barEndAt !== row.bar_end_at || body.inputWatermarkAt !== inputWatermarkAt || !sourceClockValid || !sourceAgeValid
    || evaluationBucket.at !== row.bar_end_at || !sourceAvailableValid || !decisionValid) {
    return { ...base, status: row.payload_bytes > RESEARCH_STORED_MAX_BYTES ? "payload_too_large" : "invalid", reason: "Stored scan is oversized, malformed, unsupported, or inconsistent with its indexed identity. No values returned." };
  }
  if (metadataOnly) return base;
  return { ...base, output: {
    feed: researchText(body.feed), source_session: researchText(body.session, 40), source_connection: researchText(body.connection, 40),
    universe: researchFields(body.universe, ["id", "count", "hash", "eligible", "covered", "unsupported"]),
    scan: researchFields(body.scan, ["state", "elapsedMs", "harvested", "deepCandidates", "decisions", "executable"]),
    summary: (Array.isArray(body.summary) ? body.summary : []).slice(0, 12).map(x => researchFields(x, ["label", "value", "note", "tone"])),
    backdrop: (Array.isArray(body.backdrop) ? body.backdrop : []).slice(0, 12).map(x => researchFields(x, ["label", "value", "detail", "tone"])),
    source_authority_at_publication: researchBooleans(body.authority, ["decisionSupport", "orderRoute", "tensorWrite", "galathWrite", "folioTendWrite"]),
  }, note: "Historical summary projection only. Source authority/freshness labels are publication-time claims, not current permission. Individual decision payloads and unreviewed fields are excluded." };
}

const RESEARCH_CAPABILITY_PAGE_SIZE = 4;
const RESEARCH_CAPABILITY_VOLATILE_KEYS = new Set(["retrieved_at", "age_seconds", "source_age_at_retrieval_ms"]);
const RESEARCH_CAPABILITY_PAGE_KEYS = new Set(["section", "offset", "limit", "inventory_hash"]);
function researchCapabilityPageArgumentsValid(args) {
  if (!args || typeof args !== "object" || Array.isArray(args)
    || Object.keys(args).some(key => !RESEARCH_CAPABILITY_PAGE_KEYS.has(key))) return false;
  if (!Object.hasOwn(args, "section") || !["engines", "surfaces"].includes(args.section)) return false;
  if ("offset" in args && (!Number.isInteger(args.offset) || args.offset < 0 || args.offset > 100)) return false;
  if ("limit" in args && (!Number.isInteger(args.limit) || args.limit < 1 || args.limit > RESEARCH_CAPABILITY_PAGE_SIZE)) return false;
  if ("inventory_hash" in args && (typeof args.inventory_hash !== "string" || !/^[a-f0-9]{64}$/.test(args.inventory_hash))) return false;
  if (args.offset > 0 && !args.inventory_hash) return false;
  return true;
}
function researchCapabilityPageQueryArguments(searchParams) {
  const entries = [...searchParams.entries()], seen = new Set(), args = {};
  for (const [key, value] of entries) {
    if (!RESEARCH_CAPABILITY_PAGE_KEYS.has(key) || seen.has(key)) return null;
    seen.add(key);
    if (key === "offset" || key === "limit") {
      if (!/^(?:0|[1-9]\d*)$/.test(value)) return null;
      const number = Number(value);
      if (!Number.isSafeInteger(number)) return null;
      args[key] = number;
    } else args[key] = value;
  }
  return researchCapabilityPageArgumentsValid(args) ? args : null;
}
function researchStableInventory(value) {
  if (Array.isArray(value)) return value.map(researchStableInventory);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .filter(key => !RESEARCH_CAPABILITY_VOLATILE_KEYS.has(key))
    .map(key => [key, researchStableInventory(value[key])]));
  return value;
}
async function researchCapabilitiesHash(inventory) {
  const identity = researchStableInventory({
    schema: inventory.schema, adapter_version: inventory.adapter_version, status: inventory.status, scope: inventory.scope,
    provider_requests_made: inventory.provider_requests_made, producer_execution_enabled: inventory.producer_execution_enabled,
    preopen_input_collection: inventory.preopen_input_collection, runtime_configuration: inventory.runtime_configuration,
    surface_coverage: inventory.surface_coverage, engines: inventory.engines, native_inspection: inventory.native_inspection, boundaries: inventory.boundaries,
  });
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(identity)));
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
}
function researchCapabilitiesProjection(inventory, section, offset, limit, inventoryHash) {
  const engines = Array.isArray(inventory.engines) ? inventory.engines : [];
  const surfaces = Array.isArray(inventory.surface_coverage?.surfaces) ? inventory.surface_coverage.surfaces : [];
  const engineSummary = engines.map(item => ({
    engine: researchText(item.engine, 90) || "unknown",
    status: researchText(item.status, 80) || "unknown",
    ...(typeof item.tool === "string" ? { tool: item.tool } : {}),
    ...(Array.isArray(item.tools) ? { tools: item.tools.filter(name => typeof name === "string" && name.length <= 80) } : {}),
  }));
  const surfaceSummary = surfaces.map(item => ({
    view: researchText(item.view, 90) || "unknown", title: researchText(item.title, 120) || "Research view", state: researchText(item.state, 80) || "unknown",
  }));
  const page = section === "engines" ? engines : section === "surfaces" ? surfaces : null;
  const result = {
    schema: inventory.schema, adapter_version: inventory.adapter_version, retrieved_at: inventory.retrieved_at,
    status: inventory.status, scope: inventory.scope, provider_requests_made: inventory.provider_requests_made,
    producer_execution_enabled: inventory.producer_execution_enabled, preopen_input_collection: inventory.preopen_input_collection,
    runtime_configuration: inventory.runtime_configuration,
    surface_coverage: { ...inventory.surface_coverage, route_count: surfaces.length, surfaces: surfaceSummary,
      summary_fields: ["view", "title", "state"], detail_fields_available: ["source", "tool_or_route", "limitation"],
      detail_page_section: "surfaces" },
    engine_count: engines.length, engines: engineSummary,
    capability_detail_pages: {
      inventory_sha256: inventoryHash, page_size: RESEARCH_CAPABILITY_PAGE_SIZE,
      sections: [
        { section: "engines", total: engines.length, first_offset: 0, summary_fields: ["engine", "status", "tool", "tools"], detail_fields_available: "full engine records", request_tool: "shipyard_research_capability_page", request_route: "/api/research/capabilities?section=engines" },
        { section: "surfaces", total: surfaces.length, first_offset: 0, summary_fields: ["view", "title", "state"], detail_fields_available: "full surface records", request_tool: "shipyard_research_capability_page", request_route: "/api/research/capabilities?section=surfaces" },
      ],
      note: "The summary includes every engine and surface. Full records are returned by the distinct page tool or owner Site GET route; pass inventory_sha256 as inventory_hash on continuations. If stored metadata or inventory changes, a 409 requires restarting at offset zero. Pages are separate reads, not a transactional D1 snapshot.",
    },
    native_inspection: inventory.native_inspection, boundaries: inventory.boundaries,
  };
  if (page) {
    const next = offset + limit < page.length ? offset + limit : null;
    result.detail_page = { section, items: page.slice(offset, offset + limit), pagination: {
      offset, limit, total: page.length, next_offset: next, inventory_sha256: inventoryHash,
      note: "Continue with the same section and inventory_hash. A changed inventory returns 409 and no mixed-version page.",
    } };
  }
  return result;
}

async function researchOutputsTool(name, args, env) {
  const now = Date.now();
  try {
    if (name === "shipyard_research_capability_page" && !researchCapabilityPageArgumentsValid(args)) {
      return json({ schema: "SHIPYARD_RESEARCH_CAPABILITIES_V1", status: "invalid_request", message: "A supported section and bounded pagination values are required." }, 400);
    }
    if (name === "shipyard_research_catalog") {
      const catalog = SHIPYARD_RESEARCH_CATALOG, kind = args.catalog || "source_registry", offset = args.offset || 0, limit = args.limit || 10;
      if (args.catalog_hash && args.catalog_hash !== catalog.catalog_sha256) return json({ schema: "SHIPYARD_RESEARCH_CATALOG_V1", status: "catalog_changed", message: "The published catalog changed. Restart at offset zero; no mixed-version page was returned." }, 409);
      const rows = catalog.catalogs[kind];
      return researchResponse({ schema: "SHIPYARD_RESEARCH_CATALOG_V1", status: "static_research", retrieved_at: new Date(now).toISOString(),
        catalog: kind, catalog_sha256: catalog.catalog_sha256, source_registry_version: catalog.source_registry_version,
        evidence_contract_version: catalog.evidence_contract_version, source_as_of: catalog.as_of, count_reconciliation: catalog.count_reconciliation,
        rows: rows.slice(offset, offset + limit), pagination: { offset, limit, total: rows.length, next_offset: offset + limit < rows.length ? offset + limit : null },
        restrictions: { live_market_data: false, runtime_verified_by_catalog: false, decision_eligible: false, user_inputs_uploaded: false,
          note: "Exact static browser research catalog, not running-engine proof. Catalog status/confidence are original research/engineering claims, not current producer health, trading performance or data rights. Capability inventory governs current access; source restrictions are preserved." } });
    }
    if (name === "shipyard_lector_output") return researchResponse(researchLectorProjection(await researchLectorRow(env, args), args, now));
    if (name === "shipyard_aperture_output") return researchResponse(researchApertureProjection(await researchApertureRow(env), now));
    const readMetadata = async (fn, engine) => { try { return await fn(); } catch { return researchEnvelope(engine, now, "unavailable", { reason: "Stored research read failed; no fallback/sample substituted." }); } };
    const [lector, aperture] = await Promise.all([
      readMetadata(async () => researchLectorProjection(await researchLectorRow(env, {}), {}, now, true), "lector"),
      readMetadata(async () => researchApertureProjection(await researchApertureRow(env), now, true), "aperture"),
    ]);
    const inventory = { schema: "SHIPYARD_RESEARCH_CAPABILITIES_V1", adapter_version: RESEARCH_OUTPUT_VERSION, retrieved_at: new Date(now).toISOString(),
      status: "partial", scope: "This deployed Site's reviewed research adapters, not a claim about external runtimes.", provider_requests_made: false, producer_execution_enabled: true,
      preopen_input_collection: {writer:"shipyard_capture_preopen_inputs",readers:["shipyard_preopen_status","shipyard_preopen_inputs"],scope:"Fixed SPY/QQQ raw IEX immutable inputs only; no reference/engine execution",diagnostic_never_eligible:true,schedule_status:"not_observed_by_this_read",persistence_verified_by_this_call:false},
      runtime_configuration: { alpaca_keys_present: typeof env?.ALPACA_API_KEY_ID === "string" && env.ALPACA_API_KEY_ID.length > 0 && typeof env?.ALPACA_API_SECRET_KEY === "string" && env.ALPACA_API_SECRET_KEY.length > 0,
        note: "Presence only, using the existing /api/status criterion; no secret values are returned and no entitlement or current feed delivery is inferred." },
      surface_coverage: { ...SHIPYARD_RESEARCH_SURFACES, route_count: SHIPYARD_RESEARCH_SURFACES.surfaces.length,
        note: "All current router keys, including ticker detail. Browser-local state is input-required and not synchronized. Options views read selected Tradier chains and delayed Alpaca indicative trades; GEX is a model; FINRA dark-pool activity is weekly aggregate; movers use Alpaca SIP; Azrael uses Cboe/Alpaca sources. House/Senate and SEC disclosure views open official portals; SEC automated access requires a declared operator contact. Calendar and News remain bounded on-request feeds; static definitions do not prove current provider access." },
      engines: [
        { engine: "tradier_options_research", status: "on_request_not_run", tools: ["shipyard_options_expirations","shipyard_options_chain"], source: "Connected Tradier production provider, standard contracts only; selected page can open a live quote stream", restrictions: "Separate expiration discovery and one complete bounded single-expiry capture; no entitlement inferred here. Quote and hourly Greek clocks separate, stale valid values retained for research, execution_pricing=false. OI as-of and displayed quote-size units unknown. Stateless cursor pagination refetches each page and preserves its own receipt. WebSocket streams only the selected page of up to 50 OCC contracts; no broad options flow, full-market coverage, accounts or orders." },
        { engine: "trade_brain", status: "on_request_not_run", tool: "shipyard_trade_brain_scan", freshness: "checked by the existing scan when called", restrictions: "Regular-session and source-specific freshness/eligibility gates apply at acquisition and delivery. Configured Tradier uses live bid/ask and timestamped ORATS Greeks no older than 75 minutes; failures do not switch feeds. Otherwise Alpaca options use modified indicative quotes, delayed trades and Black-Scholes Greeks. execution_pricing describes the quote basis (true only for Tradier), not trade eligibility; every candidate remains broker_quote_required. No orders or background scan." },
        { engine: "stock_quote_snapshot", status: "on_request_not_run", tool: "shipyard_stock_quote", source: "Existing Alpaca REST quote helper with SIP-to-IEX fallback", restrictions: "One-symbol REST snapshot, not continuous ticks. No competing provider WebSocket, option scanner or trading action; provider clocks and stale states explicit." },
        { engine: "integrated_daily_research", status: "on_request_not_run", tool: "shipyard_research_snapshot", source: "Exact browser research-adapter logic over existing server IEX bars and context", restrictions: "Seven daily features when inputs suffice; paged evidence/observations; rights/lineage gates unchanged. This route does not invoke Saty/RRE or forecast engines and does not accept local CSV/manual uploads." },
        { engine: "alpaca_daily", status: "on_request_not_run", tool: "shipyard_alpaca_daily_bars", source: "Alpaca IEX split-adjusted daily bars", restrictions: "Single exchange, not consolidated SIP. Calendar and source timestamps returned by the tool; configuration is not entitlement proof." },
        { engine: "chartlector_context", status: "on_request_not_run", tool: "shipyard_market_context", source: "Published Chartlector artifact plus Treasury, Federal Reserve and Cboe observations", restrictions: "Artifact/source dates govern freshness. This Site does not execute or refresh the upstream Chartlector publisher." },
        { engine: "aperture_on_demand", status: "on_request_not_run", tool: "shipyard_aperture_scan", source: "Original October Aperture per-symbol core; IEX all-adjusted histories plus QQQ", restrictions: "Requested-symbol subset, global shortlist bypass, stricter current seal; not stored September vintage or full scan. No accounts/orders or persistent producer." },
        { engine: "lector_on_demand", status: "on_request_not_run", tool: "shipyard_lector_scan", source: "Exact original desk-read-16 source vintage over fresh provider capture of completed daily IEX split-adjusted bars", restrictions: "Chart-only research computation, original unknown factors retained; no positions/news/fundamentals/options context, intraday signals, trade admission or persistent producer. Separate from stored-output tool." },
        { ...lector, tool: "shipyard_lector_output" }, { ...aperture, tool: "shipyard_aperture_output" },
        { engine: "official_scheduled_events", status: "on_request_scoped", tool: "shipyard_official_events", source: "Official BLS ICS/monthly list, with seven selected BLS release calendars on FRED when both BLS endpoints deny access, plus BEA release-date JSON and the Federal Reserve Board calendar", restrictions: "Current/next New York month only; the FRED fallback covers seven named BLS releases, not the full BLS schedule. Missing publisher scope remains unknown. No earnings/unscheduled news, universal all-clear, RRE gate activation or historical availability proof." },
        { engine: "alpaca_news", status: "on_request", tool: "shipyard_news_feed", source: "Alpaca market-news REST endpoint", restrictions: "Latest 1–50 provider articles, optional 1–10 symbol filter. Article clocks and retrieval receipts are preserved; plan entitlement can delay delivery. No WebSocket, comprehensive coverage claim, engine signal, persistence or order route." },
        { engine: "exchange_calendar_inputs", status: "on_request", tool: "shipyard_exchange_calendar", source: "Official Alpaca v2 US-equity market calendar", restrictions: "At most370 inclusive dates; explicit New York and UTC sessions/receipt. No synthetic sessions, historical availability proof, account/order data or engine execution." },
        { engine: "intraday_provider_inputs", status: "on_request", tool: "shipyard_intraday_bars", source: "Alpaca raw 1/5/10-minute bars; explicit IEX or SIP, no silent fallback", freshness: "Returned source bar clocks and actual receipt; partial bars excluded, no continuous stream", restrictions: "Not a Saty/RRE engine run. All sessions; requires verified engine-specific calendar/resampling. Historical availability is unknown; provider revisions are possible." },
        { engine: "morgue", status: "metadata_only", tool: "shipyard_morgue_readiness", source_id: MORGUE_SNAPSHOT_METADATA.source_id, generated_at: MORGUE_SNAPSHOT_METADATA.generated_at_utc,
          freshness: "unknown", values_returned: false, decision_eligible: false, restrictions: "Existing metadata-only rights, freshness, point-in-time and performance gates remain closed." },
        { engine: "saty", status: "remote_adapter_available_not_run", tools: ["shipyard_python_status","shipyard_python_run","shipyard_python_job"], service_configured: !!shipyardPythonServiceToken(env), output: null, reason: "Fixed-origin Python research bridge is implemented. This inventory does not check the service or execute a job. Actual TLS, adapter/build contract, market inputs and engine gates must pass; credential presence is not operational proof." },
        { engine: "raschke_rre", status: "remote_adapter_available_not_run", tools: ["shipyard_python_status","shipyard_python_run","shipyard_python_job"], service_configured: !!shipyardPythonServiceToken(env), output: null, reason: "Fixed-origin Python research bridge is implemented. This inventory does not check the service or execute a job. Actual TLS, adapter/build contract, market inputs and engine gates must pass; credential presence is not operational proof." },
        { engine: "forecast_fe01_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: SHIPYARD_FORECAST_TREND_FEATURES.FE01_TREND_POLICY, restrictions: "NEW daily-price policy on505 completed official sessions,split-adjusted dividend-excluded IEX. Original fixed coefficients,not fitted/calibrated; current acquisition and historical PIT are not established by this inventory." },
        { engine: "forecast_fe02_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: SHIPYARD_FORECAST_PAIRED_FEATURES.FE02_PAIRED_POLICY, restrictions: "NEW V2 paired residual policy with session-relative descriptive availability, actual source age, independent original48h age diagnostic and7-day extended-closure guard on505 matched completed official sessions for requested ticker plus SPY,split-adjusted dividend-excluded IEX. Original builder unavailable; current prior-only beta is reused on reconstructed history, so historical PIT is not claimed. Fixed scorer uncalibrated; decision eligibility closed." },
        { engine: "forecast_fe03_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: SHIPYARD_FORECAST_FE03_FEATURES.FE03_BREAKOUT_POLICY, restrictions: "NEW daily breakout acceptance policy on505 completed IEX split-adjusted OHLCV sessions. Requires latest candidate to remain at/above its frozen level,3–5 post-cross closes and20 matured historical episodes after candidate-ID exclusion; no setup, incomplete/invalidated setup or short denominator abstains without a score. Five-session outcome windows can overlap and are non-independent; sample floor is provisional, not statistical/calibration proof. Original48h age is diagnostic; original builder/PIT,rights,quality and decision eligibility remain unverified/closed." },
        { engine: "forecast_fe04_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: { id: SHIPYARD_FORECAST_FE04_FEATURES.FE04_GAP_POLICY.id, version: SHIPYARD_FORECAST_FE04_FEATURES.FE04_GAP_POLICY.version, sha256: SHIPYARD_FORECAST_FE04_FEATURES.FE04_GAP_POLICY_SHA256 }, restrictions: "NEW 62-session IEX split-adjusted 1m gap-factor/first-five-close acceptance policy for SPY/QQQ/IWM. Fair gap is predicted from prior-only OLS without SPY self-benchmark; premarket dollar-volume transform is a proxy, not depth. Six-page/symbol cap, three symbols, request/byte/deadline limits; missing slots/pagination abstain. Original builder, historical PIT, quality, calibration and decision eligibility unverified/closed." },
        { engine: "forecast_fe05_source_policy", status: "on_request_new_policy_private", tool: "shipyard_forecast_from_bars", policy: {id:SHIPYARD_FE05_FEATURES.FE05_BREADTH_POLICY.id,sha256:SHIPYARD_FE05_FEATURES.FE05_BREADTH_POLICY_SHA256}, restrictions: "NEW date-only current SPY holdings top25 CUSIP-issuer cohort; aggregates share classes before weight ranking and requires505 matched complete IEX closes per selected security plus SPY. Emits cohort-relative breadth/advance-decline/new-high-low/trend measurements only; member names stay private, cash/CVR excluded explicitly, file residual is not normalized away. Not historical S&P 500/PIT/all-market breadth; first-seen is not source observation, SSGA rights not cleared; research-only/ineligible and never publicly projected." },
        { engine: "forecast_fe06_source_policy", status: "on_request_new_policy_private_research", tool: "shipyard_forecast_from_sources", policy: SHIPYARD_FE06_POLICY, policy_sha256: SHIPYARD_FE06_POLICY_SHA256, restrictions: "NEW fixed 11-ETF issuer NAV/share/assets derivation, target-sector 21-session dividend-excluded momentum rank, positive breadth, prior252 daily dispersion z and target-fund prior252 creation/redemption estimate z. Uses verified 2025-12-05 2:1 action table; raw-source publication time unknown; first-seen download time preserved; latest common cutoff may lag latest market session within a separate48h source-age rule. Bounded on-demand private research; source-use and redistribution rights are not established. Raw workbooks are not persisted or publicly projected. Research only, exact scorer unchanged, not observed flow/volume/AUM residual; no historical PIT, calibration or decision eligibility." },
        { engine: "forecast_fe07_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: {id:SHIPYARD_FE0710_FEATURES.FE07_LEADLAG_POLICY.id,sha256:SHIPYARD_FE0710_FEATURES.FE07_LEADLAG_POLICY_SHA256}, restrictions: "NEW fixed daily SPY-leader/QQQ-follower one-session lag proxy on505 matched IEX split-adjusted dividend-excluded sessions.252 prior lagged OLS pairs, candidate leader-return z normalized only on the prior252 returns, and four disjoint63-pair sign blocks; no graph, lag or universe search. Negative beta is preserved. Source observation age is distinct from receipt and original48h age is reported separately;7-day guard. No causal-lead, PIT, calibration, rights, quality or decision-eligibility claim." },
        { engine: "forecast_fe08_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: SHIPYARD_FORECAST_FEATURES.FE08_RV_POLICY, restrictions: "FE08 uses its separate new explicit measurement policy. Fixed original coefficients, not fitted/calibrated. Other FE feature builders remain separate." },
        { engine: "forecast_fe09_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: { id: SHIPYARD_FORECAST_FE09_FEATURES.FE09_JUMP_POLICY.id, version: SHIPYARD_FORECAST_FE09_FEATURES.FE09_JUMP_POLICY.version, sha256: SHIPYARD_FORECAST_FE09_FEATURES.FE09_JUMP_POLICY_SHA256 }, restrictions: "NEW 22 completed IEX 5m sessions with explicit finite-sample RV−BV, prior-only z-scores and next-five-official-session date counts across named BEA/Federal Reserve and exactly seven BLS families (primary or complete FRED fallback). Missing family scope abstains; event-date precision is preserved; zero is not all-clear. Original builder, historical PIT, calibration and decision eligibility unverified/closed." },
        { engine: "forecast_fe10_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: {id:SHIPYARD_FE0710_FEATURES.FE10_REGIME_POLICY.id,sha256:SHIPYARD_FE0710_FEATURES.FE10_REGIME_POLICY_SHA256}, restrictions: "NEW fixed SPY/QQQ/IWM proxy panel on505 matched IEX split-adjusted dividend-excluded sessions.21-session RV/correlation, covariance PSD check and252 prior-only z normalizers; bounded disjoint-window volatility contrast is not a fitted change-point detector. Not broad-market/all-asset correlation. Source age distinct from receipt, original48h age reported,7-day guard. No PIT, calibration, rights, quality or decision-eligibility claim." },
        { engine: "forecast_fe12_source_policy", status: "on_request_new_policy", tool: "shipyard_forecast_from_bars", policy: { id: SHIPYARD_FORECAST_FE12_FEATURES.FE12_TOP_OF_BOOK_POLICY.id, version: SHIPYARD_FORECAST_FE12_FEATURES.FE12_TOP_OF_BOOK_POLICY.version, sha256: SHIPYARD_FORECAST_FE12_FEATURES.FE12_TOP_OF_BOOK_POLICY_SHA256 }, restrictions: "NEW IEX historical L1/TOPS point snapshots only: latest descending limit-1 quote in the five seconds before the latest completed five-minute RTH bucket at actual evaluation, current plus16 same-elapsed-RTH prior sessions. Early-close exclusions are calendar-only; missing selected data never backfills. Cursor denotes older rows, not stream completeness; no window mean. V2 fixed09:35 is preserved as superseded baseline. V1 five-minute prefix policy is blocked after a 1000-row probe spanned only2.403 seconds. IEX aggregate sizes are shares; visible one-level USD notional is not L2/full depth. Bar pages/bytes/deadline bounded, current age<=300s. The existing connector probe returned 1000 IEX quotes but does not verify Site worker credentials/path or future live acceptance; historical PIT is unknown. No calibration or decision eligibility." },
        { engine: "chartslector_archive_subset", status: "on_request", tool: "shipyard_chartslector_scan", source: SHIPYARD_CHARTSLECTOR.CHARTSLECTOR_SOURCE, restrictions: "Pinned RS26/78/156, alerts, RRR and candle stages on one/two requested symbols plus SPY. Not ranker, breadth, LoD or full-universe scan." },
        { engine: "forecast_numeric_calculators", status: "on_request_explicit_scalars", tools: ["shipyard_forecast_catalog", "shipyard_forecast_evaluate"],
          engine_count: 30, source: SHIPYARD_FORECAST_LOGIC.SILICON_FORECAST_SOURCE,
          restrictions: "Exact existing numeric scoring layer, not the full Python ForecastEngine validation runtime. Explicit scalar requests remain manual_unverified; this interface does not invoke feature builders, provider/PIT verification or fitted probabilities. FE01, FE02, FE03, FE04, FE05, FE07, FE08, FE09, FE10 and FE12 source-policy paths are available through from-bars; FE06 uses the separate issuer from-sources contract; the other19 feature pipelines are not connected. Browser-local CSV/manual-input policies are unchanged. No provider/database access or orders." },
        { engine: "browser_local_labs", status: "not_hosted", tool: null, output: null, reason: "Manual/CSV research, evidence exports, watchlists and alerts remain browser-local; not substituted for live engine outputs." },
        { engine: "static_research_catalog", status: "static_research", tool: "shipyard_research_catalog", source: "The same source-policy, survivor, family-crosswalk and vendor catalog constants served to the browser", restrictions: "No live outputs or user-local inputs. Existing source registry blocks server upload of browser-only manual/CSV inputs." },
      ],
      native_inspection: { tool: "Sites read_database_table_rows", purpose: "Owner-only bounded inspection already supports research table metadata. Generic cell truncation is not a complete engine payload.", tables: ["observatory_ingest_runs", "observatory_market_bars", "observatory_source_records", "observatory_relationship_registry", "aperture_asset_registry"], populated_or_fresh: "not_checked_by_this_tool" },
      boundaries: { account_data: false, orders: false, arbitrary_urls: false, arbitrary_sql: false, database_writes: false, retired_routes_restored: false },
    };
    const inventoryHash = await researchCapabilitiesHash(inventory);
    if (args.inventory_hash && args.inventory_hash !== inventoryHash) return json({ schema: "SHIPYARD_RESEARCH_CAPABILITIES_V1", status: "inventory_changed", inventory_sha256: inventoryHash,
      message: "Stored research metadata or capability inventory changed. Restart at offset zero; no mixed-version page was returned." }, 409);
    const section = args.section || "summary", offset = args.offset || 0, limit = args.limit || RESEARCH_CAPABILITY_PAGE_SIZE;
    return researchResponse(researchCapabilitiesProjection(inventory, section, offset, limit, inventoryHash));
  } catch {
    return researchResponse(researchEnvelope(name === "shipyard_lector_output" ? "lector" : "aperture", now, "unavailable", { reason: "Stored research read failed; no fallback/sample substituted." }));
  }
}
