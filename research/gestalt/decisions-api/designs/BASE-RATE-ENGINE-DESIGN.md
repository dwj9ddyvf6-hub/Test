# DESIGN: THE BASE-RATE ENGINE (Invention 9)

Status: DESIGN ONLY, Sat 2026-11-14. No build today. Registration:
midna-book/strategy-candidates/2026-11-14-invention-base-rate-engine.md.

## Mechanism

The typed layer measured exactly zero excess judging stocks. Its
untested edge is judging DECISIONS. The estate's registers are a
labeled corpus: every calibration decision, register row, B5
grade, and falsifier verdict is a triple (context, decision,
outcome). The engine mines that corpus into conditional base
rates: decisions shaped like this, in contexts like this, paid
X percent of the time. Every new proposal (a calibration change,
a candidate registration, a loosening) is priced against our own
history before the market prices it for us: the engine returns
the base rate of its decision class, the n behind it, and the
three nearest historical neighbors with their outcomes.

This is the Kalshi lesson turned inward (research report section
1.6c): a probability is only as good as its reliability diagram.
The engine publishes its own calibration on held-out decisions
continuously; an engine whose 70% bucket pays 50% is demoted to
reporting raw base rates only, automatically, by its own rule.

## Data contracts (against the attribution ledger)

The corpus: CALIBRATION-LEDGER.md decision records, the strategy
candidate registry (each falsifier verdict is an outcome), the
mandate-audit registers (EXECUTED/DONE/BLOCKED/STARTED closures
with evidence pointers), B5 grading records, and the frontier
innovation queue. Attribution join: where a decision concerns a
sleeve, its outcome fields are read from
runs/attribution_ledger_v1.json (expectancy_usd, win_rate,
excess_vs_spy_usd, own_closes, klass) rather than from prose
claims, so the corpus inherits the ledger's honesty flags
(NETTED decisions grade as provisional). Decision features:
decision class (loosening, kill, registration, sizing, filter),
surface (desk, book, terminal), sample size at decision time,
whether replay evidence existed, whether a falsifier was written
before the build, Triad vote state. Outcome: the registered
falsifier's verdict, or the graded result at its stated horizon.
Writes: its own corpus store (append-only, one row per decision,
supersede never delete) in the research lane.

## Build order

1. Corpus extraction: parse the registers into decision rows;
   Luna 6 typed extraction for the prose fields (batched, shared
   prefix, spend reported), deterministic parsing where the
   register format allows. Every row human-auditable to its
   source line.
2. Base-rate tables: per decision class and feature slice, with
   n's; slices under n=10 report as anecdotes, never as rates.
3. Proposal pricer: a lookup plus nearest-neighbor service the
   calibration lane and the candidate conveyor call before
   landing anything; its output is a flag and a prior, never a
   gate (the typed-layer standing rule applies to the engine
   too).
4. Calibration loop: held-out scoring of the engine's own
   estimates each B5; reliability diagram into the B5 record.

## Falsifier

Restated from the registration: the engine's probability
estimates calibrate no better than the fleet's raw base rate on
held-out decisions. Concretely: on the first 100 held-out
decisions, if the engine's Brier score is not strictly better
than the constant base-rate predictor, the engine is a lookup
table with pretensions and is reduced to stage 2 (tables only)
permanently.
