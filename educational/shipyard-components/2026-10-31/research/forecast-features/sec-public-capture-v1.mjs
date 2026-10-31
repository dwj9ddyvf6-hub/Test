// Bounded, fixed-destination GETs for public SEC endpoints. This module has no
// credentials, custom URL/header input, retry loop, cache, or persistence.
// Importing it is inert; callers must explicitly invoke one of the functions.
import {createHash} from 'node:crypto';
import {parseSecForm4Xml} from './sec-public-adapters-v1.mjs';

export const SEC_PUBLIC_CAPTURE_POLICY=Object.freeze({
  id:'SEC_PUBLIC_FIXED_GET_CAPTURE_V1',version:1,network_enabled:true,requires_authentication:false,
  user_agent:'ShipyardResearchTerminal/1.0',
  allowed_origins:Object.freeze(['https://data.sec.gov','https://www.sec.gov']),
  max_requests_per_shared_budget_per_second:2,max_in_flight_requests:2,sec_public_fair_access_ceiling_per_second:10,
  max_response_bytes:Object.freeze({submissions_json:8*1024*1024,companyfacts_json:16*1024*1024,form4_xml:1024*1024}),timeout_ms:15000,
  retries:0,redirects:'rejected',credentials:'omit',method:'GET',
  endpoints:Object.freeze({submissions:'https://data.sec.gov/submissions/CIK{CIK}.json',
    companyfacts:'https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json',
    form4_xml:'https://www.sec.gov/Archives/edgar/data/{CIK_UNPADDED}/{ACCESSION_COMPACT}/{PRIMARY_XML}'}),
  historical_point_in_time_claim:false,
});

const fail=(code,requestAttempted=false)=>({status:['local_sec_rate_limit','sec_capture_capacity_exhausted'].includes(code)?'busy':'unavailable',error:code,request_attempted:requestAttempted,
  network_enabled:true,source_family:null,payload:null,receipt:null});
// One module-level budget is shared across all factory-created clients in this
// runtime isolate; there is no per-instance reset or waiting queue.
const sharedBudget={lastStartMs:-Infinity,inFlight:0};
const bytes=text=>new TextEncoder().encode(text).length;
function normalizeCik(value){
  const raw=String(value??'').trim();
  if(!/^\d{1,10}$/.test(raw))return null;
  const cik=raw.padStart(10,'0');return cik==='0000000000'?null:cik;
}
function sha256(text){return createHash('sha256').update(text).digest('hex');}
function captureTime(clock){
  const value=clock();if(value instanceof Date&&!Number.isFinite(value.getTime()))return null;
  const instant=value instanceof Date?value.toISOString():String(value??'');
  const m=instant.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|([+-])(\d{2}):(\d{2}))$/);
  if(!m||!Number.isFinite(Date.parse(instant))||new Date(Date.parse(m[1]+'T00:00:00Z')).toISOString().slice(0,10)!==m[1]||
    Number(m[2])>23||Number(m[3])>59||Number(m[4])>59||(m[5]!=='Z'&&(Number(m[7])>23||Number(m[8])>59)))return null;
  return new Date(Date.parse(instant)).toISOString();
}
function assertBeforeDeadline(signal){
  if(signal?.aborted)throw signal.reason??Object.assign(new Error('SEC request deadline exceeded'),{name:'TimeoutError'});
}
function discardResponseBody(response){
  try{const pending=response?.body?.cancel?.();pending?.catch?.(()=>{});}catch{}
}
async function boundedText(response,maxBytes,signal){
  assertBeforeDeadline(signal);
  const declared=Number(response.headers?.get?.('content-length'));
  if(Number.isFinite(declared)&&declared>maxBytes)throw Object.assign(new Error('response_body_limit_exceeded'),{code:'response_body_limit_exceeded'});
  if(response.body?.getReader){
    const reader=response.body.getReader(),parts=[];let length=0;
    const onAbort=()=>{void reader.cancel().catch(()=>{});};
    signal?.addEventListener('abort',onAbort,{once:true});
    try{
      while(true){assertBeforeDeadline(signal);const {done,value}=await reader.read();assertBeforeDeadline(signal);if(done)break;length+=value.byteLength;if(length>maxBytes){void reader.cancel().catch(()=>{});throw Object.assign(new Error('response_body_limit_exceeded'),{code:'response_body_limit_exceeded'});}parts.push(value);}
    }finally{signal?.removeEventListener('abort',onAbort);reader.releaseLock?.();}
    const joined=new Uint8Array(length);let offset=0;for(const part of parts){joined.set(part,offset);offset+=part.byteLength;}
    try{return new TextDecoder('utf-8',{fatal:true}).decode(joined);}catch{throw Object.assign(new Error('response_body_not_utf8'),{code:'response_body_not_utf8'});}
  }
  const textPromise=response.text();let deadlineHandler=null;
  const deadlinePromise=signal?new Promise((_,reject)=>{deadlineHandler=()=>reject(signal.reason??Object.assign(new Error('SEC request deadline exceeded'),{name:'TimeoutError'}));signal.addEventListener('abort',deadlineHandler,{once:true});}):null;
  let text;
  try{text=deadlinePromise?await Promise.race([textPromise,deadlinePromise]):await textPromise;}
  finally{if(deadlineHandler)signal.removeEventListener('abort',deadlineHandler);}
  assertBeforeDeadline(signal);
  if(bytes(text)>maxBytes)throw Object.assign(new Error('response_body_limit_exceeded'),{code:'response_body_limit_exceeded'});return text;
}

