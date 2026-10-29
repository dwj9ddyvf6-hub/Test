// Read-only Morgue snapshot adapter. Returns provenance and section presence,
// never vendor values, signals, or order instructions.
const MORGUE_SNAPSHOT_METADATA = __MORGUE_SNAPSHOT_METADATA__;
const MORGUE_ADAPTER_VERSION = "1.2.0";

async function morgueRoute(request) {
  if (new URL(request.url).pathname !== "/api/research/morgue/readiness") return null;
  if (request.method !== "GET" && request.method !== "HEAD") return json({ error: "read_only" }, 405);
  const source = MORGUE_SNAPSHOT_METADATA;
  const generatedMs = Date.parse(source.generated_at_utc);
  const now = Date.now();
  const ageSeconds = Number.isFinite(generatedMs) ? Math.floor((now - generatedMs) / 1000) : null;
  const missingSections = Array.isArray(source.missing_sections) ? source.missing_sections : [];
  return json({
    schema: "SILICON_MORGUE_READINESS_V1",
    status: missingSections.length ? "partial" : "available",
    adapter_version: MORGUE_ADAPTER_VERSION,
    source_registry_version: source.source_registry_version,
    source_url: source.source_url,
    source_commit: source.source_commit,
    source_id: source.source_id,
    rights_status: source.rights_status,
    ingestion_policy: source.ingestion_policy,
    allowed_purposes: source.allowed_purposes,
    blocked_purposes: source.blocked_purposes,
    redistribution: source.redistribution,
    snapshot: {
      generated_at_utc: source.generated_at_utc,
      as_of_session: source.as_of_session,
      age_seconds: ageSeconds,
      clock_appears_future_dated: ageSeconds !== null && ageSeconds < 0,
      sha256: source.sha256,
      authenticity_established: false,
      present_section_count: Object.values(source.sections).filter(Boolean).length,
      expected_section_count: Object.keys(source.sections).length,
      sections: source.sections,
      missing_sections: missingSections,
    },
    freshness: { status: "unknown", maximum_age_seconds: null, reason: "No exchange-session calendar or source-specific freshness budget is configured." },
    gates: { values_returned: false, point_in_time_validation: "not_run", decision_eligible: false, performance_claim_eligible: false, order_submission_enabled: false },
    reason: "A commit-pinned metadata manifest was built from the source artifact. Feed values are excluded; freshness, source rights, and point-in-time eligibility remain unverified.",
    received_at: new Date(now).toISOString(),
  });
}
