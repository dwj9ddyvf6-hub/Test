import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const indexPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS_FILE_INDEX.csv');
const outputPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-GAP-REVIEW-MATRIX-2026-10-27.csv');
const overridePath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-GAP-TRIAGE-OVERRIDES-2026-10-28.csv');
const availabilityReviewDate = new Date().toISOString().slice(0, 10);
const inventory = parseCsv(await readFile(indexPath, 'utf8'));
const gaps = inventory.filter(row => row.availability !== 'present-in-checkout');
const sparse = gaps.filter(row => row.availability === 'tracked-but-not-materialized-in-sparse-checkout');
const vault = gaps.filter(row => row.corpus === 'legacy-rea-oversize-vault');
assert.equal(sparse.length, 0, 'all tracked sparse paths must be materialized before regenerating the gap matrix');
assert.equal(vault.length, 39, 'local-vault reference count changed; review before regenerating the gap matrix');
const recoveryPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-VAULT-SHARD-RECOVERY-2026-10-28.csv');
const recoveryRows = parseCsv(await readFile(recoveryPath, 'utf8'));
const recoveryByPath = new Map(recoveryRows.map(row => [row.source_path, row]));
assert.equal(recoveryRows.length, 39, 'verified shard recovery ledger is missing or has an unexpected row count');
for (const item of vault) {
  const recovery = recoveryByPath.get(item.path);
  assert.ok(recovery, 'shard recovery record is missing: ' + item.path);
  assert.equal(recovery.verification_status, 'VERIFIED_SOURCE_FROM_TRACKED_SHARDS', 'source shards have not passed integrity verification: ' + item.path);
  assert.equal(recovery.expected_sha256, item.sha256_from_manifest, 'manifest hash drift for ' + item.path);
}
assert.equal(gaps.length, sparse.length + vault.length, 'new unresolved availability status needs a disposition rule');

const originMainCommit = execFileSync('git', ['rev-parse', '--verify', 'origin/main^{commit}'], {
  cwd: root,
  encoding: 'utf8',
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
}).trim();
const originTreeOutput = execFileSync('git', ['ls-tree', '-r', '--full-tree', 'origin/main'], {
  cwd: root,
  encoding: 'utf8',
  maxBuffer: 16 * 1024 * 1024,
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
});
const originTreeByPath = new Map();
for (const line of originTreeOutput.trimEnd().split(/\r?\n/)) {
  const tab = line.indexOf('\t');
  assert.ok(tab > 0, `unexpected origin/main tree row: ${line}`);
  const [mode, type, oid] = line.slice(0, tab).split(/\s+/);
  assert.ok(['blob', 'commit'].includes(type), `unexpected origin/main tree object type: ${type}`);
  assert.match(oid, /^[0-9a-f]{40,64}$/);
  originTreeByPath.set(line.slice(tab + 1), oid);
}

const overrides = parseCsv(await readFile(overridePath, 'utf8'));
const indexedPaths = new Set(inventory.map(item => item.path));
const gapsByPath = new Map(gaps.map(item => [item.path, item]));
const overrideByPath = new Map();
for (const override of overrides) {
  assert.ok(indexedPaths.has(override.path), `triage override is not an indexed corpus path: ${override.path}`);
  assert.ok(!overrideByPath.has(override.path), `duplicate triage override: ${override.path}`);
  for (const field of ['scope_review_status', 'rights_review_status', 'implementation_review_status', 'triage_status', 'disposition', 'next_action', 'triage_review_date', 'triage_review_reviewer', 'triage_review_method', 'triage_review_evidence']) {
    assert.ok(override[field]?.trim(), `triage override ${override.path} is missing ${field}`);
  }
  for (const field of ['content_read', 'semantically_reviewed', 'rights_checked', 'implementation_mapped']) {
    assert.ok(['true', 'false'].includes(override[field]), `triage override ${override.path} has invalid ${field}`);
  }
  overrideByPath.set(override.path, override);
}

