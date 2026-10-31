// NEW predeclared feature policy. Never modifies the original FE01 scorer or claims canonical recovery.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex, utf8ToBytes} from '@noble/hashes/utils.js';
const hash = x => bytesToHex(sha256(utf8ToBytes(JSON.stringify(x))));
export const FE01_TREND_POLICY = Object.freeze({
  id:'FE01_DAILY_TREND_PRIOR252_V1',version:1,origin:'NEW_FEATURE_POLICY',engine_id:'FE01',
  provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',
  symbol_mapping:'Explicit asof=current acquisition New York date; current entity, not historical universe membership.',
  sessions:505,calendar_lookback_days:800,calendar:'Alpaca US equity official market calendar; America/New_York',completion_delay_ms:900000,
  returns:'R_h[u]=log(P[u])-log(P[u-h]) for h=21,63,252. Nested overlapping horizons, not independent or non-overlapping.',
  normalization:'Each current R_h[t] minus arithmetic mean of R_h[t-252]...R_h[t-1], divided by population standard deviation of those 252 prior values. Excludes current.',
  efficiency:'abs(log(P[t])-log(P[t-21])) / sum(abs(log(P[u])-log(P[u-1])),u=t-20...t).',
  volatility:'RV21[u]=sqrt(sum((log(P[j])-log(P[j-1]))^2,j=u-20...u)/21); non-demeaned daily close-to-close RMS, not intraday realized variance.',
  vol_regime:'Current RV21[t] standardized against arithmetic mean and population standard deviation of RV21[t-252]...RV21[t-1]. Excludes current.',
  units:'Fractional log price returns; z-scores and efficiency ratio. No percent conversion, annualization, sample-ddof correction, or added feature clipping.',
  degeneracy_threshold:1e-12,
  degeneracy:'Any normalization standard deviation or efficiency absolute-path denominator <=1e-12 abstains, never floors. Ratio roundoff excess <=1e-12 may clamp to1.',
  price_basis:'Split-adjusted, dividend-excluded provider prices; not total returns. Other corporate actions and historical revisions not independently checked.',
  zero_missing:'Require505 consecutive returned-calendar session bars, valid positive OHLCV, exact New York midnight stamps. No fill, skip or older-session substitution.',
  freshness_max_age_seconds:172800,
  forecast_interpretation:'Original fixed FE01 coefficients on NEW measurements; uncalibrated signed research score, not return magnitude, probability, edge or trade admission.',
});
export const FE01_TREND_POLICY_SHA256=hash(FE01_TREND_POLICY);
const ISO=/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?Z$/;
const instant=x=>typeof x==='string'&&ISO.test(x)&&!/\.\d{3}\d*[1-9]\d*Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(Date.parse(x)).toISOString().slice(0,10)===x.slice(0,10);
const date=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x+'T00:00:00Z'))&&new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
const nyFormat=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const nyTimeFormat=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const etDate=ms=>nyFormat.format(new Date(ms));
const isMidnight=ms=>nyTimeFormat.format(new Date(ms))==='00:00:00'&&ms%1000===0;
const fail=code=>{throw Error(code);};
const mean=x=>x.reduce((sum,v)=>sum+v,0)/x.length;
function standardize(current,prior,label){
  const m=mean(prior),sd=Math.sqrt(mean(prior.map(v=>(v-m)**2)));
  if(!Number.isFinite(current)||!Number.isFinite(m)||!Number.isFinite(sd)||sd<=FE01_TREND_POLICY.degeneracy_threshold)fail('degenerate_'+label+'_normalizer');
  const z=(current-m)/sd;if(!Number.isFinite(z))fail('nonfinite_feature');
  return {current,prior_mean:m,prior_population_sd:sd,prior_count:prior.length,z};
}
export function computeFE01TrendFeatures(closes){
  if(!Array.isArray(closes)||closes.length!==505||closes.some(p=>typeof p!=='number'||!Number.isFinite(p)||p<=0))fail('invalid_close_history');
  const logs=closes.map(Math.log),t=504,features={},normalization={};
  for(const h of [21,63,252]){
    const stat=standardize(logs[t]-logs[t-h],Array.from({length:252},(_,i)=>logs[t-252+i]-logs[t-252+i-h]),'ret_'+h+'d');
    features['ret_'+h+'d_z']=stat.z;normalization['ret_'+h+'d']=stat;
  }
  const returns=logs.map((p,i)=>i?p-logs[i-1]:0),path=returns.slice(t-20,t+1).reduce((sum,v)=>sum+Math.abs(v),0),net=Math.abs(logs[t]-logs[t-21]);
  if(!Number.isFinite(path)||path<=FE01_TREND_POLICY.degeneracy_threshold)fail('degenerate_efficiency_path');
  const efficiency=net/path;if(!Number.isFinite(efficiency)||efficiency>1+FE01_TREND_POLICY.degeneracy_threshold)fail('invalid_efficiency_ratio');
  features.trend_efficiency=Math.min(1,efficiency);
  const rv=u=>Math.sqrt(returns.slice(u-20,u+1).reduce((sum,r)=>sum+r*r,0)/21);
  normalization.vol_regime=standardize(rv(t),Array.from({length:252},(_,i)=>rv(t-252+i)),'vol_regime');
  features.vol_regime=normalization.vol_regime.z;
  return {features,measurements:{normalization,efficiency_net_abs_log_return:net,efficiency_path_abs_log_return:path,normalization_current_excluded:true,normalization_indices:{first:252,last:503,current:504},population_ddof:0}};
}
const base=()=>({schema:'SHIPYARD_FE01_SOURCE_FORECAST_V1',engine_id:'FE01',feature_origin:'provider_capture_new_policy',feature_policy:FE01_TREND_POLICY,feature_policy_sha256:FE01_TREND_POLICY_SHA256,
  restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,calibrated_probability:null,historical_point_in_time_claim:false}});
