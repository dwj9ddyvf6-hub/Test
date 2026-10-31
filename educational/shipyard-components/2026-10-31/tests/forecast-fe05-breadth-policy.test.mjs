import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {
  FE05_BREADTH_POLICY,FE05_BREADTH_POLICY_SHA256,parseFE05SpyHoldingsXlsx,selectFE05TopIssuerCohort,
  computeFE05BreadthMeasurements,buildFE05SourceForecast,qualifyFE05DateOnlyFreshness,
} from '../research/forecast-features/fe05-spy-breadth-v1.mjs';
import {makeSyntheticHoldings,makeSyntheticXlsx,makeCompressedXlsxBomb,makeCommentCounterfeitXlsx,makeMismatchedCellRowXlsx,makeForeignNamespaceXlsx,makeBadWorkbookRelationshipXlsx,makeNestedCellValueXlsx,makeSyntheticDates,makeSyntheticCloses} from './helpers/fe05-synthetic.mjs';

const hash='a'.repeat(64),holdings=makeSyntheticHoldings(),cohort=selectFE05TopIssuerCohort(holdings),dates=makeSyntheticDates(),
  panelSymbols=[...cohort.symbols,'SPY'],closes=makeSyntheticCloses(panelSymbols,dates),baseline=computeFE05BreadthMeasurements(cohort,closes,dates);
const same=(a,b)=>Math.abs(a-b)<=1e-12;

function sourceFixture({sourceAsOf=holdings.as_of_date,evaluationAt='2026-10-31T13:30:10.000Z',calendarEnd=null}={}){
  const localHoldings={...holdings,as_of_date:sourceAsOf},localCohort=selectFE05TopIssuerCohort(localHoldings),localDates=makeSyntheticDates(505,sourceAsOf),
    localSymbols=[...localCohort.symbols,'SPY'],localCloses=makeSyntheticCloses(localSymbols,localDates),evaluationDate=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(evaluationAt));
  const start=new Date(Date.parse(sourceAsOf+'T00:00:00Z')-800*86400000).toISOString().slice(0,10),now=Date.parse(evaluationAt)-10000;
  const receipt=(operation,subject,offset,extra={})=>({operation,subject,request_started_at:new Date(now+offset).toISOString(),
    http_response_received_at:new Date(now+offset+500).toISOString(),received_at:new Date(now+offset+1000).toISOString(),response_sha256:hash,
    hash_serialization:'raw_response_bytes',http_status:200,...extra});
  const calendarUrl=new URL('https://paper-api.alpaca.markets/v2/calendar');calendarUrl.searchParams.set('start',start);calendarUrl.searchParams.set('end',calendarEnd||evaluationDate);
  const calendar=receipt('official_calendar','US_EQUITY',2000,{request_url:calendarUrl.toString()});
  const holdingsCapture=receipt('spy_holdings_xlsx','SPY',0,{request_url:'https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx'});
  const calendarDates=new Set(localDates);for(let d=new Date(sourceAsOf+'T12:00:00Z');d.toISOString().slice(0,10)<evaluationDate;){d.setUTCDate(d.getUTCDate()+1);const day=d.getUTCDay();if(day!==0&&day!==6)calendarDates.add(d.toISOString().slice(0,10));}
  const calendarSessions=[...calendarDates].sort().filter(d=>d<=evaluationDate).map(date=>({date,open:date+'T13:30:00.000Z',close:date+'T20:00:00.000Z'}));
  const bars=[];let rowsLeft=localSymbols.length*505;
  for(let page=1;rowsLeft>0;page++){
    const count=Math.min(7000,rowsLeft);rowsLeft-=count;const url=new URL('https://data.alpaca.markets/v2/stocks/bars');
    for(const [k,v] of Object.entries({symbols:localSymbols.slice().sort().join(','),timeframe:'1Day',start:localDates[0]+'T05:00:00Z',end:sourceAsOf+'T23:59:59.999Z',feed:'iex',adjustment:'split',currency:'USD',asof:sourceAsOf,sort:'asc',limit:'7000',...(page>1?{page_token:'[continuation]'}:{})}))url.searchParams.set(k,v);
    bars.push(receipt('historical_multi_symbol_1Day_page','FE05_TOP25_ISSUER_COHORT',3000+(page-1)*1500,{request_url:url.toString(),page_index:page,provider_rows:count,has_next_page:rowsLeft>0}));
  }
  const built=buildFE05SourceForecast({holdings:localHoldings,cohort:localCohort,dates:localDates,closesBySymbol:localCloses,calendarCapture:calendar,calendarSessions,holdingsCapture,barsCaptures:bars,evaluationAt});
  return {built,bars,calendar,holdingsCapture,calendarSessions,dates:localDates,cohort:localCohort,closes:localCloses,holdings:localHoldings};
}

