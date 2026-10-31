# Forecast Factory P2 search on DEEP (2026-10-27 06:06)

Data: DEEP bars.parquet sha256 `cc6da0c128e34193…`, 6385 names, 11,565,543 bars, 2016-01-04 to 2026-10-19; market inputs dix, gex, skew, vix, vix3m (DIX/GEX: SqueezeMetrics DIX.csv, revised history, a validation fixture, non-PIT). Panel 11,473,681 rows. Split 2023-01-01, embargo ≥ 45 calendar days (longer for 60-session labels), BH q 0.1, cell minimum 30 dates and 300 observations.

Holdout opened once: key `5e165e4ceed72f145a7dd3e4` at 2026-10-27T05:54:18+0000 (discovery digest `428a215cffa64229…`).

## Headline

- Cells: 15,135 total; **11,150 tested** (m for BH); 3,985 untested (under the minimum).
- **Passing BH:** 2,986.
- Verdicts: null-overall 7,867, untested 3,985, promoted-B 1,217, holdout-failed 682, cost-failed 590, wf-failed 455, sign-flip 308, holdout-insufficient 24, tiny 7.

## Top 15 BH-passing cells by holdout effect, direction targets (up_excess, spy_ret)

Ranked by the holdout's signed block t; s̄ = the mean per-date statistic (IC for the cross-sectional lane), signed by the discovery sign.

| # | forecaster | target | cell | sign | disc s̄ (t) | q | WF agree, t | hold s̄ (t) | net/opp | capacity | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | veto.panic | up_excess_60 | spy200=above_rising|tier=q2 | -1 | -0.0239 (-7.3) | 0.004 | 1.0, +6.1 | +0.0439 (+33.6) | +0.1636 | $552,674 | promoted-B |
| 2 | avoid.jump25 | up_excess_60 | fear=calm|tier=q4 | -1 | -0.0535 (-3.1) | 0.065 | 1.0, +3.0 | +0.1393 (+23.8) | +0.1904 | $16,123,036 | promoted-B |
| 3 | xs.n9_up | up_excess_20 | fear=fear|vix=hi | +1 | +0.0398 (+2.9) | 0.079 | 1.0, +3.1 | +0.0698 (+23.1) | -0.0227 | $2,378,167 | cost-failed |
| 4 | avoid.pump | up_excess_60 | fear=calm|tier=q4 | -1 | -0.0317 (-5.0) | 0.018 | 1.0, +3.7 | +0.0717 (+23.0) | +0.2438 | $16,671,767 | promoted-B |
| 5 | avoid.surge2 | up_excess_60 | spy200=above_rising|tier=q3 | -1 | -0.0818 (-3.5) | 0.036 | 1.0, +2.3 | +0.1868 (+22.8) | +0.1502 | $3,319,795 | promoted-B |
| 6 | veto.panic | up_excess_60 | spy200=above_rising|tier=q3 | -1 | -0.0199 (-5.4) | 0.021 | 1.0, +5.8 | +0.0510 (+21.3) | +0.2197 | $3,682,328 | promoted-B |
| 7 | avoid.jump25 | up_excess_60 | spy200=above_rising|tier=q3 | -1 | -0.0638 (-3.5) | 0.036 | 1.0, +2.2 | +0.1625 (+20.4) | +0.1548 | $3,534,657 | promoted-B |
| 8 | avoid.jump25 | up_excess_60 | age=new | -1 | -0.0941 (-9.9) | 8e-06 | 1.0, +8.8 | +0.1749 (+19.9) | +0.1377 | $1,223,899 | promoted-B |
| 9 | veto.panic | up_excess_60 | spy200=above_rising | -1 | -0.0157 (-5.0) | 0.0092 | 1.0, +4.0 | +0.0387 (+19.9) | +0.1760 | $1,431,351 | promoted-B |
| 10 | veto.spikemem | up_excess_20 | fear=calm|tier=q3 | -1 | -0.0536 (-5.6) | 0.00012 | 1.0, +4.7 | +0.1273 (+19.5) | +0.0712 | $1,177,465 | promoted-B |
| 11 | avoid.surge2 | up_excess_60 | age=new|spy200=above_rising | -1 | -0.1267 (-6.1) | 0.0024 | 1.0, +4.3 | +0.1701 (+18.7) | +0.1120 | $702,959 | promoted-B |
| 12 | veto.gapup10 | up_excess_5 | all | -1 | -0.0177 (-15.4) | 0 | 1.0, +14.7 | +0.0230 (+18.1) | +0.0226 | $104,175 | promoted-B |
| 13 | veto.spikemem | up_excess_60 | spy200=above_rising|tier=q3 | -1 | -0.0773 (-5.1) | 0.0063 | 1.0, +3.6 | +0.1642 (+18.0) | +0.1672 | $3,506,090 | promoted-B |
| 14 | feat.F7neg | up_excess_60 | spy200=above_rising|state=RESET | -1 | -0.0571 (-3.1) | 0.066 | 0.8, +2.6 | +0.1318 (+17.9) | -0.0101 | $1,024,059 | cost-failed |
| 15 | feat.F3 | up_excess_20 | fear=fear|vix=hi | +1 | +0.0388 (+2.9) | 0.081 | 1.0, +3.1 | +0.0612 (+17.7) | -0.0266 | $2,085,457 | cost-failed |

## Top 15 BH-passing cells by holdout effect, volatility targets (realized_vol, spy_rv)

