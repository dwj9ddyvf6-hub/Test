# Legacy manual-ledger contract

This document describes the independently retained manual ledger. The current autonomous desk is specified in [AUTONOMY_CONTRACT.md](AUTONOMY_CONTRACT.md) and [ARCHITECTURE.md](ARCHITECTURE.md). Statements below about paused recurring cycles and approval apply only to that manual workflow.

# Aster Desk build contract

User scope: review existing agentic trading desks and build a new desk. **No strategies, signal generators, scanners, stock rankers, allocation policies, indicators or automatic trade decisions are to be added.** Build in `/workspace/agentic-desk`; original research repositories are read-only references.

## Architecture and ownership

- Backend: Python 3.12, FastAPI, SQLite WAL, real durable operational task workers; backend agent owns `backend/`, `tests/`, `requirements.txt`.
- Frontend: React, TypeScript, Vite, responsive professional desk; frontend agent owns `frontend/` including package/config/styles. No fake market prices, performance, activity or positions. Root owns launcher, README, integration, packaging and browser tests.
- App name: **Aster Desk**. Paper workspace only. Zero initial capital, holdings, quotes, trades and strategies. Six operational agents: coordinator, data_steward, accountant, risk_officer, execution_clerk, archivist. These are working desk agents, not strategy workers.
- Reasoning provider is optional: support OpenAI-compatible chat completions using `ASTER_LLM_BASE_URL`, `ASTER_LLM_MODEL`, `ASTER_LLM_API_KEY` environment variables, only on explicitly submitted brief/note tasks. Local operational workers function without it. The UI must show whether reasoning is connected and distinguish local automation from model reasoning. No external call without configuration; no built-in credential or live broker adapter.
- SQLite records tasks, steps, leases/attempts, settings, quotes, watchlist, account funding, order intents, fills, positions, events and equity snapshots. Money uses Decimal/integer cents internally. Account writes and reservations are atomic. Append-only event history carries actors and timestamps.

## HTTP contract

All paths start `/api`. JSON errors use `detail` (string or validation list); success returns the created/updated resource or a snapshot. UI refreshes `GET /desk` after writes and periodically while workers run. Dates are UTC ISO8601. Monetary and quantity fields return JSON numbers; IDs are strings unless event row IDs are integers.

### GET /desk

```ts
interface DeskSnapshot {
  desk: {
    name: string; mode: 'paper'; strategy_count: number;
    runtime: {running: boolean; last_cycle_at: string | null; heartbeat_at: string | null};
    reasoning: {provider: 'local' | 'openai-compatible'; configured: boolean; model: string | null};
  };
  account: {currency: 'USD'; cash: number; equity: number; market_value: number;
    reserved_cash: number; available_cash: number; realized_pnl: number;
    unrealized_pnl: number; missing_marks: number};
  positions: Array<{symbol: string; quantity: number; average_cost: number;
    mark_price: number | null; market_value: number; unrealized_pnl: number;
    realized_pnl: number; quote_fresh: boolean}>;
  orders: Array<{id: string; client_id: string; symbol: string; side: 'buy' | 'sell';
    quantity: number; type: 'market'; status: 'pending_review' | 'filled' | 'cancelled' | 'rejected';
    created_at: string; filled_at: string | null; fill_price: number | null; reason: string | null}>;
  fills: Array<{id: string; order_id: string; symbol: string; side: string;
    quantity: number; price: number; notional: number; timestamp: string; source: string}>;
  agents: Array<{id: string; name: string; role: string; status: 'idle' | 'working' | 'error';
    last_run_at: string | null; last_result: string | null; capabilities: string[]}>;
  tasks: Array<{id: string; kind: string; title: string;
    status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
    created_at: string; started_at: string | null; completed_at: string | null;
    result: string | null; error: string | null;
    steps: Array<{id: string; agent_id: string; title: string; status: string; result: string | null}>}>;
  watchlist: Array<{symbol: string; added_at: string;
    quote: {symbol: string; price: number; as_of: string; source: string; fresh: boolean} | null}>;
  events: Array<{id: number; event_type: string; actor: string; timestamp: string; message: string; payload: object}>;
  equity_history: Array<{timestamp: string; equity: number; cash: number}>;
  settings: {quote_max_age_seconds: number; heartbeat_seconds: number; cycle_interval_seconds: number};
  connections: {market_data: {kind: 'manual'; status: string}; broker: {kind: 'paper'; status: string};
    reasoning: {provider: string; configured: boolean; model: string | null}};
  strategy_slots: [];
}
```

