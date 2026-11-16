# THE NEAR-MISS PORTFOLIO + MUTATION CAMPAIGN 2

Owner order Sun 2026-11-15 18:26 ET: explore the unexplored areas with
extreme rigor, Tier A standard. This lane covers two of them: the
near-miss portfolio (Lane 3's unmeasurable object) and Mutation
Campaign 2 (Lane 2's second run, its falsifier standing at one barren
campaign of two). All work read-only on the desk tree; every count below
was recounted from the registers named at the end.

## POTENTIAL EDGE FOUND

**Lead 1, the near-miss set itself, recovered and armed forward.** The
trades the desk almost took are not lost: 344 of 1,057 historical entry
near-misses reconstruct exactly from the estate's own records (routes
and proof in Part 1), and the standing shadow machinery that grades
every future near-miss from Mon 2026-11-16 is built, tested (14 of 14),
and smoke-proven on today's 150 stamped records (Part 3). The historical
grade of the recovered set does not separate from the taken portfolio
(Part 2); the edge claim here is the instrument and the recovered
denominator, not a return. Cheapest forward check: the shadow book's
own first read at 20 forward sessions, H-A graded there at a power the
historical record structurally cannot give.

**Lead 2, avoidance-side corroboration: the dmac taken stream on
contract closes.** The three investandbefree_dmac variants' recorded
contract entries grade fwd1 at a daily mean of -3,274.62bp (t -1.889,
5 dates, 1,009 events, win rate 0.135) on their own contract bars,
contract basis, never pooled with equity. This is the taken side of the
lane, printed because Campaign 2's children kept re-deriving it (the
cohort's strongest |t| is a dmac contract stream at -6,878.30bp/day,
t -3.167, 3 days). It corroborates the KG-12 DMAC pole at its own
basis; it is not a new tradeable object, and its inversion does not
separate on the ShortSide clustered read (t 0.83). Its near-miss side,
87 stamped contract rows dated today, grades forward under Lead 1's
machinery.

**Lead 3, Campaign 2's best positive cells, at true strength, none
promoted.** MUT-87f9d71a0b87 (rsi_meanrev_options, EXIT_ENTRY_SWAP on
its exit stream): +446.94bp/day, t 2.836, 17 events, 3 days, q 0.625,
DSR 0.2488. MUT-bc0cb92623e1 (s_mn_macd, HOLD_INVERT): +561.08bp/day,
t 1.953, 174 events, 3 days, q 0.625, DSR 0.0646. MUT-f71c6831f4d3
(momentum, SESSION_SHIFT + EXIT_ENTRY_SWAP): +524.98bp/day, t 1.605,
65 events, 6 days, q 0.625, DSR 0.0. Every one fails the sealed bar
(q at most 0.10, t at least 3, DSR at least 0.95) by an order of
magnitude. They are printed because a funnel that only prints its
survivors hides its noise ceiling; these are the noise ceiling.

**The structural find (autopsied as method-ledger entry 19).** The
estate's historical screens all share the same 14 recorded entry dates.
Generation was never the constraint: Campaign 2 scored 23 candidates
where Campaign 1 scored 2, at effective N 1,083.8, and still nothing
approached the bar, because 3-to-10-day samples cannot carry a
deflated-Sharpe verdict. The registered consequence is in Part 4.

## Part 1: Near-miss reconstruction

Population: every dispatcher intent_rejected row with reason
insufficient_slice_bp across all five rotated logs: **1,057 rows**
(Lane 3's 773 was the then-current file; the rotations hold 29,708
rejections in total). Reconstruction routes, exact or refused:

| Route | Rows | Proof |
|---|---|---|
| STAMPED | 150 | the record itself carries symbol, side, ref_price (the 2026-11-15 cure, desk commit 87a3956): SPY 42, QQQ 21, SPY261218P00754000 87, all side buy, all dated 2026-11-15 |
| INTENT_ID_SUFFIX | 27 | aster_tensor_h1_recovery suffixes the symbol in the intent_id; every suffix validated against the bar census |
| UNIT_WEIGHT_SOURCE | 167 | the sleeve's SPECS entry in desk3 source (AST-parsed, never imported) carries weights of exactly {SYM: 1.0}; 10 sleeves validated against their stamped rows and recorded entry fills with zero contradictions (the four SPY/QQQ monthly sleeves carry this lane's rows) |
| NOT_RECONSTRUCTED | 713 | dmac variants 579 (two underlyings, OCC contract selection unrecorded pre-cure); aster_etf_leader1_m150 105 (LEADER1 basket rotation, the argmax choice unrecorded); leaps_momentum 7, t_cci_corr 5, core25 pair 8, bta pair 5, drift1 2, btc_eth_sma200 2 (multi-symbol or short universes, symbol unrecorded) |

