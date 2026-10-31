import test from 'node:test';
import assert from 'node:assert/strict';
import {buildFE12SourceForecast,FE12_TOP_OF_BOOK_POLICY,FE12_TOP_OF_BOOK_V2_SUPERSEDED_BASELINE,FE12_TOP_OF_BOOK_V3_POLICY_SHA256} from '../research/forecast-features/fe12-top-of-book-v3.mjs';
import {makeFE12V3Fixture} from './fixtures/fe12-v3-synthetic.mjs';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
const copy=x=>structuredClone(x);
test('FE12 V3 completed-bucket oracle: 09:35 is k0, noon is k29, and unchanged scorer receives source-derived features',()=>{
 const first=makeFE12V3Fixture({bucketIndex:0}),noon=makeFE12V3Fixture({bucketIndex:29}),a=buildFE12SourceForecast(first),b=buildFE12SourceForecast(noon);
 assert.equal(a.status,'computed',a.error);assert.equal(b.status,'computed',b.error);assert.equal(a.source.bucket.index,0);assert.equal(b.source.bucket.index,29);assert.equal(b.source.bucket.elapsed_rth_minutes,150);assert.equal(FE12_TOP_OF_BOOK_POLICY.id,'FE12_IEX_TOP_OF_BOOK_ELAPSED_RTH_BUCKET_V3');assert.equal(FE12_TOP_OF_BOOK_POLICY.prior_sessions,16);assert.equal(FE12_TOP_OF_BOOK_V2_SUPERSEDED_BASELINE.status,'SUPERSEDED_BASELINE');assert.match(FE12_TOP_OF_BOOK_V3_POLICY_SHA256,/^[0-9a-f]{64}$/);
 assert.deepEqual(b.calculator_result,evaluateForecastEngine('FE12',b.features));assert.equal(b.source.historical_availability,'unknown; observations acquired now do not prove historical public availability');assert.equal(b.restrictions.decision_eligible,false);assert.equal(b.source.quote_snapshots.length,17);assert.equal(b.coverage.expected_minute_bars,85);
});
test('FE12 V3 aligns elapsed RTH buckets through DST and year boundaries',()=>{
 for(const evaluationDate of ['2026-11-02','2027-01-04']){const f=makeFE12V3Fixture({evaluationDate,bucketIndex:29}),r=buildFE12SourceForecast(f);assert.equal(r.status,'computed',r.error);assert.equal(r.source.bucket.index,29);assert.match(r.source.bucket.end,/^\d{4}-\d\d-\d\dT(16|17):00:00\.000Z$/);}
});
test('FE12 V3 excludes early closes by calendar eligibility and never replaces missing selected data',()=>{
 const f=makeFE12V3Fixture({bucketIndex:50,earlyClose:true}),r=buildFE12SourceForecast(f);assert.equal(r.status,'computed',r.error);assert.equal(r.coverage.bucket_excluded_early_close_sessions,1);assert.equal(r.source.calendar.bucket_excluded_sessions.length,1);
 const missing=copy(f);missing.quote_windows[0].quotes=[];const bad=buildFE12SourceForecast(missing);assert.equal(bad.status,'unavailable');assert.equal(bad.error,'invalid_quote_point_selection');
 const noBar=copy(f);noBar.bars.shift();noBar.captures.find(c=>c.operation==='history_1Min_bars_page_1').retained_rows=84;assert.equal(buildFE12SourceForecast(noBar).error,'missing_realized_vol_or_volume_slot');
});
test('FE12 V3 rejects boundary advancement, future quotes, stale data, and caller-selected bucket indexes',()=>{
 const f=makeFE12V3Fixture(),advanced=copy(f);advanced.evaluation_at=new Date(Date.parse(f.evaluation_at)+300000).toISOString();assert.equal(buildFE12SourceForecast(advanced).error,'bucket_selection_mismatch');
 const future=copy(f);future.quote_windows.at(-1).quotes[0].t=new Date(Date.parse(f.evaluation_at)+1).toISOString();assert.equal(buildFE12SourceForecast(future).error,'invalid_l1_quote_snapshot');
 const stale=copy(f);stale.evaluation_at=new Date(Date.parse(f.evaluation_at)+300001).toISOString();assert.notEqual(buildFE12SourceForecast(stale).status,'computed');
 const wrong=copy(f);wrong.bucket_index=28;assert.equal(buildFE12SourceForecast(wrong).error,'bucket_selection_mismatch');
});

test('FE12 V3 condition-code output is bounded without truncation or partial scoring',()=>{
 const codes=n=>Array.from({length:n},(_,i)=>i.toString(36).toUpperCase().padStart(3,'0'));
 const admitted=makeFE12V3Fixture();for(const row of admitted.quote_windows)row.quotes[0].c=codes(64);const good=buildFE12SourceForecast(admitted);assert.equal(good.status,'computed',good.error);assert.equal(Object.keys(good.measurements.quote_condition_counts).length,64);assert.equal(FE12_TOP_OF_BOOK_POLICY.limits.max_condition_codes_per_quote,64);
 const over=makeFE12V3Fixture();over.quote_windows.at(-1).quotes[0].c=codes(1200);const rejected=buildFE12SourceForecast(over);assert.equal(rejected.status,'unavailable');assert.equal(rejected.error,'quote_condition_limit_exceeded');assert.equal(rejected.features,undefined);
 const unsafe=makeFE12V3Fixture();unsafe.quote_windows.at(-1).quotes[0].bs=1e100;assert.equal(buildFE12SourceForecast(unsafe).error,'invalid_quote_size');
 const infiniteNotional=makeFE12V3Fixture(),q=infiniteNotional.quote_windows.at(-1).quotes[0];q.bp=1e308;q.ap=1.1e308;q.bs=Number.MAX_SAFE_INTEGER;q.as=Number.MAX_SAFE_INTEGER;assert.equal(buildFE12SourceForecast(infiniteNotional).error,'invalid_quote_notional');
});
