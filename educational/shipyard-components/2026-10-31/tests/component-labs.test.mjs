import assert from 'node:assert/strict';
import test from 'node:test';
import { parseStaticGexCsv, buildStaticGexSnapshot, blackScholesGamma } from '../components/static-gex.mjs';
import { parseBullflowActivityCsv, calculateBullflowActivityProfile } from '../components/bullflow-activity.mjs';
import { parseFinvizSnapshotCsv, calculateFinvizContract } from '../components/finviz-filter.mjs';
import { parseStockRoverFactorCsv, calculateStockRoverFactorScores, stockRoverFactorMetrics } from '../components/stockrover-factors.mjs';
import { computeConfluenceCandidate, confluenceCategories } from '../components/confluence.mjs';
import { parseDanelfinCsv, buildDanelfinPortfolio, buildDanelfinRebalancePlan } from '../components/portfolio.mjs';
import { parseStrategyCsv, analyzeStrategy } from '../components/strategy-sma.mjs';
import { evaluateChangeAlerts } from '../components/daily-change-alerts.mjs';
import { parseEvidenceCsv } from '../dist/convergence-evidence-csv.mjs';
import { parseTreasuryCurve, parseTreasuryRealCurve, parseFedDollarIndex, parseCboeIndexCsv } from '../components/public-feed-parsers.mjs';

test('static GEX CSV validates input and signs calls/puts around an independent gamma value', () => {
  const csv = 'Ticker,AsOf,Spot,Strike,Type,OpenInterest,IV,DTE\nABC,2026-10-30,100,100,Call,10,20,30\nABC,2026-10-30,100,100,Put,10,20,30\n';
  const parsed = parseStaticGexCsv(csv);
  assert.equal(parsed.rows.length, 2);
  const gamma = blackScholesGamma(100, 100, 30, 20, 0, 0);
  const years = 30 / 365, sigma = 0.2, d1 = 0.5 * sigma * Math.sqrt(years);
  const oracleGamma = Math.exp(-0.5 * d1 * d1) / (100 * sigma * Math.sqrt(years) * Math.sqrt(2 * Math.PI));
  assert.ok(Math.abs(gamma - oracleGamma) < 1e-12);
  const result = buildStaticGexSnapshot(parsed.rows, { spot: 100, riskFreeRatePct: 0, dividendYieldPct: 0, multiplier: 100, gridRangePct: 10 });
  assert.ok(result.optionRows[0].dollarGex > 0);
  assert.ok(result.optionRows[1].dollarGex < 0);
  assert.ok(Math.abs(result.netGex) < 1e-8);
  assert.equal(result.zeroGamma, null, 'a fully offset/flat profile has no unique zero crossing');
  assert.throws(() => parseStaticGexCsv(csv.replace('20,30', '0,30')), /IV must be/);
});

test('Bullflow CSV preserves incomplete coverage and refuses synthetic sample rows', () => {
  const csv = [
    'Date,TimeET,Ticker,Contract,Expiry,Type,Strike,Size,Premium,Side,TradeType,OI,Available,ExportComplete,Cancelled,Source,TradeID,SideSource,Timestamp',
    '2026-10-29,10:00,ABC,ABC261030C00100000,2026-10-30,CALL,100,5,500,ASK,SWEEP,100,true,,false,Vendor,record-1,VENDOR,2026-10-29T14:00:00Z',
    ['2026-10-29', '', 'ABC', '', '', '', '', '0', '', '', '', '', 'true', 'true', '', '', '', '', ''].join(','),
  ].join('\n');
  const model = parseBullflowActivityCsv(csv);
  assert.equal(model.rows.length, 1);
  assert.equal(model.sessionCoverage.length, 1);
  const result = calculateBullflowActivityProfile({ ...model, ticker: 'ABC', asOfDate: '2026-10-29', asOfTime: '16:00' });
  assert.equal(result.targetAvailable, true);
  assert.equal(result.inputComplete, false, 'a declared selected session is not a complete 20-session baseline');
  assert.equal(result.callIntradayRv, null);
  assert.throws(() => parseBullflowActivityCsv(csv.replace('Vendor,record-1', 'synthetic,record-1')), /synthetic/);
});

