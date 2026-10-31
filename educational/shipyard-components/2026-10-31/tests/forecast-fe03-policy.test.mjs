import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {buildFE03SourceForecast,computeFE03BreakoutMeasurements,FE03_BREAKOUT_POLICY,FE03_BREAKOUT_POLICY_SHA256} from '../research/forecast-features/fe03-breakout-v1.mjs';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
import {fixture,boundary} from './fixtures/fe03-synthetic.mjs';

const close=(actual,expected,tolerance=1e-11)=>assert.ok(Math.abs(actual-expected)<=tolerance*Math.max(1,Math.abs(expected)),`${actual} != ${expected}`);
const digest=value=>createHash('sha256').update(value).digest('hex');
const build=input=>buildFE03SourceForecast(input);
function refreshHistoryReceipt(f){f.captures[0].provider_rows=f.bars.length;f.captures[0].response_sha256=digest(JSON.stringify({symbol:f.symbol,bars:f.bars,next_page_token:null}));}
function refreshCalendarReceipt(f){
 const payload=f.calendar.sessions.map(session=>({date:session.date,open:'09:30',close:session.close===boundary(session.date,'13:00')?'13:00':'16:00'}));
 f.calendar_capture.response_sha256=digest(JSON.stringify(payload));
}

function manual(rows){
 const t=rows.length-1;
 const level=u=>Math.max(...rows.slice(u-20,u).map(row=>row.h));
 const start=u=>u>=21&&rows[u].c>level(u)&&rows[u-1].c<=Math.max(...rows.slice(u-21,u-1).map(row=>row.h));
 const candidate=[...Array.from({length:6},(_,i)=>t-5+i)].filter(start).at(-1)??null;
 const candidateId=candidate===null?null:`SPY:${rows[candidate].date}`;
 const mature=[];
 for(let u=21;u<=t-5;u++)if(start(u)&&`SPY:${rows[u].date}`!==candidateId)mature.push(u);
 const failures=mature.filter(u=>rows.slice(u+1,u+6).some(row=>row.c<level(u)));
 const history={matured_episode_count:mature.length,false_break_count:failures.length,
  candidate_episode_excluded:candidate!==null&&candidate<=t-5&&start(candidate)};
 if(candidate===null)return {status:'no_setup',history};
 const frozen=level(candidate),post=rows.slice(candidate+1,t+1);
 if(rows[t].c<frozen)return {status:'level_invalidated',history};
 if(post.length<3)return {status:'acceptance_not_mature',history};
 if(mature.length<20)return {status:'insufficient_mature_episode_sample',history};
 const d=u=>Math.log(rows[u].c/level(u));
 const distPrior=Array.from({length:252},(_,i)=>d(candidate-252+i));
 const dMean=distPrior.reduce((sum,value)=>sum+value,0)/252;
 const dSd=Math.sqrt(distPrior.reduce((sum,value)=>sum+(value-dMean)**2,0)/252);
 const v=u=>Math.log1p(rows[u].v),vPrior=Array.from({length:20},(_,i)=>v(candidate-20+i));
 const vMean=vPrior.reduce((sum,value)=>sum+value,0)/20;
 const vSd=Math.sqrt(vPrior.reduce((sum,value)=>sum+(value-vMean)**2,0)/20);
 const features={break_distance_z:(d(candidate)-dMean)/dSd,acceptance:post.filter(row=>row.c>=frozen).length/post.length,
  volume_surprise_z:(v(candidate)-vMean)/vSd,false_break_rate:failures.length/mature.length};
 return {status:'computed',features,history,candidate,acceptance_numerator:post.filter(row=>row.c>=frozen).length,acceptance_denominator:post.length};
}

