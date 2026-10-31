// Bounded private bridge from the existing Alpaca News reader to the pinned
// Psychology Engine v0.4.1 lexicon baseline. The source article exists only in
// memory while scoring: no headline, summary, URL, body, or raw-token list is
// returned or written. This adapter is descriptive research only.

const SHIPYARD_PSYCHOLOGY_SCHEMA = "SHIPYARD_PSYCHOLOGY_HEADLINE_TONE_V1";
const SHIPYARD_PSYCHOLOGY_ENGINE_VERSION = "0.4.1";
const SHIPYARD_PSYCHOLOGY_ENGINE_ARCHIVE_SHA256 = "a054e64ae833ee9f7de41666959c7548a2780e211600f446607f4c2271d7f711";
const SHIPYARD_PSYCHOLOGY_SCORER = "transparent-en-v1";
const SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY = "alpaca_news";
const SHIPYARD_PSYCHOLOGY_MAX_AGE_SECONDS = 900;
const SHIPYARD_PSYCHOLOGY_SOURCE_TERMS_STATUS = "general_personal_noncommercial_terms_reviewed_market_data_reproduction_scope_for_news_unknown_derived_retention_unspecified";
const SHIPYARD_PSYCHOLOGY_MAX_CAPTURE_RUNS = 10000;
const SHIPYARD_PSYCHOLOGY_MAX_OBSERVATIONS = 100000;
const SHIPYARD_PSYCHOLOGY_RUN_COLUMNS = [
  "capture_id", "started_at", "completed_at", "status", "provider", "source_family",
  "request_symbols_json", "requested_limit", "retrieved_at", "served_at", "cache_hit",
  "source_status", "source_error", "source_manifest_sha256", "articles_seen",
  "observations_inserted", "duplicates", "rejected", "source_purpose_policy_status",
  "source_purpose_policy_version", "source_terms_status", "account_terms_status", "error_code",
];
const SHIPYARD_PSYCHOLOGY_OBSERVATION_COLUMNS = [
  "observation_id", "capture_id", "source_family", "provider", "source_item_id", "revision_hash",
  "supersedes_observation_id", "publisher", "event_at", "event_time_basis", "updated_at", "first_seen_at",
  "provider_received_at", "provider_received_at_basis", "locally_received_at", "extracted_at",
  "available_at", "max_age_seconds", "source_population", "source_independence", "revision_basis",
  "symbols_json", "sentiment_value", "uncertainty_value",
  "matched_tokens", "model_version", "formula_version", "parameter_hash", "input_hash",
  "source_purpose_policy_status", "source_purpose_policy_version", "source_terms_status", "account_terms_status",
];

const SHIPYARD_PSYCHOLOGY_POSITIVE = new Set(["gain", "growth", "optimistic", "bullish", "improve", "strong"]);
const SHIPYARD_PSYCHOLOGY_NEGATIVE = new Set(["loss", "fear", "bearish", "weak", "panic", "decline"]);
const SHIPYARD_PSYCHOLOGY_UNCERTAIN = new Set(["may", "might", "uncertain", "risk", "possibly", "unknown"]);
const SHIPYARD_PSYCHOLOGY_NEGATORS = new Set(["not", "never", "no"]);

function shipyardPsychologyScoreHeadline(text) {
  const words = typeof text === "string" ? (text.toLowerCase().match(/[a-z]+/g) || []) : [];
  const matches = [];
  for (let index = 0; index < words.length; index += 1) {
    const word = words[index];
    let value = SHIPYARD_PSYCHOLOGY_POSITIVE.has(word) ? 1 : SHIPYARD_PSYCHOLOGY_NEGATIVE.has(word) ? -1 : 0;
    if (value) {
      if (words.slice(Math.max(0, index - 3), index).some((prior) => SHIPYARD_PSYCHOLOGY_NEGATORS.has(prior))) value *= -1;
      matches.push(value);
    }
  }
  return {
    sentiment: matches.length ? matches.reduce((sum, value) => sum + value, 0) / matches.length : null,
    uncertainty: words.length ? words.filter((word) => SHIPYARD_PSYCHOLOGY_UNCERTAIN.has(word)).length / words.length : null,
    matched_tokens: matches.length,
    model: SHIPYARD_PSYCHOLOGY_SCORER,
  };
}

