import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {buildFE07SourceForecast,buildFE10SourceForecast,computeFE07LeadLagMeasurements,computeFE10RegimeMeasurements,
  FE07_LEADLAG_POLICY,FE07_LEADLAG_POLICY_SHA256,FE10_REGIME_POLICY,FE10_REGIME_POLICY_SHA256} from '../research/forecast-features/fe07-fe10-v1.mjs';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
import {prices,sourceFixture} from './fixtures/fe07-fe10-synthetic.mjs';

const close=(a,b,tol=5e-10)=>assert.ok(Math.abs(a-b)<=tol*Math.max(Math.abs(b),1e-12),`${a} != ${b}`);
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const python=String.raw`
import json, math, statistics, sys
d=json.load(sys.stdin)
def mean(x): return sum(x)/len(x)
def popsd(x):
 m=mean(x); return math.sqrt(mean([(v-m)**2 for v in x]))
def corr(x,y):
 mx,my=mean(x),mean(y); return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
def fit(x,y):
 mx,my=mean(x),mean(y); sxx=sum((v-mx)**2 for v in x); beta=sum((v-mx)*(y[i]-my) for i,v in enumerate(x))/sxx; alpha=my-beta*mx
 sse=sum((v-alpha-beta*x[i])**2 for i,v in enumerate(y)); syy=sum((v-my)**2 for v in y); raw=1-sse/syy
 if not math.isfinite(raw) or raw < -1e-12 or raw > 1+1e-12: raise ValueError('material_r2_violation')
 return alpha,beta,min(1,max(0,raw))
if d['engine']=='FE07':
 leader=[math.log(d['closes']['SPY'][i+1]/d['closes']['SPY'][i]) for i in range(len(d['closes']['SPY'])-1)]
 follower=[math.log(d['closes']['QQQ'][i+1]/d['closes']['QQQ'][i]) for i in range(len(d['closes']['QQQ'])-1)]
 t=len(leader)-1; x=leader[t-252:t]; y=follower[t-251:t+1]; alpha,beta,r2=fit(x,y); z=(leader[t]-mean(leader[t-252:t]))/popsd(leader[t-252:t])
 blocks=[fit(x[i*63:(i+1)*63],y[i*63:(i+1)*63])[1] for i in range(4)]; stability=sum(math.copysign(1,b)==math.copysign(1,beta) for b in blocks)/4
 out={'features':{'leader_return_z':z,'lag_beta':beta,'lag_stability':stability,'relationship_r2':r2},'alpha':alpha,'blocks':blocks,'candidate_next_follower_return_projection':alpha+beta*leader[t]}
else:
 symbols=['SPY','QQQ','IWM']; ret={s:[math.log(d['closes'][s][i+1]/d['closes'][s][i]) for i in range(len(d['closes'][s])-1)] for s in symbols}; n=len(ret['SPY'])
 rv=[]; disp=[]; rho=[]; vov=[]
 for end in range(n):
  if end<20: rv.append(None);disp.append(None)
  else:
   vals=[sum(ret[s][end-20:end+1][j]**2 for j in range(21)) for s in symbols];rv.append(mean(vals));disp.append(popsd(vals))
  if end<20: rho.append(None)
  else:
   win={s:ret[s][end-20:end+1] for s in symbols};rho.append(mean([corr(win['SPY'],win['QQQ']),corr(win['SPY'],win['IWM']),corr(win['QQQ'],win['IWM'])]))
  if end<40: vov.append(None)
  else:vov.append(popsd(rv[end-20:end+1]))
 end=n-1; start=end-252; stop=end
 def zseries(values): return (values[end]-mean(values[start:stop]))/popsd(values[start:stop])
 recent,previous=rv[end],rv[end-21]; cp=abs(recent-previous)/(recent+previous)
 out={'features':{'change_point_score':cp,'vol_of_vol_z':zseries(vov),'cross_asset_dispersion_z':zseries(disp),'correlation_shift_z':zseries(rho)}}
print(json.dumps(out,separators=(',',':')))
`;
function oracle(engine,closes){return JSON.parse(execFileSync('python3',['-c',python],{input:JSON.stringify({engine,closes}),encoding:'utf8'}));}
function vector(closeArrays){const rows=Object.values(closeArrays);return rows.map(a=>a.length);}

test('FE07 and FE10 policies are explicit NEW contracts with stable hashes and fixed universes',()=>{
  assert.equal(FE07_LEADLAG_POLICY_SHA256,sha(FE07_LEADLAG_POLICY));assert.equal(FE10_REGIME_POLICY_SHA256,sha(FE10_REGIME_POLICY));
  assert.equal(FE07_LEADLAG_POLICY.origin,'NEW_FEATURE_POLICY');assert.deepEqual(FE07_LEADLAG_POLICY.universe,{leader:'SPY',follower:'QQQ',kind:'fixed_two_ETF_pair',expansion_allowed:false});
  assert.deepEqual(FE10_REGIME_POLICY.universe.symbols,['SPY','QQQ','IWM']);assert.equal(FE10_REGIME_POLICY.universe.market_population_claim,false);
  assert.match(FE07_LEADLAG_POLICY.model,/targets follower return\[t\+1\]/);assert.match(FE07_LEADLAG_POLICY.relationship_r2,/1e-12/);
});