test('policy freezes a descriptive current top25-issuer cohort, not full-market/PIT breadth',()=>{
  assert.equal(FE05_BREADTH_POLICY.id,'FE05_SPY_CURRENT_TOP25_ISSUER_BREADTH_V1');
  assert.equal(FE05_BREADTH_POLICY.universe.issuer_count,25);
  assert.equal(FE05_BREADTH_POLICY.universe.performance_selection,false);
  assert.equal(FE05_BREADTH_POLICY.universe.point_in_time_claim,false);
  assert.equal(FE05_BREADTH_POLICY.source.rights_attestation,null);
  assert.equal(FE05_BREADTH_POLICY.freshness_guard.id,'FE05_DATE_ONLY_ASOF_INTERVAL_V2');
  assert.equal(FE05_BREADTH_POLICY.freshness_guard.version,2);
  assert.equal(FE05_BREADTH_POLICY.freshness_guard.max_age_seconds,172800);
  assert.match(FE05_BREADTH_POLICY.freshness_guard.receipt_time_rule,/never substituted/);
  assert.match(FE05_BREADTH_POLICY.identifier_policy.authority,/SEC-filed DTC CUSIP definition/);
  assert.match(FE05_BREADTH_POLICY.provider.symbol_mapping,/no alias\/punctuation rewrite/);
  assert.match(FE05_BREADTH_POLICY.constraints,/not historical index membership/);
  assert.match(FE05_BREADTH_POLICY_SHA256,/^[a-f0-9]{64}$/);
});

test('bounded XLSX parser verifies synthetic source identity, date, full denominator and disclosure boundary',async()=>{
  const parsed=await parseFE05SpyHoldingsXlsx(makeSyntheticXlsx());
  assert.equal(parsed.as_of_date,'2026-10-29');assert.equal(parsed.source_position_count,505);
  assert.ok(Math.abs(parsed.position_weight_total_percent-99.9735)<1e-10);
  assert.ok(Math.abs(parsed.unreconciled_weight_percent-0.0265)<1e-10);
  assert.equal(selectFE05TopIssuerCohort(parsed).issuer_count,25);
  await assert.rejects(parseFE05SpyHoldingsXlsx(new Uint8Array([1,2,3])),/invalid_holdings_xlsx_size/);
});

test('SpreadsheetML namespaces, workbook relationships, and direct cell values are bound structurally',async()=>{
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeForeignNamespaceXlsx()),/invalid_holdings_xml/);
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeBadWorkbookRelationshipXlsx()),/invalid_holdings_xml/);
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeNestedCellValueXlsx()),/invalid_holdings_xml/);
});

test('source roster cardinality and aggregate weights outside the frozen contract abstain',async()=>{
  const corrupted=makeSyntheticHoldings();corrupted.positions[0]={...corrupted.positions[0],weight_percent:corrupted.positions[0].weight_percent-1.5};
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeSyntheticXlsx(corrupted)),/unreconciled_holdings_total/);
  const short=makeSyntheticHoldings();short.positions=short.positions.slice(0,499);
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeSyntheticXlsx(short)),/unexpected_holdings_row_count/);
});

