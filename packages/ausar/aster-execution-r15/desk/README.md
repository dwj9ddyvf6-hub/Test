# Aster Desk

A functional autonomous **paper** trading desk built from **Femto/Midna, Cursor and GrokBot**. It has a resident supervisor, independent books, durable execution, price/bar archives, research collection, agent reviews and an operator interface.

Fresh installations start with **zero installed strategies, capital, positions, and instructions**. The explicitly installed Tensor suite adds four frozen deterministic sleeves—**H1STATE, WSTATE, D20PV, and D20TENSOR**—in separate local paper books. It may originate orders only within those supplied rules. Research, inbox messages, and optional reasoning-model output have no financial write authority. Local fills are observed-quote simulations with configured costs. The separate optional broker adapter connects exclusively to Alpaca's paper endpoint; Tensor sleeves use no broker-order submission.

## Run

Requires Python 3.12+, Node.js 20.19+ and npm.

```bash
cd /workspace/agentic-desk
./run.sh
```

On another machine, use the extracted project directory. Open **http://127.0.0.1:8787**. The launcher installs dependencies, builds the interface and starts FastAPI. State persists in `data/aster.sqlite`; closing the browser does not stop the worker. Stopping this process stops the desk. For persistent host operation, use the supplied Docker Compose configuration or systemd example.

Copy [.env.example](.env.example) to `.env` for optional configuration, then restart. Default market data is Yahoo public data. Source timestamps and delay status remain visible; stale or historical marks do not become fresh execution prices. `ASTER_MARKET_DATA=manual` disables network market-data collection. `ASTER_DB_PATH`, `ASTER_PORT` and `ASTER_HOST` override storage and binding.

## Install and operate the four Tensor paper sleeves

**The desk completed autonomous local-paper entries in the actual 15:30–15:35 UTC window on 2026-10-09.** The complete 1,820-name hourly census reached the unchanged 99% known-coverage gate at **15:34:39.484966 UTC**, 20.515034 seconds before the unchanged deadline: 1,796 ready, six verified ineligible and 18 individually blocked failures. Ten of 65 ranked opportunities filled through normal local-paper execution; 55 were denied by the ten-slot limit. The independent actual-execution audit passed **262 checks**, and the consistent operating-state archive is verified. All four independently funded sleeves remain enabled. This demonstrates the hourly entry pipeline; completed 20-bar exits, daily/weekly opening execution, profitability and QQQ outperformance remain unproved. Earlier misses and failed/cutoff rehearsals are preserved.

The owner authorized converting the R11 research into an executable strategy and then requested all four sleeves. Read [Tensor rules and operations](docs/TENSOR_SLEEVES.md) before installation. Each sleeve has its own funding, holdings, pending orders, T+1 spendable-cash ledger, decisions, and performance record. Shared market observations do not combine the books' money or rankings.

Install the named deployment in an explicit database, then use that same database for the resident desk:

```bash
export ASTER_DB_PATH="$PWD/data/tensor-paper-r12.sqlite"
export ASTER_ACTIONS_CREDENTIALS_FILE=/path/to/private/alpaca-readonly.json
.venv/bin/python -m backend.tensor_cli install --seed-directory data/research-seed-r11/native-inputs --enable
.venv/bin/python -m backend.tensor_cli status
.venv/bin/python -m backend.tensor_cli run
./run.sh
```

Before expecting action-covered entries and payments, configure the required read-only corporate-action access in a private local JSON file containing `key` and `secret` strings, and point `ASTER_ACTIONS_CREDENTIALS_FILE` to it. Keep that environment for the resident process. The adapter reads metadata through GET requests; Tensor sleeves never submit Alpaca orders. Keep credentials outside the source, research archive and exported operating state. Missing or unresolved action evidence can block affected entries and comparable performance.

`install` verifies the complete pinned research seed, frozen engine, and model assets, then explicitly creates/funds four dedicated local paper books with **$100,000 virtual principal each**. Funding is idempotent. `--enable` enables entry evaluation; without it, the installed entries stay disabled. Application construction does not perform this installation. The command also accepts `--db PATH` **before** `install`, `status`, or `run`; otherwise it uses `ASTER_DB_PATH` or `data/aster.sqlite`. The seed must first be restored from its immutable research cache. Final installation and finite verification receipts identify the actual database and enrolled universe; installation alone does not establish provider connectivity or trading readiness.

