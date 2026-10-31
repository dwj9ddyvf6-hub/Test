// NEW fixed, ETF-only feature policies for FE07 and FE10.
// These transforms are experimental research measurements, not recovered originals.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex,utf8ToBytes} from '@noble/hashes/utils.js';

const hash=value=>bytesToHex(sha256(utf8ToBytes(JSON.stringify(value))));
const fail=code=>{throw Error(code);};
const DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const TIME_FORMAT=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const NY_OFFSET_FORMAT=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',timeZoneName:'longOffset'});
const ISO=/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?Z$/;
const instant=x=>typeof x==='string'&&ISO.test(x)&&! /\.\d{3}\d*[1-9]\d*Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(Date.parse(x)).toISOString().slice(0,10)===x.slice(0,10);
const date=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x+'T00:00:00Z'))&&new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
const nyDate=ms=>DATE_FORMAT.format(new Date(ms));
const isNyMidnight=ms=>TIME_FORMAT.format(new Date(ms))==='00:00:00'&&ms%1000===0;
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
function stats(values,name){
  if(!Array.isArray(values)||!values.length||values.some(x=>!Number.isFinite(x)))fail('nonfinite_'+name);
  const m=mean(values),variance=mean(values.map(x=>(x-m)**2)),sd=Math.sqrt(variance);
  if(!Number.isFinite(m)||!Number.isFinite(sd)||sd<=1e-12)fail('degenerate_'+name+'_normalizer');
  return {mean:m,population_sd:sd,count:values.length,ddof:0};
}
function safe(values,name){if(!values.every(Number.isFinite))fail('nonfinite_'+name);return values;}

export const FE07_LEADLAG_POLICY=Object.freeze({
  id:'FE07_FIXED_ETF_SPY_TO_QQQ_LAG1_V1',version:1,origin:'NEW_FEATURE_POLICY',engine_id:'FE07',
  provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',
  universe:{leader:'SPY',follower:'QQQ',kind:'fixed_two_ETF_pair',expansion_allowed:false},
  symbol_mapping:'Current provider entity mapping asof the current New York acquisition date; not historical point-in-time membership.',
  sessions:505,calendar_lookback_days:800,calendar:'Alpaca US equity official market calendar; America/New_York',completion_delay_ms:900000,
  acquisition:{budget_seconds:25,per_request_timeout_seconds:8,max_pages_per_symbol:2,max_symbols:2,max_rows_per_symbol:1000,max_response_bytes_per_request:524288},
  return_definition:'Daily close-to-close natural log return ln(close[t]/close[t-1]) on split-adjusted, dividend-excluded IEX bars. Complete official session rows are paired by date; no forward fill, pairwise deletion, lag search or universe change.',
  model:'At cutoff t, estimate intercept+OLS beta for follower_return[s+1]=alpha+beta*leader_return[s]+error over exactly252 pairs s=t-252..t-1. The last response is follower return[t], available at cutoff. Candidate leader_return[t] is excluded from fitting and is standardized against the immediately preceding252 leader returns s=t-252..t-1 using population SD. Diagnostic next-return projection alpha+beta*leader_return[t] targets follower return[t+1]; the future follower[t+1] is neither supplied nor read.',
  stability:'Divide the ordered252 training pairs into four chronological disjoint blocks of63. lag_stability is the number of block beta signs matching the full-window beta sign divided by4; negative beta is preserved. Zero/undefined block slopes abstain; this is a descriptive sign-consistency ratio, not a confidence statistic.',
  relationship_r2:'In-sample coefficient of determination on the same252 lagged training pairs with intercept. Raw R2 outside[0,1] by at most1e-12 is clamped as floating-point roundoff; material violations abstain. No future row, per-run lag selection or clipping of signed beta.',
  sample_floor:'Exactly252 complete lagged pairs and four complete63-pair stability blocks; exact-zero predictor/response variance, any exact-zero full/block beta, or population normalization SD<=1e-12 abstains. R2 tolerance is1e-12 and applies only to roundoff. No other epsilon or fallback is substituted.',
  source_age:'Observation age is measured from the latest eligible completed official session close, never from request/receipt time. Original catalog48h input-age acceptability is reported separately. Refuse only when the returned latest eligible close is older than7calendar days.',
  price_basis:'Split-adjusted and dividend-excluded prices, not total returns. Corporate-action continuity and provider revisions are not independently verified.',
  interpretation:'Fixed-pair daily lag proxy for an intraday-to-five-session follower residual target, with a diagnostic one-session alpha+beta*leader_return[t] projection of follower_return[t+1]. It is not a causal effect, validated return forecast, calibrated probability, validated edge, trade instruction or order input.',
  research:'The chosen pair and one-session lag are fixed before calculation. This does not test or assert that SPY leads QQQ. Thin trading, asynchronous venues, market microstructure and common-factor exposure can create apparent lead/lag relationships.',
  quality:'The scalar wrapper is not the full Python FeatureObservation validator. Rights attestation and quality score remain null/unknown; source-policy output is research-only and decision-ineligible.',
});
export const FE07_LEADLAG_POLICY_SHA256=hash(FE07_LEADLAG_POLICY);

