import json, hashlib, pathlib, urllib.parse

ROOT = pathlib.Path('/workspace/github-review/repos')
OUT = pathlib.Path('/workspace/agentic-desk/docs/FEATURES_GROKBOT.json')
Q = 'quant-research-backup'
SHA = 'cae8806a8e963be365bf862a3b3e463088c90a29'
M = 'Midna'
MSHA = '1e03a16743d8e725fa123a95e8273d71e6fc6038'
PD = 'Author-research/shadow/paper_desk/'
TM = 'Author-research/shadow/terminal/'
DB = 'Author-research/db/'
PEOPLE = 'workspace__self_improvement__staging__relationships__sirun_fb0673c0c7344259b05e2bae963bb3b4__people/grokbot.md'
features = []

def source(path, a, b=None, repo=Q, classification='implemented source'):
    commit = MSHA if repo == M else SHA
    return {'repo':repo, 'commit':commit, 'path':path, 'line':a, 'end_line':b or a,
            'evidence_class':classification,
            'url':f'https://github.com/dwj9ddyvf6-hub/{repo}/blob/{commit}/{urllib.parse.quote(path)}#L{a}-L{b or a}'}

def add(id, name, behavior, requirement, refs, dependencies=None, limits=None):
    features.append({'id':id, 'feature':name, 'source_behavior':behavior,
                     'new_desk_requirement':requirement, 'sources':refs,
                     'dependencies_or_configuration':dependencies or [],
                     'limits_and_status':limits or [], 'strategy_specific':False})

add('G01','GrokBot identity and accountable team roles',
    'Midna records identify User\'s Grok-session Head of Trading team: Edge Hunter, Risk Manager, Journal & Coach. Inbox operational notes are signed Chief of Staff, with Desk Ops and Research Lab workers reported on October 5.',
    'Represent named agent roles, authority, tasks, outputs and operator ownership. If these are implemented as actual model agents, execute durable tasks through configured model providers and record their tool calls and evidence.',
    [source(PEOPLE,11,17,M,'archived relationship narrative'),source('grokbot-inbox/INBOX.md',37,39,classification='contemporaneous self-report')],
    ['Model provider and model selection are new-desk configuration; no Grok API credential was sought or copied.'],
    ['Role titles document external AI sessions. No resident general-purpose reasoning worker, model invocation, tool registry or task queue was located in the reviewed paper runtime.'])
add('G02','Separate main and experimental paper accounts',
    'Publisher is built for a $100,000 main Alpaca paper book starting October 1, 2026. A second paper_sleeve account has independent state/ledger and an allow-listed summary; it is never mixed into main account, equity, headline or statistics.',
    'Namespace broker accounts, cash, positions, intents, risk budgets, journals and metrics by desk/book; preserve separate ownership and provenance.',
    [source(TM+'README.md',3,14,'quant-research-backup','documented runtime architecture'),source(TM+'publish.py',702,724)],
    ['Separate paper broker account configuration and private credential references.'],
    ['The starting $100k is the historical reference book, not permission to fund a new account. Second-desk code or an enabled lane is not proof of activation. October6 journal says second desk was not live for trading yet.'])
add('G03','Paper broker adapter and broker truth',
    'Python runtime calls paper-api.alpaca.markets for account/positions/orders and data.alpaca.markets for market prices. Publisher uses broker account, positions and portfolio history for current account figures.',
    'Expose a paper broker integration with connection status, account identity, source timestamp and last successful read; distinguish local simulation from external paper brokerage.',
    [source(PD+'desk.py',18,23),source(TM+'publish.py',181,208)],
    ['ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY are read privately from environment; values are not in this report.','Python, pandas, numpy and tracker calendar module.'],
    ['No authenticated broker call was made; current account balance/connectivity are not independently verified.'])
add('G04','Hash-chained append-only event ledger',
    'append assigns contiguous seq, prev_hash and SHA256 hash; writes JSONL then flushes/fsyncs. verify recomputes chain and checks frozen config hashes.',
    'Persist append-only execution and decision events with immutable IDs and integrity verification; let projections be rebuilt from these events.',
    [source(PD+'desk.py',157,179)],
    ['Durable filesystem, serialized writer and canonical hash format.'],
    ['Integrity hashes are a provenance mechanism, not an independently signed broker record.'])
