// Synthetic-only FE03 market/calendar fixture. No live observations or provider data.
import {createHash} from 'node:crypto';
import {boundary as baseBoundary} from './fe01-synthetic.mjs';

export const boundary=baseBoundary;
const sha=value=>createHash('sha256').update(value).digest('hex');
function datesEnding(lastDate,count){
 const dates=[];for(let ms=Date.parse(lastDate+'T12:00:00Z');dates.length<count;ms-=86400000){
  const day=new Date(ms).getUTCDay();if(day!==0&&day!==6)dates.unshift(new Date(ms).toISOString().slice(0,10));
 }
 return dates;
}
function addDays(day,n){return new Date(Date.parse(day+'T12:00:00Z')+n*86400000).toISOString().slice(0,10);}
function makeRows({candidateAge=3,matureEpisodes=23,candidate=true,invalidated=false,breachAndReclaim=false,earlyClose=false}={}){
 const dates=datesEnding('2026-10-30',505),rows=dates.map((date,index)=>({date,o:95,h:96,l:94,c:95,v:100+(index%7)}));
 const eventStarts=[];
 const count=Math.max(0,Math.min(23,matureEpisodes));
 const spacing=count>1?Math.floor((483-21)/(count-1)):463;
 for(let n=0;n<count;n++)eventStarts.push(21+n*spacing);
 for(const u of eventStarts){
  const level=Math.max(...rows.slice(u-20,u).map(row=>row.h)),close=level*1.02;
  rows[u]={...rows[u],o:close,h:close*1.001,l:level*0.999,c:close};
  const labelFalse=(n=>n%3!==0)(eventStarts.indexOf(u));
  for(let j=1;j<=5;j++){
   const value=labelFalse?level*0.99:level*1.001;
   rows[u+j]={...rows[u+j],o:value,h:value*1.0005,l:Math.min(value,level*0.98),c:value};
  }
 }
 let candidateIndex=null;
 if(candidate){
  candidateIndex=rows.length-1-candidateAge;
  const level=Math.max(...rows.slice(candidateIndex-20,candidateIndex).map(row=>row.h)),close=level*1.02;
  rows[candidateIndex]={...rows[candidateIndex],o:close,h:close*1.001,l:level*0.999,c:close};
  for(let j=1;j<=candidateAge;j++){
   let value=level*1.001;
   if(invalidated&&j===candidateAge)value=level*0.99;
   else if(breachAndReclaim&&j===1)value=level*0.99;
   rows[candidateIndex+j]={...rows[candidateIndex+j],o:value,h:Math.max(value,level*1.0005),l:Math.min(value,level*0.98),c:value};
  }
 }
 return {dates,rows,candidateIndex,earlyClose};
}

export function fixture(options={}){
 const {dates,rows,candidateIndex,earlyClose}=makeRows(options),lastDate=dates.at(-1);
 const sessions=dates.map((date,index)=>({date,open:boundary(date,'09:30'),close:boundary(date,earlyClose&&index===504?'13:00':'16:00')}));
 const evaluationMs=Date.parse(sessions.at(-1).close)+900001,evaluation_at=new Date(evaluationMs).toISOString();
 const today=lastDate,rangeStart=addDays(today,-800),from=rangeStart,end=today;
 const bars=rows.map((row,index)=>({t:boundary(row.date,'00:00'),o:row.o,h:row.h,l:row.l,c:row.c,v:row.v}));
 const window={start:bars[0].t,end:sessions.at(-1).close,end_exclusive:true};
 const requestStarted=new Date(evaluationMs-20000).toISOString(),responseReceived=new Date(evaluationMs-15000).toISOString();
 const calendarPayload=JSON.stringify(sessions.map(session=>({date:session.date,open:'09:30',close:earlyClose&&session.date===lastDate?'13:00':'16:00'})));
 const calendarCapture={operation:'official_calendar',subject:'US_EQUITY',request_started_at:requestStarted,http_response_received_at:responseReceived,received_at:responseReceived,
  response_sha256:sha(calendarPayload),hash_serialization:'UTF-8 re-encoding of decoded response text',request_url:`https://paper-api.alpaca.markets/v2/calendar?start=${from}&end=${end}`,http_status:200};
 const historyPayload=JSON.stringify({symbol:'SPY',bars,next_page_token:null});
 const historyCapture={operation:'history_1Day_page_1',subject:'SPY',request_started_at:new Date(evaluationMs-10000).toISOString(),
  http_response_received_at:new Date(evaluationMs-5000).toISOString(),received_at:new Date(evaluationMs-5000).toISOString(),response_sha256:sha(historyPayload),
  hash_serialization:'UTF-8 re-encoding of decoded response text',request_url:'',http_status:200,provider_rows:bars.length,has_next_page:false};
 const query=new URLSearchParams({timeframe:'1Day',start:window.start,end:new Date(Date.parse(window.end)-1).toISOString(),feed:'iex',adjustment:'split',currency:'USD',asof:today,sort:'asc',limit:'1000'});
 historyCapture.request_url=`https://data.alpaca.markets/v2/stocks/SPY/bars?${query}`;
 return {symbol:'SPY',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:today,evaluation_at,
  calendar:{sessions,received_at:responseReceived,requested_range:{start_date:from,end_date:end},complete_provider_response:true},calendar_capture:calendarCapture,
  bars,requested_window:window,captures:[historyCapture],pagination_complete:true,_rows:rows,_candidate_index:candidateIndex};
}
