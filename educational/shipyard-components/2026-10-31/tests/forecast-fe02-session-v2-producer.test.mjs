import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import * as features from '../research/forecast-features/fe02-residual-session-v2.mjs';
import {fixture} from './fixtures/fe02-synthetic.mjs';
import {fixture as sessionFixture,boundary} from './fixtures/fe02-session-v2-synthetic.mjs';

const code=readFileSync(new URL('../worker/exchange-calendar.js',import.meta.url),'utf8')+'\n'
  +readFileSync(new URL('../worker/forecast-fe02-session-v2.js',import.meta.url),'utf8')
  +'\nglobalThis.run=shipyardForecastFE02;globalThis.cache=SHIPYARD_FE02_CACHE;';
function harness(options={}){
  const f=options.fixture||fixture(),clock={now:Date.parse(options.at||f.evaluation_at)},calls=[],rates=[],bodyLimits=[],pages={QQQ:0,SPY:0};
  class ClockDate extends Date {constructor(...args){super(...(args.length?args:[clock.now]));}static now(){return clock.now;}}
  const calendar=f.calendar.sessions.map(session=>({date:session.date,open:'09:30',close:(Date.parse(session.close)-Date.parse(session.open))===210*60000?'13:00':'16:00'}));
  if(!calendar.some(row=>row.date===f.symbol_asof))calendar.push({date:f.symbol_asof,open:'09:30',close:'16:00'});
  const context={Date:ClockDate,Intl,URL,URLSearchParams,AbortSignal,TextEncoder,crypto:webcrypto,
    SHIPYARD_FORECAST_PAIRED_FEATURES:{...features,buildFE02SourceForecast:input=>{const result=features.buildFE02SourceForecast(input);clock.now+=options.computeAdvance||0;return result;}},
    json:(value,status=200)=>({value,status}),researchResponse:value=>({value,status:200}),
    alpacaRateAllowed:()=>{rates.push(1);return typeof options.rate==='function'?options.rate(rates.length):options.rate!==false;},
    readBoundedBody:async(response,max)=>{bodyLimits.push(max);const text=await response.text();if(new TextEncoder().encode(text).length>max)throw Error('body_too_large');return text;},
    fetch:async(url,init)=>{
      const u=new URL(url);calls.push({url:u,init});if(options.advance)clock.now+=options.advance;
      assert.equal(init.method,'GET');assert.equal(init.redirect,'manual');assert.ok(!/accounts|orders/.test(u.toString()));
      if(options.fetch)return options.fetch(u,init,calls.length,{f,clock,calendar,pages});
      if(options.http)return new Response('{}',{status:options.http});
      if(u.pathname.endsWith('/calendar'))return Response.json(options.calendar||calendar);
      const symbol=decodeURIComponent(u.pathname.split('/').at(-2)),index=pages[symbol]++;
      const requested=options.pages?.[symbol]?.[index];
      if(requested)return Response.json({symbol,...requested});
      const rows=f.bars_by_symbol[symbol].filter(bar=>Date.parse(bar.t)>=Date.parse(u.searchParams.get('start'))&&Date.parse(bar.t)<=Date.parse(u.searchParams.get('end')));
      return Response.json({symbol,bars:rows,next_page_token:null});
    }};
  vm.createContext(context);vm.runInContext(code,context);
  const request=new Request('https://owner.test/api/research/forecast-from-bars');
  return {run:(args={symbol:'QQQ'},env={ALPACA_API_KEY_ID:'fixture-key',ALPACA_API_SECRET_KEY:'fixture-secret'},req=request)=>context.run(req,args,env),calls,rates,bodyLimits,clock,context,f,calendar};
}

