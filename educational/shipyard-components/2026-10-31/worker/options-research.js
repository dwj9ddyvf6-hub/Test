// NEW source-only research adapter. Deliberately independent of Trade Brain's
// entry gates. Host dependencies: brokerCredentials, readBoundedBody and json.
// Integration must remain behind the existing owner authorization boundary.
const SHIPYARD_OPTIONS_RESEARCH_POLICY = Object.freeze({
  id: 'TRADIER_STANDARD_OPTIONS_RESEARCH_V1',
  quote_current_max_age_seconds: 900, greeks_current_max_age_seconds: 5400,
  max_provider_bytes: 2 * 1024 * 1024, max_provider_contracts: 2000,
  max_expirations: 512, max_page_contracts: 100, max_output_bytes: 256 * 1024,
  request_timeout_ms: 10000, max_provider_requests_per_call: 3,
  standard_contract_size: 100, include_all_roots: false,
});
const SHIPYARD_OPTIONS_MARKET_SNAPSHOT_MAX_PROVIDER_REQUESTS = 4;
const SHIPYARD_OPTIONS_RESEARCH_WINDOWS = new Map();
const SHIPYARD_OPTIONS_GREEK_DENIAL_TABLE = 'shipyard_tradier_options_greek_denials';
let SHIPYARD_OPTIONS_GREEK_DENIAL_MEMORY = null;

