import { createHash } from 'node:crypto';
import { MORGUE_SNAPSHOT_SOURCE_ID, SOURCE_REGISTRY, SOURCE_REGISTRY_VERSION } from './evidence-contract.mjs';

export const MORGUE_ADAPTER_VERSION = '1.1.0';
export const MORGUE_FEED_PATH = 'research/morgue-engine/output/morgue-feed.json';

const SECTION_KEYS = Object.freeze([
  'map', 'tape', 'scorecard', 'studies', 'squeeze', 'wall_validation',
  'flow', 'chain', 'lanes', 'board',
]);
const SESSION_DATE = /^\d{4}-\d{2}-\d{2}$/;
const OFFSET_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/;
const MORGUE_SOURCE = SOURCE_REGISTRY.find(source => source.sourceId === MORGUE_SNAPSHOT_SOURCE_ID);

if (!MORGUE_SOURCE || MORGUE_SOURCE.rightsStatus !== 'unknown' || MORGUE_SOURCE.ingestionPolicy !== 'metadata_only') {
  throw new Error('Morgue metadata adapter requires a matching metadata-only source registry entry.');
}

function validSessionDate(value) {
  if (typeof value !== 'string' || !SESSION_DATE.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function validOffsetTimestamp(value) {
  return typeof value === 'string' && OFFSET_TIMESTAMP.test(value) && Number.isFinite(Date.parse(value));
}

export function summarizeMorgueSnapshot(raw, ingestedAtUtc = new Date().toISOString()) {
  const bytes = Buffer.isBuffer(raw) ? raw : Buffer.from(String(raw), 'utf8');
  if (bytes.byteLength > 1_000_000) throw new Error('Morgue snapshot exceeds the 1 MiB adapter limit.');
  const feed = JSON.parse(bytes.toString('utf8'));
  if (!feed || typeof feed !== 'object' || Array.isArray(feed)) throw new Error('Morgue snapshot must be a JSON object.');
  if (!validOffsetTimestamp(feed.generated_at_utc)) throw new Error('Morgue snapshot has no timezone-qualified generated_at_utc.');
  if (!validSessionDate(feed.as_of_session)) throw new Error('Morgue snapshot has no valid as_of_session date.');
  if (!validOffsetTimestamp(ingestedAtUtc)) throw new Error('Adapter ingestion time must include a timezone offset.');

  const sections = Object.fromEntries(SECTION_KEYS.map(key => [key, Object.hasOwn(feed, key) && feed[key] !== null]));
  const missingSections = SECTION_KEYS.filter(key => !sections[key]);
  const snapshotSha256 = createHash('sha256').update(bytes).digest('hex');

  return {
    schema: 'silicon.morgue-snapshot-metadata.v1',
    adapterVersion: MORGUE_ADAPTER_VERSION,
    sourceRegistryVersion: SOURCE_REGISTRY_VERSION,
    engine: 'Morgue Engine',
    mode: 'read_only_local_metadata',
    source: {
      sourceId: MORGUE_SOURCE.sourceId,
      rightsStatus: MORGUE_SOURCE.rightsStatus,
      allowedPurposes: [...MORGUE_SOURCE.allowedPurposes],
      redistribution: MORGUE_SOURCE.redistribution,
    },
    snapshot: {
      generatedAtUtc: feed.generated_at_utc,
      asOfSession: feed.as_of_session,
      ingestedAtUtc,
      sha256: snapshotSha256,
      authenticityEstablished: false,
    },
    sections,
    missingSections,
    boundaries: {
      marketValuesIncluded: false,
      rightsStatus: 'unknown',
      availabilityEvidence: 'unknown',
      pointInTimeValidation: 'not_run',
      decisionEligible: false,
      performanceClaimEligible: false,
      orderSubmissionEnabled: false,
      reason: 'This adapter exposes snapshot metadata only. Source-level rights, availability, and point-in-time validation remain unresolved.',
    },
  };
}

export function summarizeMorgueReadiness(snapshot, {
  evaluatedAtUtc = new Date().toISOString(),
  artifactStatus = snapshot ? 'available' : 'missing',
  reason = null,
} = {}) {
  if (!validOffsetTimestamp(evaluatedAtUtc)) {
    throw new Error('Readiness evaluation time must include a timezone offset.');
  }
  if (!['available', 'missing', 'invalid'].includes(artifactStatus)) {
    throw new Error('Artifact status must be available, missing, or invalid.');
  }

  const generatedAtUtc = snapshot?.snapshot?.generatedAtUtc || null;
  const ageSeconds = generatedAtUtc
    ? Math.floor((Date.parse(evaluatedAtUtc) - Date.parse(generatedAtUtc)) / 1000)
    : null;
  const missingSections = snapshot?.missingSections || [];
  const state = artifactStatus === 'available'
    ? (missingSections.length ? 'partial' : 'available')
    : 'unavailable';

  return {
    schema: 'silicon.pipeline-readiness.v1',
    evaluatedAtUtc,
    state,
    artifactStatus,
    snapshot: snapshot ? {
      asOfSession: snapshot.snapshot.asOfSession,
      generatedAtUtc,
      ageSeconds,
      clockAppearsFutureDated: ageSeconds < 0,
      sha256: snapshot.snapshot.sha256,
      presentSectionCount: Object.values(snapshot.sections).filter(Boolean).length,
      expectedSectionCount: Object.keys(snapshot.sections).length,
      missingSections,
    } : null,
    freshness: {
      status: 'unknown',
      maximumAgeSeconds: null,
      reason: 'No exchange-session calendar or source-specific freshness budget is configured.',
    },
    gates: {
      rightsStatus: snapshot?.source?.rightsStatus || 'unknown',
      availabilityEvidence: snapshot?.boundaries?.availabilityEvidence || 'unknown',
      pointInTimeValidation: snapshot?.boundaries?.pointInTimeValidation || 'not_run',
      decisionEligible: false,
      performanceClaimEligible: false,
      orderSubmissionEnabled: false,
    },
    reason: reason || (snapshot
      ? 'Artifact integrity and section presence were checked; source rights, source freshness, and point-in-time eligibility were not established.'
      : 'The local Morgue snapshot could not be read and validated.'),
  };
}
