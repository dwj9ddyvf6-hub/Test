// Evidence-preserving parsers/builders for public SEC filing payloads.
// Bounded explicit GET acquisition lives in sec-public-capture-v1.mjs.
// These transforms never create a forecast score.
import {createHash} from 'node:crypto';
import {validateXmlWellFormedness as validateBoundedXml} from './xml-well-formedness-preflight-v1.mjs';

export const SEC_PUBLIC_ADAPTER_POLICY = Object.freeze({
  id:'SEC_PUBLIC_CAPTURE_AND_FEATURE_INPUTS_V1', version:1,
  origin:'NEW_LOCAL_ADAPTER_POLICY', network_enabled:false,
  sec_hosts:['data.sec.gov','www.sec.gov'], provider_hosts:['api.massive.com'],
  sec_fair_access_max_requests_per_second:10, local_capture_max_requests_per_second:2,
  max_json_bytes:16*1024*1024, max_company_fact_rows:100000,
  max_filing_history_rows:1000, max_form4_xml_bytes:1024*1024,
  max_filing_section_chars:1024*1024, max_filing_section_history:20,
  original_filing_input_max_age_seconds:15552000,
  feature_policy_note:'New feature transforms are experimental research inputs only. Original FE21-FE26 scorer equations and catalog contracts are not changed.',
});

