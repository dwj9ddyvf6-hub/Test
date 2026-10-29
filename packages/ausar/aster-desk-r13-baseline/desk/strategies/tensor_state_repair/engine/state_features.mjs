import fs from 'node:fs';
import readline from 'node:readline';
import { runTensorInternals } from './engine/run_tensor_internals.mjs';
import { wilderAtr, onBalanceVolume, slope } from './engine/instrumented-v690/lib/anna-internals.mjs';

// State-only transport. No scientific source body or formula is revised.
// Full histories still reach the exact engine once. Only unrelated glyph,
// swing, ribbon, and daily-model exporter work is omitted from this output.
export const STATE_HEADER = [
  'symbol', 'interval', 'bar_index', 'timestamp', 'completed_at', 'usable_at',
  'source_origin_timestamp', 'native_status', 'open', 'high', 'low', 'close', 'volume',
  'vote_stoch', 'vote_aroon', 'vote_di', 'vote_obv', 'vote_squeeze', 'vote_pivot', 'vote_wave',
  'bullish_votes', 'bearish_votes', 'total_votes', 'atr14', 'obv_slope5', 'dollar_volume20',
  'bar_id', 'timestamp_ms', 'completed_at_ms', 'usable_at_ms', 'executable_at_ms',
  'source_origin_timestamp_ms', 'balance',
];
const CHANNELS = ['stoch', 'aroon', 'di', 'obv', 'squeeze', 'pivot', 'wave'];
const finite = Number.isFinite;
const safeNumber = value => typeof value === 'number' && finite(value) ? value : null;

