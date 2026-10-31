// Owner-scoped native access to the same fixed-origin Python research routes.
// Running creates a durable research job; it never submits a broker order.
function shipyardPythonToolArguments(name,args) {
  if(!args||typeof args!=='object'||Array.isArray(args))return false;
  if(name==='shipyard_python_status')return Object.keys(args).length===0;
  if(name==='shipyard_python_attempts')return shipyardPythonAttemptQuery(args);
  if(name==='shipyard_python_attempt')return Object.keys(args).length===1&&shipyardPythonAttemptId(args.attempt_id);
  if(name==='shipyard_python_job')return Object.keys(args).length===1&&Object.hasOwn(args,'job_id')&&typeof args.job_id==='string'&&/^[a-f0-9]{32}$/.test(args.job_id);
  return name==='shipyard_python_run'&&[2,3].includes(Object.keys(args).length)&&Object.keys(args).every(key=>['engine','symbol','attempt_id'].includes(key))&&Object.hasOwn(args,'engine')&&Object.hasOwn(args,'symbol')
    &&(args.attempt_id===undefined||shipyardPythonAttemptId(args.attempt_id))
    &&['saty','rre'].includes(args.engine)&&['SPY','QQQ'].includes(args.symbol);
}
async function shipyardPythonNativeTool(request,name,args,env) {
  if(!shipyardPythonToolArguments(name,args))return json({error:'invalid_request'},400);
  const origin=new URL(request.url).origin;
  const path=name==='shipyard_python_status'?'/api/research/python/status':name==='shipyard_python_job'?`/api/research/python/jobs/${args.job_id}`:'/api/research/python/run';
  const historyPath=name==='shipyard_python_attempt'?`/api/research/python/attempts/${args.attempt_id}`:name==='shipyard_python_attempts'?`/api/research/python/attempts?${new URLSearchParams(args)}`:path;
  const headers={'cf-connecting-ip':request.headers.get('cf-connecting-ip')||'mcp'};
  const init={method:'GET',headers,signal:request.signal};
  if(name==='shipyard_python_run')Object.assign(init,{method:'POST',headers:{...headers,origin,'content-type':'application/json'},body:JSON.stringify(args)});
  return shipyardPythonResearchRoute(new Request(new URL(historyPath,origin),init),env);
}
