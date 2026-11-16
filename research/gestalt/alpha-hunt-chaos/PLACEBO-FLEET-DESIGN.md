# THE PLACEBO FLEET: DESIGN OF RECORD

Seeded Sun 2026-11-15. Source idea: Chaos Lab Lane 4, Idea 1 (rank 1 of 15),
`~/workspace/research_notes/alpha-hunt-chaos-20261115/LANE4-ABSTRACTION-UP.md`.
Program home in the master Trial Register:
`~/workspace/research_notes/consensus-lens-examination-20261114/TRIAL-REGISTER.md`,
rows 34 to 57 (appended with this design).

## 1. Purpose, stated plainly

Every grade this estate hands out is computed against a theoretical null: a
deflated-Sharpe formula, a base rate, a degenerate baseline. Those nulls assume
a world. The Placebo Fleet replaces the assumption with a measurement: a
standing cohort of fake sleeves, driven by seeded random processes, processed
through the identical journaling, dispatcher, expression-pricing, and grading
pipeline as the real 339. From the cohort's first full census window onward,
every real cohort grade is reported as a percentile against the placebo
distribution of the same statistic over the same window.

The fleet has two jobs, in this order:

1. **Audit the machinery.** If random sleeves systematically earn grades the
   estate would promote on, some artifact (fill model, cost model, grading
   window, denominator choice) is manufacturing edge, and every verdict the
   machinery has produced inherits the suspicion until the artifact is found.
2. **Grade the real fleet honestly.** A real family's expectancy means what
   its percentile against its placebo twins says it means, no more.

A placebo is never a candidate. It cannot be promoted, sized, or traded. Its
only product is a distribution.

## 2. The cohort: 24 placebo sleeves, 8 archetypes x 3 host matches

Each archetype is instantiated three times, once per host surface, because
each surface has its own graders and its own artifacts:

- **Host T (tensor):** matched to the Tensor-family fire stream; its fires
  flow to the Ghost Book expression-pricing surface, the surface that ruled
  11 of 21 real Tensor fires viable.
- **Host E (aster-etf):** matched to the aster ETF monthly family (the
  c098/m150 mirror-twin population), the desk's low-fire-rate, high-twin
  surface where family statistics aggregate siblings.
- **Host B (book):** matched to Midna's book card flow; journaled as shadow
  fills in the book's ledger under the charter fill rule (next bar's open),
  in a segregated placebo pod so real equity never mixes.

### The eight archetypes

| Code | Name | Signal process | What it audits |
|------|------|----------------|----------------|
| A1 | PURE-RANDOM | Seeded Poisson entries at the host family's fire rate; direction drawn at the family's entry-side mix; holds drawn from the family's empirical hold distribution; universe = family universe | The whole pipeline end to end; the reference null |
| A2 | TIME-SHIFTED | A real sleeve's actual signal stream replayed shifted by a seeded offset of sessions (offset drawn 5 to 40 sessions, fixed per instance) | Timing value: keeps every distributional property of a real stream except when it fires |
| A3 | SYMBOL-SHUFFLED | A real sleeve's actual signal stream with symbols permuted inside the family universe by the instance's seeded shuffle | Name selection: keeps timing and fire structure, destroys which names |
| A4 | COIN-GATE | A real sleeve's signals admitted only when the instance's seeded coin lands heads (p = 0.5 per signal) | Fire-rate and selection effects of gating itself, with zero information |
| A5 | NOISE-TWIN GATE | A real sleeve whose decisive gate variable is replaced by a seeded noise series matched on the real variable's mean and variance over the lookback | Whether the gate variable carries information or the gate is furniture |
| A6 | SEGMENT-FORCED | A1 randomness with all entries forced into one session segment per instance (01: midday 10:30-15:00 ET; 02: open drive 09:30-10:30 ET; 03: close hour 15:00-16:00 ET) | Whether grading prices segment artifacts as sleeve skill (Lane 3 measured midday at minus 28.9 bp mean across 294 symbol-sessions while overnight and open drive were positive) |
| A7 | MIRROR-CLONE | A byte-identical clone of a real sleeve (same registry weight, sizing ladder, family membership) whose signal stream is A1 randomness | Family-level breadth illusion: whether clones of noise aggregate into a family verdict |
| A8 | CROWDED-NAMES | A1 randomness restricted to the fleet's most crowded names (the names the most real sleeves trade, from the dispatcher record) | Whether crowding itself (shared tape, shared liquidity) flatters grades |

