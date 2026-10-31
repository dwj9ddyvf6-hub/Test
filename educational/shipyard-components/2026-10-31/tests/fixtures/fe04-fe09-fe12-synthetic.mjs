import {createHash} from 'node:crypto';
const digest=x=>createHash('sha256').update(typeof x==='string'?x:JSON.stringify(x)).digest('hex');
export const sha=x=>digest(x);
const dateOk=s=>/^\d{4}-\d\d-\d\d$/.test(s);
export function etInstant(date,clock){
 const sample=new Date(`${date}T12:00:00Z`),name=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',timeZoneName:'longOffset'}).formatToParts(sample).find(p=>p.type==='timeZoneName').value;
 const m=/^GMT([+-])(\d\d):(\d\d)$/.exec(name);if(!m)throw Error('fixture timezone');const offset=(m[1]==='-'?-1:1)*(Number(m[2])*60+Number(m[3]));
 return new Date(Date.parse(`${date}T${clock}:00Z`)-offset*60000).toISOString();
}
export function businessDates(end,count){const out=[];let t=Date.parse(`${end}T00:00:00Z`);while(out.length<count){const d=new Date(t),w=d.getUTCDay(),s=d.toISOString().slice(0,10);if(w>=1&&w<=5)out.push(s);t-=86400000;}return out.reverse();}
export function session(date,close='16:00'){return {date,open:etInstant(date,'09:30'),close:etInstant(date,close)};}
function calendarRows(rows,receivedAt){return {complete_provider_response:true,received_at:receivedAt,requested_range:{start_date:rows[0].date,end_date:rows.at(-1).date},sessions:rows};}
function capture(operation,request,received,extra={}){return {operation,request_started_at:request,http_response_received_at:received,received_at:received,http_status:200,response_sha256:digest(operation+'|'+request+'|'+received),hash_serialization:'UTF-8 re-encoding of decoded response text',response_bytes:Math.min(1000,extra.response_bytes??1000),...extra};}
function candle(t,o,c,v=1000){return {t,o,h:Math.max(o,c)+0.01,l:Math.min(o,c)-0.01,c,v};}

export function makeFE04Fixture(){
 const dates=businessDates('2026-10-30',62),sessions=dates.map((d,i)=>session(d,i===10?'13:00':'16:00')),current=sessions.at(-1),evalAt=etInstant(current.date,'09:40'),accepted=Date.parse(current.open)+300000;
 const offsets={SPY:0,QQQ:0.5,IWM:1.1},gaps={SPY:[],QQQ:[],IWM:[]},barsBySymbol={};
 for(const symbol of ['SPY','QQQ','IWM']){
  const k=offsets[symbol];for(let i=0;i<61;i++){const core=0.0011*Math.sin(i*0.61)+0.0007*Math.cos(i*0.27)+0.00015*Math.sin(i*1.37);gaps[symbol].push(symbol==='SPY'?core:symbol==='QQQ'?0.68*core+0.001*Math.sin(i*0.43+k):-.16*core+0.0014*Math.cos(i*0.52+k));}
  const rows=[];let priorClose=100+k;
  for(let i=0;i<62;i++){
   const s=sessions[i],openMs=Date.parse(s.open),closeMs=Date.parse(s.close),g=i===0?0:gaps[symbol][i-1],open=priorClose*Math.exp(g),sign=g===0?1:Math.sign(g);
   if(i>=41){for(let j=0;j<5;j++){const t=new Date(openMs-300000+j*60000).toISOString(),c=open*(0.998+0.00003*j);rows.push(candle(t,c,c+0.001,900+i*13+j*3+k*20));}}
   if(i>0){const c=open*(1+sign*0.00003);rows.push(candle(new Date(openMs).toISOString(),open,c,1100+i+k*10));}
   if(i===61){for(let j=1;j<5;j++){const c=open*(1+sign*0.00003*(j+1));rows.push(candle(new Date(openMs+j*60000).toISOString(),open*(1+sign*0.00003*j),c,1000+j*50+k*10));}}
   if(i<61){const close=100+k+i*0.19+0.17*Math.sin(i*0.31+k);rows.push(candle(new Date(closeMs-60000).toISOString(),close-0.03,close,1500+i*7+k*30));priorClose=close;}
  }
  rows.sort((a,b)=>Date.parse(a.t)-Date.parse(b.t));barsBySymbol[symbol]=rows;
 }
 const request=etInstant(current.date,'09:36'),received=etInstant(current.date,'09:37'),calendarRange={start_date:dates[0],end_date:dates.at(-1)},captures=[capture('official_calendar',request,received,{request_url:`https://paper-api.alpaca.markets/v2/calendar?start=${calendarRange.start_date}&end=${calendarRange.end_date}`,response_bytes:10000})];
 for(const symbol of ['SPY','QQQ','IWM']){
  const retained=barsBySymbol[symbol].length,pageProvider=[10000,10000,10000,10000,10000,8955],pageRetained=Array(6).fill(0);let left=retained;for(let i=0;i<6;i++){pageRetained[i]=Math.min(left,[50,50,50,50,20,12][i]);left-=pageRetained[i];}
  for(let i=0;i<6;i++){const page=i+1,params=new URLSearchParams({timeframe:'1Min',start:new Date(Date.parse(sessions[0].close)-60000).toISOString(),end:new Date(Date.parse(current.open)+5*60000-1).toISOString(),feed:'iex',adjustment:'split',sort:'asc',limit:'10000',...(page>1?{page_token:'[continuation]'}:{})});captures.push(capture(`history_1Min_${symbol}_page_${page}`,request,received,{request_url:`https://data.alpaca.markets/v2/stocks/${symbol}/bars?${params}`,provider_rows:pageProvider[i],retained_rows:pageRetained[i],has_next_page:i<5,response_bytes:1400000}));}
 }
 return {symbol:'QQQ',feed:'iex',adjustment:'split',timeframe:'1Min',evaluation_at:evalAt,pagination_complete:true,calendar:calendarRows(sessions,received),bars_by_symbol:barsBySymbol,captures,gaps,sessions};
}

