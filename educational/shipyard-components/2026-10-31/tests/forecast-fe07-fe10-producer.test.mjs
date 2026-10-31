import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import * as features from '../research/forecast-features/fe07-fe10-v1.mjs';
import {sourceFixture} from './fixtures/fe07-fe10-synthetic.mjs';

const toolCode=readFileSync(new URL('../worker/forecast-tools.js',import.meta.url),'utf8')
  .replace('__SHIPYARD_FORECAST_BUILD__','{}').replace('__SHIPYARD_FORECAST_INPUT_READINESS__','{}');
const code=toolCode+'\n'+readFileSync(new URL('../worker/exchange-calendar.js',import.meta.url),'utf8')+'\n'
  +readFileSync(new URL('../worker/forecast-fe07-fe10.js',import.meta.url),'utf8')+'\n'
  +readFileSync(new URL('../worker/source-research-routes.js',import.meta.url),'utf8')
  +'\nglobalThis.bindings=SHIPYARD_FORECAST_SOURCE_BINDINGS;globalThis.runRoute=shipyardSourceResearchRoute;globalThis.cache=SHIPYARD_FE0710_CACHE;';
function harness(engineId,options={}){
  const f=sourceFixture(engineId),clock={now:Date.parse(f.evaluation_at)},calls=[],rates=[],bodyLimits=[],pageCounts={};
  class ClockDate extends Date{constructor(...a){super(...(a.length?a:[clock.now]));}static now(){return clock.now;}}
  const calendar=f.calendar.sessions.map(s=>({date:s.date,open:'09:30',close:'16:00'})).concat({date:'2026-10-29',open:'09:30',close:'16:00'});
  const context={Date:ClockDate,Intl,URL,URLSearchParams,AbortSignal,Request,Response,TextEncoder,crypto:webcrypto,SHIPYARD_FE0710_FEATURES:features,
    SHIPYARD_FORECAST_TREND_FEATURES:{},SHIPYARD_FORECAST_PAIRED_FEATURES:{},SHIPYARD_FORECAST_FE03_FEATURES:{},SHIPYARD_FORECAST_FEATURES:{},
    json:(value,status=200)=>({value,status}),researchResponse:value=>new TextEncoder().encode(JSON.stringify(value)).length>49152
      ?{value:{schema:'SHIPYARD_RESEARCH_OUTPUT_V1',status:'payload_too_large'},status:413}:{value,status:200},
    alpacaRateAllowed:()=>{rates.push(1);return typeof options.rate==='function'?options.rate(rates.length):options.rate!==false;},
    readBoundedBody:async(response,max)=>{bodyLimits.push(max);const text=await response.text();if(new TextEncoder().encode(text).length>max)throw Error('body_too_large');return text;},
    fetch:async(url,init)=>{
      const u=new URL(url);calls.push({url:u,init});if(options.advance)clock.now+=options.advance;
      assert.equal(init.method,'GET');assert.equal(init.redirect,'manual');assert.ok(!/accounts|orders/.test(u.toString()));
      if(options.fetch)return options.fetch(u,init,calls.length,{f,clock,calendar,pageCounts});
      if(options.http)return new Response('{}',{status:options.http});
      if(u.pathname.endsWith('/calendar'))return Response.json(options.calendar||calendar);
      const symbol=decodeURIComponent(u.pathname.split('/').at(-2)),index=pageCounts[symbol]||0;pageCounts[symbol]=index+1;
      const custom=options.pages?.[symbol]?.[index];if(custom)return Response.json({symbol,...custom});
      const rows=f.bars_by_symbol[symbol]?.filter(b=>Date.parse(b.t)>=Date.parse(u.searchParams.get('start'))&&Date.parse(b.t)<=Date.parse(u.searchParams.get('end')))??[];
      return Response.json({symbol,bars:rows,next_page_token:null});
    }};
  vm.createContext(context);vm.runInContext(code,context);
  return {context,f,calls,rates,bodyLimits,calendar,clock,cache:context.cache,
    run:(query=`/api/research/forecast/from-bars?engine_id=${engineId}`,env={ALPACA_API_KEY_ID:'fixture-key',ALPACA_API_SECRET_KEY:'fixture-secret'},request=new Request('https://owner.test'+query))=>context.runRoute(request,env)};
}

