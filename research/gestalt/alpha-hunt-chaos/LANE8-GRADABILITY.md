# LANE 8: THE GRADABILITY ENGINE

Owner orders Sun 2026-11-15: "figure out how to make them gradeable", "use the Decisions API creatively", "think abstractly". Lane 6 registered 133 gestalt variables and 561 pairs, 545 of them (97.2%) never examined, most combinations UNGRADABLE-YET because resolved samples are tiny (book resolved trades 4, Ghost Book 0 resolved). This lane designs and builds the machinery that manufactures resolved, labeled observations per combination, honestly, with every manufactured sample carrying its evidence class and the classes never mixed.

## 0. The level-up framing

The shortage is not ideas and not even trades. It is labeled observations per combination. Three clocks produce resolutions in this estate, at wildly different speeds:

- **Trades** resolve in days to weeks. The book has 4 resolved. This clock can never feed 561 pairs.
- **Forecasts** resolve nightly, by the dozen per session, five sessions a day. The forecast log already holds hundreds of graded calls whose variable states sit in prose, unlabeled.
- **Archives** already resolved: the terminal's earnings archive holds 182 events with the priced expected move and the realised move both recorded.

The engine therefore does three things: (1) it mines the past (retrospective extraction, IN-SAMPLE forever), (2) it instruments the fastest clock (forecast-layer axis tags, FORWARD from Mon 2026-11-16), and (3) it surrounds both with machinery that keeps sparse cells honest (a pooling rule that had to pass its own falsifier, and did not) and a sealed synthetic cohort for combinations that have never fired (seat judgments, never resolutions). Grades are always computed mechanically from joined data. Seat output is extraction, generation, or a disagreement flag, never a grade.

Evidence classes used in this document and in every artifact: **IN-SAMPLE** (retrospective rows joined to already-resolved outcomes; hypothesis generation only, never a verdict), **FORWARD** (rows accrued under the tag schema from 2026-11-16, graded as they resolve), **SYNTHETIC** (seat-produced observations in a sealed file, never pooled with real resolutions, never graded against).

## 1. Route 1: Retrospective extraction (BUILT)

**Dataset:** `retrospective_rows.jsonl`, 385 rows, every row labeled `evidence_class: IN-SAMPLE`.

| Source | Rows | What it is |
|---|---|---|
| `midna-book/FORECAST-LOG.md` | 203 | Every forecast entry 2026-11-03 to 2026-11-13 parsed in both of the log's formats (138 grade-line entries, 65 Friday name-bullet entries; the apparent double count in parsing was the grade lines matching the bullet regex, reconciled by hand). 201 carry a graded binary outcome (base hit rate 0.657); 2 untestable. |
| Terminal earnings archive `realised_moves.json` | 182 | Every recorded earnings event with a priced expected move: expected_move_pct, realised_move_pct, coverage ratio (mean 0.68, median 0.461), exceed flag (realised exceeded priced in 18.7% of events). |