**Coverage: 344 of 1,057 reconstructed, 32.5 percent**, printed per
sleeve in NEARMISS-REGISTER.jsonl (1,058 lines: 1 census row + 1,057
near-miss rows, each carrying its route or its refusal reason).

Routes examined and refused, in print: the journal last_evaluation join
(its blocked field names the symbols sizing blocked, not the instrument
the intent carried); snapshot replay (the cycle snapshot store holds 8
files, 3 complete, recent cycles only); inference from a sleeve's fills
on the rejection day (a fill proves what was taken, never what was
refused).

Entry prices: ref_price where stamped; otherwise the last close on or
before the intent date (weekend intents price at Friday's close, the
last close the desk itself could see; labeled CLOSE_PROXY in the
register, with the intent date preserved beside the bar date).

Gradeability, the number that governs Part 2: of the 344 reconstructed
rows, **288 are dated at or beyond the bar span's edge** (bars end
2026-11-13; the near-miss mass concentrates in the 2026-11-13/14/15
sessions), leaving **56 gradeable events on 5 dates (2026-11-02 to
2026-11-06), 10 distinct (date, symbol) signals**, all from the four
monthly sleeves and their unit-weight rows. The stamped equity rows
(63) and the h1_recovery suffix rows (27) are reconstructed but not yet
gradeable; they grade when the cache extends, and from Monday the
forward machinery takes over.

## Part 2: The reconstructed near-miss portfolio, graded against the taken

Identical windows and rules for both portfolios (the Campaign 1
intermediate-outcome convention): forward return from entry to the
close 1 and 5 trading days later on stored daily bars, net of the 6bp
exit haircut, minus QQQ close-to-close over the same window; events
aggregated to entry-date means; date-clustered t. Benchmark of record
QQQ (the Campaign 1 amendment stands).

| Portfolio | Basis | fwd1 daily mean | t | fwd5 daily mean | t | Events / days (fwd1) |
|---|---|---|---|---|---|---|
| Near-miss equity (reconstructed) | close proxy (gradeable core) | +1.09bp | 0.035 | -49.10bp | -1.283 | 56 / 5 |
| Taken equity | fill price | +79.93bp | 0.572 | +542.86bp | 1.180 | 5,648 / 12 |
| Taken equity | close | +118.20bp | 0.810 | +686.18bp | 1.441 | 5,648 / 12 |
| Taken, all fills incl. contracts | fill price | -487.64bp | -1.088 | +352.94bp | 0.632 | 6,657 / 12 |

The all-fills row is printed with its warning: contract fills priced on
contract closes dominate it (the KG-4 contamination), which is why the
head-to-head runs on the equity subsets only.

**Head-to-head (H-A), fwd5, close basis both sides, 5 shared dates:**
mean difference -242.39bp, t -0.679. No separation in either direction.
Per-sleeve near-miss fwd5 reads: aster_etf_spy_monthly_m150 -99.91bp
(t -1.258, 26 events, 5 days); the two QQQ monthly sleeves print exactly
-6.00bp every day (a QQQ buy graded against QQQ nets the haircut by
construction; degenerate zero variance, t reported as 0, the cell named
mechanical, not evidence); aster_etf_spy_monthly_c098 rests on 1
gradeable event. Neither portfolio separates from zero on its own
either (every |t| above is under 1.5).

**H-A verdict:** untested at power, not falsified and not supported.
The historical record cannot test it: the near-miss population exists
in size only in the final three sessions, where forward bars do not
exist yet. This is Lane 3's conclusion with its ceiling now measured
exactly (56 events, 5 dates, 10 signals), and it is why Part 3 exists.

