import assert from 'node:assert/strict';
import { existsSync, lstatSync } from 'node:fs';
import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const indexRelativePath = 'research/rea-teardowns/synthesis/CORPUS_FILE_INDEX.csv';
const indexPath = path.join(root, ...indexRelativePath.split('/'));
const headers = ['path', 'corpus', 'kind', 'extension', 'size_bytes', 'git_blob_oid', 'availability', 'sha256_from_manifest'];
const previousSnapshot = execFileSync('git', ['show', `HEAD:${indexRelativePath}`], {
  cwd: root,
  encoding: 'utf8',
  maxBuffer: 64 * 1024 * 1024,
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
});
const previousRows = parseCsv(previousSnapshot);
const previousByPath = new Map(previousRows.map(row => [row.path, row]));
const recoveryPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-VAULT-SHARD-RECOVERY-2026-10-28.csv');
const recoveryRows = parseCsv(await readFile(recoveryPath, 'utf8'));
const recoveryByPath = new Map(recoveryRows.map(row => [row.source_path, row]));
assert.equal(recoveryRows.length, 39, 'verified shard recovery ledger is missing or has an unexpected row count');
assert.ok(recoveryRows.every(row => row.verification_status === 'VERIFIED_SOURCE_FROM_TRACKED_SHARDS'), 'all shard sources must verify before rebuilding the corpus index');
const vaultRows = previousRows.filter(row => row.corpus === 'legacy-rea-oversize-vault');
assert.equal(vaultRows.length, 39, 'local-vault reference count changed; review the source manifest before rebuilding');

const stagedFiles = execFileSync('git', ['ls-files', '--stage', '-z'], {
  cwd: root,
  encoding: 'utf8',
  maxBuffer: 64 * 1024 * 1024,
});
const tracked = [];
for (const record of stagedFiles.split('\0').filter(Boolean)) {
  const tab = record.indexOf('\t');
  assert.ok(tab > 0, 'unexpected git ls-files --stage record');
  const [mode, oid, stage] = record.slice(0, tab).split(' ');
  const relativePath = record.slice(tab + 1).replaceAll('\\', '/');
  assert.equal(stage, '0', `unmerged index entry needs review: ${relativePath}`);
  if (relativePath === indexRelativePath) continue; // prevent the inventory from listing itself

  const old = previousByPath.get(relativePath);
  const parts = relativePath.split('/');
  const basename = parts.at(-1);
  const extension = path.posix.extname(basename).toLowerCase() || (basename.startsWith('.') ? basename : '');
  let sizeBytes = '';
  let present = false;
  try {
    const stat = lstatSync(path.join(root, ...parts));
    present = true;
    if (stat.isFile() || stat.isSymbolicLink()) sizeBytes = stat.size;
  } catch { /* sparse-checkout path */ }

  let inferredCorpus = parts[0] || 'repository-root';
  if (parts.length === 1) inferredCorpus = 'repository-root';
  else if (parts[0] === 'apps' && parts[1] === 'silicon-market-terminal') inferredCorpus = 'silicon-market-terminal';
  else if (parts[0] === 'research' && parts[1] === 'rea_teardowns') inferredCorpus = 'current-rea';
  else if (parts[0] === 'research' && parts[1] === 'rea-teardowns') inferredCorpus = 'legacy-rea';
  else if (parts[0] === 'research') inferredCorpus = `research/${parts[1] || ''}`;

  let inferredKind = 'other';
  if (['.md', '.txt', '.rst'].includes(extension)) inferredKind = 'documentation';
  else if (['.js', '.mjs', '.cjs', '.ts', '.tsx', '.py', '.ps1', '.sh', '.html', '.css', '.sql'].includes(extension)) inferredKind = 'source-or-script';
  else if (['.csv', '.tsv', '.json', '.jsonl', '.yaml', '.yml', '.toml'].includes(extension)) inferredKind = 'data';

  tracked.push({
    path: relativePath,
    corpus: old?.corpus || inferredCorpus,
    kind: old?.kind || inferredKind,
    extension: old?.extension || extension,
    size_bytes: present ? sizeBytes : old?.size_bytes || '',
    git_blob_oid: oid,
    availability: present ? 'present-in-checkout' : 'tracked-but-not-materialized-in-sparse-checkout',
    sha256_from_manifest: old?.sha256_from_manifest || '',
  });
}

const trackedPaths = new Set(tracked.map(row => row.path));
const stalePreviousPaths = previousRows.filter(row => row.corpus !== 'legacy-rea-oversize-vault' && row.path !== indexRelativePath && !trackedPaths.has(row.path));
assert.equal(stalePreviousPaths.length, 0, `tracked paths disappeared since the prior inventory: ${stalePreviousPaths.map(row => row.path).slice(0, 10).join(', ')}`);
const sparseCount = tracked.filter(row => row.availability === 'tracked-but-not-materialized-in-sparse-checkout').length;
assert.equal(sparseCount, 0, 'all tracked paths must be materialized before rebuilding the corpus index');

const trackedByPath = new Map(tracked.map(row => [row.path, row]));
const priorOrder = previousRows.map(row => {
  if (row.corpus === 'legacy-rea-oversize-vault') {
    const recovery = recoveryByPath.get(row.path);
    assert.ok(recovery, 'shard recovery record is missing: ' + row.path);
    assert.equal(recovery.expected_sha256, row.sha256_from_manifest, 'manifest hash drift for ' + row.path);
    return { ...row, availability: 'recoverable-from-verified-tracked-shards: ' + recovery.manifest_vault_path };
  }
  return trackedByPath.get(row.path);
});
const newTrackedRows = tracked.filter(row => !previousByPath.has(row.path));
const rows = [...priorOrder, ...newTrackedRows]; // retain the full prior order and append newly tracked paths
assert.equal(rows.length, tracked.length + vaultRows.length);
await writeFile(indexPath, serializeCsv(rows, headers, {
  quoteNonEmpty: true,
  quoteHeaders: true,
  quoteEmptyFields: ['extension', 'git_blob_oid', 'sha256_from_manifest'],
  lineEnding: '\n',
}), 'utf8');

process.stdout.write(JSON.stringify({
  output: indexRelativePath,
  trackedPathsExcludingInventory: tracked.length,
  trackedPresentInCheckout: tracked.length - sparseCount,
  sparsePaths: sparseCount,
  localVaultReferences: vaultRows.length,
  inventoryRows: rows.length,
  selfExcluded: true,
  blobContentsRead: false,
}, null, 2) + '\n');
