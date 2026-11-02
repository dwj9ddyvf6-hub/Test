// Local-input analytical model. No live chain acquisition or provider adapter.
import { parseCsvRows } from './shared/csv.mjs';

export function parseStaticGexCsv(source) {
  if (source.length > 10 * 1024 * 1024) throw new Error('Option-chain CSV files must be 10 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 2 || table.length > 5001) throw new Error('Use a header and between 1 and 5,000 option rows.');
  const header = table[0].map(value => value.trim().toLowerCase().replace(/[^a-z0-9]/g, ''));
  const column = (...aliases) => header.findIndex(name => aliases.includes(name));
  const indexes = {
    ticker: column('ticker', 'symbol', 'underlying'),
    asOf: column('asof', 'date', 'snapshotdate'),
    spot: column('spot', 'underlyingprice', 'underlyingclose'),
    strike: column('strike', 'strikeprice'),
    type: column('type', 'optiontype', 'right'),
    oi: column('oi', 'openinterest'),
    iv: column('iv', 'impliedvolatility', 'ivpercent'),
    dte: column('dte', 'daystoexpiry', 'daystoexpiration'),
  };
  const missing = ['ticker', 'asOf', 'spot', 'strike', 'type', 'oi', 'iv', 'dte'].filter(key => indexes[key] < 0);
  if (missing.length) throw new Error(`Missing required columns: ${missing.join(', ')}. Expected Ticker, AsOf, Spot, Strike, Type, OpenInterest, IV, DTE.`);
  const rows = [], seenContracts = new Set();
  let snapshotTicker = '', snapshotDate = '', snapshotSpot = null;
  const numberAt = (cells, index, label, rowNumber) => {
    const raw = String(cells[index] ?? '').trim().replace(/[$,%\s,]/g, '');
    const value = Number(raw);
    if (!raw || !Number.isFinite(value)) throw new Error(`Row ${rowNumber}: ${label} must be a finite number.`);
    return value;
  };
  for (let i = 1; i < table.length; i++) {
    const cells = table[i];
    if (!cells.some(value => String(value).trim())) continue;
    const rowNumber = i + 1;
    const ticker = String(cells[indexes.ticker] || '').trim().toUpperCase();
    if (!/^[A-Z0-9.^/-]{1,16}$/.test(ticker)) throw new Error(`Row ${rowNumber}: ticker/symbol is missing or invalid.`);
    const asOfRaw = String(cells[indexes.asOf] || '').trim();
    const asOfTime = Date.parse(asOfRaw);
    if (!Number.isFinite(asOfTime)) throw new Error(`Row ${rowNumber}: AsOf must be a readable snapshot date.`);
    const asOf = new Date(asOfTime).toISOString().slice(0, 10);
    const spot = numberAt(cells, indexes.spot, 'Spot', rowNumber);
    const strike = numberAt(cells, indexes.strike, 'Strike', rowNumber);
    const openInterest = numberAt(cells, indexes.oi, 'OpenInterest', rowNumber);
    const ivPct = numberAt(cells, indexes.iv, 'IV (%)', rowNumber);
    const dte = numberAt(cells, indexes.dte, 'DTE', rowNumber);
    const rawType = String(cells[indexes.type] || '').trim().toLowerCase();
    const type = ['c', 'call'].includes(rawType) ? 'CALL' : ['p', 'put'].includes(rawType) ? 'PUT' : '';
    if (!type) throw new Error(`Row ${rowNumber}: Type must be Call/C or Put/P.`);
    if (spot <= 0 || strike <= 0 || spot > 1000000 || strike > 1000000) throw new Error(`Row ${rowNumber}: Spot and Strike must be positive and no greater than 1,000,000.`);
    if (openInterest < 0 || !Number.isInteger(openInterest) || openInterest > 1e12) throw new Error(`Row ${rowNumber}: OpenInterest must be a whole number from 0 to 1,000,000,000,000.`);
    if (ivPct < 0.1 || ivPct > 500) throw new Error(`Row ${rowNumber}: IV must be between 0.1 and 500 percent.`);
    if (dte < 0.01 || dte > 3650) throw new Error(`Row ${rowNumber}: DTE must be at least 0.01 and at most 3,650 days; zero-DTE rows are unsupported.`);
    if (!snapshotTicker) { snapshotTicker = ticker; snapshotDate = asOf; snapshotSpot = spot; }
    if (ticker !== snapshotTicker || asOf !== snapshotDate || Math.abs(spot - snapshotSpot) > 0.005) throw new Error('Use one underlying, one AsOf date, and one consistent Spot value per CSV.');
    const contractKey = `${strike.toFixed(4)}:${type}:${dte.toFixed(4)}`;
    if (seenContracts.has(contractKey)) throw new Error(`Row ${rowNumber}: duplicate ${ticker} ${type} contract at strike ${strike} and DTE ${dte}.`);
    seenContracts.add(contractKey);
    rows.push({ ticker, asOf, spot, strike, type, openInterest, ivPct, dte });
  }
  if (!rows.length) throw new Error('The CSV contains no option rows.');
  return { rows, ticker: snapshotTicker, asOf: snapshotDate, spot: snapshotSpot };
}

export function blackScholesGamma(spot, strike, dte, ivPct, rate, dividendYield) {
  const years = dte / 365;
  const sigma = ivPct / 100;
  const denominator = spot * sigma * Math.sqrt(years);
  if (!(denominator > 0)) return 0;
  // d1 is dimensionless; spot appears only in the final gamma denominator.
  const d1 = (Math.log(spot / strike) + (rate - dividendYield + 0.5 * sigma * sigma) * years) / (sigma * Math.sqrt(years));
  return Math.exp(-dividendYield * years) * Math.exp(-0.5 * d1 * d1) / (Math.sqrt(2 * Math.PI) * denominator);
}

export function buildStaticGexSnapshot(rows, settings) {
  const rate = settings.riskFreeRatePct / 100;
  const dividendYield = settings.dividendYieldPct / 100;
  const multiplier = settings.multiplier;
  const optionRowsAt = spot => rows.map(row => {
    const gamma = blackScholesGamma(spot, row.strike, row.dte, row.ivPct, rate, dividendYield);
    const sign = row.type === 'CALL' ? 1 : -1;
    const dollarGex = gamma * sign * row.openInterest * multiplier * spot * spot * 0.01;
    return { ...row, gamma, dollarGex };
  });
  const netGexAt = spot => {
    let net = 0;
    for (const row of rows) {
      const gamma = blackScholesGamma(spot, row.strike, row.dte, row.ivPct, rate, dividendYield);
      net += gamma * (row.type === 'CALL' ? 1 : -1) * row.openInterest * multiplier * spot * spot * 0.01;
    }
    return net;
  };
  const optionRows = optionRowsAt(settings.spot);
  const strikeMap = new Map();
  for (const row of optionRows) {
    const key = row.strike.toFixed(4);
    if (!strikeMap.has(key)) strikeMap.set(key, { strike: row.strike, callGex: 0, putGex: 0, netGex: 0 });
    const item = strikeMap.get(key);
    if (row.type === 'CALL') item.callGex += row.dollarGex;
    else item.putGex += row.dollarGex;
    item.netGex += row.dollarGex;
  }
  const strikes = [...strikeMap.values()].sort((a, b) => a.strike - b.strike);
  const callWall = strikes.filter(row => row.callGex > 0).sort((a, b) => b.callGex - a.callGex || a.strike - b.strike)[0] || null;
  const putWall = strikes.filter(row => row.putGex < 0).sort((a, b) => Math.abs(b.putGex) - Math.abs(a.putGex) || a.strike - b.strike)[0] || null;
  const netGex = optionRows.reduce((sum, row) => sum + row.dollarGex, 0);
  const extent = settings.gridRangePct / 100;
  const steps = 101;
  const grid = Array.from({ length: steps }, (_, i) => settings.spot * (1 - extent + 2 * extent * i / (steps - 1)));
  const profile = grid.map(spot => ({ spot, net: netGexAt(spot) }));
  const crossings = [];
  for (let i = 1; i < profile.length; i++) {
    const before = profile[i - 1], after = profile[i];
    // Exact zeros count only when bracketed by opposite signs. An empty or
    // perfectly offset inventory has no unique zero-gamma crossing.
    if (i > 1 && before.net === 0 && profile[i - 2].net !== 0 && after.net !== 0 && Math.sign(profile[i - 2].net) !== Math.sign(after.net)) crossings.push(before.spot);
    if (before.net !== 0 && after.net !== 0 && Math.sign(before.net) !== Math.sign(after.net)) {
      const fraction = Math.abs(before.net) / (Math.abs(before.net) + Math.abs(after.net));
      crossings.push(before.spot + fraction * (after.spot - before.spot));
    }
  }
  const zeroGamma = crossings.sort((a, b) => Math.abs(a - settings.spot) - Math.abs(b - settings.spot))[0] ?? null;
  return { optionRows, strikes, netGex, callWall, putWall, zeroGamma, crossingCount: crossings.length };
}
