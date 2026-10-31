// Entirely synthetic regression fixtures. Never bundled or represented as observed market data.
import {createHash} from 'node:crypto';
const zone=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',timeZoneName:'longOffset'});
export function boundary(date,time){const name=zone.formatToParts(new Date(date+'T12:00:00Z')).find(p=>p.type==='timeZoneName').value;return new Date(date+'T'+time+':00'+name.slice(3)).toISOString();}
export function fixture({early=false,zero=false,constant=false,closeFn=null}={}){
 const dates=[];for(let ms=Date.parse('2026-10-28T12:00:00Z');dates.length<505;ms-=86400000)if(![0,6].includes(new Date(ms).getUTCDay()))dates.unshift(new Date(ms).toISOString().slice(0,10));
 const sessions=dates.map((date,i)=>({date,open:boundary(date,'09:30'),close:boundary(date,early&&i===504?'13:00':'16:00')}));
 const bars=dates.map((date,i)=>{const c=closeFn?closeFn(i):Math.exp(zero?0:constant?.001*i:1e-6*i*i+1e-4*i);return {t:boundary(date,'00:00'),o:c,h:c,l:c,c,v:100};});
 const received='2026-10-29T19:36:00.000Z';
 return {symbol:'SPY',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:'2026-10-29',evaluation_at:'2026-10-29T19:40:00.000Z',
 calendar:{sessions,received_at:'2026-10-29T19:35:00.000Z',requested_range:{start_date:'2024-08-20',end_date:'2026-10-29'},complete_provider_response:true},bars,
 requested_window:{start:bars[0].t,end:sessions.at(-1).close,end_exclusive:true},captures:[{operation:'synthetic_fixture_only',request_started_at:received,http_response_received_at:received,received_at:received,response_sha256:createHash('sha256').update(JSON.stringify(bars)).digest('hex')}],pagination_complete:true};
}
