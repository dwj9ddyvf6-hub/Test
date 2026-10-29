function validNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

export function formatSessionDate(value, options = {}) {
  const timestamp = typeof value === 'string' || value instanceof Date ? new Date(value).getTime() : NaN;
  if (!Number.isFinite(timestamp)) return '—';
  return new Date(timestamp).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', ...options, timeZone: 'America/New_York',
  });
}

export function formatSessionTimestamp(value) {
  const timestamp = typeof value === 'string' || value instanceof Date ? new Date(value).getTime() : NaN;
  if (!Number.isFinite(timestamp)) return '—';
  return new Date(timestamp).toLocaleString('en-US', {
    timeZone: 'America/New_York', month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit', timeZoneName: 'short',
  });
}

export function formatUtcTimestamp(value) {
  const timestamp = typeof value === 'string' || value instanceof Date ? new Date(value).getTime() : NaN;
  if (!Number.isFinite(timestamp)) return '—';
  return new Date(timestamp).toLocaleString('en-US', {
    timeZone: 'UTC', month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit', timeZoneName: 'short',
  });
}

export function lineChartAxisLayout(viewportWidth) {
  const compact = Number.isFinite(viewportWidth) && viewportWidth <= 560;
  return compact
    ? { compact: true, leftPadding: 108, labelX: 100, labelAnchor: 'end' }
    : { compact: false, leftPadding: 48, labelX: 4, labelAnchor: 'start' };
}

export function summarizeDailyBars(input) {
  const byTime = new Map();
  if (!Array.isArray(input)) return { bars: [], latest: null, previous: null, changePct: null, range: null };

  for (const raw of input) {
    const milliseconds = typeof raw?.at === 'string' ? Date.parse(raw.at) : NaN;
    const { open, high, low, close, volume } = raw || {};
    if (!Number.isFinite(milliseconds)
      || ![open, high, low, close, volume].every(validNumber) || !Number.isSafeInteger(volume)
      || open <= 0 || high <= 0 || low <= 0 || close <= 0 || volume < 0
      || high < Math.max(open, low, close) || low > Math.min(open, high, close)) continue;
    byTime.set(milliseconds, { ...raw, at: new Date(milliseconds).toISOString() });
  }

  const bars = [...byTime.entries()].sort(([left], [right]) => left - right).map(([, bar]) => bar);
  const latest = bars.at(-1) || null;
  const previous = bars.at(-2) || null;
  return {
    bars,
    latest,
    previous,
    changePct: latest && previous ? (latest.close / previous.close - 1) * 100 : null,
    range: latest ? latest.high - latest.low : null,
  };
}

export function shouldRefreshAt(receivedAt, now, intervalMs) {
  const receivedMs = typeof receivedAt === 'string' ? Date.parse(receivedAt) : NaN;
  return !Number.isFinite(receivedMs) || !Number.isFinite(now) || !Number.isFinite(intervalMs)
    || intervalMs <= 0 || now - receivedMs >= intervalMs;
}
