import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {FE06_TICKERS,FE06_SPLIT_TICKERS,FE06_SPLIT_DATE,fe06Dates,fe06SourceCalendar,fe06UniverseBooks,fe06Records,fe06Workbook} from './fixtures/fe06-synthetic.mjs';
import {evaluateForecastEngine} from '../dist/forecast-engines.mjs';
import {validateXmlWellFormedness} from '../research/forecast-features/xml-well-formedness-preflight-v1.mjs';

const exchange=readFileSync(new URL('../worker/exchange-calendar.js',import.meta.url),'utf8');
const adapter=readFileSync(new URL('../worker/forecast-fe06.js',import.meta.url),'utf8');
globalThis.shipyardValidateXmlWellFormedness=validateXmlWellFormedness;
vm.runInThisContext(exchange+'\n'+adapter+'\nglobalThis.__fe06Api={parse:shipyardFE06ParseWorkbook,derive:shipyardFE06Derive,produce:shipyardForecastFE06,calendarBoundary:shipyardCalendarBoundary,decimal:shipyardFE06Decimal,mul:shipyardFE06Mul,sub:shipyardFE06Sub,scale:shipyardFE06Scale,divide:shipyardFE06DivideByInteger,num:shipyardFE06Num,toString:shipyardFE06DecimalString,splitRatio:shipyardFE06SplitRatio,checkSplitSignature:shipyardFE06CheckSplitSignature,rankZ:shipyardFE06RankZ,z:shipyardFE06Z,policy:SHIPYARD_FE06_POLICY,policyHash:SHIPYARD_FE06_POLICY_SHA256,universe:SHIPYARD_FE06_UNIVERSE,resetRuntime:()=>{SHIPYARD_FE06_RUNTIME.ingressRates.clear();SHIPYARD_FE06_RUNTIME.coldRates.clear();SHIPYARD_FE06_RUNTIME.cache.clear();SHIPYARD_FE06_RUNTIME.inflight.clear();},runtime:SHIPYARD_FE06_RUNTIME,cachePut:shipyardFE06CachePut,cacheGet:shipyardFE06CacheGet,cacheKey:shipyardFE06CacheKey};');
const api=globalThis.__fe06Api;
const URLS=Object.fromEntries(FE06_TICKERS.map(ticker=>[ticker,`https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-${ticker.toLowerCase()}.xlsx`]));
const now=Date.parse('2026-10-31T12:00:00Z');
function sourceSessions(dates=fe06Dates()) {return fe06SourceCalendar(dates).map(row=>({date:row.date,open:api.calendarBoundary(row.date,row.open),close:api.calendarBoundary(row.date,row.close)}));}
async function parsedUniverse(options={}){
  const books=fe06UniverseBooks(options),result={};
  for(const ticker of FE06_TICKERS)result[ticker]=await api.parse(books[ticker],ticker,URLS[ticker],'a'.repeat(64),{started_at:'2026-10-31T11:59:00.000Z',completed_at:'2026-10-31T12:00:00.000Z'});
  return result;
}
const receipts={issuer_first_seen_at:'2026-10-31T11:59:00.000Z',workbooks:FE06_TICKERS.map(ticker=>({ticker,source_url:URLS[ticker],sha256:'a'.repeat(64),bytes:1000,retrieved_at_start:'2026-10-31T11:59:00.000Z'}))};

test('actual Decimal oracle for XLF issuer NAV/shares/asset sample and verified 2:1 split',()=>{
  const nav=api.decimal('56.927013'),shares=api.decimal('932545427'),previous=api.decimal('923395427'),assets=api.decimal('51778727662.39');
  const flow=api.mul(nav,api.sub(shares,previous));assert.equal(api.toString(flow),'520882168.95');
  assert.ok(Math.abs(api.num(flow)/api.num(assets)-0.01005977150203998)<1e-16);
  const splitFlow=api.mul(api.decimal('119.744548'),api.sub(api.decimal('200'),api.scale(api.decimal('100'),2)));
  assert.equal(api.toString(splitFlow),'0');
  const oldNav=api.decimal('238.183715'),oldShares=api.decimal('101703252'),oldAssets=api.mul(oldNav,oldShares);
  assert.equal(api.toString(api.mul(api.divide(oldNav,2),api.scale(oldShares,2))),api.toString(oldAssets));
  assert.equal(FE06_SPLIT_TICKERS.length,5);assert.equal(api.policy.id,'fe06-issuer-share-nav-flow-v1');
});

