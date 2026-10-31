import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {buildFE02SourceForecast,computeFE02PairedFeatures,FE02_PAIRED_POLICY,FE02_PAIRED_POLICY_SHA256} from '../research/forecast-features/fe02-residual-session-v2.mjs';
import * as v1 from '../research/forecast-features/fe02-residual-v1.mjs';
import {fixture as original} from './fixtures/fe02-synthetic.mjs';
import {fixture} from './fixtures/fe02-session-v2-synthetic.mjs';
const sha=value=>createHash('sha256').update(value).digest('hex');
test('V2 declares different availability policy while importing exact frozen V1 math',()=>{
 const f=original(),a=v1.buildFE02SourceForecast(f),b=buildFE02SourceForecast(f);
 assert.equal(b.status,'computed');assert.equal(b.schema,'SHIPYARD_FE02_SOURCE_FORECAST_V2');assert.equal(b.feature_policy.version,2);
 assert.equal(computeFE02PairedFeatures,v1.computeFE02PairedFeatures);assert.deepEqual(a.features,b.features);assert.deepEqual(a.calculator_result,b.calculator_result);
 assert.equal(b.source.math_policy.sha256,v1.FE02_PAIRED_POLICY_SHA256);assert.equal(b.freshness.original_catalog_age_acceptable,true);
 assert.equal(b.feature_policy.original_catalog_max_age_seconds,172800);assert.equal(b.feature_policy.calendar_session_age_guard_seconds,604800);
 assert.equal('freshness_max_age_seconds' in b.feature_policy,false);assert.equal('current_source_age_acceptable' in b.freshness,false);
 assert.equal(b.feature_policy_sha256,sha(JSON.stringify(FE02_PAIRED_POLICY)));assert.equal(b.feature_policy_sha256,FE02_PAIRED_POLICY_SHA256);
 assert.equal(b.restrictions.decision_eligible,false);assert.equal(b.restrictions.historical_point_in_time_claim,false);
});
for(const [name,lastDate,evaluationAt,hours] of [
 ['ordinary Monday','2026-10-23','2026-10-26T14:00:00.000Z',66],
 ['fall DST Monday','2026-10-30','2026-11-02T15:00:00.000Z',67],
 ['spring DST Monday','2026-03-06','2026-03-09T14:00:00.000Z',65],
 ['explicit Monday holiday through Tuesday','2026-09-04','2026-09-08T14:00:00.000Z',90],
])test(`${name}: latest complete grid is available, original48h age still fails`,()=>{
 const f=fixture({lastDate,evaluationAt}),r=buildFE02SourceForecast(f);assert.equal(r.status,'computed');
 assert.equal(v1.buildFE02SourceForecast(f).error,'stale_source');assert.equal(r.freshness.source_age_seconds,hours*3600);
 assert.equal(r.freshness.status,'latest_completed_session');assert.equal(r.freshness.source_session_date,lastDate);
 assert.equal(r.freshness.original_catalog_age_acceptable,false);assert.equal(r.freshness.original_catalog_age_status,'exceeds_original_48h');
 assert.equal(r.freshness.source_as_of,f.requested_window.end);assert.equal(r.freshness.current_calendar_request_through_date,f.symbol_asof);
 assert.equal(r.freshness.source_session_matches_calendar,true);assert.equal(r.freshness.research_display_eligible,true);
 assert.equal(r.source.calendar_omissions_independently_verified,false);assert.equal(r.restrictions.decision_eligible,false);
});
test('early close is not retimestamped to a regular close across the weekend',()=>{
 const f=fixture({earlyClose:true}),r=buildFE02SourceForecast(f);assert.equal(r.status,'computed');assert.equal(r.freshness.source_as_of,'2026-10-23T17:00:00.000Z');assert.equal(r.freshness.source_age_seconds,69*3600);
});
test('exact original48h threshold is independent of session-relative research availability',()=>{
 for(const [time,acceptable] of [['2026-10-25T20:00:00.000Z',true],['2026-10-25T20:00:00.001Z',false]]){
  const r=buildFE02SourceForecast(fixture({evaluationAt:time}));assert.equal(r.status,'computed');assert.equal(r.freshness.original_catalog_age_acceptable,acceptable);
 }
});
test('explicit7day sanity boundary passes exactly and abstains1ms beyond without redefining original48h',()=>{
 for(const [time,computed] of [['2026-10-30T20:00:00.000Z',true],['2026-10-30T20:00:00.001Z',false]]){
  const r=buildFE02SourceForecast(fixture({evaluationAt:time,extraSessions:[]}));assert.equal(r.status,computed?'computed':'unavailable');
  if(computed){assert.equal(r.freshness.original_catalog_age_acceptable,false);assert.equal(r.freshness.source_age_seconds,604800);}else{assert.equal(r.error,'extended_closure_or_calendar_staleness_unverified');assert.equal('calculator_result' in r,false);}
 }
});
test('newly eligible Monday cannot use the complete older Friday window',()=>{
 const before=buildFE02SourceForecast(fixture({evaluationAt:'2026-10-26T20:14:59.999Z'}));assert.equal(before.status,'computed');
 const after=buildFE02SourceForecast(fixture({evaluationAt:'2026-10-26T20:15:00.000Z'}));assert.equal(after.status,'unavailable');assert.equal(after.error,'invalid_requested_window');
});
for(const [name,mutate]of [
 ['missing latest target',f=>f.bars_by_symbol.QQQ.pop()],['missing interior benchmark',f=>f.bars_by_symbol.SPY.splice(9,1)],
 ['calendar incomplete',f=>f.calendar.complete_provider_response=false],['calendar unordered',f=>f.calendar.sessions.reverse()],
 ['calendar not through current date',f=>f.calendar.requested_range.end_date='2026-10-25'],
 ['calendar acquisition start exceeds25s',f=>f.calendar_capture.request_started_at=new Date(Date.parse(f.evaluation_at)-25001).toISOString()],
 ['history receipt future',f=>f.captures[0].received_at=new Date(Date.parse(f.evaluation_at)+1).toISOString()],
 ['hidden fractional bar time',f=>f.bars_by_symbol.QQQ[10].t=f.bars_by_symbol.QQQ[10].t.replace('.000Z','.000000001Z')],
 ['impossible source date',f=>{const b=f.bars_by_symbol.QQQ.find(b=>b.t.startsWith('2026-03-02'));b.t=b.t.replace('2026-03-02','2026-02-30');}],
])test(`${name} never becomes session-current research`,()=>{const f=fixture();mutate(f);const r=buildFE02SourceForecast(f);assert.equal(r.status,'unavailable');assert.equal('calculator_result' in r,false);});
test('V2 manifest pins new files and frozen correctedV1 math, producer,manifest and original scorer',()=>{
 const manifest=JSON.parse(readFileSync(new URL('../research/forecast-features/fe02-session-v2-manifest.json',import.meta.url)));
 assert.equal(manifest.policy_sha256,FE02_PAIRED_POLICY_SHA256);assert.equal(manifest.math_policy_sha256,v1.FE02_PAIRED_POLICY_SHA256);
 for(const [file,expected]of Object.entries(manifest.source_sha256))assert.equal(sha(readFileSync(new URL('../'+file,import.meta.url))),expected,file);
});