`status` reports installed sleeves, enabled flags, enrolled-universe coverage, native-data cycle readiness, pending intents, and owned positions. The strategy catalogue exposes decision receipts. The full enrolled census must be attempted; the explicit forward missing-data policy can block unavailable names individually and permit healthy candidates only with at least 99% valid or verified-ineligible coverage. The strict complete-enrollment policy is also available. Known inactive names stay in enrollment with pinned status evidence. Insufficient history, missing canonical daily anchors, mass provider failure, an unfinished census, or a missed opening window can block an enabled book. CLI `run` executes **one explicit fenced supervisor cycle**, including an operator-requested cycle when globally paused; it is not a resident daemon. `./run.sh` keeps the automatic one-second strategy schedule operating while its process and global runtime run. Stopping the process stops scheduling.

The main pre-start receipts recorded four enabled books at $100,000 each, an idempotently verified research seed, zero positions/pending intents, no broker orders, and `worker_alive=false`. The subsequent `MAIN_DESK_ACTIVATION.json` observed the resident service at **13:16:05 UTC on 2026-10-09**, at `http://127.0.0.1:8787`, with `runtime_running=true`, `worker_alive=true`, and all four installations. The current native census was warming. This establishes resident activation; a timely complete live census, actual forward fill, and profitable forward result each require their own later observation.

Hourly acquisition runs first and the decision clock advances between frames. While hourly sleeves are installed, the worker defers broad daily/weekly acquisition throughout the hourly opening window and during the 60 seconds before an immediate hourly boundary. This priority remains in force after hourly buys are queued, so normal fill processing can run before unrelated scans. Already completed cached daily/weekly censuses may still allocate at their eligible opening, and owned exits remain serviced. A cold install must prewarm its full daily/weekly census before the shared 09:30 opening; an unprepared book stays blocked rather than selecting from a partial roster.

The retained source-only 1,820-name hourly computation took **277.316 seconds**. A later full-manager source-fixture benchmark took **255.033 seconds**, or **262.033 seconds** after seven one-second intertick gaps, with a synthetic 1.2-second delay per read. It timed the full 1,820-name seed/hash/calendar/native/cache/database/census path, with entries disabled and zero intents/fills. Its original runtime pin is `647b3f5ce8508a6854fdb28a2034b35a129d2af9b6faec84730901885adfbf5a`, before the final unrelated-acquisition coordinator change. Keep each earlier receipt's source identity unchanged. These measurements exclude actual live vendor availability and action/quote/fill work; they show fixture capacity, not a completed current market-opening census or profitability.

The strategy API includes `GET /api/strategies`, `GET /api/strategies/catalogue`, `POST /api/strategies/install`, `POST /api/strategies/run`, and `PATCH /api/strategies/{id}` with `{"enabled": false}` to pause **new entries**. Owned exits continue to be processed while the runtime is operating. The HTTP run route queues work and reports `runtime_running`; it does not override a global pause or promise an immediate fill. Exact route schemas are exposed through `/docs` and the Tensor deployment receipt.

Hourly and weekly state repair use the same native seven-channel repair predicate; the two daily 20-bar models keep their original artifacts, medians, thresholds, feature order, and source-index sampling phase. All sleeves hold for 20 **observed native bars**, use whole shares, at most ten positions, 10% new-position equity and 1% signal-native-dollar-volume caps, and independent settled cash. Forward entries use fresh observed local-paper quotes within the bounded next-opening window, rather than fabricated historical opening prices. Native ingestion retains the immutable prefix, audits ordinary overlapping vendor corrections, and appends true completed periods; extra quote stubs do not become feature bars. A cached partial candle requires an actual post-close fetch, with usable time no earlier than its completion, first observation, or latest fetch. These availability/receipt/ingestion choices are disclosed forward execution differences. No profit target, stop, learned winner basket, or model refit is added, and original research returns are not claimed for the changed current-provider regime.

Corporate-action accounting implements evidenced atomic split adjustments, stale-order cancellation, and nonspendable ex-dividend receivables. Independently matched Alpaca declared payment metadata can release local paper dividend cash at the later payable/process date's 09:30 New York convention after actual observation; Yahoo establishes the USD listing. This simulates paper payment and does not claim broker money was received. Fractional cash-in-lieu remains unresolved until a trusted measured payment, and unresolved action coverage withholds comparable performance. Known post-seed splits also block new native-feature entries pending source-basis review. Raw-price benchmarks are not relabeled validated total return.

