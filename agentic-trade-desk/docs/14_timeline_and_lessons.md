# 14 — Generalized build sequence and lessons

This chapter turns recurring engineering failures into a practical order of work. It is a composite, generalized account: it omits desk names, account details, private infrastructure, and performance claims. Use it to anticipate failure modes, not as evidence that any strategy or deployment is profitable.

## Phase 1 — Inventory before consolidation

Early projects often have several strategy lists, schedulers, state files, and naming conventions. Similar names may refer to different rules, and a catalog count may not match the strategies actually configured or running.

**Lesson:** assign stable identifiers; distinguish idea, specification, implementation, configuration, and runtime instance; record source and version provenance; generate inventory from the actual deployed configuration. Do not replace a working system until its state, schedules, and dependencies are understood.

## Phase 2 — Make cutovers reversible

A new engine can appear correct while an old supervisor or scheduled job silently restarts the retired one. A cutover can also expose quote fallback, rounding, session-calendar, ported-rule, or configuration errors.

**Lesson:** rehearse the cutover; name every process that can start the old and new versions; use a canary or shadow phase; preserve a rollback path; compare decisions and state; then run a heightened post-cutover audit. The operator should be able to identify exactly which version owns each job and position.

## Phase 3 — Treat order handling as a state machine

Order behavior is more complex than “submit, then wait”: acknowledgements can be delayed, submissions can time out after reaching the broker, fills can be partial, and cancel/replace requests can race with fills.

**Lesson:** persist deterministic client order identity before submission, read back by that identity after uncertain outcomes, model every transition, and reconcile partial fills idempotently. Reserve capacity for open and queued orders. Test rejects, timeouts, partial fills, duplicate deliveries, and restarts with a simulated broker before enabling any broker-paper path.

## Phase 4 — Design for interruption and rollback

Laptops sleep, virtual machines pause, deployments roll back, disks fill, and network calls hang. A local state file may be newer or older than an off-box copy.

**Lesson:** separate durable state from disposable runtime files; use atomic writes and concurrency control; apply hard deadlines; supervise processes with restart-aware logic; keep additive off-box backups; and practise restores into a clean location. A backup is not proven until its ledger, book, and open-order set have been checked after restoration.

## Phase 5 — Separate warnings from safety controls

Two opposite designs fail: a noisy monitor can disable an entire desk for a local issue, or an alert-only system can keep creating exposure after a shared integrity failure.

**Lesson:** isolate local faults, block affected entries when data is unreliable, and use deterministic entry pauses or an emergency stop for critical shared failures. State exactly how stops affect queued entries, working orders, positions, exits, and broker-native protective orders. Preserve ownership and use a named contingency policy; never blindly liquidate on stale data or retry an unknown submission under a new id.

## Phase 6 — Scale only with observability

More sleeves increase operational interactions: shared symbols, overlapping signals, capacity limits, data dependencies, and correlated losses. Counts alone do not show which strategies are eligible, active, blocked, or retired.

**Lesson:** maintain a generated inventory and per-sleeve status; audit entry and exit reachability; measure resource use and order capacity under realistic workload; and add sleeves only as fast as their specifications, risk limits, and evidence can be maintained.

## Phase 7 — Coordinate concurrent writers and agents

A primary process, failover worker, scheduler, or more than one coding agent can overwrite state or act on stale assumptions. Duplicate work can create incompatible implementations.

**Lesson:** give every writer an explicit ownership boundary; use locks, transactions, compare-and-swap or another tested concurrency scheme; make updates idempotent and append-only where practical; record decisions and file ownership; and require a single deterministic order path. A standby should prove the primary is inactive and reconcile state before acting.

## Phase 8 — Make documentation and evidence operational

An implementation can be locally correct while its deployment, provider entitlement, current data, or user-facing claim remains unverified. A passing unit test does not prove live connectivity or safe recovery.

**Lesson:** keep a runbook, change record, issue log, open blockers, and evidence receipts. Label each result by what it proves: synthetic test, historical replay, shadow output, local simulation, broker paper, or production observation. Read back the final artifact or remote commit before reporting completion.

## The ten sentences to remember

1. Give each sleeve a stable identity and an executable specification.
2. Preserve provider time, receipt time, and usability time separately.
3. Persist deterministic order identity before sending; a timeout is unknown until read back.
4. Keep the ledger append-only and make replay reproduce the book.
5. Use a single, deterministic order path with explicit authorization gates.
6. Isolate local faults; pause new exposure on shared integrity or risk failures.
7. A tested emergency stop needs explicit behavior for orders, positions, and recovery.
8. Preserve ownership and protective exits; never guess prices to force a result.
9. Back up off-box and prove restoration.
10. A green status is a claim about evidence at a named boundary, not a feeling.

## Additional recurring patterns

Broader reviews surface recurring failure families: truth drift between data, ledgers, brokers, and published status; platform fragility from pauses, resets, timers, and storage; ownership collisions between operators, sleeves, and legacy positions; confusion between provisional and completed data or between exchange and settlement calendars; and research bias from survivorship, clipping, weak null models, or over-selection. The pitfalls catalog gives each a stable reference and a guard to adapt locally.