test('XML comments cannot smuggle counterfeit rows and each cell row must match its enclosing source row',async()=>{
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeCommentCounterfeitXlsx()),/invalid_holdings_xml/);
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeMismatchedCellRowXlsx()),/invalid_holdings_cell_address/);
});

test('compressed workbook components are streamed under the declared per-entry memory bound',async()=>{
  await assert.rejects(parseFE05SpyHoldingsXlsx(makeCompressedXlsxBomb()),/invalid_holdings_zip_entry/);
});

test('issuer groups are aggregated before top25 ranking and every selected class line is included',()=>{
  assert.equal(cohort.issuer_count,25);assert.equal(cohort.security_line_count,26);
  assert.equal(cohort.issuers[0].securities.length,2);
  assert.ok(Math.abs(cohort.selected_weight_percent-65)<1e-12);
  assert.equal(cohort.excluded_position_count,2);assert.equal(cohort.source_position_count,505);
  assert.deepEqual(cohort.issuer_keys,selectFE05TopIssuerCohort({...holdings,positions:holdings.positions.slice().reverse()}).issuer_keys);
  const bad={...holdings,positions:holdings.positions.map((p,i)=>i===2?{...p,identifier:'BAD'}:p)};
  assert.throws(()=>selectFE05TopIssuerCohort(bad),/unknown_equity_identifier_format/);
  const duplicate={...holdings,positions:holdings.positions.map((p,i)=>i===2?{...p,ticker:holdings.positions[0].ticker}:p)};
  assert.throws(()=>selectFE05TopIssuerCohort(duplicate),/duplicate_provider_ticker/);
  const changedCash={...holdings,positions:holdings.positions.map(p=>p.identifier==='999USDZ92'?{...p,name:'OTHER'}:p)};
  assert.throws(()=>selectFE05TopIssuerCohort(changedCash),/excluded_holding_identity_mismatch/);
});

test('four pure features match an independent Python oracle and current candidate excludes the future tail',()=>{
  const independent=JSON.parse(execFileSync('python3',['tests/fixtures/fe05_oracle.py'],{input:JSON.stringify({cohort,closes}),encoding:'utf8'}));
  for(const [key,value] of Object.entries(independent))assert.ok(same(baseline.features[key],value),`${key}: JS=${baseline.features[key]} Python=${value}`);
  const tailDates=[...dates,'2026-10-30','2026-11-02','2026-11-03'],tailCloses=Object.fromEntries(panelSymbols.map(symbol=>{
    const values=closes[symbol],last=values.at(-1),next1=last*1.01,next2=last*0.5,next3=last*1.7;return [symbol,[...values,next1,next2,next3]];
  }));
  assert.deepEqual(computeFE05BreadthMeasurements(cohort,tailCloses,tailDates,504).features,baseline.features);
  assert.equal(baseline.measurements.normalization.advance_decline.prior_count,252);
  assert.equal(baseline.measurements.normalization.new_high_low.prior_count,252);
  assert.equal(baseline.measurements.normalization.index_trend.prior_count,252);
  assert.equal(baseline.measurements.normalization.advance_decline.current_excluded,true);
  assert.equal(baseline.measurements.historical_membership_backfill,false);
});

test('all-member and matched-price coverage failures abstain; degenerate normalizers never use fallbacks',()=>{
  const omitted={...closes};delete omitted[cohort.securities[0].symbol];assert.throws(()=>computeFE05BreadthMeasurements(cohort,omitted,dates),/invalid_breadth_price_panel/);
  const short={...closes,[cohort.securities[0].symbol]:closes[cohort.securities[0].symbol].slice(1)};assert.throws(()=>computeFE05BreadthMeasurements(cohort,short,dates),/invalid_breadth_price_series/);
  const rising=Object.fromEntries(panelSymbols.map(symbol=>[symbol,Array.from({length:505},(_,i)=>100*Math.exp(0.001*i))]));
  assert.throws(()=>computeFE05BreadthMeasurements(cohort,rising,dates),/degenerate_advance_decline_normalizer/);
  const oscillating=Object.fromEntries(panelSymbols.map((symbol,j)=>[symbol,Array.from({length:505},(_,i)=>100+((i+j)%2))]));
  assert.throws(()=>computeFE05BreadthMeasurements(cohort,oscillating,dates),/degenerate_new_high_low_normalizer/);
  const varied={...closes,SPY:Array.from({length:505},(_,i)=>100*Math.exp(0.001*i))};
  assert.throws(()=>computeFE05BreadthMeasurements(cohort,varied,dates),/degenerate_index_trend_normalizer/);
});