The automatic `benchmark-history` schedule archives daily QQQ and SPY observations. Strategy-owned NAV comparisons require matching vendor adjusted-close benchmark series and clean, aligned closing valuations; a raw-close series cannot stand in for a distribution-inclusive account comparison. Missing benchmark/action/valuation evidence withholds comparable returns and excess-return metrics. This reporting requirement does not change the frozen entry predicates or turn the raw-open historical research into a total-return study.

## Container deployment

The supplied container packaging includes Node 22 and the frozen `strategies/` assets in its Python/Bookworm runtime. Compose stores the database and external seed in the private `desk-state` volume mounted at `/data`. Restore and verify the exact seed from the host or an authenticated external restoration step, then provision it into `/data/research-seed-r11/native-inputs` before installation and use that explicit path. The host CLI default points into the application directory. The image does not ship `gh` or GitHub authentication; presence of the restorer script is not evidence of authenticated in-container restoration. Optional GET-only action credentials belong at `/data/alpaca-readonly-credentials.json`, or the container path supplied by `ASTER_CONTAINER_ACTIONS_CREDENTIALS_FILE`. Credentials are external data, not part of the image or research archive. Missing optional action reads keep unsupported payments unresolved.

```bash
docker compose build desk
docker compose run --rm desk python -m backend.tensor_cli install --seed-directory /data/research-seed-r11/native-inputs --enable
docker compose up -d desk
```

The full image build in this workspace was deliberately stopped at the filesystem reserve to preserve space for the resident desk. The separate **offline thin-container runtime check passed at 15:17:43 UTC**, bound to repaired runtime `27c3b260` and provider `9bbff46e`, with Python 3.12.15 and Node 22.23.3. It matched all 93 native columns in three frame fixtures, confirmed full/fast operand parity, verified frozen assets/anchors and matched 32 daily prediction probes. It performed no market requests, installation, funding, financial trials or broker orders. This bounded check assembled the actual Node binary, built UI and read-only sources/assets in an existing Python container. Its empty CLI status had zero installed sleeves and no live worker. It does not certify a completed full-image build, authenticated seed restoration or persistent mounted-volume installation.

## Operate

1. Create independent main, context, forward or shadow books. Fund local books explicitly. Broker books use the configured paper account's actual balances.
2. Add symbols to the watchlist. Inspect source timestamps, quote history, bar revisions, exchange sessions and the chart workspace.
3. Supply a paper instruction with symbol, side, quantity, order type, time in force and optional stop/target. The supervisor executes it when price, session, policy and reconciliation conditions permit. These autonomous-book instructions need no second approval.
4. Monitor reservations, signed positions, partial fills, OCO protection, cancellations, policy history, reconciliation and job receipts. A halt blocks entries while preserving risk-reducing exits.
5. Use Inbox, Research Lab and Agent Team for factual handoffs, source collection, immutable study registration, results, artifacts, incidents and bounded reviews. Policy trials require an operator decision and explicit application; an approved rollback guard preserves newer operator policy.

The separate **Manual ledger** retains an explicit approve-before-fill workflow. Its capital and positions are independent of autonomous books.

## Implemented infrastructure

- Fenced background supervision; persistent interval and NYSE session jobs; heartbeat, retries, missed-window evidence, restart recovery and journal-integrity gates.
- Local equity paper execution and separately bound Alpaca paper accounts; pre-submit identities, lookup before retry, fill-confirmed accounting, partials, signed holdings, reservations, persistent stop/target/OCO and ownership-aware reconciliation.
- Actual quote/bar collection, immutable revisions, paginated history and observation provenance, provider health, exchange calendars, cashflow-aware performance and aligned QQQ/SPY comparisons when sufficient clean samples exist.
- Six operational roles plus optional independent model reviews for risk, coordination and journal coaching. Bounded tools are read-only; completed reviews produce receipts, artifacts and local inbox messages.
- Autonomous watchlist news collection; optional SEC filing receipts; read-only repository catalogue search; durable registered research workflows; immutable study hypotheses/methods/controls/source pins and append-only results.
- Tape-linked reviews, alerts, incidents, portfolio-wide exposure caps, versioned policy trials/rollback, curated public projection and state export.
- Durable notification outbox, in-app notices, optional webhook, Typefully drafts/media and browser push. External delivery requires explicit configuration and enabling. Ambiguous sends require resolution.
- Additive SQLite-consistent backups, heartbeat monitor, Docker restart/health settings and a systemd example.

