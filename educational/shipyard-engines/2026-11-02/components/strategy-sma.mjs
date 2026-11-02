// Local CSV SMA replay; inputs are user-provided, execution delayed one bar, no orders.
import { parseCsvRows } from './shared/csv.mjs';

export function parseStrategyCsv(source) {
  if (source.length > 20 * 1024 * 1024) throw new Error('CSV files must be 20 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 3 || table.length > 100001) throw new Error('Use a CSV with a header and between 2 and 100,000 data rows.');
  const header = table[0].map(value => value.trim().toLowerCase().replace(/[^a-z0-9]/g, ''));
  const dateIndex = header.findIndex(value => ['date', 'datetime', 'timestamp', 'time'].includes(value));
  const closeIndex = header.findIndex(value => ['close', 'adjclose', 'adjustedclose', 'last'].includes(value));
  if (dateIndex < 0 || closeIndex < 0) throw new Error('Required CSV columns: Date (or Timestamp) and Close (or Adj Close).');
  const rows = [];
  for (let i = 1; i < table.length; i++) {
    const date = String(table[i][dateIndex] || '').trim();
    const rawClose = String(table[i][closeIndex] || '').trim();
    if (!date && !rawClose) continue;
    if (!date || !rawClose) throw new Error(`Row ${i + 1} is missing its date or close value.`);
    const timestamp = Date.parse(date);
    const close = Number(rawClose.replace(/[$,]/g, ''));
    if (!Number.isFinite(timestamp)) throw new Error(`Row ${i + 1} has an unreadable date/time value.`);
    if (!Number.isFinite(close) || close <= 0) throw new Error(`Row ${i + 1} has a non-positive or invalid close value.`);
    rows.push({ date, timestamp, close });
  }
  if (rows.length < 2) throw new Error('The CSV needs at least two valid observations.');
  rows.sort((a, b) => a.timestamp - b.timestamp);
  for (let i = 1; i < rows.length; i++) {
    if (rows[i].timestamp === rows[i - 1].timestamp) throw new Error(`Duplicate timestamp: ${rows[i].date}.`);
  }
  return rows.map(({ date, close }) => ({ date, close }));
}

export function rollingMean(values, period) {
  let sum = 0;
  return values.map((value, index) => {
    sum += value;
    if (index >= period) sum -= values[index - period];
    return index + 1 >= period ? sum / period : null;
  });
}

export function strategyStats(records, periodsPerYear) {
  if (!records.length) return null;
  let equity = 1, benchmark = 1, highWater = 1, maxDrawdown = 0, wins = 0, exposure = 0;
  for (const record of records) {
    equity *= Math.max(0, 1 + record.net);
    benchmark *= Math.max(0, 1 + record.gross);
    highWater = Math.max(highWater, equity);
    maxDrawdown = Math.min(maxDrawdown, highWater > 0 ? equity / highWater - 1 : -1);
    if (record.net > 0) wins++;
    exposure += record.position;
  }
  const cagr = equity > 0 ? Math.pow(equity, periodsPerYear / records.length) - 1 : -1;
  return { totalReturn: equity - 1, benchmarkReturn: benchmark - 1, cagr, maxDrawdown, winBars: wins / records.length, exposure: exposure / records.length, bars: records.length };
}

export function analyzeStrategy(p) {
  const rows = p.rows;
  const fast = Number(p.fast), slow = Number(p.slow), costBps = Number(p.costBps);
  const splitPct = Number(p.splitPct), periodsPerYear = Number(p.periodsPerYear);
  if (!Number.isInteger(fast) || fast < 2 || fast > 5000) return { error: 'Fast average must be a whole number from 2 to 5,000.' };
  if (!Number.isInteger(slow) || slow <= fast || slow > 5000) return { error: 'Slow average must be a whole number greater than the fast average and no more than 5,000.' };
  if (rows.length < slow + 3) return { error: `This dataset has ${rows.length} bars; at least ${slow + 3} are required for the slow average and delayed returns.` };
  if (!Number.isFinite(costBps) || costBps < 0 || costBps > 2000) return { error: 'Estimated cost must be between 0 and 2,000 basis points per side.' };
  if (!Number.isInteger(splitPct) || splitPct < 50 || splitPct > 90) return { error: 'Out-of-sample split must be from 50% to 90%.' };
  if (!Number.isInteger(periodsPerYear) || periodsPerYear < 1 || periodsPerYear > 10000) return { error: 'Bars per year must be from 1 to 10,000.' };

  const closes = rows.map(record => record.close);
  const fastMeans = rollingMean(closes, fast);
  const slowMeans = rollingMean(closes, slow);
  const desired = closes.map((_, i) => fastMeans[i] !== null && slowMeans[i] !== null && fastMeans[i] > slowMeans[i] ? 1 : 0);
  const records = [];
  let held = 0;
  for (let i = slow; i < rows.length - 1; i++) {
    const position = desired[i - 1];
    const turnover = Math.abs(position - held);
    const gross = closes[i + 1] / closes[i] - 1;
    const net = Math.max(-1, gross * position - turnover * costBps / 10000);
    records.push({
      date: rows[i + 1].date,
      close: closes[i + 1],
      fast: fastMeans[i],
      slow: slowMeans[i],
      position,
      turnover,
      gross,
      net,
    });
    held = position;
  }
  if (records.length && held === 1) {
    const last = records[records.length - 1];
    last.turnover += 1;
    last.net = Math.max(-1, last.net - costBps / 10000);
  }
  const split = Math.min(records.length - 1, Math.max(1, Math.floor(records.length * splitPct / 100)));
  return {
    records,
    overall: strategyStats(records, periodsPerYear),
    inSample: strategyStats(records.slice(0, split), periodsPerYear),
    outOfSample: strategyStats(records.slice(split), periodsPerYear),
    split,
  };
}
