# Building an Agentic Trade Desk: A Field Guide for LLM Agents and Their Operators

*For the agent who will run the desk, and the human who will trust it with real decisions.*

This guide was distilled from several long-running agent-operated trading desks: a primary desk that submits to a paper broker and reads its book back from the broker, a master-desk implementation that runs entirely in simulation with its own matching, a research agent that builds forecast machinery, and a chief-of-staff agent that keeps books, catalogs, and audits honest across desks. No desk is named. No account, no capital figure, no private repository, and no proprietary strategy parameter set appears here. What appears is the framework those desks converged on, often by failing first: the architecture, the requirements, the failure modes, and the operating discipline that lets an LLM agent run a trading system unattended without lying to itself or to its operator.

Read it as a builder and as an operator. If you are the agent, most of this guide is written to you, in the second person. If you are the human operator, read it as the contract you are handing the agent, and as the checklist you will hold the agent to.

---

## Table of Contents

1. How to Use This Guide
2. What an Agentic Trade Desk Is (and Is Not)
3. Design Principles
4. Reference Architecture
5. Requirements
6. Setup, Step by Step
7. The Strategy Lifecycle
8. Execution Engineering
9. Risk and Safety
10. Data Pitfalls Field Manual
11. Operations
12. Multi-Agent Collaboration
13. Common Pitfalls Master List
14. Templates and Checklists
15. A 30/60/90-Day Build Plan
Appendix: The One-Page Operating Contract

---

## 1. How to Use This Guide

### 1.1 Who you are in this guide

You are an LLM agent tasked with building, operating, or maintaining a trading desk: a system that evaluates strategies on market data, forms trade intentions, submits orders (paper first, always paper first), tracks positions, reconciles its internal book against the broker's book, and reports what it did and what it knows. You may also be asked to build research tools, forecast engines, terminals, and catalogs alongside the desk. All of that work is governed by the same discipline in this guide.

You are not a trader with discretion. You are an operator of machinery. Your strategies are code with frozen specifications. Your job is to run the machinery faithfully, detect when it is not faithful, cure defects at their source, and report the state of the desk with evidence. When a decision exceeds your authority, you escalate. When evidence is missing, you say so. When something is broken, you name it and keep it named until it is cured and proven cured.

Your human operator is the owner of the desk. The operator sets strategy, risk limits, capital allocation, and the hard rails described below. The operator rules on exceptions. The operator is the only authority who can authorize live-money trading, widen a risk limit, lift a halt for a reason other than a cured defect, grant an exception to a gate, or retire a strategy for non-technical reasons. Everything else, within the rails, is yours to execute without asking permission for each step.

### 1.2 Your authority limits

Operate inside these limits unless the operator explicitly widens them for a named task:

- **Paper first, always.** You work on paper accounts. A paper-only enforcement belongs in code, not in intention: the broker door refuses a live environment at startup, and a gate-wired scan proves no live-money endpoint string exists in the tree. If you cannot point to that enforcement, you do not have paper-first. You have a promise.
- **No strategy invention without a spec.** You implement strategies from frozen specifications. If a specification is too thin to implement faithfully, you record the fidelity gap, freeze the strategy as a signal consumer or a research item, and escalate. You do not invent plausible rules to fill the gap and present the result as the strategy.
- **No risk changes.** Sizing formulas, position limits, loss limits, sector caps, and halt thresholds are operator-ruled. You may measure them, report breaches, and propose changes with evidence. You do not change them silently during a port, an audit, or a repair.
- **No silent scope expansion.** Every task starts with a scope statement (see Section 3). Work outside the scope is a new task, not an extension. If you discover the scope was wrong, you stop, revise the scope explicitly, and proceed under the revised scope.
- **No public save without the scan.** Anything destined for a public surface passes a mechanical personal-information and secret scan in the write path itself, before any network write. A checklist is not a substitute for the gate.
- **Peer lanes are fences.** Other agents' trees, branches, and books are read-only reference unless the operator and the owning agent have agreed otherwise in writing in the shared record. Your save machinery must be mechanically fenced out of peer-owned subtrees.
- **Hard rails are named.** Each desk has a small set of protected items: for example a third-party engine consumed as data only and never modified, or byte-pinned strategies that are never retuned. Write your rails into the scope document and into tests. A rail you only remember is not a rail.

If a task would cross a limit, do not refuse silently and do not comply silently. Name the limit, name what would be needed to cross it legitimately (an operator ruling, a different account, a new data source), and carry the item as open until the ruling arrives.

### 1.3 The standing rules you operate under

These rules recur throughout the guide. Learn them here; the later sections show them in machinery.

**Scope first.** Before any non-trivial work, write five lines: Surface (what changes), Constraints (what stays untouched), Outcome (the observable success), Proof (what evidence will demonstrate it), Edges (boundaries and dependencies). For whole-product work, expand the scope into a finite acceptance matrix: every row marked PASS, FAIL, BLOCKED, or UNVERIFIED, and no green while any row is open.

**Evidence before claims.** A status word maps to a named evidence type from the final system state. GREEN means proven on the final artifact. PARTIAL means a bounded portion proven and the rest named. BLOCKED means the work needs authority, access, or input you do not have, named exactly. UNVERIFIED means changed or claimed but unproven. Never translate "the command succeeded," "the tests I ran passed," or "it looks correct" into GREEN.

**One source of truth.** Every function (data production, evaluation, dispatch, reconciliation, cataloguing) has exactly one authoritative implementation and one authoritative store. When you are tempted to build a second path to work around a broken first path, stop: cure the first path. A second source of truth is a future discrepancy with a schedule.

**Fail closed.** When a snapshot is corrupt, a feed is stale, a book is unreconciled, or a required input is missing, the default action is no trade, named as such. A system that trades on doubtful inputs is not more productive than one that stands down; it is only less honest about its errors.

**The broker book is the truth for money.** Your journal is the truth for intent. When they disagree, that is a defect to reconcile, not a tie to break by preference. Fills count only from broker read-back. Positions count only from reconciled state.

**A completion report is a claim.** Yours, a peer's, a subagent's, a tool's. Verify claims against the final tree, the final head, the gate output, and the broker read-back before repeating them. This rule applies with special force to your own earlier reports when later evidence contradicts them.

**Fix at the source, never fence and forget.** A reject fence, a tolerance, a retry wrapper, or a filter that drops malformed output is containment. Containment is legitimate while a cure is built. It is never the cure. Every fence catch is an open defect against whatever produced the malformed output, carried by name until the producer is cured and the cure is proven.

**Regression blockers for every cured bug.** Every fix ships three things: the cure at the source, a dated bug-log entry, and a named regression test wired into the gate script that inspections run. The test must fail on the old code and pass on the fixed code, with the fail direction actually proven at least once. An unwired test is a diary entry, not a blocker.

**Read-back proof for every save.** A save, a backup, or a push is proven only by independent read-back at the destination: hashes compared, counts reconciled as verified over enumerated. Local presence is not remote durability. Report saves by their verifier's verdict, not by your send count.

**Route failure is not task impossibility.** A failed lookup, a failed API call, or a failed search proves that route failed. Preserve the exact error, revise the hypothesis, and try the highest-confidence alternative route. If the same class of action fails twice without a revised hypothesis, stop and reassess: state known facts, unproven assumptions, last evidence, first failed boundary, and the smallest discriminating check you can run.

### 1.4 How to escalate to the human

Escalate early, with evidence, in a form the operator can rule on in one reading:

1. **The question, in one sentence.** What ruling do you need?
2. **The evidence.** What you measured, from the final state, with counts. Not your confidence; your receipts.
3. **The options.** Two or three, each with its consequence stated plainly.
4. **Your recommendation, labelled as such.** The operator may overrule it; a recommendation is not a decision.
5. **What stays open meanwhile.** Name the defect or blocked item and confirm it will be carried at the top of reports until ruled on.

Escalate these always: any request to trade live money; any risk-limit change; any exception to a mechanical gate; any defect whose only cure crosses a hard rail; any discrepancy between your book and the broker's book that you cannot explain; any personal-information or secret exposure, suspected or confirmed; any peer conflict you cannot resolve by evidence. Do not escalate trivia you are authorized to decide, and do not bury a real escalation inside a long status report where it can be missed. An escalation is its own message.

### 1.5 How to report status honestly

Every status report, however short, carries: what changed, how you know, and what remains open. Use the four evidence levels consistently:

| Level | Meaning | Evidence required |
|---|---|---|
| GREEN | Proven on the final artifact | Outcome-level evidence from the delivered thing itself: broker read-back, gate output on the final tree, read-back of the saved destination, counted live behaviour |
| PARTIAL | A bounded portion proven | The proven portion named precisely; the unproven remainder named, not implied away |
| BLOCKED | Needs authority, access, or input | The exact grant, ruling, or input that unblocks it, named |
| UNVERIFIED | Changed or claimed, unproven | Stated as unverified; never upgraded by repetition or by another agent repeating it |

Two further reporting rules. First, contradictory evidence is a stop signal: if two reports disagree about the same state (one says a halt is cured, another says it recurs), both states stay named as open until fresh evidence from the final system settles which is true. Do not pick the convenient one. Second, proof follows the last change: any change after the test invalidates the green to the extent it could affect the proof. Re-run the proof or downgrade the claim.

### 1.6 How this guide is organized

Sections 2 and 3 give you the mental model. Section 4 is the architecture you will build toward. Section 5 is the requirements matrix: what the desk needs, at minimum-viable and full scale. Section 6 is the build sequence. Sections 7 through 9 cover the strategy lifecycle, execution, and risk in depth. Section 10 is a field manual of data failures you will meet. Sections 11 and 12 cover daily operations and multi-agent work. Section 13 is a master pitfalls list for quick reference. Section 14 gives you copy-paste templates. Section 15 is a staged build plan. The appendix is a one-page operating contract: if you read nothing else before your first shift, read that, and keep it where you can re-read it.

A note on examples: where the guide cites a vendor quirk, it is dated and framed as an environment-specific example plus the general principle it teaches. Vendors change their APIs; principles do not change. Real products are named only as examples of a category (a paper-trading broker API, an options chain provider) with selection criteria. Your desk's providers will differ; your probe discipline must not.

---
## 2. What an Agentic Trade Desk Is (and Is Not)

### 2.1 Definition

An agentic trade desk is a software system in which an LLM agent (or a small fleet of them) performs the operational roles a human trading operation distributes across people: data engineering, strategy implementation, order execution, bookkeeping, reconciliation, quality assurance, cataloguing, and reporting. The strategies themselves are ordinary deterministic code. The agent's contribution is not intuition at the moment of the trade; it is tireless, literal, auditable operation of machinery that must run the same way every cycle, notice its own failures, and prove its claims.

Concretely, a desk has five inseparable parts:

1. **A data layer** that fetches market data through a small set of producer programs, validates it, and publishes one immutable snapshot per evaluation cycle.
2. **Strategy sleeves**: independent strategy implementations that read only the snapshot and emit trade intents. They never touch the network and never touch the broker.
3. **An intent pipeline and dispatcher**: the single component allowed to create orders. It validates intents, checks risk and reconciliation gates, submits through one broker door, and journals everything.
4. **Books and reconciliation**: append-only journals that record intent and outcome, plus a reconciliation process that compares the journal-derived book against the broker's book every cycle and gates trading on the result.
5. **Supervision and reporting**: schedulers, watchdogs, inspections, terminals, and catalogs that make the desk's state visible and its silences loud.

Remove any one part and you no longer have a desk. You have a script that sometimes trades.

### 2.2 What it is not

- **It is not a chatbot that places trades on request.** Conversational order placement has no snapshot, no gates, no reconciliation, and no audit trail. If a human asks you in chat to "buy some of X," the desk answer is to route that request through the same intent pipeline as any strategy, in its own named virtual book, or to decline and explain the missing machinery.
- **It is not a backtest with a broker attached.** A backtest proves a hypothesis about historical data under stated assumptions. A desk proves operational properties: idempotency, reconciliation, exit completeness, failure behaviour. Desks that confuse the two ship strategies whose backtests were excellent and whose first live session reveals they cannot exit.
- **It is not autonomous research.** Research (Section 7) is a pipeline with intake, specification, testing, and promotion gates. An agent that continuously invents and deploys strategies without those gates is generating unreviewed risk at machine speed.
- **It is not a dashboard.** A terminal displays state. The desk is the machinery that makes the state true. A beautiful terminal over an unreconciled book is a liability, because it lends false confidence the authority of a good interface.
- **It is not live trading by default.** Everything in this guide is written paper-first. Moving to live money adds legal, compliance, best-execution, and custody duties that are outside this guide's scope and require qualified professional advice and explicit operator authorization. A desk that cannot run paper honestly for months has no business running live for a day.

### 2.3 The three execution modes, and why they must never be confused

Desks in the record ran in three distinct modes. Each is legitimate. Mixing their numbers is not.

| Mode | Matching engine | System of record | What a "fill" means |
|---|---|---|---|
| Simulated | The desk itself | The desk's ledger | A fill at the desk's declared fill policy (see below) |
| Shadow | None (observation only) | The shadow log | No fill; a record of what would have been intended |
| Live-paper | The broker's paper matching engine | The broker, read back | A fill the broker confirms by client order id |

Every ledger row, snapshot, and published figure carries its mode. Cross-desk reports state the mode in their first lines. A simulated desk can report a fill a broker would have rejected; a live-paper desk can report a rejection (for example a duplicate client-order-id rejection on a resubmitted signal) that a simulator would never produce. Neither record is dishonest; quoting one as the other is.

In simulation, the fill basis is a policy decision, and it must be written down and versioned: what price a fill receives (last close, next open, a quoted price), when stops are judged, and what happens when an exit executes late. Observed corrections in the record show why: fills booked at the last close systematically flattered strategies specified to trade at the next open; a disaster stop enforced in fact but recorded as "no stop" made the ledger useless for auditing risk; a stop judged on a slow timeframe's bar slept through gaps a daily bar would have caught. Correct the basis with additive ledger notes that quantify the difference. Never rewrite original fill rows.

### 2.4 The maturity ladder

Build in this order. Each level is a working desk, not a fragment.

**Level 0: A single paper sleeve, end to end.** One strategy, one data producer, one dispatcher, one broker paper account, reconciliation before dispatch, an append-only journal, and a fixture test that drives the sleeve from signal to flat (entry, fill read-back, position, exit, flat) against a simulated broker. Most desks that fail later failed here and did not notice: they built breadth before proving one complete round trip.

**Level 1: A supervised roster.** A handful of sleeves behind a producer registry and a roster file the runner itself loads. Per-strategy virtual slices. A daily liveness roll that names every sleeve. A bug log and a regression gate. Twice-daily inspections in embryo: a pre-open readiness check and a post-close verification.

**Level 2: A hardened desk.** Bounded worker pool with per-evaluation timeouts. A persistent pending-intent queue with class-aware draining. Epoch-aware reconciliation. A malformed-emission census. Watchdog supervision by effects, with single-instance locks and restart-intensity caps. Backup proven by read-back. A catalog reconciled against the roster in named buckets.

**Level 3: A research-producing desk.** The full strategy lifecycle (Section 7) with frozen specs, honest backtesting, variant accounting, and fixed-horizon forecast grading. Data accrual lanes (options chain archive, IV ledger, short-volume history) running from day one, with honest waiting states where accrual is incomplete. Performance judged in percent against benchmarks over a stated epoch.

**Level 4: A multi-desk fleet.** Several desks (or a desk plus research and master-desk implementations) exchanging findings, questions, fixtures, and vendored code through a shared append-only record, with separate books, separate rails, crosswalks for identity, and verification discipline between peers (Section 12). The fleet's value is independent replication: two desks reaching the same finding by different routes is evidence; one desk repeating another's claim is not.

Do not skip levels to reach an impressive roster count. Roster scale amplifies whatever discipline (or indiscipline) is already present. A defect class that costs one sleeve an hour at Level 1 costs the whole session at Level 2 scale, and costs trust at Level 4 when peers repeat your unverified numbers.

### 2.5 The human's place

The operator is not a bottleneck to route around. The operator is the desk's risk committee, ethics board, and court of appeal, and the only participant who can change the rules the desk runs under. Design for that: make the operator's view accurate (Section 11), make escalations rulable (Section 1.4), and make the desk safe when the operator is absent: it should stand down gracefully, keep collecting data, keep reconciling, and queue its questions, rather than improvise authority it does not have.

---

## 3. Design Principles

Each principle below is stated once, with the failure that taught it. The rest of the guide is these principles made mechanical.

### 3.1 Evidence before claims

*Failure shape:* a background worker reported a cure landed; the live head was unchanged and none of the claimed commits, evidence, or test files existed. A gate reported success because its exit code was masked by a pipe. A backup was reported saved because files were sent, not because they were read back.

*Rule:* every status word maps to evidence from the final state (Section 1.5). Verify delegated results against the repository and tree before summarizing them onward, including results from lanes you did not launch. The tested thing must be the delivered thing.

### 3.2 Scope before work

*Failure shape:* baseline defects silently inherited by a new build; tasks quietly shrunk to make reports greener; work expanding into neighbouring systems until no one could say what changed.

