# Midna's Memory System and Recursive Self-Improvement Plan

Designed 2026-10-29, on the owner's commission, in his words: "figure out a way to regularly save our conversational context so you don't lose it. Design a memory system for yourself, a recursive self improvement plan."

Status: design spec. Nothing in this document is live until the implementation steps in Section 9 are executed and verified. Where this document describes an existing mechanism, it says so and names the file or job. Where it proposes a new one, it says NEW and gives the exact path, template, and owner.

Style note: no em dashes, per the owner's standing style rule. Times are America/New_York unless marked UTC.

---

## 0. SCOPE (InfinityBlade)

**Surface (what this design changes):** the trading operation's working memory: how conversational context is captured, how Midna's own book remembers its decisions, how lessons are distilled, and how process changes are proposed, tested, and kept or reverted. Concretely: new files under `~/workspace/midna-book/memory/` and `~/workspace/midna-book/experiments/`, additions to the existing `midna-daily-full-audit` cron body, a weekly review job, a monthly constitution review job, and templates and checklists that any fresh session can execute without interpretation.

**Constraints (what stays untouched):**
- The platform memory system (`~/MEMORY.md`, `~/memory/` daily logs, `~/memory/people/`, `~/memory/groups/`, the alignment synthesis under `~/dreams/alignment/`) is owned by the runtime's background upkeep. This design reads it, cites it, and feeds it through the sanctioned channel (daily-log appends). It never edits `~/MEMORY.md` directly, never creates a parallel copy of it, and never builds a second store of facts about the owner. One source of truth per fact class, always.
- The desk (muse-desk-v3) is out of scope for change. Its strategy, sizing, stops, thresholds, Tensor engine, and the pinned saty_sol file change only by the owner's ruling. This memory system records desk state; it does not steer the desk.
- The book's risk constitution (CHARTER.md) is changeable only through the monthly constitution review in Section 7, with the owner's visibility, and never mid-drawdown.
- The PII gate and all public-save rules apply unchanged. Nothing in this system is public-facing; everything here is internal. If any memory artifact is ever proposed for a public surface, it goes through the mechanical PII scan first, like everything else.
- Chat law is unchanged: desk and book reporting goes to the desk chat, never the main chat.

**Outcome (observable success):** a fresh session, given only this document and the file layout it defines, can reconstruct the full working state of the trading operation in under fifteen minutes and prove it did so by completing the recovery checklist in Section 4.4 with every box checked against a named source. Separately: every trade, pass, and process change on Midna's book is traceable from decision to outcome to lesson without gaps, and every process change in force can be named with its pre-registration, its grading window, and its verdict.

**Proof (what evidence demonstrates it):** the recovery drill in Section 4.5, run monthly, in which a session that has read nothing but the snapshot stack answers a fixed set of state questions and the answers are diffed against the systems of record. A drill that passes is proof. A drill that fails names the exact layer that drifted, and that drift is an open defect until cured.

