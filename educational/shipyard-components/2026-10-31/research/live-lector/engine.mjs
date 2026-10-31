import {tensorV698Frame} from "./worker/tensor-v698/index.mjs";

// Original: worker/elliott-wave.js
/* Causal, bounded Elliott price-structure candidates on the displayed OHLC bars.
 * Hard impulse rules and Fibonacci guidelines are deliberately separate.
 * Nearby/intermediate/broader are measured pivot scales, not claimed wave degrees.
 * No provider calls, orders, calibrated probabilities or retrospective returns.
 */
const ELLIOTT_METHOD='elliott-structure-1';
const ELLIOTT_SCALES=[{width:2,name:'nearby'},{width:4,name:'intermediate'},{width:8,name:'broader'}];
function elliottNumber(value){return typeof value==='number'&&Number.isFinite(value);}
function elliottTime(value){if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(value))return null;const n=Date.parse(value),day=value.slice(0,10),d=new Date(day+'T00:00:00Z');return Number.isFinite(n)&&Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===day?n:null;}
function elliottIdentity(value){
 // Exact readable anchor identity; no collision-prone short hash and no wall clock.
 return ELLIOTT_METHOD+'|'+value;
}
function elliottPivots(bars,width,end){
 const pivots=[];
 for(let i=width;i<bars.length-width;i++){
  const b=bars[i],neighbors=bars.slice(i-width,i+width+1).filter((_,k)=>k!==width);
  const low=neighbors.every(x=>b[3]<x[3]),high=neighbors.every(x=>b[2]>x[2]);
  // OHLC does not reveal the ordering of a bar that is both swing high and low.
  if(low===high)continue;
  const confirmedIndex=i+width,confirmedAt=confirmedIndex===bars.length-1?end:bars[confirmedIndex+1][0];
  if(!confirmedAt)continue;
  const p={kind:low?'low':'high',index:i,price:b[low?3:2],pivot_at:b[0],confirmation_index:confirmedIndex,confirmed_at:confirmedAt,confirmation_clock:confirmedIndex===bars.length-1?'verified_final_close':'next_open_upper_bound'};
  const previous=pivots.at(-1);
  // Same-polarity pivots are one unresolved leg. Keep its most extreme endpoint.
  if(previous?.kind===p.kind){if(low?p.price<previous.price:p.price>previous.price)pivots[pivots.length-1]=p;}
  else pivots.push(p);
 }
 return pivots;
}
function elliottImpulseRules(points,side,bars){
 const p=points.map(x=>x.price*side),against=b=>side>0?b[3]:-b[2];
 const leg2=bars.slice(points[1].index+1,points[2].index+1);
 const rules=[{rule:'Wave 1 moves in the impulse direction',passed:p[1]>p[0]},
  {rule:'Wave 2 is a retracement that remains inside wave 1',passed:p[0]<p[2]&&p[2]<p[1]},
  {rule:'No wave 2 wick crosses or touches the wave 1 origin',passed:leg2.every(b=>against(b)>p[0])}];
 if(points.length>=5){const leg4=bars.slice(points[3].index+1,points[4].index+1);rules.push({rule:'Wave 3 exceeds the end of wave 1',passed:p[3]>p[1]},{rule:'Wave 4 retraces wave 3 and stays outside wave 1 territory',passed:p[1]<p[4]&&p[4]<p[3]},{rule:'No wave 4 wick overlaps wave 1 territory',passed:leg4.every(b=>against(b)>p[1])});}
 if(points.length>=6){const one=p[1]-p[0],three=p[3]-p[2],five=p[5]-p[4];rules.push({rule:'Wave 5 exceeds wave 3; truncations are not inferred',passed:p[5]>p[3]},{rule:'Wave 3 is not the shortest of waves 1, 3 and 5',passed:three>=Math.min(one,five)});}
 return rules;
}
function elliottScenario(points,scale,bars,series,pattern,atr){
 const trendSide=points[0].kind==='low'?1:-1,epsilon=Math.max(Number.MIN_VALUE,...points.map(p=>Math.abs(p.price)))*1e-10;
 const impulse=pattern==='abc'?points.slice(0,6):points;
 const rules=elliottImpulseRules(impulse,trendSide,bars);
 if(pattern==='abc'){
  const p=points.map(x=>x.price*trendSide);
  const correctionOriginHeld=bars.slice(points[5].index+1,points[8].index+1).every(b=>(trendSide>0?b[2]:-b[3])<p[5]);
  rules.push({rule:'A moves against the completed impulse',passed:p[6]<p[5]},{rule:'B retraces A without exceeding the impulse extreme',passed:p[7]>p[6]&&p[7]<p[5]},{rule:'C extends beyond A',passed:p[8]<p[6]},{rule:'No later correction wick reaches or crosses the impulse extreme',passed:correctionOriginHeld});
 }
 if(rules.some(r=>!r.passed))return null;
 const last=points.at(-1),one=Math.abs(points[1].price-points[0].price),p2=points[2].price;
 if(!(one>epsilon)||!(atr>0)||one<1.5*atr)return null;
 const completed=pattern==='impulse_12345',side=completed?-trendSide:trendSide;
 const direction=side>0?'bullish':'bearish',trendDirection=trendSide>0?'bullish':'bearish';
 const labels=pattern==='abc'?['0','1','2','3','4','5','A','B','C']:points.map((_,i)=>String(i));
 const candidate={id:elliottIdentity([series.symbol||'',series.interval||'',series.source||'',series.adjustment||'',scale.name,pattern,...points.map((p,i)=>labels[i]+':'+p.pivot_at+':'+p.price)].join('|')),
  pattern,direction,trend_direction:trendDirection,phase:pattern==='impulse_12'?'wave_3_watch':pattern==='impulse_1234'?'wave_5_watch':completed?'five_waves_complete':'abc_recovery_watch',degree:scale.name,
  pivots:points.map((p,i)=>({...p,label:labels[i]})),confirmed_at:last.confirmed_at,confirmation_bar_at:bars[last.confirmation_index][0],confirmation_clock:last.confirmation_clock,age_bars:bars.length-1-last.confirmation_index,
  status:completed||pattern==='abc'?'confirmed':'forming',rule_scope:'confirmed price-swing geometry',subdivision_status:'not_observed',length_basis:'arithmetic_price_distance',
  rules,guidelines:[],supporting_factors:[],invalidation:null,confirmation:null,zone:null,targets:[]};
 const retrace=Math.abs(points[1].price-p2)/one;
 candidate.guidelines.push({rule:'Wave 2 is inside the configured 38.2%–78.6% retracement reference band',observed:retrace>=.382&&retrace<=.786,value:retrace});
 if(points.length>=5){const w3=Math.abs(points[3].price-p2),r4=Math.abs(points[3].price-points[4].price)/w3;candidate.guidelines.push({rule:'Wave 4 is inside the configured 23.6%–50% retracement reference band',observed:r4>=.236&&r4<=.5,value:r4});}
 if(impulse.length>=6){
  const arithmetic=[1,3,5].map(k=>Math.abs(impulse[k].price-impulse[k-1].price));
  const percentage=[1,3,5].map((k,i)=>arithmetic[i]/impulse[k-1].price);
  const arithmeticPass=arithmetic[1]>=Math.min(arithmetic[0],arithmetic[2]),percentagePass=percentage[1]>=Math.min(percentage[0],percentage[2]);
  candidate.length_comparison={arithmetic,percentage,arithmetic_pass:arithmeticPass,percentage_pass:percentagePass,scale_disagreement:arithmeticPass!==percentagePass};
 }
 const addTarget=(label,price,ratio,basis)=>{if(elliottNumber(price)&&price>0)candidate.targets.push({label,price,ratio,basis});};
 const zone=(anchor,length,ratios,basis)=>{const values=ratios.map(r=>anchor-trendSide*length*r);const low=Math.min(...values),high=Math.max(...values),close=bars.at(-1)[4];return {low,high,ratios,basis,location:close<low?'below_zone':close>high?'above_zone':'in_zone'};};
 if(pattern==='impulse_12'){
  candidate.invalidation={price:points[0].price,basis:'intrabar',reason:'A move beyond wave 1 origin invalidates this wave 2 count.'};
  candidate.confirmation={price:points[1].price,rule:'A completed bar close '+(side>0?'above':'below')+' wave 1 confirms a break in the proposed wave 3 direction.'};
  candidate.zone=zone(points[1].price,one,[.382,.618,.786],'Wave 1 retracement area; wait for a turn and the stated confirmation');
  addTarget('Wave 3 · 1.618 × wave 1',p2+side*one*1.618,1.618,'Projected from confirmed wave 2');
  addTarget('Wave 3 extension · 2.618 × wave 1',p2+side*one*2.618,2.618,'Projected from confirmed wave 2');
 }else if(pattern==='impulse_1234'){
  const w3=Math.abs(points[3].price-p2),origin=points[4].price;
  const percentageOne=one/points[0].price,percentageThree=w3/p2;
  // A projected fifth may not create a complete count that fails either of the
  // length interpretations checked below. The percentage denominator is wave 4.
  const arithmeticCeiling=w3<one?w3:Infinity;
  const percentageCeiling=percentageThree<percentageOne?origin*percentageThree:Infinity;
  const ceiling=Math.min(arithmeticCeiling,percentageCeiling);
  candidate.invalidation={price:points[1].price,basis:'intrabar',reason:'Entering wave 1 price territory invalidates this standard wave 4 count.'};
  candidate.confirmation={price:points[3].price,rule:'A completed bar close '+(side>0?'above':'below')+' wave 3 confirms continuation beyond the prior extreme.'};
  candidate.zone=zone(points[3].price,w3,[.236,.382,.5],'Wave 3 retracement area; the wave 1 boundary remains absolute');
  for(const [label,length,ratio,basis]of[
   ['Wave 5 · wave 1 equality',one,1,'Wave 1 length projected from wave 4'],
   ['Wave 5 · 0.618 × waves 1–3',Math.abs(points[3].price-points[0].price)*.618,.618,'Waves 1–3 net distance projected from wave 4'],
   ['Wave 5 extension · 1.618 × wave 1',one*1.618,1.618,'Wave 1 length projected from wave 4']]){
   const target=origin+side*length;if(length<=ceiling&&side*(target-points[3].price)>epsilon)addTarget(label,target,ratio,basis);
  }
  candidate.zone.low=Math.max(candidate.zone.low,side>0?points[1].price+epsilon:0);
  candidate.zone.high=Math.min(candidate.zone.high,side<0?points[1].price-epsilon:Infinity);
  if(candidate.zone.low>=candidate.zone.high)candidate.zone=null;
 }else if(completed){
  candidate.invalidation={price:points[5].price,basis:'intrabar',reason:'A new extreme beyond wave 5 means this completed count must be reconsidered.'};
  candidate.confirmation={price:points[4].price,rule:'A completed bar close '+(side>0?'above':'below')+' wave 4 supports a correction of the five-wave move.'};
  const move=Math.abs(points[5].price-points[0].price);
  for(const r of [.382,.5,.618])addTarget('Correction · '+(r*100)+'% of impulse',points[5].price+side*move*r,r,'Retracement of confirmed waves 0–5');
 }else{
  candidate.invalidation={price:points[8].price,basis:'intrabar',reason:'A new extreme beyond C invalidates this completed-correction interpretation.'};
  candidate.confirmation={price:points[7].price,rule:'A completed bar close '+(side>0?'above':'below')+' B supports recovery from the A–B–C structure.'};
  addTarget('Prior impulse extreme',points[5].price,null,'Observed wave 5 extreme');
  addTarget('Recovery · prior impulse equality',points[8].price+side*Math.abs(points[5].price-points[0].price),1,'Prior complete impulse length projected from C');
 }
 const breach=bars.findIndex((b,i)=>i>=last.confirmation_index&&(side>0?b[3]<=candidate.invalidation.price+epsilon:b[2]>=candidate.invalidation.price-epsilon));
 if(breach>=0){candidate.status='invalidated';candidate.invalidated_bar_at=bars[breach][0];candidate.invalidated_at=breach===bars.length-1?(series.last_completed_at||series.observed_at):bars[breach+1][0];candidate.confirmation=null;candidate.zone=null;candidate.targets=[];}
 else{
  const firstBreak=bars.findIndex((b,i)=>i>=last.confirmation_index&&side*(b[4]-candidate.confirmation.price)>epsilon);
  const current=bars.at(-1),beyond=side*(current[4]-candidate.confirmation.price)>epsilon,observed=firstBreak>=0;
  const fmt=value=>Number(value.toPrecision(7)).toString(),word=side>0?'above':'below',opposite=side>0?'below':'above';
  const label=bar=>series.interval==='1d'||series.interval==='1wk'?bar[0].slice(0,10):bar[0];
  // Earlier rows have only a next-bar upper bound, not an exact exchange close
  // or receipt. Keep the historical candle separate from today's condition.
  const summary=observed?'The '+label(bars[firstBreak])+' candle closed at '+fmt(bars[firstBreak][4])+' '+word+' '+fmt(candidate.confirmation.price)+'. '+(beyond?'The latest close at '+fmt(current[4])+' remains '+word+' that level.':'The latest close at '+fmt(current[4])+' is '+(Math.abs(current[4]-candidate.confirmation.price)<=epsilon?'at':opposite)+' that level; the earlier break is no longer confirmed by the latest close.'):'No completed candle has closed '+word+' '+fmt(candidate.confirmation.price)+' yet.';
  candidate.confirmation={...candidate.confirmation,observed,observed_at:!observed?null:firstBreak===bars.length-1?(series.last_completed_at||series.observed_at):bars[firstBreak+1][0],
   observed_bar_at:observed?bars[firstBreak][0]:null,observed_close:observed?bars[firstBreak][4]:null,
   observed_clock:!observed?null:firstBreak<bars.length-1?'next_bar_timestamp_upper_bound':series.last_completed_at?'verified_source_close':'source_observation',
   current_bar_at:current[0],current_close:current[4],current_beyond_level:beyond,state:!observed?'awaiting_break':beyond?'holding_beyond_level':'back_inside_level',summary};
  candidate.targets=candidate.targets.filter(t=>side*(t.price-bars.at(-1)[4])>epsilon).sort((a,b)=>side*(a.price-b.price));
  if(candidate.zone)candidate.zone.location=bars.at(-1)[4]<candidate.zone.low?'below_zone':bars.at(-1)[4]>candidate.zone.high?'above_zone':'in_zone';
 }
 candidate.supporting_factors=candidate.guidelines.filter(x=>x.observed).map(x=>x.rule);
 if(candidate.status!=='invalidated'&&candidate.length_comparison?.scale_disagreement){
  candidate.status='ambiguous';candidate.ambiguity_reason='Arithmetic and percentage wave-length rules disagree.';
  candidate.confirmation=null;candidate.zone=null;candidate.targets=[];
 }
 return candidate;
}
function analyzeElliottWave(series,now=Date.now(),context={}){
 const base={method:ELLIOTT_METHOD,status:'unavailable',as_of:null,input_bar_count:0,preferred:null,alternate:null,counts:[],invalidated:[],ambiguous:[],notes:[],selection:'Newest confirmed structural endpoint, then complete rule set, then guideline fit; no probability weights'};
 const fail=reason=>({...base,reason});
 const rows=series?.bars,observed=elliottTime(series?.observed_at),received=series?.received_at==null?null:elliottTime(series.received_at),end=series?.last_completed_at==null?null:elliottTime(series.last_completed_at);
 now=typeof now==='string'?elliottTime(now):now;
 if(!elliottNumber(now)||observed===null||observed>now||(series?.received_at!=null&&(received===null||received>now))||(series?.last_completed_at!=null&&(end===null||end>now||end>observed||(received!==null&&end>received))))return fail('invalid_completion_or_receipt_clock');
 if(!Array.isArray(rows)||rows.length>260||rows.length<3)return fail('invalid_bar_count');
 let prior=-Infinity;
 for(const b of rows){const t=Array.isArray(b)?elliottTime(b[0]):null;if(!Array.isArray(b)||b.length!==6||t===null||t<=prior||t>=now||t>observed||(end!==null&&t>=end)||!b.slice(1,5).every(elliottNumber)||Math.min(...b.slice(1,5))<=0||b[2]<Math.max(b[1],b[3],b[4])||b[3]>Math.min(b[1],b[2],b[4])||(b[5]!==null&&(!elliottNumber(b[5])||b[5]<0)))return fail('invalid_bar');prior=t;}
 base.input_bar_count=rows.length;base.as_of=end===null?(series.as_of||null):new Date(end).toISOString();
 if(rows.length<20)return {...base,status:'warming',reason:'twenty_completed_bars_required'};
 let atr=Array.isArray(context.atr)?context.atr:null;
 if(!atr||atr.length!==rows.length){atr=Array(rows.length).fill(null);let value=0;for(let i=0;i<rows.length;i++){const tr=i?Math.max(rows[i][2]-rows[i][3],Math.abs(rows[i][2]-rows[i-1][4]),Math.abs(rows[i][3]-rows[i-1][4])):rows[i][2]-rows[i][3];if(i<14){value+=tr;if(i===13){value/=14;atr[i]=value;}}else{value=(value*13+tr)/14;atr[i]=value;}}}
 const candidates=[];
 for(const scale of ELLIOTT_SCALES){
  const pivots=elliottPivots(rows,scale.width,end===null?null:new Date(end).toISOString());
  for(const [count,pattern]of[[3,'impulse_12'],[5,'impulse_1234'],[6,'impulse_12345'],[9,'abc']]){
   if(pivots.length<count)continue;const points=pivots.slice(-count),point=points.at(-1),value=elliottScenario(points,scale,rows,series,pattern,atr[point.confirmation_index]);if(value)candidates.push(value);
  }
 }
 const valid=candidates.filter(x=>['forming','confirmed'].includes(x.status)).sort((a,b)=>Date.parse(b.confirmed_at)-Date.parse(a.confirmed_at)||b.rules.length-a.rules.length||b.supporting_factors.length-a.supporting_factors.length||a.id.localeCompare(b.id));
 const unique=[];for(const c of valid){const anchors=c.pattern+'|'+c.pivots.map(x=>x.pivot_at+':'+x.price).join('|');if(!unique.some(x=>x.anchors===anchors))unique.push({anchors,c});}
 base.preferred=unique[0]?.c||null;
 base.alternate=unique.find(x=>x.c.direction!==base.preferred?.direction)?.c||unique[1]?.c||null;
 base.counts=unique.slice(0,4).map(x=>x.c);
 if(base.alternate&&!base.counts.includes(base.alternate))base.counts[base.counts.length-1]=base.alternate;
 base.invalidated=candidates.filter(x=>x.status==='invalidated').sort((a,b)=>Date.parse(b.confirmed_at)-Date.parse(a.confirmed_at)).slice(0,2);
 base.ambiguous=candidates.filter(x=>x.status==='ambiguous').sort((a,b)=>Date.parse(b.confirmed_at)-Date.parse(a.confirmed_at)).slice(0,2);
 if(!base.counts.length)base.counts=base.ambiguous;
 base.status=base.preferred?'ready':base.ambiguous.length?'ambiguous':'no_valid_count';
 base.notes=['Impulse price rules are required; Fibonacci ratios only locate areas to watch.','Subwave counts are not resolved by these measured pivot scales.'];
 if(base.alternate&&base.alternate.direction!==base.preferred.direction)base.notes.push('A valid alternate structure points in the opposite direction.');
 if(base.ambiguous.length)base.notes.push('Another count has conflicting arithmetic and percentage wave lengths; no trade levels are derived from it.');
 return base;
}


// Original: worker/technicals.js
/* Bounded, read-only chart geometry. No provider calls, forecasts or order gates.
 * Conventions: Wilder RSI/ATR; strict 2-left/2-right pivots; completed bars only.
 * MACD(12,26,9): each EMA uses alpha=2/(period+1), seeded with the SMA
 * of its first complete period. The signal EMA starts at the first valid MACD
 * value; line begins at index25, signal/histogram at index33 (zero-based).
 * Recomputed from this bounded source window: no hidden prehistory seed.
 * A historical pivot's confirmation clock is a conservative next-open bound
 * unless it is the final bar, whose verified completion clock is supplied.
 */
const CHART_READ_METHOD = 'measured-chart-6';
const CHART_NUMBER_FORMATTERS = new Map();
const CHART_DATE_FORMATTERS = new Map();
function chartFormatNumber(value,options={}) {
  const key=JSON.stringify(options);let formatter=CHART_NUMBER_FORMATTERS.get(key);
  if(!formatter){formatter=new Intl.NumberFormat('en-US',options);if(CHART_NUMBER_FORMATTERS.size>=16)CHART_NUMBER_FORMATTERS.clear();CHART_NUMBER_FORMATTERS.set(key,formatter);}
  return formatter.format(value);
}
function chartDateFormatter(locale,options={}) {
  const key=locale+'|'+JSON.stringify(options);let formatter=CHART_DATE_FORMATTERS.get(key);
  if(!formatter){formatter=new Intl.DateTimeFormat(locale,options);if(CHART_DATE_FORMATTERS.size>=12)CHART_DATE_FORMATTERS.clear();CHART_DATE_FORMATTERS.set(key,formatter);}
  return formatter;
}
function chartFinite(x) { return typeof x === 'number' && Number.isFinite(x); }
function chartTime(x) {
  if (typeof x !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(x)) return null;
  const t = Date.parse(x); if (!Number.isFinite(t)) return null;
  const day = x.slice(0, 10), d = new Date(day + 'T00:00:00Z');
  return Number.isFinite(d.getTime()) && d.toISOString().slice(0, 10) === day ? t : null;
}
function chartSma(xs, n) {
  const out = Array(xs.length).fill(null); let sum = 0;
  for (let i = 0; i < xs.length; i++) { sum += xs[i]; if (i >= n) sum -= xs[i-n]; if (i >= n-1) out[i] = sum/n; }
  return out;
}
function chartWilder(xs, n) {
  const out = Array(xs.length).fill(null); if (xs.length < n) return out;
  let v = xs.slice(0,n).reduce((a,b)=>a+b,0)/n; out[n-1] = v;
  for (let i=n;i<xs.length;i++) { v = ((n-1)*v+xs[i])/n; out[i]=v; } return out;
}
function chartRsi(closes) {
  const out=Array(closes.length).fill(null), gains=[], losses=[];
  for(let i=1;i<closes.length;i++) {const d=closes[i]-closes[i-1];gains.push(Math.max(d,0));losses.push(Math.max(-d,0));}
  const g=chartWilder(gains,14),l=chartWilder(losses,14);
  for(let i=0;i<g.length;i++) if(g[i]!==null) out[i+1]=g[i]===0&&l[i]===0?50:l[i]===0?100:100-100/(1+g[i]/l[i]);
  return out;
}
function chartEma(xs, n) {
  const out=Array(xs.length).fill(null),alpha=2/(n+1);let total=0,count=0,value=null;
  for(let i=0;i<xs.length;i++) {
    // Missing prefixes are warm-up, never zero. A gap starts a fresh seed.
    if(!chartFinite(xs[i])) {total=0;count=0;value=null;continue;}
    if(value===null) {total+=xs[i];count++;if(count===n)value=total/n;}
    else value=alpha*xs[i]+(1-alpha)*value;
    out[i]=value;
  }
  return out;
}
function chartMacd(closes) {
  const fast=chartEma(closes,12),slow=chartEma(closes,26);
  const macd=closes.map((_,i)=>fast[i]===null||slow[i]===null?null:fast[i]-slow[i]);
  const signal=chartEma(macd,9),histogram=macd.map((v,i)=>v===null||signal[i]===null?null:v-signal[i]);
  return {macd,signal,histogram};
}
function chartNullableSma(xs,n) {
  const out=Array(xs.length).fill(null);
  for(let i=n-1;i<xs.length;i++){const window=xs.slice(i-n+1,i+1);if(window.every(chartFinite))out[i]=window.reduce((a,b)=>a+b,0)/n;}
  return out;
}
function chartDivergenceIndicators(bars,closes) {
  const n=bars.length,stochFast=Array(n).fill(null),typical=bars.map(b=>(b.h+b.l+b.c)/3),obv=Array(n).fill(null),ad=Array(n).fill(null),mfi=Array(n).fill(null),volumeEma5=chartEma(bars.map(b=>b.v),5),volumeEma20=chartEma(bars.map(b=>b.v),20),volumeSegments=Array(n).fill(null);
  let obvValue=0,adValue=0,segment=0,inGap=true;
  for(let i=0;i<n;i++){
    const b=bars[i];
    if(chartFinite(b.v)){
      if(inGap){obvValue=0;adValue=0;inGap=false;}volumeSegments[i]=segment;
      if(i&&chartFinite(closes[i-1]))obvValue+=closes[i]>closes[i-1]?b.v:closes[i]<closes[i-1]?-b.v:0;
      const range=b.h-b.l,mult=range>0?((b.c-b.l)-(b.h-b.c))/range:0;adValue+=mult*b.v;obv[i]=obvValue;ad[i]=adValue;
    }else if(!inGap){segment++;inGap=true;}
    if(i>=13){const w=bars.slice(i-13,i+1),hi=Math.max(...w.map(x=>x.h)),lo=Math.min(...w.map(x=>x.l));stochFast[i]=hi===lo?50:100*(b.c-lo)/(hi-lo);}
    if(i>=14){const window=bars.slice(i-14,i+1);if(window.every(x=>chartFinite(x.v))){let pos=0,neg=0;for(let j=1;j<window.length;j++){const flow=typical[i-14+j]*window[j].v;if(typical[i-14+j]>typical[i-14+j-1])pos+=flow;else if(typical[i-14+j]<typical[i-14+j-1])neg+=flow;}mfi[i]=pos+neg===0?50:neg===0?100:100-100/(1+pos/neg);}}
  }
  const stochSlow=chartNullableSma(stochFast,3),volumeOsc=volumeEma5.map((x,i)=>chartFinite(x)&&chartFinite(volumeEma20[i])?x-volumeEma20[i]:null);
  return {slow_stochastic:stochSlow,obv,ad_line:ad,mfi14:mfi,volume_ema5_20:volumeOsc,volume_segments:volumeSegments};
}
function chartAdvancedIndicators(bars, rsiSeries, adLine, atrSeries) {
  const n=bars.length, closes=bars.map(b=>b.c), highs=bars.map(b=>b.h), lows=bars.map(b=>b.l), volumes=bars.map(b=>b.v), typical=bars.map(b=>(b.h+b.l+b.c)/3);
  const empty=()=>Array(n).fill(null), range=(xs,i,p)=>i>=p-1?xs.slice(i-p+1,i+1):[];
  const sum=xs=>xs.reduce((a,b)=>a+b,0), mean=xs=>xs.length?sum(xs)/xs.length:null;
  const rolling=(xs,p,fn)=>{const out=empty();for(let i=p-1;i<n;i++){const w=xs.slice(i-p+1,i+1);if(w.every(chartFinite))out[i]=fn(w,i);}return out;};
  const cci20=rolling(typical,20,(w,i)=>{const avg=mean(w),dev=mean(w.map(x=>Math.abs(x-avg)));return dev>0?(typical[i]-avg)/(.015*dev):0;});
  const williamsR14=empty(),stochRsiK=empty();
  for(let i=13;i<n;i++){
    const hi=Math.max(...highs.slice(i-13,i+1)),lo=Math.min(...lows.slice(i-13,i+1));
    if(hi>lo)williamsR14[i]=-100*(hi-closes[i])/(hi-lo);
    const rw=rsiSeries.slice(i-13,i+1);if(rw.every(chartFinite)){const rh=Math.max(...rw),rl=Math.min(...rw);stochRsiK[i]=rh>rl?100*(rsiSeries[i]-rl)/(rh-rl):50;}
  }
  const stochRsiD=rolling(stochRsiK,3,w=>mean(w));
  const roc={};for(const p of [5,20,63,126]){const x=empty();for(let i=p;i<n;i++)if(closes[i-p]>0)x[i]=100*(closes[i]/closes[i-p]-1);roc[p]=x;}
  // Classic Coppock formula on the supplied bar interval: WMA(10) of ROC(14)+ROC(11).
  // The original convention is monthly; the readout labels the actual interval so
  // daily/weekly use cannot be mistaken for the original monthly indicator.
  const coppockRaw=empty(),coppock=empty();for(let i=14;i<n;i++)if(closes[i-14]>0&&closes[i-11]>0)coppockRaw[i]=100*(closes[i]/closes[i-14]-1)+100*(closes[i]/closes[i-11]-1);
  for(let i=23;i<n;i++){const w=coppockRaw.slice(i-9,i+1);if(w.every(chartFinite))coppock[i]=w.reduce((sum,value,j)=>sum+value*(j+1),0)/55;}
  const aroonUp=empty(),aroonDown=empty();for(let i=24;i<n;i++){
    const h=highs.slice(i-24,i+1),l=lows.slice(i-24,i+1),hi=Math.max(...h),lo=Math.min(...l);
    aroonUp[i]=100*(25-(24-h.lastIndexOf(hi)))/25;aroonDown[i]=100*(25-(24-l.lastIndexOf(lo)))/25;
  }
  const tr=bars.map((b,i)=>i?Math.max(b.h-b.l,Math.abs(b.h-bars[i-1].c),Math.abs(b.l-bars[i-1].c)):b.h-b.l),plusVm=empty(),minusVm=empty();
  for(let i=1;i<n;i++){plusVm[i]=Math.abs(highs[i]-lows[i-1]);minusVm[i]=Math.abs(lows[i]-highs[i-1]);}
  const vortexPlus=empty(),vortexMinus=empty();for(let i=14;i<n;i++){
    const trs=sum(tr.slice(i-13,i+1)),p=sum(plusVm.slice(i-13,i+1)),m=sum(minusVm.slice(i-13,i+1));if(trs>0){vortexPlus[i]=p/trs;vortexMinus[i]=m/trs;}
  }
  const e15=chartEma(closes,15),e215=chartEma(e15,15),e315=chartEma(e215,15),trix15=empty();for(let i=1;i<n;i++)if(chartFinite(e315[i])&&chartFinite(e315[i-1])&&e315[i-1]!==0)trix15[i]=100*(e315[i]/e315[i-1]-1);
  const logReturns=empty();for(let i=1;i<n;i++)if(closes[i]>0&&closes[i-1]>0)logReturns[i]=Math.log(closes[i]/closes[i-1]);
  const histVol20=rolling(logReturns,20,w=>{const avg=mean(w),variance=sum(w.map(x=>(x-avg)**2))/(w.length-1);return Math.sqrt(variance*252)*100;});
  const hvValues=histVol20.filter(chartFinite),hv=histVol20.at(-1),hvRank=chartFinite(hv)?100*hvValues.filter(x=>x<=hv).length/hvValues.length:null;
  const ema13=chartEma(closes,13),elderBull=empty(),elderBear=empty();for(let i=0;i<n;i++)if(chartFinite(ema13[i])){elderBull[i]=highs[i]-ema13[i];elderBear[i]=lows[i]-ema13[i];}
  const ranges=bars.map(b=>b.h-b.l),rangeEma9=chartEma(ranges,9),rangeEma2=chartEma(rangeEma9,9),massRatio=rangeEma9.map((x,i)=>chartFinite(x)&&chartFinite(rangeEma2[i])&&rangeEma2[i]!==0?x/rangeEma2[i]:null),massIndex=rolling(massRatio,25,w=>sum(w));
  const mfMultiplier=bars.map(b=>b.h>b.l?((b.c-b.l)-(b.h-b.c))/(b.h-b.l):0),mfVolume=mfMultiplier.map((x,i)=>chartFinite(volumes[i])?x*volumes[i]:null),cmf20=empty(),vwma20=empty(),upDownVolume20=empty(),upDownVolume50=empty(),easeRaw=empty(),efiRaw=empty();
  for(let i=0;i<n;i++){
    if(i>=19){const v=volumes.slice(i-19,i+1),mf=mfVolume.slice(i-19,i+1),vsum=v.every(chartFinite)?sum(v):null;if(vsum>0&&mf.every(chartFinite))cmf20[i]=sum(mf)/vsum;if(vsum>0&&v.every(chartFinite))vwma20[i]=sum(v.map((x,j)=>x*closes[i-19+j]))/vsum;
      if(v.every(chartFinite)){let up=0,down=0;for(let j=i-19;j<=i;j++)if(j>0){if(closes[j]>closes[j-1])up+=volumes[j];else if(closes[j]<closes[j-1])down+=volumes[j];}upDownVolume20[i]={up,down,ratio:down>0?up/down:null};}}
    if(i>=50){const v=volumes.slice(i-49,i+1);if(v.length===50&&v.every(chartFinite)){let up=0,down=0;for(let j=i-49;j<=i;j++){if(closes[j]>closes[j-1])up+=volumes[j];else if(closes[j]<closes[j-1])down+=volumes[j];}upDownVolume50[i]={up,down,ratio:down>0?up/down:null,period:50};}}
    if(i>0&&chartFinite(volumes[i])&&volumes[i]>0){const mid=(highs[i]+lows[i])/2,priorMid=(highs[i-1]+lows[i-1])/2;easeRaw[i]=(mid-priorMid)*(highs[i]-lows[i])/(volumes[i]/100000000);efiRaw[i]=(closes[i]-closes[i-1])*volumes[i];}
  }
  const easeOfMovement14=rolling(easeRaw,14,w=>mean(w)),elderForce13=chartEma(efiRaw,13),chaikinFast=chartEma(adLine,3),chaikinSlow=chartEma(adLine,10),chaikinOscillator=empty();
  for(let i=0;i<n;i++)if(chartFinite(chaikinFast[i])&&chartFinite(chaikinSlow[i]))chaikinOscillator[i]=chaikinFast[i]-chaikinSlow[i];
  const nvi=empty(),pvi=empty(),pvt=empty();let nv=1000,pv=1000,pt=0;
  for(let i=0;i<n;i++){if(i===0){if(chartFinite(volumes[i])){nvi[i]=nv;pvi[i]=pv;pvt[i]=pt;}continue;}if(!chartFinite(volumes[i])||!chartFinite(volumes[i-1])||closes[i-1]<=0)continue;const ret=closes[i]/closes[i-1]-1;if(volumes[i]<volumes[i-1])nv*=1+ret;if(volumes[i]>volumes[i-1])pv*=1+ret;pt+=volumes[i]*ret;nvi[i]=nv;pvi[i]=pv;pvt[i]=pt;}
  const ema34=chartEma(closes,34),ema50=chartEma(closes,50),ema60=chartEma(closes,60),ema3=chartEma(closes,3),ema5=chartEma(closes,5),ema8=chartEma(closes,8),ema10=chartEma(closes,10),ema12=chartEma(closes,12),ema15=chartEma(closes,15),ema30=chartEma(closes,30),ema35=chartEma(closes,35),ema40=chartEma(closes,40),ema45=chartEma(closes,45);
  const klingerForce=empty();let cumulativeDm=0,priorTrend=0;
  for(let i=1;i<n;i++)if(chartFinite(volumes[i])){const dm=highs[i]-lows[i],trend=highs[i]+lows[i]>highs[i-1]+lows[i-1]?1:-1;cumulativeDm=trend===priorTrend?cumulativeDm+dm:dm+(i?highs[i-1]-lows[i-1]:0);priorTrend=trend;if(cumulativeDm>0)klingerForce[i]=volumes[i]*Math.abs(2*(dm/cumulativeDm-1))*trend*100;}
  const klinger34=chartEma(klingerForce,34),klinger55=chartEma(klingerForce,55),klinger=empty();for(let i=0;i<n;i++)if(chartFinite(klinger34[i])&&chartFinite(klinger55[i]))klinger[i]=klinger34[i]-klinger55[i];
  const donchian=(p)=>{if(n<=p)return null;const w=bars.slice(-p-1,-1);return {period:p,high:Math.max(...w.map(b=>b.h)),low:Math.min(...w.map(b=>b.l)),basis:(Math.max(...w.map(b=>b.h))+Math.min(...w.map(b=>b.l)))/2};};
  const sma20=chartSma(closes,20),ema20=chartEma(closes,20),atr20=chartWilder(tr,20),keltner=chartFinite(ema20.at(-1))&&chartFinite(atr20.at(-1))?{basis:ema20.at(-1),upper:ema20.at(-1)+2*atr20.at(-1),lower:ema20.at(-1)-2*atr20.at(-1),atr_period:20,multiplier:2}:null;
  const bbWindow=range(closes,n-1,20),bbMean=mean(bbWindow),bbSd=bbWindow.length===20?Math.sqrt(mean(bbWindow.map(x=>(x-bbMean)**2))):null;
  let vwap20=null,vwapSd=null;const vw=bars.slice(-20);if(vw.length===20&&vw.every(b=>chartFinite(b.v))){const denominator=sum(vw.map(b=>b.v));if(denominator>0){vwap20=sum(vw.map(b=>((b.h+b.l+b.c)/3)*b.v))/denominator;vwapSd=Math.sqrt(sum(vw.map(b=>b.v*((b.h+b.l+b.c)/3-vwap20)**2))/denominator);}}
  const vwapBands=vwap20!==null?{basis:vwap20,upper1:vwap20+vwapSd,lower1:vwap20-vwapSd,upper2:vwap20+2*vwapSd,lower2:vwap20-2*vwapSd,weighted_stddev:vwapSd}:null;
  const prior=bars.at(-2),floor=prior?(()=>{const p=(prior.h+prior.l+prior.c)/3;return {pivot:p,r1:2*p-prior.l,s1:2*p-prior.h,r2:p+(prior.h-prior.l),s2:p-(prior.h-prior.l)};})():null;
  const span=(period,i)=>{const w=bars.slice(Math.max(0,i-period+1),i+1);return w.length===period?{high:Math.max(...w.map(b=>b.h)),low:Math.min(...w.map(b=>b.l))}:null;},tenkan=span(9,n-1),kijun=span(26,n-1),senkouB=span(52,n-1),ichimoku=tenkan&&kijun&&senkouB?{tenkan:(tenkan.high+tenkan.low)/2,kijun:(kijun.high+kijun.low)/2,senkou_a:((tenkan.high+tenkan.low)/2+(kijun.high+kijun.low)/2)/2,senkou_b:(senkouB.high+senkouB.low)/2,projection_bars:26,chikou_close:closes.at(-1),chikou_offset_bars:-26}:null;
  const ytdIndex=bars.findIndex(b=>b.t.slice(0,4)===bars.at(-1).t.slice(0,4)),ytd=bars.slice(Math.max(0,ytdIndex));let ytdVwap=null;if(ytd.length&&ytd.every(b=>chartFinite(b.v))){const den=sum(ytd.map(b=>b.v));if(den>0)ytdVwap=sum(ytd.map(b=>(b.h+b.l+b.c)/3*b.v))/den;}
  let gapAnchor=null;for(let i=Math.max(1,n-260);i<n;i++){const gap=bars[i].o-bars[i-1].c,baseAtr=atrSeries?.[i-1];if(chartFinite(baseAtr)&&baseAtr>0&&Math.abs(gap)>=.5*baseAtr){const tail=bars.slice(i);if(tail.every(b=>chartFinite(b.v))){const den=sum(tail.map(b=>b.v));if(den>0)gapAnchor={anchor_at:bars[i].t,gap_atr:gap/baseAtr,value:sum(tail.map(b=>(b.h+b.l+b.c)/3*b.v))/den};}}}
  const psar=chartParabolicSar(bars),supertrend=chartSupertrend(bars,tr),chandelier=chartFinite(atrSeries?.at(-1))?{long:Math.max(...highs.slice(-22))-3*atrSeries.at(-1),short:Math.min(...lows.slice(-22))+3*atrSeries.at(-1),period:22,atr_multiplier:3}:null;
  const periodKeys=chartPeriodKeys(bars),levels=periodKeys?chartPriorPeriodLevels(bars,periodKeys):null;
  const prior20=donchian(20),prior55=donchian(55),close=closes.at(-1),bbRank=chartFinite(bbSd)&&bbMean!==0&&bbWindow.length===20?4*bbSd/bbMean:null;
  const bbSeries=[];for(let i=19;i<n;i++){const w=closes.slice(i-19,i+1),avg=mean(w),sd=Math.sqrt(mean(w.map(x=>(x-avg)**2)));if(avg>0)bbSeries.push(4*sd/avg);}
  const bbPercentile=bbRank===null?null:100*bbSeries.filter(x=>x<=bbRank).length/bbSeries.length;
  const rangesLast=bars.slice(-7).map(b=>b.h-b.l),nr4=bars.length>=4?(bars.at(-1).h-bars.at(-1).l)<=Math.min(...bars.slice(-4).map(b=>b.h-b.l)):null,nr7=bars.length>=7?(bars.at(-1).h-bars.at(-1).l)<=Math.min(...rangesLast):null;
  let upCount=0,downCount=0;for(let i=n-1;i>=1&&upCount+downCount<9;i--){if(closes[i]>closes[i-4]){upCount++;downCount=0;}else if(closes[i]<closes[i-4]){downCount++;upCount=0;}else break;}
  const haClose=(bars.at(-1).o+bars.at(-1).h+bars.at(-1).l+bars.at(-1).c)/4;let haOpen=(bars[0].o+bars[0].c)/2;for(let i=1;i<n;i++){const hc=(bars[i-1].o+bars[i-1].h+bars[i-1].l+bars[i-1].c)/4;haOpen=(haOpen+hc)/2;}
  const allHigh=Math.max(...highs),allLow=Math.min(...lows),atrLast=atrSeries?.at(-1),price=closes.at(-1);
  const values={cci20:cci20.at(-1),williams_r14:williamsR14.at(-1),stoch_rsi_k14:stochRsiK.at(-1),stoch_rsi_d3:stochRsiD.at(-1),roc_horizons:Object.fromEntries(Object.entries(roc).map(([p,x])=>[p,x.at(-1)])),coppock_14_11_10:coppock.at(-1),aroon_25:{up:aroonUp.at(-1),down:aroonDown.at(-1)},vortex_14:{plus:vortexPlus.at(-1),minus:vortexMinus.at(-1)},trix_15:trix15.at(-1),historical_volatility:{annualized_20:histVol20.at(-1),percentile:hvRank,observations:hvValues.length,rank_window:'available supplied completed bars'},elder_ray:{bull:elderBull.at(-1),bear:elderBear.at(-1),ema13:ema13.at(-1)},mass_index_25:massIndex.at(-1),chaikin_money_flow_20:cmf20.at(-1),chaikin_oscillator_3_10:chaikinOscillator.at(-1),elder_force_index_13:elderForce13.at(-1),ease_of_movement_14:easeOfMovement14.at(-1),klinger_34_55:klinger.at(-1),vwma20:vwma20.at(-1),up_down_volume_20:upDownVolume20.at(-1),up_down_volume_50:upDownVolume50.at(-1),nvi:nvi.at(-1),pvi:pvi.at(-1),pvt:pvt.at(-1),
    ichimoku, floor_pivots:floor, prior_period_levels:levels, parabolic_sar:psar.at(-1), supertrend:supertrend.at(-1), keltner, donchian20:prior20, donchian55:prior55, chandelier_exit:chandelier, vwap_stddev_bands:vwapBands,
    ma_ribbon_gmma:{short:{ema3:ema3.at(-1),ema5:ema5.at(-1),ema8:ema8.at(-1),ema10:ema10.at(-1),ema12:ema12.at(-1),ema15:ema15.at(-1)},long:{ema30:ema30.at(-1),ema35:ema35.at(-1),ema40:ema40.at(-1),ema45:ema45.at(-1),ema50:ema50.at(-1),ema60:ema60.at(-1)}},
    all_time_range_available:{high:allHigh,low:allLow,bars:n,source_limited:true},ytd_anchored_vwap:ytdVwap,major_gap_anchored_vwap:gapAnchor,
    fair_value_gaps:chartFairValueGaps(bars),liquidity_sweeps:chartLiquiditySweeps(bars,prior20),nr4,nr7,td_setup:{buy_count:downCount,sell_count:upCount,complete:downCount===9||upCount===9},heikin_ashi:{open:haOpen,high:Math.max(bars.at(-1).h,haOpen,haClose),low:Math.min(bars.at(-1).l,haOpen,haClose),close:haClose,direction:haClose>haOpen?'up':haClose<haOpen?'down':'flat'},
    golden_death_cross:chartLatestAverageCross(sma20,chartSma(closes,50),chartSma(closes,200)), available_history_bars:n, close:price, atr14:atrLast,
    formula_version:'ohlcv-extensions-1'};
  return values;
}
function chartParabolicSar(bars){
  const out=Array(bars.length).fill(null);if(bars.length<3)return out;let up=bars[1].c>=bars[0].c,af=.02,ep=up?Math.max(bars[0].h,bars[1].h):Math.min(bars[0].l,bars[1].l),sar=up?Math.min(bars[0].l,bars[1].l):Math.max(bars[0].h,bars[1].h);out[1]=sar;
  for(let i=2;i<bars.length;i++){sar=sar+af*(ep-sar);if(up){sar=Math.min(sar,bars[i-1].l,bars[i-2].l);if(bars[i].l<sar){up=false;sar=ep;ep=bars[i].l;af=.02;}else if(bars[i].h>ep){ep=bars[i].h;af=Math.min(.2,af+.02);}}else{sar=Math.max(sar,bars[i-1].h,bars[i-2].h);if(bars[i].h>sar){up=true;sar=ep;ep=bars[i].h;af=.02;}else if(bars[i].l<ep){ep=bars[i].l;af=Math.min(.2,af+.02);}}out[i]=sar;}return out;
}
function chartSupertrend(bars,tr,period=10,multiplier=3){
  const atr=chartWilder(tr,period),out=Array(bars.length).fill(null);let upper=null,lower=null,direction=null;
  for(let i=period-1;i<bars.length;i++){if(!chartFinite(atr[i]))continue;const mid=(bars[i].h+bars[i].l)/2,bu=mid+multiplier*atr[i],bl=mid-multiplier*atr[i];upper=upper===null?bu:bu<upper||bars[i-1].c>upper?bu:upper;lower=lower===null?bl:bl>lower||bars[i-1].c<lower?bl:lower;if(direction===null)direction=bars[i].c>=mid?1:-1;else if(direction===1&&bars[i].c<lower)direction=-1;else if(direction===-1&&bars[i].c>upper)direction=1;out[i]={value:direction===1?lower:upper,direction:direction===1?'up':'down',atr:atr[i]};}
  return out;
}
function chartPeriodKeys(bars){if(!bars.length)return null;const dates=bars.map(b=>b.t.slice(0,10));return {day:dates,week:dates.map(d=>{const x=new Date(d+'T00:00:00Z'),day=(x.getUTCDay()+6)%7;x.setUTCDate(x.getUTCDate()-day);return x.toISOString().slice(0,10);}),month:dates.map(d=>d.slice(0,7))};}
function chartPriorPeriodLevels(bars,keys){const out={};for(const key of ['week','month']){const groups=new Map();for(let i=0;i<bars.length;i++){const id=keys[key][i],g=groups.get(id)||{high:-Infinity,low:Infinity,close:null};g.high=Math.max(g.high,bars[i].h);g.low=Math.min(g.low,bars[i].l);g.close=bars[i].c;groups.set(id,g);}const ids=[...groups.keys()],prior=groups.get(ids.at(-2));if(prior)out['prior_'+key]={high:prior.high,low:prior.low,close:prior.close,period:ids.at(-2)};}const prev=bars.at(-2);if(prev)out.prior_day={high:prev.h,low:prev.l,close:prev.c,period:keys.day.at(-2)};return out;}
function chartFairValueGaps(bars){const zones=[];for(let i=2;i<bars.length;i++){const a=bars[i-2],b=bars[i];if(b.l>a.h)zones.push({direction:'up',low:a.h,high:b.l,formed_at:b.t,index:i});else if(b.h<a.l)zones.push({direction:'down',low:b.h,high:a.l,formed_at:b.t,index:i});}return zones.filter(z=>{const after=bars.slice(z.index+1);if(!after.length)return true;return z.direction==='up'?Math.min(...after.map(b=>b.l))>z.low:Math.max(...after.map(b=>b.h))<z.high;}).slice(-12);}
function chartLiquiditySweeps(bars,donchian20){if(bars.length<22||!donchian20)return null;const last=bars.at(-1),prior=bars.slice(-21,-1),low=Math.min(...prior.map(b=>b.l)),high=Math.max(...prior.map(b=>b.h));return {lookback_bars:20,prior_low:low,prior_high:high,bullish_sweep:last.l<low&&last.c>low,bearish_sweep:last.h>high&&last.c<high,bar_at:last.t};}
function chartLatestAverageCross(fast,mid,slow){const cross=(a,b)=>{for(let i=a.length-1;i>0;i--)if(chartFinite(a[i])&&chartFinite(b[i])&&chartFinite(a[i-1])&&chartFinite(b[i-1])&&Math.sign(a[i]-b[i])!==Math.sign(a[i-1]-b[i-1]))return {index:i,bars_ago:a.length-1-i,direction:a[i]>b[i]?'bullish':'bearish'};return null;};return {golden:cross(mid,slow),short_cross:cross(fast,mid)};}
const chartDivergenceGaugeNames={RSI14:'RSI 14',MACD12_26_9:'MACD 12/26/9',SlowStochastic14_3_3:'Slow stochastic',OBV:'On-balance volume',ADLine:'Accumulation/distribution',MFI14:'Money flow index',VolumeEMA5_20:'Volume EMA 5–20'};
function chartMomentumSummary(divergences) {
  // Preserve the established RSI/MACD read used by legacy strategy decisions.
  // Additional gauges are published in the same divergence scan and factor
  // panel, but cannot silently rewrite that signal contract or act as extra votes.
  const canonical=divergences.filter(d=>d.indicator==='RSI14'||d.indicator==='MACD12_26_9'),rsi=canonical.filter(d=>d.indicator==='RSI14'),macd=canonical.filter(d=>d.indicator==='MACD12_26_9');
  const directions=[...new Set(canonical.map(d=>d.kind))];
  const direction=directions.length===0?'none':directions.length===1?directions[0]:'mixed';
  // Counts describe overlapping observations, never independent votes or a score.
  const samePair=(a,b)=>(a.divergence_type??'regular')===(b.divergence_type??'regular')&&a.kind===b.kind&&Number.isInteger(a.first_index)&&Number.isInteger(a.second_index)&&a.first_index<a.second_index&&a.first_index===b.first_index&&a.second_index===b.second_index;
  const aligned=rsi.every(a=>macd.some(b=>samePair(a,b)))&&macd.every(a=>rsi.some(b=>samePair(a,b)));
  const status=rsi.length&&macd.length?(directions.length===1&&aligned?'agreement':'disagreement'):rsi.length?'rsi_only':macd.length?'macd_only':'none';
  return {status,direction,counts:{bullish:canonical.filter(d=>d.kind==='bullish').length,bearish:canonical.filter(d=>d.kind==='bearish').length}};
}
function chartMomentum(divergences, histogram) {
  const current=histogram.at(-1)??null,previous=histogram.at(-2)??null;
  const state=!chartFinite(current)||!chartFinite(previous)?'unavailable':current===0?'neutral':current>0?(previous<=0?'positive_crossing':current<previous?'positive_weakening':current>previous?'positive_building':'positive_holding'):(previous>=0?'negative_crossing':current>previous?'negative_easing':current<previous?'negative_strengthening':'negative_holding');
  const by_type={};for(const type of ['regular','hidden'])by_type[type]=chartMomentumSummary(divergences.filter(d=>(d.divergence_type??'regular')===type));
  return {...chartMomentumSummary(divergences),by_type,histogram:{state,previous,current}};
}
function chartDivergenceNarrative(divergences, momentum) {
  const current=divergences.filter(d=>d.current_status!=='invalidated');
  if(!current.length)return 'Earlier divergences remain recorded, but none is currently intact.';
  const canonical=current.filter(d=>d.indicator==='RSI14'||d.indicator==='MACD12_26_9');
  const stochastic=current.filter(d=>d.indicator==='SlowStochastic14_3_3');
  const volume=current.filter(d=>['OBV','ADLine','MFI14','VolumeEMA5_20'].includes(d.indicator));
  const other=current.filter(d=>!['RSI14','MACD12_26_9','SlowStochastic14_3_3','OBV','ADLine','MFI14','VolumeEMA5_20'].includes(d.indicator));
  const clauses=[];
  if(canonical.length)clauses.push(momentum.status==='agreement'?`RSI and MACD agree on ${momentum.direction} divergence; they are one related momentum assessment.`:momentum.status==='disagreement'?'RSI and MACD do not confirm the same divergence type and direction at the same price pivots; momentum evidence is not aligned.':`Only ${momentum.status==='rsi_only'?'RSI':'MACD'} in the RSI/MACD momentum pair has a qualifying divergence in these bars.`);
  if(stochastic.length)clauses.push(`Slow stochastic also shows ${[...new Set(stochastic.map(d=>`${d.divergence_type??'regular'} ${d.kind}`))].join(' and ')} divergence evidence.`);
  if(volume.length)clauses.push(`Volume participation gauges with qualifying divergence: ${[...new Set(volume.map(d=>chartDivergenceGaugeNames[d.indicator]||d.indicator))].join(', ')}.`);
  if(other.length)clauses.push(`Other divergence gauges: ${[...new Set(other.map(d=>chartDivergenceGaugeNames[d.indicator]||d.indicator))].join(', ')}.`);
  return clauses.join(' ')||'Current divergence evidence is present; gauge family is not classified.';
}
function chartDivergenceType(kind, firstPrice, secondPrice, firstValue, secondValue) {
  if(![firstPrice,secondPrice,firstValue,secondValue].every(chartFinite))return null;
  if(kind==='bullish')return secondPrice<firstPrice&&secondValue>firstValue?'regular':secondPrice>firstPrice&&secondValue<firstValue?'hidden':null;
  if(kind==='bearish')return secondPrice>firstPrice&&secondValue<firstValue?'regular':secondPrice<firstPrice&&secondValue>firstValue?'hidden':null;
  return null;
}
function chartPatternScan(bars,pivots,atr,completedAt,existing=[]) {
  const ids=['head_shoulders','inverse_head_shoulders','double_top','double_bottom','triple_top','ascending_triangle','descending_triangle','symmetrical_triangle','rising_wedge','falling_wedge','expanding_wedge','bull_flag','bear_flag','bull_pennant','bear_pennant','cup_handle','inverted_cup_handle','rectangle','rising_channel','falling_channel'];
  const minimum={head_shoulders:40,inverse_head_shoulders:40,double_top:30,double_bottom:60,triple_top:50,ascending_triangle:40,descending_triangle:40,symmetrical_triangle:40,rising_wedge:40,falling_wedge:40,expanding_wedge:40,bull_flag:35,bear_flag:35,bull_pennant:35,bear_pennant:35,cup_handle:60,inverted_cup_handle:60,rectangle:40,rising_channel:40,falling_channel:40};
  const detectors=Object.fromEntries(ids.map(id=>[id,{status:bars.length>=minimum[id]?'measured':'insufficient_history',minimum_bars:minimum[id],matches:[]} ])),events=[];
  const last=bars.at(-1),scaleAt=i=>chartFinite(atr[i])&&atr[i]>0?atr[i]:Math.max(last.c*.01,1e-9),scale=scaleAt(bars.length-1),startIndex=Math.max(0,bars.length-120),counts=new Map();for(const p of pivots)counts.set(p.index,(counts.get(p.index)||0)+1);
  const clean=pivots.filter(p=>counts.get(p.index)===1&&p.index>=startIndex).sort((a,b)=>a.index-b.index),sequence=[];
  for(const p of clean){const prior=sequence.at(-1);if(prior?.kind===p.kind){const moreExtreme=p.kind==='support'?p.price<prior.price:p.price>prior.price;if(moreExtreme)sequence[sequence.length-1]=p;}else sequence.push(p);}
  const toId=p=>p.kind==='support'?'low':'high';
  const save=(id,value)=>{const eventKind=value.kind||id,eventIndex=events.findIndex(x=>x.kind===eventKind),matchIndex=detectors[id].matches.findIndex(x=>x.kind===eventKind),prior=eventIndex<0?null:events[eventIndex],merged=prior?{...prior,...value,...(value.geometry||!prior.geometry?{}:{geometry:prior.geometry})}:value;if(eventIndex<0)events.push(merged);else events[eventIndex]=merged;if(matchIndex<0)detectors[id].matches.push(merged);else detectors[id].matches[matchIndex]=merged;};
  const add=(id,event)=>{if(!detectors[id]||detectors[id].status!=='measured')return;save(id,{kind:id,...event});};
  for(const p of existing){const id=p.kind==='converging_range'?'symmetrical_triangle':p.kind;if(detectors[id])save(id,{...p});}
  const fit=points=>{if(points.length<2)return null;const mx=points.reduce((s,p)=>s+p.index,0)/points.length,my=points.reduce((s,p)=>s+p.price,0)/points.length,den=points.reduce((s,p)=>s+(p.index-mx)**2,0);if(!den)return null;const slope=points.reduce((s,p)=>s+(p.index-mx)*(p.price-my),0)/den,intercept=my-slope*mx;return {slope,intercept,at:i=>slope*i+intercept};};
  const extrema=(kind,from=0,to=bars.length-1)=>pivots.filter(p=>p.kind===kind&&p.index>=from&&p.index<=to&&counts.get(p.index)===1).sort((a,b)=>a.index-b.index);
  // Shoulder/head geometry uses five confirmed alternating pivots. Exact
  // tolerance is ATR/price normalized, so a fixed-dollar threshold never leaks.
  for(const [id,inverse] of [['head_shoulders',false],['inverse_head_shoulders',true]]){
    const q=sequence.slice(-5),expected=inverse?['support','resistance','support','resistance','support']:['resistance','support','resistance','support','resistance'];
    if(q.length!==5||q.some((p,i)=>p.kind!==expected[i])||bars.length<minimum[id])continue;
    const shoulderA=q[0].price,head=q[2].price,shoulderB=q[4].price,near=Math.max(.5*scale,.015*(shoulderA+shoulderB)/2),neckA=q[1],neckB=q[3],neckFit=fit([neckA,neckB]),neck=neckFit?.at(bars.length-1);
    const necklineDepth=inverse?neck-head:head-neck;
    // The projected neckline must remain between the head and the breakout
    // direction. Extrapolation from two troughs can otherwise carry a rising
    // bearish neckline above the head (or a falling inverse neckline below
    // it), creating a confirmed break and target with impossible geometry.
    if(!neckFit||Math.abs(shoulderA-shoulderB)>near||!((inverse?head<Math.min(shoulderA,shoulderB)-.35*scale:head>Math.max(shoulderA,shoulderB)+.35*scale))||!chartFinite(necklineDepth)||necklineDepth<=.15*scale)continue;
     const broke=inverse?last.c>neck+.15*scale:last.c<neck-.15*scale,invalid=inverse?last.c<head-.5*scale:last.c>head+.5*scale;
     add(id,{state:broke?'confirmed_break':invalid?'invalidated':'forming',direction:inverse?'up':'down',start_index:q[0].index,confirmed_at:q.at(-1).confirmed_at,break_at:broke?completedAt(bars.length-1):null,neckline:neck,invalidation_level:head,measured_target_price:neck+(inverse?1:-1)*Math.abs(head-neck),pivot_indexes:q.map(p=>p.index),description:`${inverse?'Inverse ':''}head and shoulders: outer shoulders ${chartFmt(shoulderA)} / ${chartFmt(shoulderB)}, head ${chartFmt(head)}, projected neckline ${chartFmt(neck)}. ${broke?'A completed close has broken the neckline.':invalid?'Price closed beyond the head, invalidating the shape.':'The confirmed shape has not closed through its neckline.'}`});
  }
  // Repeated highs/lows require a meaningful intervening rejection and a
  // prior trend; matched extrema alone are not labeled as a reversal.
  for(const [id,kind,count,side] of [['double_top','resistance',2,'down'],['triple_top','resistance',3,'down']]){
    const points=extrema(kind).slice(-count);if(points.length!==count||bars.length<minimum[id])continue;const first=points[0],lastPoint=points.at(-1),prior=bars[Math.max(0,first.index-15)].c,level=points.reduce((s,p)=>s+p.price,0)/count,tol=Math.max(.45*scale,.0075*level),between=extrema('support',first.index,lastPoint.index),neckline=between.length?Math.min(...between.map(p=>p.price)):null;
    if(lastPoint.index-first.index<8||lastPoint.index-first.index>90||Math.max(...points.map(p=>p.price))-Math.min(...points.map(p=>p.price))>tol||!chartFinite(neckline)||neckline>=level-scale||level-prior<.75*scale)continue;
    const broke=last.c<neckline-.15*scale,invalid=last.c>level+.5*scale;add(id,{state:broke?'confirmed_break':invalid?'invalidated':'forming',direction:'down',start_index:first.index,confirmed_at:lastPoint.confirmed_at,break_at:broke?completedAt(bars.length-1):null,neckline,invalidation_level:level,measured_target_price:neckline-(level-neckline),pivot_indexes:points.map(p=>p.index),description:`${count===2?'Double':'Triple'} top near ${chartFmt(level)} with intervening support ${chartFmt(neckline)}. ${broke?'A completed close broke below the support.':invalid?'Price closed back above the topping zone.':'No buffered support break is confirmed.'}`});
  }
  const highs=extrema('resistance'),lows=extrema('support');
  const triples=points=>points.slice(-3);
  if(bars.length>=40&&triples(highs).length===3&&triples(lows).length===3){
    const hp=triples(highs),lp=triples(lows),span=Math.min(hp.at(-1).index,lp.at(-1).index)-Math.max(hp[0].index,lp[0].index),hi=fit(hp),lo=fit(lp),from=Math.max(hp[0].index,lp[0].index),to=bars.length-1,upper0=hi?.at(from),lower0=lo?.at(from),upper=hi?.at(to),lower=lo?.at(to),width0=upper0-lower0,width=upper-lower;
    if(span>=12&&width0>0&&width>0){
      const us=(hi.slope*span)/scale,ls=(lo.slope*span)/scale,converging=width<=width0*.85,diverging=width>=width0*1.2,flatU=Math.abs(us)<=.7,flatL=Math.abs(ls)<=.7,readyIndex=Math.max(hp.at(-1).confirmation_index??hp.at(-1).index,lp.at(-1).confirmation_index??lp.at(-1).index);
      // Find the first completed close outside the confirmed formation. Keeping
      // the first crossing prevents a continuing breakout from being relabeled
      // as a new break every day and pins the measured move to its real origin.
      let firstBreak=null;
      for(let i=Math.max(from,readyIndex+1);i<=to;i++){
        const buffer=.15*scaleAt(i),close=bars[i].c;
        if(close>hi.at(i)+buffer){firstBreak={direction:'up',index:i};break;}
        if(close<lo.at(i)-buffer){firstBreak={direction:'down',index:i};break;}
      }
      let breakState={state:'forming',direction:null,break_at:null,break_index:null};
      if(firstBreak){const currentLine=firstBreak.direction==='up'?upper:lower,buffer=.15*scaleAt(to),stillOutside=firstBreak.direction==='up'?last.c>currentLine+buffer:last.c<currentLine-buffer;breakState={state:stillOutside?'confirmed_break':'failed_breakout',direction:firstBreak.direction,break_at:completedAt(firstBreak.index),break_index:firstBreak.index,...(stillOutside?{}:{failed_at:completedAt(to)})};}
      const event=(id,description,geometry=null)=>{
        const breakLevel=breakState.direction==='up'&&Number.isInteger(breakState.break_index)?hi.at(breakState.break_index):breakState.direction==='down'&&Number.isInteger(breakState.break_index)?lo.at(breakState.break_index):null;
        // A pattern objective uses the formation's widest measured height at
        // the actual break, not the nearly-zero residual width at the apex.
        const target=breakLevel===null?null:breakState.direction==='up'?breakLevel+width0:breakLevel-width0;
        const outcome=breakState.state==='forming'?'No boundary break is confirmed on a completed close.':breakState.state==='failed_breakout'?'An earlier boundary break failed when price returned inside the pattern.':id==='ascending_triangle'?breakState.direction==='up'?'A completed close broke above the flat ceiling.':'A completed close broke below the rising floor, a downside break against the usual bullish pattern bias.':id==='descending_triangle'?breakState.direction==='down'?'A completed close broke below the flat floor.':'A completed close broke above falling resistance, an upside break against the usual bearish pattern bias.':id==='symmetrical_triangle'?`A completed close broke ${breakState.direction==='up'?'above the upper':'below the lower'} boundary.`:`A completed close broke ${breakState.direction==='up'?'above resistance':'below support'}.`;
        add(id,{...breakState,start_index:from,confirmed_at:completedAt(readyIndex),support:lower,resistance:upper,upper_slope_atr:us,lower_slope_atr:ls,...(geometry?{geometry}:{}),measured_target_price:target,description:`${description} ${outcome}`});
      };
    const geometry={type:converging?'converging_boundaries':'diverging_boundaries',start_index:from,end_index:to,upper_start:upper0,upper_end:upper,lower_start:lower0,lower_end:lower};
    if(converging&&flatU&&ls>.7)event('ascending_triangle','Ascending triangle: resistance is nearly flat and confirmed lows rise.',geometry);
    if(converging&&flatL&&us<-.7)event('descending_triangle','Descending triangle: support is nearly flat and confirmed highs fall.',geometry);
    if(converging&&us<-.7&&ls>.7&&!existing.some(p=>p.kind==='converging_range'&&p.state==='forming')){
      event('symmetrical_triangle','Symmetrical triangle: confirmed highs descend and lows ascend.',geometry);
    }
      if(converging&&us>.7&&ls>us+.35)event('rising_wedge','Rising wedge: both confirmed boundaries rise, with support advancing faster into a narrowing range.',geometry);
      if(converging&&ls<-.7&&us<ls-.35)event('falling_wedge','Falling wedge: both confirmed boundaries fall, with resistance descending faster into a narrowing range.',geometry);
      if(diverging&&us>.7&&ls<-.7)event('expanding_wedge','Expanding wedge: confirmed highs expand upward while confirmed lows expand downward.',geometry);
      if(flatU&&flatL&&Math.abs(width-width0)<=width0*.35)event('rectangle','Rectangle: repeated confirmed highs and lows bound a broadly level range.',geometry);
      if(!converging&&!diverging&&Math.abs(us-ls)<=.8&&us>.7)event('rising_channel','Rising channel: support and resistance rise at similar ATR-scaled rates.',geometry);
      if(!converging&&!diverging&&Math.abs(us-ls)<=.8&&us<-.7)event('falling_channel','Falling channel: support and resistance fall at similar ATR-scaled rates.',geometry);
    }
  }
  // Flags and pennants require an impulse pole followed by a compact pause.
  if(bars.length>=35){
    const cons=bars.slice(-10,-1),pole=bars.slice(-20,-10),poleStart=pole[0].c,poleEnd=pole.at(-1).c,poleMove=poleEnd-poleStart,poleRange=Math.abs(poleMove),priorAtr=scaleAt(bars.length-11),consHigh=Math.max(...cons.map(b=>b.h)),consLow=Math.min(...cons.map(b=>b.l)),retracement=poleMove>0?(consHigh-Math.min(...cons.map(b=>b.l)))/poleRange:(Math.max(...cons.map(b=>b.h))-consLow)/poleRange,highFit=fit(cons.map((b,i)=>({index:bars.length-10+i,price:b.h}))),lowFit=fit(cons.map((b,i)=>({index:bars.length-10+i,price:b.l}))),u=highFit?.slope*8/priorAtr,l=lowFit?.slope*8/priorAtr,width0=highFit.at(bars.length-10)-lowFit.at(bars.length-10),width1=highFit.at(bars.length-2)-lowFit.at(bars.length-2),pennant=width0>0&&width1<width0*.85;
    if(poleRange>=2.5*priorAtr&&poleMove>0&&retracement<=.6&&l<.6){
      const buffer=.15*scale,confirmationLevel=consHigh+buffer,invalidationLevel=consLow,invalidationConfirmationLevel=invalidationLevel-buffer,
        broke=last.c>confirmationLevel,invalid=last.c<invalidationConfirmationLevel,state=broke?'confirmed_break':invalid?'invalidated':'forming',name=pennant?'bull_pennant':'bull_flag',shape=pennant?'pennant':'flag';
      add(name,{state,direction:'up',start_index:bars.length-20,break_at:broke?completedAt(bars.length-1):null,neckline:consHigh,invalidation_level:invalidationLevel,invalidation_confirmation_level:invalidationConfirmationLevel,invalidation_buffer_atr:.15,measured_target_price:broke?consHigh+poleRange:null,description:`Bull ${shape} candidate after a ${chartFmt(poleRange/priorAtr)} ATR advance; the pause retraced ${chartFmt(retracement*100,0)}% of the pole. ${broke?'A completed close cleared the pause high.':invalid?`A completed close fell below the pause low at ${chartFmt(invalidationLevel)}, invalidating the pattern.`:'The pause high has not been cleared on a completed close.'}`});
    }
    if(poleRange>=2.5*priorAtr&&poleMove<0&&retracement<=.6&&u>-.6){
      const buffer=.15*scale,confirmationLevel=consLow-buffer,invalidationLevel=consHigh,invalidationConfirmationLevel=invalidationLevel+buffer,
        broke=last.c<confirmationLevel,invalid=last.c>invalidationConfirmationLevel,state=broke?'confirmed_break':invalid?'invalidated':'forming',name=pennant?'bear_pennant':'bear_flag',shape=pennant?'pennant':'flag';
      add(name,{state,direction:'down',start_index:bars.length-20,break_at:broke?completedAt(bars.length-1):null,neckline:consLow,invalidation_level:invalidationLevel,invalidation_confirmation_level:invalidationConfirmationLevel,invalidation_buffer_atr:.15,measured_target_price:broke?consLow-poleRange:null,description:`Bear ${shape} candidate after a ${chartFmt(poleRange/priorAtr)} ATR decline; the pause retraced ${chartFmt(retracement*100,0)}% of the pole. ${broke?'A completed close broke the pause low.':invalid?`A completed close rose above the pause high at ${chartFmt(invalidationLevel)}, invalidating the pattern.`:'The pause low has not been broken on a completed close.'}`});
    }
  }
  // A cup needs two comparable rims, a centered bowl and a shallow handle.
  const cup=(inverse)=>{
    const rims=extrema(inverse?'support':'resistance'),handles=extrema(inverse?'resistance':'support');
    for(const right of rims.slice(-4).reverse()){
      const left=rims.filter(p=>p.index<right.index&&right.index-p.index>=25&&right.index-p.index<=100).at(-1);if(!left)continue;
      const troughs=extrema(inverse?'resistance':'support',left.index,right.index),bottom=inverse?troughs.length?Math.max(...troughs.map(p=>p.price)):null:troughs.length?Math.min(...troughs.map(p=>p.price)):null;if(bottom===null)continue;
      const rim=(left.price+right.price)/2,depth=inverse?bottom-rim:rim-bottom;if(depth<2*scale||Math.abs(left.price-right.price)>Math.max(.7*scale,.012*rim))continue;
      const after=handles.filter(p=>p.index>right.index&&bars.length-1-p.index<=20).at(-1);if(!after)continue;
      const handleDepth=inverse?after.price-right.price:right.price-after.price;if(handleDepth<.2*scale||handleDepth>.45*depth)continue;
      const level=rim,buffer=.15*scale,confirmationLevel=inverse?level-buffer:level+buffer,
        invalidationLevel=after.price,invalidationConfirmationLevel=inverse?invalidationLevel+buffer:invalidationLevel-buffer,
        broke=inverse?last.c<confirmationLevel:last.c>confirmationLevel,
        invalid=inverse?last.c>invalidationConfirmationLevel:last.c<invalidationConfirmationLevel,
        state=broke?'confirmed_break':invalid?'invalidated':'forming',
        breakText=inverse?`A completed close cleared the buffered confirmation level at ${chartFmt(confirmationLevel)} below the raw rim at ${chartFmt(level)}, confirming a downside break.`:`A completed close cleared the buffered confirmation level at ${chartFmt(confirmationLevel)} above the raw rim at ${chartFmt(level)}, confirming an upside break.`,
        invalidText=inverse?`A completed close rose above the confirmed handle high at ${chartFmt(invalidationLevel)}, invalidating the shape.`:`A completed close fell below the confirmed handle low at ${chartFmt(invalidationLevel)}, invalidating the shape.`,
        formingText=inverse?`No completed close has cleared the buffered confirmation level at ${chartFmt(confirmationLevel)} below the raw rim at ${chartFmt(level)}.`:`No completed close has cleared the buffered confirmation level at ${chartFmt(confirmationLevel)} above the raw rim at ${chartFmt(level)}.`;
      return {state,direction:inverse?'down':'up',start_index:left.index,confirmed_at:after.confirmed_at,break_at:broke?completedAt(bars.length-1):null,neckline:level,confirmation_level:confirmationLevel,confirmation_buffer_atr:.15,invalidation_level:invalidationLevel,invalidation_confirmation_level:invalidationConfirmationLevel,invalidation_buffer_atr:.15,measured_target_price:broke?(inverse?level-depth:level+depth):null,pivot_indexes:[left.index,...troughs.map(p=>p.index),right.index,after.index],description:`${inverse?'Inverted cup and handle':'Cup and handle'}: rims near ${chartFmt(rim)}, measured bowl depth ${chartFmt(depth)}, and a ${chartFmt(handleDepth)} handle. ${broke?breakText:invalid?invalidText:formingText}`};
    }
    return null;
  };
  if(bars.length>=minimum.cup_handle){const bull=cup(false),bear=cup(true);if(bull)add('cup_handle',bull);if(bear)add('inverted_cup_handle',bear);}
  for(const pattern of events){
    if(pattern.state!=='confirmed_break'||!chartFinite(pattern.measured_target_price)||!['up','down'].includes(pattern.direction))continue;
    const reached=pattern.direction==='up'?last.c>=pattern.measured_target_price:last.c<=pattern.measured_target_price;
    pattern.measured_target_status=reached?'reached':'ahead';
    if(reached)pattern.description+=` The measured objective at ${chartFmt(pattern.measured_target_price)} has already been reached; it is not a forward target.`;
  }
  const mapped=Object.fromEntries(ids.map(id=>{const matches=detectors[id].matches;return [id,{status:detectors[id].status,minimum_bars:minimum[id],matches:matches.length,method:'confirmed pivots and bounded OHLC templates'}];}));
  return {method:'confirmed-pivot-templates-2',status:'available',bars:bars.length,lookback:120,detectors:mapped,events};
}
function chartStructure(lowPair, highPair) {
  return lowPair.length===2&&highPair.length===2?(lowPair[1].price>lowPair[0].price&&highPair[1].price>highPair[0].price?'higher_highs_higher_lows':lowPair[1].price<lowPair[0].price&&highPair[1].price<highPair[0].price?'lower_highs_lower_lows':'mixed'):null;
}
function chartFmt(x) {
  if(!chartFinite(x))return 'unavailable';const a=Math.abs(x);
  if(a>0&&a<1e-10)return x.toExponential(4);
  const digits=a>0&&a<1?Math.min(12,Math.max(4,4-Math.floor(Math.log10(a)))):2;
  return chartFormatNumber(x,{maximumFractionDigits:digits});
}
function explainChart(series, now=Date.now()) {
  const base={method:CHART_READ_METHOD,status:'unavailable',as_of:null,summary:'Chart measurements are unavailable.',sections:[],metrics:{},levels:[],lines:[],indicators:{sma10:[],sma20:[],sma50:[],sma200:[],rsi14:[],macd:[],macd_signal:[],macd_histogram:[],slow_stochastic:[],obv:[],ad_line:[],mfi14:[],volume_ema5_20:[]},extended:{formula_version:'ohlcv-extensions-1',status:'unavailable'},momentum:chartMomentum([],[]),patterns:[],pattern_scan:{method:'confirmed-pivot-templates-2',status:'unavailable',bars:0,detectors:{}},divergences:[],divergence_scan:{gauges_checked:0,gauges_available:0,comparisons:0,eligible_pivot_pairs:{bullish:false,bearish:false},gauge_availability:[]},pivots:[]};
  const fail=reason=>({...base,reason});
  if(!series||typeof series!=='object')return fail('missing_series');
  const rows=series.bars??series.candles, end=chartTime(series.last_completed_at), observed=chartTime(series.observed_at), received=chartTime(series.received_at);
  now=typeof now==='string'?chartTime(now):now;
  // A source adapter may know completed daily sessions without an exact close or
  // receipt timestamp. Preserve that absence; do not invent a final-pivot clock.
  if(!chartFinite(now)||observed===null||(series.last_completed_at!=null&&end===null)||(series.received_at!=null&&received===null)||(end!==null&&(end>now||end>observed))||observed>now||(received!==null&&(received>now||(end!==null&&end>received))))return fail('invalid_completion_or_receipt_clock');
  if(!Array.isArray(rows)||!rows.length||rows.length>260)return fail('invalid_bar_count');
  const bars=[];let previous=-Infinity;
  for(const row of rows) {
    if(!Array.isArray(row)||row.length!==6)return fail('invalid_bar_shape');
    const [t,o,h,l,c,v]=row, ms=chartTime(t);
    if(ms===null||ms<=previous||ms>=now||ms>observed||(end!==null&&ms>=end)||![o,h,l,c].every(chartFinite)||Math.min(o,h,l,c)<=0||h<Math.max(o,l,c)||l>Math.min(o,h,c)||(v!==null&&(!chartFinite(v)||v<0)))return fail('invalid_bar');
    bars.push({t,ms,o,h,l,c,v});previous=ms;
  }
  const n=bars.length,last=bars[n-1],closes=bars.map(b=>b.c),sma10=chartSma(closes,10),sma20=chartSma(closes,20),sma50=chartSma(closes,50),sma200=chartSma(closes,200),rsi=chartRsi(closes),macd=chartMacd(closes),divergenceIndicators=chartDivergenceIndicators(bars,closes),
    gaugeSeries=[['RSI14',rsi],['MACD12_26_9',macd.macd],['SlowStochastic14_3_3',divergenceIndicators.slow_stochastic],['OBV',divergenceIndicators.obv],['ADLine',divergenceIndicators.ad_line],['MFI14',divergenceIndicators.mfi14],['VolumeEMA5_20',divergenceIndicators.volume_ema5_20]];
  const tr=bars.map((b,i)=>i?Math.max(b.h-b.l,Math.abs(b.h-bars[i-1].c),Math.abs(b.l-bars[i-1].c)):b.h-b.l),atr=chartWilder(tr,14),a=atr[n-1],extended=chartAdvancedIndicators(bars,rsi,divergenceIndicators.ad_line,atr);
  const completedAt=i=>i===n-1?(end===null?null:new Date(end).toISOString()):bars[i+1].t;
  const pivots=[];
  for(let i=2;i<n-2;i++) {
    const neighbors=[bars[i-2],bars[i-1],bars[i+1],bars[i+2]],b=bars[i];
    for(const [kind,field]of[['support','l'],['resistance','h']]) {
      if(!neighbors.every(x=>kind==='support'?b[field]<x[field]:b[field]>x[field]))continue;
      const firstReachedIndex=bars.findIndex((later,j)=>j>i&&(kind==='support'?later.l<=b[field]:later.h>=b[field]));
      pivots.push({kind,index:i,price:b[field],pivot_at:b.t,confirmation_index:i+2,confirmation_bar_at:bars[i+2].t,confirmed_at:completedAt(i+2),confirmation_clock:i+2===n-1?(end===null?'unknown_final_close':'verified_final_close'):'next_open_upper_bound',reached_after_pivot:firstReachedIndex>=0,first_reached_at:firstReachedIndex>=0?completedAt(firstReachedIndex):null});
    }
  }
  const lows=pivots.filter(p=>p.kind==='support'),highs=pivots.filter(p=>p.kind==='resistance'),lastTwo=xs=>xs.slice(-2),lowPair=lastTwo(lows),highPair=lastTwo(highs);
  const structure=chartStructure(lowPair,highPair);
  // Pivot-pair geometry is historical until another pivot confirms. A current
  // completed close can already invalidate that structure in the meantime.
  const lastSwingLow=lows.at(-1)?.price??null,lastSwingHigh=highs.at(-1)?.price??null;
  const structureBreach=structure==='higher_highs_higher_lows'&&last.c<lastSwingLow?'bullish_failed':structure==='lower_highs_lower_lows'&&last.c>lastSwingHigh?'bearish_failed':null;
  const support=[...lows].filter(p=>p.price<=last.c).sort((x,y)=>y.price-x.price||y.index-x.index)[0]??null;
  const resistance=[...highs].filter(p=>p.price>=last.c).sort((x,y)=>x.price-y.price||y.index-x.index)[0]??null;
  const level=p=>({...p,label:p.kind==='support'?'Confirmed support':'Confirmed resistance',distance_atr:a>0?(last.c-p.price)/a:null});
  const levels=[support&&level(support),resistance&&level(resistance)].filter(Boolean),lines=[];
  for(const [kind,pair] of [['support',lowPair],['resistance',highPair]]) {
    if(pair.length!==2||pair[1].index-pair[0].index<3)continue;
    const [p,q]=pair,slope=(q.price-p.price)/(q.index-p.index),value=i=>p.price+slope*(i-p.index);
    const evaluated=bars.slice(q.confirmation_index).map((b,j)=>({i:q.confirmation_index+j,b})).filter(({i})=>chartFinite(atr[i]));
    const breaks=evaluated.filter(({i,b})=>kind==='support'?b.c<value(i)-.1*atr[i]:b.c>value(i)+.1*atr[i]);
    lines.push({kind,start_index:p.index,end_index:n-1,start_price:p.price,end_price:value(n-1),anchor_index:q.index,anchor_price:q.price,slope_per_bar:slope,state:!evaluated.length?'untested':breaks.length?'broken':'intact',tested_bars:evaluated.length,first_break_at:breaks.length?completedAt(breaks[0].i):null,confirmed_at:q.confirmed_at,tested_from:evaluated.length?completedAt(evaluated[0].i):null});
  }
  const divergences=[];let divergenceComparisons=0;const gaugesChecked=new Set(),eligiblePivotPairs={bullish:false,bearish:false};
  for(const [kind,pair] of [['bullish',lowPair],['bearish',highPair]]) {
    if(pair.length!==2)continue;const[p,q]=pair;
    if(q.index-p.index<5||q.index-p.index>60||n-1-q.index>30)continue;eligiblePivotPairs[kind]=true;
    for(const[indicator,values]of gaugeSeries) {
      if(['OBV','ADLine','VolumeEMA5_20'].includes(indicator)&&divergenceIndicators.volume_segments[p.index]!==divergenceIndicators.volume_segments[q.index])continue;
      const first=values[p.index],second=values[q.index];if(!chartFinite(first)||!chartFinite(second))continue;
      divergenceComparisons++;gaugesChecked.add(indicator);
      const divergence_type=chartDivergenceType(kind,p.price,q.price,first,second);if(divergence_type===null)continue;
      // Context belongs to the divergence's confirmation boundary, not a later
      // swing that appears when future bars are appended to the displayed chart.
      const known=pivots.filter(x=>x.confirmation_index<=q.confirmation_index),prevailing_structure=chartStructure(known.filter(x=>x.kind==='support').slice(-2),known.filter(x=>x.kind==='resistance').slice(-2));
      const aligned=kind==='bullish'?'higher_highs_higher_lows':'lower_highs_lower_lows';
      const continuation_alignment=divergence_type==='regular'?'not_applicable':prevailing_structure===null?'unknown':prevailing_structure===aligned?'aligned':prevailing_structure==='mixed'?'mixed':'opposed';
      // Historical alignment never changes. A later completed close beyond the
      // second pivot ends this hidden continuation read, even after a rebound.
      // Earlier bars have known bar times, not necessarily exact close clocks.
      const invalidated=divergence_type==='hidden'?bars.findIndex((b,i)=>i>=q.confirmation_index&&(kind==='bullish'?b.c<q.price:b.c>q.price)):-1;
      const validity=divergence_type==='hidden'?{current_status:invalidated<0?'intact':'invalidated',invalidation_level:q.price,invalidated_bar_at:invalidated<0?null:bars[invalidated].t,invalidated_at:invalidated===n-1&&end!==null?completedAt(invalidated):null,invalidated_close:invalidated<0?null:bars[invalidated].c}:{};
      divergences.push({kind,indicator,indicator_label:chartDivergenceGaugeNames[indicator],divergence_type,first_index:p.index,second_index:q.index,first_price:p.price,second_price:q.price,first_value:first,second_value:second,...(indicator==='RSI14'?{first_rsi:first,second_rsi:second}:{}),first_confirmed_at:p.confirmed_at,first_confirmation_bar_at:p.confirmation_bar_at,confirmed_at:q.confirmed_at,confirmation_bar_at:q.confirmation_bar_at,prevailing_structure,continuation_alignment,structure_as_of:q.confirmed_at,...validity});
    }
  }
  const currentDivergences=divergences.filter(d=>d.current_status!=='invalidated');
  const momentum=chartMomentum(currentDivergences,macd.histogram);
  const gaugeAvailability=gaugeSeries.map(([name,values])=>({name,status:chartFinite(values.at(-1))?'available':'insufficient_history'})),gaugesAvailable=gaugeAvailability.filter(x=>x.status==='available').length;
  const patterns=[];
  if(lowPair.length===2&&highPair.length===2) {
    const [l1,l2]=lowPair,[h1,h2]=highPair,sl=(l2.price-l1.price)/(l2.index-l1.index),sh=(h2.price-h1.price)/(h2.index-h1.index),start=Math.max(l1.index,h1.index),known=Math.max(l2.confirmation_index,h2.confirmation_index),bottom=i=>l1.price+sl*(i-l1.index),top=i=>h1.price+sh*(i-h1.index);
    const width=top(n-1)-bottom(n-1),oldWidth=top(start)-bottom(start);
    if(l2.index-l1.index>=5&&h2.index-h1.index>=5&&sl>0&&sh<0&&width>0&&width<oldWidth&&known<n&&bars.slice(known).every((b,j)=>b.c>=bottom(known+j)&&b.c<=top(known+j)))patterns.push({kind:'converging_range',state:'forming',start_index:start,confirmed_at:completedAt(known),support:bottom(n-1),resistance:top(n-1),width,geometry:{type:'converging_boundaries',start_index:start,end_index:n-1,upper_start:top(start),upper_end:top(n-1),lower_start:bottom(start),lower_end:bottom(n-1)},description:'Rising confirmed lows and falling confirmed highs narrow the range; price remains inside.'});
  }
  if(lowPair.length===2) {
    const[p,q]=lowPair,scale=atr[q.confirmation_index],prior=Math.max(0,p.index-30),span=q.index-p.index;
    if(scale>0&&p.index-prior>=15&&span>=10&&span<=60&&n-1-q.index<=30&&Math.abs(p.price-q.price)<=.5*scale&&bars[p.index].c<=bars[prior].c-scale) {
      const middle=bars.slice(p.index+1,q.index),neckline=Math.max(...middle.map(b=>b.h));
      if(neckline-Math.max(p.price,q.price)>=scale) {
        const floor=Math.min(p.price,q.price),invalidated=bars.findIndex((b,i)=>i>=q.confirmation_index&&b.c<floor);
        const hit=bars.findIndex((b,i)=>i>=q.confirmation_index&&i<=q.index+30&&(invalidated<0||i<invalidated)&&atr[i]>0&&b.c>neckline+.25*atr[i]);
        patterns.push({kind:'double_bottom',state:invalidated>=0?'invalidated':hit<0?'forming':last.c>neckline?'confirmed_break':'back_below_neckline',direction:'up',first_index:p.index,second_index:q.index,neckline,confirmed_at:q.confirmed_at,break_at:hit<0?null:completedAt(hit),invalidation_level:floor,measured_target_price:hit<0?null:neckline+(neckline-floor),invalidated_at:invalidated<0?null:completedAt(invalidated),description:invalidated>=0?'A completed close below both confirmed bottoms invalidated this pattern.':hit<0?'Two comparable confirmed lows follow a decline; the neckline has not closed above its confirmation buffer.':last.c>neckline?'Two comparable confirmed lows were followed by a buffered close above the intervening high.':'A prior neckline break has returned below the intervening high.'});
      }
    }
  }
  const patternScan=chartPatternScan(bars,pivots,atr,completedAt,patterns);patterns.splice(0,patterns.length,...patternScan.events);
  // Fib shelves are measured locations on an explicitly named, confirmed swing.
  // Ambiguous bars that are both a high and a low never anchor this calculation.
  const counts=new Map();for(const p of pivots)counts.set(p.index,(counts.get(p.index)||0)+1);
  const clean=pivots.filter(p=>counts.get(p.index)===1),z=clean.at(-1),y=clean.slice(0,-1).reverse().find(p=>z&&p.kind!==z.kind);
  if(y&&z) {
    const scale=atr[z.confirmation_index],move=Math.abs(z.price-y.price);
    if(scale>0&&move>3*scale&&z.index-y.index>=3)for(const ratio of [.382,.5,.618])levels.push({kind:'fib',label:`${ratio*100}% of confirmed ${z.price>y.price?'upswing':'downswing'}`,ratio,price:z.price+(y.price-z.price)*ratio,start_index:y.index,end_index:z.index,start_price:y.price,end_price:z.price,confirmed_at:z.confirmed_at});
  }
  const vols=n>=21?bars.slice(n-21,n-1).map(b=>b.v):[],avgVol=vols.length===20&&vols.every(chartFinite)?vols.reduce((x,y)=>x+y,0)/20:null;
  const rvol=avgVol>0&&last.v!==null?last.v/avgVol:null,range=last.h-last.l,body=Math.abs(last.c-last.o),prev=bars.at(-2);
  const candle={direction:last.c>last.o?'up':last.c<last.o?'down':'flat',body_fraction:range>0?body/range:null,upper_wick_fraction:range>0?(last.h-Math.max(last.o,last.c))/range:null,lower_wick_fraction:range>0?(Math.min(last.o,last.c)-last.l)/range:null,close_location:range>0?(last.c-last.l)/range:null,engulfing:prev&&last.c>last.o&&prev.c<prev.o&&last.o<=prev.c&&last.c>=prev.o?'bullish':prev&&last.c<last.o&&prev.c>prev.o&&last.o>=prev.c&&last.c<=prev.o?'bearish':null};
  const metrics={close:last.c,bar_count:n,sma10:sma10.at(-1),sma20:sma20.at(-1),sma50:sma50.at(-1),sma200:sma200.at(-1),rsi14:rsi.at(-1),macd:macd.macd.at(-1),macd_signal:macd.signal.at(-1),macd_histogram:macd.histogram.at(-1),atr14:a,atr_percent:a===null?null:a/last.c*100,relative_volume:rvol,prior20_average_volume:avgVol,structure,structure_breach:structureBreach,last_swing_low:lastSwingLow,last_swing_high:lastSwingHigh,support:support?.price??null,resistance:resistance?.price??null,candle};
  const trend=sma50.at(-1)===null?'There are fewer than 50 bars for the medium-term average.':`The close is ${last.c>sma50.at(-1)?'above':last.c<sma50.at(-1)?'below':'at'} the 50-bar average (${chartFmt(sma50.at(-1))}).`;
  const shape=structureBreach==='bullish_failed'?`The last confirmed swings formed higher highs and higher lows, but the latest close is below their most recent swing low (${chartFmt(lastSwingLow)}).`:structureBreach==='bearish_failed'?`The last confirmed swings formed lower highs and lower lows, but the latest close is above their most recent swing high (${chartFmt(lastSwingHigh)}).`:structure==='higher_highs_higher_lows'?'Confirmed swings are making higher highs and higher lows.':structure==='lower_highs_lower_lows'?'Confirmed swings are making lower highs and lower lows.':structure==='mixed'?'The latest confirmed highs and lows show mixed structure.':'There are not yet two confirmed highs and two confirmed lows to compare.';
  const macdText=metrics.macd===null?'MACD needs 26 completed closes.':metrics.macd_signal===null?`MACD is ${chartFmt(metrics.macd)}; its signal and histogram need 34 completed closes.`:`MACD is ${chartFmt(metrics.macd)}, its signal is ${chartFmt(metrics.macd_signal)}, and its histogram is ${chartFmt(metrics.macd_histogram)}.`;
  const histogramText=({positive_weakening:'MACD is above its signal line, but the positive histogram is shrinking; upward momentum is fading, not a price-pivot divergence.',positive_building:'MACD is above its signal line and the positive histogram is growing; upward momentum is building, not a price-pivot divergence.',positive_holding:'MACD is above its signal line; positive momentum is holding steady, not a price-pivot divergence.',positive_crossing:'The histogram crossed above zero; MACD moved above its signal line, not a price-pivot divergence.',negative_easing:'MACD is below its signal line, but the histogram is moving toward zero; downward momentum is easing, not a price-pivot divergence.',negative_strengthening:'MACD is below its signal line and the histogram is falling; downward momentum is strengthening, not a price-pivot divergence.',negative_holding:'MACD is below its signal line; negative momentum is holding steady, not a price-pivot divergence.',negative_crossing:'The histogram crossed below zero; MACD moved below its signal line, not a price-pivot divergence.',neutral:'MACD is at its signal line; histogram momentum is neutral, not a price-pivot divergence.'})[momentum.histogram.state]||'';
  const sections=[{title:'Trend and structure',text:trend+' '+shape,tone:structureBreach?'caution':structure==='higher_highs_higher_lows'?'positive':structure==='lower_highs_lower_lows'?'negative':'neutral'},
    {title:'Nearby levels',text:[support?`Nearest confirmed support is ${chartFmt(support.price)}.`:'No confirmed support below this close is present in the available bars.',resistance?`Nearest confirmed resistance is ${chartFmt(resistance.price)}.`:'No confirmed resistance above this close is present in the available bars.'].join(' '),tone:'neutral'},
    {title:'Momentum and participation',text:[metrics.rsi14===null?'RSI needs 14 completed price changes.':`Wilder RSI is ${chartFmt(metrics.rsi14)} on its 0–100 scale.`,macdText,histogramText,rvol===null?'A complete prior 20-bar volume comparison is unavailable.':`Volume is ${rvol.toFixed(2)}× the preceding 20-bar average.`].join(' '),tone:'neutral'}];
  if(patterns.length)sections.push({title:'Measured pattern',text:patterns.map(p=>p.description).join(' '),tone:'neutral'});
  if(lines.length)sections.push({title:'Trendline tests',text:lines.map(l=>l.state==='untested'?`The line through the last two confirmed ${l.kind==='support'?'lows':'highs'} needs 14 completed bars before its volatility-based test is available.`:`The line through the last two confirmed ${l.kind==='support'?'lows':'highs'} is ${l.state==='broken'?'broken by a completed close':'intact on completed closes'} after its two-bar confirmation.`).join(' '),tone:lines.some(l=>l.state==='broken')?'caution':'neutral'});
  if(divergences.length) {
    const combined=chartDivergenceNarrative(divergences,momentum);
    const describe=d=>{
      const hidden=d.divergence_type==='hidden',bullish=d.kind==='bullish',priceMove=hidden?(bullish?'higher confirmed low':'lower confirmed high'):(bullish?'lower confirmed low':'higher confirmed high'),oscillatorMove=hidden?(bullish?'lower low':'higher high'):(bullish?'higher low':'lower high');
      const geometry=`${hidden?'Hidden':'Regular'} ${d.kind} divergence (${hidden?'continuation':'reversal'} context): price made a ${priceMove} while ${chartDivergenceGaugeNames[d.indicator]||d.indicator} made a ${oscillatorMove} at those same price pivots.`;
      if(!hidden)return geometry;
      const context=d.continuation_alignment==='aligned'?`Confirmed ${bullish?'higher highs and higher lows':'lower highs and lower lows'} at that time align with the continuation context.`:d.continuation_alignment==='mixed'?'Confirmed structure at that time was mixed, so aligned continuation is not established.':d.continuation_alignment==='opposed'?'Confirmed structure at that time opposed the continuation direction.':'Available confirmed swings at that time did not establish a prevailing trend.';
      const validity=d.current_status==='invalidated'?` A later completed close ${bullish?'below':'above'} the second pivot (${chartFmt(d.invalidation_level)}) invalidated this continuation read.`:'';
      return geometry+' '+context+validity;
    };
    sections.push({title:'Price and indicator divergences',text:combined+' '+divergences.map(describe).join(' '),tone:'neutral'});
  }
  sections.push({title:'Latest completed bar',text:candle.engulfing?`The ${candle.engulfing} candle body engulfs the prior opposite-direction body.`:range===0?'The last bar has no high-to-low range.':`The close sits ${chartFmt(candle.close_location*100)}% up its range, with a ${chartFmt(candle.lower_wick_fraction*100)}% lower wick and ${chartFmt(candle.upper_wick_fraction*100)}% upper wick.`,tone:'neutral'});
  const elliott=typeof analyzeElliottWave==='function'?analyzeElliottWave(series,now,{atr}):{method:'elliott-structure-1',status:'unavailable',reason:'engine_not_loaded',preferred:null,alternate:null,counts:[]};
  return {...base,status:n>=20?'ready':'limited',as_of:end===null?(series.as_of??null):new Date(end).toISOString(),observed_at:series.observed_at,received_at:series.received_at??null,source:series.source??null,adjustment:series.adjustment??null,input_sha256:series.sha256??null,interval:series.interval??null,summary:trend+' '+shape,sections,metrics,levels,lines,indicators:{sma10,sma20,sma50,sma200,rsi14:rsi,macd:macd.macd,macd_signal:macd.signal,macd_histogram:macd.histogram,...divergenceIndicators},extended,extended_status:'available',momentum,patterns,pattern_scan:patternScan,divergences,divergence_scan:{gauges_checked:gaugesChecked.size,gauges_available:gaugesAvailable,comparisons:divergenceComparisons,eligible_pivot_pairs:eligiblePivotPairs,gauge_availability:gaugeAvailability,gauge_names:gaugeSeries.map(([name])=>name)},pivots:pivots.slice(-16),elliott};
}


// Original: worker/setup-factor-checks.js
/*
 * Per-setup factor inventory. Every user-requested factor gets an explicit
 * disposition. Only measured, time-valid observations are eligible to become
 * material findings; absent feeds and unsupported detectors never become a
 * neutral or bullish vote.
 */
const SETUP_FACTOR_GROUPS = [
  ['Chart patterns', [
    ['head_shoulders','Head and shoulders'],['inverse_head_shoulders','Inverse head and shoulders'],
    ['double_top','Double top'],['double_bottom','Double bottom'],['triple_top','Triple top'],
    ['ascending_triangle','Ascending triangle'],['descending_triangle','Descending triangle'],['symmetrical_triangle','Symmetrical triangle'],
    ['rising_wedge','Rising wedge'],['falling_wedge','Falling wedge'],['expanding_wedge','Expanding wedge'],
    ['bull_flag','Bull flag'],['bear_flag','Bear flag'],['bull_pennant','Bull pennant'],['bear_pennant','Bear pennant'],
    ['cup_handle','Cup and handle'],['inverted_cup_handle','Inverted cup and handle'],['rectangle','Rectangle'],
    ['rising_channel','Rising channel'],['falling_channel','Falling channel'],['breakout_quality','Breakout / breakdown quality']
  ]],
  ['Price structure', [
    ['confirmed_swings','Dated confirmed swing highs and lows'],['support_resistance_trendlines','Support and resistance trendlines'],
    ['support_resistance_zones','Swing, volume-profile and round-number zones'],['level_confluence','Stacked levels at similar prices'],
    ['average_retests','20- and 50-day retests / reclaims'],['breakout_retest','Breakout-level retests'],['structure_integrity','Structure intact / broken and warnings']
  ]],
  ['Measured levels and targets', [
    ['one_year_fibonacci','One-year retracement, band and 200-day confluence'],['measured_targets','Pattern, AB=CD and 1.272 / 1.618 targets'],['fifty_two_week_range','52-week high and low']
  ]],
  ['Trend and averages', [
    ['sma10','10-day average and price position'],['sma20','20-day average and price position'],['sma50','50-day average and price position'],['sma200','200-day average and price position'],
    ['weinstein_stage','Weinstein stage'],['chartslector_stage','ChartsLector stage'],['elliott_wave','Elliott wave count and invalidation'],['higher_timeframe_map','Monthly / weekly trend map']
  ]],
  ['Momentum', [
    ['rsi','RSI'],['macd_line','MACD line'],['macd_signal','MACD signal'],['macd_histogram','MACD histogram'],['macd_crossovers','MACD crossovers'],
    ['slow_stochastic','Slow stochastic'],['six_month_momentum','Six-month momentum'],['momentum_rank','Momentum rank versus peers'],
    ['relative_strength_spy','Relative strength versus S&P 500'],['relative_strength_sector','Relative strength versus sector'],['adx_dmi','ADX / DMI trend strength']
  ]],
  ['Volume', [
    ['relative_volume','Relative volume'],['breakout_volume','Breakout participation'],['obv','On-balance volume'],['accumulation_distribution','Accumulation / distribution'],['mfi','Money flow index'],
    ['vwap20','20-day typical-price VWAP'],['value_area_high','Volume-profile value-area high'],['value_area_low','Volume-profile value-area low'],['volume_poc','Volume-profile point of control'],
    ['anchored_vwap_earnings','Earnings-anchored VWAP'],['anchored_vwap_swing','Major-swing anchored VWAP']
  ]],
  ['Divergences', [['daily_divergences','Daily divergence scan · seven momentum / volume gauges'],['weekly_divergences','Weekly divergence scan · seven momentum / volume gauges']]],
  ['Stretch and volatility', [['atr_stretch','ATR and average true range'],['extension_rank','ATR extension ranked against the year'],['bollinger_squeeze','Bollinger width percentile and squeeze']]],
  ['Candles and gaps', [['candlestick_detectors','Candle range, wick and engulfing pattern at key levels · requested 50-pattern family'],['gap_direction','Gap up / gap down'],['gap_taxonomy','Breakaway / runaway / exhaustion / common gap'],['unfilled_gaps','Unfilled gaps carried as price levels']]],
  ['Wyckoff', [['wyckoff_phase','Accumulation / distribution phase'],['wyckoff_events','Springs and upthrusts'],['effort_result','Volume effort versus price result']]],
  ['Tensor', [['tensor_slow','Slow Tensor state and markers'],['tensor_fast','Fast Tensor state and markers'],['tensor_votes','Tensor component votes'],['tensor_strength','Tensor trend strength'],['tensor_timeframes','Weekly / daily / hourly Tensor alignment']]],
  ['Timing and trade plan', [['fear_day','Fear-day QQQ timing rule'],['buy_zone','Buy zone and cap'],['buy_window','Buy window and distance to cap'],['invalidation_cases','Invalidation, good case and bad case'],['sleeve_exit','Owning sleeve stops and exits']]],
  ['Options and positioning', [['name_options','Name-level implied volatility and positioning'],['iv_rank','IV rank'],['iv_realized','Implied versus realized volatility'],['dealer_gamma_name','Name-level dealer gamma'],['market_options','Market put / call and dealer gamma'],['short_interest','Short interest and days to cover'],['short_activity','Short volume and fails to deliver'],['insider_activity','Insider buys']]],
  ['Desk book', [['current_exposure','Existing name and sector exposure'],['owning_sleeves','Sleeves already holding the name'],['prior_history','Prior desk trade history in the name']]],
  ['Liquidity', [['market_cap_float','Market capitalization and float'],['dollar_volume','Average dollar volume'],['spread','Bid / ask quote snapshot']]],
  ['Company and market context', [
    ['industry_peers','Industry peers · 21 sessions'],['sec_filings','SEC 8-K filings'],['quarterly_fundamentals','Quarterly fundamentals'],['news_counts','Ticker news count · Alpaca 24-hour feed'],
    ['earnings_calendar','Earnings dates and past reactions'],['corporate_events','Splits, dividends, index changes and lockups'],['analyst_revisions','Analyst revisions'],
    ['market_regime','Market regime'],['vix','VIX'],['breadth','Market breadth'],['rates','Rates'],['credit','Credit'],['dollar','U.S. dollar'],
    ['economic_calendar','Economic calendar'],['geopolitical_news','Geopolitical news'],['attention','Wikipedia / Reddit attention'],['seasonality','Seasonality']
  ]],
  // Append new checks so persisted numeric factor IDs from earlier reads keep
  // their meaning. Unsupported is an explicit disposition, never a negative vote.
  ['Additional chart patterns', [
    ['climax_top','Climax top'],['climax_run','Climax run'],['selling_climax','Selling climax'],['flat_base','Flat base · depth, duration and pivot'],
    ['right_angled_broadening_top','Right-angled broadening top'],['right_angled_broadening_bottom','Right-angled broadening bottom'],
    ['v_top','V-top'],['v_bottom','V-bottom'],['dead_cat_bounce','Dead-cat bounce'],['three_weeks_tight','Three-weeks-tight'],['pivot_tightness','Pivot tightness'],
    ['ascending_base','Ascending base'],['base_on_base','Base-on-base'],['ipo_base','IPO base'],['power_earnings_gap','Power Earnings Gap'],['vcp','Volatility Contraction Pattern'],
    ['high_tight_flag','High tight flag'],['diamond_top','Diamond top'],['diamond_bottom','Diamond bottom'],['island_reversal','Island reversal'],
    ['rounding_bottom','Rounding bottom / saucer base'],['bump_run_reversal','Bump-and-run reversal'],['bull_trap','Bull trap / failed upside break'],['bear_trap','Bear trap / failed downside break'],
    ['base_depth','Base depth'],['base_length','Base length'],['base_stage','Base stage count'],['volume_dry_up','Volume dry-up in base'],
    ['tower_tops','Tower tops'],['three_peaks_domed_house','Three peaks and domed house'],['horn_pattern','Horn reversal pattern'],['pipe_pattern','Pipe top / bottom'],['scallop_pattern','Scallop pattern']
  ]],
  ['Additional chart levels and overlays', [
    ['ichimoku_tenkan','Ichimoku tenkan'],['ichimoku_kijun','Ichimoku kijun'],['ichimoku_cloud','Ichimoku cloud'],['ichimoku_chikou','Ichimoku chikou'],
    ['floor_pivots','Floor pivot points'],['prior_day_week_month_levels','Prior day / week / month highs and lows'],['parabolic_sar','Parabolic SAR'],['supertrend','Supertrend'],
    ['keltner_channels','Keltner channels'],['donchian_20','Donchian 20-bar bands'],['donchian_55','Donchian 55-bar bands'],['chandelier_exit','Chandelier exit'],
    ['vwap_stdev_bands','VWAP and anchored-VWAP deviation bands'],['ma_ribbon_gmma','Moving-average ribbon / GMMA'],['all_time_high_low','All-time high / low and distance'],
    ['anchored_vwap_ipo','IPO-anchored VWAP'],['anchored_vwap_gap','Major-gap-anchored VWAP'],['andrews_pitchfork','Andrews pitchfork'],['golden_death_cross','Golden / death cross event'],['ytd_anchored_vwap','Year-to-date anchored VWAP']
  ]],
  ['Additional momentum gauges', [
    ['cci','Commodity Channel Index'],['williams_r','Williams %R'],['stoch_rsi','Stochastic RSI'],['roc_horizons','Rate of change across horizons'],
    ['aroon','Aroon'],['vortex','Vortex indicator'],['trix','TRIX'],['coppock','Coppock curve'],['historical_volatility_percentile','Historical-volatility percentile'],['elder_ray','Elder-Ray'],['mass_index','Mass Index']
  ]],
  ['Additional volume gauges', [
    ['chaikin_money_flow','Chaikin Money Flow'],['chaikin_oscillator','Chaikin oscillator'],['elder_force_index','Elder Force Index'],['ease_of_movement','Ease of Movement'],
    ['klinger','Klinger oscillator'],['vwma','Volume-weighted moving average'],['up_down_volume','Up / down volume ratio'],['nvi','Negative Volume Index'],['pvi','Positive Volume Index'],['pvt','Price Volume Trend'],['market_profile_tpo','Market-profile TPO shape']
  ]],
  ['Relative-strength chart', [['rs_line_leadership','Relative-strength line and new-high leadership']]],
  ['Options-derived levels', [
    ['options_expected_move','Options-implied expected move'],['call_wall','Call-wall strike'],['put_wall','Put-wall strike'],['gamma_flip_level','Gamma-flip / zero-gamma level'],
    ['iv_skew','Implied-volatility skew'],['iv_term_structure','Implied-volatility term structure'],['oi_strike_concentration','Open-interest strike concentration'],['options_max_pain','Max-pain level']
  ]],
  ['Modern price structure', [['fair_value_gaps','Fair-value gaps / imbalances'],['liquidity_sweeps','Liquidity pools and sweeps'],['order_blocks','Order blocks']]],
  ['Ownership and short positioning', [
    ['beta_market_correlation','Market beta and correlation'],['institutional_ownership','Institutional ownership and sponsorship trend'],
    ['short_interest_trend','Short-interest trend'],['borrow_fee_utilization','Borrow fee and utilization'],['industry_group_strength_6m','Industry-group strength · six months'],['unusual_options_flow','Unusual options flow']
  ]],
  ['Market internals and calendar', [
    ['distribution_day_count','Distribution-day count'],['follow_through_day','Follow-through day'],['mcclellan_oscillator','McClellan oscillator'],
    ['buyback_announcements','Buyback announcements'],['monthly_options_expiry','Monthly options-expiry week'],['zweig_thrust','Zweig breadth thrust'],['trin_index','TRIN Arms Index'],['aaii_sentiment','AAII investor sentiment survey'],['naaim_exposure','NAAIM manager exposure index']
  ]],
  ['Additional low-priority gauges', [['td_sequential','TD Sequential counts'],['heikin_ashi','Heikin-Ashi view'],['nr4_compression','NR4 compression'],['nr7_compression','NR7 compression']]],
  ['Additional market data', [['market_volatility_structure','Cboe VIX term structure, VVIX and SKEW index']]]
];
const SETUP_FACTOR_CATALOG = SETUP_FACTOR_GROUPS.flatMap(([category,items]) => items.map(([id,label])=>({id,label,category})));
const SETUP_FACTOR_STATUS = new Set(['measured','partial','stale','insufficient_history','insufficient_validation','not_scanned','not_supplied','not_applicable']);
const SETUP_FACTOR_NO_VALIDATED_SCREEN = new Set(['three_peaks_domed_house']);
const SETUP_FACTOR_DATE_FORMATTERS=new Map();
function setupFactorDateFormatter(locale,options){const key=locale+'|'+JSON.stringify(options);let formatter=SETUP_FACTOR_DATE_FORMATTERS.get(key);if(!formatter){formatter=new Intl.DateTimeFormat(locale,options);if(SETUP_FACTOR_DATE_FORMATTERS.size>=12)SETUP_FACTOR_DATE_FORMATTERS.clear();SETUP_FACTOR_DATE_FORMATTERS.set(key,formatter);}return formatter;}
function setupFactorFinite(x){return typeof x==='number'&&Number.isFinite(x);}
function setupFactorFmt(x,d=2){return setupFactorFinite(x)?chartFormatNumber(x,{maximumFractionDigits:d}):'unavailable';}
function setupFactorIntervalWords(interval){return ({'1d':{unit:'day',label:'daily'},'1wk':{unit:'week',label:'weekly'},'1w':{unit:'week',label:'weekly'},'1mo':{unit:'month',label:'monthly'},'1h':{unit:'hour',label:'hourly'},'4h':{unit:'four-hour',label:'four-hour'},'30m':{unit:'30-minute',label:'30-minute'},'15m':{unit:'15-minute',label:'15-minute'},'10m':{unit:'10-minute',label:'10-minute'}})[interval]||{unit:'bar',label:'chart'};}
function setupFactorSessionKey(value){
 const raw=String(value??''),dateOnly=raw.match(/^(\d{4}-\d{2}-\d{2})(?:$|T00:00(?::00(?:\.000)?(?:Z|\+00:00)?$))/);if(dateOnly)return dateOnly[1];
 const time=Date.parse(raw);if(!Number.isFinite(time))return null;
 try{return setupFactorDateFormatter('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(time));}catch{return null;}
}
function setupFactorCurrentDaily(day,now,market=null){
 if(typeof setupCurrentDaily==='function')return setupCurrentDaily(day,now,market);
 if(!/^\d{4}-\d{2}-\d{2}$/.test(day||''))return false;
 const source=new Date(day+'T12:00:00Z'),today=setupFactorSessionKey(typeof now==='number'?new Date(now).toISOString():now);
 if(!Number.isFinite(source.getTime())||source.toISOString().slice(0,10)!==day||!today||day>today||[0,6].includes(source.getUTCDay()))return false;
 if(day===today)return true;
 if(market?.calendar_verified===true){const receipt=Date.parse(market.at||''),open=Date.parse(market.open||''),close=Date.parse(market.close||''),previous=Date.parse(market.previous_session_close||'');if([receipt,open,close,previous].every(Number.isFinite)&&receipt<=now&&now-receipt<=300000&&previous<=now&&previous<open&&open<close&&setupFactorSessionKey(open)>=today&&setupFactorSessionKey(open)===setupFactorSessionKey(close)&&day===setupFactorSessionKey(previous))return true;}
 const cursor=new Date(today+'T12:00:00Z');do{cursor.setUTCDate(cursor.getUTCDate()-1);}while([0,6].includes(cursor.getUTCDay()));
 return day===cursor.toISOString().slice(0,10);
}
function setupFactorUsSessionOpen(value){
 const session=setupFactorSessionKey(value);if(!session)return null;
 try{const dateFmt=setupFactorDateFormatter('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}),timeFmt=setupFactorDateFormatter('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});for(const hour of [13,14]){const candidate=Date.parse(`${session}T${String(hour).padStart(2,'0')}:30:00Z`);if(dateFmt.format(new Date(candidate))===session&&timeFmt.format(new Date(candidate))==='09:30')return candidate;}}catch{}
 return null;
}
function setupFactorMonthExpiry(year,month){
 const first=new Date(Date.UTC(year,month,1)),firstFriday=1+((5-first.getUTCDay()+7)%7),friday=new Date(Date.UTC(year,month,firstFriday+14));
 const date=friday.toISOString().slice(0,10),easterYear=year,a=Math.floor(easterYear%19),b=Math.floor(easterYear/100),c=easterYear%100,d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,m=Math.floor((a+11*h+22*l)/451),easterMonth=Math.floor((h+l-7*m+114)/31)-1,easterDay=(h+l-7*m+114)%31+1,easter=new Date(Date.UTC(year,easterMonth,easterDay)),goodFriday=new Date(easter.getTime()-2*86400000).toISOString().slice(0,10),juneteenthObserved=new Date(Date.UTC(year,5,19)),juneteenthDay=juneteenthObserved.getUTCDay()===6?18:juneteenthObserved.getUTCDay()===0?20:19,juneteenth=year>=2022?new Date(Date.UTC(year,5,juneteenthDay)).toISOString().slice(0,10):null;
 if(date===goodFriday||date===juneteenth){friday.setUTCDate(friday.getUTCDate()-1);}
 return {date:friday.toISOString().slice(0,10),standard_friday:date,holiday_adjusted:date===goodFriday||date===juneteenth};
}
function setupFactorMonthlyOptionsExpiry(value){
 const session=setupFactorSessionKey(value);if(!session)return null;
 const [year,month]=session.split('-').map(Number),current=setupFactorMonthExpiry(year,month-1),expirationDay=Date.parse(current.date+'T00:00:00Z'),sessionDay=Date.parse(session+'T00:00:00Z'),weekStart=Date.parse(current.date+'T00:00:00Z')-((new Date(expirationDay).getUTCDay()+6)%7)*86400000;
 const inExpiryWeek=sessionDay>=weekStart&&sessionDay<=expirationDay;
 let next=current;if(sessionDay>expirationDay){const nextMonth=new Date(Date.UTC(year,month,1));next=setupFactorMonthExpiry(nextMonth.getUTCFullYear(),nextMonth.getUTCMonth());}
 return {as_of:session,expiration_date:current.date,standard_friday:current.standard_friday,holiday_adjusted:current.holiday_adjusted,in_expiry_week:inExpiryWeek,week_start:new Date(weekStart).toISOString().slice(0,10),next_expiration_date:next.date};
}
function setupFactorTreasuryCurve(curve,asOf,lookbackDays=30,maxAgeDays=7){
 if(curve?.source!=='US Treasury'||curve?.series_id!=='daily_treasury_yield_curve'||!Array.isArray(curve.observations))return null;
 const session=setupFactorSessionKey(asOf);if(!session)return null;const target=Date.parse(session+'T00:00:00Z'),observations=[],seen=new Set(),keys=['one_month','two_month','three_month','four_month','six_month','one_year','two_year','three_year','five_year','seven_year','ten_year','twenty_year','thirty_year'];
 for(const point of curve.observations){const date=setupFactorSessionKey(point?.date),clock=date?Date.parse(date+'T00:00:00Z'):NaN,values=Object.fromEntries(keys.filter(key=>setupFactorFinite(point?.[key])).map(key=>[key,point[key]]));if(!date||seen.has(date)||clock>target||!['two_year','ten_year','thirty_year'].every(key=>setupFactorFinite(values[key])))continue;seen.add(date);observations.push({date,clock,...values});}
 observations.sort((a,b)=>a.clock-b.clock);if(!observations.length)return null;
 const latest=observations.at(-1),ageDays=Math.floor((target-latest.clock)/86400000),cutoff=target-lookbackDays*86400000,prior=[...observations].reverse().find(x=>x.clock<=cutoff);
 if(ageDays>maxAgeDays)return {status:'stale',source:'US Treasury',series_id:curve.series_id,as_of:latest.date,age_days:ageDays,latest,observations:observations.length};
 if(!prior)return {status:'insufficient_history',source:'US Treasury',series_id:curve.series_id,as_of:latest.date,age_days:ageDays,latest,observations:observations.length};
 const changes=Object.fromEntries(keys.filter(key=>setupFactorFinite(latest[key])&&setupFactorFinite(prior[key])).map(key=>[key,latest[key]-prior[key]]));changes.ten_minus_two=(latest.ten_year-latest.two_year)-(prior.ten_year-prior.two_year);return {status:'measured',source:'US Treasury',series_id:curve.series_id,as_of:latest.date,age_days:ageDays,latest,prior,changes,lookback_days:lookbackDays,observations:observations.length};
}
function setupFactorRealTreasuryCurve(curve,asOf,lookbackDays=30,maxAgeDays=7){
 if(curve?.real_source!=='US Treasury'||curve?.real_series_id!=='daily_treasury_real_yield_curve'||!Array.isArray(curve.real_observations))return null;
 const session=setupFactorSessionKey(asOf);if(!session)return null;const target=Date.parse(session+'T00:00:00Z'),observations=[],seen=new Set(),keys=['five_year','seven_year','ten_year','twenty_year','thirty_year'];
 for(const point of curve.real_observations){const date=setupFactorSessionKey(point?.date),clock=date?Date.parse(date+'T00:00:00Z'):NaN,values=Object.fromEntries(keys.filter(key=>setupFactorFinite(point?.[key])).map(key=>[key,point[key]]));if(!date||seen.has(date)||clock>target||!['five_year','ten_year','thirty_year'].every(key=>setupFactorFinite(values[key])))continue;seen.add(date);observations.push({date,clock,...values});}
 observations.sort((a,b)=>a.clock-b.clock);if(!observations.length)return null;
 const latest=observations.at(-1),ageDays=Math.floor((target-latest.clock)/86400000),cutoff=target-lookbackDays*86400000,prior=[...observations].reverse().find(x=>x.clock<=cutoff);
 if(ageDays>maxAgeDays)return {status:'stale',source:'US Treasury',series_id:curve.real_series_id,as_of:latest.date,age_days:ageDays,latest,observations:observations.length};
 if(!prior)return {status:'insufficient_history',source:'US Treasury',series_id:curve.real_series_id,as_of:latest.date,age_days:ageDays,latest,observations:observations.length};
 const changes=Object.fromEntries(keys.filter(key=>setupFactorFinite(latest[key])&&setupFactorFinite(prior[key])).map(key=>[key,latest[key]-prior[key]]));return {status:'measured',source:'US Treasury',series_id:curve.real_series_id,as_of:latest.date,age_days:ageDays,latest,prior,changes,lookback_days:lookbackDays,observations:observations.length};
}
function setupFactorDollarIndex(macro,asOf,lookbackSessions=5,maxAgeDays=10){
 const series=macro?.dollar_index;if(series?.source!=='Federal Reserve Board'||series?.series_id!=='H10/H10/JRXWTFB_N.B'||!Array.isArray(series.observations))return null;
 const session=setupFactorSessionKey(asOf);if(!session)return null;const target=Date.parse(session+'T00:00:00Z'),observations=[],seen=new Set();
 for(const point of series.observations){const date=setupFactorSessionKey(point?.date),clock=date?Date.parse(date+'T00:00:00Z'):NaN,broad=point?.broad;if(!date||seen.has(date)||clock>target||!setupFactorFinite(broad)||broad<=0)continue;seen.add(date);observations.push({date,clock,broad,advanced:setupFactorFinite(point?.advanced)?point.advanced:null,emerging:setupFactorFinite(point?.emerging)?point.emerging:null});}
 observations.sort((a,b)=>a.clock-b.clock);if(!observations.length)return null;const latest=observations.at(-1),ageDays=Math.floor((target-latest.clock)/86400000);if(ageDays>maxAgeDays)return {status:'stale',source:series.source,series_id:series.series_id,as_of:latest.date,age_days:ageDays,latest,observations:observations.length};
 const prior=observations.at(-1-lookbackSessions);if(!prior)return {status:'insufficient_history',source:series.source,series_id:series.series_id,as_of:latest.date,age_days:ageDays,latest,observations:observations.length,lookback_sessions:lookbackSessions};
 const change=(current,base)=>setupFactorFinite(current)&&setupFactorFinite(base)&&base!==0?(current/base-1)*100:null;return {status:'measured',source:series.source,series_id:series.series_id,as_of:latest.date,age_days:ageDays,latest,prior,change_pct:change(latest.broad,prior.broad),advanced_change_pct:change(latest.advanced,prior.advanced),emerging_change_pct:change(latest.emerging,prior.emerging),lookback_sessions:lookbackSessions,observations:observations.length};
}
function setupFactorPriceBasis(chart){
 const adjustment=typeof chart?.adjustment==='string'?chart.adjustment.trim().toLowerCase().replace(/\s+/g,' '):'';
 if(chart?.source==='Yahoo Finance historical bars'&&['yahoo quote ohlc as supplied; no desk adjustments','yahoo adjusted_close as supplied; vendor ohlc retained without desk adjustments'].includes(adjustment))return 'yahoo-unmodified-quote-ohlcv';
 return chart?.source&&chart?.adjustment?`${chart.source}\u0000${chart.adjustment}`:null;
}
function setupFactorSamePriceBasis(a,b){
 const left=setupFactorPriceBasis(a),right=setupFactorPriceBasis(b);return !!left&&!!right&&a?.source===b?.source&&left===right;
}
function setupFactorLifetimeReferenceBasis(primary,history){
 if(setupFactorSamePriceBasis(primary,history))return {mode:'same_source',primary_source:primary?.source||null,history_source:history?.source||null};
 // Keep full-history calculations on one vendor's bars; Yahoo is reference context only for Alpaca charts, never merged into the execution series.
 const alpacaSources=new Set(['Alpaca SIP daily bars from the Lector refresh','Alpaca SIP daily bars from shared market cache']);
 if(!alpacaSources.has(primary?.source)||primary?.adjustment!=='split'||setupFactorPriceBasis(history)!=='yahoo-unmodified-quote-ohlcv')return null;
 const primarySession=setupFactorSessionKey(primary?.as_of||primary?.last_completed_at||primary?.bars?.at(-1)?.[0]),historySession=setupFactorSessionKey(history?.as_of||history?.last_completed_at||history?.bars?.at(-1)?.[0]);
 if(!primarySession||primarySession!==historySession||!Array.isArray(primary?.bars)||!Array.isArray(history?.bars))return null;
 const reference=new Map(history.bars.map(bar=>[setupFactorSessionKey(bar?.[0]),bar])),observed=new Set(),sample=primary.bars.slice(-252);let matched=0,maxPrice=0,maxVolume=0;
 for(const bar of sample){
  const session=setupFactorSessionKey(bar?.[0]),other=reference.get(session);if(!session||observed.has(session)||!other)continue;observed.add(session);
  if(![1,2,3,4,5].every(i=>setupFactorFinite(bar?.[i])&&setupFactorFinite(other?.[i])&&bar[i]>0&&other[i]>0))return null;
  for(let i=1;i<=4;i++)maxPrice=Math.max(maxPrice,Math.abs(bar[i]-other[i])/other[i]);
  maxVolume=Math.max(maxVolume,Math.abs(bar[5]-other[5])/other[5]);matched++;
 }
 if(matched<120||matched/sample.length<.95||maxPrice>.005||maxVolume>.05)return null;
 return {mode:'cross_source_verified',primary_source:primary.source,history_source:history.source,primary_adjustment:primary.adjustment,history_price_basis:'Yahoo unadjusted quote OHLC',overlap_sessions:matched,overlap_from:[...observed].sort()[0],overlap_through:[...observed].sort().at(-1),max_price_difference_pct:maxPrice*100,max_volume_difference_pct:maxVolume*100};
}
function setupFactorLifetimeHistory(value,primary,now=Date.now(),expectedSymbol=primary?.symbol){
 const chart=value?.chart||value;if(!value||!chart||value.symbol!==expectedSymbol||value.source!=='Yahoo Finance historical bars'||!Array.isArray(value.bars)||value.bars.length<20||value.bars.length>6000)return null;
 const received=Date.parse(value.received_at||''),primarySession=setupFactorSessionKey(primary?.as_of||primary?.last_completed_at||primary?.bars?.at(-1)?.[0]),historySession=setupFactorSessionKey(value.as_of||value.last_completed_at||value.bars.at(-1)?.[0]);
 if(!Number.isFinite(received)||received>now||now-received>300000||!primarySession||historySession!==primarySession||value.input_status?.current===false||value.input_status?.missing_completed_periods>0)return null;
 let prior=null;for(const bar of value.bars){const date=setupFactorSessionKey(bar?.[0]);if(!date||prior&&date<=prior||![1,2,3,4].every(i=>setupFactorFinite(bar?.[i])&&bar[i]>0)||bar[2]<Math.max(bar[1],bar[4])||bar[3]>Math.min(bar[1],bar[4])||bar[5]!=null&&(!setupFactorFinite(bar[5])||bar[5]<0))return null;prior=date;}
 const basisValidation=setupFactorLifetimeReferenceBasis(primary,{...value,...chart,bars:value.bars});if(!basisValidation)return null;
 const firstBar=setupFactorSessionKey(value.bars[0][0]),listing=setupFactorSessionKey(value.first_trade_date),firstListing=listing?Date.parse(listing+'T00:00:00Z'):NaN,firstAvailable=firstBar?Date.parse(firstBar+'T00:00:00Z'):NaN;
 if(firstBar!==value.first_bar_date||value.available_from&&setupFactorSessionKey(value.available_from)!==firstBar||setupFactorSessionKey(value.bars.at(-1)[0])!==historySession)return null;
 return {...value,complete_from_listing:value.complete_from_listing===true&&Number.isFinite(firstListing)&&Number.isFinite(firstAvailable)&&firstAvailable<=firstListing+10*86400000,basis_validation:basisValidation};
}
function setupFactorIpoAnchoredVwap(history){
 if(!history?.complete_from_listing||!Array.isArray(history.bars)||history.bars.some(b=>!setupFactorFinite(b[5])||b[5]<0))return null;
 const volume=history.bars.reduce((sum,b)=>sum+b[5],0);if(!(volume>0))return null;
 const value=history.bars.reduce((sum,b)=>sum+((b[2]+b[3]+b[4])/3)*b[5],0)/volume;
 return setupFactorFinite(value)?{value,volume,bars:history.bars.length,anchor_at:history.first_trade_date,available_from:history.available_from,source:history.source}:null;
}
function setupFactorSeasonality(bars,asOf){
 if(!Array.isArray(bars)||bars.length<756)return null;
 const asOfSession=setupFactorSessionKey(asOf);if(!asOfSession)return null;const currentMonth=asOfSession.slice(0,7),monthly=new Map();
 for(const bar of bars){const session=setupFactorSessionKey(bar?.[0]),close=bar?.[4];if(!session||session.slice(0,7)>=currentMonth||!setupFactorFinite(close)||close<=0)continue;monthly.set(session.slice(0,7),{month:session.slice(0,7),close});}
 const closes=[...monthly.values()].sort((a,b)=>a.month.localeCompare(b.month)),groups=Array.from({length:12},()=>[]);
 for(let i=1;i<closes.length;i++){const prior=closes[i-1],current=closes[i],priorDate=new Date(prior.month+'-01T00:00:00Z'),expected=new Date(Date.UTC(priorDate.getUTCFullYear(),priorDate.getUTCMonth()+1,1)).toISOString().slice(0,7);if(current.month!==expected||!(prior.close>0))continue;groups[Number(current.month.slice(5,7))-1].push(current.close/prior.close-1);}
 const median=xs=>{const sorted=[...xs].sort((a,b)=>a-b);return sorted.length?sorted.length%2?sorted[(sorted.length-1)/2]:(sorted[sorted.length/2-1]+sorted[sorted.length/2])/2:null;},months=groups.map((returns,index)=>({month:index+1,samples:returns.length,mean:returns.length?setupFactorMean(returns):null,median:median(returns),positive_rate:returns.length?returns.filter(x=>x>0).length/returns.length:null})),minimum=Math.min(...months.map(x=>x.samples)),observations=months.reduce((sum,x)=>sum+x.samples,0);
 if(observations<36||minimum<3)return {status:'insufficient_history',months,observations,minimum_samples:minimum,completed_months:closes.length,as_of:asOfSession,method:'monthly close-to-close returns; incomplete current month excluded'};
 return {status:minimum>=5?'measured':'partial',months,observations,minimum_samples:minimum,completed_months:closes.length,as_of:asOfSession,method:'monthly close-to-close returns; incomplete current month excluded'};
}
function setupFactorAlignedReturns(stockBars,benchmarkBars,period=126){
 if(!Array.isArray(stockBars)||!Array.isArray(benchmarkBars))return null;
 const index=rows=>{const map=new Map();for(const bar of Array.isArray(rows)?rows:[]){const key=setupFactorSessionKey(bar?.[0]),close=bar?.[4];if(!key||!setupFactorFinite(close)||close<=0||map.has(key))return null;map.set(key,close);}return map;};
 const stock=index(stockBars),benchmark=index(benchmarkBars);if(!stock||!benchmark)return null;
 const stockLatest=setupFactorSessionKey(stockBars?.at(-1)?.[0]),benchmarkLatest=setupFactorSessionKey(benchmarkBars?.at(-1)?.[0]);
 if(!stockLatest||stockLatest!==benchmarkLatest)return {stale:true,session:stockLatest,benchmark_session:benchmarkLatest};
 const common=[...stock.keys()].filter(key=>benchmark.has(key)).sort();if(common.length<=period)return null;
 const current=common.at(-1),base=common[common.length-1-period],stockBase=stock.get(base),benchmarkBase=benchmark.get(base);
 if(current!==stockLatest||stockBase<=0||benchmarkBase<=0)return null;
 const stock_return=stock.get(current)/stockBase-1,benchmark_return=benchmark.get(current)/benchmarkBase-1,excess=stock_return-benchmark_return;
 if(![stock_return,benchmark_return,excess].every(setupFactorFinite))return {invalid:true,session:current,matched_sessions:period+1};
 return {stale:false,session:current,stock_return,benchmark_return,excess,matched_sessions:period+1};
}
function setupFactorSectorBenchmarkSymbol(sector){
 const key=String(sector||'').trim().toLowerCase();
 return ({
  'basic materials':'XLB','communication services':'XLC','consumer cyclical':'XLY','consumer discretionary':'XLY',
  'consumer defensive':'XLP','consumer staples':'XLP','energy':'XLE','financial services':'XLF','financials':'XLF',
  'health care':'XLV','healthcare':'XLV','industrials':'XLI','real estate':'XLRE','technology':'XLK','utilities':'XLU'
 })[key]||null;
}
function setupFactorMarketBeta(stockBars,benchmarkBars,period=126){
 if(!Array.isArray(stockBars)||!Array.isArray(benchmarkBars)||!Number.isInteger(period)||period<2)return null;
 const index=rows=>{const map=new Map();for(const bar of rows){const key=setupFactorSessionKey(bar?.[0]),close=bar?.[4];if(!key||!setupFactorFinite(close)||close<=0||map.has(key))return null;map.set(key,close);}return map;};
 const stock=index(stockBars),benchmark=index(benchmarkBars);if(!stock||!benchmark)return null;
 const stockLatest=setupFactorSessionKey(stockBars.at(-1)?.[0]),benchmarkLatest=setupFactorSessionKey(benchmarkBars.at(-1)?.[0]);
 if(!stockLatest||stockLatest!==benchmarkLatest)return {stale:true,session:stockLatest,benchmark_session:benchmarkLatest};
 const common=[...stock.keys()].filter(key=>benchmark.has(key)).sort();if(common.length<=period)return null;
 const sessions=common.slice(-(period+1)),stockReturns=[],benchmarkReturns=[];
 for(let i=1;i<sessions.length;i++){const a=sessions[i-1],b=sessions[i],sr=stock.get(b)/stock.get(a)-1,br=benchmark.get(b)/benchmark.get(a)-1;if(!Number.isFinite(sr)||!Number.isFinite(br))return {invalid:true,matched_sessions:sessions.length};stockReturns.push(sr);benchmarkReturns.push(br);}
 const mean=xs=>xs.reduce((sum,x)=>sum+x,0)/xs.length,sm=mean(stockReturns),bm=mean(benchmarkReturns),cov=stockReturns.reduce((sum,x,i)=>sum+(x-sm)*(benchmarkReturns[i]-bm),0)/(period-1),sv=stockReturns.reduce((sum,x)=>sum+(x-sm)**2,0)/(period-1),bv=benchmarkReturns.reduce((sum,x)=>sum+(x-bm)**2,0)/(period-1);
 if(!(sv>0&&bv>0))return {invalid:true,matched_sessions:sessions.length};
 const beta=cov/bv,correlation=cov/Math.sqrt(sv*bv);if(!Number.isFinite(beta)||!Number.isFinite(correlation))return {invalid:true,matched_sessions:sessions.length};
 return {stale:false,beta,correlation,matched_sessions:sessions.length,return_intervals:period,session:sessions.at(-1),method:'126 matched daily simple returns; sample covariance / sample market variance'};
}
function setupFactorSourceCurrent(series,now){
 const maxAge=series?.interval==='1h'?3*86400000:series?.interval==='1d'?4*86400000:series?.interval==='1wk'?14*86400000:series?.interval==='1mo'?62*86400000:null;
 if(!maxAge)return false;
 const stamp=series.last_completed_at||series.as_of,time=Date.parse(stamp||'');
 return Number.isFinite(time)&&time<=now&&now-time<=maxAge;
}
function setupFactorSupplementCurrent(supplement,primary,now,expectedSymbol=primary?.symbol,expectedInterval='1d'){
 const chart=supplement?.chart||supplement;
 const minimumBars=expectedInterval==='1wk'?34:expectedInterval==='1mo'?6:expectedInterval==='1d'?127:expectedInterval==='1h'?35:Infinity,sourceMatches=expectedInterval==='1mo'?chart?.source==='Derived from Yahoo Finance historical daily bars'&&chart?.derived_from==='Yahoo Finance historical bars'&&chart?.derivation==='completed calendar-month OHLCV aggregation':chart?.source==='Yahoo Finance historical bars';
 if(!sourceMatches||chart?.interval!==expectedInterval||chart?.symbol!==expectedSymbol||!Array.isArray(chart.bars)||chart.bars.length<minimumBars||chart.input_status?.current===false||chart.input_status?.missing_completed_periods>0)return null;
 const sessions=chart.bars.map(bar=>setupFactorSessionKey(bar?.[0])),timestamps=chart.bars.map(bar=>Date.parse(bar?.[0]));
 // Intraday bars legitimately share a trading-session key. Validate their
 // actual timestamps for strict chronology instead of rejecting every hourly
 // frame after its second candle.
 if(sessions.some(session=>!session)||timestamps.some((stamp,index)=>!Number.isFinite(stamp)||index>0&&stamp<=timestamps[index-1])||chart.bars.some(bar=>![1,2,3,4].every(i=>setupFactorFinite(bar?.[i])&&bar[i]>0)||bar[2]<Math.max(bar[1],bar[4])||bar[3]>Math.min(bar[1],bar[4])))return null;
 const received=Date.parse(chart.received_at||''),last=chart.last_completed_at||chart.as_of||chart.bars.at(-1)?.[0];
 const primaryLast=primary?.last_completed_at||primary?.bars?.at(-1)?.[0],sourceSession=setupFactorSessionKey(last),primarySession=setupFactorSessionKey(primaryLast),barSession=setupFactorSessionKey(chart.bars.at(-1)?.[0]);
 if(!Number.isFinite(received)||received>now||now-received>300000||!setupFactorSourceCurrent(chart,now)||!primarySession||!sourceSession)return null;
 if(!barSession||chart.as_of&&setupFactorSessionKey(chart.as_of)!==sourceSession)return null;
 if(expectedInterval==='1wk'){
  const barDay=Date.parse(barSession+'T00:00:00Z'),sourceDay=Date.parse(sourceSession+'T00:00:00Z');
  if(!Number.isFinite(barDay)||!Number.isFinite(sourceDay)||barDay>sourceDay||sourceDay-barDay>=7*86400000)return null;
 }else if(expectedInterval==='1mo'){
  if(barSession.slice(0,7)!==sourceSession.slice(0,7)||barSession>sourceSession||sourceSession.slice(0,7)>=primarySession.slice(0,7)||sourceSession>primarySession)return null;
 }else if(sourceSession!==barSession)return null;
 if(expectedInterval==='1d'&&sourceSession!==primarySession)return null;
  if(expectedInterval==='1wk'){
  const sourceDay=Date.parse(sourceSession+'T00:00:00Z'),primaryDay=Date.parse(primarySession+'T00:00:00Z');
  if(sourceSession>primarySession||!Number.isFinite(sourceDay)||!Number.isFinite(primaryDay)||primaryDay-sourceDay>8*86400000)return null;
  }else if(expectedInterval==='1h'){
   const sourceDay=Date.parse(sourceSession+'T00:00:00Z'),primaryDay=Date.parse(primarySession+'T00:00:00Z');
   if(!Number.isFinite(sourceDay)||!Number.isFinite(primaryDay)||Math.abs(primaryDay-sourceDay)>4*86400000)return null;
 }
 return chart;
}
function setupFactorTensorFrame(row,relatedCharts,interval,now,analysisCache){
 const slot=interval==='1h'?'hourly':interval==='1wk'?'weekly':'daily',supplement=row?.supplemental_history?.[slot],supplementChart=supplement?.chart||supplement;
 const candidates=[row?.chart,supplementChart,...(relatedCharts||[]).filter(chart=>chart?.symbol===row?.symbol&&chart?.interval===interval)].filter((chart,index,all)=>chart&&chart.symbol===row?.symbol&&chart.interval===interval&&all.indexOf(chart)===index);
 if(!candidates.length)return {status:'not_supplied',value:null,detail:`No ${interval} completed chart is attached to this read.`};
 let last=null;
 for(const chart of candidates){
  const receipt=Date.parse(chart.received_at||chart.observed_at||'');
  if(chart.input_status?.current===false||chart.input_status?.missing_completed_periods>0||!setupFactorSourceCurrent(chart,now)||Number.isFinite(receipt)&&receipt>now){last={status:'stale',value:null,detail:`The supplied ${interval} Tensor chart is stale, incomplete, or has an invalid receipt clock.`};continue;}
  if(typeof tensorV698Frame!=='function'){last={status:'not_supplied',value:null,detail:'The pinned v698 Tensor state engine is not loaded in this runtime.'};continue;}
  const result=setupFactorMemoized(analysisCache,chart,'tensor-v698-state',()=>tensorV698Frame(chart,row.symbol,interval,now));
  if(result?.status==='measured')return result;
  if(result)last=result;
 }
 return last||{status:'not_supplied',value:null,detail:`No current ${interval} Tensor chart is available.`};
}
function setupFactorTensorSummary(frames){
 const ordered=['1wk','1d','1h'],available=ordered.map(interval=>frames[interval]).filter(frame=>frame?.status==='measured'),counts={bullish:0,bearish:0,neutral:0};
 for(const frame of available)counts[frame.value.direction]++;
 const direction=counts.bullish>=2?'bullish':counts.bearish>=2?'bearish':'neutral',alignment=available.length===3?(direction==='neutral'?'split':direction):'incomplete';
 return {frames:ordered.map(interval=>frames[interval]?.value||null),available_frames:available.length,bullish_frames:counts.bullish,bearish_frames:counts.bearish,neutral_frames:counts.neutral,direction,alignment};
}
function setupFactorMean(xs){return xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:null;}
function setupFactorSma(xs,n){const out=Array(xs.length).fill(null);let sum=0,valid=0;for(let i=0;i<xs.length;i++){if(setupFactorFinite(xs[i])){sum+=xs[i];valid++;}if(i>=n){if(setupFactorFinite(xs[i-n])){sum-=xs[i-n];valid--;}}if(i>=n-1&&valid===n)out[i]=sum/n;}return out;}
function setupFactorDailyVolumeProfile(bars,{sessions=60,bins=32,valueArea=.70}={}){
 if(!Array.isArray(bars)||bars.length<20)return null;
 const window=bars.slice(-sessions);let prior=-Infinity;
 for(const b of window){const time=Date.parse(b?.[0]);if(!Number.isFinite(time)||time<=prior||!Array.isArray(b)||b.length!==6||![1,2,3,4,5].every(i=>setupFactorFinite(b[i]))||b[1]<=0||b[2]<Math.max(b[1],b[3],b[4])||b[3]>Math.min(b[1],b[2],b[4])||b[5]<0)return null;prior=time;}
 const low=Math.min(...window.map(b=>b[3])),high=Math.max(...window.map(b=>b[2])),totalVolume=window.reduce((sum,b)=>sum+b[5],0);if(!(high>low)||!(totalVolume>0))return null;
 const width=(high-low)/bins,volume=Array(bins).fill(0);
 for(const b of window){const typical=(b[2]+b[3]+b[4])/3,index=Math.max(0,Math.min(bins-1,Math.floor((typical-low)/width)));volume[index]+=b[5];}
 let poc=0;for(let i=1;i<bins;i++)if(volume[i]>volume[poc])poc=i;
 let left=poc,right=poc,covered=volume[poc],target=totalVolume*valueArea;
 while(covered<target&&(left>0||right<bins-1)){
  const below=left>0?volume[left-1]:-1,above=right<bins-1?volume[right+1]:-1;
  if(below===above){if(left>0){left--;covered+=volume[left];}if(right<bins-1){right++;covered+=volume[right];}}
  else if(above>below){right++;covered+=volume[right];}
  else{left--;covered+=volume[left];}
 }
 const center=i=>low+(i+.5)*width;
 return {method:'daily_typical_price_volume_proxy',sessions:window.length,bins,value_area_fraction:valueArea,total_volume:totalVolume,low,high,poc:center(poc),value_area_low:low+left*width,value_area_high:low+(right+1)*width,covered_volume:covered,as_of:window.at(-1)[0]};
}
function setupFactorDivergenceSignalText(signal){
 const hidden=signal?.divergence_type==='hidden',bullish=signal?.kind==='bullish',label=signal?.indicator_label||signal?.indicator||'indicator',type=hidden?'Hidden':'Regular',priceMove=hidden?(bullish?'higher low':'lower high'):(bullish?'lower low':'higher high'),gaugeMove=hidden?(bullish?'lower low':'higher high'):(bullish?'higher low':'lower high'),dates=[signal?.first_confirmed_at,signal?.confirmed_at].every(x=>typeof x==='string'&&x.length>=10)?` at confirmed pivots ${signal.first_confirmed_at.slice(0,10)} and ${signal.confirmed_at.slice(0,10)}`:'',alignment=hidden&&signal?.continuation_alignment&&signal.continuation_alignment!=='unknown'?`; continuation ${signal.continuation_alignment}`:'',invalidated=signal?.current_status==='invalidated'?`; invalidated by a later completed close ${bullish?'below':'above'} ${setupFactorFinite(signal.invalidation_level)?setupFactorFmt(signal.invalidation_level):'the second pivot'}`:'';
 return `${type} ${signal?.kind||'unknown'} divergence in ${label}: price ${priceMove}, gauge ${gaugeMove}${dates}${alignment}${invalidated}`;
}
function setupFactorEma(xs,n){const out=Array(xs.length).fill(null),alpha=2/(n+1);let seed=0,count=0,value=null;for(let i=0;i<xs.length;i++){const x=xs[i];if(!setupFactorFinite(x)){seed=0;count=0;value=null;continue;}if(value===null){seed+=x;count++;if(count===n)value=seed/n;}else value=alpha*x+(1-alpha)*value;out[i]=value;}return out;}
function setupFactorWilder(xs,n){const out=Array(xs.length).fill(null);let seed=[];let value=null;for(let i=0;i<xs.length;i++){const x=xs[i];if(!setupFactorFinite(x)){seed=[];value=null;continue;}if(value===null){seed.push(x);if(seed.length===n){value=setupFactorMean(seed);out[i]=value;}}else{value=((n-1)*value+x)/n;out[i]=value;}}return out;}
function setupFactorRsi(closes){const moves=closes.map((x,i)=>i?x-closes[i-1]:null),g=moves.map(x=>setupFactorFinite(x)?Math.max(x,0):null),l=moves.map(x=>setupFactorFinite(x)?Math.max(-x,0):null),ga=setupFactorWilder(g,14),lo=setupFactorWilder(l,14);return closes.map((_,i)=>ga[i]===null?null:ga[i]===0&&lo[i]===0?50:lo[i]===0?100:100-100/(1+ga[i]/lo[i]));}
function setupFactorStoch(bars){const fast=Array(bars.length).fill(null);for(let i=13;i<bars.length;i++){const window=bars.slice(i-13,i+1),hi=Math.max(...window.map(x=>x[2])),lo=Math.min(...window.map(x=>x[3]));fast[i]=hi===lo?50:100*(bars[i][4]-lo)/(hi-lo);}const slow=setupFactorSma(fast,3),signal=setupFactorSma(slow,3);return {fast,slow,signal};}
function setupFactorMemoized(cache,chart,key,compute){
 const bars=chart?.bars??chart?.candles;if(!cache||!Array.isArray(bars))return compute();
 let byBars=cache.get('__setup_factor_memo_v1');if(!(byBars instanceof WeakMap)){byBars=new WeakMap();cache.set('__setup_factor_memo_v1',byBars);}
 let values=byBars.get(bars);if(!values){values=new Map();byBars.set(bars,values);}
 const memoKey=`${chart?.symbol||''}|${chart?.interval||''}|${key}`;if(values.has(memoKey))return values.get(memoKey);
 const value=compute();values.set(memoKey,value);return value;
}
const SETUP_FACTOR_ANALYSIS_CACHE=new Map(),SETUP_FACTOR_ANALYSIS_CACHE_MAX=128,SETUP_FACTOR_ANALYSIS_CACHE_MS=300000;
function setupFactorAnalysisKey(chart,requireCurrentExtensions=false){
 if(!chart||!Array.isArray(chart.bars)||!/^([a-f0-9]{64})$/.test(chart.sha256||''))return null;
 // Publisher receipt clocks change when an unchanged completed series is
 // republished. Key the expensive deterministic analysis on the actual bars
 // and their interpretation contract, not those receipt clocks. The short
 // bounded cache never bypasses the separate cadence/freshness checks.
 let input;try{input=JSON.stringify([chart.symbol||'',chart.interval||'',chart.source||'',chart.adjustment||null,chart.as_of||null,chart.last_completed_at||null,chart.bars]);}catch{return null;}
 let a=2166136261,b=0x9e3779b9,c=0x85ebca6b,d=0xc2b2ae35;
 for(let i=0;i<input.length;i++){const x=input.charCodeAt(i);a=Math.imul(a^x,16777619);b=Math.imul(b^(x+i),2246822519);c=Math.imul(c^(x-i),3266489917);d=Math.imul(d^(x+(i<<1)),668265263);}
 return `${input.length}:${(a>>>0).toString(16)}:${(b>>>0).toString(16)}:${(c>>>0).toString(16)}:${(d>>>0).toString(16)}:${requireCurrentExtensions?1:0}`;
}
function setupFactorAnalysisCacheGet(key,chart,now){
 if(!key)return null;const item=SETUP_FACTOR_ANALYSIS_CACHE.get(key);if(!item)return null;
 if(item.until<=now||item.analysis?.status==='unavailable'){SETUP_FACTOR_ANALYSIS_CACHE.delete(key);return null;}
 SETUP_FACTOR_ANALYSIS_CACHE.delete(key);SETUP_FACTOR_ANALYSIS_CACHE.set(key,item);
 // Only the analysis is reused. Carry the current receipt clocks into its
 // public projection; they are not evidence that the bars themselves changed.
 return {...item.analysis,observed_at:chart.observed_at,received_at:chart.received_at??null,source:chart.source??null,adjustment:chart.adjustment??null,input_sha256:chart.sha256??null};
}
function setupFactorAnalysisClockValid(chart,now){
 const at=typeof now==='string'?Date.parse(now):now,observed=Date.parse(chart?.observed_at),received=chart?.received_at==null?null:Date.parse(chart.received_at),end=chart?.last_completed_at==null?null:Date.parse(chart.last_completed_at),last=Date.parse(chart?.bars?.at(-1)?.[0]);
 return Number.isFinite(at)&&Number.isFinite(observed)&&observed<=at&&(chart?.received_at==null||Number.isFinite(received)&&received<=at)&&(chart?.last_completed_at==null||Number.isFinite(end)&&end<=at&&end<=observed&&(received===null||end<=received))&&Number.isFinite(last)&&last<at&&last<=observed&&(end===null||last<end);
}
function setupFactorAnalysisCachePut(key,analysis,now){
 if(!key||!analysis||analysis.status==='unavailable')return;
 SETUP_FACTOR_ANALYSIS_CACHE.delete(key);SETUP_FACTOR_ANALYSIS_CACHE.set(key,{analysis,until:now+SETUP_FACTOR_ANALYSIS_CACHE_MS});
 while(SETUP_FACTOR_ANALYSIS_CACHE.size>SETUP_FACTOR_ANALYSIS_CACHE_MAX)SETUP_FACTOR_ANALYSIS_CACHE.delete(SETUP_FACTOR_ANALYSIS_CACHE.keys().next().value);
}
function setupFactorAnalyzeChart(chart,cache,now=Date.now(),requireCurrentExtensions=false){
 if(!chart||typeof explainChart!=='function')return null;
 const key=`${chart.symbol||''}|${chart.interval||''}`,sourceKey=key+'|analysis_source',cached=cache?.get?.(key),sameSource=cache?.get?.(sourceKey)===chart;
 if(cached&&sameSource&&(!requireCurrentExtensions||cached.extended?.formula_version==='ohlcv-extensions-1'))return cached;
 const persistentKey=setupFactorAnalysisKey(chart,requireCurrentExtensions),persistent=setupFactorAnalysisClockValid(chart,now)?setupFactorAnalysisCacheGet(persistentKey,chart,now):null;
 if(persistent){if(cache){cache.set(key,persistent);cache.set(sourceKey,chart);}return persistent;}
 const identity=[chart.source||'',chart.adjustment||'',chart.as_of||'',chart.last_completed_at||'',chart.observed_at||'',chart.received_at||'',now].join('|');
 const analysis=setupFactorMemoized(cache,chart,`analysis:${identity}`,()=>explainChart(chart,now));
 setupFactorAnalysisCachePut(persistentKey,analysis,now);
 if(cache){cache.set(key,analysis);cache.set(sourceKey,chart);}
 return analysis;
}
function setupFactorMetrics(chart){
 const bars=Array.isArray(chart?.bars)?chart.bars:[],closes=bars.map(x=>x?.[4]),highs=bars.map(x=>x?.[2]),lows=bars.map(x=>x?.[3]),volumes=bars.map(x=>x?.[5]);
 const tr=bars.map((b,i)=>i?Math.max(b[2]-b[3],Math.abs(b[2]-bars[i-1][4]),Math.abs(b[3]-bars[i-1][4])):b[2]-b[3]),atr=setupFactorWilder(tr,14);
 const plus=bars.map((b,i)=>{if(!i)return null;const up=b[2]-bars[i-1][2],down=bars[i-1][3]-b[3];return up>down&&up>0?up:0;}),minus=bars.map((b,i)=>{if(!i)return null;const up=b[2]-bars[i-1][2],down=bars[i-1][3]-b[3];return down>up&&down>0?down:0;}),tr14=setupFactorWilder(tr,14),p14=setupFactorWilder(plus,14),m14=setupFactorWilder(minus,14);
 const pdi=bars.map((_,i)=>tr14[i]>0?100*p14[i]/tr14[i]:null),mdi=bars.map((_,i)=>tr14[i]>0?100*m14[i]/tr14[i]:null),dx=bars.map((_,i)=>setupFactorFinite(pdi[i])&&setupFactorFinite(mdi[i])&&pdi[i]+mdi[i]>0?100*Math.abs(pdi[i]-mdi[i])/(pdi[i]+mdi[i]):null),adx=setupFactorWilder(dx,14);
 const fast=setupFactorEma(closes,12),slow=setupFactorEma(closes,26),macdLine=closes.map((_,i)=>setupFactorFinite(fast[i])&&setupFactorFinite(slow[i])?fast[i]-slow[i]:null),macdSignal=setupFactorEma(macdLine,9),hist=macdLine.map((x,i)=>setupFactorFinite(x)&&setupFactorFinite(macdSignal[i])?x-macdSignal[i]:null);
 const stoch=setupFactorStoch(bars),obv=Array(bars.length).fill(null),ad=Array(bars.length).fill(null),mfi=Array(bars.length).fill(null),volOsc=Array(bars.length).fill(null);let obvNow=0,adNow=0;
 for(let i=0;i<bars.length;i++){const b=bars[i],v=b[5];if(!setupFactorFinite(v)){obv[i]=ad[i]=null;continue;}if(i&&setupFactorFinite(closes[i-1]))obvNow+=closes[i]>closes[i-1]?v:closes[i]<closes[i-1]?-v:0;obv[i]=obvNow;const range=b[2]-b[3],mult=range>0?((b[4]-b[3])-(b[2]-b[4]))/range:0;adNow+=mult*v;ad[i]=adNow;}
 const typical=bars.map(b=>(b[2]+b[3]+b[4])/3),positive=[],negative=[];for(let i=0;i<bars.length;i++){const flow=typical[i]*volumes[i];if(i){const prior=typical[i-1];positive.push(typical[i]>prior?flow:0);negative.push(typical[i]<prior?flow:0);}if(i>=14){const pos=positive.slice(-14).reduce((a,b)=>a+b,0),neg=negative.slice(-14).reduce((a,b)=>a+b,0);mfi[i]=pos+neg===0?50:neg===0?100:100-100/(1+pos/neg);}}
 const e5=setupFactorEma(volumes,5),e20=setupFactorEma(volumes,20);for(let i=0;i<bars.length;i++)if(setupFactorFinite(e5[i])&&setupFactorFinite(e20[i]))volOsc[i]=e5[i]-e20[i];
 const bb=[];for(let i=19;i<bars.length;i++){const win=closes.slice(i-19,i+1),avg=setupFactorMean(win),sd=Math.sqrt(setupFactorMean(win.map(x=>(x-avg)**2)));bb.push({index:i,width:avg>0?4*sd/avg:null,upper:avg+2*sd,lower:avg-2*sd});}
 const volSum=bars.slice(-20),vwapDen=volSum.every(b=>setupFactorFinite(b[5]))?volSum.reduce((a,b)=>a+b[5],0):0,vwap20=vwapDen>0?volSum.reduce((a,b)=>a+((b[2]+b[3]+b[4])/3)*b[5],0)/vwapDen:null;
 const returns=(period)=>bars.length>period&&setupFactorFinite(closes.at(-1-period))&&closes.at(-1-period)>0?closes.at(-1)/closes.at(-1-period)-1:null;
 const relvol=volumes.length>=21&&volumes.at(-1)>0&&volumes.slice(-21,-1).every(setupFactorFinite)?volumes.at(-1)/setupFactorMean(volumes.slice(-21,-1)):null;
 const validBars=bars.length>0&&bars.every(b=>Array.isArray(b)&&b.length===6&&[1,2,3,4].every(k=>setupFactorFinite(b[k])));
 return {bars,closes,highs,lows,volumes,atr,macdLine,macdSignal,hist,stoch,pdi,mdi,adx,obv,ad,mfi,volOsc,bb,vwap20,returns,relvol,validBars};
}
function setupFactorRelativeLine(stockBars,benchmarkBars,period=126){
  const index=rows=>{const map=new Map();for(const b of Array.isArray(rows)?rows:[]){const key=setupFactorSessionKey(b?.[0]);if(!key||!setupFactorFinite(b?.[4])||b[4]<=0||map.has(key))return null;map.set(key,b);}return map;},stock=index(stockBars),benchmark=index(benchmarkBars);if(!stock||!benchmark)return null;
  const common=[...stock.keys()].filter(k=>benchmark.has(k)).sort();if(common.length<=period)return null;const rows=common.slice(-(period+1)).map(k=>({session:k,stock:stock.get(k),benchmark:benchmark.get(k)})),ratios=rows.map(x=>x.stock[4]/x.benchmark[4]),base=ratios[0],current=ratios.at(-1);if(!ratios.every(setupFactorFinite)||!(base>0))return null;
  const tail=rows.slice(-63),ratioTail=ratios.slice(-63),priorRatios=ratioTail.slice(0,-1),priorPrices=tail.slice(0,-1).map(x=>x.stock[4]),rsNewHigh=priorRatios.length>0&&current>Math.max(...priorRatios),priceNewHigh=priorPrices.length>0&&rows.at(-1).stock[4]>Math.max(...priorPrices),excess=100*((rows.at(-1).stock[4]/rows[0].stock[4]-1)-(rows.at(-1).benchmark[4]/rows[0].benchmark[4]-1));if(!setupFactorFinite(excess))return null;
  return {period,matched_sessions:rows.length,through:rows.at(-1).session,indexed_100:100*current/base,excess_return_pct:excess,rs_new_63_session_high:rsNewHigh,price_new_63_session_high:priceNewHigh,rs_leads_price:rsNewHigh&&!priceNewHigh,series:rows.map(x=>[x.session,Math.round((100*(x.stock[4]/x.benchmark[4])/base)*1e6)/1e6])};
}
function setupFactorMarketInternals(chart,now){
 const series=chart?.chart||chart;if(!series||series.interval!=='1d'||!Array.isArray(series.bars)||!setupFactorSourceCurrent(series,now))return {status:series?'stale':'not_supplied',distribution_days:null,follow_through:null,source:series?.symbol||'SPY'};
 const bars=series.bars,n=bars.length;if(n<26||bars.slice(-26).some(b=>!setupFactorFinite(b?.[4])||!setupFactorFinite(b?.[5])))return {status:'insufficient_history',distribution_days:null,follow_through:null,source:series.symbol||'SPY'};
 const floor=Math.max(1,n-25),recent=[];for(let i=floor;i<n;i++){const prior=bars[i-1],bar=bars[i],drop=bar[4]/prior[4]-1;if(drop<=-.002&&bar[5]>prior[5]&&bars.at(-1)[4]<=bar[4]*1.05)recent.push({date:String(bar[0]).slice(0,10),change_pct:100*drop});}
 const start=Math.max(0,n-12);let lowIndex=start;for(let i=start+1;i<n;i++)if(bars[i][3]<bars[lowIndex][3])lowIndex=i;let ftd=null;
  for(let i=Math.max(lowIndex+4,n-9);i<n;i++){const previous=bars[i-1],bar=bars[i],gain=bar[4]/previous[4]-1;if(i-lowIndex>=4&&i-lowIndex<=10&&gain>=.017&&bar[5]>previous[5])ftd={date:String(bar[0]).slice(0,10),gain_pct:100*gain,low_date:String(bars[lowIndex][0]).slice(0,10),day_after_low:i-lowIndex};}
 return {status:'partial',source:series.symbol||'SPY',as_of:series.as_of||String(bars.at(-1)[0]).slice(0,10),distribution_days:recent,follow_through:ftd,lookback:25,method:'SPY index proxy: down >=0.2% on higher volume; distribution ages out after 25 bars or a 5% recovery; follow-through proxy is >=1.7% on higher volume 4-10 bars after the recent low'};
}
// Mechanical BARR screen: lead-in, accelerated bump, a >=2x vertical extension,
// then the close through projected support. The log-slope ratio is a scale-
// independent proxy for the source's chart-angle comparison.
// Reference: StockCharts ChartSchool, Bump and Run Reversal.
function setupFactorBumpRun(bars){
  if(!Array.isArray(bars)||bars.length<45)return null;
  const n=bars.length;
  if(bars.some(b=>!Array.isArray(b)||![2,3,4].every(i=>setupFactorFinite(b[i])&&b[i]>0)||b[2]<b[4]||b[3]>b[4]))return null;
  const leadLengths=[21,30,42,63],bumpLengths=[5,8,13,21],candidates=[];
  const fitLog=(rows,key)=>{
    const ys=rows.map(b=>Math.log(b[key]));if(ys.some(y=>!Number.isFinite(y)))return null;
    const count=ys.length,xmean=(count-1)/2,ymean=setupFactorMean(ys);let numerator=0,denominator=0;
    for(let i=0;i<count;i++){const dx=i-xmean;numerator+=dx*(ys[i]-ymean);denominator+=dx*dx;}
    if(!(denominator>0))return null;const slope=numerator/denominator,intercept=ymean-slope*xmean;
    return {slope,intercept,at:x=>Math.exp(intercept+slope*x)};
  };
  const firstBump=Math.max(21,n-105),lastBump=n-6;
  for(let bumpStart=firstBump;bumpStart<=lastBump;bumpStart++)for(const leadLength of leadLengths){
    const leadStart=bumpStart-leadLength;if(leadStart<0)continue;
    const lead=bars.slice(leadStart,bumpStart),line=fitLog(lead,3);if(!line||line.slope<=0)continue;
    let leadExcess=0;for(let i=0;i<lead.length;i++)leadExcess=Math.max(leadExcess,lead[i][2]-line.at(i));
    if(!(leadExcess>0))continue;
    for(const bumpLength of bumpLengths){
      const bumpEnd=bumpStart+bumpLength;if(bumpEnd>n-4)continue;
      const bump=bars.slice(bumpStart,bumpEnd),peakOffset=bump.reduce((best,b,i,a)=>b[2]>a[best][2]?i:best,0),peakIndex=bumpStart+peakOffset,peak=bars[peakIndex],bumpSlope=fitLog(bars.slice(bumpStart,peakIndex+1),4);
      if(!bumpSlope||bumpSlope.slope<1.5*line.slope)continue;
      const bumpExcess=peak[2]-line.at(peakIndex-leadStart),excessMultiple=bumpExcess/leadExcess;
      if(!(bumpExcess>0&&excessMultiple>=2))continue;
      let breakIndex=-1;for(let i=peakIndex+1;i<n;i++)if(bars[i][4]<line.at(i-leadStart)){breakIndex=i;break;}
      const currentSupport=line.at(n-1-leadStart),currentBelow=bars.at(-1)[4]<currentSupport;
      const rolloverPct=(peak[2]-bars.at(-1)[4])/peak[2]*100;if(!(rolloverPct>0)||peakIndex<n-30&&!(breakIndex>=n-20&&currentBelow))continue;
      const bumpPrefix=bump.slice(0,peakOffset+1),leadVolume=lead.every(b=>setupFactorFinite(b[5])&&b[5]>=0)?lead.reduce((s,b)=>s+b[5],0)/lead.length:null,bumpVolume=bumpPrefix.every(b=>setupFactorFinite(b[5])&&b[5]>=0)?bumpPrefix.reduce((s,b)=>s+b[5],0)/bumpPrefix.length:null;
      candidates.push({lead_start:String(lead[0][0]).slice(0,10),lead_end:String(lead.at(-1)[0]).slice(0,10),bump_start:String(bars[bumpStart][0]).slice(0,10),bump_peak:String(peak[0]).slice(0,10),break_at:breakIndex>=0?String(bars[breakIndex][0]).slice(0,10):null,lead_sessions:leadLength,bump_sessions:peakIndex-bumpStart+1,lead_trend_pct:(Math.exp(line.slope*Math.max(1,leadLength-1))-1)*100,bump_trend_pct:(Math.exp(bumpSlope.slope*Math.max(1,peakIndex-bumpStart))-1)*100,lead_excess_distance:leadExcess,bump_excess_distance:bumpExcess,excess_multiple:excessMultiple,rollover_pct:rolloverPct,lead_line_at_current:currentSupport,current_close:bars.at(-1)[4],current_below_support:currentBelow,downside_break_confirmed:breakIndex>=0&&currentBelow,volume_expansion:leadVolume>0&&bumpVolume!==null?bumpVolume/leadVolume:null});
    }
  }
  if(!candidates.length)return null;
  candidates.sort((a,b)=>b.bump_peak.localeCompare(a.bump_peak)||b.excess_multiple-a.excess_multiple||b.lead_sessions-a.lead_sessions);
  return candidates[0];
}
function setupFactorIsoWeek(value){
  const session=setupFactorSessionKey(value);if(!session)return null;const date=new Date(`${session}T00:00:00Z`);if(!Number.isFinite(date.getTime()))return null;
  date.setUTCDate(date.getUTCDate()+4-(date.getUTCDay()||7));const year=date.getUTCFullYear(),yearStart=Date.UTC(year,0,1),week=Math.ceil((((date.getTime()-yearStart)/86400000)+1)/7);return `${year}-${String(week).padStart(2,'0')}`;
}
// Weekly horn and pipe screens use only completed weeks. A weekly source bar
// from the same ISO week as the latest daily close is excluded so a partial
// current-week candle cannot confirm a reversal early.
function setupFactorWeeklyReversalPatterns(bars,latestDailySession){
  if(!Array.isArray(bars))return null;const currentWeek=setupFactorIsoWeek(latestDailySession),weekly=bars.filter(b=>Array.isArray(b)&&setupFactorIsoWeek(b[0])!==currentWeek);
  if(weekly.some((b,i)=>!setupFactorSessionKey(b?.[0])||![1,2,3,4].every(j=>setupFactorFinite(b[j])&&b[j]>0)||b[2]<Math.max(b[1],b[4])||b[3]>Math.min(b[1],b[4])||i>0&&setupFactorIsoWeek(b[0])<=setupFactorIsoWeek(weekly[i-1][0])))return {insufficient_history:true,completed_weeks:weekly.length};
  if(weekly.length<56)return {insufficient_history:true,completed_weeks:weekly.length};
  const candidates={horn_top:[],horn_bottom:[],pipe_top:[],pipe_bottom:[]},n=weekly.length;
  const percentile75=values=>{const sorted=values.slice().sort((a,b)=>a-b);return sorted.length?sorted[Math.min(sorted.length-1,Math.ceil(sorted.length*.75)-1)]:null;};
  const record=(kind,start,end,level,breakDirection,priorTrend,spikeRatio,overlapRatio=null)=>{
    let confirm=-1;for(let k=end+1;k<n;k++){if(breakDirection==='down'?weekly[k][4]<level:weekly[k][4]>level){confirm=k;break;}}
    if(confirm<0&&n-1-end>8)return;
    const leftVolume=weekly[start][5],rightVolume=weekly[end][5],volumeRatio=setupFactorFinite(leftVolume)&&leftVolume>0&&setupFactorFinite(rightVolume)?rightVolume/leftVolume:null;
    candidates[kind].push({kind,start_at:String(weekly[start][0]).slice(0,10),end_at:String(weekly[end][0]).slice(0,10),confirmed:confirm>=0,confirmed_at:confirm>=0?String(weekly[confirm][0]).slice(0,10):null,break_level:level,prior_trend_pct:priorTrend*100,spike_range_ratio:spikeRatio,overlap_ratio:overlapRatio,spike_volume_ratio:volumeRatio,completed_weeks:n});
  };
  for(let i=Math.max(52,n-24);i<=n-4;i++){
    const reference=weekly.slice(i-52,i).map(b=>b[2]-b[3]),threshold=percentile75(reference);if(!(threshold>0))continue;
    const trendStart=weekly[i-13]?.[4],trendEnd=weekly[i-1]?.[4];if(!(trendStart>0&&trendEnd>0))continue;const trend=trendEnd/trendStart-1;
    const a=weekly[i],mid=weekly[i+1],b=weekly[i+2],rangeA=a[2]-a[3],rangeB=b[2]-b[3],outerSpikes=rangeA>=threshold&&rangeB>=threshold?Math.min(rangeA,rangeB)/threshold:0;
    if(trend>=.10&&a[2]>mid[2]&&b[2]>mid[2]&&outerSpikes>=1){record('horn_top',i,i+2,Math.min(a[3],mid[3],b[3]),'down',trend,outerSpikes);}
    if(trend<=-.10&&a[3]<mid[3]&&b[3]<mid[3]&&outerSpikes>=1){record('horn_bottom',i,i+2,Math.max(a[2],mid[2],b[2]),'up',trend,outerSpikes);}
    const p=weekly[i],q=weekly[i+1],rangeP=p[2]-p[3],rangeQ=q[2]-q[3],overlap=Math.max(0,Math.min(p[2],q[2])-Math.max(p[3],q[3])),overlapRatio=overlap/Math.max(1e-9,Math.min(rangeP,rangeQ)),pipeSpikes=rangeP>=threshold&&rangeQ>=threshold?Math.min(rangeP,rangeQ)/threshold:0;
    if(trend>=.10&&p[2]>weekly[i-1][2]&&q[2]>weekly[i-1][2]&&pipeSpikes>=1&&overlapRatio>=.5)record('pipe_top',i,i+1,Math.min(p[3],q[3]),'down',trend,pipeSpikes,overlapRatio);
    if(trend<=-.10&&p[3]<weekly[i-1][3]&&q[3]<weekly[i-1][3]&&pipeSpikes>=1&&overlapRatio>=.5)record('pipe_bottom',i,i+1,Math.max(p[2],q[2]),'up',trend,pipeSpikes,overlapRatio);
  }
  const latest=rows=>rows.sort((a,b)=>b.end_at.localeCompare(a.end_at)||Number(b.confirmed)-Number(a.confirmed))[0]||null;
  return {completed_weeks:n,horn_top:latest(candidates.horn_top),horn_bottom:latest(candidates.horn_bottom),pipe_top:latest(candidates.pipe_top),pipe_bottom:latest(candidates.pipe_bottom)};
}
// Tower screen: a strong directional tower, a tight high/low pause, then a
// large completed candle that closes beyond the pause. It is a named geometry
// screen, not an interpretation of a single reversal candle.
function setupFactorTowerPattern(bars){
  if(!Array.isArray(bars)||bars.length<35)return null;const n=bars.length,median=values=>{const a=values.slice().sort((x,y)=>x-y);return a.length?a[Math.floor((a.length-1)/2)]:null;};
  const found=[];for(let capStart=Math.max(15,n-25);capStart<n-4;capStart++)for(let length=3;length<=8&&capStart+length<n;length++){
    const baseline=bars.slice(Math.max(0,capStart-45),capStart),bodyBase=median(baseline.map(b=>Math.abs(b[4]-b[1])).filter(x=>x>0)),rangeBase=median(baseline.map(b=>b[2]-b[3]).filter(x=>x>0));if(!(bodyBase>0&&rangeBase>0))continue;
    const cap=bars.slice(capStart,capStart+length),capLow=Math.min(...cap.map(b=>b[3])),capHigh=Math.max(...cap.map(b=>b[2])),capRange=capHigh-capLow,smallBodies=cap.every(b=>Math.abs(b[4]-b[1])<=bodyBase*1.05);if(!smallBodies||capRange>rangeBase*length*1.2)continue;
    const prior=bars.slice(Math.max(0,capStart-15),capStart),priorLow=Math.min(...prior.map(b=>b[3])),priorHigh=Math.max(...prior.map(b=>b[2])),upMove=priorLow>0?capHigh/priorLow-1:0,downMove=priorHigh>0?capLow/priorHigh-1:0;
    const left=bars.slice(Math.max(0,capStart-10),capStart),leftBull=left.some(b=>b[4]>b[1]&&b[4]-b[1]>=bodyBase*1.4),leftBear=left.some(b=>b[4]<b[1]&&b[1]-b[4]>=bodyBase*1.4);
    for(let k=capStart+length;k<Math.min(n,capStart+length+6);k++){
      const right=bars[k],body=Math.abs(right[4]-right[1]);if(upMove>=.12&&leftBull&&right[4]<right[1]&&body>=bodyBase*1.4&&right[4]<capLow)found.push({kind:'tower_top',start_at:String(left.find(b=>b[4]>b[1]&&b[4]-b[1]>=bodyBase*1.4)?.[0]||bars[capStart-1][0]).slice(0,10),cap_start:String(cap[0][0]).slice(0,10),break_at:String(right[0]).slice(0,10),prior_advance_pct:upMove*100,cap_high:capHigh,cap_low:capLow,break_close:right[4],confirmed:true});
      if(downMove<=-.12&&leftBear&&right[4]>right[1]&&body>=bodyBase*1.4&&right[4]>capHigh)found.push({kind:'tower_bottom',start_at:String(left.find(b=>b[4]<b[1]&&b[1]-b[4]>=bodyBase*1.4)?.[0]||bars[capStart-1][0]).slice(0,10),cap_start:String(cap[0][0]).slice(0,10),break_at:String(right[0]).slice(0,10),prior_decline_pct:Math.abs(downMove)*100,cap_high:capHigh,cap_low:capLow,break_close:right[4],confirmed:true});
    }
  }
  return found.sort((a,b)=>b.break_at.localeCompare(a.break_at))[0]||null;
}
function setupFactorScallop(bars,pivots=[]){
  if(!Array.isArray(bars)||bars.length<40||!Array.isArray(pivots))return null;const n=bars.length,turns=pivots.filter(p=>Number.isInteger(p.index)&&p.index>=Math.max(0,n-126)&&p.index<n-2&&p.confirmation_index<n&&setupFactorFinite(p.price)&&['support','resistance'].includes(p.kind)).sort((a,b)=>a.index-b.index),candidates=[];
  for(let j=2;j<turns.length;j++){
    const a=turns[j-2],b=turns[j-1],c=turns[j];if(a.kind!==c.kind||a.kind===b.kind||a.index>=b.index||b.index>=c.index||n-1-c.index>40)continue;
    const bullish=a.kind==='support',amplitude=bullish?b.price-a.price:a.price-b.price;if(!(amplitude>0))continue;
    const priorMovePct=amplitude/a.price,retracement=bullish?(b.price-c.price)/amplitude:(c.price-b.price)/amplitude,held=bullish?c.price>a.price+amplitude*.08:c.price<a.price-amplitude*.08;
    if(priorMovePct<.10||retracement<.2||retracement>.8||!held||b.index-a.index<4||c.index-b.index<4)continue;
    let breakout=-1;for(let i=c.index+1;i<n;i++)if(bullish?bars[i][4]>b.price:bars[i][4]<b.price){breakout=i;break;}
    const confirmed=breakout>=0&&(bullish?bars.at(-1)[4]>b.price:bars.at(-1)[4]<b.price);
    candidates.push({kind:bullish?'ascending_scallop':'descending_scallop',direction:bullish?'bullish':'bearish',start_at:String(bars[a.index][0]).slice(0,10),crest_or_trough_at:String(bars[b.index][0]).slice(0,10),retracement_at:String(bars[c.index][0]).slice(0,10),start_level:a.price,turn_level:b.price,retrace_level:c.price,prior_move_pct:priorMovePct*100,retracement_pct:retracement*100,confirmed,break_at:breakout>=0?String(bars[breakout][0]).slice(0,10):null,confirmation_level:b.price});
  }
  return candidates.sort((a,b)=>b.retracement_at.localeCompare(a.retracement_at))[0]||null;
}
function setupFactorPatternEvidence(bars,pivots=[]){
  if(!Array.isArray(bars)||bars.length<20)return null;
  const validVolume=bars.every(b=>setupFactorFinite(b?.[5])&&b[5]>=0),n=bars.length,close=bars.at(-1)[4];
  const baseCandidates=[];
  for(let length=25;length<=Math.min(90,n-1);length+=5){
    const start=n-length-1,base=bars.slice(start,n-1),high=Math.max(...base.map(b=>b[2])),low=Math.min(...base.map(b=>b[3])),prior=bars.slice(Math.max(0,start-126),start);
    if(!prior.length||!(high>0)||!(low>0))continue;
    const priorLow=Math.min(...prior.map(b=>b[3])),advance=priorLow>0?bars[start-1][4]/priorLow-1:null,depth=(high-low)/high;
    baseCandidates.push({length,start,high,low,depth,prior_advance:advance,pivot:high,breakout:close>high});
  }
  const qualifying=baseCandidates.filter(x=>x.depth<=.15&&x.prior_advance>=.30).sort((a,b)=>b.length-a.length),flat=qualifying[0]||null;
  const rangeBars=bars.slice(-Math.min(63,n)),rangeHigh=Math.max(...rangeBars.map(b=>b[2])),rangeLow=Math.min(...rangeBars.map(b=>b[3])),rangeDepth=rangeHigh>0?(rangeHigh-rangeLow)/rangeHigh:null;
  let dryup=null;if(validVolume&&flat){const base=bars.slice(flat.start,n-1),tail=base.slice(-10).map(b=>b[5]),prior=base.slice(-20,-10).map(b=>b[5]),ref=bars.slice(Math.max(0,flat.start-50),flat.start).map(b=>b[5]);if(tail.length===10&&prior.length===10&&ref.length>=10){const avg=a=>a.reduce((s,v)=>s+v,0)/a.length,tailAvg=avg(tail),priorAvg=avg(prior),refAvg=avg(ref);dryup={last10_vs_prior10:priorAvg>0?tailAvg/priorAvg:null,last10_vs_prior50:refAvg>0?tailAvg/refAvg:null,qualifies:priorAvg>0&&refAvg>0&&tailAvg<=priorAvg*.8&&tailAvg<=refAvg*.8};}}
  let tight3=null;if(n>=15){const w=[0,1,2].map(i=>bars.slice(n-15+i*5,n-10+i*5)),weekly=w.map(x=>x.at(-1)?.[4]),lo=Math.min(...weekly),hi=Math.max(...weekly);tight3={weekly_closes:weekly,range_pct:lo>0?(hi-lo)/lo*100:null,qualifies:lo>0&&(hi-lo)/lo<=.015};}
  let pivotTight=null;if(n>=30){const tail=bars.slice(-10),prior=bars.slice(-30,-10),hi=Math.max(...prior.map(b=>b[2])),lo=Math.min(...tail.map(b=>b[4])),high=Math.max(...tail.map(b=>b[4])),closeRange=lo>0?(high-lo)/lo:null; pivotTight={pivot:hi,close_range_pct:closeRange===null?null:closeRange*100,distance_below_pivot_pct:hi>0?(hi-close)/hi*100:null,qualifies:closeRange!==null&&closeRange<=.025&&close<=hi&&close>=hi*.98};}
  const turns=(Array.isArray(pivots)?pivots:[]).filter(p=>Number.isInteger(p.index)&&p.index>=Math.max(0,n-126)&&p.index<n-2&&setupFactorFinite(p.price)).sort((a,b)=>a.index-b.index),swings=[];for(const p of turns){if(!swings.length||swings.at(-1).kind!==p.kind)swings.push(p);else if(p.kind==='resistance'?p.price>swings.at(-1).price:p.price<swings.at(-1).price)swings[swings.length-1]=p;}
  const contractions=[];for(let i=0;i<swings.length-1;i++)if(swings[i].kind==='resistance'&&swings[i+1].kind==='support'&&swings[i].price>0)contractions.push({high:swings[i].price,low:swings[i+1].price,depth:(swings[i].price-swings[i+1].price)/swings[i].price,low_index:swings[i+1].index});const lastThree=contractions.slice(-3),vcp=lastThree.length===3&&lastThree[0].depth>lastThree[1].depth&&lastThree[1].depth>lastThree[2].depth&&lastThree[0].low_index<lastThree[1].low_index&&lastThree[1].low_index<lastThree[2].low_index;
  let failedBreak=null;for(let i=Math.max(20,n-35);i<n-1;i++){const prior=bars.slice(i-20,i),upper=Math.max(...prior.map(b=>b[2])),lower=Math.min(...prior.map(b=>b[3])),b=bars[i];if(b[4]>upper){for(let j=i+1;j<Math.min(n,i+6);j++)if(bars[j][4]<upper){failedBreak={kind:'bull_trap',level:upper,break_at:String(b[0]).slice(0,10),failure_at:String(bars[j][0]).slice(0,10),bars_to_failure:j-i};break;}}if(b[4]<lower){for(let j=i+1;j<Math.min(n,i+6);j++)if(bars[j][4]>lower){failedBreak={kind:'bear_trap',level:lower,break_at:String(b[0]).slice(0,10),failure_at:String(bars[j][0]).slice(0,10),bars_to_failure:j-i};break;}}}
  const recent=bars.slice(-6),volumes=validVolume?bars.slice(-21,-1).map(b=>b[5]):[],volumeBase=volumes.length===20?volumes.reduce((s,v)=>s+v,0)/20:null,atr20=bars.length>=21?bars.slice(-20).reduce((s,b,i)=>s+Math.max(b[2]-b[3],Math.abs(b[2]-bars[n-21+i][4]),Math.abs(b[3]-bars[n-21+i][4])),0)/20:null;
  const byKind=kind=>turns.filter(p=>p.kind===kind).slice(-3),recentHighs=byKind('resistance'),recentLows=byKind('support'),rangePct=xs=>xs.length>=2&&setupFactorMean(xs.map(p=>p.price))>0?100*(Math.max(...xs.map(p=>p.price))-Math.min(...xs.map(p=>p.price)))/setupFactorMean(xs.map(p=>p.price)):null,slopePct=xs=>xs.length>=2&&xs[0].price>0?100*(xs.at(-1).price/xs[0].price-1):null,highSpan=rangePct(recentHighs),lowSpan=rangePct(recentLows),highSlope=slopePct(recentHighs),lowSlope=slopePct(recentLows);
   const broadeningTop=recentLows.length===3&&recentHighs.length===3&&lowSpan<=1.8&&highSlope>=3&&recentHighs[1].price>recentHighs[0].price&&recentHighs[2].price>recentHighs[1].price?{flat_boundary:'support',flat_range_pct:lowSpan,diverging_boundary:'resistance',divergence_pct:highSlope,confirmed_break:close>Math.max(...recentHighs.map(p=>p.price)),pivots:[...recentLows,...recentHighs].map(p=>({kind:p.kind,price:p.price,date:p.pivot_at||null,confirmed_at:p.confirmed_at||null}))}:null;
   const broadeningBottom=recentLows.length===3&&recentHighs.length===3&&highSpan<=1.8&&lowSlope<=-3&&recentLows[1].price<recentLows[0].price&&recentLows[2].price<recentLows[1].price?{flat_boundary:'resistance',flat_range_pct:highSpan,diverging_boundary:'support',divergence_pct:lowSlope,confirmed_break:close<Math.min(...recentLows.map(p=>p.price)),pivots:[...recentLows,...recentHighs].map(p=>({kind:p.kind,price:p.price,date:p.pivot_at||null,confirmed_at:p.confirmed_at||null}))}:null;
   const ascendingBase=recentLows.length===3&&recentHighs.length===3&&lowSlope>=3&&highSpan<=3?{higher_lows_pct:lowSlope,resistance_range_pct:highSpan,confirmed_break:close>Math.max(...recentHighs.map(p=>p.price)),pivots:[...recentLows,...recentHighs].map(p=>({kind:p.kind,price:p.price,date:p.pivot_at||null,confirmed_at:p.confirmed_at||null}))}:null;
  const recentBars=bars.slice(-40),recentOffset=n-recentBars.length,extremeHigh=recentBars.reduce((best,b,i)=>b[2]>best.bar[2]?{i,bar:b}:best,{i:0,bar:recentBars[0]}),extremeLow=recentBars.reduce((best,b,i)=>b[3]<best.bar[3]?{i,bar:b}:best,{i:0,bar:recentBars[0]}),priorHighWindow=bars.slice(Math.max(0,recentOffset+extremeHigh.i-10),recentOffset+extremeHigh.i),priorLowWindow=bars.slice(Math.max(0,recentOffset+extremeLow.i-10),recentOffset+extremeLow.i),priorLowForTop=priorHighWindow.length?Math.min(...priorHighWindow.map(b=>b[3])):null,priorHighForBottom=priorLowWindow.length?Math.max(...priorLowWindow.map(b=>b[2])):null,postHigh=bars.slice(recentOffset+extremeHigh.i+1),postLow=bars.slice(recentOffset+extremeLow.i+1),vTop=priorLowForTop>0&&postHigh.length>=3&&100*(extremeHigh.bar[2]/priorLowForTop-1)>=15&&100*(extremeHigh.bar[2]-Math.min(...postHigh.map(b=>b[4])))/extremeHigh.bar[2]>=8?{peak_at:String(extremeHigh.bar[0]).slice(0,10),prior_rise_pct:100*(extremeHigh.bar[2]/priorLowForTop-1),decline_pct:100*(extremeHigh.bar[2]-Math.min(...postHigh.map(b=>b[4])))/extremeHigh.bar[2],state:'reversal_candidate'}:null,vBottom=priorHighForBottom>0&&postLow.length>=3&&100*(priorHighForBottom/extremeLow.bar[3]-1)>=15&&100*(Math.max(...postLow.map(b=>b[4]))-extremeLow.bar[3])/extremeLow.bar[3]>=8?{trough_at:String(extremeLow.bar[0]).slice(0,10),prior_decline_pct:100*(priorHighForBottom/extremeLow.bar[3]-1),rebound_pct:100*(Math.max(...postLow.map(b=>b[4]))-extremeLow.bar[3])/extremeLow.bar[3],state:'reversal_candidate'}:null;
  let deadCat=null;if(n>=25){const from=Math.max(0,n-35);for(let peak=from;peak<n-8;peak++){const peakHigh=Math.max(...bars.slice(Math.max(0,peak-15),peak+1).map(b=>b[2])),lowEnd=Math.min(n-4,peak+13),lowWindow=bars.slice(peak+1,lowEnd+1);if(!lowWindow.length)continue;const lowOffset=lowWindow.reduce((best,b,i,a)=>b[3]<a[best][3]?i:best,0),lowAt=peak+1+lowOffset,low=bars[lowAt]?.[3];if(!(low>0&&peakHigh/low-1>=.15))continue;const bounceEnd=Math.min(n-2,lowAt+10);if(bounceEnd<=lowAt+2)continue;const bounceBars=bars.slice(lowAt+1,bounceEnd+1),bounceHigh=Math.max(...bounceBars.map(b=>b[2])),drop=peakHigh-low,retrace=drop>0?(bounceHigh-low)/drop:null,bounceLow=Math.min(...bounceBars.map(b=>b[3])),failed=bounceBars.length>=3&&bars.at(-1)[4]<bounceLow;if(retrace>=.05&&retrace<.5){deadCat={peak_at:String(bars[peak][0]).slice(0,10),trough_at:String(bars[lowAt][0]).slice(0,10),bounce_high:bounceHigh,retracement_pct:retrace*100,bounce_low:bounceLow,state:failed?'downside_break_confirmed':'weak_bounce_candidate'};}}}
  let island=null;for(let i=Math.max(1,n-25);i<n-1&&!island;i++){const prior=bars[i-1],entry=bars[i],entryDown=entry[2]<prior[3],entryUp=entry[3]>prior[2];if(!entryDown&&!entryUp)continue;for(let j=i+1;j<Math.min(n,i+6);j++){const exit=bars[j],exitUp=exit[3]>bars[j-1][2],exitDown=exit[2]<bars[j-1][3],bull=entryDown&&exitUp&&exit[3]>entry[2],bear=entryUp&&exitDown&&exit[2]<entry[3];if(bull||bear){island={kind:bull?'bullish_island':'bearish_island',start_at:String(entry[0]).slice(0,10),end_at:String(exit[0]).slice(0,10),bars_inside:j-i,entry_gap_pct:100*Math.abs((entry[1]/prior[4])-1),exit_gap_pct:100*Math.abs((exit[1]/bars[j-1][4])-1)};break;}}}
  let roundingBottom=null;if(n>=40){for(let length=Math.min(126,n);length>=40&&!roundingBottom;length-=5){const w=bars.slice(-length),closes=w.map(b=>b[4]),third=Math.floor(length/3),left=setupFactorMean(closes.slice(0,third)),mid=setupFactorMean(closes.slice(third,2*third)),right=setupFactorMean(closes.slice(2*third)),minimum=Math.min(...closes),minimumIndex=closes.indexOf(minimum);if(left>0&&right>0&&minimumIndex>=third&&minimumIndex<2*third&&mid<=Math.min(left,right)*.92&&Math.abs(right/left-1)<=.2&&closes.at(-1)>=minimum*1.05)roundingBottom={bars:length,left_mean:left,middle_mean:mid,right_mean:right,trough_at:String(w[minimumIndex][0]).slice(0,10),state:'rounding_recovery_candidate'};}}
  let highTightFlag=null;if(validVolume&&n>=30){for(let flagLength=5;flagLength<=20&&!highTightFlag;flagLength++){for(let runLength=20;runLength<=40&&runLength+flagLength<n&&!highTightFlag;runLength++){const run=bars.slice(n-flagLength-runLength,n-flagLength),flag=bars.slice(-flagLength),runLow=Math.min(...run.map(b=>b[3])),runHigh=Math.max(...run.map(b=>b[2])),flagLow=Math.min(...flag.map(b=>b[3])),avg=a=>a.reduce((s,b)=>s+b[5],0)/a.length,runVol=avg(run),flagVol=avg(flag),rise=runLow>0?runHigh/runLow-1:0,depth=runHigh>0?(runHigh-flagLow)/runHigh:1,holdsUpper=flagLow>=runLow+(runHigh-runLow)*.55,pivotBars=flag.slice(0,-1),pivot=pivotBars.length?Math.max(...pivotBars.map(b=>b[2])):null;if(rise>=.8&&depth<=.25&&holdsUpper&&flagVol<=runVol&&setupFactorFinite(pivot))highTightFlag={run_bars:runLength,flag_bars:flagLength,advance_pct:rise*100,flag_depth_pct:depth*100,flag_volume_vs_run:runVol>0?flagVol/runVol:null,pivot,state:close>pivot?'pivot_broken':'forming'};}}}
  let climaxTop=null,sellingClimax=null;if(validVolume&&volumeBase>0&&atr20>0&&bars.length>=100){const start=bars.length-91,priorLow=Math.min(...bars.slice(start, n-6).map(b=>b[3])),runup=priorLow>0?bars[n-6][4]/priorLow-1:null;for(let i=n-6;i<n;i++){const b=bars[i],range=b[2]-b[3],rel=b[5]/volumeBase,closeLocation=range>0?(b[4]-b[3])/range:.5,prior=bars.slice(Math.max(0,i-20),i),priorHigh=prior.length?Math.max(...prior.map(x=>x[2])):null,priorLow20=prior.length?Math.min(...prior.map(x=>x[3])):null;
      if(runup!==null&&runup>=.50&&rel>=1.5&&range>=1.5*atr20&&b[4]<b[1]&&closeLocation<=.35&&priorHigh!==null&&b[2]>=priorHigh*.99)climaxTop={date:String(b[0]).slice(0,10),runup_pct:runup*100,relative_volume:rel,close_location:closeLocation};
      if(priorLow20!==null&&b[3]<=priorLow20&&rel>=1.5&&range>=1.5*atr20&&closeLocation>=.65)sellingClimax={date:String(b[0]).slice(0,10),relative_volume:rel,close_location:closeLocation,low:b[3],close:b[4]};}}
  const baseHistory=setupFactorHistoricalBases(bars),baseOnBase=setupFactorBaseOnBase(flat,baseHistory,bars),diamonds=setupFactorDiamonds(bars,turns),baseStage=setupFactorBaseStage(baseHistory,flat,bars);
  return {range:{bars:rangeBars.length,high:rangeHigh,low:rangeLow,depth_pct:rangeDepth===null?null:rangeDepth*100},flat_base:flat?{...flat,depth_pct:flat.depth*100,prior_advance_pct:flat.prior_advance*100}:null,dryup,three_weeks_tight:tight3,pivot_tightness:pivotTight,vcp:{contractions:lastThree,qualifies:vcp},failed_break:failedBreak,right_angled_broadening_top:broadeningTop,right_angled_broadening_bottom:broadeningBottom,ascending_base:ascendingBase,v_top:vTop,v_bottom:vBottom,dead_cat_bounce:deadCat,island_reversal:island,rounding_bottom:roundingBottom,high_tight_flag:highTightFlag,bump_run_reversal:setupFactorBumpRun(bars),climax_top:climaxTop,selling_climax:sellingClimax,base_history:baseHistory,base_on_base:baseOnBase,base_stage:baseStage,diamonds,runup_pct:validVolume&&bars.length>=100&&volumeBase>0&&bars[n-6][4]>0?(bars[n-6][4]/Math.min(...bars.slice(Math.max(0,n-91),n-6).map(b=>b[3]))-1)*100:null,volume_available:validVolume};
}
function setupFactorWyckoffEvidence(bars,pivots=[]){
 if(!Array.isArray(bars)||bars.length<60||!bars.every(b=>Array.isArray(b)&&setupFactorFinite(b[2])&&setupFactorFinite(b[3])&&setupFactorFinite(b[4])&&b[2]>=b[3]&&b[3]>0))return null;
 const n=bars.length,close=bars.at(-1)[4],prior=bars.slice(-60,-20),recent=bars.slice(-20),priorMean=setupFactorMean(prior.map(b=>b[4])),recentMean=setupFactorMean(recent.map(b=>b[4])),priorMovePct=prior[0][4]>0?100*(prior.at(-1)[4]/prior[0][4]-1):null,rangeBars=bars.slice(-40),high=Math.max(...rangeBars.map(b=>b[2])),low=Math.min(...rangeBars.map(b=>b[3])),rangePct=low>0?100*(high-low)/setupFactorMean(rangeBars.map(b=>b[4])):null,positionPct=high>low?100*(close-low)/(high-low):50,trendPct=priorMean>0?100*(recentMean/priorMean-1):null,baseWidthPct=low>0?100*(Math.max(...recent.map(b=>b[2]))-Math.min(...recent.map(b=>b[3])))/setupFactorMean(recent.map(b=>b[4])):null;
 let phase='transition_proxy';
 if(setupFactorFinite(priorMovePct)&&setupFactorFinite(baseWidthPct)&&baseWidthPct<=15&&priorMovePct<=-15&&positionPct>=50)phase='accumulation_candidate';
 else if(setupFactorFinite(priorMovePct)&&setupFactorFinite(baseWidthPct)&&baseWidthPct<=15&&priorMovePct>=15&&positionPct<=50)phase='distribution_candidate';
 else if(setupFactorFinite(trendPct)&&trendPct>=3&&close>=recentMean)phase='markup_proxy';
 else if(setupFactorFinite(trendPct)&&trendPct<=-3&&close<=recentMean)phase='markdown_proxy';
 else if(setupFactorFinite(baseWidthPct)&&baseWidthPct<=15&&Math.abs(trendPct||0)<3)phase='trading_range_proxy';
 const volumeReady=bars.slice(-41).every(b=>setupFactorFinite(b[5])&&b[5]>=0),trueRanges=[];for(let i=Math.max(1,n-20);i<n;i++)trueRanges.push(Math.max(bars[i][2]-bars[i][3],Math.abs(bars[i][2]-bars[i-1][4]),Math.abs(bars[i][3]-bars[i-1][4])));const atr=setupFactorMean(trueRanges);
 const confirmed=(Array.isArray(pivots)?pivots:[]).filter(p=>Number.isInteger(p.index)&&Number.isInteger(p.confirmation_index)&&p.index>=Math.max(0,n-100)&&p.confirmation_index<n&&p.index<p.confirmation_index&&setupFactorFinite(p.price)&&['support','resistance'].includes(p.kind)),events=[];
 for(const kind of ['spring','upthrust']){
  const pivotKind=kind==='spring'?'support':'resistance',levels=confirmed.filter(p=>p.kind===pivotKind).sort((a,b)=>b.confirmation_index-a.confirmation_index);
  let latest=null;
  for(const pivot of levels){
   const level=pivot.price,first=Math.max(n-20,pivot.confirmation_index+1),threshold=Math.max(level*.001,atr*.1);
   for(let i=n-1;i>=first;i--){
    const probe=bars[i],tested=kind==='spring'?probe[3]<level-threshold:probe[2]>level+threshold;if(!tested)continue;
    let confirm=-1;for(let j=i;j<Math.min(n,i+6);j++)if(kind==='spring'?bars[j][4]>level:bars[j][4]<level){confirm=j;break;}
    if(confirm<0)continue;
    const probeVolumes=bars.slice(Math.max(0,i-20),i).map(b=>b[5]),probeMean=volumeReady&&probeVolumes.length===20&&probeVolumes.every(v=>setupFactorFinite(v)&&v>=0)?setupFactorMean(probeVolumes):null,probeVolume=probeMean>0&&setupFactorFinite(probe[5])?probe[5]/probeMean:null,currentHeld=kind==='spring'?close>=level:close<=level;
    const candidate={kind:kind+'_candidate',level,pivot_at:String(pivot.pivot_at||bars[pivot.index][0]).slice(0,10),probe_at:String(probe[0]).slice(0,10),confirmed_at:String(bars[confirm][0]).slice(0,10),bars_to_reclaim:confirm-i,probe_low:probe[3],probe_high:probe[2],volume_ratio:probeVolume,current_state:currentHeld?'reclaim_held':'reclaim_lost',volume_supported:probeVolume!==null&&probeVolume>=1.25,method:'Confirmed swing level swept and recovered on a completed close within five bars; volume is a separate confirmation.'};
    if(!latest||candidate.confirmed_at>latest.confirmed_at||candidate.confirmed_at===latest.confirmed_at&&candidate.pivot_at>latest.pivot_at)latest=candidate;
    break;
   }
  }
  if(latest)events.push(latest);
 }
 const latest=[...new Map(events.map(e=>[e.kind,e])).values()].sort((a,b)=>b.confirmed_at.localeCompare(a.confirmed_at));
 return {phase:{label:phase,trend_pct:trendPct,prior_40_bar_move_pct:priorMovePct,range_40_bar_pct:rangePct,position_in_range_pct:positionPct,base_width_20_bar_pct:baseWidthPct,method:'Completed-bar trend and range proxy. Accumulation/distribution are candidates after a preceding move, not discretionary Wyckoff annotations.'},events:latest,volume_available:volumeReady,method:'Completed OHLCV and confirmed pivots only; a sweep must reclaim its level on a completed close within five bars.'};
}
function setupFactorHistoricalBases(bars){
 if(!Array.isArray(bars)||bars.length<80||bars.some(b=>!setupFactorFinite(b?.[2])||!setupFactorFinite(b?.[3])||!setupFactorFinite(b?.[4])))return [];
 const n=bars.length,raw=[];
 for(let start=25;start<=n-55;start+=5){
  const prior=bars.slice(Math.max(0,start-126),start);if(prior.length<20)continue;
  const priorLow=Math.min(...prior.map(b=>b[3])),priorClose=bars[start-1][4];if(!(priorLow>0&&priorClose>0))continue;
  for(let length=25;length<=90&&start+length<n;length+=5){
   const end=start+length,base=bars.slice(start,end),high=Math.max(...base.map(b=>b[2])),low=Math.min(...base.map(b=>b[3])),depth=high>0?(high-low)/high:null,advance=priorClose/priorLow-1;
   if(!(depth!==null&&depth<=.15&&advance>=.30))continue;
   let breakoutIndex=-1;for(let i=end;i<Math.min(n,end+6);i++)if(bars[i][4]>high){breakoutIndex=i;break;}
   if(breakoutIndex<0)continue;
   const vols=bars.slice(Math.max(0,breakoutIndex-50),breakoutIndex).map(b=>b[5]),vol=bars[breakoutIndex][5],avg=vols.length===50&&vols.every(v=>setupFactorFinite(v)&&v>=0)?setupFactorMean(vols):null;
   raw.push({start,end,length,high,low,depth_pct:depth*100,prior_advance_pct:advance*100,breakout_index:breakoutIndex,breakout_at:String(bars[breakoutIndex][0]).slice(0,10),breakout_volume_ratio:avg>0&&setupFactorFinite(vol)?vol/avg:null});
  }
 }
 const sameBreak=new Map();for(const row of raw){const prior=sameBreak.get(row.breakout_index);if(!prior||row.length>prior.length||row.length===prior.length&&row.depth_pct<prior.depth_pct)sameBreak.set(row.breakout_index,row);}
 const ordered=[...sameBreak.values()].sort((a,b)=>a.breakout_index-b.breakout_index||b.length-a.length),selected=[];
 for(const row of ordered){const last=selected.at(-1);if(!last){selected.push(row);continue;}if(row.start<=last.breakout_index||row.breakout_index-last.breakout_index<25)continue;selected.push(row);}
 return selected;
}
function setupFactorBaseOnBase(flat,history,bars){
 if(!flat||!Array.isArray(history)||!Array.isArray(bars)||bars.length<126)return null;
 const priorBases=history.filter(x=>x.breakout_index<flat.start&&flat.start-x.breakout_index<=100).sort((a,b)=>b.breakout_index-a.breakout_index);
 for(const prior of priorBases){
  const bridge=bars.slice(prior.breakout_index,flat.start);if(!bridge.length)continue;
  const bridgeHigh=Math.max(...bridge.map(b=>b[2])),advancePct=100*(bridgeHigh/prior.high-1),supportPct=100*(flat.low/prior.high-1);
  if(advancePct<0||advancePct>=25||supportPct< -5||flat.depth_pct>15)continue;
  return {first_base:{start:String(bars[prior.start]?.[0]||'').slice(0,10),pivot:prior.high,breakout_at:prior.breakout_at},upper_base:{start:String(bars[flat.start]?.[0]||'').slice(0,10),sessions:flat.length,low:flat.low,pivot:flat.high,depth_pct:flat.depth_pct},intervening_advance_pct:advancePct,upper_base_support_vs_prior_pivot_pct:supportPct,breakout:false,rule:'first confirmed base break; less than 25% advance before the next shallow base holds within 5% of the prior pivot'};
 }
 return null;
}
function setupFactorBaseStage(history,flat,bars){
 if(!Array.isArray(history)||!Array.isArray(bars)||bars.length<126)return null;
 const complete=history.slice(-8),last=complete.at(-1),forming=flat?{start:String(bars[flat.start]?.[0]||'').slice(0,10),sessions:flat.length,depth_pct:flat.depth_pct,breakout:false}:null;
 let stage=0,prior=null;for(const base of complete){if(!prior){stage=1;prior=base;continue;}const bridge=bars.slice(prior.breakout_index,base.start),advance=bridge.length?Math.max(...bridge.map(b=>b[2]))/prior.high-1:0;if(advance>=.20)stage++;prior=base;}
 if(last&&flat&&flat.start>last.breakout_index){const bridge=bars.slice(last.breakout_index,flat.start),advance=bridge.length?Math.max(...bridge.map(b=>b[2]))/last.high-1:0;if(advance>=.20)stage++;}
 return {stage_lower_bound:Math.max(complete.length?1:0,stage),completed_base_breakouts:complete.length,bases:complete.map(x=>({start:String(bars[x.start]?.[0]||'').slice(0,10),breakout_at:x.breakout_at,depth_pct:x.depth_pct})),forming_base:forming,window_sessions:bars.length,method:'distinct flat-base screens in supplied daily history; a new stage is counted only after a 20% advance between confirmed base breakouts'};
}
function setupFactorDiamonds(bars,turns){
 const result={top:null,bottom:null};if(!Array.isArray(bars)||bars.length<50||!Array.isArray(turns))return result;
 const n=bars.length,valid=turns.filter(p=>Number.isInteger(p.index)&&p.index>=Math.max(0,n-110)&&p.index<n&&Number.isInteger(p.confirmation_index??(p.index+2))&&(p.confirmation_index??(p.index+2))<n&&setupFactorFinite(p.price)&&['resistance','support'].includes(p.kind)).sort((a,b)=>a.index-b.index),swings=[];
 for(const p of valid){if(!swings.length||swings.at(-1).kind!==p.kind)swings.push(p);else if(p.kind==='resistance'?p.price>swings.at(-1).price:p.price<swings.at(-1).price)swings[swings.length-1]=p;}
 for(let start=swings.length-6;start>=0;start--){const group=swings.slice(start,start+6);if(group.length!==6||group.some((p,i)=>i&&p.kind===group[i-1].kind))continue;
  const highs=group.filter(p=>p.kind==='resistance'),lows=group.filter(p=>p.kind==='support');if(highs.length!==3||lows.length!==3)continue;
  const [h1,h2,h3]=highs,[l1,l2,l3]=lows;if(h2.index===h3.index||l2.index===l3.index)continue;const initial=h1.price-l1.price,middle=h2.price-l2.price,late=h3.price-l3.price,span=group.at(-1).index-group[0].index;
  if(!(initial>0&&middle>=initial*1.15&&middle>=late*1.15&&span>=20&&span<=100&&h2.price>=h1.price*1.02&&h2.price>=h3.price*1.02&&l2.price<=l1.price*.98&&l2.price<=l3.price*.98))continue;
  const close=bars.at(-1)[4],downSlope=(l3.price-l2.price)/(l3.index-l2.index),upSlope=(h3.price-h2.price)/(h3.index-h2.index),lowerNow=l2.price+downSlope*(n-1-l2.index),upperNow=h2.price+upSlope*(n-1-h2.index),preStart=Math.max(0,group[0].index-30),before=group[0].index>preStart?bars[preStart][4]:null,priorChange=before>0?bars[group[0].index-1][4]/before-1:null;
  if(priorChange!==null&&priorChange>=.10)result.top={start_at:String(bars[group[0].index][0]).slice(0,10),end_at:String(bars[group.at(-1).index][0]).slice(0,10),highs:highs.map(p=>({price:p.price,index:p.index})),lows:lows.map(p=>({price:p.price,index:p.index})),widths:{initial,middle,late},lower_boundary_now:lowerNow,confirmed_break:close<lowerNow,state:close<lowerNow?'downside_break_confirmed':'forming'};
  if(priorChange!==null&&priorChange<=-.10)result.bottom={start_at:String(bars[group[0].index][0]).slice(0,10),end_at:String(bars[group.at(-1).index][0]).slice(0,10),highs:highs.map(p=>({price:p.price,index:p.index})),lows:lows.map(p=>({price:p.price,index:p.index})),widths:{initial,middle,late},upper_boundary_now:upperNow,confirmed_break:close>upperNow,state:close>upperNow?'upside_break_confirmed':'forming'};
  break;
 }
 return result;
}
function setupFactorAndrewsPitchfork(bars,pivots=[]){
 if(!Array.isArray(bars)||bars.length<20||!Array.isArray(pivots))return null;
 const n=bars.length,turns=[];for(const p of pivots.filter(x=>Number.isInteger(x?.index)&&x.index>=0&&x.index<n&&Number.isInteger(x.confirmation_index??(x.index+2))&&(x.confirmation_index??(x.index+2))<n&&setupFactorFinite(x.price)&&['resistance','support'].includes(x.kind)).sort((a,b)=>a.index-b.index)){if(!turns.length||turns.at(-1).kind!==p.kind)turns.push(p);else if(p.kind==='resistance'?p.price>turns.at(-1).price:p.price<turns.at(-1).price)turns[turns.length-1]=p;}
 const anchors=turns.slice(-3);if(anchors.length!==3||anchors[0].kind===anchors[1].kind||anchors[1].kind===anchors[2].kind)return null;
 const [p0,p1,p2]=anchors,midIndex=(p1.index+p2.index)/2,midPrice=(p1.price+p2.price)/2;if(midIndex===p0.index)return null;
 const slope=(midPrice-p0.price)/(midIndex-p0.index),x=n-1,median=p0.price+slope*(x-p0.index),line1=p1.price+slope*(x-p1.index),line2=p2.price+slope*(x-p2.index),upper=Math.max(line1,line2),lower=Math.min(line1,line2),close=bars.at(-1)[4];
 return {anchors:anchors.map(p=>({kind:p.kind,price:p.price,index:p.index,date:String(p.pivot_at||bars[p.index]?.[0]||'').slice(0,10),confirmed_at:p.confirmed_at||null})),median_now:median,upper_now:upper,lower_now:lower,close,position:close>upper?'above_channel':close<lower?'below_channel':close>median?'upper_half':'lower_half',slope_per_bar:slope,method:'median line from first confirmed pivot to the midpoint of the next two alternating confirmed pivots; parallels through the second and third pivots'};
}
function setupFactorGapTaxonomy(bars){
 if(!Array.isArray(bars)||bars.length<22)return null;
 const gaps=[];for(let i=Math.max(1,bars.length-60);i<bars.length;i++){const prior=bars[i-1],b=bars[i],up=b[3]>prior[2],down=b[2]<prior[3];if(!up&&!down)continue;const direction=up?'up':'down',gapWidth=up?b[3]-prior[2]:prior[3]-b[2],trueRange=[];for(let j=Math.max(1,i-14);j<i;j++)trueRange.push(Math.max(bars[j][2]-bars[j][3],Math.abs(bars[j][2]-bars[j-1][4]),Math.abs(bars[j][3]-bars[j-1][4])));const atr=setupFactorMean(trueRange),volumes=bars.slice(Math.max(0,i-50),i).map(x=>x[5]).filter(setupFactorFinite),avgVolume=volumes.length===50?setupFactorMean(volumes):null,relativeVolume=avgVolume>0&&setupFactorFinite(b[5])?b[5]/avgVolume:null,prior20=bars.slice(Math.max(0,i-20),i),rangeHigh=prior20.length?Math.max(...prior20.map(x=>x[2])):null,rangeLow=prior20.length?Math.min(...prior20.map(x=>x[3])):null,breaksRange=direction==='up'?b[3]>rangeHigh: b[2]<rangeLow,priorCloses=bars.slice(Math.max(0,i-90),i).map(x=>x[4]),priorRun=priorCloses.length>=20&&priorCloses[0]>0?priorCloses.at(-1)/priorCloses[0]-1:null,range=b[2]-b[3],closeLocation=range>0?(b[4]-b[3])/range:.5,extended=setupFactorFinite(priorRun)&&Math.abs(priorRun)>=.5,exhaustion=extended&&relativeVolume>=1.5&&atr>0&&range>=1.5*atr&&(direction==='up'?b[4]<b[1]&&closeLocation<=.35:b[4]>b[1]&&closeLocation>=.65),kind=breaksRange&&relativeVolume>=1.5&&atr>0&&gapWidth>=.5*atr?'breakaway':exhaustion?'exhaustion':atr>0&&gapWidth>=.5*atr&&relativeVolume>=1&&((direction==='up'&&priorRun>0)||(direction==='down'&&priorRun<0))?'runaway':atr>0&&gapWidth<.5*atr?'common':'unclassified';
  gaps.push({date:String(b[0]).slice(0,10),direction,low:up?prior[2]:b[2],high:up?b[3]:prior[3],gap_atr:atr>0?gapWidth/atr:null,relative_volume:relativeVolume,volume_observations:volumes.length,kind,confirmed:false,method:'OHLCV context screen; gap class remains a candidate'});}
 return gaps;
}
function setupFactorPowerEarningsGap(bars,events,now){
 if(!Array.isArray(bars)||!Array.isArray(events))return null;
 const causal=events.filter(e=>e?.actual_occurrence_source&&[e.announcement_at,e.first_published_at,e.signal_available_at].every(x=>{const t=Date.parse(x||'');return Number.isFinite(t)&&t<=now;})).sort((a,b)=>Date.parse(b.signal_available_at)-Date.parse(a.signal_available_at));
 for(const event of causal){const available=Date.parse(event.signal_available_at);let i=-1;for(let j=1;j<bars.length;j++){const open=setupFactorUsSessionOpen(bars[j][0]);if(open!==null&&available<open){i=j;break;}}if(i<=0)continue;const prior=bars[i-1],gap=bars[i],prior50=bars.slice(Math.max(0,i-50),i),volumes=prior50.map(b=>b[5]),avg=volumes.length===50&&volumes.every(setupFactorFinite)?setupFactorMean(volumes):null,gapPct=setupFactorFinite(prior[4])&&prior[4]>0?100*(gap[1]/prior[4]-1):null,relativeVolume=avg>0&&setupFactorFinite(gap[5])?gap[5]/avg:null,upRange=bars.slice(Math.max(0,i-20),i),oldHigh=Math.max(...upRange.map(b=>b[2])),aboveRange=gap[1]>oldHigh,after=bars.slice(i+1),failed=after.some(b=>b[4]<gap[3]),held=after.length>=5&&!failed,ready=avg!==null&&relativeVolume!==null&&setupFactorFinite(gapPct),candidate=ready&&gapPct>=5&&relativeVolume>=2;return {event_at:event.announcement_at,available_at:event.signal_available_at,gap_at:String(gap[0]).slice(0,10),gap_pct:gapPct,relative_volume:relativeVolume,above_prior_20_high:aboveRange,hold_bars:Math.min(after.length,5),held,failed,state:!ready?'insufficient_data':failed?'failed':held&&candidate?'held_price_volume_candidate':candidate?'forming_price_volume_candidate':'not_qualified',rule:'Ticker-specific actual earnings were available before the 09:30 ET session open; gap >=5%; volume >=2x the preceding 50 sessions; five completed closes hold above the gap-day low for a held candidate. EPS surprise is not supplied.'};}
 return null;
}
function setupFactorPlanChecks(row,planInput=row?.action_plan,now=Date.now()){
 const plan=planInput?.brief||planInput||{},entry=plan.entry||{},invalidation=plan.invalidation||{},objective=(plan.objectives||[])[0],e=(row?.evidence||[]).find(x=>x.id===row?.primary_evidence_id)||(row?.evidence||[]).find(x=>x.active)||(row?.evidence||[])[0]||{};
 const hasEntry=setupFactorFinite(entry.acceptable_low)||setupFactorFinite(entry.price),windowStart=row?.window_start||e.entry_window_start||entry.window_start,windowEnd=row?.window_end||e.entry_window_end||entry.window_end,windowStartMs=Date.parse(windowStart||''),windowEndMs=Date.parse(windowEnd||''),hasWindow=!!(entry.window||entry.deadline||Number.isFinite(windowStartMs)||Number.isFinite(windowEndMs)),hasInvalidation=!!(invalidation.text||setupFactorFinite(invalidation.price)),hasObjective=!!(objective?.text||setupFactorFinite(objective?.price));
 const timeText=ms=>Number.isFinite(ms)?setupFactorDateFormatter('en-US',{timeZone:'America/New_York',dateStyle:'medium',timeStyle:'short'}).format(new Date(ms))+' ET':null;
 const windowClock=Number.isFinite(windowStartMs)&&Number.isFinite(windowEndMs)?now<windowStartMs?`Opens ${timeText(windowStartMs)}; closes ${timeText(windowEndMs)}.`:now>=windowEndMs?`Window closed ${timeText(windowEndMs)}.`:`Window is open; closes ${timeText(windowEndMs)}.`:Number.isFinite(windowStartMs)?`Starts ${timeText(windowStartMs)}.`:Number.isFinite(windowEndMs)?`Deadline ${timeText(windowEndMs)}.`:null;
 const daily=row?.chart?.interval==='1d'&&setupFactorSourceCurrent(row.chart,now)?row.chart:null,lastClose=daily?.bars?.at(-1)?.[4],cap=entry.acceptable_high,capDistance=setupFactorFinite(cap)&&cap>0&&setupFactorFinite(lastClose)?(cap-lastClose)/cap*100:null;
 const capText=capDistance===null?'Distance to cap unavailable: a numeric cap and fresh completed daily close are not both available.':`Distance to cap: latest completed close ${setupFactorFmt(lastClose)} is ${setupFactorFmt(Math.abs(cap-lastClose))} (${setupFactorFmt(Math.abs(capDistance))}%) ${capDistance>=0?'below':'above'} the ${setupFactorFmt(cap)} cap.`;
 const values=[
  {id:'buy_zone',status:hasEntry?'partial':'not_supplied',detail:hasEntry?`Chart research entry ${entry.rule_text||entry.text||setupFactorFmt(entry.price)}; band ${setupFactorFinite(entry.acceptable_low)?setupFactorFmt(entry.acceptable_low)+'–'+(setupFactorFinite(entry.acceptable_high)?setupFactorFmt(entry.acceptable_high):'cap not supplied'):'not supplied'}. This is the setup map, not a sleeve order instruction.`:'No explicit action-plan entry band.',material:hasEntry},
  {id:'buy_window',status:hasWindow?'partial':'not_supplied',detail:hasWindow?[entry.window||entry.deadline,windowClock,capText].filter(Boolean).join(' · ')+' No order authority is implied.':'No explicit entry-window description or clock in the public setup plan. '+capText,material:hasWindow},
  {id:'invalidation_cases',status:hasInvalidation&&hasObjective?'partial':hasInvalidation||hasObjective?'partial':'not_supplied',detail:hasInvalidation||hasObjective?`Chart-map invalidation: ${invalidation.text||invalidation.price||'not supplied'}; first objective: ${objective?.text||objective?.price||'not supplied'}. Good/bad case text is shown in the plan when available.`:'No explicit chart-map invalidation or objective.',material:hasInvalidation&&hasObjective},
  {id:'sleeve_exit',status:e.exit_rule||setupFactorFinite(e.stop_price)?'partial':'not_supplied',detail:e.exit_rule||setupFactorFinite(e.stop_price)?`Sleeve ${e.strategy_name||e.book_label||'unknown'}; stop ${e.stop_price??'rule-based'}; exit ${e.exit_rule||'not supplied'}.`:'No linked sleeve stop or exit rule in this public observation.',material:!!(e.exit_rule||setupFactorFinite(e.stop_price))}
 ];
 return values;
}
function setupFactorAttachPlan(row,read,plan,now=Date.now()){
 if(!read||!Array.isArray(read.factor_checks))return read;
 const planRows=setupFactorPlanChecks(row,plan,now),ids=new Map(SETUP_FACTOR_CATALOG.map((x,i)=>[i,x.id])),overrides=new Map(planRows.map(x=>[x.id,x]));
 const checks=read.factor_checks.map(item=>{
  if(!Array.isArray(item))return item;
  const raw=item[0],id=Number.isInteger(raw)?ids.get(raw):raw,updated=overrides.get(id);if(!updated)return item;
  const normalizedId=raw,detail=updated.status==='not_supplied'?undefined:String(updated.detail||'').replace(/\s+/g,' ').trim().slice(0,128);
  return [normalizedId,updated.status,...(detail?[detail]:[]),...(updated.material?[1]:[])];
 });
 const statuses=checks.map(x=>Array.isArray(x)?x[1]:null),factor_review={total:checks.length,measured:statuses.filter(x=>x==='measured').length,partial:statuses.filter(x=>x==='partial').length,stale:statuses.filter(x=>x==='stale').length,insufficient_history:statuses.filter(x=>x==='insufficient_history').length,insufficient_validation:statuses.filter(x=>x==='insufficient_validation').length,not_scanned:statuses.filter(x=>x==='not_scanned').length,not_supplied:statuses.filter(x=>x==='not_supplied').length,not_applicable:statuses.filter(x=>x==='not_applicable').length};
 return {...read,factor_checks:checks,factor_review};
}
function setupFactorChecks(row,snapshot,packet,analysisCache,now=Date.now()){
 const results=new Map(SETUP_FACTOR_CATALOG.map(x=>[x.id,{...x,status:'not_supplied',value:null,detail:'This input is not present in the current setup feed.',material:false}]));
 const set=(id,status,value,detail,material=false)=>{const f=results.get(id);if(f)results.set(id,{...f,status,value:value??null,detail:String(detail||''),material:!!material});};
 for(const id of SETUP_FACTOR_NO_VALIDATED_SCREEN)set(id,'insufficient_validation',null,'Rare long sequence; sources lack independent examples and stable thresholds. No inference or vote; triple tops are separate.');
 set('ipo_base','not_supplied',null,'No verified post-listing daily history is attached to this read, so an IPO-era base scan is unavailable.');
 set('market_profile_tpo','not_supplied',null,'Time-at-price TPO shape requires intraday price-time observations; daily OHLCV cannot recover that distribution.');
 set('zweig_thrust','not_supplied',null,'A Zweig breadth-thrust calculation requires a continuous advance/decline breadth series that is not in the current context packet.');
 set('trin_index','not_supplied',null,'TRIN requires advancing/declining issue counts and their volume; those underlying market-internal series are not supplied.');
 set('aaii_sentiment','not_supplied',null,'No current AAII survey observation is connected to the terminal feed.');
 set('naaim_exposure','not_supplied',null,'No current NAAIM exposure survey observation is connected to the terminal feed.');
 const terminal=snapshot?.terminal||{},relatedCharts=terminal.setup_observation?.charts?.series||[],seriesFor=(sym,interval)=>relatedCharts.find(c=>c.symbol===sym&&c.interval===interval),primaryDaily=row?.chart?.interval==='1d'?row.chart:seriesFor(row?.symbol,'1d'),supplementalDaily=setupFactorSupplementCurrent(row?.supplemental_history?.daily,primaryDaily,now,row?.symbol,'1d'),supplementalSpy=setupFactorSupplementCurrent(row?.supplemental_history?.benchmark,primaryDaily,now,'SPY','1d'),supplementalWeekly=setupFactorSupplementCurrent(row?.supplemental_history?.weekly,primaryDaily,now,row?.symbol,'1wk');
 let chart=row?.chart||null,tech=row?.technicals||{};
 const dailySource=seriesFor(row?.symbol,'1d')||(chart?.interval==='1d'?chart:null);
 if(dailySource&&chart?.interval!=='1d'){chart=dailySource;tech=setupFactorAnalyzeChart(chart,analysisCache,now)||{};}
 const lifetime=setupFactorLifetimeHistory(row?.supplemental_history?.lifetime,chart,now,row?.symbol);
 const m=tech.metrics||{},bars=chart?.bars||[],d=setupFactorMemoized(analysisCache,chart,'metrics',()=>setupFactorMetrics(chart)),close=setupFactorFinite(m.close)?m.close:d.closes.at(-1),atr=setupFactorFinite(m.atr14)?m.atr14:d.atr.at(-1),side=row?.direction==='bullish'?1:row?.direction==='bearish'?-1:0;
 const usable=packet?.context||{},market=terminal.market||{},e=(row?.evidence||[]).find(x=>x.id===row.primary_evidence_id)||(row?.evidence||[]).find(x=>x.active)||(row?.evidence||[])[0]||{};
  const chartOK=d.validBars&&bars.length>=20&&setupFactorFinite(close),precise=chart?.interval==='1d';
 const chartAnalysis=chartOK&&typeof explainChart==='function'?setupFactorAnalyzeChart(chart,analysisCache,now,true):tech;
   const ext=chartAnalysis?.extended||{},extReady=ext.formula_version==='ohlcv-extensions-1',unit=setupFactorIntervalWords(chart?.interval).unit,patternEvidence=precise?setupFactorMemoized(analysisCache,chart,'pattern-evidence',()=>setupFactorPatternEvidence(bars,chartAnalysis?.pivots||tech.pivots||[])):null;
   const usEquity=precise&&((row?.instrument?.currency==='USD'&&['EQUITY','ETF','ETP'].includes(String(row?.instrument?.instrument_type||'').toUpperCase()))||(chart?.source==='Alpaca SIP daily bars from the Lector refresh'&&chart?.adjustment==='split'&&/^[A-Z][A-Z0-9.]{0,7}$/.test(String(row?.symbol||''))));
   const expiry=usEquity?setupFactorMonthlyOptionsExpiry(chart?.as_of||chart?.last_completed_at):null;
   set('monthly_options_expiry',expiry?'measured':(row?.instrument?.currency&&row?.instrument.currency!=='USD')||(chart?.currency&&chart.currency!=='USD')?'not_applicable':'not_supplied',expiry,expiry?`US monthly equity-options calendar: standard expiry ${expiry.expiration_date}${expiry.holiday_adjusted?` (moved from Friday ${expiry.standard_friday} because of a market holiday)`:''}; ${expiry.in_expiry_week?'this is expiration week':'not expiration week'} as of ${expiry.as_of}. Calendar only; it does not establish options availability or positioning.`:(row?.instrument?.currency&&row?.instrument.currency!=='USD')||(chart?.currency&&chart.currency!=='USD')?'The instrument is not USD-denominated; the US monthly equity-options calendar does not apply.':'A verified USD equity/ETF instrument or the canonical split-adjusted Alpaca SIP equity feed and completed daily session are required to place this ticker in the US standard monthly-options calendar.',false);
  set('order_blocks','not_supplied',null,'OHLCV candles do not identify resting orders or institutional order blocks; the published setup feed has no order-book depth.',false);
 const calendarSession=(()=>{if(market.calendar_verified!==true)return null;const receipt=Date.parse(market.at||''),open=Date.parse(market.open||''),close=Date.parse(market.close||''),previous=Date.parse(market.previous_session_close||''),today=setupFactorSessionKey(new Date(now).toISOString()),openDay=setupFactorSessionKey(market.open),closeDay=setupFactorSessionKey(market.close),previousDay=setupFactorSessionKey(market.previous_session_close);return [receipt,open,close,previous].every(Number.isFinite)&&receipt<=now&&now-receipt<=300000&&previous<=now&&previous<open&&open<close&&today&&openDay===closeDay&&openDay>=today?previousDay:null;})();
 const timed=(value,maxAge=4*86400000)=>{const t=Date.parse(value||'');return Number.isFinite(t)&&t<=now&&(now-t<=maxAge||!!calendarSession&&setupFactorSessionKey(value)===calendarSession);};
  const setupNewsCoverage=market.setup_news_count_coverage,setupNewsSymbols=Array.isArray(setupNewsCoverage?.symbols)?setupNewsCoverage.symbols:[],useSetupNews=setupNewsCoverage?.source==='alpaca_news'&&setupNewsCoverage?.scope==='best_setups'&&setupNewsSymbols.includes(row?.symbol),newsCoverage=useSetupNews?setupNewsCoverage:market.news_count_coverage,newsRows=useSetupNews?market.setup_news_counts:market.news_counts,newsRow=Array.isArray(newsRows)?newsRows.find(x=>x?.symbol===row?.symbol):null;
  const newsStart=Date.parse(newsCoverage?.window_start||''),newsAsOf=Date.parse(newsCoverage?.as_of||''),newsReceived=Date.parse(newsCoverage?.received_at||''),newsWindowValid=Number.isFinite(newsStart)&&Number.isFinite(newsAsOf)&&newsStart<=newsAsOf&&Math.abs((newsAsOf-newsStart)-86400000)<=60000;
  const newsCoverageValid=newsCoverage?.source==='alpaca_news'&&newsCoverage?.window_hours===24&&newsWindowValid&&Number.isSafeInteger(newsCoverage.article_count)&&newsCoverage.article_count>=0&&Number.isSafeInteger(newsCoverage.page_count)&&newsCoverage.page_count>=1&&newsCoverage.page_count<=24&&(!useSetupNews||newsCoverage.symbols.includes(row?.symbol));
  const newsFresh=newsCoverageValid&&timed(newsCoverage.as_of,10*60000)&&timed(newsCoverage.received_at,10*60000),newsTickerCount=Number.isSafeInteger(newsRow?.count)&&newsRow.count>=0?newsRow.count:null;
  if(newsFresh&&newsCoverage.complete===true)set('news_counts','measured',{count:newsTickerCount??0,source:'alpaca_news',window_hours:24,as_of:newsCoverage.as_of,received_at:newsCoverage.received_at,feed_articles:newsCoverage.article_count,feed_pages:newsCoverage.page_count},`${newsTickerCount??0} distinct ${row.symbol} articles in Alpaca's fully paginated 24-hour feed${useSetupNews?' filtered to the Best Setups universe':''}; received ${newsCoverage.received_at}.`);
  else if(newsFresh&&newsTickerCount!==null)set('news_counts','partial',{count:newsTickerCount,source:'alpaca_news',window_hours:24,as_of:newsCoverage.as_of,received_at:newsCoverage.received_at,feed_articles:newsCoverage.article_count,feed_pages:newsCoverage.page_count},`At least ${newsTickerCount} distinct ${row.symbol} articles in Alpaca's 24-hour feed; pagination is incomplete after ${newsCoverage.page_count} pages.`);
  else if(newsCoverageValid&&!newsFresh)set('news_counts','stale',{count:newsTickerCount,source:'alpaca_news',window_hours:24,as_of:newsCoverage.as_of,received_at:newsCoverage.received_at},`Alpaca's last ticker-news count was received ${newsCoverage.received_at||'without a receipt time'} and is outside the 10-minute freshness window.`);
  else if(newsCoverageValid)set('news_counts','not_supplied',null,`Alpaca's 24-hour feed is incomplete after ${newsCoverage.page_count} pages; no ${row.symbol} count is inferred.`);
  else set('news_counts','not_supplied',null,'No valid timestamped Alpaca 24-hour ticker-news count is present in the published setup feed.');
 const byGroup=(group)=>SETUP_FACTOR_GROUPS.find(x=>x[0]===group)?.[1]||[];
 const notScanned=(id,reason)=>set(id,'not_scanned',null,reason);
 if(chartOK){
  const volumeReady=bars.every(b=>setupFactorFinite(b[5]));
  const gauge=(id,value,label,{min=1,status=null,material=false,precision=2,detail=null}={})=>{
   const ready=value!==null&&value!==undefined&&(typeof value!=='object'||Object.values(value).some(setupFactorFinite));
   const state=status||(ready?'measured':bars.length<min?'insufficient_history':volumeReady?'insufficient_history':'not_supplied');
   set(id,state,ready?value:null,detail||(ready?`${label}: ${typeof value==='number'?setupFactorFmt(value,precision):JSON.stringify(value)} from completed ${unit} bars.`:`Requires ${min} completed ${unit} bars${volumeReady?'':' with complete volume'}.`),ready&&material);
  };
  const x=extReady?ext:null;
  gauge('cci',x?.cci20,'CCI(20)',{min:20,material:Math.abs(x?.cci20||0)>=200,detail:setupFactorFinite(x?.cci20)?`CCI(20) ${setupFactorFmt(x.cci20)}; typical-price deviation divided by 0.015 × mean absolute deviation.`:null});
  gauge('williams_r',x?.williams_r14,'Williams %R(14)',{min:14,detail:setupFactorFinite(x?.williams_r14)?`Williams %R(14) ${setupFactorFmt(x.williams_r14)} on its −100 to 0 scale.`:null});
  gauge('stoch_rsi',setupFactorFinite(x?.stoch_rsi_k14)&&setupFactorFinite(x?.stoch_rsi_d3)?{k:x.stoch_rsi_k14,d:x.stoch_rsi_d3}:null,'Stochastic RSI',{min:28,detail:setupFactorFinite(x?.stoch_rsi_k14)&&setupFactorFinite(x?.stoch_rsi_d3)?`Stochastic RSI(14,14,3): %K ${setupFactorFmt(x.stoch_rsi_k14)}, %D ${setupFactorFmt(x.stoch_rsi_d3)}.`:null});
  const roc=x?.roc_horizons,rocCount=roc?Object.values(roc).filter(setupFactorFinite).length:0;set('roc_horizons',rocCount===4?'measured':rocCount?'partial':'insufficient_history',roc||null,rocCount?`Rate of change by completed ${unit} bars: ${Object.entries(roc).map(([p,v])=>`${p} ${setupFactorFinite(v)?setupFactorFmt(v)+'%':'warming'}`).join('; ')}.`:`Needs up to 126 prior completed ${unit} bars.`,false);
  gauge('aroon',x?.aroon_25,'Aroon(25)',{min:25,detail:setupFactorFinite(x?.aroon_25?.up)?`Aroon(25): up ${setupFactorFmt(x.aroon_25.up)}, down ${setupFactorFmt(x.aroon_25.down)}; most recent extreme wins ties.`:null});
  gauge('vortex',setupFactorFinite(x?.vortex_14?.plus)&&setupFactorFinite(x?.vortex_14?.minus)?x.vortex_14:null,'Vortex(14)',{min:15,detail:setupFactorFinite(x?.vortex_14?.plus)?`Vortex(14): +VI ${setupFactorFmt(x.vortex_14.plus,3)}, −VI ${setupFactorFmt(x.vortex_14.minus,3)}; summed movement divided by summed true range.`:null});
  gauge('trix',x?.trix_15,'TRIX(15)',{min:44,precision:4,detail:setupFactorFinite(x?.trix_15)?`TRIX(15) ${setupFactorFmt(x.trix_15,4)}%; one-bar percentage change in the triple EMA.`:null});
  gauge('coppock',x?.coppock_14_11_10,'Coppock curve(14,11,10)',{min:24,precision:3,detail:setupFactorFinite(x?.coppock_14_11_10)?`Coppock curve ${setupFactorFmt(x.coppock_14_11_10,3)} from a 10-bar weighted average of ROC(14)+ROC(11). This is calculated on the displayed ${unit} interval; the traditional convention is monthly.`:null});
  const hv=x?.historical_volatility,hvStatus=setupFactorFinite(hv?.percentile)?(hv.observations>=252?'measured':'partial'):'insufficient_history';set('historical_volatility_percentile',hvStatus,hv||null,setupFactorFinite(hv?.percentile)?`20-${unit} realized volatility ${setupFactorFmt(hv.annualized_20)}% annualized; percentile ${setupFactorFmt(hv.percentile,0)} across ${hv.observations} available completed-bar observations${hv.observations<252?' (short of a full 252-observation rank)':''}.`:`Needs a complete 20-bar return window to estimate realized volatility.`,false);
  gauge('elder_ray',setupFactorFinite(x?.elder_ray?.bull)&&setupFactorFinite(x?.elder_ray?.bear)?x.elder_ray:null,'Elder-Ray(13)',{min:13,detail:setupFactorFinite(x?.elder_ray?.bull)?`Elder-Ray(13): bull power ${setupFactorFmt(x.elder_ray.bull)}, bear power ${setupFactorFmt(x.elder_ray.bear)} versus EMA ${setupFactorFmt(x.elder_ray.ema13)}.`:null});
  gauge('mass_index',x?.mass_index_25,'Mass Index(25)',{min:42,detail:setupFactorFinite(x?.mass_index_25)?`Mass Index(25) ${setupFactorFmt(x.mass_index_25,3)}; 9-period EMA range ratio summed over 25 bars.`:null});
  const volumeGauges=[
   ['chaikin_money_flow',x?.chaikin_money_flow_20,'Chaikin Money Flow(20)',20,v=>setupFactorFinite(v)&&Math.abs(v)>=.1],
   ['chaikin_oscillator',x?.chaikin_oscillator_3_10,'Chaikin oscillator(3,10)',10,v=>false],
   ['elder_force_index',x?.elder_force_index_13,'Elder Force Index(13)',14,v=>false],
   ['ease_of_movement',x?.ease_of_movement_14,'Ease of Movement(14)',15,v=>false],
   ['klinger',x?.klinger_34_55,'Klinger(34,55)',67,v=>false]
  ];
  for(const [id,v,label,min,materialFn]of volumeGauges)gauge(id,volumeReady?v:null,label,{min,status:!volumeReady?'not_supplied':undefined,material:materialFn(v),detail:!volumeReady?`Complete volume is required for ${label}.`:setupFactorFinite(v)?`${label}: ${setupFactorFmt(v,4)}; OHLCV-derived volume measure, grouped with other participation evidence.`:null});
  gauge('vwma',volumeReady?x?.vwma20:null,'VWMA(20)',{min:20,status:!volumeReady?'not_supplied':undefined,detail:!volumeReady?'Complete volume is required for VWMA.':setupFactorFinite(x?.vwma20)?`VWMA(20) ${setupFactorFmt(x.vwma20)}; close × volume divided by volume.`:null});
  const udv=volumeReady?x?.up_down_volume_50:null;set('up_down_volume',setupFactorFinite(udv?.ratio)?'measured':udv?.down===0&&setupFactorFinite(udv?.up)?'partial':volumeReady?'insufficient_history':'not_supplied',udv||null,udv?.down===0?`Up volume ${setupFactorFmt(udv.up,0)}; no down volume in the 50-session window, so the ratio is undefined (not infinite).`:setupFactorFinite(udv?.ratio)?`Up/down volume ratio ${setupFactorFmt(udv.ratio,3)} over 50 completed ${unit} bars.`:`Needs 51 completed closes and complete volume for the 50-session directional-volume comparison.`,false);
  for(const [id,key,label]of [['nvi','nvi','Negative Volume Index'],['pvi','pvi','Positive Volume Index'],['pvt','pvt','Price Volume Trend']])gauge(id,volumeReady?x?.[key]:null,label,{min:2,status:!volumeReady?'not_supplied':undefined,detail:!volumeReady?`Complete volume is required for ${label}.`:setupFactorFinite(x?.[key])?`${label} cumulative index, initialized at 1,000 (NVI/PVI) or zero (PVT) over the supplied chart window.`:null});
  const overlay=(id,key,label,min=1,status=null,detailSuffix='')=>{const value=x?.[key],ready=value!==null&&value!==undefined;set(id,status||(ready?'measured':'insufficient_history'),ready?value:null,ready?`${label}: ${JSON.stringify(value)}.${detailSuffix}`:`Needs ${min} completed ${unit} bars${volumeReady?'':' and complete volume'}.`,false);};
  if(x?.ichimoku){for(const [id,key,label]of [['ichimoku_tenkan','tenkan','Tenkan(9)'],['ichimoku_kijun','kijun','Kijun(26)'],['ichimoku_cloud','senkou_b','Senkou B(52)']])set(id,'measured',x.ichimoku[key],`${label}: ${setupFactorFmt(x.ichimoku[key])}; cloud spans are projected 26 bars forward by convention.`,false);set('ichimoku_chikou','measured',{value:x.ichimoku.chikou_close,offset_bars:x.ichimoku.chikou_offset_bars},`Chikou reference is current close ${setupFactorFmt(x.ichimoku.chikou_close)} plotted 26 bars back; it is not a future observation.`,false);}
  else for(const id of ['ichimoku_tenkan','ichimoku_kijun','ichimoku_cloud','ichimoku_chikou'])set(id,'insufficient_history',null,'Ichimoku cloud needs 52 completed chart bars.',false);
  overlay('floor_pivots','floor_pivots','Prior-bar floor pivots',2,!precise?'not_applicable':null,' Derived only from the previous completed daily bar.');
  if(precise)overlay('prior_day_week_month_levels','prior_period_levels','Prior completed daily / weekly / monthly levels',2,null,' Calendar boundaries use the source bar date; incomplete periods are excluded.');else set('prior_day_week_month_levels','not_applicable',null,'Prior day/week/month levels require a daily chart with exchange-session boundaries.');
  overlay('parabolic_sar','parabolic_sar','Parabolic SAR',3,null,' Standard acceleration factor 0.02, step 0.02, maximum 0.20; seeded from first two bars.');
  overlay('supertrend','supertrend','Supertrend(10,3)',10,null,' Wilder ATR(10), multiplier 3.');overlay('keltner_channels','keltner','Keltner(EMA20 ± 2×ATR20)',20,null);
  overlay('donchian_20','donchian20','Prior 20-bar Donchian range',21,null,' Current bar is excluded from the breakout boundary.');overlay('donchian_55','donchian55','Prior 55-bar Donchian range',56,null,' Current bar is excluded from the breakout boundary.');overlay('chandelier_exit','chandelier_exit','Chandelier exit(22,3 ATR)',22,null);
  overlay('vwap_stdev_bands','vwap_stddev_bands','20-bar volume-weighted VWAP bands',20,!precise?'not_applicable':volumeReady?null:'not_supplied',' Weighted standard deviation of typical price; daily bars only.');
  overlay('ma_ribbon_gmma','ma_ribbon_gmma','EMA ribbon (3–15 and 30–60)',60,null,' Twelve EMA values; short and long groups are displayed together, not counted as independent votes.');
  const pitchfork=setupFactorAndrewsPitchfork(bars,tech.pivots||[]);set('andrews_pitchfork',!precise?'not_applicable':pitchfork?'measured':'insufficient_history',pitchfork,pitchfork?`Three confirmed alternating pivots set the pitchfork; median ${setupFactorFmt(pitchfork.median_now)}, upper/lower parallels ${setupFactorFmt(pitchfork.upper_now)} / ${setupFactorFmt(pitchfork.lower_now)}. Price is in the ${pitchfork.position.replaceAll('_',' ')}. The chart line is a structural reference, not a forecast.`:'Needs three confirmed alternating daily pivots to construct the median line and two parallels.',false);
   const sampleRange=x?.all_time_range_available;
   if(lifetime){
    const highs=lifetime.bars.map(b=>b[2]),lows=lifetime.bars.map(b=>b[3]),historyHigh=Math.max(...highs),historyLow=Math.min(...lows),basisValidation=lifetime.basis_validation||null,basisText=basisValidation?.mode==='cross_source_verified'?`Yahoo historical OHLCV was checked against split-adjusted Alpaca SIP on ${basisValidation.overlap_sessions} matched sessions (${setupFactorFmt(basisValidation.max_price_difference_pct,3)}% maximum OHLC difference; ${setupFactorFmt(basisValidation.max_volume_difference_pct,2)}% maximum volume difference).`:'Yahoo historical OHLCV price basis matches the current chart source.',rangeValue={high:historyHigh,low:historyLow,bars:lifetime.bars.length,available_from:lifetime.available_from,first_trade_date:lifetime.first_trade_date,complete_from_listing:!!lifetime.complete_from_listing,source:lifetime.source,basis_validation:basisValidation};
    set('all_time_high_low',lifetime.complete_from_listing?'measured':'partial',rangeValue,`${lifetime.complete_from_listing?'Full listing-history':'Bounded historical-window'} high / low ${setupFactorFmt(historyHigh)} / ${setupFactorFmt(historyLow)} across ${lifetime.bars.length} completed daily bars from ${lifetime.available_from}; ${lifetime.complete_from_listing?'coverage begins within 10 calendar days of provider listing date '+lifetime.first_trade_date:'provider history is bounded and is not claimed to be the instrument’s all-time range'}. ${basisText}`);
    const ipoVwap=setupFactorIpoAnchoredVwap(lifetime);set('anchored_vwap_ipo',ipoVwap?'measured':'not_supplied',ipoVwap?{...ipoVwap,basis_validation:basisValidation}:null,ipoVwap?`IPO-anchored typical-price VWAP ${setupFactorFmt(ipoVwap.value)} across ${ipoVwap.bars} completed daily bars from ${ipoVwap.anchor_at}; source OHLCV as supplied. ${basisText}`:lifetime.complete_from_listing?'The provider history is complete from listing, but IPO-anchored VWAP needs positive, complete volume across the full history.':'The available historical window starts after the provider listing date; an IPO-anchored VWAP is withheld.',false);
    if(lifetime.complete_from_listing&&lifetime.bars.length>=80){const ipoWindow=lifetime.bars.slice(0,Math.min(504,lifetime.bars.length)),bases=setupFactorHistoricalBases(ipoWindow),candidate=bases[0]||null,value={window_sessions:ipoWindow.length,window_start:String(ipoWindow[0][0]).slice(0,10),window_end:String(ipoWindow.at(-1)[0]).slice(0,10),first_confirmed_flat_base:candidate};set('ipo_base',candidate?'partial':'measured',value,candidate?`IPO-era flat-base screen found its first confirmed base ${candidate.start!=null?String(ipoWindow[candidate.start]?.[0]||'').slice(0,10):''}–${candidate.breakout_at}: ${candidate.length} sessions, ${setupFactorFmt(candidate.depth_pct,1)}% deep after a ${setupFactorFmt(candidate.prior_advance_pct,1)}% prior advance; scan covers the first ${ipoWindow.length} completed sessions after listing.`:`Scanned the first ${ipoWindow.length} completed sessions after provider listing for confirmed flat bases using the installed 25–90-session, <=15%-depth, >=30%-prior-advance and six-session breakout rules; none qualified.`);}
    else if(lifetime.complete_from_listing)set('ipo_base','insufficient_history',null,'Full listing history is verified, but fewer than 80 completed sessions are available for the installed IPO-era base screen.');
    else set('ipo_base','not_supplied',null,`The historical window begins ${lifetime.available_from}, after provider listing date ${lifetime.first_trade_date||'not supplied'}; an IPO-base result cannot be established.`);
    const seasonal=setupFactorSeasonality(lifetime.bars,lifetime.as_of);if(seasonal){const status=seasonal.status,ranked=seasonal.months.filter(x=>x.samples>=3).sort((a,b)=>(b.median??-Infinity)-(a.median??-Infinity)),best=ranked[0],weakest=ranked.at(-1),lastCompleteMonth=new Date(Date.parse(lifetime.as_of.slice(0,7)+'-01T00:00:00Z'));lastCompleteMonth.setUTCMonth(lastCompleteMonth.getUTCMonth()-1);set('seasonality',status,{...seasonal,basis_validation:basisValidation},`Completed monthly close-to-close returns through ${lastCompleteMonth.toISOString().slice(0,7)}; ${seasonal.observations} observations across 12 calendar months, minimum ${seasonal.minimum_samples} samples per month. ${best&&weakest?`Highest median month ${best.month} (${setupFactorFmt(best.median*100,1)}%, n=${best.samples}); lowest ${setupFactorFmt(weakest.median*100,1)}% (${weakest.month}, n=${weakest.samples}).`:''} Descriptive history; it is not a directional signal. ${basisText}`);}
   }else{
    set('all_time_high_low',sampleRange?'partial':'insufficient_history',sampleRange||null,sampleRange?`Highest / lowest within ${sampleRange.bars} supplied completed ${unit} bars: ${setupFactorFmt(sampleRange.high)} / ${setupFactorFmt(sampleRange.low)}. This bounded window is not claimed to be the instrument's all-time range.`:'No valid completed bars for a bounded high/low range.',false);
    if(row?.supplemental_history?.lifetime)set('anchored_vwap_ipo','not_supplied',null,'The extended history did not pass ticker, session, freshness or OHLC integrity checks; IPO-anchored VWAP is withheld.',false);
   }
  set('anchored_vwap_gap',x?.major_gap_anchored_vwap?'partial':'measured',x?.major_gap_anchored_vwap||null,x?.major_gap_anchored_vwap?`Typical-price VWAP from the most recent supplied opening gap of at least 0.5 prior ATR (${x.major_gap_anchored_vwap.anchor_at.slice(0,10)}): ${setupFactorFmt(x.major_gap_anchored_vwap.value)}. Gap anchor is a price-bar proxy, not an earnings anchor.`:'No opening gap of at least 0.5 prior ATR in the supplied bars; no gap anchor applies.',false);
  set('ytd_anchored_vwap',precise&&setupFactorFinite(x?.ytd_anchored_vwap)?'measured':!precise?'not_applicable':volumeReady?'insufficient_history':'not_supplied',precise?x?.ytd_anchored_vwap:null,precise&&setupFactorFinite(x?.ytd_anchored_vwap)?`Year-to-date typical-price VWAP: ${setupFactorFmt(x.ytd_anchored_vwap)} from supplied completed daily bars.`:!precise?'A daily chart is required for calendar-year VWAP.':'Year-to-date daily volume is incomplete or unavailable.',false);
  const averageCross=x?.golden_death_cross?.golden;set('golden_death_cross','measured',averageCross||null,averageCross?`50/200-${unit} average ${averageCross.direction} cross ${averageCross.bars_ago} completed bars ago.`:`No 50/200-${unit} average crossover in the supplied completed bars.`,false);
   const flat=patternEvidence?.flat_base,baseState=!precise?'not_applicable':!patternEvidence||bars.length<151?'insufficient_history':flat?'partial':'measured';
   set('flat_base',baseState,flat?{length:flat.length,depth_pct:flat.depth_pct,prior_advance_pct:flat.prior_advance_pct,pivot:flat.pivot,breakout:flat.breakout}:null,flat?`Flat-base screen: ${flat.length} completed sessions, ${setupFactorFmt(flat.depth_pct,1)}% deep after a ${setupFactorFmt(flat.prior_advance_pct,1)}% prior advance; pivot ${setupFactorFmt(flat.pivot)}${flat.breakout?' has a completed close above it':'; no close above the pivot yet'}. Thresholds: at least 25 sessions, no more than 15% deep, prior advance at least 30%.`:`No flat base met the stated duration, depth and prior-advance thresholds in ${bars.length} supplied daily bars; this does not rule out other base shapes.`,!!flat&&(flat.breakout||flat.depth_pct<=10));
   const range=patternEvidence?.range;set('base_depth',!precise?'not_applicable':range?'measured':'insufficient_history',precise?range:null,!precise?'Base depth is measured from daily bars only.':range?`Rolling ${range.bars}-session high-low range is ${setupFactorFmt(range.depth_pct,1)}% deep (${setupFactorFmt(range.low)}–${setupFactorFmt(range.high)}); a rolling range is not automatically a named base.`:'Needs at least 20 completed daily bars.');
   set('base_length',!precise?'not_applicable':flat?'partial':range?'measured':'insufficient_history',precise?(flat?{sessions:flat.length,base_start:String(bars[flat.start]?.[0]||'').slice(0,10)}:range?{candidate:null,scanned_sessions:range.bars}:null):null,!precise?'Base length is measured from daily bars only.':flat?`Latest qualified flat-base candidate spans ${flat.length} sessions from ${String(bars[flat.start]?.[0]||'').slice(0,10)}.`:range?`No qualifying flat base was found; the ${range.bars}-session rolling range is measured, but its pattern start is not assigned.`:'Needs enough completed daily history to scan a base.');
    const stackedBase=patternEvidence?.base_on_base;set('base_on_base',!precise?'not_applicable':bars.length<126?'insufficient_history':stackedBase?'partial':'measured',stackedBase,stackedBase?`Two shallow bases stack: the first pivot was ${setupFactorFmt(stackedBase.first_base.pivot)}, price advanced ${setupFactorFmt(stackedBase.intervening_advance_pct,1)}% before the upper base formed, and the later base held within ${setupFactorFmt(stackedBase.upper_base_support_vs_prior_pivot_pct,1)}% of the first pivot. Current upper-base pivot ${setupFactorFmt(stackedBase.upper_base.pivot)}; breakout is not confirmed.`:`No completed base followed by a shallow upper base holding within 5% of its first pivot was found in ${bars.length} supplied daily bars.`,false);
    const baseStage=patternEvidence?.base_stage;set('base_stage',!precise?'not_applicable':!baseStage?'insufficient_history':'partial',baseStage,baseStage?`${baseStage.completed_base_breakouts} distinct confirmed flat-base breakouts in ${baseStage.window_sessions} supplied sessions; stage lower bound ${baseStage.stage_lower_bound}${baseStage.forming_base?`; current base is forming from ${baseStage.forming_base.start}`:''}. The count uses a completed 20% advance to separate stages.`:'Needs 126 completed daily bars to measure a rolling base sequence.',false);
   const dry=patternEvidence?.dryup;set('volume_dry_up',!precise?'not_applicable':!patternEvidence?'insufficient_history':!patternEvidence.volume_available?'not_supplied':!flat?'not_applicable':dry?'partial':'insufficient_history',dry,!precise?'In-base volume dry-up requires daily bars.':dry?`Within the flat-base candidate, final-10-session average volume is ${setupFactorFmt(dry.last10_vs_prior10,2)}× the previous 10 and ${setupFactorFmt(dry.last10_vs_prior50,2)}× the preceding 50-session reference; ${dry.qualifies?'volume contracted at least 20% against both references':'the two-reference 20% contraction test is not met'}.`:!patternEvidence?'Needs a completed daily chart.':!patternEvidence.volume_available?'Complete volume is unavailable.':!flat?'No qualifying flat base is present to test for in-base volume dry-up.':'Not enough complete in-base and pre-base volume windows.',!!dry?.qualifies);
   const tight=patternEvidence?.three_weeks_tight;set('three_weeks_tight',!precise?'not_applicable':!tight?'insufficient_history':tight.qualifies?'partial':'measured',tight,`Last three five-session close points span ${setupFactorFmt(tight?.range_pct,2)}%; the screening threshold is 1.5% or less. This is a mechanical candidate screen, not an annotated base.`,!!tight?.qualifies);
   const pivotTight=patternEvidence?.pivot_tightness;set('pivot_tightness',!precise?'not_applicable':!pivotTight?'insufficient_history':pivotTight.qualifies?'partial':'measured',pivotTight,pivotTight?`Last 10 closes span ${setupFactorFmt(pivotTight.close_range_pct,2)}%; the latest close is ${setupFactorFmt(pivotTight.distance_below_pivot_pct,2)}% below the preceding 20-session high ${setupFactorFmt(pivotTight.pivot)}. Candidate requires a <=2.5% range and a close within 2% below that level.`:'Needs at least 30 completed daily bars.',!!pivotTight?.qualifies);
    const vcp=patternEvidence?.vcp,turnCount=(tech.pivots||[]).filter(p=>p.index>=Math.max(0,bars.length-126)).length,vcpPivot=vcp?.contractions?.at(-1)?.high,vcpBreak=setupFactorFinite(vcpPivot)&&close>vcpPivot,vcpStatus=!precise?'not_applicable':!vcp||turnCount<6?'insufficient_history':vcp.qualifies?'partial':'measured';set('vcp',vcpStatus,vcp?.qualifies?{contractions:vcp.contractions.map(x=>x.depth),pivot:vcpPivot,confirmed_break:vcpBreak}:null,vcpStatus==='insufficient_history'?'Needs three successive confirmed high-to-low contractions in the latest 126 daily bars.':vcp?.qualifies?`Three confirmed pullbacks contract in sequence: ${vcp.contractions.map(x=>setupFactorFmt(x.depth*100,1)+'%').join(' → ')}. Pivot ${setupFactorFinite(vcpPivot)?setupFactorFmt(vcpPivot):'unavailable'}; latest close ${vcpBreak?'cleared the pivot':'has not cleared the pivot'}. This is a VCP screening proxy; volume confirmation is separate.`:'No three successively shallower confirmed pullbacks appear in the latest 126 daily bars.',!!vcpBreak);
   const trap=patternEvidence?.failed_break;for(const [id,kind]of [['bull_trap','bull_trap'],['bear_trap','bear_trap']]){const found=trap?.kind===kind;set(id,!precise?'not_applicable':bars.length<40?'insufficient_history':found?'partial':'measured',found?trap:null,found?`${kind==='bull_trap'?'Upside':'Downside'} 20-session range break failed within ${trap.bars_to_failure} completed sessions at ${setupFactorFmt(trap.level)} (${trap.break_at} → ${trap.failure_at}).`:`No failed 20-session ${kind==='bull_trap'?'upside':'downside'} close break followed by a return through the level within five sessions in the latest 35 bars.`,found);}
   const runup=patternEvidence?.runup_pct,runReady=precise&&bars.length>=100&&setupFactorFinite(runup);set('climax_run',!precise?'not_applicable':!runReady?'insufficient_history':runup>=50?'partial':'measured',runReady?{runup_pct:runup}:null,runReady?`Price advanced ${setupFactorFmt(runup,1)}% from the lowest low near the start of the prior 18-week window to six sessions ago${runup>=50?'; extended-run candidate, not a reversal call':''}.`:'Needs at least 100 completed daily bars.',runReady&&runup>=50);
   const climax=patternEvidence?.climax_top;set('climax_top',!precise?'not_applicable':!runReady?'insufficient_history':climax?'partial':'measured',climax,climax?`Climax-like top candidate on ${climax.date}: prior 18-week run ${setupFactorFmt(climax.runup_pct,1)}%, volume ${setupFactorFmt(climax.relative_volume,2)}× its 20-session mean, wide red candle closing in its lower 35%. Candidate only; a top requires later structure failure.`:'No high-volume, wide-range exhaustion bar met the 18-week-run screen in the latest six sessions.',!!climax);
   const selling=patternEvidence?.selling_climax;set('selling_climax',!precise?'not_applicable':!patternEvidence?.volume_available?'not_supplied':bars.length<30?'insufficient_history':selling?'partial':'measured',selling,selling?`Selling-climax candidate on ${selling.date}: fresh 20-session low, volume ${setupFactorFmt(selling.relative_volume,2)}× its 20-session mean, wide range and close in the upper 35% of the bar. A reversal requires later confirmation.`:'No recent high-volume 20-session low with a wide intraday reversal candle met the screen.',!!selling);
   const pivotReady=(tech.pivots||[]).filter(p=>p.confirmation_index<bars.length).length>=6,patternScreen=(id,value,minimum,description,requiresPivots=false,material=false)=>{const status=!precise?'not_applicable':bars.length<minimum||requiresPivots&&!pivotReady?'insufficient_history':value?'partial':'measured';set(id,status,value||null,value?description:'Scanned '+bars.length+' completed daily bars; no '+id.replaceAll('_',' ')+' candidate met the installed screen.',material);};
   const tower=precise?setupFactorTowerPattern(bars):null;patternScreen('tower_tops',tower,35,tower?`${tower.kind.replaceAll('_',' ')} geometry: prior ${setupFactorFmt(tower.prior_advance_pct??tower.prior_decline_pct,1)}% move, compact pause ${setupFactorFmt(tower.cap_low)}–${setupFactorFmt(tower.cap_high)}, and a completed close through the pause on ${tower.break_at}.`:'',false,!!tower?.confirmed);
   const scallop=precise?setupFactorScallop(bars,tech.pivots||[]):null,scallopPivots=(tech.pivots||[]).filter(p=>p.confirmation_index<bars.length).length,scallopMove=scallop?.direction==='bearish'?'decline':'advance';set('scallop_pattern',!precise?'not_applicable':bars.length<40||scallopPivots<3?'insufficient_history':scallop?'partial':'measured',scallop,scallop?`${scallop.kind.replaceAll('_',' ')} screen: ${setupFactorFmt(scallop.prior_move_pct,1)}% prior ${scallopMove} with ${setupFactorFmt(scallop.retracement_pct,1)}% retracement from ${setupFactorFmt(scallop.start_level)} through ${setupFactorFmt(scallop.turn_level)} to ${setupFactorFmt(scallop.retrace_level)}; ${scallop.confirmed?`completed close confirmed the ${scallop.direction} break on ${scallop.break_at}.`:'the turn level has not been crossed on a completed close.'}`:`Scanned ${bars.length} completed daily bars and ${scallopPivots} confirmed pivots; no 10% A-B-C scallop with a 20–80% retracement and retained third turn met the installed screen.`,!!scallop?.confirmed);
  const rightTop=patternEvidence?.right_angled_broadening_top,rightBottom=patternEvidence?.right_angled_broadening_bottom,ascending=patternEvidence?.ascending_base;
   patternScreen('right_angled_broadening_top',rightTop,40,rightTop?'Right-angled broadening-top candidate: three rising confirmed highs ('+setupFactorFmt(rightTop.divergence_pct,1)+'%) against three lows within '+setupFactorFmt(rightTop.flat_range_pct,1)+'%. '+(rightTop.confirmed_break?'The latest completed close broke above the upper pivots.':'No completed close above the upper pivots yet.')+' Geometry is a screen, not an annotated pattern.':'',true,!!rightTop?.confirmed_break);
   patternScreen('right_angled_broadening_bottom',rightBottom,40,rightBottom?'Right-angled broadening-bottom candidate: three falling confirmed lows ('+setupFactorFmt(rightBottom.divergence_pct,1)+'%) against three highs within '+setupFactorFmt(rightBottom.flat_range_pct,1)+'%. '+(rightBottom.confirmed_break?'The latest completed close broke below the lower pivots.':'No completed close below the lower pivots yet.')+' Geometry is a screen, not an annotated pattern.':'',true,!!rightBottom?.confirmed_break);
   patternScreen('ascending_base',ascending,40,ascending?'Ascending-base candidate: three confirmed lows rise '+setupFactorFmt(ascending.higher_lows_pct,1)+'% while three highs stay within '+setupFactorFmt(ascending.resistance_range_pct,1)+'%. '+(ascending.confirmed_break?'The latest completed close cleared the upper pivots.':'Breakout confirmation is separate.'):'',true,!!ascending?.confirmed_break);
   const diamonds=patternEvidence?.diamonds||{};for(const [id,value]of [['diamond_top',diamonds.top],['diamond_bottom',diamonds.bottom]])patternScreen(id,value,50,value?`${id==='diamond_top'?'Diamond-top':'Diamond-bottom'} geometry: the middle swing range expanded at least 15% beyond both outer ranges, then the confirmed highs and lows contracted. ${value.start_at}–${value.end_at}; ${value.confirmed_break?`latest close broke the projected boundary at ${setupFactorFmt(value.lower_boundary_now??value.upper_boundary_now)}.`:'the projected boundary has not broken.'}`:'',true,!!value?.confirmed_break);
   for(const [id,value,label]of [['v_top',patternEvidence?.v_top,'V-top'],['v_bottom',patternEvidence?.v_bottom,'V-bottom']])patternScreen(id,value,30,value?label+' reversal candidate at '+(value.peak_at||value.trough_at)+': '+setupFactorFmt(value.prior_rise_pct??value.prior_decline_pct,1)+'% prior move followed by '+setupFactorFmt(value.decline_pct??value.rebound_pct,1)+'% reversal. Shape screen only; confirmation is separate.':'',false,false);
  const deadCat=patternEvidence?.dead_cat_bounce;patternScreen('dead_cat_bounce',deadCat,25,deadCat?'Dead-cat-bounce candidate: '+setupFactorFmt(deadCat.retracement_pct,1)+'% rebound of the decline; '+(deadCat.state==='downside_break_confirmed'?'price closed below the rebound low':'the rebound low has not broken on a completed close')+'.':'',false,deadCat?.state==='downside_break_confirmed');
   const island=patternEvidence?.island_reversal;patternScreen('island_reversal',island,25,island?island.kind.replaceAll('_',' ')+' candidate from '+island.start_at+' to '+island.end_at+'; '+island.bars_inside+' bar(s) isolated by opposite-direction gaps.':'',false,false);
   const rounding=patternEvidence?.rounding_bottom;patternScreen('rounding_bottom',rounding,40,rounding?'Rounding-bottom recovery candidate across '+rounding.bars+' sessions; middle closes averaged below both outer thirds, trough '+rounding.trough_at+', followed by at least 5% recovery.':'',false,false);
  const highTight=patternEvidence?.high_tight_flag;patternScreen('high_tight_flag',highTight,30,highTight?'High-tight-flag candidate: '+setupFactorFmt(highTight.advance_pct,1)+'% rise in '+highTight.run_bars+' bars, then '+setupFactorFmt(highTight.flag_depth_pct,1)+'% pullback across '+highTight.flag_bars+' bars on '+setupFactorFmt(highTight.flag_volume_vs_run,2)+'× run volume. Pivot '+setupFactorFmt(highTight.pivot)+'; state '+highTight.state+'.':'',false,!!highTight&&highTight.state==='pivot_broken');
   const bumpRun=patternEvidence?.bump_run_reversal;patternScreen('bump_run_reversal',bumpRun,45,bumpRun?`Bump-and-run geometry screen: ${bumpRun.lead_sessions}-session rising lead-in, ${bumpRun.bump_sessions}-session accelerated bump, and peak extension ${setupFactorFmt(bumpRun.excess_multiple,1)}× the largest lead-in extension. ${bumpRun.downside_break_confirmed?`The close broke projected lead-in support on ${bumpRun.break_at} and remains below ${setupFactorFmt(bumpRun.lead_line_at_current)}.`:bumpRun.current_below_support?'Price is below projected lead-in support; the exact break sequence needs review.':`Projected support at ${setupFactorFmt(bumpRun.lead_line_at_current)} has not broken on a completed close.`} Bump/lead volume ratio ${setupFactorFmt(bumpRun.volume_expansion,2)}×. Mechanical geometry screen; not a discretionary pattern label.`:'Scanned completed daily bars for a rising lead-in, faster bump, at least 2× vertical excess and a later support break; no candidate met all geometry conditions.',false,!!bumpRun?.downside_break_confirmed&&bumpRun.volume_expansion>=1.2);
  const fvg=x?.fair_value_gaps;set('fair_value_gaps',Array.isArray(fvg)?'measured':'insufficient_history',fvg||null,Array.isArray(fvg)?fvg.length?fvg.slice(-6).map(z=>`${z.direction} imbalance ${setupFactorFmt(z.low)}–${setupFactorFmt(z.high)} formed ${z.formed_at.slice(0,10)}; still unfilled in observed bars`).join('; '):'No unfilled three-candle OHLC imbalance remains in the supplied completed bars.':'Needs at least three completed bars.',false);
  const sweep=x?.liquidity_sweeps;set('liquidity_sweeps',sweep?'measured':'insufficient_history',sweep||null,sweep?`Prior 20-bar liquidity test: ${sweep.bullish_sweep?'bullish sweep below '+setupFactorFmt(sweep.prior_low)+' then close above':sweep.bearish_sweep?'bearish sweep above '+setupFactorFmt(sweep.prior_high)+' then close below':'no latest-bar sweep of the prior 20-bar extreme'}. A wick/close proxy cannot identify resting orders.`:'Needs 21 completed bars.',!!(sweep?.bullish_sweep||sweep?.bearish_sweep));
  const nr4=x?.nr4,nr7=x?.nr7;set('nr4_compression',typeof nr4==='boolean'?'measured':'insufficient_history',nr4,typeof nr4==='boolean'?`Latest completed range ${nr4?'is':'is not'} the narrowest of four bars${nr4?' (ties included)':''}.`:'Four completed bars are required.',false);set('nr7_compression',typeof nr7==='boolean'?'measured':'insufficient_history',nr7,typeof nr7==='boolean'?`Latest completed range ${nr7?'is':'is not'} the narrowest of seven bars${nr7?' (ties included)':''}.`:'Seven completed bars are required.',false);
  set('heikin_ashi',x?.heikin_ashi?'measured':'insufficient_history',x?.heikin_ashi||null,x?.heikin_ashi?`Heikin-Ashi derived candle: ${x.heikin_ashi.direction}, O ${setupFactorFmt(x.heikin_ashi.open)}, H ${setupFactorFmt(x.heikin_ashi.high)}, L ${setupFactorFmt(x.heikin_ashi.low)}, C ${setupFactorFmt(x.heikin_ashi.close)}.`:'At least one complete OHLC bar is required.',false);
  const td=x?.td_setup;set('td_sequential',td?'partial':'insufficient_history',td||null,td?`Close-vs-four-bars-back setup count: ${td.buy_count} consecutive downside-comparison bars and ${td.sell_count} upside-comparison bars; counts stop at nine. Setup counts only; TD countdown rules are not included.`:'Five completed bars are required.',false);
  for(const [id,key,n]of [['sma10','sma10',10],['sma20','sma20',20],['sma50','sma50',50],['sma200','sma200',200]]){
   const v=setupFactorSma(d.closes,n).at(-1);set(id,!precise?'not_applicable':v===null?'insufficient_history':'measured',precise?v:null,!precise?`Daily bars are not supplied for this setup; an intraday/weekly average is not labeled as a day average.`:v===null?`Needs ${n} completed daily bars; ${bars.length} supplied.`:`Price is ${close>v?'above':close<v?'below':'at'} the ${n}-day simple average (${setupFactorFmt(v)}).`,precise&&v!==null&&Math.abs((close-v)/(atr||1))>=2);
  }
  set('rsi',setupFactorFinite(m.rsi14)?'measured':'insufficient_history',m.rsi14,setupFactorFinite(m.rsi14)?`RSI(14) ${setupFactorFmt(m.rsi14)}.`:'Fourteen completed price changes are required.',setupFactorFinite(m.rsi14)&&(m.rsi14>=70||m.rsi14<=30));
  for(const [id,key,series,label]of [['macd_line','macd',d.macdLine,'MACD line'],['macd_signal','macd_signal',d.macdSignal,'MACD signal'],['macd_histogram','macd_histogram',d.hist,'MACD histogram']]){const v=setupFactorFinite(m[key])?m[key]:series.at(-1);set(id,setupFactorFinite(v)?'measured':'insufficient_history',v,setupFactorFinite(v)?`${label}: ${setupFactorFmt(v,4)}.`:`${label} is still warming up.`);}
  const cross=d.hist.length>=2&&setupFactorFinite(d.hist.at(-1))&&setupFactorFinite(d.hist.at(-2))&&(d.hist.at(-1)===0||Math.sign(d.hist.at(-1))!==Math.sign(d.hist.at(-2)));
  set('macd_crossovers',d.hist.length>=2?'measured':'insufficient_history',cross?d.hist.at(-1)>0?'bullish MACD/signal crossover':'bearish MACD/signal crossover':'No latest-bar MACD/signal crossover',cross?'The MACD line crossed its signal line on the latest completed bar.':'No MACD/signal crossover on the latest completed bar.',cross);
  const sk=d.stoch.slow.at(-1),sd=d.stoch.signal.at(-1);set('slow_stochastic',setupFactorFinite(sk)&&setupFactorFinite(sd)?'measured':'insufficient_history',setupFactorFinite(sk)?{slow_k:sk,slow_d:sd}:null,setupFactorFinite(sk)&&setupFactorFinite(sd)?`Slow %K ${setupFactorFmt(sk)}, %D ${setupFactorFmt(sd)}.`:'Needs 18 completed bars. ',setupFactorFinite(sk)&&(sk>=80||sk<=20));
  const adx=d.adx.at(-1),pdi=d.pdi.at(-1),mdi=d.mdi.at(-1);set('adx_dmi',setupFactorFinite(adx)?'measured':'insufficient_history',setupFactorFinite(adx)?{adx,pdi,mdi}:null,setupFactorFinite(adx)?`ADX ${setupFactorFmt(adx)}; +DI ${setupFactorFmt(pdi)}, −DI ${setupFactorFmt(mdi)}. ADX measures strength, DMI direction.`:'Needs enough completed bars to seed Wilder ADX.',setupFactorFinite(adx)&&adx>=25);
  for(const [id,v,label]of [['relative_volume',setupFactorFinite(m.relative_volume)?m.relative_volume:d.relvol,'Volume versus the preceding 20 bars'],['breakout_volume',d.relvol,'Participation on the latest bar']])set(id,setupFactorFinite(v)?'measured':'insufficient_history',v,setupFactorFinite(v)?`${setupFactorFmt(v)}× the preceding 20-bar average volume.`:'A complete 20-bar volume baseline is unavailable.',setupFactorFinite(v)&&v>=1.5);
  const r126=d.returns(126);set('six_month_momentum',!precise?'not_applicable':setupFactorFinite(r126)?'measured':'insufficient_history',precise?r126:null,!precise?'Six-month momentum is measured from daily bars; this setup has no daily series.':setupFactorFinite(r126)?`${(r126*100).toFixed(2)}% over 126 completed daily bars.`:`Needs 126 prior completed daily bars; ${bars.length} supplied.`,precise&&setupFactorFinite(r126)&&Math.abs(r126)>=.25);
  set('vwap20',precise&&setupFactorFinite(d.vwap20)?'measured':!precise?'not_applicable':'insufficient_history',d.vwap20,precise&&setupFactorFinite(d.vwap20)?`20 completed daily bars, typical price (H+L+C)/3 × volume: ${setupFactorFmt(d.vwap20)}.`:!precise?'This chart is not daily.':'Twenty complete daily OHLCV bars are required.',precise&&setupFactorFinite(d.vwap20)&&atr>0&&Math.abs((close-d.vwap20)/atr)>=1.5);
  const intervalWords=setupFactorIntervalWords(chart?.interval),bband=d.bb.at(-1),priorWidths=d.bb.slice(-120).map(x=>x.width).filter(setupFactorFinite),bbRank=bband&&setupFactorFinite(bband.width)&&priorWidths.length>=20?100*priorWidths.filter(x=>x<=bband.width).length/priorWidths.length:null;
  const bbDetail=bbRank===null?'Needs at least 20 completed 20-'+intervalWords.unit+' Bollinger-width observations.':`Current 20-${intervalWords.unit}, 2σ band width is at the ${setupFactorFmt(bbRank,0)}th percentile of ${priorWidths.length} observed ${intervalWords.label} widths`+(bbRank<=10?' (squeeze range)':'')+'.';
  set('bollinger_squeeze',bbRank===null?'insufficient_history':'measured',bbRank,bbDetail,bbRank!==null&&bbRank<=10);
  if(bars.length>=20&&setupFactorFinite(atr)){
   const highs20=bars.slice(-21,-1).map(b=>b[2]),lows20=bars.slice(-21,-1).map(b=>b[3]),priorHigh=highs20.length?Math.max(...highs20):null,priorLow=lows20.length?Math.min(...lows20):null;
   const state=close>priorHigh?'breakout':close<priorLow?'breakdown':'inside 20-bar range',over=state==='breakout'||state==='breakdown',distanceAtr=over?Math.abs(close-(state==='breakout'?priorHigh:priorLow))/atr:null,quality=over?`${state}; ${d.relvol>=1.5?'volume confirms':'volume is below 1.5×'}; ${distanceAtr>2?'extended >2 ATR beyond level':'not >2 ATR beyond level'}`:'No close beyond the prior 20-bar range.';
   set('breakout_quality','measured',{state,prior_high:priorHigh,prior_low:priorLow,relative_volume:d.relvol,distance_atr:distanceAtr},quality,over);
   const highs=bars.map(b=>b[2]),lows=bars.map(b=>b[3]),roundStep=close<20?1:close<100?5:close<500?10:50,round=Math.round(close/roundStep)*roundStep;
    const profile=precise?setupFactorDailyVolumeProfile(bars):null;
    if(profile){const detail=`Approximate 60-session volume concentration from daily OHLCV: POC ${setupFactorFmt(profile.poc)}, 70% area ${setupFactorFmt(profile.value_area_low)}–${setupFactorFmt(profile.value_area_high)}. Each session's volume is assigned to its HLC/3 price bin; this is not trade-level volume-at-price.`;for(const [id,key,label]of [['volume_poc','poc','POC'],['value_area_low','value_area_low','value-area low'],['value_area_high','value_area_high','value-area high']])set(id,'partial',profile[key],`${label}: ${setupFactorFmt(profile[key])}. ${detail}`);}
    else for(const id of ['value_area_high','value_area_low','volume_poc'])set(id,bars.length<20?'insufficient_history':'not_supplied',null,bars.length<20?'Needs at least 20 complete daily OHLCV sessions.':'A valid daily OHLCV volume-concentration proxy could not be computed.');
    const candidates=[...((tech.levels||[]).map(x=>({name:x.label,price:x.price}))),...['sma20','sma50','sma200'].map(k=>({name:k.toUpperCase(),price:m[k]})),...(profile?[{name:'Daily-bar POC · proxy',price:profile.poc},{name:'Daily-bar VAH · proxy',price:profile.value_area_high},{name:'Daily-bar VAL · proxy',price:profile.value_area_low}]:[]),{name:'round number',price:round}].filter(x=>setupFactorFinite(x.price));
   const threshold=Math.max(atr*.25,close*.001);const clusters=[];for(const c of candidates){let cluster=clusters.find(g=>Math.abs(g.center-c.price)<=threshold);if(!cluster){cluster={center:c.price,items:[]};clusters.push(cluster);}cluster.items.push(c);cluster.center=setupFactorMean(cluster.items.map(x=>x.price));}
    const best=clusters.sort((a,b)=>b.items.length-a.items.length)[0],levelDetail=best?`${best.items.length} levels cluster near ${setupFactorFmt(best.center)} (within 0.25 ATR): ${best.items.map(x=>x.name).join(', ')}.`:'No measured level set to compare.';set('level_confluence',best?.items.length?(profile?'partial':'measured'):'insufficient_history',best?{count:best.items.length,center:best.center,levels:best.items.map(x=>x.name),volume_profile_proxy:!!profile}:null,best?`${levelDetail}${profile?' Includes daily-bar volume-concentration estimates, not trade-level volume-at-price.':' Volume-profile data is unavailable.'}`:levelDetail,best?.items.length>=3);
    const zoneLevels=candidates.map(x=>`${x.name} ${setupFactorFmt(x.price)}`);set('support_resistance_zones','partial',zoneLevels.join('; '),`Swing, moving-average and round-number levels checked${profile?`; approximate daily-bar volume concentration: POC ${setupFactorFmt(profile.poc)}, VAL ${setupFactorFmt(profile.value_area_low)}, VAH ${setupFactorFmt(profile.value_area_high)} (60 sessions, typical-price bins; not trade-level volume-at-price)`:'. No volume-profile source or usable proxy is available'}.`);
   const retest=(period)=>{const avg=setupFactorSma(d.closes,period),from=Math.max(1,bars.length-10);for(let i=bars.length-1;i>=from;i--){const tolerance=.25*(d.atr[i]||atr),previous=bars[i-1][4],level=avg[i],priorLevel=avg[i-1];if(!setupFactorFinite(level)||!setupFactorFinite(priorLevel)||bars[i][3]>level+tolerance||bars[i][2]<level-tolerance)continue;const state=previous<priorLevel&&bars[i][4]>=level?'reclaimed':previous>priorLevel&&bars[i][4]>=level?'retest_held':previous>priorLevel&&bars[i][4]<level?'lost_on_retest':previous<priorLevel&&bars[i][4]<level?'rejected_below':'touch';return {index:i,state,date:bars[i][0],level,previous_close:previous,close:bars[i][4]};}return null;};
   if(precise){
    const r20=retest(20),r50=retest(50),retestText=x=>x?`${x.state.replaceAll('_',' ')} ${x.date.slice(0,10)} at ${setupFactorFmt(x.level)}`:'no qualifying touch in the last 10 bars';
    set('average_retests','measured',{sma20:r20,sma50:r50},`Last 10 daily bars: 20-day ${retestText(r20)}; 50-day ${retestText(r50)}. A touch is not an order trigger.`,!!(r20&&['lost_on_retest','rejected_below'].includes(r20.state)||r50&&['lost_on_retest','rejected_below'].includes(r50.state)));
    }else set('average_retests','not_applicable',null,'A matched daily series is required to assess the requested 20-day and 50-day average retests; this chart uses '+setupFactorIntervalWords(chart?.interval).label+' bars.');
   set('structure_integrity',m.structure_breach?'measured':m.structure?'measured':'insufficient_history',m.structure_breach||m.structure||null,m.structure_breach?`Swing structure broken (${m.structure_breach}); the latest completed close crossed its confirmed pivot level.`:m.structure?`The confirmed swing sequence is ${String(m.structure).replaceAll('_',' ')}; no opposing swing-structure break is confirmed.`:'Not enough confirmed pivots.',m.structure_breach==='bullish_failed'||m.structure_breach==='bearish_failed');
   const swing=(tech.pivots||[]).filter(p=>p.confirmation_index<bars.length).slice(-10).map(p=>`${p.kind==='support'?'low':'high'} ${setupFactorFmt(p.price)} · ${p.pivot_at?.slice(0,10)||'date unavailable'} (confirmed ${p.confirmed_at?.slice(0,10)||'clock unavailable'})`);
   set('confirmed_swings',swing.length?'measured':'insufficient_history',swing,swing.length?swing.join('; '):'Needs confirmed two-left / two-right swing pivots.');
   const lines=tech.lines||[];set('support_resistance_trendlines',lines.length?'measured':'insufficient_history',lines.map(x=>({kind:x.kind,state:x.state,start:x.start_price,end:x.end_price})),lines.length?lines.map(x=>`${x.kind} line ${x.state}; projected level ${setupFactorFmt(x.end_price)}.`).join(' '):'Not enough confirmed swing pairs to draw a tested trendline.',lines.some(x=>x.state==='broken'));
   const lastPivot=(tech.pivots||[]).filter(p=>p.confirmation_index<bars.length).at(-1);let swingVwap=null;if(lastPivot&&precise){const from=lastPivot.index,tail=bars.slice(from),den=tail.every(b=>setupFactorFinite(b[5]))?tail.reduce((a,b)=>a+b[5],0):0;swingVwap=den>0?tail.reduce((a,b)=>a+(b[2]+b[3]+b[4])/3*b[5],0)/den:null;}set('anchored_vwap_swing',swingVwap===null?'insufficient_history':'measured',swingVwap,swingVwap===null?'A confirmed swing anchor and complete daily volume are required.':`Typical-price VWAP since the last confirmed swing (${lastPivot.pivot_at.slice(0,10)}): ${setupFactorFmt(swingVwap)}.`);
   const gaps=[];for(let i=Math.max(1,bars.length-60);i<bars.length;i++){const p=bars[i-1],b=bars[i];if(b[3]>p[2])gaps.push({direction:'up',low:p[2],high:b[3],date:b[0],index:i});else if(b[2]<p[3])gaps.push({direction:'down',low:b[2],high:p[3],date:b[0],index:i});}
   const openGap=bars.length>1?(bars.at(-1)[1]>bars.at(-2)[4]?{direction:'up',pct:100*(bars.at(-1)[1]/bars.at(-2)[4]-1)}:bars.at(-1)[1]<bars.at(-2)[4]?{direction:'down',pct:100*(bars.at(-1)[1]/bars.at(-2)[4]-1)}:null):null;
   const unfilled=gaps.flatMap(g=>{const after=bars.slice(g.index+1);if(!after.length)return[];const lowest=Math.min(...after.map(x=>x[3])),highest=Math.max(...after.map(x=>x[2]));if(g.direction==='up'){if(lowest<=g.low)return[];return[{...g,remaining_low:g.low,remaining_high:Math.min(g.high,lowest),fill_state:lowest<g.high?'partially filled':'unfilled'}];}if(highest>=g.high)return[];return[{...g,remaining_low:Math.max(g.low,highest),remaining_high:g.high,fill_state:highest>g.low?'partially filled':'unfilled'}];});
   set('gap_direction',bars.length>1?'measured':'insufficient_history',openGap,openGap?`Latest open gapped ${openGap.direction} ${setupFactorFmt(Math.abs(openGap.pct))}% versus prior close.`:'No open gap versus prior close on the latest bar.');
   set('unfilled_gaps','measured',unfilled,unfilled.length?unfilled.slice(-8).map(x=>`${x.direction} remaining ${setupFactorFmt(x.remaining_low)}–${setupFactorFmt(x.remaining_high)} from ${x.date.slice(0,10)} (${x.fill_state})`).join('; '):'No remaining gap zones found in the last 60 supplied bars; all detected gaps were filled within the observed bars.');
   const gapTaxonomy=setupFactorGapTaxonomy(bars),gapTypes=gapTaxonomy?.filter(g=>g.kind!=='unclassified')||[];set('gap_taxonomy',gapTaxonomy?.length?'partial':'measured',gapTaxonomy||[],gapTypes.length?gapTypes.slice(-6).map(g=>g.direction+' '+g.kind+' gap candidate '+setupFactorFmt(g.gap_atr)+' ATR on '+g.date+'; '+setupFactorFmt(g.relative_volume)+'× prior volume').join('; ')+' Candidate classification only; full confirmation may require later price behavior.':gapTaxonomy?.length?'Gaps were detected but none met the contextual screens for breakaway, runaway, exhaustion or common; candidate classes are withheld.':'Scanned the last 60 completed bars; no full-range gap remains to classify.',false);
   const candle=m.candle||{},candleLevels=[...(tech.levels||[]).filter(x=>x.kind===(candle.engulfing==='bullish'?'support':'resistance')).map(x=>({name:x.label||'confirmed swing level',price:x.price})),...['sma20','sma50','sma200'].map(k=>({name:k.toUpperCase(),price:m[k]})),{name:'round number',price:Math.round(close/(close<20?1:close<100?5:close<500?10:50))*(close<20?1:close<100?5:close<500?10:50)}].filter(x=>setupFactorFinite(x.price)),candleLevel=candleLevels.sort((a,b)=>Math.abs(a.price-close)-Math.abs(b.price-close))[0]||null,candleNear=!!(candle.engulfing&&candleLevel&&atr>0&&Math.abs(close-candleLevel.price)<=.5*atr),candleRead=candle.engulfing?`${candle.engulfing} engulfing${candleLevel?` · nearest ${candleLevel.name} ${setupFactorFmt(candleLevel.price)} (${setupFactorFmt(Math.abs(close-candleLevel.price)/atr)} ATR away)`:''}`:candle.direction||null;set('candlestick_detectors','partial',candleRead,`Candle range, close location and engulfing are measured. ${candleNear?'The engulfing pattern is within 0.5 ATR of a measured key-level reference.':'No engulfing pattern is close enough to a measured key level to highlight.'} The full 50-pattern detector set is not installed; no absence claim is made for unimplemented patterns.`,candleNear);
   const effort=d.relvol!==null&&setupFactorFinite(candle.close_location)?{relative_volume:d.relvol,close_location:candle.close_location}:null;set('effort_result',effort?'partial':'insufficient_history',effort,effort?'Latest-bar volume effort and closing-range result are measured; separate phase and level-sweep screens are reported below.':'Needs complete volume and candle-range data.');
   const observedWeekly=seriesFor(row.symbol,'1wk'),weeklyCandidates=[observedWeekly,supplementalWeekly,chart?.interval==='1wk'?chart:null].filter(Boolean),wyckoffWeekly=weeklyCandidates.find(source=>Array.isArray(source.bars)&&source.bars.length>=60&&setupFactorSourceCurrent(source,now))||null,wyckoffWeeklyTech=wyckoffWeekly?setupFactorAnalyzeChart(wyckoffWeekly,analysisCache,now):null;
   const dailyWyckoffCurrent=precise&&setupFactorSourceCurrent(chart,now),wyckoffDaily=dailyWyckoffCurrent?setupFactorWyckoffEvidence(bars,tech.pivots||[]):null,wyckoffWeek=wyckoffWeekly?setupFactorWyckoffEvidence(wyckoffWeekly.bars,wyckoffWeeklyTech?.pivots||[]):null,wyckoffFrames={daily:wyckoffDaily?.phase?{current:true,as_of:chart.last_completed_at||chart.as_of||null,phase:wyckoffDaily.phase,events:wyckoffDaily.events,volume_available:wyckoffDaily.volume_available}:null,weekly:wyckoffWeek?.phase?{current:true,as_of:wyckoffWeekly.last_completed_at||wyckoffWeekly.as_of||null,phase:wyckoffWeek.phase,events:wyckoffWeek.events,volume_available:wyckoffWeek.volume_available}:null},availableWyckoff=[['daily',wyckoffDaily],['weekly',wyckoffWeek]].filter(([,x])=>x?.phase),wyckoffPhase=availableWyckoff.length?{frames:wyckoffFrames,current_intervals:availableWyckoff.map(([frame])=>frame),method:'Daily and weekly completed-bar proxies; phase labels are mechanical context, not discretionary Wyckoff annotations.'}:null;
   const hasWyckoffFrame=precise||chart?.interval==='1wk'||weeklyCandidates.length>0,wyckoffSourceStale=hasWyckoffFrame&&((precise&&!dailyWyckoffCurrent)||weeklyCandidates.some(source=>Array.isArray(source.bars)&&source.bars.length>=60&&!setupFactorSourceCurrent(source,now))),dailyWyckoffNote=!precise?'daily chart unavailable':!dailyWyckoffCurrent?'daily chart stale':bars.length<60?'daily history shorter than 60 bars':null,weeklyWyckoffNote=!weeklyCandidates.length?'weekly chart unavailable':!wyckoffWeekly?weeklyCandidates.some(source=>Array.isArray(source.bars)&&source.bars.length>=60)?'weekly chart stale':'weekly history shorter than 60 bars':null;
   const wyckoffPhaseText=availableWyckoff.length?availableWyckoff.map(([frame,x])=>`${frame}: ${x.phase.label.replaceAll('_',' ')}; 20-bar trend ${setupFactorFmt(x.phase.trend_pct,1)}%, preceding 40-bar move ${setupFactorFmt(x.phase.prior_40_bar_move_pct,1)}%, 20-bar range ${setupFactorFmt(x.phase.base_width_20_bar_pct,1)}% of mean price; close at ${setupFactorFmt(x.phase.position_in_range_pct,0)}% of 40-bar range`).join('; ')+[dailyWyckoffNote,weeklyWyckoffNote].filter(Boolean).map(x=>' · '+x).join(''):wyckoffSourceStale?'The daily/weekly OHLCV source is stale; retained measurements are not current.':hasWyckoffFrame?'Needs at least 60 completed daily or weekly OHLC bars.':'No daily or weekly chart is attached to this read.';
   set('wyckoff_phase',wyckoffPhase?'partial':wyckoffSourceStale?'stale':hasWyckoffFrame?'insufficient_history':'not_applicable',wyckoffPhase,wyckoffPhaseText,false);
   const wyckoffEvents=availableWyckoff.flatMap(([frame,x])=>x.events.map(e=>({...e,interval:frame}))).sort((a,b)=>b.confirmed_at.localeCompare(a.confirmed_at)),wyckoffEventText=wyckoffEvents.length?wyckoffEvents.map(e=>`${e.interval} ${e.kind.replaceAll('_',' ')} at ${setupFactorFmt(e.level)}: probe ${e.probe_at}, reclaimed ${e.confirmed_at} (${e.bars_to_reclaim} bars); volume ${setupFactorFinite(e.volume_ratio)?setupFactorFmt(e.volume_ratio,2)+'×':'unavailable'}, current state ${e.current_state.replaceAll('_',' ')}.`).join(' '):availableWyckoff.length?'No confirmed swing-level sweep followed by a completed-close reclaim within five bars in the latest 20 daily/weekly bars.':'Needs 60 completed daily or weekly bars with confirmed swing pivots.';
   set('wyckoff_events',availableWyckoff.length?(wyckoffEvents.length?'partial':'measured'):wyckoffSourceStale?'stale':hasWyckoffFrame?'insufficient_history':'not_applicable',availableWyckoff.length?{frames:wyckoffFrames,current_intervals:availableWyckoff.map(([frame])=>frame),events:wyckoffEvents,method:'Completed OHLCV and confirmed pivots only; a sweep must reclaim its level on a completed close within five bars.'}:null,wyckoffEventText,wyckoffEvents.some(e=>e.current_state==='reclaim_held'&&e.volume_supported));
    const patternAnalysis=chartOK&&typeof explainChart==='function'?setupFactorAnalyzeChart(seriesFor(row.symbol,'1d')||chart,analysisCache,now):tech,patternRows=patternAnalysis?.patterns||[],detectors=patternAnalysis?.pattern_scan?.detectors||{},patternIds=['head_shoulders','inverse_head_shoulders','double_top','double_bottom','triple_top','ascending_triangle','descending_triangle','symmetrical_triangle','rising_wedge','falling_wedge','expanding_wedge','bull_flag','bear_flag','bull_pennant','bear_pennant','cup_handle','inverted_cup_handle','rectangle','rising_channel','falling_channel'];
    for(const id of patternIds){const detector=detectors[id],alias=id==='symmetrical_triangle'?'converging_range':id,found=patternRows.filter(p=>p.kind===id||p.kind===alias),ready=detector?.status==='measured',material=found.some(p=>p.state==='confirmed_break');set(id,ready?'measured':chartOK?'insufficient_history':'not_scanned',found,ready?(found.length?found.map(p=>p.description).join(' '):`Scanned ${bars.length} completed bars and ${patternAnalysis?.pivots?.length||0} confirmed pivots; no qualifying ${id.replaceAll('_',' ')} geometry met the installed thresholds.`):`Needs ${detector?.minimum_bars||'a valid completed'} bars for this pattern detector.`,material);}
   const targets=tech.elliott?.preferred?.targets||[],pivots=(tech.pivots||[]).filter(p=>Number.isInteger(p.index)&&Number.isFinite(p.price)),alternating=[];for(const pivot of pivots){if(!alternating.length||pivot.kind!==alternating.at(-1).kind)alternating.push(pivot);else alternating[alternating.length-1]=pivot;}
   const abc=alternating.slice(-3),swingTargets=[];if(abc.length===3){const [a,b,c]=abc,move=b.price-a.price;if(Math.sign(move)&&c.kind===a.kind){swingTargets.push({label:'AB=CD scenario',price:c.price+move});swingTargets.push({label:'1.272 extension',price:c.price+move*1.272});swingTargets.push({label:'1.618 extension',price:c.price+move*1.618});}}
    const currentClose=setupFactorFinite(patternAnalysis?.metrics?.close)?patternAnalysis.metrics.close:setupFactorFinite(tech.metrics?.close)?tech.metrics.close:null;
    const patternTargets=(patternRows||[]).flatMap(p=>{if(p.state!=='confirmed_break')return[];const price=setupFactorFinite(p.measured_target_price)?p.measured_target_price:setupFactorFinite(p.neckline)&&setupFactorFinite(p.invalidation_level)?p.neckline+(p.neckline-p.invalidation_level):null;if(!setupFactorFinite(price)||p.measured_target_status==='reached')return[];const ahead=currentClose===null||p.direction==='up'&&price>currentClose||p.direction==='down'&&price<currentClose;if(!ahead)return[];return [{label:`${p.kind} measured move`,price}];}),allTargets=[...patternTargets,...swingTargets,...targets.filter(x=>Number.isFinite(x.price)).map(x=>({label:x.label||'Elliott scenario',price:x.price}))];
   set('measured_targets',allTargets.length?'partial':'insufficient_history',allTargets,allTargets.length?`Measured scenario levels: ${allTargets.map(x=>`${x.label} ${setupFactorFmt(x.price)}`).join('; ')}. These are chart projections, not the sleeve's order plan.`:'No complete confirmed pattern or alternating A-B-C swing supports a measured target; extensions are withheld.',allTargets.length>0);
   const lifetimeChart=lifetime?{symbol:lifetime.symbol,interval:'1d',source:lifetime.source,adjustment:lifetime.adjustment,basis_validation:lifetime.basis_validation,as_of:lifetime.as_of,last_completed_at:lifetime.last_completed_at,input_status:lifetime.input_status,bars:lifetime.bars}:null;
   const rangeChart=precise&&bars.length>=252?chart:supplementalDaily?.bars?.length>=252?supplementalDaily:lifetimeChart?.bars?.length>=252?lifetimeChart:null,rangeBars=rangeChart?.bars||[],rangeClose=rangeBars.at(-1)?.[4];
   if(rangeBars.length>=252&&setupFactorFinite(rangeClose)){
    const yr=rangeBars.slice(-252),hi=Math.max(...yr.map(b=>b[2])),lo=Math.min(...yr.map(b=>b[3])),giveback=hi>lo?(hi-rangeClose)/(hi-lo):null,band=giveback===null?'unknown':giveback<.382?'less than 38.2%':giveback<.5?'38.2–50%':giveback<.618?'50–61.8%':giveback<=1?'more than 61.8%':'price outside the measured range',fib=[.382,.5,.618].map(r=>({ratio:r,price:hi-(hi-lo)*r})),nearest=fib.sort((a,b)=>Math.abs(a.price-rangeClose)-Math.abs(b.price-rangeClose))[0],ma200=setupFactorMean(rangeBars.slice(-200).map(b=>b[4])),rangeAtr=setupFactorMemoized(analysisCache,rangeChart,'metrics',()=>setupFactorMetrics(rangeChart)).atr.at(-1),ma200Near=setupFactorFinite(ma200)&&fib.some(x=>Math.abs(x.price-ma200)<=.5*(rangeAtr||0)),crossSourceChecked=rangeChart===lifetimeChart&&lifetime?.basis_validation?.mode==='cross_source_verified',basis=rangeChart===chart?'desk chart':crossSourceChecked?'Yahoo lifetime history, cross-vendor checked against split-adjusted Alpaca SIP':setupFactorSamePriceBasis(chart,rangeChart)?'same-source extended Yahoo Finance history':'separate Yahoo Finance historical context';
    const comparableToChart=setupFactorSamePriceBasis(chart,rangeChart)||crossSourceChecked,basisMeta={source:rangeChart.source||null,price_basis:crossSourceChecked?'Yahoo unadjusted quote OHLC; overlap checked against split-adjusted Alpaca SIP':comparableToChart?'Yahoo unadjusted quote OHLC':rangeChart.adjustment||null,as_of:rangeChart.as_of||null,comparable_to_chart:comparableToChart,basis_validation:crossSourceChecked?lifetime.basis_validation:null};
    set('one_year_fibonacci','measured',{high:hi,low:lo,giveback,band,nearest_fib:nearest,ma200_confluence:ma200Near,...basisMeta},`252-session swing ${setupFactorFmt(lo)}–${setupFactorFmt(hi)}; giveback ${(giveback*100).toFixed(1)}% (${band}); nearest retracement ${setupFactorFmt(nearest.ratio*100,1)}% at ${setupFactorFmt(nearest.price)}; 200-day average ${setupFactorFinite(ma200)?setupFactorFmt(ma200):'warming'}${ma200Near?' is within 0.5 ATR of a retracement shelf':'.'} Source: ${basis}; its own OHLC is used without splicing into the desk chart.`,setupFactorFinite(giveback)&&giveback>=.382&&giveback<=.618||ma200Near);
    set('fifty_two_week_range','measured',{high:hi,low:lo,...basisMeta},`Highest high ${setupFactorFmt(hi)} and lowest low ${setupFactorFmt(lo)} across 252 completed daily sessions. Source: ${basis}; separate from the desk chart.`);
   }else{const n=bars.length;set('one_year_fibonacci','insufficient_history',null,`Requires 252 completed daily sessions; the desk chart has ${n} ${chart?.interval||''} bars and no current matched long-history supplement.`);set('fifty_two_week_range','insufficient_history',null,`Requires 252 completed daily sessions; the desk chart has ${n} bars and no current matched long-history supplement.`);}
   const recentStart=Math.max(20,bars.length-60);let breakoutRetest=null;for(let i=recentStart;i<bars.length-1;i++){const prior=bars.slice(i-20,i),b=bars[i],hi=Math.max(...prior.map(x=>x[2])),lo=Math.min(...prior.map(x=>x[3])),atrAt=d.atr[i]||atr;if(!(atrAt>0))continue;const direction=b[4]>hi+.1*atrAt?'up':b[4]<lo-.1*atrAt?'down':null;if(!direction)continue;const level=direction==='up'?hi:lo;for(let j=i+1;j<Math.min(bars.length,i+11);j++){const retest=bars[j],touch=retest[3]<=level+.25*atrAt&&retest[2]>=level-.25*atrAt;if(!touch)continue;const held=direction==='up'?retest[4]>=level:retest[4]<=level;breakoutRetest={direction,state:held?'retest_held':'failed_retest',level,breakout_at:b[0],retest_at:retest[0],close:retest[4]};}}
   const retestCurrentClose=breakoutRetest?bars.at(-1)?.[4]:null,retestCurrentRelation=breakoutRetest&&setupFactorFinite(retestCurrentClose)?(retestCurrentClose>=breakoutRetest.level?'above':'below'):null;
   const retestOutcome=breakoutRetest?(breakoutRetest.direction==='up'
    ?breakoutRetest.state==='retest_held'?'held above the breakout level on the completed close.':'closed below the breakout level; the upside break failed.'
    :breakoutRetest.state==='retest_held'?'held below the breakdown level on the completed close.':'closed above the breakdown level; the downside break failed.'):null;
   set('breakout_retest',bars.length>=40?'measured':'insufficient_history',breakoutRetest,breakoutRetest?`${breakoutRetest.direction==='up'?'Upside':'Downside'} breakout at ${breakoutRetest.breakout_at.slice(0,10)}; later test of ${setupFactorFmt(breakoutRetest.level)} on ${breakoutRetest.retest_at.slice(0,10)} ${retestOutcome} Latest completed close is ${setupFactorFmt(retestCurrentClose)}, ${retestCurrentRelation} ${setupFactorFmt(breakoutRetest.level)}.`:bars.length>=40?'No completed 20-bar range break followed by a level touch within ten bars in the last 60 observations.':'Needs more completed bars.',!!breakoutRetest);
   // Indicators that are fully computable from completed daily OHLCV.
   const obvNow=d.obv.at(-1),obvThen=d.obv.at(-21),adNow=d.ad.at(-1),adThen=d.ad.at(-21),mfiNow=d.mfi.at(-1);set('obv',setupFactorFinite(obvNow)&&setupFactorFinite(obvThen)?'measured':'insufficient_history',setupFactorFinite(obvNow)?{value:obvNow,change20:obvNow-obvThen}:null,setupFactorFinite(obvNow)&&setupFactorFinite(obvThen)?`OBV ${setupFactorFmt(obvNow,0)}; 20-bar change ${setupFactorFmt(obvNow-obvThen,0)}.`:'Requires 21 complete volume observations.');set('accumulation_distribution',setupFactorFinite(adNow)&&setupFactorFinite(adThen)?'measured':'insufficient_history',setupFactorFinite(adNow)?{value:adNow,change20:adNow-adThen}:null,setupFactorFinite(adNow)&&setupFactorFinite(adThen)?`A/D line 20-bar change ${setupFactorFmt(adNow-adThen,0)}.`:'Requires 21 complete OHLCV observations.');set('mfi',setupFactorFinite(mfiNow)?'measured':'insufficient_history',mfiNow,setupFactorFinite(mfiNow)?`MFI(14) ${setupFactorFmt(mfiNow)}.`:'Requires 14 complete typical-price and volume changes.',setupFactorFinite(mfiNow)&&(mfiNow>=80||mfiNow<=20));
   const intervalWords=setupFactorIntervalWords(chart?.interval),avg50=setupFactorSma(d.closes,50).at(-1),lastTime=Date.parse(bars.at(-1)?.[0]||''),yearStart=lastTime-365.25*86400000,atrRows=d.atr.map((value,index)=>({value,time:Date.parse(bars[index]?.[0]||'')})).filter(x=>setupFactorFinite(x.value)&&Number.isFinite(x.time)&&x.time<=lastTime&&x.time>=yearStart),atrPctile=atrRows.map(x=>x.value),coverageDays=bars.length&&Number.isFinite(lastTime)?Math.max(0,(lastTime-Date.parse(bars[0][0]))/86400000):0,fullYear=bars.length>0&&Number.isFinite(lastTime)&&Number.isFinite(Date.parse(bars[0][0]))&&Date.parse(bars[0][0])<=yearStart;
   const extension=setupFactorFinite(avg50)&&atr>0?(close-avg50)/atr:null,atrRank=atrPctile.length>=40&&setupFactorFinite(atr)?100*atrPctile.filter(x=>x<=atr).length/atrPctile.length:null,rankStatus=atrRank===null?'insufficient_history':fullYear?'measured':'partial',rankDetail=atrRank===null?`Needs 40 valid ATR observations in the trailing 365 days; ${atrPctile.length} available.`:fullYear?`Current ATR ranks at the ${setupFactorFmt(atrRank,0)}th percentile of ${atrPctile.length} completed ${intervalWords.label} ATR observations in the trailing 365 calendar days.`:`Current ATR ranks at the ${setupFactorFmt(atrRank,0)}th percentile of ${atrPctile.length} completed ${intervalWords.label} ATR observations; the available chart spans ${setupFactorFmt(coverageDays,0)} calendar days, so this is not a full-year rank.`;
   set('atr_stretch',setupFactorFinite(atr)?'measured':'insufficient_history',setupFactorFinite(atr)?{atr,atr_percent:atr/close*100,from_sma50_atr:extension}:null,setupFactorFinite(atr)?`ATR(14-${intervalWords.unit}) ${setupFactorFmt(atr)} (${setupFactorFmt(atr/close*100)}% of price); ${setupFactorFinite(extension)?setupFactorFmt(extension)+' ATR from the 50-'+intervalWords.unit+' average':'50-'+intervalWords.unit+' extension unavailable'}.`:'ATR needs 14 completed bars.',setupFactorFinite(extension)&&Math.abs(extension)>=2);
   set('extension_rank',rankStatus,atrRank,rankDetail);
   const ret20=d.returns(20);set('breakout_volume',setupFactorFinite(d.relvol)?'measured':'insufficient_history',d.relvol,setupFactorFinite(d.relvol)?`${setupFactorFmt(d.relvol)}× usual 20-bar volume${ret20!==null?`; price return ${setupFactorFmt(ret20*100)}% over the last 20 bars`:''}.`:'No complete relative-volume baseline.',setupFactorFinite(d.relvol)&&d.relvol>=1.5&&ret20!==null&&Math.abs(ret20)>=.05);
   const earnings=(market.earnings||[]).filter(x=>(x.symbol||x.sym)===row.symbol&&x.actual_occurrence_source&&timed(x.announcement_at,365*86400000)&&timed(x.first_published_at,365*86400000)&&timed(x.signal_available_at,365*86400000)).sort((a,b)=>Date.parse(b.signal_available_at)-Date.parse(a.signal_available_at))[0];if(earnings&&precise){const availableAt=Date.parse(earnings.signal_available_at),index=Number.isFinite(availableAt)?bars.findIndex(b=>Date.parse(b[0])>=availableAt):-1,tail=index>=0?bars.slice(index):[],den=tail.every(b=>setupFactorFinite(b[5]))?tail.reduce((a,b)=>a+b[5],0):0,v=den>0?tail.reduce((a,b)=>a+(b[2]+b[3]+b[4])/3*b[5],0)/den:null;set('anchored_vwap_earnings',v===null?'insufficient_history':'measured',v,v===null?'A causal earnings occurrence exists, but no complete daily bar begins after its recorded availability.':`Typical-price VWAP since the latest reported earnings became available (${earnings.signal_available_at}): ${setupFactorFmt(v)}.`);}else set('anchored_vwap_earnings','not_supplied',null,'No causal, symbol-specific earnings occurrence with a precise availability time is available for this chart.');
   const pgeEvents=(market.earnings||[]).filter(e=>(e.symbol||e.sym)===row.symbol),pgeCausalEvent=pgeEvents.some(e=>e?.actual_occurrence_source&&[e.announcement_at,e.first_published_at,e.signal_available_at].every(x=>{const t=Date.parse(x||'');return Number.isFinite(t)&&t<=now;})),pge=setupFactorPowerEarningsGap(bars,pgeEvents,now),pgeCandidate=pge&&['forming_price_volume_candidate','held_price_volume_candidate'].includes(pge.state),pgeStatus=!precise?'not_applicable':pge?.state==='insufficient_data'?'insufficient_history':pge?(pge.state==='not_qualified'?'measured':'partial'):pgeCausalEvent?'insufficient_history':'not_supplied';set('power_earnings_gap',pgeStatus,pge,pge?pge.gap_pct>=5?'Earnings-gap screen: '+setupFactorFmt(pge.gap_pct,1)+'% gap, '+setupFactorFmt(pge.relative_volume,2)+'× preceding 50-session volume, '+(pge.above_prior_20_high?'above':'not above')+' the prior 20-session high, '+pge.hold_bars+' post-gap closes; '+pge.state.replaceAll('_',' ')+'. EPS surprise is not supplied.': 'An actual earnings event is time-linked to the price series, but the gap/volume screen is not met.':'No usable causal earnings event/session-open pair with sufficient preceding daily history is available.',!!pgeCandidate&&pge.held);
    const rvBars=bars.slice(-21),rvReturns=rvBars.slice(1).map((b,i)=>Math.log(b[4]/rvBars[i][4])),rvMean=setupFactorMean(rvReturns),rvVariance=rvReturns.length>1?rvReturns.reduce((sum,x)=>sum+(x-rvMean)**2,0)/(rvReturns.length-1):null,realized=rvBars.length===21&&rvReturns.every(Number.isFinite)&&setupFactorFinite(rvVariance)?Math.sqrt(rvVariance*252):null,iv=(market.option_iv||[]).find(x=>(x.underlying||x.symbol)===row.symbol&&setupFactorFinite(x.iv)&&timed(x.market_at,30*60000));set('iv_realized',setupFactorFinite(realized)?'partial':iv?'not_supplied':'insufficient_history',setupFactorFinite(realized)?{implied:iv?.iv??null,realized,realized_observations:rvReturns.length,annualization_factor:252,implied_source:iv?.source??null,implied_market_at:iv?.market_at??null}:null,setupFactorFinite(realized)?`Realized volatility ${setupFactorFmt(realized*100,1)}% annualized from 20 completed daily log returns. ${iv?`Current IV ${setupFactorFmt(iv.iv*100,1)}% from ${iv.mode==='model_reference'?'indicative/model reference':'observed reference'} at ${iv.market_at}.`:'The matching current implied-volatility observation is not supplied, so the comparison is incomplete.'}`:'Needs 21 completed daily closes for a 20-return realized-volatility estimate.');
   set('name_options',iv?'partial':'not_supplied',iv?{iv:iv.iv,source:iv.source,mode:iv.mode,market_at:iv.market_at}:null,iv?`IV ${setupFactorFmt(iv.iv*100)}%; ${iv.mode==='model_reference'?'indicative/model reference':'observed reference'}, not a complete positioning read.`:'No current name-level option IV observation.');set('iv_rank','not_supplied',null,'A timestamped one-year implied-volatility series is not supplied.');
  }else{
   for(const id of ['sma10','sma20','sma50','sma200','rsi','macd_line','macd_signal','macd_histogram','macd_crossovers','slow_stochastic','adx_dmi','relative_volume','breakout_volume','six_month_momentum','vwap20','bollinger_squeeze','breakout_quality','level_confluence','support_resistance_zones','average_retests','structure_integrity','confirmed_swings','support_resistance_trendlines','anchored_vwap_swing','gap_direction','unfilled_gaps','gap_taxonomy','candlestick_detectors','effort_result','double_bottom','symmetrical_triangle','measured_targets','one_year_fibonacci','fifty_two_week_range','breakout_retest','obv','accumulation_distribution','mfi','extension_rank','iv_realized','name_options','iv_rank','anchored_vwap_earnings'])set(id,'insufficient_history',null,'A valid completed OHLCV chart with a usable price is required.');
   for(const id of ['head_shoulders','inverse_head_shoulders','double_top','triple_top','ascending_triangle','descending_triangle','rising_wedge','falling_wedge','expanding_wedge','bull_flag','bear_flag','bull_pennant','bear_pennant','cup_handle','inverted_cup_handle','rectangle','rising_channel','falling_channel'])notScanned(id,'The chart input is unavailable; no pattern absence is inferred.');
  }
  const available=row?.ranker;set('momentum_rank',setupFactorFinite(available?.momentum)?'measured':setupFactorFinite(available?.opp)?'partial':'not_supplied',available?.momentum??available?.opp??null,setupFactorFinite(available?.momentum)?`ChartsLector momentum component ${setupFactorFmt(available.momentum)}/100; ranks the configured 55-name universe.`:setupFactorFinite(available?.opp)?`ChartsLector composite ${setupFactorFmt(available.opp)}/100; component momentum rank not separately supplied.`:'No cross-sectional momentum row.');
    const spy=seriesFor('SPY','1d'),spyCurrent=setupFactorSourceCurrent(spy,now),aligned=setupFactorAlignedReturns(bars,spy?.bars,126),stockLast=setupFactorSessionKey(bars.at(-1)?.[0]),spyLast=setupFactorSessionKey(spy?.bars?.at(-1)?.[0]);
   const primaryAligned=spy&&spyCurrent&&!aligned?.stale&&stockLast===spyLast&&(aligned?.excess!==undefined||aligned?.invalid===true)?aligned:null;
   const supplementalAligned=supplementalDaily&&supplementalSpy?setupFactorAlignedReturns(supplementalDaily.bars,supplementalSpy.bars,126):null;
    const samePrimaryContract=!!(chart?.source&&spy?.source&&chart.source===spy.source&&chart.adjustment&&chart.adjustment===spy.adjustment),primaryBeta=primaryAligned&&!primaryAligned.invalid&&samePrimaryContract?setupFactorMarketBeta(bars,spy.bars,126):null,supplementalBeta=supplementalAligned&&!supplementalAligned.stale&&!supplementalAligned.invalid?setupFactorMarketBeta(supplementalDaily.bars,supplementalSpy.bars,126):null;
    const betaResult=primaryBeta&&!primaryBeta.stale&&!primaryBeta.invalid?{...primaryBeta,source:'desk chart pair'}:supplementalBeta&&!supplementalBeta.stale&&!supplementalBeta.invalid?{...supplementalBeta,source:'Yahoo Finance matched historical pair'}:null;
    if(row.symbol==='SPY')set('beta_market_correlation','not_applicable',null,'SPY is the benchmark itself; market beta and correlation to itself are not useful exposure measures.');
    else if(betaResult)set('beta_market_correlation','measured',betaResult,`Beta ${setupFactorFmt(betaResult.beta,2)} and correlation ${setupFactorFmt(betaResult.correlation,2)} from ${betaResult.return_intervals} matched daily return intervals through ${betaResult.session} (${betaResult.source}). Describes historical market sensitivity, not direction.`);
    else if(primaryBeta?.stale||supplementalBeta?.stale||spy&&!spyCurrent)set('beta_market_correlation','stale',null,'The stock and benchmark do not share a fresh matched daily close; no current beta or correlation is inferred.');
    else if(primaryAligned?.invalid||supplementalAligned?.invalid)set('beta_market_correlation','insufficient_history',null,'Matched closes have zero variance or invalid returns; beta and correlation are withheld.');
    else if(spy&&!samePrimaryContract&&!supplementalDaily)set('beta_market_correlation','not_supplied',null,'The available stock and benchmark bars do not share a verified source and adjustment contract.');
    else set('beta_market_correlation',spy||supplementalSpy?'insufficient_history':'not_supplied',null,spy||supplementalSpy?'Needs 127 distinct, valid, common completed sessions and non-zero benchmark variance.':'No matched stock/SPY daily return pair is available.');
    if(row.symbol==='SPY')set('relative_strength_spy','not_applicable',null,'SPY is the benchmark itself; a self-comparison is not relative-strength evidence.');
    else if(primaryAligned&&!primaryAligned.invalid)set('relative_strength_spy','measured',primaryAligned.excess,`126 matched desk-chart session returns versus SPY: excess ${(100*primaryAligned.excess).toFixed(2)} percentage points through ${primaryAligned.session}.`);
   else if(supplementalAligned&&!supplementalAligned.stale&&!supplementalAligned.invalid)set('relative_strength_spy','measured',supplementalAligned.excess,`126 matched Yahoo Finance historical session returns for ${row.symbol} and SPY: excess ${(100*supplementalAligned.excess).toFixed(2)} percentage points through ${supplementalAligned.session}. Both series use the same secondary source; neither replaces or is spliced into the desk chart.`);
   else if(primaryAligned?.invalid)set('relative_strength_spy','partial',null,'Matched desk-chart session returns produced a non-finite result and no valid secondary pair was available; relative strength is withheld.');
   else if((spy&&!spyCurrent)||aligned?.stale)set('relative_strength_spy','stale',null,`The desk symbol and SPY do not have a fresh matched close (${stockLast||'unknown'} vs ${spyLast||'unknown'}); no current relative-strength value is inferred.`);
   else if(!spy&&(!supplementalDaily||!supplementalSpy))set('relative_strength_spy','not_supplied',null,'No SPY daily comparison series is supplied with the desk chart or the matched secondary-history pair.');
    else set('relative_strength_spy','insufficient_history',null,'Needs 127 distinct, valid, common completed daily sessions (126 return intervals) from one matched source pair.');
    const primaryLine=primaryAligned&&!primaryAligned.invalid&&row.symbol!=='SPY'?setupFactorRelativeLine(bars,spy?.bars,126):null,secondaryLine=!primaryLine&&supplementalAligned&&!supplementalAligned.stale&&!supplementalAligned.invalid&&row.symbol!=='SPY'?setupFactorRelativeLine(supplementalDaily?.bars,supplementalSpy?.bars,126):null,line=primaryLine||secondaryLine;
    if(row.symbol==='SPY')set('rs_line_leadership','not_applicable',null,'SPY is the benchmark itself; no self-relative line is drawn.');
    else if(line){const plotCompatible=!!(primaryLine&&chart?.source&&spy?.source&&chart.source===spy.source&&chart.adjustment===spy.adjustment);set('rs_line_leadership','measured',{...line,source:primaryLine?'desk chart pair':'Yahoo Finance matched historical pair',plot_compatible:plotCompatible},`Matched-session relative-strength ratio indexed to 100, ${line.matched_sessions} points through ${line.through}; over the last 63 sessions the RS line ${line.rs_new_63_session_high?'made':'did not make'} a strict new high and price ${line.price_new_63_session_high?'made':'did not make'} one${line.rs_leads_price?'; relative strength is leading price':''}. ${plotCompatible?'The line is source/adjustment matched and can be drawn with this chart.':'The separately sourced ratio is a measurement only and is not overlaid on desk candles.'}`,line.rs_leads_price);}
    else set('rs_line_leadership',(spy&&!spyCurrent)||aligned?.stale?'stale':!spy&&(!supplementalDaily||!supplementalSpy)?'not_supplied':'insufficient_history',null,'A current matched stock/SPY daily pair with 127 common sessions is required to measure the relative-strength line and leadership.');
    const sectorInstrumentType=String(row?.instrument?.instrument_type||row?.chart?.instrument_type||'').toUpperCase(),sectorCurrency=String(row?.instrument?.currency||row?.chart?.currency||'').toUpperCase(),sectorInput=row?.supplemental_history?.sector,sectorETF=setupFactorSectorBenchmarkSymbol(sectorInput?.sector),sectorReceived=Date.parse(sectorInput?.received_at||''),sectorProfileCurrent=sectorInput?.source==='Yahoo Finance symbol search'&&sectorInput?.symbol===row?.symbol&&sectorETF&&sectorInput?.benchmark_symbol===sectorETF&&Number.isFinite(sectorReceived)&&sectorReceived<=now&&now-sectorReceived<=24*60*60*1000;
   const sectorRaw=sectorInput?.benchmark?.chart||sectorInput?.benchmark,sectorSeries=sectorProfileCurrent?setupFactorSupplementCurrent(sectorRaw,primaryDaily,now,sectorETF,'1d'):null;
   const sectorStockRaw=supplementalDaily||(chart?.source==='Yahoo Finance historical bars'?chart:null)||(lifetime?{...lifetime,interval:'1d',last_completed_at:lifetime.last_completed_at||lifetime.bars?.at(-1)?.[0]}:null),sectorStock=sectorProfileCurrent?setupFactorSupplementCurrent(sectorStockRaw,primaryDaily,now,row?.symbol,'1d'):null,sectorAligned=sectorStock&&sectorSeries?setupFactorAlignedReturns(sectorStock.bars,sectorSeries.bars,126):null;
    if(['ETF','ETP'].includes(sectorInstrumentType))set('relative_strength_sector','not_applicable',null,'This instrument is an exchange-traded fund; issuer-sector relative strength does not apply.');
    else if(sectorInstrumentType&&sectorInstrumentType!=='EQUITY')set('relative_strength_sector','not_applicable',null,`Issuer-sector relative strength applies to equities, not ${sectorInstrumentType.toLowerCase()} instruments.`);
    else if(sectorCurrency&&sectorCurrency!=='USD')set('relative_strength_sector','not_applicable',null,`The available sector ETF comparison is denominated in USD; ${sectorCurrency} instruments need a currency-matched sector benchmark.`);
   else if(sectorAligned&&!sectorAligned.stale&&!sectorAligned.invalid){const excessPct=100*sectorAligned.excess,stockPct=100*sectorAligned.stock_return,sectorPct=100*sectorAligned.benchmark_return;set('relative_strength_sector','measured',{sector:sectorInput.sector,benchmark_symbol:sectorETF,matched_sessions:sectorAligned.matched_sessions,session:sectorAligned.session,stock_return_pct:stockPct,sector_return_pct:sectorPct,excess_return_pct:excessPct,source:'Yahoo Finance matched historical pair'},`${row.symbol} returned ${setupFactorFmt(stockPct,1)}% versus its ${sectorInput.sector} sector ETF ${sectorETF} at ${setupFactorFmt(sectorPct,1)}% over 126 matched daily intervals through ${sectorAligned.session}; relative performance ${excessPct>=0?'+' : ''}${setupFactorFmt(excessPct,1)} percentage points.`,Math.abs(excessPct)>=3);}
   else if(sectorAligned?.stale)set('relative_strength_sector','stale',null,`The ${sectorInput?.sector||'sector'} benchmark and ${row.symbol} do not share the same latest completed session.`);
   else if(sectorAligned?.invalid)set('relative_strength_sector','partial',null,'Matched sector-relative returns were invalid; no sector-strength value is used.');
   else if(sectorProfileCurrent&&!sectorSeries)set('relative_strength_sector','stale',null,`The ${sectorInput.sector} sector ETF ${sectorETF} has no current matched daily series.`);
   else if(sectorInput&&sectorInput.symbol===row?.symbol&&!sectorETF)set('relative_strength_sector','not_supplied',null,`The issuer sector “${String(sectorInput.sector||'').slice(0,48)}” has no mapped broad-sector ETF benchmark.`);
   else if(!precise)set('relative_strength_sector','not_applicable',null,'Sector-relative performance is measured on completed daily bars.');
   else set('relative_strength_sector','not_supplied',null,'A current issuer-sector classification and matched sector ETF history are not attached. A theme-rank percentile is not sector-relative performance.');
  const lector=row?.ranker;set('chartslector_stage',lector?.stage?'measured':'not_supplied',lector?.stage||null,lector?.stage?`ChartsLector stage ${lector.stage}; relative opportunity score ${setupFactorFmt(lector.opp)}/100. This is a screen score, not a confidence or win-rate estimate.`:'No current ChartsLector row.');
   const observedWeekly=seriesFor(row.symbol,'1wk'),observedWeeklyCurrent=setupFactorSourceCurrent(observedWeekly,now)&&observedWeekly.bars?.length>=34,weekly=observedWeeklyCurrent?observedWeekly:(supplementalWeekly||observedWeekly),supplementalMonthly=setupFactorSupplementCurrent(row?.supplemental_history?.monthly,primaryDaily,now,row?.symbol,'1mo'),monthly=supplementalMonthly||seriesFor(row.symbol,'1mo'),weeklyCurrent=setupFactorSourceCurrent(weekly,now);for(const series of [weekly,monthly])if(series)setupFactorAnalyzeChart(series,analysisCache,now);
   const weeklyPatterns=weeklyCurrent&&weekly?setupFactorWeeklyReversalPatterns(weekly.bars,primaryDaily?.bars?.at(-1)?.[0]):null,weeklyPatternStatus=value=>!weekly?'not_supplied':!weeklyCurrent?'stale':!weeklyPatterns||weeklyPatterns.insufficient_history?'insufficient_history':value?'partial':'measured',weeklyPatternDetail=(label,value)=>!weekly?'No matched weekly OHLCV source was received; no pattern absence is inferred.':!weeklyCurrent?'The weekly OHLCV source is stale or not aligned to the latest daily session.':!weeklyPatterns||weeklyPatterns.insufficient_history?`Only ${weeklyPatterns?.completed_weeks||0} completed weekly bars are available; at least 56 are required for the prior-year spike comparison.`:value?`${label}: ${value.kind.replaceAll('_',' ')} from ${value.start_at} to ${value.end_at}; ${value.confirmed?`confirmed by a completed weekly close on ${value.confirmed_at} through ${setupFactorFmt(value.break_level)}.`:'the formation has not closed through its confirmation level.'} The spike-range ratio is ${setupFactorFmt(value.spike_range_ratio,2)}× the prior-year 75th-percentile range${value.overlap_ratio===null?'':`; two-bar overlap is ${setupFactorFmt(value.overlap_ratio*100,0)}%`}${value.spike_volume_ratio===null?'':`; right/left spike volume ${setupFactorFmt(value.spike_volume_ratio,2)}×`}.`: `Scanned ${weeklyPatterns?.completed_weeks||0} completed weekly bars; no ${label.toLowerCase()} met the installed shape and confirmation screen.`;
   for(const [id,keys,label]of [['horn_pattern',['horn_top','horn_bottom'],'Horn'],['pipe_pattern',['pipe_top','pipe_bottom'],'Pipe']]){const value=weeklyPatterns?Object.fromEntries(keys.map(key=>[key,weeklyPatterns[key]])):null,found=value&&keys.some(key=>value[key]);set(id,weeklyPatternStatus(found?value[keys.find(key=>value[key])]:null),found?value:null,weeklyPatternDetail(label,found?value[keys.find(key=>value[key])]:null),!!(found&&keys.some(key=>value[key]?.confirmed)));}
  const w=weekly?.bars||[],weeklyClose=w.at(-1)?.[4],weeklySma30=w.length>=30?setupFactorMean(w.slice(-30).map(b=>b[4])):null,weeklyPrior=w.length>=34?setupFactorMean(w.slice(-34,-4).map(b=>b[4])):null;
   const stage=weeklySma30!==null&&weeklyPrior!==null?(weeklyClose>weeklySma30&&weeklySma30>weeklyPrior?'Stage 2 · advancing':weeklyClose<weeklySma30&&weeklySma30<weeklyPrior?'Stage 4 · declining':weeklyClose>weeklySma30?'Stage 1 / 3 · improving or flattening':'Stage 3 · weakening / distribution'):null;set('weinstein_stage',!weekly?'insufficient_history':!weeklyCurrent?'stale':stage?'partial':'insufficient_history',stage,stage?`${stage}; proxy uses the 30-week average and its four-week slope. ${weeklyCurrent?'':'The weekly chart is stale; do not use this as current evidence.'} This is a mechanical stage read, not discretionary chart annotation.`:'Needs 34 completed weekly bars.');
  const frames=[['1mo',monthly],['1wk',weekly],['1d',seriesFor(row.symbol,'1d')||(chart?.interval==='1d'?chart:null)],['1h',seriesFor(row.symbol,'1h')]],frameRead=frames.map(([int,s])=>{const a=s?setupFactorAnalyzeChart(s,analysisCache,now):null,fresh=int==='1wk'||int==='1mo'||int==='1d'?setupFactorSourceCurrent(s,now):null;return {interval:int,structure:a?.metrics?.structure||null,status:!s?'not_supplied':fresh===false?'stale':a?.status||'unavailable',last_completed_at:s?.last_completed_at||s?.as_of||null,current:fresh};});const frameStatus=frameRead.some(x=>x.current===true)?'partial':frameRead.some(x=>x.current===false)?'stale':'not_supplied',frameText=frameRead.map(x=>`${x.interval}: ${x.current===false?'stale · ':''}${x.structure||x.status}`).join('; ')+(monthly?.derived_from?' Monthly structure is aggregated from completed daily OHLCV; the current month is excluded.':'');set('higher_timeframe_map',frameStatus,frameRead,frameText);
  const wave=tech.elliott,scannedBars=Number.isInteger(wave?.input_bar_count)?wave.input_bar_count:null,invalidated=Array.isArray(wave?.invalidated)?wave.invalidated.length:0;
  if(wave?.preferred)set('elliott_wave','measured',wave.preferred,`${wave.preferred.phase} ${wave.preferred.direction}; invalidation ${wave.preferred.invalidation?.price??'not supplied'}.`);
  else if(wave?.status==='ambiguous'){const counts=(wave.ambiguous||[]).slice(0,2).map(x=>({phase:x.phase,direction:x.direction,degree:x.degree,confirmed_at:x.confirmed_at,ambiguity_reason:x.ambiguity_reason}));set('elliott_wave','partial',{status:'ambiguous',input_bar_count:scannedBars,counts},`Scanned ${scannedBars??'the available'} completed bars. ${counts.length} structurally valid count(s) remain, but wave-length rules disagree, so no preferred count or trade level is assigned.`);}
  else if(wave?.status==='no_valid_count')set('elliott_wave','measured',{status:'no_valid_count',input_bar_count:scannedBars,as_of:wave.as_of,invalidated_count:invalidated},`Elliott structure was scanned through ${wave.as_of||'the latest completed bar'} (${scannedBars??'available'} bars); no rule-valid count remains${invalidated?`; ${invalidated} earlier candidate(s) were invalidated`:''}. This is a completed negative scan, not missing input.`);
  else set('elliott_wave',wave?.status==='warming'?'insufficient_history':'not_supplied',null,wave?.status==='warming'?`Elliott scan needs at least 20 completed bars; ${scannedBars??0} supplied.`:'No completed Elliott scan is attached to the current chart.');
  const volatility=usable.market_volatility?.source==='Cboe Global Markets'?usable.market_volatility:null,volIndices=volatility?.indices||{},officialVix=volIndices.VIX,officialVixFresh=setupFactorFinite(officialVix?.close)&&timed(officialVix?.as_of,2*86400000),fallbackVix=usable.mood_ring?.inputs?.vix,vixAsOf=usable.mood_ring?.as_of||usable.as_of||packet?.as_of,fallbackVixFresh=setupFactorFinite(fallbackVix)&&timed(vixAsOf,2*86400000),vix=officialVixFresh?officialVix.close:fallbackVix,vixDate=officialVixFresh?officialVix.as_of:vixAsOf,vixFresh=officialVixFresh||fallbackVixFresh,staleVix=setupFactorFinite(officialVix?.close)||setupFactorFinite(fallbackVix),vixStatus=vixFresh?'measured':staleVix?'stale':'not_supplied',vixValue=officialVixFresh?officialVix.close:setupFactorFinite(fallbackVix)?fallbackVix:setupFactorFinite(officialVix?.close)?officialVix.close:null;
  const vixDetail=officialVixFresh?`Cboe VIX official daily close ${setupFactorFmt(vix)} on ${vixDate}; received ${officialVix.received_at||volatility.received_at||'unknown time'}. This is a daily close, not an intraday quote.`:fallbackVixFresh?`VIX ${setupFactorFmt(fallbackVix)} from the external market-context packet as of ${vixAsOf}.` :setupFactorFinite(officialVix?.close)?`Latest Cboe VIX daily close ${setupFactorFmt(officialVix.close)} on ${officialVix.as_of}; stale and excluded from current evidence.`:setupFactorFinite(fallbackVix)?`VIX ${setupFactorFmt(fallbackVix)} from the external market-context packet as of ${vixAsOf||'unknown date'}; stale and excluded from current evidence.`:'No VIX close or current market-context reading.';
  set('vix',vixStatus,vixValue,vixDetail);
  const indexRows=['VIX','VIX3M','VVIX','SKEW'].map(name=>{const x=volIndices[name];return {name,close:setupFactorFinite(x?.close)&&x.close>0?x.close:null,as_of:x?.as_of||null,received_at:x?.received_at||null,fresh:setupFactorFinite(x?.close)&&timed(x.as_of,2*86400000)};}),freshRows=indexRows.filter(x=>x.fresh),staleRows=indexRows.filter(x=>setupFactorFinite(x.close)&&!x.fresh),short=volIndices.VIX,long=volIndices.VIX3M,termRatio=short&&long&&short.as_of===long.as_of&&setupFactorFinite(short.close)&&setupFactorFinite(long.close)&&long.close>0?short.close/long.close:null,volValue=Object.fromEntries([...freshRows.map(x=>[x.name.toLowerCase(),{close:x.close,as_of:x.as_of}]),...(termRatio!==null?[['vix_vix3m_ratio',termRatio]]:[])]),volState=freshRows.length===4&&termRatio!==null?'measured':freshRows.length?'partial':staleRows.length?'stale':'not_supplied';
  const volDetail=freshRows.length?`Cboe daily closes: ${freshRows.map(x=>`${x.name} ${setupFactorFmt(x.close)} (${x.as_of})`).join('; ')}${termRatio!==null?`; VIX/VIX3M ${setupFactorFmt(termRatio,3)} on matched dates`:''}. ${staleRows.length?`Stale series retained but excluded: ${staleRows.map(x=>x.name).join(', ')}. `:''}Cboe SKEW is the market index, not single-name put/call IV skew; VVIX is volatility of VIX, not equity volatility.`:staleRows.length?`Only stale Cboe volatility closes are available (${staleRows.map(x=>`${x.name} ${x.as_of}`).join('; ')}); no current structure is inferred.`:'No Cboe daily VIX, VIX3M, VVIX or SKEW close is supplied.';
  set('market_volatility_structure',volState,Object.keys(volValue).length?volValue:null,volDetail);
   const breadth=usable.breadth,b=breadth?.current,breadthAsOf=breadth?.as_of||usable.as_of||packet?.as_of,breadthFresh=setupFactorCurrentDaily(breadthAsOf,now,market),breadthPresent=b&&setupFactorFinite(b.pct50);set('breadth',breadthPresent?(breadthFresh?'measured':'stale'):'not_supplied',breadthPresent?{...b,as_of:breadthAsOf||null}:null,breadthPresent?`Above 20/50/200-day averages: ${setupFactorFmt(b.pct20)}% / ${setupFactorFmt(b.pct50)}% / ${setupFactorFmt(b.pct200)}%${breadthAsOf?` as of ${breadthAsOf}`:''}.${breadthFresh?'':' Stale context is retained for inspection but excluded from the current read.'}`:'No current market breadth receipt.');
   const marketInternals=setupFactorMarketInternals(seriesFor('SPY','1d')||supplementalSpy,now),internalStatus=marketInternals.status;
   set('distribution_day_count',internalStatus,internalStatus==='partial'?{count:marketInternals.distribution_days?.length||0,days:marketInternals.distribution_days,as_of:marketInternals.as_of,method:marketInternals.method}:null,internalStatus==='partial'?`${marketInternals.distribution_days.length} distribution-day proxy event(s) in the last 25 completed SPY sessions: ${marketInternals.distribution_days.map(x=>`${x.date} (${setupFactorFmt(x.change_pct,2)}%)`).join('; ')||'none'}. Rule: index down at least 0.2% on higher volume; event ages out after 25 sessions or a 5% recovery.`:`SPY volume history is ${internalStatus}; distribution count is not asserted.`,internalStatus==='partial'&&(marketInternals.distribution_days?.length||0)>=3);
   set('follow_through_day',internalStatus,internalStatus==='partial'?marketInternals.follow_through:null,internalStatus==='partial'?marketInternals.follow_through?`SPY follow-through proxy ${marketInternals.follow_through.date}: ${setupFactorFmt(marketInternals.follow_through.gain_pct,2)}% gain on higher volume, ${marketInternals.follow_through.day_after_low} sessions after the recent low. The rally-attempt day is not separately annotated, so this remains a mechanical proxy.`:'No follow-through proxy in the recent SPY window: no >=1.7% higher-volume gain 4–10 sessions after the measured low.':'SPY volume history is '+internalStatus+'; follow-through is not asserted.',internalStatus==='partial'&&!!marketInternals.follow_through);
   const regime=usable.mood_ring,regimeAsOf=regime?.as_of||usable.as_of||packet?.as_of,regimeFresh=!!regime?.state&&setupFactorCurrentDaily(regimeAsOf,now,market);set('market_regime',regime?.state?(regimeFresh?'measured':'stale'):'not_supplied',regime?.state||null,regime?.state?`Market mood ${regime.state}; composite ${setupFactorFmt(regime.composite)} as of ${regimeAsOf||'unknown date'}${regimeFresh?'':' · stale context is not treated as current regime evidence'}.`:'Market regime packet not supplied.');
  const ratios=usable.risk_appetite?.ratios||[],symbolsOf=pair=>String(pair||'').toUpperCase().split(/[^A-Z0-9.]+/).filter(Boolean),treasury=new Set(['TLT','IEF','SHY','TNX','TLH','IEI','SHV']),highYield=new Set(['HYG','JNK','USHY','BKLN']),creditNames=new Set(['HYG','LQD','JNK','USHY','BKLN']),rateRatio=ratios.find(r=>{const names=symbolsOf(r.pair);return names.length===2&&names.every(x=>treasury.has(x));}),creditRatio=ratios.find(r=>{const names=symbolsOf(r.pair);return names.length===2&&names.every(x=>creditNames.has(x))||names.length===2&&names.some(x=>highYield.has(x))&&names.some(x=>treasury.has(x));}),dollarRatio=ratios.find(r=>/UUP|DXY|dollar/i.test(String(r.pair||'')));
   const riskAsOf=usable.risk_appetite?.as_of||usable.as_of||packet?.as_of,riskFresh=setupFactorCurrentDaily(riskAsOf,now,market);for(const [id,x]of [['rates',rateRatio],['credit',creditRatio],['dollar',dollarRatio]])set(id,x?(riskFresh?'partial':'stale'):'not_supplied',x?{...x,as_of:riskAsOf||null}:null,x?`${x.pair}: points toward ${x.risk_on?'taking more risk':'safer investments'}; one-month change ${setupFactorFmt(x.chg_1m)}${riskAsOf?`; context as of ${riskAsOf}`:''}.${riskFresh?'':' Stale context is retained for inspection but excluded from the current read.'}`:`No separate ${id} comparison is included in today’s market data. Available comparisons are not counted a second time.`);
  const macroAsOf=chart?.as_of||chart?.last_completed_at||packet?.as_of,curve=setupFactorTreasuryCurve(usable.macro,macroAsOf,30,7),realCurve=setupFactorRealTreasuryCurve(usable.macro,macroAsOf,30,7),dollarIndex=setupFactorDollarIndex(usable.macro,macroAsOf,5,10);
  if(dollarIndex?.status==='measured'){
   const value={source:dollarIndex.source,series_id:dollarIndex.series_id,as_of:dollarIndex.as_of,age_days:dollarIndex.age_days,unit:'index, January 1997=100',latest:dollarIndex.latest,prior_at:dollarIndex.prior.date,change_pct:dollarIndex.change_pct,advanced_change_pct:dollarIndex.advanced_change_pct,emerging_change_pct:dollarIndex.emerging_change_pct,lookback_sessions:dollarIndex.lookback_sessions};
   set('dollar','partial',value,`Federal Reserve H.10 nominal broad U.S. dollar index ${setupFactorFmt(dollarIndex.latest.broad,2)} as of ${dollarIndex.as_of}; ${dollarIndex.lookback_sessions}-session change ${setupFactorFmt(dollarIndex.change_pct,2)}% versus ${dollarIndex.prior.date}. Advanced-economy index change ${setupFactorFmt(dollarIndex.advanced_change_pct,2)}%; emerging-economy index change ${setupFactorFmt(dollarIndex.emerging_change_pct,2)}%.`);
  }else if(!dollarRatio&&dollarIndex){set('dollar',dollarIndex.status,{source:dollarIndex.source,series_id:dollarIndex.series_id,as_of:dollarIndex.as_of,age_days:dollarIndex.age_days,latest:dollarIndex.latest},`Federal Reserve H.10 dollar index is ${dollarIndex.status}; it is not treated as a current measurement.`);}
  if(curve?.status==='measured'){
   const nominalLabels={one_month:'1m',two_month:'2m',three_month:'3m',four_month:'4m',six_month:'6m',one_year:'1y',two_year:'2y',three_year:'3y',five_year:'5y',seven_year:'7y',ten_year:'10y',twenty_year:'20y',thirty_year:'30y'},realLabels={five_year:'5y',seven_year:'7y',ten_year:'10y',twenty_year:'20y',thirty_year:'30y'},nominalText=Object.entries(nominalLabels).filter(([key])=>setupFactorFinite(curve.latest[key])).map(([key,label])=>`${label} ${setupFactorFmt(curve.latest[key],2)}%`).join(', '),realText=realCurve?.status==='measured'?Object.entries(realLabels).filter(([key])=>setupFactorFinite(realCurve.latest[key])).map(([key,label])=>`${label} ${setupFactorFmt(realCurve.latest[key],2)}%`).join(', '):`real-yield curve ${realCurve?.status||'not supplied'}`,breakeven10y=realCurve?.status==='measured'?curve.latest.ten_year-realCurve.latest.ten_year:null;
   const value={source:curve.source,series_id:curve.series_id,as_of:curve.as_of,age_days:curve.age_days,unit:'percent',nominal_yields:Object.fromEntries(Object.keys(nominalLabels).filter(key=>setupFactorFinite(curve.latest[key])).map(key=>[key,curve.latest[key]])),ten_minus_two:curve.latest.ten_year-curve.latest.two_year,prior_at:curve.prior.date,nominal_changes:curve.changes,real_yields:realCurve?.status==='measured'?Object.fromEntries(Object.keys(realLabels).filter(key=>setupFactorFinite(realCurve.latest[key])).map(key=>[key,realCurve.latest[key]])):null,real_as_of:realCurve?.as_of||null,real_age_days:realCurve?.age_days??null,real_changes:realCurve?.status==='measured'?realCurve.changes:null,ten_year_nominal_minus_real:breakeven10y,lookback_days:curve.lookback_days};
   set('rates','partial',value,`US Treasury nominal par curve as of ${curve.as_of}: ${nominalText}; 10y–2y slope ${setupFactorFmt(curve.latest.ten_year-curve.latest.two_year,2)} percentage points. Versus ${curve.prior.date}: 2y ${setupFactorFmt(curve.changes.two_year,2)} pp, 10y ${setupFactorFmt(curve.changes.ten_year,2)} pp, 30y ${setupFactorFmt(curve.changes.thirty_year,2)} pp. Real par curve ${realCurve?.as_of||'not current'}: ${realText}${setupFactorFinite(breakeven10y)?`; 10y nominal-minus-real yield spread ${setupFactorFmt(breakeven10y,2)} percentage points`:''}.`);
  }else if(realCurve?.status==='measured'){
   const labels={five_year:'5y',seven_year:'7y',ten_year:'10y',twenty_year:'20y',thirty_year:'30y'},realText=Object.entries(labels).filter(([key])=>setupFactorFinite(realCurve.latest[key])).map(([key,label])=>`${label} ${setupFactorFmt(realCurve.latest[key],2)}%`).join(', '),value={source:'US Treasury',series_id:realCurve.series_id,as_of:realCurve.as_of,age_days:realCurve.age_days,real_yields:realCurve.latest,real_changes:realCurve.changes,lookback_days:realCurve.lookback_days};
   set('rates','partial',value,`US Treasury real par curve as of ${realCurve.as_of}: ${realText}. Versus ${realCurve.prior.date}: 10y ${setupFactorFmt(realCurve.changes.ten_year,2)} percentage points.`);
  }else if(curve&& !rateRatio)set('rates',curve.status,{source:curve.source,series_id:curve.series_id,as_of:curve.as_of,age_days:curve.age_days,latest:curve.latest},`US Treasury par-curve input is ${curve.status==='stale'?'older than seven calendar days':'missing an observation at least 30 calendar days before the setup session'}; it is not used as a current rate reading.`);
  const earnings=(market.earnings||[]).filter(x=>(x.symbol||x.sym)===row.symbol&&x.actual_occurrence_source);set('earnings_calendar',earnings.length?'partial':'not_supplied',earnings,earnings.length?`${earnings.length} reported earnings occurrence(s); future calendar and prior price reactions are not included in this feed.`:'No symbol-specific earnings occurrence or reaction history.');
  const eDate=earnings.find(x=>x.announcement_at&&timed(x.announcement_at,365*86400000));if(eDate){set('events','measured',eDate.announcement_at,`Reported earnings occurrence ${eDate.announcement_at}; first published ${eDate.first_published_at||'unknown'}.`,true);}
  if(terminal.closed_trades){const own=terminal.closed_trades.filter(x=>x.symbol===row.symbol&&(!e.book_label||x.book_label===e.book_label));set('prior_history',own.length?'measured':'measured',own.length?{count:own.length,wins:own.filter(x=>x.net_pnl>0).length,losses:own.filter(x=>x.net_pnl<0).length}:0,own.length?`${own.length} linked closed paper trades in the published history.`:'No linked closed paper trades in the published history.');}
  const positions=Array.isArray(snapshot?.positions)?snapshot.positions:null,matching=positions?positions.filter(p=>String(p?.symbol||'').trim().toUpperCase()===String(row?.symbol||'').trim().toUpperCase()):null,owners=matching?[...new Set(matching.map(p=>p.book_label).filter(x=>typeof x==='string'&&x.length))]:[];
  set('owning_sleeves',positions?'measured':'not_supplied',positions?owners:null,positions?(owners.length?`Current published positions assign ${row.symbol} to ${owners.join(', ')}.`:`No current published open position in ${row.symbol}.`):'The complete public position list is not present; sleeve ownership cannot be established from candidate rows.');
  if(matching){const byCurrency=new Map();for(const p of matching){const currency=String(p.currency||'unknown').toUpperCase(),quantity=setupFactorFinite(p.quantity)?p.quantity:null,mark=setupFactorFinite(p.mark_price)?p.mark_price:null,value=setupFactorFinite(p.market_value)?p.market_value:quantity!==null&&mark!==null?quantity*mark:null,prior=byCurrency.get(currency)||{positions:0,quantity:0,market_value:0,unmarked:0};prior.positions++;if(quantity!==null)prior.quantity+=quantity;if(value!==null)prior.market_value+=value;else prior.unmarked++;byCurrency.set(currency,prior);}const exposure=Object.fromEntries([...byCurrency.entries()]);set('current_exposure','partial',{position_count:matching.length,by_currency:exposure},`${matching.length?`Name-level exposure: ${Object.entries(exposure).map(([currency,x])=>`${currency} ${setupFactorFmt(x.market_value,0)} across ${x.positions} position(s)`).join('; ')}`:`No current published ${row.symbol} position.`} Sector-level total is unavailable because the public snapshot does not bind each position to an issuer sector.`);}
  else set('current_exposure','not_supplied',null,'The complete public position list is not present; name and sector exposure cannot be established.');
  for(const factor of setupFactorPlanChecks(row,row?.action_plan,now))set(factor.id,factor.status,null,factor.detail,factor.material);
  set('fear_day','not_supplied',null,'No explicit QQQ red-day / 3:20–3:50 ET feature is present for this setup.');
  const step=close<20?1:close<100?5:close<500?10:50,near=Math.round(close/step)*step;set('support_resistance_zones',results.get('support_resistance_zones').status,results.get('support_resistance_zones').value,results.get('support_resistance_zones').detail+` Nearest round-number reference: ${setupFactorFmt(near)}.`);
  const facts=row.evidence?.flatMap(x=>Object.entries(x.features||{}).map(([k,v])=>[k,v]))||[],feature=(re)=>facts.filter(([k,v])=>re.test(k)&&(['string','number','boolean'].includes(typeof v)));
  const tensorFrames=Object.fromEntries(['1wk','1d','1h'].map(interval=>[interval,setupFactorTensorFrame(row,relatedCharts,interval,now,analysisCache)])),tensorAvailable=Object.values(tensorFrames).filter(frame=>frame.status==='measured'),tensorStale=Object.values(tensorFrames).filter(frame=>frame.status==='stale'),tensorSummary=setupFactorTensorSummary(tensorFrames),tensorFrameText=interval=>{const value=tensorFrames[interval]?.value;if(!value)return `${interval}: ${tensorFrames[interval]?.detail||'not supplied'}`;const neutral=value.components.filter(vote=>vote.direction==='neutral'&&vote.available).length,unavailable=value.components.filter(vote=>!vote.available).length;return `${interval} ${value.bullish_votes} bullish / ${value.bearish_votes} bearish / ${neutral} neutral / ${unavailable} warming votes; net ${value.balance>=0?'+':''}${value.balance} of ${value.total_votes} available, ${value.direction}, as of ${value.as_of}`;};
  const slowFrames=['1wk','1d'].filter(interval=>tensorFrames[interval]?.status==='measured'),slowDirections=new Set(slowFrames.map(interval=>tensorFrames[interval].value.direction).filter(direction=>direction!=='neutral')),slowDirection=slowDirections.size===1?[...slowDirections][0]:slowDirections.size>1?'split':'neutral',slowValue={weekly:tensorFrames['1wk']?.value||null,daily:tensorFrames['1d']?.value||null,direction:slowDirection};
  const slowStatus=slowFrames.length===2?'measured':slowFrames.length?'partial':tensorStale.length?'stale':'not_supplied';
  set('tensor_slow',slowStatus,slowFrames.length?slowValue:null,`Slow Tensor uses completed weekly and daily bars. ${tensorFrameText('1wk')}; ${tensorFrameText('1d')}. ${slowDirection==='split'?'Weekly and daily point in opposite directions.':slowDirection==='neutral'?'No directional majority is present.':`Weekly and daily ${slowDirection==='bullish'?'agree upward':'agree downward'}.`}`,slowFrames.length===2&&['bullish','bearish'].includes(slowDirection));
  const hourly=tensorFrames['1h'],hourlyStatus=hourly.status,hourlyValue=hourlyStatus==='measured'?hourly.value:null;
  set('tensor_fast',hourlyStatus,hourlyValue,`Fast Tensor uses completed hourly bars. ${tensorFrameText('1h')}`,hourlyStatus==='measured'&&hourlyValue.direction!=='neutral');
  const frameVotes=Object.fromEntries(['1wk','1d','1h'].map(interval=>[interval,tensorFrames[interval]?.value?{direction:tensorFrames[interval].value.direction,components:tensorFrames[interval].value.components,as_of:tensorFrames[interval].value.as_of}:null]));
  const tensorVoteStatus=tensorAvailable.length===3?'measured':tensorAvailable.length?'partial':tensorStale.length?'stale':'not_supplied';
  set('tensor_votes',tensorVoteStatus,tensorAvailable.length?frameVotes:null,`Canonical v698 seven-component state votes by timeframe. ${tensorFrameText('1wk')}; ${tensorFrameText('1d')}; ${tensorFrameText('1h')}.`);
  const strengths=Object.fromEntries(['1wk','1d','1h'].map(interval=>[interval,tensorFrames[interval]?.value?.strength??null])),availableStrengths=Object.values(strengths).filter(value=>setupFactorFinite(value));
  set('tensor_strength',tensorVoteStatus,availableStrengths.length?{per_timeframe:strengths,equal_weight_mean:availableStrengths.reduce((sum,value)=>sum+value,0)/availableStrengths.length}:null,`Tensor strength is net bullish minus bearish votes divided by available component votes, shown separately by timeframe. ${tensorFrameText('1wk')}; ${tensorFrameText('1d')}; ${tensorFrameText('1h')}.`);
  const timeframeStatus=tensorAvailable.length===3?'measured':tensorAvailable.length?'partial':tensorStale.length?'stale':'not_supplied';
  set('tensor_timeframes',timeframeStatus,tensorAvailable.length?tensorSummary:null,tensorAvailable.length===3?`Tensor v698 timeframe agreement: weekly ${tensorSummary.frames[0]?.direction}; daily ${tensorSummary.frames[1]?.direction}; hourly ${tensorSummary.frames[2]?.direction}; result ${tensorSummary.alignment}. The aggregate is one grouped momentum input, not seven independent confirmations.`:`Tensor v698 timeframe agreement is incomplete (${tensorAvailable.length}/3 current frames). ${tensorFrameText('1wk')}; ${tensorFrameText('1d')}; ${tensorFrameText('1h')}. Missing or stale frames do not vote.`,tensorAvailable.length===3&&['bullish','bearish'].includes(tensorSummary.direction));
  const fear=feature(/fear.?day|qqq.*red|entry.?window/i);if(fear.length)set('fear_day','partial',Object.fromEntries(fear),fear.map(([k,v])=>`${k}: ${v}`).join('; '));
  const asset=market.assets?.find?.(x=>x.symbol===row.symbol)||null,assetAt=asset?.as_of||asset?.market_at,assetValues={},assetStale=[];
  for(const [key,label,maxAge]of [['market_cap','Market capitalization',7*86400000],['float','Float',100*86400000]])if(setupFactorFinite(asset?.[key])&&asset[key]>0){if(assetAt&&timed(assetAt,maxAge))assetValues[key]=asset[key];else assetStale.push(label);}
  if(Object.keys(assetValues).length)set('market_cap_float','partial',{...assetValues,as_of:assetAt,source:asset?.source||null},`${Object.entries(assetValues).map(([key,value])=>`${key==='market_cap'?'Market capitalization':'Float'} ${setupFactorFmt(value)}`).join('; ')}; source date ${assetAt}. Float allows a longer reporting interval than market capitalization.`);
  else if(assetStale.length)set('market_cap_float','stale',{as_of:assetAt,source:asset?.source||null},`${assetStale.join(' and ')} value(s) are outside their freshness windows; they are retained as historical context only.`);
  const spread=market.asset_quotes?.find?.(x=>x.symbol===row.symbol)||null,spreadValid=spread&&setupFactorFinite(spread.bid)&&spread.bid>0&&setupFactorFinite(spread.ask)&&spread.ask>=spread.bid,spreadMarketAge=spread?.feed==='delayed_sip'?20*60000:5*60000,spreadFresh=spreadValid&&timed(spread.market_at,spreadMarketAge)&&timed(spread.received_at,5*60000),mid=spreadValid?(spread.bid+spread.ask)/2:null,spreadPct=spreadValid&&mid>0?100*(spread.ask-spread.bid)/mid:null,spreadScope=spread?.feed==='iex'?'single_exchange':(['sip','alpaca_sip','delayed_sip'].includes(spread?.feed)?'consolidated':'feed_unspecified'),spreadFeedLabel=spread?.feed==='delayed_sip'?'consolidated U.S. market feed delayed 15 minutes':spread?.feed==='iex'?'IEX single-exchange feed':(['sip','alpaca_sip'].includes(spread?.feed)?'consolidated U.S. market feed':spread?.feed||'unlabeled feed');
  const spreadScopeNote=spreadScope==='single_exchange'?' This is one exchange only; its quote may differ from the best bid and ask across the whole market.':'';
  set('spread',spreadFresh?'partial':spreadValid?'stale':'not_supplied',spreadValid?{symbol:spread.symbol,bid:spread.bid,ask:spread.ask,spread:spread.ask-spread.bid,spread_pct:spreadPct,scope:spreadScope,market_at:spread.market_at,received_at:spread.received_at,feed:spread.feed}:null,spreadFresh?`Observed ${setupFactorFmt(spread.ask-spread.bid)} quote gap (${setupFactorFmt(spreadPct,3)}% of midpoint) on the ${spreadFeedLabel}, market time ${spread.market_at}, received ${spread.received_at}. One snapshot does not establish the typical spread.${spreadScopeNote}`:spreadValid?'The quote is retained but stale or missing a trustworthy market/receipt clock; it is not a current quote snapshot.':'No valid ticker-bound bid/ask quote in the sanitized setup packet.');
  const dollarBars=precise?bars.slice(-20):[],reportedDollarVolume=e.features?.avg_dollar_volume,averageDollarVolume=setupFactorFinite(reportedDollarVolume)?reportedDollarVolume:dollarBars.length===20&&dollarBars.every(b=>setupFactorFinite(b[4])&&b[4]>0&&setupFactorFinite(b[5])&&b[5]>=0)?setupFactorMean(dollarBars.map(b=>b[4]*b[5])):null;
  set('dollar_volume',setupFactorFinite(averageDollarVolume)?(setupFactorFinite(reportedDollarVolume)?'partial':'measured'):precise?'insufficient_history':'not_applicable',averageDollarVolume,setupFactorFinite(averageDollarVolume)?`20-session average close × volume: $${setupFactorFmt(averageDollarVolume,0)}${setupFactorFinite(reportedDollarVolume)?' (strategy-reported).':' from the supplied completed daily bars.'}`:precise?'Needs 20 complete daily close and volume observations.':'A daily series is required to estimate average dollar volume.');
   const dailyChart=seriesFor(row.symbol,'1d')|| (chart?.interval==='1d'?chart:null),weeklyChart=weekly;for(const [id,series]of [['daily_divergences',dailyChart],['weekly_divergences',weeklyChart]]){
   const analysis=series?setupFactorAnalyzeChart(series,analysisCache,now):null,events=analysis?.divergences||[],activeEvents=events.filter(x=>x.current_status!=='invalidated'),invalidatedEvents=events.filter(x=>x.current_status==='invalidated'),scan=analysis?.divergence_scan,labels=new Map([['RSI14','RSI'],['MACD12_26_9','MACD'],['SlowStochastic14_3_3','slow stochastic'],['OBV','OBV'],['ADLine','A/D'],['MFI14','MFI'],['VolumeEMA5_20','volume EMA 5–20']]);
   const signals=events.map(d=>({kind:d.kind,divergence_type:d.divergence_type,indicator:d.indicator,indicator_label:d.indicator_label||labels.get(d.indicator)||d.indicator,continuation_alignment:d.continuation_alignment||'unknown',current_status:d.current_status||'intact',invalidation_level:d.invalidation_level??null,first_index:d.first_index,second_index:d.second_index,first_price:d.first_price,second_price:d.second_price,first_confirmed_at:d.first_confirmed_at||null,confirmed_at:d.confirmed_at||null}));
    const checked=Number.isInteger(scan?.comparisons)?scan.comparisons:0,gauges=Number.isInteger(scan?.gauges_checked)?scan.gauges_checked:0,available=Number.isInteger(scan?.gauges_available)?scan.gauges_available:0,pairs=scan?.eligible_pivot_pairs||{},ready=!!series&&!!analysis&&analysis.status!=='unavailable'&&analysis.pivots?.length>0,eligible=!!(pairs.bullish||pairs.bearish),missing=(scan?.gauge_availability||[]).filter(x=>x.status!=='available').map(x=>x.name),fresh=setupFactorSourceCurrent(series,now),stale=!!series&&!fresh;
    const status=stale?'stale':!ready?'insufficient_history':eligible&&gauges===7?'measured':'partial',reason=stale?`The latest completed ${id.startsWith('daily')?'daily':'weekly'} bar is stale; ${signals.length?'historical divergences are retained for inspection but excluded from current alignment.':'no current divergence conclusion is available.'}`:!ready?'No '+(id.startsWith('daily')?'daily':'weekly')+' chart with confirmed pivots.':!eligible?`${available}/7 divergence gauges have current values, but no confirmed price-pivot pair met the recency and spacing rules; no-divergence is not inferred.${invalidatedEvents.length?` Earlier: ${invalidatedEvents.map(d=>setupFactorDivergenceSignalText(signals.find(x=>x.indicator===d.indicator&&x.second_index===d.second_index)||d)).join('; ')}.`:''}`:`${activeEvents.length?activeEvents.map(d=>setupFactorDivergenceSignalText(signals.find(x=>x.indicator===d.indicator&&x.second_index===d.second_index)||d)).join('; '):'No current divergence found at the eligible confirmed price-pivot pair'} ${gauges}/7 gauges compared; ${checked} confirmed price-pivot comparisons${missing.length?`; unavailable gauges: ${missing.join(', ')}`:''}.${invalidatedEvents.length?` Earlier: ${invalidatedEvents.map(d=>setupFactorDivergenceSignalText(signals.find(x=>x.indicator===d.indicator&&x.second_index===d.second_index)||d)).join('; ')}.`:''}`;
    set(id,status,signals,reason,!!fresh&&!!activeEvents.length);
  }
  // Explicitly separate model inputs the public terminal does not currently ingest.
  for(const id of ['dealer_gamma_name','market_options','short_interest','short_activity','insider_activity','industry_peers','sec_filings','quarterly_fundamentals','corporate_events','analyst_revisions','economic_calendar','geopolitical_news','attention','market_cap_float'])if(results.get(id).status==='not_supplied')set(id,'not_supplied',null,'No current, ticker-bound observation is included in the published setup feed.');
  if(['1d','1wk','1mo'].includes(chart?.interval)&&!setupFactorSourceCurrent(chart,now))for(const id of ['head_shoulders','inverse_head_shoulders','double_top','double_bottom','triple_top','ascending_triangle','descending_triangle','symmetrical_triangle','rising_wedge','falling_wedge','expanding_wedge','bull_flag','bear_flag','bull_pennant','bear_pennant','cup_handle','inverted_cup_handle','rectangle','rising_channel','falling_channel','breakout_quality','confirmed_swings','support_resistance_trendlines','support_resistance_zones','level_confluence','average_retests','breakout_retest','structure_integrity','one_year_fibonacci','measured_targets','fifty_two_week_range','sma10','sma20','sma50','sma200','rsi','macd_line','macd_signal','macd_histogram','macd_crossovers','slow_stochastic','adx_dmi','relative_volume','breakout_volume','six_month_momentum','relative_strength_spy','beta_market_correlation','vwap20','value_area_high','value_area_low','volume_poc','anchored_vwap_earnings','anchored_vwap_swing','gap_direction','gap_taxonomy','unfilled_gaps','candlestick_detectors','obv','accumulation_distribution','mfi','atr_stretch','extension_rank','bollinger_squeeze','dollar_volume','cci','williams_r','stoch_rsi','roc_horizons','aroon','vortex','trix','coppock','historical_volatility_percentile','elder_ray','mass_index','chaikin_money_flow','chaikin_oscillator','elder_force_index','ease_of_movement','klinger','vwma','up_down_volume','nvi','pvi','pvt','ichimoku_tenkan','ichimoku_kijun','ichimoku_cloud','ichimoku_chikou','floor_pivots','prior_day_week_month_levels','parabolic_sar','supertrend','keltner_channels','donchian_20','donchian_55','chandelier_exit','vwap_stdev_bands','ma_ribbon_gmma','all_time_high_low','seasonality','ipo_base','anchored_vwap_ipo','monthly_options_expiry','anchored_vwap_gap','ytd_anchored_vwap','golden_death_cross','fair_value_gaps','liquidity_sweeps','nr4_compression','nr7_compression','heikin_ashi','td_sequential','order_blocks','base_on_base','base_stage','diamond_top','diamond_bottom','andrews_pitchfork']){const f=results.get(id);if(f&&['measured','partial'].includes(f.status))set(id,'stale',f.value,`The latest completed ${chart.interval} bar is stale; retained measurements are historical context only. ${f.detail}`,false);}
 }
 if(!chartOK){
    for(const id of ['sma10','sma20','sma50','sma200','rsi','macd_line','macd_signal','macd_histogram','macd_crossovers','slow_stochastic','adx_dmi','relative_volume','breakout_volume','six_month_momentum','relative_strength_spy','beta_market_correlation','vwap20','value_area_high','value_area_low','volume_poc','bollinger_squeeze','breakout_quality','level_confluence','support_resistance_zones','average_retests','structure_integrity','confirmed_swings','support_resistance_trendlines','anchored_vwap_swing','gap_direction','unfilled_gaps','gap_taxonomy','candlestick_detectors','effort_result','double_bottom','symmetrical_triangle','measured_targets','one_year_fibonacci','fifty_two_week_range','breakout_retest','obv','accumulation_distribution','mfi','extension_rank','iv_realized','name_options','iv_rank','anchored_vwap_earnings','cci','williams_r','stoch_rsi','roc_horizons','aroon','vortex','trix','historical_volatility_percentile','elder_ray','mass_index','chaikin_money_flow','chaikin_oscillator','elder_force_index','ease_of_movement','klinger','vwma','up_down_volume','nvi','pvi','pvt','ichimoku_tenkan','ichimoku_kijun','ichimoku_cloud','ichimoku_chikou','floor_pivots','prior_day_week_month_levels','parabolic_sar','supertrend','keltner_channels','donchian_20','donchian_55','chandelier_exit','vwap_stdev_bands','ma_ribbon_gmma','all_time_high_low','anchored_vwap_gap','ytd_anchored_vwap','golden_death_cross','fair_value_gaps','liquidity_sweeps','nr4_compression','nr7_compression','heikin_ashi','td_sequential','base_on_base','base_stage','diamond_top','diamond_bottom','andrews_pitchfork'])set(id,'insufficient_history',null,'A valid completed OHLCV chart with a usable price is required.');
  for(const id of ['head_shoulders','inverse_head_shoulders','double_top','triple_top','ascending_triangle','descending_triangle','rising_wedge','falling_wedge','expanding_wedge','bull_flag','bear_flag','bull_pennant','bear_pennant','cup_handle','inverted_cup_handle','rectangle','rising_channel','falling_channel'])set(id,'not_scanned',null,'The chart input is unavailable; no pattern absence is inferred.');
    for(const id of ['climax_top','climax_run','selling_climax','flat_base','base_depth','base_length','volume_dry_up','three_weeks_tight','pivot_tightness','vcp','bull_trap','bear_trap','base_on_base','base_stage','diamond_top','diamond_bottom'])set(id,'insufficient_history',null,'A valid completed daily OHLCV chart is required; no pattern absence is inferred.');
  for(const id of ['right_angled_broadening_top','right_angled_broadening_bottom','v_top','v_bottom','dead_cat_bounce','ascending_base','island_reversal','rounding_bottom','high_tight_flag','bump_run_reversal','power_earnings_gap'])set(id,'insufficient_history',null,'A valid completed daily OHLCV chart is required; no pattern absence is inferred.');
 }
 if(!chartOK)for(const id of ['coppock'])set(id,'insufficient_history',null,'A valid completed OHLCV chart is required.');
 if(!chartOK)for(const id of ['wyckoff_phase','wyckoff_events'])set(id,'insufficient_history',null,'A valid completed daily or weekly OHLCV chart and confirmed pivots are required.');
  if(['1d','1wk','1mo'].includes(chart?.interval)&&!setupFactorSourceCurrent(chart,now))for(const id of ['right_angled_broadening_top','right_angled_broadening_bottom','v_top','v_bottom','dead_cat_bounce','ascending_base','island_reversal','rounding_bottom','high_tight_flag','bump_run_reversal','tower_tops','horn_pattern','pipe_pattern','climax_top','climax_run','selling_climax','flat_base','base_depth','base_length','volume_dry_up','three_weeks_tight','pivot_tightness','vcp','bull_trap','bear_trap','base_on_base','base_stage','diamond_top','diamond_bottom','power_earnings_gap','rs_line_leadership']){const f=results.get(id);if(f&&['measured','partial'].includes(f.status))set(id,'stale',f.value,`The source chart is stale; retained measurements are historical context only. ${f.detail}`,false);}
 if(['1d','1wk','1mo'].includes(chart?.interval)&&!setupFactorSourceCurrent(chart,now))for(const id of ['climax_top','climax_run','selling_climax','flat_base','base_depth','base_length','volume_dry_up','three_weeks_tight','pivot_tightness','vcp','bull_trap','bear_trap','rs_line_leadership']){const f=results.get(id);if(f&&['measured','partial'].includes(f.status))set(id,'stale',f.value,`The source chart is stale; retained measurements are historical context only. ${f.detail}`,false);}
  // Surface only independent evidence that clears a fixed materiality bar.
  // Relative strength is a six-month excess-return difference; tiny residuals
  // are not a directional vote. OBV/A-D changes are normalized by the same
  // 20-session volume so large share-count names do not win by scale alone.
  const relativeStrength=results.get('relative_strength_spy');
  if(relativeStrength?.status==='measured'&&setupFactorFinite(relativeStrength.value))results.set('relative_strength_spy',{...relativeStrength,material:Math.abs(relativeStrength.value)>=.02});
  const volume20=d.volumes.slice(-20).reduce((sum,value)=>sum+(setupFactorFinite(value)?value:0),0);
  for(const id of ['obv','accumulation_distribution']){
    const factor=results.get(id),change=setupFactorFinite(factor?.value?.change20)?factor.value.change20:null;
    if(factor?.status==='measured'&&change!==null&&volume20>0){const fraction=change/volume20;results.set(id,{...factor,value:{...factor.value,change20_volume_fraction:fraction},detail:`${factor.detail} 20-session signed change is ${(fraction*100).toFixed(1)}% of traded volume.`,material:Math.abs(fraction)>=.05});}
  }
  const moneyFlow=results.get('mfi');if(moneyFlow?.status==='measured'&&setupFactorFinite(moneyFlow.value))results.set('mfi',{...moneyFlow,material:moneyFlow.value>=60||moneyFlow.value<=40});
  const order={measured:0,partial:1,stale:2,insufficient_history:3,not_scanned:4,not_supplied:5,not_applicable:6};
 return [...results.values()].map(x=>({...x,order:order[x.status]??9}));
}


// Original: worker/pattern-history.js
/* Historical chart analogs, not sleeve simulations. Features use a trailing
 * prefix; analog outcomes end before the current feature window starts.
 * Equal family weights are declared, not fitted probabilities or edge claims.
 * No network, orders, databases or wall-clock cache identity. */
var PATTERN_HISTORY_METHOD='chart-analogs-2';
const patternHistoryCache=new WeakMap();
const patternHistorySharedCache=new Map();
let patternHistoryCacheBytes=0;
function patternHistoryQuantile(values,q){
 const a=values.filter(Number.isFinite).sort((a,b)=>a-b);if(!a.length)return null;
 const p=(a.length-1)*q,l=Math.floor(p);return a[l]+(a[Math.ceil(p)]-a[l])*(p-l);
}
function patternHistoryFeature(bars,i){
 if(i<50)return null;
 const slice=bars.slice(i-49,i+1),last=bars[i],close=last[4];
 const avg=(rows,col)=>rows.reduce((s,b)=>s+b[col],0)/rows.length;
 const prior=bars.slice(i-20,i),priorHigh=Math.max(...prior.map(b=>b[2])),priorLow=Math.min(...prior.map(b=>b[3]));
 const tr=(j)=>Math.max(bars[j][2]-bars[j][3],Math.abs(bars[j][2]-bars[j-1][4]),Math.abs(bars[j][3]-bars[j-1][4]));
 // This is a simple 14-bar mean range, deliberately not labelled Wilder ATR.
 const range=Array.from({length:14},(_,k)=>tr(i-k)).reduce((a,b)=>a+b,0)/14;
 if(!(range>0)||!(priorHigh>priorLow))return null;
 let gains=0,losses=0;for(let j=i-13;j<=i;j++){const d=bars[j][4]-bars[j-1][4];gains+=Math.max(0,d);losses+=Math.max(0,-d);}
 const momentum=gains+losses>0?(gains-losses)/(gains+losses):0;
 const priorVolume=avg(prior,5),volume=priorVolume>0?Math.log1p(last[5]/priorVolume)/Math.log(3):null;
 const dayRange=last[2]-last[3],baselineRange=avg(bars.slice(i-49,i-19).map(b=>[0,0,b[2]-b[3]]),2);
 return [
  [(close-priorLow)/(priorHigh-priorLow),close>priorHigh?1:close<priorLow?-1:0],
  [(close-avg(slice.slice(-20),4))/range/3,(avg(slice.slice(-20),4)-avg(slice,4))/range/3],
  [momentum,(close-bars[i-10][4])/range/5],
  volume===null?null:[volume],
  [Math.log1p(range/close*100)/2,baselineRange>0?Math.log(range/baselineRange):0],
  dayRange>0?[(close-last[1])/dayRange,(close-last[3])/dayRange]:[0,.5]
 ];
}
function patternHistoryDistance(a,b){
 let sum=0,n=0;for(let k=0;k<a.length;k++){
  if(!a[k]||!b[k])continue;
  sum+=a[k].reduce((s,v,j)=>s+Math.min(4,(v-b[k][j])**2),0)/a[k].length;n++;
 }return n>=5?Math.sqrt(sum/n):Infinity;
}
function buildPatternHistory(chart){
 const original=chart?.bars;
 const empty=(reason)=>({method:PATTERN_HISTORY_METHOD,status:'unavailable',reason,horizons:[],orders:false});
 if(!Array.isArray(original)||original.length<110)return empty('history_shorter_than_110_completed_bars');
 const bars=original.slice(-1500),signature=JSON.stringify([chart.symbol,chart.interval,chart.source,chart.adjustment,bars]);
 const cached=patternHistoryCache.get(original);if(cached?.signature===signature)return cached.result;
 const key=JSON.stringify([chart.symbol,chart.interval,chart.source,chart.adjustment]);
 const shared=patternHistorySharedCache.get(key);
 if(shared?.signature===signature){patternHistorySharedCache.delete(key);patternHistorySharedCache.set(key,shared);patternHistoryCache.set(original,shared);return shared.result;}
 let prior=-Infinity;
 for(const b of bars){
  const t=Array.isArray(b)?Date.parse(b[0]):NaN;
  if(!Number.isFinite(t)||t<=prior||b.slice(1,5).length!==4||!b.slice(1,5).every(x=>typeof x==='number'&&Number.isFinite(x)&&x>0)||
    b[2]<Math.max(b[1],b[4])||b[3]>Math.min(b[1],b[4])||b[2]<b[3]||!(b[5]==null||typeof b[5]==='number'&&Number.isFinite(b[5])&&b[5]>=0))return empty('invalid_or_unordered_bars');
  prior=t;
 }
 // Missing volume remains missing, including partially missing windows.
 const features=bars.map((_,i)=>{
  const f=patternHistoryFeature(bars,i);
  if(f&&bars.slice(Math.max(0,i-20),i+1).some(b=>b[5]==null))f[3]=null;
  return f;
 });
 const current=features.at(-1),origin=bars.length-1;if(!current)return empty('flat_or_unusable_current_window');
 const horizons=[5,20].map(horizon=>{
  const eligible=[];
  for(let i=50;i+horizon<origin-49;i++)if(features[i])eligible.push({index:i,distance:patternHistoryDistance(current,features[i])});
  eligible.sort((a,b)=>a.distance-b.distance||b.index-a.index);
  const selected=[];for(const row of eligible){
   if(row.distance>.65)break;
   if(selected.some(s=>Math.abs(s.index-row.index)<=horizon))continue;
   selected.push(row);if(selected.length===12)break;
  }
  const returns=selected.map(s=>100*(bars[s.index+horizon][4]/bars[s.index][4]-1));
  const baseline=[];for(let i=50;i+horizon<origin-49;i+=horizon+1)baseline.push(100*(bars[i+horizon][4]/bars[i][4]-1));
  const samples=selected.map(s=>({origin:bars[s.index][0],outcome_at:bars[s.index+horizon][0],distance:+s.distance.toFixed(4)}));
  return {bars:horizon,status:selected.length>=5?'available':'limited',samples:selected.length,
   positive:returns.filter(x=>x>0).length,negative:returns.filter(x=>x<0).length,flat:returns.filter(x=>x===0).length,
   median_return_pct:patternHistoryQuantile(returns,.5),lower_quartile_pct:patternHistoryQuantile(returns,.25),upper_quartile_pct:patternHistoryQuantile(returns,.75),
   baseline_samples:baseline.length,baseline_median_return_pct:patternHistoryQuantile(baseline,.5),
   median_best_excursion_pct:patternHistoryQuantile(selected.map(s=>100*(Math.max(...bars.slice(s.index+1,s.index+horizon+1).map(b=>b[2]))/bars[s.index][4]-1)),.5),
   median_worst_excursion_pct:patternHistoryQuantile(selected.map(s=>100*(Math.min(...bars.slice(s.index+1,s.index+horizon+1).map(b=>b[3]))/bars[s.index][4]-1)),.5),
   matches:samples};
 });
 const result={method:PATTERN_HISTORY_METHOD,status:horizons.some(h=>h.status==='available')?'available':'limited',symbol:chart.symbol||null,interval:chart.interval||null,
  source:chart.source||null,adjustment:chart.adjustment||null,origin:bars.at(-1)[0],history_start:bars[0][0],history_bars:bars.length,
  family_count:current.filter(Boolean).length,families:['structure','trend','momentum','volume','volatility','candle_shape'].filter((_,i)=>current[i]),
  basis:'same_instrument_completed_bar_patterns',selection:'six_equal_family_distances_max_0.65_nonoverlapping_outcomes',horizons,orders:false};
 const entry={signature,result,bytes:signature.length*2+8192};
 patternHistoryCache.set(original,entry);
 if(shared){patternHistoryCacheBytes-=shared.bytes;patternHistorySharedCache.delete(key);}
 patternHistorySharedCache.set(key,entry);patternHistoryCacheBytes+=entry.bytes;
 while(patternHistorySharedCache.size>96||patternHistoryCacheBytes>6*1024*1024){const oldest=patternHistorySharedCache.keys().next().value;patternHistoryCacheBytes-=patternHistorySharedCache.get(oldest).bytes;patternHistorySharedCache.delete(oldest);}
 return result;
}
function patternHistorySentence(history){
 return patternHistorySentences(history).join(' ')||null;
}
function patternHistorySentences(history){
 return (history?.horizons||[]).filter(h=>h.status==='available').map(h=>{
 const unit=history.interval==='1d'?'sessions':history.interval==='1wk'?'weeks':history.interval==='1h'?'hourly bars':'bars';
 const fmt=x=>`${x>0?'+':''}${x.toFixed(1)}%`;
 return `Across ${h.samples} earlier similar chart periods in ${history.symbol||'this instrument'}, the median move over ${h.bars} ${unit} was ${fmt(h.median_return_pct)}; the middle half ranged from ${fmt(h.lower_quartile_pct)} to ${fmt(h.upper_quartile_pct)}. The unfiltered historical median was ${fmt(h.baseline_median_return_pct)}.`;
 });
}


// Original: dist/setup-plan.js
/* Display precision never changes stored levels, comparisons or risk arithmetic.
 * Entry bands round inward; unusually narrow bands retain enough digits to fit. */
function setupPriceDigits(value){const n=Math.abs(value);return n>=1?2:n>0?Math.min(12,Math.max(4,4-Math.floor(Math.log10(n)))):2;}
function setupPlainMarketConflict(value,side=0){
 const text=String(value??''),direction=side>0?'bullish':side<0?'bearish':'current';
 const counted=text.match(/cross-asset risk appetite opposes this direction\s*\(\s*([\d.]+)\s*\/\s*([\d.]+)\s*risk-on\s*\)\.?/i);
 if(counted)return `${counted[1]} of ${counted[2]} market comparisons favor taking more risk, opposing the ${direction} call.`;
 if(/cross-asset risk appetite opposes (?:the supportive chart structure|this plan)\.?/i.test(text))return `Market comparisons oppose the ${direction} plan.`;
 return text;
}
function setupMarketComparisonCount(text){const match=String(text||'').match(/(\d+(?:\.\d+)?) of (\d+(?:\.\d+)?) market comparisons/i);return match?match[1]+'/'+match[2]:null;}
function setupPriceText(value){if(typeof value!=='number'||!Number.isFinite(value))return 'Not published';return value.toLocaleString('en-US',{maximumFractionDigits:setupPriceDigits(value)});}
function setupPlanTickSize(value,tickSize=null){return Number.isFinite(tickSize)&&tickSize>0?tickSize:Math.abs(value)<1?0.0001:0.01;}
function setupPlanTickEpsilon(units){return Number.EPSILON*Math.max(1,Math.abs(units))*8;}
function setupPlanTickAligned(value,tick){const q=value/tick,n=Math.round(q);return Math.abs(q-n)<=setupPlanTickEpsilon(q);}
function setupPlanTickPrice(value,tick,rounding){const q=value/tick,n=Math.round(q),epsilon=setupPlanTickEpsilon(q);if(Math.abs(q-n)<=epsilon)return Number((n*tick).toPrecision(14));const units=rounding==='up'?Math.ceil(q-epsilon):Math.floor(q+epsilon);return Number((units*tick).toPrecision(14));}
function setupPlanTickDigits(tick){const text=tick.toFixed(12).replace(/0+$/,'');return text.includes('.')?text.length-text.indexOf('.')-1:0;}
function setupPlanPriceText(value,tickSize=null){if(typeof value!=='number'||!Number.isFinite(value))return 'Not published';const tick=setupPlanTickSize(value,tickSize),digits=Math.max(setupPriceDigits(value),setupPlanTickDigits(tick));return value.toLocaleString('en-US',{maximumFractionDigits:digits});}
function setupPlanRelationText(relation){return relation==='at_or_above'?'at or above':relation==='at_or_below'?'at or below':relation;}
function setupPlanEntryThresholds(side,price,tickSize=null,method='breakout'){
 const tick=setupPlanTickSize(price,tickSize),aligned=setupPlanTickAligned(price,tick),close=aligned?setupPlanTickPrice(price+(side>0?tick:-tick),tick,side>0?'up':'down'):setupPlanTickPrice(price,tick,side>0?'up':'down');
 const close_relation=side>0?'at_or_above':'at_or_below';
 if(method!=='structural_retest')return {test:null,close:{price:close,relation:close_relation}};
 const test=aligned?price:setupPlanTickPrice(price,tick,side>0?'down':'up');
 return {test:{price:test,relation:side>0?'at_or_below':'at_or_above'},close:{price:close,relation:close_relation}};
}
function setupPlanInvalidationThreshold(side,price,tickSize=null){
 const tick=setupPlanTickSize(price,tickSize),aligned=setupPlanTickAligned(price,tick);
 return {price:aligned?setupPlanTickPrice(price+(side>0?-tick:tick),tick,side>0?'down':'up'):setupPlanTickPrice(price,tick,side>0?'down':'up'),relation:side>0?'at_or_below':'at_or_above'};
}
function setupPlanTargetThreshold(side,price,tickSize=null){
 const tick=setupPlanTickSize(price,tickSize),aligned=setupPlanTickAligned(price,tick);
 return {price:aligned?price:setupPlanTickPrice(price,tick,side>0?'down':'up'),relation:side>0?'at_or_above':'at_or_below'};
}
function setupPlanTickBand(low,high,tickSize=null){
 if(!Number.isFinite(low)||!Number.isFinite(high)||low>high)return null;
 const lo=setupPlanTickPrice(low,setupPlanTickSize(low,tickSize),'up'),hi=setupPlanTickPrice(high,setupPlanTickSize(high,tickSize),'down');
 if(lo>hi)return null;const digits=Math.max(setupPlanTickDigits(setupPlanTickSize(lo,tickSize)),setupPlanTickDigits(setupPlanTickSize(hi,tickSize)),setupPriceDigits(lo),setupPriceDigits(hi)),format=value=>value.toLocaleString('en-US',{maximumFractionDigits:digits});
 return {low:lo,high:hi,text:format(lo)+'–'+format(hi)};
}
function setupPlanEntryCloseInBand(side,close,band,tickSize=null){
 if(!side||!Number.isFinite(close?.price)||!Number.isFinite(band?.low)||!Number.isFinite(band?.high)||band.low>band.high)return close;
 const tick=setupPlanTickSize(close.price,tickSize),boundary=side>0?Math.max(close.price,band.low):Math.min(close.price,band.high),price=setupPlanTickPrice(boundary,tick,side>0?'up':'down');
 return {...close,price};
}
// Cash distances use cents for ordinary amounts and two meaningful digits for
// sub-cent amounts. This is presentation only; a positive amount never becomes 0.
function setupAmountText(value){
  if(typeof value!=='number'||!Number.isFinite(value))return 'Not published';
  const size=Math.abs(value);if(size>0&&size<1e-10)return value.toExponential(1);
  return value.toLocaleString('en-US',size>0&&size<.01?{maximumSignificantDigits:2}:{maximumFractionDigits:2});
}
// Explain the same latest opposing swing used by the plan. An older level
// still below/above price is context, not a silent substitute for that swing.
function setupRiskPivotExplanation(row,now=Date.now()){
  const m=row.technicals?.metrics||{},side=row.direction==='bullish'?1:row.direction==='bearish'?-1:0,kind=side>0?'support':'resistance';
  if(!side||!Number.isFinite(m.close)||m.close<=0)return null;
  const pivot=(row.technicals?.pivots||[]).filter(p=>p.kind===kind&&Number.isFinite(p.price)&&p.price>0&&typeof p.confirmed_at==='string'&&Number.isFinite(Date.parse(p.confirmed_at))&&Date.parse(p.confirmed_at)<=now).sort((a,b)=>b.index-a.index)[0];
  const frame={'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly'}[row.chart?.interval]||'chart',swing=side>0?'low':'high';
  if(!pivot)return {state:'missing',text:'Define this plan’s risk at the next confirmed '+frame+' '+kind+' swing '+swing+'.'};
  const distance=side*(m.close-pivot.price);if(distance>0)return {state:'intact',pivot};
  const price=setupPriceText,date=new Date(pivot.confirmed_at).toLocaleDateString('en-US',{timeZone:'UTC',month:'short',day:'numeric'}),context=m[kind];
  const older=Number.isFinite(context)&&context>0&&side*(m.close-context)>0&&context!==pivot.price;
  const lead=distance<0?'Latest '+frame+' '+kind+' swing at '+price(pivot.price)+' failed (confirmed '+date+'): the last close '+price(m.close)+' is '+(side>0?'below':'above')+' it.':'Last close '+price(m.close)+' is testing the latest '+frame+' '+kind+' swing at '+price(pivot.price)+' (confirmed '+date+').';
  const contextText=older?'Older '+kind+' at '+price(context)+' remains secondary chart context.':'';
  const trigger=distance<0?'Reopen the '+(side>0?'bullish':'bearish')+' setup on a completed '+frame+' close '+(side>0?'above ':'below ')+price(pivot.price)+'.':'Confirm the '+(side>0?'bullish':'bearish')+' setup with a completed '+frame+' close '+(side>0?'above ':'below ')+price(pivot.price)+'.';
  return {state:distance<0?'failed':'at_level',pivot,context_price:older?context:null,context_text:contextText,text:[lead,contextText,trigger].filter(Boolean).join(' ')};
}
function setupEntryBand(low,high){
  if(!Number.isFinite(low)||!Number.isFinite(high)||low>high)return null;
  let digits=Math.max(setupPriceDigits(low),setupPriceDigits(high)),a,b;
  do{const unit=10**digits;a=Math.ceil(low*unit)/unit;b=Math.floor(high*unit)/unit;if(a<=b)break;digits++;}while(digits<=12);
  if(a>b)return {low,high,text:low.toString()+'–'+high.toString()};
  const format=x=>x.toLocaleString('en-US',{maximumFractionDigits:digits});
  return {low:a,high:b,text:format(a)+'–'+format(b)};
}
function setupEntryBandText(band){return typeof band?.text==='string'?band.text.split('–').map(x=>'$'+x).join('–'):null;}
function setupRetestConditionText(side,frame,entryPrice,band,tickSize=null){
 const range=setupEntryBandText(band),thresholds=setupPlanEntryThresholds(side,entryPrice,tickSize,'structural_retest');thresholds.close=setupPlanEntryCloseInBand(side,thresholds.close,band,tickSize);const bar=({'daily':'daily candle','weekly':'weekly candle','hourly':'hourly candle','four-hour':'four-hour candle','ten-minute':'10-minute candle'})[frame]||'candle',extreme=side>0?'low':'high',touch=side>0?'touch or move below':'touch or move above',test='$'+setupPlanPriceText(thresholds.test.price,tickSize),close='$'+setupPlanPriceText(thresholds.close.price,tickSize);
 return 'The '+bar+'’s '+extreme+' must '+touch+' '+test+'; its close must finish '+setupPlanRelationText(thresholds.close.relation)+' '+close+(range?' and inside '+range+' entry range':'')+'. Do not enter on the touch alone.';
}
function setupEntryConfirmationText(side,frame,entryPrice,band,method='breakout',tickSize=null){
  const range=setupEntryBandText(band),period=frame==='daily'?'day':frame==='weekly'?'week':frame==='hourly'?'hour':frame==='four-hour'?'four-hour candle':frame==='chart'?'chart period':frame,thresholds=setupPlanEntryThresholds(side,entryPrice,tickSize,method);thresholds.close=setupPlanEntryCloseInBand(side,thresholds.close,band,tickSize);
 if(method==='structural_retest')return setupRetestConditionText(side,frame,entryPrice,band,tickSize);
 return 'Enter only after the '+period+' closes '+setupPlanRelationText(thresholds.close.relation)+' $'+setupPlanPriceText(thresholds.close.price,tickSize)+(range?' while price is inside '+range:'')+'.';
}
function setupCompletedCloseText(row,frame,formattedPrice){
 const candle=frame==='chart'?'chart-period':frame;
 const raw=row?.chart?.last_completed_at||row?.chart?.as_of||row?.chart?.bars?.at(-1)?.[0]||row?.technicals?.as_of;
 const match=typeof raw==='string'?raw.match(/^(\d{4})-(\d{2})-(\d{2})/):null;
 const date=match?new Date(Date.UTC(Number(match[1]),Number(match[2])-1,Number(match[3]))).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):null;
 return 'The last completed '+candle+' candle closed at '+formattedPrice+(date?' on '+date:'' );
}
function setupEntryConditionText(side,frame,close,entryPrice,band,method='breakout',tickSize=null,row={}){
 const range=setupEntryBandText(band);
 if(method==='structural_retest'&&Number.isFinite(close)&&Number.isFinite(band?.low)&&Number.isFinite(band?.high)){
  const location=close<band.low?'below':close>band.high?'above':'inside',wait=location==='inside'?'Wait for price to test the range.':location==='below'?'Wait for price to rise into the range.':'Wait for price to fall into the range.',priceNow='$'+setupPriceText(close);
  return setupCompletedCloseText(row,frame,priceNow)+'; that close was '+location+' the '+range+' entry range. '+wait+' '+setupEntryConfirmationText(side,frame,entryPrice,band,method,tickSize);
 }
 const confirmation=setupEntryConfirmationText(side,frame,entryPrice,band,method,tickSize);
 return Number.isFinite(close)?setupCompletedCloseText(row,frame,'$'+setupPriceText(close))+'. '+confirmation:confirmation;
}
/* The plan engine owns literal manual-entry instructions. Renderers consume
 * these exact strings so the Focus card, detail card and read cannot drift. */
function setupManualExecutionSteps(brief,row={}){
 const side=brief?.direction==='bullish'?1:brief?.direction==='bearish'?-1:0,entry=brief?.entry,target=brief?.objectives?.[0]?.price,stop=brief?.invalidation?.price;
 if(brief?.authority!=='chart_research'||brief?.decision!=='conditional'||brief?.quality?.coherent!==true||!side||!Number.isFinite(entry?.price)||!Number.isFinite(target)||!Number.isFinite(stop))return null;
 if(!(side*(entry.price-stop)>0&&side*(target-entry.price)>0))return null;
 const symbol=typeof row.symbol==='string'&&row.symbol.trim()?row.symbol.trim():'this stock',currency=row.instrument?.currency||row.chart?.currency,tickSize=row.chart?.tick_size??row.technicals?.metrics?.tick_size??null,fmt=value=>(currency&&currency!=='USD'?'':'$')+setupPlanPriceText(value,tickSize),hasExplicitEntryBand=Number.isFinite(entry.acceptable_low)||Number.isFinite(entry.acceptable_high),low=Number.isFinite(entry.acceptable_low)?entry.acceptable_low:entry.price,high=Number.isFinite(entry.acceptable_high)?entry.acceptable_high:entry.price,short=side<0,lastClose=Number.isFinite(row.technicals?.metrics?.close)?row.technicals.metrics.close:null,method=brief.quality.entry_method||(entry.basis==='confirmed_shelf_retest'?'structural_retest':'breakout'),rawBand=setupPlanTickBand(Math.min(low,high),Math.max(low,high),tickSize),rawEntryClose=setupPlanEntryThresholds(side,entry.price,tickSize,method).close,band=rawBand&&setupPlanTickBand(hasExplicitEntryBand?rawBand.low:Math.min(rawBand.low,rawEntryClose.price),hasExplicitEntryBand?rawBand.high:Math.max(rawBand.high,rawEntryClose.price),tickSize);if(!band)return null;
 const lo=band.low,hi=band.high,range=lo===hi?'at '+fmt(lo):'from '+fmt(lo)+' to '+fmt(hi),rangeInside=lo===hi?'at '+fmt(lo):'inside the '+fmt(lo)+'–'+fmt(hi)+' entry range',interval=row.chart?.interval||'1d',frame=({'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly','1w':'weekly','10m':'ten-minute'})[interval]||'daily',frameArticle=frame==='hourly'?'an':'a',period=frame==='daily'?'day':frame==='weekly'?'week':frame==='hourly'?'hour':frame==='four-hour'?'four-hour candle':frame==='ten-minute'?'ten-minute candle':'day',confirmed=brief.lifecycle?.state==='confirmed',weeklyPending=frame==='weekly'&&!confirmed,entryThresholds=setupPlanEntryThresholds(side,entry.price,tickSize,method);entryThresholds.close=setupPlanEntryCloseInBand(side,entryThresholds.close,band,tickSize);const targetThreshold=setupPlanTargetThreshold(side,target,tickSize),invalidationThreshold=setupPlanInvalidationThreshold(side,stop,tickSize),trigger=fmt(entryThresholds.close.price),targetText=fmt(targetThreshold.price),stopText=fmt(invalidationThreshold.price),entryLimit=short?null:hi,limitText=short?null:fmt(entryLimit),confirmedAt=Number.isFinite(brief.lifecycle?.confirmation_price)?fmt(brief.lifecycle.confirmation_price):null;
 if(entryThresholds.close.price<lo||entryThresholds.close.price>hi)return null;
 if(confirmed){const confirmedPrice=brief.lifecycle.confirmation_price,confirmedTick=setupPlanTickSize(confirmedPrice,tickSize);if(!Number.isFinite(confirmedPrice)||!setupPlanTickAligned(confirmedPrice,confirmedTick)||side*(confirmedPrice-entryThresholds.close.price)<0||confirmedPrice<lo||confirmedPrice>hi)return null;}
 const adverseEntry=side>0?hi:lo,executionRisk=side*(adverseEntry-invalidationThreshold.price),executionReward=side*(targetThreshold.price-adverseEntry),executionRatio=executionReward/executionRisk;
 if(!(executionRisk>0&&executionReward>0&&executionRatio>=SETUP_PLAN_MIN_REWARD_RISK-1e-9))return null;
 let condition;
 if(confirmed)condition='A completed '+frame+' close at '+(confirmedAt||trigger)+' confirmed the trigger '+setupPlanRelationText(entryThresholds.close.relation)+' '+trigger+'. Enter only if the current price is still '+rangeInside+'; if it has left the range, do not enter this plan.';
 else if(method==='structural_retest'){
  const current=Number.isFinite(row.technicals?.metrics?.close)?row.technicals.metrics.close:null,location=current===null?'':current<lo?'below':current>hi?'above':'inside',wait=location==='below'?'Wait for price to rise into the range.':location==='above'?'Wait for price to fall into the range.':location==='inside'?'Price is inside the range. Wait for the confirmation close.':'Wait for price to enter the range.';
  const retest=setupRetestConditionText(side,frame,entry.price,band,tickSize);
  condition=current===null?'Wait for price to enter the '+fmt(lo)+'–'+fmt(hi)+' entry range. '+retest:setupCompletedCloseText(row,frame,fmt(current))+'; that close was '+location+' the '+fmt(lo)+'–'+fmt(hi)+' entry range. '+wait+' '+retest;
  }else condition=(lastClose!==null?setupCompletedCloseText(row,frame,fmt(lastClose))+'. ':'')+'Wait for a completed '+period+' to close '+setupPlanRelationText(entryThresholds.close.relation)+' '+trigger+' while price is '+rangeInside+'.';
 const currentRange=lo===hi?'at '+fmt(lo):'inside '+fmt(lo)+'–'+fmt(hi)+' entry range',recheck=weeklyPending?'After the next completed weekly candle confirms the rule above, use the following trading session only if price is still '+currentRange+', the target has not been reached, and no weekly candle has closed '+setupPlanRelationText(invalidationThreshold.relation)+' '+stopText+'. The recorded sleeve window is separate and does not activate this chart plan.':'When the market next opens, recheck the stock price. It must still be '+currentRange+', the target must not have been reached since this plan appeared, and no completed '+frame+' candle may have closed '+setupPlanRelationText(invalidationThreshold.relation)+' '+stopText+'. Otherwise, skip this entry.';
 const entryText=short
  ?'1. '+condition+' 2. '+recheck+' 3. This plan uses stock prices and does not specify a trade order.'
  :'1. '+condition+' 2. '+recheck+' 3. Open '+symbol+' in your trading app; this order buys shares, not options. Choose Buy, then choose Limit. Set the limit price to '+limitText+'. This is the highest stock price you will pay; do not raise it. Enter the number of shares, set the order duration to Day, then submit. If it is unfilled at market close, cancel it; cancel it sooner if price leaves the entry range.';
 const targetStep=short
  ?'At '+targetText+', the stock-price target is reached. This completes the bearish price plan; the level is not an order.'
  :'After your entry fills, open '+symbol+' in your trading app. Choose Sell (sell shares to close the position), then choose Limit. Set the price to '+targetText+' and the quantity to the shares in your position, then submit; this closes the position at the target.';
 const invalidationText=short
  ?'A completed '+frame+' candle closing '+setupPlanRelationText(invalidationThreshold.relation)+' '+stopText+' invalidates the bearish price plan. This level is not an order.'
  :'This bullish call is wrong after '+frameArticle+' '+frame+' close '+setupPlanRelationText(invalidationThreshold.relation)+' '+stopText+'. In your trading app, cancel any open target order. Choose Sell (sell shares to close the position), then choose Market. Enter the full remaining position size and submit to close.';

 const execution_thresholds={basis:'valid_underlying_price_increment',entry:{test:entryThresholds.test,close:entryThresholds.close},target:targetThreshold,invalidation:invalidationThreshold},execution_geometry={entry:adverseEntry,invalidation:invalidationThreshold.price,target:targetThreshold.price,risk_per_unit:executionRisk,reward_per_unit:executionReward,ratio:executionRatio,basis:'least_favorable_tick_aligned_entry_band_edge',costs_included:false};
 return {schema:'CODEX_SETUP_PRICE_PLAN_V6',direction:short?'bearish':'bullish',position:short?'underlying_price_map':'long_shares',execution_mode:short?'underlying_price_map':'shares_limit_order',instrument:short?{status:'not_selected',price_basis:'underlying_stock_price'}:{status:'shares',symbol},entry:entryText,target:targetStep,invalidation:invalidationText,...(!short?{order_actions:{entry:'Buy',target:'Sell',invalidation:'Sell'},order_types:{entry:'limit',target:'limit',invalidation:'market'}}:{}),price_levels:{basis:'underlying_stock_price',tick_size:tickSize,underlying:{entry:{trigger:entryThresholds.close.price,source_trigger:entry.price,low:lo,high:hi},target:targetThreshold.price,invalidation:invalidationThreshold.price},research_levels:{entry_trigger:entry.price,target,invalidation:stop},execution_thresholds,execution_geometry,...(!short?{entry:{trigger:entryThresholds.close.price,source_trigger:entry.price,low:lo,high:hi,limit:entryLimit}}:{})},...(!short?{entry_limit:{price:entryLimit,low:lo,high:hi,rule:'maximum_purchase_price'},entry_limit_price:entryLimit}:{}),target_price:targetThreshold.price,invalidation_price:invalidationThreshold.price};
}
function setupWeeklyResearchTiming(plan,row={}){
 const brief=plan?.brief,interval=row.chart?.interval,weekly=['1wk','1w','weekly'].includes(interval);
 if(!weekly||brief?.authority!=='chart_research'||brief?.decision!=='conditional'||brief?.quality?.coherent!==true||brief?.lifecycle?.state==='confirmed')return plan;
 return {...plan,timing:{...(plan.timing||{}),text:'Weekly chart plan: require the next completed weekly candle to confirm. If it confirms, evaluate this price plan only in the following trading session, inside the stated entry range. The paper sleeve’s recorded trigger and window are separate and do not activate this chart plan.'}};
}
function setupPlanExecutionChartLevels(levels,brief,manual,row={}){
 const thresholds=manual?.price_levels?.execution_thresholds,rawEntry=brief?.entry?.price,rawStop=brief?.invalidation?.price,rawTarget=brief?.objectives?.[0]?.price,entry=manual?.price_levels?.underlying?.entry,tickSize=manual?.price_levels?.tick_size;
 if(!thresholds||!Array.isArray(levels))return levels;
 const interval=row.chart?.interval||brief?.interval,frame=({'10m':'10-minute','1h':'Hourly','4h':'4-hour','1d':'Daily','1wk':'Weekly','1w':'Weekly'})[interval]||null;
 const near=(a,b)=>Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=Math.max(1e-8,(Number.isFinite(tickSize)&&tickSize>0?tickSize:setupPlanTickSize(b))/2+1e-9);
 const sameEntryBand=level=>['entry','reference'].includes(level?.kind)&&Number.isFinite(level?.range?.low)&&Number.isFinite(level?.range?.high)&&Number.isFinite(entry?.low)&&Number.isFinite(entry?.high)&&near(level.range.low,entry.low)&&near(level.range.high,entry.high);
 return levels.map(level=>{
  if(level?.kind==='invalidation'&&near(level.price,rawStop))return {...level,price:thresholds.invalidation.price,...(frame?{label:frame+' close invalidation',caption:frame+' close',detail:manual.invalidation}:{})};
  if(level?.kind==='target'&&near(level.price,rawTarget))return {...level,price:thresholds.target.price};
  // Saved retest maps can carry a price one tick outside their stored band.
  // The matching entry range identifies that line as the plan's entry, so
  // always rebuild it from the same validated close threshold used by the card.
  if(['entry','reference'].includes(level?.kind)&&(near(level.price,rawEntry)||sameEntryBand(level)))return {...level,price:thresholds.entry.close.price,range:entry&&entry.low<entry.high?{low:entry.low,high:entry.high}:undefined};
  return level;
 });
}
// Every outward-facing chart-research surface uses this same tick-valid plan.
// Saved maps used to rebuild their own prose and plot raw, sub-tick levels;
// that made the card, instructions and chart disagree even when each looked
// plausible in isolation.
function setupApplyManualExecutionContract(brief,row={}){
 const existing=brief?.manual_steps,storedThresholds=existing?.price_levels?.execution_thresholds;
 if(['CODEX_SETUP_MANUAL_EXECUTION_V4','CODEX_SETUP_MANUAL_EXECUTION_V5','CODEX_SETUP_PRICE_PLAN_V6'].includes(existing?.schema)&&storedThresholds){
  const storedLevels=existing.price_levels,raw=storedLevels.research_levels||{entry_trigger:storedLevels.underlying?.entry?.source_trigger??storedLevels.execution_thresholds?.entry?.test?.price??storedLevels.execution_thresholds?.entry?.close?.price??brief?.entry?.price,target:storedLevels.underlying?.target??storedLevels.execution_thresholds?.target?.price??brief?.objectives?.[0]?.price,invalidation:storedLevels.underlying?.invalidation??storedLevels.execution_thresholds?.invalidation?.price??brief?.invalidation?.price};
  if(![raw.entry_trigger,raw.target,raw.invalidation].every(Number.isFinite))return null;
  brief={...brief,manual_steps:null,entry:{...brief.entry,price:raw.entry_trigger},objectives:(brief.objectives||[]).map((item,index)=>index===0?{...item,price:raw.target}:item),invalidation:{...brief.invalidation,price:raw.invalidation}};
 }
 const manual=setupManualExecutionSteps(brief,row);if(!manual)return null;
 const thresholds=manual.price_levels.execution_thresholds,side=brief.direction==='bullish'?1:-1,entryPrice=thresholds.entry.close.price,targetPrice=thresholds.target.price,stopPrice=thresholds.invalidation.price,levels=manual.price_levels.underlying.entry;
 const triggerRisk=side*(entryPrice-stopPrice),triggerReward=side*(targetPrice-entryPrice);
 if(!(triggerRisk>0&&triggerReward>0))return null;
  const geometry={entry:entryPrice,stop:stopPrice,target:targetPrice,risk_per_unit:triggerRisk,reward_per_unit:triggerReward,ratio:triggerReward/triggerRisk,break_even_win_rate_pct:setupBreakEvenWinRate(triggerReward/triggerRisk),upside_pct:100*triggerReward/entryPrice,downside_pct:100*triggerRisk/entryPrice,basis:'tick_aligned_confirmation_price',costs_included:false},bandGeometry=manual.price_levels.execution_geometry,economicsSummary=(side<0?'Stock prices only; no option price or option outcome is calculated. ':'')+(bandGeometry?'Gross reward/risk: '+geometry.ratio.toFixed(2)+'R at the trigger and '+bandGeometry.ratio.toFixed(2)+'R at the least favorable entry ('+setupPlanPriceText(bandGeometry.entry,manual.price_levels.tick_size)+').':'Gross mapped reward/risk: '+geometry.ratio.toFixed(2)+'R.')+' Execution costs excluded.';
 const frame=({'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly','1w':'weekly','10m':'ten-minute'})[row.chart?.interval||brief.interval]||'daily',test=thresholds.entry.test,range=levels.low===levels.high?'at '+setupPlanPriceText(levels.low,manual.price_levels.tick_size):'inside '+setupPlanPriceText(levels.low,manual.price_levels.tick_size)+'–'+setupPlanPriceText(levels.high,manual.price_levels.tick_size),relation=setupPlanRelationText(thresholds.entry.close.relation),fmt=value=>(row.instrument?.currency&&row.instrument.currency!=='USD'?'':'$')+setupPlanPriceText(value,manual.price_levels.tick_size);
 const testRule=test?'after a completed '+frame+' candle’s '+(side>0?'low reaches at or below ':'high reaches at or above ')+fmt(test.price)+' and its close finishes '+relation+' '+fmt(entryPrice):'on a completed '+frame+' close '+relation+' '+fmt(entryPrice),actionText=side<0?'Bearish stock-price plan; no trade order is included.':'Trade action: in your trading app, choose Buy shares only after the entry rule is met.',thesis=(row.symbol||'This stock')+' · '+brief.direction+' call. '+actionText+' ENTRY: '+testRule+' '+range+'. TARGET: '+fmt(targetPrice)+'. INVALIDATION: exit if a completed '+frame+' close '+setupPlanRelationText(thresholds.invalidation.relation)+' '+fmt(stopPrice)+'.';
 const chartLevels=setupPlanExecutionChartLevels(brief.chart_levels,brief,manual,row),entry={...brief.entry,price:entryPrice,acceptable_low:levels.low,acceptable_high:levels.high,display_band:setupPlanTickBand(levels.low,levels.high,manual.price_levels.tick_size),text:manual.entry,rule_text:manual.entry},invalidation={...brief.invalidation,price:stopPrice,text:manual.invalidation},objectives=(brief.objectives||[]).map((item,index)=>index===0?{...item,price:targetPrice,text:manual.target}:item);
 return {...brief,thesis,geometry,band_geometry:bandGeometry,economics_summary:economicsSummary,chart_levels:chartLevels,entry,invalidation,objectives,manual_steps:manual,execution:{...brief.execution,text:manual.entry}};
}
function setupHasAllowedTick(side,trigger,low,high,tick){
  if(low>high)return false;
  const epsilon=1e-9,minTick=Math.ceil(low/tick-epsilon),maxTick=Math.floor(high/tick+epsilon);
  const first=side>0?Math.max(minTick,Math.ceil(trigger/tick-epsilon)):minTick;
  const last=side<0?Math.min(maxTick,Math.floor(trigger/tick+epsilon)):maxTick;
  return first<=last;
}
function setupEntryBandIssue(side,trigger,band,tickSize=null){
  if(!side||!Number.isFinite(trigger)||!Number.isFinite(band?.low)||!Number.isFinite(band?.high))return 'The entry trigger or displayed entry band is incomplete; this plan is not qualified.';
 const executableClose=setupPlanEntryThresholds(side,trigger,tickSize).close.price;
  // Below $1, NMS stock prices use $0.0001 increments. At and above $1 the
  // conservative current fallback is $0.01; use an assigned security tick
  // when the chart feed eventually supplies one. Test both sides of $1
  // separately because the valid-price lattice changes at that boundary.
  const belowLow=Math.max(0,band.low),belowHigh=Math.min(band.high,1-1e-10);
  const aboveLow=Math.max(1,band.low),aboveHigh=band.high,aboveTick=Number.isFinite(tickSize)&&tickSize>0?tickSize:0.01;
  const hasAllowedClose=setupHasAllowedTick(side,executableClose,belowLow,belowHigh,0.0001)||setupHasAllowedTick(side,executableClose,aboveLow,aboveHigh,aboveTick);
  const incrementLabel=band.low>=1?'$'+Number(aboveTick.toPrecision(4)).toString():band.high<1?'$0.0001':'supported market';
  return hasAllowedClose?null:`Displayed entry band ${setupEntryBandText(band)} contains no valid ${incrementLabel} price increment that can satisfy the required completed close ${side>0?'at or above':'at or below'} ${setupPlanPriceText(executableClose,tickSize)}. This plan is not qualified.`;
}
// Retain the old helper name for any saved test or caller while applying the
// same trigger/tick rule to every chart-research entry band.
function setupStrictRetestBandIssue(side,trigger,band,tickSize=null){return setupEntryBandIssue(side,trigger,band,tickSize);}
const SETUP_PLAN_MIN_REWARD_RISK=2;
const SETUP_PLAN_MAX_ENTRY_DRIFT_ATR=0.5;
function setupBreakEvenWinRate(ratio){return Number.isFinite(ratio)&&ratio>0?100/(1+ratio):null;}
function setupBandGeometry(side,band,stop,target){
  if(!side||!band||!Number.isFinite(band.low)||!Number.isFinite(band.high)||!Number.isFinite(stop)||!Number.isFinite(target))return null;
  const adverse=side>0?band.high:band.low,risk=side*(adverse-stop),reward=side*(target-adverse);
  const ratio=reward/risk;
  return risk>0&&reward>0?{entry:adverse,stop,target,risk_per_unit:risk,reward_per_unit:reward,ratio,break_even_win_rate_pct:setupBreakEvenWinRate(ratio),basis:'least_favorable_allowed_entry_band_edge',costs_included:false}:null;
}
// Keep the permitted order zone close to the confirmed trigger. The 2:1
// boundary remains a hard outer limit; the half-ATR cap prevents a wide
// theoretical R/R band from becoming an imprecise instruction. If ATR is
// absent, permit only one known price increment and still fail closed when
// that cannot satisfy the trigger and risk gates.
function setupQualifiedEntryBand(side,trigger,stop,target,atr14,limits=null,tickSize=null){
  if(!side||![trigger,stop,target].every(Number.isFinite)||trigger<=0||stop<=0||target<=0||side*(trigger-stop)<=0||side*(target-trigger)<=0)return null;
  const entryThreshold=setupPlanEntryThresholds(side,trigger,tickSize).close.price,stopThreshold=setupPlanInvalidationThreshold(side,stop,tickSize).price,targetThreshold=setupPlanTargetThreshold(side,target,tickSize).price;
  const risk=side*(entryThreshold-stopThreshold),reward=side*(targetThreshold-entryThreshold),minR=SETUP_PLAN_MIN_REWARD_RISK;
  if(!(risk>0&&reward>0))return {issue:'After prices are rounded to valid stock-price increments, the entry, target and invalidation no longer leave positive room for both reward and risk. This plan is not qualified.'};
  if(reward/risk<minR-1e-9)return {issue:'After prices are rounded to valid stock-price increments, the target is too close to preserve this plan’s minimum reward relative to its invalidation. This plan is not qualified.'};
  const bound=(targetThreshold+minR*stopThreshold)/(1+minR),tick=Number.isFinite(tickSize)&&tickSize>0?tickSize:(entryThreshold<1?0.0001:0.01),drift=Number.isFinite(atr14)&&atr14>0?atr14*SETUP_PLAN_MAX_ENTRY_DRIFT_ATR:tick;
  let low=side>0?entryThreshold:Math.max(bound,entryThreshold-drift),high=side>0?Math.min(bound,entryThreshold+drift):entryThreshold;
  if(Number.isFinite(limits?.low))low=Math.max(low,limits.low);
  if(Number.isFinite(limits?.high))high=Math.min(high,limits.high);
  const band=setupPlanTickBand(low,high,tickSize);
  if(!band)return {issue:setupEntryBandIssue(side,trigger,{low,high},tickSize)||'The entry zone cannot fit inside the chart’s measured 2:1 price boundary.'};
  const issue=setupEntryBandIssue(side,trigger,band,tickSize);
  if(issue)return {issue};
  const geometry=setupBandGeometry(side,band,stopThreshold,targetThreshold);
  if(!geometry||geometry.ratio<minR-1e-9)return {issue:'The displayed entry zone would reduce the measured reward-to-risk below 2:1.'};
  return {band,geometry,max_drift:drift};
}
/* A chart scenario is a conditional price map, never a sleeve order plan.
 * Projected zones use confirmed swing geometry; nearest measured obstacles win
 * over more distant projections. No probability or holding duration is inferred. */
function setupChartScenario(row, chartOK, now=Date.now()) {
  const finite=x=>typeof x==='number'&&Number.isFinite(x),positive=x=>finite(x)&&x>0;
  const side=row.direction==='bullish'?1:row.direction==='bearish'?-1:0;
  const tech=row.technicals||{},close=tech.metrics?.close,levels=tech.levels||[];
  if(!chartOK||!side||!positive(close))return null;
  const format=setupPriceText;
  const ew=tech.elliott,preferred=ew?.preferred;
  const candidates=[preferred,ew?.alternate].filter(Boolean);
  let count=candidates.find(x=>x.direction===row.direction&&['forming','confirmed'].includes(x.status)&&x.rules?.length&&x.rules.every(r=>r.passed===true));
  if(count?.length_comparison?.scale_disagreement===true)return null;
  let zone=count?.zone,invalid=count?.invalidation,confirmation=count?.confirmation,targets=count?.targets||[];
  let basis='elliott_wave',pattern=count?.pattern||null,phase=count?.phase||null,confirmed=count?.confirmed_at||null;
  const conflicts=[];
  const opposed=preferred&&preferred.direction!==row.direction&&['forming','confirmed'].includes(preferred.status);
  if(!zone||!positive(zone.low)||!positive(zone.high)||!positive(invalid?.price)) {
    // Reuse the measured 38.2–61.8% retracement of one confirmed swing. Do not
    // combine shelves from unrelated swings or turn a moving average into a stop.
    const fibs=levels.filter(x=>x.kind==='fib'&&positive(x.price)&&finite(x.start_index)&&finite(x.end_index)&&positive(x.start_price)&&positive(x.end_price)&&side*(x.end_price-x.start_price)>0);
    const anchor=fibs.sort((a,b)=>b.end_index-a.end_index)[0];
    if(!anchor)return null;
    const shelves=fibs.filter(x=>x.start_index===anchor.start_index&&x.end_index===anchor.end_index&&x.start_price===anchor.start_price&&x.end_price===anchor.end_price&&x.confirmed_at===anchor.confirmed_at&&[.382,.5,.618].includes(x.ratio));
    if(!shelves.some(x=>x.ratio===.382)||!shelves.some(x=>x.ratio===.618))return null;
    const available=Date.parse(anchor.confirmed_at);if(!Number.isFinite(available)||available>now)return null;
    const since=(row.chart?.bars||[]).slice(anchor.end_index+1);
    if(since.some(b=>side>0?b[3]<=anchor.start_price:b[2]>=anchor.start_price))return null;
    zone={low:Math.min(...shelves.map(x=>x.price)),high:Math.max(...shelves.map(x=>x.price)),basis:'38.2–61.8% retracement of the named confirmed swing',ratios:[.382,.618]};
    invalid={price:anchor.start_price,basis:'intrabar',reason:'A trade through the start of this confirmed swing cancels this pullback map.'};
    confirmation={price:side>0?zone.high:zone.low,rule:'After visiting the watch zone, require a completed '+(row.chart?.interval||'chart')+' close back '+(side>0?'above':'below')+' its near edge.'};
    targets=[{price:anchor.end_price,label:'Prior confirmed swing extreme',basis:'measured_swing'}];
    count=null;basis='confirmed_swing_retracement';pattern='pullback';phase='reversal_watch';confirmed=anchor.confirmed_at;
  }
  if(!(zone.low<=zone.high)||!positive(invalid?.price)||!positive(confirmation?.price))return null;
  if(opposed)conflicts.push('The preferred Elliott count points the other way; this is '+(count?'the alternate scenario.':'a separate measured-swing watch.'));
  const known=Date.parse(confirmed);if(!Number.isFinite(known)||known>now)return null;
  const adverse=side>0?zone.high:zone.low,favorable=side>0?zone.low:zone.high;
  const risk=side*(adverse-invalid.price),insideRisk=side*(favorable-invalid.price);
  if(!(risk>0&&insideRisk>0)||side*(close-invalid.price)<=0)return null;
  // Any real opposing pivot inside the zone prevents coherent whole-zone entry.
  const barriers=levels.filter(x=>x.kind===(side>0?'resistance':'support')&&positive(x.price));
  const inside=barriers.some(x=>x.price>zone.low&&x.price<zone.high);
  const objectives=[...targets.filter(x=>positive(x.price)).map(x=>({price:x.price,label:x.label||'Wave projection',basis:x.basis||'wave_projection',ratio:finite(x.ratio)?x.ratio:null})),...barriers.map(x=>({price:x.price,label:side>0?'Measured resistance':'Measured support',basis:'measured_barrier',ratio:null}))]
    .filter(x=>side*(x.price-adverse)>0&&side*(x.price-close)>0).sort((a,b)=>side*(a.price-b.price)||Number(a.basis!=='measured_barrier')-Number(b.basis!=='measured_barrier'));
  const unique=[];for(const x of objectives)if(!unique.some(y=>Math.abs(y.price-x.price)<=Math.max(Math.abs(x.price),1)*1e-10))unique.push(x);
  const first=unique[0]||null;
  const economics=entry=>{
    const objective=unique.find(x=>side*(x.price-entry)>0),downside=side*(entry-invalid.price),upside=objective?side*(objective.price-entry):null;
    return !inside&&downside>0&&upside>0?{entry,invalidation:invalid.price,objective:objective.price,risk_per_unit:downside,reward_per_unit:upside,ratio:upside/downside,upside_pct:100*upside/entry,downside_pct:100*downside/entry,basis:'conditional_underlying_price_geometry',costs_included:false}:null;
  };
  const outside=confirmation.price<zone.low||confirmation.price>zone.high;
  const observedBreakAt=Date.parse(confirmation.observed_at);
  if(confirmation.observed===true&&(!Number.isFinite(observedBreakAt)||observedBreakAt<known||observedBreakAt>now))return null;
  const priorBreak=confirmation.observed===true;
  const beyondConfirmation=side*(close-confirmation.price)>0;
  const currentInZone=close>=zone.low&&close<=zone.high;
  const frameLabel={'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly'}[row.chart?.interval]||'chart';
  const repeatRule=priorBreak?'The earlier break '+(side>0?'above ':'below ')+format(confirmation.price)+' has already been observed. For a new setup, '+(currentInZone?'require a fresh completed ':'wait for a fresh return to the watch zone, then require a new completed ')+frameLabel+' close '+(side>0?'above ':'below ')+format(confirmation.price)+'.':confirmation.rule;
  if(inside)conflicts.push('A measured opposing level lies inside this zone; wait for the zone and barrier to resolve.');
  if(outside)conflicts.push('The confirmation break lies outside the pullback zone; the two entry references have separate reward/risk.');
  const timing=side>0?(close>zone.high?'await_pullback':close<zone.low?'below_zone':'in_zone'):(close<zone.low?'await_pullback':close>zone.high?'above_zone':'in_zone');
  const zoneText=format(zone.low)+'–'+format(zone.high);
  const confirmationObjective=unique.find(x=>side*(x.price-confirmation.price)>0)||null;
  return {basis,authority:'chart_research',direction:row.direction,pattern,phase,count_id:count?.id||null,selection:count?(count===preferred?'preferred':'alternate'):'measured_swing',confirmed_at:confirmed,status:inside?'barrier_in_zone':timing,
    entry_zone:{low:zone.low,high:zone.high,basis:zone.basis||'Elliott retracement geometry',ratios:zone.ratios||[],role:'conditional_watch_zone',confirmation_required:true},
    confirmation:{price:confirmation.price,rule:repeatRule,relation_to_zone:outside?'outside':'at_or_inside',state:priorBreak?'previously_observed':'awaiting_confirmation',observed:priorBreak,observed_at:priorBreak?confirmation.observed_at:null,current_price_beyond_level:beyondConfirmation,requires_new_sequence:priorBreak},confirmation_objective:confirmationObjective,
    invalidation:{price:invalid.price,basis:invalid.basis||'intrabar',reason:invalid.reason||'This price invalidates the chart scenario.'},
    objectives:unique.slice(0,3),risk_reward:economics(adverse),confirmation_risk_reward:outside?economics(confirmation.price):null,
    holding:{text:'Reassess on each completed '+({'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly'}[row.chart?.interval]||'chart')+' candle; the pattern does not determine a holding duration.'},conflicts,
    summary:(side>0?'Pullback watch zone ':'Rally watch zone ')+zoneText+'. '+(repeatRule||'Require the stated chart confirmation.')+' Scenario invalid '+(side>0?'below ':'above ')+format(invalid.price)+'.'+(first?' Watch-zone objective '+format(first.price)+'.':' No measured watch-zone objective is available.')+(outside?(confirmationObjective?' After a new confirmation, objective '+format(confirmationObjective.price)+'.':' No measured objective beyond confirmation is available.'):'')};
}

/* A concise research plan, distinct from the sleeve's unchanged execution rules.
 * Levels come from supplied orders or causally confirmed pivots. No synthetic
 * target, probability, scoring weight or trade permission is introduced. */
function setupStoredResearchBrief(row,current,sourceFresh,now=Date.now()) {
  const p=row.research_plan;
  if(!p?.brief||p.version!=='chart-plan-1'||current.authority==='recorded_strategy'||row.saved_alert)return current;
  const b=JSON.parse(JSON.stringify(p.brief)),g=b.geometry,price=setupPriceText,side=row.direction==='bullish'?1:row.direction==='bearish'?-1:0;
  // Research plans written before authority was serialized still use this
  // dedicated chart-plan store; restore its stable contract on read.
  b.authority='chart_research';if(!['bullish','bearish'].includes(b.direction))b.direction=row.direction;
  // A lifecycle terminal state outranks a freshly rebuilt candidate brief.
  // Otherwise a wick that spent the objective on the origin candle can be
  // turned back into a green conditional plan by the public focus projection.
  const terminalLabels={born_expired:'Target reached before entry',objective_reached:'Target reached',invalidated:'Plan invalidated',expired:'Entry window ended',time_expired:'Plan horizon ended',superseded:'Plan replaced',data_revision:'Chart data changed'};
  if(Object.hasOwn(terminalLabels,p.state)){
    const reason=p.reason||terminalLabels[p.state]+'. Start from a new completed chart.';
    b.decision='pass';b.label=terminalLabels[p.state];b.skip_reason=reason;b.thesis=reason;
    b.execution={state:'research',text:reason};b.entry=null;b.invalidation=null;b.objectives=[];
    b.geometry=null;b.band_geometry=null;b.confirmation_geometry=null;b.chart_levels=[];b.manual_steps=null;
    b.economics_summary=null;b.quality={...b.quality,coherent:false,complete:false,objective_measured:false};
    b.lifecycle={id:p.id,state:p.state,recorded:p.recorded===true,recorded_at:p.recorded_at,confirmed_at:p.confirmed_at,confirmation_price:p.confirmation_price??null,confirmation_observed_at:p.confirmed_observed_at||null,confirmed_bar:p.confirmed_bar||null,reason:p.reason,expires_after_bars:p.expires_after_bars,observed_bars:p.observed_bars};
    return b;
  }
  // Historical chart plans are an overlay, not authority to re-publish invalid
  // geometry after a source repair. Keep the current recalculated read when a
  // stored price, direction, or R-multiple is impossible.
  if(!g||!side||![g.entry,g.stop,g.target,g.ratio].every(Number.isFinite)||g.entry<=0||g.stop<=0||g.target<=0||g.ratio<=0||side*(g.entry-g.stop)<=0||side*(g.target-g.entry)<=0)return current;
  const storedRisk=side*(g.entry-g.stop),storedReward=side*(g.target-g.entry),storedRatio=storedReward/storedRisk,
    geometryTolerance=Math.max(1e-6,Math.abs(storedRatio)*1e-6);
  if(!(storedRisk>0&&storedReward>0&&Math.abs(storedRatio-g.ratio)<=geometryTolerance))return current;
  // Saved research maps may be carried forward only when their stop is an
  // observed structural level. ATR and other projected stops are not chart
  // invalidations; re-evaluate the current source instead of displaying them.
  const invalidationBasis=String(b.invalidation?.basis||'').toLowerCase(),geometryBasis=String(g.basis||'').toLowerCase();
  if(/atr|projection|two_r/.test(invalidationBasis)||/atr_projection|two_r_projection/.test(geometryBasis))return current;
  // The lifecycle record remains authoritative for a still-live map after
  // its trigger confirms. Requiring today's fresh-plan builder to rediscover
  // the old trigger would erase a valid confirmed plan (the trigger is now
  // behind price), while trusting the cached record forever can resurrect a
  // spent target. Rebind it to today's complete chart and the same confirmed
  // opposing pivot; retire it when that pivot was crossed after formation.
  const chartCurrent=sourceFresh&&row.chart?.symbol===row.symbol&&row.chart?.context_only!==true&&row.technicals?.status==='ready'&&row.input_status?.current!==false&&row.curation?.chart_current!==false&&!row.desk_read?.considered?.some(x=>x.id==='freshness'&&x.status==='stale');
  if(b.entry?.basis==='confirmed_shelf_retest'){
    if(!chartCurrent)return current;
    const tickSize=row.chart?.tick_size??row.technicals?.metrics?.tick_size??null,knownStop=(row.technicals?.pivots||[]).some(x=>Number.isFinite(x.price)&&Number.isFinite(Date.parse(x.confirmed_at))&&Date.parse(x.confirmed_at)<=now&&(x.price===g.stop||b.invalidation?.basis==='confirmed_retest_boundary'&&setupPlanInvalidationThreshold(side,x.price,tickSize).price===g.stop));
    const bars=Array.isArray(row.chart?.bars)?row.chart.bars:[],targetKind=side>0?'resistance':'support',validTargetLevel=x=>x?.kind===targetKind&&x.price===g.target&&Number.isInteger(x.index)&&x.index>=0&&x.index<bars.length&&Number.isFinite(Date.parse(x.confirmed_at))&&Date.parse(x.confirmed_at)<=now;
    const knownTarget=bars.some(x=>x[side>0?2:3]===g.target&&Number.isFinite(Date.parse(x[0]))&&Date.parse(x[0])<=now)||(row.technicals?.pivots||[]).some(validTargetLevel)||(row.technicals?.levels||[]).some(validTargetLevel);
    if(!knownStop||!knownTarget)return current;
    const live=['watching','confirmed'].includes(p.state)&&!['stale','gap'].includes(p.data_status),
      low=Number.isFinite(b.entry.acceptable_low)?b.entry.acceptable_low:Number.isFinite(p.acceptable_low)?p.acceptable_low:g.entry,
      high=Number.isFinite(b.entry.acceptable_high)?b.entry.acceptable_high:Number.isFinite(p.acceptable_high)?p.acceptable_high:g.entry,
      bounded=setupQualifiedEntryBand(side,g.entry,g.stop,g.target,row.technicals?.metrics?.atr14,{low,high},tickSize);
    if(!bounded?.band)return current;
    if(p.state==='confirmed'){
      const confirmedBar=bars.find(bar=>bar?.[0]===p.confirmed_bar),confirmedAt=Date.parse(p.confirmed_at),observedAt=Date.parse(p.confirmed_observed_at),recordedAt=Date.parse(p.recorded_at),confirmation=Number(p.confirmation_price),transition=(p.transitions||[]).findLast?.(event=>event?.state==='confirmed'&&event?.from==='watching')||(p.transitions||[]).slice().reverse().find(event=>event?.state==='confirmed'&&event?.from==='watching'),thresholds=setupPlanEntryThresholds(side,g.entry,tickSize,'structural_retest'),confirmationTick=setupPlanTickSize(confirmation,tickSize),barTime=Date.parse(confirmedBar?.[0]),close=confirmedBar?.[4],lowValue=confirmedBar?.[3],highValue=confirmedBar?.[2],band=bounded.band;
      const validConfirmation=!!confirmedBar&&Number.isFinite(recordedAt)&&Number.isFinite(observedAt)&&observedAt>recordedAt&&observedAt<=now&&(!Number.isFinite(confirmedAt)||confirmedAt>recordedAt&&confirmedAt<=now)&&Number.isFinite(barTime)&&p.confirmed_bar>p.origin_bar&&Number.isFinite(confirmation)&&Number.isFinite(close)&&close===confirmation&&Number.isFinite(confirmationTick)&&setupPlanTickAligned(confirmation,confirmationTick)&&confirmation>=band.low&&confirmation<=band.high&&side*(confirmation-thresholds.close.price)>=0&&Number.isFinite(lowValue)&&Number.isFinite(highValue)&&(side>0?lowValue<=thresholds.test.price:highValue>=thresholds.test.price)&&!(side>0?highValue>=g.target:lowValue<=g.target)&&transition?.bar_at===p.confirmed_bar&&transition?.close===confirmation&&Number.isFinite(Date.parse(transition.observed_at))&&Date.parse(transition.observed_at)>recordedAt&&Date.parse(transition.observed_at)<=now;
      if(!validConfirmation)return current;
    }
    const frame={'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly'}[p.interval]||'chart',band=bounded.band,entryMethod='structural_retest',rule=p.state==='confirmed'?'The retest confirmed on a completed '+frame+' candle: price touched $'+price(g.entry)+' and closed back '+(side>0?'above':'below')+' it.':setupEntryConditionText(side,frame,row.technicals?.metrics?.close,g.entry,band,entryMethod,tickSize,row);
    b.entry={...b.entry,acceptable_low:band?.low??low,acceptable_high:band?.high??high,display_band:band,rule_text:rule,text:p.state==='confirmed'?'Retest confirmed; the '+(side>0?'share-buy':'bearish price')+' condition was met at $'+price(g.entry)+'.':setupEntryConfirmationText(side,frame,g.entry,band,entryMethod,tickSize)};
    b.quality={...b.quality,entry_method:entryMethod};
    b.lifecycle={id:p.id,state:p.state,recorded:p.recorded===true,recorded_at:p.recorded_at,confirmed_at:p.confirmed_at,confirmation_price:p.confirmation_price??null,confirmation_observed_at:p.confirmed_observed_at||null,confirmed_bar:p.confirmed_bar||null,reason:p.reason,expires_after_bars:p.expires_after_bars,observed_bars:p.observed_bars};
    b.execution={state:live?'conditional':'research',text:p.state==='confirmed'?'The retest confirmed on a later completed candle. Use the recorded entry band.':p.reason};
    b.quality={...b.quality,coherent:live};b.band_geometry=bounded.geometry;
    b.chart_levels=live?[
      {kind:'reference',price:g.entry,label:'Retest entry',...(band.low<band.high?{range:{low:band.low,high:band.high}}:{}),symbol:row.symbol,price_basis:'underlying'},
      {kind:'invalidation',price:g.stop,label:'Chart invalidation',symbol:row.symbol,price_basis:'underlying'},
      {kind:'target',price:g.target,label:'Objective 1',symbol:row.symbol,price_basis:'underlying'}
    ]:(b.chart_levels||[]).filter(x=>x.kind==='invalidation');
    if(live){
      const call=side>0?'Bullish':'Bearish',tradeAction=side<0?'Bearish stock-price plan; no trade order is included. ':'Trade action: Buy shares in your trading app only after the entry rule is met. ',
        entrySummary=p.state==='confirmed'?'The entry trigger confirmed at '+price(Number.isFinite(p.confirmation_price)?p.confirmation_price:g.entry)+'. Only enter if price remains inside '+setupEntryBandText(band)+'.':'Wait for price to '+(side<0?'rebound':'pull back')+' into '+setupEntryBandText(band)+'; require a completed '+frame+' candle to test '+price(g.entry)+' and close '+(side>0?'above':'below')+' it.',
        target=b.objectives?.[0]?.price;
      b.thesis=row.symbol+': '+call+' call. '+tradeAction+entrySummary+(Number.isFinite(target)?' Target '+price(target)+'.':'')+' Invalidation: a completed '+frame+' close '+(side>0?'below ':'above ')+price(g.stop)+'.';
    }else b.thesis=row.symbol+': '+(p.reason||'This stored price plan is no longer current.');
    if(!live){b.decision='pass';b.label='Retest plan ended';b.skip_reason=p.reason;b.entry=null;b.objectives=[];b.geometry=null;b.band_geometry=null;}
    if(live){const canonical=setupApplyManualExecutionContract(b,row);if(!canonical)return current;const expiry=Number.isInteger(p.expires_after_bars)&&p.expires_after_bars>0?p.expires_after_bars:5;canonical.holding={text:p.state==='confirmed'?'Reassess each completed '+frame+' candle; close at the target '+setupPlanPriceText(canonical.objectives[0].price,tickSize)+' or if a completed close reaches invalidation '+setupPlanPriceText(canonical.invalidation.price,tickSize)+'.':'Entry trigger expires after '+expiry+' later completed '+frame+' candles. After entry, close at target '+setupPlanPriceText(canonical.objectives[0].price,tickSize)+' or at invalidation '+setupPlanPriceText(canonical.invalidation.price,tickSize)+'.'};return canonical;}
    return b;
  }
  if(!chartCurrent||!['watching','confirmed','missed'].includes(p.state))return current;
  const m=row.technicals?.metrics||{},close=Number.isFinite(m.close)?m.close:null,target=g?.target,targetKind=side>0?'resistance':'support',pivots=Array.isArray(row.technicals?.pivots)?row.technicals.pivots:[],pivot=pivots.find(x=>x?.kind===targetKind&&Number.isFinite(x.price)&&Math.abs(x.price-target)<=Math.max(Math.abs(target),1)*1e-9);
  if(!pivot||close===null||side*(target-close)<=0)return current;
  const reachedAt=typeof pivot.first_reached_at==='string'?Date.parse(pivot.first_reached_at):NaN;
  if(pivot.reached_after_pivot===true&&(!Number.isFinite(reachedAt)||reachedAt<=now))return current;
  const pivotAt=typeof pivot.pivot_at==='string'?Date.parse(pivot.pivot_at):NaN,bars=Array.isArray(row.chart?.bars)?row.chart.bars:[];
  if(Number.isFinite(pivotAt)&&bars.some(bar=>{const at=typeof bar?.[0]==='string'?Date.parse(bar[0]):NaN,extreme=bar?.[side>0?2:3];return Number.isFinite(at)&&at>pivotAt&&at<=now&&Number.isFinite(extreme)&&(side>0?extreme>=target:extreme<=target);}))return current;
  if(p.state==='watching'&&side*(close-g.entry)>0)return current;
  if(p.state==='confirmed'&&side*(close-g.stop)<=0)return current;
  const validObjectives=(b.objectives||[]).filter(x=>x?.basis!=='two_r_projection'&&Number.isFinite(x?.price)&&x.price>0&&side*(x.price-g.entry)>0);
  if(!validObjectives.length)return current;
  b.objectives=validObjectives;
  const goodInput=sourceFresh&&row.input_status?.current!==false&&row.curation?.chart_current!==false&&!['stale','gap'].includes(p.data_status);
  const live=['watching','confirmed'].includes(p.state)&&goodInput;
  const labels={watching:side>0?'Breakout watch':side<0?'Breakdown watch':'Price trigger watch',confirmed:'Chart confirmed',missed:'Entry missed',invalidated:'Plan invalidated',objective_reached:'Objective reached',expired:'Plan expired',superseded:'Plan replaced',data_revision:'Data changed'};
  const minR=SETUP_PLAN_MIN_REWARD_RISK,triggerRisk=side*(g.entry-g.stop),triggerReward=side*(g.target-g.entry);
  if(!(triggerRisk>0&&triggerReward>0&&triggerReward/triggerRisk>=minR))return current;
  const originalLow=Number.isFinite(p.acceptable_low)?p.acceptable_low:g.entry,originalHigh=Number.isFinite(p.acceptable_high)?p.acceptable_high:g.entry,
    tickSize=row.chart?.tick_size??row.technicals?.metrics?.tick_size??null,
    bounded=setupQualifiedEntryBand(side,g.entry,g.stop,g.target,row.technicals?.metrics?.atr14,{low:originalLow,high:originalHigh},tickSize);
  if(!bounded?.band)return current;
  const displayBand=bounded.band,band=setupEntryBandText(displayBand),bandGeometry=bounded.geometry;
  const frame={'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly'}[p.interval]||'chart';
  const retest=b.quality?.entry_method==='structural_retest'||b.entry?.basis==='confirmed_shelf_retest';
  const entryMethod=retest?'structural_retest':'breakout',entryRule=p.state==='confirmed'?'A completed '+frame+' close confirmed at $'+price(p.confirmation_price)+'.':setupEntryConditionText(side,frame,row.technicals?.metrics?.close,g.entry,displayBand,entryMethod,tickSize,row);
  b.entry={...b.entry,acceptable_low:displayBand.low,acceptable_high:displayBand.high,display_band:displayBand,rule_text:entryRule,text:retest?setupEntryConfirmationText(side,frame,g.entry,displayBand,entryMethod,tickSize):'Require a completed '+frame+' close '+(side>0?'above ':'below ')+price(g.entry)+'; enter only inside '+band+'.'};
  b.quality={...b.quality,entry_method:entryMethod};
  if(b.invalidation)b.invalidation={...b.invalidation,text:'Cancel this '+(side>0?'bullish':'bearish')+' chart plan on a completed '+frame+' close '+(side>0?'below ':'above ')+price(g.stop)+'.'};
  b.objectives=b.objectives.map(x=>({...x,text:'Recorded '+(side>0?'resistance':'support')+' objective at '+price(x.price)+'.'}));
  b.lifecycle={id:p.id,state:p.state,recorded:p.recorded===true,recorded_at:p.recorded_at,confirmed_at:p.confirmed_at,confirmation_price:p.confirmation_price??null,confirmation_observed_at:p.confirmed_observed_at||null,last_checked_at:p.last_checked_at,reason:p.reason,expires_after_bars:p.expires_after_bars,observed_bars:p.observed_bars};
  b.confirmation_geometry=null;
  if(g&&Number.isFinite(g.ratio))g.break_even_win_rate_pct=setupBreakEvenWinRate(g.ratio);
  b.band_geometry=bandGeometry;
  b.economics_summary=(b.direction==='bearish'?'Stock prices only; no option price or option outcome is calculated. ':'')+(b.band_geometry?'Gross reward/risk: '+g.ratio.toFixed(2)+'R at the trigger and '+b.band_geometry.ratio.toFixed(2)+'R at the least favorable entry ('+price(b.band_geometry.entry)+'). Gross break-even hit rate: '+g.break_even_win_rate_pct.toFixed(1)+'% at the trigger and '+b.band_geometry.break_even_win_rate_pct.toFixed(1)+'% at the band edge.': 'Gross mapped reward/risk: '+g.ratio.toFixed(2)+'R. Gross break-even hit rate: '+g.break_even_win_rate_pct.toFixed(1)+'%.');
  if(Number.isFinite(p.confirmation_price)){
    const risk=side*(p.confirmation_price-g.stop),reward=side*(g.target-p.confirmation_price);
    if(risk>0&&reward>0){const ratio=reward/risk;b.confirmation_geometry={entry:p.confirmation_price,stop:g.stop,target:g.target,risk_per_unit:risk,reward_per_unit:reward,ratio,break_even_win_rate_pct:setupBreakEvenWinRate(ratio),basis:'observed_confirmation_close_not_fill',costs_included:false};}
  }
  b.decision=live?'conditional':goodInput?'pass':'unavailable';b.label=goodInput?(labels[p.state]||'Plan review'):'Update needed';
  const call=side>0?'Bullish':side<0?'Bearish':'Directional';
  const tradeAction=side<0?'Bearish stock-price plan; no trade order is included. ':'';
  b.thesis=row.symbol+': '+(!goodInput?'Update the completed chart and refresh this price map.':p.state==='watching'?call+' call. '+tradeAction+'Trigger on a completed '+frame+' close '+(side>0?'above ':'below ')+price(g.entry)+'; enter inside '+band+'. Objective '+price(g.target)+'; invalidate on a completed close '+(side>0?'below ':'above ')+price(g.stop)+'.':p.state==='confirmed'?call+' call confirmed at '+price(p.confirmation_price)+'. '+tradeAction+'Entry zone '+band+'; objective '+price(g.target)+'; invalidation '+price(g.stop)+'.':p.reason);
  b.why=current.why?.length?current.why:b.why;
  const opposing=(row.desk_read?.conflicts||[]).map(x=>setupPlainMarketConflict(x,side)).slice(0,2);
  b.tradeoff=[current.tradeoff,...opposing].filter(Boolean).filter((text,index,all)=>all.indexOf(text)===index).join(' ');
  b.holding=live?{text:p.state==='confirmed'?'Research horizon: reassess each completed '+frame+' candle; invalidate on a close '+(side>0?'below ':'above ')+price(g.stop)+' and review the objective at '+price(g.target)+'.':'Trigger window: 5 later completed '+frame+' candles. After confirmation, reassess at invalidation '+price(g.stop)+' and objective '+price(g.target)+'.'}:null;
  b.execution={...current.execution,text:live?b.entry.rule_text:b.thesis};
  b.skip_reason=live?null:b.thesis;
  b.quality={...b.quality,coherent:live,context_conflicts:current.quality?.context_conflicts||0,context_labels:current.quality?.context_labels||[],distance_atr:Number.isFinite(row.technicals?.metrics?.atr14)&&row.technicals.metrics.atr14>0?Math.abs(g.entry-row.technicals.metrics.close)/row.technicals.metrics.atr14:null};
  // Rebuild the displayed levels from the same validated geometry as the
  // plan. Older saved plans may have an empty chart_levels array, and should
  // not leave the entry band visible only in the side panel.
  b.chart_levels=live?[
    {kind:'reference',price:g.entry,label:p.state==='confirmed'?'Entry threshold':'Close trigger',...(displayBand.low<displayBand.high?{range:{low:displayBand.low,high:displayBand.high}}:{}),symbol:row.symbol,price_basis:'underlying'},
    {kind:'invalidation',price:g.stop,label:'Chart invalidation',symbol:row.symbol,price_basis:'underlying'},
    {kind:'target',price:g.target,label:'Objective 1',symbol:row.symbol,price_basis:'underlying'}
  ]:[];
  if(live){const canonical=setupApplyManualExecutionContract(b,row);if(!canonical)return current;const expiry=Number.isInteger(p.expires_after_bars)&&p.expires_after_bars>0?p.expires_after_bars:5;canonical.holding={text:p.state==='confirmed'?'Reassess each completed '+frame+' candle; close at the target '+setupPlanPriceText(canonical.objectives[0].price,tickSize)+' or if a completed close reaches invalidation '+setupPlanPriceText(canonical.invalidation.price,tickSize)+'.':'Entry trigger expires after '+expiry+' later completed '+frame+' candles. After entry, close at target '+setupPlanPriceText(canonical.objectives[0].price,tickSize)+' or at invalidation '+setupPlanPriceText(canonical.invalidation.price,tickSize)+'.'};return canonical;}
  return b;
}
// Keep confirmed pattern objectives visible when the stricter swing-level
// plan gate has no forward target. A pattern projection is context, not a
// substitute for a confirmed swing objective or a qualified plan target.
function setupPatternObjectiveContext(row,side,entry,invalidation,close,now=Date.now()) {
  if(!side||!Number.isFinite(close)||close<=0)return null;
  const names={cup_handle:'cup-and-handle',inverse_head_shoulders:'inverse head-and-shoulders',double_bottom:'double-bottom',double_top:'double-top',head_shoulders:'head-and-shoulders',falling_wedge:'falling-wedge',rising_wedge:'rising-wedge',rectangle:'rectangle',bull_flag:'bull-flag',bear_flag:'bear-flag',bull_pennant:'bull-pennant',bear_pennant:'bear-pennant'};
  const direction=side>0?'up':'down',patterns=(row.technicals?.patterns||[]).filter(pattern=>{
    if(pattern?.state!=='confirmed_break'||pattern.direction!==direction||!Number.isFinite(pattern.measured_target_price)||pattern.measured_target_price<=0)return false;
    const at=Date.parse(pattern.confirmed_at||pattern.break_at||'');
    return Number.isFinite(at)&&at<=now;
  }).map(pattern=>({...pattern,target:pattern.measured_target_price,reached:pattern.measured_target_status==='reached'||side*(pattern.measured_target_price-close)<=0}))
    .sort((a,b)=>Math.abs(a.target-close)-Math.abs(b.target-close));
  const pattern=patterns[0];if(!pattern)return null;
  const name=names[pattern.kind]||String(pattern.kind||'chart pattern').replaceAll('_','-'),target=setupPriceText(pattern.target);
  if(pattern.reached)return {state:'reached',text:`The confirmed ${name} measured objective at ${target} has already been reached; it is not a forward target.`};
  const trigger=Number.isFinite(entry?.price)&&entry.price>0?entry.price:close,stop=Number.isFinite(invalidation?.price)&&invalidation.price>0?invalidation.price:null;
  const risk=stop===null?null:side*(trigger-stop),reward=side*(pattern.target-trigger),ratio=risk>0&&reward>0?reward/risk:null;
  let economics='';
  if(ratio!==null)economics=` At the prospective trigger ${setupPriceText(trigger)}, it offers ${ratio.toFixed(2)}R to invalidation ${setupPriceText(stop)}${ratio<SETUP_PLAN_MIN_REWARD_RISK?`, below the ${SETUP_PLAN_MIN_REWARD_RISK.toFixed(1)}R minimum`:''}.`;
  else if(reward<=0)economics=` The projection is not beyond the prospective trigger ${setupPriceText(trigger)}.`;
  return {state:'ahead',target:pattern.target,ratio,text:`The confirmed ${name} breakout projects ${target}; that measured objective is not a confirmed swing target.${economics}`};
}

// A second entry geometry for an already directional chart: return to a
// measured shelf, then hold/reject it. Stops are independent confirmed levels;
// targets are observed prices, never an R-multiple manufactured as a target.
function setupRetestCandidate(row,now=Date.now()) {
  const m=row.technicals?.metrics||{},side=row.direction==='bullish'?1:row.direction==='bearish'?-1:0;
  const close=m.close,atr=m.atr14,pos=x=>Number.isFinite(x)&&x>0;
  const bars=(row.chart?.bars||[]).filter(b=>Number.isFinite(Date.parse(b[0]))&&Date.parse(b[0])<=now);
  if(!side||!pos(close)||!pos(atr)||bars.length<20)return null;
  const supported=side>0?m.structure==='higher_highs_higher_lows'&&!m.structure_breach||m.structure_breach==='bearish_failed':m.structure==='lower_highs_lower_lows'&&!m.structure_breach||m.structure_breach==='bullish_failed';
  if(!supported)return null;
  const levels=(row.technicals?.pivots||[]).filter(p=>pos(p.price)&&Number.isInteger(p.index)&&p.index>=0&&p.index>=bars.length-60&&p.index<bars.length&&Number.isFinite(Date.parse(p.confirmed_at))&&Date.parse(p.confirmed_at)<=now);
  // The retest stop/shelf contract is pivot-based, but first objectives must
  // include every confirmed structural barrier exposed to the reader. Omitting
  // technicals.levels can skip a nearer support/resistance and overstate R.
  const targetLevels=[];
  for(const p of [...levels,...(row.technicals?.levels||[])]){
    if(!pos(p.price)||!['support','resistance'].includes(p.kind)||!Number.isInteger(p.index)||p.index<0||p.index>=bars.length||!Number.isFinite(Date.parse(p.confirmed_at))||Date.parse(p.confirmed_at)>now)continue;
    if(!targetLevels.some(x=>x.kind===p.kind&&Math.abs(x.price-p.price)<=Math.max(x.price,p.price,1)*1e-9))targetLevels.push(p);
  }
  const recent=bars.slice(-20),extreme=side>0?Math.max(...recent.map(b=>b[2])):Math.min(...recent.map(b=>b[3]));
  if(!pos(extreme))return null;
  const candidates=[];
  for(const shelf of levels){
    // Pullbacks sit behind the current price, within three normal ranges.
    const distance=side*(close-shelf.price);if(distance<0||distance>3*atr)continue;
    const stop=levels.filter(p=>side*(shelf.price-p.price)>=.5*atr).sort((a,b)=>side*(b.price-a.price))[0];
    if(!stop)continue;
    const opposing=side>0?'resistance':'support';
    const objectives=[{price:extreme,basis:'observed_range_extreme',text:'Retest of the observed 20-bar '+(side>0?'high':'low')+' at '+setupPriceText(extreme)+'.'},...targetLevels.filter(p=>p.kind===opposing&&side*(p.price-close)>0).map(p=>({price:p.price,basis:'confirmed_pivot',confirmed_at:p.confirmed_at,text:'Next confirmed '+opposing+' at '+setupPriceText(p.price)+'.'}))].filter(p=>side*(p.price-shelf.price)>0).sort((a,b)=>side*(a.price-b.price));
    const target=objectives[0];if(!target)continue;
    const risk=side*(shelf.price-stop.price),reward=side*(target.price-shelf.price),ratio=reward/risk;
    if(!(risk>0&&ratio>=SETUP_PLAN_MIN_REWARD_RISK))continue;
    const frame={'1d':'daily','1h':'hourly','1wk':'weekly','4h':'four-hour'}[row.chart?.interval]||'chart';
    const roleFlip=shelf.kind!== (side>0?'support':'resistance');
    const name=roleFlip?'Break retest':'Pullback to '+(side>0?'support':'resistance');
    candidates.push({name,distance_atr:distance/atr,ratio,
      entry:{price:shelf.price,basis:'confirmed_shelf_retest',confirmed_at:shelf.confirmed_at,text:(side>0?'Buy shares after the pullback':'Buy a put after the stock rebound')+' tests '+setupPriceText(shelf.price)+' and a completed '+frame+' candle closes '+(side>0?'above':'below')+' it inside the entry band.',condition:'A new '+frame+' candle must test '+setupPriceText(shelf.price)+' and close '+(side>0?'above':'below')+' it inside the entry band. No entry on the approach alone.'},
      invalidation:{price:stop.price,basis:'confirmed_retest_boundary',confirmed_at:stop.confirmed_at,text:'Exit on a completed '+frame+' close '+(side>0?'below':'above')+' '+setupPriceText(stop.price)+', the next confirmed structural boundary.'},target});
  }
  // Prefer a reachable entry; use economics only to resolve equal distances.
  candidates.sort((a,b)=>a.distance_atr-b.distance_atr||b.ratio-a.ratio);
  return candidates[0]||null;
}

function setupDecisionBrief(row,plan,now,sourceFresh) {
  const num=x=>typeof x==='number'&&Number.isFinite(x),pos=x=>num(x)&&x>0;
  const price=x=>pos(x)?setupPriceText(x):null;
  const time=x=>typeof x==='string'&&Number.isFinite(Date.parse(x))?Date.parse(x):null;
  const frameNames={'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly','1w':'weekly','10m':'ten-minute'},
    frame=frameNames[row.chart?.interval]||row.horizon||'chart';
  const side=row.direction==='bullish'?1:row.direction==='bearish'?-1:0,verb=side>0?'above':'below';
  const e=row.on_demand?null:(row.evidence||[]).find(x=>x.id===row.primary_evidence_id)||row.evidence?.[0];
  const m=row.technicals?.metrics||{},close=m.close;
  if(row.saved_alert===true){
    const recordedAt=time(row.alert_at)||time(row.observed_at)||time(e?.observed_at);
    const archived=row.recorded_brief||row.action_plan?.brief;
    const historical=archived?JSON.parse(JSON.stringify(archived)):recordedAt!==null?setupDecisionBrief(
      {...row,saved_alert:false,action_plan:null,curation:{...row.curation,chart_current:true},desk_read:{...row.desk_read,considered:(row.desk_read?.considered||[]).filter(x=>x.id!=='freshness')}},
      {...plan,state:e?.held?'manage':e?.pending_order?'pending':e?'waiting':'research'},recordedAt,true):null;
    if(historical)return {...historical,decision:'saved',label:plan.state==='ended'?'Entry window ended · recorded plan':'Recorded plan',recorded_decision:historical.recorded_decision||historical.decision,recorded_at:recordedAt!==null?new Date(recordedAt).toISOString():null,
      recorded_manual_steps:historical.manual_steps||null,recorded_chart_levels:historical.chart_levels||[],manual_steps:null,chart_levels:[],
      execution:{state:plan.state==='ended'?'ended':'saved',text:(plan.state==='ended'?'Entry window ended. Do not reuse this recorded entry window. ':'')+'Historical read'+(recordedAt!==null?' recorded '+new Date(recordedAt).toISOString():'')+'. Open the current setup for present entry conditions.'},quality:{...historical.quality,coherent:false}};
  }
  if(['manage','pending'].includes(plan.state)){
    // A time/rule exit is a complete management contract even without a target.
    // Never replace an owned stop or entry with a fresh discretionary chart map.
    const held=plan.state==='manage',levels=plan.chart_levels.filter(l=>['Recorded paper entry','Strategy stop','Strategy target'].includes(l.label));
    const fill=levels.find(l=>l.kind==='entry'),stop=levels.find(l=>l.kind==='invalidation'),target=levels.find(l=>l.kind==='target');
    const entry=fill?{price:fill.price,text:'Recorded fill '+price(fill.price)+'.',basis:'actual_paper_fill',condition:plan.confirmation.text}:null;
    const invalidation=['strategy_stop','strategy_distance'].includes(plan.invalidation.kind)?{price:stop?.price??null,text:plan.invalidation.text,basis:plan.invalidation.kind}:null;
    return {authority:'recorded_strategy',decision:held?'manage':'pending',label:held?'Manage position':'Order pending',
      thesis:row.symbol+': '+(held?'manage the existing paper position.':'resolve the existing order before another entry.'),
      why:[plan.strategy_name,plan.strategy_summary].filter(Boolean),entry,invalidation,
      objectives:target?[{price:target.price,text:'Strategy target '+price(target.price)+'.',basis:'supplied_strategy_target'}]:[],
      holding:{text:plan.answers.how_long},tradeoff:plan.exit.text,geometry:plan.risk_reward?{...plan.risk_reward,stop:plan.risk_reward.stop}:null,
      execution:{state:held?'manage':'pending',text:plan.answers.when_to_exit},
      quality:{coherent:false,complete:!!plan.exit.text,directional_support:false,objective_measured:!!target,distance_atr:null},skip_reason:null,chart_levels:levels};
  }
  const knownPivot=p=>pos(p.price)&&['support','resistance'].includes(p.kind)&&time(p.confirmed_at)!==null&&time(p.confirmed_at)<=now;
  const pivots=(row.technicals?.pivots||[]).filter(knownPivot);
  const shelves=[...pivots,...(row.technicals?.levels||[]).filter(knownPivot)];
  const adverseKind=side>0?'support':'resistance',opposingKind=side>0?'resistance':'support';
  // Keep the latest confirmed opposite swing as the default invalidation.
  const adverse=[...pivots].filter(p=>p.kind===adverseKind&&side*(close-p.price)>0).sort((a,b)=>b.index-a.index)[0];
  const ahead=shelves.filter(p=>p.kind===opposingKind&&side*(p.price-close)>0).sort((a,b)=>side*(a.price-b.price));
  const first=ahead[0],next=first?ahead.filter(p=>side*(p.price-first.price)>Math.max(first.price,1)*1e-9):[];
  const lastBar=row.chart?.bars?.at(-1),priorBar=row.chart?.bars?.at(-2);
  const reclaim=first&&Array.isArray(lastBar)&&pos(lastBar[side>0?2:3])&&side*(lastBar[side>0?2:3]-first.price)>0&&side*(close-first.price)<0;
  const lastMove=Array.isArray(priorBar)&&pos(priorBar[4])?100*(close/priorBar[4]-1):null;
  const adverseCandle=side>0?m.candle?.direction==='down':m.candle?.direction==='up';
  const candleText=lastMove!==null?'The latest '+frame+' close '+(lastMove>=0?'rose ':'fell ')+Math.abs(lastMove).toFixed(2)+'%':m.candle?.direction==='down'?'The latest '+frame+' candle finished below its open':m.candle?.direction==='up'?'The latest '+frame+' candle finished above its open':null;
  // A confirmed opposing pivot is a current barrier when it is still ahead of
  // price. Crossing it earlier does not erase its role after price returns
  // below it; the `ahead` filter above already excludes targets behind price.
  const objectives=[];for(const p of next)if(!objectives.some(o=>Math.abs(o.price-p.price)<=Math.max(p.price,1)*1e-9))objectives.push({price:p.price,text:'Next confirmed '+opposingKind+' at '+price(p.price)+'.',basis:'confirmed_pivot',confirmed_at:p.confirmed_at});
  const stale=row.desk_read?.considered?.find(x=>x.id==='freshness')?.status==='stale'||row.curation?.chart_current===false;
  if(row.on_demand===true&&!side){
    const currentChart=sourceFresh&&!stale&&row.chart?.symbol===row.symbol&&row.chart?.context_only!==true&&row.technicals?.status==='ready'&&pos(close);
    const reason=currentChart?(row.direction_reason||'Structure and trend are balanced inside the current swing range. Set direction on the next completed break of that range.'):'Load the matching completed chart to set a directional trigger.';
    const brief={authority:'chart_research',decision:currentChart?'pass':'unavailable',label:currentChart?'Direction pending':'Chart update needed',
      thesis:row.symbol+': '+reason,why:[],entry:null,invalidation:null,objectives:[],holding:null,tradeoff:'',geometry:null,band_geometry:null,economics_summary:null,
      execution:{state:currentChart?'research':'unavailable',text:reason},
      quality:{coherent:false,complete:false,directional_support:false,objective_measured:false,distance_atr:null,context_conflicts:0,context_labels:[]},skip_reason:reason,chart_levels:[]};
    return setupStoredResearchBrief(row,brief,sourceFresh,now);
  }
  const usable=sourceFresh&&!stale&&row.chart?.symbol===row.symbol&&row.chart?.context_only!==true&&row.technicals?.status==='ready'&&pos(close)&&!!side;
  const riskSwing=setupRiskPivotExplanation(row,now);
  const breached=(side>0?m.structure_breach==='bullish_failed':m.structure_breach==='bearish_failed')||riskSwing?.state==='failed';
  const opposed=side>0?m.structure==='lower_highs_lower_lows'&&!m.structure_breach:m.structure==='higher_highs_higher_lows'&&!m.structure_breach;
  const aligned=side>0?m.structure==='higher_highs_higher_lows'&&!m.structure_breach:m.structure==='lower_highs_lower_lows'&&!m.structure_breach;
  const improving=side>0?m.structure_breach==='bearish_failed':m.structure_breach==='bullish_failed';
  const trend=pos(m.sma50)?side*(close-m.sma50):null;
  const supplied=plan.risk_reward,actual=!!supplied;
  let entry=actual?{price:supplied.entry,text:(plan.state==='manage'?'Recorded fill ':'Strategy reference ')+price(supplied.entry)+'.',basis:'supplied_strategy_levels',condition:plan.confirmation.text}:first?{price:first.price,text:'Require a completed '+frame+' close '+verb+' '+price(first.price)+(reclaim?(side>0?' to reclaim the level lost inside the latest candle.':' to confirm the break below support tested inside the latest candle.'):'.'),basis:reclaim?'confirmed_pivot_reclaim':'confirmed_pivot_break',condition:'Completed '+frame+' close '+verb+' '+price(first.price)+'.',confirmed_at:first.confirmed_at}:null;
  let invalidation=actual?{price:supplied.stop,text:'Strategy stop '+price(supplied.stop)+'.',basis:'supplied_strategy_stop'}:adverse&&side*(close-adverse.price)>0?{price:adverse.price,text:'Cancel this '+(side>0?'bullish':'bearish')+' chart plan on a completed '+frame+' close '+(side>0?'below ':'above ')+price(adverse.price)+'.',basis:'latest_confirmed_opposite_swing',confirmed_at:adverse.confirmed_at}:null;
  let targets=actual?[{price:supplied.target,text:'Strategy target '+price(supplied.target)+'.',basis:'supplied_strategy_target'}]:objectives.slice(0,2);
  // An old conditional map can contain a mathematically signed but impossible
  // downside objective. Remove invalid targets before choosing its risk model.
  targets=targets.filter(x=>pos(x.price)&&(!entry||side*(x.price-entry.price)>0));
  targets=targets.filter(x=>pos(x.price)&&(!entry||side*(x.price-entry.price)>0));
  let selectedRetest=null;
  const originalRisk=entry&&invalidation?side*(entry.price-invalidation.price):0,originalReward=entry&&targets[0]?side*(targets[0].price-entry.price):0;
  if(!actual&&usable&&!breached&&!(originalRisk>0&&originalReward/originalRisk>=SETUP_PLAN_MIN_REWARD_RISK)){
    selectedRetest=setupRetestCandidate(row,now);
    if(selectedRetest){entry=selectedRetest.entry;invalidation=selectedRetest.invalidation;targets=[selectedRetest.target];}
  }
  const risk=entry&&invalidation&&pos(entry.price)&&pos(invalidation.price)?side*(entry.price-invalidation.price):null,reward=entry&&targets[0]&&pos(targets[0].price)?side*(targets[0].price-entry.price):null;
  let geometry=risk>0&&reward>0?{entry:entry.price,stop:invalidation.price,target:targets[0].price,risk_per_unit:risk,reward_per_unit:reward,ratio:reward/risk,...(!actual?{break_even_win_rate_pct:setupBreakEvenWinRate(reward/risk)}:{}),upside_pct:100*reward/entry.price,downside_pct:100*risk/entry.price,basis:actual?'supplied_strategy_levels':'conditional_confirmed_pivots',costs_included:false}:null;
  const patternObjective=setupPatternObjectiveContext(row,side,entry,invalidation,close,now);
  let complete=!!geometry;const edge=complete&&geometry.ratio>=SETUP_PLAN_MIN_REWARD_RISK;
  const reasons=[];
  if(e?.score_basis==='predicted_net_qqq_excess'&&num(e.score)&&num(e.score_threshold))reasons.push('The '+(e.strategy_name||'daily model')+' selected '+row.symbol+' at '+(e.score*100).toFixed(2)+'% estimated excess vs QQQ, compared with its '+(e.score_threshold*100).toFixed(2)+'% threshold.');
  else if(e?.features&&num(e.features.balance))reasons.push('The '+frame+' Tensor trend balance is '+e.features.balance+'; its improvement rule selected this stock.');
  else if(row.ranker&&num(row.ranker.opp))reasons.push('ChartsLector opportunity rank: '+row.ranker.opp.toFixed(1)+'/100 in its 55-name daily universe.');
  if(aligned)reasons.push((side>0?'Higher highs and higher lows':'Lower highs and lower lows')+' support '+(side>0?'a rise':'a fall')+(trend!==null?(trend>0?'; price also holds on the favorable side of its '+(row.chart?.interval==='1d'?'50-day':'50-bar')+' average.':'; price has not regained the favorable side of its '+(row.chart?.interval==='1d'?'50-day':'50-bar')+' average.') :'.'));
  else if(improving)reasons.push('Price broke the last opposing swing; the reversal trigger is active while the new structure builds.');
  else if(opposed&&entry)reasons.push('Countertrend call: the opposing swing structure remains intact. Trigger only on the stated completed-close break.');
  if(pos(m.relative_volume))reasons.push((candleText?candleText+'; volume was ':'Latest '+frame+' volume is ')+m.relative_volume.toFixed(2)+'× its previous 20-bar average.');
  const countertrendTrigger=opposed&&entry&&['confirmed_pivot_break','next_bar_range_break','confirmed_pivot_reclaim'].includes(entry.basis);
  // On-demand reads do not get a persisted setup-lifecycle pass. Mirror its
  // born-expired rule: if the latest completed candle already traded the first
  // objective, no later candle can confirm this entry prospectively.
  const originBar=(row.on_demand===true||row.stage==='on_demand')&&Array.isArray(row.chart?.bars)?row.chart.bars.at(-1):null,
    originBarAt=typeof originBar?.[0]==='string'?Date.parse(originBar[0]):NaN,
    originTarget=targets[0]?.price,
    originObjectiveTouched=!!(usable&&originBar&&Number.isFinite(originBarAt)&&originBarAt<=now&&pos(originTarget)&&
      (side>0?Number.isFinite(originBar[2])&&originBar[2]>=originTarget:Number.isFinite(originBar[3])&&originBar[3]<=originTarget));
  let skip=null;
  if(!usable)skip='The matching completed '+frame+' chart is stale or missing. Refresh this chart before setting price levels.';
  else if(breached){const level=pos(riskSwing?.pivot?.price)?riskSwing.pivot.price:side>0?m.last_swing_low:m.last_swing_high;skip=riskSwing?.state==='failed'?riskSwing.text:'The '+(side>0?'rising':'falling')+' structure failed'+(pos(level)?' at '+price(level):'')+'. Reclaim with a completed '+frame+' close '+(side>0?'above':'below')+(pos(level)?' '+price(level):' the failed swing')+' to reopen the setup.';}
  else if(opposed&&!countertrendTrigger){const change=side>0?m.last_swing_high:m.last_swing_low;skip=(side>0?'Falling highs and lows oppose this bullish entry.':'Rising highs and lows oppose this bearish entry.')+' The trigger is a completed '+frame+' close '+verb+(pos(change)?' '+price(change):' the last opposing swing')+'.';}
  else if(!entry)skip='The chart has no confirmed '+(side>0?'ceiling':'floor')+' to anchor a price plan. Wait for a new swing level to form.'+(patternObjective?' '+patternObjective.text:'');
  else if(!invalidation)skip=setupRiskPivotExplanation(row,now)?.text||'Set the invalidation at a confirmed '+adverseKind+' swing before opening this chart map.';
  else if(!targets.length)skip=entry?'No confirmed price level lies beyond '+price(entry.price)+' yet. A new swing high or low must form before setting the next level.'+(patternObjective?' '+patternObjective.text:''):'A confirmed price level is needed beyond the planned entry before the chart has a complete price plan.'+(patternObjective?' '+patternObjective.text:'');
  else if(!edge)skip=geometry?'The nearest confirmed objective leaves '+geometry.ratio.toFixed(2)+'R at the trigger; this desk requires at least '+SETUP_PLAN_MIN_REWARD_RISK.toFixed(1)+'R to the first objective. Wait for a closer entry or new confirmed structure.':'The confirmed price levels do not make a usable entry plan.';
  else if(originObjectiveTouched)skip='The first objective already traded during the latest completed candle, before this on-demand entry could be confirmed. This price map has no forward target; refresh after a later completed candle.';
  else if(!(aligned||improving)&&trend!==null&&trend<0&&!countertrendTrigger)skip='Price is on the adverse side of its 50-bar average without an aligned swing trend. Reclaim that average before triggering this '+(side>0?'bullish':'bearish')+' plan.';
  let boundedEntry=null;
  if(!actual&&geometry&&geometry.ratio>=SETUP_PLAN_MIN_REWARD_RISK-1e-9){
    const tickSize=row.chart?.tick_size??row.technicals?.metrics?.tick_size??null;
    boundedEntry=setupQualifiedEntryBand(side,entry.price,invalidation.price,targets[0].price,m.atr14,null,tickSize);
    if(!boundedEntry?.band)skip=boundedEntry?.issue||'The entry zone cannot fit within half of this chart’s 14-bar average range while preserving the confirmed-close trigger, a valid price increment, and at least 2:1 reward to risk. This map is not qualified.';
    else {const displayBand=boundedEntry.band,entryMethod=selectedRetest?'structural_retest':'breakout',tickSize=row.chart?.tick_size??row.technicals?.metrics?.tick_size??null,entryRule=setupEntryConditionText(side,frame,close,entry.price,displayBand,entryMethod,tickSize,row);entry={...entry,acceptable_low:displayBand.low,acceptable_high:displayBand.high,display_band:displayBand,rule_text:entryRule,...(selectedRetest?{text:setupEntryConfirmationText(side,frame,entry.price,displayBand,entryMethod,tickSize)}:{})};}
  }
  // A rejected directional map must not leave a contradictory green entry or
  // enticing reward/risk beside the explicit pass. The raw chart stays intact.
  // A directional forecast may remain useful when its entry map fails a gate,
  // but rejected entry/target prices must not look like an order plan. Keep
  // only a current, confirmed invalidation for the forecast itself.
  if(!actual&&skip){const forecastInvalidation=usable&&!breached&&invalidation&&pos(invalidation.price)?invalidation:null;entry=null;invalidation=forecastInvalidation;targets=[];geometry=null;complete=false;}
  const coherent=usable&&!skip&&complete&&row.saved_alert!==true;
  let decision=coherent?'conditional':'pass',label=coherent?(actual?plan.status_label||'Strategy plan':selectedRetest?selectedRetest.name:reclaim?(side>0?'Reclaim trigger':'Breakdown trigger'):(side>0?'Breakout trigger':'Breakdown trigger')):'Setup not qualified';
  const state=plan.state;
  if(state==='manage'){decision='manage';label='Manage position';}
  else if(state==='pending'){decision='pending';label='Order pending';}
  else if(state==='unavailable'||!usable&&!actual){decision='unavailable';label='Chart update needed';}
  else if(state==='saved'){decision='saved';label='Recorded plan';}
  else if(state==='ended'){decision='pass';label='Entry window ended';skip='This entry window ended. A fresh eligible signal is required.';}
  const window=time(row.window_start||e?.entry_window_start),stamp=x=>new Date(x).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+' ET';
  const session=row.market_session||{},closed=session.market_open===false;
  const execution={state:decision==='pass'?'research':state==='ready'?'ready':state==='manage'?'manage':state==='pending'?'pending':window!==null&&window>now?'scheduled':closed?'market_closed':'conditional',text:decision==='pass'?(skip||plan.next_step||'No qualified price plan is available yet.'):state==='manage'?'Manage the open paper position with its recorded exit rules.':state==='pending'?'Reconcile the existing order before opening another.':window!==null&&window>now?'Paper sleeve window starts '+stamp(window)+'.':closed?'Market closed. Evaluate the next completed session before a new entry.':actual?plan.next_step:'Chart research trigger is conditional; paper entries follow each sleeve’s recorded trigger and risk check.'};
  if(state==='saved'){execution.state='saved';execution.text='Open the current setup for today’s entry condition and price map.';}
  const holding=actual?{text:plan.answers.how_long}:coherent?{text:'Chart horizon: '+(Number.isInteger(e?.hold_bars)&&e.hold_bars>0?e.hold_bars+' completed '+(frameNames[e?.hold_interval]||frame)+' bars. ':'reassess each completed '+frame+' candle. ')+'Exit at invalidation '+price(invalidation.price)+' or review the objective at '+price(targets[0].price)+(e?'. Strategy exit: '+plan.answers.how_long+'.':'')}:null;
  const horizonBars=Number.isInteger(e?.hold_bars)&&e.hold_bars>0?e.hold_bars:({'1h':6,'4h':6,'1d':20,'1wk':12,'1w':12,'10m':6}[row.chart?.interval]||20),horizonUnit=frameNames[e?.hold_interval||row.chart?.interval]||frame;
  const thesis=decision==='saved'?row.symbol+': saved setup recorded '+(time(row.alert_at)?new Date(time(row.alert_at)).toISOString().slice(0,10):'previously')+'. Open the current read for today’s trigger.':decision==='manage'?row.symbol+': manage the existing '+(side>0?'bullish':'bearish')+' position using its recorded exit.':decision==='pending'?row.symbol+': reconcile the existing order before opening another.':side&&entry&&invalidation&&targets[0]&&geometry?row.symbol+': '+(side>0?'Bullish':'Bearish')+' call. '+(side<0?'Bearish stock-price plan; no trade order is included. ':'')+(entry.text||entry.condition||'Trigger at '+price(entry.price)+'.')+' First objective: '+targets[0].text+' Horizon: within '+horizonBars+' completed '+horizonUnit+' bars. Invalidation: '+invalidation.text:side?row.symbol+': '+(side>0?'Bullish':'Bearish')+' read. '+(skip||'Trigger, objective and invalidation are being updated from the latest completed chart.'):row.symbol+': refresh the completed chart to resolve direction and publish its price map.';
  const contextConflicts=[];
  for(const raw of row.desk_read?.conflicts||[]){const conflict=setupPlainMarketConflict(raw,side),key=setupMarketComparisonCount(conflict);if(key?contextConflicts.some(x=>setupMarketComparisonCount(x)===key):contextConflicts.includes(conflict))continue;contextConflicts.push(conflict);}
  if(num(row.market?.breadth_above_50d)&&((side>0&&row.market.breadth_above_50d<=40)||(side<0&&row.market.breadth_above_50d>=60)))contextConflicts.push('Broad participation works against this direction ('+row.market.breadth_above_50d+'% above the 50-day average).');
  if(num(row.market?.risk_on)&&row.market.risk_total>0&&((side>0&&row.market.risk_on/row.market.risk_total<=.25)||(side<0&&row.market.risk_on/row.market.risk_total>=.75))){const count=row.market.risk_on,total=row.market.risk_total,key=count+'/'+total;if(!contextConflicts.some(x=>setupMarketComparisonCount(x)===key))contextConflicts.push(count+' of '+total+' market comparisons favor taking more risk, opposing the '+(side>0?'bullish':'bearish')+' call.');}
  const contextLabels=[...new Set(contextConflicts.map(x=>/broad participation|50-day average/.test(x)?'breadth':/market comparisons|taking more risk|risk appetite|risk-on/i.test(x)?'risk_appetite':/volatility backdrop/.test(x)?'volatility':/momentum|divergence/i.test(x)?'momentum':/wave/i.test(x)?'wave':/timeframe/i.test(x)?'timeframe':'other'))];
  const marketRisk=contextConflicts.find(x=>/\d+(?:\.\d+)? of \d+(?:\.\d+)? market comparisons/.test(x))||contextConflicts.find(x=>/broad participation|market comparisons|risk appetite|volatility backdrop|Cross-asset/i.test(x));
  const tradeoff=usable?[marketRisk].filter(Boolean).join(' '):'';
  const chartLevels=[];
  if(usable&&entry){const range=!actual&&Number.isFinite(entry.acceptable_low)&&Number.isFinite(entry.acceptable_high)&&entry.acceptable_low<entry.acceptable_high?{low:entry.acceptable_low,high:entry.acceptable_high}:null;chartLevels.push({kind:actual?(state==='manage'?'entry':'reference'):'reference',price:entry.price,label:actual?'Strategy reference':selectedRetest?'Retest entry':'Close trigger',...(range?{range}:{}),symbol:row.symbol,price_basis:'underlying'});}
  if(usable&&invalidation)chartLevels.push({kind:'invalidation',price:invalidation.price,label:actual?'Strategy stop':'Chart invalidation',symbol:row.symbol,price_basis:'underlying'});
  if(usable)targets.forEach((x,i)=>chartLevels.push({kind:'target',price:x.price,label:actual?'Strategy target':'Objective '+(i+1),symbol:row.symbol,price_basis:'underlying'}));
  const bandGeometry=geometry?setupBandGeometry(side,entry?.display_band,geometry.stop,geometry.target):null;
  const economicsSummary=geometry&&!actual?((side<0?'Stock prices only; no option price or option outcome is calculated. ':'')+(bandGeometry?'Gross reward/risk: '+geometry.ratio.toFixed(2)+'R at the trigger and '+bandGeometry.ratio.toFixed(2)+'R at the least favorable entry ('+price(bandGeometry.entry)+'). Gross break-even hit rate: '+geometry.break_even_win_rate_pct.toFixed(1)+'% at the trigger and '+bandGeometry.break_even_win_rate_pct.toFixed(1)+'% at the band edge.':'Gross mapped reward/risk: '+geometry.ratio.toFixed(2)+'R. Gross break-even hit rate: '+geometry.break_even_win_rate_pct.toFixed(1)+'%.')):null;
  const brief={authority:actual?'recorded_strategy':'chart_research',decision,label,thesis,why:reasons.slice(0,3),entry,invalidation,objectives:targets,holding,tradeoff,geometry,band_geometry:bandGeometry,economics_summary:economicsSummary,execution,quality:{coherent,complete,directional_support:aligned||improving||!!countertrendTrigger,objective_measured:targets.some(x=>['confirmed_pivot','supplied_strategy_target','observed_range_extreme'].includes(x.basis)),projected_levels:false,entry_method:selectedRetest?'structural_retest':'breakout',distance_atr:entry&&pos(m.atr14)?Math.abs(entry.price-close)/m.atr14:null,context_conflicts:contextLabels.length,context_labels:contextLabels},skip_reason:skip,chart_levels:chartLevels};
  return setupStoredResearchBrief(row,brief,sourceFresh,now);
}

/* One read-only interpretation for the shortlist, full read and chart labels.
 * Uses supplied strategy rules and measured levels; creates no signal or order. */
function buildSetupPlan(row, now=Date.now(), sourceFresh=true) {
  sourceFresh=sourceFresh&&row.input_status?.current!==false;
  const number=v=>typeof v==='number'&&Number.isFinite(v)?v:null;
  const positive=v=>number(v)!==null&&v>0;
  const fmt=v=>positive(v)?setupPriceText(v):'not supplied';
  const words=v=>typeof v==='string'?v.replaceAll('_',' ').trim():'';
  const clock=v=>typeof v==='string'&&Number.isFinite(Date.parse(v))?Date.parse(v):null;
  const at=v=>new Date(v).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+' ET';
  const frames={'1d':'daily','1h':'hourly','4h':'four-hour','10m':'ten-minute','1wk':'weekly','1w':'weekly'};
  const lookup=row.on_demand===true||row.stage==='on_demand',saved=row.saved_alert===true;
  const e=lookup?null:(row.evidence||[]).find(x=>x.id===row.primary_evidence_id)||row.evidence?.[0]||null;
  const c=row.curation||{},read=row.desk_read||{},m=row.technicals?.metrics||{};
  const side=row.direction==='bullish'?1:row.direction==='bearish'?-1:0;
  const frame=frames[row.chart?.interval]||row.horizon||'strategy';
  const intended=frames[e?.chart_interval]||row.horizon||frame;
  const explainRule=value=>words(value)
    .replace(/twenty completed holding bars/gi,'20 completed '+(frames[e?.hold_interval]||intended)+' bars')
    .replace(/A four-completed-bar panel must show Tensor balance improving by at least two, with at least two of seven component votes increasing\.?/i,'Across four completed hourly bars, the combined trend-balance score must rise by at least two, and at least two of its seven measures must improve.')
    .replace(/close > max\(previous (\d+) high\)/gi, 'the completed close is above the highest price of the previous $1 bars')
    .replace(/close < min\(previous (\d+) low\)/gi, 'the completed close falls below the lowest price of the previous $1 bars')
    .replace(/close > sma(\d+)/gi, 'the completed close is above its $1-bar moving average')
    .replace(/close < sma(\d+)/gi, 'the completed close falls below its $1-bar moving average')
    .replace(/observed quote initial 2atr stop/gi, "the observed price reaches the initial stop (twice the average true range measured at entry)")
    .replace(/(\d+) completed holding bars/gi, '$1 completed '+(frames[e?.hold_interval]||intended)+' bars after entry')
    .replace(/Exit at actual entry-bar index \+ (\d+); late observations service the owned exit without inventing a missing opening\.?/i, 'Exit after $1 completed '+(frames[e?.hold_interval]||intended)+' bars from the actual entry. The desk continues managing the exit if an observation arrives late.');
  const start=clock(row.window_start||e?.entry_window_start),end=clock(row.window_end||e?.entry_window_end);
  const held=!lookup&&(row.stage==='paper_entry'||e?.held===true),pending=e?.pending_order===true;
  const expired=!held&&!lookup&&(end!==null&&end<=now||row.lifecycle?.status==='retired');
  const chartValid=!!row.chart&&row.chart.symbol===row.symbol&&row.chart.context_only!==true&&row.technicals?.status==='ready';
  const freshRead=read.considered?.find(x=>x.id==='freshness');
  const chartOK=chartValid&&(lookup?freshRead?.status!=='stale':c.chart_current!==false&&freshRead?.status!=='stale');
  const option=['recovery','pead','xsp_pcs','opening_gamma','tensor_leaps','core_reserve'].includes(e?.native_family)||e?.mode==='local_model_paper';
  const shareUnits=e?.mode==='local_paper'&&!option&&['actual_paper_fill','signal_close','underlying_reference','entry_spot'].includes(e?.price_basis);
  const entry=held&&positive(e?.entry_price)?e.entry_price:positive(e?.reference_price)?e.reference_price:positive(e?.entry_price)?e.entry_price:null;
  const stop=number(e?.stop_price),target=number(e?.target_price);
  const risk=shareUnits&&entry!==null&&positive(stop)&&side?(entry-stop)*side:null;
  const reward=shareUnits&&entry!==null&&positive(target)&&side?(target-entry)*side:null;
  const invalidGeometry=shareUnits&&entry!==null&&((risk!==null&&risk<=0)||(reward!==null&&reward<=0));
  const risk_reward=positive(risk)&&positive(reward)?{entry,stop,target,risk_per_unit:risk,reward_per_unit:reward,ratio:reward/risk,upside_pct:100*reward/entry,downside_pct:100*risk/entry,costs_included:false,basis:held?'recorded_entry':'signal_reference'}:null;
  const rawCurrent=!!e&&e.active===true&&row.stage==='triggered'&&e.risk_permission===true&&!pending&&start!==null&&start<=now&&end!==null&&end>now;
  const ready=!!side&&c.readiness==='ready'&&rawCurrent&&chartOK&&!invalidGeometry&&sourceFresh;
  const state=saved?(expired?'ended':'saved'):held?'manage':pending?'pending':expired?'ended':!sourceFresh?'unavailable':lookup?'on_demand':ready?'ready':e?'waiting':'research';
  const labels={saved:'Saved read',manage:'Manage the paper position',pending:'Order reconciliation',ended:'Window closed',unavailable:'Chart update needed',on_demand:'On-demand chart read',ready:'Strategy ready',waiting:'Trigger pending',research:'Research setup'};
  const direction=side>0?'a rise':side<0?'a fall':'a directional break';
  const structure=m.structure_breach==='bullish_failed'?`the earlier rising swing pattern has broken below its latest swing low${positive(m.last_swing_low)?' at '+fmt(m.last_swing_low):''}`:m.structure_breach==='bearish_failed'?`the earlier falling swing pattern has broken above its latest swing high${positive(m.last_swing_high)?' at '+fmt(m.last_swing_high):''}`:{higher_highs_higher_lows:'the latest confirmed swing highs and lows are rising',lower_highs_lower_lows:'the latest confirmed swing highs and lows are falling'}[m.structure]||'the swings do not yet establish a clear trend';
  const conflicts=[...new Set(read.conflicts||[])];
  const purpose=e?.rule_summary&&!/^Tests the price pattern described below/i.test(e.rule_summary)?e.rule_summary:null;
  const call=side>0?'Bullish':side<0?'Bearish':'Directional';
  let gist=held?`${row.symbol}: manage the existing paper position using its exit conditions.`:
    side?`${row.symbol}: ${call} setup. ${chartOK?`The ${frame} chart shows ${structure}.`:chartValid?`Update the completed ${frame} chart to refresh the price map.`:'Load the matching completed chart to refresh the price map.'}`:`${row.symbol}: direction is pending a completed chart trigger.`;
  if(saved)gist=`${row.symbol}: saved setup from this alert. Open the current read for today's trigger.`;
  else if(state==='unavailable')gist=`${row.symbol}: ${call} read. Update the completed chart to refresh today's trigger and price map.`;
  // Distil the existing salient facts; do not add weights, votes or a new score.
  const factTexts={
    'Price structure':chartOK?`The ${frame} chart shows ${structure}.`:null,
    'Market breadth':number(row.market?.breadth_above_50d)!==null?`${row.market.breadth_above_50d.toFixed(1)}% of the tracked stocks are above their 50-day average.`:null,
    'Volume and volatility':chartOK&&positive(m.relative_volume)?`Trading volume is ${m.relative_volume.toFixed(2)} times its previous 20-bar average.`:null,
    'Momentum':chartOK&&number(m.rsi14)!==null?`RSI momentum is ${m.rsi14.toFixed(1)} on a 0–100 scale${m.rsi14>=70?' (above the usual 70 threshold)':m.rsi14<=30?' (below the usual 30 threshold)':''}.`:null,
    'ChartsLector':number(row.ranker?.opp)!==null?`ChartsLector opportunity rank: ${row.ranker.opp.toFixed(1)} out of 100 in its daily universe.`:null,
  };
  if(chartOK&&number(m.atr_percent)!==null&&(m.atr_percent>=6||!positive(m.relative_volume))){
    factTexts['Volume and volatility']=`Recent typical ${frame} range: ${m.atr_percent.toFixed(2)}% of price.`+(positive(m.relative_volume)?` Volume is ${m.relative_volume.toFixed(2)} times its previous 20-bar average.`:'');
  }
  const divs=row.technicals?.divergences||[],currentDivs=divs.filter(d=>d.current_status!=='invalidated');
  if(chartOK&&divs.length){
    const directions=[...new Set(currentDivs.map(d=>d.kind))],hidden=currentDivs.filter(d=>d.divergence_type==='hidden'),regular=currentDivs.some(d=>d.divergence_type!=='hidden');
    const current=directions.length>1?`Bullish and bearish momentum divergences conflict; the ${side>0?'bullish':'bearish'} call follows the stronger price-structure evidence.`:currentDivs.length?`${hidden.length?(regular?'Regular and hidden':'Hidden'):'Regular'} ${directions[0]} divergence is present${hidden.length?`; ${hidden.every(d=>d.continuation_alignment==='aligned')?'the trend aligned with this continuation when the pattern formed':'the trend opposed or failed to confirm this hidden continuation when the pattern formed'}`:`; momentum is ${directions[0]==='bullish'?'improving':'weakening'} relative to price`}.`:'';
    const failed=divs.length>currentDivs.length?'An earlier hidden divergence was invalidated by a later completed close; it no longer supports the current read.':'';
    factTexts['Regular and hidden divergence']=[current,failed].filter(Boolean).join(' ');
  }
  if(chartOK&&positive(m.atr14)&&number(m.sma20)!==null&&positive(m.close)){
    const distance=(m.close-m.sma20)/m.atr14,barrier=side>0?m.resistance:side<0?m.support:null,room=positive(barrier)?side*(barrier-m.close)/m.atr14:null;
    const extension=`Price is ${Math.abs(distance).toFixed(2)} typical bar ranges ${distance>=0?'above':'below'} its 20-bar average.`;
    const label=side>0?'resistance':'support',percent=positive(barrier)?100*Math.abs(barrier-m.close)/m.close:null;
    const nearby=room!==null&&room>=0&&room<1?(room===0?`Price is at ${label}, ${fmt(barrier)}.`:`Nearby ${label} at ${fmt(barrier)} is ${percent<0.01?'less than 0.01':percent.toFixed(2)}% ${side>0?'above':'below'} the last close.`):null;
    factTexts['Entry location']=nearby?(side*distance>2?extension+' '+nearby:nearby):extension;
  }
  const key_points=[];for(const item of read.salient||[]){
    if(item.label==='Price structure'&&gist.includes(structure))continue;
    const detail=typeof item.text==='string'?item.text.replace(/\s+/g,' ').trim():'';
    const text=factTexts[item.label]||detail;if(text&&!key_points.some(x=>x.text===text))key_points.push({label:item.label,text,tone:item.tone||'neutral',category:item.category||null,factor_id:item.id||null});if(key_points.length===3)break;
  }
  const blockers=(c.blockers||[]).map(x=>x.code==='risk_decision_pending'?'Wait for the strategy to approve a new paper entry.':x.message?.replace(/\bsleeve\b/g,'strategy')).filter(Boolean);
  if(!chartOK&&!lookup&&!blockers.some(x=>/chart/i.test(x)))blockers.push(`A usable ${intended} chart is still needed.`);
  if(invalidGeometry)blockers.push('The supplied price levels do not fit the setup direction.');
  let condition=e?.entry_rule?explainRule(e.entry_rule).replace(/^Entry:\s*/i,''):e?.reason==='recorded_strategy_candidate'?(purpose||'The strategy has flagged a possible entry'):words(e?.reason);
  if(held&&!e?.entry_rule&&/observed paper entry|not new signal/i.test(condition))condition='';
  if(e?.score_basis==='predicted_net_qqq_excess'&&number(e.score)!==null&&number(e.score_threshold)!==null){
    const period=Number.isInteger(e.hold_bars)&&e.hold_bars>0?` over ${e.hold_bars} completed ${frames[e.hold_interval]||intended} bars`:'';
    condition=`The model estimates ${(e.score*100).toFixed(2)}% performance relative to QQQ${period}, ${e.score>=e.score_threshold?'meeting':'below'} its ${(e.score_threshold*100).toFixed(2)}% entry threshold`;
  }
  const obstacle=side>0?number(m.resistance):side<0?number(m.support):null;
  const opposite=side>0?number(m.support):side<0?number(m.resistance):null;
  // A close exactly at a measured level can still cross it on the next bar.
  // This is chart-watch geometry; actual order risk/reward remains strictly positive.
  const obstacleAhead=chartOK&&!!side&&positive(obstacle)&&positive(m.close)&&side*(obstacle-m.close)>=0;
  const oppositeBehind=chartOK&&!!side&&positive(opposite)&&positive(m.close)&&side*(m.close-opposite)>=0;
  const reference=entry!==null?`${held?'Recorded entry':'Signal reference'}: ${fmt(entry)}${option?' (model or underlying reference, as recorded)':''}. `:'';
  const confirmation=e&&!lookup?{kind:held?'recorded_entry':'strategy_trigger',text:reference+(condition?`${held?'Original entry condition':'Strategy condition'}: ${condition.replace(/[.!?]+$/,'')}.`:held?'The original entry condition is not included in this observation.':'Wait for the strategy to publish its entry condition.')}:
    obstacleAhead?{kind:'chart_watch',price:obstacle,text:`Watch for a completed ${frame} close ${side>0?'above resistance':'below support'} at ${fmt(obstacle)}. This confirms a chart change; a strategy entry needs its own trigger.`}:
    {kind:'missing',text:`Wait for a clear ${frame} chart trigger; no numeric confirmation level is supplied.`};
  let invalidation;
  if(shareUnits&&positive(stop)&&risk>0)invalidation={kind:'strategy_stop',price:stop,text:`Recorded strategy stop: ${fmt(stop)}.`};
  else if(shareUnits&&positive(e?.stop_distance)&&side)invalidation={kind:'strategy_distance',text:`Strategy stop: actual filled entry ${side>0?'minus':'plus'} ${fmt(e.stop_distance)}.`};
  else if(oppositeBehind)invalidation={kind:'chart_watch',price:opposite,text:`Invalidate the chart read on a completed ${frame} close ${side>0?'below support':'above resistance'} at ${fmt(opposite)}. The strategy stop remains listed separately.`};
  else invalidation={kind:'missing',text:e?.exit_rule?'The strategy exit rule below defines invalidation; its price stop is not supplied in this record.':'Set a numeric invalidation before using this idea as an entry plan.'};
  const exits=[];
  if(positive(target))exits.push(`${option?'Recorded model target value':'Recorded strategy target'}: ${fmt(target)}.`);
  if(clock(e?.exit_at)!==null)exits.push(`Scheduled exit: ${at(e.exit_at)}.`);
  if(e?.exit_rule)exits.push(explainRule(e.exit_rule));
  const hold=Number.isInteger(e?.max_hold_bars)&&e.max_hold_bars>0?e.max_hold_bars:e?.hold_bars;
  if(Number.isInteger(hold)&&hold>0&&!exits.some(x=>x.includes(`${hold} completed ${frames[e?.hold_interval]||'strategy'} bars`)))exits.push(`Maximum hold: ${hold} completed ${frames[e?.hold_interval]||'strategy'} bars.`);
  const exit={text:exits.length?[...new Set(exits)].join(' '):'No strategy exit is supplied for this research idea.'};
  const chartForecastBars=({'1h':6,'4h':6,'10m':6,'1d':20,'1wk':12,'1w':12}[row.chart?.interval]||20);
  let timing={text:lookup?`On-demand read of completed ${frame} candles; linked strategies retain their entry and exit plans.`:start!==null&&end!==null?`${at(start)} → ${at(end)}. ${held?'This was the entry window; exits remain managed.':expired?'The window has closed; use the next eligible signal.':'Apply the strategy trigger inside this window.'}`:held?'Position management follows the exit / holding plan above.':!e?`Check after each completed ${frame} candle for the entry condition above. This call is aimed at the next ${chartForecastBars} completed ${frame} candles.`:`No entry time is scheduled. Wait until the desk shows the next entry signal and confirms it passes the risk check.`};
  let next_step=state==='saved'?'Open the current chart read for today’s entry condition.':state==='manage'?'Manage the existing paper position using the exit conditions below.':state==='pending'?'Reconcile the existing order before opening another.':state==='ended'?'Use the next eligible signal; this entry window has closed.':state==='unavailable'?'Refresh the desk update before using this setup.':state==='ready'?`The strategy trigger and paper risk checks are present. ${conflicts.length?'Review the conflicting evidence below before entry.':'Use the recorded entry window and strategy exit plan below.'}`:
    start!==null&&start>now&&!lookup?`Wait until ${at(start)}, then require the strategy condition and a current risk decision.`:
    blockers.length?[...new Set(blockers)].join(' '):e&&!lookup?(e.risk_permission!==true?'Wait for a current strategy risk decision as well as the recorded entry condition.':`Wait for the strategy's next eligible trigger. ${condition?confirmation.text:''}`):confirmation.kind==='chart_watch'?`Watch for a completed ${frame} close ${side>0?'above':'below'} ${fmt(confirmation.price)}. A chart change alone is not a strategy entry.`:confirmation.text;
  const chart_levels=[];
  const line=(kind,value,label)=>{if(chartOK&&positive(value))chart_levels.push({kind,price:value,label,symbol:row.symbol,price_basis:'underlying'});};
  if(shareUnits){line(held?'entry':'reference',entry,held?'Recorded paper entry':'Signal reference');if(risk>0)line('invalidation',stop,'Strategy stop');if(reward>0)line('target',target,'Strategy target');}
  if(confirmation.kind==='chart_watch')line('reference',confirmation.price,'Chart confirmation');
  if(invalidation.kind==='chart_watch')line('invalidation',invalidation.price,'Chart read weakens');
  const chart_scenario=setupChartScenario(row,chartOK&&sourceFresh&&!saved,now);
  const authority=lookup||!e?'chart_research':'recorded_strategy';
  const holdParts=[];
  if(clock(e?.exit_at)!==null)holdParts.push('Until '+at(e.exit_at)+', unless the strategy exit occurs first.');
  if(Number.isInteger(hold)&&hold>0)holdParts.push('At most '+hold+' completed '+(frames[e?.hold_interval]||'strategy')+' bars from actual entry.');
  if(Number.isInteger(e?.hold_sessions)&&e.hold_sessions>0)holdParts.push('At most '+e.hold_sessions+' exchange sessions under the installed strategy calendar.');
  const howLong=holdParts.join(' ')||(e?.exit_rule?'Until the recorded exit condition is met; no fixed duration is supplied.':chart_scenario?.holding.text||'Reassess each completed candle; there is no fixed holding period.');
  const scenarioPrice=chart_scenario?(side>0?'Pullback watch zone ':'Rally watch zone ')+fmt(chart_scenario.entry_zone.low)+'–'+fmt(chart_scenario.entry_zone.high)+'. '+(chart_scenario.confirmation.relation_to_zone==='outside'?'Confirmation is '+(side>0?'above ':'below ')+fmt(chart_scenario.confirmation.price)+', outside that zone; assess a confirmation entry at that separate price reference.':'Require the stated reversal confirmation at '+fmt(chart_scenario.confirmation.price)+'.'):null;
  const priceAnswer=held&&entry!==null?'Recorded fill '+fmt(entry)+'.':e&&entry!==null?'Strategy reference '+fmt(entry)+'. The actual entry still follows its trigger and window.':scenarioPrice||'No coherent entry zone is available yet.';
  const actualEntry=confirmation.text&&!next_step.includes(confirmation.text)?next_step+' '+(saved?'Recorded entry condition: ':'')+confirmation.text:next_step;
  const whenEnter=authority==='recorded_strategy'?actualEntry:chart_scenario?(chart_scenario.status==='barrier_in_zone'?'Wait for the opposing level inside the zone to resolve. ':'' )+chart_scenario.confirmation.rule+' Confirmation level: '+fmt(chart_scenario.confirmation.price)+'.':next_step;
  const relevantObjective=chart_scenario?.confirmation.relation_to_zone==='outside'?chart_scenario.confirmation_objective:chart_scenario?.objectives[0];
  const whenExit=authority==='recorded_strategy'?[invalidation.kind==='strategy_stop'||invalidation.kind==='strategy_distance'?invalidation.text:null,exit.text].filter(Boolean).join(' '):chart_scenario?(relevantObjective?'Reassess at '+fmt(relevantObjective.price):'Wait for a measured objective beyond the confirmation price')+'; cancel the chart scenario '+(side>0?'below ':'above ')+fmt(chart_scenario.invalidation.price)+'.':'A complete exit map is not available yet.';
  if(authority==='chart_research'&&chart_scenario){next_step=whenEnter;chart_levels.length=0;}
  // Nearby swing tests remain context; only the chosen scenario is called the
  // confirmation on a price map. Sleeve-supplied execution levels retain labels.
  if(chart_scenario)for(const level of chart_levels)if(level.label==='Chart confirmation')level.label=side>0?'Nearby resistance':'Nearby support';
  const answers={authority,when_to_enter:whenEnter,entry_price:priceAnswer,how_long:howLong,when_to_exit:whenExit,priority:authority==='recorded_strategy'?'The recorded strategy plan controls its paper position; chart scenarios are additional analysis.':'Research map; paper orders continue to follow the strategy trigger.'};
  const plan={schema:'CODEX_SETUP_PLAN_V1',state,status_label:labels[state],strategy_name:e?.strategy_name||e?.book_label||null,strategy_summary:purpose,gist,key_points,next_step,confirmation,invalidation,exit,timing,risk_reward,chart_levels,conflicts,answers,chart_scenario,price_note:option?'Chart levels describe the underlying; they are not option premiums.':null};
  plan.brief=setupDecisionBrief(row,plan,now,sourceFresh);
  const interval=row.chart?.interval||'1d',horizonUnits=frames[interval]||'completed',nativeHold=Number.isInteger(e?.max_hold_bars)&&e.max_hold_bars>0?e.max_hold_bars:Number.isInteger(e?.hold_bars)&&e.hold_bars>0?e.hold_bars:null;
  const horizonBars=nativeHold||({'1h':6,'4h':6,'10m':6,'1d':20,'1wk':12,'1w':12}[interval]||20),forecast_horizon={bars:horizonBars,interval:e?.hold_interval||interval,label:'within '+horizonBars+' completed '+(frames[e?.hold_interval]||horizonUnits)+' bars',basis:nativeHold?'recorded_strategy_holding_rule':'fixed_chart_research_horizon',calendar_time:false};
  plan.brief={...plan.brief,direction:side>0?'bullish':side<0?'bearish':null,forecast_horizon};
  if(plan.brief.authority==='chart_research'&&plan.brief.decision==='conditional')plan.brief={...plan.brief,holding:{text:'After the entry rule confirms, reach the first objective or invalidation '+forecast_horizon.label+'. If neither occurs by the horizon, expire this research map and reassess.'}};
  // The primary research contract has one instruction. Keep separate native
  // sleeve rules explicit, rather than leaving a second wave-derived entry in
  // gist/next_step/answers beside the canonical research brief.
  if(plan.brief.authority==='chart_research'){
    const b=plan.brief,missing=b.decision==='unavailable'||!b.entry;
    if(plan.answers.authority==='recorded_strategy')plan.strategy_plan={gist:plan.gist,next_step:plan.next_step,answers:plan.answers,confirmation:plan.confirmation,invalidation:plan.invalidation,exit:plan.exit,timing:plan.timing};
    const instruction=b.decision==='saved'?(b.execution?.text||b.thesis):b.decision==='conditional'?(b.entry?.rule_text||b.entry?.text||b.thesis):(b.skip_reason||b.thesis);
    plan.gist=b.thesis;plan.status_label=b.label;plan.next_step=instruction;
    plan.confirmation={kind:b.entry?'chart_watch':'unavailable',text:instruction,price:b.entry?.price??null};
    plan.invalidation={kind:b.invalidation?'chart_watch':'unavailable',text:b.invalidation?.text||'A current invalidation level is not available.',price:b.invalidation?.price??null};
    plan.exit={kind:'chart_research',text:b.holding?.text||(missing?'Wait for current chart inputs before defining an exit map.':'This research idea has no approved entry plan yet.')};
    plan.answers={authority:'chart_research',when_to_enter:instruction,entry_price:b.decision==='saved'?'Recorded price map; open the current setup for present entry conditions.':b.entry?(b.entry.display_band?'Only inside '+setupEntryBandText(b.entry.display_band)+' after the stated confirmation.':'Watch level '+fmt(b.entry.price)+'; '+instruction):'No current entry price is available.',how_long:b.holding?.text||'No holding period applies before a valid entry plan exists.',when_to_exit:b.holding?[b.invalidation?.text,...b.objectives.map(x=>x.text)].filter(Boolean).join(' '):plan.exit.text,priority:'This chart research plan is separate from automated sleeve orders.'};
    if(!b.entry&&!b.invalidation&&!b.objectives.length)plan.risk_reward=null;
    // A rejected primary plan does not erase a valid alternative from the
    // optional analysis. It supplies no entry authority or primary chart lines.
    if(b.decision==='unavailable'||!sourceFresh)plan.chart_scenario=null;
    key_points.length=0;
    for(const item of read.salient||[]){
      if(item.label==='Price structure'&&plan.gist.includes(structure))continue;
      const detail=typeof item.text==='string'?item.text.replace(/\s+/g,' ').trim():'';
      const text=factTexts[item.label]||detail;
      if(text&&!key_points.some(x=>x.text===text))key_points.push({label:item.label,text,tone:item.tone||'neutral',category:item.category||null,factor_id:item.id||null});
      if(key_points.length===3)break;
    }
  }
  if(plan.brief.authority==='chart_research'&&key_points.length)plan.brief={...plan.brief,why:key_points.map(x=>x.text)};
  if(!plan.key_points?.length&&read.salient?.length){plan.key_points=read.salient.map(item=>({label:item.label,text:String(item.text||'').replace(/\s+/g,' ').trim(),tone:item.tone||'neutral',category:item.category||null,factor_id:item.id||null})).filter(x=>x.text).slice(0,3);}
  if(plan.brief.authority==='chart_research'&&plan.brief.decision==='conditional'){
    const canonical=setupApplyManualExecutionContract(plan.brief,row),manualSteps=canonical?.manual_steps;
    if(manualSteps){
      plan.brief=canonical;plan.gist=canonical.thesis;plan.risk_reward=canonical.geometry;plan.execution=canonical.execution;
      const thresholds=manualSteps.price_levels.execution_thresholds,band=canonical.entry.display_band;
      plan.next_step=manualSteps.entry;
      plan.confirmation={kind:'chart_watch',text:manualSteps.entry,price:thresholds.entry.close.price};
      plan.invalidation={kind:'chart_watch',text:manualSteps.invalidation,price:thresholds.invalidation.price};
      plan.exit={kind:'chart_research',text:manualSteps.target+' '+manualSteps.invalidation};
      plan.answers={authority:'chart_research',when_to_enter:manualSteps.entry,entry_price:band?'Only inside '+setupEntryBandText(band)+' after the stated confirmation.':'Watch the stated completed-candle confirmation.',how_long:canonical.holding?.text||'Reassess on each completed candle.',when_to_exit:manualSteps.target+' '+manualSteps.invalidation,priority:'This is a chart-research plan; automated sleeves keep their own order rules.'};
    }else{
      // A conditional chart read is actionable only if the exact executable
      // stock-price increments can express its full entry/target/exit contract.
      const reason='The exact tick-valid prices could not form a complete entry, target and invalidation plan. Refresh the chart before using this setup.';
      plan.brief={...plan.brief,decision:'pass',label:'Plan needs a complete price map',skip_reason:reason,thesis:reason,entry:null,objectives:[],invalidation:null,geometry:null,band_geometry:null,manual_steps:null,quality:{...plan.brief.quality,coherent:false},chart_levels:[],execution:{state:'research',text:reason}};
      plan.gist=reason;plan.execution={state:'research',text:reason};plan.next_step=reason;
      plan.confirmation={kind:'unavailable',text:reason,price:null};plan.invalidation=null;plan.exit={kind:'chart_research',text:reason};plan.risk_reward=null;
      plan.answers={authority:'chart_research',when_to_enter:reason,entry_price:'No entry price is published.',how_long:'No holding period applies before a complete plan exists.',when_to_exit:reason,priority:'Research only until the exact price plan is complete.'};
    }
  }  if(plan.brief.authority==='chart_research'||plan.brief.chart_levels.length)plan.chart_levels=plan.brief.chart_levels;
  return setupWeeklyResearchTiming(plan,row);
}
if(typeof window!=='undefined')window.CodexSetupPlan={build:buildSetupPlan,formatPrice:setupPriceText,formatPlanPrice:setupPlanPriceText,formatAmount:setupAmountText,entryBand:setupEntryBand,weeklyResearchTiming:setupWeeklyResearchTiming};


// Original: worker/setup-clock-helpers.extracted.js
var SETUP_METHOD = "gestalt-brief-4";
var SETUP_HORIZONS = ["daily", "intraday", "weekly", "crypto"];
const SETUP_DATE_FORMATTERS=new Map();
function setupDateFormatter(locale,options){const key=locale+'|'+JSON.stringify(options);let formatter=SETUP_DATE_FORMATTERS.get(key);if(!formatter){formatter=new Intl.DateTimeFormat(locale,options);if(SETUP_DATE_FORMATTERS.size>=12)SETUP_DATE_FORMATTERS.clear();SETUP_DATE_FORMATTERS.set(key,formatter);}return formatter;}
var SETUP_FAMILIES = { G4: "tensor", C1: "tensor", BETA: "tensor", H1STATE: "tensor", WSTATE: "tensor", D20PV: "tensor", D20TENSOR: "tensor", tensor_leaps: "tensor", recovery: "recovery", pead: "earnings", xsp_pcs: "index_spread", opening_gamma: "opening", core_reserve: "allocation", etf: "allocation", hourly: "timing", cloud: "timing", overnight: "timing", native_trend: "trend", negative_funding_squeeze: "crypto_breakout", breakout_base: "crypto_breakout", absorption_negative_funding: "crypto_absorption", absorption_nonnegative_funding: "crypto_absorption", absorption_base: "crypto_absorption", public_recipe: "price_pattern", confirmed_absorption: "absorption" };
var SETUP_NATIVE_NAMES = { TRADER_DONCHIAN55: "Donchian 55-bar breakout", TRADER_RSI2: "RSI(2) pullback", TRADER_SQUEEZE20: "Bollinger/Keltner squeeze", D20PV: "Daily price-and-volume forecast", D20TENSOR: "Daily Tensor forecast", H1STATE: "Hourly Tensor state", WSTATE: "Weekly Tensor state" };
function setupStrategyName(family, fallback) {
  if (Object.hasOwn(SETUP_NATIVE_NAMES, family)) return SETUP_NATIVE_NAMES[family];
  return typeof fallback === "string" && /^[A-Za-z0-9][A-Za-z0-9 ()&+.,'/-]{0,79}$/.test(fallback) ? fallback : "Paper strategy";
}
function setupTime(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return null;
  const day = value.slice(0, 10), calendar = /* @__PURE__ */ new Date(day + "T12:00:00Z");
  if (!Number.isFinite(calendar.getTime()) || calendar.toISOString().slice(0, 10) !== day) return null;
  const at = Date.parse(value);
  return Number.isFinite(at) ? at : null;
}
function setupDay(value) {
  const at = typeof value === "number" ? value : setupTime(value);
  if (at === null || !Number.isFinite(at)) return null;
  return setupDateFormatter("en-CA", { timeZone: "America/New_York" }).format(new Date(at));
}
function setupPublishedTime(value) {
  const iso = setupTime(value);
  if (iso !== null) return iso;
  const match = typeof value === "string" && value.match(/^(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}) ET$/);
  if (!match) return null;
  const wall = setupTime(match[1] + "T" + match[2] + ":" + match[3] + ":00Z");
  if (wall === null) return null;
  const formatter = setupDateFormatter("en-US", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  const matches = [4, 5].map((offset) => wall + offset * 36e5).filter((at) => {
    const p = Object.fromEntries(formatter.formatToParts(new Date(at)).map((x) => [x.type, x.value]));
    return p.year + "-" + p.month + "-" + p.day + " " + p.hour + ":" + p.minute === match[1] + " " + match[2] + ":" + match[3];
  });
  return matches.length === 1 ? matches[0] : null;
}
function setupCurrentDaily(day, now, market = null) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day || "")) return false;
  const source = /* @__PURE__ */ new Date(day + "T12:00:00Z"), today = setupDay(now);
  if (!Number.isFinite(source.getTime()) || source.toISOString().slice(0, 10) !== day || !today || day > today || [0, 6].includes(source.getUTCDay())) return false;
  if (day === today) return true;
  // A fresh verified calendar can witness a holiday gap. Never invent a
  // holiday or extend an older daily packet from elapsed time alone.
  if(market?.calendar_verified===true){
    const receipt=setupTime(market.at),open=setupTime(market.open),close=setupTime(market.close),previous=setupTime(market.previous_session_close);
    if([receipt,open,close,previous].every(x=>x!==null)&&receipt<=now&&now-receipt<=300000&&previous<=now&&previous<open&&open<close&&setupDay(open)>=today&&setupDay(open)===setupDay(close)&&day===setupDay(previous))return true;
  }
  const cursor = /* @__PURE__ */ new Date(today + "T12:00:00Z");
  do {
    cursor.setUTCDate(cursor.getUTCDate() - 1);
  } while ([0, 6].includes(cursor.getUTCDay()));
  return day === cursor.toISOString().slice(0, 10);
}
function setupDailyPacketCurrent(packet, now, market = null) {
  const generated = setupPublishedTime(packet?.generated_at);
  return setupCurrentDaily(packet?.as_of, now, market) && generated !== null && generated <= now && setupDay(generated) >= packet.as_of;
}


// Original: worker/desk-read.js
// A transparent interpretation of observations, never an order. Curation may
// consider its distinct conflicts without treating the qualitative call as a score.
var DESK_READ_METHOD = 'desk-read-16';
var DESK_GESTALT_REGISTRY = []
;
const DESK_DATE_FORMATTERS=new Map();
function deskDateFormatter(locale,options={}) { const key=locale+'|'+JSON.stringify(options);let formatter=DESK_DATE_FORMATTERS.get(key);if(!formatter){formatter=new Intl.DateTimeFormat(locale,options);if(DESK_DATE_FORMATTERS.size>=12)DESK_DATE_FORMATTERS.clear();DESK_DATE_FORMATTERS.set(key,formatter);}return formatter; }
function deskNum(x) { return typeof x==='number'&&Number.isFinite(x)?x:null; }
const DESK_NUMBER_FORMATTERS=new Map();
function deskFormatNumber(value,options={}) { const key=JSON.stringify(options);let formatter=DESK_NUMBER_FORMATTERS.get(key);if(!formatter){formatter=new Intl.NumberFormat('en-US',options);if(DESK_NUMBER_FORMATTERS.size>=16)DESK_NUMBER_FORMATTERS.clear();DESK_NUMBER_FORMATTERS.set(key,formatter);}return formatter.format(value); }
function deskFmt(x,d=1) { return deskNum(x)===null?'unknown':deskFormatNumber(x,{maximumFractionDigits:d}); }
// Prices retain the chart's small-value precision; scores and percentages keep
// their own units/formatting. A positive entry or stop must never print as zero.
function deskPrice(x) {
  if(deskNum(x)===null)return 'unknown';const a=Math.abs(x);
  if(a>0&&a<1e-10)return x.toExponential(4);
  const digits=a>0&&a<1?Math.min(12,Math.max(4,4-Math.floor(Math.log10(a)))):4;
  return deskFormatNumber(x,{maximumFractionDigits:digits});
}
function deskMacdHistogramText(metrics,histogram) {
  const current=deskNum(metrics?.macd_histogram??histogram?.current),previous=deskNum(histogram?.previous);
  if(current===null)return 'MACD histogram is unavailable.';
  if(current===0)return 'MACD is at its signal line; histogram momentum is neutral.';
  if(previous===null)return current>0?'MACD is above its signal line; positive momentum is present, but its latest direction is unavailable.':'MACD is below its signal line; negative momentum is present, but its latest direction is unavailable.';
  if(current>0){if(previous<=0)return 'The histogram crossed above zero; MACD moved above its signal line.';if(current<previous)return 'MACD remains above its signal line, but the positive histogram is shrinking; upward momentum is fading.';if(current>previous)return 'MACD remains above its signal line and the positive histogram is growing; upward momentum is building.';return 'MACD remains above its signal line; positive momentum is holding steady.';}
  if(previous>=0)return 'The histogram crossed below zero; MACD moved below its signal line.';
  if(current>previous)return 'MACD remains below its signal line, but the histogram is moving toward zero; downward momentum is easing.';
  if(current<previous)return 'MACD remains below its signal line and the histogram is falling; downward momentum is strengthening.';
  return 'MACD remains below its signal line; negative momentum is holding steady.';
}
function deskDivergenceSummary(factors,tech,interval,metrics={},selectedDirection=null){
  const ids=interval==='1d'?['daily_divergences']:interval==='1wk'?['weekly_divergences']:['daily_divergences','weekly_divergences'];
  const rows=ids.map(id=>(factors||[]).find(x=>x.id===id)).filter(Boolean),authoritative=rows.some(x=>Array.isArray(x.value));
  const usableRows=rows.filter(x=>['measured','partial'].includes(x.status));
  const observed=authoritative?usableRows.flatMap(x=>Array.isArray(x.value)?x.value:[]):(tech?.divergences||[]);
  const divergences=observed.filter(x=>x.current_status!=='invalidated');
  const directionSet=new Set(divergences.map(x=>x.kind).filter(Boolean));
  const selectedSide=selectedDirection==='bullish'?1:selectedDirection==='bearish'?-1:0;
  const divergenceSide=x=>x.kind==='bullish'?1:x.kind==='bearish'?-1:0;
  const supporting=selectedSide?divergences.filter(x=>divergenceSide(x)===selectedSide):[];
  const opposing=selectedSide?divergences.filter(x=>divergenceSide(x)===-selectedSide):[];
  const samePivot=(a,b)=>a.kind===b.kind&&a.divergence_type===b.divergence_type&&(
    a.first_confirmed_at&&a.confirmed_at&&b.first_confirmed_at&&b.confirmed_at
      ?a.first_confirmed_at===b.first_confirmed_at&&a.confirmed_at===b.confirmed_at
      :Number.isInteger(a.first_index)&&Number.isInteger(a.second_index)&&Number.isInteger(b.first_index)&&Number.isInteger(b.second_index)&&a.first_index===b.first_index&&a.second_index===b.second_index
  );
  const rsiMacdConflict=authoritative?usableRows.some(row=>{
    const events=Array.isArray(row.value)?row.value:[],rsi=events.filter(x=>x.indicator==='RSI14'),macd=events.filter(x=>x.indicator==='MACD12_26_9');
    return rsi.length>0&&macd.length>0&&!rsi.some(a=>macd.some(b=>samePivot(a,b)));
  }):tech?.momentum?.status==='disagreement';
  const fallbackLabels={RSI14:'RSI',MACD12_26_9:'MACD',SlowStochastic14_3_3:'slow stochastic',OBV:'OBV',ADLine:'A/D',MFI14:'MFI',VolumeEMA5_20:'volume EMA 5–20'};
  const fallbackScan=tech?.divergence_scan||{},warmup=deskNum(metrics.macd)===null?' MACD is still warming up.':'',fallbackText=observed.length
    ?observed.map(d=>`${d.divergence_type==='hidden'?'Hidden':'Regular'} ${d.kind} ${d.indicator_label||fallbackLabels[d.indicator]||d.indicator}${d.divergence_type==='hidden'?`; continuation ${d.continuation_alignment||'unknown'}`:''}${d.current_status==='invalidated'?`; invalidated by a later completed close ${d.kind==='bullish'?'below':'above'} ${deskNum(d.invalidation_level)!==null?deskPrice(d.invalidation_level):'the second pivot'}`:''}`).join('. ')+`. ${fallbackScan.comparisons||0} eligible confirmed price-pivot comparisons across ${fallbackScan.gauges_checked||0}/7 gauges on this ${interval||'chart'} view.`+warmup
    :deskNum(metrics.macd)!==null||deskNum(metrics.rsi14)!==null?'No qualifying regular or hidden divergence at the eligible confirmed pivots.'+warmup:'Divergence scan is warming up.';
  const rowText=row=>{
    const label=row.id.startsWith('daily')?'Daily':'Weekly';
    if(['measured','partial'].includes(row.status)&&Array.isArray(row.value)&&row.value.length){
      const events=row.value.slice(0,3).map(x=>typeof setupFactorDivergenceSignalText==='function'?setupFactorDivergenceSignalText(x):`${x.divergence_type==='hidden'?'Hidden':'Regular'} ${x.kind} divergence in ${x.indicator_label||x.indicator}`);
      return `${label}: ${events.join('; ')}${row.value.length>3?`; ${row.value.length-3} more in the factor review`:''}.`;
    }
    return `${label}: ${row.detail||'No current divergence conclusion is available.'}`;
  };
  const pivotNote=rsiMacdConflict?' RSI and MACD use different confirmed swing pairs; do not count them as one matched confirmation.':'';
  const text=(authoritative?rows.map(rowText).join(' '):fallbackText)+pivotNote;
  const opposingLabels=[...new Set(opposing.map(x=>x.indicator_label||fallbackLabels[x.indicator]||x.indicator).filter(Boolean))];
  const counterpoint=opposing.length?`${selectedSide>0?'Bearish':'Bullish'} divergence${opposingLabels.length?` in ${opposingLabels.join(', ')}`:''} opposes the ${selectedSide>0?'bullish':'bearish'} call.`:null;
  const status=usableRows.length?'available':rows.some(x=>x.status==='stale')?'stale':divergences.length||deskNum(metrics.macd)!==null||deskNum(metrics.rsi14)!==null?'available':'missing';
  const divergenceConflict=selectedSide?opposing.length>0||rsiMacdConflict:directionSet.size>1||rsiMacdConflict;
  return {divergences,directionSet,supporting,opposing,counterpoint,rsiMacdConflict,momentumConflict:rsiMacdConflict,divergenceConflict,text,status,authoritative};
}
// A concise synthesis of the measured differences, not a second signal model.
// Numeric source values and the original call/score stay unchanged.
function deskReadNarrative(row,{held,pending,readFresh,hasChart,structureSummary,structureSign,trendSign,conflicts,breadth,risk,vix,now=Date.now()}){
  const m=row.technicals?.metrics||{},side=row.direction==='bullish'?1:row.direction==='bearish'?-1:0;
  const price=x=>deskNum(x)===null?'unavailable':Math.abs(x)>=1?deskFormatNumber(x,{maximumFractionDigits:2}):deskPrice(x);
  const frame={'1h':'hourly','4h':'four-hour','1d':'daily','1wk':'weekly'}[row.chart?.interval]||'chart';
  if(pending)return `${row.symbol}: reconcile the pending paper order before considering another entry. The existing strategy's order and exit rules remain authoritative.`;
  if(held)return `${row.symbol}: manage the existing paper position using its recorded exit. ${readFresh?structureSummary:'Its chart observation needs a fresh update; do not infer a new entry from the older chart.'}`;
  if(!hasChart||!readFresh)return `${row.symbol}: ${row.input_status?.message||row.chart?.input_status?.message||'the matching completed chart needs an update.'} A current entry and exit map cannot be established from these inputs. Reassess after the missing chart data arrives.`;
  const bars=row.chart?.bars||[],prior=bars.at(-2)?.[4],move=deskNum(prior)!==null&&prior>0&&deskNum(m.close)!==null?100*(m.close/prior-1):null;
  const sentence=[`${row.symbol} closed at ${price(m.close)}${move===null?'':`, ${move>=0?'up':'down'} ${deskFmt(Math.abs(move),2)}% on the latest ${frame} candle`}${deskNum(m.relative_volume)!==null?` on ${deskFmt(m.relative_volume,2)}× its usual volume`:''}.`];
  const obstacle=side>0?m.resistance:side<0?m.support:null,warning=side>0?m.support:side<0?m.resistance:null;
  const brokenAgainst=side>0&&m.structure_breach==='bullish_failed'||side<0&&m.structure_breach==='bearish_failed';
  const failedSwing=side>0?deskNum(m.last_swing_low):side<0?deskNum(m.last_swing_high):null;
  if(side&&deskNum(obstacle)!==null&&side*(obstacle-m.close)>0){const distance=Math.abs(obstacle-m.close),atr=m.atr14>0?` (${deskFmt(distance/m.atr14,2)} ATR)`:'';sentence.push(`The next ${side>0?'resistance':'support'} test is ${price(obstacle)}, ${deskFmt(100*distance/m.close,2)}% away${atr}.`);}
  const riskPivot=typeof setupRiskPivotExplanation==='function'?setupRiskPivotExplanation(row,now):null;
  if(['failed','at_level'].includes(riskPivot?.state))sentence.push(riskPivot.text);
  const localConflict=conflicts.find(x=>!/(broad participation|risk appetite|volatility backdrop|relative-strength rank)/i.test(x));
  if(localConflict)sentence.push(localConflict);
  else if(structureSign>0&&trendSign>=0)sentence.push(`The ${side>0?'rising':'falling'} swings and 50-bar trend support this direction.`);
  else if(structureSign<0&&trendSign<0)sentence.push(`Both the swing pattern and 50-bar trend oppose this ${side>0?'long':'short'} idea.`);
  else sentence.push(structureSummary);
  const backdrop=[];
  if(deskNum(breadth.pct50)!==null)backdrop.push(`${deskFmt(breadth.pct50)}% of the market is above its 50-day average`);
  if(deskNum(risk.risk_on)!==null&&risk.of>0)backdrop.push(`${deskFmt(risk.risk_on,0)} of ${deskFmt(risk.of,0)} market comparisons favor taking more risk`);
  if(vix!==null&&vix>=30)backdrop.push(`VIX is elevated at ${deskFmt(vix,2)}`);
  if(backdrop.length)sentence.push(`Backdrop: ${backdrop.join('; ')}.`);
  const conditions=[];
  if(brokenAgainst){
    if(failedSwing!==null)conditions.push(`The ${side>0?'long':'short'} chart read remains on hold until a completed ${frame} close back ${side>0?'above':'below'} the failed swing at ${price(failedSwing)} and a new valid entry map is available; a reclaim alone is not an entry.`);
    else conditions.push(`The ${side>0?'long':'short'} chart read remains on hold until the failed structure is resolved and a new valid entry map is available.`);
    if(side&&deskNum(obstacle)!==null)conditions.push(`A close ${side>0?'above resistance':'below support'} at ${price(obstacle)} does not clear the failed structure or satisfy the entry condition; the recovery level and a fresh valid entry map remain required.`);
    if(side&&deskNum(warning)!==null)conditions.push(`A close ${side>0?'below support':'above resistance'} at ${price(warning)} would weaken the near-term chart further; it does not replace the failed swing reference.`);
  }else{
    if(side&&deskNum(obstacle)!==null)conditions.push(`a completed ${frame} close ${side>0?'above':'below'} ${price(obstacle)} would improve the chart`);
    if(side&&deskNum(warning)!==null)conditions.push(`a close ${side>0?'below':'above'} ${price(warning)} would weaken it`);
  }
  if(conditions.length)sentence.push(conditions.join('; ').replace(/^./,x=>x.toUpperCase())+'.');
  return sentence.join(' ');
}
function deskFactorAlignment(row,factors,{side,readFresh,breadthSign,risk,vix}){
  const byId=new Map((factors||[]).map(x=>[x.id,x])),tech=row?.technicals||{},metrics=tech.metrics||{},groups=[],factorDirections=[];
  const labels={price_trend:'Price and trend',participation:'Volume participation',relative_strength:'Relative strength versus SPY',momentum:'Momentum',market:'Market backdrop',catalysts:'Catalysts, positioning and book'};
  function add(group,id,raw,text=null,allowPartial=false){const f=byId.get(id);if(!f||!(f.status==='measured'||allowPartial&&f.status==='partial')||!raw||!side)return;const sign=raw*side,disposition=sign>0?'supports_setup':'opposes_setup';if(!groups.some(x=>x.id===group))groups.push({id:group,label:labels[group],support:0,against:0,evidence:[]});const g=groups.find(x=>x.id===group);if(sign>0)g.support++;else g.against++;const detail=String(text||f.detail||'').replace(/\s+/g,' ').trim().slice(0,160);if(!factorDirections.some(x=>x.group===group&&x.id===id&&x.disposition===disposition))factorDirections.push({group,id,disposition,label:f.label,text:detail});if(g.evidence.length<4&&!g.evidence.some(x=>x.label===f.label&&x.text===detail&&x.disposition===disposition))g.evidence.push({label:f.label,text:detail,disposition});}
  const get=id=>byId.get(id),finite=x=>typeof x==='number'&&Number.isFinite(x),higher=metrics.structure==='higher_highs_higher_lows',lower=metrics.structure==='lower_highs_lower_lows';
  if(readFresh){
    const structure=get('structure_integrity');if(structure?.status==='measured'){const value=String(structure.value||'');if(value==='bullish_failed')add('price_trend','structure_integrity',-1);else if(value==='bearish_failed')add('price_trend','structure_integrity',1);else if(higher)add('price_trend','structure_integrity',1);else if(lower)add('price_trend','structure_integrity',-1);}
    const breakout=get('breakout_quality');if(breakout?.status==='measured'){if(breakout.value?.state==='breakout')add('price_trend','breakout_quality',1);else if(breakout.value?.state==='breakdown')add('price_trend','breakout_quality',-1);}
    const retest=get('breakout_retest'),retestDirection=retest?.value?.direction,retestState=retest?.value?.state;if(retest?.status==='measured'&&['up','down'].includes(retestDirection)&&['retest_held','failed_retest'].includes(retestState))add('price_trend','breakout_retest',(retestDirection==='up'?1:-1)*(retestState==='retest_held'?1:-1));
    // Wyckoff sweep/reclaims are emitted as partial because volume is a
    // separate confirmation and the detector is a mechanical proxy. Let only
    // a volume-supported reclaim from the same, recent setup chart inform the
    // price group; stale, lost, unconfirmed and cross-timeframe events stay
    // descriptive context and never become directional evidence.
    const wyckoff=get('wyckoff_events'),chartInterval=row?.chart?.interval||tech.interval,frame=chartInterval==='1d'?'daily':(['1wk','1w'].includes(chartInterval)?'weekly':null),chartBars=row?.chart?.bars||[],lastBar=chartBars.at(-1),lastClose=deskNum(lastBar?.[4]),events=wyckoff?.status==='partial'&&frame&&Array.isArray(wyckoff.value?.events)?wyckoff.value.events:[];
    if(events.length&&chartBars.length&&Number.isFinite(lastClose))for(const event of events){
      const confirmedDate=String(event?.confirmed_at||'').slice(0,10),eventIndex=chartBars.findIndex(bar=>String(bar?.[0]||'').slice(0,10)===confirmedDate),age=chartBars.length-1-eventIndex,level=deskNum(event?.level),spring=event?.kind==='spring_candidate',upthrust=event?.kind==='upthrust_candidate',stillHeld=spring?lastClose>=level:upthrust?lastClose<=level:false;
      if(event?.interval!==frame||!['spring_candidate','upthrust_candidate'].includes(event?.kind)||event?.current_state!=='reclaim_held'||event?.volume_supported!==true||!Number.isFinite(event?.volume_ratio)||event.volume_ratio<1.25||!Number.isFinite(level)||eventIndex<0||age<0||age>5||!stillHeld)continue;
      const detail=spring?`Price swept below confirmed support at $${deskPrice(level)}, then closed back above it; the latest close still holds above support with ${deskFmt(event.volume_ratio,2)}× volume.`:`Price swept above confirmed resistance at $${deskPrice(level)}, then closed back below it; the latest close still holds below resistance with ${deskFmt(event.volume_ratio,2)}× volume.`;
      add('price_trend','wyckoff_events',spring?1:-1,detail,true);
    }
    const averages=['sma10','sma20','sma50','sma200'].filter(id=>get(id)?.status==='measured'&&finite(get(id).value));if(averages.length){const up=averages.filter(id=>metrics.close>get(id).value).length,down=averages.filter(id=>metrics.close<get(id).value).length,source=averages[0];if(up>down)add('price_trend',source,1,`${up} of ${averages.length} measured daily averages are below price.`);else if(down>up)add('price_trend',source,-1,`${down} of ${averages.length} measured daily averages are above price.`);}
    const timeframes=get('higher_timeframe_map')?.value;if(Array.isArray(timeframes))for(const frame of timeframes.filter(x=>x?.current===true&&['1wk','1mo'].includes(x.interval))){if(frame.structure==='higher_highs_higher_lows')add('price_trend','higher_timeframe_map',1,`${frame.interval} completed swings are rising.`);else if(frame.structure==='lower_highs_lower_lows')add('price_trend','higher_timeframe_map',-1,`${frame.interval} completed swings are falling.`);}
    const wave=get('elliott_wave'),count=wave?.value,confirmation=count?.confirmation,waveSide=count?.direction==='bullish'?1:count?.direction==='bearish'?-1:0,waveClose=metrics.close,waveLevel=confirmation?.price;
    // A historical breakout does not keep voting after price closes back
    // through its confirmation. Count Elliott only when a completed break was
    // observed and the latest measured close still holds beyond that level.
    if(wave?.status==='measured'&&waveSide&&confirmation?.observed===true&&confirmation.current_beyond_level===true&&finite(waveClose)&&finite(waveLevel)&&waveSide*(waveClose-waveLevel)>0){
      const invalidation=count.invalidation?.price,detail=`${String(count.phase||'Elliott count').replaceAll('_',' ')}; latest completed close ${deskPrice(waveClose)} still ${waveSide>0?'above':'below'} the confirmed level ${deskPrice(waveLevel)}${finite(invalidation)?'; invalidation '+deskPrice(invalidation):''}.`;
      add('price_trend','elliott_wave',waveSide,detail);
    }
    for(const [id] of (typeof SETUP_FACTOR_GROUPS==='undefined'?[]:SETUP_FACTOR_GROUPS.find(x=>x[0]==='Chart patterns')?.[1]||[])){const f=get(id),rows=Array.isArray(f?.value)?f.value:[];if(f?.status!=='measured')continue;for(const pattern of rows){if(pattern?.state!=='confirmed_break'||pattern.measured_target_status==='reached')continue;const direction=pattern.direction==='up'?1:pattern.direction==='down'?-1:0;if(direction)add('price_trend',id,direction,`${pattern.kind?.replaceAll('_',' ')||id} confirmed break ${direction>0?'up':'down'}; chart level ${finite(pattern.neckline)?deskPrice(pattern.neckline):finite(pattern.resistance)?deskPrice(pattern.resistance):finite(pattern.support)?deskPrice(pattern.support):'see chart geometry'}.`);}}
    const rsi=get('rsi');if(rsi?.status==='measured'&&finite(rsi.value)){if(rsi.value>=55)add('momentum','rsi',1);else if(rsi.value<=45)add('momentum','rsi',-1);}
    const hist=get('macd_histogram'),close=deskNum(row?.technicals?.metrics?.close),atr=deskNum(row?.technicals?.metrics?.atr14);
    // MACD is denominated in dollars. Treat sub-cent/near-zero numerical
    // residue as neutral relative to the instrument's price and range instead
    // of manufacturing a momentum conflict from floating-point noise.
    const histFloor=Math.max(close!==null?Math.abs(close)*0.0001:0,atr!==null?Math.abs(atr)*0.01:0,1e-12);
    if(hist?.status==='measured'&&finite(hist.value)&&Math.abs(hist.value)>histFloor)add('momentum','macd_histogram',Math.sign(hist.value));
    const stoch=get('slow_stochastic');if(stoch?.status==='measured'&&finite(stoch.value?.slow_k)){if(stoch.value.slow_k>=60)add('momentum','slow_stochastic',1);else if(stoch.value.slow_k<=40)add('momentum','slow_stochastic',-1);}
    const rs=get('relative_strength_spy');if(rs?.status==='measured'&&finite(rs.value)&&Math.abs(rs.value)>=.02)add('relative_strength','relative_strength_spy',Math.sign(rs.value),`Across 126 matched sessions, the stock ${rs.value>0?'outperformed':'underperformed'} SPY by ${(100*Math.abs(rs.value)).toFixed(1)} percentage points.`);
    const sixMonth=get('six_month_momentum');if(sixMonth?.status==='measured'&&finite(sixMonth.value)&&sixMonth.value!==0)add('momentum','six_month_momentum',Math.sign(sixMonth.value));
    const dmi=get('adx_dmi');if(dmi?.status==='measured'&&finite(dmi.value?.adx)&&dmi.value.adx>=20&&finite(dmi.value?.pdi)&&finite(dmi.value?.mdi)&&Math.abs(dmi.value.pdi-dmi.value.mdi)>=5)add('momentum','adx_dmi',dmi.value.pdi>dmi.value.mdi?1:-1,`ADX ${deskFmt(dmi.value.adx)} confirms trend strength; ${dmi.value.pdi>dmi.value.mdi?'+DI':'−DI'} leads by ${deskFmt(Math.abs(dmi.value.pdi-dmi.value.mdi))} points.`);
    const tensor=get('tensor_timeframes'),tensorValue=tensor?.value;
    // Treat the complete Tensor weekly/daily/hourly agreement as one grouped
    // momentum observation. Its seven internal votes are already part of the
    // v698 state calculation and must not be multiplied into seven desk votes.
    if(tensor?.status==='measured'&&tensorValue?.available_frames===3&&['bullish','bearish'].includes(tensorValue.direction))
      add('momentum','tensor_timeframes',tensorValue.direction==='bullish'?1:-1,`Tensor v${tensorValue.frames.find(Boolean)?.version||'698'} agrees ${tensorValue.direction==='bullish'?'up':'down'} on weekly, daily and hourly completed bars; its 7 component votes count here as one momentum input.`);
    const divergenceRows=['daily_divergences','weekly_divergences'].map(id=>get(id)).filter(f=>f?.status==='measured');
    const divergenceFamilies=[
      {group:'momentum',label:'momentum',indicators:new Set(['RSI14','MACD12_26_9','SlowStochastic14_3_3'])},
      {group:'participation',label:'volume participation',indicators:new Set(['OBV','ADLine','MFI14','VolumeEMA5_20'])}
    ];
    for(const f of divergenceRows){
      const raw=Array.isArray(f.value)?f.value:Array.isArray(f.value?.events)?f.value.events:[];
      let events=raw.length&&typeof raw[0]==='object'?raw:(raw.length?raw.map(text=>({kind:/\bbearish\b/i.test(text)?'bearish':/\bbullish\b/i.test(text)?'bullish':null,divergence_type:/\bhidden\b/i.test(text)?'hidden':'regular'})):[]);
      if(!events.length&&((f.id==='daily_divergences'&&tech.interval==='1d')||(f.id==='weekly_divergences'&&tech.interval==='1wk')))events=(tech.divergences||[]).filter(x=>x.current_status!=='invalidated');
      const eligible=events.filter(x=>x.kind&&x.current_status!=='invalidated'&&(x.divergence_type!=='hidden'||x.continuation_alignment==='aligned'));
      for(const family of divergenceFamilies){
        const familyEvents=eligible.filter(x=>family.indicators.has(x.indicator)),directions=new Set(familyEvents.map(x=>x.kind));
        const gaugeLabels=[...new Set(familyEvents.filter(x=>directions.has(x.kind)).map(x=>x.indicator_label||x.indicator).filter(Boolean))];
        if(directions.has('bullish'))add(family.group,f.id,1,`Bullish ${f.id.startsWith('daily')?'daily':'weekly'} ${family.label} divergence in ${gaugeLabels.join(', ')||'available gauges'}; grouped once per timeframe.`);
        if(directions.has('bearish'))add(family.group,f.id,-1,`Bearish ${f.id.startsWith('daily')?'daily':'weekly'} ${family.label} divergence in ${gaugeLabels.join(', ')||'available gauges'}; grouped once per timeframe.`);
      }
    }
    const obv=get('obv');if(obv?.status==='measured'&&finite(obv.value?.change20_volume_fraction)&&Math.abs(obv.value.change20_volume_fraction)>=.05)add('participation','obv',Math.sign(obv.value.change20_volume_fraction));
    const ad=get('accumulation_distribution');if(ad?.status==='measured'&&finite(ad.value?.change20_volume_fraction)&&Math.abs(ad.value.change20_volume_fraction)>=.05)add('participation','accumulation_distribution',Math.sign(ad.value.change20_volume_fraction));
    const mfi=get('mfi');if(mfi?.status==='measured'&&finite(mfi.value)){if(mfi.value>=60)add('participation','mfi',1);else if(mfi.value<=40)add('participation','mfi',-1);}
  }
  if(side){if(breadthSign)add('market','breadth',breadthSign);const ratio=finite(risk?.risk_on)&&finite(risk?.of)&&risk.of>0?risk.risk_on/risk.of:null;if(ratio!==null){const countText=`${risk.risk_on} of ${risk.of} market comparisons favor taking more risk.`;if(ratio>=.75)add('market','market_regime',1,countText);else if(ratio<=.25)add('market','market_regime',-1,countText);}}
  const result=groups.map(g=>({...g,disposition:g.support&&g.against?'mixed':g.support?'supports_setup':g.against?'opposes_setup':'context_only'}));
  const observed=new Set((factors||[]).filter(x=>['measured','partial','stale'].includes(x.status)).map(x=>x.category)).size;
  const measured=(factors||[]).filter(x=>x.status==='measured').length,partial=(factors||[]).filter(x=>x.status==='partial').length;
  const summary=result.filter(x=>x.disposition!=='context_only').map(x=>`${x.label} ${x.disposition==='supports_setup'?(x.id==='price_trend'?'support':'supports'):x.disposition==='opposes_setup'?(x.id==='price_trend'?'oppose':'opposes'):'is mixed'}`).join(' · ');
  return {method:'grouped-measured-evidence-3',summary:summary||'No grouped directional evidence is strong enough to vote.',measured_factors:measured,partial_factors:partial,categories_with_observations:observed,groups:result.map(({id,label,disposition,support,against,evidence})=>({id,label,disposition,supporting_inputs:support,opposing_inputs:against,evidence})),factor_directions:factorDirections,volatility_caution:finite(vix)&&vix>=30?'Elevated VIX is treated as risk context, not a directional vote.':null};
}
function deskResolveDirection(row,factors,{readFresh=false,held=false,pending=false}={}){
  const source=['bullish','bearish'].includes(row?.direction)?row.direction:null,m=row?.technicals?.metrics||{},bar=row?.chart?.bars?.at(-1),last=deskNum(m.close),fresh=readFresh&&row?.chart?.context_only!==true;
  const result=(direction,rule,strength,evidence=[],tie_break=null)=>({direction,source_direction:source,contrary_to_source:!!source&&source!==direction,rule,strength,evidence:evidence.slice(0,3),tie_break,freshness:fresh?'current':'needs_refresh',paper_order_authority:'none'});
  const byId=new Map((factors||[]).map(x=>[x.id,x])),hard=[];
  const add=(direction,priority,rule,text,at=null)=>{if(direction==='bullish'||direction==='bearish')hard.push({direction,priority,rule,text:String(text||rule),at:Number.isFinite(Date.parse(at||''))?Date.parse(at):0});};
  if(fresh){
    if(m.structure_breach==='bullish_failed')add('bearish',100,'confirmed_swing_failure','The latest completed close broke the confirmed rising swing structure.');
    if(m.structure_breach==='bearish_failed')add('bullish',100,'confirmed_swing_failure','The latest completed close broke the confirmed falling swing structure.');
    // Derive the same decisive structure failure when the upstream summary
    // omitted its breach flag. Only pivots confirmed by the latest completed
    // bar can reverse the call; future confirmations never enter the read.
    const completedAt=Date.parse(row?.chart?.last_completed_at||bar?.[0]||''),swingKind=source==='bullish'?'support':source==='bearish'?'resistance':null,
      latestSourceSwing=swingKind&&Number.isFinite(completedAt)?(row?.technicals?.pivots||[])
        .filter(p=>p?.kind===swingKind&&Number.isFinite(p.price)&&p.price>0&&Number.isFinite(Date.parse(p.confirmed_at||''))&&Date.parse(p.confirmed_at)<=completedAt)
        .sort((a,b)=>(Number(b.index)||0)-(Number(a.index)||0))[0]:null,
      pivotFailed=!!latestSourceSwing&&last!==null&&(source==='bullish'?last<latestSourceSwing.price:last>latestSourceSwing.price);
    if(pivotFailed&&!(source==='bullish'?m.structure_breach==='bullish_failed':m.structure_breach==='bearish_failed'))
      add(source==='bullish'?'bearish':'bullish',100,'confirmed_swing_failure',`The latest close ${deskPrice(last)} broke the confirmed ${source==='bullish'?'support':'resistance'} swing at ${deskPrice(latestSourceSwing.price)}.`,row?.chart?.last_completed_at);
    const retest=byId.get('breakout_retest'),rv=retest?.value,rt=row?.chart?.bars||[],retestIndex=Array.isArray(rv)?-1:rt.findIndex(b=>b?.[0]===rv?.retest_at),lastIndex=rt.length-1,stillFailed=rv?.state==='failed_retest'&&Number.isFinite(last)&&Number.isFinite(rv.level)&&((rv.direction==='up'&&last<=rv.level)||(rv.direction==='down'&&last>=rv.level)),recentRetest=retestIndex>=0&&lastIndex-retestIndex<=5,retestBar=retestIndex>=0?rt[retestIndex]:null,
      // A failed range break is a warning against the old direction, not by
      // itself proof of a new trend. Require a later completed close beyond
      // the failure candle's opposite extreme before it can overrule the
      // grouped trend, momentum and participation evidence as a hard reversal.
      failureFollowThrough=!!retestBar&&lastIndex>retestIndex&&Number.isFinite(retestBar[2])&&Number.isFinite(retestBar[3])&&
        (rv?.direction==='down'?last>retestBar[2]:rv?.direction==='up'?last<retestBar[3]:false);
    if(retest?.status==='measured'&&stillFailed&&recentRetest&&failureFollowThrough)add(rv.direction==='up'?'bearish':'bullish',90,'failed_breakout_retest',`${rv.direction==='up'?'Upside':'Downside'} breakout retest failed at ${deskPrice(rv.level)}; a later completed close also cleared the failure candle's ${rv.direction==='up'?'low':'high'} at ${deskPrice(rv.direction==='up'?retestBar[3]:retestBar[2])}.`,rv.retest_at);
    const breakout=byId.get('breakout_quality'),bv=breakout?.value;
    if(breakout?.status==='measured'&&bv?.state==='breakout')add('bullish',bv.relative_volume>=1.5?80:65,bv.relative_volume>=1.5?'volume_confirmed_breakout':'confirmed_range_breakout',`The latest close broke the prior 20-bar high${bv.relative_volume>=1.5?' on confirming volume':' without 1.5× volume confirmation'}.`,row?.chart?.last_completed_at);
    if(breakout?.status==='measured'&&bv?.state==='breakdown')add('bearish',bv.relative_volume>=1.5?80:65,bv.relative_volume>=1.5?'volume_confirmed_breakdown':'confirmed_range_breakdown',`The latest close broke the prior 20-bar low${bv.relative_volume>=1.5?' on confirming volume':' without 1.5× volume confirmation'}.`,row?.chart?.last_completed_at);
    for(const f of factors||[])if(f?.status==='measured'&&Array.isArray(f.value))for(const pattern of f.value){
      if(pattern?.state!=='confirmed_break'||pattern.measured_target_status==='reached'||!['up','down'].includes(pattern.direction))continue;
      add(pattern.direction==='up'?'bullish':'bearish',60,'confirmed_pattern_break',`${String(pattern.kind||f.id).replaceAll('_',' ')} confirmed ${pattern.direction} break.`,pattern.confirmed_at||pattern.at||row?.chart?.last_completed_at);
    }
  }
  if(hard.length){hard.sort((a,b)=>b.priority-a.priority||b.at-a.at||Number(b.direction===source)-Number(a.direction===source)||a.direction.localeCompare(b.direction));const chosen=hard[0],sameTier=hard.filter(x=>x.priority===chosen.priority&&x.at===chosen.at),contradictory=sameTier.some(x=>x.direction!==chosen.direction);let tieBreak=null;if(contradictory){const trend=last!==null&&deskNum(m.sma50)!==null?(last>m.sma50?'bullish':last<m.sma50?'bearish':null):null;tieBreak=trend&&sameTier.some(x=>x.direction===trend)?'same-time hard evidence resolved by current close versus the 50-bar average':source&&sameTier.some(x=>x.direction===source)?'same-time hard evidence resolved in favor of the recorded sleeve side':'same-time hard evidence resolved by stable direction order';if(trend&&sameTier.some(x=>x.direction===trend))chosen.direction=trend;else if(source&&sameTier.some(x=>x.direction===source))chosen.direction=source;else chosen.direction='bearish';}
    return result(chosen.direction,chosen.rule,'decisive_hard',[chosen.text,...sameTier.filter(x=>x!==chosen).map(x=>x.text)],tieBreak);
  }
  const aligned=deskFactorAlignment(row,factors,{side:1,readFresh:fresh,breadthSign:0,risk:{},vix:null}),weights={price_trend:5,participation:3,relative_strength:3,momentum:2,market:1},votes=[];
  for(const group of aligned.groups){const net=group.supporting_inputs-group.opposing_inputs;if(net){const direction=net>0?'bullish':'bearish';votes.push({group:group.id,direction,net,weight:weights[group.id]||1,text:`${group.label} evidence favors the ${direction} side across its measured checks.`});}}
  const sum=votes.reduce((total,v)=>total+(v.direction==='bullish'?v.weight:-v.weight),0);
  if(votes.length===1){
    const only=votes[0];
    if(source&&source!==only.direction&&only.group!=='price_trend')return result(source,'single_non_price_group_retains_source','single_group',[only.text],`${only.text} is the only directional group, so it does not overturn the recorded chart side.`);
    return result(only.direction,only.group==='price_trend'?'single_price_group_direction':'single_group_direction','single_group',[only.text],source&&source===only.direction?'The one measured directional group agrees with the recorded chart side.':null);
  }
  if(sum!==0){const direction=sum>0?'bullish':'bearish',opposition=votes.some(v=>v.direction!==direction),distinctSupport=votes.filter(v=>v.direction===direction).length;if(!opposition&&distinctSupport>=2&&Math.abs(sum)>=5)return result(direction,'distinct_group_confluence','strong_confluence',votes.filter(v=>v.direction===direction).map(v=>v.text));if(Math.abs(sum)>=2)return result(direction,'weighted_group_balance','convergent',votes.filter(v=>v.direction===direction).map(v=>v.text),opposition?'Higher-priority price, volume and momentum evidence outweighs the disagreement.':null);return result(direction,'weighted_group_balance','convergent',votes.filter(v=>v.direction===direction).map(v=>v.text));}
  if(votes.length){const ordered=[...votes].sort((a,b)=>b.weight-a.weight||Math.abs(b.net)-Math.abs(a.net)||(['price_trend','participation','relative_strength','momentum','market'].indexOf(a.group)-['price_trend','participation','relative_strength','momentum','market'].indexOf(b.group))),winner=ordered[0];return result(winner.direction,'priority_group_tiebreak','tie_break',[winner.text],'Confirmed price events → volume participation → relative strength → momentum → market context → recorded sleeve side.');}
  if(source)return result(source,held||pending?'position_state_tiebreak':'recorded_sleeve_side_tiebreak',held||pending?'locked':'source_tiebreak',[held?'No fresh measured evidence changes the existing position direction.':pending?'No fresh measured evidence changes the pending order direction.':'No higher-priority measured price event resolves the direction; the recorded sleeve side breaks the tie.'],'price structure → failed retest → volume-confirmed move → distinct groups → market context → recorded sleeve side.');
  if(last!==null&&deskNum(m.sma50)!==null&&last!==m.sma50)return result(last>m.sma50?'bullish':'bearish','close_vs_50_bar_average','fallback',['Price relative to the measured 50-bar average breaks the directional tie.']);
  const hist=deskNum(m.macd_histogram);if(hist)return result(hist>0?'bullish':'bearish','macd_histogram_tiebreak','fallback',['The measured MACD histogram sign breaks the directional tie.']);
  if(Array.isArray(bar)&&deskNum(bar[1])!==null&&deskNum(bar[4])!==null&&bar[1]!==bar[4])return result(bar[4]>bar[1]?'bullish':'bearish','latest_completed_candle_tiebreak','fallback',['The latest completed candle direction breaks the tie.']);
  return result('neutral','no_directional_evidence','unresolved',['No fresh price event, independent evidence group, trend measure or completed-candle direction is available to support a bullish or bearish call.'],'A directional call requires at least one current measured price input; missing evidence is not a long signal.');
}
function deskSalientSnippet(value,max=260){
  const text=String(value||'').replace(/\s+/g,' ').trim();if(text.length<=max)return text;
  const prefix=text.slice(0,max),boundary=Math.max(prefix.lastIndexOf('. '),prefix.lastIndexOf('; '));
  if(boundary>=Math.floor(max*.55))return prefix.slice(0,boundary+1).trimEnd()+' …';
  const word=prefix.lastIndexOf(' ');return (word>0?prefix.slice(0,word):prefix).trimEnd()+'…';
}
function deskReadAlignmentNote(tone){return tone==='positive'?' It supports the current call.':tone==='caution'?' It conflicts with the current call.':tone==='mixed'?' The detected gauges point in different directions.':'';}
function deskDivergenceFinding(factor,tone){
  const events=(Array.isArray(factor?.value)?factor.value:[]).filter(x=>x&&['bullish','bearish'].includes(x.kind)&&['regular','hidden'].includes(x.divergence_type)&&!['invalidated','superseded'].includes(x.current_status)&&(x.divergence_type!=='hidden'||x.continuation_alignment==='aligned'));
  if(!events.length)return null;
  const grouped=new Map();for(const event of events){
    const key=[event.kind,event.divergence_type,event.first_confirmed_at||event.first_index,event.confirmed_at||event.second_index].join('|');
    if(!grouped.has(key))grouped.set(key,{event,indicators:[]});
    const group=grouped.get(key),rawIndicator=String(event.indicator_label||event.indicator||'indicator'),indicatorKey=rawIndicator.toUpperCase().replace(/[^A-Z0-9]/g,''),indicator=({RSI14:'RSI',MACD12269:'MACD',SLOWSTOCHASTIC1433:'slow stochastic',OBV:'OBV',ADLINE:'A/D line',MFI14:'MFI',VOLUMEEMA520:'volume EMA 5–20'})[indicatorKey]||rawIndicator.replace(/_/g,' ').replace(/([A-Z]+)(\d)/g,'$1 $2');
    if(!group.indicators.includes(indicator))group.indicators.push(indicator);
  }
  const formatDate=value=>{const match=typeof value==='string'&&value.match(/^(\d{4})-(\d{2})-(\d{2})/);if(!match)return null;const date=new Date(Date.UTC(Number(match[1]),Number(match[2])-1,Number(match[3])));return deskDateFormatter('en-US',{month:'short',day:'numeric',timeZone:'UTC'}).format(date);};
  const lines=[];for(const {event,indicators} of [...grouped.values()].slice(0,2)){
    const bullish=event.kind==='bullish',hidden=event.divergence_type==='hidden',priceMove=hidden?(bullish?'held a higher low':'made a lower high'):(bullish?'made a lower low':'made a higher high'),gaugeMove=hidden?(bullish?'made a lower low':'made a higher high'):(bullish?'made higher lows':'made lower highs'),names=indicators.length===1?indicators[0]:indicators.length===2?indicators.join(' and '):indicators.slice(0,-1).join(', ')+' and '+indicators.at(-1),first=formatDate(event.first_confirmed_at),second=formatDate(event.confirmed_at),dates=first&&second?` at the ${first} and ${second} swing pivots`:'';
    lines.push(`${hidden?'Hidden':'Regular'} ${event.kind} divergence: price ${priceMove} while ${names} ${gaugeMove}${dates}.`);
  }
  if(grouped.size>2)lines.push(`${grouped.size-2} additional distinct divergence pattern${grouped.size-2===1?'':'s'} remain in the full factor review.`);
  const directions=new Set([...grouped.values()].map(x=>x.event.kind));
  if(directions.size>1){
    const sideText=kind=>{const types=new Set([...grouped.values()].filter(x=>x.event.kind===kind).map(x=>x.event.divergence_type==='regular'?'reversal':'continuation'));return `${kind} ${[...types].join(' and ')} signal${types.size===1?'':'s'}`;};
    return `${lines.join(' ')} The ${sideText('bullish')} points up; the ${sideText('bearish')} points down. These signals conflict.`;
  }
  return lines.join(' ')+deskReadAlignmentNote(tone);
}
function deskBreakoutFinding(factor,tone){
  const value=factor?.value;if(!value||!['breakout','breakdown'].includes(value.state))return null;
  const up=value.state==='breakout',level=deskNum(up?value.prior_high:value.prior_low),relativeVolume=deskNum(value.relative_volume),distance=deskNum(value.distance_atr),name=up?'upside':'downside';
  const volume=relativeVolume===null?'Volume confirmation is unavailable.':relativeVolume>=1.5?`Volume was ${relativeVolume.toFixed(2)} times its recent average and confirms the move.`:`Volume was ${relativeVolume.toFixed(2)} times its recent average, below the 1.5× confirmation level.`;
  const extension=distance===null?'':distance>2?` Price extended ${distance.toFixed(2)} average daily ranges beyond the break.`:` Price remained within two average daily ranges of the break.`;
  return `The latest close broke ${up?'above the prior 20-day high':'below the prior 20-day low'}${level===null?'':` at $${deskPrice(level)}`}. ${volume}${extension}${deskReadAlignmentNote(tone)}`;
}
function deskSalientEvidenceClass(factor){
  const id=String(factor?.id||''),value=factor?.value;
  if(id==='breakout_quality'&&['breakout','breakdown'].includes(value?.state))return'confirmed_price_event';
  if(id==='breakout_retest'&&['retest_held','failed_retest'].includes(value?.state))return'confirmed_price_event';
  if(id==='structure_integrity'&&['bullish_failed','bearish_failed'].includes(value))return'confirmed_price_event';
  if(Array.isArray(value)&&value.some(x=>x?.state==='confirmed_break'&&x.measured_target_status!=='reached'))return'confirmed_price_event';
  if(id==='relative_strength_spy')return'relative_strength';
  if(['obv','accumulation_distribution','mfi'].includes(id))return'participation';
  return'other';
}
function deskSelectSalientFindings(factorChecks,evidenceAlignment,existingSalient,limit=5){
  const aligned=new Map();for(const item of evidenceAlignment?.factor_directions||[]){if(!aligned.has(item.id))aligned.set(item.id,new Set());aligned.get(item.id).add(item.disposition);}
  const toneFor=id=>{const directions=aligned.get(id)||new Set();return directions.has('supports_setup')&&directions.has('opposes_setup')?'mixed':directions.has('opposes_setup')?'caution':directions.has('supports_setup')?'positive':'neutral';};
  const candidates=[];let order=0;
  for(const factor of factorChecks||[])if(factor.material&&['measured','partial'].includes(factor.status)){
    const tone=toneFor(factor.id),statusRank=factor.status==='measured'?2:1;
    const evidenceClass=deskSalientEvidenceClass(factor),classRank={confirmed_price_event:60,participation:26,relative_strength:24,other:0}[evidenceClass]||0;
    const priority=classRank+({caution:100,mixed:95,positive:80,neutral:65}[tone]||60)+statusRank;
    const divergence=['daily_divergences','weekly_divergences'].includes(factor.id)?deskDivergenceFinding(factor,tone):null,breakout=factor.id==='breakout_quality'?deskBreakoutFinding(factor,tone):null;
    const evidenceGroup=evidenceClass==='confirmed_price_event'?'price_trend':evidenceClass==='participation'?'participation':evidenceClass==='relative_strength'?'relative_strength':null;
    candidates.push({id:factor.id,label:factor.label,text:divergence||breakout||deskSalientSnippet(factor.detail),tone,category:evidenceGroup?`evidence:${evidenceGroup}`:factor.category,evidence_group:evidenceGroup,evidence_class:evidenceClass,priority,order:order++,source:'factor'});
  }
  for(const group of evidenceAlignment?.groups||[])if(['supports_setup','opposes_setup','mixed'].includes(group.disposition)){
    const tone=group.disposition==='opposes_setup'?'caution':group.disposition==='mixed'?'mixed':'positive';
    const support=Number(group.supporting_inputs)||0,against=Number(group.opposing_inputs)||0;
    const stance=group.disposition==='opposes_setup'?'opposes the setup':group.disposition==='supports_setup'?'supports the setup':'is mixed';
    const supportText=`${support} ${support===1?'input supports':'inputs support'}`,againstText=`${against} ${against===1?'input opposes':'inputs oppose'}`;
    const balance=group.disposition==='mixed'?`${supportText} and ${againstText}`:group.disposition==='opposes_setup'?againstText:supportText;
    // Specific findings are selected separately above; keep this group summary
    // additive instead of repeating the same factor in the top read.
    candidates.push({id:`alignment_${group.id}`,label:group.label,text:`${group.label} evidence ${stance} (${balance}).`,tone,category:`alignment:${group.id}`,evidence_group:group.id,priority:({caution:92,mixed:88,positive:72}[tone]||60)+Math.min(4,support+against),order:order++,source:'alignment'});
  }
  for(const item of existingSalient||[]){
    const tone=['caution','positive','mixed'].includes(item.tone)?item.tone:'neutral';
    candidates.push({...item,tone,category:item.category||`observation:${item.id||item.label}`,priority:({caution:58,mixed:56,positive:54,neutral:50}[tone]||50)+(Number(item._salience)||0)/100,order:order++,source:'observation'});
  }
  const ordered=candidates.filter(x=>x.text).sort((a,b)=>b.priority-a.priority||a.order-b.order||String(a.label).localeCompare(String(b.label))),chosen=[],usedIds=new Set(),usedCategories=new Set(),usedEvidenceGroups=new Set();
  const take=(items,preferNewCategory=true)=>{const pool=items.filter(x=>!usedIds.has(x.id)),eligible=x=>!x.evidence_group||!usedEvidenceGroups.has(x.evidence_group)||x.source==='alignment'&&x.evidence_group==='price_trend',candidate=(preferNewCategory?pool.find(x=>!usedCategories.has(x.category)&&eligible(x)):null)||pool.find(eligible);if(!candidate)return false;chosen.push(candidate);usedIds.add(candidate.id);usedCategories.add(candidate.category);if(candidate.evidence_group)usedEvidenceGroups.add(candidate.evidence_group);return true;};
  // Lead with the strongest confirmed event, surface the best opposing clue,
  // then reserve separate slots for independent volume and relative strength.
  take(ordered.filter(x=>x.evidence_class==='confirmed_price_event'));
  take(ordered.filter(x=>x.source==='factor'&&['caution','mixed'].includes(x.tone)));
  take(ordered.filter(x=>x.source==='factor'&&x.evidence_group==='participation'));
  take(ordered.filter(x=>x.source==='factor'&&x.evidence_group==='relative_strength'));
  take(ordered.filter(x=>x.source==='alignment'&&['caution','mixed'].includes(x.tone)));
  take(ordered.filter(x=>x.source==='alignment'&&x.tone==='positive'));
  while(chosen.length<Math.min(5,Math.max(0,limit))&&take(ordered));
  return chosen.map(({id,label,text,tone,category,source,evidence_group})=>({id,label,text,tone,category,source,...(evidence_group?{evidence_group}:{})}));
}
function deskWords(x) { return String(x??'').replace(/_/g,' ').slice(0,280); }
function deskCurrentCboeVolatility(packet,now,market) {
  const feed=packet?.context?.market_volatility;
  if(feed?.source!=='Cboe Global Markets'||typeof setupCurrentDaily!=='function')return null;
  const names=['VIX','VIX3M','VVIX','SKEW'],rows=names.map(name=>{
    const point=feed.indices?.[name],close=deskNum(point?.close),asOf=point?.as_of,dayStart=typeof asOf==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(asOf)?Date.parse(asOf+'T00:00:00Z'):NaN;
    const received=Date.parse(point?.received_at||feed.received_at||''),validDay=Number.isFinite(dayStart)&&new Date(dayStart).toISOString().slice(0,10)===asOf;
    const current=close!==null&&close>0&&validDay&&setupCurrentDaily(asOf,now,market)&&Number.isFinite(received)&&received>=dayStart&&received<=now;
    return {name,close,as_of:asOf||null,current};
  }),current=rows.filter(x=>x.current),vix=current.find(x=>x.name==='VIX');
  if(!current.length)return null;
  const text=current.map(x=>`${x.name} ${x.close.toFixed(2)} (as of ${x.as_of})`).join('; '),notCurrent=rows.filter(x=>!x.current).map(x=>`${x.name}${x.as_of?` last close ${x.as_of}`:' not supplied'}`).join(', ');
  return {status:current.length===names.length?'available':'partial',vix:vix?.close??null,text:`Cboe daily closes: ${text}.${notCurrent?` Other indices are stale or missing: ${notCurrent}.`:''} Daily closes, not intraday quotes.`};
}
// A new regular session has no new hourly candle until its first hour closes.
// The previous close must be witnessed by the same verified calendar receipt;
// neither weekends nor early closes are inferred from wall-clock age.
function deskPreviousSessionHourlyCurrent(chart,market,reference,now) {
  const time=value=>typeof value==='string'&&/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)?Date.parse(value):NaN;
  if(chart?.interval!=='1h'||market?.calendar_verified!==true||market.market_open!==true)return false;
  const at=time(market.at),open=time(market.open),close=time(market.close),previous=time(market.previous_session_close),last=time(chart.last_completed_at);
  return [at,open,close,previous,last,reference,now].every(Number.isFinite)&&last===previous&&previous<open&&open<close&&
    open<=at&&at<=reference&&reference<=now&&now-reference<=300000&&reference-at<=300000&&
    open<=now&&now<Math.min(open+3600000,close);
}
function deskChartCadenceCurrent(chart,tech,market,snapshotAt,now,{onDemand=false,allowPreviousSession=false}={}) {
  if(chart?.input_status?.current===false)return false;
  const last=Date.parse(chart?.last_completed_at||tech?.as_of||chart?.bars?.at(-1)?.[0]),sessionAt=Date.parse(market?.at),reference=onDemand?now:snapshotAt;
  const closed=market?.market_open===false&&Number.isFinite(sessionAt)&&Number.isFinite(reference)&&reference<=now&&sessionAt<=reference&&reference-sessionAt<=300000;
  const maxAge={'1h':closed?4*86400000:2*3600000,'4h':8*3600000,'1d':4*86400000,'1wk':11*86400000}[chart?.interval]||0;
  return Number.isFinite(last)&&last<=now&&(now-last<=maxAge||allowPreviousSession&&!onDemand&&deskPreviousSessionHourlyCurrent(chart,market,reference,now));
}
function buildDeskRead(row,snapshot,packet,now=Date.now(),analysisCache=new Map()) {
  const terminal=snapshot?.terminal||{}, tech=row.technicals, m=tech?.metrics||{}, e=(row.evidence||[]).find(x=>x.id===row.primary_evidence_id)||(row.evidence||[]).find(x=>x.active)||row.evidence?.[0], sourceDirection=row.direction;
  const onDemand=row.on_demand===true,held=row.stage==='paper_entry'||e?.held===true,pending=e?.pending_order===true;let technicalAmbiguity=false;
  const current=typeof setupDailyPacketCurrent==='function'&&setupDailyPacketCurrent(packet,now,terminal.market);
  const ctx=packet?.context||{}, usable=current?ctx:{}, considered=[], conflicts=[], changes=[], signs={};
  function fact(id,label,text,{status='available',tone='neutral',salience=1,family=null,sign=0}={}) {
    const f={id,label,text,status,tone};considered.push(f);
    if(status==='available'&&family&&sign) { if(!signs[family]) signs[family]=new Set(); signs[family].add(sign); }
    f._salience=salience;return f;
  }
  const missing=(id,label,reason)=>fact(id,label,reason,{status:'missing'});
  const orient=x=>side?x*side:0;
  const tone=x=>x>0?'positive':x<0?'negative':'neutral';
  const hasChart=!!tech&&tech.status!=='unavailable'&&deskNum(m.close)!==null;
  const chartOnly=row.chart?.context_only===true;
  const marketData=terminal.market||{},snapshotAt=Date.parse(snapshot?.observed_at_utc),snapshotFresh=Number.isFinite(snapshotAt)&&snapshotAt<=now&&now-snapshotAt<=300000;
  const chartFresh=hasChart&&deskChartCadenceCurrent(row.chart,tech,marketData,snapshotAt,now,{onDemand,allowPreviousSession:row.horizon==='intraday'}),readFresh=chartFresh&&(onDemand||snapshotFresh);
  let factorChecks=typeof setupFactorChecks==='function'?setupFactorChecks(row,snapshot,packet,analysisCache,now):[];
  if(!readFresh)factorChecks=factorChecks.map(f=>['measured','partial'].includes(f.status)&&['Chart patterns','Price structure','Measured levels and targets','Trend and averages','Momentum','Volume','Divergences','Stretch and volatility','Candles and gaps','Wyckoff','Tensor'].includes(f.category)?{...f,status:'stale',detail:`Chart snapshot is stale for its cadence. ${f.detail}`} : f);
  factorChecks=deskDailyVolumeClockAbstention(row,factorChecks);
  const directionResolution=deskResolveDirection(row,factorChecks,{readFresh,held,pending}),direction=directionResolution.direction,side=direction==='bullish'?1:direction==='bearish'?-1:0,readRow=direction===sourceDirection?row:{...row,direction};
  const primaryScore=deskNum(e?.score),lectorScore=deskNum(row.ranker?.opp);
  const score=primaryScore!==null?{value:primaryScore,max:null,label:e.score_basis==='predicted_net_qqq_excess'?'Model estimate':'Strategy evidence',basis:e.score_basis||'native strategy score',display:e.score_basis==='predicted_net_qqq_excess'?(primaryScore*100).toFixed(2)+'% vs QQQ':deskFmt(primaryScore,4)}:lectorScore!==null?{value:lectorScore,max:100,label:'ChartsLector relative score',basis:'opportunity_v2',display:deskFmt(lectorScore)+'/100'}:{value:null,max:null,label:'Strategy evidence',basis:'rule_based',display:'Rule-based'};
  if(e) {
    fact('sleeve','Strategy read',`${e.strategy_name||'Strategy'}: ${deskWords(e.reason)||'recorded condition'}. ${onDemand?(e.active?'A separate current sleeve trigger is present.':'The linked sleeve is waiting for its next condition or window.'):row.stage==='paper_entry'?'An existing paper entry, not a new trigger.':row.stage==='triggered'?'Its recorded entry window is open.':'Waiting for its next condition or window.'}`,{salience:4});
    const features=Object.entries(e.features||{}).filter(([,v])=>['string','number','boolean'].includes(typeof v)&&!(typeof v==='number'&&!Number.isFinite(v)));
    if(features.length)fact('features','Strategy measurements',features.map(([k,v])=>`${deskWords(k)}: ${typeof v==='number'?deskFmt(v,5):deskWords(v)}`).join('; '));
    else missing('features','Strategy measurements','No additional per-signal model measurements are in this public observation.');
    fact('plan','Plan and risk',[
      e.entry_price!=null?`Recorded entry ${deskPrice(e.entry_price)}`:e.reference_price!=null?`Reference ${deskPrice(e.reference_price)}`:'No numeric entry level',
      e.stop_price!=null?`stop ${deskPrice(e.stop_price)}`:'exit follows the strategy rule',
      e.target_price!=null?`target ${deskPrice(e.target_price)}`:null,e.exit_at?`scheduled exit ${e.exit_at}`:e.exit_rule,
      `mode: ${deskWords(e.mode)}`,e.pending_order?'Order outcome pending':held?'Existing paper position':e.risk_permission===false?'New entry is risk-blocked':e.risk_permission===true?'Recorded risk permission passed':'Current entry permission is not supplied'
    ].filter(Boolean).join('; '),{salience:e.pending_order||e.risk_permission===false?8:2,tone:e.pending_order||e.risk_permission===false?'caution':'neutral'});
  } else { const requested=direction==='bullish'?'long-side':direction==='bearish'?'short-side':'direction-neutral';fact('sleeve',onDemand?'On-demand chart read':'Research watch',onDemand?'A '+requested+' chart assessment. No current sleeve trigger accompanies it.':'This name comes from the daily opportunity list; no sleeve trigger accompanies it.',{salience:3});missing('features','Strategy measurements','No linked sleeve signal for this watch.'); }
  if(onDemand&&primaryScore===null&&lectorScore===null)Object.assign(score,{label:'Chart read',basis:'unscored',display:'Unscored'});
  if(lectorScore!==null)fact('lector','ChartsLector',`Opportunity ${deskFmt(lectorScore)}/100; ${deskWords(row.ranker.stage)}. `+['momentum','breakout','rs','low_atr','expansion','risk'].filter(k=>deskNum(row.ranker[k])!==null).map(k=>`${deskWords(k)} ${deskFmt(row.ranker[k])}`).join('; '),{salience:lectorScore>=90||lectorScore<=10?6:2});
  else missing('lector','ChartsLector','This symbol has no current opportunity row in the ranker universe.');
  const related=(terminal.setup_observation?.candidates||[]).filter(c=>c.symbol===row.symbol);
  const eligible=related.filter(c=>{
    const sleeve=terminal.sleeves?.find(s=>s.book_label===c.book_label),observed=Date.parse(c.observed_at),available=Date.parse(c.usable_after),signal=Date.parse(c.signal_at),end=Date.parse(c.entry_window_end||c.expires_at),start=Date.parse(c.entry_window_start);
    return sleeve?.enabled===true&&c.qualification==='ready'&&['candidate','waiting'].includes(c.state)&&!c.held&&!c.pending_order&&c.risk_permission!==false&&Number.isFinite(observed)&&observed<=now&&now-observed<=86400000&&Number.isFinite(available)&&available<=now&&signal<=available&&observed>=available&&(!c.entry_window_end||Number.isFinite(end))&&(!Number.isFinite(end)?c.state==='waiting'&&now-observed<=300000:end>now)&&(!c.entry_window_start||Number.isFinite(start)&&start<=now);
  });
  const mechanisms=ds=>new Set(eligible.filter(c=>ds.includes(c.direction)).map(c=>typeof SETUP_FAMILIES!=='undefined'?(SETUP_FAMILIES[c.family]||c.family):c.family));
  const aligned=mechanisms([direction]),opposed=mechanisms([side>0?'bearish':'bullish']);
  fact('agreement','Other strategies',`${aligned.size} mechanism${aligned.size===1?'':'s'} share this direction; ${opposed.size} point the other way. ${related.length-eligible.length} other observations are holding, gated, stale or not eligible. Parameter variants are grouped.`,{status:related.length?'available':'missing',salience:opposed.size?9:aligned.size>1?5:1,tone:opposed.size?'caution':'neutral'});
  if(opposed.size){conflicts.push('Eligible strategies disagree on direction for this symbol.');technicalAmbiguity=true;}
  const peers=(row.evidence||[]).filter(x=>x!==e);
  if(peers.length)fact('peer_details','Contributing sleeve details',peers.map(p=>`${p.strategy_name||deskWords(p.native_family)}: ${deskWords(p.reason)}; ${p.score_basis?deskWords(p.score_basis)+' '+deskFmt(p.score,5):'rule-based'}; ${Object.entries(p.features||{}).filter(([,v])=>typeof v==='number'||typeof v==='boolean').map(([k,v])=>deskWords(k)+' '+v).join(', ')}`).join(' | '));
  const chartState=hasChart?'available':'missing';
  let structureSign=0,trendSign=0,divergenceConflict=false,stretched=false,structureSummary='';
  if(hasChart) {
    const brokenStructure=['bullish_failed','bearish_failed'].includes(m.structure_breach);
    structureSign=brokenStructure?0:orient(m.structure==='higher_highs_higher_lows'?1:m.structure==='lower_highs_lower_lows'?-1:0);
    trendSign=deskNum(m.sma50)!==null?orient(m.close>m.sma50?1:m.close<m.sma50?-1:0):0;
    const breachText=m.structure_breach==='bullish_failed'?`The latest completed close is below the last confirmed swing low (${deskPrice(m.last_swing_low)}); the earlier upward structure is no longer intact.`:m.structure_breach==='bearish_failed'?`The latest completed close is above the last confirmed swing high (${deskPrice(m.last_swing_high)}); the earlier downward structure is no longer intact.`:'';
    structureSummary=breachText||`The measured ${row.chart?.interval||''} swings show ${deskWords(m.structure||'no clear structure')}.`;
    const breachDirection=m.structure_breach==='bullish_failed'?'bearish':m.structure_breach==='bearish_failed'?'bullish':null;
    const breachOpposes=brokenStructure&&breachDirection!==direction;
    if(breachOpposes)conflicts.push(breachText);
    fact('structure','Price structure',`Last confirmed swings: ${deskWords(m.structure||'not enough confirmed swings')}; close ${deskPrice(m.close)}. ${breachText} `+['sma20','sma50','sma200'].map(k=>`${k.replace('sma','')}-bar average ${deskPrice(m[k])}`).join('; '),{salience:brokenStructure?9:structureSign?6:3,tone:brokenStructure||breachOpposes?'caution':tone(structureSign),family:'price',sign:structureSign});
    if(trendSign&&structureSign&&trendSign!==structureSign){conflicts.push('The swing structure and the 50-bar trend point in different directions.');technicalAmbiguity=true;}
    fact('momentum','Momentum',`RSI ${deskFmt(m.rsi14)}; MACD ${deskPrice(m.macd)}, signal ${deskPrice(m.macd_signal)}, histogram ${deskPrice(m.macd_histogram)}. ${deskMacdHistogramText(m,tech.momentum?.histogram)}.`,{status:deskNum(m.rsi14)!==null||deskNum(m.macd)!==null?'available':'missing',salience:deskNum(m.rsi14)!==null&&(m.rsi14>=80||m.rsi14<=20)?6:2});
    const divergenceRead=deskDivergenceSummary(factorChecks,tech,row.chart?.interval,m,direction),currentDivergences=divergenceRead.divergences;
    divergenceConflict=divergenceRead.divergenceConflict;
    fact('divergence','Regular and hidden divergence',divergenceRead.text,{status:divergenceRead.status,salience:currentDivergences.length?8:1,tone:divergenceConflict?'caution':'neutral'});
    if(divergenceRead.counterpoint){conflicts.push(divergenceRead.counterpoint);if(divergenceRead.supporting.length)technicalAmbiguity=true;}
    if(divergenceRead.rsiMacdConflict){conflicts.push('RSI and MACD detect different confirmed swing pairs, so they do not form one joint divergence confirmation.');technicalAmbiguity=true;}
    fact('participation','Volume and volatility',`Volume ${deskFmt(m.relative_volume,2)}× its prior 20-bar average; ATR ${deskPrice(m.atr14)} (${deskFmt(m.atr_percent,2)}% of price).`,{status:deskNum(m.relative_volume)!==null||deskNum(m.atr14)!==null?'available':'missing',salience:m.relative_volume>=2||m.atr_percent>=6?7:2});
    fact('candle','Latest candle',`Close ${deskFmt((m.candle?.close_location??NaN)*100)}% up the range; upper wick ${deskFmt((m.candle?.upper_wick_fraction??NaN)*100)}%, lower wick ${deskFmt((m.candle?.lower_wick_fraction??NaN)*100)}%; ${deskWords(m.candle?.engulfing?m.candle.engulfing+' engulfing body':m.candle?.direction||'unknown')}.`,{salience:m.candle?.engulfing?5:1});
    fact('geometry','Levels, trendlines and patterns',[...(tech.levels||[]).map(x=>`${x.label}: ${deskPrice(x.price)}`),...(tech.lines||[]).map(x=>`${x.kind} trendline ${x.state}`),...(tech.patterns||[]).map(x=>`${deskWords(x.kind)}: ${deskWords(x.state)}`)].join('; ')||'No confirmed geometry in the available bars.',{salience:tech.patterns?.length?5:2});
    const distance=m.atr14>0&&deskNum(m.sma20)!==null?(m.close-m.sma20)/m.atr14:null;
    stretched=distance!==null&&orient(distance)>2;
    const obstacle=side>0?m.resistance:m.support,room=m.atr14>0&&deskNum(obstacle)!==null?Math.abs(obstacle-m.close)/m.atr14:null;
    fact('location','Entry location',`${distance===null?'20-bar extension unavailable':`${deskFmt(distance,2)} ATR from the 20-bar average`}; ${room===null?'no confirmed opposing level in this range':`${deskFmt(room,2)} ATR to ${side>0?'resistance':'support'}`}.`,{salience:stretched||room!==null&&room<.5?8:2,tone:stretched||room!==null&&room<.5?'caution':'neutral'});
    if(stretched)conflicts.push(`Price is ${deskFmt(Math.abs(distance),2)} ATR ${side>0?'above':'below'} its 20-bar average${room!==null?`; the next ${side>0?'resistance':'support'} is ${deskFmt(room,2)} ATR away`:''}.`);
    const invalidation=side>0?m.support:side<0?m.resistance:null;
    const breachAgainst=side>0&&m.structure_breach==='bullish_failed'||side<0&&m.structure_breach==='bearish_failed';
    const failedSwing=side>0?deskNum(m.last_swing_low):side<0?deskNum(m.last_swing_high):null;
    if(breachAgainst){
      changes.push(failedSwing!==null
        ?`Reconsider this ${side>0?'long':'short'} chart idea only after a completed ${row.chart.interval} close back ${side>0?'above':'below'} the failed swing at ${deskPrice(failedSwing)} and a new valid entry map is available. A reclaim alone is not an entry.`
        :`Reconsider this ${side>0?'long':'short'} chart idea only after the failed structure is resolved and a new valid entry map is available.`);
      if(deskNum(obstacle)!==null)changes.push(`A sustained close ${side>0?'above resistance':'below support'} at ${deskPrice(obstacle)} does not satisfy the recovery condition above; the failed structure must first be reclaimed on a sustained close.`);
      if(deskNum(invalidation)!==null)changes.push(`A completed ${row.chart.interval} close ${side>0?'below support':'above resistance'} at ${deskPrice(invalidation)} would weaken the near-term chart further; it does not replace the failed swing reference.`);
    }else{
      if(deskNum(invalidation)!==null)changes.push(`A completed ${row.chart.interval} close ${side>0?'below support':'above resistance'} at ${deskPrice(invalidation)} would weaken this read.`);
      if(side&&deskNum(obstacle)!==null)changes.push(`A sustained close ${side>0?'above resistance':'below support'} at ${deskPrice(obstacle)}, with stronger participation, would improve it.`);
    }
  } else {
    for(const [id,label] of [['structure','Price structure'],['momentum','Momentum'],['divergence','Regular and hidden divergence'],['participation','Volume and volatility'],['candle','Latest candle'],['geometry','Levels, trendlines and patterns'],['location','Entry location']])missing(id,label,'Completed chart measurements are not available for this setup.');
  }
  const wave=tech?.elliott, preferred=wave?.preferred, alternate=wave?.alternate;
  if(wave?.ambiguous?.length){conflicts.push('A wave count changes validity between arithmetic and percentage scales; its projected trade levels are withheld.');technicalAmbiguity=true;}
  if(preferred&&preferred.status!=='invalidated'){
    const opposing=side&&orient(preferred.direction==='bullish'?1:-1)<0, completed=['five_waves_complete','abc_recovery_watch'].includes(preferred.phase);
    const competing=alternate&&alternate.status!=='invalidated'&&alternate.direction!==preferred.direction;
    const breakAt=Date.parse(preferred.confirmation?.observed_at),countAt=Date.parse(preferred.confirmed_at),knownBreak=preferred.confirmation?.observed===true&&Number.isFinite(breakAt)&&Number.isFinite(countAt)&&countAt<=breakAt&&breakAt<=now;
    const waveConfirmation=knownBreak?`${preferred.confirmation.summary||`An earlier completed candle closed ${preferred.direction==='bullish'?'above':'below'} ${deskPrice(preferred.confirmation.price)}.`} A new entry needs a fresh setup; that earlier break is history.`:preferred.confirmation?.observed===true?'The prior confirmation clock is unavailable; it does not establish a current trigger.':preferred.confirmation?.summary||preferred.confirmation?.rule||'';
    fact('elliott','Elliott wave scenario',`${deskWords(preferred.phase)} · ${preferred.direction}, ${deskWords(preferred.degree)} swings. ${waveConfirmation} ${preferred.invalidation?`The count fails on an intrabar move ${preferred.direction==='bullish'?'below':'above'} ${deskPrice(preferred.invalidation.price)}.`:''}${alternate?` Alternate: ${deskWords(alternate.phase)}, ${alternate.direction}.`:''}`,{salience:opposing||competing||completed?8:4,tone:opposing||competing?'caution':'neutral'});
    // The count uses the same price geometry as structure/Fibonacci. It is not
    // another independent score vote and cannot create sleeve order permission.
  if(preferred.length_comparison?.scale_disagreement){conflicts.push('The wave-length rule differs between percentage and arithmetic scales; the count needs a clearer structure.');technicalAmbiguity=true;}
  if(opposing){conflicts.push('The preferred wave scenario points against this setup direction.');technicalAmbiguity=true;}
    if(competing){conflicts.push('Valid wave alternatives point in different directions; wait for the stated price confirmation.');technicalAmbiguity=true;}
  if(preferred.phase==='five_waves_complete'){conflicts.push('The measured five-wave move is complete; a fresh continuation entry needs a new confirmed structure.');technicalAmbiguity=true;}
    if(preferred.invalidation)changes.push(`The ${preferred.direction} wave scenario fails ${preferred.direction==='bullish'?'below':'above'} ${deskPrice(preferred.invalidation.price)}; reassess the count if that level trades.`);
  }else fact('elliott','Elliott wave scenario',wave?.status==='warming'?'More confirmed swings are needed for a wave count.':wave?.status==='ready'?'No current continuation count remains valid.':'No clear rule-valid wave count in the available completed candles.',{status:wave&&wave.status!=='unavailable'?'available':'missing',salience:1});
  if(chartOnly)conflicts.push(`The available ${row.chart.interval} chart is context for a ${row.horizon} setup; its entry-timeframe chart is missing.`);
  const frameReads=(terminal.setup_observation?.charts?.series||[]).filter(c=>c.symbol===row.symbol).map(c=>{
    const key=c.symbol+'|'+c.interval,a=typeof setupFactorAnalyzeChart==='function'?setupFactorAnalyzeChart(c,analysisCache,now):analysisCache.has(key)?analysisCache.get(key):typeof explainChart==='function'?explainChart(c,now):null;
    if(!analysisCache.has(key))analysisCache.set(key,a);
    const current=a?.status!=='unavailable'&&deskNum(a?.metrics?.close)!==null&&deskChartCadenceCurrent(c,a,terminal.market,Date.parse(snapshot?.observed_at_utc),now,{onDemand,allowPreviousSession:row.horizon!=='crypto'});
    return {interval:c.interval,structure:a?.metrics?.structure||null,breach:a?.metrics?.structure_breach||null,status:a?.status||'unavailable',current};
  });
  fact('timeframes','Timeframe coverage',frameReads.length?frameReads.map(a=>`${a.interval}: ${a.status==='unavailable'?'unavailable':!a.current?'stale ('+deskWords(a.structure||a.status)+')':deskWords(a.structure||a.status)+(a.breach?' (structure breached)':'')}`).join('; '):'Weekly, daily and hourly alignment is unknown without those charts.',{status:frameReads.some(a=>a.current)?'available':frameReads.some(a=>a.status!=='unavailable')?'stale':'missing'});
  if(frameReads.some(a=>a.current&&!a.breach&&a.structure==='higher_highs_higher_lows')&&frameReads.some(a=>a.current&&!a.breach&&a.structure==='lower_highs_lower_lows')){conflicts.push('The supplied chart timeframes disagree on swing direction.');technicalAmbiguity=true;}
  const contextStatus=current?'available':packet?.context?'stale':'missing';
  const marketPresent={breadth:()=>Object.values(usable.breadth?.current||{}).some(x=>deskNum(x)!==null),mood:()=>deskNum(usable.mood_ring?.composite)!==null,volatility:()=>Object.values(usable.mood_ring?.inputs||{}).some(x=>deskNum(x)!==null),risk_appetite:()=>deskNum(usable.risk_appetite?.risk_on)!==null,pulse:()=>Object.values(usable.pulse||{}).some(x=>deskNum(x.score)!==null),themes:()=>usable.themes?.rows?.length>0,screens:()=>usable.screens?.screens?.length>0};
  function market(id,label,text,opts={}){
    let status=contextStatus==='available'&&!marketPresent[id]?.()?'missing':contextStatus;
    if(['themes','screens'].includes(id)&&status==='available'&&!setupCurrentDaily(usable[id]?.as_of,now,terminal.market))status='stale';
    return fact(id,label,text,{status,...opts});
  }
  const b=usable.breadth?.current||{},risk=usable.risk_appetite||{},mood=usable.mood_ring||{},officialVolatility=deskCurrentCboeVolatility(packet,now,terminal.market),vix=officialVolatility?.vix??(current?deskNum(mood.inputs?.vix):null);
  const breadthSign=deskNum(b.pct50)!==null?orient(b.pct50>=60?1:b.pct50<=40?-1:0):0;
  market('breadth','Market breadth',`Above 20/50/200-day averages: ${deskFmt(b.pct20)}% / ${deskFmt(b.pct50)}% / ${deskFmt(b.pct200)}%; advances ${deskFmt(b.adv,0)}, declines ${deskFmt(b.dec,0)}. Up/down 4%: ${deskFmt(b.up4,0)}/${deskFmt(b.dn4,0)}; 13% in 34 bars: ${deskFmt(b.up13_34,0)}/${deskFmt(b.dn13_34,0)}; 25% in 63 bars: ${deskFmt(b.up25_63,0)}/${deskFmt(b.dn25_63,0)}.`,{salience:breadthSign?6:2,tone:tone(breadthSign),family:'market',sign:breadthSign});
  market('mood','Market mood',`Mood Ring ${deskFmt(mood.composite)}; ${deskWords(mood.state||'state unavailable')}${mood.divergence?`; ${deskWords(mood.divergence)}`:''}.`,{salience:2});
  if(officialVolatility)fact('volatility','Volatility backdrop',officialVolatility.text,{status:officialVolatility.status,salience:vix>=30?8:2,tone:vix>=30?'caution':'neutral'});
  else market('volatility','Volatility backdrop',`VIX ${deskFmt(vix,2)}, VIX3M ${deskFmt(current?mood.inputs?.vix3m:null,2)}; term ratio ${deskFmt(current?mood.inputs?.term_ratio:null,3)}; VVIX ${deskFmt(current?mood.inputs?.vvix:null)}, skew ${deskFmt(current?mood.inputs?.skew:null)}.`,{salience:vix>=30?8:2,tone:vix>=30?'caution':'neutral'});
  market('risk_appetite','Market comparisons',`${deskFmt(risk.risk_on,0)} of ${deskFmt(risk.of,0)} market comparisons favor taking more risk. `+(risk.ratios||[]).map(x=>`${x.pair}: points toward ${x.risk_on?'taking more risk':'safer investments'}, one-month change ${deskFmt(x.chg_1m,2)}`).join('; '),{salience:2});
  market('pulse','Market pulse',Object.entries(usable.pulse||{}).map(([k,v])=>`${k}: ${deskWords(v.state)}, score ${deskFmt(v.score)}, RAM ${deskFmt(v.ram)}`).join('; ')||'No current equal-weight index pulse.');
  const themes=usable.themes?.rows||[],matched=themes.find(x=>x.sym===row.symbol),leaders=[...themes].filter(x=>deskNum(x.rs21)!==null).sort((a,b)=>b.rs21-a.rs21).slice(0,3),laggards=[...themes].filter(x=>deskNum(x.rs21)!==null).sort((a,b)=>a.rs21-b.rs21).slice(0,3);
  market('themes','Sectors and themes',`21-observation relative-strength percentiles: highest readings ${leaders.map(x=>x.sym+' '+deskFmt(x.rs21,2)).join(', ')||'unavailable'}; lowest readings ${laggards.map(x=>x.sym+' '+deskFmt(x.rs21,2)).join(', ')||'unavailable'}. Each compares its current close/SPY ratio with its own recent history.`);
  if(matched)fact('sector_binding','This instrument in the theme map',`${matched.sym}: ${deskWords(matched.quadrant)}; RS readings over 5/21/63/126 observations ${[matched.rs5,matched.rs21,matched.rs63,matched.rs126].map(x=>deskFmt(x,2)).join(' / ')}. The 21-observation value is a relative-strength percentile within its own recent history, not a return or peer rank; volume ${deskNum(matched.rvol)!==null?deskFmt(matched.rvol/100,2):'unknown'}× its reference average. Rotation: ${Object.entries(matched.rrr_tf||{}).map(([k,v])=>k+' '+deskWords(v.quadrant)).join('; ')}.`,{status:setupCurrentDaily(usable.themes?.as_of,now,terminal.market)?'available':'stale',salience:3});
  else missing('sector_binding','Instrument-to-sector link','No explicit issuer-to-sector mapping accompanies this symbol; the broader theme map is still considered.');
  const screens=(usable.screens?.screens||[]).filter(s=>s.hits?.some(h=>h.sym===row.symbol));
  market('screens','Other screens',screens.length?screens.map(s=>s.label).join('; '):'No matching hit in the supplied screens.');
  const histories=[['Mood',usable.mood_ring?.history,'v'],['Breadth above 50-day',usable.breadth?.history,'p50'],['Market comparisons favoring more risk',usable.risk_appetite?.history,'n'],['QQQE pulse',usable.pulse?.QQQE?.history,'sc'],['RSP pulse',usable.pulse?.RSP?.history,'sc']];
  const shifts=histories.flatMap(([label,rows,key])=>{
    const known=(rows||[]).filter(x=>deskNum(x[key])!==null&&x.d<=packet.as_of),a=known.at(-6),z=known.at(-1);
    return a&&z?[`${label}: ${deskFmt(z[key]-a[key],2)} change across five recorded observations (${a.d} to ${z.d})`]:[];
  });
  fact('context_change','How the backdrop is changing',shifts.join('; ')||'Five-observation context changes are not available.',{status:shifts.length?'available':current?'missing':contextStatus});
  const past=x=>Number.isFinite(Date.parse(x))&&Date.parse(x)<=now;
  const earnings=(marketData.earnings||[]).filter(x=>(x.symbol||x.sym)===row.symbol&&x.actual_occurrence_source&&[x.announcement_at,x.first_published_at,x.signal_available_at].every(past)&&Date.parse(x.announcement_at)<=Date.parse(x.signal_available_at)&&Date.parse(x.first_published_at)<=Date.parse(x.signal_available_at));
  const iv=(marketData.option_iv||[]).filter(x=>(x.underlying||x.symbol)===row.symbol&&deskNum(x.iv)!==null&&x.iv>=0&&past(x.market_at));
  fact('events','Reported company events',earnings.length?earnings.map(x=>`Earnings occurrence ${x.announcement_at}; published ${x.first_published_at}; available ${x.signal_available_at}.`).join('; '):'No causal, symbol-specific earnings occurrence is supplied.',{status:earnings.length?'available':'missing',salience:earnings.length?7:1});
  fact('options','Options context',iv.length?iv.map(x=>`${x.symbol}: IV ${deskFmt(x.iv,4)}, ${deskWords(x.mode)} from ${x.source}, measured ${x.market_at}`).join('; '):'No causal, symbol-specific implied-volatility observation is supplied.',{status:iv.length?'available':'missing'});
  const quotes=(marketData.benchmark_quotes||[]).filter(q=>deskNum(q.bid)!==null&&deskNum(q.ask)!==null&&q.ask>=q.bid&&past(q.market_at)&&past(q.received_at));
  fact('benchmarks','Benchmark quotes',quotes.map(q=>`${q.symbol}: ${deskFmt(q.bid,2)} / ${deskFmt(q.ask,2)} (${q.feed}, market time ${q.market_at})`).join('; ')||'No timestamped benchmark quotes are supplied.',{status:quotes.length?'available':'missing'});
  missing('fundamentals','Company fundamentals','A normalized issuer financial-quality assessment is not connected to this read.');
  missing('story','News and catalysts','A verified, timestamped company news narrative is not supplied.');
  missing('credit','Macro and credit','No complete macro calendar or credit-stress series is supplied.');
  missing('positioning','Dealer positioning','Dealer gamma and options positioning are not collected by this public feed.');
  const sleeve=terminal.sleeves?.find(s=>s.book_label===e?.book_label);
  fact('operations','Desk and paper status',`${marketData.market_open===true?'Market session open':marketData.market_open===false?'Market session closed':'Market session not supplied'}. ${sleeve?`${sleeve.title||'Linked sleeve'}: ${deskWords(sleeve.state)}.`:'No linked sleeve.'} ${(terminal.errors||[]).length} reported desk issue(s).`,{tone:terminal.errors?.length?'caution':'neutral'});
  const trades=(terminal.closed_trades||[]).filter(x=>x.book_label===e?.book_label&&past(x.exit_at));
  fact('track_record','Linked paper history',trades.length?`${trades.length} recent closed paper trades for the linked sleeve are available; ${trades.filter(x=>x.net_pnl>0).length} positive, ${trades.filter(x=>x.net_pnl<0).length} negative. This read has its own forward record.`:'No linked closed-paper-trade history in this observation.',{status:trades.length?'available':'missing'});
  // Cadence-aware context freshness, not a five-minute expiry on daily charts.
  // A captured market receipt belongs to the snapshot that contains it. Re-aging
  // that same receipt on every GET changes an otherwise immutable saved read.
  // The snapshot itself still has the current-time five-minute freshness gate.
  fact('freshness','Data freshness',`Desk snapshot ${snapshotFresh?'current':'stale or unavailable'}; chart ${tech?.as_of||row.chart?.bars?.at(-1)?.[0]||'unavailable'}; market context ${packet?.as_of||'unavailable'}. ${chartFresh?'Chart age fits its cadence.':'Chart age is missing or outside its cadence.'} ${current?'Market context is current.':'Market context is missing or dated.'}`,{status:readFresh?'available':'stale',salience:!readFresh?10:1,tone:!readFresh?'caution':'neutral'});
  if(structureSign>0&&breadthSign<0)conflicts.push('The setup structure is supportive while broad participation works against it.');
  if(vix!==null&&vix>=30)conflicts.push('The elevated volatility backdrop makes a clean-looking chart less forgiving.');
  if(deskNum(risk.risk_on)!==null&&risk.of>0&&orient(risk.risk_on/risk.of<=.25?-1:risk.risk_on/risk.of>=.75?1:0)<0&&structureSign>0){const count=risk.risk_on,total=risk.of;conflicts.push(`${count} of ${total} market comparisons favor taking more risk, opposing the ${side>0?'bullish':'bearish'} chart direction.`);}
  if(matched&&setupCurrentDaily(usable.themes?.as_of,now,terminal.market)&&deskNum(matched.rs21)!==null&&orient(matched.rs21<=25?-1:matched.rs21>=75?1:0)<0&&structureSign>0)conflicts.push('This instrument’s relative strength against SPY is near the '+(matched.rs21<=25?'low':'high')+' end of its own recent history, opposing this direction.');
  const chartSupport=structureSign>0&&trendSign>=0,marketSupport=breadthSign>0;
  // Direction is always resolved separately. The call grades the evidence, not
  // its direction; mixed/against/unavailable are never final outcomes.
  let call='cautious';
  if(!changes.length)changes.push('A completed entry-timeframe structure with clear support and resistance would make this read more decisive.');
  // Keep change-of-view instructions tied to measured levels, freshness or
  // lifecycle state above. Conflicts are already listed separately; a generic
  // agreement sentence neither names the conflict nor gives a testable trigger.
  if(!current||!chartFresh)changes.push('A fresh completed chart and current market packet are needed before increasing conviction.');
  if(e?.pending_order)changes.push('The pending paper order needs a confirmed fill or cancellation outcome.');
  else if(e&&!held&&!onDemand&&e.risk_permission!==true)changes.push('A current sleeve evaluation with its risk decision is still needed for a new paper entry.');
  const evidenceAlignment=deskFactorAlignment(row,factorChecks,{side,readFresh,breadthSign,risk,vix});
  for(const group of evidenceAlignment.groups){
    if(group.disposition==='opposes_setup')conflicts.push(`${group.label} evidence opposes the ${side>0?'bullish':'bearish'} call; the call follows the stronger price evidence.`);
    else if(group.disposition==='mixed')conflicts.push(`${group.label} readings disagree: ${group.supporting_inputs} ${group.supporting_inputs===1?'supports':'support'} this view, while ${group.opposing_inputs} ${group.opposing_inputs===1?'points':'point'} the other way.`);
  }
  const coreSplit=evidenceAlignment.groups.some(g=>['price_trend','momentum','participation'].includes(g.id)&&g.disposition==='mixed');
  const split=evidenceAlignment.groups.filter(g=>g.disposition==='mixed').length;
  const localOpposition=evidenceAlignment.groups.some(g=>['price_trend','momentum','participation'].includes(g.id)&&g.disposition==='opposes_setup');
  const backdropOpposition=evidenceAlignment.groups.some(g=>g.id==='market'&&g.disposition==='opposes_setup');
  if(side&&readFresh&&!chartOnly){
    const supporting=evidenceAlignment.groups.filter(g=>g.disposition==='supports_setup').length,opposing=evidenceAlignment.groups.filter(g=>g.disposition==='opposes_setup').length;
    const materialConflict=technicalAmbiguity||coreSplit||localOpposition||backdropOpposition;
    // A fresh confirmed price break is itself a hard evidence group. Do not
    // require a second indicator to restate it before acknowledging its force;
    // measured opposition, split inputs or chart ambiguity still lower the grade.
    const strongHard=directionResolution.strength==='decisive_hard'&&opposing===0&&split===0&&!technicalAmbiguity;
    const strongConfluence=directionResolution.strength==='strong_confluence'&&supporting>=2&&opposing===0&&split===0&&!technicalAmbiguity;
    if(strongHard||strongConfluence||chartSupport&&marketSupport&&vix!==null&&vix<30&&!materialConflict&&opposing===0&&split===0)call='strong';
    else if(!materialConflict&&(chartSupport||directionResolution.strength==='convergent'&&supporting>opposing))call='constructive';
    else call='cautious';
  }
  const factorCounts={total:factorChecks.length,measured:factorChecks.filter(x=>x.status==='measured').length,partial:factorChecks.filter(x=>x.status==='partial').length,stale:factorChecks.filter(x=>x.status==='stale').length,insufficient_history:factorChecks.filter(x=>x.status==='insufficient_history').length,insufficient_validation:factorChecks.filter(x=>x.status==='insufficient_validation').length,not_scanned:factorChecks.filter(x=>x.status==='not_scanned').length,not_supplied:factorChecks.filter(x=>x.status==='not_supplied').length,not_applicable:factorChecks.filter(x=>x.status==='not_applicable').length};
  const historicalPatterns=readFresh&&typeof buildPatternHistory==='function'?buildPatternHistory(row.chart):null;
  const historicalSentence=historicalPatterns&&typeof patternHistorySentence==='function'?patternHistorySentence(historicalPatterns):null;
  if(historicalSentence)fact('historical_patterns','Earlier similar charts',historicalSentence,{salience:1});
  const existingSalient=considered.filter(x=>x.status==='available'||x.id==='freshness').sort((a,b)=>b._salience-a._salience||a.id.localeCompare(b.id));
  const salient=deskSelectSalientFindings(factorChecks,evidenceAlignment,existingSalient,5);
  // The public read needs human-readable detail, not duplicate raw OHLCV-derived
  // payloads. Keep the durable record bounded and reconstructable.
  // Persist stable factor IDs and dispositions. Labels/categories live once in
  // the static UI catalog; meaningful evidence stays with the setup read.
  const factorOutput=factorChecks.map(({id,status,detail,material})=>{
   // Each factor row is part of the user's audit trail, including negative
   // results such as "no crossover" and specific insufficiency reasons. Keep
   // measured and partial explanations in the saved read; omit only the
   // repetitive generic text for a missing feed, which the UI can state once.
   const text=String(detail||'').replace(/\s+/g,' ').trim();
   const keepDetail=!!text&&status!=='not_supplied';
   const maxDetailLength=id==='wyckoff_events'?768:id==='wyckoff_phase'?384:128;
   return keepDetail?[id,status,text.slice(0,maxDetailLength)+(text.length>maxDetailLength?'…':''),...(material?[1]:[])]:[id,status,...(material?[1]:[])];
  });
  const paragraph=deskReadNarrative(readRow,{held,pending,readFresh:readFresh&&!chartOnly,hasChart,structureSummary,structureSign,trendSign,conflicts,breadth:b,risk,vix,now});
  const clean=considered.map(({_salience,...f})=>({...f,text:String(f.text||'').replace(/\s+/g,' ').trim().slice(0,240)}));
  const profileFactor=id=>factorChecks.find(x=>x.id===id),profileReady=row.chart?.interval==='1d'&&readFresh&&['value_area_high','value_area_low','volume_poc'].every(id=>profileFactor(id)?.status==='partial'&&deskNum(profileFactor(id)?.value)!==null);
  const chart_levels=profileReady?[
    {kind:'volume_profile',label:'Daily-bar POC · proxy',price:profileFactor('volume_poc').value},
    {kind:'volume_profile',label:'Daily-bar value-area low · proxy',price:profileFactor('value_area_low').value},
    {kind:'volume_profile',label:'Daily-bar value-area high · proxy',price:profileFactor('value_area_high').value}
  ]:[];
  const rsLineFactor=factorChecks.find(x=>x.id==='rs_line_leadership'),rsValue=rsLineFactor?.value,chart_relative_strength=row.chart?.interval==='1d'&&rsLineFactor?.status==='measured'&&rsValue?.plot_compatible===true&&Array.isArray(rsValue.series)?{period:rsValue.period,through:rsValue.through,points:rsValue.series}:null;
  const directionEvidence=directionResolution.evidence.join(' '),sourceNote=directionResolution.contrary_to_source?` The original shortlist leaned ${sourceDirection}; this chart review calls it ${directionResolution.direction}. ${directionEvidence||'The call follows the latest measured price evidence.'}`:directionEvidence;
  const finalParagraph=[paragraph,sourceNote].filter(Boolean).join(' ');
  if(directionResolution.freshness!=='current')conflicts.push('Direction uses the recorded strategy side as the tie-break; refresh the chart before treating its levels as current.');
  return {method:DESK_READ_METHOD,call, direction_resolution:directionResolution,score,salient,conflicts:[...new Set(conflicts)],paragraph:finalParagraph,historical_patterns:historicalPatterns?{...historicalPatterns,summary:historicalSentence,summaries:patternHistorySentences(historicalPatterns)}:null,changes_mind:[...new Set(changes)],considered:clean,evidence_alignment:evidenceAlignment,factor_checks:factorOutput,factor_review:factorCounts,chart_levels,chart_relative_strength,recorded_at:null,read_id:null,scope:'All listed factors are checked for availability. Directional alignment groups related measured factors to avoid counting overlapping indicators as separate votes; missing or partial inputs never become positive evidence.'};
}


// Isolated source-clock adapter; original scorer sources remain unchanged.
// This adapter is appended after the hash-pinned original scorer. It changes
// only the evidence eligibility of volume-dependent factors when any supplied
// volume observation is absent; it does not alter indicator formulas, weights,
// thresholds, price-only factors, or the original scorer implementation.
function deskDailyVolumeClockAbstention(row,factors){
  if(row?.on_demand!==true||row?.chart?.interval!=='1d'||!Array.isArray(factors))return factors;
  const bars=row.chart.bars||[],hasMissingVolume=bars.some(bar=>!Array.isArray(bar)||bar[5]===null||bar[5]===undefined||!Number.isFinite(bar[5])||bar[5]<0);
  if(!hasMissingVolume)return factors;
  const clock=row.chart?.source_capture?.daily_volume_interval||{},clockStatus=clock.status||'unknown';
  const captureDate=clock.capture_date||'unknown capture date',barDate=clock.bar_date||'unknown bar date';
  const reason=clockStatus==='open_at_capture'
    ?`The latest daily bar is retained for its OHLC, but its New York-date volume interval was still open at the original source receipt (capture date ${captureDate}; bar date ${barDate}).`
    :clockStatus==='closed_as_observed'
      ?`The latest daily bar is retained for its OHLC, but the supplied daily volume history contains a missing observation (capture date ${captureDate}; bar date ${barDate}).`
      :`The latest daily bar is retained for its OHLC, but capture evidence does not verify closure of its New York-date volume interval (capture date ${captureDate}; bar date ${barDate}).`;
  const caveat=` ${reason} This is an interval-completeness abstention, not a provider-finality claim: finality is unknown and later provider revisions remain possible.`;
  const extraVolumeIds=new Set([
    'dollar_volume','effort_result','gap_taxonomy','high_tight_flag','bump_run_reversal',
    'climax_top','climax_run','selling_climax','volume_dry_up','power_earnings_gap',
    'anchored_vwap_gap','ytd_anchored_vwap','vwap_stdev_bands'
  ]);
  return factors.map(f=>{
    if(!f||typeof f!=='object')return f;
    const directVolume=f.category==='Volume'||(f.category==='Additional volume gauges'&&f.id!=='market_profile_tpo')||extraVolumeIds.has(f.id);
    if(directVolume)return {...f,status:'not_supplied',value:null,material:false,detail:caveat.trim()};
    // A price-only breakout remains readable, but never lets a missing current
    // volume value masquerade as a below-threshold confirmation.
    if(f.id==='breakout_quality'&&f.value&&typeof f.value==='object'){
      const detail=String(f.detail||'').replace(/;\s*volume (?:confirms|is below 1\.5×);?/i,'');
      return {...f,value:{...f.value,relative_volume:null},detail:`${detail}${detail?'.':''} Current-bar volume confirmation is unavailable.${caveat}`};
    }
    return f;
  });
}


export {explainChart,buildDeskRead,setupFactorChecks,DESK_READ_METHOD};
