# W2-7 GENETICS TICKET COMPLETED: items 2 and 3, and the synthetic noise proof

Workstream W2-7, Alpha Hunt Wave 2. Sat 2026-11-14.
Design of record: designs/SLEEVE-GENETICS-STAGED-DESIGN.md.
Item 1 (the gauntlet as code) was already punched:
tools/admission_exam.py, proof in runs/ADMISSION-EXAM-PROOF-2026-11-15.md.
This file punches items 2 and 3 and runs the proof the ticket demands
before any real offspring may be replayed. No desk tree files were
touched; everything lives in this research folder.

## Item 2: a complete trial log (tools/trial_log.py, wave2/genetics_trial_log.jsonl)

The log is append-only JSONL. From its creation forward it is
complete by construction: the genetics engine appends every variant
it generates or replays (variant identity and genome identity hash,
parentage, full canonical parameters, data window, exam outputs)
before examination, and the admission exam is fed the log's running
count. Variants refused by the identity rules are logged too, with
status generated_refused_identity; they count in the generated total
but not in the replayed trial count fed to the DSR, because they were
never evaluated on data. That asymmetry is written into the module
docstring so it never has to be guessed.

Seeding, honestly. The log was seeded from the estate's three
surviving trial records, read at seed time: hunt/exam_results.json
(per-candidate honest trial counts from the H1 conveyor exam:
CAND-ROT-04 56, CAND-WASH-01 6, CAND-FORCED-01 3, CAND-FORCED-05 3,
CAND-CTB-SPOT-ADA 3, CAND-CTB-SPOT-LINK 3), midna-book/trial-registry.jsonl
(15 rows; counted as 0 additional trials because its candidates are
the named candidates already inside the exam counts, the rotation
family's registry count of 10 sitting inside ROT-04's 56-cell sweep
grid, or are typed-layer and book-process trials that are not sleeve
replays), and hunt/conveyor_ledger.jsonl (23 records; the examined
ones already counted via the exam results, the rest recorded
NOT_EXAMINED or design-stage, which adds specification count, not
trials).

The header of the log states the limit in plain words: the
historical record is INCOMPLETE. Variants run, eyeballed, or
discarded before 2026-11-14 without being written into one of those
three records are not in this log and cannot be reconstructed;
inventing them would be fabrication. The defensible effective N
floor is therefore 74, stated as a floor, and every DSR computed
against it is an upper bound on the true DSR.

## Item 3: a genome encoding with identity rules (tools/genome.py)

A genome is: an ordered set of gates (13 gate types: trend_filter,
momentum_rank, volatility_gate, volume_gate, breakout_trigger,
absorption_trigger, cooldown, regime_gate, rsi_gate, calendar_gate,
tensor_score, marker_gate, continuation_hold; each gate carries
typed parameters), a universe, a horizon,
an exit rule (triple_barrier, trailing_stop, time_stop,
signal_reversal, fixed_horizon), a declared defining distinction, and
parentage. The canonical form (gates sorted, floats rounded) hashes
to an identity hash; two genomes with the same canonical form are
the same strategy for trial counting, whatever their labels say.

Identity rules, enforced in code and tested in tools/test_genetics.py
(all 10 checks pass):

- R1, distinction preservation. Crossover and mutation refuse any
  offspring whose gate set no longer contains at least one defining
  gate from each parent it claims descent from. The test case is the
  documented C1-cool erasure itself: the cool trio's defining gate is
  the buy-cyan marker (gates documented verbatim in
  midna-book/strategy-candidates/2026-11-14-c1-cool-relaxed.md:
  marker required, close at most 5, ret60 at least 31, atr at most
  1.0), and the loosening refused on 2026-11-14 (marker removed, atr
  cap raised) is refused again here by _enforce, mechanically.
- R2, no silent identity collision. An offspring canonically
  identical to a parent or to any registered identity is refused
  (tested: a zero-jitter mutation clone is refused).
- R3, parentage is mandatory. A generation above 0 with no recorded
  parents cannot be constructed.
- R4, live sleeves are immutable. Operators always mint a new
  candidate id; a live sleeve's genome can be a parent, never a
  return value.

Expressiveness proof: tools/build_fleet_genomes.py encodes six real
fleet sleeves into wave2/fleet_genomes.json, all with distinct
identity hashes: the Tensor lens sleeve (Tensor family), 
absorption_base_link (absorption), breakout_ada (breakout), gate_1h
(gated continuation), Pod A1 VCP (book breakout), and the C1 cool
trio. Each carries its source pointer. Five carry
schematic_params=True, stated on the record: their gate structure is
documented, but the desk's exact live thresholds were not in the
records read for this pass, so the numbers are structural
reconstructions and are flagged as such rather than presented as
desk values. Only the C1 cool trio's gate values are the documented
ones. The exit rule on the 4H sleeves (triple barrier 2xATR(14),
vertical 30 bars) is documented in hunt/nsm_fleet_v2.json.

What the encoding cannot express, stated plainly:

- Discretionary judgment. A sleeve whose entries depend on a human
  or typed-layer read of a specific situation (the Capitulation
  Basket form) has no genome; it is outside the population, not
  approximated.
