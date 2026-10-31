import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const appPath = path.join(here, 'app.js');
const resultPath = path.resolve(here, '..', '..', 'research', 'rea-teardowns', 'synthesis', 'CANDIDATE-CALCULATION-FIXTURE-RESULTS-2026-10-27.json');
const appSource = await readFile(appPath, 'utf8');
const rootElement = { innerHTML: '' };
const document = {
  getElementById: id => id === 'app' ? rootElement : null,
  addEventListener() {},
  querySelector() { return null; },
  querySelectorAll() { return []; },
  documentElement: { dataset: {} },
};
const context = {
  document,
  localStorage: { getItem() { return null; }, setItem() {} },
  window: { addEventListener() {} },
  location: { hash: '' },
  history: { pushState() {} },
  fetch: async () => ({ ok: true, json: async () => ({ families: [], requestedPasses: 100, targetFamilies: 86, asOf: '2026-10-28' }) }),
  console, Intl, Date, Math, Number, String, Array, Object, Map, Set, JSON, RegExp, Error, FormData: class {},
};
const exports = [
  'buildAzraelMap', 'buildStaticGexSnapshot', 'optionStrategyPnlAt', 'optionStrategyStats', 'standardNormalCdf', 'blackScholesEuropean', 'crrAmericanOption', 'buildOptionStrategyModel', 'buildOptionStrategySensitivity', 'parseOptionStrategyLegs', 'calculateStockRoverFactorScores',
  'calculateFinvizContract', 'parseFinvizSnapshotCsv', 'parseDanelfinCsv', 'parseStaticGexCsv',
  'parseOptionStrategyLegs', 'parseStockRoverFactorCsv', 'calculateBullflowActivityProfile', 'parseBullflowActivityCsv',
  'computeConfluenceCandidate', 'computeConfluenceEffectiveCandidate', 'buildDanelfinPortfolio', 'buildDanelfinRebalancePlan', 'shiftDanelfinCalendarDate', 'renderDanelfinPortfolioLab',
  'confluenceCategories', 'confluenceEffectiveCategories', 'stockRoverFactorMetrics', 'renderEvidenceGraph', 'renderBullflowActivityProfile', 'renderOptionStrategyLab', 'state',
];
vm.runInNewContext(`${appSource}\nglobalThis.__reaCandidateFixtureApi = { ${exports.join(', ')} };`, context, { timeout: 5000 });
const api = context.__reaCandidateFixtureApi;
const passed = [];
const boundaryAssertions = [];
const close = (actual, expected, tolerance = 1e-9) => assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} differs from ${expected}`);
const record = (id, fn) => { fn(); passed.push(id); };

record('CAND-leadr-55-metadata', () => {
  const scores = Object.fromEntries(api.confluenceCategories.flatMap(category => category.metrics.map(([key]) => [key, 80])));
  const result = api.computeConfluenceCandidate({ scores, qualified: true, dataConfidence: 80, realIndexCount: 4 });
  assert.equal(result.metricCount, 55);
  assert.equal(result.coveredMetrics, 55);
  assert.equal(result.score, 80);
  assert.equal(result.confirming, 8);
  assert.equal(result.grade, 'Exceptional');
  assert.equal(result.status, 'qualified');
});

record('CAND-leadr-v3-effective', () => {
  const effectiveScores = Object.fromEntries(api.confluenceEffectiveCategories
    .filter(category => !category.externalFramework)
    .flatMap(category => category.leaves.map(([key]) => [key, 80])));
  const result = api.computeConfluenceEffectiveCandidate({ effectiveScores, qualified: true, dataConfidence: 80, realIndexCount: 4 });
  assert.equal(result.metricCount, 14);
  assert.equal(result.coveredMetrics, 14);
  assert.equal(result.score, 80);
  assert.equal(result.confirming, 7);
  assert.equal(result.categories.find(category => category.externalFramework).status, 'no-data');
  assert.equal(result.status, 'qualified');
});

record('CAND-danelfin-sector-portfolio', () => {
  const rows = [
    { ticker: 'AAA', sector: 'Technology', score: 8, lowRisk: 5, avg3mVolume: 100001, provenBuy: false },
    { ticker: 'AAB', sector: 'Technology', score: 7, lowRisk: 8, avg3mVolume: 100001, provenBuy: true },
    { ticker: 'BBB', sector: 'Health Care', score: 9, lowRisk: 4, avg3mVolume: 500000, provenBuy: true },
  ];
  const result = api.buildDanelfinPortfolio(rows, true);
  assert.deepEqual(Array.from(result.chosen, row => row.ticker), ['AAB', 'AAA']);
  assert.equal(result.filteredCount, 1);
  close(result.sectors[0].meanScore, 7.5);
  assert.deepEqual(Array.from(result.chosen, row => row.weightPct), [50, 50]);
});

record('CAND-danelfin-point-in-time-rebalance-plan', () => {
  const snapshot = (date, rows) => rows.map(([ticker, score, lowRisk = 6]) => ({
    ticker, sector: 'Technology', score, lowRisk, avg3mVolume: 200000, provenBuy: true,
    asOf: date, snapshotComplete: true,
  }));
  const history = [
    ...snapshot('2024-01-31', [['AAA', 9], ['BBB', 8]]),
    ...snapshot('2024-04-30', [['AAA', 9, 4], ['BBB', 8], ['CCC', 7]]),
    ...snapshot('2024-07-31', [['BBB', 8], ['CCC', 7]]),
    ...snapshot('2024-10-31', [['BBB', 8], ['CCC', 7]]),
    ...snapshot('2025-01-31', [['BBB', 8], ['CCC', 7]]),
  ];
  const plan = api.buildDanelfinRebalancePlan(history, '2024-01-31', true);
  assert.deepEqual(Array.from(plan.events, event => event.dueDate), ['2024-01-31', '2024-04-30', '2024-07-31', '2024-10-31', '2025-01-31', '2025-04-30']);
  assert.deepEqual(Array.from(plan.events[1].addedTickers), ['CCC']);
  assert.deepEqual(Array.from(plan.events[1].removedTickers), ['AAA']);
  assert.equal(plan.events[1].targetWeightPct, null);
  assert.equal(plan.events[4].annualWeightReviewDue, true);
  assert.equal(plan.events[4].targetWeightPct, 50);
  assert.equal(plan.events[5].status, 'NO_FRESH_SNAPSHOT');
  assert.equal(api.shiftDanelfinCalendarDate('2024-02-29', 12), '2025-02-28');

  const oneSnapshotPlan = api.buildDanelfinRebalancePlan(snapshot('2024-01-31', [['AAA', 9]]), '2024-01-31', true);
  assert.deepEqual(Array.from(oneSnapshotPlan.events, event => event.dueDate), ['2024-01-31', '2024-04-30']);
  assert.equal(oneSnapshotPlan.events[1].status, 'NO_FRESH_SNAPSHOT');
  const previousPortfolio = api.state.danelfinPortfolio;
  let scheduleHtml = '';
  try {
    api.state.danelfinPortfolio = {
      rows: snapshot('2024-01-31', [['AAA', 9]]), filename: 'fixture.csv', source: 'csv', error: '', notice: '',
      provenBuyProvided: true, preferProvenBuy: true, asOf: '2024-01-31', startDate: '2024-01-31',
    };
    scheduleHtml = api.renderDanelfinPortfolioLab();
  } finally {
    api.state.danelfinPortfolio = previousPortfolio;
  }
  assert.ok(scheduleHtml.includes('2024-04-30'));
  assert.ok(scheduleHtml.includes('NO FRESH SNAPSHOT'));

  const atAgeLimit = api.buildDanelfinRebalancePlan([
    ...snapshot('2024-01-31', [['AAA', 9]]),
    ...snapshot('2024-04-23', [['AAA', 9]]),
  ], '2024-01-31', true);
  assert.equal(atAgeLimit.events[1].ageDays, 7);
  assert.equal(atAgeLimit.events[1].status, 'MEMBERSHIP_REVIEW');
  const staleAndFuture = api.buildDanelfinRebalancePlan([
    ...snapshot('2024-01-31', [['AAA', 9]]),
    ...snapshot('2024-05-01', [['BBB', 10]]),
  ], '2024-01-31', true);
  assert.equal(staleAndFuture.events[1].dueDate, '2024-04-30');
  assert.equal(staleAndFuture.events[1].snapshotDate, '2024-01-31');
  assert.equal(staleAndFuture.events[1].status, 'NO_FRESH_SNAPSHOT');
  const unknownCompleteness = api.buildDanelfinRebalancePlan([
    ...snapshot('2024-01-31', [['AAA', 9]]),
    { ...snapshot('2024-04-30', [['BBB', 10]])[0], snapshotComplete: null },
  ], '2024-01-31', true);
  assert.equal(unknownCompleteness.events[1].status, 'SNAPSHOT_COMPLETENESS_UNKNOWN');

  const datedCsv = [
    'Ticker,Score,Sector,LowRisk,Avg3MVolume,ProvenBuySignal,AsOf,SnapshotComplete',
    'AAA,8,Technology,6,200000,yes,2024-01-31,true',
    'AAA,9,Technology,6,200000,yes,2024-04-30,true',
  ].join('\n');
  const parsed = api.parseDanelfinCsv(datedCsv);
  assert.deepEqual(Array.from(parsed.snapshotDates), ['2024-01-31', '2024-04-30']);
  assert.equal(parsed.asOf, '2024-04-30');
  assert.equal(parsed.startDate, '2024-01-31');
  assert.throws(() => api.parseDanelfinCsv(`${datedCsv}\nAAA,7,Technology,6,200000,no,2024-04-30,true`), /duplicate ticker AAA/);
  const inconsistentCsv = `${datedCsv}\nBBB,7,Healthcare,6,200000,no,2024-04-30,true`
    .replace('AAA,9,Technology,6,200000,yes,2024-04-30,true', 'AAA,9,Technology,6,200000,yes,2024-04-30,false');
  assert.throws(() => api.parseDanelfinCsv(inconsistentCsv), /SnapshotComplete must use one consistent value/);
});
boundaryAssertions.push('Danelfin schedule replay uses point-in-time snapshots only, rejects stale/unknown-completeness inputs, replaces changed members on 3-month reviews, and marks annual equal-weight targets without modeling returns.');
boundaryAssertions.push('The planner displays the next scheduled review after the final supplied snapshot as unknown when no fresh snapshot supports it.');
boundaryAssertions.push('The portfolio lab renders the next scheduled date and unknown status from a one-snapshot CSV without inventing membership.');

record('CAND-spotgamma-static-gex', () => {
  const rows = [
    { ticker: 'SPY', asOf: '2026-10-26', spot: 100, strike: 100, type: 'CALL', openInterest: 10, ivPct: 20, dte: 30 },
    { ticker: 'SPY', asOf: '2026-10-26', spot: 100, strike: 100, type: 'PUT', openInterest: 5, ivPct: 20, dte: 30 },
  ];
  const result = api.buildStaticGexSnapshot(rows, { spot: 100, riskFreeRatePct: 0, dividendYieldPct: 0, multiplier: 100, gridRangePct: 10 });
  const years = 30 / 365, sigma = 0.2, denominator = 100 * sigma * Math.sqrt(years);
  const d1 = (0.5 * sigma * sigma * years) / denominator;
  const gamma = Math.exp(-0.5 * d1 * d1) / (Math.sqrt(2 * Math.PI) * denominator);
  close(result.optionRows[0].gamma, gamma);
  close(result.netGex, gamma * 50000);
  assert.equal(result.callWall.strike, 100);
  assert.equal(result.putWall.strike, 100);
  assert.equal(result.zeroGamma, null);
  assert.equal(result.crossingCount, 0);
});

record('CAND-optionstrat-expiration-payoff', () => {
  const legs = [
    { type: 'call', side: 'long', strike: 100, premium: 5, contracts: 1, multiplier: 100 },
    { type: 'call', side: 'short', strike: 110, premium: 2, contracts: 1, multiplier: 100 },
  ];
  const result = api.optionStrategyStats(legs);
  assert.equal(api.optionStrategyPnlAt(legs, 100), -300);
  assert.equal(api.optionStrategyPnlAt(legs, 103), 0);
  assert.equal(api.optionStrategyPnlAt(legs, 120), 700);
  assert.equal(result.minPnl, -300);
  assert.equal(result.maxPnl, 700);
  assert.deepEqual(Array.from(result.breakEvens), [103]);
  assert.equal(result.netDebit, 300);
  assert.equal(result.unboundedLoss, false);
  assert.equal(result.unboundedProfit, false);
});

record('CAND-optionstrat-independent-european-model', () => {
  const call = api.blackScholesEuropean(100, 100, 365, 20, 0, 0, 'call');
  const put = api.blackScholesEuropean(100, 100, 365, 20, 0, 0, 'put');
  close(call.theoreticalPrice, 7.9656, 0.0001);
  close(put.theoreticalPrice, 7.9656, 0.0001);
  close(call.delta, 0.5398279, 1e-7);
  close(put.delta, -0.4601721, 1e-7);
  close(call.gamma, 0.0198476, 1e-7);
  assert.ok(call.vegaPerPctPoint > 0);
  assert.ok(call.thetaPerDay < 0);
  const dividendCall = api.blackScholesEuropean(100, 100, 180, 35, 4.5, 2, 'call');
  const dividendPut = api.blackScholesEuropean(100, 100, 180, 35, 4.5, 2, 'put');
  close(dividendCall.theoreticalPrice - dividendPut.theoreticalPrice, 100 * Math.exp(-0.02 * 180 / 365) - 100 * Math.exp(-0.045 * 180 / 365), 1e-5);
  close(dividendCall.delta - dividendPut.delta, Math.exp(-0.02 * 180 / 365), 1e-7);
  const parsed = api.parseOptionStrategyLegs('type,side,strike,premium,contracts,multiplier,ivPct\ncall,long,100,5,1,100,30\nput,short,90,3,2,100,');
  assert.equal(parsed[0].ivPct, 30);
  assert.equal(parsed[1].ivPct, null);
  assert.throws(() => api.parseOptionStrategyLegs('call,long,100,5,1,100,0'), /IV percent/);
  const matched = api.buildOptionStrategyModel([
    { type: 'call', side: 'long', strike: 100, premium: 7, contracts: 1, multiplier: 100 },
    { type: 'call', side: 'short', strike: 100, premium: 5, contracts: 1, multiplier: 100 },
  ], { spot: 100, daysToExpiration: 365, volatilityPct: 20, riskFreeRatePct: 0, dividendYieldPct: 0 });
  close(matched.netTheoreticalValue, 0);
  close(matched.netDelta, 0);
  close(matched.netGamma, 0);
  close(matched.netVegaPerPctPoint, 0);
  close(matched.modeledPnlVsEntry, -200);
  const rowIv = api.buildOptionStrategyModel(parsed, { spot: 100, daysToExpiration: 30, volatilityPct: 20, riskFreeRatePct: 4, dividendYieldPct: 0 });
  assert.equal(rowIv.rows[0].ivPct, 30);
  assert.equal(rowIv.rows[1].ivPct, 20);
  const longCall = [{ type: 'call', side: 'long', strike: 100, premium: 7, contracts: 1, multiplier: 100, ivPct: null }];
  const settings = { spot: 100, daysToExpiration: 30, volatilityPct: 20, riskFreeRatePct: 4, dividendYieldPct: 0 };
  const sensitivity = api.buildOptionStrategySensitivity(longCall, settings);
  assert.deepEqual(Array.from(sensitivity.spotChangesPct), [-10, -5, 0, 5, 10]);
  assert.deepEqual(Array.from(sensitivity.rows, row => row.multiplier), [0.8, 1, 1.2]);
  const baseModel = api.buildOptionStrategyModel(longCall, settings);
  close(sensitivity.rows[1].cells[2].netTheoreticalValue, baseModel.netTheoreticalValue);
  close(sensitivity.rows[1].cells[2].modeledPnlVsEntry, baseModel.modeledPnlVsEntry);
  assert.ok(sensitivity.rows[1].cells[4].netTheoreticalValue > sensitivity.rows[1].cells[0].netTheoreticalValue);
  assert.ok(sensitivity.rows[2].cells[2].netTheoreticalValue > sensitivity.rows[0].cells[2].netTheoreticalValue);
  const html = api.renderOptionStrategyLab();
  assert.ok(html.includes('European Black–Scholes scenario'));
  assert.ok(html.includes('Scenario sensitivity · model P/L vs entry'));
  assert.ok(html.includes('80% of selected IV'));
  assert.ok(html.includes('not a forecast, quote, or probability'));
  assert.ok(html.includes('NET DELTA'));
  assert.ok(html.includes('theoretical scenario mark, not a quote or probability'));
  assert.ok(html.includes('No OptionStrat code, data, or outputs are used'));
});
boundaryAssertions.push('The independent European model checks standard Black–Scholes price/parity/Greek behavior, manual per-leg IV override and shared-IV fallback, position sign and contract scaling, confirms the base sensitivity cell equals the model mark, checks spot/IV direction for a long call, renders its forecast/quote/probability/vendor-code boundaries, and rejects out-of-range IV without claiming vendor parity.');

record('CAND-optionstrat-independent-american-crr-model', () => {
  const call = api.crrAmericanOption(100, 100, 365, 20, 5, 0, 'call', 300);
  const europeanCall = api.blackScholesEuropean(100, 100, 365, 20, 5, 0, 'call');
  close(call, europeanCall.theoreticalPrice, 0.12);
  const europeanPut = api.blackScholesEuropean(100, 100, 365, 20, 5, 0, 'put');
  const americanPut = api.crrAmericanOption(100, 100, 365, 20, 5, 0, 'put', 200);
  assert.ok(americanPut >= europeanPut.theoreticalPrice);

  const deepInTheMoneyAmericanPut = api.crrAmericanOption(40, 50, 365, 10, 10, 0, 'put', 200);
  const deepInTheMoneyEuropeanPut = api.blackScholesEuropean(40, 50, 365, 10, 10, 0, 'put');
  assert.ok(deepInTheMoneyAmericanPut > deepInTheMoneyEuropeanPut.theoreticalPrice + 1);

  const up = Math.exp(0.2);
  const down = Math.exp(-0.2);
  const probabilityUp = (Math.exp(0.05) - down) / (up - down);
  const oneStepExpected = Math.exp(-0.05) * (probabilityUp * Math.max(100 * up - 100, 0) + (1 - probabilityUp) * Math.max(100 * down - 100, 0));
  close(api.crrAmericanOption(100, 100, 365, 20, 5, 0, 'call', 1), oneStepExpected, 1e-10);
  assert.equal(api.crrAmericanOption(40, 50, 0, 20, 5, 0, 'put', 200), 10);
  assert.throws(() => api.crrAmericanOption(100, 100, 365, 20, -100, 100, 'call', 25), /probability is outside/);
  assert.throws(() => api.crrAmericanOption(100, 100, 365, 20, 5, 0, 'call', 0), /steps must be/);
  assert.throws(() => api.crrAmericanOption(100, 100, 365, 20, 5, 0, 'call', 301), /steps must be/);

  const legs = [{ type: 'call', side: 'long', strike: 100, premium: 5, contracts: 1, multiplier: 100 }];
  const settings = { spot: 100, daysToExpiration: 30, volatilityPct: 20, riskFreeRatePct: 4, dividendYieldPct: 0, exerciseStyle: 'american', treeSteps: 100 };
  const model = api.buildOptionStrategyModel(legs, settings);
  const sensitivity = api.buildOptionStrategySensitivity(legs, settings);
  close(model.rows[0].theoreticalPrice, api.crrAmericanOption(100, 100, 30, 20, 4, 0, 'call', 100));
  close(sensitivity.rows[1].cells[2].netTheoreticalValue, model.netTheoreticalValue);
  assert.ok(Number.isFinite(model.netDelta) && Number.isFinite(model.netGamma) && Number.isFinite(model.netVegaPerPctPoint) && Number.isFinite(model.netThetaPerDay) && Number.isFinite(model.netRhoPerPctPoint));

  const previous = api.state.optionLab;
  api.state.optionLab = { ...previous, ...settings, legs, error: '' };
  const html = api.renderOptionStrategyLab();
  api.state.optionLab = previous;
  assert.ok(html.includes('American CRR binomial scenario'));
  assert.ok(html.includes('FINITE DIFF'));
  assert.ok(html.includes('American · CRR binomial'));
  assert.ok(html.includes('exercise is checked at each CRR lattice node'));
  assert.ok(html.includes('No OptionStrat code, data, or outputs are used'));
});
boundaryAssertions.push('The independent American CRR model checks one-step lattice arithmetic, convergence toward the no-dividend European-call value, early-exercise value for an American put, finite-difference Greeks, the shared-model sensitivity center, tree/probability bounds, and explicit clean-room and theoretical-mark labels.');

record('CAND-optionstrat-zero-payoff-regions', () => {
  const zeroBelow100 = api.optionStrategyStats([
    { type: 'call', side: 'long', strike: 100, premium: 5, contracts: 1, multiplier: 100 },
    { type: 'call', side: 'short', strike: 110, premium: 5, contracts: 1, multiplier: 100 },
  ]);
  assert.deepEqual(Array.from(zeroBelow100.breakEvens), []);
  assert.deepEqual(Array.from(zeroBelow100.breakEvenIntervals, interval => [interval.from, interval.to]), [[0, 100]]);
  const previous = api.state.optionLab;
  api.state.optionLab = { ...previous, spot: 100, legs: [
    { type: 'call', side: 'long', strike: 100, premium: 5, contracts: 1, multiplier: 100 },
    { type: 'call', side: 'short', strike: 110, premium: 5, contracts: 1, multiplier: 100 },
  ] };
  assert.ok(api.renderOptionStrategyLab().includes('≤ $100'));

  const zeroAbove110 = api.optionStrategyStats([
    { type: 'call', side: 'long', strike: 100, premium: 11, contracts: 1, multiplier: 100 },
    { type: 'call', side: 'short', strike: 110, premium: 1, contracts: 1, multiplier: 100 },
  ]);
  assert.deepEqual(Array.from(zeroAbove110.breakEvens), []);
  assert.deepEqual(Array.from(zeroAbove110.breakEvenIntervals, interval => [interval.from, interval.to]), [[110, null]]);
  api.state.optionLab = { ...previous, spot: 110, legs: [
    { type: 'call', side: 'long', strike: 100, premium: 11, contracts: 1, multiplier: 100 },
    { type: 'call', side: 'short', strike: 110, premium: 1, contracts: 1, multiplier: 100 },
  ] };
  assert.ok(api.renderOptionStrategyLab().includes('≥ $110'));
  api.state.optionLab = previous;
});
boundaryAssertions.push('Option payoff distinguishes isolated breakevens from zero-P/L intervals and unbounded flat tails in the displayed summary.');

const asOfDate = '2026-10-27';
const ticker = 'SPY';
const cursor = new Date('2026-10-26T12:00:00Z');
const priorDates = [];
while (priorDates.length < 20) {
  const day = cursor.getUTCDay();
  if (day !== 0 && day !== 6) priorDates.push(cursor.toISOString().slice(0, 10));
  cursor.setUTCDate(cursor.getUTCDate() - 1);
}
priorDates.reverse();
const flowModel = {
  ticker,
  asOfDate,
  asOfTime: '14:00',
  cancellationStatusProvided: true,
  availableSessions: [...priorDates, asOfDate].map(date => ({ ticker, date, exportComplete: true })),
  sessionCoverage: [...priorDates, asOfDate].map(date => ({ ticker, date, available: true, exportComplete: true })),
  rows: priorDates.map(date => ({ sessionDate: date, timeSeconds: 13 * 3600, ticker, contract: 'SPY BASE CALL', expiry: '', type: 'CALL', strike: 600, size: 10, premium: 1000, side: 'ASK', sideSource: 'VENDOR', source: 'Bullflow API', tradeType: 'SWEEP', openInterest: 100 })),
};
flowModel.rows.push(
  { ...flowModel.rows[0], sessionDate: asOfDate, timeSeconds: 13 * 3600, contract: 'SPY 2026-10-30 600C', expiry: '2026-10-30', size: 20, premium: 2500, side: 'ASK', openInterest: 10 },
  { ...flowModel.rows[0], sessionDate: asOfDate, timeSeconds: 15 * 3600, contract: 'SPY 2026-10-30 600C', expiry: '2026-10-30', size: 50, premium: 5000, side: 'ABOVE_ASK', openInterest: 10 },
);

record('CAND-bullflow-activity-profile', () => {
  const result = api.calculateBullflowActivityProfile(flowModel);
  assert.equal(result.targetAvailable, true);
  assert.equal(result.baselineCount, 20);
  assert.equal(result.callVolume, 20);
  assert.equal(result.targetRows.length, 1);
  assert.equal(result.callIntradayRv, 2);
  assert.equal(result.callAskShare, 1);
  assert.equal(result.flags.find(flag => flag.name === 'CALL_VOLUME_SPIKE').active, true);
  assert.equal(result.flags.find(flag => flag.name === 'CALL_BUYING_SURGE').active, true);
  assert.equal(result.flags.find(flag => flag.name === 'UNUSUAL_WEEKLY_ACTIVITY').active, true);
  const baselineOnly = flowModel.rows.filter(row => row.sessionDate !== asOfDate);
  const withAskShare = askSize => ({
    ...flowModel,
    rows: [
      ...baselineOnly,
      { ...flowModel.rows[0], sessionDate: asOfDate, timeSeconds: 13 * 3600, size: askSize, premium: askSize * 100, side: 'ASK' },
      { ...flowModel.rows[0], sessionDate: asOfDate, timeSeconds: 13 * 3600, size: 20 - askSize, premium: (20 - askSize) * 100, side: 'BID' },
    ],
  });
  const exactThreshold = api.calculateBullflowActivityProfile(withAskShare(14));
  assert.equal(exactThreshold.callIntradayRv, 2);
  assert.equal(exactThreshold.callAskShare, 0.7);
  assert.equal(exactThreshold.flags.find(flag => flag.name === 'CALL_BUYING_SURGE').active, true);
  const belowThreshold = api.calculateBullflowActivityProfile(withAskShare(13));
  assert.equal(belowThreshold.flags.find(flag => flag.name === 'CALL_BUYING_SURGE').active, false);
});
boundaryAssertions.push('Bullflow call-buying surge fires at the documented 2× volume and 70% ask-share thresholds, and remains off below 70%.');

record('CAND-bullflow-canceled-print-exclusion', () => {
  const sourceTimestamp = Math.floor(Date.parse('2026-10-27T17:00:00Z') / 1000);
  const csv = [
    'Date,TimeET,Ticker,Contract,Expiry,Type,Strike,Size,Premium,Side,TradeType,OpenInterest,Cancelled,Source,TradeID,SideSource,Timestamp',
    `2026-10-27,13:00,SPY,SPY 2026-10-30 600C,2026-10-30,CALL,600,99,99999,Ask,Sweep,10,true,Bullflow API,trade-1,vendor,${sourceTimestamp}`,
  ].join('\n');
  const parsed = api.parseBullflowActivityCsv(csv);
  assert.equal(parsed.cancellationStatusProvided, true);
  assert.equal(parsed.rows[0].cancelled, true);
  assert.equal(parsed.rows[0].source, 'Bullflow API');
  assert.equal(parsed.rows[0].tradeId, 'trade-1');
  assert.equal(parsed.rows[0].sideSource, 'VENDOR');
  assert.equal(parsed.rows[0].sourceTimestamp, String(sourceTimestamp));
  assert.equal(parsed.sourceTimestampProvided, true);
  assert.ok(parsed.availableSessions.some(item => item.ticker === 'SPY' && item.date === '2026-10-27'));
  const withCancellation = {
    ...flowModel,
    rows: [...flowModel.rows, { ...flowModel.rows[0], sessionDate: asOfDate, timeSeconds: 13 * 3600, size: 99, premium: 99999, cancelled: true }],
  };
  const result = api.calculateBullflowActivityProfile(withCancellation);
  assert.equal(result.callVolume, 20);
  assert.equal(result.netDirectionalPremium, 2500);
  assert.equal(result.targetRows.length, 1);
  const missingCancellation = api.calculateBullflowActivityProfile({ ...flowModel, cancellationStatusProvided: false });
  assert.ok(missingCancellation.statuses.includes('CANCELLATION_STATUS_NOT_PROVIDED'));
  assert.throws(() => api.parseBullflowActivityCsv(csv.replace(',true', ',')), /Cancelled must be true or false/);
  assert.throws(() => api.parseBullflowActivityCsv(csv.replace(String(sourceTimestamp), String(sourceTimestamp + 60))), /Timestamp must match Date and TimeET/);
});
boundaryAssertions.push('Bullflow excludes canceled prints, preserves source ID/side-source/raw timestamp fields, checks timestamp-to-ET consistency, and rejects missing cancellation status.');

record('CAND-bullflow-provenance-and-export-completeness', () => {
  const completeZeroCsv = [
    'Date,TimeET,Ticker,Contract,Expiry,Type,Strike,Size,Premium,Side,TradeType,OpenInterest,Available,ExportComplete,Source,Cancelled,TradeID,SideSource',
    '2026-10-27,,SPY,,,,,0,,,,,true,true,Bullflow API,,,',
  ].join('\n');
  const parsed = api.parseBullflowActivityCsv(completeZeroCsv);
  assert.equal(parsed.sessionCoverage[0].available, true);
  assert.equal(parsed.sessionCoverage[0].exportComplete, true);
  assert.equal(parsed.sessionCoverage[0].source, 'Bullflow API');
  const unknownExport = api.calculateBullflowActivityProfile({
    ...flowModel,
    sessionCoverage: flowModel.sessionCoverage.map((item, index) => index === 0 || item.date === asOfDate ? { ...item, exportComplete: null } : item),
  });
  assert.equal(unknownExport.callIntradayRv, null);
  assert.equal(unknownExport.inputComplete, false);
  assert.ok(unknownExport.statuses.includes('BASELINE_EXPORT_COMPLETENESS_UNKNOWN'));
  const partialSelected = api.calculateBullflowActivityProfile({
    ...flowModel,
    rows: flowModel.rows.filter(row => row.sessionDate !== asOfDate),
    sessionCoverage: flowModel.sessionCoverage.map(item => item.date === asOfDate ? { ...item, exportComplete: false } : item),
  });
  assert.equal(partialSelected.callVolume, null);
  assert.equal(partialSelected.flags.find(flag => flag.name === 'CALL_VOLUME_SPIKE').active, null);
  assert.ok(partialSelected.statuses.includes('NO_PRINTS_IN_UNVERIFIED_EXPORT'));
  assert.throws(() => api.parseBullflowActivityCsv([
    'Date,TimeET,Ticker,Contract,Expiry,Type,Strike,Size,Premium,Side,TradeType,OpenInterest,Source,TradeID,SideSource,Cancelled',
    '2026-10-27,13:00,SPY,C1,2026-10-30,CALL,600,1,100,Ask,Sweep,1,Bullflow API,dup,vendor,false',
    '2026-10-27,13:01,SPY,C2,2026-10-30,CALL,601,1,100,Ask,Sweep,1,Bullflow API,dup,vendor,false',
  ].join('\n')), /duplicate TradeID/);
  const unknownSide = api.calculateBullflowActivityProfile({
    ...flowModel,
    rows: flowModel.rows.map(row => row.sessionDate === asOfDate && row.type === 'CALL' ? { ...row, sideSource: 'UNKNOWN' } : row),
  });
  assert.equal(unknownSide.callIntradayRv, 2);
  assert.equal(unknownSide.callAskShare, null);
  assert.equal(unknownSide.netDirectionalPremium, null);
  assert.equal(unknownSide.flags.find(flag => flag.name === 'CALL_BUYING_SURGE').active, null);
  const sourceLabeledZero = api.calculateBullflowActivityProfile({
    ...flowModel,
    rows: flowModel.rows.filter(row => row.sessionDate !== asOfDate),
    sessionCoverage: flowModel.sessionCoverage.map(item => item.date === asOfDate ? { ...item, source: 'Zero-print export' } : item),
  });
  assert.ok(sourceLabeledZero.rowSources.includes('Zero-print export'));
});
boundaryAssertions.push('Bullflow requires explicit export-completeness declarations for ratios and known-zero claims, rejects duplicate source IDs, and suppresses side-derived output when classification provenance is unknown.');

record('CAND-finviz-filter-subset', () => {
  const csv = [
    'Ticker,Name,SecurityType,Exchange,Index,Sector,Country,MarketCap,PE,Price,AvgVolume,RelativeVolume,ChangePct,PatternTag,CandlestickTag',
    'AAA,Alpha,Stock,NASD,S&P 500,Technology,USA,20B,10,100,1000,1,1,wedgeup,d',
    'BBB,Beta,Stock,NYSE,S&P 500,Technology,USA,30B,15,110,2000,1,2,2,wedgeup,d',
    'CCC,Gamma,Stock,NASD,S&P 500,Energy,USA,40B,20,200,3000,1,3,3,wedgeup,d',
    'SPY,Index ETF,ETF,NYSE,S&P 500,Technology,USA,500B,20,500,10000,1,0.5,0,wedgeup,d',
  ].join('\n');
  const rows = api.parseFinvizSnapshotCsv(csv);
  const result = api.calculateFinvizContract({ rows, filterQuery: 'exch_nasd,exch_nyse,sec_technology,cap_largeover', order: '-marketCap', tickers: '' });
  assert.deepEqual(Array.from(result.rows, row => row.ticker), ['BBB']);
  assert.equal(result.overrides, 1);
  assert.equal(result.filtersApplied, 3);
  assert.equal(result.excludedEtfs[0], 'SPY');
  assert.equal(result.filteredOut, 2);
});

record('CAND-stockrover-factor-profile', () => {
  assert.equal(api.stockRoverFactorMetrics.length, 23);
  const strong = {}, weak = {};
  for (const metric of api.stockRoverFactorMetrics) {
    strong[metric.key] = metric.lowerBetter ? 1 : 2;
    weak[metric.key] = metric.lowerBetter ? 2 : 1;
  }
  const result = api.calculateStockRoverFactorScores([
    { ticker: 'AAA', sector: 'Technology', asOf: '2026-10-26', raw: strong },
    { ticker: 'BBB', sector: 'Technology', asOf: '2026-10-26', raw: weak },
  ]);
  assert.equal(result.fullyScored, 2);
  assert.equal(result.top.ticker, 'AAA');
  assert.equal(result.top.composite, 100);
  assert.equal(result.rows.find(row => row.ticker === 'BBB').composite, 0);
  assert.equal(result.medianComposite, 50);
});

record('CAND-azrael-public-1587-map', () => {
  const result = api.buildAzraelMap({ anchorClose: 500, vixClose: 15.87, elapsedMinutes: 90, sessionMinutes: 360, candidateTarget: 504 });
  assert.equal(result.pct, 1);
  assert.equal(result.expectedMove, 5);
  assert.equal(result.half, 2.5);
  assert.equal(result.fundedMove, 2.5);
  assert.equal(result.regime, 'MIXED');
  assert.equal(result.targetRead.label, 'Inside the outer half of the expected band');
  assert.equal(result.lines[0].level, 505);
  assert.equal(result.lines.at(-1).level, 495);
  const homepageExample = api.buildAzraelMap({ anchorClose: 7659.44, vixClose: 19.99, elapsedMinutes: 0, sessionMinutes: 390 });
  assert.equal(homepageExample.expectedMove, 96.5);
  assert.equal(homepageExample.fundedMove, 0);
  assert.equal(homepageExample.lines[0].level, 7755.94);
  assert.equal(homepageExample.lines.at(-1).level, 7562.94);
  const publicPostExample = api.buildAzraelMap({ anchorClose: 7757.17, vixClose: 16.68, elapsedMinutes: 0, sessionMinutes: 390 });
  assert.equal(publicPostExample.expectedMove, 81.5);
  assert.equal(publicPostExample.weeklyMove.toFixed(1), '182.2');
});

boundaryAssertions.push('Azrael reproduces the public homepage and post examples with the documented one-decimal pipeline.');
const earlyCloseMap = api.buildAzraelMap({ anchorClose: 500, vixClose: 15.87, elapsedMinutes: 105, sessionMinutes: 210, candidateTarget: 505 });
assert.ok(Math.abs(earlyCloseMap.fundedMove - (5 * Math.sqrt(0.5))) < 1e-12);
assert.equal(earlyCloseMap.lines[0].level, 505);
assert.equal(earlyCloseMap.targetRead.label, 'Inside the outer half of the expected band');
const beyondWallMap = api.buildAzraelMap({ anchorClose: 500, vixClose: 15.87, elapsedMinutes: 0, sessionMinutes: 390, candidateTarget: 505.01 });
assert.equal(beyondWallMap.targetRead.label, 'Beyond the upper ±1.0 wall');
boundaryAssertions.push('Azrael early-close scaling changes only the funded range; fixed walls and exact target-band boundaries remain stable.');
assert.equal(api.computeConfluenceCandidate({ scores: { rsMarket: 101 } }).status, 'invalid-input');
boundaryAssertions.push('Leadr rejects an out-of-range normalized metric.');
assert.ok(api.buildAzraelMap({ anchorClose: 500, vixClose: 15, elapsedMinutes: 361, sessionMinutes: 360 }).error);
boundaryAssertions.push('Azrael rejects elapsed time beyond the declared session.');
assert.throws(() => api.calculateFinvizContract({ rows: [], filterQuery: 'unsupported_token', order: 'ticker', tickers: '' }), /Unsupported filter token/);
boundaryAssertions.push('Finviz rejects a token outside the implemented documented subset.');
const shortHistory = api.calculateBullflowActivityProfile({
  ...flowModel,
  availableSessions: flowModel.availableSessions.slice(1),
  sessionCoverage: flowModel.sessionCoverage.slice(1),
});
assert.equal(shortHistory.callIntradayRv, null);
assert.ok(shortHistory.statuses.includes('INSUFFICIENT_HISTORY'));
assert.equal(shortHistory.flags.find(flag => flag.name === 'CALL_VOLUME_SPIKE').active, null);
boundaryAssertions.push('Bullflow preserves unknown when fewer than 20 baseline sessions are covered.');

const metadataBoundaryScores = Object.fromEntries(api.confluenceCategories[0].metrics.slice(0, 4).map(([key]) => [key, 80]));
const underFloor = api.computeConfluenceCandidate({ scores: metadataBoundaryScores });
assert.equal(underFloor.categories[0].status, 'no-data');
assert.equal(underFloor.coveredMetrics, 4);
boundaryAssertions.push('Leadr metadata category remains unavailable below the 60% leaf-coverage floor.');
const floorScores = Object.fromEntries(api.confluenceCategories[0].metrics.slice(0, 5).map(([key]) => [key, 60]));
const atFloor = api.computeConfluenceCandidate({ scores: floorScores });
assert.equal(atFloor.categories[0].status, 'confirming');
assert.equal(atFloor.categories[0].score, 60);
boundaryAssertions.push('Leadr metadata category computes at five of seven leaves and classifies a score of 60 as confirming.');
assert.equal(api.computeConfluenceCandidate({ scores: {}, dataConfidence: 101 }).status, 'invalid-input');
boundaryAssertions.push('Leadr rejects out-of-range optional confidence even when no score leaves are supplied.');
const effectiveHalf = api.computeConfluenceEffectiveCandidate({ effectiveScores: { mom12_1: 80 } });
assert.equal(effectiveHalf.categories[0].status, 'no-data');
assert.equal(effectiveHalf.categories.at(-1).status, 'no-data');
boundaryAssertions.push('Leadr v3 keeps one of two relative-strength leaves below coverage and external context unavailable.');

const danelfinAtBoundary = api.buildDanelfinPortfolio([
  { ticker: 'PASS', sector: 'Alpha', score: 7, lowRisk: 5, avg3mVolume: 100001, provenBuy: false },
  { ticker: 'RISK', sector: 'Beta', score: 9, lowRisk: 4, avg3mVolume: 100001, provenBuy: true },
  { ticker: 'VOLUME', sector: 'Gamma', score: 9, lowRisk: 5, avg3mVolume: 100000, provenBuy: true },
], true);
assert.deepEqual(Array.from(danelfinAtBoundary.chosen, row => row.ticker), ['PASS']);
assert.equal(danelfinAtBoundary.filteredCount, 2);
boundaryAssertions.push('Danelfin includes LowRisk 5 and volume 100001, while excluding LowRisk 4 and volume exactly 100000.');
assert.throws(() => api.parseDanelfinCsv('Ticker,Score,Sector,LowRisk,Avg3MVolume\nAAA,7,Tech,6,200000\nAAA,8,Tech,7,300000'), /duplicate ticker AAA/);
boundaryAssertions.push('Danelfin CSV rejects duplicate tickers instead of double-counting a snapshot.');

assert.throws(() => api.parseStaticGexCsv('Ticker,AsOf,Spot,Strike,Type,OpenInterest,IV,DTE\nSPY,2026-10-26,100,100,Call,1,20,0'), /DTE must be at least 0.01/);
boundaryAssertions.push('Static GEX CSV rejects unsupported zero-DTE contracts.');
assert.throws(() => api.parseStaticGexCsv('Ticker,AsOf,Spot,Strike,Type,OpenInterest,IV,DTE\nSPY,2026-10-26,100,100,Call,1,20,30\nSPY,2026-10-26,100,100,C,2,20,30'), /duplicate SPY CALL contract/);
boundaryAssertions.push('Static GEX CSV rejects duplicate strike/type/expiry-day contracts.');
const zeroOiGex = api.buildStaticGexSnapshot([
  { ticker: 'SPY', asOf: '2026-10-26', spot: 100, strike: 100, type: 'CALL', openInterest: 0, ivPct: 20, dte: 30 },
], { spot: 100, riskFreeRatePct: 0, dividendYieldPct: 0, multiplier: 100, gridRangePct: 10 });
assert.equal(zeroOiGex.netGex, 0);
assert.equal(zeroOiGex.callWall, null);
boundaryAssertions.push('Static GEX reports no call wall when supplied open interest is zero.');

const eightLegs = Array.from({ length: 8 }, () => 'call,long,100,1,1').join('\n');
assert.equal(api.parseOptionStrategyLegs(eightLegs).length, 8);
assert.throws(() => api.parseOptionStrategyLegs(`${eightLegs}\ncall,long,100,1,1`), /no more than eight/);
boundaryAssertions.push('Option payoff accepts the eight-leg maximum and rejects a ninth leg.');
const shortCall = api.optionStrategyStats([{ type: 'call', side: 'short', strike: 100, premium: 5, contracts: 1, multiplier: 100 }]);
assert.equal(shortCall.unboundedLoss, true);
assert.equal(shortCall.unboundedProfit, false);
assert.deepEqual(Array.from(shortCall.breakEvens), [105]);
boundaryAssertions.push('Option payoff marks a naked short-call tail as unbounded loss and locates its 105 breakeven.');

const unavailableTarget = api.calculateBullflowActivityProfile({
  ...flowModel,
  availableSessions: flowModel.availableSessions.filter(item => item.date !== asOfDate),
  sessionCoverage: flowModel.sessionCoverage.filter(item => item.date !== asOfDate),
});
assert.equal(unavailableTarget.targetAvailable, false);
assert.equal(unavailableTarget.flags.find(flag => flag.name === 'CALL_VOLUME_SPIKE').active, null);
boundaryAssertions.push('Bullflow distinguishes an unavailable selected session from a covered zero-print session.');
const knownZero = api.calculateBullflowActivityProfile({ ...flowModel, rows: flowModel.rows.filter(row => row.sessionDate !== asOfDate) });
assert.equal(knownZero.targetAvailable, true);
assert.equal(knownZero.callVolume, 0);
assert.equal(knownZero.flags.find(flag => flag.name === 'CALL_VOLUME_SPIKE').active, false);
assert.ok(knownZero.statuses.includes('NO_PRINTS_THROUGH_AS_OF'));
boundaryAssertions.push('Bullflow preserves a covered no-print session as known zero and returns a false spike flag.');

const finvizListRows = api.parseFinvizSnapshotCsv([
  'Ticker,Name,SecurityType,Exchange,Sector,Country,MarketCap',
  'AAA,Alpha,Stock,NASD,Technology,USA,20B',
  'BBB,Beta,Stock,NYSE,Technology,USA,30B',
  'SPY,Index ETF,ETF,NYSE,Technology,USA,500B',
].join('\n'));
const finvizList = api.calculateFinvizContract({ rows: finvizListRows, filterQuery: '', order: 'tickersfilter', tickers: 'BBB,SPY,MISS,AAA,BBB' });
assert.deepEqual(Array.from(finvizList.rows, row => row.ticker), ['BBB', 'AAA']);
assert.deepEqual(Array.from(finvizList.missingTickers), ['MISS']);
assert.deepEqual(Array.from(finvizList.excludedEtfs), ['SPY']);
boundaryAssertions.push('Finviz ticker-list mode preserves requested order, deduplicates requests, and reports missing/ETF symbols.');

const oneMissing = Object.fromEntries(api.stockRoverFactorMetrics.map(metric => [metric.key, metric.lowerBetter ? 1 : 2]));
oneMissing[api.stockRoverFactorMetrics[0].key] = null;
const incompleteFactor = api.calculateStockRoverFactorScores([
  { ticker: 'AAA', sector: 'Technology', asOf: '2026-10-26', raw: oneMissing },
  { ticker: 'BBB', sector: 'Technology', asOf: '2026-10-26', raw: Object.fromEntries(api.stockRoverFactorMetrics.map(metric => [metric.key, metric.lowerBetter ? 2 : 1])) },
]);
const incompleteRow = incompleteFactor.rows.find(row => row.ticker === 'AAA');
assert.equal(incompleteRow.missingMetrics, 1);
assert.equal(incompleteRow.composite, null);
assert.ok(incompleteRow.completedCategories < 4);
boundaryAssertions.push('Stock Rover leaves an incomplete composite unavailable rather than imputing the missing metric.');
const tiedRaw = Object.fromEntries(api.stockRoverFactorMetrics.map(metric => [metric.key, 5]));
const tiedFactors = api.calculateStockRoverFactorScores([
  { ticker: 'AAA', sector: 'Technology', asOf: '2026-10-26', raw: tiedRaw },
  { ticker: 'BBB', sector: 'Technology', asOf: '2026-10-26', raw: { ...tiedRaw } },
]);
assert.equal(tiedFactors.rows.find(row => row.ticker === 'AAA').percentiles.EVEBITDA, 50);
assert.equal(tiedFactors.rows.find(row => row.ticker === 'BBB').percentiles.EVEBITDA, 50);
boundaryAssertions.push('Stock Rover assigns midpoint percentiles to a two-name tie.');

const regimeEdges = [
  [14.99, 'CALM'], [15, 'MIXED'], [18.5, 'MIXED'], [18.5001, 'FAST'],
].map(([vixClose, expected]) => [api.buildAzraelMap({ anchorClose: 500, vixClose, elapsedMinutes: 0, sessionMinutes: 390 }).regime, expected]);
assert.deepEqual(regimeEdges, [['CALM', 'CALM'], ['MIXED', 'MIXED'], ['MIXED', 'MIXED'], ['FAST', 'FAST']]);
boundaryAssertions.push('Azrael regime transitions are checked immediately below, at, and above both published boundaries.');
const azraelClockEdges = api.buildAzraelMap({ anchorClose: 500, vixClose: 15.87, elapsedMinutes: 0, sessionMinutes: 390, candidateTarget: 505 });
assert.equal(azraelClockEdges.fundedMove, 0);
assert.equal(azraelClockEdges.targetRead.label, 'Inside the outer half of the expected band');
assert.equal(api.buildAzraelMap({ anchorClose: 500, vixClose: 15.87, elapsedMinutes: 390, sessionMinutes: 390 }).fundedMove, 5);
boundaryAssertions.push('Azrael checks zero-time/full-session funding and treats an exact upper wall as in-band.');

record('EVIDENCE-ainvest-products-stay-distinct', () => {
  const html = api.renderEvidenceGraph();
  assert.ok(html.includes('AIME / AIME+ · AI research surface'));
  assert.ok(html.includes('Magic Signal · public claim audit'));
  assert.ok(html.includes('Option Pilot · options score evidence'));
  assert.ok(!html.includes('AInvest / Option Pilot · evidence audit'));
  assert.ok(html.includes('Shared models, backend, entitlements'));
  assert.ok(html.includes('personal, internal, non-commercial'));
  assert.ok(html.includes('one-day IC +0.0001'));
  const aInvestCards = [...html.matchAll(/<article class="coverage-vendor evidence-build">([\s\S]*?)<\/article>/g)]
    .map(([, card]) => card)
    .filter(card => /<h3>(?:AIME \/ AIME\+ · AI research surface|Magic Signal · public claim audit|Option Pilot · options score evidence)<\/h3>/.test(card));
  assert.equal(aInvestCards.length, 3);
  assert.ok(aInvestCards.every(card => card.includes('<summary>Source claims, caveats, and access boundary</summary>')));
});
boundaryAssertions.push('AIME, Magic Signal, and Option Pilot render as separate evidence cards with public-only claims and access limits.');

record('EVIDENCE-stock-moe-offers-stay-separate', () => {
  const html = api.renderEvidenceGraph();
  assert.ok(html.includes('Stock Moe Earner · public offer audit'));
  assert.ok(html.includes('$49.99/month'));
  assert.ok(html.includes('$162.99/month'));
  assert.ok(html.includes('$48/week'));
  assert.ok(html.includes('not one canonical tier schedule'));
  assert.ok(html.includes('Wednesday livestream, exclusive support channel'));
  assert.ok(html.includes('No Discord role, private bot output'));
});
boundaryAssertions.push('Stock Moe pricing remains separated by dated public listing, and Earner Plus entitlements retain their own offer boundary.');

record('EVIDENCE-bullflow-boundary-display', () => {
  const evidenceHtml = api.renderEvidenceGraph();
  assert.ok(evidenceHtml.includes('Bullflow · Options Activity Profile'));
  assert.ok(evidenceHtml.includes('prior 20 available ticker dates'));
  assert.ok(evidenceHtml.includes('The vendor describes SigScore as proprietary'));
  assert.ok(evidenceHtml.includes('No paid API, stream, site extraction'));
  const previous = api.state.bullflowProfile;
  api.state.bullflowProfile = { ...flowModel, cancellationStatusProvided: false, filename: 'fixture.csv', error: '', notice: '' };
  const profileHtml = api.renderBullflowActivityProfile();
  api.state.bullflowProfile = previous;
  assert.ok(profileHtml.includes('CANCELLATION STATUS NOT PROVIDED'));
  assert.ok(profileHtml.includes('Cancelled'));
});
boundaryAssertions.push('Bullflow evidence cards disclose source limits, and its profile view surfaces missing cancellation status.');

const report = {
  status: 'PASS',
  runDateUtc: new Date().toISOString(),
  candidateCaseCount: passed.length,
  passedCandidateCases: passed,
  boundaryAssertionCount: boundaryAssertions.length,
  boundaryAssertions,
  appSha256: createHash('sha256').update(appSource).digest('hex'),
  fixtureSha256: createHash('sha256').update(await readFile(fileURLToPath(import.meta.url))).digest('hex'),
  command: 'node apps/silicon-market-terminal/candidate-calculation-fixtures.mjs',
  scope: 'Focused deterministic fixtures against current local browser calculation functions and evidence graph rendering; no vendor runtime or external-output parity is tested.',
};
await writeFile(resultPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
process.stdout.write(`${JSON.stringify({ status: report.status, candidateCaseCount: report.candidateCaseCount, boundaryAssertionCount: report.boundaryAssertionCount, appSha256: report.appSha256, reportPath: path.relative(path.resolve(here, '..', '..'), resultPath).replaceAll(path.sep, '/') }, null, 2)}\n`);
