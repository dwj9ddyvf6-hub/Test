// Explicit NEW daily breakout/acceptance policy. The original FE03 feature builder
// was not recovered; this is a research-only source policy, not a canonical port.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex,utf8ToBytes} from '@noble/hashes/utils.js';

const hash=value=>bytesToHex(sha256(utf8ToBytes(JSON.stringify(value))));
const fail=code=>{throw Error(code);};
const DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const TIME_FORMAT=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const WALL_TIME_FORMAT=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});

export const FE03_BREAKOUT_POLICY=Object.freeze({
  id:'FE03_DAILY_BREAKOUT_ACCEPTANCE_MATURED_V1',version:1,origin:'NEW_FEATURE_POLICY',engine_id:'FE03',
  provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',
  symbol_mapping:'Explicit asof=current acquisition New York date; current entity, not historical universe membership.',
  sessions:505,calendar_lookback_days:800,calendar:'Alpaca US equity official market calendar; America/New_York',completion_delay_ms:900000,
  acquisition_budget_seconds:25,per_request_timeout_seconds:8,max_pages:2,max_rows:1000,max_response_bytes_per_request:524288,
  episode_trigger:'For session u>=21, L[u]=max(high[u-20..u-1]); priorL=max(high[u-21..u-2]); one episode start iff close[u]>L[u] AND close[u-1]<=priorL. Episode ID is the symbol plus official session date. Trigger attempts within a five-session outcome window are distinct starts if they independently satisfy this rule; outcomes may overlap and are not independent observations.',
  candidate_window:'Choose the latest episode start u in the final six completed session positions [t-5..t], including an event that has matured exactly at t. A newer episode takes precedence; never fall back to an older candidate.',
  level:'The episode level is frozen as L[u]=max(high[u-20..u-1]) from exactly the prior20 official sessions; the candidate current close must remain >=L[u], otherwise return level_invalidated with no numeric score.',
  break_distance:'d[u]=ln(close[u]/L[u]). break_distance_z=(d[u]-mean(d[u-252..u-1]))/population_SD(d[u-252..u-1]); each historical d[k]=ln(close[k]/max(high[k-20..k-1])). Current and future rows are excluded from the normalizer.',
  volume_surprise:'volume_surprise_z=(ln(1+volume[u])-mean(ln(1+volume[u-20..u-1])))/population_SD(ln(1+volume[u-20..u-1])). Provider split-adjusted daily share volume; no percent conversion or clipping.',
  acceptance:'Across ALL observed post-crossing completed closes u+1..t, numerator=count(close[j]>=L[u]); denominator=t-u. Require3..5 observed post-crossing closes. Acceptance=numerator/denominator. Report denominator, any close<L[u], and whether a later close>=L[u] reclaimed after a breach. Equality is accepted.',
  current_setup:'A candidate is numeric only if latest completed close[t]>=L[u]. If close[t]<L[u], return level_invalidated; equality remains valid. If no episode starts in [t-5..t], return no_setup.',
  false_break:'A mature episode is false if any of its next5 official-session closes is < its own frozen L[u]; equality is not a failure. Denominator is every trigger episode with start u in the 479 possible date positions [21..t-5] of exactly505 rows, excluding the selected candidate by episode ID even when u=t-5 and its outcome is mature. Every denominator row has all five subsequent closes. Numerator is the exact count of such failures; rate=numerator/denominator.',
  minimum_mature_episodes:20,
  sample_floor:'Require >=20 matured historical episode IDs after candidate exclusion. This is a provisional policy sample floor, not a precision claim, inferential minimum, calibration, statistical independence, or performance evidence. If unmet, report counts and abstain without a numeric rate or score.',
  dependencies:'History contains exactly505 consecutive completed official-calendar sessions. A failed/missing/duplicate/off-grid bar is not skipped, filled, or replaced. Any population SD <=1e-12 abstains; no epsilon floor.',
  units:'Natural-log price ratios; both *_z inputs are population z-scores (ddof=0); acceptance and false_break_rate are empirical ratios in [0,1]. OHLC prices are positive split-adjusted USD; volume is positive split-adjusted shares. No annualization, sample-ddof correction, imputation, epsilon, or feature clipping.',
  original_quality_contract:'The pinned catalog requires min_quality=0.2 per input. This provider adapter does not invent a quality score or rights attestation; source.quality_score and rights_attestation remain null. The scalar scorer wrapper is not the full Python FeatureObservation validator.',
  price_basis:'Split-adjusted, dividend-excluded provider prices; not total returns. Other corporate actions and historical revisions not independently checked.',
  source_age:'Report source age from latest eligible completed close separately against original catalog172800s maximum. A weekend/holiday source-age diagnostic never becomes a fresh observation; session-relative research is descriptive only. Refuse if latest returned close is older than7calendar days.',
  provenance:'Event clock u (price level, distance, volume surprise), acceptance window u+1..t, and latest source cutoff t are separately disclosed. False-break episodes are historical labels fully mature by t and candidate ID is explicitly excluded. Current event outcome is never part of its own false-break rate.',
  forecast_interpretation:'Unchanged fixed FE03 scorer on NEW conditionally accepted-breakout measurements; uncalibrated signed orientation only, not return magnitude, probability, edge, fill, trading permission, or a recommendation. Forecast horizon begins at latest source cutoff t, not event u.',
});
export const FE03_BREAKOUT_POLICY_SHA256=hash(FE03_BREAKOUT_POLICY);

