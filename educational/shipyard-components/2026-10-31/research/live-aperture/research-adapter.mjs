// Offline adapter. No network, credentials, accounts, order routes, or timers.
import { buildLiveDiscoveryView } from './lib/live-scan-engine.ts';
import { isScannerEligible } from './services/aperture-runner/src/coverage.ts';
import { APERTURE_EQUITY_SYMBOLS } from './lib/aperture-universe.ts';
export const SOURCE_COMMIT = '6c11b27c11ffedee314fd608fc83853ccf2cb23a';
const fail = (message) => { throw new Error(message); };
const time = (s) => typeof s === 'string' && Number.isFinite(Date.parse(s)) ? Date.parse(s) : fail('Invalid timestamp');
function bars(series, frame, cutoff) {
  if (!Array.isArray(series) || series.length > (frame === 'daily' ? 500 : 3000)) fail('Invalid or oversized bar series');
  let previous = -Infinity;
  for (const b of series) {
    const t = time(b.t);
    if (t <= previous || t > cutoff) fail('Duplicate, unsorted, or future bar');
    if (![b.o,b.h,b.l,b.c].every(x=>Number.isFinite(x)&&x>0) || !Number.isFinite(b.v) || b.v<0 || b.h<Math.max(b.o,b.c) || b.l>Math.min(b.o,b.c) || b.h<b.l) fail('Malformed OHLCV');
    if (frame === 'intraday' && t % 300000 !== 0) fail('Intraday input must be five-minute bar-start timestamps');
    previous=t;
  }
}
/** Capture is source evidence, not authenticated by this offline adapter. */
export function prepareInput(capture) {
  const { requested_symbol: requested, benchmark_symbol: benchmark, provenance, scan } = capture;
  if (!APERTURE_EQUITY_SYMBOLS.includes(requested) || !['SPY','QQQ'].includes(benchmark)) fail('Unsupported requested symbol or benchmark');
  if (!provenance || provenance.provider !== 'alpaca' || !['iex','sip'].includes(provenance.feed) || provenance.adjustment !== 'all') fail('Original source basis requires Alpaca IEX/SIP and explicit adjustment=all');
  const received = time(provenance.received_at), generated=time(scan.generatedAt), end=time(scan.barEndAt);
  if (received>generated || end>received || end%300000!==0) fail('Invalid capture clock order or unsealed five-minute boundary');
  if (!['PREMARKET','REGULAR','AFTERHOURS','CLOSED'].includes(scan.session)) fail('Invalid session');
  if (!provenance.calendar_source || !provenance.calendar_received_at || time(provenance.calendar_received_at)>generated) fail('Explicit official calendar provenance required; offline adapter does not infer session');
  if (!['LIVE','BASELINE','LAGGING','STALE','CLOSED','WARMING','OFFLINE'].includes(scan.freshness)) fail('Invalid freshness');
  if (scan.freshness==='LIVE' && generated-end>390000) fail('LIVE capture has stale sealed-bar clock');
  const expected = [...new Set([requested, benchmark])];
  if (!Array.isArray(scan.symbols) || scan.symbols.length !== expected.length || new Set(scan.symbols.map(x=>x.symbol)).size !== expected.length || scan.symbols.some(x=>!expected.includes(x.symbol))) fail('Exactly requested symbol and selected benchmark required');
  let eligible=0, covered=0;
  const symbols = scan.symbols.map(s=>{
    bars(s.daily,'daily',received); bars(s.intraday,'intraday',end-300000);
    const providerEligible = isScannerEligible(s.daily) && s.providerEligible!==false;
    if (providerEligible) eligible++;
    const sealed = s.intraday.length>=3 && time(s.intraday.at(-1).t)===end-300000;
    const qualityFlags=[...(s.qualityFlags??[]),...(!sealed?['CURRENT_COMPLETED_5M_BAR_MISSING']:[])];
    if (providerEligible && sealed && !qualityFlags.length) covered++;
    return {...s,providerEligible,qualityFlags};
  });
  return {...scan,provider:provenance.provider,feed:provenance.feed,symbols,eligibleCount:eligible,coveredCount:covered,unsupportedCount:expected.length-eligible};
}
export function runResearch(capture) {
  const input=prepareInput(capture);
  const result=buildLiveDiscoveryView(input);
  const decisions=result.decisions.filter(d=>d.symbol===capture.requested_symbol).map(({ownerAction,...d})=>d);
  return {
    schema:'aperture-subset-research.v1', engine_source_commit:SOURCE_COMMIT,
    source_identity:'Recovered October pre-retirement implementation; NOT verified as September stored 383-symbol scan',
    scope:{kind:'requested_symbol_and_benchmark',requested_symbol:capture.requested_symbol,benchmark_symbol:capture.benchmark_symbol,full_universe_scanned:false,provided_symbols:input.symbols.map(s=>s.symbol)},
    provenance:capture.provenance, provenance_verified:false,
    research_only:true, decision_eligible:false, order_submission_enabled:false,
    generated_at:input.generatedAt, bar_end_at:input.barEndAt,
    source_reported_freshness:input.freshness,
    warnings:['OFFLINE_CAPTURE_NOT_AUTHENTICATED','PARTIAL_UNIVERSE','NOT_A_PERSISTENT_PRODUCER','ORIGINAL_HEURISTICS_NOT_INDEPENDENTLY_VALIDATED'],
    scope_coverage:{eligible:input.eligibleCount,covered:input.coveredCount,unsupported:input.unsupportedCount},
    decisions,
  };
}
