# MAD LAB, BATCH 1: PRE-REGISTRATION LEDGER

Written 2026-11-15T04:51Z (Sat 2026-11-14 night ET), BEFORE any trial
in this batch was run and before any result was read. This file is the
batch's pre-registration: every trial below is fully specified here,
and the runner (mad_lab_run.py, written after this file) implements
exactly these specifications. The ledger is light-saved to the estate
repo before the run, so its timestamp is external, not self-asserted.

## The law of the lab

Generation is mad; graduation is not. Every trial runs on real data
already on this box (plus one bars fetch, Panel S, specified below).
Survivors are graded at three trial counts printed side by side: the
local operator-family count, the lab cumulative count (87, this
batch), and the hunt program's pooled bound (260 at Wave 4's close,
composition in the Wave 4 record). A survivor at 260 is GOLD. A
survivor only at a smaller count is labeled exactly that. Nothing
leaves the lab: no sleeve, card, or registration changes result from
this batch. Survivors are handed to the next wave as exam candidates
with their trial cost attached.

Grading conventions, frozen here:

- DSR is the estate tool's (tools/admission_exam.py,
  deflated_sharpe_ratio), computed per trial from its own Sharpe,
  observation count, skew and kurtosis, at RAW trial counts. No
  correlation-clustering credit is taken anywhere in this batch,
  which is the conservative direction (the find's own family took
  clustering credit; the lab does not).
- var_sr (the cross-trial Sharpe variance the DSR deflates against)
  is computed in two pools, stated here so it cannot be tuned after
  the fact: the DAILY pool is the variance of per-day Sharpe ratios
  across all daily-grain trials in this batch; the EVENT pool is the
  variance of per-observation Sharpe ratios across all event-grain
  trials in this batch. Each trial is deflated against its own
  grain's pool at all three counts.
- Friction: every overnight trial is charged 5bp per traded night
  (daily grain) or 5bp per event (event grain), the registered
  falsifier's basis for the auction form. DSRs are computed on NET
  series. Gross figures are printed beside net ones where the
  comparison demands it (the subset distribution, whose comparator,
  the whole basket's 1.67, is a gross number).
- A trial whose construction yields fewer than 20 observations is
  still run and printed with its n; it simply cannot clear anything
  and is labeled SMALL-N.
- Daily-grain Sharpe is annualized (x sqrt(252)); event-grain Sharpe
  is per-observation and is never annualized in print.

## Panels

- PANEL F: the Focus 29 plus SPY and QQQ, bars at
  keepgoing2/wave3/focus_bars.json (SIP, split-adjusted, fetched by
  Wave 3). Overnight_t = open_t / close_{t-1} - 1; intraday_t =
  close_t / open_t - 1, exactly the Wave 3 construction. The session
  grid is the Wave 3 grid: dates where the Focus equal-weight series
  has at least 10 names, intersected with basket and SPY
  availability (2,229 sessions, 2018-01-03 to 2026-11-13). The
  runner asserts, before any trial result is read, that its rebuilt
  ON_focus29 reproduces Wave 3's recorded gross figures (Sharpe
  1.67, mean +0.165% per night, t 4.97) within rounding; if the
  assert fails the run stops and the construction is fixed first.
  Basket-variant inclusion rule: a session counts for a variant if
  at least 10 of the variant's names have prints that session (or
  the variant's own stated minimum where one is specified below);
  excluded sessions are dropped, never zero-filled, and n_obs is
  printed per trial.
- PANEL B: the broad 100-name pull at
  keepgoing2/wave3/lane_c_raw_bars.json (SIP, split-adjusted), each
  name on its own session grid. Used by the event and population
  crosses.
- PANEL S: the 34 unique symbols of the morgue point-in-time
  short-interest file (~/workspace/morgue/output/short_interest_pit.jsonl,
  822 rows, 3 publication dates, Oct-Nov 2026). Neither bar panel
  contains a single one of these symbols (verified tonight by set
  intersection: 0 of 34 in Panel F, 0 of 34 in Panel B), so their
  bars are fetched tonight through the estate Alpaca route exactly
  as Wave 3 fetched Panel F (SIP, adjustment=split, from 2018-01-01),
  saved as madlab/si_bars.json. If the fetch fails, CRS-7 and CRS-8
  are recorded NOT RUN with the exact error, never silently dropped.

## Trials (87)

### INVERT (family count 5), Panel F, daily grain

- INV-1 SHORT_ON_focus29: the negative of the base overnight basket.
- INV-2 SHORT_INTRADAY_focus29: the negative of the intraday basket
  (the leg the family exam graded at Sharpe 0.01).
- INV-3 SHORT_ON_spy: the negative of SPY's overnight leg (which
  failed the family exam long, DSR 0.715).
- INV-4 SHORT_ON_basket8: the negative of the 8-name basket's
  overnight leg (minimum 5 names per session, as in Wave 3).
- INV-5 SHORT_INTRADAY_basket8: the negative of the basket's
  intraday leg.

### ABLATE (family count 8), Panel F, overnight basket variants