Ranked by the holdout's signed block t; s̄ = the mean per-date statistic (IC for the cross-sectional lane), signed by the discovery sign.

| # | forecaster | target | cell | sign | disc s̄ (t) | q | WF agree, t | hold s̄ (t) | net/opp | capacity | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | vol.garch | realized_vol_20 | spy200=above_rising|vix=lo | +1 | +0.7773 (+79.2) | 0 | 1.0, +35.6 | +0.8123 (+154.6) | — | — | promoted-B |
| 2 | vol.garch | realized_vol_20 | vix=lo | +1 | +0.7778 (+79.2) | 0 | 1.0, +39.2 | +0.8109 (+154.4) | — | — | promoted-B |
| 3 | vol.garch | realized_vol_20 | age=old|vix=lo | +1 | +0.7778 (+79.2) | 0 | 1.0, +39.2 | +0.8109 (+154.4) | — | — | promoted-B |
| 4 | vol.garch | realized_vol_20 | all | +1 | +0.7702 (+66.5) | 0 | 1.0, +55.9 | +0.8037 (+137.9) | — | — | promoted-B |
| 5 | vol.garch | realized_vol_20 | age=old | +1 | +0.7702 (+66.5) | 0 | 1.0, +55.9 | +0.8037 (+137.9) | — | — | promoted-B |
| 6 | vol.garch | realized_vol_20 | tier=q2 | +1 | +0.7751 (+58.5) | 0 | 1.0, +49.3 | +0.7856 (+130.8) | — | — | promoted-B |
| 7 | vol.garch | realized_vol_20 | age=old|tier=q2 | +1 | +0.7751 (+58.5) | 0 | 1.0, +49.3 | +0.7856 (+130.8) | — | — | promoted-B |
| 8 | vol.garch | realized_vol_20 | fear=fear|spy200=above_rising | +1 | +0.7536 (+49.9) | 3.2e-05 | 1.0, +51.0 | +0.8045 (+127.5) | — | — | promoted-B |
| 9 | vol.garch | realized_vol_20 | state=UP|tier=q1 | +1 | +0.7648 (+73.1) | 0 | 1.0, +64.2 | +0.8142 (+120.4) | — | — | promoted-B |
| 10 | vol.garch | realized_vol_20 | spy200=above_rising | +1 | +0.7683 (+72.8) | 0 | 1.0, +58.4 | +0.8072 (+119.0) | — | — | promoted-B |
| 11 | vol.garch | realized_vol_20 | age=old|spy200=above_rising | +1 | +0.7683 (+72.8) | 0 | 1.0, +58.4 | +0.8072 (+119.0) | — | — | promoted-B |
| 12 | vol.garch | realized_vol_20 | fear=calm|vix=lo | +1 | +0.7777 (+85.8) | 0 | 1.0, +39.2 | +0.8121 (+119.0) | — | — | promoted-B |
| 13 | vol.garch | realized_vol_20 | fear=calm|vix=mid | +1 | +0.7784 (+86.6) | 0 | 1.0, +72.3 | +0.8039 (+115.4) | — | — | promoted-B |
| 14 | vol.garch | realized_vol_20 | spy200=above_rising|tier=q1 | +1 | +0.7462 (+63.6) | 0 | 1.0, +53.4 | +0.6821 (+113.0) | — | — | promoted-B |
| 15 | vol.garch | realized_vol_20 | state=UP|tier=q2 | +1 | +0.7713 (+79.7) | 0 | 1.0, +67.7 | +0.8099 (+110.2) | — | — | promoted-B |


## Promoted (grade B; A needs a second dataset): 1217

