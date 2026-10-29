import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const inputPath = 'research/rea-teardowns/synthesis/FAMILY-SEMANTIC-EXTRACTIONS-2026-10-27.md';
const outputPath = 'research/rea-teardowns/synthesis/SCOPED-FAMILY-REQUIREMENTS-2026-10-27.csv';
const evidenceClasses = new Set(['PUBLIC_OBSERVATION', 'VENDOR_PUBLISHED', 'INFERENCE', 'UNKNOWN', 'CONFLICT']);
const mappingStates = new Set(['PARTIAL', 'GAP']);
const familySlugByIdPrefix = { ainvest: 'ainvest', alertsify: 'alertsify', algoalpha: 'algoalpha', algobars: 'algobars', 'algopoint-qalpha': 'algopoint-qalpha', arkham: 'arkham-intelligence', 'capitalise-ai': 'capitalise-ai', azrael: 'azrael-options', bullflow: 'bullflow', bybit: 'bybit-apk-grid-dca', 'citrini-citrindex': 'citrini-citrindex', 'chaikin-power-gauge': 'chaikin-power-gauge', coincodecap: 'coincodecap-signals', deepseek: 'deepseek-news-grid-scalper-v2', edgeful: 'edgeful', gainzalgo: 'gainzalgo', guardian: 'guardian-ftmo-swing-free', insiderfinance: 'insiderfinance', 'kobeissi-letter': 'kobeissi-letter', kavout: 'kavout', kucoin: 'kucoin-app-4.43.0', malgo: 'm-algo-eurusd-m1-core', nansen: 'nansen', 'stock-moe': 'stock-moe', stockrover: 'stock-rover', simplywallst: 'simply-wall-st', spotgamma: 'spotgamma', altindex: 'altindex', optionalpha: 'option-alpha', optionality: 'optionality-sinux', quantix: 'quantix', quantcharts: 'quantcharts', 'schwar-capital': 'schwar-capital', 'summit-iq': 'summit-iq', tickeron: 'tickeron', 'ticker-nerd': 'ticker-nerd', tipranks: 'tipranks', tradingkit: 'tradingkit', vectorvest: 'vectorvest', prospero: 'prospero-ai', wundertrading: 'wundertrading', zeiierman: 'zeiierman', zerith: 'zerith-macd-martingale-grid-v2.20' };
familySlugByIdPrefix.finviz = 'finviz-screener';
familySlugByIdPrefix['trade-ideas'] = 'trade-ideas';
familySlugByIdPrefix.danelfin = 'danelfin';
familySlugByIdPrefix.tradytics = 'tradytics';
familySlugByIdPrefix['market-chameleon'] = 'market-chameleon';
familySlugByIdPrefix['quant-data'] = 'quant-data';
familySlugByIdPrefix.chartprime = 'chartprime';
const headers = [
  'requirement_id', 'family_slug', 'requirement_title', 'user_job', 'inputs', 'outputs',
  'rules_and_states', 'evidence_class', 'evidence_statement', 'source_reference',
  'implementation_mapping', 'mapping_state', 'rights_boundary',
];

