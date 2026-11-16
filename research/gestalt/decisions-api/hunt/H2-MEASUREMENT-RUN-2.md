# H2 MEASUREMENT RUN 2 (Sat 2026-11-14)

Workstream H2, measurement inventions at fleet scale. Research lane,
paper and shadow only, measurement only: no kill verdicts anywhere in
this run, per the tempering law. Method is run 1 verbatim wherever
run 1 exists (invention_workstreams.py, execution_alpha.py,
disagreement_index.py, entry_clv.py); extensions use the identical
machinery on additional series already on disk. Gross figures, costs
not deducted. Small samples are labeled anecdotes, never verdicts.
Machine outputs beside this report: nsm_fleet_v2.json,
decay_atlas_forward_seed.json, clv_twins_v2.json,
disagreement_index_v2.json. Compute script: h2_compute.py.
Data state: snapshot asof 2026-11-14T21:22:38Z; fill ledger 8,928
fills (2026-10-27 to 2026-11-13), unchanged since run 1; warm daily
bars end 2026-11-13.

## Part 1: Negative space mining, fleet extension

Coverage ledger. Attempted: every family with both a fire cohort and
a measurable near miss band in the gate distance and replay data on
disk. Included (11): absorption_base_ada, absorption_base_link,
absorption_spot_ada (new, ADA/USD 4H spot series, 546 bars),
absorption_spot_link (new), breakout_ada, breakout_link (new,
PF_LINKUSD 4H), breakout_spot_ada (new), breakout_spot_link (new),
rsi2_recovery_qqq, eth_sma200, btc_sma200 (new, BTC/USD daily fresh
cross). Excluded, named: RSI2 on SPY, IWM and other daily symbols
(no registered RSI2 gate family on those symbols in the gate
distance or replay data; unregistered variants not mined); funding
and Tensor margin families (gate distance probes exist, but no
replay machinery or forward price cohorts on disk, so no near miss
band is computable in this lane; this is a route limit, not a claim
that no band exists).

Cohort means, percent, fire vs near miss. 4H families at 1/3/6/12
bars (24 and 42 bar values in the JSON); Welch t at the 6 bar
horizon; triple barrier up share (2xATR14, vertical 30 bars).

| family | fire n | near n | fire 1/3/6/12 | near 1/3/6/12 | Welch t (6) | TB up fire/near |
|---|---|---|---|---|---|---|
| absorption_base_ada | 8 | 18 | -0.054 / -0.530 / -0.962 / -0.844 | +0.921 / +0.331 / +1.027 / +0.758 | -1.59 | 0.500 / 0.500 |
| absorption_base_link | 15 | 23 | +0.506 / +0.190 / +0.245 / +0.092 | +0.204 / +0.074 / +0.490 / -0.500 | -0.26 | 0.267 / 0.478 |
| absorption_spot_ada | 6 | 3 | -0.163 / -0.452 / -2.971 / -3.265 | -0.179 / -0.528 / +0.507 / -5.470 | -1.65 | 0.000 / 0.333 |
| absorption_spot_link | 6 | 2 | -0.511 / -0.326 / -0.357 / -1.733 | +1.065 / +0.767 / +1.362 / +0.355 | n/a (near n=2) | 0.500 / 0.000 |
| breakout_ada | 93 | 213 | +0.002 / +0.042 / -0.192 / -0.127 | +0.058 / -0.098 / +0.015 / -0.451 | -0.35 | 0.505 / 0.479 |
| breakout_link | 90 | 361 | -0.063 / -0.119 / -0.259 / -0.166 | +0.101 / +0.134 / -0.035 / +0.020 | -0.54 | 0.444 / 0.537 |
| breakout_spot_ada | 26 | 47 | -0.131 / +0.374 / +0.472 / +1.296 | +0.027 / +0.018 / -0.122 / -1.513 | +0.38 | 0.577 / 0.340 |
| breakout_spot_link | 19 | 69 | +0.158 / +0.055 / +0.035 / +0.255 | +0.275 / +0.383 / +0.053 / +0.158 | -0.01 | 0.474 / 0.507 |

Daily families at 1/5/10/20 sessions (3/6/12 session crosswalk in
the JSON); triple barrier vertical 5 sessions.

