import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import * as fe04 from '../research/forecast-features/fe04-gap-decomposition-v1.mjs';
import * as fe09 from '../research/forecast-features/fe09-jump-tail-v1.mjs';
import * as fe12 from '../research/forecast-features/fe12-top-of-book-v3.mjs';
import {makeFE04Fixture,makeFE09Fixture} from './fixtures/fe04-fe09-fe12-synthetic.mjs';
import {makeFE12V3Fixture} from './fixtures/fe12-v3-synthetic.mjs';

const exchange=readFileSync(new URL('../worker/exchange-calendar.js',import.meta.url),'utf8');
const readers={
 FE04:readFileSync(new URL('../worker/forecast-fe04.js',import.meta.url),'utf8'),
 FE09:readFileSync(new URL('../worker/forecast-fe09.js',import.meta.url),'utf8'),
 FE12:readFileSync(new URL('../worker/forecast-fe12.js',import.meta.url),'utf8'),
};
const clone=x=>JSON.parse(JSON.stringify(x));

function harness(engine,options={}){
 const f=options.fixture||(engine==='FE04'?makeFE04Fixture():engine==='FE09'?makeFE09Fixture():makeFE12V3Fixture());
 const clock={now:Date.parse(options.at||f.evaluation_at)},calls=[],rates=[],limits=[],eventCalls=[];
 class ClockDate extends Date{constructor(...args){super(...(args.length?args:[clock.now]));}static now(){return clock.now;}}
 const sessions=(f.calendar.sessions||[]).map(s=>({date:s.date,open:new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(s.open)),close:new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(s.close))}));
 const context={Date:ClockDate,Intl,URL,URLSearchParams,AbortSignal,AbortController,TextEncoder,crypto:webcrypto,setTimeout,clearTimeout,
  SHIPYARD_FORECAST_FE04_FEATURES:fe04,SHIPYARD_FORECAST_FE09_FEATURES:fe09,SHIPYARD_FORECAST_FE12_FEATURES:fe12,
  json:(value,status=200)=>({value,status}),researchResponse:value=>({value,status:200}),
  alpacaRateAllowed:()=>{rates.push(1);return options.rate!==false;},
  readBoundedBody:async(response,max)=>{limits.push(max);const text=await response.text();if(new TextEncoder().encode(text).length>max)throw Error('body_size_exceeded');return text;},
  shipyardOfficialEvents:async(_request,{month})=>{eventCalls.push(month);if(options.eventHandler)return options.eventHandler(_request,month,{f,clock,eventCalls});if(options.eventError)return new Response('{}',{status:503});const row=f.macro_events.months.find(m=>m.month===month);return Response.json(row?{schema:'SHIPYARD_OFFICIAL_EVENTS_V1',month,...row}:{schema:'SHIPYARD_OFFICIAL_EVENTS_V1',month,status:'partial',received_at:new Date(clock.now).toISOString(),sources:[],events:[]});},
  fetch:async(url,init)=>{
   const parsed=new URL(url);calls.push({url:parsed.toString(),init});
   assert.equal(init.method,'GET');assert.equal(init.redirect,'manual');assert.ok(!/accounts|orders/.test(parsed.toString()));
   if(options.advance)clock.now+=options.advance;
   if(options.fetch)return options.fetch(parsed,init,calls.length,{f,clock,sessions});
   if(options.http)return new Response('{}',{status:options.http});
   if(parsed.pathname==='/v2/calendar')return Response.json(options.calendar??sessions);
   if(parsed.pathname.endsWith('/quotes')){
    if(options.quoteHttp&&calls.length===options.quoteHttp.at)return new Response('{}',{status:options.quoteHttp.status});
    const window=f.quote_windows.find(w=>w.start===parsed.searchParams.get('start'));
    if(!window)throw Error('fixture_quote_window_missing');
    const rows=options.quotePages?.shift()??{symbol:f.symbol,quotes:window.quotes,next_page_token:null};return Response.json(rows);
   }
   if(parsed.pathname.endsWith('/bars')){
    if(engine==='FE12'&&options.barPages)return Response.json(options.barPages.shift());
    const bars=engine==='FE04'?f.bars_by_symbol[decodeURIComponent(parsed.pathname.split('/').at(-2))]:f.bars;
    if(engine==='FE09')return Response.json(options.barPayload??{symbol:f.symbol,bars,next_page_token:null});
    return Response.json({symbol:engine==='FE04'?decodeURIComponent(parsed.pathname.split('/').at(-2)):f.symbol,bars:options.barPayload?.bars??bars,next_page_token:options.barPayload?.next_page_token??null});
   }
   throw Error('unexpected_provider_url');
  }};
 vm.createContext(context);vm.runInContext(exchange+'\n'+readers[engine]+`\nglobalThis.run=shipyardForecast${engine};` ,context);
 const request=new Request('https://owner.test/api/research/forecast/from-bars');
 return {run:(args={symbol:f.symbol},env={ALPACA_API_KEY_ID:'fixture-key',ALPACA_API_SECRET_KEY:'fixture-secret'},req=request)=>context.run(req,args,env),calls,rates,limits,eventCalls,clock,context,f,sessions,request};
}

