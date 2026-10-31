// A transparent interpretation of observations, never an order. Curation may
// consider its distinct conflicts without treating the qualitative call as a score.
var DESK_READ_METHOD = 'desk-read-16';
var DESK_GESTALT_REGISTRY = __DESK_GESTALT_REGISTRY__;
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
