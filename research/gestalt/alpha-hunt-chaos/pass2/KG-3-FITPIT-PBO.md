# KG-3. FIT-PIT LEAVE-ONE-OUT PBO: THE LEG IS A COMPOSITION EFFECT, AND THE MEDIAN DOES NOT CLEAR

## DISPOSITION: FIT-PIT STAYS WATCH

The disposition rule was fixed before the run: FIT-PIT advances to a registered forward falsifier design only if the leave-one-out median PBO clears the 0.20 bar, with the interquartile range printed. It does not clear. On the rebuilt count-46 matrix, the 42 leave-one-out fold PBOs have median 0.2444, interquartile range [0.2222, 0.2667], mean 0.2444, minimum 0.0444, and maximum 0.4222. Only 1 of 42 folds prints below 0.20. FIT-PIT therefore stays WATCH, for the leg anatomy priced below, and no forward falsifier design is printed, because the rule that would authorize one was not met.

The member-level record is unchanged and is not what failed: FIT-PROXY-PIT-v1 (PROXY) stands at mean +13.72bp per night, Sharpe 1.462, t 4.35, DSR 0.99688 at count 46, SPA 0.002 against SPY and 0.003 against QQQ. The full rebuilt matrix PBO reproduced exactly at 0.2222 (10 of 45 CPCV splits at or below the OOS median), against the promotion bar of below 0.20.

## WHAT THE LEAVE-ONE-OUT DISTRIBUTION SAYS

One fold in 42 moves the PBO down materially, and it is not the candidate. Removing ON_1n_RKLB drops the PBO from 0.2222 to 0.0444 (delta -0.1778, bad splits 10 to 2). Every other removal leaves the PBO unchanged or raises it: 17 folds print 0.2222, 5 print 0.2444, 18 print 0.2667, and removing ON_energy8 raises it to 0.4222 (delta +0.2000, bad splits 10 to 19). Removing FIT-PIT itself raises the PBO to 0.2667 (delta +0.0444, bad splits 10 to 12): the candidate is not the carrier of the failing leg, and deleting it makes the leg worse.

The split anatomy names the carrier. In the full rebuilt matrix the in-sample winner is ON_energy8 in 30 of 45 splits (none bad), ON_1n_RKLB in 10 (9 bad), ON_focus29 in 4 (none bad), and ON_1n_TSM in 1 (bad). Nine of the ten bad splits are therefore one pattern: RKLB wins the training window and ranks at or below the OOS median. Remove RKLB and the bad count falls to 2, both TSM-winner splits; remove RKLB and TSM together in the targeted leave-two-out check and the PBO prints 0.0000.

## WHY THE AS-STAMPED MATRIX PRINTED 0.000

The count-45 comparator reproduces the Wave 4 result exactly: full PBO 0.0000, leave-one-out median 0.0000 with interquartile range [0.0000, 0.0000], and 41 of 42 folds at 0.0000. The single exception is removing the as-stamped ON_fit_lo14 column, which raises the PBO to 0.2667. The shared 41-column core, with neither FIT variant present, prints PBO 0.2667 with 12 bad splits (RKLB-winner 9, ON_focus29-winner 2, TSM-winner 1).

The mechanism is winner substitution. The as-stamped lookahead column is the in-sample winner in 38 of 45 splits and holds up out of sample, as a lookahead artifact does, so it masks the core's RKLB signature completely. The lawful PIT column never wins a training split; adding it to the core only moves the relative rank of the winner in two splits, taking the bad count from 12 to 10 and the PBO from 0.2667 to 0.2222. The 0.222 is therefore not a property of FIT-PIT, and not a diffuse property of the whole family either. It is a concentrated composition effect: a one-column overfit signature (RKLB) in the core matrix, unmasked when the lookahead column that used to win the training splits was lawfully replaced, and partly suppressed by ON_energy8, whose removal is the largest upward move in the table (+0.2000).

## METHOD

