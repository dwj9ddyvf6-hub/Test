// Explicit NEW FE04 source policy. It is not recovered from the original
// engine notes and does not change the original FE04 scorer.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex,utf8ToBytes} from '@noble/hashes/utils.js';

const hash=x=>bytesToHex(sha256(utf8ToBytes(JSON.stringify(x))));
export const FE04_GAP_POLICY=Object.freeze({
  id:'FE04_GAP_FACTOR_OPEN_ACCEPTANCE_V1',version:1,origin:'NEW_FEATURE_POLICY',engine_id:'FE04',
  provider:'Alpaca Market Data',universe:['SPY','QQQ','IWM'],feed:'iex',adjustment:'split',timeframe:'1Min',
  provider_documentation:'https://docs.alpaca.markets/us/reference/stockbarsingle-1',calendar_documentation:'https://docs.alpaca.markets/us/v1.4.2/reference/getcalendar-1',
  calendar:'Provider-returned US-equity sessions, New York time; exact UTC open/close instants, including DST/early close.',
  sessions:62,prior_fit_sessions:60,prior_normalizer_sessions:20,
  gap:'G[d]=ln(first IEX 09:30 RTH minute-bar open[d]/last IEX 15:59-or-close-minus-one-minute RTH bar close[d-1]); IEX open/close proxies, not consolidated official auction prices.',
  fair_gap:'QQQ/IWM: OLS with intercept, asset raw overnight gap on SPY raw overnight gap, fit to prior60 sessions only. SPY: OLS with intercept, SPY gap on QQQ and IWM gaps, fit to same prior60 sessions. Predict fair raw gap at current-date opening; express predicted gap in the exact same prior20 asset gap z scale as gap_z. SPY is never its own zero benchmark.',
  gap_z:'Current raw log gap standardized by arithmetic mean and population SD of exactly the previous20 raw gaps; candidate excluded.',
  open_acceptance:'After the first five completed RTH 1-minute bars only: count closes strictly above prior RTH close for a positive opening gap, or strictly below prior RTH close for a negative opening gap; divide by5. Direction is fixed by first RTH bar open vs prior close. A zero gap abstains.',
  premarket_liquidity:'NEW dollar-volume proxy, not depth or full liquidity: sum(close*volume) across exactly the five 09:25–09:30 ET one-minute bars; divide current proxy by current proxy plus the median of the exact same five-minute window for prior20 sessions using scale-normalized arithmetic to avoid finite-value overflow. Requires all five slots each day and positive prior median.',
  sampling:'Only the RTH first five one-minute bars, the RTH last one-minute bar, and the fixed 09:25–09:30 premarket bars are consumed. Missing required slots abstain; off-grid/duplicate/unordered bars abstain. Other returned RTH bars are not treated as evidence of full sequence completeness.',
  normalization:'Population SD (ddof=0); gap z and fair-gap z share one prior-only asset-gap mean/SD. Regression OLS includes intercept. Zero/near-zero SD or singular factor design abstains; no epsilon/fill.',
  freshness_max_age_seconds:21600,source_age:'Component clocks use the actual feature observations: gap/fair-gap and premarket bars through 09:30 ET; opening acceptance through 09:35 ET. Maximum age is enforced per original input contract, never from retrieval time.',
  limits:{max_symbols:3,max_sessions:62,max_retained_bars_per_symbol:250,max_provider_rows_per_symbol:60000,max_pages_per_symbol:6,max_requests:19,max_response_bytes_per_page:2097152,max_total_response_bytes:39845888,deadline_ms:25000,max_parallel_requests:3},
  price_basis:'Split-adjusted, dividend-excluded IEX bars; cash-dividend ex-date gaps remain in the measured price gap. Provider revisions and complete historical corporate-action availability are not independently verified.',
  interpretation:'Uncalibrated gap-continuation-vs-fade research score. Fixed original FE04 coefficients are unchanged; no probability, profitability, historical point-in-time or trade-admission claim.',
});
export const FE04_GAP_POLICY_SHA256=hash(FE04_GAP_POLICY);
const fail=code=>{throw Error(code);};
const finite=(x)=>typeof x==='number'&&Number.isFinite(x);
const instant=/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/;
const validInstant=x=>typeof x==='string'&&instant.test(x)&&Number.isFinite(Date.parse(x))&&new Date(Date.parse(x)).toISOString().slice(0,10)===x.slice(0,10);
const validDate=x=>typeof x==='string'&&/^\d{4}-\d\d-\d\d$/.test(x)&&Number.isFinite(Date.parse(x+'T00:00:00Z'))&&new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
const etDate=ms=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(ms));
const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
const median=xs=>{const a=[...xs].sort((x,y)=>x-y),m=a.length>>1;return a.length%2?a[m]:a[m-1]/2+a[m]/2;};
function stableRatioOverSum(a,b){if(!finite(a)||a<0||!finite(b)||b<=0)fail('invalid_premarket_liquidity_proxy');const scale=Math.max(a,b),x=a/scale,y=b/scale,result=x/(x+y);if(!finite(result)||result<0||result>1)fail('invalid_premarket_liquidity_proxy');return result;}
function validCalendar(input,now){
 const c=input.calendar,r=c?.requested_range;
 if(!c||c.complete_provider_response!==true||!Array.isArray(c.sessions)||c.sessions.length>801||!validInstant(c.received_at)||Date.parse(c.received_at)>now||!validDate(r?.start_date)||!validDate(r?.end_date)||r.start_date>r.end_date||Date.parse(r.end_date)-Date.parse(r.start_date)>800*86400000)fail('invalid_calendar_lineage');
 const rows=[];let prior='';
 for(const s of c.sessions){
  if(!validDate(s?.date)||s.date<=prior||s.date<r.start_date||s.date>r.end_date||!validInstant(s.open)||!validInstant(s.close))fail('invalid_calendar');
  const o=Date.parse(s.open),cl=Date.parse(s.close),duration=cl-o;
  if(duration<=0||duration>390*60000||duration%60000||etDate(o)!==s.date||etDate(cl-1)!==s.date)fail('invalid_calendar');
  const local=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(o));
  if(local!=='09:30')fail('invalid_regular_open');
  rows.push({date:s.date,open:new Date(o).toISOString(),close:new Date(cl).toISOString()});prior=s.date;
 }
 return rows;
}
function validateCapture(c,now,minStarted){
 if(!c||typeof c.operation!=='string'||!validInstant(c.request_started_at)||!validInstant(c.http_response_received_at)||!validInstant(c.received_at)||Date.parse(c.request_started_at)<minStarted||Date.parse(c.request_started_at)>Date.parse(c.http_response_received_at)||Date.parse(c.http_response_received_at)>Date.parse(c.received_at)||Date.parse(c.received_at)>now||c.http_status!==200||!/^[0-9a-f]{64}$/.test(c.response_sha256||'')||c.hash_serialization!=='UTF-8 re-encoding of decoded response text'||!Number.isInteger(c.response_bytes)||c.response_bytes<=0||c.response_bytes>FE04_GAP_POLICY.limits.max_response_bytes_per_page)fail('invalid_source_receipt');
}
function validateRequestURL(c,expectedPath,expectedParams,expectedOrigin){let url;try{url=new URL(c.request_url);}catch{return false;}if(url.origin!==expectedOrigin||url.pathname!==expectedPath)return false;const entries=[...url.searchParams.entries()],params=Object.fromEntries(entries),keys=Object.keys(params).sort(),expectedKeys=Object.keys(expectedParams).sort();return entries.length===expectedKeys.length&&JSON.stringify(keys)===JSON.stringify(expectedKeys)&&expectedKeys.every(k=>params[k]===expectedParams[k]);}
function validateBars(input,symbol,selected,now){
 const rows=input.bars_by_symbol?.[symbol];if(!Array.isArray(rows)||rows.length>FE04_GAP_POLICY.limits.max_retained_bars_per_symbol)fail('history_bound_exceeded');
 const allowed=new Set();for(let i=0;i<selected.length;i++){const s=selected[i],open=Date.parse(s.open);if(i>0)allowed.add(open);if(i<selected.length-1)allowed.add(Date.parse(s.close)-60000);if(i>=selected.length-21)for(let j=0;j<5;j++)allowed.add(open-300000+j*60000);if(i===selected.length-1)for(let j=1;j<5;j++)allowed.add(open+j*60000);}
 const byTime=new Map();let prior=-Infinity;
 for(const b of rows){
  if(!b||!validInstant(b.t)||![b.o,b.h,b.l,b.c].every(v=>finite(v)&&v>0)||!finite(b.v)||b.v<0||b.h<Math.max(b.o,b.c)||b.l>Math.min(b.o,b.c)||b.h<b.l)fail('invalid_bar');
  const at=Date.parse(b.t);if(at%60000||at<=prior||byTime.has(at))fail('unordered_duplicate_or_off_grid_bar');if(!allowed.has(at)||at+60000>now)fail('bar_outside_selected_feature_windows');prior=at;
  // Reuse immutable provider rows rather than cloning the bounded three-symbol history.
  byTime.set(at,b);
 }
 return {rows,byTime};
}
function sampleFive(byTime,openMs,label){
 const out=[];for(let i=0;i<5;i++){const b=byTime.get(openMs+i*60000);if(!b)fail('missing_'+label+'_slot');out.push(b);}return out;
}
// Page reducer used by a future bounded HTTP adapter: parsed provider pages are
// scanned once; only the exact slots consumed by FE04 survive between pages.
// It cannot prove the source query was complete; callers must verify receipts,
// cursors, byte/deadline limits, and pass their counts to the pure builder.
export function createFE04BoundedBarReducer(sessions,symbol){
 if(!Array.isArray(sessions)||sessions.length!==62||!FE04_GAP_POLICY.universe.includes(symbol))fail('invalid_reducer_scope');
 const wanted=new Set();for(let i=0;i<sessions.length;i++){const s=sessions[i],open=Date.parse(s.open),close=Date.parse(s.close);if(!finite(open)||!finite(close)||close<=open)fail('invalid_reducer_calendar');if(i>0)wanted.add(open);if(i<sessions.length-1)wanted.add(close-60000);if(i>=sessions.length-21)for(let j=0;j<5;j++)wanted.add(open-300000+j*60000);if(i===sessions.length-1)for(let j=1;j<5;j++)wanted.add(open+j*60000);}
 if(wanted.size>FE04_GAP_POLICY.limits.max_retained_bars_per_symbol)fail('selected_slot_budget_exceeded');let pageCount=0,providerRows=0,lastAt=-Infinity,hasMore=false,finished=false;const retained=new Map();
 return Object.freeze({
  pushPage(rows,hasNextPage){if(finished||!Array.isArray(rows)||rows.length<1||rows.length>10000||typeof hasNextPage!=='boolean')fail('invalid_provider_page');if(pageCount>=FE04_GAP_POLICY.limits.max_pages_per_symbol||providerRows+rows.length>FE04_GAP_POLICY.limits.max_provider_rows_per_symbol)fail('provider_row_or_page_budget_exceeded');pageCount++;providerRows+=rows.length;let retainedOnPage=0;for(const b of rows){if(!b||!validInstant(b.t)||![b.o,b.h,b.l,b.c].every(v=>finite(v)&&v>0)||!finite(b.v)||b.v<0||b.h<Math.max(b.o,b.c)||b.l>Math.min(b.o,b.c)||b.h<b.l)fail('invalid_provider_bar');const at=Date.parse(b.t);if(at%60000||at<=lastAt)fail('unordered_or_duplicate_provider_bar');lastAt=at;if(wanted.has(at)){if(retained.has(at))fail('duplicate_selected_provider_bar');retained.set(at,b);retainedOnPage++;if(retained.size>FE04_GAP_POLICY.limits.max_retained_bars_per_symbol)fail('retained_row_budget_exceeded');}}
   hasMore=hasNextPage;if(!hasMore)finished=true;if(pageCount===FE04_GAP_POLICY.limits.max_pages_per_symbol&&hasMore)fail('provider_page_budget_exceeded');return {page:pageCount,provider_rows:rows.length,retained_rows:retainedOnPage,has_next_page:hasMore};},
  finish(){if(!finished||pageCount<1)fail('provider_pagination_incomplete');return {bars:[...retained.values()],provider_rows:providerRows,retained_rows:retained.size,page_count:pageCount,pagination_complete:true};},
 });
}
function rawGap(byTime,session,previous){
 const open=Date.parse(session.open),close=Date.parse(session.close),first=byTime.get(open),lastPrevious=byTime.get(Date.parse(previous.close)-60000);
 if(!first||!lastPrevious)fail('missing_rth_open_or_close_bar');
 return Math.log(first.o/lastPrevious.c);
}
function reg1(x,y){
 if(x.length!==y.length||x.length<3)fail('insufficient_ols_rows');const mx=mean(x),my=mean(y),v=mean(x.map(a=>(a-mx)**2));
 // Log-gap predictor variance is naturally around 1e-6 or smaller. An
 // absolute 1e-12 cutoff would reject ordinary, well-scaled market returns.
 if(!finite(v)||v<=1e-18)fail('singular_ols_design');const beta=mean(x.map((a,i)=>(a-mx)*(y[i]-my)))/v,alpha=my-beta*mx;
 if(!finite(alpha)||!finite(beta))fail('invalid_ols_coefficients');return {alpha,beta};
}
function reg2(x1,x2,y){
 if(x1.length!==y.length||x2.length!==y.length||y.length<5)fail('insufficient_ols_rows');
 // Centered two-factor OLS with intercept, solved by the 2x2 covariance system.
 const m1=mean(x1),m2=mean(x2),my=mean(y),a=mean(x1.map(x=>(x-m1)**2)),d=mean(x2.map(x=>(x-m2)**2)),b=mean(x1.map((x,i)=>(x-m1)*(x2[i]-m2))),c1=mean(x1.map((x,i)=>(x-m1)*(y[i]-my))),c2=mean(x2.map((x,i)=>(x-m2)*(y[i]-my))),det=a*d-b*b;
 // Use a relative collinearity test: predictor units are log returns and the
 // raw covariance determinant is around 1e-12 for an otherwise healthy fit.
 if(!finite(det)||a<=1e-18||d<=1e-18||det<=1e-12*a*d)fail('singular_ols_design');const beta1=(c1*d-c2*b)/det,beta2=(c2*a-c1*b)/det,alpha=my-beta1*m1-beta2*m2;
 if(![alpha,beta1,beta2].every(finite))fail('invalid_ols_coefficients');return {alpha,beta1,beta2};
}
function zscore(value,prior,label){
 const m=mean(prior),sd=Math.sqrt(mean(prior.map(x=>(x-m)**2)));
 if(!finite(value)||!finite(sd)||sd<=1e-12)fail('degenerate_'+label+'_normalizer');const z=(value-m)/sd;if(!finite(z))fail('nonfinite_'+label);return {value,mean:m,population_sd:sd,count:prior.length,z};
}
const base=()=>({schema:'SHIPYARD_FE04_SOURCE_FORECAST_V1',engine_id:'FE04',feature_origin:'provider_capture_new_policy',feature_policy:FE04_GAP_POLICY,feature_policy_sha256:FE04_GAP_POLICY_SHA256,
 restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false}});

