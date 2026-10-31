import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
import * as core from '../research/live-aperture/lib/live-scan-engine.ts';import * as coverage from '../research/live-aperture/services/aperture-runner/src/coverage.ts';import {APERTURE_EQUITY_SYMBOLS} from '../research/live-aperture/lib/aperture-universe.ts';
const source=fs.readFileSync(new URL('../worker/aperture-producer.js',import.meta.url),'utf8');
const fixture=JSON.parse(fs.readFileSync(new URL('../research/live-aperture/synthetic-fixture.json',import.meta.url)));
const base=Date.parse('2026-10-29T14:30:30Z');
const dailyDates=[];let day=Date.parse('2026-10-28T04:00:00Z');while(dailyDates.length<fixture.scan.symbols[0].daily.length){if(![0,6].includes(new Date(day).getUTCDay()))dailyDates.unshift(new Date(day).toISOString());day-=86400000;}
const currentDaily=fixture.scan.symbols[0].daily.map((b,i)=>({...b,t:dailyDates[i]}));
const weekendDates=[];day=Date.parse('2026-10-30T04:00:00Z');while(weekendDates.length<fixture.scan.symbols[0].daily.length){if(![0,6].includes(new Date(day).getUTCDay()))weekendDates.unshift(new Date(day).toISOString());day-=86400000;}
const weekendDaily=fixture.scan.symbols[0].daily.map((b,i)=>({...b,t:weekendDates[i]}));
async function run(mode='ok',rateBudget=Infinity,repeatAfterMs=null) {
 let now=mode==='weekend'?Date.parse('2026-10-31T04:42:00Z'):base,calls=0,captured=null,reservations=0;
 class FakeDate extends Date {constructor(...args){super(...(args.length?args:[now]));}static now(){return now;}}
 const ctx={SHIPYARD_LIVE_BUILD:{test:true},URL,Intl,Math,Map,Set,Array,Date:FakeDate,AbortSignal,console,
  SHIPYARD_LIVE_RESEARCH:{...coverage,APERTURE_EQUITY_SYMBOLS,buildLiveDiscoveryView(input){captured=input;return core.buildLiveDiscoveryView(input);}},
  shipyardProviderInstant:v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(v)&&Number.isFinite(Date.parse(v)),
  alpacaRateAllowed:()=>++reservations<=rateBudget,json:(data,status=200)=>({data,status}),researchResponse:data=>({data,status:200}),readBoundedBody:async r=>JSON.stringify(r.payload),
  fetch:async value=>{calls++;const url=new URL(value);let payload;
   if(url.pathname.endsWith('/calendar'))payload=mode==='weekend'?[{date:'2026-10-30',open:'09:30',close:'16:00'},{date:'2026-10-29',open:'09:30',close:'16:00'}]:[{date:'2026-10-28',open:'09:30',close:'16:00'},{date:'2026-10-29',open:mode==='bad-calendar'?'09:99':'09:30',close:'16:00'}];
   else if(url.pathname.endsWith('/clock')){if(mode==='rollover')now=base+300000;if(mode==='afterclose')now=Date.parse('2026-10-29T20:30:00Z');payload={timestamp:new Date(now+(mode==='futureclock'?3000:0)).toISOString(),is_open:!['afterclose','badclock','weekend'].includes(mode),next_open:mode==='weekend'?'2026-11-02T14:30:00Z':'2026-10-30T13:30:00Z',next_close:mode==='weekend'?'2026-10-30T20:00:00Z':'2026-10-29T20:00:00Z'};if(mode==='offsetclock')payload={...payload,timestamp:'2026-10-29T10:30:30.000000000-04:00',next_open:'2026-10-30T09:30:00-04:00',next_close:'2026-10-29T16:00:00-04:00'};}
   else if(url.pathname.endsWith('/latest'))payload={bars:Object.fromEntries(['NVDA','QQQ'].map(s=>[s,{t:mode==='weekend'?(s==='NVDA'?'2026-10-30T20:33:00Z':'2026-10-30T20:54:00Z'):'2026-10-29T14:29:00Z',o:110,h:111,l:109,c:110,v:1234}]))};
   else {
    const frame=url.searchParams.get('timeframe');assert.equal(url.searchParams.get('adjustment'),'all');assert.equal(url.searchParams.get('feed'),'iex');
    let rows=frame==='1Day'?(mode==='stale-daily'?fixture.scan.symbols[0].daily:mode==='weekend'?weekendDaily:currentDaily):frame==='5Min'?fixture.scan.symbols[0].intraday:mode==='weekend'?[]:Array.from({length:15},(_,i)=>({t:new Date(Date.parse('2026-10-29T14:15:00Z')+i*60000).toISOString(),o:110,h:111,l:109,c:110,v:1000}));
    if(mode==='bad-row'&&frame==='1Day')rows=rows.map((b,i)=>i?b:{...b,h:1});
    if(mode==='missing-minute'&&frame==='1Min')rows=rows.slice(0,-1);
    if(mode==='pages'||mode==='repeated')rows=[];
    payload={bars:{NVDA:rows,QQQ:rows},next_page_token:mode==='repeated'?'same':mode==='pages'?String(calls):null};
   }
   return {ok:true,payload};
  }};
 vm.createContext(ctx);vm.runInContext(source,ctx);ctx.req={signal:new AbortController().signal};ctx.args={symbol:'NVDA'};ctx.env={ALPACA_API_KEY_ID:'TEST',ALPACA_API_SECRET_KEY:'TEST'};
 const result=await vm.runInContext('shipyardApertureScan(req,args,env)',ctx);let repeated=null;if(repeatAfterMs!==null){now+=repeatAfterMs;repeated=await vm.runInContext('shipyardApertureScan(req,args,env)',ctx);}return {result,repeated,captured,calls,reservations};
}
const ok=await run();assert.equal(ok.result.status,200,JSON.stringify(ok.result));assert.ok(ok.captured);assert.equal(ok.captured.symbols[0].currentDailyVolume,1234);
assert.deepEqual(JSON.parse(JSON.stringify(ok.result.data.decisions)),core.buildLiveDiscoveryView(ok.captured).decisions.filter(d=>d.symbol==='NVDA').map(({ownerAction,...d})=>d));
assert.equal(ok.result.data.scope.full_universe_scanned,false);
const exactBudget=await run('ok',6);assert.equal(exactBudget.result.status,200);assert.equal(exactBudget.calls,6);assert.equal(exactBudget.reservations,6);
const exhausted=await run('ok',5);assert.equal(exhausted.result.status,429);assert.equal(exhausted.result.data.error,'rate_limited');assert.equal(exhausted.calls,5);assert.equal(exhausted.reservations,6);
const cached=await run('ok',Infinity,0);assert.equal(cached.result.status,200);assert.equal(cached.repeated.status,200);assert.equal(cached.calls,6);assert.equal(cached.reservations,6);assert.equal(cached.repeated.data.cache_hit,true);assert.equal(cached.repeated.data.computed_at,cached.result.data.computed_at);assert.equal(cached.repeated.data.source.latest_expected_minute,cached.result.data.source.latest_expected_minute);assert.ok(cached.repeated.data.served_at);
const expired=await run('ok',Infinity,16000);assert.equal(expired.result.status,200);assert.equal(expired.repeated.status,200);assert.equal(expired.calls,12);assert.equal(expired.repeated.data.cache_hit,false);assert.notEqual(expired.repeated.data.computed_at,expired.result.data.computed_at);
for(const mode of ['pages','repeated','bad-calendar','bad-row','stale-daily','afterclose','futureclock','badclock']){const r=await run(mode);assert.equal(r.result.status,503,mode);if(mode==='pages'||mode==='repeated')assert.ok(r.calls<=9);}
const rolled=await run('rollover');assert.notEqual(rolled.result.data.freshness,'LIVE');assert.equal(rolled.captured.decisionWindowOpen,false);
const missing=await run('missing-minute');assert.equal(missing.result.data.status,'no_view');assert.equal(missing.result.data.scope_coverage.sealed,0);
const weekend=await run('weekend');assert.equal(weekend.result.status,200);assert.equal(weekend.result.data.session.session,'CLOSED');assert.equal(weekend.result.data.freshness,'CLOSED');assert.equal(weekend.result.data.source_as_of,'2026-10-30T20:54:00.000Z');assert.equal(weekend.result.data.source.source_age_ms,Date.parse('2026-10-31T04:42:00Z')-Date.parse('2026-10-30T20:54:00Z'));assert.equal(weekend.result.data.expected_bar_end_at,'2026-10-31T04:40:00.000Z');assert(!weekend.result.data.quality.missingInputs.includes('INCOMPLETE_CURRENT_5M_BAR'));assert(!weekend.result.data.quality.missingInputs.includes('CURRENT_QQQ_OR_SPY_BAR'));assert(weekend.result.data.quality.flags.includes('COVERAGE_NOT_EVALUATED_CLOSED_SESSION'));assert(!weekend.result.data.quality.flags.includes('PARTIAL_PROVIDER_COVERAGE'));
console.log('PASS worker draft: exact constructed-input decision parity, original minute-volume mapping, page caps/repeated tokens, bad calendar/OHLCV, finish rollover, strict minute seal, subset scope');

assert.equal((await run('offsetclock')).result.status,200);
const clockContext={Date,Number};vm.createContext(clockContext);vm.runInContext(source,clockContext);
for(const value of ['2022-04-28T14:07:45.485843765-04:00','2026-10-29T00:01:00+14:00','2026-10-29T23:59:59-12:00','2026-10-29T19:00:00Z'])assert.equal(clockContext.shipyardApertureClockInstant(value),true,value);
for(const value of ['2026-02-30T19:00:00-04:00','2026-10-29T24:00:00Z','2026-10-29T19:00:00+24:00','2026-10-29T19:00:00+04:60','2026-10-29T19:00:00.1234567890Z','2026-10-29T19:00:00','2026-10-29T19:00:00-00:00'])assert.equal(clockContext.shipyardApertureClockInstant(value),false,value);
