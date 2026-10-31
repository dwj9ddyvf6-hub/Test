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
