import test from 'node:test';
import assert from 'node:assert/strict';
import { parseStaticGexCsv, buildStaticGexSnapshot, blackScholesGamma } from '../components/static-gex.mjs';
import { parseBullflowActivityCsv, calculateBullflowActivityProfile } from '../components/bullflow-activity.mjs';
import { parseFinvizSnapshotCsv, calculateFinvizContract } from '../components/finviz-filter.mjs';
import { parseStockRoverFactorCsv, calculateStockRoverFactorScores, stockRoverFactorMetrics } from '../components/stockrover-factors.mjs';
import { computeConfluenceCandidate, confluenceCategories } from '../components/confluence.mjs';
import { parseDanelfinCsv, buildDanelfinPortfolio, buildDanelfinRebalancePlan } from '../components/portfolio.mjs';
import { parseStrategyCsv, analyzeStrategy } from '../components/strategy-sma.mjs';
import { evaluateChangeAlerts } from '../components/daily-change-alerts.mjs';

// Every row below is a fabricated test input. No vendor feed or user dataset is read.
test('static GEX math uses caller-provided rows and the documented call/put sign convention', () => {
  const csv = 'Ticker,AsOf,Spot,Strike,Type,OpenInterest,IV,DTE\nSYN,2026-01-02,100,100,Call,10,20,30\nSYN,2026-01-02,100,100,Put,10,20,30\n';
  const parsed = parseStaticGexCsv(csv);
  assert.equal(parsed.rows.length, 2);
  const gamma = blackScholesGamma(100, 100, 30, 20, 0, 0);
  const years = 30 / 365, sigma = 0.2, d1 = 0.5 * sigma * Math.sqrt(years);
  const oracle = Math.exp(-0.5 * d1 * d1) / (100 * sigma * Math.sqrt(years) * Math.sqrt(2 * Math.PI));
  assert.ok(Math.abs(gamma - oracle) < 1e-12);
  const result = buildStaticGexSnapshot(parsed.rows, { spot: 100, riskFreeRatePct: 0, dividendYieldPct: 0, multiplier: 100, gridRangePct: 10 });
  assert.ok(result.optionRows[0].dollarGex > 0);
  assert.ok(result.optionRows[1].dollarGex < 0);
  assert.ok(Math.abs(result.netGex) < 1e-8);
  assert.equal(result.zeroGamma, null);
  assert.throws(() => parseStaticGexCsv(csv.replace('20,30', '0,30')), /IV must be/);
});

test('activity summary respects explicit incomplete coverage without relying on sampled data', () => {
  const csv = [
    'Date,TimeET,Ticker,Contract,Expiry,Type,Strike,Size,Premium,Side,TradeType,OI,Available,ExportComplete,Cancelled,Source,TradeID,SideSource,Timestamp',
    '2026-01-02,10:00,SYN,SYN260109C00100000,2026-01-09,CALL,100,5,500,ASK,SWEEP,100,true,,false,ExampleSource,row-1,UNKNOWN,2026-01-02T15:00:00Z',
    ['2026-01-02', '', 'SYN', '', '', '', '', '0', '', '', '', '', 'true', '', '', '', '', '', ''].join(','),
  ].join('\n');
  const model = parseBullflowActivityCsv(csv);
  const result = calculateBullflowActivityProfile({ ...model, ticker: 'SYN', asOfDate: '2026-01-02', asOfTime: '16:00' });
  assert.equal(model.rows.length, 1);
  assert.equal(result.inputComplete, false);
  assert.equal(result.callIntradayRv, null);
  assert.throws(() => parseBullflowActivityCsv(csv.replace('ExampleSource,row-1', 'synthetic,row-1')), /synthetic/);
});

test('screener constructor treats tags as supplied input and applies documented filters', () => {
  const rows = parseFinvizSnapshotCsv('Ticker,Name,SecurityType,Sector,MarketCap,Price,PatternTag\nAAA,Example,Stock,Technology,20B,12,horizontal\nBBB,Example Two,Stock,Industrials,9B,8,wedgeup\n');
  const result = calculateFinvizContract({ rows, filterQuery: 'cap_largeover', order: '-marketcap' });
  assert.deepEqual(result.rows.map(row => row.ticker), ['AAA']);
  assert.equal(result.rows[0].pattern, 'horizontal');
  assert.equal(result.filteredOut, 1);
  assert.throws(() => calculateFinvizContract({ rows, filterQuery: 'ta_pattern_not-real', order: 'ticker' }), /Unsupported pattern/);
});