const fail = code => { const e=new Error(code); e.code=code; throw e; };
const isoDate = x => typeof x==='string' && /^\d{4}-\d{2}-\d{2}$/.test(x) && Number.isFinite(Date.parse(x+'T00:00:00Z')) && new Date(Date.parse(x+'T00:00:00Z')).toISOString().slice(0,10)===x;
const isoInstant = x => {
  if(typeof x!=='string')return false;
  const m=x.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|([+-])(\d{2}):(\d{2}))$/);
  if(!m||!isoDate(m[1])||Number(m[2])>23||Number(m[3])>59||Number(m[4])>59)return false;
  if(m[5]!=='Z'&&(Number(m[7])>23||Number(m[8])>59))return false;
  return Number.isFinite(Date.parse(x));
};
const SEC_ACCEPTANCE_CLOCK_OK=new Set(['source_timestamp_explicit_timezone_unconflicted','cross_source_clock_verified']);
const ACTUAL_FINANCIAL_FORMS=new Set(['10-Q','10-Q/A','10-K','10-K/A']);
// A third-party report is tracked as an unverified conflict hypothesis, not
// as evidence of an actual source disagreement or authority for a correction.
export const REPORTED_SEC_CLOCK_CONFLICT_HYPOTHESES=Object.freeze({
  '0000320193-26-000020':{status:'reported_conflict_unverified',source:'https://github.com/dgunning/edgartools/issues/1501',
    authoritative_correction:false,independent_current_submission_json_comparison:'pending'},
});
function usableAcceptanceClock(row){
  if(!row||!SEC_ACCEPTANCE_CLOCK_OK.has(row.accepted_clock_status)||!isoInstant(row.accepted_at))return false;
  if(row.accepted_clock_status==='source_timestamp_explicit_timezone_unconflicted')return row.acceptance_clock_source_family==='SEC_SUBMISSIONS_API';
  const v=row.clock_verification;
  return row.acceptance_clock_source_family==='CROSS_SOURCE_RECONCILIATION'&&v?.status==='cross_source_agreement'&&v.accession===row.accession&&
    v.accepted_at===new Date(Date.parse(row.accepted_at)).toISOString()&&Array.isArray(v.source_receipts)&&v.source_receipts.length>=2&&
    new Set(v.source_receipts.map(r=>r.source_family)).size>=2&&v.source_receipts.every(r=>/^([0-9a-f]{64})$/.test(r.receipt_sha256??''));
}
const hash = value => createHash('sha256').update(typeof value==='string'?value:JSON.stringify(value)).digest('hex');
const finite = x => typeof x==='number' && Number.isFinite(x);
const ci = x => String(x??'').trim().toUpperCase();
const maxDate = (...xs) => xs.filter(Boolean).sort().at(-1)??null;
function bytes(text){return new TextEncoder().encode(text).length;}
function boundedJson(value, limit=SEC_PUBLIC_ADAPTER_POLICY.max_json_bytes){
  if(typeof value==='string'){
    if(bytes(value)>limit)fail('source_body_limit_exceeded');
    try{return JSON.parse(value);}catch{fail('invalid_source_json');}
  }
  if(!value || typeof value!=='object')fail('invalid_source_json');
  if(bytes(JSON.stringify(value))>limit)fail('source_body_limit_exceeded');
  return value;
}
function requireInstant(x,code='invalid_timezone_qualified_timestamp'){if(!isoInstant(x))fail(code);return new Date(Date.parse(x)).toISOString();}
function calendarDayAt(instant,timeZone){
  if(!isoInstant(instant))return null;
  const parts=new Intl.DateTimeFormat('en-US',{timeZone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(Date.parse(instant)));
  const fields=Object.fromEntries(parts.filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
  return `${fields.year}-${fields.month}-${fields.day}`;
}
function acceptancePrecedesFinancialPeriod(form,acceptedAt,periodEnd){
  if(!ACTUAL_FINANCIAL_FORMS.has(String(form??'').trim().toUpperCase())||!isoInstant(acceptedAt)||!isoDate(periodEnd))return false;
  return calendarDayAt(acceptedAt,'America/New_York')<periodEnd;
}
function requireCalendarNotBefore(instant,eventDay,code){
  if(!isoDate(eventDay))fail(code);
  let day;try{day=calendarDayAt(instant,'America/New_York');}catch{fail('evaluation_timezone_unavailable');}
  if(!day||day<eventDay)fail(code);
  return day;
}
function requireCaptureNotBeforeAcceptance(acceptedAt,capturedAt,code='capture_precedes_acceptance'){
  if(!isoInstant(acceptedAt)||!isoInstant(capturedAt))fail('capture_or_acceptance_clock_missing');
  if(Date.parse(capturedAt)<Date.parse(acceptedAt))fail(code);
}
function ymdFromDate(value){
  if(!isoDate(value))return null;
  return value;
}
function daysBetween(a,b){return (Date.parse(b+'T00:00:00Z')-Date.parse(a+'T00:00:00Z'))/86400000;}

export function secCaptureReadiness(){
  return {
    status:'bounded_public_get_path_available_provider_unverified',
    network_enabled:false, request_sent:false,request_required_for_probe:false,
    reason:'Readiness is descriptive only. An explicit caller may use the separate fixed-host, rate-limited public SEC GET adapter; this helper makes no request. Live provider connectivity and any deployed Site binding remain unverified.',
    user_agent_header:'ShipyardResearchTerminal/1.0',
    contact_value_disclosed:false,
    allowed_origins:['https://data.sec.gov','https://www.sec.gov'],
    SEC_public_max_requests_per_second:10,
    local_policy_max_requests_per_second:SEC_PUBLIC_ADAPTER_POLICY.local_capture_max_requests_per_second,
    contact_requirement:'no_contact_header_or_user_email_is_constructed_by_this_code_path',
  };
}

function accession(value){
  const s=String(value??'');
  return /^\d{10}-\d{2}-\d{6}$/.test(s)?s:null;
}
function rowArrays(recent){
  if(!recent||typeof recent!=='object')fail('missing_submission_recent');
  const needed=['accessionNumber','filingDate','form','acceptanceDateTime'];
  const arrays={};
  for(const key of needed){if(!Array.isArray(recent[key]))fail('missing_submission_column_'+key);arrays[key]=recent[key];}
  for(const key of ['reportDate','primaryDocument'])arrays[key]=Array.isArray(recent[key])?recent[key]:Array(recent.accessionNumber.length).fill('');
  const n=arrays.accessionNumber.length;
  if(n>SEC_PUBLIC_ADAPTER_POLICY.max_filing_history_rows)fail('submission_row_limit_exceeded');
  if(Object.values(arrays).some(v=>v.length!==n))fail('submission_column_length_mismatch');
  return {arrays,n};
}
export function parseSecSubmissions(input,{as_of=null,additional_history=[],clock_conflicts=[],clock_verifications={}}={}){
  try{
    const payload=boundedJson(input), cikRaw=payload.cik??payload.submissions?.cik??payload.filings?.cik;
    const cik=normalizedCik(cikRaw,'invalid_submission_cik');
    const {arrays,n}=rowArrays(payload.filings?.recent);
    const rows=[]; const seen=new Set();
    const append=(r,fromRecent=false)=>{
      const acc=accession(r.accessionNumber??r.accession_number); if(!acc)fail('invalid_accession_number');
      if(acc.slice(0,10)!==cik)fail('accession_cik_mismatch');
      if(seen.has(acc))fail('duplicate_accession'); seen.add(acc);
      const filed=ymdFromDate(r.filingDate??r.filing_date), report=ymdFromDate(r.reportDate??r.report_date)||null;
      const form=String(r.form??r.type??'').trim().toUpperCase();
      if(!filed)fail('invalid_filing_date');
      const rawAccepted=String(r.acceptanceDateTime??r.acceptance_datetime??'');
      const reportedClockHypothesis=REPORTED_SEC_CLOCK_CONFLICT_HYPOTHESES[acc]??null;
      const verificationCandidate=clock_verifications&&typeof clock_verifications==='object'?clock_verifications[acc]:null;
      const verification=clockVerificationsRecord(clock_verifications,acc);
      const sourceQualifiedClock=isoInstant(rawAccepted)?new Date(Date.parse(rawAccepted)).toISOString():null;
      const verifiedClockDisagrees=!!verification&&!!sourceQualifiedClock&&Math.abs(Date.parse(verification.accepted_at)-Date.parse(sourceQualifiedClock))>1000;
      const clockConflict=(Array.isArray(clock_conflicts)&&clock_conflicts.includes(acc))||verificationCandidate?.status==='conflict_unknown'||verifiedClockDisagrees;
      const candidateAcceptedAt=!clockConflict?(verification?.accepted_at||sourceQualifiedClock):null;
      const chronologyConflict=acceptancePrecedesFinancialPeriod(form,candidateAcceptedAt,report);
      const acceptedAt=chronologyConflict?null:candidateAcceptedAt;
      rows.push({cik,accession:acc,form,filing_date:filed,period_end:report,
        accepted_at:acceptedAt,accepted_clock_text:rawAccepted,source_family:'SEC_SUBMISSIONS_API',
        accepted_clock_status:clockConflict?'cross_source_clock_conflict_quarantined':chronologyConflict?'acceptance_precedes_period_end_quarantined':verification?'cross_source_clock_verified':sourceQualifiedClock?'source_timestamp_explicit_timezone_unconflicted':rawAccepted?'timezone_unknown_not_usable_as_availability_clock':'acceptance_timestamp_missing',
        availability_chronology_status:chronologyConflict?'acceptance_precedes_financial_period_end':ACTUAL_FINANCIAL_FORMS.has(form)&&report&&candidateAcceptedAt?'acceptance_on_or_after_financial_period_end':ACTUAL_FINANCIAL_FORMS.has(form)&&report?'unknown_acceptance_period_chronology':'not_applicable_or_period_unknown',
        reported_clock_conflict_hypothesis:reportedClockHypothesis,
        historical_point_in_time_claim:false,
        acceptance_clock_source_family:verification?'CROSS_SOURCE_RECONCILIATION':'SEC_SUBMISSIONS_API',
        clock_verification:verification,
        primary_document:String(r.primaryDocument??r.primary_document??''),
        amendment:/\/A$/.test(String(r.form??r.type??'')),
        available_by_as_of:as_of&&isoInstant(as_of)&&acceptedAt?Date.parse(acceptedAt)<=Date.parse(as_of):null,
        source:'SEC_submissions',from_recent_payload:fromRecent});
    };
    for(let i=0;i<n;i++)append({accessionNumber:arrays.accessionNumber[i],filingDate:arrays.filingDate[i],reportDate:arrays.reportDate[i],acceptanceDateTime:arrays.acceptanceDateTime[i],form:arrays.form[i],primaryDocument:arrays.primaryDocument[i]},true);
    if(!Array.isArray(additional_history)||additional_history.length>SEC_PUBLIC_ADAPTER_POLICY.max_filing_history_rows)fail('submission_history_limit_exceeded');
    for(const row of additional_history)append(row,false);
    if(rows.length>SEC_PUBLIC_ADAPTER_POLICY.max_filing_history_rows)fail('submission_total_row_limit_exceeded');
    rows.sort((a,b)=>String(a.accepted_at??'').localeCompare(String(b.accepted_at??''))||a.accession.localeCompare(b.accession));
    const reportedClockHypotheses=rows.filter(r=>r.reported_clock_conflict_hypothesis).map(r=>r.accession);
    return {status:'parsed',cik,rows,coverage:{recent_rows:n,additional_rows:additional_history.length,
      complete_history:additional_history.length>0?null:false,acceptance_clock_missing:rows.filter(r=>!r.accepted_at).length},
      input_sha256:hash(payload),warnings:['FILING_DATE_IS_NOT_ACCEPTANCE_TIME','SOURCE_TIMESTAMP_REQUIRES_CROSSCHECK_WHEN_CONFLICT_EXISTS',
        ...(rows.some(r=>r.availability_chronology_status==='acceptance_precedes_financial_period_end')?['ACTUAL_FINANCIAL_PERIOD_CLOCK_CONFLICT_QUARANTINED']:[]),
        ...(reportedClockHypotheses.length?['REPORTED_CLOCK_CONFLICT_HYPOTHESIS_NOT_INDEPENDENTLY_VERIFIED:'+reportedClockHypotheses.join(',')]:[]),
        'NO_NETWORK_REQUEST_PERFORMED','HISTORICAL_SUBMISSION_FILES_NOT_FETCHED']};
  }catch(error){return {status:'unavailable',error:error.code||'submission_parse_failed',network_enabled:false};}
}

function clockVerificationsRecord(map,acc){
  if(!map||typeof map!=='object')return null;
  const v=map[acc];
  if(!v||v.status!=='cross_source_agreement'||v.accession!==acc||!isoInstant(v.accepted_at)||!Array.isArray(v.records)||v.records.length<2)return null;
  if(v.records.some(r=>r?.accession!==acc||!r?.source_family||!isoInstant(r?.instant)||!/^([0-9a-f]{64})$/.test(r?.receipt_sha256??'')))return null;
  const families=[...new Set(v.records.map(r=>String(r.source_family)))].sort();
  if(families.length<2)return null;
  const checked=reconcileAcceptanceClocks(acc,v.records);
  if(checked.status!=='cross_source_agreement'||checked.accepted_at!==new Date(Date.parse(v.accepted_at)).toISOString())return null;
  return {status:v.status,accession:acc,accepted_at:checked.accepted_at,source_families:families,source_receipts:v.records.map(r=>({source_family:r.source_family,receipt_sha256:r.receipt_sha256})).sort((a,b)=>a.source_family.localeCompare(b.source_family))};
}

// A cross-provider/date-page disagreement is a provenance conflict, not a timezone
// conversion problem. Keep each raw value and return no canonical instant on conflict.
export function reconcileAcceptanceClocks(accessionId,records){
  if(!accession(accessionId)||!Array.isArray(records)||records.length<2||records.length>8)
    return {status:'unknown_insufficient_independent_clocks',accession:accession(accessionId),accepted_at:null,records:Array.isArray(records)?records:[]};
  const parsed=records.map(r=>({accession:String(r?.accession??''),source_family:String(r?.source_family??''),receipt_sha256:String(r?.receipt_sha256??''),raw_clock:String(r?.raw_clock??''),
    instant:isoInstant(r?.raw_clock)?new Date(Date.parse(r.raw_clock)).toISOString():null}));
  if(parsed.some(r=>r.accession!==accessionId||!r.source_family||!/^([0-9a-f]{64})$/.test(r.receipt_sha256)))
    return {status:'unknown_source_identity_or_receipt_missing',accession:accessionId,accepted_at:null,records:parsed};
  if(new Set(parsed.map(r=>r.source_family)).size<2)
    return {status:'unknown_insufficient_independent_source_families',accession:accessionId,accepted_at:null,records:parsed};
  if(parsed.some(r=>!r.instant))return {status:'unknown_timezone_or_timestamp_basis',accession:accessionId,accepted_at:null,records:parsed};
  const ticks=parsed.map(r=>Date.parse(r.instant)),min=Math.min(...ticks),max=Math.max(...ticks);
  if(max-min>1000)return {status:'conflict_unknown',accession:accessionId,accepted_at:null,records:parsed};
  return {status:'cross_source_agreement',accession:accessionId,accepted_at:new Date(min).toISOString(),records:parsed};
}

// Candidate standard-tag families only. They require a versioned taxonomy review before use.
export const SEC_XBRL_CANDIDATE_TAGS = Object.freeze({
  revenue:['RevenueFromContractWithCustomerExcludingAssessedTax','SalesRevenueNet','Revenues'],
  net_income:['NetIncomeLoss'],
  cash_from_operations:['NetCashProvidedByUsedInOperatingActivities'],
  receivables_current:['AccountsReceivableNetCurrent'],
  deferred_revenue_total:['ContractWithCustomerLiability'],
  capex_outflow:['PaymentsToAcquirePropertyPlantAndEquipment'],
  issuer_shares_outstanding:['EntityCommonStockSharesOutstanding'],
});
const candidateTagSet=new Set(Object.values(SEC_XBRL_CANDIDATE_TAGS).flat());
export function parseSecCompanyFacts(input,submissions,{as_of=null,max_fact_rows=SEC_PUBLIC_ADAPTER_POLICY.max_company_fact_rows}={}){
  try{
    const payload=boundedJson(input), facts=payload.facts?.['us-gaap'];
    if(!facts||typeof facts!=='object')fail('missing_standard_us_gaap_facts');
    if(!Array.isArray(submissions))fail('submission_accession_index_required');
    if(!isoInstant(as_of))fail('evaluation_clock_required');
    if(!Number.isInteger(max_fact_rows)||max_fact_rows<1||max_fact_rows>SEC_PUBLIC_ADAPTER_POLICY.max_company_fact_rows)fail('invalid_fact_row_limit');
    const cik=normalizedCik(payload.cik,'invalid_companyfacts_cik');
    const filingMap=new Map(submissions.map(r=>[r.accession,r]));
    const rows=[];let seen=0;
    for(const tag of candidateTagSet){
      const concept=facts[tag]; if(!concept?.units||typeof concept.units!=='object')continue;
      for(const [unit,arr] of Object.entries(concept.units)){
        if(!Array.isArray(arr))continue;
        for(const fact of arr){
          if(++seen>max_fact_rows)fail('company_fact_row_limit_exceeded');
          const accessionId=accession(fact.accn), filing=accessionId?filingMap.get(accessionId):null;
          const end=ymdFromDate(fact.end), hasStart=Object.hasOwn(fact,'start'), rawStart=fact.start, start=hasStart?ymdFromDate(rawStart):null, val=fact.val;
          if(hasStart&&!start)fail('invalid_companyfacts_start_date');
          if(!accessionId||!end||!finite(val))continue;
          if(accessionId.slice(0,10)!==cik)fail('companyfacts_accession_cik_mismatch');
          const form=String(fact.form??filing?.form??'').trim().toUpperCase();
          const filingMetadataMatch=!!filing&&(!fact.form||fact.form===filing.form)&&(!fact.filed||fact.filed===filing.filing_date);
          const clockValid=filingMetadataMatch&&usableAcceptanceClock(filing);
          const candidateAcceptedAt=clockValid?filing.accepted_at:null;
          const accessionChronologyConflict=filing?.availability_chronology_status==='acceptance_precedes_financial_period_end';
          const factChronologyConflict=acceptancePrecedesFinancialPeriod(form,candidateAcceptedAt,end);
          const chronologyConflict=accessionChronologyConflict||factChronologyConflict;
          const acceptedAt=chronologyConflict?null:candidateAcceptedAt;
          const timeStatus=chronologyConflict?'acceptance_precedes_period_end_quarantined':clockValid?filing.accepted_clock_status:filingMetadataMatch?'unknown_accession_acceptance_time':'filing_metadata_mismatch';
        rows.push({cik,taxonomy:'us-gaap',taxonomy_version:'not_provided_by_companyfacts_payload',tag,
            tag_family:Object.keys(SEC_XBRL_CANDIDATE_TAGS).find(k=>SEC_XBRL_CANDIDATE_TAGS[k].includes(tag))||null,
            mapping_status:'candidate_tag_requires_taxonomy_review',unit,value:val,period_kind:start?'duration':'instant',period_start:start,period_end:end,
            accession:accessionId,form,fy:fact.fy??null,fp:fact.fp??null,
            filing_date:ymdFromDate(fact.filed)||filing?.filing_date||null,accepted_at:usableAcceptanceClock(filing)&&!chronologyConflict?acceptedAt:null,
            acceptance_clock_raw_text:filing?.accepted_clock_text??filing?.accepted_at??null,availability_clock_status:timeStatus,
            availability_chronology_status:chronologyConflict?'acceptance_precedes_financial_period_end':ACTUAL_FINANCIAL_FORMS.has(form)&&clockValid?'acceptance_on_or_after_financial_period_end':ACTUAL_FINANCIAL_FORMS.has(form)?'unknown_acceptance_period_chronology':'not_applicable_nonfinancial_form',
            acceptance_clock_source_family:clockValid?filing.acceptance_clock_source_family:null,clock_verification:clockValid?filing?.clock_verification??null:null,
            available_by_as_of:acceptedAt&&!chronologyConflict?Date.parse(acceptedAt)<=Date.parse(as_of):null,
            filing_metadata_match:filingMetadataMatch,
            frame:typeof fact.frame==='string'?fact.frame:null,dimensions_included:false,source:'SEC_companyfacts'});
        }
      }
    }
    return {status:'parsed',cik,entity_name:String(payload.entityName??''),rows,
      coverage:{candidate_rows:rows.length,scanned_fact_rows:seen,standard_namespace_only:true,custom_tags_included:false,
        accession_join_coverage:rows.length?rows.filter(r=>r.accepted_at).length/rows.length:0},
      warnings:['COMPANYFACTS_EXCLUDES_CUSTOM_TAXONOMIES_AND_DIMENSIONAL_FACTS','TAXONOMY_VERSION_NOT_PRESENT','CANDIDATE_TAG_MAP_NOT_REVIEWED','ACCESSION_ACCEPTANCE_JOIN_REQUIRED',
        ...(rows.some(r=>r.availability_chronology_status==='acceptance_precedes_financial_period_end')?['ACTUAL_FINANCIAL_FACT_PERIOD_CLOCK_CONFLICT_QUARANTINED']:[]),
        'NO_NETWORK_REQUEST_PERFORMED']};
  }catch(error){return {status:'unavailable',error:error.code||'companyfacts_parse_failed',network_enabled:false};}
}

const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
function zAgainstPrior(current,prior){
  if(!finite(current)||prior.length!==8||prior.some(x=>!finite(x)))return {status:'unknown',value:null,reason:'eight_prior_valid_observations_required'};
  const avg=mean(prior),sd=Math.sqrt(mean(prior.map(x=>(x-avg)**2)));
  if(!finite(sd)||sd<=1e-12)return {status:'unknown',value:null,reason:'zero_or_degenerate_prior_normalizer'};
  return {status:'measured',value:(current-avg)/sd,current,prior_mean:avg,prior_population_sd:sd,prior_count:8,population_ddof:0};
}
const featureUnknown=reason=>({status:'unknown',value:null,reason});

export const FE21_XBRL_TRANSFORM_POLICY=Object.freeze({
  id:'FE21_SEC_QUARTERLY_CASH_QUALITY_PRIOR8_V1',origin:'NEW_FEATURE_POLICY',
  quarterly_basis:'single-quarter values only; YTD subtraction and restated comparatives are not inferred by this builder',
  cash_conversion:'CFO / positive net income; z against eight immediately prior quarterly ratios',
  receivables_growth_gap:'ln(AR_t/AR_t-4) - ln(Revenue_t/Revenue_t-4); z against eight prior values',
  deferred_revenue_change:'ln(DeferredRevenue_t/DeferredRevenue_t-4) - ln(Revenue_t/Revenue_t-4); requires an explicit total deferred-revenue tag; z against prior eight',
  fcf_acceleration:'(CFO-capex_outflow)/revenue minus the corresponding margin four quarters earlier; z against prior eight',
  units:'USD amounts from one accession per quarter; no cross-currency or silent tag aliasing; USD ratios are dimensionless',
  normalizer:'population SD, prior eight only; no epsilon, fill, or current observation in reference sample',
  abstain:'missing/unverified taxonomy map, ambiguous amendment, noncomparable quarter, or degenerate denominator => null field',
  score:'not called; original FE21 coefficients remain untouched',
});

export function buildFE21PublicInputs(periods,as_of){
  const base={engine_id:'FE21',feature_origin:'new_sec_xbrl_feature_policy',policy:FE21_XBRL_TRANSFORM_POLICY,
    score_called:false,decision_eligible:false,calibrated_probability:null};
  try{
    if(!Array.isArray(periods)||periods.length>20||periods.length<13)fail('thirteen_comparable_quarters_required');
    const cutoff=requireInstant(as_of,'evaluation_clock_required');
    const data=periods.map(q=>{
      const start=ymdFromDate(q?.period_start),end=ymdFromDate(q?.period_end),accepted=requireInstant(q?.accepted_at,'quarter_acceptance_clock_required'),captured=requireInstant(q?.captured_at,'quarter_capture_clock_required');
      if(!usableAcceptanceClock(q))fail('quarter_acceptance_clock_source_contract_unverified');
      if(!start||!end||start>end||daysBetween(start,end)<60||daysBetween(start,end)>125)fail('not_single_quarter_duration');
      if(accepted>cutoff)fail('future_filing_not_available_at_cutoff');
      if(captured>cutoff)fail('source_capture_after_cutoff');
      requireCaptureNotBeforeAcceptance(accepted,captured);
      requireCalendarNotBefore(accepted,end,'acceptance_precedes_period_end');
      if(end>cutoff.slice(0,10))fail('future_report_period_not_available_at_cutoff');
      if(q?.quarter_basis!=='single_quarter')fail('ytd_or_derived_quarter_not_accepted');
      if(q?.taxonomy_mapping_verified!==true||typeof q?.taxonomy_map_id!=='string'||!q.taxonomy_map_id)fail('taxonomy_mapping_unverified');
      if(q?.amendment_status!=='clear')fail('amendment_or_restating_vintage_ambiguous');
      if(!accession(q?.accession))fail('accession_identity_required');
      if(!['10-Q','10-K'].includes(q?.form))fail('unsupported_filing_form');
      if(q?.currency!=='USD'||q?.amount_unit!=='USD')fail('same_currency_usd_required');
      const vals=['revenue_usd','cfo_usd','net_income_usd','receivables_usd','deferred_revenue_total_usd','capex_outflow_usd'];
      if(vals.some(k=>!finite(q[k])))fail('required_xbrl_component_missing');
      if(q.revenue_usd<=0||q.net_income_usd<=0||q.receivables_usd<=0||q.deferred_revenue_total_usd<=0||q.capex_outflow_usd<0)fail('nonpositive_or_invalid_denominator');
      return {...q,period_start:start,period_end:end,accepted_at:accepted,captured_at:captured};
    });
    const tagKeys=['capex_outflow','cfo','deferred_revenue_total','net_income','receivables_current','revenue'];
    const familyByField={revenue:'revenue',cfo:'cash_from_operations',net_income:'net_income',receivables_current:'receivables_current',
      deferred_revenue_total:'deferred_revenue_total',capex_outflow:'capex_outflow'};
    const tagSignature=q=>JSON.stringify(Object.entries(q.component_fact_tags??{}).sort(([a],[b])=>a.localeCompare(b)));
    const tagSignature0=tagSignature(data[0]);
    if(!/^\d{10}$/.test(String(data[0].issuer_cik??''))||data[0].issuer_cik==='0000000000'||tagKeys.some(k=>typeof data[0].component_fact_tags?.[k]!=='string'||
      !SEC_XBRL_CANDIDATE_TAGS[familyByField[k]].includes(data[0].component_fact_tags[k])))fail('issuer_identity_or_component_tag_map_missing_or_unreviewed');
    for(const q of data){
      if(q.issuer_cik!==data[0].issuer_cik||!q.accession.startsWith(data[0].issuer_cik))fail('cross_issuer_period_history');
      if(q.taxonomy_map_id!==data[0].taxonomy_map_id||tagSignature(q)!==tagSignature0)fail('taxonomy_mapping_vintage_changed');
    }
    if(new Set(data.map(q=>q.accession)).size!==data.length)fail('duplicate_quarter_accession');
    for(let i=1;i<data.length;i++){
      if(data[i].period_end<=data[i-1].period_end||daysBetween(data[i-1].period_end,data[i].period_end)<70||daysBetween(data[i-1].period_end,data[i].period_end)>115)fail('quarter_grid_gap_or_duplicate');
      if(data[i].period_start!==new Date(Date.parse(data[i-1].period_end+'T00:00:00Z')+86400000).toISOString().slice(0,10))fail('noncontiguous_fiscal_periods');
    }
    if((Date.parse(cutoff)-Date.parse(data.at(-1).accepted_at))/1000>SEC_PUBLIC_ADAPTER_POLICY.original_filing_input_max_age_seconds)fail('feature_source_exceeds_original_max_age');
    const metric={cash_conversion:[],receivables_gap:[],deferred_change:[],fcf_margin:[]};
    for(let i=0;i<data.length;i++){
      const q=data[i], fcf=(q.cfo_usd-q.capex_outflow_usd)/q.revenue_usd;
      metric.cash_conversion.push(q.cfo_usd/q.net_income_usd); metric.fcf_margin.push(fcf);
      if(i>=4){const y=data[i-4];
        metric.receivables_gap.push(Math.log(q.receivables_usd/y.receivables_usd)-Math.log(q.revenue_usd/y.revenue_usd));
        metric.deferred_change.push(Math.log(q.deferred_revenue_total_usd/y.deferred_revenue_total_usd)-Math.log(q.revenue_usd/y.revenue_usd));
      }else{metric.receivables_gap.push(null);metric.deferred_change.push(null);}
    }
    const t=data.length-1, prior8=(xs,offset=0)=>xs.slice(t-8+offset,t+offset);
    const latestGap=metric.receivables_gap[t],latestDef=metric.deferred_change[t];
    const fcfAccel=metric.fcf_margin[t]-metric.fcf_margin[t-4];
    const fcfHistory=Array.from({length:8},(_,j)=>metric.fcf_margin[t-8+j]-metric.fcf_margin[t-12+j]);
    const fields={
      cash_conversion_z:zAgainstPrior(metric.cash_conversion[t],metric.cash_conversion.slice(t-8,t)),
      receivables_growth_gap_z:zAgainstPrior(latestGap,metric.receivables_gap.slice(t-8,t)),
      deferred_revenue_change_z:zAgainstPrior(latestDef,metric.deferred_change.slice(t-8,t)),
      fcf_acceleration_z:zAgainstPrior(fcfAccel,fcfHistory),
    };
    const complete=Object.values(fields).every(f=>f.status==='measured');
    return {...base,status:complete?'inputs_ready_new_policy':'partial_unknown_fields',feature_policy_id:FE21_XBRL_TRANSFORM_POLICY.id,
      features:complete?Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.value])):null,fields,
      source:{accessions:data.map(q=>q.accession),period_range:{start:data[0].period_start,end:data.at(-1).period_end},accepted_at_latest:data.at(-1).accepted_at,
        latest_available_age_seconds:(Date.parse(cutoff)-Date.parse(data.at(-1).accepted_at))/1000,
        captured_at:maxDate(...data.map(q=>q.captured_at)),taxonomy_mapping_verified:true,issuer_cik:data.at(-1).issuer_cik??null,
        component_fact_tags:data.at(-1).component_fact_tags??null,historical_point_in_time_claim:false},
      warnings:['NEW_POLICY_NOT_ORIGINAL_ENGINE_BUILDER','REQUIRES_EXTERNAL_TAXONOMY_REVIEW_AND_SOURCE_RIGHTS','QUARTERLY_YTD_FACTS_NOT_AUTOMATICALLY_DIFFERENCED','NO_SCORE_OR_DECISION_ELIGIBILITY']};
  }catch(error){return {...base,status:'unavailable',error:error.code||'feature_build_failed',features:null,fields:{
      cash_conversion_z:featureUnknown(error.code||'feature_build_failed'),receivables_growth_gap_z:featureUnknown(error.code||'feature_build_failed'),
      deferred_revenue_change_z:featureUnknown(error.code||'feature_build_failed'),fcf_acceleration_z:featureUnknown(error.code||'feature_build_failed')}};}
}

