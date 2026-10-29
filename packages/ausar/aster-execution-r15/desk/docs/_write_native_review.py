import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path('/workspace/github-review')
OUT = Path('/workspace/agentic-desk/docs')
SHAS = {
    'autopilot-desk': '48e8f90f5d9def28363eb4013dac4dd8d78f74bf',
    'ChatGPT': '34f690003cfa2e503eebe3b3f4b0be9eaad11703',
    'Author-desk': '652db7afcc4312b6bd44d41547ca0f73981fe3ff',
    'Author-desk-backup': '652db7afcc4312b6bd44d41547ca0f73981fe3ff',
    'Femto': '8913e55f387062ba1546b714faa00e3db7e7ec1d',
}

def source(repo, path, start, end):
    file = BASE / 'repos' / repo / path
    assert file.is_file(), str(file)
    assert 0 < start <= end <= len(file.read_text().splitlines()), (path, start, end)
    return {'repo': repo, 'branch': 'main', 'commit_sha': SHAS[repo], 'path': path,
            'line_start': start, 'line_end': end,
            'url': f'https://github.com/dwj9ddyvf6-hub/{repo}/blob/{SHAS[repo]}/{path}#L{start}-L{end}'}

sources = {
    'A-runtime': source('autopilot-desk', 'src/lib/desk/worker.ts', 1305, 1444),
    'A-clock': source('autopilot-desk', 'src/lib/desk/worker-record.mjs', 1, 73),
    'A-http-lifecycle': source('autopilot-desk', 'src/routes/api/desk-worker.ts', 112, 167),
    'A-cron': source('autopilot-desk', 'vercel.json', 1, 13),
    'A-database': source('autopilot-desk', 'src/lib/db.ts', 1, 159),
    'A-ledger': source('autopilot-desk', 'src/lib/desk/persist.ts', 7, 153),
    'A-cycle-receipts': source('autopilot-desk', 'src/lib/desk/worker.ts', 610, 677),
    'A-account': source('autopilot-desk', 'src/lib/desk/engine.ts', 44, 83),
    'A-paper-fill': source('autopilot-desk', 'src/lib/desk/engine.ts', 238, 294),
    'A-broker': source('autopilot-desk', 'src/lib/broker/execute.ts', 17, 215),
    'A-truth': source('autopilot-desk', 'src/lib/desk/worker.ts', 152, 229),
    'A-optional-model': source('autopilot-desk', 'src/lib/scanner/server.ts', 49, 101),
    'A-scout-loop': source('autopilot-desk', 'src/lib/scanner/scout-cycle.ts', 23, 126),
    'A-scout-research': source('autopilot-desk', 'src/lib/scanner/scout-research.mjs', 81, 185),
    'A-scout-browser': source('autopilot-desk', 'src/lib/scanner/scout-run.mjs', 264, 341),
    'A-contract': source('autopilot-desk', 'src/lib/scanner/cassius-core.mjs', 21, 71),
    'A-terminal': source('autopilot-desk', 'src/lib/desk/cassius-sit.ts', 63, 117),
    'A-cli': source('autopilot-desk', 'scripts/cassius.mjs', 37, 91),
    'A-protection-lifecycle': source('autopilot-desk', 'src/lib/desk/always-on-core.mjs', 51, 64),
    'A-ui': source('autopilot-desk', 'src/lib/desk/store.ts', 179, 215),
    'A-status-ui': source('autopilot-desk', 'src/routes/desk/health.tsx', 37, 109),
    'C-entry': source('ChatGPT', 'app/page.tsx', 1, 5),
    'C-schedule': source('ChatGPT', 'worker/index.ts', 72, 84),
    'C-trigger': source('ChatGPT', 'vite.config.ts', 14, 20),
    'C-leases': source('ChatGPT', 'app/lib/desk-worker.ts', 87, 149),
    'C-sweep': source('ChatGPT', 'app/lib/desk-worker.ts', 288, 390),
    'C-mandates': source('ChatGPT', 'app/lib/desk-store.ts', 25, 135),
    'C-ledger': source('ChatGPT', 'app/lib/desk-runtime-store.ts', 5, 149),
    'C-chain': source('ChatGPT', 'app/lib/desk-runtime-store.ts', 183, 219),
    'C-execution-schema': source('ChatGPT', 'app/lib/paper-execution-store.ts', 10, 113),
    'C-paper-adapter': source('ChatGPT', 'app/lib/paper-execution-adapter.ts', 25, 82),
    'C-paper-position': source('ChatGPT', 'app/lib/paper-execution-store.ts', 178, 200),
    'C-fill-lifecycle': source('ChatGPT', 'app/lib/paper-execution-store.ts', 407, 470),
    'C-risk': source('ChatGPT', 'app/lib/paper-risk-store.ts', 7, 112),
    'C-truth': source('ChatGPT', 'app/lib/desk-market-provider.ts', 53, 130),
    'C-compiler': source('ChatGPT', 'app/api/mandate/compile/route.ts', 1, 17),
    'C-compiler-identity': source('ChatGPT', 'app/lib/mandate-compiler.ts', 316, 321),
    'C-browser-proposals': source('ChatGPT', 'app/lib/skyvern-trader.ts', 44, 56),
    'C-browser-gates': source('ChatGPT', 'app/lib/skyvern-trader.ts', 126, 194),
    'C-browser-lifecycle': source('ChatGPT', 'app/lib/skyvern-trader.ts', 251, 309),
    'C-browser-default': source('ChatGPT', 'app/lib/skyvern-store.ts', 155, 186),
    'C-ui': source('ChatGPT', 'app/components/AutopilotDesk.tsx', 854, 880),
    'C-preview': source('ChatGPT', 'app/components/AutopilotDesk.tsx', 651, 674),
}

