import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {buildFE02SourceForecast,computeFE02PairedFeatures,FE02_PAIRED_POLICY,FE02_PAIRED_POLICY_SHA256} from '../research/forecast-features/fe02-residual-v1.mjs';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
import {fixture,series} from './fixtures/fe02-synthetic.mjs';

const close=(actual,expected,tolerance=2e-10)=>assert.ok(Math.abs(actual-expected)<=tolerance*Math.max(Math.abs(expected),1e-12),`${actual} != ${expected}`);
function manualReference(symbolCloses,benchmarkCloses){
  const symbolReturns=symbolCloses.slice(1).map((price,index)=>Math.log(price/symbolCloses[index]));
  const benchmarkReturns=benchmarkCloses.slice(1).map((price,index)=>Math.log(price/benchmarkCloses[index]));
  const current=symbolReturns.length-1,from=current-252,to=current-1;
  const x=benchmarkReturns.slice(from,to+1),y=symbolReturns.slice(from,to+1);
  const xbar=x.reduce((a,b)=>a+b,0)/252,ybar=y.reduce((a,b)=>a+b,0)/252;
  const beta=x.reduce((s,value,index)=>s+(value-xbar)*(y[index]-ybar),0)/x.reduce((s,value)=>s+(value-xbar)**2,0),alpha=ybar-beta*xbar;
  const residual=symbolReturns.map((value,index)=>value-alpha-beta*benchmarkReturns[index]);
  const prior=residual.slice(from,to+1),priorMean=prior.reduce((a,b)=>a+b,0)/252;
  const sigma=Math.sqrt(prior.reduce((sum,value)=>sum+(value-priorMean)**2,0)/252);
  const roll=(end)=>Math.sqrt(residual.slice(end-20,end+1).reduce((s,value)=>s+value*value,0)/21);
  const baseline=Array.from({length:252},(_,i)=>roll(current-252+i)),baselineMean=baseline.reduce((a,b)=>a+b,0)/252;
  const baselineSd=Math.sqrt(baseline.reduce((s,value)=>s+(value-baselineMean)**2,0)/252);
  const points=[];
  for(const size of [8,16,32,64]){
    let ratioSum=0,count=0;
    for(let start=current-251;start+size<=current+1;start+=size){
      const block=residual.slice(start,start+size),avg=block.reduce((a,b)=>a+b,0)/size;
      let path=0,lo=0,hi=0,squares=0;
      for(const value of block){const d=value-avg;path+=d;lo=Math.min(lo,path);hi=Math.max(hi,path);squares+=d*d;}
      ratioSum+=(hi-lo)/Math.sqrt(squares/(size-1));count++;
    }
    points.push([Math.log(size),Math.log(ratioSum/count)]);
  }
  const mx=points.reduce((s,p)=>s+p[0],0)/4,my=points.reduce((s,p)=>s+p[1],0)/4;
  const hurst=points.reduce((s,p)=>s+(p[0]-mx)*(p[1]-my),0)/points.reduce((s,p)=>s+(p[0]-mx)**2,0);
  const residual5=residual.slice(current-4,current+1).reduce((a,b)=>a+b,0),residual63=residual.slice(current-62,current+1).reduce((a,b)=>a+b,0);
  return {alpha,beta,sigma,residual5,residual63,hurst,volRegime:(roll(current)-baselineMean)/baselineSd};
}
function replaceBars(input,closesBySymbol){
  for(const symbol of [input.symbol,'SPY'])input.bars_by_symbol[symbol]=input.bars_by_symbol[symbol].map((bar,index)=>({...bar,o:closesBySymbol[symbol][index],h:closesBySymbol[symbol][index],l:closesBySymbol[symbol][index],c:closesBySymbol[symbol][index]}));
}
const sha=text=>createHash('sha256').update(text).digest('hex');
test('impossible calendar dates cannot normalize into an accepted source bar',()=>{
 const input=fixture(),bar=input.bars_by_symbol.QQQ.find(row=>row.t.startsWith('2026-03-02'));
 assert.ok(bar);bar.t=bar.t.replace('2026-03-02','2026-02-30');
 const result=buildFE02SourceForecast(input);assert.notEqual(result.status,'computed');assert.equal(result.error,'invalid_bar');
});

