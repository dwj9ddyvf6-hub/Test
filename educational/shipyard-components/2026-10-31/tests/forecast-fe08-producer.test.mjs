import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto,createHash} from 'node:crypto';
import * as features from '../research/forecast-features/fe08-rv-v1.mjs';
import {fixture} from './fixtures/fe08-synthetic.mjs';
const code=readFileSync(new URL('../worker/exchange-calendar.js',import.meta.url),'utf8')+'\n'+readFileSync(new URL('../worker/forecast-fe08.js',import.meta.url),'utf8')+'\nglobalThis.run=shipyardForecastFE08;globalThis.boundary=shipyardCalendarBoundary;globalThis.cache=SHIPYARD_FE08_CACHE;';
function harness(options={}) {
 const f=fixture(),clock={now:Date.parse(options.at||f.evaluation_at)},calls=[],rates=[],bodyLimits=[];
 class ClockDate extends Date {constructor(...args){super(...(args.length?args:[clock.now]));}static now(){return clock.now;}}
 const calendar=f.calendar.sessions.map(s=>({date:s.date,open:'09:30',close:'16:00'})).concat({date:'2026-10-29',open:'09:30',close:'16:00'});
 let page=0;
 const context={Date:ClockDate,Intl,URL,URLSearchParams,AbortSignal,TextEncoder,crypto:webcrypto,SHIPYARD_FORECAST_FEATURES:{...features,buildFE08SourceForecast:input=>{const r=features.buildFE08SourceForecast(input);clock.now+=options.computeAdvance||0;return r;}},
  json:(value,status=200)=>({value,status}),researchResponse:value=>({value,status:200}),alpacaRateAllowed:()=>{rates.push(1);return typeof options.rate==='function'?options.rate(rates.length):options.rate!==false;},
  readBoundedBody:async(response,max)=>{bodyLimits.push(max);const text=await response.text();if(new TextEncoder().encode(text).length>max)throw Error('too_large');return text;},
  fetch:async(url,init)=>{calls.push({url:url.toString(),init});if(options.advance)clock.now+=options.advance;
   assert.equal(init.method,'GET');assert.equal(init.redirect,'manual');assert.ok(!/accounts|orders/.test(url.toString()));
   if(options.fetch)return options.fetch(url,init,calls.length,{f,clock,calendar});
   if(options.http)return new Response('{}',{status:options.http});
   if(url.toString().includes('/calendar'))return Response.json(options.calendar??calendar);
   const requested=new URL(url);const rows=f.bars.filter(b=>Date.parse(b.t)>=Date.parse(requested.searchParams.get('start'))&&Date.parse(b.t)<=Date.parse(requested.searchParams.get('end')));
   const p=options.pages?.[page]??{symbol:decodeURIComponent(requested.pathname.split('/').at(-2)),bars:rows,next_page_token:null};page++;
   return Response.json(p);
  }};
 vm.createContext(context);vm.runInContext(code,context);
 const request=new Request('https://owner.test/api/research/forecast-from-bars');
 return {run:(args={symbol:'SPY'},env={ALPACA_API_KEY_ID:'fixture-key',ALPACA_API_SECRET_KEY:'fixture-secret'},req=request)=>context.run(req,args,env),calls,rates,bodyLimits,clock,context,f,calendar};
}
test('bounded source request computes exact scorer; cache preserves source and evaluation clocks',async()=>{const h=harness(),a=await h.run();assert.equal(a.status,200);assert.equal(a.value.status,'computed');assert.equal(h.calls.length,2);assert.equal(h.rates.length,3);assert.equal(a.value.source.captures.length,1);assert.equal(a.value.acquisition.request_count,2);assert.equal(a.value.delivery.cache_hit,false);const url=new URL(h.calls[1].url);assert.equal(url.searchParams.get('timeframe'),'5Min');assert.equal(url.searchParams.get('adjustment'),'raw');assert.equal(url.searchParams.get('feed'),'iex');assert.equal(url.searchParams.get('limit'),'5000');assert.equal(url.searchParams.get('end'),'2026-10-28T19:59:59.999Z');h.clock.now+=10000;const b=await h.run();assert.equal(b.value.delivery.cache_hit,true);assert.equal(h.calls.length,2);assert.equal(b.value.evaluation_at,a.value.evaluation_at);assert.deepEqual(b.value.source.captures,a.value.source.captures);assert.notEqual(b.value.delivery.served_at,a.value.delivery.served_at);assert.equal(b.value.restrictions.order_submission_enabled,false);});
test('two-page complete provider cursor is followed with immutable query',async()=>{const f=fixture(),h=harness({pages:[{bars:f.bars.slice(0,900),next_page_token:'next'},{bars:f.bars.slice(900),next_page_token:null}]});const r=await h.run();assert.equal(r.value.status,'computed');assert.equal(h.calls.length,3);const a=new URL(h.calls[1].url),b=new URL(h.calls[2].url);assert.equal(b.searchParams.get('page_token'),'next');b.searchParams.delete('page_token');assert.equal(a.toString(),b.toString());assert.equal(r.value.source.captures[1].request_url.includes('next'),false);});
test('unfinished pagination is never labeled complete',async()=>{const h=harness({pages:[{bars:[],next_page_token:'a'},{bars:[],next_page_token:'b'}]});const r=await h.run();assert.equal(r.value.error,'provider_pagination_bound_exceeded');assert.equal(h.calls.length,3);});
test('repeated provider cursor fails',async()=>{const h=harness({pages:[{bars:[],next_page_token:'a'},{bars:[],next_page_token:'a'}]});assert.equal((await h.run()).value.error,'invalid_provider_pagination');});
test('provider identity mismatch rejected without fallback',async()=>{const h=harness({pages:[{symbol:'QQQ',bars:[],next_page_token:null}]});assert.equal((await h.run()).value.error,'provider_schema_invalid');assert.equal(h.calls.length,2);});
for(const [http,error] of [[401,'market_data_authentication_failed'],[403,'requested_feed_not_entitled'],[429,'provider_rate_limited'],[500,'provider_unavailable']])test(`provider${http} stays explicit and never falls back`,async()=>{const h=harness({http});assert.equal((await h.run()).value.error,error);assert.equal(h.calls.length,1);});
test('rate limit and missing keys do not fetch',async()=>{let h=harness({rate:false});assert.equal((await h.run()).status,429);assert.equal(h.calls.length,0);h=harness();assert.equal((await h.run({symbol:'SPY'},{})).value.error,'market_data_credentials_unavailable');assert.equal(h.calls.length,0);});
test('caller cannot upload features, URLs, feed, dates or arbitrary engine policy',async()=>{for(const extra of [{features:{}},{url:'https://example.com'},{feed:'sip'},{start:'2020-01-01'},{engine_id:'FE09'}]){const h=harness();assert.equal((await h.run({symbol:'SPY',...extra})).status,400);assert.equal(h.calls.length,0);}});
test('request cancellation is not cached or fetched',async()=>{const h=harness(),c=new AbortController();c.abort();const req=new Request('https://owner.test/',{signal:c.signal});assert.equal((await h.run({symbol:'SPY'},undefined,req)).status,408);assert.equal(h.calls.length,0);});
test('acquisition deadline is bounded',async()=>{const h=harness({advance:26000});assert.equal((await h.run()).value.error,'acquisition_deadline_exceeded');assert.equal(h.calls.length,1);});
test('cache expiry cannot keep yesterday when newly completed session becomes eligible',async()=>{const h=harness({at:'2026-10-29T20:14:50Z'});assert.equal((await h.run()).value.status,'computed');h.clock.now+=20000;const r=await h.run();assert.equal(r.value.status,'unavailable');assert.equal(r.value.error,'missing_regular_session_slot');assert.equal(h.calls.length,4);});
test('calendar DST conversion and early-close boundary are exact',()=>{const h=harness();assert.equal(h.context.boundary('2026-10-30','09:30'),'2026-10-30T13:30:00.000Z');assert.equal(h.context.boundary('2026-11-02','09:30'),'2026-11-02T14:30:00.000Z');assert.equal(h.context.boundary('2026-11-27','13:00'),'2026-11-27T18:00:00.000Z');});