def finding(statement, *refs):
    return {'statement': statement, 'source_ids': list(refs)}

report = {
    'title': 'Native desk infrastructure review for Aster Desk',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'review_mode': 'Read-only source tracing; no app source edits, production actions, remote service tests or strategy design.',
    'scope': ['Runtime and task/agent model', 'Persistence and receipts', 'Paper accounting and data provenance', 'Lifecycle and operator controls', 'Implemented capability versus published/deployed claims'],
    'excluded': ['Strategies, scanners, signals, ranking, indicators, allocation policies', 'Security audit'],
    'summary': 'Reuse durable operational evidence and lifecycle patterns, rather than existing trading decisions. ChatGPT has the most explicit durable scheduling and browser-task boundary; Sable has a process-worker and full paper-book facade; Author supplies file-worker/receipt patterns with important health-claim limits; Femto is a published read-only surface. None is an existing general six-agent operational task desk.',
    'repositories': [
      {
        'repo': 'autopilot-desk', 'commit_sha': SHAS['autopilot-desk'], 'names': ['Sable paper desk', 'Cassius operator/terminal'],
        'runtime': finding('TanStack React Start/Vite server application. The worker uses a process-global 30-second interval, 15-second watchdog, per-process in-flight flag and persisted heartbeat. It loops onboarded books and records per-cycle reports. This is a bounded deterministic desk worker, not a generic durable task queue or distributed agent scheduler.', 'A-runtime', 'A-clock'),
        'task_agent_model': [
          finding('Cassius duty contracts describe permitted reads/actions and paper-only boundaries. The terminal actually reads persisted books, obtains completed daily paths and a read-only Alpaca MCP probe, assembles a structured view and writes a diary card. The Cassius CLI calls those HTTP operations; its name/comment does not implement a separate reasoning agent.', 'A-contract', 'A-terminal', 'A-cli'),
          finding('Optional Grok 4.5 performs one constrained prose-to-schema interpretation when configured. Missing/model-failed cases return the deterministic interpretation. This call is not a autonomous tool loop, task delegation system or continuous public-news researcher.', 'A-optional-model'),
          finding('A separate bounded Edge/scout cycle is genuinely implemented: scheduled/manual cadence gating, public Yahoo/calendar/headline reads, structured SEEN/INFERRED/missing-evidence brief and durable policy/brief records. Optional Skyvern can launch one read-only Yahoo-page task with an eight-step budget and cooldown; this path records a launch URL rather than establishing a completed browser result. Optional paper hands are a separate deterministic desk-action path, not free-form model control.', 'A-scout-loop', 'A-scout-research', 'A-scout-browser'),
        ],
        'persistence': finding('PostgreSQL when DATABASE_URL is configured; otherwise PGlite on a disk directory. A per-user JSON snapshot is projected into account/event/order/fill/position/bracket tables. Event idempotency and fill IDs preserve receipts; cycle reports persist input freshness and resulting entity IDs. Snapshot projections are sequential writes, not one transaction over the whole book.', 'A-database', 'A-ledger', 'A-cycle-receipts'),
        'paper_accounting': finding('Local paper fills update cash, quantity, weighted average and marked equity. The simulator applies explicit simulated slippage. Connected Alpaca-paper orders remain pending until broker evidence reports fills, and reconciliation refreshes account/positions. Simulator values and broker values are distinct paths; the existing numeric/rounding model is not a Decimal accounting foundation to copy.', 'A-account', 'A-paper-fill', 'A-broker'),
        'data_truth': finding('Provider-derived quotes come from completed bars; absent history is not synthesized into live-read evidence. Demo/live-read/stale modes, provider fetch time, completed-bar time and worker time are tracked separately. Quote/print marks can fall back to cost when no quote exists, so marked equity should retain missing-mark provenance.', 'A-truth', 'A-account'),
        'lifecycle_limits': [
          finding('A local preview GET starts the process timer. Other GETs can perform an opportunistic sweep when the heartbeat is stale. The Vercel scheduled endpoint is one daily pulse, whose branch writes a running heartbeat and returns before performing a sweep. Source therefore does not establish uninterrupted unattended production operation.', 'A-http-lifecycle', 'A-cron'),
          finding('Pause/park blocks new work while existing protection evaluation remains enabled. UI pause/resume mutates a local clone and saves it; the worker tries to merge concurrent events/orders, but this is not a fenced generic task state machine.', 'A-protection-lifecycle', 'A-ui', 'A-runtime'),
        ],
        'operator_controls': finding('The UI exposes pause/resume, approvals, manual paper tickets, cancellations, position closes, broker sync and freshness/worker health. These are real server/store operations, not decorative activity cards.', 'A-ui', 'A-status-ui', 'A-broker'),
        'deployment_evidence': 'Reviewed pinned source only. No current running process, configured broker, external Grok availability or production uptime was tested.'
      },
      {
        'repo': 'ChatGPT', 'commit_sha': SHAS['ChatGPT'], 'names': ['Native AutopilotDesk / FolioTend Desk'],
        'runtime': finding('Main route renders AutopilotDesk. The Cloudflare Worker scheduled handler invokes the desk sweep and outbox dispatcher; source configuration supplies a five-minute cron. Active saved desks are dispatched independently of browser requests. Runtime deployment/configuration was not observed remotely.', 'C-entry', 'C-schedule', 'C-trigger', 'C-sweep'),
        'task_agent_model': [
          finding('Saved prompt/mandate versions are durable objects. The mandate compiler is explicitly deterministic. Research runs, observations and execution decisions are bounded application jobs, not free-form agents with arbitrary tools.', 'C-mandates', 'C-compiler', 'C-compiler-identity', 'C-ledger'),
          finding('Optional Skyvern is a real external browser-task boundary with persisted lifecycle/result/proposals. It defaults disabled and OBSERVE; enabled/configured tasks can propose only enumerated actions. Server gates apply paper actions according to explicit approval or PAPER_AUTOMATIC. This is not an unrestricted agent or a live-broker capability.', 'C-browser-default', 'C-browser-lifecycle', 'C-browser-proposals', 'C-browser-gates'),
        ],
        'persistence': finding('D1 records versioned desks, run/context/observation/candidate provenance, audit events and paper decision→intent→fill→protection→reconciliation→outcome links. Worker leases are per desk/window, expire after four minutes and fence completion by token. Stable run IDs allow retrying a window without inventing a new history entry. Health, bounded retry budget, provider cooldown, dead letters and notification outbox expose real failure states.', 'C-mandates', 'C-ledger', 'C-chain', 'C-execution-schema', 'C-leases', 'C-sweep'),
        'paper_accounting': [
          finding('PaperLedgerAdapter submits a PENDING handle and fills only from a later completed REAL_DATA bar supplied by the server. Cumulative fill quantities cannot move backward/overfill or rewrite terminal states. Order/fill/protection are committed together; position projection is updated afterward and failures are recorded as reconciliation mismatches.', 'C-paper-adapter', 'C-fill-lifecycle'),
          finding('Positions track weighted cost and realized P&L; exposure is reconstructed from durable open positions plus unfilled pending intents. The risk row has a seeded/cached account_equity value, and position market_value initially reflects cost. This is not a complete independent funding/cash/equity accounting ledger.', 'C-paper-position', 'C-risk'),
        ],
        'data_truth': finding('Yahoo requests are bounded, cached and try a secondary origin. Bars are filtered to completed intervals; source status/provider health and retrieved/completed timestamps remain explicit. Anonymous preview is a labeled fixture; saved desks can request provider-backed runs. A preview/compiled mandate is not evidence that real work executed.', 'C-truth', 'C-preview', 'C-ui'),
        'lifecycle_limits': finding('Separate controls exist for whole-desk active/paused status and paper-risk entry pause/park/kill switch. The scheduled query processes only active desks; risk pause still allows the active desk to settle protection/orders. These scopes should be explicit in a generic operational desk.', 'C-sweep', 'C-risk', 'C-ui'),
        'operator_controls': finding('Compile/accept/save/version/compare/export, run preview or server research, desk pause/resume, entry controls, paper review/cancel-replace, and optional browser-task run/status/review are implemented UI routes. They depend on durable saved owner-scoped objects; no general task inbox or six-agent operational handoff UI is present.', 'C-mandates', 'C-ui', 'C-preview', 'C-browser-gates'),
        'deployment_evidence': 'Reviewed pinned source and configuration. No deployed D1 contents, cron delivery, model connection, Skyvern session or paper-provider operation was tested.'
      },
      {
        'repo': 'Author-desk / Author-desk-backup', 'commit_sha': SHAS['Author-desk'],
        'summary': 'Deterministic Node/file workdesk with JSON persisted book/receipts, PID locks and heartbeat/watchdog recovery. Both repos preserve the same tree. Current halt flags disable paper execution and publishing; some workers still operate. LIVE_CLOCK=zero is not a global process halt. Status literals/same-day scan stamps and successful workflow exits do not independently prove delivery.',
        'detail_review': 'review-Author-infrastructure.json',
        'portable_patterns': ['Single publisher and recorded external delivery receipts', 'Completed-bar duplicate boundaries', 'Book/receipt and operator status views', 'Worker restart/heartbeat observability'],
        'limits': ['No generic agent/task reasoning runtime', 'Do not reuse literal renderer health or heartbeat-as-delivery semantics', 'Archived book snapshot is not current broker truth'],
      },
      {
        'repo': 'Femto', 'commit_sha': SHAS['Femto'],
        'summary': 'Published static HTML terminals and a JSON feed. The browser fetches/render snapshots with fallback and freshness labels. No agent runner, task producer, ledger writer, order handling or enforcement source is present here.',
        'detail_review': 'review-femto-published-ui.json',
        'portable_patterns': ['Read-only desk visibility with timestamped provenance', 'Retain last known snapshot on feed failure while making age visible', 'Operator-facing book, activity, pending-work and review surfaces'],
        'limits': ['Feed freshness is not engine or broker health', 'Published values were not reconciled independently', 'Saved GitHub Pages success supports publication of this commit, not present live operation'],
      },
    ],
    'patterns_for_strategy_free_desk': [
      {'pattern': 'Durable task and ordered attempt/step history', 'application': 'Store queued/running/completed/failed/cancelled operational work; identify each worker attempt and actor. A display card or event row alone is not an agent task.'},
      {'pattern': 'Fenced claims and restart recovery', 'application': 'Persist a lease/token or equivalent single-worker exclusion, bound attempts and recover expired in-flight work. Keep stable task/effect identities across retries.'},
      {'pattern': 'Independent accounting authority', 'application': 'Reconcile human funding and recorded fills into cash, reserved cash, positions, cost and realized P&L. Commit reservation/fill effects atomically using exact monetary values.'},
      {'pattern': 'Truthful empty state and evidence clocks', 'application': 'Start with zero funding/positions/orders/strategies. Preserve manual quote source, as-of time, ingestion time, missing/stale marks and the time a task actually completed.'},
      {'pattern': 'Local automation versus configured reasoning', 'application': 'Operational local workers can audit/reconcile/journal without a model. Show reasoning configuration and observed task results separately; only explicit brief/note requests may call the optional provider.'},
      {'pattern': 'Explicit human action boundary', 'application': 'Agents report pending intents and operational gaps. They cannot fund accounts, create strategy decisions or approve/fill human orders.'},
      {'pattern': 'Receipt-based health', 'application': 'Expose last successful effect, last attempt, active lease, error/degraded state and evidence age. A running timer, green workflow exit or recent HTTP pulse is insufficient proof of delivery.'},
      {'pattern': 'Scoped pause/cancel semantics', 'application': 'Pause prevents new recurring cycles; manual tasks remain available. Cancellation stops future steps while preserving already completed receipts and history.'},
      {'pattern': 'Audit trail and export', 'application': 'Record actor/time/object transitions and source references. Preserve settings, tasks, quotes, account facts and receipts in a portable export.'},
    ],
    'actual_agent_capabilities_and_limits': {
      'implemented': ['Deterministic bounded desk work and explicit cycle/receipt persistence', 'Optional constrained Grok mandate interpretation in Sable', 'Sable bounded public-data scout briefs and optional one-page Skyvern launch; a launch is not a completed browser result', 'Optional configured Skyvern browser tasks in ChatGPT, with server-applied enumerated paper actions', 'Static feed publication/rendering in Femto'],
      'not_established': ['General-purpose autonomous multi-agent planning/delegation', 'A common durable agent/task inbox spanning these repos', 'Current deployed uptime or enabled model/broker connections', 'Full accounting solely from cached risk/equity or published feed values'],
      'new_desk_boundary': 'The six Aster roles should be actual operational task steps, not strategy labels. Local automation, optional reasoning, human accounting/order operations and immutable evidence must remain distinct.'
    },
    'sources': sources,
    'limitations': ['Focused infrastructure source review, not every line of these repositories.', 'Strategies and security intentionally excluded.', 'No remote deployed services or production effects were exercised.', 'Companion Author/Femto reports preserve their deeper source paths and exact implementation/publication distinctions.'],
}

for file, key in [('review-Author-infrastructure.json', 'Author_detail_available'), ('review-femto-published-ui.json', 'femto_detail_available')]:
    report[key] = (OUT / file).is_file()

(OUT / 'review-native-desks.json').write_text(json.dumps(report, indent=2) + '\n')
print(f"Saved {OUT / 'review-native-desks.json'} with {len(sources)} checked source references")
