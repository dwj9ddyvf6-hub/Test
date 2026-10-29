import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const candidatePath = 'research/rea-teardowns/synthesis/CANDIDATE-REQUIREMENT-REGISTER-2026-10-27.csv';
const scopedPath = 'research/rea-teardowns/synthesis/SCOPED-FAMILY-REQUIREMENTS-2026-10-27.csv';
const familySemanticPath = 'research/rea-teardowns/synthesis/OPTIONSTRAT-PUBLIC-SEMANTIC-REQUIREMENTS-2026-10-27.json';
const traceabilityPath = 'research/rea-teardowns/synthesis/FAMILY-REQUIREMENT-TRACEABILITY-2026-10-27.csv';
const outputPath = 'research/rea-teardowns/synthesis/UNIFIED-REQUIREMENT-INDEX-2026-10-27.csv';
const headers = [
  'requirement_id', 'record_kind', 'family_slug', 'requirement_scope', 'user_job', 'inputs',
  'outputs', 'rules_settings_and_states', 'states_and_failure_modes', 'evidence_class_or_grade',
  'source_references', 'implementation_mapping', 'mapping_status', 'reconstruction_choices',
  'known_gaps_and_nonclaims', 'rights_boundary', 'fixture_or_validation_reference',
  'validation_status', 'full_vendor_recreation',
];

const [candidateRows, scopedRows, familySemanticRegister, traceRows] = await Promise.all([
  readFile(path.join(root, candidatePath), 'utf8').then(parseCsv),
  readFile(path.join(root, scopedPath), 'utf8').then(parseCsv),
  readFile(path.join(root, familySemanticPath), 'utf8').then(JSON.parse),
  readFile(path.join(root, traceabilityPath), 'utf8').then(parseCsv),
]);
assert.equal(candidateRows.length, 9, `expected 9 bounded candidate records, found ${candidateRows.length}`);
assert.equal(scopedRows.length, 14, `expected 14 adopted, source-anchored scoped evidence records, found ${scopedRows.length}`);
assert.equal(familySemanticRegister.schemaVersion, '1.0.0', 'OptionStrat semantic register version changed; review before regenerating');
assert.equal(familySemanticRegister.familySlug, 'optionstrat', 'OptionStrat semantic register has the wrong family slug');
assert.equal(familySemanticRegister.requirements.length, 8, `expected 8 OptionStrat public-surface requirements, found ${familySemanticRegister.requirements.length}`);
const locatorById = new Map(traceRows.map(row => [row.requirement_locator_id, row]));
const reportCache = new Map();
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

const verifyManifest = async (entries, label) => {
  const seen = new Set();
  for (const entry of entries) {
    assert.ok(entry.path && /^[a-f0-9]{64}$/.test(entry.sha256), `${label} entry requires a repo path and lowercase SHA-256`);
    assert.ok(!seen.has(entry.path), `${label} contains a duplicate path: ${entry.path}`);
    seen.add(entry.path);
    const absolute = path.resolve(root, entry.path);
    const relative = path.relative(root, absolute);
    assert.ok(relative && !relative.startsWith('..'), `${label} path must stay inside the repository: ${entry.path}`);
    assert.ok(existsSync(absolute), `${label} file is missing: ${entry.path}`);
    const bytes = await readFile(absolute);
    assert.equal(sha256(bytes), entry.sha256, `${label} hash changed: ${entry.path}`);
    reportCache.set(absolute, bytes.toString('utf8'));
  }
  return seen;
};

const sourceManifestPaths = await verifyManifest(familySemanticRegister.sourceManifest, 'OptionStrat source manifest');
await verifyManifest(familySemanticRegister.implementationManifest, 'OptionStrat implementation manifest');

const semanticIds = new Set();
const familySemanticRecords = await Promise.all(familySemanticRegister.requirements.map(async requirement => {
  assert.ok(requirement.requirement_id && !semanticIds.has(requirement.requirement_id), `duplicate or missing semantic requirement ID: ${requirement.requirement_id}`);
  semanticIds.add(requirement.requirement_id);
  if (requirement.family_slug !== undefined) assert.equal(requirement.family_slug, familySemanticRegister.familySlug, `${requirement.requirement_id} family slug mismatch`);
  assert.equal(requirement.full_vendor_recreation, false, `${requirement.requirement_id} cannot claim a full vendor recreation`);
  assert.ok(Array.isArray(requirement.source_references) && requirement.source_references.length > 0, `${requirement.requirement_id} needs source spans`);
  for (const reference of requirement.source_references) {
    assert.ok(sourceManifestPaths.has(reference.path), `${requirement.requirement_id} source is absent from the hash manifest: ${reference.path}`);
    const absolute = path.resolve(root, reference.path);
    const relative = path.relative(root, absolute);
    assert.ok(relative && !relative.startsWith('..'), `${requirement.requirement_id} source must stay inside the repository`);
    const contents = reportCache.get(absolute);
    assert.ok(contents !== undefined, `${requirement.requirement_id} source has not been hash-verified: ${reference.path}`);
    const lineCount = contents.split(/\r?\n/).length;
    assert.ok(Number.isInteger(reference.startLine) && Number.isInteger(reference.endLine)
      && reference.startLine > 0 && reference.endLine >= reference.startLine && reference.endLine <= lineCount,
    `${requirement.requirement_id} has an invalid source span in ${reference.path}`);
  }
  const { source_references, ...fields } = requirement;
  return {
    ...fields,
    family_slug: familySemanticRegister.familySlug,
    full_vendor_recreation: String(fields.full_vendor_recreation),
    record_kind: 'FAMILY_PUBLIC_SURFACE',
    source_references: source_references.map(reference => `${reference.path}#L${reference.startLine}-L${reference.endLine}`).join('; '),
  };
}));

