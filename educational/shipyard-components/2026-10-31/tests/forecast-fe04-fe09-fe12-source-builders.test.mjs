import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
import {buildFE04SourceForecast,createFE04BoundedBarReducer} from '../research/forecast-features/fe04-gap-decomposition-v1.mjs';
import {buildFE09SourceForecast} from '../research/forecast-features/fe09-jump-tail-v1.mjs';
import {buildFE12SourceForecast,FE12_TOP_OF_BOOK_POLICY,FE12_TOP_OF_BOOK_V1_BLOCKED_BASELINE} from '../research/forecast-features/fe12-top-of-book-v2.mjs';
import {businessDates,etInstant,makeFE04Fixture,makeFE09Fixture,makeFE12Fixture} from './fixtures/fe04-fe09-fe12-synthetic.mjs';

const copy=x=>structuredClone(x),EPS=1e-10;
function close(actual,expected,eps=EPS){assert.ok(Number.isFinite(actual)&&Number.isFinite(expected)&&Math.abs(actual-expected)<=eps,`${actual} != ${expected}`);}
function scorerParity(id,result){assert.equal(result.status,'computed',result.error);assert.deepEqual(result.calculator_result,evaluateForecastEngine(id,result.features));}

test('FE04 bounded gap/fair-gap/open-acceptance builder: independent feature checks and unchanged scorer',()=>{
 const input=makeFE04Fixture(),result=buildFE04SourceForecast(input);scorerParity('FE04',result);
 assert.equal(result.coverage.selected_sessions,62);assert.equal(result.coverage.required_prior_premarket_slots,100);
 close(result.features.fair_gap_z,(result.measurements.fair_split_adjusted_log_gap-result.measurements.gap_normalization.mean)/result.measurements.gap_normalization.population_sd);
 close(result.features.premarket_liquidity,result.measurements.premarket_split_adjusted_dollar_volume_proxy/(result.measurements.premarket_split_adjusted_dollar_volume_proxy+result.measurements.premarket_prior_median_split_adjusted_dollar_volume_proxy));
 assert.equal(result.features.open_acceptance,1);assert.equal(result.features.gap_z,result.measurements.gap_normalization.z);
 assert.equal(result.restrictions.decision_eligible,false);assert.equal(result.source.adjustment,'split');
});


test('FE04 premarket dollar-volume transform stays finite at large but valid source magnitudes',()=>{
 const input=makeFE04Fixture(),sessions=input.calendar.sessions,current=sessions.at(-1);
 for(const symbol of ['SPY','QQQ','IWM'])for(const session of [...sessions.slice(-21,-1),current]){const volume=session.date===current.date?2e305:1.5e305,open=Date.parse(session.open)-300000;for(let i=0;i<5;i++){const bar=input.bars_by_symbol[symbol].find(b=>Date.parse(b.t)===open+i*60000);assert.ok(bar);bar.v=volume;}}
 const result=buildFE04SourceForecast(input);assert.equal(result.status,'computed',result.error);const currentVolume=result.measurements.premarket_split_adjusted_dollar_volume_proxy,priorMedian=result.measurements.premarket_prior_median_split_adjusted_dollar_volume_proxy,scale=Math.max(currentVolume,priorMedian),expected=(currentVolume/scale)/((currentVolume/scale)+(priorMedian/scale));assert.ok(Number.isFinite(currentVolume)&&Number.isFinite(priorMedian));assert.ok(Number.isFinite(result.features.premarket_liquidity));close(result.features.premarket_liquidity,expected);assert.ok(result.features.premarket_liquidity>0.5&&result.features.premarket_liquidity<1);
});

test('FE04 split-scale invariance is tested; wrong adjustment, missing windows, truncated page or scope injection abstain',()=>{
 const input=makeFE04Fixture(),base=buildFE04SourceForecast(input);assert.equal(base.status,'computed');
 const scaled=copy(input);for(const rows of Object.values(scaled.bars_by_symbol))for(const b of rows){b.o*=0.5;b.h*=0.5;b.l*=0.5;b.c*=0.5;b.v*=2;}
 const split=buildFE04SourceForecast(scaled);assert.equal(split.status,'computed');
 for(const key of Object.keys(base.features))close(split.features[key],base.features[key]);
 const raw=copy(input);raw.adjustment='raw';assert.equal(buildFE04SourceForecast(raw).status,'unavailable');
 const missing=copy(input);missing.bars_by_symbol.QQQ.pop();assert.notEqual(buildFE04SourceForecast(missing).status,'computed');
 const truncated=copy(input);truncated.captures.find(c=>c.operation==='history_1Min_SPY_page_6').has_next_page=true;assert.equal(buildFE04SourceForecast(truncated).status,'unavailable');
 const unsupported=copy(input);unsupported.symbol='DIA';assert.equal(buildFE04SourceForecast(unsupported).status,'unavailable');
});

