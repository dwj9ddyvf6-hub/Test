import assert from 'node:assert/strict';
import test from 'node:test';
import { formatSessionDate, formatSessionTimestamp, formatUtcTimestamp, lineChartAxisLayout, shouldRefreshAt, summarizeDailyBars } from '../dist/market-overview.mjs';
import { selectCompletedDailyBars, simpleAtr14, simpleMovingAverage, simpleRsi14 } from '../dist/research-adapters.mjs';

test('daily summary sorts bars, keeps the last duplicate, and calculates change from the prior close', () => {
  const bars = [
    { at: '2026-10-28T04:00:00.000Z', open: 102, high: 106, low: 101, close: 105, volume: 300 },
    { at: '2026-10-27T04:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
    { at: '2026-10-28T04:00:00.000Z', open: 102, high: 107, low: 101, close: 106, volume: 301 },
  ];
  const before = structuredClone(bars);
  const summary = summarizeDailyBars(bars);
  assert.deepEqual(summary.bars.map(bar => bar.at), ['2026-10-27T04:00:00.000Z', '2026-10-28T04:00:00.000Z']);
  assert.equal(summary.latest.close, 106);
  assert.equal(summary.latest.volume, 301);
  assert.equal(summary.previous.close, 100);
  assert.ok(Math.abs(summary.changePct - 6) < 1e-12);
  assert.equal(summary.range, 6);
  assert.deepEqual(bars, before, 'input rows remain unchanged');
});

test('invalid OHLC rows and duplicate timestamps do not create false metrics', () => {
  const summary = summarizeDailyBars([
    { at: '2026-10-27T04:00:00Z', open: 100, high: 99, low: 98, close: 100, volume: 10 },
    { at: 'bad timestamp', open: 100, high: 102, low: 98, close: 101, volume: 10 },
    { at: '2026-10-28T04:00:00Z', open: 100, high: 102, low: 98, close: 101, volume: -1 },
    { at: '2026-10-29T04:00:00Z', open: 100, high: 102, low: 98, close: 101, volume: 10.5 },
  ]);
  assert.equal(summary.latest, null);
  assert.equal(summary.changePct, null);
  assert.equal(summary.range, null);
});

test('auto refresh is due when a feed is missing or older than its interval', () => {
  const now = Date.parse('2026-10-28T22:00:00.000Z');
  assert.equal(shouldRefreshAt(null, now, 300_000), true);
  assert.equal(shouldRefreshAt('2026-10-28T21:55:01.000Z', now, 300_000), false);
  assert.equal(shouldRefreshAt('2026-10-28T21:55:00.000Z', now, 300_000), true);
});

test('market timestamps keep their exchange date across visitor time zones', () => {
  assert.equal(formatSessionDate('2026-10-28T04:00:00.000Z', { year: 'numeric' }), 'Oct 28, 2026');
  assert.equal(formatSessionTimestamp('2026-10-28T23:41:00.000Z'), 'Oct 28, 2026, 7:41 PM EDT');
  assert.equal(formatUtcTimestamp('2026-10-28T23:41:00.000Z'), 'Oct 28, 2026, 11:41 PM UTC');
  assert.equal(formatSessionDate('bad timestamp'), '—');
});

test('line chart reserves readable y-axis space on narrow screens', () => {
  assert.deepEqual(lineChartAxisLayout(390), { compact: true, leftPadding: 108, labelX: 100, labelAnchor: 'end' });
  assert.deepEqual(lineChartAxisLayout(560), { compact: true, leftPadding: 108, labelX: 100, labelAnchor: 'end' });
  assert.deepEqual(lineChartAxisLayout(561), { compact: false, leftPadding: 48, labelX: 4, labelAnchor: 'start' });
  assert.deepEqual(lineChartAxisLayout(Number.NaN), { compact: false, leftPadding: 48, labelX: 4, labelAnchor: 'start' });
});

test('overview close metrics use completed sessions while today’s bar is still forming', () => {
  const bars = [
    { at: '2026-10-27T04:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
    { at: '2026-10-28T04:00:00.000Z', open: 102, high: 108, low: 101, close: 107, volume: 300 },
  ];
  const duringSession = selectCompletedDailyBars(bars, new Date('2026-10-28T19:00:00.000Z'));
  assert.equal(duringSession.currentSessionBarExcluded, true);
  assert.equal(summarizeDailyBars(duringSession.bars).latest.close, 100);
  const afterCutoff = selectCompletedDailyBars(bars, new Date('2026-10-28T20:16:00.000Z'));
  assert.equal(afterCutoff.currentSessionBarExcluded, false);
  assert.equal(summarizeDailyBars(afterCutoff.bars).latest.close, 107);
});

test('NYSE fallback early-close bars become eligible 15 minutes after the scheduled close', () => {
  const cases = [
    ['2026-11-27', '2026-11-27T18:14:59.000Z', '2026-11-27T18:15:00.000Z'],
    ['2026-12-24', '2026-12-24T18:14:59.000Z', '2026-12-24T18:15:00.000Z'],
    ['2027-11-26', '2027-11-26T18:14:59.000Z', '2027-11-26T18:15:00.000Z'],
    ['2028-07-03', '2028-07-03T17:14:59.000Z', '2028-07-03T17:15:00.000Z'],
    ['2028-11-24', '2028-11-24T18:14:59.000Z', '2028-11-24T18:15:00.000Z'],
  ];
  for (const [date, before, cutoff] of cases) {
    const bars = [
      { at: '2026-10-28T17:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
      { at: `${date}T17:00:00.000Z`, open: 102, high: 108, low: 101, close: 107, volume: 300 },
    ];
    const beforeCutoff = selectCompletedDailyBars(bars, new Date(before));
    assert.equal(beforeCutoff.currentSessionBarExcluded, true, `${date}: the daily bar remains excluded before 13:15 ET`);
    assert.equal(beforeCutoff.scheduledCloseEt, '13:00');
    assert.equal(beforeCutoff.calculationCutoffEt, '13:15');
    assert.equal(beforeCutoff.sessionCalendar, 'nyse_reference_2026_2028');
    assert.equal(summarizeDailyBars(beforeCutoff.bars).latest.close, 100);
    const atCutoff = selectCompletedDailyBars(bars, new Date(cutoff));
    assert.equal(atCutoff.currentSessionBarExcluded, false, `${date}: the bar becomes eligible at 13:15 ET`);
    assert.equal(summarizeDailyBars(atCutoff.bars).latest.close, 107);
  }
});

test('same-day bars on published NYSE holidays and weekends are excluded', () => {
  const dates = [
    '2026-01-01', '2026-01-19', '2026-02-16', '2026-04-03', '2026-05-25',
    '2026-06-19', '2026-07-03', '2026-09-07', '2026-11-26', '2026-12-25',
    '2027-01-01', '2027-01-18', '2027-02-15', '2027-03-26', '2027-05-31',
    '2027-06-18', '2027-07-05', '2027-09-06', '2027-11-25', '2027-12-24',
    '2028-01-17', '2028-02-21', '2028-04-14', '2028-05-29', '2028-06-19',
    '2028-07-04', '2028-09-04', '2028-11-23', '2028-12-25',
    '2026-10-31',
  ];
  for (const date of dates) {
    const bars = [
      { at: '2026-10-28T17:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
      { at: `${date}T17:00:00.000Z`, open: 102, high: 108, low: 101, close: 107, volume: 300 },
    ];
    const result = selectCompletedDailyBars(bars, new Date(`${date}T17:00:00.000Z`));
    assert.equal(result.nonTradingDateBarExcluded, true, `${date} must not be treated as a trading session`);
    assert.equal(result.latestDateBarExcluded, true);
    assert.equal(result.bars.at(-1).close, 100);
  }
});

test('unpublished future dates keep the conservative 16:15 ET weekday cutoff', () => {
  const bars = [
    { at: '2029-11-22T17:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
    { at: '2029-11-23T17:00:00.000Z', open: 102, high: 108, low: 101, close: 107, volume: 300 },
  ];
  const beforeCutoff = selectCompletedDailyBars(bars, new Date('2029-11-23T19:00:00.000Z'));
  assert.equal(beforeCutoff.currentSessionBarExcluded, true);
  assert.equal(beforeCutoff.sessionCalendar, 'weekday_fallback');
  assert.equal(beforeCutoff.calculationCutoffEt, '16:15');
});

test('Alpaca IEX calendar close overrides the NYSE reference schedule', () => {
  const bars = [
    { at: '2026-11-26T05:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
    { at: '2026-11-27T05:00:00.000Z', open: 102, high: 108, low: 101, close: 107, volume: 300 },
  ];
  const providerCalendar = {
    market: 'IEX', date: '2026-11-27', status: 'open',
    core_end: '2026-11-27T21:00:00.000Z', source: 'alpaca_iex_calendar_v3',
  };
  const beforeProviderCutoff = selectCompletedDailyBars(bars, new Date('2026-11-27T18:30:00.000Z'), providerCalendar);
  assert.equal(beforeProviderCutoff.currentSessionBarExcluded, true, 'the provider close governs even when the NYSE reference closes early');
  assert.equal(beforeProviderCutoff.sessionCalendar, 'alpaca_iex');
  assert.equal(beforeProviderCutoff.scheduledCloseEt, '16:00');
  assert.equal(beforeProviderCutoff.calculationCutoffEt, '16:15');
  assert.equal(beforeProviderCutoff.bars.at(-1).close, 100);
  const afterProviderCutoff = selectCompletedDailyBars(bars, new Date('2026-11-27T21:15:00.000Z'), providerCalendar);
  assert.equal(afterProviderCutoff.currentSessionBarExcluded, false);
  assert.equal(afterProviderCutoff.bars.at(-1).close, 107);
});

test('Alpaca IEX closed status excludes a same-day provider bar', () => {
  const bars = [
    { at: '2026-10-27T04:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
    { at: '2026-10-28T04:00:00.000Z', open: 102, high: 108, low: 101, close: 107, volume: 300 },
  ];
  const result = selectCompletedDailyBars(bars, new Date('2026-10-28T22:00:00.000Z'), {
    market: 'IEX', date: '2026-10-28', status: 'closed', core_end: null, source: 'alpaca_iex_calendar_v3',
  });
  assert.equal(result.nonTradingDateBarExcluded, true);
  assert.equal(result.sessionCalendar, 'alpaca_iex');
  assert.equal(result.bars.at(-1).close, 100);
});

test('a session calendar for another market or date is ignored', () => {
  const bars = [
    { at: '2026-10-27T04:00:00.000Z', open: 99, high: 103, low: 98, close: 100, volume: 200 },
    { at: '2026-10-28T04:00:00.000Z', open: 102, high: 108, low: 101, close: 107, volume: 300 },
  ];
  const wrongMarket = selectCompletedDailyBars(bars, new Date('2026-10-28T19:00:00.000Z'), {
    market: 'NYSE', date: '2026-10-28', status: 'closed', core_end: null,
  });
  const wrongDate = selectCompletedDailyBars(bars, new Date('2026-10-28T19:00:00.000Z'), {
    market: 'IEX', date: '2026-10-27', status: 'closed', core_end: null,
  });
  assert.equal(wrongMarket.sessionCalendar, 'nyse_reference_2026_2028');
  assert.equal(wrongDate.sessionCalendar, 'nyse_reference_2026_2028');
  assert.equal(wrongMarket.currentSessionBarExcluded, true);
  assert.equal(wrongDate.currentSessionBarExcluded, true);
});

test('shared indicator calculations agree on flat, rising, and falling price series', () => {
  assert.equal(simpleMovingAverage(Array.from({ length: 50 }, (_, index) => index + 1), 50), 25.5);
  assert.equal(simpleRsi14(Array(15).fill(100)), 50, 'a flat series has a neutral RSI');
  assert.equal(simpleRsi14(Array.from({ length: 15 }, (_, index) => 100 + index)), 100);
  assert.equal(simpleRsi14(Array.from({ length: 15 }, (_, index) => 100 - index)), 0);
  assert.equal(simpleAtr14(Array.from({ length: 15 }, () => ({ high: 101, low: 99, close: 100 }))), 2);
});