### The 24 registered instances and their seeds

Seeds are derived, not chosen: `seed = first 8 bytes (big-endian uint64) of
SHA256("PLACEBO-FLEET-2026-11-15|" + placebo_id)`. They are printed here, in
advance, before any placebo has run. This table is the seed registry.

| Placebo ID | Archetype | Host | Seed (uint64) |
|---|---|---|---|
| PLC-A1-01 | A1 PURE-RANDOM | tensor | 4214450105643567765 |
| PLC-A1-02 | A1 PURE-RANDOM | aster-etf | 14630443754422475164 |
| PLC-A1-03 | A1 PURE-RANDOM | book | 13094985731221803594 |
| PLC-A2-01 | A2 TIME-SHIFTED | tensor | 1549133021098496569 |
| PLC-A2-02 | A2 TIME-SHIFTED | aster-etf | 3329498781936379361 |
| PLC-A2-03 | A2 TIME-SHIFTED | book | 16158752639431155021 |
| PLC-A3-01 | A3 SYMBOL-SHUFFLED | tensor | 15603371431760574164 |
| PLC-A3-02 | A3 SYMBOL-SHUFFLED | aster-etf | 2275377457387210095 |
| PLC-A3-03 | A3 SYMBOL-SHUFFLED | book | 11421291535920947510 |
| PLC-A4-01 | A4 COIN-GATE | tensor | 16136860191243639977 |
| PLC-A4-02 | A4 COIN-GATE | aster-etf | 10048379350936978327 |
| PLC-A4-03 | A4 COIN-GATE | book | 11545684739409238453 |
| PLC-A5-01 | A5 NOISE-TWIN GATE | tensor | 11390102071429729450 |
| PLC-A5-02 | A5 NOISE-TWIN GATE | aster-etf | 13969087884153481025 |
| PLC-A5-03 | A5 NOISE-TWIN GATE | book | 6879865926899236579 |
| PLC-A6-01 | A6 SEGMENT-FORCED (midday) | tensor | 3067464749535632940 |
| PLC-A6-02 | A6 SEGMENT-FORCED (open drive) | aster-etf | 8065151652499610821 |
| PLC-A6-03 | A6 SEGMENT-FORCED (close hour) | book | 14319372705227124292 |
| PLC-A7-01 | A7 MIRROR-CLONE | tensor | 18230609175744146869 |
| PLC-A7-02 | A7 MIRROR-CLONE | aster-etf | 11900371294071464770 |
| PLC-A7-03 | A7 MIRROR-CLONE | book | 3690010273795881756 |
| PLC-A8-01 | A8 CROWDED-NAMES | tensor | 10586776903364742973 |
| PLC-A8-02 | A8 CROWDED-NAMES | aster-etf | 14388024002753426513 |
| PLC-A8-03 | A8 CROWDED-NAMES | book | 9127506938603504782 |

### Seed discipline (registered, binding)

1. The seeds above are fixed before any placebo output exists. No seed is
   ever re-rolled, for any reason, including a seed whose placebo grades
   embarrassingly well or badly. A suspiciously good placebo is a finding
   about the machinery, not a reason to deal again.
2. All randomness in a placebo instance draws from a single stream seeded
   with its registered seed (PCG64 or the desk's standard seeded RNG; the
   generator algorithm is recorded beside the first output it produces).
   Draws are consumed in journal order, so any run is reproducible
   byte-for-byte from the seed and the input tape.
3. If a placebo must be rebuilt (code defect, corrupted journal), the
   rebuild uses the same seed and the defect is logged in the desk BUGLOG
   with the rebuild noted on the instance's Trial Register row. If a rebuild
   with the same seed is impossible, the instance is retired on its row and
   a replacement enters only as a new row in a new cohort (PLACEBO-FLEET-2),
   never as an edit to this table.