const digest = text => createHash('sha256').update(text).digest('hex');
test('all completed response receipts carry actual clocks and reproducible hashes',async()=>{
 const h=harness(),r=(await h.run()).value;
 assert.equal(r.acquisition.calendar_capture.response_sha256,digest(JSON.stringify(h.calendar)));
 assert.equal(r.source.captures[0].response_sha256,digest(JSON.stringify({symbol:'SPY',bars:h.f.bars,next_page_token:null})));
 for(const receipt of [r.acquisition.calendar_capture,...r.source.captures]){
  assert.equal(receipt.http_status,200);assert.equal(receipt.request_started_at,h.f.evaluation_at);
  assert.equal(receipt.http_response_received_at,h.f.evaluation_at);assert.equal(receipt.received_at,h.f.evaluation_at);
  assert.equal(receipt.hash_serialization,'UTF-8 re-encoding of decoded response text');
 }
 assert.deepEqual(h.bodyLimits,[262144,2097152]);
 assert.ok(new TextEncoder().encode(JSON.stringify(r)).length<48*1024);
 assert.equal(JSON.stringify(r).includes('fixture-secret'),false);
 assert.equal(JSON.stringify(r).includes('fixture-key'),false);
});
test('lowercase symbol shares normalized cache but a different symbol does not',async()=>{
 const h=harness(),a=await h.run({symbol:'spy'}),b=await h.run({symbol:'SPY'}),c=await h.run({symbol:'QQQ'});
 assert.equal(a.value.symbol,'SPY');assert.equal(b.value.delivery.cache_hit,true);
 assert.equal(c.value.symbol,'QQQ');assert.equal(c.value.delivery.cache_hit,false);assert.equal(h.calls.length,4);
});
test('cache expires at exactly 60 seconds and retains at most eight symbols',async()=>{
 const h=harness();await h.run();h.clock.now+=60000;assert.equal((await h.run()).value.delivery.cache_hit,false);
 for(const symbol of ['AAA','BBB','CCC','DDD','EEE','FFF','GGG','HHH'])assert.equal((await h.run({symbol})).value.status,'computed');
 assert.equal(h.context.cache.size,8);assert.equal((await h.run()).value.delivery.cache_hit,false);
});
test('cache is discarded on backwards clock change rather than delivering future evaluation',async()=>{
 const h=harness();await h.run();h.clock.now-=1000;assert.equal((await h.run()).value.delivery.cache_hit,false);assert.equal(h.calls.length,4);
});
test('cache expires at declared source-age threshold, without changing old receipts',async()=>{
 const calendar=fixture().calendar.sessions.map(s=>({date:s.date,open:'09:30',close:'16:00'}));
 const h=harness({at:'2026-10-30T19:59:50Z',calendar}),a=await h.run();assert.equal(a.value.freshness.status,'within_declared_age');
 h.clock.now+=11000;const b=await h.run();assert.equal(b.value.delivery.cache_hit,false);assert.equal(b.value.freshness.status,'stale');
 assert.equal(b.value.freshness.source_as_of,a.value.freshness.source_as_of);assert.equal(b.value.restrictions.decision_eligible,false);
});
test('credential removal and cancellation are honored even on an otherwise valid cache hit',async()=>{
 const h=harness();await h.run();assert.equal((await h.run({symbol:'SPY'},{})).status,503);
 const c=new AbortController();c.abort();assert.equal((await h.run({symbol:'SPY'},undefined,new Request('https://owner.test/',{signal:c.signal}))).status,408);
 assert.equal(h.calls.length,2);
});
test('all worst-case requests must be reserved before provider acquisition starts',async()=>{
 const h=harness({rate:n=>n<3});assert.equal((await h.run()).status,429);assert.equal(h.calls.length,0);assert.equal(h.rates.length,3);
});
test('an HTTP rejection records headers receipt, never an unconsumed body receipt',async()=>{
 const h=harness({http:403}),r=(await h.run()).value;assert.equal(r.source_receipts.length,1);
 assert.equal(r.source_receipts[0].http_status,403);assert.equal(r.source_receipts[0].http_response_received_at,h.f.evaluation_at);
 assert.equal(r.source_receipts[0].received_at,null);assert.equal(r.source_receipts[0].response_sha256,null);
 assert.equal(r.feature_policy_sha256,features.FE08_RV_POLICY_SHA256);
 assert.equal(r.restrictions.historical_point_in_time_claim,false);assert.equal(h.context.cache.size,0);
});
test('network failure has no fabricated provider receipt and failure is not cached',async()=>{
 const h=harness({fetch:()=>{throw Error('network fixture-secret');}}),a=await h.run();
 assert.equal(a.value.error,'source_acquisition_failed');assert.equal(a.value.source_receipts.length,0);
 assert.equal(JSON.stringify(a).includes('fixture-secret'),false);await h.run();assert.equal(h.calls.length,2);assert.equal(h.context.cache.size,0);
});
test('timeout remains bounded and actionable without fallback',async()=>{
 const h=harness({fetch:()=>{const e=Error('synthetic timeout');e.name='TimeoutError';throw e;}});
 assert.equal((await h.run()).value.error,'source_request_timeout');assert.equal(h.calls.length,1);
});
test('invalid JSON still preserves received response hash',async()=>{
 const h=harness({fetch:()=>new Response('not json')}),r=(await h.run()).value;
 assert.equal(r.error,'provider_schema_invalid');assert.equal(r.source_receipts[0].response_sha256,digest('not json'));
 assert.equal(r.source_receipts[0].received_at,h.f.evaluation_at);
});
for(const [label,bytes] of [['calendar',262145],['bars',2097153]])test(`${label} body-size bound fails closed`,async()=>{
 const h=harness({fetch:(url,init,n,{calendar})=>n===1&&label==='bars'?Response.json(calendar):new Response('x'.repeat(bytes))});
 const r=(await h.run()).value;assert.equal(r.error,'source_acquisition_failed');assert.equal(r.source_receipts.at(-1).received_at,null);
 assert.equal(r.source_receipts.at(-1).response_sha256,null);assert.equal(h.context.cache.size,0);
});
for(const token of [true,{},'x'.repeat(2049),'bad\nvalue'])test(`invalid provider cursor ${typeof token}/${String(token).length} fails closed`,async()=>{
 const h=harness({pages:[{bars:[],next_page_token:token}]});assert.equal((await h.run()).value.error,'invalid_provider_pagination');assert.equal(h.calls.length,2);
});
test('absence of continuation field is not evidence that pagination completed',async()=>{
 const h=harness({pages:[{bars:fixture().bars}]});assert.equal((await h.run()).value.error,'provider_schema_invalid');
});
test('maximum provider page row count is enforced before feature construction',async()=>{
 const h=harness({pages:[{bars:Array(5001).fill(null),next_page_token:null}]});assert.equal((await h.run()).value.error,'provider_schema_invalid');
});
test('calendar schema, order, lookback range and insufficient completed sessions reject before bars',async()=>{
 for(const calendar of [{},[],Array(62).fill({}),[{date:'2026-02-30',open:'09:30',close:'16:00'}],
  [{date:'2026-10-28',open:'09:30',close:'16:00'},{date:'2026-10-28',open:'09:30',close:'16:00'}],
  [{date:'2020-01-01',open:'09:30',close:'16:00'}],[{date:'2026-10-28',open:'09:70',close:'16:00'}]]){
  const h=harness({calendar}),r=await h.run();assert.equal(r.value.status,'unavailable');assert.equal(h.calls.length,1);
 }
});
test('crossing newly eligible session during acquisition aborts instead of caching a prior window',async()=>{
 const h=harness({at:'2026-10-29T20:14:50Z',advance:6000}),r=await h.run();
 assert.equal(r.value.error,'session_boundary_advanced');assert.equal(h.context.cache.size,0);assert.equal(h.calls.length,2);
});
test('request cancellation between responses preserves only actually received captures',async()=>{
 const c=new AbortController(),h=harness({fetch:(url,init,n,{calendar})=>{c.abort();return Response.json(calendar);}});
 const r=await h.run({symbol:'SPY'},undefined,new Request('https://owner.test/',{signal:c.signal}));
 assert.equal(r.status,408);assert.equal(r.value.error,'cancelled');assert.equal(r.value.source_receipts.length,1);assert.equal(h.calls.length,1);assert.equal(h.context.cache.size,0);
});
test('duplicate bar across provider page boundary cannot be silently deduplicated',async()=>{
 const f=fixture(),h=harness({pages:[{bars:f.bars.slice(0,900),next_page_token:'a'},{bars:f.bars.slice(899),next_page_token:null}]});
 const r=await h.run();assert.equal(r.value.error,'unordered_or_duplicate_bar');assert.equal(h.context.cache.size,0);
 assert.equal(r.value.symbol,'SPY');assert.equal(r.value.source_receipts.length,3);assert.equal('calculator_result' in r.value,false);
});

test('a result computed exactly at source-age limit cannot cache fresh status beyond that instant',async()=>{
 const calendar=fixture().calendar.sessions.map(s=>({date:s.date,open:'09:30',close:'16:00'}));
 const h=harness({at:'2026-10-30T20:00:00Z',calendar}),a=await h.run();assert.equal(a.value.freshness.status,'within_declared_age');
 h.clock.now+=1;const b=await h.run();assert.equal(b.value.delivery.cache_hit,false);assert.equal(b.value.freshness.status,'stale');assert.equal(h.calls.length,4);
});

test('actual computation completion clock and boundary are checked after feature construction',async()=>{
 const h=harness({computeAdvance:10}),a=await h.run();
 assert.equal(Date.parse(a.value.computed_at)-Date.parse(a.value.evaluation_at),10);
 assert.equal(a.value.delivery.served_at,a.value.computed_at);assert.equal(a.value.acquisition.elapsed_ms,10);
 const crossed=harness({at:'2026-10-29T20:14:59.999Z',computeAdvance:2}),b=await crossed.run();
 assert.equal(b.value.error,'session_boundary_advanced');assert.equal(crossed.context.cache.size,0);
});
