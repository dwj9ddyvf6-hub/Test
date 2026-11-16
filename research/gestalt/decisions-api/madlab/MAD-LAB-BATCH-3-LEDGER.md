# MAD LAB, BATCH 3, PRE-REGISTRATION LEDGER

Written 2026-11-15 night (Wave 7 Lane D) BEFORE the batch 3 runner
exists. This file's content is the pre-registration: every
specification below was fixed in writing before any batch 3 result
was read. The runner (madlab/mad_lab_run3.py) implements this
ledger exactly; any deviation found after the run is reported as
a deviation, never silently absorbed. No em dashes in this file.

## Inherited state, frozen

- Lab cumulative trial count inherited: 487 (batch 1: 87; batch 2:
  400). Program pooled bound inherited: 347. No record held by
  this lane states a higher pooled bound tonight, so 347 is the
  pooled grading bound used here, named as inherited, not updated.
- Grading: estate DSR (tools/admission_exam.deflated_sharpe_ratio)
  on NET series at raw counts, no correlation clustering credit
  anywhere, exactly as batches 1 and 2.
- var_sr pools: batch 1's frozen pools are inherited whole and
  never recomputed inside this batch: daily pool 0.002128609548212684
  (batch 1 results file: 0.00213 rounded), event pool 0.09159
  (unused in this batch; every batch 3 trial is daily grain).
- Friction baseline: 5bp per traded night, as batches 1 and 2.
- Reproduction gate, run before any result is read: the runner
  rebuilds the Wave 3 matrix from keepgoing2/wave3/focus_bars.json
  and asserts against Wave 3's own recorded artifact
  (w3_overnight_intraday.json): 2,229 sessions, ON_focus29 mean
  +0.1646 percent per night, gross Sharpe 1.671, to the recorded
  digit tolerances batch 1 used (n exact, mean within 2e-5, Sharpe
  within 0.02). The runner then recounts ILL-1 and asserts batch
  1's recorded figures to 1e-9 (n 731, gross Sharpe 2.3820139550,
  net Sharpe 1.9354516906) before placing it in any null. If a
  gate fails, the batch stops; no result is read.

## Part A. The three carried near-misses at their harder tests

Trials: RND-7 (range-rank gate), REG-8 (trend conditioner), MTH-4
(sign filter), each at its batch 1 specification EXACTLY as
implemented in madlab/mad_lab_run.py, quoted here so the spec
lives in this ledger and not only in code:

- RND-7 (family ADD_RANDOM, local count 8): for each grid session,
  take the names with a non-missing prior-session range
  ((high minus low) over prior close, from the prior bar) and a
  non-missing overnight return; if at least 5 such names, keep the
  top tercile by prior range (threshold: the k-th largest value
  with k = ceil(count / 3)); if at least 5 names pass, the night's
  observation is the equal-weight mean overnight return of the
  passing names. Series length as batch 1 recorded it.
- REG-8 (family REGIME, local count 8): for each grid session i
  from index 200 onward with at least 10 names present, compute
  the mean of SPY closes over the 200 sessions before i; if SPY's
  close at i minus 1 is at or above that mean, the session's
  basket overnight return (the unmutated focus29 basket value) is
  kept; otherwise the session contributes nothing. Series as
  batch 1 recorded it (1,595 nights).
- MTH-4 (family METHOD, local count 7): for each grid session i
  from 1 onward, keep the names whose prior-session total return
  (close over prior close minus 1) is strictly positive and whose
  overnight return is non-missing; if at least 5 such names, the
  night's observation is their equal-weight mean overnight return.

The harder test is defined once and applies to all three: the
SAME specification on the SAME series with NO re-tuning of any
constant, graded at the inherited counts. A regrade is a re-read
of an existing trial at a larger count; it is not a new trial and
adds nothing to the cumulative count. For each near-miss the
runner prints, from the identical net series batch 1 graded:

1. DSR at its original local family count (8, 8, 7 respectively),
   which must reproduce batch 1's recorded values (0.922, 0.919,
   0.879) to three decimals; a mismatch stops the batch.
2. DSR at the lab cumulative count 487.
3. DSR at the program pooled bound 347.
4. DSR at the lab cumulative count after this batch (991, per the
   counting rule below), printed last and labeled as the count
   the batch leaves behind.

The honest grading is the point of this part: a near-miss that
only lives at count 8 is labeled exactly that, in those words, in
the batch report.

## Part B. One pre-registered interaction per near-miss: the auction form

