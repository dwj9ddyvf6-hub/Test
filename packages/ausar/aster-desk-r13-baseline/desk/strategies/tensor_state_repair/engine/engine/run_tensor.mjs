import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { buildAnnaReplica } from './frozen-v690/lib/anna-replica.mjs';

// Research-only transport wrapper. The five frozen native modules are exact
// release bytes. This wrapper validates externally supplied completed bars,
// retains the native full enriched arrays, and never requests market data.
export function runTensorResearch(request) {
  if (!request || typeof request !== 'object' || Array.isArray(request)) throw new Error('request object required');
  const bars = request.bars;
  if (!Array.isArray(bars) || bars.length === 0) throw new Error('nonempty bars required');
  const intervals = new Set(['2m','5m','10m','1h','2h','4h','1d','1wk']);
  if (!intervals.has(request.interval)) throw new Error('explicit supported interval required');
  if (request.latestBarOpen !== undefined && typeof request.latestBarOpen !== 'boolean') throw new Error('latestBarOpen must be Boolean');
  const asOf = request.asOf;
  if (asOf !== undefined && (!Number.isSafeInteger(asOf) || asOf <= 0)) throw new Error('asOf must be positive integer epoch seconds');
  let prior = 0;
  for (const bar of bars) {
    if (!bar || typeof bar !== 'object' || Array.isArray(bar)) throw new Error('bar object required');
    if (!Number.isSafeInteger(bar.timestamp) || bar.timestamp <= prior) throw new Error('timestamps must be strictly increasing positive integer seconds');
    prior = bar.timestamp;
    if (asOf !== undefined) {
      if (bar.timestamp > asOf) throw new Error('future bar supplied after asOf');
      // Bar start is never bar availability. Daily/weekly finality requires
      // actual calendar close plus data receipt, supplied by the data owner.
      // This wrapper does not infer a holiday calendar or vendor latency.
      if (!Number.isSafeInteger(bar.completedAt) || bar.completedAt <= bar.timestamp) throw new Error('asOf requires per-bar completedAt strictly after bar start');
      if (!Number.isSafeInteger(bar.usableAt) || bar.usableAt < bar.completedAt) throw new Error('asOf requires usableAt at or after actual completion and receipt');
      if (bar.usableAt > asOf) throw new Error('bar not usable at asOf');
    }
    for (const field of ['open','high','low','close','volume']) {
      if (typeof bar[field] !== 'number' || !Number.isFinite(bar[field])) throw new Error('numeric finite OHLCV required');
    }
    if (Math.min(bar.open,bar.high,bar.low,bar.close) <= 0 || bar.volume < 0) throw new Error('positive OHLC and nonnegative volume required');
    if (bar.high < Math.max(bar.open,bar.close) || bar.low > Math.min(bar.open,bar.close)) throw new Error('invalid OHLC envelope');
  }
  const native = buildAnnaReplica({
    symbol: request.symbol ?? 'RESEARCH', interval: request.interval,
    intervalLabel: request.intervalLabel ?? request.interval,
    timezone: request.timezone ?? 'America/New_York', currency: request.currency ?? 'USD',
    exchange: request.exchange ?? null,
    latestBarOpen: request.latestBarOpen ?? false,
    displayBars: bars.length,
    bars,
  },{latestOnly:false});
  if (!native) throw new Error('native minimum bars not met');
  // generatedAt is runtime metadata rather than a mathematical feature.
  const {generatedAt, ...deterministic} = native;
  return {
    schema: 'tensor-r11-research-wrapper/2',
    engineSha256: createHash('sha256').update(fs.readFileSync(new URL('./frozen-v690/lib/anna-replica.mjs',import.meta.url))).digest('hex'),
    sourceInputSha256: createHash('sha256').update(JSON.stringify(request)).digest('hex'),
    originalAnnaFormulaParity: 'NOT_ESTABLISHED',
    inputClock: {
      asOf: asOf ?? null,
      completionContract: asOf === undefined ? 'completed prefix asserted by caller; not authenticated' : 'explicit completedAt > timestamp; usableAt >= completedAt; usableAt <= asOf',
      completenessAssertion: 'caller supplied; source timestamps alone do not prove historical availability or session completeness',
    },
    ...deterministic,
  };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const input = process.argv[2] ? fs.readFileSync(process.argv[2],'utf8') : fs.readFileSync(0,'utf8');
  const output = runTensorResearch(JSON.parse(input));
  const serialized = JSON.stringify(output);
  if (process.argv[3]) fs.writeFileSync(process.argv[3],serialized+'\n');
  else process.stdout.write(serialized+'\n');
}
