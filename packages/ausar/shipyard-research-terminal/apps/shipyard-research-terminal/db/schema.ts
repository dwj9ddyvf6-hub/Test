import { index, integer, primaryKey, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  email: text("email").notNull().unique(),
  displayName: text("display_name").notNull(),
  bio: text("bio").notNull().default(""),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
});

export const apps = sqliteTable("apps", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  ownerId: integer("owner_id").notNull().references(() => users.id),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  tagline: text("tagline").notNull(),
  description: text("description").notNull(),
  websiteUrl: text("website_url").notNull(),
  category: text("category").notNull(),
  status: text("status").notNull().default("launched"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
});

export const votes = sqliteTable("votes", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  appId: integer("app_id").notNull().references(() => apps.id, { onDelete: "cascade" }),
  userId: integer("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
}, (table) => [uniqueIndex("votes_app_user_idx").on(table.appId, table.userId)]);

export const reviews = sqliteTable("reviews", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  appId: integer("app_id").notNull().references(() => apps.id, { onDelete: "cascade" }),
  userId: integer("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  rating: integer("rating").notNull(),
  body: text("body").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
}, (table) => [uniqueIndex("reviews_app_user_idx").on(table.appId, table.userId)]);

// Observatory tables are append-only research storage. The hosted browser reads
// precomputed read_models; it never joins raw history or reaches production.
export const observatoryIngestRuns = sqliteTable("observatory_ingest_runs", {
  id: text("id").primaryKey(),
  sourceType: text("source_type").notNull(),
  provider: text("provider").notNull(),
  snapshotSha256: text("snapshot_sha256").notNull().unique(),
  status: text("status").notNull(),
  startedAt: text("started_at").notNull(),
  completedAt: text("completed_at"),
  inputWatermarkAt: text("input_watermark_at"),
  recordsAccepted: integer("records_accepted").notNull().default(0),
  recordsRejected: integer("records_rejected").notNull().default(0),
  manifestJson: text("manifest_json").notNull(),
  qualityJson: text("quality_json").notNull().default("{}"),
  errorCode: text("error_code"),
}, (table) => [
  index("obs_ingest_status_started_idx").on(table.status, table.startedAt),
]);

export const observatorySourceRecords = sqliteTable("observatory_source_records", {
  recordId: text("record_id").primaryKey(),
  ingestRunId: text("ingest_run_id").notNull().references(() => observatoryIngestRuns.id),
  recordType: text("record_type").notNull(),
  sourceKey: text("source_key").notNull(),
  eventKey: text("event_key"),
  symbol: text("symbol"),
  provider: text("provider").notNull(),
  barAt: text("bar_at"),
  availableAt: text("available_at").notNull(),
  observedAt: text("observed_at"),
  inputHash: text("input_hash").notNull(),
  payloadJson: text("payload_json").notNull(),
  qualityJson: text("quality_json").notNull().default("{}"),
  createdAt: text("created_at").notNull(),
}, (table) => [
  uniqueIndex("obs_source_record_dedupe_idx").on(table.recordType, table.sourceKey, table.inputHash),
  index("obs_source_event_idx").on(table.eventKey),
  index("obs_source_type_available_idx").on(table.recordType, table.availableAt),
]);

export const observatoryMarketBars = sqliteTable("observatory_market_bars", {
  provider: text("provider").notNull(),
  symbol: text("symbol").notNull(),
  timeframe: text("timeframe").notNull(),
  barEndAt: text("bar_end_at").notNull(),
  barStartAt: text("bar_start_at").notNull(),
  availableAt: text("available_at").notNull(),
  sessionDate: text("session_date").notNull(),
  open: text("open").notNull(),
  high: text("high").notNull(),
  low: text("low").notNull(),
  close: text("close").notNull(),
  volume: text("volume"),
  adjustmentMethod: text("adjustment_method").notNull(),
  isRth: integer("is_rth").notNull(),
  inputHash: text("input_hash").notNull(),
  qualityJson: text("quality_json").notNull().default("{}"),
  ingestRunId: text("ingest_run_id").notNull().references(() => observatoryIngestRuns.id),
}, (table) => [
  primaryKey({ columns: [table.provider, table.symbol, table.timeframe, table.barEndAt] }),
  index("obs_bars_symbol_time_idx").on(table.symbol, table.timeframe, table.barEndAt),
]);

