const root = document.getElementById('app');
const KEY = 'shipyard-research-terminal:v1';
const safeStored = (() => {
  try {
    const value = JSON.parse(localStorage.getItem(KEY) || '{}');
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  } catch { return {}; }
})();

function marketContextFreshness(asOf, now = new Date()) {
  if (typeof asOf !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(asOf)) {
    return { state: 'unknown', ageDays: null, label: 'FRESHNESS UNKNOWN' };
  }
  const asOfTimestamp = Date.parse(`${asOf}T00:00:00.000Z`);
  if (!Number.isFinite(asOfTimestamp) || new Date(asOfTimestamp).toISOString().slice(0, 10) !== asOf) {
    return { state: 'unknown', ageDays: null, label: 'FRESHNESS UNKNOWN' };
  }
  const today = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now).map(({ type, value }) => [type, value]));
  const todayTimestamp = Date.parse(`${today.year}-${today.month}-${today.day}T00:00:00.000Z`);
  if (!Number.isFinite(todayTimestamp)) return { state: 'unknown', ageDays: null, label: 'FRESHNESS UNKNOWN' };
  const ageDays = Math.floor((todayTimestamp - asOfTimestamp) / 86400000);
  if (ageDays < 0) return { state: 'future', ageDays, label: 'FUTURE-DATED · REVIEW' };
  if (ageDays > 3) return { state: 'stale', ageDays, label: `STALE · ${ageDays} DAYS OLD` };
  if (ageDays === 0) return { state: 'fresh', ageDays, label: 'CURRENT · 0 DAYS OLD' };
  return { state: 'fresh', ageDays, label: `FRESH · ${ageDays} ${ageDays === 1 ? 'DAY' : 'DAYS'} OLD` };
}

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

function normalizeVendorCoverageMeta(registry) {
  return {
    requestedPasses: Number.isInteger(registry?.requestedPasses) && registry.requestedPasses > 0 ? registry.requestedPasses : 100,
    requestedNames: Number.isInteger(registry?.requestedNames) && registry.requestedNames > 0 ? registry.requestedNames : 92,
    targetFamilies: Number.isInteger(registry?.targetFamilies) && registry.targetFamilies > 0 ? registry.targetFamilies : 86,
    asOf: typeof registry?.asOf === 'string' ? registry.asOf : undefined,
  };
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
  view: location.hash.slice(1) || 'brain',
  ticker: storedTicker,
  flowSearch: '', flowType: 'all', flowSide: 'all', minPremium: 0, flowSort: 'time',
  dpTicker: '', disclosureSearch: '', screenerSector: 'all', screenerType: 'all',
  newsSearch: '', calendarRange: 'week', gexBasis: 'vol', chartRange: '1D',
  dataMode: 'live', chartSymbol: storedTicker, showAlertForm: false,
  tradeBrainRiskBudget: Number.isFinite(Number(safeStored.tradeBrainRiskBudget)) && Number(safeStored.tradeBrainRiskBudget) > 0 ? Number(safeStored.tradeBrainRiskBudget) : 0,
  tradeBrain: { status: 'idle', scans: {}, scanning: false, lastScanAt: null, liveQuotes: {}, streamStatus: 'idle', streamFeed: 'sip', streamError: '' },
  marketContext: { status: 'idle', value: null, error: '' },
  alpacaFeed: { symbol: storedTicker, days: 90, bars: [], status: 'idle', receivedAt: null, asOf: null, refreshing: false, refreshError: '', error: '' },
  enginePipeline: { status: 'idle', ranAt: null },
  engineEvidence: { status: 'idle', bundle: null, error: '' },
  morgueReadiness: { status: 'idle', value: null, error: '' },
  watchlist: Array.isArray(safeStored.watchlist) ? safeStored.watchlist : ['SPY', 'NVDA', 'AAPL', 'TSLA'],
  savedTrades: Array.isArray(safeStored.savedTrades) ? safeStored.savedTrades : [],
  alerts: Array.isArray(safeStored.alerts) ? safeStored.alerts : [],
  savedLayouts: Array.isArray(safeStored.savedLayouts) ? safeStored.savedLayouts : [],
  strategy: {
    rows: [],
    filename: 'No CSV loaded',
    source: 'none',
    fast: Number(safeStored.strategyConfig?.fast) || 20,
    slow: Number(safeStored.strategyConfig?.slow) || 50,
    costBps: Number(safeStored.strategyConfig?.costBps ?? 5),
    splitPct: Number(safeStored.strategyConfig?.splitPct) || 70,
    periodsPerYear: Number(safeStored.strategyConfig?.periodsPerYear) || 252,
    artifactSha256: null,
    evidence: null,
    evidenceError: '',
    error: '',
    notice: '',
  },
  strategyRuns: Array.isArray(safeStored.strategyRuns) ? safeStored.strategyRuns : [],
  confluence: initialConfluence,
  confluenceByTicker,
  confluenceMode: safeStored.confluenceMode === 'effective' ? 'effective' : 'metadata',
  danelfinPortfolio: {
    rows: [],
    filename: 'No CSV loaded',
    source: 'none',
    error: '',
    notice: '',
    provenBuyProvided: true,
    preferProvenBuy: true,
    asOf: '',
    startDate: '',
  },
  staticGex: {
    rows: [],
    filename: 'No CSV loaded',
    source: 'none',
    error: '',
    notice: '',
    ticker: 'SPY',
    asOf: '',
    spot: null,
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
    anchorClose: null,
    vixClose: null,
    elapsedMinutes: null,
    sessionMinutes: null,
    candidateTarget: null,
    error: '',
  },
  vendorFamilies: [],
  vendorCoverageMeta: { requestedPasses: 100, requestedNames: 92, targetFamilies: 86 },
  coverageError: '',
  vendorSearch: '',
  vendorLane: 'all',
  vendorResearch: 'all',
  convergenceSearch: '',
  convergenceImport: { status: 'idle', filename: '', records: [], rejected: [], headers: [], importedAt: null, error: '' },
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
    evidence: null,
    evidenceError: '',
  },
};

