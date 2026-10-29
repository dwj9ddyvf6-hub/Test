import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const registryPath = 'apps/silicon-market-terminal/vendor-coverage.json';
const backlogPath = 'research/rea-teardowns/synthesis/VENDOR-IMPLEMENTATION-BACKLOG-2026-10-27.csv';
const familySemanticPath = 'research/rea-teardowns/synthesis/OPTIONSTRAT-PUBLIC-SEMANTIC-REQUIREMENTS-2026-10-27.json';
const scopedRequirementPath = 'research/rea-teardowns/synthesis/SCOPED-FAMILY-REQUIREMENTS-2026-10-27.csv';
const appPath = 'apps/silicon-market-terminal/app.js';
const outputPath = 'research/rea-teardowns/synthesis/FAMILY-REQUIREMENT-TRACEABILITY-2026-10-27.csv';

const registry = JSON.parse(await readFile(path.join(root, registryPath), 'utf8'));
const backlog = parseCsv(await readFile(path.join(root, backlogPath), 'utf8'));
const familySemanticRegister = JSON.parse(await readFile(path.join(root, familySemanticPath), 'utf8'));
const scopedRequirementRows = parseCsv(await readFile(path.join(root, scopedRequirementPath), 'utf8'));
const scopedRequirements = scopedRequirementRows.map(requirement => {
  const anchor = requirement.source_reference.match(/^(.+?)#L(\d+)$/);
  assert.ok(anchor, `${requirement.requirement_id} must have a line-anchored source reference`);
  const absolute = path.resolve(path.dirname(path.join(root, scopedRequirementPath)), anchor[1]);
  const relative = path.relative(root, absolute);
  assert.ok(relative && !relative.startsWith('..'), `${requirement.requirement_id} source must stay inside the repository`);
  return { ...requirement, source_path: relative.replaceAll(path.sep, '/'), source_line: Number(anchor[2]) };
});
const appSource = await readFile(path.join(root, appPath), 'utf8');
const pageMap = appSource.match(/const pages = \{([\s\S]*?)\};/);
assert.ok(pageMap, 'renderPage route table was not found');
const routeIds = new Set([...pageMap[1].matchAll(/(?:^|,)\s*([A-Za-z0-9_]+)\s*:/gm)].map(match => match[1]));

const laneMap = {
  options: { adapter: 'shared/options-research', routes: ['flow', 'gex', 'darkpool', 'optionlab', 'staticgex', 'bullflow'], status: 'PARTIAL_SHARED_SURFACE' },
  equity: { adapter: 'shared/equity-research', routes: ['screener', 'ticker', 'portfolio', 'confluence', 'finviz', 'stockrover', 'congress', 'insiders'], status: 'PARTIAL_SHARED_SURFACE' },
  charting: { adapter: 'shared/charting-research', routes: ['charts', 'strategy', 'alerts'], status: 'PARTIAL_SHARED_SURFACE' },
  automation: { adapter: 'shared/automation-research-no-execution', routes: ['strategy', 'watchlists', 'alerts'], status: 'PARTIAL_SHARED_SURFACE_NO_ORDER_PATH' },
  events: { adapter: 'shared/events-research', routes: ['calendar', 'news', 'congress', 'insiders', 'ticker'], status: 'PARTIAL_SHARED_SURFACE' },
  onchain: { adapter: 'none', routes: [], status: 'NOT_IMPLEMENTED' },
};

const candidateMap = {
  'leadr-labs-original': { adapter: 'candidate/leadr-confluence', route: 'confluence', note: 'research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md' },
  danelfin: { adapter: 'candidate/danelfin-portfolio', route: 'portfolio', note: 'research/rea-teardowns/danelfin/PORTFOLIO-LAB-IMPLEMENTATION.md' },
  spotgamma: { adapter: 'candidate/spotgamma-static-gex', route: 'staticgex', note: 'research/rea-teardowns/spotgamma/GEX-LAB-IMPLEMENTATION.md' },
  optionstrat: { adapter: 'candidate/optionstrat-payoff', route: 'optionlab', note: 'research/rea-teardowns/optionstrat/OPTIONSTRAT-LAB-IMPLEMENTATION.md' },
  bullflow: { adapter: 'candidate/bullflow-activity-profile', route: 'bullflow', note: 'research/rea-teardowns/bullflow/ACTIVITY-PROFILE-LAB-IMPLEMENTATION.md' },
  'finviz-screener': { adapter: 'candidate/finviz-filter-contract', route: 'finviz', note: 'research/rea-teardowns/finviz-screener/FINVIZ-LAB-IMPLEMENTATION.md' },
  'stock-rover': { adapter: 'candidate/stockrover-factor', route: 'stockrover', note: 'research/rea-teardowns/stockrover/STOCKROVER-FACTOR-LAB-IMPLEMENTATION.md' },
  'azrael-options': { adapter: 'candidate/azrael-public-map', route: 'azrael', note: 'research/rea-teardowns/azrael-1587/MAP-LAB-IMPLEMENTATION.md' },
};

for (const [lane, mapping] of Object.entries(laneMap)) {
  for (const route of mapping.routes) assert.ok(routeIds.has(route), `Unknown ${lane} route in traceability map: ${route}`);
}
for (const [slug, mapping] of Object.entries(candidateMap)) {
  assert.ok(routeIds.has(mapping.route), `Unknown candidate route for ${slug}: ${mapping.route}`);
  await readFile(path.join(root, mapping.note));
}

assert.equal(registry.targetFamilies, 86, 'active family denominator changed; review before regeneration');
assert.equal(registry.families.length, registry.targetFamilies);
assert.equal(backlog.length, registry.targetFamilies, 'implementation backlog does not cover every active family');
const backlogBySlug = new Map(backlog.map(row => [row.family_slug, row]));
assert.equal(backlogBySlug.size, backlog.length, 'duplicate family slug in implementation backlog');

const ignoredHeadings = new Set(['sources', 'captures']);
const classifySection = heading => {
  const value = heading.toLowerCase();
  if (/evidence|unknown|open item|limit|caveat|risk|conflict|correction|postmortem/.test(value)) return 'evidence-limit-or-unknown';
  if (/method|scor|algorithm|signal|indicator|strategy|formula|backtest|performance|track record|result/.test(value)) return 'method-or-empirical-claim';
  if (/data|fresh|latency|coverage|source|api|privacy|security|legal|access|license|terms|plan|pricing/.test(value)) return 'data-access-or-rights';
  if (/product|workflow|feature|surface|catalog|platform|mobile|desktop|identity|delivery|architecture/.test(value)) return 'product-or-workflow';
  return 'unclassified';
};
const tagEvidence = text => {
  const tags = [];
  if (/\bobserved\b/i.test(text)) tags.push('observed-marker');
  if (/source-static|vendor[- ]published|seller-published|marketing claim|advertis(?:e|es|ed|ing)|vendor claim/i.test(text)) tags.push('vendor-claim-marker');
  if (/\binferred\b|appears to|seems to|suggests that|likely\b/i.test(text)) tags.push('inference-marker');
  if (/unknown|not disclosed|not published|not available|not recoverable|unverified|not independently|not established|unavailable/i.test(text)) tags.push('unknown-or-limit-marker');
  return tags.length ? tags.join(';') : 'no-heuristic-marker';
};

const rows = [];
for (const family of registry.families) {
  const work = backlogBySlug.get(family.slug);
  assert.ok(work, `Missing backlog row for ${family.slug}`);
  assert.equal(work.lane, family.lane, `Lane mismatch for ${family.slug}`);
  assert.equal(work.research_status, family.research, `Research-state mismatch for ${family.slug}`);
  const reportPath = work.active_report;
  const report = await readFile(path.join(root, reportPath), 'utf8');
  const lines = report.split(/\r?\n/);
  const headings = [];
  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(/^(#{2,6})\s+(.+?)\s*#*\s*$/);
    if (match) headings.push({ level: match[1].length, title: match[2].trim(), index: i });
  }
  if (!headings.length) headings.push({ level: 1, title: 'REPORT BODY', index: 0 });
  const familyMap = laneMap[family.lane];
  assert.ok(familyMap, `No shared-surface mapping for lane ${family.lane}`);
  const candidate = candidateMap[family.slug];
  const adapter = candidate?.adapter || familyMap.adapter;
  const routes = candidate ? [candidate.route] : familyMap.routes;
  const implementationStatus = candidate ? 'PARTIAL_CANDIDATE' : familyMap.status;
  const note = candidate?.note || '';

  let sectionNumber = 0;
  let ignoredSubtreeLevel = null;
  for (let h = 0; h < headings.length; h++) {
    const current = headings[h];
    if (ignoredSubtreeLevel !== null) {
      if (current.level > ignoredSubtreeLevel) continue;
      ignoredSubtreeLevel = null;
    }
    if (ignoredHeadings.has(current.title.toLowerCase())) {
      ignoredSubtreeLevel = current.level;
      continue;
    }
    const next = headings[h + 1];
    const endIndex = next?.index ?? lines.length;
    const bodyText = lines.slice(current.index + 1, endIndex).join('\n').trim();
    if (next && next.level > current.level && bodyText.length === 0) continue;
    const sectionText = lines.slice(current.index, endIndex).join('\n');
    sectionNumber++;
    const publicSurfaceRequirements = familySemanticRegister.requirements.filter(requirement =>
      requirement.source_references.some(reference => reference.path === reportPath
        && reference.startLine <= endIndex
        && reference.endLine >= current.index + 1));
    const scopedSectionRequirements = scopedRequirements.filter(requirement => requirement.family_slug === family.slug
      && requirement.source_path === reportPath
      && requirement.source_line >= current.index + 1
      && requirement.source_line <= endIndex);
    const semanticRequirements = [
      ...publicSurfaceRequirements,
      ...scopedSectionRequirements.map(requirement => ({
        requirement_id: requirement.requirement_id,
        user_job: requirement.user_job,
        fixture_or_validation_reference: `${scopedRequirementPath}#${requirement.requirement_id}; ${requirement.mapping_state} mapping; no vendor-behavior fixture recorded`,
        validation_status: 'SCOPED_SCHEMA_AND_SOURCE_ANCHOR_VALIDATED; VENDOR_RUNTIME_NOT_TESTED',
      })),
    ];
    const reviewedRequirementStatement = semanticRequirements
      .map(requirement => `${requirement.requirement_id}: ${requirement.user_job}`)
      .join(' | ');
    rows.push({
      requirement_locator_id: `LOC-${family.slug}-${String(sectionNumber).padStart(2, '0')}`,
      family_slug: family.slug,
      vendor_family: family.name,
      lane: family.lane,
      research_status: family.research,
      report_path: reportPath,
      report_line_start: current.index + 1,
      report_line_end: endIndex,
      report_section: current.title,
      section_topic_heuristic: classifySection(current.title),
      evidence_marker_heuristic: tagEvidence(sectionText),
      section_sha256: createHash('sha256').update(sectionText, 'utf8').digest('hex'),
      requirement_statement: reviewedRequirementStatement || 'NOT EXTRACTED: inspect this source section and write a concise, testable user-job/behavior requirement.',
      semantic_review_status: semanticRequirements.length
        ? scopedSectionRequirements.length ? 'CURATED_MANUAL_REQUIREMENTS_LINKED' : 'CURATED_PUBLIC_SURFACE_REQUIREMENTS_LINKED'
        : 'NOT_REVIEWED_BY_GENERATOR',
      semantic_requirement_ids: semanticRequirements.map(requirement => requirement.requirement_id).join(';'),
      suggested_adapter_or_gap: adapter,
      current_route_ids: routes.join(';'),
      implementation_status: implementationStatus,
      implementation_note: note,
      fixture_or_validation: semanticRequirements.length
        ? semanticRequirements.map(requirement => `${requirement.requirement_id}: ${requirement.fixture_or_validation_reference} (${requirement.validation_status})`).join(' | ')
        : 'NOT_LINKED_IN_THIS_TRACEABILITY_PASS',
      next_action: semanticRequirements.length
        ? 'Review the remaining unidentified/private behavior and confirm whether other captured passes add requirements; retain every unknown and do not infer full vendor parity.'
        : 'Extract job, inputs, outputs, rules, settings, state transitions, failures, source class and evidence grade; then link implementation and deterministic fixture or document the gap.',
    });
  }
}

const uniqueFamilies = new Set(rows.map(row => row.family_slug));
assert.equal(uniqueFamilies.size, registry.targetFamilies, 'not every active family has a source-section locator');
const scopedRequirementIds = new Set(scopedRequirements.map(requirement => requirement.requirement_id));
const linkedScopedIds = rows.flatMap(row => row.semantic_requirement_ids ? row.semantic_requirement_ids.split(';') : [])
  .filter(requirementId => scopedRequirementIds.has(requirementId));
assert.equal(new Set(linkedScopedIds).size, scopedRequirementIds.size, 'every scoped requirement must link to exactly one report section');
assert.deepEqual([...new Set(linkedScopedIds)].sort(), [...scopedRequirementIds].sort(), 'every scoped requirement must be present in traceability');
const output = path.join(root, outputPath);
await writeFile(output, serializeCsv(rows), 'utf8');
const curatedRows = rows.filter(row => row.semantic_requirement_ids);
process.stdout.write(JSON.stringify({
  output: outputPath,
  activeFamilies: uniqueFamilies.size,
  reportSections: rows.length,
  candidateAdapters: [...new Set(rows.filter(row => row.implementation_status === 'PARTIAL_CANDIDATE').map(row => row.family_slug))].length,
  unimplementedFamilies: [...new Set(rows.filter(row => row.implementation_status === 'NOT_IMPLEMENTED').map(row => row.family_slug))].length,
  sourceSectionsWithCuratedRequirements: curatedRows.length,
  familiesWithCuratedRequirements: new Set(curatedRows.map(row => row.family_slug)).size,
  curatedRequirementLinks: rows.reduce((total, row) => total + (row.semantic_requirement_ids ? row.semantic_requirement_ids.split(';').length : 0), 0),
  scopedRequirementLinks: linkedScopedIds.length,
  uniqueCuratedFixtures: new Set(familySemanticRegister.requirements.flatMap(requirement => (requirement.fixture_or_validation_reference.match(/CAND-[A-Za-z0-9-]+/g) || []))).size,
}, null, 2) + '\n');