test('FE03 is an explicitly NEW policy on unchanged original scorer bytes',()=>{
 const input=fixture(),r=build(input),scorer=readFileSync(new URL('../dist/forecast-engines.mjs',import.meta.url),'utf8').replace(/\r\n/g,'\n');
 const manifest=JSON.parse(readFileSync(new URL('../research/forecast-features/fe03-manifest.json',import.meta.url),'utf8'));
 assert.equal(r.status,'computed');assert.equal(r.engine_id,'FE03');assert.equal(r.feature_origin,'provider_capture_new_policy');
 assert.equal(FE03_BREAKOUT_POLICY_SHA256,digest(JSON.stringify(FE03_BREAKOUT_POLICY)));
 assert.equal(manifest.schema,'SHIPYARD_FE03_SOURCE_POLICY_MANIFEST_V1');assert.equal(manifest.base_source_commit,'f45c8c8606ca86df479676baf238fa373d849aa5');
 assert.equal(manifest.policy_id,FE03_BREAKOUT_POLICY.id);assert.equal(manifest.policy_sha256,FE03_BREAKOUT_POLICY_SHA256);assert.deepEqual(manifest.policy,FE03_BREAKOUT_POLICY);
 for(const [path,expected]of Object.entries(manifest.source_sha256))assert.equal(digest(readFileSync(new URL('../'+path,import.meta.url),'utf8').replace(/\r\n/g,'\n')),expected,path);
 assert.deepEqual(manifest.original_catalog_contract.inputs.map(({name,unit,value_range})=>({name,unit,value_range})),[
  {name:'break_distance_z',unit:'z',value_range:null},{name:'acceptance',unit:'ratio',value_range:[0,1]},
  {name:'volume_surprise_z',unit:'z',value_range:null},{name:'false_break_rate',unit:'ratio',value_range:[0,1]}]);
 assert.equal(manifest.original_catalog_contract.target_unit,'forward_return_fraction');assert.equal(manifest.original_catalog_contract.horizon,'1-5 sessions');
 assert.equal(digest(scorer),'5d9f555d548e0e96df90bbde4b61b3daf32364ce869d3a4bef61ba58a7d6317e');
 assert.deepEqual(r.calculator_result,evaluateForecastEngine('FE03',r.features));
 assert.deepEqual(r.calculator_result.source,{repository:'__UPSTREAM_REPOSITORY_URL__',commit:'f88c874656857841ba1d52c988b8210095949608',path:'research/forecast_engines'});
 assert.equal(r.restrictions.decision_eligible,false);assert.equal(r.restrictions.order_submission_enabled,false);
 assert.equal(r.coverage.required_sessions,505);assert.equal(r.coverage.complete_sessions,505);assert.equal(r.coverage.trigger_date_slots,479);
 assert.equal(r.freshness.original_catalog_max_age_seconds,172800);assert.equal(r.freshness.original_catalog_age_acceptable,true);
 assert.equal(r.episode.cutoff_session,r.freshness.source_session_date);
 assert.equal(r.forecast_target.horizon_anchor_session,r.freshness.source_session_date);
 assert.equal(r.forecast_target.horizon_anchor_at,r.freshness.source_as_of);
 assert.match(r.warnings.join(' '),/NEW_FEATURE_POLICY_NOT_RECOVERED_ORIGINAL_BUILDER/);
});

test('independent manual scalar oracle verifies causal level, all post-cross closes, z windows and matured sample',()=>{
 const f=fixture({breachAndReclaim:true}),r=build(f),expected=manual(f._rows);
 assert.equal(r.status,expected.status);assert.equal(r.history.matured_episode_count,expected.history.matured_episode_count);
 assert.equal(r.false_break.denominator,expected.history.matured_episode_count);assert.equal(r.false_break.numerator,expected.history.false_break_count);
 assert.equal(r.episode.acceptance_numerator,expected.acceptance_numerator);assert.equal(r.episode.acceptance_denominator,expected.acceptance_denominator);
 for(const key of Object.keys(expected.features))close(r.features[key],expected.features[key]);
 assert.equal(r.episode.any_breach,true);assert.equal(r.episode.reclaimed_after_breach,true);assert.equal(r.episode.acceptance_denominator,3);
 assert.equal(r.episode.event_source_as_of,boundary(r.episode.episode_session,'16:00'));
 assert.equal(r.episode.acceptance_source_as_of,r.freshness.source_as_of);
 assert.equal(r.freshness.source_session_date,f._rows.at(-1).date);
});

