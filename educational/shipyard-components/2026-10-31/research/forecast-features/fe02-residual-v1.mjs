// Explicitly NEW FE02 feature policy. The canonical input builder was not recovered.
// The imported scorer and coefficients remain untouched; this is not an equivalent port.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex,utf8ToBytes} from '@noble/hashes/utils.js';

const hash=value=>bytesToHex(sha256(utf8ToBytes(JSON.stringify(value))));
const fail=code=>{throw Error(code);};
const mean=values=>values.reduce((sum,value)=>sum+value,0)/values.length;
const populationSd=values=>{const m=mean(values);return Math.sqrt(mean(values.map(value=>(value-m)**2)));};
const sum=values=>values.reduce((total,value)=>total+value,0);
const EPS=1e-12;
const DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const TIME_FORMAT=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});

export const FE02_PAIRED_POLICY=Object.freeze({
  id:'FE02_PAIRED_BENCHMARK_RESIDUAL_V1',version:1,origin:'NEW_FEATURE_POLICY',engine_id:'FE02',
  provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',benchmark:'SPY',
  sessions:505,calendar_lookback_days:800,completion_delay_ms:900000,freshness_max_age_seconds:172800,
  acquisition_budget_seconds:25,per_request_timeout_seconds:8,max_pages_per_series:2,max_rows_per_series:1000,max_response_bytes_per_request:524288,
  regression:'OLS with intercept on the 252 paired daily log returns immediately before the latest completed return; current return excluded. Population covariance/variance sums; beta=cross_sum/benchmark_sum_squares; alpha=mean(symbol_return)-beta*mean(SPY_return).',
  residual:'For this evaluation, e_i=log(symbol_close_i/symbol_close_i-1)-alpha-beta*log(SPY_close_i/SPY_close_i-1), using the one prior-only fitted alpha/beta for all supplied residual history. Inputs are only through the latest completed close. Reconstructed past residuals are not historical point-in-time observations.',
  residual_z:'Sum of latest 5 residual log returns divided by prior-252 residual daily population SD times sqrt(5). Prior sigma uses the 252 returns used to fit beta; current return excluded from sigma.',
  trend_z:'Sum of latest 63 residual log returns divided by the same prior-252 residual daily population SD times sqrt(63).',
  vol_regime:'Population z-score of latest 21-residual-return RMS versus 252 preceding rolling 21-return RMS values. Current RMS excluded from baseline; RMS=sqrt(sum(e_i^2)/21).',
  hurst:'R/S slope from OLS of log(block size) against log(mean block R/S), sizes 8,16,32,64, using non-overlapping blocks anchored at the first of the latest 252 residual log returns. Within each block subtract its arithmetic mean, cumulatively sum centered values, R is max(cumulative)-min(cumulative), S is sample standard deviation (ddof=1), and average R/S across complete blocks. Require the resulting exponent to be in [0,1]; never clip.',
  windows:'All lookbacks are in official completed US-equity sessions. Returns use close-to-close natural-log price changes. The current residual return is available only after the completed-session delay.',
  units:'residual_z and trend_z are dimensionless z-scaled log-return sums; hurst is a dimensionless R/S exponent; vol_regime is a dimensionless z-score. No percent conversion, annualization, dividend adjustment, imputation, or feature clipping.',
  degeneracy:'Reject non-finite intermediates and any OLS denominator, residual population SD, R/S block SD, R/S average or volatility normalizer <=1e-12. No variance floor.',
  price_basis:'Split-adjusted, dividend-excluded provider prices. IEX is one exchange, not consolidated SIP; provider revisions and historical availability remain unverified.',
  zero_missing:'Require 505 exact paired official-session bars per symbol on the same dates. No forward fill, skipped bars, substituted ticker, or alternate benchmark.',
  forecast_interpretation:'Unchanged fixed FE02 scorer applied to NEW measurements; research-only uncalibrated signed score, not a residual-return magnitude, probability, edge or trade admission.',
});
export const FE02_PAIRED_POLICY_SHA256=hash(FE02_PAIRED_POLICY);

