# HARDEN-RESEARCH — production execution-engine reliability research

Date: 2026-10-24. Companion to HARDEN-SCOPE.md (rows H21–H23 bind
the ADOPT items). Method: web + GitHub research on the six named
topics, each finding dispositioned **ADOPT / ALREADY-HAVE / REJECT**
with a one-line evidence reason tied to THIS desk (311 sleeves,
2 vCPU / 7.7 GiB box, stdlib-only, Alpaca paper door, one 60s cycle).
Research informs decisions; it never expands scope on its own —
every ADOPT lands only as a named harden item with a blocker.

Desk baseline facts used for the dispositions (from the v3 build
record, re-verified at scope): one immutable content-hashed snapshot
per cycle; bounded persistent worker pool (= cpu_count) with hard
per-eval timeout, kill+respawn, recycle after 200 evals; ONE
dispatcher/writer with `v3-<sleeve>-<intent_id>` client order ids,
journal-indexed idempotency, fills only from broker read-back;
per-cycle reconcile (journal-derived vs broker) halting entries for
the affected sleeve only, cash discrepancy halting entries desk-wide;
producer registry with UNFED-by-name; persisted scheduler cursors
(restart no-refire); append-only per-sleeve journals; gate 674 tests
GREEN at adoption close; cycle 25.78s for 311 on the warm harness.

---

## 1. Idempotent order submission

- **Finding:** execution engines treat idempotency as a first-class
  requirement — unique stable client order IDs plus deduplication at
  the gateway AND the venue layer, because retries/reconnects will
  otherwise double a position; dead-letter queues capture orders
  that cannot be processed for investigation instead of dropping
  them. Sources: https://gegobyteapps.com/resources/trading-system-architecture ;
  https://www.designgurus.io/blog/grokking-idempotency (idempotency
  keys, put-if-absent natural keys, dedupe on unique constraint).
  **ALREADY-HAVE** — dispatcher already stamps stable
  `v3-<sleeve>-<intent_id>` ids, dedupes via the journal seen-index,
  and counts fills only from broker read-back by client order id
  (CORE-5 blockers); the broker's own client-id dedup is the second
  layer.
- **Finding:** at-least-once delivery is the realistic assumption;
  consumers dedupe on a stable event id, order is guaranteed only
  per partition/entity key, and poison messages go to a DLQ so one
  malformed item cannot block the stream. Source:
  https://aibuildersnetwork.org/api/expert-insights/how-do-you-stop-duplicate-events-in-an-event-driven-pipeline/export-pdf
  **ADOPT (R-ADOPT-3)** — the desk refuses malformed intents
  per-intent (owner ruling R-4, kept), but a repeatedly-malformed
  producer currently just accrues rejects; add a named quarantine:
  after N malformed intents from one sleeve in a session, the sleeve
  is journaled QUARANTINED, named in the terminal, and its producer
  defect is the tracked item — main flow never blocks. (Matrix H14.)
- **REJECT:** a Redis/external idempotency store (the pattern in
  several reference implementations) — the desk is stdlib-only on
  one box; the append-only dispatcher journal already is the durable
  dedupe store, and a second store would be a second source of
  truth, which doctrine forbids.

## 2. Worker-pool isolation + supervision

- **Finding:** OTP supervision is the canonical form of this desk's
  pool: `one_for_one` restarts only the failed child; shutdown is a
  bounded grace then brutal kill; critically, supervisors carry a
  **restart-intensity cap** (max restarts in a time window) so a
  repeatedly-dying child escalates instead of restart-looping
  forever. Sources: http://erlang.org/documentation/doc-6.4/lib/stdlib-2.4/doc/html/supervisor.html ;
  https://deepwiki.com/seven1m/30-days-of-elixir/5.4-otp-and-supervision-trees
  (fault isolation, automatic recovery, separation of supervision
  from business logic).
  **ALREADY-HAVE** for isolation/kill+respawn/recycle (CORE-1);
  **ADOPT (R-ADOPT-1)** for the missing half: a restart-intensity cap
  per worker/sleeve — beyond the cap the sleeve is marked wedged for
  the session and the pool runs in a named degraded state instead of
  respawning indefinitely. (Matrix H22.)
- **Finding:** pool sizing should be treated as capacity planning
  against the next boundary, and overload must shed rather than
  cascade (ErlangB-style dimensioning; bounded pools sized to peak
  with supervisors isolating only the congested workers). Source:
  https://copyprogramming.com/howto/erlang-otp-behaviors-for-beginner
  **ALREADY-HAVE** — pool is bounded at cpu_count with cost-aware
  list scheduling (EFF-1); the governing constraint is measured as
  saty_gpt_v02's single-core floor, not pool size.

