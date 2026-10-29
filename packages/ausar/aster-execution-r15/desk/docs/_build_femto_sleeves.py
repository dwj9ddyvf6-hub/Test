import ast, hashlib, json, pathlib

D = pathlib.Path('/workspace/agentic-desk/docs')
ROOT = pathlib.Path('/workspace/github-review/historical-source/Midna/b19f9d7a')
PREFIX = 'workspace/alpaca-swing-desk/'
COMMIT = 'b19f9d7a1f92f12883ced3c7cd3fa30e37a0c8c4'
manifest = json.loads((D/'FEMTO_CANONICAL_CORE_MANIFEST.json').read_text())
blobs = {x['path']:x for x in manifest['files']}
trees = {}
def tree(file):
    if file not in trees:
        trees[file] = ast.parse((ROOT/PREFIX/file).read_text())
    return trees[file]
def ev(file, name=None, start=None, end=None, classification='executable_source'):
    p = ROOT/PREFIX/file
    data = p.read_bytes()
    if name:
        n = next(n for n in ast.walk(tree(file)) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name == name)
        start,end = n.lineno,n.end_lineno
    start = start or 1
    end = end or start
    path = PREFIX+file
    git_sha = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert git_sha == blobs[path]['sha'],path
    return {'repo':'Midna','repository':'dwj9ddyvf6-hub/Midna','commit':COMMIT,'path':path,'line_start':start,'line_end':end,
            'local_path':str(p),'git_blob_sha':git_sha,'sha256':hashlib.sha256(data).hexdigest(),
            'url':f'https://github.com/dwj9ddyvf6-hub/Midna/blob/{COMMIT}/{path}#L{start}',
            'classification':classification}
features = []
def f(id,title,behavior,req,groups,refs,tests=(),deps=(),limits=()):
    features.append({'id':id,'title':title,'observed_mechanism':behavior,'implementable_requirement':req,
                     'parity_groups':groups,'source_evidence':[ev(*r) for r in refs],
                     'test_source_evidence':[ev(*r,classification='static_test_source') for r in tests],
                     'configuration_dependencies':list(deps),'limits':list(limits),
                     'current_status':'implemented in pinned historical source; deployment and historical test execution unverified',
                     'transfer_status':'operational infrastructure only; strategy rules, capital, position sizing defaults and numerical thresholds excluded'})

f('variant_duties','Explicit worker duties and bounded batch invocation',
  'Runners expose separate rank/scan, fill, settle, daily, intraday, reconcile and status duties; each invocation returns. Cadences are external scheduler contracts rather than embedded model workers.',
  'Configure durable jobs by duty, submission window and completion receipt; run independently of UI and distinguish deterministic job from reasoning agent.',
  ['U03','U05','U06'],[('bilbo_options.py','main'),('spx_premium.py','main'),('phase_daily.py','main'),('phoenix_sleeve.py','main'),('ts_momentum_decile.py','main')],deps=['External scheduler','Python','Exchange calendar','Per-duty run receipts'])
f('variant_namespaces','Per-runner books, client IDs and writer scopes',
  'Shared wrappers instantiate Sleeve with separate names and CID prefixes; custom runners use their own hidden state, JSONL ledger and locks. Morning Dip and Legends share a broker symbol yet attribute owned fills separately.',
  'Give each book/run/order an explicit identity; maintain local ownership independently from net broker position and use stable single-writer resource locks.',
  ['U01','U02','U08','U15'],[('leader_d_sleeve.py',None,30,48),('momentum_sleeve.py','acquire_lock'),('bilbo_options.py','acquire_lock'),('phase_daily.py','acquire_lock'),('morning_dip.py','my_position_qty')],limits=['Morning Dip main does not acquire a process-wide file lock in the reviewed body; do not infer universal locking from other runners.'])
f('option_contract_identity','Explicit option contracts and idempotent order intents',
  'Bilbo uses OCC contract symbols, whole-contract quantities, buy_to_open/sell_to_close and deterministic hashed episode/exit CIDs; source restricts execution to paper.',
  'When options support is configured, validate contract identity, multiplier, whole quantity and position intent, and persist account/book-scoped order identity before submission.',
  ['U10','U13','U16'],[('bilbo_options.py','submit_option_order'),('bilbo_options.py','client_order_id'),('bilbo_options.py','_exit_cid'),('bilbo_options.py','main')], [('tests/test_bilbo_options_runner.py','test_entry_full_path_and_idempotent')],deps=['Alpaca option contract/quote/order CLI modules','Paper options entitlement'],limits=['Source strategy selection and premium allocation are excluded.'])