add('G05','Atomic state and pre-submit intent durability',
    'State snapshots and order-intent JSON use temporary files, fsync, replace and directory fsync. Intents are distinct from completed broker orders.',
    'Persist intended submission before contacting the broker, then persist receipt and settle the intent only after durable state/event commit; recover after worker death.',
    [source(PD+'desk.py',180,198),source(PD+'desk.py',1271,1276)],
    ['Durable storage for state and intents; broker client-order-ID lookups.'])
add('G06','Versioned frozen operational configuration',
    'Runtime refuses missing/unfrozen or hash-mismatched playbooks. Records and positions carry the playbook version/hash; immutable history copies preserve earlier settings.',
    'Version broker, risk, workflow and account settings separately from strategy modules; keep an auditable change record and previous configuration.',
    [source(PD+'desk.py',200,210),source(PD+'README.md',3,5)],
    ['Configuration schema and ledger-backed settings history.'],
    ['Existing strategy playbooks, ranking formulas, signal units, exits and thresholds are excluded from new-desk defaults.'])
add('G07','Explicit pass lifecycle and receipt',
    'A pass logs run_start, reconciles first, services queued orders, manages exits, evaluates candidates, re-reads positions, manages exits again and commits run_end/state. Partial pass errors can preserve effects.',
    'Make reconciliation, servicing existing orders, risk checks, permitted intents and receipt persistence explicit workflow stages with attempts and resumable outcomes.',
    [source(PD+'desk.py',1245,1276)],
    ['Scheduler and broker adapter.'],
    ['Existing candidate generation is strategy-specific and excluded. Strategy-free starts with empty strategies and operator/authorized task intents only.'])
add('G08','Session calendar and broker clock verification',
    'Runtime compares broker trading-day/close calendar to tracker calendar and logs disagreements before halting that pass. The current version includes broker-clock checks for time-sensitive submissions.',
    'Use an authoritative session clock with holidays, DST and early closes; validate the submission window at the actual send time.',
    [source(PD+'desk.py',1364,1378),source(PD+'desk.py',24)],
    ['Alpaca calendar/clock endpoints and market-calendar implementation.'],
    ['Calendar request exceptions currently print a warning and continue; a confirmed calendar mismatch halts. Do not overstate this as every clock/data error halting.'])
add('G09','Internal trade accounting and status report',
    'Generated report separates queued, pending, failed, open, closed and mismatched positions; shows entry/exit quantities, average prices, realized/unrealized dollars and lock reasons.',
    'Provide broker-reconciled internal position/order views with explicit lifecycle states and quantity/price provenance.',
    [source(PD+'desk.py',1278,1313),source(PD+'report.md',3,5,classification='stored generated snapshot')],
    ['Broker fills/marks, local ledger and state.'],
    ['Stored October6 snapshot reports 18 open positions, $2,587.80 unrealized and 0 closed trades, not current balances. report() uses entry-price fallback if broker marks fail; public metrics need explicit stale/unavailable semantics.'])
add('G10','Execution quality and slippage report',
    'Internal report compares actual fills to known research reference prices, preserving sample size, mean/median slippage and assumed transaction cost per side.',
    'Record intended reference price, actual fill, mark source and timing; expose execution slippage without representing estimated fills as broker fills.',
    [source(PD+'desk.py',1314,1325)],
    ['Reference-price provenance and broker execution events.'],
    ['The reference study price and cost schedule are historical strategy assets; port the measurement interface without importing their assumptions.'])
add('G11','Idempotent daily account snapshots',
    'Close writes one P&L row per NYSE trading date; a rerun replaces that date instead of double-counting, and a holiday writes none.',
    'Store unique book/date account snapshots, preserving revised source timestamp and preventing duplicate daily P&L.',
    [source(PD+'desk.py',1334,1343),source(PD+'desk.py',1382,1390)],
    ['Market calendar, local state and broker equity.'])
