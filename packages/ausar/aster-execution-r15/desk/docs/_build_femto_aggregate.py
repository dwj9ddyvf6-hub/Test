import collections, hashlib, json, pathlib, re
D=pathlib.Path('/workspace/agentic-desk/docs')
COMMIT='b19f9d7a1f92f12883ced3c7cd3fa30e37a0c8c4'
FILES=['FEATURES_FEMTO_CORE_CRITICAL.json','FEATURES_FEMTO_OPERATIONS.json','FEATURES_FEMTO_SLEEVES.json']
if (D/'FEATURES_FEMTO_ANCILLARY.json').exists(): FILES.append('FEATURES_FEMTO_ANCILLARY.json')
ORCH=D/'FEATURES_FEMTO_EXTERNAL_AGENTS.json'
if ORCH.exists(): FILES.append(ORCH.name)
companions={f:json.loads((D/f).read_text()) for f in FILES}
legacy=json.loads((D/'review-femto-midna-operational-contracts.json').read_text())
core_groups={
 'scan_runtime':['U03','U06','U25'],'market_clock':['U05','U11'],'paper_mode':['U10','U30'],
 'broker_contract':['U10','U13','U14'],'resource_locks':['U08'],'recovery_provenance':['U08','U15'],
 'scan_receipts':['U06','U09','U21'],'broker_truth':['U10','U12','U15'],'idempotent_orders':['U13'],
 'commitment_capacity':['U17'],'parallel_reads':['U11','U25'],'order_state_machine':['U13','U14','U15'],
 'terminal_partial_fill':['U14','U16'],'fill_plan_bridge':['U12','U19'],'stale_order_cleanup':['U14','U15'],
 'position_protection':['U16','U21'],'protection_recovery':['U15','U16'],'risk_reduction_paths':['U18'],
 'exposure_accounting':['U17','U19','U20'],'exposure_reconciliation':['U15','U17'],'entry_reservations':['U17'],
 'risk_verdicts':['U17','U21'],'drawdown_history':['U17','U20'],'advisory_reductions':['U17','U24'],
 'data_lineage':['U11','U26'],'scorer_contract':['U25','U26'],'decision_outcomes':['U19','U24','U26'],
 'calibration_permissions':['U26'],'calibration_evidence':['U26'],'calibration_rollback':['U18','U26']}
ops_groups={
 'ops_broker_read_contracts':['U10','U15'],'ops_stock_order_types':['U10','U16'],
 'ops_options_order_adapters':['U10','U16'],'ops_close_cancel_receipts':['U14','U16'],
 'ops_marketdata_protocol':['U11'],'ops_api_failure_budget':['U06','U11'],
 'ops_journal':['U09','U24'],'ops_health':['U04','U21'],
 'ops_outcome_store':['U08','U26','U27'],'ops_forward_outcomes':['U20','U26'],
 'ops_decision_attribution':['U19','U24'],'ops_regime_stats':['U19','U20'],
 'ops_nightly_review':['U24','U26'],'ops_registry_activity':['U09','U24'],
 'ops_scorecards':['U19','U20'],'ops_streak_reporting':['U20','U24'],
 'ops_authority_docs':['U17','U24','U26'],'ops_position_audit':['U15','U21'],
 'ops_scheduled_health_audit':['U06','U21'],'ops_exact_engine_contract':['U25','U26'],
 'ops_drift_watch':['U21','U26'],'ops_daily_context':['U11','U25'],
 'ops_news_inputs':['U11','U25','U26'],'ops_calendar_unknown':['U05','U11'],
 'ops_entry_pause_contract':['U18','U21'],'ops_research_tools':['U25','U26'],
 'ops_edgar_observation':['U11','U25','U26'],'ops_oi_observations':['U11','U26'],
 'ops_research_pipeline':['U03','U25','U26'],'ops_snapshot_broker_truth':['U10','U19','U22'],
 'ops_snapshot_validation':['U19','U21','U22'],'ops_attribution_panels':['U19','U20'],
 'ops_reference_panels':['U05','U20'],'ops_narrative_projection':['U22'],
 'ops_publishing':['U22','U23'],'ops_public_client':['U22'],
 'ops_terminal_artifact_publish':['U22']}