test('bounded parser reads all eleven synthetic issuer workbooks and the pure derivation matches independent window/oracle checks',async()=>{
  const rows=await parsedUniverse(),dates=fe06Dates(),sessions=sourceSessions(dates),value=api.derive(rows,sessions,now,receipts,'XLF');
  assert.equal(value.status,'computed');assert.equal(value.coverage.fixed_universe_size,11);assert.equal(value.coverage.complete_funds,11);
  assert.equal(value.coverage.session_count,254);assert.deepEqual(value.coverage.missing_sessions,[]);assert.deepEqual(value.coverage.unexpected_sessions,[]);
  assert.equal(value.target_sector_symbol,'XLF');assert.deepEqual(Object.keys(value.features).sort(),['leadership_breadth','sector_dispersion_z','sector_flow_z','sector_momentum_rank_z'].sort());
  assert.notEqual(value.features.sector_momentum_rank_z,0);assert.ok(value.features.leadership_breadth>=0&&value.features.leadership_breadth<=1);
  assert.equal(value.source.observed_at,'2026-10-29T20:00:00.000Z');assert.equal(value.source.publication_at,null);
  assert.equal(value.source.latest_completed_market_session,'2026-10-30');assert.equal(value.source.issuer_lag_sessions,1);
  assert.equal(value.source.source_rows.XLF.flow.baseline_count,252);assert.equal(value.source.source_rows.XLF.flow.baseline_start,dates[1]);
  assert.equal(value.source.source_rows.XLF.flow.baseline_end,dates.at(-2));assert.equal(value.source.source_rows.XLF.first_seen_at,'2026-10-31T11:59:00.000Z');
  assert.equal(value.restrictions.decision_eligible,false);assert.equal(value.restrictions.observed_vendor_flow,false);
  assert.equal(value.restrictions.volume_substituted,false);assert.equal(value.restrictions.aum_change_substituted,false);
  const targetRows=rows.XLF.rows;const prior=targetRows[1],current=targetRows[0],oracleFlow=api.mul(current.nav,api.sub(current.shares,prior.shares));
  assert.equal(value.source.source_rows.XLF.flow.current_flow_usd,api.toString(oracleFlow));
  assert.equal(value.source.source_rows.XLF.flow.current_normalized_flow,api.num(oracleFlow)/api.num(prior.assets));
  assert.equal(value.source.source_rows.XLF.flow.split_ratio,1);assert.equal(value.source.source_rows.XLF.source_sha256,'a'.repeat(64));
  for(const ticker of FE06_SPLIT_TICKERS){const currentSplit=rows[ticker].rows.find(row=>row.date===FE06_SPLIT_DATE),previousSplit=rows[ticker].rows.find(row=>row.date<'2025-12-05');
    assert.ok(currentSplit&&previousSplit);assert.equal(api.splitRatio(ticker,FE06_SPLIT_DATE),2);
    assert.equal(api.toString(api.mul(currentSplit.nav,api.sub(currentSplit.shares,api.scale(previousSplit.shares,2)))),'0');
    assert.equal(currentSplit.quality,'complete');
  }
});

test('current row mutation cannot leak into prior-only 252 flow baseline',async()=>{
  const rows=await parsedUniverse(),sessions=sourceSessions();const base=api.derive(rows,sessions,now,receipts,'XLF');
  const changed=structuredClone(rows),last=changed.XLF.rows[0];last.nav=api.decimal('80');last.shares=api.decimal('999999999');last.assets=api.mul(last.nav,last.shares);last.quality='complete';
  const next=api.derive(changed,sessions,now,receipts,'XLF');
  assert.equal(next.source.source_rows.XLF.flow.baseline_mean,base.source.source_rows.XLF.flow.baseline_mean);
  assert.equal(next.source.source_rows.XLF.flow.baseline_sample_sd,base.source.source_rows.XLF.flow.baseline_sample_sd);
  assert.notEqual(next.source.source_rows.XLF.flow.current_normalized_flow,base.source.source_rows.XLF.flow.current_normalized_flow);
});

