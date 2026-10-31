// NEW descriptive breadth transform for a current, fixed SPY-holdings cohort.
// It is not historical S&P 500 breadth or a point-in-time reconstruction.
import {evaluateForecastEngine} from '../../dist/forecast-engines.mjs';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex,utf8ToBytes} from '@noble/hashes/utils.js';
import {validateXmlWellFormedness} from './xml-well-formedness-preflight-v1.mjs';

const hash=value=>bytesToHex(sha256(utf8ToBytes(JSON.stringify(value))));
const fail=code=>{throw Error(code);};
const MONTHS=Object.freeze({JAN:'01',FEB:'02',MAR:'03',APR:'04',MAY:'05',JUN:'06',JUL:'07',AUG:'08',SEP:'09',OCT:'10',NOV:'11',DEC:'12'});
const POLICY_SOURCE='https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx';
const CUSIP_RULE='CUSIP-9: exactly nine characters from 0-9,A-Z,*,@,# with decimal ninth check digit; positions1-6 identify issuer, positions7-8 issue, position9 check digit. Preserve text including leading zeroes; exact format/check digit required, never inferred from ticker/name.';
const date=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x+'T00:00:00Z'))&&new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
const isoInstant=x=>{
  if(typeof x!=='string')return false;
  const m=x.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|([+-])(\d{2}):(\d{2}))$/);
  if(!m||!date(m[1])||Number(m[2])>23||Number(m[3])>59||Number(m[4])>59)return false;
  if(m[6]!=='Z'&&(Number(m[8])>23||Number(m[9])>59))return false;
  return Number.isFinite(Date.parse(x));
};
const NY_DATE_FORMAT=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'});
const NY_WALL_TIME_FORMAT=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
function validCUSIP(value){
  if(typeof value!=='string'||!/^[0-9A-Z*@#]{8}[0-9]$/.test(value))return false;
  const charValue=ch=>ch>='0'&&ch<='9'?Number(ch):ch>='A'&&ch<='Z'?ch.charCodeAt(0)-55:ch==='*'?36:ch==='@'?37:ch==='#'?38:-1;
  let sum=0;for(let i=0;i<8;i++){const v=charValue(value[i]);if(v<0)return false;const n=v*(i%2===0?1:2);sum+=Math.floor(n/10)+n%10;}
  return (10-sum%10)%10===Number(value[8]);
}
function publicCapture(receipt){
  const {request_url,...safe}=receipt;
  return receipt.operation==='historical_multi_symbol_1Day_page'
    ?{...safe,request_url:'https://data.alpaca.markets/v2/stocks/bars?symbols=%5Bcurrent_cohort_redacted%5D',request_url_redacted:true,redacted_query_fields:['symbols']}
    :{...safe,request_url};
}
function stats(values,name){
  if(!Array.isArray(values)||!values.length||values.some(x=>!Number.isFinite(x)))fail('nonfinite_'+name);
  const m=mean(values),variance=mean(values.map(x=>(x-m)**2)),sd=Math.sqrt(variance);
  if(!Number.isFinite(m)||!Number.isFinite(sd)||sd<=1e-12)fail('degenerate_'+name+'_normalizer');
  return {mean:m,population_sd:sd,count:values.length,ddof:0};
}

function nextCalendarDate(value){const day=new Date(value+'T12:00:00.000Z');day.setUTCDate(day.getUTCDate()+1);return day.toISOString().slice(0,10);}
function fe05NewYorkMidnightMs(value){
  if(!date(value))fail('invalid_source_asof_date');
  // Use the offset in force at the requested local midnight. Sampling 00:00Z
  // on the same UTC date is before the US transition hour and shares the
  // midnight offset (unlike a fixed -04/-05 assumption or +24h arithmetic).
  const sample=Date.parse(value+'T00:00:00.000Z'),parts=Object.fromEntries(NY_WALL_TIME_FORMAT.formatToParts(new Date(sample)).map(p=>[p.type,p.value]));
  const wallAsUtc=Date.UTC(Number(parts.year),Number(parts.month)-1,Number(parts.day),Number(parts.hour),Number(parts.minute),Number(parts.second));
  return Date.parse(value+'T00:00:00.000Z')-(wallAsUtc-sample);
}

/** Conservative source-age classification for a date-only as-of value.
 * The source timestamp remains unknown; receipt time is deliberately unused.
 */
export function qualifyFE05DateOnlyFreshness({sourceAsOf,evaluationAt,calendarCapture,calendarSessions,selectedDates=[]}){
  if(!date(sourceAsOf)||!isoInstant(evaluationAt)||!Array.isArray(selectedDates))fail('invalid_breadth_freshness_inputs');
  const evaluationMs=Date.parse(evaluationAt),evaluationDate=NY_DATE_FORMAT.format(new Date(evaluationMs));
  if(sourceAsOf>evaluationDate)fail('invalid_breadth_freshness_inputs');
  const sourceStartMs=fe05NewYorkMidnightMs(sourceAsOf),sourceEndMs=fe05NewYorkMidnightMs(nextCalendarDate(sourceAsOf));
  const ageLower=Math.max(0,evaluationMs-sourceEndMs)/1000,ageUpper=(evaluationMs-sourceStartMs)/1000,maxAge=FE05_BREADTH_POLICY.freshness_guard.max_age_seconds;
  let sourceAgeStatus,sourceAgeAcceptable;
  if(ageUpper<=maxAge){sourceAgeStatus='within_max_age';sourceAgeAcceptable=true;}
  else if(ageLower>=maxAge){sourceAgeStatus='definitely_stale';sourceAgeAcceptable=false;}
  else{sourceAgeStatus='age_bounds_overlap_max_age';sourceAgeAcceptable=null;}

  let calendarEndDate=null,calendarRowsValid=false,providerSelectedDatesCovered=false,providerObservedCompletedSessions=0,providerLatestCompletedSession=null,providerReturnedLastDate=null,providerReturnedCount=null;
  try{
    const url=new URL(calendarCapture?.request_url||''),keys=[...url.searchParams.keys()].sort(),startDate=url.searchParams.get('start'),endDate=url.searchParams.get('end');
    calendarEndDate=endDate;
    const rowsValid=Array.isArray(calendarSessions)&&calendarSessions.length<=801&&calendarSessions.length>0&&calendarSessions.every((row,i)=>{
      if(!row||!date(row.date)||row.date<startDate||row.date>endDate||i&&row.date<=calendarSessions[i-1].date||!isoInstant(row.open)||!isoInstant(row.close))return false;
      const openMs=Date.parse(row.open),closeMs=Date.parse(row.close);
      return openMs<closeMs&&NY_DATE_FORMAT.format(new Date(openMs))===row.date&&NY_DATE_FORMAT.format(new Date(closeMs-1))===row.date;
    });
    const calendarRangeValid=url.origin==='https://paper-api.alpaca.markets'&&url.pathname==='/v2/calendar'&&keys.join(',')==='end,start'
      &&calendarCapture?.http_status===200&&date(startDate)&&date(endDate)&&startDate<=sourceAsOf&&endDate===evaluationDate
      &&Date.parse(sourceAsOf+'T00:00:00.000Z')-Date.parse(startDate+'T00:00:00.000Z')<=FE05_BREADTH_POLICY.calendar_lookback_days*86400000;
    const selectedCovered=rowsValid&&selectedDates.every(d=>calendarSessions.some(row=>row.date===d));
    calendarRowsValid=calendarRangeValid&&rowsValid;
    providerSelectedDatesCovered=calendarRowsValid&&selectedCovered&&calendarSessions.some(row=>row.date===sourceAsOf);
    if(calendarRowsValid){
      providerReturnedCount=calendarSessions.length;providerReturnedLastDate=calendarSessions.at(-1)?.date??null;
      const completed=calendarSessions.filter(row=>Date.parse(row.close)+FE05_BREADTH_POLICY.completion_delay_ms<=evaluationMs);
      providerLatestCompletedSession=completed.at(-1)?.date??null;
      providerObservedCompletedSessions=completed.filter(row=>row.date>sourceAsOf).length;
    }
  }catch{/* A missing or malformed evaluation calendar is an unknown, never zero sessions. */}
  // The provider response does not independently establish that omitted
  // sessions were not left out. Keep full-calendar completeness unknown; the
  // separate provider-grid/request-coverage check below may still qualify an
  // age-bounded research result, but it must never self-certify market lag.
  const calendarCompletenessIndependentlyVerified=false;
  const providerCalendarCoverageValid=calendarRowsValid&&providerSelectedDatesCovered&&calendarEndDate===evaluationDate;
  const freshnessEligible=sourceAgeAcceptable===true&&providerCalendarCoverageValid;
  return {guard_id:FE05_BREADTH_POLICY.freshness_guard.id,guard_version:FE05_BREADTH_POLICY.freshness_guard.version,
    source_as_of:sourceAsOf,source_asof_granularity:'date_only',source_time_unknown:true,source_age_seconds:null,
    source_age_bounds_seconds:{lower_bound:ageLower,upper_bound:ageUpper,bounds_timezone:'America/New_York',interval:'[source-date local midnight, next local midnight)'},
    source_age_max_age_status:sourceAgeStatus,source_age_max_age_acceptable:sourceAgeAcceptable,
    original_catalog_age_acceptable:sourceAgeAcceptable,
    original_catalog_age_status:sourceAgeStatus==='within_max_age'?'date_only_interval_within_max_age':sourceAgeStatus==='definitely_stale'?'date_only_interval_definitely_stale':'date_only_interval_overlaps_max_age',
    max_age_seconds:maxAge,age_evaluated_at:evaluationAt,calendar_coverage:{requested_end_date:calendarEndDate,required_end_date:evaluationDate,
      provider_rows_structurally_valid:calendarRowsValid,provider_selected_dates_covered:providerSelectedDatesCovered,
      provider_request_covers_evaluation_date:calendarEndDate===evaluationDate,
      provider_returned_row_count:providerReturnedCount,provider_returned_last_date:providerReturnedLastDate,
      complete_through_evaluation_date:null,independently_verified_complete:calendarCompletenessIndependentlyVerified,
      status:providerCalendarCoverageValid?'provider_observed_coverage_valid':'unavailable_or_invalid'},
    observed_returned_completed_sessions_after_source_asof_count:calendarRowsValid?providerObservedCompletedSessions:null,
    provider_latest_completed_session_date:calendarRowsValid?providerLatestCompletedSession:null,
    current_session_lag_sessions:null,current_session_lag_status:'unknown_calendar_completeness',
    freshness_eligible:freshnessEligible,decision_eligible:false};
}

export const FE05_BREADTH_POLICY=Object.freeze({
  id:'FE05_SPY_CURRENT_TOP25_ISSUER_BREADTH_V1',version:1,origin:'NEW_FEATURE_POLICY',engine_id:'FE05',
  source:{provider:'State Street Investment Management / SPDR',product:'SPY daily holdings XLSX',url:POLICY_SOURCE,
    file:'holdings-daily-us-en-spy.xlsx',asof_granularity:'date_only',first_seen_is_not_observation:true,
    rights_attestation:null,redistribution:'not_cleared; do not emit or persist raw holdings/member list'},
  source_snapshot_contract:{position_rows_min:500,position_rows_max:510,reported_weight_total_percent_min:99.9,reported_weight_total_percent_max:100.1,
    outside_contract:'abstain; residual retained and never renormalized'},
  identifier_policy:{type:'CUSIP-9',issuer_key:'first_six_characters',format:'exactly nine characters from 0-9,A-Z,*,@,# with a valid decimal ninth check digit; positions1-6 issuer,7-8 issue,9 check digit. Preserve text exactly including leading zeroes.',class_aggregation:'aggregate each CUSIP issuer prefix before top-N selection; include every class line for a selected issuer',authority:'SEC-filed DTC CUSIP definition and CUSIP Global Services format; not a ticker/name heuristic'},
  universe:{kind:'current_SPY_holdings_top25_issuer_cohort',selection:'exclude only verified US-dollar cash and contra-Hologic CVR identifiers; sum current source weights by exact CUSIP issuer prefix; rank top25 issuers by total weight; deterministic issuer-prefix tie-break; include every security line for each selected issuer',issuer_count:25,max_security_lines:35,top_selection_by:'source_weight_only',performance_selection:false,denominator:'selected cohort weight mass, disclosed separately as a subset of the whole SPY holdings file; no full-file normalization or market-wide breadth claim',survivor_replacement:false,historical_membership_backfill:false,point_in_time_claim:false},
  exclusions:[{identifier:'999USDZ92',reason:'US DOLLAR cash line only when exact source name/ticker/currency match holds'},{identifier:'436CVR021',reason:'CONTRA HOLOGIC contingent-value-right line only when exact source name/ticker/currency match holds'}],
  sessions:505,calendar_lookback_days:800,calendar:'Alpaca official US equity calendar; America/New_York',completion_delay_ms:900000,
  freshness_guard:{id:'FE05_DATE_ONLY_ASOF_INTERVAL_V2',version:2,max_age_seconds:172800,source_date_timezone:'America/New_York',
    date_interval:'Treat the date-only as-of date as an effective-date interval [local midnight, next local midnight); do not infer an observation/publication timestamp.',
    pass_rule:'The conservative age upper bound (evaluation time minus source-date start) is at most max_age_seconds and a structurally valid official provider calendar response requested through the evaluation local date covers the selected 505-session source grid. Calendar completeness remains provider-observed, not independently verified.',
    stale_rule:'The conservative age lower bound (evaluation time minus source-date end) is at least max_age_seconds; the source-date interval is half-open.',
    overlap_rule:'If the age bounds straddle max_age_seconds, freshness is indeterminate and ineligible; retain only a diagnostic result.',
    calendar_lag_rule:'Calendar rows and completed rows after source_as_of are provider-observed diagnostics only. Completeness is not independently verified; report observed returned-row counts separately and keep exact market-session lag null.',
    receipt_time_rule:'File received_at is an acquisition receipt, not an observation/publication time and is never substituted for source age.'},
  provider:{bars:'Alpaca Stock Bars API',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',symbol_mapping:'Use exact SSGA ticker strings, no alias/punctuation rewrite; Alpaca asof is the date-only holdings date; require returned requested-symbol keys and full matched histories or abstain.',end_date:'holdings as-of date, which must itself be an official completed session',price_basis:'split-adjusted dividend-excluded closes; not total return'},
  acquisition:{budget_seconds:35,per_request_timeout_seconds:8,max_symbols:36,max_bars_rows:7000,max_pages:3,max_decoded_bytes_per_bars_page:2097152,max_holdings_file_bytes:1048576,max_holdings_uncompressed_component_bytes:4194304,max_calendar_bytes:262144,max_concurrent_upstream_requests:1,cache_seconds:0},
  features:{breadth_delta:'Current cohort-relative, issuer-weighted signed direction: sum(w_i * sign(r_i,t)) / sum(w_i); ties contribute zero.',advance_decline_z:'Current breadth_delta standardized by exactly the preceding252 daily breadth values; population SD; candidate excluded.',new_high_low_z:'For each issuer, chain-link its current-source-weighted share-class log returns. Daily H-L is cohort-weighted +1/-1/0 when that index is strictly above/below its prior252-session extrema; current H-L standardized against exactly the preceding252 daily H-L values; population SD; candidate excluded.',index_trend_z:'SPY 20-session log return standardized against exactly preceding252 SPY 20-session log returns; candidate excluded.'},
  sample_floor:'Exactly25 issuer groups, all source lines for each selected group, exactly505 complete matched official close bars per selected security plus SPY, no missing-price imputation, no pairwise deletion, no member substitution. Population SD <=1e-12 abstains.',
  constraints:'The current holdings roster is descriptive and survivorship/selection-biased. It is not historical index membership, a constituent backtest, all-stock market breadth, complete S&P 500 issuer breadth, or a tradability screen. SSGA terms/redistribution rights are not cleared; output is research-only and decision-ineligible.',
  quality:{source_quality_score:null,rights_attestation:null,decision_eligible:false,calibrated_probability:null},
});
export const FE05_BREADTH_POLICY_SHA256=hash(FE05_BREADTH_POLICY);

const FE05_XML_MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main';
const FE05_XML_PACKAGE_REL='http://schemas.openxmlformats.org/package/2006/relationships';
const FE05_XML_OFFICE_REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const FE05_XML_NS='http://www.w3.org/XML/1998/namespace';
function decodeFE05XML(text){
  if(typeof text!=='string'||/&(?!#x[0-9a-f]+;|#\d+;|amp;|lt;|gt;|quot;|apos;)/i.test(text))fail('invalid_holdings_xml');
  const decoded=text.replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos);/gi,(_entity,code)=>{
    if(code==='amp')return '&';if(code==='lt')return '<';if(code==='gt')return '>';if(code==='quot')return '"';if(code==='apos')return "'";
    const n=code[1].toLowerCase()==='x'?parseInt(code.slice(2),16):parseInt(code.slice(1),10);
    if(!Number.isInteger(n)||n<=0||n>0x10ffff||(n>=0xd800&&n<=0xdfff)||(n<0x20&&![9,10,13].includes(n)))fail('invalid_holdings_xml');return String.fromCodePoint(n);
  });
  for(const char of decoded){const cp=char.codePointAt(0);if(cp===0||(cp<0x20&&![9,10,13].includes(cp))||(cp>=0xd800&&cp<=0xdfff))fail('invalid_holdings_xml');}
  return decoded;
}
// A deliberately small, bounded XML grammar for XLSX parts. DTDs, entities,
// comments and processing instructions are unsupported; CDATA is accepted only
// in actual odd/even worksheet footers. Namespaces are resolved before use.
function parseFE05XML(text){
  if(typeof text!=='string'||text.length>FE05_BREADTH_POLICY.acquisition.max_holdings_uncompressed_component_bytes)fail('invalid_holdings_xml');
  if(text.charCodeAt(0)===0xfeff)text=text.slice(1);
  try{validateXmlWellFormedness(text,{maxBytes:2*1024*1024,maxDepth:80,maxNodes:30000,allowCdata:true});}
  catch{fail('invalid_holdings_xml');}
  if(/<!--|-->/i.test(text))fail('invalid_holdings_xml');
  if(/<!\s*(?:DOCTYPE|ENTITY)\b|\b(?:SYSTEM|PUBLIC)\s+["']/i.test(text))fail('invalid_holdings_xml');
  const declaration=/^<\?xml\s+version=(["'])1\.0\1(?:\s+encoding=(["'])[A-Za-z][A-Za-z0-9._-]*\2)?(?:\s+standalone=(["'])(?:yes|no)\3)?\s*\?>/;
  if(text.startsWith('<?xml')){const match=text.match(declaration);if(!match)fail('invalid_holdings_xml');text=text.slice(match[0].length);}
  if(text.includes('<?'))fail('invalid_holdings_xml');
  const document={qname:'#document',local:'#document',uri:'',attrs:Object.create(null),children:[],text:''};
  const baseNs={xml:FE05_XML_NS},stack=[{node:document,ns:baseNs}],namePattern=/^[A-Za-z_][A-Za-z0-9_.:-]*$/;
  let i=0,nodes=0,rootClosed=false;
  const splitName=(raw,ns,isElement)=>{
    if(!namePattern.test(raw)||raw.startsWith(':')||raw.endsWith(':')||(raw.match(/:/g)||[]).length>1)fail('invalid_holdings_xml');
    const parts=raw.split(':');if(parts.length===1)return {local:parts[0],uri:isElement?(ns['']||''):''};
    if(!ns[parts[0]])fail('invalid_holdings_xml');return {local:parts[1],uri:ns[parts[0]]};
  };
  const tagEnd=start=>{let quote='';for(let j=start+1;j<text.length;j++){const c=text[j];if(quote){if(c===quote)quote='';}else if(c==='"'||c==="'")quote=c;else if(c==='>')return j;}fail('invalid_holdings_xml');};
  while(i<text.length){
    if(text.startsWith('<![CDATA[',i)){
      const parent=stack.at(-1)?.node;if(stack.length===1||parent?.uri!==FE05_XML_MAIN||!['oddFooter','evenFooter'].includes(parent.local))fail('invalid_holdings_xml');
      const end=text.indexOf(']]>',i+9);if(end<0)fail('invalid_holdings_xml');parent.text+=text.slice(i+9,end);i=end+3;continue;
    }
    if(text[i]!=='<'){
      const end=text.indexOf('<',i),stop=end<0?text.length:end,value=decodeFE05XML(text.slice(i,stop));
      if(stack.length===1){if(value.trim())fail('invalid_holdings_xml');}else stack.at(-1).node.text+=value;
      i=stop;continue;
    }
    if(text.startsWith('<!',i)||text.startsWith('<?',i))fail('invalid_holdings_xml');
    const end=tagEnd(i),raw=text.slice(i,end+1);i=end+1;
    if(raw.startsWith('</')){
      const match=/^<\/([A-Za-z_][A-Za-z0-9_.:-]*)\s*>$/.exec(raw);if(!match||stack.length===1||stack.at(-1).node.qname!==match[1])fail('invalid_holdings_xml');
      stack.pop();if(stack.length===1)rootClosed=true;continue;
    }
    const opening=/^<([A-Za-z_][A-Za-z0-9_.:-]*)([\s\S]*?)>$/.exec(raw);if(!opening)fail('invalid_holdings_xml');
    const rawName=opening[1];let tail=opening[2],selfClose=false;
    if(/\/\s*$/.test(tail)){selfClose=true;tail=tail.replace(/\/\s*$/,'');}
    if(rootClosed)fail('invalid_holdings_xml');
    const rawAttrs=[];let pos=0;
    while(pos<tail.length){
      const ws=/^\s+/.exec(tail.slice(pos));if(!ws)fail('invalid_holdings_xml');pos+=ws[0].length;if(pos>=tail.length)break;
      const attrName=/^[A-Za-z_][A-Za-z0-9_.:-]*/.exec(tail.slice(pos));if(!attrName)fail('invalid_holdings_xml');pos+=attrName[0].length;
      while(pos<tail.length&&/\s/.test(tail[pos]))pos++;if(tail[pos++]!=='=')fail('invalid_holdings_xml');while(pos<tail.length&&/\s/.test(tail[pos]))pos++;
      const quote=tail[pos++];if(quote!=='"'&&quote!=="'")fail('invalid_holdings_xml');const valueStart=pos;while(pos<tail.length&&tail[pos]!==quote){if(tail[pos]==='<')fail('invalid_holdings_xml');pos++;}
      if(pos>=tail.length)fail('invalid_holdings_xml');const value=decodeFE05XML(tail.slice(valueStart,pos));pos++;
      if(rawAttrs.some(a=>a.name===attrName[0]))fail('invalid_holdings_xml');rawAttrs.push({name:attrName[0],value});
    }
    const ns={...stack.at(-1).ns};
    for(const a of rawAttrs){if(a.name==='xmlns')ns['']=a.value;else if(a.name.startsWith('xmlns:')){const prefix=a.name.slice(6);if(!/^[A-Za-z_][A-Za-z0-9_.-]*$/.test(prefix)||prefix==='xmlns'||!a.value||prefix==='xml'&&a.value!==FE05_XML_NS||prefix!=='xml'&&a.value===FE05_XML_NS)fail('invalid_holdings_xml');ns[prefix]=a.value;}}
    const en=splitName(rawName,ns,true),attrs=Object.create(null);for(const a of rawAttrs){if(a.name==='xmlns'||a.name.startsWith('xmlns:'))continue;const at=splitName(a.name,ns,false),key=at.uri+'\u0000'+at.local;if(Object.hasOwn(attrs,key))fail('invalid_holdings_xml');attrs[key]=a.value;}
    const node={qname:rawName,local:en.local,uri:en.uri,attrs,children:[],text:''};stack.at(-1).node.children.push(node);if(++nodes>250000)fail('invalid_holdings_xml');
    if(!selfClose){stack.push({node,ns});if(stack.length>100)fail('invalid_holdings_xml');}else if(stack.length===1)rootClosed=true;
  }
  const roots=document.children;if(roots.length!==1||stack.length!==1||!rootClosed)fail('invalid_holdings_xml');return roots[0];
}
function xmlFE05Children(node,local,uri=FE05_XML_MAIN){return node?.children.filter(child=>typeof child==='object'&&child.local===local&&child.uri===uri)||[];}
function xmlFE05Child(node,local,uri=FE05_XML_MAIN,{required=false}={}){const found=xmlFE05Children(node,local,uri);if(found.length>1)fail('invalid_holdings_xml');if(!found.length){if(required)fail('invalid_holdings_xml');return null;}return found[0];}
function xmlFE05Attr(node,local,uri=''){return node?.attrs?.[uri+'\u0000'+local]??null;}
function xmlFE05Text(node){if(node.children.some(child=>typeof child==='object'))fail('invalid_holdings_xml');return node.text;}
function sharedFE05String(si){let out='';for(const child of si.children){if(child.local==='t'&&child.uri===FE05_XML_MAIN){out+=xmlFE05Text(child);continue;}if(child.local==='r'&&child.uri===FE05_XML_MAIN){const ts=xmlFE05Children(child,'t');if(ts.length!==1)fail('invalid_holdings_xml');out+=xmlFE05Text(ts[0]);continue;}fail('invalid_holdings_xml');}return out;}
function valueFE05Cell(cell,strings){
  if(!cell)return null;const type=xmlFE05Attr(cell,'t');if(xmlFE05Children(cell,'f').length)fail('invalid_holdings_xml');
  const inline=xmlFE05Child(cell,'is'),values=xmlFE05Children(cell,'v');
  if(inline){if(values.length||type!=='inlineStr')fail('invalid_holdings_xml');let out='';for(const child of inline.children){if(child.local==='t'&&child.uri===FE05_XML_MAIN)out+=xmlFE05Text(child);else if(child.local==='r'&&child.uri===FE05_XML_MAIN){const ts=xmlFE05Children(child,'t');if(ts.length!==1)fail('invalid_holdings_xml');out+=xmlFE05Text(ts[0]);}else fail('invalid_holdings_xml');}return out;}
  if(values.length>1)fail('invalid_holdings_xml');if(!values.length)return null;const decoded=xmlFE05Text(values[0]);
  if(type==='s'){if(!/^\d+$/.test(decoded)||Number(decoded)>=strings.length)fail('invalid_holdings_xml');return strings[Number(decoded)];}
  if(type&&type!=='n'&&type!=='str')fail('invalid_holdings_xml');return decoded;
}

async function inflateRaw(bytes,limit){
  if(typeof DecompressionStream!=='function')fail('xlsx_deflate_unavailable');
  let stream,reader;try{stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));reader=stream.getReader();}catch{fail('xlsx_deflate_unsupported');}
  const chunks=[];let size=0;
  try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>limit){await reader.cancel();fail('invalid_holdings_zip_entry');}chunks.push(value);}}
  catch(error){if(error?.message==='invalid_holdings_zip_entry')throw error;fail('invalid_holdings_zip_entry');}
  const out=new Uint8Array(size);let offset=0;for(const chunk of chunks){out.set(chunk,offset);offset+=chunk.byteLength;}return out;
}
function zipCRC32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
async function zipParts(input){
  const bytes=input instanceof Uint8Array?input:new Uint8Array(input);
  if(bytes.length<22||bytes.length>FE05_BREADTH_POLICY.acquisition.max_holdings_file_bytes)fail('invalid_holdings_xlsx_size');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);let eocd=-1;
  for(let p=Math.max(0,bytes.length-65557);p<=bytes.length-22;p++)if(view.getUint32(p,true)===0x06054b50)eocd=p;
  if(eocd<0||view.getUint16(eocd+4,true)!==0||view.getUint16(eocd+6,true)!==0||view.getUint16(eocd+8,true)!==view.getUint16(eocd+10,true))fail('invalid_holdings_zip_directory');
  const count=view.getUint16(eocd+10,true),dirSize=view.getUint32(eocd+12,true),dirOffset=view.getUint32(eocd+16,true),commentLen=view.getUint16(eocd+20,true);
  if(count>256||eocd+22+commentLen!==bytes.length||dirOffset+dirSize!==eocd)fail('invalid_holdings_zip_directory');
  const wanted=new Set(['xl/workbook.xml','xl/_rels/workbook.xml.rels','xl/sharedStrings.xml','xl/worksheets/sheet1.xml']),parts=new Map();let p=dirOffset,total=0;
  for(let i=0;i<count;i++){
    if(p+46>bytes.length||view.getUint32(p,true)!==0x02014b50)fail('invalid_holdings_zip_directory');
    const flags=view.getUint16(p+8,true),method=view.getUint16(p+10,true),crc=view.getUint32(p+16,true),compressed=view.getUint32(p+20,true),uncompressed=view.getUint32(p+24,true),nameLen=view.getUint16(p+28,true),extraLen=view.getUint16(p+30,true),entryCommentLen=view.getUint16(p+32,true),startDisk=view.getUint16(p+34,true),local=view.getUint32(p+42,true);
    if((flags&0x41)||startDisk||![0,8].includes(method)||compressed===0xffffffff||uncompressed===0xffffffff||local===0xffffffff)fail('invalid_holdings_zip_entry');
    const name=new TextDecoder('utf-8',{fatal:true}).decode(bytes.slice(p+46,p+46+nameLen));p+=46+nameLen+extraLen+entryCommentLen;
    if(!wanted.has(name))continue;
    if(parts.has(name)||uncompressed>FE05_BREADTH_POLICY.acquisition.max_holdings_uncompressed_component_bytes||local+30>bytes.length||view.getUint32(local,true)!==0x04034b50)fail('invalid_holdings_zip_entry');
    const localFlags=view.getUint16(local+6,true),localMethod=view.getUint16(local+8,true),localCRC=view.getUint32(local+14,true),localCompressed=view.getUint32(local+18,true),localUncompressed=view.getUint32(local+22,true),localName=view.getUint16(local+26,true),localExtra=view.getUint16(local+28,true),localNameBytes=bytes.slice(local+30,local+30+localName),start=local+30+localName+localExtra,end=start+compressed;
    if(localFlags!==flags||localMethod!==method||new TextDecoder('utf-8',{fatal:true}).decode(localNameBytes)!==name||!(flags&8)&&(localCRC!==crc||localCompressed!==compressed||localUncompressed!==uncompressed))fail('invalid_holdings_zip_entry');
    if(end>bytes.length||total+uncompressed>6*1024*1024)fail('invalid_holdings_zip_entry');
    const compressedBytes=bytes.slice(start,end);let data;
    if(method===0)data=compressedBytes;else if(method===8)data=await inflateRaw(compressedBytes,FE05_BREADTH_POLICY.acquisition.max_holdings_uncompressed_component_bytes);else fail('unsupported_holdings_zip_compression');
    if(data.length!==uncompressed||zipCRC32(data)!==crc)fail('invalid_holdings_zip_uncompressed_length');total+=data.length;
    parts.set(name,new TextDecoder('utf-8',{fatal:true}).decode(data));
  }
  if(p!==dirOffset+dirSize)fail('invalid_holdings_zip_directory');
  if(![...wanted].every(name=>parts.has(name)))fail('holdings_xlsx_parts_missing');
  return parts;
}
function sharedStringList(root){
  if(root?.local!=='sst'||root.uri!==FE05_XML_MAIN)fail('invalid_holdings_xml');
  const items=xmlFE05Children(root,'si');if(root.children.some(c=>typeof c==='object'&&(c.local!=='si'||c.uri!==FE05_XML_MAIN))||items.length>20000)fail('invalid_holdings_xml');
  return items.map(sharedFE05String);
}
function parseSheetRows(root,strings){
  if(root?.local!=='worksheet'||root.uri!==FE05_XML_MAIN)fail('invalid_holdings_xml');
  const data=xmlFE05Child(root,'sheetData',FE05_XML_MAIN,{required:true});
  if(root.children.some(c=>typeof c==='object'&&c.local==='sheetData'&&c.uri!==FE05_XML_MAIN))fail('invalid_holdings_xml');
  const rows=xmlFE05Children(data,'row');if(data.children.some(c=>typeof c==='object'&&(c.uri!==FE05_XML_MAIN||c.local!=='row'))||rows.length>1024)fail('invalid_holdings_xml');
  const out=[];let prior=0;const seen=new Set();
  for(const row of rows){
    const raw=xmlFE05Attr(row,'r'),rowNumber=Number(raw);if(!/^[1-9]\d*$/.test(raw||'')||!Number.isSafeInteger(rowNumber)||rowNumber<=prior||seen.has(rowNumber))fail('invalid_holdings_row');prior=rowNumber;seen.add(rowNumber);
    const cells=xmlFE05Children(row,'c');if(row.children.some(c=>typeof c==='object'&&(c.uri!==FE05_XML_MAIN||c.local!=='c')))fail('invalid_holdings_xml');
    const values=Object.create(null);
    for(const cell of cells){
      const ref=xmlFE05Attr(cell,'r'),match=typeof ref==='string'?/^([A-Z]+)(\d+)$/.exec(ref):null;
      if(!match||Number(match[2])!==rowNumber||Object.hasOwn(values,match[1]))fail('invalid_holdings_cell_address');
      if(cell.children.some(c=>typeof c==='object'&&(c.uri!==FE05_XML_MAIN||!['v','is','f'].includes(c.local))))fail('invalid_holdings_xml');
      if(xmlFE05Children(cell,'f').length)fail('invalid_holdings_xml');
      const value=valueFE05Cell(cell,strings);values[match[1]]=value===null?'':value;
    }
    out.push({rowNumber,cells:values});
  }
  return out;
}
function sourceDate(value){
  const m=typeof value==='string'&&value.trim().match(/^As of (\d{1,2})-([A-Za-z]{3})-(\d{4})$/);if(!m||!MONTHS[m[2].toUpperCase()])fail('invalid_holdings_asof_date');
  const result=`${m[3]}-${MONTHS[m[2].toUpperCase()]}-${m[1].padStart(2,'0')}`;if(!date(result))fail('invalid_holdings_asof_date');return result;
}
export async function parseFE05SpyHoldingsXlsx(input){
  const parts=await zipParts(input),workbook=parseFE05XML(parts.get('xl/workbook.xml'));
  if(workbook?.local!=='workbook'||workbook.uri!==FE05_XML_MAIN)fail('invalid_holdings_xml');
  const sheets=xmlFE05Child(workbook,'sheets',FE05_XML_MAIN,{required:true}),sheetNodes=xmlFE05Children(sheets,'sheet');
  if(sheets.children.some(c=>typeof c==='object'&&(c.local!=='sheet'||c.uri!==FE05_XML_MAIN))||sheetNodes.length!==1
    ||xmlFE05Attr(sheetNodes[0],'name')!=='holdings'||xmlFE05Attr(sheetNodes[0],'sheetId')!=='1'||xmlFE05Attr(sheetNodes[0],'id',FE05_XML_OFFICE_REL)!=='rId1')fail('unexpected_holdings_workbook');
  const rels=parseFE05XML(parts.get('xl/_rels/workbook.xml.rels'));
  if(rels?.local!=='Relationships'||rels.uri!==FE05_XML_PACKAGE_REL)fail('invalid_holdings_xml');
  const relationships=rels.children.filter(c=>typeof c==='object'&&c.local==='Relationship'&&c.uri===FE05_XML_PACKAGE_REL);
  if(rels.children.some(c=>typeof c==='object'&&(c.local!=='Relationship'||c.uri!==FE05_XML_PACKAGE_REL))||relationships.some(r=>xmlFE05Attr(r,'TargetMode')?.toLowerCase()==='external'))fail('invalid_holdings_xml');
  const rel=relationships.filter(r=>xmlFE05Attr(r,'Id')==='rId1');
  const target=rel.length===1?xmlFE05Attr(rel[0],'Target'):null;
  if(rel.length!==1||typeof target!=='string'||target!=='worksheets/sheet1.xml'||target.startsWith('/')||target.includes('\\')||target.split('/').some(part=>!part||part==='.'||part==='..')||xmlFE05Attr(rel[0],'TargetMode')||xmlFE05Attr(rel[0],'Type')!==FE05_XML_OFFICE_REL+'/worksheet')fail('invalid_holdings_xml');
  const worksheetPath='xl/'+target;if(!parts.has(worksheetPath))fail('invalid_holdings_xml');
  const strings=sharedStringList(parseFE05XML(parts.get('xl/sharedStrings.xml'))),rows=parseSheetRows(parseFE05XML(parts.get(worksheetPath)),strings);
  const rowByNumber=new Map(rows.map(r=>[r.rowNumber,r.cells]));
  if(rowByNumber.get(1)?.A!=='Fund Name:'||rowByNumber.get(1)?.B!=='State Street® SPDR® S&P 500® ETF Trust'||rowByNumber.get(2)?.A!=='Ticker Symbol:'||rowByNumber.get(2)?.B!=='SPY'||rowByNumber.get(3)?.A!=='Holdings:')fail('unexpected_spy_workbook_identity');
  const asOf=sourceDate(rowByNumber.get(3)?.B);
  const headerRow=rows.find(r=>r.rowNumber<=20&&r.cells.A==='Name'&&r.cells.B==='Ticker'&&r.cells.C==='Identifier'&&r.cells.E==='Weight'&&r.cells.F==='Sector'&&r.cells.H==='Local Currency');
  if(!headerRow)fail('unexpected_holdings_headers');
  const data=[];let inPositions=false,ended=false;
  for(const r of rows.filter(x=>x.rowNumber>headerRow.rowNumber)){
    const c=r.cells,required=[c.A,c.B,c.C,c.E,c.H],blank=required.every(v=>v===undefined||v==='');
    if(blank){if(inPositions)ended=true;continue;}
    if(ended){if(c.C!==undefined&&c.C!==''&&c.E!==undefined&&c.E!=='')fail('unexpected_noncontiguous_holdings_rows');continue;}
    if(required.some(v=>v===undefined||v===''))fail('invalid_holdings_position_row');
    inPositions=true;data.push(r);
  }
  if(data.length<FE05_BREADTH_POLICY.source_snapshot_contract.position_rows_min||data.length>FE05_BREADTH_POLICY.source_snapshot_contract.position_rows_max)fail('unexpected_holdings_row_count');
  const positions=data.map(r=>{
    const c=r.cells,w=Number(c.E);
    if(typeof c.A!=='string'||!c.A||typeof c.B!=='string'||typeof c.C!=='string'||!Number.isFinite(w)||w<=0||w>100||c.H!=='USD')fail('invalid_holdings_position');
    return {source_row:r.rowNumber,name:c.A,ticker:c.B,identifier:c.C,weight_percent:w,sector:typeof c.F==='string'?c.F:'',local_currency:c.H};
  });
  const identifiers=new Set();for(const p of positions){if(identifiers.has(p.identifier))fail('duplicate_holdings_identifier');identifiers.add(p.identifier);}
  const total=positions.reduce((s,p)=>s+p.weight_percent,0);if(!Number.isFinite(total)||total<FE05_BREADTH_POLICY.source_snapshot_contract.reported_weight_total_percent_min||total>FE05_BREADTH_POLICY.source_snapshot_contract.reported_weight_total_percent_max)fail('unreconciled_holdings_total');
  return {product:'SPY',as_of_date:asOf,as_of_granularity:'date_only',source_position_count:positions.length,position_weight_total_percent:total,
    unreconciled_weight_percent:100-total,positions};
}

