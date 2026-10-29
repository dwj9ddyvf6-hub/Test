import fs from 'node:fs';
import { extractNativeFeatures, HEADER } from './scripts/replay_native_features.mjs';

// Transport only. All 93 mathematical features are produced by the exact R11
// exporter and its exact engine/helper closure, without revised formulas.
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
if (request.schema !== 'aster-tensor-native-request/1') throw new Error('invalid request schema');
if (!['1h', '1d', '1wk'].includes(request.frame)) throw new Error('invalid frame');
if (!Array.isArray(request.bars) || request.bars.length === 0) throw new Error('nonempty bars required');
if (!Number.isSafeInteger(request.as_of_ms) || request.as_of_ms <= 0) throw new Error('invalid as-of');
let prior = 0;
for (const b of request.bars) {
  for (const key of ['timestamp_ms', 'completed_at_ms', 'usable_at_ms']) {
    if (!Number.isSafeInteger(b[key]) || b[key] <= 0) throw new Error('invalid clock');
  }
  if (b.timestamp_ms % 1000 !== 0 || b.timestamp_ms <= prior) throw new Error('invalid bar start');
  prior = b.timestamp_ms;
  if (b.completed_at_ms <= b.timestamp_ms || b.usable_at_ms < b.completed_at_ms || b.usable_at_ms > request.as_of_ms) {
    throw new Error('bar not completed and available as of request');
  }
  if (b.executable_at_ms !== null && b.executable_at_ms !== undefined &&
      (!Number.isSafeInteger(b.executable_at_ms) || b.executable_at_ms < b.timestamp_ms || b.executable_at_ms >= b.completed_at_ms)) {
    throw new Error('invalid executable period open');
  }
  if (!['open', 'high', 'low', 'close', 'volume'].every(k => typeof b[k] === 'number' && Number.isFinite(b[k])) ||
      Math.min(b.open, b.high, b.low, b.close) <= 0 || b.volume < 0 ||
      b.high < Math.max(b.open, b.close) || b.low > Math.min(b.open, b.close) || b.high < b.low) {
    throw new Error('invalid OHLCV');
  }
}
const history = {
  symbol: request.symbol, interval: request.frame, latestBarOpen: false,
  timezone: 'America/New_York', currency: 'USD',
  bars: request.bars.map(b => ({
    timestamp: b.timestamp_ms / 1000,
    // The sealed exporter accepts integer seconds. Round availability clocks
    // upwards only for that transport; exact original milliseconds are kept in
    // the feature snapshot below and govern the Python as-of validation.
    completedAt: Math.ceil(b.completed_at_ms / 1000),
    usableAt: Math.ceil(b.usable_at_ms / 1000),
    open: b.open, high: b.high, low: b.low, close: b.close, volume: b.volume,
  })),
};
const rows = extractNativeFeatures(history);
const start = Math.max(0, rows.length - 4);
const features = rows.slice(start).map((r, n) => {
  const source = request.bars[start + n];
  return {
    symbol: request.symbol, frame: request.frame, bar_index: r.bar_index,
    bar_id: `${request.symbol}:${request.frame}:${source.timestamp_ms}`,
    timestamp_ms: source.timestamp_ms, completed_at_ms: source.completed_at_ms,
    usable_at_ms: source.usable_at_ms, executable_at_ms: source.executable_at_ms ?? null,
    source_origin_timestamp_ms: request.bars[0].timestamp_ms,
    native_status: r.native_status,
    open: r.open, high: r.high, low: r.low, close: r.close, volume: r.volume,
    votes: ['stoch','aroon','di','obv','squeeze','pivot','wave'].map(k => r[`vote_${k}`]),
    bullish_votes: r.bullish_votes, bearish_votes: r.bearish_votes, total_votes: r.total_votes,
    atr14: r.atr14, obv_slope5: r.obv_slope5, dollar_volume20: r.dollar_volume20,
  };
});
process.stdout.write(JSON.stringify({
  schema: 'aster-tensor-native-result/1', features,
  full_rows: request.include_full_rows ? rows : null,
  full_header: request.include_full_rows ? HEADER : null,
}) + '\n');
