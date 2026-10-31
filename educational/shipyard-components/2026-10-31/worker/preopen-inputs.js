// Fixed-roster immutable input capture. No strategy decisions/accounts/orders.
const SHIPYARD_PREOPEN_CONFIG='PREOPEN_SPY_QQQ_RAW_IEX_V1';
const SHIPYARD_PREOPEN_SYMBOLS=['SPY','QQQ'];
const SHIPYARD_PREOPEN_CAP=44000;
function shipyardPreopenArguments(name,a){
 if(!a||typeof a!=='object'||Array.isArray(a))return false;
 if(name==='shipyard_preopen_status')return Object.keys(a).every(k=>k==='check_inputs')&&(a.check_inputs===undefined||typeof a.check_inputs==='boolean');
 if(name==='shipyard_capture_preopen_inputs')return Object.keys(a).length===1&&['capture','diagnostic'].includes(a.mode);
 return Object.keys(a).length===2&&SHIPYARD_PREOPEN_SYMBOLS.includes(a.symbol)&&shipyardCalendarDate(a.target_session);
}
function shipyardPreopenBase(){return {schema:'SHIPYARD_PREOPEN_INPUTS_V1',config_version:SHIPYARD_PREOPEN_CONFIG,symbols:SHIPYARD_PREOPEN_SYMBOLS,provider:'Alpaca Market Data',feed:'iex',adjustment:'raw',restrictions:{inputs_only:true,reference_computed:false,engine_executed:false,decision_eligible:false,account_data_returned:false,order_submission_enabled:false,continuous_collection:false},bounds:{max_provider_reads:3,max_body_bytes:2359296,max_record_bytes:SHIPYARD_PREOPEN_CAP,max_sessions_per_symbol:400,max_storage_bytes:134217728,retention:'Pause at cap; no automatic deletion.'},note:'Genuine preopen receipts can support later reference construction. Historical availability/event gates/full engine warmup remain separate. This tool does not schedule itself; the separate weekday Site automation invokes its capture writer.'};}
function shipyardPreopenMeta(row){return row?{id:row.id,config_version:row.config_version,target_session:row.target_session,symbol:row.symbol,source_received_at:row.source_received_at,persisted_at:row.persisted_at,cutoff_at:row.cutoff_at,input_hash:row.input_hash,bytes:row.bytes}:null;}
async function shipyardPreopenRow(env,id){return env.DB.prepare('SELECT id,config_version,target_session,symbol,source_received_at,persisted_at,cutoff_at,input_hash,payload_json,bytes FROM shipyard_preopen_inputs WHERE id=?').bind(id).first();}
async function shipyardPreopenVerifiedRow(env,id,day,symbol){
 const row=await shipyardPreopenRow(env,id);if(!row)return null;
 if(row.config_version!==SHIPYARD_PREOPEN_CONFIG||row.symbol!==symbol||row.target_session!==day||row.bytes>SHIPYARD_PREOPEN_CAP||new TextEncoder().encode(row.payload_json).length!==row.bytes)throw Error('stored_capture_invalid');
 const payload=JSON.parse(row.payload_json),receipt=Date.parse(row.source_received_at),persisted=Date.parse(row.persisted_at),cutoff=Date.parse(row.cutoff_at);
 if(payload.schema!=='SHIPYARD_FROZEN_PREOPEN_INPUT_V1'||payload.config_version!==SHIPYARD_PREOPEN_CONFIG||payload.diagnostic!==false||payload.preopen_receipt_eligible!==true||payload.symbol!==symbol||payload.target_session!==day||!Number.isFinite(receipt)||!Number.isFinite(persisted)||!Number.isFinite(cutoff)||receipt>persisted||persisted>=cutoff||await SHIPYARD_RESEARCH_LOGIC_HASH(row.payload_json)!==row.input_hash)throw Error('stored_capture_invalid');
 return row;
}
async function shipyardPreopenId(day,symbol){return 'preopen:'+await SHIPYARD_RESEARCH_LOGIC_HASH(`${SHIPYARD_PREOPEN_CONFIG}:${day}:${symbol}`);}
async function shipyardPreopenCalendar(request,env){
 const today=newYorkDate(new Date()),start=new Date(Date.parse(today+'T00:00:00Z')-180*86400000).toISOString().slice(0,10);
 const response=await shipyardExchangeCalendar(request,{start_date:start,end_date:today},env),data=await response.json();
 if(!response.ok||data.status!=='available'||!data.complete_provider_response)throw Error('calendar_unavailable');
 const target=data.calendar.find(s=>s.date===today),previous=data.calendar.filter(s=>s.date<today).at(-1);
 if(!previous)throw Error('previous_session_unavailable');
 const windowStart=shipyardCalendarBoundary(today,'08:00'),cutoff=target?new Date(Date.parse(target.open)-60000).toISOString():null;
 return {data,today,target,previous,start,windowStart,cutoff};
}
function shipyardPreopenGate(c,now=Date.now()){
 if(!c.target)return 'closed';if(now<Date.parse(c.windowStart))return 'too_early';if(now>=Date.parse(c.cutoff))return 'too_late';return 'open';
}
async function shipyardPreopenSources(request,env,c){
 let reads=1,bytes=0;
 const get=async(frame,start,end)=>{
  if(++reads>3||!alpacaRateAllowed(request,Date.now()))throw Error('rate_limited');
  const url=new URL('https://data.alpaca.markets/v2/stocks/bars');
  for(const [k,v] of Object.entries({symbols:'SPY,QQQ',timeframe:frame,start,end:new Date(Date.parse(end)-1).toISOString(),adjustment:'raw',feed:'iex',sort:'asc',limit:'5000'}))url.searchParams.set(k,v);
  const response=await fetch(url,{headers:{'APCA-API-KEY-ID':env.ALPACA_API_KEY_ID,'APCA-API-SECRET-KEY':env.ALPACA_API_SECRET_KEY,accept:'application/json'},redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(5000)])});
  if(!response.ok)throw Error('provider_unavailable');const text=await readBoundedBody(response,1048576);bytes+=new TextEncoder().encode(text).length;if(bytes>2097152)throw Error('source_bound_exceeded');
  const payload=JSON.parse(text),received_at=new Date().toISOString();
  if(payload.next_page_token||!payload.bars||typeof payload.bars!=='object'||Array.isArray(payload.bars)||Object.keys(payload.bars).some(s=>!SHIPYARD_PREOPEN_SYMBOLS.includes(s)))throw Error('provider_history_incomplete');
  const bars={};
  for(const symbol of SHIPYARD_PREOPEN_SYMBOLS){const raw=payload.bars[symbol];if(!Array.isArray(raw)||!raw.length||raw.length>(frame==='1Day'?180:100))throw Error('invalid_market_data');bars[symbol]=raw.map(shipyardApertureBar);if(bars[symbol].some((b,i)=>Date.parse(b.t)<Date.parse(start)||Date.parse(b.t)>=Date.parse(end)||(i&&b.t<=bars[symbol][i-1].t)))throw Error('invalid_market_data');}
  return {bars,received_at,request:{frame,start,end},provider_revisions_possible:true};
 };
 const daily=await get('1Day',c.start+'T00:00:00Z',c.previous.close);
 const five=await get('5Min',c.previous.open,c.previous.close);
 const requiredDays=c.data.calendar.filter(s=>s.date<c.today).map(s=>s.date);
 if(requiredDays.length<20)throw Error('insufficient_daily_history');
 for(const symbol of SHIPYARD_PREOPEN_SYMBOLS){
  const days=daily.bars[symbol].map(b=>newYorkDate(new Date(b.t)));
  if(days.length!==requiredDays.length||days.some((d,i)=>d!==requiredDays[i]))throw Error('daily_session_gap');
  const count=(Date.parse(c.previous.close)-Date.parse(c.previous.open))/300000;
  if(five.bars[symbol].length!==count||five.bars[symbol].some((b,i)=>Date.parse(b.t)!==Date.parse(c.previous.open)+i*300000))throw Error('prior_session_grid_gap');
 }
 return {daily,five,provider_reads:reads,decoded_bytes:bytes};
}
async function shipyardPreopenTool(request,args,env,operation){
 const base=shipyardPreopenBase();
 if(operation==='write'&&env.SHIPYARD_PREOPEN_CAPTURE_DISABLED==='true')return researchResponse({...base,status:'disabled',preopen_receipt_eligible:false});
 if(!env.DB)return json({...base,status:'blocked',error:'database_unavailable'},503);
 const boundedRequest=new Request(request.url,{method:'GET',headers:request.headers,signal:AbortSignal.any([request.signal,AbortSignal.timeout(45000)])});
 try{
  if(operation==='read'){
   const row=await shipyardPreopenVerifiedRow(env,await shipyardPreopenId(args.target_session,args.symbol),args.target_session,args.symbol);
   if(!row)return researchResponse({...base,status:'not_captured',target_session:args.target_session,symbol:args.symbol});
   if(row.config_version!==SHIPYARD_PREOPEN_CONFIG||row.symbol!==args.symbol||row.target_session!==args.target_session||row.bytes>SHIPYARD_PREOPEN_CAP)throw Error('stored_capture_invalid');
   const payload=JSON.parse(row.payload_json);if(payload.schema!=='SHIPYARD_FROZEN_PREOPEN_INPUT_V1'||payload.diagnostic===true||await SHIPYARD_RESEARCH_LOGIC_HASH(row.payload_json)!==row.input_hash)throw Error('stored_capture_invalid');
   return researchResponse({...base,status:'captured_inputs',metadata:shipyardPreopenMeta(row),inputs:payload});
  }
  if(operation==='write'&&args.mode==='diagnostic'){
   // Constant synthetic transport proof only, never a market/reference record.
   const id='preopen:diagnostic:v1',payload='{"schema":"SHIPYARD_CAPTURE_DIAGNOSTIC_V1","diagnostic":true,"preopen_receipt_eligible":false,"market_data":false}',hash=await SHIPYARD_RESEARCH_LOGIC_HASH(payload);
   await env.DB.prepare("INSERT OR IGNORE INTO shipyard_preopen_inputs (id,config_version,target_session,symbol,source_received_at,persisted_at,cutoff_at,input_hash,payload_json,bytes) VALUES (?,'DIAGNOSTIC_V1','diagnostic','NONE',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),'not_applicable',?,?,?)").bind(id,hash,payload,new TextEncoder().encode(payload).length).run();
   const row=await shipyardPreopenRow(env,id);if(!row||row.payload_json!==payload||row.input_hash!==hash)throw Error('diagnostic_readback_failed');
   return researchResponse({...base,status:'diagnostic_verified',diagnostic:true,preopen_receipt_eligible:false,metadata:shipyardPreopenMeta(row)});
  }
  const totals=await env.DB.prepare('SELECT COUNT(*) AS records,COALESCE(SUM(bytes),0) AS bytes FROM shipyard_preopen_inputs').first();
  const c=await shipyardPreopenCalendar(boundedRequest,env),gate=shipyardPreopenGate(c),enabled=env.SHIPYARD_PREOPEN_CAPTURE_DISABLED!=='true';
  const existing=await Promise.all(SHIPYARD_PREOPEN_SYMBOLS.map(async symbol=>shipyardPreopenVerifiedRow(env,await shipyardPreopenId(c.today,symbol),c.today,symbol)));
  const status={...base,enabled,target_session:c.target?c.today:null,window_start:c.target?c.windowStart:null,cutoff_at:c.cutoff,window_status:gate,storage:totals,existing:existing.map(shipyardPreopenMeta),calendar_received_at:c.data.received_at};
  if(operation==='status'&&!args.check_inputs)return researchResponse({...status,status:'status',would_capture_now:enabled&&gate==='open'});
  if(operation==='write'&&(!enabled||gate!=='open'))return researchResponse({...status,status:enabled?gate:'disabled',preopen_receipt_eligible:false});
  if(operation==='write'&&existing.every(Boolean))return researchResponse({...status,status:'already_captured',captures:existing.map(shipyardPreopenMeta)});
  const sources=await shipyardPreopenSources(boundedRequest,env,c);
  if(operation==='status')return researchResponse({...status,status:'preflight_ok',would_capture_now:enabled&&shipyardPreopenGate(c)==='open',provider_reads:sources.provider_reads,source_receipts:{daily:sources.daily.received_at,prior_5m:sources.five.received_at},counts:Object.fromEntries(SHIPYARD_PREOPEN_SYMBOLS.map(s=>[s,{daily:sources.daily.bars[s].length,prior_5m:sources.five.bars[s].length}])),database_write_verified:false,preopen_receipt_eligible:false});
  if(shipyardPreopenGate(c)!=='open'||boundedRequest.signal.aborted)throw Error('capture_cutoff_crossed');
  if([c.data.received_at,sources.daily.received_at,sources.five.received_at].some(at=>!shipyardStrictInstant(at)||Date.parse(at)<Date.parse(c.windowStart)||Date.parse(at)>=Date.parse(c.cutoff)))throw Error('capture_cutoff_crossed');
  const captures=[];
  for(let i=0;i<SHIPYARD_PREOPEN_SYMBOLS.length;i++){
   const symbol=SHIPYARD_PREOPEN_SYMBOLS[i];if(existing[i]){captures.push(shipyardPreopenMeta(existing[i]));continue;}
   const payload={schema:'SHIPYARD_FROZEN_PREOPEN_INPUT_V1',config_version:SHIPYARD_PREOPEN_CONFIG,symbol,target_session:c.today,diagnostic:false,preopen_receipt_eligible:true,reference_computed:false,engine_executed:false,provider:'Alpaca',feed:'iex',adjustment:'raw',target_open:c.target.open,cutoff_at:c.cutoff,calendar_received_at:c.data.received_at,source_receipts:{daily:sources.daily.received_at,prior_5m:sources.five.received_at},daily_bars:sources.daily.bars[symbol],prior_5m_bars:sources.five.bars[symbol],calendar:c.data.calendar.map(({date,open,close})=>({date,open,close})),historical_publication_availability:'unknown',provider_revisions_possible:true};
   const text=JSON.stringify(payload),bytes=new TextEncoder().encode(text).length;if(bytes>SHIPYARD_PREOPEN_CAP)throw Error('capture_size_exceeded');
   const id=await shipyardPreopenId(c.today,symbol),hash=await SHIPYARD_RESEARCH_LOGIC_HASH(text),receipt=sources.five.received_at;
   if(shipyardPreopenGate(c)!=='open'||boundedRequest.signal.aborted)throw Error('capture_cutoff_crossed');
   await env.DB.prepare("INSERT OR IGNORE INTO shipyard_preopen_inputs (id,config_version,target_session,symbol,source_received_at,persisted_at,cutoff_at,input_hash,payload_json,bytes) SELECT ?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?,?,?,? WHERE strftime('%Y-%m-%dT%H:%M:%fZ','now')>=? AND strftime('%Y-%m-%dT%H:%M:%fZ','now')<? AND (SELECT COUNT(*) FROM shipyard_preopen_inputs WHERE config_version=? AND symbol=?)<400 AND (SELECT COALESCE(SUM(bytes),0) FROM shipyard_preopen_inputs)+?<=134217728").bind(id,SHIPYARD_PREOPEN_CONFIG,c.today,symbol,receipt,c.cutoff,hash,text,bytes,c.windowStart,c.cutoff,SHIPYARD_PREOPEN_CONFIG,symbol,bytes).run();
   const row=await shipyardPreopenVerifiedRow(env,id,c.today,symbol);if(!row)throw Error('database_cutoff_or_storage_cap');captures.push(shipyardPreopenMeta(row));
  }
  return researchResponse({...status,status:'captured_inputs',captures,provider_reads:sources.provider_reads,preopen_receipt_eligible:true});
 }catch(error){const allowed=['calendar_unavailable','previous_session_unavailable','rate_limited','provider_unavailable','provider_history_incomplete','invalid_market_data','source_bound_exceeded','insufficient_daily_history','daily_session_gap','prior_session_grid_gap','stored_capture_invalid','diagnostic_readback_failed','capture_cutoff_crossed','capture_size_exceeded','database_cutoff_or_storage_cap'];return json({...base,status:'blocked',error:allowed.includes(error?.message)?error.message:'capture_unavailable',preopen_receipt_eligible:false,partial_persistence_possible:operation==='write'},503);}
}