| family | fire n | near n | fire 1/5/10/20 | near 1/5/10/20 | Welch t (5) | TB up fire/near |
|---|---|---|---|---|---|---|
| rsi2_recovery_qqq | 15 | 15 | -0.014 / +0.713 / +1.959 / +1.278 | +0.459 / +1.040 / -0.084 / +0.902 | -0.27 | 0.133 / 0.333 |
| eth_sma200 | 1 | 2 | +3.304 / +10.297 / +9.180 / +10.369 | -1.747 / -12.954 / n/a / n/a | n/a | 1.000 / 0.000 |
| btc_sma200 | 1 | 7 | +5.340 / +13.952 / +12.875 / +13.184 | -1.473 / -2.751 / -5.184 / -11.421 | n/a (fire n=1) | 1.000 / 0.000 |

Readings, measurement only:

1. The five run 1 families reproduce run 1 exactly on the current
   snapshot (every mean above matches invention_run1 to the printed
   precision), except the ETH near miss 5 session mean, which moved
   from -11.86% (run 1) to -12.954% on the regenerated 21:22
   snapshot. The ETH fire cohort is identical. Both ETH cohorts and
   the BTC fire cohort are single digit anecdotes.
2. The ADA absorption pattern from run 1 (fires negative at 1/3/6/12,
   the 1.5 to 2.0 near miss band positive) does not generalize across
   the new families. Spot ADA absorption fires are worse than the PF
   fires at 6 and 12 bars (-2.971%, -3.265%, n=6, anecdote) but its
   near band (n=3) is mixed. Spot LINK absorption near band (n=2)
   sits above its fires at 1/3/6/12. No fleet wide inversion claim
   survives contact with the extension; the ADA PF result stays a
   family specific observation at n=8.
3. Breakout LINK (the largest new sample: fires n=90, near n=361) is
   indistinguishable to slightly inverted: near misses beat fires at
   1, 3, 12, 24 and 42 bars, Welch t between -0.32 and -1.08 at every
   horizon, triple barrier up share 0.537 near vs 0.444 fire. Same
   qualitative shape as breakout ADA in run 1 (indistinguishable),
   with a consistent small near miss edge that no single horizon
   separates from noise.
4. Breakout spot ADA is the one extension where fires clearly sit
   above near misses at the traded horizons: +1.296% vs -1.513% at
   12 bars, +2.442% vs -1.031% at 24 bars, triple barrier up share
   0.577 vs 0.340, Welch t +1.44 at 12 bars (fires n=26, near n=47).
   Interesting, not decisive: no horizon reaches t=2.
5. SMA200 crosses (ETH n=1, BTC n=1) remain anecdotes by
   construction. The near bands are the informative side at this
   sample: BTC approach days (n=7) average -11.421% at 20 sessions,
   ETH approach days (n=2) -12.954% at 5 sessions. Approaching the
   200 day line from below, in this history, preceded further
   downside; crossing it is too rare to grade.
6. RSI2 QQQ with the added crosswalk horizons: fires -0.243% at 3
   sessions and +1.324% at 6, +1.928% at 12; near band +1.301% at 3,
   +0.320% at 6, +0.718% at 12. The near band leads early, the fires
   lead late, Welch t at 5 sessions -0.27. Indistinguishable, as in
   run 1.

Registered falsifier state (unchanged, forward): near miss shadow
returns statistically indistinguishable from fires over a full
quarter means gate geometry carries no information either way. This
run is still replay era, in sample. No family is killed, promoted or
resized by anything here.

## Part 2: Decay atlas, forward edition seed

File: decay_atlas_forward_seed.json. It carries (a) the per family
decay table as it stands, recomputed on disk data, (b) the accrual
schema the nightly runs extend, and (c) the seed observations.

Replay fire decay (mean forward return, percent; median bar of
maximum favorable excursion inside the family window):