export const FE10_REGIME_POLICY=Object.freeze({
  id:'FE10_FIXED_ETF_PROXY_REGIME_V1',version:1,origin:'NEW_FEATURE_POLICY',engine_id:'FE10',
  provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',
  universe:{symbols:['SPY','QQQ','IWM'],kind:'fixed_three_ETF_proxy_panel',expansion_allowed:false,market_population_claim:false},
  symbol_mapping:'Current provider entity mapping asof the current New York acquisition date; not historical point-in-time membership.',
  sessions:505,calendar_lookback_days:800,calendar:'Alpaca US equity official market calendar; America/New_York',completion_delay_ms:900000,
  acquisition:{budget_seconds:25,per_request_timeout_seconds:8,max_pages_per_symbol:2,max_symbols:3,max_rows_per_symbol:1000,max_response_bytes_per_request:524288},
  returns:'Daily close-to-close natural log returns from matched split-adjusted dividend-excluded IEX bars. All three ETFs must have the same complete official session grid; no pairwise deletion or imputation.',
  rolling_window:21,normalization_window:252,panel_history_sessions:505,population_ddof:0,
  vol_of_vol:'For each session s, RV21[s] is the cross-sectional mean of each ETF sum(r[i,j]^2) over its latest21 returns. VOV[s] is population SD of the21 RV21 values ending at s. vol_of_vol_z is current VOV[t] standardized against exactly the prior252 VOV values VOV[t-252..t-1].',
  cross_asset_dispersion:'For each session s, dispersion[s] is population SD across the three per-ETF RV21[s] values. cross_asset_dispersion_z is current dispersion[t] standardized against exactly prior252 dispersion values.',
  correlation_shift:'For each session s, calculate all three Pearson correlations over the same complete21x3 return matrix. correlation[s] is their arithmetic mean. correlation_shift_z is current correlation[t] standardized against exactly prior252 rolling correlation values. Each covariance/correlation matrix is computed from the same observations and checked positive-semidefinite; there is no pairwise deletion.',
  change_point_score:'A bounded two-window volatility-level contrast, not a fitted/likelihood change-point detector: recent is equal-weight panel RV21 on returns[t-20..t]; previous is equal-weight panel RV21 on the immediately preceding disjoint returns[t-41..t-21]. score=abs(recent-previous)/(recent+previous). It is in[0,1]; both zero abstains. Only completed returns through t are used.',
  sample_floor:'252 prior causal scalar observations for each z normalizer,21 matched returns per correlation/RV estimate,3 fixed panel members and exactly505 completed bars per member. Population normalization SD<=1e-12, exact-zero return variance, invalid/non-PSD covariance (relative eigenvalue tolerance1e-10), or zero change-point denominator abstains. No epsilon substitution.',
  source_age:'Observation age is measured from the latest eligible completed official session close, never from request/receipt time. Original catalog48h input-age acceptability is reported separately. Refuse only when the returned latest eligible close is older than7calendar days.',
  price_basis:'Split-adjusted and dividend-excluded prices, not total returns. Corporate-action continuity and provider revisions are not independently verified.',
  interpretation:'Three-ETF proxy panel only; not a broad market or all-asset correlation estimate, not a calibrated change-point probability, forecast or trading permission. Overlapping rolling windows are dependent.',
  quality:'The scalar wrapper is not the full Python FeatureObservation validator. Rights attestation and quality score remain null/unknown; source-policy output is research-only and decision-ineligible.',
});
export const FE10_REGIME_POLICY_SHA256=hash(FE10_REGIME_POLICY);