const ISO=/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?Z$/;
const instant=x=>typeof x==='string'&&ISO.test(x)&&! /\.\d{3}\d*[1-9]\d*Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(Date.parse(x)).toISOString().slice(0,10)===x.slice(0,10);
const date=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x+'T00:00:00Z'))&&new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
const etDate=ms=>DATE_FORMAT.format(new Date(ms));
const isNyMidnight=ms=>TIME_FORMAT.format(new Date(ms))==='00:00:00'&&ms%1000===0;
const mean=values=>values.reduce((sum,value)=>sum+value,0)/values.length;
function populationStats(values,label){
  if(!Array.isArray(values)||!values.length||values.some(value=>!Number.isFinite(value)))fail('nonfinite_'+label);
  const m=mean(values),variance=mean(values.map(value=>(value-m)**2)),sd=Math.sqrt(variance);
  if(!Number.isFinite(m)||!Number.isFinite(sd)||sd<=1e-12)fail('degenerate_'+label+'_normalizer');
  return {mean:m,population_sd:sd,count:values.length};
}
function isEpisodeStart(rows,index){
  if(index<21||index>=rows.length)return false;
  const level=Math.max(...rows.slice(index-20,index).map(row=>row.h));
  const priorLevel=Math.max(...rows.slice(index-21,index-1).map(row=>row.h));
  return rows[index].c>level&&rows[index-1].c<=priorLevel;
}

