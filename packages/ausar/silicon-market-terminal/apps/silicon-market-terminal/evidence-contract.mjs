export const EVIDENCE_CONTRACT_VERSION = '1.0.0';
export const SOURCE_REGISTRY_VERSION = '1.1.0';
export const MORGUE_SNAPSHOT_SOURCE_ID = 'morgue.local-snapshot';

// This registry describes the prototype's actual sources. A configured credential is
// deliberately not treated as proof of data entitlement or redistribution rights.
export const SOURCE_REGISTRY = Object.freeze([
  {
    sourceId: 'silicon.synthetic-demo',
    name: 'Silicon synthetic demo fixtures',
    sourceClass: 'generated_fixture',
    rightsStatus: 'internal_fixture',
    ingestionPolicy: 'fixture_only',
    allowedPurposes: ['illustration', 'ui_exercise'],
    blockedPurposes: ['trading_decision', 'performance_claim', 'market_data_redistribution'],
    persistsRawData: false,
    redistribution: 'not_market_data',
    note: 'Generated examples; never market observations or evidence of strategy performance.',
  },
  {
    sourceId: 'user.local-csv',
    name: 'User-selected local CSV',
    sourceClass: 'user_supplied_file',
    rightsStatus: 'user_asserted_local_scope',
    ingestionPolicy: 'browser_memory_only',
    allowedPurposes: ['local_analysis', 'paper_research'],
    blockedPurposes: ['server_upload', 'third_party_redistribution'],
    persistsRawData: false,
    redistribution: 'not_applicable_to_local_processing',
    note: 'The app keeps imported rows in the active browser tab; this entry does not verify the file owner’s rights.',
  },
  {
    sourceId: 'user.manual-input',
    name: 'User-entered values',
    sourceClass: 'user_supplied_values',
    rightsStatus: 'user_asserted_local_scope',
    ingestionPolicy: 'browser_memory_only',
    allowedPurposes: ['local_analysis', 'paper_research'],
    blockedPurposes: ['server_upload', 'third_party_redistribution'],
    persistsRawData: false,
    redistribution: 'not_applicable_to_local_processing',
    note: 'Values are used by local calculations; source, freshness, and rights still require explicit evidence.',
  },
  {
    sourceId: 'unusual-whales.api',
    name: 'Unusual Whales API proxy',
    sourceClass: 'third_party_api',
    rightsStatus: 'entitlement_unverified',
    ingestionPolicy: 'disabled_until_entitlement_verified',
    allowedPurposes: [],
    blockedPurposes: ['terminal_ingestion', 'persistence', 'redistribution'],
    credentialPresenceProvesEntitlement: false,
    terminalIngestionEnabled: false,
    persistsRawData: false,
    redistribution: 'unknown',
    note: 'The optional route is a read-only diagnostic proxy. A configured API key does not establish feed entitlement or output rights.',
  },
  {
    sourceId: MORGUE_SNAPSHOT_SOURCE_ID,
    name: 'Local Morgue snapshot metadata',
    sourceClass: 'local_artifact_metadata',
    rightsStatus: 'unknown',
    ingestionPolicy: 'metadata_only',
    allowedPurposes: ['integrity_inspection'],
    blockedPurposes: ['trading_decision', 'performance_claim', 'market_data_redistribution'],
    terminalIngestionEnabled: false,
    persistsRawData: false,
    redistribution: 'unknown',
    note: 'Only snapshot dates, a byte hash, and section-presence flags are exposed; market values are excluded until source rights and point-in-time evidence are reviewed.',
  },
]);

const clockNames = ['eventAt', 'publishedAt', 'availableAt', 'ingestedAt', 'decisionAt'];
const evidenceStates = ['observed', 'delayed', 'stale', 'partial', 'no_data', 'known_zero', 'rejected', 'inferred'];
const timestampPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

