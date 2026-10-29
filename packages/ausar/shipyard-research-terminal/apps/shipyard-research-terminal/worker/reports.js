// Public reporting only. Inputs are the existing sanitized paper-book projection.
const REPORT_VERSION='public-book-totals-v1';
const REPORT_PREFIX='ausar-report-v1:';
const REPORT_HISTORY=32;
let reportReadCache=null;

// Python round(x, 8): round the exact binary64 rational with ties to even,
// then parse its decimal representation once (avoid double rounding).
function reportRound8(value){
  if(!Number.isFinite(value))throw Error('aggregate_overflow');
  if(value===0)return 0;
  const negative=value<0,view=new DataView(new ArrayBuffer(8));view.setFloat64(0,Math.abs(value));
  const bits=view.getBigUint64(0),exponent=Number((bits>>52n)&2047n);
  let n=bits&((1n<<52n)-1n),shift=exponent?exponent-1023-52:-1074;
  if(exponent)n+=1n<<52n;
  let denominator=1n;n*=100000000n;
  if(shift>=0)n<<=BigInt(shift);else denominator<<=BigInt(-shift);
  let q=n/denominator;const remainder=n%denominator;
  if(remainder*2n>denominator||(remainder*2n===denominator&&q%2n))q++;
  const digits=q.toString().padStart(9,'0');
  return Number((negative?'-':'')+digits.slice(0,-8)+'.'+digits.slice(-8));
}
function aggregatePublicBooks(books){
  if(!Array.isArray(books)||books.length>200)throw Error('report_book_bound');
  const totals={},coverage={},summary={closed_roundtrips:0,wins:0,losses:0};
  for(const input of books){
    const book=record(input),code=currency(book.currency);
    if(!totals[code]){
      if(Object.keys(totals).length>=16)throw Error('report_currency_bound');
      totals[code]=Object.fromEntries(ACCOUNT_FIELDS.map(k=>[k,0]));totals[code].book_count=0;
      coverage[code]=Object.fromEntries(ACCOUNT_FIELDS.map(k=>[k,0]));
    }
    totals[code].book_count++;
    for(const field of ACCOUNT_FIELDS){const value=finite(book[field]);if(value!==null){totals[code][field]+=value;coverage[code][field]++;}}
    for(const field of ['closed_roundtrips','wins','losses']){const value=whole(book[field]);if(value!==null){summary[field]+=value;if(!Number.isSafeInteger(summary[field]))throw Error('report_count_overflow');}}
  }
  for(const row of Object.values(totals))for(const field of ACCOUNT_FIELDS){row[field]=reportRound8(row[field]);if(Math.abs(row[field])>1e18)throw Error('report_public_numeric_bound');}
  const denominator=summary.wins+summary.losses;if(!Number.isSafeInteger(denominator))throw Error('report_count_overflow');
  summary.win_rate_percent=denominator?(summary.wins/denominator)*100:null;
  return {currency_totals:totals,performance_summary:summary,coverage};
}
function reportEnvelope(body,receivedAt){
  const sourceAge=Date.now()-Date.parse(body.observed_at_utc),receiptAge=Date.now()-Date.parse(receivedAt);
  return {...body,received_at_utc:receivedAt,source_age_ms:sourceAge,receipt_age_ms:receiptAge,
    status:sourceAge<0||receiptAge<0?'clock_skew':sourceAge>900000||receiptAge>180000?'stale':'observed',
    authority:'Derived public report only; no ledger, order or readiness authority.'};
}
async function verifiedReport(env,row){
  const metadata=JSON.parse(row.quality_json),object=await env.BUCKET.get(metadata.artifact_key);
  if(!object)throw Error('report_artifact_unavailable');
  const text=await object.text();if(new TextEncoder().encode(text).length>65536||await digest(text)!==row.etag)throw Error('report_integrity');
  return {body:JSON.parse(text),receivedAt:metadata.source_received_at};
}
async function trimReportHistory(env){
  const rows=(await env.DB.prepare('SELECT view_key,quality_json FROM observatory_read_models WHERE view_key LIKE ? ORDER BY input_watermark_at DESC,view_key DESC LIMIT 8 OFFSET 32').bind(REPORT_PREFIX+'%').all()).results;
  for(const row of rows){await env.DB.prepare('DELETE FROM observatory_read_models WHERE view_key=?').bind(row.view_key).run();
    try{await env.BUCKET.delete(JSON.parse(row.quality_json).artifact_key);}catch{}}
}
async function sweepReportArtifacts(env){
  const rows=(await env.DB.prepare('SELECT quality_json FROM observatory_read_models WHERE view_key LIKE ? LIMIT 40').bind(REPORT_PREFIX+'%').all()).results;
  const keep=new Set(rows.map(r=>JSON.parse(r.quality_json).artifact_key));
  const page=await env.BUCKET.list({prefix:'ausar-reports/v1/',limit:100});
  for(const object of page.objects||[])if(!keep.has(object.key)&&Date.now()-new Date(object.uploaded).getTime()>86400000)await env.BUCKET.delete(object.key);
}
async function materializeLatestReport(env){
  const source=await env.DB.prepare('SELECT payload_json,received_at_utc,payload_sha256 FROM ausar_terminal_snapshots WHERE id=1').first();
  if(!source)return null;
  if(new TextEncoder().encode(source.payload_json).length>MAX_SNAPSHOT_BYTES||await digest(source.payload_json)!==source.payload_sha256)throw Error('report_source_integrity');
  const key=REPORT_PREFIX+source.payload_sha256;
  const existing=await env.DB.prepare('SELECT etag,quality_json FROM observatory_read_models WHERE view_key=?').bind(key).first();
  if(existing)return verifiedReport(env,existing);
  await trimReportHistory(env);
  const count=await env.DB.prepare('SELECT count(*) AS n FROM observatory_read_models WHERE view_key LIKE ?').bind(REPORT_PREFIX+'%').first();
  if(count.n>=40)throw Error('report_retention_backpressure');
  const input=sanitize(JSON.parse(source.payload_json)),calculated=aggregatePublicBooks(input.books);
  const report={schema:'AUSAR_PUBLIC_REPORT_V1',formula_version:REPORT_VERSION,formula_reference_sha256:'5fe1b003f8c529787591c0000ae2cd65efa0e18fa30ca88ed7b217fe23229d2e',source_sha256:source.payload_sha256,
    observed_at_utc:input.observed_at_utc,book_count:input.books.length,...calculated,
    coverage_note:'Sums follow the publisher formula: missing values contribute no amount; coverage counts show incompleteness. Currencies are never pooled.'};
  const text=JSON.stringify(report),hash=await digest(text),artifactKey='ausar-reports/v1/'+hash+'.json';
  if(new TextEncoder().encode(text).length>65536)throw Error('report_size');
  await env.BUCKET.put(artifactKey,text,{httpMetadata:{contentType:'application/json'}});
  const check=await env.BUCKET.get(artifactKey);if(!check||await digest(await check.text())!==hash)throw Error('report_upload_verification');
  const quality=JSON.stringify({artifact_key:artifactKey,source_received_at:source.received_at_utc});
  await env.DB.prepare('INSERT OR IGNORE INTO observatory_read_models (view_key,schema_version,generated_at,input_watermark_at,freshness_status,source_mode,etag,record_count,body_json,quality_json) SELECT ?,?,?,?,?,?,?,?,?,? WHERE (SELECT count(*) FROM observatory_read_models WHERE view_key LIKE ?)<40')
    .bind(key,'1',new Date().toISOString(),report.observed_at_utc,'derived','public_snapshot',hash,report.book_count,text,quality,REPORT_PREFIX+'%').run();
  const committed=await env.DB.prepare('SELECT etag,quality_json FROM observatory_read_models WHERE view_key=?').bind(key).first();
  if(!committed||committed.etag!==hash)throw Error('report_publish_conflict');
  // Maintenance never changes the source snapshot or makes a failed report visible.
  try{await trimReportHistory(env);await sweepReportArtifacts(env);}catch{}
  return {body:report,receivedAt:source.received_at_utc};
}
async function reportRoute(request,env){
  const path=new URL(request.url).pathname;
  if(path!=='/api/ausar/report'&&path!=='/api/ausar/reports'&&!path.startsWith('/api/ausar/report/'))return null;
  if(!['GET','HEAD'].includes(request.method))return json({error:'read_only'},405);
  if(!env.DB||!env.BUCKET)return json({error:'report_storage_unavailable'},503);
  try{
    if(path==='/api/ausar/reports'){
      const rows=(await env.DB.prepare('SELECT view_key,etag,input_watermark_at,generated_at,record_count FROM observatory_read_models WHERE view_key LIKE ? ORDER BY input_watermark_at DESC,view_key DESC LIMIT 32').bind(REPORT_PREFIX+'%').all()).results;
      return json({schema:'AUSAR_PUBLIC_REPORT_INDEX_V1',retention:REPORT_HISTORY,reports:rows.map(r=>({source_sha256:r.view_key.slice(REPORT_PREFIX.length),sha256:r.etag,observed_at_utc:r.input_watermark_at,computed_at_utc:r.generated_at,book_count:r.record_count,location:'/api/ausar/report/'+r.view_key.slice(REPORT_PREFIX.length)}))});
    }
    let result;
    if(path==='/api/ausar/report'){
      if(reportReadCache&&Date.now()<reportReadCache.until)result=reportReadCache.value;
      else{
        result=await materializeLatestReport(env);
        reportReadCache={value:result,until:Date.now()+10000};
      }
    }else{
      const id=path.split('/').pop();if(!/^[a-f0-9]{64}$/.test(id))return json({error:'not_found'},404);
      const row=await env.DB.prepare('SELECT etag,quality_json FROM observatory_read_models WHERE view_key=?').bind(REPORT_PREFIX+id).first();
      if(!row)return json({error:'not_found'},404);result=await verifiedReport(env,row);
    }
    return result?json(reportEnvelope(result.body,result.receivedAt)):json({status:'unconnected',error:'source_snapshot_unavailable'},503);
  }catch{return json({error:'report_unavailable',status:'unknown'},503);}
}