test('paired producer acquires only requested ticker plus SPY on the declared completed-session window',async()=>{
  const h=harness(),result=await h.run();assert.equal(result.status,200);assert.equal(result.value.status,'computed');
  assert.equal(result.value.engine_id,'FE02');assert.equal(result.value.symbol,'QQQ');assert.equal(result.value.benchmark_symbol,'SPY');
  assert.equal(h.calls.length,3);assert.equal(h.rates.length,5);assert.deepEqual(h.bodyLimits,[262144,524288,524288]);
  const history=h.calls.filter(call=>call.url.pathname.includes('/bars'));
  assert.deepEqual(history.map(call=>decodeURIComponent(call.url.pathname.split('/').at(-2))).sort(),['QQQ','SPY']);
  for(const {url}of history){assert.equal(url.searchParams.get('timeframe'),'1Day');assert.equal(url.searchParams.get('adjustment'),'split');assert.equal(url.searchParams.get('feed'),'iex');assert.equal(url.searchParams.get('currency'),'USD');assert.equal(url.searchParams.get('limit'),'1000');assert.equal(url.searchParams.get('asof'),'2026-10-29');assert.equal(url.searchParams.get('start'),h.f.bars_by_symbol.QQQ[0].t);}
  assert.equal(result.value.source.calendar.selected_session_grid.rows.length,505);assert.equal(result.value.coverage.complete_sessions,505);
  assert.equal(result.value.source.captures.length,2);assert.equal(result.value.acquisition.calendar_capture.http_status,200);
  assert.equal(result.value.acquisition.request_count,3);assert.equal(result.value.acquisition.request_bound,5);
  assert.equal(JSON.stringify(result).includes('fixture-secret'),false);assert.equal(JSON.stringify(result).includes('fixture-key'),false);
  assert.ok(new TextEncoder().encode(JSON.stringify(result.value)).length<48*1024);
});

test('bounded continuation pages preserve the query and receipts without exposing page tokens',async()=>{
  const rows={QQQ:harness().f.bars_by_symbol.QQQ,SPY:harness().f.bars_by_symbol.SPY};
  const pages=Object.fromEntries(Object.entries(rows).map(([symbol,bars])=>[symbol,[{bars:bars.slice(0,300),next_page_token:'cursor-one'},{bars:bars.slice(300),next_page_token:null}]]));
  const h=harness({pages}),result=await h.run();assert.equal(result.value.status,'computed');assert.equal(h.calls.length,5);
  for(const symbol of ['QQQ','SPY']){
    const symbolCalls=h.calls.filter(call=>call.url.pathname.includes(`/stocks/${symbol}/`));assert.equal(symbolCalls.length,2);
    const first=new URL(symbolCalls[0].url),second=new URL(symbolCalls[1].url);assert.equal(second.searchParams.get('page_token'),'cursor-one');
    second.searchParams.delete('page_token');assert.equal(first.toString(),second.toString());
    assert.equal(result.value.source.captures.find(c=>c.operation===`history_${symbol}_1Day_page_2`).request_url.includes('cursor-one'),false);
  }
});

test('no source success is cached; bounded successful cache retains original evaluation and receipts',async()=>{
  const h=harness(),first=await h.run();h.clock.now+=1000;const cached=await h.run({symbol:'qqq'});assert.equal(first.value.status,'computed');assert.equal(cached.value.delivery.cache_hit,true);
  assert.equal(h.calls.length,3);assert.deepEqual(cached.value.source.captures,first.value.source.captures);assert.equal(cached.value.evaluation_at,first.value.evaluation_at);
  assert.notEqual(cached.value.delivery.served_at,first.value.delivery.served_at);
  const other=await h.run({symbol:'AAPL'});assert.equal(other.value.status,'unavailable');assert.equal(h.calls.length,6);
});

for(const [status,error]of [[401,'market_data_authentication_failed'],[403,'requested_feed_not_entitled'],[429,'provider_rate_limited'],[500,'provider_unavailable']])
  test(`provider HTTP ${status} is explicit and never falls back`,async()=>{const h=harness({http:status}),r=await h.run();assert.equal(r.status,503);assert.equal(r.value.error,error);assert.equal(h.calls.length,1);assert.equal(h.context.cache.size,0);});

test('missing credentials, disallowed symbol, rate limit and caller payload fail before provider calls',async()=>{
  let h=harness();assert.equal((await h.run({symbol:'QQQ'},{})).value.error,'market_data_credentials_unavailable');assert.equal(h.calls.length,0);
  h=harness();assert.equal((await h.run({symbol:'SPY'})).status,400);assert.equal((await h.run({symbol:'QQQ',features:{}})).status,400);assert.equal(h.calls.length,0);
  h=harness({rate:n=>n<5});assert.equal((await h.run()).status,429);assert.equal(h.calls.length,0);assert.equal(h.rates.length,5);
});