export const observatoryObservations = sqliteTable("observatory_observations", {
  observationId: text("observation_id").primaryKey(),
  logicalKey: text("logical_key").notNull(),
  observationType: text("observation_type").notNull(),
  revision: integer("revision").notNull().default(1),
  supersedesObservationId: text("supersedes_observation_id"),
  createdAt: text("created_at").notNull(),
  computedAt: text("computed_at").notNull(),
  effectiveAt: text("effective_at").notNull(),
  inputWatermarkAt: text("input_watermark_at").notNull(),
  expiresAt: text("expires_at"),
  formulaVersion: text("formula_version").notNull(),
  parameterHash: text("parameter_hash").notNull(),
  inputHash: text("input_hash").notNull(),
  codeCommit: text("code_commit").notNull(),
  provider: text("provider").notNull(),
  eventKey: text("event_key"),
  barAt: text("bar_at"),
  rosterVersion: text("roster_version"),
  rosterHash: text("roster_hash"),
  symbol: text("symbol"),
  timeframe: text("timeframe"),
  pairId: text("pair_id"),
  studyId: text("study_id"),
  direction: text("direction"),
  status: text("status"),
  summaryJson: text("summary_json").notNull().default("{}"),
  payloadJson: text("payload_json").notNull(),
  qualityJson: text("quality_json").notNull().default("{}"),
  ingestRunId: text("ingest_run_id").references(() => observatoryIngestRuns.id),
}, (table) => [
  uniqueIndex("obs_logical_revision_idx").on(table.logicalKey, table.revision),
  index("obs_type_effective_idx").on(table.observationType, table.effectiveAt),
  index("obs_symbol_type_effective_idx").on(table.symbol, table.observationType, table.effectiveAt),
  index("obs_event_key_idx").on(table.eventKey),
  index("obs_pair_type_effective_idx").on(table.pairId, table.observationType, table.effectiveAt),
  index("obs_study_idx").on(table.studyId),
]);

export const observatoryObservationSteps = sqliteTable("observatory_observation_steps", {
  observationId: text("observation_id").notNull().references(() => observatoryObservations.observationId),
  stepKind: text("step_kind").notNull(),
  sequence: integer("sequence").notNull(),
  name: text("name").notNull(),
  startedAt: text("started_at"),
  endedAt: text("ended_at"),
  effectiveAt: text("effective_at"),
  durationMs: integer("duration_ms"),
  status: text("status"),
  valueText: text("value_text"),
  payloadJson: text("payload_json").notNull().default("{}"),
}, (table) => [
  primaryKey({ columns: [table.observationId, table.stepKind, table.sequence] }),
]);

export const observatoryRelationshipRegistry = sqliteTable("observatory_relationship_registry", {
  relationshipId: text("relationship_id").primaryKey(),
  legA: text("leg_a").notNull(),
  legB: text("leg_b").notNull(),
  timeframe: text("timeframe").notNull(),
  provider: text("provider").notNull(),
  formulaVersion: text("formula_version").notNull(),
  parameterHash: text("parameter_hash").notNull(),
  configJson: text("config_json").notNull(),
  effectiveAt: text("effective_at").notNull(),
  retiredAt: text("retired_at"),
  active: integer("active").notNull().default(1),
  updatedAt: text("updated_at").notNull(),
}, (table) => [
  index("obs_relationship_active_idx").on(table.active, table.relationshipId),
]);

export const observatoryReadModels = sqliteTable("observatory_read_models", {
  viewKey: text("view_key").primaryKey(),
  schemaVersion: text("schema_version").notNull(),
  generatedAt: text("generated_at").notNull(),
  inputWatermarkAt: text("input_watermark_at").notNull(),
  freshnessStatus: text("freshness_status").notNull(),
  sourceMode: text("source_mode").notNull(),
  etag: text("etag").notNull(),
  recordCount: integer("record_count").notNull().default(0),
  bodyJson: text("body_json").notNull(),
  qualityJson: text("quality_json").notNull().default("{}"),
}, (table) => [
  index("obs_read_model_generated_idx").on(table.generatedAt),
]);

export const apertureIngestNonces = sqliteTable("aperture_ingest_nonces", {
  nonce: text("nonce").primaryKey(),
  keyId: text("key_id").notNull(),
  receivedAt: text("received_at").notNull(),
  expiresAt: text("expires_at").notNull(),
}, (table) => [
  index("aperture_nonce_expires_idx").on(table.expiresAt),
]);

export const apertureAssetRegistry = sqliteTable("aperture_asset_registry", {
  symbol: text("symbol").primaryKey(),
  providerSymbol: text("provider_symbol"),
  assetClass: text("asset_class").notNull(),
  exchange: text("exchange"),
  active: integer("active").notNull().default(0),
  providerEligible: integer("provider_eligible").notNull().default(0),
  statusReason: text("status_reason"),
  validatedAt: text("validated_at").notNull(),
}, (table) => [
  index("aperture_asset_eligible_idx").on(table.providerEligible, table.active),
]);

export const apertureScanHistory = sqliteTable("aperture_scan_history", {
  scanId: text("scan_id").primaryKey(),
  barEndAt: text("bar_end_at").notNull(),
  generatedAt: text("generated_at").notNull(),
  provider: text("provider").notNull(),
  freshness: text("freshness").notNull(),
  universeCovered: integer("universe_covered").notNull(),
  decisionCount: integer("decision_count").notNull(),
  bodyJson: text("body_json").notNull(),
  createdAt: text("created_at").notNull(),
}, (table) => [
  index("aperture_scan_bar_idx").on(table.barEndAt),
]);

