(() => {
  'use strict';

  const SNAPSHOT_URL = './data/desk-snapshot.json';
  const POLL_MS = 30000;
  const STALE_AFTER_MS = 15 * 60 * 1000;
  let snapshot = null;

  const byId = (id) => document.getElementById(id);
  const text = (id, value, fallback = '—') => {
    const node = byId(id);
    if (node) node.textContent = value === null || value === undefined || value === '' ? fallback : String(value);
  };
  const date = (value) => {
    if (!value) return null;
    const parsed = new Date(value);
    return Number.isFinite(parsed.getTime()) ? parsed : null;
  };
  const fmtDate = (value) => {
    const d = date(value);
    return d ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(d) : 'Not observed';
  };
  const age = (value) => {
    const d = date(value);
    if (!d) return 'not observed';
    const seconds = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    return minutes < 60 ? `${minutes}m ago` : `${Math.floor(minutes / 60)}h ${minutes % 60}m ago`;
  };
  const numeric = (value) => typeof value === 'number' && Number.isFinite(value);
  const numberFmt = new Intl.NumberFormat(undefined, { maximumFractionDigits: 4 });
  const percentFmt = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });

  function amount(value, currency, digits = 2) {
    if (!numeric(value)) return '—';
    const code = typeof currency === 'string' && /^[A-Z]{3,6}$/.test(currency) ? currency : '';
    if (code === 'USD') return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
    const formatted = new Intl.NumberFormat(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
    return code ? `${code} ${formatted}` : formatted;
  }
  function groupedMoney(currencies, key) {
    if (!currencies || !Object.keys(currencies).length) return 'Awaiting desk feed';
    const pairs = Object.entries(currencies).filter(([, totals]) => numeric(totals[key]));
    return pairs.length ? pairs.map(([currency, totals]) => amount(totals[key], currency)).join(' · ') : 'Not available';
  }
  function setMoney(id, value, currency) {
    const node = byId(id);
    if (!node) return;
    node.textContent = amount(value, currency);
    node.classList.toggle('number-positive', numeric(value) && value > 0);
    node.classList.toggle('number-negative', numeric(value) && value < 0);
  }
  function createCell(value, className = '') {
    const td = document.createElement('td');
    td.textContent = value === null || value === undefined || value === '' ? '—' : String(value);
    if (className) td.className = className;
    return td;
  }
  function setPill(id, state, label) {
    const node = byId(id);
    if (!node) return;
    node.textContent = label;
    node.className = `system-pill ${state}`;
  }
  function renderClock() {
    text('local-clock', new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date()));
  }

  function renderBooks(books) {
    const body = byId('books-body');
    if (!body) return;
    body.replaceChildren();
    if (!Array.isArray(books) || !books.length) {
      const row = document.createElement('tr');
      row.append(createCell('Ausar account-level performance has not been observed.', 'empty-row'));
      row.firstChild.colSpan = 17;
      body.append(row);
      return;
    }
    for (const book of books) {
      const row = document.createElement('tr');
      row.append(createCell(book.label || 'Paper book', 'public-label'));
      row.append(createCell(book.currency || '—', 'currency-cell'));
      row.append(createCell(amount(book.equity, book.currency)));
      row.append(createCell(amount(book.cash, book.currency)));
      row.append(createCell(amount(book.market_value, book.currency)));
      row.append(createCell(amount(book.gross_exposure, book.currency)));
      const realized = createCell(amount(book.realized_pnl, book.currency), numeric(book.realized_pnl) ? (book.realized_pnl < 0 ? 'number-negative' : book.realized_pnl > 0 ? 'number-positive' : '') : '');
      row.append(realized);
      const unrealized = createCell(amount(book.unrealized_pnl, book.currency), numeric(book.unrealized_pnl) ? (book.unrealized_pnl < 0 ? 'number-negative' : book.unrealized_pnl > 0 ? 'number-positive' : '') : '');
      row.append(unrealized);
      row.append(createCell(amount(book.closed_trade_net_pnl, book.currency)));
      row.append(createCell(numeric(book.return_percent) ? `${percentFmt.format(book.return_percent)}%` : 'Not available'));
      row.append(createCell(numeric(book.closed_roundtrips) ? book.closed_roundtrips : '—'));
      row.append(createCell(numeric(book.win_rate_percent) ? `${percentFmt.format(book.win_rate_percent)}%` : '—'));
      const metrics = book.metrics || {};
      const publishedMetric = (key, digits = 2) => {
        const item = metrics[key];
        return item && item.status === 'available' && numeric(item.value) ? new Intl.NumberFormat(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(item.value) : '—';
      };
      row.append(createCell(publishedMetric('sharpe_ratio')));
      row.append(createCell(publishedMetric('profit_factor')));
      row.append(createCell(publishedMetric('max_drawdown_percent') !== '—' ? `${publishedMetric('max_drawdown_percent')}%` : '—'));
      const excess = (symbol) => {
        const item = Array.isArray(book.benchmarks) ? book.benchmarks.find(entry => entry.symbol === symbol) : null;
        return item && numeric(item.excess_return_percent) ? `${percentFmt.format(item.excess_return_percent)}%` : 'Not available';
      };
      row.append(createCell(excess('QQQ')));
      row.append(createCell(excess('SPY')));
      body.append(row);
    }
  }

  function renderPositions(positions, bookCount) {
    const body = byId('positions-body');
    if (!body) return;
    body.replaceChildren();
    if (!Array.isArray(positions) || !positions.length) {
      const row = document.createElement('tr');
      row.append(createCell(snapshot?.data_status === 'connected' ? 'No open paper positions in this observation.' : 'Ausar positions have not been observed.', 'empty-row'));
      row.firstChild.colSpan = 7;
      body.append(row);
      return;
    }
    for (const position of positions) {
      const row = document.createElement('tr');
      row.append(createCell(position.book_label || 'Paper book', 'public-label'));
      row.append(createCell(position.symbol || 'Unknown'));
      row.append(createCell(numeric(position.quantity) ? numberFmt.format(position.quantity) : '—'));
      row.append(createCell(numeric(position.mark_price) ? numberFmt.format(position.mark_price) : '—'));
      row.append(createCell(amount(position.market_value, position.currency)));
      const pnl = createCell(amount(position.unrealized_pnl, position.currency), numeric(position.unrealized_pnl) ? (position.unrealized_pnl < 0 ? 'number-negative' : position.unrealized_pnl > 0 ? 'number-positive' : '') : '');
      row.append(pnl);
      const quote = document.createElement('td');
      const pill = document.createElement('span');
      const quoteState = position.quote_fresh === true ? 'quote-fresh' : position.quote_fresh === false ? 'quote-stale' : 'quote-unknown';
      pill.className = `quote-pill ${quoteState}`;
      pill.textContent = position.quote_fresh === true ? 'FRESH' : position.quote_fresh === false ? 'STALE' : 'UNKNOWN';
      quote.append(pill);
      row.append(quote);
      body.append(row);
    }
    text('position-detail', `${positions.length} open position${positions.length === 1 ? '' : 's'} across ${bookCount ?? '—'} paper books`);
  }

  function renderSnapshot(data) {
    if (!data || data.schema !== 'AUSAR_PUBLIC_TERMINAL_SNAPSHOT_V1') throw new Error('Unrecognized desk snapshot.');
    snapshot = data;
    const currencies = data.currency_totals || {};
    const books = Array.isArray(data.books) ? data.books : [];
    const positions = Array.isArray(data.positions) ? data.positions : [];
    const connected = data.data_status === 'connected';
    const observedAt = date(data.observed_at_utc);
    const snapshotStale = !observedAt || Date.now() - observedAt.getTime() > STALE_AFTER_MS;
    const staleQuotes = positions.filter(position => position.quote_fresh === false).length;
    const unknownQuotes = positions.filter(position => position.quote_fresh !== true && position.quote_fresh !== false).length;
    const quotesStale = staleQuotes > 0;
    const statusStale = snapshotStale || quotesStale;

    text('snapshot-time', connected ? fmtDate(data.observed_at_utc) + ' · UTC' : 'Ausar feed not observed');
    const quoteSummary = positions.length
      ? `${staleQuotes}/${positions.length} quotes stale${unknownQuotes ? ` · ${unknownQuotes} unknown` : ''}`
      : 'no open positions';
    text('portfolio-observed', connected ? `Observed ${age(data.observed_at_utc)} · ${quoteSummary}` : 'No live desk observation');
    text('positions-updated', connected ? `Snapshot ${age(data.observed_at_utc)}` : 'Not observed');
    text('systems-observed', data.services?.observed_at_utc ? `Checked ${age(data.services.observed_at_utc)}` : 'Status not observed');

    const dot = byId('snapshot-dot');
    if (dot) dot.className = !connected ? 'error' : statusStale ? 'stale' : 'current';
    const snapshotLabel = !connected
      ? 'FEED NOT CONNECTED'
      : snapshotStale
        ? 'DESK SNAPSHOT STALE'
        : quotesStale
          ? 'SNAPSHOT CURRENT · QUOTES STALE'
          : unknownQuotes
            ? 'SNAPSHOT CURRENT · QUOTES UNKNOWN'
            : 'DESK SNAPSHOT CURRENT';
    text('snapshot-label', snapshotLabel);
    text('snapshot-age', connected ? age(data.observed_at_utc) : '—');

    text('total-equity', groupedMoney(currencies, 'equity'));
    text('equity-detail', Object.keys(currencies).length ? `${Object.values(currencies).reduce((n, v) => n + (Number.isFinite(v.book_count) ? v.book_count : 0), 0)} separate paper books` : 'Awaiting Ausar data');
    text('position-count', connected ? positions.length : '—');
    text('realized-pnl', groupedMoney(currencies, 'realized_pnl'));
    text('unrealized-pnl', groupedMoney(currencies, 'unrealized_pnl'));
    text('market-value', groupedMoney(currencies, 'market_value'));
    text('available-cash', groupedMoney(currencies, 'available_cash'));
    text('closed-trades', connected && numeric(data.performance_summary?.closed_roundtrips) ? data.performance_summary.closed_roundtrips : connected ? 0 : '—');
    text('win-loss-detail', connected ? `${data.performance_summary?.wins ?? 0} wins · ${data.performance_summary?.losses ?? 0} losses` : 'Not observed');
    text('fees', groupedMoney(currencies, 'fees'));
    text('book-count', connected ? books.length : '—');
    const strategyCount = data.desk?.strategy_count;
    text('strategy-count-label', connected && numeric(strategyCount) ? `Installed strategies: ${strategyCount}` : 'Installed strategies: not observed');
    text('accounting-note', data.benchmark_note || 'Currency totals remain separate. QQQ and SPY comparisons appear only when the desk has aligned, distribution-aware benchmark evidence.');

    renderBooks(books);
    renderPositions(positions, books.length);
    renderServices(data.services || {});
  }

  function renderServices(services) {
    const main = services.main || {};
    const wave = services.wave || {};
    const isObserved = (service) => service.observed === true;
    setPill('main-state', !isObserved(main) ? 'unknown' : main.healthy ? 'healthy' : 'error', !isObserved(main) ? 'UNOBSERVED' : main.healthy ? 'HEALTHY' : 'CHECK');
    setPill('wave-state', !isObserved(wave) ? 'unknown' : wave.healthy ? 'healthy' : 'error', !isObserved(wave) ? 'UNOBSERVED' : wave.healthy ? 'HEALTHY' : 'CHECK');
    text('main-heartbeat', main.heartbeat_at ? `Heartbeat ${age(main.heartbeat_at)}` : 'No current observation');
    text('wave-heartbeat', wave.heartbeat_at ? `${Number.isFinite(wave.books_evaluated) ? `${wave.books_evaluated} evaluated · ` : ''}heartbeat ${age(wave.heartbeat_at)}` : 'No current observation');
    const schedule = services.scheduled_briefs || {};
    setPill('brief-state', schedule.enabled ? 'healthy' : 'unknown', schedule.enabled ? 'ENABLED' : 'UNOBSERVED');
    text('brief-detail', schedule.enabled ? `Brief cadence · every ${Math.round((schedule.interval_seconds || 3600) / 60)} min` : 'No current observation');
    const marketTime = main.market_data_last_success_at;
    setPill('market-state', marketTime ? 'healthy' : 'unknown', marketTime ? 'OBSERVED' : 'UNOBSERVED');
    text('market-detail', marketTime ? `Last successful pull ${age(marketTime)}` : 'No current observation');
  }

  async function refresh() {
    const button = byId('refresh-button');
    if (button) button.disabled = true;
    try {
      const response = await fetch(`${SNAPSHOT_URL}?check=${Date.now()}`, { cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer' });
      if (!response.ok) throw new Error(`Published snapshot request failed (${response.status}).`);
      renderSnapshot(await response.json());
    } catch (error) {
      text('snapshot-label', 'PUBLISHED DATA UNAVAILABLE');
      text('snapshot-age', 'Check failed');
      const dot = byId('snapshot-dot');
      if (dot) dot.className = 'error';
    } finally {
      if (button) button.disabled = false;
    }
  }

  function installSectionNavigation() {
    const links = [...document.querySelectorAll('.bottom-nav a[href^="#"]')];
    if (!links.length) return;
    const setCurrent = (hash) => {
      for (const link of links) {
        if (link.getAttribute('href') === hash) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
      }
    };
    for (const link of links) link.addEventListener('click', () => setCurrent(link.getAttribute('href')));
    if ('IntersectionObserver' in window) {
      const sections = links.map((link) => document.querySelector(link.getAttribute('href'))).filter(Boolean);
      const observer = new IntersectionObserver((entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]) setCurrent(`#${visible[0].target.id}`);
      }, { rootMargin: '-15% 0px -62% 0px', threshold: [0, .15, .35, .6] });
      for (const section of sections) observer.observe(section);
    }
  }

  byId('refresh-button')?.addEventListener('click', refresh);
  installSectionNavigation();
  renderClock();
  refresh();
  window.setInterval(renderClock, 1000);
  window.setInterval(refresh, POLL_MS);
})();
