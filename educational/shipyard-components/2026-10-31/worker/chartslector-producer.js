// Read-only bounded acquisition for the ChartsLector archive subset. Host supplies
// SHIPYARD_CHARTSLECTOR exports, json/researchResponse/readBoundedBody,
// alpacaRateAllowed and shipyardCalendarBoundary. No caller URLs or account reads.
const SHIPYARD_CHARTSLECTOR_CACHE = new Map();
const SHIPYARD_CHARTSLECTOR_CACHE_MS = 30000;
function shipyardChartslectorArguments(args) {
  return args&&typeof args==='object'&&!Array.isArray(args)&&Object.keys(args).length===1&&Array.isArray(args.symbols)&&args.symbols.length>=1&&args.symbols.length<=2&&args.symbols.every(s=>typeof s==='string'&&/^[A-Z][A-Z0-9.-]{0,9}$/.test(s))&&new Set(args.symbols).size===args.symbols.length;
}
function shipyardChartslectorDate(value) {
  const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(value)).map(p=>[p.type,p.value]));return `${parts.year}-${parts.month}-${parts.day}`;
}
function shipyardChartslectorInstant(value) {
  if(typeof value!=='string')return false;
  const match=/^(\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d)(?:\.(\d{1,9}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  if(!match||match[3]==='-00:00')return false;
  const local=Date.parse(match[1]+'.'+(match[2]||'').padEnd(3,'0').slice(0,3)+'Z');return Number.isFinite(local)&&new Date(local).toISOString().slice(0,19)===match[1]&&Number.isFinite(Date.parse(value));
}
function shipyardChartslectorClock(clock,now) {
  if(!clock||typeof clock.is_open!=='boolean'||!shipyardChartslectorInstant(clock.timestamp)||!shipyardChartslectorInstant(clock.next_open)||!shipyardChartslectorInstant(clock.next_close)||now-Date.parse(clock.timestamp)>60000||Date.parse(clock.timestamp)-now>2000||Date.parse(clock.next_open)<=Date.parse(clock.timestamp)||Date.parse(clock.next_close)<=Date.parse(clock.timestamp))throw Error('calendar_or_clock_unavailable');return clock;
}
async function shipyardChartslectorDigest(value) {return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(value))))).map(n=>n.toString(16).padStart(2,'0')).join('');}
async function shipyardChartslectorRun(request,args,env) {
  const started=Date.now(),base={schema:'SHIPYARD_CHARTSLECTOR_SUBSET_V1',source_identity:SHIPYARD_CHARTSLECTOR.CHARTSLECTOR_SOURCE,implementation:'original_archive_python_parity_port',
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,manual_inputs_accepted:false,stored_output_retimestamped:false},
    scope:{benchmark:'SPY',full_universe_scanned:false,ranker_executed:false,lod_overlay_enabled:false,subset:['RS26','RS78','RS156','RS26 alerts','RRR blended','candle stages']},
    remaining_components:{ranker:{status:'unavailable',reason:'Requires original fitted cache/ranker_coefs.json (absent at recovered pinned path) and cross-section of at least 20 names; no substitute score computed'},broader_archive:'Not executed by this bounded subset',femto_39_discovery_primitives:'Source inventoried separately; not claimed executed here',lector_desk_read:'Separate source lineage and producer; not this ChartsLector archive subset'}};
  if(!shipyardChartslectorArguments(args))return json({...base,status:'invalid_request',error:'expected_one_or_two_distinct_uppercase_symbols'},400);
  const names=[...new Set([...args.symbols,'SPY'])];base.scope.requested_symbols=args.symbols;base.scope.provided_symbols=names;
  const providerConfigured=typeof env.ALPACA_API_KEY_ID==='string'&&!!env.ALPACA_API_KEY_ID&&typeof env.ALPACA_API_SECRET_KEY==='string'&&!!env.ALPACA_API_SECRET_KEY;
  const cacheKey=JSON.stringify(args.symbols),cached=SHIPYARD_CHARTSLECTOR_CACHE.get(cacheKey);
  if(providerConfigured&&cached&&started<cached.until)return researchResponse({...cached.value,served_at:new Date(started).toISOString(),cache_hit:true});
  // Max 3 bar pages, calendar and two clock reads: six reserved provider calls.
  for(let i=0;i<6;i++)if(!alpacaRateAllowed(request,started))return json({...base,status:'unavailable',error:'rate_limited'},429);
  if(!providerConfigured)return json({...base,status:'unavailable',error:'provider_not_configured'},503);
  const captures=[],get=async(url,operation)=>{
    if(request.signal.aborted)throw Error('cancelled');
    const response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':env.ALPACA_API_KEY_ID,'APCA-API-SECRET-KEY':env.ALPACA_API_SECRET_KEY,accept:'application/json'},signal:AbortSignal.any([request.signal,AbortSignal.timeout(8000)]),redirect:'manual'});
    if(!response.ok)throw Error('provider_unavailable');const payload=JSON.parse(await readBoundedBody(response,2*1024*1024));captures.push({operation,received_at:new Date().toISOString()});return payload;
  };
  try {
    const initial=shipyardChartslectorClock(await get('https://paper-api.alpaca.markets/v2/clock','official_clock_initial'),Date.now()),endDate=shipyardChartslectorDate(initial.timestamp),startDate=new Date(Date.parse(endDate+'T12:00:00Z')-369*86400000).toISOString().slice(0,10);
    const calendarRaw=await get(`https://paper-api.alpaca.markets/v2/calendar?start=${startDate}&end=${endDate}`,'official_full_range_calendar');
    if(!Array.isArray(calendarRaw)||calendarRaw.length<156||calendarRaw.length>370)throw Error('calendar_or_clock_unavailable');
    const calendar=calendarRaw.map((d,i)=>{
      if(!d||typeof d.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(d.date)||!Number.isFinite(Date.parse(d.date+'T00:00:00Z'))||new Date(d.date+'T00:00:00Z').toISOString().slice(0,10)!==d.date||d.date<startDate||d.date>endDate||(i&&d.date<=calendarRaw[i-1].date)||typeof d.open!=='string'||typeof d.close!=='string'||d.open<'04:00'||d.close>'20:00'||d.open>=d.close)throw Error('calendar_or_clock_unavailable');
      return {date:d.date,open:shipyardCalendarBoundary(d.date,d.open),close:shipyardCalendarBoundary(d.date,d.close)};
    });
    const completed=calendar.filter(d=>Date.parse(d.close)+15*60000<=Date.parse(initial.timestamp));
    if(completed.length<156)throw Error('insufficient_history');
    const latest=completed.at(-1),from=shipyardCalendarBoundary(startDate,'00:00'),until=new Date(Date.parse(initial.timestamp)).toISOString(),rows=Object.fromEntries(names.map(s=>[s,[]]));
    let token=null;const tokens=new Set();
    for(let page=0;page<3;page++){
      const url=new URL('https://data.alpaca.markets/v2/stocks/bars');for(const [k,v] of Object.entries({symbols:names.join(','),timeframe:'1Day',start:from,end:until,adjustment:'split',feed:'iex',sort:'asc',limit:'10000',...(token?{page_token:token}:{})}))url.searchParams.set(k,v);
      const data=await get(url,`split_daily_page_${page+1}`);
      if(!data||!data.bars||typeof data.bars!=='object'||Array.isArray(data.bars)||Object.keys(data.bars).some(s=>!names.includes(s)))throw Error('invalid_market_data');
      for(const symbol of names){const source=data.bars[symbol]??[];if(!Array.isArray(source)||source.length+rows[symbol].length>400)throw Error('history_bound_exceeded');
        for(const b of source){if(!b||!shipyardChartslectorInstant(b.t)||![b.o,b.h,b.l,b.c].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>0)||!Number.isFinite(b.v)||b.v<0||b.h<Math.max(b.o,b.c)||b.l>Math.min(b.o,b.c)||b.h<b.l)throw Error('invalid_market_data');
          const date=shipyardChartslectorDate(b.t),at=new Date(Date.parse(b.t)).toISOString(),prev=rows[symbol].at(-1);
          // Daily timestamps must identify local midnight and official sessions.
          if(at!==shipyardCalendarBoundary(date,'00:00')||Date.parse(at)<Date.parse(from)||Date.parse(at)>Date.parse(until)||!calendar.some(d=>d.date===date)||(prev&&at<=prev.at))throw Error('invalid_market_data');
          rows[symbol].push({at,open:b.o,high:b.h,low:b.l,close:b.c,volume:b.v});
        }
      }
      token=data.next_page_token;if(token==null||token==='')break;if(typeof token!=='string'||!token||token.length>2048||tokens.has(token)||page===2)throw Error('incomplete_history');tokens.add(token);
    }
    const final=shipyardChartslectorClock(await get('https://paper-api.alpaca.markets/v2/clock','official_clock_final'),Date.now()),finish=Date.now();
    if(finish-started>60000||Date.parse(final.timestamp)<Date.parse(initial.timestamp)||shipyardChartslectorDate(final.timestamp)!==endDate)throw Error('source_window_advanced');
    const now=Date.parse(final.timestamp),today=calendar.find(d=>d.date===endDate),isOpen=Boolean(today&&now>=Date.parse(today.open)&&now<Date.parse(today.close));
    if(final.is_open!==isOpen||calendar.filter(d=>Date.parse(d.close)+15*60000<=now).at(-1)?.date!==latest.date)throw Error('source_window_advanced');
    const dates=completed.map(d=>d.date),grid=new Set(dates),cleaned=Object.fromEntries(names.map(symbol=>[symbol,rows[symbol].filter(b=>grid.has(shipyardChartslectorDate(b.at)))]));
    for(const symbol of names){const found=cleaned[symbol];if(found.length!==dates.length||found.some((b,i)=>shipyardChartslectorDate(b.at)!==dates[i]))throw Error('incomplete_session_grid');}
    if(request.signal.aborted)throw Error('cancelled');
    const result=args.symbols.map(symbol=>{const values=SHIPYARD_CHARTSLECTOR.calculateChartslector(cleaned[symbol],cleaned.SPY),latestValues=Object.fromEntries(Object.entries(values).map(([key,v])=>[key,v.at(-1)]));if(Object.values(latestValues).some(v=>v===null))throw Error('calculation_unavailable');
      return {symbol,session_date:latest.date,source_as_of:latest.close,close:cleaned[symbol].at(-1).close,...latestValues,stage:SHIPYARD_CHARTSLECTOR.STAGE_NAMES[latestValues.stage_code],recent_observations:dates.slice(-20).map((date,j)=>({session_date:date,...Object.fromEntries(Object.entries(values).map(([key,v])=>[key,v[v.length-20+j]]))}))};});
    const inputCaptures=await Promise.all(names.map(async symbol=>({symbol,bars:cleaned[symbol].length,first_session:dates[0],last_session:latest.date,last_bar_timestamp:cleaned[symbol].at(-1).at,sha256:await shipyardChartslectorDigest(cleaned[symbol])})));
    const output={...base,status:'computed',computed_at:new Date(finish).toISOString(),source_as_of:latest.close,freshness:'CURRENT_COMPLETED_SESSION',source:{provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Day',received_at:new Date(finish).toISOString(),clock_at:final.timestamp,clock_is_open:final.is_open,source_age_ms:finish-Date.parse(latest.close),publication_guard_minutes:15,request_window:{start:from,end:until},calendar_range:{start_date:startDate,end_date:endDate},calendar,complete_provider_response:true,complete_session_grid:true,grid_basis:'All sessions returned by the official provider; provider calendar omissions are not independently excluded',missing_intervals_filled:false,historical_publication_availability:'unknown; present receipt only',provider_revisions_possible:true,captures},input_captures:inputCaptures,rows:result,
      warnings:['BOUNDED_SYMBOL_SUBSET_NOT_GLOBAL_RANKER','IEX_NOT_CONSOLIDATED','PRESENT_VINTAGE_SPLIT_ADJUSTMENT_NOT_POINT_IN_TIME_BACKTEST','EMA_INITIALIZED_FROM_FETCHED_WINDOW','SIGNAL_PARITY_NOT_PROFITABILITY_VALIDATION','SEPARATE_FROM_LECTOR_DESK_READ'],served_at:new Date(finish).toISOString(),cache_hit:false};
    if(SHIPYARD_CHARTSLECTOR_CACHE.size>50)SHIPYARD_CHARTSLECTOR_CACHE.clear();
    SHIPYARD_CHARTSLECTOR_CACHE.set(cacheKey,{value:output,until:finish+SHIPYARD_CHARTSLECTOR_CACHE_MS});
    return researchResponse(output);
  }catch(error){const allowed=['cancelled','provider_unavailable','calendar_or_clock_unavailable','source_window_advanced','insufficient_history','invalid_market_data','history_bound_exceeded','incomplete_history','incomplete_session_grid','calculation_unavailable'];return json({...base,status:request.signal.aborted?'cancelled':'unavailable',error:allowed.includes(error?.message)?error.message:'chartslector_computation_unavailable',received_at:new Date().toISOString()},request.signal.aborted?408:503);}
}
