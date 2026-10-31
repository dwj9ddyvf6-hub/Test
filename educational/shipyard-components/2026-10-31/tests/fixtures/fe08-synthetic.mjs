// Isolated test prices, never included in Worker build.
export function fixture({early=false,zero=false}={}) {
  const dates=[];for(let ms=Date.parse('2026-09-29T00:00:00Z');dates.length<22;ms+=86400000)if(![0,6].includes(new Date(ms).getUTCDay()))dates.push(new Date(ms).toISOString().slice(0,10));
  const sessions=dates.map((date,i)=>({date,open:date+'T13:30:00.000Z',close:date+(early&&i===21?'T17:00:00.000Z':'T20:00:00.000Z')}));
  const bars=[];for(const [i,s] of sessions.entries()){let price=100+200*i;const r=zero?0:(i+1)/10000;for(let at=Date.parse(s.open);at<Date.parse(s.close);at+=300000){const close=price*Math.exp(r);bars.push({t:new Date(at).toISOString(),o:price,h:Math.max(price,close),l:Math.min(price,close),c:close,v:100});price=close;}}
  return {symbol:'SPY',feed:'iex',adjustment:'raw',timeframe:'5Min',evaluation_at:'2026-10-29T19:40:00.000Z',calendar:{sessions,received_at:'2026-10-29T19:35:00.000Z',requested_range:{start_date:dates[0],end_date:'2026-10-29'},complete_provider_response:true},bars,requested_window:{start:sessions[0].open,end:sessions.at(-1).close},captures:[{operation:'fixture_synthetic_only',received_at:'2026-10-29T19:36:00.000Z'}],pagination_complete:true};
}