function shipyardPsychologyIsoMillis(value) {
  if (typeof value !== "string" || value.length > 64) return null;
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|([+-])(\d{2}):(\d{2}))$/);
  if (!match) return null;
  const year = Number(match[1]), month = Number(match[2]), day = Number(match[3]);
  const hour = Number(match[4]), minute = Number(match[5]), second = Number(match[6]);
  const offsetHour = match[9] === undefined ? 0 : Number(match[9]), offsetMinute = match[10] === undefined ? 0 : Number(match[10]);
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth || hour > 23 || minute > 59 || second > 59
    || offsetHour > 23 || offsetMinute > 59) return null;
  const milliseconds = Date.parse(value);
  return Number.isFinite(milliseconds) ? milliseconds : null;
}

function shipyardPsychologyIso(milliseconds) { return new Date(milliseconds).toISOString(); }
function shipyardPsychologyMean(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
function shipyardPsychologyPlaceholders(count) { return Array.from({ length: count }, () => "?").join(","); }

async function shipyardPsychologySha256(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function shipyardPsychologyFreshness(nowMs, eventMs) {
  const ageSeconds = (nowMs - eventMs) / 1000;
  return { ageSeconds, status: ageSeconds < 0 ? "future_dated" : ageSeconds <= 90 ? "current" : ageSeconds <= SHIPYARD_PSYCHOLOGY_MAX_AGE_SECONDS ? "recent" : "stale" };
}

function shipyardPsychologySafeCode(value, fallback = "source_error") {
  return typeof value === "string" && /^[a-z0-9_-]{1,64}$/i.test(value) ? value.toLowerCase() : fallback;
}

async function shipyardPsychologyDerive(news, { firstSeenAt = new Date().toISOString(), computedAt = new Date().toISOString() } = {}) {
  if (!news || news.schema !== "SHIPYARD_ALPACA_NEWS_V1") {
    return { schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "invalid", error: "unsupported_news_response", evidence: [] };
  }
  if (!["connected", "partial", "no_articles"].includes(news.status)) {
    const sourceReceivedMs = shipyardPsychologyIsoMillis(news.retrieved_at);
    const extractionMs = shipyardPsychologyIsoMillis(computedAt);
    return {
      schema: SHIPYARD_PSYCHOLOGY_SCHEMA,
      status: news.status === "unavailable" ? "unavailable" : "unknown",
      source_error: shipyardPsychologySafeCode(news.error, "source_status_unknown"),
      engine_reference: { version: SHIPYARD_PSYCHOLOGY_ENGINE_VERSION, scorer: SHIPYARD_PSYCHOLOGY_SCORER, archive_sha256: SHIPYARD_PSYCHOLOGY_ENGINE_ARCHIVE_SHA256 },
      as_of: extractionMs === null ? null : shipyardPsychologyIso(extractionMs),
      computed_at: extractionMs === null ? null : shipyardPsychologyIso(extractionMs),
      source: { provider: "Alpaca Market Data News", family: SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY,
        status: news.status || "unknown", retrieved_at: sourceReceivedMs === null ? null : shipyardPsychologyIso(sourceReceivedMs),
        served_at: shipyardPsychologyIsoMillis(news.served_at) === null ? null : shipyardPsychologyIso(shipyardPsychologyIsoMillis(news.served_at)),
        source_terms_status: SHIPYARD_PSYCHOLOGY_SOURCE_TERMS_STATUS, account_terms_status: "unknown_not_verified" },
      aggregate: { sentiment: { value: null, units: "lexicon_score_v1", matched_article_count: 0 }, uncertainty: { value: null, units: "uncertainty_token_fraction", article_count: 0 }, stale_count: 0, missingness: "source_unavailable_or_unknown" },
      evidence: [], quality: { partial: true, raw_text_in_output: false }, authority: { advisory_only: true, automatic_strategy_change: false, order_submission_enabled: false },
    };
  }
  const retrievedMs = shipyardPsychologyIsoMillis(news.retrieved_at);
  const servedMs = shipyardPsychologyIsoMillis(news.served_at) ?? retrievedMs;
  const requestStartedMs = shipyardPsychologyIsoMillis(firstSeenAt);
  const computedMs = shipyardPsychologyIsoMillis(computedAt);
  if (retrievedMs === null || servedMs === null || requestStartedMs === null || computedMs === null
    || retrievedMs > computedMs || servedMs > computedMs || requestStartedMs > computedMs
    || !Array.isArray(news.articles) || news.articles.length > 50) {
    return { schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "invalid", error: "invalid_response_clocks_or_rows", evidence: [] };
  }
  // First seen is the adapter's local observation of the returned response,
  // not the earlier start of an API request.
  const firstSeenMs = Math.max(requestStartedMs, retrievedMs, servedMs);
  const seen = new Map(), evidence = [];
  const issues = { invalid_rows: 0, duplicate_ids: 0, revision_conflicts: 0, future_dated: 0 };
  for (const article of news.articles) {
    const eventMs = shipyardPsychologyIsoMillis(article?.created_at);
    const updatedMs = shipyardPsychologyIsoMillis(article?.updated_at);
    if (!article || !Number.isSafeInteger(article.id) || article.id < 1 || typeof article.headline !== "string"
      || !article.headline.trim() || eventMs === null || updatedMs === null || !Array.isArray(article.symbols)) {
      issues.invalid_rows += 1;
      continue;
    }
    if (eventMs > retrievedMs || updatedMs > retrievedMs) { issues.future_dated += 1; continue; }
    const symbols = [...new Set(article.symbols.filter((symbol) => typeof symbol === "string" && /^[A-Za-z0-9./-]{1,20}$/.test(symbol))
      .map((symbol) => symbol.toUpperCase()))].sort();
    const publisher = (typeof article.source === "string" && article.source.trim() ? article.source.trim() : "unknown").slice(0, 120);
    const score = shipyardPsychologyScoreHeadline(article.headline);
    const eventAt = shipyardPsychologyIso(eventMs), updatedAt = shipyardPsychologyIso(updatedMs);
    // A content-free revision identity. Raw words are deliberately excluded;
    // this identifies observed score/clock revisions, not every text edit.
    const revisionBasis = {
      source_family: SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY, item_id: String(article.id), publisher,
      event_at: eventAt, updated_at: updatedAt, symbols,
      sentiment_value: score.sentiment, uncertainty_value: score.uncertainty,
      matched_tokens: score.matched_tokens, model: SHIPYARD_PSYCHOLOGY_SCORER,
    };
    const revisionHash = await shipyardPsychologySha256(JSON.stringify(revisionBasis));
    const prior = seen.get(article.id);
    if (prior) {
      issues.duplicate_ids += 1;
      if (prior !== revisionHash) issues.revision_conflicts += 1;
      continue;
    }
    seen.set(article.id, revisionHash);
    const freshness = shipyardPsychologyFreshness(computedMs, eventMs);
    const servedAt = shipyardPsychologyIso(servedMs);
    const firstSeen = shipyardPsychologyIso(firstSeenMs);
    const extractedAt = shipyardPsychologyIso(computedMs);
    const availableAt = shipyardPsychologyIso(Math.max(retrievedMs, servedMs, firstSeenMs, computedMs));
    evidence.push({
      evidence_id: `alpaca-news:${article.id}:${revisionHash}`,
      item_id: String(article.id), revision_hash: revisionHash,
      revision_basis: "derived_score_clock_metadata_v1",
      source_family: SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY,
      provider: "Alpaca Market Data News", publisher,
      source_population: "Latest Alpaca articles returned for this request; not an investor sample",
      source_independence: "not_assessed_single_feed",
      symbols, event_at: eventAt, event_time_basis: "Alpaca_created_at",
      updated_at: updatedAt, first_seen_at: firstSeen,
      provider_received_at: null,
      provider_received_at_basis: "provider_receive_clock_not_supplied_by_existing_route",
      locally_received_at: servedAt, served_at: servedAt, extracted_at: extractedAt,
      available_at: availableAt, max_age_seconds: SHIPYARD_PSYCHOLOGY_MAX_AGE_SECONDS,
      freshness_status: freshness.status, freshness_included: ["current", "recent"].includes(freshness.status),
      age_seconds: freshness.ageSeconds,
      measures: {
        sentiment: { value: score.sentiment, units: "lexicon_score_v1", matched_tokens: score.matched_tokens, model: score.model },
        uncertainty: { value: score.uncertainty, units: "uncertainty_token_fraction", model: score.model },
      },
      missing_reason: score.sentiment === null ? "no_lexicon_sentiment_matches" : null,
      storage_scope: "owner_private_content_free_derived_only",
      raw_content_returned_or_stored: false,
    });
  }
  evidence.sort((left, right) => Date.parse(right.available_at) - Date.parse(left.available_at) || Number(left.item_id) - Number(right.item_id));
  const eligible = evidence.filter((item) => item.freshness_included);
  const sentiments = eligible.map((item) => item.measures.sentiment.value).filter((value) => value !== null);
  const uncertainties = eligible.map((item) => item.measures.uncertainty.value).filter((value) => value !== null);
  return {
    schema: SHIPYARD_PSYCHOLOGY_SCHEMA,
    status: sentiments.length ? "available_advisory" : eligible.length ? "no_sentiment_matches" : evidence.length ? "stale_or_unknown" : "no_usable_evidence",
    engine_reference: { version: SHIPYARD_PSYCHOLOGY_ENGINE_VERSION, scorer: SHIPYARD_PSYCHOLOGY_SCORER, archive_sha256: SHIPYARD_PSYCHOLOGY_ENGINE_ARCHIVE_SHA256 },
    as_of: shipyardPsychologyIso(computedMs), computed_at: shipyardPsychologyIso(computedMs),
    source: {
      provider: "Alpaca Market Data News", family: SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY,
      status: news.status, retrieved_at: shipyardPsychologyIso(retrievedMs), served_at: shipyardPsychologyIso(servedMs), cache_hit: news.cache_hit === true,
      requested_limit: Number.isInteger(news.requested_limit) ? news.requested_limit : null,
      returned_article_count: evidence.length,
      source_article_count: Number.isSafeInteger(news.source_article_count) ? news.source_article_count : evidence.length,
      invalid_article_count: Number.isSafeInteger(news.invalid_article_count) ? news.invalid_article_count : 0,
      partial_article_count: Number.isSafeInteger(news.partial_article_count) ? news.partial_article_count : 0,
      provider_validation_issues: news.validation_issues && typeof news.validation_issues === "object" && !Array.isArray(news.validation_issues)
        ? Object.fromEntries(Object.entries(news.validation_issues).filter(([key, value]) => /^[a-z0-9_-]{1,64}$/i.test(key) && Number.isSafeInteger(value) && value >= 0).slice(0, 32))
        : {},
      next_page_available: news.next_page_available === true,
      source_population: "Latest Alpaca articles returned for this request; not an investor sample",
      source_family_count: 1, independence_claim: "none",
      realtime_entitlement: "unknown", source_terms_status: SHIPYARD_PSYCHOLOGY_SOURCE_TERMS_STATUS,
      account_terms_status: "unknown_not_verified",
    },
    aggregate: {
      sentiment: { value: shipyardPsychologyMean(sentiments), units: "lexicon_score_v1", matched_article_count: sentiments.length },
      uncertainty: { value: shipyardPsychologyMean(uncertainties), units: "uncertainty_token_fraction", article_count: uncertainties.length },
      stale_count: evidence.filter((item) => item.freshness_status === "stale").length,
      missingness: sentiments.length ? null : "no_fresh_lexicon_matches",
    },
    evidence,
    quality: { issues, partial: Object.values(issues).some((count) => count > 0) || news.status === "partial" || news.next_page_available === true, raw_text_in_output: false },
    limits: [
      "This is headline wording, not investor sentiment, representative consensus, positioning, or private thought.",
      "Summaries, article content, URLs, authors, and raw tokens are not scored, stored, or returned.",
      "One provider feed is not independent-source confirmation; publisher copies are not deduplicated across feeds.",
      "The transparent lexicon is uncalibrated and not a validated predictive signal or alpha.",
      "May inform discretionary simulated-trade discussion only; no automatic strategy, sizing, risk, or order authority.",
    ],
    authority: { advisory_only: true, llm_may_use_as_context: true, automatic_strategy_change: false, order_submission_enabled: false },
  };
}

function shipyardPsychologySourcePurposePolicy(env) {
  const version = env?.SHIPYARD_PSYCHOLOGY_SOURCE_PURPOSE_POLICY_VERSION;
  const hash = env?.SHIPYARD_PSYCHOLOGY_SOURCE_PURPOSE_POLICY_SHA256;
  const reviewed = env?.SHIPYARD_PSYCHOLOGY_SOURCE_PURPOSE_POLICY_STATUS === "reviewed_private_derived"
    && env?.SHIPYARD_PSYCHOLOGY_SOURCE_PURPOSE_POLICY_SCOPE === "owner_private_noncommercial_derived_only"
    && typeof version === "string" && /^[A-Za-z0-9._-]{1,64}$/.test(version)
    && typeof hash === "string" && /^[a-f0-9]{64}$/.test(hash);
  return {
    status: reviewed ? "reviewed_private_derived" : "pending_explicit_source_purpose_review",
    version: reviewed ? version : null, sha256: reviewed ? hash : null,
    scope: reviewed ? "owner_private_noncommercial_derived_only" : "owner_private_personal_noncommercial_derived_only_pending_review",
    source_terms_status: SHIPYARD_PSYCHOLOGY_SOURCE_TERMS_STATUS,
    account_terms_status: "unknown_account_specific_terms_not_verified",
    raw_source_text_storage: false, redistribution: false,
  };
}

function shipyardPsychologyManifest(tone) {
  return (tone.evidence || []).map((item) => ({
    item_id: item.item_id, revision_hash: item.revision_hash, publisher: item.publisher,
    event_at: item.event_at, updated_at: item.updated_at, symbols: item.symbols,
    available_at: item.available_at, sentiment_value: item.measures.sentiment.value,
    uncertainty_value: item.measures.uncertainty.value, matched_tokens: item.measures.sentiment.matched_tokens,
  }));
}

async function shipyardPsychologyPersist(env, tone, capture) {
  const policy = shipyardPsychologySourcePurposePolicy(env);
  const base = {
    status: "not_written_source_policy_pending", policy_status: policy.status,
    policy_version: policy.version, account_terms_status: policy.account_terms_status,
    source_terms_status: policy.source_terms_status,
    raw_content_persisted: false, public_projection: false,
  };
  // The read path remains useful even while persistence review is pending.
  if (!policy.version || !policy.sha256) return base;
  if (!env?.DB) return { ...base, status: "not_written_storage_unavailable" };
  const manifest = shipyardPsychologyManifest(tone);
  const manifestHash = await shipyardPsychologySha256(JSON.stringify(manifest));
  let inserted = 0, duplicates = 0, capSkipped = 0, rejected = Number(tone.quality?.issues?.invalid_rows || 0) + Number(tone.source?.invalid_article_count || 0);
  const run = {
    capture_id: capture.id, started_at: capture.started_at, completed_at: null, status: "started",
    provider: "alpaca_market_data_news", source_family: SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY,
    request_symbols_json: JSON.stringify(capture.symbols), requested_limit: capture.limit,
    retrieved_at: capture.retrieved_at, served_at: capture.served_at, cache_hit: capture.cache_hit ? 1 : 0,
    source_status: capture.source_status, source_error: capture.source_error, source_manifest_sha256: manifestHash,
    articles_seen: Number(tone.source?.source_article_count ?? tone.source?.returned_article_count ?? 0), observations_inserted: 0,
    duplicates: 0, rejected, source_purpose_policy_status: policy.status,
    source_purpose_policy_version: policy.version, source_terms_status: policy.source_terms_status,
    account_terms_status: policy.account_terms_status, error_code: null,
  };
  try {
    // Hard global storage caps are enforced in the same SQLite statement as
    // each insert; a prior COUNT followed by a write is racy across captures.
    const runInsertSql = `INSERT INTO shipyard_psychology_capture_runs (${SHIPYARD_PSYCHOLOGY_RUN_COLUMNS.join(",")}) SELECT ${shipyardPsychologyPlaceholders(SHIPYARD_PSYCHOLOGY_RUN_COLUMNS.length)} WHERE (SELECT COUNT(*) FROM shipyard_psychology_capture_runs) < ?`;
    const runInsert = await env.DB.prepare(runInsertSql)
      .bind(...SHIPYARD_PSYCHOLOGY_RUN_COLUMNS.map((column) => run[column]), SHIPYARD_PSYCHOLOGY_MAX_CAPTURE_RUNS).run();
    if (Number(runInsert?.meta?.changes || 0) !== 1) {
      return { ...base, status: "not_written_capture_run_cap", max_capture_runs: SHIPYARD_PSYCHOLOGY_MAX_CAPTURE_RUNS };
    }
    for (const item of tone.evidence || []) {
      const priorExact = await env.DB.prepare("SELECT observation_id FROM shipyard_psychology_headline_tone_observations WHERE source_family=? AND source_item_id=? AND revision_hash=? LIMIT 1")
        .bind(SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY, item.item_id, item.revision_hash).first();
      if (priorExact) { duplicates += 1; continue; }
      const priorRevision = await env.DB.prepare("SELECT observation_id,updated_at FROM shipyard_psychology_headline_tone_observations WHERE source_family=? AND source_item_id=? AND available_at<=? ORDER BY available_at DESC,updated_at DESC LIMIT 1")
        .bind(SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY, item.item_id, item.available_at).first();
      const priorUpdatedMs = shipyardPsychologyIsoMillis(priorRevision?.updated_at);
      const incomingUpdatedMs = shipyardPsychologyIsoMillis(item.updated_at);
      const revisionBasis = priorUpdatedMs !== null && incomingUpdatedMs !== null && incomingUpdatedMs < priorUpdatedMs
        ? "derived_score_clock_metadata_v1_updated_at_regressed" : item.revision_basis;
      const observationId = await shipyardPsychologySha256(JSON.stringify([SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY, item.item_id, item.revision_hash]));
      const row = {
        observation_id: observationId, capture_id: capture.id, source_family: item.source_family,
        provider: item.provider, source_item_id: item.item_id, revision_hash: item.revision_hash,
        supersedes_observation_id: priorRevision?.observation_id || null, publisher: item.publisher,
        event_at: item.event_at, event_time_basis: item.event_time_basis,
        updated_at: item.updated_at, first_seen_at: item.first_seen_at,
        provider_received_at: null, provider_received_at_basis: item.provider_received_at_basis,
        locally_received_at: item.locally_received_at, extracted_at: item.extracted_at,
        available_at: item.available_at, max_age_seconds: item.max_age_seconds,
        source_population: item.source_population, source_independence: item.source_independence,
        revision_basis: revisionBasis,
        symbols_json: JSON.stringify(item.symbols), sentiment_value: item.measures.sentiment.value,
        uncertainty_value: item.measures.uncertainty.value, matched_tokens: item.measures.sentiment.matched_tokens,
        model_version: SHIPYARD_PSYCHOLOGY_SCORER,
        formula_version: `psychology-engine-${SHIPYARD_PSYCHOLOGY_ENGINE_VERSION}/alpaca-headline-score-clock-v1`,
        parameter_hash: policy.sha256, input_hash: item.revision_hash,
        source_purpose_policy_status: policy.status, source_purpose_policy_version: policy.version,
        source_terms_status: policy.source_terms_status, account_terms_status: policy.account_terms_status,
      };
      const observationInsertSql = `INSERT OR IGNORE INTO shipyard_psychology_headline_tone_observations (${SHIPYARD_PSYCHOLOGY_OBSERVATION_COLUMNS.join(",")}) SELECT ${shipyardPsychologyPlaceholders(SHIPYARD_PSYCHOLOGY_OBSERVATION_COLUMNS.length)} WHERE (SELECT COUNT(*) FROM shipyard_psychology_headline_tone_observations) < ?`;
      const result = await env.DB.prepare(observationInsertSql)
        .bind(...SHIPYARD_PSYCHOLOGY_OBSERVATION_COLUMNS.map((column) => row[column]), SHIPYARD_PSYCHOLOGY_MAX_OBSERVATIONS).run();
      if (Number(result?.meta?.changes || 0) > 0) inserted += 1;
      else {
        const concurrentDuplicate = await env.DB.prepare("SELECT observation_id FROM shipyard_psychology_headline_tone_observations WHERE source_family=? AND source_item_id=? AND revision_hash=? LIMIT 1")
          .bind(SHIPYARD_PSYCHOLOGY_SOURCE_FAMILY, item.item_id, item.revision_hash).first();
        if (concurrentDuplicate) duplicates += 1; else capSkipped += 1;
      }
    }
    rejected += capSkipped;
    const status = capture.source_status === "unavailable" ? "unavailable"
      : capture.source_status === "invalid" ? "invalid"
        : ["connected", "no_articles"].includes(capture.source_status) && !tone.quality?.partial && !capSkipped ? "complete" : "partial";
    const completedAt = new Date().toISOString();
    await env.DB.prepare("UPDATE shipyard_psychology_capture_runs SET completed_at=?,status=?,observations_inserted=?,duplicates=?,rejected=? WHERE capture_id=?")
      .bind(completedAt, status, inserted, duplicates, rejected, capture.id).run();
    return {
      status: status === "complete" ? "persisted" : `persisted_${status}`,
      policy_status: policy.status, policy_version: policy.version,
      source_terms_status: policy.source_terms_status, account_terms_status: policy.account_terms_status, capture_id: capture.id,
      source_manifest_sha256: manifestHash, observations_inserted: inserted,
      duplicates, rejected, cap_skipped: capSkipped, raw_content_persisted: false, public_projection: false,
    };
  } catch (error) {
    const code = shipyardPsychologySafeCode(error?.name, "storage_error");
    try {
      await env.DB.prepare("UPDATE shipyard_psychology_capture_runs SET completed_at=?,status='partial',error_code=? WHERE capture_id=?")
        .bind(new Date().toISOString(), code, capture.id).run();
    } catch { /* a failed D1 update is not proof of a completed capture */ }
    return { ...base, status: "storage_error", error_code: code, capture_id: capture.id, observations_inserted: inserted, duplicates, rejected, cap_skipped: capSkipped };
  }
}

async function shipyardPsychologyReadHistory(env, args = {}) {
  const limit = Number.isInteger(args.limit) ? args.limit : 20;
  const asOfMs = args.as_of ? shipyardPsychologyIsoMillis(args.as_of) : Date.now();
  const symbol = args.symbol ? args.symbol.toUpperCase() : null;
  if (asOfMs === null || asOfMs > Date.now() || limit < 1 || limit > 50) {
    return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "invalid", error: "invalid_history_query", observations: [] }, 400);
  }
  if (!env?.DB) return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "unavailable", error: "psychology_storage_not_configured", observations: [] }, 503);
  const asOf = new Date(asOfMs).toISOString();
  try {
    const rows = await env.DB.prepare(`SELECT ${SHIPYARD_PSYCHOLOGY_OBSERVATION_COLUMNS.join(",")} FROM shipyard_psychology_headline_tone_observations WHERE available_at<=? AND event_at<=? AND first_seen_at<=? AND (? IS NULL OR symbols_json LIKE ?) ORDER BY available_at DESC,updated_at DESC LIMIT ?`)
      .bind(asOf, asOf, asOf, symbol, symbol ? `%"${symbol}"%` : null, Math.min(500, limit * 10)).all();
    const latest = new Map();
    for (const row of rows.results || []) {
      if (latest.has(row.source_item_id)) continue;
      let symbols;
      try { symbols = JSON.parse(row.symbols_json || "[]"); } catch { continue; }
      if (!Array.isArray(symbols) || (symbol && !symbols.includes(symbol))) continue;
      const ageSeconds = (asOfMs - Date.parse(row.event_at)) / 1000;
      const freshness = ageSeconds < 0 ? "future_dated" : ageSeconds <= 90 ? "current" : ageSeconds <= SHIPYARD_PSYCHOLOGY_MAX_AGE_SECONDS ? "recent" : "stale";
      latest.set(row.source_item_id, {
        evidence_id: row.observation_id, item_id: row.source_item_id,
        revision_hash: row.revision_hash, supersedes_observation_id: row.supersedes_observation_id,
        revision_basis: row.revision_basis, source_population: row.source_population,
        source_independence: row.source_independence, source_family: row.source_family,
        provider: row.provider, publisher: row.publisher, symbols,
        event_at: row.event_at, event_time_basis: row.event_time_basis,
        updated_at: row.updated_at, first_seen_at: row.first_seen_at,
        provider_received_at: row.provider_received_at,
        provider_received_at_basis: row.provider_received_at_basis,
        locally_received_at: row.locally_received_at, extracted_at: row.extracted_at,
        available_at: row.available_at, max_age_seconds: row.max_age_seconds,
        freshness_status: freshness, age_seconds: ageSeconds,
        measures: {
          sentiment: { value: row.sentiment_value, units: "lexicon_score_v1", matched_tokens: row.matched_tokens, model: row.model_version },
          uncertainty: { value: row.uncertainty_value, units: "uncertainty_token_fraction", model: row.model_version },
        },
        retention_policy_status: row.source_purpose_policy_status,
        retention_policy_version: row.source_purpose_policy_version,
        source_terms_status: row.source_terms_status,
        account_terms_status: row.account_terms_status, raw_content_stored: false,
      });
    }
    const observations = [...latest.values()].sort((left, right) => Date.parse(right.available_at) - Date.parse(left.available_at)).slice(0, limit);
    const eligible = observations.filter((item) => ["current", "recent"].includes(item.freshness_status));
    const sentiments = eligible.map((item) => item.measures.sentiment.value).filter((value) => value !== null);
    const uncertainties = eligible.map((item) => item.measures.uncertainty.value).filter((value) => value !== null);
    return json({
      schema: SHIPYARD_PSYCHOLOGY_SCHEMA,
      status: sentiments.length ? "available_advisory" : eligible.length ? "no_sentiment_matches" : observations.length ? "stale_or_unknown" : "empty",
      as_of: asOf, computed_at: new Date().toISOString(), symbol,
      aggregate: {
        sentiment: { value: shipyardPsychologyMean(sentiments), units: "lexicon_score_v1", matched_article_count: sentiments.length },
        uncertainty: { value: shipyardPsychologyMean(uncertainties), units: "uncertainty_token_fraction", article_count: uncertainties.length },
        stale_count: observations.filter((item) => item.freshness_status === "stale").length,
        missingness: sentiments.length ? null : "no_fresh_lexicon_matches",
      },
      observations,
      limits: ["One Alpaca feed; no source-independence claim.", "Headline tone is not investor sentiment or private thought.", "Descriptive, unvalidated research only; no automatic strategy or order authority."],
      authority: { advisory_only: true, llm_may_use_as_context: true, automatic_strategy_change: false, order_submission_enabled: false },
    });
  } catch (error) {
    return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "unavailable", error: "psychology_storage_unavailable", error_code: shipyardPsychologySafeCode(error?.name, "storage_error"), observations: [] }, 503);
  }
}