add('G12','Broker-backed readonly public terminal',
    'Publisher builds a static JSON projection; browser polls every 60 seconds. The publisher never submits orders. It has a separate single-instance 5 minute loop and publishes only changed payloads.',
    'Keep public/readonly views distinct from operator commands; show provenance and refresh health while orders remain server-side.',
    [source(TM+'README.md',3,24,classification='documented architecture'),source(TM+'publish_loop.sh',1,28)],
    ['Publisher process, hosting or local HTTP server, broker read connection.'],
    ['Source documents a public GitHub Pages URL; live hosting was not independently visited during this read-only source review.'])
add('G13','Honest session and freshness labels',
    'Outside regular market hours the headline uses last-close wording; official close history is used when available. A stale public update turns the header amber.',
    'Expose observation time, feed age, session state, latest-mark versus official-close basis and unavailable values.',
    [source(TM+'publish.py',89,146),source(TM+'README.md',28,35,classification='documented UI behavior')],
    ['Broker calendar and portfolio history.'],
    ['Publisher has Mon–Fri09:30–16:00 fallback when calendar unavailable; fallback cannot know holidays.'])
add('G14','Realized results and closed-only win rate',
    'Public closed-trade log uses trade_closed ledger events, requires state agreeclosed, and calculates quantity-weighted exit. Track record keeps realized/partial-exit P&L separate from unrealized and includes sample counts.',
    'Compute wins/returns from actual completed trades; label open marks, partial exits and sample sizes separately.',
    [source(TM+'publish.py',490,530)],
    ['Broker fills plus closed-trade ledger/state.'])
add('G15','Drawdown and benchmark comparisons',
    'Public account curve uses Alpaca portfolio history and synchronized SPY bars. Maximum drawdown uses chronological broker equity marks plus latest mark and exposes basis.',
    'Provide book equity history, realized/unrealized attribution, drawdown and benchmark comparison with aligned timestamps and common start basis.',
    [source(TM+'publish.py',196,223),source(TM+'publish.py',510,530)],
    ['Broker portfolio history and benchmark bars.'],
    ['Display metrics are not the automatic exposure/drawdown breaker: inbox explicitly says no automatic breaker on GrokBot main desk.'])
add('G16','Filled-holdings exposure and beta provenance',
    'Holdings heatmap draws broker-filled long positions only; long-beta panel market-value weights observed OLS beta to IWM, exposes data coverage and records forward daily points without backfilling nonexistent lane history.',
    'Offer exposure by book/symbol/sector and optional benchmark beta with coverage and method; isolate queued reservations from filled market value.',
    [source(TM+'publish.py',532,553),source(TM+'publish.py',608,620),source(TM+'publish.py',648,700)],
    ['Historical return bars and correct asset/book classification.'],
    ['Existing lane grouping, IWM reference and63/30session parameters are source-specific; new desk configuration should not import them automatically. Heatmap source filters out shorts.'])
add('G17','Separately labelled research expectations',
    'Source scorecards carry research statistics and separately compute live paper statistics, closed counts and small-sample notes; missing reference numbers remain missing.',
    'Keep research artifacts/results distinct from paper executions and include provenance; a research task output does not become an order.',
    [source(TM+'publish.py',555,595),source(TM+'publish.py',403,408)],
    ['Artifact store with study IDs and data/version provenance.'],
    ['No research strategy, alpha claim or default funded sleeve is copied into the new desk.'])
add('G18','Visible worker, gate and missed-slot health',
    'Terminal derives last completed run, matching scheduler phaseexit, ledger-check status, passes_today, lock count and latest gate/slot audit. Missing MOC window alerts are recorded once per date.',
    'Expose heartbeat separately from last useful work; show incomplete passes, missed/failed slots, reconciling locks and data age as actionable operator state.',
    [source(TM+'publish.py',311,332),source(TM+'publish.py',1547,1570),source('Author-research/shadow/moc_window_check.py',2,44)],
    ['Persisted scheduler receipts, broker/reconcile status and event log.'],
    ['Existing alert sink is log/stdout/terminal; no generic Telegram/email notification transport located in these alert sources.'])
