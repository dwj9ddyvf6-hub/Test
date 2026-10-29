// Shared public read model. No desk imports, financial mutations or owner inference.
const OPS_KEY = 'ausar-public-operations-v1';
const CACHE_MS = 10000;
const PROJECTION_MAX_AGE_MS = 300000; // Materialized observer contract, never a trading gate.
const MAX_FUTURE_SKEW_MS = 60000;
const readCaches = new Map(); // two bounded entries per isolate
function invalidateRead(key) { readCaches.delete(key); }
async function cachedRead(key, loader) {
  const hit = readCaches.get(key);
  if (hit && Date.now() < hit.until) return hit.value;
  // Keep only completed data across invocations. A canceled request's I/O
  // promise belongs to that request and must never hold later readers hostage.
  const value = await loader();
  readCaches.set(key, {value, until: Date.now()+CACHE_MS});
  return value;
}
// RFC 9110 13.1.2: If-None-Match uses weak comparison. Hosting compression can
// expose W/"tag" even when this worker emitted "tag". Commas inside opaque
// tags are legal, so parse the list rather than splitting it on every comma.
function ifNoneMatchMatches(value, currentTag) {
  if(typeof value!=='string'||value.length>8192)return false;
  const field=value.replace(/^[ \t]+|[ \t]+$/g,'');
  if(field==='*')return true;
  let cursor=0,members=0,tags=0,matched=false;
  while(cursor<field.length){
    if(++members>64)return false;
    while(field[cursor]===' '||field[cursor]==='\t')cursor++;
    // A reasonable number of empty list elements is permitted by #entity-tag.
    if(field[cursor]===','){cursor++;continue;}
    if(cursor===field.length)break;
    if(field.slice(cursor,cursor+2)==='W/')cursor+=2;
    if(field[cursor]!=='"')return false;
    const end=field.indexOf('"',cursor+1);
    if(end<0||!/^[\x21\x23-\x7e\x80-\xff]*$/.test(field.slice(cursor+1,end)))return false;
    tags++;matched ||= field.slice(cursor,end+1)===currentTag.replace(/^W\//,'');
    cursor=end+1;
    while(field[cursor]===' '||field[cursor]==='\t')cursor++;
    if(cursor<field.length&&field[cursor++]!==',')return false;
  }
  // Validate the entire field before accepting any member. A malformed suffix
  // must not turn an otherwise nonmatching request into a false 304.
  return tags>0&&matched;
}
function conditionalJson(request, body, etag) {
  const headers = {'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=10, must-revalidate','etag':'"'+etag+'"','x-content-type-options':'nosniff'};
  const unchanged=['GET','HEAD'].includes(request.method)&&ifNoneMatchMatches(request.headers.get('if-none-match'),headers.etag);
  return new Response(unchanged || request.method === 'HEAD' ? null : JSON.stringify(body), {status:unchanged ? 304 : 200,headers});
}
function assetJson(path) {return JSON.parse(new TextDecoder().decode(decodeAsset(STATIC_ASSETS[path])));}
function historicalOperationsBoundary(value) {
  return {...value,record_role:'historical_evidence',current_desk:false,current_snapshot_url:'/api/ausar/snapshot',
    scope:'Preserved earlier Ausar operations and recovery receipts. Use the current snapshot for Codex Desk status.'};
}
function publicEvidence(state) {
  const baseline=assetJson('/data/evidence.json');
  return {...baseline,restore_test:{status:state.recovery.status,
    last_receipt_at:state.recovery.restore_test_at,backup_at:state.recovery.backup_at,
    observation_status:state.status,
    scope:'Dated independently restored snapshot evidence; not whole-desk readiness or cross-database atomicity.'},
    generations:state.generations};
}
function emptyOperations() {
  return {schema:'AUSAR_OPERATIONS_V1',sequence:0,generation:null,observed_at:null,received_at:null,event_at:null,
    rows:assetJson('/data/inventory.json').rows,health:{last_useful_work_at:null,reconciled_at:null,inputs_at:null},
    events:[],experiments:[],receipts:[],generations:[],recovery:{backup_at:null,restore_test_at:null,status:'unconnected'}};
}
async function operationsState(env) {
  if (!env.DB) return emptyOperations();
  const row=await env.DB.prepare('SELECT body_json FROM observatory_read_models WHERE view_key = ?').bind(OPS_KEY).first();
  return row ? JSON.parse(row.body_json) : emptyOperations();
}
async function leanTerminal(env) {
  if(!env.DB)return null;
  const row=await env.DB.prepare('SELECT payload_json, received_at_utc FROM ausar_terminal_snapshots WHERE id = 1').first();
  if(!row)return null;
  const value=JSON.parse(row.payload_json);
  return value.desk?.epoch==='AUSAR_LEAN_FORWARD'?{...value,published_at:row.received_at_utc}:null;
}
function publicState(state) {
  const now=Date.now(),ageOf=v=>v==null?null:now-Date.parse(v);
  const statusOf=age=>age==null?'unknown':age<0?'clock_skew':age>PROJECTION_MAX_AGE_MS?'stale':'observed';
  const age=ageOf(state.observed_at),workAge=ageOf(state.health.last_useful_work_at),inputAge=ageOf(state.health.inputs_at);
  const rows=state.rows.map(r=>{const eventAge=ageOf(r.event_at),eventStatus=statusOf(eventAge);
    return {...r,event_age_ms:eventAge,event_status:eventStatus,
      last_financial_evaluation_at:r.last_financial_evaluation_at??(r.kind==='strategy'?(r.event_at??null):null),
      cadence_status:r.next_due_at==null?'unverified_cadence':Date.parse(r.next_due_at)>now?'healthy_periodic_wait':'next_observation_due',
      current:['observed','waiting'].includes(r.current)&&statusOf(age)!=='observed'?(statusOf(age)==='stale'?'stale':'unknown'):r.current};});
  return {...state,rows,status:!state.sequence?'unconnected':statusOf(age),age_ms:age,source_age_ms:age,
    receipt_age_ms:ageOf(state.received_at),source_clock_skew_ms:age==null?null:Math.max(0,-age),
    last_useful_work_age_ms:workAge,last_useful_work_status:statusOf(workAge),input_age_ms:inputAge,input_status:statusOf(inputAge),
    freshness_policy:{projection_max_age_ms:PROJECTION_MAX_AGE_MS,max_future_skew_ms:MAX_FUTURE_SKEW_MS,scope:'observation_only'},
    counts:{definitions:rows.length,monitors:rows.filter(r=>r.kind==='monitor').length,evaluated:rows.filter(r=>r.kind==='strategy'&&r.evaluation==='evaluated').length,waiting_window:rows.filter(r=>r.kind==='strategy'&&r.evaluation==='waiting_window').length,blocked:rows.filter(r=>r.kind==='strategy'&&r.evaluation==='blocked').length,unevaluated:rows.filter(r=>r.kind==='strategy'&&!['evaluated','waiting_window','blocked'].includes(r.evaluation)).length},
    control:{executing:false,owner_identity:'not_configured',scope:'Public terminal has no execution owner or order authority; DigitalOcean owns the desk.',requests:'local_draft_only',acknowledgment:'not_connected'},
    limits:{rows:169,events:100,generations:16,body_bytes:262144,cache_seconds:10},
    authority:'Existing desk remains the sole ledger and order writer.'};
}
const allowedStates=['unconnected','unknown','blocked','observed','stale','waiting'];
const enumValue=(v,items)=>{if(!items.includes(v))throw Error('invalid enum');return v;};
function requireTime(v) {const t=timestamp(v);if(!t||Date.parse(t)>Date.now()+MAX_FUTURE_SKEW_MS)throw Error('invalid time');return v;}
function optionalTime(v) {return v==null?null:requireTime(v);}
function optionalDue(v) {if(v==null)return null;const t=timestamp(v);if(!t||Date.parse(t)>Date.now()+32*86400000)throw Error('invalid due time');return v;}
function safeId(v,p=/^(strategy-\d{3}|monitor-\d{3})$/) {if(typeof v!=='string'||!p.test(v))throw Error('invalid id');return v;}
function sanitizeBatch(input) {
  if(input?.schema!=='AUSAR_EXPORT_V1'||input.source!=='ausar-paper'||input.paper_only!==true)throw Error('invalid identity');
  if(!Number.isSafeInteger(input.sequence)||input.sequence<1||!Number.isSafeInteger(input.base_sequence)||input.base_sequence<0||input.sequence!==input.base_sequence+1)throw Error('invalid sequence');
  const ids=new Set(assetJson('/data/inventory.json').rows.map(r=>r.id));
  if(!Array.isArray(input.rows)||input.rows.length>169)throw Error('invalid rows');
  const seen=new Set();const rows=input.rows.map(r=>{
    const id=safeId(r.id);if(!ids.has(id)||seen.has(id))throw Error('invalid row');seen.add(id);
    return {id,current:enumValue(r.current,allowedStates),event_at:optionalTime(r.event_at),
      installation:enumValue(r.installation,['historical_source_verified','unverified','installed']),
      evaluation:enumValue(r.evaluation,['qualified_inputs_required','not_evaluated','blocked','evaluated','waiting_window']),
      last_attempt_at:optionalTime(r.last_attempt_at),last_financial_evaluation_at:optionalTime(r.last_financial_evaluation_at),last_successful_evaluation_at:optionalTime(r.last_successful_evaluation_at),next_due_at:optionalDue(r.next_due_at),
      typed_status:r.typed_status==null?null:{input_qualification:enumValue(r.typed_status.input_qualification,['denied','unknown','qualified','ineligible']),signal_state:enumValue(r.typed_status.signal_state,['unknown','no_signal','signal']),window_state:enumValue(r.typed_status.window_state,['unknown','outside_window','open']),risk_permission:enumValue(r.typed_status.risk_permission,['unknown','denied','permitted']),execution_mode:enumValue(r.typed_status.execution_mode,['unknown','local_paper','broker_paper','local_simulation','monitor']),lifecycle_status:enumValue(r.typed_status.lifecycle_status,['unverified','unknown','open','pending','closed'])},
      promotion:enumValue(r.promotion,['not_authorized','review_requested','acknowledged'])};
  });
  const mode=enumValue(input.kind,['snapshot','delta']);if(mode==='snapshot'&&rows.length!==169)throw Error('full census required');
  if(!Array.isArray(input.events)||input.events.length>100)throw Error('invalid events');
  const events=input.events.map(e=>({id:safeId(e.id,/^[a-f0-9]{64}$/),type:enumValue(e.type,['input_stale','input_recovered','reconciliation_completed','work_completed','export_disconnected','export_recovered']),at:requireTime(e.at),subject:e.subject==null?null:safeId(e.subject)}));
  if(events.some(e=>e.subject&&!ids.has(e.subject)))throw Error('unknown subject');
  if(input.experiments!=null&&(!Array.isArray(input.experiments)||input.experiments.length>50))throw Error('experiment bounds');
  const experiments=(input.experiments||[]).map(e=>({id:safeId(e.id,/^[a-f0-9]{64}$/),
    installation:enumValue(e.installation,['unverified','installed']),evaluation:enumValue(e.evaluation,['not_evaluated','blocked','evaluated']),promotion:enumValue(e.promotion,['not_authorized','review_requested','acknowledged']),
    input_sha256:safeId(e.input_sha256,/^[a-f0-9]{64}$/),code_sha256:safeId(e.code_sha256,/^[a-f0-9]{64}$/),observed_at:requireTime(e.observed_at)}));
  const h=record(input.health),r=record(input.recovery);
  return {schema:input.schema,source:'ausar-paper',paper_only:true,batch_id:safeId(input.batch_id,/^[a-f0-9]{64}$/),sequence:input.sequence,base_sequence:input.base_sequence,kind:mode,
    observed_at:requireTime(input.observed_at),event_at:requireTime(input.event_at),rows,events,experiments,
    health:{last_useful_work_at:optionalTime(h.last_useful_work_at),reconciled_at:optionalTime(h.reconciled_at),inputs_at:optionalTime(h.inputs_at)},
    recovery:{backup_at:optionalTime(r.backup_at),restore_test_at:optionalTime(r.restore_test_at),status:enumValue(r.status||'unconnected',['unconnected','unverified','backup_observed','restore_test_passed','restore_test_failed'])}};
}
function legacyTimeBatch(batch) {
  const keys=new Set(['at','observed_at','event_at','last_useful_work_at','reconciled_at','inputs_at','backup_at','restore_test_at']);
  return JSON.parse(JSON.stringify(batch,(key,value)=>keys.has(key)&&value!=null?timestamp(value):value));
}
function sameLegacyEvent(old,next) {
  return old.id===next.id&&old.type===next.type&&old.subject===next.subject&&old.at===timestamp(next.at);
}
function reduceBatch(state,batch,hash,legacyHash=null) {
  const prior=state.receipts.find(r=>r.batch_id===batch.batch_id);
  if(prior){if(prior.hash!==hash&&prior.hash!==legacyHash)throw Error('batch_id_conflict');return null;}
  if(batch.base_sequence!==state.sequence||batch.sequence!==state.sequence+1)throw Error('sequence_conflict');
  if(state.observed_at&&Date.parse(batch.observed_at)<Date.parse(state.observed_at))throw Error('observation_regressed');
  if(Date.now()-Date.parse(batch.observed_at)>PROJECTION_MAX_AGE_MS)throw Error('stale_export');
  if(batch.kind==='delta'&&state.sequence===0)throw Error('snapshot_required');
  const updates=new Map(batch.rows.map(r=>[r.id,r]));
  const eventMap=new Map(state.events.map(e=>[e.id,e]));
  for(const e of batch.events){const old=eventMap.get(e.id);if(old){if(JSON.stringify(old)!==JSON.stringify(e)&&!sameLegacyEvent(old,e))throw Error('event_id_conflict');continue;}eventMap.set(e.id,e);}
  const now=new Date().toISOString();
  return {...state,sequence:batch.sequence,generation:hash,observed_at:batch.observed_at,event_at:batch.event_at,received_at:now,
    experiments:[...new Map([...state.experiments,...batch.experiments].map(e=>[e.id,e])).values()].slice(-50),
    rows:state.rows.map(r=>({...r,...updates.get(r.id)})),health:batch.health,recovery:batch.recovery,
    events:[...eventMap.values()].sort((a,b)=>Date.parse(a.at)-Date.parse(b.at)||a.id.localeCompare(b.id)).slice(-100),
    receipts:[...state.receipts,{batch_id:batch.batch_id,hash,sequence:batch.sequence}].slice(-16),
    generations:[...state.generations,{sequence:batch.sequence,sha256:hash,location:'/api/ausar/evidence/'+hash,observed_at:batch.observed_at,verified:true}].slice(-16)};
}
async function ingestOperations(request,env) {
  // Uses only the already-established public publisher boundary; no credential provisioning.
  if(typeof env.AUSAR_PUBLIC_PUBLISH_TOKEN!=='string'||env.AUSAR_PUBLIC_PUBLISH_TOKEN.length<40)return json({error:'publisher_not_configured'},503);
  if(!constantTimeEqual(request.headers.get('authorization')||'','Bearer '+env.AUSAR_PUBLIC_PUBLISH_TOKEN))return json({error:'unauthorized'},401);
  if(!env.DB||!env.BUCKET)return json({error:'storage_not_configured'},503);
  if(!(request.headers.get('content-type')||'').startsWith('application/json'))return json({error:'application_json_required'},415);
  let batch,raw;
  try {raw=await readBoundedBody(request);if(new TextEncoder().encode(raw).length>262144)throw Error();batch=sanitizeBatch(JSON.parse(raw));}catch{return json({error:'invalid_batch'},400);}
  try {
    const state=await operationsState(env),body=JSON.stringify(batch),hash=await digest(body);
    const legacyHash=state.receipts.some(r=>r.batch_id===batch.batch_id&&r.hash!==hash)?await digest(JSON.stringify(legacyTimeBatch(batch))):null;
    let next;try{next=reduceBatch(state,batch,hash,legacyHash);}catch(e){return json({error:e.message},409);}
    if(!next)return json({accepted:true,duplicate:true,sequence:batch.sequence});
    // Immutable artifact first; D1 CAS is the single publish marker. No partial generation is visible.
    const key='ausar-public/'+hash+'.json';
    await env.BUCKET.put(key,body,{httpMetadata:{contentType:'application/json'}});
    const object=await env.BUCKET.get(key);
    if(!object||await digest(await object.text())!==hash)return json({error:'artifact_verification_failed'},503);
    const result=await env.DB.prepare('INSERT INTO observatory_read_models (view_key,schema_version,generated_at,input_watermark_at,freshness_status,source_mode,etag,record_count,body_json,quality_json) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(view_key) DO UPDATE SET generated_at=excluded.generated_at,input_watermark_at=excluded.input_watermark_at,etag=excluded.etag,record_count=excluded.record_count,body_json=excluded.body_json WHERE observatory_read_models.etag = ?')
      .bind(OPS_KEY,'1',next.received_at,next.observed_at,'observed','paper_export',hash,169,JSON.stringify(next),'{}',state.generation||'').run();
    if(!result.meta?.changes)return json({error:'concurrent_generation_conflict'},409);
    invalidateRead('operations');
    // Retention does not affect the commit. Failed cleanup is retried by the next export sweep.
    try {const objects=await env.BUCKET.list({prefix:'ausar-public/',limit:100});const keep=new Set(next.generations.map(g=>'ausar-public/'+g.sha256+'.json'));
      for(const o of objects.objects||[])if(!keep.has(o.key)&&Date.now()-new Date(o.uploaded).getTime()>86400000)await env.BUCKET.delete(o.key);
    }catch{}
    return json({accepted:true,sequence:next.sequence,generation:hash,artifact_verified:true});
  }catch{return json({error:'export_store_unavailable'},503);}
}
async function operationsRoute(request,env) {
  const url=new URL(request.url),path=url.pathname;
  if(path.startsWith('/api/ausar/owner')||path==='/api/ausar/requests')return json({error:'owner_integration_not_configured',executing:false},403);
  if(path==='/api/ausar/ingest')return request.method==='POST'?ingestOperations(request,env):json({error:'method_not_allowed'},405);
  if(path==='/api/ausar/operations'){
    if(!['GET','HEAD'].includes(request.method))return json({error:'method_not_allowed'},405);
    try {const s=await cachedRead('operations',()=>operationsState(env));return conditionalJson(request,historicalOperationsBoundary(publicState(s)),(s.generation||'unconnected')+'-'+Math.floor(Date.now()/10000));}catch{return json({error:'read_model_unavailable'},503);}
  }
  if(path==='/api/ausar/evidence'){
    if(!['GET','HEAD'].includes(request.method))return json({error:'method_not_allowed'},405);
    try {const s=publicState(await cachedRead('operations',()=>operationsState(env)));return conditionalJson(request,historicalOperationsBoundary(publicEvidence(s)),(s.generation||'unconnected')+'-'+Math.floor(Date.now()/10000));}catch{return json({error:'read_model_unavailable'},503);}
  }
  if(path.startsWith('/api/ausar/evidence/')){
    if(!['GET','HEAD'].includes(request.method))return json({error:'method_not_allowed'},405);
    const hash=path.split('/').pop();if(!/^[a-f0-9]{64}$/.test(hash))return json({error:'not_found'},404);
    try {const s=await cachedRead('operations',()=>operationsState(env));if(!s.generations.some(g=>g.sha256===hash))return json({error:'not_found'},404);
      const o=await env.BUCKET?.get('ausar-public/'+hash+'.json');if(!o)return json({error:'artifact_unavailable'},503);const body=await o.text();if(await digest(body)!==hash)return json({error:'artifact_integrity_failure'},503);
      return conditionalJson(request,JSON.parse(body),hash);
    }catch{return json({error:'artifact_unavailable'},503);}
  }
  if(path==='/mcp'){
    if(request.method!=='POST')return json({error:'method_not_allowed'},405);
    let rpc;try{rpc=JSON.parse(await readBoundedBody(request));}catch{return json({jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}},400);}
    const names=['ausar_public_inventory','ausar_public_health','ausar_public_evidence','ausar_public_incidents','ausar_public_research'];
    let result;
    if(rpc.method==='server/discover')result={supportedVersions:['2026-07-28'],capabilities:{tools:{}}};
    else if(rpc.method==='initialize')result={protocolVersion:'2026-07-28',capabilities:{tools:{}},serverInfo:{name:'Ausar public observer',version:'1.0.0'}};
    else if(rpc.method==='notifications/initialized')return new Response(null,{status:202});
    else if(rpc.method==='tools/list')result={tools:names.map(name=>({name,description:'Read sanitized paper evidence; never execute or change the desk.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,destructiveHint:false,idempotentHint:true,openWorldHint:false}}))};
    else if(rpc.method==='tools/call'&&names.includes(rpc.params?.name)){
      const lean=await leanTerminal(env);
      if(lean){
        const fresh=Date.now()-Date.parse(lean.observed_at_utc)<=300000;
        const values={ausar_public_inventory:{epoch:lean.desk.epoch,books:lean.books,sleeves:lean.terminal?.sleeves||[],monitor_count:15},
          ausar_public_health:{status:fresh?'observed':'stale',observed_at:lean.observed_at_utc,published_at:lean.published_at,services:lean.services},
          ausar_public_evidence:{epoch:lean.desk.epoch,mode:'fresh forward local/model paper',broker_fills:false,historical_results_imported:false},
          ausar_public_incidents:{events:[],scope:'No incident feed configured for lean campaign; service status is separate'},
          ausar_public_research:{experiments:[],engine:lean.terminal?.engine||null,memory:lean.services?.learning || {observed:false},scope:'Read-only descriptive forward memory; no automatic promotion',executing:false}};
        return json({jsonrpc:'2.0',id:rpc.id??null,result:{content:[{type:'text',text:JSON.stringify(values[rpc.params.name])}]}});
      }
      try{const s=publicState(await cachedRead('operations',()=>operationsState(env)));const value={ausar_public_inventory:{rows:s.rows,status:s.status},ausar_public_health:{status:s.status,observed_at:s.observed_at,received_at:s.received_at,source_age_ms:s.source_age_ms,receipt_age_ms:s.receipt_age_ms,last_useful_work_age_ms:s.last_useful_work_age_ms,last_useful_work_status:s.last_useful_work_status,input_age_ms:s.input_age_ms,input_status:s.input_status,freshness_policy:s.freshness_policy,health:s.health,control:s.control},ausar_public_evidence:publicEvidence(s),ausar_public_incidents:{events:s.events,retention:100},ausar_public_research:{experiments:s.experiments,requests:'local_draft_only',executing:false}}[rpc.params.name];result={content:[{type:'text',text:JSON.stringify(value)}]};}
      catch{result={isError:true,content:[{type:'text',text:'Read model unavailable'}]};}
    }else return json({jsonrpc:'2.0',id:rpc.id??null,error:{code:-32601,message:'Read-only method not found'}});
    return json({jsonrpc:'2.0',id:rpc.id??null,result});
  }
  return null;
}