test('Python reference oracle agrees without importing the JS builder',()=>{
 for(const options of [{},{candidateAge:4},{candidateAge:5},{candidateAge:2},{breachAndReclaim:true}]){
  const f=fixture(options),js=computeFE03BreakoutMeasurements(f._rows,'SPY'),py=JSON.parse(execFileSync('python3',['research/forecast-features/fe03_breakout_v1.py'],
    {input:JSON.stringify(f._rows),encoding:'utf8'}));
  assert.equal(js.status,py.status);assert.equal(js.history.matured_episode_count,py.history.matured_episode_count);
  assert.equal(js.history.false_break_count,py.history.false_break_count);assert.equal(js.history.candidate_episode_excluded,py.history.candidate_episode_excluded);
  if(js.status==='computed')for(const key of Object.keys(js.features))close(js.features[key],py.features[key]);
 }
});

test('candidate at t-5 is explicitly removed by episode ID even though its outcome just matured',()=>{
 const r=build(fixture({candidateAge:5}));assert.equal(r.status,'computed');
 assert.equal(r.episode.episode_index,499);assert.equal(r.history.candidate_episode_excluded,true);
 assert.equal(r.history.candidate_episode_excluded_count,1);assert.equal(r.history.candidate_episode_excluded_id,r.episode.episode_id);
 assert.equal(r.history.matured_episode_count_before_candidate_exclusion,r.history.matured_episode_count+1);
 assert.equal(r.false_break.denominator,r.history.matured_episode_count);assert.equal(r.false_break.candidate_episode_excluded,true);
 assert.equal(r.false_break.numerator,r.history.false_break_count);assert.equal(r.false_break.rate,r.features.false_break_rate);
 assert.equal(r.false_break.outcome_window_sessions,5);assert.equal(r.false_break.statistical_independence_claim,false);
});

test('strict breakout/failure and inclusive acceptance/current-level boundaries are consistent',()=>{
 const equalBreak=fixture(),u=equalBreak._candidate_index,level=Math.max(...equalBreak._rows.slice(u-20,u).map(row=>row.h));
 equalBreak._rows[u].c=level;equalBreak.bars[u].c=level;refreshHistoryReceipt(equalBreak);
 assert.equal(build(equalBreak).status,'no_setup','a close equal to the level is not a strict breakout');

 const crossing=fixture(),crossingU=crossing._candidate_index,priorLevel=Math.max(...crossing._rows.slice(crossingU-21,crossingU-1).map(row=>row.h));
 crossing._rows[crossingU-1].o=priorLevel;crossing._rows[crossingU-1].h=Math.max(crossing._rows[crossingU-1].h,priorLevel);crossing._rows[crossingU-1].c=priorLevel;
 Object.assign(crossing.bars[crossingU-1],{o:crossing._rows[crossingU-1].o,h:crossing._rows[crossingU-1].h,c:priorLevel});refreshHistoryReceipt(crossing);
 assert.equal(build(crossing).episode.episode_id,'SPY:'+crossing._rows[crossingU].date,'previous close equal to prior range remains a valid crossing');

 const accepted=fixture(),candidate=accepted._candidate_index,frozen=Math.max(...accepted._rows.slice(candidate-20,candidate).map(row=>row.h));
 for(let index=candidate+1;index<accepted._rows.length;index++){
  accepted._rows[index].o=frozen;accepted._rows[index].c=frozen;accepted.bars[index].o=frozen;accepted.bars[index].c=frozen;
 }
 refreshHistoryReceipt(accepted);const acceptedResult=build(accepted);
 assert.equal(acceptedResult.status,'computed');assert.equal(acceptedResult.episode.observed_current_close,frozen);
 assert.equal(acceptedResult.episode.acceptance_numerator,3);assert.equal(acceptedResult.episode.acceptance_denominator,3);
 assert.equal(acceptedResult.features.acceptance,1);assert.equal(acceptedResult.episode.any_breach,false);

 const historical=fixture(),baseline=build(historical);
 const eventLevel=index=>Math.max(...historical._rows.slice(index-20,index).map(row=>row.h));
 const isStart=index=>index>=21&&historical._rows[index].c>eventLevel(index)&&historical._rows[index-1].c<=Math.max(...historical._rows.slice(index-21,index-1).map(row=>row.h));
 const episode=historical._rows.findIndex((row,index)=>isStart(index)&&historical._rows.slice(index+1,index+6).some(next=>next.c<eventLevel(index)));
 assert.notEqual(episode,-1,'synthetic history includes a mature false-break episode');
 const historicalLevel=Math.max(...historical._rows.slice(episode-20,episode).map(row=>row.h));
 for(let index=episode+1;index<=episode+5;index++){
  historical._rows[index].o=historicalLevel;historical._rows[index].h=Math.max(historical._rows[index].h,historicalLevel);
  historical._rows[index].l=Math.min(historical._rows[index].l,historicalLevel);historical._rows[index].c=historicalLevel;
  Object.assign(historical.bars[index],{o:historicalLevel,h:historical._rows[index].h,l:historical._rows[index].l,c:historicalLevel});
 }
 refreshHistoryReceipt(historical);const historicalResult=build(historical);
 assert.equal(historicalResult.status,'computed');assert.equal(historicalResult.false_break.denominator,historicalResult.history.matured_episode_count);
 assert.equal(historicalResult.false_break.numerator,historicalResult.history.false_break_count);
 assert.equal(historicalResult.history.false_break_count,baseline.history.false_break_count-1,'exact-level closes are not labeled failures');
 assert.equal(historicalResult.false_break.false_episode_ids_sha256,historicalResult.history.false_episode_ids_sha256);
});

