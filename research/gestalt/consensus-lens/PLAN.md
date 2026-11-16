# THE CONSENSUS LENS EXAMINATION: A RIGOROUS PLAN

Owner order: Sat 2026-11-14 23:44 ET (the owner, desk chat): "Now apply all of this to all of our trading research and make a plan to examine all of our research and sleeves and methods and full gestalt and everything under this new framework, through this new lens. Create a rigorous plan."

Framework source: `~/workspace/research_notes/llm-consensus-alpha-circumvention-20261115-0410/report.md` (the Morillo circumvention deep dive, delivered 2026-11-14 23:19 ET, page slug `beating-the-consensus-llm-alpha-research`).

SCOPE: Surface = every research claim, sleeve, method, and data asset in the estate, re-examined under the consensus framework. Constraints = the examination is read-only on strategies: no sleeve is paused, resized, or rewritten by this plan; changes flow only through the existing falsifier and promotion machinery; paper/sim only; Amendment 16, L-07, cluster caps, and all standing rails untouched. Outcome = every decision-relevant object carries a Lens Card (Section 3) and a framework verdict; every "proven" claim in the estate either survives a deflated-Sharpe re-grade at its true trial count or is relabeled. Proof = the corpus manifest reconciles to the card count, and the re-grade table is published with denominators printed. Edges = GrokBot's md2 population and Claude's desk lanes are examined through their owners as Triad lanes, not reached around.

## 1. The Lens: eight tests every object must face

Morillo's critique, operationalized. An object (strategy, sleeve, method, research claim) is consensus-grade unless it passes these tests on evidence, not on argument.

