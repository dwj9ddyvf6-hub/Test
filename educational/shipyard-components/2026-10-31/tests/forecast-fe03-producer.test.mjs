import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto,createHash} from 'node:crypto';
import * as features from '../research/forecast-features/fe03-breakout-v1.mjs';
import {fixture,boundary} from './fixtures/fe03-synthetic.mjs';

const code=readFileSync(new URL('../worker/exchange-calendar.js',import.meta.url),'utf8')+'\n'
 +readFileSync(new URL('../worker/forecast-fe03.js',import.meta.url),'utf8')
 +'\nglobalThis.run=shipyardForecastFE03;globalThis.cache=SHIPYARD_FE03_CACHE;globalThis.boundary=(date,time)=>shipyardCalendarBoundary(date,time);';
const sha=value=>createHash('sha256').update(value).digest('hex');
function localTime(utc){return new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(utc));}
function harness(options={}){
 const f=options.fixture||fixture(),clock={now:Date.parse(options.at||f.evaluation_at)},calls=[],rates=[],bodyLimits=[];
 class ClockDate extends Date {constructor(...args){super(...(args.length?args:[clock.now]));}static now(){return clock.now;}}
 const calendar=options.calendar||f.calendar.sessions.map(session=>({date:session.date,open:'09:30',close:localTime(session.close)}));
 let page=0;
 const context={Date:ClockDate,Intl,URL,URLSearchParams,AbortSignal,TextEncoder,crypto:webcrypto,
  SHIPYARD_FORECAST_FE03_FEATURES:{...features,buildFE03SourceForecast:input=>{const result=features.buildFE03SourceForecast(input);clock.now+=options.computeAdvance||0;return result;}},
  json:(value,status=200)=>({value,status}),researchResponse:value=>({value,status:200}),
  alpacaRateAllowed:()=>{rates.push(1);return typeof options.rate==='function'?options.rate(rates.length):options.rate!==false;},
  readBoundedBody:async(response,max)=>{bodyLimits.push(max);const body=await response.text();if(new TextEncoder().encode(body).length>max)throw Error('body_too_large');return body;},
  fetch:async(url,init)=>{
   const u=new URL(url);calls.push({url:u,init});
   assert.equal(init.method,'GET');assert.equal(init.redirect,'manual');assert.ok(!/accounts|orders/.test(u.toString()));
   if(options.advance)clock.now+=options.advance;
   if(options.fetch)return options.fetch(u,init,calls.length,{f,clock,calendar});
   if(options.http)return new Response('{}',{status:options.http});
   if(u.pathname.endsWith('/calendar'))return new Response(JSON.stringify(calendar),{headers:{'content-type':'application/json'}});
   const requested=new URL(u),rows=f.bars.filter(bar=>Date.parse(bar.t)>=Date.parse(requested.searchParams.get('start'))&&Date.parse(bar.t)<=Date.parse(requested.searchParams.get('end')));
   const payload=options.pages?.[page]||{symbol:decodeURIComponent(u.pathname.split('/').at(-2)),bars:rows,next_page_token:null};page++;
   return new Response(JSON.stringify(payload),{headers:{'content-type':'application/json'}});
  }};
 vm.createContext(context);vm.runInContext(code,context);
 const req=new Request('https://owner.test/api/research/forecast/from-bars');
 return {run:(args={symbol:'SPY'},env={ALPACA_API_KEY_ID:'fixture-key',ALPACA_API_SECRET_KEY:'fixture-secret'},request=req)=>context.run(request,args,env),calls,rates,bodyLimits,clock,context,f,calendar};
}