const STOP=new Set('a an and are as at be by for from has have in into is it its of on or our that the their this to was were will with we you your about after all also any can could during each had how if may more most not other should such than them these they those through under until upon what when where which while who why would'.split(' '));
const POS=new Set(['accelerate','accelerated','accelerating','benefit','beneficial','expand','expanded','expansion','favorable','growth','improve','improved','improving','increase','increased','profitable','record','resilient','strong','success']);
const NEG=new Set(['adverse','decline','declined','decrease','decreased','default','delay','deteriorate','deterioration','impairment','litigation','loss','risk','shortage','uncertain','uncertainty','weak','weakness']);
function sectionTokens(text){
  if(typeof text!=='string'||text.length<500||text.length>SEC_PUBLIC_ADAPTER_POLICY.max_filing_section_chars)fail('section_text_length_invalid');
  if(/<\/?[A-Za-z][^>]*>|\[truncated\]/i.test(text))fail('section_text_not_clean_or_truncated');
  const words=text.normalize('NFKC').toLowerCase().match(/[\p{L}]{2,}/gu)||[];
  if(words.length<100||words.length>200000)fail('section_token_count_invalid');
  const filtered=words.filter(w=>!STOP.has(w)); if(filtered.length<50)fail('section_content_too_sparse');
  return filtered;
}
function cosine(a,b){
  const dot=0; const aa=new Map(),bb=new Map(); for(const x of a)aa.set(x,(aa.get(x)||0)+1); for(const x of b)bb.set(x,(bb.get(x)||0)+1);
  let d=0,na=0,nb=0; for(const [k,v] of aa){na+=v*v;d+=v*(bb.get(k)||0);} for(const v of bb.values())nb+=v*v;
  if(!na||!nb)return null; return Math.max(0,Math.min(1,d/Math.sqrt(na*nb)));
}
function lexicalTone(tokens){let p=0,n=0;for(const w of tokens){if(POS.has(w))p++;if(NEG.has(w))n++;}return 1000*(p-n)/tokens.length;}
export const FE22_LEXICAL_POLICY=Object.freeze({id:'FE22_SECTION_LEXICAL_CHANGE_PRIOR8_V1',origin:'NEW_LEXICAL_PROXY_NOT_SEMANTIC_MODEL',
  source_sections:['business','risk_factors'],scope:'matched same-issuer, same-form, same-section, same parser; 10-K history only in this implementation',
  semantic_delta:'lexicon polarity delta per 1000 non-stopword tokens; z against eight prior matched filing-to-filing deltas',
  novelty:'1 minus bag-of-words cosine similarity to previous matched section; bounded [0,1]',
  parser_confidence:'only 1 when source explicitly attests complete section extraction, parser hash is present, and no markup/truncation checks fail; otherwise unknown',
  section_relevance:'1 for declared SEC business/risk_factors sections only; not an analyst or model confidence',
  lexicon:{positive:[...POS].sort(),negative:[...NEG].sort()}, stopwords_sha256:hash([...STOP].sort()),
  score:'not called; lexical proxy cannot be described as an NLP semantic model'});
