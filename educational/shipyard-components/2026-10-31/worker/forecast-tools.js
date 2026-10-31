// Request-scoped scalar research calculations, not browser-file ingestion.
// No provider, environment, database, account, persistence, or order access.
const SHIPYARD_FORECAST_BUILD = __SHIPYARD_FORECAST_BUILD__;
const SHIPYARD_FORECAST_INPUT_READINESS = __SHIPYARD_FORECAST_INPUT_READINESS__;
const SHIPYARD_FORECAST_INPUT_POLICY = Object.freeze({
  id: 'explicit_scalar_calculation_request_v1',
  origin: 'caller_supplied_scalar_request',
  storage: 'request_memory_only',
  provenance: 'manual_unverified',
  note: 'Only numeric arguments intentionally supplied to this calculator are accepted. No browser-local CSV, saved dataset, upload, source URL or provenance attestation is read or imported. Existing user.local-csv and user.manual-input browser-only policies are unchanged.',
});
// Single agent-facing source binding registry: this drives feature-pipeline catalog metadata,
// native from-bars dispatch, and the MCP enum. The exact original scorers remain separate.
const SHIPYARD_FORECAST_SOURCE_BINDINGS=Object.freeze({
  FE01:Object.freeze({run:(request,args,env)=>shipyardForecastFE01(request,{symbol:args.symbol},env),
    publication_policy:'legacy',policy:()=>SHIPYARD_FORECAST_TREND_FEATURES.FE01_TREND_POLICY,policyHash:()=>SHIPYARD_FORECAST_TREND_FEATURES.FE01_TREND_POLICY_SHA256}),
  FE02:Object.freeze({run:(request,args,env)=>shipyardForecastFE02(request,{symbol:args.symbol},env),reserved_symbol:'SPY',
    publication_policy:'legacy',policy:()=>SHIPYARD_FORECAST_PAIRED_FEATURES.FE02_PAIRED_POLICY,policyHash:()=>SHIPYARD_FORECAST_PAIRED_FEATURES.FE02_PAIRED_POLICY_SHA256}),
  FE03:Object.freeze({run:(request,args,env)=>shipyardForecastFE03(request,{symbol:args.symbol},env),
    publication_policy:'legacy',policy:()=>SHIPYARD_FORECAST_FE03_FEATURES.FE03_BREAKOUT_POLICY,policyHash:()=>SHIPYARD_FORECAST_FE03_FEATURES.FE03_BREAKOUT_POLICY_SHA256}),
  FE04:Object.freeze({run:(request,args,env)=>shipyardForecastFE04(request,{symbol:args.symbol},env),allowed_symbols:Object.freeze(['SPY','QQQ','IWM']),publication_policy:'private',
    policy:()=>SHIPYARD_FORECAST_FE04_FEATURES.FE04_GAP_POLICY,policyHash:()=>SHIPYARD_FORECAST_FE04_FEATURES.FE04_GAP_POLICY_SHA256}),
  FE05:Object.freeze({run:(request,args,env)=>shipyardForecastFE05(request,args,env),fixed_panel:true,publication_policy:'private',
    policy:()=>SHIPYARD_FE05_FEATURES.FE05_BREADTH_POLICY,policyHash:()=>SHIPYARD_FE05_FEATURES.FE05_BREADTH_POLICY_SHA256}),
  FE07:Object.freeze({run:(request,args,env)=>shipyardForecastFE07(request,args,env),fixed_panel:true,publication_policy:'private',
    policy:()=>SHIPYARD_FE0710_FEATURES.FE07_LEADLAG_POLICY,policyHash:()=>SHIPYARD_FE0710_FEATURES.FE07_LEADLAG_POLICY_SHA256}),
  FE08:Object.freeze({run:(request,args,env)=>shipyardForecastFE08(request,{symbol:args.symbol},env),
    publication_policy:'legacy',policy:()=>SHIPYARD_FORECAST_FEATURES.FE08_RV_POLICY,policyHash:()=>SHIPYARD_FORECAST_FEATURES.FE08_RV_POLICY_SHA256}),
  FE09:Object.freeze({run:(request,args,env)=>shipyardForecastFE09(request,{symbol:args.symbol},env),allowed_symbols:Object.freeze(['SPY','QQQ','IWM']),publication_policy:'private',
    policy:()=>SHIPYARD_FORECAST_FE09_FEATURES.FE09_JUMP_POLICY,policyHash:()=>SHIPYARD_FORECAST_FE09_FEATURES.FE09_JUMP_POLICY_SHA256}),
  FE10:Object.freeze({run:(request,args,env)=>shipyardForecastFE10(request,args,env),fixed_panel:true,publication_policy:'private',
    policy:()=>SHIPYARD_FE0710_FEATURES.FE10_REGIME_POLICY,policyHash:()=>SHIPYARD_FE0710_FEATURES.FE10_REGIME_POLICY_SHA256}),
  FE12:Object.freeze({run:(request,args,env)=>shipyardForecastFE12(request,{symbol:args.symbol},env),allowed_symbols:Object.freeze(['SPY','QQQ','IWM']),publication_policy:'private',
    policy:()=>SHIPYARD_FORECAST_FE12_FEATURES.FE12_TOP_OF_BOOK_POLICY,policyHash:()=>SHIPYARD_FORECAST_FE12_FEATURES.FE12_TOP_OF_BOOK_V3_POLICY_SHA256}),
});
// Different source contract from from-bars: FE06 binds only the fixed official issuer-workbook adapter.
const SHIPYARD_FORECAST_FROM_SOURCE_BINDINGS=Object.freeze({
  FE06:Object.freeze({run:(request,args,env)=>shipyardForecastFE06(request,{engine_id:'FE06',symbol:args.symbol},env),publication_policy:'private',
    policy:()=>SHIPYARD_FE06_POLICY,policyHash:()=>SHIPYARD_FE06_POLICY_SHA256}),
});
const SHIPYARD_FORECAST_SOURCE_ENGINE_IDS=Object.freeze(Object.keys(SHIPYARD_FORECAST_SOURCE_BINDINGS));
// FE28 is a bounded diagnostic capture, not an automatic scorer-feature binding.
const SHIPYARD_FORECAST_PARTIAL_PUBLIC_POLICIES=Object.freeze({
  FE28:Object.freeze({featurePolicyId:'FE28_TREASURY_BIS_CREDIT_ACCELERATION_V1',adapterPolicyId:'FE28_TREASURY_BIS_BEA_PUBLIC_CAPTURE_V1',policyHash:()=>SHIPYARD_FORECAST_BUILD.fe28_public_policy_sha256,
    adapterHash:()=>SHIPYARD_FORECAST_BUILD.fe28_public_adapter_sha256,transformHash:()=>SHIPYARD_FORECAST_BUILD.fe28_public_transform_sha256,tool:'shipyard_forecast_macro_features',
    diagnostic_features:['curve_slope_z','curve_change_z','credit_impulse_z','macro_transition_score'],partial_features:[],
    missing:['curve_slope_z','curve_change_z','credit_impulse_z','macro_transition_score']}),
});

