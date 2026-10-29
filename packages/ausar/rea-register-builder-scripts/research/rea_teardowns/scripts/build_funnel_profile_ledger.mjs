import assert from 'node:assert/strict';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const registryPath = path.join(root, 'apps', 'silicon-market-terminal', 'vendor-coverage.json');
const profileDirectory = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'funnel');
const legacyCrosswalkPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'LEGACY-ACTIVE-PASS-CROSSWALK-2026-10-27.csv');
const outputPath = path.join(root, 'research', 'rea-teardowns', 'synthesis', 'HISTORICAL-FUNNEL-PROFILE-LEDGER-2026-10-27.csv');

const registry = JSON.parse(await readFile(registryPath, 'utf8'));
const legacyCrosswalk = parseCsv(await readFile(legacyCrosswalkPath, 'utf8'));
const volSignalsDisposition = legacyCrosswalk.find(row => row.historical_label === 'VolSignals' && row.mapping_status === 'NOT_IN_ACTIVE_94_PASS_SCOPE');
assert.ok(volSignalsDisposition?.historical_report_path, 'VolSignals needs a documented post-index disposition before mapping its profile');
assert.equal(registry.targetFamilies, 86, 'active target-family count changed; review the crosswalk before regeneration');
const normalizeSlug = value => value.toLowerCase().replace(/[^a-z0-9]/g, '');
const activeByNormalizedSlug = new Map();
for (const family of registry.families) {
  const key = normalizeSlug(family.slug);
  const candidates = activeByNormalizedSlug.get(key) || [];
  candidates.push(family.slug);
  activeByNormalizedSlug.set(key, candidates);
}

const files = (await readdir(profileDirectory)).filter(file => /^profiles-g[1-8]\.md$/.test(file)).sort((a, b) => Number(a.match(/g(\d+)/)[1]) - Number(b.match(/g(\d+)/)[1]));
assert.deepEqual(files, Array.from({ length: 8 }, (_, index) => `profiles-g${index + 1}.md`), 'historical profile group set changed');