test('bounded provider acquisition produces source-bound FE03 only from completed IEX daily bars',async()=>{
 const h=harness(),result=await h.run(),r=result.value;
 assert.equal(result.status,200);assert.equal(r.status,'computed');assert.equal(r.engine_id,'FE03');assert.equal(r.feature_policy.id,'FE03_DAILY_BREAKOUT_ACCEPTANCE_MATURED_V1');
 assert.equal(h.calls.length,2);assert.deepEqual(h.rates,[1,1,1]);assert.deepEqual(h.bodyLimits,[262144,524288]);
 assert.equal(r.acquisition.request_count,2);assert.equal(r.acquisition.request_bound,3);assert.equal(r.coverage.complete_sessions,505);
 const history=new URL(h.calls[1].url);assert.equal(history.searchParams.get('timeframe'),'1Day');assert.equal(history.searchParams.get('feed'),'iex');
 assert.equal(history.searchParams.get('adjustment'),'split');assert.equal(history.searchParams.get('currency'),'USD');assert.equal(history.searchParams.get('limit'),'1000');
 assert.equal(history.searchParams.get('asof'),'2026-10-30');assert.equal(r.restrictions.decision_eligible,false);assert.equal(r.restrictions.order_submission_enabled,false);
 assert.equal(r.freshness.source_as_of,r.source.calendar.selected_session_grid.rows.at(-1)[2]);
 assert.equal(r.acquisition.calendar_capture.response_sha256,sha(JSON.stringify(h.calendar)));
 assert.equal(r.source.captures[0].response_sha256,sha(JSON.stringify({symbol:'SPY',bars:h.f.bars,next_page_token:null})));
 assert.equal(JSON.stringify(r).includes('fixture-key'),false);assert.equal(JSON.stringify(r).includes('fixture-secret'),false);
 assert.ok(new TextEncoder().encode(JSON.stringify(r)).length<48*1024,`response bytes: ${new TextEncoder().encode(JSON.stringify(r)).length}`);
});

test('bounded page continuation fixes the query and redacts tokens',async()=>{
 const f=fixture(),pages=[{symbol:'SPY',bars:f.bars.slice(0,300),next_page_token:'cursor-secret'},
  {symbol:'SPY',bars:f.bars.slice(300),next_page_token:null}],h=harness({pages}),r=(await h.run()).value;
 assert.equal(r.status,'computed');assert.equal(h.calls.length,3);const first=new URL(h.calls[1].url),second=new URL(h.calls[2].url);
 assert.equal(second.searchParams.get('page_token'),'cursor-secret');second.searchParams.delete('page_token');assert.equal(first.toString(),second.toString());
 assert.equal(r.source.captures[1].request_url.includes('cursor-secret'),false);assert.equal(r.source.captures[1].has_next_page,false);
 assert.equal(r.acquisition.request_count,3);
});

test('legitimate no_setup and acceptance_not_mature stay distinct from source failure and never score',async()=>{
 for(const [options,status]of [[{fixture:fixture({candidate:false})},'no_setup'],[{fixture:fixture({candidateAge:2})},'acceptance_not_mature'],
  [{fixture:fixture({invalidated:true})},'level_invalidated'],[{fixture:fixture({matureEpisodes:10})},'insufficient_mature_episode_sample']]){
  const h=harness(options),response=await h.run();assert.equal(response.status,200);assert.equal(response.value.status,status);
  assert.equal('features' in response.value,false);assert.equal('calculator_result' in response.value,false);assert.equal(h.calls.length,2);
 }
});

test('provider/auth/rate/arguments failures are explicit, bounded, and never cached',async()=>{
 for(const [http,error]of [[401,'market_data_authentication_failed'],[403,'requested_feed_not_entitled'],[429,'provider_rate_limited'],[500,'provider_unavailable']]){
  const h=harness({http}),r=await h.run();assert.equal(r.status,503);assert.equal(r.value.error,error);assert.equal(h.calls.length,1);assert.equal(h.context.cache.size,0);
 }
 let h=harness();assert.equal((await h.run({symbol:'SPY'},{})).value.error,'market_data_credentials_unavailable');assert.equal(h.calls.length,0);
 assert.equal((await h.run({symbol:'SPY',feed:'sip'})).status,400);assert.equal(h.calls.length,0);
 h=harness({rate:count=>count<3});assert.equal((await h.run()).status,429);assert.equal(h.calls.length,0);assert.equal(h.rates.length,3);
});

