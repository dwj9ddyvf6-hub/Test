import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseCsv, serializeCsv } from './csv_utils.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..', '..');
const registryPath = 'apps/silicon-market-terminal/vendor-coverage.json';
const traceabilityPath = 'research/rea-teardowns/synthesis/FAMILY-REQUIREMENT-TRACEABILITY-2026-10-27.csv';
const appPath = 'apps/silicon-market-terminal/app.js';
const fixturePath = 'apps/silicon-market-terminal/candidate-calculation-fixtures.mjs';
const fixtureReportPath = 'research/rea-teardowns/synthesis/CANDIDATE-CALCULATION-FIXTURE-RESULTS-2026-10-27.json';
const outputPath = 'research/rea-teardowns/synthesis/CANDIDATE-REQUIREMENT-REGISTER-2026-10-27.csv';
const markdownPath = 'research/rea-teardowns/synthesis/CANDIDATE-REQUIREMENT-REGISTER-2026-10-27.md';

const registry = JSON.parse(await readFile(path.join(root, registryPath), 'utf8'));
const locatorRows = parseCsv(await readFile(path.join(root, traceabilityPath), 'utf8'));
const app = await readFile(path.join(root, appPath), 'utf8');
const fixtureSource = await readFile(path.join(root, fixturePath), 'utf8');
const fixtureReport = JSON.parse(await readFile(path.join(root, fixtureReportPath), 'utf8'));
const sha256 = value => createHash('sha256').update(value).digest('hex');
assert.equal(fixtureReport.status, 'PASS', 'candidate fixture report must pass');
assert.equal(fixtureReport.fixtureSha256, sha256(fixtureSource), 'candidate fixture report must match the current fixture source');
const fixtureReportMatchesCurrentSources = fixtureReport.appSha256 === sha256(app) && fixtureReport.fixtureSha256 === sha256(fixtureSource);
const pageMap = app.match(/const pages = \{([\s\S]*?)\};/);
assert.ok(pageMap, 'renderPage route table was not found');
const routes = new Set([...pageMap[1].matchAll(/(?:^|,)\s*([A-Za-z0-9_]+)\s*:/gm)].map(match => match[1]));
const familySlugs = new Set(registry.families.map(family => family.slug));
const locators = new Map(locatorRows.map(row => [row.requirement_locator_id, row]));

