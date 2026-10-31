// Read-only source-computed research. Never accepts caller datasets or credentials.
function shipyardSourceArguments(name, args) {
  if (!args || typeof args !== 'object' || Array.isArray(args)) return false;
  if (name === 'shipyard_forecast_from_bars') {
    const binding=Object.hasOwn(SHIPYARD_FORECAST_SOURCE_BINDINGS,args.engine_id)?SHIPYARD_FORECAST_SOURCE_BINDINGS[args.engine_id]:null;
    if(!binding)return false;
    if(binding.fixed_panel)return Object.keys(args).length===1&&Object.hasOwn(args,'engine_id');
    return Object.keys(args).length === 2 && Object.hasOwn(args,'engine_id') && Object.hasOwn(args,'symbol')
      && typeof args.symbol === 'string' && /^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$/.test(args.symbol)
      && (!binding.reserved_symbol||args.symbol.toUpperCase()!==binding.reserved_symbol)
      && (!binding.allowed_symbols||binding.allowed_symbols.includes(args.symbol));
  }
  if (name === 'shipyard_forecast_from_sources') {
    return Object.keys(args).length===2&&args.engine_id==='FE06'&&typeof args.symbol==='string'
      &&SHIPYARD_FE06_UNIVERSE.some(row=>row.ticker===args.symbol);
  }
  if (name === 'shipyard_chartslector_scan') return shipyardChartslectorArguments(args);
  return false;
}

async function shipyardSourceResearchRoute(request, env) {
  const url = new URL(request.url);
  if (url.pathname !== '/api/research/forecast/from-bars' && url.pathname !== '/api/research/forecast/from-sources' && url.pathname !== '/api/research/chartslector') return null;
  if (request.method !== 'GET') return json({error:'method_not_allowed'},405);
  const keys = [...url.searchParams.keys()];
  if (url.pathname === '/api/research/forecast/from-bars') {
    const engine_id=url.searchParams.get('engine_id');
    const binding=Object.hasOwn(SHIPYARD_FORECAST_SOURCE_BINDINGS,engine_id)?SHIPYARD_FORECAST_SOURCE_BINDINGS[engine_id]:null;
    const args=binding?.fixed_panel?{engine_id}:{engine_id,symbol:url.searchParams.get('symbol')};
    const expected=binding?.fixed_panel?['engine_id']:['engine_id','symbol'];
    if (keys.length !== expected.length || new Set(keys).size !== expected.length || !keys.every(k => expected.includes(k))
      || !shipyardSourceArguments('shipyard_forecast_from_bars',args)) return json({error:'invalid_request'},400);
    return shipyardForecastFromBars(request,args,env);
  }
  if (url.pathname === '/api/research/forecast/from-sources') {
    const args={engine_id:url.searchParams.get('engine_id'),symbol:url.searchParams.get('symbol')};
    if(keys.length!==2||new Set(keys).size!==2||!keys.every(k=>['engine_id','symbol'].includes(k))
      ||!shipyardSourceArguments('shipyard_forecast_from_sources',args))return json({error:'invalid_request'},400);
    return shipyardForecastFromSources(request,args,env);
  }
  const args = {symbols:[url.searchParams.get('symbol')]};
  if (keys.length !== 1 || keys[0] !== 'symbol' || !shipyardSourceArguments('shipyard_chartslector_scan',args)) return json({error:'invalid_request'},400);
  return shipyardChartslectorRun(request,args,env);
}

async function shipyardForecastFromBars(request,args,env) {
  if(!shipyardSourceArguments('shipyard_forecast_from_bars',args))return json({error:'invalid_arguments'},400);
  return SHIPYARD_FORECAST_SOURCE_BINDINGS[args.engine_id].run(request,args,env);
}
async function shipyardForecastFromSources(request,args,env) {
  if(!shipyardSourceArguments('shipyard_forecast_from_sources',args))return json({error:'invalid_arguments'},400);
  return shipyardForecastFE06(request,{engine_id:args.engine_id,symbol:args.symbol.toUpperCase()},env);
}
