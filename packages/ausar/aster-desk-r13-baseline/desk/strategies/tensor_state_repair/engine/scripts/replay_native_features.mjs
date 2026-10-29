import fs from 'node:fs';
import path from 'node:path';
import {gunzipSync,gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {runTensorInternals} from '../engine/run_tensor_internals.mjs';
import {macdSeries,stochasticRsi,wilderAtr,onBalanceVolume,slope} from '../engine/instrumented-v690/lib/anna-internals.mjs';
import {buildTensorSwingSignal} from '../engine/frozen-v690/lib/tensor-swing-signals.mjs';
import {buildSwingTransition} from '../engine/frozen-v690/lib/tensor-swing-transition.mjs';

export const HEADER = ['symbol','interval','bar_index','timestamp','completed_at','usable_at','source_origin_timestamp','native_status',
 'open','high','low','close','volume','buy_green','buy_cyan','sell_red','sell_magenta','primary_markers','marker_event_ids',
 'swing_setup','swing_confirmed','swing_first_confirmation','swing_setup_timestamp','swing_confirmation_age','swing_setup_id','swing_confirmation_id','swing_phenotype','swing_score',
 'swing_transition_qualifies','swing_floor_distance_atr','swing_floor_taps','swing_floor_age','swing_reclaim_age','swing_runway_atr',
 'ema200','ema21','ribbon_ema10','ribbon_ema20','ribbon_ema30','ribbon_ema40','ribbon_ema50','ribbon_ema60','ribbon_ema70','ribbon_ema80',
 'ribbon_inversion_count','ribbon_width','ribbon_slope','obv_slope5','obv_slope10','rvol','vote_stoch','vote_aroon','vote_di','vote_obv','vote_squeeze','vote_pivot','vote_wave',
 'bullish_votes','bearish_votes','total_votes','squeeze_on','squeeze_momentum','squeeze_length','ut_regime','ut_event','mcdx_position','mcdx_position_delta3','rsi14','macd_line','macd_signal','macd_histogram','atr14',
 'efficiency10','sign_entropy20','normalized_sign_entropy20','overhead60_atr','high20','ema21_reclaim','return20','return60','dollar_volume20',
 'prior_sell_avwap','prior_sell_timestamp','prior_sell_completed_at','prior_sell_low','prior_sell_close','prior_sell_atr','up_volume_share13','prior_up_volume_share13','weekly_resistance_5x5','weekly_resistance_known_at','overhead_volume_burden52','raw_overhead_volume_burden52'];

const finite=Number.isFinite;
const yes=x=>x?1:0;
const sha=b=>createHash('sha256').update(b).digest('hex');
const expected=(bars,fn,start,end)=>bars.slice(start,end).reduce((sum,b,i)=>sum+fn(b,start+i),0);
const nullArray=n=>Array(n).fill(null);
const safeNumber=x=>typeof x==='number'&&finite(x)?x:null;

export function extractNativeFeatures(history) {
  if(!history || !Array.isArray(history.bars)||!history.bars.length)throw new Error('nonempty history required');
  if(history.latestBarOpen!==false)throw new Error('prepared completed history required');
  if(!['1h','1d','1wk'].includes(history.interval))throw new Error('replay frame must be1h/1d/1wk');
  const source=history.bars,asOf=Math.max(...source.map(b=>b.usableAt));
  // Validate the clock and OHLCV contract also for symbol histories shorter
  // than the native minimum. Such source rows are retained as warming.
  let prior=0;
  for(const b of source){
    if(!Number.isSafeInteger(b.timestamp)||b.timestamp<=prior)throw new Error('input timestamps not strictly increasing');prior=b.timestamp;
    if(!Number.isSafeInteger(b.completedAt)||b.completedAt<=b.timestamp||!Number.isSafeInteger(b.usableAt)||b.usableAt<b.completedAt||b.usableAt>asOf)throw new Error('invalid completed/usable clock');
    if(!['open','high','low','close','volume'].every(k=>typeof b[k]==='number'&&finite(b[k]))||Math.min(b.open,b.high,b.low,b.close)<=0||b.volume<0||b.high<Math.max(b.open,b.close)||b.low>Math.min(b.open,b.close))throw new Error('invalid numeric OHLCV');
  }
  const request={...history,asOf};
  const minimum=history.interval==='1wk'?4:35;
  let native,internal;
  if(source.length>=minimum){const result=runTensorInternals(request);native=result.bars;internal=result.internalArrays;}
  else {
    const close=source.map(b=>b.close),high=source.map(b=>b.high),low=source.map(b=>b.low),volume=source.map(b=>b.volume);
    const macd=macdSeries(close,12,26,9),stoch=stochasticRsi(close,14,14,3,3),obv=onBalanceVolume(close,volume);
    native=source.map(b=>({...b,barFinality:'closed',primaryMarkers:[],stateVotes:[],bullishVotes:0,bearishVotes:0,totalVotes:0}));
    internal={macdLine:macd.macd,macdSignal:macd.signal,macdHistogram:macd.histogram,stochRsiUnderlyingRsi14:stoch.rsi,wilderAtr14:wilderAtr(high,low,close,14),obvSlope5:obv.map((_,i)=>slope(obv,i,5)),obvSlope10:obv.map((_,i)=>slope(obv,i,10))};
  }
  if(native.length!==source.length)throw new Error('native/source denominator mismatch');
  const structural=native.map((b,i)=>({timestamp:b.timestamp,barFinality:b.barFinality,low:b.low,high:b.high,close:b.close,ribbonSlope:b.ribbonSlope,ema8:b.ema8,ema21:b.ema21,candleRegime:b.candleRegime,ribbonOrder:b.ribbonOrder,emaRibbon:b.emaRibbon,rvol:b.rvol,squeezeOn:b.squeezeOn,primaryMarkers:b.primaryMarkers,fastState:b.fastState,slowState:b.slowState,vectorStructuralLocation:{atr:internal.wilderAtr14[i]}}));
  const seenSwing=new Set(),pivots=[];
  let sell=null,sellNumerator=0,sellVolume=0;
  const rows=[];
  for(let i=0;i<native.length;i++){
    const b=native[i],s=source[i],atr=safeNumber(internal.wilderAtr14[i]),markers=b.primaryMarkers||[],votes=Object.fromEntries((b.stateVotes||[]).map(v=>[v.id,v.direction==='bullish'?1:v.direction==='bearish'?-1:null]));
    const directions=['stoch','aroon','di','obv','squeeze','pivot','wave'].map(id=>votes[id]??null);
    if(directions.filter(v=>v===1).length!==b.bullishVotes||directions.filter(v=>v===-1).length!==b.bearishVotes||directions.filter(v=>v!==null).length!==b.totalVotes)throw new Error('native published direction/count reconciliation failed '+i);
    const swing=history.interval==='1h'?buildTensorSwingSignal({bars:native,index:i,symbol:history.symbol,registry:{}}):null;
    const first=Boolean(swing?.confirmed&&!seenSwing.has(swing.setupBarTimestamp));
    if(swing?.confirmed)seenSwing.add(swing.setupBarTimestamp);
    const transition=history.interval==='1h'?buildSwingTransition({bars:structural,index:i,symbol:history.symbol,confirmed:Boolean(swing?.confirmed)}):null;
    const ribbon=b.emaRibbon||[];let inversions=null;
    if(ribbon.length===8&&ribbon.every(finite)){inversions=0;for(let a=0;a<8;a++)for(let c=a+1;c<8;c++)if(ribbon[a]<ribbon[c])inversions++;}
    const typical=(s.high+s.low+s.close)/3;
    if(sell){sellNumerator+=typical*s.volume;sellVolume+=s.volume;}
    if(history.interval==='1wk'&&i>=10){
      const candidate=i-5,level=source[candidate].high;
      let pivot=true;for(let j=candidate-5;j<=candidate+5;j++)if(j!==candidate&&source[j].high>=level){pivot=false;break;}
      if(pivot)pivots.push({level,knownAt:s.completedAt});
    }
    let resistance=null;for(const p of pivots)if(p.level>s.close&&(!resistance||p.level<resistance.level))resistance=p;
    let efficiency=null;if(i>=10){let denominator=0;for(let j=i-9;j<=i;j++)denominator+=Math.abs(source[j].close-source[j-1].close);efficiency=denominator?Math.abs(s.close-source[i-10].close)/denominator:null;}
    let entropy=null;if(i>=20){const counts=[0,0,0];for(let j=i-19;j<=i;j++)counts[Math.sign(source[j].close-source[j-1].close)+1]++;entropy=0;for(const count of counts)if(count)entropy-=(count/20)*Math.log2(count/20);}
    const high20=i>=20?Math.max(...source.slice(i-20,i).map(x=>x.high)):null;
    const high60=i>=60?Math.max(...source.slice(i-60,i).map(x=>x.high)):null;
    const dollarVol=i>=19?expected(source,x=>x.close*x.volume,i-19,i+1)/20:null;
    let upShare=null;if(i>=13){const total=expected(source,x=>x.volume,i-12,i+1);const up=expected(source,(x,j)=>x.close>source[j-1].close?x.volume:0,i-12,i+1);upShare=total>0?up/total:null;}
    let priorUpShare=null;if(i>=14){const total=expected(source,x=>x.volume,i-13,i);const up=expected(source,(x,j)=>x.close>source[j-1].close?x.volume:0,i-13,i);priorUpShare=total>0?up/total:null;}
    let burden=null,rawBurden=null;if(i>=52){
      const prior52=source.slice(i-52,i),total=prior52.reduce((sum,x)=>sum+x.volume,0);
      const overhead=prior52.reduce((sum,x)=>sum+((x.high+x.low+x.close)/3>s.close?x.volume:0),0);rawBurden=total>0?overhead/total:null;
      const floor=Math.min(...prior52.map(x=>x.low)),ceiling=Math.max(...prior52.map(x=>x.high));
      if(total>0&&ceiling>floor){const bins=Array(12).fill(0),step=(ceiling-floor)/12;
        for(const x of prior52){const price=(x.high+x.low+x.close)/3,index=Math.max(0,Math.min(11,Math.floor((price-floor)/step)));bins[index]+=x.volume;}
        burden=bins.reduce((sum,v,k)=>sum+(floor+(k+.5)*step>s.close?v:0),0)/total;
      }
    }
    const out={symbol:history.symbol,interval:history.interval,bar_index:i,timestamp:s.timestamp,completed_at:s.completedAt,usable_at:s.usableAt,source_origin_timestamp:source[0].timestamp,native_status:i+1>=minimum?'ready':'warming',open:s.open,high:s.high,low:s.low,close:s.close,volume:s.volume,
      buy_green:yes(markers.includes('buy-green')),buy_cyan:yes(markers.includes('buy-cyan')),sell_red:yes(markers.includes('sell-red')),sell_magenta:yes(markers.includes('sell-magenta')),primary_markers:markers.join('|'),marker_event_ids:markers.map(m=>`${history.symbol}:${history.interval}:${s.timestamp}:${m}`).join('|'),
      swing_setup:yes(swing?.setup),swing_confirmed:yes(swing?.confirmed),swing_first_confirmation:yes(first),swing_setup_timestamp:swing?.setupBarTimestamp??null,swing_confirmation_age:swing?.confirmationAgeBars??null,swing_setup_id:swing?.setupBarTimestamp!=null?`${history.symbol}:1h:${swing.setupBarTimestamp}:swing-setup`:'',swing_confirmation_id:swing?.confirmed?`${history.symbol}:1h:${swing.setupBarTimestamp}:swing-confirmation`:'',swing_phenotype:swing?.phenotype??'',swing_score:swing?.score??null,
      swing_transition_qualifies:yes(transition?.qualifies),swing_floor_distance_atr:transition?.context?.floorDistanceAtr??null,swing_floor_taps:transition?.context?.floorTapCount??null,swing_floor_age:transition?.context?.floorAgeBars??null,swing_reclaim_age:transition?.context?.reclaimAgeBars??null,swing_runway_atr:transition?.context?.runwayAtr??null,
      ema200:b.ema200??null,ema21:b.ema21??null,ribbon_inversion_count:inversions,ribbon_width:b.ribbonWidth??null,ribbon_slope:b.ribbonSlope??null,obv_slope5:safeNumber(internal.obvSlope5[i]),obv_slope10:safeNumber(internal.obvSlope10[i]),rvol:b.rvol??null,
      bullish_votes:b.bullishVotes,bearish_votes:b.bearishVotes,total_votes:b.totalVotes,squeeze_on:b.squeezeOn==null?null:yes(b.squeezeOn),squeeze_momentum:b.squeezeMomentum??null,squeeze_length:b.squeezeLength??null,ut_regime:b.utRegime??'',ut_event:b.utEvent??'',mcdx_position:b.mcdxProfit??null,mcdx_position_delta3:i>=3&&finite(b.mcdxProfit)&&finite(native[i-3].mcdxProfit)?b.mcdxProfit-native[i-3].mcdxProfit:null,
      rsi14:safeNumber(internal.stochRsiUnderlyingRsi14[i]),macd_line:safeNumber(internal.macdLine[i]),macd_signal:safeNumber(internal.macdSignal[i]),macd_histogram:safeNumber(internal.macdHistogram[i]),atr14:atr,
      efficiency10:efficiency,sign_entropy20:entropy,normalized_sign_entropy20:entropy===null?null:entropy/Math.log2(3),overhead60_atr:finite(high60)&&atr>0?(high60-s.close)/atr:null,high20,ema21_reclaim:yes(i>0&&finite(b.ema21)&&finite(native[i-1].ema21)&&native[i-1].close<=native[i-1].ema21&&b.close>b.ema21),return20:i>=20?s.close/source[i-20].close-1:null,return60:i>=60?s.close/source[i-60].close-1:null,dollar_volume20:dollarVol,
      prior_sell_avwap:sell&&sellVolume>0?sellNumerator/sellVolume:null,prior_sell_timestamp:sell?.timestamp??null,prior_sell_completed_at:sell?.completedAt??null,prior_sell_low:sell?.low??null,prior_sell_close:sell?.close??null,prior_sell_atr:sell?.atr??null,up_volume_share13:upShare,prior_up_volume_share13:priorUpShare,weekly_resistance_5x5:resistance?.level??null,weekly_resistance_known_at:resistance?.knownAt??null,overhead_volume_burden52:burden,raw_overhead_volume_burden52:rawBurden};
    for(const id of ['stoch','aroon','di','obv','squeeze','pivot','wave'])out['vote_'+id]=votes[id]??null;
    [10,20,30,40,50,60,70,80].forEach((p,k)=>out['ribbon_ema'+p]=safeNumber(ribbon[k]));
    for(const key of HEADER){const value=out[key];if(value===undefined||typeof value==='number'&&!finite(value))throw new Error(`invalid output ${key} ${i}`);}
    if(out.swing_first_confirmation&&!out.swing_confirmed)throw new Error('dedup confirmation without native confirmation');
    if(out.weekly_resistance_known_at!=null&&out.weekly_resistance_known_at>s.completedAt)throw new Error('future weekly pivot');
    rows.push(out);
    // Reset after emission so the anchor is strictly a prior sell, never the
    // current sell glyph. Its causal AVWAP includes current completed volume.
    if(markers.some(m=>m.startsWith('sell-'))){sell={timestamp:s.timestamp,completedAt:s.completedAt,low:s.low,close:s.close,atr};sellNumerator=typical*s.volume;sellVolume=s.volume;}
  }
  return rows;
}

const csv=value=>value===null?'':String(value).includes(',')||String(value).includes('"')||String(value).includes('\n')?'"'+String(value).replaceAll('"','""')+'"':String(value);
export function encodeRows(rows){return HEADER.join(',')+'\n'+rows.map(r=>HEADER.map(k=>csv(r[k])).join(',')).join('\n')+'\n';}

export async function replayFrame({inputRoot='/tmp/r11-tensor-inputs/native-inputs',outputRoot='/tmp/r11-tensor-inputs/native-features',frame,limit=Infinity,receiptRoot=new URL('../experiments/',import.meta.url),symbols=null}){
  const inputDir=path.join(inputRoot,'bars',frame),outDir=path.join(outputRoot,frame);fs.mkdirSync(outDir,{recursive:true});
  const names=fs.readdirSync(inputDir).filter(n=>n.endsWith('.json.gz')&&(!symbols||symbols.includes(n.slice(0,-8)))).sort().slice(0,limit);
  const started=new Date(),groups=[],errors=[];let rows=0;
  const producerSha256=sha(fs.readFileSync(fileURLToPath(import.meta.url)));
  const receiptPath=new URL(`NATIVE_REPLAY_${frame.replace('1','')}_${symbols?'PILOT':'RECEIPT'}.json`,receiptRoot);
  const writeReceipt=status=>fs.writeFileSync(receiptPath,JSON.stringify({schema:'tensor-r11-native-feature-replay/2',status,startedAt:started.toISOString(),updatedAt:new Date().toISOString(),producerSha256,header:HEADER,frame,inputRoot,outputRoot,groups,errors,totalRows:rows,financialOutcomesRead:false,financialExperiments:0,availability:'calendar completion idealized receipt; actual receipt unknown',historicalStockMaster:'NOT_ESTABLISHED',voteConservation:'Per-row +1/-1/null columns reconcile exact native bullish/bearish/total counts; checked before writing.',sourceFingerprint:'NATIVE_REPLAY_INPUT_BINDING.json',failureHistory:'native_replay_v1_failure/FAILURE_RECEIPT.json'},null,2)+'\n');
  writeReceipt('RUNNING');
  for(const name of names){
    const startedAt=performance.now(),inputPath=path.join(inputDir,name);
    try{
      const compressed=fs.readFileSync(inputPath),history=JSON.parse(gunzipSync(compressed));
      if(history.interval!==frame||name!==history.symbol+'.json.gz')throw new Error('path/source identity mismatch');
      const features=extractNativeFeatures(history),encoded=encodeRows(features),packed=gzipSync(encoded,{level:4}),outputPath=path.join(outDir,history.symbol+'.csv.gz');
      const temp=outputPath+'.tmp';fs.writeFileSync(temp,packed);fs.renameSync(temp,outputPath);
      rows+=features.length;groups.push({symbol:history.symbol,inputPath,inputSha256:sha(compressed),inputRows:history.bars.length,outputPath,outputSha256:sha(packed),outputRows:features.length,uncompressedCsvSha256:sha(encoded),bytes:packed.length,elapsedMs:Math.round(performance.now()-startedAt)});
    }catch(e){errors.push({inputPath,error:String(e.stack||e)});}
    if((groups.length+errors.length)%25===0){writeReceipt('RUNNING');console.log(JSON.stringify({frame,groups:groups.length,errors:errors.length,rows,seconds:Math.round((Date.now()-started)/1000)}));}
  }
  writeReceipt(errors.length?'PARTIAL_FAILED':'COMPLETE');
  console.log(JSON.stringify({frame,status:errors.length?'PARTIAL_FAILED':'COMPLETE',groups:groups.length,errors:errors.length,rows,seconds:Math.round((Date.now()-started)/1000),receiptPath:fileURLToPath(receiptPath)}));
  return {groups,errors,rows};
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
  const args=process.argv.slice(2),frame=args[0];if(!['1h','1d','1wk'].includes(frame))throw new Error('usage: node replay_native_features.mjs 1h|1d|1wk [comma-separated pilot symbols]');
  const r=await replayFrame({frame,symbols:args[1]?args[1].split(','):null});process.exitCode=r.errors.length?1:0;
}