function shipyardPsychologyArguments(args = {}, history = false) {
  const allowed = history ? new Set(["symbol", "limit", "as_of"]) : new Set(["symbol", "symbols", "limit"]);
  if (!args || typeof args !== "object" || Array.isArray(args) || Object.keys(args).some((key) => !allowed.has(key))) throw new Error("invalid_arguments");
  const symbols = args.symbol ? [args.symbol] : Array.isArray(args.symbols) ? args.symbols : [];
  if (symbols.length > 10 || symbols.some((value) => typeof value !== "string" || !/^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$/.test(value))
    || new Set(symbols.map((value) => value.toUpperCase())).size !== symbols.length) throw new Error("invalid_symbols");
  const limit = args.limit === undefined ? (history ? 20 : 50) : args.limit;
  if (!Number.isInteger(limit) || limit < 1 || limit > (history ? 50 : 50)) throw new Error("invalid_limit");
  const asOfMs = args.as_of === undefined ? null : shipyardPsychologyIsoMillis(args.as_of);
  if (history && args.as_of !== undefined && (asOfMs === null || asOfMs > Date.now())) throw new Error("invalid_as_of");
  return { symbols: symbols.map((value) => value.toUpperCase()), symbol: args.symbol ? args.symbol.toUpperCase() : null, limit, as_of: args.as_of };
}

