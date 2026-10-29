import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import {
  FAMILY_CROSSWALK,
  MAX_EVIDENCE_CSV_BYTES,
  MAX_EVIDENCE_CSV_ROWS,
  SURVIVOR_CATALOG,
  parseEvidenceCsv,
} from '../dist/convergence-engine.mjs';

test('20 survivors map the complete active corpus exactly once', async () => {
  assert.equal(SURVIVOR_CATALOG.length, 20);
  assert.equal(FAMILY_CROSSWALK.length, 86);
  assert.equal(new Set(FAMILY_CROSSWALK.map((family) => family.slug)).size, 86);
  assert.equal(FAMILY_CROSSWALK.reduce((sum, family) => sum + family.passes, 0), 100);
  assert.equal(FAMILY_CROSSWALK.filter((family) => family.status === 'complete').length, 81);
  assert.equal(FAMILY_CROSSWALK.filter((family) => family.status === 'bounded-complete').length, 5);
  assert.ok(SURVIVOR_CATALOG.every((survivor) => survivor.status === 'OPERATIONAL WITH SCOPE'));
  assert.ok(FAMILY_CROSSWALK.every((family) => family.survivor_id && family.report_path && family.report_url && family.kernel.length >= 70));

  const app = await readFile(new URL('../dist/app.js', import.meta.url), 'utf8');
  const start = app.indexOf('const pages = {');
  const end = app.indexOf('};', start);
  assert.ok(start >= 0 && end > start, 'app route registry exists');
  const registry = app.slice(start, end);
  assert.ok(registry.includes('convergence: renderConvergenceEngine'));
  assert.ok(SURVIVOR_CATALOG.every((survivor) => survivor.route.every((route) => registry.includes(route + ':'))));
});

test('CSV contract preserves quoted values and separate provenance clocks', () => {
  const csv = 'ObservedAt,Entity,Source,Metric,Value,PublicAt,ReceivedAt,EventType,SourceURL\r\n'
    + '2026-10-27T13:00:00Z,ACME,filing,headline,\"Revenue, \"\"beat\"\"\",2026-10-27T12:55:00Z,2026-10-27T13:01:00Z,earnings,https://example.com/filing\r\n';
  const result = parseEvidenceCsv(csv);
  assert.equal(result.acceptedCount, 1);
  assert.equal(result.rejectedCount, 0);
  assert.equal(result.records[0].Value, 'Revenue, \"beat\"');
  assert.equal(result.records[0].PublicAt, '2026-10-27T12:55:00Z');
  assert.equal(result.records[0].ReceivedAt, '2026-10-27T13:01:00Z');
  assert.equal(result.records[0].EventType, 'earnings');
});

test('invalid rows are reported without filling missing values', () => {
  const csv = 'ObservedAt,Entity,Source,Metric,Value,PublicAt,SourceURL\n'
    + 'not-a-date,ACME,feed,score,0,,\n'
    + '2026-10-27,ACME,feed,score,,,\n'
    + '2026-10-27,ACME,feed,score,3,not-a-date,\n'
    + '2026-10-27,ACME,feed,score,4,,javascript:alert(1)\n';
  const result = parseEvidenceCsv(csv);
  assert.equal(result.acceptedCount, 0);
  assert.equal(result.rejectedCount, 4);
  assert.match(result.rejected[0].reason, /ObservedAt/);
  assert.match(result.rejected[1].reason, /Value is required/);
  assert.match(result.rejected[2].reason, /PublicAt/);
  assert.match(result.rejected[3].reason, /HTTP or HTTPS/);
});

test('headers, malformed quoting, byte limits and row limits fail closed', () => {
  assert.throws(() => parseEvidenceCsv('ObservedAt,Entity,Source,Metric\n'), /missing required columns/);
  assert.throws(() => parseEvidenceCsv('ObservedAt,Entity,Source,Metric,Value,Value\n'), /duplicate column/);
  assert.throws(() => parseEvidenceCsv('ObservedAt,Entity,Source,Metric,Value\n2026-10-27,ACME,feed,metric,\"unfinished'), /quoted field/);
  assert.throws(() => parseEvidenceCsv('x'.repeat(MAX_EVIDENCE_CSV_BYTES + 1)), /10 MiB/);
  const header = 'ObservedAt,Entity,Source,Metric,Value\n';
  const row = '2026-10-27,ACME,feed,score,1\n';
  assert.ok(MAX_EVIDENCE_CSV_ROWS > 0);
  assert.throws(() => parseEvidenceCsv(header + row.repeat(MAX_EVIDENCE_CSV_ROWS + 1)), /50,000-row/);
});