f('option_pending_lifecycle','Options pending entry and exit lifecycle',
  'Accepted entry becomes pending_entry; later broker fill confirms open. Accepted exit becomes pending_exit; the position moves to closed only after confirmation. Existing pending_exit is preserved during held-contract recovery.',
  'Represent accepted, working, partial, terminal, uncertain and confirmed states explicitly; submission acknowledgment must not create/remove held positions.',
  ['U12','U14','U15'],[('bilbo_options.py','_reconcile_pending_entries'),('bilbo_options.py','_reconcile_pending_exits'),('bilbo_options.py','run_entry'),('bilbo_options.py','run_exit')], [('tests/test_bilbo_options_runner.py','test_pending_entry_promoted_on_fill'),('tests/test_bilbo_options_runner.py','test_pending_exit_fill_confirmed_closes')],limits=['Option entry_premium_mid remains a sizing/reference quote, not a verified transaction cost basis.'])
f('variant_partial_fills','Terminal partial fills and residual exits',
  'Phase adopts terminal entry/reentry partials, reduces stop/market-exit remainder and retains protection retry. Confluence restages residual sell quantity after a dead partial exit; Momentum/Beatendown differ. Working partial fills in the copied equity pending state machines wait for terminal status.',
  'Import cumulative filled quantity, notional and fee deltas exactly once immediately on observation, retain residual intent and ensure coverage matches actual remaining holdings.',
  ['U14','U16','U19'],[('phase_daily.py','detect_fills'),('phase_daily.py','_settle_stop_fill'),('confluence_sleeve.py','reconcile_pending'),('momentum_sleeve.py','reconcile_pending'),('beatendown_sleeve.py','reconcile_pending')], [('tests/test_durability_20261007_b.py','test_E4_phase_daily_int_qty'),('tests/test_durability_20261007_b.py','test_E5_phase_daily_terminal_partial_fills')],limits=['Behavior is not uniform across runner families; source test presence is not proof every family handles a case.'])
f('option_reprice_escalation','Bounded exit repricing with manual-review retention',
  'Bilbo retains unfilled exits, obtains new two-sided quotes, attempts bounded cancel-replace repricing and raises a persistent manual-review flag when retry allowance is exhausted.',
  'Configure bounded cancel/replace retries, verify cancellation and quantity before replacement, retain unresolved holdings and generate actionable escalation without inventing a fill.',
  ['U14','U16','U21','U23'],[('bilbo_options.py','_reconcile_pending_exits')], [('tests/test_bilbo_options_runner.py','test_pending_exit_reprice_then_manual_review')],deps=['Order reads','Option quotes','Manual-review/notification channel'],limits=['Bilbo cancellation helpers do not verify terminal cancellation before replacement; improve this rather than copying the race. Log escalation alone does not establish delivered notification.'])
f('spread_submit_uncertainty','Multi-leg submission and uncertain acceptance recovery',
  'Actual SPX entry calls atomic mleg despite the older header describing separate entry legs. After submit error/bad shape it searches exact CID across open and closed orders; unreadable lists prevent concluding no order exists. Cancel failure retains pending_unverified for later verification.',
  'Prefer supported atomic multi-leg submission; journal acceptance uncertainty, lookup the same CID, and keep unknown orders in durable reconciliation rather than duplicating or declaring failure.',
  ['U10','U13','U15','U16'],[('spx_premium.py','submit_spread_mleg'),('spx_premium.py','_find_order_by_cid'),('spx_premium.py','run_entry'),('spx_premium.py','run_settle')],deps=['Alpaca mleg CLI','Broker options margin/entitlement'],limits=['No strategy, underlying, width or account floor is imported. Successful cancel request is not followed by cancellation confirmation in every entry branch.'])
f('settlement_provenance','Actual broker close versus explicit modeled settlement',
  'SPX records broker_close when both close legs are confirmed, otherwise retains incomplete/unverifiable legs. A broker-flat post-expiry path uses marked settled_proxy derived from market data.',
  'Distinguish verified execution P&L from modeled settlement, retain valuation source/date/cost assumptions, and keep incomplete or unknown legs visible for reconciliation.',
  ['U12','U14','U19','U21'],[('spx_premium.py','run_settle')], [('tests/test_regressions.py','test_R5_spx_settle_cancels_first')],limits=['Entry credit is derived from quote context rather than imported leg fill notional. The referenced regression is a source-pattern check, not a full broker-close behavior test.'])
f('bracket_parent_truth','Direct parent-order truth for generated bracket legs',
  'Morning Dip resolves the bracket parent by owned CID and GETs the parent because list responses can return legs=null. Broker-generated child IDs are related by parent identity, not by bare symbol/side.',
  'Fetch expanded parent/child order details when list views omit legs; retain parent-child identity and deduplicate the same fill visible in several reads.',
  ['U14','U15','U16'],[('morning_dip.py','_bracket_sell_leg_fills'),('morning_dip.py','_bracket_leg_ids'),('morning_dip.py','mdl_close_fills')], [('tests/test_morning_dip_ownership.py','test_bracket_leg_fill_closes'),('tests/test_morning_dip_ownership.py','test_no_double_count_across_lists')])
