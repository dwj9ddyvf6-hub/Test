// Deterministic, invented values for FE02 regression tests only; never provider data.
import {createHash} from 'node:crypto';

const zone=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',timeZoneName:'longOffset'});
export function boundary(date,time){
  const name=zone.formatToParts(new Date(date+'T12:00:00Z')).find(part=>part.type==='timeZoneName').value;
  return new Date(date+'T'+time+':00'+name.slice(3)).toISOString();
}
export function series(symbol='QQQ'){
  const spy=[],target=[];
  for(let index=0;index<505;index++){
    const benchmarkLog=.00002*index+.000001*index*index+.003*Math.sin(index/9)+.002*Math.cos(index/21);
    const residualShock=.002*Math.sin(index*1.7)+.001*Math.cos(index/7)+.0004*Math.sin(index/31);
    spy.push(Math.exp(benchmarkLog));
    target.push(Math.exp(.00001*index+.000002*index*index+1.25*benchmarkLog+residualShock));
  }
  return {SPY:spy,[symbol]:target};
}
export function fixture({symbol='QQQ',evaluationAt='2026-10-29T19:40:00.000Z'}={}){
  const dates=[];
  for(let ms=Date.parse('2026-10-28T12:00:00Z');dates.length<505;ms-=86400000){
    const date=new Date(ms).toISOString().slice(0,10),weekday=new Date(ms).getUTCDay();
    if(weekday!==0&&weekday!==6)dates.unshift(date);
  }
  const closes=series(symbol),sessions=dates.map(date=>({date,open:boundary(date,'09:30'),close:boundary(date,'16:00')}));
  const barsBySymbol={};
  for(const name of [symbol,'SPY'])barsBySymbol[name]=dates.map((date,index)=>{
    const close=closes[name][index];return {t:boundary(date,'00:00'),o:close,h:close,l:close,c:close,v:100};
  });
  const today=evaluationAt.slice(0,10),rangeStart='2024-08-20',evaluationMs=Date.parse(evaluationAt);
  const calendarStarted=new Date(evaluationMs-20000).toISOString(),calendarReceived=new Date(evaluationMs-15000).toISOString();
  const requestedWindow={start:barsBySymbol[symbol][0].t,end:sessions.at(-1).close,end_exclusive:true};
  const calendarUrl=new URL('https://paper-api.alpaca.markets/v2/calendar');calendarUrl.searchParams.set('start',rangeStart);calendarUrl.searchParams.set('end',today);
  const calendarCapture={operation:'official_calendar',subject:'US_EQUITY',request_started_at:calendarStarted,
    http_response_received_at:calendarReceived,received_at:calendarReceived,response_sha256:createHash('sha256').update('synthetic-calendar').digest('hex'),
    request_url:calendarUrl.toString(),http_status:200,hash_serialization:'UTF-8 re-encoding of decoded response text'};
  const captures=[symbol,'SPY'].map(name=>{
    const url=new URL(`https://data.alpaca.markets/v2/stocks/${name}/bars`);
    for(const [key,value] of Object.entries({timeframe:'1Day',start:requestedWindow.start,end:new Date(Date.parse(requestedWindow.end)-1).toISOString(),feed:'iex',adjustment:'split',currency:'USD',asof:today,sort:'asc',limit:'1000'}))url.searchParams.set(key,value);
    return {operation:`history_${name}_1Day_page_1`,subject:name,request_started_at:new Date(evaluationMs-10000).toISOString(),
      http_response_received_at:new Date(evaluationMs-5000).toISOString(),received_at:new Date(evaluationMs-5000).toISOString(),
      response_sha256:createHash('sha256').update(name).digest('hex'),request_url:url.toString(),http_status:200,
      hash_serialization:'UTF-8 re-encoding of decoded response text',provider_rows:505,has_next_page:false};
  });
  return {symbol,benchmark_symbol:'SPY',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:today,evaluation_at:evaluationAt,
    calendar:{sessions,received_at:calendarReceived,requested_range:{start_date:rangeStart,end_date:today},complete_provider_response:true},calendar_capture:calendarCapture,
    bars_by_symbol:barsBySymbol,requested_window:requestedWindow,captures,pagination_complete:true};
}
