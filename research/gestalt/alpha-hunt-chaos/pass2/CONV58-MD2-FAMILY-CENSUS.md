# CONV-58 MD2 FAMILY CENSUS: THE DECOMPOSED POPULATION OVER ITS SCORECARD FIELDS

Built Sun 2026-11-15 as the named cheapest forward step of Conversion Register row CONV-58 (CONVERSION-REGISTER-2026-11-15.md, section CONV-58: "a family census over the register's scorecard fields, the 1w family's 132 ids first, which either names a portable form for a Triad decision or closes the question with evidence").

SCOPE. Surface: this one new file, computed only from held records. Sources: pass2/MD2-REGISTER.jsonl (the register) and the md2 half of pass2/MD2-DEALER-DIG.md (family definitions and join semantics). Constraints: the CONVERSION-REGISTER files were not edited; the desk tree was not touched; no external datum was used; no field was invented, every aggregated field below is a register field under its own name. Outcome: a recount, a census of all 107 catalog families over the scorecard fields, a deep read of the 1w family, and a verdict on whether any family carries a portable form on held records. Proof: every number in this file was recomputed from the register rows by the census script, and the census table's column sums are re-asserted against the register totals in section 2.

FIELD DEFINITIONS (the register's own names). Each register row carries sid, population, family, catalog_source_field, strategy, status_2026_10_29, disposition, and, for joined rows, scorecard_2026_11_11 with status, engine, n_open, entry_filled, exit_filled, n_closed, wins, losses, realized, excess_vs_spy, beats_spy, confidence, machinery_vs_signal, evidence, first_event, last_event. In this census: "entry ids" counts scorecard ids with entry_filled greater than 0; "closed ids" counts scorecard ids with n_closed greater than 0; "realized median" is the median of realized over a family's scorecard ids, zeros included, because realized is present (and usually 0.0) on every joined row; mean excess_vs_spy is taken over the scorecard ids where excess_vs_spy is not null.

## 1. RECOUNT AGAINST THE BRIEF

| Figure | Brief and CONV-58 | Recounted from the rows | Agreement |
|---|---|---|---|
| Register rows | 577 | 577 rows, 577 unique sids | exact |
| Decomposed catalog ids | 556 | 556 (557 catalog population rows minus the 1 residual row) | exact |
| Catalog families | 107 | 107 distinct family values over the 556 | exact |
| Scorecard joined ids | 409 | 409 (disposition DECOMPOSED-WITH-LIVE-RECORD) | exact |
| Ids with entry fills | 51 | 51 ids with entry_filled greater than 0, 397 entry fills in total | exact |
| Ids with closed trades | 31 | 31 ids with n_closed greater than 0, 184 closed trades in total | exact |
| Ids with nonzero realized | 29 | 29 | exact |
| 1w family size | 132 ids | 132 ids | exact |

No disagreement was found on any figure. Two framing clarifications the rows themselves carry, printed rather than absorbed:

1. The 577 rows split as 557 catalog population rows, 20 t474u intake rows, and within the 557, one aggregate row (sid MD2-RESIDUAL-65, family null, disposition RESIDUAL-UNNAMED) standing for the 65 unnamed residual ids. The decomposed count is therefore 556 catalog ids plus 20 separately decomposed t474u intake ids, and this census covers the CONV-58 population: the 556 catalog ids in 107 families.
2. The register file carries 114 distinct non-null family values in total, not 107: the extra 7 are the t474u intake families (mfi_gate 5, bar_range_atr 4, btc_stdev 4, fib_ew_poc 2, midas_vwap_fib 2, zlema_mtf 2, oneil_cwh 1; 20 ids, disposition DECOMPOSED-INTAKE-RECORD, scorecard_2026_11_11 null on every row). They are outside CONV-58's 107 because CONV-58 counts the catalog population, and they carry no scorecard fields to census. Counting them would change no verdict: their live record is zero by construction.

## 2. THE GRADEABLE GROUND, IN TOTAL

Over the 409 joined scorecard ids: entry_filled sums to 397 across 51 ids; n_closed sums to 184 across 31 ids; wins sum to 61 and losses to 123; n_open sums to 211; realized sums to -15766.50 dollars, with absolute realized mass of 18777.94 dollars. Only 7 of the 409 joined ids carry positive realized (total +1505.72); 22 carry negative realized; the remaining 380 sit at exactly 0.0. Confidence on the scorecard tops out at moderate: {'none': 378, 'tiny': 23, 'moderate': 3, 'low': 5} over the joined ids, with no id at high. machinery_vs_signal reads trading on only 50 joined ids, unknown_silent on 234, machinery on 84.

Live substance is concentrated to a sliver: only 16 of the 107 families have any entry fill at all, the same 16 families hold all 184 closed trades, and only 5 families sum to positive realized: sleeves.raschke_pf3 (+1104.40 on 25 closed), intraday_reversal_liquidity_sweep (+39.47 on 17 closed), sleeves.phase_daily (+6.79 on 4 closed), sleeves.ts_momentum_decile (+97.01 on 2 closed), sleeves.morning_dip (+16.39 on 2 closed).

Census table integrity, re-asserted after generation: the table in section 4 sums to 556 ids, 409 scorecard ids, 51 entry ids, 397 entry fills, 31 closed ids, 184 closed trades, 61 wins, 123 losses and realized -15766.50, matching this section's totals computed directly from the rows.

## 3. THE PORTABLE FORM BAR

A family names a portable form for a Triad decision only if all three of the following hold on held records alone:

1. Coherence: the family's live record ids share one signal definition, statable from the held records, not merely a shared label, timeframe bucket, or parameter grid.
2. Substance: the family carries closed trades with positive realized mass at family level, enough that a Triad decision would be deciding on evidence rather than on a name.
3. Completeness: the held records carry the form itself (what the signal is, on what universe and timeframe, with what entry and exit), so a fresh registration could be written without an external datum. A record that points at a definition held elsewhere (an adapter note, a ported signal held in another codebase) fails this test on held records, however good its numbers are.

## 4. FAMILY CENSUS: ALL 107 CATALOG FAMILIES

Ranked by live record substance: n_closed sum descending, then absolute realized sum descending, then entry_filled sum descending, then id count descending, then family name. realized_median is over scorecard ids (n/a where a family has no scorecard ids). mean_excess is excess_vs_spy averaged over scorecard ids where it is not null.

| Rank | Family | ids | scorecard_ids | entry_ids | entry_filled | closed_ids | n_closed | wins | losses | realized_sum | realized_median | nonzero_ids | beats_spy_true | mean_excess_vs_spy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1h | 3 | 3 | 3 | 83 | 2 | 41 | 7 | 34 | -7971.67 | -1504.30 | 2 | 2 | 0.058487 |
| 2 | 1d | 29 | 29 | 16 | 139 | 11 | 33 | 4 | 29 | -5186.33 | 0.00 | 11 | 6 | -0.005731 |
| 3 | sleeves.ema_vwap | 1 | 1 | 1 | 34 | 1 | 31 | 16 | 15 | -43.93 | -43.93 | 1 | 1 | 0.007092 |
| 4 | sleeves.raschke_pf3 | 1 | 1 | 1 | 25 | 1 | 25 | 11 | 14 | 1104.40 | 1104.40 | 1 | 1 | 0.208047 |
| 5 | intraday_reversal_liquidity_sweep | 1 | 1 | 1 | 17 | 1 | 17 | 10 | 7 | 39.47 | 39.47 | 1 | 1 | 0.012074 |
| 6 | 1w | 132 | 132 | 18 | 50 | 4 | 7 | 0 | 7 | -1601.86 | 0.00 | 4 | 14 | 0.017089 |
| 7 | daily_pullback_cci_correction | 1 | 1 | 1 | 11 | 1 | 6 | 1 | 5 | -30.66 | -30.66 | 1 | 0 | -0.019636 |
| 8 | sleeves.free_opt_parity | 1 | 1 | 1 | 8 | 1 | 4 | 0 | 4 | -1761.01 | -1761.01 | 1 | 0 | n/a |
| 9 | sleeves.phase_daily | 1 | 1 | 1 | 4 | 1 | 4 | 4 | 0 | 6.79 | 6.79 | 1 | 1 | 0.007943 |
| 10 | native_trend | 4 | 2 | 2 | 4 | 2 | 4 | 4 | 0 | 0.00 | 0.00 | 0 | 2 | 0.003272 |
| 11 | sleeves.red_day_reversal | 1 | 1 | 1 | 3 | 1 | 3 | 0 | 3 | -237.18 | -237.18 | 1 | 0 | -0.016454 |
| 12 | sleeves.momentum | 1 | 1 | 1 | 4 | 1 | 2 | 0 | 2 | -178.12 | -178.12 | 1 | 0 | -0.009702 |
| 13 | sleeves.ts_momentum_decile | 1 | 1 | 1 | 9 | 1 | 2 | 2 | 0 | 97.01 | 97.01 | 1 | 0 | -0.029092 |
| 14 | sleeves.donchian | 1 | 1 | 1 | 3 | 1 | 2 | 1 | 1 | -18.71 | -18.71 | 1 | 1 | 0.006205 |
| 15 | sleeves.morning_dip | 1 | 1 | 1 | 2 | 1 | 2 | 1 | 1 | 16.39 | 16.39 | 1 | 1 | 0.008084 |
| 16 | intraday_macd_divergence_fib_variant | 10 | 10 | 1 | 1 | 1 | 1 | 0 | 1 | -1.09 | 0.00 | 1 | 1 | 0.012522 |
| 17 | negative_funding_squeeze | 60 | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 18 | etf | 52 | 26 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 19 | recovery | 32 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 20 | G4 | 24 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 21 | C1 | 18 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 22 | absorption_base | 12 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 23 | absorption_negative_funding | 12 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 24 | absorption_nonnegative_funding | 12 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 25 | breakout_base | 12 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 26 | public_recipe | 9 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 27 | hourly | 8 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 28 | pead | 8 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 29 | xsp_pcs | 8 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 30 | cloud | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 31 | confirmed_absorption | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 32 | core_reserve | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 33 | opening_gamma | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 34 | overnight | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 35 | tensor | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 36 | tensor_leaps | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 37 | BETA | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 38 | intraday_macd_divergence_fib | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.012413 |
| 39 | midna_em_1587 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 40 | midna_po10_qqq | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 41 | midna_saty_day | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 42 | midna_saty_sol | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 43 | midna_saty_sol_0dte | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 44 | saty_research | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 45 | shen_fade | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | n/a |
| 46 | sleeves.aurelia_gold | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 47 | sleeves.aurelia_ndx | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 48 | sleeves.bb_rsi_divergence | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 49 | sleeves.beatendown | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 50 | sleeves.bilbo_options | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 51 | sleeves.capitulation | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 52 | sleeves.capitulation_options | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 53 | sleeves.confluence | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 54 | sleeves.daily_cyan_gbm | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 55 | sleeves.donchian_crypto | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 56 | sleeves.earnings_buyback | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 57 | sleeves.em_1587 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 58 | sleeves.ema_vwap_options | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 59 | sleeves.fear_premium | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 60 | sleeves.free_etf | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 61 | sleeves.free_kraken_ada_basis | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 62 | sleeves.free_kraken_ada_breakdown | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 63 | sleeves.free_kraken_ada_crowded | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 64 | sleeves.free_kraken_enj_spot | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 65 | sleeves.free_kraken_link_basis | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 66 | sleeves.free_kraken_link_breakdown | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 67 | sleeves.free_kraken_link_crowded | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 68 | sleeves.free_opt_own_iv | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 69 | sleeves.free_opt_pair | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 70 | sleeves.free_opt_release | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 71 | sleeves.free_opt_tail | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 72 | sleeves.free_opt_wheel | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 73 | sleeves.fwd_alpaca_ada_rsi2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 74 | sleeves.fwd_alpaca_enj_iu_body | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 75 | sleeves.fwd_alpaca_link_ai_volume | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 76 | sleeves.fwd_coinbase_sma200 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 77 | sleeves.gate_1h | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 78 | sleeves.iron_condor | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 79 | sleeves.leader_d | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 80 | sleeves.leader_sc | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 81 | sleeves.leaps_momentum | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 82 | sleeves.legends_ema | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 83 | sleeves.momentum_rotation | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 84 | sleeves.phoenix | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 85 | sleeves.po10_qqq | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 86 | sleeves.qqq_put_ladder | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 87 | sleeves.qullamaggie | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 88 | sleeves.qullamaggie_paper | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 89 | sleeves.raschke_rre | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 90 | sleeves.rsi_meanrev | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 91 | sleeves.rsi_meanrev_options | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 92 | sleeves.rule_1d_cyan_smallcap | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 93 | sleeves.rule_1d_green_tom | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 94 | sleeves.rule_1h_cyan_raw | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 95 | sleeves.rule_1w_cyan_mom_adx | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 96 | sleeves.rule_1w_swing_beta_wt | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 97 | sleeves.saty_day | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 98 | sleeves.saty_gpt_v02 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 99 | sleeves.saty_gpt_v03 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 100 | sleeves.saty_magnum | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 101 | sleeves.saty_sol | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 102 | sleeves.saty_sol_0dte | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 103 | sleeves.snapback | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 104 | sleeves.spx_premium | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 105 | sleeves.tensor_red_dip | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 106 | sleeves.tensor_swing | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |
| 107 | sleeves.vix_hedge | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0.007264 |

## 5. THE LIVE SIXTEEN, READ ONE BY ONE

Only 16 families carry any live record. Their reads, in census rank order:

- **1h** (ids 3, closed 41, wins 7, losses 34, realized -7971.67): Three ids, three different strategy strings (1H Swing; Midna Hourly, a Midna port; Midna Nostop, a Midna port). The largest closed mass in the census and the largest loss: 41 closed, 7 wins against 34 losses, realized -7971.67. Fails coherence (no shared definition) and fails substance (negative).
- **1d** (ids 29, closed 33, wins 4, losses 29, realized -5186.33): 29 ids, 29 distinct strategy strings: the daily sibling of the 1w bucket, a cell population, not a form. 33 closed, 4 wins against 29 losses, realized -5186.33. Its only positive ids are two Midna ports (lz_s_mn_reversal +202.66 on 3 closed; lz_s_mn_hedge +39.00 on 1 closed), each its own definition. Fails coherence and substance.
- **sleeves.ema_vwap** (ids 1, closed 31, wins 16, losses 15, realized -43.93): A single id family. 31 closed, 16 wins against 15 losses, realized -43.93, effectively flat and negative. Its strategy field is an adapter note (interface glue only, in its own words), so the form itself is not in the held record. Fails substance and completeness.
- **sleeves.raschke_pf3** (ids 1, closed 25, wins 11, losses 14, realized 1104.40): A single id family and the census's nearest miss; read in full in section 7. Positive and the joint highest confidence in the population, but the definition is not in the held record. Fails completeness, and as a one id family it names a sleeve, not a family form.
- **intraday_reversal_liquidity_sweep** (ids 1, closed 17, wins 10, losses 7, realized 39.47): A single id family (sid t_kz_sweep). The one singleton whose held record does sketch a form (strategy: ICT killzone sweep and reclaim; status_reason carries QQQ and SPY plus BTC-USD long only, entries 09:45 to 10:30, flat at 12:00 ET). Its record is 17 closed, 10 wins against 7 losses, realized +39.47 in total, which is +2.32 per closed trade and 0.21 percent of the population's absolute realized mass, at confidence low. A nameable sketch with no measurable edge behind it fails substance: there is nothing here for a Triad decision to decide on.
- **1w** (ids 132, closed 7, wins 0, losses 7, realized -1601.86): Read in full in section 6. 7 closed, 0 wins, realized -1601.86, 132 distinct strategy strings. Fails coherence and substance.
- **daily_pullback_cci_correction** (ids 1, closed 6, wins 1, losses 5, realized -30.66): A single id family (sid t_cci_corr). Its strategy field does name a form (CCI correction pullback, Lowest(CCI27,18) below -100, credited to @onlybreakouts in the record), and its record is 6 closed, 1 win against 5 losses, realized -30.66, confidence low. Nameable and negative: fails substance.
- **sleeves.free_opt_parity** (ids 1, closed 4, wins 0, losses 4, realized -1761.01): A single id family. 4 closed, 0 wins, realized -1761.01, the worst singleton. Adapter note only. Fails substance and completeness.
- **sleeves.phase_daily** (ids 1, closed 4, wins 4, losses 0, realized 6.79): A single id family. 4 closed, all 4 wins, realized +6.79 in total (+1.70 per closed trade), confidence tiny. Adapter note only. Fails substance (mass is negligible) and completeness.
- **native_trend** (ids 4, closed 4, wins 4, losses 0, realized 0.00): 4 ids, 2 joined, both joined ids the same strategy string (Daily SMA200 spot allocation) with 2 closed each, 4 wins, realized exactly 0.00 on both, excess_vs_spy +0.003272 on both. The one multi id family whose live ids genuinely share one definition, and its closed record carries zero realized mass and zero nonzero ids. Coherent and empty: fails substance. A daily SMA200 allocation is also the most consensus form in the census, which a Triad port decision would have to weigh even if the record were positive.
- **sleeves.red_day_reversal** (ids 1, closed 3, wins 0, losses 3, realized -237.18): A single id family. 3 closed, 0 wins, realized -237.18. Adapter note only. Fails substance and completeness.
- **sleeves.momentum** (ids 1, closed 2, wins 0, losses 2, realized -178.12): A single id family. 2 closed, 0 wins, realized -178.12. Its strategy field states the strategy lives in the sleeve file of another codebase (a faithful copy, in its own words), not in this record. Fails substance and completeness.
- **sleeves.ts_momentum_decile** (ids 1, closed 2, wins 2, losses 0, realized 97.01): A single id family. 2 closed, both wins, realized +97.01, with 7 still open; excess_vs_spy is negative (-0.029092) and beats_spy is False, confidence tiny. Adapter note only (interface glue only, in its own words). Fails completeness, and 2 closed trades at tiny confidence fail substance as a family claim.
- **sleeves.donchian** (ids 1, closed 2, wins 1, losses 1, realized -18.71): A single id family. 2 closed, 1 win and 1 loss, realized -18.71. Adapter note only (interface glue only, in its own words). Fails substance and completeness.
- **sleeves.morning_dip** (ids 1, closed 2, wins 1, losses 1, realized 16.39): A single id family. 2 closed, 1 win and 1 loss, realized +16.39, confidence tiny. Its strategy field ends mid sentence at the word Strategy, an adapter note for a ported signal whose definition is not carried. Fails substance (2 trades, +16.39) and completeness.
- **intraday_macd_divergence_fib_variant** (ids 10, closed 1, wins 0, losses 1, realized -1.09): 10 ids, 10 joined, one entry id with 1 closed trade, 0 wins, realized -1.09; the other 9 joined ids never filled. Fails substance, and its live sliver shares no tested definition across the family.

The other 91 families, including every large named family, carry zero entry fills and zero closed trades on their joined ids, or no joined ids at all. Section 7 reads the coherent ones among them.

## 6. DEEP READ: THE 1W FAMILY (132 IDS)

### 6.1 Composition

All 132 ids are catalog_source_field lazarus, engine lazarus on the scorecard, and disposition DECOMPOSED-WITH-LIVE-RECORD: uniquely in this census, every id in the family joined the scorecard. status_2026_10_29 is installed 122 and off 10, matching the scorecard status field. machinery_vs_signal: unknown_silent 104, trading 18, disabled 10. The scorecard evidence text for the 104 unknown_silent ids states, in paraphrase, that the sleeve is funded and installed with no journal and no fills, so missing machinery cannot be told apart from a rare trigger without eval receipts. The 10 disabled ids are the off ids (lazarus sleeve disabled in config, per their evidence text).

The family is a weekly timeframe bucket holding a parameter grid, not a strategy. All 132 strategy strings are distinct: 132 ids, 132 definitions. Token census over the strategy strings: Q07 appears in 115 ids; the word test appears in 121; horizon H52 in 56, H78 in 57, neither in 19, both in none. Stream labels partition the grid: cyan in 39, green in 40, swing in 42, none of the three in 11. Size tiers: micro 38, small 45, midlarge (including the one mid/large spelling) 34. Condition tokens recur across cells: cheap5 54, deep70 43, mom6 38, tierA 48, wiki variants 32, insider variants 20, stress variants 28. The remaining 17 ids carry no Q07 marker and are different in kind, not just in parameters: tier A Cyan and Green tests (4), lab forms (Lab 1W Cyan books, Lab 1W Swing covered, Lab rule 1W), 1W Swing stress pockets, the desk form (lz_1w, strategy 1W desk), a Midna port (lz_s_mn_hourly_1w, Midna Hourly 1W), Moonshot, CHASE, and six WAIT books (FLOW, intraweek early entry, OLX books, Q14, R2 Daily Cyan extended, and the chase form). No one of these kinds is the family; the family is the bucket that contains all of them.

### 6.2 Live record

Of 132 joined ids, 18 carry entry fills (50 entry_filled in total) and 4 carry closed trades (7 n_closed in total). wins sum to 0 and losses to 7: every closed trade in the family lost. n_open sums to 43, so most of the family's fills were still open at the 2026-11-11 scorecard. beats_spy is True on 14 ids, all of them among the 18 trading ids, but beats_spy on this scorecard coexists with negative realized on the closed subset (the closed ids below sum to -1278.61 of realized among the beats_spy True set) and rests largely on open positions; it does not grade the closed record.

The 18 ids with entry fills, in full:

| sid | strategy | entry_filled | n_closed | wins | losses | realized | excess_vs_spy | confidence |
|---|---|---|---|---|---|---|---|---|
| lz_s_1wlab | Lab 1W Cyan books (test) | 15 | 4 | 0 | 4 | -862.97 | 0.005096 | tiny |
| lz_1w | 1W desk | 10 | 1 | 0 | 1 | -323.25 | -0.006501 | tiny |
| lz_s_rules_1w | Lab rule 1W (test) | 6 | 0 | 0 | 0 | 0.00 | 0.026113 | none |
| lz_s_1wc_ml | 1W Cyan tier A mid/large (test) | 3 | 1 | 0 | 1 | -230.62 | 0.015499 | tiny |
| lz_s_q07w_s78_ml_deep70_wcov | Q07 w_swing H78 midlarge deep70+wiki_cov (test) | 3 | 1 | 0 | 1 | -185.02 | 0.008704 | tiny |
| lz_s_1wsw_stress | 1W Swing stress pockets (test) | 1 | 0 | 0 | 0 | 0.00 | 0.037205 | none |
| lz_s_mn_hourly_1w | Midna Hourly 1W (Midna port) | 1 | 0 | 0 | 0 | 0.00 | -0.023936 | none |
| lz_s_q07w_g52_ml_ins2_wlow | Q07 w_green H52 midlarge insider2+wiki_low (test) | 1 | 0 | 0 | 0 | 0.00 | 0.067864 | none |
| lz_s_q07w_s52_ml_cheap5 | Q07 w_swing H52 midlarge cheap5 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.347164 | none |
| lz_s_q07w_s52_ml_deep70_wlow | Q07 w_swing H52 midlarge deep70+wiki_low (test) | 1 | 0 | 0 | 0 | 0.00 | -0.020866 | none |
| lz_s_q07w_s52_ml_ins2_mom6_vix20 | Q07 w_swing H52 midlarge insider2+mom6+stress_vix20 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.010667 | none |
| lz_s_q07w_s52_sm_cheap5_deep70_vix20 | Q07 w_swing H52 small cheap5+deep70+stress_vix20 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.047234 | none |
| lz_s_q07w_s52_sm_cheap5_vix20 | Q07 w_swing H52 small cheap5+stress_vix20 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.047234 | none |
| lz_s_q07w_s78_ml_cheap5 | Q07 w_swing H78 midlarge cheap5 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.347164 | none |
| lz_s_q07w_s78_ml_cheap5_mom6 | Q07 w_swing H78 midlarge cheap5+mom6 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.347164 | none |
| lz_s_q07w_s78_ml_deep70_mom6_wlow | Q07 w_swing H78 midlarge deep70+mom6+wiki_low (test) | 1 | 0 | 0 | 0 | 0.00 | -0.020866 | none |
| lz_s_q07w_s78_sm_cheap5_deep70_vix20 | Q07 w_swing H78 small cheap5+deep70+stress_vix20 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.047234 | none |
| lz_s_q07w_s78_sm_cheap5_vix20 | Q07 w_swing H78 small cheap5+stress_vix20 (test) | 1 | 0 | 0 | 0 | 0.00 | 0.047234 | none |

### 6.3 Realized distribution

Realized over the 132 joined ids: sum -1601.86, median 0.00, mean -12.14, minimum -862.97, maximum 0.00. The maximum is the point: no id in the family carries positive realized. The only nonzero values are the four closed ids, all negative: -862.97, -323.25, -230.62, -185.02. The other 128 joined ids sit at exactly 0.0, 114 of them with no fills at all and 14 with fills still open and ungraded on the closed record.

### 6.4 Coherence verdict for 1w

No single coherent form can be named. The four closed ids carry four different strategy strings (Lab 1W Cyan books; 1W desk; 1W Cyan tier A mid/large; Q07 w_swing H78 midlarge deep70+wiki_cov) spanning three of the family's stream labels and both a lab form and the desk form. The 18 entry ids carry 18 different strategy strings. What the live ids share is only the family label itself, the weekly bucket, and a test grid idiom (12 of the 18 entry ids are Q07 cells and 2 more are lab forms) whose cells differ in horizon (H52 against H78), stream (cyan, green, swing), size tier (micro, small, midlarge) and condition set (cheap5, deep70, mom6, tierA, wiki, insider, stress). A portable form needs one of those cells to be the form, and the closed record cannot pick one: the only cell with a closed trade in size is none, the largest closed count on any single id is 4, and every closed trade in every cell lost. Porting "1w" would port a bucket; porting any single cell would be deciding on at most 4 closed trades, all losses, at confidence tiny. The 1w question is closed by its own numbers: 132 ids, 18 with fills, 4 with closes, 0 wins, realized -1601.86, no positive id.

## 7. COHERENT BUT UNTRADED, AND THE NEAREST MISS

The families that do pass the coherence test fail on substance in the opposite direction. The ausar grid families are genuine forms at grid level: negative_funding_squeeze (60 ids, 30 distinct strategy strings, each carried by exactly 2 ids, an ausar replaced copy joined to the scorecard and an ausar-r19 installed copy recorded only) is one negative funding breakout form over LINKUSDT, ADAUSDT and ENJUSDT cells varying hold (16 hour, 96 hour, failed breakout exit) and sizing (available cash, 1 percent volume cap); etf (52 ids, 26 strategies in the same paired structure), recovery (32 ids, 8 strategies in groups of 4), G4 (24), C1 (18), absorption_base, absorption_negative_funding, absorption_nonnegative_funding and breakout_base (12 each) have the same shape. On the scorecard every joined id in all of these families reads entry_filled 0, n_closed 0, realized 0.0: negative_funding_squeeze's 30 joined ids are all machinery unknown_silent with no journal and no fills; recovery's 16 joined ids are all machinery class with catalog blocked evidence (an options book needing a chain and pricing feed not wired in md2). A census over scorecard fields can name these forms as definitions, but it cannot promote one: there is no live record to decide on, and CONV-58's census was named precisely as a read of the live record. Naming one of these as the portable candidate would be porting an untested definition from another agent's catalog, which is the manufacturing CONV-58 forbids without a Triad decision, and this census gives a Triad nothing to decide with beyond the catalog strings themselves.

The nearest miss in the whole census is sleeves.raschke_pf3, and it is named here so the verdict does not rest on ignoring it. One id, sid raschke_pf3: entry_filled 25, exit_filled 25, n_closed 25, wins 11, losses 14, realized +1104.40, excess_vs_spy +0.208047, beats_spy True, confidence moderate (the joint highest in the population; only 3 of 409 joined ids reach moderate and none reach high), machinery_vs_signal trading, and its evidence field carries real eval decision counts (enter_long 10, enter_short 16, exit_slope_reverse 15, exit_target 3, among other tallies). It fails the bar on completeness, decisively: its strategy field reads, in full, "Adapter for raschke_pf3 (batch 5): v2 ctx -> ported raschke_pf3 signal(). Strategy", a sentence that stops at the word Strategy. The held record names the sleeve, grades its record, and points at a ported signal held elsewhere; the signal's definition, universe, timeframe and exit rules are not in the register, the scorecard, or the dig. On held records there is no form to write into a fresh registration, only a name and a grade. Its 11 wins against 14 losses also mean the positive realized rests on payoff asymmetry that the held records do not document. If the Triad wants this one, what a fresh registration would still need is exactly the missing piece: the raschke_pf3 signal definition from its home codebase, after which it would register as a single sleeve intake (like the t474u intake), not as a family port. That is a request for an external definition, not a candidate this census can name.

## 8. VERDICT: THE QUESTION IS CLOSED WITH EVIDENCE (OPTION B)

No family among the 107 carries a portable form on held records. The census numbers that prove it, each recounted from the rows:

1. Substance is a sliver: 16 of 107 families hold all 184 closed trades; 91 families never filled at all. The whole joined population of 409 ids sums to realized -15766.50 on 61 wins against 123 losses, with only 7 positive ids (+1505.72 combined).
2. Every family with real closed mass is negative at family level: 1h (41 closed, -7971.67), 1d (33 closed, -5186.33), 1w (7 closed, 0 wins, -1601.86), sleeves.free_opt_parity (4 closed, -1761.01), sleeves.ema_vwap (31 closed, -43.93).
3. Every family with positive family realized is a one id family: sleeves.raschke_pf3, intraday_reversal_liquidity_sweep, sleeves.phase_daily, sleeves.ts_momentum_decile, sleeves.morning_dip. Of those five, four carry adapter only strategy fields whose definitions live outside the held records, and the fifth (intraday_reversal_liquidity_sweep, +39.47 on 17 closed, confidence low) carries a nameable sketch with +2.32 per closed trade behind it. None names a family form, and none carries both a definition and an edge in the held record.
4. The one multi id family whose live ids share a single definition, native_trend (Daily SMA200 spot allocation, 2 joined ids), closed 4 trades for realized exactly 0.00 and zero nonzero ids.
5. The large coherent families (negative_funding_squeeze 60, etf 52, recovery 32, G4 24, C1 18, the absorption and breakout grids at 12 each) are definable grids with zero fills, zero closes and zero realized on every joined id: coherence without a record.
6. The 1w family, read first and in full as CONV-58 directed, is 132 distinct definitions in a weekly bucket; its live ids share no definition, its closed ids are 4, its wins are 0, and no id in it is positive (section 6).

Scope of the closure, stated exactly: this verdict covers the 556 decomposed catalog ids in 107 families and their 409 joined scorecard records. It does not cover the 65 residual ids, which remain unnamed on their external datum exactly as CONV-58 left them (the master desk catalog at a 2026-11-11 to 2026-11-14 state, or GrokBot's reply to the desktriad post p7iq9o), nor the 20 t474u intake ids, which carry no scorecard and were registered through their own intake. If the residual ids are ever named and joined, they would need their own census before this verdict could extend to them.

What would reopen the question, named so the closure is falsifiable: (a) a signal definition arriving from outside the held records for a graded singleton, raschke_pf3 first, which converts the question from a family port to a single sleeve intake decision; (b) any of the coherent ausar grids acquiring a live record on md2 with positive family realized; (c) the residual 65 being named and joined with a family that passes all three tests in section 3. None of the three is in the held records tonight.

STATUS: GREEN for the census task itself, proven on this final artifact: 577 register rows recounted with zero disagreement against the brief, 107 catalog families censused over the register's own scorecard fields (table in section 4, column sums re-asserted in section 2), the 1w family read in full (section 6), and the CONV-58 question closed with evidence under option (b) for the 556 decomposed ids, with the residual 65 and the t474u 20 explicitly outside the closure. Evidence pointer: this file, CONV58-MD2-FAMILY-CENSUS.md, computed from pass2/MD2-REGISTER.jsonl; the CONVERSION-REGISTER files and the desk tree were not modified.
