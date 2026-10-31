// Bounded fixed-panel daily-price acquisition for the NEW FE07/FE10 policies.
// No caller datasets, arbitrary symbol fan-out, account endpoints, or order access.
const SHIPYARD_FE0710_CACHE=new Map();
const SHIPYARD_FE0710_DATE=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const shipyardFE0710Date=ms=>SHIPYARD_FE0710_DATE.format(new Date(ms));
function shipyardFE0710Delivery(value,now,cacheHit,cachedAt){
  const sourceAge=(now-Date.parse(value.freshness.source_as_of))/1000;
  const receipts=[value.source.calendar.capture,...value.source.captures];
  return {cache_hit:cacheHit,served_at:new Date(now).toISOString(),cached_at:cachedAt,source_receipts_retimestamped:false,
    source_age_seconds_at_delivery:sourceAge,original_catalog_age_acceptable_at_delivery:sourceAge<=172800,
    last_capture_age_seconds_at_delivery:(now-Math.max(...receipts.map(r=>Date.parse(r.received_at))))/1000};
}
async function shipyardForecastFE0710(engineId,request,env){
  const started=Date.now(),isFE07=engineId==='FE07',feature=SHIPYARD_FE0710_FEATURES;
  const policy=isFE07?feature.FE07_LEADLAG_POLICY:feature.FE10_REGIME_POLICY;
  const policyHash=isFE07?feature.FE07_LEADLAG_POLICY_SHA256:feature.FE10_REGIME_POLICY_SHA256;
  const symbols=isFE07?['SPY','QQQ']:['SPY','QQQ','IWM'];
  const base={schema:`SHIPYARD_${engineId}_SOURCE_FORECAST_V1`,engine_id:engineId,feature_origin:'provider_capture_new_policy',feature_policy:policy,feature_policy_sha256:policyHash,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false}};
  if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
  const today=shipyardFE0710Date(started),cacheKey=`${engineId}:${policyHash}:iex:split:1Day:USD:${symbols.join(',')}:${today}`;
  const key=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
  if(typeof key!=='string'||!key||typeof secret!=='string'||!secret)return json({...base,status:'unavailable',error:'market_data_credentials_unavailable'},503);
  const cached=SHIPYARD_FE0710_CACHE.get(cacheKey);
  if(cached&&started>=Date.parse(cached.cached_at)&&started<cached.expires_at)
    return researchResponse({...cached.value,delivery:shipyardFE0710Delivery(cached.value,started,true,cached.cached_at)});
  SHIPYARD_FE0710_CACHE.delete(cacheKey);
  const requestBound=1+symbols.length*2;
  for(let i=0;i<requestBound;i++)if(!alpacaRateAllowed(request,started))return json({...base,status:'unavailable',error:'rate_limited'},429);
  const deadline=started+25000,captures=[];
  const get=async(url,operation,subject,maxBytes)=>{
    if(request.signal.aborted)throw Error('cancelled');if(Date.now()>=deadline)throw Error('acquisition_deadline_exceeded');
    const sent=new Date().toISOString(),response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret,accept:'application/json'},
      redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(Math.max(1,Math.min(8000,deadline-Date.now())))])});
    const safeURL=new URL(url);if(safeURL.searchParams.has('page_token'))safeURL.searchParams.set('page_token','[continuation]');
    const receipt={operation,subject,request_started_at:sent,http_response_received_at:new Date().toISOString(),received_at:null,response_sha256:null,request_url:safeURL.toString(),http_status:response.status};
    captures.push(receipt);
    if(!response.ok)throw Error(response.status===401?'market_data_authentication_failed':response.status===403?'requested_feed_not_entitled':response.status===429?'provider_rate_limited':'provider_unavailable');
    const body=await readBoundedBody(response,maxBytes);receipt.received_at=new Date().toISOString();
    receipt.response_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body))),b=>b.toString(16).padStart(2,'0')).join('');
    receipt.hash_serialization='UTF-8 re-encoding of decoded response text';
    let payload;try{payload=JSON.parse(body);}catch{throw Error('provider_schema_invalid');}
    return {payload,receipt};
  };
  try{
    const from=new Date(Date.parse(today+'T12:00:00Z')-800*86400000).toISOString().slice(0,10);
    const calendarUrl=new URL('https://paper-api.alpaca.markets/v2/calendar');calendarUrl.searchParams.set('start',from);calendarUrl.searchParams.set('end',today);
    const calendar=await get(calendarUrl,'official_calendar','US_EQUITY',262144),calendarRows=calendar.payload;
    if(!Array.isArray(calendarRows)||calendarRows.length>801)throw Error('invalid_calendar');
    let previous='';const sessions=calendarRows.map(row=>{
      if(!row||!shipyardCalendarDate(row.date)||row.date<from||row.date>today||row.date<=previous||typeof row.open!=='string'||typeof row.close!=='string'
        ||row.open<'04:00'||row.close>'20:00'||row.open>=row.close)throw Error('invalid_calendar');
      previous=row.date;const open=shipyardCalendarBoundary(row.date,row.open),close=shipyardCalendarBoundary(row.date,row.close);
      if(Date.parse(close)<=Date.parse(open)||Date.parse(close)-Date.parse(open)>390*60000)throw Error('invalid_calendar');return {date:row.date,open,close};
    });
    const eligible=sessions.filter(s=>Date.parse(s.close)+900000<=started);if(eligible.length<505)throw Error('insufficient_completed_sessions');
    const selected=eligible.slice(-505),start=shipyardCalendarBoundary(selected[0].date,'00:00'),end=selected.at(-1).close;
    const getSeries=async symbol=>{
      const bars=[],seen=new Set();let token=null,complete=false;
      for(let page=1;page<=2;page++){
        const url=new URL(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/bars`);
        const query={timeframe:'1Day',start,end:new Date(Date.parse(end)-1).toISOString(),feed:'iex',adjustment:'split',currency:'USD',asof:today,sort:'asc',limit:'1000',...(token?{page_token:token}:{})};
        for(const [k,v] of Object.entries(query))url.searchParams.set(k,v);
        const result=await get(url,`history_${symbol}_1Day_page_${page}`,symbol,524288),payload=result.payload;
        if(!payload||payload.symbol!==undefined&&payload.symbol!==symbol||!Array.isArray(payload.bars)||!Object.hasOwn(payload,'next_page_token')
          ||payload.bars.length>1000||bars.length+payload.bars.length>1000)throw Error('provider_schema_invalid');
        result.receipt.request_url=url.origin+url.pathname+'?'+new URLSearchParams({...query,...(token?{page_token:'[continuation]'}:{})});
        result.receipt.provider_rows=payload.bars.length;bars.push(...payload.bars);token=payload.next_page_token;result.receipt.has_next_page=token!=null&&token!=='';
        if(token==null||token===''){complete=true;break;}
        if(typeof token!=='string'||!/^[\x21-\x7e]{1,2048}$/.test(token)||seen.has(token))throw Error('invalid_provider_pagination');seen.add(token);
      }
      if(!complete)throw Error('provider_pagination_bound_exceeded');return bars;
    };
    // Fixed, ordered, deduplicated panel only. The official calendar and every series must complete.
    const bySymbol={};for(const symbol of symbols)bySymbol[symbol]=await getSeries(symbol);
    const finished=Date.now();if(request.signal.aborted)throw Error('cancelled');if(finished>=deadline)throw Error('acquisition_deadline_exceeded');
    const latestEligible=sessions.filter(s=>Date.parse(s.close)+900000<=finished).at(-1)?.date;
    if(shipyardFE0710Date(finished)!==today||latestEligible!==selected.at(-1).date)throw Error('session_boundary_advanced');
    const value=feature[isFE07?'buildFE07SourceForecast':'buildFE10SourceForecast']({engine_id:engineId,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',
      symbol_asof:today,evaluation_at:new Date(finished).toISOString(),calendar:{sessions,received_at:calendar.receipt.received_at,
        requested_range:{start_date:from,end_date:today},complete_provider_response:true},calendar_capture:calendar.receipt,bars_by_symbol:bySymbol,
      requested_window:{start,end,end_exclusive:true},captures:captures.filter(c=>c.operation.startsWith('history_')),pagination_complete:true});
    const computed=Date.now();if(request.signal.aborted)throw Error('cancelled');if(computed>=deadline)throw Error('acquisition_deadline_exceeded');
    if(shipyardFE0710Date(computed)!==today||sessions.filter(s=>Date.parse(s.close)+900000<=computed).at(-1)?.date!==selected.at(-1).date)throw Error('session_boundary_advanced');
    value.acquisition={calendar_capture:calendar.receipt,request_count:captures.length,request_bound:requestBound,max_rows_per_symbol:1000,
      max_response_bytes_per_request:524288,elapsed_ms:computed-started,elapsed_budget_ms:25000};value.computed_at=new Date(computed).toISOString();
    if(value.status!=='computed')return researchResponse({...value,evaluation_at:new Date(finished).toISOString(),source_receipts:captures});
    if(computed-Date.parse(value.freshness.source_as_of)>604800000)throw Error('extended_closure_or_calendar_staleness_unverified');
    const sourceAsOf=Date.parse(value.freshness.source_as_of),tomorrow=new Date(Date.parse(today+'T12:00:00Z')+86400000).toISOString().slice(0,10);
    const nextBoundary=sessions.map(s=>Date.parse(s.close)+900000).find(t=>t>finished)??Infinity;
    const midnight=Date.parse(shipyardCalendarBoundary(tomorrow,'00:00')),extended=sourceAsOf+604800000;
    const expires=Math.min(finished+60000,nextBoundary,midnight,extended);
    for(const [k,v] of SHIPYARD_FE0710_CACHE)if(v.expires_at<=finished)SHIPYARD_FE0710_CACHE.delete(k);
    if(SHIPYARD_FE0710_CACHE.size>=8)SHIPYARD_FE0710_CACHE.delete(SHIPYARD_FE0710_CACHE.keys().next().value);
    SHIPYARD_FE0710_CACHE.set(cacheKey,{value,expires_at:expires,cached_at:new Date(computed).toISOString()});
    return researchResponse({...value,delivery:shipyardFE0710Delivery(value,computed,false,null)});
  }catch(error){
    const allowed=['cancelled','acquisition_deadline_exceeded','market_data_authentication_failed','requested_feed_not_entitled','provider_rate_limited','provider_unavailable',
      'provider_schema_invalid','invalid_calendar','insufficient_completed_sessions','invalid_provider_pagination','provider_pagination_bound_exceeded','session_boundary_advanced',
      'extended_closure_or_calendar_staleness_unverified'];
    const code=request.signal.aborted?'cancelled':Date.now()>=deadline?'acquisition_deadline_exceeded':error?.name==='TimeoutError'?'source_request_timeout'
      :allowed.includes(error?.message)?error.message:'source_acquisition_failed';
    return json({...base,status:code==='cancelled'?'cancelled':'unavailable',error:code,source_receipts:captures,computed_at:new Date().toISOString()},code==='cancelled'?408:503);
  }
}
async function shipyardForecastFE07(request,args,env){return shipyardForecastFE0710('FE07',request,env);}
async function shipyardForecastFE10(request,args,env){return shipyardForecastFE0710('FE10',request,env);}
