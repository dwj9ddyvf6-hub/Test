const root = document.getElementById('app');
const KEY = 'silicon-market-terminal:v1';
const safeStored = (() => {
  try {
    const value = JSON.parse(localStorage.getItem(KEY) || '{}');
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  } catch { return {}; }
})();

function normalizeTicker(value) {
  const ticker = String(value || '').trim().toUpperCase();
  return /^[A-Z0-9.-]{1,10}$/.test(ticker) ? ticker : null;
}

function emptyConfluenceState() {
  return { scores: {}, effectiveScores: {}, qualified: false, dataConfidence: '', realIndexCount: '' };
}

function normalizeConfluenceState(value) {
  const candidate = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  return {
    scores: candidate.scores && typeof candidate.scores === 'object' && !Array.isArray(candidate.scores) ? candidate.scores : {},
    effectiveScores: candidate.effectiveScores && typeof candidate.effectiveScores === 'object' && !Array.isArray(candidate.effectiveScores) ? candidate.effectiveScores : {},
    qualified: candidate.qualified === true,
    dataConfidence: candidate.dataConfidence ?? '',
    realIndexCount: candidate.realIndexCount ?? '',
  };
}

function confluenceHasValues(value) {
  const hasScore = scores => scores && Object.values(scores).some(score => score !== null && score !== undefined && String(score).trim() !== '');
  return value?.qualified === true || hasScore(value?.scores) || hasScore(value?.effectiveScores)
    || String(value?.dataConfidence ?? '').trim() !== '' || String(value?.realIndexCount ?? '').trim() !== '';
}

const storedTicker = normalizeTicker(safeStored.ticker) || 'SPY';
const confluenceByTicker = {};
if (safeStored.confluenceByTicker && typeof safeStored.confluenceByTicker === 'object' && !Array.isArray(safeStored.confluenceByTicker)) {
  for (const [tickerKey, candidate] of Object.entries(safeStored.confluenceByTicker)) {
    const ticker = normalizeTicker(tickerKey);
    if (ticker) {
      const normalized = normalizeConfluenceState(candidate);
      if (confluenceHasValues(normalized)) confluenceByTicker[ticker] = normalized;
    }
  }
}
// Older builds kept one score set without a ticker key. Migrate it to the last
// saved ticker when present, otherwise to the historical SPY default.
if (!confluenceByTicker[storedTicker] && safeStored.confluence) {
  const legacyConfluence = normalizeConfluenceState(safeStored.confluence);
  if (confluenceHasValues(legacyConfluence)) confluenceByTicker[storedTicker] = legacyConfluence;
}
const initialConfluence = confluenceByTicker[storedTicker] || emptyConfluenceState();

const state = {
  view: location.hash.slice(1) || 'overview',
  ticker: storedTicker,
  flowSearch: '', flowType: 'all', flowSide: 'all', minPremium: 0, flowSort: 'time',
  dpTicker: '', disclosureSearch: '', screenerSector: 'all', screenerType: 'all',
  newsSearch: '', calendarRange: 'week', gexBasis: 'vol', chartRange: '1D',
  dataMode: 'demo', chartSymbol: storedTicker, showAlertForm: false,
  watchlist: Array.isArray(safeStored.watchlist) ? safeStored.watchlist : ['SPY', 'NVDA', 'AAPL', 'TSLA'],
  savedTrades: Array.isArray(safeStored.savedTrades) ? safeStored.savedTrades : [],
  alerts: Array.isArray(safeStored.alerts) ? safeStored.alerts : [],
  savedLayouts: Array.isArray(safeStored.savedLayouts) ? safeStored.savedLayouts : [],
  strategy: {
    rows: [],
    filename: 'Generated synthetic sample',
    source: 'synthetic',
    fast: Number(safeStored.strategyConfig?.fast) || 20,
    slow: Number(safeStored.strategyConfig?.slow) || 50,
    costBps: Number(safeStored.strategyConfig?.costBps ?? 5),
    splitPct: Number(safeStored.strategyConfig?.splitPct) || 70,
    periodsPerYear: Number(safeStored.strategyConfig?.periodsPerYear) || 252,
    error: '',
    notice: '',
  },
  strategyRuns: Array.isArray(safeStored.strategyRuns) ? safeStored.strategyRuns : [],
  confluence: initialConfluence,
  confluenceByTicker,
  confluenceMode: safeStored.confluenceMode === 'effective' ? 'effective' : 'metadata',
  danelfinPortfolio: {
    rows: [],
    filename: 'Synthetic demonstration universe',
    source: 'synthetic',
    error: '',
    notice: '',
    provenBuyProvided: true,
    preferProvenBuy: true,
    asOf: '',
    startDate: '',
  },
  staticGex: {
    rows: [],
    filename: 'Synthetic demonstration option chain',
    source: 'synthetic',
    error: '',
    notice: '',
    ticker: 'SPY',
    asOf: '',
    spot: 681.44,
    riskFreeRatePct: 4.5,
    dividendYieldPct: 0,
    multiplier: 100,
    gridRangePct: 20,
  },
  bullflowProfile: {
    rows: [],
    availableSessions: [],
    sessionCoverage: [],
    filename: '',
    importedAt: '',
    ticker: 'SPY',
    asOfDate: '2026-10-27',
    asOfTime: '15:00',
    error: '',
    notice: '',
  },
  finvizLab: {
    rows: [],
    filename: '',
    filterQuery: 'exch_nasd,cap_largeover',
    order: '-change',
    tickers: '',
    error: '',
    notice: '',
  },
  stockRoverLab: {
    rows: [],
    filename: '',
    source: '',
    error: '',
    notice: '',
  },
  azraelMap: {
    anchorClose: 7757.17,
    vixClose: 16.68,
    elapsedMinutes: 120,
    sessionMinutes: 390,
    candidateTarget: 7800,
    error: '',
  },
  vendorFamilies: [],
  vendorCoverageMeta: { requestedPasses: 94, targetFamilies: 86 },
  coverageError: '',
  vendorSearch: '',
  vendorLane: 'all',
  vendorResearch: 'all',
  layoutMessage: '',
  theme: safeStored.theme === 'light' ? 'light' : 'dark',
  payoff: { type: 'call', side: 'long', strike: 100, premium: 4.25, contracts: 1, spot: 100 },
  optionLab: {
    spot: 100,
    daysToExpiration: 30,
    volatilityPct: 25,
    riskFreeRatePct: 4.5,
    dividendYieldPct: 0,
    exerciseStyle: 'european',
    treeSteps: 200,
    legsText: 'type,side,strike,premium,contracts,multiplier\ncall,long,100,4.25,1,100\ncall,short,110,1.55,1,100',
    legs: [
      { type: 'call', side: 'long', strike: 100, premium: 4.25, contracts: 1, multiplier: 100 },
      { type: 'call', side: 'short', strike: 110, premium: 1.55, contracts: 1, multiplier: 100 },
    ],
    error: '',
  },
};

const indexes = [
  { ticker: 'SPX', label: 'S&P 500', value: 6815.42, change: 0.43 },
  { ticker: 'NDX', label: 'NASDAQ 100', value: 25142.7, change: 0.81 },
  { ticker: 'DJI', label: 'DOW JONES', value: 47625.18, change: 0.26 },
  { ticker: 'VIX', label: 'VOLATILITY', value: 17.84, change: -2.15 },
];
const sectors = [
  ['Technology', 'XLK', 1.38], ['Communication', 'XLC', 0.94], ['Consumer Discretionary', 'XLY', 0.62],
  ['Industrials', 'XLI', 0.42], ['Financials', 'XLF', 0.31], ['Energy', 'XLE', -0.46],
  ['Healthcare', 'XLV', -0.14], ['Utilities', 'XLU', -0.23], ['Real Estate', 'XLRE', -0.51],
];
const movers = [
  { ticker: 'NVDA', price: 184.26, change: 3.72, net: 18.4 }, { ticker: 'TSLA', price: 412.85, change: -2.34, net: -12.8 },
  { ticker: 'AMD', price: 188.43, change: 2.16, net: 9.6 }, { ticker: 'AAPL', price: 276.18, change: 0.84, net: 7.1 },
  { ticker: 'PLTR', price: 169.34, change: 4.28, net: 6.5 }, { ticker: 'META', price: 724.1, change: -0.92, net: -5.3 },
  { ticker: 'AMZN', price: 252.37, change: 0.68, net: 4.9 },
];
const flowTrades = [
  ['10:42:18', 'NVDA', 'CALL', '11/21', 190, 'ASK', 2.84, 520, 147680, 184.26, 0.34, 38.6, 'SWEEP'],
  ['10:41:52', 'SPY', 'PUT', '11/07', 670, 'BID', 3.22, 410, 132020, 681.44, 0.21, 24.2, 'MULTI'],
  ['10:41:10', 'TSLA', 'CALL', '11/14', 430, 'MID', 8.15, 125, 101875, 412.85, 0.45, 62.1, 'SPLIT'],
  ['10:39:46', 'AMD', 'CALL', '12/19', 200, 'ASK', 6.3, 140, 88200, 188.43, 0.61, 46.8, 'SWEEP'],
  ['10:38:21', 'AAPL', 'PUT', '11/21', 265, 'ASK', 4.65, 175, 81375, 276.18, 0.28, 31.7, 'BLOCK'],
  ['10:37:04', 'META', 'CALL', '11/07', 740, 'BID', 12.7, 55, 69850, 724.1, 0.18, 29.5, 'FLOOR'],
  ['10:35:59', 'PLTR', 'CALL', '01/16', 180, 'ASK', 11.2, 60, 67200, 169.34, 0.52, 58.3, 'SWEEP'],
  ['10:34:32', 'QQQ', 'PUT', '11/14', 605, 'BID', 7.4, 85, 62900, 612.18, 0.16, 27.4, 'MULTI'],
  ['10:33:20', 'AMZN', 'CALL', '11/21', 260, 'ASK', 5.35, 110, 58850, 252.37, 0.31, 34.8, 'SWEEP'],
  ['10:30:17', 'MSFT', 'PUT', '12/19', 490, 'MID', 8.95, 60, 53700, 504.42, 0.29, 23.6, 'BLOCK'],
  ['10:28:45', 'SPY', 'CALL', '11/07', 690, 'ASK', 4.18, 125, 52250, 681.44, 0.13, 20.8, 'SWEEP'],
  ['10:25:16', 'COIN', 'PUT', '11/14', 300, 'BID', 14.6, 35, 51100, 287.22, 0.44, 71.3, 'FLOOR'],
  ['10:22:08', 'GOOGL', 'CALL', '12/19', 310, 'ASK', 8.3, 60, 49800, 298.4, 0.39, 33.1, 'SWEEP'],
  ['10:18:34', 'IWM', 'PUT', '11/21', 230, 'ASK', 3.65, 130, 47450, 234.76, 0.27, 26.3, 'MULTI'],
  ['10:15:12', 'AVGO', 'CALL', '01/16', 400, 'BID', 21.8, 20, 43600, 392.58, 0.19, 39.4, 'BLOCK'],
  ['10:12:53', 'META', 'PUT', '12/19', 690, 'ASK', 21.3, 20, 42600, 724.1, 0.47, 42.8, 'SWEEP'],
  ['10:08:04', 'NFLX', 'CALL', '11/21', 1270, 'ASK', 27.2, 15, 40800, 1248.6, 0.17, 51.2, 'FLOOR'],
  ['10:04:29', 'XLF', 'CALL', '12/19', 55, 'BID', 1.31, 300, 39300, 54.18, 0.31, 19.1, 'MULTI'],
].map((r, i) => ({ id: `demo-${i + 1}`, time: r[0], ticker: r[1], type: r[2], expiry: r[3], strike: r[4], side: r[5], price: r[6], size: r[7], premium: r[8], spot: r[9], diff: r[10], iv: r[11], code: r[12] }));

const darkpoolTrades = [
  ['10:40:22', 'NVDA', 184.12, 88400, 16277312, 'Above ask'], ['10:36:14', 'SPY', 681.2, 120500, 82084600, 'At midpoint'],
  ['10:31:08', 'TSLA', 413.05, 34200, 14128860, 'Below bid'], ['10:26:47', 'AAPL', 276.32, 56800, 15697376, 'At midpoint'],
  ['10:18:39', 'AMD', 188.61, 22500, 4243725, 'Above ask'], ['10:12:11', 'META', 723.8, 14700, 10639860, 'Below bid'],
  ['10:05:03', 'AMZN', 252.55, 31600, 7980580, 'At midpoint'], ['09:58:48', 'PLTR', 169.2, 42100, 7123320, 'Above ask'],
  ['09:52:07', 'MSFT', 504.1, 13800, 6956580, 'Below bid'], ['09:45:52', 'COIN', 287.35, 9800, 2816030, 'At midpoint'],
].map(r => ({ time: r[0], ticker: r[1], price: r[2], shares: r[3], value: r[4], side: r[5] }));

const disclosures = [
  { date: '2026-10-24', person: 'Nancy Pelosi', party: 'D', ticker: 'NVDA', action: 'Purchase', size: '$1M–$5M', filed: '2026-10-25' },
  { date: '2026-10-23', person: 'Michael McCaul', party: 'R', ticker: 'MSFT', action: 'Sale', size: '$250K–$500K', filed: '2026-10-25' },
  { date: '2026-10-22', person: 'Mark Green', party: 'R', ticker: 'AMZN', action: 'Purchase', size: '$50K–$100K', filed: '2026-10-24' },
  { date: '2026-10-21', person: 'Josh Gottheimer', party: 'D', ticker: 'META', action: 'Sale', size: '$100K–$250K', filed: '2026-10-23' },
  { date: '2026-10-20', person: 'Dan Crenshaw', party: 'R', ticker: 'AAPL', action: 'Purchase', size: '$15K–$50K', filed: '2026-10-22' },
  { date: '2026-10-19', person: 'Ro Khanna', party: 'D', ticker: 'TSLA', action: 'Purchase', size: '$50K–$100K', filed: '2026-10-22' },
  { date: '2026-10-17', person: 'Tommy Tuberville', party: 'R', ticker: 'GOOGL', action: 'Sale', size: '$100K–$250K', filed: '2026-10-20' },
];
const insiders = [
  { date: '2026-10-24', person: 'Chief Executive Officer', ticker: 'ORCL', action: 'Purchase', shares: '18,400', value: '$3.2M', form: 'Form 4' },
  { date: '2026-10-23', person: 'Director', ticker: 'META', action: 'Sale', shares: '6,200', value: '$4.5M', form: 'Form 4' },
  { date: '2026-10-22', person: 'Chief Financial Officer', ticker: 'AMD', action: 'Purchase', shares: '12,500', value: '$2.3M', form: 'Form 4' },
  { date: '2026-10-21', person: '10% Owner', ticker: 'COIN', action: 'Sale', shares: '4,000', value: '$1.2M', form: 'Form 4' },
  { date: '2026-10-20', person: 'Chief Operating Officer', ticker: 'NFLX', action: 'Purchase', shares: '1,400', value: '$1.8M', form: 'Form 4' },
];
const newsItems = [
  { time: '10:41', ticker: 'NVDA', tag: 'TECH', title: 'Demo headline: semiconductor sector firms as chipmakers lead the morning tape', source: 'Silicon sample desk' },
  { time: '10:32', ticker: 'SPY', tag: 'MACRO', title: 'Demo headline: index options activity skews toward near-dated contracts', source: 'Silicon sample desk' },
  { time: '10:14', ticker: 'TSLA', tag: 'AUTO', title: 'Demo headline: automaker shares move lower in synthetic session data', source: 'Silicon sample desk' },
  { time: '09:58', ticker: 'AMD', tag: 'TECH', title: 'Demo headline: chip stocks outperform broader market in sample feed', source: 'Silicon sample desk' },
  { time: '09:42', ticker: 'AAPL', tag: 'EARNINGS', title: 'Demo headline: calendar reminder for the next reported earnings date', source: 'Silicon sample desk' },
  { time: '09:23', ticker: 'XLF', tag: 'FINANCIALS', title: 'Demo headline: financial sector moves inside a narrow synthetic range', source: 'Silicon sample desk' },
];
const calendarItems = [
  { date: 'MON 26', time: '08:30', type: 'ECONOMIC', title: 'Durable Goods Orders', detail: 'United States · High impact' },
  { date: 'TUE 27', time: '10:00', type: 'ECONOMIC', title: 'Consumer Confidence', detail: 'United States · Medium impact' },
  { date: 'WED 28', time: '14:00', type: 'FED', title: 'FOMC Rate Decision', detail: 'United States · High impact' },
  { date: 'THU 29', time: '08:30', type: 'ECONOMIC', title: 'Initial Jobless Claims', detail: 'United States · Medium impact' },
  { date: 'FRI 30', time: '16:00', type: 'OPTIONS', title: 'Monthly options expiration', detail: 'U.S. listed options · Market event' },
  { date: 'MON 02', time: '16:05', type: 'EARNINGS', title: 'Demo company earnings after close', detail: 'Sample calendar record' },
];
const screenerRows = [
  { ticker: 'NVDA', name: 'NVIDIA Corporation', sector: 'Technology', price: 184.26, change: 3.72, volume: '68.2M', iv: 48.2, putCall: 0.72 },
  { ticker: 'PLTR', name: 'Palantir Technologies', sector: 'Technology', price: 169.34, change: 4.28, volume: '24.6M', iv: 68.4, putCall: 0.51 },
  { ticker: 'TSLA', name: 'Tesla, Inc.', sector: 'Consumer Discretionary', price: 412.85, change: -2.34, volume: '42.8M', iv: 57.8, putCall: 1.28 },
  { ticker: 'AMD', name: 'Advanced Micro Devices', sector: 'Technology', price: 188.43, change: 2.16, volume: '32.5M', iv: 52.7, putCall: 0.83 },
  { ticker: 'COIN', name: 'Coinbase Global', sector: 'Financials', price: 287.22, change: -1.68, volume: '8.1M', iv: 82.6, putCall: 1.13 },
  { ticker: 'META', name: 'Meta Platforms', sector: 'Communication', price: 724.1, change: -0.92, volume: '11.2M', iv: 35.7, putCall: 0.96 },
  { ticker: 'AAPL', name: 'Apple Inc.', sector: 'Technology', price: 276.18, change: 0.84, volume: '31.9M', iv: 29.4, putCall: 0.89 },
  { ticker: 'XOM', name: 'Exxon Mobil', sector: 'Energy', price: 123.82, change: -0.51, volume: '9.4M', iv: 24.1, putCall: 1.04 },
];

function persist() {
  if (confluenceHasValues(state.confluence)) state.confluenceByTicker[state.ticker] = state.confluence;
  else delete state.confluenceByTicker[state.ticker];
  localStorage.setItem(KEY, JSON.stringify({
    ticker: state.ticker,
    watchlist: state.watchlist,
    savedTrades: state.savedTrades,
    alerts: state.alerts,
    savedLayouts: state.savedLayouts,
    theme: state.theme,
    strategyConfig: {
      fast: state.strategy.fast,
      slow: state.strategy.slow,
      costBps: state.strategy.costBps,
      splitPct: state.strategy.splitPct,
      periodsPerYear: state.strategy.periodsPerYear,
    },
    strategyRuns: state.strategyRuns.slice(0, 12),
    confluenceByTicker: state.confluenceByTicker,
    confluenceMode: state.confluenceMode,
  }));
}
function money(value, compact = false) {
  if (compact && Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (compact && Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: value < 100 ? 2 : 0 }).format(value);
}
function integer(value) { return new Intl.NumberFormat('en-US').format(value); }
function pct(value) { return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`; }
function signedClass(value) { return value >= 0 ? 'positive' : 'negative'; }
function esc(value) { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function icon(symbol, cls = '') { return `<span class="nav-icon ${cls}" aria-hidden="true">${symbol}</span>`; }
function label(text, cls = '') { return `<span class="badge ${cls}">${text}</span>`; }
function moneyFlow(row) { return row.premium; }
function activeNav(view) { return state.view === view || (view === 'ticker' && state.view === 'ticker'); }

const navGroups = [
  { heading: 'MARKETS', items: [['overview', 'Overview', '⌂'], ['flow', 'Options flow', '↗', 'LIVE'], ['gex', 'GEX & Greeks', '◈'], ['darkpool', 'Dark pools', '◌'], ['screener', 'Screeners', '⌕'], ['charts', 'Charting', '⌁']] },
  { heading: 'RESEARCH', items: [['congress', 'Congress trades', '▤'], ['insiders', 'Insider activity', '◉'], ['calendar', 'Calendar', '▦'], ['news', 'News flow', '≋'], ['ticker', 'Ticker research', '⌖'], ['confluence', 'Confluence lab', '◈'], ['portfolio', 'Sector portfolio lab', '▦'], ['staticgex', 'Static GEX lab', '◈'], ['azrael', '15.87 Rule map', '⌖'], ['optionlab', 'Option strategy lab', '⌗'], ['bullflow', 'Activity profile lab', '◉'], ['finviz', 'Filter contract lab', '⌕'], ['stockrover', 'Factor profile lab', '⌖'], ['coverage', 'Vendor coverage', '▧'], ['evidence', 'Evidence graph', '⟁']] },
  { heading: 'WORKSPACE', items: [['watchlists', 'Watchlists', '☆'], ['alerts', 'My alerts', '♧'], ['tools', 'Tools', '⊞'], ['strategy', 'Strategy lab', '⌁']] },
];

const stockRoverFactorCategories = [
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
const stockRoverFactorMetrics = stockRoverFactorCategories.flatMap(category => category.metrics);

function renderShell() {
  const pageTitle = ({ overview: 'Market overview', flow: 'Options flow', gex: 'GEX & Greeks', staticgex: 'Static GEX Lab', azrael: '15.87 Rule map', optionlab: 'Option strategy lab', bullflow: 'Options activity profile', finviz: 'Finviz filter contract lab', stockrover: 'Stock Rover factor lab', darkpool: 'Dark-pool activity', screener: 'Market screeners', charts: 'Chart workspace', congress: 'Congress trades', insiders: 'Insider activity', calendar: 'Event calendar', news: 'News flow', ticker: `${state.ticker} research`, confluence: 'Confluence lab', portfolio: 'Sector portfolio lab', watchlists: 'Watchlists', alerts: 'Alert rules', tools: 'Research tools', strategy: 'Strategy lab', coverage: 'Vendor coverage', evidence: 'Evidence graph', api: 'Data connection' })[state.view] || 'Market overview';
  const localCsvView = (state.view === 'strategy' && state.strategy.source === 'csv') || (state.view === 'portfolio' && state.danelfinPortfolio.source === 'csv') || (state.view === 'staticgex' && state.staticGex.source === 'csv') || (state.view === 'stockrover' && state.stockRoverLab.source === 'csv');
  const localCsvLabel = state.view === 'portfolio' ? 'Sector Portfolio Lab' : state.view === 'staticgex' ? 'Static GEX Lab' : state.view === 'stockrover' ? 'Factor Profile Lab' : 'Strategy Lab';
  const localCsvFilename = state.view === 'portfolio' ? state.danelfinPortfolio.filename : state.view === 'staticgex' ? state.staticGex.filename : state.view === 'stockrover' ? state.stockRoverLab.filename : state.strategy.filename;
  const dataBanner = localCsvView
    ? `<div class="demo-banner csv-data-banner"><span class="demo-mark">i</span><b>LOCAL CSV DATA</b><span>${esc(localCsvLabel)} is analyzing ${esc(localCsvFilename)} in this browser tab. The file was not uploaded or stored.</span><button data-view="api">Data source details <span>→</span></button></div>`
    : state.view === 'optionlab'
      ? '<div class="demo-banner csv-data-banner"><span class="demo-mark">i</span><b>LOCAL PAYOFF CALCULATION</b><span>The starter strategy and any edits are calculated in this tab only; no quote or vendor connection is used.</span><button data-view="api">Data source details <span>→</span></button></div>'
      : state.view === 'bullflow'
        ? `<div class="demo-banner csv-data-banner"><span class="demo-mark">i</span><b>LOCAL OPTIONS INPUT</b><span>${state.bullflowProfile.filename ? `${esc(state.bullflowProfile.filename)} is held in this tab only.` : 'Load a local CSV or synthetic sample; no vendor connection is used.'}</span><button data-view="api">Data source details <span>→</span></button></div>`
      : state.view === 'finviz'
        ? `<div class="demo-banner csv-data-banner"><span class="demo-mark">i</span><b>LOCAL SCREENER SNAPSHOT</b><span>${state.finvizLab.filename ? `${esc(state.finvizLab.filename)} is held in this tab only.` : 'Load your CSV or synthetic sample; no Finviz connection is used.'}</span><button data-view="api">Data source details <span>→</span></button></div>`
      : state.view === 'azrael'
        ? '<div class="demo-banner csv-data-banner"><span class="demo-mark">i</span><b>PUBLIC METHOD · MANUAL INPUTS</b><span>Enter prior-session closes. No vendor service, market feed, or account data is accessed.</span><button data-view="api">Data source details <span>→</span></button></div>'
      : state.view === 'stockrover'
        ? `<div class="demo-banner csv-data-banner"><span class="demo-mark">i</span><b>${state.stockRoverLab.source === 'synthetic' ? 'SYNTHETIC FACTOR SAMPLE' : 'LOCAL FACTOR INPUT'}</b><span>${state.stockRoverLab.source === 'synthetic' ? 'Generated values illustrate the ranking workflow and are not market data.' : state.stockRoverLab.filename ? `${esc(state.stockRoverLab.filename)} is held in this tab only.` : 'Load your CSV or a synthetic sample; no Stock Rover connection is used.'}</span><button data-view="api">Data source details <span>→</span></button></div>`
      : '<div class="demo-banner"><span class="demo-mark">i</span><b>SYNTHETIC DEMO DATA</b><span>All prices, trades, disclosures, headlines, and exposure values are locally generated examples — not live market information.</span><button data-view="api">Data source details <span>→</span></button></div>';
  const footerData = localCsvView ? 'Local CSV analysis · no data sent to a server' : state.view === 'optionlab' ? 'Option payoff · local calculation only' : state.view === 'bullflow' ? 'Options activity profile · local input only' : state.view === 'finviz' ? 'Screener contract · local input only' : state.view === 'stockrover' ? 'Factor scores · local input only' : 'Demo fixtures only';
  const nav = navGroups.map(group => `<div class="nav-group"><div class="nav-heading">${group.heading}</div>${group.items.map(([view, title, glyph, tag]) => `<button class="nav-item ${activeNav(view) ? 'active' : ''}" data-view="${view}">${icon(glyph)}<span>${title}</span>${tag ? `<span class="nav-live">${tag}</span>` : ''}</button>`).join('')}</div>`).join('');
  const content = renderPage();
  root.innerHTML = `<div class="app-shell ${state.theme === 'light' ? 'light-theme' : ''}">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">S</span><span class="brand-name">silicon<span> / markets</span></span><button class="collapse-button" data-action="collapse-sidebar" aria-label="Collapse sidebar">‹</button></div>
      <div class="workspace-select"><span class="workspace-dot"></span><span>Personal workspace</span><span class="chevron">⌄</span></div>
      <button class="overview-shortcut" data-view="overview">${icon('⌂')} Market overview <span>⌘ 1</span></button>
      ${nav}
      <div class="sidebar-bottom">
        <div class="workspace-card"><div class="workspace-card-top"><span class="workspace-dot"></span>LOCAL WORKSPACE</div><p>Your lists and alerts are stored in this browser.</p><button class="text-button" data-view="api">Data source settings <span>→</span></button></div>
        <button class="nav-item" data-view="api">${icon('⚙')}<span>Settings & API</span></button>
        <div class="profile-row"><div class="avatar">SJ</div><div><b>Silicon user</b><small>Local account</small></div><span class="chevron">···</span></div>
      </div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <button class="mobile-menu" data-action="mobile-menu" aria-label="Open menu">☰</button>
        <div class="breadcrumbs"><span>Workspace</span><span class="slash">/</span><b>${esc(pageTitle)}</b></div>
        <div class="topbar-actions">
          <form class="symbol-search" id="symbol-search"><span>⌕</span><input id="global-symbol" name="ticker" aria-label="Search ticker" placeholder="Search ticker or tool" value="${esc(state.ticker)}" /><kbd>⌘ K</kbd></form>
          <div class="market-session"><span class="session-dot"></span><span>DEMO SESSION</span><span class="session-time">10:42 ET</span></div>
          <button class="icon-button theme-toggle" data-action="theme" aria-label="Toggle theme">${state.theme === 'dark' ? '☼' : '☾'}</button>
          <button class="avatar small-avatar" aria-label="Local profile">SJ</button>
        </div>
      </header>
      ${dataBanner}
      <section class="page-content">${content}</section>
      <footer class="app-footer"><span>Silicon Market Terminal <span class="footer-sep">·</span> Local prototype</span><span>${state.view === 'azrael' ? 'Manual map inputs · no live feed' : footerData} · Not investment advice · <button data-view="api">Data & privacy</button></span></footer>
    </main>
  </div>`;
  document.documentElement.dataset.theme = state.theme;
}

function renderPage() {
  const pages = { overview: renderOverview, flow: renderFlow, gex: renderGex, staticgex: renderStaticGexLab, azrael: renderAzraelMapLab, optionlab: renderOptionStrategyLab, bullflow: renderBullflowActivityProfile, finviz: renderFinvizContractLab, stockrover: renderStockRoverFactorLab, darkpool: renderDarkpool, congress: () => renderDisclosures('congress'), insiders: () => renderDisclosures('insiders'), screener: renderScreener, calendar: renderCalendar, news: renderNews, ticker: renderTicker, confluence: renderConfluenceLab, portfolio: renderDanelfinPortfolioLab, charts: renderCharts, watchlists: renderWatchlists, alerts: renderAlerts, tools: renderTools, strategy: renderStrategyLab, coverage: renderVendorCoverage, evidence: renderEvidenceGraph, api: renderApi };
  return (pages[state.view] || renderOverview)();
}

function pageHeading(eyebrow, title, description, actions = '') {
  return `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${description}</p></div><div class="heading-actions">${actions}</div></div>`;
}
function panel(title, subtitle, content, action = '') {
  return `<section class="panel"><div class="panel-heading"><div><h2>${title}</h2>${subtitle ? `<p>${subtitle}</p>` : ''}</div>${action}</div>${content}</section>`;
}
function statCard(title, value, sub, change, glyph) {
  return `<div class="stat-card"><div class="stat-label">${title}<span class="stat-glyph">${glyph}</span></div><div class="stat-value">${value}</div><div class="stat-foot muted">${sub}</div></div>`;
}
function lineChart(series, options = {}) {
  const width = options.width || 780, height = options.height || 240, pad = { l: 48, r: 14, t: 14, b: 28 };
  const vals = series.flatMap(s => s.values); const min = Math.min(...vals), max = Math.max(...vals), span = (max - min) || 1;
  const x = i => pad.l + i * (width - pad.l - pad.r) / (Math.max(...series.map(s => s.values.length)) - 1);
  const y = v => height - pad.b - (v - min) / span * (height - pad.t - pad.b);
  const grid = Array.from({ length: 4 }, (_, i) => { const gy = pad.t + i * (height - pad.t - pad.b) / 3; return `<line class="chart-grid" x1="${pad.l}" y1="${gy}" x2="${width - pad.r}" y2="${gy}"/><text class="chart-axis" x="4" y="${gy + 4}">${options.axis || ''}${(max - i * span / 3).toFixed(0)}</text>`; }).join('');
  const paths = series.map(s => {
    const points = s.values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    const area = `${points} L${x(s.values.length - 1)},${height - pad.b} L${pad.l},${height - pad.b} Z`;
    return `${s.fill ? `<path d="${area}" fill="${s.color}" opacity=".08"/>` : ''}<path d="${points}" fill="none" stroke="${s.color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`;
  }).join('');
  const axisLabels = options.xLabels || ['09:30', '10:00', '10:30', '11:00', '11:30'];
  const labels = axisLabels.map((t, i) => `<text class="chart-axis" text-anchor="${i === 0 ? 'start' : i === axisLabels.length - 1 ? 'end' : 'middle'}" x="${pad.l + i * (width - pad.l - pad.r) / (axisLabels.length - 1)}" y="${height - 4}">${esc(t)}</text>`).join('');
  return `<svg class="line-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.ariaLabel || 'Synthetic sample chart')}">${grid}${paths}${labels}</svg>`;
}
function chartLegend(items) { return `<div class="chart-legend">${items.map(i => `<span><i style="--legend:${i.color}"></i>${i.label}</span>`).join('')}</div>`; }
function tickerLink(ticker) { return `<button class="ticker-link" data-symbol="${ticker}">${ticker}</button>`; }
function changeText(value) { return `<span class="${signedClass(value)}">${pct(value)}</span>`; }
function tableEmpty(text) { return `<div class="empty-state"><span>⌕</span><b>No matching rows</b><p>${text}</p></div>`; }

const coverageLanes = {
  options: { name: 'Options & derivatives', routes: 'Options flow · GEX & Greeks · dark pools · payoff calculator', gap: 'Synthetic sample rows; no vendor-specific feeds, classifiers, history, entitlements, or alert delivery.' },
  equity: { name: 'Equity research & screening', routes: 'Screener · ticker research · Strategy Lab · 15.87 Rule map', gap: 'No vendor rating models, financial-data licenses, proprietary scores, or source-linked valuation engine.' },
  charting: { name: 'Charting & technical analysis', routes: 'Chart workspace · CSV Strategy Lab', gap: 'No Pine runtime, proprietary indicators, vendor chart data, replay, or desktop/mobile application parity.' },
  automation: { name: 'Automation & portfolio tools', routes: 'Local alert definitions · Strategy Lab', gap: 'No broker/exchange connection, hosted automation, account sync, order execution, or background alert service.' },
  events: { name: 'Events, research & signals', routes: 'Calendar · news · disclosures · ticker research', gap: 'No licensed news/event feeds, paid research, source attribution pipeline, or vendor signal history.' },
  onchain: { name: 'Onchain analytics', routes: 'No corresponding product surface', gap: 'Wallet/entity labeling, chain data, attribution, alerts, and portfolio views are not implemented.' },
};

const confluenceCategories = [
  { key: 'relativeStrength', label: 'Relative strength', weight: 15, metrics: [['rsMarket', 'Broad-market relative return', 20], ['rsGrowth', 'Growth-market relative return', 10], ['rsSector', 'Sector-relative return', 15], ['peerRank', 'Industry / peer rank', 15], ['rsLine', 'RS-line trend', 15], ['downsideResilience', 'Downside resilience', 15], ['longMomentum', 'Long-term momentum', 10]] },
  { key: 'priceAction', label: 'Price action', weight: 18, metrics: [['trendStructure', 'Trend structure', 20], ['baseQuality', 'Base quality', 20], ['volContraction', 'Volatility contraction', 15], ['pullbackQuality', 'Pullback quality', 15], ['technicalRespect', 'Technical respect', 10], ['stageDevelopment', 'Stage development', 10], ['extension', 'Extension', 10]] },
  { key: 'volumeParticipation', label: 'Volume participation', weight: 15, metrics: [['relVolume', 'Relative volume', 20], ['dollarVolTrend', 'Dollar-volume trend', 10], ['accDist', 'Accumulation / distribution', 20], ['volPriceAgreement', 'Volume-price agreement', 20], ['pullbackVolume', 'Pullback volume', 15], ['participationBreadth', 'Participation breadth', 10], ['expansionReadiness', 'Expansion readiness', 5]] },
  { key: 'trendAlignment', label: 'Trend alignment', weight: 12, metrics: [['emaPosition', 'EMA position', 15], ['emaSlope', 'EMA slope', 15], ['dailyWeeklyAgreement', 'Daily / weekly agreement', 25], ['stageAlignment', 'Stage alignment', 15], ['htfLevelPosition', 'Higher-timeframe level position', 15], ['weeklyAccExhaustion', 'Weekly accumulation / exhaustion', 15]] },
  { key: 'supportResistance', label: 'Support / resistance', weight: 12, metrics: [['supportProximity', 'Support proximity', 20], ['roomToResistance', 'Room to resistance', 20], ['levelSignificance', 'Level significance', 20], ['srConversion', 'Support / resistance conversion', 15], ['tradeGeometry', 'Trade geometry', 20], ['chasePenalty', 'Chase penalty', 5]] },
  { key: 'sectorLeadership', label: 'Sector leadership', weight: 10, metrics: [['sectorStrength', 'Sector strength', 15], ['industryStrength', 'Industry strength', 15], ['capitalRotation', 'Capital rotation', 20], ['stockLeadership', 'Stock leadership', 20], ['peerConfirmation', 'Peer confirmation', 10], ['themeSympathy', 'Theme sympathy', 15], ['crowding', 'Crowding', 5]] },
  { key: 'institutionalPositioning', label: 'Institutional positioning', weight: 8, metrics: [['instOwnership', 'Institutional ownership', 15], ['instActivity', 'Institutional activity', 10], ['insiderActivity', 'Insider activity', 10], ['optionsPositioning', 'Options positioning', 25], ['dealerPositioning', 'Dealer positioning', 15], ['darkPool', 'Dark-pool activity', 15], ['shortPositioning', 'Short positioning', 10]] },
  { key: 'marketContext', label: 'Market context', weight: 10, metrics: [['marketRegime', 'Market regime', 20], ['marketBreadth', 'Market breadth', 20], ['indexAccDist', 'Index accumulation / distribution', 15], ['breakoutFollowThrough', 'Breakout follow-through', 15], ['riskAppetite', 'Risk appetite', 10], ['sectorRotation', 'Sector rotation', 10], ['macroEventRisk', 'Macro event risk', 5], ['indexConfirmation', 'Index confirmation', 5]] },
];