function fe09Bars(sessions){const bars=[];let priorClose=100;for(let d=0;d<sessions.length;d++){const s=sessions[d],open=Date.parse(s.open),n=(Date.parse(s.close)-open)/300000,base=100+d*0.23+0.2*Math.sin(d*0.4),dayGap=0.001*Math.sin(d*0.69)+0.0003*Math.cos(d*0.33),dayOpen=priorClose*Math.exp(dayGap);let prev=dayOpen;
  for(let i=0;i<n;i++){let r=0.00025*Math.sin(d*2.1+i*0.83)+0.00013*Math.cos(d*0.73+i*1.37);if(i===10&&d%3===0)r+=0.0025+0.00015*(d%7);if(i===30&&d%4===1)r-=0.0016;const o=i===0?dayOpen:prev,c=o*Math.exp(r);bars.push(candle(new Date(open+i*300000).toISOString(),o,c,2500+i*11+d*17));prev=c;}
  priorClose=prev;
 }
 return bars;}
export function makeFE09Fixture({currentDate='2026-10-30'}={}){
 const priorDates=businessDates(currentDate,22),futureDates=[];let next=Date.parse(currentDate+'T00:00:00Z');while(futureDates.length<5){next+=86400000;const d=new Date(next),weekday=d.getUTCDay();if(weekday>=1&&weekday<=5)futureDates.push(d.toISOString().slice(0,10));}
 let sessions=priorDates.map((d,i)=>session(d,i===9?'13:00':'16:00')).concat(futureDates.map(d=>session(d)));sessions.sort((a,b)=>a.date.localeCompare(b.date));
 const evalAt=etInstant(currentDate,'16:20'),received=etInstant(currentDate,'16:19'),bars=fe09Bars(sessions.slice(0,22)),request=etInstant(currentDate,'16:15'),range={start_date:sessions[0].date,end_date:sessions.at(-1).date},barsParams=new URLSearchParams({timeframe:'5Min',start:sessions[0].open,end:new Date(Date.parse(sessions[21].close)-1).toISOString(),feed:'iex',adjustment:'split',sort:'asc',limit:'5000'}),captures=[capture('official_calendar',request,received,{request_url:`https://paper-api.alpaca.markets/v2/calendar?start=${range.start_date}&end=${range.end_date}`,response_bytes:10000}),capture('history_5Min_page_1',request,received,{request_url:`https://data.alpaca.markets/v2/stocks/SPY/bars?${barsParams}`,provider_rows:bars.length,has_next_page:false,response_bytes:500000})];
 const sourceRows=month=>[['BEA','bea_release_date_json','https://apps.bea.gov/API/signup/release_dates.json'],['BLS','bls_published_calendar','https://www.bls.gov/schedule/news_release/bls.ics'],['Federal Reserve','federal_reserve_board_monthly_calendar',`https://www.federalreserve.gov/newsevents/${month.slice(0,4)}-${['january','february','march','april','may','june','july','august','september','october','november','december'][Number(month.slice(5,7))-1]}.htm`]].map(([source,coverage_scope,url])=>({source,status:'parsed',scope_complete:true,coverage_scope,received_at:received,raw_sha256:digest(source+month),url}));
 const eventAt=etInstant(futureDates[1],'10:00'),eventMonth=futureDates[1].slice(0,7),event={source:'BLS',source_event_id:`${futureDates[1]}|10:00|TEST`,title:'Consumer Price Index',source_url:sourceRows(eventMonth).find(s=>s.source==='BLS').url,scheduled_at:eventAt,scheduled_date:futureDates[1],time_status:'scheduled',available_at:received,cancelled:false},months=[...new Set(futureDates.map(d=>d.slice(0,7)))].map(month=>({month,status:'available_scoped',received_at:received,sources:sourceRows(month),events:month===eventMonth?[event]:[]})),macro_events={months};
 return {symbol:'SPY',feed:'iex',adjustment:'split',timeframe:'5Min',evaluation_at:evalAt,calendar:{...calendarRows(sessions,received),requested_range:range},bars,captures,pagination_complete:true,bars_capture:{http_status:200,pagination_complete:true,provider_rows:bars.length,response_sha256:captures[1].response_sha256},macro_events,sessions,businessFuture:futureDates};
}