test('request cancellation, acquisition deadline and page bound do not produce partial scores',async()=>{
  let h=harness(),controller=new AbortController();controller.abort();assert.equal((await h.run({symbol:'QQQ'},undefined,new Request('https://owner.test/',{signal:controller.signal}))).status,408);assert.equal(h.calls.length,0);
  h=harness({advance:26000});assert.equal((await h.run()).value.error,'acquisition_deadline_exceeded');assert.equal(h.calls.length,1);
  h=harness({pages:{QQQ:[{bars:[],next_page_token:'a'},{bars:[],next_page_token:'b'}]}});assert.equal((await h.run()).value.error,'provider_pagination_bound_exceeded');assert.equal(h.context.cache.size,0);
});

test('provider identity and complete pair are required, with no stale/calendar substitution',async()=>{
  let h=harness({fetch:(url,init,n,{f,calendar})=>url.pathname.endsWith('/calendar')?Response.json(calendar):Response.json({symbol:'SPY',bars:f.bars_by_symbol.SPY,next_page_token:null})});
  assert.equal((await h.run()).value.error,'provider_schema_invalid');
  h=harness({fetch:(url,init,n,{f,calendar})=>url.pathname.endsWith('/calendar')?Response.json(calendar):Response.json({symbol:decodeURIComponent(url.pathname.split('/').at(-2)),bars:url.pathname.includes('/SPY/')?[]:f.bars_by_symbol.QQQ,next_page_token:null})});
  assert.equal((await h.run()).value.status,'unavailable');assert.equal(h.context.cache.size,0);
  h=harness({calendar:[{date:'not-a-date',open:'09:30',close:'16:00'}]});assert.equal((await h.run()).value.error,'invalid_calendar');assert.equal(h.calls.length,1);
});

test('provider capture records real receipt clocks and selected session watermark separately',async()=>{
  const h=harness(),r=(await h.run()).value,receipts=[r.acquisition.calendar_capture,...r.source.captures];
  for(const receipt of receipts){assert.equal(receipt.http_status,200);assert.ok(Date.parse(receipt.request_started_at)<=Date.parse(receipt.http_response_received_at));assert.ok(Date.parse(receipt.http_response_received_at)<=Date.parse(receipt.received_at));assert.match(receipt.response_sha256,/^[a-f0-9]{64}$/);assert.equal(receipt.hash_serialization,'UTF-8 re-encoding of decoded response text');}
  assert.equal(r.freshness.source_as_of,'2026-10-28T20:00:00.000Z');assert.equal(r.evaluation_at,'2026-10-29T19:40:00.000Z');
  assert.equal(r.source.atomic_snapshot,false);assert.equal(r.source.rights_attestation,null);assert.equal(r.restrictions.decision_eligible,false);
});