4. New archetypes or instances enter only as new register rows with new
   derived seeds (same derivation, new IDs), appended, never inserted.

## 3. Matching statistics: what "matched" means, with sources

A placebo that does not match the real fleet's gross statistics tests a
fleet that does not exist. The matching targets, each with its source of
record in the estate:

| Statistic | Matched value / computation | Source of record |
|---|---|---|
| Population and states | 339 desk sleeves; 65 LIVE-FIRING, 38 FIXTURE-PROVEN, 233 ARMED-PROVEN, 1 DEFECT, 2 UNFED at seed time | `~/workspace/research_notes/sleeve-activation-calibration-20261111/execution_board.csv` (2026-11-14 board) |
| Fire rate | Per-sleeve fills per session and closes per 5 sessions, taken per host family; fleet aggregate: 71,495 intents over 14 sessions, 6,803 filled (9.5 percent of intents) | `frequency.csv` in the same calibration directory (per-sleeve `fills_per_session`, `closes_per_5_sessions`); fleet census in `~/workspace/research_notes/alpha-hunt-chaos-20261115/LANE3-PRIVATE-DATA.md` section 0 (counted from `~/workspace/muse-desk-v3/state/*/journal.jsonl`, 1,353,045 lines, 2026-10-23 to 2026-11-15) |
| Intent outcome mix | Filled 9.5 percent, rejected 62.9 percent, queued 16.5 percent, submitted 7.2 percent, duplicate 3.8 percent of intents. Placebos do not script this mix: they submit through the same dispatcher with sizing drawn from the host family's ladder, so the mix must emerge; a placebo whose fill rate departs the family band is a matching defect, reported as such | Lane 3 census, same source as above; dispatcher record `~/workspace/muse-desk-v3/state/dispatcher.jsonl` |
| Direction mix | Entry-side mix per family, computed at build from the dispatcher record (849 buy_to_open fills counted in the record at Lane 3's pass; the fleet is long-dominant). A1/A6/A8 draw direction at the computed per-family mix, never at 50/50 | `dispatcher.jsonl`, mined in LANE3-PRIVATE-DATA.md sections (a) and (c) |
| Holding periods | Per-family empirical hold distribution, computed at build from journal fill pairs (entry fill to exit fill per sleeve); cadence classes on record: hourly (cadence_s 3600), 4H (14400), daily, and monthly (the c098 ETF family). Book holds on record: 14 fills, 4 resolved trades (SHOP, MO, ELF, NVDA) 2026-10-30 to 2026-11-13 | `frequency.csv` evidence column (per-sleeve cadence); `~/workspace/midna-book/ledger.json` |
| Universe | Host family universe as traded: desk dispatcher record carries 33 symbols; desk bar cache carries 22 daily symbols; book universe is the Focus 30. A placebo never trades a name outside its host family's traded set | LANE3-PRIVATE-DATA.md section 0 inventory; `~/workspace/muse-desk-v3/cache/bars/` |
| Unfed share | 36.0 percent of all journal lines are `unfed` evaluations. A placebo whose feed is always live is not matched: the placebo's evaluation loop reads the same feed-health state as its host family, so it evaluates unfed exactly when the family does | Lane 3 census (487,327 of 1,353,045 lines) |
| Session-segment shape | Fleet intents run on a machine clock (2,014 to 5,996 intents in every ET hour, no RTH concentration); segment returns on record: overnight +15.6 bp, open drive +11.7 bp, midday minus 28.9 bp, close hour minus 7.8 bp (294 symbol-sessions) | LANE3-PRIVATE-DATA.md section (d) |
| Expression viability base rate | Ghost Book: 21 real Tensor fires priced, 11 viable at R >= 1.0 (52 percent). Tensor-host placebo fires are priced by the same selector; their viability rate is the null for that surface | `~/workspace/midna-book/ghost-book-ledger.jsonl` |
| Sizing | The host family's own sizing ladder and slice accounting, unchanged, so the dispatcher's slice buying-power gate bites placebos at the family rate (773 insufficient_slice_bp blocks on record, 552 from three mirrored dmac variants) | `dispatcher.jsonl` via LANE3-PRIVATE-DATA.md section (a) |

Matching is verified, not asserted: at the cohort's first census, each
placebo's realized fire rate, fill rate, direction mix, and hold
distribution are printed beside its host family's, and any statistic outside
the family's interquartile band is named a matching defect on the
instance's register row. A mismatched placebo grades nothing until fixed;
fixing a matching defect is a build change, never a seed change.

## 4. Trial registration and denominator rules

1. Every placebo instance is one row in the master Trial Register (rows 34
   to 57), appended with this design. Each instance is a countable trial.
2. Placebo denominators are printed as placebo trials wherever they are
   used: a real family graded against this cohort carries the line
   "null: 24 placebo trials (8 archetypes x 3 hosts), nominal fires as
   accrued, hidden trials 0 by construction (archetypes and seeds
   pre-registered 2026-11-15 in PLACEBO-FLEET-DESIGN.md), effective N of
   the null 8 to 24 (24 independent seeds, discounted toward 8 by
   archetype clustering: instances of one archetype share a generator
   design and are not fully independent draws)."
3. Hidden trials are zero by construction and stay zero: the archetype
   list, the instance count, the seeds, and the matching statistics were
   all fixed in this document before any placebo output existed. Any
   later design change is a new cohort, not an edit, so it cannot smuggle
   hidden trials into this cohort's denominator retroactively.
4. Placebo grades never enter any real cohort's numerator. They form the
   null distribution only. A report that averages placebos into a fleet
   statistic is a defect on its face.

## 5. How grades get reported once the fleet runs

1. No percentile is reported before the cohort completes its first full
   census window (14 sessions, matching the window the fleet statistics
   above were counted over). Before that, placebo output is plumbing
   evidence only.
2. From that window on, every family-level and cohort-level grade in the
   Friday grading and the mandate audit carries three numbers: the real
   statistic, the placebo distribution of the same statistic over the
   same window (median and interquartile band across the 24, and across
   the host-matched subset where the family has one), and the real
   statistic's percentile in that distribution.
3. The placebo cohort's own distribution is printed as a standing audit
   line each census: median placebo expectancy, share of placebos with
   positive expectancy, best placebo expectancy, and the count of
   placebos grading above the real fleet's median sleeve. That line is
   the audit of the machinery, and it is reported even when (especially
   when) it is embarrassing.
4. A single placebo grading in the real fleet's top decile in two
   consecutive census windows triggers a named machinery audit (fill
   model, cost model, grading window, denominators, in that order), not
   a promotion, not a seed change.

## 6. Falsifiers

**For the placebo program itself (the machinery falsifier).** If, over two
full quarters from the cohort's first live session (quarters ending
2027-02-16 and 2027-05-17; read at the Fri 2027-05-14 B5, the last B5
before the second quarter closes), no real cohort (family or book cohort)
separates from the placebo distribution at cohort level (operationally:
the real cohort's median statistic inside the placebo interquartile band
in both quarters, on expectancy and on profit factor), then the finding
is the grading machinery itself: the census, the Ghost Book viability
surface, and the family verdict machinery are graded as producing grades
without signal discrimination, that verdict is reported at B5 in those
words, and no promotion decision may cite those grades until the
machinery is rebuilt and re-proven against a fresh placebo cohort.

