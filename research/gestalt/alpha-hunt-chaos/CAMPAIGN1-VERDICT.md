# MUTATION CAMPAIGN 1, VERDICT

The first real evaluation run of the Chaos Lab's mutation engine (Lane 2
design and prototype: LANE2-MUTATION-ENGINE.md). Owner order Sun
2026-11-15: go further and deeper. Generation, registration, and the
sealed funnel ran exactly as Lane 2 specified. No trading; the desk tree
was read only.

## The headline, with its denominator

1,200 candidates were generated and registered as trials (seed 20261116,
recorded in the register header before generation). Every one of the
1,200 received a funnel disposition. **Two candidates (0.17 percent)
could be scored on the estate's stored history. Neither scored anywhere
near the bar. Survivors: zero.** The campaign's binding constraint is
not candidate quality and not compute; it is evaluation coverage, the
exact bottleneck Lane 2 Section 8 named in advance, now measured.

## The funnel, stage by stage (cohort level, denominators printed)

Stage 0, Register: 1,200 candidates, trial indices 1 to 1,200, from 248
distinct parents of the desk 339 (84 constants-extracted parents mutated
on constants, adapter-seam parents mutated structurally). 2,089 operator
applications across the 16 operators. 718 of 1,200 landed in novelty
cells empty in the parent fleet, across 193 distinct cells.

Stage 1, Mechanical screen (reads no performance data): 122 pass,
1,078 fail, every fail registered with its reason:

- 691 no_parent_event_stream: the parent sleeve has no recorded entry or
  exit fills in the dispatcher record at all. The fleet's recorded firing
  history lives in 42 of 339 sleeves.
- 154 near_miss_feed_has_no_symbol_side_price: NEARMISS_FLIP candidates.
  The historical rejection log (29,487 rows) carries sleeve, reason, and
  intent id, but no symbol, side, or price, so the near-miss set cannot
  be priced. Failed closed per Lane 2 Section 8, never invented.
- 104 expression_not_priceable_on_stored_history: options expressions;
  the stored chain archive reaches back only to 2026-11-13.
- 94 gate_blocked_set_unpriceable: GATE_DROP candidates; the fires a
  dropped gate would restore are the same unpriceable rejection set.
- 35 byte_duplicate_within_campaign (0 duplicate the prototype).

Stage 2, Historical screen: of the 122 who passed Stage 1:

- 57 ENGINE_REQUIRED: a signal-generation operator (DROP_VARIABLE,
  PARAM_JITTER, PARAM_EXTREME, ESTIMATOR_SWAP, TIMEFRAME_SHIFT) changes
  what the parent fires, so the recorded event stream cannot grade it.
  Grading these needs the parent engines re-run per candidate, the
  throughput Lane 2 named as the estate's bottleneck. Registered,
  counted, never proxy-graded.
- 4 DATA_FAIL: UNIVERSE_SWAP to inverse_of_parent (3) or
  random_50_sp500 (1) names a foreign universe with no parent stream;
  no breadth-gate candidate reached this stage.
- 59 INSUFFICIENT: evaluable transforms whose scored events fell below
  the pre-registered minimum (10 events on 3 distinct entry dates).
- 2 SCORED.

## Why so few could be scored: the coverage census

The dispatcher record holds 6,708 entry fills (buy_to_open / sell_to_open)
across 14 dates, 2026-10-27 to 2026-11-13. Stored daily bars cover 49
symbols. Only **613 of 6,708 entry events (9.1 percent)** sit in
bar-covered symbols, spanning 29 sleeves, and the covered events are
concentrated in a few imported sessions: s_mn_macd's 172 covered events
fall on a single date (2026-10-27), red_day_reversal's 69 covered events
on 2 dates. Under date-clustered statistics those are samples of 1 and
2, whatever the event count says. The one parent whose covered stream
spans enough independent dates to score a transform is
aster_etf_qqq_monthly_c098 (46 covered events, 8 dates), and both scored
candidates are its children.

