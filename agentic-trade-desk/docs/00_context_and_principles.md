# 00 — Context and principles

> **Read this first.** Everything else in this guide is a consequence of the ideas on this page.

## 0.1 What this guide is

This is a build manual for an **agentic trade desk**: a software system, operated largely by AI agents (LLMs with tools), that

1. turns *strategy rules* ("sleeves") into *decisions* from market data,
2. turns decisions into *orders* (simulated or on a broker's **paper** account),
3. keeps an **auditable book** that always agrees with the broker,
4. keeps itself running (supervision, failover, backups) without a human watching every minute, and
5. reports honestly on what it did and what is broken.

It distills generalized lessons from iterative desk-building work involving human operators and AI agents with research, coding, and review roles. The failure patterns are presented as anonymized composites; no account, desk, person, or private deployment is identified. A first-time builder can use them to design local safeguards, then verify those safeguards against the actual code and providers in their own environment.

## 0.2 Risk note (not optional)

* **This is not financial advice.** Nothing here says any strategy makes money. Most strategies do not, and a backtest that looks good is usually wrong.
* **Start on paper and stay on paper.** Use a simulated broker first, then a broker's *paper-trading* account. Do **not** connect real money until (a) the desk has run unattended on paper for a long period, (b) you have personally audited every order path, and (c) you accept that you can lose all of it. Even then, treat this guide as a source of ideas, not as certification.
* **Never give an agent authority you have not bounded.** The architecture below limits what an agent can do (single order path, allow-lists, caps). Keep those limits.
* Software here is educational reference code. It has no warranty.

## 0.3 Who this guide is written for (you, the LLM)

You are an agent that has been pointed at this repository and asked to help build or operate a trade desk. You can read files, run shell commands and write code. You *cannot* see the human's intent unless they tell you, you *forget* between sessions unless you write things down, and you are prone to saying "done" when something merely *looks* right. The guide is written to counter those tendencies. See `../AGENTS.md` for your standing rules.

## 0.4 The nine principles

Each principle is stated, justified by a real failure, and tied to the document that implements it.

### P1. One order path
Exactly **one component** in the whole system is allowed to send real (paper) orders. Everything else is *simulated* or *advisory*.
*Why:* a desk had a research loop that simulated fills and a separate engine that sent real paper orders. Positions in the book and at the broker drifted apart for days because "the desk is trading" meant two different things. When a cloud failover was added later, the rule "only the primary engine sends orders, the failover sends only while the primary is stale and only with the same ids" was what kept it safe.
→ `05_execution_and_order_safety.md`

### P2. Idempotency by construction
Every decision has a **deterministic id derived from data** (sleeve, symbol, the data bar that triggered it, side, leg, attempt), and the id is written to durable storage *before* the order leaves the machine. Restarting, retrying, or running twice must be harmless.
*Why:* a strategy library stamped signals with the *pass's wall-clock time*; every restart looked like a new signal; the same signal was entered four times in one morning.
→ `05`, `10_pitfalls_catalog.md` (P-01…P-04)

### P3. The ledger is truth; state is a fold
Keep an **append-only, hash-chained event ledger**. Current positions are a pure fold over events and must equal the live in-memory book on every pass. Corrections are new events, never edits.
*Why:* when two writers disagreed about the book, the only way to tell who was right was a replayable history.
→ `06_state_reconciliation.md`

### P4. Reconcile with the broker every pass — and never "fix" by trading
Compare book vs broker per symbol, allowing for in-flight orders. Mismatch → **alert**, repair the *book* from broker truth (add-only import), never place an order to "make them match".
→ `06`

### P5. Fail safe by failure class; preserve the book
Do not make every warning a desk-wide stop, and do not let an alert-only monitor stand in for a safety control. A sleeve-specific fault should normally block that sleeve's new entries while healthy sleeves continue. Missing, stale, malformed, or mismatched inputs block the affected decision; shared data-identity failures, account mismatches, ledger corruption, unexplained broker state, risk-limit breaches, and duplicate/unknown order outcomes can require a desk-wide **entry pause** or **emergency stop**. Define these states and their exact effects in deterministic code, outside the LLM.

An emergency stop must specify what happens to queued and working entry orders, exits, broker-native protective orders, and existing positions. Keep ownership and exit obligations intact. Do not cancel protective orders or liquidate positions merely because a monitor failed; use trusted inputs and a preapproved contingency policy, and escalate when safe action cannot be established. Every stop and recovery is durable, visible, tested, and attributable. Never fabricate a price or silently resume after a critical integrity failure.
*Why:* overbroad gates can suppress valid decisions for days, while alert-only monitoring can allow unsafe exposure after a shared failure. Controls must isolate local faults and stop risk growth when critical invariants fail.
→ `07_reliability_ops.md`

### P6. Assume the machine will be paused, wiped, rolled back, or killed
Design for: process death, VM pause (wall-clock jump), disk rollback to an earlier snapshot, memory kills, network stalls, provider outages, usage limits on the *agents themselves*. Use hard deadlines, monotonic clocks, supervisors, off-box backups and a failover.
→ `07`

### P7. Evidence before "green"
A status is **GREEN** only when the *final* artifact has been exercised at the boundary the claim names (a real pass against the real or faithfully faked broker; a restore drill from the backup; a restart that did not re-enter). Otherwise say PARTIAL, BLOCKED or UNVERIFIED. "The command exited 0" is not evidence.
→ `08_research_and_validation.md`, `11_checklists.md`

### P8. Every bug becomes an invariant, a test and a log row
When something breaks: write the incident, find the *first failed boundary*, make the smallest structural fix, add a **regression guard that fails on the old code**, and record it where the next agent will find it.
→ `10`, `09_multi_agent_coordination.md`

### P9. Autonomy has a perimeter
Agents repair the desk on their own (restart a loop, fix a timeout, add a test, import an orphaned fill). Agents **ask a human** for: enabling real-money trading, changing risk limits upward, deleting data, force-pushing, spending money, publishing externally, circumventing a provider's geo-block or terms. Know which side of the line you are on. Do not ask permission for repairs inside the perimeter — that wastes the human's attention and was a repeated complaint.
→ `AGENTS.md`, `09`, `12_security.md`

## 0.5 Vocabulary

| term | meaning |
|---|---|
| **desk** | the whole system: engine, data, ledger, broker adapter, supervisor, reporting |
| **sleeve** | one strategy with its own entry rule, exit rule, size rule, budget and slot cap. A sleeve is a *unit of accountability*. |
| **lane** | the allocation container of a sleeve: `max_slots`, `budget_usd`, entry window, size class. Often used interchangeably with sleeve; a family may share one lane. |
| **slot** | one concurrent position (or queued entry) a lane may hold |
| **pass** | one scheduled evaluation cycle: recover → exits → entries → reconcile → snapshot |
| **fire / signal** | the strategy's output that says "this symbol qualifies" (usually dated; may have a validity window) |
| **intent** | a decision to send an order; written to the ledger first |
| **cid** | client order id: deterministic id the broker echoes back, used for idempotency and lookup |
| **shadow** | simulated mode: fills at the last observed mark, no broker contact |
| **paper** | real orders on a broker's simulated-money account |
| **live** | real money. **Out of scope for this guide.** |
| **heartbeat** | file/record the primary writes to prove progress |
| **primary / standby** | the full desk / a small failover that trades only when the primary is stale |
| **dead-drop** | a shared inbox file in a git repo that agents use to hand messages to each other |
| **undo copy** | a copy of any file you change, kept in an `evidence/undo/` folder before editing |

## 0.6 The shape of the journey (what to expect)

A realistic build takes weeks, not hours, and passes through these stages. Skipping a stage is the main source of the failures catalogued in `10`.

1. **Skeleton on a simulated broker** with one trivial sleeve, a ledger, a pass loop and tests. (`03`, `skeleton/`)
2. **Real data** with freshness checks and a bar cache. (`02`, `08`)
3. **Paper broker, single order path**, idempotent ids, reconciliation, read-back. (`05`, `06`)
4. **Supervision and backups**: a loop that survives restarts, a restore drill. (`07`)
5. **More sleeves via an onboarding pipeline**: research → shadow → paper, with caps and budgets. (`04`, `08`)
6. **Failover and monitoring** once the primary is stable. (`07`)
7. **Multi-agent operation** with coordination rules. (`09`)
8. **Long forward test**. Judge strategies on out-of-sample forward results, not on the backtest that produced them. (`08`)

## 0.7 What "good" looks like

A desk is in good shape when, at any moment, an agent can answer with receipts:

* Is it running? When did it last make *progress* (not just exist)?
* What did it decide today and why (including the decisions *not* to trade, and which gate said no)?
* Does the book equal the broker? If not, by how much and which in-flight order explains it?
* Which sleeves are blocked and *why* (full lane by design? missing data? error?)?
* What is the last good backup and has a restore been rehearsed?
* What changed since yesterday and is there a test that fails on the old behaviour?
