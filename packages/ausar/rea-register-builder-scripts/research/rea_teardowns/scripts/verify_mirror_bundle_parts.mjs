import assert from 'node:assert/strict';
import { createReadStream } from 'node:fs';
import { readFile, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const manifestPath = path.join(root, 'MANIFEST.md');
const outputPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-MIRROR-BUNDLE-RECOVERY-2026-10-28.csv');
const manifest = await readFile(manifestPath, 'utf8');
const manifestRows = [];
for (const line of manifest.split(/\r?\n/)) {
  if (!line.startsWith('|') || !line.endsWith('|')) continue;
  const fields = line.slice(1, -1).split('|').map(value => value.trim());
  if (fields.length !== 5 || !/^\d+$/.test(fields[2]) || !/^\d+$/.test(fields[4])) continue;
  const prefix = fields[3].match(/^[0-9a-fA-F]+/)?.[0]?.toLowerCase() || '';
  assert.ok(prefix.length >= 8, `manifest SHA-256 prefix is missing for ${fields[0]}`);
  manifestRows.push({ repo: fields[0], defaultHead: fields[1], expectedBytes: Number(fields[2]), sha256Prefix: prefix, expectedParts: Number(fields[4]) });
}
assert.equal(manifestRows.length, 224, 'mirror manifest repo count changed; review before verifying');

const staged = execFileSync('git', ['ls-files', '--stage', '-z', '--', 'bundles'], {
  cwd: root,
  encoding: 'utf8',
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
});
const oidByPath = new Map();
for (const record of staged.split('\0').filter(Boolean)) {
  const tab = record.indexOf('\t');
  const [mode, oid, stage] = record.slice(0, tab).split(' ');
  const relative = record.slice(tab + 1).replaceAll('\\', '/');
  assert.equal(stage, '0', `unmerged bundle path: ${relative}`);
  assert.match(oid, /^[0-9a-f]{40,64}$/);
  oidByPath.set(relative, oid);
}
assert.equal(oidByPath.size, 403, 'tracked mirror bundle-part count changed; review before verifying');

const rows = [];
let totalBytes = 0;
let verifiedPartBlobs = 0;
for (const item of manifestRows) {
  const partPaths = item.expectedParts === 1
    ? [`bundles/${item.repo}.bundle`]
    : Array.from({ length: item.expectedParts }, (_, i) => `bundles/${item.repo}.bundle.part${String(i).padStart(2, '0')}`);
  const bundleHash = createHash('sha256');
  let observedBytes = 0;
  let verifiedParts = 0;
  for (const relative of partPaths) {
    const expectedOid = oidByPath.get(relative);
    assert.ok(expectedOid, `manifest part is not tracked: ${relative}`);
    const absolute = path.join(root, ...relative.split('/'));
    const fileStat = await stat(absolute);
    assert.ok(fileStat.isFile(), `bundle part is not a regular file: ${relative}`);
    const partHash = createHash('sha1');
    partHash.update(Buffer.from(`blob ${fileStat.size}\0`));
    for await (const chunk of createReadStream(absolute)) {
      partHash.update(chunk);
      bundleHash.update(chunk);
      observedBytes += chunk.length;
    }
    const observedOid = partHash.digest('hex');
    assert.equal(observedOid, expectedOid, `Git blob hash mismatch: ${relative}`);
    verifiedParts += 1;
    verifiedPartBlobs += 1;
  }
  const observedSha256 = bundleHash.digest('hex');
  const byteCountVerified = observedBytes === item.expectedBytes;
  const shaPrefixVerified = observedSha256.startsWith(item.sha256Prefix);
  assert.ok(byteCountVerified, `manifest byte count mismatch for ${item.repo}: ${observedBytes} != ${item.expectedBytes}`);
  assert.ok(shaPrefixVerified, `manifest SHA-256 prefix mismatch for ${item.repo}`);
  assert.equal(verifiedParts, item.expectedParts);
  totalBytes += observedBytes;
  rows.push({
    repo: item.repo,
    default_head_manifest: item.defaultHead,
    expected_parts: item.expectedParts,
    verified_parts: verifiedParts,
    expected_bytes: item.expectedBytes,
    observed_bytes: observedBytes,
    manifest_sha256_prefix: item.sha256Prefix,
    observed_bundle_sha256: observedSha256,
    git_blob_parts_verified: verifiedParts === item.expectedParts,
    byte_count_verified: byteCountVerified,
    manifest_sha256_prefix_verified: shaPrefixVerified,
    semantic_payload_reviewed: false,
    bundle_extracted: false,
    verification_status: 'VERIFIED_TRACKED_PART_BLOBS_BUNDLE_SIZE_AND_MANIFEST_SHA256_PREFIX',
  });
}
assert.equal(totalBytes, 4_019_267_109, 'mirror manifest aggregate size changed; review before updating');
assert.equal(verifiedPartBlobs, 403);
await writeFile(outputPath, serializeCsv(rows, Object.keys(rows[0])), 'utf8');
process.stdout.write(JSON.stringify({
  output: path.relative(root, outputPath).replaceAll(path.sep, '/'),
  manifestRepositories: manifestRows.length,
  bundlePartBlobsVerified: verifiedPartBlobs,
  bundleStreamsVerified: rows.length,
  expectedBytes: totalBytes,
  observedBytes: totalBytes,
  semanticPayloadRead: false,
  bundlesExtracted: false,
}, null, 2) + '\n');