test('factor ranking requires complete dated caller input and midranks ties', () => {
  const header = ['Ticker', 'Sector', 'AsOf', ...stockRoverFactorMetrics.map(metric => metric.key)].join(',');
  const row = (ticker, value) => [ticker, 'ExampleSector', '2026-01-02', ...stockRoverFactorMetrics.map(metric => metric.key === 'PriceTo52WeekHigh' ? 0.5 : value)].join(',');
  const parsed = parseStockRoverFactorCsv(`${header}\n${row('AAA', 1)}\n${row('BBB', 2)}\n`);
  const result = calculateStockRoverFactorScores(parsed.rows);
  assert.equal(parsed.asOf, '2026-01-02');
  assert.equal(result.fullyScored, 2);
  assert.equal(result.rows[0].ticker, 'BBB');
  assert.ok(result.rows[0].composite > result.rows[1].composite);
  assert.ok(result.rows.every(item => item.completedCategories === 4));
  assert.throws(() => parseStockRoverFactorCsv(`${header}\n${row('AAA', 1)}\n${row('AAA', 2)}\n`), /Duplicate ticker/);
});

test('manual confluence aggregation reports missing data and enforces declared bounds', () => {
  const scores = Object.fromEntries(confluenceCategories.flatMap(category => category.metrics.map(([key]) => [key, 70])));
  const full = computeConfluenceCandidate({ scores, qualified: true, dataConfidence: 90, realIndexCount: 6 });
  assert.equal(full.metricCount, 55);
  assert.equal(full.score, 70);
  assert.equal(full.status, 'qualified');
  assert.equal(computeConfluenceCandidate({}).status, 'insufficient-data');
  assert.equal(computeConfluenceCandidate({ scores: { rsMarket: 101 } }).status, 'invalid-input');
});

test('portfolio constructor creates hypothetical weights from supplied rows, not holdings', () => {
  const csv = 'Ticker,Score,Sector,LowRisk,Avg3MVolume,ProvenBuySignal,AsOf,SnapshotComplete\nSYN,8,Technology,6,150000,true,2026-01-02,true\n';
  const parsed = parseDanelfinCsv(csv);
  const portfolio = buildDanelfinPortfolio(parsed.rows);
  assert.equal(portfolio.chosen.length, 1);
  assert.equal(portfolio.chosen[0].ticker, 'SYN');
  assert.equal(portfolio.chosen[0].weightPct, 100);
  const plan = buildDanelfinRebalancePlan(parsed.rows, parsed.startDate);
  assert.equal(plan.events[0].status, 'INITIAL_ALLOCATION');
  assert.deepEqual(plan.events[0].selectedTickers, ['SYN']);
  const tooThin = parseDanelfinCsv(csv.replace('150000', '100000'));
  assert.equal(buildDanelfinPortfolio(tooThin.rows).chosen.length, 0);
});

test('SMA replay uses explicit rows and rejects invalid windows/cost settings', () => {
  const rows = parseStrategyCsv('Date,Close\n2026-01-01,10\n2026-01-02,11\n2026-01-03,12\n2026-01-04,13\n2026-01-05,14\n2026-01-06,15\n');
  const result = analyzeStrategy({ rows, fast: 2, slow: 3, costBps: 10, splitPct: 70, periodsPerYear: 252 });
  assert.equal(result.error, undefined);
  assert.equal(result.records.length, 2);
  assert.equal(result.records[0].date, '2026-01-05');
  assert.ok(result.overall.totalReturn > 0);
  assert.match(analyzeStrategy({ rows, fast: 2, slow: 2, costBps: 0, splitPct: 70, periodsPerYear: 252 }).error, /Slow average/);
  assert.throws(() => parseStrategyCsv('Date,Close\n2026-01-01,-1\n2026-01-02,2\n'), /non-positive/);
});

test('daily-change evaluator is a pure input/output calculation', () => {
  const alerts = [
    { id: 'example-1', ticker: 'SYN', condition: 'change', threshold: 5 },
    { id: 'example-2', ticker: 'OTHER', condition: 'change', threshold: 5 },
    { id: 'example-3', ticker: 'SYN', condition: 'premium', threshold: 1 },
  ];
  const feed = { symbol: 'SYN', bars: [
    { at: '2026-01-01T00:00:00Z', close: 100 },
    { at: '2026-01-02T00:00:00Z', close: 106 },
  ] };
  const result = evaluateChangeAlerts(alerts, feed);
  assert.notEqual(result, alerts);
  assert.equal(result[0].lastEvaluation.barAt, feed.bars[1].at);
  assert.ok(Math.abs(result[0].lastEvaluation.changePct - 6) < 1e-12);
  assert.equal(result[0].lastEvaluation.matched, true);
  assert.equal(result[1], alerts[1]);
  assert.equal(result[2], alerts[2]);
  assert.equal(alerts[0].lastEvaluation, undefined, 'input records are not mutated');
});