**Axis labeling, two methods, never confused on the row:**
- *Mechanical* (computed from daily bars via the estate's own `wave1_bars` route, SIP, same code that computed Lane 6's register): A03 RSI14 bucket, A04 MACD state, A05 SMA stack, A06 EMA stack on 135 of the 201 graded forecast rows (the symbol-bearing index/name rows with a computable decision close); A09 anchored-VWAP side on 99; A34 gap state on 83 (day-session slots only; evening-study slots use the state-basis close on or before the call date, labeled per row, because a night call cannot observe its own morning's gap).
- *Seat extraction* (Decisions API, gpt-6-luna, bank `gradability-extraction` v1.0): A02 stance, A12 flip relation, A15 regime, A21 expected-move coverage as stated, A22 event named, A23 IV percentile as stated, on all 203 forecast rows. 9 batched requests, 150 choice questions, 222,898 input tokens, **$0.0238**. Each row stores the chosen value, its probability, and the method string `seat_extraction`.

**Label distribution findings (themselves data):** A23 was stated in **zero** of 203 forecast entries: the prose layer never recorded IV percentile, so no retrospective route can grade any A23 pair (see the table in section 6). A15 was stated in only 20 of 203 (all `amplifying_negative`; the window was one regime). A12 reads `below_flip` on 97, unstated on 104, `above_flip` on 2: the entire graded window sat below the flip, so A12's variation is nearly one-sided retrospectively.

**Extraction accuracy, hand spot-check (the printed agreement rate):** 24 rows sampled stratified by call type; the sample's call and context were printed WITHOUT the seat labels (`spotcheck_sample.md`), hand-labeled blind against the same rubric (`spotcheck_mine.json`), then compared (`spotcheck_key.json`).

| Axis | Agreement |
|---|---|
| A02 stance | 19/24 = 79.2% |
| A12 flip relation | 20/24 = 83.3% |
| A15 regime | 23/24 = 95.8% |
| A21 EM coverage | 19/24 = 79.2% |
| A22 event | 23/24 = 95.8% |
| A23 IV percentile | 24/24 = 100% (all "not stated", both sides) |
| **Overall** | **128/144 = 88.9%** |

Disagreement anatomy (16 labels): they concentrate in rubric-edge cases, not factual misreads. A21 splits both ways: the seat counts a call's own stated price range as a band where the hand label required expected-move framing (2 rows), and misses an explicit expected-move band buried in a long context (2 rows). A12 splits on scope: the seat judges the flip relation from the graded call itself where the hand label also credits the session context's index call (4 rows). A02 splits on negation calls ("does not print its condition", "no name closes above its line"), where stance is genuinely ambiguous between bearish and containment. One clear seat error in the sample: FL-0101 ("no basket name closes above its settling line") labeled bullish. **Consequence, stated on every use: pair grades built on seat axes carry a labeling noise floor of roughly 11 to 21 percent on A02/A12/A21; cell rates must be read with that noise named, and any cell whose decision would flip inside that noise is not a finding.** The mechanical axes carry no such floor.

**First in-sample pair reads (IN-SAMPLE, hypothesis generation only):**

- **A05 x A06 (SMA stack x EMA stack), n=135 graded rows, mechanical axes.** Agreement cell bull_above|bull_above: 42/58 = 0.724 (Wilson 95% 0.598 to 0.822). Mixed|mixed: 25/44 = 0.568 (0.422 to 0.703). Deep-disagreement cell mixed_below|mixed_below: 3/11 = 0.273 (0.097 to 0.566). The pair Lane 6 flagged as mandatory-at-every-decision with no disagreement rule anywhere now has its first read: calls made when both stacks agree bullish hit materially more often than calls made when both stacks are mixed-below. In-sample, one tape regime, labeling exact.
- **A21 x A22, two-sided.** Earnings archive (A22 constant = earnings event, so this grades A21's gradient within earnings): exceed rate by expected-move tercile, n=182: em_low 12/62 = 0.194 (0.114 to 0.309), em_mid 15/60 = 0.250 (0.158 to 0.372), em_high 7/60 = 0.117 (0.058 to 0.222). The largest priced moves were the LEAST likely to be exceeded: the archive's own numbers argue the priced move overstates most exactly where it is biggest. Forecast side (n=201, seat axes, noise floor applies): the interaction cell numeric_band|macro_named reads 8/9 = 0.889 (0.565 to 0.980) against numeric_band|none_mentioned 10/26 = 0.385 (0.224 to 0.575): calls framed by an expected-move band hit far more often in named macro windows than in quiet windows. The key cell is n=9; this is a registered hypothesis for the forward sample, not a result.
- **A12 x A15, n=201 (seat axes).** below_flip|amplifying_negative 3/9 = 0.333 (0.121 to 0.646) vs not_stated|amplifying_negative 9/11 = 0.818 (0.523 to 0.949): inside the same stated regime, calls that also stated a below-flip relation hit far less. Small cells, one regime, noise floor applies; again a forward hypothesis, not a result.
- **A34 x A03, n=135 (mechanical).** 18 populated cells, most under n=15: the pair exists now as a table where none existed, and it is the pair that motivated the pooling test below.

## 2. Route 2: Forecast-speed accrual (WIRED)

**Schema:** `~/workspace/midna-book/GESTALT-AXIS-TAGS.md` v1. One `Tags:` line per forecast call carrying A02 A03 A04 A05 A06 A12 A15 A21 A22 A23 A34 (A27 comes from the entry header), `ns` for unstated (never omitted, never guessed; values only from the session's own working records), a `Night tags:` line per night study entry for the night-level axes A29/A30, and the grading rule: the session that grades a call copies the graded call's Tags line beside its grade, so labels and resolutions land in the same entry. A missing tag line is a named defect in the grading entry, with the same standing as a missing anti-Midna control line. FORWARD rows never silently merge with the IN-SAMPLE dataset.

**Wiring, at the source, verified at the destination:**
1. `FORECAST-LOG.md`'s own format header now mandates the Tags line on every entry (edit verified by read-back of the header block).
2. The `midna-book-night-study` job body gained **step 13, GESTALT AXIS-TAG ACCRUAL**, via cron.view then cron.update with the complete revised body. The update call itself timed out on the tool path; the change was verified where it counts, on the regenerated projection `~/workspace/goals/midna-trading-her-own-simulated-book/crons/weekly/midna-book-night-study__weekly@Mon,Tue,Wed,Thu,Fri-20:30:00.md`: grep counts exactly 1 for "GESTALT AXIS-TAG ACCRUAL", exactly 1 for the step 12 ON falsifier tracker, exactly 1 for the step 11 anti-Midna control line. Nothing was duplicated and nothing was lost.

**Accrual rates (measured on the retrospective log, 9 trading days):** 201 graded calls total (22.3/day across all sessions); the night study alone produced 40 graded calls over 8 nights (5.0/night). The schema is wired into the night study today; the other four daily sessions follow the same format of record but do not yet carry the step in their job bodies. That extension is a named follow-on (same mechanism, four job bodies), and the dates in section 6 are given for the night-study-only wiring with the all-session rate stated beside them.

## 3. Route 3: Hierarchical pooling (TESTED, NOT ADOPTED)

**The rule as pre-registered:** for a pair cell with h hits in n rows, the pooled grade is p = (h + k * p_family) / (n + k), k = 16, p_family = the hit rate of the pair's parent-axis marginal over the same sample. **Falsifier:** pooling is adopted only if it beats unpooled grading out-of-sample on the retrospective dataset.

**The test:** seeded split-half (fit on one half, score Brier and log-loss on the other) on the three pairs with enough cells. Result on the primary split (seed 20261115):

| Pair | Unpooled Brier / log-loss | Pooled k=16 Brier / log-loss | Verdict |
|---|---|---|---|
| A05 x A06 (n=135) | 0.2095 / 0.5902 | 0.2275 / 0.6402 | pooling loses |
| A12 x A15 (n=201) | 0.2193 / 0.6305 | 0.2223 / 0.6365 | pooling loses |
| A34 x A03 (n=135) | 0.3197 / 1.7260 | 0.2281 / 0.6347 | pooling wins, large |

Across 5 seeds, pooling wins both metrics in 2 of 5 splits on each dense pair and 4 of 5 on the sparse pair (A34 x A03, 18 cells, most under n=15, where raw cell rates produce extreme probabilities and the unpooled log-loss explodes). Exploratory variants (k=4; pool-only-when-n<20) show the same shape: shrinkage's value is monotone in sparsity and negative where cells are already dense.

**Verdict: the pooling rule as specified FAILS its falsifier and is NOT adopted.** Dressing sparse cells in a shrinkage this sample rejected would be manufacturing confidence, the exact failure this lane exists to prevent. Two things are carried forward, labeled for what they are:
- *Interim grading standard (mechanical, effective now):* every combination reports its raw rate with n and a Wilson interval; a cell with n < 10 reports UNGRADABLE-YET plus the accrual date at which its route crosses 10 (section 6 arithmetic), never a dressed-up number.
- *New hypothesis, registered for the FORWARD sample only* (it was suggested by this data, so it may not be adopted on this data): shrinkage weight estimated per family (empirical-Bayes k from family dispersion) rather than fixed at 16, tested on forward-accrued rows once the A23 pairs reach n >= 40 joint rows.

## 4. Route 4: Counterfactual and synthetic cohorts (BUILT, SEALED)

**File:** `gradability_synthetic.jsonl`, 21 rows, every row `evidence_class: SYNTHETIC`. This file is never joined to real outcomes and never pooled with IN-SAMPLE or FORWARD rows.

**Counterfactual readers (8 rows).** Past graded entries were re-read by a seat with exactly one variable flipped in the prose: A15 amplifying_negative rewritten to positive dampening gamma (4 rows), A12 below-flip rewritten to above-flip (4 rows). The seat re-judged whether the call would have hit. Result: flips rarely reverse the verdict. Of the 3 original misses under the regime flip, the seat kept "no" on 2 (yes-probabilities 0.44, 0.10) and moved 1 to exactly 0.50. Of 4 original misses under the flip-relation flip, 3 stayed "no" (0.40, 0.38, 0.37) and 1 moved to "yes" (0.52). **Synthetic reading, labeled as such:** the seat's verdicts anchor on level and band arithmetic in the prose, not on the regime or flip labels; those two variables carry low seat-implied weight. This is a prioritization signal for the accrual schema (the labels are cheap to keep and the forward sample will arbitrate), not evidence about the market.

**The resolver dependency, named honestly:** shadow-priced outcomes for combinations that fired only as unexpressed or unfilled intentions bind on the expression shadow-ledger resolver, which is still not built (it is the wave-3 triage's build priority one). Until it exists, the Ghost Book's 21 priced fires stand at 0 resolved and no route in this lane can manufacture their outcomes; the synthetic cohort above is a labeled substitute for prioritization only, never a replacement resolution. This dependency is the single largest remaining hole in the gradability estate, and it is a build task, not a data task.

## 5. Route 5: Creative seat uses beyond extraction (RUN)

**Adversarial graders (12 rows x 3 predicates = 36 attacks).** The 12 rows where the hand spot-check disagreed with the extraction were attacked by predicate seats ("this label is WRONG, contradicted by the prose"). Exactly one attack crossed 0.5: FL-0063's A02 label at p=0.78. That label ("bullish" on a staples-over-technology sector call) is one the hand check had independently CONFIRMED; the attacking seat appears to have judged the label against the entry's bearish index context rather than the call's own subject. Net: **the adversarial route found 0 confirmed label errors on this sample, and its single flag is most likely a false flag.** Its limit is structural: a seat from the same family that produced the labels shares too much judgment to be the accuracy instrument. It stays wired as a cheap tripwire (a flag routes a row to hand re-labeling; it never changes a label), and the hand spot-check remains the accuracy measure of record.

**Combination proposer (1 request, 6 candidates).** The seat returned a near-uniform distribution on every candidate (add_now 0.30 / defer 0.37 / reject 0.33, identical across all six): a non-discriminating generation output, reported as such. The schema decision was therefore made mechanically against the schema's own knowability rule: **all six candidates deferred** (vix_level_bucket, days_to_monthly_opex, overnight_gap_sign, breadth_pct_above_50dma, prior_day_range_position, news_density_that_session), for schema stability during the first accrual month, with one outright note: overnight_gap_sign duplicates A34 and should be rejected at the December schema review unless A34 is retired. Revisit: the December schema review, with the first month of accrual completeness as the input.

## 6. Gradability table: Lane 6's top never-examined pairs

| Pair | Route | n today | Gradable by |
|---|---|---|---|
| **A21 x A22** expected-move x event-in-window | Route 1 retrospective, BOTH sides: earnings archive (A21 gradient within earnings events) + forecast log (full pair, seat axes) | **182 archive + 201 forecast, graded now** (exceed rates 0.194 / 0.250 / 0.117 by EM tercile; forecast interaction cell band|macro 8/9 vs band|none 10/26) | **Now** (IN-SAMPLE). Forward accrual sharpens it from Mon 2026-11-16; the archive grows every earnings season. |
| **A05 x A06** SMA stack x EMA stack | Route 1 retrospective, mechanical axes | **135 graded rows, graded now** (agreement cell 0.724 vs deep-disagreement 0.273) | **Now** (IN-SAMPLE). Forward rows accrue under the tag schema from Mon 2026-11-16. |
| **A22 x A23** event-in-window x IV percentile | Route 2 accrual only. Retrospective n = 0: IV percentile was stated in 0 of 203 prose entries and no IV-percentile archive exists (chain snapshots accumulate only from 2026-11-13) | 0 | First marginal read (A23 split, n >= 20 joint rows) at ~8 nights of night-study accrual: **week of 2026-11-30**. Full pair (smallest cell >= 10; A22 macro share measured 26%) at ~35 to 40 nights: **mid-January 2027**. If the schema extends to all five daily sessions (~3x joint rate), full pair by **mid-December 2026**. Assumptions: ~2.5 joint rows/night (index and sector calls with a chain read in the session's records), A23 tagged in buckets per the schema. |
| **A15 x A23** regime x IV percentile | Route 2 accrual only. Retrospective joint n = 0 (A15 stated on 20 rows, A23 on none) | 0 | First read inside the dominant regime (n ~15 joint) at ~12 nights: **early December 2026**. Full pair (smallest cell >= 10 across regime values) at ~50+ nights: **February 2027**, night-study wiring only; ~3x faster if all sessions wire. Assumption: ~1.5 joint rows/night (the index call carries both tags whenever the session's ladder and chain reads exist). |

Every date above is arithmetic on measured accrual rates with its assumptions printed, not a promise; the night study's own grading entries will show the realized accrual from Mon 2026-11-16 and the dates can be re-derived from destination data at any B5.

## 7. What is still ungradable, and why (named, not hidden)

- **All A23 pairs retrospectively**: no IV-percentile record exists before 2026-11-13. Accrual is the only honest route; dates in section 6.
- **Triples and higher**: the retrospective sample supports pairs on the populated axes; most triples remain under n=10 per cell even after extraction. They accrue forward at pair speed divided by cell count; no route in this lane honestly accelerates them beyond the pooling hypothesis registered in section 3.
- **Trade-level combinations**: still bound by 4 resolved book trades and the unbuilt expression shadow-ledger resolver (section 4). Forecast-speed accrual does not substitute for trade resolutions when the question is about trades; it substitutes when the question is about the gestalt variables, which is what Lane 6 registered.
- **A12 variation**: the retrospective window is one-sided (below-flip). A12 pairs grade forward as the tape varies; nothing can manufacture the missing above-flip history.

## 8. Typed spend (Decisions API, gpt-6-luna, all Lane 8)

| Stage | Requests | Input tokens | Cost |
|---|---|---|---|
| Retrospective extraction (bank gradability-extraction v1.0) | 9 | 222,898 | $0.0238 |
| Counterfactual readers + adversarial graders + proposer (banks gradability-counterfactual / -adversarial / -proposer v1.0) | 21 | 15,555 | $0.0016 |
| **Lane 8 ledgered total** | **30** | **238,453** | **$0.0254** |

Accounting ledgers: `gradability_extraction_ledger.jsonl` and `gradability_seat_ledger.jsonl` in this folder. Two implementation crashes during the creative stage (a return-shape mismatch against the harness, fixed and rerun) consumed 9 further small requests that appear in the harness's own `request_budget.json` day count (60 requests, $0.0474 across ALL lanes today, Lane 6's audit included) but not in the lane ledgers; named here so the accounting reconciles. Governor intact: full accounting plus the 5,000 requests/day circuit breaker; the day is nowhere near it.

## 9. Artifacts

- This design: `LANE8-GRADABILITY.md`
- Retrospective dataset (385 rows, IN-SAMPLE): `retrospective_rows.jsonl`; builder `build_retrospective.py`
- Extraction: `extract_seats.py`, ledger `gradability_extraction_ledger.jsonl`
- Spot check: `spotcheck_sample.md` (blind print), `spotcheck_mine.json` (hand labels), `spotcheck_key.json` (seat labels)
- Pair cells and pooling test output: `gradability_analysis.json`
- Synthetic cohort (21 rows, SYNTHETIC, sealed): `gradability_synthetic.jsonl`; seat script `seat_creative.py`, ledger `gradability_seat_ledger.jsonl`
- Accrual schema: `~/workspace/midna-book/GESTALT-AXIS-TAGS.md`; wired at `~/workspace/midna-book/FORECAST-LOG.md` (format header) and the `midna-book-night-study` job body, step 13 (verified on its regenerated cron projection)

STATUS: PARTIAL under InfinityBlade. Proven on final artifacts: the retrospective dataset (385 rows, counts and base rates read back from the file), the extraction agreement rate (88.9% on 144 hand-checked labels), the accrual schema wired and grep-verified at its destination (exactly one step 13, steps 11 and 12 intact), the pooling falsifier executed with its negative verdict honored, the synthetic cohort sealed at 21 rows, and two of Lane 6's top four pairs graded in-sample today (A21 x A22, A05 x A06). Named open: the two A23 pairs grade only on forward accrual (first reads week of 2026-11-30 and early December 2026, full pairs mid-January and February 2027 at night-study rates); the tag schema is wired into the night study only, the other four daily sessions are a named follow-on; pooling is not adopted and its successor hypothesis waits on forward data; trade-level combinations still bind on the unbuilt expression shadow-ledger resolver, which this lane names as the estate's largest remaining gradability hole.