test('FE04 end-to-end source reader retains only selected bars and computes via NEW policy',async()=>{
 const h=harness('FE04'),r=await h.run();assert.equal(r.status,200);assert.equal(r.value.status,'computed');
 assert.equal(h.calls.length,4);assert.equal(h.rates.length,19);assert.equal(r.value.acquisition.request_count,4);
 assert.equal(r.value.source.feed,'iex');assert.equal(r.value.source.adjustment,'split');assert.equal(r.value.features.fair_gap_z===r.value.features.gap_z,false);
 assert.equal(r.value.source_receipts,undefined);assert.equal(r.value.delivery.cache_hit,false);
 for(const row of h.calls.slice(1)){const u=new URL(row.url);assert.equal(u.searchParams.get('feed'),'iex');assert.equal(u.searchParams.get('adjustment'),'split');assert.equal(u.searchParams.get('timeframe'),'1Min');}
 assert.ok(h.limits.includes(2097152));assert.ok(JSON.stringify(r).length<65536);assert.equal(JSON.stringify(r).includes('fixture-secret'),false);
});
test('FE04 follows provider continuation pages within reducer/page ceiling and rejects truncation',async()=>{
 const f=makeFE04Fixture(),q=f.bars_by_symbol.SPY,first=q.slice(0,Math.ceil(q.length/2)),second=q.slice(Math.ceil(q.length/2));
 const h=harness('FE04',{fetch:async(url,init,n,{sessions})=>{
  if(url.pathname==='/v2/calendar')return Response.json(sessions);
  const symbol=decodeURIComponent(url.pathname.split('/').at(-2)),page=Number(url.searchParams.get('page_token')||0);
  const rows=f.bars_by_symbol[symbol],split=Math.ceil(rows.length/2);return Response.json({symbol,bars:page?rows.slice(split):rows.slice(0,split),next_page_token:page?null:'1'});
 }});const r=await h.run();assert.equal(r.value.status,'computed');assert.equal(h.calls.length,7);assert.equal(r.value.source.captures.filter(c=>c.operation.includes('page_2')).length,3);
 const bad=harness('FE04',{fetch:async(url,init,n,{sessions})=>{if(url.pathname==='/v2/calendar')return Response.json(sessions);const symbol=decodeURIComponent(url.pathname.split('/').at(-2)),page=Number(url.searchParams.get('page_token')||0),rows=f.bars_by_symbol[symbol],size=Math.ceil(rows.length/6);return Response.json({symbol,bars:rows.slice(page*size,(page+1)*size),next_page_token:String(page+1)});}});
 const failed=await bad.run();assert.equal(failed.value.error,'provider_page_budget_exceeded');
});
test('FE04 rejects unentitled IEX feed, request widening and missing credentials without fallback',async()=>{
 let h=harness('FE04',{http:403});assert.equal((await h.run()).value.error,'requested_feed_not_entitled');assert.equal(h.calls.length,1);
 h=harness('FE04');assert.equal((await h.run({symbol:'SPY',feed:'sip'})).status,400);assert.equal(h.calls.length,0);
 assert.equal((await h.run({symbol:'SPY'},{})).value.error,'market_data_credentials_unavailable');assert.equal(h.calls.length,0);
});