const ISO=/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?Z$/;
const instant=value=>typeof value==='string'&&ISO.test(value)&&! /\.\d{3}\d*[1-9]\d*Z$/.test(value)&&Number.isFinite(Date.parse(value))&&new Date(value).toISOString().slice(0,10)===value.slice(0,10);
const validDate=value=>typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&Number.isFinite(Date.parse(value+'T00:00:00Z'))&&new Date(value+'T00:00:00Z').toISOString().slice(0,10)===value;
const nyDate=ms=>DATE_FORMAT.format(new Date(ms));
const isNyMidnight=ms=>TIME_FORMAT.format(new Date(ms))==='00:00:00'&&ms%1000===0;
const safeSeriesKey=symbol=>symbol.replace(/[^A-Z0-9.-]/g,'_');
function validCapture(receipt,operation,subject,now){
  if(!receipt||receipt.operation!==operation||receipt.subject!==subject||receipt.http_status!==200
    ||!instant(receipt.request_started_at)||!instant(receipt.http_response_received_at)||!instant(receipt.received_at)
    ||Date.parse(receipt.request_started_at)>Date.parse(receipt.http_response_received_at)
    ||Date.parse(receipt.http_response_received_at)>Date.parse(receipt.received_at)||Date.parse(receipt.received_at)>now
    ||now-Date.parse(receipt.received_at)>FE02_PAIRED_POLICY.acquisition_budget_seconds*1000
    ||!/^[0-9a-f]{64}$/.test(receipt.response_sha256||'')||receipt.hash_serialization!=='UTF-8 re-encoding of decoded response text')return false;
  return true;
}
function validHistoryReceipt(receipt,symbol,page,input){
  const operation=`history_${symbol}_1Day_page_${page}`;
  if(!validCapture(receipt,operation,symbol,Date.parse(input.evaluation_at))||!Number.isInteger(receipt.provider_rows)
    ||receipt.provider_rows<0||receipt.provider_rows>1000||typeof receipt.has_next_page!=='boolean')return false;
  let url;try{url=new URL(receipt.request_url);}catch{return false;}
  const window=input.requested_window,expectedEnd=new Date(Date.parse(window.end)-1).toISOString();
  return url.origin==='https://data.alpaca.markets'&&url.pathname===`/v2/stocks/${encodeURIComponent(symbol)}/bars`
    &&[...url.searchParams.keys()].sort().join(',')===(page===1?'adjustment,asof,currency,end,feed,limit,sort,start,timeframe':'adjustment,asof,currency,end,feed,limit,page_token,sort,start,timeframe')
    &&url.searchParams.get('timeframe')==='1Day'&&url.searchParams.get('start')===window.start&&url.searchParams.get('end')===expectedEnd
    &&url.searchParams.get('feed')==='iex'&&url.searchParams.get('adjustment')==='split'&&url.searchParams.get('currency')==='USD'
    &&url.searchParams.get('asof')===input.symbol_asof&&url.searchParams.get('sort')==='asc'&&url.searchParams.get('limit')==='1000'
    &&(page===1?!url.searchParams.has('page_token'):url.searchParams.get('page_token')==='[continuation]')
    &&(page===1||!receipt.has_next_page);
}

function regress(priorSymbol,priorBenchmark){
  if(priorSymbol.length!==252||priorBenchmark.length!==252)fail('invalid_regression_window');
  const mx=mean(priorBenchmark),my=mean(priorSymbol),xx=sum(priorBenchmark.map(value=>(value-mx)**2));
  if(!Number.isFinite(xx)||xx<=EPS)fail('degenerate_benchmark_regression');
  const beta=sum(priorBenchmark.map((value,index)=>(value-mx)*(priorSymbol[index]-my)))/xx;
  const alpha=my-beta*mx;
  if(!Number.isFinite(alpha)||!Number.isFinite(beta))fail('nonfinite_regression');
  return {alpha,beta,observations:252,prior_window_excludes_current:true,benchmark_sum_squares:xx};
}

function rescaledRangeExponent(values){
  if(values.length!==252)fail('invalid_hurst_window');
  const sizes=[8,16,32,64],points=[];
  for(const size of sizes){
    const ratios=[];
    for(let start=0;start+size<=values.length;start+=size){
      const block=values.slice(start,start+size),m=mean(block),centered=block.map(value=>value-m),sd=Math.sqrt(sum(centered.map(value=>value*value))/(size-1));
      if(!Number.isFinite(sd)||sd<=EPS)fail('degenerate_hurst_block');
      let cumulative=0,low=Infinity,high=-Infinity;
      for(const value of centered){cumulative+=value;low=Math.min(low,cumulative);high=Math.max(high,cumulative);}
      const ratio=(high-low)/sd;if(!Number.isFinite(ratio)||ratio<=EPS)fail('degenerate_hurst_range');
      ratios.push(ratio);
    }
    const average=mean(ratios);if(!Number.isFinite(average)||average<=EPS)fail('degenerate_hurst_average');
    points.push({block_size:size,block_count:ratios.length,mean_rescaled_range:average});
  }
  const x=points.map(point=>Math.log(point.block_size)),y=points.map(point=>Math.log(point.mean_rescaled_range)),mx=mean(x),my=mean(y);
  const exponent=sum(x.map((value,index)=>(value-mx)*(y[index]-my)))/sum(x.map(value=>(value-mx)**2));
  if(!Number.isFinite(exponent)||exponent<0||exponent>1)fail('hurst_out_of_range');
  return {value:exponent,estimator:'nonoverlapping_demeaned_R_over_sample_S_OLS_loglog',points};
}

