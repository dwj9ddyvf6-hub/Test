import json, pathlib, re, collections

D=pathlib.Path('/workspace/agentic-desk/docs')
INPUTS={'Femto/Midna':'FEATURES_FEMTO.json','Cursor':'FEATURES_CURSOR.json','GrokBot':'FEATURES_GROKBOT.json'}
raw={name:json.loads((D/file).read_text()) for name,file in INPUTS.items()}
rows=[]
def evidence_class(e):
    if e.get('evidence_class'): return e['evidence_class']
    if e.get('classification'): return e['classification']
    p=e.get('path','')
    if p.endswith('INBOX.md'): return 'reported_operation_or_channel_protocol'
    if '__memory' in p or '__people/' in p: return 'archived_memory_or_relationship'
    if 'desk-terminal-feed' in p: return 'published_snapshot'
    return 'implemented_source'
def norm_evidence(e):
    lines=e.get('lines') or [e.get('line',e.get('line_start')),e.get('end_line',e.get('line_end'))]
    return {'repo':e.get('repo',e.get('repository','')).split('/')[-1], 'commit':e.get('commit',e.get('commit_sha')),
            'path':e.get('path'),'line':lines[0],'end_line':lines[-1],
            'url':e.get('url'),'evidence_class':evidence_class(e),
            'sha256':e.get('sha256'),'git_blob_sha':e.get('git_blob_sha',e.get('blob_sha'))}
for name,x in raw.items():
    for f in x['features']:
        label=f.get('feature',f.get('label',f['id'].replace('-',' ').replace('_',' ')))
        behavior=f.get('source_behavior',f.get('implemented_behavior',''))
        requirement=f.get('new_desk_requirement',f.get('implementable_requirement'))
        if not requirement: requirement='Provide '+label.lower()+' with the documented source behavior, while keeping strategy modules and portfolio defaults empty.'
        ev=[norm_evidence(e) for e in f.get('sources',f.get('evidence',[]))]
        rows.append({'id':name.lower().replace('/','_')+'.'+f['id'],'reference':name,'source_feature_id':f['id'],
                     'feature':label,'source_behavior':behavior,'implementation_requirement':requirement,
                     'source_status':f.get('current_status','evidence class is recorded on each source citation'),
                     'target_status':'planned; new-desk implementation not verified by this source inventory',
                     'dependencies':f.get('dependencies_or_configuration',f.get('configuration_dependencies',[])),
                     'limitations':f.get('limits_and_status',f.get('limits',[])),
                     'evidence':ev,'strategy_specific':False,
                     'additional_parity_groups':f.get('parity_groups',[]),
                     'source_artifact':f.get('source_artifact',INPUTS[name]),
                     'provenance_scope':f.get('provenance_scope','See source artifact for review depth and implementation/report distinction')})

# Each canonical requirement maps to exact atomic records, preserving source-specific differences.
groups=[]
def g(id,name,requirement,refs,config,acceptance):
    groups.append({'id':id,'feature':name,'requirement':requirement,'source_features':refs,
                   'configuration_dependencies':config,'acceptance_criteria':acceptance,
                   'target_status':'planned; verify against new-desk code and meaningful tests before marking implemented'})
F=lambda id:'femto_midna.'+id
C=lambda id:'cursor.cursor.'+id
G=lambda id:'grokbot.'+id
g('U01','Desk, account and agent identities','Maintain distinct desk/book/account and named agent-role identities with scoped ownership and explicit execution mode.',
  [F('desk-and-agent-identity'),C('book_identity'),G('G01')],['Desk/account registry','Agent roles and provider selection'],['No role title is represented as a strategy. External session claims are labelled.'])
g('U02','Independent books and authority','Never blend separate books, cash, positions, ledgers, operator authority or reference-desk policies.',
  [F('independent-books-and-authority'),C('independent_books'),G('G02')],['Book/account namespaces'],['Two books with same symbol remain independently attributable; no historical capital or holdings are seeded.'])
g('U03','Unattended execution and host recovery','Run useful work independently of the browser/model session, with durable scheduled tasks and restart-safe service ownership.',
  [F('external-scheduler-disposable-worker'),F('cadence-by-worker-duty'),C('unattended_loop'),C('external_operator'),G('G35')],['Service/scheduler runtime','Task cadence/session policies'],['Closing browser does not stop jobs. Worker or host restart resumes due tasks using durable state.'])
g('U04','Child supervision and heartbeats','Track process/task identity, heartbeat, last useful completion, failure, restart/backoff and stalled-state reason.',
  [C('child_supervision'),C('heartbeat'),G('G35')],['Supervisor policy'],['Heartbeat from an old PID cannot make a replacement healthy; stale alive and missing/dead states remain distinct.'])