test('cash distribution with unchanged shares is not mislabeled as outflow',async()=>{
  const rows=await parsedUniverse({cashDistribution:true}),value=api.derive(rows,sourceSessions(),now,receipts,'XLF');
  assert.equal(value.source.source_rows.XLF.current.nav!==value.source.source_rows.XLF.prior.nav,true);
  assert.equal(value.source.source_rows.XLF.flow.current_flow_usd,'0');assert.equal(value.source.source_rows.XLF.flow.current_normalized_flow,0);
});

test('parser and derivation fail closed on missing/duplicate/calendar-gap/zero-asset/10bp-breach rows',async()=>{
  const dates=fe06Dates(),last=dates.at(-1),books=fe06UniverseBooks();
  for(const [options,expected] of [[{missingSharesAt:last},'invalid_window_row'],[{zeroAssetsAt:last},'invalid_window_row'],[{breachAssetsAt:last},'invalid_window_row']]){
    const bad={...books,XLF:fe06Workbook('XLF',fe06Records(4),options)};
    const rows={};for(const ticker of FE06_TICKERS)rows[ticker]=await api.parse(bad[ticker],ticker,URLS[ticker],'b'.repeat(64),{started_at:'2026-10-31T11:59:00Z'});
    assert.throws(()=>api.derive(rows,sourceSessions(dates),now,receipts,'XLF'),error=>error.code.startsWith(expected));
  }
  const duplicate=fe06Workbook('XLF',fe06Records(4),{duplicateDateAt:dates.at(-5)});
  await assert.rejects(()=>api.parse(duplicate,'XLF',URLS.XLF,'c'.repeat(64),{started_at:'2026-10-31T11:59:00Z'}),error=>error.code==='xlsx_duplicate_or_unsorted_date');
  const rows=await parsedUniverse(),gap=sourceSessions(dates).filter(s=>s.date!==dates[100]);
  assert.throws(()=>api.derive(rows,gap,now,receipts,'XLF'),error=>error.code==='official_calendar_mismatch');
});

test('unknown inverse share-price basis jumps abstain while ordinary flow and verified action remain usable',()=>{
  const prior={nav:api.decimal('100'),shares:api.decimal('1000')};
  for(const ratio of [2,3,4,1.5,5,10])for(const factor of [ratio,1/ratio]){
    const current={nav:api.decimal(String(100/factor)),shares:api.decimal(String(1000*factor))};
    assert.throws(()=>api.checkSplitSignature('XLF',current,prior,1),error=>error.code==='unsupported_share_basis_change',`ratio=${factor}`);
  }
  const ordinary={nav:api.decimal('100.25'),shares:api.decimal('1001')};assert.doesNotThrow(()=>api.checkSplitSignature('XLF',ordinary,prior,1));
  const verified={nav:api.decimal('50'),shares:api.decimal('2000')};assert.doesNotThrow(()=>api.checkSplitSignature('XLF',verified,prior,2));
  assert.equal(api.policy.unsupported_split_signature_tolerance,0.15);
});