orch_groups={
 'external-scheduler':['U03','U05','U06','U25'],'keyed-delegation':['U01','U06','U25'],
 'checkpoint-resume':['U03','U06','U08','U25'],'budgets':['U06','U25'],
 'premarket-analyst':['U25','U26'],'earnings-curator':['U05','U11','U25'],
 'nightly-strategist':['U24','U25','U26'],'postmortems':['U19','U24','U25'],
 'bounded-calibration':['U17','U26'],'weekly-review':['U20','U24','U25'],
 'continuous-reconcile':['U03','U15','U16','U18'],'event-delivery':['U09','U23'],
 'readonly-audit':['U19','U21','U25'],'safe-bugcheck':['U21','U24','U25'],
 'full-code-auditor':['U21','U25'],'version-drift':['U21','U26'],
 'peer-inbox':['U09','U25','U28'],'research-collectors':['U11','U25','U26'],
 'research-governance':['U24','U26'],'verification-gates':['U21','U25','U26'],
 'feed-refresh':['U21','U22'],'artifact-actions':['U06','U25','U27'],
 'public-contract':['U19','U22'],'diagnostic-approval':['U17','U24','U26']}
ancillary_groups={
 'ancillary_structured_engine_cli':['U25','U26'],
 'ancillary_offline_replay_harnesses':['U06','U25','U26','U30'],
 'ancillary_cross_sectional_missing_data':['U11','U20','U26']}
features=[]
for f in legacy['features']:
    f=dict(f)
    f['provenance_scope']='supplemental chronology, published snapshot or reported agent/operator behavior; actual source companions supersede earlier absent-source interpretation'
    f['current_status']='historical narrative/protocol evidence; consult actual-code companion for implementation'
    features.append(f)
for filename,j in companions.items():
    prefix=('core.' if 'CORE_CRITICAL' in filename else 'ops.' if 'OPERATIONS' in filename else 'sleeves.' if 'SLEEVES' in filename else 'ancillary.' if 'ANCILLARY' in filename else 'orchestration.')
    for original in j['features']:
        groups=original.get('parity_groups')
        if groups is None:
            mapping=core_groups if prefix=='core.' else ops_groups if prefix=='ops.' else orch_groups if prefix=='orchestration.' else ancillary_groups if prefix=='ancillary.' else {}
            groups=mapping.get(original['id'])
        if groups is None:
            # External companion must provide precise categories before it can
            # be marked mapped; do not silently map arbitrary source features.
            raise RuntimeError('Need parity groups for '+filename+':'+original['id'])
        refs=[dict(e) for e in original.get('source_evidence',original.get('sources',original.get('evidence',[])))]
        if prefix=='orchestration.':
            for e in refs:
                e['commit']=e.get('commit',e.get('ref'))
                e['classification']=original.get('evidence_class','archived configuration/orchestration source; no execution observed')
        tests=original.get('test_source_evidence',[])
        normalized={
            'id':prefix+original['id'],'feature':original.get('title',original.get('feature',original['id'])),
            'source_behavior':original.get('observed_mechanism',original.get('source_behavior',original.get('behavior',''))),
            'new_desk_requirement':original.get('implementable_requirement',original.get('new_desk_requirement',original.get('generic_requirements_for_new_zero_strategy_desk',''))),
            'sources':refs,'test_sources':tests,
            'dependencies_or_configuration':original.get('configuration_dependencies',[]),
            'limits_and_status':original.get('limits',[]),'parity_groups':groups,
            'current_status':original.get('current_status','archived external workflow/config source; host/provider/execution not verified' if prefix=='orchestration.' else 'implemented in pinned historical source; deployment/test execution not verified'),
            'source_artifact':filename,'provenance_scope':'actual pinned source; companion describes full versus selected body-review scope',
            'strategy_specific':False,'target_status':'planned; not a new-application verification claim'}
        if original['id']=='ops_nightly_review':
            normalized['current_status']='implemented but statically blocked at pinned commit: datetime class is used as datetime.timezone; companion records exact evidence'
            normalized['limits_and_status']=list(normalized['limits_and_status'])+['Nightly strategist path is not functioning runtime proof at this commit; source body includes a confirmed datetime namespace error before output writes.']
        features.append(normalized)

assert len({f['id'] for f in features})==len(features)
roots=list(legacy['source_roots'])+[{'key':'recovered_femto_runtime','repo':'dwj9ddyvf6-hub/Midna','ref':'historical main snapshot','sha':COMMIT,'local_root':'/workspace/github-review/historical-source/Midna/b19f9d7a','root_path':'workspace/alpaca-swing-desk'}]
inventory=[]
for filename,j in companions.items():
    for kind in ['reviewed_file_inventory','test_source_inventory','reviewed_files']:
        for item in j.get(kind,[]): inventory.append({'artifact':filename,'kind':kind,'record':item})
