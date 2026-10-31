// NEW feature policy, not a recovered Silicon feature builder. Original algebra stays imported.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex, utf8ToBytes} from '@noble/hashes/utils.js';
const hash = x => bytesToHex(sha256(utf8ToBytes(JSON.stringify(x))));
export const FE08_RV_POLICY = Object.freeze({
  id:'FE08_RV_RTH_5M_V1', version:1, origin:'NEW_FEATURE_POLICY', engine_id:'FE08',
  provider:'Alpaca Market Data', feed:'iex', adjustment:'raw', timeframe:'5Min', interval_ms:300000,
  sessions:22, calendar:'Alpaca US equity official market calendar; America/New_York',
  completion_delay_ms:900000,
  returns:'First regular bar log(close/open); later regular bars log(close/previous regular bar close). No cross-session returns.',
  session_variance:'Sum of squared fractional log returns over every expected regular-session 5-minute slot.',
  aggregation:'log_rv_1=log(last RV); log_rv_5=log(arithmetic mean of last 5 RV); log_rv_22=log(arithmetic mean of last 22 RV).',
  baseline:'log_rv_baseline equals log_rv_22; same trailing 22-session reference INCLUDING latest completed session, not an independent control.',
  units:'Fractional log-return squared per observed session; no square root, percent conversion, annualization or 1-to-5-day scaling.',
  early_close:'Use actual official session length; no 390-minute normalization.',
  zero_missing:'Any nonpositive session RV, absent slot, duplicate, malformed or off-grid bar abstains. No epsilon, fill or older-session substitution.',
  overnight:'Excluded; raw prices do not cross sessions. Intraday corporate actions or bad prints are not independently identified.',
  freshness_max_age_seconds:172800,
  freshness:'Age is from latest selected session close, never retrieval time. Old source can be shown as stale research, never represented as fresh.',
  forecast_interpretation:'Fixed original FE08 blend on this NEW daily measurement policy. Original 1-5-session label is not horizon-specific fitted calibration.',
});
export const FE08_RV_POLICY_SHA256 = hash(FE08_RV_POLICY);
const ISO = /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?Z$/;
// Date.parse truncates sub-millisecond digits; reject nonzero hidden precision.
const instant = x => typeof x==='string' && ISO.test(x) && !/\.\d{3}\d*[1-9]\d*Z$/.test(x) && Number.isFinite(Date.parse(x)) && new Date(Date.parse(x)).toISOString().slice(0,10)===x.slice(0,10);
const date = x => typeof x==='string' && /^\d{4}-\d{2}-\d{2}$/.test(x) && Number.isFinite(Date.parse(x+'T00:00:00Z')) && new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
const fail = code => {throw Error(code);};
const base = () => ({schema:'SHIPYARD_FE08_SOURCE_FORECAST_V1',engine_id:'FE08',feature_origin:'provider_capture_new_policy',feature_policy:FE08_RV_POLICY,feature_policy_sha256:FE08_RV_POLICY_SHA256,
  restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,calibrated_probability:null,historical_point_in_time_claim:false}});