For each of the three near-misses, ONE interaction variant, fixed
here before running: the identical gross series from Part A,
charged at the measured auction cost instead of the 5bp flat
charge. The measured auction cost used is +5.845bp per traded
night: the Wave 5 W5-1 true-print measurement (keepgoing2/wave5/
w5a_carry_capture.json, reported in WAVE-5-2026-11-14.md,
Correction 2): the six-name CARRY basket's true-print auction
cost, median +5.845bp per session (mean +3.701bp), against Wave
4's bar-based basket figure of minus 0.626bp on 29 names. The
label travels with the number: this cost was measured on the
six-name CARRY subset (SNDK, CRWV, RKLB, NVDA, AMD, MU) over 10
sessions, and applying it flat to a 29-name basket series is a
conservative bound, not a basket measurement. The median is used,
not the mean, because Wave 5's own table carries the
mid-reference noise caveat and the median is its robust summary.

Trial ids: RND-7-AUC, REG-8-AUC, MTH-4-AUC. Each is a NEW trial
(3 added to the cumulative count). Each is graded at local count
3 (its interaction family), at 487, at 991, and at pooled 347,
with batch 1's frozen daily var_sr pool. Net Sharpe, mean net bp,
n, and t are printed beside every DSR.

## Part C. ROTNULL-C: the corrected rotating null (Wave 6 cell 5)

Batch 2's open row 3, carried into Wave 6's starting cells:
batch 2's rotating schemes kept 385 to 731 of the 731 shared
dates (median 587.5) because random groups include late-listed
names, and nights drop where fewer than 3 drawn names were
present. Batch 3 must choose deliberately between two designs,
and the choice is made HERE, before running:

CHOSEN: restrict the rotating schemes to the kept-night set:
names listed for the full window. Definition, frozen: the pool
is every Focus 29 name whose overnight return is non-missing on
EVERY one of ILL-1's 731 shared traded dates (the five traded
months' dates from batch 2's recount). Every scheme drawn from
this pool keeps exactly 731 nights by construction, because each
drawn name is present on each shared date and each month group
has at least 3 names. The runner asserts kept nights equal 731
for all 200 schemes and prints the pool's membership and size;
if the pool holds fewer than 5 names the design cannot draw the
largest group (size 5) and the batch stops with that fact
printed, rather than relaxing the definition after seeing it.

REJECTED, with the reason recorded: model the drop process
explicitly. That route needs a listing-date and presence process
estimated from the same tape the null grades, which builds the
null out of fitted parameters of the object under test; the
restriction route prices the construction with no fitted
parameters at all, and it answers the exact question batch 2
left open (does the placement verdict survive when kept nights
are matched by construction). The rejected route stays available
to a later batch as a separate, separately counted design.

Construction, otherwise identical to batch 2's ROTNULL: 200
schemes, months ascending over the five traded months (May,
June, July, September, November), group sizes 4, 4, 5, 3, 3 from
batch 2's corrected map, each month's group drawn without
replacement from the restricted pool, membership the only
randomized element, 5bp charged per kept night. Rng stream:
numpy default_rng(20261118), one stream, schemes drawn in order
1 to 200, months ascending inside each scheme. This stream is
new (batch 2 used 20261115) because the pool changed; reusing
the old stream against a different pool would imply a pairing
that does not exist.

Read: ILL-1's gross and net Sharpe placed against the corrected
distribution exactly as batch 2 placed it (share of schemes at
or above ILL-1, and ILL-1's percentile, both measures), plus the
distribution's median, interquartile range, minimum and maximum,
and the best scheme's DSR at local 200, lab 991, and pooled 347.
ILL-1 is buried (batch 2's verdict stands and is not retried
here); this part prices the null's own construction, and every
output line carries that label. The 200 schemes are counted as
trials under the lab's standing convention (batch 2 counted its
200 the same way).

## Amendment, 2026-11-15 01:15 ET, written before any batch 3 run

The owner's X10 order of 2026-11-15 01:15 ET expands this batch
to the 400-trial class batch 2 proved. This amendment is written
while the batch 3 runner exists but has NOT been executed (no
mad_lab_results3.json exists at the time of writing; that
absence is the proof the amendment is still pre-registration).
It adds Part D (conditioner nulls) and Part E (the gap-factor
hedge) below, supersedes the counting rule, and moves every
after-batch grading count in Parts A to C from 690 to 991. The
original counting text is replaced, not silently edited: the
superseded figures were 203 new trials and a cumulative 690.

## Part D. Conditioner nulls: PERM and LAG for each near-miss