export function buildFE22PublicInputs(documents,as_of){
  const base={engine_id:'FE22',feature_origin:'new_public_filing_lexical_proxy',score_called:false,decision_eligible:false,calibrated_probability:null,policy:FE22_LEXICAL_POLICY};
  try{
    if(!Array.isArray(documents)||documents.length>SEC_PUBLIC_ADAPTER_POLICY.max_filing_section_history||documents.length<10)fail('ten_matched_filings_required');
    const cutoff=requireInstant(as_of,'evaluation_clock_required'), rows=documents.map(d=>{
      if(!/^(10-K|10-Q)$/.test(d?.form)||!['business','risk_factors'].includes(d?.section_id))fail('unsupported_document_or_section');
      if(d.form!=='10-K')fail('quarterly_semantic_policy_not_defined');
      const accessionId=accession(d?.accession), period=ymdFromDate(d?.period_end), accepted=requireInstant(d?.accepted_at,'section_acceptance_clock_required'),captured=requireInstant(d?.captured_at,'section_capture_clock_required');
      if(!usableAcceptanceClock(d))fail('section_acceptance_clock_source_contract_unverified');
      if(!accessionId||!period||accepted>cutoff)fail('filing_identity_or_point_in_time_failure');
      if(captured>cutoff)fail('source_capture_after_cutoff');
      requireCaptureNotBeforeAcceptance(accepted,captured);
      requireCalendarNotBefore(accepted,period,'acceptance_precedes_period_end');
      if(period>cutoff.slice(0,10))fail('future_report_period_not_available_at_cutoff');
      if(d?.section_extract_complete!==true||typeof d?.parser_sha256!=='string'||!/^([0-9a-f]{64})$/.test(d.parser_sha256))fail('section_parser_evidence_missing');
      if(d?.amendment_status!=='clear')fail('section_amendment_vintage_ambiguous');
      const tokens=sectionTokens(d.text);
      return {...d,accession:accessionId,period_end:period,accepted_at:accepted,captured_at:captured,tokens,tone:lexicalTone(tokens)};
    });
    const first=rows[0];
    if(!/^\d{10}$/.test(String(first.issuer_cik??''))||first.issuer_cik==='0000000000'||rows.some(d=>!d.accession.startsWith(first.issuer_cik)))fail('section_issuer_or_accession_identity_invalid');
    if(new Set(rows.map(d=>d.accession)).size!==rows.length)fail('duplicate_filing_accession');
    for(let i=0;i<rows.length;i++){
      const d=rows[i];if(d.issuer_cik!==first.issuer_cik||d.form!==first.form||d.section_id!==first.section_id||d.parser_sha256!==first.parser_sha256)fail('section_identity_mismatch');
      if(i&& (d.period_end<=rows[i-1].period_end || daysBetween(rows[i-1].period_end,d.period_end)<330 || daysBetween(rows[i-1].period_end,d.period_end)>400))fail('annual_section_history_gap_or_duplicate');
    }
    if((Date.parse(cutoff)-Date.parse(rows.at(-1).accepted_at))/1000>SEC_PUBLIC_ADAPTER_POLICY.original_filing_input_max_age_seconds)fail('feature_source_exceeds_original_max_age');
    const deltas=rows.slice(1).map((d,i)=>d.tone-rows[i].tone), currentDelta=deltas.at(-1), novelty=1-(cosine(rows.at(-1).tokens,rows.at(-2).tokens)??0);
    const z=zAgainstPrior(currentDelta,deltas.slice(-9,-1));
    const fields={semantic_delta_z:z,parser_confidence:{status:'measured',value:1,reason:'complete section extract attested; parser content passed size/markup/truncation checks',parser_sha256:first.parser_sha256},
      novelty_score:{status:'measured',value:Math.max(0,Math.min(1,novelty)),reason:'one minus prior/current token-frequency cosine similarity'},
      section_relevance:{status:'measured',value:1,reason:'declared relevant SEC section '+first.section_id}};
    const complete=Object.values(fields).every(f=>f.status==='measured');
    return {...base,status:complete?'inputs_ready_new_policy':'partial_unknown_fields',feature_policy_id:FE22_LEXICAL_POLICY.id,
      features:complete?Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.value])):null,fields,
      source:{issuer_cik:first.issuer_cik,form:first.form,section_id:first.section_id,accessions:rows.map(r=>r.accession),period_range:{start:rows[0].period_end,end:rows.at(-1).period_end},accepted_at_latest:rows.at(-1).accepted_at,
        captured_at:maxDate(...rows.map(r=>r.captured_at)),text_sha256:rows.map(r=>hash(r.text)),parser_sha256:first.parser_sha256,historical_point_in_time_claim:false},
      warnings:['NEW_LEXICAL_PROXY_NOT_ORIGINAL_SEMANTIC_MODEL','FILING_TEXT_VINTAGES_MUST_BE_SOURCE_VERIFIED','NO_SCORE_OR_DECISION_ELIGIBILITY']};
  }catch(error){return {...base,status:'unavailable',error:error.code||'feature_build_failed',fields:{
      semantic_delta_z:featureUnknown(error.code||'feature_build_failed'),parser_confidence:featureUnknown(error.code||'feature_build_failed'),
      novelty_score:featureUnknown(error.code||'feature_build_failed'),section_relevance:featureUnknown(error.code||'feature_build_failed')}};}
}