const confluenceEffectiveCategories = [
  { key: 'relativeStrength', label: 'Relative strength', weight: 15, leaves: [['mom12_1', '12–1 momentum', 7.2], ['rsVsSpy', 'Relative strength vs S&P 500', 5.4]] },
  { key: 'priceAction', label: 'Price action & structure', weight: 18, leaves: [['macd', 'MACD / trend acceleration', 2.7], ['rsi', 'RSI / momentum extremes', 3.6]] },
  { key: 'volumeParticipation', label: 'Volume & participation', weight: 15, leaves: [['volAccum', 'Volume & accumulation', 4.5]] },
  { key: 'trendAlignment', label: 'Higher-timeframe alignment', weight: 12, leaves: [['maTrend', 'Moving-average trend', 3.6]] },
  { key: 'supportResistance', label: 'Key levels & trade geometry', weight: 12, leaves: [['supportResist', 'Support / resistance structure', 3.6]] },
  { key: 'sectorLeadership', label: 'Sector & theme leadership', weight: 10, leaves: [['sectorStrength', 'Sector strength', 3], ['factorFit', 'Factor-regime fit', 3]] },
  { key: 'institutionalPositioning', label: 'Positioning & ownership', weight: 8, leaves: [['insiderActivity', 'Insider activity', 3.75], ['institutionalTrend', 'Institutional ownership trends', 2.25], ['shortInterest', 'Short interest & borrow pressure', 3.75], ['optionsPositioning', 'Options positioning / put-call', 3], ['darkPool', 'Dark-pool / block activity', 2.25]] },
  { key: 'marketContext', label: 'Broader market context', weight: 10, externalFramework: true, leaves: [['macroEnv', 'Macro environment', 2.4], ['fedOutlook', 'Fed rates outlook', 1.8], ['volatilityFear', 'Volatility / fear', 1.8]] },
];

function computeConfluenceCandidate(input = {}) {
  const scores = input.scores && typeof input.scores === 'object' ? input.scores : {};
  const errors = [];
  let coveredMetrics = 0;
  const metricCount = confluenceCategories.reduce((sum, category) => sum + category.metrics.length, 0);
  const categories = confluenceCategories.map(category => {
    let covered = 0;
    let weightedScore = 0;
    let availableWeight = 0;
    for (const [key, , weight] of category.metrics) {
      const raw = scores[key];
      if (raw === null || raw === undefined || String(raw).trim() === '') continue;
      const value = Number(raw);
      if (!Number.isFinite(value) || value < 0 || value > 100) {
        errors.push(`${key} must be a finite score from 0 to 100.`);
        continue;
      }
      covered += 1;
      coveredMetrics += 1;
      weightedScore += value * weight;
      availableWeight += weight;
    }
    const coverage = covered / category.metrics.length;
    const score = coverage < 0.6 || availableWeight === 0 ? null : weightedScore / availableWeight;
    const status = score === null ? 'no-data' : score >= 60 - 1e-9 ? 'confirming' : score < 45 - 1e-9 ? 'conflicting' : 'neutral';
    return { ...category, covered, designed: category.metrics.length, coverage, score, status };
  });

  const confidenceRaw = input.dataConfidence;
  let dataConfidence = null;
  if (confidenceRaw !== null && confidenceRaw !== undefined && String(confidenceRaw).trim() !== '') {
    dataConfidence = Number(confidenceRaw);
    if (!Number.isFinite(dataConfidence) || dataConfidence < 0 || dataConfidence > 100) errors.push('Data confidence must be a finite score from 0 to 100.');
  }
  const indexRaw = input.realIndexCount;
  let realIndexCount = null;
  if (indexRaw !== null && indexRaw !== undefined && String(indexRaw).trim() !== '') {
    realIndexCount = Number(indexRaw);
    if (!Number.isInteger(realIndexCount) || realIndexCount < 0) errors.push('Real index count must be a non-negative whole number.');
  }

  const measuredCategories = categories.filter(category => category.score !== null);
  const categoryWeightCovered = measuredCategories.reduce((sum, category) => sum + category.weight, 0);
  const score = categoryWeightCovered
    ? measuredCategories.reduce((sum, category) => sum + category.score * category.weight, 0) / categoryWeightCovered
    : null;
  const confirming = categories.filter(category => category.status === 'confirming').length;
  const grades = [[71, 'Exceptional'], [65, 'Strong'], [52, 'Positive'], [39, 'Mixed'], [30, 'Weak (High Risk)'], [0, 'Very Weak (Severe Risk)']];
  let grade = score === null ? null : (grades.find(([minimum]) => score >= minimum)?.[1] || 'Very Weak (Severe Risk)');
  if (grade && ((realIndexCount !== null && realIndexCount < 4) || (dataConfidence !== null && dataConfidence < 70))) {
    const gradeFloor = grades.findIndex(([, label]) => label === 'Mixed');
    const gradeIndex = grades.findIndex(([, label]) => label === grade);
    if (gradeIndex >= 0 && gradeIndex < gradeFloor) grade = 'Mixed';
  }

  const blockers = [];
  if (input.qualified !== true) blockers.push('Eligibility is not marked as met.');
  if (confirming < 5) blockers.push(`Only ${confirming} categories confirm; 5 are required.`);
  if (score === null || Math.round(score) < 65) blockers.push('The weighted score is below 65 or unavailable.');
  if (dataConfidence !== null && dataConfidence < 70) blockers.push('Data confidence is below 70.');
  const status = errors.length ? 'invalid-input' : score === null ? 'insufficient-data' : blockers.length ? 'not-qualified' : 'qualified';
  return { categories, coveredMetrics, metricCount, submetricCoverage: metricCount ? coveredMetrics / metricCount : 0, categoryWeightCovered, score, confirming, grade, dataConfidence, realIndexCount, blockers, errors, status };
}

function computeConfluenceEffectiveCandidate(input = {}) {
  const scores = input.effectiveScores && typeof input.effectiveScores === 'object' ? input.effectiveScores : {};
  const errors = [];
  let coveredMetrics = 0;
  const metricCount = confluenceEffectiveCategories.filter(category => !category.externalFramework).reduce((sum, category) => sum + category.leaves.length, 0);
  const categories = confluenceEffectiveCategories.map(category => {
    if (category.externalFramework) {
      return { ...category, covered: 0, designed: category.leaves.length, coverage: 0, score: null, status: 'no-data' };
    }
    let covered = 0;
    let weightedScore = 0;
    let availableWeight = 0;
    for (const [key, , weight] of category.leaves) {
      const raw = scores[key];
      if (raw === null || raw === undefined || String(raw).trim() === '') continue;
      const value = Number(raw);
      if (!Number.isFinite(value) || value < 0 || value > 100) {
        errors.push(`${key} must be a finite score from 0 to 100.`);
        continue;
      }
      covered += 1;
      coveredMetrics += 1;
      weightedScore += value * weight;
      availableWeight += weight;
    }
    const coverage = covered / category.leaves.length;
    const score = coverage < 0.6 || availableWeight === 0 ? null : weightedScore / availableWeight;
    const status = score === null ? 'no-data' : score >= 60 - 1e-9 ? 'confirming' : score < 45 - 1e-9 ? 'conflicting' : 'neutral';
    return { ...category, covered, designed: category.leaves.length, coverage, score, status };
  });

  const confidenceRaw = input.dataConfidence;
  let dataConfidence = null;
  if (confidenceRaw !== null && confidenceRaw !== undefined && String(confidenceRaw).trim() !== '') {
    dataConfidence = Number(confidenceRaw);
    if (!Number.isFinite(dataConfidence) || dataConfidence < 0 || dataConfidence > 100) errors.push('Data confidence must be a finite score from 0 to 100.');
  }
  const indexRaw = input.realIndexCount;
  let realIndexCount = null;
  if (indexRaw !== null && indexRaw !== undefined && String(indexRaw).trim() !== '') {
    realIndexCount = Number(indexRaw);
    if (!Number.isInteger(realIndexCount) || realIndexCount < 0) errors.push('Real index count must be a non-negative whole number.');
  }

  const measuredCategories = categories.filter(category => category.score !== null);
  const categoryWeightCovered = measuredCategories.reduce((sum, category) => sum + category.weight, 0);
  const score = categoryWeightCovered
    ? measuredCategories.reduce((sum, category) => sum + category.score * category.weight, 0) / categoryWeightCovered
    : null;
  const confirming = categories.filter(category => category.status === 'confirming').length;
  const grades = [[71, 'Exceptional'], [65, 'Strong'], [52, 'Positive'], [39, 'Mixed'], [30, 'Weak (High Risk)'], [0, 'Very Weak (Severe Risk)']];
  let grade = score === null ? null : (grades.find(([minimum]) => score >= minimum)?.[1] || 'Very Weak (Severe Risk)');
  if (grade && ((realIndexCount !== null && realIndexCount < 4) || (dataConfidence !== null && dataConfidence < 70))) {
    const gradeFloor = grades.findIndex(([, label]) => label === 'Mixed');
    const gradeIndex = grades.findIndex(([, label]) => label === grade);
    if (gradeIndex >= 0 && gradeIndex < gradeFloor) grade = 'Mixed';
  }

  const blockers = [];
  if (input.qualified !== true) blockers.push('Eligibility is not marked as met.');
  if (confirming < 5) blockers.push(`Only ${confirming} categories confirm; 5 are required.`);
  if (score === null || Math.round(score) < 65) blockers.push('The weighted score is below 65 or unavailable.');
  if (dataConfidence !== null && dataConfidence < 70) blockers.push('Data confidence is below 70.');
  const status = errors.length ? 'invalid-input' : score === null ? 'insufficient-data' : blockers.length ? 'not-qualified' : 'qualified';
  return { categories, coveredMetrics, metricCount, submetricCoverage: metricCount ? coveredMetrics / metricCount : 0, categoryWeightCovered, score, confirming, grade, dataConfidence, realIndexCount, blockers, errors, status };
}

function confluenceModelSwitch() {
  return `<div class="confluence-model-switch" role="tablist" aria-label="Confluence candidate model"><button class="button ${state.confluenceMode === 'metadata' ? 'primary' : 'secondary'}" type="button" role="tab" aria-selected="${state.confluenceMode === 'metadata'}" data-action="confluence-model" data-model="metadata">55-field metadata candidate</button><button class="button ${state.confluenceMode === 'effective' ? 'primary' : 'secondary'}" type="button" role="tab" aria-selected="${state.confluenceMode === 'effective'}" data-action="confluence-model" data-model="effective">Observed effective path</button></div>`;
}

function renderConfluenceEffectiveLab() {
  const result = computeConfluenceEffectiveCandidate(state.confluence);
  const resultLabel = ({ qualified: 'QUALIFIED CANDIDATE', 'not-qualified': 'THRESHOLD NOT MET', 'insufficient-data': 'INSUFFICIENT DATA', 'invalid-input': 'INPUT NEEDS REVIEW' })[result.status];
  const categoryCards = result.categories.map(category => {
    const categoryScore = category.score === null ? '—' : category.score.toFixed(1);
    const stateLabel = category.status === 'no-data' ? 'NO DATA' : category.status.toUpperCase();
    const fields = category.externalFramework
      ? '<p class="muted">The shipped path reads this category from a separate market-context framework payload (passed / evaluated and coverage). That payload is not reproduced here, so this category stays unavailable.</p>'
      : category.leaves.map(([key, label, weight]) => {
        const stored = state.confluence.effectiveScores[key];
        const value = stored === null || stored === undefined ? '' : esc(String(stored));
        return `<label class="confluence-metric"><span>${esc(label)} <b>${weight.toFixed(2)} effective weight</b></span><input type="number" name="${key}" min="0" max="100" step="any" value="${value}" placeholder="No data" aria-label="${esc(label)} normalized score"></label>`;
      }).join('');
    return `<details class="confluence-category"><summary><span class="confluence-category-name">${esc(category.label)} <small>${category.weight}% category weight</small></span><span class="confluence-category-result">${categoryScore} · ${category.covered}/${category.designed} inputs · ${stateLabel}</span></summary><div class="confluence-metrics">${fields}</div></details>`;
  }).join('');
  const blockers = result.errors.length ? result.errors : result.blockers;
  const blockerList = blockers.length ? `<ul>${blockers.map(message => `<li>${esc(message)}</li>`).join('')}</ul>` : '<p>All available observed client-candidate checks pass for these manual inputs.</p>';
  const scoreLabel = result.score === null ? '—' : result.score.toFixed(1);
  const confidence = state.confluence.dataConfidence === '' ? '' : esc(String(state.confluence.dataConfidence));
  const indexCount = state.confluence.realIndexCount === '' ? '' : esc(String(state.confluence.realIndexCount));
  return `${pageHeading('CLIENT EFFECTIVE PATH · PARTIAL', `${state.ticker} Confluence Lab`, 'A separate manual candidate for the shipped v3Effective leaf map. Inputs are normalized by the analyst; raw transforms and server-produced framework values remain unavailable.', '<button class="button" data-view="coverage">Vendor evidence →</button>')}
    ${confluenceModelSwitch()}
    <div class="coverage-summary confluence-summary"><div><b>${scoreLabel}</b><span>weighted candidate score${result.grade ? ` · ${esc(result.grade)}` : ''}</span></div><div><b>${Math.round(result.submetricCoverage * 100)}%</b><span>of 14 manual leaves populated</span></div><div><b>${result.categoryWeightCovered}%</b><span>category weight represented</span></div><div><b>${result.confirming}/8</b><span>confirming categories</span></div></div>
    <div class="evidence-callout confluence-callout"><b>${resultLabel}</b><span>Observed client path: available leaf values use v3Effective weights within each category; a category needs 60% leaf coverage; the category-level score uses the documented eight-category weights over available categories. Qualification checks require eligibility, 5 confirming categories, rounded score 65+, and data confidence 70+ when supplied. A stronger grade is capped at Mixed when real-index count is below 4 or confidence is below 70. Market context requires a separate framework payload and remains no-data here.</span></div>
    <form id="confluence-effective-form" class="panel confluence-form" novalidate>
      <div class="panel-heading"><div><h2>Effective-path inputs for ${esc(state.ticker)}</h2><p>Enter normalized 0–100 values only when you have evidence. Fourteen ticker/sector leaves are available; market context is sourced separately in the client.</p></div><div class="confluence-form-actions"><button class="button" type="button" data-action="confluence-reset">Clear all local inputs</button><button class="button primary" type="submit">Evaluate candidate</button></div></div>
      <div class="confluence-qualification"><label><input type="checkbox" name="qualified" value="true" ${state.confluence.qualified ? 'checked' : ''}> Eligibility criteria are met</label><label class="field-label">Data confidence (optional, 0–100)<input type="number" name="dataConfidence" min="0" max="100" step="any" value="${confidence}" placeholder="Not supplied"></label><label class="field-label">Real index count (optional)<input type="number" name="realIndexCount" min="0" step="1" value="${indexCount}" placeholder="Not supplied"></label></div>
      <div class="confluence-groups">${categoryCards}</div>
    </form>
    <section class="panel confluence-result-panel"><div class="panel-heading"><div><h2>Candidate decision audit</h2><p>Scores are manual estimates, not Leadr outputs or validated signals.</p></div></div>${blockerList}<div class="coverage-footnote">This path reproduces the public client’s effective leaf weights and checkable aggregation boundaries only. The bundle also accepts a packed server/framework score vector; its source data, transformations, freshness, and authenticated score pipeline remain unknown. <a href="../../research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md">Open the implementation record →</a></div></section>`;
}

function renderConfluenceLab() {
  if (state.confluenceMode === 'effective') return renderConfluenceEffectiveLab();
  const result = computeConfluenceCandidate(state.confluence);
  const resultLabel = ({ qualified: 'QUALIFIED CANDIDATE', 'not-qualified': 'THRESHOLD NOT MET', 'insufficient-data': 'INSUFFICIENT DATA', 'invalid-input': 'INPUT NEEDS REVIEW' })[result.status];
  const categoryCards = result.categories.map(category => {
    const metricFields = category.metrics.map(([key, label, weight]) => {
      const stored = state.confluence.scores[key];
      const value = stored === null || stored === undefined ? '' : esc(String(stored));
      return `<label class="confluence-metric"><span>${esc(label)} <b>${weight}%</b></span><input type="number" name="${key}" min="0" max="100" step="any" value="${value}" placeholder="No data" aria-label="${esc(label)} normalized score"></label>`;
    }).join('');
    const categoryScore = category.score === null ? '—' : category.score.toFixed(1);
    const stateLabel = category.status === 'no-data' ? 'NO DATA' : category.status.toUpperCase();
    return `<details class="confluence-category"><summary><span class="confluence-category-name">${esc(category.label)} <small>${category.weight}% model weight</small></span><span class="confluence-category-result">${categoryScore} · ${category.covered}/${category.designed} inputs · ${stateLabel}</span></summary><div class="confluence-metrics">${metricFields}</div></details>`;
  }).join('');
  const blockers = result.errors.length ? result.errors : result.blockers;
  const blockerList = blockers.length ? `<ul>${blockers.map(message => `<li>${esc(message)}</li>`).join('')}</ul>` : '<p>All observed public candidate checks pass for these manual inputs.</p>';
  const scoreLabel = result.score === null ? '—' : result.score.toFixed(1);
  const confidence = state.confluence.dataConfidence === '' ? '' : esc(String(state.confluence.dataConfidence));
  const indexCount = state.confluence.realIndexCount === '' ? '' : esc(String(state.confluence.realIndexCount));
  return `${pageHeading('55-FIELD METADATA CANDIDATE', `${state.ticker} Confluence Lab`, 'A manual candidate built from the client’s descriptive 55-submetric weight table. This is distinct from the shipped v3Effective scoring path and from the unknown production server model.', '<button class="button" data-view="coverage">Vendor evidence →</button>')}
    ${confluenceModelSwitch()}
    <div class="coverage-summary confluence-summary"><div><b>${scoreLabel}</b><span>weighted candidate score${result.grade ? ` · ${esc(result.grade)}` : ''}</span></div><div><b>${Math.round(result.submetricCoverage * 100)}%</b><span>submetrics populated</span></div><div><b>${result.categoryWeightCovered}%</b><span>category weight represented</span></div><div><b>${result.confirming}/8</b><span>confirming categories</span></div></div>
    <div class="evidence-callout confluence-callout"><b>${resultLabel}</b><span>This metadata candidate uses a 60% per-category coverage floor; the public bundle exposes that floor in other leaf evaluators but does not establish that it applies to this 55-field table. Category scores at 60+ confirm and below 45 conflict; qualification uses the visible 5-confirmation, rounded-score 65+, and optional data-confidence 70+ checks. A supplied real-index count below 4 or data confidence below 70 caps a stronger grade at Mixed. This is a manual candidate, not the authenticated server score.</span></div>
    <form id="confluence-form" class="panel confluence-form" novalidate>
      <div class="panel-heading"><div><h2>Metadata-candidate inputs for ${esc(state.ticker)}</h2><p>Enter 0–100 scores only when you have evidence for that submetric. Blank fields stay unavailable and are never treated as zero.</p></div><div class="confluence-form-actions"><button class="button" type="button" data-action="confluence-reset">Clear all local inputs</button><button class="button primary" type="submit">Evaluate candidate</button></div></div>
      <div class="confluence-qualification"><label><input type="checkbox" name="qualified" value="true" ${state.confluence.qualified ? 'checked' : ''}> Eligibility criteria are met</label><label class="field-label">Data confidence (optional, 0–100)<input type="number" name="dataConfidence" min="0" max="100" step="any" value="${confidence}" placeholder="Not supplied"></label><label class="field-label">Real index count (optional)<input type="number" name="realIndexCount" min="0" step="1" value="${indexCount}" placeholder="Not supplied"></label></div>
      <div class="confluence-groups">${categoryCards}</div>
    </form>
    <section class="panel confluence-result-panel"><div class="panel-heading"><div><h2>Candidate decision audit</h2><p>Every blocker is shown so missing evidence cannot silently become a positive score.</p></div></div>${blockerList}<div class="coverage-footnote">The public bundle uses a separate six-axis model as well. This lab implements only the documented eight-category candidate. Input values stay in this browser’s local storage; no score data is sent to a server. <a href="../../research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md">Open the implementation record →</a></div></section>`;
}

function createDanelfinDemoRows() {
  const groups = [
    ['Technology', [['NVDA', 9.2, 8, 84000000, true], ['MSFT', 8.8, 7, 21000000, true], ['AVGO', 8.1, 6, 6400000, false], ['AMD', 7.8, 6, 35000000, true], ['ORCL', 7.1, 5, 9600000, false], ['INTC', 8.9, 4, 44000000, true]]],
    ['Health Care', [['LLY', 8.7, 8, 3100000, true], ['ISRG', 8.1, 7, 1500000, false], ['ABT', 7.7, 6, 5100000, true], ['AMGN', 7.3, 6, 2200000, false], ['VRTX', 6.9, 5, 1700000, true], ['PFE', 8.5, 5, 9200000, false]]],
    ['Financials', [['JPM', 8.5, 8, 10200000, true], ['V', 8.2, 7, 6100000, true], ['MA', 7.9, 6, 2900000, false], ['GS', 7.4, 6, 1900000, true], ['MS', 6.8, 5, 4900000, false], ['C', 8.4, 4, 12200000, true]]],
    ['Industrials', [['GE', 8.3, 8, 4600000, true], ['CAT', 7.9, 7, 2200000, false], ['ETN', 7.6, 6, 1400000, true], ['HON', 7.2, 6, 2300000, false], ['DE', 6.7, 5, 1700000, true], ['BA', 8.6, 5, 5300000, false]]],
    ['Communication', [['META', 8.2, 8, 12100000, true], ['GOOGL', 8.0, 7, 18400000, false], ['NFLX', 7.5, 6, 4300000, true], ['TMUS', 7.1, 6, 4500000, false], ['DIS', 6.6, 5, 8100000, true], ['CMCSA', 8.1, 5, 15400000, false]]],
    ['Energy', [['XOM', 7.5, 8, 13900000, true], ['CVX', 7.1, 7, 6500000, false], ['COP', 6.8, 6, 5100000, true], ['SLB', 6.4, 6, 8700000, false], ['EOG', 6.0, 5, 2300000, true], ['OXY', 7.8, 5, 96000, false]]],
  ];
  return groups.flatMap(([sector, names]) => names.map(([ticker, score, lowRisk, avg3mVolume, provenBuy]) => ({ ticker, sector, score, lowRisk, avg3mVolume, provenBuy, asOf: 'Synthetic' })));
}

function parseDanelfinCsv(source) {
  if (source.length > 10 * 1024 * 1024) throw new Error('Portfolio CSV files must be 10 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 2 || table.length > 10001) throw new Error('Use a header and between 1 and 10,000 candidate rows.');
  const header = table[0].map(value => value.trim().toLowerCase().replace(/[^a-z0-9]/g, ''));
  const column = (...aliases) => header.findIndex(name => aliases.includes(name));
  const indexes = {
    ticker: column('ticker', 'symbol', 'stocksymbol'),
    score: column('score', 'aiscore'),
    sector: column('sector', 'gicssector'),
    lowRisk: column('lowrisk', 'lowriskscore'),
    volume: column('avg3mvolume', 'average3mvolume', 'avg3monthvolume', 'average3monthvolume', 'avgvolume', 'averagevolume'),
    provenBuy: column('provenbuysignal', 'provenbuy', 'confirmedbuy', 'hasprovenbuysignal'),
    asOf: column('asof', 'date', 'snapshotdate', 'evaluationdate'),
    snapshotComplete: column('snapshotcomplete', 'exportcomplete', 'universeexportcomplete'),
  };
  const missing = ['ticker', 'score', 'sector', 'lowRisk', 'volume'].filter(key => indexes[key] < 0);
  if (missing.length) throw new Error(`Missing required CSV columns: ${missing.join(', ')}. Expected Ticker, Score, Sector, LowRisk, Avg3MVolume; ProvenBuySignal and AsOf are optional.`);
  const rows = [], seenSnapshotTickers = new Set(), dates = new Set(), completenessBySnapshot = new Map();
  let blankAsOf = false;
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
    let asOf = '';
    if (indexes.asOf >= 0) {
      const raw = String(cells[indexes.asOf] || '').trim();
      if (!raw) blankAsOf = true;
      else {
        const time = Date.parse(raw);
        if (!Number.isFinite(time)) throw new Error(`Row ${rowNumber}: AsOf/Date is not a readable date.`);
        asOf = new Date(time).toISOString().slice(0, 10);
        dates.add(asOf);
      }
    }
    let snapshotComplete = null;
    if (indexes.snapshotComplete >= 0) {
      const raw = String(cells[indexes.snapshotComplete] ?? '').trim().toLowerCase();
      if (['true', '1', 'yes', 'y', 'complete'].includes(raw)) snapshotComplete = true;
      else if (['false', '0', 'no', 'n', 'partial'].includes(raw)) snapshotComplete = false;
      else if (raw) throw new Error(`Row ${rowNumber}: SnapshotComplete must be true/false, yes/no, complete/partial, or blank.`);
      const key = asOf || 'UNDATED';
      if (completenessBySnapshot.has(key) && completenessBySnapshot.get(key) !== snapshotComplete) {
        throw new Error(`Row ${rowNumber}: SnapshotComplete must use one consistent value for ${asOf || 'the undated snapshot'}.`);
      }
      completenessBySnapshot.set(key, snapshotComplete);
    }
    const snapshotTickerKey = `${asOf || 'UNDATED'}|${ticker}`;
    if (seenSnapshotTickers.has(snapshotTickerKey)) throw new Error(`Row ${rowNumber}: duplicate ticker ${ticker} for ${asOf || 'the undated snapshot'}; use one row per symbol per snapshot.`);
    seenSnapshotTickers.add(snapshotTickerKey);
    const sector = String(cells[indexes.sector] || '').trim();
    if (!sector) throw new Error(`Row ${rowNumber}: sector is required.`);
    const score = numberAt(cells, indexes.score, 'Score', rowNumber);
    const lowRisk = numberAt(cells, indexes.lowRisk, 'LowRisk', rowNumber);
    const avg3mVolume = numberAt(cells, indexes.volume, 'Avg3MVolume', rowNumber);
    if (score < 1 || score > 10) throw new Error(`Row ${rowNumber}: Score must be between 1 and 10.`);
    if (lowRisk < 1 || lowRisk > 10) throw new Error(`Row ${rowNumber}: LowRisk must be between 1 and 10.`);
    if (avg3mVolume < 0) throw new Error(`Row ${rowNumber}: Avg3MVolume cannot be negative.`);
    let provenBuy = false;
    if (indexes.provenBuy >= 0) {
      const raw = String(cells[indexes.provenBuy] ?? '').trim().toLowerCase();
      if (['true', 'yes', '1', 'buy', 'confirmed'].includes(raw)) provenBuy = true;
      else if (!['', 'false', 'no', '0', 'none', 'no signal'].includes(raw)) throw new Error(`Row ${rowNumber}: ProvenBuySignal must be true/false, yes/no, or blank.`);
    }
    rows.push({ ticker, sector, score, lowRisk, avg3mVolume, provenBuy, asOf, snapshotComplete });
  }
  if (!rows.length) throw new Error('The CSV contains no candidate rows.');
  if (indexes.asOf >= 0 && dates.size && blankAsOf) throw new Error('Every row must include a valid AsOf/Date when any dated snapshots are present.');
  const snapshotDates = [...dates].sort();
  return {
    rows,
    provenBuyProvided: indexes.provenBuy >= 0,
    asOf: snapshotDates.at(-1) || '',
    startDate: snapshotDates[0] || '',
    snapshotDates,
  };
}

function buildDanelfinPortfolio(rows, preferProvenBuy = true) {
  const eligible = [], rejected = [];
  const sectorMap = new Map();
  for (const row of rows) {
    const reasons = [];
    if (row.lowRisk < 5) reasons.push('Low Risk below 5');
    if (row.avg3mVolume <= 100000) reasons.push('3-month average volume is not above 100,000');
    if (reasons.length) rejected.push({ ...row, decision: reasons.join('; '), decisionCode: 'filtered', sectorRank: null, nameRank: null, sectorMean: null });
    else {
      eligible.push(row);
      const key = row.sector.toLowerCase();
      if (!sectorMap.has(key)) sectorMap.set(key, { key, name: row.sector, rows: [] });
      sectorMap.get(key).rows.push(row);
    }
  }
  const sectors = [...sectorMap.values()].map(group => ({
    ...group,
    meanScore: group.rows.reduce((sum, row) => sum + row.score, 0) / group.rows.length,
  })).sort((a, b) => b.meanScore - a.meanScore || a.name.localeCompare(b.name));
  sectors.forEach((sector, index) => { sector.rank = index + 1; sector.inPortfolio = index < 5; });
  const chosenSectorKeys = new Set(sectors.slice(0, 5).map(sector => sector.key));
  const chosen = [];
  const nonChosen = [];
  for (const sector of sectors) {
    const ranked = sector.rows.slice().sort((a, b) => {
      if (preferProvenBuy && a.provenBuy !== b.provenBuy) return Number(b.provenBuy) - Number(a.provenBuy);
      return b.score - a.score || a.ticker.localeCompare(b.ticker);
    });
    ranked.forEach((row, index) => {
      const item = { ...row, sectorRank: sector.rank, sectorMean: sector.meanScore, nameRank: index + 1 };
      if (!chosenSectorKeys.has(sector.key)) nonChosen.push({ ...item, decision: 'Sector outside the top five', decisionCode: 'sector-out' });
      else if (index < 5) chosen.push({ ...item, decision: 'Selected', decisionCode: 'selected' });
      else nonChosen.push({ ...item, decision: 'Reserve beyond five names for this sector', decisionCode: 'reserve' });
    });
  }
  const weightPct = chosen.length ? 100 / chosen.length : 0;
  chosen.forEach(row => { row.weightPct = weightPct; });
  const auditRows = [...chosen, ...nonChosen, ...rejected].sort((a, b) => {
    const sectorA = a.sectorRank ?? Number.MAX_SAFE_INTEGER, sectorB = b.sectorRank ?? Number.MAX_SAFE_INTEGER;
    return sectorA - sectorB || (a.nameRank ?? Number.MAX_SAFE_INTEGER) - (b.nameRank ?? Number.MAX_SAFE_INTEGER) || a.ticker.localeCompare(b.ticker);
  });
  return { eligible, sectors, chosen, auditRows, filteredCount: rejected.length, preferProvenBuy };
}

function shiftDanelfinCalendarDate(dateValue, months) {
  if (!validProfileDate(dateValue) || !Number.isInteger(months)) return null;
  const [year, month, day] = dateValue.split('-').map(Number);
  const firstOfMonth = new Date(Date.UTC(year, month - 1, 1));
  firstOfMonth.setUTCMonth(firstOfMonth.getUTCMonth() + months);
  const targetYear = firstOfMonth.getUTCFullYear(), targetMonth = firstOfMonth.getUTCMonth();
  const lastDay = new Date(Date.UTC(targetYear, targetMonth + 1, 0)).getUTCDate();
  const result = new Date(Date.UTC(targetYear, targetMonth, Math.min(day, lastDay)));
  return result.toISOString().slice(0, 10);
}

function buildDanelfinRebalancePlan(rows, startDate, preferProvenBuy = true) {
  const snapshots = new Map();
  for (const row of rows) {
    if (!validProfileDate(row.asOf)) continue;
    if (!snapshots.has(row.asOf)) snapshots.set(row.asOf, []);
    snapshots.get(row.asOf).push(row);
  }
  const snapshotDates = [...snapshots.keys()].sort();
  const inceptionDate = validProfileDate(startDate) ? startDate : snapshotDates[0] || '';
  if (!snapshotDates.length || !inceptionDate) return { status: 'NO_DATED_SNAPSHOTS', startDate: inceptionDate, snapshotDates, events: [], maxSnapshotAgeDays: 7 };

  const maxSnapshotAgeDays = 7;
  const lastSnapshotDate = snapshotDates.at(-1);
  const events = [];
  let priorTickers = [];
  for (let monthOffset = 0; monthOffset <= 1200; monthOffset += 3) {
    const dueDate = shiftDanelfinCalendarDate(inceptionDate, monthOffset);
    if (!dueDate) break;
    const snapshotDate = snapshotDates.filter(date => date <= dueDate).at(-1) || '';
    const ageDays = snapshotDate ? (Date.parse(`${dueDate}T00:00:00Z`) - Date.parse(`${snapshotDate}T00:00:00Z`)) / 86400000 : null;
    const annualWeightReviewDue = monthOffset === 0 || monthOffset % 12 === 0;
    if (!snapshotDate || ageDays > maxSnapshotAgeDays) {
      events.push({
        monthOffset, dueDate, snapshotDate, ageDays, status: 'NO_FRESH_SNAPSHOT',
        selectedTickers: [], addedTickers: [], removedTickers: [],
        annualWeightReviewDue, targetWeightPct: null,
      });
      if (dueDate > lastSnapshotDate) break;
      continue;
    }
    const snapshotRows = snapshots.get(snapshotDate);
    const snapshotCompleteness = snapshotRows[0]?.snapshotComplete;
    if (snapshotCompleteness !== true) {
      events.push({
        monthOffset, dueDate, snapshotDate, ageDays,
        status: snapshotCompleteness === false ? 'SNAPSHOT_DECLARED_PARTIAL' : 'SNAPSHOT_COMPLETENESS_UNKNOWN',
        selectedTickers: [], addedTickers: [], removedTickers: [],
        annualWeightReviewDue, targetWeightPct: null,
      });
      if (dueDate > lastSnapshotDate) break;
      continue;
    }
    const portfolio = buildDanelfinPortfolio(snapshotRows, preferProvenBuy);
    const selectedTickers = portfolio.chosen.map(row => row.ticker);
    const selectedSet = new Set(selectedTickers), priorSet = new Set(priorTickers);
    const addedTickers = selectedTickers.filter(ticker => !priorSet.has(ticker)).sort();
    const removedTickers = priorTickers.filter(ticker => !selectedSet.has(ticker)).sort();
    events.push({
      monthOffset, dueDate, snapshotDate, ageDays,
      status: monthOffset === 0 ? 'INITIAL_ALLOCATION' : 'MEMBERSHIP_REVIEW',
      selectedTickers, addedTickers, removedTickers,
      annualWeightReviewDue,
      targetWeightPct: annualWeightReviewDue && selectedTickers.length ? 100 / selectedTickers.length : null,
    });
    priorTickers = selectedTickers;
    if (dueDate > lastSnapshotDate) break;
  }
  return {
    status: events.some(event => event.status !== 'NO_FRESH_SNAPSHOT') ? 'READY' : 'NO_FRESH_SNAPSHOT',
    startDate: inceptionDate,
    lastSnapshotDate,
    maxSnapshotAgeDays,
    snapshotCount: snapshotDates.length,
    events,
  };
}

