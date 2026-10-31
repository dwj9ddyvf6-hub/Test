// Invented data/calendar responses only. Holidays are explicit fixture omissions, not a calendar fallback.
import {fixture as original,boundary} from './fe02-synthetic.mjs';
export {boundary};
export function fixture({lastDate='2026-10-23',evaluationAt='2026-10-26T14:00:00.000Z',extraSessions=null,earlyClose=false,symbol='QQQ'}={}){
  const input=original({symbol}),dates=[];
  for(let ms=Date.parse(lastDate+'T12:00:00Z');dates.length<505;ms-=86400000)if(![0,6].includes(new Date(ms).getUTCDay()))dates.unshift(new Date(ms).toISOString().slice(0,10));
  const et=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
  const today=et.format(new Date(evaluationAt)),evaluationMs=Date.parse(evaluationAt),stamp=delay=>new Date(evaluationMs-delay).toISOString();
  const from=new Date(Date.parse(today+'T12:00:00Z')-800*86400000).toISOString().slice(0,10);
  const sessions=dates.map((date,i)=>({date,open:boundary(date,'09:30'),close:boundary(date,earlyClose&&i===504?'13:00':'16:00')}));
  const completedClose=sessions.at(-1).close;
  if(extraSessions!==null)sessions.push(...extraSessions.map(date=>({date,open:boundary(date,'09:30'),close:boundary(date,'16:00')})));
  else if(today>lastDate&&![0,6].includes(new Date(today+'T12:00:00Z').getUTCDay()))sessions.push({date:today,open:boundary(today,'09:30'),close:boundary(today,'16:00')});
  input.evaluation_at=evaluationAt;input.symbol_asof=today;
  input.calendar={sessions,received_at:stamp(15000),requested_range:{start_date:from,end_date:today},complete_provider_response:true};
  input.requested_window={start:boundary(dates[0],'00:00'),end:completedClose,end_exclusive:true};
  Object.assign(input.calendar_capture,{request_started_at:stamp(20000),http_response_received_at:stamp(15000),received_at:stamp(15000),request_url:`https://paper-api.alpaca.markets/v2/calendar?start=${from}&end=${today}`});
  for(const name of [symbol,'SPY'])input.bars_by_symbol[name].forEach((bar,i)=>bar.t=boundary(dates[i],'00:00'));
  for(const receipt of input.captures){
    Object.assign(receipt,{request_started_at:stamp(10000),http_response_received_at:stamp(5000),received_at:stamp(5000)});
    const url=new URL(receipt.request_url);url.searchParams.set('start',input.requested_window.start);url.searchParams.set('end',new Date(Date.parse(completedClose)-1).toISOString());url.searchParams.set('asof',today);receipt.request_url=url.toString();
  }
  return input;
}