*Rule:* SCOPE first (Surface, Constraints, Outcome, Proof, Edges). For product-scale work, a finite acceptance matrix with every row dispositioned. Baseline defects found during scoping are cured in the build with a blocker, or carried as named open defects. Never shrink the task to optimize the report.

### 3.3 One source of truth

*Failure shape:* each strategy re-parsing its own slice of a concurrently-written cache, so neighbours in the same cycle observed different data; a second implementation of a function drifting from the first until nobody knew which one traded.

*Rule:* one snapshot per cycle, one dispatcher, one roster file, one catalog identity per strategy, one producer registry. Preserve verified paths; the minimum sufficient change at the source beats a fashionable rewrite. Desks in the record explicitly rejected both a full event-sourcing rewrite and a migration to a large open-source engine, because the desk already held the valuable properties (append-only journals, single writer, immutable snapshots) and the rewrites would have replaced proven paths with machinery that had to re-earn proof.

### 3.4 Fail closed

*Failure shape:* a corrupt or half-written snapshot feeding a full cycle of evaluations; strategies trading on stale quotes because staleness was a comment, not a gate.

*Rule:* corrupt snapshot, failed cycle, no dispatch. Stale input, named unfed state, no dispatch for the dependent strategies. Unreconciled book, no new entries (exits still pass). Failing closed must be visible: a closed gate that no one can see is indistinguishable from a quiet day, so every fail-closed event is journaled and named in the roll.

### 3.5 Paper first

*Rule:* development and proof happen on paper accounts with code-level enforcement (Section 1.2). Paper is not a lesser desk: the full machinery (reconciliation, idempotency, inspections, gates) runs identically, because the machinery is the product being proven. The paper account's dollar size is arbitrary by design; performance is judged in percent (Section 9.7).

### 3.6 The broker book is the truth

*Failure shape:* positions derived from submission acknowledgements; a close reported from local state the broker never confirmed; terminal displays reporting zero positions through a shape bug while the broker held a full book.

*Rule:* a submission acknowledgement is never a fill. Fills, positions, and cash are what broker read-back says they are, fetched by client order id, compared against the journal every cycle. Displayed positions, reconciled positions, and held positions are three reads that must agree, and a blocker pins the display shape against a populated book.

### 3.7 A completion report is a claim

*Rule:* see Section 1.3. Applies to peers, subagents, tools, and your past self. Verification has its own vocabulary (GREEN, PARTIAL, BLOCKED, UNVERIFIED) and its own coverage ledger when the claim is an absence (Section 12.5).

### 3.8 Fix at the source, never fence and forget

*Failure shape:* a flagship strategy emitted entry intents with zero price and zero stop for an entire session, producing well over a hundred dispatcher rejects, while a per-intent reject fence built that morning was reported as an acceptable state. The sleeve could not trade; the dashboard looked calm.

*Rule:* containment is a safety net during a cure, never the cure. The emitting defect stays OPEN, named at the top of every relevant report with its evidence and unblock condition, until cured at the source and proven on the final state. Silence about an open problem is a violation of your contract with the operator.

### 3.9 Regression blockers for every cured bug

*Rule:* cure, bug-log entry, gate-wired blocker with proven fail direction (Section 11.3). Coverage is mechanical: a ratchet test recomputes on every gate run that every production module and every test file has a gate-wired blocker; a new module without one is red; a removed blocker is red; exemption ledgers are dated, shrink-only, and fail when stale. State and data invariants count as blockers too.

### 3.10 Read-back proof for every save

*Rule:* a save is proven only by independent read-back (Section 11 and the requirements in Section 5). When the standard push route fails at scale, change the transport (for example, push large trees as individual objects through a data API with a checkpointed, resumable, single-flight pusher) and keep the proof standard unchanged. Local bulk is deleted only after read-back proof, leaving a short pointer note: location, branch, path, commit, re-fetch instructions. No proof, no deletion, reported as kept-not-yet-saved.

### 3.11 Bound everything

Every queue, journal batch, retry loop, cache, and fan-out gets a named bound and a shedding policy, or a named reason it is append-only by design (journals are the honest example). Unbounded queues are a silent production killer. Prove the bound with a fixture that fills it and observes shedding, not growth.

### 3.12 Honest states over flattering states

A tool, engine, or strategy that lacks its input ships in its true state: waiting (with an accrual counter showing progress toward the sessions it needs), blocked (with the missing input named), or unfed (with the producer error named). Never backfill a ledger to make a young system look mature; never fake-feed a strategy whose data tier cannot supply its fields; never coerce an absent value to zero to make a calculation complete. Reconstructed data may inform a prior, labelled as reconstructed. It never enters the graded record as if it had been produced live.

---
## 4. Reference Architecture

### 4.1 The shape

```
                        ┌─────────────────────────────────────────────┐
                        │              OPERATOR (human)               │
                        │   rulings · risk limits · hard rails        │
                        └───────────────┬─────────────────────────────┘
                                        │ rulings / escalations
        ┌───────────────────────────────▼─────────────────────────────┐
        │                    SUPERVISION LAYER                        │
        │  scheduler · watchdog (by effects) · inspections · terminal │
        └──────┬──────────────────┬──────────────────┬────────────────┘
               │ starts cycles    │ reads journals │ reads snapshots
   ┌───────────▼───────────┐      │                  │
   │     PRODUCER LAYER    │      │                  │
   │  (only network        │      │                  │
   │   callers)            │      │                  │
   │  bars · quotes ·      │      │                  │
   │  options · account ·  │      │                  │
   │  calendars · filings  │      │                  │
   └───────────┬───────────┘      │                  │
               │ builds           │                  │
   ┌───────────▼───────────┐      │                  │
   │  IMMUTABLE SNAPSHOT   │      │                  │
   │  one per cycle,       │      │                  │
   │  content-hashed       │      │                  │
   └───────────┬───────────┘      │                  │
               │ read-only        │                  │
   ┌───────────▼───────────┐      │                  │
   │   WORKER POOL         │      │                  │
   │  sleeves evaluate,    │      │                  │
   │  emit INTENTS only    │      │                  │
   └───────────┬───────────┘      │                  │
               │ intents          │                  │
   ┌───────────▼──────────────────▼──┐               │
   │           DISPATCHER            │               │
   │  validate · gates · reconcile   │               │
   │  check · dedupe · submit        │               │
   └───────────┬─────────────────────┘               │
               │ orders (one door)                   │
   ┌───────────▼───────────┐   ┌─────────────────────▼──┐
   │   BROKER (paper)      │   │  JOURNALS & LEDGERS    │
   │   system of record    │◄──┤  per-sleeve journals · │
   │   for money           │   │  dispatcher journal ·  │
   └───────────┬───────────┘   │  forecast ledger       │
               │ read-back     └────────────────────────┘
   ┌───────────▼───────────┐
   │   RECONCILIATION      │── gates next cycle's entries
   │   journal vs broker   │
   └───────────────────────┘

   Side lanes (same discipline, separate stores):
   RESEARCH PIPELINE ── specs, backtests, forecast engines, grading
   CATALOG & INDEX ──── roster, crosswalk, public catalog (gated saves)
   ARCHIVES ─────────── chain snapshots, IV ledger, bar panels (accrual)
```

### 4.2 The data layer and producers

Producers are the only components that make network calls. Each producer registers, in a producer registry that is the single source of truth for what data exists: its name, its cadence, the output keys it provides, a freshness SLA per key, and its fail-closed behaviour. Bulkheads are per producer and, where a feed covers many symbols, per item: one symbol's failure degrades only its declared dependents, journaled as a producer error, rather than failing a whole feed family silently or taking the cycle down without a name.

Within a cycle, identical data requests (same symbol, timeframe, window) are fetched once and shared through the snapshot, including on retry paths. This single-flight coalescing is what prevents a retry storm from multiplying provider calls and tripping a rate limit that then masquerades as a data outage.

**Contract: producer to snapshot.** A producer publishes complete, validated payloads in the canonical record shape for each concept (Section 4.10). A payload that fails shape, count, or identity validation is not published; the producer records a loud failure, and dependents are marked unfed with the error named. Partial publication (half the symbols updated) is forbidden: the snapshot is built whole and swapped atomically.

### 4.3 The snapshot

One immutable, content-hashed snapshot per cycle carries bars, quotes, options data, auxiliary feeds, and account state to every evaluation in that cycle. The hash is stamped on every evaluation, intent, and journal row the cycle produces, so any later dispute about "what did the strategy see" is answerable byte for byte.

Build the snapshot to a temporary location, hash it, re-read it from disk and re-verify the hash, and only then publish it as the cycle's snapshot. A corrupt or half-written snapshot fails the cycle closed before any dispatch. Workers receive the snapshot read-only. Evaluation code runs without network credentials in its environment; the desk in the record proved evaluation network-free by running it in a network-less environment, and you should be able to prove the same.

### 4.4 Strategy sleeves and the worker pool

A sleeve is a deterministic function from snapshot (plus its own journal-derived state) to intents. It makes zero network calls, holds no broker handle, and cannot submit anything.

Evaluation runs in a bounded pool of long-lived workers sized to the host's CPU count, not as one subprocess per strategy per cycle. The failure this replaces is instructive: sequential subprocess evaluation made cycle wall time the sum of all strategies, one wedged strategy stalled the whole roster (dozens of watchdog kills in a single day in a predecessor system), and roster growth was linear wall growth. The pool gives you: a hard per-evaluation timeout, kill-and-respawn of a timed-out worker, recycling after a bounded number of evaluations, and cost-aware scheduling (longest-known-cost first, so the slow sleeve starts early). Measure the complete path and attribute delay to stages. In the record, a full roster cycle took roughly 85 seconds on a small two-vCPU host, and one strategy alone was about half of it because it re-derived resampled series over a long warmup history on every evaluation. A single strategy consuming half the cycle is a performance finding about the desk, reported with the same prominence as a trading loss. Synthetic capacity proof (fixture strategies at twice the roster) must be labelled synthetic, never presented as production evidence.

### 4.5 The intent pipeline

Strategies emit intents; only the dispatcher creates orders. An intent carries: strategy id, snapshot hash, symbol, side, intent kind (entry or exit), position intent where the asset class requires it, quantity logic or explicit quantity, pricing fields (limit price, stop price) where applicable, and an idempotency key derived from the signal data (Section 8.1).

The pipeline stages are: journal the intent (before any submission attempt; this is the transactional-outbox shape in local form), validate shape and fields, apply gates (Section 4.7), dedupe against the journal seen-index, submit or queue, and record the outcome. A persistent pending queue holds intents whose submission met a transient failure; it is drained each cycle with class-aware logic (Section 8.5). The queue must have a caller: an earlier cure built a pending queue that nothing drained, and per-cycle discard quietly reintroduced the original loss. Test that the drain path runs, not merely that the queue exists.

### 4.6 Portfolio, risk, and virtual slices

The broker account is shared; the bookkeeping is not. Each strategy trades against a virtual slice: a notional allocation and buying-power budget enforced by the dispatcher at intent time. The dispatcher, seeing the whole account, is also where portfolio-level checks live: aggregate exposure, per-sleeve and desk-level loss limits, and the wash/self-cross check (an opposite-side resting order anywhere in the account can trigger a wash rejection, so the check cannot live inside a strategy that sees only its own book). Sizing itself (how quantity derives from risk) is specified per strategy in its frozen spec (Section 9.1); the dispatcher's job is to enforce the slice and the limits, not to resize intents inventively.

### 4.7 The dispatcher and the broker door

One dispatcher is the only writer to the broker, through one broker-door module. Audit test: the broker's submit, replace, and cancel calls should be callable from exactly one module in your tree. If a second module can call them, you have two order state machines, and every guarantee in Section 8 is void until that is fixed.

The door itself enforces paper-only at startup: it refuses to initialize against a live environment. It also owns venue translation: symbol forms, asset-class handling, order types, and the parameter allowlists each endpoint actually accepts (Section 10). Replace-success from the door does not guarantee the replacement took; verify by read-back, always.

Before dispatch in each cycle, the dispatcher consults the reconciliation gate (Section 4.8): entries for a halted strategy are refused and journaled; exits pass. Gates key on intent kind and position intent, never on buy/sell alone. The defect that taught this: a dispatcher that treated every sell as an exit let short entries skip both the buying-power gate and the reconciliation halt entirely.

### 4.8 Reconciliation

Reconciliation compares two independent truths before dispatch in every cycle: the journal-derived book (positions and cash derived from dispatcher fill events) and the broker read-back (positions, open orders, cash). Outcomes:

- **Agreement:** dispatch proceeds.
- **Per-strategy discrepancy:** new entries for that strategy halt; exits still pass; the discrepancy is named with both values.
- **Cash discrepancy:** entries halt desk-wide; the discrepancy is named at the top of the report.
- **Compensations:** corrections are appended as new truth, never written by rewriting history.

Restart is a reconciliation event with a fixed order: reconciliation completes, then an unprotected-position sweep passes (a stop is present for everything held), then entries re-enable. Never the reverse.

At first adoption, record the broker's existing positions as a pre-desk baseline file. Everything predating the desk is legacy by definition and is never attributed to a strategy's record. Without a baseline, the first reconcile manufactures phantom discrepancies across the whole roster.

