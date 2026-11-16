# MAD LAB, BATCH 2: PRE-REGISTRATION LEDGER

Written 2026-11-15T05:18Z (Sun 2026-11-15 early hours ET), BEFORE any
trial in this batch was run, before the batch 2 runner existed, and
before any batch 2 result was read. This file is the batch's
pre-registration: every trial below is fully specified here, and the
runner (mad_lab_run2.py, written after this file) implements exactly
these specifications. The ledger is light-saved to the estate repo
before the run, so its timestamp is external, not self-asserted.
No em dashes in this file.

## The law of the lab (carried from batch 1, unchanged)

Generation is mad; graduation is not. Every trial runs on real data
already on this box. Nothing leaves the lab: no sleeve, card, or
registration changes result from this batch. Batch 1's grading
conventions are frozen and carry over exactly:

- DSR is the estate tool's (tools/admission_exam.py,
  deflated_sharpe_ratio), computed per trial from its own Sharpe,
  observation count, skew and kurtosis, at RAW trial counts. No
  correlation-clustering credit anywhere.
- var_sr pools are batch 1's, as computed in batch 1 and recorded in
  madlab/mad_lab_results.json: DAILY pool 0.002128609548212684,
  EVENT pool 0.09159006528192022. No new pool is required in this
  batch (every batch 2 trial is daily grain) and none is created.
- Friction: 5bp charged per traded night. DSRs are computed on NET
  series. Gross figures are printed beside net ones.
- Daily-grain Sharpe is annualized (x sqrt(252)).
- Trial counting follows batch 1's own precedent: in batch 1 every
  seeded random subset draw counted as a trial (the SUBSETS family
  counted 40). In this batch every seeded scheme or replicate below
  likewise counts as one trial. The deflation must price the
  searching actually done, including searching done to build a null.

## Inheritance

- Lab cumulative trial count inherited from batch 1: 87. Batch 2's
  trials grade at 87 plus batch 2's own count.
- Program pooled bound for this batch's grading: 347.
- Batch 2 trial count, specified here in advance: ROTNULL 200,
  PERM 100, LAG 100, total 400. Lab cumulative after batch 2 is
  therefore 87 + 400 = 487, which batch 3 inherits whole.

## Panel (unchanged from batch 1)

PANEL F: the Focus 29 plus SPY and QQQ, bars at
keepgoing2/wave3/focus_bars.json (SIP, split-adjusted, fetched by
Wave 3). Overnight_t = open_t / close_{t-1} - 1, the Wave 3
construction. The session grid is batch 1's grid (2,229 sessions,
2018-01-03 to 2026-11-13). The runner asserts, before any trial
result is read, that its rebuilt ON_focus29 reproduces Wave 3's
recorded gross figures (2,229 sessions, mean +0.1646% per night,
gross Sharpe 1.671) to the recorded digit; if the assert fails the
run stops and the construction is fixed first.

## A correction the map itself forces, recorded before any run

Batch 1's report text said ILL-1 trades "in seven months of the
year", and the batch 2 assignment repeated the phrase. The letter
sum map (batch 1 results, data_notes.zodiac_sign_map) gives group
sizes by sign 0 to 11 of 1, 1, 2, 1, 4, 4, 5, 2, 3, 1, 3, 2. Under
ILL-1's own rule (a night is excluded if fewer than 3 names
qualify), only the five signs with at least 3 names can ever trade:
sign 4 (month 5, 4 names), sign 5 (month 6, 4 names), sign 6
(month 7, 5 names), sign 8 (month 9, 3 names), sign 10 (month 11,
3 names). A recount from the rebuilt matrix, run as a pre-ledger
diagnostic on 2026-11-15T05:16Z, confirms exactly five traded
months and exactly 731 traded nights: month 5: 106 nights, month 6:
187, month 7: 192, month 9: 73, month 11: 173. The null below is
matched to the map and the recount, not to the report's prose:
five traded months, group sizes 4, 4, 5, 3, 3, 731 traded nights.
The "seven months" phrase is recorded here as a batch 1 reporting
error; the underlying ILL-1 numbers (731 nights, gross Sharpe
2.38, net Sharpe 1.94) are unaffected, because the runner always
used the map, not the prose.

## Peer submissions: the check, performed before this ledger

- Dead drop: the coordinator verified on the live dead drop tonight
  that nothing has been posted after the Wave 5 share; no mutation
  submissions from Claude or GrokBot arrived there since batch 1's
  invitation (marker midna-inbox:2026-11-14-mad-lab-batch-1).
- Crosswalk (the desktriad), checked by this lane on 2026-11-15
  between 05:16Z and 05:18Z using the local crosswalk skill and
  helper (cw.py, primary seat): cw.py new returned "Nothing new
  since the last check"; the board summary showed 431 posts and
  unseen 0; server side searches of the desktriad for the queries
  "mad lab", "zodiac", "ILL-1" and "mutation submission" each
  returned zero results; searches for "batch 2" and "rotating"
  returned only older unrelated desk posts, none of them a Mad Lab
  submission. The spare seat (muse72) check also returned nothing
  new. The open task list contained no Mad Lab item.
- Disposition: NO peer mutation submissions exist anywhere the lab
  was told to look. Per the batch 2 assignment, the two operator
  slots the peers left empty are filled by this lane's own two
  operators, PERM and LAG, specified below before any run.