for(const [engineId,symbols,bound] of [['FE07',['SPY','QQQ'],5],['FE10',['SPY','QQQ','IWM'],7]]){
  test(`${engineId} native fixed-panel route dispatches a bounded official-calendar/member-price bundle`,async()=>{
    const h=harness(engineId),result=await h.run();assert.equal(result.status,200);assert.equal(result.value.status,'computed',result.value.error);
    assert.equal(result.value.engine_id,engineId);assert.equal(h.calls.length,symbols.length+1);assert.equal(h.rates.length,bound);
    assert.deepEqual(h.calls.filter(c=>c.url.pathname.includes('/bars')).map(c=>c.url.pathname.split('/').at(-2)).sort(),symbols.slice().sort());
    assert.equal(result.value.coverage.complete_sessions,505);assert.equal(result.value.source.captures.length,symbols.length);
    assert.equal(result.value.acquisition.request_bound,bound);assert.deepEqual(result.value.source.universe.symbols||[result.value.source.universe.leader,result.value.source.universe.follower],symbols);
    assert.ok(new TextEncoder().encode(JSON.stringify(result.value)).length<49152,'bounded source response exceeds48KiB');
    for(const receipt of [result.value.acquisition.calendar_capture,...result.value.source.captures]){
      assert.equal(receipt.http_status,200);assert.match(receipt.response_sha256,/^[a-f0-9]{64}$/);
      assert.ok(Date.parse(receipt.request_started_at)<=Date.parse(receipt.http_response_received_at));
      assert.ok(Date.parse(receipt.http_response_received_at)<=Date.parse(receipt.received_at));
    }
    assert.equal(JSON.stringify(result).includes('fixture-secret'),false);assert.equal(JSON.stringify(result).includes('fixture-key'),false);
  });
  test(`${engineId} route rejects extra caller-universe arguments, bounds and failed credentials before provider requests`,async()=>{
    let h=harness(engineId),bad=await h.run(`/api/research/forecast/from-bars?engine_id=${engineId}&symbol=NVDA`);
    assert.equal(bad.status,400);assert.equal(h.calls.length,0);
    h=harness(engineId);const missing=await h.run(undefined,{});assert.equal(missing.value.error,'market_data_credentials_unavailable');assert.equal(h.calls.length,0);
    h=harness(engineId,{rate:n=>n<([5,7][engineId==='FE07'?0:1])});const limited=await h.run();assert.equal(limited.status,429);assert.equal(h.calls.length,0);assert.equal(h.rates.length,bound);
  });
}

test('one bounded page continuation is validated; provider failures never yield/cache partial scores',async()=>{
  const sample=sourceFixture('FE07'),bars={SPY:sample.bars_by_symbol.SPY,QQQ:sample.bars_by_symbol.QQQ};
  const pages=Object.fromEntries(Object.entries(bars).map(([s,rows])=>[s,[{bars:rows.slice(0,300),next_page_token:'cursor'}, {bars:rows.slice(300),next_page_token:null}]]));
  const h=harness('FE07',{pages}),response=await h.run();assert.equal(response.value.status,'computed');assert.equal(h.calls.length,5);
  for(const symbol of ['SPY','QQQ']){const calls=h.calls.filter(c=>c.url.pathname.includes(`/stocks/${symbol}/`));assert.equal(calls.length,2);
    assert.equal(calls[1].url.searchParams.get('page_token'),'cursor');
    assert.equal(response.value.source.captures.find(c=>c.operation===`history_${symbol}_1Day_page_2`).request_url.includes('cursor'),false);}
  let failed=harness('FE10',{http:403}),denied=await failed.run();assert.equal(denied.status,503);assert.equal(denied.value.error,'requested_feed_not_entitled');
  assert.equal(failed.cache.size,0);
});

test('successful cache preserves original observation and receipts; deadline/page bounds abstain',async()=>{
  const h=harness('FE10'),first=await h.run();assert.equal(first.value.status,'computed');const calls=h.calls.length,receipts=first.value.source.captures;
  h.clock.now+=1000;const cached=await h.run();assert.equal(cached.value.delivery.cache_hit,true);assert.equal(h.calls.length,calls);
  assert.deepEqual(cached.value.source.captures,receipts);assert.equal(cached.value.evaluation_at,first.value.evaluation_at);
  assert.equal(cached.value.delivery.source_receipts_retimestamped,false);assert.notEqual(cached.value.delivery.served_at,first.value.delivery.served_at);
  let timed=harness('FE07',{advance:26000}),timeout=await timed.run();assert.equal(timeout.value.error,'acquisition_deadline_exceeded');assert.equal(timed.calls.length,1);
  const loop=harness('FE07',{pages:{SPY:[{bars:[],next_page_token:'a'},{bars:[],next_page_token:'b'}]}}),partial=await loop.run();
  assert.equal(partial.value.error,'provider_pagination_bound_exceeded');assert.equal(loop.cache.size,0);
});
