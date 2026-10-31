// Deterministic invented prices/receipts for FE07/FE10 tests only; never provider data.
import {createHash} from 'node:crypto';
import {fixture as baseFixture,series as baseSeries,boundary} from './fe02-synthetic.mjs';

function iwmSeries(){let p=1;const out=[p];for(let i=1;i<505;i++){
  const vol=i>250?1.65:1,ret=.00003+.0012*vol*Math.sin(i/4.8)+.0007*Math.cos(i/17)+.00045*Math.sin(i*1.31);
  p*=Math.exp(ret);out.push(p);
}return out;}
export function prices(){return {...baseSeries('QQQ'),IWM:iwmSeries()};}
function extraReceipt(symbol,base){
  const now=Date.parse(base.evaluation_at),start=base.requested_window.start,end=base.requested_window.end;
  const url=new URL(`https://data.alpaca.markets/v2/stocks/${symbol}/bars`);
  for(const [k,v] of Object.entries({timeframe:'1Day',start,end:new Date(Date.parse(end)-1).toISOString(),feed:'iex',adjustment:'split',currency:'USD',asof:base.symbol_asof,sort:'asc',limit:'1000'}))url.searchParams.set(k,v);
  return {operation:`history_${symbol}_1Day_page_1`,subject:symbol,request_started_at:new Date(now-10000).toISOString(),
    http_response_received_at:new Date(now-5000).toISOString(),received_at:new Date(now-5000).toISOString(),response_sha256:createHash('sha256').update(symbol).digest('hex'),
    request_url:url.toString(),http_status:200,hash_serialization:'UTF-8 re-encoding of decoded response text',provider_rows:505,has_next_page:false};
}
export function sourceFixture(engineId){
  const base=baseFixture(),p=prices(),symbols=engineId==='FE07'?['SPY','QQQ']:['SPY','QQQ','IWM'];
  const bars_by_symbol=Object.fromEntries(symbols.map(symbol=>[symbol,base.calendar.sessions.map((s,i)=>{
    const c=p[symbol][i];return {t:boundary(s.date,'00:00'),o:c,h:c,l:c,c,v:100};
  })]));
  const captures=base.captures.filter(r=>symbols.includes(r.subject));
  for(const symbol of symbols)if(!captures.some(r=>r.subject===symbol))captures.push(extraReceipt(symbol,base));
  const input={...base,engine_id:engineId,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:base.evaluation_at.slice(0,10),
    bars_by_symbol,captures,requested_window:{start:bars_by_symbol[symbols[0]][0].t,end:base.calendar.sessions.at(-1).close,end_exclusive:true},pagination_complete:true};
  return input;
}
