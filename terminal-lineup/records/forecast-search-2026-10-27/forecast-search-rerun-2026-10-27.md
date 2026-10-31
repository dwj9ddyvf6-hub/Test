# Forecast Factory P2 grade A: the rerun on the second dataset (2026-10-27)

Status: **PARTIAL.** Section 1 was written and committed before the rerun was executed (commit 3a823ac46); sections 2
onward were appended after it. The pre-registered rule was applied unchanged. 63 of run 1's 1,217 promoted cells are
graded A, 6 of them stock-direction avoid flags and 57 volatility cells; the second dataset shares its calendar with
run 1's holdout, so grade A here is not independent-in-time evidence (section 7).

## 1. Pre-registration (written before the run)

**Question.** Which of the 1,217 cells that run 1 promoted (grade B, `docs/research/forecast-search-2026-10-27.json`,
holdout key `5e165e4ceed72f145a7dd3e4`) replicate on a second dataset, so that they may be graded A?

**Run 1 is not touched.** Its holdout (2023-01-01 onward, DEEP) was opened once and logged; this rerun does not open,
read again or re-score it. Run 1's promoted list is read only as the fixed list of hypotheses to confirm.

**Second dataset.** The desk's split-adjusted daily cache (`cache/bars.tar.xz`, sha256
`5e8b1d314d055366f8c2b8e8bd047847f4df3e13c3551656e67baefb2677ae53`): 3,446 symbols, 2018-12-10 to 2026-10-16, with
most names starting 2023-02-27 (1,613) or 2024-05-13 (1,072). It is a different pull, universe and adjustment from DEEP
(6,385 segments, delisted names included), and the factory's code, forecasters, targets, contexts, costs, BH q and
gates are unchanged (search-p2-1). What it is NOT: independent in calendar time. Its 2023+ sessions are the same
market days as run 1's holdout, so a replication here tests the data pipeline, the universe and survivorship, and a
fresh split of the same period; it cannot test a new market regime. Grade A is worded accordingly.

