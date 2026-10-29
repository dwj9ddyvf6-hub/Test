# Autonomous desk integration contract

References: **Femto/Midna, Cursor, GrokBot**. Shared channel `quant-research-backup/grokbot-inbox/INBOX.md`, reviewed at `cae8806a8e963be365bf862a3b3e463088c90a29` and subsequently read/appended live. Cursor executable source Midna `cursor/paper-desk-f184`, reviewed at `164be062`; the branch later advanced to `c0cc0b6e`. Complete historical Femto code was recovered from Midna `b19f9d7a1f92f12883ced3c7cd3fa30e37a0c8c4`, under `workspace/alpaca-swing-desk/`, with external cron/workflow bodies and broker/engine dependencies. All 370 recovered bodies were Git-blob verified. Midna's live inbox reply reports a newer local-only `main@914ed868`; distinguish that reported state from the executable historical snapshot. The latest flattened main backup is partial and cannot substitute for the full historical tree.

No strategies, stock selection, generated orders or allocations. Explicit operator/API intents execute autonomously; order mechanics are infrastructure. Research/inbox/model outputs cannot originate orders, fund books or change protected risk policy. Defaults have no funded accounts or sample trades. Never copy original credentials or books. All original repositories stay read-only.

## Ownership and common interfaces

Backend owner: `backend/trading.py`, `backend/app.py`, existing worker integration, paper-engine tests/dependencies. `TradingDesk(store)` uses separate `p_` tables in same SQLite DB; preserve legacy manual book. Runtime owner: `backend/providers.py`, `backend/autonomy.py`, provider/runtime tests; do not edit app/store/worker. Root owns `backend/lab.py`, `/api/lab` router, docs/deployment/e2e. Frontend owner owns all frontend.

`Lab(store)` exposes `snapshot()`, `operate(...)`, `alert(key,severity,message,payload=None)`. Alerts and local inbox writes never post to source GitHub inbox.

`GET /api/autonomy` joins `trading.snapshot()` plus `runtime.snapshot()` plus `lab.snapshot()` under keys `trading`, `runtime`, `lab`, `research`, `reports`, `notifications`; use this public layout consistently. `/api/desk` legacy continues unchanged. `/api/autonomy` runtime snapshot includes provider status/calendar/jobs/schedules. All timestamps UTC ISO. Error detail conventional.

## Trading engine

`TradingDesk` methods: `snapshot()`, `create_book(payload)`, `fund_book(book_id,amount,client_id)`, `submit_intent(payload)`, `cancel_intent(id)`, `set_book(book_id,payload)`, `process(providers,clock=None)`, `reconcile(providers,clock=None)`. Snapshot keys books/intents/positions/fills/equity_history/reconciliations. Decimal qty/price, integer cents cash. Durable pre-submit identity, atomic effects, unique fills, pending cash/share reservations. Broker books never simulate local fills or merge with other books.

Book payload name/kind(main,context,forward,shadow)/broker(local,alpaca)/description optional, connection_id defaultdefault. Default main local book exists empty; cash zero. Explicit funding only for local books. Broker account truth fetched. Only one book per actual Alpaca account binding prevents misattribution; separately configured account aliases support independent broker books. Labels for sleeves are descriptive, no trading rules.

Intent payload book_id/symbol/side(buy,sell)/quantity/order_type(market,limit,stop,stop_limit)/time_in_force(day,gtc,opg,cls)/client_id; optional limit_price,stop_price,not_before,expires_at,reason,sleeve,take_profit,stop_loss. Validate combinations and protective price relationships. Shorts require operator allow_short flag default false. Persistent protective stops/targets, OCO, partial fills, cancellation/expiry, fees/slippage and actual timestamped marks. Explicit max-fill quantity can model partials; never infer liquidity limits. Local execution is quote-based simulation, not broker/exchange fills.