test('corporate-action, XML and ZIP attacks are rejected or ignored according to the pinned boundary',async()=>{
  const dates=fe06Dates(),normal=fe06Records(4);
  const unsupported=await api.parse(fe06Workbook('XLF',fe06Records(4,{unsupportedSplit:true})),'XLF',URLS.XLF,'d'.repeat(64),{started_at:'2026-10-31T11:59:00Z'});
  const all=await parsedUniverse();all.XLF=unsupported;assert.throws(()=>api.derive(all,sourceSessions(dates),now,receipts,'XLF'),error=>error.code==='unsupported_share_basis_change');
  const external=await api.parse(fe06Workbook('XLF',normal,{externalWorksheetRelations:true}),'XLF',URLS.XLF,'e'.repeat(64),{started_at:'2026-10-31T11:59:00Z'});assert.equal(external.ticker,'XLF');
  const fakeDate=normal.at(-1).date;
  await assert.rejects(()=>api.parse(fe06Workbook('XLF',fe06Records(4),{commentRowAt:fakeDate}),'XLF',URLS.XLF,'f'.repeat(64),{started_at:'2026-10-31T11:59:00Z'}),error=>error.code==='xlsx_xml_comments_unsupported');
  for(const part of ['xl/workbook.xml','xl/_rels/workbook.xml.rels','xl/sharedStrings.xml','xl/worksheets/sheet1.xml','xl/worksheets/_rels/sheet1.xml.rels']){
    await assert.rejects(()=>api.parse(fe06Workbook('XLF',fe06Records(4),{commentXmlPart:part}),'XLF',URLS.XLF,'f'.repeat(64),{started_at:'2026-10-31T11:59:00Z'}),error=>error.code==='xlsx_xml_comments_unsupported',part);
  }
  await assert.rejects(()=>api.parse(fe06Workbook('XLF',fe06Records(4),{malformedXmlStart:true}),'XLF',URLS.XLF,'f'.repeat(64),{started_at:'2026-10-31T11:59:00Z'}),error=>error.code==='xlsx_xml_malformed');
  await assert.rejects(()=>api.parse(fe06Workbook('XLF',fe06Records(4),{foreignRowAt:fakeDate}),'XLF',URLS.XLF,'f'.repeat(64),{started_at:'2026-10-31T11:59:00Z'}),error=>error.code==='xlsx_sheetdata_structure_invalid');
  await assert.rejects(()=>api.parse(fe06Workbook('XLF',fe06Records(4),{mismatchCellRowAt:fakeDate}),'XLF',URLS.XLF,'f'.repeat(64),{started_at:'2026-10-31T11:59:00Z'}),error=>error.code==='xlsx_cell_ref_invalid');
  for(const [opts,expected] of [[{doctype:true},'xlsx_xml_active_content'],[{macro:true},'xlsx_active_content_unsupported'],[{extraEntries:[['../evil','x']]},'xlsx_zip_path_invalid'],[{corrupt:true},'xlsx_entry_crc_mismatch']]){
    await assert.rejects(()=>api.parse(fe06Workbook('XLF',normal,opts),'XLF',URLS.XLF,'f'.repeat(64),{started_at:'2026-10-31T11:59:00Z'}),error=>error.code===expected);
  }
  assert.throws(()=>api.rankZ(Array(11).fill(0)),error=>error.code==='zero_rank_dispersion');
  const ties=api.rankZ([1,1,2,3,4,5,6,7,8,9,10]);assert.equal(ties.ranks[0],1.5);assert.equal(ties.ranks[1],1.5);
  assert.throws(()=>api.z(1,Array(252).fill(0)),error=>error.code==='zero_baseline_variance');
});

test('freshness is semantic-close age, strict at 48h; DST, early-close, unknown publication and zero-SD are preserved',async()=>{
  assert.equal(api.calendarBoundary('2026-10-29','16:00'),'2026-10-29T20:00:00.000Z');
  assert.equal(api.calendarBoundary('2025-11-28','13:00'),'2025-11-28T18:00:00.000Z');
  const rows=await parsedUniverse(),sessions=sourceSessions();
  const last=Date.parse('2026-10-29T20:00:00.000Z');
  assert.equal(api.derive(rows,sessions,last+172800000-1,receipts,'XLF').source.publication_at,null);
  assert.throws(()=>api.derive(rows,sessions,last+172800000,receipts,'XLF'),error=>error.code==='source_data_stale');
  assert.throws(()=>api.derive(rows,sessions,last-1,receipts,'XLF'),error=>error.code==='future_source_timestamp');
  const flat=await parsedUniverse({constantShares:true});assert.throws(()=>api.derive(flat,sessions,now,receipts,'XLF'),error=>error.code==='zero_baseline_variance');
});