test('date-only age bounds abstain on the actual Thursday-to-Saturday 48h overlap while keeping metrics diagnostic-only',()=>{
  const {built,bars,cohort:localCohort}=sourceFixture({sourceAsOf:'2026-10-29',evaluationAt:'2026-10-31T15:38:30.000Z'});
  assert.equal(built.status,'abstained');assert.equal(built.abstention_reasons[0],'source_age_interval_overlaps_max_age');
  assert.equal(built.calculator_result,undefined);assert.equal(built.features,undefined);assert.equal(built.restrictions.decision_eligible,false);
  assert.equal(built.diagnostic_only,true);assert.equal(built.diagnostic_only_values.scorer.invoked,false);
  assert.equal(built.freshness.guard_id,'FE05_DATE_ONLY_ASOF_INTERVAL_V2');assert.equal(built.freshness.source_time_unknown,true);
  assert.equal(built.freshness.source_age_seconds,null);assert.equal(built.freshness.source_age_bounds_seconds.lower_bound,128310);
  assert.equal(built.freshness.source_age_bounds_seconds.upper_bound,214710);assert.equal(built.freshness.source_age_max_age_acceptable,null);
  assert.equal(built.freshness.current_session_lag_sessions,null);assert.equal(built.freshness.observed_returned_completed_sessions_after_source_asof_count,1);
  assert.equal(built.freshness.calendar_coverage.independently_verified_complete,false);assert.equal(built.freshness.freshness_eligible,false);
  assert.equal(built.source.universe.member_names_and_symbols_returned,false);
  assert.equal(built.source.captures[2].request_url_redacted,true);assert.equal(built.source.captures[2].redacted_query_fields[0],'symbols');
  assert.doesNotMatch(JSON.stringify(built.source.captures),new RegExp(localCohort.securities[0].symbol));
  assert.equal(bars.length,2);assert.equal(bars.reduce((s,r)=>s+r.provider_rows,0),(localCohort.symbols.length+1)*505);
});

test('a date-only Friday source can pass the age bound on its provider-observed grid without asserting exact market lag',()=>{
  const first=sourceFixture({sourceAsOf:'2026-10-30',evaluationAt:'2026-10-31T15:38:30.000Z'}).built;
  assert.equal(first.status,'computed');assert.equal(first.freshness.source_time_unknown,true);assert.equal(first.freshness.source_age_seconds,null);
  assert.equal(first.freshness.source_age_bounds_seconds.lower_bound,41910);assert.equal(first.freshness.source_age_bounds_seconds.upper_bound,128310);
  assert.equal(first.freshness.original_catalog_age_acceptable,true);assert.equal(first.freshness.source_age_max_age_acceptable,true);
  assert.equal(first.freshness.calendar_coverage.status,'provider_observed_coverage_valid');
  assert.equal(first.freshness.calendar_coverage.independently_verified_complete,false);assert.equal(first.freshness.freshness_eligible,true);
  assert.equal(first.freshness.observed_returned_completed_sessions_after_source_asof_count,0);
  assert.equal(first.freshness.current_session_lag_sessions,null);assert.equal(first.calculator_result.status,'research_only_score');
  const exact=sourceFixture({sourceAsOf:'2026-10-30',evaluationAt:'2026-11-01T04:00:00.000Z'}).built;
  assert.equal(exact.status,'computed');assert.equal(exact.freshness.source_age_bounds_seconds.upper_bound,172800);
  assert.equal(exact.freshness.source_age_max_age_acceptable,true);assert.equal(exact.calculator_result.status,'research_only_score');
  assert.equal(exact.freshness.current_session_lag_sessions,null);assert.equal(exact.restrictions.decision_eligible,false);
  const expected=computeFE05BreadthMeasurements(selectFE05TopIssuerCohort({...holdings,as_of_date:'2026-10-30'}),makeSyntheticCloses([...cohort.symbols,'SPY'],makeSyntheticDates(505,'2026-10-30')),makeSyntheticDates(505,'2026-10-30'));
  assert.deepEqual(exact.features,expected.features);
});