export function computeFE02PairedFeatures(symbolCloses,benchmarkCloses){
  if(!Array.isArray(symbolCloses)||!Array.isArray(benchmarkCloses)||symbolCloses.length!==505||benchmarkCloses.length!==505
    ||[...symbolCloses,...benchmarkCloses].some(value=>typeof value!=='number'||!Number.isFinite(value)||value<=0))fail('invalid_paired_close_history');
  const symbolReturns=symbolCloses.slice(1).map((close,index)=>Math.log(close/symbolCloses[index]));
  const benchmarkReturns=benchmarkCloses.slice(1).map((close,index)=>Math.log(close/benchmarkCloses[index]));
  if([...symbolReturns,...benchmarkReturns].some(value=>!Number.isFinite(value)))fail('nonfinite_log_return');
  const t=symbolReturns.length-1,regression=regress(symbolReturns.slice(t-252,t),benchmarkReturns.slice(t-252,t));
  const residuals=symbolReturns.map((value,index)=>value-regression.alpha-regression.beta*benchmarkReturns[index]);
  const priorResiduals=residuals.slice(t-252,t),priorResidualSd=populationSd(priorResiduals);
  if(!Number.isFinite(priorResidualSd)||priorResidualSd<=EPS)fail('degenerate_residual_volatility');
  const residual5=sum(residuals.slice(t-4,t+1)),residual63=sum(residuals.slice(t-62,t+1));
  const residualZ=residual5/(priorResidualSd*Math.sqrt(5)),trendZ=residual63/(priorResidualSd*Math.sqrt(63));
  const hurst=rescaledRangeExponent(residuals.slice(t-251,t+1));
  const rollingRms=end=>Math.sqrt(sum(residuals.slice(end-20,end+1).map(value=>value*value))/21);
  const priorVol=Array.from({length:252},(_,index)=>rollingRms(t-252+index)),currentVol=rollingRms(t);
  const priorVolMean=mean(priorVol),priorVolSd=populationSd(priorVol);
  if(!Number.isFinite(priorVolSd)||priorVolSd<=EPS)fail('degenerate_volatility_regime');
  const volRegime=(currentVol-priorVolMean)/priorVolSd;
  const features={residual_z:residualZ,hurst:hurst.value,trend_z:trendZ,vol_regime:volRegime};
  if(Object.values(features).some(value=>!Number.isFinite(value)))fail('nonfinite_feature');
  return {features,regression,measurements:{residual_daily_prior_population_sd:priorResidualSd,residual_5_session_sum:residual5,
    residual_63_session_sum:residual63,prior_residual_count:252,normalization_current_excluded:true,population_ddof:0,
    hurst_window:252,hurst_estimator:hurst,volatility_window:21,volatility_baseline_count:252,volatility_baseline_mean:priorVolMean,
    volatility_baseline_population_sd:priorVolSd,current_residual_rms_21:currentVol,volatility_normalization_current_excluded:true,
    regression_current_return_excluded:true,regression_prior_window:{first_return_index:t-252,last_return_index:t-1}}};
}

function emptyResult(){return {schema:'SHIPYARD_FE02_SOURCE_FORECAST_V1',engine_id:'FE02',feature_origin:'provider_capture_new_policy',
  feature_policy:FE02_PAIRED_POLICY,feature_policy_sha256:FE02_PAIRED_POLICY_SHA256,
  restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,
    calibrated_probability:null,historical_point_in_time_claim:false}};}

