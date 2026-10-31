// Owner-private, sanitized attempt receipts. Requires normal D1 migration 0012.
// No runtime DDL, caller-selected owner, payload persistence, pruning or replay.
// Site-platform owner authentication is the existing boundary; this is not a
// new user authentication mechanism. Never project these records publicly.
const SHIPYARD_PYTHON_ATTEMPT_SCOPE = '__SITE_SCOPE_ID__';
const SHIPYARD_PYTHON_ATTEMPT_CAP = 10000;
const SHIPYARD_PYTHON_ATTEMPT_COLUMNS = 'sequence,scope,attempt_id,request_id,idempotency_key,engine,symbol,created_at,updated_at,stage,submission_outcome,terminal,failure_code,job_id,job_created_at,build_id,input_hash,source_receipts_json';
const SHIPYARD_PYTHON_ATTEMPT_STAGES = ['received','service_check','calendar','preopen','market_bars','event_schedule','inputs_ready','submitting','accepted'];
function shipyardPythonAttemptId(value) { return typeof value === 'string' && /^[a-f0-9]{32}$/.test(value); }
function shipyardPythonAttemptKey(row) { return `shipyard-${row.engine}:${row.request_id}`; }
function shipyardPythonAttemptClocks(value) {
  const names = ['calendar','intraday','current_intraday','preopen_daily','preopen_prior_5m','preopen_captured_at','preopen_capture','event_schedule','provider_received_at'];
  return Object.fromEntries(names.filter(key => timestamp(value?.[key])).map(key => [key, timestamp(value[key])]));
}
function shipyardPythonAttemptFailure(value) {
  if (value === null) return null;
  const special = ['market_closed','service_token_not_configured','service_unreachable_or_contract_mismatch','research_job_submission_failed','research_inputs_unavailable','receipt_storage_unavailable','receipt_write_failed','request_cancelled_before_submit'];
  return special.includes(value) || shipyardPythonSafeError({message:value}) === value ? value : 'research_inputs_unavailable';
}
function shipyardPythonAttemptProject(row) {
  if (!row || row.scope !== SHIPYARD_PYTHON_ATTEMPT_SCOPE || !Number.isSafeInteger(row.sequence) || row.sequence < 1
      || !shipyardPythonAttemptId(row.attempt_id) || !shipyardPythonAttemptId(row.request_id)
      || !['saty','rre'].includes(row.engine) || !['SPY','QQQ'].includes(row.symbol)
      || row.idempotency_key !== shipyardPythonAttemptKey(row)
      || !SHIPYARD_PYTHON_ATTEMPT_STAGES.includes(row.stage) || !['unknown','not_submitted','accepted'].includes(row.submission_outcome)
      || ![0,1].includes(row.terminal) || !timestamp(row.created_at) || !timestamp(row.updated_at)
      || (row.job_id !== null && !shipyardPythonAttemptId(row.job_id))
      || (row.input_hash !== null && !/^[a-f0-9]{64}$/.test(row.input_hash))
      || (row.build_id !== null && (typeof row.build_id !== 'string' || !/^silicon-[a-f0-9]{40}$/.test(row.build_id)))
      || (row.submission_outcome !== 'accepted' && (row.job_id !== null || row.job_created_at !== null || row.build_id !== null || row.stage === 'accepted'))
      || (row.submission_outcome === 'not_submitted' && row.terminal !== 1)
      || (row.submission_outcome === 'accepted' && (row.terminal !== 1 || row.stage !== 'accepted' || row.failure_code !== null || !row.input_hash || !row.job_id || !timestamp(row.job_created_at) || !row.build_id))) throw Error('receipt_storage_unavailable');
  let source;
  try { if (typeof row.source_receipts_json !== 'string' || row.source_receipts_json.length > 2048) throw Error(); source = JSON.parse(row.source_receipts_json); }
  catch { throw Error('receipt_storage_unavailable'); }
  return { schema: 'SHIPYARD_PYTHON_ATTEMPT_V1', sequence: row.sequence, attempt_id: row.attempt_id, request_id: row.request_id,
    engine: row.engine, symbol: row.symbol, created_at: timestamp(row.created_at), updated_at: timestamp(row.updated_at),
    stage: row.stage, submission_outcome: row.submission_outcome, terminal: row.terminal === 1,
    failure_code: shipyardPythonAttemptFailure(row.failure_code), job_id: row.job_id,
    job_created_at: timestamp(row.job_created_at), build_id: row.build_id,
    input_sha256: row.input_hash, source_receipts: shipyardPythonAttemptClocks(source),
    receipt_persisted: true, retrieval_freshness: 'stored_attempt_not_requalified',
    research_only: true, decision_eligible: false, order_submission_enabled: false, replay_supported: false };
}
function shipyardPythonAttemptDatabase(env) {
  if (!env.DB || typeof env.DB.prepare !== 'function') throw Error('receipt_storage_unavailable');
  return env.DB;
}
async function shipyardPythonAttemptRow(env, attemptId) {
  return shipyardPythonAttemptDatabase(env).prepare(`SELECT ${SHIPYARD_PYTHON_ATTEMPT_COLUMNS} FROM shipyard_python_attempts WHERE scope=? AND attempt_id=?`)
    .bind(SHIPYARD_PYTHON_ATTEMPT_SCOPE, attemptId).first();
}
async function shipyardPythonAttemptStart(env, attemptId, requestId, engine, symbol) {
  const db = shipyardPythonAttemptDatabase(env), key = shipyardPythonAttemptKey({engine,request_id:requestId});
  // One atomic unique insert elects the sole creator. A duplicate never prepares
  // new inputs or POSTs, even if the first invocation is still in flight.
  let created=false;
  try {
  const result = await db.prepare("INSERT INTO shipyard_python_attempts (scope,attempt_id,request_id,idempotency_key,engine,symbol,created_at,updated_at,stage,submission_outcome,terminal,source_receipts_json) SELECT ?,?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),'received','unknown',0,'{}' WHERE (SELECT COUNT(*) FROM shipyard_python_attempts WHERE scope=?)<? ON CONFLICT(scope,attempt_id) DO NOTHING")
    .bind(SHIPYARD_PYTHON_ATTEMPT_SCOPE,attemptId,requestId,key,engine,symbol,SHIPYARD_PYTHON_ATTEMPT_SCOPE,SHIPYARD_PYTHON_ATTEMPT_CAP).run();
  if (result?.success !== true || ![0,1].includes(result.meta?.changes)) throw Error('receipt_storage_unavailable');
  created=result.meta.changes===1;
  const row = await shipyardPythonAttemptRow(env, attemptId), receipt = shipyardPythonAttemptProject(row);
  if (row.engine !== engine || row.symbol !== symbol) throw Error('attempt_identity_conflict');
  if (result.meta.changes === 1 && (row.request_id !== requestId || row.idempotency_key !== key || row.stage !== 'received' || row.terminal !== 0)) throw Error('receipt_storage_unavailable');
  return { created, receipt, row };
  } catch (error) { error.attempt_created=created; throw error; }
}
async function shipyardPythonAttemptUpdate(env, attempt, change) {
  const row = attempt.row;
  const next = { ...row, ...change, source_receipts_json: JSON.stringify(shipyardPythonAttemptClocks({
    ...JSON.parse(row.source_receipts_json), ...(change.source_receipts || {}),
  })) };
  const result = await shipyardPythonAttemptDatabase(env).prepare("UPDATE shipyard_python_attempts SET stage=?,submission_outcome=?,terminal=?,failure_code=?,job_id=?,job_created_at=?,build_id=?,input_hash=?,source_receipts_json=?,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE scope=? AND attempt_id=? AND request_id=? AND terminal=0")
    .bind(next.stage,next.submission_outcome,next.terminal,next.failure_code ?? null,next.job_id ?? null,next.job_created_at ?? null,next.build_id ?? null,next.input_hash ?? null,next.source_receipts_json,SHIPYARD_PYTHON_ATTEMPT_SCOPE,row.attempt_id,row.request_id).run();
  if (result?.success !== true || result.meta?.changes !== 1) throw Error('receipt_write_failed');
  const actual = await shipyardPythonAttemptRow(env,row.attempt_id), receipt = shipyardPythonAttemptProject(actual);
  for (const key of ['scope','attempt_id','request_id','idempotency_key','engine','symbol','sequence','created_at','stage','submission_outcome','terminal','failure_code','job_id','job_created_at','build_id','input_hash','source_receipts_json']) {
    if ((actual[key] ?? null) !== (next[key] ?? null)) throw Error('receipt_write_failed');
  }
  attempt.row = actual; attempt.receipt = receipt;
  return receipt;
}
async function shipyardPythonAttemptFinish(env, attempt, code, sourceClocks = {}) {
  try {
    await shipyardPythonAttemptUpdate(env,attempt,{ terminal:1, submission_outcome:'not_submitted', failure_code:shipyardPythonAttemptFailure(code), source_receipts:sourceClocks });
    return {attempt_id:attempt.row.attempt_id,request_id:attempt.row.request_id,receipt_persisted:true,attempt_receipt:attempt.receipt};
  } catch {
    // Only called before POST. Durable pending remains unknown; never rewrite
    // that row as certain absence when a persistence operation did not succeed.
    return {attempt_id:attempt.row.attempt_id,request_id:attempt.row.request_id,receipt_persisted:false,receipt_error:'receipt_write_failed'};
  }
}
function shipyardPythonAttemptQuery(args) {
  return args && typeof args === 'object' && !Array.isArray(args) && Object.keys(args).every(k=>['engine','symbol','limit','before'].includes(k))
    && (args.engine === undefined || ['saty','rre'].includes(args.engine)) && (args.symbol === undefined || ['SPY','QQQ'].includes(args.symbol))
    && (args.limit === undefined || Number.isSafeInteger(args.limit) && args.limit >= 1 && args.limit <= 20)
    && (args.before === undefined || Number.isSafeInteger(args.before) && args.before >= 1);
}
async function shipyardPythonAttemptRead(env, args = {}, attemptId = null) {
  const base = {schema:'SHIPYARD_PYTHON_ATTEMPT_HISTORY_V1',research_only:true,decision_eligible:false,order_submission_enabled:false,
    retrieval_freshness:'stored_attempt_not_requalified',replay_supported:false,retention:{max_attempts:SHIPYARD_PYTHON_ATTEMPT_CAP,policy:'pause_at_cap_no_automatic_deletion'}};
  try {
    if (attemptId) {
      const row = await shipyardPythonAttemptRow(env,attemptId);
      return row ? json({...base,status:'recorded',attempt:shipyardPythonAttemptProject(row)}) : json({...base,status:'not_found',error:'attempt_not_recorded',note:'Not found does not prove that no remote job exists.'},404);
    }
    const where=['scope=?'],values=[SHIPYARD_PYTHON_ATTEMPT_SCOPE],limit=args.limit ?? 20;
    for (const key of ['engine','symbol']) if (args[key]) { where.push(`${key}=?`); values.push(args[key]); }
    if (args.before !== undefined) { where.push('sequence<?'); values.push(args.before); }
    const result=await shipyardPythonAttemptDatabase(env).prepare(`SELECT ${SHIPYARD_PYTHON_ATTEMPT_COLUMNS} FROM shipyard_python_attempts WHERE ${where.join(' AND ')} ORDER BY sequence DESC LIMIT ?`).bind(...values,limit+1).all();
    if (result?.success === false || !Array.isArray(result?.results) || result.results.length > limit+1) throw Error('receipt_storage_unavailable');
    const rows=result.results.slice(0,limit).map(shipyardPythonAttemptProject);
    return json({...base,status:'recorded',attempts:rows,has_more:result.results.length>limit,next_before:result.results.length>limit?rows.at(-1).sequence:null,
      note:'Only attempts recorded by this Site are listed. Older remote jobs are not backfilled or enumerated.'});
  } catch { return json({...base,status:'unavailable',error:'receipt_storage_unavailable',migration_required:'0012_python_attempt_receipts'},503); }
}
async function shipyardPythonAttemptLink(env, record) {
  try {
    const row=await shipyardPythonAttemptDatabase(env).prepare(`SELECT ${SHIPYARD_PYTHON_ATTEMPT_COLUMNS} FROM shipyard_python_attempts WHERE scope=? AND job_id=? ORDER BY sequence DESC LIMIT 1`).bind(SHIPYARD_PYTHON_ATTEMPT_SCOPE,record.id).first();
    if (!row) return {attempt_linkage:'not_recorded',attempt_receipt:null};
    const receipt=shipyardPythonAttemptProject(row);
    if (receipt.engine!==record.engine || receipt.symbol!==record.symbol || receipt.build_id!==record.build_id) return {attempt_linkage:'identity_mismatch'};
    return {attempt_linkage:'exact_job_id',attempt_receipt:receipt};
  } catch { return {attempt_linkage:'receipt_storage_unavailable',attempt_receipt:null}; }
}