export const OBSERVATION_SCHEMA = Object.freeze({
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  title: 'Silicon canonical observation',
  type: 'object',
  additionalProperties: false,
  required: ['observationId', 'entity', 'measure', 'clocks', 'state', 'stateReason', 'source', 'rights', 'coverage', 'revision'],
  properties: {
    observationId: { type: 'string', minLength: 1 },
    entity: {
      type: 'object', additionalProperties: false, required: ['kind', 'id'],
      properties: {
        kind: { enum: ['equity', 'option', 'future', 'crypto_asset', 'onchain_entity', 'index', 'issuer', 'other'] },
        id: { type: 'string', minLength: 1 },
        symbol: { type: ['string', 'null'] },
        venue: { type: ['string', 'null'] },
        currency: { type: ['string', 'null'] },
        contract: { type: ['object', 'null'] },
      },
    },
    measure: {
      type: 'object', additionalProperties: false, required: ['key', 'value', 'unit'],
      properties: {
        key: { type: 'string', minLength: 1 },
        value: { type: ['number', 'string', 'boolean', 'object', 'array', 'null'] },
        unit: { type: 'string', minLength: 1 },
        adjustment: { type: ['string', 'null'] },
      },
    },
    clocks: {
      type: 'object', additionalProperties: false,
      required: ['eventAt', 'publishedAt', 'availableAt', 'availabilityEvidence', 'availabilityEvidenceRef', 'ingestedAt', 'decisionAt', 'missingReasons'],
      properties: {
        eventAt: { type: ['string', 'null'], format: 'date-time' },
        publishedAt: { type: ['string', 'null'], format: 'date-time' },
        availableAt: { type: ['string', 'null'], format: 'date-time' },
        availabilityEvidence: { enum: ['verified', 'source_reported', 'unknown'] },
        availabilityEvidenceRef: { type: ['string', 'null'] },
        ingestedAt: { type: ['string', 'null'], format: 'date-time' },
        decisionAt: { type: ['string', 'null'], format: 'date-time' },
        missingReasons: { type: 'object', additionalProperties: { type: 'string', minLength: 1 } },
      },
    },
    state: { enum: evidenceStates },
    stateReason: { type: ['string', 'null'] },
    source: {
      type: 'object', additionalProperties: false, required: ['sourceId', 'sourceVersion'],
      properties: {
        sourceId: { type: 'string', minLength: 1 },
        sourceVersion: { type: 'string', minLength: 1 },
        uri: { type: ['string', 'null'] },
        artifactSha256: { type: ['string', 'null'], pattern: '^[a-f0-9]{64}$' },
        captureId: { type: ['string', 'null'] },
      },
    },
    rights: {
      type: 'object', additionalProperties: false, required: ['status', 'evidenceRef', 'allowedPurposes', 'redistribution'],
      properties: {
        status: { enum: ['internal_fixture', 'user_asserted_local_scope', 'approved', 'entitlement_unverified', 'unknown', 'prohibited'] },
        evidenceRef: { type: ['string', 'null'] },
        entitlementId: { type: ['string', 'null'] },
        allowedPurposes: { type: 'array', items: { type: 'string' }, uniqueItems: true },
        redistribution: { enum: ['approved', 'restricted', 'unknown', 'not_applicable_to_local_processing', 'not_market_data'] },
        retentionUntil: { type: ['string', 'null'], format: 'date-time' },
      },
    },
    coverage: {
      type: 'object', additionalProperties: false, required: ['status', 'observedCount', 'expectedCount', 'missingReasons'],
      properties: {
        status: { enum: ['complete', 'partial', 'unknown', 'not_applicable'] },
        observedCount: { type: ['integer', 'null'], minimum: 0 },
        expectedCount: { type: ['integer', 'null'], minimum: 0 },
        missingReasons: { type: 'array', items: { type: 'string' } },
      },
    },
    revision: {
      type: 'object', additionalProperties: false, required: ['number', 'supersedesObservationId'],
      properties: {
        number: { type: 'integer', minimum: 1 },
        supersedesObservationId: { type: ['string', 'null'] },
      },
    },
  },
});

