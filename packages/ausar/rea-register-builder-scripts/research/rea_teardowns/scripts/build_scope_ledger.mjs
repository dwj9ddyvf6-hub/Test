import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const registryPath = path.join(root, 'apps', 'silicon-market-terminal', 'vendor-coverage.json');
const indexPath = path.join(root, 'research', 'rea_teardowns', 'INDEX.md');
const legacyIndexPath = path.join(root, 'research', 'rea-teardowns', 'TEARDOWN-INDEX.md');
const outputPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'ACTIVE-FAMILY-SCOPE-LEDGER-2026-10-27.csv');
const historicalCrosswalkPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'LEGACY-ACTIVE-PASS-CROSSWALK-2026-10-27.csv');
const normalizeLineEndings = value => value.replace(/\r\n?/g, '\n');

const registry = JSON.parse(await readFile(registryPath, 'utf8'));
const checkOnly = process.argv.includes('--check');
const index = await readFile(indexPath, 'utf8');
const legacyIndex = await readFile(legacyIndexPath, 'utf8');
const passLinks = [];
let activeSection = '';
for (const [offset, lineText] of index.split(/\r?\n/).entries()) {
  if (lineText.startsWith('## ')) activeSection = lineText.slice(3).trim();
  for (const match of lineText.matchAll(/\[([^\]]+)\]\(targets\/([^)#]+\.md)(?:#([^)]+))?\)/g)) {
    passLinks.push({ sequence: passLinks.length + 1, section: activeSection, label: match[1].trim(),
      report: `targets/${match[2]}`, anchor: match[3] || '', line: offset + 1 });
  }
}

const legacyPasses = [];
const postIndexAdditions = [];
let legacySection = '';
for (const [offset, line] of legacyIndex.split(/\r?\n/).entries()) {
  if (line.startsWith('## ')) legacySection = line.slice(3).trim();
  if (['Wave 1 (23)', 'Wave 2 (46)', 'Torn down before the sweep'].includes(legacySection)) {
    const match = line.match(/^(\d+)\.\s+(.+)$/);
    if (match) legacyPasses.push({ section: legacySection, number: Number(match[1]), label: match[2].trim(), line: offset + 1 });
  } else if (legacySection === 'Post-index additions') {
    const match = line.match(/^(\d+)\.\s+(.+?)\s+—\s+`([^`]+)`/);
    if (match) postIndexAdditions.push({ section: legacySection, number: Number(match[1]), label: match[2].trim(), report: match[3], line: offset + 1 });
  }
}

assert.equal(legacyPasses.filter(row => row.section === 'Wave 1 (23)').length, 23, 'legacy Wave 1 entry count changed');
assert.equal(legacyPasses.filter(row => row.section === 'Wave 2 (46)').length, 46, 'legacy Wave 2 entry count changed');
assert.equal(legacyPasses.filter(row => row.section === 'Torn down before the sweep').length, 25, 'legacy pre-sweep entry count changed');
assert.equal(legacyPasses.length, 94, 'legacy numbered pass total changed');
assert.equal(postIndexAdditions.length, 3, 'legacy post-index addition count changed');
const activeWave1 = passLinks.filter(row => row.section === 'Wave 1 (23)');
const activeWave2 = passLinks.filter(row => row.section === 'Wave 2 (52)');
const activePreSweep = passLinks.filter(row => row.section === 'Torn down before the sweep (25)');
assert.equal(activeWave1.length, 23, 'active Wave 1 count changed');
assert.equal(activeWave2.length, 52, 'active Wave 2 count changed');
assert.equal(activePreSweep.length, 25, 'active pre-sweep count changed');
assert.equal(passLinks.length, 100, 'active pass total changed');
const activeForLegacySection = new Map([
  ['Wave 1 (23)', activeWave1],
  ['Wave 2 (46)', activeWave2.slice(0, 46)],
  ['Torn down before the sweep', activePreSweep],
]);
const activePassForLegacy = new Map();
for (const legacyPass of legacyPasses) {
  const activePass = activeForLegacySection.get(legacyPass.section)?.[legacyPass.number - 1];
  assert.ok(activePass, `no active counterpart for historical ${legacyPass.section} entry ${legacyPass.number}`);
  activePassForLegacy.set(`${legacyPass.section}\0${legacyPass.number}`, activePass);
}
const activePassAdditions = activeWave2.slice(46);
assert.equal(activePassAdditions.length, 6, 'active additions since the legacy index changed');

const normalizeLabel = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const documentedLabelRefinements = new Set([
  'LuxAlgo (original pass)\u0000LuxAlgo (original toolkit-era pass)',
  'SpotGamma (original pass)\u0000SpotGamma (original model/levels pass)',
  'OptionStrat (original pass)\u0000OptionStrat (original builder/flow pass)',
  'Cheddar Flow (original pass)\u0000Cheddar Flow (original flow/alerts pass)',
  'GainzAlgo V2 Alpha (original pass)\u0000GainzAlgo V2 Alpha (original public-surface pass)',
  'TrendSpider (original pass)\u0000TrendSpider (original product/workflow pass)',
  'Trade Ideas (original pass)\u0000Trade Ideas / Holly AI (original product pass)',
  'TradingKit\u0000TradingKit (same-name product identities)',
  'FolioTend / Tensor (public surfaces)\u0000FolioTend / Tensor',
]);
const crosswalkRows = legacyPasses.map((legacyPass, index) => {
  const activePass = activePassForLegacy.get(`${legacyPass.section}\0${legacyPass.number}`);
  const familySlug = activePass.report.slice('targets/'.length, -'.md'.length);
  const refinementKey = `${legacyPass.label}\u0000${activePass.label}`;
  let mappingStatus;
  if (normalizeLabel(legacyPass.label) === normalizeLabel(activePass.label)) mappingStatus = 'LABEL_MATCH_AFTER_NORMALIZATION';
  else {
    assert.ok(documentedLabelRefinements.has(refinementKey), `unreviewed legacy/active label difference at pass ${index + 1}: ${legacyPass.label} → ${activePass.label}`);
    documentedLabelRefinements.delete(refinementKey);
    mappingStatus = 'DOCUMENTED_LABEL_REFINEMENT';
  }
  return {
    historical_entry_type: 'NUMBERED_PASS',
    historical_section: legacyPass.section,
    historical_entry_number: legacyPass.number,
    historical_label: legacyPass.label,
    historical_index_line: legacyPass.line,
    historical_report_path: '',
    active_pass_sequence: activePass.sequence,
    active_label: activePass.label,
    active_index_line: activePass.line,
    family_slug: familySlug,
    active_report_path: `research/rea_teardowns/${activePass.report}`,
    mapping_status: mappingStatus,
  };
});
assert.equal(documentedLabelRefinements.size, 0, 'a documented legacy/active label refinement was not used');
for (const addition of postIndexAdditions) {
  const historicalReport = path.posix.join('research/rea-teardowns', addition.report.replaceAll('\\', '/'));
  const historicalSlug = path.posix.basename(path.posix.dirname(addition.report));
  assert.ok(existsSync(path.join(root, ...historicalReport.split('/'))), `historical post-index report is missing: ${historicalReport}`);
  assert.ok(!registry.families.some(family => family.slug === historicalSlug), `post-index addition ${historicalSlug} is already in the active family registry`);
  crosswalkRows.push({
    historical_entry_type: 'POST_INDEX_ADDITION',
    historical_section: addition.section,
    historical_entry_number: addition.number,
    historical_label: addition.label,
    historical_index_line: addition.line,
    historical_report_path: historicalReport,
    active_pass_sequence: '',
    active_label: '',
    active_index_line: '',
    family_slug: '',
    active_report_path: '',
    mapping_status: 'NOT_IN_ACTIVE_100_PASS_SCOPE',
  });
}

for (const activePass of activePassAdditions) {
  const familySlug = activePass.report.slice('targets/'.length, -'.md'.length);
  crosswalkRows.push({
    historical_entry_type: 'ACTIVE_PASS_ADDITION',
    historical_section: '',
    historical_entry_number: '',
    historical_label: '',
    historical_index_line: '',
    historical_report_path: '',
    active_pass_sequence: activePass.sequence,
    active_label: activePass.label,
    active_index_line: activePass.line,
    family_slug: familySlug,
    active_report_path: `research/rea_teardowns/${activePass.report}`,
    mapping_status: 'ADDED_TO_ACTIVE_SCOPE',
  });
}

const byReport = new Map();
for (const pass of passLinks) {
  const rows = byReport.get(pass.report) || [];
  rows.push(pass);
  byReport.set(pass.report, rows);
}

assert.equal(registry.targetFamilies, registry.families.length, 'registry declared family total must match its rows');
assert.equal(passLinks.length, registry.requestedPasses, 'index target-link occurrences must match requested pass total');
assert.equal(byReport.size, registry.targetFamilies, 'unique index report links must match active family total');
assert.ok(registry.families.every(family => ['complete', 'bounded-complete', 'in-progress'].includes(family.research)), 'every active family needs an explicit research state');

const missingReports = [];
const unregisteredReports = [...byReport.keys()].filter(report => !registry.families.some(family => `targets/${family.slug}.md` === report));
const rows = registry.families.map(family => {
  const report = `targets/${family.slug}.md`;
  const occurrences = byReport.get(report) || [];
  const absoluteReport = path.join(root, 'research', 'rea_teardowns', report);
  const reportExists = existsSync(absoluteReport);
  if (!reportExists) missingReports.push(report);
  assert.ok(occurrences.length > 0, `active family ${family.slug} must appear in the pass index`);
  return {
    family_slug: family.slug,
    family_name: family.name,
    primary_lane: family.lane,
    research_status: family.research,
    pass_occurrences: occurrences.length,
    repeated_family: occurrences.length > 1,
    pass_references: occurrences.map(pass => `INDEX.md:${pass.line}${pass.anchor ? `#${pass.anchor}` : ''} [${pass.label}]`).join(' | '),
    active_report_path: `research/rea_teardowns/${report}`,
    active_report_exists: reportExists,
  };
});

assert.equal(missingReports.length, 0, `active report files missing: ${missingReports.join(', ')}`);
assert.equal(unregisteredReports.length, 0, `index reports absent from registry: ${unregisteredReports.join(', ')}`);
assert.equal(rows.reduce((sum, row) => sum + row.pass_occurrences, 0), registry.requestedPasses, 'family pass occurrences must reconcile to total passes');
const inProgressSlugs = rows.filter(row => row.research_status === 'in-progress').map(row => row.family_slug).sort();
assert.deepEqual(inProgressSlugs, [], 'bounded public/local review scope should have no unstarted or unfinished report rows');
const boundedCompleteSlugs = rows.filter(row => row.research_status === 'bounded-complete').map(row => row.family_slug).sort();
assert.deepEqual(boundedCompleteSlugs, [
  'deepseek-news-grid-scalper-v2',
  'guardian-ftmo-swing-free',
  'm-algo-eurusd-m1-core',
  'tradingkit',
  'zerith-macd-martingale-grid-v2.20',
], 'bounded-complete families must retain explicit source/runtime follow-up scope');
const repeatedCounts = rows.filter(row => row.repeated_family)
  .map(row => [row.family_slug, row.pass_occurrences]).sort(([a], [b]) => a.localeCompare(b));
assert.deepEqual(repeatedCounts, [
  ['altindex', 2], ['cheddar-flow', 2], ['danelfin', 3], ['finviz-screener', 2], ['gainzalgo', 2],
  ['luxalgo', 2], ['optionstrat', 2], ['saty-ecosystem', 2], ['spotgamma', 2], ['tickeron', 2],
  ['trade-ideas', 3], ['trendspider', 2],
], 'repeat-pass family counts changed; review the denominator crosswalk');

const headers = Object.keys(rows[0]);
const csv = serializeCsv(rows, headers);
const crosswalkCsv = serializeCsv(crosswalkRows, Object.keys(crosswalkRows[0]));
if (checkOnly) {
  assert.equal(normalizeLineEndings(await readFile(outputPath, 'utf8')), normalizeLineEndings(csv), 'generated active-family scope ledger is stale');
  assert.equal(normalizeLineEndings(await readFile(historicalCrosswalkPath, 'utf8')), normalizeLineEndings(crosswalkCsv), 'generated legacy-to-active crosswalk is stale');
} else {
  await writeFile(outputPath, csv, 'utf8');
  await writeFile(historicalCrosswalkPath, crosswalkCsv, 'utf8');
}

process.stdout.write(JSON.stringify({
  output: path.relative(root, outputPath).replaceAll(path.sep, '/'),
  mode: checkOnly ? 'check' : 'write',
  families: rows.length,
  passes: rows.reduce((sum, row) => sum + row.pass_occurrences, 0),
  completeFamilies: rows.filter(row => row.research_status === 'complete').length,
  boundedCompleteFamilies: rows.filter(row => row.research_status === 'bounded-complete').length,
  reviewedFamilies: rows.filter(row => row.research_status !== 'in-progress').length,
  inProgressFamilies: rows.filter(row => row.research_status === 'in-progress').length,
  repeatedFamilies: rows.filter(row => row.repeated_family).map(row => row.family_slug),
  repeatedPassesBeyondFirst: rows.reduce((sum, row) => sum + Math.max(0, row.pass_occurrences - 1), 0),
  legacySweepEntries: legacyPasses.filter(row => row.section.startsWith('Wave ')).length,
  legacyPreSweepEntries: legacyPasses.filter(row => row.section.startsWith('Torn down')).length,
  legacyActivePassCrosswalkRows: crosswalkRows.filter(row => row.historical_entry_type === 'NUMBERED_PASS').length,
  exactNormalizedLabelMatches: crosswalkRows.filter(row => row.mapping_status === 'LABEL_MATCH_AFTER_NORMALIZATION').length,
  documentedLabelRefinements: crosswalkRows.filter(row => row.mapping_status === 'DOCUMENTED_LABEL_REFINEMENT').length,
  activePassAdditionsSinceLegacyIndex: crosswalkRows.filter(row => row.mapping_status === 'ADDED_TO_ACTIVE_SCOPE').map(row => row.active_label),
  postIndexAdditionsOutsideActiveScope: crosswalkRows.filter(row => row.mapping_status === 'NOT_IN_ACTIVE_100_PASS_SCOPE').map(row => row.historical_label),
}, null, 2) + '\n');