The four Tensor sleeves bind retained native source, frozen model artifacts, and their R11 reference books. Their source-bound research returns are documented separately from forward paper execution. General strategy candidates retain an interface for source/data pins, pre-registration, training/holdout boundaries, cost assumptions and QQQ/SPY benchmark identity. An automatic alpha search engine, walk-forward optimizer, options/multi-leg execution and full fundamental valuation model remain **extension work**. Historical leads do not guarantee future profitability or QQQ/SPY outperformance.

## Optional connections

- **Reasoning:** `ASTER_LLM_BASE_URL`, `ASTER_LLM_MODEL`, `ASTER_LLM_API_KEY`. `ASTER_LLM_MULTI_AGENT=true` enables separate risk/coordinator/journal reviews. Local operations work without a model. Configuration and successful responses are distinct.
- **Alpaca paper:** `ASTER_ALPACA_KEY`, `ASTER_ALPACA_SECRET`. Named connections use `ASTER_ALPACA_ACCOUNTS=research,forward` and corresponding `ASTER_ALPACA_RESEARCH_KEY` / `_SECRET`, etc. One book per actual account binding prevents mixed ownership. No broker orders were submitted during this build.
- **SEC:** `ASTER_SEC_USER_AGENT` identifying the requester. Failed collections remain failures.
- **Research catalogue:** `ASTER_RESEARCH_INDEX=/workspace/github-review/catalogue/research-index.sqlite` in this workspace. The large catalogue is a separate artifact, outside this application's package.
- **Notifications:** see `.env.example` and Operations. Provider configuration alone does not enable delivery or replay past events.

## Verification and evidence

The [full code audit and repair report](docs/FULL_AUDIT_REPORT.md) records the earlier pinned financial, runtime, agent/research, analytics, notification, UI/API and recovery inspection. Its [code manifest](docs/AUDIT_CODE_MANIFEST.json) identifies the exact reviewed files and functions. It does not retrospectively verify the new Tensor code. The Tensor deployment carries its own source, native/model parity, rule, accounting, runtime, and interface receipts; see [Tensor rules and operations](docs/TENSOR_SLEEVES.md). The frozen repaired whole-backend run passed **495 tests in 35.167 seconds**; the independent source-bound audit passed **171 Tensor tests and 15 harnesses**. These finite checks add no retrospective financial trials or fitting; actual opening capacity and forward results have separate receipts. Main resident activation was separately observed; current census readiness and actual forward performance are reported by their own observations. Earlier delivery and feature receipts retain their original scope.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

```bash
cd frontend
npm run typecheck
npm run build
```

[Desk review](docs/DESK_REVIEW.md) identifies source roots and freshness limits. [Operations](docs/OPERATIONS.md) covers persistent hosting, backup and restoration. [Architecture](docs/ARCHITECTURE.md) explains persistence, execution and research authority. [Integration contract](docs/AUTONOMY_CONTRACT.md) documents module/API boundaries. [Feature verification](docs/FEATURE_IMPLEMENTATION_VERIFICATION.json) separates implementation, configuration and extensions. The running API schema is at `/docs`.

Tests use isolated databases and simulated broker transports. Browser checks also use isolated databases; default project capital/instructions remain empty. Host supervision examples are supplied, not remotely installed. The service defaults to localhost and is a single-operator workspace application.

The tested Python dependency set is pinned in `requirements-lock.txt`. The launcher and Docker image use that file; `requirements.txt` declares the supported direct dependency ranges. Historical daily fallback to Stooq is implemented, but its live availability was not verified in this environment. Immutable history pages state provider completeness and provisional finality; they do not promise final vendor data. Automatic cancel/replace repair of missing broker protection remains an explicit extension.
# Additional public-rule paper sleeves

Three separately owned daily ETF sleeves extend the four Tensor installations: Donchian 55 trend, RSI(2) pullback, and modern BB/KC squeeze. Their [frozen rules and execution contract](docs/TRADER_SLEEVES.md) explain source adaptations, next-opening execution, position/risk sizing, owned exits, and validation limits. Run `.venv/bin/python -m backend.trader_cli install --enable` only as the explicit operator installation and virtual-funding action; the application still starts empty on a new database. These are executable paper research candidates. Their historical testing does not establish QQQ or SPY outperformance.