**Names.** Common stock only: the cache's ETFs and funds are dropped (the explicit set `search_deep.CACHE_ETFS`, plus
every symbol DEEP's universe lists that DEEP's own ETF/fund filter dropped). SPY is the market series (taken from the
cache). No price or volume floor. The cache holds split-adjusted bars only, so adjusted and raw close and volume are
the same series (the P1 replay's precedent); dollar volume, and so tier, cost and capacity, are approximate for names
that split. Market inputs are the same files as run 1 (Cboe VIX, VIX3M, SKEW; SqueezeMetrics DIX/GEX, non-PIT).

**Windows (declared now).**
- Warm-up: sessions before 2024-03-01. Features and contexts need up to 252 prior sessions; rows with a missing input
  are excluded, never imputed.
- Discovery: every session before 2025-07-01 less the embargo (max of 45 calendar days and the label span +4 days;
  64 days at 60 sessions), that is the rows valid from about 2024-03 to 2025-04/05.
- Holdout: 2025-07-01 to the last session (2026-10-16): 327 sessions. It is opened once; the ledger key is the
  run key (search version, specs, data identity, split, fold unit) and a second opening is refused.
- Walk-forward: expanding **quarterly** folds inside discovery (the yearly folds of run 1 give fewer than the
  minimum 3 folds on a 15-month discovery); everything else as run 1 (agree share >= 0.70, pooled block t >= 2.0,
  at least 3 folds of at least 10 dates).
- Cell minimum 30 dates and 300 observations; BH q 0.10 over this run's own tested cells.
- Age: a name whose first bar falls on a date shared by at least 100 names (2023-02-27, 2024-05-13, 2024-06-25) is
  left-censored (age unknown, not "new"); other first bars are listings.

**Replication rule (the only verdicts that count).** A run-1 promoted cell is looked up by (forecaster, target, cell).
It is graded:
- **A (replicated)**: the cell is tested here, its discovery sign here equals run 1's, and it earns the rerun's own
  full verdict `promoted-B` (BH, walk-forward, holdout, costs, capacity). Nothing weaker is called A.
- **confirmed-directional**: not A, but the cell is tested here, the sign equals run 1's and the rerun holdout's
  signed block t is >= 2.0 (one-sided p <= 0.0228); reported beside A, never merged into it.
- **flipped**: tested here and the rerun holdout's signed block t is <= -2.0 against run 1's sign.
- **not replicated**: tested here, none of the above.
- **untestable**: the cell is under the minimum in the rerun (reported, not counted against the cell).

The replication rate is A / (A + confirmed-directional + flipped + not replicated), with untestable cells excluded
from the denominator and counted separately. A forecaster x target passes as a whole when at least half of its tested
promoted cells are A or confirmed-directional. Run 1's `all` cell of each forecaster x target is reported alone as
well, since it is the least cell-picked.

**No changes after seeing results.** The rule above, the windows and the filters are fixed. Any later change to code
that affects a number is recorded as a deviation in the results section, with the rerun repeated only if the deviation
is a defect, never a tuning.

## 2. The rerun

Holdout opened once: key `823be99705b4b483485e91ed` at 2026-10-27T16:30:39+0000 (discovery digest `b8811a8c3e34f398…`). Split 2025-07-01, fold unit quarter, embargo >= 45 days, BH q 0.1.
Data: 3,337 names, 2,543,994 bars, 2018-12-10 to 2026-10-16; panel 2,496,763 rows; 155 cross-sectional and 14 market specs (the registry has grown since run 1's 109 + 14).
Cells 21,345; tested 13,841; untested 7,504; passing BH 195. Verdicts: null-overall 13,240, untested 7,504, sign-flip 406, promoted-B 69, holdout-failed 43, holdout-insufficient 41, cost-failed 27, wf-failed 14, tiny 1.

## 3. Replication of run 1's promoted cells

Run 1 promoted 1,217 cells (grade B).

| grade | cells |
|---|---|
| A | 63 |
| confirmed | 337 |
| flipped | 0 |
| not-replicated | 564 |
| untestable | 253 |

Denominator (tested here, not untestable): 964. Replication rate: **A 6.5%**; A or confirmed 41.5%. Flipped (the rerun holdout significantly against run 1): 0.

## 4. By forecaster and target

| forecaster | target | promoted | A | confirmed | flipped | not replicated | untestable | passes |
|---|---|---|---|---|---|---|---|---|
| vol.garch | realized_vol_20 | 88 | 48 | 5 | 0 | 30 | 5 | yes |
| tai.pct | realized_vol_20 | 21 | 7 | 2 | 0 | 11 | 1 | no |
| veto.gapup10 | up_excess_5 | 71 | 2 | 50 | 0 | 13 | 6 | yes |
| avoid.pump | up_excess_20 | 77 | 2 | 36 | 0 | 21 | 18 | yes |
| vol.gex_pct | spy_rv_5 | 5 | 2 | 0 | 0 | 3 | 0 | no |
| veto.gapup10 | up_excess_20 | 55 | 1 | 26 | 0 | 18 | 10 | yes |
| avoid.deadcat | up_excess_20 | 65 | 1 | 25 | 0 | 15 | 24 | yes |
| avoid.jump25 | up_excess_20 | 66 | 0 | 31 | 0 | 29 | 6 | yes |
| veto.spikemem | up_excess_20 | 76 | 0 | 31 | 0 | 36 | 9 | no |
| avoid.surge2 | up_excess_20 | 65 | 0 | 28 | 0 | 32 | 5 | no |
| veto.panic | up_excess_20 | 59 | 0 | 23 | 0 | 15 | 21 | yes |
| veto.crashed | up_excess_20 | 34 | 0 | 18 | 0 | 12 | 4 | yes |
| avoid.x1p6 | up_excess_20 | 51 | 0 | 17 | 0 | 29 | 5 | no |
| veto.pump100 | up_excess_20 | 47 | 0 | 15 | 0 | 24 | 8 | no |
| avoid.mfi75 | up_excess_20 | 31 | 0 | 6 | 0 | 22 | 3 | no |
| avoid.stretch | up_excess_20 | 49 | 0 | 6 | 0 | 41 | 2 | no |
| avoid.idio | up_excess_20 | 20 | 0 | 5 | 0 | 10 | 5 | no |
| ap.regime | realized_vol_20 | 20 | 0 | 4 | 0 | 15 | 1 | no |
| avoid.newlist | up_excess_20 | 13 | 0 | 4 | 0 | 9 | 0 | no |
| veto.cgtph | up_excess_5 | 5 | 0 | 2 | 0 | 3 | 0 | no |
| alt.antichase | up_excess_20 | 6 | 0 | 1 | 0 | 5 | 0 | no |
| cs.correction | up_excess_20 | 2 | 0 | 1 | 0 | 1 | 0 | yes |
| sm.V | realized_vol_20 | 3 | 0 | 1 | 0 | 0 | 2 | yes |
| alt.antichase | up_excess_60 | 9 | 0 | 0 | 0 | 7 | 2 | no |
| avoid.deadcat | up_excess_60 | 24 | 0 | 0 | 0 | 4 | 20 | no |
| avoid.idio | up_excess_60 | 2 | 0 | 0 | 0 | 0 | 2 | no |
| avoid.jump25 | up_excess_60 | 28 | 0 | 0 | 0 | 25 | 3 | no |
| avoid.mfi75 | up_excess_60 | 7 | 0 | 0 | 0 | 6 | 1 | no |
| avoid.newlist | up_excess_60 | 4 | 0 | 0 | 0 | 4 | 0 | no |
| avoid.pump | up_excess_60 | 31 | 0 | 0 | 0 | 13 | 18 | no |
| avoid.r20 | up_excess_60 | 1 | 0 | 0 | 0 | 0 | 1 | no |
| avoid.stretch | up_excess_60 | 17 | 0 | 0 | 0 | 15 | 2 | no |
| avoid.surge2 | up_excess_60 | 32 | 0 | 0 | 0 | 22 | 10 | no |
| avoid.x1p6 | up_excess_60 | 24 | 0 | 0 | 0 | 14 | 10 | no |
| mom.volscaled | up_excess_60 | 1 | 0 | 0 | 0 | 0 | 1 | no |
| nvi.ema255 | up_excess_60 | 2 | 0 | 0 | 0 | 0 | 2 | no |
| risk.semidev | up_excess_60 | 2 | 0 | 0 | 0 | 0 | 2 | no |
| sr.hi52 | up_excess_60 | 5 | 0 | 0 | 0 | 3 | 2 | no |
| veto.cgtph | up_excess_20 | 1 | 0 | 0 | 0 | 1 | 0 | no |
| veto.crashed | up_excess_60 | 18 | 0 | 0 | 0 | 11 | 7 | no |
| veto.panic | up_excess_60 | 20 | 0 | 0 | 0 | 4 | 16 | no |
| veto.pump100 | up_excess_60 | 23 | 0 | 0 | 0 | 11 | 12 | no |
| veto.spikemem | up_excess_60 | 34 | 0 | 0 | 0 | 27 | 7 | no |
| vol.gex_pct | spy_rv_20 | 2 | 0 | 0 | 0 | 2 | 0 | no |
| vol.vix_ts | spy_rv_5 | 1 | 0 | 0 | 0 | 1 | 0 | no |

## 5. The pooled (`all`) cell of each forecaster and target

| forecaster | target | grade | rerun verdict | disc here | hold here (signed t) | hold run 1 (signed t) |
|---|---|---|---|---|---|---|
| avoid.deadcat | up_excess_20 | A | promoted-B | -0.0276 | +0.0457 (+5.9) | +0.0446 (+11.5) |
| avoid.deadcat | up_excess_60 | not-replicated | null-overall | -0.0314 | +0.0582 (—) | +0.0529 (+7.9) |
| avoid.idio | up_excess_20 | confirmed | null-overall | -0.0148 | +0.0194 (+6.8) | +0.0164 (+4.5) |
| avoid.jump25 | up_excess_20 | confirmed | null-overall | -0.0321 | +0.0796 (+3.7) | +0.0837 (+10.3) |
| avoid.jump25 | up_excess_60 | not-replicated | null-overall | -0.0268 | +0.1081 (—) | +0.1078 (+9.3) |
| avoid.mfi75 | up_excess_20 | confirmed | null-overall | -0.0165 | +0.0398 (+2.7) | +0.0386 (+5.8) |
| avoid.mfi75 | up_excess_60 | not-replicated | null-overall | -0.0078 | +0.0553 (—) | +0.0523 (+8.5) |
| avoid.newlist | up_excess_20 | not-replicated | null-overall | -0.0437 | +0.0364 (+1.5) | +0.0309 (+4.6) |
| avoid.newlist | up_excess_60 | not-replicated | null-overall | -0.0606 | +0.0595 (—) | +0.0528 (+6.4) |
| avoid.pump | up_excess_20 | A | promoted-B | -0.0308 | +0.0404 (+5.9) | +0.0422 (+10.5) |
| avoid.pump | up_excess_60 | not-replicated | null-overall | -0.0228 | +0.0515 (—) | +0.0515 (+13.5) |
| avoid.stretch | up_excess_20 | not-replicated | null-overall | -0.0219 | +0.0216 (+0.8) | +0.0340 (+3.6) |
| avoid.stretch | up_excess_60 | not-replicated | null-overall | -0.0107 | +0.0306 (—) | +0.0475 (+5.1) |
| avoid.surge2 | up_excess_20 | confirmed | null-overall | -0.0286 | +0.1111 (+3.8) | +0.1034 (+10.3) |
| avoid.surge2 | up_excess_60 | not-replicated | null-overall | -0.0352 | +0.1447 (—) | +0.1355 (+7.4) |
| avoid.x1p6 | up_excess_20 | confirmed | null-overall | -0.0126 | +0.0322 (+3.3) | +0.0355 (+6.8) |
| avoid.x1p6 | up_excess_60 | not-replicated | null-overall | -0.0111 | +0.0426 (—) | +0.0474 (+10.0) |
| sr.hi52 | up_excess_60 | not-replicated | null-overall | +0.0752 | +0.1928 (—) | +0.1626 (+3.4) |
| veto.crashed | up_excess_20 | confirmed | null-overall | -0.0311 | +0.1076 (+4.1) | +0.0895 (+10.4) |
| veto.crashed | up_excess_60 | not-replicated | null-overall | -0.0372 | +0.1505 (—) | +0.1192 (+7.8) |
| veto.gapup10 | up_excess_5 | confirmed | null-overall | -0.0127 | +0.0232 (+8.3) | +0.0230 (+18.1) |
| veto.gapup10 | up_excess_20 | confirmed | null-overall | -0.0129 | +0.0288 (+6.3) | +0.0301 (+11.3) |
| veto.panic | up_excess_20 | confirmed | null-overall | -0.0114 | +0.0306 (+5.4) | +0.0303 (+11.9) |
| veto.panic | up_excess_60 | not-replicated | null-overall | -0.0158 | +0.0370 (—) | +0.0372 (+10.5) |
| veto.pump100 | up_excess_20 | confirmed | null-overall | -0.0116 | +0.0357 (+4.0) | +0.0378 (+8.8) |
| veto.pump100 | up_excess_60 | not-replicated | null-overall | -0.0166 | +0.0467 (—) | +0.0488 (+10.8) |
| veto.spikemem | up_excess_20 | confirmed | null-overall | -0.0316 | +0.0979 (+4.6) | +0.0940 (+12.0) |
| veto.spikemem | up_excess_60 | not-replicated | null-overall | -0.0344 | +0.1247 (—) | +0.1251 (+9.0) |
| vol.garch | realized_vol_20 | A | promoted-B | +0.7108 | +0.8076 (+81.5) | +0.8037 (+137.9) |
| vol.gex_pct | spy_rv_5 | A | promoted-B | -0.3214 | +0.2069 (+3.4) | +0.2110 (+5.1) |
| vol.gex_pct | spy_rv_20 | not-replicated | holdout-failed | -0.2090 | +0.1062 (+1.2) | +0.1505 (+2.7) |

## 6. Cells graded A: 63

| forecaster | target | cell | sign | disc here | hold here (signed t) | net/opp here | hold run 1 (signed t) |
|---|---|---|---|---|---|---|---|
| avoid.deadcat | up_excess_20 | all | -1 | -0.0276 | +0.0457 (+5.9) | +0.0701 | +0.0446 (+11.5) |
| avoid.pump | up_excess_20 | all | -1 | -0.0308 | +0.0404 (+5.9) | +0.0700 | +0.0422 (+10.5) |
| avoid.pump | up_excess_20 | fear=calm|tier=q3 | -1 | -0.0522 | +0.0609 (+12.7) | +0.0741 | +0.0562 (+11.6) |
| veto.gapup10 | up_excess_20 | tier=q2 | -1 | -0.0367 | +0.0380 (+9.6) | +0.0688 | +0.0272 (+8.7) |
| veto.gapup10 | up_excess_5 | fear=calm|tier=q2 | -1 | -0.0365 | +0.0309 (+6.0) | +0.0269 | +0.0213 (+7.8) |
| veto.gapup10 | up_excess_5 | fear=fear|spy200=above_rising | -1 | -0.0210 | +0.0272 (+6.2) | +0.0301 | +0.0229 (+9.7) |
| tai.pct | realized_vol_20 | age=old|state=UP | +1 | +0.1842 | +0.1847 (+5.1) | — | +0.1755 (+11.2) |
| tai.pct | realized_vol_20 | fear=calm|state=UP | +1 | +0.2137 | +0.2029 (+4.5) | — | +0.1973 (+10.2) |
| tai.pct | realized_vol_20 | spy200=above_rising|state=UP | +1 | +0.1964 | +0.1842 (+4.2) | — | +0.1857 (+10.9) |
| tai.pct | realized_vol_20 | state=UP | +1 | +0.1841 | +0.1848 (+5.1) | — | +0.1755 (+11.2) |
| tai.pct | realized_vol_20 | state=UP|tier=q4 | +1 | +0.1518 | +0.1950 (+7.9) | — | +0.1816 (+11.2) |
| tai.pct | realized_vol_20 | state=UP|tier=q5 | +1 | +0.1412 | +0.2879 (+7.8) | — | +0.1839 (+9.8) |
| tai.pct | realized_vol_20 | state=UP|vix=mid | +1 | +0.1943 | +0.1921 (+4.6) | — | +0.1874 (+7.5) |
| vol.garch | realized_vol_20 | age=old | +1 | +0.7108 | +0.8076 (+81.5) | — | +0.8037 (+137.9) |
| vol.garch | realized_vol_20 | age=old|fear=calm | +1 | +0.7066 | +0.8055 (+50.3) | — | +0.8063 (+98.3) |
| vol.garch | realized_vol_20 | age=old|spy200=above_rising | +1 | +0.6940 | +0.8067 (+67.5) | — | +0.8072 (+119.0) |
| vol.garch | realized_vol_20 | age=old|state=RESET | +1 | +0.5447 | +0.6811 (+32.6) | — | +0.6519 (+58.4) |
| vol.garch | realized_vol_20 | age=old|state=UP | +1 | +0.6746 | +0.8005 (+82.9) | — | +0.7932 (+100.9) |
| vol.garch | realized_vol_20 | age=old|tier=q1 | +1 | +0.6240 | +0.6688 (+65.7) | — | +0.6837 (+99.6) |
| vol.garch | realized_vol_20 | age=old|tier=q2 | +1 | +0.6999 | +0.8091 (+97.5) | — | +0.7856 (+130.8) |
| vol.garch | realized_vol_20 | age=old|tier=q3 | +1 | +0.6927 | +0.7765 (+43.7) | — | +0.7879 (+97.2) |
| vol.garch | realized_vol_20 | age=old|tier=q4 | +1 | +0.7051 | +0.7524 (+45.1) | — | +0.7450 (+71.1) |
| vol.garch | realized_vol_20 | age=old|tier=q5 | +1 | +0.6554 | +0.7693 (+97.1) | — | +0.7301 (+75.6) |
| vol.garch | realized_vol_20 | age=old|vix=mid | +1 | +0.7193 | +0.8038 (+40.5) | — | +0.8027 (+73.6) |
| vol.garch | realized_vol_20 | all | +1 | +0.7108 | +0.8076 (+81.5) | — | +0.8037 (+137.9) |
| vol.garch | realized_vol_20 | fear=calm | +1 | +0.7066 | +0.8055 (+50.3) | — | +0.8063 (+98.3) |
| vol.garch | realized_vol_20 | fear=calm|spy200=above_rising | +1 | +0.6983 | +0.8055 (+50.3) | — | +0.8079 (+101.1) |
| vol.garch | realized_vol_20 | fear=calm|state=RESET | +1 | +0.4859 | +0.6779 (+18.6) | — | +0.6522 (+42.4) |
| vol.garch | realized_vol_20 | fear=calm|state=UP | +1 | +0.6776 | +0.7969 (+44.0) | — | +0.7951 (+70.9) |
| vol.garch | realized_vol_20 | fear=calm|tier=q1 | +1 | +0.6287 | +0.6670 (+46.0) | — | +0.6824 (+84.5) |
| vol.garch | realized_vol_20 | fear=calm|tier=q2 | +1 | +0.7005 | +0.8084 (+75.7) | — | +0.7864 (+97.6) |
| vol.garch | realized_vol_20 | fear=calm|tier=q3 | +1 | +0.6881 | +0.7759 (+35.0) | — | +0.7914 (+69.4) |
| vol.garch | realized_vol_20 | fear=calm|tier=q4 | +1 | +0.6929 | +0.7517 (+32.0) | — | +0.7493 (+49.1) |
| vol.garch | realized_vol_20 | fear=calm|tier=q5 | +1 | +0.6597 | +0.7641 (+34.4) | — | +0.7313 (+56.1) |
| vol.garch | realized_vol_20 | fear=calm|vix=mid | +1 | +0.7137 | +0.8022 (+98.1) | — | +0.8039 (+115.4) |
| vol.garch | realized_vol_20 | spy200=above_rising | +1 | +0.6940 | +0.8067 (+67.5) | — | +0.8072 (+119.0) |
| vol.garch | realized_vol_20 | spy200=above_rising|state=RESET | +1 | +0.4851 | +0.6785 (+28.1) | — | +0.6546 (+57.8) |
| vol.garch | realized_vol_20 | spy200=above_rising|state=UP | +1 | +0.6723 | +0.7989 (+56.1) | — | +0.7981 (+91.1) |
| vol.garch | realized_vol_20 | spy200=above_rising|tier=q1 | +1 | +0.6127 | +0.6689 (+47.6) | — | +0.6821 (+113.0) |
| vol.garch | realized_vol_20 | spy200=above_rising|tier=q2 | +1 | +0.6903 | +0.8086 (+90.0) | — | +0.7860 (+107.3) |
| vol.garch | realized_vol_20 | spy200=above_rising|tier=q3 | +1 | +0.6739 | +0.7756 (+42.1) | — | +0.7931 (+88.7) |
| vol.garch | realized_vol_20 | spy200=above_rising|tier=q4 | +1 | +0.6755 | +0.7512 (+42.6) | — | +0.7523 (+64.0) |
| vol.garch | realized_vol_20 | spy200=above_rising|tier=q5 | +1 | +0.6507 | +0.7670 (+62.3) | — | +0.7308 (+67.6) |
| vol.garch | realized_vol_20 | spy200=above_rising|vix=mid | +1 | +0.6934 | +0.8038 (+40.5) | — | +0.8054 (+81.4) |
| vol.garch | realized_vol_20 | state=RESET | +1 | +0.5447 | +0.6811 (+32.6) | — | +0.6519 (+58.4) |
| vol.garch | realized_vol_20 | state=UP | +1 | +0.6746 | +0.8005 (+82.9) | — | +0.7932 (+100.9) |
| vol.garch | realized_vol_20 | state=UP|tier=q2 | +1 | +0.7008 | +0.8068 (+100.6) | — | +0.8099 (+110.2) |
| vol.garch | realized_vol_20 | state=UP|tier=q3 | +1 | +0.6545 | +0.7612 (+60.2) | — | +0.7820 (+76.0) |
| vol.garch | realized_vol_20 | state=UP|tier=q4 | +1 | +0.6465 | +0.7778 (+62.8) | — | +0.7310 (+48.3) |
| vol.garch | realized_vol_20 | state=UP|tier=q5 | +1 | +0.6511 | +0.7961 (+44.5) | — | +0.7291 (+43.9) |
| vol.garch | realized_vol_20 | state=UP|vix=mid | +1 | +0.6882 | +0.7954 (+31.1) | — | +0.7939 (+49.5) |
| vol.garch | realized_vol_20 | tier=q1 | +1 | +0.6240 | +0.6688 (+65.7) | — | +0.6837 (+99.6) |
| vol.garch | realized_vol_20 | tier=q2 | +1 | +0.6999 | +0.8091 (+97.5) | — | +0.7856 (+130.8) |
| vol.garch | realized_vol_20 | tier=q2|vix=mid | +1 | +0.7093 | +0.8056 (+61.5) | — | +0.7870 (+93.7) |
| vol.garch | realized_vol_20 | tier=q3 | +1 | +0.6927 | +0.7765 (+43.7) | — | +0.7879 (+97.2) |
| vol.garch | realized_vol_20 | tier=q3|vix=mid | +1 | +0.7189 | +0.7735 (+26.9) | — | +0.7900 (+49.7) |
| vol.garch | realized_vol_20 | tier=q4 | +1 | +0.7051 | +0.7524 (+45.1) | — | +0.7450 (+71.1) |
| vol.garch | realized_vol_20 | tier=q4|vix=mid | +1 | +0.7266 | +0.7479 (+23.8) | — | +0.7509 (+30.8) |
| vol.garch | realized_vol_20 | tier=q5 | +1 | +0.6554 | +0.7693 (+97.1) | — | +0.7301 (+75.6) |
| vol.garch | realized_vol_20 | tier=q5|vix=mid | +1 | +0.6687 | +0.7558 (+22.1) | — | +0.7297 (+34.1) |
| vol.garch | realized_vol_20 | vix=mid | +1 | +0.7193 | +0.8038 (+40.5) | — | +0.8027 (+73.6) |
| vol.gex_pct | spy_rv_5 | all | -1 | -0.3214 | +0.2069 (+3.4) | — | +0.2110 (+5.1) |
| vol.gex_pct | spy_rv_5 | spy200=above_rising | -1 | -0.2330 | +0.1884 (+2.8) | — | +0.1747 (+5.0) |

## 7. Reading the result

**Power.** The rerun's discovery is about 15 months (valid rows from 2024-03 to the embargo before 2025-07-01) against
run 1's seven years, so its own BH gate is weak: 195 of 13841 cells pass BH (1.4%) against 2,986 of 11,150 (26.8%) in run 1.
Of the 964 run-1 promoted cells testable here, 815 are `null-overall` in the rerun (they did not clear BH on 15 months)
and 103 passed BH. A strict "promoted-B again" rule on this little data is therefore a low-power test, and A is a floor.

**Direction.** Where the rerun has a holdout t for a promoted cell (555 cells), 548 (98.7%) point the way run 1's sign
says, 446 (80.4%) have t >= 2, none has t <= -2, and the median t is +4.2. Random cells would split about half and half.
This is the `confirmed` tier (337 cells: 325 stock-direction flags, 12 volatility) and the 0 flipped. It shares calendar
with run 1's holdout (below), so it shows that the edge survives a different pull, universe and re-selection, not that it
survives a new market.

**What A is.** 63 cells: stock direction 6, all avoid flags (`avoid.deadcat` 20 sessions pooled; `avoid.pump` 20 sessions
pooled and in calm days at tier q3; `veto.gapup10` 20 sessions at tier q2, 5 sessions in calm q2 and in fear above a rising
200-day), and volatility 57 (`vol.garch` 48 of 88, `tai.pct` 7 of 21, `vol.gex_pct` 2 of 5 on spy_rv_5). A forecaster x target
passes as a whole (at least half of its tested promoted cells A or confirmed) in 10 of 45 pairs; the pooled `all` cell
is A for `avoid.deadcat`, `avoid.pump`, `vol.garch` (20 sessions) and `vol.gex_pct` (spy_rv_5), and `confirmed` for 11 more
(section 5).

**There is no long edge at A.** Every stock-direction A cell is an avoid flag. No buy-side cell (feature, momentum,
reset) replicated at A. The router can say AVOID today and BUY only if a long cell reaches A.

**Not independent in time.** The cache's 2023+ sessions are the market days of run 1's holdout. The rerun's discovery
(2024-03 to 2025-05) and holdout (2025-07 to 2026-10) both sit inside it. What the rerun does test: a separately pulled
and adjusted dataset of 3,337 names (DEEP: 6,385 segments with 944 delisted), the factory code on fresh splits, and the
cell definitions re-selected on data that run 1 never used for selection. Whether delisted names are absent from the cache
was not checked (UNVERIFIED); a survivors-only cache would, if anything, hide the worst losers an avoid flag is meant to
catch. Grade A therefore means: replicated on a second pull with its own pre-declared windows and the strict gates, with
the calendar overlap stated. The only clean test left is forward time (the P4 record).

**Selection in the utilities used later.** The cards of section 9 take their per-date utilities from the two holdouts,
which also served selection (run 1's gate; the rerun's gate for A). Their lower bounds are therefore optimistic, and the
router takes the lower of the two windows' bounds. The forward record is the unbiased check.

## 8. Deviations from the pre-registration

None in the rule, the windows or the filters. Facts the pre-registration could not state: the registry has grown since run
1 (155 cross-sectional and 14 market specs against 109 and 14; the vendors2 group is now searched), so the rerun's BH
family is larger than run 1's, which makes the strict test harder, not easier. The search module gained two parameters
(`split`, `wf_unit`; defaults reproduce run 1's key) and `tables()` gained the share of names beating the group mean (cards);
no number of run 1 changes. Cache bars were read through a local parquet copy of the same tarball members (identical
bars; the tarball's sha256 is in the data identity).

## 9. The promoted book

`tools/forecast_book.py` wrote `desk/forecast/frozen/promoted-book-1.json` (sha256
`56728a593611bee2835f9f7ee4766cee65b08a0b6336c34b6d2947b6241c1092`, pinned in freeze.PINS): 388 entries, 63 promoted (6
stock-direction, 57 volatility as risk context) and 325 probation (grade B, shown and never routed). Each stock-direction
entry carries a card per window (the rerun's holdout from 2025-07-01 and run 1's from 2023-01-01): observations, dates,
base rate, rate inside the set, lift, cost, and the per-date utility series. Example, `avoid.pump` 20 sessions pooled:
base rate 0.466, flagged names beat their group's mean 0.323 of the time (lift -0.143), 4.5 million observations on
932 dates (2023+) and 0.323 on 307 dates in the rerun window, mean avoided excess +7.3% and +7.0% per date.

## 10. Reproduce

`python3 -m tools.forecast_search --search --config <local JSON with cache, deep, vix, vix3m, skew, dix, holdout_root,
split 2025-07-01, wf_unit quarter> --workers 3`, then `python3 -m tools.forecast_book --run1
docs/research/forecast-search-2026-10-27.json --run2 docs/research/forecast-search-rerun-2026-10-27.json ...`. Rerun
holdout key `823be99705b4b483485e91ed`; run 1's key `5e165e4ceed72f145a7dd3e4` was not reopened.