async function shipyardPsychologyNewsResponse(request, env, symbols, limit) {
  const target = new URL("/api/research/news", request.url);
  if (symbols.length) target.searchParams.set("symbols", symbols.join(","));
  target.searchParams.set("limit", String(limit));
  return alpacaRoute(new Request(target, {
    headers: { "cf-connecting-ip": request.headers.get("cf-connecting-ip") || "mcp" },
    signal: request.signal,
  }), env);
}

async function shipyardPsychologyTool(request, env, name, rawArgs = {}) {
  if (name === "shipyard_psychology_history") {
    let args;
    try { args = shipyardPsychologyArguments(rawArgs, true); }
    catch (error) { return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "invalid", error: error.message }, 400); }
    return shipyardPsychologyReadHistory(env, args);
  }
  let args;
  try { args = shipyardPsychologyArguments(rawArgs, false); }
  catch (error) { return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "invalid", error: error.message }, 400); }
  const startedAt = new Date().toISOString();
  const upstream = await shipyardPsychologyNewsResponse(request, env, args.symbols, args.limit);
  if (!upstream) return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "unavailable", error: "existing_news_reader_unavailable", evidence: [] }, 503);
  let news;
  try { news = await upstream.json(); }
  catch { return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "unavailable", error: "existing_news_reader_invalid_response", evidence: [] }, 502); }
  const computedAt = new Date().toISOString();
  const tone = await shipyardPsychologyDerive(news, { firstSeenAt: startedAt, computedAt });
  if (name === "shipyard_psychology_headline_tone") {
    return json({ ...tone, collection: { mode: "on_demand_private_read", persistence_status: "not_requested", raw_content_persisted: false, public_projection: false } }, upstream.status);
  }
  if (name !== "shipyard_psychology_capture") return json({ schema: SHIPYARD_PSYCHOLOGY_SCHEMA, status: "invalid", error: "unknown_tool" }, 400);
  const captureId = crypto.randomUUID();
  const persistence = await shipyardPsychologyPersist(env, tone, {
    id: captureId, started_at: startedAt, symbols: args.symbols, limit: args.limit,
    source_status: news.status || "unknown",
    source_error: shipyardPsychologySafeCode(news.error, null),
    retrieved_at: news.retrieved_at || null, served_at: news.served_at || null,
    cache_hit: news.cache_hit === true,
  });
  return json({ ...tone, collection: { mode: "single_bounded_capture", persistence, raw_content_persisted: false, public_projection: false, no_schedule_created: true } }, upstream.status);
}