const knownDuplicateAliases = new Map([
  ['tradeideas', 'trade-ideas'],
  ['trade-ideas', 'trade-ideas'],
]);
const curatedFamilyAliases = new Map([
  ['unusualwhales', { family: 'unusual-whales-original', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis and active report title both identify Unusual Whales.' }],
  ['optionality', { family: 'optionality-sinux', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis describes Optionality and the Sinux Signals dashboard; the active report title names Optionality / Sinux Signals.' }],
  ['chaikin', { family: 'chaikin-power-gauge', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis describes Chaikin Power Gauge; the active report title names Chaikin Power Gauge.' }],
  ['prospero', { family: 'prospero-ai', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis names Prospero.ai; the active report title names Prospero.ai.' }],
  ['intellectia', { family: 'intellectia-ai', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis names Intellectia and its AI research platform; the active report title names Intellectia AI.' }],
  ['saty-stack', { family: 'saty-ecosystem', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis lists Saty indicators; the active report title names the Saty Ecosystem.' }],
  ['algopoint', { family: 'algopoint-qalpha', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis identifies Qalpha as an AlgoPoint suite; the active report title names AlgoPoint / Qalpha.' }],
  ['leadrlabs', { family: 'leadr-labs-original', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile heading and active report title both identify Leadr Labs.' }],
  ['citrini', { family: 'citrini-citrindex', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis covers Citrini Research and the Citrindex; the active report title names both.' }],
  ['kobeissi', { family: 'kobeissi-letter', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis names The Kobeissi Letter; the active report title names The Kobeissi Letter.' }],
  ['coincodecap', { family: 'coincodecap-signals', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis describes CoinCodeCap signals; the active report title names CoinCodeCap Signals.' }],
  ['tjr', { family: 'tjr-indicators', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis describes TJR TradingView indicators; the active report title names TJR Trades Indicators.' }],
  ['capitalise', { family: 'capitalise-ai', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis and active report title both identify Capitalise.ai.' }],
  ['arkham', { family: 'arkham-intelligence', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis and active report title both identify Arkham Intelligence.' }],
  ['azrael-1587', { family: 'azrael-options', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis identifies The 15.87 Rule by Azrael; the active report title names The 15.87 Rule (Azraël Options).' }],
  ['correctionscope-ai', { family: 'correction-scope-ai-v1', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis and active report title both identify CorrectionScope AI v1.' }],
  ['apexquant', { family: 'apex-quant-ai', status: 'CURATED_FAMILY_ALIAS_MATCH_IDENTITY_UNRESOLVED', basis: 'The profile and report title share the Apex Quant name; the active report explicitly leaves exact target identity ambiguous.' }],
  ['schwar', { family: 'schwar-capital', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis and active report title both identify Schwar Capital Research.' }],
  ['zerith-macd-grid', { family: 'zerith-macd-martingale-grid-v2.20', status: 'CURATED_FAMILY_ALIAS_MATCH_PUBLIC_SOURCE_PINNED_LINK_RUNTIME_UNVERIFIED', basis: 'The exact-named public v2.20 source candidate is pinned and matches the local snapshot; the repository-to-roster/commercial-publisher relationship, compiled release, and runtime remain unverified.' }],
  ['ezalgo', { family: 'eztrades-manipulationx', status: 'CURATED_FAMILY_ALIAS_MATCH', basis: 'The profile synopsis describes EzAlgo and ManipulationX; the active report title names both products.' }],
  ['gridscalperea', { family: 'deepseek-news-grid-scalper-v2', status: 'CURATED_FAMILY_ALIAS_MATCH_SOURCE_PINNED_RUNTIME_UNVERIFIED', basis: 'The profile synopsis names DeepSeek News Grid Scalper V2; a matching public source file and v2.0.0 tag are pinned, but official publisher linkage and compiled/runtime build remain unverified.' }],
]);
const curatedAliasUsage = new Set();
const documentedOutOfScopeUsage = new Set();
const rows = [];
for (const file of files) {
  const group = `G${file.match(/g(\d+)/)[1]}`;
  const sourcePath = `research/rea-teardowns/synthesis/funnel/${file}`;
  const source = await readFile(path.join(profileDirectory, file), 'utf8');
  let groupSequence = 0;
  for (const [lineIndex, line] of source.split(/\r?\n/).entries()) {
    const heading = line.match(/^## ([a-z0-9][a-z0-9-]*)$/);
    if (!heading) continue;
    const slug = heading[1];
    groupSequence++;
    const candidates = activeByNormalizedSlug.get(normalizeSlug(slug)) || [];
    assert.ok(candidates.length <= 1, `profile ${slug} ambiguously matches active family slugs: ${candidates.join(', ')}`);
    const alias = curatedFamilyAliases.get(slug);
    const documentedOutOfScope = slug === 'volsignals' ? volSignalsDisposition : null;
    assert.ok(!(alias && candidates.length), `curated alias ${slug} is now also an exact normalized match`);
    assert.ok(!(documentedOutOfScope && (alias || candidates.length)), `documented out-of-scope profile ${slug} unexpectedly matches an active family`);
    if (alias) {
      assert.ok(registry.families.some(family => family.slug === alias.family), `curated alias ${slug} points to an unknown active family ${alias.family}`);
      curatedAliasUsage.add(slug);
    }
    if (documentedOutOfScope) documentedOutOfScopeUsage.add(slug);
    const activeFamilySlug = candidates[0] || alias?.family || '';
    const activeReportPath = activeFamilySlug ? `research/rea_teardowns/targets/${activeFamilySlug}.md` : '';
    let activeReportHeadingLine = '';
    if (activeReportPath) {
      const activeReport = await readFile(path.join(root, ...activeReportPath.split('/')), 'utf8');
      const headingLine = activeReport.split(/\r?\n/).findIndex(reportLine => /^# /.test(reportLine));
      assert.ok(headingLine >= 0, `active report heading missing for ${activeFamilySlug}`);
      activeReportHeadingLine = headingLine + 1;
    }
    rows.push({
      profile_id: `FUNNEL-${group}-${String(groupSequence).padStart(2, '0')}`,
      group_id: group,
      historical_profile_slug: slug,
      historical_vendor_key: knownDuplicateAliases.get(slug) || slug,
      source_path: sourcePath,
      source_heading_line: lineIndex + 1,
      active_family_slug: activeFamilySlug,
      active_report_path: activeReportPath,
      active_report_heading_line: activeReportHeadingLine,
      related_historical_report_path: documentedOutOfScope?.historical_report_path || '',
      mapping_status: candidates.length ? 'NORMALIZED_SLUG_MATCH' : alias?.status || (documentedOutOfScope ? 'DOCUMENTED_OUTSIDE_ACTIVE_SCOPE' : 'NO_NORMALIZED_SLUG_MATCH_REVIEW_REQUIRED'),
      mapping_basis: candidates.length ? 'slug equality after lowercase and punctuation removal' : alias?.basis || (documentedOutOfScope ? 'The legacy pass crosswalk explicitly lists VolSignals as a post-index addition outside the active 94-pass scope.' : 'no normalized slug match; alias versus scope disposition not determined'),
    });
  }
}

assert.equal(rows.length, 96, `historical profile heading count changed: ${rows.length}`);
const vendorsByKey = new Map();
for (const row of rows) {
  const matches = vendorsByKey.get(row.historical_vendor_key) || [];
  matches.push(row);
  vendorsByKey.set(row.historical_vendor_key, matches);
}
assert.equal(vendorsByKey.size, 95, `historical unique-vendor count changed: ${vendorsByKey.size}`);
const duplicateKeys = [...vendorsByKey].filter(([, matches]) => matches.length > 1);
assert.deepEqual(duplicateKeys.map(([key]) => key), ['trade-ideas'], 'the historical profile duplicate set changed');
assert.equal(duplicateKeys[0][1].length, 2, 'Trade Ideas should have two historical profile entries');
assert.deepEqual([...curatedAliasUsage].sort(), [...curatedFamilyAliases.keys()].sort(), 'a curated alias was not found in the historical profile sources');
assert.deepEqual([...documentedOutOfScopeUsage], ['volsignals'], 'the documented out-of-scope historical profile set changed');

const matchedRows = rows.filter(row => row.active_family_slug);
const matchedFamilies = new Set(matchedRows.map(row => row.active_family_slug));
const normalizedMatchRows = rows.filter(row => row.mapping_status === 'NORMALIZED_SLUG_MATCH');
const curatedAliasRows = rows.filter(row => row.mapping_status.startsWith('CURATED_FAMILY_ALIAS_MATCH'));
const unmatchedRows = rows.filter(row => row.mapping_status === 'NO_NORMALIZED_SLUG_MATCH_REVIEW_REQUIRED');
assert.equal(normalizedMatchRows.length, 60, `normalized active-family profile matches changed: ${normalizedMatchRows.length}`);
assert.equal(curatedAliasRows.length, 21, `curated family alias count changed: ${curatedAliasRows.length}`);
assert.equal(matchedRows.length, 81, `mapped profile count changed: ${matchedRows.length}`);
assert.equal(matchedFamilies.size, 80, `mapped active-family count changed: ${matchedFamilies.size}`);
assert.equal(unmatchedRows.length, 14, `unmatched profile count changed: ${unmatchedRows.length}`);
const activeFamiliesWithoutProfile = registry.families.filter(family => !matchedFamilies.has(family.slug)).map(family => family.slug).sort();
assert.equal(activeFamiliesWithoutProfile.length, 6, `active-family profile coverage changed: ${activeFamiliesWithoutProfile.length}`);

const headers = [
  'profile_id', 'group_id', 'historical_profile_slug', 'historical_vendor_key',
  'source_path', 'source_heading_line', 'active_family_slug', 'active_report_path', 'active_report_heading_line', 'related_historical_report_path', 'mapping_status', 'mapping_basis',
];
await writeFile(outputPath, serializeCsv(rows, headers), 'utf8');
console.log(JSON.stringify({
  output: path.relative(root, outputPath).replaceAll('\\', '/'),
  historicalProfiles: rows.length,
  historicalUniqueVendors: vendorsByKey.size,
  knownDuplicateProfiles: duplicateKeys[0][1].map(row => `${row.group_id}:${row.historical_profile_slug}`),
  normalizedMatchProfiles: normalizedMatchRows.length,
  curatedAliasProfiles: curatedAliasRows.length,
  mappedProfileRows: matchedRows.length,
  matchedActiveFamilies: matchedFamilies.size,
  unmatchedProfilesRequiringAliasOrScopeReview: unmatchedRows.length,
  documentedOutsideActiveScopeProfiles: [...documentedOutOfScopeUsage],
  activeFamilies: registry.targetFamilies,
  activeFamiliesWithoutProfileMatch: activeFamiliesWithoutProfile,
  requested92Roster: 'UNAVAILABLE_IN_REVIEWED_REPOSITORY',
}, null, 2));
