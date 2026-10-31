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