const sparseObjectIds = sparse.map(item => item.git_blob_oid);
assert.ok(sparseObjectIds.every(oid => /^[0-9a-f]{40,64}$/.test(oid)), 'sparse path is missing a valid Git blob object ID');
const objectChecks = sparse.length ? execFileSync('git', ['cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)'], {
  cwd: root,
  input: `${sparseObjectIds.join('\n')}\n`,
  encoding: 'utf8',
  maxBuffer: 4 * 1024 * 1024,
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
}).trim().split(/\r?\n/) : [];
assert.equal(objectChecks.length, sparse.length, 'Git returned an unexpected number of object metadata rows');
const localObjectsById = new Map(objectChecks.map(line => {
  const match = line.match(/^([0-9a-f]{40,64}) (blob|missing)(?: (\d+))?$/);
  assert.ok(match, `unexpected git cat-file metadata row: ${line}`);
  return [match[1], match[2] === 'missing'
    ? { status: 'missing-from-local-object-database-fetchability-unverified', type: '', size: '' }
    : { status: 'present-in-local-object-database-not-materialized', type: match[2], size: match[3] }];
}));

const rows = gaps.map(item => {
  const manifestOnly = item.corpus === 'legacy-rea-oversize-vault';
  const override = overrideByPath.get(item.path);
  const localPathExists = existsSync(path.join(root, ...item.path.split('/')));
  if (!manifestOnly) assert.equal(localPathExists, false, `sparse path unexpectedly materialized; refresh inventory and review: ${item.path}`);
  const object = manifestOnly ? null : localObjectsById.get(item.git_blob_oid);
  assert.ok(manifestOnly || object, `Git object metadata was not returned for ${item.path}`);
  const originMainOid = originTreeByPath.get(item.path);
  const originMainTreeStatus = manifestOnly
    ? (originMainOid ? 'indexed-path-present-in-origin-main' : 'indexed-path-absent-from-origin-main')
    : (originMainOid === item.git_blob_oid ? 'path-and-blob-oid-match-origin-main' : 'path-or-blob-oid-mismatch-in-origin-main');
  const localUnavailableReviewed = override?.triage_status === 'REVIEWED_UNAVAILABLE_AT_CHECKED_PATHS';
  const recovery = manifestOnly ? recoveryByPath.get(item.path) : null;
  const sourceBytesIntegrityVerified = recovery?.verification_status === 'VERIFIED_SOURCE_FROM_TRACKED_SHARDS';
  return {
    path: item.path,
    corpus: item.corpus,
    kind: item.kind,
    extension: item.extension,
    size_bytes: item.size_bytes,
    git_blob_oid: item.git_blob_oid,
    git_object_status: manifestOnly ? 'not-applicable-local-manifest-reference' : object.status,
    git_object_type: object?.type || '',
    git_object_size_bytes: object?.size || '',
    origin_main_tree_status: originMainTreeStatus,
    origin_main_tree_commit: originMainCommit,
    availability: item.availability,
    availability_review_status: manifestOnly
      ? (sourceBytesIntegrityVerified ? 'SHARDED_SOURCE_STREAM_SHA256_AND_GIT_TREE_VERIFIED'
        : localUnavailableReviewed ? 'UNSHARDED_SOURCE_PATH_ABSENT_SHARD_RECOVERY_UNVERIFIED' : 'MANIFEST_METADATA_ONLY_LOCATION_UNVERIFIED')
      : object.status,
    availability_review_date: override?.triage_review_date || availabilityReviewDate,
    availability_review_reviewer: override?.triage_review_reviewer || 'Codex',
    availability_review_method: override?.triage_review_method || (manifestOnly
      ? 'Repository manifest metadata only; referenced external path not checked.'
      : 'git cat-file --batch-check with GIT_NO_LAZY_FETCH=1 plus origin/main git ls-tree path/OID check; blob contents not read.'),
    availability_review_evidence: override?.triage_review_evidence || `research/rea-teardowns/synthesis/CORPUS_FILE_INDEX.csv; origin/main@${originMainCommit}`,
    local_manifest_reference: manifestOnly ? item.availability.replace(/^[^:]+:\\s*/, '').trim() : '',
    sha256_from_manifest: item.sha256_from_manifest,
    source_recovery_status: recovery?.verification_status || '',
    source_recovery_part_count: recovery?.observed_part_count || '',
    source_recovery_bytes: recovery?.observed_git_blob_bytes || '',
    source_recovery_sha256: recovery?.reconstructed_git_blob_stream_sha256 || '',
    source_bytes_integrity_verified: sourceBytesIntegrityVerified,
    source_recovery_origin_main_commit: recovery?.origin_main_commit || '',
    listed: true,
    materialized_in_checkout: localPathExists,
    content_read: override?.content_read || false,
    semantically_reviewed: override?.semantically_reviewed || false,
    rights_checked: override?.rights_checked || false,
    implementation_mapped: override?.implementation_mapped || false,
    scope_review_status: override?.scope_review_status || 'NOT_REVIEWED',
    rights_review_status: override?.rights_review_status || 'NOT_REVIEWED',
    implementation_review_status: override?.implementation_review_status || 'NOT_REVIEWED',
    triage_review_date: override?.triage_review_date || '',
    triage_review_reviewer: override?.triage_review_reviewer || '',
    triage_review_method: override?.triage_review_method || '',
    triage_review_evidence: override?.triage_review_evidence || '',
    triage_status: override?.triage_status || (manifestOnly ? 'BLOCKED_VAULT_BYTES_UNAVAILABLE'
      : object.status === 'present-in-local-object-database-not-materialized'
        ? 'AVAILABLE_LOCAL_OBJECT_PENDING_SCOPE_RIGHTS'
        : originMainTreeStatus === 'path-and-blob-oid-match-origin-main'
          ? 'ORIGIN_MAIN_TREE_ENTRY_CONFIRMED_LOCAL_BLOB_MISSING_FETCHABILITY_UNVERIFIED'
          : 'ORIGIN_MAIN_TREE_ENTRY_UNVERIFIED_REVIEW_REQUIRED'),
    disposition: override?.disposition || (manifestOnly ? 'reference-only-no-bytes-in-checkout' : object.status === 'present-in-local-object-database-not-materialized'
      ? 'local-object-available-awaiting-scope-and-rights-selection'
      : originMainTreeStatus === 'path-and-blob-oid-match-origin-main'
        ? 'origin-main-tree-entry-confirmed-local-blob-absent-content-not-read'
        : 'origin-main-tree-path-or-blob-oid-unverified'),
    next_action: override?.next_action || (manifestOnly ? 'Recover from an owner-controlled source or record unavailable.' : object.status === 'present-in-local-object-database-not-materialized'
      ? 'Triage scope and rights, then selectively materialize if needed.'
      : originMainTreeStatus === 'path-and-blob-oid-match-origin-main'
        ? 'Review scope and rights; selectively materialize only if needed.'
        : 'Check the authorized origin tree and archive availability only if selected by scope and rights review.'),
  };
});