function requireExcluded(p,name,ticker){
  if(p.name!==name||p.ticker!==ticker||p.local_currency!=='USD')fail('excluded_holding_identity_mismatch');
}
export function selectFE05TopIssuerCohort(holdings){
  if(!holdings||holdings.product!=='SPY'||!date(holdings.as_of_date)||!Array.isArray(holdings.positions)||holdings.positions.length<FE05_BREADTH_POLICY.source_snapshot_contract.position_rows_min||holdings.positions.length>FE05_BREADTH_POLICY.source_snapshot_contract.position_rows_max
    ||!Number.isFinite(holdings.position_weight_total_percent)||holdings.position_weight_total_percent<FE05_BREADTH_POLICY.source_snapshot_contract.reported_weight_total_percent_min||holdings.position_weight_total_percent>FE05_BREADTH_POLICY.source_snapshot_contract.reported_weight_total_percent_max)fail('invalid_holdings_snapshot');
  const groups=new Map(),identifiers=new Set(),tickers=new Set(),excluded=[];
  for(const p of holdings.positions){
    if(!p||typeof p.name!=='string'||typeof p.ticker!=='string'||typeof p.identifier!=='string'||!Number.isFinite(p.weight_percent)||p.weight_percent<=0||p.local_currency!=='USD')fail('invalid_holdings_position');
    if(identifiers.has(p.identifier))fail('duplicate_holdings_identifier');identifiers.add(p.identifier);
    if(p.identifier==='999USDZ92'){requireExcluded(p,'US DOLLAR','-');excluded.push(p.identifier);continue;}
    if(p.identifier==='436CVR021'){requireExcluded(p,'CONTRA HOLOGIC INCORPO','2602335D');excluded.push(p.identifier);continue;}
    if(!validCUSIP(p.identifier))fail('unknown_equity_identifier_format');
    if(!/^[A-Z][A-Z0-9.-]{0,9}$/.test(p.ticker))fail('unknown_equity_ticker_format');
    if(tickers.has(p.ticker))fail('duplicate_provider_ticker');tickers.add(p.ticker);
    const issuer=p.identifier.slice(0,6);let g=groups.get(issuer);if(!g){g={issuer_key:issuer,weight_percent:0,securities:[]};groups.set(issuer,g);}
    g.weight_percent+=p.weight_percent;g.securities.push({symbol:p.ticker,identifier:p.identifier,weight_percent:p.weight_percent});
  }
  if(excluded.length!==2||groups.size<25)fail('incomplete_holdings_universe');
  const ranked=[...groups.values()].sort((a,b)=>b.weight_percent-a.weight_percent||a.issuer_key.localeCompare(b.issuer_key));
  const issuers=ranked.slice(0,25);if(issuers.length!==25||issuers.some(g=>!Number.isFinite(g.weight_percent)||g.weight_percent<=0))fail('incomplete_top_issuer_cohort');
  const securities=issuers.flatMap(g=>g.securities);if(securities.length<25||securities.length>FE05_BREADTH_POLICY.universe.max_security_lines)fail('issuer_cohort_symbol_bound_exceeded');
  const selectedWeight=issuers.reduce((s,g)=>s+g.weight_percent,0),symbols=securities.map(s=>s.symbol);
  if(!Number.isFinite(selectedWeight)||selectedWeight<=0||new Set(symbols).size!==symbols.length)fail('invalid_top_issuer_weight');
  return {as_of_date:holdings.as_of_date,source_position_count:holdings.positions.length,position_weight_total_percent:holdings.position_weight_total_percent,
    unreconciled_weight_percent:holdings.unreconciled_weight_percent,excluded_position_count:excluded.length,issuer_count:issuers.length,
    security_line_count:securities.length,selected_weight_percent:selectedWeight,issuer_keys:issuers.map(g=>g.issuer_key),issuers,securities,symbols};
}