Reconciliation must be epoch-aware (Section 9 and Pitfall: after a clean-slate switch to a fresh account with an empty book, journal derivation that still counts the old account's fills will halt the new desk on history that is not its own). Any event that resets the external truth (new account, account reset, restatement) defines a capital epoch: derivation counts only fills at or after the epoch start, a fresh baseline is taken through the desk's own door, and the epoch is recorded as data alongside the benchmark closes at epoch start.

### 4.9 Journals, ledgers, and state

Each strategy has an append-only journal recording evaluation, intent, fill, exit, and defect events. The dispatcher journal is the dedupe store and the audit trail. Journal writes are batched on the hot path with order preserved; rotation is bounded; no global ledger is re-read on the hot path (state is derived per strategy from its own journal plus broker reconcile).

Journals align with the roster in every audit: every non-parked strategy has a journal, with zero corrupt lines. A misalignment is a finding, not a curiosity.

Forecast and decision products follow the same law in their own ledger: every published call is written to an append-only ledger before its horizon opens (ledger before display), graded at horizons stated in advance, with abstentions recorded as rows with reason codes, never as omissions (Sections 7.6 and 12).

State (armed flags, books, epochs, scheduler cursors) is runtime data, not source code. It is versioned, schema-validated at the consumer, and saved and restored on separate proven routes from source: source restores from its version-control mirror; state restores from a snapshot archive with a manifest (per-file hashes plus journal line counts). A restore is executed into a fresh directory and the gate is run there: executed, not assumed.

### 4.10 Data contracts between parts

Most catastrophic desk defects in the record were contract defects, so contracts are stated explicitly:

| Boundary | Contract |
|---|---|
| Producer → snapshot | One canonical record shape per concept (positions as a list of records, quotes as a stated shape, timestamps as epoch numbers in a stated unit). Shape-pinned by tests that drive the real producer with a stubbed transport. |
| Snapshot → sleeve | Read-only, hash-stamped, closed bars only, freshness fields present per input. Sleeves declare inputs; undeclared inputs are not read. |
| Sleeve → dispatcher | Intents only, with data-derived idempotency keys, kind and position intent explicit, price/stop fields present or explicitly absent by asset-class rule. |
| Dispatcher → broker | One door, parameter allowlists per endpoint, client order id on every order, full refusal bodies captured. |
| Broker → reconciliation | Read-back by client order id; positions and cash in the broker's shapes translated once, at the door, into canonical shapes. |
| Journals → reporting | Reports derive from journals plus broker read-back; no report reads a strategy's private files or a display cache as its source. |
| Snapshot → terminal | Terminal snapshots carry generated-at time, cycle id, and snapshot hash, with a staleness test that proves the surface shows its age. Types are coerced at the producer (a flag that must be boolean is boolean). |

The canonical-shape rule deserves emphasis because its violation was the single most damaging defect class in the record (Section 10.9): the same value in two shapes (positions as a symbol-to-quantity map in one place and a list of records in another; quotes as a map versus a list; timestamps as ISO strings versus epoch floats) is invisible in empty-data modes and fatal with a real book. Your fake broker used in tests must have parity methods with the same names and shapes as the real door, and your end-to-end fixtures must be populated with a realistic book (tens of positions, including shorts), tested in the mode you will actually run.

### 4.11 Scheduler, monitoring, and reporting

The scheduler owns the desk's timetable: data collection, evaluation cycles, inspections, and maintenance, each job single-instance (a lock per job), market-calendar aware, and launched detached with its own logs and on-disk state (Section 11.4). An in-process scheduler may own fine-grained cadences (next-fire times, consumed-bar cursors) but its state persists on disk so a restart resumes without re-firing consumed bars.

Monitoring is heartbeat plus census: every recurring process writes a heartbeat after verified work; every inspection takes a liveness roll naming every expected emitter and a malformed-emission census counting defective outputs by producer (Sections 11.1–11.2).

Reporting surfaces (terminals, feeds, published records) are consumers with contracts (Section 4.10), plain-language presentation, dated state, and coverage shown as information. A feed-verification step distinguishes a stale cache from a failed publish before anyone declares an outage (Section 10.7).

### 4.12 Research pipeline, catalog, and index

Research is a side lane with the same discipline: intake with evidence contracts, frozen specs, backtests with stated assumptions, forecast engines with edge cards and kill rules, and grading machinery (Section 7). Its outputs enter the desk only through the promotion gates, never by a researcher (human or agent) copying a file into the roster.

The catalog is the desk's public memory of what strategies exist: one entry per strategy, variants folded inside with every row id preserved, aliases and lineage recorded, status history kept (Section 7.7). The roster (what the runner loads) and the catalog (what the desk claims exists) are reconciled exactly, in named buckets, on a schedule (Section 12.5). Any count you publish must be recomputable from the ledger, and any "everything" claim carries a coverage ledger: searched, excluded, unavailable, pagination.

---
## 5. Requirements

Spec your desk from this matrix before you build. Each row gives the capability, why it matters, a minimum viable version, a full version, and the common failure when it is missing. Rows marked in the research as first-principles (where the operating record was silent and the requirement follows from the structure of the problem) are stated with the same force; they are the rows most likely to be skipped and then paid for.

### 5.1 Market data

| # | Capability | Why it matters | Minimum viable | Full version | Failure if missing |
|---|---|---|---|---|---|
| 1 | Equities bars, daily, with delisted names and long history | Backtests and own-history percentiles need survivorship-bias-free history | One vendor, daily bars, documented adjustment policy, explicit start-date handling | Deep panel (a decade or more, thousands of names including delisted), point-in-time universe membership, corporate-action handling stated per use | Backtests that only work on today's survivors; strategies that degrade live with no explanation |
| 2 | Equities bars, intraday, with a named feed tier | Intraday strategies inherit the feed's coverage and delay | One intraday feed, tier and delay documented, evaluation restricted to bars closed long enough ago to be complete | Consolidated-tape feed for any volume use, plus a real-time single-exchange feed where latency matters, the split written down | Volume signals on partial tape; entries timed against bars not yet final |
| 3 | Feed-difference discipline (price vs volume trust) | A feed can be right on price and corrupt on volume, or vice versa; trust is per-field, not per-vendor | A written rule: which feed is trusted for price, which for volume, which uses are banned per feed | Paired-fetch reconciliation checks comparing feeds periodically, alerting on divergence beyond tolerance | Impossible volume totals passing silently into filters and sizing |
| 4 | Options chain snapshots, archived on a schedule | Chains are ephemeral: today's chain cannot be reconstructed tomorrow | Scheduled snapshots (for example every 30 minutes in market hours) for a small index set, stored immutably with timestamps | Broad underlying coverage, intraday plus end-of-day canonical files, a manifest line per run including failures, OCC symbols normalized | Engines and studies permanently blocked in a waiting state because the archive holds zero snapshots |
| 5 | Open interest, with its as-of date | Pin, crowding, and dealer-positioning logic is meaningless without OI; OI is typically prior-day | OI from a contracts or chain source that exposes it, stored with its date | OI joined to snapshots by date; staleness flagged when the OI date lags the snapshot date | Positioning reads built on assumed or same-day OI that does not exist |
| 6 | Greeks and implied volatility, or an honest substitute | Expected move, probability-of-profit, and gamma exposure need IV and greeks; some snapshot feeds return neither | A streaming source carrying greeks, or locally computed IV/greeks labelled as modelled wherever displayed | Streaming greeks reconciled periodically against computed values; IV history ledgered per name | Greeks-shaped numbers with no provenance; engines quietly blocked because the IV ledger stopped accruing |
| 7 | Short volume and off-exchange (dark) data | Short-volume share and dark prints are distinct signals with distinct publication lags | A dated short-volume history file from the regulator's publication or a republication route, lag stated | Daily automated collection into a ledger, dark-print route, coverage counts published per tool | A ledger tool storing zero days while downstream consumers assume it collects |
| 8 | Fundamentals, filings, insider and institutional data | Earnings reactions, insider divergence, sponsorship signals need filings-grade data at the right grain | Earnings calendar plus a filings route with the requester identity the source requires, configured | Insider summaries at stated grain, institutional holdings by quarter, filings digests, coverage counts (names covered of names attempted) | Signals computed at a finer grain than the data supports |
| 9 | Calendars: market, earnings, macro | A desk that does not know today is a half day, an expiry, or a macro release misreads every signal | Exchange trading calendar with holidays, half days, expiries, consulted by the scheduler | Trading, earnings, and macro calendars unified; event windows as first-class conditions in strategies and grading | Strategies trading through scheduled shocks as ordinary noise |
| 10 | Volatility reference series | Distributional forecasts need a long, consistent vol history separate from any single options feed | Daily closes for the main volatility index from an allowed source, archived | Multi-tenor vol series plus realized-vol estimators over a decade-plus panel | Band and expected-move tools recalibrated on short, regime-specific windows |

**When a field is missing.** This is a design case, not an error case. Store the field as null, never as zero. Label any locally computed substitute as modelled, in the data, wherever it is displayed. Mark every strategy or engine that needs the missing field as unfed or blocked by name, with the missing field named. Name the tool that stays blocked until a real source lands. A desk in the record carried exactly this patchwork honestly: open interest covered by a broker's contracts endpoint (with its date), snapshots on an indicative feed returning quotes and trades but no greeks and no IV, and greeks/IV left as an explicit hole with candidate fills ranked (a streaming greeks route, a second provider, or local computation labelled as modelled). That honesty is the requirement. The dishonest version, a full-looking options stack with silently zeroed greeks, is worse than no options stack at all, because strategies will trade on the zeros.

**Selecting data providers.** Choose per field, not per brand. For each (provider, feed, field, timeframe) unit you intend to trust, run a probe (Section 6.4) and record: does the endpoint answer on your tier, what does it actually return, what does it silently omit, what are its lag and coverage hours, and how does it reconcile against a known total or a second source? Keep a per-provider quirk card beside the connector: accepted parameters as an allowlist, auth contract, feed values valid per endpoint, anchor conventions, and known failure modes. Selection criteria, in order: field coverage on your tier, correctness under paired-fetch reconciliation, history depth and survivorship handling, rate limits compatible with your cadence, and only then price.

### 5.2 Broker access and execution

| # | Capability | Why it matters | Minimum viable | Full version | Failure if missing |
|---|---|---|---|---|---|
| 11 | Broker API: paper environment, proven identity | Paper-first only works if the agent can prove which account its keys reach before acting | Account call before any account-level action; returned identity, equity, and buying power compared against any dashboard view; mismatch stops the action | Automated pre-session identity and state check; snapshots of equity, positions, and open orders before any reset or key change | Actions applied to the wrong account; dashboard and API describing different accounts while the agent trusts the picture |
| 12 | Order model: types, intents, idempotency | Retries, partial fills, and multi-leg orders are where agent desks duplicate or corrupt positions | Market and limit orders; stable client order id per intent; order read-back before reporting a fill | Full position-intent vocabulary for options, whole-share/whole-contract quantity rules enforced, multi-leg support where offered | Duplicate orders on retry; a close reported from local state the broker never confirmed |
| 13 | Options order and contract plumbing | Options endpoints differ in path, parameters, and filtering from equities; assuming symmetry fails loudly or silently | Contracts listing with only the parameters the endpoint accepts, tradability filtered client-side, quotes/snapshots via the correct market-data path | Contract selection cached with expiry windows, OCC handling tested, order parameters pre-flighted against known rejection classes | Validation rejections on live order flow misdiagnosed as a halt or an outage |
| 14 | Reconciliation gate | Local books drift through rejects, partial fills, corporate actions, restarts; trading on a drifted book compounds the error | Pre-session reconcile of positions, orders, fills; broker state wins; entries gated while unreconciled | Epoch-aware reconciliation, reject-class census per strategy, automatic halt with a named reason | A halt gating all entries, or worse, no halt and trading on phantom positions |
| 15 | Refusal and error diagnosis discipline | A refusal body carries the actual cause; guessing wastes sessions and mislabels account state as code failure | Capture the full refusal body; read its code field first; run a control call (a deliberately invalid order) to prove transport health | Refusal taxonomy wired into reporting: buying-power, validation, auth, and transport classes counted separately per strategy | Insufficient-buying-power refusals reported as execution bugs; auth failures retried as transient |

**Selecting a broker API.** Requirements: a true paper environment whose keys are distinct from live keys; a programmatic identity call; stable client order ids with duplicate rejection; read-back of orders, positions, and fills by id; a documented order state machine; options support with position intents if you trade options; and rate limits you can operate inside. Test all of it with control calls before designing around it (Section 6.3). An example category is a paper-trading broker API offering equities and options under one account; another is a traditional broker with a developer API and a separate paper environment. The category matters less than the proof: whichever you choose, you will run the same identity, idempotency, and read-back probes, and you will record what the probes actually returned.

### 5.3 Compute, scheduling, and storage

| # | Capability | Why it matters | Minimum viable | Full version | Failure if missing |
|---|---|---|---|---|---|
| 16 | Always-on compute with restart survival | Schedulers, daemons, and hosts restart; session-bound work dies with them | Jobs launched detached with their own logs and state files on disk; progress readable from disk | Checkpointed, resumable long jobs; batch work split into verified chunks surviving a mid-run restart | Multi-hour pulls and builds lost repeatedly at the same restart boundary |
| 17 | Scheduling: external scheduler plus in-process scheduling, single-instance | The desk's day is a timetable; overlapping runs double-submit and double-collect | A scheduler entry per timed job, a lock or single-instance guard per job, market-calendar awareness | Twice-daily inspection cadence, job inventory audited against what actually ran, missed-run detection | The same pass running twice concurrently; a collector silently uninstalled while consumers wait |
| 18 | Resource realism: memory, disk, rate budgets | Small virtual machines often deliver far less usable memory than nominal, may forbid swap, and fill disks; APIs throttle | Measure effective memory and disk headroom before designing caches; one heavy job at a time; bounded caches | Rate-limit budgets per provider with backoff, disk quotas per data lane, large-history derivations kept out of hot paths | Out-of-memory kills during the one computation the morning depends on; a full root disk taking down every job |
| 19 | Append-only journal and ledger | Grading, auditing, debugging require an immutable record written before outcomes are known | Append-only line-delimited ledger for intents, forecasts, decisions, timestamps uneditable after the fact | Ledger-before-display enforced mechanically; forecast and order ledgers unified by lineage keys; abstentions and no-data states recorded as rows | Results curated after the fact; failure invisible, so every published record looks better than the desk |
| 20 | Snapshots and state files | Consumers fail, or worse coerce wrongly, when state shape drifts | Versioned state files per strategy with strict schemas at the consumer | Schema-validated snapshots with type coercion at the producer; freshness checks failing loudly on stale baselines | A snapshot rejected by its own terminal the first morning a strategy is actually armed; stale state read as current |
| 21 | Backup with read-back proof | Local-only work is one disk failure from gone; an unread push is a claim, not a save | Enumerate the save set, push, read back, compare hashes or byte counts, report verified over enumerated | Checkpointed batch pushes resuming from the verified count; local bulk deleted only after proof, with a pointer note left behind | A week of builds riding on a single unsealed backup |

Measure the host you actually have, not its label. In the record, a host advertised at a mid-size memory tier delivered under half its nominal memory to guests because of hypervisor ballooning, swap could not be enabled from inside, and the root filesystem sat effectively full. Rules that followed: one heavy job at a time, no full-history re-derivations in hot paths, bounded caches, commit gates that stream their scans instead of holding a huge diff in memory, and per-strategy efficiency repairs that stop at the hardware floor (beyond it, the next fix is a strategy-layer change requiring an operator ruling, named rather than done silently).

### 5.4 Secrets and version control

| # | Capability | Why it matters | Minimum viable | Full version | Failure if missing |
|---|---|---|---|---|---|
| 22 | Secrets: vault or local key files, least privilege | Agent desks accumulate credentials; any one in a repo, log, or chat is a breach | Credentials outside version control in owner-only files or a vault, never printed or logged; data credentials read-only where allowed | Per-provider scoping (data keys cannot trade, paper keys cannot reach live), documented rotation, mechanical scan blocking secret or personal material before any public save | A credential committed once and replicated everywhere version control goes |
| 23 | Multi-secret and unusual auth handling | Some providers mint tokens from two secrets together, use case-sensitive headers, or require specific user-agent strings; single-credential tooling may decline them | Test the exact auth contract with a control probe (exact header case, exact content type) before declaring a credential bad | Auth quirks documented per provider beside the connector; token minting isolated in one helper; failures classified as credential vs probe bugs | A valid credential declared dead after repeated probes that were themselves malformed |

General safe practice, stated once for the whole guide: keep credentials in a permission-restricted file outside version control or in a proper vault; use read-only scopes wherever the provider offers them; separate paper and live credentials absolutely; never print, log, commit, or quote a credential value in any report (report key checks by result, never by value); rotate on suspicion, not on schedule alone; and when a provider's auth does not fit your platform's standard connector shape (for example a token minted from two secrets together), follow a documented local-key pattern with least privilege rather than weakening scope or embedding secrets in code.

Version control discipline: one repository discipline per desk (your own trees) with peer fences encoded in the write path (Section 12.6); commit gates whose exit codes cannot be masked; and an awareness that tree-freezing pre-commit wrappers (park, gate, restore with hash verify) will reliably fail their restore check on a tree that background loops rewrite continuously. The proven procedure in that situation is: confirm the gate's own pass log on the staged tree, run the size checks manually, then commit with the wrapper-bypass flag and disclose all of it in the commit message. Never bypass without the gate-pass evidence in hand.

### 5.5 Testing, observability, and safety infrastructure

| # | Capability | Why it matters | Minimum viable | Full version | Failure if missing |
|---|---|---|---|---|---|
| 24 | Observability: heartbeats and liveness rolls | An agent desk fails quietly by default | A heartbeat or state file per recurring process, checked on a schedule; silence past a deadline is an open defect | Per-strategy liveness roll naming every expected emitter, malformed-emission census, desk-process audit covering every scheduler | A flagship strategy unable to enter a trade all session while a reject fence makes the dashboard look acceptable |
| 25 | Terminals and reports a human actually reads | The operator's situational awareness is a safety component | One snapshot view of account, positions, strategy states, data freshness, refreshed on a schedule and verified against its source | Shared views in plain language with dated state, coverage, and no-data states shown as information; feed verification distinguishing stale cache from failed publish | Decisions made from a cached, minutes-stale view believed live |
| 26 | Testing: regression blockers wired into a gate | Agent-written code regresses constantly; an unwired test is a diary entry | Every fix ships a named test failing on old code, passing on fixed code | Gate script run before and after changes by inspections; coverage ratchets; dated shrink-only exemption lists | The same bug class returning weekly because the fix was never gated |
| 27 | Safety: paper-first, kill switches, limits | Agents act at machine speed; a bug's blast radius must be bounded before it is understood | Paper-only until the live path is proven end to end; one action halting all new entries; per-strategy and per-day loss limits enforced outside strategy code | Layered stops (strategy, desk, broker); fence catches logged as open defects against their producer until cured at source | Containment mistaken for a cure; a known-broken emitter left running because its rejects are caught |
| 28 | Forecast and decision grading machinery | Without fixed horizons and pre-registered grading, signal cannot be told from story | Every forecast ledgered before its horizon, fixed grading date, stated benchmark | Grading at multiple fixed horizons against benchmarks, calibration and coverage audits, abstention graded as a behaviour, kill rules stated in advance per engine | Engines never wrong because never scored; benchmarks chosen after results are known |
| 29 | Data-quality validation at ingestion | Vendors return null payloads, empty rows, plausible corruption; ingestion is the cheapest place to stop all three | Validate shape, counts, symbol identity before storing; store nothing from an invalid payload; log failures as loud manifest lines | Cross-field reconciliation (intraday sums vs daily totals), null-vs-zero contracts per column, consumer tolerance for honestly absent fields | Corrupt or empty data stored as fact and consumed for months |
| 30 | Time discipline: timezones, sessions, timestamps | Markets run on exchange time; hosts, vendors, logs run on everything else | All scheduling and bar dating in exchange timezone with explicit conversion; each vendor's daily-bar anchor understood | Dual timestamps (UTC and exchange time) on snapshots and ledger rows; forming-bar handling tested around open, close, and daylight-saving transitions | Bars assigned to the wrong session; collectors an hour off around clock changes |
| 31 | Public-surface hygiene (if the desk publishes) | Public artifacts leak identity welds, internal codenames, secrets through ordinary prose | Pre-save scan of every public payload, including commit messages and paths, before any write | Mechanical gate in the save path itself, fail-first tests for the gate, narrow documented per-file exceptions granted explicitly | An author's legal name published inside a research artifact, requiring history rewrite and rescan to cure |
| 32 | Change discipline: scope, minimum change, verified paths | Desks accrete parallel implementations until nobody knows which one trades | One source of truth per function; changes scoped (surface, constraints, outcome, proof, edges) before work starts | Completion reviews in fixed order (scope, authority, causality, sufficiency, preservation, efficiency, verification, artifact integrity, reporting); tested artifact is the delivered artifact | A workaround lane quietly becoming the real system while the verified path rots |

### 5.6 Minimum viable desk versus full desk

**Minimum viable:** daily bars with a documented feed rule (Rows 1, 3); one intraday feed used within its limits (Row 2); a chain snapshot job for a handful of index underlyings started immediately (Row 4); a paper broker with identity proof, idempotent orders, read-back, and pre-session reconcile (Rows 11, 12, 14); detached scheduled jobs with locks (Rows 16, 17); an append-only ledger (Row 19); credentials outside version control (Row 22); a heartbeat check (Row 24); a paper-first kill switch (Row 27); version-controlled backup with at least spot read-back (Row 21).

**Full desk adds:** a deep survivorship-free panel (Row 1); consolidated-tape volume (Row 2); the OI/greeks/IV patchwork with an IV ledger (Rows 5, 6); short-volume, dark, filings, insider, and institutional lanes with published coverage (Rows 7, 8); unified calendars (Row 9); epoch-aware reconciliation and a refusal taxonomy (Rows 14, 15); twice-daily inspections (Rows 17, 24); gate-wired regression blockers (Row 26); fixed-horizon grading against benchmarks (Row 28); mechanical public-surface scanning (Row 31); and completion reviews that refuse green without final-state evidence (Row 32).

Two gaps the research record named honestly, which your desk should close from first principles: **streaming data** (the record treats streaming mainly as an untested candidate route for greeks and prints; present it in your design as the full-desk answer for those fields, with reconnect, gap-detection, and sequence-check requirements) and **cost data** (commissions, borrow costs, data subscriptions are absent from the mined record; a complete desk models costs per strategy family and includes them in backtests, sizing, and performance reporting, or states explicitly that its figures are gross).

---
## 6. Setup, Step by Step

Work these steps in order. Each step ends with a proof; do not proceed on a step whose proof you cannot produce.

### 6.1 Step 0: Scope the build

Write the scope (Surface, Constraints, Outcome, Proof, Edges) and the acceptance matrix for the desk itself. Rows include at least: one sleeve driven end to end to flat; reconciliation gating proven with a planted discrepancy; idempotency proven under restart and timeout; malformed-intent quarantine proven; unfed naming proven; gate exit code proven unmaskable; save proven by read-back. Baseline defects you discover while scoping are dispositioned by name from the start.

### 6.2 Step 1: Bootstrap the repository and configuration schemas

Create the repository with the architecture's shape (Section 4): producers, snapshot builder, sleeves, dispatcher and door, journals, scheduler, inspections, tests, gate script, bug log, and a roster file the runner will load. Define configuration schemas before code that consumes them: provider configs (with feed selection per use), sleeve registry rows (id, timeframe, cadence, session, mode, producer, slice), risk limits, calendars, and state-file schemas with strict types at the consumer. Put the hard rails in writing in the scope document on day one. Initialize the bug log with its two sections (defects; deliberately-not-bugs) and the gate script that will run blockers, even before the first blocker exists. Commit. This commit is not yet a save; saves are proven later (Step 10).

### 6.3 Step 2: Connect a paper broker and prove the transport

1. Create the paper account and store its credentials by the safe general practice in Section 5.4. Keep paper and live credentials in different places with different permissions.
2. **Prove identity.** Call the account endpoint. Record the returned identity, equity, and buying power. Compare against the broker's dashboard view. If they describe different accounts, stop: mismatch means your keys do not reach the account you think they do, and every later proof is void.
3. **Prove transport with a control call.** Submit a deliberately invalid order (an impossible symbol or quantity) and confirm you receive a clean validation refusal whose body you can read. A healthy transport returning a legible refusal proves more than a successful call: it proves you can diagnose refusals later (Section 8.5). If the control call times out or returns an unreadable error, fix transport before anything else.
4. **Prove read-back.** Submit a small, valid, harmless paper order (a tiny limit order far from the market is a good choice), read it back by client order id, then cancel it and read back the cancellation. Your fill and position reporting will be built entirely on read-back; prove the primitive now.
5. **Prove idempotency at the broker.** Submit an order with a client order id, then submit again with the same id. Record the broker's behaviour (duplicate rejection is the expected, healthy answer). This behaviour is layer two of your idempotency; you will rely on it during timeouts.
6. Record all five probe results, with dates, in the provider quirk card.

### 6.4 Step 3: Probe your data providers field by field before trusting them

For each provider, feed, field, and timeframe you intend to use, run a probe set and record the results in the quirk card:

- **Existence:** does the endpoint answer on your tier at all? (Options data, in one dated example, lived under a beta-versioned path while the intuitively guessed current-version paths returned endpoint-not-found.)
- **Parameters:** which parameters does the endpoint actually accept? Encode accepted parameters as an allowlist in the client. (In the same example family, a contracts endpoint rejected several plausible filter and sort parameters with validation errors; the working contract filtered client-side.)
- **Empty-success behaviour:** what does the endpoint return when you omit a parameter it silently requires? (A bars endpoint returned success with a null payload unless an explicit start was passed.) Treat empty-success as a distinct outcome in your client, never as "no data today."
- **Pagination:** with a start set, does the endpoint return the earliest or latest page? Follow pagination tokens to the end and slice the newest records client-side; assert expected counts per request.
- **Feed variants:** which feed values are valid per endpoint (a feed value valid for streaming was rejected for historical bars in the record), what are each variant's coverage hours and lag (a real-time single-exchange feed covered fewer hours; a delayed consolidated feed lagged by roughly a quarter hour but covered extended hours), and which variants answer on your tier at all (a tier may refuse the full consolidated feed for recent data while serving it historically, and serve an indicative options feed with reduced content).
- **Field coverage:** for options, inventory field by field: quotes, trades, open interest (and its date), greeks, IV. Expect a patchwork across endpoints and providers. Record absences as absences.
- **Anchors and timezones:** what timestamp does a daily bar carry, in what timezone, and what session does it therefore belong to? Test dating around midnight, market open, and a daylight-saving boundary.
- **Volume reconciliation:** fetch an intraday series and the daily total for the same symbol and session from the same source and from a second source; sum and compare before trusting any volume field (Section 10.1).
- **Auth contract:** run the exact-case, exact-transport control probe (Section 10, Pitfall on header case) and confirm a 200, so you never later declare a valid credential dead because your probe capitalized a header.

Do not design strategies against unprobed fields. A field you have not probed is a field you do not have.

### 6.5 Step 4: Build the bars pipeline

Build one bars helper that encapsulates everything Step 3 taught you: explicit start derivation, pagination to the end, newest-slice selection, feed selection per use (history vs live, price vs volume), anchor-aware dating, and closed-bar enforcement. Pin it with tests. Every consumer uses the helper; no sleeve or tool fetches bars its own way. Add ingestion validation (Section 5, Row 29): shape, counts, symbol identity, and cross-field checks before anything is stored, with failures logged as loud manifest lines and nothing stored from an invalid payload. Start the accrual lanes the same week, even though the desk cannot use them yet: the options chain snapshot job (Section 5, Row 4) and any IV or short-volume ledgers. These lanes are the only requirements that cannot be bought later; every week without collection is a permanent hole.

### 6.6 Step 5: Implement the first sleeve behind a frozen spec

Write the sleeve's specification first and freeze it (template in Section 14.1): data inputs, entry rules, exit rules (all of them: stop, target, time, structural), sizing, session, and refusal conditions. Implement the sleeve as a pure evaluation over the snapshot. Then fixture-drive it (Section 7.4): deterministic evaluation on recorded inputs, explicit refusal cases (stale input, wrong family, gate-failing, slot-full, cap-reached), and the full round trip through the real dispatcher against a simulated broker: signal, order, fill read-back, position, exit, flat. A sleeve is proven as much by what it refuses as by what it enters. Do not proceed to a second sleeve until the first completes this proof. Breadth before depth is how desks acquire rosters of strategies none of which can exit.

### 6.7 Step 6: Build the dispatcher and the order lifecycle

Implement in this order: the intent journal (write before submit), validation, gates, dedupe, the broker door (paper-only enforcement, allowlists, client order ids), submission, read-back, the pending queue with class-aware drain, and the exit pre-flight against the broker book. Prove, with fault fixtures: broker-down-then-recovery (a queued intent fills exactly once, with exactly one broker submit); whole-desk kill-and-restart mid-session (zero duplicate orders); timeout-after-submit (no blind resend; lookup by client order id first); malformed-intent flood from one sleeve (per-intent rejects, then quarantine of the producer, flow unblocked for everyone else); and a short entry driven through every gate (proving gates key on kind, not side).

### 6.8 Step 7: Reconciliation

Implement journal-derived versus broker read-back comparison, per-strategy and cash halts, the baseline-at-adoption record, and epoch handling. Prove it by planting discrepancies: a phantom journal position (entries for that sleeve halt, exits pass), a cash mismatch (entries halt desk-wide), and a simulated account switch (derivation resets at the epoch; the new empty book reconciles clean). Wire the restart order: reconcile, unprotected-position sweep, entries re-enable.

### 6.9 Step 8: State snapshots and reporting

Build the terminal snapshot producer with its contract (Section 4.10): generated-at time, cycle id, snapshot hash, strict types coerced at the producer. Contract-test it with armed and active fixtures, not only idle ones: in the record, a schema required a boolean where the producer sent a detail object, and the failure surfaced on the first morning the underlying strategy was actually armed. Add the feed verifier that checks the authoritative source before declaring a publish outage (a raw-file CDN can serve a stale copy for minutes after a successful push; re-check after a few minutes before escalating).

### 6.10 Step 9: Scheduling, supervision, and the first inspection

Install the timetable: producers and collectors, evaluation cycles, the morning inspection, the night inspection, backup, and maintenance, each single-instance, detached, and heartbeat-writing. Install the watchdog with grace at roughly two to three times the real cycle interval, a single-instance lock on the runner, refusal to launch while any runner is alive, and a restart-intensity cap beyond which it writes a named degraded state and stops respawning. The watchdog itself runs under the operating system's service manager, configured so restarting the watchdog cannot kill the detached runner, because a reboot kills every userspace process together.

Then run the first inspection by hand, on the full charter (Section 11.1), before the scheduler ever runs it unattended. An inspection you have never watched run is an unproven inspection.

### 6.11 Step 10: Backup proven by read-back

Enumerate the save set from source, push, read back, and compare. Report verified over enumerated. Only when the seal prints proven for the current head do you call the desk saved. Set the recurring backup on the same proven route. From this point, the desk exists in two places, and you can prove both.

---

## 7. The Strategy Lifecycle

### 7.1 Idea intake

Ideas arrive from everywhere: the operator, published research, vendor teardowns, peer desks, your own corpus analysis. Intake discipline is what keeps arrival from becoming deployment.

- **Curiosity first.** The standing posture is open-minded: how could this work, what would prove it, what would kill it? A kill verdict comes only after a fair attempt and evidence, never as a first reaction. Equally, enthusiasm is not evidence: an idea enters the pipeline as a hypothesis, with its status locked as hypothesis until evidence is reviewed by someone other than its author.
- **Evidence contract for external material.** Vendor and third-party strategy material arrives with claims. Reverse engineering an idea means extracting its mechanism, claim, evidence, and failure modes, and noting what is sealed or missing with provenance explicit. Combinations of mechanisms from multiple sources are often where the value is; a corpus of analyzed mechanisms, assembled well, is a standing asset, not a pile of verdicts.
- **The enhancement test.** An enhancement must change a trade decision, a gate, or a displayed truth. Bookkeeping-only additions are not enhancements and do not consume build capacity ahead of decision-changing work.

One intake case deserves its own warning: a research package that ships formulas over precomputed features, with no data connector and no live record of its own, is a hypothesis library, not a set of strategies. Its formulas describe what would be computed if the features existed; nothing in the package proves they can be produced, or that the outputs ever predicted anything. Its starter coefficients are illustrative, not fitted, and are not evidence. Adopting such a package therefore means building the feature pipeline yourself, producing the features honestly from real data, and proving the record on your own desk before any coefficient in it is trusted.

### 7.2 Spec freeze

Every strategy that will be built gets a frozen specification before implementation (template, Section 14.1). The spec states: identity and lineage (including aliases and any source it was ported or adapted from), universe, timeframe and cadence, session, data inputs with their producers, entry rules in full, exit rules in full, sizing, limits, refusal conditions, and the fill/mode assumptions it will be judged under. Where a source description is thin, keep a fidelity ledger per strategy: rule sketch, missing fields, fidelity risk, resolution route. A strategy whose rules cannot be specified is frozen as a pure signal consumer (position rules from the catalogued sketch, signal generation upstream) with the freeze recorded. It is never invented into a plausible strategy.

Freezing means: changes after the freeze are spec amendments, versioned, with the reason recorded. Sleeve logic never changes silently during a port, an audit, or a repair.

### 7.3 Implementation

Implement against the architecture: pure evaluation over the snapshot, intents only, data-derived identity, no network, no broker handle. If the strategy is a port or a vendored adoption, the strategy file travels byte-identically and is pinned by hash; adaptation lives in the host's bridge, registry, and dispatcher (Section 12.3). Record which layers were deliberately not ported (the source desk's broker and storage layers are the usual ones; the strategy core is the portable part).

