// Bounded read-only US equity session metadata; no account/order endpoints.
function shipyardCalendarDate(value) {
  return typeof value==='string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value+'T00:00:00Z')) && new Date(value+'T00:00:00Z').toISOString().slice(0,10)===value;
}
function shipyardCalendarArguments(a) {
  return a && typeof a==='object' && !Array.isArray(a) && Object.keys(a).length===2 && shipyardCalendarDate(a.start_date) && shipyardCalendarDate(a.end_date) && Date.parse(a.end_date)>=Date.parse(a.start_date) && Date.parse(a.end_date)-Date.parse(a.start_date)<=369*86400000;
}
function shipyardCalendarBoundary(date,local) {
  if(typeof local!=='string'||!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(local))throw Error('invalid_calendar');
  const offsetFormat=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',timeZoneName:'longOffset'});
  const offsetAt=ms=>{
    const offsetName=offsetFormat.formatToParts(new Date(ms)).find(p=>p.type==='timeZoneName')?.value;
    const match=/^GMT([+-])(\d{2}):(\d{2})$/.exec(offsetName||'');if(!match)throw Error('invalid_calendar');
    return (match[1]==='-'?-1:1)*(Number(match[2])*60+Number(match[3]));
  };
  // A transition-day midnight can have a different offset from that day's noon.
  // Refine at the actual candidate instant; the strict local roundtrip below
  // still rejects nonexistent wall-clock times rather than shifting them.
  const wall=Date.parse(date+'T'+local+':00Z');
  let candidate=wall-offsetAt(Date.parse(date+'T12:00:00Z'))*60000;
  candidate=wall-offsetAt(candidate)*60000;
  const at=new Date(candidate);
  const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(at).map(p=>[p.type,p.value]));
  if(`${parts.year}-${parts.month}-${parts.day}`!==date||`${parts.hour}:${parts.minute}`!==local)throw Error('invalid_calendar');
  return at.toISOString();
}
async function shipyardExchangeCalendar(request,args,env) {
  const base={schema:'SHIPYARD_EXCHANGE_CALENDAR_V1',requested_range:{start_date:args.start_date,end_date:args.end_date,inclusive:true},source:'Alpaca market calendar v2',market:'US equities',timezone:'America/New_York',restrictions:{market_metadata_only:true,account_data_returned:false,order_submission_enabled:false,engine_executed:false,decision_eligible:false}};
  if(!alpacaRateAllowed(request,Date.now()))return json({...base,status:'unavailable',error:'rate_limited'},429);
  if(typeof env.ALPACA_API_KEY_ID!=='string'||!env.ALPACA_API_KEY_ID||typeof env.ALPACA_API_SECRET_KEY!=='string'||!env.ALPACA_API_SECRET_KEY)return json({...base,status:'unavailable',error:'provider_not_configured'},503);
  try {
    if(request.signal.aborted)throw Error('cancelled');
    const url=new URL('https://paper-api.alpaca.markets/v2/calendar');url.searchParams.set('start',args.start_date);url.searchParams.set('end',args.end_date);
    const response=await fetch(url,{method:'GET',headers:{'APCA-API-KEY-ID':env.ALPACA_API_KEY_ID,'APCA-API-SECRET-KEY':env.ALPACA_API_SECRET_KEY,accept:'application/json'},signal:AbortSignal.any([request.signal,AbortSignal.timeout(8000)]),redirect:'manual'});
    if(!response.ok)throw Error('provider_unavailable');
    const rows=JSON.parse(await readBoundedBody(response,262144)),received=new Date().toISOString();
    if(!Array.isArray(rows)||rows.length>370)throw Error('invalid_calendar');
    const sessions=rows.map((row,i)=>{
      if(!row||!shipyardCalendarDate(row.date)||row.date<args.start_date||row.date>args.end_date||(i&&row.date<=rows[i-1].date)||typeof row.open!=='string'||typeof row.close!=='string'||row.open<'04:00'||row.close>'20:00'||row.open>=row.close)throw Error('invalid_calendar');
      const open=shipyardCalendarBoundary(row.date,row.open),close=shipyardCalendarBoundary(row.date,row.close),minutes=(Date.parse(close)-Date.parse(open))/60000;
      if(minutes<=0||minutes>960)throw Error('invalid_calendar');
      return {date:row.date,open,close,open_local:row.open,close_local:row.close,session_minutes:minutes};
    });
    if(request.signal.aborted)throw Error('cancelled');
    return researchResponse({...base,status:'available',received_at:received,complete_provider_response:true,calendar:sessions,session_count:sessions.length,non_session_dates:'No synthetic sessions inserted. Only sessions explicitly returned by the official provider are included; absence is not independently verified.',historical_publication_availability:'unknown; present receipt only',provider_revisions_possible:true});
  }catch(error){return json({...base,status:request.signal.aborted?'cancelled':'unavailable',error:['invalid_calendar','provider_unavailable','cancelled'].includes(error?.message)?error.message:'calendar_read_failed',received_at:new Date().toISOString()},request.signal.aborted?408:503);}
}