- ABL-1 ON minus the five CARRY names (SNDK, CRWV, RKLB, NVDA, AMD):
  the other 24 names. Does the effect survive the removal of the
  only legs that survive even crossing friction?
- ABL-2 ON minus FCEL (the largest single gross contributor,
  +42bp per night in the Wave 4 friction table).
- ABL-3 ON minus the top three gross contributors (FCEL, SNDK, CRWV).
- ABL-4 ON on even-index grid sessions only (cadence ablation, half
  the nights, one-night holds).
- ABL-5 ON on odd-index grid sessions only (the other half).
- ABL-6 ON tail-trimmed: per calendar year, the 10 best basket
  nights removed. Labeled ex-post: this measures tail dependence of
  the find; it is not a tradeable rule and is never cited as one.
- ABL-7 ON minus the energy8 members (FLNC, EOSE, FCEL, BE, OKLO,
  VST, CEG, XLE): the other 21 names.
- ABL-8 ON minus the semis12 members (SMH, SOXX, NVDA, AVGO, AMD,
  MRVL, ARM, TSM, AMAT, MU, SNDK, WDC): the other 17 names.

### ADD RANDOM (family count 8), Panel F, overnight basket

- RND-1 ON on sessions whose day-of-month is 15 or less only.
- RND-2 ON on sessions whose day-of-month is 16 or more only.
- RND-3 ON restricted to tickers of length 3 or less (SMH, AMD, ARM,
  TSM, MU, WDC, BE, VST, CEG, XLE), minimum 6 names per session.
- RND-4 ON restricted to tickers of length exactly 4 (the other 19
  names), minimum 10 per session.
- RND-5 ON gated by a seeded coin: numpy default_rng(20261114), one
  Bernoulli(0.5) draw per grid session in date order; trade only
  heads nights. A pure-noise control with the seed frozen here.
- RND-6 ON on prime day-of-month sessions only (2, 3, 5, 7, 11, 13,
  17, 19, 23, 29, 31).
- RND-7 ON range-rank gate: hold only names whose prior session
  (t-1) range, (high - low) / close, ranks in the top tercile of
  that session's cross-section; the gate is known at the close of
  t-1, before the overnight hold. Night excluded if fewer than 5
  names pass.
- RND-8 ON restricted to names whose ticker letter-sum (A=1 to
  Z=26) is even. The subset is whatever the rule produces; the rule,
  not the subset, is what is frozen here.

### METHOD SCRAMBLE (family count 7), Panel F, overnight

Same signals, different estimators, applied to the nightly
cross-section of the 29 names' overnight returns:

- MTH-1 Median: the nightly cross-sectional median replaces the mean.
- MTH-2 Trimmed mean: drop the 3 highest and 3 lowest names nightly.
- MTH-3 Dollar-volume weights: weights proportional to prior
  session volume x close, normalized nightly.
- MTH-4 Sign filter: hold, equal weight, only names whose total
  return on session t-1 was positive; night excluded if fewer than
  5 qualify.
- MTH-5 Rank-momentum weights: weights proportional to the rank of
  the name's prior-night overnight return (ascending ranks 1..n,
  normalized), among names present both nights.
- MTH-6 Inverse-vol weights: weights proportional to 1 / sigma21,
  sigma21 the trailing 21-session standard deviation of the name's
  overnight returns through t-1, floored at one quarter of that
  night's cross-sectional median sigma21; names need at least 10
  trailing overnight observations; night excluded if fewer than 10
  names qualify.
- MTH-7 Log-mean: nightly return = exp(mean(log(1 + r_i))) - 1.

### REGIME SCRAMBLE (family count 8), Panel F, overnight

All regime variables are lagged: known at the close of t-1, before
the hold. Terciles are on expanding history with a 252-session
minimum before the first classified night; unclassified nights are
excluded.

- REG-1 ON when SPY's trailing 21-session realized volatility (of
  total returns, through t-1) is in its top tercile.