Each of the three Part A conditioners (RND-7, REG-8, MTH-4)
faces the same null discipline the basket faced in batch 2:
permutation and lag replicates of its own construction, 100
replicates per conditioner, split 50 PERM and 50 LAG, 300
replicates in total. Every replicate rebuilds the conditioner's
series from the scrambled matrix by the Part A specification,
unchanged, and is graded as a placement distribution only.

- PERM (batch 2's operator): each Focus name's overnight
  returns permuted among its own present nights; presence and
  marginals preserved, shared calendar nights destroyed.
  Conditioner features that come from other series stay on the
  calendar: RND-7's range-rank uses the calendar night's range
  values against the permuted overnight returns; MTH-4's sign
  filter uses the prior calendar session's total returns;
  REG-8's trend gate uses the calendar SPY close path and gates
  the rebuilt basket of permuted names.
- LAG (batch 2's operator): each name's overnight column
  shifted by its own seeded lag, uniform on 21 sessions either
  way, never zero; serial order preserved, exact-night synchrony
  destroyed. Features as in PERM: range, total-return, and SPY
  series stay on the calendar; only the overnight columns move.
- Rng streams, one per conditioner per operator, frozen:
  PERM: RND-7 default_rng(20261119), REG-8
  default_rng(20261120), MTH-4 default_rng(20261121).
  LAG: RND-7 default_rng(20261122), REG-8
  default_rng(20261123), MTH-4 default_rng(20261124).
  Draw order inside a stream: replicates 1 to 50 in order;
  inside PERM, names in FOCUS order; inside LAG, per name the
  magnitude draw then the sign draw, exactly as batch 2's runner
  drew them.
- Read, per conditioner: the real conditioner's gross and net
  Sharpe placed against its own PERM 50 and its own LAG 50
  separately (share of replicates at or above the real value,
  and the real value's percentile), and against the pooled 100.
  Replicates are null constructions, not tradeable series; any
  DSR printed for a replicate is arithmetic about a scrambled
  tape and is not a graduation, survival, or candidate, exactly
  as batch 2 labeled its PERM and LAG replicates.
- Counting: 300 new trials (3 conditioners x 100). Trial ids:
  RND7-PERM-01..50, RND7-LAG-01..50, and the same pattern for
  REG8 and MTH4.

## Part E. GAP-HEDGE-1: the gap-factor-hedged expression of the find

Wave 6 cell 5 named this batch's candidate specification: a
gap-factor-hedged expression of the find, demanded by batch 2's
PERM and LAG result (synchrony is variance, not mean: the shared
overnight factor is variance the basket pays for). ONE
specification, frozen here:

- The gap factor on night t is SPY's overnight return on night
  t (the market-wide overnight gap, the shared component the
  basket's names gap with).
- The hedge loading on night t is the ordinary least squares
  beta of the focus29 basket's overnight returns on SPY's
  overnight returns over the trailing 252 sessions ending at
  t minus 1 (prior sessions only, no lookahead; the first 252
  grid sessions are the estimation burn-in and produce no
  hedged observation).
- The hedged observation on night t is: basket overnight return
  on t minus beta times SPY overnight return on t. Basket means
  the unmutated focus29 basket value on nights with at least 10
  names present, exactly as the reproduction gate builds it.
- Charge: the lab's flat 5bp per traded night, stated as a
  convention for comparability; the hedge leg's own measured
  cost is not in any held table and is not invented here.
- Grading: estate DSR on the net series at local family count 1
  (its own family, HEDGE), at 487, at 991, and at pooled 347,
  batch 1's frozen daily var_sr pool. Net Sharpe, mean net bp,
  n, and t printed beside every DSR. One specification means
  one: no beta window, factor, or charge variant is run in this
  batch, and a variant anyone wants later is a new trial in a
  later ledger at the count then standing.

## Counting rule for this batch, fixed in advance (as amended)

- Part A regrades: 0 new trials (re-reads at larger counts).
- Part B interactions: 3 new trials.
- Part C schemes: 200 new trials.
- Part D conditioner null replicates: 300 new trials.
- Part E GAP-HEDGE-1: 1 new trial.
- Batch 3 total: 504 new trials, in the 400-trial class batch 2
  established (batch 2 ran 400). Lab cumulative count after
  batch 3: 487 + 504 = 991. Any run that produces a different
  total has deviated from this ledger and says so.

## What this batch is not

No trial here is a candidate, a sleeve, or a registration.
Nothing leaves the lab. A near-miss that clears 0.95 at any
printed count in Part A or B is reported as a number with its
count attached, not as a survival, because the counts it must
clear are the inherited ones and the report prints all four.