| family | n | 1 | 3 | 6 | 12 | 24 | 42 | median MFE bar |
|---|---|---|---|---|---|---|---|---|
| absorption_base_ada | 8 | -0.054 | -0.530 | -0.962 | -0.844 | -2.155 | -0.036 | 21 of 42 |
| absorption_base_link | 15 | +0.506 | +0.190 | +0.245 | +0.092 | +0.319 | +1.222 | 30 of 42 |
| absorption_spot_ada | 6 | -0.163 | -0.452 | -2.971 | -3.265 | -4.762 | -9.440 | 12 of 42 |
| absorption_spot_link | 6 | -0.511 | -0.326 | -0.357 | -1.733 | -2.496 | -2.737 | 13 of 42 |
| breakout_ada | 93 | +0.002 | +0.042 | -0.192 | -0.127 | -0.175 | -1.812 | 10 of 42 |
| breakout_link | 90 | -0.063 | -0.119 | -0.259 | -0.166 | +0.307 | +0.512 | 13 of 42 |
| breakout_spot_ada | 26 | -0.131 | +0.374 | +0.472 | +1.296 | +2.442 | -0.124 | 14 of 42 |
| breakout_spot_link | 19 | +0.158 | +0.055 | +0.035 | +0.255 | +1.960 | +1.757 | 16 of 42 |

Daily replay families (1/5/10/20 sessions, MFE window 20 sessions):
rsi2_recovery_qqq n=15: -0.014 / +0.713 / +1.959 / +1.278, median MFE
bar 10. eth_sma200 n=1: +3.304 / +10.297 / +9.180 / +10.369, MFE bar
8 (anecdote). btc_sma200 n=1: +5.340 / +13.952 / +12.875 / +13.184,
MFE bar 15 (anecdote).

Fill ledger daily grain (run 1 part b, recomputed; fills and warm
bars unchanged since run 1, so it reproduces run 1 exactly): 8,928
fills total, 50 buy fills used after filters, rejections no_series
2,241, price_disagreement 22, short_series 3,265. Only aster_other
clears the n=30 family bar: n=33 cells, +1 session -3.117% (win
share 0.364), +5 sessions -18.368% (win share 0.030), +10 sessions
-16.907% (win share 0.061). As run 1 established, this is one
concentrated basket population, not a fleet curve.

Accrual schema (full text in the JSON): one observation per
(family, symbol, date); multiple fills or fires inside a cell
collapse to the cell mean before any aggregate; fields family,
symbol, date, grain, event type, forward returns by horizon, MFE
bar, triple barrier label; horizons replay 4H [1,3,6,12,24,42],
replay daily [1,3,5,6,10,12,20], fill daily [1,5,10]; integrity
filters carried from run 1 (fill price within 25% of the series
close on its date, full horizon coverage required, symbol and date
must exist in the warm series, rejection counts reported every run,
never dropped silently). Seed observations: the 50 deduped fill
ledger cells and every replay fire event date per family.
Falsifier (registered): decay curves flat within noise for most
families on forward fires means timing carries no exploitable
structure here. Open row: the nightly accrual writer starts Mon
2026-11-16; the seed alone proves no forward decay claim.

## Part 3: Entry CLV deduped twins, fleet wide

Rule (entry CLV ledger v1, verbatim): one observation per (sleeve,
symbol, date); the cell value is the mean of that cell's fills; the
twin is the mean over cells. Applied to every aggregate in
runs/execution_alpha_v1.json and runs/attribution_ledger_v1.json.
Verification first: recomputing the raw markouts from the fill
ledger reproduces v1 exactly (entry +0.0017894053, n=5,024; exit
-0.0023729429, n=1,413), so the twins are computed on the same
population as the headlines they sit beside.

Estate headlines that change under dedupe:

| aggregate | raw | deduped twin | cells | effect |
|---|---|---|---|---|
| Execution alpha, estate entry markout +1 session | +0.1789% (n=5,024) | -1.4006% | 384 | SIGN FLIP |
| Execution alpha, estate exit markout +1 session | -0.2373% (n=1,413) | -0.1235% | 643 | same sign, magnitude halves |
| Entry CLV estate T0 (already twinned at source) | +0.4359% (n=5,041) | -0.6497% | 396 | SIGN FLIP (known from the Sunday program; restated) |
| Entry CLV estate T1 (already twinned at source) | +0.1773% (n=5,024) | -1.3927% | 384 | SIGN FLIP (restated) |
| Trip expectancy per trip, realized | +$466.56 (18 trips) | +$750.41 | 10 | size grows 61%; no flip |
| Trip expectancy per trip, bar path | +$1,046.95 | +$1,789.02 | 10 | size grows 71%; no flip |
| Trip expectancy per trip, execution component | -$580.38 | -$1,038.61 | 10 | size grows 79%; no flip |