const requirements = [
  {
    requirementId: 'CAND-leadr-55-metadata', familySlug: 'leadr-labs-original', routeId: 'confluence',
    codeFunctions: ['renderConfluenceLab', 'computeConfluenceCandidate'],
    locators: ['LOC-leadr-labs-original-01', 'LOC-leadr-labs-original-02', 'LOC-leadr-labs-original-04'],
    userJob: 'Let an analyst enter evidence-backed normalized values for the public 55-field descriptive model, inspect coverage/category states, and see how the local candidate qualifies without mistaking it for Leadr output.',
    inputs: 'Manual 0–100 scores for the 55 named submetrics; an eligible flag; optional real-index count and data-confidence value; selected ticker. Values are held in local browser state.',
    outputs: 'Eight category scores/states, overall candidate score and grade, represented category weight, submetric coverage, confirming-category count, and an explicit qualification/blocker audit.',
    rules: 'Category requires at least 60% of its leaves; documented within-category weights form the category mean; available categories are reweighted over represented category weights. Category states: confirm ≥60, neutral 45–<60, conflict <45. Qualification: eligible flag, at least five confirming categories, rounded overall score ≥65, and confidence ≥70 when supplied. A supplied real-index count below four or confidence below 70 caps stronger grades at Mixed.',
    states: 'Missing leaves remain missing; a category below coverage is unavailable. Inputs are local and ticker-keyed. Missing confidence does not fail the observed public qualification predicate; this behavior is exposed as a caveat, not silently repaired.',
    evidence: 'Observed public-client metadata and threshold logic; the 55-field weighted-mean calculation is a Silicon analyst candidate, not a demonstrated Leadr scoring formula.',
    assumptions: 'Applying the client’s 60% leaf threshold to the descriptive 55-field table is a local design choice. No raw feature transform, data source, freshness or authenticated score is available.',
    limitations: 'Do not label as Leadr score or trading signal. Authenticated server model, production source transforms, alerts, entitlements, and full data lineage remain unknown.',
    note: 'research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md',
    validation: 'The source comparison records exact metadata-key/weight agreement; no automated candidate fixture is linked or executed in this register.',
  },
  {
    requirementId: 'CAND-leadr-v3-effective', familySlug: 'leadr-labs-original', routeId: 'confluence',
    codeFunctions: ['renderConfluenceEffectiveLab'],
    locators: ['LOC-leadr-labs-original-01', 'LOC-leadr-labs-original-02', 'LOC-leadr-labs-original-04'],
    userJob: 'Provide a separate, auditable manual candidate for the 17 statically mapped v3Effective leaves while keeping external market-context data visibly unavailable.',
    inputs: 'Manual normalized 0–100 values for the 17 leaves, with 14 ticker/sector fields and three framework-dependent market-context leaves; selected ticker.',
    outputs: 'Seven calculable ticker/sector category candidates, an unavailable market-context category, represented-category overall score, grade, coverage and decision blockers.',
    rules: 'Seven ticker/sector categories compute a weighted mean over present leaves and require ≥60% coverage. The context category uses the separate framework object and passed/evaluated ratio; Silicon does not fabricate that object. Overall score renormalizes the documented category weights over available categories; qualification follows visible client thresholds.',
    states: 'Absent leaves stay unavailable; the context category remains unavailable without the separate framework payload. Local manual inputs are not persisted to a server.',
    evidence: 'Observed static public-client mapping and aggregation. User-entered leaf normalization is a Silicon candidate choice.',
    assumptions: 'Raw transforms, source freshness, packed framework vector and server-produced scoring are not recovered.',
    limitations: 'Keep this path distinct from the 55-field metadata table and from authenticated Leadr scores; no vendor parity or predictive edge claim.',
    note: 'research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md',
    validation: 'Static source mapping is documented; no automated fixture or independent server-output comparison is linked or run.',
  },
  {
    requirementId: 'CAND-danelfin-sector-portfolio', familySlug: 'danelfin', routeId: 'portfolio',
    codeFunctions: ['parseDanelfinCsv', 'buildDanelfinPortfolio', 'shiftDanelfinCalendarDate', 'buildDanelfinRebalancePlan', 'renderDanelfinPortfolioLab'],
    locators: ['LOC-danelfin-01', 'LOC-danelfin-02', 'LOC-danelfin-03', 'LOC-danelfin-04', 'LOC-danelfin-09'],
    userJob: 'Construct an auditable sector portfolio and inspect dated membership-review and annual target-weight events from user-supplied point-in-time snapshots using the publicly described Best Stocks rules.',
    inputs: 'Local CSV: Ticker/Symbol, Score/AIScore (1–10), Sector, LowRisk/LowRiskScore (1–10), average 3-month share volume, optional ProvenBuySignal, AsOf, and SnapshotComplete/ExportComplete/UniverseExportComplete. Tickers may repeat across dates but not within a snapshot. Limit 10 MiB and 10,000 rows.',
    outputs: 'Eligible rows, top five eligible sectors by mean score, up to five names per selected sector, latest-snapshot equal-weight construction, dated additions/removals, quarterly membership-review states, annual equal-weight targets, and a row-level CSV decision audit.',
    rules: 'Require Low Risk ≥5 and average daily 3-month volume >100,000. Rank eligible sectors by arithmetic mean score, then sector name ascending. Within selected sectors, default to Proven Buy names in score-descending order, then fill remaining slots with the highest-scoring other eligible names; expose score-only ranking as a local override and ticker ascending as the deterministic name tie-break. Missing signal is unconfirmed. Quarterly and annual events are calendar-month anniversaries anchored to the declared start date; each event uses only the latest prior snapshot up to 7 days old, and an event is selectable only when all rows declare SnapshotComplete=true.',
    states: 'Mixed dated/undated rows, duplicate tickers within a snapshot, inconsistent completeness flags, and invalid/missing required columns fail import. Missing, stale, partial, or completeness-unknown snapshots suppress selection for that event. Filtered names, under-filled sectors, additions/removals, and unknown schedule events remain visible.',
    evidence: 'Publicly published Best Stocks construction and timing guidance. The AI Score itself is server-produced and not reconstructed. Sector/name tie ordering, calendar-month anchoring, the seven-day freshness threshold, and reliance on user-declared completeness are local deterministic choices.',
    assumptions: 'Avg3MVolume means average daily shares. Quarterly membership reviews are anchored to the user-selected start date, and annual rebalance rows report target equal weights only. Snapshot completeness is not independently verified.',
    limitations: 'No score generation, live data, verified full point-in-time universe, actual weight drift, historical return series, transaction costs, tax/corporate-action handling, trades, or return validation. Not a Danelfin replica or strategy claim.',
    note: 'research/rea-teardowns/danelfin/PORTFOLIO-LAB-IMPLEMENTATION.md',
    validation: 'Focused deterministic fixtures cover date anchoring/clipping, membership additions/removals, annual targets, exact seven-day freshness, stale/future snapshots, unknown completeness, multi-date parsing, duplicate rows, and inconsistent completeness. No vendor-output comparison or return validation is run.',
  },
  {
    requirementId: 'CAND-spotgamma-static-gex', familySlug: 'spotgamma', routeId: 'staticgex',
    codeFunctions: ['renderStaticGexLab'],
    locators: ['LOC-spotgamma-07', 'LOC-spotgamma-08', 'LOC-spotgamma-11'],
    userJob: 'Calculate a transparent, static prior-snapshot GEX view from a user-supplied option chain and inspect the contribution of each contract.',
    inputs: 'One ticker/date/spot snapshot with strike, call/put type, non-negative whole-number OI, IV in percent points and DTE ≥0.01 day; user-supplied risk-free rate, dividend yield, and multiplier (default 100).',
    outputs: 'Per-contract Black–Scholes gamma and signed 1%-GEX audit; strike aggregates; largest positive call wall and largest absolute put wall; nearest zero-crossing estimate from a 101-point spot grid, or none.',
    rules: 'For each row, Γ uses continuous-yield Black–Scholes with T=DTE/365; GEX = Γ×OI×multiplier×spot²×0.01×sign, with calls positive and puts negative. Grid repricing holds OI/IV/expiry/rate/yield fixed and linearly interpolates crossings.',
    states: 'Mixed ticker/date/spot, duplicate strike/type/DTE, invalid numeric ranges, zero-DTE and oversized files/rows are rejected; no-crossing returns none. Inputs stay in the browser tab.',
    evidence: 'Published static formula and sign convention. Applying OI as modeled-position magnitude and using Black–Scholes/grid details are explicit reconstruction choices.',
    assumptions: 'A signed-OI convention is not observed dealer inventory. Rates, dividends, surface, exercise style, timestamp and contract terms may differ from vendor methods.',
    limitations: 'No live feed, vendor API, dealer-position inventory, HIRO, TRACE, Synthetic OI or proprietary intraday walls; GEX is not a directional forecast.',
    note: 'research/rea-teardowns/spotgamma/GEX-LAB-IMPLEMENTATION.md',
    validation: 'Published method and reconstruction note are linked; no automated numeric fixture or external independent calculation is linked or run here.',
  },
  {
    requirementId: 'CAND-optionstrat-expiration-payoff', familySlug: 'optionstrat', routeId: 'optionlab',
    codeFunctions: ['renderOptionStrategyLab', 'buildOptionStrategyModel', 'buildOptionStrategySensitivity', 'blackScholesEuropean', 'crrAmericanOption'],
    locators: ['LOC-optionstrat-03', 'LOC-optionstrat-09'],
    userJob: 'Build a manual multi-leg option strategy and inspect its expiration payoff, breakevens, unbounded tails, and an independent European or American pricing scenario.',
    inputs: 'One underlying and one expiration; 1–8 call/put legs with long/short side, strike, entry premium, contracts, optional multiplier, and optional per-leg IV; scenario calendar DTE, shared IV, risk-free rate, continuous yield, exercise style, and 25–300 CRR steps.',
    outputs: 'Aggregate expiration P/L, exact extrema and breakeven regions, plus per-leg theoretical European Black–Scholes or American CRR values and model-vs-entry P/L; position-adjusted delta, gamma, vega, theta, and rho; a 3×5 deterministic P/L sensitivity matrix for spot and IV scenarios.',
    rules: 'Expiration payoff is signed intrinsic value less signed entry premium times contracts and multiplier. European Black–Scholes uses T=DTE/365 and manual annual inputs. The American CRR tree uses uniform time steps, a continuous yield, risk-neutral probability, and the greater of continuation or intrinsic value at each node; out-of-range probabilities are rejected. Per-leg IV overrides the shared IV. European Greeks are analytic; American Greeks are finite-difference approximations. Greeks use position sign and contract scaling; vega/rho are per percentage point and theta per calendar day. Sensitivity scenarios vary spot by −10/−5/0/+5/+10% and each selected leg IV by ×0.8/×1.0/×1.2 while holding other inputs fixed; the center cell must equal the base mark.',
    states: 'Leg count is bounded to eight; invalid payoff/model inputs, IV overrides, tree-step counts, and CRR probabilities are rejected. Output separates exact expiration payoff from the selected theoretical scenario mark and labels exercise, time, step, and volatility assumptions.',
    evidence: 'General expiration payoff identity, the Options Industry Council Black–Scholes method, and the independently published Cox–Ross–Rubinstein (1979) binomial method. No OptionStrat code, data, outputs, or expected values are used; no vendor parity claim is made.',
    assumptions: 'The European path assumes European exercise; the CRR path exercises at lattice nodes and approximates continuous exercise opportunities at the selected resolution. Both use annual percentage inputs, T=DTE/365, continuous yield, and shared flat IV unless a per-leg value is supplied. The fixed spot and volatility grid is illustrative and does not assign scenario probabilities.',
    limitations: 'No option chain or quote quality, discrete dividend schedule, implied-volatility solver, calibrated volatility surface, probability, optimizer, flow score, saved links, vendor pricing parity, or outcome validation.',
    note: 'research/rea-teardowns/optionstrat/OPTIONSTRAT-LAB-IMPLEMENTATION.md',
    validation: 'Focused fixtures check payoff boundaries, independent European price/parity/Greek conventions, independent American CRR one-step arithmetic and early exercise, finite-difference Greeks, position signs and scaling, per-leg IV override, shared-IV fallback, sensitivity center-cell equality and directional behavior for a long call, invalid IV, tree bounds, and invalid CRR probability. No vendor-output comparison is run.',
  },
  {
    requirementId: 'CAND-bullflow-activity-profile', familySlug: 'bullflow', routeId: 'bullflow',
    codeFunctions: ['renderBullflowActivityProfile'],
    locators: ['LOC-bullflow-04', 'LOC-bullflow-06'],
    userJob: 'Describe a ticker session against the prior 20 sessions and know whether the supplied source exports support complete-input profile results.',
    inputs: 'Local print rows with Date, TimeET, Ticker, contract fields, Side, TradeType, OpenInterest and explicit Cancelled values; optional raw Timestamp, source labels, TradeIDs and SideSource provenance; coverage-only rows with Available and ExportComplete declarations.',
    outputs: 'Same-time and full-session relative-volume measures, coverage and export-completeness diagnostics, side-label provenance counts, source-ID deduplication errors, activity flags, and per-flag known/unknown state.',
    rules: 'Use the latest 20 available dates before the selected session and compare at the same ET time. Ratios require all 20 baseline exports, the selected as-of export, and cancellation status to be declared complete. A zero is known only when the session is explicitly available and its export is declared complete. Side-derived output requires attributed labels. Call/put spikes require relative volume ≥2; buying surge additionally requires ≥70% ask/above-ask call share; unusual weekly activity requires expiry 0–7 days and volume/OI ≥2 with positive OI. Multi-leg prints are excluded from side-premium arithmetic; mid/unknown sides add zero.',
    states: 'Missing or unavailable dates are not zero. Partial/unknown exports and missing cancellation status suppress complete-input ratios; unknown side provenance suppresses side-derived output. Duplicate source IDs fail import. Missing prerequisites make flags UNKNOWN, not false. User completeness labels do not establish market-wide tape coverage.',
    evidence: 'Published public profile formulas, thresholds, historical trade IDs/timestamps, applied filters and cursor-completion fields; source labels, export completeness, cancellation status and side provenance come from the supplied file and are not independently verified.',
    assumptions: 'TimeET is treated as Eastern wall-clock time; optional raw API timestamps are retained and checked against that ET value when supplied. As-of calculations do not inspect future selected-session prints. ExportComplete describes a specific user-declared query window, not the vendor feed universe.',
    limitations: 'No live feed, source feed lineage, proprietary SigScore, hidden alert rule, entry/exit/size policy or tested profitability.',
    note: 'research/rea-teardowns/bullflow/ACTIVITY-PROFILE-LAB-IMPLEMENTATION.md',
    validation: 'Focused deterministic fixtures cover complete 20-session same-ET reproduction, known-zero versus unknown/partial sessions, cancellation handling, duplicate IDs, and unknown side provenance. No vendor-output comparison or point-in-time walk-forward validation is run.',
  },
  {
    requirementId: 'CAND-finviz-filter-subset', familySlug: 'finviz-screener', routeId: 'finviz',
    codeFunctions: ['renderFinvizContractLab'],
    locators: ['LOC-finviz-screener-02', 'LOC-finviz-screener-03', 'LOC-finviz-screener-10'],
    userJob: 'Apply a documented subset of Finviz filter-query behavior to a user-provided market snapshot while exposing unsupported tokens and ordering decisions.',
    inputs: 'Local one-row-per-ticker CSV with Ticker/Symbol and optional company/security/exchange/index/sector/industry/country/market-cap/valuation/price/volume/change/pattern tags; query tokens, sort key and optional ordered ticker list.',
    outputs: 'Filtered and sorted local rows, filter-key override count, explicit unsupported-token errors, and separate reporting of missing/filtered/ETF symbols for ordered ticker requests.',
    rules: 'Distinct supported filter keys combine with AND; repeated keys use the last value; supported subset includes exchange, exact sector/country/index, cap_largeover >$10B, and supplied pattern/candlestick tags. `o=` sorts ascending, `o=-` descending; `o=tickersfilter` preserves requested ticker order.',
    states: 'Unsupported filters are rejected; ticker matching is case-insensitive; absent security type prevents ETF identification rather than guessing; empty values sort last and ties retain input order.',
    evidence: 'Public query-contract behavior sampled from the teardown. Filter subset is explicitly incomplete; tag values are user data, not algorithmic pattern detection.',
    assumptions: 'All screening occurs on the supplied snapshot. Numeric normalization follows local parser conventions.',
    limitations: 'No full 82-filter taxonomy, live universe/data, paging, Elite custom filters, charting server, pattern detector or alpha claim.',
    note: 'research/rea-teardowns/finviz-screener/FINVIZ-LAB-IMPLEMENTATION.md',
    validation: 'A static scenario JSON exists for the candidate, but no automated fixture is linked or run in this register.',
  },
  {
    requirementId: 'CAND-stockrover-factor-profile', familySlug: 'stock-rover', routeId: 'stockrover',
    codeFunctions: ['renderStockRoverFactorLab'],
    locators: ['LOC-stock-rover-01', 'LOC-stock-rover-02', 'LOC-stock-rover-05', 'LOC-stock-rover-06'],
    userJob: 'Rank a single user-supplied cross-sectional stock snapshot using the public four-category factor input lists and a clearly labeled local combination rule.',
    inputs: 'Unique ticker, sector, shared YYYY-MM-DD decision date, and all 23 required Value/Growth/Quality/Sentiment metrics; numeric values must be finite, blank/NA stays missing.',
    outputs: 'Within-snapshot percentile per metric, four category means and a composite score only where every required metric/category input is present.',
    rules: 'Use midpoint ranks for ties; scale min/max observations to 0/100; invert EV/EBITDA, P/E, price/tangible-book, price/sales, debt/equity, short-interest ratio and days-since-52-week-high. Price/tangible-book and price/sales rank within sector; other metrics rank across the supplied universe. Equal-weight metrics within categories and four categories equally.',
    states: 'Reject duplicate tickers, mixed dates, missing required headers and non-finite values. No forward-fill, imputation or missing-to-zero; incomplete categories/composite remain unavailable.',
    evidence: 'Published factor lists are source-static. Percentile normalization and equal weights are explicit desk reconstruction choices, not Stock Rover formula disclosure.',
    assumptions: 'R1 EPS-predictability proxy and R2/R3 returns/normalized MACD are user-supplied; AsOf is a declared date, not verified publication time or point-in-time data proof.',
    limitations: 'No vendor score normalization, DCF, Piotroski, Altman, margin-of-safety, warnings, licensed financial data, or historical performance validation.',
    note: 'research/rea-teardowns/stockrover/STOCKROVER-FACTOR-LAB-IMPLEMENTATION.md',
    validation: 'SPEC and synthetic example document input semantics; no automated fixture is linked or run in this register.',
  },
  {
    requirementId: 'CAND-azrael-public-1587-map', familySlug: 'azrael-options', routeId: 'azrael',
    codeFunctions: ['renderAzraelMapLab'],
    locators: ['LOC-azrael-options-02', 'LOC-azrael-options-03', 'LOC-azrael-options-04', 'LOC-azrael-options-07'],
    userJob: 'Calculate a local public 15.87 expected-move map from user-entered prior-session values and compare a candidate target with the displayed range.',
    inputs: 'Prior-session anchor close and VIX close; elapsed minutes since 09:30, total session minutes, optional target in anchor-price units.',
    outputs: 'Expected-move percentage/points, half/full range levels, CALM/MIXED/FAST prior-VIX regime, square-root funded-range estimate, weekly context, and target-region classification.',
    rules: 'pct=VIX/15.87; round daily move to one decimal before constructing ±0.5 and ±1.0 levels. CALM <15; MIXED 15–18.5 inclusive; FAST >18.5. Funded range = rounded daily move × sqrt(elapsed/session); weekly context = rounded daily move × sqrt(5).',
    states: 'Manual inputs only; optional target can be absent. The target label is descriptive, and no target probability is computed. Invalid numerical or time inputs must remain visible as calculation blockers.',
    evidence: 'Published formula/examples and a dated public ledger; the map implementation matches the documented example. VIX scaling convention is not a calibrated intraday probability.',
    assumptions: 'Trading-session square-root scaling, one-decimal rounding order and regime boundaries are local candidate semantics documented by the implementation note.',
    limitations: 'No live feed, private OI shortlist, three-ticker opening-range lifecycle, contract sizing, options-flow checks, member desk, paid workbook, fill model or validated edge.',
    note: 'research/rea-teardowns/azrael-1587/MAP-LAB-IMPLEMENTATION.md',
    validation: 'Implementation note and WORKED-EXAMPLES.md contain manual arithmetic references; no automated fixture is linked or run in this register.',
  },
];