function parseForm4XmlTree(xml){
  if(typeof xml!=='string'||bytes(xml)>SEC_PUBLIC_ADAPTER_POLICY.max_form4_xml_bytes)fail('form4_xml_size_invalid');
  let source=xml.startsWith('\uFEFF')?xml.slice(1):xml;
  if(/<!\s*(?:DOCTYPE|ENTITY)\b|\b(?:SYSTEM|PUBLIC)\s+["']/i.test(source))fail('unsafe_xml_declaration');
  if(/<!--[\s\S]*?-->|<!\[CDATA\[/i.test(source))fail('unsupported_xml_comment_or_cdata');
  const declaration=/^<\?xml\s+version=(["'])1\.0\1(?:\s+encoding=(["'])[A-Za-z][A-Za-z0-9._-]*\2)?(?:\s+standalone=(["'])(?:yes|no)\3)?\s*\?>/;
  if(source.startsWith('<?xml')){
    const match=source.match(declaration);if(!match)fail('unsupported_xml_processing_instruction');source=source.slice(match[0].length);
  }
  if(source.includes('<?'))fail('unsupported_xml_processing_instruction');
  const tokens=source.match(/<[^>]*>|[^<]+|</g)||[];
  if(tokens.join('')!==source||tokens.length>30000)fail('malformed_or_overcomplex_xml');
  const document={name:'#document',children:[]},stack=[document];let roots=0,rootClosed=false,depthMax=0;
  const validEntities=value=>!/&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[\da-f]+);)/.test(value);
  const decodeText=value=>value.replace(/&(amp|lt|gt|quot|apos|#\d+|#x[\da-f]+);/g,(_,e)=>{
    if(e==='amp')return '&';if(e==='lt')return '<';if(e==='gt')return '>';if(e==='quot')return '"';if(e==='apos')return "'";
    const cp=e.startsWith('#x')?parseInt(e.slice(2),16):Number(e.slice(1));
    if(!Number.isInteger(cp)||cp<1||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff)||(cp<0x20&&![9,10,13].includes(cp)))fail('invalid_xml_character_reference');
    return String.fromCodePoint(cp);
  });
  for(const token of tokens){
    if(token.startsWith('<!'))fail('unsafe_xml_declaration');
    if(!token.startsWith('<')){
      if(!validEntities(token))fail('unknown_xml_entity');
      if(stack.length===1){if(token.trim())fail('xml_text_outside_root');}
      else stack.at(-1).children.push(decodeText(token));
      continue;
    }
    // XML's '<' and '</' are immediately followed by a Name. Permissive
    // whitespace here accepts non-well-formed spellings such as '< tag>' and
    // '</ tag>'; saxes validation below independently enforces XML 1.0 syntax.
    const match=token.match(/^<(\/?)((?:[A-Za-z_])[\w:.-]*)([\s\S]*?)\s*(\/?)>$/);
    if(!match)fail('malformed_xml_tag');
    const [,closing,name,tail,selfClose]=match;
    if(closing){if(tail.trim()||selfClose||stack.length===1||stack.pop().name!==name)fail('unbalanced_xml_tags');if(stack.length===1)rootClosed=true;continue;}
    if(name.includes(':'))fail('unsupported_xml_namespace_prefix');
    if(rootClosed)fail('multiple_xml_roots');
    if(stack.length===1)roots++;if(roots>1)fail('multiple_xml_roots');
    if(tail&&!/^\s/.test(tail))fail('malformed_xml_attribute');
    let rest=tail.trim();const attributeNames=new Set();
    while(rest){
      const attr=rest.match(/^([A-Za-z_:][\w:.-]*)\s*=\s*("([^"]*)"|'([^']*)')(?:\s+|$)/);
      if(!attr)fail('malformed_xml_attribute');
      if(attr[1].includes(':')||attr[1]==='xmlns')fail('unsupported_xml_namespace_declaration');
      if(attributeNames.has(attr[1]))fail('duplicate_xml_attribute');attributeNames.add(attr[1]);
      if(!validEntities(attr[3]??attr[4]??''))fail('unknown_xml_entity');
      // Validate numeric character references in attributes as rigorously as
      // references in text; otherwise &#0; could bypass the local decoder.
      decodeText(attr[3]??attr[4]??'');
      rest=rest.slice(attr[0].length).trim();
    }
    const node={name,children:[]};stack.at(-1).children.push(node);
    if(!selfClose){stack.push(node);depthMax=Math.max(depthMax,stack.length-1);if(depthMax>80)fail('xml_nesting_limit_exceeded');}
    else if(stack.length===1)rootClosed=true;
  }
  const rootsFound=document.children.filter(child=>typeof child==='object');
  if(roots!==1||stack.length!==1||!rootClosed||rootsFound.length!==1)fail('unbalanced_xml_document');
  validateXmlWellFormedness(source);
  return rootsFound[0];
}
function validateXmlWellFormedness(source){
  try{return validateBoundedXml(source,{maxBytes:SEC_PUBLIC_ADAPTER_POLICY.max_form4_xml_bytes,maxDepth:80,maxNodes:30000,
    allowDoctype:false,allowProcessingInstructions:false,allowComments:false,allowCdata:false,allowXmlDeclaration:true,rejectNamespaces:true});}
  catch(error){if(error?.code==='xml_preflight_depth_limit_exceeded')fail('xml_nesting_limit_exceeded');
    if(error?.code==='xml_preflight_node_limit_exceeded')fail('malformed_or_overcomplex_xml');
    if(error?.code==='xml_preflight_byte_limit_exceeded')fail('form4_xml_size_invalid');
    throw error;}
}
const xmlLocalName=node=>String(node?.name??'');
const xmlChildren=(node,name)=>node?.children?.filter(child=>typeof child==='object'&&xmlLocalName(child)===name)??[];
function xmlChild(node,name,{required=false}={}){
  const found=xmlChildren(node,name), normalized=name.replace(/[A-Z]/g,letter=>'_'+letter.toLowerCase());
  if(found.length>1)fail('duplicate_'+normalized);
  if(!found.length){if(required)fail('missing_'+normalized);return null;}
  return found[0];
}
function xmlText(node){
  const children=node?.children??[];
  if(children.some(child=>typeof child==='object'))fail('nested_scalar_xml_content');
  return children.filter(child=>typeof child==='string').join('').trim()||null;
}
function xmlPathText(node,path){let current=node;for(const name of path){current=xmlChild(current,name);if(!current)return null;}return xmlText(current);}
function normalizedCik(value,error){
  const raw=String(value??'').trim();if(!/^\d{1,10}$/.test(raw))fail(error);
  const cik=raw.padStart(10,'0');if(cik==='0000000000')fail(error);return cik;
}
function parsePlanFlag(raw){if(raw===null)return 'unknown';if(['1','true','y'].includes(raw.toLowerCase()))return '10b5_1';if(['0','false','n'].includes(raw.toLowerCase()))return 'not_10b5_1';return 'unknown';}
function positiveXmlDecimal(value){
  if(typeof value!=='string'||! /^(?:\d+(?:\.\d*)?|\.\d+)$/.test(value))return null;
  const number=Number(value);return finite(number)&&number>0&&number<=Number.MAX_SAFE_INTEGER?number:null;
}
export function parseSecForm4Xml(xml,filing){
  try{
    const root=parseForm4XmlTree(xml);
    if(xmlLocalName(root)!=='ownershipDocument')fail('form4_root_element_mismatch');
    const metadata=filing||{};
    const accessionId=accession(metadata.accession??metadata.accession_number);if(!accessionId)fail('accession_identity_required');
    const documentType=xmlText(xmlChild(root,'documentType',{required:true}));
    const form=String(metadata.form??documentType??'');
    if(!documentType||!['4','4/A'].includes(form)||!['4','4/A'].includes(documentType)||documentType!==form)fail('form4_document_type_mismatch');
    const issuer=xmlChild(root,'issuer',{required:true});
    const issuerCik=normalizedCik(xmlText(xmlChild(issuer,'issuerCik',{required:true})),'issuer_cik_missing');
    const symbol=ci(xmlText(xmlChild(issuer,'issuerTradingSymbol')));
    if(metadata.issuer_cik&&normalizedCik(metadata.issuer_cik,'issuer_cik_mismatch')!==issuerCik)fail('issuer_cik_mismatch');
    const reportingOwnerBlocks=xmlChildren(root,'reportingOwner');
    if(!reportingOwnerBlocks.length)fail('missing_reporting_owner');
    const ownerCiks=reportingOwnerBlocks.map(owner=>normalizedCik(xmlPathText(owner,['reportingOwnerId','rptOwnerCik']),'reporting_owner_cik_invalid'));
    if(new Set(ownerCiks).size!==ownerCiks.length)fail('duplicate_reporting_owner_cik');
    const reportingOwnerIdentityComplete=true;
    const plan=parsePlanFlag(xmlText(xmlChild(root,'aff10b5One')));
    const periodOfReport=ymdFromDate(xmlText(xmlChild(root,'periodOfReport',{required:true})));
    if(!periodOfReport)fail('invalid_form4_period_of_report');
    const rawAccepted=metadata.accepted_at??metadata.acceptance_datetime??null;
    const clockCandidate={accession:accessionId,accepted_at:rawAccepted,accepted_clock_status:metadata.accepted_clock_status,
      acceptance_clock_source_family:metadata.acceptance_clock_source_family,clock_verification:metadata.clock_verification};
    const acceptedClockValid=metadata.accepted_clock_conflict!==true&&usableAcceptanceClock(clockCandidate);
    const acceptedAt=acceptedClockValid?new Date(Date.parse(rawAccepted)).toISOString():null;
    const rejectedClockStatus=metadata.accepted_clock_status;
    const acceptedClockStatus=metadata.accepted_clock_conflict===true?'cross_source_clock_conflict_quarantined':acceptedAt?metadata.accepted_clock_status:
      ['cross_source_clock_conflict_quarantined','reported_accession_clock_quarantined','timezone_unknown_not_usable_as_availability_clock','acceptance_timestamp_missing'].includes(rejectedClockStatus)?rejectedClockStatus:
      ['source_timestamp_explicit_timezone_unconflicted','cross_source_clock_verified'].includes(rejectedClockStatus)?'source_timestamp_contract_unverified':
      rejectedClockStatus??(rawAccepted?'source_timestamp_unverified_or_timezone_unknown':'acceptance_timestamp_missing');
    const rawCaptured=metadata.captured_at??null;
    const capturedAt=isoInstant(rawCaptured)?new Date(Date.parse(rawCaptured)).toISOString():null;
    if(acceptedAt&&capturedAt)requireCaptureNotBeforeAcceptance(acceptedAt,capturedAt);
    if(acceptedAt)requireCalendarNotBefore(acceptedAt,periodOfReport,'acceptance_precedes_period_end');
    const table=xmlChild(root,'nonDerivativeTable');
    const blocks=table?xmlChildren(table,'nonDerivativeTransaction'):[];
    if(blocks.length>100)fail('form4_transaction_limit_exceeded');
    const transactions=[];
    for(let i=0;i<blocks.length;i++){
      const b=blocks[i],code=ci(xmlPathText(b,['transactionCoding','transactionCode'])??''),
        tradeDate=ymdFromDate(xmlPathText(b,['transactionDate','value'])),
        acquiredDisposed=ci(xmlPathText(b,['transactionAmounts','transactionAcquiredDisposedCode','value'])??'');
      const sharesText=xmlPathText(b,['transactionAmounts','transactionShares','value']);
      const sharesValue=positiveXmlDecimal(sharesText);
      const priceText=xmlPathText(b,['transactionAmounts','transactionPricePerShare','value']);
      const priceValue=positiveXmlDecimal(priceText);
      const direct=ci(xmlPathText(b,['ownershipNature','directOrIndirectOwnership','value'])??'');
      const security=xmlPathText(b,['securityTitle','value'])||'';
      const formCode=xmlPathText(b,['transactionCoding','transactionFormType']);
      const codingConsistent=(code==='P'&&acquiredDisposed==='A')||(code==='S'&&acquiredDisposed==='D');
      const reportedNotional=sharesValue*priceValue;
      const sourceFieldsValid=!!tradeDate&&['P','S'].includes(code)&&codingConsistent&&formCode==='4'&&finite(sharesValue)&&finite(priceValue)&&
        finite(reportedNotional)&&reportedNotional<=Number.MAX_SAFE_INTEGER;
      if(acceptedAt&&tradeDate)requireCalendarNotBefore(acceptedAt,tradeDate,'filing_acceptance_precedes_transaction_date');
      const candidate=sourceFieldsValid&&reportingOwnerIdentityComplete&&direct==='D'&&plan==='not_10b5_1'&&!/\/A$/.test(form);
      transactions.push({transaction_id:hash(accessionId+':'+i),row_index:i,accession:accessionId,issuer_cik:issuerCik,issuer_symbol:symbol||null,
        reporting_owner_ciks:ownerCiks,transaction_date:tradeDate,transaction_code:code||null,form_code:formCode,
        security_title:security||null,shares:finite(sharesValue)?sharesValue:null,price_per_share:finite(priceValue)?priceValue:null,acquired_disposed:acquiredDisposed||'unknown',
        signed_reported_notional_usd:sourceFieldsValid?(code==='P'?1:-1)*reportedNotional:null,
        direct_or_indirect:direct||'unknown',plan_status:plan,filing_form:form,accepted_at:acceptedAt,
        available_at_status:acceptedClockStatus,
        candidate_nonplan_direct_P_S:candidate,
        discretionary_status:candidate?'still_unverified_not_equivalent_to_discretionary':'unknown_or_excluded',
        inclusion_reason:candidate?'P/S, matching acquired/disposed code, identified reporting owner, direct ownership, explicit non-10b5-1 checkbox; execution venue and discretion unverified':!reportingOwnerIdentityComplete?'reporting owner identity missing or incomplete':sourceFieldsValid?'plan/ownership/amendment filter not satisfied':'ineligible or inconsistent P/S coding'});
    }
    return {status:'parsed',schema:'SHIPYARD_SEC_FORM4_LOCAL_V1',source_family:'SEC_FORM4_XML',network_enabled:false,accession:accessionId,
      issuer_cik:issuerCik,issuer_symbol:symbol||null,period_of_report:periodOfReport,
      accepted_at:acceptedAt,accepted_clock_text:rawAccepted,accepted_clock_status:acceptedClockStatus,
      reported_clock_conflict_hypothesis:REPORTED_SEC_CLOCK_CONFLICT_HYPOTHESES[accessionId]??null,
      acceptance_clock_source_family:acceptedAt?metadata.acceptance_clock_source_family:null,clock_verification:acceptedAt?metadata.clock_verification??null:null,captured_at:capturedAt,plan_status:plan,
      filing_form:form,transactions,source_sha256:hash(xml),
      coverage:{parsed_non_derivative_rows:blocks.length,form4_rows_capped:true,reporting_owner_count:ownerCiks.length,reporting_owner_identity_complete:true,derivative_table_not_used:true,
        transaction_list_complete:metadata.transaction_list_complete===true,issuer_share_class_match:metadata.share_class_verified===true},
      warnings:['FORM4_NON_10B5_1_IS_NOT_PROOF_OF_DISCRETION','PRE_2023_OR_MISSING_PLAN_FIELD_REMAINS_UNKNOWN','P_OR_S_CODE_ALONE_DOES_NOT_PROVE_NET_DISCRETIONARY_FLOW','FORM4_AMENDMENTS_RETAINED_SEPARATELY','NO_NETWORK_REQUEST_PERFORMED']};
  }catch(error){return {status:'unavailable',error:error.code||'form4_parse_failed',network_enabled:false};}
}