test('FE09 end-to-end source reader uses exact completed sessions and scoped official calendar',async()=>{
 const h=harness('FE09'),r=await h.run();assert.equal(r.status,200);assert.equal(r.value.status,'computed');assert.equal(h.calls.length,2);assert.equal(h.rates.length,2);
 assert.deepEqual(h.eventCalls,['2026-11']);assert.equal(r.value.measurements.macro_event_date_precision,'official-session-date; unknown intraday time preserved and not inferred');
 assert.equal(r.value.features.event_density,0.5);assert.equal(r.value.source.captures.length,2);
 const bars=new URL(h.calls[1].url);assert.equal(bars.searchParams.get('adjustment'),'split');assert.equal(bars.searchParams.get('feed'),'iex');assert.equal(bars.searchParams.get('timeframe'),'5Min');
});

test('FE09 route returns a typed unsupported open and stops before bars or event reads',async()=>{
 const base=makeFE09Fixture(),shifted=base.calendar.sessions.map(s=>({date:s.date,open:'10:00',close:'16:30'})),h=harness('FE09',{calendar:shifted}),r=await h.run();
 assert.equal(r.value.status,'unavailable');assert.equal(r.value.error,'unsupported_session_open');assert.equal(h.calls.length,1);assert.equal(h.eventCalls.length,0);
});


test('FE09 counts scoped event HTTP attempts separately and shares the full deadline across both month readers',async()=>{
 const fixture=makeFE09Fixture({currentDate:'2026-10-27'}),h=harness('FE09',{fixture}),r=await h.run();assert.equal(r.value.status,'computed',r.value.error);assert.deepEqual(h.eventCalls,['2026-10','2026-11']);assert.equal(r.value.acquisition.request_count,2);assert.equal(r.value.acquisition.request_count_scope.startsWith('Alpaca calendar/bar'),true);assert.equal(r.value.acquisition.event_source_http_request_count,6);assert.equal(r.value.acquisition.event_source_http_request_count_if_fresh,6);assert.equal(r.value.acquisition.event_source_http_request_bound,22);assert.equal(r.value.acquisition.event_source_http_response_bytes_bound,11534336);assert.equal(r.value.acquisition.event_source_http_response_bytes_bound_total,11534336);assert.ok(r.value.acquisition.event_month_summary_response_bytes>0);assert.equal(r.value.acquisition.event_month_summary_response_bytes_bound,4194304);assert.ok(r.value.acquisition.direct_market_response_bytes>0);assert.ok(r.value.acquisition.response_bytes_scope.includes('direct Alpaca calendar/bar'));assert.equal(JSON.stringify(r.value.acquisition.event_source_http_request_count_by_month.map(m=>m.count)),'[3,3]');
 const cached=harness('FE09',{fixture,eventHandler:async(_request,month,{f})=>{const row=f.macro_events.months.find(m=>m.month===month);return Response.json({schema:'SHIPYARD_OFFICIAL_EVENTS_V1',month,cache_hit:true,...row});}}),cachedResult=await cached.run();assert.equal(cachedResult.value.status,'computed',cachedResult.value.error);assert.equal(cachedResult.value.acquisition.event_source_http_request_count,0);assert.equal(cachedResult.value.acquisition.event_source_http_request_count_if_fresh,6);assert.equal(cachedResult.value.acquisition.event_source_http_request_count_by_month.every(m=>m.cache_hit),true);
 const fallback=harness('FE09',{fixture,eventHandler:async(_request,month,{f})=>{const row=f.macro_events.months.find(m=>m.month===month),sources=clone(row.sources),bls=sources.find(s=>s.source==='BLS');bls.fallback_attempt={url:`https://www.bls.gov/schedule/${month.slice(0,4)}/${month.slice(5,7)}_sched_list.htm`,status:'unavailable'};bls.fred_fallback={release_pages:Array.from({length:7},()=>({status:'parsed'}))};return Response.json({schema:'SHIPYARD_OFFICIAL_EVENTS_V1',month,...row,sources});}}),fallbackResult=await fallback.run();assert.equal(fallbackResult.value.status,'computed',fallbackResult.value.error);assert.equal(fallbackResult.value.acquisition.event_source_http_request_count,22);assert.equal(fallbackResult.value.acquisition.event_source_http_request_bound,22);assert.equal(JSON.stringify(fallbackResult.value.acquisition.event_source_http_request_count_by_month.map(m=>m.count)),'[11,11]');
 const overBudget=harness('FE09',{fixture,eventHandler:async(_request,month,{f})=>{const row=f.macro_events.months.find(m=>m.month===month),sources=clone(row.sources),bls=sources.find(s=>s.source==='BLS');bls.fallback_attempt={status:'unavailable'};bls.fred_fallback={release_pages:Array.from({length:8},()=>({status:'parsed'}))};return Response.json({schema:'SHIPYARD_OFFICIAL_EVENTS_V1',month,...row,sources});}}),overResult=await overBudget.run();assert.equal(overResult.value.status,'unavailable');assert.equal(overResult.value.error,'event_source_http_budget_exceeded');
 const signals=[],deadlineHarness=harness('FE09',{fixture,eventHandler:async(request,month,{f,clock})=>{signals.push(request.signal);clock.now+=13000;const row=f.macro_events.months.find(m=>m.month===month);return Response.json({schema:'SHIPYARD_OFFICIAL_EVENTS_V1',month,...row});}}),expired=await deadlineHarness.run();assert.equal(expired.value.status,'unavailable');assert.equal(expired.value.error,'acquisition_deadline_exceeded');assert.deepEqual(deadlineHarness.eventCalls,['2026-10','2026-11']);assert.equal(signals.length,2);assert.equal(signals[0],signals[1]);assert.notEqual(signals[0],deadlineHarness.request.signal);assert.equal(signals[0].aborted,true);
});