export const FEATURE_SCHEMA = Object.freeze({
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  title: 'Silicon derived feature and lineage record',
  type: 'object',
  additionalProperties: false,
  required: ['featureId', 'value', 'unit', 'method', 'parentObservationIds', 'sourceFamilyIds', 'asOfTime', 'computedAt', 'evidenceStatus', 'coverageStatus'],
  properties: {
    featureId: { type: 'string', minLength: 1 },
    value: { type: ['number', 'string', 'boolean', 'object', 'array', 'null'] },
    unit: { type: 'string', minLength: 1 },
    method: {
      type: 'object', additionalProperties: false, required: ['methodId', 'version', 'methodRef', 'implementationSha256', 'parametersSha256'],
      properties: {
        methodId: { type: 'string', minLength: 1 },
        version: { type: 'string', minLength: 1 },
        methodRef: { type: 'string', minLength: 1 },
        implementationSha256: { type: 'string', pattern: '^[a-f0-9]{64}$' },
        parametersSha256: { type: 'string', pattern: '^[a-f0-9]{64}$' },
      },
    },
    parentObservationIds: { type: 'array', minItems: 1, uniqueItems: true, items: { type: 'string', minLength: 1 } },
    sourceFamilyIds: { type: 'array', minItems: 1, uniqueItems: true, items: { type: 'string', minLength: 1 } },
    asOfTime: { type: 'string', format: 'date-time' },
    computedAt: { type: 'string', format: 'date-time' },
    evidenceStatus: { enum: ['observed', 'published', 'reproduced', 'inferred', 'unknown'] },
    coverageStatus: { enum: ['complete', 'partial', 'unknown', 'not_applicable'] },
    resultSha256: { type: ['string', 'null'], pattern: '^[a-f0-9]{64}$' },
  },
});

export const EVIDENCE_CONTRACT = Object.freeze({
  contractVersion: EVIDENCE_CONTRACT_VERSION,
  sourceRegistryVersion: SOURCE_REGISTRY_VERSION,
  policy: 'fail-closed; preserve unknowns; no implicit zero or neutral imputation',
  availabilityEvidenceRegistry: Object.freeze({ version: '1.0.0', verifiedRefs: Object.freeze([]) }),
  sourceRegistry: SOURCE_REGISTRY,
  observationSchema: OBSERVATION_SCHEMA,
  featureSchema: FEATURE_SCHEMA,
});

async function cryptoProvider() {
  if (globalThis.crypto?.subtle) return globalThis.crypto;
  try {
    return (await import('node:crypto')).webcrypto;
  } catch {
    throw new Error('Web Crypto is required to create evidence hashes.');
  }
}

