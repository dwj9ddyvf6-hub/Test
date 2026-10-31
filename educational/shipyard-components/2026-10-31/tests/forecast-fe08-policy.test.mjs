import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {buildFE08SourceForecast,FE08_RV_POLICY,FE08_RV_POLICY_SHA256} from '../research/forecast-features/fe08-rv-v1.mjs';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
import {fixture} from './fixtures/fe08-synthetic.mjs';

const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-10*Math.max(Math.abs(b),1e-8),`${a} != ${b}`);
test('policy fingerprint is exact and original evaluator is unchanged',()=>{assert.equal(FE08_RV_POLICY_SHA256,createHash('sha256').update(JSON.stringify(FE08_RV_POLICY)).digest('hex'));const r=buildFE08SourceForecast(fixture());assert.equal(r.status,'computed');assert.deepEqual(r.calculator_result,evaluateForecastEngine('FE08',r.features));assert.equal(r.calculator_result.input_provenance,'manual_unverified');assert.equal(r.feature_origin,'provider_capture_new_policy');assert.equal(r.restrictions.decision_eligible,false);});
test('hand-computable log returns, sum squares, arithmetic aggregation and same22 reference',()=>{const r=buildFE08SourceForecast(fixture());for(let i=0;i<22;i++)close(r.measurements[i].variance,78*((i+1)/10000)**2);const rv=Array.from({length:22},(_,i)=>78*((i+1)/10000)**2);close(r.features.log_rv_1,Math.log(rv.at(-1)));close(r.features.log_rv_5,Math.log(rv.slice(-5).reduce((a,b)=>a+b)/5));close(r.features.log_rv_22,Math.log(rv.reduce((a,b)=>a+b)/22));assert.equal(r.features.log_rv_baseline,r.features.log_rv_22);assert.notEqual(r.features.log_rv_22,rv.reduce((s,v)=>s+Math.log(v),0)/22);close(r.calculator_result.forecast_value,Math.exp(.5*r.features.log_rv_1+.3*r.features.log_rv_5+.2*r.features.log_rv_22));assert.equal(r.coverage.used_regular_bars,1716);});
test('early close counts actual slots without normalizing to390 minutes',()=>{const r=buildFE08SourceForecast(fixture({early:true}));assert.equal(r.status,'computed');assert.equal(r.measurements.at(-1).expected_bars,42);close(r.measurements.at(-1).variance,42*.0022**2);});
test('overnight jumps never enter returns',()=>{const f=fixture(),original=buildFE08SourceForecast(f);for(const b of f.bars){const k=Date.parse(b.t)<Date.parse(f.calendar.sessions[1].open)?1000:1;for(const n of ['o','h','l','c'])b[n]*=k;}const r=buildFE08SourceForecast(f);close(r.features.log_rv_22,original.features.log_rv_22);});
test('zero variance has no silent floor',()=>assert.equal(buildFE08SourceForecast(fixture({zero:true})).error,'nonpositive_or_nonfinite_session_variance'));
for(const [name,mutate,code] of [
 ['missing slot',x=>x.bars.splice(10,1),'missing_regular_session_slot'],
 ['missing latest session',x=>x.bars=x.bars.filter(b=>b.t.slice(0,10)!==x.calendar.sessions.at(-1).date),'missing_regular_session_slot'],
 ['duplicate',x=>x.bars.splice(10,0,x.bars[10]),'unordered_or_duplicate_bar'],
 ['unordered',x=>[x.bars[0],x.bars[1]]=[x.bars[1],x.bars[0]],'unordered_or_duplicate_bar'],
 ['off grid',x=>x.bars[1].t=new Date(Date.parse(x.bars[1].t)+1000).toISOString(),'off_grid_bar'],
 ['invalid OHLC',x=>x.bars[1].h=1,'invalid_bar'],
 ['non-numeric',x=>x.bars[1].c='100','invalid_bar'],
 ['outside window',x=>x.requested_window.start=new Date(Date.parse(x.requested_window.start)+300000).toISOString(),'invalid_requested_window'],
 ['incomplete pagination',x=>x.pagination_complete=false,'incomplete_provider_pagination'],
 ['future receipt',x=>x.captures[0].received_at='2026-10-30T00:00:00Z','invalid_source_receipts'],
 ['unknown calendar response',x=>x.calendar.complete_provider_response=false,'invalid_calendar_lineage'],
 ['future calendar receipt',x=>x.calendar.received_at='2026-10-30T00:00:00Z','invalid_calendar_lineage'],
 ['calendar not current date',x=>x.calendar.requested_range.end_date='2026-10-28','invalid_calendar_lineage'],
 ['mixed feed',x=>x.feed='sip','source_identity_mismatch'],
 ['10m is not silently 5m',x=>x.timeframe='10Min','source_identity_mismatch'],
 ['adjustment identity',x=>x.adjustment='all','source_identity_mismatch'],
 ['zero first open',x=>x.bars[0].o=0,'invalid_bar'],
 ['window future',x=>x.requested_window.end='2026-10-30T00:00:00Z','invalid_requested_window'],
])test(name,()=>{const f=fixture();mutate(f);assert.equal(buildFE08SourceForecast(f).error,code);});
test('15min conservative delay excludes newly closed session; no fallback after eligible boundary',()=>{const f=fixture();f.calendar.sessions.push({date:'2026-10-29',open:'2026-10-29T13:30:00Z',close:'2026-10-29T20:00:00Z'});f.evaluation_at='2026-10-29T20:14:59Z';assert.equal(buildFE08SourceForecast(f).status,'computed');f.evaluation_at='2026-10-29T20:15:00Z';assert.equal(buildFE08SourceForecast(f).error,'invalid_requested_window');});
test('current partial session is excluded, not leaked into selected windows',()=>{const f=fixture();f.calendar.sessions.push({date:'2026-10-29',open:'2026-10-29T13:30:00Z',close:'2026-10-29T20:00:00Z'});f.requested_window.end='2026-10-29T14:00:00Z';f.bars.push({t:'2026-10-29T13:30:00Z',o:1,h:100000,l:1,c:100000,v:1});const r=buildFE08SourceForecast(f);assert.equal(r.status,'computed');assert.equal(r.coverage.outside_selected_regular_sessions_excluded,1);assert.equal(r.freshness.source_as_of,'2026-10-28T20:00:00.000Z');});
test('stale data remains explicitly labeled research, not hidden by current receipt',()=>{const f=fixture();f.evaluation_at='2026-11-01T15:00:00Z';f.calendar.requested_range.end_date='2026-11-01';const r=buildFE08SourceForecast(f);assert.equal(r.status,'computed');assert.equal(r.freshness.status,'stale');assert.equal(r.freshness.current_source_age_acceptable,false);assert.equal(r.source.quality_score,null);assert.equal(r.source.rights_attestation,null);});
test('nonzero hidden sub-millisecond bar timestamp precision is rejected, not rounded onto grid',()=>{
 const f=fixture();f.bars[0].t=f.bars[0].t.replace('.000Z','.000000001Z');assert.equal(buildFE08SourceForecast(f).error,'invalid_bar');
 f.bars[0].t=f.bars[0].t.replace('.000000001Z','.000000000Z');assert.equal(buildFE08SourceForecast(f).status,'computed');
});
test('regular-session RV is never normalized or annually scaled by wrapper',()=>{
 const a=buildFE08SourceForecast(fixture()),b=buildFE08SourceForecast(fixture({early:true}));
 assert.ok(b.calculator_result.forecast_value<a.calculator_result.forecast_value);
 close(a.calculator_result.drivers.baseline_variance,Math.exp(a.features.log_rv_22));
 assert.match(a.feature_policy.units,/no square root, percent conversion, annualization/);
});

test('reviewed source-policy manifest hashes match checked-in implementation and original scorer identity',()=>{
 const manifest=JSON.parse(readFileSync(new URL('../research/forecast-features/manifest.json',import.meta.url)));
 assert.equal(manifest.policy_id,FE08_RV_POLICY.id);assert.equal(manifest.policy_sha256,FE08_RV_POLICY_SHA256);
 for(const [file,sha] of Object.entries(manifest.source_sha256)){const source=readFileSync(new URL('../'+file,import.meta.url)).toString('utf8').replace(/\r\n/g,'\n');assert.equal(createHash('sha256').update(source).digest('hex'),sha,file);}
 const r=buildFE08SourceForecast(fixture());assert.deepEqual(r.calculator_result.source,manifest.unchanged_scorer);
 assert.equal(r.source.source_policy_fingerprint,manifest.source_policy_fingerprint);
});