const etDate = ms => new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(ms));
export function buildFE08SourceForecast(input) {
  const out=base();
  try {
    if(!input || typeof input.symbol!=='string' || !/^[A-Z0-9][A-Z0-9.-]{0,9}$/.test(input.symbol||'') || input.feed!=='iex' || input.adjustment!=='raw' || input.timeframe!=='5Min')fail('source_identity_mismatch');
    if(!instant(input.evaluation_at))fail('invalid_evaluation_clock');
    const now=Date.parse(input.evaluation_at), cal=input.calendar, range=cal?.requested_range;
    if(!cal || cal.complete_provider_response!==true || !Array.isArray(cal.sessions) || cal.sessions.length>370 || !instant(cal.received_at) || Date.parse(cal.received_at)>now || !date(range?.start_date) || !date(range?.end_date) || range.start_date>range.end_date || range.end_date!==etDate(now))fail('invalid_calendar_lineage');
    const sessions=[]; let previous=-Infinity,previousDate='';
    for(const s of cal.sessions) {
      if(!date(s?.date)||s.date<=previousDate||s.date<range.start_date||s.date>range.end_date||!instant(s.open)||!instant(s.close))fail('invalid_calendar');
      const open=Date.parse(s.open),close=Date.parse(s.close),duration=close-open;
      if(open<=previous||duration<=0||duration>390*60000||duration%300000!==0||etDate(open)!==s.date||etDate(close-1)!==s.date)fail('invalid_calendar');
      previous=close;previousDate=s.date;
      if(close+FE08_RV_POLICY.completion_delay_ms<=now)sessions.push({date:s.date,open:new Date(open).toISOString(),close:new Date(close).toISOString(),expected_bars:duration/300000});
    }
    if(sessions.length<22)fail('insufficient_completed_sessions');
    const selected=sessions.slice(-22), start=Date.parse(selected[0].open),end=Date.parse(selected.at(-1).close);
    if(!instant(input.requested_window?.start)||!instant(input.requested_window?.end)||Date.parse(input.requested_window.start)>start||Date.parse(input.requested_window.end)<end||Date.parse(input.requested_window.end)>now)fail('invalid_requested_window');
    if(input.pagination_complete!==true)fail('incomplete_provider_pagination');
    if(!Array.isArray(input.captures)||input.captures.length<1||input.captures.length>128||input.captures.some(c=>!c||typeof c.operation!=='string'||!instant(c.received_at)||Date.parse(c.received_at)>now||Date.parse(c.received_at)<end))fail('invalid_source_receipts');
    if(!Array.isArray(input.bars)||input.bars.length>10000)fail('history_bound_exceeded');
    const bars=new Map();previous=-Infinity;let outsideRegular=0;
    for(const b of input.bars) {
      if(!b||!instant(b.t)||![b.o,b.h,b.l,b.c].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>0)||!Number.isFinite(b.v)||b.v<0||b.h<Math.max(b.o,b.c)||b.l>Math.min(b.o,b.c)||b.h<b.l)fail('invalid_bar');
      const at=Date.parse(b.t);
      if(at<=previous)fail('unordered_or_duplicate_bar');previous=at;
      if(at<Date.parse(input.requested_window.start)||at>=Date.parse(input.requested_window.end)||at+300000>Date.parse(input.requested_window.end)||at+300000>now)fail('bar_outside_requested_window');
      if(at%300000!==0|| (b.bar_end!==undefined&&(!instant(b.bar_end)||Date.parse(b.bar_end)!==at+300000)))fail('off_grid_bar');
      // Validate every acquired row, then only consume the selected regular-session grid.
      const session=selected.find(s=>at>=Date.parse(s.open)&&at<Date.parse(s.close));
      if(!session){outsideRegular++;continue;}
      bars.set(at,{t:new Date(at).toISOString(),o:b.o,h:b.h,l:b.l,c:b.c,v:b.v});
    }
    const measurements=[],used=[];
    for(const s of selected) {
      let rv=0,prevClose=null;
      for(let at=Date.parse(s.open);at<Date.parse(s.close);at+=300000) {
        const b=bars.get(at);if(!b)fail('missing_regular_session_slot');
        const ret=Math.log(b.c/(prevClose??b.o));prevClose=b.c;rv+=ret*ret;used.push(b);
      }
      if(!Number.isFinite(rv)||rv<=0)fail('nonpositive_or_nonfinite_session_variance');
      measurements.push({...s,variance:rv});
    }
    const mean = n => measurements.slice(-n).reduce((sum,s)=>sum+s.variance,0)/n;
    const features={log_rv_1:Math.log(mean(1)),log_rv_5:Math.log(mean(5)),log_rv_22:Math.log(mean(22)),log_rv_baseline:Math.log(mean(22))};
    const calculator=evaluateForecastEngine('FE08',features);if(calculator.status!=='research_only_score')fail('calculator_abstained');
    const age=(now-end)/1000, fresh=age<=FE08_RV_POLICY.freshness_max_age_seconds;
    return {...out,status:'computed',symbol:input.symbol,evaluation_at:input.evaluation_at,features,calculator_result:calculator,
      calculator_provenance_note:'Unchanged numeric evaluator retains its manual-wrapper metadata. The outer envelope, not that evaluator, establishes this provider-capture feature path. No statistical or licensed-rights attestation follows.',
      source:{provider:FE08_RV_POLICY.provider,feed:'iex',adjustment:'raw',timeframe:'5Min',requested_window:input.requested_window,calendar:{received_at:cal.received_at,requested_range:range,selected_sessions:selected,complete_provider_response:true},captures:input.captures,
        pagination_complete:true,selected_bars_sha256:hash(used),source_policy_fingerprint:hash({policy_sha256:FE08_RV_POLICY_SHA256,provider:FE08_RV_POLICY.provider,feed:'iex',adjustment:'raw',timeframe:'5Min'}),
        historical_availability:'unknown; source observations were acquired at the listed receipts, not known available at past decisions',provider_revisions_possible:true,atomic_snapshot:false,calendar_omissions_independently_verified:false,rights_attestation:null,quality_score:null},
      measurements,coverage:{required_sessions:22,complete_sessions:22,expected_regular_bars:selected.reduce((n,s)=>n+s.expected_bars,0),used_regular_bars:used.length,received_bars:input.bars.length,outside_selected_regular_sessions_excluded:outsideRegular,missing_intervals_filled:false},
      freshness:{age_evaluated_at:input.evaluation_at,source_as_of:selected.at(-1).close,source_age_seconds:age,max_age_seconds:FE08_RV_POLICY.freshness_max_age_seconds,status:fresh?'within_declared_age':'stale',current_source_age_acceptable:fresh},
      warnings:['NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER','FIXED_COEFFICIENTS_NOT_FITTED','IEX_SINGLE_EXCHANGE_NOT_CONSOLIDATED','PROVIDER_REVISIONS_POSSIBLE','NO_HISTORICAL_POINT_IN_TIME_ASSERTION','NO_CALIBRATION_OR_PROFITABILITY_CLAIM',...(!fresh?['STALE_SOURCE_RESEARCH_DIAGNOSTIC_ONLY']:[])]};
  } catch(error) {return {...out,status:'unavailable',error:error?.message||'feature_construction_failed'};}
}