// Pure deterministic oracle surface for independent tests and native from-bars use.
// It intentionally consumes only the supplied fixed window; no caller data can reach the provider adapter.
export function computeFE03BreakoutMeasurements(rows,symbol='SPY',cutoffIndex=Array.isArray(rows)?rows.length-1:-1){
  if(!Array.isArray(rows)||rows.length<FE03_BREAKOUT_POLICY.sessions||!Number.isInteger(cutoffIndex)
    ||cutoffIndex<FE03_BREAKOUT_POLICY.sessions-1||cutoffIndex>=rows.length)fail('invalid_daily_history');
  if(rows.slice(0,cutoffIndex+1).some(row=>!row||!date(row.date)||![row.h,row.c,row.v].every(value=>typeof value==='number'&&Number.isFinite(value)&&value>0)))fail('invalid_daily_history');
  const t=cutoffIndex;
  const levelAt=index=>Math.max(...rows.slice(index-20,index).map(row=>row.h));
  const prefix=rows.slice(0,t+1),distances=prefix.map((row,index)=>index<20?null:Math.log(row.c/levelAt(index)));
  const volumeLogs=prefix.map(row=>Math.log1p(row.v));
  const recentStarts=[];
  for(let index=t-5;index<=t;index++)if(isEpisodeStart(rows,index))recentStarts.push(index);
  const candidateIndex=recentStarts.at(-1)??null;
  const possibleMatureStarts=[];
  for(let index=21;index<=t-5;index++)if(isEpisodeStart(rows,index))possibleMatureStarts.push(index);
  const candidateId=candidateIndex===null?null:`${symbol}:${rows[candidateIndex].date}`;
  const matureEpisodes=possibleMatureStarts.filter(index=>`${symbol}:${rows[index].date}`!==candidateId);
  const falseBreakCount=matureEpisodes.filter(index=>rows.slice(index+1,index+6).some(row=>row.c<levelAt(index))).length;
  const maturedIds=matureEpisodes.map(index=>`${symbol}:${rows[index].date}`),falseIds=matureEpisodes.filter(index=>rows.slice(index+1,index+6).some(row=>row.c<levelAt(index))).map(index=>`${symbol}:${rows[index].date}`);
  const history={eligible_episode_date_slots:t-5-21+1,eligible_trigger_start_index:21,eligible_trigger_end_index:t-5,
    recent_trigger_count:recentStarts.length,matured_episode_count_before_candidate_exclusion:possibleMatureStarts.length,
    candidate_episode_excluded_count:candidateId!==null&&possibleMatureStarts.includes(candidateIndex)?1:0,
    candidate_episode_excluded_id:candidateId!==null&&possibleMatureStarts.includes(candidateIndex)?candidateId:null,
    unmatured_trigger_count:Array.from({length:5},(_,index)=>t-4+index).filter(index=>isEpisodeStart(rows,index)).length,
    matured_episode_count:matureEpisodes.length,false_break_count:falseBreakCount,
    minimum_required:FE03_BREAKOUT_POLICY.minimum_mature_episodes,candidate_episode_excluded:candidateId!==null&&possibleMatureStarts.includes(candidateIndex),
    sample_floor_met:matureEpisodes.length>=FE03_BREAKOUT_POLICY.minimum_mature_episodes,
    mature_episode_ids_sha256:hash(maturedIds),false_episode_ids_sha256:hash(falseIds),outcome_windows_may_overlap:true,independent_sample_claim:false};
  if(candidateIndex===null)return {status:'no_setup',cutoff_index:t,candidate:null,history};
  const level=levelAt(candidateIndex),post=rows.slice(candidateIndex+1,t+1),age=t-candidateIndex;
  const breachIndices=post.map((row,index)=>row.c<level?candidateIndex+1+index:null).filter(index=>index!==null);
  const acceptanceNumerator=post.filter(row=>row.c>=level).length;
  const reclaimedAfterBreach=breachIndices.some(index=>rows.slice(index+1,t+1).some(row=>row.c>=level));
  const candidate={episode_id:candidateId,episode_index:candidateIndex,episode_session:rows[candidateIndex].date,
    event_level:level,event_close:rows[candidateIndex].c,event_volume:rows[candidateIndex].v,
    acceptance_numerator:acceptanceNumerator,acceptance_denominator:post.length,
    acceptance:post.length?acceptanceNumerator/post.length:null,any_breach:breachIndices.length>0,
    reclaimed_after_breach:reclaimedAfterBreach,breach_sessions:breachIndices.map(index=>rows[index].date),
    acceptance_window_start:post[0]?.date??null,acceptance_window_end:post.at(-1)?.date??null,
    observed_current_close:rows[t].c,observed_current_session:rows[t].date,age_in_completed_sessions:age};
  if(rows[t].c<level)return {status:'level_invalidated',cutoff_index:t,candidate,history};
  if(post.length<3)return {status:'acceptance_not_mature',cutoff_index:t,candidate,history};
  if(post.length>5)fail('acceptance_window_bound_exceeded');
  if(matureEpisodes.length<FE03_BREAKOUT_POLICY.minimum_mature_episodes)
    return {status:'insufficient_mature_episode_sample',cutoff_index:t,candidate,history};
  const distancePrior=distances.slice(candidateIndex-252,candidateIndex),distanceStats=populationStats(distancePrior,'break_distance');
  const distance=distances[candidateIndex],breakDistanceZ=(distance-distanceStats.mean)/distanceStats.population_sd;
  const volumePrior=volumeLogs.slice(candidateIndex-20,candidateIndex),volumeStats=populationStats(volumePrior,'volume_surprise');
  const volumeLog=volumeLogs[candidateIndex],volumeSurpriseZ=(volumeLog-volumeStats.mean)/volumeStats.population_sd;
  if(!Number.isFinite(breakDistanceZ)||!Number.isFinite(volumeSurpriseZ))fail('nonfinite_feature');
  const features={break_distance_z:breakDistanceZ,acceptance:candidate.acceptance,volume_surprise_z:volumeSurpriseZ,
    false_break_rate:falseBreakCount/matureEpisodes.length};
  const failures=matureEpisodes.filter(index=>rows.slice(index+1,index+6).some(row=>row.c<levelAt(index)));
  return {status:'computed',cutoff_index:t,candidate,features,history,normalization:{break_distance:{current:distance,...distanceStats,window_start:rows[candidateIndex-252].date,window_end:rows[candidateIndex-1].date,current_excluded:true,population_ddof:0},
      volume_surprise:{current:volumeLog,...volumeStats,window_start:rows[candidateIndex-20].date,window_end:rows[candidateIndex-1].date,current_excluded:true,population_ddof:0}},
    false_break:{numerator:falseBreakCount,denominator:matureEpisodes.length,rate:features.false_break_rate,episode_ids_sha256:history.mature_episode_ids_sha256,
      false_episode_ids_sha256:history.false_episode_ids_sha256,outcome_window_sessions:5,candidate_episode_excluded:history.candidate_episode_excluded,
      outcome_windows_may_overlap:true,statistical_independence_claim:false}};
}