**For the fleet's added value (the Lane 4 falsifier, carried verbatim in
substance).** If real sleeves' percentile ranks under the empirical null
match their ranks under the theoretical null within noise across two
families, the placebo fleet adds nothing over the formula it replaced and
is retired to a one-time pipeline audit, with the retirement and its
evidence printed in the register.

**Per-archetype falsifiers** ride on the cohort read: an archetype whose
distribution sits visibly below the real lower quartile on every host
(A4 is the expected candidate) has audited its surface and found it
honest; that is a result, recorded on its rows, not a failure of the
program.

## 7. Pipeline touchpoints: what the placebos must flow through

Registration (this task) changes only the Trial Register. The build that
makes the fleet live touches the following, each change stated here and
**not made in this task**:

1. **Desk sleeve registry and runner** (`~/workspace/muse-desk-v3/`, sleeve
   configs feeding `state/<sleeve>/journal.jsonl`). Change needed: a
   placebo sleeve class whose signal source is the seeded generator of
   section 2, registered in the same roster as the 339, journaling to
   `state/<placebo_id>/journal.jsonl` in the identical record shapes.
   The Tensor engine is not touched; Tensor-host placebos consume the
   family's published fire interface, they do not enter the engine.
2. **Dispatcher** (`state/dispatcher.jsonl`). No change needed by design:
   placebos submit intents through the same dispatcher, the same slice
   buying-power accounting, and the same rejection paths. If the
   dispatcher cannot accept a non-sleeve intent source, that gap is
   itself a finding and is reported before any workaround is built.
