# 17 — Reconciliation with the companion build guide, and data/service hardening

The repository also contains a shorter, independent guide: [`../../docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md`](../../docs/AGENTIC_TRADE_DESK_BUILD_GUIDE.md). Read both. This kit is *operational* (invariants, skeleton code, 130 pitfalls, runbooks). The companion is *architectural* (layers, data contracts, phases, acceptance checklist). They agree on almost everything; this page records where each adds something the other lacks, and the two places they differ.

## 17.1 Where they differ (decide consciously)

| Topic | Companion guide | This kit | How to reconcile |
|---|---|---|---|
| Halt / kill switch | A global and per-strategy halt with reason and operator identity | Layered, deterministic entry-pause and emergency-stop states | Isolate sleeve-local faults; pause new exposure for validated critical account, data, ledger, broker, or risk failures. An unverified metric must not trigger blind liquidation, but a real policy breach must not be reduced to an alert. Define and test effects on queued/working orders, existing positions, protective orders, exits, reconciliation, and recovery. Log trigger, evidence, owner, and state transition. |
| Live promotion | Describes a staged path to live trading | Out of scope: this kit is **paper-only**; live is not implemented | Treat the companion's live phase as a separate project needing human, legal and risk sign-off; nothing here authorises it. |
| Missing data | Fail closed | Fail closed for *entries*; never let missing data erase ownership of a position | Same rule: "missing/untrusted data blocks new entries; exits and reconciliation follow a separately reviewed policy" (P-81). |

## 17.2 Lessons unique to the companion guide, folded in here

**Provenance-bearing observations.** Store with every market observation: instrument id, symbol, provider, feed, asset class, interval, `market_at` (source time), `received_at` (first seen by you), `usable_at` (earliest permitted for decisions), `completed`, session id, price basis, currency, revision id, source receipt. Never back-date `received_at`. A bar is not complete because the wall clock passed its nominal close; corrections are new revisions, never silent rewrites (P-116).

**Coverage states.** FRESH, STALE, INCOMPLETE, UNAVAILABLE, UNENTITLED, INVALID, BLOCKED — and distinct reasons for "no signal" (P-129). A data gate names *what* is missing and what evidence would clear it.

**Three kinds of objects.** *Strategy* (exact rule, may produce intents), *monitor* (reports a condition; owns no capital, emits no order), *research recorder* (stores evidence; does not become a strategy because its output is numeric). Use a stable sleeve identity for ownership — a display name is not enough to decide what a code path may exit (P-127).

**Mode taxonomy.** Always name the mode: research · local simulation · broker paper · live. Evidence ladder: unit test → deterministic replay → historical backtest → simulated paper → broker paper → small live pilot. Each proves less than the next; none proves profit. Label synthetic fixtures as synthetic.

**Money arithmetic and the outbox.** Use decimal/integer minor units for money; immutable fill/fee events; derive positions and cash from the ledger. A database commit and a network call do not succeed together: use a **transactional outbox** (persist intent, then a sender drains it with the idempotent id).

**Risk independent of strategy; policy changes are versioned.** A proposed risk-policy change is not applied until an authorised operator approves it; if an approved *trial* exists, compare-and-swap the policy hash so an automatic rollback cannot erase a newer human decision (P-126). Models may recommend rejecting a trade; only deterministic code or a human changes a gate.

**Agent workflows.** Roles with bounded tool allow-lists (research analyst, data reviewer, strategy reviewer, risk reviewer, operations reviewer, operator). Outputs validated against a schema:
`{claim, evidence:[{source, version, supports}], counterevidence, missing_inputs, confidence, recommended_next_check, authority}`. Retrieved documents are untrusted data. Agreeing agents with the same data/prompt are not independent (P-124). Keep agents away from broker credentials and raw order tools; route any permitted action as a typed request through the same deterministic risk/idempotency/audit path. For model-emitted probabilities keep model version, input hash, calibration period and outcomes; do not present uncalibrated 'confidence' as probability.

**Honest terminal.** Each signal shows: instrument/venue, direction/horizon, event/source/calculation times, provider/feed/delay/basis, coverage, strategy version/commit/config hash/run id, **mode**, status (candidate/waiting/blocked/rejected/accepted/expired/closed), evidence, counter-evidence, invalidation, next required action and whether a human must approve. Separate badges for process, input freshness, account reconciliation and strategy readiness (P-121); alert lifecycle fields (P-123).

**Service boundaries.** A web page is not a worker. Use a supervised host with restart policy, separate service users, least privilege, leases/unique job ids, bounded retries/timeouts/rate limits/CPU-memory-process limits, disk alerts, source-age/queue-age/lag monitoring, secrets outside source/prompt/URL/logs, restricted egress, backup-before-upgrade **and a proven restore**. Health endpoints are read-only (P-122). "Always on" has stated limits: restart policy does not cover host deletion, power loss, storage exhaustion, lost credentials, provider/DNS/cert failure or corrupt state — state the real coverage and test it.

**Multi-user hosting.** Authenticate and authorise every resource; bind data to a tenant id; prevent cross-tenant reads/writes/caches/logs/notifications; per-tenant quotas and backpressure; test isolation separately from load (P-130).

**Licensing and terms.** Real-time consolidated options (and many other) feeds need a licence; a free/delayed endpoint is not a substitute. Don't scrape behind authentication, bypass paywalls or rate limits, or reverse-engineer access controls — use an authorised provider, delayed feed, or reduced, accurately-labelled capability. Review imported strategy packages (install scripts, network, filesystem, licence) before giving them any broker access. For crypto record venue, market type, funding interval, denomination and clock; spot ≠ perpetual. For options verify contract identity, quote coverage, sizes, greeks source and lifecycle (exercise/assignment/expiry) and fail closed if a fresh quote path is not proven.

**Build sequence (their phases A–G, abridged).** A source audit → B research-only vertical slice → C reproducible research → D local paper ledger → E persistent service → F broker paper (only if required) → G live (out of scope here). Do not skip ahead; the acceptance checklists for each phase are in the companion's §15 and this kit's `11_checklists.md`.

## 17.3 Lessons from this kit the companion lacks (so you can cross-read)

Deterministic data-derived order ids and send-unknown handling (P-01, P-02); hash-chained append-only ledger and adoption merge-back (P-05, P-06); VM-pause/clock safety and the supervisor pattern (docs 07); failover worker with the same ids; lane caps with deadlines; reconciliation with pending tolerance; recorder-bypass and verify-at-the-broker rules (P-89, P-90); the research hygiene stack and "green is an evidence state" (docs 08, AGENTS.md); multi-agent dead-drop/claim protocol (doc 09). The companion's table of failure patterns maps to P-121..P-130 here.