assert.equal(requirements.length, 9, 'curated candidate requirement count changed; review before regeneration');
assert.deepEqual([...new Set(requirements.map(row => row.familySlug))].sort(), [
  'azrael-options', 'bullflow', 'danelfin', 'finviz-screener', 'leadr-labs-original', 'optionstrat', 'spotgamma', 'stock-rover',
].sort(), 'candidate family set changed; review the curated scope');
const supplementalCaseIds = [
  'CAND-bullflow-canceled-print-exclusion',
  'CAND-bullflow-provenance-and-export-completeness',
  'CAND-danelfin-point-in-time-rebalance-plan',
  'CAND-optionstrat-independent-european-model',
  'CAND-optionstrat-independent-american-crr-model',
  'CAND-optionstrat-zero-payoff-regions',
  'EVIDENCE-ainvest-products-stay-distinct',
  'EVIDENCE-option-strategy-contract-lineage',
  'EVIDENCE-stock-moe-offers-stay-separate',
  'EVIDENCE-bullflow-boundary-display',
];
for (const item of requirements) {
  assert.ok(familySlugs.has(item.familySlug), `Unknown family: ${item.familySlug}`);
  assert.ok(routes.has(item.routeId), `Unknown route: ${item.routeId}`);
  for (const locatorId of item.locators) {
    assert.equal(locators.get(locatorId)?.family_slug, item.familySlug, `Invalid source locator ${locatorId}`);
  }
  for (const fn of item.codeFunctions) assert.match(app, new RegExp(`function\\s+${fn}\\s*\\(`), `Missing code function: ${fn}`);
  await readFile(path.join(root, item.note));
}
const expectedFixtureCaseIds = [...requirements.map(row => row.requirementId), ...supplementalCaseIds].sort();
assert.deepEqual([...fixtureReport.passedCandidateCases].sort(), expectedFixtureCaseIds, 'fixture report must cover every curated candidate requirement and declared supplement exactly once');
assert.equal(fixtureReport.candidateCaseCount, expectedFixtureCaseIds.length, 'fixture report case count does not match core requirements plus declared supplements');

