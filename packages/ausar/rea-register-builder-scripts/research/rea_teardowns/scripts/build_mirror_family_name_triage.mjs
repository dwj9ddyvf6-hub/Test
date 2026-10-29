import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const familyPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'ACTIVE-FAMILY-SCOPE-LEDGER-2026-10-27.csv');
const mirrorPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-MIRROR-BUNDLE-RECOVERY-2026-10-28.csv');
const outputPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-MIRROR-FAMILY-NAME-TRIAGE-2026-10-28.csv');

const families = parseCsv(await readFile(familyPath, 'utf8'));
const mirrors = parseCsv(await readFile(mirrorPath, 'utf8'));
assert.equal(families.length, 86, 'active family registry changed; review before rebuilding name triage');
assert.equal(mirrors.length, 224, 'mirror bundle inventory changed; review before rebuilding name triage');

const normalize = value => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
const familyTokens = families.flatMap(family => [family.family_slug, family.family_name]
  .map(normalize)
  .filter(token => token.length >= 5)
  .map(token => ({ token, slug: family.family_slug, name: family.family_name })));

const rows = mirrors.map(mirror => {
  const repo = normalize(mirror.repo);
  const hits = familyTokens.filter(({ token }) => repo === token || repo.includes(token));
  const candidates = [...new Map(hits.map(hit => [hit.slug, hit])).values()];
  return {
    repo: mirror.repo,
    default_head_manifest: mirror.default_head_manifest,
    expected_parts: mirror.expected_parts,
    expected_bytes: mirror.expected_bytes,
    manifest_sha256_prefix: mirror.manifest_sha256_prefix,
    candidate_family_slugs: candidates.map(candidate => candidate.slug).join('|'),
    candidate_family_names: candidates.map(candidate => candidate.name).join('|'),
    candidate_count: candidates.length,
    match_rule: 'normalized repo slug equals or contains normalized canonical family slug/name (minimum token length 5)',
    payload_reviewed: mirror.semantic_payload_reviewed,
    bundle_extracted: mirror.bundle_extracted,
    triage_boundary: 'Name-only candidate screen. Zero matches do not rule out aliases, product code hidden inside a bundle, or family relevance; no payloads were extracted or rights-adjudicated.',
  };
});

await writeFile(outputPath, serializeCsv(rows, Object.keys(rows[0]), { quoteAll: true, lineEnding: '\n' }), 'utf8');
const matched = rows.filter(row => row.candidate_count > 0).length;
process.stdout.write(JSON.stringify({
  output: path.relative(root, outputPath).replaceAll(path.sep, '/'),
  activeFamilies: families.length,
  mirrorBundles: mirrors.length,
  candidateMatches: matched,
  payloadsReviewed: 0,
}, null, 2) + '\n');