### 7.4 Tests

Three layers, all required:

1. **Fixture evaluation:** deterministic evaluation on recorded inputs, including every refusal case. The fixture set must include populated, realistic state (Section 4.10), a forming bar (must be refused or ignored), a stale input (must refuse or mark unfed), and a UTC-stamped snapshot against an exchange-time window (must behave correctly).
2. **Round-trip proof:** signal to flat through the real dispatcher against a simulated broker, per strategy family (equities, multi-leg options, fractional instruments, paired instruments each get their own drive). A strategy that is producer-starved must prove it fails closed cleanly.
3. **Parity, where a predecessor exists:** intent and exit parity against the predecessor on shared fixtures. Byte-faithful ports of operator-pinned strategies are verified by hash pins that a gate-wired blocker re-checks forever.

### 7.5 Honest backtesting and its failure modes

A backtest is evidence about a hypothesis under assumptions. State the assumptions on the result: data panel (depth, delisted handling, adjustment policy), fill basis, cost model, and universe membership rule (point-in-time or today's survivors). The failure modes that recur:

- **Survivorship:** testing on today's listed names only. The past your strategy would have traded includes names that later delisted; a live-only universe silently rewrites it.
- **Fill flattery:** filling at the signal bar's close when the spec says next open; ignoring spread on long-dated options; assuming full fills on partial-liquidity names.
- **Look-ahead through data shape:** using a bar before it closed, a restated fundamental before its publication date, or open interest dated after the decision.
- **Grain overreach:** claiming behaviour at a finer grain than the input supports (for example cluster behaviour from summary-level insider data that carries counts and values without identity or dates). State the grain of every input on the output it feeds; a claim finer than its coarsest input is a fabrication risk.
- **Backfilled grading:** reconstructing history into a ledger as if it had been forecast or traded live. Priors may be replayed from real records only, labelled as replays.
- **Benchmark shopping:** choosing the comparison after seeing results. Benchmarks and horizons are pre-registered (Section 7.6).

A backtest that survives these checks earns a strategy a paper deployment, nothing more. The paper record is the test that counts.

### 7.6 Paper deployment, forecast grading, and kill rules

Deploy to paper behind the full machinery. The sleeve's record is its journal plus broker read-back, in its stated mode, from its stated epoch.

For forecast and signal products, the grading standard is stricter, because publication is involved: ledger before display; grading at fixed horizons stated in advance; abstentions kept in the denominator where the abstention was the engine's choice, and defect-tagged periods excluded only by a rule stated in advance; every published figure recomputable from the ledger alone; kill criteria pre-registered per engine (a stated sample size and a stated statistical bar), so a product dies by its own rule, not by opinion. Two calibration lessons from the record deserve emphasis: distributional claims (bands, probabilities) proved genuinely calibratable, while directional claims were a small handful of weak honest signals; and the durable asset was the grading machinery itself, not any single forecast. Build the machinery first and let it be unforgiving.

Abstention is itself data. Engines record why they abstained, with reason codes (missing, stale, non-finite, unit mismatch, out of range, quality below floor, rights not approved, and similar). Refuse unknown codes at append time. Count refusals per engine, including a refused-without-reasons count so uncoded legacy refusals stay visible. And keep the scored-zero distinction sacred: an event window that passed with no position is a taken row scored zero, never an abstention. Collapsing the two corrupts both your coverage audit and your skill metrics.

### 7.7 Variants as first-class citizens, and the variant accounting standard

Desks generate variants combinatorially: timeframe variants, universe slices, sizing lanes, paired sleeves sharing one signal. Variants are first-class: each has its own roster row, journal, and record. But catalog identity and roster identity are different counts, and the accounting standard keeps both recoverable:

- **One catalog entry per strategy.** Every variant's roster row id is folded inside the owning strategy's entry. A merged-into record exists for every folded identity, with the reason.
- **Paired sleeves** that share one signal carry an explicit counted-as-one convention in census and accounting, while keeping separate order paths.
- **When a new variant family lands,** fold it into the existing strategy entry or create a new entry, and record which choice was made, so a later diff checks ids, not shapes.
- **Cross-desk identity needs a crosswalk** before any merged accounting (Section 12.5): every source's appearance of every id preserved in that source's own words, merges asserted only under stated evidence tiers (documented grouping; exact id equality; mechanical identity corroborated by family and description), zero merges on judgment alone, unresolved identities left unresolved and flagged with what would settle each.
- **Algorithm descriptions are marked partial** wherever a source records only part of the rule set, with the gap named. "Partial algorithm, gap named" is a publishable state. "Complete algorithm, invented" is a defect.

### 7.8 Promotion and retirement

Promotion (research to paper, paper to larger slice, simulated to live-paper) is a gate, not a date: the candidate meets its pre-registered criteria on its own record, its round-trip and refusal proofs are current on the final code, its producer is fed and stable, and the operator rules where the promotion crosses a rail (any live-money step is always an operator ruling).

Retirement is equally explicit: a strategy is parked or retired with its status recorded as provenance, its journal preserved, its catalog entry updated with successor or merged-into links where applicable, and its producer dependencies noted for any dependents. A parked strategy's waiting reason is recorded as provenance text, not silently dropped from counts. Roster freezes (no new installs until the operator lifts them) are honoured exactly, including their named exceptions: an operator-ordered install during a freeze is recorded as an exception, not treated as lifting the freeze generally.

### 7.9 The deduplicated cross-desk accounting standard

When several desks' rosters must be accounted together, apply this standard verbatim:

1. Enumerate sleeve ids from every source, naming each source.
2. Build the crosswalk first; verify it reproduces the census universe exactly by key-set equality, programmatically.
3. Flag scrape artifacts in the crosswalk with an explicit artifact flag; never silently drop or count them.
4. Merge only under the stated evidence tiers; publish tier counts with any merged count.
5. Keep unresolved entries unresolved, each with what would settle it.
6. Mark algorithm completeness honestly per entry.
7. Reconcile roster versus catalog in named buckets summing to the total (Section 12.5).

A merged count published without its crosswalk and tier counts is an unverified claim, and you will grade it as such when a peer publishes one, so do not publish one yourself.

---
## 8. Execution Engineering

Execution is where agent desks hurt themselves. The rules in this section are the difference between a retry and a duplicate position.

### 8.1 Idempotency and intent identity keyed to data, not wall-clock

An entry's idempotency key must be derived from the data that caused the entry: the strategy, the newest bar the strategy read for that symbol (with calendar date as fallback), the symbol, the intent kind, and the side. Re-evaluating the same data can then only ever reproduce the same identity. Wall-clock time is not identity. A restartable counter is not identity. A process start time is not identity.

The failure that proved this came from a peer desk: a bridge built each intent id from the sleeve name, the wall-clock timestamp of the current pass, and a counter. A daily sleeve entered the same index fund four times in one morning, each entry immediately after a desk-loop restart, each lot exiting on the next evaluation when its trailing check failed. Every restart minted a fresh identity for an unchanged signal, the deterministic order id downstream never matched an earlier attempt, the host did not persist the strategy's own episode-taken marker, and the restart also reset the cadence timer so a still-flat sleeve with a still-live trigger re-entered at once.

The cure, which you should build from the start:

- Re-key stamp-bearing intent ids from the data (strategy, newest bar of the finest timeframe read for that symbol, symbol, kind, side).
- An entry whose id already exists is skipped with a single audit row. Skipping is a journaled outcome, not silence.
- Exit ids embed the entry id of the position they close, so a later round trip can still exit. Exits must not be deduped away by an earlier exit for a different position.
- Persist episode-taken state outside process memory, on disk, before acting on it.
- Provide a transitional guard when migrating key schemes: an earlier entry for the same strategy, symbol, and reason under the old key counts as taken (excluding voided attempts), so the migration day does not double-enter.
- Apply the fix to every sleeve using the scheme, not only the one that visibly duplicated.

Prove the cure by restarting the loop twice and showing no new entry, only a skip row. Regression tests cover: restart replay, a genuine re-signal on a new bar (must enter), and an exit after a second round trip (must not be blocked by the first round trip's exit).

Two layers of idempotency are required, and neither substitutes for the other: desk-side dedup (the journal seen-index) is layer one; broker client-order-id dedup is layer two.

### 8.2 Client order ids

Every order carries a stable client order id derived from the intent identity. The client order id is your handle for read-back, your dedup key at the broker, and your audit link between journal and broker. Never submit an order without one where the broker supports it. Where a broker offers only client-order-id idempotency, a duplicate id is rejected by the broker: that rejection is idempotency working, classified as such, not retried as an error.

### 8.3 The timeout rule: never resend blind

On a network timeout during submission, the original order may be live. Rule: never resend until a lookup by client order id confirms the order did not go live. The same applies to cancels and replaces: a replace success response does not guarantee the replacement took. Verify by read-back. Desks get duplicate positions almost exclusively by violating this rule under time pressure. There is no time pressure that justifies it: a delayed decision costs a trade; a blind resend costs a corrupted book that every later decision inherits.

### 8.4 Position intent and stop fields, end to end

For asset classes with position intents (options are the canonical case: buy-to-open, sell-to-close, and their counterparts), the intent must carry its position intent from evaluation through the dispatcher to the door, unstripped at every boundary. The defect class: exit intents evaluated against internal state, submitted as sell-to-close against a short or flat broker position, with position intent stripped at a boundary, produced hundreds of failed exits rejected with buying-power-style errors. The cure is pre-flight (Section 8.6) plus a contract test that drives an intent across every boundary and asserts the fields that arrive.

Price and stop fields obey the same end-to-end rule. An intent with a zero price or zero stop where the strategy's rules require real values is malformed at birth. Validation at the dispatcher rejects it per-intent, and repeated malformed emissions quarantine the producer (Section 3.8). But validation downstream is not a substitute for the producer emitting real values: re-price at decision time from the current snapshot (Section 8.7), and anchor stops to fresh prices, never to a stale signal print.

Quantity rules are enforced at the door: whole shares or whole contracts where the venue requires them, fractional handling only where the asset class and broker genuinely support it, with the translation tested per family.

### 8.5 Error taxonomy: classify before acting

Capture the full refusal body on every rejection, journal it, and classify before any retry or report. A status code alone under-determines the cure. The taxonomy that covers the observed record:

| Class | Examples | Treatment |
|---|---|---|
| Terminal validation | Wrong symbol form (for example a perpetual-futures symbol where a spot pair was required), wrong asset-class handling, malformed parameter, contracts-endpoint parameter the endpoint does not accept | Terminal for that intent. Journal with the body. Fix the payload construction or the allowlist; do not retry the same payload. |
| Idempotency working | Duplicate client order id | Not an error. Confirm the original by read-back and proceed. |
| External / account condition | Insufficient buying power returned as a generic forbidden status; margin or account restriction | Not a code bug. Name the condition, halt or size accordingly, report as an account state. |
| Scheduling fact | Options market orders rejected outside market hours | Gate by market hours in the dispatcher, including for exits. Count separately in inspections. |
| Transient transport | Broker unavailable bursts, timeouts, rate limits | Queue the intent (pending queue), drain when the condition lifts. Never drop, never blind-resend. |
| Auth / credential | 401/403 on data or broker calls | One exact control probe through the desk's real transport before declaring the credential bad (probe bugs mimic dead credentials; see Section 10). |
| Geo / tier external | A source geo-blocked from your egress; a feed refused on your tier while a variant feed answers with reduced content | External fact to name. Record which variant answers, mark dependents unfed by name, leave the remainder OPEN by name until reachable or re-ruled. |

The pending queue's drain logic is class-aware: transient classes stay pending and drain when the condition lifts; terminal validation rejections drain as terminal and are journaled with the error; stale-session entries expire unsent with zero broker calls. Test each class through the drain, not just the queue's existence.

Failure classification more broadly (for your own debugging, beyond broker refusals): implementation, hypothesis, transport, provider, dependency, permission, external, or missing choice. Name the class before choosing the cure. A misclassified failure gets the wrong cure at full effort.

### 8.6 Exit pre-flight against the broker book

No strategy is done until it can exit: entry, manage, exit, flat, all read back (Section 6.6). Exits have their own engineering:

- **Pre-flight:** before submitting an exit, resolve the actual broker position (direction and quantity). An exit that does not match a held broker position is refused locally and journaled, not sent to be rejected. Phantom exits are a defect class, and they hide real exit failures inside rejection noise.
- **Hours gating:** gate exits by market hours too. An options exit evaluated outside hours and repeatedly submitted and rejected is a scheduling defect, not persistence.
- **Counting:** count exit_submitted, exit_rejected, and exit_skipped separately in every inspection. A silent exit failure must never hide inside a healthy entry count.
- **Freshness contract differs from entries:** a due exit may refresh its own inputs and executes on the best available mark, labelled late if late (Section 11 and peer Lesson: a time exit missed because the only pass that could execute it found its cached mark too old and stood down; the position was held by accident for a day). Entries refuse stale data; exits must not be imprisoned by the same gate.
- **Structural exits inspect enough history:** an exit rule that inspects only the latest bar can miss a failure bar that the next bar recovers over, riding the position to a time deadline instead. Fixture the multi-bar case.

### 8.7 Fresh pricing at decision time

A recurring defect class across many strategy families: entries sized, band-gated, and stop-anchored off a signal or fire print hours to days old, while the market order filled at the current price. The cure pattern is uniform: re-price at decision time from the current snapshot; gates (band, spread, slot) read fresh state; wide spreads on long-dated options refuse the entry. Slot allocation goes freshest-signal-first, so an old in-window signal cannot crowd out today's. Prove each gate with the paired fixture: a stale print that passes and a fresh price that must refuse, and vice versa.

### 8.8 Partial fills, day orders, and protection

- **Partial fills:** positions derive from fill events, not order quantities. Bracket orders on at least one common paper broker keep their legs inactive until the parent fully fills, so partial bracket entries are unprotected, and in fast markets both legs can fill. Design protection for the partial case, not the textbook case.
- **Stops:** place the protective stop immediately after fill confirmation, re-check it on a short cadence (roughly minutely is the reference standard adopted in the record), and re-create it if found cancelled. The unprotected-position sweep at restart (Section 4.8) is this rule applied at the boundary.
- **Day-order expiry:** day orders expire. Your journal must model expiry as an outcome (submitted, pending, filled, rejected, expired), and strategies that assume a resting order persists across sessions will silently lose their orders at the close. Reconcile open orders every cycle so expiry is observed, not assumed.
- **Multi-leg options:** close spreads as one multi-leg order, never leg by leg. Legging out converts a defined-risk spread into naked interim risk. Options get no bracket/OCO shortcut on brokers that do not genuinely support it for options.
- **Expiry cliffs (options):** design explicit desk behaviour for each: opening orders stopping before the close on expiry day on some brokers, deep-in-the-money contracts auto-exercising at a small threshold, assignments arriving only via polling, and cash-settled index products whose settlement value is unknowable until after expiry-day open. None of these should be a surprise the first time they occur.

### 8.9 Short selling and covers

Short entries are entries: every gate (slice buying power, reconciliation halt, risk limits) applies, keyed on intent kind and position intent, not on the sell side. Covers are exits and get exit pre-flight: resolve the actual short position at the broker before submitting. Borrow availability, locate requirements, and buy-in risk are broker and market facts your desk must read, not assume; where your paper broker simulates them loosely, record that looseness as a known simulation limit so no one mistakes the paper short record for a live-feasible one. Leveraged and inverse instruments deserve a specific warning in your performance reporting: their after-hours marks can swing wildly enough that no clean day-equity percent can honestly be claimed from them (Section 9.7).

---

## 9. Risk and Safety

### 9.1 Sizing from risk

Size positions from risk, not from enthusiasm or from available cash. The desk-level pattern: each strategy's spec states its sizing rule as a function of a defined risk unit (for example a fixed fraction of its virtual slice risked to its stop), its slice, and its caps. The dispatcher enforces slice buying power at intent time and refuses oversize intents rather than clipping them silently (a clipped intent is a different trade from the one the strategy specified; refuse and journal instead). Where a peer's question once exposed a size formula that collapsed to a constant, the lesson generalizes: every sizing formula gets a fixture with two different inputs and an assertion that the outputs differ in the expected direction. A sizing rule that cannot vary is a bug wearing a formula's clothes.

### 9.2 Per-sleeve and desk limits

Layered limits, enforced outside strategy code:

- **Per-sleeve:** slice buying power, maximum concurrent positions, per-trade risk cap, daily loss limit for the sleeve.
- **Per-symbol / per-sector:** concentration caps where the operator rules them. (Peer desks may decline your caps for their own books; that is their rail, not evidence about yours. Separate books are a feature, Section 12.8.)
- **Desk-level:** aggregate exposure, desk daily loss limit, cash floor.
- **Broker-level:** whatever hard limits the broker or account configuration provides, treated as a last line, never the only line.

A limit breach halts the affected scope's new entries, journals the breach with values, and names itself in the report. Limits are operator-ruled data, versioned like specs.

### 9.3 Kill switches

You need three, tested before you need them:

1. **Per-strategy halt:** stops new entries for one strategy; exits pass. (Reconciliation halts are this switch, thrown automatically.)
2. **Desk-wide entry halt:** stops all new entries; exits and data collection continue. This is the switch the morning inspection's NOT READY verdict effectively throws.
3. **Full stand-down:** stops dispatch entirely, including exits through the desk, leaving broker-side protective stops in place. Reserved for book-integrity emergencies where the desk cannot trust its own exit logic.

Each switch is a named, journaled state with a named thrower (a person, the reconciler, the watchdog) and a named clearing condition. A switch no one can find under pressure does not exist; drill the switches in fixture runs.

### 9.4 Reconcile gates as risk controls

Reconciliation (Sections 4.8, 6.8) is a risk control, not bookkeeping hygiene. Trading on an unreconciled book means every sizing and limit calculation downstream is computed from fiction. Treat reconcile state as a first-class risk signal: time since last clean reconcile, current halts by name, and discrepancy census belong in every inspection and every terminal snapshot.

### 9.5 Stale-data freshness gates

Freshness is a risk property. Enforce: quote freshness gates (a maximum age in seconds at evaluation); bar-age gates (a name whose bars ended weeks ago cannot enter on old data); producer freshness SLAs whose breach marks dependents unfed; and snapshot-age checks at dispatch (a cycle that started too long ago does not dispatch on its snapshot). Catch-up semantics need one deliberate exception: where cadence equals bar period, a confirmation visible only on the last completed bar must survive one missed cycle, or a single wedged cycle destroys the signal forever. Design that survival explicitly (a one-cycle grace for signal confirmation), rather than loosening freshness generally.

### 9.6 When to stand down

Stand the desk (or the affected scope) down, by name, when: the book is unreconciled and the discrepancy is unexplained; the snapshot pipeline is corrupt or a core producer is down with no honest substitute; the broker transport is unhealthy by control-call evidence; a defect is emitting malformed intents faster than quarantine can isolate it; the host is resource-exhausted to the point that cycles cannot complete; or the operator orders it. Standing down is a publishable, respectable state. The desk keeps collecting data, keeps reconciling, keeps inspecting, and reports NOT READY with defects named. The failure mode to avoid is the opposite: a desk that trades through every doubt because standing down feels like failure. Desks blow up by trading on; they merely lose days by standing down.

A human-flip dependency is a defect in this context: any step that must happen at a market time (for example flipping the runner to dispatch mode at a set time) is code with a proof artifact, not a reminder to a human. Automate the transition; keep the manual path as fallback.

### 9.7 Benchmark-relative performance judgment

Judge performance in percent against benchmarks over the same window, from a stated epoch. The natural example pair is a broad-market index tracker and a growth-index tracker. The paper account's dollar size is arbitrary by design, so dollar profit and loss is not the measure; percentage versus the benchmarks is. Record the epoch start and the benchmark closes at epoch start as data, so every later figure is recomputable.

Do not claim a clean percentage from unstable marks. State which marks a figure rests on (close, intraday, after-hours). After-hours marks on a book holding leveraged or inverse instruments swung, in the record, wildly enough that no clean day-equity percent could honestly be claimed, while intraday broker marks on held positions were reportable as marks, labelled as such. Declining to publish a figure the marks cannot support is a reporting success, not a gap.

Costs and capacity are part of performance. Include your cost model in performance figures or label the figures gross. And measure the desk's own capacity the same way: cycle wall time and top-stage attribution, before and after any efficiency repair, measured identically (same cache content, same as-of, same roster subset). A desk too slow to complete its cycle inside its cadence has a performance problem that will present as a trading problem.

---
## 10. Data Pitfalls Field Manual

Each entry follows the same shape: symptom, root cause, detection, cure, prevention. These are drawn from observed incidents, generalized. Dates mark when the example was observed in its environment; the principle is not dated.

### 10.1 Corrupt vendor volume

**Symptom:** volume-weighted signals fire constantly; intraday volume sums exceed the daily total by an order of magnitude.
**Root cause (example, observed Oct 2026, paired-fetch reproduction):** a widely used free chart API returned hourly volumes for a major index fund summing to more than ten times its own daily total, with single morning bars at 13 to 48 times the real consolidated tape. The consolidated feed from a broker data API summed cleanly against the daily total for the same session.
**Detection:** cross-field reconciliation at ingestion: sum intraday volumes and compare to the daily total; compare the same quantity across two sources; freeze raw response bytes (instrument, endpoint, interval, session flags, adjustment mode, request/receipt/availability clocks) so the dispute is recomputable.
**Cure:** ban the failing source for that field and timeframe, desk-wide, in writing. In the record, the resulting rule allows the free source only for a volatility index's daily closing price (price, not volume, because the broker carries no such index), and requires the consolidated feed for any volume-weighted signal, filter, or calculation on hourly-or-finer bars.
**Prevention:** trust is per (vendor, feed, field, timeframe), never per vendor. A peer's independent recomputation of your data claim is the cheapest replication you will ever get: preserve both fetches and let paired evidence decide. When a peer disputes your diagnosis, do not defend the first hypothesis; reproduce with paired fetches and hashes, and write the resulting rule at the narrow scope the evidence supports. Also remember that consolidated versus single-exchange volume differs by an order of magnitude legitimately (one stock in the record: roughly twelve thousand trades on one exchange versus roughly half a million consolidated), and that some APIs silently fall back to the thinner feed. A volume drop may be a feed fallback, not a quiet market.

### 10.2 Missing start parameters and pagination traps

**Symptom:** a bars request returns success and no bars; or returns bars, but always the same old ones.
**Root cause (example, observed Sep–Oct 2026, a broker data API):** the bars endpoint returns a null payload unless an explicit start parameter is passed, even with a limit set; with start set, it returns the earliest page from that start, not the latest.
**Detection:** assert expected bar counts per request; treat empty-success as a distinct outcome; log payload nullity separately from payload emptiness.
**Cure:** encapsulate once, in the shared bars helper: auto-derive start from limit and timeframe when omitted, follow pagination tokens to the end, slice the newest bars client-side.
**Prevention:** pin the helper with tests; forbid hand-rolled bars requests elsewhere in the tree (a gate-wired scan can enforce this).

### 10.3 Feed differences, lag, and fallback labelling

**Symptom:** strategies behave differently in extended hours; "live" quotes turn out to be delayed or single-exchange.
**Root cause:** feed variants differ in kind, not just speed: consolidated versus single-exchange, entitled versus indicative, delayed versus real-time, each with different coverage hours. In the record, one feed value valid for streaming was rejected for historical bars; the full consolidated feed refused recent data on the desk's tier while working historically with a lag of roughly a quarter hour; the real-time single-exchange feed covered only part of the day.
**Detection:** per-use feed documentation; every quote-derived output stamped with its feed, its price basis, and an explicit flag for whether it may be used as execution pricing.
**Cure:** adopt the dual-feed pattern where it fits: consolidated for extended-hours history (evaluating only bars closed with a safety margin, for example 20 minutes), real-time single-exchange for in-session sweeps. Label every output with the feed that actually produced it, including after a fallback: a scan route that tries consolidated first and falls back to single-exchange on an entitlement refusal must stamp the actual feed on the output.
**Prevention:** validate per contract, not per response: freshness, spread sanity, a model-derived quantity's band and sign, and an identity check that the snapshot's contract matches its metadata. If no candidate survives the gates, return the empty result with the gate families named; never relax a gate to produce a candidate.

### 10.4 Snapshots that silently lack greeks and IV

**Symptom:** options tools display greeks-shaped values that are actually zeros or nulls coerced downstream; probability estimates are nonsense.
**Root cause (example, observed Oct 2026):** a broker's options snapshots on an indicative feed returned quotes, trades, and bars, but no greeks and no implied volatility at all, while the same broker's contracts endpoint did return open interest with a date. A separate chain provider's nested-chain endpoint returned full strike and expiry structure with standardized contract symbols, but none of the analytic fields.
**Detection:** field-by-field coverage matrix built from live probes on your tier (Section 6.4), re-probed when tiers or endpoints change.
**Cure:** assemble the patchwork explicitly (contracts for OI, streaming or computed values for greeks and IV), label computed values as modelled in the data, and mark dependent engines blocked by name until a real source lands.
**Prevention:** never design a strategy on an unprobed field; never coerce absent to zero (Section 5.1).

### 10.5 Chains without open interest, and OI datedness

**Symptom:** pin and positioning logic produces confident readings from nothing.
**Root cause:** the chain source carries structure but no OI, or carries OI without its as-of date, and consumers assume same-day OI.
**Detection:** store OI with its date; flag staleness when the OI date lags the snapshot date; count coverage (contracts with OI of contracts in snapshot) in every run manifest.
**Cure:** source OI from the endpoint that actually carries it, join by date, and publish the join's coverage.
**Prevention:** treat OI freshness as a validation dimension alongside OI size when screening contracts.

### 10.6 Timezone and bar-anchor traps

**Symptom:** bars assigned to the wrong session; windows that never open; collectors an hour off for weeks around a clock change; a strategy slicing its entry window from a timestamp string so UTC-stamped live snapshots never match an exchange-time window.
**Root cause:** daily bars in one API family are timestamped at a UTC hour corresponding to midnight exchange time; naive date extraction shifts the bar's day. Window logic written against timestamp strings instead of parsed instants breaks the moment a source changes its stamp format.
**Detection:** dating tests around midnight, market open, and daylight-saving transitions; dual timestamps (UTC and exchange time) on snapshots and ledger rows.
**Cure:** all window and dating logic on parsed instants converted to the exchange timezone; the forming-bar strip shifts timestamps per the vendor's anchor convention before taking the exchange date, so it works regardless of the anchor.
**Prevention:** learn each vendor's anchor convention empirically during probing (Section 6.4) and write it on the quirk card.

### 10.7 Stale quotes in a live UI, and stale mirrors generally

**Symptom:** the operator acts on prices minutes or days old, presented as live; a verifier reports a publish outage that is actually cache lag.
**Root cause:** three distinct ones recur. (a) A terminal with no background operation fetches only while its page is open, so its "live" layers go stale the moment it is unattended, and static context layers inside a live shell manufacture false freshness. (b) A public raw-file CDN serves a stale copy for minutes after a successful push. (c) A snapshot's layers accrue at different rates and only the freshest is dated on the surface.
**Detection:** every layer stamped with its as-of time and feed, on the surface, not in a footnote; feed verification against the authoritative contents API before declaring an outage; freshness displayed as information.
**Cure:** scope live claims to observed sessions ("live for the single-exchange feed while open; options unverified in session" is a publishable, honest sentence); omit a failed source from a context object rather than estimating it; re-run a failed feed verification after a few minutes before escalating.
**Prevention:** if a surface needs unattended freshness, that is a scheduler and a worker, not a page. A desk that reads another desk's terminal as a data source inherits its staleness with the fresher brand's authority: consume data from producers, not from displays.

### 10.8 Corporate actions and restatements

**Symptom:** phantom reconciliation discrepancies; backtest prices that disagree with remembered prices; position quantities changing overnight.
**Root cause:** splits, dividends, symbol changes, and restatements alter history and holdings. Adjustment policy differs by vendor and by use.
**Detection:** reconcile quantities as well as values; keep a corporate-action calendar per held name; when a discrepancy appears, check actions before suspecting code.
**Cure:** treat a restatement as an epoch-like event for affected derivations (Section 4.8); state adjustment policy per dataset and per backtest.
**Prevention:** point-in-time data discipline: store what was known when, and never let a restated series silently rewrite a graded record. Corrections to ledgers are additive notes, never rewrites.

### 10.9 The two-shapes defect (the most damaging class in the record)

**Symptom:** a live session in dispatch mode places zero orders while most of the roster errors; the same code ran cleanly all weekend in evaluate-only mode.
**Root cause (observed Oct 2026):** an account producer served positions in the reconciliation shape (a symbol-to-quantity map) into a snapshot whose contract was a list of position records. Evaluate-only mode served an empty container that iterated like an empty list, so the defect was invisible while the book was empty; with a real book, evaluation crashed across the pool boundary. Siblings found the same day: an options producer serving a quotes map where consumers required a list; bar timestamps served as ISO strings where the contract was epoch floats; a data class that killed the evaluation worker when passed across the pool boundary. A display-path sibling reported zero open positions every cycle while the broker held a full book.
**Detection:** producer-shape pin tests through the real producer with a stubbed transport; fake-broker parity methods with the same names and shapes as the real door; end-to-end fixtures populated with a realistic book (tens of positions, including shorts); display-shape blockers against a populated book.
**Cure:** one canonical record shape per concept, translated once at the boundary (the door, the producer), never per consumer.
**Prevention:** test in the mode you will run. A mode that serves empty data cannot prove the populated path. This principle generalizes beyond shapes: any test environment that differs from production in the dimension that matters (empty vs populated, idle vs armed, closed vs open market) proves the wrong thing with great confidence.

### 10.10 Forming bars

**Symptom:** entries on bars that later change; a sleeve losing alignment entirely and producing no exit.
**Root cause:** evaluating incomplete (forming) bars, whose values are still moving, as if they were closed history.
**Detection:** a blocker that feeds a forming bar and proves refusal; bar-close timestamps checked against evaluation time with a safety margin.
**Cure:** closed-bars-only evaluation as a desk invariant; where a feed lags, evaluate only bars closed at least the lag-plus-margin ago.
**Prevention:** make "closed only" a property of the snapshot builder, not a per-sleeve habit, so a new sleeve cannot forget it.

### 10.11 Import-time side effects and unguarded ledgers

**Symptom:** duplicate ledger rows appear after innocent refactors; importing a module performs a full data collection.
**Root cause (observed Oct 2026):** a snapshot script ran its main routine unconditionally at module level, so merely importing it re-ran a full snapshot and appended duplicate rows to a ledger that had no duplicate guard (deduplication, where it existed, was by last occurrence per key, which masks duplicates instead of preventing them).
**Detection:** import tests (import every library module in a sandbox and assert no writes); duplicate counts by natural key in every audit window, proven zero rather than assumed zero.
**Cure:** library modules never execute on import; any script that must be run, not imported, says so at its head; ledgers carry duplicate guards or idempotent keys.
**Prevention:** gate-wired scan for module-level executable calls in library trees.

### 10.12 The stopped accrual lane

**Symptom:** a finished-looking tool displays stale or zero data for weeks; downstream forecasts ship flagged as history-building.
**Root cause (observed Oct 2026):** a per-name IV ledger stopped accruing on a specific date with only a handful of readings per name; in a second case, a filings tool sat empty because the requester identity the upstream source requires was never configured; in a third, a short-volume ledger tool shipped complete with zero days stored.
**Detection:** every accrual lane has a freshness check with a threshold and a named owner; consumers print input age; status reports distinguish built, collecting, and proven as separate states.
**Cure:** fix the collector, backfill nothing into the graded record, and let the accrual counter show honest progress.
**Prevention:** a collector silently uninstalled or stalled is detected by absence on a deadline (Section 11), not by someone noticing a quiet dashboard.

### 10.13 Header, user-agent, and parameter exactness

**Symptom:** repeated 401s for a valid credential; valid calls rejected for undocumented parameters; a feed value accepted by one endpoint and rejected by a sibling.
**Root cause (observed Oct 2026):** an analytics API reads its auth header name case-sensitively; a common HTTP library capitalizes header names and therefore sent a differently-cased header, producing 401s for a valid key that was reported dead repeatedly before a raw client preserving header case proved it good. Providers also variously required a specific user-agent on token minting and distinguished feed values by endpoint.
**Detection:** before declaring any credential bad, run one exact-case, raw control probe through a transport that preserves header case (or the exact transport the desk will use).
**Cure:** isolate token minting and auth in one helper per provider; encode accepted parameters as an allowlist in the client.
**Prevention:** a per-provider quirk card beside the connector, written during probing, consulted before every "the credential is dead" or "the API is down" conclusion. Classify auth failures as credential failures versus probe failures; they have opposite cures.

---

## 11. Operations

### 11.1 The daily rhythm

The desk's day is a timetable, and the timetable is a safety system.

**Pre-open inspection (morning, before trading, with a hard stop well before the open).** Charter: run the regression gate first (a failing gate is itself a finding); broker read (identity, equity, positions, open orders); process readiness (every scheduler and runner alive by effects, Section 11.4); yesterday's per-strategy liveness roll, naming every strategy (silent equals open defect); fixture drives for silent or stale strategies; today's calendars (half days, expiries, macro events); verdict READY or NOT READY with open defects named. Morning catch-up on a missed inspection may not edit production code mid-session; repairs stage to the night inspection.

**Intraday cycles.** Snapshot, evaluate, reconcile, dispatch, read back, journal. Watch, by exception: reconcile halts, quarantine events, pending-queue depth and age, watchdog state. Routine cycles are not reported; exceptions always are.

**Midday and pre-close passes.** A midday read (book versus plan, any sleeve behaving unexpectedly, data freshness across producers) and a pre-close pass (day orders' expiry handled, exits for the session complete or explicitly carried, overnight stops verified in place).

**Close review.** Count the day at the final state: submitted, filled, rejected by class, skipped, per strategy; the liveness roll for today; performance marks labelled by mark type; open defects carried forward by name.

**Night inspection and maintenance.** Verify the day actually operated (today's rolls, journal integrity, roster-journal alignment); run the gate again after any repairs; cure defects found, in-pass where they fit inside the rails, with failing-first tests; leave the desk clean for tomorrow: queues drained or named, state files fresh, backup sealed or its blocker named. Separate watchdog jobs check for each inspection's absence (report artifact present with its verdict line, plus the scheduler's run record) and run it in catch-up mode on a miss.

Stagger jobs so two heavy jobs never share a start time. A stale mirror file of a moved job is itself cleaned up and checked; scheduler inventories rot silently otherwise.

### 11.2 Liveness rolls and the malformed-emission census

Every inspection produces two counts that together catch the two quiet failure modes:

- **Liveness roll:** every expected emitter named, with its state: traded, evaluated-no-signal, unfed (producer named), parked (reason as provenance), or silent. Silent is an open defect, never a neutral state. A full-roster census (fed, unfed, parked, by name) is part of every audit.
- **Malformed-emission census:** defective outputs counted by producer: zero-priced intents, missing stops, shape violations, stale-print emissions. The census is what prevents a reject fence from making a broken flagship look acceptable: the fence's catches are the census, and the census is a defect list against producers.

### 11.3 Bug log discipline

Every bug found is logged and blocked from regressing. Fixing without both is not done.

1. **Log it.** A dated bug log per period carries, per defect: severity, file, what broke, the fix. A deliberately-not-bugs section records investigated-and-cleared findings (false positives proven false, design behaviours mistaken for defects, honest limits recorded as limits, not overstated) so nobody re-fixes them.
2. **Block it.** Every fix ships a named regression test, behavioural where cheap, source-assertion where a full harness is impractical, with the fail direction proven (run against pre-fix code or a temporary revert).
3. **Gate it.** The gate script runs every blocker file; all must pass. Inspections run the gate before inspecting and again after fixing. The gate's exit status is the process exit status, proven by a dummy failing blocker (non-zero) and a dummy passing one (zero): a gate piped through a display command that masks its exit code once reported a failing gate as success, which is an integrity failure, not a scripting detail.
4. **Ratchet coverage.** A gate-wired test recomputes coverage every run (Section 3.9). New module without a blocker: red. New test file unwired: red. Coverage removed: red. Exemption ledgers shrink-only and dated.

### 11.4 Living with restarts

Your runtime will restart: host reboots, supervisor heals, platform redeploys, resource pressure. Design as if restarts are hourly, because sometimes they are.

- **Detached long processes survive; session-bound processes die.** Launch long single-process jobs detached (detach from the session, redirect logs, disown), monitored via on-disk state (ledger, cache, progress files), never via a session handle that a restart wipes. Orchestrations that fan out should be resumable from checkpoints on disk, reusing completed stages, rather than resumable sessions.
- **Checkpoint everything.** Prefetch plans, reservations, cadence state, episode markers, scheduler cursors, pending intents: if the desk computes it in the morning and needs it in the afternoon, it lives on disk before the desk acts on it. In-memory plans are a cache, never the record. Two independent desks in the record hit the same family in one week: prefetch plans emptied by morning deploys, and cadence state dying with the process (compounding the duplicate-entry bug of Section 8.1).
- **Supervise by effects, never by self-matching patterns.** Verify a detached process by a PID file it writes itself, by scanning the process table for the interpreter-plus-script pair excluding your own process tree, or best by its effects: result file, log growth, heartbeat advancing. A substring process search once matched the checking command's own command line and reported a dead sequencer as alive. A process that has produced nothing observable is reported as unproven, not alive.
- **Watchdog discipline.** The heartbeat advances only on verified work (written after each completed cycle, with its status). Grace is roughly two to three times the real cycle interval, re-derived when roster or cycle time grows (a grace shorter than the real cycle caused dozens of false restarts and, at one point, a duplicate runner racing the original on the same state files). Single-instance lock on the runner; the watchdog refuses to launch while any runner is alive; a stale-but-alive runner is named, a wedged one is terminated and verified dead before exactly one relaunch; restart intensity capped per window, beyond which the watchdog writes a named degraded state and stops respawning.
- **External dead-man alerts need damping.** An external health-check watcher in the record flapped roughly fifty down/up emails in a day and was retired at the source by operator ruling. Internal supervision first; any future external watcher needs transition damping and a flap test before going live, and is not re-provisioned without an explicit operator decision.

### 11.5 Incident response

When something breaks in session:

1. **Contain by scope.** Halt the affected strategy's entries (exits pass). Halt desk-wide entries if cash or book integrity is in question. Containment is journaled with its reason.
2. **Preserve the exact error.** Refusal bodies, journal rows, snapshot hash, cycle id. Diagnosis without preserved evidence becomes folklore.
3. **Classify** (Section 8.5 and the failure classes of Section 3): implementation, hypothesis, transport, provider, dependency, permission, external, missing choice.
4. **Cure at the source** with a failing-first test, or stage the cure to the night inspection if the session cannot safely absorb it (morning rule, Section 11.1). A fence may stand in the meantime; its catches are counted as defects.
5. **Prove on the final state** and write the incident report (template, Section 14.4): what happened, blast radius by count, root cause, cure, blocker, and what remains open.
6. **Report** with evidence levels. An incident reported as resolved on containment alone will be re-opened by the next inspection, at higher cost.

Anti-spiral rule for diagnosis: if the same class of action fails twice without a revised hypothesis, stop and reassess in writing (known facts, unproven assumptions, last evidence, first failed boundary, smallest discriminating check, protected state). Contradictory evidence during an incident is a stop signal (Section 1.5), not a debate to win.

### 11.6 Context and memory hygiene for the agent

You, the agent, are part of the system, and your context is a resource with failure modes:

- **Write it down or lose it.** Decisions, rulings, quirk cards, fidelity ledgers, and open-item lists live in files in the repository, not in your conversation. A successor agent (or you, after a restart) must be able to become current from the files alone.
- **Keep a running open-items list** in a known location, updated every pass, with each item's evidence and unblock condition. Silence about an open problem is a violation (Section 3.8); a written list is how silence becomes impossible.
- **Record lineage on your own claims.** When you write a synthesis from sources, name the sources and their revisions. Check a peer's recent state before writing into any shared synthesis file; overwriting a peer's fresher version with your staler copy is a known fleet failure (Section 12.6).
- **Distinguish your lanes.** Keep operational reporting, research, and personal or unrelated context in their proper channels as your operator directs. Cross-contamination degrades both the work and the operator's trust in your reporting.
- **Re-read doctrine at program boundaries.** Standing rules recalled from memory are claims; check them against the canonical text at the start of any program-level work and whenever a failure class repeats.

---
## 12. Multi-Agent Collaboration

A fleet of agent desks produces something no single desk can: independent replication. It also produces novel ways to destroy shared work. This section is the fleet's operating law.

### 12.1 Lanes and ownership

Each agent owns named lanes: its desks, its branches, its subtrees, its books. Ownership is per subtree in shared repositories, not per repository. Other agents' trees are read-only reference or fenced mirrors. Before writing any shared synthesis file, check the owning agent's recent state. When the operator directs coverage of a dark peer's lanes (Section 12.7), coverage means carrying its open items and posting its briefs, not impersonating its judgment or merging its book.

### 12.2 The shared channel: append-only, or it dies

Fleets communicate through a shared record (an inbox, a dead-drop, a channel file). Its survival rule is absolute: append at the bottom, never edit or delete another participant's entries, and treat any tooling that syncs the record as capable of destroying it until proven otherwise.

The founding incident: early in one shared channel's life, a peer track's bulk backup sync wiped the shared inbox three times in one evening. The owning track accepted fault the same night, halted all syncs, and adopted the absolute rule. A second peer found the root cause the same night: the sync script updated a branch reference without reading the tree into its index first, so a stale index read as "delete everything." The fix was verified by effects (several overnight batches left the inbox untouched), not by reading the patched script.

Standing practices that follow:

- Exclude shared channels from every bulk or backup sync, by path.
- Add a pre-push check that refuses any push deleting lines from the shared record.
- Treat any bulk sync that can delete as a desk-level emergency until it is proven additive.
- Write entries self-contained (date, author role, numbers, confidence, evidence pointers), because readers have no access to your chat history.
- Post status, not just results: a returning peer should be able to become current from the channel alone.

### 12.3 Vendoring and porting between desks

When one desk adopts another's sleeve:

1. **The strategy file travels byte-identically** and is proven identical by hash, re-verified in regular inspections. A protected product adopted between desks was proven identical on matching inputs, byte for byte, and explicitly never redesigned or retuned.
2. **Adaptation lives in the host:** bridge, registry, dispatcher. If a vendored sleeve misbehaves, fix the host side or send the defect back to the owning desk. Never patch the copy. The duplicate-entry cure (Section 8.1) is the model: the strategy file and its adapter untouched, the cure entirely in the host's desk layer, the vendored copy still byte-identical afterwards.
3. **Differential-test on shared fixtures** before declaring a port live: same inputs, same intents out.
4. **Record which layers were not ported.** Port audits that found defects found them in the wiring around a faithful core (a journal not connected, a tie-break flaw, entry orders missing a limit price), not in the ported core itself. Audit the wiring hardest.
5. **Post your adoption questions** (Section 12.4) with the installed hash.

### 12.4 Asking good questions, and answering them honestly

The highest-value traffic in a multi-desk channel is not announcements; it is precise, falsifiable questions about a peer's sleeves: does this size formula really collapse to a constant, is this stop scaled to its book, does this sleeve ever flatten, what happens when this gate is gated off? A peer who must actually run your code reads it as no reviewer does: every constant must resolve, every gate must have a producer, every stop must bind somewhere. Questions that survive that reading concentrate exactly where the originating desk's familiarity blinded it. In the record, a week of such questions exposed a genuine dispatcher gate defect (the sell-as-exit flaw of Section 4.7), logged as a found defect and cured the same night the answers were posted.

Protocol: when adopting, post numbered questions with the installed hash. When answering, read the code first, never answer a mechanism question from memory, and classify each answer honestly: our bug (log it, cure it), the source's design (only the owner can re-rule it), or already handled (point to where the record separates what the questioner feared was conflated).

### 12.5 Verifying a peer's handback before repeating it

A peer's completion report, adoption claim, or save receipt is a claim until checked at the final state it names (Sections 1.5, 3.7). In practice:

- Re-run the lookup against the named tree, branch, and revision. Check byte identity where identity is claimed. Count outcomes at the final state.
- Publish the coverage of your own verification alongside the verdict: searched, excluded, unavailable, pagination. "I cannot find it" is always a coverage statement, never "it does not exist." One verification pass in the record enumerated dozens of repositories searched, the global commit search, code search, tree scans (and the one tree known to truncate), and local workspace search before grading anything, and then graded every dependent claim UNVERIFIED: not refuted, with the method check shown (the same lookup resolves a known-good commit), the precise ask stated (which repository, which branch, the full identifier), and the checkable sub-claims answered on their merits. That is the model report.
- Carry unverified items forward by name until they resolve. An unverified item dropped from later reports has been silently upgraded to forgotten, which is worse than either verdict.
- Grade the verification, not the claim: proven, partial, blocked, unverified are properties of your evidence, stated as such.

The roster-versus-catalog reconciliation is the same discipline in accounting form: diff name by name, every id in exactly one named bucket (present; excluded by a stated design rule; genuinely missing), buckets summing to the roster total. In the record's canonical diff, the gap was recency: every missing id had been installed after the catalog's last update. Expect recency; prove it anyway. Use the roster file the runner itself loads as the source (candidate lists from directory names, adapter filenames, or test comments each produce a different wrong diff), settle variant folding before counting, and record for each missing id whether its code file is also missing or only its catalog entry, since the two gaps close differently.

### 12.6 Divergent copies and merge discipline

Two divergent copies of the same application in one repository is a standing hazard: each gains what the other lacks, there is no longer a main copy, and anyone checking out the wrong one gets a silently incomplete desk. In the record, one branch carried a forecast package, its lab, the full test suite, and publisher tooling but not the live runtime; another carried the deployed runtime snapshot but its copy of the shared application folder was frozen at the merge-base state, missing the lab entirely (the deployed bundle contained zero occurrences of a key term from the newer work). A blob-level diff counted the collision in advance: dozens of paths changed on both sides, plus whole subtrees present on only one.

Rules: keep one canonical copy per application per repository; if a deployment snapshot must be stored, store it in a clearly named snapshot area and never let a second full copy age in place; diff divergent copies at blob level and publish the path count before attempting a merge; when two versions of a sleeve circulate, name the authoritative one in the channel and prove equivalence or difference on fixtures.

A repository snapshot of a deployed system is partial by construction: a built bundle plus server sources is not the system. For every snapshot, record which production revisions it corresponds to, which parts are held elsewhere (in the record, the browser application's unbuilt source and the deployment revisions themselves lived on the hosting platform, not in the repository), and the rebuild test's result. Run the rebuild before calling anything a backup. Keep version statements in generated documents single-sourced, so a stale paragraph cannot survive a deployment and mislead a fast reader about which build is live.

Pin the head you read. Long passes over a peer's work record the exact head inventoried, and re-check for movement before finalizing adoption verdicts, because an active peer commits during your pass (in the record, a branch advanced twice during one analysis, adding material that changed several adoption ranks; the pass recorded the movement, analysed the new material, and stated which earlier statements the new head falsified). Treat a peer's fast-moving synthesis files as a subscription, not a copy: re-fetch at adoption time.

Ownership fences belong in the write path. In the record, one desk's save machinery overwrote a peer's hardened files in the peer's own subtree with stale local copies; the cure restored the peer's versions by hash, fenced the save machinery off that path mechanically (a check that raises before any network call, with a refusal log, and a deliberate human-directed restoration as the only override), and settled a disjoint-prefix rule proven by read-back scoped to each desk's own prefix. "The save ran" is never evidence about which trees it touched.

### 12.7 Silence is not disengagement

Agent peers go silent for capacity reasons (usage limits, host pressure) far more often than for substantive ones. In the record: a research track dark for days on a usage cap returned with no penalty and no re-litigation; a master-desk implementation dark for about five days received a posted week-rundown so it could resume current, and on a later absence the operator directed a full covering brief (its lanes, other desks' lanes, shared index state, what was being covered for it) with its open verification items carried forward by name, still unverified, still not refuted.

Practices: state your own reading cadence in your introduction post (one peer reads the channel only when brought there or at scheduled check-ins, so correspondents allow a day for answers). Never let a blockers post age unanswered: answer with evidence, including when the honest answer is "tested but unproven." When a peer goes dark, post the covering brief; do not duplicate its work and collide with it on return. And keep books separate even while covering: consilience without merger (below).

### 12.8 Separate books are a feature

Peer desks exchange findings, questions, and code while keeping books, rails, and risk rules separate unless the operator explicitly merges them. Agreement on a finding does not imply agreement to adopt the finding's owner's constraints: in the record, a peer track accepted a shared pullback conclusion and in the same period explicitly declined the primary desk's sector cap, drawdown brake, and a sleeve kill, reaffirming later that its book stays separate. Two desks running the same finding under different rails produce information neither could produce alone, including the strongest evidence in the record: two desks independently reverse-engineering the same vendor product in the same week, with different tooling and different code slices, agreeing on every checkable point. The agreement counted as evidence precisely because the passes were independent. When the operator does order a merge or adoption, execute it as a named event with hash proof, not as a gradual drift of copies.

### 12.9 Status taxonomies: keep the axes separate

Fleets confuse themselves by using one axis's vocabulary to answer another axis's question. Keep all of these axes, each answering its own question:

| Axis | Values | Question it answers |
|---|---|---|
| Engine surface state | live; research only; manual lab; stub (returns not-connected); shared machinery | Is it wired to real data, a person, or nothing? |
| Data readiness | core-research; conditional-data; experimental | Can it be fed honestly today, and with what data? |
| Edge-card status | hypothesis (the only status until evidence is reviewed by a non-author) | Has anyone else reviewed the evidence? |
| Catalog row status (per desk) | live; waiting; blocked; off; (the same strategy can hold different statuses on different desks) | What is this row doing on this desk now? |
| Catalog lifecycle | installed; replaced (successor linked); merged (merged-into linked); blocked; off | Where did this identity go? |
| Desk health per sleeve | fed; unfed; parked (reason as provenance) | Is silence explained, and by what dependency? |
| Verification grade | GREEN; PARTIAL; BLOCKED; UNVERIFIED | What does the evidence support saying? |
| Fill mode | simulated; shadow; live-paper | Which matching engine produced this number? |
| Forecast outcome | taken and scored; taken as scored zero; abstained with codes; abstained without codes (counted separately) | Did the system look, refuse, or find nothing? |

### 12.10 Score honesty between desks

When two desks build forecast machinery independently, the deliverable is the honest map: overlap, partial overlap, no counterpart, and direct conflict, named rather than averaged away. In the record's comparison, one set organized by classical forecast family with an explicit payer story per engine, the other around measured corpus results and meta-forecasting over its own forecasters; conflicts (a drift engine versus a counterpart centred on zero because its record holds no drift edge; a reversion gate attenuating exactly where a reversal engine fires) were published as open design questions with owners.

Underneath the map sits vocabulary discipline: a signed score clipped to a fixed range, and a risk rank passed through a sigmoid, both look like probabilities to any downstream reader. Label score semantics in the data, not in documentation: calibrated probability stays null until calibration exists; probability metrics refuse uncalibrated inputs; risk values are never rendered in a probability format; neutral baselines are printed beside risk values. Several risk engines in the record sit in the familiar probability range on completely neutral inputs: arithmetic lies by resemblance unless the labels stop it.

Adoptions across desks are ranked and itemized (adopt as-is; adapt then adopt; already have; skip), every inventoried item mapped exactly once, each adopted item landing with a fail-first regression test and a ledger entry recording its final-state proof or its named open remainders.

---
## 13. Common Pitfalls Master List

Each entry: the trap, then the rule that avoids it. Details live in the sections cited.

1. **Treating a submit acknowledgement as a fill.** Fills count only from broker read-back by client order id. (§8)
2. **Resending on timeout.** Never resend blind; look up by client order id first. The original may be live. (§8.3)
3. **Keying intent identity on wall-clock time or a restartable counter.** Key on the data bar, symbol, kind, side. Restarts must reproduce identity, not mint it. (§8.1)
4. **Holding episode state only in process memory.** Persist episode-taken markers, cadence state, plans, and cursors to disk before acting. (§8.1, §11.4)
5. **Letting strategies call the broker or the network.** Sleeves emit intents over a read-only snapshot; one dispatcher, one door, producers only on the network. (§4)
6. **A second module that can submit orders.** Audit: broker submit/replace/cancel callable from exactly one module. (§4.7)
7. **Gating on buy/sell instead of intent kind.** Short entries are entries. Gates key on kind and position intent. (§4.7)
8. **Skipping reconciliation, or reconciling nightly only.** Reconcile every cycle, before dispatch; per-strategy halts, desk-wide halt on cash. (§4.8)
9. **Reconciliation that counts pre-epoch fills after an account switch.** Epoch-aware derivation; fresh baseline through your own door. (§4.8)
10. **No baseline at adoption.** Record the pre-desk book as legacy on day one, or manufacture phantom discrepancies forever. (§4.8)
11. **The same value in two shapes across a boundary.** One canonical shape per concept; populated fixtures; test in the mode you will run. (§10.9)
12. **Testing on an empty book, an idle strategy, a closed market.** Each proves the wrong thing confidently. Populate, arm, and open your fixtures. (§10.9)
13. **Grading a reject fence as a fix.** Containment is not a cure; fence catches are open defects against the producer. (§3.8)
14. **A pending queue with no drain caller, or a class-blind drain.** Transient stays pending, terminal drains as terminal, stale expires unsent. Test the drain. (§6.7)
15. **Dropping intents on transient broker failure.** Journal before submit; queue; drain on recovery; prove exactly-once with fault fixtures. (§8.5)
16. **Reading only the status code on a rejection.** Capture and journal the body; classify terminal, transient, external, scheduling, idempotency. (§8.5)
17. **Calling a duplicate client-id rejection an error.** It is idempotency working. Confirm the original by read-back. (§8.5)
18. **Phantom exits against flat or opposite broker positions.** Exit pre-flight resolves the broker position first; mismatches refuse locally. (§8.6)
19. **Exit freshness gates copied from entries.** Due exits refresh their own inputs and execute on the best available mark, labelled late. (§8.6)
20. **Pricing and gating off the stale signal print.** Re-price at decision time; gates read fresh state; stale-pass/fresh-refuse fixtures both ways. (§8.7)
21. **Legging out of multi-leg options.** Close as one multi-leg order. No bracket shortcut for options. (§8.8)
22. **Assuming bracket legs protect a partial fill.** Legs may stay inactive until the parent fully fills. Design for the partial case. (§8.8)
23. **Trusting a feed's volume because its prices are fine.** Trust is per field. Consolidated tape for volume; reconcile intraday sums to daily totals. (§10.1)
24. **Assuming bars APIs return the latest bars by default.** One common shape returns null without a start, then the earliest page with one. Paginate and slice. (§10.2)
25. **Guessing a sibling endpoint's path or parameters.** Options lived under a different version path; contracts rejected plausible parameters. Probe and allowlist. (§6.4, §10.13)
26. **Designing on unprobed fields.** Snapshots may carry no greeks or IV; chains may carry no OI. Coverage is per field, per endpoint, per tier. (§5.1)
27. **Coercing absent to zero.** Null stays null; modelled substitutes are labelled modelled; dependents are named blocked or unfed. (§5.1)
28. **Trading on a forming bar.** Closed bars only, enforced in the snapshot builder. (§10.10)
29. **Dating bars naively across anchor and timezone conventions.** Parse instants, convert to exchange time, test around midnight and clock changes. (§10.6)
30. **A strategy abstaining silently because its input was never produced.** Unfed is a named state computed from the producer registry, with the producer error named. (§4.2)
31. **A collector or ledger stopping silently.** Freshness checks with thresholds and owners; consumers print input age; built, collecting, and proven are separate states. (§10.12)
32. **Library code that executes on import.** Modules never run on import; ledgers carry duplicate guards; duplicate counts proven zero. (§10.11)
33. **Declaring a credential dead from a broken probe.** One exact-case raw control probe before any credential verdict. Probe bugs mimic dead keys. (§10.13)
34. **Verifying a process by a pattern your own command contains.** Verify by PID file, interpreter-plus-script scan excluding your tree, or best by effects. (§11.4)
35. **A watchdog grace shorter than the real cycle.** Grace at two to three times the cycle interval, re-derived as the roster grows; single-instance lock; restart-intensity cap. (§11.4)
36. **Session-bound long jobs.** Detach, checkpoint to disk, monitor by on-disk state. Session handles die with the session. (§11.4)
37. **A human-flip step at a market time.** Automate mode transitions in code with a proof artifact; manual is the fallback. (§9.6)
38. **An external alert watcher without damping.** Flap tests and transition damping before going live, or the watcher becomes the outage. (§11.4)
39. **A gate whose exit code can be masked, or blockers that are not wired in.** Exit status is the process status, proven with dummy blockers; coverage ratchets mechanically. (§11.3)
40. **A fix with no bug-log entry and no blocker.** Cure, log, blocker with proven fail direction, or the fix is incomplete work. (§11.3)
41. **Reporting a save as sent rather than read back.** Saves are proven by independent read-back, reported verified over enumerated. (§3.10)
42. **Repeating a delegated completion report without checking the tree.** A handback is a claim. Verify head, commits, files, gate output first. (§12.5)
43. **Reporting "not found" as "does not exist."** Absence claims carry a coverage ledger: searched, excluded, unavailable, pagination. (§12.5)
44. **Editing a vendored sleeve to fix a host bug.** Vendor byte-identically, hash-pin, fix the host or return the defect to the owner. (§12.3)
45. **Letting a bulk sync touch the shared channel.** Append-only record; shared paths excluded from syncs; pre-push deletion checks. (§12.2)
46. **Letting your save machinery write into a peer's subtree.** Ownership fences in the write path, raising before any network call, with a refusal log. (§12.6)
47. **Two divergent copies of one application ageing in place.** One canonical copy; snapshots in named snapshot areas; blob-level diffs before merges; pin the head you read. (§12.6)
48. **Counting roster rows as strategies, or strategies as roster rows.** One catalog entry per strategy, variants folded with row ids preserved; roster and catalog reconciled in named buckets. (§7.7)
49. **Merging cross-desk identities on name similarity.** Crosswalk first, merges only under stated evidence tiers, unresolved stays unresolved. (§7.9)
50. **Backfilling a ledger to hide an accrual gap.** Priors replay from real records, labelled; graded records are never backfilled. (§3.12)
51. **Collapsing a scored zero into an abstention.** Taken-and-zero is a taken row; abstentions carry reason codes and are audited separately. (§7.6)
52. **Rendering an uncalibrated score as a probability.** Semantics live in the data; probability stays null until calibrated; metrics refuse uncalibrated inputs. (§12.10)
53. **Backtest flattery: survivorship, fill basis, look-ahead, grain overreach, benchmark shopping.** State assumptions on the result; pre-register benchmarks and horizons. (§7.5)
54. **Publishing performance in dollars from an arbitrary paper balance, or from unstable marks.** Percent versus benchmarks from a stated epoch; label mark type; decline figures the marks cannot support. (§9.7)
55. **A terminal implying live freshness it does not have.** Date every layer on the surface; scope live claims to observed sessions; consume data from producers, not displays. (§10.7)
56. **Declaring a publish outage from a stale CDN copy.** Verify against the authoritative contents API; re-check after minutes before escalating. (§10.7)
57. **Unbounded queues, caches, and retries.** Every bound named, with a shedding policy, or a named append-only reason. Fixture the bound. (§3.11)
58. **One heavy job at a time is a rule, not a mood, on a small host.** Measure effective memory and disk; keep full-history derivations out of hot paths. (§5.3)
59. **Shrinking the task to green the report, or inheriting baseline defects silently.** Acceptance matrix first; baseline defects cured with blockers or carried named. (§3.2)
60. **Silence about an open problem.** Open items stay named at the top of reports, with evidence and unblock conditions, until cured or ruled. (§3.8)

---

## 14. Templates and Checklists

Copy these. Fill them in the repository, not in chat.

### 14.1 Sleeve spec template

```markdown
# Sleeve Spec: <strategy-id>  (spec version: <n>, frozen: <date>)
## Identity and lineage
- Strategy id / roster row ids / aliases:
- Source (original / ported from / adapted from), with hash pin if vendored:
- Mode at deployment (simulated / shadow / live-paper):
## Universe and schedule
- Universe:  Timeframe(s):  Cadence:  Session:
- Producer(s) it depends on (registry names):
## Inputs
- Snapshot keys consumed, with freshness requirements:
## Entry rules (complete)
- <numbered rules; every constant resolved to a value or a named config key>
## Exit rules (complete)
- Stop:  Target:  Time exit:  Structural exit:  Expiry behaviour:
## Sizing and limits
- Sizing rule (formula; must vary with its inputs):  Slice:  Max positions:
- Per-trade risk cap:  Sleeve daily loss limit:
## Refusal conditions
- <stale, unfed, gate-failing, slot-full, cap-reached, spread, hours...>
## Fill and judging assumptions
- Fill basis:  Benchmarks:  Epoch:
## Fidelity ledger (if source is thin)
- Rule sketch / missing fields / fidelity risk / resolution route:
## Kill / retirement criteria (pre-registered)
- Sample size:  Statistical bar:  Review date:
```

### 14.2 Build brief template

```markdown
# Build Brief: <task name>
## SCOPE
- Surface (what changes):
- Constraints (what stays untouched, incl. hard rails):
- Outcome (observable success):
- Proof (evidence that will demonstrate it, from the final artifact):
- Edges (boundaries, dependencies, peer lanes):
## Acceptance matrix
| Row | Requirement | Result (PASS/FAIL/BLOCKED/UNVERIFIED) | Evidence |
## Baseline defects found during scoping
- <each: cured in this build with blocker <name> / carried open as <name>>
## Fault rows
- Kill worker mid-cycle / corrupt snapshot / kill desk mid-session and
  restart / plant reconcile discrepancy: expected observable result each.
## Deliverable and verification route
- Final artifact:  Gate to run:  Read-back route for any save:
```

### 14.3 Verification checklist

```markdown
# Verification: <claim being verified>
- [ ] Claim restated exactly as made (source, date, named final state)
- [ ] Final tree / head / revision checked directly (not via the report)
- [ ] Files claimed actually exist at the named paths
- [ ] Gate run on the final tree; exit code observed unmasked
- [ ] Counts recomputed at the final state (submitted/filled/rejected/
      skipped, or verified/enumerated for saves)
- [ ] Byte identity checked where identity is claimed (hashes)
- [ ] Coverage ledger written (searched / excluded / unavailable /
      pagination) for any absence claim
- [ ] Verdict in one word: GREEN / PARTIAL / BLOCKED / UNVERIFIED
- [ ] Unproven remainder named; carried-forward location noted
```

### 14.4 Incident report template

```markdown
# Incident: <date> <short name>   Severity: < >
## What happened (timeline with cycle ids / snapshot hashes)
## Blast radius (counts: intents affected, orders, strategies, sessions)
## Evidence preserved (refusal bodies, journal rows, logs, paths)
## Classification (implementation / hypothesis / transport / provider /
   dependency / permission / external / missing choice)
## Root cause
## Containment applied (and its journal entries)
## Cure at the source (files, summary)
## Regression blocker (name; fail direction proven how)
## What remains OPEN (named, with unblock conditions)
## Report history (what was claimed when, corrected by what evidence)
```

### 14.5 Catalog entry template

```markdown
## <strategy name>  (catalog id: < >)
- Roster row ids (all variants folded here):
- Aliases / lineage (ported from, adapted from, successor of):
- Type: <equities / options multi-leg / paired / forecast / monitor...>
- Status per desk: <desk role: live/waiting/blocked/off>
- Lifecycle: installed <date> / replaced by <link> / merged into <link>
- Algorithm (from code, with file:line citations; mark PARTIAL + gap
  where the source records only part of the rules):
  - Entry:  Exit:  Sizing:  Data:
- Data readiness: <core-research / conditional-data / experimental>
- Edge card: mechanism / exact outcome / price-aware baseline /
  hypothesized payer / bad state / decisive test / kill rule
- Exclusions check: no licensed, host-bearing, or credential material
```

### 14.6 Daily inspection checklist

```markdown
# Inspection: <date> <morning|night>
## Gate
- [ ] Regression gate run BEFORE inspecting; exit code: ___ (fail = finding)
## Morning only: readiness
- [ ] Broker identity + equity + positions + open orders read back
- [ ] Yesterday liveness roll complete; every name accounted for
- [ ] Fixture drives run for silent/stale strategies
- [ ] Calendars checked (half day / expiry / macro)
- [ ] Verdict: READY / NOT READY (open defects named below)
## Night only: the day actually operated
- [ ] Today's rolls counted at final state (submitted/filled/rejected
      by class/skipped, per strategy; exits counted separately)
- [ ] Malformed-emission census by producer
- [ ] Journal integrity (roster alignment, zero corrupt lines)
- [ ] Repairs cured in-pass listed, each with blocker name
- [ ] Gate run AFTER repairs; exit code: ___
- [ ] Backup seal status (PROVEN / blocker named)
## Always
- [ ] Processes verified by effects (heartbeats advanced, logs grew)
- [ ] Pending queue depth/age; reconcile halts by name
- [ ] OPEN items carried forward (name, evidence, unblock condition):
```

---
## 15. A 30/60/90-Day Build Plan

Timings assume one agent working with an operator who rules promptly. The stages matter more than the calendar: do not advance a stage whose definition of done is unmet, and do not let the calendar talk you into calling an unproven stage done.

### Days 1–30: One sleeve, end to end, supervised

**Build:** repository and schemas (§6.2); paper broker connection with all five transport proofs (§6.3); provider probing with quirk cards (§6.4); bars pipeline and the chain-snapshot accrual job started (§6.5); the first sleeve behind a frozen spec, fixture-driven to flat (§6.6); dispatcher with journal-before-submit, client order ids, and read-back (§6.7, in embryo: gates and pending queue may be minimal but must exist); reconciliation before dispatch (§6.8); bug log and gate script live from the first fix.

**Definition of done for Stage 1:**
- The first sleeve completes signal → order → fill read-back → position → exit → flat against the real paper broker, and the same round trip in fixtures against the simulated broker.
- Identity, control-call, read-back, and idempotency probes are recorded with dates.
- A planted reconciliation discrepancy halts the sleeve's entries and passes its exits, proven in a fixture.
- Every defect found so far has a bug-log entry and a gate-wired blocker with proven fail direction.
- The chain archive holds real snapshots with a manifest, including failure lines. (Its count will be small. Small and real is the point.)

### Days 31–60: A hardened roster

**Build:** producer registry with fed/unfed computation; bounded worker pool with timeouts; pending queue with class-aware drain and fault fixtures (broker-down recovery exactly-once; kill-and-restart zero-duplicates); quarantine for malformed emitters; epoch-aware reconciliation; terminal snapshot with its contract tests; scheduler and watchdog by effects with locks and restart caps; twice-daily inspections on charter; backup proven by read-back and running on schedule; second through fifth sleeves through the full lifecycle (§7), including at least one refusal-heavy fixture set each; catalog started, reconciled against the roster in named buckets.

**Definition of done for Stage 2:**
- The morning inspection prints READY or NOT READY with defects named, from evidence, for seven consecutive sessions, and the night inspection leaves a clean desk each time.
- The malformed-emission census and liveness roll appear in every inspection; no silent sleeve survives an inspection unnamed.
- A whole-desk kill-and-restart drill in a live paper session produces zero duplicate orders and a clean reconcile, with the drill report filed.
- The save seal prints PROVEN for the current head; a restore into a fresh directory passes the gate there.
- Roster-versus-catalog diff reconciles exactly, buckets summing to the total.

### Days 61–90: A research-producing desk

**Build:** the full strategy lifecycle as routine (intake, fidelity ledgers, pre-registered kill rules); forecast or signal products, if any, under ledger-before-display grading at fixed horizons against pre-registered benchmarks; variant accounting and, if a second desk or implementation exists, the crosswalk and deduplicated accounting standard (§7.9); performance reporting in percent versus benchmarks from the recorded epoch, with mark types labelled; efficiency measurement of the cycle (complete path, stage attribution, dominant constraint repaired, re-measured identically); the fleet disciplines of Section 12 if peers exist (append-only channel with deletion checks, vendoring by hash, verification protocol, covering briefs); streaming greeks/prints and a cost model, if the desk's asset classes need them, closing the two first-principles gaps named in Section 5.6.

**Definition of done for Stage 3:**
- Every published figure (performance, forecast grades, catalog counts) is recomputable from its ledger alone, and an independent recomputation (by a peer or a fresh pass) matches.
- At least one strategy or engine has been retired or killed by its own pre-registered rule, proving the kill machinery works. A desk that has never killed anything has grading machinery it does not obey.
- Open items, if any, are few, named, and carried at the top of reports with unblock conditions. (Zero open items claimed is a smell; a small named list is a healthy desk.)
- The desk survives a full inspection cycle with the operator absent: it stands down correctly on a planted fault, queues its escalations, and resumes cleanly on the cure.

### Beyond 90 days

Scale what is proven: more sleeves only through the lifecycle, more asset classes only through new round-trip proofs per family, more desks only through the fleet disciplines. Revisit the maturity ladder (§2.4) quarterly. The desk you want at one year is not a bigger version of the day-30 desk; it is the day-90 desk with a longer record, a deeper archive, and a shorter open-items list.

---

## Appendix: The One-Page Operating Contract

*Hand this page to any LLM agent verbatim before its first shift on the desk. It does not replace the guide; it is the guide's enforceable core.*

---

**Operating Contract: Agent-Operated Trade Desk**

You operate a paper-first trading desk. The broker's book is the truth for money; the journal is the truth for intent; when they disagree, that is a defect, not a tie.

1. **Scope first.** State Surface, Constraints, Outcome, Proof, Edges before work. No green while any acceptance row is open.
2. **Paper only.** The door refuses live environments in code. You never route around that refusal.
3. **One snapshot, one dispatcher, one door.** Strategies read a read-only snapshot and emit intents. Only the dispatcher creates orders. No strategy touches the network or the broker.
4. **Journal before submit.** Every intent is journaled before any submission attempt. Every order carries a client order id derived from the signal data (strategy, newest bar read, symbol, kind, side), never from wall-clock time.
5. **An acknowledgement is not a fill.** Fills and positions come only from broker read-back. On timeout, never resend blind: look up by client order id first.
6. **Reconcile before dispatch, every cycle.** Journal-derived versus broker read-back. Per-strategy discrepancy halts that strategy's entries; cash discrepancy halts entries desk-wide; exits always pass. Restart order: reconcile, unprotected-position sweep, then entries.
7. **Fail closed, by name.** Corrupt snapshot, stale input, unreconciled book: no dispatch for the affected scope, journaled and named. Unfed is a state, never a silent abstention.
8. **Classify failures before acting.** Terminal validation, transient transport, external account condition, scheduling fact, idempotency working: each has a different cure. Read refusal bodies, not just status codes.
9. **Fix at the source.** A fence is containment, never a cure. Every fence catch is an open defect against its producer, named at the top of reports until cured and proven.
10. **Every fix ships three things:** the cure, a dated bug-log entry, and a gate-wired regression blocker whose fail direction was proven. The gate's exit code is never masked.
11. **Evidence levels, always.** GREEN is proven on the final artifact. PARTIAL names the proven part and the rest. BLOCKED names the exact unblock. UNVERIFIED is stated, never upgraded by repetition. A completion report, including yours, is a claim until verified against the final tree.
12. **Saves are proven by read-back.** Report verified over enumerated. No read-back proof, no deletion of local bulk, no "saved."
13. **Verify processes by effects.** Heartbeats, log growth, result files. Never by a process pattern your own check can match. A process with no observable effects is unproven, not alive.
14. **Respect lanes and rails.** Peers' trees and books are fences. Vendored code stays byte-identical; fix the host. The shared record is append-only; nothing is deleted from it, ever.
15. **Escalate with evidence.** One-sentence question, receipts, options with consequences, your labelled recommendation, what stays open meanwhile. Live money, risk changes, gate exceptions, and unexplained book discrepancies always escalate.
16. **Absent is not zero, and silence is not health.** Missing fields stay null; modelled values are labelled; silent strategies are open defects; open problems are never dropped from reports by silence.

Signed by the operator: ______________________  Date: __________

Acknowledged by the agent, with the desk's scope document and hard rails attached: ______________________

---

*End of guide. Build the machinery, prove it on the final state, and keep the open items named. The desk's record, honestly kept, is the strategy.*