test('FE04 reducer streams a near-60k extended-hours six-page history but retains only consumed windows',()=>{
 const input=makeFE04Fixture(),symbol='QQQ',sessions=input.calendar.sessions,targets=new Map(input.bars_by_symbol[symbol].map(b=>[Date.parse(b.t),b])),reducer=createFE04BoundedBarReducer(sessions,symbol),last=sessions.at(-1),acceptanceEnd=Date.parse(last.open)+5*60000,expectedRows=241+60*960+335;
 let page=[],pageNumber=0,total=0;for(let i=0;i<sessions.length;i++){const s=sessions[i],start=i===0?Date.parse(s.close)-60000:Date.parse(etInstant(s.date,'04:00')),end=i===sessions.length-1?acceptanceEnd:Date.parse(etInstant(s.date,'20:00'));for(let at=start;at<end;at+=60000){const t=new Date(at).toISOString(),bar=targets.get(at)||{t,o:100,h:100.01,l:99.99,c:100,v:10};page.push(bar);total++;if(page.length===10000){pageNumber++;reducer.pushPage(page,pageNumber*10000<expectedRows);page=[];}}}
 if(page.length){pageNumber++;reducer.pushPage(page,pageNumber*10000<expectedRows);}
 const reduced=reducer.finish();assert.equal(total,expectedRows);assert.equal(pageNumber,6);assert.equal(reduced.provider_rows,expectedRows);assert.equal(reduced.page_count,6);assert.equal(reduced.retained_rows,input.bars_by_symbol[symbol].length);assert.ok(reduced.retained_rows<=250);assert.deepEqual(reduced.bars,input.bars_by_symbol[symbol]);
 const incomplete=createFE04BoundedBarReducer(sessions,symbol);assert.throws(()=>incomplete.finish(),/provider_pagination_incomplete/);
 const overflow=createFE04BoundedBarReducer(sessions,symbol);for(let p=0;p<5;p++)overflow.pushPage(Array.from({length:10000},(_,i)=>({t:new Date(Date.parse(sessions[0].close)-60000-(50000-(p*10000+i))*60000).toISOString(),o:10,h:10.1,l:9.9,c:10,v:1})),true);assert.throws(()=>overflow.pushPage([{t:sessions.at(-1).open,o:10,h:10.1,l:9.9,c:10,v:1}],true),/provider_page_budget_exceeded/);
});

test('FE09 finite-sample BV oracle, overnight gap, scoped event density and unchanged scorer',()=>{
 const input=makeFE09Fixture(),result=buildFE09SourceForecast(input);scorerParity('FE09',result);
 const session=result.measurements.session_variation.at(-1),s=input.sessions.find(x=>x.date===session.session),bars=input.bars.filter(b=>Date.parse(b.t)>=Date.parse(s.open)&&Date.parse(b.t)<Date.parse(s.close));
 const rs=bars.map((b,i)=>Math.log(b.c/(i?bars[i-1].c:b.o))),rv=rs.reduce((a,r)=>a+r*r,0),sum=rs.slice(1).reduce((a,r,i)=>a+Math.abs(r)*Math.abs(rs[i]),0);
 close(session.rv,rv);close(session.bv,(Math.PI/2)*(rs.length/(rs.length-1))*sum);close(session.jump_variation,Math.max(0,rv-session.bv));
 assert.equal(result.measurements.macro_event_count,1);close(result.features.event_density,0.5);assert.equal(result.coverage.required_sessions,22);
});


test('FE09 refuses a shifted session open instead of retimestamping a matching 10:00-16:30 bar grid',()=>{
 const input=makeFE09Fixture(),shift=v=>new Date(Date.parse(v)+30*60000).toISOString();
 for(const s of input.calendar.sessions){s.open=shift(s.open);s.close=shift(s.close);}
 for(const b of input.bars)b.t=shift(b.t);
 input.evaluation_at=etInstant('2026-10-30','16:50');
 for(const c of input.captures){c.request_started_at=shift(c.request_started_at);c.http_response_received_at=shift(c.http_response_received_at);c.received_at=shift(c.received_at);}
 input.calendar.received_at=shift(input.calendar.received_at);
 for(const month of input.macro_events.months){month.received_at=shift(month.received_at);for(const source of month.sources)source.received_at=shift(source.received_at);for(const event of month.events)event.available_at=shift(event.available_at);}
 const barCapture=input.captures.find(c=>c.operation==='history_5Min_page_1'),url=new URL(barCapture.request_url);url.searchParams.set('start',input.calendar.sessions[0].open);url.searchParams.set('end',new Date(Date.parse(input.calendar.sessions[21].close)-1).toISOString());barCapture.request_url=url.toString();
 const result=buildFE09SourceForecast(input);assert.equal(result.status,'unavailable');assert.equal(result.error,'unsupported_session_open');
});