f('shared_symbol_ownership','Shared-symbol ownership and conflicting net exposure',
  'Morning Dip owns verified entry fills minus its parent legs/scoped closes. Legends attributes same-day prefix closing fills and clamps close/protection quantity to matching broker direction. Manual and another sleeve orders are excluded.',
  'Maintain book-level ownership and broker-level net separately; never cancel or close by symbol alone; detect conflicting/net-divergent ownership and stop conflicting mutation.',
  ['U02','U15','U16'],[('morning_dip.py','my_position_qty'),('morning_dip.py','cancel_my_sells'),('legends_ema.py','my_open_qty'),('legends_ema.py','_close_qty')], [('tests/test_morning_dip_ownership.py','test_two_trades_same_day_attribution'),('tests/test_morning_dip_ownership.py','test_manual_qqq_sell_untouched'),('tests/test_legends_ema.py','test_close_opposing_net_stands_down')],limits=['Attribution inference relies on bounded order history and can fail when old fills disappear or generated OCO legs are not expanded.'])
f('close_intent_checkpoint','Persisted explicit close intent and retry identity',
  'Morning Dip writes closing CID/quantity/reason/submitted=False before broker POST, marks receipt separately, and reuses its CID on failure. Working close is left intact; state persists until observed closure.',
  'Write ahead the close intent, make retry identity stable, refresh broker truth after cancellations and use confirmed remaining quantity for retries.',
  ['U08','U13','U14'],[('morning_dip.py','close_my_long'),('morning_dip.py','flatten'),('morning_dip.py','manage')], [('tests/test_morning_dip_ownership.py','test_close_submit_failure_persists_cid'),('tests/test_morning_dip_ownership.py','test_flatten_no_resubmit_working_close'),('tests/test_morning_dip_ownership.py','test_flatten_aborts_on_cancel_failure')])
f('oco_replace_verification','Verified OCO replacement and tracked protection gap',
  'Legends checks current protection, validates response and observes exact new OCO live before marking protected. Replacement waits until the old OCO disappears, stores refresh_pending/refresh_since and escalates stale gaps.',
  'Model protection replacement as cancel-requested, cancel-confirmed, replacement-submitted and live; expose gap age and avoid stacking coverage orders.',
  ['U14','U16','U21'],[('legends_ema.py','ensure_protection'),('legends_ema.py','replace_protection')], [('tests/test_legends_ema.py','test_replace_protection_keeps_old_on_cancel_fail'),('tests/test_legends_ema.py','test_replace_protection_swaps_on_clean_cancel'),('tests/test_legends_ema.py','test_main_refresh_gap_is_not_a_timeout')],limits=['Existing protection detection tests closing-side prefix orders rather than proving complete OCO leg quantity/price coverage; preserve this limitation.'])
f('stop_retry_identity','Missing-stop recovery with fresh replacement identity',
  'Phase/Phoenix preserve held positions when initial stop fails, flag missing protection for retry, reject malformed/terminal stop responses and rotate retry CID so idempotency does not return a dead old order.',
  'Protect only confirmed held quantity; retain held positions through protection failure; use fresh replacement identity linked to original intent and verify live covered quantity.',
  ['U15','U16','U21'],[('phase_daily.py','open_position_from_fill'),('phase_daily.py','ensure_stop_live'),('phoenix_sleeve.py','place_disaster_stop'),('phoenix_sleeve.py','_fresh_stop_cid'),('phoenix_sleeve.py','ensure_disaster_stop')], [('tests/test_phase_runner.py','test_initial_stop_failure_records_unprotected_position'),('tests/test_durability_20261007_b.py','test_E6_phoenix_disaster_stop_idempotency')],limits=['Phase/Phoenix existence checks do not comprehensively verify price/covered quantity; source stop levels are excluded.'])
f('protection_only_job','Separate lightweight reconciliation job',
  'Phase reconcile_pass and Phoenix reconcile body process fills, stale intents and stop liveness without bar fetching, signals or new entries, shortening dependence on heavier daily research scans.',
  'Schedule urgent reconcile/protection work independently from research/data scans and keep it serviceable during entry pause or research failures.',
  ['U03','U06','U15','U16','U18'],[('phase_daily.py','reconcile_pass'),('phoenix_sleeve.py','_reconcile_pass_body')],deps=['Independent reconcile cadence','Order/position broker reads'])