3. **Census and ranking builders** (`build_frequency.py`,
   `build_ranking.py`, outputs `frequency.csv` and `ranking.csv` in
   `~/workspace/research_notes/sleeve-activation-calibration-20261111/`).
   Change needed: include placebo directories in the census population
   under a `population = placebo` tag, and add the percentile computation
   of section 5 to the family rows. Until the builders carry the tag,
   placebo rows are excluded from fleet statistics by hand and the
   exclusion is named in each census.
4. **Ghost Book and expression selector**
   (`~/workspace/midna-book/ghost-book-ledger.jsonl`,
   `~/workspace/midna-book/tools/expression_selector.py`). Change needed:
   tensor-host placebo fires priced by the same selector on the same
   chain data and appended to the ledger with a placebo flag and the
   placebo ID, resolvable by the same resolver path as real fires.
5. **Book ledger and journal** (`~/workspace/midna-book/ledger.json`,
   `JOURNAL.md`). Change needed: a segregated placebo pod (the pod field
   is mandatory at signing and fill from Mon 2026-11-16) carrying
   book-host placebo shadow fills at the charter fill rule; placebo pod
   equity is reported separately and never enters book equity, pod
   ladders, or heat.
6. **The shadow-ledger resolver (Lane 8)**. Change needed: placebo
   expressions and fills enter the same resolution queue with the same
   priority rules; a resolver that grades real fires and skips placebo
   fires voids the design.
7. **Friday grading and the nightly mandate audit**. Change needed: the
   standing percentile line and placebo audit line of section 5 added to
   both bodies (the audit body addition follows the owner's confirmed-step
   pattern for job edits; stated here, made by that route, not in this
   task).
8. **Trial Register**. Done in this task: rows 34 to 57. Future cohorts
   append below them.

## 8. Divergent generation input: the typed seats (Decisions API)

Per the task, typed seats (connector `custom.openai`, POST /v1/decisions,
model `gpt-6-luna`, through the governed harness
`~/workspace/midna-book/typed-layer/decisions_harness.py`) were asked for
the most deceptive placebo designs: the ones most likely to fool our own
graders. Bank `placebo-fleet-generation` v1.0, one request, 17 questions,
run 2026-11-15T13:14:11Z, cost $0.000482 (4,820 input tokens, output
uncharged). Full record with pack hash:
`~/workspace/research_notes/alpha-hunt-chaos-20261115/PLACEBO-GENERATION-RECEIPT.json`.
The seat's standing in this estate is a disagreement flag only (verdict
excess exactly 0 to date, Trial Register row 31); its answers below are
generation input, recorded verbatim in substance, and they decided
nothing. What they changed: replication emphasis inside a cohort whose
composition the matching statistics had already fixed (section 8.3).

### 8.1 Deceptiveness scores (probability-weighted band, 0 = harmless null to 4 = maximally deceptive)

| Archetype | Weighted band | Modal band (probability) |
|---|---|---|
| A2 TIME-SHIFTED | 2.69 | deceptive (0.38), highly deceptive close behind (0.36), maximally deceptive 0.20 |
| A3 SYMBOL-SHUFFLED | 2.57 | highly deceptive (0.53) |
| A7 MIRROR-CLONE | 2.51 | deceptive (0.59), maximally deceptive 0.21 |
| A6 SEGMENT-FORCED | 2.43 | deceptive (0.54) |
| A5 NOISE-TWIN GATE | 2.31 | deceptive (0.67) |
| A8 CROWDED-NAMES | 2.21 | deceptive (0.60) |
| A1 PURE-RANDOM | 2.04 | deceptive (0.64) |
| A4 COIN-GATE | 1.98 | deceptive (0.66) |