export function buildFE02SourceForecast(input){
  const out=emptyResult();
  try{
    if(!input||typeof input.symbol!=='string'||!/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(input.symbol)||input.symbol==='SPY'
      ||input.benchmark_symbol!=='SPY'||input.feed!=='iex'||input.adjustment!=='split'||input.timeframe!=='1Day'||input.currency!=='USD')fail('source_identity_mismatch');
    if(!instant(input.evaluation_at))fail('invalid_evaluation_clock');
    const now=Date.parse(input.evaluation_at),cal=input.calendar,range=cal?.requested_range;
    if(input.symbol_asof!==nyDate(now))fail('symbol_mapping_mismatch');
    if(!cal||cal.complete_provider_response!==true||!Array.isArray(cal.sessions)||cal.sessions.length>801||!instant(cal.received_at)||Date.parse(cal.received_at)>now
      ||!validDate(range?.start_date)||!validDate(range?.end_date)||range.start_date>range.end_date||range.end_date!==nyDate(now)
      ||Date.parse(range.end_date)-Date.parse(range.start_date)>800*86400000)fail('invalid_calendar_lineage');
    const calendarCapture=input.calendar_capture;
    if(!validCapture(calendarCapture,'official_calendar','US_EQUITY',now)||calendarCapture.received_at!==cal.received_at)fail('invalid_calendar_receipt');
    let calendarUrl;try{calendarUrl=new URL(calendarCapture.request_url);}catch{fail('invalid_calendar_receipt');}
    if(calendarUrl.origin!=='https://paper-api.alpaca.markets'||calendarUrl.pathname!=='/v2/calendar'
      ||[...calendarUrl.searchParams.keys()].sort().join(',')!=='end,start'
      ||calendarUrl.searchParams.get('start')!==range.start_date||calendarUrl.searchParams.get('end')!==range.end_date)fail('invalid_calendar_receipt');
    const sessions=[];let previousClose=-Infinity,previousDate='';
    for(const session of cal.sessions){
      if(!validDate(session?.date)||session.date<=previousDate||session.date<range.start_date||session.date>range.end_date
        ||!instant(session.open)||!instant(session.close))fail('invalid_calendar');
      const open=Date.parse(session.open),close=Date.parse(session.close),duration=close-open;
      if(open<=previousClose||duration<=0||duration>390*60000||duration%60000!==0||nyDate(open)!==session.date||nyDate(close-1)!==session.date)fail('invalid_calendar');
      previousClose=close;previousDate=session.date;
      if(close+FE02_PAIRED_POLICY.completion_delay_ms<=now)sessions.push({date:session.date,open:new Date(open).toISOString(),close:new Date(close).toISOString()});
    }
    if(sessions.length<505)fail('insufficient_completed_sessions');
    const selected=sessions.slice(-505),end=Date.parse(selected.at(-1).close),start=Date.parse(input.requested_window?.start);
    if(!instant(input.requested_window?.start)||!instant(input.requested_window?.end)||!isNyMidnight(start)||nyDate(start)!==selected[0].date
      ||Date.parse(input.requested_window.end)!==end||input.requested_window.end_exclusive!==true)fail('invalid_requested_window');
    if(input.pagination_complete!==true)fail('incomplete_provider_pagination');
    const receipts=input.captures,operations=new Set();
    const allowedOperations=new Set([`history_${input.symbol}_1Day_page_1`,`history_${input.symbol}_1Day_page_2`,'history_SPY_1Day_page_1','history_SPY_1Day_page_2']);
    if(!Array.isArray(receipts)||receipts.length<2||receipts.length>4||receipts.some(receipt=>{
      if(!receipt||typeof receipt.operation!=='string'||!allowedOperations.has(receipt.operation)||operations.has(receipt.operation))return true;operations.add(receipt.operation);
      return !Number.isFinite(Date.parse(receipt.request_started_at))||Date.parse(receipt.request_started_at)<end+FE02_PAIRED_POLICY.completion_delay_ms;
    }))fail('invalid_source_receipts');
    if(Date.parse(calendarCapture.received_at)>Math.min(...receipts.map(receipt=>Date.parse(receipt.request_started_at))))fail('invalid_source_receipts');
    for(const subject of [input.symbol,'SPY']){
      const first=receipts.filter(receipt=>receipt.operation===`history_${subject}_1Day_page_1`),second=receipts.filter(receipt=>receipt.operation===`history_${subject}_1Day_page_2`);
      if(first.length!==1||second.length>1||!validHistoryReceipt(first[0],subject,1,input)
        ||first[0].has_next_page!==(second.length===1)||second.length===1&&!validHistoryReceipt(second[0],subject,2,input))fail('invalid_source_receipts');
      if((first[0].provider_rows+(second[0]?.provider_rows||0))!==505)fail('invalid_source_receipts');
    }
    const series=input.bars_by_symbol;
    if(!series||typeof series!=='object'||Array.isArray(series)||Object.keys(series).sort().join(',')!==[input.symbol,'SPY'].sort().join(','))fail('invalid_paired_series');
    const selectedDates=new Set(selected.map(session=>session.date));
    const used={};
    for(const name of [input.symbol,'SPY']){
      const bars=series[name];if(!Array.isArray(bars)||bars.length>1000)fail('history_bound_exceeded');
      const byDate=new Map();let previous=-Infinity;
      for(const bar of bars){
        if(!bar||!instant(bar.t)||![bar.o,bar.h,bar.l,bar.c,bar.v].every(value=>typeof value==='number'&&Number.isFinite(value)&&value>0)
          ||bar.h<Math.max(bar.o,bar.c)||bar.l>Math.min(bar.o,bar.c)||bar.h<bar.l)fail('invalid_bar');
        const at=Date.parse(bar.t),day=nyDate(at);
        if(at<=previous||byDate.has(day))fail('unordered_or_duplicate_bar');previous=at;
        if(at<start||at>=end)fail('bar_outside_requested_window');
        if(!isNyMidnight(at))fail('off_daily_grid_bar');
        if(!selectedDates.has(day))fail('non_session_bar');
        byDate.set(day,{t:new Date(at).toISOString(),o:bar.o,h:bar.h,l:bar.l,c:bar.c,v:bar.v});
      }
      used[name]=selected.map(session=>{const bar=byDate.get(session.date);if(!bar)fail(name==='SPY'?'missing_benchmark_session_bar':'missing_symbol_session_bar');return bar;});
    }
    for(let index=0;index<505;index++)if(used[input.symbol][index].t!==used.SPY[index].t)fail('paired_session_mismatch');
    const latestAge=(now-end)/1000;if(!Number.isFinite(latestAge)||latestAge<0||latestAge>FE02_PAIRED_POLICY.freshness_max_age_seconds)fail('stale_source');
    const {features,regression,measurements}=computeFE02PairedFeatures(used[input.symbol].map(bar=>bar.c),used.SPY.map(bar=>bar.c));
    const calculator=evaluateForecastEngine('FE02',features);if(calculator.status!=='research_only_score')fail('calculator_abstained');
    return {...out,status:'computed',symbol:input.symbol,benchmark_symbol:'SPY',evaluation_at:input.evaluation_at,features,calculator_result:calculator,
      calculator_provenance_note:'The original fixed FE02 scorer is unchanged. This outer policy constructs new paired residual features; it is not a recovered canonical builder or validated forecast.',
      source:{provider:FE02_PAIRED_POLICY.provider,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:input.symbol_asof,benchmark_symbol:'SPY',
        requested_window:input.requested_window,calendar:{received_at:cal.received_at,capture:calendarCapture,requested_range:range,
          selected_session_grid:{columns:['date','open','close'],rows:selected.map(session=>[session.date,session.open,session.close])},
          selected_calendar_sha256:hash(selected),complete_provider_response:true},captures:receipts,pagination_complete:true,
        selected_bars_sha256:hash({[input.symbol]:used[input.symbol],SPY:used.SPY}),series_sha256:{[safeSeriesKey(input.symbol)]:hash(used[input.symbol]),SPY:hash(used.SPY)},
        regression:{...regression,window_start:selected.at(-253).date,window_end:selected.at(-2).date,benchmark:'SPY'},
        source_policy_fingerprint:hash({policy_sha256:FE02_PAIRED_POLICY_SHA256,provider:FE02_PAIRED_POLICY.provider,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',benchmark:'SPY'}),
        historical_availability:'unknown; current captures do not establish availability at historical decisions',price_basis:'split_adjusted_dividend_excluded',provider_revisions_possible:true,
        atomic_snapshot:false,calendar_omissions_independently_verified:false,corporate_actions_independently_verified:false,historical_symbol_continuity_independently_verified:false,
        rights_attestation:null,quality_score:null},
      measurements,coverage:{required_sessions:505,complete_sessions:505,used_daily_bars_per_symbol:505,symbol_bars:505,benchmark_bars:505,missing_intervals_filled:false,
        aligned_session_grid:true,benchmark:'SPY'},freshness:{age_evaluated_at:input.evaluation_at,source_as_of:selected.at(-1).close,source_age_seconds:latestAge,
        max_age_seconds:FE02_PAIRED_POLICY.freshness_max_age_seconds,status:'within_declared_age',current_source_age_acceptable:true},
      warnings:['NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER','DECISION_TIME_BETA_REUSED_FOR_HISTORY_NOT_POINT_IN_TIME','FIXED_COEFFICIENTS_NOT_FITTED',
        'IEX_SINGLE_EXCHANGE_NOT_CONSOLIDATED','DIVIDEND_EXCLUDED_NOT_TOTAL_RETURN','PROVIDER_REVISIONS_POSSIBLE','NO_HISTORICAL_POINT_IN_TIME_ASSERTION',
        'NO_CALIBRATION_OR_PROFITABILITY_CLAIM','NOT_DECISION_ELIGIBLE']};
  }catch(error){return {...out,status:'unavailable',error:error?.message||'feature_construction_failed'};}
}