f('orphan_order_retries','Stop/exit races and parked orphan cancellation',
  'Phase verifies stop cancellation and parks orphan_stop for retry. Phoenix delays time exit if its stop cannot be verified gone, suppresses stop rearm while exit working and sweeps sibling stops after closure.',
  'Track surviving orders after close, honor fills from superseded orders and park unresolved cancellations with retry/escalation; never treat cancellation request as proof protection is gone.',
  ['U14','U15','U16','U21'],[('phase_daily.py','cancel_verified'),('phase_daily.py','sweep_orphan_stops'),('phase_daily.py','_clear_position_after_market_exit'),('phoenix_sleeve.py','_verified_cancel_stop'),('phoenix_sleeve.py','_on_stop_fill'),('phoenix_sleeve.py','_on_exit_fill')], [('tests/test_regressions.py','test_R6_phase_orphan_stop_sweep'),('tests/test_phase_runner.py','test_superseded_stop_fill_closes_position')])
f('intraday_end_state','Session-aware close and explicit pending flatten verification',
  'Legends queries session close, advances close on early-close day and uses a conservative early close when calendar unavailable. flat_pending verifies broker net and waits for working close before retry/clearing.',
  'Use exchange-calendar close and persisted pending-close end-state verification; report unknown calendar and missed end-state rather than claiming submission means flat.',
  ['U05','U07','U14','U21'],[('legends_ema.py','session_close_hm'),('legends_ema.py','verify_flatten_pending'),('legends_ema.py','main')], [('tests/test_legends_ema.py','test_flatten_verify_clears_on_flat_net'),('tests/test_legends_ema.py','test_flatten_verify_retries_on_nonzero_net')],limits=['Several other variant runners gate only weekdays/hardcoded RTH; do not imply one universal holiday/early-close implementation.'])
f('completed_data_boundaries','Completed versus provisional data boundaries',
  'Phase excludes today from completed daily bars; Phoenix separates include_forming data for detection from completed signals; Morning Dip waits until a three-minute candle is closed; hourly wrappers filter session grids and completed hours.',
  'Record bar start/end, session, adjustment and feed, and explicitly separate provisional observations from completed research data.',
  ['U05','U11','U26'],[('phase_daily.py','fetch_daily'),('phoenix_sleeve.py','_bars_request'),('morning_dip.py','closed_candles'),('blowoff_1h_sleeve.py','_drop_forming_1h'),('gate_1h_sleeve.py','mode_scan'),('phoenix_watch.py','main')], [('tests/test_phoenix_sleeve.py','test_forming_bar_never_in_signal_bars'),('tests/test_phoenix_sleeve.py','test_forming_bar_available_only_for_detection')],limits=['Different scripts use SIP/IEX and split/all/raw adjustment; this is explicit source heterogeneity, not a unified data-truth contract.'])
f('read_pipeline_failures','Parallel read isolation and bounded cache top-ups',
  'Phase/Phoenix fetch symbols concurrently and isolate per-symbol failures; shared hourly wrappers merge/deduplicate cache bars and retain bounded history; rank jobs wait if critical market inputs or excessive universe reads fail.',
  'Bound/paginate external reads, retain sufficient history and data lineage, isolate symbol failures and give missing critical dependency a visible non-success state.',
  ['U06','U11','U21'],[('phase_daily.py','fetch_daily_parallel'),('phoenix_sleeve.py','fetch_daily_parallel'),('blowoff_1h_sleeve.py','topup_1h'),('momentum_sleeve.py','mode_rank'),('confluence_sleeve.py','mode_rank')], [('tests/test_phase_runner.py','test_fetch_daily_parallel_isolates_failures')],deps=['Provider entitlements','Cache ownership','Fetch budgets'])
f('research_subprocess_boundary','Typed computation boundary and scorer failures',
  'Daily GBM and hourly rule wrappers submit JSON batches to Node scorers with timeouts and fail on nonzero exit, non-JSON or ok=false; these are deterministic computation workers, not general-purpose model agents.',
  'Execute research/computation tasks through explicit input/output schema, version and timeout/fault receipts; keep executable strategy modules absent until separately selected.',
  ['U06','U25','U26'],[('daily_cyan_gbm_sleeve.py','score_symbols'),('rule_1h_cyan_raw.py','score_1h')],deps=['Node','Scorer modules and model artifact dependencies'],limits=['No scorer weights, thresholds, signals or strategy model are imported.'])
f('plan_fill_clocks','Staged plan and actual execution clocks',
  'Rank/scan stores pending buys/sells, signal/entry anchors and exit dates. Hourly wrappers stamp modeled bar anchor after fill; MOC wrappers configure cls while daily/weekly variants use market/day, with documented execution approximation.',
  'Preserve observation, plan, requested execution, accepted and actual fill times/prices separately; show deviation from modeled research assumptions.',
  ['U07','U12','U19','U26'],[('blowoff_1h_sleeve.py','stamp_entry_bars'),('gate_1h_sleeve.py','stamp_entry_bars'),('rule_1w_cyan_mom_adx.py',None,36,45),('leader_d_sleeve.py','mode_rank'),('snapback_sleeve.py','mode_rank')], [('tests/test_regressions.py','test_R21_moc_sleeves'),('tests/test_durability_20261007.py','test_D12_blowoff_1h_signal_bars_stamp')],limits=['Neither staged intent nor modeled bar anchor proves actual close/open fill.'])
