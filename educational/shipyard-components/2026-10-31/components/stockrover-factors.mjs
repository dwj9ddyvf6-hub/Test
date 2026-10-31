// User-supplied factor CSV; desk-defined equal-weight ranking, not vendor model access.
import { parseCsvRows } from './shared/csv.mjs';
import { normalizeTicker } from './shared/input-validation.mjs';

export const stockRoverFactorCategories = [
  { key: 'value', label: 'Value', metrics: [
    { key: 'EVEBITDA', label: 'EV / EBITDA', lowerBetter: true },
    { key: 'PE', label: 'P / E', lowerBetter: true },
    { key: 'EPSPredictabilityR1', label: 'EPS predictability · R1', lowerBetter: false },
    { key: 'PriceTangibleBook', label: 'Price / tangible book', lowerBetter: true, sectorRelative: true },
    { key: 'PriceSales', label: 'Price / sales', lowerBetter: true, sectorRelative: true },
  ] },
  { key: 'growth', label: 'Growth', metrics: [
    { key: 'RevenueGrowth5Y', label: '5Y revenue growth' },
    { key: 'NetIncomeGrowth5Y', label: '5Y net income growth' },
    { key: 'ForwardEBITDAGrowth', label: 'Forward EBITDA growth' },
    { key: 'ForwardSalesGrowth', label: 'Forward sales growth' },
    { key: 'ForwardEPSGrowth', label: 'Forward EPS growth' },
  ] },
  { key: 'quality', label: 'Quality', metrics: [
    { key: 'ROIC', label: 'ROIC' },
    { key: 'NetMargin', label: 'Net margin' },
    { key: 'GrossMargin', label: 'Gross margin' },
    { key: 'InterestCoverage', label: 'Interest coverage' },
    { key: 'DebtEquity', label: 'Debt / equity', lowerBetter: true },
  ] },
  { key: 'sentiment', label: 'Sentiment', metrics: [
    { key: 'ShortInterestRatio', label: 'Short interest ratio', lowerBetter: true },
    { key: 'Return1M', label: '1M total return' },
    { key: 'Return3M', label: '3M total return' },
    { key: 'Return6M', label: '6M total return' },
    { key: 'Return12M', label: '12M total return' },
    { key: 'PriceTo52WeekHigh', label: 'Price / 52-week high' },
    { key: 'DaysSince52WeekHigh', label: 'Days since 52-week high', lowerBetter: true },
    { key: 'NormalizedMACDSignal', label: 'Normalized MACD signal · R3' },
  ] },
];

export const stockRoverFactorMetrics = stockRoverFactorCategories.flatMap(category => category.metrics);