export function buildFE04SourceForecast(input){
 const out=base();
 try{
  if(!input||!['SPY','QQQ','IWM'].includes(input.symbol)||input.feed!=='iex'||input.adjustment!=='split'||input.timeframe!=='1Min'||!validInstant(input.evaluation_at))fail('source_identity_mismatch');
  const now=Date.parse(input.evaluation_at),all=validCalendar(input,now),selected=all.slice(-FE04_GAP_POLICY.sessions);
  if(selected.length!==FE04_GAP_POLICY.sessions||selected.at(-1).date!==etDate(now))fail('insufficient_or_misaligned_sessions');
  const current=selected.at(-1),currentOpen=Date.parse(current.open),acceptanceEnd=currentOpen+5*60000;
  if(now<acceptanceEnd)fail('opening_acceptance_incomplete');
  const gapAge=(now-currentOpen)/1000,acceptanceAge=(now-acceptanceEnd)/1000,premarketAge=(now-currentOpen)/1000;
  if(gapAge<0||gapAge>172800||acceptanceAge<0||acceptanceAge>172800||premarketAge<0||premarketAge>FE04_GAP_POLICY.freshness_max_age_seconds)fail('stale_opening_window');
  const age=premarketAge;
  if(!input.pagination_complete||!input.captures||!Array.isArray(input.captures)||input.captures.length<4||input.captures.length>FE04_GAP_POLICY.limits.max_requests)fail('incomplete_source_capture');
  const bySymbol={};for(const symbol of FE04_GAP_POLICY.universe){const checked=validateBars(input,symbol,selected,now);bySymbol[symbol]=checked;}
  const calendarCaptures=input.captures.filter(c=>c.operation==='official_calendar');
  const historyCaptures=input.captures.filter(c=>/^history_1Min_(SPY|QQQ|IWM)_page_\d+$/.test(c?.operation||''));
  if(calendarCaptures.length!==1||historyCaptures.length!==input.captures.length-1)fail('unexpected_source_operation');
  const captureSymbols=new Set(historyCaptures.map(c=>c.operation.match(/^history_1Min_(SPY|QQQ|IWM)_/)[1]));
  if(FE04_GAP_POLICY.universe.some(s=>!captureSymbols.has(s)))fail('missing_symbol_capture');
  for(const symbol of FE04_GAP_POLICY.universe){const pages=historyCaptures.filter(c=>c.operation.startsWith(`history_1Min_${symbol}_`)).sort((a,b)=>Number(a.operation.match(/page_(\d+)/)[1])-Number(b.operation.match(/page_(\d+)/)[1]));const providerRows=pages.reduce((n,c)=>n+(Number.isInteger(c.provider_rows)?c.provider_rows:-1),0),retainedRows=pages.reduce((n,c)=>n+(Number.isInteger(c.retained_rows)?c.retained_rows:-1),0);if(pages.length<1||pages.length>FE04_GAP_POLICY.limits.max_pages_per_symbol||pages.some((c,i)=>Number(c.operation.match(/page_(\d+)/)[1])!==i+1)||providerRows<0||providerRows>FE04_GAP_POLICY.limits.max_provider_rows_per_symbol||retainedRows!==input.bars_by_symbol[symbol].length||pages.some((c,i)=>!Number.isInteger(c.provider_rows)||c.provider_rows<0||c.provider_rows>10000||!Number.isInteger(c.retained_rows)||c.retained_rows<0||c.retained_rows>c.provider_rows||c.has_next_page!==(i<pages.length-1)))fail('invalid_symbol_page_coverage');}
  if(Date.parse(calendarCaptures[0].received_at)!==Date.parse(input.calendar.received_at)||!validateRequestURL(calendarCaptures[0],'/v2/calendar',{start:input.calendar.requested_range.start_date,end:input.calendar.requested_range.end_date},'https://paper-api.alpaca.markets'))fail('calendar_receipt_mismatch');
  const historyStart=new Date(Date.parse(selected[0].close)-60000).toISOString();
  for(const c of input.captures){validateCapture(c,now,acceptanceEnd);if(c.operation==='official_calendar')continue;const m=c.operation.match(/^history_1Min_(SPY|QQQ|IWM)_page_(\d+)$/);if(!m)fail('unexpected_source_operation');const page=Number(m[2]),params={timeframe:'1Min',start:historyStart,end:new Date(acceptanceEnd-1).toISOString(),feed:'iex',adjustment:'split',sort:'asc',limit:'10000',...(page>1?{page_token:'[continuation]'}:{})};if(!validateRequestURL(c,`/v2/stocks/${m[1]}/bars`,params,'https://data.alpaca.markets'))fail('source_request_identity_mismatch');}
  if(input.captures.reduce((sum,c)=>sum+c.response_bytes,0)>FE04_GAP_POLICY.limits.max_total_response_bytes)fail('response_byte_budget_exceeded');
  const gaps={};
  for(const symbol of FE04_GAP_POLICY.universe){
   const map=bySymbol[symbol].byTime,values=[];
   for(let i=1;i<selected.length;i++)values.push(rawGap(map,selected[i],selected[i-1]));
   gaps[symbol]=values;
   // Current opening acceptance: five fully completed one-minute closes versus the prior official RTH close.
   const curIndex=selected.length-1,curPrevClose=map.get(Date.parse(selected[curIndex-1].close)-60000)?.c;
   const openBar=map.get(currentOpen);if(!finite(curPrevClose)||!openBar)fail('missing_current_gap_anchor');
   const gap=values.at(-1);if(Math.abs(gap)<=1e-12)fail('zero_opening_gap');
   const acceptanceBars=sampleFive(map,currentOpen,`opening_acceptance_${symbol}`);
   if(acceptanceBars.some(b=>Date.parse(b.t)+60000>now))fail('opening_acceptance_incomplete');
   const preOpen=currentOpen-5*60000,preBars=sampleFive(map,preOpen,`premarket_${symbol}`);
   const currentPremarketDollarVolume=preBars.reduce((sum,b)=>sum+b.c*b.v,0);
   const preMarketHistory=[];
   for(let i=selected.length-21;i<selected.length-1;i++){
    const bars=sampleFive(map,Date.parse(selected[i].open)-5*60000,`historical_premarket_${symbol}`);
    preMarketHistory.push(bars.reduce((sum,b)=>sum+b.c*b.v,0));
   }
   const historicalMedian=median(preMarketHistory);if(!finite(historicalMedian)||historicalMedian<=0||!finite(currentPremarketDollarVolume)||currentPremarketDollarVolume<0)fail('invalid_premarket_liquidity_proxy');
   const openAcceptance=acceptanceBars.filter(b=>gap>0?b.c>curPrevClose:b.c<curPrevClose).length/5;
   const liquidity=stableRatioOverSum(currentPremarketDollarVolume,historicalMedian);
   bySymbol[symbol]={...bySymbol[symbol],gap_values:values,current_open:openBar.o,current_gap:gap,prior_close:curPrevClose,acceptance:openAcceptance,premarket_dollar_volume:currentPremarketDollarVolume,premarket_prior_median:historicalMedian,premarket_liquidity:liquidity};
  }
  const priorGapBySymbol=Object.fromEntries(FE04_GAP_POLICY.universe.map(s=>[s,gaps[s].slice(-61,-1)]));
  // Candidate is the last gap value; 60 preceding paired observations train the factors.
  const currentGap=Object.fromEntries(FE04_GAP_POLICY.universe.map(s=>[s,gaps[s].at(-1)]));
  const fitStart=priorGapBySymbol.SPY.length-FE04_GAP_POLICY.prior_fit_sessions;
  const fit={};
  for(const s of FE04_GAP_POLICY.universe)if(s!=='SPY')fit[s]=reg1(priorGapBySymbol.SPY.slice(fitStart),priorGapBySymbol[s].slice(fitStart));
  const fitSPY=reg2(priorGapBySymbol.QQQ.slice(fitStart),priorGapBySymbol.IWM.slice(fitStart),priorGapBySymbol.SPY.slice(fitStart));
  const fair={QQQ:fit.QQQ.alpha+fit.QQQ.beta*currentGap.SPY,IWM:fit.IWM.alpha+fit.IWM.beta*currentGap.SPY,SPY:fitSPY.alpha+fitSPY.beta1*currentGap.QQQ+fitSPY.beta2*currentGap.IWM};
  const target=input.symbol,prior20=gaps[target].slice(-21,-1),normalization=zscore(currentGap[target],prior20,'gap'),fairGapZ=(fair[target]-normalization.mean)/normalization.population_sd;
  const features={gap_z:normalization.z,fair_gap_z:fairGapZ,open_acceptance:bySymbol[target].acceptance,premarket_liquidity:bySymbol[target].premarket_liquidity};
  const calculation=evaluateForecastEngine('FE04',features);if(calculation.status!=='research_only_score')fail('calculator_abstained');
  const selectedBars=FE04_GAP_POLICY.universe.flatMap(s=>{const m=bySymbol[s].byTime,used=new Map();for(let i=0;i<selected.length;i++){const session=selected[i],open=Date.parse(session.open);if(i>0){const b=m.get(open);if(b)used.set(open,b);}if(i<selected.length-1){const close=Date.parse(session.close)-60000,b=m.get(close);if(b)used.set(close,b);}if(i>=selected.length-21)for(const b of sampleFive(m,open-300000,'premarket_hash'))used.set(Date.parse(b.t),b);if(i===selected.length-1)for(const b of sampleFive(m,open,'opening_hash'))used.set(Date.parse(b.t),b);}return [...used.values()];});
  return {...out,status:'computed',symbol:target,evaluation_at:input.evaluation_at,features,calculator_result:calculation,
   source:{provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Min',currency:'USD',captures:input.captures,calendar:{received_at:input.calendar.received_at,requested_range:input.calendar.requested_range,selected_sessions:selected,complete_provider_response:true},pagination_complete:true,selected_bars_sha256:hash(selectedBars),source_policy_fingerprint:hash({policy_sha256:FE04_GAP_POLICY_SHA256,provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Min'}),historical_availability:'unknown; current captures do not establish historical point-in-time availability',provider_revisions_possible:true,atomic_snapshot:false,rights_attestation:null,quality_score:null},
   measurements:{split_adjusted_log_gap:currentGap[target],fair_split_adjusted_log_gap:fair[target],gap_normalization:normalization,gap_fit:target==='SPY'?fitSPY:fit[target],gap_fit_sessions:FE04_GAP_POLICY.prior_fit_sessions,premarket_split_adjusted_dollar_volume_proxy:bySymbol[target].premarket_dollar_volume,premarket_prior_median_split_adjusted_dollar_volume_proxy:bySymbol[target].premarket_prior_median,opening_acceptance_threshold:'first-five-bar close strictly beyond prior RTH close in the sign of current split-adjusted gap',acceptance_complete_bars:5,source_as_of:new Date(currentOpen).toISOString()},
   coverage:{required_symbols:3,received_symbols:3,selected_sessions:62,required_current_premarket_slots:5,required_prior_premarket_slots:100,required_acceptance_slots:5,missing_intervals_filled:false},
   freshness:{age_evaluated_at:input.evaluation_at,source_as_of:new Date(currentOpen).toISOString(),source_age_seconds:age,max_age_seconds:FE04_GAP_POLICY.freshness_max_age_seconds,components:{gap_z:{source_as_of:new Date(currentOpen).toISOString(),age_seconds:gapAge,max_age_seconds:172800},fair_gap_z:{source_as_of:new Date(currentOpen).toISOString(),age_seconds:gapAge,max_age_seconds:172800},open_acceptance:{source_as_of:new Date(acceptanceEnd).toISOString(),age_seconds:acceptanceAge,max_age_seconds:172800},premarket_liquidity:{source_as_of:new Date(currentOpen).toISOString(),age_seconds:premarketAge,max_age_seconds:FE04_GAP_POLICY.freshness_max_age_seconds}},status:'within_declared_age',current_source_age_acceptable:true},
   warnings:['NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER','IEX_SINGLE_EXCHANGE_GAP_PROXY_NOT_CONSOLIDATED_OPEN','FAIR_GAP_IS_PRIOR_ONLY_FACTOR_FIT_NOT_FUTURES_FAIR_VALUE','PREMARKET_DOLLAR_VOLUME_IS_NOT_BOOK_LIQUIDITY','FIXED_COEFFICIENTS_NOT_FITTED','CURRENT_CAPTURE_DOES_NOT_ESTABLISH_HISTORICAL_PIT','NO_CALIBRATION_OR_PROFITABILITY_CLAIM','NO_DECISION_OR_ORDER_AUTHORITY']};
 }catch(error){return {...out,status:'unavailable',error:error?.message||'feature_construction_failed'};}
}