test('Finviz lab treats pattern tags as supplied fields and applies documented cap filter', () => {
  const rows = parseFinvizSnapshotCsv('Ticker,Name,SecurityType,Sector,MarketCap,Price,PatternTag\nAAA,Example,Stock,Technology,20B,12,horizontal\nBBB,Example Two,Stock,Industrials,9B,8,wedgeup\n');
  const result = calculateFinvizContract({ rows, filterQuery: 'cap_largeover', order: '-marketcap' });
  assert.deepEqual(result.rows.map(row => row.ticker), ['AAA']);
  assert.equal(result.rows[0].pattern, 'horizontal');
  assert.equal(result.filteredOut, 1);
  assert.throws(() => calculateFinvizContract({ rows, filterQuery: 'ta_pattern_not-real', order: 'ticker' }), /Unsupported pattern/);
});

test('Stock Rover-style factor constructor requires complete dated inputs and midranks ties', () => {
  const header = ['Ticker', 'Sector', 'AsOf', ...stockRoverFactorMetrics.map(metric => metric.key)].join(',');
  const row = (ticker, value) => [ticker, 'Technology', '2026-10-30', ...stockRoverFactorMetrics.map(metric => metric.key === 'PriceTo52WeekHigh' ? 0.5 : value)].join(',');
  const parsed = parseStockRoverFactorCsv(`${header}\n${row('AAA', 1)}\n${row('BBB', 2)}\n`);
  const result = calculateStockRoverFactorScores(parsed.rows);
  assert.equal(parsed.asOf, '2026-10-30');
  assert.equal(result.fullyScored, 2);
  assert.equal(result.rows[0].ticker, 'BBB');
  assert.ok(result.rows[0].composite > result.rows[1].composite);
  assert.ok(result.rows.every(row => row.completedCategories === 4));
  assert.throws(() => parseStockRoverFactorCsv(`${header}\n${row('AAA', 1)}\n${row('AAA', 2)}\n`), /Duplicate ticker/);
});

test('manual confluence aggregation reports missing data and enforces qualification', () => {
  const full = Object.fromEntries(confluenceCategories.flatMap(category => category.metrics.map(([key]) => [key, 70])));
  const qualified = computeConfluenceCandidate({ scores: full, qualified: true, dataConfidence: 90, realIndexCount: 6 });
  assert.equal(qualified.metricCount, 55);
  assert.equal(qualified.score, 70);
  assert.equal(qualified.status, 'qualified');
  assert.equal(computeConfluenceCandidate({}).status, 'insufficient-data');
  assert.equal(computeConfluenceCandidate({ scores: { rsMarket: 101 } }).status, 'invalid-input');
});

test('portfolio constructor is not account data and dated replay requires declared complete snapshots', () => {
  const input = 'Ticker,Score,Sector,LowRisk,Avg3MVolume,ProvenBuySignal,AsOf,SnapshotComplete\nABC,8,Technology,6,150000,true,2026-10-30,true\n';
  const parsed = parseDanelfinCsv(input);
  const portfolio = buildDanelfinPortfolio(parsed.rows);
  assert.equal(portfolio.chosen.length, 1);
  assert.equal(portfolio.chosen[0].ticker, 'ABC');
  assert.equal(portfolio.chosen[0].weightPct, 100);
  const plan = buildDanelfinRebalancePlan(parsed.rows, parsed.startDate);
  assert.equal(plan.events[0].status, 'INITIAL_ALLOCATION');
  assert.equal(plan.events[0].selectedTickers[0], 'ABC');
  const tooThin = parseDanelfinCsv(input.replace('150000', '100000'));
  assert.equal(buildDanelfinPortfolio(tooThin.rows).chosen.length, 0, 'the eligibility boundary is strictly above 100,000');
});

test('SMA replay uses only explicit inputs and rejects invalid window/cost parameters', () => {
  const rows = parseStrategyCsv('Date,Close\n2026-01-01,10\n2026-01-02,11\n2026-01-03,12\n2026-01-04,13\n2026-01-05,14\n2026-01-06,15\n');
  const result = analyzeStrategy({ rows, fast: 2, slow: 3, costBps: 10, splitPct: 70, periodsPerYear: 252 });
  assert.equal(result.error, undefined);
  assert.equal(result.records.length, 2);
  assert.equal(result.records[0].date, '2026-01-05');
  assert.ok(result.overall.totalReturn > 0);
  assert.match(analyzeStrategy({ rows, fast: 2, slow: 2, costBps: 0, splitPct: 70, periodsPerYear: 252 }).error, /Slow average/);
  assert.throws(() => parseStrategyCsv('Date,Close\n2026-01-01,-1\n2026-01-02,2\n'), /non-positive/);
});

