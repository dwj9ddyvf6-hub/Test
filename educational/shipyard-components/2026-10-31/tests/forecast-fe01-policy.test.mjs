import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {buildFE01SourceForecast,computeFE01TrendFeatures,FE01_TREND_POLICY,FE01_TREND_POLICY_SHA256} from '../research/forecast-features/fe01-trend-v1.mjs';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
import {fixture,boundary} from './fixtures/fe01-synthetic.mjs';
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-10*Math.max(Math.abs(b),1e-6),`${a} != ${b}`);
const python=process.env.SHIPYARD_PYTHON||(process.platform==='win32'?'python':'python3');
test('policy and unchanged scorer provenance remain exact',()=>{const r=buildFE01SourceForecast(fixture());assert.equal(r.status,'computed');assert.equal(FE01_TREND_POLICY_SHA256,createHash('sha256').update(JSON.stringify(FE01_TREND_POLICY)).digest('hex'));assert.deepEqual(r.calculator_result,evaluateForecastEngine('FE01',r.features));assert.equal(r.calculator_result.input_provenance,'manual_unverified');assert.equal(r.feature_origin,'provider_capture_new_policy');assert.equal(r.restrictions.decision_eligible,false);assert.equal(r.restrictions.order_submission_enabled,false);assert.equal(r.coverage.used_daily_bars,505);});
test('hand-derived quadratic log price has exact prior-only population z and monotone efficiency',()=>{const r=buildFE01SourceForecast(fixture());assert.equal(r.status,'computed');const z=126.5/Math.sqrt((252**2-1)/12);for(const h of [21,63,252]){close(r.features[`ret_${h}d_z`],z);const s=r.measurements.normalization[`ret_${h}d`];close(s.prior_mean,2e-6*h*377.5+1e-4*h-1e-6*h*h);close(s.prior_population_sd,2e-6*h*Math.sqrt((252**2-1)/12));assert.equal(s.prior_count,252);}close(r.features.trend_efficiency,1);const rv=u=>Math.sqrt((2e-6*u-21e-6+1e-4)**2+(440/3)*1e-12);const prior=Array.from({length:252},(_,i)=>rv(252+i)),m=prior.reduce((a,b)=>a+b)/252,sd=Math.sqrt(prior.reduce((s,x)=>s+(x-m)**2,0)/252);close(r.features.vol_regime,(rv(504)-m)/sd);close(r.calculator_result.model_score,z/(1+.2*Math.abs(r.features.vol_regime)));assert.equal(r.measurements.population_ddof,0);});
test('latest price shock cannot contaminate any prior normalization population',()=>{const f=fixture(),a=buildFE01SourceForecast(f);f.bars.at(-1).c*=2;f.bars.at(-1).h=f.bars.at(-1).c;const b=buildFE01SourceForecast(f);assert.equal(b.status,'computed');for(const key of Object.keys(a.measurements.normalization)){assert.equal(a.measurements.normalization[key].prior_mean,b.measurements.normalization[key].prior_mean);assert.equal(a.measurements.normalization[key].prior_population_sd,b.measurements.normalization[key].prior_population_sd);}assert.notEqual(a.features.ret_252d_z,b.features.ret_252d_z);});
test('scale invariance, reversal and alternating efficiency retain declared log units',()=>{const f=fixture(),a=buildFE01SourceForecast(f);for(const b of f.bars)for(const key of ['o','h','l','c'])b[key]*=100;const b=buildFE01SourceForecast(f);for(const key of Object.keys(a.features))close(a.features[key],b.features[key]);const down=buildFE01SourceForecast(fixture({closeFn:i=>Math.exp(-1e-6*i*i-1e-4*i)}));close(down.features.ret_21d_z,-a.features.ret_21d_z);close(down.features.trend_efficiency,1);const alt=buildFE01SourceForecast(fixture({closeFn:i=>Math.exp(1e-6*i*i+1e-4*i+(i%2?.02:0))}));assert.ok(alt.features.trend_efficiency<.1);});
for(const [name,mutate,code] of [
 ['504 is insufficient',x=>x.calendar.sessions.shift(),'insufficient_completed_sessions'],
 ['missing oldest',x=>x.bars.shift(),'missing_daily_session_bar'],
 ['missing latest',x=>x.bars.pop(),'missing_daily_session_bar'],
 ['missing middle',x=>x.bars.splice(250,1),'missing_daily_session_bar'],
 ['duplicate',x=>x.bars.splice(10,0,x.bars[10]),'unordered_or_duplicate_bar'],
 ['unordered',x=>[x.bars[0],x.bars[1]]=[x.bars[1],x.bars[0]],'unordered_or_duplicate_bar'],
 ['off daily grid',x=>x.bars[3].t=new Date(Date.parse(x.bars[3].t)+60000).toISOString(),'off_daily_grid_bar'],
 ['invalid OHLC',x=>x.bars[1].h=.01,'invalid_bar'],
 ['NaN',x=>x.bars[1].c=NaN,'invalid_bar'],
 ['string price',x=>x.bars[1].c='1','invalid_bar'],
 ['zero volume',x=>x.bars[1].v=0,'invalid_bar'],
 ['zero price',x=>x.bars[1].c=0,'invalid_bar'],
 ['negative volume',x=>x.bars[1].v=-1,'invalid_bar'],
 ['too many rows',x=>x.bars=Array(1001).fill(x.bars[0]),'history_bound_exceeded'],
 ['unfinished pages',x=>x.pagination_complete=false,'incomplete_provider_pagination'],
 ['future receipt',x=>x.captures[0].received_at='2026-10-30T00:00:00Z','invalid_source_receipts'],
 ['out of order receipt',x=>x.captures[0].request_started_at='2026-10-29T19:38:00Z','invalid_source_receipts'],
 ['missing body hash',x=>delete x.captures[0].response_sha256,'invalid_source_receipts'],
 ['unknown calendar',x=>x.calendar.complete_provider_response=false,'invalid_calendar_lineage'],
 ['future calendar',x=>x.calendar.received_at='2026-10-30T00:00:00Z','invalid_calendar_lineage'],
 ['oversized calendar range',x=>x.calendar.requested_range.start_date='2000-01-01','invalid_calendar_lineage'],
 ['different asof',x=>x.symbol_asof='2026-10-28','symbol_mapping_mismatch'],
 ['mixed feed',x=>x.feed='sip','source_identity_mismatch'],
 ['raw not split',x=>x.adjustment='raw','source_identity_mismatch'],
 ['all not split',x=>x.adjustment='all','source_identity_mismatch'],
 ['foreign currency',x=>x.currency='EUR','source_identity_mismatch'],
 ['intraday not daily',x=>x.timeframe='5Min','source_identity_mismatch'],
 ['window no exclusive flag',x=>delete x.requested_window.end_exclusive,'invalid_requested_window'],
 ['window too late',x=>x.requested_window.start=x.bars[1].t,'invalid_requested_window'],
 ['submillisecond hidden precision',x=>x.bars[0].t=x.bars[0].t.replace('.000Z','.000000001Z'),'invalid_bar'],
])test(name,()=>{const f=fixture();mutate(f);const r=buildFE01SourceForecast(f);assert.equal(r.error,code);assert.equal('calculator_result' in r,false);});
test('non-session date cannot fill the official calendar grid',()=>{const f=fixture(),i=f.bars.findIndex(b=>new Date(b.t).getUTCDay()===5);f.bars.splice(i+1,0,{...f.bars[i],t:boundary(new Date(Date.parse(f.bars[i].t)+86400000).toISOString().slice(0,10),'00:00')});assert.equal(buildFE01SourceForecast(f).error,'non_session_bar');});
test('zero, constant geometric and near-degenerate inputs abstain without an epsilon floor',()=>{for(const f of [fixture({zero:true}),fixture({constant:true}),fixture({closeFn:i=>Math.exp(1e-18*i*i)})])assert.equal(buildFE01SourceForecast(f).error,'degenerate_ret_21d_normalizer');const f=fixture();for(let i=483;i<=504;i++)for(const k of ['o','h','l','c'])f.bars[i][k]=f.bars[483].c;assert.equal(buildFE01SourceForecast(f).error,'degenerate_efficiency_path');});
test('past flat volatility is separately rejected even with varying long return normalization',()=>{const f=fixture({closeFn:i=>Math.exp(i<231?1e-6*i*i:(i%2?.01:0))});assert.equal(buildFE01SourceForecast(f).error,'degenerate_vol_regime_normalizer');});
test('official early close and DST midnight stamps are used, never fixed UTC or weekdays',()=>{const f=fixture({early:true}),r=buildFE01SourceForecast(f);assert.equal(r.status,'computed');assert.equal(r.freshness.source_as_of,'2026-10-28T17:00:00.000Z');assert.ok(f.bars.some(b=>b.t.includes('T04:00:00')));assert.ok(f.bars.some(b=>b.t.includes('T05:00:00')));const winter=f.bars.slice(1).find(b=>b.t.includes('T05:00:00'));winter.t=winter.t.replace('T05:00','T06:00');assert.equal(buildFE01SourceForecast(f).error,'off_daily_grid_bar');});
test('latest session switches at exactly official close+15min with no missing-day fallback',()=>{const f=fixture();f.calendar.sessions.push({date:'2026-10-29',open:boundary('2026-10-29','09:30'),close:boundary('2026-10-29','16:00')});f.evaluation_at='2026-10-29T20:14:59Z';assert.equal(buildFE01SourceForecast(f).status,'computed');f.evaluation_at='2026-10-29T20:15:00Z';assert.equal(buildFE01SourceForecast(f).error,'invalid_requested_window');});
test('stale research not refreshed by receipt or computation clock',()=>{const f=fixture();f.evaluation_at='2026-11-01T15:00:00Z';f.symbol_asof='2026-11-01';f.calendar.requested_range.end_date='2026-11-01';f.calendar.requested_range.start_date='2024-08-23';const r=buildFE01SourceForecast(f);assert.equal(r.status,'computed');assert.equal(r.freshness.status,'stale');assert.equal(r.freshness.source_as_of,'2026-10-28T20:00:00.000Z');});
test('ordered selected normalized bars hash is reproducible and changes on price revision',()=>{const f=fixture(),a=buildFE01SourceForecast(f);assert.equal(a.source.selected_bars_sha256,createHash('sha256').update(JSON.stringify(f.bars)).digest('hex'));f.bars[0].c*=1.001;f.bars[0].h=f.bars[0].c;assert.notEqual(a.source.selected_bars_sha256,buildFE01SourceForecast(f).source.selected_bars_sha256);});
test('independent Python reference agrees across quadratic, falling, alternating and deterministic irregular paths',()=>{for(const closeFn of [null,i=>Math.exp(-1e-6*i*i),i=>Math.exp(.01*Math.sin(i)+1e-6*i*i),i=>Math.exp(.02*Math.cos(i/11)+.03*Math.sin(i/31)+.0002*i)]){const closes=fixture({closeFn}).bars.map(b=>b.c),js=computeFE01TrendFeatures(closes).features,py=JSON.parse(execFileSync(python,['research/forecast-features/fe01_trend_v1.py'],{input:JSON.stringify(closes),encoding:'utf8'}));for(const k of Object.keys(js))close(js[k],py.features[k]);}const py=JSON.parse(execFileSync(python,['research/forecast-features/fe01_trend_v1.py'],{input:JSON.stringify(Array(505).fill(1)),encoding:'utf8'}));assert.equal(py.error,'degenerate_ret_21d_normalizer');});
test('reviewed manifest pins builder, producer, reference math and original scorer bytes',()=>{const m=JSON.parse(readFileSync(new URL('../research/forecast-features/fe01-manifest.json',import.meta.url)));assert.equal(m.policy_sha256,FE01_TREND_POLICY_SHA256);for(const [file,sha]of Object.entries(m.source_sha256)){const source=readFileSync(new URL('../'+file,import.meta.url)).toString('utf8').replace(/\r\n/g,'\n');assert.equal(createHash('sha256').update(source).digest('hex'),sha,file);}const r=buildFE01SourceForecast(fixture());assert.deepEqual(r.calculator_result.source,m.unchanged_scorer);assert.equal(r.source.source_policy_fingerprint,m.source_policy_fingerprint);});