- REG-2 ON when that volatility is in its bottom tercile.
- REG-3 ON on pre-2020 sessions only (date before 2020-01-01).
- REG-4 ON on post-2020 sessions only (date on or after 2020-01-01).
- REG-5 ON when the prior session's cross-sectional dispersion
  (standard deviation of the Focus names' total returns) is in its
  top tercile.
- REG-6 ON when that dispersion is in its bottom tercile.
- REG-7 ON when SPY's close at t-1 is below its trailing
  200-session mean. SUBSTITUTION, stated openly: the operator list
  asked for a rate regime; no rates series exists in either bar
  panel on this box tonight (TLT and IEF verified absent from both
  files), so the fourth regime axis is the SPY trend regime. This
  trial is a trend-regime test and is never cited as a rate test.
- REG-8 ON when SPY's close at t-1 is at or above that mean.

### CROSS THE DEAD (family count 10)

Killed and rejected families, crossed with each other and with the
find. Event-grain trials are graded in the event pool.

- CRS-1 TAX-LOSS x OVERNIGHT, in-window (Panel B, pooled-night
  grain): for each season Y (December of Y into January of Y+1),
  the population is the names with year-to-date total return at or
  below -30% at the last session on or before Nov 30 of Y, with at
  least 120 sessions of bars during Y. Window nights are sessions
  dated Dec 15 of Y through Jan 10 of Y+1. The series is the
  equal-weight mean overnight return of population names present
  (at least 3 required), pooled across seasons 2018-19 through
  2025-26. This is the FX-01/FORCED-05 population idea with its
  close-to-close leg amputated and only the overnight leg kept.
- CRS-2 TAX-LOSS x OVERNIGHT, placebo shoulders: same populations,
  nights in Nov 1 to Dec 14 of Y and Jan 11 to Feb 28 of Y+1.
- CRS-3 GUIDANCE CUTS x OVERNIGHT (Panel B, event grain): events
  from keepgoing2/wave4/v5_guidance_events.jsonl with direction
  "cut" and ticker in Panel B (14 such events at ledger time).
  Entry at the close of the first session on or after the file
  date; exit at the open of the next session; one observation per
  event.
- CRS-4 GUIDANCE RAISES x OVERNIGHT, INVERTED (event grain): the
  21 "raise" events in Panel B; the observation is the negative of
  the same overnight return construction as CRS-3.
- CRS-5 DIVIDEND x OVERNIGHT (event grain): cash-dividend records
  from keepgoing2/wave3/lane_c_events_raw.json (pulls.cash_dividend),
  symbol in Panel B, special = false, rate above 0, ex-date inside
  the name's bar span and not its first bar. The bars are
  split-adjusted only, so the dividend is credited by hand:
  observation = (open on ex-date + rate) / close on the prior
  session - 1. This is the overnight slice of the dividend-capture
  family Wave 3 rejected close-to-close.
- CRS-6 DIVIDEND x OVERNIGHT, INVERTED: the negative of CRS-5's
  gross observation, friction charged the same way.
- CRS-7 SHORT INTEREST x OVERNIGHT (Panel S, membership, daily
  grain): membership is the top tercile of SI/float (latest
  settlement per symbol) among the 34 SI symbols; the series is
  the equal-weight overnight return of member names (at least 3
  present) over the fetched history. CAVEAT, printed wherever this
  trial is cited: the membership is an Oct-Nov 2026 snapshot
  applied backward over the whole history, the FIT-precedent form;
  the PIT file is backfilled with only 3 publication dates, which
  is the defect that killed the standalone in Wave 3, and this
  cross inherits that label in full. It is a membership test, never
  a point-in-time strategy.
- CRS-8 SHORT INTEREST x INTRADAY: same membership, the intraday leg.
- CRS-9 FIT-HI x INTRADAY (Panel F, daily grain): the intraday
  basket over the 15 FIT_HI names (hunt/fit_proxy_v1.json ranking,
  as used by Wave 4's family exam), at least 8 present. The
  conditioner that did not carry the overnight effect, crossed
  with the leg that was worthless.
- CRS-10 GUIDANCE CUTS x LOSER STATE (event grain): CRS-3's events
  further filtered to names whose entry-session close is below
  their close 126 sessions earlier (a point-in-time loser state,
  the tax-loss condition in miniature). Runs and prints its n
  however small it lands.

### RANDOM SUBSETS (family count 40), Panel F, overnight

numpy default_rng(20261114), draws in this exact order: 20 subsets
of 5 names (SUB5-01 to SUB5-20), then 20 subsets of 10 names
(SUB10-01 to SUB10-20), each drawn without replacement from the 29
Focus names in the FOCUS list order of the Wave 3 script, via
rng.choice(29, size=k, replace=False) called sequentially.
Series: equal-weight overnight over subset names present; a
session counts if at least max(3, ceil(0.6 x k)) subset names have
prints. The distribution of the 40 subset Sharpes against the whole
basket's is itself the finding of this family: selection effect
measured, not hidden. Each subset is graded at the family count of
40 like any other trial; the best subset is a selection artifact
until proven otherwise, and the report will say so in those words.

### ONE GENUINELY ILLOGICAL TRIAL (family count 1)

- ILL-1 THE ZODIAC DESK (Panel F, daily grain): each Focus name is
  assigned a sign, sign = (sum of its ticker's letter values,
  A=1 to Z=26) mod 12. For a session in calendar month m (1 to 12),
  hold overnight, equal weight, only the names whose sign equals
  m - 1; a night is excluded if fewer than 3 names qualify. There
  is no economic hypothesis for this rule, no channel by which the
  calendar month could select the right letters, and no defense of
  it beyond this: the lab was ordered to do one thing that defies
  reason, with real data, fully specified in advance, and graded at
  the same three counts as everything else. If it survives
  anywhere, that survival is itself the measurement of how much
  noise this batch can manufacture.

## Reference line (not a trial)

The rebuilt ON_focus29, gross and net of 5bp, printed as the
comparator for the ablations and the subset distribution. It is
not counted in the 87.

## Inheritance

The lab's cumulative trial count after this batch is 87. Batch 2
inherits it: its survivors are graded at 87 plus batch 2's own
count, and the program pooled bound rises by the same amount. The
peers are invited, in tonight's Triad share, to submit mutations
for batch 2, each with its data contract.