Per-book operator-only policies: halted+reason, allow_short, optional gross/symbol exposure caps, drawdown alert/brake, fees/slippage. Policy version/hash/history. Defaults never copy historical desk calibration. Halt blocks entries and preserves risk-reducing exits. Exchange-session calendar, fresh marks, documented auction windows, no late replay or automatic fallback without explicit instruction. Broker reconcile every pass: account/positions/open orders; owned client-prefix orphan adoption; external positions marked unknown/locked, never assigned invented sleeves. Failed reads don't corrupt saved truth. Ambiguous submission looked up by client ID before any resend.

Routes: POST /api/books; POST /api/books/{id}/funding; PATCH /api/books/{id}; POST /api/intents; POST /api/intents/{id}/cancel; POST /api/reconciliation. Return durable results. No broker orders submitted during build verification.

## Providers and runtime

`Providers(store)` methods `status()`, `refresh(symbols)`, `bars(symbol,range='1mo',interval='1d')`, `calendar(clock=None)`; `.broker` adapter or None. Refresh persists via Store.ingest_quote and preserves provider timestamps. `ASTER_MARKET_DATA=manual|yahoo|alpaca`, default yahoo. `ASTER_ALPACA_KEY`/`ASTER_ALPACA_SECRET` env only. Broker URL hardcoded https://paper-api.alpaca.markets, no live endpoint option. Adapter methods account(),positions(),orders(),get_order(client_id=...),submit(intent),cancel(order_id). Bounded timeout; redact errors; connected only after successful read. No demo fallback. Historical daily bars do not authorize intraday fills. Calendar library handles NYSE DST/holidays/early close.

`AutonomyRuntime(store,trading,lab,reasoning)` methods start/stop/status/run_once/configure(payload)/schedule(payload)/retry_job(id)/snapshot(). Independently fenced single background loop. Operational automation on by default; no financial side effects without intents. Refresh data, reconcile before execution, process due jobs, publish health and evidence. Durable interval and session jobs (preopen/open/intraday/close/postclose), NY exchange clock; remain due until success, retry with bounded backoff, stamp success only after completion; time-sensitive stale trading windows never replay. Heartbeat, stale-worker, failed-job alerts, post-window order verification, disk capacity gates and SQLite health. Bound network calls and journal volume.

Optional configured LLM on autonomous scheduled briefs with bounded read-only tool use and durable receipts; local agents work without provider and UI distinguishes them. Models cannot select stocks or write order/risk/funding state. Runtime can enqueue existing desk_brief task at configured cadence; existing worker does reasoning and journals calls. Scheduled cycles stay local unless configured brief requested by operational schedule.

Routes: POST /api/autonomy/runtime (running/refresh_seconds); POST /api/autonomy/cycle; POST /api/schedules; POST /api/jobs/{id}/retry; GET /api/market/bars/{symbol}; GET /api/market/calendar.

## Lab and communication

Root lab: append-only local inbox with sender/recipient/topic/body/source/confidence/timestamp, durable reader cursors; acknowledge/resolve alerts; incident records; immutable preregistration and studies registered/running/completed/rejected/archived; source/artifact path/hash/pins; proposals requiring operator decisions and audit. Studies never install strategies. Chief/coordinator, data, accounting, risk, execution and journal/research roles leave actual evidence and handoffs. Execution metrics/equity/stop state/export visible.

Persistent data volume, Docker restart/health and systemd sample. External monitor script + health endpoint; do not claim off-host scheduler installed without chosen host. SQLite-consistent additive timestamped backups, no ledger/inbox/research deletion. Missing research outputs do not freeze trading. Preserve existing accounting tests and add meaningful unattended/partial/short/OCO/idempotency/reboot/calendar/provider tests.

Current additions: versioned portfolio policy via PATCH `/api/portfolio-policy`; immutable history manifests/pages/continuation via `/api/market/revisions/...`; bounded registered research workflows under `/api/research/workflows` with persisted run/node receipts, retries and cancellation fences; approved policy effects require a stage/token guard in the same trading transaction. See the generated API schema for route payloads and FEATURE_IMPLEMENTATION_VERIFICATION.json for exact capabilities and extensions. This equity runtime has no installed strategies or automatic broker cancel/replace protection repair.