- vol.garch → realized_vol_20: 88 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=mid …)
- avoid.pump → up_excess_20: 77 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=mid …)
- veto.spikemem → up_excess_20: 76 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=mid …)
- veto.gapup10 → up_excess_5: 71 cells (all, fear=fear, fear=calm, spy200=above_rising, spy200=below, vix=lo …)
- avoid.jump25 → up_excess_20: 66 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=hi …)
- avoid.deadcat → up_excess_20: 65 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=mid …)
- avoid.surge2 → up_excess_20: 65 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=hi …)
- veto.panic → up_excess_20: 59 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=mid …)
- veto.gapup10 → up_excess_20: 55 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=mid …)
- avoid.x1p6 → up_excess_20: 51 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=hi …)
- avoid.stretch → up_excess_20: 49 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=hi …)
- veto.pump100 → up_excess_20: 47 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=lo, vix=hi …)
- veto.crashed → up_excess_20: 34 cells (all, fear=calm, spy200=above_rising, vix=lo, vix=mid, tier=q2 …)
- veto.spikemem → up_excess_60: 34 cells (all, fear=calm, spy200=above_rising, tier=q1, tier=q2, tier=q3 …)
- avoid.surge2 → up_excess_60: 32 cells (all, fear=calm, tier=q1, tier=q2, tier=q3, tier=q4 …)
- avoid.mfi75 → up_excess_20: 31 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=hi, tier=q2 …)
- avoid.pump → up_excess_60: 31 cells (all, fear=calm, spy200=above_rising, tier=q1, tier=q2, tier=q3 …)
- avoid.jump25 → up_excess_60: 28 cells (all, fear=calm, spy200=above_rising, tier=q2, tier=q3, tier=q4 …)
- avoid.deadcat → up_excess_60: 24 cells (all, fear=calm, spy200=above_rising, tier=q2, tier=q3, age=new …)
- avoid.x1p6 → up_excess_60: 24 cells (all, fear=calm, spy200=above_rising, tier=q2, tier=q3, tier=q4 …)
- veto.pump100 → up_excess_60: 23 cells (all, fear=calm, spy200=above_rising, tier=q3, tier=q4, tier=q5 …)
- tai.pct → realized_vol_20: 21 cells (fear=fear, state=UP, state=RESET, fear=fear|vix=hi, age=old|fear=fear, fear=fear|state=UP …)
- ap.regime → realized_vol_20: 20 cells (tier=q3, state=UP, fear=calm|tier=q2, fear=calm|tier=q3, fear=calm|tier=q4, fear=calm|state=UP …)
- avoid.idio → up_excess_20: 20 cells (all, spy200=above_rising, tier=q2, tier=q3, age=new, age=old …)
- veto.panic → up_excess_60: 20 cells (all, fear=calm, spy200=above_rising, tier=q2, tier=q3, age=new …)
- veto.crashed → up_excess_60: 18 cells (all, spy200=above_rising, tier=q2, tier=q3, age=old, fear=calm|spy200=above_rising …)
- avoid.stretch → up_excess_60: 17 cells (all, tier=q1, tier=q2, tier=q3, tier=q4, age=new …)
- avoid.newlist → up_excess_20: 13 cells (all, fear=fear, fear=calm, spy200=above_rising, vix=hi, tier=q2 …)
- alt.antichase → up_excess_60: 9 cells (tier=q3, tier=q4, state=UP, fear=calm|spy200=above_rising, age=old|tier=q3, age=old|tier=q4 …)
- avoid.mfi75 → up_excess_60: 7 cells (all, tier=q3, age=old, fear=calm|spy200=above_rising, spy200=above_rising|tier=q3, age=old|tier=q3 …)
- alt.antichase → up_excess_20: 6 cells (fear=calm, state=UP, spy200=above_rising|state=UP, state=UP|tier=q1, state=UP|tier=q4, age=old|state=UP)
- sr.hi52 → up_excess_60: 5 cells (all, age=old, fear=calm|spy200=above_rising, fear=calm|state=RESET, spy200=above_rising|state=RESET)
- veto.cgtph → up_excess_5: 5 cells (tier=q2, fear=fear|tier=q2, spy200=above_rising|tier=q2, age=old|tier=q2, state=UP|tier=q2)
- vol.gex_pct → spy_rv_5: 5 cells (all, fear=calm, spy200=above_rising, vix=mid, fear=calm|spy200=above_rising)
- avoid.newlist → up_excess_60: 4 cells (all, spy200=above_rising, tier=q1, spy200=above_rising|tier=q2)
- sm.V → realized_vol_20: 3 cells (age=new|tier=q3, state=UP|tier=q1, state=RESET|tier=q2)
- avoid.idio → up_excess_60: 2 cells (state=UP, age=old|state=UP)
- cs.correction → up_excess_20: 2 cells (fear=calm|state=RESET, spy200=above_rising|state=RESET)
- nvi.ema255 → up_excess_60: 2 cells (fear=calm|state=RESET, spy200=above_rising|state=RESET)
- risk.semidev → up_excess_60: 2 cells (fear=calm|state=RESET, spy200=above_rising|state=RESET)
- vol.gex_pct → spy_rv_20: 2 cells (all, fear=calm)
- avoid.r20 → up_excess_60: 1 cells (state=RESET|tier=q2)
- mom.volscaled → up_excess_60: 1 cells (age=new|spy200=above_rising)
- veto.cgtph → up_excess_20: 1 cells (state=UP|tier=q2)
- vol.vix_ts → spy_rv_5: 1 cells (vix=mid)

## Sign flips in the holdout (X): 308

- avoid.mfi75 → up_excess_20 in spy200=above_rising|state=RESET: disc +0.0002 (t -0.3), hold signed t -11.9
- avoid.mfi75 → up_excess_20 in fear=calm|state=RESET: disc +0.0062 (t -0.3), hold signed t -9.2
- avoid.mfi75 → up_excess_20 in state=RESET|vix=lo: disc +0.0037 (t +1.0), hold signed t -7.0
- feat.N5neg → up_excess_20 in spy200=above_rising|tier=q4: disc +0.0175 (t +1.7), hold signed t -6.9
- feat.F6 → up_excess_60 in tier=q4: disc +0.0013 (t -0.1), hold signed t -6.5
- feat.F6 → up_excess_60 in age=old|tier=q4: disc +0.0015 (t -0.4), hold signed t -6.2
- chk.px_dema200 → up_excess_20 in age=old|state=RESET: disc -0.0044 (t -0.3), hold signed t -6.0
- chk.px_dema200 → up_excess_20 in state=RESET: disc -0.0045 (t -0.3), hold signed t -6.0
- avoid.mfi75 → up_excess_20 in state=RESET|vix=mid: disc +0.0183 (t +0.4), hold signed t -5.8
- xs.n9_up → up_excess_60 in fear=calm|tier=q4: disc +0.0034 (t +1.1), hold signed t -5.7
- avoid.mfi75 → up_excess_60 in age=new|spy200=above_rising: disc +0.0007 (t +0.2), hold signed t -5.3
- qc.streak → up_excess_5 in spy200=above_rising|state=RESET: disc -0.0060 (t -1.5), hold signed t -5.3
- chk.trendclip → up_excess_60 in spy200=above_rising|tier=q1: disc -0.0070 (t -0.1), hold signed t -5.2
- veto.crashed → up_excess_20 in state=RESET|tier=q4: disc +0.0180 (t +0.9), hold signed t -5.1
- chk.vol30_90 → up_excess_20 in age=new|vix=hi: disc +0.0088 (t +0.8), hold signed t -5.1

