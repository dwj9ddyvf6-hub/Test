# W7-7. MAD LAB BATCH 3 AND GRAVEYARD PULSES, 2026-11-15

Wave 7 Lane D. Batch 3 was pre-registered in
madlab/MAD-LAB-BATCH-3-LEDGER.md before the runner ran; the
ledger carries a dated amendment (2026-11-15 01:15 ET, the
owner's X10 order) that expanded the batch to the 400-trial
class before any batch 3 result existed, with the amendment's
timing proven on its face (no results file existed when it was
written). The runner is madlab/mad_lab_run3.py; full results in
madlab/mad_lab_results3.json. Shadow only; nothing leaves the
lab. No em dashes in this record.

## Verdict in one paragraph

504 trials ran. The three batch 1 near-misses were graded at
the inherited counts and the honest grading is the headline:
each one lives only at its local family count and nowhere else
(RND-7: DSR 0.922 at 8, then 0.022 at lab 487, 0.007 at lab 991,
0.037 at pooled 347; REG-8: 0.919, 0.074, 0.034, 0.103; MTH-4:
0.879, 0.029, 0.011, 0.044). The corrected rotating null moved
the Zodiac Desk from below median to above median, which prices
batch 2's null construction honestly without unburying anything.
The conditioner nulls split the three gates on the mean side:
the range gate's concentration survives scrambling, the trend
gate's does not survive lagging, the sign filter splits. And
the gap-factor hedge, batch 3's one candidate specification,
halves the find's mean and leaves its Sharpe exactly where it
was: the denominator attack fails, in numbers. Lab cumulative
count after batch 3: 991.

## The gates, before any result

- Reproduction assert: the runner rebuilt the Wave 3 matrix
  from focus_bars.json and matched Wave 3's recorded artifact
  to the digit (2,229 sessions, ON_focus29 mean +0.1646 percent,
  gross Sharpe 1.671). Passed before any trial was read.
- Part A reproduction: the three near-miss series rebuilt from
  batch 1's constructions reproduced batch 1's recorded local
  DSRs to 1e-6 (RND-7 0.921714, REG-8 0.918637, MTH-4 0.878639,
  at n 2,229, 1,595, 1,774). The regrades below are re-reads of
  batch 1's own series, not new series.
- ILL-1 recount: n 731, gross and net Sharpe matched batch 1 to
  1e-9 before placement in the corrected null.
- One deviation, named: the runner's first execution failed
  before any result was read, on a construction deviation this
  lane introduced (the basket date set was derived from the raw
  bars file where batch 1 derived both date sets from the focus
  bars). The exact error (KeyError: SMH, in the date-set
  construction) was preserved in the lane's run transcript,
  fixed to batch 1's exact construction, and rerun clean;
  mad_lab_run3.log holds the successful run. No specification
  changed; the ledger was not touched after the amendment.

## Part A. The near-misses at their harder tests

Same specifications, same series, no re-tuning, graded at the
inherited counts. Net of the 5bp flat charge.

| Trial | n | Net bp | Net Sharpe | t | DSR local | DSR lab 487 | DSR lab 991 | DSR pooled 347 |
|---|---|---|---|---|---|---|---|---|
| RND-7 range-rank gate | 2,229 | +20.48 | 1.55 | 4.61 | 0.922 (at 8) | 0.022 | 0.007 | 0.037 |
| REG-8 trend conditioner | 1,595 | +15.27 | 1.64 | 4.12 | 0.919 (at 8) | 0.074 | 0.034 | 0.103 |
| MTH-4 sign filter | 1,774 | +14.24 | 1.48 | 3.92 | 0.879 (at 7) | 0.029 | 0.011 | 0.044 |

The label the ledger promised, in its own words: each of these
near-misses lives only at its local count. At every count the
estate actually paid for the search, all three are deflated to
nothing. They remain what batch 1 said they were, measurement:
the range gate and the sign filter concentrate the per-night
mean, the trend conditioner names the find's habitat, and none
of it is a strategy at the honest counts.

## Part B. The auction-form interaction

The identical gross series charged at the measured auction cost
instead of 5bp flat: +5.845bp per traded night, the Wave 5
true-print CARRY basket median (mean +3.701bp), a six-name
subset measurement applied flat as a conservative bound and
labeled as such in the ledger.

| Trial | n | Net bp | Net Sharpe | t | DSR local 3 | DSR lab 487 | DSR lab 991 | DSR pooled 347 |
|---|---|---|---|---|---|---|---|---|
| RND-7-AUC | 2,229 | +19.63 | 1.48 | 4.42 | 0.994 | 0.014 | 0.004 | 0.024 |
| REG-8-AUC | 1,595 | +14.42 | 1.55 | 3.89 | 0.988 | 0.047 | 0.020 | 0.068 |
| MTH-4-AUC | 1,774 | +13.40 | 1.39 | 3.69 | 0.974 | 0.017 | 0.006 | 0.026 |

The auction charge costs each series 0.85bp of mean and 0.07 to
0.09 of Sharpe against the 5bp flat charge. It changes no
verdict at any inherited count: the near-misses were never
friction-bound at the counts that govern, they were count-bound.
(The local DSRs near 1.000 at family count 3 are the same
small-count arithmetic batch 1 labeled on ILL-1, printed
because the ledger promised every count.)

## Part C. ROTNULL-C: the corrected rotating null

Design chosen in the ledger before running: restrict the
rotating schemes to the kept-night set, names present on all
731 of ILL-1's shared traded dates. The pool holds 17 names
(SMH, SOXX, NVDA, AVGO, AMD, MRVL, TSM, AMAT, MU, WDC, AAOI,
COHR, LITE, AXTI, FCEL, VST, XLE). Every one of the 200 schemes
kept exactly 731 nights, asserted in the runner scheme by
scheme; the dispersion batch 2 reported (385 to 731, median
587.5) is zero by construction here. The rejected alternative,
modeling the drop process explicitly, is recorded in the
ledger with its reason.

Corrected distribution (200 schemes): gross Sharpe median
2.276, interquartile range 2.108 to 2.431, range 1.564 to
2.865. Net median 1.855, interquartile range 1.665 to 2.013,
range 1.090 to 2.433.

ILL-1's placement, then and now:

| Measure | Batch 2 null (uncorrected) | Batch 3 null (corrected) |
|---|---|---|
| Gross percentile | 45.5 (109 of 200 at or above) | 69.5 (61 of 200 at or above) |
| Net percentile | 39.0 (122 of 200 at or above) | 63.0 (74 of 200 at or above) |

The honest read, in two halves. First: the correction moves
ILL-1 from below median to above median on both measures, so
part of batch 2's placement verdict was the null's own
construction, kept-night dispersion, and not the Zodiac. That
is what this part was built to price, and it is reported
against this lane's own predecessor batch without softening.
Second: the burial stands, on the grounds that always governed
it. ILL-1's DSR at lab 487 was 0.304 (batch 2's reference
regrade); 30.5 percent of random corrected schemes still beat
it gross; and the best corrected scheme of the 200, ROTC-192
(net Sharpe 2.433), grades DSR 0.758 at its local 200, 0.636 at
lab 487, 0.535 at lab 991, 0.684 at pooled 347, surviving
nowhere. No rotating scheme, letters or coins, restricted pool
or full pool, survives at any count. ILL-1 is buried; this part
priced the null, labeled as such on every line of the results
file.