test('FE09 does not treat HTTP success, an event zero, or an incomplete family scope as coverage',async()=>{
 const h=harness('FE09',{eventError:true}),r=await h.run();assert.notEqual(r.value.status,'computed');assert.equal(h.calls.length,2);
 const partial=harness('FE09');partial.f.macro_events.months[0].sources[1].scope_complete=false;
 const result=await partial.run();assert.equal(result.value.status,'unavailable');assert.equal(result.value.error,'macro_event_source_scope_incomplete');
});
test('FE09 provider cursor is never silently accepted and split-adjusted bars are required',async()=>{
 const h=harness('FE09',{barPayload:{symbol:'SPY',bars:makeFE09Fixture().bars,next_page_token:'next'}}),r=await h.run();assert.equal(r.value.error,'provider_pagination_bound_exceeded');assert.equal(h.calls.length,2);
 const missing=harness('FE09',{http:403}),b=await missing.run();assert.equal(b.value.error,'requested_feed_not_entitled');assert.equal(missing.calls.length,1);
});

test('FE12 V3 acquires 17 explicit-IEX snapshots at the latest completed intraday RTH bucket',async()=>{
 const h=harness('FE12'),r=await h.run();assert.equal(r.status,200,r.value.error);assert.equal(r.value.status,'computed',JSON.stringify(r.value));assert.equal(h.calls.length,19);assert.equal(h.rates.length,20);
 assert.equal(r.value.source.quote_feed,'iex');assert.equal(r.value.source.quote_size_unit,'shares');assert.equal(r.value.acquisition.quote_snapshot_count,17);assert.equal(r.value.coverage.received_quote_snapshots,17);assert.equal(r.value.coverage.provider_cursor_present_snapshots,0);assert.equal(r.value.source.quote_selection.includes('latest IEX TOPS point in the five seconds before the latest completed RTH five-minute bucket'),true);assert.equal(r.value.source.bucket.index,29);assert.equal(r.value.source.bucket.elapsed_rth_minutes,150);
 assert.equal(r.value.coverage.prior_baseline_sessions,16);assert.equal(h.calls.filter(x=>new URL(x.url).pathname.endsWith('/quotes')).length,17);
 const quoteCalls=h.calls.filter(x=>new URL(x.url).pathname.endsWith('/quotes'));assert.ok(quoteCalls.every(x=>{const u=new URL(x.url);return u.searchParams.get('feed')==='iex'&&u.searchParams.get('sort')==='desc'&&u.searchParams.get('limit')==='1'&&Date.parse(u.searchParams.get('end'))-Date.parse(u.searchParams.get('start'))===5000;}));
 assert.equal(JSON.stringify(r).includes('fixture-secret'),false);
});
test('FE12 IEX 403 and unknown/mixed size-unit conditions abstain without SIP fallback',async()=>{
 const h=harness('FE12',{quoteHttp:{at:2,status:403}}),r=await h.run();assert.equal(r.value.error,'requested_feed_not_entitled');assert.equal(h.calls.length,6);assert.ok(h.calls.filter(x=>new URL(x.url).pathname.endsWith('/quotes')).every(x=>new URL(x.url).searchParams.get('feed')==='iex'));
 const bad=harness('FE12'),result=await bad.run();assert.equal(result.value.source.quote_size_unit,'shares');
 const truncated=harness('FE12',{barPages:[{symbol:'SPY',bars:makeFE12V3Fixture().bars,next_page_token:'first'},{symbol:'SPY',bars:[],next_page_token:'second'}]}),incomplete=await truncated.run();assert.equal(incomplete.value.error,'bar_pagination_bound_exceeded');assert.equal(truncated.calls.length,20);
});
test('all three readers reject unsupported universe, rate denial, and cancellation before source calls',async()=>{
 for(const engine of ['FE04','FE09','FE12']){
  let h=harness(engine);assert.equal((await h.run({symbol:'AAPL'})).status,400);assert.equal(h.calls.length,0);
  h=harness(engine,{rate:false});assert.equal((await h.run()).status,429);assert.equal(h.calls.length,0);
  h=harness(engine);const ac=new AbortController();ac.abort();assert.equal((await h.run(undefined,undefined,new Request('https://owner.test/',{signal:ac.signal}))).status,408);assert.equal(h.calls.length,0);
 }
});

