// Finviz-format lab logic for user-supplied cross-sectional CSV; no vendor API.
import { parseCsvRows } from './shared/csv.mjs';
import { normalizeTicker } from './shared/input-validation.mjs';

const finvizCsvAliases = {
  ticker: ['ticker', 'symbol'], name: ['name', 'company', 'companyname'], securityType: ['securitytype', 'assettype', 'securityclass', 'type'],
  exchange: ['exchange', 'exch'], indexes: ['index', 'indexes', 'indices', 'benchmark'], sector: ['sector', 'sec'], industry: ['industry'],
  country: ['country', 'geo'], marketCap: ['marketcap', 'marketcapitalization', 'marketcapusd'], pe: ['pe', 'peratio', 'priceearnings'],
  price: ['price', 'last', 'close'], avgVolume: ['avgvolume', 'averagevolume', 'avgvol'], relativeVolume: ['relativevolume', 'relvolume', 'relvol'],
  changePct: ['changepct', 'changepercent', 'change'], pattern: ['patterntag', 'pattern', 'chartpattern'], candlestick: ['candlesticktag', 'candlestick', 'candlestickpattern'],
};

function finvizNorm(value) { return String(value ?? '').trim().toLowerCase().replace(/[^a-z0-9]/g, ''); }

function parseFinvizScalar(value) {
  const raw = String(value ?? '').trim();
  if (!raw || ['—', '-', 'n/a', 'na', 'null'].includes(raw.toLowerCase())) return null;
  const match = /^([+\-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([kmbt])?$/i.exec(raw.replace(/[,$%x×\s]/gi, '').replace(/[−–]/g, '-'));
  if (!match) return null;
  const scale = ({ k: 1e3, m: 1e6, b: 1e9, t: 1e12 })[String(match[2] || '').toLowerCase()] || 1;
  const number = Number(match[1]) * scale;
  return Number.isFinite(number) ? number : null;
}

function finvizTagCode(value, candlestick = false) {
  const token = finvizNorm(value);
  const aliases = candlestick
    ? { longlowershadow: 'lls', longuppershadow: 'lus', hammer: 'h', invertedhammer: 'ih', spinningtopwhite: 'stw', spinningtopblack: 'stb', doji: 'd', dragonflydoji: 'dd', gravestonedoji: 'gd', marubozuwhite: 'mw', marubozublack: 'mb' }
    : { horizontalsr: 'horizontal', horizontalsupportresistance: 'horizontal', trendlineresistance: 'tlresistance', trendlinesupport: 'tlsupport', triangleascending: 'wedgeresistance', triangledescending: 'wedgesupport', headandshouldersinverse: 'headandshouldersinv', headandshouldersinverted: 'headandshouldersinv' };
  if (aliases[token]) return aliases[token];
  if (!candlestick && token.endsWith('strong')) {
    const base = token.slice(0, -6);
    const code = aliases[base] || base;
    if (['horizontal', 'tlresistance', 'tlsupport', 'wedgeup', 'wedgedown', 'wedgeresistance', 'wedgesupport', 'wedge', 'channelup', 'channeldown', 'channel'].includes(code)) return `${code}2`;
  }
  return token;
}

function parseFinvizFilterQuery(query) {
  const filters = new Map(); let overrides = 0;
  const knownPatterns = new Set(['horizontal', 'tlresistance', 'tlsupport', 'wedgeup', 'wedgedown', 'wedgeresistance', 'wedgesupport', 'wedge', 'channelup', 'channeldown', 'channel', 'doubletop', 'doublebottom', 'multipletop', 'multiplebottom', 'headandshoulders', 'headandshouldersinv']);
  const knownStrongPatterns = new Set(['horizontal2', 'tlresistance2', 'tlsupport2', 'wedgeup2', 'wedgedown2', 'wedgeresistance2', 'wedgesupport2', 'wedge2', 'channelup2', 'channeldown2', 'channel2']);
  const knownCandles = new Set(['lls', 'lus', 'h', 'ih', 'stw', 'stb', 'd', 'dd', 'gd', 'mw', 'mb']);
  for (const token of String(query || '').split(',').map(value => value.trim().toLowerCase()).filter(Boolean)) {
    const match = /^(ta_pattern|ta_candlestick|exch|sec|geo|idx|cap)_(.+)$/.exec(token);
    if (!match) throw new Error(`Unsupported filter token “${token}”. Use the documented subset shown below.`);
    const [, key, value] = match;
    if (key === 'exch' && !['nasd', 'nyse', 'amex'].includes(value)) throw new Error(`Unsupported exchange code “${value}”; this lab supports nasd, nyse, and amex.`);
    if (key === 'cap' && value !== 'largeover') throw new Error(`Unsupported market-cap code “${value}”; this lab implements cap_largeover (> $10B).`);
    if (key === 'ta_pattern' && !knownPatterns.has(value) && !knownStrongPatterns.has(value)) throw new Error(`Unsupported pattern tag “${value}”. Pattern values must come from the documented tag set.`);
    if (key === 'ta_candlestick' && !knownCandles.has(value)) throw new Error(`Unsupported candlestick code “${value}”.`);
    if (filters.has(key)) overrides++;
    filters.set(key, value);
  }
  return { filters, overrides };
}

function matchesFinvizFilter(row, key, value) {
  if (key === 'exch') {
    const aliases = { nasd: ['nasd', 'nasdaq'], nyse: ['nyse'], amex: ['amex', 'nyseamerican'] };
    return aliases[value].includes(finvizNorm(row.exchange));
  }
  if (key === 'sec') return finvizNorm(row.sector) === value;
  if (key === 'geo') {
    const country = finvizNorm(row.country);
    return value === 'usa' ? ['us', 'usa', 'unitedstates', 'unitedstatesofamerica'].includes(country) : country === value;
  }
  if (key === 'idx') return String(row.indexes || '').split(/[|;,]/).some(item => finvizNorm(item) === value);
  if (key === 'cap') return Number.isFinite(row.marketCap) && row.marketCap > 10_000_000_000;
  if (key === 'ta_pattern') return row.pattern === value;
  if (key === 'ta_candlestick') return row.candlestick === value;
  return false;
}

function finvizSortField(value, rows) {
  const aliases = { symbol: 'ticker', company: 'name', companyname: 'name', cap: 'marketCap', marketcap: 'marketCap', peratio: 'pe', priceearnings: 'pe', last: 'price', close: 'price', averagevolume: 'avgVolume', avgvol: 'avgVolume', relvolume: 'relativeVolume', relvol: 'relativeVolume', change: 'changePct', changepct: 'changePct', changepercent: 'changePct', indexes: 'indexes', index: 'indexes', candlesticktag: 'candlestick', patterntag: 'pattern' };
  const key = finvizNorm(value), field = aliases[key] || key;
  if (Object.hasOwn(finvizCsvAliases, field)) return { field, raw: false };
  if (rows.some(row => Object.hasOwn(row.raw, key))) return { field: key, raw: true };
  throw new Error(`Sort column “${value}” is not present in this snapshot.`);
}

export function parseFinvizSnapshotCsv(source) {
  if (source.length > 10 * 1024 * 1024) throw new Error('Screener snapshot CSV files must be 10 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 2 || table.length > 50001) throw new Error('Use a header and between 1 and 50,000 symbol rows.');
  const headers = table[0].map(value => finvizNorm(value));
  const index = Object.fromEntries(Object.entries(finvizCsvAliases).map(([field, aliases]) => [field, headers.findIndex(name => aliases.includes(name))]));
  if (index.ticker < 0) throw new Error('The snapshot needs a Ticker or Symbol column.');
  const read = (cells, field) => index[field] < 0 ? '' : String(cells[index[field]] ?? '').trim();
  const numericFields = ['marketCap', 'pe', 'price', 'avgVolume', 'relativeVolume', 'changePct'];
  const rows = [], seen = new Set();
  for (let i = 1; i < table.length; i++) {
    const cells = table[i], rowNumber = i + 1, ticker = normalizeTicker(read(cells, 'ticker'));
    if (!ticker) throw new Error(`Row ${rowNumber}: Ticker must contain 1–10 letters, numbers, dots, or hyphens.`);
    if (seen.has(ticker)) throw new Error(`Row ${rowNumber}: duplicate ticker ${ticker}; keep one snapshot row per symbol.`);
    seen.add(ticker);
    const row = { ticker, raw: {} };
    for (const [field, aliases] of Object.entries(finvizCsvAliases)) row[field] = read(cells, field);
    row.ticker = ticker;
    for (const field of numericFields) {
      const raw = row[field];
      if (!raw || ['—', '-', 'n/a', 'na', 'null'].includes(raw.toLowerCase())) { row[field] = null; continue; }
      const value = parseFinvizScalar(raw);
      if (value === null) throw new Error(`Row ${rowNumber}: ${field} must be a number; market cap and volume may use K, M, B, or T.`);
      row[field] = value;
    }
    row.pattern = finvizTagCode(row.pattern);
    row.candlestick = finvizTagCode(row.candlestick, true);
    for (let column = 0; column < headers.length; column++) {
      const key = headers[column], raw = String(cells[column] ?? '').trim();
      row.raw[key] = parseFinvizScalar(raw) ?? raw;
    }
    rows.push(row);
  }
  return rows;
}

export function calculateFinvizContract(model) {
  const { filters, overrides } = parseFinvizFilterQuery(model.filterQuery);
  const order = String(model.order || 'ticker').trim();
  const tickerListMode = order.toLowerCase() === 'tickersfilter';
  const orderField = tickerListMode ? null : finvizSortField(order.replace(/^-/, ''), model.rows);
  let rows, missingTickers = [], excludedEtfs = [], filteredTickers = [];
  if (tickerListMode) {
    const tickerTokens = String(model.tickers || '').split(',').map(value => value.trim()).filter(Boolean);
    const invalidTickers = tickerTokens.filter(value => !normalizeTicker(value));
    if (invalidTickers.length) throw new Error(`Invalid ticker value${invalidTickers.length === 1 ? '' : 's'} in t=: ${invalidTickers.join(', ')}.`);
    const requested = tickerTokens.map(value => normalizeTicker(value));
    if (!requested.length) throw new Error('Order tickersfilter requires a comma-separated Ticker list in the t= field.');
    const uniqueRequested = [...new Set(requested)], byTicker = new Map(model.rows.map(row => [row.ticker, row]));
    rows = [];
    for (const ticker of uniqueRequested) {
      const row = byTicker.get(ticker);
      if (!row) { missingTickers.push(ticker); continue; }
      if (finvizNorm(row.securityType) === 'etf') { excludedEtfs.push(ticker); continue; }
      rows.push(row);
    }
  } else {
    rows = model.rows.filter(row => {
      if (finvizNorm(row.securityType) === 'etf') { excludedEtfs.push(row.ticker); return false; }
      return true;
    });
  }
  const unfilteredCount = rows.length;
  rows = rows.filter(row => [...filters].every(([key, value]) => matchesFinvizFilter(row, key, value)));
  if (tickerListMode) {
    const matched = new Set(rows.map(row => row.ticker));
    filteredTickers = model.tickers.split(',').map(value => normalizeTicker(value)).filter(ticker => ticker && !missingTickers.includes(ticker) && !excludedEtfs.includes(ticker) && !matched.has(ticker));
  } else {
    const descending = order.startsWith('-'), field = orderField.field, raw = orderField.raw;
    rows = rows.map((row, index) => ({ row, index })).sort((a, b) => {
      const left = raw ? a.row.raw[field] : a.row[field], right = raw ? b.row.raw[field] : b.row[field];
      if (left === null || left === '' || left === undefined) return right === null || right === '' || right === undefined ? a.index - b.index : 1;
      if (right === null || right === '' || right === undefined) return -1;
      const comparison = typeof left === 'number' && typeof right === 'number' ? left - right : String(left).localeCompare(String(right), undefined, { numeric: true, sensitivity: 'base' });
      return (descending ? -comparison : comparison) || a.index - b.index;
    }).map(item => item.row);
  }
  const unclassifiedUniverseRows = model.rows.filter(row => !String(row.securityType || '').trim()).length;
  return { rows, filtersApplied: filters.size, overrides, tickerListMode, missingTickers, excludedEtfs, filteredTickers, filteredOut: unfilteredCount - rows.length, sourceCount: model.rows.length, unclassifiedUniverseRows };
}