test('FE09 date-only events count by official-session date, scoped primary/FRED family denominator is fixed, bad scope/future bars abstain',()=>{
 const input=makeFE09Fixture(),unknown=copy(input);unknown.macro_events.months[0].events[0]={...unknown.macro_events.months[0].events[0],source_event_id:'date-only',title:'Employment Situation',scheduled_at:null,scheduled_date:input.businessFuture[0],time_status:'time_unknown',available_at:unknown.macro_events.months[0].received_at};const dateOnly=buildFE09SourceForecast(unknown);assert.equal(dateOnly.status,'computed');assert.equal(dateOnly.measurements.macro_event_count,1);assert.equal(dateOnly.measurements.macro_event_date_precision,'official-session-date; unknown intraday time preserved and not inferred');
 const outside=copy(input);outside.macro_events.months[0].events[0]={source:'BLS',source_event_id:'outside',title:'Unlisted release',scheduled_date:'2026-11-07',time_status:'time_unknown',available_at:outside.macro_events.months[0].received_at};assert.equal(buildFE09SourceForecast(outside).status,'computed');
 const scope=copy(input);scope.macro_events.months[0].sources[1].url='https://not-bls.example/feed';assert.equal(buildFE09SourceForecast(scope).status,'unavailable');
 const future=copy(input);future.bars.push({...future.bars.at(-1),t:'2026-10-31T15:00:00.000Z'});future.bars.sort((a,b)=>Date.parse(a.t)-Date.parse(b.t));assert.equal(buildFE09SourceForecast(future).status,'unavailable');
 const fallback=copy(input),month=fallback.macro_events.months[0],ids=[[10,'Consumer Price Index'],[11,'Employment Cost Index'],[46,'Producer Price Index'],[47,'Productivity and Costs'],[50,'Employment Situation'],[188,'U.S. Import and Export Price Indexes'],[192,'Job Openings and Labor Turnover Survey']];const fredUrl='https://fred.stlouisfed.org/releases/calendar';
 const pages=ids.map(([id,title])=>({release_id:id,title,url:`${fredUrl}?view=month&y=2026&m=11&rid=${id}`,status:'no_rows_in_requested_month',received_at:month.received_at,raw_sha256:'a'.repeat(64),parsed_rows:0}));
 month.status='partial';month.sources[1]={source:'FRED',status:'parsed',scope_complete:true,coverage_scope:'selected_bls_releases',received_at:month.received_at,raw_sha256:'b'.repeat(64),url:fredUrl,release_pages:pages};month.events[0]={...month.events[0],source:'FRED',release_id:10,source_url:pages[0].url,source_event_id:'FRED:10:2026-11-03:10:00'};
 const fallbackResult=buildFE09SourceForecast(fallback);assert.equal(fallbackResult.status,'computed',fallbackResult.error);assert.equal(fallbackResult.measurements.macro_event_count,1);assert.equal(fallbackResult.source.macro_event_sources.find(s=>s.source==='FRED').aggregate_status,'partial');close(fallbackResult.features.event_density,dateOnly.features.event_density);
 const incomplete=copy(fallback);incomplete.macro_events.months[0].sources[1].release_pages.pop();assert.equal(buildFE09SourceForecast(incomplete).status,'unavailable');
});

