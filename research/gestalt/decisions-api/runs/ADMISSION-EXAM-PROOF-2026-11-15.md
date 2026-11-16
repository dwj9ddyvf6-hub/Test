# ADMISSION EXAM PROOF: S3, the fleet admission exam as tested code

Date of run: Sat 2026-11-14 (file dated 2026-11-15 per the program
schedule). Code: tools/admission_exam.py. Proof script:
tools/test_admission_exam.py, executed end to end, exit code 0,
final line "ALL CHECKS PASSED". Runtime of the proof script:
6.0 to 25.3 seconds across three executions (wall clock varies
with machine load; every statistic below is deterministic and
was identical in all three runs; limit: about 10 minutes).
Fixed seed 34 throughout (numpy PCG64); every number below is
quoted verbatim from those runs.

## What was built

tools/admission_exam.py implements the charter exam from the Sleeve
Improvement Program 2026-11-14, Phase C, with each method cited in
its docstring:

1. PSR and DSR (Bailey and Lopez de Prado 2012, 2014). DSR deflates
   the observed Sharpe by SR0, the expected maximum Sharpe across
   N trials under the null, using the variance of trial Sharpes.
   The trial count is an effective count N_eff from correlation
   clustering: single-linkage clusters of the trial return matrix
   at |rho| >= 0.5, one cluster counting as one independent trial;
   a caller-supplied honest trial count larger than the matrix is
   scaled by the same cluster ratio.
2. CPCV PBO: combinatorial purged cross-validation, N = 10 groups,
   k = 2 test groups, 45 combinations, purge 1 bar on either side
   of each test block and embargo 1 further bar after it. PBO is
   the fraction of combinations where the in-sample best strategy
   ranks at or below the out-of-sample median (logit lambda <= 0).
3. Hansen SPA (2005) against a benchmark return series, studentized,
   stationary bootstrap (Politis and Romano 1994), consistent
   SPA_c recentering, callable against SPY and against QQQ series.
4. exam() entry point: strategy daily-return matrix (T x N),
   benchmark returns, honest trial count; outputs per-strategy
   DSR, the family PBO, SPA p-values per benchmark, and verdicts
   under the charter bars (promote: DSR >= 0.95 and PBO < 0.2 and
   SPA rejected at 0.05 vs every benchmark and, for new families,
   |t| > 3 per Harvey, Liu and Zhu 2016; family kill: PBO > 0.5).

## Proof numbers (verbatim from the run)

Synthetic fleet: 1,000 pure-noise strategies, iid normal daily
returns, T = 750, sigma 1 percent daily, zero true mean. Columns
0 to 199 share a common factor (loadings 0.6 to 0.9), forming one
correlation cluster. Benchmarks are synthetic SPY-like and
QQQ-like series from the same generator stream.

Noise fleet:

- N = 1000, T = 750, clusters = 801, N_eff = 801.0, var_sr = 0.001222
- SR0 (expected max Sharpe under the null) = 1.771 annualized
- Best noise strategy: column 658, in-sample Sharpe 2.037
  annualized, DSR = 0.676, verdict = KILL (family PBO > 0.5)
- Fleet PBO = 0.644 over 45 CPCV splits
- Family SPA p-values (noise fleet): SPY = 0.678, QQQ = 0.989
- Family verdict (noise fleet) = KILL
- CPCV subset statement: CPCV ran on the top 100 of 1000
  strategies by in-sample Sharpe; DSR and SPA ran on the full
  matrix. The subset is the most overfit-prone slice, so the PBO
  leg is conservative for the family.

Positive control (one planted genuine edge appended, trial
count 1,001):

- Planted true annualized Sharpe = 3.5 (stated before the run;
  daily mean 3.5/sqrt(252) times 1 percent, sigma 1 percent)
- Realized annualized Sharpe = 3.728, DSR = 0.999 at trial
  count 1001 (N_eff = 802.0)
- Planted |t| of mean return = 6.43 (clears the |t| > 3 hurdle)
- Planted-fleet PBO = 0.044 over the top 101 columns (the top
  100 noise strategies plus the planted one, which ranks first
  in-sample)

SPA sanity (single-strategy legs vs the SPY-like benchmark,
1,000 stationary-bootstrap resamples):

- Single noise strategy (column 290, the median in-sample
  Sharpe): statistic = 0.00, p = 0.529
- Single planted-edge strategy: statistic = 3.48, p = 0.000