function ols(x,y,name){
  if(x.length!==y.length||x.length<2)fail('insufficient_'+name+'_pairs');
  const mx=mean(x),my=mean(y),sxx=x.reduce((s,v)=>s+(v-mx)**2,0),syy=y.reduce((s,v)=>s+(v-my)**2,0);
  if(!Number.isFinite(sxx)||sxx<=0||!Number.isFinite(syy)||syy<=0)fail('degenerate_'+name);
  const sxy=x.reduce((s,v,i)=>s+(v-mx)*(y[i]-my),0),beta=sxy/sxx,alpha=my-beta*mx;
  const sse=y.reduce((s,v,i)=>s+(v-alpha-beta*x[i])**2,0),rawR2=1-sse/syy,r2RoundoffTolerance=1e-12;
  if(!Number.isFinite(rawR2)||rawR2 < -r2RoundoffTolerance||rawR2 > 1+r2RoundoffTolerance)fail('invalid_'+name+'_r2');
  const r2=Math.max(0,Math.min(1,rawR2));
  if(![alpha,beta,r2].every(Number.isFinite))fail('nonfinite_'+name);
  return {alpha,beta,r2,observations:x.length,predictor_mean:mx,response_mean:my,predictor_ss:sxx,response_ss:syy,residual_ss:sse};
}

// Pure measurement oracle surface. Inputs are full matched close arrays, never provider data.
export function computeFE07LeadLagMeasurements(leaderCloses,followerCloses,cutoffIndex=Array.isArray(leaderCloses)?leaderCloses.length-1:-1){
  const need=FE07_LEADLAG_POLICY.sessions;
  if(!Array.isArray(leaderCloses)||!Array.isArray(followerCloses)||leaderCloses.length!==followerCloses.length||leaderCloses.length<need
    ||!Number.isInteger(cutoffIndex)||cutoffIndex<need-1||cutoffIndex>=leaderCloses.length
    ||[...leaderCloses.slice(0,cutoffIndex+1),...followerCloses.slice(0,cutoffIndex+1)].some(x=>typeof x!=='number'||!Number.isFinite(x)||x<=0))fail('invalid_leadlag_series');
  leaderCloses=leaderCloses.slice(cutoffIndex-need+1,cutoffIndex+1);followerCloses=followerCloses.slice(cutoffIndex-need+1,cutoffIndex+1);
  const lr=safe(leaderCloses.slice(1).map((p,i)=>Math.log(p/leaderCloses[i])),'leader_returns');
  const fr=safe(followerCloses.slice(1).map((p,i)=>Math.log(p/followerCloses[i])),'follower_returns');
  const t=lr.length-1,from=t-252,to=t-1,x=lr.slice(from,to+1),y=fr.slice(from+1,to+2);
  if(x.length!==252||y.length!==252)fail('insufficient_lag_pairs');
  const fit=ols(x,y,'lag_regression'),prior=lr.slice(t-252,t),normalizer=stats(prior,'leader_return');
  const leaderZ=(lr[t]-normalizer.mean)/normalizer.population_sd;
  const blockFits=[];
  for(let i=0;i<4;i++)blockFits.push(ols(x.slice(i*63,(i+1)*63),y.slice(i*63,(i+1)*63),`stability_block_${i+1}`));
  const sign=Math.sign(fit.beta);if(sign===0)fail('degenerate_lag_beta_sign');
  if(blockFits.some(v=>Math.sign(v.beta)===0))fail('degenerate_stability_block_beta');
  const stable=blockFits.filter(v=>Math.sign(v.beta)===sign).length/4;
  return {features:{leader_return_z:leaderZ,lag_beta:fit.beta,lag_stability:stable,relationship_r2:fit.r2},
    regression:{...fit,training_window_start_return_index:from,training_window_end_predictor_return_index:to,
      response_window_start_return_index:from+1,response_window_end_return_index:t,candidate_return_index:t,
      candidate_next_follower_return_index:t+1,candidate_next_follower_return_projection:fit.alpha+fit.beta*lr[t],
      prior_window_excludes_candidate_predictor:true,candidate_future_response_excluded:true,
      next_forecast_uses_current_leader_return:true,next_follower_response_read:false,
      block_betas:blockFits.map(v=>v.beta),block_sign_matches:blockFits.map(v=>Math.sign(v.beta)===sign),block_observations:63},
    normalization:{leader_return:{current:lr[t],...normalizer,window_start_return_index:t-252,window_end_return_index:t-1,current_excluded:true}},
    measurements:{leader_return_current:lr[t],training_pair_count:252,stability_block_count:4,stability_block_size:63,
      coefficient_sign:sign,negative_beta_preserved:true,lag_choice:'fixed_one_official_session'} };
}