function shipyardForecastCanonical(value) {
  if (Array.isArray(value)) return '[' + value.map(shipyardForecastCanonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + shipyardForecastCanonical(value[key])).join(',') + '}';
  return JSON.stringify(value);
}
async function shipyardForecastHash(value) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(shipyardForecastCanonical(value)));
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}
function shipyardForecastPlain(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
}
function shipyardForecastArguments(name, args) {
  if (!shipyardForecastPlain(args)) return false;
  if (new TextEncoder().encode(JSON.stringify(args)).length > 4096) return false;
  const catalog = SHIPYARD_FORECAST_LOGIC.listForecastEngines();
  if (name === 'shipyard_forecast_catalog') {
    if (Object.keys(args).some(key => !['engine_id', 'offset', 'limit', 'catalog_hash'].includes(key))) return false;
    if ('engine_id' in args && (typeof args.engine_id !== 'string' || !catalog.some(item => item.engine_id === args.engine_id))) return false;
    if ('catalog_hash' in args && (typeof args.catalog_hash !== 'string' || !/^[a-f0-9]{64}$/.test(args.catalog_hash))) return false;
    if ('offset' in args && (!Number.isInteger(args.offset) || args.offset < 0 || args.offset > catalog.length)) return false;
    // Keep the entire MCP envelope below its 160 KiB response ceiling. Full
    // catalog discovery remains available through the pinned continuation.
    if ('limit' in args && (!Number.isInteger(args.limit) || args.limit < 1 || args.limit > 20)) return false;
    if ('engine_id' in args && ('offset' in args || 'limit' in args)) return false;
    return !(args.offset > 0 && !args.catalog_hash);
  }
  if (name !== 'shipyard_forecast_evaluate' || Object.keys(args).length !== 2
    || !Object.hasOwn(args, 'engine_id') || !Object.hasOwn(args, 'features')) return false;
  const engine = catalog.find(item => item.engine_id === args.engine_id);
  if (!engine || !shipyardForecastPlain(args.features)) return false;
  const entries = Object.entries(args.features);
  return entries.length <= engine.inputs.length && entries.every(([key, value]) =>
    engine.inputs.some(input => input.name === key) && typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= 1e18);
}
function shipyardForecastMethod() {
  return {
    id: 'silicon_forecast_numeric_scorer', adapter_version: '1.0.0',
    source: SHIPYARD_FORECAST_LOGIC.SILICON_FORECAST_SOURCE,
    ...SHIPYARD_FORECAST_BUILD,
    scope: 'Exact existing browser numeric scorer, not the Python ForecastEngine provenance, point-in-time or target-label validator. No feature transforms or coefficients are changed.',
  };
}
function shipyardForecastRestrictions() {
  return {
    research_only: true, decision_eligible: false, calibrated_probability: null,
    provider_requests_made: false, database_accessed: false, input_persisted: false,
    source_provenance_verified: false, point_in_time_verified: false, feature_builders_invoked: false,
    catalog_max_age_and_min_quality_enforced: false,
    account_data_returned: false, order_submission_enabled: false,
  };
}
async function shipyardForecastTool(name, args) {
  if (!shipyardForecastArguments(name, args)) return json({ schema: 'SHIPYARD_FORECAST_CALCULATOR_V1', status: 'invalid_request' }, 400);
  const method = shipyardForecastMethod();
  const common = { method, input_policy: SHIPYARD_FORECAST_INPUT_POLICY, restrictions: shipyardForecastRestrictions() };
  if (name === 'shipyard_forecast_catalog') {
    const engines = SHIPYARD_FORECAST_LOGIC.listForecastEngines();
    const sourceFeaturePolicies=Object.fromEntries([
      ...Object.entries(SHIPYARD_FORECAST_SOURCE_BINDINGS).map(([id,binding])=>[id,binding.policyHash()]),
      ...Object.entries(SHIPYARD_FORECAST_FROM_SOURCE_BINDINGS).map(([id,binding])=>[`${id}_FROM_SOURCES`,binding.policyHash()]),
      ...Object.entries(SHIPYARD_FORECAST_PARTIAL_PUBLIC_POLICIES).map(([id,binding])=>[`${id}_PUBLIC_PARTIAL`,{policy:binding.policyHash(),adapter:binding.adapterHash(),transform:binding.transformHash()}]),
    ]);
    const catalogHash = await shipyardForecastHash({ engines, method, input_policy: SHIPYARD_FORECAST_INPUT_POLICY, source_feature_policies: sourceFeaturePolicies });
    if (args.catalog_hash && args.catalog_hash !== catalogHash) return json({ schema: 'SHIPYARD_FORECAST_CATALOG_V1', status: 'catalog_changed', catalog_sha256: catalogHash, message: 'The source, calculator, adapter or contract changed. Restart at offset zero.' }, 409);
    const offset = args.offset || 0, limit = args.limit || 20;
    const selection = args.engine_id ? engines.filter(item => item.engine_id === args.engine_id) : engines.slice(offset, offset + limit);
    return json({ schema: 'SHIPYARD_FORECAST_CATALOG_V1', status: 'available', ...common,
      catalog_sha256: catalogHash, engine_count: engines.length,
      engines: selection.map(engine => ({ ...engine,
        implementation_status: 'numeric_calculator_ready', native_tool: 'shipyard_forecast_evaluate',
        feature_pipeline: shipyardForecastSourceReadiness(engine),
      })),
      pagination: args.engine_id ? null : { offset, limit, total: engines.length, next_offset: offset + limit < engines.length ? offset + limit : null },
    });
  }
  const result = SHIPYARD_FORECAST_LOGIC.evaluateForecastEngine(args.engine_id, args.features);
  const requestHash = await shipyardForecastHash({ engine_id: args.engine_id, features: args.features, method });
  return json({ schema: 'SHIPYARD_FORECAST_CALCULATOR_V1', ...common,
    status: result.status, computed_at: new Date().toISOString(), engine_id: args.engine_id,
    input_origin: SHIPYARD_FORECAST_INPUT_POLICY.origin, input_provenance: 'manual_unverified',
    request_sha256: requestHash, result_sha256: await shipyardForecastHash({ request_sha256: requestHash, result }),
    result,
  });
}