Formula unit checks inside the same run: PSR evaluated at
SR* equal to the observed Sharpe returned exactly 0.500000;
SR0 at N = 1000 with var_sr = 1/749 returned 0.1189 daily
(1.888 annualized).

## The anchor, and where it did not reproduce exactly

Charter anchor: the best of 1,000 pure-noise strategies shows
Sharpe 2.23 and DSR 0.746. This run: Sharpe 2.037 and DSR 0.676.
The verdict is identical (refused, far below the 0.95 bar), but
the point values did not reproduce, and the reason is sampling,
not formula: 2.23 is one realized maximum from the source's
worked example, and the realized maximum of 1,000 draws varies
from fleet to fleet. Sensitivity recorded during the build:
across 39 probed seeds under the same protocol, the best noise
Sharpe ranged 1.526 to 2.177, its DSR ranged 0.194 to 0.734,
and the fleet PBO ranged 0.511 to 1.000. In all 39 fleets the
exam rejected the best noise strategy on DSR and the PBO sat
above the 0.5 kill bar. The anchor's implied SR0 (backed out of
2.23 and 0.746 at T = 750) is about 1.84 annualized, against
this module's theoretical 1.888 at var_sr = 1/749, so the
deflation machinery itself agrees with the anchor; the draw
differs.

One further honest note on the positive control: at 1,000
trials and T = 750, the deflation hurdle SR0 is itself about
1.8 annualized, so a planted true Sharpe near 2.0 could not
have passed DSR >= 0.95. The control therefore plants a true
Sharpe of 3.5. That is the exam working as chartered, and it
prices what a promotion claim must clear at this fleet size.

## Pre-registered fleet-level falsifier (Deep Dive Two, section 1.2)

The exam now makes the following test computable, and it is
registered here before any forward data exists. Pre-register
the next 100 paper strategies with, per strategy: in-sample
Sharpe, honest trial count (every variant anyone looked at,
including discarded ones), family, and publication status.
Prediction over the following 6 months, forward returns net of
modelled spread, graded vs SPY and QQQ as appropriate: the
DSR >= 0.95 subset will outperform the DSR < 0.95 subset by a
positive margin, and forward Sharpe will average at most 0.5x
in-sample for published families. If the DSR >= 0.95 subset
does not outperform, the finding is that the fleet's
trial-count accounting is dishonest (unlogged trials), not
that the exam needs a softer bar. Planning haircuts from the
same source stand until the fleet's own estimates replace
them: budget a new strategy at 0.42x its paper Sharpe if it is
a known published family, 0.74x if genuinely private and
pre-registered, and 0x until its DSR on the honest trial count
exceeds 0.95. Supporting replication context: Harvey, Liu and
Zhu's t > 3.0 hurdle for new families, and Hou, Xue and Zhang's
finding that a majority of 452 anomalies are insignificant
under one consistent method with microcap filters.

## Stated limits of the exam

- Daily returns only; the purge and embargo assume a one-day
  label horizon. A strategy whose label spans h days needs
  purge and embargo scaled to h before its PBO is believed.
- Sharpe-based throughout: no drawdown, tail, or capacity
  criterion. A strategy can pass this exam and still be
  untradeable on cost or capacity grounds.
- DSR is only as honest as the trial count fed to it. The
  matrix's own clustering cannot see variants that were run
  elsewhere and never logged; that is what the trial registry
  and the falsifier above are for.
- N_eff treats a whole correlation cluster as one trial
  (single linkage at |rho| >= 0.5). Chained clusters collapse
  even when their endpoints are weakly correlated, which
  deflates less than an eigenvalue-based count would in some
  fleets and more in others; the threshold is a stated
  convention, not an estimate.
- SPA studentization fixes omega at the sample long-run
  estimate (stationary bootstrap, mean block about 9 days at
  T = 750) rather than re-estimating it per resample, and the
  p-value resolution is 1 divided by the bootstrap count
  (0.001 at the proof's 1,000 resamples; p = 0.000 above means
  no resample exceeded the statistic, not a literal zero).
- CPCV PBO on a top-Sharpe subset measures the family's most
  overfit-prone slice, by design. A PBO computed on a random
  subset would read lower and mean less.
- The synthetic benchmarks in this proof validate the code,
  not any live claim. Live use requires real SPY and QQQ
  return series aligned to the strategy sample.

STATUS: GREEN, proven on the final artifacts. Evidence pointer:
tools/test_admission_exam.py run output, 2026-11-14, all checks
passed in three executions (6.0 to 25.3 seconds wall clock);
numbers above quoted from those runs.
