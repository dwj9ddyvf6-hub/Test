# Full desk audit and repairs

The entire first-party Aster Desk implementation was inspected and the confirmed defects were repaired. The final source passes **320 tests in two independent complete runs**, the production frontend builds, the browser workflows pass, and the final container preserves its database across restart and recreation. The actual desk was restarted with the repaired code and its existing financial state intact.

Audit date: **8 October 2026, UTC**. Baseline: local release `32f6f14dccd1e8831f7ba276da037e8490e2ebf8`. The release ZIP records the audited commit and a hash for every packaged file. This is a functional correctness and reliability audit of the desk built from Femto/Midna, Cursor and GrokBot.

## Inspection coverage

The [code manifest](AUDIT_CODE_MANIFEST.json) inventories the final files, hashes, lines, Python classes/functions including nested bodies, and TypeScript/JavaScript functions. It distinguishes application code, tests, configuration, historical evidence generators and compiled assets. Area reports identify the reviewed bodies, defects, repairs, regressions and remaining integration limits.

| Area | Detailed report | Recorded repair groups |
| --- | --- | ---: |
| Money, positions, reservations, broker receipts and journal | [Financial](AUDIT_FINANCIAL.json) | 12 |
| Supervisor, scheduling, provider adapters and market archives | [Runtime](AUDIT_RUNTIME.json) | 19 |
| Agent roles, reasoning, worker leases, research and policy trials | [Agents and research](AUDIT_AGENTS_RESEARCH.json) | 16 |
| Returns, benchmarks, episodes and history scaling | [Analytics](AUDIT_ANALYTICS.json) | 7 |
| Notification claims, receivers, retries and delivery receipts | [Notifications](AUDIT_NOTIFICATIONS.json) | 16 |
| HTTP routes, state export, all eleven views and browser behavior | [Frontend and API](AUDIT_FRONTEND_API.json) | 13 |
| Backup, restore, monitoring, launcher, deployment and shared HTTP | [Operations](AUDIT_OPERATIONS.json) | 5 |
| Independent adversarial recheck of critical repairs | [Independent recheck](AUDIT_INDEPENDENT_RECHECK.json) | Four cross-check findings, all repaired |

The first seven reports contain 88 repair groups. These include overlapping and joint repairs; this is **not a count of 88 distinct bugs**. Independent recheck findings overlap those reports. Every confirmed finding is repaired; the independent reviewer reports no remaining confirmed finding.

Historical source comparisons and previous delivery receipts remain preserved and labelled as pre-audit evidence. Their historical test counts and line references do not replace the final manifest. Third-party dependency implementations and generated font/bundle bodies are outside the first-party code inspection; the locked dependencies and production assets were built and exercised.

## Material repairs

**Accounting and execution.** Pending limit and stop liabilities now participate in reservations and exposure caps. Signed integer-cent limits are checked before ledger effects, preventing overflow and partial accounting. Broker receipts must match the exact owned instruction before advancing cumulative fills; stale statuses cannot reopen terminal orders. Exact cumulative source notional is retained separately from rounded money, so a measured sub-cent increment can legitimately advance quantity without inventing a cent of cash. Native protection cannot increase quantity without authorization. Local accounting follows durable append order when wall clocks move backward.

Broker order-level snapshots cannot establish a complete, ordered execution tape. Public broker realized P&L is therefore withheld, and position basis/unrealized P&L are shown only when supported by a matching complete recorded source position snapshot that has not been superseded by later fill receipts. Coverage reasons appear in the API and interface. Historical raw reconstruction estimates remain preserved and labelled in export. Manual daily historical bars cannot authorize intraday fills. Concurrent journal verification now scans and publishes its checkpoint atomically.

**Autonomous operations and data.** Pauses, schedule disablement, leases and shutdown are rechecked at execution boundaries, including inside local financial transactions. Session cursors persist bounded catch-up progress and record expired known windows without replaying them. Runtime interval changes update next due times. Open broker orders are separately censused and merged with recent history; an incomplete bounded census reports failure. Malformed vendor responses are contained per symbol. Immutable archive payloads, hashes, metadata, timestamps and OHLC/volume are validated; corrupt cache state cannot silently become an acceptable fallback. Recovered runtime incidents resolve through the coordinator without fabricating operator acknowledgements.

**Agents, research and policy authority.** A worker cannot re-enter its own active tick, duplicate model handoffs or renew expired/cancelled ownership. Shutdown retains ownership until active work exits. Failed research DAG retries cannot overlap a newer active run. Atom feeds are parsed, nested parameters are validated, and model output/tool messages retain valid bounded JSON. Policy application and rollback use the actual committed actor/token/history identity, preserving newer operator changes even when a response fails after commit. Reopened alerts clear obsolete acknowledgement state. Model, provider, research and notification transports share bounded HTTP behavior.

**Analytics.** Benchmark selection uses verified immutable revisions with the best common valuation coverage; viewing a short chart cannot shrink a previously available comparison. Corrupt benchmark payloads, ambiguous funding boundaries and unknown broker accounting produce explicit withheld results. Pre-calendar vendor history remains archived without breaking desk reports. Clock reversals preserve causal money while withholding invalid time-based statistics. Timestamp indexing and session memoization remove repeated history scans. A 21,021-row synthetic probe retained identical metrics and ran in 0.225 seconds versus 7.078 seconds on the baseline in that measured run.