add('G19','Operational gate and critical-input diagnostics',
    'Gate checks scheduler presence, desk gate, critical file health, missed slots, STOP/FREEZE and heartbeat next slot, emits JSONL and explicit failure reasons.',
    'Define readiness checks and dependency-specific health reasons, with explicit recovery actions and separate entry pause versus existing-order servicing.',
    [source('Author-research/shadow/live_trading_gate_check.sh',14,46)],
    ['Critical-input allowlist, scheduler manifest, account readiness and source-data freshness.'],
    ['Although the gate wrapper is described readonly, called helpers may enforce recovery/FREEZE state. Do not assume running it has no local effects. No helper was executed in this review.'])
add('G20','Research/operations isolation and durable context journals',
    'Inbox reports separate Desk Ops and Research Lab workers. Daily journals explicitly declare context for evening learning, not trade overrides; dated daily/week/month/memory files preserve incident and rationale history.',
    'Provide scheduled premarket context, post-session review, durable decisions/lessons and task artifacts with source links, without allowing free-form narrative to change order/risk settings.',
    [source('grokbot-inbox/INBOX.md',37,39,classification='contemporaneous self-report'),source(PD+'journal/daily/2026-10-06.md',1,6,classification='stored journal'),source(PD+'journal/memory.md',98,112,classification='stored journal')],
    ['Research tools/data sources, journal task worker and persistent artifact store.'],
    ['No generic automatic model-agent journal writer was located. Exact journals are evidence of completed external-agent/operator work, not proof of native worker implementation.'])
add('G21','Queryable ledger, decisions, fills and journal evidence',
    'DuckDB refresh projects append ledger tables incrementally and rebuilds changed state/journal/report sources; SQL views expose orders, updates, fills, decisions, closed trades and runs. Journal is section-indexed for search.',
    'Offer read-only searchable task/decision/execution history and rebuildable analytics projections without blocking time-critical runtime.',
    [source(DB+'refresh.py',1,10),source(DB+'refresh.py',226,237),source(DB+'refresh.py',332,336),source(DB+'refresh.py',515,542),source(DB+'QUERIES.md',103,138)],
    ['DuckDB/pyarrow for reference implementation; new implementation can use its existing database.'],
    ['Projection is not a separate authoritative ledger. Publisher avoids opening research DuckDB to prevent locking the scheduled writer.'])
add('G22','Three-peer append-only shared inbox',
    'INBOX is a shared Markdown dead-drop for GrokBot, Cursor and Midna. Entries append at bottom withETdate/time/author/topic, evidence/confidence and urgency; participants lack each other\'s chat histories. Midna hourly sweep/relay is documented.',
    'Implement persistent messages with author/desk, timestamp, topic, body, evidence, urgency and delivery/read cursor. Expose incoming/outgoing threads and safe idempotent append; keep independent desks/accounts.',
    [source('grokbot-inbox/INBOX.md',1,14,classification='channel protocol'),source(PEOPLE,13,17,M,'relationship narrative')],
    ['For an external shared-inbox integration, repository/reference/path and write-capable connector configured explicitly; local inbox can work without remote credentials.'],
    ['Archived hourly sweep is documented external automation, not a source-verifiable standing inbox API. This review sent no message and made no remote writes.'])
add('G23','Inbox preservation and backup-safe synchronization',
    'Backup installs pre-push guard and refreshes index with read-tree HEAD after admin-ref updates. Hook rejects ref/file deletions and protected-inbox changes by bulkbackup. Deliberate inbox appends use a scoped protected-path opt-in.',
    'Protect the inbox/event/journal stores from bulk backup reconciliation; make remote collaboration appends additive and retain cursor/message IDs through restart.',
    [source('backup/sync.sh',22,36),source('backup/hooks/pre-push',2,24),source('grokbot-inbox/INBOX.md',318,326,classification='reported box verification')],
    ['Backup and connector ownership distinct from collaboration messages.'],
    ['No backup command or hook was run. October6 report says deployedbox copies matched, but deployed copies are not accessible here.'])