## 3. Snapshot consistency / single writer

- **Finding:** event-sourcing/CQRS practice converges on: append-only
  immutable log as source of truth, single writer per aggregate,
  snapshots as rebuildable projections — and a warning that full
  event sourcing costs real complexity and is wrong for simple
  domains. Sources: https://dev.to/ohugonnot/event-sourcing-and-cqrs-a-practical-guide-for-developers-m6o ;
  https://mvpfactory.io/blog/event-sourcing-cqrs-mobile-backends/
  **ALREADY-HAVE** — the desk already has the valuable subset:
  append-only journals, one dispatcher-writer, one immutable
  content-hashed snapshot per cycle that every sleeve in the cycle
  provably shares, corrupt snapshot fails closed (CORE-2/3).
  **REJECT** — a CQRS/event-sourcing rewrite: it would replace
  verified paths with new machinery to re-derive properties the
  desk already proves by blocker; doctrine's minimum-sufficient-
  change order forbids it.
- **Finding:** mature engines (QuantConnect LEAN) converge on the
  same seams — data layer, strategy layer, portfolio/risk layer,
  execution layer, analytics — with pluggable handlers per seam and
  deterministic behavior across environments. Sources:
  https://github.com/masouddargi/Lean ;
  https://y26fdp.klef.in/fdp-fdp06.html
  **ALREADY-HAVE** — v3's producers → snapshot → pool → dispatcher →
  terminal shape is that seam layout; **no adoption action** (a
  LEAN migration would be a rewrite of a working desk, rejected by
  the same reasoning as CQRS).

## 4. Reconciliation loops

- **Finding:** financial systems assume drift and run reconciliation
  as a CONTINUOUS validation mechanism, not a nightly afterthought:
  compare ledger state against aggregated transaction streams,
  cross-check settlement/read-back against posted entries, verify
  idempotency keys across boundaries; compensations are appended
  truth, never history rewrites. Source:
  https://oceanobe.com/news/eventual-consistency-without-losing-money/1858
  **ALREADY-HAVE** — reconcile runs every dispatch cycle before
  dispatch (CURE2-3): journal-derived positions/cash vs broker
  read-back, per-sleeve entry halt on discrepancy, desk-wide entry
  halt on cash discrepancy, legacy book recorded as a pre-v3
  baseline and never attributed.
- **Finding:** the transactional outbox pattern (business write +
  event row in ONE local transaction, relay retries until ack,
  consumers dedupe) is the standard cure for dual-write loss.
  Sources: https://www.alekseialeinikov.com/en/blog/topics/architecture/transactional-outbox-pattern ;
  https://www.developers.dev/tech-talk/the-outbox-pattern-mastering-transactional-integrity-in-microservices-architecture.html
  **ALREADY-HAVE (equivalent form)** — the desk's dual-write risk is
  journal↔broker, and its shape already matches: the intent is
  journaled before submission, broker-down intents are queued and
  retried by `retry_pending()` (SCALE-1b), and the client order id
  makes the retry safe. No outbox table is added; naming the
  equivalence is the disposition.

## 5. Watchdog / supervision of the whole desk