function base(){return {schema:'SHIPYARD_FE03_SOURCE_FORECAST_V1',engine_id:'FE03',feature_origin:'provider_capture_new_policy',feature_policy:FE03_BREAKOUT_POLICY,
  feature_policy_sha256:FE03_BREAKOUT_POLICY_SHA256,restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,
    account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false}};}
function validReceipt(receipt,operation,subject,now,earliest){
  return !!receipt&&receipt.operation===operation&&receipt.subject===subject&&receipt.http_status===200
    &&instant(receipt.request_started_at)&&instant(receipt.http_response_received_at)&&instant(receipt.received_at)
    &&Date.parse(receipt.request_started_at)>=earliest&&Date.parse(receipt.request_started_at)<=Date.parse(receipt.http_response_received_at)
    &&Date.parse(receipt.http_response_received_at)<=Date.parse(receipt.received_at)&&Date.parse(receipt.received_at)<=now
    &&now-Date.parse(receipt.request_started_at)<=FE03_BREAKOUT_POLICY.acquisition_budget_seconds*1000
    &&/^[0-9a-f]{64}$/.test(receipt.response_sha256||'')&&receipt.hash_serialization==='UTF-8 re-encoding of decoded response text';
}
function validCaptureUrl(receipt,kind,input,page){
  let url;try{url=new URL(receipt.request_url);}catch{return false;}
  const range=input.calendar.requested_range;
  if(kind==='calendar')return url.origin==='https://paper-api.alpaca.markets'&&url.pathname==='/v2/calendar'
    &&[...url.searchParams.keys()].sort().join(',')==='end,start'&&url.searchParams.get('start')===range.start_date&&url.searchParams.get('end')===range.end_date;
  const window=input.requested_window,expectedEnd=new Date(Date.parse(window.end)-1).toISOString();
  const keys=page===1?'adjustment,asof,currency,end,feed,limit,sort,start,timeframe':'adjustment,asof,currency,end,feed,limit,page_token,sort,start,timeframe';
  return url.origin==='https://data.alpaca.markets'&&url.pathname===`/v2/stocks/${encodeURIComponent(input.symbol)}/bars`
    &&[...url.searchParams.keys()].sort().join(',')===keys&&url.searchParams.get('timeframe')==='1Day'
    &&url.searchParams.get('start')===window.start&&url.searchParams.get('end')===expectedEnd&&url.searchParams.get('feed')==='iex'
    &&url.searchParams.get('adjustment')==='split'&&url.searchParams.get('currency')==='USD'&&url.searchParams.get('asof')===input.symbol_asof
    &&url.searchParams.get('sort')==='asc'&&url.searchParams.get('limit')==='1000'
    &&(page===1?!url.searchParams.has('page_token'):url.searchParams.get('page_token')==='[continuation]');
}

