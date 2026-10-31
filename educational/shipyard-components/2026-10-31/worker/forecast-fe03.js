// Source-only, bounded on-demand acquisition for an explicitly NEW FE03 policy.
// Host: SHIPYARD_FORECAST_FE03_FEATURES, shipyardCalendarDate/Boundary,
// readBoundedBody, researchResponse/json/alpacaRateAllowed. No account/order endpoints.
const SHIPYARD_FE03_CACHE=new Map();
const SHIPYARD_FE03_DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
function shipyardFE03Date(ms){return SHIPYARD_FE03_DATE_FORMAT.format(new Date(ms));}
function shipyardFE03ValidLocalTime(value){return typeof value==='string'&&/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value);}
function shipyardFE03Base(){
 const policy=SHIPYARD_FORECAST_FE03_FEATURES.FE03_BREAKOUT_POLICY;
 return {schema:'SHIPYARD_FE03_SOURCE_FORECAST_V1',engine_id:'FE03',feature_origin:'provider_capture_new_policy',feature_policy:policy,
  feature_policy_sha256:SHIPYARD_FORECAST_FE03_FEATURES.FE03_BREAKOUT_POLICY_SHA256,
  restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,
   calibrated_probability:null,historical_point_in_time_claim:false}};
}
async function shipyardForecastFE03(request,args,env){
 const started=Date.now(),policy=SHIPYARD_FORECAST_FE03_FEATURES.FE03_BREAKOUT_POLICY,base=shipyardFE03Base();
 if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).length!==1||!Object.hasOwn(args,'symbol')
  ||typeof args.symbol!=='string'||!/^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$/.test(args.symbol))return json({...base,status:'invalid',error:'invalid_arguments'},400);
 const symbol=args.symbol.toUpperCase(),cacheKey=policy.id+':iex:split:1Day:'+symbol;base.symbol=symbol;
 if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
 const key=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
 if(typeof key!=='string'||!key||typeof secret!=='string'||!secret)return json({...base,status:'unavailable',error:'market_data_credentials_unavailable'},503);
 const cached=SHIPYARD_FE03_CACHE.get(cacheKey);
 if(cached&&started>=Date.parse(cached.cached_at)&&started<cached.expires_at)return researchResponse({...cached.value,
  delivery:{cache_hit:true,served_at:new Date(started).toISOString(),cached_at:cached.cached_at,source_receipts_retimestamped:false}});
 SHIPYARD_FE03_CACHE.delete(cacheKey);
 // One calendar plus at most two history pages; reserve worst-case before the first request.
 for(let i=0;i<3;i++)if(!alpacaRateAllowed(request,started))return json({...base,status:'unavailable',error:'rate_limited'},429);
 const deadline=started+policy.acquisition_budget_seconds*1000,captures=[],offsets=new Map();
 const get=async(url,operation,subject,maxBytes)=>{
  if(request.signal.aborted)throw Error('cancelled');if(Date.now()>=deadline)throw Error('acquisition_deadline_exceeded');
  const requestStartedAt=new Date().toISOString();
  const response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret,accept:'application/json'},
   redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(Math.max(1,Math.min(policy.per_request_timeout_seconds*1000,deadline-Date.now())))])});
  const safeURL=new URL(url);if(safeURL.searchParams.has('page_token'))safeURL.searchParams.set('page_token','[continuation]');
  const receipt={operation,subject,request_started_at:requestStartedAt,http_response_received_at:new Date().toISOString(),received_at:null,
   response_sha256:null,request_url:safeURL.toString(),http_status:response.status};captures.push(receipt);
  if(!response.ok)throw Error(response.status===401?'market_data_authentication_failed':response.status===403?'requested_feed_not_entitled':response.status===429?'provider_rate_limited':'provider_unavailable');
  const body=await readBoundedBody(response,maxBytes);receipt.received_at=new Date().toISOString();
  receipt.response_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body))),byte=>byte.toString(16).padStart(2,'0')).join('');
  receipt.hash_serialization='UTF-8 re-encoding of decoded response text';
  let payload;try{payload=JSON.parse(body);}catch{throw Error('provider_schema_invalid');}return payload;
 };
 try{
  const today=shipyardFE03Date(started),from=new Date(Date.parse(today+'T12:00:00Z')-policy.calendar_lookback_days*86400000).toISOString().slice(0,10);
  const calendarURL=new URL('https://paper-api.alpaca.markets/v2/calendar');calendarURL.searchParams.set('start',from);calendarURL.searchParams.set('end',today);
  const calendarRows=await get(calendarURL,'official_calendar','US_EQUITY',262144);
  if(!Array.isArray(calendarRows)||calendarRows.length>801)throw Error('invalid_calendar');
  let previousDate='';const calendar=calendarRows.map(row=>{
   if(!row||!shipyardCalendarDate(row.date)||row.date<from||row.date>today||row.date<=previousDate
    ||!shipyardFE03ValidLocalTime(row.open)||!shipyardFE03ValidLocalTime(row.close)||row.open<'04:00'||row.close>'20:00'||row.open>=row.close)throw Error('invalid_calendar');
   previousDate=row.date;const open=shipyardCalendarBoundary(row.date,row.open),close=shipyardCalendarBoundary(row.date,row.close),duration=Date.parse(close)-Date.parse(open);
   if(duration<=0||duration>960*60000||duration%60000!==0)throw Error('invalid_calendar');
   return {date:row.date,open,close};
  });
  const eligible=()=>calendar.filter(session=>Date.parse(session.close)+policy.completion_delay_ms<=Date.now());
  const selected=eligible().slice(-policy.sessions);if(selected.length!==policy.sessions)throw Error('insufficient_completed_sessions');
  const start=shipyardCalendarBoundary(selected[0].date,'00:00'),end=selected.at(-1).close,bars=[],tokens=new Set();let token=null,complete=false;
  for(let page=0;page<policy.max_pages;page++){
   const url=new URL(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/bars`);
   const query={timeframe:'1Day',start,end:new Date(Date.parse(end)-1).toISOString(),feed:'iex',adjustment:'split',currency:'USD',asof:today,sort:'asc',limit:'1000',...(token?{page_token:token}:{})};
   for(const [name,value]of Object.entries(query))url.searchParams.set(name,value);
   const payload=await get(url,`history_1Day_page_${page+1}`,symbol,policy.max_response_bytes_per_request);
   if(!payload||(payload.symbol!==undefined&&payload.symbol!==symbol)||!Array.isArray(payload.bars)
    ||!Object.prototype.hasOwnProperty.call(payload,'next_page_token')||payload.bars.length>1000||bars.length+payload.bars.length>policy.max_rows)throw Error('provider_schema_invalid');
   const safeQuery={...query,...(token?{page_token:'[continuation]'}:{})};
   captures.at(-1).request_url=url.origin+url.pathname+'?'+new URLSearchParams(safeQuery);
   captures.at(-1).provider_rows=payload.bars.length;bars.push(...payload.bars);token=payload.next_page_token;
   captures.at(-1).has_next_page=token!=null&&token!=='';
   if(token==null||token===''){complete=true;break;}
   if(typeof token!=='string'||!/^[\x21-\x7e]{1,2048}$/.test(token)||tokens.has(token))throw Error('invalid_provider_pagination');tokens.add(token);
  }
  if(!complete)throw Error('provider_pagination_bound_exceeded');
  const finished=Date.now();if(request.signal.aborted)throw Error('cancelled');if(finished>=deadline)throw Error('acquisition_deadline_exceeded');
  const latestEligible=eligible().at(-1)?.date;
  if(latestEligible!==selected.at(-1).date||shipyardFE03Date(finished)!==today)throw Error('session_boundary_advanced');
  const value=SHIPYARD_FORECAST_FE03_FEATURES.buildFE03SourceForecast({symbol,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:today,
   evaluation_at:new Date(finished).toISOString(),calendar:{sessions:calendar,received_at:captures[0].received_at,requested_range:{start_date:from,end_date:today},complete_provider_response:true},
   calendar_capture:captures[0],bars,requested_window:{start,end,end_exclusive:true},captures:captures.slice(1),pagination_complete:true});
  const computed=Date.now();if(request.signal.aborted)throw Error('cancelled');if(computed>=deadline)throw Error('acquisition_deadline_exceeded');
  if(eligible().at(-1)?.date!==selected.at(-1).date||shipyardFE03Date(computed)!==today)throw Error('session_boundary_advanced');
  value.acquisition={request_count:captures.length,request_bound:3,max_rows:policy.max_rows,max_response_bytes:policy.max_response_bytes_per_request,
   elapsed_ms:computed-started,elapsed_budget_ms:policy.acquisition_budget_seconds*1000,calendar_capture:captures[0]};
  value.computed_at=new Date(computed).toISOString();
  const successful=['computed','no_setup','level_invalidated','acceptance_not_mature','insufficient_mature_episode_sample'].includes(value.status);
  if(!successful)return researchResponse({...value,source_receipts:captures,evaluation_at:new Date(finished).toISOString()});
  if(value.status!=='computed')return researchResponse({...value,delivery:{cache_hit:false,served_at:new Date(computed).toISOString(),cached_at:null,source_receipts_retimestamped:false}});
  const nextBoundary=calendar.map(session=>Date.parse(session.close)+policy.completion_delay_ms).find(at=>at>finished)??Infinity;
  const midnight=Date.parse(shipyardCalendarBoundary(today,'00:00'));
  const sourceAsOf=Date.parse(value.freshness.source_as_of),ageBoundary=sourceAsOf+172800000,guardBoundary=sourceAsOf+604800000;
  const expires=Math.min(finished+60000,nextBoundary,midnight>finished?midnight:Infinity,ageBoundary>=finished?ageBoundary:Infinity,guardBoundary>=finished?guardBoundary:Infinity);
  for(const [key,entry]of SHIPYARD_FE03_CACHE)if(entry.expires_at<=finished)SHIPYARD_FE03_CACHE.delete(key);
  if(SHIPYARD_FE03_CACHE.size>=8)SHIPYARD_FE03_CACHE.delete(SHIPYARD_FE03_CACHE.keys().next().value);
  SHIPYARD_FE03_CACHE.set(cacheKey,{value,expires_at:expires,cached_at:new Date(computed).toISOString()});
  return researchResponse({...value,delivery:{cache_hit:false,served_at:new Date(computed).toISOString(),cached_at:null,source_receipts_retimestamped:false}});
 }catch(error){
  const allowed=['cancelled','acquisition_deadline_exceeded','market_data_authentication_failed','requested_feed_not_entitled','provider_rate_limited','provider_unavailable',
   'provider_schema_invalid','invalid_calendar','insufficient_completed_sessions','invalid_provider_pagination','provider_pagination_bound_exceeded',
   'session_boundary_advanced','extended_closure_or_calendar_staleness_unverified'];
  const code=request.signal.aborted?'cancelled':Date.now()>=deadline?'acquisition_deadline_exceeded':error?.name==='TimeoutError'?'source_request_timeout'
   :allowed.includes(error?.message)?error.message:'source_acquisition_failed';
  return json({...base,status:code==='cancelled'?'cancelled':'unavailable',error:code,source_receipts:captures,computed_at:new Date().toISOString()},code==='cancelled'?408:503);
 }
}
