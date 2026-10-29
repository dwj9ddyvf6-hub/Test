export type TaskKind = 'desk_brief' | 'data_audit' | 'reconcile' | 'research_note';
export interface AccountingCoverage {
  status: 'known' | 'withheld'; reason?: string; method?: string;
  required_evidence?: string; source?: string; observed_at?: string;
}
export interface AutonomousAccount {
  cash: number; equity: number; realized_pnl: number | null; unrealized_pnl: number | null;
  realized_pnl_coverage: AccountingCoverage; unrealized_pnl_coverage?: AccountingCoverage;
}
export interface AutonomousPosition {
  book_id: string; symbol: string; quantity: number; average_cost: number | null; cost_basis: number | null;
  cost_basis_coverage: AccountingCoverage; realized_pnl: number | null; unrealized_pnl: number | null;
  realized_pnl_coverage: AccountingCoverage; mark_price: number | null; quote_fresh: boolean;
}
export interface AutonomousFill {
  id: string; book_id: string; quantity: number; price: number; fee: number;
  observed_at: string; source_timestamp: string | null; realized_cents: number | null;
  realized_pnl: number | null; realized_pnl_coverage: AccountingCoverage;
}
export interface Agent {
  id: string; name: string; role: string; status: 'idle' | 'working' | 'error';
  last_run_at: string | null; last_result: string | null; capabilities: string[];
}
export interface Task {
  id: string; kind: string; title: string; status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string; started_at: string | null; completed_at: string | null; result: string | null; error: string | null;
  steps: {id: string; agent_id: string; title: string; status: string; result: string | null}[];
}
export interface Order {
  id: string; client_id: string; symbol: string; side: 'buy' | 'sell'; quantity: number; type: 'market';
  status: 'pending_review' | 'filled' | 'cancelled' | 'rejected'; created_at: string; filled_at: string | null;
  fill_price: number | null; reason: string | null;
}
export interface DeskSnapshot {
  desk: { name: string; mode: 'paper'; strategy_count: number;
    runtime: {running: boolean; last_cycle_at: string | null; heartbeat_at: string | null};
    reasoning: {provider: 'local' | 'openai-compatible'; configured: boolean; model: string | null}; };
  account: {currency: 'USD'; cash: number; equity: number; market_value: number; reserved_cash: number;
    available_cash: number; realized_pnl: number | null; unrealized_pnl: number | null; missing_marks: number};
  positions: {symbol: string; quantity: number; average_cost: number | null; mark_price: number | null;
    market_value: number; unrealized_pnl: number | null; realized_pnl: number | null; quote_fresh: boolean}[];
  orders: Order[];
  fills: {id: string; order_id: string; symbol: string; side: string; quantity: number; price: number;
    notional: number; timestamp: string; source: string}[];
  agents: Agent[]; tasks: Task[];
  watchlist: {symbol: string; added_at: string; quote: {symbol: string; price: number; as_of: string;
    source: string; fresh: boolean} | null}[];
  events: {id: number; event_type: string; actor: string; timestamp: string; message: string; payload: object}[];
  equity_history: {timestamp: string; equity: number; cash: number}[];
  settings: {quote_max_age_seconds: number; heartbeat_seconds: number; cycle_interval_seconds: number};
  connections: {market_data: {kind: 'manual'; status: string}; broker: {kind: 'paper'; status: string};
    reasoning: {provider: string; configured: boolean; model: string | null}};
  strategy_slots: [];
}
