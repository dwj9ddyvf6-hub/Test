// Trusted bounded on-demand transport: host supplies readBoundedBody/json/shipyardProviderInstant/
// researchResponse/alpacaRateAllowed and trusted SHIPYARD_LIVE_RESEARCH exports:
// APERTURE_EQUITY_SYMBOLS, isScannerEligible, classifyRunnerFreshness,
// buildLiveDiscoveryView. No account/order endpoints, caller URLs, or credentials.
// Alpaca clock uses RFC3339 offsets (including nanoseconds), unlike UTC bar stamps.
const SHIPYARD_APERTURE_CACHE = new Map();
const SHIPYARD_APERTURE_CACHE_MS = 15000;
function shipyardApertureCacheUsable(cached, now) {
  if (!cached || now >= cached.until) return false;
  const expectedBucket = new Date(Math.floor(now / 300000) * 300000).toISOString();
  const expectedMinute = new Date(Math.floor(now / 60000) * 60000 - 60000).toISOString();
  return cached.value.bar_end_at === expectedBucket && cached.value.source?.latest_expected_minute === expectedMinute;
}
function shipyardApertureClockInstant(value) {
  if(typeof value!=='string')return false;
  const match=/^(\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d)(?:\.(\d{1,9}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  if(!match||match[3]==='-00:00')return false;
  const local=Date.parse(match[1]+'.'+(match[2]||'').padEnd(3,'0').slice(0,3)+'Z');
  return Number.isFinite(local)&&new Date(local).toISOString().slice(0,19)===match[1]&&Number.isFinite(Date.parse(value));
}
function shipyardApertureEtParts(value) {
  return Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(value)).map(p=>[p.type,p.value]));
}
function shipyardApertureDate(parts) {return `${parts.year}-${parts.month}-${parts.day}`;}
function shipyardApertureSession(barEndAt,calendar,clock) {
  // Original fetchOfficialSession's pure logic, with validation at acquisition.
  const parts=shipyardApertureEtParts(Date.parse(barEndAt)-1),date=shipyardApertureDate(parts),minute=Number(parts.hour)*60+Number(parts.minute);
  const day=calendar.find(item=>item.date===date);
  if(!day)return {session:'CLOSED',sessionLabel:'Market closed · official calendar',nextTransitionAt:clock.next_open??null,decisionWindowOpen:false};
  const minutes=s=>Number(s.slice(0,2))*60+Number(s.slice(3,5));
  const open=minutes(day.open),close=minutes(day.close);
  const barSession=minute>=240&&minute<open?'PREMARKET':minute>=open&&minute<close?'REGULAR':minute>=close&&minute<1200?'AFTERHOURS':'CLOSED';
  const current=shipyardApertureEtParts(clock.timestamp),currentDate=shipyardApertureDate(current),currentMinute=Number(current.hour)*60+Number(current.minute);
  const session=clock.is_open?'REGULAR':currentDate===date&&currentMinute>=240&&currentMinute<open?'PREMARKET':currentDate===date&&currentMinute>=close&&currentMinute<1200?'AFTERHOURS':'CLOSED';
  const sessionLabel=session==='REGULAR'?`Regular · ${day.open}–${day.close} ET`:session==='PREMARKET'?`Premarket · 04:00–${day.open} ET`:session==='AFTERHOURS'?`After hours · ${day.close}–20:00 ET`:'Market closed · official calendar';
  return {session,sessionLabel,nextTransitionAt:clock.is_open?clock.next_close:clock.next_open??null,decisionWindowOpen:clock.is_open&&barSession==='REGULAR'};
}
function shipyardApertureBar(b) {
  if(!b||!shipyardProviderInstant(b.t)||![b.o,b.h,b.l,b.c].every(x=>Number.isFinite(x)&&x>0)||!Number.isFinite(b.v)||b.v<0||b.h<Math.max(b.o,b.c)||b.l>Math.min(b.o,b.c)||b.h<b.l)throw Error('invalid_market_data');
  return {t:new Date(Date.parse(b.t)).toISOString(),o:b.o,h:b.h,l:b.l,c:b.c,v:b.v};
}
function shipyardApertureSeal(bars,start) {
  const map=new Map(bars.map(b=>[Date.parse(b.t),b]));
  const five=Array.from({length:5},(_,i)=>map.get(start+i*60000));
  if(five.some(b=>!b))return null;
  return {t:new Date(start).toISOString(),o:five[0].o,h:Math.max(...five.map(b=>b.h)),l:Math.min(...five.map(b=>b.l)),c:five[4].c,v:five.reduce((sum,b)=>sum+b.v,0)};
}
async function shipyardApertureScan(request,args,env) {
  const started=Date.now(),base={implementation:SHIPYARD_LIVE_BUILD,schema:'SHIPYARD_APERTURE_SUBSET_V1',producer:'original Aperture core recovered from 6c11b27c11ffedee314fd608fc83853ccf2cb23a',
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,stored_output_retimestamped:false},
    scope:{full_universe_scanned:false,selection_mode:'requested_symbol_bypass_of_global_shortlist',benchmark:'QQQ'},
    identity_note:'Recovered 413-roster implementation, not verified identical to stored September 383-symbol scan'};
  if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).some(k=>k!=='symbol')||typeof args.symbol!=='string'||!SHIPYARD_LIVE_RESEARCH.APERTURE_EQUITY_SYMBOLS.includes(args.symbol.toUpperCase()))return json({...base,status:'invalid_request'},400);
  const symbol=args.symbol.toUpperCase(),names=[...new Set([symbol,'QQQ'])];base.scope.requested_symbol=symbol;base.scope.provided_symbols=names;
  const providerConfigured=typeof env.ALPACA_API_KEY_ID==='string'&&!!env.ALPACA_API_KEY_ID&&typeof env.ALPACA_API_SECRET_KEY==='string'&&!!env.ALPACA_API_SECRET_KEY;
  if(!providerConfigured)return json({...base,status:'unavailable',error:'provider_not_configured'},503);
  const cached=SHIPYARD_APERTURE_CACHE.get(symbol);
  if(shipyardApertureCacheUsable(cached,started))return researchResponse({...cached.value,served_at:new Date(started).toISOString(),cache_hit:true});
  const captures=[];
  const providerGet=async(url,label)=>{
    if(request.signal.aborted)throw Error('cancelled');
    if(!alpacaRateAllowed(request,Date.now()))throw Error('rate_limited');
    const response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':env.ALPACA_API_KEY_ID,'APCA-API-SECRET-KEY':env.ALPACA_API_SECRET_KEY,accept:'application/json'},signal:AbortSignal.any([request.signal,AbortSignal.timeout(8000)]),redirect:'manual'});
    if(!response.ok)throw Error('provider_unavailable');
    const payload=JSON.parse(await readBoundedBody(response,2*1024*1024));
    captures.push({operation:label,received_at:new Date().toISOString()});return payload;
  };
  const end=Math.floor(started/300000)*300000,start=end-300000,expectedMinute=Math.floor(started/60000)*60000-60000;
  const history=async(frame,from,cap)=>{
    const out=Object.fromEntries(names.map(s=>[s,[]])),tokens=new Set();let token=null;
    for(let page=0;page<3;page++) {
      const url=new URL('https://data.alpaca.markets/v2/stocks/bars');
      for(const [k,v] of Object.entries({symbols:names.join(','),timeframe:frame,start:new Date(from).toISOString(),end:new Date(started).toISOString(),adjustment:'all',feed:'iex',sort:'asc',limit:'10000',...(token?{page_token:token}:{})}))url.searchParams.set(k,v);
      const result=await providerGet(url,`history_${frame}_page_${page+1}`);
      if(!result||!result.bars||typeof result.bars!=='object'||Array.isArray(result.bars)||Object.keys(result.bars).some(k=>!names.includes(k)))throw Error('invalid_market_data');
      for(const s of names) {
        const rows=result.bars[s]??[];if(!Array.isArray(rows)||out[s].length+rows.length>cap)throw Error('history_bound_exceeded');
        for(const raw of rows) {
          const b=shipyardApertureBar(raw),t=Date.parse(b.t),previous=out[s].at(-1);
          if(t<from||t>started||(previous&&(t<=Date.parse(previous.t)||(frame==='1Day'&&shipyardApertureDate(shipyardApertureEtParts(t))<=shipyardApertureDate(shipyardApertureEtParts(previous.t)))))||(frame!=='1Day'&&t%(frame==='5Min'?300000:60000)!==0))throw Error('invalid_market_data');
          out[s].push(b);
        }
      }
      token=result.next_page_token;
      if(token==null||token==='')return out;
      if(typeof token!=='string'||token.length>2048||tokens.has(token))throw Error('incomplete_history');tokens.add(token);
    }
    throw Error('incomplete_history');
  };
  try {
    // Three simultaneous data operations maximum; each history is serial paginated.
    const [daily,five,one]=await Promise.all([history('1Day',started-220*86400000,500),history('5Min',started-5*86400000,3000),history('1Min',start-600000,100)]);
    const date=shipyardApertureDate(shipyardApertureEtParts(end-1)),calendarStart=new Date(Date.parse(date+'T12:00:00Z')-8*86400000).toISOString().slice(0,10);
    const latestUrl=new URL('https://data.alpaca.markets/v2/stocks/bars/latest');latestUrl.searchParams.set('symbols',names.join(','));latestUrl.searchParams.set('feed','iex');
    const [latest,calendar,clock]=await Promise.all([providerGet(latestUrl,'latest_1m'),providerGet(`https://paper-api.alpaca.markets/v2/calendar?start=${calendarStart}&end=${date}`,'official_calendar'),providerGet('https://paper-api.alpaca.markets/v2/clock','official_clock')]);
    const finish=Date.now();
    if(request.signal.aborted)throw Error('cancelled');
    if(!Array.isArray(calendar)||calendar.length>9||new Set(calendar.map(d=>d.date)).size!==calendar.length||calendar.some(d=>typeof d.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(d.date)||!Number.isFinite(Date.parse(d.date+'T00:00:00Z'))||new Date(d.date+'T00:00:00Z').toISOString().slice(0,10)!==d.date||d.date<calendarStart||d.date>date||!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(d.open)||!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(d.close)||d.open<'04:00'||d.close>'20:00'||d.open>=d.close)||!clock||typeof clock.is_open!=='boolean'||!shipyardApertureClockInstant(clock.timestamp)||finish-Date.parse(clock.timestamp)>60000||Date.parse(clock.timestamp)-finish>2000||!shipyardApertureClockInstant(clock.next_open)||!shipyardApertureClockInstant(clock.next_close))throw Error('calendar_or_clock_unavailable');
    if(!latest?.bars||typeof latest.bars!=='object'||Array.isArray(latest.bars)||Object.keys(latest.bars).some(k=>!names.includes(k)))throw Error('invalid_market_data');
    const session=shipyardApertureSession(new Date(end).toISOString(),calendar,clock),eligible=new Set(),current=new Set(),sealed=new Set();
    const previousSession=calendar.map(d=>d.date).filter(d=>d<date).sort().at(-1);
    if(!previousSession)throw Error('calendar_or_clock_unavailable');
    const clockParts=shipyardApertureEtParts(clock.timestamp),clockDate=shipyardApertureDate(clockParts),clockMinute=Number(clockParts.hour)*60+Number(clockParts.minute),todaySession=calendar.find(d=>d.date===clockDate);
    const clockMinutes=s=>Number(s.slice(0,2))*60+Number(s.slice(3,5));
    const calendarOpen=Boolean(todaySession && clockMinute>=clockMinutes(todaySession.open) && clockMinute<clockMinutes(todaySession.close));
    if(clockDate!==shipyardApertureDate(shipyardApertureEtParts(finish)) || clock.is_open!==calendarOpen)throw Error('calendar_or_clock_unavailable');
    const todayClosed=Boolean(todaySession && clockMinute>=clockMinutes(todaySession.close));
    const inputs=names.map(name=>{
      const dailyDate=daily[name].length?shipyardApertureDate(shipyardApertureEtParts(daily[name].at(-1).t)):null;
      if((todayClosed && dailyDate!==clockDate) || (dailyDate!==date && dailyDate!==previousSession))throw Error('latest_daily_session_missing');
      if(SHIPYARD_LIVE_RESEARCH.isScannerEligible(daily[name]))eligible.add(name);
      const last=latest.bars[name]?shipyardApertureBar(latest.bars[name]):null;
      if(last&&Date.parse(last.t)>finish)throw Error('invalid_market_data');
      if(last&&Date.parse(last.t)===expectedMinute)current.add(name);
      const completed=five[name].filter(b=>Date.parse(b.t)<=start),seal=shipyardApertureSeal(one[name],start);
      // Require exact local 1m seal; historical5m alone cannot pass current completeness.
      if(seal){const index=completed.findIndex(b=>Date.parse(b.t)===start);if(index>=0)completed[index]=seal;else completed.push(seal);sealed.add(name);}
      const qualityFlags=[...(!eligible.has(name)?['INELIGIBLE_HISTORY']:[]),...(session.session!=='CLOSED'&&!seal?['INCOMPLETE_CURRENT_5M_BAR']:[])];
      return {symbol:name,daily:daily[name],intraday:completed,currentDailyVolume:current.has(name)?last.v:undefined,providerEligible:Boolean(seal),qualityFlags};
    });
    const sourceTimestamps=names.map(name=>latest.bars[name]?.t).filter(value=>typeof value==='string').map(Date.parse).filter(Number.isFinite);
    const sourceAsOfMs=sourceTimestamps.length?Math.max(...sourceTimestamps):null;
    const sourceAsOf=sourceAsOfMs===null?null:new Date(sourceAsOfMs).toISOString();
    const sourceAgeMs=sourceAsOfMs===null?null:finish-sourceAsOfMs;
    const sourceAvailableAt=captures.find(capture=>capture.operation==='latest_1m')?.received_at??null;
    const covered=[...eligible].filter(s=>current.has(s)).length;
    let freshness=SHIPYARD_LIVE_RESEARCH.classifyRunnerFreshness({session:session.session,eligibleCount:eligible.size,coveredCount:covered,deepRequiredCount:names.length,deepCoveredCount:sealed.size,benchmarkCurrent:eligible.has('QQQ')&&current.has('QQQ'),benchmarkSealed:eligible.has('QQQ')&&sealed.has('QQQ')});
    // Provider clocks are re-evaluated after all fetches; a bucket rollover cannot
    // retain LIVE even when original request-start freshness would allow it.
    const bucketAdvanced=Math.floor(finish/300000)*300000!==end;
    const minuteAdvanced=Math.floor(finish/60000)*60000-60000!==expectedMinute;
    if(freshness==='LIVE'&&(bucketAdvanced||finish-end>390000))freshness='STALE';
    else if(freshness==='LIVE'&&minuteAdvanced)freshness='LAGGING';
    const computed=SHIPYARD_LIVE_RESEARCH.buildLiveDiscoveryView({provider:'ALPACA_IEX',feed:'IEX',generatedAt:new Date(finish).toISOString(),barEndAt:new Date(end).toISOString(),session:session.session,sessionLabel:session.sessionLabel,marketNextTransitionAt:session.nextTransitionAt,decisionWindowOpen:session.decisionWindowOpen&&!bucketAdvanced,freshness,elapsedMs:finish-started,symbols:inputs,eligibleCount:eligible.size,coveredCount:covered,unsupportedCount:names.length-eligible.size});
    // Preserve the pinned original core. Normalize only the wrapper's clock and
    // closed-session coverage semantics: a wall-clock bucket is not market data.
    if(session.session==='CLOSED'){
      computed.connection='DEGRADED';
      computed.inputWatermarkAt=sourceAsOf??computed.inputWatermarkAt;
      if(computed.scan?.stages?.[0])computed.scan.stages[0]={...computed.scan.stages[0],label:'Last source bar',value:sourceAsOf??computed.scan.stages[0].value,note:'market closed · no current bucket expected'};
      const closedFlags=new Set(['PARTIAL_PROVIDER_COVERAGE','FULL_PROVIDER_COVERAGE','BENCHMARK_UNAVAILABLE_CURRENT_WATERMARK']);
      computed.quality.flags=computed.quality.flags.filter(flag=>!closedFlags.has(flag));
      computed.quality.flags.push('COVERAGE_NOT_EVALUATED_CLOSED_SESSION','BENCHMARK_NOT_EVALUATED_CLOSED_SESSION');
      computed.quality.missingInputs=computed.quality.missingInputs.filter(flag=>flag!=='INCOMPLETE_CURRENT_5M_BAR'&&flag!=='CURRENT_QQQ_OR_SPY_BAR');
      const freshnessStage=computed.backdrop.find(stage=>stage.label==='Freshness');
      if(freshnessStage)freshnessStage.detail=sourceAsOf??new Date(end).toISOString();
    }
    const decisions=computed.decisions.filter(d=>d.symbol===symbol).map(({ownerAction,...decision})=>decision);
    const decisionAt=new Date(finish).toISOString();
    const output={...base,status:decisions.length?'computed':'no_view',computed_at:decisionAt,decision_at:decisionAt,bar_end_at:new Date(end).toISOString(),expected_bar_end_at:new Date(end).toISOString(),input_watermark_at:computed.inputWatermarkAt,source_as_of:sourceAsOf,freshness,session,connection:computed.connection,quality:computed.quality,source:{provider:'Alpaca Market Data',feed:'iex',history_adjustment:'all',latest_minute_adjustment:'provider_latest_unadjusted_time_and_original_unused_volume_field',source_as_of:sourceAsOf,source_age_ms:sourceAgeMs,source_age_basis:'latest_provider_1m_bar_across_requested_symbols',available_at:sourceAvailableAt,decision_at:decisionAt,evaluation_bucket_end_at:new Date(end).toISOString(),captures,calendar:calendar.map(({date,open,close})=>({date,open,close})),clock_at:clock.timestamp,latest_expected_minute:new Date(expectedMinute).toISOString(),complete_paginated_responses:true},input_captures:inputs.map(s=>({symbol:s.symbol,daily_count:s.daily.length,daily_source_as_of:s.daily.at(-1)?.t??null,completed_intraday_count:s.intraday.length,intraday_source_as_of:s.intraday.at(-1)?.t??null,latest_minute_source_as_of:latest.bars[s.symbol]?.t??null,local_current_bucket_sealed:sealed.has(s.symbol),quality_flags:s.qualityFlags})),scope_coverage:{eligible:eligible.size,current:covered,sealed:sealed.size,total:names.length},warnings:['PARTIAL_UNIVERSE','GLOBAL_SHORTLIST_NOT_REPRODUCED','IEX_NOT_CONSOLIDATED_VOLUME','HEURISTIC_PERFORMANCE_NOT_INDEPENDENTLY_VALIDATED','TRANSPORT_SEAL_STRICTER_THAN_ORIGINAL_HISTORICAL_5M_FALLBACK','ORIGINAL_CURRENT_DAILY_VOLUME_FIELD_IS_LATEST_CURRENT_MINUTE_VOLUME',...(bucketAdvanced?['BUCKET_ADVANCED_DURING_ACQUISITION']:[])],decisions,served_at:new Date(finish).toISOString(),cache_hit:false};
    if(SHIPYARD_APERTURE_CACHE.size>50)SHIPYARD_APERTURE_CACHE.clear();
    SHIPYARD_APERTURE_CACHE.set(symbol,{value:output,until:finish+SHIPYARD_APERTURE_CACHE_MS});
    return researchResponse(output);
  }catch(error){if(error?.message==='rate_limited')return json({...base,status:'unavailable',error:'rate_limited',retry_after_seconds:60},429);const allowed=['provider_unavailable','invalid_market_data','history_bound_exceeded','incomplete_history','calendar_or_clock_unavailable','latest_daily_session_missing','cancelled'];return json({...base,status:request.signal.aborted?'cancelled':'unavailable',error:allowed.includes(error?.message)?error.message:'aperture_computation_unavailable',computed_at:new Date().toISOString()},request.signal.aborted?408:503);}
}
