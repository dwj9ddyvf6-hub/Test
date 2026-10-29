import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawn, execFileSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const recoveryPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-VAULT-SHARD-RECOVERY-2026-10-28.csv');
const crosswalkPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-VAULT-FAMILY-CROSSWALK-2026-10-28.csv');
const indexPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS_FILE_INDEX.csv');
const outputPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'CORPUS-VAULT-STRUCTURE-INDEX-2026-10-28.csv');

const recoveryRows = parseCsv(await readFile(recoveryPath, 'utf8'));
const crosswalkRows = parseCsv(await readFile(crosswalkPath, 'utf8'));
const corpusRows = parseCsv(await readFile(indexPath, 'utf8'));
assert.equal(recoveryRows.length, 39, 'expected the verified 39-source recovery ledger');
assert.ok(recoveryRows.every(row => row.verification_status === 'VERIFIED_SOURCE_FROM_TRACKED_SHARDS'), 'source integrity ledger is not fully verified');

const crosswalk = new Map(crosswalkRows.map(row => [row.vault_label, row]));
const blobByPath = new Map(corpusRows.filter(row => row.path && row.git_blob_oid).map(row => [row.path, row.git_blob_oid]));
const stagedFiles = execFileSync('git', ['ls-files', '--stage', '-z'], {
  cwd: root,
  encoding: 'utf8',
  maxBuffer: 64 * 1024 * 1024,
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
});
for (const record of stagedFiles.split('\0').filter(Boolean)) {
  const tab = record.indexOf('\t');
  assert.ok(tab > 0, 'unexpected git ls-files --stage record');
  const [mode, oid, stage] = record.slice(0, tab).split(' ');
  const relativePath = record.slice(tab + 1).replaceAll('\\', '/');
  assert.equal(stage, '0', 'unmerged Git index entry: ' + relativePath);
  if (relativePath.startsWith('research/rea-teardowns/_vault/')) {
    assert.equal(blobByPath.get(relativePath), oid, 'corpus inventory blob ID drift: ' + relativePath);
  }
}

const partsBySource = recoveryRows.map(row => {
  const sourceSegments = row.source_path.split('/');
  const vaultLabel = sourceSegments[sourceSegments.indexOf('rea-teardowns') + 1];
  const family = crosswalk.get(vaultLabel);
  assert.ok(family, 'missing active-family crosswalk entry: ' + vaultLabel);
  const partCount = Number(row.expected_part_count);
  assert.ok(Number.isInteger(partCount) && partCount > 0, 'invalid shard count: ' + row.source_path);
  const prefix = row.tracked_shard_pattern.replace(/partNNN$/, 'part');
  const parts = Array.from({ length: partCount }, (_, index) => {
    const partPath = prefix + String(index + 1).padStart(3, '0');
    const oid = blobByPath.get(partPath);
    assert.ok(oid, 'shard missing from current corpus index: ' + partPath);
    return { path: partPath, oid };
  });
  return { row, family, parts };
});