export function makeFE12Fixture(){
 const priorDates=businessDates('2026-10-29',16),currentDate='2026-10-30',sessions=[...priorDates,currentDate].map(d=>session(d));const current=sessions.at(-1),open=Date.parse(current.open),cutoff=open+300000,evalAt=new Date(cutoff+240000).toISOString(),received=new Date(cutoff+90000).toISOString(),request=new Date(cutoff+10000).toISOString();
 const quoteWindows=sessions.map((s,idx)=>{const sessionOpen=Date.parse(s.open),at=sessionOpen+299000,mid=100+idx*0.14,spread=0.00008+0.000018*Math.sin(idx*0.77)+0.000006*Math.cos(idx*1.31),bp=mid*(1-spread/2),ap=mid*(1+spread/2),bs=1200+idx*20,as=900+idx*17,quote={t:new Date(at).toISOString(),bp,ap,bs,as,c:['R']},quoteStart=sessionOpen+295000,quoteCutoff=sessionOpen+300000,hasNext=idx%3===0,quoteParams=new URLSearchParams({start:new Date(quoteStart).toISOString(),end:new Date(quoteCutoff).toISOString(),feed:'iex',sort:'desc',limit:'1'}),cap=capture(`history_quotes_${s.date}_latest`,request,received,{request_url:`https://data.alpaca.markets/v2/stocks/SPY/quotes?${quoteParams}`,provider_rows:1,has_next_page:hasNext,response_bytes:5000});return {date:s.date,start:new Date(quoteStart).toISOString(),end_inclusive:new Date(quoteCutoff).toISOString(),snapshot_at:new Date(quoteCutoff).toISOString(),point_selection:true,selection_method:'latest_by_provider_desc_limit_1',provider_next_page_token_present:hasNext,quotes:[quote],capture:cap};});
 const bars=[];for(let d=0;d<sessions.length;d++){const sessionOpen=Date.parse(sessions[d].open),base=100+d*0.17;let prev=base;for(let j=0;j<5;j++){const o=prev,r=0.00008*Math.sin(d*1.7+j*0.83)+0.00003*Math.cos(d+j*1.31),c=o*Math.exp(r);bars.push(candle(new Date(sessionOpen+j*60000).toISOString(),o,c,1200+(d*61+j*103)%1400));prev=c;}}
 const calendarAt=new Date(cutoff+30000).toISOString(),range={start_date:priorDates[0],end_date:currentDate},calendarCapture=capture('official_calendar',request,calendarAt,{request_url:`https://paper-api.alpaca.markets/v2/calendar?start=${range.start_date}&end=${range.end_date}`,response_bytes:10000}),barParams=new URLSearchParams({timeframe:'1Min',start:sessions[0].open,end:new Date(cutoff-1).toISOString(),feed:'iex',adjustment:'raw',sort:'asc',limit:'10000'}),barCapture=capture('history_1Min_bars_page_1',request,received,{request_url:`https://data.alpaca.markets/v2/stocks/SPY/bars?${barParams}`,provider_rows:bars.length,retained_rows:bars.length,has_next_page:false,response_bytes:100000}),captures=[calendarCapture,...quoteWindows.map(w=>w.capture),barCapture];
 return {symbol:'SPY',feed:'iex',quote_feed:'iex',quote_size_unit:'shares',adjustment:'raw',bar_timeframe:'1Min',evaluation_at:evalAt,calendar:{...calendarRows(sessions,calendarAt),requested_range:range},quote_windows:quoteWindows,bars,bars_capture:{http_status:200,pagination_complete:true,provider_rows:bars.length,response_sha256s:[barCapture.response_sha256]},captures,pagination_complete:true,sessions};
}