export const FE23_INPUT_STATUS=Object.freeze({
  status:'partial_candidates_only',
  known_fields:['issuer_cik','transaction_date','transaction_code','shares','price_per_share','direct_or_indirect','aff10b5One','accession','accepted_at_if_timezone_qualified'],
  unknown_fields:['discretionary_net_flow_z','insider_recency','issuer_illiquidity_z'],
  policy:'Directly held, P/S-coded, explicitly non-10b5-1 rows are candidates only; P/S does not prove open-market execution or discretionary intent.',
  blockers:['bounded complete Form 4 coverage','share-class/corporate-action mapping','amendment reconciliation','30-day transaction/filing vintage','approved normalizer and price-liquidity input'],
  no_plan_flag_means:'unknown_not_non_10b5_1',
  transaction_date_policy:'Date-only Form 4 trade dates and evaluation cutoffs are compared on America/New_York calendar days; the acceptance day must not precede the transaction day.',
});

export function buildFE23PublicInputs(forms,evaluation_at,{complete_accession_window=false,issuer_liquidity=null}={}){
  const base={engine_id:'FE23',feature_origin:'new_form4_candidate_transform',score_called:false,decision_eligible:false,calibrated_probability:null,
    feature_policy:'FE23_NONPLAN_DIRECT_P_S_CANDIDATES_V1',time_policy:'America/New_York calendar date for Form 4 trade-date as-of checks'};
  const unknown=reason=>({status:'unknown',value:null,reason});
  try{
    if(!Array.isArray(forms)||forms.length>200||forms.length===0)fail('form4_capture_batch_required');
    const cutoff=requireInstant(evaluation_at,'evaluation_clock_required');
    let evalDay;try{evalDay=calendarDayAt(cutoff,'America/New_York');}catch{fail('evaluation_timezone_unavailable');}
    if(!evalDay)fail('evaluation_calendar_day_unavailable');
    const issuer=forms[0]?.issuer_cik, symbol=forms[0]?.issuer_symbol;
    if(!/^\d{10}$/.test(String(issuer??''))||issuer==='0000000000'||forms.some(f=>f?.issuer_cik!==issuer||f?.issuer_symbol!==symbol))fail('form4_issuer_identity_mismatch');
    const accessionIds=forms.map(f=>f?.accession);
    // EDGAR accession prefixes identify the submitting CIK, which may be an
    // owner's agent rather than the issuer in the Form 4 XML. Bind issuers via
    // parsed issuer_cik and the requested archive-directory CIK, not prefix.
    if(accessionIds.some(a=>!accession(a))||new Set(accessionIds).size!==accessionIds.length)fail('form4_accession_identity_or_duplicate');
    let allReceiptsValid=true, anyAmendment=false; const rows=[];
    for(const form of forms){
      if(form?.status!=='parsed'||!Array.isArray(form.transactions))fail('invalid_form4_parsed_record');
      if(form.transactions.length>100||rows.length+form.transactions.length>20000)fail('form4_candidate_row_limit_exceeded');
      const acceptedUsable=usableAcceptanceClock(form),capturedUsable=isoInstant(form.captured_at);
      if(acceptedUsable&&capturedUsable)requireCaptureNotBeforeAcceptance(form.accepted_at,form.captured_at);
      if(acceptedUsable&&form.period_of_report)requireCalendarNotBefore(form.accepted_at,form.period_of_report,'acceptance_precedes_period_end');
      if(!acceptedUsable||!capturedUsable||!isoDate(form.period_of_report)||Date.parse(form.accepted_at)>Date.parse(cutoff)||Date.parse(form.captured_at)>Date.parse(cutoff))allReceiptsValid=false;
      if(/\/A$/.test(form.filing_form||''))anyAmendment=true;
      for(const txn of form.transactions){
        if(acceptedUsable&&txn?.transaction_date)requireCalendarNotBefore(form.accepted_at,txn.transaction_date,'filing_acceptance_precedes_transaction_date');
        if(txn?.transaction_date&&txn.transaction_date>evalDay)fail('future_insider_transaction');
        if(!['P','S'].includes(txn.transaction_code)||txn.direct_or_indirect!=='D')continue;
        if(!txn.transaction_date||txn.transaction_date>evalDay)fail('future_insider_transaction');
        const tradeAge=daysBetween(txn.transaction_date,evalDay), acceptanceAge=form.accepted_at?((Date.parse(cutoff)-Date.parse(form.accepted_at))/86400000):Infinity;
        if(tradeAge<0)fail('future_insider_transaction');
        if(tradeAge<=30&&acceptanceAge<=30)rows.push({...txn,acceptance_age_days:acceptanceAge,transaction_age_days:tradeAge,form_captured_at:form.captured_at});
      }
    }
    const receiptComplete=forms.every(f=>f?.coverage?.transaction_list_complete===true&&f?.coverage?.issuer_share_class_match===true)&&complete_accession_window===true&&allReceiptsValid&&!anyAmendment;
    const unknownPlan=rows.some(r=>r.plan_status==='unknown'), resolvedPlan=rows.every(r=>['not_10b5_1','10b5_1'].includes(r.plan_status));
    const candidateRows=rows.filter(r=>r.candidate_nonplan_direct_P_S===true&&r.discretionary_status==='still_unverified_not_equivalent_to_discretionary');
    const candidateNotional=candidateRows.reduce((sum,r)=>sum+(finite(r.signed_reported_notional_usd)?r.signed_reported_notional_usd:0),0);
    const candidateNotionalSafe=finite(candidateNotional)&&Math.abs(candidateNotional)<=Number.MAX_SAFE_INTEGER;
    const latestAge=candidateRows.length?Math.min(...candidateRows.map(r=>r.transaction_age_days)):null;
    const fields={
      discretionary_net_flow_z:unknown('candidate_form4_notional_is_not_discretionary_flow_and_no_prior_normalizer_supplied'),
      non_10b5_1_confidence:!receiptComplete?unknown('complete_accession_window_and_accepted_receipts_required'):unknownPlan||!resolvedPlan?unknown('any_missing_or_legacy_plan_flag_keeps_confidence_unknown'):rows.length?{status:'measured',value:rows.filter(r=>r.plan_status==='not_10b5_1').length/rows.length,reason:'share of direct P/S rows with explicit non-10b5-1 indication; not a discretion classifier'}:unknown('no_direct_P_or_S_transactions'),
      insider_recency:!receiptComplete?unknown('complete_accession_window_and_accepted_receipts_required'):candidateRows.length?{status:'measured',value:Math.exp(-latestAge/30),latest_transaction_age_days:latestAge,reason:'exp(-days since most recent explicit non-plan direct P/S transaction / 30)'}:unknown('no_current_candidate_trade'),
      issuer_illiquidity_z:unknown('no_verified_same-issuer_recent_liquidity_input'),
    };
    if(issuer_liquidity&&issuer_liquidity.status==='measured'&&issuer_liquidity.unit==='z'&&issuer_liquidity.issuer_cik===issuer&&finite(issuer_liquidity.value)&&issuer_liquidity.source_verified===true&&isoInstant(issuer_liquidity.source_as_of)&&isoInstant(issuer_liquidity.captured_at)&&Date.parse(issuer_liquidity.source_as_of)<=Date.parse(cutoff)&&Date.parse(issuer_liquidity.captured_at)<=Date.parse(cutoff)&&Date.parse(cutoff)-Date.parse(issuer_liquidity.source_as_of)<=172800000)
      fields.issuer_illiquidity_z={status:'measured',value:issuer_liquidity.value,source_as_of:issuer_liquidity.source_as_of,reason:'caller-attested current same-issuer liquidity series; rights and underlying source remain external'};
    return {...base,status:'partial_unknown_fields',features:null,fields,
      candidate_metrics:{screened_nonplan_direct_P_S_net_usd:receiptComplete&&candidateNotionalSafe?candidateNotional:null,
        eligible_candidate_transaction_count:receiptComplete?candidateRows.length:null,transaction_count_in_window:receiptComplete?rows.length:null,
        aggregate_notional_status:!candidateNotionalSafe?'unknown_numeric_range':'measured',complete_accession_window:receiptComplete},
      source:{issuer_cik:issuer,symbol,accessions:[...new Set(forms.map(f=>f.accession))],capture_at_latest:maxDate(...forms.map(f=>f.captured_at).filter(Boolean)),
        accepted_at_latest:maxDate(...forms.map(f=>f.accepted_at).filter(Boolean)),historical_point_in_time_claim:false},
      warnings:['NEW_CANDIDATE_POLICY_NOT_ORIGINAL_DISCRETION_CLASSIFIER','NO_SCORE_OR_DECISION_ELIGIBILITY','P_S_CODES_DO_NOT_PROVE_OPEN_MARKET_OR_DISCRETION','FORM4_PLAN_FLAG_IS_NOT_PROOF_OF_TRADING_INTENT']};
  }catch(error){return {...base,status:'unavailable',features:null,error:error.code||'feature_build_failed',fields:{
    discretionary_net_flow_z:unknown(error.code||'feature_build_failed'),non_10b5_1_confidence:unknown(error.code||'feature_build_failed'),
    insider_recency:unknown(error.code||'feature_build_failed'),issuer_illiquidity_z:unknown(error.code||'feature_build_failed')}};}
}