test('NEW FE02 policy, provenance gates and unchanged fixed scorer are pinned',()=>{
  const input=fixture(),result=buildFE02SourceForecast(input);
  assert.equal(result.status,'computed');assert.equal(FE02_PAIRED_POLICY_SHA256,sha(JSON.stringify(FE02_PAIRED_POLICY)));
  assert.equal(result.feature_origin,'provider_capture_new_policy');assert.equal(result.feature_policy.origin,'NEW_FEATURE_POLICY');
  assert.deepEqual(result.calculator_result,evaluateForecastEngine('FE02',result.features));
  assert.equal(result.calculator_result.input_provenance,'manual_unverified');
  assert.deepEqual(result.restrictions,{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false});
  assert.equal(result.source.provider,'Alpaca Market Data');assert.equal(result.source.feed,'iex');assert.equal(result.source.adjustment,'split');
  assert.equal(result.coverage.complete_sessions,505);assert.equal(result.coverage.aligned_session_grid,true);
  assert.equal(result.source.historical_availability,'unknown; current captures do not establish availability at historical decisions');
  assert.equal(result.source.calendar.capture.operation,'official_calendar');assert.equal(result.freshness.status,'within_declared_age');
});

test('independent manual paired-return calculation matches exact OLS, residual windows, R/S and RMS normalization',()=>{
  const data=series(),actual=computeFE02PairedFeatures(data.QQQ,data.SPY),expected=manualReference(data.QQQ,data.SPY);
  close(actual.regression.alpha,expected.alpha);close(actual.regression.beta,expected.beta);
  close(actual.measurements.residual_daily_prior_population_sd,expected.sigma);
  close(actual.measurements.residual_5_session_sum,expected.residual5);close(actual.measurements.residual_63_session_sum,expected.residual63);
  close(actual.features.residual_z,expected.residual5/(expected.sigma*Math.sqrt(5)));
  close(actual.features.trend_z,expected.residual63/(expected.sigma*Math.sqrt(63)));
  close(actual.features.hurst,expected.hurst);close(actual.features.vol_regime,expected.volRegime);
  assert.equal(actual.regression.observations,252);assert.equal(actual.regression.prior_window_excludes_current,true);
  assert.equal(actual.measurements.population_ddof,0);assert.equal(actual.measurements.hurst_estimator.estimator,'nonoverlapping_demeaned_R_over_sample_S_OLS_loglog');
});

test('current residual is excluded from beta and normalizers; positive and negative shocks reverse residual sign',()=>{
  const original=fixture(),base=buildFE02SourceForecast(original),series0=series();
  for(const [symbol,shock] of [['QQQ',.05],['QQQ',-.05]]){
    const input=fixture(),bar=input.bars_by_symbol[symbol].at(-1);bar.c*=Math.exp(shock);bar.h=Math.max(bar.o,bar.c);bar.l=Math.min(bar.o,bar.c);
    const after=buildFE02SourceForecast(input);assert.equal(after.status,'computed');
    assert.equal(after.source.regression.beta,base.source.regression.beta);assert.equal(after.source.regression.alpha,base.source.regression.alpha);
    assert.equal(after.measurements.residual_daily_prior_population_sd,base.measurements.residual_daily_prior_population_sd);
    assert.equal(after.measurements.volatility_baseline_mean,base.measurements.volatility_baseline_mean);
    if(shock>0)assert.ok(after.features.residual_z>base.features.residual_z);else assert.ok(after.features.residual_z<base.features.residual_z);
  }
  const flatBeta=computeFE02PairedFeatures(series0.QQQ,series0.SPY);assert.equal(flatBeta.regression.prior_window_excludes_current,true);
});

test('split-adjusted price scaling leaves the paired feature vector invariant',()=>{
  const input=fixture(),baseline=buildFE02SourceForecast(input),closes=series();
  for(const symbol of [input.symbol,'SPY'])closes[symbol]=closes[symbol].map(value=>value*100);
  replaceBars(input,closes);const scaled=buildFE02SourceForecast(input);assert.equal(scaled.status,'computed');
  for(const key of Object.keys(baseline.features))close(scaled.features[key],baseline.features[key]);
});