export function buildFE03SourceForecast(input){
  const out=base();
  try{
    if(!input||typeof input.symbol!=='string'||!/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(input.symbol)||input.feed!=='iex'||input.adjustment!=='split'
      ||input.timeframe!=='1Day'||input.currency!=='USD')fail('source_identity_mismatch');
    if(!instant(input.evaluation_at))fail('invalid_evaluation_clock');
    const now=Date.parse(input.evaluation_at),cal=input.calendar,range=cal?.requested_range;
    if(input.symbol_asof!==etDate(now))fail('symbol_mapping_mismatch');
    if(!cal||cal.complete_provider_response!==true||!Array.isArray(cal.sessions)||cal.sessions.length>801||!instant(cal.received_at)
      ||Date.parse(cal.received_at)>now||!date(range?.start_date)||!date(range?.end_date)||range.start_date>range.end_date||range.end_date!==etDate(now)
      ||Date.parse(range.end_date)-Date.parse(range.start_date)>800*86400000)fail('invalid_calendar_lineage');
    const calendarCapture=input.calendar_capture;
    if(!validReceipt(calendarCapture,'official_calendar','US_EQUITY',now,now-FE03_BREAKOUT_POLICY.acquisition_budget_seconds*1000)
      ||calendarCapture.received_at!==cal.received_at||!validCaptureUrl(calendarCapture,'calendar',input))fail('invalid_calendar_receipt');
    let previousDate='',previousClose=-Infinity;
    const sessions=[];
    for(const session of cal.sessions){
      if(!date(session?.date)||session.date<=previousDate||session.date<range.start_date||session.date>range.end_date||!instant(session.open)||!instant(session.close))fail('invalid_calendar');
      const open=Date.parse(session.open),close=Date.parse(session.close),duration=close-open;
      const openLocal=WALL_TIME_FORMAT.format(new Date(open)),closeLocal=WALL_TIME_FORMAT.format(new Date(close));
      if(open>=close||duration<=0||duration>960*60000||duration%60000!==0||open%60000!==0||close%60000!==0||open<=previousClose||etDate(open)!==session.date||etDate(close-1)!==session.date
        ||openLocal<'04:00'||closeLocal>'20:00'||openLocal>=closeLocal)fail('invalid_calendar');
      previousDate=session.date;previousClose=close;
      if(close+FE03_BREAKOUT_POLICY.completion_delay_ms<=now)sessions.push({date:session.date,open:new Date(open).toISOString(),close:new Date(close).toISOString()});
    }
    if(sessions.length<FE03_BREAKOUT_POLICY.sessions)fail('insufficient_completed_sessions');
    const selected=sessions.slice(-FE03_BREAKOUT_POLICY.sessions),sourceClose=Date.parse(selected.at(-1).close),sourceAge=(now-sourceClose)/1000;
    if(sourceAge<0)fail('future_dated_source');
    if(sourceAge>604800)fail('extended_closure_or_calendar_staleness_unverified');
    const requestedStart=Date.parse(input.requested_window?.start),requestedEnd=Date.parse(input.requested_window?.end);
    if(!instant(input.requested_window?.start)||!instant(input.requested_window?.end)||!isNyMidnight(requestedStart)
      ||etDate(requestedStart)!==selected[0].date||requestedEnd!==sourceClose||input.requested_window.end_exclusive!==true)fail('invalid_requested_window');
    if(input.pagination_complete!==true||!Array.isArray(input.captures)||input.captures.length<1||input.captures.length>2)fail('incomplete_provider_pagination');
    const captures=input.captures;
    let priorReceipt=Date.parse(calendarCapture.received_at);
    for(let index=0;index<captures.length;index++){
      const page=index+1,receipt=captures[index];
      if(!validReceipt(receipt,`history_1Day_page_${page}`,input.symbol,now,priorReceipt)||!Number.isInteger(receipt.provider_rows)
        ||receipt.provider_rows<0||receipt.provider_rows>1000||typeof receipt.has_next_page!=='boolean'||!validCaptureUrl(receipt,'history',input,page))fail('invalid_source_receipts');
      if(page>1&&captures[page-2].has_next_page!==true)fail('invalid_provider_pagination');
      if(page===1&&captures.length===2&&!receipt.has_next_page)fail('invalid_provider_pagination');
      if(page===captures.length&&receipt.has_next_page)fail('invalid_provider_pagination');
      priorReceipt=Date.parse(receipt.received_at);
    }
    if(captures.reduce((sum,receipt)=>sum+receipt.provider_rows,0)!==input.bars?.length)fail('provider_row_count_mismatch');
    if(!Array.isArray(input.bars)||input.bars.length>1000)fail('history_bound_exceeded');
    const selectedDates=new Set(selected.map(session=>session.date)),byDate=new Map();let previousBar=-Infinity;
    for(const bar of input.bars){
      if(!bar||!instant(bar.t)||![bar.o,bar.h,bar.l,bar.c,bar.v].every(value=>typeof value==='number'&&Number.isFinite(value)&&value>0)
        ||bar.h<Math.max(bar.o,bar.c)||bar.l>Math.min(bar.o,bar.c)||bar.h<bar.l)fail('invalid_bar');
      const at=Date.parse(bar.t),day=etDate(at);
      if(at<=previousBar||byDate.has(day))fail('unordered_or_duplicate_bar');previousBar=at;
      if(at<requestedStart||at>=requestedEnd)fail('bar_outside_requested_window');
      if(!isNyMidnight(at))fail('off_daily_grid_bar');
      if(!selectedDates.has(day))fail('non_session_bar');
      byDate.set(day,{date:day,t:new Date(at).toISOString(),o:bar.o,h:bar.h,l:bar.l,c:bar.c,v:bar.v});
    }
    const used=selected.map(session=>{const bar=byDate.get(session.date);if(!bar)fail('missing_daily_session_bar');return bar;});
    const measurements=computeFE03BreakoutMeasurements(used,input.symbol);
    const selectedBarsSha=hash(used),selectedCalendarSha=hash(selected),policyFingerprint=hash({policy_sha256:FE03_BREAKOUT_POLICY_SHA256,
      provider:FE03_BREAKOUT_POLICY.provider,feed:FE03_BREAKOUT_POLICY.feed,adjustment:FE03_BREAKOUT_POLICY.adjustment,
      timeframe:FE03_BREAKOUT_POLICY.timeframe,currency:FE03_BREAKOUT_POLICY.currency});
    const source={provider:FE03_BREAKOUT_POLICY.provider,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:input.symbol_asof,
      requested_window:input.requested_window,calendar:{received_at:cal.received_at,requested_range:range,
        selected_session_grid:{columns:['date','open','close'],rows:selected.map(session=>[session.date,session.open,session.close])},
        selected_calendar_sha256:selectedCalendarSha,complete_provider_response:true,historical_availability:'unknown; current calendar receipt does not establish historical availability',calendar_omissions_independently_verified:false},
      captures,pagination_complete:true,selected_bars_sha256:selectedBarsSha,
      source_policy_fingerprint:policyFingerprint,historical_availability:'unknown; current captures do not establish availability at historical decisions',
      price_basis:'split_adjusted_dividend_excluded',provider_revisions_possible:true,atomic_snapshot:false,
      corporate_actions_independently_verified:false,historical_symbol_continuity_independently_verified:false,rights_attestation:null,quality_score:null};
    const freshness={basis:'latest_completed_session_in_current_official_provider_calendar',status:'latest_completed_session',
      age_evaluated_at:input.evaluation_at,source_as_of:selected.at(-1).close,source_session_date:selected.at(-1).date,source_age_seconds:sourceAge,
      original_catalog_max_age_seconds:172800,original_catalog_age_acceptable:sourceAge<=172800,
      original_catalog_age_status:sourceAge<=172800?'within_declared_age':'exceeds_original_48h',calendar_session_age_guard_seconds:604800,
      research_display_eligible:true,decision_eligible:false};
    const candidateClose=measurements.candidate?Date.parse(selected.find(session=>session.date===measurements.candidate.episode_session).close):null;
    const common={...out,symbol:input.symbol,evaluation_at:input.evaluation_at,source,freshness,
      forecast_target:{target:'breakout continuation',target_unit:'forward_return_fraction',horizon:'1-5 sessions',
        horizon_anchor:'latest completed source cutoff session close',horizon_anchor_session:selected.at(-1).date,horizon_anchor_at:selected.at(-1).close},
      coverage:{required_sessions:505,complete_sessions:505,used_daily_bars:used.length,received_bars:input.bars.length,missing_intervals_filled:false,
        trigger_date_slots:measurements.history.eligible_episode_date_slots,matured_episode_count:measurements.history.matured_episode_count,
        min_matured_episode_count:measurements.history.minimum_required},
      episode:{...measurements.candidate,cutoff_session:selected.at(-1).date,cutoff_source_as_of:selected.at(-1).close,
        event_source_as_of:candidateClose===null?null:new Date(candidateClose).toISOString(),
        event_age_seconds:candidateClose===null?null:(sourceClose-candidateClose)/1000,
        acceptance_source_as_of:selected.at(-1).close,acceptance_age_seconds:0},
      history:measurements.history,
      warnings:['NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER','CONDITIONAL_BREAKOUT_SETUP_ONLY','FIXED_COEFFICIENTS_NOT_FITTED',
        'IEX_SINGLE_EXCHANGE_NOT_CONSOLIDATED','DIVIDEND_EXCLUDED_NOT_TOTAL_RETURN','PROVIDER_REVISIONS_POSSIBLE',
        'OVERLAPPING_EPISODE_OUTCOME_WINDOWS_NOT_INDEPENDENT','SOURCE_QUALITY_AND_RIGHTS_ATTESTATIONS_UNKNOWN',
        'NO_HISTORICAL_POINT_IN_TIME_ASSERTION','NO_CALIBRATION_OR_PROFITABILITY_CLAIM',
        'NOT_DECISION_ELIGIBLE','FORECAST_HORIZON_FROM_LATEST_SOURCE_CUTOFF_NOT_EVENT_DATE',
        ...(sourceAge>172800?['ORIGINAL_CATALOG_48H_AGE_EXCEEDED_RESEARCH_ONLY']:[])]};
    if(measurements.status!=='computed')return {...common,status:measurements.status,...(measurements.candidate?{candidate:measurements.candidate}:{}),
      ...(measurements.false_break?{false_break:measurements.false_break}:{}),...(measurements.normalization?{normalization:measurements.normalization}:{})};
    const calculator=evaluateForecastEngine('FE03',measurements.features);if(calculator.status!=='research_only_score')fail('calculator_abstained');
    return {...common,status:'computed',features:measurements.features,calculator_result:calculator,
      calculator_provenance_note:'The original fixed FE03 scorer is byte-for-byte unchanged. This separate NEW daily policy constructs conditional breakout features; it is not a recovered canonical builder, calibrated forecast, or trading admission.',
      candidate:measurements.candidate,normalization:measurements.normalization,false_break:measurements.false_break};
  }catch(error){return {...out,status:'unavailable',error:error?.message||'feature_construction_failed'};}
}