function rv21(returns,end){
  const from=end-20;if(from<0)fail('insufficient_21_session_window');
  return returns.map(series=>series.slice(from,end+1).reduce((s,r)=>s+r*r,0));
}
function covarianceAndCorrelation(window){
  const n=window.length;if(n!==21||window.some(row=>!Array.isArray(row)||row.length!==3||row.some(x=>!Number.isFinite(x))))fail('invalid_correlation_window');
  const columns=[0,1,2].map(j=>window.map(row=>row[j])),means=columns.map(mean);
  const cov=columns.map((x,i)=>columns.map((y,j)=>x.reduce((s,v,k)=>s+(v-means[i])*(y[k]-means[j]),0)/(n-1)));
  if(cov.some((row,i)=>row.some((v,j)=>!Number.isFinite(v)||Math.abs(v-cov[j][i])>1e-12)))fail('invalid_covariance_matrix');
  const scale=Math.max(...cov.map((row,i)=>Math.abs(row[i])));if(!(scale>0))fail('degenerate_correlation_window');
  // Jacobi diagonalization for a symmetric 3x3 covariance; catches numerical PSD violations.
  const a=cov.map(row=>row.slice());
  for(let pass=0;pass<24;pass++){
    let p=0,q=1;if(Math.abs(a[0][2])>Math.abs(a[p][q]))[p,q]=[0,2];if(Math.abs(a[1][2])>Math.abs(a[p][q]))[p,q]=[1,2];
    if(Math.abs(a[p][q])<=1e-14*scale)break;
    const angle=.5*Math.atan2(2*a[p][q],a[q][q]-a[p][p]),c=Math.cos(angle),s=Math.sin(angle),app=c*c*a[p][p]-2*s*c*a[p][q]+s*s*a[q][q],aqq=s*s*a[p][p]+2*s*c*a[p][q]+c*c*a[q][q];
    for(let k=0;k<3;k++)if(k!==p&&k!==q){const akp=c*a[k][p]-s*a[k][q],akq=s*a[k][p]+c*a[k][q];a[k][p]=a[p][k]=akp;a[k][q]=a[q][k]=akq;}
    a[p][p]=app;a[q][q]=aqq;a[p][q]=a[q][p]=0;
  }
  const eigenvalues=[a[0][0],a[1][1],a[2][2]];
  if(Math.min(...eigenvalues)<-1e-10*scale)fail('covariance_not_positive_semidefinite');
  const variances=cov.map((row,i)=>row[i]);if(variances.some(v=>v<=0))fail('degenerate_correlation_window');
  const correlations=[];for(const [i,j] of [[0,1],[0,2],[1,2]])correlations.push(cov[i][j]/Math.sqrt(variances[i]*variances[j]));
  if(correlations.some(r=>!Number.isFinite(r)||r < -1-1e-10||r > 1+1e-10))fail('invalid_correlation_value');
  const boundedCorrelations=correlations.map(r=>Math.max(-1,Math.min(1,r)));
  return {correlations:boundedCorrelations,mean_correlation:mean(boundedCorrelations),covariance:cov,eigenvalues};
}
function standardize(value,prior,name){const s=stats(prior,name);return {z:(value-s.mean)/s.population_sd,normalization:{current:value,...s,current_excluded:true,prior_count:prior.length}};}