add('G24','Failure recovery must verify effects before retry',
    'Inbox records broker accepts before state-save as a crash gap and describes verify-before-retry plus deterministic intents. Current source persists intents and settles after durable state.',
    'On retries query prior intent/client-ID and broker state; never replay an external side effect merely because a worker lacks success receipt. Keep journaled attempts and reconcile after restarts.',
    [source('grokbot-inbox/INBOX.md',238,258,classification='contemporaneous implementation discussion'),source(PD+'desk.py',191,198),source(PD+'desk.py',1274,1276)],
    ['Broker idempotency identity, task attempts and durable receipt store.'],
    ['October5/October6 narrative promises are dated; current pinned source supersedes them where implementation is present.'])

add('G25','Validated external paper account readiness',
    'Paper adapter rejects non-paper URL configuration, missing credentials, inactive/non-PA or trading-blocked account before execution.',
    'Require explicit paper mode and verified account readiness; connection status must come from actual account reads.',
    [source(PD+'desk.py',438,448)],
    ['Private broker credentials and account connection setup.'])
add('G26','Idempotent submission and ambiguous receipt recovery',
    'Deterministic client-order IDs identify attempts; pre-submit intent is persisted, failed/ambiguous submit looks up the same client ID, then records the broker receipt and any immediate fill.',
    'Persist intent before submission; reuse idempotency identity on uncertain outcomes and recover exact broker receipts before retrying.',
    [source(PD+'desk.py',652,678)],
    ['Broker client-ID lookup and submission adapter, durable intent store.'])
add('G27','Cumulative partial-fill import and confirmed cancellation',
    'refresh imports cumulative filled quantity and average price; apply_fill books only additional quantity; cancellation polls actual broker status and does not assume a request is a completed cancel.',
    'Track cumulative filled quantity AND notional/fees; book deltas exactly once, and preserve pending-cancel state until confirmed.',
    [source(PD+'desk.py',680,717)],
    ['Broker order polling or stream, monotonic execution receipt IDs.'],
    ['Source sell accounting uses each new quantity at the current cumulative average, which can misstate proceeds when fill prices differ. New implementation must delta cumulative notional, not copy this accounting shortcut.'])
add('G28','Broker reconciliation with explicit symbol locks',
    'Every pass refreshes unfinished orders, broker positions and open orders. Unknown orders/positions, local phantoms and quantity mismatches become reasoned symbol locks.',
    'Reconcile broker versus local state before new intents, report mismatches, block conflicting symbol activity and provide safe resolution/adoption controls.',
    [source(PD+'desk.py',719,748)],
    ['Account positions/open-orders reads and local ownership map.'],
    ['This symbol-local control is distinct from automatic global gross-exposure/drawdown breakers; main inbox reports no such automatic breaker.'])
add('G29','Crash-safe adoption preserving existing broker facts',
    'Current runtime recovers durable intents and matching orphan entry/exit orders. A known queued/pending position can adopt an accepted broker entry without resubmitting; missing source plan leaves symbol locked.',
    'Adopt only identifiable owned broker records, preserving IDs, fill quantities, cost, protection and ownership; unknown legacy positions require explicit metadata rather than invented strategy/ATR.',
    [source(PD+'desk.py',753,790),source(PD+'desk.py',817,846),source(PD+'desk.py',1118,1138)],
    ['Stable ownership/client-ID mapping, intent and order history.'],
    ['Existing generic orphan reconstruction depends on strategy fire and frozen plan. Strategy-free adoption must retain unknown metadata and cannot recreate those plans.'])
add('G30','Protection quantity and cancel-replace lifecycle',
    'Manage-exits maintains GTC stop/limit orders, tracks partial targets, resizes coverage when entries keep filling and waits for cancel confirmation before replacing.',
    'When a protection policy is explicitly supplied, track covered versus uncovered broker quantity and manage replacement/cancellation without overselling.',
    [source(PD+'desk.py',882,926),source(PD+'desk.py',655,659)],
    ['Explicit operator/strategy protection intent, broker-supported order types.'],
    ['Existing orders are independent stops/limits, not a proven atomic OCO/bracket. Sell-reservation guard can block competing coverage. No stop/target/trailing formulas copied.'])