Contract class, kept apart: the 87 stamped dmac near-miss rows are
dated 2026-11-15 and grade zero forward windows today
(WINDOW_INCOMPLETE, the correct state). The taken dmac contract stream
grades in Lead 2 above (fwd5: daily mean -1,826.75bp, t -0.778, 3 days,
581 events).

## Part 3: The forward instrument (built, tested, smoke-proven)

Deliverables in ~/workspace/midna-book/tools/:
nearmiss_shadow.py (ingest + grade CLI), NEARMISS-SHADOW-SPEC.md,
test_nearmiss_shadow.py (14 tests, all passing).

- Ingest: reads all dispatcher rotations, selects intent_rejected rows
  with reason insufficient_slice_bp and symbol/side/ref_price stamped,
  appends each once per intent_id to the shadow ledger with the
  sleeve's exit profile frozen from the PASS2-C register.
- Grade: a complete registered profile (stop, target, horizon) resolves
  close-based first-touch; otherwise the row resolves once as
  FALLBACK_MARKS carrying +1 and +5 session marks. Returns are
  direction-signed, net of the 6bp haircut, excess versus QQQ over the
  same window. OCC rows grade on their own contract bars, labeled
  contract basis, never pooled with equity. Unresolvable rows stay OPEN
  with NO_BARS or WINDOW_INCOMPLETE named. Reruns are idempotent;
  originals are never edited.
- Spec's named limits, on its face: only 1 of 339 register sleeves
  carries a complete exit-profile triple and only 61 carry any
  exit_params field, so the fallback governs most rows; no size is
  stamped on a rejection, so the shadow book is equal-count, never
  capital-weighted; ref_price is the dispatcher's own price at
  rejection, not a fill.
- Smoke run (scratch output only, production ledger untouched and
  still nonexistent): 67,683 dispatcher records read, exactly 150
  selected and ingested (63 equity, 87 OCC; the six sleeves at 29/29/29/
  21/21/21), rerun added 0, grade produced 0 resolutions and 150 OPEN,
  every one WINDOW_INCOMPLETE, which is correct: no forward session
  after Sun 2026-11-15 exists yet. First production rows land with
  Monday's session under the spec; the nightly cadence is described in
  the spec, no cron was created by this lane.

## Part 4: Mutation Campaign 2

Registration: seed **20261118**, printed in the generator and in this
lane's brief before generation. Nominal 1,500 candidates (Campaign 1:
1,200). Generation amendments, recorded in the register header:
parent coverage guarantee (the first draws are one per parent) and the
family cap scaled to 375 of 1,500 (the same 25 percent). One
header_correction record is appended to the register: at generation
time the roster held **358 parents**, not 339, because the 19
registered variations were rostered into sleeves.json earlier today;
the guarantee drew all 358 distinct parents, 85 with extracted source
constants. Operator usage across 2,673 applications covers all 16
operators; 908 of 1,500 candidates landed in novelty cells empty in the
parent fleet, across 222 distinct cells; 56 byte-duplicates within the
campaign and 88 candidates also present in Campaign 1's register
(report only; a new campaign is a new trial set).

The funnel, stage by stage (denominators printed):

- Stage 1, mechanical: 155 pass, 1,345 fail: no_parent_event_stream
  985, near_miss_set_empty_for_parent 190, expression_not_priceable_on_
  stored_history 114, byte_duplicate_within_campaign 56.
- Stage 2, historical: SCORED 23, INSUFFICIENT 62, ENGINE_REQUIRED 69,
  DATA_FAIL 1 (breadth gate, series not stored).
- Survivors: **zero.** Best q in the cohort 0.625 (bar 0.10); best DSR
  0.2488 (bar 0.95); the only |t| above 3 is negative (a dmac contract
  stream, Lead 2). Campaign effective N 1,083.8 (sibling rho measured
  where scored siblings exist, 0.5 default elsewhere). PBO NOT
  COMPUTED: the CSCV-lite gate (at least 10 scored candidates carrying
  block means in at least 6 of 8 calendar blocks) was not met; the 23
  scored candidates span 3 to 10 entry dates each. Peek budget: 1, the
  scheduled cohort close read, logged in the register.