const requests = partsBySource.flatMap(source => source.parts.map(part => part.oid));
const child = spawn('git', ['cat-file', '--batch'], {
  cwd: root,
  env: { ...process.env, GIT_NO_LAZY_FETCH: '1' },
  stdio: ['pipe', 'pipe', 'pipe'],
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
async function readObject(oid, partPath) {
  const header = await readLine();
  const match = header.match(/^([0-9a-f]{40,64}) (blob|missing)(?: (\d+))?$/);
  assert.ok(match, 'unexpected git cat-file header for ' + partPath);
  assert.equal(match[1], oid, 'Git object ID mismatch: ' + partPath);
  assert.equal(match[2], 'blob', 'Git object is not a blob: ' + partPath);
  const size = Number(match[3]);
  const chunks = [];
  let remaining = size;
  while (remaining > 0) {
    if (!pending.length) await appendOutput();
    const take = Math.min(remaining, pending.length);
    chunks.push(Buffer.from(pending.subarray(0, take)));
    pending = pending.subarray(take);
    remaining -= take;
  }
  while (!pending.length) await appendOutput();
  assert.equal(pending[0], 0x0a, 'git cat-file framing newline missing');
  pending = pending.subarray(1);
  return { size, chunks };
}

const headers = [
  'source_path', 'vault_label', 'active_family_slug', 'active_family_name', 'mapping_type',
  'bytes', 'sha256', 'integrity_status', 'parse_status', 'document_count', 'record_count', 'evidence_ids', 'subject_names',
  'valid_json_prefix_bytes', 'unparsed_fragment_bytes', 'unparsed_fragment_sha256',
  'provider_id', 'provider_name', 'provider_version', 'predicate_type', 'operation',
  'confidence', 'authority', 'raw_result_type', 'normalized_format',
  'summary_keys', 'numeric_summary_by_record_json', 'statistics_by_record_json', 'graph_node_count',
  'graph_edge_count', 'graph_node_kinds_json', 'semantic_node_count',
  'semantic_relation_count', 'semantic_unknown_count', 'semantic_fingerprint_count',
  'integrity_contradiction_count', 'limitation_count', 'evidence_link_count',
  'review_boundary',
];
const outputRows = [];
let totalBytes = 0;
function objectOrEmpty(value) { return value && typeof value === 'object' && !Array.isArray(value) ? value : {}; }
function visitJsonDocuments(text, visit) {
  let position = 0;
  let documentCount = 0;
  while (position < text.length) {
    while (/\s/.test(text[position] || '')) position++;
    if (position >= text.length) break;
    const start = position;
    const first = text[position];
    if (first !== '{' && first !== '[') return { documentCount, trailingStart: position };
    let depth = 0;
    let inString = false;
    let escaped = false;
    let end = -1;
    for (; position < text.length; position++) {
      const char = text[position];
      if (inString) {
        if (escaped) escaped = false;
        else if (char === '\\') escaped = true;
        else if (char === '"') inString = false;
        continue;
      }
      if (char === '"') inString = true;
      else if (char === '{' || char === '[') depth++;
      else if (char === '}' || char === ']') {
        depth--;
        if (depth === 0) { end = position + 1; break; }
        if (depth < 0) throw new Error(`unbalanced JSON container at character ${position}`);
      }
    }
    if (end < 0) throw new Error(`unterminated JSON container starting at character ${start}`);
    const value = JSON.parse(text.slice(start, end));
    const records = Array.isArray(value) ? value : [value];
    for (const record of records) visit(record);
    documentCount++;
    position = end;
  }
  return { documentCount, trailingStart: null };
}
function countKinds(values, key) {
  const counts = {};
  for (const value of Array.isArray(values) ? values : []) {
    const label = String(value?.[key] ?? 'unspecified');
    counts[label] = (counts[label] || 0) + 1;
  }
  return counts;
}
function flattenNumbers(value, prefix = '', out = {}) {
  if (!value || typeof value !== 'object') {
    if (typeof value === 'number' || typeof value === 'boolean') out[prefix || 'value'] = value;
    return out;
  }
  for (const [key, childValue] of Object.entries(value)) {
    const next = prefix ? `${prefix}.${key}` : key;
    if (childValue && typeof childValue === 'object') flattenNumbers(childValue, next, out);
    else if (typeof childValue === 'number' || typeof childValue === 'boolean') out[next] = childValue;
  }
  return out;
}

child.stdin.end(requests.join('\n') + '\n');
for (let i = 0; i < partsBySource.length; i++) {
  const source = partsBySource[i];
  const buffers = [];
  const hash = createHash('sha256');
  let bytes = 0;
  for (const part of source.parts) {
    const object = await readObject(part.oid, part.path);
    const gitObjectHash = createHash('sha1').update(Buffer.concat([
      Buffer.from(`blob ${object.size}\0`, 'utf8'),
      ...object.chunks,
    ])).digest('hex');
    assert.equal(gitObjectHash, part.oid, 'Git blob digest mismatch: ' + part.path);
    for (const chunk of object.chunks) {
      hash.update(chunk);
      buffers.push(chunk);
      bytes += chunk.length;
    }
  }
  const observedSha256 = hash.digest('hex');
  assert.equal(bytes, Number(source.row.expected_bytes), 'source byte count mismatch: ' + source.row.source_path);
  assert.equal(observedSha256, source.row.expected_sha256, 'source SHA-256 mismatch: ' + source.row.source_path);
  totalBytes += bytes;

  const raw = Buffer.concat(buffers, bytes);
  const aggregate = {
    recordCount: 0,
    evidenceIds: new Set(),
    subjects: new Set(),
    providerIds: new Set(),
    providerNames: new Set(),
    providerVersions: new Set(),
    predicates: new Set(),
    operations: new Set(),
    confidences: new Set(),
    authorities: new Set(),
    rawTypes: new Set(),
    formats: new Set(),
    summaryKeys: new Set(),
    numericSummaries: [],
    statistics: [],
    graphNodes: 0,
    graphEdges: 0,
    graphKinds: {},
    semanticNodes: 0,
    semanticRelations: 0,
    semanticUnknowns: 0,
    semanticFingerprints: 0,
    contradictions: 0,
    limitations: 0,
    evidenceLinks: 0,
  };
  const add = (set, value) => { if (value != null && String(value).length) set.add(String(value)); };
  let documentCount = 0;
  let validJsonPrefixBytes = bytes;
  let unparsedFragmentBytes = 0;
  let unparsedFragmentSha256 = '';
  let parseStatus = 'PARSED_JSON_STRUCTURE';
  try {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(raw);
    const documentScan = visitJsonDocuments(text, evidence => {
      const top = objectOrEmpty(evidence);
      const normalized = objectOrEmpty(top.normalized_result);
      const graph = objectOrEmpty(normalized.graph);
      const semantic = objectOrEmpty(normalized.semantic_graph);
      const summary = objectOrEmpty(normalized.summary);
      const statistics = objectOrEmpty(normalized.statistics);
      const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
      const edges = Array.isArray(graph.edges) ? graph.edges : [];
      const semanticNodes = Array.isArray(semantic.nodes) ? semantic.nodes : [];
      const relations = Array.isArray(semantic.relations) ? semantic.relations : [];
      const unknowns = Array.isArray(semantic.unknowns) ? semantic.unknowns : [];
      const fingerprints = Array.isArray(semantic.fingerprints) ? semantic.fingerprints : [];
      const contradictions = Array.isArray(normalized.integrity_contradictions) ? normalized.integrity_contradictions : [];
      aggregate.recordCount++;
      add(aggregate.evidenceIds, top.evidence_id);
      add(aggregate.subjects, objectOrEmpty(top.subject).name);
      add(aggregate.providerIds, objectOrEmpty(top.provider).id);
      add(aggregate.providerNames, objectOrEmpty(top.provider).name);
      add(aggregate.providerVersions, objectOrEmpty(top.provider).version);
      add(aggregate.predicates, top.predicate_type);
      add(aggregate.operations, top.operation);
      add(aggregate.confidences, top.confidence);
      add(aggregate.authorities, top.authority);
      add(aggregate.rawTypes, Array.isArray(top.raw_result) ? 'array' : typeof top.raw_result);
      add(aggregate.formats, normalized.format);
      for (const key of Object.keys(summary)) aggregate.summaryKeys.add(key);
      aggregate.numericSummaries.push(flattenNumbers(summary));
      aggregate.statistics.push(statistics);
      aggregate.graphNodes += nodes.length;
      aggregate.graphEdges += edges.length;
      for (const [kind, count] of Object.entries(countKinds(nodes, 'kind'))) aggregate.graphKinds[kind] = (aggregate.graphKinds[kind] || 0) + count;
      aggregate.semanticNodes += semanticNodes.length;
      aggregate.semanticRelations += relations.length;
      aggregate.semanticUnknowns += unknowns.length;
      aggregate.semanticFingerprints += fingerprints.length;
      aggregate.contradictions += contradictions.length;
      aggregate.limitations += (Array.isArray(top.limitations) ? top.limitations.length : 0) + (Array.isArray(normalized.limitations) ? normalized.limitations.length : 0);
      aggregate.evidenceLinks += Array.isArray(top.evidence_links) ? top.evidence_links.length : 0;
    });
    documentCount = documentScan.documentCount;
    if (documentScan.trailingStart != null) {
      const suffix = Buffer.from(text.slice(documentScan.trailingStart), 'utf8');
      validJsonPrefixBytes = Buffer.byteLength(text.slice(0, documentScan.trailingStart), 'utf8');
      unparsedFragmentBytes = suffix.length;
      unparsedFragmentSha256 = createHash('sha256').update(suffix).digest('hex');
      parseStatus = documentCount ? 'PARTIAL_VALID_JSON_PREFIX_TRAILING_FRAGMENT' : 'PARSE_FAILED_NO_JSON_DOCUMENT';
    }
    if (documentScan.trailingStart == null && documentCount > 1) {
      parseStatus = `PARSED_JSON_STRUCTURE_MULTIPLE_DOCUMENTS_${documentCount}`;
    }
  } catch (error) {
    parseStatus = `PARSE_FAILED: ${String(error.message || error).slice(0, 180)}`;
  }

  outputRows.push({
    source_path: source.row.source_path,
    vault_label: source.family.vault_label,
    active_family_slug: source.family.active_family_slug,
    active_family_name: source.family.active_family_name,
    mapping_type: source.family.mapping_type,
    bytes,
    sha256: observedSha256,
    integrity_status: 'VERIFIED_EXACT_GIT_BLOB_STREAM',
    parse_status: parseStatus,
    document_count: documentCount,
    record_count: aggregate.recordCount,
    evidence_ids: [...aggregate.evidenceIds].join('|'),
    subject_names: [...aggregate.subjects].join('|'),
    valid_json_prefix_bytes: validJsonPrefixBytes,
    unparsed_fragment_bytes: unparsedFragmentBytes,
    unparsed_fragment_sha256: unparsedFragmentSha256,
    provider_id: [...aggregate.providerIds].join('|'),
    provider_name: [...aggregate.providerNames].join('|'),
    provider_version: [...aggregate.providerVersions].join('|'),
    predicate_type: [...aggregate.predicates].join('|'),
    operation: [...aggregate.operations].join('|'),
    confidence: [...aggregate.confidences].join('|'),
    authority: [...aggregate.authorities].join('|'),
    raw_result_type: [...aggregate.rawTypes].join('|'),
    normalized_format: [...aggregate.formats].join('|'),
    summary_keys: [...aggregate.summaryKeys].join('|'),
    numeric_summary_by_record_json: JSON.stringify(aggregate.numericSummaries),
    statistics_by_record_json: JSON.stringify(aggregate.statistics),
    graph_node_count: aggregate.graphNodes,
    graph_edge_count: aggregate.graphEdges,
    graph_node_kinds_json: JSON.stringify(aggregate.graphKinds),
    semantic_node_count: aggregate.semanticNodes,
    semantic_relation_count: aggregate.semanticRelations,
    semantic_unknown_count: aggregate.semanticUnknowns,
    semantic_fingerprint_count: aggregate.semanticFingerprints,
    integrity_contradiction_count: aggregate.contradictions,
    limitation_count: aggregate.limitations,
    evidence_link_count: aggregate.evidenceLinks,
    review_boundary: 'JSON document boundaries and declared graph/statistics metadata parsed from exact verified Git blobs; any trailing fragment is separately hashed and left uninterpreted; graph claims, source rights, roster identity, and vendor parity not independently adjudicated.',
  });

  if ((i + 1) % 5 === 0 || i + 1 === partsBySource.length) {
    process.stdout.write(`parsed ${i + 1}/${partsBySource.length}: ${source.row.source_path} (${bytes} bytes; ${parseStatus})\n`);
  }
  buffers.length = 0;
  if (global.gc) global.gc();
}
const closeResult = await childClosed;
assert.equal(closeResult.code, 0, 'git cat-file failed: ' + (stderr || closeResult.signal || closeResult.code));
assert.equal(totalBytes, recoveryRows.reduce((sum, row) => sum + Number(row.expected_bytes), 0), 'total source bytes mismatch');
await writeFile(outputPath, serializeCsv(outputRows, headers, { quoteAll: true, lineEnding: '\n' }), 'utf8');
const fullyParsed = outputRows.filter(row => row.parse_status.startsWith('PARSED_JSON_STRUCTURE')).length;
const partial = outputRows.filter(row => row.parse_status === 'PARTIAL_VALID_JSON_PREFIX_TRAILING_FRAGMENT').length;
const failed = outputRows.length - fullyParsed - partial;
process.stdout.write(JSON.stringify({
  output: path.relative(root, outputPath).replaceAll(path.sep, '/'),
  verifiedSourceStreams: outputRows.filter(row => row.integrity_status === 'VERIFIED_EXACT_GIT_BLOB_STREAM').length,
  fullyParsedSourceStreams: fullyParsed,
  partialJsonSourceStreams: partial,
  failedSourceStreams: failed,
  sourceBytesRead: totalBytes,
  semanticAdjudication: 'NOT_PERFORMED',
}, null, 2) + '\n');
if (failed > 0) process.exitCode = 1;