function failCode(error){
  const code=String(error?.code??'');return /^[a-z0-9_]{1,80}$/.test(code)?code:'sec_request_failed';
}

export function createSecPublicCaptureClient({fetchImpl=globalThis.fetch,clock=()=>new Date(),timeout_ms=SEC_PUBLIC_CAPTURE_POLICY.timeout_ms}={}){
  const requestedTimeout=Number(timeout_ms);
  const timeoutMs=Number.isFinite(requestedTimeout)&&requestedTimeout>=1?Math.min(SEC_PUBLIC_CAPTURE_POLICY.timeout_ms,Math.floor(requestedTimeout)):SEC_PUBLIC_CAPTURE_POLICY.timeout_ms;
  async function get({url,accept,maxBytes,sourceFamily,expectedCik,decode}){
    if(typeof fetchImpl!=='function')return fail('fetch_unavailable');
    const start=performance.now();
    if(!Number.isFinite(start))return fail('monotonic_clock_invalid');
    if(sharedBudget.inFlight>=SEC_PUBLIC_CAPTURE_POLICY.max_in_flight_requests)return fail('sec_capture_capacity_exhausted');
    if(start-sharedBudget.lastStartMs<500)return fail('local_sec_rate_limit');
    sharedBudget.lastStartMs=start;sharedBudget.inFlight++;
    let response,body,requestAttempted=false,signal=null;
    try{
      signal=AbortSignal.timeout(timeoutMs);
      requestAttempted=true;
      response=await fetchImpl(url,{method:'GET',headers:{'User-Agent':SEC_PUBLIC_CAPTURE_POLICY.user_agent,Accept:accept},
        redirect:'manual',credentials:'omit',cache:'no-store',signal});
      if(response.status>=300&&response.status<400){await discardResponseBody(response);return fail('redirect_rejected',true);}
      if(response.status!==200){await discardResponseBody(response);return fail(`http_status_${response.status}`,true);}
      const contentType=String(response.headers?.get?.('content-type')??'').toLowerCase();
      if(contentType&&!decode.contentType.test(contentType)){await discardResponseBody(response);return fail('unexpected_content_type',true);}
      body=await boundedText(response,maxBytes,signal);
      const decoded=decode.parse(body);
      const observedCik=normalizeCik(decoded?.cik);
      if(!observedCik||observedCik!==expectedCik)return fail('response_cik_identity_mismatch',true);
      const capturedAt=captureTime(clock);if(!capturedAt)return fail('capture_clock_invalid',true);
      if(sourceFamily==='SEC_FORM4_ARCHIVES_XML'){
        const parsed=parseSecForm4Xml(decoded.text,{accession:decode.accession,issuer_cik:expectedCik,form:decode.form,captured_at:capturedAt});
        if(parsed.status!=='parsed'||parsed.issuer_cik!==expectedCik||parsed.accession!==decode.accession)return fail('form4_xml_identity_or_schema_unverified',true);
      }
      const receipt={source_family:sourceFamily,source_origin:new URL(url).origin,endpoint_id:decode.endpointId,
        request_method:'GET',request_path:new URL(url).pathname,http_status:200,content_type:contentType||'not_reported',
        captured_at:capturedAt,response_bytes:bytes(body),response_sha256:sha256(body),response_cik:observedCik,
        user_agent:SEC_PUBLIC_CAPTURE_POLICY.user_agent,credentials:'omitted',redirects:'not_followed',retries:0,
        request_budget:{scope:'module_shared',max_requests_per_second:SEC_PUBLIC_CAPTURE_POLICY.max_requests_per_shared_budget_per_second,
          max_in_flight:SEC_PUBLIC_CAPTURE_POLICY.max_in_flight_requests,max_response_bytes:maxBytes,timeout_ms:timeoutMs},
        historical_point_in_time_claim:false};
      return {status:'captured',source_family:sourceFamily,cik:observedCik,captured_at:capturedAt,payload:decoded,receipt,
        warnings:['PUBLIC_SOURCE_CAPTURE_IS_NOT_HISTORICAL_POINT_IN_TIME_PROOF','LIVE_SITE_PROVIDER_BINDING_REMAINS_UNVERIFIED']};
    }catch(error){return fail(signal?.aborted||error?.name==='TimeoutError'?'sec_capture_deadline_exceeded':failCode(error),requestAttempted);}
    finally{sharedBudget.inFlight=Math.max(0,sharedBudget.inFlight-1);}
  }
  return Object.freeze({
    fetchSubmissions(cikInput){
      const cik=normalizeCik(cikInput);if(!cik)return Promise.resolve(fail('invalid_cik'));
      const url=`https://data.sec.gov/submissions/CIK${cik}.json`;
      return get({url,accept:'application/json',maxBytes:SEC_PUBLIC_CAPTURE_POLICY.max_response_bytes.submissions_json,
        sourceFamily:'SEC_SUBMISSIONS_API',expectedCik:cik,decode:{endpointId:'sec_submissions_by_cik_v1',contentType:/json/,
          parse:text=>JSON.parse(text)}});
    },
    fetchCompanyFacts(cikInput){
      const cik=normalizeCik(cikInput);if(!cik)return Promise.resolve(fail('invalid_cik'));
      const url=`https://data.sec.gov/api/xbrl/companyfacts/CIK${cik}.json`;
      return get({url,accept:'application/json',maxBytes:SEC_PUBLIC_CAPTURE_POLICY.max_response_bytes.companyfacts_json,
        sourceFamily:'SEC_COMPANYFACTS_API',expectedCik:cik,decode:{endpointId:'sec_companyfacts_by_cik_v1',contentType:/json/,
          parse:text=>JSON.parse(text)}});
    },
    fetchForm4Xml({cik:cikInput,accession,primary_document,form}={}){
      const cik=normalizeCik(cikInput),acc=String(accession??''),doc=String(primary_document??'');
      if(!cik)return Promise.resolve(fail('invalid_cik'));
      if(!/^\d{10}-\d{2}-\d{6}$/.test(acc))return Promise.resolve(fail('invalid_accession_number'));
      if(!['4','4/A'].includes(String(form??'')))return Promise.resolve(fail('unsupported_form4_type'));
      const segments=doc.split('/');
      if(!doc||doc.length>240||segments.some(part=>!part||part==='.'||part==='..'||! /^[A-Za-z0-9_.-]+$/.test(part))||!segments.at(-1).toLowerCase().endsWith('.xml'))
        return Promise.resolve(fail('unsafe_form4_primary_document_path'));
      const compact=acc.replaceAll('-','');
      const path=segments.map(part=>encodeURIComponent(part)).join('/');
      const url=`https://www.sec.gov/Archives/edgar/data/${Number(cik)}/${compact}/${path}`;
      return get({url,accept:'application/xml,text/xml;q=0.9',maxBytes:SEC_PUBLIC_CAPTURE_POLICY.max_response_bytes.form4_xml,
        sourceFamily:'SEC_FORM4_ARCHIVES_XML',expectedCik:cik,decode:{endpointId:'sec_form4_primary_xml_v1',contentType:/xml|text\/plain/,accession:acc,form:String(form),
          parse:text=>({cik,text})}}).then(result=>result.status==='captured'?{...result,accession:acc,form:String(form),primary_document:doc}:result);
    },
  });
}

let defaultClient;
function client(){return defaultClient??=createSecPublicCaptureClient();}
export const fetchSecSubmissions=cik=>client().fetchSubmissions(cik);
export const fetchSecCompanyFacts=cik=>client().fetchCompanyFacts(cik);
export const fetchSecForm4Xml=filing=>client().fetchForm4Xml(filing);