test('sample floor abstains with exact numerator and denominator and no numeric feature/scorer',()=>{
 const r=build(fixture({matureEpisodes:10}));assert.equal(r.status,'insufficient_mature_episode_sample');
 assert.equal(r.history.matured_episode_count,10);assert.equal(r.history.minimum_required,20);assert.equal(r.history.sample_floor_met,false);
 assert.equal(r.history.false_break_count,6);assert.equal('features' in r,false);assert.equal('calculator_result' in r,false);
 assert.equal(r.restrictions.decision_eligible,false);
});

test('no recent setup, incomplete post-cross acceptance and invalidated current level are distinct no-score statuses',()=>{
 for(const [options,status]of [[{candidate:false},'no_setup'],[{candidateAge:2},'acceptance_not_mature'],[{invalidated:true},'level_invalidated']]){
  const r=build(fixture(options));assert.equal(r.status,status);assert.equal('features' in r,false);assert.equal('calculator_result' in r,false);
 }
 const invalid=build(fixture({invalidated:true}));assert.ok(invalid.episode.observed_current_close<invalid.episode.event_level);
});

test('future-tail invariance: bars and labels after the fixed cutoff cannot change earlier features',()=>{
 const f=fixture(),base=computeFE03BreakoutMeasurements(f._rows,'SPY',504),tail=Array.from({length:5},(_,i)=>({date:`2026-11-${String(2+i).padStart(2,'0')}`,h:10000+i,c:9000+i,v:999999+i}));
 const withFuture=computeFE03BreakoutMeasurements([...f._rows,...tail],'SPY',504);
 assert.deepEqual(withFuture,base);
});

test('normalizer degeneracy abstains without a floor or epsilon',()=>{
 const f=fixture({candidate:false,matureEpisodes:0}),rows=f._rows;
 for(let i=0;i<rows.length;i++)Object.assign(rows[i],{o:99,h:100,l:98,c:99});
 for(let u=21;u<=211;u+=10){
  const level=Math.max(...rows.slice(u-20,u).map(row=>row.h)),value=level*1.02;
  Object.assign(rows[u],{o:value,h:value*1.001,l:level*.99,c:value});
  for(let j=1;j<=5;j++){const close=level*.99;Object.assign(rows[u+j],{o:close,h:close*1.0005,l:close*.99,c:close});}
 }
 const u=501,level=Math.max(...rows.slice(u-20,u).map(row=>row.h)),value=level*1.02;
 Object.assign(rows[u],{o:value,h:value*1.001,l:level*.99,c:value});
 for(let j=1;j<=3;j++){const close=level*1.001;Object.assign(rows[u+j],{o:close,h:close*1.0005,l:level*.98,c:close});}
 for(let i=0;i<rows.length;i++)Object.assign(f.bars[i],{o:rows[i].o,h:rows[i].h,l:rows[i].l,c:rows[i].c,v:rows[i].v});refreshHistoryReceipt(f);
 assert.equal(build(f).error,'degenerate_break_distance_normalizer');
});