f('variant_capacity_checks','Pending commitments and projected global exposure',
  'Confluence/Beatendown capacity subtract pending entries; custom TS fill uses projected desk exposure plus accepted intra-pass notional and fail-closes if exposure module unavailable. Entry risk/context checks remain separate from existing exits.',
  'Use current broker/readiness truth and atomic pending reservations across books; separate capacity, hard limits and advisory risk observations, with operator-configured policy.',
  ['U10','U17','U18'],[('confluence_sleeve.py','mode_rank'),('beatendown_sleeve.py','mode_rank'),('ts_momentum_decile.py','mode_fill'),('momentum_sleeve.py','mode_fill')],limits=['Source risk constants and allocations excluded. Separate read/check followed by submit is not an atomic reservation across processes.'])
f('pause_semantics','Distinguish entry halt from research-only pause',
  'Phoenix entries_paused blocks entries while exits/protection continue; Morning Dip TRADING_ENABLED=False dispatches a signal-only pass that deliberately omits protective management unless --force. Both states are explicit in code/tests.',
  'Make entry halt, servicing-only, research-only and shutdown distinct controls; existing lifecycle servicing must remain active unless operator intentionally chooses a different mode.',
  ['U18','U21','U30'],[('phoenix_sleeve.py','_maybe_disaster_pause'),('phoenix_sleeve.py','maybe_enter'),('phoenix_sleeve.py','maybe_exit'),('morning_dip.py','_paused_pass'),('morning_dip.py','main')], [('tests/test_phoenix_sleeve.py','test_paused_exits_continue'),('tests/test_morning_dip_pause_20261002.py','test_paused_pass_never_manages_stale_state'),('tests/test_morning_dip_pause_20261002.py','test_main_force_bypasses_guard')],limits=['Historical approval text is evidence only; it does not impose a new permission workflow on the current user.'])
f('variant_durability','Atomic snapshots and honest corrupt-state recovery',
  'Options/Phase/Phoenix/intraday files flush/fsync a temporary JSON snapshot and rotate backups; several preserve corrupt bytes and flag recovery. Some start blank rather than reconstructing complete books; copied momentum-family writes lack the stronger fsync/backup behavior.',
  'Use durable transactional execution state, explicit new-book initialization and last-valid recovery; preserve corruption and block new commitments until holdings/intent ownership is reconstructed.',
  ['U08','U09','U15'],[('bilbo_options.py','load_state'),('bilbo_options.py','save_state'),('phase_daily.py','load_state'),('phase_daily.py','save_state'),('phoenix_sleeve.py','load_state'),('momentum_sleeve.py','save_state'),('spx_premium.py','load_state')], [('tests/test_phase_runner.py','test_atomic_write_roundtrip'),('tests/test_phase_runner.py','test_corrupt_state_preserved_and_flagged')],limits=['Per-runner JSONL logging is not universally fsynced or hash-chained. Backup existence alone does not prove automatic complete recovery.'])
f('variant_dryrun_scope','Dry-run side-effect boundaries are explicit per duty',
  'Bilbo/SPX/Phase/Phoenix logger prints only in DRY_RUN and state save skips. Shared wrapper dry-run often logs/locks and may fetch; TS rank always saves shared cache via fetch_bars despite dry_run. Source tests cover selected paths only.',
  'Give simulated/replay/dry-run jobs isolated stores and declared permitted reads; verify no broker mutations or production execution/account/message writes in dry-run.',
  ['U08','U30'],[('bilbo_options.py','log'),('phase_daily.py','save_state'),('ts_momentum_decile.py','fetch_bars'),('ts_momentum_decile.py','mode_rank'),('snapback_sleeve.py','main')], [('tests/test_bilbo_options_runner.py','test_exit_box_low_dryrun'),('tests/test_durability_20261007_b.py','test_E20_log_print_only_in_dry_run')],limits=['A --dry-run flag is not proof of whole-program purity across all variants.'])
f('research_watch_dedup','Separate nontrading monitors and persisted alert state',
  'Focus/Top10 watches fetch fresh data, calculate deterministic output and compare JSON-stable swing/regime state to suppress unchanged prints. Phoenix watch appends deduplicated symbol/date forward observations to a separate monitoring file and never submits orders.',
  'Preserve research-only observations independently from execution; use stable dedup/cursors, show data failures, and separate alert production from delivery receipts.',
  ['U09','U23','U25','U26'],[('focus_watch.py','state_key'),('focus_watch.py','main'),('top10_watch.py','main'),('phoenix_watch.py','load_logged'),('phoenix_watch.py','main')], [('tests/test_focus_watch.py','test_state_key_survives_json_round_trip'),('tests/test_focus_watch.py','test_state_key_regime_compared_close_ignored')],limits=['These monitoring scripts do not implement general autonomous reasoning, durable notification delivery or peer inbox processing.'])