export function extractStateFeatures(request) {
  if (request.schema !== 'aster-tensor-native-request/1') throw new Error('invalid request schema');
  if (!['1h', '1d', '1wk'].includes(request.frame)) throw new Error('invalid frame');
  if (!Array.isArray(request.bars) || request.bars.length === 0) throw new Error('nonempty bars required');
  if (!Number.isSafeInteger(request.as_of_ms) || request.as_of_ms <= 0) throw new Error('invalid as-of');
  let prior = 0, priorCompleted = 0;
  for (const b of request.bars) {
    for (const key of ['timestamp_ms', 'completed_at_ms', 'usable_at_ms']) {
      if (!Number.isSafeInteger(b[key]) || b[key] <= 0) throw new Error('invalid clock');
    }
    if (b.timestamp_ms % 1000 !== 0 || b.timestamp_ms <= prior) throw new Error('invalid bar start');
    prior = b.timestamp_ms;
    if (b.completed_at_ms <= b.timestamp_ms || b.completed_at_ms <= priorCompleted ||
        b.usable_at_ms < b.completed_at_ms || b.usable_at_ms > request.as_of_ms) {
      throw new Error('bar not completed and available as of request');
    }
    priorCompleted = b.completed_at_ms;
    if (b.executable_at_ms !== null && b.executable_at_ms !== undefined &&
        (!Number.isSafeInteger(b.executable_at_ms) || b.executable_at_ms < b.timestamp_ms || b.executable_at_ms >= b.completed_at_ms)) {
      throw new Error('invalid executable period open');
    }
    if (!['open', 'high', 'low', 'close', 'volume'].every(k => typeof b[k] === 'number' && finite(b[k])) ||
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
      completedAt: Math.ceil(b.completed_at_ms / 1000),
      usableAt: Math.ceil(b.usable_at_ms / 1000),
      open: b.open, high: b.high, low: b.low, close: b.close, volume: b.volume,
    })),
  };
  const minimum = request.frame === '1wk' ? 4 : 35;
  let native, atr, obvSlope;
  if (history.bars.length >= minimum) {
    const result = runTensorInternals({ ...history, asOf: Math.max(...history.bars.map(b => b.usableAt)) });
    native = result.bars;
    atr = result.internalArrays.wilderAtr14;
    obvSlope = result.internalArrays.obvSlope5;
  } else {
    // This is the identical exporter fallback for native-short warming data.
    // Only its required helper arrays are calculated; no vote is invented.
    const close = history.bars.map(b => b.close), high = history.bars.map(b => b.high);
    const low = history.bars.map(b => b.low), volume = history.bars.map(b => b.volume);
    const obv = onBalanceVolume(close, volume);
    atr = wilderAtr(high, low, close, 14);
    obvSlope = obv.map((_, i) => slope(obv, i, 5));
    native = history.bars.map(b => ({ ...b, stateVotes: [], bullishVotes: 0, bearishVotes: 0, totalVotes: 0 }));
  }
  if (native.length !== history.bars.length) throw new Error('native/source denominator mismatch');
  const origin = request.bars[0].timestamp_ms;
  const rows = native.map((b, i) => {
    const s = history.bars[i], exact = request.bars[i];
    const votes = Object.fromEntries((b.stateVotes || []).map(v => [v.id, v.direction === 'bullish' ? 1 : v.direction === 'bearish' ? -1 : null]));
    const directions = CHANNELS.map(k => votes[k] ?? null);
    if (directions.filter(v => v === 1).length !== b.bullishVotes ||
        directions.filter(v => v === -1).length !== b.bearishVotes ||
        directions.filter(v => v !== null).length !== b.totalVotes) {
      throw new Error(`native published direction/count reconciliation failed ${i}`);
    }
    // Keep the exact original left-to-right 20-bar summation order. A rolling
    // sum would be faster but can alter floating-point results and is excluded.
    const dv = i >= 19 ? history.bars.slice(i - 19, i + 1).reduce((sum, x) => sum + x.close * x.volume, 0) / 20 : null;
    const row = {
      symbol: request.symbol, interval: request.frame, bar_index: i,
      timestamp: s.timestamp, completed_at: s.completedAt, usable_at: s.usableAt,
      source_origin_timestamp: origin / 1000, native_status: i + 1 >= minimum ? 'ready' : 'warming',
      open: s.open, high: s.high, low: s.low, close: s.close, volume: s.volume,
      bullish_votes: b.bullishVotes, bearish_votes: b.bearishVotes, total_votes: b.totalVotes,
      atr14: safeNumber(atr[i]), obv_slope5: safeNumber(obvSlope[i]), dollar_volume20: dv,
      bar_id: `${request.symbol}:${request.frame}:${exact.timestamp_ms}`,
      timestamp_ms: exact.timestamp_ms, completed_at_ms: exact.completed_at_ms,
      usable_at_ms: exact.usable_at_ms, executable_at_ms: exact.executable_at_ms ?? null,
      source_origin_timestamp_ms: origin, balance: b.bullishVotes - b.bearishVotes,
    };
    for (const channel of CHANNELS) row[`vote_${channel}`] = votes[channel] ?? null;
    return row;
  });
  const features = rows.slice(-4).map(r => ({
    symbol: r.symbol, frame: r.interval, bar_index: r.bar_index, bar_id: r.bar_id,
    timestamp_ms: r.timestamp_ms, completed_at_ms: r.completed_at_ms, usable_at_ms: r.usable_at_ms,
    executable_at_ms: r.executable_at_ms, source_origin_timestamp_ms: r.source_origin_timestamp_ms,
    native_status: r.native_status, open: r.open, high: r.high, low: r.low, close: r.close, volume: r.volume,
    votes: CHANNELS.map(k => r[`vote_${k}`]), bullish_votes: r.bullish_votes,
    bearish_votes: r.bearish_votes, total_votes: r.total_votes, atr14: r.atr14,
    obv_slope5: r.obv_slope5, dollar_volume20: r.dollar_volume20,
  }));
  return { schema: 'aster-tensor-native-result/1', features, full_rows: rows, full_header: STATE_HEADER };
}

// Importing this module for an isolated benchmark does not consume stdin.
if (process.argv[1] && new URL(import.meta.url).pathname === process.argv[1]) {
  if (process.argv[2] === '--worker') {
    const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
    for await (const line of input) {
      // One isolated result per request. A malformed request terminates this
      // worker; Python discards it and never interprets partial output.
      const result = extractStateFeatures(JSON.parse(line));
      const ready = process.stdout.write(JSON.stringify(result) + '\n');
      if (!ready) await new Promise(resolve => process.stdout.once('drain', resolve));
    }
  } else {
    process.stdout.write(JSON.stringify(extractStateFeatures(JSON.parse(fs.readFileSync(0, 'utf8')))) + '\n');
  }
}