function persist() {
  if (confluenceHasValues(state.confluence)) state.confluenceByTicker[state.ticker] = state.confluence;
  else delete state.confluenceByTicker[state.ticker];
  localStorage.setItem(KEY, JSON.stringify({
    ticker: state.ticker,
    watchlist: state.watchlist,
    savedTrades: state.savedTrades,
    alerts: state.alerts,
    tradeBrainRiskBudget: state.tradeBrainRiskBudget,
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
  { heading: 'TRADE', items: [['brain', 'Trade Brain', '✳', 'SCAN'], ['watchlists', 'My watchlist', '☆'], ['alerts', 'Alerts', '♧']] },
  { heading: 'MARKETS', items: [['overview', 'Market overview', '⌂'], ['context', 'Market context', '◌'], ['alpaca', 'Daily charts', '⌁']] },
  { heading: 'RESEARCH', items: [['enginehub', 'Research suite', '⟁']] },
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
  const pageTitle = ({ brain: 'Trade Brain', enginehub: 'Research engine suite', context: 'Market Context & Chartlector', alpaca: 'Alpaca market data', overview: 'Market overview', flow: 'Options flow', gex: 'GEX & Greeks', staticgex: 'Static GEX Lab', azrael: '15.87 Rule map', optionlab: 'Option strategy lab', bullflow: 'Options activity profile', finviz: 'Finviz filter contract lab', stockrover: 'Stock Rover factor lab', darkpool: 'Dark-pool activity', screener: 'Market screeners', charts: 'Chart workspace', congress: 'Congress trades', insiders: 'Insider activity', calendar: 'Event calendar', news: 'News flow', ticker: `${state.ticker} research`, confluence: 'Confluence lab', portfolio: 'Sector portfolio lab', watchlists: 'Watchlists', alerts: 'Alert rules', tools: 'Research tools', strategy: 'Strategy lab', coverage: 'Vendor coverage', evidence: 'Evidence graph', convergence: 'Convergence engine', api: 'Data connection' })[state.view] || 'Market overview';
  const dataBanner = '';
  const nav = navGroups.map(group => `<div class="nav-group"><div class="nav-heading">${group.heading}</div>${group.items.map(([view, title, glyph, tag]) => `<button class="nav-item ${activeNav(view) ? 'active' : ''}" data-view="${view}">${icon(glyph)}<span>${title}</span>${tag ? `<span class="nav-live">${tag}</span>` : ''}</button>`).join('')}</div>`).join('');
  const content = renderPage();
  root.innerHTML = `<div class="app-shell ${state.theme === 'light' ? 'light-theme' : ''}">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">S</span><span class="brand-name">shipyard<span> / research</span></span><button class="collapse-button" data-action="collapse-sidebar" aria-label="Collapse sidebar">‹</button></div>
      <div class="workspace-select"><span class="workspace-dot"></span><span>Personal research workspace</span><span class="chevron">⌄</span></div>
      <button class="overview-shortcut" data-view="overview">${icon('⌂')} Home <span>⌘ 1</span></button>
      ${nav}
      <div class="sidebar-bottom">
        <div class="workspace-card"><div class="workspace-card-top"><span class="workspace-dot"></span>BROWSER WORKSPACE</div><p>Your lists and alerts are stored in this browser.</p><button class="text-button" data-view="api">Data source settings <span>→</span></button></div>
        <button class="nav-item" data-view="api">${icon('⚙')}<span>Settings & API</span></button>
        <div class="profile-row"><div class="avatar">S</div><div><b>Owner</b><small>Personal terminal</small></div><span class="chevron">···</span></div>
      </div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <button class="mobile-menu" data-action="mobile-menu" aria-label="Open menu">☰</button>
        <div class="breadcrumbs"><span>Workspace</span><span class="slash">/</span><b>${esc(pageTitle)}</b></div>
        <div class="topbar-actions">
          <form class="symbol-search" id="symbol-search"><span>⌕</span><input id="global-symbol" name="ticker" aria-label="Search ticker" placeholder="Search ticker or tool" value="${esc(state.ticker)}" /><kbd>⌘ K</kbd></form>
          <div class="market-session"><span class="session-dot"></span><span>READ-ONLY DATA</span></div>
          <button class="icon-button theme-toggle" data-action="theme" aria-label="Toggle theme">${state.theme === 'dark' ? '☼' : '☾'}</button>
          <button class="avatar small-avatar" aria-label="Local profile">SJ</button>
        </div>
      </header>
      ${dataBanner}
      <section class="page-content">${content}</section>
      <footer class="app-footer"><span>Shipyard Research Terminal</span><span><button data-view="api">Data sources</button></span></footer>
    </main>
  </div>`;
  document.documentElement.dataset.theme = state.theme;
}

function renderPage() {
  const disconnectedFeeds = {
    flow: ['Options flow', 'Live transaction-level options prints are not connected. Trade Brain evaluates Alpaca indicative option quotes only.'],
    gex: ['GEX & Greeks', 'A complete, sourced options inventory feed is not connected for strike exposure calculations.'],
    darkpool: ['Dark-pool prints', 'No live off-exchange or ATS print feed is connected.'],
    congress: ['Congress trades', 'No live official congressional disclosure feed is connected.'],
    insiders: ['Insider activity', 'No live SEC Form 4 feed is connected.'],
    screener: ['Market screener', 'A live market-wide symbol and fundamentals feed is not connected. Trade Brain scans your browser watchlist.'],
    calendar: ['Event calendar', 'No live earnings or economic event feed is connected.'],
    news: ['News flow', 'No live news feed is connected.'],
    azrael: ['15.87 Rule map', 'This map requires fresh, sourced VIX and underlying inputs; this terminal does not yet connect those inputs to this calculation.'],
    optionlab: ['Option strategy lab', 'The pricing form uses manual assumptions rather than live quotes. Use Trade Brain for provider-priced live contracts.'],
    tools: ['Options tools', 'Manual payoff tools are not connected to live option quotes. Use Trade Brain for current contracts and prices.'],
  };
  if (disconnectedFeeds[state.view]) return renderFeedUnavailable(...disconnectedFeeds[state.view]);
  if (state.view === 'ticker') return renderLiveTicker();
  const pages = { brain: renderTradeBrain, enginehub: renderEngineHub, context: renderChartlector, alpaca: renderAlpaca, overview: renderOverview, flow: renderFlow, gex: renderGex, staticgex: renderStaticGexLab, azrael: renderAzraelMapLab, optionlab: renderOptionStrategyLab, bullflow: renderBullflowActivityProfile, finviz: renderFinvizContractLab, stockrover: renderStockRoverFactorLab, darkpool: renderDarkpool, congress: () => renderDisclosures('congress'), insiders: () => renderDisclosures('insiders'), screener: renderScreener, calendar: renderCalendar, news: renderNews, ticker: renderTicker, confluence: renderConfluenceLab, portfolio: renderDanelfinPortfolioLab, charts: renderCharts, watchlists: renderWatchlists, alerts: renderAlerts, tools: renderTools, strategy: renderStrategyLab, coverage: renderVendorCoverage, convergence: renderConvergenceEngine, evidence: renderEvidenceGraph, api: renderApi };
  return (pages[state.view] || renderOverview)();
}

function renderFeedUnavailable(title, message) {
  return `${pageHeading('LIVE DATA', esc(title), esc(message), '<button class="button primary" data-view="brain">Open Trade Brain</button>')}${panel('Feed status', 'No provider data returned for this view.', '<div class="empty-state compact"><b>No live records</b><p>This view will show data after its provider feed is connected.</p></div>', '')}`;
}

function renderLiveTicker() {
  const feed = state.alpacaFeed;
  const selection = window.SiliconResearchAdapters?.selectCompletedDailyBars?.(feed.bars || [], new Date(), feed.value?.session_calendar) || { bars: feed.bars || [] };
  const bars = selection.bars;
  const latest = bars.at(-1), previous = bars.at(-2);
  const change = latest && previous ? (latest.close / previous.close - 1) * 100 : null;
  const body = bars.slice(-20).reverse().map((bar) => `<tr><td>${esc(marketSessionDate(bar.at, { year: 'numeric' }))}</td><td>${money(bar.open)}</td><td>${money(bar.high)}</td><td>${money(bar.low)}</td><td>${money(bar.close)}</td><td>${integer(Math.round(bar.volume))}</td></tr>`).join('');
  const chart = bars.length > 1 ? lineChart([{ values: bars.slice(-60).map((bar) => bar.close), color: '#42d6ab', fill: true, label: 'Close' }], { axis: '$', decimals: 2, xLabels: [marketSessionDate(bars.at(-60)?.at || bars[0].at), marketSessionDate(latest.at)] }) : '<div class="empty-state">Waiting for live Alpaca history.</div>';
  const status = feed.status === 'loading' ? 'Loading Alpaca IEX daily history…' : feed.status === 'unavailable' ? `Unavailable · ${esc(feed.error || 'provider request failed')}` : latest ? `Alpaca IEX · completed daily bars through ${esc(marketSessionDate(latest.at, { year: 'numeric' }))}` : 'No live daily bars are available.';
  return `${pageHeading('ALPACA · IEX DAILY', `${esc(state.ticker)} research`, 'Completed split-adjusted daily bars. Open Trade Brain for current stock and option quotes.', '<button class="button primary" data-view="brain">Open Trade Brain</button>')}
    <div class="flow-summary-grid">${statCard('LATEST COMPLETED CLOSE', latest ? money(latest.close) : '—', latest ? marketSessionDate(latest.at, { year: 'numeric' }) : status, null, '⌖')}${statCard('DAILY CHANGE', change === null ? '—' : pct(change), 'completed close vs prior close', change, '↕')}${statCard('SMA 20', formatFeedNumber(window.SiliconResearchAdapters?.simpleMovingAverage?.(bars.map((bar) => bar.close), 20) ?? NaN), 'completed daily bars', null, '⌁')}${statCard('SMA 50', formatFeedNumber(window.SiliconResearchAdapters?.simpleMovingAverage?.(bars.map((bar) => bar.close), 50) ?? NaN), 'completed daily bars', null, '⌁')}</div>
    ${panel('Daily price history', status, chart, '<button class="button secondary" data-action="refresh-alpaca-bars">Refresh</button>')}
    ${panel('Recent completed sessions', 'Provider bars only · IEX feed', `<div class="table-wrap"><table class="data-table"><thead><tr><th>SESSION</th><th>OPEN</th><th>HIGH</th><th>LOW</th><th>CLOSE</th><th>VOLUME</th></tr></thead><tbody>${body || '<tr><td colspan="6">No completed daily bars loaded.</td></tr>'}</tbody></table></div>`)}`;
}

function renderEngineHub() {
  const feed = state.alpacaFeed || {};
  const bars = Array.isArray(feed.bars) ? feed.bars : [];
  const selector = window.SiliconResearchAdapters?.selectCompletedDailyBars;
  const barSelection = selector ? selector(bars, new Date(), feed.value?.session_calendar) : { bars, currentSessionBarExcluded: false };
  const calculationBars = barSelection.bars;
  const context = state.marketContext?.value?.context || {};
  const market = state.marketContext?.value;
  const indicators = window.SiliconResearchAdapters;
  const closes = calculationBars.map(row => Number(row.close)).filter(Number.isFinite);
  const sma20 = indicators?.simpleMovingAverage?.(closes, 20) ?? null;
  const sma50 = indicators?.simpleMovingAverage?.(closes, 50) ?? null;
  const last = calculationBars.at(-1);
  const prior = calculationBars.at(-2);
  const dailyMove = last && prior && Number(prior.close) !== 0 ? (Number(last.close) / Number(prior.close) - 1) * 100 : null;
  const rsi14 = indicators?.simpleRsi14?.(closes) ?? null;
  const atr14 = indicators?.simpleAtr14?.(calculationBars) ?? null;
  const pipeline = state.enginePipeline || { status: 'idle', ranAt: null };
  const evidence = state.engineEvidence || { status: 'idle', bundle: null, error: '' };
  const running = pipeline.status === 'loading' || evidence.status === 'loading';
  const sourcesLoading = feed.status === 'loading' || state.marketContext?.status === 'loading';
  const runLabel = running || sourcesLoading ? 'Loading sources…' : 'Run integrated research snapshot';
  const contextFreshness = marketContextFreshness(market?.as_of);
  const contextAgeDays = contextFreshness.ageDays;
  const contextAgeCaption = contextFreshness.state === 'future' ? ' · future-dated' : Number.isInteger(contextAgeDays) ? ` · ${contextAgeDays} calendar ${contextAgeDays === 1 ? 'day' : 'days'} old` : ' · freshness unknown';
  const contextStatus = market ? `Loaded · ${market.as_of || 'date not supplied'}${contextAgeCaption}` : state.marketContext?.status === 'loading' ? 'Loading' : state.marketContext?.error || 'Not loaded';
  const barsStatus = feed.status === 'connected' ? `Loaded · ${bars.length} returned / ${calculationBars.length} calculation bars · ${feed.asOf ? marketSessionDate(feed.asOf, { year: 'numeric' }) : 'date not supplied'}${barSelection.currentSessionBarExcluded ? ' · current-session bar excluded' : barSelection.nonTradingDateBarExcluded ? ' · non-session date bar excluded' : ''}` : feed.status === 'loading' ? 'Loading' : feed.error || 'Not loaded';
  const trend = sma20 === null || sma50 === null ? 'Needs ≥50 bars' : Number(last?.close) > sma20 && sma20 > sma50 ? 'Close > SMA20 > SMA50' : Number(last?.close) < sma20 && sma20 < sma50 ? 'Close < SMA20 < SMA50' : 'Mixed moving-average state';
  const workflowCards = [
    ['Macro context & Chartlector', 'Published regime, breadth, themes, volatility, rates and macro series.', 'context', market ? (contextFreshness.state === 'fresh' ? 'READY · PUBLIC DATA' : contextFreshness.label) : 'LOAD SOURCE'],
    ['Price, indicators & charts', 'Alpaca IEX daily bars, OHLCV, SMA20/50, RSI14 and ATR14.', 'alpaca', feed.status === 'connected' ? 'READY · DAILY BARS' : 'LOAD SOURCE'],
    ['Screening & factor research', 'Local screeners, the Finviz query contract, factor profiles and sector portfolio construction.', 'screener', 'LOCAL / USER INPUT'],
    ['Options & positioning labs', 'Payoff scenarios, static GEX, activity profiles and the 15.87 Rule map.', 'optionlab', 'LOCAL / USER INPUT'],
    ['Strategy replay & watchlists', 'CSV replay, browser-local lists and manually evaluated daily-move alerts.', 'strategy', 'BROWSER LOCAL'],
    ['Evidence & vendor coverage', '86-family registry, provenance links, implementation gaps and dependency graph.', 'coverage', 'RESEARCH REGISTRY'],
  ];
  const workflowMarkup = workflowCards.map(([title, description, route, stateLabel]) => `<article class="coverage-vendor"><div class="coverage-vendor-top"><span class="coverage-state coverage-local">${esc(stateLabel)}</span></div><h3>${esc(title)}</h3><p>${esc(description)}</p><button class="text-button" data-view="${esc(route)}">Open module →</button></article>`).join('');
  const pythonEngines = [
    ['Saty Adaptive Opportunity Engine v0.3.0', 'Python research/paper engine with independent setup families, deterministic ranking, causal context, event guards and risk controls. Requires its Python runtime and documented multitimeframe inputs.', 'https://github.com/dwj9ddyvf6-hub/Silicon/tree/main/research/saty_mahajan'],
    ['Raschke Research Engine v0.2.0', 'Python research/paper engine with canonical setup rules, context routing and a paper-only execution kernel. The Site Worker does not run its broker or SQLite lifecycle.', 'https://github.com/dwj9ddyvf6-hub/Silicon/tree/main/research/linda_raschke/v02'],
    ['Morgue Engine', 'Python data pipeline for positioning, tape, disclosures and confluence. External providers, options feeds and point-in-time inputs are not configured in this public Site.', 'https://github.com/dwj9ddyvf6-hub/Silicon/tree/main/research/morgue-engine'],
    ['ChartsLector research systems', 'Python ranker, breadth, themes and pulse studies. This terminal loads its published context feed; it does not execute the separate research package.', 'https://github.com/dwj9ddyvf6-hub/Silicon/tree/main/research/lector-systems'],
  ];
  const pythonMarkup = pythonEngines.map(([title, description, link]) => `<article class="coverage-vendor"><div class="coverage-vendor-top"><span class="coverage-state coverage-partial">PYTHON PACKAGE · SITE RUNTIME NOT CONNECTED</span></div><h3>${esc(title)}</h3><p>${esc(description)}</p><a href="${esc(link)}" target="_blank" rel="noopener noreferrer">Open source and run guide ↗</a></article>`).join('');
  const morgue = state.morgueReadiness || { status: 'idle', value: null, error: '' };
  const morgueValue = morgue.value;
  const morgueSnapshot = morgueValue?.snapshot;
  const morgueStateLabel = morgue.status === 'loading' ? 'CHECKING PUBLIC SNAPSHOT…'
    : morgueValue?.status === 'available' ? 'FEED PRESENT · METADATA ONLY'
      : morgueValue?.status === 'partial' ? 'PARTIAL SNAPSHOT'
        : morgueValue?.status === 'invalid' ? 'SOURCE SCHEMA INVALID'
          : morgue.status === 'unavailable' || morgueValue?.status === 'unavailable' ? 'SOURCE UNAVAILABLE'
            : 'NOT CHECKED';
  const morguePanel = `<section class="panel engine-pipeline-panel"><div class="panel-heading"><div><h2>Morgue snapshot intake</h2><p>Read-only provenance and section-presence adapter for a feed pinned to its source commit. Snapshot values are not copied into this Site.</p></div><button class="button secondary" data-action="refresh-morgue-readiness" ${morgue.status === 'loading' ? 'disabled' : ''}>${morgue.status === 'loading' ? 'Checking…' : 'Check snapshot'}</button></div>
      <div class="flow-summary-grid engine-result-grid">${statCard('FEED STATUS', morgueStateLabel, 'Morgue snapshot source', null, '◈')}${statCard('AS OF SESSION', morgueSnapshot?.as_of_session || '—', morgueSnapshot?.generated_at_utc ? `generated ${utcTimestamp(morgueSnapshot.generated_at_utc)}` : 'No validated artifact', null, '◷')}${statCard('SECTIONS', morgueSnapshot ? `${morgueSnapshot.present_section_count}/${morgueSnapshot.expected_section_count}` : '—', morgueSnapshot?.missing_sections?.length ? `missing: ${morgueSnapshot.missing_sections.join(', ')}` : 'presence only · freshness unknown', null, '▦')}${statCard('ARTIFACT SHA-256', morgueSnapshot?.sha256 ? morgueSnapshot.sha256.slice(0, 16) : '—', 'hash of received public feed', null, '#')}</div>
      ${morgue.error ? `<div class="optionlab-error" role="status">${esc(morgue.error)}</div>` : ''}<div class="evidence-callout"><b>Eligibility gates stay closed</b><span>Source rights, freshness budget, and point-in-time validation are unresolved. No market values, decisions, performance claims, or orders are returned.</span><a href="${esc(morgueValue?.source_url || 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/morgue-engine/output/morgue-feed.json')}" target="_blank" rel="noopener noreferrer">Open source artifact ↗</a></div></section>`;
  const runTime = pipeline.ranAt ? new Date(pipeline.ranAt).toLocaleString() : 'Not run in this browser session';
  const pipelineState = pipeline.status === 'ready' ? (contextFreshness.state === 'fresh' ? 'DATA LOADED' : contextFreshness.state === 'stale' ? 'DATA LOADED · CONTEXT STALE' : contextFreshness.state === 'future' ? 'DATA LOADED · FUTURE-DATED CONTEXT' : 'DATA LOADED · CONTEXT FRESHNESS UNKNOWN') : pipeline.status === 'partial' ? 'PARTIAL DATA' : pipeline.status === 'unavailable' ? 'SOURCES UNAVAILABLE' : running ? 'RUNNING' : 'NOT RUN';
  const contextFields = context.mood || {};
  const breadth = context.breadth || {};
  const volatility = context.market_volatility?.indices || {};
  const systemError = [state.marketContext?.error, feed.status === 'unavailable' ? feed.error : ''].filter(Boolean).join(' · ');
  return `${pageHeading('INTEGRATED RESEARCH WORKSPACE', 'Research engine suite', 'Run a read-only snapshot across the public market-context feed and Alpaca daily bars. The evidence layer records provenance, validation, and unresolved eligibility gates.', `<button class="button primary" data-action="run-research-pipeline" ${running || sourcesLoading ? 'disabled' : ''}>${runLabel}</button>`)}
    <section class="panel engine-pipeline-panel"><div class="panel-heading"><div><h2>Integrated market snapshot</h2><p>One request refreshes Chartlector context and one symbol of Alpaca IEX daily bars. Indicator calculations stay in this browser.</p></div><span class="coverage-state ${pipeline.status === 'ready' && contextFreshness.state === 'fresh' ? 'coverage-local' : pipeline.status === 'ready' || pipeline.status === 'partial' ? 'coverage-partial' : 'coverage-none'}">${esc(pipelineState)}</span></div>
      <div class="activity-controls"><label class="field-label">SYMBOL<input data-engine-symbol value="${esc(feed.symbol || state.ticker)}" maxlength="10" pattern="[A-Za-z0-9.-]{1,10}" /></label><label class="field-label">HISTORY<select data-engine-days>${[20,60,90,180].map(days => `<option value="${days}" ${Number(feed.days) === days ? 'selected' : ''}>${days} calendar days</option>`).join('')}</select></label><div class="engine-source-state"><b>Chartlector</b><span>${esc(contextStatus)}</span></div><div class="engine-source-state"><b>Alpaca IEX</b><span>${esc(barsStatus)}</span></div></div>
      ${systemError ? `<div class="optionlab-error" role="alert">${esc(systemError)}</div>` : ''}
      <div class="flow-summary-grid engine-result-grid">${statCard('LAST CLOSE', last ? `$${formatFeedNumber(Number(last.close))}` : '—', last ? `${esc(feed.symbol || state.ticker)} · ${marketSessionDate(last.at, { year: 'numeric' })}` : 'Load Alpaca bars', null, '◈')}${statCard('DAILY CHANGE', dailyMove === null ? '—' : pct(dailyMove), 'prior available close', null, '↗')}${statCard('TREND STRUCTURE', trend, 'close and SMA20/50 relation', null, '⌁')}${statCard('RSI 14', formatFeedNumber(rsi14, 1), 'simple mean-gain / mean-loss', null, '◈')}${statCard('ATR 14', atr14 === null ? '—' : `$${formatFeedNumber(atr14)}`, 'mean true range · daily bars', null, '↕')}${statCard('VIX', volatility.VIX ? formatFeedNumber(volatility.VIX.close) : '—', volatility.VIX?.as_of ? `as of ${volatility.VIX.as_of}` : 'not in latest context', null, '◉')}</div>
      <div class="table-bottom"><span>Context: ${esc(market?.as_of || 'not loaded')}</span><span>Breadth &gt; 50D: ${breadth.current?.pct50 == null ? '—' : `${formatFeedNumber(breadth.current.pct50, 1)}%`}</span><span>Last pipeline run: ${esc(runTime)}</span></div>
      <div class="privacy-footnote"><b>Method</b><span>One read-only snapshot combines published market context, Alpaca daily bars, and browser-calculated indicators.</span></div>
    </section>
    ${renderResearchEvidencePanel(evidence)}
    ${panel('Browser-ready product modules', 'These workflows run in the Site using public feeds or browser-local inputs.', `<div class="coverage-lane-grid">${workflowMarkup}</div>`, '')}
    ${panel('Research engines with a separate Python runtime', 'The source packages and run guides are available in the Silicon repository. This Site Worker runs JavaScript and currently does not invoke those Python engines.', `<div class="coverage-lane-grid">${pythonMarkup}</div><div class="evidence-callout"><b>Runtime status</b><span>These Python packages are linked from the source repo but do not run on this Site. On-site use needs a supervised Python service and read-only adapter.</span></div>`, '')}
    ${morguePanel}
    ${panel('Quick access to specialist tools', 'The research components remain separate so each calculation retains its own source, input contract and limitations.', `<div class="engine-quick-links"><button class="button secondary" data-view="confluence">Confluence lab</button><button class="button secondary" data-view="staticgex">Static GEX</button><button class="button secondary" data-view="azrael">15.87 Rule map</button><button class="button secondary" data-view="optionlab">Option strategy</button><button class="button secondary" data-view="bullflow">Activity profile</button><button class="button secondary" data-view="finviz">Filter contract</button><button class="button secondary" data-view="stockrover">Factor profile</button><button class="button secondary" data-view="evidence">Evidence graph</button><button class="button secondary" data-view="alerts">Alert rules</button></div>`, '')}`;
}

async function runResearchPipeline() {
  if (state.alpacaFeed.status === 'loading' || state.marketContext?.status === 'loading') return;
  const input = document.querySelector('[data-engine-symbol]');
  const period = Number(document.querySelector('[data-engine-days]')?.value || state.alpacaFeed.days);
  const symbol = normalizeTicker(input?.value || state.alpacaFeed.symbol || state.ticker);
  if (!symbol || ![20, 60, 90, 180].includes(period)) {
    state.enginePipeline = { status: 'unavailable', ranAt: new Date().toISOString() };
    state.engineEvidence = { status: 'unavailable', bundle: null, error: 'Enter a valid symbol and supported history range.' };
    render();
    return;
  }
  state.enginePipeline = { status: 'loading', ranAt: null };
  state.engineEvidence = { status: 'loading', bundle: null, error: '' };
  state.alpacaFeed = { ...state.alpacaFeed, symbol, days: period };
  render();
  await Promise.all([loadMarketContext(), loadAlpacaBars(symbol, period)]);
  const hasContext = Boolean(state.marketContext?.value);
  const hasBars = state.alpacaFeed?.status === 'connected' && state.alpacaFeed.bars.length > 0;
  if (hasBars) {
    try {
      const adapters = window.SiliconResearchAdapters;
      if (!adapters?.buildAlpacaResearchEvidence) throw new Error('The browser research adapter did not load.');
      const bundle = await adapters.buildAlpacaResearchEvidence({
        symbol,
        bars: state.alpacaFeed.bars,
        receivedAt: state.alpacaFeed.receivedAt,
        requestedDays: period,
        context: state.marketContext?.value,
        sessionCalendar: state.alpacaFeed.value?.session_calendar || null,
      });
      state.engineEvidence = { status: 'ready', bundle, error: '' };
    } catch (error) {
      state.engineEvidence = { status: 'error', bundle: null, error: error instanceof Error ? error.message : 'Could not create the evidence bundle.' };
    }
  } else {
    state.engineEvidence = { status: 'unavailable', bundle: null, error: 'Load valid Alpaca daily bars before creating a market evidence bundle.' };
  }
  state.enginePipeline = { status: hasContext && hasBars ? 'ready' : hasContext || hasBars ? 'partial' : 'unavailable', ranAt: new Date().toISOString() };
  render();
}

function renderResearchEvidencePanel(evidence) {
  const bundle = evidence?.bundle;
  if (!bundle) {
    const stateLabel = evidence?.status === 'loading' ? 'Building source records…' : evidence?.status === 'error' ? 'Evidence build failed' : 'Waiting for the integrated snapshot';
    const detail = evidence?.error || 'Run the integrated snapshot to validate daily bars against the evidence contract. Records remain in this browser tab.';
    return panel('Evidence, provenance & eligibility', stateLabel, `<div class="evidence-callout"><b>Market data evidence adapter</b><span>${esc(detail)}</span><span>Historical availability and provider display rights stay unverified until there is explicit evidence. No server upload or persistence is used by this adapter.</span></div>`, '');
  }
  const quality = bundle.quality;
  const blockers = [...new Set(bundle.features.flatMap((item) => item.lineageEligibility.blockers))].slice(0, 5);
  const featureRows = bundle.features.map((item) => {
    const record = item.record;
    const value = typeof record.value === 'number' ? formatFeedNumber(record.value, 4) : JSON.stringify(record.value);
    return `<tr><td>${esc(item.label)}</td><td>${esc(value)}</td><td>${esc(record.unit)}</td><td>${item.lineageEligibility.eligible ? 'Eligible' : 'Research only'}</td></tr>`;
  }).join('');
  const contextAge = Number.isInteger(bundle.contextReference?.ageCalendarDays) ? ` · ${bundle.contextReference.ageCalendarDays} calendar days old` : '';
  const contextReference = bundle.contextReference?.asOf
    ? `Chartlector reference ${esc(bundle.contextReference.asOf)}${contextAge} · context values are not included in the bundle.`
    : 'Chartlector reference was unavailable for this run.';
  const validationState = quality.allObservationRecordsValid && quality.featureValidationFailures === 0 ? 'VALID RECORDS' : 'VALIDATION ISSUE';
  const analysisAsOf = bundle.analysis?.calculationAsOfTime || 'no completed bars';
  const partialBarNote = bundle.analysis?.currentSessionBarExcluded ? ' · current-session bar excluded' : '';
  return panel('Evidence, provenance & eligibility', `${bundle.sourceCapture.symbol} · calculations through ${analysisAsOf}${partialBarNote} · ${validationState}`, `<div class="flow-summary-grid">${statCard('BAR OBSERVATIONS', integer(quality.acceptedBarCount), `${integer(quality.rejectedBarCount)} rejected · ${integer(quality.duplicateBarCount)} duplicate`, null, '◈')}${statCard('DERIVED FEATURES', integer(bundle.features.length), 'hash-linked, versioned methods', null, '⌁')}${statCard('PIT AVAILABILITY', 'UNKNOWN', 'no verified availability refs', null, '◉')}${statCard('DECISION ELIGIBLE', integer(quality.decisionEligibleFeatureCount), 'paper-research purpose', null, '↗')}</div>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>FEATURE</th><th>VALUE</th><th>UNIT</th><th>GATE</th></tr></thead><tbody>${featureRows || '<tr><td colspan="4">Insufficient bars for the listed indicators.</td></tr>'}</tbody></table></div>
      <div class="privacy-footnote"><b>Capture ${esc(bundle.sourceCapture.captureId)}</b><span>Normalized payload SHA-256 ${esc(bundle.sourceCapture.captureSha256)} · ${esc(contextReference)} Browser memory only; download creates a local JSON file. Method inputs are included beside each hashed feature record.</span></div>
      ${blockers.length ? `<details class="evidence-callout"><summary>Why the research features are blocked from decision use</summary><ul>${blockers.map((item) => `<li>${esc(item)}</li>`).join('')}</ul></details>` : ''}
      <div class="engine-quick-links"><button class="button secondary" data-action="export-research-evidence">Download evidence JSON</button><button class="button secondary" data-view="evidence">Open evidence graph</button></div>`, '');
}

function exportResearchEvidenceBundle() {
  const bundle = state.engineEvidence?.bundle;
  if (!bundle) return;
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `shipyard-research-evidence-${bundle.sourceCapture.symbol}-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function formatFeedNumber(value, digits = 2) {
  return Number.isFinite(value) ? value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—';
}
function marketSessionDate(value, options = {}) {
  return window.SiliconMarketOverview?.formatSessionDate(value, options) || '—';
}
function marketSessionTimestamp(value) {
  return window.SiliconMarketOverview?.formatSessionTimestamp(value) || '—';
}
function utcTimestamp(value) {
  return window.SiliconMarketOverview?.formatUtcTimestamp(value) || '—';
}
function renderAlpaca() {
  const feed = state.alpacaFeed;
  const returnedBars = feed.bars || [];
  const asOfLabel = feed.asOf ? marketSessionDate(feed.asOf, { year: 'numeric' }) : 'unknown';
  const selectCompleted = window.SiliconResearchAdapters?.selectCompletedDailyBars;
  const selection = selectCompleted ? selectCompleted(returnedBars, new Date(), feed.value?.session_calendar) : { bars: returnedBars, currentSessionBarExcluded: false, nonTradingDateBarExcluded: false, latestDateBarExcluded: false, cutoffRule: 'Adapter unavailable; returned bars shown without session-date filtering.', calculationAsOfTime: returnedBars.at(-1)?.at || null };
  const bars = selection.bars;
  const symbol = feed.symbol || state.ticker;
  const chart = bars.length ? bars.slice(-120) : [];
  const closes = chart.map(bar => bar.close);
  const sma = period => closes.map((_, index) => index < period - 1 ? null : closes.slice(index - period + 1, index + 1).reduce((sum, value) => sum + value, 0) / period);
  const chartStart = chart.length >= 50 ? 49 : chart.length >= 20 ? 19 : 0;
  const chartSeries = chart.length ? [{ values: closes.slice(chartStart), color: '#42d6ab', fill: true, label: 'Close' }] : [];
  if (chart.length > chartStart) {
    const s20 = sma(20).slice(chartStart), s50 = sma(50).slice(chartStart);
    if (s20.every(Number.isFinite)) chartSeries.push({ values: s20, color: '#63a9fa', label: 'SMA 20' });
    if (s50.every(Number.isFinite)) chartSeries.push({ values: s50, color: '#aa91ff', label: 'SMA 50' });
  }
  const labelIndexes = chart.length ? [...new Set([0, Math.floor((chart.length - 1) / 4), Math.floor((chart.length - 1) / 2), Math.floor(3 * (chart.length - 1) / 4), chart.length - 1])] : [];
  const chartMarkup = chart.length > 1 ? `${chartLegend(chartSeries.map(series => ({ label: series.label, color: series.color })))}${lineChart(chartSeries, { width: 900, height: 300, axis: '$', decimals: 2, xLabels: labelIndexes.map(index => marketSessionDate(chart[index].at)) })}` : '<div class="empty-state">No bars loaded. Choose a symbol and request data.</div>';
  const indicators = window.SiliconResearchAdapters;
  const closesForIndicators = bars.map(bar => bar.close);
  const sma20Value = indicators?.simpleMovingAverage?.(closesForIndicators, 20) ?? null;
  const sma50Value = indicators?.simpleMovingAverage?.(closesForIndicators, 50) ?? null;
  const rsi = indicators?.simpleRsi14?.(closesForIndicators) ?? null;
  const atr = indicators?.simpleAtr14?.(bars) ?? null;
  const last = bars.at(-1);
  const change = bars.length > 1 ? (last.close / bars.at(-2).close - 1) * 100 : null;
  const totalReturn = bars.length > 1 ? (last.close / bars[0].close - 1) * 100 : null;
  const rows = returnedBars.slice(-12).reverse().map(bar => {
    const latestDateBarExcluded = selection.latestDateBarExcluded && bar.at === selection.latestReturnedBarAsOf;
    const exclusionLabel = latestDateBarExcluded ? (selection.nonTradingDateBarExcluded ? ' · NON-SESSION DATE' : ' · IN-PROGRESS BAR') : '';
    const date = marketSessionDate(bar.at, { year: 'numeric' });
    return `<tr><td>${date}${exclusionLabel}</td><td>${formatFeedNumber(bar.open)}</td><td>${formatFeedNumber(bar.high)}</td><td>${formatFeedNumber(bar.low)}</td><td>${formatFeedNumber(bar.close)}</td><td>${integer(Math.round(bar.volume))}</td></tr>`;
  }).join('');
  const status = feed.refreshError ? `Refresh failed: ${esc(feed.refreshError)}. Showing the last valid bars through ${esc(asOfLabel)}.` : feed.refreshing ? `Refreshing · current bars remain visible through ${esc(asOfLabel)}.` : feed.status === 'loading' ? 'Loading Alpaca IEX daily bars…' : feed.status === 'connected' ? `Updated ${feed.receivedAt ? marketSessionTimestamp(feed.receivedAt) : 'recently'} · IEX · through ${esc(asOfLabel)}${selection.currentSessionBarExcluded ? ' · today’s partial bar is excluded from indicators' : selection.nonTradingDateBarExcluded ? ' · today’s non-session bar is excluded' : ''}${selection.sessionCalendar === 'alpaca_iex' ? '' : ' · calendar fallback'}` : feed.status === 'unavailable' ? `Unavailable · ${feed.error || 'check the connection'}` : feed.status === 'no_data' ? `No bars returned for ${esc(symbol)}.` : 'Choose a ticker and load daily bars.';
  return `${pageHeading('ALPACA · IEX · DAILY', 'Alpaca chart & indicator lab', 'Split-adjusted daily bars with close-based charts and indicators. This page refreshes every five minutes while open.', '<button class="button secondary" data-action="refresh-alpaca-bars">↻ Refresh bars</button>')}
    ${panel('Symbol and history', 'One symbol per request · daily bars · bounded to 20–180 calendar days', `<form id="alpaca-chart-form" class="activity-controls"><label class="field-label">SYMBOL<input name="symbol" value="${esc(symbol)}" maxlength="10" pattern="[A-Za-z0-9.-]{1,10}" required /></label><label class="field-label">RANGE<select name="days">${[20,60,90,180].map(days => `<option value="${days}" ${Number(feed.days) === days ? 'selected' : ''}>${days} calendar days</option>`).join('')}</select></label><button class="button primary" ${feed.status === 'loading' ? 'disabled' : ''}>Load bars</button><a class="button secondary" href="https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}/" target="_blank" rel="noopener noreferrer">Yahoo Finance ↗</a></form><div class="api-result" role="status" aria-live="polite">${esc(status)}</div>${feed.error ? `<div class="optionlab-error" role="alert">${esc(feed.error)}</div>` : ''}`, '')}
    ${last ? `<div class="flow-summary-grid">${statCard('LAST COMPLETED CLOSE', `$${formatFeedNumber(last.close)}`, `${esc(symbol)} · ${marketSessionDate(last.at, { year: 'numeric' })}`, null, '◈')}${statCard('DAILY CHANGE', change === null ? '—' : pct(change), 'prior completed daily close', null, '↗')}${statCard(`${feed.days}-DAY RETURN`, totalReturn === null ? '—' : pct(totalReturn), 'completed bars · excludes cash distributions', null, '⌁')}${statCard('CALCULATION BARS', integer(bars.length), `${integer(returnedBars.length)} returned by Alpaca`, null, '▤')}</div>` : ''}
    ${panel('Price and moving averages', 'Completed daily closes · 20- and 50-bar averages', chartMarkup, '')}
    ${last ? panel('Technical indicators', 'Completed daily bars.', `<div class="flow-summary-grid">${statCard('SMA 20', formatFeedNumber(sma20Value), 'simple close average', null, '⌁')}${statCard('SMA 50', formatFeedNumber(sma50Value), 'simple close average', null, '⌁')}${statCard('RSI 14', formatFeedNumber(rsi, 1), 'simple mean gain/loss ratio', null, '◈')}${statCard('ATR 14', `$${formatFeedNumber(atr)}`, 'simple mean true range', null, '↕')}</div>`, '') : ''}
    ${returnedBars.length ? panel('Latest daily bars', selection.sessionCalendar === 'alpaca_iex' ? 'Today’s bar is eligible 15 minutes after the IEX core close; IEX non-session dates are excluded.' : 'Today’s bar uses the NYSE schedule fallback; the status line identifies this mode.', `<div class="table-wrap"><table class="data-table"><thead><tr><th>DATE</th><th>OPEN</th><th>HIGH</th><th>LOW</th><th>CLOSE</th><th>VOLUME</th></tr></thead><tbody>${rows}</tbody></table></div><div class="table-bottom"><span>Feed: ${esc(feed.value?.feed || 'IEX')}</span><span>Adjusted: split</span><span>As of: ${esc(asOfLabel)}</span><span>Calculated through: ${esc(selection.calculationAsOfTime ? marketSessionDate(selection.calculationAsOfTime, { year: 'numeric' }) : 'no completed bars')}</span></div>`, '') : ''}
    <div class="privacy-footnote"><b>Source</b><span>Alpaca Market Data · IEX · split-adjusted daily bars. Yahoo Finance opens as a source link.</span></div>`;
}
function renderChartlector() {
  const loaded = state.marketContext;
  const value = loaded.value;
  const c = value?.context || {};
  if (!value) return `${pageHeading('END-OF-DAY CONTEXT', 'Market Context & Chartlector', 'Regime, breadth, volatility and macro series with source dates.', '<button class="button primary" data-action="refresh-market-context">Load context ↻</button>')}<div class="api-result" role="status" aria-live="polite">${loaded.status === 'loading' ? 'Loading Chartlector and macro context…' : loaded.error ? esc(loaded.error) : 'Context has not been loaded yet.'}</div><p class="small-muted">Source: public Chartlector data.</p>`;
  const mood = c.mood_ring || {}, breadth = c.breadth || {}, appetite = c.risk_appetite || {}, themes = c.themes?.rows || [], screens = c.screens?.screens || [], vol = c.market_volatility?.indices || {};
  const moodHistory = (mood.history || []).filter(row => Number.isFinite(row.v)).slice(-60);
  const breadthHistory = (breadth.history || []).slice(-60);
  const breadthChart = breadthHistory.length ? lineChart([{ values: breadthHistory.map(x => x.p20).filter(Number.isFinite), color: '#42d6ab', label: '% > 20D' }, { values: breadthHistory.map(x => x.p50).filter(Number.isFinite), color: '#63a9fa', label: '% > 50D' }, { values: breadthHistory.map(x => x.p200).filter(Number.isFinite), color: '#aa91ff', label: '% > 200D' }].filter(s => s.values.length), { width: 820, height: 240, axis: '%' }) : '<div class="empty-state">No breadth history in the latest publication.</div>';
  const themeRows = themes.slice().sort((a,b) => (b.m1 ?? -Infinity) - (a.m1 ?? -Infinity)).slice(0,20).map(row => `<tr><td>${esc(row.sym || '—')}</td><td>${esc(row.group || '—')}</td><td>${formatFeedNumber(row.close)}</td><td>${row.d1 === null ? '—' : pct(row.d1)}</td><td>${row.m1 === null ? '—' : pct(row.m1)}</td><td>${formatFeedNumber(row.rs21, 1)}</td><td>${esc(row.quadrant || '—')}</td></tr>`).join('');
  const screenRows = screens.flatMap(screen => (screen.hits || []).slice(0, 12).map(hit => `<tr><td>${esc(screen.label || screen.key || 'Screen')}</td><td>${esc(hit.sym || '—')}</td><td>${formatFeedNumber(hit.close)}</td><td>${hit.d1 === null ? '—' : pct(hit.d1)}</td><td>${formatFeedNumber(hit.rvol, 2)}</td></tr>`)).slice(0,40).join('');
  const macro = c.macro || {}, curve = macro.observations || [], latestCurve = curve.at(-1) || {}, dollar = macro.dollar_index?.observations?.at(-1) || {};
  const received = value.received_at ? marketSessionTimestamp(value.received_at) : 'unknown';
  const freshness = marketContextFreshness(value.as_of);
  const freshnessClass = freshness.state === 'fresh' ? 'coverage-local' : freshness.state === 'stale' ? 'coverage-partial' : 'coverage-none';
  const connectionClass = freshness.state === 'fresh' ? ' connected' : '';
  return `${pageHeading('PUBLIC END-OF-DAY CONTEXT', 'Market Context & Chartlector', 'Market regime, breadth, themes and macro data with source dates.', '<button class="button secondary" data-action="refresh-market-context">↻ Refresh context</button>')}
    <div class="connection-card${connectionClass}"><div class="connection-state-icon">◉</div><div class="connection-main"><span class="eyebrow">CHARTLECTOR PUBLIC CONTEXT</span><span class="coverage-state ${freshnessClass}" role="status" aria-label="Chartlector data freshness">${esc(freshness.label)}</span><h2>As of ${esc(value.as_of || 'unknown')}</h2><p>Published end-of-day values.</p></div><div class="connection-badge">received ${esc(received)}</div></div>
    <div class="flow-summary-grid">${statCard('MOOD RING', mood.state || '—', `Composite ${formatFeedNumber(mood.composite, 1)} · divergence ${mood.divergence || '—'}`, null, '◈')}${statCard('BREADTH SCORE', formatFeedNumber(breadth.current?.score, 1), `${integer(breadth.universe || 0)} names · ${formatFeedNumber(breadth.current?.pct50, 1)}% above 50D`, null, '↗')}${statCard('RISK APPETITE', `${integer(appetite.risk_on || 0)} / ${integer(appetite.of || 0)}`, 'risk-on pairs / tracked pairs', null, '⌁')}${statCard('VIX', vol.VIX ? formatFeedNumber(vol.VIX.close) : '—', vol.VIX?.as_of ? `as of ${vol.VIX.as_of}` : 'not published', null, '↕')}</div>
    ${panel('Volatility context', 'Cboe published daily reference values; not dealer positioning or intraday quotes.', `<div class="flow-summary-grid">${['VIX','VIX3M','VVIX','SKEW'].map(key => statCard(key, vol[key] ? formatFeedNumber(vol[key].close) : '—', vol[key]?.as_of ? `as of ${vol[key].as_of}` : 'unavailable', null, '◈')).join('')}</div>`, '')}
    ${panel('Market breadth', 'Share of the tracked universe above moving averages, using the latest Chartlector observation.', `${chartLegend([{label:'Above 20D',color:'#42d6ab'},{label:'Above 50D',color:'#63a9fa'},{label:'Above 200D',color:'#aa91ff'}])}${breadthChart}<div class="table-bottom"><span>Advancers ${integer(breadth.current?.adv || 0)}</span><span>Decliners ${integer(breadth.current?.dec || 0)}</span><span>20D ${formatFeedNumber(breadth.current?.pct20, 1)}%</span><span>200D ${formatFeedNumber(breadth.current?.pct200, 1)}%</span></div>`, '')}
    ${moodHistory.length ? panel('Regime history', 'Published Chartlector composite history.', lineChart([{ values: moodHistory.map(x => x.v), color: '#42d6ab', fill: true, label: 'Composite' }], { width: 820, height: 210, axis: '' }), '') : ''}
    ${panel('Themes and sectors', `Chartlector rows · as of ${esc(c.themes?.as_of || value.as_of || 'unknown')}`, `<div class="table-wrap"><table class="data-table"><thead><tr><th>SYMBOL</th><th>GROUP</th><th>CLOSE</th><th>1D</th><th>1M</th><th>RS 21D</th><th>QUADRANT</th></tr></thead><tbody>${themeRows || '<tr><td colspan="7">No theme rows available.</td></tr>'}</tbody></table></div>`, '')}
    ${panel('Published screens', 'Recent screen hits are context only and are not evaluated as trading signals.', `<div class="table-wrap"><table class="data-table"><thead><tr><th>SCREEN</th><th>SYMBOL</th><th>CLOSE</th><th>1D</th><th>RVOL</th></tr></thead><tbody>${screenRows || '<tr><td colspan="5">No screen hits published.</td></tr>'}</tbody></table></div>`, '')}
    ${panel('Rates and dollar index', 'Latest rows from public U.S. Treasury and Federal Reserve sources when available.', `<div class="flow-summary-grid">${statCard('10Y TREASURY', formatFeedNumber(latestCurve.ten_year), latestCurve.date || 'unavailable', null, '⌁')}${statCard('2Y TREASURY', formatFeedNumber(latestCurve.two_year), latestCurve.date || 'unavailable', null, '⌁')}${statCard('30Y TREASURY', formatFeedNumber(latestCurve.thirty_year), latestCurve.date || 'unavailable', null, '⌁')}${statCard('BROAD DOLLAR', formatFeedNumber(dollar.broad), dollar.date || 'unavailable', null, '⌁')}</div>`, '')}
    <div class="privacy-footnote"><b>Sources</b><span>Chartlector · U.S. Treasury · Federal Reserve Board · Cboe Global Markets.</span></div>`;
}
async function loadMarketContext() {
  if (state.marketContext.status === 'loading') return;
  state.marketContext.status = 'loading'; state.marketContext.error = ''; render();
  try {
    const response = await fetch('/api/terminal/context', { headers: { Accept: 'application/json' } });
    const value = await response.json();
    if (!response.ok || value.status === 'unavailable') throw new Error(`Market context unavailable (HTTP ${response.status}).`);
    state.marketContext = { status: 'connected', value, error: '' };
  } catch (error) { state.marketContext = { status: 'unavailable', value: null, error: error.message || 'Market context could not be loaded.' }; }
  render();
}
async function loadMorgueReadiness() {
  if (state.morgueReadiness?.status === 'loading') return;
  state.morgueReadiness = { status: 'loading', value: state.morgueReadiness?.value || null, error: '' };
  render();
  try {
    const response = await fetch('/api/research/morgue/readiness', { headers: { Accept: 'application/json' } });
    const value = await response.json();
    if (!response.ok) throw new Error(`Morgue snapshot unavailable (HTTP ${response.status}).`);
    state.morgueReadiness = { status: value.status === 'available' || value.status === 'partial' ? 'connected' : value.status || 'unavailable', value, error: '' };
  } catch (error) {
    state.morgueReadiness = { status: 'unavailable', value: null, error: error instanceof Error ? error.message : 'Morgue snapshot could not be checked.' };
  }
  render();
}
function evaluateAlpacaAlerts(feed) {
  const returnedBars = Array.isArray(feed?.bars) ? feed.bars : [];
  const selector = window.SiliconResearchAdapters?.selectCompletedDailyBars;
  const bars = selector ? selector(returnedBars, new Date(), feed?.session_calendar).bars : returnedBars;
  if (bars.length < 2) return;
  const latest = bars.at(-1), previous = bars.at(-2);
  if (!(previous.close > 0) || !Number.isFinite(latest.close)) return;
  const changePct = (latest.close / previous.close - 1) * 100;
  let changed = false;
  state.alerts = state.alerts.map(alert => {
    if (alert.condition !== 'change' || alert.ticker !== feed.symbol) return alert;
    const lastEvaluation = { barAt: latest.at, changePct, matched: Math.abs(changePct) >= Number(alert.threshold) };
    changed = true;
    return { ...alert, lastEvaluation };
  });
  if (changed) persist();
}

async function loadAlpacaBars(symbol = state.alpacaFeed.symbol, days = state.alpacaFeed.days, { silent = false } = {}) {
  if (state.alpacaFeed.status === 'loading' || state.alpacaFeed.refreshing) return;
  const normalized = String(symbol || 'SPY').trim().toUpperCase();
  if (!/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(normalized)) { state.alpacaFeed.error = 'Enter a valid ticker containing letters, numbers, dots, or hyphens.'; state.alpacaFeed.status = 'unavailable'; render(); return; }
  const range = [20,60,90,180].includes(Number(days)) ? Number(days) : 90;
  const previous = state.alpacaFeed;
  const retained = previous.symbol === normalized && Number(previous.days) === range && previous.bars.length > 0;
  state.alpacaFeed = {
    ...previous, symbol: normalized, days: range,
    value: retained ? previous.value : null,
    bars: retained ? previous.bars : [],
    receivedAt: retained ? previous.receivedAt : null,
    asOf: retained ? previous.asOf : null,
    status: retained ? 'connected' : 'loading',
    refreshing: retained, refreshError: '', error: '',
  };
  if (!silent || !retained) render();
  try {
    const response = await fetch(`/api/alpaca/bars?symbol=${encodeURIComponent(normalized)}&days=${range}`, { headers: { Accept: 'application/json' } });
    const value = await response.json();
    if (!response.ok) throw new Error(value.error === 'credentials_or_feed_rejected' ? 'Alpaca rejected the configured credentials or IEX feed access.' : value.error || `Market-data request failed (HTTP ${response.status}).`);
    if (value.symbol !== normalized || value.feed !== 'iex' || value.timeframe !== '1Day' || value.adjustment !== 'split') throw new Error('The market-data response did not match the selected Alpaca daily feed.');
    const receivedMs = Date.parse(value.received_at || '');
    if (!Number.isFinite(receivedMs)) throw new Error('The market-data response has no valid received time.');
    const summary = window.SiliconMarketOverview.summarizeDailyBars(value.bars);
    if (retained && !summary.latest) throw new Error('No valid bars came back.');
    if (summary.latest && value.as_of && Date.parse(value.as_of) !== Date.parse(summary.latest.at)) throw new Error('The feed date did not match its latest bar.');
    state.alpacaFeed = {
      ...state.alpacaFeed, value, bars: summary.bars,
      status: summary.latest ? 'connected' : value.status || 'no_data',
      receivedAt: value.received_at, asOf: summary.latest?.at || value.as_of || null,
      refreshing: false, refreshError: '', error: '',
    };
    evaluateAlpacaAlerts({ ...value, bars: summary.bars, symbol: normalized });
  } catch (error) {
    const message = error.message || 'Market-data request failed.';
    state.alpacaFeed = retained
      ? { ...state.alpacaFeed, status: 'connected', refreshing: false, refreshError: message, error: '' }
      : { ...state.alpacaFeed, status: 'unavailable', refreshing: false, refreshError: '', error: message };
  }
  render();
}

const LIVE_BARS_REFRESH_MS = 5 * 60 * 1000;
const MARKET_CONTEXT_REFRESH_MS = 15 * 60 * 1000;
const LIVE_BRAIN_REFRESH_MS = 60 * 1000;
function refreshVisibleMarketData() {
  if (document.visibilityState === 'hidden') return;
  if (state.view === 'context') {
    if (state.marketContext.status !== 'loading' && window.SiliconMarketOverview.shouldRefreshAt(state.marketContext.value?.received_at, Date.now(), MARKET_CONTEXT_REFRESH_MS)) void loadMarketContext();
    return;
  }
  if (!['overview', 'alpaca', 'charts'].includes(state.view)) return;
  const symbol = state.view === 'overview' || state.view === 'charts' ? state.ticker : state.alpacaFeed.symbol;
  if (state.alpacaFeed.status === 'loading' || state.alpacaFeed.refreshing) return;
  if (state.alpacaFeed.symbol !== symbol || window.SiliconMarketOverview.shouldRefreshAt(state.alpacaFeed.receivedAt, Date.now(), LIVE_BARS_REFRESH_MS)) {
    void loadAlpacaBars(symbol, state.alpacaFeed.days, { silent: true });
  }
}
window.setInterval(refreshVisibleMarketData, LIVE_BARS_REFRESH_MS);
window.setInterval(refreshTradeBrain, LIVE_BRAIN_REFRESH_MS);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') { refreshVisibleMarketData(); refreshTradeBrain(); } });
window.addEventListener('focus', () => { refreshVisibleMarketData(); refreshTradeBrain(); });

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
  const width = options.width || 780, height = options.height || 240;
  const axisLayout = window.SiliconMarketOverview?.lineChartAxisLayout?.(window.innerWidth)
    || { compact: false, leftPadding: 48, labelX: 4, labelAnchor: 'start' };
  const pad = { l: axisLayout.leftPadding, r: 14, t: 14, b: 28 };
  const vals = series.flatMap(s => s.values); const min = Math.min(...vals), max = Math.max(...vals), span = (max - min) || 1;
  const x = i => pad.l + i * (width - pad.l - pad.r) / (Math.max(...series.map(s => s.values.length)) - 1);
  const y = v => height - pad.b - (v - min) / span * (height - pad.t - pad.b);
  const grid = Array.from({ length: 4 }, (_, i) => { const gy = pad.t + i * (height - pad.t - pad.b) / 3; return `<line class="chart-grid" x1="${pad.l}" y1="${gy}" x2="${width - pad.r}" y2="${gy}"/><text class="chart-axis" text-anchor="${axisLayout.labelAnchor}" x="${axisLayout.labelX}" y="${gy + 4}">${options.axis || ''}${(max - i * span / 3).toFixed(options.decimals ?? 0)}</text>`; }).join('');
  const paths = series.map(s => {
    const points = s.values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    const area = `${points} L${x(s.values.length - 1)},${height - pad.b} L${pad.l},${height - pad.b} Z`;
    return `${s.fill ? `<path d="${area}" fill="${s.color}" opacity=".08"/>` : ''}<path d="${points}" fill="none" stroke="${s.color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`;
  }).join('');
  const axisLabels = options.xLabels || ['09:30', '10:00', '10:30', '11:00', '11:30'];
  const labels = axisLabels.map((t, i) => `<text class="chart-axis" text-anchor="${i === 0 ? 'start' : i === axisLabels.length - 1 ? 'end' : 'middle'}" x="${pad.l + i * (width - pad.l - pad.r) / (axisLabels.length - 1)}" y="${height - 4}">${esc(t)}</text>`).join('');
  return `<svg class="line-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.ariaLabel || 'Chart')}">${grid}${paths}${labels}</svg>`;
}
function chartLegend(items) { return `<div class="chart-legend">${items.map(i => `<span><i style="--legend:${i.color}"></i>${i.label}</span>`).join('')}</div>`; }
function tickerLink(ticker) { return `<button class="ticker-link" data-symbol="${ticker}">${ticker}</button>`; }
function changeText(value) { return `<span class="${signedClass(value)}">${pct(value)}</span>`; }
function tableEmpty(text) { return `<div class="empty-state"><span>⌕</span><b>No matching rows</b><p>${text}</p></div>`; }

const coverageLanes = {
  options: { name: 'Options & derivatives', routes: 'Options flow · GEX & Greeks · dark pools · payoff calculator', gap: 'Live transaction prints, complete positioning history, vendor classifications, and alert delivery are not connected.' },
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
    <section class="panel confluence-result-panel"><div class="panel-heading"><div><h2>Candidate decision audit</h2><p>Scores are manual estimates, not Leadr outputs or validated signals.</p></div></div>${blockerList}<div class="coverage-footnote">This path reproduces the public client’s effective leaf weights and checkable aggregation boundaries only. The bundle also accepts a packed server/framework score vector; its source data, transformations, freshness, and authenticated score pipeline remain unknown. <a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md">Open the implementation record →</a></div></section>`;
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
    <section class="panel confluence-result-panel"><div class="panel-heading"><div><h2>Candidate decision audit</h2><p>Every blocker is shown so missing evidence cannot silently become a positive score.</p></div></div>${blockerList}<div class="coverage-footnote">The public bundle uses a separate six-axis model as well. This lab implements only the documented eight-category candidate. Input values stay in this browser’s local storage; no score data is sent to a server. <a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/leadr_labs/CONFLUENCE-LAB-IMPLEMENTATION.md">Open the implementation record →</a></div></section>`;
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
  const actions = `<button class="button secondary" data-action="portfolio-export" ${stateData.rows.length ? '' : 'disabled'}>Export decision audit</button>`;
  return `${pageHeading('PUBLIC METHOD · INDEPENDENT CONSTRUCTOR', 'Sector Portfolio Lab', 'A point-in-time portfolio constructor. Import existing scores; the lab selects and weights candidates but does not calculate the AI Score.', actions)}
    <div class="evidence-callout portfolio-callout"><b>Published rules</b><span>Low Risk ≥ 5, three-month volume &gt; 100, top five passing sectors, five names per sector, Proven Buy priority, and equal weights. Vendor scores and weights are private; this lab applies the published selection rules to your CSV.</span><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/danelfin/TEARDOWN.md">Review teardown evidence →</a></div>
    <div class="strategy-data-banner portfolio-data-banner"><div><span class="coverage-state ${stateData.source === 'csv' ? 'coverage-local' : 'coverage-none'}">${stateData.source === 'csv' ? 'LOCAL CSV' : 'NO DATA'}</span><b>${esc(stateData.filename)}</b><small>${stateData.rows.length.toLocaleString()} input rows · ${snapshotDates.length} dated snapshots · latest ${dateCaption} · this is a local-input study, not a live feed</small>${stateData.notice ? `<small class="strategy-notice">${esc(stateData.notice)}</small>` : ''}${signalNote}</div><label class="button primary file-pick">Choose CSV<input id="portfolio-file" type="file" accept=".csv,text/csv" /></label></div>
    <div class="portfolio-schema-note"><b>CSV columns:</b> required <code>Ticker, Score, Sector, LowRisk, Avg3MVolume</code> · optional <code>ProvenBuySignal, AsOf, SnapshotComplete</code>. Scores must be 1–10; volume is average daily shares, not dollars. Use one row per symbol per dated snapshot. For schedule replay, every row in a snapshot must declare <code>SnapshotComplete=true</code>; this is your assertion about the supplied snapshot, not proof of full-market coverage.</div>
    ${dataError}
    <div class="coverage-summary portfolio-summary"><div><b>${selectedSnapshotRows.length.toLocaleString()}</b><span>selected-snapshot rows</span></div><div><b>${result.eligible.length.toLocaleString()}</b><span>pass both filters</span></div><div><b>${result.chosen.length}/25</b><span>selected positions</span></div><div><b>${result.chosen.length ? `${(100 / result.chosen.length).toFixed(2)}%` : '—'}</b><span>initial equal-weight target</span></div></div>
    <section class="panel portfolio-settings"><div class="panel-heading"><div><h2>Selection controls</h2><p>Score and risk values are imported as supplied; sector means use only names passing both filters.</p></div></div><label class="portfolio-toggle"><input type="checkbox" data-portfolio-preference ${stateData.preferProvenBuy ? 'checked' : ''} /> Prefer confirmed Proven Buy names within each selected sector before score ranking</label><span class="small-muted">If selected, the priority signal is the first ordering key, followed by score descending and ticker ascending. Turn this off to rank by score only.</span></section>
    <section class="panel portfolio-sector-panel"><div class="panel-heading"><div><h2>Sector rank</h2><p>Mean score across eligible names; highest five sectors define the portfolio universe.</p></div><span class="small-muted">${result.sectors.length} eligible sectors</span></div><div class="table-wrap"><table><thead><tr><th>RANK</th><th>SECTOR</th><th>MEAN SCORE</th><th>ELIGIBLE NAMES</th><th>CONSTRUCTION</th></tr></thead><tbody>${sectorRows}</tbody></table></div>${result.sectors.length > 50 ? `<div class="portfolio-table-note">Showing first 50 of ${result.sectors.length} sectors by mean score.</div>` : ''}</section>
    <section class="panel portfolio-selected-panel"><div class="panel-heading"><div><h2>Current equal-weight portfolio</h2><p>${result.chosen.length ? `${result.chosen.length} of 25 possible names · ${result.chosen.length < 25 ? 'under-filled because qualifying inputs are limited' : 'full 25-name construction'}` : 'No qualifying names in the supplied snapshot'}</p></div><span class="small-muted">${dateCaption}</span></div><div class="table-wrap"><table><thead><tr><th>#</th><th>TICKER</th><th>SECTOR</th><th>SCORE</th><th>LOW RISK</th><th>AVG 3M VOLUME</th><th>PROVEN BUY</th><th>WEIGHT</th></tr></thead><tbody>${chosenRows}</tbody></table></div></section>
    <section class="panel portfolio-schedule-panel"><div class="panel-heading"><div><h2>Membership reviews and annual weight targets</h2><p>Schedule cycles use calendar-month anniversaries anchored to the declared portfolio start date.</p></div><label class="field-label">PORTFOLIO START DATE<input type="date" data-portfolio-start-date value="${esc(plan.startDate || '')}" ${snapshotDates.length ? '' : 'disabled'} /></label></div><p class="small-muted">Each scheduled review uses the latest supplied snapshot dated on or before the event; snapshots older than 7 calendar days or lacking <code>SnapshotComplete=true</code> are left unknown. Annual rows show an equal-weight target only. This planner does not calculate actual weight drift or returns without position and price history.</p><div class="table-wrap"><table><thead><tr><th>REVIEW DATE</th><th>INPUT SNAPSHOT</th><th>AGE</th><th>STATE</th><th>ADDITIONS</th><th>REMOVALS</th><th>SELECTED</th><th>WEIGHT TARGET</th></tr></thead><tbody>${scheduleRows}</tbody></table></div>${scheduleCoverageNote ? `<div class="portfolio-table-note">${esc(scheduleCoverageNote)}</div>` : ''}</section>
    <section class="panel portfolio-audit-panel"><div class="panel-heading"><div><h2>Candidate decision audit</h2><p>Filter failures, sector exclusions, reserves, and selected names are listed with the applied decision.</p></div><span class="small-muted">${result.auditRows.length.toLocaleString()} total candidates</span></div><div class="table-wrap"><table><thead><tr><th>TICKER</th><th>SECTOR</th><th>SCORE</th><th>LOW RISK</th><th>AVG 3M VOL</th><th>BUY</th><th>SECTOR RANK / MEAN</th><th>DECISION</th></tr></thead><tbody>${auditRows}</tbody></table></div>${result.auditRows.length > auditLimit ? `<div class="portfolio-table-note">Showing first ${auditLimit} of ${result.auditRows.length.toLocaleString()} candidates. Export includes the full decision audit.</div>` : ''}</section>
    <div class="method-note method-note-spacing">Scores and dates come from the loaded CSV. This planner has no historical score archive or return series.</div>`;
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
    const reportState = v.research === 'in-progress' ? 'RESEARCH IN PROGRESS' : v.research === 'bounded-complete' ? 'BOUNDED REVIEW COMPLETE' : 'RESEARCH COMPLETE';
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
    <div class="coverage-summary"><div><b>${meta.requestedPasses}</b><span>requested passes</span></div><div><b>${meta.targetFamilies}</b><span>registered families</span></div><div><b>${fullReplicaCount}</b><span>full vendor replicas</span></div><div><b>${onchainCount}</b><span>families with no suite surface</span></div></div>
    <div class="evidence-callout"><b>${meta.requestedNames}-name roster is not reconciled.</b><span>The current operational scoreboard records ${meta.requestedPasses} passes: 95 complete, 5 bounded-review complete, 0 in progress, across ${meta.targetFamilies} registered report families (as of 2026-10-28). Earlier 94/99/100 pass-count displays are drift; use the dated scoreboard for the current count. The historical ${meta.requestedNames}-name roster is absent, so the six-name difference is not mapped or guessed.</span><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/SCOREBOARD.md" target="_blank" rel="noopener noreferrer">Open current scoreboard ↗</a> · <a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/synthesis/SCOPE-AND-DENOMINATOR-RECONCILIATION-2026-10-27.md" target="_blank" rel="noopener noreferrer">Open denominator reconciliation ↗</a></div>
    <div class="coverage-lane-grid">${laneCards}</div>
    <div class="coverage-footnote">The legacy teardown index separately lists OpenMarket, VolSignals, and TheStrat as three post-index additions outside the active 86-family / 100-pass scope. They are not counted or assumed to fill the missing 92-name roster. A bounded teardown or tested partial prototype is not a full vendor recreation.</div>
    <section class="panel coverage-registry"><div class="panel-heading"><div><h2>Target-family registry</h2><p>${filtered.length} of ${families.length || meta.targetFamilies} families · teardown status is separate from implementation status</p></div><span class="small-muted">As of ${esc(meta.asOf || '2026-10-27')}</span></div>
      <div class="coverage-controls"><label class="field-label">SEARCH<input data-filter="vendorSearch" value="${esc(state.vendorSearch)}" placeholder="Vendor or product family" /></label><label class="field-label">PRODUCT LANE<select data-filter="vendorLane"><option value="all" ${state.vendorLane === 'all' ? 'selected' : ''}>All lanes</option>${Object.entries(coverageLanes).map(([id, lane]) => `<option value="${id}" ${state.vendorLane === id ? 'selected' : ''}>${esc(lane.name)}</option>`).join('')}</select></label><label class="field-label">RESEARCH STATUS<select data-filter="vendorResearch"><option value="all" ${state.vendorResearch === 'all' ? 'selected' : ''}>All reports</option><option value="complete" ${state.vendorResearch === 'complete' ? 'selected' : ''}>Research complete</option><option value="bounded-complete" ${state.vendorResearch === 'bounded-complete' ? 'selected' : ''}>Bounded review complete</option><option value="in-progress" ${state.vendorResearch === 'in-progress' ? 'selected' : ''}>Research in progress</option></select></label></div>
      <div class="coverage-grid">${loadState}</div>
      <div class="coverage-footnote">“Bounded review complete” means the available public/local evidence for the pass was reviewed and its limits recorded. It does not mean an exact build, protected runtime, source provenance, or full product recreation was verified. Remaining evidence requests are tracked in the linked reports and do not block this bounded review state.</div>
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
  { name: 'Zeiierman Trading · public product and access notes', status: 'PUBLIC EVIDENCE / NO VENDOR LOGIC', cls: 'coverage-partial', text: 'Summarizes dated public disclosures only. Invite-Only scripts, private signals, account state, paid data, and trading execution are not connected or reproduced.', details: ['Official help identifies Arcturus Algo and Crypto Punk Bot as Invite-Only Scripts, says its scripts are proprietary and not shared, and describes alerts routed through third-party execution services. No private script or live order behavior was accessed.', 'Current pricing lists $95.20/month billed monthly, $59.99/month billed quarterly, and $37.99/month billed annually. Access timing differs across pages: 2–5 minutes in help versus instant/within one minute on pricing. No checkout or entitlement was verified.', 'Current Terms restrict reverse engineering/transcription, scraping/security circumvention, and commercial reproduction of service content. The separate Neural Weight Oscillator is labeled CC BY-NC-SA 4.0; its source was not copied into Silicon.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/zeiierman.md#current-first-party-recheck-2026-10-28', linkText: 'Open dated evidence report ↗', secondaryLink: 'https://docs.zeiierman.com/help/indicator-and-bots', secondaryLinkText: 'Open first-party help page ↗' },
  { name: 'ChartPrime · public product and rights contract', status: 'PUBLIC EVIDENCE / NO VENDOR LOGIC', cls: 'coverage-partial', text: 'Summarizes ChartPrime public product, policy, pricing, privacy, and access disclosures. No Pine source, indicator calculation, private data, or trading execution is reproduced or connected.', details: ['The 2026-10-28 homepage displayed Pro at $67/month or $489/year, Plus at $117/month or $708/year, and a 20% PRIME20 offer; checkout was not opened. The 2026-10-26 capture recorded a 30% offer.', 'Terms dated 2026-10-02 prohibit reverse engineering, copying or extracting indicator logic, access-control bypass, and automated collection without written permission. Exchange data remains separately licensed.', 'The Privacy Policy describes account/platform identifiers, purchase and eligibility data, device/usage information, cookies, and advertising disclosures. It says the role updater does not read messages or track presence. These are policy claims, not tested runtime behavior.', 'The refund page remains dated 2023-12-12, states seven-day refund requests, and routes cancellation through live support; newer Terms describe email cancellation and generally non-refundable lifetime plans. Purchase-specific policy precedence is unresolved.', 'Prime Automation marketing claims one-click activation, live result tracking, and 24/7 trading, but public material does not establish venue, account authorization, order lifecycle, or audited performance.', 'No account, private Discord, invite-only TradingView script, checkout, feed, broker, or vendor source was accessed; no code was copied and no access control was bypassed.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/chartprime.md#L53', linkText: 'Open current evidence report ↗', secondaryLink: 'https://chartprime.com/terms-conditions', secondaryLinkText: 'Open first-party Terms ↗' },
  { name: 'Quant Data · public API contract', status: 'PUBLIC CONTRACT / NO LIVE FEED', cls: 'coverage-partial', text: 'The public docs describe options REST endpoints and hosted MCP access, but their examples are not observed API responses. Silicon’s options-flow, exposure, and dark-pool pages remain synthetic and do not connect to Quant Data.', details: ['The 2026-10-28 first-party docs recheck confirms Bearer-key REST/MCP access, a shared documented request quota, and Streaming marked “Coming Soon.” No API key, endpoint, MCP call, account, or paid feed was used.', 'The docs list separate options and CME futures products, but the reviewed REST catalog did not show a futures endpoint. Dashboard/mobile sync, feed quality, completeness, latency, and advertised uptime were not independently tested.', 'The current linked Terms and Privacy pages could not be retrieved. The project contains no Quant Data API-specific license, data grant, or vendor source artifact; protected data and code are not integrated.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/quant-data.md#L62', linkText: 'Open Quant Data evidence report ↗', secondaryLink: 'https://quantdata.us/api/docs/introduction', secondaryLinkText: 'Open public API docs ↗' },
  { name: 'Optionality / Sinux Signals · alert evidence audit', status: 'PUBLIC EVIDENCE ONLY', cls: 'coverage-partial', text: 'The public alert schema shows symbol, contract, entry range, size, timestamp, desk, and thread updates. Its sample is explicitly illustrative, and the linked live-P&L dashboard returned only an app shell without authentication. No private Discord history, fills, or P&L were inspected.', link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/optionality-sinux.md', linkText: 'Open alert evidence review ↗' },
  { name: 'Stock Moe Earner · public offer audit', status: 'PUBLIC OFFER AUDIT', cls: 'coverage-partial', text: 'The public offer separates Earner from Earner Plus; feature delivery, session schedule, and captured listing prices remain vendor-advertised. Private bot payloads, signal history, and performance are unverified.', details: ['At the 2026-10-26 capture, the current Earner listing showed $49.99/month. Separate linked records showed Earner plus indicator at $99.99/month, Earner annual at $499/year, and Earner lifetime at $2,999.', 'Separate Earner Plus creator-catalog records showed $162.99/month, $48/week, $1,649.99/year, and “Lifetime” at $410/month; older variants showed $249.99/month and $2,499/year. Keep each record separate: these are not one canonical tier schedule, and price/availability can change.', 'Earner advertises Tuesday/Thursday sessions; Earner Plus adds a Wednesday livestream, exclusive support channel, and invite-only Bread Recipe TradingView indicator. No Discord role, private bot output, TradingView invite, or account was accessed.', 'AI-generated, backtested, reversal, and performance descriptions are seller claims. No script source, test report, signal history, fills, or strategy returns were inspected. Public Whop listings state no refunds because access is immediate.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/stock-moe.md#pricing-and-listing-drift', linkText: 'Open offer and price evidence ↗', secondaryLink: 'https://whop.com/stock-moe/stock-moe-earner-discord/', secondaryLinkText: 'Open public Earner listing ↗' },
  { name: 'AIME / AIME+ · AI research surface', status: 'PUBLIC SURFACE ONLY', cls: 'coverage-partial', text: 'AIME is described as an AI research terminal; the related Aime mobile app is a separate listing. Shared models, backend, entitlements, and mobile privacy behavior are not established.', details: ['AIME terms warn that generated information can be wrong, stale, incomplete, or fabricated.', 'The privacy policy describes processing and retention of prompts, voice interactions, and linked brokerage data for service operation and improvement. No chat, voice input, or brokerage connection was used.', 'The separate API terms limit API use to personal, internal, non-commercial purposes and restrict copying/export and competitive use. No API key, API data, or vendor code is used here.'], link: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md#product-boundary', linkText: 'Open AIME product evidence ↗', secondaryLink: 'https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea_teardowns/targets/ainvest.md#api-and-access-boundary', secondaryLinkText: 'Open API and access limits ↗' },
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

function renderConvergenceEngine() {
  const engine = window.SiliconConvergenceEngine;
  const catalog = engine?.SURVIVOR_CATALOG || [];
  const familyIndex = engine?.FAMILY_CROSSWALK || [];
  const imported = state.convergenceImport || { status: 'idle', records: [], rejected: [], headers: [], filename: '', importedAt: null, error: '' };
  const query = String(state.convergenceSearch || '').trim().toLowerCase();
  const passes = familyIndex.reduce((sum, family) => sum + family.passes, 0);
  const completeCount = familyIndex.filter(family => family.status === 'complete').length;
  const boundedCount = familyIndex.filter(family => family.status === 'bounded-complete').length;
  const visibleSurvivors = catalog.filter(survivor => {
    if (!query) return true;
    const familyText = familyIndex.filter(family => family.survivor_id === survivor.id).map(family => family.name).join(' ');
    return (survivor.id + ' ' + survivor.name + ' ' + survivor.thesis + ' ' + survivor.source + ' ' + familyText).toLowerCase().includes(query);
  });
  const visibleFamilies = familyIndex.filter(family => !query || (family.name + ' ' + family.slug + ' ' + family.lane + ' ' + family.kernel + ' ' + family.survivor_name).toLowerCase().includes(query));
  const survivorCards = visibleSurvivors.map(survivor => {
    const familyNames = familyIndex.filter(family => family.survivor_id === survivor.id).map(family => family.name);
    const routeButtons = survivor.route.map((route, index) => '<button class="text-button" data-view="' + esc(route) + '">' + (index === 0 ? 'Open' : 'Also open') + ' ' + esc(survivor.routeLabel.split(' / ')[index] || route) + ' →</button>').join('');
    return '<article class="coverage-vendor convergence-card"><div class="coverage-vendor-top"><span class="coverage-state coverage-local">' + esc(survivor.status) + '</span><span class="coverage-research">RANK ' + survivor.confidence_rank + ' · ' + survivor.confidence_score + '/100</span></div><h3>' + esc(survivor.id) + ' · ' + esc(survivor.name) + '</h3><p>' + esc(survivor.thesis) + '</p><div class="convergence-card-actions">' + routeButtons + '</div><details><summary>Source, run path and build method</summary><dl><div><dt>Data source</dt><dd>' + esc(survivor.source) + '</dd></div><div><dt>Execution path</dt><dd>' + esc(survivor.path) + '</dd></div><div><dt>Minimal build</dt><dd>' + esc(survivor.mvp) + '</dd></div><div><dt>Novelty</dt><dd>' + esc(survivor.novelty) + '</dd></div><div><dt>Ascension</dt><dd>' + esc(survivor.ascension) + '</dd></div><div><dt>Distilled</dt><dd>' + esc(survivor.stripped) + '</dd></div><div><dt>REA inputs</dt><dd>' + familyNames.map(esc).join('; ') + '</dd></div><div><dt>Operations</dt><dd>' + esc(survivor.ops) + '</dd></div></dl></details></article>';
  }).join('') || '<div class="coverage-error">No survivor capabilities match this search.</div>';
  const sortedEvents = [...(imported.records || [])].filter(row => String(row.EventType || '').trim()).sort((a, b) => Date.parse(a.ObservedAt) - Date.parse(b.ObservedAt));
  const eventRows = sortedEvents.slice(0, 40).map(row => '<tr><td class="mono">' + esc(row.ObservedAt) + '</td><td>' + esc(row.EventType) + '</td><td><b>' + esc(row.Entity) + '</b></td><td>' + esc(row.Metric) + '</td><td>' + esc(row.Value) + '</td><td>' + esc(row.PublicAt || '—') + '</td><td>' + esc(row.ReceivedAt || imported.importedAt || '—') + '</td><td>' + esc(row.Source) + '</td></tr>').join('');
  const recordRows = (imported.records || []).slice(0, 50).map(row => '<tr><td class="mono">' + esc(row.ObservedAt) + '</td><td>' + esc(row.Entity) + '</td><td>' + esc(row.Source) + '</td><td>' + esc(row.Metric) + '</td><td>' + esc(row.Value) + '</td><td>' + esc(row.Unit || '—') + '</td><td>' + esc(row.Method || '—') + '</td><td>' + esc(row.Confidence || '—') + '</td><td>' + (row.SourceURL ? '<a href="' + esc(row.SourceURL) + '" target="_blank" rel="noopener noreferrer">Source ↗</a>' : '—') + '</td></tr>').join('');
  const rejectedRows = (imported.rejected || []).slice(0, 25).map(row => '<tr><td>' + row.rowNumber + '</td><td>' + esc(row.reason) + '</td></tr>').join('');
  const familyRows = visibleFamilies.map(family => '<tr><td><b>' + esc(family.name) + '</b><small class="convergence-family-slug">' + esc(family.slug) + '</small></td><td>' + esc(family.lane) + '</td><td>' + esc(family.status) + ' · ' + family.passes + ' pass' + (family.passes === 1 ? '' : 'es') + '</td><td>' + esc(family.survivor_id) + ' · ' + esc(family.survivor_name) + '</td><td>' + esc(family.kernel) + '</td><td><a href="' + esc(family.report_url) + '" target="_blank" rel="noopener noreferrer">Open report ↗</a></td></tr>').join('');
  const importMessage = imported.status === 'loading' ? 'Reading and validating this file in the current tab…' : imported.status === 'error' ? imported.error : imported.status === 'ready' ? imported.acceptedCount + ' accepted · ' + imported.rejectedCount + ' rejected · received ' + imported.importedAt + ' · ' + imported.filename : 'No file loaded. Select a CSV to begin.';
  const importCounts = imported.status === 'ready' ? '<div class="convergence-import-counts"><span><b>' + imported.acceptedCount + '</b> accepted</span><span><b>' + imported.rejectedCount + '</b> rejected</span><span><b>' + sortedEvents.length + '</b> typed events</span><span><b>' + esc(imported.headers.join(', ')) + '</b> input columns</span></div>' : '';
  const eventEmpty = imported.status === 'ready' ? 'No accepted rows contain EventType.' : 'Load a CSV with explicit EventType values to build this timeline.';
  const recordPanel = imported.records.length ? '<details class="panel convergence-registry"><summary>Normalized evidence envelope · showing ' + Math.min(50, imported.records.length) + ' of ' + imported.records.length + ' accepted rows</summary><div class="table-wrap"><table class="data-table convergence-table"><thead><tr><th>OBSERVED AT</th><th>ENTITY</th><th>SOURCE</th><th>METRIC</th><th>VALUE</th><th>UNIT</th><th>METHOD</th><th>CONFIDENCE</th><th>REFERENCE</th></tr></thead><tbody>' + recordRows + '</tbody></table></div>' + (imported.records.length > 50 ? '<div class="coverage-footnote">The complete accepted record set is available in the downloaded JSON.</div>' : '') + '</details>' : '';
  const rejectedPanel = imported.rejected.length ? '<details class="panel convergence-registry"><summary>Rejected rows · ' + imported.rejected.length + '</summary><div class="table-wrap"><table class="data-table"><thead><tr><th>CSV ROW</th><th>REASON</th></tr></thead><tbody>' + rejectedRows + '</tbody></table></div></details>' : '';
  const manyEvents = sortedEvents.length > 40 ? '<div class="table-bottom">Showing 40 of ' + sortedEvents.length + ' typed events. Download accepted JSON for the full set.</div>' : '';
  const heading = pageHeading('20 CAPABILITIES · 86 ACTIVE FAMILIES · 100 REVIEW PASSES', 'Convergence engine', 'A searchable map from the REA corpus to runnable, scoped research workflows. Each path names its actual data source and route.', '<button class="button secondary" data-view="enginehub">Open research engine suite →</button>');
  return heading
    + '<div class="flow-summary-grid convergence-kpis"><div class="stat-card"><div class="stat-label">SURVIVOR CAPABILITIES</div><div class="stat-value">' + catalog.length + '</div><div class="stat-foot"><span class="muted">Operational with scope</span></div></div>'
    + '<div class="stat-card"><div class="stat-label">ACTIVE REA FAMILIES</div><div class="stat-value">' + familyIndex.length + '</div><div class="stat-foot"><span class="muted">Exact report links</span></div></div>'
    + '<div class="stat-card"><div class="stat-label">RECORDED PASSES</div><div class="stat-value">' + passes + '</div><div class="stat-foot"><span class="muted">' + completeCount + ' complete · ' + boundedCount + ' bounded</span></div></div>'
    + '<div class="stat-card"><div class="stat-label">EVIDENCE IMPORT</div><div class="stat-value">' + (imported.records.length ? imported.records.length.toLocaleString() : '—') + '</div><div class="stat-foot"><span class="muted">' + (imported.status === 'ready' ? 'Rows in this tab only' : 'Local CSV intake') + '</span></div></div></div>'
    + '<section class="panel convergence-intake"><div class="panel-heading"><div><h2>Observation and event intake</h2><p>Local CSV validation, event chronology and provenance-preserving export.</p></div></div>'
    + '<div class="convergence-controls"><div><label class="eyebrow" for="convergence-search">FILTER SURVIVORS AND FAMILY INDEX</label><input id="convergence-search" class="convergence-search" data-filter="convergenceSearch" value="' + esc(state.convergenceSearch) + '" placeholder="Search name, lane, value kernel, or survivor" /></div><div class="engine-quick-links"><label class="button primary file-pick">Choose CSV<input id="convergence-evidence-file" type="file" accept=".csv,text/csv" aria-label="Choose a local evidence CSV" /></label><button class="button secondary" data-action="convergence-template">CSV template</button><button class="button secondary" data-action="convergence-export" ' + (imported.records.length ? '' : 'disabled') + '>Download accepted JSON</button></div></div>'
    + '<div class="convergence-import-state" role="status" aria-live="polite">' + esc(importMessage) + ' <span>File content stays in this tab; nothing is uploaded or saved to browser storage.</span></div>' + importCounts
    + '<div class="coverage-footnote">Required: <code>ObservedAt, Entity, Source, Metric, Value</code>. Optional: <code>PublicAt, ReceivedAt, Unit, Method, Confidence, EventType, SourceURL</code>. Values remain text; the parser preserves source clocks and rejects invalid dates or source URLs.</div></section>'
    + '<section class="panel convergence-event-panel"><div class="panel-heading"><div><h2>Catalyst and event timeline</h2><p>Rows with explicit EventType, sorted by observed time. Public and local receipt times stay separate.</p></div><span class="coverage-research">' + sortedEvents.length + ' typed events</span></div><div class="table-wrap"><table class="data-table convergence-table"><thead><tr><th>OBSERVED AT</th><th>EVENT TYPE</th><th>ENTITY</th><th>METRIC</th><th>VALUE</th><th>PUBLIC AT</th><th>RECEIVED AT</th><th>SOURCE</th></tr></thead><tbody>' + (eventRows || '<tr><td colspan="8">' + eventEmpty + '</td></tr>') + '</tbody></table></div>' + manyEvents + '</section>'
    + recordPanel + rejectedPanel
    + '<section class="panel"><div class="panel-heading"><div><h2>Twenty converged capabilities</h2><p>Evidence-derived inputs feed visible local routes; confidence describes engineering evidence, not predicted return.</p></div><span class="coverage-research">' + visibleSurvivors.length + ' shown</span></div><div class="coverage-grid">' + survivorCards + '</div></section>'
    + '<details class="panel convergence-registry"><summary>86-family REA source index · ' + visibleFamilies.length + ' shown</summary><div class="coverage-footnote">The ledger reconciles 86 active families and 100 pass occurrences. The historical 92-name roster was not recovered, so six missing names are not inferred.</div><div class="table-wrap"><table class="data-table convergence-table"><thead><tr><th>FAMILY</th><th>LANE</th><th>STATUS</th><th>SURVIVOR</th><th>VALUE KERNEL</th><th>REPORT</th></tr></thead><tbody>' + (familyRows || '<tr><td colspan="6">No families match this search.</td></tr>') + '</tbody></table></div></details>';
}

function renderEvidenceGraph() {
  const coverageMeta = normalizeVendorCoverageMeta(state.vendorCoverageMeta);
  const inProgressCount = state.vendorFamilies.filter(v => v.research === 'in-progress').length;
  const boundedCompleteCount = state.vendorFamilies.filter(v => v.research === 'bounded-complete').length;
  const dependencyCards = evidenceDependencies.map(item => `<article class="coverage-lane evidence-lane"><div><span>${esc(item.name)}</span></div><small>${esc(item.sources)}</small><p><b>Products:</b> ${esc(item.examples)}</p><p class="evidence-rule">${esc(item.rule)}</p><span class="coverage-state coverage-partial">DEPENDENCY FAMILY</span></article>`).join('');
  const buildCards = auditedBuilds.map(item => {
    const details = item.details?.length ? `<details class="evidence-detail"><summary>Source notes</summary><ul>${item.details.map(detail => `<li>${esc(detail)}</li>`).join('')}</ul></details>` : '';
    return `<article class="coverage-vendor evidence-build"><div class="coverage-vendor-top"><span class="coverage-state ${item.cls}">${esc(item.status)}</span></div><h3>${esc(item.name)}</h3><p>${esc(item.text)}</p>${details}<a href="${item.link}" target="_blank" rel="noreferrer">${esc(item.linkText)}</a>${item.secondaryLink ? `<a href="${item.secondaryLink}" target="_blank" rel="noreferrer">${esc(item.secondaryLinkText)}</a>` : ''}${item.route ? `<button class="text-button" data-view="${esc(item.route)}">Open in suite →</button>` : ''}</article>`;
  }).join('');
  const clocks = [
    ['EVENT TIME', 'When the market event or action happened.'],
    ['PUBLIC TIME', 'When the source made the fact available.'],
    ['INGESTION TIME', 'When this system first recorded it.'],
    ['DECISION TIME', 'When the feature or paper decision was made.'],
  ].map(([label, detail]) => `<div><b>${label}</b><span>${detail}</span></div>`).join('');
  return `${pageHeading('RESEARCH GOVERNANCE', 'Evidence graph', 'Combine observations by source lineage, not by the number of vendor labels that repeat them.', '<button class="button primary" data-view="coverage">Open 86-family registry →</button>')}
    <div class="coverage-summary"><div><b>${coverageMeta.requestedPasses}</b><span>requested REA passes</span></div><div><b>${coverageMeta.targetFamilies}</b><span>target-family reports</span></div><div><b>0</b><span>full vendor replicas</span></div><div><b>${state.vendorFamilies.filter(v => v.lane === 'onchain').length || 2}</b><span>families with no suite surface</span></div></div>
    <div class="evidence-callout"><b>Pass count is not vendor count.</b><span>The current scoreboard records 100 requested passes across 86 report families: 95 complete, 5 bounded-review complete, 0 in progress, and 0 queued. The historical 92-name roster is missing from the active index; the six-name difference remains unmapped. ${inProgressCount} target-family reports are currently marked in progress and ${boundedCompleteCount} are bounded-complete. The terminal has shared prototypes, eight partial candidates (Leadr, Danelfin, SpotGamma, OptionStrat, Bullflow, Finviz, Stock Rover, and the public 15.87 Rule map), and no full vendor replicas. Views without a live feed return no market records.</span></div>
    <section class="panel evidence-panel"><div class="panel-heading"><div><h2>Six evidence dependency families</h2><p>Several vendor products can be views of the same underlying event or dataset.</p></div></div><div class="coverage-lane-grid evidence-grid">${dependencyCards}</div><div class="coverage-footnote">Do not count correlated price features, duplicate flow prints, or modeled GEX summaries as separate confirmations. Preserve the raw observation and label every derived or inferred field.</div></section>
    <section class="panel evidence-panel"><div class="panel-heading"><div><h2>Four clocks for point-in-time truth</h2><p>Publication delay and ingestion timing can otherwise leak future information into a historical decision.</p></div></div><div class="coverage-summary evidence-clocks">${clocks}</div></section>
    <section class="panel evidence-panel"><div class="panel-heading"><div><h2>Semantic audit highlights</h2><p>Formula fidelity, runtime behavior, attribution, and trading evidence are different claims.</p></div></div><div class="coverage-grid evidence-build-grid">${buildCards}</div><div class="coverage-footnote"><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/synthesis/CONTRIBUTOR-SEMANTIC-AUDIT-2026-10-27.md" target="_blank" rel="noreferrer">Open the full semantic audit ↗</a> · The report also records the limited checkout and artifact gaps.</div></section>
    <div class="evidence-workflow"><span>OBSERVATION</span><i>→</i><span>NORMALIZED FACT</span><i>→</i><span>VERSIONED FEATURE</span><i>→</i><span>INTERPRETATION</span><i>→</i><span>PAPER DECISION</span><i>→</i><span>FIXED-HORIZON OUTCOME</span></div>`;
}

function renderOverview() {
  const feed = state.alpacaFeed;
  const returnedBars = feed.bars || [];
  const selectCompleted = window.SiliconResearchAdapters?.selectCompletedDailyBars;
  const selection = selectCompleted ? selectCompleted(returnedBars, new Date(), feed.value?.session_calendar) : { bars: returnedBars, currentSessionBarExcluded: false };
  const summary = window.SiliconMarketOverview?.summarizeDailyBars(selection.bars) || { bars: [], latest: null, previous: null, changePct: null, range: null };
  const { bars, latest, changePct, range } = summary;
  const latestReturned = returnedBars.at(-1) || null;
  const symbol = feed.symbol || state.ticker;
  const dateLabel = latest ? marketSessionDate(latest.at, { year: 'numeric' }) : 'waiting for data';
  const providerDateLabel = latestReturned ? marketSessionDate(latestReturned.at, { year: 'numeric' }) : 'unknown';
  const receivedLabel = feed.receivedAt ? new Date(feed.receivedAt).toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' }) : 'not yet received';
  const refreshStatus = feed.refreshError
    ? `Refresh failed. Showing the last valid bars through ${esc(providerDateLabel)}.`
    : feed.status === 'loading' && !latest ? 'Loading Alpaca IEX daily bars…'
      : latest ? `${feed.refreshing ? 'Checking' : 'Updated'} ${receivedLabel} · complete through ${dateLabel}.${selection.currentSessionBarExcluded ? ` ${providerDateLabel} bar is partial.` : selection.nonTradingDateBarExcluded ? ` ${providerDateLabel} is not a scheduled session.` : ''}${selection.sessionCalendar === 'alpaca_iex' ? '' : ' · calendar fallback'}`
        : feed.error ? esc(feed.error) : 'Daily bars are not available yet.';
  const buttonDisabled = feed.status === 'loading' || feed.refreshing ? 'disabled' : '';
  const actions = `<button class="button secondary" data-action="refresh-alpaca-bars" ${buttonDisabled}>↻ Refresh now</button><button class="button primary" data-view="alpaca">Open chart lab →</button>`;
  const chart = bars.slice(-30);
  const labelIndexes = chart.length ? [...new Set([0, Math.floor((chart.length - 1) / 4), Math.floor((chart.length - 1) / 2), Math.floor(3 * (chart.length - 1) / 4), chart.length - 1])] : [];
  const chartMarkup = chart.length > 1
    ? lineChart([{ values: chart.map(bar => bar.close), color: '#42d6ab', fill: true, label: 'Daily close' }], {
      width: 900, height: 300, axis: '$', decimals: 2,
      xLabels: labelIndexes.map(index => marketSessionDate(chart[index].at)),
      ariaLabel: `${symbol} daily bar closes through ${dateLabel}`,
    })
    : '<div class="empty-state"><span>◉</span><b>Waiting for price history</b><p>Refresh to load daily bars.</p></div>';
  const tableBars = returnedBars.slice(-10).reverse();
  const rows = tableBars.map(bar => {
    const latestDateBarExcluded = selection.latestDateBarExcluded && bar.at === selection.latestReturnedBarAsOf;
    const barStatus = latestDateBarExcluded ? (selection.nonTradingDateBarExcluded ? ' · NON-SESSION' : ' · PARTIAL') : '';
    return `<tr><td>${marketSessionDate(bar.at, { year: 'numeric' })}${barStatus}</td><td>${formatFeedNumber(bar.open)}</td><td>${formatFeedNumber(bar.high)}</td><td>${formatFeedNumber(bar.low)}</td><td><b>${formatFeedNumber(bar.close)}</b></td><td>${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(bar.volume)}</td></tr>`;
  }).join('');
  return `${pageHeading('ALPACA · IEX · DAILY', 'Market overview', `${symbol} · refreshes every five minutes while open.`, actions)}
    <div class="api-result" role="status" aria-live="polite">${refreshStatus}</div>
    <div class="flow-summary-grid">${statCard('LATEST COMPLETED CLOSE', latest ? `$${formatFeedNumber(latest.close)}` : '—', symbol, null, '⌁')}${statCard('CHANGE VS PRIOR CLOSE', changePct === null ? '—' : changeText(changePct), 'completed sessions', null, '↕')}${statCard('SESSION RANGE', latest ? `$${formatFeedNumber(latest.low)} – $${formatFeedNumber(latest.high)}` : '—', latest ? `${formatFeedNumber(range)} points` : 'waiting for data', null, '↕')}${statCard('IEX VOLUME', latest ? new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(latest.volume) : '—', latest?.trades ? `${integer(latest.trades)} trades` : 'completed session', null, '▤')}</div>
    ${panel(`${symbol} · ${chart.length} completed sessions`, '', chartMarkup, '')}
    ${panel('Recent sessions', selection.latestDateBarExcluded ? 'Today’s provider bar is listed separately; metrics use completed sessions.' : 'Latest 10 provider bars', `<div class="table-wrap"><table class="data-table overview-table"><thead><tr><th>DATE</th><th>OPEN</th><th>HIGH</th><th>LOW</th><th>CLOSE</th><th>IEX VOLUME</th></tr></thead><tbody>${rows || '<tr><td colspan="6">Daily bars will appear here after a successful refresh.</td></tr>'}</tbody></table></div><div class="table-bottom"><span>Alpaca IEX · split-adjusted</span></div>`, '<button class="text-button" data-view="context">Open market context →</button>')}`;
}

function renderFlow() { return renderFeedUnavailable('Options flow', 'Live options trade prints are not connected.'); }

function renderGex() { return renderFeedUnavailable('GEX & Greeks', 'Live, complete options positioning data is not connected.'); }


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

function renderAzraelMapLab() { return renderFeedUnavailable('15.87 Rule map', 'Live inputs for this calculation are not connected.'); }

function renderStaticGexLab() {
  const p = state.staticGex;
  const result = p.rows.length ? buildStaticGexSnapshot(p.rows, p) : null;
  const dateCaption = p.asOf || 'Date unavailable';
  const strikeRows = (result?.strikes || []).slice(0, 250).map(row => `<tr><td>${money(row.strike)}</td><td class="positive">${formatGex(row.callGex)}</td><td class="negative">${formatGex(row.putGex)}</td><td class="${signedClass(row.netGex)}">${formatGex(row.netGex)}</td><td>${pct((row.strike / p.spot - 1) * 100)}</td></tr>`).join('') || '<tr><td colspan="5" class="muted">No strike aggregates are available.</td></tr>';
  const actions = `<button class="button secondary" data-action="static-gex-export" ${p.rows.length ? '' : 'disabled'}>Export contract audit</button>`;
  return `${pageHeading('PUBLISHED STATIC FORMULA · CLEAN-ROOM MODEL', 'Static GEX Lab', 'Calculate a convention-signed, open-interest-based GEX snapshot from a local option-chain CSV. This is a static model, not SpotGamma’s proprietary intraday inventory system.', actions)}
    <div class="evidence-callout portfolio-callout"><b>What this calculation means</b><span>The public formula is Γ × modeled position × contract multiplier × spot² × 0.01, summed by strike, for dollar exposure per 1% underlying move. This implementation treats calls as positive and puts as negative, as the published simplifying convention describes. Open interest is a proxy, not observed dealer inventory; GEX does not predict direction. Black–Scholes gamma and constant IV over the zero-gamma spot grid are explicit local assumptions.</span><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/spotgamma/TEARDOWN.md">Review teardown evidence →</a></div>
    <div class="strategy-data-banner portfolio-data-banner"><div><span class="coverage-state ${p.source === 'csv' ? 'coverage-local' : 'coverage-none'}">${p.source === 'csv' ? 'LOCAL CSV' : 'NO DATA'}</span><b>${esc(p.filename)}</b><small>${p.rows.length.toLocaleString()} option rows · ${esc(p.ticker)} · ${esc(dateCaption)} · local-input model; no live option chain is connected</small>${p.notice ? `<small class="strategy-notice">${esc(p.notice)}</small>` : ''}</div><label class="button primary file-pick">Choose CSV<input id="static-gex-file" type="file" accept=".csv,text/csv" /></label></div>
    <div class="portfolio-schema-note"><b>Required CSV:</b> <code>Ticker,AsOf,Spot,Strike,Type,OpenInterest,IV,DTE</code> · IV is percent points (e.g. 25), DTE is calendar days, OI is contracts, Type is Call/C or Put/P. One underlying, date, and spot per file.</div>
    ${p.error ? `<div class="strategy-error">${esc(p.error)}</div>` : ''}
    ${result ? `<div class="coverage-summary static-gex-summary"><div><b>${money(p.spot)}</b><span>underlying spot · ${esc(dateCaption)}</span></div><div><b>${formatGex(result.netGex)}</b><span>net GEX per 1% move</span></div><div><b>${result.callWall ? money(result.callWall.strike) : '—'}</b><span>largest call gamma concentration</span></div><div><b>${result.putWall ? money(result.putWall.strike) : '—'}</b><span>largest put gamma concentration</span></div><div><b>${result.zeroGamma !== null ? money(result.zeroGamma) : 'No cross'}</b><span>nearest zero within ±${p.gridRangePct}% spot grid</span></div></div>` : '<div class="empty-state"><b>No option data loaded</b><p>Import a sourced option-chain snapshot. This lab does not retrieve or present live GEX.</p></div>'}
    <section class="panel static-gex-settings"><div class="panel-heading"><div><h2>Pricing assumptions</h2><p>These inputs affect theoretical gamma and the zero-gamma repricing grid.</p></div></div><form id="static-gex-config" class="strategy-form"><label class="field-label">RISK-FREE RATE · ANNUAL %<input name="riskFreeRatePct" type="number" min="-10" max="40" step="0.01" value="${p.riskFreeRatePct}" required /></label><label class="field-label">DIVIDEND YIELD %<input name="dividendYieldPct" type="number" min="-10" max="40" step="0.01" value="${p.dividendYieldPct}" required /></label><label class="field-label">CONTRACT MULTIPLIER<input name="multiplier" type="number" min="1" max="10000" step="1" value="${p.multiplier}" required /></label><label class="field-label">ZERO-GAMMA GRID · ± %<input name="gridRangePct" type="number" min="5" max="50" step="1" value="${p.gridRangePct}" required /></label><button class="button primary strategy-run-button">Recalculate GEX</button></form><div class="strategy-assumptions">Gamma is calculated with Black–Scholes using a continuous dividend yield and annualized rate. IV is held constant for each contract as spot moves across a 101-point grid. The zero level is the nearest interpolated net-GEX sign change inside the selected range; no crossing means no value is reported.</div></section>
    ${result ? `<section class="panel static-gex-profile"><div class="panel-heading"><div><h2>GEX by strike</h2><p>Call exposure is positive; put exposure is negative · units are dollars per 1% move.</p></div><span class="small-muted">${result.optionRows.length.toLocaleString()} contracts · prior-night OI convention</span></div><div class="table-wrap"><table><thead><tr><th>STRIKE</th><th>CALL GEX</th><th>PUT GEX</th><th>NET GEX</th><th>SPOT DISTANCE</th></tr></thead><tbody>${strikeRows}</tbody></table></div>${result.strikes.length > 250 ? `<div class="portfolio-table-note">Showing 250 of ${result.strikes.length} strikes. The contract audit export includes all rows.</div>` : ''}</section>` : ''}
    <div class="method-note method-note-spacing">Static open interest model. Dealer sign is assumed; HIRO, TRACE, Volatility Trigger and Risk Pivot feeds are not connected.</div>`;
}

function renderDarkpool() { return renderFeedUnavailable('Dark-pool prints', 'Live off-exchange and ATS prints are not connected.'); }

function renderDisclosures(kind) { return renderFeedUnavailable(kind === 'congress' ? 'Congress trades' : 'Insider activity', 'A live official disclosure feed is not connected.'); }

function renderScreener() { return renderFeedUnavailable('Market screener', 'A live market-wide symbol and fundamentals feed is not connected.'); }

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
  const rows = result?.rows.map(row => `<tr><td>${tickerLink(row.ticker)}</td><td>${esc(row.name || '—')}</td><td>${esc(row.sector || '—')}</td><td>${esc(compactFinvizNumber(row.marketCap))}</td><td>${Number.isFinite(row.pe) ? row.pe.toFixed(2) : '—'}</td><td>${Number.isFinite(row.price) ? money(row.price) : '—'}</td><td class="${Number.isFinite(row.changePct) ? row.changePct >= 0 ? 'positive' : 'negative' : 'muted'}">${Number.isFinite(row.changePct) ? `${row.changePct.toFixed(2)}%` : '—'}</td><td>${compactFinvizNumber(row.avgVolume)}</td><td>${Number.isFinite(row.relativeVolume) ? `${row.relativeVolume.toFixed(2)}×` : '—'}</td><td>${esc(row.pattern || '—')}</td><td>${esc(row.candlestick || '—')}</td></tr>`).join('') || `<tr><td colspan="11">${tableEmpty(result ? 'No snapshot rows match the current filters.' : 'Import a sourced ticker snapshot to run this local screen.')}</td></tr>`;
  const notices = result ? [result.missingTickers.length ? `Not found: ${result.missingTickers.join(', ')}` : '', result.excludedEtfs.length ? `ETF rows excluded: ${result.excludedEtfs.join(', ')}` : '', result.unclassifiedUniverseRows ? `${result.unclassifiedUniverseRows} rows have no SecurityType; ETFs cannot be identified for those rows.` : '', result.filteredTickers.length ? `Present but filtered out: ${result.filteredTickers.join(', ')}` : ''].filter(Boolean).map(text => `<span>${esc(text)}</span>`).join('') : '';
  return `${pageHeading('PUBLIC CONTRACT · LOCAL SNAPSHOT', 'Finviz filter contract lab', 'Apply the documented filter subset to a local snapshot. Pattern tags come from the CSV; this page does not generate them.', '<button class="button secondary" data-view="coverage">Vendor evidence →</button>')}
    ${panel('Snapshot and query controls', 'Filters are ANDed across distinct keys; repeating a key replaces its prior value. Sorting uses o=column or o=-column; o=tickersfilter preserves the provided t= list order. CSV data is local and does not refresh automatically.', `<form id="finviz-contract-form" class="finviz-controls"><label class="field-label">FILTER QUERY f=<input name="filterQuery" value="${esc(model.filterQuery)}" placeholder="exch_nasd,cap_largeover,ta_pattern_wedgeup" /></label><label class="field-label">ORDER o=<input name="order" value="${esc(model.order)}" placeholder="-change or tickersfilter" /></label><label class="field-label">TICKER LIST t=<input name="tickers" value="${esc(model.tickers)}" placeholder="NVDA,SPY,XLE" /></label><button class="button primary">Apply local screen</button></form>
      <div class="activity-file-row"><label class="field-label">SNAPSHOT CSV<input id="finviz-file" type="file" accept=".csv,text/csv" /></label><span class="small-muted">${model.filename ? `Loaded: ${esc(model.filename)}` : 'CSV stays in this browser tab.'}</span></div>
      <div class="activity-input-help"><b>CSV:</b> <code>Ticker,Name,SecurityType,Exchange,Index,Sector,Country,MarketCap,PE,Price,AvgVolume,RelativeVolume,ChangePct,PatternTag,CandlestickTag</code>. Minimum is <code>Ticker</code>; other columns are optional. Supported filters: <code>exch_nasd|nyse|amex</code>, <code>sec_&lt;sector&gt;</code>, <code>geo_&lt;country&gt;</code>, <code>idx_&lt;index&gt;</code>, <code>cap_largeover</code> (&gt;$10B), documented <code>ta_pattern_&lt;tag&gt;</code> and <code>ta_candlestick_&lt;tag&gt;</code>. Pattern columns must be supplied by you; this tool does not detect patterns.</div>
      ${model.error ? `<div class="optionlab-error" role="alert">${esc(model.error)}</div>` : ''}${calculateError ? `<div class="optionlab-error" role="alert">${esc(calculateError)}</div>` : ''}${model.notice ? `<div class="activity-notice">${esc(model.notice)}</div>` : ''}`, '')}
    ${result ? `${status}${notices ? `<div class="finviz-notices">${notices}</div>` : ''}${panel('Screen results', `${result.sourceCount} source rows · ${result.excludedEtfs.length} ETF exclusions · ${result.filteredOut} rows removed by query filters`, `<div class="table-wrap"><table class="data-table"><thead><tr><th>TICKER</th><th>COMPANY</th><th>SECTOR</th><th>MARKET CAP</th><th>P/E</th><th>PRICE</th><th>CHANGE</th><th>AVG VOL</th><th>REL VOL</th><th>PATTERN TAG</th><th>CANDLESTICK TAG</th></tr></thead><tbody>${rows}</tbody></table></div>`, '')}` : model.rows.length ? '<div class="empty-state"><span>!</span><b>Screen not applied</b><p>Correct the query or order field above, then apply it again.</p></div>' : '<div class="empty-state"><span>⌕</span><b>No snapshot loaded</b><p>Import a sourced local ticker snapshot.</p></div>'}
    <div class="evidence-callout portfolio-callout"><b>Supported filters</b><span>AND logic, last-value-wins, ticker-list order, sorting, and ETF exclusion work on your CSV. This lab covers a documented subset of Finviz filters.</span><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/finviz-screener/TEARDOWN.md">Review teardown evidence →</a></div>`;
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
  const rows = result?.rows.slice(0, 250).map(row => `<tr><td>${tickerLink(row.ticker)}</td><td>${esc(row.sector)}</td><td>${factorScore(row.categoryScores.value)}</td><td>${factorScore(row.categoryScores.growth)}</td><td>${factorScore(row.categoryScores.quality)}</td><td>${factorScore(row.categoryScores.sentiment)}</td><td><b>${factorScore(row.composite)}</b></td><td>${row.completedCategories}/4 · ${row.missingMetrics} missing</td></tr>`).join('') || `<tr><td colspan="8">${tableEmpty('Load a point-in-time CSV snapshot to calculate ranks.')}</td></tr>`;
  const metricRows = stockRoverFactorCategories.map(category => `<tr><td>${esc(category.label)}</td><td>${category.metrics.map(metric => `${esc(metric.label)} <code>${esc(metric.key)}</code>`).join(' · ')}</td><td>${category.metrics.length}</td></tr>`).join('');
  const summary = result ? `<div class="coverage-summary stockrover-summary"><div><b>${integer(result.sourceCount)}</b><span>universe rows · ${esc(model.rows[0].asOf)}</span></div><div><b>${integer(result.fullyScored)}</b><span>complete 4-factor composites</span></div><div><b>${factorScore(result.medianComposite)}</b><span>median complete composite</span></div><div><b>${result.top ? `${esc(result.top.ticker)} · ${factorScore(result.top.composite)}` : '—'}</b><span>highest complete composite</span></div></div>` : '';
  return `${pageHeading('PUBLIC INPUTS · DESK RECONSTRUCTION', 'Stock Rover factor profile lab', 'Rank user-supplied cross-sectional fundamentals against the published Value, Growth, Quality, and Sentiment input lists. Local calculation only; scoring weights are a declared desk choice.', '<button class="button secondary" data-view="coverage">Vendor evidence →</button>')}
    ${panel('Point-in-time cross-section', 'Use one decision-date snapshot. Every input column is required; blank metric cells remain missing and are never imputed. CSV snapshots are local inputs and are not refreshed automatically.', `<div class="stockrover-controls"><label class="button primary file-pick">Choose CSV<input id="stockrover-file" type="file" accept=".csv,text/csv" /></label><button class="button secondary" type="button" data-action="stockrover-template">Download CSV template</button>${result ? '<button class="button secondary" type="button" data-action="stockrover-export">Export score audit</button>' : ''}<span class="small-muted">${model.filename ? `Loaded: ${esc(model.filename)} · local CSV` : 'No snapshot loaded; files stay in this browser tab.'}</span></div>
      <div class="activity-input-help"><b>Required columns:</b> <code>Ticker,Sector,AsOf</code> plus all ${stockRoverFactorMetrics.length} metric columns. AsOf must be a shared <code>YYYY-MM-DD</code> decision date; this does not verify that source data were actually available then. Percent returns, growth, and margins use percentage points (e.g. <code>12.5</code> = 12.5%); <code>PriceTo52WeekHigh</code> is a 0–1 ratio; <code>NormalizedMACDSignal</code> is the price-normalized MACD-line minus signal value. Missing cells accept blank, NA, or N/A. File contents are neither uploaded nor retained after the tab closes.</div>
      ${model.error ? `<div class="optionlab-error" role="alert">${esc(model.error)}</div>` : ''}${model.notice ? `<div class="activity-notice">${esc(model.notice)}</div>` : ''}`, '')}
    ${summary}
    ${result ? `<section class="panel stockrover-results"><div class="panel-heading"><div><h2>Cross-sectional factor scores</h2><p>Midrank percentiles run 0–100; equal-weight inputs within each category and equal-weight categories in the composite. Sector-relative ranking applies only to Price / tangible book and Price / sales.</p></div><span class="small-muted">${result.rows.length > 250 ? `Showing 250 of ${integer(result.rows.length)}` : `${integer(result.rows.length)} symbols`}</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>TICKER</th><th>SECTOR</th><th>VALUE</th><th>GROWTH</th><th>QUALITY</th><th>SENTIMENT</th><th>COMPOSITE</th><th>COVERAGE</th></tr></thead><tbody>${rows}</tbody></table></div></section>` : '<div class="empty-state"><span>⌖</span><b>No factor snapshot loaded</b><p>Import a sourced CSV snapshot.</p></div>'}
    <section class="panel stockrover-method"><div class="panel-heading"><div><h2>Inputs and scoring</h2><p>Percentiles use available observations only for each input. A category is blank unless every input in that category is present; the composite is blank unless all four categories are complete.</p></div></div><details><summary>Show the published input list and ranking directions</summary><div class="table-wrap"><table class="data-table"><thead><tr><th>CATEGORY</th><th>INPUTS</th><th>COUNT</th></tr></thead><tbody>${metricRows}</tbody></table></div></details><div class="evidence-callout portfolio-callout"><b>Method</b><span>R1 uses an EPS-predictability proxy; R2 combines 1/3/6/12-month returns; R3 uses normalized MACD; R4 weights factors equally. This CSV lab omits the vendor’s Piotroski, Altman, DCF, and margin-of-safety features.</span><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/stockrover/STOCKROVER-FACTOR-LAB-IMPLEMENTATION.md">Review build notes →</a> · <a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/stockrover/SPEC.md">Review research SPEC →</a></div></section>`;
}

function renderCalendar() { return renderFeedUnavailable('Event calendar', 'A live earnings and economic event feed is not connected.'); }

function renderNews() { return renderFeedUnavailable('News flow', 'A live news feed is not connected.'); }

function renderTicker() { return renderLiveTicker(); }

function renderCharts() { return renderLiveTicker(); }


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

function analyzeStrategy(p = state.strategy) {
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

async function buildStrategyEvidence(strategy, result = analyzeStrategy(strategy)) {
  const contract = window.SiliconEvidenceContract;
  if (!contract) throw new Error('The local evidence contract did not load.');
  if (strategy.source !== 'csv' || !/^[a-f0-9]{64}$/.test(strategy.artifactSha256 || '')) {
    throw new Error('Import a local CSV with a verified file hash before creating an evidence bundle.');
  }
  if (result.error) throw new Error(result.error);

  const parameters = {
    fast: Number(strategy.fast),
    slow: Number(strategy.slow),
    costBpsPerSide: Number(strategy.costBps),
    splitPct: Number(strategy.splitPct),
    periodsPerYear: Number(strategy.periodsPerYear),
    signalDelayBars: 1,
    executionModel: 'close_only_next_bar_return',
  };
  const parametersSha256 = await contract.sha256Hex(JSON.stringify(parameters));
  const observationId = await contract.stableObservationId({
    sourceId: 'user.local-csv',
    sourceKey: `strategy-lab:${strategy.artifactSha256}`,
    revision: 1,
  });
  const now = new Date().toISOString();
  const observation = {
    observationId,
    entity: { kind: 'other', id: 'local:strategy-lab:close-series', symbol: null, venue: null, currency: null, contract: null },
    measure: {
      key: 'strategy_lab.close_series',
      value: { filename: strategy.filename, fileSha256: strategy.artifactSha256, rows: strategy.rows },
      unit: 'user_supplied_close_price',
      adjustment: null,
    },
    clocks: {
      eventAt: null,
      publishedAt: null,
      availableAt: null,
      availabilityEvidence: 'unknown',
      availabilityEvidenceRef: null,
      ingestedAt: now,
      decisionAt: null,
      missingReasons: {
        eventAt: 'CSV dates are preserved as supplied; venue, session, timezone, and timestamp semantics are not verified.',
        publishedAt: 'The file contains no independently verified publication timestamp.',
        availableAt: 'Point-in-time market availability is not established by the local CSV.',
        decisionAt: 'This is a historical research calculation, not a trading decision.',
      },
    },
    state: 'observed',
    stateReason: 'Rows were parsed from a user-supplied file; market-source identity, adjustment policy, and completeness are unverified.',
    source: { sourceId: 'user.local-csv', sourceVersion: 'silicon-strategy-lab-input-v1', uri: null, artifactSha256: strategy.artifactSha256, captureId: null },
    rights: {
      status: 'user_asserted_local_scope',
      evidenceRef: null,
      entitlementId: null,
      allowedPurposes: ['local_analysis', 'paper_research'],
      redistribution: 'not_applicable_to_local_processing',
      retentionUntil: null,
    },
    coverage: {
      status: 'unknown',
      observedCount: strategy.rows.length,
      expectedCount: null,
      missingReasons: ['The input does not declare an expected venue calendar or complete market-session count.'],
    },
    revision: { number: 1, supersedesObservationId: null },
  };
  const analysis = {
    overall: result.overall,
    inSample: result.inSample,
    outOfSample: result.outOfSample,
    splitIndex: result.split,
    records: result.records,
  };
  const implementationSha256 = await contract.sha256Hex([
    rollingMean,
    strategyStats,
    analyzeStrategy,
  ].map(method => `${method.name}\n${method.toString()}`).join('\n'));
  const resultSha256 = await contract.sha256Hex(JSON.stringify(analysis));
  const featureId = `feature_${(await contract.sha256Hex(`${observationId}\0${implementationSha256}\0${parametersSha256}`)).slice(0, 32)}`;
  const feature = {
    featureId,
    value: { overall: result.overall, inSample: result.inSample, outOfSample: result.outOfSample, splitIndex: result.split },
    unit: 'fractional return, drawdown, exposure, and evaluated bars',
    method: {
      methodId: 'silicon.strategy-lab.close-only-sma',
      version: '1.0.0',
      methodRef: 'apps/silicon-market-terminal/app.js#analyzeStrategy',
      implementationSha256,
      parametersSha256,
    },
    parentObservationIds: [observationId],
    sourceFamilyIds: ['user.local-csv'],
    asOfTime: now,
    computedAt: now,
    evidenceStatus: 'reproduced',
    coverageStatus: 'unknown',
    resultSha256,
  };
  const observationValidation = contract.validateObservation(observation);
  const featureValidation = contract.validateFeatureRecord(feature);
  const decisionEligibility = contract.assessDecisionEligibility(observation, { purpose: 'paper_research' });
  const lineageEligibility = contract.assessFeatureLineage(feature, [observation], { purpose: 'paper_research' });
  return { observation, feature, parameters, analysis, observationValidation, featureValidation, decisionEligibility, lineageEligibility };
}

function renderStrategyEvidence(strategy) {
  if (strategy.source !== 'csv') {
    return '<div class="evidence-callout portfolio-callout"><b>Evidence contract</b><span>No input file is loaded.</span><span>Import a sourced CSV to create a hashed, replayable input and result bundle.</span></div>';
  }
  if (!strategy.artifactSha256) {
    return `<div class="evidence-callout portfolio-callout"><b>Evidence contract unavailable</b><span>${esc(strategy.evidenceError || 'This browser could not hash the selected CSV bytes.')}</span><span>Analysis remains local; decision use stays blocked.</span></div>`;
  }
  if (strategy.evidenceError) {
    return `<div class="evidence-callout portfolio-callout"><b>Evidence bundle unavailable</b><span>${esc(strategy.evidenceError)}</span><span>The source file remains in this tab; analysis is still blocked from decision use.</span></div>`;
  }
  if (!strategy.evidence) {
    return '<div class="evidence-callout portfolio-callout"><b>Evidence contract</b><span>Input file SHA-256 is recorded in memory. Export an evidence bundle to include the canonical rows, method/parameter hashes, result hash, and eligibility blockers.</span><span>Source availability, venue/calendar completeness, and source rights remain unverified.</span></div>';
  }
  const evidence = strategy.evidence;
  const blockers = evidence.blockers.slice(0, 4).map(blocker => `<li>${esc(blocker)}</li>`).join('');
  return `<div class="evidence-callout portfolio-callout"><b>Evidence bundle · ${evidence.observationValid && evidence.featureValid ? 'records valid' : 'validation failed'}</b><span>Input SHA-256 ${esc(evidence.inputSha256.slice(0, 20))}… · result SHA-256 ${esc(evidence.resultSha256.slice(0, 20))}…</span><span>Decision use: blocked · availability and CSV coverage are unknown; raw rows remain browser-local until you download the bundle.</span>${blockers ? `<details><summary>Why decision use is blocked</summary><ul>${blockers}</ul></details>` : ''}</div>`;
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
  return `<svg class="strategy-equity-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Close-only strategy equity curve from the loaded CSV"><line x1="${pad}" y1="${baseline}" x2="${width - pad}" y2="${baseline}" class="strategy-baseline"/><polyline points="${points}" fill="none" stroke="#42d6ab" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/></svg>`;
}

function percentReturn(value) { return `${(value * 100).toFixed(2)}%`; }

function renderStrategyLab() {
  const p = state.strategy;
  const result = analyzeStrategy();
  const overall = result.error ? null : result.overall;
  const stat = (labelText, value, sub, cls = '') => `<div class="strategy-stat"><span>${labelText}</span><b class="${cls}">${value}</b><small>${sub}</small></div>`;
  const splitStats = (labelText, value) => value ? `<div class="strategy-split-row"><b>${labelText}</b><span>Return <strong class="${value.totalReturn >= 0 ? 'positive' : 'negative'}">${percentReturn(value.totalReturn)}</strong></span><span>Max drawdown <strong class="negative">${percentReturn(value.maxDrawdown)}</strong></span><span>Buy & hold <strong>${percentReturn(value.benchmarkReturn)}</strong></span><span>Win bars <strong>${percentReturn(value.winBars)}</strong></span></div>` : '';
  const history = state.strategyRuns.length ? state.strategyRuns.map(run => `<tr><td>${esc(run.savedAt)}</td><td>${esc(run.filename)}</td><td>${run.fast}/${run.slow}</td><td>${percentReturn(run.outOfSample)}</td><td>${percentReturn(run.maxDrawdown)}</td></tr>`).join('') : '<tr><td colspan="5" class="muted">No saved run summaries in this browser.</td></tr>';
  const errorText = result.error || p.error;
  const actions = `<button class="button secondary" data-action="strategy-export" ${result.error ? 'disabled' : ''}>Export results CSV</button><button class="button secondary" data-action="strategy-evidence-export" ${result.error || p.source !== 'csv' || !p.artifactSha256 ? 'disabled' : ''}>Export evidence bundle</button>`;
  return `${pageHeading('RESEARCH WORKBENCH', 'Strategy Lab', 'Run a transparent long-or-flat moving-average study on your own CSV bars. Signals use a full-bar delay; costs are charged on entries and exits.', actions)}
    <div class="strategy-data-banner"><div><span class="coverage-state ${p.source === 'csv' ? 'coverage-local' : 'coverage-none'}">${p.source === 'csv' ? 'LOCAL CSV' : 'NO DATA'}</span><b>${esc(p.filename)}</b><small>${p.rows.length.toLocaleString()} bars · close-only · local replay only; this input does not update automatically</small>${p.notice ? `<small class="strategy-notice">${esc(p.notice)}</small>` : ''}</div><label class="button primary file-pick">Choose CSV<input id="strategy-file" type="file" accept=".csv,text/csv" /></label></div>
    ${renderStrategyEvidence(p)}
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
    <div class="method-note">Local bar replay · uses the loaded CSV, date split and configured costs.</div>`;
}

function renderWatchlists() {
  const rows = state.watchlist.map(ticker => {
    const scan = state.tradeBrain.scans[ticker];
    const status = scan?.status === 'connected' ? 'Scanned · live feeds' : scan?.status === 'market_closed' ? 'Market closed' : scan ? 'No live setup' : 'Waiting for scan';
    return `<tr><td>${tickerLink(ticker)}</td><td>${esc(status)}</td><td><button class="text-button" data-view="brain">Scan →</button></td><td><button class="tiny-action remove-action" data-action="watch-remove" data-ticker="${ticker}" title="Remove">×</button></td></tr>`;
  }).join('');
  return `${pageHeading('LOCAL WORKSPACE', 'My watchlists', 'Add symbols to the live Trade Brain scan. The list stays in this browser.', '<button class="button primary" data-view="brain">Open Trade Brain</button>')}
    <div class="watchlist-summary"><div><span class="watchlist-count">${state.watchlist.length}</span><div><b>Market watch</b><small>Default list · saved in this browser only</small></div></div><form id="watch-form" class="watch-add-form"><input name="ticker" maxlength="10" placeholder="Add ticker" aria-label="Ticker to add" required/><button class="button primary">＋ Add</button></form></div>
    ${panel('Symbols', 'Live scan status', `<div class="table-wrap"><table class="data-table"><thead><tr><th>TICKER</th><th>SCAN STATUS</th><th></th><th></th></tr></thead><tbody>${rows || `<tr><td colspan="4">${tableEmpty('Use the add field to start your watchlist.')}</td></tr>`}</tbody></table></div><div class="table-bottom"><span>Stored in local browser storage</span><span>Live quotes appear in Trade Brain scans</span></div>`)}`;
}

function renderAlerts() {
  const matches = state.alerts.filter(alert => alert.lastEvaluation?.matched === true).length;
  const checked = state.alerts.filter(alert => alert.condition === 'change' && alert.lastEvaluation).length;
  const form = state.showAlertForm ? `<form class="alert-form" id="alert-form"><div class="form-heading"><div><b>New alert rule</b><small>Daily-move checks run after Alpaca bars load. Premium alerts need an options feed.</small></div><button type="button" class="icon-button" data-action="close-alert-form">×</button></div><div class="form-grid"><label class="field-label">TICKER<input name="ticker" maxlength="10" placeholder="SPY" required /></label><label class="field-label">WHEN<select name="condition"><option value="change">Absolute daily move exceeds</option><option value="premium">Option premium exceeds</option></select></label><label class="field-label">THRESHOLD<input name="threshold" type="number" min="0.01" step="any" placeholder="e.g. 2.0% or 50000 USD" required /><small>Percent for daily move; USD for option premium.</small></label><label class="field-label">OPTION TYPE<select name="type"><option value="all">Calls or puts</option><option value="call">Calls</option><option value="put">Puts</option></select></label></div><div class="form-actions"><span class="small-muted">Checks run in this browser after a bar refresh.</span><button class="button primary">Save rule</button></div></form>` : '';
  const rules = state.alerts.map((alert, index) => {
    const evaluation = alert.lastEvaluation;
    const condition = alert.condition === 'premium' ? `option premium > ${money(Number(alert.threshold), true)}` : `absolute daily move ≥ ${formatFeedNumber(Number(alert.threshold), 2)}%`;
    const result = alert.condition === 'premium' ? 'OPTIONS FEED NEEDED' : evaluation ? (evaluation.matched ? 'MATCH' : 'CLEAR') : 'CHECK ON BAR LOAD';
    const cls = evaluation?.matched ? 'orange' : evaluation ? 'green-badge' : 'muted-badge';
    const detail = evaluation ? `Latest ${evaluation.changePct > 0 ? '+' : ''}${formatFeedNumber(evaluation.changePct,2)}% on ${marketSessionDate(evaluation.barAt, { year: 'numeric' })}` : alert.condition === 'premium' ? 'Waiting for an options-data source' : 'Load this ticker in Alpaca charts to evaluate';
    return `<div class="alert-rule"><div class="alert-rule-icon">♧</div><div class="alert-rule-main"><b>${esc(alert.ticker)} <span>${condition}</span></b><small>${detail} · Created ${esc(alert.created || 'unknown')}</small></div><div class="alert-rule-status">${label(result, cls)}</div><button class="tiny-action remove-action" data-action="alert-remove" data-index="${index}">×</button></div>`;
  }).join('');
  return `${pageHeading('BROWSER-LOCAL WORKSPACE', 'Alert rules', 'Daily-move rules are evaluated against the latest loaded Alpaca daily bar when you request it. There is no server polling, email, or push delivery.', `<button class="button primary" data-action="new-alert">＋ New rule</button>`)}
    ${form}<div class="flow-summary-grid">${statCard('ACTIVE RULES', state.alerts.length, 'stored in this browser', null, '♧')}${statCard('DAILY RULES CHECKED', checked, 'by Alpaca bar load', null, '◉')}${statCard('CURRENT MATCHES', matches, 'latest loaded daily bar', null, '⚑')}${statCard('DELIVERY', 'ON PAGE', 'no background alerts', null, '⌁')}</div>
    ${panel('Your rules', 'Rule definitions and last manual evaluation', `<div class="alert-rule-list">${rules || tableEmpty('No rules yet. Add a daily-move rule, then load matching Alpaca bars to evaluate it.')}</div><div class="table-bottom"><span>Local rules; a match is informational and is not a trade instruction.</span><button class="text-button" data-view="alpaca">Open Alpaca charts →</button></div>`)}`;
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
function renderTools() { return renderFeedUnavailable('Options tools', 'Live option quotes are required before these calculations can be used.'); }

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

async function buildOptionStrategyEvidence(model) {
  const contract = window.SiliconEvidenceContract;
  if (!contract) throw new Error('The local evidence contract did not load.');

  const parameters = {
    spot: model.spot,
    daysToExpiration: model.daysToExpiration,
    volatilityPct: model.volatilityPct,
    riskFreeRatePct: model.riskFreeRatePct,
    dividendYieldPct: model.dividendYieldPct,
    exerciseStyle: model.exerciseStyle,
    treeSteps: model.treeSteps,
    legs: model.legs.map(leg => ({
      type: leg.type,
      side: leg.side,
      strike: leg.strike,
      premium: leg.premium,
      contracts: leg.contracts,
      multiplier: leg.multiplier,
      ivPct: leg.ivPct ?? null,
    })),
  };
  const parametersJson = JSON.stringify(parameters);
  const parametersSha256 = await contract.sha256Hex(parametersJson);
  const observationId = await contract.stableObservationId({
    sourceId: 'user.manual-input',
    sourceKey: `option-strategy-inputs:${parametersSha256}`,
    revision: 1,
  });
  const now = new Date().toISOString();
  const observation = {
    observationId,
    entity: { kind: 'other', id: 'local:option-strategy:scenario-inputs', symbol: null, venue: null, currency: 'USD', contract: null },
    measure: { key: 'option_strategy.scenario_inputs', value: parameters, unit: 'user_assumption_pack' },
    clocks: {
      eventAt: null,
      publishedAt: null,
      availableAt: null,
      availabilityEvidence: 'unknown',
      availabilityEvidenceRef: null,
      ingestedAt: null,
      decisionAt: null,
      missingReasons: {
        eventAt: 'A local what-if scenario has no market event time.',
        publishedAt: 'User-entered assumptions are not a published market observation.',
        availableAt: 'No source or point-in-time market availability evidence is attached.',
        ingestedAt: 'The scenario remains in browser memory; no ingestion clock is recorded.',
        decisionAt: 'This calculation is not a trading decision.',
      },
    },
    state: 'inferred',
    stateReason: 'The record contains user-entered assumptions, not independently sourced market observations.',
    source: { sourceId: 'user.manual-input', sourceVersion: 'silicon-option-lab-v1', uri: null, artifactSha256: null, captureId: null },
    rights: {
      status: 'user_asserted_local_scope',
      evidenceRef: null,
      entitlementId: null,
      allowedPurposes: ['local_analysis', 'paper_research'],
      redistribution: 'not_applicable_to_local_processing',
      retentionUntil: null,
    },
    coverage: { status: 'not_applicable', observedCount: null, expectedCount: null, missingReasons: [] },
    revision: { number: 1, supersedesObservationId: null },
  };

  const modelStats = buildOptionStrategyModel(model.legs, model);
  const payoffStats = optionStrategyStats(model.legs);
  const result = {
    netTheoreticalValue: modelStats.netTheoreticalValue,
    modeledPnlVsEntry: modelStats.modeledPnlVsEntry,
    netDelta: modelStats.netDelta,
    netGamma: modelStats.netGamma,
    netVegaPerPctPoint: modelStats.netVegaPerPctPoint,
    netThetaPerDay: modelStats.netThetaPerDay,
    netRhoPerPctPoint: modelStats.netRhoPerPctPoint,
    expiration: {
      netDebit: payoffStats.netDebit,
      maxProfit: payoffStats.unboundedProfit ? null : payoffStats.maxPnl,
      maxProfitUnbounded: payoffStats.unboundedProfit,
      maxLoss: payoffStats.unboundedLoss ? null : Math.max(0, -payoffStats.minPnl),
      maxLossUnbounded: payoffStats.unboundedLoss,
      breakEvens: payoffStats.breakEvens,
      breakEvenIntervals: payoffStats.breakEvenIntervals,
    },
  };
  const implementation = [
    optionStrategyPnlAt,
    optionStrategyStats,
    standardNormalCdf,
    blackScholesEuropean,
    crrAmericanOption,
    americanCrrGreeks,
    optionScenarioModel,
    buildOptionStrategyModel,
    buildOptionStrategySensitivity,
  ].map(method => `${method.name}\n${method.toString()}`).join('\n');
  const implementationSha256 = await contract.sha256Hex(implementation);
  const resultSha256 = await contract.sha256Hex(JSON.stringify(result));
  const featureId = `feature_${(await contract.sha256Hex(`${observationId}\0${implementationSha256}\0${parametersSha256}`)).slice(0, 32)}`;
  const feature = {
    featureId,
    value: result,
    unit: 'USD scenario metrics and position-scaled sensitivities',
    method: {
      methodId: 'silicon.option-strategy-scenario',
      version: '1.0.0',
      methodRef: 'apps/silicon-market-terminal/app.js#buildOptionStrategyModel',
      implementationSha256,
      parametersSha256,
    },
    parentObservationIds: [observationId],
    sourceFamilyIds: ['user.manual-input'],
    asOfTime: now,
    computedAt: now,
    evidenceStatus: 'inferred',
    coverageStatus: 'not_applicable',
    resultSha256,
  };
  const observationValidation = contract.validateObservation(observation);
  const featureValidation = contract.validateFeatureRecord(feature);
  const decisionEligibility = contract.assessDecisionEligibility(observation, { purpose: 'paper_research' });
  const lineageEligibility = contract.assessFeatureLineage(feature, [observation], { purpose: 'paper_research' });
  return { observation, feature, observationValidation, featureValidation, decisionEligibility, lineageEligibility };
}

function renderOptionStrategyEvidence(model) {
  const record = model.evidence;
  if (!record) {
    const status = model.evidenceError
      ? `<span>Contract record could not be created: ${esc(model.evidenceError)}</span>`
      : `<span>${model.error ? 'Input rejected; the last valid profile remains visible without a new evidence record.' : 'Submit a valid scenario to create a browser-memory observation and derived-feature record.'}</span>`;
    return `<div class="evidence-callout portfolio-callout"><b>Evidence contract</b>${status}<span>This is a local what-if tool. It does not attach quotes, market-data timestamps, or decision eligibility.</span></div>`;
  }
  const blockers = [...new Set([...record.decisionEligibility.blockers, ...record.lineageEligibility.blockers])];
  const issueSummary = blockers.slice(0, 4).map(blocker => `<li>${esc(blocker)}</li>`).join('');
  return `<div class="evidence-callout portfolio-callout"><b>Evidence contract · ${record.observationValidation.valid && record.featureValidation.valid ? 'records valid' : 'record validation failed'}</b><span>Local user assumptions only · availability unknown · not eligible for trading decisions · held in this browser tab.</span><span>Observation ${esc(record.observation.observationId.slice(0, 20))}… · feature ${esc(record.feature.featureId)} · SHA-256 method, parameters, and result hashes recorded.</span>${issueSummary ? `<details><summary>Why decision use is blocked</summary><ul>${issueSummary}</ul></details>` : ''}</div>`;
}

function renderOptionStrategyLab() { return renderFeedUnavailable('Option strategy lab', 'Live option quotes are required before this pricing tool can be used.'); }

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
    if (/^(synthetic|sample|fixture)$/i.test(source.trim())) throw new Error(`Row ${rowNumber}: synthetic, sample, and fixture records are not accepted as market input.`);
    const tradeId = cell(cells, 'tradeId');
    const sourceTimestampRaw = ix.sourceTimestamp < 0 ? '' : cell(cells, 'sourceTimestamp');
    const sourceTimestamp = sourceTimestampRaw ? parseBullflowSourceTimestamp(sourceTimestampRaw) : null;
    const sideSource = (cell(cells, 'sideSource') || 'unknown').toUpperCase().replace(/[^A-Z]/g, '');
    const sideSourceValue = ({ VENDOR: 'VENDOR', USER: 'USER', INFERRED: 'INFERRED', UNKNOWN: 'UNKNOWN' })[sideSource];
    if (timeSeconds === null) throw new Error(`Row ${rowNumber}: TimeET must use HH:MM or HH:MM:SS.`);
    if (ix.sourceTimestamp >= 0 && (!sourceTimestampRaw || !sourceTimestamp)) throw new Error(`Row ${rowNumber}: Timestamp must be Unix seconds or ISO 8601 with an explicit UTC offset.`);
    if (sourceTimestamp && !bullflowTimestampMatchesEt(sourceTimestamp, date, cell(cells, 'time'))) throw new Error(`Row ${rowNumber}: Timestamp must match Date and TimeET in America/New_York.`);
    if (cancelled === null) throw new Error(`Row ${rowNumber}: Cancelled must be true or false when that column is present.`);
    if (!['CALL', 'PUT'].includes(type) || !side || !sideSourceValue || strike <= 0 || premium < 0 || (openInterest !== null && openInterest < 0)) throw new Error(`Row ${rowNumber}: check Type, Side, SideSource (vendor/user/inferred/unknown), positive Strike, nonnegative Premium, and OpenInterest.`);
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
  const sideProvenanceCounts = Object.fromEntries(['VENDOR', 'USER', 'INFERRED', 'UNKNOWN'].map(source => [source, targetRows.filter(row => (row.sideSource || 'UNKNOWN') === source).length]));
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


function renderBullflowActivityProfile() {
  const model = state.bullflowProfile;
  const result = model.rows.length || model.availableSessions.length ? calculateBullflowActivityProfile(model) : null;
  const show = value => value === null || !Number.isFinite(value) ? '—' : `${value.toFixed(2)}×`;
  const share = value => value === null || !Number.isFinite(value) ? '—' : `${(value * 100).toFixed(1)}%`;
  const sideSources = result ? ['VENDOR', 'USER', 'INFERRED', 'UNKNOWN'].map(source => `${source.toLowerCase()}: ${result.sideProvenanceCounts[source]}`).join(' · ') : '';
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
  </div>` : '<div class="empty-state"><span>◉</span><b>No activity data loaded</b><p>Upload a sourced local CSV to calculate this profile.</p></div>';
  const statusMarkup = result ? result.statuses.length ? result.statuses.map(status => label(status.replace(/_/g, ' '), 'orange')).join(' ') : label('COMPLETE INPUT DECLARED', 'green-badge') : '';
  const flags = result ? result.flags.map(flag => `<div class="activity-flag ${flag.active === null ? 'unknown' : flag.active ? 'active' : 'inactive'}"><div><b>${esc(flag.name)}</b><small>${esc(flag.rule)}</small></div><span>${flag.active === null ? 'UNKNOWN' : flag.active ? 'TRIGGERED' : 'NOT MET'}</span></div>`).join('') : '';
  const contracts = result?.unusualContracts.length ? result.unusualContracts.map(item => `<tr><td>${esc(item.contract)}</td><td>${item.type}</td><td>${item.expiry || '—'}</td><td>${integer(item.volume)}</td><td>${item.openInterest === null ? '—' : integer(item.openInterest)}</td><td>${item.ratio.toFixed(2)}×</td><td>${money(item.premium, true)}</td></tr>`).join('') : '<tr><td colspan="7">No contract exceeded volume/open interest &gt; 1 with positive OI.</td></tr>';
  return `${pageHeading('PUBLISHED METHOD · LOCAL DATA', 'Options Activity Profile', 'Apply Bullflow’s documented profile method to locally supplied rows. Ratios require 20 complete baseline exports and a complete selected export; completeness remains a user declaration.', '<button class="button secondary" data-view="coverage">Vendor evidence →</button>')}
    ${panel('Source data and as-of controls', 'TimeET is Eastern wall-clock time. Only prints through the selected as-of time are included. CSV input is local and does not update automatically.', `<form id="bullflow-profile-config" class="activity-controls"><label class="field-label">TICKER<input name="ticker" value="${esc(model.ticker)}" maxlength="10" required /></label><label class="field-label">SESSION DATE<input name="asOfDate" type="date" value="${esc(model.asOfDate)}" required /></label><label class="field-label">AS-OF ET<input name="asOfTime" type="time" value="${esc(model.asOfTime)}" required /></label><button class="button primary">Recalculate profile</button></form>
      <div class="activity-file-row"><label class="field-label">PRINT HISTORY CSV<input id="bullflow-profile-file" type="file" accept=".csv,text/csv" /></label><span class="small-muted">${model.filename ? `Loaded: ${esc(model.filename)}${model.importedAt ? ` · imported ${esc(model.importedAt)}` : ''}` : 'CSV stays in this browser tab.'}</span></div>
    <div class="activity-input-help"><b>Required columns:</b> <code>Date,TimeET,Ticker,Contract,Expiry,Type,Strike,Size,Premium,Side,TradeType,OpenInterest</code>. A 20-session ratio also requires an explicit cancellation field (<code>Cancelled</code>) and a coverage-only declaration for each baseline and selected date: blank Contract, zero Size, <code>Available=true</code>, and <code>ExportComplete=true</code>. That declaration means the supplied export/query is complete for that session or as-of window; it does not mean complete market-wide options activity. <code>Available=false</code> and missing dates stay unavailable. Without <code>ExportComplete</code>, no-print rows are not known zero and incomplete dates cannot enter a ratio. Optional <code>Timestamp</code> accepts Unix seconds or ISO 8601 with an explicit UTC offset and is checked against Date/TimeET in New York time. <code>Source</code> records a user-provided source label, <code>TradeID</code> rejects duplicate source IDs, and <code>SideSource</code> accepts vendor/user/inferred/unknown. Unknown side provenance suppresses side-derived calculations. Premium is total dollars per print; Side accepts Ask, Above Ask, Mid, Bid, Below Bid, or Unknown.</div>
      ${model.error ? `<div class="optionlab-error" role="alert">${esc(model.error)}</div>` : ''}${model.notice ? `<div class="activity-notice">${esc(model.notice)}</div>` : ''}`, '')}
    ${result ? `<div class="activity-result-head"><div><b>${esc(model.ticker)} · ${esc(model.asOfDate)} · through ${esc(model.asOfTime)} ET</b><span>${result.baselineCount}/20 prior available sessions · ${result.targetAvailable ? 'selected session declared available' : 'selected session unavailable or undeclared'}</span></div><div>${statusMarkup}</div></div>
      ${coverageDiagnostics}${metrics}
      ${panel('Published activity flags', 'Only the four documented thresholds are evaluated; no proprietary score is inferred.', `<div class="activity-flag-list">${flags}</div>`, '')}
      ${panel('Unusual contracts', 'Computed from supplied rows only: volume / open interest > 1, ordered by ratio, premium, then contract symbol.', `<div class="table-wrap"><table class="data-table"><thead><tr><th>CONTRACT</th><th>TYPE</th><th>EXPIRY</th><th>VOLUME</th><th>OPEN INTEREST</th><th>VOL / OI</th><th>PREMIUM</th></tr></thead><tbody>${contracts}</tbody></table></div>`, '')}` : ''}
    <div class="evidence-callout portfolio-callout"><b>Source notes</b><span>The baseline and thresholds follow Bullflow’s public documentation. Source, completeness, and side labels come from your CSV. No live Bullflow feed is connected.</span><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/research/rea-teardowns/bullflow/TEARDOWN.md">Review teardown evidence →</a></div>`;
}

function tradeBrainReason(data) {
  const messages = {
    market_data_credentials_unavailable: 'Alpaca data access is not configured.',
    session_calendar_unavailable: 'The market session could not be verified.',
    market_data_authentication_failed: 'Alpaca rejected the market-data credentials.',
    underlying_iex_entitlement_unavailable: 'Live IEX stock quotes are unavailable for this account.',
    underlying_quote_unavailable: 'The live stock quote is unavailable.',
    underlying_quote_stale_or_invalid: 'The stock quote is stale or invalid.',
    daily_bar_feed_unavailable: 'Historical daily bars are unavailable.',
    daily_bars_unavailable: 'Historical daily bars could not be loaded.',
    underlying_spread_too_wide: 'The live stock spread is too wide for a setup.',
    option_contract_metadata_unavailable: 'Alpaca option contract details are unavailable.',
    indicative_options_unavailable: 'Alpaca indicative options data is unavailable for this account.',
    indicative_options_request_failed: 'Alpaca could not return an indicative options snapshot.',
    provider_rate_limited: 'The market-data provider has rate-limited this scan.',
    rate_limited: 'The terminal scan limit was reached. It will retry automatically.',
    provider_request_failed: 'The live provider could not be reached.',
    market_closed: 'Market is closed. Scanning resumes during the next regular session.',
  };
  return messages[data?.error] || messages[data?.status] || data?.options?.error || 'No live setup matched the rules.';
}

function renderTradeBrainSetup(setup, budget) {
  const option = setup.instrument !== 'equity';
  const maxLoss = option ? setup.estimated_max_loss_per_contract_at_indicative_ask : setup.max_loss_per_share_to_invalidation;
  const riskUnit = option ? 'per contract' : 'per share';
  const quantity = budget > 0 && maxLoss > 0 ? Math.floor(budget / maxLoss) : null;
  const qtyLabel = quantity === null ? 'Set risk cap for size' : quantity > 0 ? `${integer(quantity)} ${option ? 'contract' : 'share'}${quantity === 1 ? '' : 's'}` : 'Below risk cap';
  const instrumentTitle = option ? `LONG ${setup.instrument.toUpperCase()}` : 'COMMON STOCK';
  const optionDetails = option ? `<div><span>Contract</span><b class="mono">${esc(setup.symbol)}</b></div><div><span>Expiration</span><b>${esc(setup.expiration)} · ${setup.dte} days</b></div><div><span>Indicative bid / ask</span><b>${money(setup.indicative_bid)} / ${money(setup.indicative_ask)}</b></div><div><span>Alpaca model delta · IV</span><b>${Number(setup.delta).toFixed(2)} · ${(Number(setup.implied_volatility) * 100).toFixed(1)}%</b></div><div><span>Open interest</span><b>${integer(setup.open_interest)} · ${esc(setup.open_interest_as_of)}</b></div><div><span>Quote source</span><b>Alpaca Indicative · ${utcTimestamp(setup.quote_at)}</b></div><div><span>Last trade · delayed</span><b>${setup.delayed_trade_at ? `${utcTimestamp(setup.delayed_trade_at)} · ${setup.trade_delay_minutes}m source delay` : 'Not provided'}</b></div>` : `<div><span>Quote feed</span><b>${esc(String(setup.quote_feed || 'IEX').toUpperCase())} · ${utcTimestamp(setup.quote_at)}</b></div><div><span>Risk to invalidation</span><b>${money(setup.max_loss_per_share_to_invalidation)} per share</b></div>`;
  const priceLabel = option ? 'Indicative midpoint reference' : 'Entry reference';
  const price = option ? setup.indicative_midpoint_reference : setup.entry_limit_reference;
  const maxLossLabel = option ? 'Est. max loss at indicative ask' : `Maximum loss ${riskUnit}`;
  return `<article class="brain-setup"><div class="brain-setup-head"><div><span class="eyebrow">${esc(instrumentTitle)}</span><h3>${esc(setup.underlying || setup.symbol)}</h3></div><span class="brain-live-dot ${option ? 'indicative' : ''}">${option ? 'INDICATIVE' : 'LIVE'}</span></div><div class="brain-setup-grid"><div><span>${priceLabel}</span><b>${money(price)}</b></div><div><span>Underlying invalidation</span><b>${money(setup.invalidation)}</b></div><div><span>Underlying objective</span><b>${money(setup.underlying_objective || setup.objective)}</b></div><div><span>${maxLossLabel}</span><b>${money(maxLoss)}</b></div><div><span>Size at risk cap</span><b>${qtyLabel}</b></div>${optionDetails}</div>${option ? '<p class="brain-feed-note">Modified quote reference only. Confirm the current broker bid and ask before any order.</p>' : ''}<p class="brain-rationale">${esc(setup.rationale)}</p></article>`;
}

function renderTradeBrain() {
  const symbols = [...new Set(state.watchlist.map(normalizeTicker).filter(Boolean))].slice(0, 5);
  const budget = state.tradeBrainRiskBudget || 0;
  const rows = symbols.map((symbol) => {
    const data = state.tradeBrain.scans[symbol];
    if (!data) return `<article class="brain-symbol"><div class="brain-symbol-head"><b>${esc(symbol)}</b><span>${state.tradeBrain.scanning ? 'Waiting for live scan' : 'Not scanned yet'}</span></div></article>`;
    const receivedAt = Date.parse(data.received_at || '');
    const fresh = Number.isFinite(receivedAt) && Date.now() - receivedAt <= 90000 && Date.now() >= receivedAt - 5000;
    const setups = fresh && data.status === 'connected' ? (Array.isArray(data.setups) ? data.setups : []).filter((setup) => setup.instrument === 'equity' ? ['sip', 'iex'].includes(setup.quote_feed) : setup.feed === 'indicative' && setup.price_basis === 'modified_indicative_quote' && setup.execution_status === 'broker_quote_required' && data.options?.feed === 'indicative') : [];
    const stockSetupCount = setups.filter((setup) => setup.instrument === 'equity').length;
    const optionSetupCount = setups.filter((setup) => ['call', 'put'].includes(setup.instrument)).length;
    const setupSummary = [stockSetupCount ? `${stockSetupCount} live stock setup${stockSetupCount === 1 ? '' : 's'}` : '', optionSetupCount ? `${optionSetupCount} indicative option candidate${optionSetupCount === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ');
    const status = data.status === 'unavailable' ? tradeBrainReason(data) : !fresh && data.status !== 'market_closed' ? 'Scan expired · no setup shown' : data.status === 'connected' ? setupSummary || 'No setup matched the rules' : tradeBrainReason(data);
    const age = Number.isFinite(receivedAt) ? `${data.status === 'connected' ? 'Updated' : 'Checked'} ${utcTimestamp(data.received_at)}${data.status === 'connected' ? ` · ${data.feeds?.underlying || data.underlying_quote?.feed || 'live data'}` : ''}` : '';
    const cards = setups.map((setup) => renderTradeBrainSetup(setup, budget)).join('');
    const metrics = data.indicators ? `<div class="brain-evidence"><span>Close ${money(data.indicators.latest_close)}</span><span>SMA 20 ${money(data.indicators.sma20)}</span><span>SMA 50 ${money(data.indicators.sma50)}</span><span>RSI ${Number(data.indicators.rsi14).toFixed(1)}</span><span>ATR ${money(data.indicators.atr14)}</span><span>Daily bars through ${utcTimestamp(data.indicators.as_of)}</span></div>` : '';
    const quote = state.tradeBrain.liveQuotes[symbol];
    const quoteAt = Date.parse(quote?.quote?.at || '');
    const quoteAge = Number.isFinite(quoteAt) ? Date.now() - quoteAt : Number.POSITIVE_INFINITY;
    const quotePanel = quoteAge >= -5000 && quoteAge <= 90000
      ? `<div class="brain-stream-quote"><span>Streaming ${esc(String(quote.feed || 'iex').toUpperCase())} · bid / ask</span><b>${money(quote.quote.bid)} / ${money(quote.quote.ask)}</b><small>Provider ${utcTimestamp(quote.quote.at)} · received ${utcTimestamp(quote.received_at)}</small></div>`
      : quote ? `<div class="brain-stream-quote stale"><span>Streaming ${esc(String(quote.feed || 'iex').toUpperCase())} quote is stale</span><small>Last provider quote ${utcTimestamp(quote.quote.at)}</small></div>` : '';
    return `<article class="brain-symbol"><div class="brain-symbol-head"><div><b>${esc(symbol)}</b><small>${esc(status)}</small></div><span class="brain-time">${esc(age)}</span></div>${quotePanel}${metrics}${cards}${data.options?.status === 'unavailable' ? `<p class="brain-feed-note">Options: ${esc(tradeBrainReason({ error: data.options.error }))}</p>` : ''}</article>`;
  }).join('');
  const lastScan = state.tradeBrain.lastScanAt ? `Last scan ${utcTimestamp(state.tradeBrain.lastScanAt)}` : 'Waiting for first scan';
  const status = state.tradeBrain.scanning ? 'Scanning live feeds…' : lastScan;
  const streamFeed = String(state.tradeBrain.streamFeed || 'iex').toUpperCase();
  const streamStatus = state.tradeBrain.streamError === 'market_data_authentication_failed' ? 'Alpaca rejected the market-data credentials'
    : state.tradeBrain.streamError === 'iex_entitlement_unavailable' ? 'IEX access not enabled'
      : state.tradeBrain.streamError === 'iex_stream_unavailable' ? 'IEX stream unavailable'
        : ({ idle: 'Waiting for Trade Brain', awaiting_subscription: `Opening ${streamFeed} stream`, connecting: `Connecting to ${streamFeed}`, authenticated: `${streamFeed} authenticated`, subscribed: `${streamFeed} connected · waiting for quotes`, live: `Streaming ${streamFeed} quotes`, disconnected: 'Disconnected · reconnecting', fallback: 'Using IEX feed', unavailable: 'Stock feed unavailable' })[state.tradeBrain.streamStatus] || `Stock stream starting · ${streamFeed}`;
  const streamDotClass = ['live', 'subscribed'].includes(state.tradeBrain.streamStatus) ? 'live' : state.tradeBrain.streamStatus === 'unavailable' ? 'unavailable' : 'waiting';
  return `${pageHeading('LIVE MARKET SCAN', 'Trade Brain', 'Scans Alpaca stock quotes and modified indicative option quotes once per minute while this page is open.', `<button class="button primary" data-action="brain-scan" ${state.tradeBrain.scanning ? 'disabled' : ''}>${state.tradeBrain.scanning ? 'Scanning…' : '↻ Scan now'}</button>`)}
    <section class="brain-controls"><div><b>${esc(status)}</b><small>Scans up to five symbols from your browser watchlist · no orders are sent</small></div><form id="brain-risk-form"><label class="field-label">MAX LOSS PER IDEA ($)<input name="riskBudget" type="number" min="1" max="100000000" step="1" value="${budget || ''}" placeholder="Enter your limit" required /></label><button class="button secondary">Save risk cap</button></form></section>
    <section class="brain-feed-strip"><span><i class="brain-stream-dot ${streamDotClass}"></i>Stock quotes · ${esc(streamStatus)}</span><span>IEX completed daily bars</span><span>Alpaca indicative options · each scan</span><span>Modified quotes · trades delayed 15m</span></section>
    ${rows ? `<div class="brain-symbol-list">${rows}</div>` : `<section class="panel brain-empty"><h2>No watchlist symbols</h2><p>Add symbols in Watchlists to start the automated scan.</p><button class="button secondary" data-view="watchlists">Open watchlists</button></section>`}
    <div class="brain-footnote">The stock stream and scans run while this page is open. SIP is consolidated; IEX covers one exchange. Alpaca indicative option quotes are modified, and the latest option trades are delayed 15 minutes. Option prices and risk sizing are references, not executable quotes. Closing the page stops scans; order placement is disabled.</div>`;
}

async function scanTradeBrain() {
  if (state.tradeBrain.scanning) return;
  const symbols = [...new Set(state.watchlist.map(normalizeTicker).filter(Boolean))].slice(0, 5);
  if (!symbols.length) { state.tradeBrain.status = 'empty'; render(); return; }
  state.tradeBrain.scanning = true;
  state.tradeBrain.status = 'scanning';
  render();
  for (const symbol of symbols) {
    try {
      const response = await fetch(`/api/alpaca/brain/scan?symbol=${encodeURIComponent(symbol)}`, { headers: { Accept: 'application/json' }, cache: 'no-store' });
      const data = await response.json();
      if (data?.symbol && data.symbol !== symbol) throw new Error('The live scan returned an unexpected source record.');
      if (data?.schema !== 'SHIPYARD_TRADE_BRAIN_SCAN_V2') throw new Error('The live scan returned an unexpected source record.');
      if (data.status === 'connected') {
        if (!['Alpaca SIP', 'Alpaca IEX'].includes(data.feeds?.underlying) || !['sip', 'iex'].includes(data.underlying_quote?.feed) || data.feeds.underlying !== `Alpaca ${data.underlying_quote.feed.toUpperCase()}` || data.feeds?.history !== 'Alpaca IEX daily bars' || data.session_calendar?.source !== 'alpaca_iex_calendar_v3') throw new Error('The live scan source checks failed.');
        const age = Date.now() - Date.parse(data.received_at || '');
        if (!Number.isFinite(age) || age > 90000 || age < -5000) { data.status = 'stale'; data.error = 'underlying_quote_stale_or_invalid'; data.setups = []; }
        else data.setups = (Array.isArray(data.setups) ? data.setups : []).filter((setup) => {
          const quoteAge = (Date.now() - Date.parse(setup.quote_at || '')) / 1000;
          if (setup.instrument === 'equity') {
            const baseFieldsValid = Number.isFinite(setup.entry_limit_reference) && Number.isFinite(setup.invalidation) && Number.isFinite(setup.max_loss_per_share_to_invalidation);
            return ['sip', 'iex'].includes(setup.quote_feed) && setup.quote_feed === data.underlying_quote.feed && setup.symbol === symbol && setup.side === 'long' && Number.isFinite(quoteAge) && quoteAge >= -5 && quoteAge <= 90 && baseFieldsValid && setup.objective > setup.entry_limit_reference;
          }
          const optionFieldsValid = Number.isFinite(setup.indicative_midpoint_reference) && Number.isFinite(setup.invalidation) && Number.isFinite(setup.estimated_max_loss_per_contract_at_indicative_ask);
          return ['call', 'put'].includes(setup.instrument) && setup.feed === 'indicative' && setup.price_basis === 'modified_indicative_quote' && setup.execution_status === 'broker_quote_required' && data.options?.feed === 'indicative' && data.options?.execution_pricing === false && setup.underlying === symbol && Number.isFinite(quoteAge) && quoteAge >= -5 && quoteAge <= 90 && optionFieldsValid && setup.estimated_max_loss_per_contract_at_indicative_ask > 0 && setup.multiplier === 100 && setup.dte >= 21 && setup.dte <= 45 && (setup.instrument !== 'call' || setup.delta > 0) && (setup.instrument !== 'put' || setup.delta < 0);
        });
      }
      state.tradeBrain.scans[symbol] = data;
      state.tradeBrain.status = 'updated';
    } catch (error) {
      state.tradeBrain.scans[symbol] = { status: 'unavailable', error: 'provider_request_failed', message: error.message, symbol, setups: [] };
      state.tradeBrain.status = 'partial';
    }
    if (state.view === 'brain') render();
    if (state.tradeBrain.scans[symbol]?.error === 'rate_limited' || state.tradeBrain.scans[symbol]?.error === 'provider_rate_limited') break;
  }
  state.tradeBrain.scanning = false;
  state.tradeBrain.lastScanAt = new Date().toISOString();
  if (state.view === 'brain') render();
}

let tradeBrainSocket = null;
let tradeBrainSocketSymbols = '';
let tradeBrainRetryTimer = null;
let tradeBrainRetryCount = 0;
let tradeBrainRenderTimer = null;
let tradeBrainRetryBlocked = false;

function scheduleTradeBrainStreamRender() {
  if (tradeBrainRenderTimer !== null) return;
  tradeBrainRenderTimer = window.setTimeout(() => {
    tradeBrainRenderTimer = null;
    if (state.view === 'brain') render();
  }, 250);
}

function disconnectTradeBrainStream() {
  if (tradeBrainRetryTimer !== null) window.clearTimeout(tradeBrainRetryTimer);
  tradeBrainRetryTimer = null;
  const socket = tradeBrainSocket;
  tradeBrainSocket = null;
  tradeBrainSocketSymbols = '';
  if (socket && socket.readyState < WebSocket.CLOSING) {
    try { socket.close(1000, 'Trade Brain page is inactive'); } catch { /* socket already closed */ }
  }
  if (!tradeBrainRetryBlocked && state.tradeBrain.streamStatus !== 'idle') state.tradeBrain.streamStatus = 'idle';
}

function scheduleTradeBrainStreamReconnect(socket) {
  if (socket !== tradeBrainSocket || tradeBrainRetryBlocked || state.view !== 'brain' || document.visibilityState === 'hidden' || tradeBrainRetryTimer !== null) return;
  state.tradeBrain.streamStatus = 'disconnected';
  scheduleTradeBrainStreamRender();
  const delay = Math.min(30000, 1000 * (2 ** Math.min(tradeBrainRetryCount, 5)));
  tradeBrainRetryCount += 1;
  tradeBrainRetryTimer = window.setTimeout(() => {
    tradeBrainRetryTimer = null;
    if (socket === tradeBrainSocket) { tradeBrainSocket = null; tradeBrainSocketSymbols = ''; }
    connectTradeBrainStream();
  }, delay);
}

function connectTradeBrainStream(force = false) {
  if (force) { tradeBrainRetryBlocked = false; tradeBrainRetryCount = 0; state.tradeBrain.streamError = ''; }
  const symbols = [...new Set(state.watchlist.map(normalizeTicker).filter(Boolean))].slice(0, 5);
  if (state.view !== 'brain' || document.visibilityState === 'hidden' || !symbols.length) { disconnectTradeBrainStream(); return; }
  if (tradeBrainRetryBlocked || state.tradeBrain.streamError === 'iex_entitlement_unavailable') return;
  const key = symbols.join(',');
  if (tradeBrainSocket && tradeBrainSocketSymbols === key && tradeBrainSocket.readyState < WebSocket.CLOSING) return;
  disconnectTradeBrainStream();
  tradeBrainRetryBlocked = false;
  tradeBrainSocketSymbols = key;
  state.tradeBrain.streamStatus = 'awaiting_subscription';
  state.tradeBrain.streamError = '';
  scheduleTradeBrainStreamRender();
  let socket;
  try {
    socket = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/api/alpaca/stream`);
  } catch {
    state.tradeBrain.streamStatus = 'unavailable';
    scheduleTradeBrainStreamRender();
    return;
  }
  tradeBrainSocket = socket;
  socket.addEventListener('open', () => {
    if (socket !== tradeBrainSocket) return;
    state.tradeBrain.streamStatus = 'connecting';
    try { socket.send(JSON.stringify({ action: 'subscribe', symbols })); }
    catch { scheduleTradeBrainStreamReconnect(socket); }
    scheduleTradeBrainStreamRender();
  });
  socket.addEventListener('message', (event) => {
    if (socket !== tradeBrainSocket || typeof event.data !== 'string') return;
    let message;
    try { message = JSON.parse(event.data); } catch { return; }
    if (message?.type === 'status') {
      state.tradeBrain.streamStatus = message.status || 'unavailable';
      if (message.feed) state.tradeBrain.streamFeed = message.feed;
      state.tradeBrain.streamError = message.error || '';
      if (message.error === 'iex_entitlement_unavailable') tradeBrainRetryBlocked = true;
      if (message.status === 'live' || message.status === 'subscribed') tradeBrainRetryCount = 0;
      scheduleTradeBrainStreamRender();
    } else if (message?.type === 'quote') {
      const symbol = normalizeTicker(message.symbol);
      const quote = message.quote;
      const quoteAt = Date.parse(quote?.at || '');
      if (!symbol || !symbols.includes(symbol) || !['sip', 'iex'].includes(message.feed)
        || ![quote?.bid, quote?.ask, quote?.bid_size, quote?.ask_size].every(Number.isFinite)
        || quote.bid <= 0 || quote.ask < quote.bid || quote.bid_size <= 0 || quote.ask_size <= 0
        || !Number.isFinite(quoteAt) || quoteAt > Date.now() + 5000 || Date.now() - quoteAt > 90000) return;
      state.tradeBrain.liveQuotes[symbol] = { quote, received_at: message.received_at, feed: message.feed };
      state.tradeBrain.streamStatus = 'live';
      scheduleTradeBrainStreamRender();
    }
  });
  socket.addEventListener('error', () => {
    if (socket !== tradeBrainSocket) return;
    state.tradeBrain.streamStatus = 'unavailable';
    scheduleTradeBrainStreamRender();
  });
  socket.addEventListener('close', () => scheduleTradeBrainStreamReconnect(socket));
}

function refreshTradeBrain() {
  if (state.view !== 'brain' || document.visibilityState === 'hidden') { disconnectTradeBrainStream(); return; }
  connectTradeBrainStream();
  if (state.tradeBrain.scanning) return;
  const last = Date.parse(state.tradeBrain.lastScanAt || '');
  if (!Number.isFinite(last) || Date.now() - last >= LIVE_BRAIN_REFRESH_MS) void scanTradeBrain();
}

function renderApi() {
  const status = state.apiStatus || { mode: 'unconfigured', provider: 'Checking Site configuration…', keyConfigured: false, allowedReads: [] };
  const feed = state.alpacaFeed || {};
  const symbol = normalizeTicker(feed.symbol || state.ticker) || 'SPY';
  const configured = status.keyConfigured === true;
  return `${pageHeading('DATA SOURCE & PRIVACY', 'Connections and data rights', 'Review which feeds are live, which tools use local inputs, and how data is handled.', '<button class="button secondary" data-action="refresh-status">↻ Refresh status</button>')}
    <div class="connection-card ${configured ? 'connected' : ''}"><div class="connection-state-icon">${configured ? '✓' : '◉'}</div><div class="connection-main"><span class="eyebrow">SERVER-SIDE CONFIGURATION</span><h2>${configured ? 'Alpaca market-data credentials are present' : 'Alpaca market-data credentials are not configured'}</h2><p>${configured ? 'The Site Worker holds the credentials. Load a symbol in Alpaca charts to validate feed access.' : 'Market-data charts require the owner-configured runtime secrets.'}</p></div><div class="connection-badge">${configured ? label('SECRET · SERVER ONLY', 'green-badge') : label('NOT CONFIGURED', 'orange')}</div></div>
    <div class="api-settings-grid"><div class="api-settings-main">${panel('Available server reads', 'Live market-data routes.', `<div class="endpoint-list"><div><code>GET</code><span>/api/alpaca/brain/scan?symbol=SPY</span><small>Fresh SIP quote or IEX fallback, completed IEX daily history, verified session, and Alpaca indicative option snapshots</small></div><div><code>WS</code><span>/api/alpaca/stream</span><small>Server-authenticated SIP stream with automatic IEX fallback for the browser watchlist</small></div><div><code>GET</code><span>/api/alpaca/bars?symbol=SPY&amp;days=90</span><small>Alpaca IEX daily bars, split-adjusted, one symbol per request</small></div><div><code>GET</code><span>/api/terminal/context</span><small>Published Chartlector, Treasury, Federal Reserve, and Cboe observations with source dates</small></div><div><code>POST</code><span>/mcp</span><small>Read-only context, daily bars, live Trade Brain scans, and readiness tools</small></div></div>`, '')}${panel('Yahoo Finance', 'External source link.', `<p><a href="https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}/" target="_blank" rel="noopener noreferrer">Open ${esc(symbol)} on Yahoo Finance ↗</a></p><p class="small-muted">Yahoo is a link-out only. Live quotes and charts use Alpaca.</p>`, '')}${panel('Data used by each tool', 'Live feeds and local studies are separated.', `<ul class="setup-steps"><li><b>Trade Brain</b><span>Streaming SIP quotes when entitled with automatic live IEX fallback, completed IEX daily bars, verified session hours, and current Alpaca indicative option snapshots. Failed or stale inputs produce no setup.</span></li><li><b>Market charts</b><span>Alpaca IEX completed daily bars with source timestamps.</span></li><li><b>Local research labs</b><span>CSV uploads are user-supplied snapshots. They are not live or refreshed and do not feed Trade Brain.</span></li><li><b>Unavailable feeds</b><span>Options flow, dark-pool, news, disclosures, and broad-market screener views stay empty until live sources are connected.</span></li></ul>`, '')}</div>
    <aside class="api-settings-side">${panel('Connection status', esc(status.provider || 'Unknown'), `<div class="status-details"><div><span>Alpaca keys</span><b>${configured ? 'Present · not validated until request' : 'Not configured'}</b></div><div><span>Market feeds</span><b>IEX bars · SIP / IEX quotes · Alpaca indicative options</b></div><div><span>Account balances / positions</span><b>Not exposed</b></div><div><span>Orders / trading</span><b>Not available</b></div><div><span>Browser storage</span><b>Watchlists and alerts stay local</b></div></div>`, '')}${panel('Provider references', 'Official documentation and source links', `<div class="reference-links"><a href="https://docs.alpaca.markets/us/docs/about-market-data-api" target="_blank" rel="noopener noreferrer">Alpaca Market Data API ↗</a><a href="https://docs.alpaca.markets/us/reference/stockbars" target="_blank" rel="noopener noreferrer">Historical bars reference ↗</a><a href="https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html" target="_blank" rel="noopener noreferrer">Yahoo Terms of Service ↗</a><a href="https://github.com/dwj9ddyvf6-hub/Silicon/blob/main/apps/silicon-market-terminal/vendor-coverage.json" target="_blank" rel="noopener noreferrer">86-family coverage registry ↗</a></div>`, '')}</aside></div>
    <div class="privacy-footnote"><b>Data scope</b><span>Market bars and public context. Account and order data are off. CSVs, watchlists, and alerts stay in this browser.</span></div>`;
}

function renderModal() { /* reserved for future focused detail panels */ }

function render() {
  renderShell();
  if (state.view === 'brain') connectTradeBrainStream();
  else disconnectTradeBrainStream();
  const appShell = document.querySelector('.app-shell');
  if (state.mobileNavOpen) appShell?.classList.add('mobile-nav-open');
}

function navigate(view) {
  state.view = view;
  if (location.hash !== `#${view}`) history.pushState({ view }, '', `#${view}`);
  render();
  if ((view === 'overview' || view === 'charts') && (state.alpacaFeed.status === 'idle' || state.alpacaFeed.symbol !== state.ticker)) void loadAlpacaBars(state.ticker);
  if (view === 'context' && state.marketContext.status === 'idle') void loadMarketContext();
  if (view === 'alpaca' && state.alpacaFeed.status === 'idle') void loadAlpacaBars();
  if (view === 'ticker' && (state.alpacaFeed.status === 'idle' || state.alpacaFeed.symbol !== state.ticker)) void loadAlpacaBars(state.ticker);
  if (view === 'enginehub' && state.morgueReadiness?.status === 'idle') void loadMorgueReadiness();
  if (view === 'brain') refreshTradeBrain();
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

async function refreshStatus() {
  const button = document.querySelector('[data-action="refresh-status"]');
  if (button) { button.disabled = true; button.textContent = 'Checking…'; }
  try {
    const response = await fetch('/api/status', { headers: { Accept: 'application/json' } });
    state.apiStatus = await response.json();
  } catch {
    state.apiStatus = { mode: 'unconfigured', provider: 'Site status unavailable', keyConfigured: false, allowedReads: [] };
  }
  render();
}

async function importStrategyCsv(file) {
  try {
    if (file.size > 20 * 1024 * 1024) throw new Error('CSV files must be 20 MiB or smaller.');
    const bytes = new Uint8Array(await file.arrayBuffer());
    const rows = parseStrategyCsv(new TextDecoder().decode(bytes));
    let artifactSha256 = null;
    let evidenceError = '';
    try {
      artifactSha256 = await window.SiliconEvidenceContract.sha256Hex(bytes);
    } catch (error) {
      evidenceError = error instanceof Error ? error.message : 'Could not hash the CSV bytes.';
    }
    state.strategy.rows = rows;
    state.strategy.filename = file.name;
    state.strategy.source = 'csv';
    state.strategy.artifactSha256 = artifactSha256;
    state.strategy.evidence = null;
    state.strategy.evidenceError = evidenceError;
    state.strategy.error = '';
    state.strategy.notice = `Loaded ${rows.length.toLocaleString()} ordered observations. File loaded in this browser tab.`;
  } catch (error) {
    state.strategy.error = error.message || 'Could not read this CSV.';
    state.strategy.notice = 'CSV could not be read. The previous data is still loaded.';
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
    target.notice = 'CSV could not be loaded. Previous rows remain available.';
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
    target.notice = `Loaded ${parsed.rows.length.toLocaleString()} option rows for ${parsed.ticker} as of ${parsed.asOf}. File remains in this tab.`;
  } catch (error) {
    target.error = error.message || 'Could not read this option-chain CSV.';
    target.notice = 'CSV could not be loaded. The previous chain remains available.';
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
    target.notice = 'CSV could not be loaded. The previous profile remains available.';
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
    target.notice = 'CSV could not be loaded. The previous snapshot remains available.';
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
    target.notice = 'CSV could not be loaded. The previous snapshot remains available.';
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

async function importConvergenceEvidenceCsv(file) {
  const engine = window.SiliconConvergenceEngine;
  state.convergenceImport = { status: 'loading', filename: file.name, records: [], rejected: [], headers: [], importedAt: null, error: '' };
  render();
  try {
    if (!engine?.parseEvidenceCsv) throw new Error('The convergence CSV contract did not load.');
    if (file.size > engine.MAX_EVIDENCE_CSV_BYTES) throw new Error('CSV exceeds the 10 MiB local import limit.');
    const parsed = engine.parseEvidenceCsv(await file.text());
    state.convergenceImport = { ...parsed, status: 'ready', filename: file.name, importedAt: new Date().toISOString(), error: '' };
  } catch (error) {
    state.convergenceImport = { status: 'error', filename: file.name, records: [], rejected: [], headers: [], importedAt: null, error: error instanceof Error ? error.message : 'Could not read this CSV.' };
  }
  render();
}

function downloadConvergenceText(filename, value, contentType) {
  const blob = new Blob([value], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function downloadConvergenceTemplate() {
  downloadConvergenceText('silicon-evidence-envelope-template.csv', 'ObservedAt,Entity,Source,Metric,Value,PublicAt,ReceivedAt,Unit,Method,Confidence,EventType,SourceURL\r\n', 'text/csv;charset=utf-8');
}

function exportConvergenceEvidence() {
  const imported = state.convergenceImport;
  if (!Array.isArray(imported?.records) || !imported.records.length) return;
  const payload = { schema: 'SILICON_RESEARCH_EVIDENCE_V1', filename: imported.filename, importedAt: imported.importedAt, headers: imported.headers, records: imported.records };
  const filename = 'silicon-research-evidence-' + new Date().toISOString().slice(0, 10) + '.json';
  downloadConvergenceText(filename, JSON.stringify(payload, null, 2), 'application/json;charset=utf-8');
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

async function downloadStrategyEvidenceBundle() {
  const strategy = state.strategy;
  const result = analyzeStrategy(strategy);
  try {
    const evidence = await buildStrategyEvidence(strategy, result);
    if (!evidence.observationValidation.valid || !evidence.featureValidation.valid) {
      throw new Error('The evidence contract rejected an observation or feature record.');
    }
    const bundle = {
      format: 'silicon.strategy-lab-evidence-bundle',
      bundleVersion: '1.0.0',
      contractVersion: window.SiliconEvidenceContract.EVIDENCE_CONTRACT.contractVersion,
      sourceRegistryVersion: window.SiliconEvidenceContract.EVIDENCE_CONTRACT.sourceRegistryVersion,
      exportedAt: evidence.feature.computedAt,
      observation: evidence.observation,
      feature: evidence.feature,
      parameters: evidence.parameters,
      analysis: evidence.analysis,
      validation: { observation: evidence.observationValidation, feature: evidence.featureValidation },
      eligibility: { decision: evidence.decisionEligibility, lineage: evidence.lineageEligibility },
      limitations: [
        'The CSV source, market-data entitlement, corporate-action treatment, venue calendar, timezone, and point-in-time availability are not independently verified.',
        'Close-only replay. It excludes fills, costs, exercise, and assignment; results cover this input period.',
      ],
    };
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `strategy-lab-evidence-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    strategy.evidence = {
      inputSha256: strategy.artifactSha256,
      resultSha256: evidence.feature.resultSha256,
      observationValid: evidence.observationValidation.valid,
      featureValid: evidence.featureValidation.valid,
      blockers: [...new Set([...evidence.decisionEligibility.blockers, ...evidence.lineageEligibility.blockers])],
    };
    strategy.evidenceError = '';
  } catch (error) {
    strategy.evidenceError = error instanceof Error ? error.message : 'Could not create the evidence bundle.';
  }
  render();
}

document.addEventListener('click', (event) => {
  const navButton = event.target.closest('[data-view]');
  if (navButton) { event.preventDefault(); navigate(navButton.dataset.view); return; }
  const symbolButton = event.target.closest('[data-symbol]');
  if (symbolButton) { if (selectTicker(symbolButton.dataset.symbol)) navigate('ticker'); return; }
  const action = event.target.closest('[data-action]');
  if (!action) return;
  const name = action.dataset.action;
  if (name === 'brain-scan') { void scanTradeBrain(); return; }
  if (name === 'convergence-template') { downloadConvergenceTemplate(); return; }
  if (name === 'convergence-export') { exportConvergenceEvidence(); return; }
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
  if (name === 'refresh-morgue-readiness') void loadMorgueReadiness();
  if (name === 'run-research-pipeline') void runResearchPipeline();
  if (name === 'export-research-evidence') exportResearchEvidenceBundle();
  if (name === 'chart-range') { state.chartRange = action.dataset.value; render(); }
  if (name === 'save-chart') { state.savedLayouts.unshift({ symbol: state.chartSymbol, range: state.chartRange, savedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }); state.savedLayouts = state.savedLayouts.slice(0, 12); state.layoutMessage = `Saved ${state.chartSymbol} ${state.chartRange} locally`; persist(); render(); }
  if (name === 'load-layout') { const layout = state.savedLayouts[Number(action.dataset.index)]; if (layout) { state.chartSymbol = layout.symbol; state.chartRange = layout.range; state.layoutMessage = `Loaded ${layout.symbol} ${layout.range}`; render(); } }
  if (name === 'toggle-indicators') { action.classList.toggle('selected'); document.querySelector('.chart-tools')?.classList.toggle('highlighted'); }
  if (name === 'fullscreen') { document.querySelector('.chart-workspace')?.classList.toggle('chart-fullscreen'); }
  if (name === 'reset-overlays') { document.querySelectorAll('.toggle-row input').forEach((input, i) => { input.checked = i < 2; }); }
  if (name === 'news-tag') { state.newsSearch = action.dataset.value === 'all' ? '' : action.dataset.value; render(); }
  if (name === 'portfolio-export') exportDanelfinPortfolioAudit();
  if (name === 'stockrover-template') downloadStockRoverFactorTemplate();
  if (name === 'stockrover-export') exportStockRoverFactorAudit();
  if (name === 'static-gex-export') exportStaticGexContractAudit();
  if (name === 'strategy-save-run') saveStrategyRun();
  if (name === 'strategy-export') downloadStrategyReport();
  if (name === 'strategy-evidence-export') void downloadStrategyEvidenceBundle();
});

document.addEventListener('click', (event) => {
  if (event.target.closest('[data-action="refresh-market-context"]')) { event.preventDefault(); void loadMarketContext(); }
  if (event.target.closest('[data-action="refresh-alpaca-bars"]')) { event.preventDefault(); void loadAlpacaBars(); }
});
document.addEventListener('submit', (event) => {
  const form = event.target;
  if (form?.id === 'alpaca-chart-form') {
    event.preventDefault();
    const fields = Object.fromEntries(new FormData(form).entries());
    void loadAlpacaBars(fields.symbol, fields.days);
  }
});

document.addEventListener('change', (event) => {
  if (event.target.name === 'exerciseStyle') {
    const treeSteps = document.querySelector('#option-strategy-form [name="treeSteps"]');
    if (treeSteps) treeSteps.disabled = event.target.value !== 'american';
    return;
  }
  if (event.target.id === 'convergence-evidence-file') {
    const file = event.target.files?.[0];
    if (file) void importConvergenceEvidenceCsv(file);
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

document.addEventListener('submit', async (event) => {
  const form = event.target;
  if (form.id === 'brain-risk-form') {
    event.preventDefault();
    const amount = Number(new FormData(form).get('riskBudget'));
    if (!Number.isFinite(amount) || amount < 1 || amount > 100000000) return;
    state.tradeBrainRiskBudget = amount;
    persist();
    render();
  }
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
    const threshold = Number(fields.threshold);
    if (!Number.isFinite(threshold) || threshold <= 0) return;
    state.alerts.unshift({ ticker, condition: fields.condition, threshold, type: fields.type, created: new Date().toLocaleString(), lastEvaluation: null });
    state.showAlertForm = false; persist(); render();
  }
  if (form.id === 'payoff-form') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    state.payoff = { type: fields.type, side: fields.side, strike: Number(fields.strike), premium: Number(fields.premium), contracts: Math.max(1, Number(fields.contracts)), spot: Number(fields.spot) };
    render();
  }
  if (form.id === 'option-strategy-form') {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(form).entries());
    state.optionLab.evidence = null;
    state.optionLab.evidenceError = '';
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
      try {
        state.optionLab.evidence = await buildOptionStrategyEvidence(state.optionLab);
      } catch (evidenceError) {
        state.optionLab.evidenceError = evidenceError instanceof Error ? evidenceError.message : 'Evidence contract validation failed.';
      }
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
    state.strategy.evidence = null;
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

window.addEventListener('popstate', () => { state.view = location.hash.slice(1) || 'overview'; render(); if (state.view === 'overview' && (state.alpacaFeed.status === 'idle' || state.alpacaFeed.symbol !== state.ticker)) void loadAlpacaBars(state.ticker); if (state.view === 'context' && state.marketContext.status === 'idle') void loadMarketContext(); if (state.view === 'alpaca' && state.alpacaFeed.status === 'idle') void loadAlpacaBars(); if (state.view === 'ticker' && (state.alpacaFeed.status === 'idle' || state.alpacaFeed.symbol !== state.ticker)) void loadAlpacaBars(state.ticker); if (state.view === 'enginehub' && state.morgueReadiness.status === 'idle') void loadMorgueReadiness(); if (state.view === 'brain') refreshTradeBrain(); });
window.addEventListener('popstate', () => { if (state.view === 'charts' && (state.alpacaFeed.status === 'idle' || state.alpacaFeed.symbol !== state.ticker)) void loadAlpacaBars(state.ticker); });
let compactChartLayout = window.SiliconMarketOverview?.lineChartAxisLayout?.(window.innerWidth)?.compact === true;
window.addEventListener('resize', () => {
  const nextCompactLayout = window.SiliconMarketOverview?.lineChartAxisLayout?.(window.innerWidth)?.compact === true;
  if (nextCompactLayout !== compactChartLayout) {
    compactChartLayout = nextCompactLayout;
    render();
  }
}, { passive: true });
render();
if (state.view === 'brain') refreshTradeBrain();
if (state.view === 'overview' || state.view === 'charts') void loadAlpacaBars(state.ticker);
if (state.view === 'context') void loadMarketContext();
if (state.view === 'alpaca') void loadAlpacaBars();
if (state.view === 'ticker') void loadAlpacaBars(state.ticker);
if (state.view === 'enginehub') void loadMorgueReadiness();
fetch('./vendor-coverage.json?v=b3a79c616990446f', { headers: { Accept: 'application/json' } })
  .then(response => { if (!response.ok) throw new Error('Could not load the local family registry.'); return response.json(); })
  .then(registry => {
    state.vendorFamilies = Array.isArray(registry.families) ? registry.families : [];
    state.vendorCoverageMeta = normalizeVendorCoverageMeta(registry);
    if (state.view === 'coverage' || state.view === 'evidence') render();
  })
  .catch(() => {
    state.coverageError = 'The local 86-family registry could not be loaded.';
    if (state.view === 'coverage' || state.view === 'evidence') render();
  });
fetch('/api/status', { headers: { Accept: 'application/json' } }).then(r => r.json()).then(s => { state.apiStatus = s; if (state.view === 'api') render(); }).catch(() => { state.apiStatus = { mode: 'unconfigured', provider: 'Site status unavailable', keyConfigured: false, allowedReads: [] }; if (state.view === 'api') render(); });
