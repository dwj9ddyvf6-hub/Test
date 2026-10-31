// Bounded paired daily-price acquisition for a NEW FE02 residual feature policy.
// Uses only the existing Alpaca IEX/calendar helpers. No accounts or orders.
const SHIPYARD_FE02_CACHE=new Map();
const SHIPYARD_FE02_DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
function shipyardFE02Date(ms){return SHIPYARD_FE02_DATE_FORMAT.format(new Date(ms));}

async function shipyardForecastFE02(request,args,env){
  const started=Date.now(),policy=SHIPYARD_FORECAST_PAIRED_FEATURES.FE02_PAIRED_POLICY;
  const base={schema:'SHIPYARD_FE02_SOURCE_FORECAST_V1',engine_id:'FE02',feature_origin:'provider_capture_new_policy',feature_policy:policy,
    feature_policy_sha256:SHIPYARD_FORECAST_PAIRED_FEATURES.FE02_PAIRED_POLICY_SHA256,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,
      calibrated_probability:null,historical_point_in_time_claim:false}};
  if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).length!==1||!Object.hasOwn(args,'symbol')
    ||typeof args.symbol!=='string'||!/^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$/.test(args.symbol)||args.symbol.toUpperCase()==='SPY')
    return json({...base,status:'invalid',error:'invalid_arguments'},400);
  const symbol=args.symbol.toUpperCase(),cacheKey=`${policy.id}:iex:split:1Day:${symbol}:SPY`;
  base.symbol=symbol;base.benchmark_symbol='SPY';
  if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
  const key=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
  if(typeof key!=='string'||!key||typeof secret!=='string'||!secret)return json({...base,status:'unavailable',error:'market_data_credentials_unavailable'},503);
  const cached=SHIPYARD_FE02_CACHE.get(cacheKey);
  if(cached&&started>=Date.parse(cached.cached_at)&&started<cached.expires_at)
    return researchResponse({...cached.value,delivery:{cache_hit:true,served_at:new Date(started).toISOString(),cached_at:cached.cached_at,source_receipts_retimestamped:false}});
  SHIPYARD_FE02_CACHE.delete(cacheKey);
  // One calendar plus at most two pages each for the requested ticker and SPY.
  for(let index=0;index<5;index++)if(!alpacaRateAllowed(request,started))return json({...base,status:'unavailable',error:'rate_limited'},429);
  const deadline=started+25000,captures=[];
  const get=async(url,operation,subject,maxBytes)=>{
    if(request.signal.aborted)throw Error('cancelled');
    if(Date.now()>=deadline)throw Error('acquisition_deadline_exceeded');
    const requestStarted=new Date().toISOString();
    const response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret,accept:'application/json'},
      redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(Math.max(1,Math.min(8000,deadline-Date.now())))])});
    const safeURL=new URL(url);if(safeURL.searchParams.has('page_token'))safeURL.searchParams.set('page_token','[continuation]');
    const receipt={operation,subject,request_started_at:requestStarted,http_response_received_at:new Date().toISOString(),received_at:null,
      response_sha256:null,request_url:safeURL.toString(),http_status:response.status};
    captures.push(receipt);
    if(!response.ok)throw Error(response.status===401?'market_data_authentication_failed':response.status===403?'requested_feed_not_entitled':response.status===429?'provider_rate_limited':'provider_unavailable');
    const body=await readBoundedBody(response,maxBytes);receipt.received_at=new Date().toISOString();
    receipt.response_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body))),byte=>byte.toString(16).padStart(2,'0')).join('');
    receipt.hash_serialization='UTF-8 re-encoding of decoded response text';
    let payload;try{payload=JSON.parse(body);}catch{throw Error('provider_schema_invalid');}
    return {payload,receipt};
  };
  try{
    const today=shipyardFE02Date(started),from=new Date(Date.parse(today+'T12:00:00Z')-800*86400000).toISOString().slice(0,10);
    const calendarUrl=new URL('https://paper-api.alpaca.markets/v2/calendar');calendarUrl.searchParams.set('start',from);calendarUrl.searchParams.set('end',today);
    const calendarCapture=await get(calendarUrl,'official_calendar','US_EQUITY',262144),calendarRows=calendarCapture.payload;
    if(!Array.isArray(calendarRows)||calendarRows.length>801)throw Error('invalid_calendar');
    let previous='';const sessions=calendarRows.map(row=>{
      if(!row||!shipyardCalendarDate(row.date)||row.date<from||row.date>today||row.date<=previous||typeof row.open!=='string'||typeof row.close!=='string'
        ||row.open<'04:00'||row.close>'20:00'||row.open>=row.close)throw Error('invalid_calendar');
      previous=row.date;
      const open=shipyardCalendarBoundary(row.date,row.open),close=shipyardCalendarBoundary(row.date,row.close);
      if(Date.parse(close)<=Date.parse(open)||(Date.parse(close)-Date.parse(open))>390*60000)throw Error('invalid_calendar');
      return {date:row.date,open,close};
    });
    const eligible=sessions.filter(session=>Date.parse(session.close)+policy.completion_delay_ms<=started);
    if(eligible.length<505)throw Error('insufficient_completed_sessions');
    const selected=eligible.slice(-505),start=shipyardCalendarBoundary(selected[0].date,'00:00'),end=selected.at(-1).close;
    const getSeries=async subject=>{
      const bars=[],seen=new Set();let token=null,complete=false;
      for(let page=1;page<=2;page++){
        const url=new URL(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(subject)}/bars`);
        const query={timeframe:'1Day',start,end:new Date(Date.parse(end)-1).toISOString(),feed:'iex',adjustment:'split',currency:'USD',asof:today,
          sort:'asc',limit:'1000',...(token?{page_token:token}:{})};
        for(const [name,value] of Object.entries(query))url.searchParams.set(name,value);
        const result=await get(url,`history_${subject}_1Day_page_${page}`,subject,512*1024),payload=result.payload;
        if(!payload||payload.symbol!==undefined&&payload.symbol!==subject||!Array.isArray(payload.bars)
          ||!Object.hasOwn(payload,'next_page_token')||payload.bars.length>1000||bars.length+payload.bars.length>1000)throw Error('provider_schema_invalid');
        result.receipt.request_url=url.origin+url.pathname+'?'+new URLSearchParams({...query,...(token?{page_token:'[continuation]'}:{})});
        result.receipt.provider_rows=payload.bars.length;bars.push(...payload.bars);token=payload.next_page_token;
        result.receipt.has_next_page=token!=null&&token!=='';
        if(token==null||token===''){complete=true;break;}
        if(typeof token!=='string'||!/^[\x21-\x7e]{1,2048}$/.test(token)||seen.has(token))throw Error('invalid_provider_pagination');
        seen.add(token);
      }
      if(!complete)throw Error('provider_pagination_bound_exceeded');
      return bars;
    };
    // The sole market pairing is the requested ticker with the declared SPY benchmark.
    const [symbolBars,spyBars]=await Promise.all([getSeries(symbol),getSeries('SPY')]);
    const finished=Date.now();if(request.signal.aborted)throw Error('cancelled');if(finished>=deadline)throw Error('acquisition_deadline_exceeded');
    const latestEligible=sessions.filter(session=>Date.parse(session.close)+policy.completion_delay_ms<=finished).at(-1)?.date;
    if(shipyardFE02Date(finished)!==today||latestEligible!==selected.at(-1).date)throw Error('session_boundary_advanced');
    const receipts=captures.filter(receipt=>receipt.operation.startsWith('history_'));
    const value=SHIPYARD_FORECAST_PAIRED_FEATURES.buildFE02SourceForecast({symbol,benchmark_symbol:'SPY',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',
      symbol_asof:today,evaluation_at:new Date(finished).toISOString(),calendar:{sessions,received_at:calendarCapture.receipt.received_at,
        requested_range:{start_date:from,end_date:today},complete_provider_response:true},calendar_capture:calendarCapture.receipt,bars_by_symbol:{[symbol]:symbolBars,SPY:spyBars},
      requested_window:{start,end,end_exclusive:true},captures:receipts,pagination_complete:true});
    const computed=Date.now();if(request.signal.aborted)throw Error('cancelled');if(computed>=deadline)throw Error('acquisition_deadline_exceeded');
    if(shipyardFE02Date(computed)!==today||sessions.filter(session=>Date.parse(session.close)+policy.completion_delay_ms<=computed).at(-1)?.date!==selected.at(-1).date)
      throw Error('session_boundary_advanced');
    value.acquisition={calendar_capture:calendarCapture.receipt,request_count:captures.length,request_bound:5,max_rows_per_symbol:1000,
      max_response_bytes_per_request:512*1024,elapsed_ms:computed-started,elapsed_budget_ms:25000};
    value.computed_at=new Date(computed).toISOString();
    if(value.status!=='computed')return researchResponse({...value,symbol,benchmark_symbol:'SPY',evaluation_at:new Date(finished).toISOString(),source_receipts:captures});
    const sourceAsOf=Date.parse(value.freshness.source_as_of),ageBoundary=sourceAsOf+policy.freshness_max_age_seconds*1000;
    const nextBoundary=sessions.map(session=>Date.parse(session.close)+policy.completion_delay_ms).find(boundary=>boundary>finished)??Infinity;
    const expires=Math.min(finished+60000,nextBoundary,ageBoundary>=finished?ageBoundary:Infinity);
    for(const [cacheKeyExisting,item] of SHIPYARD_FE02_CACHE)if(item.expires_at<=finished)SHIPYARD_FE02_CACHE.delete(cacheKeyExisting);
    if(SHIPYARD_FE02_CACHE.size>=8)SHIPYARD_FE02_CACHE.delete(SHIPYARD_FE02_CACHE.keys().next().value);
    SHIPYARD_FE02_CACHE.set(cacheKey,{value,expires_at:expires,cached_at:new Date(computed).toISOString()});
    return researchResponse({...value,delivery:{cache_hit:false,served_at:new Date(computed).toISOString(),cached_at:null,source_receipts_retimestamped:false}});
  }catch(error){
    const allowed=['cancelled','acquisition_deadline_exceeded','market_data_authentication_failed','requested_feed_not_entitled','provider_rate_limited',
      'provider_unavailable','provider_schema_invalid','invalid_calendar','insufficient_completed_sessions','invalid_provider_pagination',
      'provider_pagination_bound_exceeded','session_boundary_advanced'];
    const code=request.signal.aborted?'cancelled':Date.now()>=deadline?'acquisition_deadline_exceeded':error?.name==='TimeoutError'?'source_request_timeout'
      :allowed.includes(error?.message)?error.message:'source_acquisition_failed';
    return json({...base,status:code==='cancelled'?'cancelled':'unavailable',error:code,source_receipts:captures,computed_at:new Date().toISOString()},code==='cancelled'?408:503);
  }
}