test('daily-change evaluator returns a pure state transition equivalent to legacy persistence behavior', () => {
  const alerts = [
    { id: 'a', ticker: 'ABC', condition: 'change', threshold: 5 },
    { id: 'b', ticker: 'XYZ', condition: 'change', threshold: 5 },
    { id: 'c', ticker: 'ABC', condition: 'premium', threshold: 1 },
  ];
  const feed = { symbol: 'ABC', bars: [
    { at: '2026-10-29T00:00:00Z', close: 100 },
    { at: '2026-10-30T00:00:00Z', close: 106 },
  ] };
  const updated = evaluateChangeAlerts(alerts, feed);
  assert.notEqual(updated, alerts);
  assert.equal(updated[0].lastEvaluation.barAt, feed.bars[1].at);
  assert.ok(Math.abs(updated[0].lastEvaluation.changePct - 6) < 1e-12);
  assert.equal(updated[0].lastEvaluation.matched, true);
  assert.equal(updated[1], alerts[1]);
  assert.equal(updated[2], alerts[2]);
  const oldState = { alerts: structuredClone(alerts) }; let persisted = 0;
  const oldFunction = feedValue => {
    const bars = Array.isArray(feedValue?.bars) ? feedValue.bars : [];
    if (bars.length < 2) return;
    const latest = bars.at(-1), previous = bars.at(-2);
    if (!(previous.close > 0) || !Number.isFinite(latest.close)) return;
    const changePct = (latest.close / previous.close - 1) * 100;
    let changed = false;
    oldState.alerts = oldState.alerts.map(alert => {
      if (alert.condition !== 'change' || alert.ticker !== feedValue.symbol) return alert;
      changed = true;
      return { ...alert, lastEvaluation: { barAt: latest.at, changePct, matched: Math.abs(changePct) >= Number(alert.threshold) } };
    });
    if (changed) persisted++;
  };
  oldFunction(feed);
  assert.deepEqual(updated, oldState.alerts, 'source mutation converted to return value preserves result');
  assert.equal(persisted, 1, 'host persistence remains outside the pure module');
});

test('generic convergence evidence parser accepts documented schema and rejects unknown columns', () => {
  const ok = parseEvidenceCsv('ObservedAt,Entity,Source,Metric,Value,PublicAt\n2026-10-30T16:00:00Z,ABC,user,close,10,2026-10-30T16:00:00Z\n');
  assert.equal(ok.acceptedCount, 1);
  assert.equal(ok.records[0].Entity, 'ABC');
  assert.throws(() => parseEvidenceCsv('Date,Ticker,Secret\n2026-10-30,ABC,x\n'), /unrecognized column/);
});

test('public-reference macro parsers map only synthetic Treasury, Fed and Cboe rows', () => {
  const nominal = '<title>DailyTreasuryYieldCurveRateData</title><entry><d:NEW_DATE>2026-10-29</d:NEW_DATE><d:BC_2YEAR>3.5</d:BC_2YEAR><d:BC_10YEAR>4.1</d:BC_10YEAR><d:BC_30YEAR>4.7</d:BC_30YEAR></entry>';
  const parsedNominal = parseTreasuryCurve(nominal, '2026-10-30T00:00:00Z', '2026-10-29');
  assert.equal(parsedNominal.observations[0].ten_year, 4.1);
  const real = '<title>DailyTreasuryRealYieldCurveRateData</title><entry><d:NEW_DATE>2026-10-29</d:NEW_DATE><d:TC_5YEAR>1.2</d:TC_5YEAR><d:TC_10YEAR>1.7</d:TC_10YEAR><d:TC_30YEAR>2.0</d:TC_30YEAR></entry>';
  assert.equal(parseTreasuryRealCurve(real, '2026-10-30T00:00:00Z', '2026-10-29').observations[0].five_year, 1.2);
  const fed = 'Nominal Broad Dollar Index\nH10/H10/JRXWTFB_N.B\nTime Period\n2026-10-29,120.1,110.2,130.4\n';
  assert.equal(parseFedDollarIndex(fed, '2026-10-30T00:00:00Z', '2026-10-29').observations[0].broad, 120.1);
  const cboe = 'DATE,OPEN,HIGH,LOW,CLOSE\n10/29/2026,18,20,17,19\n';
  assert.equal(parseCboeIndexCsv(cboe, 'VIX', '2026-10-30T00:00:00Z', '2026-10-29').observations[0].close, 19);
  assert.equal(parseCboeIndexCsv(cboe, 'UNKNOWN', '2026-10-30T00:00:00Z', '2026-10-29'), null);
});