The trip expectancy twins grow because the one suspect
aster_trader_donchian55 trip (flagged as an artifact in run 1) is 1
of 18 trips raw but 1 of 10 cells deduped: dedupe doubles the weight
of the least credible observation in the set. The twins are printed
as required; neither version of the 18 trip decomposition supports
a ranking claim, exactly as run 1 said.

Per sleeve flips and material size changes (v1 reported rows only;
material means sign flip, or the twin moves at least half the raw
magnitude, or at least 0.5 points):

SIGN FLIPS:
1. s_mn_hourly_1w entry markout: +7.4905% raw (n=184) to -13.4653%
   deduped (4 cells). The run 1 top three headline does not survive
   dedupe; 184 fills are 4 symbol days.
2. s_mn_macd entry markout: +1.6385% raw (n=175) to -4.7224%
   deduped (3 cells).
3. aster_saty_research exit markout: +0.1451% raw (n=234) to
   -3.1603% deduped (38 cells).
4. In the CLV ledger per sleeve table (already twinned at source,
   listed here because these are headline sized): s_mn_hourly_1w
   flips at both T0 (+2.6939% to -2.3317%, 4 cells) and T1
   (+7.4905% to -13.4653%, 4 cells; the T1 pair is the same
   computation as the execution alpha entry markout, and the two
   ledgers agree to the digit); s_mn_macd flips at T1 (+1.6385% to
   -4.7224%, 3 cells); aster_native_btc_eth_sma200 flips at T0
   (+0.5401% to -1.2100%, 4 cells) and T1 (+0.2205% to -0.4554%,
   4 cells); s_mn_reversal flips at T0 (-1.2084% to +0.4659%,
   9 cells) and T1 (+0.5589% to -4.8510%, 9 cells); bta_onebar_basket
   flips at T1 (-0.3409% to +0.0788%, 8 cells); s_mn_vwap flips at
   T1 (+1.7722% to -1.4432%, 3 cells). Nine sleeve horizon flips in
   total in the CLV table.

MATERIAL SIZE CHANGES, no flip:
5. red_day_reversal entry: -1.3616% raw (n=164) to -5.8932% deduped
   (13 cells). The bottom of the run 1 table gets four times worse.
6. aster_trader_donchian55 entry: +1.2604% raw (n=42) to +0.1476%
   deduped (14 cells), an 88% shrink.
7. capitulation exit: +1.4662% raw (n=45) to +0.1017% deduped
   (38 cells), a 93% shrink.
8. aster_etf_spy_monthly_c098 entry: +0.1260% raw (n=51) to
   +1.2017% deduped (10 cells); aster_etf_qqq_monthly_c098 entry:
   +0.1021% raw (n=49) to +0.8661% deduped (11 cells).
9. confluence exit: -0.5915% raw (n=39) to -2.5918% deduped
   (21 cells).
10. donchian trip expectancy (the sleeve, 4 trips, 2 cells):
    realized +$149.83 raw to +$222.65 deduped; execution component
    -$40.15 to -$58.37. Every other sleeve in the trip table has
    exactly 1 cell, so raw and twin are identical there by
    construction.

Headlines that SURVIVE dedupe, stated so the flip list is not read
as universal: aster_tensor_d20_tensor entry +8.4992% raw (n=282) to
+10.6717% deduped (12 cells); aster_tensor_d20_pv +7.8709% raw
(n=173) to +7.8031% deduped (9 cells), essentially unchanged;
tensor_swing entry -1.0871% raw (n=3,633) to -1.0691% deduped
(117 cells), so the dip buyer markout signature from run 1 is not a
basket artifact. The estate entry flip is driven by the s_mn basket
days and the reweighting of the large tensor_swing population from
3,633 fills to 117 cells, not by tensor_swing changing its own sign.