**Edges (boundaries and dependencies):** this system depends on the platform's hourly memory upkeep and nightly dreaming continuing to run (they are runtime-managed and outside Midna's control); on the daily audit job firing (cron `midna-daily-full-audit`, daily about 21:46 ET, goal-owned by the book's goal); on market data availability for fill pricing (Alpaca SIP 5-minute bars, per the charter); and on the owner's rulings arriving through chat, which is why rulings get their own capture protocol in Section 3.3 rather than relying on any single session remembering them.

---

## 1. What already exists (the survey)

A memory system designed in ignorance of the existing one would duplicate it, and duplication is how records diverge. So first, the inventory, with sources. Everything in this section was read directly on 2026-10-29.

### 1.1 The platform memory stack (runtime-owned, read-only for this design)

Per `~/docs/memory.md` and `~/docs/self_improvement.md`:

- **`~/MEMORY.md`** (311 lines at survey time): the curated long-term memory. Facts, laws, preferences, and dated program records about the owner and the operation. Maintained by hourly background memory upkeep: new conversation is consolidated into it, newer claims supersede older ones, and it is the file a fresh session reads first. The daily audit job's own body already states the boundary: "Do not edit ~/MEMORY.md from this job."
- **`~/memory/YYYY-MM-DD.md`** daily logs (continuous from 2026-09-24 through 2026-10-29 at survey time): the append-only evidence trail. Entries are structured extractions carrying a claim id, a quote, and source message ids, for example the 2026-10-29 log's verified extractions on the forecast engines and on the master-trader study correction. This is the layer that lets any claim in MEMORY.md be traced back to who said it and when, via `muse.memory_explain`.
- **`~/memory/people/` and `~/memory/groups/`**: one page per person and group, maintained hourly by the relationships pass, ordered by closeness in each directory's INDEX.md.
- **The alignment synthesis** (`~/dreams/alignment/derived/ALIGNMENT_SYNTHESIS.md`, plus ALIGNMENT_STATE.yaml and PROGRESSION_HISTORY.yaml): the nightly dreaming pass's product. It synthesizes who the owner is, how to act for him, current frictions, and where the dated conflicts sit unresolved. It is the single best "how to work with this person" document in the system, and notably it already models the dated-conflict practice this design generalizes in Section 8: two tellings of the reconcile-halt state are both carried, named, and explicitly not silently resolved.
- **Quiet-moment passes**: after a substantial conversation goes quiet, a bounded sweep internalizes what just happened, a few times a day at most.
- **Skill review (daily)**: recurring workflows can become saved skills under `~/workspace/custom-skills/`; changes that measurably do not help are retired. This is already a form of recursive self-improvement at the platform level, and Section 7 is designed to feed it rather than compete with it.

What this stack does well: facts about the owner, his rulings and laws, relationships, and the narrative trail. What it does not do, by design: it is memory about the user and the relationship, consolidated hourly from conversation. It is not a working-state store for a trading operation. It does not hold, and should not hold, the state of every in-flight program at operational granularity, the book's per-trade reasoning, per-strategy live-versus-design records, or pre-registered process experiments. Those are the gaps this design fills, in the book's own workspace, without touching the platform stack.

### 1.2 The goals system

Per `~/docs/goals.md`: goals are durable milestones with progress entries, subgoals one level deep, background briefings, and goal-owned cron jobs whose output stays in the goal's workspace (`~/workspace/goals/<goal-slug>/files/` for documents the owner asked for, `hidden_files/` for bookkeeping). The book's goal already exists: "Midna trading her own simulated book" (goal_1b3513cd0b3d), and the daily audit job is owned by it. This design attaches its weekly and monthly jobs to the same goal, so the whole memory apparatus shares one lifecycle owner and dies with the goal if the owner ever closes it, rather than scattering orphan jobs.

### 1.3 The book's own files (created 2026-10-29)

Under `~/workspace/midna-book/`:

- **CHARTER.md**: the constitution. $100,000 virtual from 2026-10-30, US equities and ETFs long and short, options only as defined-risk structures after the formation research lands and the charter is amended in writing. Fill realism: every decision journaled with a timestamp before its fill price exists; fill is the open of the next 5-minute SIP bar at or after the decision timestamp, adjusted 5 bp against the trade; an unfetchable bar means the trade does not count and is journaled as unfilled. Risk: invalidation defined before entry, size computed from invalidation; 0.5% standard, 0.75% A+, 0.25% probe; 25% max in one name; 100% max gross; 3% heat cap; 2% daily loss stop; drawdown ladder halving risk at minus 5% and stopping entries at minus 10% pending a written review. Decision cadence at the standing slots (08:00 pre-open, 12:30 midday, 15:00 pre-close, 16:30 close review). Every decision journaled, including passes.
- **ledger.json**: the machine record. Cash, positions, fills, equity history, and the rules block mirroring the charter numbers. At survey time: inception state only, no fills yet.
- **JOURNAL.md**: the decision journal. At survey time it holds exactly one entry, the pre-inception note of 2026-10-29. Its header already states the contract: every decision in order, reasoning included, fills appended to the same entry once priced.
- **IDEAS.md**: the brainstorm log fed by the daily audit.
- **CONTEXT-SNAPSHOT.md**: the fast-recovery layer. Its header states its purpose plainly: a fresh session reads this file and recovers the working state without digging through the whole archive; the canonical long-term record stays in MEMORY.md and the daily logs. The initial snapshot (2026-10-29 21:50 ET) is a good specimen: it names the commission, the book's terms, what is in flight (six named programs), the desk headline with its verification timestamp, the Test repo state, and the open rulings waiting on the owner, each in one or two lines.

CONTEXT-SNAPSHOT.md is the seed of this whole design. It exists, it has the right shape, and its weakness is that it is one flat file maintained by one job with no template enforcement, no staleness marker, no verification step, and no drill that proves a fresh session can actually recover from it. Sections 3 and 4 harden it.

### 1.4 The daily audit job (the engine this design extends)

Cron `midna-daily-full-audit`, daily at 21:46 ET (flexible, so read "about 21:46"), goal-owned, timeout 3600s, delivering to the desk chat. Its current body, read in full on 2026-10-29, already mandates: desk health read (read-only for strategy), terminal freshness and the accrual gap named, save-seal state with an unsealed save reported as an open defect by name, the book's equity and journal completeness, the CONTEXT-SNAPSHOT rewrite, a daily-log append, and at least one genuinely considered idea (or a reasoned note that none survived scrutiny) in IDEAS.md. Improvements inside the rails are applied; anything touching desk strategy, the risk constitution, or needing the owner's ruling is reported as a decision item, never applied silently. InfinityBlade rules are stated in the body: proof before green, open defects named, no unverified state reported as good.

Section 9 gives the exact additions to this body. The design principle: the audit is the heartbeat. Every capture, check, and review in this document hangs off a job that already exists and already fires, or off the two new jobs (weekly, monthly) defined in Section 7.4. Nothing in this system depends on a live session remembering to do it.

### 1.5 What the survey found missing

1. No template or schema enforcement for the snapshot or the journal. Both are prose conventions. Prose conventions drift.
2. No lessons layer. The charter mandates Friday grading with an error taxonomy tally, but no file exists where a distilled lesson lives, gets tested, and graduates into a rule or dies.
3. No strategy memory. The book tags each trade with its setup and source strategy (charter, Decision cadence), but no per-strategy record compares live behavior against design claims over time.
4. No pre-registration machinery for process change. The charter says "one pre-registered process experiment at a time (per the memory system design)", deferring the mechanism to this document. Until now, the mechanism did not exist.
5. No recovery verification. The snapshot's purpose is recovery, but nothing tests recovery. Under InfinityBlade, an untested recovery path is an unverified claim, not a capability.
6. No staleness or conflict protocol for the operational layer. The platform layer has supersession and the dated-conflict practice; the book's layer has neither written down.

---

## 2. Design principles

Five principles govern everything below. Each is traceable to a standing law or a learned failure in the existing record, not invented for this document.

**P1. One source of truth per fact class.** Facts about the owner and his rulings: MEMORY.md and the daily logs. The book's money: ledger.json. The book's reasoning: JOURNAL.md. Working state: the snapshot stack. Lessons: the lessons ledger. Strategy truth: the strategy records. When two layers could hold the same fact, one is designated the record and the other carries a pointer or a dated quote, never a silent copy. Copies drift; pointers do not.

**P2. Append-only at the bottom, curated at the top.** Raw capture (daily logs, journal entries, fill records) is never rewritten. Curation (MEMORY.md consolidation, snapshot rewrites, lesson graduation) happens in layers above the raw record and can always be audited against it. This is the platform stack's existing shape, generalized to the book.

**P3. Claims carry sources and dates.** Every load-bearing statement in a curated layer names where it came from and when it was verified. The daily log's claim/quote/source format is the model. A fact without a date is a rumor the system tells itself.

**P4. Learn before judging.** the owner's correction on the master-trader study (2026-10-28, claim e3c4994a7ac9e7daf6f7c4d3792063d6 in the daily log: "I didn't say grade them") is standing law for how this system treats strategies, teachers, and its own past decisions: absorb and record how something works and what it claims, in its own terms, before any verdict. Verdicts come only from the live record, accumulated over a stated window, against criteria written before the window opened. This principle is why the strategy memory in Section 6 has a claims section that is filled in first and a verdict section that stays empty until the evidence threshold is met, and why the lessons ledger distinguishes a rule candidate from a rule.

**P5. Proof before green, including for memory itself.** A snapshot is not "saved" because a job wrote it; it is saved when the recovery drill passes. A lesson is not learned because it is written down; it is learned when its blocker test or behavioral check exists and passes. A process change is not an improvement because it was adopted; it is an improvement when its pre-registered grading window closes with the stated criteria met. Memory that cannot be verified is treated the way the desk treats an unsealed backup: an open defect, named.

---

## 3. Layer 1: Context preservation

### 3.1 What conversational context actually matters

Not everything. A transcript is not context; the platform already keeps transcripts and the daily logs already extract claims from them. What a fresh session needs, and what is genuinely lost when a session ends without capture, falls into six classes:

1. **Decisions.** What was decided, by whom, when, and on what reasoning. Includes trade decisions (owned by the journal, Section 5), program decisions (build this, park that, kill this other thing), and process decisions. The test for whether a decision needs capture: would a fresh session, not knowing it, plausibly redo, undo, or contradict it? If yes, capture it.
2. **Rulings.** the owner's decisions that bind future behavior: laws, exceptions, approvals, refusals. Rulings are the highest-value, lowest-volume class and the most dangerous to lose, because a lost ruling does not produce an error, it produces confident wrong action (the PII gate exceptions are the standing example: each is one-file, codename-only, and granted on a specific date; a session that half-remembers them will either block a legal save or, worse, generalize an exception the owner never granted). Rulings are captured verbatim where possible, with date and scope.
3. **Open threads.** Work in flight, work blocked, work waiting on the owner, work waiting on data accrual, work waiting on a date. Each thread needs: name, state, owner, what unblocks it, and the date it was last verified. The initial CONTEXT-SNAPSHOT already models this ("In flight at snapshot time", "Open rulings for the owner").
4. **State of every program.** For each standing program (the desk, the terminal lineup, the forecast engines, the book, the save machinery, each research program): a headline state, the metric or artifact that proves it, and the timestamp of that proof. Not a narrative. A headline plus a proof pointer.
5. **The owner's corrections.** Corrections are the highest-signal learning data in the system (the grade-first correction, the interpret-do-not-transcribe correction, the kill-happy correction all reshaped standing behavior). Each correction is captured with what behavior it replaced. The platform's supersession mechanism handles these at the fact level; the operational layer additionally keeps them visible in the snapshot's standing-orders section so a fresh session reads them before it acts, not after it errs.
6. **Negative context.** What was tried and failed, what is parked and why, what must not be re-attempted without new evidence. Absence of negative context is why agents re-propose dead ideas and re-run dead ends. The parked Tensor product, the retired external dead-man, the dropped voice notes: each is one line that saves a future session from re-litigating it.

What does not need capture in this layer: routine execution detail (it lives in run logs and the daily logs), anything already in MEMORY.md (pointer, not copy), and patient or personal logistics detail beyond what the platform memory already holds under its own rules.

### 3.2 The snapshot stack (file layout)

NEW directory: `~/workspace/midna-book/memory/`, holding the operational memory layer. The book's directory is the home because this layer serves the trading operation the owner commissioned in the same breath as the book, and the daily audit that maintains it is already the book goal's job. Layout:

```
~/workspace/midna-book/
  CHARTER.md                  (exists; constitution; amended only per Section 7)
  ledger.json                 (exists; machine record of money)
  JOURNAL.md                  (exists; decision journal, schema in Section 5)
  IDEAS.md                    (exists; brainstorm log)
  CONTEXT-SNAPSHOT.md         (exists; becomes Tier 1 of the stack, template-bound)
  memory/
    STATE.md                  NEW: Tier 2, program-by-program state ledger
    RULINGS.md                NEW: Tier 2, rulings register (operational view)
    OPEN-THREADS.md           NEW: Tier 2, open thread register
    LESSONS.md                NEW: lessons ledger (Section 5.3)
    STRATEGIES.md             NEW: strategy memory index (Section 6)
    strategies/
      <strategy_id>.md        NEW: one record per strategy (Section 6.2)
    snapshots/
      CONTEXT-YYYY-MM-DD.md   NEW: dated Tier 1 archives, one per audit run
  experiments/
    INDEX.md                  NEW: experiment register (Section 7.2)
    EXP-YYYY-NN-<slug>.md     NEW: one pre-registration per experiment
  reviews/
    WEEKLY-YYYY-Www.md        NEW: weekly review output (Section 7.4)
    MONTHLY-YYYY-MM.md        NEW: monthly constitution review output
```

Tier definitions:

- **Tier 0 (platform, untouched):** MEMORY.md, daily logs, people and groups pages, alignment synthesis. Canonical for facts about the owner, his laws, and the relationship.
- **Tier 1 (the snapshot):** CONTEXT-SNAPSHOT.md. The fast-recovery layer. Small enough to read whole in one pass (target: under 200 lines), current as of the last audit run, and stamped with the exact time and the commit or state it was verified against. Every line in Tier 1 is either a pointer to Tier 0 or Tier 2, or a headline with a proof pointer.
- **Tier 2 (the registers):** STATE.md, RULINGS.md, OPEN-THREADS.md. The operational detail Tier 1 summarizes. Each register has a fixed schema (Sections 3.4 to 3.6) so entries can be checked mechanically for completeness: a thread with no unblock condition or no last-verified date is a malformed entry and the audit flags it.
- **Tier 3 (the evidence):** the journal, the ledger, the daily logs, program artifacts, run records. Append-only. Tier 1 and Tier 2 claims must resolve to Tier 3 evidence on demand; the recovery drill tests exactly this resolution.

Dated Tier 1 archives (`memory/snapshots/`): each audit run, before rewriting CONTEXT-SNAPSHOT.md, copies the outgoing version to the dated archive. This gives the snapshot a history, which is what makes summary drift (Section 8.3) detectable: any claim can be diffed across archives to see when its wording changed and whether the underlying evidence changed with it. Retention: keep all; they are small. The archive is also the rollback for a bad snapshot rewrite.

### 3.3 Capture protocol: who writes what, when

Capture happens at four moments. The design rule is that no capture depends on a session's good intentions at the moment it happens to end; three of the four moments are job-driven.

**Moment 1: In-session, at the event (the deciding session writes).**
- A ruling from the owner is appended to RULINGS.md in the same session that receives it, in the format of Section 3.5, before the session moves on to other work. Rationale: rulings are rare, short, and catastrophic to lose; the hourly platform upkeep will consolidate them into MEMORY.md on its own schedule, but the operational register does not wait for that.
- A trade decision is journaled before its fill exists. This is already charter law; Section 5 adds the schema.
- A program state change (a program starts, lands, is parked, is killed) updates STATE.md's row for that program in the same session, with the proof pointer.
- A new open thread is added to OPEN-THREADS.md when it becomes concrete, not when someone remembers it later. A thread that closes is marked closed with its closing evidence in the same session, and stays in the register (struck through, dated) until the monthly review prunes closed threads older than 60 days into the dated snapshot archive's month.

**Moment 2: Quiet-moment and hourly upkeep (platform, already running).** Unchanged. The platform consolidation into MEMORY.md and the daily logs proceeds as it does today. This design adds one feed into it: the daily audit's daily-log append (Moment 3) is written in the daily log's established format so the platform extraction can pick it up.

**Moment 3: The daily audit (about 21:46 ET, job `midna-daily-full-audit`).** The audit is the reconciliation pass. It does not originate most content; it verifies, completes, and curates:
- Archives the outgoing snapshot, then rewrites CONTEXT-SNAPSHOT.md from the registers and the systems of record, using the template in Section 4.2. Any register entry it cannot verify against a system of record is carried into the new snapshot marked UNVERIFIED with the reason, never silently dropped and never silently promoted.
- Sweeps the day's sessions' durable output for rulings, decisions, and threads that Moment 1 missed, and backfills the registers, marking backfilled entries with their true source date. (A backfill is labeled a backfill. Rewriting history to look contemporaneous is summary drift in its worst form.)
- Appends the day's durable observations to `~/memory/YYYY-MM-DD.md`, as its body already mandates.
- Runs the memory health checks of Section 8.5 and reports failures as open defects by name.

**Moment 4: The weekly and monthly reviews (Section 7.4).** These curate upward: lessons graduate or die, strategy verdicts are updated, registers are pruned, and the snapshot's standing-orders section is re-read against MEMORY.md for divergence. Divergence between the operational layer and the platform layer is resolved in favor of the platform layer for facts about the owner, and in favor of the systems of record for operational state, and the resolution is logged.

### 3.4 STATE.md schema

One row-block per program. Fixed fields:

```
## <program name> (<stable id>)
- State: LIVE | BUILDING | PARKED | BLOCKED | DONE | BROKEN
- Headline: one sentence, present tense, factual.
- Proof: <artifact path, metric, or read-back> as of <YYYY-MM-DD HH:MM ET>.
- Owner: Midna | the owner | <named peer> | external
- Next event: what happens next and what triggers it.
- Open defects: names, or "none verified".
- Last verified: <date> by <session or job>.
```

Rules: a program with no row is a program the system has forgotten, so the audit's weekly pass diffs the STATE.md program list against the goal list and the cron list and flags any program present in one and absent in another. "Last verified" older than 7 days on a LIVE program is flagged as stale at the weekly review (Section 8.1).

### 3.5 RULINGS.md schema

One entry per ruling, newest first, never edited after the day it is written except to append a supersession note:

```
## YYYY-MM-DD: <short title>
- Ruling: <what the owner decided, verbatim quote where the wording itself binds>.
- Scope: <exactly what it covers and, where stated, what it does not>.
- Source: <chat, message context, or MEMORY.md citation>.
- Operational consequence: <what Midna does differently because of it>.
- Supersedes: <prior ruling title and date, or none>.
- Status: IN FORCE | SUPERSEDED by <entry> | EXPIRED <date>.
```

RULINGS.md is an operational view, not a second source of truth: MEMORY.md remains canonical for rulings as facts. RULINGS.md exists because a fresh session needs the operational consequences in one scannable place, and because the monthly review diffs RULINGS.md against MEMORY.md's laws to catch any ruling the operational layer missed or misstated. A conflict between the two is a dated conflict (Section 8.2): both readings carried, the owner asked, neither silently resolved.

Scope discipline matters more here than anywhere. The PII gate exceptions are the template: each names one file, one pattern waived, the patterns still blocked, and the date of the ruling. Every RULINGS.md entry must state scope at that granularity. An entry whose scope reads "approved" with no object is malformed.

### 3.6 OPEN-THREADS.md schema

One entry per thread:

```
## <thread name> (<stable id>)
- Opened: <date>. State: OPEN | BLOCKED | WAITING-ON-OWNER | WAITING-ON-DATA | WAITING-ON-DATE
- What it is: one or two sentences.
- Unblocks when: <the specific event, ruling, data threshold, or date>.
- Owner of next action: Midna | the owner | <named>.
- Last verified: <date>, evidence <pointer>.
- If abandoned: <what closing it would require, or "owner ruling only">.
```

WAITING-ON-OWNER threads are additionally mirrored into the snapshot's "Open rulings for the owner" section (Tier 1), because that is the list the owner actually sees. The mirror is a pointer list only: title and one-line ask. The detail stays in the register.

---

## 4. The snapshot protocol

### 4.1 What is written

CONTEXT-SNAPSHOT.md is rewritten in full at each audit run (with the outgoing version archived first). A full rewrite from sources, rather than an incremental edit, is deliberate: incremental edits accumulate drift and orphaned lines; a rewrite forces every line to re-justify itself against the registers and the systems of record each night. The cost is one job run; the benefit is that the snapshot's age is bounded by one day and its content is always traceable to that night's verification.

### 4.2 Snapshot template (normative)

```
# Context Snapshot

Snapshot: <YYYY-MM-DD HH:MM ET> by <job or session id>.
Verified against: <ledger.json state, desk state pointer, save seal verdict,
goal states, register states, each with its own timestamp>.
Previous snapshot: memory/snapshots/CONTEXT-<YYYY-MM-DD>.md.
Health: <GREEN only if Section 8.5 checks all passed tonight; otherwise
PARTIAL or UNVERIFIED with the failed checks named>.

## Who and what (stable, changes rarely)
- the owner, the book's commission one-liner, the charter version in force,
  the standing style and chat-law constraints a fresh session needs before acting.
- Pointers: MEMORY.md for facts and laws; alignment synthesis for posture.

## The book right now
- Equity, cash, open positions with invalidations, heat, drawdown state
  vs the ladder, % vs SPY and QQQ (window named), journal completeness verdict.

## Programs (one line each, from STATE.md)
- <program>: <state>, <headline>, proof as of <time>.
(Every program in STATE.md appears. None are omitted because quiet.)

## Open threads needing the owner
- <title>: <one-line ask>. (From OPEN-THREADS.md, WAITING-ON-OWNER only.)

## Open defects (named, never summarized away)
- <defect>: <state, evidence, what unblocks the cure>.

## Dated conflicts in force
- <conflict>: <reading A per source/date> vs <reading B per source/date>;
  carried unresolved since <date>; resolution needs <what>.

## Standing orders a fresh session must not violate
- The short list: hard rails, chat law pointer, no-em-dash, PII gate,
  Tensor fence, saty_sol pin, parked items not to resurrect.
  Each item one line with its ruling date.

## What happens next (scheduled)
- Next audit, next weekly review, next monthly review, next trading slots,
  any dated waits (data accrual thresholds, grading windows closing).

## Recovery
- "You are recovered when you can answer the Section 4.4 checklist.
  Start: this file, then STATE.md, then the book's JOURNAL.md tail,
  then MEMORY.md sections named here."
```

### 4.3 Freshness and stamping rules

- The snapshot header carries the exact write time and the verification basis. A snapshot older than 36 hours is stale by definition: the audit fires daily, so a gap means the audit failed, which is itself an open defect the next run (or any session that notices) must name.
- Every program line carries its proof timestamp, not the snapshot's timestamp. A snapshot written tonight may honestly carry a program proof from three days ago, and must show that age rather than launder it into tonight's freshness. This is the single most important anti-drift rule in the design: **the snapshot's date is the date of assembly, never the date of the facts.**
- Numbers come from the system of record at assembly time (ledger.json for the book, the desk's own records for the desk, the seal verifier for saves), never from the previous snapshot. Copying last night's number into tonight's snapshot is falsification by inertia and is the failure the weekly review samples for (Section 8.5, check M4).

### 4.4 Recovery protocol and checklist

A fresh session (new chat, post-restart, post-compaction, a delegated worker adopting the operation) recovers in this order, reading whole files, not searching fragments:

1. CONTEXT-SNAPSHOT.md (Tier 1). Note its Health line and its age before trusting anything in it.
2. `memory/STATE.md`, `memory/RULINGS.md` (in-force entries), `memory/OPEN-THREADS.md`.
3. The book's JOURNAL.md, last 20 entries or last 7 days, whichever is longer; ledger.json in full.
4. MEMORY.md, at minimum the laws and the entries the snapshot points to; the alignment synthesis for posture when the session will interact with the owner directly.
5. Any experiment in force (Section 7): its pre-registration, so the session does not unknowingly violate or double-run it.

The session is recovered when it can answer, in writing in its first work product or report, each of these against a named source:

- [ ] Book equity, cash, open positions, and each position's invalidation and heat contribution. Source: ledger.json plus journal entries.
- [ ] Performance vs SPY and QQQ for the current week and since inception, windows named.
- [ ] Drawdown state: current drawdown from peak and which ladder rung, if any, is active.
- [ ] Every open thread waiting on the owner, stated as the exact ask.
- [ ] Every open defect, by name, with its unblocking condition.
- [ ] Every dated conflict in force, both readings.
- [ ] The experiment currently in force, its window, and its kill criteria; or "none in force".
- [ ] The standing orders list, from memory of the read, with ruling dates.
- [ ] The next three scheduled events that affect the operation, with times.
- [ ] Anything in the snapshot marked UNVERIFIED, restated as unverified, not smoothed over.

Any box the session cannot check is not a failure of the session; it is a finding against the memory system, logged as a defect with the missing layer named. Recovery gaps are system bugs, not reader errors. That stance is what makes the drill in Section 4.5 honest: the checker is incentivized to find gaps, not to bluff past them.

### 4.5 The recovery drill (monthly proof)

Once a month, as part of the monthly review, a fresh session (or a delegated worker with no exposure to the month's work) is given only the snapshot stack and the checklist, answers it, and a second pass diffs every answer against the systems of record. The drill result is recorded in the monthly review file with one of three verdicts: RECOVERED (all answers correct and sourced), PARTIAL (gaps named, each becoming an open defect with an owner and a cure), FAILED (the stack cannot support recovery; the memory system itself is the top open defect until cured). Under InfinityBlade, the snapshot protocol is GREEN only in months where the drill reads RECOVERED. This is the "no green without evidence from the final system state" rule applied to memory itself.

---

## 5. Layer 2: Trading memory

Trading memory is the book's memory of itself as a trader. It has three components: the decision journal (what was decided and why), the lessons ledger (what the outcomes teach), and strategy memory (Section 6, what each approach is actually doing versus what it claims). The charter already mandates the journal and the grading; this section gives them schemas and the connective tissue between them.

### 5.1 The decision journal as long-term memory

The journal is the book's episodic memory. Its charter contract (reasoning recorded before the fill, fills appended to the same entry) already makes it the one record that can later distinguish a good decision with a bad outcome from a bad decision with a lucky one, which is the distinction all grading depends on. The schema below makes that contract machine-checkable, so the audit's "journal completeness" check (already in its body) can be exact rather than impressionistic.

### 5.2 Journal entry schema (normative)

Every entry, whether trade or pass, carries these fields. Markdown with a fixed field order; the audit parses fields, not prose.

```
## <YYYY-MM-DD HH:MM ET> · <ENTRY|EXIT|ADJUST|PASS|REVIEW> · <id: J-YYYYMMDD-NN>
- Slot: pre-open | midday | pre-close | close-review | unscheduled (<reason>)
- Instrument: <symbol, or "book" for book-level entries>
- Setup: <playbook setup name, or "none" with why a non-playbook action was taken>
- Sources consulted: <terminal tools, engines, sleeves drawn from, with ids>
- Thesis: <the case, in the setup's own terms, two to five sentences>
- Invalidation: <price or condition; for PASS entries, what would have changed the pass>
- Levels: entry zone, targets by role, expected path (for trades)
- Size math: equity at decision, risk fraction and class (standard/A+/probe),
  dollar risk, share count derivation from invalidation distance
- Heat after: <book heat if this entry fills, vs the 3% cap>
- Regime note: <the day's regime call and whether this trade agrees with it>
- Decision: <the action, stated as an order or an explicit pass with reason>
- Fill (appended when priced): bar timestamp, bar open, slippage applied,
  fill price; or UNFILLED with the reason (no bar, halt, superseded)
- Outcome (appended at close of the position or at the Friday grading):
  exit fill, realized R, R available on the setup's own rules, rule adherence
  (full | partial with the deviation named | broken with the deviation named)
- Lesson link: <LESSON-id, or "none", or "pending Friday grading">
```

Rules that make the journal memory rather than a diary:

- **Timestamp discipline.** The entry timestamp is the decision timestamp the charter's fill rule keys on. An entry written after its fill bar is a charter violation and is labeled as such in the entry itself, not hidden. Backfilled reasoning is worthless as evidence and dangerous as self-deception; the label is what keeps the record usable.
- **Passes are first-class.** A pass entry requires the same thesis and invalidation fields, where invalidation reads "what would have made this a trade". The Friday grading counts passes alongside trades, because a book that only remembers its trades cannot learn whether its selectivity is its edge or its leak. The charter already says a pass with a reason is a decision; the schema makes the reason structured.
- **No silent edits.** Corrections to an entry are appended as dated amendments under the entry, never inline rewrites. The original reasoning stands, wrong or right, because grading it is the point.
- **IDs are forever.** J-ids are cited by the lessons ledger, the strategy records, and experiment reports. An id is never reused.

### 5.3 The lessons ledger (memory/LESSONS.md)

The lessons ledger is the book's semantic memory: distilled, general, and few. Its discipline is that most candidate lessons should die. A journal full of trades produces dozens of plausible-sounding lessons, most of them noise wearing a narrative; the ledger's graduation process exists to keep noise out of the rule set.

Entry lifecycle: **CANDIDATE, then TESTED, then RULE or DEAD.** One entry per lesson:

```
## <LESSON-id: L-NN> · <one-line statement, imperative or falsifiable>
- Status: CANDIDATE | TESTED | RULE | DEAD
- Origin: <journal ids and dates; the specific losses or errors that prompted it>
- Claim: <what behavior the lesson prescribes or forbids, stated so it can be obeyed or violated observably>
- Evidence so far: <dated observations, for and against, each with journal or ledger pointers>
- Counter-case: <the strongest reason this lesson might be wrong, written at creation, not after>
- Graduation test: <what would promote it: a stated count of confirming instances,
  a stated absence of counter-instances over a stated window, or a blocker check>
- If RULE: effective <date>; enforced by <journal field, audit check, or experiment>;
  supersedes <prior lesson id, or none>
- If DEAD: killed <date>; reason <evidence>; retained so it is not re-proposed
  without new evidence materially different from <pointer>
```

Operating rules:

- **Creation bar.** A lesson is created from a loss, an error, or a repeated pattern, at the Friday grading at the earliest. Never in the heat of the day it happened, and never from a single win. A single loss creates a candidate only when the loss traces to a decision fault (a rule bent, a field skipped, a known trap walked into), not merely to a setup that lost: setups lose at their base rate, and a ledger that converts base-rate losses into rules will strangle every setup it touches. Where the distinction is unclear, the candidate's counter-case field must say so.
- **Error taxonomy.** Each candidate is tagged with the charter's Friday taxonomy, extended as needed and kept stable once used: invalidation fault, sizing fault, timing fault, regime fault (traded against the day's own call), source fault (acted on a stale or unverified input), selectivity fault (took a trade the playbook's own funnel rejects, or passed one it mandates reviewing), execution fault (fill handling, missed slot), constitution fault (a charter rule broken). The taxonomy tally at Friday grading is the input to experiment selection in Section 7: the most frequent fault class is the first place the improvement loop looks.
- **Testing.** A candidate is TESTED while its graduation window runs. During the window, every relevant journal entry notes obey/violate/not-applicable for the candidate in its lesson-link field. The daily audit tallies; it does not judge early.
- **Graduation.** At a weekly review, a candidate meeting its stated test becomes a RULE, written into the journal schema's checks or the audit's checklist as applicable, with its enforcement named. A rule without an enforcement mechanism is a wish, and the entry must say which mechanism enforces it or stay a candidate.
- **Death and retention.** A candidate that fails its test, or whose counter-case proves stronger, becomes DEAD and stays in the ledger. Dead lessons are negative context (Section 3.1, class 6): they prevent the system from relearning the same false lesson every quarter, which is a real failure mode of any memory that only keeps what it currently believes.
- **Conflict with the charter.** A lesson can never override the charter. If a graduated lesson implies a charter change, it becomes an input to the monthly constitution review (Section 7.5), nothing more.

### 5.4 Friday grading as the memory consolidation point

The charter's Friday grading (% vs SPY/QQQ for the week, R captured vs R available, rule adherence count, error taxonomy tally) is the trading layer's consolidation pass, the analog of the platform's hourly upkeep. This design fixes its outputs: the grading is written as a REVIEW journal entry; its taxonomy tally updates LESSONS.md candidates; its per-strategy numbers update Section 6 records; and its one-paragraph narrative summary is the week's input to the snapshot's book section at the next audit. Grading that produces no ledger writes is grading that did not happen, for memory purposes.

---

## 6. Layer 3: Strategy memory

### 6.1 Purpose

The book draws on setups and strategies with design claims: the master-trader playbook's five stock setups and four options expressions, the desk's sleeves it consults as sources, terminal tools and forecast engines with their own published claims and kill rules. Design claims are hypotheses. Strategy memory is where each one's live record accumulates next to its claims until the record can speak. Per principle P4, the claims are recorded first, faithfully, in the source's own terms, and the verdict section stays empty until the evidence threshold written in the record is met. The forecast engines program already works this way (ledger before display, fixed horizons, kill thresholds stated in advance, engines printing NOT MET on their own faces when their history verdict fails); strategy memory generalizes that machinery to the book's playbook.

### 6.2 Per-strategy record (memory/strategies/&lt;strategy_id&gt;.md)

```
# <Strategy name> (<strategy_id>)
## Design claims (recorded <date>, from <source pointer>)
- What it is: the algorithm or setup in its own terms, completely enough
  that a fresh session could run it without the source open.
- Claimed edge and mechanism: why it is supposed to work.
- Claimed conditions: regime, universe, timeframe it claims to need.
- Source's own numbers: any backtest or record the source publishes,
  labeled as the source's, with the source's own caveats.
## Book's adaptation
- What the book actually runs: parameters, funnel position, risk class.
- Differences from the source design, each with its reason and date.
  (A silent difference makes the live record uninterpretable.)
## Live record (updated at Friday gradings)
- Trades: n, journal ids. Wins/losses. R captured vs R available.
- Expectancy in R, with the window named. % contribution vs SPY/QQQ context.
- Rule adherence within the strategy: full/partial/broken counts.
- Conditions observed: regimes and conditions the trades actually occurred in
  vs the claimed conditions.
## Verdict (empty until threshold met)
- Evidence threshold: <stated at record creation: e.g., 30 graded trades
  or 12 weeks of live record, whichever later>
- Verdict: KEEP | MODIFY (via experiment only) | RETIRE | INSUFFICIENT RECORD
- Basis: the live-record numbers, quoted, not paraphrased.
## History
- Dated change log: adaptations, experiment effects, verdict changes.
```

### 6.3 Rules

- **One record per strategy as the book runs it.** Two variants that differ in a parameter that could affect outcomes are two records (or one record with an explicit variant split in the live record), because pooling variants manufactures a blended record that describes neither. The sleeve accounting program learned this the hard way in October 2026, when five options variants folded into their stock versions had to be split back out on a verifier's catch. Strategy memory adopts the repaired rule from the start: doubtful cases stay separate and are flagged, never merged for tidiness.
- **The desk's sleeves as sources.** When the book draws on a desk sleeve's signal, the strategy record cites the sleeve and treats the sleeve's own live state (from STATE.md) as part of its conditions. The record never grades the desk's sleeve itself; grading the desk is the inspections' job, and the book's record covers only the book's use of it.
- **Retirement is a verdict, not a mood.** A strategy is retired only at its threshold, on its numbers, at a weekly or monthly review, and the record is retained in full. Retired records are negative context for re-adoption: re-adopting a retired strategy requires new evidence named in the record, not a fresh burst of enthusiasm.
- **Index.** memory/STRATEGIES.md is the one-page index: strategy, id, state (learning, live, in experiment, retired), trades so far vs threshold, current expectancy with window. The snapshot's book section points here rather than summarizing strategies itself.

---

## 7. Recursive self-improvement

### 7.1 The loop

The improvement loop operates on Midna's process: how she scans, journals, sizes attention, grades, and reviews. It does not operate on the desk, and it operates on the book's charter only through Section 7.5. One cycle:

1. **Observe.** Inputs: the Friday error taxonomy tallies, the lessons ledger's tested candidates, the recovery drill findings, the strategy records' adherence counts, the audit's own defect list. Observation is a written artifact (the weekly review), not a feeling.
2. **Hypothesize one change.** Exactly one process change per cycle, stated as: the current behavior, the proposed behavior, the mechanism by which it should help, and the metric that will move if it does. One change at a time is what makes the result attributable; two simultaneous changes with a good outcome teach nothing and with a bad outcome cost a revert of both.
3. **Pre-register.** Before the change takes effect, an experiment file (Section 7.2) is written with hypothesis, window, metrics, grading criteria, and kill criteria, and committed to the register. A change that is already running before its registration exists is not an experiment; it is drift, and the weekly review names it as such if it finds one.
4. **Run the fixed window.** The window is stated in trading days or calendar weeks at registration and does not shorten because results look clear early, in either direction. Early clarity is how small samples lie. The one exception: a kill criterion firing ends the window immediately, by design.
5. **Grade.** At window close, the experiment is graded on two axes, both required:
   - **Decision quality:** did the journal show the targeted fault class falling, adherence rising, fields completed, passes reasoned? Decision quality is graded from journal and audit records, which exist regardless of market outcome.
   - **Results:** the book's numbers over the window vs SPY/QQQ and vs the pre-window baseline period of equal length, R captured vs available, drawdown behavior. Results are reported with their sample size attached and are never sufficient alone: a window of eight trades cannot promote a change on results, only fail to veto it.
6. **Keep, modify, or revert.** KEEP: the change becomes standing process, written into the relevant template or checklist, and the experiment closes as ADOPTED. MODIFY: a follow-up experiment is registered (a new cycle, not an extension). REVERT: the change is undone, the experiment closes as REVERTED, and the record stays. Reverts are successes of the loop, not failures of the experimenter; a loop that never reverts is a loop that is not testing anything real.

### 7.2 Experiment register and pre-registration schema

experiments/INDEX.md: one line per experiment (id, title, state: REGISTERED | RUNNING | GRADING | ADOPTED | REVERTED | KILLED, window, verdict pointer). The register enforces the one-at-a-time rule mechanically: the weekly review checks that at most one experiment is in RUNNING state; a second RUNNING experiment is a process defect.

```
# EXP-<YYYY>-<NN>: <title>
- Registered: <date, before effect>. Proposed by: <session, review, or lesson id>.
- Fault addressed: <taxonomy class and its recent tally, with pointers>.
- Current behavior: <what the process does now, with the template or job pointer>.
- Proposed behavior: <the change, exactly>.
- Mechanism: <why this should move the metric>.
- Window: <start date> to <end date or N trading days>, fixed.
- Primary metric: <the decision-quality measure> and its baseline.
- Secondary metric: <results measure> and its baseline.
- Grade criteria: ADOPT if <...>; REVERT if <...>; MODIFY if <...>.
- Kill criteria: <conditions ending the window early, e.g., constitution
  breach, journal completeness falling below <x>, drawdown ladder rung hit>.
- Charter interaction: NONE | REQUIRES constitution review (then it is not
  an experiment, it is a Section 7.5 proposal; experiments never touch risk).
- Rollback: <the exact steps that restore the prior behavior>.
- Grade (filled at close): decision quality <evidence>, results <evidence>,
  verdict, date, grader (a session other than the proposer where feasible).
```

### 7.3 Safeguards (hard rules, not guidelines)

- **The risk constitution never changes mid-drawdown.** While the book is at or beyond the minus 5% ladder rung, no charter amendment, no experiment touching sizing behavior, and no risk-class redefinition may take effect. Proposals may be drafted and registered; effect waits for recovery above the rung and the monthly review. Rationale: drawdown is precisely when the urge to change the rules is strongest and the judgment behind it is least trustworthy. The charter's own ladder (entries stop at minus 10% pending a written review) is the floor this safeguard builds on.
- **Experiments never touch risk parameters.** Risk fractions, caps, the heat limit, the daily loss stop, the ladder: charter territory, monthly review only. An experiment may change information flow, checklists, slot discipline, source consultation order, journaling practice, review depth, anything about process that is not the risk numbers.
- **Every change is versioned and reversible.** Templates, checklists, and job bodies changed by an adopted experiment carry a dated change note naming the experiment id. The rollback field of every experiment is written before the window opens, while reverting is still cheap to imagine.
- **the owner sees every constitutional change.** Section 7.5 routes charter amendments through the monthly review, whose output is a decision item in the desk chat naming the amendment, its evidence, and its effective date. Nothing constitutional takes effect silently, and nothing constitutional is buried in a longer report.
- **The loop cannot edit its own safeguards.** Sections 7.3's rules change only by the owner's ruling, recorded in RULINGS.md. A system that can relax its own constraints will, eventually, at the worst moment.
- **Desk rails are absolute.** No experiment, lesson, or review in this system authorizes any change to desk strategy, sizing, or the Tensor engine. Findings about the desk are reported as decision items for the owner, per the audit job's existing rule.

### 7.4 Cadence

- **Daily (about 21:46 ET):** the audit. Capture, reconciliation, snapshot, health checks, one idea. (Exists; Section 9 adds to it.)
- **Weekly (Friday, after the 17:45 weekly grading job's window, NEW job `midna-weekly-memory-review`, about 19:00 ET Fridays, goal-owned by the book's goal):** the improvement loop's home. Agenda, fixed: (1) Friday grading outputs consolidated; (2) lessons: candidates created, tested tallies updated, graduations and deaths decided; (3) strategy records updated from the week's journal; (4) experiment state: the running experiment's interim metrics checked against kill criteria only (no early verdicts), a closed experiment graded, a new one registered if the slot is free and a fault class justifies it; (5) register hygiene: STATE.md staleness, OPEN-THREADS pruning check, RULINGS.md versus MEMORY.md spot diff on the week's rulings; (6) the week's review file written to reviews/WEEKLY-YYYY-Www.md and its decision items surfaced in the desk chat.
- **Monthly (first weekend of the month, NEW job `midna-monthly-constitution-review`, Saturday about 11:00 ET, goal-owned):** the deep pass. Agenda: (1) the recovery drill (Section 4.5); (2) constitution review (Section 7.5); (3) full RULINGS.md versus MEMORY.md diff; (4) summary-drift sampling (Section 8.5, check M5); (5) strategy verdicts whose thresholds fell due; (6) experiment program review: adoption rate, revert rate, whether the loop is selecting faults that matter (measured by whether adopted changes' metrics held in the following month); (7) memory system self-assessment against Section 8's failure modes, written into reviews/MONTHLY-YYYY-MM.md.

### 7.5 Constitution review

The charter is versioned (v1 at inception). An amendment requires: a written proposal citing its evidence (lessons, strategy records, experiment results, or a ruling from the owner); a statement of what behavior changes and what provably does not; the owner's visibility before effect (the monthly review surfaces it as a decision item; an amendment the owner objects to does not land, and one he explicitly approves lands on his word); the drawdown safeguard of Section 7.3 checked and recorded; and the charter file edited with a dated amendment note appended, version incremented, prior version preserved in the book's git history or a CHARTER-HISTORY section. Options enablement is the expected first amendment class: the charter already conditions it on the formation research landing, which it now has, so the first monthly review should either propose the options amendment with its defined-risk structures specified or record why it is deferred. Silence on a charter-anticipated amendment is drift.

### 7.6 Feeding the platform's skill review

When an adopted experiment stabilizes into a repeatable procedure (it has survived a full month in force with its metric holding), the weekly review flags it as a skill candidate. The platform's daily skill review already converts recurring workflows into saved skills and retires ones that measurably do not help; flagging candidates in IDEAS.md with the experiment id gives that pass evidence to work from instead of impressions. This design does not create skills itself; it produces the graded record that makes the platform's decisions about skills better.

---

## 8. Failure modes of memory itself

A memory system is a system, and it fails in characteristic ways. Each mode below is named with its observed instance in this operation's own record where one exists, because the desk's history is the best evidence that these are not hypothetical.

### 8.1 Stale facts

**Mode:** a record was true when written and is false now, and nothing marks the transition. State changes faster than curation.
**Observed instance:** the terminal's accrual gaps (an IV ledger stopped on October 14 still being read as if live by anything that does not check its last date) and every "waiting on data" engine state that changes the day the data arrives.
**Counters:** every STATE.md row and snapshot line carries its proof timestamp (Section 4.3); the weekly review flags LIVE programs unverified for over 7 days; data-dependent claims must name the series' last date, not the claim's write date; the audit's terminal freshness check already names stale accrual items and this design extends the same treatment to the registers.

### 8.2 Conflicting records

**Mode:** two layers assert incompatible states. The failure is not the conflict; the failure is resolving it silently, by recency, by confidence, or by whichever record the current session happened to read.
**Observed instance, and the practice to generalize:** the reconcile-halt dated conflict. The record carries both tellings: cured at the source on 2026-10-26 with orders reaching the broker, and described on 2026-10-28 (in inspection reporting and the covering brief for a peer agent) as recurring and gating entries. The alignment synthesis holds both, dates both, and states plainly that the conflict must not be silently resolved and stands until fresh final-state proof settles it. That is the correct behavior, and this design adopts it as a general rule:
- A discovered conflict is entered in the snapshot's "Dated conflicts in force" section with both readings, their sources, and their dates.
- Neither reading is edited, demoted, or deleted by the memory system.
- Resolution requires new evidence from the system of record (not a more confident summary), and the resolution is appended as a dated note recording which reading the evidence settled and what happened to the other.
- Conflicts about the owner (rulings, preferences) resolve only by the owner's word or by MEMORY.md's supersession record, and are surfaced to him if they touch anything he is about to be advised on.
- A conflict that survives two monthly reviews is escalated as a standing decision item, not carried forever in silence.

### 8.3 Summary drift

**Mode:** each curation pass paraphrases the last, and the paraphrase slowly migrates: qualifiers fall off, numbers round toward the narrative, a PARTIAL becomes a "basically done", a claim's scope widens. The end state is a curated layer that no longer matches any evidence, while looking exactly like memory.
**Observed instances:** the fabricated completion report of 2026-10-23 (a handback claiming a cure that had not landed, which is why delegated results are now verified against the tree before being repeated) is drift's malicious cousin; the ordinary version is the nightly snapshot that copies last night's numbers (Section 4.3's rule exists because of this).
**Counters:** numbers only from systems of record at assembly time; verdicts quoted from source records rather than paraphrased (strategy records quote their basis); the dated snapshot archive makes drift measurable by diff; the monthly drift sample (check M5) re-derives five random snapshot claims from Tier 3 evidence and reports any mismatch as a defect; delegated handbacks are verified before entering any curated layer, per the standing rule the owner set after 2026-10-23.

### 8.4 False completeness

**Mode:** the index says everything is captured because the index is what got checked. A register that lists 60 programs proves the register is consistent with itself, nothing more.
**Counters:** reconciliation runs against independent enumerations, never against the register's own list: STATE.md against the goal list and cron list; the journal against ledger.json fills (every fill has an entry, every entry that claims a fill has one); the strategy index against the set of setup tags actually used in the journal. This is the save-verification discipline (enumerate the full set first, verify every item by read-back) applied to memory. The desk's catalog reconciliation of October 2026, which settled its roster diff exactly (312 present, 1 excluded by design, 20 installed after the catalog date, summing to the roster count with no remainder), is the standard: a reconciliation that does not sum exactly has not reconciled.

### 8.5 Memory health checks (run by the audit and the reviews)

Daily (audit): **M1** snapshot written and stamped, age under 36 hours projected; **M2** journal completeness: every ledger fill has a journal entry with a pre-fill timestamp, every open position has an entry with an invalidation; **M3** every RULINGS.md entry from today also appears in today's daily-log append (the feed into platform consolidation).
Weekly: **M4** number provenance sample: five numeric claims drawn from the week's snapshots, each re-derived from its system of record; **M6** register schema sweep: every STATE, RULINGS, and OPEN-THREADS entry carries all required fields; **M7** experiment register cardinality: at most one RUNNING.
Monthly: **M5** drift sample: five curated claims (snapshot, strategy verdicts, lessons) traced to Tier 3 evidence verbatim; **M8** the recovery drill (Section 4.5); **M9** dead-lesson resurrection check: no RULE or experiment in force restates a DEAD lesson's claim without citing new evidence.
Every failed check is an open defect named in the next report, with the layer at fault. Checks are listed here so their absence is also visible: a week with no M4 result recorded is a failed M4.

### 8.6 Overwriting and loss

**Mode:** a rewrite destroys the prior state, a job overwrites a file it meant to append to, a consolidation supersedes a claim whose original wording mattered.
**Counters:** append-only Tier 3; dated archives before every Tier 1 rewrite; schema rule from the desk's own scar tissue (the manifest incident of 2026-09-30, where reading the wrong key and rewriting blindly nearly destroyed an index): any script or session writing a register must read the existing file first, write against its actual structure, and verify the write by reading it back. A write that cannot be read back as intended did not happen, and is reported as failed, not assumed.

### 8.7 Memory as authority it has not earned

**Mode:** the system starts treating its own summaries as evidence ("the snapshot says the desk is fine") in place of the system of record, or a lesson graduates into behavior without its enforcement existing, or a strategy's design claims get quoted as if they were its live record.
**Counters:** the snapshot Health line and UNVERIFIED markings; principle P4's empty verdict sections; the grading rule that a worker's or a job's completion report is a claim until its evidence is checked, applied inward to this system's own jobs. The audit reporting "snapshot written" proves a file exists. The drill proves recovery works. Only the second is green.

---

## 9. Implementation: exact additions and build order

### 9.1 Additions to the `midna-daily-full-audit` job body

The existing body stands. The following blocks are appended to it verbatim (the parent agent applies them with `cron.update` using the same job id, preserving the existing body, schedule, and delivery, then verifies with `cron.view`):

**Addition A (extends scope item 5, Memory and context), add after the existing snapshot sentence:**

> MEMORY REGISTERS: maintain ~/workspace/midna-book/memory/ per MEMORY-SYSTEM.md (~/workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md). Before rewriting CONTEXT-SNAPSHOT.md, copy the outgoing version to ~/workspace/midna-book/memory/snapshots/CONTEXT-YYYY-MM-DD.md using the outgoing snapshot's own date. Rewrite the snapshot from the registers and the systems of record using the Section 4.2 template: numbers only from the systems of record at assembly time, every program line carrying its own proof timestamp, anything unverifiable carried as UNVERIFIED with the reason. Backfill any of today's rulings, decisions, or threads the registers missed, labeled as backfills with their true source dates, into memory/RULINGS.md, memory/STATE.md, and memory/OPEN-THREADS.md. Enter any conflict discovered between layers into the snapshot's Dated conflicts section with both readings and dates; never resolve a conflict silently.

**Addition B (new scope item, journal and lessons):**

> JOURNAL AND LESSONS CHECK: verify journal completeness exactly: every fill in ledger.json has a JOURNAL.md entry whose decision timestamp precedes its fill bar; every open position has an entry carrying an invalidation; every entry from the standing slots today exists, including PASS entries. Report any gap by journal id as an open defect. Append today's lesson-link tallies to memory/LESSONS.md TESTED candidates (obey, violate, not-applicable counts only; no graduation judgments, those belong to the weekly review).

**Addition C (new scope item, memory health):**

> MEMORY HEALTH: run checks M1, M2, M3 from MEMORY-SYSTEM.md Section 8.5 and set the snapshot's Health line from the results (GREEN only if all pass). A failed check is an open defect in the report, named with the layer at fault. If the outgoing snapshot is older than 36 hours, report the audit gap itself as an open defect.

**Addition D (experiments guard, added to the RULES paragraph):**

> EXPERIMENT GUARD: if an experiment is RUNNING per ~/workspace/midna-book/experiments/INDEX.md, do not alter any template, checklist, slot behavior, or process the experiment touches, and check its kill criteria against today's records; a fired kill criterion is reported as the top defect and the experiment is marked KILLED with the evidence. Never register a new experiment from this job; registration belongs to the weekly review.

### 9.2 New jobs

- `midna-weekly-memory-review`: weekly, Fridays about 19:00 ET, goal-owned (`goal:midna-trading-her-own-simulated-book`), mode task, body implementing Section 7.4's weekly agenda verbatim, writing reviews/WEEKLY-YYYY-Www.md into the book's directory and delivering decision items to the desk chat. Timeout 3600s.
- `midna-monthly-constitution-review`: monthly-equivalent via a weekly Saturday job whose body skips non-first-Saturdays (the scheduler has no nth-weekday kind; the body checks the date and exits after logging the skip), Saturdays about 11:00 ET, same owner, body implementing Section 7.4's monthly agenda, writing reviews/MONTHLY-YYYY-MM.md. Timeout 7200s (the drill is the long pole).

Both jobs follow the audit's rules block: InfinityBlade, no em dashes in reports, paper only, improvements inside the rails applied, everything touching the charter or the owner's rulings surfaced as a decision item.

### 9.3 Build order (each step verified before the next is called done)

1. Create the directory layout of Section 3.2 with empty schema-headed files; verify by listing.
2. Seed STATE.md from the initial snapshot's program list (six in-flight programs plus the desk, terminal, engines, saves, and the book) and verify each row against its system of record at seeding time, stamping real proof timestamps.
3. Seed RULINGS.md from MEMORY.md's laws and the standing rulings relevant to the operation, each entry citing its MEMORY.md source; run the first full diff immediately, since seeding is where transcription errors breed.
4. Apply Section 9.1's additions to the audit job; verify with `cron.view`; run the audit once manually and verify the archive copy, the templated snapshot, and the Health line all appear.
5. Create the two new jobs; verify schedules and owners; the weekly job's first run produces the first WEEKLY file even if its content is "registers seeded, no trades yet graded", because the book's first session is 2026-10-30 and the machinery must be proven before it is needed, not after.
6. Create experiments/INDEX.md with zero experiments and the one-running rule stated; the first experiment is registered only when the first Friday grading produces a taxonomy tally with a leading fault class. Registering an experiment before there is data to aim it at would violate the loop's own observe-first step.
7. First monthly drill at the first monthly review; until it reads RECOVERED, the snapshot protocol's status in every report is UNVERIFIED, per Section 4.5.

### 9.4 What this design deliberately does not build

- No new database, vector store, or external memory service. The operation's memory is files in the workspace, readable by any session and by the owner, diffable, archivable, and already inside the backup and save machinery's reach. A store the owner cannot open and read is a store he cannot audit, and auditability is the point.
- No automated extraction of lessons or rulings by unsupervised passes beyond the platform's existing upkeep. Distillation is judgment work; jobs tally and flag, sessions judge, reviews decide.
- No memory of other people beyond the platform's people pages, and no capture of patient or personal detail into the trading layer at all. The layers stay in their lanes: the trading memory holds the trading operation, the platform memory holds the owner.

---

## 10. Closing statement of state

Per InfinityBlade reporting: this document is a design, delivered as specified, grounded in a direct survey of the existing platform memory stack (`~/docs/memory.md`, `~/docs/self_improvement.md`, `~/docs/goals.md`), the book's CHARTER.md, JOURNAL.md, ledger.json, and CONTEXT-SNAPSHOT.md, MEMORY.md's record of the book's commission and the audit job, and the live body of cron `midna-daily-full-audit`, all read on 2026-10-29. Its status is UNVERIFIED as a system: nothing in Sections 3 through 9 is operational until the build order in Section 9.3 is executed and the first recovery drill passes. The first honest green this system can earn is that drill, and until then every report that mentions it should call it what it is: designed, not yet proven.