test('FE12 V3 two-page cold start uses exactly20 provider reservations and then abstains at saturation',async()=>{
 const fixture=makeFE12V3Fixture();fixture.symbol='QQQ';const split=Math.floor(fixture.bars.length/2),first=fixture.bars.slice(0,split),second=fixture.bars.slice(split),h=harness('FE12',{fixture,fetch:async(url,_init,n,{f,sessions})=>{
  if(url.pathname==='/v2/calendar')return Response.json(sessions);
  if(url.pathname.endsWith('/quotes')){const w=f.quote_windows.find(x=>x.start===url.searchParams.get('start'));return Response.json({symbol:f.symbol,quotes:w.quotes,next_page_token:'older-point'});}
  if(url.pathname.endsWith('/bars'))return url.searchParams.has('page_token')?Response.json({symbol:f.symbol,bars:second,next_page_token:null}):Response.json({symbol:f.symbol,bars:first,next_page_token:'bars-page-2'});
  throw Error('unexpected provider URL');
 }}),r=await h.run({symbol:'QQQ'});
 assert.equal(r.value.status,'computed',JSON.stringify(r.value));assert.equal(r.value.acquisition.request_count,20);assert.equal(r.value.acquisition.request_bound,20);assert.equal(r.value.source.bar_pages.length,2);assert.equal(r.value.coverage.prior_baseline_sessions,16);assert.equal(r.value.coverage.provider_cursor_present_snapshots,17);assert.equal(h.calls.length,20);assert.equal(h.rates.length,20);assert.equal(h.calls.filter(x=>new URL(x.url).pathname.endsWith('/quotes')).length,17);assert.equal(h.calls.filter(x=>new URL(x.url).pathname.endsWith('/bars')).length,2);
});
test('FE12 V3 pre-open bucket warmup and cross-bucket acquisition do not return old snapshots as current',async()=>{
 const f=makeFE12V3Fixture(),open=Date.parse(f.calendar.sessions.at(-1).open),warm=harness('FE12',{at:new Date(open+4*60000).toISOString()}),w=await warm.run();assert.equal(w.value.error,'intraday_warmup');assert.equal(warm.calls.length,0);
 const boundary=harness('FE12',{fetch:async(url,_init,n,{f,clock,sessions})=>{if(url.pathname==='/v2/calendar')return Response.json(sessions);if(url.pathname.endsWith('/quotes')){const q=f.quote_windows.find(x=>x.start===url.searchParams.get('start'));return Response.json({symbol:f.symbol,quotes:q.quotes,next_page_token:null});}if(url.pathname.endsWith('/bars')){clock.now+=300000;return Response.json({symbol:f.symbol,bars:f.bars,next_page_token:null});}throw Error('unexpected URL');}}),b=await boundary.run();assert.equal(b.value.error,'bucket_advanced_during_acquisition');
});