Matrices rebuilt exactly as in keepgoing2/wave7/w7b_fit_pit_exam.py: 2,229 sessions, 2018-01-03 to 2026-11-13, 42 columns. The count-46 form replaces ON_fit_lo14 with the point-in-time rebuilt ON_fit_lo14_pit series from w7b_fit_pit_series.json; the count-45 form keeps the as-stamped ON_fit_lo14 column. PBO is admission_exam.cpcv_pbo at its defaults (10 contiguous groups, 2 test groups per split, 45 splits, purge 1 bar, embargo 1 bar; a split is bad when the logit of the in-sample winner's OOS relative rank is at or below 0). A leave-one-out fold deletes one column and recomputes the PBO on the remaining 41 columns. Quartiles use linear interpolation. Validation: the rebuilt full matrix reproduces the Wave 7 exam PBO of 0.222222 to the printed digit, and the as-stamped full matrix reproduces the Wave 4 PBO of 0.000000.

Count context, stated once: the nominal trial count (45, 46, or 61) enters the exam's DSR leg, not cpcv_pbo, which takes only the return matrix. At a nominal count of 61 with these same 42 columns the leave-one-out PBO distribution would be identical to the count-46 distribution above; count 61 in the record belongs to the separate seven-column Wednesday exam, which contains no FIT column and prices a different matrix.

## TARGETED LEAVE-TWO-OUT CHECKS

Pairs selected from the leave-one-out anatomy before running (the dominant downward mover, the candidate, the dominant upward mover, the residual bad-split winner). This is a targeted interaction check, not a full 861-pair sweep.

| Removed pair | PBO | Bad splits / 45 |
|---|---:|---:|
| ON_1n_RKLB + ON_fit_lo14_pit | 0.0444 | 2 |
| ON_1n_RKLB + ON_energy8 | 0.1778 | 8 |
| ON_fit_lo14_pit + ON_energy8 | 0.4222 | 19 |
| ON_1n_RKLB + ON_1n_TSM | 0.0000 | 0 |
| ON_1n_RKLB + ON_focus29 | 0.0444 | 2 |

Read: RKLB plus TSM together account for every bad split the RKLB removal leaves behind; RKLB plus FIT-PIT prints the same 0.0444 as RKLB alone, confirming FIT-PIT is not part of the carrier pair; FIT-PIT plus energy8 prints the same 0.4222 as energy8 alone, confirming energy8's suppressor role does not run through the candidate.

## FOLD TABLE, COUNT-46 REBUILT MATRIX (PRIMARY)

Full-matrix PBO 0.2222 (10 bad splits of 45).

| # | Removed column (leave-one-out) | Fold PBO | Bad splits / 45 | Delta vs full |
|---:|---|---:|---:|---:|
| 1 | ON_focus29 | 0.2222 | 10 | +0.0000 |
| 2 | INTRADAY_focus29 | 0.2444 | 11 | +0.0222 |
| 3 | ON_basket8 | 0.2667 | 12 | +0.0444 |
| 4 | INTRADAY_basket8 | 0.2222 | 10 | +0.0000 |
| 5 | ON_spy | 0.2444 | 11 | +0.0222 |
| 6 | INTRADAY_spy | 0.2222 | 10 | +0.0000 |
| 7 | ON_semis12 | 0.2667 | 12 | +0.0444 |
| 8 | ON_photonics3 | 0.2667 | 12 | +0.0444 |
| 9 | ON_aiinfra4 | 0.2667 | 12 | +0.0444 |
| 10 | ON_energy8 | 0.4222 | 19 | +0.2000 |
| 11 | ON_fit_hi15 | 0.2667 | 12 | +0.0444 |
| 12 | ON_fit_lo14_pit | 0.2667 | 12 | +0.0444 |
| 13 | ON_broad100 | 0.2222 | 10 | +0.0000 |
| 14 | ON_1n_SMH | 0.2667 | 12 | +0.0444 |
| 15 | ON_1n_SOXX | 0.2667 | 12 | +0.0444 |
| 16 | ON_1n_NVDA | 0.2667 | 12 | +0.0444 |
| 17 | ON_1n_AVGO | 0.2222 | 10 | +0.0000 |
| 18 | ON_1n_AMD | 0.2222 | 10 | +0.0000 |
| 19 | ON_1n_MRVL | 0.2667 | 12 | +0.0444 |
| 20 | ON_1n_ARM | 0.2222 | 10 | +0.0000 |
| 21 | ON_1n_TSM | 0.2444 | 11 | +0.0222 |
| 22 | ON_1n_AMAT | 0.2667 | 12 | +0.0444 |
| 23 | ON_1n_MU | 0.2667 | 12 | +0.0444 |
| 24 | ON_1n_SNDK | 0.2222 | 10 | +0.0000 |
| 25 | ON_1n_WDC | 0.2667 | 12 | +0.0444 |
| 26 | ON_1n_AAOI | 0.2444 | 11 | +0.0222 |
| 27 | ON_1n_COHR | 0.2222 | 10 | +0.0000 |
| 28 | ON_1n_LITE | 0.2667 | 12 | +0.0444 |
| 29 | ON_1n_CRDO | 0.2667 | 12 | +0.0444 |
| 30 | ON_1n_ALAB | 0.2222 | 10 | +0.0000 |
| 31 | ON_1n_AXTI | 0.2667 | 12 | +0.0444 |
| 32 | ON_1n_CRWV | 0.2222 | 10 | +0.0000 |
| 33 | ON_1n_PLTR | 0.2667 | 12 | +0.0444 |
| 34 | ON_1n_RKLB | 0.0444 | 2 | -0.1778 |
| 35 | ON_1n_FLNC | 0.2222 | 10 | +0.0000 |
| 36 | ON_1n_EOSE | 0.2222 | 10 | +0.0000 |
| 37 | ON_1n_FCEL | 0.2222 | 10 | +0.0000 |
| 38 | ON_1n_BE | 0.2222 | 10 | +0.0000 |
| 39 | ON_1n_OKLO | 0.2444 | 11 | +0.0222 |
| 40 | ON_1n_VST | 0.2222 | 10 | +0.0000 |
| 41 | ON_1n_CEG | 0.2667 | 12 | +0.0444 |
| 42 | ON_1n_XLE | 0.2222 | 10 | +0.0000 |

## FOLD TABLE, COUNT-45 AS-STAMPED MATRIX (COMPARATOR)

Full-matrix PBO 0.0000 (0 bad splits of 45). This matrix contains the labeled lookahead artifact and is printed as composition evidence only, never as evidence for the candidate.

| # | Removed column (leave-one-out) | Fold PBO | Bad splits / 45 | Delta vs full |
|---:|---|---:|---:|---:|
| 1 | ON_focus29 | 0.0000 | 0 | +0.0000 |
| 2 | INTRADAY_focus29 | 0.0000 | 0 | +0.0000 |
| 3 | ON_basket8 | 0.0000 | 0 | +0.0000 |
| 4 | INTRADAY_basket8 | 0.0000 | 0 | +0.0000 |
| 5 | ON_spy | 0.0000 | 0 | +0.0000 |
| 6 | INTRADAY_spy | 0.0000 | 0 | +0.0000 |
| 7 | ON_semis12 | 0.0000 | 0 | +0.0000 |
| 8 | ON_photonics3 | 0.0000 | 0 | +0.0000 |
| 9 | ON_aiinfra4 | 0.0000 | 0 | +0.0000 |
| 10 | ON_energy8 | 0.0000 | 0 | +0.0000 |
| 11 | ON_fit_hi15 | 0.0000 | 0 | +0.0000 |
| 12 | ON_fit_lo14 | 0.2667 | 12 | +0.2667 |
| 13 | ON_broad100 | 0.0000 | 0 | +0.0000 |
| 14 | ON_1n_SMH | 0.0000 | 0 | +0.0000 |
| 15 | ON_1n_SOXX | 0.0000 | 0 | +0.0000 |
| 16 | ON_1n_NVDA | 0.0000 | 0 | +0.0000 |
| 17 | ON_1n_AVGO | 0.0000 | 0 | +0.0000 |
| 18 | ON_1n_AMD | 0.0000 | 0 | +0.0000 |
| 19 | ON_1n_MRVL | 0.0000 | 0 | +0.0000 |
| 20 | ON_1n_ARM | 0.0000 | 0 | +0.0000 |
| 21 | ON_1n_TSM | 0.0000 | 0 | +0.0000 |
| 22 | ON_1n_AMAT | 0.0000 | 0 | +0.0000 |
| 23 | ON_1n_MU | 0.0000 | 0 | +0.0000 |
| 24 | ON_1n_SNDK | 0.0000 | 0 | +0.0000 |
| 25 | ON_1n_WDC | 0.0000 | 0 | +0.0000 |
| 26 | ON_1n_AAOI | 0.0000 | 0 | +0.0000 |
| 27 | ON_1n_COHR | 0.0000 | 0 | +0.0000 |
| 28 | ON_1n_LITE | 0.0000 | 0 | +0.0000 |
| 29 | ON_1n_CRDO | 0.0000 | 0 | +0.0000 |
| 30 | ON_1n_ALAB | 0.0000 | 0 | +0.0000 |
| 31 | ON_1n_AXTI | 0.0000 | 0 | +0.0000 |
| 32 | ON_1n_CRWV | 0.0000 | 0 | +0.0000 |
| 33 | ON_1n_PLTR | 0.0000 | 0 | +0.0000 |
| 34 | ON_1n_RKLB | 0.0000 | 0 | +0.0000 |
| 35 | ON_1n_FLNC | 0.0000 | 0 | +0.0000 |
| 36 | ON_1n_EOSE | 0.0000 | 0 | +0.0000 |
| 37 | ON_1n_FCEL | 0.0000 | 0 | +0.0000 |
| 38 | ON_1n_BE | 0.0000 | 0 | +0.0000 |
| 39 | ON_1n_OKLO | 0.0000 | 0 | +0.0000 |
| 40 | ON_1n_VST | 0.0000 | 0 | +0.0000 |
| 41 | ON_1n_CEG | 0.0000 | 0 | +0.0000 |
| 42 | ON_1n_XLE | 0.0000 | 0 | +0.0000 |

## BAD SPLITS, COUNT-46 FULL MATRIX

| Test groups | IS-best | IS Sharpe (daily) | OOS Sharpe (daily) | omega | lambda |
|---|---|---:|---:|---:|---:|
| 1, 2 | ON_1n_RKLB | 0.1125 | 0.0000 | 0.2674 | -1.0076 |
| 1, 10 | ON_1n_RKLB | 0.1214 | 0.0114 | 0.0930 | -2.2773 |
| 2, 3 | ON_1n_RKLB | 0.1125 | 0.0000 | 0.1628 | -1.6376 |
| 2, 6 | ON_1n_TSM | 0.1206 | -0.0312 | 0.1628 | -1.6376 |
| 2, 7 | ON_1n_RKLB | 0.1069 | 0.0702 | 0.4186 | -0.3285 |
| 2, 9 | ON_1n_RKLB | 0.1110 | 0.0550 | 0.3488 | -0.6242 |
| 2, 10 | ON_1n_RKLB | 0.1214 | 0.0114 | 0.0698 | -2.5903 |
| 7, 10 | ON_1n_RKLB | 0.1166 | 0.0535 | 0.1628 | -1.6376 |
| 8, 10 | ON_1n_RKLB | 0.1075 | 0.0885 | 0.3721 | -0.5232 |
| 9, 10 | ON_1n_RKLB | 0.1227 | 0.0476 | 0.2326 | -1.1939 |

## FILES

- pass2/kg3_fitpit_pbo.py and pass2/kg3_fitpit_pbo.json: matrix build, full PBOs, all 84 folds and distributions.
- pass2/kg3_cpcv_anatomy.py and pass2/kg3_cpcv_anatomy.json: split-level winners, lambdas, and fold comparisons.
- pass2/kg3_selected_lto.py and pass2/kg3_selected_lto.json: the targeted leave-two-out checks.
- Sources: keepgoing2/wave7/w7b_fit_pit_exam.py, w7b_fit_pit_exam.json, w7b_fit_pit_series.json, W7B-FITPIT-PEAD.md; keepgoing2/wave4/v2_family_exam.py and v2_family_exam.json; tools/admission_exam.py.

STATUS: GREEN, proven on the final artifacts. EVIDENCE POINTER: pass2/kg3_fitpit_pbo.json (count-46 full PBO 0.2222 reproduced; 42 folds, median 0.2444, IQR [0.2222, 0.2667]) and pass2/kg3_cpcv_anatomy.json (9 of 10 bad splits are RKLB-winner splits; removing RKLB prints 0.0444; removing FIT-PIT prints 0.2667). Disposition: FIT-PIT stays WATCH under the pre-fixed rule; the daily quarter-to-date PIT form (trial 47) is not authorized by this read and remains unrun.