function renderDanelfinPortfolioLab() {
  const stateData = state.danelfinPortfolio;
  if (!stateData.rows.length) stateData.rows = createDanelfinDemoRows();
  const snapshotDates = [...new Set(stateData.rows.map(row => row.asOf).filter(validProfileDate))].sort();
  const selectedSnapshotRows = stateData.asOf ? stateData.rows.filter(row => row.asOf === stateData.asOf) : stateData.rows;
  const result = buildDanelfinPortfolio(selectedSnapshotRows, stateData.preferProvenBuy);
  const plan = buildDanelfinRebalancePlan(stateData.rows, stateData.startDate || snapshotDates[0] || '', stateData.preferProvenBuy);
  const chosenRows = result.chosen.length ? result.chosen.map((row, index) => `<tr><td>${index + 1}</td><td><b>${esc(row.ticker)}</b></td><td>${esc(row.sector)}</td><td>${row.score.toFixed(1)}</td><td>${row.lowRisk.toFixed(1)}</td><td>${integer(row.avg3mVolume)}</td><td>${row.provenBuy ? label('CONFIRMED', 'coverage-local') : '<span class="muted">—</span>'}</td><td>${row.weightPct.toFixed(2)}%</td></tr>`).join('') : '<tr><td colspan="8" class="muted">No names qualify with the current input.</td></tr>';
  const sectorRows = result.sectors.slice(0, 50).map(sector => `<tr><td>${sector.rank}</td><td><b>${esc(sector.name)}</b></td><td>${sector.meanScore.toFixed(2)}</td><td>${sector.rows.length}</td><td>${sector.inPortfolio ? label('TOP 5', 'coverage-local') : label('OUTSIDE TOP 5', 'coverage-none')}</td></tr>`).join('') || '<tr><td colspan="5" class="muted">No names pass both eligibility filters.</td></tr>';
  const auditLimit = 250;
  const auditRows = result.auditRows.slice(0, auditLimit).map(row => `<tr><td>${esc(row.ticker)}</td><td>${esc(row.sector)}</td><td>${row.score.toFixed(1)}</td><td>${row.lowRisk.toFixed(1)}</td><td>${integer(row.avg3mVolume)}</td><td>${row.provenBuy ? 'Yes' : 'No'}</td><td>${row.sectorRank ? `#${row.sectorRank} · ${row.sectorMean.toFixed(2)}` : '—'}</td><td><span class="portfolio-decision ${row.decisionCode}">${esc(row.decision)}</span></td></tr>`).join('') || '<tr><td colspan="8" class="muted">No candidate rows.</td></tr>';
  const dataError = stateData.error ? `<div class="strategy-error">${esc(stateData.error)}</div>` : '';
  const dateCaption = stateData.asOf ? `As of ${esc(stateData.asOf)}` : 'As-of date not supplied';
  const nameList = values => values.length ? esc(values.join(', ')) : '—';
  const planRows = plan.events.map(event => {
    const accepted = ['INITIAL_ALLOCATION', 'MEMBERSHIP_REVIEW'].includes(event.status);
    const status = event.status.replace(/_/g, ' ');
    const weightAction = event.targetWeightPct !== null ? `${event.targetWeightPct.toFixed(2)}% target / position` : event.annualWeightReviewDue ? 'Due; snapshot unavailable' : 'No annual reset due';
    return `<tr><td>${esc(event.dueDate)}</td><td>${esc(event.snapshotDate || '—')}</td><td>${event.ageDays === null ? '—' : `${event.ageDays}d`}</td><td>${esc(status)}</td><td>${accepted ? nameList(event.addedTickers) : '—'}</td><td>${accepted ? nameList(event.removedTickers) : '—'}</td><td>${accepted ? event.selectedTickers.length : '—'}</td><td>${esc(weightAction)}</td></tr>`;
  }).join('');
  const scheduleRows = planRows || `<tr><td colspan="8">${snapshotDates.length ? 'No scheduled event is supported by the selected start date and supplied snapshots.' : 'Add dated snapshots to build a rebalance schedule.'}</td></tr>`;
  const scheduleCoverageNote = snapshotDates.length === 0
    ? 'No dated snapshots are available; add dated, complete snapshots to inspect scheduled selections.'
    : snapshotDates.length === 1
      ? 'Only one dated snapshot is available; later membership reviews remain unknown until more snapshots are supplied.'
      : '';
  const signalNote = stateData.provenBuyProvided ? '' : '<span class="portfolio-signal-note">No ProvenBuySignal column was supplied; all candidates are treated as not confirmed.</span>';
  const actions = `<button class="button secondary" data-action="portfolio-demo">Load synthetic sample</button><button class="button secondary" data-action="portfolio-export" ${stateData.rows.length ? '' : 'disabled'}>Export decision audit</button>`;
  return `${pageHeading('PUBLIC METHOD · INDEPENDENT CONSTRUCTOR', 'Sector Portfolio Lab', 'A point-in-time portfolio constructor from the published selection rules. Import scores you already have; this tool does not produce or validate the underlying AI Score.', actions)}
    <div class="evidence-callout portfolio-callout"><b>Clean-room implementation boundary</b><span>The public write-up specifies Low Risk ≥ 5, average three-month volume &gt; 100, the five sectors with the highest mean passing score, five names per selected sector, Proven Buy priority within those sectors, and equal weights. Danelfin’s server-side score model, features, weights, and historical vintage are not public. This lab does not reproduce them or claim an edge. Ties and the optional score-only override are explicit local reconstruction choices.</span><a href="../../research/rea-teardowns/danelfin/TEARDOWN.md">Review teardown evidence →</a></div>
    <div class="strategy-data-banner portfolio-data-banner"><div><span class="coverage-state ${stateData.source === 'csv' ? 'coverage-local' : 'coverage-partial'}">${stateData.source === 'csv' ? 'LOCAL CSV' : 'SYNTHETIC SAMPLE'}</span><b>${esc(stateData.filename)}</b><small>${stateData.rows.length.toLocaleString()} input rows · ${snapshotDates.length} dated snapshots · latest ${dateCaption} · input stays in memory in this browser tab</small>${stateData.notice ? `<small class="strategy-notice">${esc(stateData.notice)}</small>` : ''}${signalNote}</div><label class="button primary file-pick">Choose CSV<input id="portfolio-file" type="file" accept=".csv,text/csv" /></label></div>
    <div class="portfolio-schema-note"><b>CSV columns:</b> required <code>Ticker, Score, Sector, LowRisk, Avg3MVolume</code> · optional <code>ProvenBuySignal, AsOf, SnapshotComplete</code>. Scores must be 1–10; volume is average daily shares, not dollars. Use one row per symbol per dated snapshot. For schedule replay, every row in a snapshot must declare <code>SnapshotComplete=true</code>; this is your assertion about the supplied snapshot, not proof of full-market coverage.</div>
    ${dataError}
    <div class="coverage-summary portfolio-summary"><div><b>${selectedSnapshotRows.length.toLocaleString()}</b><span>selected-snapshot rows</span></div><div><b>${result.eligible.length.toLocaleString()}</b><span>pass both filters</span></div><div><b>${result.chosen.length}/25</b><span>selected positions</span></div><div><b>${result.chosen.length ? `${(100 / result.chosen.length).toFixed(2)}%` : '—'}</b><span>initial equal-weight target</span></div></div>
    <section class="panel portfolio-settings"><div class="panel-heading"><div><h2>Selection controls</h2><p>Score and risk values are imported as supplied; sector means use only names passing both filters.</p></div></div><label class="portfolio-toggle"><input type="checkbox" data-portfolio-preference ${stateData.preferProvenBuy ? 'checked' : ''} /> Prefer confirmed Proven Buy names within each selected sector before score ranking</label><span class="small-muted">If selected, the priority signal is the first ordering key, followed by score descending and ticker ascending. Turn this off to rank by score only.</span></section>
    <section class="panel portfolio-sector-panel"><div class="panel-heading"><div><h2>Sector rank</h2><p>Mean score across eligible names; highest five sectors define the portfolio universe.</p></div><span class="small-muted">${result.sectors.length} eligible sectors</span></div><div class="table-wrap"><table><thead><tr><th>RANK</th><th>SECTOR</th><th>MEAN SCORE</th><th>ELIGIBLE NAMES</th><th>CONSTRUCTION</th></tr></thead><tbody>${sectorRows}</tbody></table></div>${result.sectors.length > 50 ? `<div class="portfolio-table-note">Showing first 50 of ${result.sectors.length} sectors by mean score.</div>` : ''}</section>
    <section class="panel portfolio-selected-panel"><div class="panel-heading"><div><h2>Current equal-weight portfolio</h2><p>${result.chosen.length ? `${result.chosen.length} of 25 possible names · ${result.chosen.length < 25 ? 'under-filled because qualifying inputs are limited' : 'full 25-name construction'}` : 'No qualifying names in the supplied snapshot'}</p></div><span class="small-muted">${dateCaption}</span></div><div class="table-wrap"><table><thead><tr><th>#</th><th>TICKER</th><th>SECTOR</th><th>SCORE</th><th>LOW RISK</th><th>AVG 3M VOLUME</th><th>PROVEN BUY</th><th>WEIGHT</th></tr></thead><tbody>${chosenRows}</tbody></table></div></section>
    <section class="panel portfolio-schedule-panel"><div class="panel-heading"><div><h2>Membership reviews and annual weight targets</h2><p>Schedule cycles use calendar-month anniversaries anchored to the declared portfolio start date.</p></div><label class="field-label">PORTFOLIO START DATE<input type="date" data-portfolio-start-date value="${esc(plan.startDate || '')}" ${snapshotDates.length ? '' : 'disabled'} /></label></div><p class="small-muted">Each scheduled review uses the latest supplied snapshot dated on or before the event; snapshots older than 7 calendar days or lacking <code>SnapshotComplete=true</code> are left unknown. Annual rows show an equal-weight target only. This planner does not calculate actual weight drift or returns without position and price history.</p><div class="table-wrap"><table><thead><tr><th>REVIEW DATE</th><th>INPUT SNAPSHOT</th><th>AGE</th><th>STATE</th><th>ADDITIONS</th><th>REMOVALS</th><th>SELECTED</th><th>WEIGHT TARGET</th></tr></thead><tbody>${scheduleRows}</tbody></table></div>${scheduleCoverageNote ? `<div class="portfolio-table-note">${esc(scheduleCoverageNote)}</div>` : ''}</section>
    <section class="panel portfolio-audit-panel"><div class="panel-heading"><div><h2>Candidate decision audit</h2><p>Filter failures, sector exclusions, reserves, and selected names are listed with the applied decision.</p></div><span class="small-muted">${result.auditRows.length.toLocaleString()} total candidates</span></div><div class="table-wrap"><table><thead><tr><th>TICKER</th><th>SECTOR</th><th>SCORE</th><th>LOW RISK</th><th>AVG 3M VOL</th><th>BUY</th><th>SECTOR RANK / MEAN</th><th>DECISION</th></tr></thead><tbody>${auditRows}</tbody></table></div>${result.auditRows.length > auditLimit ? `<div class="portfolio-table-note">Showing first ${auditLimit} of ${result.auditRows.length.toLocaleString()} candidates. Export includes the full decision audit.</div>` : ''}</section>
    <div class="strategy-disclaimer portfolio-disclaimer">This is a user-supplied membership-reconstitution planner based on published selection rules and review timing. It is not Danelfin’s historical backtest: score vintages and full-universe inputs are unverified, and no realized returns, weight drift, transaction costs, taxes, corporate actions, or survivorship correction are modeled. Uploaded scores, classifications, and completeness labels must be checked against their source and date before research use.</div>`;
}

function renderVendorCoverage() {
  const meta = state.vendorCoverageMeta;
  const families = state.vendorFamilies;
  const query = state.vendorSearch.trim().toLowerCase();
  const filtered = families.filter(v => {
    const matchesText = !query || `${v.name} ${v.slug} ${coverageLanes[v.lane]?.name || ''}`.toLowerCase().includes(query);
    const matchesLane = state.vendorLane === 'all' || v.lane === state.vendorLane;
    const matchesResearch = state.vendorResearch === 'all' || v.research === state.vendorResearch;
    return matchesText && matchesLane && matchesResearch;
  });
  const onchainCount = families.filter(v => v.lane === 'onchain').length;
  const fullReplicaCount = 0;
  const laneCards = Object.entries(coverageLanes).map(([id, lane]) => {
    const count = families.filter(v => v.lane === id).length;
    return `<article class="coverage-lane"><div><span>${esc(lane.name)}</span><b>${count}</b></div><small>${esc(lane.routes)}</small><p>${esc(lane.gap)}</p><span class="coverage-state ${id === 'onchain' ? 'coverage-none' : 'coverage-partial'}">${id === 'onchain' ? 'NOT IMPLEMENTED' : 'PARTIAL SHARED SURFACE'}</span></article>`;
  }).join('');
  const cards = filtered.map(v => {
    const lane = coverageLanes[v.lane] || { name: 'Unmapped', gap: '' };
    const isLeadrCandidate = v.slug === 'leadr-labs-original';
    const isDanelfinCandidate = v.slug === 'danelfin';
    const isSpotGammaCandidate = v.slug === 'spotgamma';
    const isOptionStratCandidate = v.slug === 'optionstrat';
    const isBullflowCandidate = v.slug === 'bullflow';
    const isFinvizCandidate = v.slug === 'finviz-screener';
    const isStockRoverCandidate = v.slug === 'stock-rover';
    const isAzraelCandidate = v.slug === 'azrael-options';
    const isPartialCandidate = isLeadrCandidate || isDanelfinCandidate || isSpotGammaCandidate || isOptionStratCandidate || isBullflowCandidate || isFinvizCandidate || isStockRoverCandidate || isAzraelCandidate;
    const status = v.lane === 'onchain' ? 'NOT IMPLEMENTED' : isPartialCandidate ? 'PARTIAL CANDIDATE' : 'PARTIAL';
    const reportState = v.research === 'in-progress' ? 'RESEARCH IN PROGRESS' : 'RESEARCH COMPLETE';
    const reportPath = isLeadrCandidate ? 'research/leadr_labs/LEADR-REVERSE-ENGINEERING.md' : isDanelfinCandidate ? 'research/rea-teardowns/danelfin/TEARDOWN.md' : isSpotGammaCandidate ? 'research/rea-teardowns/spotgamma/TEARDOWN.md' : isOptionStratCandidate ? 'research/rea-teardowns/optionstrat/TEARDOWN.md' : isBullflowCandidate ? 'research/rea-teardowns/bullflow/TEARDOWN.md' : isFinvizCandidate ? 'research/rea-teardowns/finviz-screener/TEARDOWN.md' : isStockRoverCandidate ? 'research/rea-teardowns/stockrover/TEARDOWN.md' : isAzraelCandidate ? 'research/rea-teardowns/azrael-1587/TEARDOWN.md' : `research/rea_teardowns/targets/${encodeURIComponent(v.slug)}.md`;
    const reportUrl = `https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/${reportPath}`;
    const implementationLink = isLeadrCandidate
      ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open candidate build notes ↗</a>'
      : isDanelfinCandidate
        ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/danelfin/PORTFOLIO-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open constructor build notes ↗</a>'
        : isSpotGammaCandidate
          ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/spotgamma/GEX-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open GEX lab build notes ↗</a>'
        : isOptionStratCandidate
          ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/optionstrat/OPTIONSTRAT-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open option lab build notes ↗</a>'
        : isBullflowCandidate
          ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/bullflow/ACTIVITY-PROFILE-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open activity profile build notes ↗</a>'
        : isFinvizCandidate
          ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/finviz-screener/FINVIZ-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open filter contract build notes ↗</a>'
        : isStockRoverCandidate
          ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/stockrover/STOCKROVER-FACTOR-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open factor lab build notes ↗</a>'
        : isAzraelCandidate
          ? '<a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/azrael-1587/MAP-LAB-IMPLEMENTATION.md" target="_blank" rel="noreferrer">Open map lab build notes ↗</a>'
        : '';
    const productGap = isLeadrCandidate
      ? 'Public eight-category model candidate with manual normalized inputs; production score remains unverified.'
      : isDanelfinCandidate
        ? 'Public sector-ranked portfolio construction with user-supplied scores; server-side AI Score remains opaque.'
        : isSpotGammaCandidate
          ? 'Published static GEX formula with user-supplied open interest; proprietary intraday positioning remains sealed.'
        : isOptionStratCandidate
          ? 'Manual multi-leg expiration payoff constructor; the proprietary optimizer ranking, pricing stack, and flow score are not reproduced.'
        : isBullflowCandidate
          ? 'Published 20-session volume profile and thresholds using user-supplied prints; SigScore and proprietary alert triggers remain sealed.'
        : isFinvizCandidate
          ? 'Local CSV implementation of a documented subset of filter algebra, repeated-filter override, ticker-list ordering, and sorting; Finviz data and pattern detection are not recreated.'
        : isStockRoverCandidate
          ? 'Local cross-sectional reconstruction of the published four-factor input lists with transparent equal-weight desk choices; vendor normalization, weights, DCF, and safety overlays are not reproduced.'
        : isAzraelCandidate
          ? 'Public 15.87 expected-move map, regime bands, square-root funded range, and target-band description using manual prior-close inputs; OI shortlist and intraday setup engine remain out of scope.'
        : `${lane.name} · ${lane.gap}`;
    const candidateRoute = isLeadrCandidate ? 'confluence' : isDanelfinCandidate ? 'portfolio' : isSpotGammaCandidate ? 'staticgex' : isOptionStratCandidate ? 'optionlab' : isBullflowCandidate ? 'bullflow' : isFinvizCandidate ? 'finviz' : isStockRoverCandidate ? 'stockrover' : isAzraelCandidate ? 'azrael' : '';
    return `<article class="coverage-vendor"><div class="coverage-vendor-top"><span class="coverage-state ${status.startsWith('PARTIAL') ? 'coverage-partial' : 'coverage-none'}">${status}</span><span class="coverage-research">${reportState}</span></div><h3>${esc(v.name)}</h3><p>${esc(productGap)}</p><a href="${reportUrl}" target="_blank" rel="noreferrer">Open teardown evidence ↗</a>${implementationLink}${candidateRoute ? `<button class="text-button" data-view="${candidateRoute}">Open candidate tool →</button>` : ''}</article>`;
  }).join('');
  const loadState = state.coverageError && !families.length
    ? `<div class="coverage-error">${esc(state.coverageError)} Start the local server from this folder and reload.</div>`
    : !families.length
      ? '<div class="coverage-error">Loading the 86-family registry…</div>'
      : filtered.length ? cards : '<div class="coverage-error">No families match those filters.</div>';
  return `${pageHeading('IMPLEMENTATION AUDIT', 'Vendor coverage map', 'All teardown target families are tracked below. This independent suite is not a set of vendor replicas; the status describes current shared product surfaces only.', '<button class="button primary" data-view="strategy">Open Strategy Lab →</button>')}
    <div class="coverage-summary"><div><b>${meta.requestedPasses}</b><span>teardown passes</span></div><div><b>${meta.targetFamilies}</b><span>target families</span></div><div><b>${fullReplicaCount}</b><span>full vendor replicas</span></div><div><b>${onchainCount}</b><span>families with no suite surface</span></div></div>
    <div class="coverage-lane-grid">${laneCards}</div>
    <section class="panel coverage-registry"><div class="panel-heading"><div><h2>Target-family registry</h2><p>${filtered.length} of ${families.length || meta.targetFamilies} families · teardown status is separate from implementation status</p></div><span class="small-muted">As of ${esc(meta.asOf || '2026-10-27')}</span></div>
      <div class="coverage-controls"><label class="field-label">SEARCH<input data-filter="vendorSearch" value="${esc(state.vendorSearch)}" placeholder="Vendor or product family" /></label><label class="field-label">PRODUCT LANE<select data-filter="vendorLane"><option value="all" ${state.vendorLane === 'all' ? 'selected' : ''}>All lanes</option>${Object.entries(coverageLanes).map(([id, lane]) => `<option value="${id}" ${state.vendorLane === id ? 'selected' : ''}>${esc(lane.name)}</option>`).join('')}</select></label><label class="field-label">RESEARCH STATUS<select data-filter="vendorResearch"><option value="all" ${state.vendorResearch === 'all' ? 'selected' : ''}>All reports</option><option value="complete" ${state.vendorResearch === 'complete' ? 'selected' : ''}>Research complete</option><option value="in-progress" ${state.vendorResearch === 'in-progress' ? 'selected' : ''}>Research in progress</option></select></label></div>
      <div class="coverage-grid">${loadState}</div>
      <div class="coverage-footnote">“Research complete” means the public-source teardown met the repository’s evidence boundary. It does not mean protected runtime, licensed data, vendor source code, or a full product recreation was verified. Eight target reports still list unresolved artifact or runtime inputs.</div>
    </section>`;
}

const evidenceDependencies = [
  { name: 'Price bars and technical features', sources: 'OHLCV history · corporate actions · universe membership', examples: 'RSI · moving averages · breakouts · trend ranks · chart patterns', rule: 'These features usually reuse the same price history. Group them as one price-derived family and test incremental value.' },
  { name: 'Options prints and quote context', sources: 'OPRA prints · condition codes · NBBO or latest-quote joins', examples: 'Sweeps · premium totals · buyer/seller estimates · flow alerts', rule: 'Deduplicate shared prints where possible. Separate the observed print from estimated side and inferred intent.' },
  { name: 'Option-chain inventory models', sources: 'Open interest · Greeks · sign and dealer-position assumptions', examples: 'GEX · gamma walls · zero-gamma · dealer-positioning summaries', rule: 'Treat these as one modeled inventory family. Show OI vintage, dropped contracts, and assumptions.' },
  { name: 'Filings and short-position reports', sources: '13F · Form 4 · FINRA settlement files · short volume', examples: 'Ownership · insider activity · short interest · short-volume ratios', rule: 'Keep publication and settlement dates, float basis, and definitions separate; do not merge them into generic “smart money.”' },
  { name: 'News and event source chains', sources: 'Original article or filing · republisher · alert ingestion time', examples: 'Catalyst scans · newsletters · event alerts · trade calls', rule: 'Cluster repeated coverage of one catalyst and retain original publication and system-ingestion times.' },
  { name: 'On-chain facts and attribution', sources: 'Chain transaction · exchange or venue · entity-label provider', examples: 'Wallet flow · entity activity · exchange movement', rule: 'Store the transaction separately from the vendor’s entity label and its confidence/version.' },
];

const auditedBuilds = [
  { name: 'Zeiierman Trading · public product, pricing, and rights boundary', status: 'PUBLIC EVIDENCE / NO VENDOR LOGIC', cls: 'coverage-partial', text: 'Summarizes dated public disclosures only. Invite-Only scripts, private signals, account state, paid data, and trading execution are not connected or reproduced.', details: ['Official help identifies Arcturus Algo and Crypto Punk Bot as Invite-Only Scripts, says its scripts are proprietary and not shared, and describes alerts routed through third-party execution services. No private script or live order behavior was accessed.', 'Current pricing lists $95.20/month billed monthly, $59.99/month billed quarterly, and $37.99/month billed annually. Access timing differs across pages: 2–5 minutes in help versus instant/within one minute on pricing. No checkout or entitlement was verified.', 'Current Terms restrict reverse engineering/transcription, scraping/security circumvention, and commercial reproduction of service content. The separate Neural Weight Oscillator is labeled CC BY-NC-SA 4.0; its source was not copied into Silicon.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/zeiierman.md#current-first-party-recheck-2026-10-28', linkText: 'Open dated evidence report ↗', secondaryLink: 'https://docs.zeiierman.com/help/indicator-and-bots', secondaryLinkText: 'Open first-party help page ↗' },
  { name: 'ChartPrime · public product and rights contract', status: 'PUBLIC EVIDENCE / NO VENDOR LOGIC', cls: 'coverage-partial', text: 'Summarizes ChartPrime public product, policy, pricing, privacy, and access disclosures. No Pine source, indicator calculation, private data, or trading execution is reproduced or connected.', details: ['The 2026-10-28 homepage displayed Pro at $67/month or $489/year, Plus at $117/month or $708/year, and a 20% PRIME20 offer; checkout was not opened. The 2026-10-26 capture recorded a 30% offer.', 'Terms dated 2026-10-02 prohibit reverse engineering, copying or extracting indicator logic, access-control bypass, and automated collection without written permission. Exchange data remains separately licensed.', 'The Privacy Policy describes account/platform identifiers, purchase and eligibility data, device/usage information, cookies, and advertising disclosures. It says the role updater does not read messages or track presence. These are policy claims, not tested runtime behavior.', 'The refund page remains dated 2023-12-12, states seven-day refund requests, and routes cancellation through live support; newer Terms describe email cancellation and generally non-refundable lifetime plans. Purchase-specific policy precedence is unresolved.', 'Prime Automation marketing claims one-click activation, live result tracking, and 24/7 trading, but public material does not establish venue, account authorization, order lifecycle, or audited performance.', 'No account, private Discord, invite-only TradingView script, checkout, feed, broker, or vendor source was accessed; no code was copied and no access control was bypassed.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/chartprime.md#L53', linkText: 'Open current evidence report ↗', secondaryLink: 'https://chartprime.com/terms-conditions', secondaryLinkText: 'Open first-party Terms ↗' },
  { name: 'Quant Data · public API contract', status: 'PUBLIC CONTRACT / NO LIVE FEED', cls: 'coverage-partial', text: 'The public docs describe options REST endpoints and hosted MCP access, but their examples are not observed API responses. Silicon’s options-flow, exposure, and dark-pool pages remain synthetic and do not connect to Quant Data.', details: ['The 2026-10-28 first-party docs recheck confirms Bearer-key REST/MCP access, a shared documented request quota, and Streaming marked “Coming Soon.” No API key, endpoint, MCP call, account, or paid feed was used.', 'The docs list separate options and CME futures products, but the reviewed REST catalog did not show a futures endpoint. Dashboard/mobile sync, feed quality, completeness, latency, and advertised uptime were not independently tested.', 'The current linked Terms and Privacy pages could not be retrieved. The project contains no Quant Data API-specific license, data grant, or vendor source artifact; protected data and code are not integrated.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/quant-data.md#L62', linkText: 'Open Quant Data evidence report ↗', secondaryLink: 'https://quantdata.us/api/docs/introduction', secondaryLinkText: 'Open public API docs ↗' },
  { name: 'Optionality / Sinux Signals · alert evidence audit', status: 'PUBLIC EVIDENCE ONLY', cls: 'coverage-partial', text: 'The public alert schema shows symbol, contract, entry range, size, timestamp, desk, and thread updates. Its sample is explicitly illustrative, and the linked live-P&L dashboard returned only an app shell without authentication. No private Discord history, fills, or P&L were inspected.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/optionality-sinux.md', linkText: 'Open alert evidence review ↗' },
  { name: 'Stock Moe Earner · public offer audit', status: 'PUBLIC OFFER AUDIT', cls: 'coverage-partial', text: 'The public offer separates Earner from Earner Plus; feature delivery, session schedule, and captured listing prices remain vendor-advertised. Private bot payloads, signal history, and performance are unverified.', details: ['At the 2026-10-26 capture, the current Earner listing showed $49.99/month. Separate linked records showed Earner plus indicator at $99.99/month, Earner annual at $499/year, and Earner lifetime at $2,999.', 'Separate Earner Plus creator-catalog records showed $162.99/month, $48/week, $1,649.99/year, and “Lifetime” at $410/month; older variants showed $249.99/month and $2,499/year. Keep each record separate: these are not one canonical tier schedule, and price/availability can change.', 'Earner advertises Tuesday/Thursday sessions; Earner Plus adds a Wednesday livestream, exclusive support channel, and invite-only Bread Recipe TradingView indicator. No Discord role, private bot output, TradingView invite, or account was accessed.', 'AI-generated, backtested, reversal, and performance descriptions are seller claims. No script source, test report, signal history, fills, or strategy returns were inspected. Public Whop listings state no refunds because access is immediate.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/stock-moe.md#pricing-and-listing-drift', linkText: 'Open offer and price evidence ↗', secondaryLink: 'https://whop.com/stock-moe/stock-moe-earner-discord/', secondaryLinkText: 'Open public Earner listing ↗' },
  { name: 'AIME / AIME+ · AI research surface', status: 'PUBLIC SURFACE ONLY', cls: 'coverage-partial', text: 'AIME is described as an AI research terminal; the related Aime mobile app is a separate listing. Shared models, backend, entitlements, and mobile privacy behavior are not established.', details: ['AIME terms warn that generated information can be wrong, stale, incomplete, or fabricated.', 'The privacy policy describes processing and retention of prompts, voice interactions, and linked brokerage data for service operation and improvement. No chat, voice input, or brokerage connection was used.', 'The separate API terms limit API use to personal, internal, non-commercial purposes and restrict copying/export and competitive use. No API key, API data, or vendor code is used here.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md#product-boundary', linkText: 'Open AIME product boundary ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md#api-and-access-boundary', secondaryLinkText: 'Open API and access limits ↗' },
  { name: 'Magic Signal · public claim audit', status: 'CLAIMS NOT REPRODUCED', cls: 'coverage-partial', text: 'Public materials contain materially different performance and update descriptions. The underlying model, training/evaluation data, and complete signal rules remain unknown; no Magic Signal engine is implemented.', details: ['The feature page advertises “up to 64% prediction accuracy”; an AInvest-hosted share article describes different backtest thresholds and sub-100ms alerts, while a later guide says the signal list updates at market close.', 'The sources do not establish comparable targets, samples, or update semantics. Treat these as separate vendor claims, not a validated track record.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md#magic-signal-claims-and-privacy', linkText: 'Open Magic Signal claim review ↗' },
  { name: 'Option Pilot · options score evidence', status: 'PUBLIC METHOD / NO EDGE SHOWN', cls: 'coverage-partial', text: 'Option Pilot is a separate options research and scoring product. Its report documents the published score, data timing, corrections, a null predictive test, and unresolved public-page conflicts.', details: ['Published method: Value 25%, Sentiment 20%, Activity 20%, Liquidity 20%, Timing 15%; relative context is described as 50% ticker, 30% sector, and 20% universe. A glossary instead says equal weights; universe counts and the 0–100 pillar versus 0–10 overall scale also conflict.', 'The policy names ThetaData, Polygon.io, and Financial Modeling Prep; it reports prior-session inputs and a one-session OCC open-interest lag. Disclosed corrections: straddle volatility was 2x too high until 2026-09-05; IV rank was broken for thousands of names for about two weeks and fixed 2026-09-03. Affected outputs were not independently reconstructed.', 'For 2025-12-17 through 2026-09-04, the published 172-session test (~2,943 liquid names/session; about 500,000 ticker-days) reports one-day IC +0.0001, 95% CI [−0.011, +0.011], and flat deciles. Treat the score as a screen, not demonstrated return prediction.', 'The track-record page showed a zero-trade summary alongside nonzero strategy details; the live forward table was stale at capture. These are unresolved vendor-reported conflicts, not verified performance. Evidence was captured 2026-10-26.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md#option-pilot-scoring-reconstruction', linkText: 'Open Option Pilot methodology ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md#data-backtests-and-performance-disclosures', secondaryLinkText: 'Open data and performance evidence ↗' },
  { name: 'Leadr Labs · Codex + Midna', status: 'PARTIAL MODEL CANDIDATE', cls: 'coverage-partial', text: 'The Confluence Lab separates the descriptive 55-field metadata candidate from a partial 17-leaf v3Effective path. Inputs are local and ticker-scoped; market-context framework and production scoring remain unavailable.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md', linkText: 'Open candidate build notes ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/leadr_labs/midna_rea_pass/TEARDOWN.md', secondaryLinkText: 'Open paired-pass verdict ↗', route: 'confluence' },
  { name: 'Danelfin · portfolio construction', status: 'PARTIAL CONSTRUCTION CANDIDATE', cls: 'coverage-partial', text: 'Builds the published Low Risk and liquidity filters, top-five sector ranking, top-five names per sector, and equal-weight snapshot from user-supplied scores. Dated complete snapshots can drive quarterly membership reviews and annual target weights; actual drift and returns are not modeled. The server-side AI Score and historical-vintage provenance are not recreated.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/danelfin/PORTFOLIO-LAB-IMPLEMENTATION.md', linkText: 'Open constructor build notes ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/danelfin/TEARDOWN.md', secondaryLinkText: 'Open teardown evidence ↗', route: 'portfolio' },
  { name: 'SpotGamma · existing static GEX candidate', status: 'RIGHTS HOLD · PRIOR PARTIAL ONLY', cls: 'coverage-partial', text: 'Current Terms review holds further vendor-specific work absent applicable written authorization. The existing user-input model is prior partial work, not vendor parity or rights clearance; proprietary intraday products remain outside scope.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/spotgamma/GEX-LAB-IMPLEMENTATION.md', linkText: 'Open existing GEX lab notes ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/spotgamma/TEARDOWN.md', secondaryLinkText: 'Open rights and evidence review ↗', route: 'staticgex' },
  { name: 'Option strategy · independent pricing models', status: 'PARTIAL GENERIC METHOD', cls: 'coverage-partial', text: 'Calculates manual expiration payoff plus a user-input European Black–Scholes or American CRR binomial scenario, position Greeks, and a deterministic sensitivity grid. No option feed, vendor code/data, or pricing-parity claim is included.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/optionstrat/OPTIONSTRAT-LAB-IMPLEMENTATION.md', linkText: 'Open option lab method notes ↗', secondaryLink: 'https://bpb-us-w2.wpmucdn.com/u.osu.edu/dist/7/36891/files/2017/07/CRR79-1yy8av8.pdf', secondaryLinkText: 'Open CRR paper ↗', route: 'optionlab' },
  { name: 'Bullflow · Options Activity Profile', status: 'PARTIAL PUBLIC-METHOD CANDIDATE', cls: 'coverage-partial', text: 'Computes the published 20-session profile from user-supplied ticker activity, not the complete market tape. Tracks session availability separately from user-declared export completeness; complete-input ratios require 20 complete baseline exports, the selected export, and cancellation status. Duplicate source IDs are rejected, side-label provenance is reported, and unknown side labels suppress side-derived output. SigScore, algo alerts, and predictive edge remain unimplemented or unvalidated.', details: ['Baseline: prior 20 available ticker dates, excluding the selected session; intraday comparison uses the same Eastern time. Unavailable dates are not treated as zero, and insufficient history/denominators stay null. Published flags: call/put spike ≥2×; call-buying surge also requires ≥70% ask/above-ask share; unusual weekly activity requires 0–7 calendar DTE and volume/OI ≥2×.', 'Directional premium follows the published call-ask − call-bid − put-ask + put-bid formula. Multi-leg side totals are excluded; mid/unknown sides contribute zero. Execution side does not reveal whether a position opened or the trader’s intent.', 'The local CSV candidate is built from published profile documentation and user-supplied rows. It does not call Bullflow or use vendor code/data. Availability, export completeness, raw event timestamps, source IDs, cancellation, and side-label provenance are separate; timestamp-to-ET consistency is checked, partial or unknown exports suppress ratios, duplicate source IDs are rejected, and canceled rows are excluded.', 'The vendor describes SigScore as proprietary. Its API terms limit ordinary data use to personal use unless broader rights are granted in writing, and prohibit site scraping outside documented API access. No paid API, stream, site extraction, account, or private surface was used.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/bullflow/ACTIVITY-PROFILE-LAB-IMPLEMENTATION.md', linkText: 'Open clean-room profile notes ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/bullflow.md#methodology-disclosures', secondaryLinkText: 'Open source methodology and limits ↗', route: 'bullflow' },
  { name: 'Finviz · filter contract', status: 'PARTIAL CONTRACT CANDIDATE', cls: 'coverage-partial', text: 'Applies documented multi-filter AND, last-value-per-filter override, ticker-list ordering, and column sorting to a local CSV subset. No Finviz feed or proprietary pattern detector is reproduced.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/finviz-screener/FINVIZ-LAB-IMPLEMENTATION.md', linkText: 'Open contract build notes ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/finviz-screener/TEARDOWN.md', secondaryLinkText: 'Open teardown evidence ↗', route: 'finviz' },
  { name: 'Stock Rover · factor profile', status: 'PARTIAL PUBLIC-METHOD CANDIDATE', cls: 'coverage-partial', text: 'Ranks the published 22 factor inputs from a user-supplied cross-section with transparent equal-weight construction and explicit R1–R4 choices. Vendor weights, safety overlays, DCF, and forward edge are not reproduced or validated.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/stockrover/STOCKROVER-FACTOR-LAB-IMPLEMENTATION.md', linkText: 'Open factor lab build notes ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/stockrover/TEARDOWN.md', secondaryLinkText: 'Open teardown evidence ↗', route: 'stockrover' },
  { name: 'ChartsLector · formula port', status: 'RESEARCH ONLY', cls: 'coverage-partial', text: 'Date alignment, as-of filtering, and split-adjustment defects were corrected and rechecked. The ~0.736 Spearman is a fitted match to one vendor snapshot, not forward predictive evidence.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/lector-systems/AUDIT_V2.md', linkText: 'Open formula audit ↗' },
  { name: 'Femto Lean · Midna / Claude', status: 'CLAUDE-LINKED COMMIT', cls: 'coverage-partial', text: 'Full history found commit a67e481 by Midna <midna@claude.local>: fail-closed gates, T+15 persistence, scheduler census, Donchian level parity, and stop refusal. Probes still expose non-finite input gaps.', link: 'https://github.com/dwj9ddyvf6-hub/femto-lean/commit/a67e481732245385e0060720ca10c7757c2ad2c4', linkText: 'Open audited commit ↗' },
];

function renderEvidenceGraph() {
  const dependencyCards = evidenceDependencies.map(item => `<article class="coverage-lane evidence-lane"><div><span>${esc(item.name)}</span></div><small>${esc(item.sources)}</small><p><b>Products:</b> ${esc(item.examples)}</p><p class="evidence-rule">${esc(item.rule)}</p><span class="coverage-state coverage-partial">DEPENDENCY FAMILY</span></article>`).join('');
  const buildCards = auditedBuilds.map(item => {
    const details = item.details?.length ? `<details class="evidence-detail"><summary>Source claims, caveats, and access boundary</summary><ul>${item.details.map(detail => `<li>${esc(detail)}</li>`).join('')}</ul></details>` : '';
    return `<article class="coverage-vendor evidence-build"><div class="coverage-vendor-top"><span class="coverage-state ${item.cls}">${esc(item.status)}</span></div><h3>${esc(item.name)}</h3><p>${esc(item.text)}</p>${details}<a href="${item.link}" target="_blank" rel="noreferrer">${esc(item.linkText)}</a>${item.secondaryLink ? `<a href="${item.secondaryLink}" target="_blank" rel="noreferrer">${esc(item.secondaryLinkText)}</a>` : ''}${item.route ? `<button class="text-button" data-view="${esc(item.route)}">Open in suite →</button>` : ''}</article>`;
  }).join('');
  const clocks = [
    ['EVENT TIME', 'When the market event or action happened.'],
    ['PUBLIC TIME', 'When the source made the fact available.'],
    ['INGESTION TIME', 'When this system first recorded it.'],
    ['DECISION TIME', 'When the feature or paper decision was made.'],
  ].map(([label, detail]) => `<div><b>${label}</b><span>${detail}</span></div>`).join('');
  return `${pageHeading('RESEARCH GOVERNANCE', 'Evidence graph', 'Combine observations by source lineage, not by the number of vendor labels that repeat them.', '<button class="button primary" data-view="coverage">Open 86-family registry →</button>')}
    <div class="coverage-summary"><div><b>99</b><span>requested REA passes</span></div><div><b>86</b><span>target-family reports</span></div><div><b>0</b><span>full vendor replicas</span></div><div><b>2</b><span>families with no suite surface</span></div></div>
    <div class="evidence-callout"><b>Pass count is not vendor count.</b><span>The current ledger has 99 requested passes across 86 report families; six target-family reports remain in progress. The terminal has shared prototypes, eight partial candidates (Leadr, Danelfin, SpotGamma, OptionStrat, Bullflow, Finviz, Stock Rover, and the public 15.87 Rule map), and no full vendor replicas. Its market screens still use synthetic examples.</span></div>
    <section class="panel evidence-panel"><div class="panel-heading"><div><h2>Six evidence dependency families</h2><p>Several vendor products can be views of the same underlying event or dataset.</p></div></div><div class="coverage-lane-grid evidence-grid">${dependencyCards}</div><div class="coverage-footnote">Do not count correlated price features, duplicate flow prints, or modeled GEX summaries as separate confirmations. Preserve the raw observation and label every derived or inferred field.</div></section>
    <section class="panel evidence-panel"><div class="panel-heading"><div><h2>Four clocks for point-in-time truth</h2><p>Publication delay and ingestion timing can otherwise leak future information into a historical decision.</p></div></div><div class="coverage-summary evidence-clocks">${clocks}</div></section>
    <section class="panel evidence-panel"><div class="panel-heading"><div><h2>Semantic audit highlights</h2><p>Formula fidelity, runtime behavior, attribution, and trading evidence are different claims.</p></div></div><div class="coverage-grid evidence-build-grid">${buildCards}</div><div class="coverage-footnote"><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/synthesis/CONTRIBUTOR-SEMANTIC-AUDIT-2026-10-27.md" target="_blank" rel="noreferrer">Open the full semantic audit ↗</a> · The report also records the limited checkout and artifact gaps.</div></section>
    <div class="evidence-workflow"><span>OBSERVATION</span><i>→</i><span>NORMALIZED FACT</span><i>→</i><span>VERSIONED FEATURE</span><i>→</i><span>INTERPRETATION</span><i>→</i><span>PAPER DECISION</span><i>→</i><span>FIXED-HORIZON OUTCOME</span></div>`;
}

function renderOverview() {
  const charts = lineChart([
    { values: [31, 35, 33, 41, 44, 39, 48, 50, 47, 55, 58, 56, 62, 66, 62, 69, 72, 70, 76, 73, 80, 82, 79, 85], color: '#42d6ab', fill: true },
    { values: [54, 53, 50, 52, 48, 49, 47, 44, 47, 43, 42, 40, 44, 41, 39, 43, 38, 40, 37, 36, 39, 34, 36, 32], color: '#f16e7a' },
  ], { width: 840, height: 250, axis: '$' });
  const indexMarkup = indexes.map((item, i) => `<div class="index-card"><div class="index-top"><span>${item.label}</span><span class="index-symbol">${item.ticker}</span></div><b>${item.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</b><div>${changeText(item.change)} <span class="muted">· synthetic</span></div><div class="sparkline">${lineChart([{ values: Array.from({ length: 10 }, (_, n) => 30 + n * (item.change >= 0 ? 1.8 : -1.1) + Math.sin(n * 2 + i) * 4), color: item.change >= 0 ? '#42d6ab' : '#f16e7a' }], { width: 180, height: 48 }).replace(/<text[^>]*>[\s\S]*?<\/text>/g, '').replace(/<line[^>]*>/g, '')}</div></div>`).join('');
  const sectorRows = sectors.map(([name, ticker, change]) => `<div class="sector-row"><span class="sector-name">${name}</span><span class="sector-symbol">${ticker}</span><span class="sector-bar"><i style="width:${Math.min(100, Math.abs(change) * 34 + 12)}%;background:${change >= 0 ? 'var(--green)' : 'var(--red)'}"></i></span>${changeText(change)}</div>`).join('');
  const leaders = movers.slice(0, 5).map(m => `<tr><td>${tickerLink(m.ticker)}</td><td>${money(m.price)}</td><td>${changeText(m.change)}</td><td class="${m.net >= 0 ? 'positive' : 'negative'}">${m.net >= 0 ? '+' : '−'}${money(Math.abs(m.net) * 1e6, true)}</td><td><button class="tiny-action" data-action="watch-toggle" data-ticker="${m.ticker}" title="Toggle watchlist">${state.watchlist.includes(m.ticker) ? '★' : '☆'}</button></td></tr>`).join('');
  const latestFlow = flowTrades.slice(0, 5).map(flowRowMini).join('');
  return `${pageHeading('MONDAY, OCTOBER 26, 2026', 'Market overview', 'A bird’s-eye view of broad market positioning and activity.', '<button class="button secondary" data-view="calendar">⌑ Economic calendar</button><button class="button primary" data-view="flow">Open flow feed <span>→</span></button>')}
    <div class="index-grid">${indexMarkup}</div>
    <div class="overview-grid">
      <div class="overview-main">
        ${panel('Market tide <span class="info-dot" title="Illustrative call and put premium series, not the proprietary vendor calculation.">i</span>', 'Synthetic intraday call vs put premium · $M', `${chartLegend([{ label: 'Call premium', color: '#42d6ab' }, { label: 'Put premium', color: '#f16e7a' }])}${charts}<div class="chart-footnote"><span class="status-dot demo"></span>Illustrative activity series <span class="muted">· midpoint prints excluded from net-flow convention</span></div>`, '<button class="text-button" data-view="flow">View flow →</button>')}
        ${panel('Notable options flow', 'Large synthetic sample prints · sorted by time', `<div class="table-wrap"><table class="compact-table"><thead><tr><th>TIME</th><th>TICKER</th><th>CONTRACT</th><th>SIDE EST.</th><th>SIZE</th><th>PREMIUM</th><th></th></tr></thead><tbody>${latestFlow}</tbody></table></div>`, '<button class="text-button" data-view="flow">All flow →</button>')}
      </div>
      <div class="overview-side">
        ${panel('Sector pulse', 'Synthetic day move', `<div class="sector-list">${sectorRows}</div>`, '<button class="text-button" data-view="screener">Explore →</button>')}
        ${panel('Top net impact', 'Demo flow aggregation · $M', `<div class="leader-table"><table><thead><tr><th>TICKER</th><th>PRICE</th><th>DAY</th><th>NET</th><th></th></tr></thead><tbody>${leaders}</tbody></table></div>`, '<button class="text-button" data-view="screener">Open screener →</button>')}
        ${panel('Market headlines', 'Sample desk headlines', `<div class="headline-list">${newsItems.slice(0, 3).map(newsCard).join('')}</div>`, '<button class="text-button" data-view="news">News flow →</button>')}
      </div>
    </div>
    <div class="overview-bottom">${panel('This week', 'Upcoming sample events', `<div class="event-strip">${calendarItems.slice(0, 4).map(eventCard).join('')}</div>`, '<button class="text-button" data-view="calendar">Full calendar →</button>')}${panel('Your watchlist', `${state.watchlist.length} symbols · stored locally`, `<div class="watch-chip-list">${state.watchlist.slice(0, 6).map(t => `<button class="watch-chip" data-symbol="${t}">${t}<span>↗</span></button>`).join('') || '<span class="muted">Add a ticker from Watchlists</span>'}</div>`, '<button class="text-button" data-view="watchlists">Manage →</button>')}</div>`;
}

function flowRows() {
  let rows = [...flowTrades];
  if (state.flowSearch) rows = rows.filter(r => `${r.ticker} ${r.type} ${r.expiry}`.toLowerCase().includes(state.flowSearch.toLowerCase()));
  if (state.flowType !== 'all') rows = rows.filter(r => r.type.toLowerCase() === state.flowType);
  if (state.flowSide !== 'all') rows = rows.filter(r => r.side.toLowerCase() === state.flowSide);
  rows = rows.filter(r => r.premium >= Number(state.minPremium || 0));
  if (state.flowSort === 'premium') rows.sort((a, b) => b.premium - a.premium);
  if (state.flowSort === 'size') rows.sort((a, b) => b.size - a.size);
  return rows;
}
function flowRow(row) {
  const isSaved = state.savedTrades.includes(row.id);
  const sideClass = row.side === 'ASK' ? 'positive' : row.side === 'BID' ? 'negative' : 'neutral';
  return `<tr><td class="mono muted">${row.time}<small> ET</small></td><td>${tickerLink(row.ticker)}</td><td><span class="option-type ${row.type === 'CALL' ? 'call' : 'put'}">${row.type}</span></td><td><b>${row.expiry}</b> <span class="muted">${row.strike}</span></td><td><span class="side-pill ${sideClass}">${row.side === 'ASK' ? '↑' : row.side === 'BID' ? '↓' : '·'} ${row.side}</span><small class="micro-note">quote-relative estimate</small></td><td>${money(row.price, false)}</td><td>${integer(row.size)}</td><td><b>${money(row.premium, true)}</b></td><td>${money(row.spot)}</td><td>${row.iv.toFixed(1)}%</td><td><span class="code-pill">${row.code}</span></td><td><button class="tiny-action ${isSaved ? 'saved' : ''}" data-action="save-trade" data-id="${row.id}" aria-label="${isSaved ? 'Unsave' : 'Save'} trade">${isSaved ? '★' : '☆'}</button></td></tr>`;
}
function flowRowMini(row) {
  return `<tr><td class="mono muted">${row.time}</td><td>${tickerLink(row.ticker)}</td><td><span class="option-type ${row.type === 'CALL' ? 'call' : 'put'}">${row.type}</span> <span class="muted">${row.strike} · ${row.expiry}</span></td><td><span class="side-pill ${row.side === 'ASK' ? 'positive' : row.side === 'BID' ? 'negative' : 'neutral'}">${row.side}</span></td><td>${integer(row.size)}</td><td><b>${money(row.premium, true)}</b></td><td><button class="tiny-action ${state.savedTrades.includes(row.id) ? 'saved' : ''}" data-action="save-trade" data-id="${row.id}">${state.savedTrades.includes(row.id) ? '★' : '☆'}</button></td></tr>`;
}
function renderFlow() {
  const rows = flowRows();
  const callTotal = flowTrades.filter(r => r.type === 'CALL').reduce((a, r) => a + r.premium, 0);
  const putTotal = flowTrades.filter(r => r.type === 'PUT').reduce((a, r) => a + r.premium, 0);
  const content = rows.length ? rows.map(flowRow).join('') : `<tr><td colspan="12">${tableEmpty('Try clearing one or more filters.')}</td></tr>`;
  return `${pageHeading('OPTIONS · TAPE', 'Options flow', 'Filter transaction-shaped sample data. Side labels are quote-relative estimates, not opening/closing position labels.', '<button class="button secondary" data-action="clear-flow">Reset filters</button><button class="button primary" data-view="alerts">＋ Create alert</button>')}
    <div class="flow-summary-grid">${statCard('CALL PREMIUM', money(callTotal, true), 'sample sum', 1.28, '↗')}${statCard('PUT PREMIUM', money(putTotal, true), 'sample sum', -0.42, '↘')}${statCard('PRINTS SHOWN', `${rows.length} <small>/ ${flowTrades.length}</small>`, 'after local filters', 0.64, '≋')}${statCard('FEED STATUS', 'DEMO', 'no live stream', 0, '◉')}</div>
    ${panel('Flow feed', 'Local synthetic records · simulated complete sample · no live updates', `<div class="filter-toolbar">
      <label class="filter-input"><span>⌕</span><input name="flowSearch" data-filter="flowSearch" value="${esc(state.flowSearch)}" placeholder="Ticker, expiry, contract" /></label>
      <label class="select-filter"><span>TYPE</span><select data-filter="flowType"><option value="all" ${state.flowType === 'all' ? 'selected' : ''}>Calls + puts</option><option value="call" ${state.flowType === 'call' ? 'selected' : ''}>Calls</option><option value="put" ${state.flowType === 'put' ? 'selected' : ''}>Puts</option></select></label>
      <label class="select-filter"><span>SIDE</span><select data-filter="flowSide"><option value="all" ${state.flowSide === 'all' ? 'selected' : ''}>Any side</option><option value="ask" ${state.flowSide === 'ask' ? 'selected' : ''}>Near ask</option><option value="bid" ${state.flowSide === 'bid' ? 'selected' : ''}>Near bid</option><option value="mid" ${state.flowSide === 'mid' ? 'selected' : ''}>Midpoint</option></select></label>
      <label class="select-filter"><span>MIN PREMIUM</span><select data-filter="minPremium"><option value="0" ${state.minPremium == 0 ? 'selected' : ''}>Any size</option><option value="25000" ${state.minPremium == 25000 ? 'selected' : ''}>$25K+</option><option value="50000" ${state.minPremium == 50000 ? 'selected' : ''}>$50K+</option><option value="100000" ${state.minPremium == 100000 ? 'selected' : ''}>$100K+</option></select></label>
      <label class="select-filter"><span>SORT BY</span><select data-filter="flowSort"><option value="time" ${state.flowSort === 'time' ? 'selected' : ''}>Latest</option><option value="premium" ${state.flowSort === 'premium' ? 'selected' : ''}>Premium</option><option value="size" ${state.flowSort === 'size' ? 'selected' : ''}>Size</option></select></label>
      <button class="button small secondary" data-action="clear-flow">Clear</button></div>
      <div class="flow-notice"><span class="notice-dot"></span><span><b>Interpretation note</b> — ask/bid proximity estimates which side initiated a print. It cannot tell whether a trade opened or closed a position; midpoint and multi-leg prints need extra caution.</span><button title="Read source notes" data-view="api">ⓘ</button></div>
      <div class="table-wrap"><table class="data-table flow-table"><thead><tr><th>TIME</th><th>TICKER</th><th>TYPE</th><th>CONTRACT</th><th>SIDE EST.</th><th>FILL</th><th>SIZE</th><th>PREMIUM</th><th>SPOT</th><th>IV</th><th>CODE</th><th></th></tr></thead><tbody>${content}</tbody></table></div>
      <div class="table-bottom"><span>Showing <b>${rows.length}</b> of ${flowTrades.length} synthetic records</span><span>Local fixture set <span class="dot-sep">·</span> No completeness claim</span><span class="muted">Static fixture set · No live refresh</span></div>`)}`;
}

function underlying(ticker = state.ticker) {
  return ({ SPY: 681.44, QQQ: 612.18, NVDA: 184.26, TSLA: 412.85, AMD: 188.43, AAPL: 276.18, META: 724.1, PLTR: 169.34, MSFT: 504.42 })[ticker] || 152.8;
}
function makeGexRows(ticker = state.ticker) {
  const spot = underlying(ticker), step = spot > 500 ? 10 : 5;
  return Array.from({ length: 13 }, (_, i) => {
    const strike = Math.round((spot + (i - 6) * step) * 100) / 100;
    const distance = i - 6;
    const oiScale = state.gexBasis === 'oi' ? 0.7 + Math.abs(distance) * 0.055 : 1;
    const call = Math.round((Math.max(1, 15 - Math.abs(distance - 2) * 2.2) * (distance >= -1 ? 1 : 0.62) * oiScale + (distance === -2 ? 13 : 0)) * 10) / 10;
    const put = Math.round((Math.max(1, 13 - Math.abs(distance + 2) * 2.1) * (distance <= 2 ? -1 : -0.52) * (state.gexBasis === 'oi' ? 1.22 : 1)) * 10) / 10;
    return { strike, call, put, net: call + put, exp: i % 3 === 0 ? '11/07' : i % 3 === 1 ? '11/14' : '12/19' };
  });
}
function gexBars(rows) {
  const max = Math.max(...rows.map(r => Math.max(Math.abs(r.call), Math.abs(r.put))));
  return `<div class="gex-bars">${rows.map(r => `<div class="gex-bar-row"><span class="gex-strike">${r.strike.toFixed(0)}</span><div class="gex-bar-side left"><i style="width:${Math.abs(r.put) / max * 92}%;background:var(--red)"></i></div><div class="gex-mid"></div><div class="gex-bar-side right"><i style="width:${Math.abs(r.call) / max * 92}%;background:var(--green)"></i></div><span class="gex-net ${signedClass(r.net)}">${r.net > 0 ? '+' : ''}${r.net.toFixed(1)}</span></div>`).join('')}</div>`;
}
function renderGex() {
  const rows = makeGexRows();
  const net = rows.reduce((sum, r) => sum + r.net, 0);
  const spot = underlying();
  const callWall = rows.filter(r => r.strike > spot && r.net > 0).sort((a, b) => b.net - a.net)[0]?.strike || spot + 15;
  const putWall = rows.filter(r => r.strike < spot && r.net > 0).sort((a, b) => b.net - a.net)[0]?.strike || spot - 15;
  const crossings = rows.slice(1).flatMap((row, i) => {
    const prior = rows[i];
    if (prior.net === 0) return [prior.strike];
    if (row.net === 0) return [row.strike];
    if (Math.sign(prior.net) === Math.sign(row.net)) return [];
    const fraction = Math.abs(prior.net) / (Math.abs(prior.net) + Math.abs(row.net));
    return [prior.strike + fraction * (row.strike - prior.strike)];
  });
  const gammaFlip = crossings.sort((a, b) => Math.abs(a - spot) - Math.abs(b - spot))[0];
  return `${pageHeading('POSITIONING · GREEKS', 'GEX & Greeks', 'Explore strike-level synthetic exposure. Every surface shows its calculation basis and sample status.', `<label class="ticker-picker"><span>TICKER</span><input data-state="ticker" value="${esc(state.ticker)}" maxlength="10" /></label><button class="button secondary" data-view="ticker">Ticker detail →</button><button class="button primary" data-view="staticgex">Static GEX Lab →</button>`)}
    <div class="segmented-control"><button class="${state.gexBasis === 'vol' ? 'selected' : ''}" data-action="gex-basis" data-value="vol">Directionalized volume</button><button class="${state.gexBasis === 'oi' ? 'selected' : ''}" data-action="gex-basis" data-value="oi">Open interest</button><span class="segmented-note">Basis: ${state.gexBasis === 'vol' ? 'sample volume-side proxy' : 'sample open-interest proxy'}</span></div>
    <div class="flow-summary-grid gex-stats">${statCard('SYNTHETIC SPOT', money(spot), 'sample underlier', 0.42, '⌖')}${statCard('NET GAMMA', `${net >= 0 ? '+' : ''}${net.toFixed(1)}B`, 'sample model units', net >= 0 ? 0.58 : -0.58, '◈')}${statCard('CALL WALL', money(callWall), 'highest positive level above spot', 0.24, '↑')}${statCard('PUT WALL', money(putWall), 'highest positive level below spot', -0.21, '↓')}</div>
    <div class="two-column-layout">
      ${panel(`${state.ticker} · strike exposure`, 'Calls extend right · puts extend left · synthetic scale in $B', `<div class="gex-legend"><span><i class="green-square"></i>Call GEX</span><span><i class="red-square"></i>Put GEX</span><span><i class="spot-line"></i>Spot reference ${money(spot)}</span></div><div class="gex-axis"><span>PUT EXPOSURE</span><span>STRIKE</span><span>CALL EXPOSURE</span></div>${gexBars(rows)}<div class="chart-footnote"><span class="status-dot demo"></span>Demo model only. A displayed wall or flip is not a price forecast.</div>`, `<button class="text-button" data-action="gex-basis" data-value="${state.gexBasis === 'vol' ? 'oi' : 'vol'}">Change basis →</button>`)}
      <div class="stacked-panels">${panel('Key levels', 'Illustrative strike-derived references', `<div class="level-list"><div><span>Call wall</span><b class="positive">${money(callWall)}</b><small>Largest positive net gamma above spot</small></div><div><span>Put wall</span><b class="negative">${money(putWall)}</b><small>Largest positive net gamma below spot</small></div><div><span>Gamma magnet</span><b>${money(rows.slice().sort((a, b) => Math.abs(b.net) - Math.abs(a.net))[0].strike)}</b><small>Largest absolute sample strike exposure</small></div><div><span>Gamma flip</span><b>${Number.isFinite(gammaFlip) ? money(gammaFlip) : '—'}</b><small>${Number.isFinite(gammaFlip) ? 'Interpolated local zero-crossing candidate' : 'No sign change in this sample range'}</small></div></div>`, '')}${panel('Reading exposure', 'The documented API separates inputs and outputs', `<ul class="insight-list"><li>Directionalized volume and open interest are different exposure bases.</li><li>The sign of aggregate net gamma is a regime cue; a cumulative flip may be null or far from spot.</li><li>Dealer positions and hedging are modeled, not directly observed here.</li></ul><a class="inline-link" href="https://api.unusualwhales.com/docs/operations/PublicApi.GexController.gex_levels" target="_blank" rel="noreferrer">Read official GEX contract ↗</a>`, '')}</div>
    </div>
    ${panel('Exposure by strike', 'Synthetic call and put values · switch the basis above', `<div class="table-wrap"><table class="data-table"><thead><tr><th>EXPIRY</th><th>STRIKE</th><th>CALL GEX</th><th>PUT GEX</th><th>NET GEX</th><th>SPOT DIST.</th></tr></thead><tbody>${rows.map(r => `<tr><td>${r.exp}</td><td>${money(r.strike)}</td><td class="positive">+${r.call.toFixed(1)}B</td><td class="negative">${r.put.toFixed(1)}B</td><td class="${signedClass(r.net)}">${r.net > 0 ? '+' : ''}${r.net.toFixed(1)}B</td><td>${pct((r.strike / spot - 1) * 100)}</td></tr>`).join('')}</tbody></table></div>`)}`;
}

function createStaticGexDemoRows() {
  const ticker = 'SPY', spot = 681.44, strikes = [650, 660, 670, 680, 690, 700, 710];
  const expiries = [2, 9, 30];
  return expiries.flatMap((dte, expiryIndex) => strikes.flatMap(strike => {
    const distance = (strike - spot) / 10;
    const ivPct = 23 + Math.abs(distance) * 0.75 + (expiryIndex === 0 ? 4 : 0);
    const callOi = Math.round(12000 * Math.exp(-Math.abs(distance - 1.1) / 2.3) * (1 + expiryIndex * 0.15)) + 500;
    const putOi = Math.round(10000 * Math.exp(-Math.abs(distance + 1.2) / 2.5) * (1 + expiryIndex * 0.13)) + 450;
    return [
      { ticker, asOf: 'Synthetic sample', spot, strike, type: 'CALL', openInterest: callOi, ivPct, dte },
      { ticker, asOf: 'Synthetic sample', spot, strike, type: 'PUT', openInterest: putOi, ivPct: ivPct + 0.4, dte },
    ];
  }));
}

function parseStaticGexCsv(source) {
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

function blackScholesGamma(spot, strike, dte, ivPct, rate, dividendYield) {
  const years = dte / 365;
  const sigma = ivPct / 100;
  const denominator = spot * sigma * Math.sqrt(years);
  if (!(denominator > 0)) return 0;
  const d1 = (Math.log(spot / strike) + (rate - dividendYield + 0.5 * sigma * sigma) * years) / denominator;
  return Math.exp(-dividendYield * years) * Math.exp(-0.5 * d1 * d1) / (Math.sqrt(2 * Math.PI) * denominator);
}

function buildStaticGexSnapshot(rows, settings) {
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
    if (before.net === 0) crossings.push(before.spot);
    if (before.net * after.net < 0) {
      const fraction = Math.abs(before.net) / (Math.abs(before.net) + Math.abs(after.net));
      crossings.push(before.spot + fraction * (after.spot - before.spot));
    }
  }
  if (profile.at(-1)?.net === 0) crossings.push(profile.at(-1).spot);
  const zeroGamma = crossings.sort((a, b) => Math.abs(a - settings.spot) - Math.abs(b - settings.spot))[0] ?? null;
  return { optionRows, strikes, netGex, callWall, putWall, zeroGamma, crossingCount: crossings.length };
}

function formatGex(value) {
  if (!Number.isFinite(value)) return '—';
  const sign = value < 0 ? '−' : value > 0 ? '+' : '';
  const amount = Math.abs(value);
  if (amount >= 1e9) return `${sign}$${(amount / 1e9).toFixed(2)}B`;
  if (amount >= 1e6) return `${sign}$${(amount / 1e6).toFixed(2)}M`;
  if (amount >= 1e3) return `${sign}$${(amount / 1e3).toFixed(1)}K`;
  return `${sign}$${amount.toFixed(0)}`;
}

function buildAzraelMap(input) {
  const anchorClose = Number(input.anchorClose);
  const vixClose = Number(input.vixClose);
  const elapsedMinutes = Number(input.elapsedMinutes);
  const sessionMinutes = Number(input.sessionMinutes);
  const candidateText = String(input.candidateTarget ?? '').trim();
  const candidateTarget = candidateText === '' ? null : Number(candidateText);
  if (!Number.isFinite(anchorClose) || anchorClose <= 0 || anchorClose > 1e7) return { error: 'Prior close must be greater than zero and no more than 10,000,000.' };
  if (!Number.isFinite(vixClose) || vixClose <= 0 || vixClose > 300) return { error: 'Prior VIX close must be greater than zero and no more than 300.' };
  if (!Number.isInteger(sessionMinutes) || sessionMinutes < 1 || sessionMinutes > 600) return { error: 'Session length must be a whole number from 1 to 600 minutes.' };
  if (!Number.isInteger(elapsedMinutes) || elapsedMinutes < 0 || elapsedMinutes > sessionMinutes) return { error: 'Elapsed minutes must be a whole number within the session length.' };
  if (candidateTarget !== null && (!Number.isFinite(candidateTarget) || candidateTarget <= 0 || candidateTarget > 1e7)) return { error: 'Candidate target must be blank or a price greater than zero and no more than 10,000,000.' };

  const pct = vixClose / 15.87;
  const expectedMove = Math.round((anchorClose * pct / 100) * 10) / 10;
  const half = expectedMove / 2;
  const fundedMove = elapsedMinutes === 0 ? 0 : expectedMove * Math.sqrt(elapsedMinutes / sessionMinutes);
  const regime = vixClose < 15 ? 'CALM' : vixClose > 18.5 ? 'FAST' : 'MIXED';
  let targetRead = null;
  if (candidateTarget !== null) {
    if (candidateTarget > anchorClose + expectedMove) targetRead = { label: 'Beyond the upper ±1.0 wall', detail: `${formatAzraelPrice(candidateTarget - (anchorClose + expectedMove))} above the expected-move band.` };
    else if (candidateTarget < anchorClose - expectedMove) targetRead = { label: 'Beyond the lower ±1.0 wall', detail: `${formatAzraelPrice((anchorClose - expectedMove) - candidateTarget)} below the expected-move band.` };
    else if (candidateTarget >= anchorClose - half && candidateTarget <= anchorClose + half) targetRead = { label: 'Inside the central half-move', detail: 'The published brief describes targets between the half-move lines as fitting a normal day.' };
    else targetRead = { label: 'Inside the outer half of the expected band', detail: 'Within the ±1.0 walls, but outside the central half-move.' };
  }
  return {
    anchorClose, vixClose, pct, expectedMove, half, fundedMove, weeklyMove: expectedMove * Math.sqrt(5), regime, targetRead,
    lines: [
      { name: '+1.0 wall', level: anchorClose + expectedMove, note: 'Upper expected-move boundary' },
      { name: '+0.5 shelf', level: anchorClose + half, note: 'Upper half-move line' },
      { name: '0.00 magnet', level: anchorClose, note: 'Prior close anchor' },
      { name: '−0.5 shelf', level: anchorClose - half, note: 'Lower half-move line' },
      { name: '−1.0 wall', level: anchorClose - expectedMove, note: 'Lower expected-move boundary' },
    ],
  };
}

function formatAzraelPrice(value) {
  return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
}

function renderAzraelMapLab() {
  const p = state.azraelMap;
  const result = buildAzraelMap(p);
  const elapsedLabel = `${p.elapsedMinutes} / ${p.sessionMinutes} min`;
  const lineRows = result.error ? '' : result.lines.map(row => `<tr><td><b>${row.name}</b></td><td class="mono">${formatAzraelPrice(row.level)}</td><td class="muted">${row.note}</td></tr>`).join('');
  return `${pageHeading('PUBLIC RULE · CLEAN-ROOM MAP CALCULATOR', 'The 15.87 Rule map', 'Build the prior-close expected-move map and compare a candidate price with its published bands. All inputs are manual; no trading signal or live feed is implied.', '<button class="button secondary" data-action="azrael-example">Load published example</button>')}
    <div class="evidence-callout portfolio-callout"><b>Method boundary</b><span>Daily move = prior anchor close × (VIX ÷ 15.87) ÷ 100, rounded to 0.1 price units. The 15.87 divisor is this map’s trading-session convention (approximately √252). Cboe describes VIX around a constant 30-day horizon and publishes a calendar-day daily reference using VIX ÷ √365; the two conventions produce different widths. This map keeps its published divisor. Funded range uses the session clock and square-root-of-time scaling; weekly context multiplies the rounded daily move by √5. These are scaling conventions, not calibrated intraday probabilities or guarantees. <a href="https://www.cboe.com/insights/posts/inside-volatility-trading-breaking-down-the-vix-index-and-its-correlation-to-the-s-p-500-index/" target="_blank" rel="noopener noreferrer">Cboe calendar-day reference →</a> <a href="https://cdn.cboe.com/resources/vix/VIX_Methodology.pdf" target="_blank" rel="noopener noreferrer">VIX methodology →</a></span><a href="../../research/rea-teardowns/azrael-1587/SPEC.md">Review extracted method →</a></div>
    <section class="panel azrael-map-input"><div class="panel-heading"><div><h2>Prior-close inputs</h2><p>Use matching units for the anchor and candidate target. Set session length to the actual session, including early closes.</p></div></div><form id="azrael-map-form" class="strategy-form"><label class="field-label">PRIOR ANCHOR CLOSE<input name="anchorClose" type="number" min="0.000001" max="10000000" step="any" value="${esc(p.anchorClose)}" required /></label><label class="field-label">PRIOR VIX CLOSE<input name="vixClose" type="number" min="0.000001" max="300" step="any" value="${esc(p.vixClose)}" required /></label><label class="field-label">MINUTES SINCE 09:30<input name="elapsedMinutes" type="number" min="0" max="600" step="1" value="${esc(p.elapsedMinutes)}" required /></label><label class="field-label">SESSION LENGTH · MINUTES<input name="sessionMinutes" type="number" min="1" max="600" step="1" value="${esc(p.sessionMinutes)}" required /></label><label class="field-label">CANDIDATE TARGET · OPTIONAL<input name="candidateTarget" type="number" min="0.000001" max="10000000" step="any" value="${p.candidateTarget === '' ? '' : esc(p.candidateTarget)}" placeholder="e.g. 7800" /></label><button class="button primary strategy-run-button">Recalculate map</button></form></section>
    ${p.error || result.error ? `<div class="strategy-error">${esc(p.error || result.error)}</div>` : ''}
    ${result.error ? '' : `<div class="coverage-summary azrael-map-summary"><div><b>${result.expectedMove.toFixed(1)}</b><span>daily expected move · ${result.pct.toFixed(2)}%</span></div><div><b>${result.regime}</b><span>prior-VIX regime band</span></div><div><b>±${result.fundedMove.toFixed(1)}</b><span>funded range · ${elapsedLabel}</span></div><div><b>±${result.weeklyMove.toFixed(1)}</b><span>weekly move context</span></div></div>
    ${panel('Frozen session map', 'All levels use the prior close and the rounded expected move', `<div class="table-wrap"><table class="data-table"><thead><tr><th>LINE</th><th>LEVEL</th><th>INTERPRETATION</th></tr></thead><tbody>${lineRows}</tbody></table></div><div class="portfolio-table-note">Expected-move amount is rounded to one decimal before deriving the half-move and wall levels.</div>`)}
    ${result.targetRead ? panel('Candidate target read', `${formatAzraelPrice(p.candidateTarget)} · descriptive band check`, `<div class="azrael-target-read"><b>${result.targetRead.label}</b><span>${result.targetRead.detail}</span></div>`) : ''}`}
    <div class="strategy-disclaimer portfolio-disclaimer">This implements only the pre-open map and descriptive target bands. It does not implement the three-ticker breakout, fades, OI shortlist, touch accounting, options-flow check, contract sizing, or any live feed. The source’s own worked examples are not evidence of predictive edge; no performance claim or trading instruction is made. See <a href="../../research/rea-teardowns/azrael-1587/WORKED-EXAMPLES.md">worked-example audit →</a>.</div>`;
}

function renderStaticGexLab() {
  const p = state.staticGex;
  if (!p.rows.length) p.rows = createStaticGexDemoRows();
  const result = buildStaticGexSnapshot(p.rows, p);
  const dateCaption = p.source === 'synthetic' ? 'Synthetic sample' : p.asOf || 'Date unavailable';
  const strikeRows = result.strikes.slice(0, 250).map(row => `<tr><td>${money(row.strike)}</td><td class="positive">${formatGex(row.callGex)}</td><td class="negative">${formatGex(row.putGex)}</td><td class="${signedClass(row.netGex)}">${formatGex(row.netGex)}</td><td>${pct((row.strike / p.spot - 1) * 100)}</td></tr>`).join('') || '<tr><td colspan="5" class="muted">No strike aggregates are available.</td></tr>';
  const actions = `<button class="button secondary" data-action="static-gex-demo">Load synthetic sample</button><button class="button secondary" data-action="static-gex-export" ${p.rows.length ? '' : 'disabled'}>Export contract audit</button>`;
  return `${pageHeading('PUBLISHED STATIC FORMULA · CLEAN-ROOM MODEL', 'Static GEX Lab', 'Calculate a convention-signed, open-interest-based GEX snapshot from a local option-chain CSV. This is a static model, not SpotGamma’s proprietary intraday inventory system.', actions)}
    <div class="evidence-callout portfolio-callout"><b>What this calculation means</b><span>The public formula is Γ × modeled position × contract multiplier × spot² × 0.01, summed by strike, for dollar exposure per 1% underlying move. This implementation treats calls as positive and puts as negative, as the published simplifying convention describes. Open interest is a proxy, not observed dealer inventory; GEX does not predict direction. Black–Scholes gamma and constant IV over the zero-gamma spot grid are explicit local assumptions.</span><a href="../../research/rea-teardowns/spotgamma/TEARDOWN.md">Review teardown evidence →</a></div>
    <div class="strategy-data-banner portfolio-data-banner"><div><span class="coverage-state ${p.source === 'csv' ? 'coverage-local' : 'coverage-partial'}">${p.source === 'csv' ? 'LOCAL CSV' : 'SYNTHETIC SAMPLE'}</span><b>${esc(p.filename)}</b><small>${p.rows.length.toLocaleString()} option rows · ${esc(p.ticker)} · ${esc(dateCaption)} · input stays in this tab</small>${p.notice ? `<small class="strategy-notice">${esc(p.notice)}</small>` : ''}</div><label class="button primary file-pick">Choose CSV<input id="static-gex-file" type="file" accept=".csv,text/csv" /></label></div>
    <div class="portfolio-schema-note"><b>Required CSV:</b> <code>Ticker,AsOf,Spot,Strike,Type,OpenInterest,IV,DTE</code> · IV is percent points (e.g. 25), DTE is calendar days, OI is contracts, Type is Call/C or Put/P. One underlying, date, and spot per file.</div>
    ${p.error ? `<div class="strategy-error">${esc(p.error)}</div>` : ''}
    <div class="coverage-summary static-gex-summary"><div><b>${money(p.spot)}</b><span>underlying spot · ${esc(dateCaption)}</span></div><div><b>${formatGex(result.netGex)}</b><span>net GEX per 1% move</span></div><div><b>${result.callWall ? money(result.callWall.strike) : '—'}</b><span>largest call gamma concentration</span></div><div><b>${result.putWall ? money(result.putWall.strike) : '—'}</b><span>largest put gamma concentration</span></div><div><b>${result.zeroGamma !== null ? money(result.zeroGamma) : 'No cross'}</b><span>nearest zero within ±${p.gridRangePct}% spot grid</span></div></div>
    <section class="panel static-gex-settings"><div class="panel-heading"><div><h2>Pricing assumptions</h2><p>These inputs affect theoretical gamma and the zero-gamma repricing grid.</p></div></div><form id="static-gex-config" class="strategy-form"><label class="field-label">RISK-FREE RATE · ANNUAL %<input name="riskFreeRatePct" type="number" min="-10" max="40" step="0.01" value="${p.riskFreeRatePct}" required /></label><label class="field-label">DIVIDEND YIELD %<input name="dividendYieldPct" type="number" min="-10" max="40" step="0.01" value="${p.dividendYieldPct}" required /></label><label class="field-label">CONTRACT MULTIPLIER<input name="multiplier" type="number" min="1" max="10000" step="1" value="${p.multiplier}" required /></label><label class="field-label">ZERO-GAMMA GRID · ± %<input name="gridRangePct" type="number" min="5" max="50" step="1" value="${p.gridRangePct}" required /></label><button class="button primary strategy-run-button">Recalculate GEX</button></form><div class="strategy-assumptions">Gamma is calculated with Black–Scholes using a continuous dividend yield and annualized rate. IV is held constant for each contract as spot moves across a 101-point grid. The zero level is the nearest interpolated net-GEX sign change inside the selected range; no crossing means no value is reported.</div></section>
    <section class="panel static-gex-profile"><div class="panel-heading"><div><h2>GEX by strike</h2><p>Call exposure is positive; put exposure is negative · units are dollars per 1% move.</p></div><span class="small-muted">${result.optionRows.length.toLocaleString()} contracts · prior-night OI convention</span></div><div class="table-wrap"><table><thead><tr><th>STRIKE</th><th>CALL GEX</th><th>PUT GEX</th><th>NET GEX</th><th>SPOT DISTANCE</th></tr></thead><tbody>${strikeRows}</tbody></table></div>${result.strikes.length > 250 ? `<div class="portfolio-table-note">Showing 250 of ${result.strikes.length} strikes. The contract audit export includes all rows.</div>` : ''}</section>
    <div class="strategy-disclaimer portfolio-disclaimer">This does not reproduce SpotGamma’s Options Inventory Model, HIRO trade signing, TRACE, Synthetic OI, Volatility Trigger, or Risk Pivot. Static OI can be stale intraday; dealer sign is assumed rather than observed. No historical validation, forecast, or trading instruction is provided.</div>`;
}

function renderDarkpool() {
  const rows = darkpoolTrades.filter(r => !state.dpTicker || r.ticker.toLowerCase().includes(state.dpTicker.toLowerCase()));
  return `${pageHeading('OFF-EXCHANGE ACTIVITY', 'Dark-pool prints', 'Explore sample off-exchange prints and price levels. A print alone does not reveal the full intent of the participants.', '<button class="button secondary" data-action="clear-dp">Clear filter</button>')}
    <div class="flow-summary-grid">${statCard('SAMPLE PRINTS', rows.length, 'local sample rows', 0.32, '◌')}${statCard('SAMPLE NOTIONAL', money(rows.reduce((s, r) => s + r.value, 0), true), 'sum of displayed rows', 0.51, '$')}${statCard('ABOVE / BELOW', `${rows.filter(r => /above|below/i.test(r.side)).length}`, 'classification examples', 0.18, '↕')}${statCard('SOURCE', 'DEMO', 'not exchange feed', 0, '◉')}</div>
    ${panel('Recent prints', 'Synthetic sample records · exchange and sale-condition details are illustrative', `<div class="filter-toolbar"><label class="filter-input"><span>⌕</span><input data-filter="dpTicker" value="${esc(state.dpTicker)}" placeholder="Filter ticker" /></label><span class="toolbar-spacer"></span><span class="small-muted">Side is based on the fixture label only</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>TIME</th><th>TICKER</th><th>PRICE</th><th>SHARES</th><th>NOTIONAL</th><th>PRICE RELATION</th><th>SESSION</th></tr></thead><tbody>${rows.map(r => `<tr><td class="mono">${r.time} ET</td><td>${tickerLink(r.ticker)}</td><td>${money(r.price)}</td><td>${integer(r.shares)}</td><td><b>${money(r.value, true)}</b></td><td><span class="code-pill">${r.side}</span></td><td class="muted">Demo</td></tr>`).join('') || `<tr><td colspan="7">${tableEmpty('Try a different ticker.')}</td></tr>`}</tbody></table></div><div class="table-bottom"><span>${rows.length} sample prints</span><span>Data generated locally · no live venue data</span></div>`)}`;
}

function renderDisclosures(kind) {
  const congress = kind === 'congress';
  const source = congress ? disclosures : insiders;
  const rows = source.filter(r => !state.disclosureSearch || Object.values(r).join(' ').toLowerCase().includes(state.disclosureSearch.toLowerCase()));
  const body = congress ? rows.map(r => `<tr><td>${r.date}</td><td><b>${esc(r.person)}</b><small class="muted">${r.party === 'D' ? 'Democrat' : 'Republican'} · sample</small></td><td>${tickerLink(r.ticker)}</td><td><span class="${r.action === 'Purchase' ? 'positive' : 'negative'}">${r.action}</span></td><td>${r.size}</td><td>${r.filed}</td><td><span class="code-pill">DISCLOSURE</span></td></tr>`).join('') : rows.map(r => `<tr><td>${r.date}</td><td><b>${esc(r.person)}</b><small class="muted">${r.form} · sample</small></td><td>${tickerLink(r.ticker)}</td><td><span class="${r.action === 'Purchase' ? 'positive' : 'negative'}">${r.action}</span></td><td>${r.shares}</td><td>${r.value}</td><td><span class="code-pill">${r.form}</span></td></tr>`).join('');
  return `${pageHeading(congress ? 'PUBLIC DISCLOSURES' : 'INSIDER FILINGS', congress ? 'Congress trades' : 'Insider activity', 'Disclosure-shaped sample records. Filing ranges and reported transaction dates can differ; verify source filings before analysis.', `<button class="button secondary" data-action="clear-disclosure">Clear search</button><button class="button primary" data-view="ticker">Research a ticker →</button>`)}
    <div class="tab-row"><button class="tab-button ${congress ? 'selected' : ''}" data-view="congress">Congress</button><button class="tab-button ${!congress ? 'selected' : ''}" data-view="insiders">Corporate insiders</button><span class="tab-row-spacer"></span><span class="small-muted">Sample source records only</span></div>
    <div class="flow-summary-grid">${statCard(congress ? 'FILINGS SHOWN' : 'INSIDER FILINGS', rows.length, 'synthetic sample', 0.26, '▤')}${statCard('PURCHASES', source.filter(r => r.action === 'Purchase').length, 'sample labels', 0.44, '↗')}${statCard('SALES', source.filter(r => r.action === 'Sale').length, 'sample labels', -0.19, '↘')}${statCard('DATA STATUS', 'DEMO', 'not sourced filings', 0, '◉')}</div>
    ${panel(congress ? 'Recent congressional disclosures' : 'Recent insider transactions', 'Local examples only · values and names are not current disclosures', `<div class="filter-toolbar"><label class="filter-input"><span>⌕</span><input data-filter="disclosureSearch" value="${esc(state.disclosureSearch)}" placeholder="Search person or ticker" /></label><span class="toolbar-spacer"></span><span class="small-muted">Sort: newest sample first</span></div><div class="table-wrap"><table class="data-table"><thead><tr>${congress ? '<th>TRADE DATE</th><th>TRADER</th><th>TICKER</th><th>ACTION</th><th>REPORTED RANGE</th><th>FILED</th><th>RECORD TYPE</th>' : '<th>TRADE DATE</th><th>ROLE</th><th>TICKER</th><th>ACTION</th><th>SHARES</th><th>VALUE</th><th>FILING</th>'}</tr></thead><tbody>${body || `<tr><td colspan="7">${tableEmpty('No records match this search.')}</td></tr>`}</tbody></table></div><div class="table-bottom"><span>${rows.length} local sample records</span><span>Verify disclosures against primary government or SEC filings</span></div>`)}`;
}

function renderScreener() {
  let rows = [...screenerRows];
  if (state.screenerSector !== 'all') rows = rows.filter(r => r.sector === state.screenerSector);
  if (state.screenerType === 'gainers') rows = rows.filter(r => r.change > 0);
  if (state.screenerType === 'losers') rows = rows.filter(r => r.change < 0);
  if (state.screenerType === 'high-iv') rows = rows.filter(r => r.iv >= 50);
  return `${pageHeading('SCANNERS', 'Market screener', 'A local example screener over a small, synthetic universe. Provider screening rules are not inferred.', '<button class="button secondary" data-action="reset-screener">Reset</button><button class="button secondary" data-view="finviz">Filter contract lab →</button><button class="button primary" data-view="alerts">＋ Save as alert</button>')}
    <div class="screener-controls"><div><span class="eyebrow">UNIVERSE</span><b>U.S. liquid names</b></div><label><span>SECTOR</span><select data-filter="screenerSector"><option value="all">All sectors</option>${[...new Set(screenerRows.map(r => r.sector))].map(s => `<option value="${s}" ${state.screenerSector === s ? 'selected' : ''}>${s}</option>`).join('')}</select></label><label><span>QUICK FILTER</span><select data-filter="screenerType"><option value="all" ${state.screenerType === 'all' ? 'selected' : ''}>All samples</option><option value="gainers" ${state.screenerType === 'gainers' ? 'selected' : ''}>Gainers</option><option value="losers" ${state.screenerType === 'losers' ? 'selected' : ''}>Losers</option><option value="high-iv" ${state.screenerType === 'high-iv' ? 'selected' : ''}>IV ≥ 50%</option></select></label><div class="screener-note">Rows: <b>${rows.length}</b></div></div>
    ${panel('Equity and options overview', 'Sample price, volume, IV, and put/call context', `<div class="table-wrap"><table class="data-table"><thead><tr><th>TICKER</th><th>COMPANY</th><th>SECTOR</th><th>LAST</th><th>DAY</th><th>VOLUME</th><th>IV SAMPLE</th><th>PUT/CALL VOL.</th><th></th></tr></thead><tbody>${rows.map(r => `<tr><td>${tickerLink(r.ticker)}</td><td>${r.name}</td><td class="muted">${r.sector}</td><td>${money(r.price)}</td><td>${changeText(r.change)}</td><td>${r.volume}</td><td>${r.iv.toFixed(1)}%</td><td>${r.putCall.toFixed(2)}</td><td><button class="tiny-action ${state.watchlist.includes(r.ticker) ? 'saved' : ''}" data-action="watch-toggle" data-ticker="${r.ticker}">${state.watchlist.includes(r.ticker) ? '★' : '☆'}</button></td></tr>`).join('') || `<tr><td colspan="9">${tableEmpty('Adjust the screen filters.')}</td></tr>`}</tbody></table></div><div class="table-bottom"><span>Sample universe: ${screenerRows.length} symbols</span><span>Numbers are synthetic and not live screening output</span></div>`)}`;
}

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

function parseFinvizSnapshotCsv(source) {
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

function calculateFinvizContract(model) {
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

function createFinvizContractSample() {
  const metadata = {
    NVDA: ['nasd', 'S&P 500|NASDAQ100', 4_500_000_000_000, 52.4, 1.42, 'wedgeup', 'd'],
    PLTR: ['nasd', 'S&P 500|NASDAQ100', 390_000_000_000, 210.3, 1.68, 'wedgeup2', 'h'],
    TSLA: ['nasd', 'S&P 500|NASDAQ100', 1_300_000_000_000, 176.2, 1.12, 'wedgedown', 'ih'],
    AMD: ['nasd', 'S&P 500|NASDAQ100', 305_000_000_000, 118.7, 1.21, 'channelup', 'stw'],
    COIN: ['nasd', 'S&P 500', 82_000_000_000, 48.1, 1.53, 'doubletop', 'dd'],
    META: ['nasd', 'S&P 500|NASDAQ100', 1_850_000_000_000, 29.8, 0.93, 'horizontal', 'gd'],
    AAPL: ['nasd', 'S&P 500|NASDAQ100', 4_050_000_000_000, 32.7, 0.88, 'tlresistance', 'mw'],
    XOM: ['nyse', 'S&P 500', 600_000_000_000, 15.4, 0.79, 'wedgesupport', 'mb'],
  };
  const rows = screenerRows.map(item => {
    const [exchange, indexes, marketCap, pe, relativeVolume, pattern, candlestick] = metadata[item.ticker];
    return { ticker: item.ticker, name: item.name, securityType: 'stock', exchange, indexes, sector: item.sector, industry: '', country: 'USA', marketCap, pe, price: item.price, avgVolume: parseFinvizScalar(item.volume), relativeVolume, changePct: item.change, pattern, candlestick, raw: {} };
  });
  rows.push({ ticker: 'XLE', name: 'Energy Select Sector ETF', securityType: 'ETF', exchange: 'nyse', indexes: '', sector: 'Energy', industry: '', country: 'USA', marketCap: 34_000_000_000, pe: null, price: 93.21, avgVolume: 16_000_000, relativeVolume: 0.94, changePct: 0.42, pattern: '', candlestick: '', raw: {} });
  return rows;
}

function compactFinvizNumber(value, suffix = '') {
  if (!Number.isFinite(value)) return '—';
  const abs = Math.abs(value), unit = abs >= 1e12 ? [1e12, 'T'] : abs >= 1e9 ? [1e9, 'B'] : abs >= 1e6 ? [1e6, 'M'] : [1, ''];
  return `${value < 0 ? '−' : ''}${unit[1] ? `${(abs / unit[0]).toFixed(2)}${unit[1]}` : abs.toLocaleString('en-US')}${suffix}`;
}

function renderFinvizContractLab() {
  const model = state.finvizLab;
  let result = null, calculateError = '';
  if (model.rows.length) {
    try { result = calculateFinvizContract(model); }
    catch (error) { calculateError = error instanceof Error ? error.message : 'Could not apply this filter query.'; }
  }
  const status = result ? `<div class="finviz-summary"><span><b>${result.rows.length}</b> matched</span><span>${result.filtersApplied} distinct filter${result.filtersApplied === 1 ? '' : 's'}${result.overrides ? ` · ${result.overrides} repeated filter override${result.overrides === 1 ? '' : 's'}` : ''}</span><span>${result.excludedEtfs.length} ETF${result.excludedEtfs.length === 1 ? '' : 's'} excluded from stocks universe</span></div>` : '';
  const rows = result?.rows.map(row => `<tr><td>${tickerLink(row.ticker)}</td><td>${esc(row.name || '—')}</td><td>${esc(row.sector || '—')}</td><td>${esc(compactFinvizNumber(row.marketCap))}</td><td>${Number.isFinite(row.pe) ? row.pe.toFixed(2) : '—'}</td><td>${Number.isFinite(row.price) ? money(row.price) : '—'}</td><td class="${Number.isFinite(row.changePct) ? row.changePct >= 0 ? 'positive' : 'negative' : 'muted'}">${Number.isFinite(row.changePct) ? `${row.changePct.toFixed(2)}%` : '—'}</td><td>${compactFinvizNumber(row.avgVolume)}</td><td>${Number.isFinite(row.relativeVolume) ? `${row.relativeVolume.toFixed(2)}×` : '—'}</td><td>${esc(row.pattern || '—')}</td><td>${esc(row.candlestick || '—')}</td></tr>`).join('') || `<tr><td colspan="11">${tableEmpty(result ? 'No snapshot rows match the current filters.' : 'Load a CSV or synthetic sample to run the local screen.')}</td></tr>`;
  const notices = result ? [result.missingTickers.length ? `Not found: ${result.missingTickers.join(', ')}` : '', result.excludedEtfs.length ? `ETF rows excluded: ${result.excludedEtfs.join(', ')}` : '', result.unclassifiedUniverseRows ? `${result.unclassifiedUniverseRows} rows have no SecurityType; ETFs cannot be identified for those rows.` : '', result.filteredTickers.length ? `Present but filtered out: ${result.filteredTickers.join(', ')}` : ''].filter(Boolean).map(text => `<span>${esc(text)}</span>`).join('') : '';
  return `${pageHeading('PUBLIC CONTRACT · LOCAL SNAPSHOT', 'Finviz filter contract lab', 'Apply a measured subset of Finviz’s screener grammar to a user-provided point-in-time CSV. This is a local contract analogue, not Finviz data or pattern detection.', '<button class="button secondary" data-view="coverage">Vendor evidence →</button>')}
    ${panel('Snapshot and query controls', 'Filters are ANDed across distinct keys; repeating a key replaces its prior value. Sorting uses o=column or o=-column; o=tickersfilter preserves the provided t= list order.', `<form id="finviz-contract-form" class="finviz-controls"><label class="field-label">FILTER QUERY f=<input name="filterQuery" value="${esc(model.filterQuery)}" placeholder="exch_nasd,cap_largeover,ta_pattern_wedgeup" /></label><label class="field-label">ORDER o=<input name="order" value="${esc(model.order)}" placeholder="-change or tickersfilter" /></label><label class="field-label">TICKER LIST t=<input name="tickers" value="${esc(model.tickers)}" placeholder="NVDA,SPY,XLE" /></label><button class="button primary">Apply local screen</button><button class="button secondary" type="button" data-action="finviz-demo">Load synthetic sample</button></form>
      <div class="activity-file-row"><label class="field-label">SNAPSHOT CSV<input id="finviz-file" type="file" accept=".csv,text/csv" /></label><span class="small-muted">${model.filename ? `Loaded: ${esc(model.filename)}` : 'CSV stays in this browser tab.'}</span></div>
      <div class="activity-input-help"><b>CSV:</b> <code>Ticker,Name,SecurityType,Exchange,Index,Sector,Country,MarketCap,PE,Price,AvgVolume,RelativeVolume,ChangePct,PatternTag,CandlestickTag</code>. Minimum is <code>Ticker</code>; other columns are optional. Supported filters: <code>exch_nasd|nyse|amex</code>, <code>sec_&lt;sector&gt;</code>, <code>geo_&lt;country&gt;</code>, <code>idx_&lt;index&gt;</code>, <code>cap_largeover</code> (&gt;$10B), documented <code>ta_pattern_&lt;tag&gt;</code> and <code>ta_candlestick_&lt;tag&gt;</code>. Pattern columns must be supplied by you; this tool does not detect patterns.</div>
      ${model.error ? `<div class="optionlab-error" role="alert">${esc(model.error)}</div>` : ''}${calculateError ? `<div class="optionlab-error" role="alert">${esc(calculateError)}</div>` : ''}${model.notice ? `<div class="activity-notice">${esc(model.notice)}</div>` : ''}`, '')}
    ${result ? `${status}${notices ? `<div class="finviz-notices">${notices}</div>` : ''}${panel('Screen results', `${result.sourceCount} source rows · ${result.excludedEtfs.length} ETF exclusions · ${result.filteredOut} rows removed by query filters`, `<div class="table-wrap"><table class="data-table"><thead><tr><th>TICKER</th><th>COMPANY</th><th>SECTOR</th><th>MARKET CAP</th><th>P/E</th><th>PRICE</th><th>CHANGE</th><th>AVG VOL</th><th>REL VOL</th><th>PATTERN TAG</th><th>CANDLESTICK TAG</th></tr></thead><tbody>${rows}</tbody></table></div>`, '')}` : model.rows.length ? '<div class="empty-state"><span>!</span><b>Screen not applied</b><p>Correct the query or order field above, then apply it again.</p></div>' : '<div class="empty-state"><span>⌕</span><b>No snapshot loaded</b><p>Import a local ticker snapshot or load the synthetic example.</p></div>'}
    <div class="evidence-callout portfolio-callout"><b>Contract boundary</b><span>The public teardown supports AND across distinct filters, last-value-wins for repeated keys, ticker-list ordering, sorting direction, and a stocks universe that excludes ETFs. This lab implements a documented subset against your CSV only. It does not reproduce all 82 filter controls, Finviz’s live universe, custom Elite filters, server-side results, or the unrecovered pattern detector. Legacy Signals parameters remain unsupported.</span><a href="../../research/rea-teardowns/finviz-screener/TEARDOWN.md">Review teardown evidence →</a></div>`;
}

function parseStockRoverFactorCsv(source) {
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

function createStockRoverFactorSample() {
  const symbols = ['MSFT', 'NVDA', 'JPM', 'LLY', 'COST', 'XOM', 'AMD', 'V', 'UNH', 'CAT', 'CRM', 'KO'];
  const sectors = ['Information Technology', 'Information Technology', 'Financials', 'Health Care', 'Consumer Staples', 'Energy', 'Information Technology', 'Financials', 'Health Care', 'Industrials', 'Information Technology', 'Consumer Staples'];
  return symbols.map((ticker, i) => ({
    ticker, sector: sectors[i], asOf: '2026-10-26', raw: {
      EVEBITDA: 8 + i * 1.65, PE: 11 + i * 2.35, EPSPredictabilityR1: 0.42 + ((i * 5) % 10) * 0.065,
      PriceTangibleBook: 1.1 + ((i * 3) % 9) * 0.38, PriceSales: 0.85 + ((i * 4) % 11) * 0.34,
      RevenueGrowth5Y: -2 + ((i * 7) % 31), NetIncomeGrowth5Y: -8 + ((i * 11) % 45),
      ForwardEBITDAGrowth: -5 + ((i * 9) % 33), ForwardSalesGrowth: -3 + ((i * 6) % 28),
      ForwardEPSGrowth: i === 10 ? null : -12 + ((i * 13) % 48),
      ROIC: 3 + ((i * 7) % 29), NetMargin: -2 + ((i * 5) % 27), GrossMargin: 14 + ((i * 9) % 61),
      InterestCoverage: 1.2 + i * 1.85, DebtEquity: 0.12 + i * 0.18, ShortInterestRatio: 0.8 + i * 0.58,
      Return1M: -8 + ((i * 9) % 21), Return3M: -15 + ((i * 11) % 39), Return6M: -22 + ((i * 17) % 56),
      Return12M: -30 + ((i * 23) % 83), PriceTo52WeekHigh: 0.69 + i * 0.024, DaysSince52WeekHigh: 112 - i * 8,
      NormalizedMACDSignal: (i - 5.5) * 0.0035,
    },
  }));
}

function calculateStockRoverFactorScores(sourceRows) {
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

function factorScore(value) { return Number.isFinite(value) ? value.toFixed(1) : '—'; }

function renderStockRoverFactorLab() {
  const model = state.stockRoverLab;
  const result = model.rows.length ? calculateStockRoverFactorScores(model.rows) : null;
  const rows = result?.rows.slice(0, 250).map(row => `<tr><td>${tickerLink(row.ticker)}</td><td>${esc(row.sector)}</td><td>${factorScore(row.categoryScores.value)}</td><td>${factorScore(row.categoryScores.growth)}</td><td>${factorScore(row.categoryScores.quality)}</td><td>${factorScore(row.categoryScores.sentiment)}</td><td><b>${factorScore(row.composite)}</b></td><td>${row.completedCategories}/4 · ${row.missingMetrics} missing</td></tr>`).join('') || `<tr><td colspan="8">${tableEmpty('Load a point-in-time snapshot or synthetic sample to calculate ranks.')}</td></tr>`;
  const metricRows = stockRoverFactorCategories.map(category => `<tr><td>${esc(category.label)}</td><td>${category.metrics.map(metric => `${esc(metric.label)} <code>${esc(metric.key)}</code>`).join(' · ')}</td><td>${category.metrics.length}</td></tr>`).join('');
  const summary = result ? `<div class="coverage-summary stockrover-summary"><div><b>${integer(result.sourceCount)}</b><span>universe rows · ${esc(model.rows[0].asOf)}</span></div><div><b>${integer(result.fullyScored)}</b><span>complete 4-factor composites</span></div><div><b>${factorScore(result.medianComposite)}</b><span>median complete composite</span></div><div><b>${result.top ? `${esc(result.top.ticker)} · ${factorScore(result.top.composite)}` : '—'}</b><span>highest complete composite</span></div></div>` : '';
  return `${pageHeading('PUBLIC INPUTS · DESK RECONSTRUCTION', 'Stock Rover factor profile lab', 'Rank user-supplied cross-sectional fundamentals against the published Value, Growth, Quality, and Sentiment input lists. Local calculation only; scoring weights are a declared desk choice.', '<button class="button secondary" data-view="coverage">Vendor evidence →</button>')}
    ${panel('Point-in-time cross-section', 'Use one decision-date snapshot. Every input column is required; blank metric cells remain missing and are never imputed.', `<div class="stockrover-controls"><label class="button primary file-pick">Choose CSV<input id="stockrover-file" type="file" accept=".csv,text/csv" /></label><button class="button secondary" type="button" data-action="stockrover-template">Download CSV template</button><button class="button secondary" type="button" data-action="stockrover-demo">Load synthetic sample</button>${result ? '<button class="button secondary" type="button" data-action="stockrover-export">Export score audit</button>' : ''}<span class="small-muted">${model.filename ? `Loaded: ${esc(model.filename)} · ${model.source === 'synthetic' ? 'synthetic' : 'local CSV'}` : 'No snapshot loaded; files stay in this browser tab.'}</span></div>
      <div class="activity-input-help"><b>Required columns:</b> <code>Ticker,Sector,AsOf</code> plus all ${stockRoverFactorMetrics.length} metric columns. AsOf must be a shared <code>YYYY-MM-DD</code> decision date; this does not verify that source data were actually available then. Percent returns, growth, and margins use percentage points (e.g. <code>12.5</code> = 12.5%); <code>PriceTo52WeekHigh</code> is a 0–1 ratio; <code>NormalizedMACDSignal</code> is the price-normalized MACD-line minus signal value. Missing cells accept blank, NA, or N/A. File contents are neither uploaded nor retained after the tab closes.</div>
      ${model.error ? `<div class="optionlab-error" role="alert">${esc(model.error)}</div>` : ''}${model.notice ? `<div class="activity-notice">${esc(model.notice)}</div>` : ''}`, '')}
    ${summary}
    ${result ? `<section class="panel stockrover-results"><div class="panel-heading"><div><h2>Cross-sectional factor scores</h2><p>Midrank percentiles run 0–100; equal-weight inputs within each category and equal-weight categories in the composite. Sector-relative ranking applies only to Price / tangible book and Price / sales.</p></div><span class="small-muted">${result.rows.length > 250 ? `Showing 250 of ${integer(result.rows.length)}` : `${integer(result.rows.length)} symbols`}</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>TICKER</th><th>SECTOR</th><th>VALUE</th><th>GROWTH</th><th>QUALITY</th><th>SENTIMENT</th><th>COMPOSITE</th><th>COVERAGE</th></tr></thead><tbody>${rows}</tbody></table></div></section>` : '<div class="empty-state"><span>⌖</span><b>No factor snapshot loaded</b><p>Import your CSV or load the synthetic workflow example.</p></div>'}
    <section class="panel stockrover-method"><div class="panel-heading"><div><h2>Inputs and interpretation boundary</h2><p>Percentiles use available observations only for each input. A category is blank unless every input in that category is present; the composite is blank unless all four categories are complete.</p></div></div><details><summary>Show the published input list and ranking directions</summary><div class="table-wrap"><table class="data-table"><thead><tr><th>CATEGORY</th><th>INPUTS</th><th>COUNT</th></tr></thead><tbody>${metricRows}</tbody></table></div></details><div class="evidence-callout portfolio-callout"><b>Reconstruction boundary</b><span>R1 is a desk proxy for EPS predictability; R2 uses 1/3/6/12-month total returns; R3 uses normalized MACD line minus signal; equal weighting is R4. This lab does not implement Piotroski F-Score, Altman Z-Score, DCF, margin of safety, vendor weights, ratings, or investor warnings. It is not a live Stock Rover feed and makes no alpha claim.</span><a href="../../research/rea-teardowns/stockrover/STOCKROVER-FACTOR-LAB-IMPLEMENTATION.md">Review build notes →</a> · <a href="../../research/rea-teardowns/stockrover/SPEC.md">Review research SPEC →</a></div></section>`;
}

function eventCard(item) {
  return `<div class="event-card"><div class="event-date"><b>${item.date.split(' ')[1]}</b><span>${item.date.split(' ')[0]}</span></div><div class="event-info"><span class="event-type">${item.type}</span><b>${esc(item.title)}</b><small>${esc(item.detail)}</small></div><time>${item.time}</time></div>`;
}
function renderCalendar() {
  const items = state.calendarRange === 'week' ? calendarItems.slice(0, 5) : calendarItems;
  return `${pageHeading('CATALYSTS', 'Event calendar', 'Economic, earnings, and market events in a synthetic sample calendar.', '<button class="button secondary" data-action="calendar-range" data-value="week">This week</button><button class="button secondary" data-action="calendar-range" data-value="month">Next 30 days</button>')}
    <div class="calendar-toolbar"><div class="month-title"><span>‹</span><b>October 26 — November 2, 2026</b><span>›</span></div><div class="calendar-filters">${label('ECONOMIC', 'blue')}${label('EARNINGS', 'purple')}${label('OPTIONS', 'orange')}${label('FED', 'red')}</div></div>
    ${panel(state.calendarRange === 'week' ? 'Upcoming this week' : 'Next 30 days', `${items.length} sample calendar events`, `<div class="event-list">${items.map(eventCard).join('')}</div><div class="calendar-disclaimer">Calendar examples are generated locally. Check official releases for actual event dates and times.</div>`)}`;
}

function newsCard(item) {
  return `<article class="headline-card"><div class="headline-meta"><time>${item.time} ET</time>${tickerLink(item.ticker)}${label(item.tag, 'muted-badge')}</div><b>${esc(item.title)}</b><small>${esc(item.source)} · synthetic</small></article>`;
}
function renderNews() {
  const items = newsItems.filter(item => !state.newsSearch || `${item.title} ${item.ticker} ${item.tag}`.toLowerCase().includes(state.newsSearch.toLowerCase()));
  return `${pageHeading('RESEARCH DESK', 'News flow', 'Search and scan locally generated headline examples. No third-party news feed is connected.', '<button class="button secondary" data-action="clear-news">Clear search</button>')}
    <div class="news-layout"><div class="news-filter-panel"><h2>Filter feed</h2><label class="field-label">TICKER OR KEYWORD<input data-filter="newsSearch" value="${esc(state.newsSearch)}" placeholder="e.g. NVDA" /></label><div class="filter-chip-row"><button class="filter-chip selected" data-action="news-tag" data-value="all">All news</button><button class="filter-chip" data-action="news-tag" data-value="TECH">Technology</button><button class="filter-chip" data-action="news-tag" data-value="MACRO">Macro</button></div><p class="small-muted">Feed source: local synthetic examples</p></div><div class="news-stream">${items.map(newsCard).join('') || tableEmpty('Try a shorter search phrase.')}<div class="load-more">You’re viewing all sample headlines</div></div></div>`;
}

function renderTicker() {
  const symbol = state.ticker;
  const match = screenerRows.find(r => r.ticker === symbol) || { name: `${symbol} sample security`, price: underlying(symbol), change: 0.72, volume: '—', iv: 38.4, putCall: 0.92 };
  const base = underlying(symbol);
  const tickerPrices = Array.from({ length: 20 }, (_, i) => base + Math.sin(i * 0.7) * base * 0.004 + (i - 10) * base * 0.00045);
  const line = lineChart([{ values: tickerPrices, color: '#44d4a9', fill: true }], { width: 760, height: 250, axis: '$' });
  const chain = [
    { strike: underlying(symbol) - 10, cb: 2.24, ca: 2.48, pb: 1.82, pa: 2.07, vol: 2840, oi: 12400 },
    { strike: underlying(symbol) - 5, cb: 4.15, ca: 4.42, pb: 3.48, pa: 3.74, vol: 6420, oi: 18600 },
    { strike: underlying(symbol), cb: 6.8, ca: 7.15, pb: 5.9, pa: 6.22, vol: 10320, oi: 22100 },
    { strike: underlying(symbol) + 5, cb: 3.66, ca: 3.92, pb: 8.1, pa: 8.45, vol: 4960, oi: 14800 },
    { strike: underlying(symbol) + 10, cb: 1.8, ca: 2.03, pb: 10.5, pa: 10.9, vol: 2170, oi: 9900 },
  ];
  return `${pageHeading('SECURITY RESEARCH', `${tickerLink(symbol)} <span class="heading-company">${esc(match.name)}</span>`, 'A consolidated local research view with price, options, exposure, and activity context.', `<button class="button ${state.watchlist.includes(symbol) ? 'secondary' : 'primary'}" data-action="watch-toggle" data-ticker="${symbol}">${state.watchlist.includes(symbol) ? '★ In watchlist' : '☆ Add to watchlist'}</button><button class="button secondary" data-view="flow">View flow →</button>`)}
    <div class="ticker-hero"><div><span class="ticker-symbol">${symbol}</span><span class="ticker-exchange">NASDAQ · DEMO</span><div class="ticker-last">${money(match.price)} <span class="${signedClass(match.change)}">${pct(match.change)}</span></div><small>Synthetic sample price · not a quote</small></div><div class="ticker-metrics"><div><span>VOLUME</span><b>${match.volume}</b></div><div><span>IMPLIED VOL.</span><b>${match.iv.toFixed(1)}%</b></div><div><span>PUT / CALL VOL.</span><b>${match.putCall.toFixed(2)}</b></div><div><span>SESSION</span><b>DEMO</b></div></div></div>
    <div class="two-column-layout ticker-layout">${panel('Price action', `${symbol} · intraday sample series`, `<div class="chart-tabs"><button class="selected">1D</button><button>5D</button><button>1M</button><button>6M</button><span class="toolbar-spacer"></span><span class="chart-value">${money(match.price)} <small>demo close</small></span></div>${line}<div class="chart-legend"><span><i style="--legend:#44d4a9"></i>Sample close</span><span class="small-muted">OHLC pattern is synthetic</span></div>`, '')}${panel('Options snapshot', 'Contract chain shape · synthetic values', `<div class="chain-mini"><div class="chain-column call-bg"><span>CALL BID</span>${chain.map(r => `<b>${r.cb.toFixed(2)}</b>`).join('')}</div><div class="chain-column strike-bg"><span>STRIKE</span>${chain.map(r => `<b>${money(r.strike)}</b>`).join('')}</div><div class="chain-column put-bg"><span>PUT ASK</span>${chain.map(r => `<b>${r.pa.toFixed(2)}</b>`).join('')}</div></div><div class="chain-bottom"><span>Volume <b>${integer(chain.reduce((s, r) => s + r.vol, 0))}</b></span><span>Open interest <b>${integer(chain.reduce((s, r) => s + r.oi, 0))}</b></span></div><button class="button secondary full-button" data-view="tools">Open payoff calculator →</button>`, '')}</div>
    <div class="three-column-layout">${panel('Flow activity', 'Quote-side sample', `<div class="mini-bars"><span>Ask-side call premium</span><b class="positive">$286K</b><i style="width:68%"></i><span>Bid-side call premium</span><b class="negative">$114K</b><i class="red" style="width:32%"></i><span>Ask-side put premium</span><b class="negative">$183K</b><i class="red" style="width:48%"></i><span>Bid-side put premium</span><b class="positive">$92K</b><i style="width:24%"></i></div>`, '')}${panel('Exposure levels', 'Sample only', `<div class="ticker-levels"><div><span>Call wall</span><b>${money(underlying(symbol) + 10)}</b></div><div><span>Gamma flip</span><b>${money(underlying(symbol) - 5)}</b></div><div><span>Put wall</span><b>${money(underlying(symbol) - 15)}</b></div></div><button class="text-button" data-view="gex">Explore GEX →</button>`, '')}${panel('Related activity', 'Local sample records', `<div class="related-lines"><div><span>Dark pool</span><b>3 prints</b><button class="text-button" data-view="darkpool">View →</button></div><div><span>Insider filings</span><b>1 record</b><button class="text-button" data-view="insiders">View →</button></div><div><span>Headlines</span><b>2 items</b><button class="text-button" data-view="news">View →</button></div></div>`, '')}</div>`;
}

function rangeSeries() {
  const multiplier = state.chartRange === '1D' ? 1 : state.chartRange === '5D' ? 1.8 : state.chartRange === '1M' ? 2.8 : 4;
  const base = underlying(state.chartSymbol), amplitude = base * 0.0022 * multiplier;
  const values = Array.from({ length: 46 }, (_, i) => base + Math.sin(i * 0.6) * amplitude + Math.cos(i * 0.17) * amplitude * 1.25 + (i - 23) * amplitude * 0.025);
  return values;
}
function renderCharts() {
  const symbol = state.chartSymbol;
  const chartValues = rangeSeries();
  const movingAverage = chartValues.map((_, i) => chartValues.slice(Math.max(0, i - 4), i + 1).reduce((sum, value) => sum + value, 0) / Math.min(5, i + 1));
  return `${pageHeading('CHARTING WORKSPACE', 'Chart workspace', 'A compact charting prototype with local price fixtures, overlays, and saved local tabs.', `<button class="button secondary" data-view="ticker">Ticker research →</button><button class="button primary" data-action="save-chart">Save layout</button>${state.layoutMessage ? `<span class="small-muted">${esc(state.layoutMessage)}</span>` : ''}`)}
    <div class="chart-toolbar"><label class="chart-symbol-input"><span>⌕</span><input data-state="chartSymbol" value="${esc(symbol)}" maxlength="10" /><span class="exchange-tag">NASDAQ</span></label><div class="timeframe-group">${['1D', '5D', '1M', '6M'].map(t => `<button class="${state.chartRange === t ? 'selected' : ''}" data-action="chart-range" data-value="${t}">${t}</button>`).join('')}</div><div class="chart-toolbar-right"><button class="icon-button" title="Indicators" data-action="toggle-indicators">∿</button><button class="icon-button" title="Fullscreen" data-action="fullscreen">⛶</button></div></div>
    ${state.savedLayouts.length ? `<div class="saved-layout-strip"><b>Saved layouts</b>${state.savedLayouts.map((layout, i) => `<button data-action="load-layout" data-index="${i}">${esc(layout.symbol)} · ${esc(layout.range)}</button>`).join('')}</div>` : ''}
    <div class="chart-workspace"><div class="chart-canvas-panel"><div class="chart-topline"><div><b>${symbol}</b><span class="muted"> · Synthetic ${state.chartRange} price history</span></div><div><b>${money(underlying(symbol))}</b><span class="positive"> ${pct(0.82)}</span></div></div>${lineChart([{ values: chartValues, color: '#41d6aa', fill: true }, { values: movingAverage, color: '#a78bfa' }], { width: 1020, height: 380, axis: '$' })}<div class="chart-bottom-labels"><span>10:00</span><span>11:00</span><span>12:00</span><span>13:00</span><span>14:00</span><span>15:00</span><span>16:00</span></div></div><aside class="chart-tools"><div class="tool-heading"><b>Overlays</b><button class="text-button" data-action="reset-overlays">Reset</button></div><label class="toggle-row"><span><i class="overlay-dot green"></i>Volume weighted avg.</span><input type="checkbox" checked /></label><label class="toggle-row"><span><i class="overlay-dot purple"></i>20-period average</span><input type="checkbox" checked /></label><label class="toggle-row"><span><i class="overlay-dot blue"></i>VWAP</span><input type="checkbox" /></label><label class="toggle-row"><span><i class="overlay-dot orange"></i>Market tide</span><input type="checkbox" /></label><hr/><div class="tool-heading"><b>Drawing tools</b><span class="muted">8 shown</span></div><div class="drawing-grid"><button>↗ Trend</button><button>⌖ Crosshair</button><button>〰 Brush</button><button>▱ Rectangle</button><button>F Fib retrace</button><button>T Text note</button><button>⊞ Price range</button><button>↔ Measure</button></div><hr/><div class="chart-note"><b>Demo chart</b><p>This chart does not contain licensed market data, vendor studies, or a Pine-compatible runtime.</p></div></aside></div>`;
}

function createDemoStrategyRows() {
  const rows = [];
  const date = new Date('2024-01-02T00:00:00Z');
  for (let i = 0; i < 420; i++) {
    const close = 100 * Math.exp(i * 0.00042 + 0.11 * Math.sin(i / 21) + 0.055 * Math.sin(i / 7.2) + 0.018 * Math.sin(i / 2.6));
    rows.push({ date: date.toISOString().slice(0, 10), close });
    do { date.setUTCDate(date.getUTCDate() + 1); } while (date.getUTCDay() === 0 || date.getUTCDay() === 6);
  }
  return rows;
}

function parseCsvRows(source) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < source.length; i++) {
    const char = source[i];
    if (quoted) {
      if (char === '"' && source[i + 1] === '"') { field += '"'; i++; }
      else if (char === '"') quoted = false;
      else field += char;
      continue;
    }
    if (char === '"' && field.length === 0) { quoted = true; continue; }
    if (char === ',') { row.push(field); field = ''; continue; }
    if (char === '\n' || char === '\r') {
      if (char === '\r' && source[i + 1] === '\n') i++;
      row.push(field);
      if (row.some(value => value.trim())) rows.push(row);
      row = []; field = '';
      continue;
    }
    field += char;
  }
  if (quoted) throw new Error('The CSV ends inside a quoted field.');
  row.push(field);
  if (row.some(value => value.trim())) rows.push(row);
  return rows;
}

function parseStrategyCsv(source) {
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

function rollingMean(values, period) {
  let sum = 0;
  return values.map((value, index) => {
    sum += value;
    if (index >= period) sum -= values[index - period];
    return index + 1 >= period ? sum / period : null;
  });
}

function strategyStats(records, periodsPerYear) {
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

function analyzeStrategy() {
  const p = state.strategy;
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

function strategyEquitySvg(records) {
  if (!records.length) return '';
  const values = [1];
  let equity = 1;
  for (const record of records) { equity *= Math.max(0, 1 + record.net); values.push(equity); }
  const maxPoints = 160, step = Math.max(1, Math.ceil(values.length / maxPoints));
  const sampled = values.filter((_, i) => i % step === 0 || i === values.length - 1);
  const min = Math.min(...sampled), max = Math.max(...sampled), span = max - min || 1;
  const width = 820, height = 190, pad = 12;
  const points = sampled.map((value, i) => `${(pad + i * (width - pad * 2) / Math.max(1, sampled.length - 1)).toFixed(1)},${(height - pad - (value - min) / span * (height - pad * 2)).toFixed(1)}`).join(' ');
  const baseline = (height - pad - (1 - min) / span * (height - pad * 2)).toFixed(1);
  return `<svg class="strategy-equity-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Synthetic or imported close-only strategy equity curve"><line x1="${pad}" y1="${baseline}" x2="${width - pad}" y2="${baseline}" class="strategy-baseline"/><polyline points="${points}" fill="none" stroke="#42d6ab" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/></svg>`;
}

function percentReturn(value) { return `${(value * 100).toFixed(2)}%`; }

function renderStrategyLab() {
  if (!state.strategy.rows.length) state.strategy.rows = createDemoStrategyRows();
  const p = state.strategy;
  const result = analyzeStrategy();
  const overall = result.error ? null : result.overall;
  const stat = (labelText, value, sub, cls = '') => `<div class="strategy-stat"><span>${labelText}</span><b class="${cls}">${value}</b><small>${sub}</small></div>`;
  const splitStats = (labelText, value) => value ? `<div class="strategy-split-row"><b>${labelText}</b><span>Return <strong class="${value.totalReturn >= 0 ? 'positive' : 'negative'}">${percentReturn(value.totalReturn)}</strong></span><span>Max drawdown <strong class="negative">${percentReturn(value.maxDrawdown)}</strong></span><span>Buy & hold <strong>${percentReturn(value.benchmarkReturn)}</strong></span><span>Win bars <strong>${percentReturn(value.winBars)}</strong></span></div>` : '';
  const history = state.strategyRuns.length ? state.strategyRuns.map(run => `<tr><td>${esc(run.savedAt)}</td><td>${esc(run.filename)}</td><td>${run.fast}/${run.slow}</td><td>${percentReturn(run.outOfSample)}</td><td>${percentReturn(run.maxDrawdown)}</td></tr>`).join('') : '<tr><td colspan="5" class="muted">No saved run summaries in this browser.</td></tr>';
  const errorText = result.error || p.error;
  const actions = `<button class="button secondary" data-action="strategy-demo">Load synthetic sample</button><button class="button secondary" data-action="strategy-export" ${result.error ? 'disabled' : ''}>Export results CSV</button>`;
  return `${pageHeading('RESEARCH WORKBENCH', 'Strategy Lab', 'Run a transparent long-or-flat moving-average study on your own CSV bars. Signals use a full-bar delay; costs are charged on entries and exits.', actions)}
    <div class="strategy-data-banner"><div><span class="coverage-state ${p.source === 'csv' ? 'coverage-local' : 'coverage-partial'}">${p.source === 'csv' ? 'LOCAL CSV' : 'SYNTHETIC SAMPLE'}</span><b>${esc(p.filename)}</b><small>${p.rows.length.toLocaleString()} bars · close-only · file data stays in this tab and is not uploaded or saved</small>${p.notice ? `<small class="strategy-notice">${esc(p.notice)}</small>` : ''}</div><label class="button primary file-pick">Choose CSV<input id="strategy-file" type="file" accept=".csv,text/csv" /></label></div>
    <div class="strategy-grid">
      <section class="panel"><div class="panel-heading"><div><h2>Study assumptions</h2><p>One long-or-flat trend rule; no shorting or optimization</p></div></div><form class="strategy-form" id="strategy-config">
        <label class="field-label">FAST SMA<input name="fast" type="number" min="2" max="5000" step="1" value="${esc(p.fast)}" required /></label>
        <label class="field-label">SLOW SMA<input name="slow" type="number" min="3" max="5000" step="1" value="${esc(p.slow)}" required /></label>
        <label class="field-label">COST / SIDE (BPS)<input name="costBps" type="number" min="0" max="2000" step="0.1" value="${esc(p.costBps)}" required /></label>
        <label class="field-label">TRAIN SPLIT (%)<input name="splitPct" type="number" min="50" max="90" step="1" value="${esc(p.splitPct)}" required /></label>
        <label class="field-label">BARS / YEAR<input name="periodsPerYear" type="number" min="1" max="10000" step="1" value="${esc(p.periodsPerYear)}" required /></label>
        <button class="button primary strategy-run-button">Recalculate study</button>
      </form><div class="strategy-assumptions">At bar <i>, the signal is based on information through bar i−1. The position applies to the close-to-close return after bar i. This conservative one-bar delay avoids trading on a close before it is known. It is not a full execution simulator.</div></section>
      <section class="panel"><div class="panel-heading"><div><h2>Result summary</h2><p>${overall ? `${overall.bars.toLocaleString()} evaluated returns · ${Number(p.costBps).toFixed(1)} bps per side` : 'Study unavailable until the inputs pass validation'}</p></div></div>
        ${errorText ? `<div class="strategy-error">${esc(errorText)}</div>` : `<div class="strategy-stat-grid">${stat('NET TOTAL RETURN', percentReturn(overall.totalReturn), 'after estimated turnover costs', overall.totalReturn >= 0 ? 'positive' : 'negative')}${stat('CAGR', percentReturn(overall.cagr), `${p.periodsPerYear} bars per year`)}${stat('MAX DRAWDOWN', percentReturn(overall.maxDrawdown), 'close-only equity curve', 'negative')}${stat('BUY & HOLD', percentReturn(overall.benchmarkReturn), 'same evaluated date range')}${stat('MARKET EXPOSURE', percentReturn(overall.exposure), 'fraction of bars invested')}${stat('WIN BARS', percentReturn(overall.winBars), 'positive net return bars')}</div>${strategyEquitySvg(result.records)}<div class="strategy-chart-caption"><span>Strategy equity, rebased to 1.00</span><button class="text-button" data-action="strategy-save-run">Save summary locally</button></div>`}</section>
    </div>
    ${!result.error ? `<section class="panel strategy-split-panel"><div class="panel-heading"><div><h2>Chronological split</h2><p>No shuffle: first ${p.splitPct}% of evaluated bars in-sample; remaining bars out-of-sample</p></div></div><div class="strategy-split-grid">${splitStats('In-sample', result.inSample)}${splitStats('Out-of-sample', result.outOfSample)}</div><div class="strategy-assumptions">The rule has no fitted weights. The split is a reporting check only; it does not establish predictive power or protect against selection bias.</div></section>` : ''}
    <section class="panel strategy-history"><div class="panel-heading"><div><h2>Saved study summaries</h2><p>Browser-local settings and summary metrics only; raw CSV rows are never persisted.</p></div></div><div class="table-wrap"><table><thead><tr><th>SAVED</th><th>DATASET</th><th>SMA FAST / SLOW</th><th>OUT-OF-SAMPLE RETURN</th><th>MAX DRAWDOWN</th></tr></thead><tbody>${history}</tbody></table></div></section>
    <div class="strategy-disclaimer">Research tool only. Results depend on the uploaded dataset, bar frequency, timing assumptions, costs, survivorship, corporate actions, and data quality. No vendor indicator or strategy has been copied. No profitability or investment edge is established.</div>`;
}

function renderWatchlists() {
  const rows = state.watchlist.map(ticker => {
    const item = screenerRows.find(r => r.ticker === ticker) || { name: `${ticker} sample security`, price: underlying(ticker), change: 0.32, volume: '—' };
    return `<tr><td>${tickerLink(ticker)}</td><td>${item.name}</td><td>${money(item.price)}</td><td>${changeText(item.change)}</td><td>${item.volume}</td><td><button class="text-button" data-symbol="${ticker}">Research →</button></td><td><button class="tiny-action remove-action" data-action="watch-remove" data-ticker="${ticker}" title="Remove">×</button></td></tr>`;
  }).join('');
  return `${pageHeading('LOCAL WORKSPACE', 'My watchlists', 'Manage a browser-local list of tickers. It is not synced to an account or another device.', '<button class="button secondary" data-view="screener">Browse screener</button>')}
    <div class="watchlist-summary"><div><span class="watchlist-count">${state.watchlist.length}</span><div><b>Market watch</b><small>Default list · saved in this browser only</small></div></div><form id="watch-form" class="watch-add-form"><input name="ticker" maxlength="10" placeholder="Add ticker" aria-label="Ticker to add" required/><button class="button primary">＋ Add</button></form></div>
    ${panel('Symbols', 'Sample quotes shown for layout demonstration', `<div class="table-wrap"><table class="data-table"><thead><tr><th>TICKER</th><th>COMPANY</th><th>LAST</th><th>DAY</th><th>VOLUME</th><th></th><th></th></tr></thead><tbody>${rows || `<tr><td colspan="7">${tableEmpty('Use the add field to start your watchlist.')}</td></tr>`}</tbody></table></div><div class="table-bottom"><span>Stored in local browser storage</span><span>Prices and changes are synthetic</span></div>`)}`;
}

function renderAlerts() {
  const form = state.showAlertForm ? `<form class="alert-form" id="alert-form"><div class="form-heading"><div><b>Create a local alert rule</b><small>Rules are saved in this browser and are not monitored in real time.</small></div><button type="button" class="icon-button" data-action="close-alert-form">×</button></div><div class="form-grid"><label class="field-label">TICKER<input name="ticker" maxlength="10" placeholder="SPY" required /></label><label class="field-label">WHEN<select name="condition"><option value="premium">Option premium exceeds</option><option value="change">Daily move exceeds</option></select></label><label class="field-label">THRESHOLD<input name="threshold" type="number" min="1" step="1" value="50000" required /></label><label class="field-label">OPTION TYPE<select name="type"><option value="all">Calls or puts</option><option value="call">Calls</option><option value="put">Puts</option></select></label></div><div class="form-actions"><span class="small-muted">Notification: local demo only</span><button class="button primary">Save rule</button></div></form>` : '';
  return `${pageHeading('PERSONAL WORKSPACE', 'Alert rules', 'Create local rule examples and see simulated matches. No push, email, or server-side monitoring is active.', `<button class="button primary" data-action="new-alert">＋ New rule</button>`)}
    ${form}<div class="flow-summary-grid">${statCard('ACTIVE RULES', state.alerts.length, 'stored locally', 0.27, '♧')}${statCard('SAMPLE MATCHES', '—', 'no event evaluation', 0, '◉')}${statCard('DELIVERY', 'LOCAL', 'no notifications', 0, '⌁')}${statCard('RULE STATUS', 'DEMO', 'not server-enforced', 0, '⚑')}</div>
    ${panel('Your rules', 'Alert definitions saved on this device', `<div class="alert-rule-list">${state.alerts.map((a, i) => `<div class="alert-rule"><div class="alert-rule-icon">♧</div><div class="alert-rule-main"><b>${esc(a.ticker)} <span>${a.condition === 'premium' ? `premium > ${money(Number(a.threshold), true)}` : `daily move > ${Number(a.threshold).toFixed(1)}%`}</span></b><small>${a.type === 'all' ? 'Calls and puts' : `${a.type.toUpperCase()} only`} · Local rule · Created ${esc(a.created)}</small></div><div class="alert-rule-status">${i === 0 ? label('SIMULATED MATCH', 'orange') : label('ARMED · LOCAL', 'muted-badge')}</div><button class="tiny-action remove-action" data-action="alert-remove" data-index="${i}">×</button></div>`).join('') || tableEmpty('No rules yet. Create one to see the local rule workflow.')}</div><div class="table-bottom"><span>Local rules are not evaluated against live events.</span><button class="text-button" data-action="new-alert">＋ Add a rule</button></div>`)}`;
}

function payoffValues() {
  const p = state.payoff, multiplier = 100 * Number(p.contracts || 1), values = [];
  for (let i = 0; i < 15; i++) {
    const price = Number(p.spot) * (0.8 + i * 0.03);
    const intrinsic = p.type === 'call' ? Math.max(0, price - Number(p.strike)) : Math.max(0, Number(p.strike) - price);
    const long = (intrinsic - Number(p.premium)) * multiplier;
    values.push(Math.round(p.side === 'long' ? long : -long));
  }
  return values;
}
function renderTools() {
  const p = state.payoff, premiumCost = Number(p.premium) * Number(p.contracts) * 100, breakeven = Number(p.strike) + (p.type === 'call' ? 1 : -1) * Number(p.premium);
  const maxLossLabel = p.side === 'long' ? money(premiumCost) : p.type === 'call' ? 'Unlimited' : money(Math.max(0, (Number(p.strike) - Number(p.premium)) * Number(p.contracts) * 100));
  const maxProfitLabel = p.side === 'short' ? money(premiumCost) : p.type === 'call' ? 'Unlimited' : money(Math.max(0, (Number(p.strike) - Number(p.premium)) * Number(p.contracts) * 100));
  const vals = payoffValues();
  return `${pageHeading('WORKSPACE TOOLS', 'Options tools', 'Simple local payoff calculator and saved-flow journal. Prices are illustrative; this is not a pricing model.', '<button class="button secondary" data-view="optionlab">Open multi-leg option lab</button><button class="button secondary" data-view="flow">Find a sample trade</button>')}
    <div class="tool-cards"><div class="tool-card calculator-card"><div class="tool-card-heading"><div><span class="eyebrow">STRATEGY BUILDER</span><h2>Payoff calculator</h2><p>Single long or short call/put at expiration</p></div><span class="tool-icon">⌗</span></div><form id="payoff-form" class="calculator-form"><label class="field-label">UNDERLYING<input name="spot" type="number" step="0.01" value="${p.spot}" /></label><label class="field-label">OPTION TYPE<select name="type"><option value="call" ${p.type === 'call' ? 'selected' : ''}>Call</option><option value="put" ${p.type === 'put' ? 'selected' : ''}>Put</option></select></label><label class="field-label">POSITION<select name="side"><option value="long" ${p.side === 'long' ? 'selected' : ''}>Long</option><option value="short" ${p.side === 'short' ? 'selected' : ''}>Short</option></select></label><label class="field-label">STRIKE<input name="strike" type="number" step="0.5" value="${p.strike}" /></label><label class="field-label">PREMIUM<input name="premium" type="number" step="0.01" value="${p.premium}" /></label><label class="field-label">CONTRACTS<input name="contracts" type="number" min="1" step="1" value="${p.contracts}" /></label><button class="button primary">Update payoff</button></form><div class="payoff-summary"><div><span>MAX LOSS</span><b class="negative">${maxLossLabel}</b></div><div><span>MAX PROFIT</span><b class="positive">${maxProfitLabel}</b></div><div><span>BREAKEVEN</span><b>${money(breakeven)}</b></div></div>${lineChart([{ values: vals, color: '#42d6ab', fill: true }], { width: 650, height: 195, axis: '$' })}<div class="chart-footnote">Expiration-only intrinsic value sketch; excludes fees, early exercise, and volatility/time-value changes.</div></div>
    <div class="tool-side">${panel('Saved flow journal', 'Your saved local sample trades', `<div class="saved-list">${flowTrades.filter(r => state.savedTrades.includes(r.id)).map(r => `<div class="saved-item"><div>${tickerLink(r.ticker)}<span class="option-type ${r.type === 'CALL' ? 'call' : 'put'}">${r.type}</span></div><b>${money(r.premium, true)}</b><small>${r.expiry} ${r.strike} · ${r.side} estimate</small></div>`).join('') || '<div class="empty-state compact"><span>☆</span><b>No saved trades</b><p>Use the star in Options flow to keep a local sample.</p></div>'}<button class="button secondary full-button" data-view="flow">Browse flow feed →</button></div>`, '')}${panel('Other tools', 'Prototype workflow links', `<div class="other-tool-list"><button data-view="optionlab"><span>⌗</span><div><b>Multi-leg option lab</b><small>Model user-entered expiration payoff</small></div>→</button><button data-view="screener"><span>⌕</span><div><b>Stock screener</b><small>Filter a sample symbol universe</small></div>→</button><button data-view="calendar"><span>▦</span><div><b>Event calendar</b><small>Review upcoming catalysts</small></div>→</button><button data-view="gex"><span>◈</span><div><b>GEX explorer</b><small>Inspect sample strike exposure</small></div>→</button></div>`, '')}</div></div>`;
}

function parseOptionStrategyLegs(text) {
  const lines = String(text).split(/\r?\n/).map((line, index) => ({ line: line.trim(), row: index + 1 })).filter(item => item.line);
  if (lines[0]?.line.split(',')[0].trim().toLowerCase() === 'type') lines.shift();
  if (!lines.length) throw new Error('Enter at least one option leg.');
  if (lines.length > 8) throw new Error('Use no more than eight option legs in one profile.');
  return lines.map(({ line, row }) => {
    const cells = line.split(',').map(value => value.trim());
    if (cells.length < 5 || cells.length > 7) throw new Error(`Line ${row}: use type, side, strike, premium, contracts, optional multiplier, and optional IV percent.`);
    const [type, side, strikeText, premiumText, contractsText, multiplierText, ivText] = cells;
    const leg = {
      type: type.toLowerCase(),
      side: side.toLowerCase(),
      strike: Number(strikeText),
      premium: Number(premiumText),
      contracts: Number(contractsText),
      multiplier: multiplierText === undefined || multiplierText === '' ? 100 : Number(multiplierText),
      ivPct: ivText === undefined || ivText === '' ? null : Number(ivText),
    };
    if (!['call', 'put'].includes(leg.type)) throw new Error(`Line ${row}: type must be call or put.`);
    if (!['long', 'short'].includes(leg.side)) throw new Error(`Line ${row}: side must be long or short.`);
    if (!Number.isFinite(leg.strike) || leg.strike <= 0 || leg.strike > 1e6 || !Number.isFinite(leg.premium) || leg.premium < 0 || leg.premium > 1e6) throw new Error(`Line ${row}: strike must be between 0 and 1,000,000; premium must be 0 to 1,000,000.`);
    if (!Number.isSafeInteger(leg.contracts) || leg.contracts < 1 || leg.contracts > 10000 || !Number.isSafeInteger(leg.multiplier) || leg.multiplier < 1 || leg.multiplier > 10000) throw new Error(`Line ${row}: contracts and multiplier must be whole numbers from 1 to 10,000.`);
    if (leg.ivPct !== null && (!Number.isFinite(leg.ivPct) || leg.ivPct < 0.1 || leg.ivPct > 500)) throw new Error(`Line ${row}: IV percent must be blank or between 0.1 and 500.`);
    return leg;
  });
}

function optionStrategyPnlAt(legs, underlyingPrice) {
  return legs.reduce((total, leg) => {
    const intrinsic = leg.type === 'call' ? Math.max(0, underlyingPrice - leg.strike) : Math.max(0, leg.strike - underlyingPrice);
    const direction = leg.side === 'long' ? 1 : -1;
    return total + direction * (intrinsic - leg.premium) * leg.contracts * leg.multiplier;
  }, 0);
}

function optionStrategyStats(legs) {
  const knots = [...new Set([0, ...legs.map(leg => leg.strike)])].sort((a, b) => a - b);
  const values = knots.map(price => optionStrategyPnlAt(legs, price));
  const tailSlope = legs.reduce((sum, leg) => leg.type === 'call' ? sum + (leg.side === 'long' ? 1 : -1) * leg.contracts * leg.multiplier : sum, 0);
  const breakEvens = [];
  const breakEvenIntervals = [];
  const isZero = value => Math.abs(value) < 1e-8;
  const addBreakEven = price => {
    if (Number.isFinite(price) && price >= 0 && !breakEvens.some(value => Math.abs(value - price) < 1e-7)) breakEvens.push(price);
  };
  knots.forEach((price, index) => {
    if (isZero(values[index])) addBreakEven(price);
    if (index < knots.length - 1 && isZero(values[index]) && isZero(values[index + 1])) {
      breakEvenIntervals.push({ from: price, to: knots[index + 1] });
    } else if (index < knots.length - 1 && values[index] * values[index + 1] < 0) {
      addBreakEven(price + (knots[index + 1] - price) * (-values[index]) / (values[index + 1] - values[index]));
    }
  });
  const lastKnot = knots[knots.length - 1], lastValue = values[values.length - 1];
  if (Math.abs(tailSlope) > 1e-10) {
    const tailRoot = lastKnot - lastValue / tailSlope;
    if (tailRoot > lastKnot + 1e-7) addBreakEven(tailRoot);
  } else if (isZero(lastValue)) {
    breakEvenIntervals.push({ from: lastKnot, to: null });
  }
  breakEvenIntervals.sort((a, b) => a.from - b.from);
  const mergedBreakEvenIntervals = breakEvenIntervals.reduce((merged, interval) => {
    const previous = merged[merged.length - 1];
    if (previous && (previous.to === null || interval.from <= previous.to + 1e-7)) {
      previous.to = previous.to === null || interval.to === null ? null : Math.max(previous.to, interval.to);
    } else merged.push({ ...interval });
    return merged;
  }, []);
  const isolatedBreakEvens = breakEvens.filter(price => !mergedBreakEvenIntervals.some(interval => price >= interval.from - 1e-7 && (interval.to === null || price <= interval.to + 1e-7)));
  breakEvens.sort((a, b) => a - b);
  return {
    minPnl: Math.min(...values),
    maxPnl: Math.max(...values),
    unboundedLoss: tailSlope < -1e-10,
    unboundedProfit: tailSlope > 1e-10,
    breakEvens: isolatedBreakEvens,
    breakEvenIntervals: mergedBreakEvenIntervals,
    netDebit: legs.reduce((sum, leg) => sum + (leg.side === 'long' ? 1 : -1) * leg.premium * leg.contracts * leg.multiplier, 0),
  };
}

function standardNormalCdf(value) {
  const absolute = Math.abs(value);
  if (absolute >= 8) return value < 0 ? 0 : 1;
  const t = 1 / (1 + 0.2316419 * absolute);
  const density = Math.exp(-0.5 * absolute * absolute) / Math.sqrt(2 * Math.PI);
  const tail = density * t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  return value < 0 ? tail : 1 - tail;
}

function blackScholesEuropean(spot, strike, daysToExpiration, ivPct, riskFreeRatePct, dividendYieldPct, type) {
  const years = daysToExpiration / 365;
  const sigma = ivPct / 100;
  const rate = riskFreeRatePct / 100;
  const dividendYield = dividendYieldPct / 100;
  const rootTime = Math.sqrt(years);
  const d1 = (Math.log(spot / strike) + (rate - dividendYield + 0.5 * sigma * sigma) * years) / (sigma * rootTime);
  const d2 = d1 - sigma * rootTime;
  const density = Math.exp(-0.5 * d1 * d1) / Math.sqrt(2 * Math.PI);
  const discountedSpot = spot * Math.exp(-dividendYield * years);
  const discountedStrike = strike * Math.exp(-rate * years);
  const call = type === 'call';
  const theoreticalPrice = call
    ? discountedSpot * standardNormalCdf(d1) - discountedStrike * standardNormalCdf(d2)
    : discountedStrike * standardNormalCdf(-d2) - discountedSpot * standardNormalCdf(-d1);
  const delta = Math.exp(-dividendYield * years) * (call ? standardNormalCdf(d1) : standardNormalCdf(d1) - 1);
  const gamma = Math.exp(-dividendYield * years) * density / (spot * sigma * rootTime);
  const vegaPerPctPoint = discountedSpot * density * rootTime / 100;
  const thetaAnnual = call
    ? -(discountedSpot * density * sigma) / (2 * rootTime) + dividendYield * discountedSpot * standardNormalCdf(d1) - rate * discountedStrike * standardNormalCdf(d2)
    : -(discountedSpot * density * sigma) / (2 * rootTime) - dividendYield * discountedSpot * standardNormalCdf(-d1) + rate * discountedStrike * standardNormalCdf(-d2);
  const rhoPerPctPoint = call
    ? years * discountedStrike * standardNormalCdf(d2) / 100
    : -years * discountedStrike * standardNormalCdf(-d2) / 100;
  return { theoreticalPrice: Math.max(0, theoreticalPrice), delta, gamma, vegaPerPctPoint, thetaPerDay: thetaAnnual / 365, rhoPerPctPoint };
}

function crrAmericanOption(spot, strike, daysToExpiration, ivPct, riskFreeRatePct, dividendYieldPct, type, steps = 200) {
  const numericInputs = [spot, strike, daysToExpiration, ivPct, riskFreeRatePct, dividendYieldPct];
  if (!numericInputs.every(Number.isFinite) || spot <= 0 || strike <= 0 || daysToExpiration < 0 || ivPct <= 0) {
    throw new RangeError('CRR pricing needs positive spot, strike, and IV plus finite rates and nonnegative days to expiration.');
  }
  if (type !== 'call' && type !== 'put') throw new RangeError('Option type must be call or put.');
  if (!Number.isInteger(steps) || steps < 1 || steps > 300) throw new RangeError('CRR tree steps must be a whole number from 1 to 300.');
  const intrinsicValue = value => type === 'call' ? Math.max(value - strike, 0) : Math.max(strike - value, 0);
  if (daysToExpiration === 0) return intrinsicValue(spot);

  const years = daysToExpiration / 365;
  const sigma = ivPct / 100;
  const rate = riskFreeRatePct / 100;
  const dividendYield = dividendYieldPct / 100;
  const dt = years / steps;
  const stepLog = sigma * Math.sqrt(dt);
  const up = Math.exp(stepLog);
  const down = Math.exp(-stepLog);
  const forwardGrowth = Math.exp((rate - dividendYield) * dt);
  const probabilityUp = (forwardGrowth - down) / (up - down);
  if (!Number.isFinite(probabilityUp) || probabilityUp < 0 || probabilityUp > 1) {
    throw new RangeError('CRR risk-neutral probability is outside [0, 1]; adjust the rate, yield, volatility, time, or tree steps.');
  }
  const discount = Math.exp(-rate * dt);
  if (!Number.isFinite(discount)) throw new RangeError('CRR discount factor is outside the numeric range.');

  let values = Array.from({ length: steps + 1 }, (_, upMoves) => {
    const terminalSpot = spot * Math.exp((2 * upMoves - steps) * stepLog);
    return intrinsicValue(terminalSpot);
  });
  for (let timeStep = steps - 1; timeStep >= 0; timeStep -= 1) {
    const earlierValues = new Array(timeStep + 1);
    for (let upMoves = 0; upMoves <= timeStep; upMoves += 1) {
      const nodeSpot = spot * Math.exp((2 * upMoves - timeStep) * stepLog);
      const continuation = discount * (probabilityUp * values[upMoves + 1] + (1 - probabilityUp) * values[upMoves]);
      earlierValues[upMoves] = Math.max(continuation, intrinsicValue(nodeSpot));
    }
    values = earlierValues;
  }
  if (!Number.isFinite(values[0])) throw new RangeError('CRR result is outside the numeric range.');
  return values[0];
}

function americanCrrGreeks(spot, strike, daysToExpiration, ivPct, riskFreeRatePct, dividendYieldPct, type, steps, basePrice) {
  const priceAt = overrides => crrAmericanOption(
    overrides.spot ?? spot,
    strike,
    overrides.daysToExpiration ?? daysToExpiration,
    overrides.ivPct ?? ivPct,
    overrides.riskFreeRatePct ?? riskFreeRatePct,
    dividendYieldPct,
    type,
    steps,
  );
  const spotStep = Math.min(Math.max(spot * 0.001, 0.001), spot * 0.25);
  const priceSpotUp = priceAt({ spot: spot + spotStep });
  const priceSpotDown = priceAt({ spot: spot - spotStep });
  const delta = (priceSpotUp - priceSpotDown) / (2 * spotStep);
  const gamma = (priceSpotUp - 2 * basePrice + priceSpotDown) / (spotStep * spotStep);

  const oneSidedOrCentral = (plusValue, minusValue, step, key) => {
    let plusPrice = null;
    let minusPrice = null;
    try { plusPrice = priceAt({ [key]: plusValue }); } catch {}
    try { minusPrice = priceAt({ [key]: minusValue }); } catch {}
    if (plusPrice !== null && minusPrice !== null) return (plusPrice - minusPrice) / (2 * step);
    if (plusPrice !== null) return (plusPrice - basePrice) / step;
    if (minusPrice !== null) return (basePrice - minusPrice) / step;
    throw new RangeError(`Unable to estimate the American-model ${key} sensitivity within the CRR probability range.`);
  };
  const ivStep = Math.min(0.1, ivPct / 2);
  const vegaPerPctPoint = oneSidedOrCentral(ivPct + ivStep, ivPct - ivStep, ivStep, 'ivPct');
  const rateStep = 0.01;
  const rhoPerPctPoint = oneSidedOrCentral(riskFreeRatePct + rateStep, riskFreeRatePct - rateStep, rateStep, 'riskFreeRatePct');
  const thetaStepDays = Math.min(1, daysToExpiration);
  const priceAfterOneDay = priceAt({ daysToExpiration: daysToExpiration - thetaStepDays });
  return { delta, gamma, vegaPerPctPoint, thetaPerDay: (priceAfterOneDay - basePrice) / thetaStepDays, rhoPerPctPoint };
}

function optionScenarioModel(spot, strike, daysToExpiration, ivPct, settings, type) {
  if (settings.exerciseStyle !== 'american') {
    return blackScholesEuropean(spot, strike, daysToExpiration, ivPct, settings.riskFreeRatePct, settings.dividendYieldPct, type);
  }
  const steps = settings.treeSteps ?? 200;
  const theoreticalPrice = crrAmericanOption(spot, strike, daysToExpiration, ivPct, settings.riskFreeRatePct, settings.dividendYieldPct, type, steps);
  return {
    theoreticalPrice,
    ...americanCrrGreeks(spot, strike, daysToExpiration, ivPct, settings.riskFreeRatePct, settings.dividendYieldPct, type, steps, theoreticalPrice),
  };
}

function buildOptionStrategyModel(legs, settings) {
  const modelRows = legs.map(leg => {
    const ivPct = leg.ivPct ?? settings.volatilityPct;
    const model = optionScenarioModel(settings.spot, leg.strike, settings.daysToExpiration, ivPct, settings, leg.type);
    const position = (leg.side === 'long' ? 1 : -1) * leg.contracts * leg.multiplier;
    return { ...leg, ivPct, ...model, signedModelValue: model.theoreticalPrice * position, modeledPnlVsEntry: (model.theoreticalPrice - leg.premium) * position, positionDelta: model.delta * position, positionGamma: model.gamma * position, positionVega: model.vegaPerPctPoint * position, positionTheta: model.thetaPerDay * position, positionRho: model.rhoPerPctPoint * position };
  });
  const sum = key => modelRows.reduce((total, row) => total + row[key], 0);
  return {
    rows: modelRows,
    netTheoreticalValue: sum('signedModelValue'),
    modeledPnlVsEntry: sum('modeledPnlVsEntry'),
    netDelta: sum('positionDelta'),
    netGamma: sum('positionGamma'),
    netVegaPerPctPoint: sum('positionVega'),
    netThetaPerDay: sum('positionTheta'),
    netRhoPerPctPoint: sum('positionRho'),
  };
}

function buildOptionStrategySensitivity(legs, settings) {
  const spotChangesPct = [-10, -5, 0, 5, 10];
  const volatilityScenarios = [
    { label: '80% of selected IV', multiplier: 0.8 },
    { label: 'Base selected IV', multiplier: 1 },
    { label: '120% of selected IV', multiplier: 1.2 },
  ];
  return {
    spotChangesPct,
    rows: volatilityScenarios.map(scenario => ({
      ...scenario,
      cells: spotChangesPct.map(spotChangePct => {
        const spot = settings.spot * (1 + spotChangePct / 100);
        let netTheoreticalValue = 0, modeledPnlVsEntry = 0;
        for (const leg of legs) {
          const ivPct = (leg.ivPct ?? settings.volatilityPct) * scenario.multiplier;
          const theoreticalPrice = settings.exerciseStyle === 'american'
            ? crrAmericanOption(spot, leg.strike, settings.daysToExpiration, ivPct, settings.riskFreeRatePct, settings.dividendYieldPct, leg.type, settings.treeSteps ?? 200)
            : blackScholesEuropean(spot, leg.strike, settings.daysToExpiration, ivPct, settings.riskFreeRatePct, settings.dividendYieldPct, leg.type).theoreticalPrice;
          const position = (leg.side === 'long' ? 1 : -1) * leg.contracts * leg.multiplier;
          netTheoreticalValue += theoreticalPrice * position;
          modeledPnlVsEntry += (theoreticalPrice - leg.premium) * position;
        }
        return { spot, spotChangePct, netTheoreticalValue, modeledPnlVsEntry };
      }),
    })),
  };
}

function formatOptionGreek(value) {
  if (!Number.isFinite(value)) return '—';
  const sign = value < 0 ? '−' : '+';
  return sign + Math.abs(value).toLocaleString('en-US', { maximumFractionDigits: 4 });
}

function renderOptionStrategyLab() {
  const model = state.optionLab;
  const americanModel = model.exerciseStyle === 'american';
  const legs = model.legs;
  const stats = optionStrategyStats(legs);
  const modelStats = buildOptionStrategyModel(legs, model);
  const sensitivity = buildOptionStrategySensitivity(legs, model);
  const maxStrike = Math.max(...legs.map(leg => leg.strike));
  const chartHigh = Math.max(model.spot * 1.5, maxStrike * 1.25, model.spot + 10, 10);
  const values = Array.from({ length: 61 }, (_, index) => Math.round(optionStrategyPnlAt(legs, chartHigh * index / 60)));
  const xLabels = Array.from({ length: 5 }, (_, index) => money(chartHigh * index / 4, true));
  const maxLossLabel = stats.unboundedLoss ? 'Unlimited' : money(Math.max(0, -stats.minPnl));
  const maxProfitLabel = stats.unboundedProfit ? 'Unlimited' : money(stats.maxPnl);
  const netEntryLabel = `${stats.netDebit >= 0 ? 'DEBIT' : 'CREDIT'} ${money(Math.abs(stats.netDebit))}`;
  const breakevenItems = [
    ...stats.breakEvens.map(price => ({ from: price, label: money(price) })),
    ...stats.breakEvenIntervals.map(({ from, to }) => ({ from, label: to === null ? `≥ ${money(from)}` : from === 0 ? `≤ ${money(to)}` : `${money(from)}–${money(to)}` })),
  ].sort((a, b) => a.from - b.from);
  const breakevenLabel = breakevenItems.length ? breakevenItems.map(item => item.label).join(' · ') : 'None';
  const legRows = legs.map((leg, index) => `<tr><td>${index + 1}</td><td>${leg.side.toUpperCase()} ${leg.type.toUpperCase()}</td><td>${money(leg.strike)}</td><td>${money(leg.premium)}</td><td>${integer(leg.contracts)}</td><td>${integer(leg.multiplier)}</td></tr>`).join('');
  const modelRows = modelStats.rows.map((row, index) => `<tr><td>${index + 1}</td><td>${row.side.toUpperCase()} ${row.type.toUpperCase()}</td><td>${money(row.strike)}</td><td>${money(row.premium)}</td><td>${row.ivPct.toFixed(2)}%</td><td>${money(row.theoreticalPrice)}</td><td class="${signedClass(row.modeledPnlVsEntry)}">${money(row.modeledPnlVsEntry)}</td></tr>`).join('');
  const sensitivityHeaders = sensitivity.spotChangesPct.map(change => `<th>${change === 0 ? 'CURRENT' : `${change > 0 ? '+' : '−'}${Math.abs(change)}%`}</th>`).join('');
  const sensitivityRows = sensitivity.rows.map(row => `<tr><th scope="row">${row.label}</th>${row.cells.map(cell => `<td class="${signedClass(cell.modeledPnlVsEntry)}">${money(cell.modeledPnlVsEntry)}</td>`).join('')}</tr>`).join('');
  const greekCard = (label, value) => `<div><span>${americanModel ? `${label} · FINITE DIFF` : label}</span><b class="${signedClass(value)}">${formatOptionGreek(value)}</b></div>`;
  const modelPanel = `<div class="optionlab-model-panel"><div class="panel-heading"><div><h3>${americanModel ? 'American CRR binomial scenario' : 'European Black–Scholes scenario'}</h3><p>${americanModel ? `CRR tree · ${model.treeSteps} steps` : 'Black–Scholes'} · ${model.daysToExpiration} calendar days · ${model.riskFreeRatePct}% rate · ${model.dividendYieldPct}% continuous yield</p></div></div>
      <div class="optionlab-summary optionlab-greeks"><div><span>NET MODEL VALUE</span><b class="${signedClass(modelStats.netTheoreticalValue)}">${money(modelStats.netTheoreticalValue)}</b></div><div><span>MODEL P/L VS ENTRY</span><b class="${signedClass(modelStats.modeledPnlVsEntry)}">${money(modelStats.modeledPnlVsEntry)}</b></div>${greekCard('NET DELTA · SHARES / $1', modelStats.netDelta)}${greekCard('NET GAMMA · DELTA / $1', modelStats.netGamma)}${greekCard('NET VEGA · PER IV POINT', modelStats.netVegaPerPctPoint)}${greekCard('NET THETA · PER DAY', modelStats.netThetaPerDay)}${greekCard('NET RHO · PER RATE POINT', modelStats.netRhoPerPctPoint)}</div>
      <div class="table-wrap optionlab-leg-table"><table class="data-table"><thead><tr><th>#</th><th>POSITION</th><th>STRIKE</th><th>ENTRY / SHARE</th><th>MODEL IV</th><th>MODEL VALUE / SHARE</th><th>MODEL P/L VS ENTRY</th></tr></thead><tbody>${modelRows}</tbody></table></div>
      <div class="panel-heading"><div><h3>Scenario sensitivity · model P/L vs entry</h3><p>Spot changes across columns; each selected leg IV is scaled by the row.</p></div></div>
      <div class="table-wrap optionlab-sensitivity"><table class="data-table optionlab-sensitivity-table" aria-label="${americanModel ? 'American CRR' : 'European Black–Scholes'} option model P/L sensitivity by spot and implied volatility"><thead><tr><th>IV SCENARIO / SPOT</th>${sensitivityHeaders}</tr></thead><tbody>${sensitivityRows}</tbody></table></div>
      <div class="chart-footnote">Underlying scenarios are −10%, −5%, unchanged, +5%, and +10%. IV scenarios are 80%, 100%, and 120% of each leg’s selected IV. DTE, rates, yield, and entry premiums stay fixed. This is an assumption sensitivity, not a forecast, quote, or probability.</div>
      <div class="chart-footnote">${americanModel ? `American exercise is checked at each CRR lattice node; finite-difference Greeks are approximate at ${model.treeSteps} steps.` : 'Model values assume European exercise and use analytic Black–Scholes Greeks.'} IV is row-specific when supplied; otherwise the shared IV applies. This is a theoretical scenario mark, not a quote or probability.</div></div>`;
  return `${pageHeading('INDEPENDENT MODEL · USER-ENTERED INPUTS', 'Option strategy lab', 'Combine up to eight calls and puts into an expiration payoff and choose an independent European Black–Scholes or American CRR pricing scenario. No option chain, live quote, probability, or vendor signal is fetched.', '<button class="button secondary" data-view="coverage">Method notes →</button>')}
    <div class="optionlab-layout">
      <section class="panel optionlab-input"><div class="panel-heading"><div><h2>Strategy inputs</h2><p>A vertical call spread is prefilled; replace it with legs for one underlying and expiration.</p></div></div>
        <form id="option-strategy-form" class="optionlab-form"><label class="field-label">CURRENT UNDERLYING<input name="spot" type="number" min="0.01" max="1000000" step="0.01" value="${model.spot}" required /></label>
          <div class="optionlab-model-inputs"><label class="field-label">DAYS TO EXPIRATION<input name="daysToExpiration" type="number" min="0.01" max="3650" step="0.01" value="${model.daysToExpiration}" required /></label><label class="field-label">SHARED IV (%)<input name="volatilityPct" type="number" min="0.1" max="500" step="0.1" value="${model.volatilityPct}" required /></label><label class="field-label">RISK-FREE RATE (%)<input name="riskFreeRatePct" type="number" min="-100" max="100" step="0.01" value="${model.riskFreeRatePct}" required /></label><label class="field-label">CONTINUOUS YIELD (%)<input name="dividendYieldPct" type="number" min="-100" max="100" step="0.01" value="${model.dividendYieldPct}" required /></label><label class="field-label">EXERCISE MODEL<select name="exerciseStyle"><option value="european" ${americanModel ? '' : 'selected'}>European · Black–Scholes</option><option value="american" ${americanModel ? 'selected' : ''}>American · CRR binomial</option></select></label><label class="field-label">AMERICAN TREE STEPS<input name="treeSteps" type="number" min="25" max="300" step="1" value="${model.treeSteps}" ${americanModel ? 'required' : 'disabled'} /></label></div>
          <small class="optionlab-help">CRR steps are used only for American exercise. The model checks exercise at each tree node and rejects inputs whose risk-neutral step probability is outside [0, 1].</small>
          <label class="field-label">OPTION LEGS · CSV<textarea class="optionlab-legs" name="legs" rows="9" spellcheck="false" aria-describedby="optionlab-format" required>${esc(model.legsText)}</textarea></label>
          <small id="optionlab-format" class="optionlab-help">Columns: type, side, strike, entry premium, contracts, optional multiplier, optional IV percent. The first header line is optional; multiplier defaults to 100 and blank IV uses the shared assumption.</small>
          <button class="button primary">Recalculate payoff and model</button>
          ${model.error ? `<div class="optionlab-error" role="alert">${esc(model.error)}</div>` : ''}
        </form>
      </section>
      <section class="panel optionlab-output"><div class="panel-heading"><div><h2>Expiration profile</h2><p>${model.error ? 'Input rejected; showing the last valid profile.' : 'Piecewise-linear payoff from the submitted legs'}</p></div><span class="small-muted">${legs.length} legs · spot ${money(model.spot)}</span></div>
        <div class="optionlab-summary"><div><span>MAX LOSS</span><b class="negative">${maxLossLabel}</b></div><div><span>MAX PROFIT</span><b class="${signedClass(stats.maxPnl)}">${maxProfitLabel}</b></div><div><span>NET ENTRY</span><b>${netEntryLabel}</b></div><div><span>BREAKEVEN${breakevenItems.length === 1 ? '' : 'S'}</span><b>${breakevenLabel}</b></div></div>
        ${lineChart([{ values, color: '#42d6ab', fill: true }], { width: 740, height: 235, axis: '$', xLabels, ariaLabel: 'User-entered option strategy expiration profit and loss profile' })}
        <div class="chart-footnote">P/L = signed intrinsic value less entry premium × contracts × multiplier. Maximums are exact over nonnegative underlying prices; commissions, taxes, early exercise, assignment, and time value are excluded.</div>
        <div class="table-wrap optionlab-leg-table"><table class="data-table"><thead><tr><th>#</th><th>POSITION</th><th>STRIKE</th><th>PREMIUM / SHARE</th><th>CONTRACTS</th><th>MULTIPLIER</th></tr></thead><tbody>${legRows}</tbody></table></div>
        ${modelPanel}
      </section>
    </div>
    <div class="evidence-callout portfolio-callout"><b>Method boundary</b><span>European scenarios use Black–Scholes; American scenarios use an independently specified CRR binomial tree with early exercise checked at each node. Both use manual assumptions and local calculations. No OptionStrat code, data, or outputs are used; there is no vendor pricing-parity claim, volatility-surface inference, probability estimate, optimizer ranking, or sealed flow score. Expiration payoff remains separate from the theoretical mark.</span><a href="../../research/rea-teardowns/optionstrat/OPTIONSTRAT-LAB-IMPLEMENTATION.md">Review implementation notes →</a> · <a href="https://prd-web.optionseducation.org/advancedconcepts/black-scholes-formula" target="_blank" rel="noreferrer">Options Industry Council: Black–Scholes method ↗</a> · <a href="https://bpb-us-w2.wpmucdn.com/u.osu.edu/dist/7/36891/files/2017/07/CRR79-1yy8av8.pdf" target="_blank" rel="noreferrer">Cox–Ross–Rubinstein paper ↗</a></div>`;
}

function validProfileDate(value) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(`${value}T00:00:00Z`)) && new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) === value;
}

function parseEtClock(value) {
  const match = /^(?:([01]\d|2[0-3])):([0-5]\d)(?::([0-5]\d))?$/.exec(String(value || ''));
  return match ? Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3] || 0) : null;
}

function parseBullflowSourceTimestamp(value) {
  const raw = String(value || '').trim();
  if (!raw) return null;
  let milliseconds = null;
  if (/^\d{10}(?:\.\d+)?$/.test(raw)) milliseconds = Number(raw) * 1000;
  else if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})$/.test(raw)) milliseconds = Date.parse(raw);
  return Number.isFinite(milliseconds) ? new Date(milliseconds) : null;
}

function bullflowTimestampMatchesEt(eventTimestamp, date, timeValue) {
  if (!(eventTimestamp instanceof Date) || !Number.isFinite(eventTimestamp.getTime())) return false;
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  }).formatToParts(eventTimestamp).filter(part => part.type !== 'literal').map(part => [part.type, part.value]));
  const expected = /^\d{4}-\d{2}-\d{2}$/.test(date) && parseEtClock(timeValue) !== null ? timeValue.split(':') : null;
  if (!expected) return false;
  const matches = parts.year === date.slice(0, 4) && parts.month === date.slice(5, 7) && parts.day === date.slice(8, 10)
    && parts.hour === expected[0] && parts.minute === expected[1];
  return matches && (expected.length < 3 || parts.second === expected[2]);
}

function normalizeExecutionSide(value) {
  const side = String(value || '').trim().toLowerCase().replace(/[^a-z]/g, '');
  return ({ ask: 'ASK', atask: 'ASK', aboveask: 'ABOVE_ASK', aa: 'ABOVE_ASK', bid: 'BID', atbid: 'BID', belowbid: 'BELOW_BID', bb: 'BELOW_BID', mid: 'MID', midpoint: 'MID', atmid: 'MID', unknown: 'UNKNOWN', other: 'UNKNOWN' })[side] || null;
}

function parseBullflowActivityCsv(source) {
  if (source.length > 10 * 1024 * 1024) throw new Error('Options activity CSV files must be 10 MiB or smaller.');
  const table = parseCsvRows(source.replace(/^\uFEFF/, ''));
  if (table.length < 2 || table.length > 50001) throw new Error('Use a header and between 1 and 50,000 activity or coverage rows.');
  const header = table[0].map(value => value.trim().toLowerCase().replace(/[^a-z0-9]/g, ''));
  const column = (...aliases) => header.findIndex(name => aliases.includes(name));
  const ix = {
    date: column('date', 'sessiondate'), time: column('timeet', 'executiontimeet'), ticker: column('ticker', 'symbol'),
    contract: column('contract', 'optioncontract'), expiry: column('expiry', 'expiration', 'expirationdate'),
    type: column('type', 'optiontype', 'right'), strike: column('strike', 'strikeprice'),
    size: column('size', 'volume', 'contracts'), premium: column('premium', 'premiumusd', 'totalpremium', 'transactionpremium'),
    side: column('side', 'executionside'), tradeType: column('tradetype', 'tradekind'), oi: column('oi', 'openinterest'),
    available: column('available', 'sessionavailable', 'dataavailable'), cancelled: column('cancelled', 'iscancelled', 'canceled', 'iscanceled'),
    exportComplete: column('exportcomplete', 'querycomplete', 'sessioncomplete'), source: column('source', 'datasource', 'sourcename'),
    tradeId: column('tradeid', 'sourcerecordid', 'recordid', 'id'), sideSource: column('sidesource', 'sideprovenance'),
    sourceTimestamp: column('timestamp', 'sourcetimestamp', 'tradeeventtimestamp'),
  };
  const missing = ['date', 'time', 'ticker', 'contract', 'expiry', 'type', 'strike', 'size', 'premium', 'side', 'tradeType', 'oi'].filter(key => ix[key] < 0);
  if (missing.length) throw new Error(`Missing required columns: ${missing.join(', ')}.`);
  const rows = [], sessions = new Map(), tradeIds = new Set();
  const cell = (cells, key) => String(cells[ix[key]] ?? '').trim();
  const sessionKey = (ticker, date) => `${ticker}|${date}`;
  const sessionFor = (ticker, date) => {
    const key = sessionKey(ticker, date);
    if (!sessions.has(key)) sessions.set(key, { ticker, date, available: true, exportComplete: null, explicitCoverage: false, source: '' });
    return sessions.get(key);
  };
  const number = (raw, name, rowNumber, optional = false) => {
    if (!raw && optional) return null;
    const value = Number(raw.replace(/[$,%\s,]/g, ''));
    if (!raw || !Number.isFinite(value)) throw new Error(`Row ${rowNumber}: ${name} must be a finite number.`);
    return value;
  };
  const bool = raw => {
    const value = String(raw || '').trim().toLowerCase();
    if (['true', '1', 'yes', 'y'].includes(value)) return true;
    if (['false', '0', 'no', 'n'].includes(value)) return false;
    return null;
  };
  for (let i = 1; i < table.length; i++) {
    const cells = table[i], rowNumber = i + 1;
    const date = cell(cells, 'date'), ticker = normalizeTicker(cell(cells, 'ticker'));
    if (!validProfileDate(date) || !ticker) throw new Error(`Row ${rowNumber}: Date must be YYYY-MM-DD and Ticker must be valid.`);
    const contract = cell(cells, 'contract');
    const sizeRaw = cell(cells, 'size');
    const size = sizeRaw ? number(sizeRaw, 'Size', rowNumber) : 0;
    const isCoverageMarker = !contract && size === 0;
    const availabilityRaw = ix.available < 0 ? '' : String(cells[ix.available] ?? '').trim();
    if (isCoverageMarker) {
      const marker = bool(availabilityRaw);
      if (marker === null) throw new Error(`Row ${rowNumber}: a zero-activity coverage row needs Available=true or false.`);
      const completeRaw = ix.exportComplete < 0 ? '' : cell(cells, 'exportComplete');
      const exportComplete = completeRaw ? bool(completeRaw) : null;
      if (completeRaw && exportComplete === null) throw new Error(`Row ${rowNumber}: ExportComplete must be true or false when provided.`);
      if (!marker && exportComplete === true) throw new Error(`Row ${rowNumber}: an unavailable session cannot be marked ExportComplete=true.`);
      const session = sessionFor(ticker, date);
      if (session.explicitCoverage) throw new Error(`Row ${rowNumber}: duplicate coverage declaration for ${ticker} ${date}.`);
      if (session.hasPrints && !marker) throw new Error(`Row ${rowNumber}: a session with print rows cannot be marked unavailable.`);
      session.available = marker;
      session.exportComplete = exportComplete;
      session.explicitCoverage = true;
      session.source = cell(cells, 'source') || session.source;
      continue;
    }
    if (!contract || contract.length > 100 || !Number.isSafeInteger(size) || size < 1 || size > 1e7) throw new Error(`Row ${rowNumber}: a print needs a contract and an integer Size from 1 to 10,000,000.`);
    if (availabilityRaw && bool(availabilityRaw) !== true) throw new Error(`Row ${rowNumber}: a print row must use Available=true.`);
    if (ix.exportComplete >= 0 && cell(cells, 'exportComplete')) throw new Error(`Row ${rowNumber}: declare ExportComplete on a coverage-only row, not a print row.`);
    const timeSeconds = parseEtClock(cell(cells, 'time'));
    const typeRaw = cell(cells, 'type').toUpperCase();
    const type = typeRaw === 'C' ? 'CALL' : typeRaw === 'P' ? 'PUT' : typeRaw;
    const side = normalizeExecutionSide(cell(cells, 'side'));
    const cancelledRaw = ix.cancelled < 0 ? '' : cell(cells, 'cancelled');
    const cancelled = cancelledRaw ? bool(cancelledRaw) : (ix.cancelled < 0 ? false : null);
    const strike = number(cell(cells, 'strike'), 'Strike', rowNumber);
    const premium = number(cell(cells, 'premium'), 'Premium', rowNumber);
    const openInterest = number(cell(cells, 'oi'), 'OpenInterest', rowNumber, true);
    const expiry = cell(cells, 'expiry');
    const source = cell(cells, 'source');
    const tradeId = cell(cells, 'tradeId');
    const sourceTimestampRaw = ix.sourceTimestamp < 0 ? '' : cell(cells, 'sourceTimestamp');
    const sourceTimestamp = sourceTimestampRaw ? parseBullflowSourceTimestamp(sourceTimestampRaw) : null;
    const sideSource = (cell(cells, 'sideSource') || 'unknown').toUpperCase().replace(/[^A-Z]/g, '');
    const sideSourceValue = ({ VENDOR: 'VENDOR', USER: 'USER', INFERRED: 'INFERRED', SYNTHETIC: 'SYNTHETIC', UNKNOWN: 'UNKNOWN' })[sideSource];
    if (timeSeconds === null) throw new Error(`Row ${rowNumber}: TimeET must use HH:MM or HH:MM:SS.`);
    if (ix.sourceTimestamp >= 0 && (!sourceTimestampRaw || !sourceTimestamp)) throw new Error(`Row ${rowNumber}: Timestamp must be Unix seconds or ISO 8601 with an explicit UTC offset.`);
    if (sourceTimestamp && !bullflowTimestampMatchesEt(sourceTimestamp, date, cell(cells, 'time'))) throw new Error(`Row ${rowNumber}: Timestamp must match Date and TimeET in America/New_York.`);
    if (cancelled === null) throw new Error(`Row ${rowNumber}: Cancelled must be true or false when that column is present.`);
    if (!['CALL', 'PUT'].includes(type) || !side || !sideSourceValue || strike <= 0 || premium < 0 || (openInterest !== null && openInterest < 0)) throw new Error(`Row ${rowNumber}: check Type, Side, SideSource (vendor/user/inferred/synthetic/unknown), positive Strike, nonnegative Premium, and OpenInterest.`);
    if (expiry && !validProfileDate(expiry)) throw new Error(`Row ${rowNumber}: Expiry must be YYYY-MM-DD or blank.`);
    const session = sessionFor(ticker, date);
    if (!session.available) throw new Error(`Row ${rowNumber}: a print row conflicts with an unavailable session declaration.`);
    session.hasPrints = true;
    session.source ||= source;
    if (tradeId) {
      if (tradeId.length > 160) throw new Error(`Row ${rowNumber}: TradeID must be 160 characters or fewer.`);
      const idKey = `${source.toLowerCase()}|${tradeId}`;
      if (tradeIds.has(idKey)) throw new Error(`Row ${rowNumber}: duplicate TradeID ${tradeId} for source ${source || 'unspecified'}.`);
      tradeIds.add(idKey);
    }
    rows.push({ sessionDate: date, timeSeconds, ticker, contract, expiry: expiry || '', type, strike, size, premium, side, sideSource: sideSourceValue, source: source || '', tradeId: tradeId || '', sourceTimestamp: sourceTimestampRaw || '', tradeType: cell(cells, 'tradeType').toUpperCase().replace(/[^A-Z0-9]/g, ''), openInterest, cancelled });
  }
  const sessionCoverage = Array.from(sessions.values()).map(({ hasPrints, ...session }) => session);
  return {
    rows,
    sessionCoverage,
    availableSessions: sessionCoverage.filter(item => item.available).map(({ available, exportComplete, explicitCoverage, source, ...item }) => ({ ...item, exportComplete })),
    cancellationStatusProvided: ix.cancelled >= 0,
    sideSourceProvided: ix.sideSource >= 0,
    sourceProvided: ix.source >= 0,
    tradeIdProvided: ix.tradeId >= 0,
    sourceTimestampProvided: ix.sourceTimestamp >= 0,
  };
}

function calculateBullflowActivityProfile(model) {
  const { rows, ticker, asOfDate } = model;
  const cutoff = parseEtClock(model.asOfTime);
  const coverage = model.sessionCoverage || (model.availableSessions || []).map(item => ({ ...item, available: true, exportComplete: item.exportComplete ?? null }));
  const coverageByDate = new Map(coverage.filter(item => item.ticker === ticker).map(item => [item.date, item]));
  const targetCoverage = coverageByDate.get(asOfDate) || null;
  const targetAvailable = targetCoverage?.available === true;
  const targetComplete = targetCoverage?.exportComplete === true;
  const baselineDates = Array.from(new Set(coverage.filter(item => item.ticker === ticker && item.available === true && item.date < asOfDate).map(item => item.date))).sort((a, b) => b.localeCompare(a)).slice(0, 20);
  const baselineSet = new Set(baselineDates);
  const baselineByDate = new Map(baselineDates.map(date => [date, []]));
  for (const row of rows) if (!row.cancelled && row.ticker === ticker && baselineSet.has(row.sessionDate)) baselineByDate.get(row.sessionDate).push(row);
  const targetRows = targetAvailable ? rows.filter(row => !row.cancelled && row.ticker === ticker && row.sessionDate === asOfDate && row.timeSeconds <= cutoff) : [];
  const baselineCompleteCount = baselineDates.filter(date => coverageByDate.get(date)?.exportComplete === true).length;
  const baselinePartialCount = baselineDates.filter(date => coverageByDate.get(date)?.exportComplete === false).length;
  const baselineUnknownCount = baselineDates.length - baselineCompleteCount - baselinePartialCount;
  const baselineComplete = baselineDates.length === 20 && baselineCompleteCount === 20;
  const cancellationComplete = model.cancellationStatusProvided === true;
  const selectedInputComplete = targetAvailable && targetComplete && cancellationComplete;
  const inputComplete = selectedInputComplete && baselineComplete;
  const volume = (items, type, throughTime = null) => items.reduce((sum, row) => sum + (row.type === type && (throughTime === null || row.timeSeconds <= throughTime) ? row.size : 0), 0);
  const observedCallVolume = volume(targetRows, 'CALL'), observedPutVolume = volume(targetRows, 'PUT');
  const observedCallAskVolume = targetRows.reduce((sum, row) => sum + (row.type === 'CALL' && ['ASK', 'ABOVE_ASK'].includes(row.side) ? row.size : 0), 0);
  const completeCallVolume = selectedInputComplete ? observedCallVolume : null;
  const completePutVolume = selectedInputComplete ? observedPutVolume : null;
  const meanVolume = (type, intraday) => !baselineComplete ? null : baselineDates.reduce((sum, date) => sum + volume(baselineByDate.get(date), type, intraday ? cutoff : null), 0) / 20;
  const ratio = (current, baseline) => !inputComplete || current === null || baseline === null || baseline <= 0 ? null : current / baseline;
  const callIntradayRv = ratio(completeCallVolume, meanVolume('CALL', true));
  const putIntradayRv = ratio(completePutVolume, meanVolume('PUT', true));
  const callDailyRv = ratio(completeCallVolume, meanVolume('CALL', false));
  const putDailyRv = ratio(completePutVolume, meanVolume('PUT', false));
  const unknownCallSideSource = targetRows.some(row => row.type === 'CALL' && (row.sideSource || 'UNKNOWN') === 'UNKNOWN');
  const callAskShare = selectedInputComplete && !unknownCallSideSource && observedCallVolume > 0 ? observedCallAskVolume / observedCallVolume : null;
  const putCallRatio = selectedInputComplete && observedCallVolume > 0 ? observedPutVolume / observedCallVolume : null;
  const contractMap = new Map();
  let netDirectionalPremium = 0, totalPremium = 0;
  for (const row of targetRows) {
    totalPremium += row.premium;
    const multi = row.tradeType === 'MULTI' || row.tradeType === 'MULTILEG';
    if (!multi) {
      if (row.type === 'CALL' && ['ASK', 'ABOVE_ASK'].includes(row.side)) netDirectionalPremium += row.premium;
      if (row.type === 'CALL' && ['BID', 'BELOW_BID'].includes(row.side)) netDirectionalPremium -= row.premium;
      if (row.type === 'PUT' && ['ASK', 'ABOVE_ASK'].includes(row.side)) netDirectionalPremium -= row.premium;
      if (row.type === 'PUT' && ['BID', 'BELOW_BID'].includes(row.side)) netDirectionalPremium += row.premium;
    }
    const key = `${row.type}|${row.contract}`;
    const item = contractMap.get(key) || { contract: row.contract, type: row.type, expiry: row.expiry, strike: row.strike, volume: 0, premium: 0, openInterest: null, latestTime: -1 };
    item.volume += row.size;
    item.premium += row.premium;
    if (row.timeSeconds >= item.latestTime && row.openInterest !== null) { item.openInterest = row.openInterest; item.latestTime = row.timeSeconds; }
    contractMap.set(key, item);
  }
  const unusualContracts = Array.from(contractMap.values()).filter(item => item.openInterest > 0 && item.volume / item.openInterest > 1)
    .map(item => ({ ...item, ratio: item.volume / item.openInterest }))
    .sort((a, b) => b.ratio - a.ratio || b.premium - a.premium || a.contract.localeCompare(b.contract)).slice(0, 5);
  const unusualWeekly = Array.from(contractMap.values()).some(item => {
    if (!item.expiry || !(item.openInterest > 0)) return false;
    const dte = (Date.parse(`${item.expiry}T00:00:00Z`) - Date.parse(`${asOfDate}T00:00:00Z`)) / 86400000;
    return dte >= 0 && dte <= 7 && item.volume / item.openInterest >= 2;
  });
  const flags = [
    { name: 'CALL_VOLUME_SPIKE', active: callIntradayRv === null ? null : callIntradayRv >= 2, rule: 'Call intraday relative volume ≥ 2×' },
    { name: 'PUT_VOLUME_SPIKE', active: putIntradayRv === null ? null : putIntradayRv >= 2, rule: 'Put intraday relative volume ≥ 2×' },
    { name: 'CALL_BUYING_SURGE', active: callIntradayRv === null || callAskShare === null ? null : callIntradayRv >= 2 && callAskShare >= 0.7, rule: 'Call intraday relative volume ≥ 2× and ask/above-ask share ≥ 70%' },
    { name: 'UNUSUAL_WEEKLY_ACTIVITY', active: selectedInputComplete ? unusualWeekly : null, rule: 'A 0–7 DTE contract has volume/open interest ≥ 2×' },
  ];
  const statuses = [];
  if (!cancellationComplete) statuses.push('CANCELLATION_STATUS_NOT_PROVIDED');
  if (!targetAvailable) statuses.push('SELECTED_SESSION_UNAVAILABLE');
  if (targetAvailable && !targetComplete) statuses.push(targetCoverage?.exportComplete === false ? 'SELECTED_EXPORT_PARTIAL' : 'SELECTED_EXPORT_COMPLETENESS_UNKNOWN');
  if (baselineDates.length < 20) statuses.push('INSUFFICIENT_HISTORY');
  else if (!baselineComplete) statuses.push(baselinePartialCount ? 'BASELINE_EXPORT_PARTIAL' : 'BASELINE_EXPORT_COMPLETENESS_UNKNOWN');
  if (targetAvailable && targetRows.length === 0) statuses.push(targetComplete ? 'NO_PRINTS_THROUGH_AS_OF' : 'NO_PRINTS_IN_UNVERIFIED_EXPORT');
  const sideProvenanceCounts = Object.fromEntries(['VENDOR', 'USER', 'INFERRED', 'SYNTHETIC', 'UNKNOWN'].map(source => [source, targetRows.filter(row => (row.sideSource || 'UNKNOWN') === source).length]));
  const sourceTimestampCount = targetRows.filter(row => row.sourceTimestamp).length;
  const directionalSidesAttributed = targetRows.filter(row => row.tradeType !== 'MULTI' && row.tradeType !== 'MULTILEG').every(row => (row.sideSource || 'UNKNOWN') !== 'UNKNOWN');
  const baselineRows = Array.from(baselineByDate.values()).flat();
  const rowSources = Array.from(new Set([
    ...targetRows.map(row => row.source),
    ...baselineRows.map(row => row.source),
    ...baselineDates.map(date => coverageByDate.get(date)?.source),
    targetCoverage?.source,
  ].map(source => String(source || '').trim()).filter(Boolean)));
  if (unknownCallSideSource) statuses.push('CALL_SIDE_PROVENANCE_UNKNOWN');
  if (!directionalSidesAttributed) statuses.push('DIRECTIONAL_SIDE_PROVENANCE_UNKNOWN');
  return {
    targetAvailable, targetComplete, targetRows, baselineCount: baselineDates.length,
    baselineCompleteCount, baselinePartialCount, baselineUnknownCount, inputComplete, selectedInputComplete,
    observedCallVolume, observedPutVolume, callVolume: completeCallVolume, putVolume: completePutVolume,
    callIntradayRv, putIntradayRv, callDailyRv, putDailyRv, callAskShare, putCallRatio,
    netDirectionalPremium: selectedInputComplete && directionalSidesAttributed ? netDirectionalPremium : null,
    totalPremium: selectedInputComplete ? totalPremium : null,
    sideProvenanceCounts, sourceTimestampCount, rowSources, statuses, flags, unusualContracts,
  };
}

function createBullflowProfileSample(asOfDate, ticker) {
  const rows = [], availableSessions = [], sessionCoverage = [], cursor = new Date(`${asOfDate}T12:00:00Z`), priorDates = [];
  while (priorDates.length < 20) {
    cursor.setUTCDate(cursor.getUTCDate() - 1);
    if (cursor.getUTCDay() !== 0 && cursor.getUTCDay() !== 6) priorDates.push(cursor.toISOString().slice(0, 10));
  }
  priorDates.reverse().forEach((date, index) => {
    availableSessions.push({ ticker, date, exportComplete: true });
    sessionCoverage.push({ ticker, date, available: true, exportComplete: true, explicitCoverage: true, source: 'SYNTHETIC SAMPLE' });
    if (index === 5) return;
    const expiry = new Date(`${date}T12:00:00Z`); expiry.setUTCDate(expiry.getUTCDate() + 21);
    rows.push({ sessionDate: date, timeSeconds: 10 * 3600 + 30 * 60, ticker, contract: `${ticker} ${expiry.toISOString().slice(0, 10)} 700C`, expiry: expiry.toISOString().slice(0, 10), type: 'CALL', strike: 700, size: 20 + index % 5 * 2, premium: 9000 + index * 150, side: 'ASK', sideSource: 'SYNTHETIC', source: 'SYNTHETIC SAMPLE', tradeType: 'SWEEP', openInterest: 180 });
    rows.push({ sessionDate: date, timeSeconds: 14 * 3600, ticker, contract: `${ticker} ${expiry.toISOString().slice(0, 10)} 670P`, expiry: expiry.toISOString().slice(0, 10), type: 'PUT', strike: 670, size: 12 + index % 4, premium: 4200 + index * 90, side: 'BID', sideSource: 'SYNTHETIC', source: 'SYNTHETIC SAMPLE', tradeType: 'BLOCK', openInterest: 140 });
  });
  availableSessions.push({ ticker, date: asOfDate, exportComplete: true });
  sessionCoverage.push({ ticker, date: asOfDate, available: true, exportComplete: true, explicitCoverage: true, source: 'SYNTHETIC SAMPLE' });
  const weeklyExpiry = new Date(`${asOfDate}T12:00:00Z`); weeklyExpiry.setUTCDate(weeklyExpiry.getUTCDate() + 3);
  const longExpiry = new Date(`${asOfDate}T12:00:00Z`); longExpiry.setUTCDate(longExpiry.getUTCDate() + 14);
  const weekly = weeklyExpiry.toISOString().slice(0, 10), later = longExpiry.toISOString().slice(0, 10);
  rows.push({ sessionDate: asOfDate, timeSeconds: 14 * 3600 + 35 * 60, ticker, contract: `${ticker} ${weekly} 700C`, expiry: weekly, type: 'CALL', strike: 700, size: 55, premium: 33000, side: 'ASK', sideSource: 'SYNTHETIC', source: 'SYNTHETIC SAMPLE', tradeType: 'SWEEP', openInterest: 20 });
  rows.push({ sessionDate: asOfDate, timeSeconds: 14 * 3600 + 50 * 60, ticker, contract: `${ticker} ${weekly} 700C`, expiry: weekly, type: 'CALL', strike: 700, size: 35, premium: 21000, side: 'ABOVE_ASK', sideSource: 'SYNTHETIC', source: 'SYNTHETIC SAMPLE', tradeType: 'SWEEP', openInterest: 20 });
  rows.push({ sessionDate: asOfDate, timeSeconds: 14 * 3600 + 45 * 60, ticker, contract: `${ticker} ${later} 670P`, expiry: later, type: 'PUT', strike: 670, size: 12, premium: 7200, side: 'BID', sideSource: 'SYNTHETIC', source: 'SYNTHETIC SAMPLE', tradeType: 'BLOCK', openInterest: 100 });
  rows.push({ sessionDate: asOfDate, timeSeconds: 14 * 3600 + 48 * 60, ticker, contract: `${ticker} ${weekly} 710C-MULTI`, expiry: weekly, type: 'CALL', strike: 710, size: 5, premium: 5000, side: 'ASK', sideSource: 'SYNTHETIC', source: 'SYNTHETIC SAMPLE', tradeType: 'MULTI', openInterest: 200 });
  return { rows, availableSessions, sessionCoverage, cancellationStatusProvided: true, sideSourceProvided: true, sourceProvided: true, tradeIdProvided: false };
}

function renderBullflowActivityProfile() {
  const model = state.bullflowProfile;
  const result = model.rows.length || model.availableSessions.length ? calculateBullflowActivityProfile(model) : null;
  const show = value => value === null || !Number.isFinite(value) ? '—' : `${value.toFixed(2)}×`;
  const share = value => value === null || !Number.isFinite(value) ? '—' : `${(value * 100).toFixed(1)}%`;
  const sideSources = result ? ['VENDOR', 'USER', 'INFERRED', 'SYNTHETIC', 'UNKNOWN'].map(source => `${source.toLowerCase()}: ${result.sideProvenanceCounts[source]}`).join(' · ') : '';
  const targetCompleteness = result?.targetComplete ? 'user-declared complete' : result?.targetAvailable ? 'available; completeness unknown or partial' : 'unavailable / undeclared';
  const coverageDiagnostics = result ? `<div class="activity-diagnostics"><div><b>SELECTED SESSION</b><span>${result.targetAvailable ? 'Declared available' : 'Unavailable / undeclared'}</span></div><div><b>EXPORT COMPLETENESS</b><span>${esc(targetCompleteness)}</span></div><div><b>COMPLETE BASELINE</b><span>${result.baselineCompleteCount}/20 · ${result.baselinePartialCount} partial · ${result.baselineUnknownCount} unknown</span></div><div><b>SIDE LABEL PROVENANCE</b><span>${esc(sideSources)}</span></div><div><b>RAW SOURCE TIMESTAMPS</b><span>${result.sourceTimestampCount}/${result.targetRows.length} selected prints retained</span></div><div><b>USER-PROVIDED SOURCES IN INPUT WINDOW</b><span>${result.rowSources.length ? esc(result.rowSources.join(', ')) : 'Unspecified'}</span></div></div>` : '';
  const metrics = result ? `<div class="flow-summary-grid activity-metric-grid">
    <article class="stat-card"><div class="stat-label">CALL INTRADAY RV</div><div class="stat-value">${show(result.callIntradayRv)}</div><div class="stat-foot muted">vs 20 same-time sessions</div></article>
    <article class="stat-card"><div class="stat-label">PUT INTRADAY RV</div><div class="stat-value">${show(result.putIntradayRv)}</div><div class="stat-foot muted">vs 20 same-time sessions</div></article>
    <article class="stat-card"><div class="stat-label">CALL SESSION RV</div><div class="stat-value">${show(result.callDailyRv)}</div><div class="stat-foot muted">to as-of / full-day mean</div></article>
    <article class="stat-card"><div class="stat-label">PUT SESSION RV</div><div class="stat-value">${show(result.putDailyRv)}</div><div class="stat-foot muted">to as-of / full-day mean</div></article>
    <article class="stat-card"><div class="stat-label">CALL ASK-SIDE SHARE</div><div class="stat-value">${share(result.callAskShare)}</div><div class="stat-foot muted">ask + above ask / call size</div></article>
    <article class="stat-card"><div class="stat-label">PUT / CALL VOLUME</div><div class="stat-value">${result.putCallRatio === null ? '—' : result.putCallRatio.toFixed(2)}</div><div class="stat-foot muted">recorded size ratio</div></article>
    <article class="stat-card"><div class="stat-label">NET DIRECTIONAL PREMIUM</div><div class="stat-value">${result.netDirectionalPremium === null ? '—' : money(result.netDirectionalPremium, true)}</div><div class="stat-foot muted">multi-leg excluded from sides</div></article>
    <article class="stat-card"><div class="stat-label">SUPPLIED PRINTS THROUGH AS-OF</div><div class="stat-value">${integer(result.targetRows.length)}</div><div class="stat-foot muted">${integer(result.observedCallVolume + result.observedPutVolume)} observed contracts</div></article>
    <article class="stat-card"><div class="stat-label">TOTAL PREMIUM</div><div class="stat-value">${result.totalPremium === null ? '—' : money(result.totalPremium, true)}</div><div class="stat-foot muted">includes multi-leg prints</div></article>
  </div>` : '<div class="empty-state"><span>◉</span><b>No activity data loaded</b><p>Upload a local CSV or load the synthetic 21-session example to calculate the profile.</p></div>';
  const statusMarkup = result ? result.statuses.length ? result.statuses.map(status => label(status.replace(/_/g, ' '), 'orange')).join(' ') : label('COMPLETE INPUT DECLARED', 'green-badge') : '';
  const flags = result ? result.flags.map(flag => `<div class="activity-flag ${flag.active === null ? 'unknown' : flag.active ? 'active' : 'inactive'}"><div><b>${esc(flag.name)}</b><small>${esc(flag.rule)}</small></div><span>${flag.active === null ? 'UNKNOWN' : flag.active ? 'TRIGGERED' : 'NOT MET'}</span></div>`).join('') : '';
  const contracts = result?.unusualContracts.length ? result.unusualContracts.map(item => `<tr><td>${esc(item.contract)}</td><td>${item.type}</td><td>${item.expiry || '—'}</td><td>${integer(item.volume)}</td><td>${item.openInterest === null ? '—' : integer(item.openInterest)}</td><td>${item.ratio.toFixed(2)}×</td><td>${money(item.premium, true)}</td></tr>`).join('') : '<tr><td colspan="7">No contract exceeded volume/open interest &gt; 1 with positive OI.</td></tr>';
  return `${pageHeading('PUBLISHED METHOD · LOCAL DATA', 'Options Activity Profile', 'Apply Bullflow’s documented profile method to locally supplied rows. Ratios require 20 complete baseline exports and a complete selected export; completeness remains a user declaration.', '<button class="button secondary" data-view="coverage">Vendor evidence →</button>')}
    ${panel('Source data and as-of controls', 'TimeET is Eastern wall-clock time. Only prints through the selected as-of time are included.', `<form id="bullflow-profile-config" class="activity-controls"><label class="field-label">TICKER<input name="ticker" value="${esc(model.ticker)}" maxlength="10" required /></label><label class="field-label">SESSION DATE<input name="asOfDate" type="date" value="${esc(model.asOfDate)}" required /></label><label class="field-label">AS-OF ET<input name="asOfTime" type="time" value="${esc(model.asOfTime)}" required /></label><button class="button primary">Recalculate profile</button><button class="button secondary" type="button" data-action="bullflow-profile-demo">Load synthetic sample</button></form>
      <div class="activity-file-row"><label class="field-label">PRINT HISTORY CSV<input id="bullflow-profile-file" type="file" accept=".csv,text/csv" /></label><span class="small-muted">${model.filename ? `Loaded: ${esc(model.filename)}${model.importedAt ? ` · imported ${esc(model.importedAt)}` : ''}` : 'CSV stays in this browser tab.'}</span></div>
      <div class="activity-input-help"><b>Required columns:</b> <code>Date,TimeET,Ticker,Contract,Expiry,Type,Strike,Size,Premium,Side,TradeType,OpenInterest</code>. A 20-session ratio also requires an explicit cancellation field (<code>Cancelled</code>) and a coverage-only declaration for each baseline and selected date: blank Contract, zero Size, <code>Available=true</code>, and <code>ExportComplete=true</code>. That declaration means the supplied export/query is complete for that session or as-of window; it does not mean complete market-wide options activity. <code>Available=false</code> and missing dates stay unavailable. Without <code>ExportComplete</code>, no-print rows are not known zero and incomplete dates cannot enter a ratio. Optional <code>Timestamp</code> accepts Unix seconds or ISO 8601 with an explicit UTC offset and is checked against Date/TimeET in New York time. <code>Source</code> records a user-provided source label, <code>TradeID</code> rejects duplicate source IDs, and <code>SideSource</code> accepts vendor/user/inferred/unknown; the synthetic sample is internally labeled synthetic. Unknown side provenance suppresses side-derived calculations. Premium is total dollars per print; Side accepts Ask, Above Ask, Mid, Bid, Below Bid, or Unknown.</div>
      ${model.error ? `<div class="optionlab-error" role="alert">${esc(model.error)}</div>` : ''}${model.notice ? `<div class="activity-notice">${esc(model.notice)}</div>` : ''}`, '')}
    ${result ? `<div class="activity-result-head"><div><b>${esc(model.ticker)} · ${esc(model.asOfDate)} · through ${esc(model.asOfTime)} ET</b><span>${result.baselineCount}/20 prior available sessions · ${result.targetAvailable ? 'selected session declared available' : 'selected session unavailable or undeclared'}</span></div><div>${statusMarkup}</div></div>
      ${coverageDiagnostics}${metrics}
      ${panel('Published activity flags', 'Only the four documented thresholds are evaluated; no proprietary score is inferred.', `<div class="activity-flag-list">${flags}</div>`, '')}
      ${panel('Unusual contracts', 'Computed from supplied rows only: volume / open interest > 1, ordered by ratio, premium, then contract symbol.', `<div class="table-wrap"><table class="data-table"><thead><tr><th>CONTRACT</th><th>TYPE</th><th>EXPIRY</th><th>VOLUME</th><th>OPEN INTEREST</th><th>VOL / OI</th><th>PREMIUM</th></tr></thead><tbody>${contracts}</tbody></table></div>`, '')}` : ''}
    <div class="evidence-callout portfolio-callout"><b>Interpretation boundary</b><span>The 20-date baseline, same-time-of-day comparison, side premium arithmetic, and four thresholds come from Bullflow’s public API documentation. Availability, export completeness, source labels, cancellation flags, and side-label provenance are declarations from the supplied file, not independently verified facts. Bullflow describes historical flow as recorded activity, not a complete record of every transaction; source feed lineage is not published. No Bullflow endpoint is called. SigScore and proprietary algo-alert triggers remain sealed; these flags are not a validated alpha signal.</span><a href="../../research/rea-teardowns/bullflow/TEARDOWN.md">Review teardown evidence →</a></div>`;
}

function renderApi() {
  const status = state.apiStatus || { mode: 'demo', provider: 'Checking local server…', keyConfigured: false, allowedReads: ['market-tide', 'flow', 'gex', 'darkpool', 'news', 'movers'] };
  const configured = status.keyConfigured;
  return `${pageHeading('DATA SOURCE & PRIVACY', 'Connection settings', 'Understand exactly where local demo data ends and optional vendor reads begin.', '<button class="button secondary" data-action="refresh-status">↻ Check local status</button>')}
    <div class="connection-card ${configured ? 'connected' : ''}"><div class="connection-state-icon">${configured ? '✓' : '◉'}</div><div class="connection-main"><span class="eyebrow">CURRENT MODE</span><h2>${configured ? 'API key configured on local server' : 'Synthetic demo mode'}</h2><p>${configured ? 'The server sees a key in its environment. The browser never receives it.' : 'No UW_API_KEY is configured. All screens continue to use generated sample data.'}</p></div><div class="connection-badge">${configured ? label('KEY PRESENT · SERVER SIDE', 'green-badge') : label('DEMO DATA', 'orange')}</div></div>
    <div class="api-settings-grid"><div class="api-settings-main">${panel('Enable optional live reads', 'The connector uses the official bearer-authenticated API', `<ol class="setup-steps"><li><b>Create or rotate a token</b><span>Use the official Unusual Whales API dashboard. A lost token cannot be recovered from public assets.</span><a href="https://unusualwhales.com/dashboard/api" target="_blank" rel="noreferrer">Open API dashboard ↗</a></li><li><b>Keep the key out of browser storage</b><span>Set <code>UW_API_KEY</code> in the shell environment that starts this local server.</span><code class="command-line">$env:UW_API_KEY = "your-token"<br/>node server.mjs</code></li><li><b>Restart the server and check status</b><span>The key is read once when the server starts. The status check returns presence only, never the secret.</span></li></ol><div class="callout-warning"><b>Commercial use</b><span>API product plans differ. Do not redistribute market data unless your vendor license permits it. Confirm current terms with the provider.</span></div>`, '')}${panel('Read-only provider endpoint allowlist', 'Only these documented provider GET endpoints are reachable through the local proxy', `<div class="endpoint-list">${[['GET', '/api/market/market-tide', 'Market tide'], ['GET', '/api/stock/{ticker}/flow-recent', 'Recent option flow'], ['GET', '/api/stock/{ticker}/gex-levels', 'GEX levels'], ['GET', '/api/darkpool/recent', 'Recent dark-pool prints'], ['GET', '/api/darkpool/{ticker}', 'Ticker dark-pool prints'], ['GET', '/api/news/headlines', 'News headlines'], ['GET', '/api/market/movers', 'Market movers']].map(([m, p, d]) => `<div><code>${m}</code><span>${p}</span><small>${d}</small></div>`).join('')}</div><div class="api-result" id="api-result">${state.apiMessage ? esc(state.apiMessage) : 'No live request has been made from this screen.'}</div><button class="button secondary" data-action="probe-market">Request market-tide sample</button>`, '')}</div>
      <aside class="api-settings-side">${panel('Local server status', '127.0.0.1 · port 4173', `<div class="status-details"><div><span>Provider mode</span><b>${esc(status.provider || 'Unknown')}</b></div><div><span>Credential exposure</span><b class="positive">Server only</b></div><div><span>HTTP methods</span><b>GET only</b></div><div><span>Account data</span><b>Blocked / unsupported</b></div><div><span>Write operations</span><b>Blocked</b></div></div><button class="text-button" data-action="refresh-status">Refresh status →</button>`, '')}${panel('Research references', 'Public vendor documentation', `<div class="reference-links"><a href="https://api.unusualwhales.com/docs" target="_blank" rel="noreferrer">API reference ↗</a><a href="https://unusualwhales.com/public-api/mcp" target="_blank" rel="noreferrer">MCP setup page ↗</a><a href="https://docs.unusualwhales.com/features/2-options-flow/" target="_blank" rel="noreferrer">Options flow semantics ↗</a><a href="../../research/unusual_whales/PRODUCT_APPROXIMATION.md">Local research notes →</a></div>`, '')}</aside></div>
    <div class="privacy-footnote"><b>Privacy by design</b><span>This prototype has no login or cloud service. Your watchlists, saved trades, alert rules, and theme are stored in this browser's local storage. Never paste an API key into this screen or commit it to the repository.</span></div>`;
}

function renderModal() { /* reserved for future focused detail panels */ }

function render() {
  renderShell();
  const appShell = document.querySelector('.app-shell');
  if (state.mobileNavOpen) appShell?.classList.add('mobile-nav-open');
}

function navigate(view) {
  state.view = view;
  if (location.hash !== `#${view}`) history.pushState({ view }, '', `#${view}`);
  render();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function selectTicker(value) {
  const ticker = normalizeTicker(value);
  if (!ticker) return false;
  if (confluenceHasValues(state.confluence)) state.confluenceByTicker[state.ticker] = state.confluence;
  else delete state.confluenceByTicker[state.ticker];
  state.ticker = ticker;
  state.chartSymbol = ticker;
  state.confluence = state.confluenceByTicker[ticker] || emptyConfluenceState();
  persist();
  return true;
}

function setApiMessage(message) {
  state.apiMessage = message;
  const node = document.getElementById('api-result');
  if (node) node.textContent = message;
}

async function refreshStatus() {
  const button = document.querySelector('[data-action="refresh-status"]');
  if (button) { button.disabled = true; button.textContent = 'Checking…'; }
  try {
    const response = await fetch('/api/status', { headers: { Accept: 'application/json' } });
    state.apiStatus = await response.json();
  } catch {
    state.apiStatus = { mode: 'demo', provider: 'Local server not detected', keyConfigured: false, allowedReads: [] };
  }
  render();
}

async function probeMarketTide() {
  setApiMessage('Sending GET /api/uw/market-tide through the local read-only proxy…');
  try {
    const response = await fetch('/api/uw/market-tide', { headers: { Accept: 'application/json' } });
    const text = await response.text();
    let data; try { data = JSON.parse(text); } catch { data = { message: 'Non-JSON response' }; }
    if (!response.ok) return setApiMessage(`Request returned HTTP ${response.status}: ${data.message || data.error || 'Check local server configuration.'}`);
    const array = Array.isArray(data) ? data : Object.values(data).find(Array.isArray);
    setApiMessage(`HTTP ${response.status} · received ${array?.length ?? 'an object'} response. The dashboard remains on synthetic data until a provider-specific adapter is reviewed.`);
  } catch {
    setApiMessage('Could not reach the local connector. Start the app with node server.mjs and try again.');
  }
}

async function importStrategyCsv(file) {
  try {
    if (file.size > 20 * 1024 * 1024) throw new Error('CSV files must be 20 MiB or smaller.');
    const rows = parseStrategyCsv(await file.text());
    state.strategy.rows = rows;
    state.strategy.filename = file.name;
    state.strategy.source = 'csv';
    state.strategy.error = '';
    state.strategy.notice = `Loaded ${rows.length.toLocaleString()} ordered observations. Upload remains local to this browser tab.`;
  } catch (error) {
    state.strategy.error = error.message || 'Could not read this CSV.';
    state.strategy.notice = 'The previous dataset is still loaded. The selected file was not uploaded.';
  }
  render();
}

async function importDanelfinPortfolioCsv(file) {
  const target = state.danelfinPortfolio;
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error('Portfolio CSV files must be 10 MiB or smaller.');
    const parsed = parseDanelfinCsv(await file.text());
    target.rows = parsed.rows;
    target.filename = file.name;
    target.source = 'csv';
    target.asOf = parsed.asOf;
    target.startDate = parsed.startDate;
    target.provenBuyProvided = parsed.provenBuyProvided;
    target.error = '';
    target.notice = `Loaded ${parsed.rows.length.toLocaleString()} symbols across ${parsed.snapshotDates.length} dated snapshots locally. ${parsed.asOf ? `Latest snapshot: ${parsed.asOf}; schedule starts at ${parsed.startDate}.` : 'No AsOf/Date field supplied; point-in-time scheduling is unavailable.'} ${parsed.provenBuyProvided ? '' : 'No ProvenBuySignal column supplied; all are treated as unconfirmed.'}`.trim();
  } catch (error) {
    target.error = error.message || 'Could not read this portfolio CSV.';
    target.notice = 'The previous candidate set remains loaded; the selected file was not uploaded.';
  }
  render();
}

function exportDanelfinPortfolioAudit() {
  const stateData = state.danelfinPortfolio;
  const snapshotRows = stateData.asOf ? stateData.rows.filter(row => row.asOf === stateData.asOf) : stateData.rows;
  const result = buildDanelfinPortfolio(snapshotRows, stateData.preferProvenBuy);
  const quote = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
  const selectedWeights = new Map(result.chosen.map(row => [row.ticker, row.weightPct]));
  const lines = [
    ['ticker', 'sector', 'score_user_supplied', 'low_risk_user_supplied', 'avg_3m_volume_shares_user_supplied', 'proven_buy_signal_user_supplied', 'sector_rank', 'sector_mean_score', 'within_sector_rank', 'decision', 'equal_weight_percent', 'as_of', 'snapshot_complete_user_declared'].map(quote).join(','),
    ...result.auditRows.map(row => [row.ticker, row.sector, row.score, row.lowRisk, row.avg3mVolume, row.provenBuy, row.sectorRank ?? '', row.sectorMean ?? '', row.nameRank ?? '', row.decision, selectedWeights.get(row.ticker) ?? '', row.asOf || stateData.asOf || '', row.snapshotComplete === null || row.snapshotComplete === undefined ? '' : row.snapshotComplete].map(quote).join(',')),
  ];
  const blob = new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `sector-portfolio-audit-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function importStaticGexCsv(file) {
  const target = state.staticGex;
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error('Option-chain CSV files must be 10 MiB or smaller.');
    const parsed = parseStaticGexCsv(await file.text());
    target.rows = parsed.rows;
    target.ticker = parsed.ticker;
    target.asOf = parsed.asOf;
    target.spot = parsed.spot;
    target.filename = file.name;
    target.source = 'csv';
    target.error = '';
    target.notice = `Loaded ${parsed.rows.length.toLocaleString()} option rows for ${parsed.ticker} as of ${parsed.asOf}. The upload stays local to this tab.`;
  } catch (error) {
    target.error = error.message || 'Could not read this option-chain CSV.';
    target.notice = 'The previous chain remains loaded; the selected file was not uploaded.';
  }
  render();
}

async function importBullflowActivityCsv(file) {
  const target = state.bullflowProfile;
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error('Options activity CSV files must be 10 MiB or smaller.');
    const parsed = parseBullflowActivityCsv(await file.text());
    Object.assign(target, {
      rows: parsed.rows,
      availableSessions: parsed.availableSessions,
      sessionCoverage: parsed.sessionCoverage,
      cancellationStatusProvided: parsed.cancellationStatusProvided,
      sideSourceProvided: parsed.sideSourceProvided,
      sourceProvided: parsed.sourceProvided,
      tradeIdProvided: parsed.tradeIdProvided,
      filename: file.name,
      importedAt: new Date().toISOString(),
      error: '',
      notice: `Loaded ${parsed.rows.length.toLocaleString()} prints and ${parsed.availableSessions.length.toLocaleString()} declared available ticker-sessions. Completeness is tracked separately; the file stays local to this tab.`,
    });
  } catch (error) {
    target.error = error instanceof Error ? error.message : 'Could not read this options activity CSV.';
    target.notice = 'The previous profile remains loaded; the selected file was not uploaded.';
  }
  render();
}

async function importFinvizSnapshotCsv(file) {
  const target = state.finvizLab;
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error('Screener snapshot CSV files must be 10 MiB or smaller.');
    const rows = parseFinvizSnapshotCsv(await file.text());
    Object.assign(target, { rows, filename: file.name, error: '', notice: `Loaded ${rows.length.toLocaleString()} unique ticker rows. The file stays local to this tab.` });
  } catch (error) {
    target.error = error instanceof Error ? error.message : 'Could not read this screener snapshot CSV.';
    target.notice = 'The previous snapshot remains loaded; the selected file was not uploaded.';
  }
  render();
}

async function importStockRoverFactorCsv(file) {
  const target = state.stockRoverLab;
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error('Factor snapshot CSV files must be 10 MiB or smaller.');
    const parsed = parseStockRoverFactorCsv(await file.text());
    Object.assign(target, {
      rows: parsed.rows,
      filename: file.name,
      source: 'csv',
      error: '',
      notice: `Loaded ${parsed.rows.length.toLocaleString()} symbols for ${parsed.asOf}. Values remain in this tab and are not uploaded.`,
    });
  } catch (error) {
    target.error = error instanceof Error ? error.message : 'Could not read this factor snapshot CSV.';
    target.notice = 'The previous factor snapshot remains loaded; the selected file was not uploaded.';
  }
  render();
}

function exportStockRoverFactorAudit() {
  const model = state.stockRoverLab;
  if (!model.rows.length) return;
  const result = calculateStockRoverFactorScores(model.rows);
  const quote = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
  const headers = ['Ticker', 'Sector', 'AsOf', ...stockRoverFactorMetrics.map(metric => metric.key), ...stockRoverFactorMetrics.map(metric => `${metric.key}Percentile`), ...stockRoverFactorCategories.map(category => `${category.label}Score`), 'CompositeScore', 'CompletedCategories', 'MissingMetrics'];
  const lines = [headers.map(quote).join(','), ...result.rows.map(row => [
    row.ticker, row.sector, row.asOf, ...stockRoverFactorMetrics.map(metric => row.raw[metric.key]),
    ...stockRoverFactorMetrics.map(metric => row.percentiles[metric.key]),
    ...stockRoverFactorCategories.map(category => row.categoryScores[category.key]), row.composite,
    row.completedCategories, row.missingMetrics,
  ].map(quote).join(','))];
  const blob = new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `stock-rover-factor-audit-${model.rows[0].asOf}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function downloadStockRoverFactorTemplate() {
  const headers = ['Ticker', 'Sector', 'AsOf', ...stockRoverFactorMetrics.map(metric => metric.key)];
  const blob = new Blob([headers.join(',') + '\r\n'], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'stock-rover-factor-snapshot-template.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportStaticGexContractAudit() {
  const p = state.staticGex;
  const result = buildStaticGexSnapshot(p.rows, p);
  const quote = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
  const lines = [
    ['ticker', 'as_of', 'spot', 'strike', 'type', 'open_interest_prior_night', 'iv_percent_user_supplied', 'dte_calendar_days', 'gamma_black_scholes', 'signed_dollar_gex_per_1pct_move', 'sign_convention', 'risk_free_rate_pct', 'dividend_yield_pct', 'contract_multiplier'].map(quote).join(','),
    ...result.optionRows.map(row => [row.ticker, row.asOf, row.spot, row.strike, row.type, row.openInterest, row.ivPct, row.dte, row.gamma, row.dollarGex, row.type === 'CALL' ? 'call-positive' : 'put-negative', p.riskFreeRatePct, p.dividendYieldPct, p.multiplier].map(quote).join(',')),
  ];
  const blob = new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `static-gex-contract-audit-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function saveStrategyRun() {
  const result = analyzeStrategy();
  if (result.error) {
    state.strategy.error = result.error;
    render();
    return;
  }
  state.strategy.error = '';
  state.strategy.notice = 'Saved this summary in local browser storage.';
  state.strategyRuns.unshift({
    savedAt: new Date().toLocaleString(),
    filename: state.strategy.filename,
    fast: state.strategy.fast,
    slow: state.strategy.slow,
    outOfSample: result.outOfSample.totalReturn,
    maxDrawdown: result.overall.maxDrawdown,
  });
  state.strategyRuns = state.strategyRuns.slice(0, 12);
  persist();
  render();
}

function downloadStrategyReport() {
  const result = analyzeStrategy();
  if (result.error) {
    state.strategy.error = result.error;
    render();
    return;
  }
  const escapeCsv = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
  let strategyEquity = 1, benchmarkEquity = 1;
  const lines = [['date', 'close', 'fast_sma', 'slow_sma', 'long_position', 'turnover', 'gross_return', 'estimated_cost_bps_per_side', 'net_return', 'strategy_equity', 'buy_hold_equity']];
  for (const row of result.records) {
    strategyEquity *= Math.max(0, 1 + row.net);
    benchmarkEquity *= Math.max(0, 1 + row.gross);
    lines.push([row.date, row.close, row.fast, row.slow, row.position, row.turnover, row.gross, state.strategy.costBps, row.net, strategyEquity, benchmarkEquity]);
  }
  const blob = new Blob([lines.map(line => line.map(escapeCsv).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `strategy-lab-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

document.addEventListener('click', (event) => {
  const navButton = event.target.closest('[data-view]');
  if (navButton) { event.preventDefault(); navigate(navButton.dataset.view); return; }
  const symbolButton = event.target.closest('[data-symbol]');
  if (symbolButton) { if (selectTicker(symbolButton.dataset.symbol)) navigate('ticker'); return; }
  const action = event.target.closest('[data-action]');
  if (!action) return;
  const name = action.dataset.action;
  if (name === 'confluence-reset') {
    state.confluence = emptyConfluenceState();
    persist(); render();
  }
  if (name === 'confluence-model') {
    state.confluenceMode = action.dataset.model === 'effective' ? 'effective' : 'metadata';
    persist(); render();
  }
  if (name === 'theme') { state.theme = state.theme === 'dark' ? 'light' : 'dark'; persist(); render(); }
  if (name === 'mobile-menu') document.querySelector('.app-shell')?.classList.toggle('mobile-nav-open');
  if (name === 'collapse-sidebar') document.querySelector('.app-shell')?.classList.toggle('sidebar-collapsed');
  if (name === 'save-trade') { const id = action.dataset.id; state.savedTrades = state.savedTrades.includes(id) ? state.savedTrades.filter(v => v !== id) : [...state.savedTrades, id]; persist(); render(); }
  if (name === 'watch-toggle') { const ticker = normalizeTicker(action.dataset.ticker); if (!ticker) return; state.watchlist = state.watchlist.includes(ticker) ? state.watchlist.filter(t => t !== ticker) : [...state.watchlist, ticker]; persist(); render(); }
  if (name === 'watch-remove') { state.watchlist = state.watchlist.filter(t => t !== action.dataset.ticker); persist(); render(); }
  if (name === 'clear-flow') { state.flowSearch = ''; state.flowType = 'all'; state.flowSide = 'all'; state.minPremium = 0; state.flowSort = 'time'; render(); }
  if (name === 'clear-dp') { state.dpTicker = ''; render(); }
  if (name === 'clear-disclosure') { state.disclosureSearch = ''; render(); }
  if (name === 'clear-news') { state.newsSearch = ''; render(); }
  if (name === 'reset-screener') { state.screenerSector = 'all'; state.screenerType = 'all'; render(); }
  if (name === 'gex-basis') { state.gexBasis = action.dataset.value; render(); }
  if (name === 'calendar-range') { state.calendarRange = action.dataset.value; render(); }
  if (name === 'chart-range') { state.chartRange = action.dataset.value; render(); }
  if (name === 'new-alert') { state.showAlertForm = true; render(); document.querySelector('#alert-form input[name="ticker"]')?.focus(); }
  if (name === 'close-alert-form') { state.showAlertForm = false; render(); }
  if (name === 'alert-remove') { state.alerts.splice(Number(action.dataset.index), 1); persist(); render(); }
  if (name === 'refresh-status') refreshStatus();
  if (name === 'probe-market') probeMarketTide();
  if (name === 'chart-range') { state.chartRange = action.dataset.value; render(); }
  if (name === 'save-chart') { state.savedLayouts.unshift({ symbol: state.chartSymbol, range: state.chartRange, savedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }); state.savedLayouts = state.savedLayouts.slice(0, 12); state.layoutMessage = `Saved ${state.chartSymbol} ${state.chartRange} locally`; persist(); render(); }
  if (name === 'load-layout') { const layout = state.savedLayouts[Number(action.dataset.index)]; if (layout) { state.chartSymbol = layout.symbol; state.chartRange = layout.range; state.layoutMessage = `Loaded ${layout.symbol} ${layout.range}`; render(); } }
  if (name === 'toggle-indicators') { action.classList.toggle('selected'); document.querySelector('.chart-tools')?.classList.toggle('highlighted'); }
  if (name === 'fullscreen') { document.querySelector('.chart-workspace')?.classList.toggle('chart-fullscreen'); }
  if (name === 'reset-overlays') { document.querySelectorAll('.toggle-row input').forEach((input, i) => { input.checked = i < 2; }); }
  if (name === 'news-tag') { state.newsSearch = action.dataset.value === 'all' ? '' : action.dataset.value; render(); }
  if (name === 'portfolio-demo') {
    state.danelfinPortfolio = { rows: createDanelfinDemoRows(), filename: 'Synthetic demonstration universe', source: 'synthetic', error: '', notice: 'Loaded a deterministic 36-name sample for workflow demonstration.', provenBuyProvided: true, preferProvenBuy: true, asOf: '', startDate: '' };
    render();
  }
  if (name === 'portfolio-export') exportDanelfinPortfolioAudit();
  if (name === 'static-gex-demo') {
    Object.assign(state.staticGex, { rows: createStaticGexDemoRows(), filename: 'Synthetic demonstration option chain', source: 'synthetic', error: '', notice: 'Loaded a deterministic 42-row option-chain sample. Values are synthetic.', ticker: 'SPY', asOf: '', spot: 681.44 });
    render();
  }
  if (name === 'azrael-example') {
    Object.assign(state.azraelMap, { anchorClose: 7757.17, vixClose: 16.68, elapsedMinutes: 120, sessionMinutes: 390, candidateTarget: 7800, error: '' });
    render();
  }
  if (name === 'bullflow-profile-demo') {
    const fields = new FormData(document.getElementById('bullflow-profile-config'));
    const ticker = normalizeTicker(fields.get('ticker'));
    const asOfDate = String(fields.get('asOfDate') || '').trim();
    const asOfTime = String(fields.get('asOfTime') || '').trim();
    if (!ticker || !validProfileDate(asOfDate) || parseEtClock(asOfTime) === null) {
      state.bullflowProfile.error = 'Enter a valid ticker, session date, and Eastern as-of time before loading the sample.';
    } else {
      const sample = createBullflowProfileSample(asOfDate, ticker);
      Object.assign(state.bullflowProfile, sample, {
        ticker, asOfDate, asOfTime,
        filename: 'Synthetic 21-session sample',
        error: '',
        notice: 'Loaded a deterministic synthetic sample with one covered zero-print baseline session. Values are invented for workflow demonstration.',
      });
    }
    render();
  }
  if (name === 'finviz-demo') {
    const form = document.getElementById('finviz-contract-form');
    const fields = form ? Object.fromEntries(new FormData(form).entries()) : {};
    Object.assign(state.finvizLab, {
      rows: createFinvizContractSample(),
      filename: 'Synthetic 9-row snapshot',
      filterQuery: String(fields.filterQuery ?? state.finvizLab.filterQuery),
      order: String(fields.order ?? state.finvizLab.order),
      tickers: String(fields.tickers ?? state.finvizLab.tickers),
      error: '',
      notice: 'Loaded a deterministic synthetic snapshot, including one ETF row to illustrate stocks-universe handling. All values and supplied tags are invented.',
    });
    render();
  }
  if (name === 'stockrover-demo') {
    Object.assign(state.stockRoverLab, {
      rows: createStockRoverFactorSample(),
      filename: 'Synthetic 12-name cross-section',
      source: 'synthetic',
      error: '',
      notice: 'Loaded a deterministic synthetic snapshot; CRM intentionally has one missing forward estimate to demonstrate fail-closed category coverage.',
    });
    render();
  }
  if (name === 'stockrover-template') downloadStockRoverFactorTemplate();
  if (name === 'stockrover-export') exportStockRoverFactorAudit();
  if (name === 'static-gex-export') exportStaticGexContractAudit();
  if (name === 'strategy-demo') {
    state.strategy.rows = createDemoStrategyRows();
    state.strategy.filename = 'Generated synthetic sample';
    state.strategy.source = 'synthetic';
    state.strategy.error = '';
    state.strategy.notice = 'Loaded a deterministic 420-bar sample for workflow demonstration.';
    render();
  }
  if (name === 'strategy-save-run') saveStrategyRun();
  if (name === 'strategy-export') downloadStrategyReport();
});

document.addEventListener('change', (event) => {
  if (event.target.name === 'exerciseStyle') {
    const treeSteps = document.querySelector('#option-strategy-form [name="treeSteps"]');
    if (treeSteps) treeSteps.disabled = event.target.value !== 'american';
    return;
  }
  if (event.target.id === 'stockrover-file') {
    const file = event.target.files?.[0];
    if (file) void importStockRoverFactorCsv(file);
    return;
  }
  if (event.target.id === 'finviz-file') {
    const file = event.target.files?.[0];
    if (file) void importFinvizSnapshotCsv(file);
    return;
  }
  if (event.target.id === 'bullflow-profile-file') {
    const file = event.target.files?.[0];
    if (file) void importBullflowActivityCsv(file);
    return;
  }
  if (event.target.id === 'static-gex-file') {
    const file = event.target.files?.[0];
    if (file) void importStaticGexCsv(file);
    return;
  }
  if (event.target.id === 'portfolio-file') {
    const file = event.target.files?.[0];
    if (file) void importDanelfinPortfolioCsv(file);
    return;
  }
  if (event.target.matches('[data-portfolio-preference]')) {
    state.danelfinPortfolio.preferProvenBuy = event.target.checked;
    render();
    return;
  }
  if (event.target.matches('[data-portfolio-start-date]')) {
    const startDate = String(event.target.value || '').trim();
    if (startDate && !validProfileDate(startDate)) state.danelfinPortfolio.error = 'Portfolio start date must use YYYY-MM-DD.';
    else {
      state.danelfinPortfolio.startDate = startDate;
      state.danelfinPortfolio.error = '';
    }
    render();
    return;
  }
  if (event.target.id === 'strategy-file') {
    const file = event.target.files?.[0];
    if (file) void importStrategyCsv(file);
    return;
  }
  const filter = event.target.dataset.filter;
  if (filter) { state[filter] = event.target.value; render(); return; }
  const field = event.target.dataset.state;
  if (field) {
    if (field === 'ticker' && selectTicker(event.target.value)) render();
    if (field === 'chartSymbol') { const ticker = normalizeTicker(event.target.value); if (ticker) { state.chartSymbol = ticker; render(); } }
  }
});

document.addEventListener('submit', (event) => {
  const form = event.target;
  if (form.id === 'symbol-search') {
    event.preventDefault(); const ticker = normalizeTicker(new FormData(form).get('ticker'));
    if (ticker && selectTicker(ticker)) navigate('ticker');
  }
  if (form.id === 'watch-form') {
    event.preventDefault(); const ticker = normalizeTicker(new FormData(form).get('ticker'));
    if (ticker && !state.watchlist.includes(ticker)) state.watchlist.unshift(ticker);
    persist(); render();
  }
  if (form.id === 'alert-form') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries()); const ticker = normalizeTicker(fields.ticker);
    if (!ticker) return;
    state.alerts.unshift({ ticker, condition: fields.condition, threshold: Number(fields.threshold), type: fields.type, created: 'just now' });
    state.showAlertForm = false; persist(); render();
  }
  if (form.id === 'payoff-form') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    state.payoff = { type: fields.type, side: fields.side, strike: Number(fields.strike), premium: Number(fields.premium), contracts: Math.max(1, Number(fields.contracts)), spot: Number(fields.spot) };
    render();
  }
  if (form.id === 'option-strategy-form') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    state.optionLab.legsText = String(fields.legs || '');
    const spot = Number(fields.spot);
    const pricing = {
      daysToExpiration: Number(fields.daysToExpiration),
      volatilityPct: Number(fields.volatilityPct),
      riskFreeRatePct: Number(fields.riskFreeRatePct),
      dividendYieldPct: Number(fields.dividendYieldPct),
      exerciseStyle: String(fields.exerciseStyle || ''),
      treeSteps: fields.treeSteps === undefined ? state.optionLab.treeSteps : Number(fields.treeSteps),
    };
    try {
      if (!Number.isFinite(spot) || spot <= 0 || spot > 1e6) throw new Error('Underlying price must be greater than zero and no more than 1,000,000.');
      if (!Number.isFinite(pricing.daysToExpiration) || pricing.daysToExpiration < 0.01 || pricing.daysToExpiration > 3650) throw new Error('Days to expiration must be between 0.01 and 3,650 calendar days.');
      if (!Number.isFinite(pricing.volatilityPct) || pricing.volatilityPct < 0.1 || pricing.volatilityPct > 500) throw new Error('Shared IV must be between 0.1 and 500 percent.');
      if (!Number.isFinite(pricing.riskFreeRatePct) || pricing.riskFreeRatePct < -100 || pricing.riskFreeRatePct > 100) throw new Error('Risk-free rate must be between -100 and 100 percent.');
      if (!Number.isFinite(pricing.dividendYieldPct) || pricing.dividendYieldPct < -100 || pricing.dividendYieldPct > 100) throw new Error('Continuous yield must be between -100 and 100 percent.');
      if (pricing.exerciseStyle !== 'european' && pricing.exerciseStyle !== 'american') throw new Error('Choose European Black–Scholes or American CRR exercise.');
      if (pricing.exerciseStyle === 'american' && (!Number.isInteger(pricing.treeSteps) || pricing.treeSteps < 25 || pricing.treeSteps > 300)) throw new Error('American tree steps must be a whole number from 25 to 300.');
      const legs = parseOptionStrategyLegs(state.optionLab.legsText);
      const proposedSettings = { spot, ...pricing };
      buildOptionStrategyModel(legs, proposedSettings);
      buildOptionStrategySensitivity(legs, proposedSettings);
      Object.assign(state.optionLab, { ...proposedSettings, legs, error: '' });
    } catch (error) {
      state.optionLab.error = error instanceof Error ? error.message : 'Check the option leg inputs and try again.';
    }
    render();
  }
  if (form.id === 'strategy-config') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    state.strategy.fast = Number(fields.fast);
    state.strategy.slow = Number(fields.slow);
    state.strategy.costBps = Number(fields.costBps);
    state.strategy.splitPct = Number(fields.splitPct);
    state.strategy.periodsPerYear = Number(fields.periodsPerYear);
    state.strategy.error = '';
    state.strategy.notice = '';
    persist(); render();
  }
  if (form.id === 'static-gex-config') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    const values = {
      riskFreeRatePct: Number(fields.riskFreeRatePct),
      dividendYieldPct: Number(fields.dividendYieldPct),
      multiplier: Number(fields.multiplier),
      gridRangePct: Number(fields.gridRangePct),
    };
    if (!Object.values(values).every(Number.isFinite) || values.riskFreeRatePct < -10 || values.riskFreeRatePct > 40 || values.dividendYieldPct < -10 || values.dividendYieldPct > 40 || !Number.isInteger(values.multiplier) || values.multiplier < 1 || values.multiplier > 10000 || values.gridRangePct < 5 || values.gridRangePct > 50) {
      state.staticGex.error = 'Check the pricing assumptions: rates must be −10% to 40%, multiplier 1–10,000, and grid range 5–50%.';
      render();
      return;
    }
    Object.assign(state.staticGex, values, { error: '', notice: 'Recalculated using the displayed Black–Scholes and constant-IV assumptions.' });
    render();
  }
  if (form.id === 'azrael-map-form') {
    event.preventDefault();
    const fields = Object.fromEntries(new FormData(form).entries());
    const values = {
      anchorClose: Number(fields.anchorClose),
      vixClose: Number(fields.vixClose),
      elapsedMinutes: Number(fields.elapsedMinutes),
      sessionMinutes: Number(fields.sessionMinutes),
      candidateTarget: String(fields.candidateTarget ?? '').trim(),
    };
    const result = buildAzraelMap(values);
    Object.assign(state.azraelMap, values, { error: result.error || '' });
    render();
  }
  if (form.id === 'bullflow-profile-config') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    const ticker = normalizeTicker(fields.ticker);
    const asOfDate = String(fields.asOfDate || '').trim();
    const asOfTime = String(fields.asOfTime || '').trim();
    if (!ticker || !validProfileDate(asOfDate) || parseEtClock(asOfTime) === null) {
      state.bullflowProfile.error = 'Enter a valid ticker, session date, and Eastern as-of time.';
      render();
      return;
    }
    Object.assign(state.bullflowProfile, { ticker, asOfDate, asOfTime, error: '', notice: '' });
    render();
  }
  if (form.id === 'finviz-contract-form') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    Object.assign(state.finvizLab, {
      filterQuery: String(fields.filterQuery || '').trim(),
      order: String(fields.order || 'ticker').trim(),
      tickers: String(fields.tickers || '').trim(),
      error: '',
      notice: '',
    });
    render();
  }
  if (form.id === 'confluence-effective-form') {
    event.preventDefault();
    const fields = new FormData(form);
    const effectiveScores = {};
    for (const category of confluenceEffectiveCategories) {
      if (category.externalFramework) continue;
      for (const [key] of category.leaves) effectiveScores[key] = fields.get(key) ?? '';
    }
    state.confluence = {
      ...state.confluence,
      effectiveScores,
      qualified: fields.get('qualified') === 'true',
      dataConfidence: fields.get('dataConfidence') ?? '',
      realIndexCount: fields.get('realIndexCount') ?? '',
    };
    persist(); render();
  }
  if (form.id === 'confluence-form') {
    event.preventDefault();
    const fields = new FormData(form);
    const scores = {};
    for (const category of confluenceCategories) {
      for (const [key] of category.metrics) scores[key] = fields.get(key) ?? '';
    }
    state.confluence = {
      ...state.confluence,
      scores,
      qualified: fields.get('qualified') === 'true',
      dataConfidence: fields.get('dataConfidence') ?? '',
      realIndexCount: fields.get('realIndexCount') ?? '',
    };
    persist(); render();
  }
});