### Mutations

- `POST /account/funding` `{amount: number, client_id: string}` — positive paper-cash deposit, idempotent; no fabricated return. Zero initial funding. Funding cannot occur from an agent.
- `POST /watchlist` `{symbol: string}`; `DELETE /watchlist/{symbol}`. Uppercase canonical equities symbols, permit dot/dash where valid. No price lookup implied.
- `POST /quotes` `{symbol: string, price: number, as_of: string, source: string}` — positive price, timezone-aware timestamp, known age. Reject future timestamps beyond a small clock tolerance and out-of-order updates. Explicit manual provenance. Watchlist membership can be created on ingestion.
- `POST /orders` `{symbol: string, side: 'buy'|'sell', quantity: number, type: 'market', client_id: string}` — explicit human paper-order intent; create `pending_review`, reserve cash or sell quantity; require fresh quote and enough available cash/shares. Idempotent client identity with mismatched reused payload rejected. Concurrent requests cannot overcommit funds/shares.
- `POST /orders/{id}/approve` `{}` — explicit operator approval; recheck quote freshness, cash/shares/reservations atomically and fill paper order at available manual quote. No fictitious broker bid/ask/partial fill. Repeat approval is idempotent. Failed rechecks do not mutate holdings. A pending order can be cancelled.
- `POST /orders/{id}/cancel` `{}` — release reservation, preserve intent/history; filled orders cannot be cancelled.
- `POST /tasks` `{kind: 'desk_brief'|'data_audit'|'reconcile'|'research_note', title?: string, instructions?: string, symbol?: string}` — persistent operational workflow; accept user notes and evidence, no strategy prompt compiler. Execute with a bounded real background worker even if recurring runtime is paused. Return task. Enforce input bounds and valid kind.
- `POST /tasks/{id}/cancel` `{}` — cancel queued task; prevent future steps of running task.
- `POST /runtime/cycle` `{}` — enqueue one six-agent operational cycle and return task; idempotent while an equivalent cycle is pending/running.
- `POST /runtime` `{running: boolean}` — start/pause recurring operational cycles. Paused on first launch. Manual queued work still executes. Pause stops new recurring cycles; a running step finishes with its history preserved.
- `PATCH /settings` accepts bounded positive `quote_max_age_seconds`, `heartbeat_seconds`, `cycle_interval_seconds`.
- `GET /strategies` returns `[]`.
- `GET /health` returns truthful worker/database/provider health, not market or broker reachability claims.
- `GET /export` downloads all desk-owned state as JSON (no environment secrets).

## Operational agent behavior

A cycle passes durable results through Data steward → Accountant → Risk officer → Execution clerk → Coordinator → Archivist. Data steward audits manual quote age and coverage. Accountant independently reconciles funding and fills to cash and positions and records a balance snapshot. Risk officer reports actual reservations, exposure and stale/missing marks, with no entry/exit recommendations. Execution clerk reviews pending paper intents and reports explicit operator actions needed, without approving them. Coordinator composes a factual operational brief (local by default; optional configured model for explicitly requested brief/note). Archivist journals completion and preserves the task/result. Notes preserve supplied source text and symbols rather than inventing findings.

Tasks have restart recovery, fenced leases or equivalent single-worker exclusion, bounded attempts, visible failures and idempotent effects. Tests must cover durable restart, task handoffs, zero strategies/no orders from cycles, funding/order idempotency, oversubscription, partial liquidation/realized P&L, stale-price rejection, cancellation/reservation release, and failed quote updates.

## Interface

Clean professional visual system: restrained off-white workspace, dark sidebar, ink typography, violet accent, monospaced financial figures. Sections Overview, Agent team, Work queue, Watchlist, Paper book, Journal, Controls. Real empty states with meaningful actions. Header shows Paper mode, worker state, and empty strategy count. Buttons/forms support capital funding, watchlist, manual quote, operator paper order, explicit approval/cancellation, new task, one cycle, runtime start/pause, and JSON export. Task detail shows actual ordered agent steps and results. Agent actions route real tasks. Error/loading feedback, accessible dialogs/form labels, mobile layout. No demo trades/data on default startup and no disabled fake connection buttons.

For dev Vite proxies `/api` to port **8787**. UI port **5173**. For production the FastAPI app serves `frontend/dist` when built. Root creates a one-command launcher and verifies the actual interface in Chromium.
