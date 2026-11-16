# CLV-GRADE-01: closing line value grades for the fleet

Run 2026-11-14 by continuation/clv_grade.py. Every number below is printed by that script from the artifacts named in Method; the script and its clv_grade.json sit beside this file.

## Headline

Estate raw mean CLV: T0 +0.004359 over 5041 graded entry fills; T1 +0.001773 over 5024. Estate deduped mean CLV: T0 -0.006497 over 396 cells; T1 -0.013927 over 384 cells. Deduping flips the estate sign at both horizons: the raw figure is carried by repeated fills inside a few cells.

Classifications issued: LUCKY 0, GOOD 0, UNPROFITABLE 1, SAMPLE_TOO_SMALL 2, not_applicable 39 of 42 CLV ledger sleeves. No LUCKY and no GOOD verdict exists in this run, and the reason is structural, not a near miss: only 3 sleeves in the whole attribution register have any realized P&L, none of them reaches the dive's 100 trade threshold on any count (largest: 42 raw graded T1 fills, 14 deduped T1 cells, 8 own closes), and the only sleeve at or above 100 deduped T1 cells is tensor_swing (117 cells, T1 deduped CLV -0.010691), which has no realized P&L and is therefore not_applicable by the rule.

## Method and the inherited CLV definition

Definition inherited verbatim from entry_clv.py (entry CLV ledger v1), not reinvented: entry fills only (buy_to_open, sell_to_open); session is the America/New_York date of the fill; T0 reference is the symbol's daily close that session and T1 reference is its next session close, both from the warm |1Day series; CLV for a buy is ref_close / fill_price - 1, and for a sell the negation. Dedupe rule inherited verbatim: one observation per (sleeve, symbol, date) cell, the cell value is the mean of its fill CLVs, and every mean above the fill level is a mean over cells.