add('G31','Entry pause that preserves existing-position management',
    'STOP holds newly offered and already queued entries; main pass still reconciles and manages existing exits.',
    'Provide pause-new-entries and resume controls with operator, reason and audit event, independently of shutdown/cancel/flatten controls.',
    [source(PD+'desk.py',1024,1032),source(PD+'desk.py',1163,1172),source(PD+'desk.py',1252,1258)],
    ['Persistent book control state and role-aware operator commands.'])
add('G32','Cash reservations and account/book risk budgets',
    'Reference entry path reads cash, subtracts pending reservations, limits whole-share notional to available cash and configured lane budgets, and records retryable capacity blocks with deadline.',
    'Reserve notional for pending intents/orders and enforce configured book/symbol/exposure constraints using current broker cash/buying power; release reservations only on verified lifecycle change.',
    [source(PD+'desk.py',1045,1078)],
    ['Broker cash/buying power, current positions/open orders, configured risk policy.'],
    ['Source claim order, lane budgets, liquidity floors and sizing formulas are strategy-specific. New desk retains configurable constraints with no imported allocation.'])
add('G33','Durable success-only schedule receipts and bounded retries',
    'Watch loop uses singleton flock, explicit heartbeat and per-slot attempts. Zero process exit is insufficient: it requires a matching ledger run_end. Failure retries use bounded window/cadence and can rerun only the desk when tracker already succeeded.',
    'Persist scheduled slot/attempt/stage completion and side-effect receipts; retry unfinished stages within their valid window without duplicating completed effects.',
    [source('Author-research/shadow/watch_scheduler.sh',26,39),source('Author-research/shadow/watch_scheduler.sh',45,60),source('Author-research/shadow/watch_scheduler.sh',78,104)],
    ['Independent scheduler, task lease, broker idempotency and receipt verification.'])
add('G34','NYSE slots, late catch-up and post-session verification',
    'Watch slots skip holidays/weekends and honor early closes. Preopen/open and close-relative MOC slots are computed separately; an unrecorded late MOC slot remains eligible before cutoff. Close scheduler includes restart catch-up.',
    'Schedule operational passes against exchange sessions; preserve due work after restart, and explicitly mark expired work rather than executing it outside its valid window.',
    [source('Author-research/shadow/watch_slots.py',1,21),source('Author-research/shadow/watch_slots.py',46,53),source('Author-research/shadow/scheduler.sh',18,66)],
    ['Exchange calendar, persistent slot receipts and pass receipt verifier.'],
    ['Close scheduler weekday gating differs from intraday calendar-aware slots; calendar check in order runtime remains relevant.'])
add('G35','Independent scheduler supervision and host-reset recovery',
    'On-box supervisor polls scheduler processes, records deaths/restarts and launches missing schedulers. Alive-but-stale heartbeats warn without killing. Inbox reports off-box routines restart workers after VM replacement.',
    'Supervise resident jobs independently of browser/model sessions; persist heartbeat/death/restart evidence and use an external service supervisor for host restart.',
    [source('Author-research/shadow/supervisor/sched_supervisor.sh',103,134),source('grokbot-inbox/INBOX.md',251,258,classification='reported external routines')],
    ['Persistent process/service manager or externally hosted scheduler.'],
    ['External routine definitions are not included in reviewed source. On-box supervisor alone cannot survive host replacement; stale-but-alive process does not auto-restart in this reference.'])
add('G36','Independent staged account arming and rollback',
    'Second desk has separate credential names, process namespace and ARMED gate; soft rollback pauses entries, resume clears it and full rollback checks that broker is empty. Snapshot README describes staged/unarmed state, and newer1.0.4 sibling is explicitly staging.',
    'Support staged connection, explicit activation, pause/resume and account-safe rollback without disturbing another book. Show staged versus active state from actual runtime receipts.',
    [source('Author-research/shadow/paper_sleeve/README.md',1,27,classification='documented staged lifecycle'),source('Author-research/shadow/paper_sleeve/sleeve_scheduler.sh',17,20),source('Author-research/shadow/paper_sleeve/rollback.sh',11,29)],
    ['Separate paper account/credential references and durable activation state.'],
    ['No arm/rollback operation executed. Source availability and enabled configuration are not proof of deployed trading.'])