const verifyLocalLineReference = async (baseDirectory, reference, context) => {
  const match = reference.match(/^(.+?)#L(\d+)$/);
  assert.ok(match, `${context} must use a local #L line reference`);
  const absolute = path.resolve(baseDirectory, match[1]);
  const relative = path.relative(root, absolute);
  assert.ok(relative && !relative.startsWith('..'), `${context} source must stay inside the repository`);
  assert.ok(existsSync(absolute), `${context} source report is missing: ${match[1]}`);
  if (!reportCache.has(absolute)) reportCache.set(absolute, await readFile(absolute, 'utf8'));
  const lineNumber = Number(match[2]);
  const lineCount = reportCache.get(absolute).split(/\r?\n/).length;
  assert.ok(lineNumber > 0 && lineNumber <= lineCount, `${context} line anchor #L${lineNumber} is outside ${match[1]}`);
};

const resolveCandidateSources = async row => {
  const locatorIds = row.report_locator_ids.split(';').map(value => value.trim()).filter(Boolean);
  assert.ok(locatorIds.length, `${row.requirement_id} has no report locator IDs`);
  return Promise.all(locatorIds.map(async locatorId => {
    const locator = locatorById.get(locatorId);
    assert.ok(locator, `${row.requirement_id} references unknown locator ${locatorId}`);
    assert.equal(locator.family_slug, row.family_slug, `${row.requirement_id} locator family mismatch`);
    const start = Number(locator.report_line_start);
    const end = Number(locator.report_line_end);
    assert.ok(start > 0 && end >= start, `${locatorId} has an invalid line span`);
    const absolute = path.resolve(root, locator.report_path);
    const relative = path.relative(root, absolute);
    assert.ok(relative && !relative.startsWith('..'), `${locatorId} source must stay inside the repository`);
    assert.ok(existsSync(absolute), `${row.requirement_id} source report is missing: ${locator.report_path}`);
    if (!reportCache.has(absolute)) reportCache.set(absolute, await readFile(absolute, 'utf8'));
    const lines = reportCache.get(absolute).split(/\r?\n/);
    assert.ok(end <= lines.length, `${row.requirement_id} locator ${locatorId} is outside ${locator.report_path}`);
    return `${locatorId} [${locator.report_path}#L${start}-L${end}] (${locator.report_section})`;
  }));
};

const candidateRecords = await Promise.all(candidateRows.map(async row => {
  assert.equal(row.full_vendor_recreation, 'false', `${row.requirement_id} must retain its current non-recreation status`);
  for (const requiredPath of [row.implementation_note, row.code_path]) {
    assert.ok(existsSync(path.resolve(root, requiredPath)), `${row.requirement_id} implementation reference is missing: ${requiredPath}`);
  }
  const sourceReferences = await resolveCandidateSources(row);
  return {
    requirement_id: row.requirement_id,
    record_kind: 'BOUNDED_CANDIDATE',
    family_slug: row.family_slug,
    requirement_scope: row.requirement_scope,
    user_job: row.user_job,
    inputs: row.inputs,
    outputs: row.outputs,
    rules_settings_and_states: row.rules_and_settings,
    states_and_failure_modes: row.states_and_failure_modes,
    evidence_class_or_grade: row.evidence_grade_and_class,
    source_references: sourceReferences.join('; '),
    implementation_mapping: [
      `note=${row.implementation_note}`,
      `code=${row.code_path}`,
      `functions=${row.code_functions}`,
      `route=${row.route_id}`,
    ].join('; '),
    mapping_status: 'PARTIAL_CANDIDATE',
    reconstruction_choices: row.reconstruction_choices,
    known_gaps_and_nonclaims: row.known_gaps_and_nonclaims,
    rights_boundary: row.family_slug === 'danelfin'
      ? 'W2-51 rights recheck: Danelfin API terms limit use to internal purposes and prohibit transfer or third-party disclosure of API scores/data without consent and competing/displacing use. The bounded portfolio route remains user-supplied-CSV only; API/data ingestion and Danelfin-specific marketing/competing behavior remain on hold pending an applicable grant or rights review.'
      : 'NOT_SEPARATELY_CAPTURED_IN_CANDIDATE_REGISTER; review source-specific rights before extending this slice.',
    fixture_or_validation_reference: row.fixture_or_validation_reference,
    validation_status: row.fixture_validation_status,
    full_vendor_recreation: row.full_vendor_recreation,
  };
}));

const scopedRecords = await Promise.all(scopedRows.map(async row => {
  const reference = row.source_reference;
  await verifyLocalLineReference(path.dirname(path.join(root, scopedPath)), reference, row.requirement_id);
  const sourcePath = reference.slice(0, reference.indexOf('#'));
  assert.equal(path.basename(sourcePath, '.md'), row.family_slug, `${row.requirement_id} source report/family mismatch`);
  return {
    requirement_id: row.requirement_id,
    record_kind: 'SCOPED_PUBLIC_EVIDENCE',
    family_slug: row.family_slug,
    requirement_scope: 'SCOPED_PUBLIC_EVIDENCE_AND_RIGHTS_SLICE',
    user_job: row.user_job,
    inputs: row.inputs,
    outputs: row.outputs,
    rules_settings_and_states: row.rules_and_states,
    states_and_failure_modes: 'No vendor workflow is implemented in this evidence record; unresolved behavior remains unknown or unavailable as stated in the source rule contract.',
    evidence_class_or_grade: row.evidence_class,
    source_references: `${row.source_reference} (${row.evidence_statement})`,
    implementation_mapping: row.implementation_mapping,
    mapping_status: row.mapping_state,
    reconstruction_choices: 'No vendor calculation is reconstructed; this record captures public evidence and its visible uncertainty.',
    known_gaps_and_nonclaims: 'This scoped research record is not a full vendor workflow; see the implementation mapping and rights boundary.',
    rights_boundary: row.rights_boundary,
    fixture_or_validation_reference: 'Static evidence index only; no behavioral fixture is present.',
    validation_status: 'SCOPED_INDEX_SCHEMA_AND_LOCAL_SOURCE_ANCHOR_CHECKS_PASS',
    full_vendor_recreation: 'false',
  };
}));

const rows = [...candidateRecords, ...scopedRecords, ...familySemanticRecords];
assert.equal(rows.length, 31, 'unified record count changed; review the adopted source registers before regenerating');
assert.equal(new Set(rows.map(row => row.requirement_id)).size, rows.length, 'unified requirement IDs must be unique');
for (const row of rows) {
  for (const header of headers) assert.ok(row[header], `${row.requirement_id} has an empty ${header}`);
  assert.equal(row.full_vendor_recreation, 'false', `${row.requirement_id} must not claim full vendor recreation`);
}
const familyCounts = Object.fromEntries([...new Set(rows.map(row => row.family_slug))].sort().map(slug => [slug, rows.filter(row => row.family_slug === slug).length]));
assert.equal(Object.keys(familyCounts).length, 11, `expected 11 represented families, found ${Object.keys(familyCounts).length}`);
const recordKindCounts = Object.fromEntries([...new Set(rows.map(row => row.record_kind))].sort().map(kind => [kind, rows.filter(row => row.record_kind === kind).length]));
assert.deepEqual(recordKindCounts, { BOUNDED_CANDIDATE: 9, FAMILY_PUBLIC_SURFACE: 8, SCOPED_PUBLIC_EVIDENCE: 14 });

const csv = serializeCsv(rows, headers);
const roundTrip = parseCsv(csv);
assert.equal(roundTrip.length, rows.length, 'unified CSV round-trip row count differs');
for (let index = 0; index < rows.length; index++) {
  for (const header of headers) assert.equal(roundTrip[index][header], rows[index][header], `${rows[index].requirement_id} round-trip changed ${header}`);
}
await writeFile(path.join(root, outputPath), csv, 'utf8');
console.log(JSON.stringify({
  output: outputPath,
  rows: rows.length,
  families: Object.keys(familyCounts).length,
  recordKinds: recordKindCounts,
  candidateLocatorReferencesVerified: candidateRecords.reduce((total, row) => total + [...row.source_references.matchAll(/\bLOC-[A-Za-z0-9-]+\b/g)].length, 0),
  sourceFilesHashVerified: familySemanticRegister.sourceManifest.length + familySemanticRegister.implementationManifest.length,
  fullVendorRecreations: rows.filter(row => row.full_vendor_recreation === 'true').length,
}, null, 2));