f('ondemand_research_tools','On-demand deterministic analysis and chart artifacts',
  'Holistic analyzer fetches paginated market data, produces technical/chart/context and fresh-computation output, while composite/dip scripts return per-symbol structured component evidence and source-state context without order calls.',
  'Expose configured read-only research tools with source/timestamp/provenance, structured results and preserved chart artifacts; identify heuristic scoring versus actual model inference.',
  ['U11','U25','U26','U27'],[('holistic_analyzer.py','fetch_bars'),('holistic_analyzer.py','make_chart'),('holistic_analyzer.py','analyze'),('composite_score.py','score_symbol'),('dip_score.py','main')],deps=['Alpaca market data','NumPy/Pandas','Optional Matplotlib','Versioned computation modules'],limits=['Holistic header mentions news search and --chart-only, but actual analyze does not fetch news and main registers no --chart-only option. Numeric scoring methods excluded from transfer.'])
f('review_trigger_boundaries','Review triggers and frozen executable settings',
  'Phoenix records completed-trade metadata and emits deduplicated review-due events rather than automatically altering its module risk constants; tests pin exclusion from the separate calibration configuration.',
  'Produce evidence-linked review proposals and persist sample/readiness; keep research recommendations distinct from active configuration, version any later changes and retain rollback history.',
  ['U17','U24','U26'],[('phoenix_sleeve.py','_close_position'),('phoenix_sleeve.py','_maybe_risk_review'),('phoenix_sleeve.py','_maybe_cohold_review')], [('tests/test_phoenix_decisions.py','test_phoenix_runner_never_reads_calibrator_config'),('tests/test_phoenix_sleeve.py','test_no_review_before_25_and_no_duplicate')],limits=['Source numeric thresholds, universe-specific rules and approval requirements are historical evidence only, not new desk settings. Source max_adverse_excursion field is the worst completed trade return, not true intratrade MAE.'])
f('periodic_job_receipts','Period gates and durable completion meaning',
  'TS rebalance gates first exchange trading day and last_rebalance_month; rank and fill are separate stages. Source main writes month complete after mode_fill returns even when individual orders remain failed/pending.',
  'Persist scheduled period/slot attempts and stage-specific success receipts; incomplete or failed effects remain retryable rather than equating function return to completed rebalance.',
  ['U05','U06','U07'],[('ts_momentum_decile.py','should_rebalance'),('ts_momentum_decile.py','main'),('ts_momentum_decile.py','mode_fill')],limits=['No strategy decile/ranking, risk sizing or sector constants imported.'])
f('strict_unknown_reads','Unknown reads remain distinct from empty/flat',
  'Morning Dip rejects malformed non-list orders/positions as None. Phase critical stale-intent cleanup requires both open and closed book reads; options spread lookup returns a dedicated unreadable sentinel.',
  'Validate broker response shapes and use typed unknown/not-configured/empty outcomes; never clear intent, book or protection merely because a dependency read failed.',
  ['U10','U15','U21'],[('morning_dip.py','open_orders'),('morning_dip.py','positions'),('phase_daily.py','sweep_stale_pending'),('spx_premium.py','_find_order_by_cid')], [('tests/test_durability_20261007_b.py','test_E19_morning_dip_malformed_cli_response_returns_none'),('tests/test_phase_runner.py','test_sweep_keeps_live_pending')],limits=['Other lenient source helper paths do return [] on failure; strict behavior is not universal.'])
f('recovered_position_provenance','Recovered holdings preserve uncertain basis and ownership',
  'Phoenix reconstructs aged-out pending entries from broker quantity and an explicitly approximate reference price; today-scoped Legends/Morning Dip recovery searches owned fill identity. Phoenix broker-flat exit recovery substitutes entry price and orphan-short cleanup assumes broker net ownership.',
  'Adopt only with explicit account/order ownership evidence; retain observed cost and provenance, keep unknown basis/strategy/protection unknown and prevent invented realized P&L.',
  ['U12','U15','U19'],[('phoenix_sleeve.py','_adopt_recovered_entry'),('phoenix_sleeve.py','_reconcile_stuck_submits'),('phoenix_sleeve.py','_reconcile_orphan_fill'),('legends_ema.py','recover_entry'),('morning_dip.py','recover_armed')], [('tests/test_morning_dip_ownership.py','test_recover_armed_ignores_completed_trade'),('tests/test_morning_dip_ownership.py','test_recover_armed_unknown_is_none')],limits=['Synthetic zero-return broker-flat recovery and automatic net-short ownership assumptions are explicit source limitations to avoid.'])