const markdown = await readFile(path.join(root, inputPath), 'utf8');
const headings = [...markdown.matchAll(/^### (FSEM-([a-z0-9-]+)-(\d{2})) — (.+)$/gm)];
assert.equal(headings.length, 735, `expected 735 scoped requirements, found ${headings.length}`);

const sourceCache = new Map();
const rows = await Promise.all(headings.map(async (heading, index) => {
  const nextRequirement = headings[index + 1]?.index ?? Number.POSITIVE_INFINITY;
  const nextSection = markdown.indexOf('\n## ', heading.index + heading[0].length);
  const end = Math.min(nextRequirement, nextSection < 0 ? markdown.length : nextSection);
  const block = markdown.slice(heading.index, end);
  const field = label => {
    const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const values = [...block.matchAll(new RegExp(`^- \\*\\*${escaped}:\\*\\*\\s+(.+)$`, 'gm'))];
    assert.equal(values.length, 1, `${heading[1]} must contain exactly one ${label} field`);
    return values[0][1].trim();
  };
  const evidence = field('Evidence');
  const sourceLink = evidence.match(/\[([^\]]+)\]\(([^)]+)\)/);
  assert.ok(sourceLink, `${heading[1]} must link to a report source`);
  const sourceReference = sourceLink[2];
  const [relativeSource, anchor] = sourceReference.split('#');
  assert.match(anchor || '', /^L\d+$/, `${heading[1]} source must have a #L line anchor`);
  assert.match(relativeSource, /^\.\.\/\.\.\/rea_teardowns\/targets\/[a-z0-9.-]+\.md$/, `${heading[1]} source must point to a REA target report`);
  const sourceAbsolute = path.resolve(path.dirname(path.join(root, inputPath)), relativeSource);
  const sourceRelativeToRoot = path.relative(root, sourceAbsolute);
  assert.ok(sourceRelativeToRoot && !sourceRelativeToRoot.startsWith('..'), `${heading[1]} source must stay inside the repository`);
  if (!sourceCache.has(sourceAbsolute)) sourceCache.set(sourceAbsolute, await readFile(sourceAbsolute, 'utf8'));
  const sourceLines = sourceCache.get(sourceAbsolute).split(/\r?\n/);
  const lineNumber = Number(anchor.slice(1));
  assert.ok(lineNumber > 0 && lineNumber <= sourceLines.length, `${heading[1]} source anchor ${anchor} is outside ${relativeSource}`);

  const evidenceClass = field('Evidence class').split(';').map(value => value.trim().replaceAll('`', ''));
  assert.ok(evidenceClass.length > 0 && evidenceClass.every(value => evidenceClasses.has(value)), `${heading[1]} has an unsupported evidence class`);
  const mappingState = field('Mapping state').replaceAll('`', '');
  assert.ok(mappingStates.has(mappingState), `${heading[1]} has an unsupported mapping state`);
  assert.ok(familySlugByIdPrefix[heading[2]], `${heading[1]} has an unmapped family prefix`);
  const row = {
    requirement_id: heading[1],
    family_slug: familySlugByIdPrefix[heading[2]],
    requirement_title: heading[4].trim(),
    user_job: field('User job'),
    inputs: field('Inputs'),
    outputs: field('Outputs'),
    rules_and_states: field('Rules and states'),
    evidence_class: evidenceClass.join('; '),
    evidence_statement: evidence.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1'),
    source_reference: sourceReference,
    implementation_mapping: field('Mapping').replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1 ($2)'),
    mapping_state: mappingState,
    rights_boundary: field('Rights boundary'),
  };
  for (const header of headers) assert.ok(row[header], `${heading[1]} has an empty ${header}`);
  assert.ok(row.implementation_mapping.length >= 10, `${heading[1]} needs an explicit implementation or gap mapping`);
  return row;
}));

const ids = rows.map(row => row.requirement_id);
assert.equal(new Set(ids).size, rows.length, 'requirement IDs must be unique');
const familyCounts = Object.fromEntries([...new Set(rows.map(row => row.family_slug))].sort().map(slug => [slug, rows.filter(row => row.family_slug === slug).length]));
assert.deepEqual(familyCounts, { ainvest: 6, alertsify: 24, algoalpha: 24, algobars: 15, 'algopoint-qalpha': 24, 'arkham-intelligence': 29, altindex: 25, 'azrael-options': 6, bullflow: 4, 'bybit-apk-grid-dca': 7, 'capitalise-ai': 14, 'chaikin-power-gauge': 20, chartprime: 26, 'citrini-citrindex': 13, 'coincodecap-signals': 24, danelfin: 2, 'deepseek-news-grid-scalper-v2': 8, edgeful: 5, 'finviz-screener': 25, gainzalgo: 24, 'guardian-ftmo-swing-free': 11, insiderfinance: 1, 'kobeissi-letter': 12, kavout: 24, 'market-chameleon': 1, 'kucoin-app-4.43.0': 9, 'm-algo-eurusd-m1-core': 8, nansen: 23, 'option-alpha': 14, 'optionality-sinux': 4, 'prospero-ai': 24, 'quant-data': 28, quantix: 15, quantcharts: 4, 'schwar-capital': 20, spotgamma: 1, 'simply-wall-st': 28, 'stock-moe': 4, 'stock-rover': 24, 'summit-iq': 24, tickeron: 25, 'ticker-nerd': 18, tipranks: 24, 'trade-ideas': 1, tradytics: 1, tradingkit: 10, vectorvest: 24, wundertrading: 13, zeiierman: 8, 'zerith-macd-martingale-grid-v2.20': 7 }, 'scoped-family coverage changed; review before regenerating');

const csv = serializeCsv(rows, headers);
const roundTrip = parseCsv(csv);
assert.equal(roundTrip.length, rows.length, 'CSV round-trip row count differs');
for (let index = 0; index < rows.length; index++) {
  for (const header of headers) assert.equal(roundTrip[index][header], rows[index][header], `${rows[index].requirement_id} CSV round-trip changed ${header}`);
}
await writeFile(path.join(root, outputPath), csv, 'utf8');
console.log(JSON.stringify({
  output: outputPath,
  rows: rows.length,
  families: familyCounts,
  sourceFilesVerified: sourceCache.size,
  mappingStates: Object.fromEntries([...mappingStates].map(state => [state, rows.filter(row => row.mapping_state === state).length])),
}, null, 2));