function optionsResearchObject(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
function optionsResearchDate(value) {
  return typeof value === 'string' && /^20\d{2}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value + 'T00:00:00Z'))
    && new Date(value + 'T00:00:00Z').toISOString().slice(0,10) === value;
}
function optionsResearchToday(now) {
  return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(now));
}
function optionsResearchNumber(value, min, max, integer = false) {
  return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max && (!integer || Number.isSafeInteger(value)) ? value : null;
}
function optionsResearchGreekNumber(greeks, key, optionType) {
  const iv=key.endsWith('_iv')||key==='smv_vol';
  const min=key==='delta'?(optionType==='call'?0:-1):iv||['gamma','vega'].includes(key)?0:-1000000;
  const max=key==='delta'?(optionType==='call'?1:0):iv?100:1000000;
  return optionsResearchNumber(greeks?.[key],iv?Number.MIN_VALUE:min,max);
}
function optionsResearchClock(value, now, iso = false) {
  if (value === undefined || value === null || value === 0 || value === '') return { at:null, age_seconds:null, status:'missing', source_unit:null };
  let ms, unit;
  if (iso) {
    if (typeof value !== 'string' || !/^20\d{2}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,3})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value) || !optionsResearchDate(value.slice(0,10))) return {at:null,age_seconds:null,status:'invalid',source_unit:null};
    ms=Date.parse(value); unit='ISO-8601';
  } else {
    // Preserve the explicit input unit in the output. Never use receipt time as
    // a source clock. Legacy epoch-seconds and epoch-ms occupy disjoint ranges.
    if (!Number.isSafeInteger(value)) return {at:null,age_seconds:null,status:'invalid',source_unit:null};
    if (value >= 946684800000 && value < 4102444800000) { ms=value; unit='unix_milliseconds'; }
    else if (value >= 946684800 && value < 4102444800) { ms=value*1000; unit='unix_seconds'; }
  }
  if (!Number.isFinite(ms) || ms < 946684800000 || ms > now) return {at:null,age_seconds:null,status:'invalid',source_unit:null};
  return {at:new Date(ms).toISOString(),age_seconds:(now-ms)/1000,status:'valid',source_unit:unit};
}
// Diagnostic context is not a source clock and never admits Greek values.
// Echo only bounded timestamp-shaped scalars, not arbitrary provider strings.
function optionsResearchClockDiagnostic(value, now) {
  const type=value===undefined?'absent':value===null?'null':Array.isArray(value)?'array':typeof value;
  const safeString=typeof value==='string'&&value.length<=80&&/^[0-9TtZz :.+/\-]*$/.test(value);
  const raw=safeString?value:typeof value==='number'&&Number.isFinite(value)?value:null;
  const clock=optionsResearchClock(value,now,true);
  let reason;
  if(value===undefined||value===null||value===''||value===0)reason='missing_source_clock';
  else if(typeof value!=='string')reason='expected_iso8601_string';
  else if(value.length>80)reason='source_clock_string_too_long';
  else if(!safeString)reason='non_timestamp_characters_redacted';
  else if(!optionsResearchDate(value.slice(0,10)))reason='invalid_calendar_date';
  else if(/^20\d{2}-\d{2}-\d{2}[T ][0-2]\d:[0-5]\d:[0-5]\d(?:\.\d{1,3})?$/.test(value))reason='timezone_missing_not_inferred';
  else if(clock.status==='valid')reason='valid_explicit_timezone_source_clock';
  else if(/^20\d{2}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,3})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value)&&Number.isFinite(Date.parse(value))&&Date.parse(value)>now)reason='source_clock_in_future';
  else reason='unsupported_iso8601_format_or_range';
  return {raw_updated_at:raw,raw_type:type,raw_redacted:value!=null&&raw===null,validation_reason:reason,clock_status:clock.status,timezone_inferred:false};
}
function optionsResearchRejectedIdentity(raw, reason) {
  const row=optionsResearchObject(raw)?raw:{};
  const safe=(key,pattern,max)=>typeof row[key]==='string'&&row[key].length<=max&&pattern.test(row[key])?row[key]:null;
  return {reason,symbol:safe('symbol',/^[A-Z0-9.]+$/,32),underlying:safe('underlying',/^[A-Z0-9.]+$/,10),root_symbol:safe('root_symbol',/^[A-Z0-9.]+$/,10),
    expiration_date:safe('expiration_date',/^\d{4}-\d{2}-\d{2}$/,10),option_type:['call','put'].includes(row.option_type)?row.option_type:null,
    strike:optionsResearchNumber(row.strike,0,1000000),contract_size:optionsResearchNumber(row.contract_size,0,1000000)};
}
function optionsResearchRestrictions() {
  return {research_only:true,source_only:true,execution_pricing:false,decision_eligible:false,discretionary_research_input:true,order_submission_enabled:false,account_data_returned:false,
    continuous_stream:false,selected_page_quote_stream_available:true,whole_market_coverage:false,options_flow:false,derived_features_computed:false,completed_models:[],
    potential_feature_consumers:['FE14','FE15','FE17'],feature_consumer_status:'additional_inputs_and_reviewed_feature_policies_required'};
}
function optionsResearchBase(kind, now) {
  return {schema:'SHIPYARD_OPTIONS_RESEARCH_V1',kind,provider:'tradier',source:'Tradier brokerage production API',
    policy:SHIPYARD_OPTIONS_RESEARCH_POLICY,restrictions:optionsResearchRestrictions(),requested_at:new Date(now).toISOString(),
    retrieved_at:null,market_session:'unknown_not_requested',status:'unavailable',error:null,symbol:null,expiration:null,
    source_receipts:[],contracts:[],expirations:[],
    source_access:{configured:null,request_succeeded:false,validated_data_observed:false,scope:kind==='chain'?'one_standard_option_chain':'one_underlying_expirations',ongoing_entitlement_proven:false},
    freshness:{quote_status:'missing',greeks_status:'missing',source_as_of:null,source_as_of_basis:null,open_interest_as_of:null,
      note:'Source clocks and retrieval clocks are distinct. Valid last-available values are retained even when stale; current means only within the declared research age threshold, never executable or market-open.'},
    coverage:{complete_provider_response:false,provider_rows:0,accepted_rows:0,rejected_rows:0,returned_rows:0,rejection_reasons:{},rejected_identity_examples:[],rejected_identity_examples_limit:5,field_issues:{},all_roots:false,whole_market:false},
    pagination:{provider_pagination:'not_supported_not_followed',offset:0,limit:null,next_offset:null,next_after_symbol:null,has_more:false,same_snapshot_across_pages:false,page_response_sha256:null,
      combination_rule:'Each page is a new provider capture. Pass next_after_symbol to continue; source clocks and rows may change between pages. Pages are not a simultaneous chain snapshot.'}};
}
function optionsResearchStoredDenial(row,revision) {
  if(!optionsResearchObject(row)||row.provider!=='tradier'||row.operation!=='options_greeks'||row.connection_revision!==revision||row.http_status!==403
    ||typeof row.denied_at!=='string'||row.denied_at.length>64||!/^20\d{2}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d\.\d{3}Z$/.test(row.denied_at))return null;
  const milliseconds=Date.parse(row.denied_at);
  if(!Number.isFinite(milliseconds)||new Date(milliseconds).toISOString()!==row.denied_at)return null;
  return {provider:'tradier',operation:'options_greeks',connection_revision:revision,http_status:403,denied_at:row.denied_at};
}
async function optionsResearchGreekDenialState(env,revision) {
  if(typeof revision!=='string'||!revision||revision.length>64)return {status:'unavailable'};
  if(SHIPYARD_OPTIONS_GREEK_DENIAL_MEMORY?.connection_revision===revision)return {status:'denied',persisted:false,receipt:SHIPYARD_OPTIONS_GREEK_DENIAL_MEMORY};
  if(!env?.DB||typeof env.DB.prepare!=='function')return {status:'unavailable'};
  try {
    const row=await env.DB.prepare(`SELECT provider,operation,connection_revision,http_status,denied_at FROM ${SHIPYARD_OPTIONS_GREEK_DENIAL_TABLE} WHERE provider=? AND operation=? AND connection_revision=?`)
      .bind('tradier','options_greeks',revision).first();
    if(!row)return {status:'clear'};
    const receipt=optionsResearchStoredDenial(row,revision);
    return receipt?{status:'denied',persisted:true,receipt}:{status:'unavailable'};
  } catch { return {status:'unavailable'}; }
}
async function optionsResearchPersistGreekDenial(env,revision,deniedAt) {
  if(!env?.DB||typeof env.DB.prepare!=='function'||typeof revision!=='string'||!revision||revision.length>64
    ||typeof deniedAt!=='string'||!/^20\d{2}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d\.\d{3}Z$/.test(deniedAt)||!Number.isFinite(Date.parse(deniedAt)))throw Error('greek_denial_storage_unavailable');
  const result=await env.DB.prepare(`INSERT OR IGNORE INTO ${SHIPYARD_OPTIONS_GREEK_DENIAL_TABLE} (provider,operation,connection_revision,http_status,denied_at) VALUES (?,?,?,?,?)`)
    .bind('tradier','options_greeks',revision,403,deniedAt).run();
  if(result?.success===false)throw Error('greek_denial_storage_unavailable');
  const row=await env.DB.prepare(`SELECT provider,operation,connection_revision,http_status,denied_at FROM ${SHIPYARD_OPTIONS_GREEK_DENIAL_TABLE} WHERE provider=? AND operation=? AND connection_revision=?`)
    .bind('tradier','options_greeks',revision).first();
  const receipt=optionsResearchStoredDenial(row,revision);
  if(!receipt)throw Error('greek_denial_storage_unavailable');
  return receipt;
}
function optionsResearchGreekDenialStatus(base,state) {
  const receipt=state.receipt;
  base.greeks_enrichment={status:'suppressed',source:'Tradier options/greeks · ORATS',error:'tradier_requested_data_not_entitled',provider_rows:null,
    matched_contracts:0,rejected_rows:0,invalid_clock_rows:0,source_receipt_index:null,
    denial_suppression:{status:state.persisted?'persisted':'process_local_only',persisted:state.persisted===true,
      http_status:receipt.http_status,denied_at:receipt.denied_at,automatic_recheck:false}};
}
function optionsResearchArgs(args, kind, now) {
  const allowed=kind==='chain'?['symbol','expiration','limit','offset','after_symbol']:['symbol'];
  if(!optionsResearchObject(args)||Object.keys(args).some(k=>!allowed.includes(k))||typeof args.symbol!=='string'||!/^[A-Za-z]{1,6}$/.test(args.symbol))throw Error('invalid_arguments');
  const out={symbol:args.symbol.toUpperCase()};
  if(kind==='chain') {
    const today=optionsResearchToday(now);
    if(!optionsResearchDate(args.expiration)||args.expiration<today||Date.parse(args.expiration+'T00:00:00Z')>now+5*366*86400000)throw Error('invalid_expiration');
    out.expiration=args.expiration;out.limit=args.limit===undefined?50:args.limit;out.offset=args.offset===undefined?0:args.offset;
    if(!Number.isSafeInteger(out.limit)||out.limit<1||out.limit>100||!Number.isSafeInteger(out.offset)||out.offset<0||out.offset>=2000)throw Error('invalid_pagination_arguments');
    if(out.offset>0&&args.after_symbol===undefined)throw Error('invalid_page_cursor_required');
    if(args.after_symbol!==undefined) {
      if(typeof args.after_symbol!=='string')throw Error('invalid_after_symbol');
      const match=args.after_symbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/);
      const cursorExpiration=match?`20${match[2].slice(0,2)}-${match[2].slice(2,4)}-${match[2].slice(4,6)}`:null;
      if(!match||match[1]!==out.symbol||cursorExpiration!==out.expiration||!optionsResearchDate(cursorExpiration))throw Error('invalid_after_symbol');
      out.after_symbol=args.after_symbol;
    }
  }
  return out;
}
function optionsResearchRateAllowed(request, now) {
  const key=request.headers.get('cf-connecting-ip')||'owner';
  const prior=SHIPYARD_OPTIONS_RESEARCH_WINDOWS.get(key);
  const row=!prior||now<prior.started||now-prior.started>=60000?{started:now,count:0}:prior;
  row.count++;SHIPYARD_OPTIONS_RESEARCH_WINDOWS.set(key,row);
  while(SHIPYARD_OPTIONS_RESEARCH_WINDOWS.size>128)SHIPYARD_OPTIONS_RESEARCH_WINDOWS.delete(SHIPYARD_OPTIONS_RESEARCH_WINDOWS.keys().next().value);
  return row.count<=12;
}
function optionsResearchNoPagination(payload, wrapper) {
  for(const object of [payload,wrapper])if(optionsResearchObject(object)) {
    for(const key of ['next_page_token','nextPageToken','next_page','next','cursor','continuation_token','has_more','hasMore']) {
      if(Object.hasOwn(object,key)&&![null,'',false].includes(object[key]))throw Error('unsupported_provider_pagination');
    }
    if(object.links?.next||object._links?.next||object.pagination?.next||object.pagination?.has_more||object.pagination?.next_page_token)throw Error('unsupported_provider_pagination');
    // Any otherwise unknown pagination envelope is not evidence of completion.
    if(Object.hasOwn(object,'pagination')&&object.pagination!==null)throw Error('unsupported_provider_pagination');
  }
}
async function optionsResearchFetch(request, credentials, kind, args, base, beforeRequest = null) {
  const path=kind==='chain'?'/v1/markets/options/chains':kind==='greeks'?'/v1/markets/options/greeks':'/v1/markets/options/expirations';
  const url=new URL('https://api.tradier.com'+path);
  const query=kind==='chain'?{symbol:args.symbol,expiration:args.expiration,greeks:'true'}:kind==='greeks'?{symbol:args.symbol,expiration:args.expiration}:{symbol:args.symbol,includeAllRoots:'false',strikes:'false'};
  for(const [key,value] of Object.entries(query))url.searchParams.set(key,value);
  const started=Date.now(),signal=AbortSignal.any([request.signal,AbortSignal.timeout(SHIPYARD_OPTIONS_RESEARCH_POLICY.request_timeout_ms)]);
  if(beforeRequest)beforeRequest();
  const response=await fetch(url.toString(),{method:'GET',headers:{authorization:`Bearer ${credentials.token}`,accept:'application/json'},redirect:'manual',signal});
  const receipt={operation:kind==='chain'?'options_chain':kind==='greeks'?'options_greeks':'options_expirations',request_url:url.toString(),request_started_at:new Date(started).toISOString(),
    http_response_received_at:new Date().toISOString(),received_at:null,http_status:response.status,response_sha256:null,response_bytes:null,
    hash_serialization:'SHA-256 of UTF-8 re-encoding of decoded response text'};
  base.source_receipts.push(receipt);
  if(response.status>=300&&response.status<400)throw Error('provider_redirect_rejected');
  let body;
  try {body=await readBoundedBody(response,kind==='expirations'?128*1024:SHIPYARD_OPTIONS_RESEARCH_POLICY.max_provider_bytes);}
  catch(error) {if(signal.aborted)throw error;throw Error(error?.message==='response too large'?'provider_response_bound_exceeded':'provider_body_invalid');}
  if(Date.now()<started)throw Error('acquisition_clock_invalid');
  if(Date.now()-started>=SHIPYARD_OPTIONS_RESEARCH_POLICY.request_timeout_ms)throw Error('source_request_timeout');
  receipt.received_at=new Date().toISOString();
  receipt.response_bytes=new TextEncoder().encode(body).byteLength;
  receipt.response_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body))),b=>b.toString(16).padStart(2,'0')).join('');
  if(response.status===429||(response.status===400&&body.includes('Quota Violation')))throw Error('provider_rate_limited');
  if(!response.ok)throw Error(response.status===401?'tradier_authentication_failed':response.status===403?'tradier_requested_data_not_entitled':'provider_unavailable');
  let payload;try{payload=JSON.parse(body);}catch{throw Error('provider_schema_invalid');}
  if(!optionsResearchObject(payload)||Object.hasOwn(payload,'errors')||Object.hasOwn(payload,'error'))throw Error('provider_schema_invalid');
  if(payload.symbol!==undefined&&payload.symbol!==args.symbol||payload.underlying!==undefined&&payload.underlying!==args.symbol)throw Error('provider_identity_mismatch');
  base.source_access.request_succeeded=true;base.retrieved_at=receipt.received_at;
  return payload;
}
function optionsResearchExpirations(payload,args,now,base) {
  if(!Object.hasOwn(payload,'expirations'))throw Error('provider_schema_invalid');
  const wrapper=payload.expirations;optionsResearchNoPagination(payload,wrapper);
  if(wrapper!==null&&(!optionsResearchObject(wrapper)||!Object.hasOwn(wrapper,'date')))throw Error('provider_schema_invalid');
  if(wrapper?.symbol!==undefined&&wrapper.symbol!==args.symbol)throw Error('provider_identity_mismatch');
  const raw=wrapper?.date;
  const dates=raw===null||wrapper===null?[]:typeof raw==='string'?[raw]:raw;
  if(!Array.isArray(dates))throw Error('provider_schema_invalid');
  if(dates.length>512)throw Error('provider_row_bound_exceeded');
  const today=optionsResearchToday(now),seen=new Set();
  for(const date of dates) {
    if(!optionsResearchDate(date)||date<today||Date.parse(date+'T00:00:00Z')>now+5*366*86400000||seen.has(date))throw Error('provider_expirations_invalid');
    seen.add(date);
  }
  base.expirations=[...dates].sort();base.status=dates.length?'current':'missing';
  base.source_access.validated_data_observed=dates.length>0;
  Object.assign(base.coverage,{complete_provider_response:true,provider_rows:dates.length,accepted_rows:dates.length,returned_rows:dates.length});
  base.freshness.source_as_of_basis='provider_does_not_supply_expiration_list_as_of';
  base.expiration_list_as_of=null;
  base.note='Expiration discovery only; a listed date does not prove chain, quote or Greek access. Null/empty is no available expirations, not a usable chain.';
}
function optionsResearchCount(target,key) {target[key]=(target[key]||0)+1;}
function optionsResearchContract(raw,args,now,issues) {
  if(!optionsResearchObject(raw))throw Error('contract_schema_invalid');
  const match=typeof raw.symbol==='string'?raw.symbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/):null;
  const expiration=match?`20${match[2].slice(0,2)}-${match[2].slice(2,4)}-${match[2].slice(4,6)}`:null;
  if(!match||!optionsResearchDate(expiration)||match[1]!==args.symbol||raw.underlying!==args.symbol||raw.root_symbol!==args.symbol
    ||expiration!==args.expiration||raw.expiration_date!==args.expiration||raw.option_type!==(match[3]==='C'?'call':'put')
    ||optionsResearchNumber(raw.strike,0.001,99999.999)!==Number(match[4])/1000||raw.type!==undefined&&raw.type!=='option')throw Error('contract_identity_invalid');
  if(raw.contract_size!==100)throw Error('nonstandard_or_missing_multiplier');
  const issue=name=>optionsResearchCount(issues,name);
  const number=(key,min,max,integer=false)=>{const v=optionsResearchNumber(raw[key],min,max,integer);if(v===null)issue((raw[key]==null?'missing_':'invalid_')+key);return v;};
  const price=(side,dateKey)=>{
    const clock=optionsResearchClock(raw[dateKey],now),value=number(side,0,1000000);
    if(clock.status!=='valid'){issue(clock.status+'_'+dateKey);return {value:null,at:null,age_seconds:null,state:clock.status==='invalid'?'invalid':'missing',source_unit:null};}
    return {value,at:clock.at,age_seconds:clock.age_seconds,state:value===null?'missing':clock.age_seconds<=900?'current':'stale',source_unit:clock.source_unit};
  };
  const bid=price('bid','bid_date'),ask=price('ask','ask_date'),last=price('last','trade_date');
  if(bid.value!==null&&ask.value!==null&&ask.value<bid.value) {
    issue('crossed_quote');bid.value=null;ask.value=null;bid.state='invalid';ask.state='invalid';
  }
  const states=[bid.state,ask.state],quoteState=states.every(x=>x==='current')?'current':states.every(x=>['current','stale'].includes(x))?'stale':states.some(x=>['current','stale'].includes(x))?'partial':'missing';
  const quoteAt=bid.value!==null&&ask.value!==null?[bid.at,ask.at].sort()[0]:null;
  const greekKeys=['delta','gamma','theta','vega','rho','phi','bid_iv','mid_iv','ask_iv','smv_vol'];
  const fieldStatus=Object.fromEntries(greekKeys.map(key=>[key,'missing']));
  const greeks={source_clock_diagnostic:optionsResearchClockDiagnostic(raw.greeks?.updated_at,now),source_updated_at:optionsResearchClock(raw.greeks?.updated_at,now,true).status==='valid'?raw.greeks.updated_at:null,source:'ORATS via Tradier',cadence:'approximately_hourly_not_tick_live',status:'missing',field_status:fieldStatus,as_of:null,age_seconds:null,
    reported_status:'missing',reported_as_of:null,reported_values:Object.fromEntries(greekKeys.map(k=>[k,null])),
    reported_implied_volatility:null,reported_implied_volatility_units:null,units:'provider_raw_no_rescaling; Greek convention must be reviewed before risk calculations',values:Object.fromEntries(greekKeys.map(k=>[k,null]))};
  if(raw.greeks!=null) {
    if(!optionsResearchObject(raw.greeks))issue('invalid_greeks');
    else {
      const clock=optionsResearchClock(raw.greeks.updated_at,now,true);
      if(clock.status!=='valid'){
        issue(clock.status+'_greeks_updated_at');
        let reported=0;
        for(const key of greekKeys) {
          const value=optionsResearchGreekNumber(raw.greeks,key,raw.option_type);
          if(value!==null){greeks.reported_values[key]=value;reported++;}
          if(raw.greeks[key]!==undefined&&raw.greeks[key]!==null)greeks.field_status[key]='invalid_clock';
        }
        if(reported)greeks.reported_status='clock_unqualified';
      }
      else {
        greeks.as_of=clock.at;greeks.age_seconds=clock.age_seconds;
        let valid=0;
        for(const key of greekKeys) {
          const value=optionsResearchGreekNumber(raw.greeks,key,raw.option_type);
          if(value===null){issue((raw.greeks[key]==null?'missing_':'invalid_')+'greek_'+key);greeks.field_status[key]=raw.greeks[key]==null?'missing':'invalid';}
          else {greeks.values[key]=value;greeks.field_status[key]=clock.age_seconds<=5400?'current':'stale';valid++;}
        }
        if(greeks.values.bid_iv!==null&&greeks.values.ask_iv!==null&&greeks.values.bid_iv>greeks.values.ask_iv) {
          issue('crossed_greek_iv');greeks.values.bid_iv=null;greeks.values.ask_iv=null;greeks.field_status.bid_iv='invalid';greeks.field_status.ask_iv='invalid';valid-=2;
        }
        greeks.status=valid===0?'missing':valid<greekKeys.length?'partial':clock.age_seconds<=5400?'current':'stale';
      }
    }
  } else issue('missing_greeks');
  return {symbol:raw.symbol,underlying:args.symbol,root_symbol:raw.root_symbol,expiration:args.expiration,option_type:raw.option_type,strike:raw.strike,
    contract_size:100,identity_validated:true,standard_contract:true,execution_pricing:false,
    quote:{status:quoteState,bid:bid.value,ask:ask.value,last:last.value,bid_at:bid.at,ask_at:ask.at,last_at:last.at,
      bid_age_seconds:bid.age_seconds,ask_age_seconds:ask.age_seconds,last_age_seconds:last.age_seconds,
      bid_state:bid.state,ask_state:ask.state,last_state:last.state,quote_at:quoteAt,
      bid_size:number('bidsize',0,Number.MAX_SAFE_INTEGER,true),ask_size:number('asksize',0,Number.MAX_SAFE_INTEGER,true),
      source_timestamps:{bid_date:Number.isSafeInteger(raw.bid_date)?raw.bid_date:null,ask_date:Number.isSafeInteger(raw.ask_date)?raw.ask_date:null,trade_date:Number.isSafeInteger(raw.trade_date)?raw.trade_date:null},
      displayed_size_units:'unknown_provider_documentation_not_verified',displayed_sizes_rescaled:false,
      clock_units:{bid:bid.source_unit,ask:ask.source_unit,last:last.source_unit},price_units:'USD_per_share_as_reported_no_rescaling',
      midpoint:null,midpoint_computed:false},
    greeks,open_interest:{value:number('open_interest',0,Number.MAX_SAFE_INTEGER,true),as_of:null,as_of_status:'unknown_provider_does_not_supply',units:'contracts'},
    volume:{value:number('volume',0,Number.MAX_SAFE_INTEGER,true),as_of:null,as_of_status:'unknown_provider_does_not_supply',units:'contracts'}};
}
function optionsResearchChain(payload,args,now,base) {
  if(!Object.hasOwn(payload,'options'))throw Error('provider_schema_invalid');
  const wrapper=payload.options;optionsResearchNoPagination(payload,wrapper);
  if(wrapper!==null&&(!optionsResearchObject(wrapper)||!Object.hasOwn(wrapper,'option')))throw Error('provider_schema_invalid');
  if(wrapper?.symbol!==undefined&&wrapper.symbol!==args.symbol||wrapper?.underlying!==undefined&&wrapper.underlying!==args.symbol||wrapper?.expiration!==undefined&&wrapper.expiration!==args.expiration)throw Error('provider_identity_mismatch');
  const raw=wrapper?.option;
  const rows=wrapper===null||raw===null?[]:Array.isArray(raw)?raw:optionsResearchObject(raw)?[raw]:null;
  if(!rows)throw Error('provider_schema_invalid');
  if(rows.length>2000)throw Error('provider_row_bound_exceeded');
  const accepted=[],seen=new Set();
  for(const row of rows) {
    if(optionsResearchObject(row)&&typeof row.symbol==='string') {
      if(seen.has(row.symbol))throw Error('duplicate_contract_identity');
      seen.add(row.symbol);
    }
    try {accepted.push(optionsResearchContract(row,args,now,base.coverage.field_issues));}
    catch(error) {const code=['contract_schema_invalid','contract_identity_invalid','nonstandard_or_missing_multiplier'].includes(error.message)?error.message:'contract_schema_invalid';optionsResearchCount(base.coverage.rejection_reasons,code);if(base.coverage.rejected_identity_examples.length<5)base.coverage.rejected_identity_examples.push(optionsResearchRejectedIdentity(row,code));}
  }
  accepted.sort((a,b)=>a.strike-b.strike||a.option_type.localeCompare(b.option_type)||a.symbol.localeCompare(b.symbol));
  Object.assign(base.coverage,{complete_provider_response:true,provider_rows:rows.length,accepted_rows:accepted.length,rejected_rows:rows.length-accepted.length});
  const statusFor=key=>accepted.length===0?'missing':accepted.every(c=>c[key].status==='current')?'current':accepted.every(c=>['current','stale'].includes(c[key].status))?'stale':accepted.every(c=>c[key].status==='missing')?'missing':'partial';
  base.freshness.quote_status=statusFor('quote');base.freshness.greeks_status=statusFor('greeks');
  const clocks=accepted.map(c=>c.quote.quote_at).filter(Boolean);
  base.freshness.source_as_of=clocks.length?clocks.sort()[0]:null;
  base.freshness.source_as_of_basis='oldest_accepted_two_sided_quote; not a chain-wide simultaneous snapshot';
  base.source_access.validated_data_observed=accepted.length>0;
  const missing=accepted.some(c=>['missing','partial'].includes(c.quote.status)||['missing','partial'].includes(c.greeks.status));
  base.status=rows.length===0?'missing':accepted.length===0?'unavailable':base.coverage.rejected_rows||missing||Object.keys(base.coverage.field_issues).length?'partial':accepted.some(c=>c.quote.status==='stale'||c.greeks.status==='stale')?'stale':'current';
  if(rows.length&&!accepted.length)base.error='no_valid_standard_contracts';
  let start=args.offset;
  if(args.after_symbol!==undefined) {
    const cursorIndex=accepted.findIndex(contract=>contract.symbol===args.after_symbol);
    if(cursorIndex<0)throw Error('pagination_cursor_unavailable');
    start=cursorIndex+1;
  }
  base.contracts=accepted.slice(start,start+args.limit);base.coverage.returned_rows=base.contracts.length;
  const hasMore=start+args.limit<accepted.length;
  Object.assign(base.pagination,{offset:start,limit:args.limit,has_more:hasMore,next_offset:hasMore?start+base.contracts.length:null,
    next_after_symbol:hasMore?base.contracts.at(-1)?.symbol??null:null,page_response_sha256:base.source_receipts[0]?.response_sha256??null});
  base.note='One expiration only; not options flow, historical chain storage or a completed forecast. Valid stale prices/Greeks remain available for research. Invalid/future values are null, never repaired; rejected contracts are counted. OI/volume as-of is unknown. When embedded ORATS clocks or values are incomplete, a separately receipted Tradier Greeks read may supplement matching OCC contracts. If that provider is unavailable or supplies no usable clock, Alpaca indicative snapshots may supply matching provider Greeks; their Greek-specific clock remains unknown, quotes are modified and trades are delayed 15 minutes. Every page fetches a new complete provider response; source clocks and chain rows can change between pages, so pages are not simultaneous.';
}
function optionsResearchChainRowsForGreeks(payload) {
  if(!optionsResearchObject(payload)||!optionsResearchObject(payload.options)||!Object.hasOwn(payload.options,'option'))return null;
  const raw=payload.options.option;
  if(raw===null)return [];
  return Array.isArray(raw)?raw:optionsResearchObject(raw)?[raw]:null;
}
function optionsResearchNeedsGreekAcquisition(payload,args,now) {
  const rows=optionsResearchChainRowsForGreeks(payload);
  if(!rows||rows.length===0||rows.length>2000)return false;
  const seen=new Set();
  for(const row of rows) {
    if(!optionsResearchObject(row)||typeof row.symbol!=='string')continue;
    const match=row.symbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/);
    if(!match)continue;
    const expiration='20'+match[2].slice(0,2)+'-'+match[2].slice(2,4)+'-'+match[2].slice(4,6);
    if(match[1]!==args.symbol||expiration!==args.expiration||row.underlying!==args.symbol||row.root_symbol!==args.symbol
      ||row.expiration_date!==args.expiration||row.option_type!==(match[3]==='C'?'call':'put')
      ||optionsResearchNumber(row.strike,0.001,99999.999)!==Number(match[4])/1000||row.contract_size!==100)continue;
    if(seen.has(row.symbol))return false;
    seen.add(row.symbol);
    const raw=row.greeks;
    if(!optionsResearchObject(raw)||optionsResearchClock(raw.updated_at,now,true).status!=='valid'
      ||['delta','gamma','theta','vega','rho','phi','bid_iv','mid_iv','ask_iv','smv_vol'].some(key=>raw[key]===null||raw[key]===undefined))return true;
  }
  return false;
}
function optionsResearchGreekMap(payload,args,now,base) {
  if(!optionsResearchObject(payload)||!Object.hasOwn(payload,'greeks'))throw Error('provider_schema_invalid');
  const wrapper=payload.greeks;optionsResearchNoPagination(payload,wrapper);
  if(wrapper!==null&&(!optionsResearchObject(wrapper)||!Object.hasOwn(wrapper,'greek')))throw Error('provider_schema_invalid');
  if(wrapper?.symbol!==undefined&&wrapper.symbol!==args.symbol||wrapper?.underlying!==undefined&&wrapper.underlying!==args.symbol
    ||wrapper?.expiration!==undefined&&wrapper.expiration!==args.expiration)throw Error('provider_identity_mismatch');
  const raw=wrapper===null?[]:wrapper.greek;
  const rows=raw===null?[]:Array.isArray(raw)?raw:optionsResearchObject(raw)?[raw]:null;
  if(!rows)throw Error('provider_schema_invalid');
  if(rows.length>2000)throw Error('provider_row_bound_exceeded');
  const result=new Map();let rejected=0,invalidClocks=0;
  for(const row of rows) {
    const match=optionsResearchObject(row)&&typeof row.symbol==='string'?row.symbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/):null;
    const expiration=match?'20'+match[2].slice(0,2)+'-'+match[2].slice(2,4)+'-'+match[2].slice(4,6):null;
    if(!match||!optionsResearchDate(expiration)||match[1]!==args.symbol||expiration!==args.expiration
      ||row.option_type!==undefined&&row.option_type!==(match[3]==='C'?'call':'put')){rejected++;continue;}
    if(result.has(row.symbol))throw Error('duplicate_contract_identity');
    if(optionsResearchClock(row.updated_at,now,true).status!=='valid'){invalidClocks++;continue;}
    result.set(row.symbol,row);
  }
  base.greeks_enrichment={status:result.size?'available':'missing',source:'Tradier options/greeks · ORATS',provider_rows:rows.length,
    matched_contracts:0,rejected_rows:rejected,invalid_clock_rows:invalidClocks,source_receipt_index:base.source_receipts.length-1};
  return result;
}
function optionsResearchWithSupplementalGreeks(payload,greeks,base) {
  const rows=optionsResearchChainRowsForGreeks(payload),matched=new Set();
  if(!rows)return payload;
  const optionRows=rows.map(row=>{
    const supplemental=optionsResearchObject(row)&&typeof row.symbol==='string'?greeks.get(row.symbol):null;
    if(!supplemental)return row;
    matched.add(row.symbol);
    return {...row,greeks:supplemental};
  });
  if(base.greeks_enrichment) {
    base.greeks_enrichment.matched_contracts=matched.size;
    base.greeks_enrichment.status=matched.size?'available':'missing';
  }
  return {...payload,options:{...payload.options,option:optionRows}};
}
async function optionsResearchEnrichChainGreeks(request,args,credentials,payload,base,beforeRequest=null,env=null,connectionRevision=null) {
  if(!optionsResearchNeedsGreekAcquisition(payload,args,Date.now()))return payload;
  const denial=await optionsResearchGreekDenialState(env,connectionRevision);
  if(denial.status==='denied') {optionsResearchGreekDenialStatus(base,denial);return payload;}
  if(denial.status==='unavailable') {
    base.greeks_enrichment={status:'suppression_state_unavailable',source:'Tradier options/greeks · ORATS',error:'greek_denial_storage_unavailable',provider_rows:null,
      matched_contracts:0,rejected_rows:0,invalid_clock_rows:0,source_receipt_index:null,denial_suppression:{status:'unavailable',persisted:false,automatic_recheck:false}};
    return payload;
  }
  try {
    if(base.source_receipts.length>=SHIPYARD_OPTIONS_RESEARCH_POLICY.max_provider_requests_per_call)throw Error('provider_request_budget_exceeded');
    if(!optionsResearchRateAllowed(request,Date.now()))throw Error('rate_limited');
    const greekPayload=await optionsResearchFetch(request,credentials,'greeks',args,base,beforeRequest);
    const greeks=optionsResearchGreekMap(greekPayload,args,Date.now(),base);
    return optionsResearchWithSupplementalGreeks(payload,greeks,base);
  } catch(error) {
    optionsResearchGreekEnrichmentError(error,base);
    if(error?.message==='tradier_requested_data_not_entitled') {
      const sourceReceipt=base.source_receipts.at(-1),deniedAt=sourceReceipt?.operation==='options_greeks'?sourceReceipt.received_at:null;
      try {
        const receipt=await optionsResearchPersistGreekDenial(env,connectionRevision,deniedAt);
        base.greeks_enrichment.denial_suppression={status:'persisted',persisted:true,http_status:403,denied_at:receipt.denied_at,automatic_recheck:false};
      } catch {
        // A known 403 is still suppressed in this worker when its durable write
        // fails; subsequent reads never re-probe while the same revision is held.
        if(typeof connectionRevision==='string'&&connectionRevision)SHIPYARD_OPTIONS_GREEK_DENIAL_MEMORY={connection_revision:connectionRevision,http_status:403,denied_at:deniedAt||new Date().toISOString()};
        base.greeks_enrichment.status='denial_storage_unavailable';
        base.greeks_enrichment.denial_suppression={status:'persistence_unavailable_process_local_suppression',persisted:false,
          http_status:403,denied_at:deniedAt||null,automatic_recheck:false};
      }
    }
    return payload;
  }
}
function optionsResearchGreekEnrichmentError(error,base) {
  const allowed=['provider_rate_limited','tradier_authentication_failed','tradier_requested_data_not_entitled','provider_unavailable',
    'provider_redirect_rejected','provider_response_bound_exceeded','provider_body_invalid','provider_schema_invalid',
    'provider_identity_mismatch','provider_row_bound_exceeded','unsupported_provider_pagination','duplicate_contract_identity',
    'source_request_timeout','acquisition_clock_invalid','cancelled','rate_limited','provider_request_budget_exceeded'];
  const code=error?.name==='TimeoutError'?'source_request_timeout':allowed.includes(error?.message)?error.message:'provider_unavailable';
  base.greeks_enrichment={status:'unavailable',source:'Tradier options/greeks · ORATS',error:code,provider_rows:null,
    matched_contracts:0,rejected_rows:0,invalid_clock_rows:0,source_receipt_index:base.source_receipts.length>1?base.source_receipts.length-1:null};
}
function optionsResearchAlpacaClock(value,now) {
  if(typeof value!=='string'||!/^20\d{2}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value)||!optionsResearchDate(value.slice(0,10)))return {at:null,age_seconds:null,status:'missing'};
  const normalized=value.replace(/\.(\d{1,9})(?=Z|[+-])/,(match,fraction)=>'.'+fraction.slice(0,3).padEnd(3,'0'));
  const ms=Date.parse(normalized);if(!Number.isFinite(ms))return {at:null,age_seconds:null,status:'invalid'};
  const age=(now-ms)/1000;return {at:new Date(ms).toISOString(),age_seconds:age,status:age < -5?'future':age<=90?'current':'stale'};
}
async function optionsResearchAlpacaSnapshotsFetch(request,args,contracts,env,base) {
  if(!Array.isArray(contracts)||contracts.length===0)return {snapshots:{},receipt_index:null};
  if(contracts.length>SHIPYARD_OPTIONS_RESEARCH_POLICY.max_page_contracts)throw Error('provider_request_bound_exceeded');
  const symbols=[...new Set(contracts.map(contract=>contract?.symbol).filter(symbol=>typeof symbol==='string'))];
  if(symbols.length!==contracts.length)throw Error('provider_identity_mismatch');
  const keyId=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
  if(typeof keyId!=='string'||!keyId||typeof secret!=='string'||!secret)throw Error('market_data_credentials_unavailable');
  if(typeof alpacaRateAllowed!=='function'||!alpacaRateAllowed(request,Date.now()))throw Error('provider_rate_limited');
  const url=new URL('https://data.alpaca.markets/v1beta1/options/snapshots');
  url.searchParams.set('symbols',symbols.join(','));url.searchParams.set('feed','indicative');url.searchParams.set('limit',String(symbols.length));
  const started=Date.now(),signal=AbortSignal.any([request.signal,AbortSignal.timeout(8000)]);
  const response=await fetch(url.toString(),{method:'GET',headers:{'APCA-API-KEY-ID':keyId,'APCA-API-SECRET-KEY':secret,accept:'application/json'},redirect:'manual',signal});
  const receipt={operation:'alpaca_options_indicative_snapshots',provider:'Alpaca Market Data',feed:'indicative',request_url:url.toString(),request_started_at:new Date(started).toISOString(),http_response_received_at:new Date().toISOString(),received_at:null,http_status:response.status,response_sha256:null,response_bytes:null,hash_serialization:'SHA-256 of UTF-8 re-encoding of decoded response text'};
  base.source_receipts.push(receipt);
  if(response.status>=300&&response.status<400)throw Error('provider_redirect_rejected');
  let body;try{body=await readBoundedBody(response,SHIPYARD_OPTIONS_RESEARCH_POLICY.max_provider_bytes);}catch(error){if(signal.aborted)throw error;throw Error(error?.message==='response too large'?'provider_response_bound_exceeded':'provider_body_invalid');}
  if(Date.now()<started)throw Error('acquisition_clock_invalid');
  if(Date.now()-started>=8000)throw Error('source_request_timeout');
  receipt.received_at=new Date().toISOString();receipt.response_bytes=new TextEncoder().encode(body).byteLength;
  receipt.response_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body))),b=>b.toString(16).padStart(2,'0')).join('');
  if(response.status===429)throw Error('provider_rate_limited');
  if(!response.ok)throw Error(response.status===401?'alpaca_authentication_failed':response.status===403?'alpaca_indicative_options_unavailable':'provider_unavailable');
  let payload;try{payload=JSON.parse(body);}catch{throw Error('provider_schema_invalid');}
  if(!optionsResearchObject(payload)||!optionsResearchObject(payload.snapshots)||Array.isArray(payload.snapshots))throw Error('provider_schema_invalid');
  if(payload.next_page_token!==undefined&&payload.next_page_token!==null&&payload.next_page_token!=='')throw Error('unsupported_provider_pagination');
  return {snapshots:payload.snapshots,receipt_index:base.source_receipts.length-1};
}
function optionsResearchApplyAlpacaSnapshots(result,args,contracts,prior,now) {
  const expected=new Set(contracts.map(contract=>contract.symbol)),snapshots=result.snapshots,matched=new Set();let invalidRows=0;
  for(const symbol of Object.keys(snapshots))if(!expected.has(symbol))invalidRows++;
  for(const contract of contracts) {
    const snapshot=snapshots[contract.symbol];
    if(!optionsResearchObject(snapshot))continue;
    const occ=contract.symbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/),expiration=occ?'20'+occ[2].slice(0,2)+'-'+occ[2].slice(2,4)+'-'+occ[2].slice(4,6):null;
    if(!occ||occ[1]!==args.symbol||expiration!==args.expiration||occ[3]!== (contract.option_type==='call'?'C':'P')||Number(occ[4])/1000!==contract.strike||!expected.has(contract.symbol)){invalidRows++;continue;}
    const raw=optionsResearchObject(snapshot.greeks)?snapshot.greeks:{};
    const call=contract.option_type==='call';
    const values={
      delta:optionsResearchNumber(raw.delta,call?0:-1,call?1:0),
      gamma:optionsResearchNumber(raw.gamma,0,1000000),
      theta:optionsResearchNumber(raw.theta,-1000000,1000000),
      vega:optionsResearchNumber(raw.vega,0,1000000),
      rho:optionsResearchNumber(raw.rho,-1000000,1000000),
    };
    const iv=optionsResearchNumber(snapshot.impliedVolatility,Number.MIN_VALUE,100);
    if(Object.values(values).every(value=>value===null)&&iv===null){invalidRows++;continue;}
    const quoteClock=optionsResearchAlpacaClock(snapshot.latestQuote?.t,now),tradeClock=optionsResearchAlpacaClock(snapshot.latestTrade?.t,now);
    contract.greeks={
      ...contract.greeks,source:'Alpaca indicative options snapshot',cadence:'snapshot provider analytics; Greek-specific timestamp not supplied',
      status:'clock_unknown',as_of:null,age_seconds:null,source_updated_at:null,
      source_clock_diagnostic:{status:'greek_timestamp_not_supplied'},
      values:{...(contract.greeks?.values||{}),...Object.fromEntries(Object.entries(values).filter(([,value])=>value!==null))},
      reported_implied_volatility:iv,reported_implied_volatility_units:'provider_fraction',
      indicative_snapshot:{feed:'indicative',retrieved_at:result.retrieved_at,greek_clock:'not_supplied',quote_as_of:quoteClock.at,quote_age_seconds:quoteClock.age_seconds,quote_status:quoteClock.status,trade_as_of:tradeClock.at,trade_age_seconds:tradeClock.age_seconds,trade_status:tradeClock.status,trade_delay_minutes:15,quote_prices_modified:true,source_receipt_index:result.receipt_index},
    };
    matched.add(contract.symbol);
  }
  const matchedSnapshots=Object.keys(snapshots).filter(symbol=>expected.has(symbol)).length;
  const status=matched.size?'alpaca_indicative_clock_unknown':'alpaca_indicative_missing';
  return {matched:matched.size,status,invalid_rows:invalidRows,provider_rows:Object.keys(snapshots).length,matched_snapshot_rows:matchedSnapshots,
    primary_status:prior?.status||'not_attempted',primary_error:prior?.error||null,source_receipt_index:result.receipt_index};
}
async function optionsResearchAlpacaGreeksFallback(request,args,env,base) {
  const contracts=(base.contracts||[]).filter(contract=>contract?.greeks&&!contract.greeks.as_of&&Object.values(contract.greeks.values||{}).every(value=>value===null));
  if(!contracts.length)return;
  const prior=base.greeks_enrichment||{status:'missing'};
  try {
    if(base.source_receipts.length>=SHIPYARD_OPTIONS_RESEARCH_POLICY.max_provider_requests_per_call)throw Error('provider_request_budget_exceeded');
    if(!optionsResearchRateAllowed(request,Date.now()))throw Error('rate_limited');
    const result=await optionsResearchAlpacaSnapshotsFetch(request,args,contracts,env,base);
    result.retrieved_at=base.source_receipts[result.receipt_index]?.received_at||new Date().toISOString();
    const enrichment=optionsResearchApplyAlpacaSnapshots(result,args,contracts,prior,Date.now());
    base.greeks_enrichment={status:enrichment.status,source:'Alpaca options snapshots · indicative',feed:'indicative',greek_clock:'not_supplied',quote_prices_modified:true,trade_delay_minutes:15,
      provider_rows:enrichment.provider_rows,matched_contracts:enrichment.matched,requested_contracts:contracts.length,matched_snapshot_rows:enrichment.matched_snapshot_rows,
      invalid_rows:enrichment.invalid_rows,primary_status:enrichment.primary_status,primary_error:enrichment.primary_error,primary_rejected_rows:prior.rejected_rows||0,
      primary_invalid_clock_rows:prior.invalid_clock_rows||0,source_receipt_index:enrichment.source_receipt_index,
      ...(prior.denial_suppression?{denial_suppression:prior.denial_suppression}:{})};
    if(enrichment.matched)base.freshness.greeks_status='partial';
  } catch(error) {
    const allowed=['market_data_credentials_unavailable','alpaca_authentication_failed','alpaca_indicative_options_unavailable','provider_rate_limited','provider_unavailable','provider_redirect_rejected','provider_response_bound_exceeded','provider_body_invalid','provider_schema_invalid','provider_identity_mismatch','provider_request_bound_exceeded','unsupported_provider_pagination','source_request_timeout','acquisition_clock_invalid','cancelled','rate_limited','provider_request_budget_exceeded'];
    const code=error?.name==='TimeoutError'?'source_request_timeout':allowed.includes(error?.message)?error.message:'provider_unavailable';
    const lastIndex=base.source_receipts.length-1,lastReceipt=lastIndex>=0?base.source_receipts[lastIndex]:null;
    base.greeks_enrichment={status:'alpaca_indicative_unavailable',source:'Alpaca options snapshots · indicative',feed:'indicative',greek_clock:'not_supplied',error:code,
      primary_status:prior.status||'not_attempted',primary_error:prior.error||null,primary_rejected_rows:prior.rejected_rows||0,primary_invalid_clock_rows:prior.invalid_clock_rows||0,
      requested_contracts:contracts.length,matched_contracts:0,source_receipt_index:lastReceipt?.operation==='alpaca_options_indicative_snapshots'?lastIndex:null,
      ...(prior.denial_suppression?{denial_suppression:prior.denial_suppression}:{})};
  }
}
async function optionsResearchRun(request,args,env,kind) {
  const started=Date.now(),base=optionsResearchBase(kind,started);
  try {
    const parsed=optionsResearchArgs(args,kind,started);base.symbol=parsed.symbol;base.expiration=parsed.expiration??null;
    if(request.signal.aborted)throw Error('cancelled');
    let credentialSnapshot;
    try{credentialSnapshot=await brokerCredentialSnapshot(env,'tradier');}catch(error){throw Error(['broker_storage_unavailable','broker_credentials_unreadable'].includes(error?.message)?error.message:'broker_storage_unavailable');}
    const credentials=credentialSnapshot?.credentials??null,connectionRevision=credentialSnapshot?.connection_revision??null;
    base.source_access.configured=!!credentials;
    if(!credentials)throw Error('tradier_not_connected');
    if(!optionsResearchRateAllowed(request,started))throw Error('rate_limited');
    let payload=await optionsResearchFetch(request,credentials,kind,parsed,base);
    if(kind==='chain')payload=await optionsResearchEnrichChainGreeks(request,parsed,credentials,payload,base,null,env,connectionRevision);
    if(request.signal.aborted)throw Error('cancelled');
    const now=Date.now();if(now<started)throw Error('acquisition_clock_invalid');
    if(kind==='chain'){
      optionsResearchChain(payload,parsed,now,base);
      if(base.greeks_enrichment)await optionsResearchAlpacaGreeksFallback(request,parsed,env,base);
    }else optionsResearchExpirations(payload,parsed,now,base);
    const evaluated=Date.now(),maxDuration=SHIPYARD_OPTIONS_RESEARCH_POLICY.request_timeout_ms*(kind==='chain'&&base.greeks_enrichment?3:1);
    if(evaluated<started)throw Error('acquisition_clock_invalid');
    if(evaluated-started>=maxDuration)throw Error('source_request_timeout');
    base.evaluated_at=new Date(evaluated).toISOString();
    if(new TextEncoder().encode(JSON.stringify(base)).byteLength>SHIPYARD_OPTIONS_RESEARCH_POLICY.max_output_bytes)throw Error('output_bound_exceeded');
    return json(base);
  } catch(error) {
    const codes=['invalid_page_cursor_required','invalid_after_symbol','pagination_cursor_unavailable','invalid_arguments','invalid_expiration','invalid_pagination_arguments','cancelled','broker_storage_unavailable','broker_credentials_unreadable','tradier_not_connected','rate_limited','provider_rate_limited','tradier_authentication_failed','tradier_requested_data_not_entitled','provider_unavailable','provider_redirect_rejected','provider_response_bound_exceeded','provider_body_invalid','provider_schema_invalid','provider_identity_mismatch','provider_expirations_invalid','provider_row_bound_exceeded','unsupported_provider_pagination','duplicate_contract_identity','source_request_timeout','acquisition_clock_invalid','output_bound_exceeded'];
    const code=request.signal.aborted?'cancelled':error?.name==='TimeoutError'?'source_request_timeout':codes.includes(error?.message)?error.message:'source_acquisition_failed';
    base.error=code;base.status=code.startsWith('invalid_')?'invalid':code==='pagination_cursor_unavailable'?'partial':'unavailable';base.contracts=[];base.expirations=[];
    // Never expose exception/provider bodies, URLs supplied by the provider, or credentials.
    return json(base,code==='pagination_cursor_unavailable'?409:code.startsWith('invalid_')?400:code==='cancelled'?408:code.includes('rate_limited')?429:503);
  }
}
async function shipyardOptionsResearchExpirations(request,args,env) {return optionsResearchRun(request,args,env,'expirations');}
async function shipyardOptionsResearchChain(request,args,env) {return optionsResearchRun(request,args,env,'chain');}
function optionsResearchQuery(request,kind) {
  const args=Object.create(null),params=new URL(request.url).searchParams;
  for(const [key,value] of params) {
    if(Object.hasOwn(args,key))throw Error('invalid_arguments');
    if(['limit','offset'].includes(key)) {if(!/^(0|[1-9]\d{0,3})$/.test(value))throw Error('invalid_arguments');args[key]=Number(value);}
    else args[key]=value;
  }
  return optionsResearchArgs(args,kind,Date.now());
}
async function optionsResearchHandle(request,env,kind) {
  if(request.method!=='GET')return json({...optionsResearchBase(kind,Date.now()),status:'invalid',error:'method_not_allowed'},405);
  let args;try{args=optionsResearchQuery(request,kind);}catch{return json({...optionsResearchBase(kind,Date.now()),status:'invalid',error:'invalid_arguments'},400);}
  return optionsResearchRun(request,args,env,kind);
}
async function handleOptionsResearchExpirations(request,env) {return optionsResearchHandle(request,env,'expirations');}
async function handleOptionsResearchChain(request,env) {return optionsResearchHandle(request,env,'chain');}
async function handleOptionsResearchSnapshot(request,env) {
  const base = { schema:'SHIPYARD_OPTIONS_MARKET_SNAPSHOT_V1', provider:'Tradier + Alpaca', source:'Tradier standard options chain and Alpaca stock quote', status:'unavailable', symbol:null, expiration:null, requested_at:new Date().toISOString(), retrieved_at:null, underlying:null, contracts:[], gamma_profile:[], gex:null,
    coverage:{provider_rows:0,accepted_rows:0,rejected_rows:0,returned_contracts:0,eligible_gex_contracts:0,complete_provider_response:false,all_roots:false,whole_market:false},
    method:{gamma:'Tradier/ORATS reported option gamma',open_interest:'Tradier reported open interest; vintage not supplied by provider',position_sign:'positive calls / negative puts as a declared simplifying convention; actual dealer positions are unknown',unit:'dollars per 1% underlying move',formula:'signed gamma × open interest × contract size × spot² × 0.01'},
    restrictions:{source_only:true,execution_pricing:false,decision_eligible:false,marketwide_flow:false,accounts:false,orders:false}};
  if(request.method!=='GET')return json({...base,status:'invalid',error:'method_not_allowed'},405);
  const url=new URL(request.url),keys=[...url.searchParams.keys()],symbol=url.searchParams.get('symbol')?.trim().toUpperCase(),expiration=url.searchParams.get('expiration');
  if(keys.length!==2||new Set(keys).size!==2||keys.some(key=>!['symbol','expiration'].includes(key))||!symbol||!expiration) return json({...base,status:'invalid',error:'invalid_arguments'},400);
  let parsed;try{parsed=optionsResearchArgs({symbol,expiration,limit:100,offset:0},'chain',Date.now());}catch{return json({...base,status:'invalid',error:'invalid_arguments'},400);}
  base.symbol=parsed.symbol;base.expiration=parsed.expiration;
  const started=Date.now();
  try{
    if(request.signal.aborted)throw Error('cancelled');
    let credentialSnapshot;try{credentialSnapshot=await brokerCredentialSnapshot(env,'tradier');}catch(error){throw Error(['broker_storage_unavailable','broker_credentials_unreadable'].includes(error?.message)?error.message:'broker_storage_unavailable');}
    const credentials=credentialSnapshot?.credentials??null,connectionRevision=credentialSnapshot?.connection_revision??null;
    if(!credentials)throw Error('tradier_not_connected');
    if(!optionsResearchRateAllowed(request,started))throw Error('rate_limited');
    const chainBase=optionsResearchBase('chain',started);chainBase.symbol=parsed.symbol;chainBase.expiration=parsed.expiration;
    // One chain read, optional Tradier Greek enrichment, one SIP quote, and at most
    // one predeclared IEX entitlement fallback: no unbounded provider retries.
    let providerReads=0;const consumeSnapshotRead=()=>{if(providerReads>=SHIPYARD_OPTIONS_MARKET_SNAPSHOT_MAX_PROVIDER_REQUESTS)throw Error('provider_request_budget_exceeded');providerReads++;};
    const payload=await optionsResearchFetch(request,credentials,'chain',parsed,chainBase,consumeSnapshotRead);
    const enriched=await optionsResearchEnrichChainGreeks(request,parsed,credentials,payload,chainBase,consumeSnapshotRead,env,connectionRevision);
    const acquired=Date.now();if(request.signal.aborted)throw Error('cancelled');
    // One provider response contains the entire standard single-expiry chain. It is parsed once;
    // the response returned to the browser is reduced to a nearby contract set and strike profile.
    optionsResearchChain(enriched,{...parsed,offset:0,limit:2000},acquired,chainBase);
    if(chainBase.error)throw Error(chainBase.error);
    if(chainBase.pagination?.has_more)throw Error('provider_chain_limit_reached');

    const keyId=env?.ALPACA_API_KEY_ID,secret=env?.ALPACA_API_SECRET_KEY;
    if(typeof keyId!=='string'||!keyId||typeof secret!=='string'||!secret)throw Error('market_data_credentials_unavailable');
    if(!alpacaRateAllowed(request,Date.now()))throw Error('rate_limited');
    consumeSnapshotRead();
    let quoteResult=await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/quotes/latest?feed=sip`,keyId,secret);
    let underlyingFeed='sip';
    if(!quoteResult.ok&&quoteResult.status===403){consumeSnapshotRead();quoteResult=await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(symbol)}/quotes/latest?feed=iex`,keyId,secret);underlyingFeed='iex';}
    if(!quoteResult.ok)throw Error(quoteResult.status===401?'market_data_authentication_failed':quoteResult.status===403?'underlying_iex_entitlement_unavailable':quoteResult.status===429?'provider_rate_limited':'underlying_quote_unavailable');
    const rawQuote=quoteResult.value?.quote,parsedQuote=alpacaQuote(rawQuote);
    if(quoteResult.value?.symbol!==symbol||!parsedQuote)throw Error('underlying_quote_invalid');
    const evaluated=Date.now(),quoteAge=(evaluated-Date.parse(parsedQuote.at))/1000;
    // Preserve the existing five-second tolerance for provider/receiver clock skew.
    if(!Number.isFinite(quoteAge)||quoteAge < -5)throw Error('underlying_quote_clock_invalid');
    const spot=(parsedQuote.bid+parsedQuote.ask)/2;
    base.underlying={symbol,spot,bid:parsedQuote.bid,ask:parsedQuote.ask,source:`Alpaca ${underlyingFeed.toUpperCase()}`,provider:'Alpaca Market Data',feed:underlyingFeed,source_identity:{provider:'Alpaca Market Data',feed:underlyingFeed,endpoint:`/v2/stocks/${encodeURIComponent(symbol)}/quotes/latest`,response_symbol:quoteResult.value?.symbol},as_of:parsedQuote.at,age_seconds:quoteAge,age_status:quoteAge<=90?'current':quoteAge<=900?'recent':'stale'};

    const all=chainBase.contracts,strikes=new Map();let eligible=0,excludedMissing=0,excludedGreeks=0;
    for(const contract of all){
      const oi=contract.open_interest?.value,gamma=contract.greeks?.values?.gamma;
      if(!Number.isSafeInteger(oi)||oi<0){excludedMissing++;continue;}
      if(!Number.isFinite(gamma)||gamma<0||contract.greeks?.field_status?.gamma!=='current'){excludedGreeks++;continue;}
      const magnitude=gamma*oi*100*spot*spot*.01;
      if(!Number.isFinite(magnitude)){excludedGreeks++;continue;}
      const row=strikes.get(contract.strike)||{strike:contract.strike,call_gex:0,put_gex:0,contracts:0};
      if(contract.option_type==='call')row.call_gex+=magnitude;else row.put_gex-=magnitude;
      row.contracts++;strikes.set(contract.strike,row);eligible++;
    }
    const profileAll=[...strikes.values()].map(row=>({...row,net_gex:row.call_gex+row.put_gex})).sort((a,b)=>a.strike-b.strike);
    const profile=[...profileAll].sort((a,b)=>Math.abs(a.strike-spot)-Math.abs(b.strike-spot)||a.strike-b.strike).slice(0,250).sort((a,b)=>a.strike-b.strike);
    const callGex=profileAll.reduce((sum,row)=>sum+row.call_gex,0),putGex=profileAll.reduce((sum,row)=>sum+row.put_gex,0),netGex=callGex+putGex;
    const nearby=all.toSorted((a,b)=>Math.abs(a.strike-spot)-Math.abs(b.strike-spot)||a.strike-b.strike||a.option_type.localeCompare(b.option_type)).slice(0,100).sort((a,b)=>a.strike-b.strike||a.option_type.localeCompare(b.option_type));
    base.contracts=nearby;base.gamma_profile=profile;base.gex=eligible?{call_gex:callGex,put_gex:putGex,net_gex:netGex,unit:'USD per 1% move',eligible_contracts:eligible,excluded_missing_open_interest:excludedMissing,excluded_stale_or_missing_greeks:excludedGreeks,zero_gamma_interpretation:'The sign convention is a model assumption. The result does not establish dealer positions or predict direction.'}:null;
    base.coverage={provider_rows:chainBase.coverage.provider_rows,accepted_rows:chainBase.coverage.accepted_rows,rejected_rows:chainBase.coverage.rejected_rows,returned_contracts:nearby.length,eligible_gex_contracts:eligible,gamma_profile_strikes_total:profileAll.length,gamma_profile_strikes_displayed:profile.length,complete_provider_response:chainBase.coverage.complete_provider_response,all_roots:false,whole_market:false};
    base.chain_freshness=chainBase.freshness;base.chain_received_at=chainBase.retrieved_at;base.chain_receipt=chainBase.source_receipts[0]||null;base.chain_receipts=chainBase.source_receipts;base.greeks_enrichment=chainBase.greeks_enrichment||null;
    const sourceStale=chainBase.status==='stale'||base.underlying.age_status==='stale';
    base.status=chainBase.status==='current'&&base.underlying.age_status==='current'&&eligible===all.length?'connected':sourceStale?'stale':'partial';
    base.retrieved_at=new Date(evaluated).toISOString();base.option_scope='One standard root and one expiration; up to 2,000 provider rows, nearest 100 contracts returned.';
    base.notes=['Open interest is reported without a provider vintage.','Greeks come from Tradier/ORATS and are hourly rather than tick-live.','The underlying quote and option chain are separate captures.','This profile is not full-market options flow or observed dealer positioning.'];
    if(new TextEncoder().encode(JSON.stringify(base)).byteLength>SHIPYARD_OPTIONS_RESEARCH_POLICY.max_output_bytes)throw Error('output_bound_exceeded');
    return json(base);
  }catch(error){
    const codes=['cancelled','broker_storage_unavailable','broker_credentials_unreadable','tradier_not_connected','rate_limited','provider_rate_limited','tradier_authentication_failed','tradier_requested_data_not_entitled','provider_unavailable','provider_redirect_rejected','provider_response_bound_exceeded','provider_body_invalid','provider_schema_invalid','provider_identity_mismatch','provider_row_bound_exceeded','unsupported_provider_pagination','duplicate_contract_identity','provider_request_budget_exceeded','source_request_timeout','acquisition_clock_invalid','output_bound_exceeded','provider_chain_limit_reached','market_data_credentials_unavailable','market_data_authentication_failed','underlying_iex_entitlement_unavailable','underlying_quote_unavailable','underlying_quote_invalid','underlying_quote_clock_invalid'];
    const code=request.signal.aborted?'cancelled':error?.name==='TimeoutError'?'source_request_timeout':codes.includes(error?.message)?error.message:'source_acquisition_failed';
    base.status='unavailable';base.error=code;base.contracts=[];base.gamma_profile=[];base.gex=null;
    return json(base,code==='cancelled'?408:code.includes('rate_limited')?429:code.startsWith('invalid_')?400:503);
  }
}
async function handleTradierMarketStreamSession(request,env) {
  const base={schema:'SHIPYARD_TRADIER_STREAM_SESSION_V1',provider:'tradier',status:'unavailable',websocket_url:null,session_id:null,expires_at:null,
    symbols:[],created_at:new Date().toISOString(),restrictions:{market_data_only:true,account_stream:false,account_data_returned:false,orders:false}};
  if(request.method!=='POST')return json({...base,status:'invalid',error:'method_not_allowed'},405);
  try {
    if(request.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='application/json')throw Error('invalid_stream_request');
    const body=await readBoundedBody(request,8192);let args;try{args=JSON.parse(body);}catch{throw Error('invalid_stream_request');}
    if(!optionsResearchObject(args)||Object.keys(args).length!==1||!Array.isArray(args.symbols)||args.symbols.length<1||args.symbols.length>50)throw Error('invalid_stream_request');
    const identities=args.symbols.map(symbol=>typeof symbol==='string'?symbol.match(/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/):null);
    if(identities.some(x=>!x)||new Set(args.symbols).size!==args.symbols.length)throw Error('invalid_stream_symbols');
    const cursorDates=identities.map(match=>`20${match[2].slice(0,2)}-${match[2].slice(2,4)}-${match[2].slice(4,6)}`);
    const today=optionsResearchToday(Date.now());
    if(cursorDates.some(date=>!optionsResearchDate(date)||date<today)||new Set(identities.map(match=>match[1])).size!==1||new Set(cursorDates).size!==1)throw Error('invalid_stream_symbols');
    base.symbols=args.symbols;
    let credentials;try{credentials=await brokerCredentials(env,'tradier');}catch(error){throw Error(['broker_storage_unavailable','broker_credentials_unreadable'].includes(error?.message)?error.message:'broker_storage_unavailable');}
    if(!credentials)throw Error('tradier_not_connected');
    const now=Date.now();if(!optionsResearchRateAllowed(request,now))throw Error('rate_limited');
    const signal=AbortSignal.any([request.signal,AbortSignal.timeout(SHIPYARD_OPTIONS_RESEARCH_POLICY.request_timeout_ms)]);
    let response;try{response=await fetch('https://api.tradier.com/v1/markets/events/session',{method:'POST',headers:{authorization:`Bearer ${credentials.token}`,accept:'application/json','content-type':'application/x-www-form-urlencoded'},body:'',redirect:'manual',signal});}
    catch(error){if(signal.aborted)throw error;throw Error('provider_unavailable');}
    if(response.status>=300&&response.status<400)throw Error('provider_redirect_rejected');
    let text;try{text=await readBoundedBody(response,64*1024);}catch(error){if(signal.aborted)throw error;throw Error(error?.message==='response too large'?'provider_response_bound_exceeded':'provider_body_invalid');}
    if(request.signal.aborted)throw Error('cancelled');
    if(response.status===429)throw Error('provider_rate_limited');
    if(!response.ok)throw Error(response.status===401?'tradier_authentication_failed':response.status===403?'tradier_stream_not_entitled':'provider_unavailable');
    let payload;try{payload=JSON.parse(text);}catch{throw Error('provider_schema_invalid');}
    if(!optionsResearchObject(payload)||Object.hasOwn(payload,'error')||Object.hasOwn(payload,'errors'))throw Error('provider_schema_invalid');
    const session=payload.stream;
    if(!optionsResearchObject(session))throw Error('provider_stream_missing');
    if(typeof session.sessionid!=='string'||!/^[A-Za-z0-9_-]{16,256}$/.test(session.sessionid))throw Error('provider_session_id_invalid');
    if(typeof session.url!=='string'||session.url.length<1||session.url.length>2048)throw Error('provider_stream_url_missing');
    let streamUrl;try{streamUrl=new URL(session.url);}catch{throw Error('provider_stream_url_malformed');}
    // Treat provider schemes only as endpoint metadata. The browser never uses
    // the supplied URL; after validating the exact host/path, it connects to
    // Tradier's documented TLS WebSocket endpoint below.
    if(!['wss:','ws:','https:','http:'].includes(streamUrl.protocol))throw Error('provider_stream_protocol_unsupported');
    // Tradier documents ws.tradier.com for WebSockets and stream.tradier.com
    // for HTTP streaming. Both use market sessions; normalize either known
    // provider transport to the fixed secure WebSocket endpoint below.
    if(!['ws.tradier.com','stream.tradier.com'].includes(streamUrl.hostname))throw Error('provider_stream_host_unsupported');
    if(streamUrl.port)throw Error('provider_stream_port_unsupported');
    if(streamUrl.username||streamUrl.password||streamUrl.hash)throw Error('provider_stream_url_components_unsupported');
    if(streamUrl.pathname!=='/v1/markets/events')throw Error('provider_stream_path_invalid');
    if(streamUrl.search)throw Error('provider_stream_query_invalid');
    // Normalize the provider's URL scheme variants to the documented secure
    // endpoint. This upgrades any HTTP hint; the browser never follows it.
    const websocketUrl='wss://ws.tradier.com/v1/markets/events';
    const expires=session.expires===''||session.expires==null?null:typeof session.expires==='string'&&Number.isFinite(Date.parse(session.expires))?new Date(session.expires).toISOString():null;
    if(session.expires!==''&&session.expires!=null&&!expires)throw Error('provider_stream_expiry_invalid');
    base.status='session_ready';base.websocket_url=websocketUrl;base.session_id=session.sessionid;base.expires_at=expires;base.created_at=new Date().toISOString();
    base.note='Short-lived market-data session. The API token remains server-side. Open the WebSocket immediately; this route never creates account streams or sends orders.';
    return json(base);
  }catch(error){
    const codes=['invalid_stream_request','invalid_stream_symbols','broker_storage_unavailable','broker_credentials_unreadable','tradier_not_connected','rate_limited','provider_rate_limited','tradier_authentication_failed','tradier_stream_not_entitled','provider_unavailable','provider_redirect_rejected','provider_response_bound_exceeded','provider_body_invalid','provider_schema_invalid','provider_stream_missing','provider_stream_url_missing','provider_stream_url_malformed','provider_stream_protocol_unsupported','provider_stream_host_unsupported','provider_stream_port_unsupported','provider_stream_url_components_unsupported','provider_stream_path_invalid','provider_stream_query_invalid','provider_session_id_invalid','provider_stream_expiry_invalid'];
    const code=request.signal.aborted?'cancelled':error?.name==='TimeoutError'?'source_request_timeout':codes.includes(error?.message)?error.message:'source_acquisition_failed';
    base.status=code.startsWith('invalid_')?'invalid':'unavailable';base.error=code;base.session_id=null;base.websocket_url=null;
    return json(base,code.startsWith('invalid_')?400:code==='cancelled'?408:code.includes('rate_limited')?429:503);
  }
}