g('U05','Session clock and operational cadences','Use exchange timezone, DST, holidays and early closes; validate current submission window and worker-specific duties.',
  [C('session_calendar'),F('cadence-by-worker-duty'),G('G08'),G('G34')],['Market calendar','Configured duties/valid windows'],['Holiday and early-close schedules are correct; stale queued work is never sent outside its window.'])
g('U06','Durable attempts and success receipts','Persist slot/task attempts; mark success only after useful completion/ledger receipt, and retry unfinished stages with bounds.',
  [C('slot_receipts'),C('missed_slot_recovery'),G('G33'),G('G34')],['Task queue/lease','Retry policy'],['Lock-held or exit-zero-without-receipt work is not counted complete; retry does not duplicate completed side effects.'])
g('U07','Critical-window end-state verification','Verify actual intended end state after a time-critical window and raise actionable missed/failed status.',
  [F('critical-window-end-state-verification'),C('preopen_check'),G('G18')],['Verifier cadence and expected-state contract'],['A submitted order is not treated as proof of desired holdings; a missed pass is visible after its window.'])
g('U08','Single-writer atomic persistence and recovery','Use ownership locks/leases, durable snapshots, explicit initialization and preserved unreadable prior state.',
  [C('single_writer'),C('staged_recovery'),C('unreadable_state'),F('idempotent-pass-and-state'),G('G05')],['Durable database/storage','Writer lease'],['Restart after partial write recovers last valid state; corruption never silently resets an account.'])
g('U09','Ordered immutable ledger and observer cursors','Preserve append-only ordered events with integrity checks and durable unread cursors rather than recent-time slices.',
  [C('ledger_chain'),F('durable-ledger-observer-cursors'),G('G04')],['Ledger','Per-agent/observer cursors'],['Missed polls retain all unseen events; repeated reads do not reissue events/orders/messages.'])
g('U10','External paper broker and account readiness','Implement explicit paper broker adapter, actual connection/account status and validated paper account identity.',
  [F('account-and-position-truth'),G('G03'),G('G25')],['Paper broker provider/account','Private credential references'],['Missing configuration gives honest not-configured status; accepted receipt remains distinct from fill. Cursor reference has no broker.'])
g('U11','Market-data providers, freshness and provenance','Fetch configured data with provider fallback, timestamp/session/freshness checks and explicit missing/stale/crossed quote states.',
  [C('quote_providers'),C('quote_validation'),G('G03'),G('G13')],['Market-data adapters/entitlements','Freshness policy'],['Every mark identifies source/time/mode; missing data never becomes a synthetic live price.'])
g('U12','Paper-fill and transaction-cost provenance','Distinguish local simulated fills, observed quote assumptions and broker-confirmed fills; preserve fees/cost basis.',
  [C('paper_fill_provenance'),F('accounting-baseline-and-attribution'),G('G10')],['Execution adapter','Cost/fee policy'],['Local simulation cannot be labelled broker filled; execution reference is separate from actual fill.'])
g('U13','Intent-before-submit and ambiguous-order recovery','Persist client-ID intent before external submission, lookup uncertainty by that identity, and journal receipt before retry.',
  [F('idempotent-pass-and-state'),G('G05'),G('G24'),G('G26')],['Broker idempotency support','Durable intents/receipts'],['Crash after broker acceptance cannot create duplicate order or unmanaged owned fill.'])
g('U14','Cumulative partial fills and cancellation','Import fill quantity/notional/fee deltas exactly once and represent cancellation as requested/pending/confirmed.',
  [G('G27'),F('protection-and-ownership')],['Broker order poll/stream','Execution import cursors'],['Changing partial-fill prices produces exact realized proceeds; duplicate receipts do not double-book; cancel request never implies cancellation.'])
g('U15','Reconcile, mismatch controls and adoption','Compare complete broker positions/orders/fills with local ownership; surface phantoms, unknowns and quantity mismatches; adopt identifiable orders without invented metadata.',
  [F('broker-reconciliation'),F('protection-and-ownership'),G('G28'),G('G29')],['Broker truth reads','Ownership/adoption policy'],['Unknown strategy/ATR/protection remains unknown; source quantity/cost/IDs are retained; mismatches block conflicting activity.'])
g('U16','Existing-order lifecycle and protection','Maintain existing order/protection state, covered quantity and cancellation/replacement confirmations while respecting supported broker semantics.',
  [F('protection-and-ownership'),G('G30'),G('G07')],['Explicit protection policy','Broker supported order types'],['No overselling or duplicate protection; coverage is observable; independent orders are not mislabelled atomic OCO.'])
