// Bounded read-only FE04 adapter. Uses only the published market-data APIs,
// never Trading API/account/order routes. The feature builder is a NEW policy.
const SHIPYARD_FE04_CACHE=new Map();
const SHIPYARD_FE04_DATE=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const SHIPYARD_FE04_TIME=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
function shipyardFE04Date(ms){return SHIPYARD_FE04_DATE.format(new Date(ms));}
function shipyardFE04Base(){const f=SHIPYARD_FORECAST_FE04_FEATURES;return {schema:'SHIPYARD_FE04_SOURCE_FORECAST_V1',engine_id:'FE04',feature_origin:'provider_capture_new_policy',feature_policy:f.FE04_GAP_POLICY,feature_policy_sha256:f.FE04_GAP_POLICY_SHA256,restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false}};}
async function shipyardForecastFE04(request,args,env){
 const started=Date.now(),features=SHIPYARD_FORECAST_FE04_FEATURES,policy=features.FE04_GAP_POLICY,base=shipyardFE04Base();
 if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).length!==1||!Object.hasOwn(args,'symbol')||typeof args.symbol!=='string'||!['SPY','QQQ','IWM'].includes(args.symbol.toUpperCase()))return json({...base,status:'invalid',error:'invalid_arguments'},400);
 const symbol=args.symbol.toUpperCase(),today=shipyardFE04Date(started),cacheKey=policy.id+':iex:split:1Min:'+symbol+':'+today;base.symbol=symbol;
 if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
 // Do not spend quota for a window that cannot yet contain five completed bars.
 if(SHIPYARD_FE04_TIME.format(new Date(started))<'09:35')return json({...base,status:'unavailable',error:'opening_acceptance_incomplete'},425);
 const cached=SHIPYARD_FE04_CACHE.get(cacheKey);if(cached&&started>=Date.parse(cached.cached_at)&&started<cached.expires_at)return researchResponse({...cached.value,delivery:{cache_hit:true,served_at:new Date(started).toISOString(),cached_at:cached.cached_at,source_receipts_retimestamped:false}});
 SHIPYARD_FE04_CACHE.delete(cacheKey);
 const key=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;if(typeof key!=='string'||!key||typeof secret!=='string'||!secret)return json({...base,status:'unavailable',error:'market_data_credentials_unavailable'},503);
 // Reserve the documented worst case before any HTTP request: calendar + 6 pages x 3 symbols.
 for(let i=0;i<policy.limits.max_requests;i++)if(!alpacaRateAllowed(request,started))return json({...base,status:'unavailable',error:'rate_limited'},429);
 const deadline=started+policy.limits.deadline_ms,captures=[],acquisitionAbort=new AbortController();let calendarCapture=null;
 const get=async(url,operation,maxBytes)=>{
  if(request.signal.aborted)throw Error('cancelled');if(acquisitionAbort.signal.aborted)throw Error('peer_request_aborted');if(Date.now()>=deadline)throw Error('acquisition_deadline_exceeded');
  const requestStartedAt=new Date().toISOString(),response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret,accept:'application/json'},redirect:'manual',signal:AbortSignal.any([request.signal,acquisitionAbort.signal,AbortSignal.timeout(Math.max(1,Math.min(8000,deadline-Date.now())))])});
  const safe=new URL(url);if(safe.searchParams.has('page_token'))safe.searchParams.set('page_token','[continuation]');
  const receipt={operation,request_started_at:requestStartedAt,http_response_received_at:new Date().toISOString(),received_at:null,response_sha256:null,response_bytes:null,request_url:safe.toString(),hash_serialization:'UTF-8 re-encoding of decoded response text',http_status:response.status};captures.push(receipt);
  if(request.signal.aborted)throw Error('cancelled');if(acquisitionAbort.signal.aborted)throw Error('peer_request_aborted');if(!response.ok)throw Error(response.status===401?'market_data_authentication_failed':response.status===403?'requested_feed_not_entitled':response.status===429?'provider_rate_limited':'provider_unavailable');
  const body=await readBoundedBody(response,maxBytes);receipt.received_at=new Date().toISOString();receipt.response_bytes=new TextEncoder().encode(body).byteLength;receipt.response_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body))),b=>b.toString(16).padStart(2,'0')).join('');
  let payload;try{payload=JSON.parse(body);}catch{throw Error('provider_schema_invalid');}return payload;
 };
 try{
  const from=new Date(Date.parse(today+'T12:00:00Z')-120*86400000).toISOString().slice(0,10),calendarURL=new URL('https://paper-api.alpaca.markets/v2/calendar');calendarURL.searchParams.set('start',from);calendarURL.searchParams.set('end',today);
  const calendarRows=await get(calendarURL,'official_calendar',262144);if(!Array.isArray(calendarRows)||calendarRows.length>121)throw Error('invalid_calendar');let previousDate='';
  const sessions=calendarRows.map(row=>{if(!row||typeof row.date!=='string'||row.date<from||row.date>today||row.date<=previousDate||typeof row.open!=='string'||typeof row.close!=='string'||row.open<'04:00'||row.close>'20:00'||row.open>=row.close)throw Error('invalid_calendar');previousDate=row.date;const open=shipyardCalendarBoundary(row.date,row.open),close=shipyardCalendarBoundary(row.date,row.close),minutes=(Date.parse(close)-Date.parse(open))/60000;if(minutes<=0||minutes>390||minutes%1)throw Error('invalid_calendar');return {date:row.date,open,close};});
  calendarCapture=captures[0];const current=sessions.find(s=>s.date===today);if(!current)throw Error('current_session_unavailable');const acceptanceEnd=Date.parse(current.open)+5*60000;if(Date.now()<acceptanceEnd)throw Error('opening_acceptance_incomplete');
  const selected=sessions.slice(-policy.sessions);if(selected.length!==policy.sessions||selected.at(-1).date!==today)throw Error('insufficient_or_misaligned_sessions');
  const barsBySymbol={},allHistory=[];const historyStart=new Date(Date.parse(selected[0].close)-60000).toISOString(),historyEnd=new Date(acceptanceEnd-1).toISOString();
  const acquireSymbol=async target=>{try{const reducer=features.createFE04BoundedBarReducer(selected,target),tokens=new Set();let token=null,complete=false;
   for(let page=1;page<=policy.limits.max_pages_per_symbol;page++){
    if(request.signal.aborted)throw Error('cancelled');if(acquisitionAbort.signal.aborted)throw Error('peer_request_aborted');const url=new URL(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(target)}/bars`),query={timeframe:'1Min',start:historyStart,end:historyEnd,feed:'iex',adjustment:'split',sort:'asc',limit:'10000',...(token?{page_token:token}:{})};for(const [k,v]of Object.entries(query))url.searchParams.set(k,v);
    const operation=`history_1Min_${target}_page_${page}`,payload=await get(url,operation,policy.limits.max_response_bytes_per_page);
    if(!payload||payload.symbol!==undefined&&payload.symbol!==target||!Array.isArray(payload.bars)||payload.bars.length<1||payload.bars.length>10000||!Object.hasOwn(payload,'next_page_token'))throw Error('provider_schema_invalid');
    const next=payload.next_page_token;if(next!==null&&next!==undefined&&next!==''&&(typeof next!=='string'||!/^[\x21-\x7e]{1,2048}$/.test(next)||tokens.has(next)||next===token))throw Error('invalid_provider_pagination');
    const hasNext=next!==null&&next!==undefined&&next!=='';const capture=captures.find(c=>c.operation===operation);if(!capture)throw Error('provider_schema_invalid');capture.provider_rows=payload.bars.length;const pageReceipt=reducer.pushPage(payload.bars,hasNext);capture.retained_rows=pageReceipt.retained_rows;capture.has_next_page=hasNext;
    token=hasNext?next:null;if(hasNext)tokens.add(next);else{complete=true;break;}
   }
   if(!complete)throw Error('provider_pagination_bound_exceeded');const result=reducer.finish();barsBySymbol[target]=result.bars;allHistory.push(result);return result;
  }catch(error){if(!acquisitionAbort.signal.aborted)acquisitionAbort.abort();throw error;}
  };
  await Promise.all(policy.universe.map(acquireSymbol));
  const finish=Date.now();if(request.signal.aborted)throw Error('cancelled');if(finish>=deadline)throw Error('acquisition_deadline_exceeded');if(shipyardFE04Date(finish)!==today||Date.parse(current.open)+5*60000>finish)throw Error('session_boundary_advanced');if(captures.length>policy.limits.max_requests||captures.reduce((n,c)=>n+(c.response_bytes||0),0)>policy.limits.max_total_response_bytes)throw Error('response_byte_budget_exceeded');
  const value=features.buildFE04SourceForecast({symbol,feed:'iex',adjustment:'split',timeframe:'1Min',evaluation_at:new Date(finish).toISOString(),calendar:{sessions,received_at:calendarCapture.received_at,requested_range:{start_date:from,end_date:today},complete_provider_response:true},bars_by_symbol:barsBySymbol,captures,pagination_complete:true});
  const completedAt=Date.now();if(request.signal.aborted)throw Error('cancelled');if(completedAt>=deadline)throw Error('acquisition_deadline_exceeded');if(shipyardFE04Date(completedAt)!==today||Date.parse(current.open)+5*60000>completedAt)throw Error('session_boundary_advanced');
  value.acquisition={request_count:captures.length,request_bound:policy.limits.max_requests,history_provider_rows:allHistory.reduce((n,x)=>n+x.provider_rows,0),retained_rows_by_symbol:Object.fromEntries(Object.entries(barsBySymbol).map(([s,rows])=>[s,rows.length])),response_bytes:captures.reduce((n,c)=>n+(c.response_bytes||0),0),elapsed_ms:completedAt-started,elapsed_budget_ms:policy.limits.deadline_ms};value.computed_at=new Date(completedAt).toISOString();
  if(value.status!=='computed')return researchResponse({...value,source_receipts:captures});
  const midnight=Date.parse(shipyardCalendarBoundary(today,'23:59')),freshUntil=Date.parse(value.freshness.source_as_of)+policy.freshness_max_age_seconds*1000,expires=Math.min(completedAt+30000,midnight>completedAt?midnight:Infinity,freshUntil>=completedAt?freshUntil:Infinity);
  for(const [k,v] of SHIPYARD_FE04_CACHE)if(v.expires_at<=completedAt)SHIPYARD_FE04_CACHE.delete(k);if(SHIPYARD_FE04_CACHE.size>=8)SHIPYARD_FE04_CACHE.delete(SHIPYARD_FE04_CACHE.keys().next().value);SHIPYARD_FE04_CACHE.set(cacheKey,{value,expires_at:expires,cached_at:new Date(completedAt).toISOString()});
  return researchResponse({...value,delivery:{cache_hit:false,served_at:new Date(completedAt).toISOString(),cached_at:null,source_receipts_retimestamped:false}});
 }catch(error){
  const allowed=['cancelled','acquisition_deadline_exceeded','market_data_authentication_failed','requested_feed_not_entitled','provider_rate_limited','provider_unavailable','provider_schema_invalid','invalid_calendar','current_session_unavailable','opening_acceptance_incomplete','insufficient_or_misaligned_sessions','invalid_provider_pagination','provider_pagination_bound_exceeded','provider_page_budget_exceeded','response_byte_budget_exceeded','session_boundary_advanced'];
  const code=request.signal.aborted?'cancelled':Date.now()>=deadline?'acquisition_deadline_exceeded':error?.name==='TimeoutError'?'source_request_timeout':allowed.includes(error?.message)?error.message:error?.message==='invalid_provider_bar'||error?.message==='unordered_or_duplicate_provider_bar'?'invalid_provider_data':'source_acquisition_failed';
  const result={...base,status:code==='cancelled'?'cancelled':'unavailable',error:code,source_receipts:captures,computed_at:new Date().toISOString()};return json(result,code==='cancelled'?408:code==='rate_limited'?429:503);
 }
}