for(const [name,mutate,error] of [
  ['wrong benchmark',x=>x.benchmark_symbol='QQQ','source_identity_mismatch'],['wrong feed',x=>x.feed='sip','source_identity_mismatch'],
  ['wrong adjustment',x=>x.adjustment='all','source_identity_mismatch'],['wrong currency',x=>x.currency='EUR','source_identity_mismatch'],
  ['SPY cannot be target',x=>x.symbol='SPY','source_identity_mismatch'],['unmatched dates',x=>x.bars_by_symbol.SPY[10].t=x.bars_by_symbol.SPY[11].t,'unordered_or_duplicate_bar'],
  ['missing symbol session',x=>x.bars_by_symbol.QQQ.splice(10,1),'missing_symbol_session_bar'],
  ['missing benchmark session',x=>x.bars_by_symbol.SPY.splice(10,1),'missing_benchmark_session_bar'],
  ['invalid units',x=>x.bars_by_symbol.QQQ[0].c='20','invalid_bar'],['invalid OHLC',x=>x.bars_by_symbol.SPY[0].h=.5,'invalid_bar'],
  ['incomplete pagination',x=>x.pagination_complete=false,'incomplete_provider_pagination'],
  ['calendar receipt hash absent',x=>delete x.calendar_capture.response_sha256,'invalid_calendar_receipt'],
  ['calendar request identity drift',x=>x.calendar_capture.request_url='https://other.invalid/calendar','invalid_calendar_receipt'],
  ['duplicate page receipt',x=>x.captures.push({...x.captures[0]}),'invalid_source_receipts'],
  ['wrong page request window',x=>x.captures[0].request_url=x.captures[0].request_url.replace('timeframe=1Day','timeframe=5Min'),'invalid_source_receipts'],
  ['partial page',x=>x.captures[0].provider_rows=504,'invalid_source_receipts'],
  ['unentitled feed provenance',x=>x.captures[0].http_status=403,'invalid_source_receipts'],
  ['source time is stale',x=>{
    x.evaluation_at='2026-10-31T19:40:00.000Z';x.symbol_asof='2026-10-31';x.calendar.requested_range.end_date='2026-10-31';x.calendar.requested_range.start_date='2024-08-22';
    x.calendar.received_at='2026-10-31T19:39:45.000Z';x.calendar_capture.request_started_at='2026-10-31T19:39:40.000Z';
    x.calendar_capture.http_response_received_at=x.calendar.received_at;x.calendar_capture.received_at=x.calendar.received_at;
    const calendarUrl=new URL(x.calendar_capture.request_url);calendarUrl.searchParams.set('start','2024-08-22');calendarUrl.searchParams.set('end','2026-10-31');x.calendar_capture.request_url=calendarUrl.toString();
    for(const receipt of x.captures){receipt.request_started_at='2026-10-31T19:39:50.000Z';receipt.http_response_received_at='2026-10-31T19:39:55.000Z';receipt.received_at=receipt.http_response_received_at;const url=new URL(receipt.request_url);url.searchParams.set('asof','2026-10-31');receipt.request_url=url.toString();}
  },'stale_source'],
  ['sub-505 warmup',x=>x.calendar.sessions=x.calendar.sessions.slice(1),'insufficient_completed_sessions'],
])test(`${name} fails closed without numeric score`,()=>{
  const input=fixture();mutate(input);const result=buildFE02SourceForecast(input);assert.equal(result.status,'unavailable');assert.equal(result.error,error);assert.equal('calculator_result' in result,false);
});

test('degenerate benchmark regression and degenerate residual normalizer abstain without a floor',()=>{
  const input=fixture();for(const name of ['QQQ','SPY'])for(const bar of input.bars_by_symbol[name]){bar.o=bar.h=bar.l=bar.c=1;}
  assert.equal(buildFE02SourceForecast(input).error,'degenerate_benchmark_regression');
  const data=series(),same=data.SPY.map((value,index)=>value*Math.exp(.0001*index)),features=computeFE02PairedFeatures;
  assert.throws(()=>features(same,data.SPY),/degenerate_residual_volatility/);
});

test('reviewed FE02 manifest pins policy, builder, producer and unchanged scorer bytes',()=>{
  const manifest=JSON.parse(readFileSync(new URL('../research/forecast-features/fe02-manifest.json',import.meta.url)));
  assert.equal(manifest.policy_id,FE02_PAIRED_POLICY.id);assert.equal(manifest.policy_sha256,FE02_PAIRED_POLICY_SHA256);
  for(const [file,expected] of Object.entries(manifest.source_sha256)){
    const source=readFileSync(new URL('../'+file,import.meta.url)).toString('utf8').replace(/\r\n/g,'\n');assert.equal(sha(source),expected,file);
  }
  const result=buildFE02SourceForecast(fixture());assert.deepEqual(result.calculator_result.source,manifest.unchanged_scorer);
  assert.equal(result.source.source_policy_fingerprint,manifest.source_policy_fingerprint);
});
