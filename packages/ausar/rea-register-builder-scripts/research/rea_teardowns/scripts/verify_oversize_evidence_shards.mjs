import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawn, execFileSync } from 'node:child_process';
import { readFile, readdir, rename, unlink, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const manifestPath = path.join(root, 'research', 'rea-teardowns', 'OVERSIZE-EVIDENCE-MANIFEST.md');
const indexPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS_FILE_INDEX.csv');
const outputPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-VAULT-SHARD-RECOVERY-2026-10-28.csv');
const chunkBytes = 20_000_000;
const restoreWorkingTree = process.argv.includes('--restore-working-tree');

const manifest = await readFile(manifestPath, 'utf8');
const manifestRows = manifest.split(/\r?\n/)
  .filter(line => /^\|\s*workspace\/opt\/rea-teardowns\//.test(line))
  .map(line => line.slice(1, -1).split('|').map(cell => cell.trim()))
  .map(([sourcePath, manifestVaultPath, bytes, sha256]) => ({
    sourcePath,
    manifestVaultPath,
    expectedBytes: Number(bytes),
    expectedSha256: sha256.toLowerCase(),
  }));
assert.equal(manifestRows.length, 39, 'expected the 39-file oversize evidence manifest');
assert.ok(manifestRows.every(row => row.sourcePath && row.manifestVaultPath && Number.isSafeInteger(row.expectedBytes) && /^[0-9a-f]{64}$/.test(row.expectedSha256)), 'manifest contains an invalid row');
assert.equal(manifestRows.reduce((total, row) => total + row.expectedBytes, 0), 4_185_551_561, 'manifest byte total changed');

const indexRows = parseCsv(await readFile(indexPath, 'utf8'));
const trackedOids = new Map(indexRows.filter(row => row.path && row.git_blob_oid).map(row => [row.path, row.git_blob_oid]));
const originCommit = execFileSync('git', ['rev-parse', '--verify', 'origin/main^{commit}'], {
  cwd: root, encoding: 'utf8', env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
}).trim();
const treeOutput = execFileSync('git', ['ls-tree', '-r', '--full-tree', 'origin/main'], {
  cwd: root, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
});
const originTree = new Map();
for (const line of treeOutput.trimEnd().split(/\r?\n/)) {
  const tab = line.indexOf('\t');
  assert.ok(tab > 0, 'unexpected origin/main tree row');
  const fields = line.slice(0, tab).split(/\s+/);
  assert.equal(fields[1], 'blob', 'unexpected Git tree entry type');
  originTree.set(line.slice(tab + 1), fields[2]);
}

const states = [];
const queuedParts = [];
for (const manifestRow of manifestRows) {
  const markerIndex = manifestRow.manifestVaultPath.indexOf('/_vault/');
  assert.ok(markerIndex >= 0, 'invalid vault path: ' + manifestRow.manifestVaultPath);
  const relativeVaultPath = manifestRow.manifestVaultPath.slice(markerIndex + '/_vault/'.length);
  const segments = relativeVaultPath.split('/');
  const fileName = segments.pop();
  const localDirectory = path.join(root, 'research', 'rea-teardowns', '_vault', ...segments);
  const partPrefix = fileName + '.part';
  const directoryEntries = await readdir(localDirectory, { withFileTypes: true });
  const foundParts = new Map();
  for (const entry of directoryEntries) {
    if (!entry.isFile() || !entry.name.startsWith(partPrefix)) continue;
    const suffix = entry.name.slice(partPrefix.length);
    if (!/^\d+$/.test(suffix)) continue;
    const number = Number(suffix);
    assert.ok(!foundParts.has(number), 'duplicate shard number for ' + relativeVaultPath);
    foundParts.set(number, entry.name);
  }

  const expectedPartCount = Math.ceil(manifestRow.expectedBytes / chunkBytes);
  const expectedNumbers = Array.from({ length: expectedPartCount }, (_, index) => index + 1);
  const missingNumbers = expectedNumbers.filter(number => !foundParts.has(number));
  const unexpectedNumbers = [...foundParts.keys()].filter(number => !expectedNumbers.includes(number)).sort((a, b) => a - b);
  const state = {
    manifestRow, relativeVaultPath, expectedPartCount, missingNumbers, unexpectedNumbers,
    expectedBytes: manifestRow.expectedBytes, observedBytes: 0, sha256: createHash('sha256'),
    partRecords: [],
  };
  states.push(state);

  for (const number of expectedNumbers) {
    const partName = foundParts.get(number);
    if (!partName) continue;
    const relativePartPath = 'research/rea-teardowns/_vault/' + [...segments, partName].join('/');
    const trackedOid = trackedOids.get(relativePartPath) || '';
    const originOid = originTree.get(relativePartPath) || '';
    const expectedPartBytes = number < expectedPartCount
      ? chunkBytes
      : manifestRow.expectedBytes - chunkBytes * (expectedPartCount - 1);
    const part = { state, relativePartPath, absolutePartPath: path.join(root, ...relativePartPath.split('/')), trackedOid, originOid, expectedPartBytes };
    state.partRecords.push(part);
    part.metadataValid = Boolean(trackedOid && originOid === trackedOid);
    if (part.metadataValid) queuedParts.push(part);
  }
}

const child = spawn('git', ['cat-file', '--batch'], {
  cwd: root, env: { ...process.env, GIT_NO_LAZY_FETCH: '1' }, stdio: ['pipe', 'pipe', 'pipe'],
});
let stderr = '';
child.stderr.on('data', chunk => { if (stderr.length < 4000) stderr += chunk.toString('utf8').slice(0, 4000 - stderr.length); });
const childClosed = new Promise((resolve, reject) => {
  child.once('error', reject);
  child.once('close', (code, signal) => resolve({ code, signal }));
});
const stdoutIterator = child.stdout[Symbol.asyncIterator]();
let pending = Buffer.alloc(0);
async function appendOutput() {
  const item = await stdoutIterator.next();
  if (item.done) throw new Error('git cat-file ended early' + (stderr ? ': ' + stderr : ''));
  pending = pending.length ? Buffer.concat([pending, item.value]) : item.value;
}
async function readLine() {
  while (true) {
    const newline = pending.indexOf(0x0a);
    if (newline >= 0) {
      const line = pending.subarray(0, newline).toString('utf8');
      pending = pending.subarray(newline + 1);
      return line;
    }
    await appendOutput();
  }
}
async function streamObjectBytes(length, callback) {
  let remaining = length;
  while (remaining > 0) {
    if (!pending.length) await appendOutput();
    const take = Math.min(remaining, pending.length);
    callback(pending.subarray(0, take));
    pending = pending.subarray(take);
    remaining -= take;
  }
  while (!pending.length) await appendOutput();
  assert.equal(pending[0], 0x0a, 'git cat-file framing newline missing');
  pending = pending.subarray(1);
}

child.stdin.end(queuedParts.map(part => part.trackedOid).join('\n') + '\n');
let totalBytesStreamed = 0;
let partBlobsVerified = 0;
let workingTreePartsRestored = 0;
for (const part of queuedParts) {
  const header = await readLine();
  const match = header.match(/^([0-9a-f]{40,64}) (blob|missing)(?: (\d+))?$/);
  assert.ok(match, 'unexpected git cat-file header for ' + part.relativePartPath);
  assert.equal(match[2], 'blob', 'Git object is not a blob: ' + part.relativePartPath);
  assert.equal(match[1], part.trackedOid, 'Git object ID mismatch: ' + part.relativePartPath);
  const objectBytes = Number(match[3]);
  part.sizeValid = objectBytes === part.expectedPartBytes;
  const blobHash = createHash('sha1');
  const restoreChunks = restoreWorkingTree ? [] : null;
  blobHash.update(Buffer.from('blob ' + objectBytes + '\0', 'utf8'));
  await streamObjectBytes(objectBytes, chunk => {
    blobHash.update(chunk);
    part.state.sha256.update(chunk);
    if (restoreChunks) restoreChunks.push(Buffer.from(chunk));
  });
  part.gitBlobHashMatch = blobHash.digest('hex') === part.trackedOid;
  if (restoreWorkingTree && part.sizeValid && part.gitBlobHashMatch && part.metadataValid) {
    const temporaryPath = part.absolutePartPath + '.restore-' + process.pid + '-' + Date.now() + '.tmp';
    await writeFile(temporaryPath, Buffer.concat(restoreChunks), { flag: 'wx' });
    try {
      await rename(temporaryPath, part.absolutePartPath);
    } catch (error) {
      await unlink(temporaryPath).catch(() => {});
      throw error;
    }
    part.workingTreeRestored = true;
    workingTreePartsRestored++;
  }
  part.objectBytes = objectBytes;
  part.state.observedBytes += objectBytes;
  totalBytesStreamed += objectBytes;
  partBlobsVerified++;
  if (partBlobsVerified % 25 === 0 || partBlobsVerified === queuedParts.length) {
    process.stdout.write('verified Git blob ' + partBlobsVerified + '/' + queuedParts.length + '; ' + totalBytesStreamed + ' bytes streamed\n');
  }
}
const closeResult = await childClosed;
assert.equal(closeResult.code, 0, 'git cat-file failed: ' + (stderr || closeResult.signal || closeResult.code));

const outputRows = states.map(state => {
  const complete = state.missingNumbers.length === 0 && state.unexpectedNumbers.length === 0;
  const metadataComplete = state.partRecords.length === state.expectedPartCount && state.partRecords.every(part => part.metadataValid);
  const contentComplete = state.partRecords.every(part => Number.isSafeInteger(part.objectBytes));
  const allGitBlobOidsMatch = contentComplete && state.partRecords.every(part => part.gitBlobHashMatch);
  const allPartSizesValid = contentComplete && state.partRecords.every(part => part.sizeValid);
  const observedSha256 = complete && contentComplete ? state.sha256.digest('hex') : '';
  const sha256Match = Boolean(observedSha256 && observedSha256 === state.manifestRow.expectedSha256);
  const status = !complete ? 'INCOMPLETE_PART_SET'
    : !metadataComplete ? 'GIT_ORIGIN_METADATA_MISMATCH'
    : !allPartSizesValid ? 'PART_SIZE_MISMATCH'
    : !allGitBlobOidsMatch ? 'GIT_BLOB_OID_MISMATCH'
    : !sha256Match ? 'SOURCE_SHA256_MISMATCH'
    : 'VERIFIED_SOURCE_FROM_TRACKED_SHARDS';
  return {
    source_path: state.manifestRow.sourcePath,
    manifest_vault_path: state.manifestRow.manifestVaultPath,
    tracked_shard_pattern: 'research/rea-teardowns/_vault/' + state.relativeVaultPath + '.partNNN',
    expected_bytes: state.expectedBytes,
    observed_git_blob_bytes: state.observedBytes,
    expected_sha256: state.manifestRow.expectedSha256,
    reconstructed_git_blob_stream_sha256: observedSha256,
    expected_part_count: state.expectedPartCount,
    observed_part_count: state.partRecords.filter(part => Number.isSafeInteger(part.objectBytes)).length,
    missing_part_numbers: state.missingNumbers.join('|'),
    unexpected_part_numbers: state.unexpectedNumbers.join('|'),
    all_part_sizes_valid: allPartSizesValid,
    all_git_blob_oids_match: allGitBlobOidsMatch,
    all_origin_main_tree_entries_match: metadataComplete,
    origin_main_commit: originCommit,
    source_bytes_streamed_for_integrity: state.observedBytes,
    working_tree_shard_parts_restored: state.partRecords.filter(part => part.workingTreeRestored).length,
    content_semantically_parsed: false,
    checkout_line_endings_used: false,
    verification_status: status,
    verification_method: 'Sequential SHA-256 over raw Git blob bytes from numeric .partNNN sequence; each blob SHA-1 checked against the tracked index and origin/main tree; working-tree bytes bypassed to avoid core.autocrlf conversion; optional --restore-working-tree writes verified raw blobs to individual part paths without assembling full source files.',
  };
});

await writeFile(outputPath, serializeCsv(outputRows, Object.keys(outputRows[0]), { lineEnding: '\n' }), 'utf8');
const verified = outputRows.filter(row => row.verification_status === 'VERIFIED_SOURCE_FROM_TRACKED_SHARDS').length;
process.stdout.write(JSON.stringify({
  output: path.relative(root, outputPath).replaceAll(path.sep, '/'),
  manifestFiles: outputRows.length,
  verifiedSourceStreams: verified,
  expectedBytes: manifestRows.reduce((total, row) => total + row.expectedBytes, 0),
  bytesStreamed: totalBytesStreamed,
  partBlobsVerified,
  restoreWorkingTreeRequested: restoreWorkingTree,
  workingTreePartsRestored,
  originMainCommit: originCommit,
  semanticPayloadRead: false,
  assembledFilesCreated: false,
}, null, 2) + '\n');
if (verified !== manifestRows.length) process.exitCode = 1;
