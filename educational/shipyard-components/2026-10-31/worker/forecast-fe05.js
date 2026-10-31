// Bounded read-only source path for the NEW FE05 current SPY-holdings breadth
// proxy. Raw holdings and member symbols stay request-scoped and are not returned.
const SHIPYARD_FE05_ET=date=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(date));
const SHIPYARD_FE05_BAR_DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
function shipyardFE05Hex(bytes){return [...bytes].map(v=>v.toString(16).padStart(2,'0')).join('');}
async function shipyardFE05Digest(bytes){return shipyardFE05Hex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)));}
async function shipyardFE05ReadBytes(response,limit){
  const declared=Number(response.headers.get('content-length'));if(Number.isFinite(declared)&&declared>limit)throw Error('source_response_too_large');
  if(!response.body)throw Error('source_response_empty');const reader=response.body.getReader(),chunks=[];let size=0;
  for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>limit){await reader.cancel();throw Error('source_response_too_large');}chunks.push(value);}
  const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}return bytes;
}
function shipyardFE05SafeCapture(receipt){
  const {request_url,...safe}=receipt;
  if(receipt.operation==='historical_multi_symbol_1Day_page')return {...safe,request_url:'https://data.alpaca.markets/v2/stocks/bars?symbols=%5Bcurrent_cohort_redacted%5D',request_url_redacted:true,redacted_query_fields:['symbols']};
  return {...safe,request_url};
}
function shipyardFE05DeliveryError(base,error,captures,started,codeOverride=null){
  const known=new Set(['cancelled','acquisition_deadline_exceeded','market_data_credentials_unavailable','market_data_authentication_failed','requested_feed_not_entitled','provider_rate_limited','provider_unavailable','ssga_source_denied','ssga_source_unavailable','source_request_timeout','source_response_too_large','source_response_empty','xlsx_deflate_unavailable','xlsx_deflate_unsupported','invalid_holdings_xlsx_size','invalid_holdings_zip_directory','invalid_holdings_zip_entry','invalid_holdings_zip_uncompressed_length','unsupported_holdings_zip_compression','holdings_xlsx_parts_missing','invalid_holdings_xml','invalid_holdings_shared_string_index','invalid_holdings_cell_address','invalid_holdings_row','invalid_holdings_position_row','unexpected_noncontiguous_holdings_rows','unexpected_holdings_row_count','unexpected_holdings_workbook','unexpected_spy_workbook_identity','invalid_holdings_asof_date','unexpected_holdings_headers','invalid_holdings_row_count','invalid_holdings_position','duplicate_holdings_identifier','unreconciled_holdings_total','invalid_holdings_snapshot','excluded_holding_identity_mismatch','unknown_equity_identifier_format','unknown_equity_ticker_format','duplicate_provider_ticker','incomplete_holdings_universe','incomplete_top_issuer_cohort','issuer_cohort_symbol_bound_exceeded','invalid_top_issuer_weight','invalid_calendar','invalid_calendar_range','holdings_asof_not_completed_session','insufficient_completed_sessions','provider_schema_invalid','invalid_provider_pagination','provider_pagination_bound_exceeded','matched_session_coverage_incomplete','invalid_breadth_cohort_or_dates','invalid_breadth_price_panel','invalid_breadth_price_series','invalid_breadth_weight_denominator','issuer_mapping_mismatch','issuer_weight_mismatch','insufficient_breadth_normalization','degenerate_advance_decline_normalizer','degenerate_new_high_low_normalizer','degenerate_index_trend_normalizer','invalid_breadth_features','invalid_breadth_source_receipts','breadth_scorer_unavailable','session_boundary_advanced']);
  const message=String(error?.message||'source_acquisition_failed'),code=codeOverride||(known.has(message)?message:'source_acquisition_failed');
  return json({...base,status:code==='cancelled'?'cancelled':'unavailable',error:code,source_receipts:captures.map(shipyardFE05SafeCapture),acquisition:{request_count:captures.length,budget_seconds:35,elapsed_ms:Date.now()-started}},code==='cancelled'?408:503);
}
async function shipyardForecastFE05(request,args,env){
  const started=Date.now(),deadline=started+35000,policy=SHIPYARD_FE05_FEATURES.FE05_BREADTH_POLICY,policyHash=SHIPYARD_FE05_FEATURES.FE05_BREADTH_POLICY_SHA256;
  const base={schema:'SHIPYARD_FE05_SOURCE_FORECAST_V1',engine_id:'FE05',feature_origin:'provider_capture_new_policy',feature_policy:policy,feature_policy_sha256:policyHash,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false,market_population_claim:false,redistribution_rights_cleared:false}};
  if(!args||args.engine_id!=='FE05'||Object.keys(args).length!==1)return json({...base,status:'invalid_request',error:'invalid_arguments'},400);
  if(request.signal.aborted)return json({...base,status:'cancelled',error:'cancelled'},408);
  const key=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
  if(typeof key!=='string'||!key||typeof secret!=='string'||!secret)return json({...base,status:'unavailable',error:'market_data_credentials_unavailable'},503);
  const captures=[],requestBound=5;
  for(let i=0;i<requestBound-1;i++)if(!alpacaRateAllowed(request,started))return json({...base,status:'unavailable',error:'rate_limited'},429);
  const get=async(url,operation,subject,maxBytes,provider=false)=>{
    if(request.signal.aborted)throw Error('cancelled');if(Date.now()>=deadline)throw Error('acquisition_deadline_exceeded');
    const sent=new Date().toISOString(),headers={accept:provider?'application/json':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'};
    if(provider){headers['APCA-API-KEY-ID']=key;headers['APCA-API-SECRET-KEY']=secret;}
    const response=await fetch(url,{method:'GET',headers,redirect:'manual',cache:'no-store',signal:AbortSignal.any([request.signal,AbortSignal.timeout(Math.max(1,Math.min(8000,deadline-Date.now())))])});
    const receipt={operation,subject,request_started_at:sent,http_response_received_at:new Date().toISOString(),received_at:null,response_sha256:null,request_url:new URL(url).toString(),http_status:response.status};captures.push(receipt);
    if(!response.ok)throw Error(provider?(response.status===401?'market_data_authentication_failed':response.status===403?'requested_feed_not_entitled':response.status===429?'provider_rate_limited':'provider_unavailable')
      :(response.status===401||response.status===403||response.status===404?'ssga_source_denied':'ssga_source_unavailable'));
    const bytes=await shipyardFE05ReadBytes(response,maxBytes);receipt.received_at=new Date().toISOString();receipt.response_sha256=await shipyardFE05Digest(bytes);receipt.hash_serialization='raw_response_bytes';
    return {bytes,receipt};
  };
  try{
    const sourceResult=await get(policy.source.url,'spy_holdings_xlsx','SPY',policy.acquisition.max_holdings_file_bytes,false);
    const holdings=await SHIPYARD_FE05_FEATURES.parseFE05SpyHoldingsXlsx(sourceResult.bytes);
    const cohort=SHIPYARD_FE05_FEATURES.selectFE05TopIssuerCohort(holdings);
    if(holdings.as_of_date>SHIPYARD_FE05_ET(started))throw Error('invalid_holdings_asof_date');
    const evaluationCalendarDate=SHIPYARD_FE05_ET(started);
    const from=new Date(Date.parse(holdings.as_of_date+'T00:00:00Z')-policy.calendar_lookback_days*86400000).toISOString().slice(0,10),calendarUrl=new URL('https://paper-api.alpaca.markets/v2/calendar');
    // Reuse the existing calendar request to cover the evaluation date. The
    // as-of history window still ends at the holdings date; these later rows
    // only qualify the date-only age bound and disclose completed-session lag.
    calendarUrl.searchParams.set('start',from);calendarUrl.searchParams.set('end',evaluationCalendarDate);
    const calResult=await get(calendarUrl,'official_calendar','US_EQUITY',policy.acquisition.max_calendar_bytes,true),calendarPayload=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(calResult.bytes));
    if(!Array.isArray(calendarPayload)||calendarPayload.length>801)throw Error('invalid_calendar');
    let last='';const sessions=calendarPayload.map(row=>{
      if(!row||!shipyardCalendarDate(row.date)||row.date<from||row.date>evaluationCalendarDate||row.date<=last||typeof row.open!=='string'||typeof row.close!=='string'||row.open<'04:00'||row.close>'20:00'||row.open>=row.close)throw Error('invalid_calendar');
      last=row.date;const open=shipyardCalendarBoundary(row.date,row.open),close=shipyardCalendarBoundary(row.date,row.close);
      if(Date.parse(close)<=Date.parse(open)||Date.parse(close)-Date.parse(open)>390*60000)throw Error('invalid_calendar');return {date:row.date,open,close};
    });
    const eligible=sessions.filter(s=>s.date<=holdings.as_of_date&&Date.parse(s.close)+policy.completion_delay_ms<=started);
    if(eligible.length<505)throw Error('insufficient_completed_sessions');if(eligible.at(-1).date!==holdings.as_of_date)throw Error('holdings_asof_not_completed_session');
    const selected=eligible.slice(-505),dates=selected.map(s=>s.date),start=shipyardCalendarBoundary(dates[0],'00:00');
    const tomorrow=new Date(Date.parse(holdings.as_of_date+'T00:00:00Z')+86400000).toISOString().slice(0,10),end=new Date(Date.parse(shipyardCalendarBoundary(tomorrow,'00:00'))-1).toISOString();
    const symbols=[...cohort.symbols,'SPY'].sort();if(symbols.length>policy.acquisition.max_symbols||new Set(symbols).size!==symbols.length)throw Error('issuer_cohort_symbol_bound_exceeded');
    const barsBySymbol=Object.fromEntries(symbols.map(symbol=>[symbol,[]])),seenTokens=new Set();let token=null,complete=false,page=0;
    for(page=1;page<=policy.acquisition.max_pages;page++){
      const url=new URL('https://data.alpaca.markets/v2/stocks/bars');
      const query={symbols:symbols.join(','),timeframe:'1Day',start,end,feed:'iex',adjustment:'split',currency:'USD',asof:holdings.as_of_date,sort:'asc',limit:String(policy.acquisition.max_bars_rows),...(token?{page_token:token}:{})};
      for(const [k,v] of Object.entries(query))url.searchParams.set(k,v);
      const pageResult=await get(url,'historical_multi_symbol_1Day_page','FE05_TOP25_ISSUER_COHORT',policy.acquisition.max_decoded_bytes_per_bars_page,true);
      const payload=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(pageResult.bytes));
      if(!payload||!payload.bars||typeof payload.bars!=='object'||Array.isArray(payload.bars)||!Object.hasOwn(payload,'next_page_token'))throw Error('provider_schema_invalid');
      const keys=Object.keys(payload.bars);if(keys.some(symbol=>!symbols.includes(symbol)))throw Error('provider_schema_invalid');
      let pageRows=0;
      for(const [symbol,rows] of Object.entries(payload.bars)){
        if(!Array.isArray(rows))throw Error('provider_schema_invalid');pageRows+=rows.length;if(barsBySymbol[symbol].length+rows.length>505)throw Error('provider_schema_invalid');barsBySymbol[symbol].push(...rows);
      }
      if(pageRows>policy.acquisition.max_bars_rows)throw Error('provider_schema_invalid');
      const receipt=pageResult.receipt;receipt.provider_rows=pageRows;receipt.has_next_page=payload.next_page_token!==null&&payload.next_page_token!=='';
      receipt.page_index=page;
      receipt.request_url=url.origin+url.pathname+'?'+new URLSearchParams({...query,...(token?{page_token:'[continuation]'}:{})});
      token=payload.next_page_token;if(token==null||token===''){complete=true;break;}
      if(typeof token!=='string'||!/^[\x21-\x7e]{1,2048}$/.test(token)||seenTokens.has(token))throw Error('invalid_provider_pagination');seenTokens.add(token);
    }
    if(!complete)throw Error('provider_pagination_bound_exceeded');
    const closesBySymbol={};for(const symbol of symbols){
      const rows=barsBySymbol[symbol],byDate=new Map();let prior=-Infinity;
      for(const bar of rows){
        if(!bar||typeof bar.t!=='string'||!Number.isFinite(Date.parse(bar.t))||!Number.isFinite(bar.c)||bar.c<=0)throw Error('provider_schema_invalid');
        const at=Date.parse(bar.t),day=SHIPYARD_FE05_BAR_DATE_FORMAT.format(new Date(at));
        if(at<=prior||byDate.has(day)||!dates.includes(day))throw Error('provider_schema_invalid');prior=at;byDate.set(day,bar.c);
      }
      if(rows.length!==505||dates.some(day=>!byDate.has(day)))throw Error('matched_session_coverage_incomplete');closesBySymbol[symbol]=dates.map(day=>byDate.get(day));
    }
    const finished=Date.now();if(request.signal.aborted)throw Error('cancelled');if(finished>=deadline)throw Error('acquisition_deadline_exceeded');
    if(SHIPYARD_FE05_ET(finished)!==evaluationCalendarDate)throw Error('session_boundary_advanced');
    const evaluationAt=new Date(finished).toISOString();
    const built=SHIPYARD_FE05_FEATURES.buildFE05SourceForecast({holdings,cohort,dates,closesBySymbol,calendarSessions:sessions,calendarCapture:calResult.receipt,
      holdingsCapture:sourceResult.receipt,barsCaptures:captures.filter(c=>c.operation==='historical_multi_symbol_1Day_page'),evaluationAt});
    built.source.captures=built.source.captures.map(shipyardFE05SafeCapture);
    built.acquisition={request_count:captures.length,request_bound:requestBound,requested_symbols_count:symbols.length,expected_bar_rows:symbols.length*505,
      max_bars_rows_per_page:policy.acquisition.max_bars_rows,max_response_bytes_per_bars_page:policy.acquisition.max_decoded_bytes_per_bars_page,
      max_holdings_bytes:policy.acquisition.max_holdings_file_bytes,elapsed_ms:Date.now()-started,budget_seconds:policy.acquisition.budget_seconds,cache_seconds:0};
    return researchResponse(built);
  }catch(error){
    if(error?.name==='TimeoutError')return shipyardFE05DeliveryError(base,error,captures,started,'source_request_timeout');
    return shipyardFE05DeliveryError(base,error,captures,started);
  }
}