**Notifications and network behavior.** Atomic claims cannot resurrect paused or cancelled items. New/resumed subscriptions start from their future-event boundary. Receiver changes fence pending messages from the old audience. Backoff starts at completion, attempt limits are enforced, and ambiguous non-idempotent sends remain unresolved rather than automatically replayed. Delivery receipts disclose truncation and media integrity. WebPush uses real encryption through the same bounded transport. Four bounded daemon resolver workers prevent queued DNS growth and interpreter shutdown delays; cancellation prevents a late lookup from initiating a later HTTP send. Deadlines apply to each HTTP operation, with bounded cancellation cleanup; they do not assert a hard deadline for a whole multi-stage desk cycle.

**API, interface and recovery.** Startup/shutdown cleanup survives a worker failure. Raw export is one database read snapshot, with derived views identified separately. Book policy forms use compare-and-swap hashes, worker status refreshes on every view, charts keep symbols aligned with their data, and collection responses cannot be overwritten by stale reads. Timed-out writes instruct the operator to refresh before retrying. Service-worker malformed push data and failed browser subscription cleanup are handled. Restore validates and publishes the exact receipted private copy, ignores unreceipted backup WAL and preserves concurrently appearing destination state. Health probes evaluate worker progress, database and journal gates. The launcher reinstalls frontend dependencies when its lock receipt changes.

## Final verification

| Check | Result and evidence |
| --- | --- |
| Baseline complete suite | 194 passed; [baseline log](verification/audit-baseline-tests.log) |
| Final complete suite | **320 passed**, 10.230 seconds; [final log](verification/audit-verified-tests.log) |
| Independent final complete suite | **320 passed**, 8.867 seconds; all 29 Python source/test hashes unchanged during verification; [receipt](verification/audit-independent-final-tests.json), [log](verification/audit-independent-final-tests.log) |
| Additional regression methods | 126 added across money, runtime, agents, analytics, notifications, HTTP and recovery |
| Malformed API input probe | **222 cases, zero HTTP 500 responses**; [receipt](verification/audit-validation-probes-final.json) |
| Frontend typecheck and production build | Passed; [build receipt](../frontend/build-receipt.json); final `index-CHhv1Bb5.js` / `index-Sdmf3nfc.css` |
| Integrated browser operations | **16 workflow groups**, no JavaScript errors; [receipt](verification/audit-integration-browser-qa-receipt.json) |
| Targeted browser/client/service-worker behavior | **12 groups**, including all eleven desktop views and mobile navigation; [receipt](verification/audit-frontend-api-results.json) |
| Accounting interface follow-up | **Four groups**, including withheld broker basis/P&L and known local fees/timestamps; [receipt](verification/audit-broker-accounting-ui-results.json) |
| Independent original defect probes | All four pass on final hashes; [receipt](verification/audit-independent-final-probes.json) |
| HTTP deadline/resource probes | Streaming response, DNS cancellation, resolver saturation/recovery, response limits, redirect/status handling and subprocess shutdown pass; [independent receipt](verification/audit-independent-http-resources.json) |
| Final Docker image | Build passed; image `sha256:d1b0bd385b993156d4ff992eb9894b54408e06004d8ced83bb20f6c6e36b9683`; [build log](verification/audit-docker-build-final.log) |
| Container operations | Healthy workers/database/journal and Docker healthcheck; explicit isolated $125.50 paper funding survives restart and removal/recreation; zero intents/fills/strategies; [receipt](verification/audit-docker-final-receipt.json) |
| Restarted actual desk | Health and monitor pass, catalogue available, financial state preserved; [receipt](verification/audit-live-repaired-receipt.json) |
| Preserved database backup | Additive SQLite-consistent backup with integrity/hash receipt before restart; [receipt](verification/audit-pre-restart-backup.json) |
| Syntax and dependencies | Python compilation, shell syntax, `git diff --check` for code/configuration/prose (raw logs preserved), dependency consistency and JSON parsing pass |

The 16 + 12 + 4 browser checks are grouped, partly overlapping checks rather than 32 independent unit tests. Financial/provider/model/notification mutations ran against isolated temporary databases and explicit fixtures. Network regressions contacted local loopback servers. Actual market archives were inspected read-only. No broker order, configured model request or external notification was sent during this audit.

The actual desk remains at `http://127.0.0.1:8787`. Its main local book still has $0.00 cash, zero positions, zero intents and zero fills. Background workers can continue recording ordinary operational receipts. No strategy was installed and no initial capital was invented. The research catalogue remains separately connected; its large database is outside the application ZIP. Temporary QA containers were stopped and removed while their evidence/databases were preserved separately.

## Evidence boundaries

This inspection and regression work is not a formal proof that every possible defect is absent. Real configured broker, model, SEC and external notification integrations still need deployment-specific end-to-end validation; simulated protocol fixtures do not establish provider availability. Broker full activity/cashflow/fee history and generic protection repair remain extensions, and unavailable accounting is explicitly withheld. Local fills remain quote-based paper simulations. No strategies, profitability or QQQ/S&P 500 outperformance are claimed by this architecture audit.

Docker supervision and the systemd example remain local deployment options. Docker restart policy handles an exited process; a running container that becomes unhealthy needs an external supervisor/operator action. No off-host deployment or host power-loss test was performed. The supplied monitor checks the actual runtime gates and does not send notifications or place orders.