Family funnel (generated / Stage 1 pass / scored): adapters3 375 / 36 /
11; desk3 375 / 41 / 4; adapters 205 / 41 / 5; aster_sleeves 183 / 0 /
0 (its parents still hold no recorded dispatcher entry stream);
laz_sleeves 180 / 7 / 0; red_day_reversal 18 / 15 / 2;
rsi_meanrev_options 15 / 1 / 1; rsi_meanrev 15 / 12 / 0; the remaining
families scored 0. Coverage comparison against Campaign 1: scored
candidates 2 to 23, priceable share of the entry record transformed by
the widened cache (151 symbol dirs against 49 usable daily series), and
aster_sleeves remains the standing coverage hole, now the largest one.

**The NEARMISS_FLIP arm, counted exactly:** 212 candidates carried the
operator. 190 failed Stage 1 closed (parent holds no reconstructed
near-miss events; only 9 of 358 sleeves hold any), 13 were
byte-duplicates, 7 carried an unpriceable expression. Exactly 2 reached
an event-holding parent: MUT-e883d6ddf83e (aster_etf_spy_monthly_m150,
NEARMISS_FLIP + ESTIMATOR_SWAP; Stage 1 PASS on a 26-event near-miss
stream, then ENGINE_REQUIRED because the co-operator changes signal
generation; the pure stream's own grade is Part 2's -99.91bp read) and
MUT-a3a1818ea759 (investandbefree_dmac, NEARMISS_FLIP + SESSION_SHIFT;
29 contract near-misses, 0 scoreable forward windows, INSUFFICIENT).
GATE_DROP, restored by the same set: 158 candidates, 3 scored, all on
fill-dominated streams; the restored near-misses added no scoreable
event in the window.

**Campaign verdict and the falsifier.** Zero survivors is the funnel's
printed outcome, accepted as specified. Lane 2 Section 9's campaign
falsifier, registered before Campaign 1 ran: two consecutive campaigns
with no cohort clearing the bar demote the mutation premise. That count
now stands at two. **The mutation premise is therefore demoted as a
historical screen, and per the same registered text the multiplication
moves to resolution throughput**: forward accrual on the cured intent
records, the near-miss shadow book of Part 3, and the resolver class of
instruments, which manufacture the forward windows stored history does
not contain. The 1,477 unscored candidates are unmeasured, not failed;
their register rows carry their reasons, and nothing in this verdict
reaches the sleeves, the parents, or the forward shadow stage, which
was always a separate premise with its own falsifiers.

## Registers and code

- NEARMISS-REGISTER.jsonl: 1,058 lines (1 census + 1,057 near-miss
  rows), nearmiss_reconstruct.py.
- CAMPAIGN2-REGISTER.jsonl: 3,004 lines (1 header + 1 header_correction
  + 1,500 candidates + 1,500 evaluations + 1 peek + 1 cohort summary),
  campaign2_generate.py and campaign2_evaluate.py (the sealed funnel,
  Campaign 1's rules verbatim; deltas pre-registered in its header).
- Forward machinery: ~/workspace/midna-book/tools/nearmiss_shadow.py,
  NEARMISS-SHADOW-SPEC.md, test_nearmiss_shadow.py.
- Method autopsy: EDGE-FIND-METHOD-LEDGER.md entry 19, with geology
  row 19 and three negative-ledger bullets (the NEARMISS_FLIP
  historical arm, the second barren campaign, the refused inexact
  reconstruction routes).

STATUS: PARTIAL. Proven on the final artifacts: the reconstruction
census and grades recounted from NEARMISS-REGISTER.jsonl (344 of 1,057
reconstructed, 32.5 percent coverage, every unreconstructed row carrying
its reason); the forward machinery GREEN on its own tests (14 of 14)
and smoke run (150 of 150 ingested, all correctly OPEN); Campaign 2's
complete funnel recounted from CAMPAIGN2-REGISTER.jsonl (1,500
registered, 1,500 evaluated, 23 scored, 0 survivors, effective N
1,083.8). Named open rows, none of them silent: H-A grades at power
only on the forward shadow book from Mon 2026-11-16; the 288
span-edge reconstructed rows grade as the cache extends; PBO remains
uncomputed under its printed gate; the campaign falsifier's demotion
is recorded above and takes effect on the premise, with resolution
throughput as its registered successor.