export async function sha256Hex(value) {
  const provider = await cryptoProvider();
  const bytes = value instanceof Uint8Array ? value : new TextEncoder().encode(String(value));
  const digest = await provider.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

export async function stableObservationId({ sourceId, sourceKey, revision = 1 } = {}) {
  if (typeof sourceId !== 'string' || !sourceId.trim() || typeof sourceKey !== 'string' || !sourceKey.trim() || !Number.isInteger(revision) || revision < 1) {
    throw new TypeError('sourceId, sourceKey, and a positive integer revision are required.');
  }
  const digest = await sha256Hex(`${sourceId}\0${sourceKey}\0${revision}`);
  return `obs_${digest}`;
}

function validTimestamp(value) {
  return typeof value === 'string' && timestampPattern.test(value) && Number.isFinite(Date.parse(value));
}

export function validateObservation(observation) {
  const issues = [];
  const issue = (path, message) => issues.push({ path, message });

  if (!observation || typeof observation !== 'object' || Array.isArray(observation)) {
    return { valid: false, issues: [{ path: '$', message: 'Observation must be an object.' }] };
  }
  for (const key of ['observationId', 'entity', 'measure', 'clocks', 'state', 'stateReason', 'source', 'rights', 'coverage', 'revision']) {
    if (!(key in observation)) issue(key, 'Required field is missing.');
  }
  if (typeof observation.observationId !== 'string' || !observation.observationId.trim()) issue('observationId', 'Must be a non-empty string.');
  if (!observation.entity || !['equity', 'option', 'future', 'crypto_asset', 'onchain_entity', 'index', 'issuer', 'other'].includes(observation.entity.kind)) issue('entity.kind', 'Must use a canonical entity kind.');
  if (!observation.entity || typeof observation.entity.id !== 'string' || !observation.entity.id.trim()) issue('entity.id', 'Must be a non-empty canonical entity identifier.');
  if (!observation.measure || typeof observation.measure.key !== 'string' || !observation.measure.key.trim()) issue('measure.key', 'Must be a non-empty measure key.');
  if (!observation.measure || typeof observation.measure.unit !== 'string' || !observation.measure.unit.trim()) issue('measure.unit', 'Unit is required; use an explicit unit token for dimensionless values.');
  if (!observation.measure || !Object.hasOwn(observation.measure, 'value')) issue('measure.value', 'A value field is required; represent unavailable values with null and a non-data state.');
  if (observation.measure && Object.hasOwn(observation.measure, 'value') && !['number', 'string', 'boolean', 'object'].includes(typeof observation.measure.value) && observation.measure.value !== null) issue('measure.value', 'Must be a JSON value or null.');
  if (typeof observation.measure?.value === 'number' && !Number.isFinite(observation.measure.value)) issue('measure.value', 'Numeric values must be finite.');
  if (!evidenceStates.includes(observation.state)) issue('state', `Must be one of: ${evidenceStates.join(', ')}.`);
  if (observation.state === 'observed' && observation.measure?.value === null) issue('measure.value', 'observed requires a non-null value; use no_data when unavailable.');
  if (observation.state === 'known_zero' && observation.measure?.value !== 0) issue('measure.value', 'known_zero requires a literal numeric zero.');
  if (['no_data', 'rejected'].includes(observation.state) && observation.measure?.value !== null) issue('measure.value', `${observation.state} requires null, never a fabricated neutral or zero.`);
  if (['no_data', 'rejected', 'delayed', 'stale', 'partial', 'inferred'].includes(observation.state) && (typeof observation.stateReason !== 'string' || !observation.stateReason.trim())) issue('stateReason', `${observation.state} requires an explicit reason.`);
  if (['observed', 'known_zero'].includes(observation.state) && observation.stateReason !== null && typeof observation.stateReason !== 'string') issue('stateReason', 'Must be a string or null.');
  if (!Number.isInteger(observation.revision?.number) || observation.revision.number < 1) issue('revision.number', 'Must be a positive integer.');

  const clocks = observation.clocks;
  if (!clocks || typeof clocks !== 'object') {
    issue('clocks', 'Clock object is required.');
  } else {
    if (!clocks.missingReasons || typeof clocks.missingReasons !== 'object' || Array.isArray(clocks.missingReasons)) issue('clocks.missingReasons', 'An object is required to explain unavailable or inapplicable timestamps.');
    for (const name of clockNames) {
      if (!(name in clocks)) {
        issue(`clocks.${name}`, 'Clock field is required; use null with a missing reason when unknown or not applicable.');
      } else if (clocks[name] !== null && !validTimestamp(clocks[name])) {
        issue(`clocks.${name}`, 'Must be an RFC 3339 timestamp with timezone or null.');
      } else if (clocks[name] === null && (typeof clocks.missingReasons?.[name] !== 'string' || !clocks.missingReasons[name].trim())) {
        issue(`clocks.missingReasons.${name}`, 'A missing reason is required for every null clock.');
      }
    }
    if (!['verified', 'source_reported', 'unknown'].includes(clocks.availabilityEvidence)) issue('clocks.availabilityEvidence', 'Must distinguish verified availability from source-reported or unknown timing.');
    if (['verified', 'source_reported'].includes(clocks.availabilityEvidence) && (typeof clocks.availabilityEvidenceRef !== 'string' || !clocks.availabilityEvidenceRef.trim())) issue('clocks.availabilityEvidenceRef', 'Verified or source-reported availability requires a traceable evidence reference.');
    if (clocks.availabilityEvidence === 'unknown' && clocks.availabilityEvidenceRef !== null) issue('clocks.availabilityEvidenceRef', 'Use null when availability evidence is unknown.');
  }

  if (!observation.source || typeof observation.source.sourceId !== 'string' || !observation.source.sourceId.trim()) issue('source.sourceId', 'Must reference a registry source.');
  if (!observation.source || typeof observation.source.sourceVersion !== 'string' || !observation.source.sourceVersion.trim()) issue('source.sourceVersion', 'Source version is required; use an explicit unknown marker when unavailable.');
  if (!observation.rights || !['internal_fixture', 'user_asserted_local_scope', 'approved', 'entitlement_unverified', 'unknown', 'prohibited'].includes(observation.rights.status)) issue('rights.status', 'A known rights state is required.');
  if (observation.rights?.status === 'approved' && (typeof observation.rights.evidenceRef !== 'string' || !observation.rights.evidenceRef.trim())) issue('rights.evidenceRef', 'Approved rights require a traceable license or entitlement evidence reference.');
  if (observation.rights?.status !== 'approved' && observation.rights?.evidenceRef !== null && typeof observation.rights?.evidenceRef !== 'string') issue('rights.evidenceRef', 'Must be a string reference or null.');
  if (!observation.rights || !Array.isArray(observation.rights.allowedPurposes)) issue('rights.allowedPurposes', 'Allowed purposes must be an explicit array, including an empty array when none are approved.');
  if (observation.rights?.allowedPurposes?.some(value => typeof value !== 'string' || !value.trim())) issue('rights.allowedPurposes', 'Each allowed purpose must be a non-empty string.');
  if (observation.rights && !['approved', 'restricted', 'unknown', 'not_applicable_to_local_processing', 'not_market_data'].includes(observation.rights.redistribution)) issue('rights.redistribution', 'Redistribution status must be explicit.');
  if (!observation.coverage || !['complete', 'partial', 'unknown', 'not_applicable'].includes(observation.coverage.status)) issue('coverage.status', 'Coverage state must be explicit.');
  if (observation.coverage && !Array.isArray(observation.coverage.missingReasons)) issue('coverage.missingReasons', 'An array is required; use an empty array only when no coverage gaps are known.');
  if (observation.coverage?.observedCount !== null && observation.coverage?.observedCount !== undefined && (!Number.isInteger(observation.coverage.observedCount) || observation.coverage.observedCount < 0)) issue('coverage.observedCount', 'Must be a non-negative integer or null.');
  if (observation.coverage?.expectedCount !== null && observation.coverage?.expectedCount !== undefined && (!Number.isInteger(observation.coverage.expectedCount) || observation.coverage.expectedCount < 0)) issue('coverage.expectedCount', 'Must be a non-negative integer or null.');
  if (observation.coverage?.status === 'complete' && Number.isInteger(observation.coverage.expectedCount) && Number.isInteger(observation.coverage.observedCount) && observation.coverage.expectedCount !== observation.coverage.observedCount) issue('coverage', 'Complete coverage requires observedCount to equal expectedCount.');
  if (['partial', 'unknown'].includes(observation.coverage?.status) && observation.coverage.missingReasons?.length === 0) issue('coverage.missingReasons', `${observation.coverage.status} coverage requires at least one reason.`);

  return { valid: issues.length === 0, issues };
}

export function assessDecisionEligibility(observation, {
  purpose = 'paper_research',
  decisionAt = observation?.clocks?.decisionAt,
  verifiedAvailabilityEvidenceRefs = EVIDENCE_CONTRACT.availabilityEvidenceRegistry.verifiedRefs,
} = {}) {
  const validation = validateObservation(observation);
  const blockers = validation.issues.map(({ path, message }) => `${path}: ${message}`);
  const registeredSource = SOURCE_REGISTRY.find(source => source.sourceId === observation?.source?.sourceId);

  if (!registeredSource) blockers.push('source.sourceId: source is absent from the reviewed local registry.');
  if (registeredSource && registeredSource.ingestionPolicy === 'disabled_until_entitlement_verified') blockers.push('source: provider entitlement has not been verified; ingestion is disabled.');
  if (registeredSource && registeredSource.ingestionPolicy === 'fixture_only') blockers.push('source: synthetic fixtures are for illustration and UI exercise only.');
  if (registeredSource && !registeredSource.allowedPurposes.includes(purpose)) blockers.push(`source: registry does not permit purpose "${purpose}".`);
  if (registeredSource && observation?.rights?.status !== registeredSource.rightsStatus) blockers.push('rights.status: observation does not match the reviewed source registry.');
  if (registeredSource && !observation?.rights?.allowedPurposes?.includes(purpose)) blockers.push(`rights: observation does not declare purpose "${purpose}".`);
  if (registeredSource && observation?.rights?.allowedPurposes?.some(value => !registeredSource.allowedPurposes.includes(value))) blockers.push('rights: observation claims a purpose not present in the reviewed source registry.');
  if (!validTimestamp(decisionAt)) blockers.push('clocks.decisionAt: a timezone-qualified decision timestamp is required.');
  if (observation?.clocks?.availabilityEvidence !== 'verified') blockers.push('clocks.availabilityEvidence: point-in-time availability is not verified.');
  if (!validTimestamp(observation?.clocks?.availableAt)) blockers.push('clocks.availableAt: point-in-time availability is missing.');
  if (!verifiedAvailabilityEvidenceRefs.includes(observation?.clocks?.availabilityEvidenceRef)) blockers.push('clocks.availabilityEvidenceRef: reference is not in the reviewed availability-evidence registry.');
  if (validTimestamp(decisionAt) && validTimestamp(observation?.clocks?.availableAt) && Date.parse(observation.clocks.availableAt) > Date.parse(decisionAt)) blockers.push('clocks.availableAt: observation was not available by the decision time.');
  if (validTimestamp(decisionAt) && validTimestamp(observation?.clocks?.ingestedAt) && Date.parse(observation.clocks.ingestedAt) > Date.parse(decisionAt)) blockers.push('clocks.ingestedAt: observation was ingested after the decision time.');
  if (!['observed', 'known_zero'].includes(observation?.state)) blockers.push(`state: ${observation?.state || 'unknown'} is not decision-eligible.`);
  if (observation?.coverage?.status !== 'complete' && observation?.coverage?.status !== 'not_applicable') blockers.push(`coverage: ${observation?.coverage?.status || 'unknown'} coverage is not decision-eligible.`);
  if (observation?.rights?.status === 'prohibited' || observation?.rights?.status === 'unknown' || observation?.rights?.status === 'entitlement_unverified') blockers.push('rights: source use is not cleared for this decision purpose.');

  return { eligible: blockers.length === 0, purpose, blockers: [...new Set(blockers)] };
}

export function validateFeatureRecord(feature) {
  const issues = [];
  const issue = (path, message) => issues.push({ path, message });
  if (!feature || typeof feature !== 'object' || Array.isArray(feature)) {
    return { valid: false, issues: [{ path: '$', message: 'Feature record must be an object.' }] };
  }
  for (const key of ['featureId', 'value', 'unit', 'method', 'parentObservationIds', 'sourceFamilyIds', 'asOfTime', 'computedAt', 'evidenceStatus', 'coverageStatus']) {
    if (!Object.hasOwn(feature, key)) issue(key, 'Required field is missing.');
  }
  if (typeof feature.featureId !== 'string' || !feature.featureId.trim()) issue('featureId', 'Must be a non-empty stable identifier.');
  if (typeof feature.unit !== 'string' || !feature.unit.trim()) issue('unit', 'Unit is required.');
  if (!feature.method || typeof feature.method.methodId !== 'string' || !feature.method.methodId.trim()) issue('method.methodId', 'A versioned method identifier is required.');
  if (!feature.method || typeof feature.method.version !== 'string' || !feature.method.version.trim()) issue('method.version', 'Method version is required.');
  if (typeof feature.method?.methodRef !== 'string' || !feature.method.methodRef.trim()) issue('method.methodRef', 'A replayable code or method reference is required.');
  if (!/^[a-f0-9]{64}$/.test(feature.method?.implementationSha256 || '')) issue('method.implementationSha256', 'A SHA-256 hash of the method implementation is required.');
  if (!/^[a-f0-9]{64}$/.test(feature.method?.parametersSha256 || '')) issue('method.parametersSha256', 'A SHA-256 hash of the canonical parameter set is required.');
  if (!Array.isArray(feature.parentObservationIds) || feature.parentObservationIds.length === 0 || new Set(feature.parentObservationIds).size !== feature.parentObservationIds.length) issue('parentObservationIds', 'At least one unique parent observation ID is required.');
  if (!Array.isArray(feature.sourceFamilyIds) || feature.sourceFamilyIds.length === 0 || new Set(feature.sourceFamilyIds).size !== feature.sourceFamilyIds.length) issue('sourceFamilyIds', 'At least one unique source family ID is required; correlated feeds should share a family ID.');
  if (!validTimestamp(feature.asOfTime)) issue('asOfTime', 'Must be a timezone-qualified timestamp.');
  if (!validTimestamp(feature.computedAt)) issue('computedAt', 'Must be a timezone-qualified timestamp.');
  if (typeof feature.value === 'number' && !Number.isFinite(feature.value)) issue('value', 'Numeric values must be finite.');
  if (validTimestamp(feature.asOfTime) && validTimestamp(feature.computedAt) && Date.parse(feature.computedAt) < Date.parse(feature.asOfTime)) issue('computedAt', 'Cannot precede the as-of time.');
  if (!['observed', 'published', 'reproduced', 'inferred', 'unknown'].includes(feature.evidenceStatus)) issue('evidenceStatus', 'Evidence status must remain explicit.');
  if (!['complete', 'partial', 'unknown', 'not_applicable'].includes(feature.coverageStatus)) issue('coverageStatus', 'Coverage status must remain explicit.');
  if (feature.resultSha256 != null && !/^[a-f0-9]{64}$/.test(feature.resultSha256)) issue('resultSha256', 'Must be a lowercase SHA-256 hash or null.');
  return { valid: issues.length === 0, issues };
}

export function assessFeatureLineage(feature, parentObservations, {
  purpose = 'paper_research',
  verifiedAvailabilityEvidenceRefs = EVIDENCE_CONTRACT.availabilityEvidenceRegistry.verifiedRefs,
} = {}) {
  const validation = validateFeatureRecord(feature);
  const blockers = validation.issues.map(({ path, message }) => `${path}: ${message}`);
  const parents = Array.isArray(parentObservations) ? parentObservations : [];
  const parentsById = new Map(parents.map(observation => [observation?.observationId, observation]));

  for (const id of feature?.parentObservationIds || []) {
    const parent = parentsById.get(id);
    if (!parent) {
      blockers.push(`parentObservationIds: observation "${id}" was not supplied for replay.`);
      continue;
    }
    const eligibility = assessDecisionEligibility(parent, { purpose, decisionAt: feature.asOfTime, verifiedAvailabilityEvidenceRefs });
    if (!eligibility.eligible) blockers.push(`parent ${id}: ${eligibility.blockers.join(' ')}`);
  }
  return { eligible: blockers.length === 0, purpose, blockers: [...new Set(blockers)] };
}