test('an ancient date is definitely stale; provider-returned calendar omissions cannot self-certify completeness or exact lag',()=>{
  const stale=sourceFixture({sourceAsOf:'2026-10-28',evaluationAt:'2026-10-31T15:38:30.000Z'}).built;
  assert.equal(stale.status,'abstained');assert.equal(stale.freshness.source_age_max_age_status,'definitely_stale');
  assert.equal(stale.freshness.source_age_max_age_acceptable,false);assert.ok(stale.freshness.source_age_bounds_seconds.lower_bound>172800);
  assert.equal(stale.freshness.current_session_lag_sessions,null);assert.equal(stale.freshness.observed_returned_completed_sessions_after_source_asof_count,2);
  assert.equal(stale.freshness.provider_latest_completed_session_date,'2026-10-30');assert.equal(stale.calculator_result,undefined);
  const missing=sourceFixture({sourceAsOf:'2026-10-30',evaluationAt:'2026-10-31T15:38:30.000Z',calendarEnd:'2026-10-30'}).built;
  assert.equal(missing.status,'abstained');assert.equal(missing.freshness.source_age_max_age_acceptable,true);
  assert.equal(missing.freshness.calendar_coverage.status,'unavailable_or_invalid');assert.equal(missing.freshness.current_session_lag_sessions,null);
  assert.equal(missing.freshness.freshness_eligible,false);assert.ok(missing.abstention_reasons.includes('provider_calendar_coverage_unavailable'));
  const noCalendar=qualifyFE05DateOnlyFreshness({sourceAsOf:'2026-10-30',evaluationAt:'2026-10-31T15:38:30.000Z'});
  assert.equal(noCalendar.source_age_max_age_acceptable,true);assert.equal(noCalendar.freshness_eligible,false);
  assert.equal(noCalendar.calendar_coverage.status,'unavailable_or_invalid');assert.equal(noCalendar.current_session_lag_sessions,null);
  const {built:withFriday,calendarSessions,calendar,dates:selectedDates,holdings:fridayHoldings,cohort:fridayCohort,closes:fridayCloses,
    holdingsCapture:fridayHoldingsCapture,bars:fridayBars}=sourceFixture({sourceAsOf:'2026-10-29',evaluationAt:'2026-10-31T04:00:00.000Z'});
  assert.equal(withFriday.status,'computed');assert.equal(withFriday.freshness.source_age_max_age_acceptable,true);
  assert.equal(withFriday.freshness.observed_returned_completed_sessions_after_source_asof_count,1);
  const omittedFriday=calendarSessions.filter(row=>row.date!=='2026-10-30');
  const omitted=qualifyFE05DateOnlyFreshness({sourceAsOf:'2026-10-29',evaluationAt:'2026-10-31T04:00:00.000Z',calendarCapture:calendar,calendarSessions:omittedFriday,selectedDates});
  assert.equal(omitted.source_age_max_age_acceptable,true);assert.equal(omitted.calendar_coverage.independently_verified_complete,false);
  assert.equal(omitted.calendar_coverage.status,'provider_observed_coverage_valid');assert.equal(omitted.freshness_eligible,true);
  assert.equal(omitted.current_session_lag_sessions,null);assert.equal(omitted.observed_returned_completed_sessions_after_source_asof_count,0);
  const omittedFridayResult=buildFE05SourceForecast({holdings:fridayHoldings,cohort:fridayCohort,dates:selectedDates,closesBySymbol:fridayCloses,
    calendarCapture:calendar,calendarSessions:omittedFriday,holdingsCapture:fridayHoldingsCapture,barsCaptures:fridayBars,evaluationAt:'2026-10-31T04:00:00.000Z'});
  assert.equal(omittedFridayResult.status,'computed');assert.ok(omittedFridayResult.features);assert.ok(omittedFridayResult.calculator_result);
  assert.equal(omittedFridayResult.freshness.calendar_coverage.complete_through_evaluation_date,null);
  assert.equal(omittedFridayResult.freshness.calendar_coverage.independently_verified_complete,false);
  assert.equal(omittedFridayResult.freshness.current_session_lag_sessions,null);
  assert.equal(omittedFridayResult.freshness.observed_returned_completed_sessions_after_source_asof_count,0);
  assert.equal(omittedFridayResult.source.calendar.complete_provider_response,undefined);
  assert.equal(omittedFridayResult.source.calendar_evaluation_coverage.complete_through_evaluation_date,null);
});