## The scored pair (the cohort's best deflated statistics)

Advancement bar, fixed before results were read: BH q <= 0.10, date-
clustered t >= 3, DSR >= 0.95 at campaign effective N. BH denominator:
the 2 scored candidates (q is defined only over scored tests; printed
here so the small denominator is never hidden).

- MUT-529febfb3aac (adapters3; parent aster_etf_qqq_monthly_c098;
  BOLT_RANDOM_VARIABLE, prime_day_of_month as entry condition):
  10 events, 4 dates, mean daily net excess -83.49 bp, t = -2.929,
  p = 0.061, q = 0.1221, DSR = 0.0. A nonsense-variable gate printing
  negative at the cohort's best p-value is the control working as
  designed: it is evidence about noise, not about primes.
- MUT-1be9175ea843 (adapters3; parent aster_etf_qqq_monthly_c098;
  INVERT_SIGNAL): 46 events, 8 dates, mean daily net excess -1.61 bp,
  t = -0.008, p = 0.994, q = 0.9942, DSR = 0.0. The parent's recorded
  stream, inverted, is worth the same as the parent: nothing, on this
  window, net of the 6 bp exit cost.

Outcomes are intermediate per the funnel: forward return from the
recorded fill price to the close 1 trading day later (5 for HOLD_INVERT
primaries), net of a 6 bp exit haircut (Wave 5's measured real auction
cost, 5.8 bp), minus the benchmark's close-to-close return over the same
window. Benchmark of record: QQQ (see Evaluator notes).

## Multiple-comparison accounting

- Campaign effective N: 750.8, computed per Lane 2 Section 5 (per family
  cluster 1 + (k-1)(1-rho) over generated k; sibling rho measured at
  0.021 for adapters3, the only cluster with two scored siblings, and the
  stated 0.5 default elsewhere). Read this number correctly: it sizes
  the search space the DSR deflates against. The EVALUATED denominator
  is 2 scored candidates; no deflation arithmetic converts 2 scores into
  a cohort verdict, and none is claimed.
- PBO: NOT COMPUTED. CSCV requires at least 10 scored candidates; the
  cohort produced 2. Named here rather than silently absent.
- Peek budget: 1 peek taken, the scheduled Stage 2 cohort close read,
  logged in the register. No per-candidate browsing preceded the cohort
  close; the evaluator printed aggregates only.
- Luck ceiling check: at 1,200 nominal trials the False Strategy
  Theorem's best-of-null Sharpe is about 3.3; the scored pair's daily
  Sharpe ratios are negative to zero, so no luck-ceiling question even
  arises.

## Per-family funnel table

| family cluster | generated | Stage 1 pass | engine-required | data-fail | insufficient | scored |
|---|---|---|---|---|---|---|
| adapters3 | 300 | 21 | 10 | 0 | 9 | 2 |
| desk3 | 300 | 34 | 13 | 1 | 20 | 0 |
| adapters | 159 | 37 | 18 | 1 | 18 | 0 |
| aster_sleeves | 158 | 0 | 0 | 0 | 0 | 0 |
| laz_sleeves | 156 | 7 | 2 | 0 | 5 | 0 |
| rule_1d_cyan_smallcap | 17 | 0 | 0 | 0 | 0 | 0 |
| raschke_rre | 15 | 0 | 0 | 0 | 0 | 0 |
| saty_day | 14 | 0 | 0 | 0 | 0 | 0 |
| rule_1d_green_tom | 14 | 0 | 0 | 0 | 0 | 0 |
| rsi_meanrev | 14 | 9 | 7 | 2 | 0 | 0 |
| rule_1h_cyan_raw | 12 | 0 | 0 | 0 | 0 | 0 |
| red_day_reversal | 12 | 11 | 6 | 0 | 5 | 0 |
| rsi_meanrev_options | 12 | 3 | 1 | 0 | 2 | 0 |
| rule_1w_cyan_mom_adx | 9 | 0 | 0 | 0 | 0 | 0 |
| rule_1w_swing_beta_wt | 8 | 0 | 0 | 0 | 0 | 0 |