export function parseStockRoverFactorCsv(source) {
  if (source.length > 10 * 1024 * 1024) throw new Error('Factor snapshot CSV files must be 10 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 2 || table.length > 10001) throw new Error('Use a header and between 1 and 10,000 company rows.');
  const header = table[0].map(value => value.trim().toLowerCase().replace(/[^a-z0-9]/g, ''));
  if (new Set(header).size !== header.length) throw new Error('The CSV has duplicate columns after header normalization.');
  const find = (...aliases) => header.findIndex(value => aliases.includes(value));
  const tickerIndex = find('ticker', 'symbol');
  const sectorIndex = find('sector');
  const asOfIndex = find('asof', 'snapshotdate', 'date');
  if (tickerIndex < 0 || sectorIndex < 0 || asOfIndex < 0) throw new Error('Required columns: Ticker, Sector, and AsOf (or SnapshotDate / Date).');
  const metricIndexes = new Map(stockRoverFactorMetrics.map(metric => [metric.key, find(metric.key.toLowerCase())]));
  const absent = [...metricIndexes].filter(([, index]) => index < 0).map(([key]) => key);
  if (absent.length) throw new Error(`Add all ${stockRoverFactorMetrics.length} factor columns; missing: ${absent.join(', ')}.`);
  const rows = [], seen = new Set();
  let snapshotDate = '';
  for (let i = 1; i < table.length; i++) {
    const line = table[i], rawTicker = String(line[tickerIndex] ?? '').trim();
    if (!rawTicker) throw new Error(`Row ${i + 1} is missing its ticker.`);
    const ticker = normalizeTicker(rawTicker);
    if (!ticker) throw new Error(`Row ${i + 1} has an invalid ticker: ${rawTicker}.`);
    if (seen.has(ticker)) throw new Error(`Duplicate ticker: ${ticker}.`);
    seen.add(ticker);
    const sector = String(line[sectorIndex] ?? '').trim();
    if (!sector) throw new Error(`Row ${i + 1} is missing its sector.`);
    const asOf = String(line[asOfIndex] ?? '').trim();
    const parsedAsOf = /^\d{4}-\d{2}-\d{2}$/.test(asOf) ? new Date(`${asOf}T00:00:00Z`) : null;
    if (!parsedAsOf || !Number.isFinite(parsedAsOf.getTime()) || parsedAsOf.toISOString().slice(0, 10) !== asOf) throw new Error(`Row ${i + 1} needs a valid AsOf date in YYYY-MM-DD format.`);
    if (snapshotDate && asOf !== snapshotDate) throw new Error(`Mixed snapshot dates: ${snapshotDate} and ${asOf}. Load one decision-date cross section at a time.`);
    snapshotDate = asOf;
    const raw = {};
    for (const [key, index] of metricIndexes) {
      const cell = String(line[index] ?? '').trim();
      if (!cell || ['NA', 'N/A', 'NULL', '—', '-'].includes(cell.toUpperCase())) { raw[key] = null; continue; }
      const value = Number(cell.replace(/,/g, ''));
      if (!Number.isFinite(value)) throw new Error(`Row ${i + 1} has an invalid numeric value in ${key}.`);
      raw[key] = value;
    }
    if (raw.PriceTo52WeekHigh !== null && (raw.PriceTo52WeekHigh < 0 || raw.PriceTo52WeekHigh > 1)) throw new Error(`Row ${i + 1}: PriceTo52WeekHigh must be a ratio from 0 to 1.`);
    if (raw.DaysSince52WeekHigh !== null && raw.DaysSince52WeekHigh < 0) throw new Error(`Row ${i + 1}: DaysSince52WeekHigh cannot be negative.`);
    rows.push({ ticker, sector, asOf, raw });
  }
  if (!rows.length) throw new Error('The factor snapshot contains no company rows.');
  return { rows, asOf: snapshotDate };
}

export function calculateStockRoverFactorScores(sourceRows) {
  const rows = sourceRows.map(row => ({ ...row, percentiles: {}, categoryScores: {}, composite: null }));
  for (const metric of stockRoverFactorMetrics) {
    const groups = new Map();
    rows.forEach((row, index) => {
      const value = row.raw?.[metric.key];
      if (!Number.isFinite(value)) return;
      const groupKey = metric.sectorRelative ? row.sector.trim().toLowerCase() : '*';
      if (!groups.has(groupKey)) groups.set(groupKey, []);
      groups.get(groupKey).push({ row, index, value });
    });
    for (const group of groups.values()) {
      group.sort((a, b) => a.value - b.value || a.index - b.index);
      for (let start = 0; start < group.length;) {
        let end = start + 1;
        while (end < group.length && group[end].value === group[start].value) end++;
        const midrank = (start + end - 1) / 2;
        const ascendingPercentile = group.length === 1 ? 50 : 100 * midrank / (group.length - 1);
        const score = metric.lowerBetter ? 100 - ascendingPercentile : ascendingPercentile;
        for (let i = start; i < end; i++) group[i].row.percentiles[metric.key] = score;
        start = end;
      }
    }
  }
  for (const row of rows) {
    for (const category of stockRoverFactorCategories) {
      const scores = category.metrics.map(metric => row.percentiles[metric.key]);
      row.categoryScores[category.key] = scores.every(Number.isFinite) ? scores.reduce((sum, value) => sum + value, 0) / scores.length : null;
    }
    const categoryScores = stockRoverFactorCategories.map(category => row.categoryScores[category.key]);
    row.completedCategories = categoryScores.filter(Number.isFinite).length;
    row.missingMetrics = stockRoverFactorMetrics.filter(metric => !Number.isFinite(row.percentiles[metric.key])).length;
    row.composite = row.completedCategories === stockRoverFactorCategories.length ? categoryScores.reduce((sum, value) => sum + value, 0) / categoryScores.length : null;
  }
  const scored = rows.filter(row => Number.isFinite(row.composite)).map(row => row.composite).sort((a, b) => a - b);
  const median = scored.length ? (scored.length % 2 ? scored[(scored.length - 1) / 2] : (scored[scored.length / 2 - 1] + scored[scored.length / 2]) / 2) : null;
  const ordered = [...rows].sort((a, b) => {
    if (Number.isFinite(a.composite) && Number.isFinite(b.composite)) return b.composite - a.composite || a.ticker.localeCompare(b.ticker);
    if (Number.isFinite(a.composite)) return -1;
    if (Number.isFinite(b.composite)) return 1;
    return a.ticker.localeCompare(b.ticker);
  });
  return { rows: ordered, sourceCount: rows.length, fullyScored: scored.length, medianComposite: median, top: ordered.find(row => Number.isFinite(row.composite)) || null };
}