test('date-only intervals honor New York DST day lengths and exact freshness uses evaluation time, not acquisition receipt time',()=>{
  const onSpringDay=qualifyFE05DateOnlyFreshness({sourceAsOf:'2026-03-08',evaluationAt:'2026-03-09T04:00:00.000Z'});
  const onFallDay=qualifyFE05DateOnlyFreshness({sourceAsOf:'2026-11-01',evaluationAt:'2026-11-02T05:00:00.000Z'});
  assert.equal(onSpringDay.source_age_bounds_seconds.upper_bound,23*3600);
  assert.equal(onFallDay.source_age_bounds_seconds.upper_bound,25*3600);
  const {built,holdingsCapture,calendar,calendarSessions,bars,holdings:localHoldings,cohort:localCohort,dates:localDates,closes:localCloses}=sourceFixture({sourceAsOf:'2026-10-30',evaluationAt:'2026-10-31T15:38:30.000Z'});
  const recaptured={...holdingsCapture,request_started_at:'2026-10-31T15:38:05.000Z',http_response_received_at:'2026-10-31T15:38:08.000Z',received_at:'2026-10-31T15:38:10.000Z'};
  const recapturedForecast=buildFE05SourceForecast({holdings:localHoldings,cohort:localCohort,dates:localDates,closesBySymbol:localCloses,calendarCapture:calendar,calendarSessions,
    holdingsCapture:recaptured,barsCaptures:bars,evaluationAt:'2026-10-31T15:38:30.000Z'});
  assert.deepEqual(recapturedForecast.freshness.source_age_bounds_seconds,built.freshness.source_age_bounds_seconds);
  assert.equal(recapturedForecast.freshness.source_age_seconds,null);
});

test('strict instant validation rejects normalized impossible dates and accepts a valid explicit timezone offset',()=>{
  assert.equal(qualifyFE05DateOnlyFreshness({sourceAsOf:'2026-03-01',evaluationAt:'2026-03-01T12:00:00+05:30'}).source_age_bounds_seconds.upper_bound,5400);
  for(const evaluationAt of ['2026-02-30T12:00:00Z','2026-04-31T12:00:00Z','2026-01-01T24:00:00Z','2026-01-01T12:60:00Z','2026-01-01T12:00:00+24:00','2026-01-01T12:00:00+05:60'])
    assert.throws(()=>qualifyFE05DateOnlyFreshness({sourceAsOf:'2026-01-01',evaluationAt}),/invalid_breadth_freshness_inputs/);
});

test('source receipts require expected subjects and exact source URLs',()=>{
  const {bars,calendar,holdingsCapture,calendarSessions}=sourceFixture(),bad={...bars[0],subject:'SPY'};
  assert.throws(()=>buildFE05SourceForecast({holdings,cohort,dates,closesBySymbol:closes,calendarCapture:calendar,calendarSessions,holdingsCapture,barsCaptures:[bad,...bars.slice(1)],evaluationAt:'2026-10-31T13:30:10.000Z'}),/invalid_breadth_source_receipts/);
});