Attribution ledger disposition (339 rows): every aggregate is
either twinned, exempt with reason, or withdrawn with reason.
Expectancy and win rate per sleeve: WITHDRAWN for dedupe certified
use, because attribution_ledger_v1.json preserves only per sleeve
aggregates and the per close (symbol, date) rows needed to build
cells are not in the artifact; only 3 sleeves have any own closes
(aster_trader_donchian55: 8 closes, expectancy +$686.17;
bta_onebar_rth: 3 closes, +$220.45; bta_onebar_qqq: 2 closes,
-$150.25), so the affected population is named and tiny; unblocker
is a v1.1 ledger that preserves per close rows. Realized and excess
vs SPY dollar totals: twin equals raw by construction, because
dedupe reweights means and does not change sums. Counts (own
closes, wins, losses, fills, sessions, and the class counts NOT
FIRED 223, PARKED 54, LOW SAMPLE 62): exempt, counts have no fill
multiplicity to dedupe. Nothing else in the attribution ledger is a
mean over fills.

Full per sleeve twin tables (every sleeve, reported or not) are in
clv_twins_v2.json.

## Part 4: Disagreement index, accrual extension

File: disagreement_index_v2.json. Run 1 logic recomputed over the
full preserved fire history. The honest headline first: the fill
ledger on disk is unchanged since run 1 (8,928 fills, 2026-10-27 to
2026-11-13) and warm daily bars still end 2026-11-13, so the graded
population is the run 1 population; the extension is real as a
recomputation and a carried forward accrual base, and empty as new
data. The first generation capture now running accrues new symbol
days from Mon 2026-11-16.

Numbers (identical to run 1, as they must be on identical inputs):
269 symbol days carried entries; 68 had two or more sleeves opening;
25 had sleeves on both sides. Forward windows exist for 50 symbol
days at +1 session and 41 at +5.

Spearman(D, |forward return|): -0.2258 at +1 session, -0.1902 at +5
sessions.

Bucket means, |fwd| (and majority signed fwd):

| bucket | +1 n | +1 mean |fwd| | +1 majority signed | +5 n | +5 mean |fwd| | +5 majority signed |
|---|---|---|---|---|---|---|
| unanimous D=0 | 26 | 7.3685% | +1.0508% | 19 | 12.3700% | +8.5719% |
| mild 0<D<0.5 | 15 | 6.0912% | -1.1731% | 15 | 13.8803% | +12.9433% |
| split D>=0.5 | 9 | 2.2552% | -2.3756% | 7 | 4.6114% | +5.3272% |

Falsifier state, stated without story smoothing: the registered
kill condition is no forward relationship on any channel beyond
chance at 200 multi sleeve symbol days. At n=68 (50 graded at +1,
41 at +5) the falsifier is NOT TRIGGERED and the invention is NOT
CONFIRMED. The absolute channel still shows the run 1 direction
(disagreement predicts smaller moves, monotone across buckets at
+1, near monotone at +5 with the mild bucket on top), and the split
bucket at +1 is still n=9, an anecdote with a sign. Nothing in this
extension strengthens or weakens run 1; it fixes the accrual base
so the next graded symbol days land on a verified foundation.

## Verdict

STATUS: GREEN for the deliverable set as scoped (four parts
measured, four machine outputs written, every number above traceable
to its JSON). EVIDENCE POINTER: hunt/nsm_fleet_v2.json,
hunt/decay_atlas_forward_seed.json, hunt/clv_twins_v2.json,
hunt/disagreement_index_v2.json, computed by hunt/h2_compute.py;
raw recomputation checks against run 1 v1 pass exactly (execution
alpha estate entry and exit, all five run 1 NSM families).

Open rows, named:
1. Attribution expectancy and win rate twins: withdrawn pending a
   v1.1 attribution ledger that preserves per close (symbol, date)
   rows. Owner: attribution ledger lane.
2. Decay atlas and disagreement accruals start Mon 2026-11-16; both
   falsifiers are forward and untested until the accrual passes its
   registered sample (one full quarter for NSM shadow pricing; 200
   multi sleeve symbol days for the disagreement index).
3. Funding and Tensor margin near miss bands: no replay machinery on
   disk in this lane; named as a coverage gap, not an absence claim.
4. The s_mn basket day concentration (184 fills in 4 cells, 175 in
   3) is the single largest measurement hazard found in this run;
   any future estate aggregate printed without its deduped twin
   should be treated as unmeasured.
