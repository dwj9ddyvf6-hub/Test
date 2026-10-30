# Repository instructions for LLM agents

For strategy, market-data, research, trading, or deployment work:

1. Read [docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md](docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md), this repository's README, [docs/CATALOG.json](docs/CATALOG.json), and [docs/VERIFY.md](docs/VERIFY.md).
2. Read and follow any narrower AGENTS.md under the package or code path you will touch. Do not treat a historical package as the current runtime without checking its provenance and version.
3. Trace a strategy from card to exact source, configuration, adapter, tests, state owner, and execution boundary. Distinguish research-only, local simulation, broker paper, and live.
4. Keep LLM and research outputs read-only by default. Route any explicitly permitted action through deterministic authorization, data, risk, idempotency, and audit controls.
5. Preserve source timestamps, first receipt times, usable times, provider/feed identity, adjustment basis, official session boundaries, and explicit missing/stale/blocked states. Never fabricate observations or silently change feeds.
6. Preserve book ownership, ledger state, orders, positions, and exit obligations across restarts and strategy disable.
7. Never commit secrets, private account data, or user-specific financial state. Do not enable a broker, fund a book, or submit an order from this catalog repository without explicit authorization for that action and verified runtime/account context.
8. Verify the final file/commit and report evidence separately from assumptions. Do not claim strategy profitability from implementation or test success.

These are repository-wide guardrails. More specific nested instructions apply within their paths and may add constraints.