export function computeFE10RegimeMeasurements(closesBySymbol,cutoffIndex){
  const symbols=FE10_REGIME_POLICY.universe.symbols,need=FE10_REGIME_POLICY.sessions;
  if(!closesBySymbol||typeof closesBySymbol!=='object'||Array.isArray(closesBySymbol)||Object.keys(closesBySymbol).sort().join(',')!==symbols.slice().sort().join(','))fail('invalid_regime_panel');
  const length=closesBySymbol[symbols[0]]?.length;
  if(!Number.isInteger(cutoffIndex))cutoffIndex=length-1;
  if(!Number.isInteger(length)||length<need||!Number.isInteger(cutoffIndex)||cutoffIndex<need-1||cutoffIndex>=length)fail('invalid_regime_series');
  const clipped={};for(const symbol of symbols){if(!Array.isArray(closesBySymbol[symbol])||closesBySymbol[symbol].length!==length
    ||closesBySymbol[symbol].slice(0,cutoffIndex+1).some(x=>typeof x!=='number'||!Number.isFinite(x)||x<=0))fail('invalid_regime_series');
    clipped[symbol]=closesBySymbol[symbol].slice(cutoffIndex-need+1,cutoffIndex+1);}
  closesBySymbol=clipped;
  const returnsBySymbol=Object.fromEntries(symbols.map(symbol=>[symbol,safe(closesBySymbol[symbol].slice(1).map((p,i)=>Math.log(p/closesBySymbol[symbol][i])),symbol+'_returns')]));
  const returns=Array.from({length:need-1},(_,i)=>symbols.map(symbol=>returnsBySymbol[symbol][i]));
  const end=returns.length-1,rv=Array.from({length:returns.length},(_,i)=>i<20?null:rv21(symbols.map(symbol=>returnsBySymbol[symbol]),i));
  const panelRV=rv.map(v=>v?mean(v):null),dispersion=rv.map(v=>v?Math.sqrt(mean(v.map(x=>(x-mean(v))**2))):null);
  const vov=Array.from({length:returns.length},(_,i)=>i<40?null:Math.sqrt(mean(panelRV.slice(i-20,i+1).map(x=>(x-mean(panelRV.slice(i-20,i+1)))**2))));
  const rho=Array.from({length:returns.length},(_,i)=>i<20?null:covarianceAndCorrelation(returns.slice(i-20,i+1)).mean_correlation);
  const priorFrom=end-252,priorTo=end-1;
  if(priorFrom<0)fail('insufficient_regime_history');
  const vovStd=standardize(vov[end],vov.slice(priorFrom,priorTo+1),'vol_of_vol');
  const dispersionStd=standardize(dispersion[end],dispersion.slice(priorFrom,priorTo+1),'cross_asset_dispersion');
  const corrStd=standardize(rho[end],rho.slice(priorFrom,priorTo+1),'correlation_shift');
  const recent=panelRV[end],previous=panelRV[end-21];
  if(!Number.isFinite(recent)||!Number.isFinite(previous)||recent+previous<=0)fail('degenerate_change_point_window');
  const cp=Math.abs(recent-previous)/(recent+previous);
  if(!Number.isFinite(cp)||cp<0||cp>1)fail('invalid_change_point_score');
  const features={change_point_score:cp,vol_of_vol_z:vovStd.z,cross_asset_dispersion_z:dispersionStd.z,correlation_shift_z:corrStd.z};
  if(Object.values(features).some(x=>!Number.isFinite(x)))fail('nonfinite_regime_feature');
  const currentMatrix=covarianceAndCorrelation(returns.slice(end-20,end+1));
  return {features,measurements:{panel_symbols:symbols,matched_return_rows:returns.length,latest_return_index:end,rolling_window:21,
      vov_current:vov[end],cross_asset_dispersion_current:dispersion[end],mean_pair_correlation_current:rho[end],
      recent_panel_rv21:recent,previous_panel_rv21:previous,change_point_score:cp,
      current_covariance_matrix:currentMatrix.covariance,current_covariance_eigenvalues:currentMatrix.eigenvalues,
      current_pair_correlations:currentMatrix.correlations,normalization:{vol_of_vol:vovStd.normalization,cross_asset_dispersion:dispersionStd.normalization,correlation_shift:corrStd.normalization},
      prior_normalization_start_return_index:priorFrom,prior_normalization_end_return_index:priorTo,prior_window_excludes_current:true,
      pairwise_deletion:false,missing_interval_fill:false,market_population_claim:false,overlapping_windows_dependent:true}};
}

function empty(engine){const policy=engine==='FE07'?FE07_LEADLAG_POLICY:FE10_REGIME_POLICY,policyHash=engine==='FE07'?FE07_LEADLAG_POLICY_SHA256:FE10_REGIME_POLICY_SHA256;
  return {schema:`SHIPYARD_${engine}_SOURCE_FORECAST_V1`,engine_id:engine,feature_origin:'provider_capture_new_policy',feature_policy:policy,feature_policy_sha256:policyHash,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false}};}