test('FE12 IEX L1 snapshot oracle, fixed-clock selection, unit and page safeguards, split-scale invariance',()=>{
 const input=makeFE12Fixture(),result=buildFE12SourceForecast(input);scorerParity('FE12',result);
 const q=input.quote_windows.at(-1).quotes[0],spread=(q.ap-q.bp)/((q.ap+q.bp)/2);
 close(result.measurements.spread.current,spread);assert.equal(result.source.quote_feed,'iex');assert.equal(result.source.quote_size_unit,'shares');assert.equal(result.source.quote_endpoint,'historical_stock_L1_quotes');assert.equal(result.source.quote_selection.includes('point at fixed 09:35 ET cutoff'),true);assert.equal(result.measurements.historical_quote_source.includes('no Level-2'),true);assert.equal(result.coverage.provider_cursor_present_snapshots,6);assert.equal(FE12_TOP_OF_BOOK_POLICY.id,'FE12_IEX_TOP_OF_BOOK_CUTOFF_SNAPSHOT_V2');assert.equal(FE12_TOP_OF_BOOK_V1_BLOCKED_BASELINE.status,'BLOCKED_BASELINE');
 const scaled=copy(input);for(const w of scaled.quote_windows)for(const q of w.quotes){q.bp*=0.5;q.ap*=0.5;q.bs*=2;q.as*=2;}for(const b of scaled.bars){b.o*=0.5;b.h*=0.5;b.l*=0.5;b.c*=0.5;}
 const split=buildFE12SourceForecast(scaled);assert.equal(split.status,'computed');for(const key of Object.keys(result.features))close(split.features[key],result.features[key]);
 const paged=copy(input);paged.quote_windows[1].provider_next_page_token_present=true;paged.quote_windows[1].capture.has_next_page=true;assert.equal(buildFE12SourceForecast(paged).status,'computed');assert.equal(buildFE12SourceForecast(paged).coverage.provider_cursor_present_snapshots,7);
 const after=copy(input);after.quote_windows.at(-1).quotes[0].t='2026-10-30T13:35:00.000000001Z';assert.equal(buildFE12SourceForecast(after).status,'unavailable');const invalidTime=copy(input);invalidTime.quote_windows.at(-1).quotes[0].t='2026-10-30T13:34:60.000Z';assert.equal(buildFE12SourceForecast(invalidTime).status,'unavailable');const before=copy(input);before.quote_windows.at(-1).quotes[0].t='2026-10-30T13:34:54.999999999Z';assert.equal(buildFE12SourceForecast(before).status,'unavailable');
 const ascending=copy(input);ascending.quote_windows[0].capture.request_url=ascending.quote_windows[0].capture.request_url.replace('sort=desc','sort=asc');assert.equal(buildFE12SourceForecast(ascending).status,'unavailable');
 const missingPage=copy(input);missingPage.captures.find(c=>c.operation==='history_1Min_bars_page_1').has_next_page=true;assert.equal(buildFE12SourceForecast(missingPage).status,'unavailable');
 const twoPages=copy(input),bar1=twoPages.captures.find(c=>c.operation==='history_1Min_bars_page_1');bar1.has_next_page=true;const url2=new URL(bar1.request_url);url2.searchParams.set('page_token','[continuation]');const bar2={...bar1,operation:'history_1Min_bars_page_2',request_url:url2.toString(),provider_rows:0,retained_rows:0,has_next_page:false,response_sha256:'c'.repeat(64)};twoPages.captures.push(bar2);twoPages.bars_capture.response_sha256s.push(bar2.response_sha256);const twoPageResult=buildFE12SourceForecast(twoPages);assert.equal(twoPageResult.status,'computed');assert.equal(twoPageResult.source.bar_pages.length,2);
 const crossed=copy(input);crossed.quote_windows[0].quotes[0].bp=crossed.quote_windows[0].quotes[0].ap+0.01;assert.equal(buildFE12SourceForecast(crossed).status,'unavailable');
 const stale=copy(input);for(const q of stale.quote_windows.at(-1).quotes)q.t='2026-10-30T13:33:59.000Z';assert.equal(buildFE12SourceForecast(stale).status,'unavailable');
 const feed=copy(input);feed.quote_feed='sip';assert.equal(buildFE12SourceForecast(feed).status,'unavailable');const unit=copy(input);delete unit.quote_size_unit;assert.equal(buildFE12SourceForecast(unit).status,'unavailable');
 const older=copy(input),replacement=businessDates('2024-10-30',18);for(let i=0;i<17;i++){const from=input.sessions[i].date,to=replacement[i];const shift=v=>{if(typeof v==='string')return v.split(from).join(to);if(Array.isArray(v))return v.map(shift);if(v&&typeof v==='object')for(const k of Object.keys(v))v[k]=shift(v[k]);return v;};shift(older);}assert.equal(older.sessions[0].date<'2025-11-03',true);assert.equal(buildFE12SourceForecast(older).status,'computed');
});

test('FE04 premarket age uses 09:30 source clock, not the newer 09:35 acceptance clock',()=>{const input=makeFE04Fixture();input.evaluation_at='2026-10-30T19:30:00.000Z';const fresh=buildFE04SourceForecast(input);assert.equal(fresh.status,'computed',fresh.error);assert.equal(fresh.freshness.source_age_seconds,21600);assert.equal(fresh.freshness.components.premarket_liquidity.max_age_seconds,21600);input.evaluation_at='2026-10-30T19:30:01.000Z';const stale=buildFE04SourceForecast(input);assert.equal(stale.status,'unavailable');assert.equal(stale.error,'stale_opening_window');});