test('FE07 fixed-pair OLS and FE10 panel transforms match an independent Python oracle',()=>{
  const closeSets=prices(),f7=computeFE07LeadLagMeasurements(closeSets.SPY,closeSets.QQQ),py7=oracle('FE07',{SPY:closeSets.SPY,QQQ:closeSets.QQQ});
  for(const k of Object.keys(f7.features))close(f7.features[k],py7.features[k]);close(f7.regression.alpha,py7.alpha);
  close(f7.regression.candidate_next_follower_return_projection,py7.candidate_next_follower_return_projection);
  assert.equal(f7.regression.candidate_next_follower_return_index,f7.regression.response_window_end_return_index+1);
  assert.equal(f7.regression.next_forecast_uses_current_leader_return,true);assert.equal(f7.regression.next_follower_response_read,false);
  assert.ok(f7.features.relationship_r2>=0&&f7.features.relationship_r2<=1);
  assert.equal(f7.regression.observations,252);assert.equal(f7.regression.prior_window_excludes_candidate_predictor,true);
  assert.equal(f7.regression.candidate_future_response_excluded,true);assert.equal(f7.regression.block_observations,63);
  const f10=computeFE10RegimeMeasurements(closeSets),py10=oracle('FE10',closeSets);
  for(const k of Object.keys(f10.features))close(f10.features[k],py10.features[k],2e-8);
  assert.equal(f10.measurements.pairwise_deletion,false);assert.equal(f10.measurements.current_covariance_eigenvalues.length,3);
  assert.ok(Math.min(...f10.measurements.current_covariance_eigenvalues)>=-1e-16);
});

test('future tails do not alter candidate measurements; negative beta is preserved',()=>{
  const p=prices(),base=computeFE07LeadLagMeasurements(p.SPY,p.QQQ),leader=p.SPY.slice(),negative=[1];
  for(let i=1;i<505;i++){const ret=-.9*Math.log(leader[i-1]/leader[Math.max(0,i-2)])+.0007*Math.sin(i*1.37);negative.push(negative.at(-1)*Math.exp(ret));}
  const neg=computeFE07LeadLagMeasurements(leader,negative);assert.ok(neg.features.lag_beta<0);
  const leaderTail=[...p.SPY,NaN],followerTail=[...p.QQQ,Infinity];
  const same=computeFE07LeadLagMeasurements(leaderTail,followerTail,504);assert.deepEqual(same.features,base.features);
  assert.equal(same.regression.candidate_next_follower_return_projection,base.regression.candidate_next_follower_return_projection);
  const changedFuture=[...p.QQQ,p.QQQ[504]*Math.exp(.25)];
  assert.equal(computeFE07LeadLagMeasurements([...p.SPY,p.SPY[504]*Math.exp(-.17)],changedFuture,504).regression.candidate_next_follower_return_projection,base.regression.candidate_next_follower_return_projection);
  const panTail=Object.fromEntries(Object.entries(p).map(([s,a])=>[s,[...a,NaN]]));
  assert.deepEqual(computeFE10RegimeMeasurements(panTail,504).features,computeFE10RegimeMeasurements(p).features);
});

test('source builders require exact complete pair/panel, preserve source age, unchanged scorer and research-only gates',()=>{
  for(const [engine,builder,symbols] of [['FE07',buildFE07SourceForecast,['SPY','QQQ']],['FE10',buildFE10SourceForecast,['SPY','QQQ','IWM']]]){
    const input=sourceFixture(engine),out=builder(input);assert.equal(out.status,'computed',out.error);assert.deepEqual(out.calculator_result,evaluateForecastEngine(engine,out.features));
    assert.deepEqual(out.restrictions,{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false});
    assert.deepEqual(out.coverage.universe_symbols,symbols);assert.equal(out.source.atomic_snapshot,false);assert.equal(out.source.rights_attestation,null);
    assert.equal(out.freshness.source_as_of,out.source.calendar.selected_session_grid.rows.at(-1)[2]);
    assert.ok(out.freshness.source_age_seconds>=0);assert.equal(out.freshness.source_session_matches_calendar,true);
  }
});

test('source mutation, incomplete matching and degeneracy abstain without a calculator result',()=>{
  const input=sourceFixture('FE07');input.feed='sip';let out=buildFE07SourceForecast(input);assert.equal(out.status,'unavailable');assert.equal(out.error,'source_identity_mismatch');
  const broken=sourceFixture('FE10');broken.bars_by_symbol.IWM.pop();out=buildFE10SourceForecast(broken);assert.equal(out.status,'unavailable');assert.equal(out.error,'history_bound_exceeded');
  const misbound=sourceFixture('FE07');misbound.captures.find(x=>x.operation==='history_SPY_1Day_page_1').subject='QQQ';out=buildFE07SourceForecast(misbound);assert.equal(out.status,'unavailable');assert.equal(out.error,'invalid_source_receipts');
  assert.throws(()=>computeFE07LeadLagMeasurements(Array(505).fill(1),Array(505).fill(1)),/degenerate_lag_regression/);
  assert.throws(()=>computeFE10RegimeMeasurements({SPY:Array(505).fill(1),QQQ:Array(505).fill(1),IWM:Array(505).fill(1)}),/degenerate_correlation_window/);
});
