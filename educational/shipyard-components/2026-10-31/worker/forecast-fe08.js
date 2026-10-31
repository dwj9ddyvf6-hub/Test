// Source-only, bounded on-demand acquisition for an explicitly NEW FE08 feature policy.
// Host: SHIPYARD_FORECAST_FEATURES, calendar helpers, readBoundedBody,
// researchResponse/json/alpacaRateAllowed. No account/order endpoints or caller data.
const SHIPYARD_FE08_CACHE = new Map();
function shipyardFE08Date(ms) {
  return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(ms));
}
async function shipyardForecastFE08(request,args,env) {
  const started=Date.now(), policy=SHIPYARD_FORECAST_FEATURES.FE08_RV_POLICY;
  const base={schema:'SHIPYARD_FE08_SOURCE_FORECAST_V1',engine_id:'FE08',feature_origin:'provider_capture_new_policy',feature_policy:policy,feature_policy_sha256:SHIPYARD_FORECAST_FEATURES.FE08_RV_POLICY_SHA256,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false}};
  if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).some(k=>k!=='symbol')||typeof args.symbol!=='string'||!/^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$/.test(args.symbol))return json({...base,status:'invalid',error:'invalid_arguments'},400);
  const symbol=args.symbol.toUpperCase(),cacheKey=policy.id+':iex:raw:5Min:'+symbol;
  base.symbol=symbol;
  if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
  const key=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
  if(typeof key!=='string'||!key||typeof secret!=='string'||!secret)return json({...base,status:'unavailable',error:'market_data_credentials_unavailable'},503);
  // Read-only 60s bounded process cache; receipts, evaluation_at and source_as_of are immutable.
  const cached=SHIPYARD_FE08_CACHE.get(cacheKey);
  if(cached&&started>=Date.parse(cached.cached_at)&&started<cached.expires_at)return researchResponse({...cached.value,delivery:{cache_hit:true,served_at:new Date(started).toISOString(),cached_at:cached.cached_at,source_receipts_retimestamped:false}});
  SHIPYARD_FE08_CACHE.delete(cacheKey);
  // Worst case: one calendar + two pages. Each is charged before any fetch.
  for(let i=0;i<3;i++)if(!alpacaRateAllowed(request,started))return json({...base,status:'unavailable',error:'rate_limited'},429);
  const deadline=started+25000,captures=[];
  const get=async(url,operation,maxBytes)=>{
    if(request.signal.aborted)throw Error('cancelled');
    if(Date.now()>=deadline)throw Error('acquisition_deadline_exceeded');
    const sent=new Date().toISOString();
    const response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret,accept:'application/json'},redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(Math.max(1,Math.min(8000,deadline-Date.now())))])});
    const safeURL=new URL(url);if(safeURL.searchParams.has('page_token'))safeURL.searchParams.set('page_token','[continuation]');
    const receipt={operation,request_started_at:sent,http_response_received_at:new Date().toISOString(),received_at:null,response_sha256:null,request_url:safeURL.toString(),http_status:response.status};
    captures.push(receipt);
    if(!response.ok)throw Error(response.status===401?'market_data_authentication_failed':response.status===403?'requested_feed_not_entitled':response.status===429?'provider_rate_limited':'provider_unavailable');
    const body=await readBoundedBody(response,maxBytes);
    receipt.received_at=new Date().toISOString();
    receipt.response_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body))),b=>b.toString(16).padStart(2,'0')).join('');
    receipt.hash_serialization='UTF-8 re-encoding of decoded response text';
    let payload;try{payload=JSON.parse(body);}catch{throw Error('provider_schema_invalid');}
    return payload;
  };
  try {
    const today=shipyardFE08Date(started),from=new Date(Date.parse(today+'T12:00:00Z')-60*86400000).toISOString().slice(0,10);
    const url=new URL('https://paper-api.alpaca.markets/v2/calendar');url.searchParams.set('start',from);url.searchParams.set('end',today);
    const calendarRows=await get(url,'official_calendar',262144);
    if(!Array.isArray(calendarRows)||calendarRows.length>61)throw Error('invalid_calendar');
    let previous='';
    const sessions=calendarRows.map(s=>{
      if(!s||!shipyardCalendarDate(s.date)||s.date<from||s.date>today||s.date<=previous||typeof s.open!=='string'||typeof s.close!=='string'||s.open<'04:00'||s.close>'20:00'||s.open>=s.close)throw Error('invalid_calendar');
      previous=s.date;
      return {date:s.date,open:shipyardCalendarBoundary(s.date,s.open),close:shipyardCalendarBoundary(s.date,s.close)};
    });
    const selected=sessions.filter(s=>Date.parse(s.close)+policy.completion_delay_ms<=started).slice(-22);
    if(selected.length!==22)throw Error('insufficient_completed_sessions');
    const start=selected[0].open,end=selected.at(-1).close,bars=[],tokens=new Set();let token=null,complete=false;
    for(let page=0;page<2;page++) {
      const target=new URL(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/bars`);
      const query={timeframe:'5Min',start,end:new Date(Date.parse(end)-1).toISOString(),feed:'iex',adjustment:'raw',sort:'asc',limit:'5000',...(token?{page_token:token}:{})};
      for(const [k,v] of Object.entries(query))target.searchParams.set(k,v);
      const payload=await get(target,`history_5Min_page_${page+1}`,2*1024*1024);
      if(!payload||payload.symbol!==undefined&&payload.symbol!==symbol||!Array.isArray(payload.bars)||!Object.prototype.hasOwnProperty.call(payload,'next_page_token')||payload.bars.length>5000||bars.length+payload.bars.length>10000)throw Error('provider_schema_invalid');
      // Provider cursors are not credentials, but avoid exposing them as source identities.
      captures.at(-1).request_url=target.origin+target.pathname+'?'+new URLSearchParams({...query,...(token?{page_token:'[continuation]'}:{})});
      captures.at(-1).provider_rows=payload.bars.length;
      bars.push(...payload.bars);
      token=payload.next_page_token;
      captures.at(-1).has_next_page=token!=null&&token!=='';
      if(token==null||token===''){complete=true;break;}
      if(typeof token!=='string'||!/^[\x21-\x7e]{1,2048}$/.test(token)||tokens.has(token))throw Error('invalid_provider_pagination');
      tokens.add(token);
    }
    if(!complete)throw Error('provider_pagination_bound_exceeded');
    const finished=Date.now();if(request.signal.aborted)throw Error('cancelled');if(finished>=deadline)throw Error('acquisition_deadline_exceeded');
    // Crossing the next eligible-session boundary requires a new acquisition, not a stale window.
    if(sessions.filter(s=>Date.parse(s.close)+policy.completion_delay_ms<=finished).at(-1)?.date!==selected.at(-1).date||shipyardFE08Date(finished)!==today)throw Error('session_boundary_advanced');
    const value=SHIPYARD_FORECAST_FEATURES.buildFE08SourceForecast({symbol,feed:'iex',adjustment:'raw',timeframe:'5Min',evaluation_at:new Date(finished).toISOString(),
      calendar:{sessions,received_at:captures[0].received_at,requested_range:{start_date:from,end_date:today},complete_provider_response:true},bars,requested_window:{start,end,end_exclusive:true},captures:captures.filter(c=>c.operation.startsWith('history_')),pagination_complete:true});
    const computed=Date.now();if(request.signal.aborted)throw Error('cancelled');if(computed>=deadline)throw Error('acquisition_deadline_exceeded');
    if(sessions.filter(s=>Date.parse(s.close)+policy.completion_delay_ms<=computed).at(-1)?.date!==selected.at(-1).date||shipyardFE08Date(computed)!==today)throw Error('session_boundary_advanced');
    value.acquisition={calendar_capture:captures[0],request_count:captures.length,request_bound:3,max_rows:10000,max_response_bytes:2*1024*1024,elapsed_ms:computed-started,elapsed_budget_ms:25000};
    value.computed_at=new Date(computed).toISOString();
    if(value.status!=='computed')return researchResponse({...value,symbol,evaluation_at:new Date(finished).toISOString(),source_receipts:captures});
    const nextBoundary=sessions.map(s=>Date.parse(s.close)+policy.completion_delay_ms).find(t=>t>finished)??Infinity;
    // Expire at source-age threshold too, so a cache hit cannot conceal stale diagnostics.
    const ageBoundary=Date.parse(value.freshness.source_as_of)+policy.freshness_max_age_seconds*1000;
    const expires=Math.min(finished+60000,nextBoundary,ageBoundary>=finished?ageBoundary:Infinity);
    for(const [k,v] of SHIPYARD_FE08_CACHE)if(v.expires_at<=finished)SHIPYARD_FE08_CACHE.delete(k);
    if(SHIPYARD_FE08_CACHE.size>=8)SHIPYARD_FE08_CACHE.delete(SHIPYARD_FE08_CACHE.keys().next().value);
    SHIPYARD_FE08_CACHE.set(cacheKey,{value,expires_at:expires,cached_at:new Date(computed).toISOString()});
    return researchResponse({...value,delivery:{cache_hit:false,served_at:new Date(computed).toISOString(),cached_at:null,source_receipts_retimestamped:false}});
  } catch(error) {
    const allowed=['cancelled','acquisition_deadline_exceeded','market_data_authentication_failed','requested_feed_not_entitled','provider_rate_limited','provider_unavailable','provider_schema_invalid','invalid_calendar','insufficient_completed_sessions','invalid_provider_pagination','provider_pagination_bound_exceeded','session_boundary_advanced'];
    const code=request.signal.aborted?'cancelled':Date.now()>=deadline?'acquisition_deadline_exceeded':error?.name==='TimeoutError'?'source_request_timeout':allowed.includes(error?.message)?error.message:'source_acquisition_failed';
    return json({...base,status:code==='cancelled'?'cancelled':'unavailable',error:code,source_receipts:captures,computed_at:new Date().toISOString()},code==='cancelled'?408:503);
  }
}