add('G37','Isolated dry-run/replay and operator command surface',
    'Dry run uses separate state/ledger/report/lock; CLI exposes verify, run, report, configuration freezes and controlled configuration-mode changes.',
    'Separate simulation/replay fixtures and operational tasks from external paper accounting; expose explicit status, verification, reconcile, pause and resume tools to authorized operators/agents.',
    [source(PD+'desk.py',1364,1370),source(PD+'desk.py',1518,1535)],
    ['Separate run-mode namespaces and command/task tool contracts.'],
    ['The connectivity-test CLI sends then cancels a paper order, so it was not run as a read-only check. Replay carries source strategy logic; no strategy replay copied.'])

doc={'reference_name':'GrokBot','status':'source-backed operational feature inventory for corrected reference set',
     'scope':'GrokBot only; strategies and security excluded', 'review_date':'2026-10-08',
     'identity':{'team':'Head of Trading','roles':['Edge Hunter','Risk Manager','Journal & Coach'],
                 'operational_signoff':'Chief of Staff','runtime_path':PD+'desk.py',
                 'repository':Q,'branch':'main','commit':SHA,'desk_version':'paper-desk 1.7.6.1','playbook_version':'1.4.4-r1'},
     'features':features,
     'evidence_policy':'Implemented source, stored snapshot, documented protocol and reported external agent/deployment behavior are labelled separately. No archived settings or instructions authorize production changes.',
     'strategy_exclusions':['signals/scanners','alpha models','ranking/eligibility','specific lane/sleeve/default funding','stop/target/timeexit formulas','research performance claims'],
     'review_scope':{'inbox':'All narrative entries across lines1–700 read; embedded225-rowSnorlaxCSV structurally parsed. Cursor/Midna strategy discussions not ported.',
                     'source':'Targeted complete functions for durability/pass/report/publisher/projection/inbox safeguards; runtime/scheduler companion reviewed by child.',
                     'execution':'No tests, dependency installation, broker calls, clouddeploy, message sending or GitHub writes.'},
     'limitations':['Archived pinned snapshot does not establish current deployment, broker balance or running workerhealth.','External Grok/Muse/Cursor session prompts/toolaccess/scheduledservice infrastructure are outside this repository; role titles alone cannot supply model execution.','Source report notes explicit missing/staged states and does not collapse them into shipped capability.'],
     'dependencies_summary':['Configured paperbroker or honestlocal simulator','Marketdata source withsession/timestamp/freshness','Independent durable scheduler/supervisor','Persistent intents/receipts/ledger/state','Configured model provider foractualagent tasks','Queryable research/journal/message artifacts','Optional external shared-inbox connector']}

# Verify every unique referenced body matches this repository's pinned tree.
trees={}
verification=[]
for f in features:
    for s in f['sources']:
        key=(s['repo'],s['path'])
        if key in {(x['repo'],x['path']) for x in verification}: continue
        if s['repo'] not in trees:
            j=json.load(open('/workspace/github-review/metadata/'+s['repo']+'/tree.json'))
            trees[s['repo']]={x['path']:x for x in j.get('data',j)['tree']}
        p=ROOT/s['repo']/s['path']; body=p.read_bytes()
        blob=hashlib.sha1(('blob '+str(len(body))+'\0').encode()+body).hexdigest()
        expected=trees[s['repo']][s['path']]['sha']
        assert blob==expected,(key,blob,expected)
        assert 1<=s['line']<=s['end_line']<=len(body.splitlines()),s
        verification.append({'repo':s['repo'],'path':s['path'],'git_blob_sha':blob,'matches_pinned_tree':True})
doc['source_body_verification']=verification
OUT.write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'features':len(features),'verified_bodies':len(verification)}))