## Pooled cell (all) per forecaster and target

| forecaster | target | disc s̄ (t) | q | WF | hold s̄ signed (t) | net/opp | verdict |
|---|---|---|---|---|---|---|---|
| alt.antichase | up_excess_20 | -0.0155 (-2.3) | 0.11 | 1.0, +1.9 | +0.0241 (+3.0) | +0.0078 | null-overall |
| alt.antichase | up_excess_60 | -0.0208 (-4.6) | 0.0066 | 0.833, +4.1 | +0.0340 (+1.9) | +0.0197 | holdout-failed |
| ap.regime | realized_vol_20 | +0.0298 (+1.8) | 0.2 | 0.667, +1.2 | -0.0052 (-0.9) | — | null-overall |
| ap.trend | up_excess_20 | -0.0122 (-0.3) | 0.86 | 1.0, +0.4 | -0.0057 (-0.2) | -0.0441 | null-overall |
| ap.trend | up_excess_5 | -0.0104 (-2.3) | 0.091 | 0.833, +2.0 | -0.0020 (-0.1) | -0.0425 | holdout-failed |
| avoid.deadcat | up_excess_20 | -0.0206 (-6.8) | 1e-06 | 1.0, +6.3 | +0.0446 (+11.5) | +0.0670 | promoted-B |
| avoid.deadcat | up_excess_60 | -0.0246 (-6.3) | 0.00076 | 1.0, +5.7 | +0.0529 (+7.9) | +0.1498 | promoted-B |
| avoid.idio | up_excess_20 | -0.0111 (-3.9) | 0.0064 | 1.0, +3.4 | +0.0164 (+4.5) | +0.0344 | promoted-B |
| avoid.idio | up_excess_60 | -0.0115 (-1.6) | 0.3 | 0.833, +1.3 | +0.0235 (+5.7) | +0.0906 | null-overall |
| avoid.jump25 | up_excess_20 | -0.0385 (-6.7) | 2e-06 | 1.0, +6.2 | +0.0837 (+10.3) | +0.0503 | promoted-B |
| avoid.jump25 | up_excess_60 | -0.0470 (-6.2) | 0.00061 | 0.833, +5.6 | +0.1078 (+9.3) | +0.1138 | promoted-B |
| avoid.mfi75 | up_excess_20 | -0.0199 (-4.1) | 0.0026 | 1.0, +4.4 | +0.0386 (+5.8) | +0.0152 | promoted-B |
| avoid.mfi75 | up_excess_60 | -0.0168 (-3.2) | 0.037 | 1.0, +2.9 | +0.0523 (+8.5) | +0.0399 | promoted-B |
| avoid.newlist | up_excess_20 | -0.0337 (-4.2) | 0.0025 | 1.0, +3.8 | +0.0309 (+4.6) | +0.0140 | promoted-B |
| avoid.newlist | up_excess_60 | -0.0514 (-3.0) | 0.058 | 1.0, +2.7 | +0.0528 (+6.4) | +0.0572 | promoted-B |
| avoid.pump | up_excess_20 | -0.0243 (-11.0) | 0 | 1.0, +10.3 | +0.0422 (+10.5) | +0.0728 | promoted-B |
| avoid.pump | up_excess_60 | -0.0252 (-9.1) | 3.2e-05 | 1.0, +9.1 | +0.0515 (+13.5) | +0.1503 | promoted-B |
| avoid.r20 | up_excess_20 | -0.0104 (-0.0) | 0.99 | 0.667, +0.0 | -0.0208 (-2.0) | -0.0656 | null-overall |
| avoid.r20 | up_excess_60 | +0.0090 (+1.2) | 0.43 | 0.833, -0.7 | +0.0283 (+0.9) | -0.0526 | null-overall |
| avoid.stretch | up_excess_20 | -0.0307 (-5.7) | 3.2e-05 | 1.0, +5.6 | +0.0340 (+3.6) | +0.0111 | promoted-B |
| avoid.stretch | up_excess_60 | -0.0315 (-5.1) | 0.0034 | 0.833, +4.6 | +0.0475 (+5.1) | +0.0224 | promoted-B |
| avoid.surge2 | up_excess_20 | -0.0497 (-6.6) | 3e-06 | 1.0, +6.2 | +0.1034 (+10.3) | +0.0360 | promoted-B |
| avoid.surge2 | up_excess_60 | -0.0623 (-5.4) | 0.0022 | 0.833, +5.0 | +0.1355 (+7.4) | +0.0959 | promoted-B |
| avoid.x1p6 | up_excess_20 | -0.0216 (-7.9) | 0 | 1.0, +7.5 | +0.0355 (+6.8) | +0.0704 | promoted-B |
| avoid.x1p6 | up_excess_60 | -0.0254 (-6.6) | 0.00052 | 1.0, +6.3 | +0.0474 (+10.0) | +0.1396 | promoted-B |
| chk.cmf21 | up_excess_20 | +0.0062 (+1.1) | 0.45 | 0.833, +1.5 | +0.0295 (+4.1) | -0.0384 | null-overall |
| chk.cmf21 | up_excess_60 | +0.0228 (+3.8) | 0.016 | 0.833, +1.4 | +0.0384 (+2.8) | -0.0426 | wf-failed |
| chk.dema_roc42 | up_excess_20 | -0.0277 (-2.1) | 0.13 | 1.0, +2.0 | +0.0021 (+0.3) | -0.0503 | null-overall |
| chk.dema_roc42 | up_excess_60 | -0.0205 (-0.4) | 0.83 | 0.6, -0.4 | +0.0108 (+1.5) | -0.0426 | null-overall |
| chk.px_dema200 | up_excess_20 | -0.0124 (-0.4) | 0.8 | 0.833, -0.1 | -0.0090 (-1.3) | -0.0666 | null-overall |
| chk.px_dema200 | up_excess_60 | +0.0088 (+0.6) | 0.73 | 0.6, -2.7 | +0.0132 (+0.4) | -0.0492 | null-overall |
| chk.rs126 | up_excess_20 | +0.0291 (+2.8) | 0.042 | 1.0, +2.7 | +0.0644 (+5.0) | -0.0374 | cost-failed |
| chk.rs126 | up_excess_60 | +0.0525 (+4.2) | 0.011 | 0.833, +2.1 | +0.0912 (+3.7) | -0.0322 | cost-failed |
| chk.tech5 | up_excess_20 | -0.0220 (-1.8) | 0.2 | 1.0, +1.1 | +0.0172 (+2.4) | -0.0290 | null-overall |
| chk.tech5 | up_excess_60 | -0.0097 (-0.4) | 0.81 | 0.75, +1.3 | +0.0203 (+1.6) | -0.0261 | null-overall |
| chk.trendclip | up_excess_20 | +0.0140 (+1.1) | 0.46 | 0.833, +0.6 | +0.0377 (+4.6) | -0.0337 | null-overall |
| chk.trendclip | up_excess_60 | -0.0019 (-0.3) | 0.87 | 0.4, -1.9 | -0.0482 (-3.8) | -0.0058 | sign-flip |
| chk.vol30_90 | up_excess_20 | +0.0067 (+0.8) | 0.63 | 0.667, +0.5 | -0.0162 (-3.2) | -0.0650 | sign-flip |
| chk.vol30_90 | up_excess_60 | +0.0075 (+0.1) | 0.97 | 0.833, +0.2 | -0.0138 (-0.4) | -0.0808 | null-overall |
| cs.correction | up_excess_20 | +0.0008 (-0.8) | 0.63 | 0.5, -0.8 | -0.0164 (-2.6) | -0.0572 | sign-flip |
| cs.correction | up_excess_5 | +0.0019 (+1.3) | 0.39 | 0.667, +1.2 | -0.0092 (-2.3) | -0.0513 | sign-flip |
| eg.gapfill | up_excess_20 | +0.0023 (-0.5) | 0.77 | 0.667, -0.9 | -0.0037 (-1.2) | -0.0492 | null-overall |
| eg.gapfill | up_excess_5 | +0.0081 (+4.4) | 0.00043 | 1.0, +4.0 | +0.0047 (+1.5) | -0.0450 | holdout-failed |
| eg.pdr_break | up_excess_20 | -0.0072 (-0.6) | 0.74 | 0.833, +0.1 | -0.0009 (+0.4) | -0.0447 | null-overall |
| eg.pdr_break | up_excess_5 | -0.0136 (-4.8) | 7.6e-05 | 1.0, +4.4 | +0.0048 (+0.8) | -0.0421 | holdout-failed |
| feat.F3 | up_excess_20 | +0.0210 (+2.3) | 0.099 | 1.0, +1.7 | +0.0122 (+2.9) | -0.0337 | wf-failed |
| feat.F3 | up_excess_60 | +0.0134 (+0.8) | 0.61 | 0.6, -0.3 | +0.0081 (+0.9) | -0.0337 | null-overall |
| feat.F6 | up_excess_20 | +0.0139 (+2.0) | 0.15 | 0.833, +2.0 | +0.0087 (+1.4) | -0.0484 | null-overall |
| feat.F6 | up_excess_60 | +0.0143 (+2.2) | 0.15 | 1.0, +2.0 | +0.0068 (+1.6) | -0.0579 | null-overall |
| feat.F7neg | up_excess_20 | +0.0124 (+0.4) | 0.83 | 0.667, -0.1 | -0.0110 (-0.6) | -0.0625 | null-overall |
| feat.F7neg | up_excess_60 | -0.0019 (-0.9) | 0.55 | 0.833, -0.3 | +0.0241 (+1.3) | -0.0539 | null-overall |
| feat.N1 | up_excess_20 | +0.0158 (+2.1) | 0.14 | 1.0, +1.8 | +0.0079 (+2.3) | -0.0351 | null-overall |
| feat.N1 | up_excess_60 | +0.0079 (+0.6) | 0.73 | 0.8, +1.1 | +0.0025 (+0.6) | -0.0351 | null-overall |
| feat.N5neg | up_excess_20 | +0.0138 (-0.3) | 0.89 | 1.0, -0.0 | -0.0034 (+0.5) | -0.0602 | null-overall |
| feat.N5neg | up_excess_60 | +0.0037 (+1.5) | 0.42 | 0.25, — | -0.0130 (—) | -0.0644 | null-overall |
| feat.N7 | up_excess_20 | +0.0137 (+3.3) | 0.017 | 1.0, +3.3 | +0.0132 (+1.7) | -0.0391 | holdout-failed |
| feat.N7 | up_excess_60 | +0.0200 (+3.5) | 0.027 | 1.0, +3.2 | +0.0218 (+1.3) | -0.0375 | holdout-failed |
| ict.c2 | up_excess_20 | -0.0040 (-2.6) | 0.058 | 1.0, +2.7 | +0.0040 (+2.8) | -0.0390 | cost-failed |
| ict.c2 | up_excess_5 | -0.0037 (-2.3) | 0.088 | 1.0, +2.4 | +0.0004 (-0.1) | -0.0396 | holdout-failed |
| ict.c2cisd | up_excess_20 | -0.0028 (-0.1) | 0.94 | 0.667, -0.2 | -0.0006 (+0.3) | -0.0431 | null-overall |
| ict.c2cisd | up_excess_5 | -0.0045 (-3.9) | 0.002 | 1.0, +3.7 | +0.0005 (+0.1) | -0.0428 | holdout-failed |
| idx.dix_pct | spy_ret_20 | +0.0030 (+1.3) | 0.39 | 0.667, +0.5 | -0.0005 (+0.4) | -0.0018 | null-overall |
| idx.dix_pct | spy_ret_60 | -0.0020 (+0.4) | 0.83 | 0.5, +0.1 | -0.0003 (+0.7) | +0.0030 | null-overall |
| idx.skew_pct | spy_ret_20 | -0.0004 (-0.3) | 0.89 | 0.333, +0.1 | +0.0033 (-0.8) | +0.0002 | null-overall |
| idx.vrp | spy_ret_20 | -0.0024 (-0.3) | 0.86 | 0.333, -0.9 | +0.0051 (+0.6) | +0.0010 | null-overall |
| idx.vrp | spy_ret_60 | -0.0091 (-0.8) | 0.63 | 0.5, -1.7 | +0.0078 (+0.7) | -0.0045 | null-overall |
| mom.r126 | up_excess_20 | +0.0291 (+2.8) | 0.042 | 1.0, +2.7 | +0.0644 (+5.0) | -0.0374 | cost-failed |
| mom.r126 | up_excess_60 | +0.0525 (+4.2) | 0.011 | 0.833, +2.1 | +0.0912 (+3.7) | -0.0322 | cost-failed |
| mom.r126_21 | up_excess_20 | +0.0358 (+3.0) | 0.026 | 1.0, +2.6 | +0.0647 (+5.2) | -0.0373 | cost-failed |
| mom.r126_21 | up_excess_60 | +0.0559 (+4.5) | 0.0071 | 0.833, +2.5 | +0.0914 (+4.1) | -0.0300 | cost-failed |
| mom.r5 | up_excess_20 | -0.0122 (-0.4) | 0.83 | 0.667, -0.2 | -0.0066 (-0.4) | -0.0608 | null-overall |
| mom.r5 | up_excess_5 | -0.0171 (-3.7) | 0.0037 | 1.0, +3.5 | -0.0014 (+0.2) | -0.0575 | holdout-failed |
| mom.resid126 | up_excess_20 | +0.0124 (+1.7) | 0.23 | 0.833, +0.4 | +0.0277 (+1.8) | -0.0329 | null-overall |
| mom.resid126 | up_excess_60 | +0.0271 (+1.4) | 0.34 | 0.8, +0.6 | +0.0385 (+0.8) | -0.0287 | null-overall |
| mom.volscaled | up_excess_20 | +0.0267 (+2.4) | 0.079 | 1.0, +2.2 | +0.0579 (+4.2) | -0.0235 | cost-failed |
| mom.volscaled | up_excess_60 | +0.0502 (+3.3) | 0.034 | 0.833, +1.7 | +0.0839 (+2.6) | -0.0170 | wf-failed |
| nvi.ema255 | up_excess_20 | +0.0645 (+3.8) | 0.0056 | 1.0, +3.6 | +0.1247 (+5.9) | -0.0157 | cost-failed |
| nvi.ema255 | up_excess_60 | +0.0876 (+2.9) | 0.061 | 0.8, +2.4 | +0.1709 (+5.2) | -0.0012 | cost-failed |
| qc.streak | up_excess_20 | -0.0041 (+0.3) | 0.84 | 0.5, -0.7 | -0.0062 (-1.5) | -0.0450 | null-overall |
| qc.streak | up_excess_5 | -0.0108 (-3.7) | 0.0034 | 1.0, +3.6 | +0.0023 (+0.5) | -0.0430 | holdout-failed |
| risk.semidev | up_excess_20 | -0.0697 (-3.0) | 0.03 | 0.75, +2.5 | +0.1249 (+4.6) | -0.0150 | cost-failed |
| risk.semidev | up_excess_60 | -0.0900 (-2.2) | 0.16 | 0.75, +1.5 | +0.1704 (+3.3) | -0.0180 | null-overall |
| sf.fade | up_excess_20 | +0.0027 (-0.3) | 0.85 | 0.667, -0.6 | -0.0037 (-1.1) | -0.0482 | null-overall |
| sf.fade | up_excess_5 | +0.0051 (+2.6) | 0.046 | 0.667, +2.6 | +0.0001 (-0.6) | -0.0459 | wf-failed |
| sf.smart | up_excess_20 | +0.0027 (-0.5) | 0.77 | 0.667, -0.6 | -0.0038 (-1.1) | -0.0475 | null-overall |
| sf.smart | up_excess_5 | +0.0049 (+2.6) | 0.045 | 0.667, +0.6 | -0.0000 (-0.6) | -0.0458 | wf-failed |
| sm.P | up_excess_20 | -0.0107 (-0.1) | 0.96 | 0.667, +0.2 | -0.0141 (-0.9) | -0.0457 | null-overall |
| sm.V | realized_vol_20 | +0.0157 (+0.9) | 0.56 | 1.0, +0.2 | +0.0168 (+1.8) | — | null-overall |
| sr.hi52 | up_excess_20 | +0.0679 (+3.2) | 0.021 | 0.8, +3.3 | +0.1205 (+5.3) | -0.0143 | cost-failed |
| sr.hi52 | up_excess_60 | +0.0999 (+3.2) | 0.045 | 0.8, +2.7 | +0.1626 (+3.4) | +0.0025 | promoted-B |
| surv.rev1 | up_excess_20 | +0.0071 (+0.7) | 0.68 | 0.667, +0.1 | -0.0047 (-1.0) | -0.0609 | null-overall |
| surv.rev1 | up_excess_5 | +0.0149 (+5.0) | 4.2e-05 | 1.0, +4.6 | +0.0043 (+1.0) | -0.0567 | holdout-failed |
| tai.pct | realized_vol_20 | -0.0573 (-2.3) | 0.096 | 0.6, +2.3 | +0.0460 (+2.9) | — | wf-failed |
| veto.cgtph | up_excess_20 | -0.0046 (-0.7) | 0.68 | 0.667, +0.3 | -0.0030 (-0.9) | +0.0018 | null-overall |
| veto.cgtph | up_excess_5 | -0.0103 (-4.6) | 0.00016 | 1.0, +4.2 | +0.0033 (+0.8) | +0.0008 | holdout-failed |
| veto.crashed | up_excess_20 | -0.0303 (-4.7) | 0.00067 | 0.833, +4.4 | +0.0895 (+10.4) | +0.0393 | promoted-B |
| veto.crashed | up_excess_60 | -0.0387 (-5.1) | 0.0032 | 0.833, +4.7 | +0.1192 (+7.8) | +0.1206 | promoted-B |
| veto.gapup10 | up_excess_20 | -0.0165 (-9.3) | 0 | 1.0, +9.1 | +0.0301 (+11.3) | +0.0653 | promoted-B |
| veto.gapup10 | up_excess_5 | -0.0177 (-15.4) | 0 | 1.0, +14.7 | +0.0230 (+18.1) | +0.0226 | promoted-B |
| veto.lod | up_excess_20 | -0.0446 (-3.4) | 0.011 | 1.0, +3.3 | +0.0777 (+5.6) | -0.0284 | cost-failed |
| veto.lod | up_excess_5 | -0.0355 (-4.8) | 9.1e-05 | 1.0, +4.8 | +0.0522 (+7.8) | -0.0322 | cost-failed |
| veto.panic | up_excess_20 | -0.0123 (-5.9) | 2.3e-05 | 1.0, +5.3 | +0.0303 (+11.9) | +0.0875 | promoted-B |
| veto.panic | up_excess_60 | -0.0131 (-5.1) | 0.0033 | 0.833, +4.6 | +0.0373 (+10.5) | +0.1694 | promoted-B |
| veto.pump100 | up_excess_20 | -0.0207 (-7.9) | 0 | 1.0, +7.6 | +0.0378 (+8.8) | +0.0929 | promoted-B |
| veto.pump100 | up_excess_60 | -0.0245 (-6.6) | 0.00051 | 1.0, +6.1 | +0.0488 (+10.8) | +0.1920 | promoted-B |
| veto.spikemem | up_excess_20 | -0.0442 (-6.8) | 1e-06 | 1.0, +6.2 | +0.0940 (+12.0) | +0.0536 | promoted-B |
| veto.spikemem | up_excess_60 | -0.0579 (-6.9) | 0.00025 | 1.0, +5.8 | +0.1251 (+9.0) | +0.1341 | promoted-B |
| vol.garch | realized_vol_20 | +0.7702 (+66.5) | 0 | 1.0, +55.9 | +0.8037 (+137.9) | — | promoted-B |
| vol.gex_pct | spy_rv_20 | -0.2317 (-3.8) | 0.0047 | 0.833, +3.3 | +0.1505 (+2.7) | — | promoted-B |
| vol.gex_pct | spy_rv_5 | -0.3826 (-9.0) | 0 | 1.0, +8.3 | +0.2110 (+5.1) | — | promoted-B |
| vol.gex_pct | spy_rvx_20 | +0.0333 (+0.8) | 0.6 | 0.833, +0.2 | -0.0265 (-1.6) | — | null-overall |
| vol.vix_level | spy_rv_20 | +0.4170 (+5.8) | 2.7e-05 | 1.0, +5.2 | +0.0937 (+3.2) | — | holdout-failed |
| vol.vix_level | spy_rv_5 | +0.5372 (+8.7) | 0 | 1.0, +8.2 | +0.1304 (+4.6) | — | holdout-failed |
| vol.vix_level | spy_rvx_20 | -0.0703 (-0.7) | 0.68 | 0.667, +0.4 | +0.0245 (-0.4) | — | null-overall |
| vol.vix_ts | spy_rv_20 | +0.3397 (+3.7) | 0.0067 | 1.0, +3.1 | +0.1270 (+2.6) | — | holdout-failed |
| vol.vix_ts | spy_rv_5 | +0.4715 (+7.7) | 0 | 1.0, +7.0 | +0.1765 (+4.0) | — | holdout-failed |
| vol.vix_ts | spy_rvx_20 | -0.0231 (+0.1) | 0.94 | 0.667, -0.4 | -0.0064 (-1.1) | — | null-overall |
| xs.momdip | up_excess_20 | +0.0277 (+3.0) | 0.028 | 1.0, +3.0 | +0.0435 (+5.1) | -0.0317 | cost-failed |
| xs.momdip | up_excess_60 | +0.0383 (+4.7) | 0.0057 | 0.833, +3.1 | +0.0535 (+4.0) | -0.0238 | cost-failed |
| xs.n9_reset | up_excess_20 | +0.0311 (+0.9) | 0.59 | 1.0, +0.9 | +0.0092 (+0.4) | -0.0439 | null-overall |
| xs.n9_reset | up_excess_60 | +0.0217 (+3.6) | 0.12 | 0.75, — | +0.0052 (—) | -0.0446 | null-overall |
| xs.n9_up | up_excess_20 | +0.0237 (+3.2) | 0.02 | 1.0, +2.6 | +0.0160 (+3.2) | -0.0328 | cost-failed |
| xs.n9_up | up_excess_60 | +0.0186 (+1.9) | 0.2 | 1.0, +0.1 | +0.0150 (+1.3) | -0.0310 | null-overall |