const rows = requirements.map(item => ({
  requirement_id: item.requirementId,
  family_slug: item.familySlug,
  requirement_scope: 'BOUNDED_PARTIAL_CANDIDATE',
  report_locator_ids: item.locators.join(';'),
  implementation_note: item.note,
  code_path: 'apps/silicon-market-terminal/app.js',
  code_functions: item.codeFunctions.join(';'),
  route_id: item.routeId,
  user_job: item.userJob,
  inputs: item.inputs,
  outputs: item.outputs,
  rules_and_settings: item.rules,
  states_and_failure_modes: item.states,
  evidence_grade_and_class: item.evidence,
  reconstruction_choices: item.assumptions,
  known_gaps_and_nonclaims: item.limitations,
  fixture_or_validation_reference: `${item.validation.replace(/\s*;?\s*no automated.*$/i, '').replace(/\.$/, '')}; executable case \`${item.requirementId}\` in \`${fixturePath}\`; hash-bound result in \`${fixtureReportPath}\`.`,
  fixture_validation_status: fixtureReportMatchesCurrentSources ? 'PASS_CURRENT_APP_AND_FIXTURE_SHA256_MATCH' : 'STALE_APP_SOURCE_HASH_REQUIRES_FIXTURE_REPLAY',
  full_vendor_recreation: false,
}));

