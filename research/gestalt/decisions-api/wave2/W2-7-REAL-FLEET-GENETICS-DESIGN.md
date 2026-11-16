# W2-7 REAL-FLEET GENETICS DESIGN (DESIGN ONLY, no real offspring replayed)

Status: filed Sat 2026-11-14, after the synthetic noise proof in
W2-7-GENETICS-TICKET.md (zero promotions from noise). This document
scopes a future real-fleet pass. Nothing in it was executed in the
W2-7 run: no real sleeve was crossed, mutated, or replayed.

## Scope

Population: the fleet genomes in wave2/fleet_genomes.json, extended
before any run to the full encodable fleet (every live sleeve whose
gate structure the encoding in tools/genome.py can express; sleeves
it cannot express are named and excluded, never approximated
silently). The six founding genomes already encoded: the Tensor lens
sleeve, absorption_base_link, breakout_ada, gate_1h, Pod A1 VCP, and
the C1 cool trio (the only one whose gate values are fully documented
rather than schematic).

Precondition that is NOT yet met: five of the six founding genomes
carry schematic_params=True. A real pass may not start until each
participating genome's parameters are transcribed from the desk's
own records and the schematic flag is cleared genome by genome, with
the transcription source recorded. Running evolution on schematic
parameters would evolve the reconstruction, not the fleet.

## Shape of the run, when it is authorized

1. Generation loop in the research lane only, on replay
   infrastructure only, exactly as the staged design specifies
   (designs/SLEEVE-GENETICS-STAGED-DESIGN.md). No offspring touches a
   live sleeve's parameters at any stage; promotion is by candidate
   registration, never by mutation in place (identity rule R4).
2. Every generated variant, accepted or identity-refused, is
   appended to wave2/genetics_trial_log.jsonl by tools/trial_log.py
   before any replay, and the exam is fed the log's honest count
   (seeded floor 74 plus every replayed variant, growing as the log
   grows). The floor caveat rides along: the true historical N is
   larger than 74 by an unknown amount, so real-fleet DSRs computed
   against the floor are upper bounds, and any promotion near the
   0.95 bar must be reported with that caveat attached.
3. Fitness and selection: the admission exam only (DSR with
   correlation-clustered effective trials, CPCV PBO N=10 k=2,
   Hansen SPA vs real SPY and QQQ series, |t| > 3 for new-family
   claims), is_new_family set per offspring by whether its gate-type
   set matches an existing family's. Raw backtest Sharpe is never a
   selection criterion.
4. The comparative falsifier from the staged design is part of the
   run, not an afterthought: one generation of evolved offspring
   versus one generation of random draws from the same genome space,
   identical gauntlet, identical forward window. If the evolved
   cohort's forward survival does not beat the random cohort's, the
   invention dies with its control group as witness.
5. Survivors register as candidates in the strategy-candidate
   registry with parentage and gauntlet scores attached, then enter
   the ordinary conveyor: shadow, paper, B5 grading.

## Known encoding limits that bind this design

Stated in full in W2-7-GENETICS-TICKET.md. The binding ones here:
discretionary sleeves (the Capitulation Basket form) cannot be
encoded and are out of population; options expression choice is not
in the genome, so offspring inherit their parents' expression lane
by registration, not by evolution; the Tensor score is an opaque
input, so Tensor-family offspring evolve around the engine, never
inside it (and the Tensor engine and its pins are untouched by this
program in any case).

## Degeneracy note carried from the synthetic pass

Crossover unions parental gate sets and signals are a conjunction,
so offspring are systematically more restrictive than parents: in
the synthetic pass 31 of 72 variants never fired. A real pass must
either accept that waste (each dead variant still counts as a trial)
or adopt a stated operator change (for example gate dropout with a
recorded probability) BEFORE the run, in writing, in an amendment to
this design. Changing operators mid-run is forbidden.

## What would authorize execution

A separate, explicit go decision naming: the cleared (non-schematic)
genome set, the replay data windows, the generation size, and the
random-control cohort size. This design alone authorizes nothing.