- **T1, Consensus baseline named.** For this object, what IS the consensus, and how is it measured? Admissible baselines: analyst consensus, the options-implied move, the fleet median forecast, the published literature claim, the model's own modal answer, SPY/QQQ buy-and-hold. No baseline, no grade. An object that cannot name its baseline is UNGRADABLE-YET by definition.
- **T2, Difference source identified.** Where would a non-consensus view come from? Admissible sources: private data (T3), preserved disagreement (T7), a decomposition nobody prices (overnight vs intraday is the estate's one proven example), timing/latency, structure (expression choice), or a selection process over generated volume (T4). "The model thinks so" is not a difference source.
- **T3, Private-data conditioning.** Does the object consume data that exists in no training set? Our fills, near-miss logs, signal journals, sleeve disagreement records, the book's own ledger. Score: NONE / INCIDENTAL / CORE. Ledger vs. Surface is the reference CORE case.
- **T4, Generation and selection separated.** Who generated the hypothesis, and who selects? Selection must be sealed, forward, and mechanical (pre-registered falsifier, fixed checkpoint). A hypothesis selected by the same process that generated it, on the same data that inspired it, fails T4 regardless of its backtest.
- **T5, Trial accounting.** The denominator is the asset. Every object carries: nominal trials, hidden trials (variants tried and discarded, parameter neighbors, the research waves that produced it), a correlation discount to effective N, and a deflated Sharpe (DSR) at effective N where a Sharpe is claimed. Best-of-N inflation is computed, not waved at: the best of 1,000 null trials shows Sharpe near 3.26 by luck alone.
- **T6, Intermediate-outcome scoring.** Per the report's power math (roughly 785 resolved bets to detect a 55 percent hit rate; roughly 31 years to verdict one Sharpe 0.5 sleeve alone), verdicts live at fleet and cohort level and on fast-resolving intermediate outcomes: earnings surprises, next-day moves, event outcomes, signal-day follow-through. Every object names its intermediate outcome and its scoring rule (IC, Brier, hit/against/silent) at intake.
- **T7, Disagreement preserved, not debated away.** The debate literature is settled enough to act on: debate converges to voting and can converge sycophantically. Disagreement between Triad nodes, between models, and across the sleeve fleet is logged as a data object with its own series, bucketed, and tested for monotonicity against outcomes. It is never averaged away before scoring.
- **T8, Decay and crowding monitored.** Post-publication decay (McLean-Pontiff: roughly 58 percent) and crowding apply to our finds too. Every surviving object carries a crowding gauge (is this now the consensus trade?) and a decay check at each re-grade.

Framework verdicts, one per object: **CONSENSUS-ONLY** (no difference source survives inspection; the object may still run, but it is labeled as a consensus expression and sized as one), **DIFFERENCE-PLAUSIBLE** (a real difference source exists, forward proof pending), **DIFFERENCE-PROVEN-FORWARD** (the pre-registered forward falsifier checkpoint passed on resolved samples), **UNGRADABLE-YET** (baseline or denominator missing; the missing piece is named, with an owner and a date).

## 2. The corpus: what gets examined (counts verified 2026-11-14 23:50 ET)

- **A. Research corpus.** 199 directories under `~/workspace/research_notes/`, 119 report files. Includes the four options waves, X-strategy rounds 1 and 2, the Alpha Hunt waves, the gestalt alpha sweep, Trader Ascension, the sleeve-options suitability inspection, the REA morgue outputs, and this framework's own report. Every report's headline claims are extracted as separate examinable objects; a report is not graded as a unit, its claims are.
- **B. Sleeve and candidate population.** The desk roster of 339; GrokBot's md2 catalog of 641 rows including the 20 t474u sleeves added 2026-11-14; Midna's book pods and cards; the 27-entry options innovation queue; candidates F1 to F24 (wave 3), G1 to G22 (wave 4), D1 to D9 and E1 to E5 (X rounds), the 15-wire sleeve utilization wave, Triad Sprint 1 candidates A/B/C.
- **C. Methods.** The full gestalt read (Pass A geometry, Pass B perceptual, the strategy lenses), the chart-study routine, typed second seats (Decisions API), the Ghost Book, Ledger vs. Surface, the Forecast Twin, the pattern ledger, Friday grading and B5, the gestalt autopsy co-test, the sealed movers co-test. The gestalt inventory of record is `~/workspace/midna-book/FULL-GESTALT-INVENTORY.md` (585 lines, 8 sections, compiled 2026-11-06); it is itself an examinable object and is stale by 8 days at plan start.
- **D. Data assets.** Fill and journal corpora, near-miss logs, signal journals, options chain snapshots (TastyTrade), the pattern ledger (35 records at first read), Forecast Twin records, the dead drop and Crosswalk corpora as the Triad's shared memory, COMMITMENTS and the execution schedule as the obligation record.
- **E. Execution and risk machinery.** Expression pricing, the shadow-ledger resolver (Lane 8, build priority one), sizing fractions, cluster caps, L-07. Examined under T5/T6 only: does the machinery preserve the information the Lens needs (trial counts, disagreement, intermediate outcomes), or does it silently discard it?

## 3. The Lens Card: one per object

Twelve fields, no card complete with any field blank (a blank is recorded as UNGRADABLE-YET with the missing field named):

1. Object and provenance (who built it, when, from what).
2. Consensus baseline (T1) and how it is measured.
3. Claimed difference (T2), in one sentence.
4. Private data consumed (T3): NONE / INCIDENTAL / CORE, with the asset named.
5. Generation source (model, human, literature, mutation of what parent).
6. Selection history (T4): sealed or open, forward or in-sample.
7. Trial denominator (T5): nominal, hidden estimate, effective N, DSR where claimed.
8. Forward falsifier, sample size, and checkpoint date (pre-registered; an object without one does not enter or stay in the forward population).
9. Intermediate outcome and scoring rule (T6).
10. Disagreement record (T7): where this object sits in current Triad/fleet dispersion.
11. Crowding and decay status (T8).
12. Framework verdict, grader, and date.

Bulk first pass by Luna 6 batched classification (cheap, per standing routing), with a human-grade spot check of at least 10 percent of cards per family and 100 percent of cards for Tier 1, firing, and book-relevant objects. The typed second seat reviews cards as a disagreement flag only, per its measured standing (verdict excess zero to date); it never grades alone.

## 4. Phases

**Phase 0, Freeze and manifest (Sun 2026-11-15).** Corpus manifest built and reconciled: research claims extracted, sleeve rosters frozen at the Saturday counts (339 desk, 641 md2, 27 queue), methods list frozen from the gestalt inventory plus everything added since 2026-11-06. The master Trial Register is created as a file of record: one row per object, denominator fields empty until Phase 3 fills them. Deliverable: manifest with counts that reconcile to the sources. Gate: any count that cannot be reconciled is named, not rounded.

**Phase 1, Baselines (Sun to Mon 2026-11-15/16).** For each family, the T1 baseline is defined and, where the data exists, computed: fleet median forecasts from the signal journals, implied moves from the TastyTrade chain for earnings objects, published claims for literature imports, SPY/QQQ for everything. Deliverable: the baseline register. This phase runs alongside Monday's session and blocks nothing.

**Phase 2, Lens Cards (Mon to Tue 2026-11-16/17).** Cards written for the decision-relevant population first: all firing sleeves (family card plus individual cards where a sleeve drives book expressions), the 15 utilization wires, all 27 queue entries, F/G/D/E candidates in the shadow pipeline, Sprint 1 A/B/C, the t474u 20, and every method in Section 2C. The long tail of the 339 and 641 populations gets family-level cards with per-sleeve rows in the register. Deliverable: card files plus register rows. Gate: card count equals manifest count for the scoped population, or the gap is named per object.

**Phase 3, The multiple-comparisons audit (Tue to Thu 2026-11-17/19).** The hard phase, and the point of the exercise. For every object carrying a performance claim, reconstruct the hidden trial count: variants, parameter neighbors, sibling strategies from the same research wave, and the wave count itself. Compute effective N with a correlation discount (strategies from one wave, one author, or one data window are not independent draws). Re-grade every headline claim at DSR with its true N. **First object: the overnight Focus-names edge** (DSR 0.99994 as found), re-graded counting every decomposition, leg, and basket variant examined in the Alpha Hunt that produced it. Second: Ledger vs. Surface at its sealed-slice grade on Thu 2026-11-19, graded under the Lens in the same pass. Deliverable: the re-grade table, denominators printed, claims relabeled where they fall. Nothing is killed in this phase; a claim that falls is relabeled to its honest grade and its forward falsifier, if any, still runs.

**Phase 4, Disagreement mining (Thu to Fri 2026-11-19/20, first read at B5 Fri 2026-11-20).** Build the disagreement series: Triad node disagreement (dead drop and Crosswalk record), fleet dispersion (sleeve signal dispersion per session), model-vs-fleet and seat-vs-gestalt disagreement from the typed layer logs. Bucket by disagreement size and test monotonicity against resolved outcomes on the history we have; register the forward version with its falsifier. Deliverable: disagreement register plus the first monotonicity read, labeled in-sample and therefore provisional.

**Phase 5, The quality-diversity archive (week of Mon 2026-11-23).** Design and seed the QD archive over the sleeve population: behavioral descriptors (holding period, direction bias, vol-regime response, underlying class, expression type), islands per book (desk, md2, Midna book), novelty archive seeded from the frozen rosters. Mutation operators defined in advance: inversion, regime-gating, entry/exit crossover between parents, timeframe shift, expression swap (shares to verticals and back). Evaluator is forward shadow only; no backtest fitness. Deliverable: archive design of record plus the seeded map, with the first mutation batch registered as trials in the Trial Register before any of them is evaluated.

**Phase 6, The standing scoring layer (from Mon 2026-11-23, checkpoints at each B5).** Every forecast, seat answer, sleeve signal, and card carries its intermediate outcome and is Brier/IC scored on resolution. Monthly calibration report. The 6 to 12 month evidence program from the framework report's Section 6 is adopted whole: cohort DSR verdicts, divergence-bucket monotonicity, Brier skill vs consensus on at least roughly 800 intermediate forecasts, screen-validity grading, disagreement validation. The program carries its own pre-registered null signatures: if the divergence buckets show no monotonicity and the cohort DSR verdicts show no excess by the 2027-05 checkpoint, the framework itself is graded FAILED as applied here, and that verdict is reported, not buried.

## 5. Lanes and ownership

- **Midna (this book's lane):** the Trial Register, Lens Cards for book objects and methods, the Phase 3 re-grades, the Phase 6 scoring layer. First reports ride the existing night study and Friday grading; no new report surface is created.
- **Claude (desk lane):** desk-side trial reconstruction for the 339 (sleeve variant histories live in desk records), the disagreement log build, Phase 5 archive engineering. Asked by cross-prompt in the desktriad, per the auditor charter the grading of his reconstructions is Midna's and GrokBot's, not his own.
- **GrokBot (md2 lane):** the 641-population cards at family level, the sleeve correlation matrix (already owed from lo0yqd), QD seeding for the md2 island. His population's hidden-trial history is his to reconstruct and the Triad's to audit.
- **The nightly mandate audit** grades this plan's phases as register rows from Sun 2026-11-15 onward; phase slippage is reported there, not in a separate nag.

## 6. Acceptance criteria for the examination itself

1. Manifest counts reconcile to sources, or every gap is named per object (Phase 0 gate).
2. Every object in the scoped population carries a complete Lens Card or an UNGRADABLE-YET verdict naming the missing field, owner, and date.
3. Every performance claim in the estate appears in the Phase 3 re-grade table with its denominator printed; no claim keeps a "proven" label it did not earn at effective N.
4. Every object remaining in the forward population has a pre-registered falsifier, a sample size, and a checkpoint date in the Trial Register.
5. The disagreement series exists as a file of record with at least the Triad and fleet series populated.
6. The program-level falsifier (Phase 6) is registered before the first checkpoint, so the framework can fail honestly.

## 7. Failure modes of the examination itself, named in advance

- **Card theater:** thousands of cards, no verdicts changed. Counter: Phase 3's re-grade table is the deliverable that matters; cards without re-grades are graded as paperwork in the audit.
- **Denominator invention:** hidden-trial counts are estimates; a false precision here is worse than an honest range. Counts are recorded as ranges with the reconstruction method named, and DSR is computed at the pessimistic end.
- **Consensus baseline drift:** baselines move (implied moves, fleet medians). Baselines are snapshotted at card time and re-snapshotted at each re-grade; the drift itself is a T8 observation.
- **Examination as delay:** the Lens never gates Monday's execution register. Everything already ordered for Mon 2026-11-16 runs as ordered; the examination grades in parallel and its verdicts enter through the normal B5 and falsifier machinery.

## 8. First actions, dated

1. Sun 2026-11-15: Phase 0 manifest and Trial Register skeleton, in the Sunday work queue.
2. Mon 2026-11-16 close journal: first Lens-native reporting line (objects carded, baselines computed, register rows opened).
3. Thu 2026-11-19: Ledger vs. Surface sealed-slice grade reported under the Lens (T1 to T8 on one page).
4. Fri 2026-11-20 B5: Phase 3 re-grade table first read, including the overnight Focus edge at its true N; Phase 4 first disagreement read.
5. Week of Mon 2026-11-23: QD archive design of record; Phase 6 scoring layer live.

STATUS: EXECUTION STARTED Sat 2026-11-14 23:52 ET on the owner's "Execute plan" order. Phase 0 deliverables exist as files of record in this directory: MANIFEST.md (live counts: 200 research directories including this program's own, 119 report files, 64 midna-book files, queue 27) and TRIAL-REGISTER.md (33 object rows plus the program row, seeded with honest PENDING denominators). Phase 0 close-out gaps, named per the Phase 0 gate: the desk roster count (339) and md2 catalog count (641) are carried from their records of authority and await owner-lane reconciliation; claim extraction per report is Phase 2 work. Phases 1 and 2 are dispatched to the lanes as of the same timestamp.