# Human body-review inventory: exact named operational bodies, not a claim of
# complete strategy-math review. AST/hash verification is a separate check.
review = {
 'momentum_sleeve.py':['load_state','save_state','acquire_lock','get_order','reconcile_pending','fetch_daily','mode_rank','fresh_quote_ok','mode_fill','main'],
 'confluence_sleeve.py':['load_state','save_state','acquire_lock','get_order','reconcile_pending','fetch_daily','mode_rank','fresh_quote_ok','mode_fill','main'],
 'beatendown_sleeve.py':['load_state','save_state','acquire_lock','get_order','reconcile_pending','fetch_daily','mode_rank','fresh_quote_ok','mode_fill','main'],
 'bilbo_options.py':['log','load_state','save_state','acquire_lock','_run_cli','fetch_5min','option_chain','option_quotes','gate3_spread_ok','submit_option_order','_open_exit_order','_reconcile_pending_entries','client_order_id','_prune_submitted_orders','run_entry','_position_record','_exit_cid','_reconcile_pending_exits','run_exit','main'],
 'spx_premium.py':['load_state','save_state','acquire_lock','submit_spread_mleg','_find_order_by_cid','_filled_qty','run_entry','run_settle','main'],
 'legends_ema.py':['load_state','save_state','fetch_1min','bars_15m','open_orders','closed_orders','signed_position_qty','my_open_qty','cancel_orders','verify_flatten_pending','_close_qty','close_my_qty','wait_for_fill','submit_oco','my_protection_orders','ensure_protection','replace_protection','recover_entry','session_close_hm','main'],
 'morning_dip.py':['load_state','save_state','fetch_3min','closed_candles','open_orders','closed_orders','positions','my_position_qty','_bracket_sell_leg_fills','mdl_close_fills','close_order_state','cancel_all_mdl','_bracket_leg_ids','cancel_my_sells','close_my_long','flatten','recover_armed','_paused_pass','main','manage'],
 'phase_daily.py':['acquire_lock','load_state','save_state','load_earnings','get_equity','fetch_daily','fetch_daily_parallel','fetch_5min_today','open_orders','closed_orders_strict','submit','cancel_order','cancel_verified','ensure_stop_live','sweep_stale_pending','cancel_resting','manage_k5_daily','place_stop','open_position_from_fill','open_position_from_reentry','_settle_stop_fill','detect_fills','_clear_position_after_market_exit','sweep_orphan_stops','manage_position_daily','maybe_nc_fire','earnings_flatten_pass','earnings_reentry_pass','reconcile_episode','daily_pass','load_bars_cache','intraday_pass','fire_scr3_exits','retry_armed_trail_breaches','reconcile_pass','main'],
 'phoenix_sleeve.py':['load_state','save_state','_maybe_risk_review','_maybe_soxl_review','_maybe_cohold_review','_maybe_disaster_pause','_bars_request','fetch_daily_parallel','load_earnings','get_equity','submit_moc','place_disaster_stop','_fresh_stop_cid','cancel_verified','_broker_qty','_reconcile_orphan_fill','_reconcile_stuck_submits','detect_fills','_adopt_recovered_entry','_on_entry_fill','_close_position','_on_stop_fill','_on_exit_fill','_on_order_dead','ensure_disaster_stop','maybe_enter','_verified_cancel_stop','maybe_exit','daily_pass','_daily_pass_body','reconcile_pass','_reconcile_pass_body','main'],
 'ts_momentum_decile.py':['apply_sector_cap','load_universe','fetch_bars','mode_rank','mode_fill','should_rebalance','main'],
 'blowoff_1h_sleeve.py':['topup_1h','_drop_forming_1h','mode_scan','stamp_entry_bars','main'],
 'gate_1h_sleeve.py':['topup_1h','mode_scan','stamp_entry_bars','main'],
 'rule_1h_cyan_raw.py':['load_1h_cache','topup_1h_bars','score_1h','mode_rank','main'],
 'focus_watch.py':'all','top10_watch.py':'all','phoenix_watch.py':'all','holistic_analyzer.py':'all',
 'composite_score.py':['score_symbol','main'],'dip_score.py':['fetch_bars','main'],
 'rule_1d_green_tom.py':'all','leader_d_sleeve.py':'all','daily_cyan_gbm_sleeve.py':'all',
 'blowoff_d_sleeve.py':['mode_rank','main'],'leader_sc_sleeve.py':['mode_rank','main'],
 'rule_1w_cyan_mom_adx.py':['mode_rank','main'],'rule_1w_swing_beta_wt.py':['mode_rank','main'],
 'rule_1d_cyan_smallcap.py':['mode_rank','main'],'snapback_sleeve.py':['mode_rank','main'],
 'bilbo_options_signals.py':'pure strategy-only helper; header, function map and I/O absence classified; formulas intentionally excluded',
 'phase_signals.py':'pure strategy-only helper; header, function map and I/O absence classified; formulas intentionally excluded',
}
inventory=[]
for file,names in review.items():
    funcs=[n for n in tree(file).body if isinstance(n,ast.FunctionDef)]
    if names=='all': names=[n.name for n in funcs]
    e=ev(file)
    e['read_scope']=names
    e['reviewed_function_ranges']=[{'name':n.name,'start':n.lineno,'end':n.end_lineno} for n in funcs if isinstance(names,list) and n.name in names]
    e['scope_note']='Human-read operational bodies; signal/ranking mathematics not transferred. Common copied lifecycle functions compared by full normalized AST diff; meaningful variants read.'
    inventory.append(e)