## Contexts

- Dims: {"fear": ["fear", "calm"], "spy200": ["above_rising", "above_falling", "below"], "vix": ["lo", "mid", "hi"], "tier": ["q1", "q2", "q3", "q4", "q5"], "age": ["new", "old"], "state": ["UP", "RESET"]}.
- Missing: sector (no point-in-time sector map in the desk data (DEEP universe.csv / assets.json carry no sector; own_index is not point in time): marked missing, no cell).
- Cells per forecaster x target: 135 cross-sectional, 30 market.

Runtime: {'law_check': 33.4, 'panel': 218.8, 'search': 1903.3}.

## Findings and deviations (P2), read before using any row

State: **PARTIAL.** The search, gates and registry are built and tested, and this run is real. Grade A (a second dataset) and the 2023+ cache rerun are not done.

- **Vetoes carry the run.** Of 1,217 promoted cells (45 distinct forecaster × target pairs), 1,050 are avoid/veto flags on up_excess: avoid.pump, deadcat, surge2, jump25, x1p6, stretch, mfi75 and idio (P1), plus veto.spikemem, gapup10, panic, pump100 and crashed (P2). A veto's net is the excess it avoids, and it trades nothing. This matches EVIDENCE §AVOID and the gestalt "vetoes beat buys".
- **The fear-day buy survivors are re-found but fail costs.** F3, N1, N7 and xs.n9_up pass BH, walk-forward and the holdout in the fear and VIX-high cells. For example, F3 → up_excess_20 in fear=fear|vix=hi has a discovery IC of +0.039 and a holdout IC of +0.061. But the top-quintile long is negative net of own-name costs (−0.027 per opportunity), so the verdict is `cost-failed`. The quintile includes thin names; a tier-restricted application is a P3 router question. N9-RESET, F6 and −F7 are not re-found as promoted. RESET cells are often under the minimum (untested). −F7 in RESET flips sign outside the liquid names, which P1 already measured.
- **Momentum and reversal don't survive.** mom.r126, xs.momdip and surv.rev1 have no promoted cell. Their verdicts are cost-failed, null-overall, or holdout-failed with sign flips. Single promoted cells exist for mom.volscaled at 60 sessions and NVI.
- **Volatility.** vol.garch, tai.pct, ap.regime and sm.V rank next-month realized volatility cross-sectionally. That is mostly persistence: no incremental-over-HAR target is in this run.
  - Market lane: low GEX → higher SPY realized vol is promoted at 5 and 20 sessions (discovery s̄ −0.38, t −9.0; holdout signed t 5.1). It is **not** promoted on spy_rvx_20, the part persistence does not give, where it is null.
  - DIX/GEX is a revised-history fixture (non-PIT), so the GEX row is validation only.
  - VIX/VIX3M and VIX level are holdout-failed: their holdout effect is under 50% of discovery.
  - Every index direction forecaster is null: DIX, VRP and SKEW on SPY returns.