const outputHeaders = Object.keys(rows[0]);
await writeFile(outputPath, serializeCsv(rows, outputHeaders), 'utf8');
process.stdout.write(JSON.stringify({
  output: path.relative(root, outputPath).replaceAll(path.sep, '/'),
  totalGapRows: rows.length,
  sparseTrackedPaths: sparse.length,
  localVaultReferences: vault.length,
  originMainTreeCommit: originMainCommit,
  originMainSparsePathMatches: rows.filter(row => row.corpus !== 'legacy-rea-oversize-vault' && row.origin_main_tree_status === 'path-and-blob-oid-match-origin-main').length,
  originalUnshardedVaultPathsAbsent: rows.filter(row => row.corpus === 'legacy-rea-oversize-vault' && row.origin_main_tree_status === 'indexed-path-absent-from-origin-main').length,
  shardedVaultSourceStreamsVerified: rows.filter(row => row.corpus === 'legacy-rea-oversize-vault' && row.source_recovery_status === 'VERIFIED_SOURCE_FROM_TRACKED_SHARDS').length,
  sparseGitObjectsPresent: rows.filter(row => row.git_object_status === 'present-in-local-object-database-not-materialized').length,
  sparseGitObjectsMissing: rows.filter(row => row.git_object_status === 'missing-from-local-object-database-fetchability-unverified').length,
  availabilityMetadataReviewed: rows.filter(row => row.availability_review_status).length,
  triageOverridesApplied: rows.filter(row => overrideByPath.has(row.path)).length,
  materializedButNotReviewed: rows.filter(row => row.materialized_in_checkout).length,
  contentRead: rows.filter(row => row.content_read === true || row.content_read === 'true').length,
  semanticReviews: rows.filter(row => row.semantically_reviewed === true || row.semantically_reviewed === 'true').length,
  rightsReviews: rows.filter(row => row.rights_checked === true || row.rights_checked === 'true').length,
  implementationReviews: rows.filter(row => row.implementation_mapped === true || row.implementation_mapped === 'true').length,
  gitObjectMetadataCheckedWithoutLazyFetch: true,
  gitObjectContentsReadByThisRun: false,
}, null, 2) + '\n');
