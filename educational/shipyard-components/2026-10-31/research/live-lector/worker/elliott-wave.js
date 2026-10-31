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