Family caps held at generation (adapters3 and desk3 at the 300 cap).
aster_sleeves' 158 candidates all failed Stage 1: its parents produced
no recorded dispatcher event stream in the window.

## Evaluator notes and incidents, on the face

- Benchmark substitution: the funnel text says excess over SPY; the
  stored SPY, IWM, and DIA caches end 2026-10-31 and cannot price
  November windows. QQQ 1Day covers the full window to 2026-11-13, so
  QQQ close-to-close is the benchmark of record and the trading
  calendar. Recorded in the evaluator before any scored result existed;
  the estate's standing yardstick is SPY and QQQ, and every excess
  number above is against QQQ.
- Daily bars for symbols without a 1Day file were aggregated from stored
  1Hour/1Min bars (last close per New York date). 49 symbols carry a
  usable daily series.
- First-run defect and cure: the evaluator's first run keyed evaluation
  records by candidate_id, collapsing the 35 content-duplicate records,
  and scored zero candidates because the SPY calendar ended 2026-10-31.
  Its appended records were removed, the generation register verified
  byte-identical to its pre-evaluation sha256
  (c10687dcbb8bb063bf7cf6ad67823b746b1e7930784a4d72df15d18992c2cd29),
  both defects fixed at the source, and the evaluation rerun once. No
  per-candidate result from the defective run was read or acted on; its
  aggregates are superseded by this verdict.
- Exit events for EXIT_ENTRY_SWAP streams: 243 bar-covered exit fills
  exist across other sleeves; no EXIT_ENTRY_SWAP candidate combined a
  Stage 1 pass, evaluable operators, and the 10-event / 3-date minimum.

## What this campaign proves and what it does not

Proven: the generator and register work at campaign scale (1,200 trials,
718 in novel cells, caps held, deterministic seed on record); the sealed
funnel executes end to end with every candidate dispositioned and every
denominator printed; the estate's stored history can currently score
almost none of it. Not proven: anything about the 1,198 unscored
candidates' quality. They are not failures of the mutation premise;
they are unmeasured, each with its reason on its register row.

The campaign falsifier from Lane 2 Section 9 (two consecutive campaigns
with no cohort clearing Stage 3's bar demotes the mutation premise)
stands at one campaign. The named unblockers, in order: widen the stored
bar cache beyond 49 symbols (613 of 6,708 events covered is the single
largest leak); let forward accrual run on the intent records cured
2026-11-15, which now carry symbol, side, and ref_price, unblocking
NEARMISS_FLIP and GATE_DROP sets for Campaign 2; and the expression
shadow-ledger resolver (Lane 8, build priority one), which is what
Stage 3 forward shadow and the options-expression candidates wait on.

## Deliverables

- CAMPAIGN1-REGISTER.jsonl: 2,403 lines (1 campaign header, 1,200
  candidate records, 1,200 evaluation records, 1 peek event, 1 cohort
  summary), in this directory.
- CAMPAIGN1-SURVIVORS.md: zero survivors, the bar stated.
- campaign1_generate.py and campaign1_evaluate.py: the campaign's code,
  pre-registered rules in the evaluator's header.

STATUS: PARTIAL. Proven on the final artifacts: generation and
registration of the full 1,200-candidate cohort, the complete sealed
funnel run with all 1,200 dispositions read back from the register, and
scored verdicts on the 2 candidates stored history could price (both
null to negative, DSR 0.0, zero survivors). Named open remainder: 120
candidates hold no Stage 2 grade (57 engine-required awaiting evaluator
throughput, 59 insufficient on current coverage, 4 data-fail on foreign
universes), and PBO is uncomputed for want of 10 scored candidates. The
denominator was never shrunk: it is printed at every stage.