document.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); document.getElementById('global-symbol')?.focus(); }
  if (event.key === 'Escape') document.querySelector('.app-shell')?.classList.remove('mobile-nav-open', 'chart-fullscreen');
  if (event.target?.id === 'global-symbol' && event.key === 'Enter') {
    event.preventDefault(); const ticker = normalizeTicker(event.target.value); if (ticker && selectTicker(ticker)) navigate('ticker');
  }
});

window.addEventListener('popstate', () => { state.view = location.hash.slice(1) || 'overview'; render(); });
state.strategy.rows = createDemoStrategyRows();
state.danelfinPortfolio.rows = createDanelfinDemoRows();
state.staticGex.rows = createStaticGexDemoRows();
render();
fetch('./vendor-coverage.json', { headers: { Accept: 'application/json' } })
  .then(response => { if (!response.ok) throw new Error('Could not load the local family registry.'); return response.json(); })
  .then(registry => {
    state.vendorFamilies = Array.isArray(registry.families) ? registry.families : [];
    state.vendorCoverageMeta = { requestedPasses: registry.requestedPasses || 99, targetFamilies: registry.targetFamilies || 86, asOf: registry.asOf };
    if (state.view === 'coverage') render();
  })
  .catch(() => {
    state.coverageError = 'The local 86-family registry could not be loaded.';
    if (state.view === 'coverage') render();
  });
fetch('/api/status', { headers: { Accept: 'application/json' } }).then(r => r.json()).then(s => { state.apiStatus = s; }).catch(() => { state.apiStatus = { mode: 'demo', provider: 'Local server not detected', keyConfigured: false, allowedReads: [] }; });