export function buildFE01SourceForecast(input){
  const out=base();
  try{
    if(!input||typeof input.symbol!=='string'||!/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(input.symbol)||input.feed!=='iex'||input.adjustment!=='split'||input.timeframe!=='1Day'||input.currency!=='USD')fail('source_identity_mismatch');
    if(!instant(input.evaluation_at))fail('invalid_evaluation_clock');
    const now=Date.parse(input.evaluation_at),cal=input.calendar,range=cal?.requested_range;
    if(input.symbol_asof!==etDate(now))fail('symbol_mapping_mismatch');
    if(!cal||cal.complete_provider_response!==true||!Array.isArray(cal.sessions)||cal.sessions.length>801||!instant(cal.received_at)||Date.parse(cal.received_at)>now||!date(range?.start_date)||!date(range?.end_date)||range.start_date>range.end_date||range.end_date!==etDate(now)||Date.parse(range.end_date)-Date.parse(range.start_date)>800*86400000)fail('invalid_calendar_lineage');
    const sessions=[];let previous=-Infinity,previousDate='';
    for(const s of cal.sessions){
      if(!date(s?.date)||s.date<=previousDate||s.date<range.start_date||s.date>range.end_date||!instant(s.open)||!instant(s.close))fail('invalid_calendar');
      const open=Date.parse(s.open),close=Date.parse(s.close),duration=close-open;
      if(open<=previous||duration<=0||duration>390*60000||duration%60000!==0||etDate(open)!==s.date||etDate(close-1)!==s.date)fail('invalid_calendar');
      previous=close;previousDate=s.date;
      if(close+FE01_TREND_POLICY.completion_delay_ms<=now)sessions.push({date:s.date,open:new Date(open).toISOString(),close:new Date(close).toISOString()});
    }
    if(sessions.length<505)fail('insufficient_completed_sessions');
    const selected=sessions.slice(-505),end=Date.parse(selected.at(-1).close),start=Date.parse(input.requested_window?.start);
    if(!instant(input.requested_window?.start)||!instant(input.requested_window?.end)||!isMidnight(start)||etDate(start)!==selected[0].date||Date.parse(input.requested_window.end)!==end||input.requested_window.end_exclusive!==true)fail('invalid_requested_window');
    if(input.pagination_complete!==true)fail('incomplete_provider_pagination');
    if(!Array.isArray(input.captures)||input.captures.length<1||input.captures.length>2||input.captures.some(c=>!c||typeof c.operation!=='string'||!instant(c.request_started_at)||!instant(c.http_response_received_at)||!instant(c.received_at)||Date.parse(c.request_started_at)<end+FE01_TREND_POLICY.completion_delay_ms||Date.parse(c.request_started_at)>Date.parse(c.http_response_received_at)||Date.parse(c.http_response_received_at)>Date.parse(c.received_at)||Date.parse(c.received_at)>now||!/^[0-9a-f]{64}$/.test(c.response_sha256||'')))fail('invalid_source_receipts');
    if(!Array.isArray(input.bars)||input.bars.length>1000)fail('history_bound_exceeded');
    const byDate=new Map(),selectedDates=new Set(selected.map(s=>s.date));previous=-Infinity;
    for(const b of input.bars){
      if(!b||!instant(b.t)||![b.o,b.h,b.l,b.c,b.v].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>0)||b.h<Math.max(b.o,b.c)||b.l>Math.min(b.o,b.c)||b.h<b.l)fail('invalid_bar');
      const at=Date.parse(b.t),day=etDate(at);
      if(at<=previous||byDate.has(day))fail('unordered_or_duplicate_bar');previous=at;
      if(at<start||at>=end)fail('bar_outside_requested_window');
      if(!isMidnight(at))fail('off_daily_grid_bar');
      if(!selectedDates.has(day))fail('non_session_bar');
      byDate.set(day,{t:new Date(at).toISOString(),o:b.o,h:b.h,l:b.l,c:b.c,v:b.v});
    }
    const used=selected.map(s=>{const b=byDate.get(s.date);if(!b)fail('missing_daily_session_bar');return b;});
    const {features,measurements}=computeFE01TrendFeatures(used.map(b=>b.c));
    const calculator=evaluateForecastEngine('FE01',features);if(calculator.status!=='research_only_score')fail('calculator_abstained');
    const age=(now-end)/1000,fresh=age<=FE01_TREND_POLICY.freshness_max_age_seconds;
    return {...out,status:'computed',symbol:input.symbol,evaluation_at:input.evaluation_at,features,calculator_result:calculator,
      calculator_provenance_note:'Unchanged evaluator retains manual-wrapper metadata; outer envelope establishes this new provider-capture feature path, not statistical validation or licensed-rights attestation.',
      source:{provider:FE01_TREND_POLICY.provider,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:input.symbol_asof,requested_window:input.requested_window,
        calendar:{received_at:cal.received_at,requested_range:range,selected_session_grid:{columns:['date','open','close'],rows:selected.map(s=>[s.date,s.open,s.close])},selected_calendar_sha256:hash(selected),complete_provider_response:true},captures:input.captures,pagination_complete:true,
        selected_bars_sha256:hash(used),source_policy_fingerprint:hash({policy_sha256:FE01_TREND_POLICY_SHA256,provider:FE01_TREND_POLICY.provider,feed:'iex',adjustment:'split',timeframe:'1Day'}),
        historical_availability:'unknown; current captures do not establish availability at historical decisions',price_basis:'split_adjusted_dividend_excluded',provider_revisions_possible:true,atomic_snapshot:false,calendar_omissions_independently_verified:false,corporate_actions_independently_verified:false,historical_symbol_continuity_independently_verified:false,rights_attestation:null,quality_score:null},
      measurements,coverage:{required_sessions:505,complete_sessions:505,used_daily_bars:used.length,received_bars:input.bars.length,missing_intervals_filled:false},
      freshness:{age_evaluated_at:input.evaluation_at,source_as_of:selected.at(-1).close,source_age_seconds:age,max_age_seconds:FE01_TREND_POLICY.freshness_max_age_seconds,status:fresh?'within_declared_age':'stale',current_source_age_acceptable:fresh},
      warnings:['NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER','FIXED_COEFFICIENTS_NOT_FITTED','IEX_SINGLE_EXCHANGE_NOT_CONSOLIDATED','DIVIDEND_EXCLUDED_NOT_TOTAL_RETURN','NESTED_OVERLAPPING_HORIZONS_AND_NORMALIZATION','DAILY_CLOSE_RMS_NOT_INTRADAY_REALIZED_VOLATILITY','PROVIDER_REVISIONS_POSSIBLE','NO_HISTORICAL_POINT_IN_TIME_ASSERTION','NO_CALIBRATION_OR_PROFITABILITY_CLAIM',...(!fresh?['STALE_SOURCE_RESEARCH_DIAGNOSTIC_ONLY']:[])]};
  }catch(error){return {...out,status:'unavailable',error:error?.message||'feature_construction_failed'};}
}