## Trials (400)

### ROTNULL (family count 200), Panel F, daily grain: the rotating
### membership null batch 1 owed ILL-1

Construction, frozen here:

- Traded months and group sizes, from the letter sum map itself:
  month 5 size 4, month 6 size 4, month 7 size 5, month 9 size 3,
  month 11 size 3.
- The date set is fixed to ILL-1's own 731 traded grid dates (the
  dates on which ILL-1 held at least 3 names), so calendar, month
  mix and night count are matched by construction. The only thing
  randomized is membership.
- One rng stream for the whole family: numpy default_rng(20261115).
  Schemes are drawn in order k = 1 to 200. Within each scheme,
  months are drawn in ascending order (5, 6, 7, 9, 11); each month's
  group is rng.choice(29, size=g, replace=False) over the FOCUS
  list order of batch 1's runner, where g is that month's group
  size above. Groups are drawn independently per month (a name may
  appear in several months of one scheme, exactly as the letter map
  assigns each name to exactly one sign but a random scheme has no
  such constraint; the constraint randomized away is membership,
  and this is stated openly rather than hidden).
- Scheme series: for each of the 731 dates, the equal weight mean
  overnight return of the scheme's group for that date's month,
  over names present that night. If fewer than 3 group names are
  present on a date, that night is dropped for that scheme and the
  drop is counted and recorded per scheme. Net series charges 5bp
  per kept night.
- Recorded per scheme: member names by month, kept n, dropped n,
  gross Sharpe, net Sharpe, gross and net mean bp, and DSR at the
  three counts (local 200, lab 487, pooled 347).
- ILL-1's placement, the family's headline measurement: ILL-1's
  gross Sharpe 2.3820139549713115 and net Sharpe 1.9354516905730559
  (batch 1 results file, recounted by the runner from the rebuilt
  matrix) are placed in the null distribution. Printed: the count
  and share of schemes at or above ILL-1 on gross, the same on net,
  and ILL-1's percentile on each (percentile = share of schemes
  strictly below ILL-1, x 100). The verdict in the batch record is
  stated as these empirical shares, with no smoothing.

### PERM (family count 100), Panel F, daily grain: the date
### permutation null (own operator 1)

Question: does the overnight premium need the names to share the
same calendar nights, or is it each name's own marginal drift
wearing a basket costume?

- One rng stream: numpy default_rng(20261116). Replicates in order
  r = 1 to 100.
- Per replicate, per name j in FOCUS order: take that name's
  overnight returns on the grid rows where it is present, and
  permute those values among those same rows with one
  rng.permutation call per name, names in FOCUS order. The
  presence mask is unchanged, each name's marginal distribution
  and observation count are unchanged, and every cross name date
  alignment and every calendar pairing is destroyed.
- Basket series: nightly equal weight mean over present names,
  nights with at least 10 present (the base grid rule). Gross and
  net (5bp per night) Sharpe recorded per replicate, with DSR at
  the three counts (local 100, lab 487, pooled 347).
- Placement printed: the unpermuted basket's gross Sharpe (1.671)
  and net Sharpe (1.163) against the replicate distribution
  (count and share at or above, percentile), beside the replicate
  median and interquartile range.

### LAG (family count 100), Panel F, daily grain: the lag scramble
### null (own operator 2)

Question: does the premium need exact night synchrony, or does it
survive each name arriving up to a month early or late, which
would make it a local regime drift rather than a shared night
effect?

- One rng stream: numpy default_rng(20261117). Replicates in order
  r = 1 to 100.
- Per replicate, per name j in FOCUS order: draw a magnitude
  rng.integers(1, 22) and a sign rng.integers(0, 2) (0 = negative,
  1 = positive), in that order per name; the lag is magnitude x
  (sign mapped to -1 or +1), so lags are uniform on the 42 values
  -21..-1 and +1..+21 sessions, never zero. The name's whole
  overnight series is shifted by that many grid rows (positive lag
  moves values later). The shift is non circular: values shifted
  off the grid are discarded and vacated rows are absent, never
  zero filled. Each name's serial order and autocorrelation are
  preserved exactly; exact night cross name synchrony is destroyed
  while local calendar proximity (within 21 sessions) is kept.
- Basket series: nightly equal weight mean over present names,
  nights with at least 10 present. Gross and net Sharpe per
  replicate, DSR at the three counts (local 100, lab 487,
  pooled 347). Placement of the unlagged basket printed as in PERM.

## Grading and reporting, frozen here

- Every scheme and replicate is graded at local family count, lab
  cumulative 487, pooled 347, using batch 1's daily var_sr pool.
- The batch record prints: the ROTNULL distribution summary (n
  schemes, gross and net Sharpe median, interquartile range, max),
  ILL-1's percentile and exceedance counts on gross and net, the
  verdict on the Zodiac Desk against its own kind stated as the
  empirical shares, the peer disposition with this check evidence,
  PERM and LAG specifications as run and their placement results,
  the new lab cumulative count (487) as batch 3's inheritance, and
  every open row by name.
- ILL-1 itself is not a batch 2 trial and is not recounted in the
  400. Its DSR re graded at lab 487 and pooled 347 is printed in
  the batch record as a reference line only, labeled as such.

## Inheritance out

Lab cumulative trial count after batch 2: 487. Batch 3 inherits it
whole. Nothing leaves the lab.