function validCapture(receipt,operation,subject,now){
  return !!receipt&&receipt.operation===operation&&receipt.subject===subject&&receipt.http_status===200&&instant(receipt.request_started_at)
    &&instant(receipt.http_response_received_at)&&instant(receipt.received_at)&&Date.parse(receipt.request_started_at)<=Date.parse(receipt.http_response_received_at)
    &&Date.parse(receipt.http_response_received_at)<=Date.parse(receipt.received_at)&&Date.parse(receipt.received_at)<=now
    &&now-Date.parse(receipt.request_started_at)<=25000&&now-Date.parse(receipt.received_at)<=25000
    &&/^[0-9a-f]{64}$/.test(receipt.response_sha256||'')&&receipt.hash_serialization==='UTF-8 re-encoding of decoded response text';
}
function receiptUrl(receipt,symbol,page,input){
  if(receipt?.subject!==symbol)return false;
  let url;try{url=new URL(receipt.request_url);}catch{return false;}
  const w=input.requested_window,keys=page===1?'adjustment,asof,currency,end,feed,limit,sort,start,timeframe':'adjustment,asof,currency,end,feed,limit,page_token,sort,start,timeframe';
  return url.origin==='https://data.alpaca.markets'&&url.pathname===`/v2/stocks/${encodeURIComponent(symbol)}/bars`
    &&[...url.searchParams.keys()].sort().join(',')===keys&&url.searchParams.get('timeframe')==='1Day'
    &&url.searchParams.get('start')===w.start&&url.searchParams.get('end')===new Date(Date.parse(w.end)-1).toISOString()
    &&url.searchParams.get('feed')==='iex'&&url.searchParams.get('adjustment')==='split'&&url.searchParams.get('currency')==='USD'
    &&url.searchParams.get('asof')===input.symbol_asof&&url.searchParams.get('sort')==='asc'&&url.searchParams.get('limit')==='1000'
    &&(page===1?!url.searchParams.has('page_token'):url.searchParams.get('page_token')==='[continuation]')
    &&Number.isInteger(receipt.provider_rows)&&receipt.provider_rows>=0&&receipt.provider_rows<=1000&&typeof receipt.has_next_page==='boolean';
}