function requireReturns(values,name){if(!values.every(Number.isFinite))fail('nonfinite_'+name);return values;}
export function computeFE05BreadthMeasurements(cohort,closesBySymbol,dates,cutoffIndex=Array.isArray(dates)?dates.length-1:-1){
  if(!cohort||cohort.issuer_count!==25||!Array.isArray(cohort.issuers)||cohort.issuers.length!==25||!Array.isArray(cohort.securities)||cohort.securities.length<25||cohort.securities.length>35
    ||!Array.isArray(dates)||dates.length<505||dates.some((d,i)=>!date(d)||(i&&d<=dates[i-1]))||!Number.isInteger(cutoffIndex)||cutoffIndex<504||cutoffIndex>=dates.length)fail('invalid_breadth_cohort_or_dates');
  const expected=[...cohort.securities.map(s=>s.symbol),'SPY'].sort(),actual=closesBySymbol&&typeof closesBySymbol==='object'&&!Array.isArray(closesBySymbol)?Object.keys(closesBySymbol).sort():[];
  if(expected.length!==actual.length||expected.some((s,i)=>s!==actual[i]))fail('invalid_breadth_price_panel');
  for(const symbol of expected){const a=closesBySymbol[symbol];if(!Array.isArray(a)||a.length!==dates.length||a.some(x=>typeof x!=='number'||!Number.isFinite(x)||x<=0))fail('invalid_breadth_price_series');}
  dates=dates.slice(cutoffIndex-504,cutoffIndex+1);closesBySymbol=Object.fromEntries(expected.map(symbol=>[symbol,closesBySymbol[symbol].slice(cutoffIndex-504,cutoffIndex+1)]));cutoffIndex=504;
  const selectedWeight=cohort.issuers.reduce((s,g)=>s+g.weight_percent,0);if(!Number.isFinite(selectedWeight)||selectedWeight<=0||Math.abs(selectedWeight-cohort.selected_weight_percent)>1e-9)fail('invalid_breadth_weight_denominator');
  const issuerReturns=[],issuerIndices=[];
  for(const group of cohort.issuers){
    if(!Array.isArray(group.securities)||!group.securities.length||group.securities.some(s=>s.identifier.slice(0,6)!==group.issuer_key))fail('issuer_mapping_mismatch');
    const groupWeight=group.securities.reduce((s,x)=>s+x.weight_percent,0);if(Math.abs(groupWeight-group.weight_percent)>1e-9)fail('issuer_weight_mismatch');
    const r=Array.from({length:504},(_,i)=>group.securities.reduce((s,x)=>s+x.weight_percent*Math.log(closesBySymbol[x.symbol][i+1]/closesBySymbol[x.symbol][i]),0)/groupWeight);
    requireReturns(r,'issuer_return');const px=[1];for(const x of r)px.push(px.at(-1)*Math.exp(x));issuerReturns.push(r);issuerIndices.push(px);
  }
  const breadth=new Array(505).fill(null),highLow=new Array(505).fill(null);
  for(let i=1;i<505;i++)breadth[i]=cohort.issuers.reduce((s,g,j)=>s+g.weight_percent*Math.sign(issuerReturns[j][i-1]),0)/selectedWeight;
  for(let i=252;i<505;i++)highLow[i]=cohort.issuers.reduce((s,g,j)=>{
    const px=issuerIndices[j],prior=px.slice(i-252,i),high=Math.max(...prior),low=Math.min(...prior);
    return s+g.weight_percent*(px[i]>high?1:px[i]<low?-1:0);
  },0)/selectedWeight;
  const indexReturns=Array.from({length:485},(_,j)=>Math.log(closesBySymbol.SPY[j+20]/closesBySymbol.SPY[j]));
  requireReturns(indexReturns,'spy_20_session_return');
  const t=504,priorBreadth=breadth.slice(t-252,t),priorHL=highLow.slice(t-252,t),priorTrend=indexReturns.slice(232,484);
  if(priorBreadth.length!==252||priorBreadth.some(x=>!Number.isFinite(x))||priorHL.length!==252||priorHL.some(x=>!Number.isFinite(x))||priorTrend.length!==252)fail('insufficient_breadth_normalization');
  const bStats=stats(priorBreadth,'advance_decline'),hlStats=stats(priorHL,'new_high_low'),trendStats=stats(priorTrend,'index_trend');
  const currentBreadth=breadth[t],currentHL=highLow[t],currentTrend=indexReturns[484];
  const features={breadth_delta:currentBreadth,advance_decline_z:(currentBreadth-bStats.mean)/bStats.population_sd,
    new_high_low_z:(currentHL-hlStats.mean)/hlStats.population_sd,index_trend_z:(currentTrend-trendStats.mean)/trendStats.population_sd};
  if(Object.values(features).some(x=>!Number.isFinite(x))||currentBreadth < -1||currentBreadth>1)fail('invalid_breadth_features');
  return {features,measurements:{cohort_issuer_count:25,cohort_security_line_count:cohort.securities.length,
    position_weight_total_percent:cohort.position_weight_total_percent,unreconciled_weight_percent:cohort.unreconciled_weight_percent,
    selected_cohort_weight_percent:cohort.selected_weight_percent,selected_cohort_fraction_of_reported_holdings:cohort.selected_weight_percent/cohort.position_weight_total_percent,
    source_position_count:cohort.source_position_count,excluded_position_count:cohort.excluded_position_count,
    latest_breadth_delta:currentBreadth,latest_new_high_low_ratio:currentHL,spy_20_session_log_return:currentTrend,
    normalization:{advance_decline:{current:currentBreadth,...bStats,prior_count:252,current_excluded:true,prior_start_index:252,prior_end_index:503},
      new_high_low:{current:currentHL,...hlStats,prior_count:252,current_excluded:true,prior_start_index:252,prior_end_index:503},
      index_trend:{current:currentTrend,...trendStats,prior_count:252,current_excluded:true,prior_start_index:252,prior_end_index:503}},
    historical_membership_backfill:false,market_population_claim:false,all_member_rows_required:true,missing_interval_fill:false}};
}