function shipyardForecastSourceReadiness(engine) {
  const fromBars=SHIPYARD_FORECAST_SOURCE_BINDINGS[engine.engine_id],fromSources=SHIPYARD_FORECAST_FROM_SOURCE_BINDINGS[engine.engine_id],partial=SHIPYARD_FORECAST_PARTIAL_PUBLIC_POLICIES[engine.engine_id];
  const binding=fromSources||fromBars,policy=binding?.policy()??null,policyHash=binding?.policyHash()??partial?.policyHash()??null;
  const note=engine.engine_id==='FE06'
    ?'NEW FE06 issuer-workbook derived proxy is available only through shipyard_forecast_from_sources with an allowlisted sector ETF symbol. It uses a current fixed 11-ETF universe, 254 common sessions, target-specific 21-session split-adjusted dividend-excluded NAV rank-z and creation/redemption estimate z, cross-sectional breadth, and prior-252 dispersion normalization. Missing/invalid rows, unknown split-like basis changes, zero variance, calendar gaps or stale/future clocks abstain. It is not observed vendor flow or volume; latest issuer cutoff may lag the latest official session inside the distinct 48h semantic-close bound. Processing is bounded/on-demand for private research; source-use and redistribution rights are not established. Raw workbooks are not persisted or publicly projected. Research-only and decision-ineligible; original FE06 scorer unchanged.'
    :engine.engine_id==='FE28'
    ?'Bounded, no-credential public source diagnostic captures Treasury nominal curve, BIS WS_TC U.S. private non-financial credit plus dataset release metadata, and BEA NIPA Table 1.1.5 current-dollar GDP plus current release metadata. It emits diagnostic_features only; scorer-ready features remain empty until Treasury session completeness/source age, per-quarter BIS/BEA vintages, rights and quality gates are independently validated. Dataset release dates are not per-quarter vintages and are not atomically linked to data downloads. NEW transforms include curve diagnostics, quarterly credit-flow acceleration and an equal-weight tanh transition-risk diagnostic; original transition builder is unrecovered. No scorer invocation or automatic feature binding.'
    :engine.engine_id==='FE03'
    ?'Separate bounded NEW FE03_DAILY_BREAKOUT_ACCEPTANCE_MATURED_V1 uses frozen prior-20-session close-break levels, causal prior-only distance/volume z-scores, 3–5 completed post-cross closes and at least20 matured historical breakout episodes (candidate episode excluded). Missing setup, incomplete acceptance, invalidated level or an insufficient sample abstains with no numeric score. The original builder was not recovered; five-session outcome windows may overlap and are not independent. Original source age retains the48h diagnostic; catalog min-quality0.2/rights attestation remain unknown (score is not the full Python FeatureObservation validator). No historical PIT, calibration or trade admission is claimed.'
    :engine.engine_id==='FE02'
    ?'Separate on-demand builder applies NEW FE02_PAIRED_BENCHMARK_RESIDUAL_SESSION_V2 to current Alpaca IEX split-adjusted daily bars for the requested ticker and SPY. Canonical original features were not recovered; prior-only beta is reused across reconstructed history, so it is not historical point-in-time data. V2 permits descriptive research on the latest completed session in a fresh official calendar; actual source age and original48h age failure remain explicit, with a separate7-day extended-closure guard. Research-only, uncalibrated, and never decision eligible.'
    :engine.engine_id==='FE07'?'Separate fixed NEW SPY-leader→QQQ-follower daily one-session-lag policy; exactly252 prior lagged OLS pairs, current leader-return z excludes the candidate from normalization, and four disjoint63-pair stability blocks. No lag/universe search; beta sign is preserved. Exploratory, not causal/PIT, fitted, calibrated or decision-eligible.'
    :engine.engine_id==='FE10'?'Separate fixed NEW SPY/QQQ/IWM daily ETF proxy panel. Matched complete sessions feed21-session covariance/correlation and252 prior-only scalar normalizers; bounded two-window volatility contrast is a proxy, not a fitted change-point detector. Not market-wide correlation, PIT, calibrated or decision-eligible.'
    :engine.engine_id==='FE05'?'Separate fixed NEW current SPY-holdings top25 issuer cohort: group by verified CUSIP-9 first-six issuer key before ranking current weights, retain every share-class line for selected issuers, and require505 matched complete daily closes per line plus SPY. Computes cohort-relative breadth, advance/decline z, normalized new-high/low z and SPY trend z. Date-only current membership is not historical S&P500/PIT or all-market breadth; source rights/age are unknown, raw member list is private, missing bars abstain with no replacement; research-only and ineligible.'
    :policy?'Separate on-demand source tool builds explicitly NEW versioned features. No recovered canonical builder, fitted forecast or live acquisition success is asserted by this catalog; scalar evaluation stays caller-supplied.':'Required features must be explicitly supplied. Existing readers and daily snapshot features are not automatic builders for these contracts.';
  return {...SHIPYARD_FORECAST_INPUT_READINESS[engine.engine_id],status:partial?'partial_public_source_path':policy?'new_source_policy_available':'not_connected',automatic_feature_binding:!!binding,
    missing_transform_policy:partial?'All exact-name FE28 diagnostic transforms are defined. The public source path deliberately leaves scorer-ready features empty: Treasury session completeness/source age and per-quarter BIS/BEA release/revision vintages are not independently validated; rights/quality gates remain closed.':policy?'Original conventions were unspecified; separate source path freezes NEW '+policy.id+' without changing original coefficients.':SHIPYARD_FORECAST_INPUT_READINESS[engine.engine_id].missing_transform_policy,
    source_tool:partial?partial.tool:policy?(fromSources?'shipyard_forecast_from_sources':'shipyard_forecast_from_bars'):null,feature_policy_id:policy?.id??partial?.featurePolicyId??null,feature_policy_sha256:policyHash,
    missing_builders:partial?partial.missing:policy?[]:engine.inputs.map(input=>input.name),
    note,...(partial?{adapter_policy_id:partial.adapterPolicyId,source_adapter_sha256:partial.adapterHash(),source_transform_sha256:partial.transformHash(),partial_features:partial.partial_features,diagnostic_features:partial.diagnostic_features}:{})};
}