- **Holdout power for 60-session targets is low.** The gapped-block t over the holdout uses ⌊dates / (2h − 1)⌋ blocks, so only 5–8 blocks for h = 60. The declared rule is t ≥ 2. I checked a stricter df-aware rule *after* the opening: block p < 0.05 on blocks − 1 df. It keeps 1,184 of the 1,217 promoted cells and all 45 pairs. The verdicts above use the pre-declared rule. The stricter rule is for information only and was not used to choose anything.
- **Deviations from FACTORY §4.**
  1. The BH p and the holdout t are P1's gapped-block statistics, not Newey-West. NW t is kept as `disc_t_nw` in the JSON.
  2. The embargo is max(45 days, the label's span), so it is 88 calendar days for 60-session labels.
  3. Holdout pass uses block t ≥ 2 with ≥ 50% of the discovery effect.
  4. Costs are Corwin-Schultz half-spread × 2.3 + 2 bp + square-root impact on a $10k order. NBBO-audit medians are not on DEEP.
  5. Sector is missing: there is no point-in-time map, so no cell is built.
  6. Listing age is left-censored for names already present on DEEP's first session.
  7. Context cells are singles and pairs only.
- **Holdout log.** It was opened once, under the key shown above. HoldoutLedger refuses a second opening, and the file sits under state/forecast/holdout/ (not committed). Two earlier attempts on this data died before the opening: one on a law-check refusal (chk.cmf21 round-off, fixed by a clip) and one on a pool deadlock/OOM (fixed). Neither opened the holdout.