g('U17','Risk policy versions and reservations','Use configurable account/book/symbol budgets with pending-order notional reservations and exact broker buying-power provenance.',
  [F('risk-policy-versioning'),G('G06'),G('G32')],['Operator-configured risk policy','Current broker equity/cash/buying power'],['Hard limit versus suggestion is explicit/versioned; no old150%,10%,25% or source lane constants imported.'])
g('U18','Entry pause, activation, resume and rollback','Separate new-entry pause from existing servicing, account activation, shutdown/cancel/flatten and safe rollback.',
  [C('halt_contract'),G('G31'),G('G36')],['Persistent operator control state','Activation policy'],['Paused entries stay paused while reconciliation/exits continue; separate book is not disturbed by another book rollback.'])
g('U19','Account/P&L baselines and attribution','Show realized/unrealized P&L, actual trade basis, fees and account baseline adjustments with auditable attribution.',
  [F('accounting-baseline-and-attribution'),G('G09'),G('G11'),G('G14')],['Broker equity/fills','Book baseline/snapshot rules'],['Daily snapshot is unique per book/date; open mark gains are not reported as closed-trade wins.'])
g('U20','Performance, risk and position observations','Expose equity, exposures, drawdown, completed-trade sample counts, lifecycle/excursion observations and configurable benchmark comparisons.',
  [C('risk_projection'),C('position_observations'),G('G15'),G('G16')],['Benchmark data (QQQ and S&P500/SPY for new-desk goal)','Aligned dates/coverage'],['Benchmark comparisons share time/base; coverage/missing history is visible; source small-cap beta grouping is not imported.'])
g('U21','Health/readiness and operator diagnostics','Combine useful-work receipts, dependency readiness, data age, broker/reconcile status and missed slots into reasoned operator status.',
  [F('health-and-readiness'),C('preopen_check'),G('G18'),G('G19')],['Health contracts','Incident event log'],['Healthy cannot conceal incomplete pass, stale feed or unresolved ownership; PENDING differs from failure.'])
g('U22','Readonly public projections and reliable UI polls','Separate readonly/public presentation from internal order controls; preserve cent precision and prevent an older response replacing newer data.',
  [F('public-feed-versus-internal-workspace'),C('public_projection'),C('poll_chronology'),G('G12'),G('G13')],['Projection API/static publisher','Source timestamps/request sequence'],['Public projection does not execute orders; late poll cannot overwrite newer account state.'])
g('U23','Notification cursors and optional delivery','Provide persistent event-based alert delivery, explicit delivery receipts/dedup and optional configured browser push/external posts with media lifecycle.',
  [C('webpush'),C('typefully'),C('historical_replay'),G('G18')],['Opt-in destination/provider config','Delivery cursor/retry policy'],['Historical events are not replay-posted accidentally; log-only alert is not labelled successfully delivered notification.'])
g('U24','Structured journals, nightly review and lessons','Schedule all-book operational reviews, preserve failures/losses/context/evidence and maintain durable learning artifacts distinct from executable settings.',
  [F('all-book-nightly-review'),F('postmortem-and-learning'),C('daily_journal'),C('memory'),G('G20')],['Journal/review agent tasks','Evidence/artifact store'],['Every book is represented; lessons link actual executions; reasoning does not silently mutate risk or strategy.'])
g('U25','Research/agent tool execution with context separation','Support actual configured model tasks and permitted market/research tools, durable handoffs/artifacts and accountable role outputs; keep research separate from execution.',
  [F('research-as-preserved-artifact'),C('external_operator'),C('role_log'),C('context_separation'),G('G01'),G('G17'),G('G20')],['Configured model provider','Read/research tool registry','Durable tasks/checkpoints'],['An agent shows real model/tool receipts or clear missing configuration; deterministic role logs are not represented as autonomous reasoning; empty strategies remains enforced.'])
g('U26','Evidence-backed research revisions and rollback','Version study hypotheses/artifacts and proposed revisions; evaluate future strategy research against configured benchmarks before any explicit activation.',
  [F('calibration-gates-and-rollback'),F('research-as-preserved-artifact'),C('memory'),G('G06'),G('G17')],['Research registry','Data versions','QQQ/S&P500 benchmark contract'],['Current desk contains no imported strategies; source historical approval thresholds are not imposed as new session rules.'])