test('end-to-end source producer bounds 12 requests and calls the unchanged FE06 scorer',async()=>{
  const RealDate=globalThis.Date,RealFetch=globalThis.fetch,RealJson=globalThis.json,RealResearchResponse=globalThis.researchResponse,RealLogic=globalThis.SHIPYARD_FORECAST_LOGIC;
  const evaluationAt='2026-10-31T12:00:00.000Z',evaluationMs=Date.parse(evaluationAt),dates=fe06Dates(),books=fe06UniverseBooks(),requests=[];
  class ClockDate extends RealDate{constructor(...args){super(...(args.length?args:[evaluationMs]));}static now(){return evaluationMs;}}
  globalThis.Date=ClockDate;globalThis.SHIPYARD_FORECAST_LOGIC={evaluateForecastEngine};
  globalThis.json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});
  globalThis.researchResponse=(value,status=200)=>globalThis.json(value,status);
  globalThis.fetch=async (input,options)=>{
    const url=new URL(input);requests.push({url:url.href,options});
    if(url.hostname==='paper-api.alpaca.markets')return new Response(JSON.stringify(fe06SourceCalendar(dates)),{status:200,headers:{'content-type':'application/json'}});
    const ticker=/-([a-z]{3,4})\.xlsx$/i.exec(url.pathname)?.[1]?.toUpperCase();assert.ok(ticker&&books[ticker],`unexpected fixed-source URL ${url.href}`);
    return new Response(books[ticker],{status:200,headers:{'content-type':'application/octet-stream'}});
  };
  try{
    api.resetRuntime();
    const request=new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLF',{headers:{'cf-connecting-ip':'198.51.100.10'}});
    const response=await api.produce(request,{engine_id:'FE06',symbol:'XLF'},{ALPACA_API_KEY_ID:'synthetic',ALPACA_API_SECRET_KEY:'synthetic'});
    const value=await response.json();assert.equal(response.status,200,JSON.stringify(value));assert.equal(value.status,'computed');assert.equal(value.target_sector_symbol,'XLF');
    assert.equal(requests.length,12);assert.equal(value.acquisition.request_count,12);assert.equal(value.acquisition.request_bound,12);assert.equal(value.acquisition.concurrency_bound,2);
    assert.ok(value.acquisition.response_bytes>Object.values(books).reduce((n,b)=>n+b.length,0));
    assert.ok(value.acquisition.response_bytes<=value.acquisition.source_bytes_bound);
    assert.equal(value.acquisition.calendar_receipt.latest_completed_session,'2026-10-30');assert.equal(value.source.issuer_lag_sessions,1);
    assert.equal(value.source.source_receipts.length,11);assert.equal(value.source.source_receipts.every(r=>/^[a-f0-9]{64}$/.test(r.sha256)),true);
    assert.equal(value.calculator_result.status,'research_only_score');assert.deepEqual(value.calculator_result,evaluateForecastEngine('FE06',value.features));
    assert.equal(value.restrictions.decision_eligible,false);assert.equal(value.restrictions.order_submission_enabled,false);
    assert.equal(value.restrictions.redistribution_rights_established,false);assert.ok(new TextEncoder().encode(JSON.stringify(value)).length<48*1024);
    assert.equal(requests.filter(r=>new URL(r.url).hostname!=='paper-api.alpaca.markets').length,11);
    for(const {url,options} of requests){const u=new URL(url),headers=Object.fromEntries(new Headers(options.headers).entries());
      assert.equal(options.redirect,'manual');assert.equal(headers.authorization,undefined);
      if(u.hostname==='paper-api.alpaca.markets'){
        assert.deepEqual(Object.keys(headers).sort(),['accept','apca-api-key-id','apca-api-secret-key'].sort());
        assert.equal(headers['apca-api-key-id'],'synthetic');assert.equal(headers['apca-api-secret-key'],'synthetic');
        assert.equal((Date.parse(u.searchParams.get('end'))-Date.parse(u.searchParams.get('start')))/86400000,450);
      }else{
        assert.equal(u.hostname,'www.ssga.com');assert.deepEqual(Object.keys(headers),['accept']);
        assert.equal(!url.includes('synthetic'),true);assert.equal(!Object.values(headers).some(v=>String(v).includes('synthetic')),true);
      }
    }
    const cachedResponse=await api.produce(new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLK',{headers:{'cf-connecting-ip':'198.51.100.10'}}),{engine_id:'FE06',symbol:'XLK'},{ALPACA_API_KEY_ID:'synthetic',ALPACA_API_SECRET_KEY:'synthetic'});
    const cached=await cachedResponse.json();assert.equal(cachedResponse.status,200);assert.equal(cached.target_sector_symbol,'XLK');assert.equal(cached.source_cache.status,'hit');assert.equal(cached.source_cache.provider_requests_this_call,0);assert.equal(requests.length,12);
    assert.equal(cached.source.observed_at,value.source.observed_at);assert.equal(cached.source.first_seen_at,value.source.first_seen_at);assert.equal(cached.features.sector_flow_z,cached.source.source_rows.XLK.flow.z);
    assert.equal(cached.calculator_result.status,'research_only_score');assert.deepEqual(cached.calculator_result,evaluateForecastEngine('FE06',cached.features));
    assert.ok(cached.source_cache.stored_result_bytes>0&&cached.source_cache.stored_result_bytes<=262144);assert.equal(api.runtime.cache.size,1);
    for(const symbol of ['XLC','XLY','XLP','XLE','XLV','XLI','XLB','XLRE','XLU']){
      const response=await api.produce(new Request(`https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=${symbol}`,{headers:{'cf-connecting-ip':'198.51.100.10'}}),{engine_id:'FE06',symbol},{ALPACA_API_KEY_ID:'synthetic',ALPACA_API_SECRET_KEY:'synthetic'});
      const target=await response.json();assert.equal(response.status,200);assert.equal(target.target_sector_symbol,symbol);assert.equal(target.source_cache.status,'hit');assert.equal(target.features.sector_flow_z,target.source.source_rows[symbol].flow.z);
    }
    assert.equal(requests.length,12);assert.equal(api.runtime.ingressRates.get('198.51.100.10').count,11);
    for(let i=0;i<3;i++){api.runtime.cache.clear();const response=await api.produce(new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLF',{headers:{'cf-connecting-ip':'198.51.100.10'}}),{engine_id:'FE06',symbol:'XLF'},{ALPACA_API_KEY_ID:'synthetic',ALPACA_API_SECRET_KEY:'synthetic'});assert.equal(response.status,200);}
    api.runtime.cache.clear();const limited=await api.produce(new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLF',{headers:{'cf-connecting-ip':'198.51.100.10'}}),{engine_id:'FE06',symbol:'XLF'},{ALPACA_API_KEY_ID:'synthetic',ALPACA_API_SECRET_KEY:'synthetic'});
    assert.equal(limited.status,429);assert.equal((await limited.json()).error,'cold_source_rate_limited');assert.equal(requests.length,48);
  }finally{
    api.resetRuntime();globalThis.Date=RealDate;globalThis.fetch=RealFetch;
    if(RealJson===undefined)delete globalThis.json;else globalThis.json=RealJson;
    if(RealResearchResponse===undefined)delete globalThis.researchResponse;else globalThis.researchResponse=RealResearchResponse;
    if(RealLogic===undefined)delete globalThis.SHIPYARD_FORECAST_LOGIC;else globalThis.SHIPYARD_FORECAST_LOGIC=RealLogic;
  }
});

test('FE06 coalesces identical in-flight panels across target symbols and cleans up failed acquisitions',async()=>{
  const RealDate=globalThis.Date,RealFetch=globalThis.fetch,RealJson=globalThis.json,RealResearchResponse=globalThis.researchResponse,RealLogic=globalThis.SHIPYARD_FORECAST_LOGIC;
  const evaluationMs=Date.parse('2026-10-31T12:00:00.000Z'),dates=fe06Dates(),books=fe06UniverseBooks(),requests=[];let failCalendar=false;
  class ClockDate extends RealDate{constructor(...args){super(...(args.length?args:[evaluationMs]));}static now(){return evaluationMs;}}
  api.resetRuntime();globalThis.Date=ClockDate;globalThis.SHIPYARD_FORECAST_LOGIC={evaluateForecastEngine};globalThis.json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});globalThis.researchResponse=(value,status=200)=>globalThis.json(value,status);
  globalThis.fetch=async(input,options)=>{const url=new URL(input);requests.push(url.href);await new Promise(resolve=>setTimeout(resolve,2));if(url.hostname==='paper-api.alpaca.markets'){if(failCalendar)return new Response('upstream unavailable',{status:503});return new Response(JSON.stringify(fe06SourceCalendar(dates)),{status:200});}
    const ticker=/-([a-z]{3,4})\.xlsx$/i.exec(url.pathname)?.[1]?.toUpperCase();assert.ok(ticker&&books[ticker]);return new Response(books[ticker],{status:200});};
  const env={ALPACA_API_KEY_ID:'synthetic',ALPACA_API_SECRET_KEY:'synthetic'};
  try{
    const xlf=api.produce(new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLF',{headers:{'cf-connecting-ip':'198.51.100.20'}}),{engine_id:'FE06',symbol:'XLF'},env);
    const xlk=api.produce(new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLK',{headers:{'cf-connecting-ip':'198.51.100.21'}}),{engine_id:'FE06',symbol:'XLK'},env);
    const [r1,r2]=await Promise.all([xlf,xlk]),[v1,v2]=await Promise.all([r1.json(),r2.json()]);
    assert.equal(r1.status,200);assert.equal(r2.status,200);assert.equal(requests.length,12);assert.equal(v1.target_sector_symbol,'XLF');assert.equal(v2.target_sector_symbol,'XLK');
    assert.equal(v1.source_cache.status,'miss');assert.equal(v2.source_cache.status,'inflight_coalesced');assert.equal(v2.source_cache.provider_requests_this_call,0);assert.equal(api.runtime.inflight.size,0);assert.equal(api.runtime.cache.size,1);
    api.resetRuntime();requests.length=0;failCalendar=true;
    const failed=await api.produce(new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLF',{headers:{'cf-connecting-ip':'198.51.100.22'}}),{engine_id:'FE06',symbol:'XLF'},env);
    assert.equal(failed.status,503);assert.equal(api.runtime.inflight.size,0);assert.equal(api.runtime.cache.size,0);
    failCalendar=false;const retried=await api.produce(new Request('https://owner.test/api/research/forecast/from-sources?engine_id=FE06&symbol=XLF',{headers:{'cf-connecting-ip':'198.51.100.22'}}),{engine_id:'FE06',symbol:'XLF'},env);
    assert.equal(retried.status,200);assert.equal(requests.length,13);assert.equal(api.runtime.cache.size,1);
  }finally{api.resetRuntime();globalThis.Date=RealDate;globalThis.fetch=RealFetch;if(RealJson===undefined)delete globalThis.json;else globalThis.json=RealJson;if(RealResearchResponse===undefined)delete globalThis.researchResponse;else globalThis.researchResponse=RealResearchResponse;if(RealLogic===undefined)delete globalThis.SHIPYARD_FORECAST_LOGIC;else globalThis.SHIPYARD_FORECAST_LOGIC=RealLogic;}
});

test('FE06 derived cache expires at NY-date boundary and never grows beyond bounded memory',()=>{
  api.resetRuntime();const base={status:'computed',source:{observed_at:'2026-10-31T20:00:00.000Z',freshness_expires_at:'2026-11-02T20:00:00.000Z'}};
  for(let i=0;i<6;i++){const instant=Date.parse('2026-10-31T12:00:00Z')+i*86400000;api.cachePut('cache-key-'+i,base,instant);}
  assert.ok(api.runtime.cache.size<=4);const bytes=[...api.runtime.cache.values()].reduce((n,x)=>n+x.size_bytes,0);assert.ok(bytes<=262144);
  const before=Date.parse('2026-10-31T23:59:00Z'),key=api.cacheKey(before);api.cachePut(key,{...base,source:{...base.source,observed_at:'2026-10-31T20:00:00.000Z'}},before);
  assert.ok(api.cacheGet(key,before));assert.equal(api.cacheGet(key,Date.parse('2026-11-01T04:00:00.000Z')),null);api.resetRuntime();
});