export function buildFE05SourceForecast({holdings,cohort,dates,closesBySymbol,calendarCapture,calendarSessions,holdingsCapture,barsCaptures,evaluationAt}){
  const empty={schema:'SHIPYARD_FE05_SOURCE_FORECAST_V1',engine_id:'FE05',feature_origin:'provider_capture_new_policy',feature_policy:FE05_BREADTH_POLICY,feature_policy_sha256:FE05_BREADTH_POLICY_SHA256,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,calibrated_probability:null,historical_point_in_time_claim:false,market_population_claim:false,redistribution_rights_cleared:false}};
  if(!holdings||!cohort||holdings.as_of_date!==cohort.as_of_date||!date(holdings.as_of_date)||!isoInstant(evaluationAt)||!Array.isArray(dates)||dates.length!==505||dates.at(-1)!==holdings.as_of_date
    ||!calendarCapture||calendarCapture.operation!=='official_calendar'||calendarCapture.subject!=='US_EQUITY'
    ||!holdingsCapture||holdingsCapture.operation!=='spy_holdings_xlsx'||holdingsCapture.subject!=='SPY'||!Array.isArray(barsCaptures)||barsCaptures.length<1||barsCaptures.length>3
    ||barsCaptures.some(r=>r.operation!=='historical_multi_symbol_1Day_page'||r.subject!=='FE05_TOP25_ISSUER_COHORT'))fail('invalid_breadth_source_receipts');
  const evalMs=Date.parse(evaluationAt),validCapture=(r,operation,subject)=>r?.operation===operation&&r.subject===subject&&r.http_status===200
    &&[r.request_started_at,r.http_response_received_at,r.received_at].every(isoInstant)&&Date.parse(r.request_started_at)<=Date.parse(r.http_response_received_at)
    &&Date.parse(r.http_response_received_at)<=Date.parse(r.received_at)&&Date.parse(r.received_at)<=evalMs&&/^[a-f0-9]{64}$/.test(r.response_sha256||'')&&r.hash_serialization==='raw_response_bytes';
  const safeURL=(r,origin,path)=>{let u;try{u=new URL(r.request_url);}catch{return null;}return u.origin===origin&&u.pathname===path?u:null;};
  const hUrl=safeURL(holdingsCapture,'https://www.ssga.com','/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx');
  const cUrl=safeURL(calendarCapture,'https://paper-api.alpaca.markets','/v2/calendar');
  const barSymbols=[...cohort.securities.map(s=>s.symbol),'SPY'].sort(),firstSession=dates[0];
  const evaluationDate=NY_DATE_FORMAT.format(new Date(evalMs)),calendarStart=cUrl?.searchParams.get('start'),calendarEnd=cUrl?.searchParams.get('end');
  if(!validCapture(holdingsCapture,'spy_holdings_xlsx','SPY')||!validCapture(calendarCapture,'official_calendar','US_EQUITY')||!hUrl||!cUrl
    ||[...hUrl.searchParams.keys()].length||[...cUrl.searchParams.keys()].sort().join(',')!=='end,start'
    ||!date(calendarStart)||!date(calendarEnd)||calendarStart>holdings.as_of_date||calendarEnd<holdings.as_of_date||calendarEnd>evaluationDate
    ||Date.parse(holdings.as_of_date+'T00:00:00Z')-Date.parse(calendarStart+'T00:00:00Z')>FE05_BREADTH_POLICY.calendar_lookback_days*86400000
    ||Date.parse(holdingsCapture.received_at)>Date.parse(calendarCapture.request_started_at))fail('invalid_breadth_source_receipts');
  let rows=0,priorReceipt=calendarCapture;
  for(let i=0;i<barsCaptures.length;i++){
    const r=barsCaptures[i],u=safeURL(r,'https://data.alpaca.markets','/v2/stocks/bars'),page=r.page_index;
    const required='adjustment,asof,currency,end,feed,limit,sort,start,symbols,timeframe';
    if(!validCapture(r,'historical_multi_symbol_1Day_page','FE05_TOP25_ISSUER_COHORT')||!u||!Number.isInteger(page)||page!==i+1
      ||[...u.searchParams.keys()].filter(k=>k!=='page_token').sort().join(',')!==required||u.searchParams.get('symbols')!==barSymbols.join(',')
      ||u.searchParams.get('timeframe')!=='1Day'||u.searchParams.get('feed')!=='iex'||u.searchParams.get('adjustment')!=='split'||u.searchParams.get('currency')!=='USD'
      ||u.searchParams.get('sort')!=='asc'||u.searchParams.get('limit')!=='7000'||u.searchParams.get('asof')!==holdings.as_of_date
      ||(page===1?u.searchParams.has('page_token'):u.searchParams.get('page_token')!=='[continuation]')||r.has_next_page!==(i<barsCaptures.length-1)
      ||!Number.isInteger(r.provider_rows)||r.provider_rows<0||r.provider_rows>7000||Date.parse(priorReceipt.received_at)>Date.parse(r.request_started_at))fail('invalid_breadth_source_receipts');
    const barStart=Date.parse(u.searchParams.get('start')||''),barEnd=Date.parse(u.searchParams.get('end')||'');
    if(!Number.isFinite(barStart)||!Number.isFinite(barEnd)||barStart>=barEnd||NY_DATE_FORMAT.format(new Date(barStart))!==firstSession||NY_DATE_FORMAT.format(new Date(barEnd))!==holdings.as_of_date)fail('invalid_breadth_source_receipts');
    rows+=r.provider_rows;priorReceipt=r;
  }
  if(rows!==barSymbols.length*505)fail('invalid_breadth_source_receipts');
  const computed=computeFE05BreadthMeasurements(cohort,closesBySymbol,dates,504),freshness=qualifyFE05DateOnlyFreshness({sourceAsOf:holdings.as_of_date,evaluationAt,calendarCapture,calendarSessions,selectedDates:dates});
  const source={provider:'Alpaca Market Data + State Street Investment Management',feed:'iex',adjustment:'split',timeframe:'1Day',currency:'USD',price_basis:'split_adjusted_dividend_excluded',
      holdings_url:POLICY_SOURCE,holdings_asof_date:holdings.as_of_date,holdings_asof_granularity:'date_only',symbol_asof:holdings.as_of_date,first_seen_is_not_observation:true,
      universe:{kind:'current_SPY_holdings_top25_issuer_cohort',issuer_count:25,security_line_count:cohort.securities.length,selected_weight_percent:cohort.selected_weight_percent,
        position_weight_total_percent:cohort.position_weight_total_percent,unreconciled_weight_percent:cohort.unreconciled_weight_percent,excluded_position_count:cohort.excluded_position_count,
        issuer_identifier_scheme:'CUSIP-9 first-six issuer key',member_names_and_symbols_returned:false,market_population_claim:false,historical_membership_backfill:false},
      rights_attestation:null,quality_score:null,source_policy_fingerprint:hash({policy:FE05_BREADTH_POLICY,as_of_date:holdings.as_of_date,position_count:holdings.source_position_count,weight_total:holdings.position_weight_total_percent}),
      pagination_complete:true,selected_bars_sha256:hash({dates,closesBySymbol}),calendar:{selected_session_count:dates.length,selected_first_session:dates[0],selected_last_session:dates.at(-1),provider_response_received:true,completeness_independently_verified:false},
      calendar_evaluation_coverage:{requested_start_date:calendarStart,requested_end_date:calendarEnd,required_end_date:evaluationDate,
        complete_through_evaluation_date:freshness.calendar_coverage.complete_through_evaluation_date,completeness_independently_verified:false,
        provider_request_covers_evaluation_date:freshness.calendar_coverage.provider_request_covers_evaluation_date,
        provider_rows_structurally_valid:freshness.calendar_coverage.provider_rows_structurally_valid,
        provider_selected_dates_covered:freshness.calendar_coverage.provider_selected_dates_covered,
        provider_session_count:freshness.calendar_coverage.provider_returned_row_count,provider_returned_last_date:freshness.calendar_coverage.provider_returned_last_date},
      captures:[holdingsCapture,calendarCapture,...barsCaptures].map(publicCapture)};
  const common={...empty,computed_at:evaluationAt,evaluation_at:evaluationAt,as_of_date:holdings.as_of_date,source_as_of:holdings.as_of_date,source,freshness,
    coverage:{required_sessions:505,complete_sessions:505,used_daily_bars_per_security:505,matched_calendar_sessions:505,cohort_issuer_count:25,cohort_security_line_count:cohort.securities.length,
      required_symbols_count:cohort.securities.length+1,universe_symbols_returned:false,missing_intervals_filled:false,survivor_replacements:0}};
  if(!freshness.freshness_eligible){
    const reasons=[];
    if(freshness.source_age_max_age_status==='age_bounds_overlap_max_age')reasons.push('source_age_interval_overlaps_max_age');
    if(freshness.source_age_max_age_status==='definitely_stale')reasons.push('source_age_interval_definitely_exceeds_max_age');
    if(!freshness.calendar_coverage.provider_request_covers_evaluation_date||!freshness.calendar_coverage.provider_selected_dates_covered)reasons.push('provider_calendar_coverage_unavailable');
    const bounds=freshness.source_age_bounds_seconds,ageText=`${bounds.lower_bound.toFixed(0)}–${bounds.upper_bound.toFixed(0)} seconds`,observed=freshness.observed_returned_completed_sessions_after_source_asof_count===null?'unavailable':String(freshness.observed_returned_completed_sessions_after_source_asof_count);
    const message=`FE05 freshness abstained: date-only source as-of ${holdings.as_of_date} has a conservative age interval of ${ageText} against the 172800-second max; exact observation/publication time remains unknown. Provider calendar coverage is ${freshness.calendar_coverage.status}; ${observed} completed returned rows were observed after the source date. Independent calendar completeness is unverified; exact market-session lag is unknown. No scorer was invoked; decision eligibility remains false.`;
    return {...common,status:'abstained',message,abstention_reasons:reasons,diagnostic_only:true,
      diagnostic_only_values:{features:computed.features,measurements:computed.measurements,scorer:{invoked:false,status:'not_invoked',reason:'source_freshness_not_qualified'}}};
  }
  const calc=evaluateForecastEngine('FE05',computed.features);
  if(calc.status!=='research_only_score'||!Number.isFinite(calc.model_score))fail('breadth_scorer_unavailable');
  return {...common,status:'computed',features:computed.features,measurements:computed.measurements,calculator_result:calc};
}
