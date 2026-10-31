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