### 8.2 The seat's picks

- Most deceptive against the per-sleeve census: **A2 TIME-SHIFTED**
  (probability 0.63; next A7 at 0.16).
- Most deceptive against the Ghost Book surface: **A2 TIME-SHIFTED**
  (0.59; next A3 at 0.36).
- Most deceptive against family-level grading: **A7 MIRROR-CLONE**
  (0.98, near-unanimous).
- Pipeline artifact most likely to manufacture phantom edge:
  **imported_marks** (the one-session imported fill record, 0.28), then
  **unfed_exclusion** (0.25), then **cost_model** (0.17). Fill model 0.06,
  grading window 0.06, armed denominator 0.05, mirror twins 0.13.
- Best additional mechanism: **M1** (real fire timestamps, random exits,
  0.44), then **M2** (random entries, real exit logic, 0.33). M4 0.09,
  M5 0.09, M3 0.05.
- Predicates (probability the statement is true): a placebo family built
  from clones of one random stream would show breadth that changes a
  family verdict, **0.74**; the cohort's expectancy distribution will be
  centered at or below zero after modeled costs in its first quarter,
  **0.65**; at least one purely random placebo will show positive graded
  expectancy over its first 14-session window, **0.57**; the best placebo
  will grade above the real fleet's median sleeve in the first quarter,
  **0.55**.

### 8.3 How the generation input was used (selection stayed mechanical)

Cohort composition was fixed by the matching statistics of section 3
before the call: 8 archetypes x 3 hosts, because each archetype audits a
different named surface and dropping any one leaves a surface unaudited.
The seat's answers were used for exactly two things, both recorded here:
(1) **emphasis in the audit order of section 5.4**: the machinery audit
triggered by a top-decile placebo inspects imported marks and unfed
exclusion first, ahead of the fill model, reversing the order this
design's author would have chosen; (2) **the expansion queue**: M1 and M2
are registered as the cohort's first expansion archetypes (A9
TIMESTAMP-CLONE and A10 EXIT-INHERIT), to enter as new rows with derived
seeds at the cohort's first census, in that order, ahead of M4, M5, M3.
No archetype was dropped, added, or re-weighted on the seat's say-so. The
disagreement is preserved on the record: the seat rates A4 COIN-GATE the
least deceptive design in the cohort; A4 stays at full weight because it
is the only archetype that isolates gating itself, and the first census
will grade the seat's read against the realized distributions like any
other forecast in this estate.

## 9. What this design does not do

It does not build the placebo sleeves, touch desk code, edit any job
body, or price a single fire. It registers the cohort, fixes the seeds,
names the matching statistics and their sources, states the falsifiers,
and records the generation input. The build is a separate, dated step
for the desk lane and the book lane under section 7, graded by the same
register it feeds.

STATUS: GREEN for the seeding as scoped. Evidence pointers: this file
(design of record, seed registry in section 2); Trial Register rows 34 to
57 in `~/workspace/research_notes/consensus-lens-examination-20261114/TRIAL-REGISTER.md`
(appended with this design, change log entry dated 2026-11-15); generation
receipt `~/workspace/research_notes/alpha-hunt-chaos-20261115/PLACEBO-GENERATION-RECEIPT.json`
(Decisions API, bank placebo-fleet-generation v1.0, 17 questions, cost
$0.000482, pack hash in the receipt); matching-statistic sources:
`~/workspace/research_notes/alpha-hunt-chaos-20261115/LANE3-PRIVATE-DATA.md`,
`~/workspace/research_notes/sleeve-activation-calibration-20261111/execution_board.csv`
and `frequency.csv`, `~/workspace/midna-book/ghost-book-ledger.jsonl`,
`~/workspace/midna-book/ledger.json`. Open rows, named: the section 7
build (desk lane and book lane, undated at seed time; the mandate audit
carries it as a started item from this design), the A9/A10 expansion at
first census, and the first percentile print, which cannot exist before
the cohort's first full 14-session census window closes.