await writeFile(path.join(root, outputPath), serializeCsv(rows), 'utf8');
const markdown = [
  '# Curated candidate requirement register',
  '',
  '**As of:** 2026-10-27',
  '**Scope:** nine manually curated requirement records across the eight bounded terminal candidate families.',
  '',
  `This register links each requirement to its active route, implementation function, candidate note, and report-section locator. The detailed machine-readable records are in [the CSV register](CANDIDATE-REQUIREMENT-REGISTER-2026-10-27.csv). The separate [OptionStrat public-surface register](OPTIONSTRAT-PUBLIC-SEMANTIC-REQUIREMENTS-2026-10-27.json) maps its wider available capture, and the [unified index](UNIFIED-REQUIREMENT-INDEX-2026-10-27.csv) combines both with scoped evidence records. These Silicon candidate behaviors do not assert vendor parity.`,
  '',
  `**Coverage:** ${rows.length} requirements; ${new Set(rows.map(row => row.family_slug)).size} candidate families; ${new Set(rows.map(row => row.route_id)).size} routes; ${new Set(rows.flatMap(row => row.report_locator_ids.split(';'))).size} source-section locators. **Core candidate fixture coverage:** ${rows.length}/${rows.length} pass; **total fixture cases:** ${fixtureReport.candidateCaseCount} (${supplementalCaseIds.length} declared supplements); **boundary assertions:** ${fixtureReport.boundaryAssertionCount}; **full vendor recreations:** 0.`,
  '',
  `Latest local fixture report: [${fixtureReportPath}](../../../${fixtureReportPath}) · app SHA-256 \`${fixtureReport.appSha256}\`.`,
  '',
  '## Requirements',
  '',
];
for (const row of rows) {
  const list = (value) => value.split(';').map(item => `\`${item}\``).join(', ');
  markdown.push(
    `### ${row.requirement_id} — ${row.family_slug}`,
    '',
    `- **Surface:** route \`${row.route_id}\`; ${list(row.code_functions)} in [${row.code_path}](../../../${row.code_path}); [implementation note](../../../${row.implementation_note}).`,
    `- **Source locators:** ${list(row.report_locator_ids)}.`,
    `- **User job:** ${row.user_job}`,
    `- **Inputs:** ${row.inputs}`,
    `- **Outputs:** ${row.outputs}`,
    `- **Rules and states:** ${row.rules_and_settings} ${row.states_and_failure_modes}`,
    `- **Evidence class:** ${row.evidence_grade_and_class}`,
    `- **Reconstruction choices:** ${row.reconstruction_choices}`,
    `- **Known gaps and non-claims:** ${row.known_gaps_and_nonclaims}`,
    `- **Validation:** ${row.fixture_or_validation_reference} Status: \`${row.fixture_validation_status}\`.`,
    `- **Full vendor recreation:** \`${row.full_vendor_recreation}\`.`,
    '',
  );
}
markdown.push(
  '## Acceptance gaps',
  '',
  '- This curated extraction covers only the declared candidate slices. The separate OptionStrat register maps the available public capture but does not complete product-level semantics across all 86 families.',
  '- Most section-locator rows remain heuristic navigation; ten OptionStrat report sections now link to curated requirements. Neither those links nor source hashes independently verify vendor claims.',
  `- The nine core fixtures cover one deterministic calculation path per curated requirement; ${supplementalCaseIds.length} additional cases cover selected semantic and evidence boundaries. All ${fixtureReport.boundaryAssertionCount} boundary assertions are deterministic, but they do not exhaust input domains, prove independent vendor parity, or validate predictive performance.`,
  '- Full product parity, live-data lineage, rights review of every input, and prospective performance evidence remain open where identified in each record.',
  '- Do not use candidate scores or maps as vendor outputs or validated trading signals.',
  '',
  '## Regeneration',
  '',
  'Run `node apps/silicon-market-terminal/candidate-calculation-fixtures.mjs` after changing candidate calculation code. Then run `node research/rea_teardowns/scripts/build_candidate_requirement_register.mjs` after changing an implementation route/function, candidate note, active-family registry, source locator, or fixture report. The register generator checks the fixture-source hash and marks app-source hash drift stale until the fixture runner is rerun; it does not itself execute calculations.',
  '',
);
await writeFile(path.join(root, markdownPath), markdown.join('\n'), 'utf8');
process.stdout.write(JSON.stringify({
  output: outputPath,
  markdown: markdownPath,
  curatedRequirements: rows.length,
  candidateFamilies: new Set(rows.map(row => row.family_slug)).size,
  routesChecked: [...new Set(rows.map(row => row.route_id))].length,
  sourceLocatorsChecked: new Set(rows.flatMap(row => row.report_locator_ids.split(';'))).size,
  automatedFixturesLinked: fixtureReport.candidateCaseCount,
  boundaryAssertions: fixtureReport.boundaryAssertionCount,
  fixtureReportMatchesCurrentSources: fixtureReport.appSha256 === sha256(app) && fixtureReport.fixtureSha256 === sha256(fixtureSource),
  fullVendorReplicas: 0,
}, null, 2) + '\n');