## Part D. Conditioner nulls (PERM and LAG, 300 replicates)

Each conditioner faced 50 permutation and 50 lag replicates of
its own construction, the batch 2 operator pattern. Two reads,
because the batch taught us they measure different things:

Sharpe placement: the real conditioner sits at percentile 0.0
against every one of its six null distributions (all 300
replicates at or above the real Sharpe; null net median Sharpes
2.373 and 2.552 for RND-7, 3.609 and 4.669 for REG-8, 2.474 and
2.938 for MTH-4, against real 1.55, 1.64, 1.48). This is batch
2's basket phenomenon again, now measured on gated series:
destroy synchrony and the scrambled series Sharpe higher,
because what synchrony adds is variance. Sharpe placement
against these nulls is uninformative for gated series, and the
lab will not use it as one again; that is a methods finding
with 300 replicates behind it.

Mean placement, which does discriminate (share of replicates
whose mean net bp reaches the real conditioner's mean):

| Conditioner | Real mean net | vs PERM 50 (median) | vs LAG 50 (median) |
|---|---|---|---|
| RND-7 | +20.48bp | beats 50 of 50 (16.61bp) | beats 42 of 50 (19.44bp) |
| REG-8 | +15.27bp | beats 50 of 50 (12.08bp) | beats 0 of 50 (17.26bp) |
| MTH-4 | +14.24bp | beats 50 of 50 (11.66bp) | beats 27 of 50 (13.87bp) |

All three gates concentrate the mean beyond anything
permutation produces. The trend gate's concentration does not
survive lagging: shift the names off the calendar and the
gated mean rises past the real one in every replicate, which
says REG-8's mean edge is entangled with exact-night alignment
in a way a conditioner should not be. The range gate's mean
mostly survives both scrambles. None of this promotes anything
(Part A's counts already settled that); it ranks the three
dead conditioners by how real their one measured property was,
which is the lab's product.

## Part E. GAP-HEDGE-1, the gap-factor-hedged expression

One specification, frozen in the ledger: the basket's
overnight return hedged by SPY's overnight return (the gap
factor) at the trailing 252-session beta estimated from prior
sessions only. Result: n 1,977 nights, mean net +6.55bp,
net Sharpe 1.18, t 3.31. DSR 1.000 at its local family count
of 1 (arithmetic at count 1, labeled as batch 1 labeled it),
0.002 at lab 487, 0.000 at lab 991, 0.003 at pooled 347.

Against the unhedged basket (net +11.46bp, net Sharpe 1.163):
the hedge removes about 43 percent of the mean and essentially
none of the Sharpe problem, because it removes variance in the
same proportion. Batch 2's PERM and LAG nulls suggested the
shared gap factor was variance the basket pays for; this
specification, the direct tradeable form of that suggestion,
says the factor carries the mean too, in the same proportion.
The denominator attack fails in this form, and the failure is
measured, not argued. GAP-HEDGE-1 is not a candidate and
nothing is registered from it.

## Survivors and counts

- GOLD (DSR at or above 0.95 at pooled 347): none.
- LAB (at or above 0.95 at lab 991): none.
- LOCAL: the three auction interactions print 0.974 to 0.994 at
  their interaction family count of 3, and GAP-HEDGE-1 prints
  1.000 at count 1; both are small-count arithmetic, labeled,
  worth exactly what their counts are worth.
- New trials: 504 (ROTNULL-C 200, conditioner nulls 300,
  auction interactions 3, GAP-HEDGE-1 1). Part A regrades added
  0, as the ledger fixed. Lab cumulative after batch 3: 991.

## W7-7b. Graveyard pulses armed

Scripts on the foundry pattern, constructions frozen from
foundry/c3_graveyard.py, each docstring carrying the revival
rule copied verbatim from the registration
(2026-11-15-graveyard-book.md): a leg is declared REVIVED only
if its forward read, at 250 further active days (or 100
further events for PEAD), shows its published-direction mean
positive with t at or above 2 in the forward window alone.

| Leg | Script | Ledger | Dry run on held data |
|---|---|---|---|
| TOM | keepgoing2/wave7/w7d_tom_accrual.py | w7d_tom_shadow.jsonl | genesis written once; 0 active days appended; rerun appended 0 |
| PAIRS | keepgoing2/wave7/w7d_pairs_accrual.py | w7d_pairs_shadow.jsonl | genesis written once; 0 appended; rerun 0. Construction proof: the script's rebuilt pairs leg on the held panel reproduces the foundry record exactly (1,469 active days, mean +1.04bp) |
| PEAD | keepgoing2/wave7/w7d_pead_accrual.py | w7d_pead_shadow.jsonl | held mode (Wave 5 corpus): genesis written once; 0 forward events; rerun 0 |

PEAD was buildable tonight, and the reason is on the record:
the same EDGAR submissions route the Wave 5 corpus was built
with (data.sec.gov per-CIK, 8-K Item 2.02, the same 24 filers
and the same named exclusions) serves forward events directly,
so the accrual reads filings after the 2026-11-15 registration,
prices each event by the foundry construction as bars cover
it, and leaves unpriced fields null rather than inventing
them. No missing input had to be named.

Crons, armed and read back (cron.status for each, cron.view
for the TOM body): w7-tom-accrual-daily, w7-pairs-accrual-daily,
w7-pead-accrual-daily, all enabled, weekdays at 09:51 ET, all
with next run Mon 2026-11-16 09:51 EST. The time is chosen and
its reason stated: the sessions these legs grade complete at
the 09:30 open, the sibling shadow accruals already hold 09:46,
and 09:51 puts these five minutes behind them on the same bar
fetch while still running minutes after the open exists. Each
job body carries the revival rule and the estate's standing
pattern: silent on normal runs, report only on a revival read
or a repeated failure. (Each cron.add call returned a
tool-extension timeout while the scheduler in fact saved the
job; arming was verified by status read-back for all three,
never assumed from the add call.)

The other three graveyard legs (WEEKEND, JANUARY, SELLMAY)
were not in this brief and are not armed here; they are named
so their absence is a scope fact, not an oversight.

## Typed spend

Zero typed seats, $0.00, this lane tonight. Every judgment in
the batch was pre-registered in the ledger and the exams are
deterministic, the same posture Wave 4 recorded for its own
deterministic work.

STATUS: GREEN for batch 3 as pre-registered (504 trials, all
gates passed, cumulative 991, survivors none, every number in
this record read from madlab/mad_lab_results3.json after the
run) and GREEN for the pulses (three scripts dry-run proven at
0 appended on rerun, three crons armed and read back with next
runs Mon 2026-11-16 09:51 EST). EVIDENCE POINTER:
madlab/MAD-LAB-BATCH-3-LEDGER.md, madlab/mad_lab_run3.py,
madlab/mad_lab_results3.json, madlab/mad_lab_run3.log,
keepgoing2/wave7/w7d_tom_accrual.py, w7d_pairs_accrual.py,
w7d_pead_accrual.py and their three shadow ledgers beside them.