test('V2 weekend source stays at Friday close with false original age flag and delivery-only cache ages',async()=>{
 const h=harness({fixture:sessionFixture()}),a=(await h.run()).value;assert.equal(a.status,'computed');assert.equal(a.schema,'SHIPYARD_FE02_SOURCE_FORECAST_V2');
 assert.equal(a.freshness.source_age_seconds,66*3600);assert.equal(a.freshness.original_catalog_age_acceptable,false);assert.equal(a.delivery.original_catalog_age_acceptable_at_delivery,false);
 h.clock.now+=59000;const b=(await h.run()).value;assert.equal(b.delivery.cache_hit,true);assert.equal(h.calls.length,3);
 assert.equal(b.evaluation_at,a.evaluation_at);assert.deepEqual(b.source.captures,a.source.captures);assert.deepEqual(b.freshness,a.freshness);
 assert.equal(b.delivery.source_age_seconds_at_delivery,a.freshness.source_age_seconds+59);assert.equal(b.delivery.last_capture_age_seconds_at_delivery,59);
 h.clock.now+=1000;const c=(await h.run()).value;assert.equal(c.delivery.cache_hit,false);assert.equal(h.calls.length,6);
});
test('V2 caches never carry Friday across new eligible Monday close',async()=>{
 const f=sessionFixture({evaluationAt:'2026-10-26T20:14:50.000Z'}),h=harness({fixture:f});assert.equal((await h.run()).value.status,'computed');
 h.clock.now+=10000;const r=await h.run();assert.equal(r.value.status,'unavailable');assert.equal('calculator_result' in r.value,false);assert.equal(h.calls.length,6);
});
test('V2 acquisition and computation crossing eligibility boundary abstain rather than falling back',async()=>{
 const f=sessionFixture({evaluationAt:'2026-10-26T20:14:59.000Z'});
 for(const opts of [{advance:500},{computeAdvance:1000}]){const h=harness({...opts,fixture:f}),r=await h.run();assert.equal(r.value.status,'unavailable');assert.equal(r.value.error,'session_boundary_advanced');assert.equal(h.context.cache.size,0);}
});
test('V2 midnight/mapping change invalidates cache, even with unchanged latest session',async()=>{
 const f=sessionFixture({evaluationAt:'2026-10-24T03:59:50.000Z',extraSessions:[]}),h=harness({fixture:f});const a=await h.run();assert.equal(a.value.status,'computed');
 h.clock.now+=10000;const b=await h.run();assert.equal(b.value.status,'computed');assert.equal(b.value.delivery.cache_hit,false);assert.equal(h.calls.length,6);assert.equal(b.value.source.symbol_asof,'2026-10-24');
});
test('V2 original48h cache boundary refreshes diagnostic without blocking Sunday research',async()=>{
 const f=sessionFixture({evaluationAt:'2026-10-25T19:59:59.000Z'}),h=harness({fixture:f,calendar:f.calendar.sessions.map(s=>({date:s.date,open:'09:30',close:'16:00'}))});
 const a=(await h.run()).value;assert.equal(a.freshness.original_catalog_age_acceptable,true);
 h.clock.now+=1001;const b=(await h.run()).value;assert.equal(b.status,'computed');assert.equal(b.delivery.cache_hit,false);assert.equal(b.freshness.original_catalog_age_acceptable,false);assert.equal(h.calls.length,6);
});
test('V2 seven-day guard expires cache and rejects computation that crosses the guard',async()=>{
 const f=sessionFixture({evaluationAt:'2026-10-30T19:59:59.000Z',extraSessions:[]}),calendar=f.calendar.sessions.map(s=>({date:s.date,open:'09:30',close:'16:00'}));
 const h=harness({fixture:f,calendar}),a=(await h.run()).value;assert.equal(a.status,'computed');h.clock.now+=1001;
 const b=(await h.run()).value;assert.equal(b.status,'unavailable');assert.equal(b.error,'extended_closure_or_calendar_staleness_unverified');assert.equal(h.calls.length,6);
 const crossing=harness({fixture:f,calendar,computeAdvance:1001});assert.equal((await crossing.run()).value.error,'extended_closure_or_calendar_staleness_unverified');assert.equal(crossing.context.cache.size,0);
});
test('V2 cached responses still honor credential removal, cancellation and clock reversal',async()=>{
 const h=harness({fixture:sessionFixture()});await h.run();
 assert.equal((await h.run({symbol:'QQQ'},{})).value.error,'market_data_credentials_unavailable');assert.equal(h.calls.length,3);
 const c=new AbortController();c.abort();assert.equal((await h.run({symbol:'QQQ'},undefined,new Request('https://owner.test/',{signal:c.signal}))).value.status,'cancelled');assert.equal(h.calls.length,3);
 h.clock.now-=1;const r=await h.run();assert.equal(r.value.delivery.cache_hit,false);assert.equal(h.calls.length,6);
});

for(const [lastDate,evaluationAt,midnight] of [
 ['2026-10-30','2026-11-01T03:59:50.000Z','2026-11-01T04:00:00.000Z'],
 ['2026-03-06','2026-03-08T04:59:50.000Z','2026-03-08T05:00:00.000Z'],
])test(`V2 computes before DST-transition midnight ${midnight} and expires cache at the actual boundary`,async()=>{
 const f=sessionFixture({lastDate,evaluationAt,extraSessions:[]});
 const h=harness({fixture:f,calendar:f.calendar.sessions.map(s=>({date:s.date,open:'09:30',close:'16:00'}))});
 const first=(await h.run()).value;assert.equal(first.status,'computed');assert.equal(h.calls.length,3);
 assert.equal(new Date([...h.context.cache.values()][0].expires_at).toISOString(),midnight);
 assert.equal(first.freshness.source_as_of,f.calendar.sessions.at(-1).close);assert.equal(first.restrictions.decision_eligible,false);
 h.clock.now+=9999;assert.equal((await h.run()).value.delivery.cache_hit,true);assert.equal(h.calls.length,3);
 h.clock.now+=1;const next=(await h.run()).value;assert.equal(next.status,'computed');assert.equal(next.delivery.cache_hit,false);assert.equal(h.calls.length,6);
 assert.notEqual(next.source.symbol_asof,first.source.symbol_asof);assert.equal(next.freshness.source_as_of,first.freshness.source_as_of);
});