test('missing, duplicate, off-grid and malformed OHLCV/session clocks fail closed',()=>{
 const cases=[
  [f=>{f.bars.splice(100,1);f.captures[0].provider_rows--;},'missing_daily_session_bar'],
  [f=>f.bars[100].t=f.bars[99].t,'unordered_or_duplicate_bar'],
  [f=>f.bars[100].t=new Date(Date.parse(f.bars[100].t)+60000).toISOString(),'off_daily_grid_bar'],
  [f=>f.bars[100].h=f.bars[100].c/2,'invalid_bar'],
  [f=>f.bars[100].v=0,'invalid_bar'],
  [f=>f.evaluation_at='not-a-clock','invalid_evaluation_clock'],
  [f=>f.calendar.sessions[100].close=f.calendar.sessions[100].open,'invalid_calendar'],
  [f=>{f.calendar.sessions[100].close=new Date(Date.parse(f.calendar.sessions[100].close)+1000).toISOString();refreshCalendarReceipt(f);},'invalid_calendar'],
  [f=>{const i=f._rows.findIndex((row,index)=>index>0&&new Date(f._rows[index-1].date+'T12:00:00Z').getUTCDay()===5&&new Date(row.date+'T12:00:00Z').getUTCDay()===1);
    const saturday=new Date(Date.parse(f._rows[i-1].date+'T12:00:00Z')+86400000).toISOString().slice(0,10);f.bars[i].t=boundary(saturday,'00:00');},'non_session_bar'],
 ];
 for(const [mutate,error]of cases){const f=fixture();mutate(f);refreshHistoryReceipt(f);assert.equal(build(f).error,error,error);}
});

test('calendar early close and New York DST midnight grid are respected',()=>{
 const f=fixture({earlyClose:true}),r=build(f);assert.equal(r.status,'computed');
 assert.equal(r.freshness.source_as_of,boundary(f.calendar.sessions.at(-1).date,'13:00'));
 assert.ok(f.bars.some(bar=>bar.t.endsWith('T04:00:00.000Z')));assert.ok(f.bars.some(bar=>bar.t.endsWith('T05:00:00.000Z')));
 const winter=f.bars.find(bar=>bar.t.endsWith('T05:00:00.000Z'));winter.t=winter.t.replace('T05:00','T06:00');
 assert.equal(build(f).error,'off_daily_grid_bar');
});

test('stale weekend/holiday age remains diagnostic and never opens decision eligibility',()=>{
 const f=fixture(),today='2026-11-02',session={date:today,open:boundary(today,'09:30'),close:boundary(today,'16:00')};
 f.calendar.sessions.push(session);f.calendar.requested_range.start_date='2024-08-24';f.calendar.requested_range.end_date=today;f.calendar.received_at='2026-11-02T14:59:45.000Z';f.symbol_asof=today;f.evaluation_at='2026-11-02T15:00:00.000Z';
 f.calendar_capture.request_url=f.calendar_capture.request_url.replace(/start=[0-9-]+&end=[0-9-]+$/,`start=2024-08-24&end=${today}`);
 f.calendar_capture.request_started_at='2026-11-02T14:59:40.000Z';f.calendar_capture.http_response_received_at='2026-11-02T14:59:45.000Z';f.calendar_capture.received_at=f.calendar_capture.http_response_received_at;
 f.captures[0].request_started_at='2026-11-02T14:59:50.000Z';f.captures[0].http_response_received_at='2026-11-02T14:59:55.000Z';f.captures[0].received_at=f.captures[0].http_response_received_at;
 const url=new URL(f.captures[0].request_url);url.searchParams.set('asof',today);f.captures[0].request_url=url.toString();
 refreshCalendarReceipt(f);
 const r=build(f);assert.equal(r.status,'computed');assert.equal(r.freshness.source_session_date,'2026-10-30');
 assert.ok(r.freshness.source_age_seconds>172800);assert.equal(r.freshness.original_catalog_age_acceptable,false);
 assert.equal(r.restrictions.decision_eligible,false);assert.equal(r.freshness.decision_eligible,false);
});
