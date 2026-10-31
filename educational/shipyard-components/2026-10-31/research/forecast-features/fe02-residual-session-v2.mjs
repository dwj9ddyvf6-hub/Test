// NEW V2 source-session availability policy. Frozen V1 math and original scorer remain unchanged.
// Current research availability is distinct from the original48h input-age contract.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {computeFE02PairedFeatures,FE02_PAIRED_POLICY as V1_POLICY,FE02_PAIRED_POLICY_SHA256 as V1_POLICY_SHA256} from './fe02-residual-v1.mjs';
export {computeFE02PairedFeatures};
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex,utf8ToBytes} from '@noble/hashes/utils.js';

const hash=value=>bytesToHex(sha256(utf8ToBytes(JSON.stringify(value))));
const fail=code=>{throw Error(code);};
const DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const TIME_FORMAT=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});

const {freshness_max_age_seconds:originalCatalogAge,...V1_MEASUREMENT_POLICY}=V1_POLICY;
export const FE02_PAIRED_POLICY=Object.freeze({
  ...V1_MEASUREMENT_POLICY,id:'FE02_PAIRED_BENCHMARK_RESIDUAL_SESSION_V2',version:2,
  math_policy_id:V1_POLICY.id,math_policy_sha256:V1_POLICY_SHA256,
  original_catalog_max_age_seconds:originalCatalogAge,
  calendar_session_age_guard_seconds:604800,
  session_currency:'Latest completed session in a fresh complete official-provider calendar response through the current New York date; close+15min must be <= actual evaluation. Every selected paired session is required; no older-window substitution.',
  original_age_semantics:'The original catalog48h maximum is unchanged and reported independently. Exceeding it does not satisfy the original input contract; V2 only permits descriptive research when the complete latest official-returned session grid is present.',
  extended_closure_guard:'If the latest returned completed close is older than7calendar days, abstain extended_closure_or_calendar_staleness_unverified. This sanity/review boundary is not an observation-freshness claim or a replacement for the original48h rule.',
  acquisition_currency:'All actual acquisition request starts and receipts must be within25s before evaluation; calendar completes before history starts. Same original response/page/rate budgets. Source observation clocks are never replaced by retrieval time.',
  cache:'Successful results only, at most60s from evaluation; expire at next eligible-session boundary, New York midnight, original48h threshold if future, or7day guard. Delivery age is separate; original source/evaluation/receipt clocks are immutable.',
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
    ||now-Date.parse(receipt.request_started_at)>FE02_PAIRED_POLICY.acquisition_budget_seconds*1000
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

function emptyResult(){return {schema:'SHIPYARD_FE02_SOURCE_FORECAST_V2',engine_id:'FE02',feature_origin:'provider_capture_new_policy',
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
    if(Date.parse(calendarCapture.request_started_at)<end+FE02_PAIRED_POLICY.completion_delay_ms)fail('invalid_calendar_receipt');
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
      if(second.length===1&&Date.parse(second[0].request_started_at)<Date.parse(first[0].received_at))fail('invalid_source_receipts');
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
    const latestAge=(now-end)/1000;
    if(!Number.isFinite(latestAge)||latestAge<0)fail('invalid_source_age');
    if(latestAge>FE02_PAIRED_POLICY.calendar_session_age_guard_seconds)fail('extended_closure_or_calendar_staleness_unverified');
    const originalAgeAcceptable=latestAge<=FE02_PAIRED_POLICY.original_catalog_max_age_seconds;
    const {features,regression,measurements}=computeFE02PairedFeatures(used[input.symbol].map(bar=>bar.c),used.SPY.map(bar=>bar.c));
    const calculator=evaluateForecastEngine('FE02',features);if(calculator.status!=='research_only_score')fail('calculator_abstained');
    return {...out,status:'computed',symbol:input.symbol,benchmark_symbol:'SPY',evaluation_at:input.evaluation_at,features,calculator_result:calculator,
      calculator_provenance_note:'The original fixed FE02 scorer is unchanged. This outer policy constructs new paired residual features; it is not a recovered canonical builder or validated forecast.',
      source:{provider:FE02_PAIRED_POLICY.provider,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:input.symbol_asof,benchmark_symbol:'SPY',
        requested_window:input.requested_window,calendar:{received_at:cal.received_at,capture:calendarCapture,requested_range:range,
          selected_session_grid:{columns:['date','open','close'],rows:selected.map(session=>[session.date,session.open,session.close])},
          selected_calendar_sha256:hash(selected),complete_provider_response:true},captures:receipts,pagination_complete:true,
        selected_bars_sha256:hash({[input.symbol]:used[input.symbol],SPY:used.SPY}),series_sha256:{[safeSeriesKey(input.symbol)]:hash(used[input.symbol]),SPY:hash(used.SPY)},
        math_policy:{id:V1_POLICY.id,sha256:V1_POLICY_SHA256},
        regression:{...regression,window_start:selected.at(-253).date,window_end:selected.at(-2).date,benchmark:'SPY'},
        source_policy_fingerprint:hash({policy_sha256:FE02_PAIRED_POLICY_SHA256,provider:FE02_PAIRED_POLICY.provider,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',benchmark:'SPY'}),
        historical_availability:'unknown; current captures do not establish availability at historical decisions',price_basis:'split_adjusted_dividend_excluded',provider_revisions_possible:true,
        atomic_snapshot:false,calendar_omissions_independently_verified:false,corporate_actions_independently_verified:false,historical_symbol_continuity_independently_verified:false,
        rights_attestation:null,quality_score:null},
      measurements,coverage:{required_sessions:505,complete_sessions:505,used_daily_bars_per_symbol:505,symbol_bars:505,benchmark_bars:505,missing_intervals_filled:false,
        aligned_session_grid:true,benchmark:'SPY'},freshness:{basis:'latest_completed_session_in_current_official_provider_calendar',status:'latest_completed_session',
        age_evaluated_at:input.evaluation_at,source_as_of:selected.at(-1).close,source_age_seconds:latestAge,source_session_date:selected.at(-1).date,
        expected_completed_session_date:selected.at(-1).date,source_session_matches_calendar:true,current_calendar_request_through_date:range.end_date,
        original_catalog_max_age_seconds:FE02_PAIRED_POLICY.original_catalog_max_age_seconds,original_catalog_age_acceptable:originalAgeAcceptable,
        original_catalog_age_status:originalAgeAcceptable?'within_declared_age':'exceeds_original_48h',calendar_session_age_guard_seconds:FE02_PAIRED_POLICY.calendar_session_age_guard_seconds,
        research_display_eligible:true,decision_eligible:false},
      warnings:['NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER','DECISION_TIME_BETA_REUSED_FOR_HISTORY_NOT_POINT_IN_TIME','FIXED_COEFFICIENTS_NOT_FITTED',
        'IEX_SINGLE_EXCHANGE_NOT_CONSOLIDATED','DIVIDEND_EXCLUDED_NOT_TOTAL_RETURN','PROVIDER_REVISIONS_POSSIBLE','NO_HISTORICAL_POINT_IN_TIME_ASSERTION',
        'NO_CALIBRATION_OR_PROFITABILITY_CLAIM','NOT_DECISION_ELIGIBLE','SESSION_RELATIVE_RESEARCH_CURRENCY_NOT_INTRADAY_FRESHNESS',
        ...(!originalAgeAcceptable?['ORIGINAL_CATALOG_48H_AGE_EXCEEDED_RESEARCH_ONLY']:[])]};
  }catch(error){return {...out,status:'unavailable',error:error?.message||'feature_construction_failed'};}
}
