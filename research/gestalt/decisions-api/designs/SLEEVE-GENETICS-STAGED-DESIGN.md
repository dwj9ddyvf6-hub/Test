# STAGED DESIGN NOTE: SLEEVE GENETICS (Invention 11)

Status: STAGED, NOT BUILT, Sat 2026-11-14. Registration:
midna-book/strategy-candidates/2026-11-14-invention-sleeve-genetics.md.

## The idea in one paragraph

339 parameterized rule sets are a gene pool. Encode each sleeve's
gate structure as a genome (gate types, thresholds, universes,
horizons); crossover the proven sleeves' structures with the
wider fleet; mutate thresholds within discipline; replay the
offspring; keep only what survives the multiple-testing gauntlet.
Hand design explores the strategy space we can imagine; evolution
explores the space we cannot. The overfitting danger is not a
caveat on this invention, it IS the invention's central problem,
and the gauntlet below is therefore a build prerequisite, not a
grading step.

## Entry ticket (all required before any offspring is replayed)

1. **The gauntlet as code.** A tested module implementing, from
   the research report section 1.2: DSR with correlation-clustered
   effective trial counts (cluster the fleet's return series
   first; raw variant counts are forbidden as N), CPCV (N=10,
   k=2, purge and embargo) producing the OOS path distribution
   and PBO, White/Hansen SPA against SPY and QQQ, and the
   Harvey-Liu-Zhu |t| > 3 hurdle for any offspring claiming a new
   family. Promotion bar: DSR >= 0.95 AND PBO < 0.2; kill bar:
   PBO > 0.5. The module ships with its own unit tests on
   synthetic noise fleets (it must reject the best of 1,000 pure
   noise strategies, the report's worked example: best noise
   Sharpe 2.23 at DSR 0.746, correctly refused at the 0.95 bar).
2. **A complete trial log.** Every variant ever run counts toward
   N, including discarded and eyeballed ones; the trial-registry
   discipline (midna-book/trial-registry.jsonl) extends to every
   replay the genetics engine runs, automatically, or the DSR is
   theatre (the report's own warning).
3. **A genome encoding with identity rules.** Crossover may not
   erase a variant's defining distinction (the C1-cool lesson of
   2026-11-14: a loosening that makes a variant identical to its
   sibling is identity erasure, not evolution). Genomes record
   parentage; every offspring is a new candidate identity, never
   a silent edit of a live sleeve.

## Entry ticket item 1: code proof exists (2026-11-14)

The gauntlet as code is built and proven: `tools/admission_exam.py`
(DSR with correlation-clustered effective trials, CPCV PBO at
N=10/k=2 with purge and embargo, Hansen SPA vs SPY and QQQ,
|t| > 3 new-family hurdle) with its synthetic-fleet proof in
`tools/test_admission_exam.py`, executed and passing. Headline
proof numbers: the best of 1,000 pure-noise strategies (Sharpe
2.037 annualized) was refused at DSR 0.676 with fleet PBO 0.644;
a planted true-Sharpe-3.5 control passed at DSR 0.999. Full
numbers, the anchor comparison, and the exam's stated limits:
`runs/ADMISSION-EXAM-PROOF-2026-11-15.md`. Ticket items 2 (trial
log) and 3 (genome encoding) remain open; no offspring is
replayed until all three are punched.

## Shape of the build, when the ticket is punched

Generation loop in the research lane on replay infrastructure
only: population = offspring of the current fleet's genomes,
fitness = CPCV OOS expectancy with the gauntlet as the selection
gate (not raw backtest Sharpe, which is precisely the failure
mode). Survivors register as candidates in the strategy-candidate
registry with parentage and gauntlet scores attached, then enter
the ordinary conveyor: shadow, paper, B5 grading. No offspring
touches a live sleeve's parameters at any stage; promotion is by
registration, never by mutation in place.

## Falsifier

Restated from the registration: evolved offspring fail
out-of-sample at the same rate as random parameter draws. The
pilot is explicitly comparative: one generation of evolved
offspring versus one generation of random draws from the same
genome space, both through the identical gauntlet and forward
window. If the evolved cohort's forward survival rate does not
beat the random cohort's, evolution added nothing and the
invention dies with its control group as the witness.
