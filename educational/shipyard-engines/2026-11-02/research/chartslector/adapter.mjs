/** Faithful bounded port of the pinned CHARTSLECTOR archive, not Lector desk-read.
 * Float32 panel boundaries match the original NumPy inputs/indicators. No learned
 * ranker, LoD overlay, entries, position sizing, order intent or synthetic data.
 */
export const CHARTSLECTOR_SOURCE = Object.freeze({repository:'__ARCHIVE_REPOSITORY__',commit:'4985ae5989923731b5dbd1edb4c08ec1bd1424d9',prefix:'__OWNER_SUPPLIED_ARCHIVE_SUBTREE__',family:'ChartsLector archive Pine subset',companion_adapter_revision:'53096b3a3151b1705e5b437411597138d91a4495'});
export const STAGE_NAMES = Object.freeze({0:'WARMUP',1:'1A',2:'1B',3:'2A',4:'2B',5:'2C',6:'2D',7:'3A',8:'3B',9:'4A',10:'4B',11:'4C',12:'NA'});
const f = Math.fround;
function ema(x,n,minimum=0,round=false) {
  const a=2/(n+1),out=[];let state=x[0];
  for(let i=0;i<x.length;i++) {if(i)state=a*x[i]+(1-a)*state;out.push(i+1<minimum?NaN:round?f(state):state);}return out;
}
function mean(x,n,round=false) {return x.map((_,i)=>i+1<n?NaN:(round?f:x=>x)(x.slice(i+1-n,i+1).reduce((s,v)=>s+v,0)/n));}
function rma(x,n) {const a=1/n,out=[];let state=NaN;for(let i=0;i<x.length;i++){if(i===n-1)state=x.slice(0,n).reduce((s,v)=>s+v,0)/n;else if(i>=n)state=a*x[i]+(1-a)*state;out.push(f(state));}return out;}
function rs(close,ref,n) {
  const r=close.map((v,i)=>f(v/ref[i])),pct=r.map((v,i)=>i+1<n?NaN:f(r.slice(i+1-n,i+1).filter(x=>x<v).length/(n-1)*100));
  let run=0;const streak=pct.map(v=>{run=v>50?run+1:0;return run>=15;});
  // Count PREVIOUS 15 bars, not a rolling window including today's value.
  const prior=pct.map((_,i)=>i<15?false:pct.slice(i-15,i).filter(v=>v>50).length>=12);
  return {pct,streak,prior};
}
function stage(high,low,close) {
  const e10=ema(close,10,10,true),e20=ema(close,20,20,true),s50=mean(close,50,true);
  const tr=close.map((_,i)=>i===0?f(high[i]-low[i]):Math.max(f(high[i]-low[i]),Math.abs(f(high[i]-close[i-1])),Math.abs(f(low[i]-close[i-1])))),atr=rma(tr,14);
  return close.map((c,i)=>{
    if(!Number.isFinite(s50[i])||!Number.isFinite(atr[i]))return 0;
    const e=e10[i],e2=e20[i],s=s50[i],a=atr[i],ax=f(f(f(c-s)/s)/f(a/c)),spread=f(Math.max(e,e2,s)-Math.min(e,e2,s)),e10up=e>=e10[i-1];
    const up=c>=e&&e>=e2&&e2>=s,dn=c<e2&&e<e2&&e2<s,bo=c>=Math.max(...high.slice(i-20,i)),bd=c<Math.min(...low.slice(i-20,i));
    const basing=Math.abs(f(c-s))<a&&spread<f(1.5*a),bb50=c>e2&&c<s&&e2>e&&e2<s;
    const extB=up&&ax>=7&&ax<11,exhB=up&&ax>=11,extBear=dn&&ax< -7,fadeA=c>=s&&e>=e2&&(c<e||!e10up),fadeB=!extBear&&c>=s&&e<e2,mr=!up&&!dn&&!(basing||bb50)&&c>e2&&e>=e2;
    return exhB?6:extB?5:extBear?11:fadeA?7:fadeB?8:up&&bo?4:up?3:dn&&bd?10:dn?9:basing||bb50?1:mr?2:12;
  });
}
function rrr(close,ref) {
  const ratio=(x,s,n)=>{const sm=ema(x,s),b=ema(sm,n);return sm.map((v,i)=>100*v/b[i]);};
  const rs=close.map((v,i)=>100*v/ref[i]),fast=ratio(rs,15,21),slow=ratio(rs,26,34),r=fast.map((v,i)=>.6*v+.4*slow[i]);
  const mf=ratio(r,8,15),ms=ratio(r,15,26),ch=r.map((v,i)=>i?v-r[i-1]:NaN);
  const m=mf.map((v,i)=>{let adj=0;if(i>=20){const w=ch.slice(i-19,i+1),avg=w.reduce((s,v)=>s+v,0)/20,sd=Math.sqrt(w.reduce((s,v)=>s+(v-avg)**2,0)/20);if(sd>1e-12)adj=.10*Math.tanh(Math.max(-20,Math.min(20,(ch[i]-(r[i]-r[i-5])/5)/(sd+1e-12))));}return .6*v+.4*ms[i]+adj;});
  return {r,m};
}
export function calculateChartslector(bars,spy) {
  if(!Array.isArray(bars)||!Array.isArray(spy)||bars.length!==spy.length||bars.length<156||bars.length>400)throw Error('insufficient_or_unaligned_history');
  for(const rows of [bars,spy])for(let i=0;i<rows.length;i++){
    const b=rows[i];if(!b||typeof b.at!=='string'||!Number.isFinite(Date.parse(b.at))||(i&&Date.parse(b.at)<=Date.parse(rows[i-1].at))||![b.open,b.high,b.low,b.close].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>0&&Number.isFinite(f(v))&&f(v)>0)||!Number.isFinite(b.volume)||b.volume<0||b.high<Math.max(b.open,b.close)||b.low>Math.min(b.open,b.close)||b.high<b.low)throw Error('invalid_market_data');
  }
  if(bars.some((b,i)=>b.at!==spy[i].at))throw Error('unaligned_session_grid');
  const c=bars.map(b=>f(b.close)),h=bars.map(b=>f(b.high)),l=bars.map(b=>f(b.low)),ref=spy.map(b=>f(b.close));
  const n26=rs(c,ref,26),n78=rs(c,ref,78),n156=rs(c,ref,156),st=stage(h,l,c),{r,m}=rrr(c,ref),out={rs26:n26.pct,rs78:n78.pct,rs156:n156.pct,rs_run15:n26.streak,rs_12of15:n26.prior,stage_code:st,rrr_ratio:r,rrr_momentum:m};
  return Object.fromEntries(Object.entries(out).map(([key,values])=>[key,values.map(v=>typeof v==='number'&&!Number.isFinite(v)?null:v)]));
}