Threshold: 100 or more paper trades, sourced from the X10 dive itself (ALPHA-HUNT-X10-2026-11-14.md: a strategy profitable with negative mean CLV over 100 or more paper trades is classified lucky). Trade count basis here: deduped cells at T1, the primary horizon (the ledger's falsifier is stated at T+1 and the twins headline is the T1 deduped figure). Raw graded counts are printed in every row; for all three sleeves with realized P&L the raw count is also below 100, so no classification in this run depends on the basis choice.

Realized P&L comes from wave2/attribution_ledger_v1_1.json. A sleeve counts as having realized P&L only when own_closes is above zero. In that ledger 336 of 339 sleeves carry realized_usd 0 with zero closes; that zero is absence of closes, not breakeven, and is graded not_applicable here.

Family grouping rule, from the names themselves: s_mn_ and s_cl_ group at that two token prefix (s_ alone is a namespace marker); every other name groups at its first underscore token plus underscore; a name with no underscore is its own family. Consequence stated plainly: aster_tensor_* sleeves sit in aster_, and tensor_ holds tensor_swing alone. Family CLV means are pooled over all cells in the family, cell weighted, never a mean of sleeve means.

## Verification (rebuilt, not trusted)

- per sleeve deduped cells rebuilt from rows match published counts for all 42 sleeves at both horizons; max mean deviation vs the published 6 decimal figures is 4.99e-07 (rounding only)
- estate deduped T0: rebuilt -0.006497 over 396 cells; twins clv_ledger_restated says -0.006497 over 396 cells; match=True
- estate deduped T1: rebuilt -0.013927 over 384 cells; twins clv_ledger_restated says -0.013927 over 384 cells; match=True
- twins entry_by_sleeve per sleeve check: 35 of 36 rows match the ledger T1 raw counts and deduped means exactly; the exception is aster_native_btc_eth_sma200, whose twins row carries its T0 figures (raw +0.005401, deduped -0.012100) instead of its T1 figures (raw +0.002205, deduped -0.004554); this grader uses the ledger T1 figures for that sleeve and names the twins row as mislabeled
- named discrepancy: twins execution_alpha estate entry_markout1 deduped is -0.014006 over 384 cells, while the CLV ledger estate deduped T1 is -0.013927 over the same 384 cells (difference 0.000079); this grader uses the ledger figure, which is the CLV definition in force
- raw to deduped sign flips rebuilt: [('aster_native_btc_eth_sma200', 't0'), ('aster_native_btc_eth_sma200', 't1'), ('bta_onebar_basket', 't1'), ('s_mn_hourly_1w', 't0'), ('s_mn_hourly_1w', 't1'), ('s_mn_macd', 't1'), ('s_mn_reversal', 't0'), ('s_mn_reversal', 't1'), ('s_mn_vwap', 't1')]; twins lists [('aster_native_btc_eth_sma200', 't0'), ('aster_native_btc_eth_sma200', 't1'), ('bta_onebar_basket', 't1'), ('s_mn_hourly_1w', 't0'), ('s_mn_hourly_1w', 't1'), ('s_mn_macd', 't1'), ('s_mn_reversal', 't0'), ('s_mn_reversal', 't1'), ('s_mn_vwap', 't1')]; match=True

## Classifications on their face

LUCKY: none issued. GOOD: none issued. The table below shows why: every profitable sleeve with realized P&L is below threshold.

- aster_trader_donchian55: SAMPLE_TOO_SMALL. Realized +5,489.35 over 8 own closes (expectancy +686.17, win rate 1.0). Deduped CLV T0 -0.028432 over 14 cells; T1 +0.001476 over 14 cells; raw graded fills T0 42, T1 42; sample flag below_threshold against the 100 threshold on T1 cells.
- bta_onebar_qqq: UNPROFITABLE. Realized -300.49 over 2 own closes (expectancy -150.25, win rate 0.0). Deduped CLV T0 +0.003349 over 4 cells; T1 -0.002361 over 4 cells; raw graded fills T0 7, T1 7; sample flag below_threshold against the 100 threshold on T1 cells.
- bta_onebar_rth: SAMPLE_TOO_SMALL. Realized +661.36 over 3 own closes (expectancy +220.45, win rate 1.0). Deduped CLV T0 +0.005417 over 3 cells; T1 -0.002259 over 3 cells; raw graded fills T0 5, T1 5; sample flag below_threshold against the 100 threshold on T1 cells.

Horizon warning on all three classified sleeves: T0 and T1 deduped CLV disagree in sign for aster_trader_donchian55 (T0 negative, T1 positive), bta_onebar_qqq (T0 positive, T1 negative) and bta_onebar_rth (T0 positive, T1 negative). Any future LUCKY or GOOD verdict for these sleeves will be horizon sensitive and must print both horizons, as this table does.

## Per sleeve table (all 42 CLV ledger sleeves)

| sleeve | family | n entries | raw graded T0 | raw graded T1 | cells T0 | mean deduped CLV T0 | cells T1 | mean deduped CLV T1 | CLV sign | realized USD | own closes | classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aster_core_rsi2_long | aster_ | 2 | 2 | 2 | 2 | -0.020207 | 2 | -0.010504 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| aster_core_rsi2_vertical | aster_ | 2 | 2 | 2 | 2 | -0.019780 | 2 | -0.010075 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| aster_etf_core25_c098 | aster_ | 2 | 2 | 2 | 2 | -0.000655 | 2 | +0.012466 | MIXED | not_applicable | not_applicable | not_applicable |
| aster_etf_core25_m150 | aster_ | 2 | 2 | 2 | 2 | -0.000497 | 2 | +0.012625 | MIXED | not_applicable | not_applicable | not_applicable |
| aster_etf_drift1_c098 | aster_ | 1 | 1 | 1 | 1 | +0.000406 | 1 | +0.016930 | POSITIVE | not_applicable | not_applicable | not_applicable |
| aster_etf_leader1_m150 | aster_ | 18 | 18 | 18 | 9 | -0.001081 | 9 | +0.014020 | MIXED | not_applicable | not_applicable | not_applicable |
| aster_etf_qqq_monthly_c098 | aster_ | 49 | 49 | 49 | 11 | -0.004748 | 11 | +0.008661 | MIXED | not_applicable | not_applicable | not_applicable |
| aster_etf_qqq_monthly_m150 | aster_ | 15 | 15 | 15 | 7 | -0.003003 | 7 | +0.015747 | MIXED | not_applicable | not_applicable | not_applicable |
| aster_etf_spy_monthly_c098 | aster_ | 53 | 53 | 51 | 11 | -0.002328 | 10 | +0.012017 | MIXED | not_applicable | not_applicable | not_applicable |
| aster_etf_spy_monthly_m150 | aster_ | 5 | 5 | 5 | 4 | -0.003647 | 4 | -0.007237 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| aster_native_btc_eth_sma200 | aster_ | 26 | 26 | 26 | 4 | -0.012100 | 4 | -0.004554 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| aster_saty_research | aster_ | 7 | 7 | 7 | 7 | -0.004665 | 7 | -0.061571 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| aster_tensor_d20_pv | aster_ | 420 | 173 | 173 | 9 | +0.022788 | 9 | +0.078031 | POSITIVE | not_applicable | not_applicable | not_applicable |
| aster_tensor_d20_tensor | aster_ | 684 | 282 | 282 | 12 | -0.000586 | 12 | +0.106717 | MIXED | not_applicable | not_applicable | not_applicable |
| aster_tensor_h1_recovery | aster_ | 14 | 14 | 0 | 10 | -0.030824 | 0 | n/a | NEGATIVE | not_applicable | not_applicable | not_applicable |
| aster_trader_donchian55 | aster_ | 42 | 42 | 42 | 14 | -0.028432 | 14 | +0.001476 | MIXED | +5,489.35 | 8 | SAMPLE_TOO_SMALL |
| beatendown | beatendown | 17 | 17 | 17 | 17 | -0.023010 | 17 | -0.025373 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| bta_onebar_basket | bta_ | 12 | 12 | 12 | 8 | +0.002346 | 8 | +0.000788 | POSITIVE | not_applicable | not_applicable | not_applicable |
| bta_onebar_qqq | bta_ | 7 | 7 | 7 | 4 | +0.003349 | 4 | -0.002361 | MIXED | -300.49 | 2 | UNPROFITABLE |
| bta_onebar_rth | bta_ | 5 | 5 | 5 | 3 | +0.005417 | 3 | -0.002259 | MIXED | +661.36 | 3 | SAMPLE_TOO_SMALL |
| capitulation | capitulation | 14 | 14 | 14 | 14 | -0.022991 | 14 | -0.062597 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| confluence | confluence | 17 | 17 | 17 | 17 | -0.030275 | 17 | -0.047394 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| donchian | donchian | 13 | 13 | 13 | 13 | -0.032833 | 13 | -0.076839 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| ema_vwap | ema_ | 2 | 2 | 2 | 2 | -0.010660 | 2 | +0.104521 | MIXED | not_applicable | not_applicable | not_applicable |
| investandbefree_dmac | investandbefree_ | 280 | 0 | 0 | 0 | n/a | 0 | n/a | NO_CLV_DATA | not_applicable | not_applicable | not_applicable |
| investandbefree_dmac_dailyonly | investandbefree_ | 279 | 0 | 0 | 0 | n/a | 0 | n/a | NO_CLV_DATA | not_applicable | not_applicable | not_applicable |
| investandbefree_dmac_intraday | investandbefree_ | 179 | 0 | 0 | 0 | n/a | 0 | n/a | NO_CLV_DATA | not_applicable | not_applicable | not_applicable |
| investandbefree_dmac_premacd | investandbefree_ | 277 | 0 | 0 | 0 | n/a | 0 | n/a | NO_CLV_DATA | not_applicable | not_applicable | not_applicable |
| leaps_momentum | leaps_ | 16 | 16 | 15 | 3 | +0.001959 | 2 | +0.010230 | POSITIVE | not_applicable | not_applicable | not_applicable |
| momentum | momentum | 7 | 7 | 7 | 7 | -0.013596 | 7 | -0.013508 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| morning_dip | morning_ | 1 | 1 | 1 | 1 | -0.005787 | 1 | -0.011867 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| qqq_put_ladder | qqq_ | 1 | 0 | 0 | 0 | n/a | 0 | n/a | NO_CLV_DATA | not_applicable | not_applicable | not_applicable |
| red_day_reversal | red_ | 164 | 164 | 164 | 13 | -0.022862 | 13 | -0.058932 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| rsi_meanrev | rsi_ | 8 | 8 | 8 | 8 | -0.012908 | 8 | -0.001625 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| s_cl_vmr_qqq | s_cl_ | 3 | 3 | 3 | 3 | +0.009686 | 3 | -0.012129 | MIXED | not_applicable | not_applicable | not_applicable |
| s_mn_hourly_1w | s_mn_ | 184 | 184 | 184 | 4 | -0.023317 | 4 | -0.134653 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| s_mn_macd | s_mn_ | 177 | 175 | 175 | 3 | +0.043941 | 3 | -0.047224 | MIXED | not_applicable | not_applicable | not_applicable |
| s_mn_reversal | s_mn_ | 23 | 23 | 23 | 9 | +0.004659 | 9 | -0.048510 | MIXED | not_applicable | not_applicable | not_applicable |
| s_mn_vwap | s_mn_ | 6 | 6 | 6 | 3 | +0.023204 | 3 | -0.014432 | MIXED | not_applicable | not_applicable | not_applicable |
| t_cci_corr | t_ | 27 | 27 | 27 | 26 | +0.003651 | 26 | -0.013763 | MIXED | not_applicable | not_applicable | not_applicable |
| tensor_swing | tensor_ | 3633 | 3633 | 3633 | 117 | +0.004347 | 117 | -0.010691 | MIXED | not_applicable | not_applicable | not_applicable |
| ts_momentum_decile | ts_ | 14 | 14 | 14 | 14 | -0.031307 | 14 | -0.054848 | NEGATIVE | not_applicable | not_applicable | not_applicable |

## Family table

| family | sleeves | n entries | raw graded T1 | cells T0 | mean deduped CLV T0 | cells T1 | mean deduped CLV T1 | CLV sign | realized USD (sleeves with closes) | own closes | classification |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aster_ | 16 | 1342 | 677 | 107 | -0.007424 | 96 | +0.020867 | MIXED | +5,489.35 | 8 | SAMPLE_TOO_SMALL |
| beatendown | 1 | 17 | 17 | 17 | -0.023010 | 17 | -0.025373 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| bta_ | 3 | 24 | 24 | 15 | +0.003227 | 15 | -0.000661 | MIXED | +360.87 | 5 | SAMPLE_TOO_SMALL |
| capitulation | 1 | 14 | 14 | 14 | -0.022991 | 14 | -0.062597 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| confluence | 1 | 17 | 17 | 17 | -0.030275 | 17 | -0.047394 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| donchian | 1 | 13 | 13 | 13 | -0.032833 | 13 | -0.076839 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| ema_ | 1 | 2 | 2 | 2 | -0.010660 | 2 | +0.104521 | MIXED | not_applicable | not_applicable | not_applicable |
| investandbefree_ | 4 | 1015 | 0 | 0 | n/a | 0 | n/a | NO_CLV_DATA | not_applicable | not_applicable | not_applicable |
| leaps_ | 1 | 16 | 15 | 3 | +0.001959 | 2 | +0.010230 | POSITIVE | not_applicable | not_applicable | not_applicable |
| momentum | 1 | 7 | 7 | 7 | -0.013596 | 7 | -0.013508 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| morning_ | 1 | 1 | 1 | 1 | -0.005787 | 1 | -0.011867 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| qqq_ | 1 | 1 | 0 | 0 | n/a | 0 | n/a | NO_CLV_DATA | not_applicable | not_applicable | not_applicable |
| red_ | 1 | 164 | 164 | 13 | -0.022862 | 13 | -0.058932 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| rsi_ | 1 | 8 | 8 | 8 | -0.012908 | 8 | -0.001625 | NEGATIVE | not_applicable | not_applicable | not_applicable |
| s_cl_ | 1 | 3 | 3 | 3 | +0.009686 | 3 | -0.012129 | MIXED | not_applicable | not_applicable | not_applicable |
| s_mn_ | 4 | 390 | 388 | 19 | +0.007900 | 19 | -0.061062 | MIXED | not_applicable | not_applicable | not_applicable |
| t_ | 1 | 27 | 27 | 26 | +0.003651 | 26 | -0.013763 | MIXED | not_applicable | not_applicable | not_applicable |
| tensor_ | 1 | 3633 | 3633 | 117 | +0.004347 | 117 | -0.010691 | MIXED | not_applicable | not_applicable | not_applicable |
| ts_ | 1 | 14 | 14 | 14 | -0.031307 | 14 | -0.054848 | NEGATIVE | not_applicable | not_applicable | not_applicable |

Family notes: aster_ realized is aster_trader_donchian55 alone. bta_ realized sums bta_onebar_qqq (negative) and bta_onebar_rth (positive) and nets positive at family level while one member is UNPROFITABLE at sleeve level; both levels are printed so the netting is visible. tensor_ (tensor_swing alone) is the only family at or above the 100 cell threshold at T1 and it has no realized P&L, so its negative CLV stands as a CLV sign only, with no LUCKY or GOOD question to answer.

## Gaps named, not reconstructed

1. Profitability coverage: attribution_ledger_v1_1.json registers 339 sleeves and only 3 have any own closes (aster_trader_donchian55: 8, bta_onebar_rth: 3, bta_onebar_qqq: 2; 13 per close rows in total). Every other CLV sleeve is not_applicable on profitability. CLV grades entries now; the LUCKY versus GOOD question cannot be answered for the fleet until closes exist at scale. This is the binding gap.
2. CLV coverage: the entry CLV ledger carries 42 sleeves against 339 in the attribution register. The remaining sleeves have no entry fills in the fill ledger population the CLV ledger grades, so they get no row here rather than a fabricated zero.
3. Ungraded entries: 1667 entry fills have no T0 grade, every one for the single reason no_warm_daily_series. Five sleeves have entries and zero graded fills and therefore NO_CLV_DATA: investandbefree_dmac (280 entries), investandbefree_dmac_dailyonly (279), investandbefree_dmac_premacd (277), investandbefree_dmac_intraday (179) and qqq_put_ladder (1). Two more are heavily thinned by the same gap: aster_tensor_d20_tensor (402 of 684 entries ungraded) and aster_tensor_d20_pv (247 of 420). Their printed CLV means describe only the graded remainder.
4. Twins estate discrepancy: named in Verification above. The twins execution_alpha estate entry_markout1 deduped aggregate differs from the CLV ledger estate deduped T1 by 0.000079 over the same 384 cells, and the artifacts do not say why. This grader follows the ledger, the CLV definition in force, and flags the twins aggregate rather than averaging the two.
5. Twins per sleeve mislabel: 35 of 36 rows in the twins execution_alpha entry_by_sleeve table match the ledger T1 figures exactly. The exception, aster_native_btc_eth_sma200, carries its T0 figures in that table (raw +0.005401, deduped -0.012100) where its T1 figures are raw +0.002205 and deduped -0.004554. The sign is negative under either horizon, so no sign conclusion changes; the magnitude printed here is the ledger T1 figure.
6. aster_tensor_h1_recovery has T0 cells (10) and no T1 grade at all (no next session in the warm series for its fills at ledger build time), so it has no primary horizon figure; it is also absent from the twins entry_by_sleeve table, which is a T1 table.

## Falsifier carried from the ledger

If per sleeve CLV at T1 shows no association with sleeves' realized expectancy where both exist, the ledger is demoted to a diagnostic (entry_clv.py). With only three sleeves carrying both, that test has no power yet; it stays open and named here rather than graded.