test_inventory=[]
test_names={
 'tests/test_bilbo_options_runner.py':lambda n:not any(x in n.name for x in ['ema21_gate','oversize_one','spread_gate']),
 'tests/test_morning_dip_ownership.py':lambda n:True,
 'tests/test_morning_dip_pause_20261002.py':lambda n:'arm_plan_matches' not in n.name,
 'tests/test_legends_ema.py':lambda n:not any(x in n.name for x in ['ema_warmed']),
 'tests/test_phase_runner.py':lambda n:not any(x in n.name for x in ['k5_dies','k5_arms','k5_stands','nc_stands','nc_fires','size_qty','k5_no_rearm','trail_ratchets']),
 'tests/test_phoenix_sleeve.py':lambda n:n.lineno>=315,
 'tests/test_phoenix_decisions.py':lambda n:True,
 'tests/test_phase_specfix_20261002.py':lambda n:n.name in ['test_scr3_fire_sells_and_clears','test_reentry_uses_recomputed_trail','test_reentry_fires_when_above_recomputed_trail'],
 'tests/test_focus_watch.py':lambda n:True,
 'tests/test_extension_shadow.py':lambda n:True,
}
for file,predicate in test_names.items():
    tests=[n for n in ast.walk(tree(file)) if isinstance(n,ast.FunctionDef) and n.name.startswith('test') and predicate(n)]
    test_inventory.append({'source':ev(file,classification='static_test_source'),'read_test_bodies':[{'name':n.name,'start':n.lineno,'end':n.end_lineno} for n in tests],'execution_status':'not executed; static test intent only'})
for file in ['tests/test_durability_20261007.py','tests/test_durability_20261007_b.py','tests/test_regressions.py']:
    tokens=['bilbo','spx','legends','lema','morning','mdp','phase','phoenix','phx','blowoff','gate_1h','confluence','momentum','beatendown','snapback','leader','rule_1','cyan']
    tests=[n for n in ast.walk(tree(file)) if isinstance(n,ast.FunctionDef) and n.name.startswith('test') and any(x in ast.unparse(n).lower() for x in tokens)]
    if '_b.py' in file: tests=[n for n in tests if not any(x in n.name for x in ['snapshot','bugcheck','age_min'])]
    test_inventory.append({'source':ev(file,classification='static_test_source'),'read_test_bodies':[{'name':n.name,'start':n.lineno,'end':n.end_lineno} for n in tests],'execution_status':'not executed; static test intent only','limits':'Mixed suites; only sleeve-relevant bodies read by this reviewer. Many tests assert source text rather than exercising full operational behavior.'})

doc={'title':'Recovered Femto sleeve operational contracts','repository':'Midna','commit':COMMIT,
     'source_root':str(ROOT/PREFIX),'scope':'All 30 top-level variant/helper Python files classified; operational bodies and selected related test bodies read. Strategy-only formulas excluded by user scope. Shared engine/control/status/publisher bodies belong companion reviews.',
     'review_method':'Read-only original source and AST-unparsed complete named bodies; copied lifecycle bodies compared by normalized AST; exact Git blob identity and pinned line references validated. No module imports, broker calls, source modifications or historical test execution.',
     'features':features,'reviewed_file_inventory':inventory,'test_source_inventory':test_inventory,
     'limitations':['Pinned October 8 historical source establishes implementation, not deployed process health or live broker access.','External scheduler/model-agent session definitions are not embedded in these runners.','No strategy formulas, source capital/holdings/risk defaults or historical approval rules are copied.','Test source inspection records intent and scope; tests were not run and some string assertions/fixtures are stale.','This reviewer does not claim personal full-body coverage of all 136 executable files; shared core, operations, scorer dependencies and source coverage are tracked in companions.'],
     'counts':{'features':len(features),'top_level_files':len(inventory),'related_test_files':len(test_inventory),'reviewed_test_bodies':sum(len(x['read_test_bodies']) for x in test_inventory),'source_citations':sum(len(x['source_evidence'])+len(x['test_source_evidence']) for x in features)}}
(D/'FEATURES_FEMTO_SLEEVES.json').write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(doc['counts']))