export const PUBLIC_INPUT_READINESS=Object.freeze({
  FE21:{engine:'XBRL cash-conversion inflection',status:'partial_public_source_path_no_sec_capture',fields:{
    cash_conversion_z:'unknown_no_approved_sec_operator_profile_and_unreviewed_tag_map',receivables_growth_gap_z:'unknown_tag_and_comparable_quarter_missing',deferred_revenue_change_z:'unknown_total_deferred_revenue_tag_not_verified',fcf_acceleration_z:'unknown_cash_flow_quarter_basis_and_capex_tag_review_needed'}},
  FE22:{engine:'Filing and guidance semantic delta',status:'partial_official_text_public_source_provider_section_entitlement_unverified',fields:{
    semantic_delta_z:'unknown_no_versioned_parser_or_semantic_model; lexical proxy only is implemented',parser_confidence:'unknown_until_section_extract_receipt_and_parser_hash',novelty_score:'unknown_until_matched_vintage_text',section_relevance:'unknown_until_section_identity_and_taxonomy_review'}},
  FE23:{engine:'Insider activity adjusted for plan status',status:'partial_form4_local_parser_candidate_only',fields:{
    discretionary_net_flow_z:'unknown_candidate_trade_notional_is_not_discretionary_flow',non_10b5_1_confidence:'unknown_if_form_flag_absent_or_pre_2023_04_01',insider_recency:'unknown_until_complete_accepted_at_bound_flow',issuer_illiquidity_z:'unknown_until_matched_issuer_daily_price_liquidity'}},
  FE24:{engine:'13F crowding-unwind hazard',status:'public_holdings_source_possible_panel_not_bound',fields:{
    ownership_crowding_z:'unknown_manager_universe_and_historical_cusip_issuer_map',fundamental_deterioration_z:'unknown_requires_FE21_inputs',liquidity_stress_z:'unknown_requires_current_quote_or_daily_liquidity_source',filing_staleness:'unknown_until_report_period_and_accepted_at_joined'},limits:['13F holdings are delayed and incomplete, not current position truth','manager denominator and confidential-treatment gaps matter']},
  FE25:{engine:'Executed buyback support',status:'partial_monthly_item703_public_input_blackout_unknown',fields:{
    buyback_pace_float_z:'partial_item703_reports_aggregate_executed_shares_not_daily; float_not_established',execution_confidence:'partial_monthly_reported_share_volume_only',blackout_risk:'unknown_undisclosed_blackout_is_not_zero',liquidity_anomaly_z:'unknown_until_matched_price_volume_history'},limits:['do not infer flow from authorizations','2023 daily rule was vacated effective 2023-12-19; prior disclosure rules returned']},
  FE26:{engine:'Index rebalance and basket flow pressure',status:'blocked_no_named_index_or_effective_event_panel',fields:{
    flow_estimate_z:'unknown_model_output_not_a_public_fact',flow_model_confidence:'unknown_without_reconciled_weights_aum_and_model_error_history',days_to_effective:'unknown_without_official_announcement_and_calendar',crowding_z:'unknown_without_current_weighted_member_panel'},limits:['specific index provider and constituent/weight basis must be selected','public announcement does not prove actual fund demand']},
});

export function getPublicInputReadiness(){return JSON.parse(JSON.stringify(PUBLIC_INPUT_READINESS));}