- **Finding:** a dead-man's switch only proves anything if the
  heartbeat is sent AFTER verified work completes ("pet it only
  after real work completes, not from a dumb timer"); absence is the
  signal; grace should be ~2–3× the expected interval so one missed
  cycle does not false-alarm. Sources:
  https://medium.com/@wsx5031060310guy/dead-mans-switches-monitoring-jobs-that-fail-by-not-running-0b583b13dca6 ;
  https://philipptheserver.medium.com/a-dead-mans-switch-for-the-monitoring-system-itself-a5bd704eb63f ;
  https://www.sharetechnote.com/html/db/html/FAQ_EmbeddedSystem_WatchdogTimer.html
  (also: log the reset cause; after repeated resets enter a
  safe/degraded mode rather than looping forever).
  **ADOPT (R-ADOPT-2)** — formalize the runner heartbeat
  (state/runner.json) as a verified-work heartbeat: it advances only
  on a completed cycle with a recorded status, the inspection reads
  it by EFFECTS (file advancing + pid's /proc cmdline — never a
  self-matching pgrep pattern, per desk law), and the staleness
  threshold is set at 2–3× the 60s cycle. (Matrix H22.)
  **REJECT** — any external/third-party dead-man service: the owner
  retired the Healthchecks.io watcher on 2026-10-23 after it flapped
  ~50 emails in a day and ruled it not re-provisioned without his
  explicit ask; supervision stays internal (inspections + heartbeat).

## 6. Lean runtime design (bounded everything, coalescing, bulkheads)

- **Finding:** unbounded queues are a silent production killer —
  acceptance must be bounded by execution capacity, with an explicit
  rejection/shedding policy; protect each downstream with bulkheads
  and circuit breakers so one slow/flaky dependency cannot starve
  the rest; stampede protection via single-flight request
  coalescing on shared reads. Sources:
  https://dev.to/tpmsh/unbounded-queues-the-silent-killer-of-production-services-4me3 ;
  https://www.sharpbyte.dev/production/high-concurrency-design ;
  http://compositecode.blog/2025/07/03/go-concurrency-patternssingleflight-pattern/
  **ADOPT (R-ADOPT-4)** — circuit-breaker/bulkhead posture per
  external producer boundary (Alpaca bars/options, Kraken, Tensor
  bundle, fires ingest, broker door): a failing producer degrades
  ONLY its declared dependents to UNFED-by-name and backs off with
  bounded retries inside the warm stage; today the fed gate already
  isolates by dependency, the missing piece is the bounded
  retry/backoff + breaker state being journaled per producer.
  (Matrix H23.)
  **ADOPT (R-ADOPT-5)** — single-flight coalescing as an explicit
  invariant for producer fetches: within a cycle, same-identity
  requests (symbol/timeframe/window) are fetched once and shared
  via the snapshot (already true by construction for bars); extend
  the proof to retries and to the options/kraken warm paths so a
  retry storm cannot multiply provider calls. (Doctrine field
  manual states the same rule; this makes it a blocker.)
  **ADOPT (R-ADOPT-6)** — a boundedness census in the harden phase:
  every queue, journal batch, retry loop, and fan-out in the cycle
  path gets a named bound or a named reason it is append-only-by-
  design (journals), verified by inspection + one fixture that
  fills a bound and observes shedding, not growth. (Matrix H20/H23.)
  **ALREADY-HAVE** — bounded pool, batched journal writes, per-eval
  hard timeouts, cost-aware scheduling, snapshot-local evaluation
  with zero provider calls during evaluation.
- **REJECT:** LMAX-Disruptor / lock-free ring buffers, kernel
  bypass, co-location, FPGA — latency machinery for µs HFT; this
  desk's governing constraint is a 60s cycle on a 2-vCPU box whose
  measured bottleneck is one sleeve's single-core re-derivation.
  Sources describing them: https://mdsanwarhossain.me/blog-stock-exchange-system-design.html ;
  https://atozofsoftwareengineering.blog/2026/10/19/the-great-thread-death-architecting-non-blocking-event-loops-lock-free-memory-rings-and-zero-copy-i-o-pipelines-under-1m-qps-catastrophic-load-%F0%9F%9A%A8-serverside-backendengineering-systemde/
  Adopting any of it would add machinery with zero effect on the
  measured constraint — the anti-pattern the Efficiency Breakthrough
  doctrine exists to prevent.

---

## Adopts summary (the only scope the research adds)

| ID | Adopt | Lands as |
|---|---|---|
| R-ADOPT-1 | OTP-style restart-intensity cap + named degraded mode for worker/sleeve respawns | Harden item + blocker (H22) |
| R-ADOPT-2 | Verified-work heartbeat semantics (advance only on completed cycle; 2–3× grace; effects-based verification) | Harden item + blocker (H22) |
| R-ADOPT-3 | Poison-intent quarantine: repeated malformed intents from one sleeve → QUARANTINED, named, producer defect tracked; flow never blocks | Audit/harden item + blocker (H14) |
| R-ADOPT-4 | Per-producer circuit breaker + bounded backoff, journaled; failure degrades only declared dependents | Harden item + fixtures (H23) |
| R-ADOPT-5 | Single-flight coalescing proven for warm retries and options/kraken fetch paths | Harden item + blocker (H20/H23) |
| R-ADOPT-6 | Boundedness census: every queue/retry/fan-out named-bounded or named append-only-by-design, with a fill-the-bound fixture | Leanness/harden item (H19/H20) |

## Coverage ledger

- Searched: idempotent order submission; OTP supervision/worker
  isolation; reconciliation loops + transactional outbox; immutable
  snapshot / single-writer / CQRS; watchdog + dead-man's switch;
  bounded queues / backpressure / single-flight / bulkheads;
  LEAN engine architecture (GitHub).
- Excluded: vendor marketing pages without mechanisms; HFT latency
  literature beyond the reject disposition above.
- Unavailable: none material — every topic returned primary or
  practitioner sources; GitHub reached via search results for the
  LEAN repo (no repo clone was needed for an architecture-level
  disposition, and none is claimed beyond it).