- Stateful path dependence beyond the exit rule: pyramiding,
  tranche scaling, and add-on logic that depends on the trade's own
  history are not representable; gates are functions of market state
  only.
- Cross-sleeve interaction: portfolio heat, correlated exposure, and
  one sleeve's fill changing another's decision are portfolio-layer
  facts, not genome facts.
- Options expression: strike, tenor, and structure choice are not in
  the genome. An offspring inherits an expression lane by candidate
  registration, never by evolution.
- Intraday microstructure: the genome is bar-grain. Timing inside
  the bar, queue position, and spread capture are invisible to it.
- The inside of an opaque score: tensor_score and marker_gate take
  the engine's output as an input. Offspring can evolve thresholds
  around the Tensor engine; they cannot evolve the engine.

## The proof: first genetics pass on a synthetic noise fleet only

tools/genetics_pass.py, seed 20261114, fully reproducible. Market:
six synthetic underlyings, geometric random walk, zero drift, daily
sigma 1.2 percent, T = 750 bars, with synthetic OHLC, volume, a
random Tensor-like score series, and a random marker series.
Benchmarks: synthetic SPY-like and QQQ-like series as in the exam's
own proof. Every strategy on this market is noise by construction:
the price series contains no information about its own future.
Replay semantics are stated in the module: signals are the AND of a
genome's gates on daily features, entry next bar, exit by the
genome's exit rule at daily grain.

One correction was made before the counted run, stated here as the
rules require. The first execution (discarded, not counted) exposed
a semantics bug in the synthetic layer, not in the gauntlet: the
marker_gate's default ret60_min range (20 to 40 percent over 60
days) is unreachable on a 1.2 percent daily sigma random walk, so
every marker-carrying variant was a constant zero series and its DSR
was undefined. Rule adopted in writing before the rerun: synthetic
gate parameter ranges must be reachable on the synthetic market
(marker ret60_min redrawn at 2 to 12 percent), founder genomes draw
2 to 3 signal gates, and any variant that still replays to a zero
series is logged, counted as a trial, reported as degenerate in the
accounting, and excluded only from the best-variant statistics
(a zero series has no Sharpe and cannot promote). The gauntlet's
bars were not touched.

Accounting of the counted run (wave2/W2-7-SYNTHETIC-PASS-RESULTS.json,
trial log wave2/genetics_trial_log.jsonl, 82 lines: 1 header, 8 seed
records, 72 trial records, 1 exam record):

- Parents: 12 synthetic noise founders (NOISE-P00 to NOISE-P11).
- Offspring: 60 accepted (NOISE-X000 to NOISE-X059) from 63 attempts
  (crossover two of three attempts, mutation one of three); 0
  identity refusals occurred in this run (the refusal path is proven
  by the unit tests above, and any refusal would have been logged).
- Trials logged this pass: 72 replayed (12 parents + 60 offspring),
  on top of the seeded floor of 74, for a total honest trial count
  of 146 fed to the admission exam. Exam setting: is_new_family=True
  (the strictest), SPA 500 bootstraps.
- Degenerate zero-series variants: 31 of 72, all logged and counted.
  Cause, stated as a property of the encoding, not hidden: crossover
  unions parental gate sets and signals are a conjunction, so
  offspring are systematically more restrictive than their parents.
- Best offspring: NOISE-X039, annualized Sharpe 0.672, DSR 0.262,
  |t| recorded in the results file. Best variant overall was also
  NOISE-X039.
- Family PBO: 0.422 (above the 0.2 promotion bar). Family SPA
  p-values: SPY 0.804, QQQ 0.882 (no rejection against either).
- Family verdict: REJECT.
- Promotions: 0, of offspring and of parents alike.

The gauntlet promoted zero offspring from noise, on every leg at
once: the best offspring failed DSR by a wide margin (0.262 against
the 0.95 bar), the family failed PBO, and SPA rejected nothing. No
finding against the gauntlet arises from this run, and no bar was
tightened or loosened after seeing the numbers.

## Real-fleet design

Filed as wave2/W2-7-REAL-FLEET-GENETICS-DESIGN.md, design only. No
real offspring was replayed in this run. Its named precondition: the
five schematic genomes must be transcribed from desk records and
cleared genome by genome before any real pass, and the comparative
falsifier (evolved cohort versus random cohort through the identical
gauntlet) is part of that future run, not an afterthought.

## Verdict

Ticket items 2 and 3 are built, tested, and proven in the artifacts
named above; the synthetic noise proof passed with zero promotions.
Combined with item 1 (punched 2026-11-14), the Sleeve Genetics entry
ticket is fully punched. What remains open, named: the historical
trial floor of 74 is a floor, not the true N; five of six fleet
genomes carry schematic parameters pending desk transcription; and
the real-fleet pass itself awaits its own explicit go decision under
the filed design.

STATUS: GREEN, proven on the final artifacts. Evidence pointer:
tools/test_genetics.py (10 of 10 checks passed) and
tools/genetics_pass.py run output with wave2/W2-7-SYNTHETIC-PASS-RESULTS.json
and wave2/genetics_trial_log.jsonl (72 trial records, exam record
trial count 146, promotions empty), all 2026-11-14.