g('U27','Queryable evidence and rebuildable analytics','Provide query/search over tasks, decisions, fills, account events, journals and research reports; analytical projections remain rebuildable.',
  [G('G21'),F('durable-ledger-observer-cursors'),C('daily_journal')],['Database/full-text artifact index'],['Analytics cannot overwrite execution truth or block urgent work indefinitely.'])
g('U28','Three-peer inbox and message lifecycle','Persist incoming/outgoing peer messages with author, time, topic, evidence, urgency and unread/delivery cursor; safe appends preserve independent desk authority.',
  [F('peer-inbox-workflow'),C('shared_inbox'),G('G22')],['Local inbox','Optional external repository/connector config'],['Shared collaboration does not merge books or turn peer findings into commands; appends are idempotent and preserve history.'])
g('U29','Backup/channel preservation','Keep backup restore/sync additive for collaboration history and protect ledger, journal, intent and message stores from bulk replacement.',
  [C('backup_channel'),G('G23')],['Backup policy/store ownership','Protected artifact paths'],['Missing remote-only inbox entries cannot be staged as deletions; restore retains execution/message continuity.'])
g('U30','Isolated staging/simulation and operator tools','Provide separate dry-run/replay namespaces and explicit verification/status/reconcile/pause/resume/activation tools.',
  [G('G37'),G('G36'),G('G19')],['Run-mode namespace','Command/tool contracts'],['Simulation cannot contaminate broker ledger; side-effecting connectivity tests are identified as such.'])

for row in rows:
    for group_id in row['additional_parity_groups']:
        group=next(g for g in groups if g['id']==group_id)
        if row['id'] not in group['source_features']:
            group['source_features'].append(row['id'])

by_id={r['id']:r for r in rows}
assert len(by_id)==len(rows)
used=[]
for group in groups:
    for rid in group['source_features']:
        assert rid in by_id,rid
        used.append(rid)
    group['reference_membership']=sorted({by_id[rid]['reference'] for rid in group['source_features']})
assert set(by_id)<=set(used),set(by_id)-set(used)
for row in rows:
    assert row['evidence'],row['id']
    for e in row['evidence']:
        assert re.fullmatch('[0-9a-f]{40}',e['commit'] or ''),e
        assert e['path'] and e['line'] and e['end_line']>=e['line'],e
        assert '/blob/'+e['commit']+'/' in e['url'],e

doc={'schema_version':3,'status':'corrected reference inventory with recovered executable Femto core; replaces earlier absent-source interpretation and superseded broad desk matrix',
     'selected_reference_desks':['Femto/Midna','Cursor','GrokBot'],
     'purpose':'Actionable operational feature union for an autonomous paper research desk with an empty strategy registry.',
     'latest_design_goal':'Autonomous market research with evidence/artifacts and future edge evaluation against QQQ and S&P500 benchmarks. No existing strategies, allocations, holdings or source risk constants are imported.',
     'reference_identification':{
        'Femto/Midna':{'source_roots':raw['Femto/Midna']['source_roots'],'identity':raw['Femto/Midna']['identity'],'runtime_status':raw['Femto/Midna']['runtime_classification'],'review_coverage':raw['Femto/Midna']['coverage']},
        'Cursor':raw['Cursor']['reference_identity'],
        'GrokBot':raw['GrokBot']['identity']},
     'source_artifacts':INPUTS,
     'operational_union':groups,'features':rows,
     'evidence_rules':['Source implementation, published snapshots, documented protocols and reported external agent/deployment behavior stay distinct.','Reference capability is not a claim that the new desk implements it. All target statuses remain planned until matched to new code and appropriate verification.','Historical strategy/risk/permission statements are evidence only; current user scope and authorized configuration control the new desk.','Static pages/feed schemas alone do not establish order runtime or model agents.'],
     'reference_limits':{name:x.get('limitations',x.get('provenance_limits',[])) for name,x in raw.items()},
     'implementation_priorities':['Account/provider truth and durable intents/receipts','Unattended schedule/reconcile/partial-fill/protection lifecycle','Actual agent task execution and research tools','Journals/evidence/metrics with benchmark provenance','Persistent shared inbox and optional configured notifications','Readonly/operator UI and verified lifecycle controls'],
     'verification':{'kind':'read-only inventory/schema/evidence normalization checks','duplicate_ids':0,'all_atomic_features_mapped':True,'all_citations_have_pinned_commit_path_lines_url':True,'application_code_or_live_services_tested':False},
     'counts':{'canonical_operational_features':len(groups),'atomic_source_features':len(rows),'references_by_desk':dict(collections.Counter(r['reference'] for r in rows)),'pinned_citations':sum(len(r['evidence']) for r in rows)}}
(D/'FEATURE_PARITY.json').write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(doc['counts']))