test('provider schema, incomplete bars and malformed calendars fail closed without a score',async()=>{
 for(const [options,error]of [
  [{calendar:[]},'insufficient_completed_sessions'],
  [{pages:[{symbol:'QQQ',bars:[],next_page_token:null}]},'provider_schema_invalid'],
  [{pages:[{bars:fixture().bars}]},'provider_schema_invalid'],
  [{pages:[{bars:[],next_page_token:'a'},{bars:[],next_page_token:'b'}]},'provider_pagination_bound_exceeded'],
  [{calendar:[{date:'2026-02-30',open:'09:30',close:'16:00'}]},'invalid_calendar'],
 ]){
  const h=harness(options),r=await h.run();assert.equal(r.value.status,'unavailable');assert.equal(r.value.error,error);assert.equal(h.context.cache.size,0);
 }
 const f=fixture(),pages=[{symbol:'SPY',bars:f.bars.slice(1),next_page_token:null}],h=harness({pages}),r=await h.run();
 assert.equal(r.value.error,'missing_daily_session_bar');assert.equal('calculator_result' in r.value,false);assert.equal(h.context.cache.size,0);
});

test('credential removal, cancellation, timeout, body bound and provider failure are not cached',async()=>{
 const h=harness(),first=await h.run();assert.equal(first.value.status,'computed');
 assert.equal((await h.run({symbol:'SPY'},{})).value.error,'market_data_credentials_unavailable');
 const controller=new AbortController();controller.abort();const cancelled=await h.run({symbol:'SPY'},undefined,new Request('https://owner.test/',{signal:controller.signal}));assert.equal(cancelled.value.status,'cancelled');
 assert.equal(h.context.cache.size,1);
 let b=harness({fetch:()=>{throw Error('network fixture-secret');}}),bad=await b.run();assert.equal(bad.value.error,'source_acquisition_failed');assert.equal(JSON.stringify(bad).includes('fixture-secret'),false);
 b=harness({fetch:()=>{const error=Error('fixture timeout');error.name='TimeoutError';throw error;}});bad=await b.run();assert.equal(bad.value.error,'source_request_timeout');
 b=harness({fetch:(url,init,n)=>n===1?new Response('x'.repeat(262145)):new Response('{}')});bad=await b.run();assert.equal(bad.value.status,'unavailable');assert.equal(bad.value.error,'source_acquisition_failed');
});

test('cache preserves original clocks, expires at the official session boundary, and refreshes Monday without age promotion',async()=>{
 const f=fixture(),monday='2026-11-02',level=Math.max(...f._rows.slice(481,501).map(row=>row.h)),close=f._rows[501].c;
 f.calendar.sessions.push({date:monday,open:boundary(monday,'09:30'),close:boundary(monday,'16:00')});
 f._rows.push({date:monday,o:close,h:close*1.001,l:level,c:close,v:104});
 f.bars.push({t:boundary(monday,'00:00'),o:close,h:close*1.001,l:level,c:close,v:104});
 const h=harness({fixture:f,at:'2026-11-02T21:14:30.000Z'}),first=(await h.run()).value;
 assert.equal(first.status,'computed');assert.equal(first.freshness.source_session_date,'2026-10-30');assert.equal(first.freshness.original_catalog_age_acceptable,false);
 assert.equal(first.restrictions.decision_eligible,false);assert.equal(first.episode.cutoff_session,'2026-10-30');assert.equal(h.calls.length,2);
 h.clock.now=Date.parse('2026-11-02T21:14:59.999Z');assert.equal((await h.run()).value.delivery.cache_hit,true);assert.equal(h.calls.length,2);
 h.clock.now=Date.parse('2026-11-02T21:15:00.000Z');const next=(await h.run()).value;
 assert.equal(next.status,'computed');assert.equal(next.freshness.source_session_date,'2026-11-02');assert.equal(next.freshness.original_catalog_age_acceptable,true);
 assert.equal(next.restrictions.decision_eligible,false);assert.equal(h.calls.length,4);assert.notEqual(next.freshness.source_as_of,first.freshness.source_as_of);
});