function build(engine,input){
  const out=empty(engine);const symbols=engine==='FE07'?['SPY','QQQ']:FE10_REGIME_POLICY.universe.symbols;
  try{
    if(!input||input.engine_id!==engine||input.feed!=='iex'||input.adjustment!=='split'||input.timeframe!=='1Day'||input.currency!=='USD'
      ||input.symbol_asof!==nyDate(Date.parse(input.evaluation_at)))fail('source_identity_mismatch');
    if(!instant(input.evaluation_at))fail('invalid_evaluation_clock');const now=Date.parse(input.evaluation_at);
    const cal=input.calendar,range=cal?.requested_range;
    if(!cal||cal.complete_provider_response!==true||!Array.isArray(cal.sessions)||cal.sessions.length>801||!instant(cal.received_at)||Date.parse(cal.received_at)>now
      ||!date(range?.start_date)||!date(range?.end_date)||range.start_date>range.end_date||range.end_date!==nyDate(now)
      ||Date.parse(range.end_date)-Date.parse(range.start_date)>800*86400000)fail('invalid_calendar_lineage');
    const cc=input.calendar_capture;
    if(!validCapture(cc,'official_calendar','US_EQUITY',now)||cc.received_at!==cal.received_at)fail('invalid_calendar_receipt');
    let cu;try{cu=new URL(cc.request_url);}catch{fail('invalid_calendar_receipt');}
    if(cu.origin!=='https://paper-api.alpaca.markets'||cu.pathname!=='/v2/calendar'||[...cu.searchParams.keys()].sort().join(',')!=='end,start'
      ||cu.searchParams.get('start')!==range.start_date||cu.searchParams.get('end')!==range.end_date)fail('invalid_calendar_receipt');
    const sessions=[];let lastDate='',lastClose=-Infinity;
    for(const s of cal.sessions){
      if(!date(s?.date)||s.date<=lastDate||s.date<range.start_date||s.date>range.end_date||!instant(s.open)||!instant(s.close))fail('invalid_calendar');
      const open=Date.parse(s.open),close=Date.parse(s.close);
      if(close<=open||close-open>390*60000||open<=lastClose||nyDate(open)!==s.date||nyDate(close-1)!==s.date)fail('invalid_calendar');
      lastDate=s.date;lastClose=close;if(close+900000<=now)sessions.push({date:s.date,open:new Date(open).toISOString(),close:new Date(close).toISOString()});
    }
    if(sessions.length<505)fail('insufficient_completed_sessions');const selected=sessions.slice(-505),start=Date.parse(input.requested_window?.start),end=Date.parse(input.requested_window?.end);
    if(!instant(input.requested_window?.start)||!instant(input.requested_window?.end)||!isNyMidnight(start)||nyDate(start)!==selected[0].date
      ||end!==Date.parse(selected.at(-1).close)||input.requested_window.end_exclusive!==true)fail('invalid_requested_window');
    if(Date.parse(cc.request_started_at)<end+900000)fail('invalid_calendar_receipt');
    if(input.pagination_complete!==true)fail('incomplete_provider_pagination');
    const receipts=input.captures,ops=new Set(),allowed=new Set(symbols.flatMap(s=>[`history_${s}_1Day_page_1`,`history_${s}_1Day_page_2`]));
    if(!Array.isArray(receipts)||receipts.length<symbols.length||receipts.length>symbols.length*2||receipts.some(r=>{
      if(!r||!allowed.has(r.operation)||ops.has(r.operation))return true;ops.add(r.operation);
      return !validCapture(r,r.operation,r.subject,now)||Date.parse(r.request_started_at)<end+900000;
    }))fail('invalid_source_receipts');
    if(Date.parse(cc.received_at)>Math.min(...receipts.map(r=>Date.parse(r.request_started_at))))fail('invalid_source_receipts');
    const bars=input.bars_by_symbol;if(!bars||typeof bars!=='object'||Array.isArray(bars)||Object.keys(bars).sort().join(',')!==symbols.slice().sort().join(','))fail('invalid_matched_panel');
    const used={};
    for(const symbol of symbols){
      const first=receipts.filter(r=>r.operation===`history_${symbol}_1Day_page_1`),second=receipts.filter(r=>r.operation===`history_${symbol}_1Day_page_2`);
      if(first.length!==1||second.length>1||!receiptUrl(first[0],symbol,1,input)||first[0].has_next_page!==(second.length===1)
        ||second.length===1&&(!receiptUrl(second[0],symbol,2,input)||second[0].has_next_page||Date.parse(second[0].request_started_at)<Date.parse(first[0].received_at)))fail('invalid_source_receipts');
      if(first[0].provider_rows+(second[0]?.provider_rows||0)!==505)fail('invalid_source_receipts');
      const rows=bars[symbol];if(!Array.isArray(rows)||rows.length!==505||rows.length>1000)fail('history_bound_exceeded');
      const byDate=new Map();let prior=-Infinity;
      for(const bar of rows){
        if(!bar||!instant(bar.t)||![bar.o,bar.h,bar.l,bar.c,bar.v].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>0)
          ||bar.h<Math.max(bar.o,bar.c)||bar.l>Math.min(bar.o,bar.c)||bar.h<bar.l)fail('invalid_bar');
        const at=Date.parse(bar.t),day=nyDate(at);
        if(at<=prior||byDate.has(day))fail('unordered_or_duplicate_bar');prior=at;
        if(at<start||at>=end)fail('bar_outside_requested_window');if(!isNyMidnight(at))fail('off_daily_grid_bar');byDate.set(day,bar);
      }
      used[symbol]=selected.map(s=>{const bar=byDate.get(s.date);if(!bar)fail(`missing_${symbol.toLowerCase()}_session_bar`);return {t:new Date(Date.parse(bar.t)).toISOString(),o:bar.o,h:bar.h,l:bar.l,c:bar.c,v:bar.v};});
      if(used[symbol].length!==505)fail('incomplete_session_series');
    }
    for(let i=0;i<505;i++)for(const symbol of symbols)if(used[symbol][i].t!==used[symbols[0]][i].t)fail('paired_session_mismatch');
    const latestAge=(now-end)/1000;if(!Number.isFinite(latestAge)||latestAge<0)fail('invalid_source_age');
    if(latestAge>604800)fail('extended_closure_or_calendar_staleness_unverified');
    let computed;
    if(engine==='FE07')computed=computeFE07LeadLagMeasurements(used.SPY.map(x=>x.c),used.QQQ.map(x=>x.c));
    else computed=computeFE10RegimeMeasurements(Object.fromEntries(symbols.map(s=>[s,used[s].map(x=>x.c)])));
    const calculator=evaluateForecastEngine(engine,computed.features);if(calculator.status!=='research_only_score')fail('calculator_abstained');
    const sourceAsOf=selected.at(-1).close,age=(now-Date.parse(sourceAsOf))/1000;
    const grid={columns:['date','open','close'],rows:selected.map(s=>[s.date,s.open,s.close])};
    const source={provider:'Alpaca Market Data',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_asof:input.symbol_asof,
      universe:engine==='FE07'?{leader:'SPY',follower:'QQQ',fixed:true}:{symbols,kind:'fixed_three_ETF_proxy_panel',fixed:true,market_population_claim:false},
      requested_window:input.requested_window,calendar:{received_at:cal.received_at,capture:cc,requested_range:range,selected_session_grid:grid,
        selected_calendar_sha256:hash(selected),complete_provider_response:true},captures:receipts,pagination_complete:true,
      selected_bars_sha256:hash(used),series_sha256:Object.fromEntries(symbols.map(s=>[s,hash(used[s])])),
      source_policy_fingerprint:hash({policy_sha256:out.feature_policy_sha256,symbols,feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD'}),
      historical_availability:'unknown; current captures do not establish availability at historical decisions',price_basis:'split_adjusted_dividend_excluded',provider_revisions_possible:true,
      atomic_snapshot:false,calendar_omissions_independently_verified:false,corporate_actions_independently_verified:false,
      historical_symbol_continuity_independently_verified:false,rights_attestation:null,quality_score:null,
      ...(engine==='FE07'?{regression:computed.regression,normalization:computed.normalization,measurements:computed.measurements}:{measurements:computed.measurements})};
    return {...out,status:'computed',evaluation_at:input.evaluation_at,features:computed.features,calculator_result:calculator,
      calculator_provenance_note:'The unchanged fixed scorer is applied to a separate NEW feature policy. This is not a recovered canonical builder, fitted forecast, or validated trade signal.',source,
      coverage:{required_sessions:505,complete_sessions:505,used_daily_bars_per_symbol:505,per_symbol:Object.fromEntries(symbols.map(s=>[s,505])),matched_session_grid:true,
        universe_symbols:symbols,missing_intervals_filled:false,pairwise_deletion:false},
      freshness:{basis:'latest_completed_session_in_current_official_provider_calendar',status:age<=172800?'within_declared_age':'original_catalog_age_exceeded_research_only',
        age_evaluated_at:input.evaluation_at,source_as_of:sourceAsOf,source_age_seconds:age,source_session_date:selected.at(-1).date,
        expected_completed_session_date:selected.at(-1).date,source_session_matches_calendar:true,current_calendar_request_through_date:range.end_date,
        original_catalog_max_age_seconds:172800,original_catalog_age_acceptable:age<=172800,original_catalog_age_status:age<=172800?'within_declared_age':'exceeds_original_48h',
        calendar_session_age_guard_seconds:604800,research_display_eligible:true,decision_eligible:false},
      warnings:['NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER','FIXED_COEFFICIENTS_NOT_FITTED','IEX_SINGLE_EXCHANGE_NOT_CONSOLIDATED',
        'DIVIDEND_EXCLUDED_NOT_TOTAL_RETURN','PROVIDER_REVISIONS_POSSIBLE','NO_HISTORICAL_POINT_IN_TIME_ASSERTION','NO_CALIBRATION_OR_PROFITABILITY_CLAIM',
        'NOT_DECISION_ELIGIBLE','FIXED_PROXY_PANEL_NOT_MARKET_POPULATION',...(age>172800?['ORIGINAL_CATALOG_48H_AGE_EXCEEDED_RESEARCH_ONLY']:[])]};
  }catch(error){return {...out,status:'unavailable',error:error?.message||'feature_construction_failed'};}
}
export const buildFE07SourceForecast=input=>build('FE07',input);
export const buildFE10SourceForecast=input=>build('FE10',input);