def path_of(x): return x.get('path',x.get('source',{}).get('path'))
canonical=json.loads((D/'FEMTO_CANONICAL_CORE_MANIFEST.json').read_text())
canonical_source={x['path'] for x in canonical['files'] if x['path'].endswith(('.py','.js','.mjs','.cjs','.ts','.tsx'))}
declared={path_of(x['record']) for x in inventory}
uncovered=sorted(canonical_source-declared)
gaps=[]
for filename,j in companions.items():
    for item in j.get('operational_gaps',[]): gaps.append({'artifact':filename,'record':item})
for f in features:
    if f['id'].startswith('sleeves.') and f.get('limits_and_status'):
        gaps.append({'artifact':'FEATURES_FEMTO_SLEEVES.json','record':{'feature':f['id'],'limits':f['limits_and_status'],'source_evidence':f['sources']}})

# Evidence validation does not substitute for body review or runtime tests.
all_refs=[e for f in features for e in f.get('sources',[])+f.get('test_sources',[])]
for e in all_refs:
    commit=e.get('commit',e.get('commit_sha'))
    assert re.fullmatch('[0-9a-f]{40}',commit or ''),e
    line=e.get('line_start',e.get('line')) or (e.get('lines') or [None])[0]
    end=e.get('line_end',e.get('end_line',line)) or (e.get('lines') or [line])[-1]
    if e.get('lines'): line,end=e['lines'][0],e['lines'][-1]
    assert isinstance(line,int) and isinstance(end,int) and 0<line<=end,e
    assert e.get('path') and '/blob/'+commit+'/' in e.get('url',''),e
    p=e.get('local_path')
    if p and pathlib.Path(p).is_file() and e.get('sha256'):
        assert hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==e['sha256'],p

doc={'schema_version':3,'title':'Femto/Midna actual-source operational feature inventory',
 'identity':{'name':'Femto/Midna','repository':'Midna','canonical_runtime_commit':COMMIT,'canonical_runtime_root':'workspace/alpaca-swing-desk','external_dependencies_root':'workspace/skills/alpaca-paper','published_ui_repo':'Femto','status':'Complete historical executable desk core recovered; deployment health and current account state not tested'},
 'source_roots':roots,'companion_artifacts':FILES,'supplemental_chronology_artifact':'review-femto-midna-operational-contracts.json',
 'runtime_classification':{'python_broker_loops':'Actual deterministic paper broker/data lifecycle jobs with persistent state; scheduler is external.','external_agents':'Recovered external workflow source invokes keyed agent({key,label,timeoutMs,schema}) and parallel workers; 70 archived cron prompts and seven workflows describe analyst/reviewer/curator duties. Host/provider/current execution receipts are unverified.','nightly_review':'Deterministic strategist exists but pinned implementation has a static namespace blocker; external no-order model strategist is a separate source-defined role.','published_ui':'Projection over snapshots; static site is not order runtime.'},
 'features':features,'operational_gaps':gaps,'review_inventory':inventory,
 'coverage':{'canonical_executable_or_test_files':len(canonical_source),'canonical_files_with_declared_review_or_classification':len(canonical_source&declared),'canonical_files_not_declared_in_companion_review_inventory':uncovered,'companion_counts':{f:j.get('coverage_counts',j.get('counts',{})) for f,j in companions.items()},'meaning':'Full-body, selected named-body and scope-classification records remain explicit per file. Strategy algorithm bodies and strategy-only tests are intentionally outside transfer scope. A source hash verification is not a body-review claim.'},
 'limitations':['Historical pinned code establishes source capability, not deployment/account health or current test results.','External agent prompts/workflows and deterministic paper loops are distinct execution layers.','No historical strategy, signal thresholds, capital, holdings, allocation or permission requirements are imported.','Tests were read statically only; some are source-pattern pins or stale fixtures, not comprehensive end-to-end guarantees.','Per-source review depth is retained; this report does not claim every mathematical body of all 136 canonical files was exhaustively audited.'],
 'verification':{'pinned_reference_shape_checks':True,'available_sha256_sources_match':True,'historical_sources_imported_or_executed':False,'broker_orders_or_external_notifications_sent':False},
 'counts':{'features':len(features),'actual_runtime_or_interface_features':sum(f['id'].startswith(('core.','ops.','sleeves.','ancillary.')) for f in features),'external_orchestration_or_archived_config_features':sum(f['id'].startswith('orchestration.') for f in features),'supplemental_narrative_features':len(legacy['features']),'source_and_test_citations':len(all_refs),'operational_gaps_or_limits':len(gaps)}}
(D/'FEATURES_FEMTO.json').write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(doc['counts']))