export const tensorAuditRuns = sqliteTable("tensor_audit_runs", {
  runId: text("run_id").primaryKey(),
  dateKey: text("date_key").notNull(),
  generatedAt: text("generated_at").notNull(),
  universeHash: text("universe_hash").notNull(),
  universeCount: integer("universe_count").notNull(),
  chartMode: text("chart_mode").notNull(),
  eventCount: integer("event_count").notNull().default(0),
  cyanCount: integer("cyan_count").notNull().default(0),
  greenCount: integer("green_count").notNull().default(0),
  goldCount: integer("gold_count").notNull().default(0),
  manifestJson: text("manifest_json").notNull(),
  createdAt: text("created_at").notNull(),
}, (table) => [
  index("tensor_audit_runs_generated_idx").on(table.generatedAt),
  index("tensor_audit_runs_date_idx").on(table.dateKey),
]);

export const tensorAuditEvents = sqliteTable("tensor_audit_events", {
  eventKey: text("event_key").primaryKey(),
  runId: text("run_id").notNull().references(() => tensorAuditRuns.runId, { onDelete: "cascade" }),
  eventDate: text("event_date").notNull(),
  symbol: text("symbol").notNull(),
  interval: text("interval").notNull(),
  eventTime: integer("event_time").notNull(),
  cohort: text("cohort").notNull(),
  cyan: integer("cyan").notNull().default(0),
  green: integer("green").notNull().default(0),
  gold: integer("gold").notNull().default(0),
  tier: text("tier").notNull(),
  significant: integer("significant").notNull().default(0),
  tierMovePct: text("tier_move_pct"),
  chartFile: text("chart_file"),
  pngFile: text("png_file"),
  htmlFile: text("html_file"),
  payloadJson: text("payload_json").notNull(),
  createdAt: text("created_at").notNull(),
}, (table) => [
  index("tensor_audit_events_run_time_idx").on(table.runId, table.eventTime),
  index("tensor_audit_events_date_cohort_idx").on(table.eventDate, table.cohort),
  index("tensor_audit_events_symbol_time_idx").on(table.symbol, table.eventTime),
]);

// One public, paper-only observation. The Worker writes id=1 atomically and
// derives the public projection again before it reaches this table.
export const ausarTerminalSnapshots = sqliteTable("ausar_terminal_snapshots", {
  id: integer("id").primaryKey(),
  observedAtUtc: text("observed_at_utc").notNull(),
  receivedAtUtc: text("received_at_utc").notNull(),
  payloadSha256: text("payload_sha256").notNull(),
  payloadJson: text("payload_json").notNull(),
});

export const terminalPublicHistory = sqliteTable("terminal_public_history", {
  slot: text("slot").primaryKey(),
  observedAt: text("observed_at").notNull(),
  payloadJson: text("payload_json").notNull(),
});

// Private device capabilities and optional account ownership; never exported.
export const terminalPushSubscriptions = sqliteTable("terminal_push_subscriptions", {
  id: text("id").primaryKey(),
  userId: text("user_id").notNull(),
  deviceKeyHash: text("device_key_hash").unique(),
  endpointHash: text("endpoint_hash").notNull().unique(),
  subscriptionJson: text("subscription_json").notNull(),
  label: text("label").notNull(),
  createdAt: integer("created_at").notNull(),
  activatedAt: integer("activated_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
  expiresAt: integer("expires_at"),
  vapidKeyId: text("vapid_key_id").notNull(),
  disabledAt: integer("disabled_at"),
  lastSentAt: integer("last_sent_at"),
  lastTestAt: integer("last_test_at"),
}, table => [index("terminal_push_user_active_idx").on(table.userId, table.disabledAt)]);

// Short-lived anonymous registration counters; no raw network addresses.
export const terminalPushRateLimits = sqliteTable("terminal_push_rate_limits", {
  id: text("id").primaryKey(),
  attempts: integer("attempts").notNull(),
  expiresAt: integer("expires_at").notNull(),
}, table => [index("terminal_push_rate_expiry_idx").on(table.expiresAt)]);

export const terminalPushDeliveries = sqliteTable("terminal_push_deliveries", {
  subscriptionId: text("subscription_id").notNull(),
  eventId: text("event_id").notNull(),
  status: text("status").notNull(),
  attempts: integer("attempts").notNull(),
  attemptedAt: integer("attempted_at").notNull(),
  signalAt: integer("signal_at").notNull(),
  providerStatus: integer("provider_status"),
}, table => [primaryKey({columns:[table.subscriptionId, table.eventId]}), index("terminal_push_delivery_age_idx").on(table.attemptedAt)]);

// Immutable sanitized public briefs let notification taps resolve the original event.
export const terminalSetupEvents = sqliteTable("terminal_setup_events", {
  id: text("id").primaryKey(),
  createdAt: integer("created_at").notNull(),
  expiresAt: integer("expires_at").notNull(),
  payloadJson: text("payload_json").notNull(),
}, table => [index("terminal_setup_event_expiry_idx").on(table.expiresAt), index("terminal_setup_event_created_idx").on(table.createdAt, table.id)]);
