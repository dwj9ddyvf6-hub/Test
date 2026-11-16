# LANE 9: GO DEEPER ON THE THREE LIVE THREADS

Owner order Sun 2026-11-15: "go further and further and deeper and deeper." Three sections, every number computed in this pass from estate records, scripts kept in `lane9_work/` beside this file (`s1_inversion.py`, `s2_segments.py`, `s3_disagreement.py`, outputs `s1_inversion.json`, `s2_segments.json`, `s3_disagreement.json`). No trading. Read-only on strategies.

Replication gates passed before any new number was trusted: the C-1 anti-Midna pooled result rebuilt from the study files reproduces the founding measurement exactly (+268.80bp, t 4.37, n 58, hit 0.724, net of 5bp +263.80); the Focus basket overnight series reproduces the overnight edge's founding statistics exactly (2,229 sessions, t 4.97); Lane 3's segment table reproduces within the filter differences named in Section 2.

## 1. THE INVERSION AUTOPSY

### 1.1 The construction, reconstructed exactly

Source: `foundry/c1_anti_midna.py` and `conversion/ANTI-MIDNA-CONTROL-LINE-SPEC-2026-11-15.md`. The anti-Midna portfolio is built from the night study's own stated directional conclusions, in two extraction forms:

- **TARGET cohorts** (studies of 2026-11-11 and 2026-11-12, `entries.md`): per Focus name, bias = sign(base-case target minus last close), target and close read from the entry's own text. Zero difference is no position.
- **STAGE cohorts** (studies of 2026-11-09 and 2026-11-10, `fragment_set*.md`): Pass A Stage 2 is +1, Stage 4 is -1, Stages 1, 3, and unnumbered posture language are no position.

Per positioned name, the anti return is minus bias times the forward overnight return (close on the study's asof date to next session's open, SIP split-adjusted daily bars, `keepgoing2/wave3/focus_bars.json`). Four cohort nights, 58 positions. The decisive structural fact, confirmed on the rebuild: **every cohort is one-signed.** TARGET cohorts ran 21 of 21 and 22 of 22 long; STAGE cohorts ran 7 of 7 and 8 of 8 short. The study never discriminated within a night, so the anti book is, by construction, a signed position in the whole complex each night: short it on TARGET nights, long it on STAGE nights.

One naming discrepancy found in the spec and printed here because the autopsy turns on it: the spec's prose defines the control as "short the whole complex, ignoring the study entirely" (an always-short line), but the founding table's control column is computed as the **sign-matched** universe term, minus bias times the complex mean, which is short the complex on TARGET nights and long it on STAGE nights. The founding pooled numbers (+272.13 control, -3.33 excess) reconcile only with the sign-matched computation, and it is the economically coherent one (anti and control hold the same side each night). On the literal always-short definition the pooled control is +170.34bp and the pooled "excess" is +98.45bp (t 1.21), a number manufactured entirely by sign mismatch on the two STAGE nights (nightly excesses -654.42 and +1,292.74bp that net against the true selection terms). Everything below uses the as-computed, sign-matched basis.

### 1.2 The exact decomposition

Every anti position splits exactly into a universe term (minus bias times that night's equal-weight complex overnight mean) and an idiosyncratic term (the positioned name's overnight return minus the complex mean, signed the same way). Pooled over 58 positions:

| Component | Mean bp | t (positions) | Hit |
|---|---|---|---|
| Anti-Midna book | +268.80 | 4.37 | 0.724 |
| Universe term (sign-matched EW complex) | +272.13 | 6.64 | 0.879 |
| Idiosyncratic (selection) term | -3.34 | -0.08 | 0.483 |
| Study's own side (mirror) | -268.80 | -4.37 | 0.276 |

**101 percent of the anti book's pooled return is the universe term.** The selection term is -3.34bp with a hit rate of 0.483, a coin flip. This is the founding -3.33bp excess, identified: it is not an approximation of the selection effect, it is the selection effect, and it is zero.

### 1.3 Per-night attribution against all three benchmarks

| Cohort night | Pos | Bias split | Complex ON | SPY ON | QQQ ON | Anti bp | Universe term | Idio term | Anti book beta | Excess vs beta-matched SPY |
|---|---|---|---|---|---|---|---|---|---|---|
| TARGET 2026-11-11 | 21 | 21 long | -546.17 | -76.73 | -145.79 | +522.58 (t 5.08) | +546.17 | -23.59 | -3.30 | +269.23 |
| TARGET 2026-11-12 | 22 | 22 long | -61.92 | +38.96 | +5.38 | +82.13 (t 3.09) | +61.92 | +20.21 | -3.34 | +212.18 |
| STAGE 2026-11-09 | 7 | 7 short | -275.22 | -63.11 | -100.24 | -379.20 (t -5.35) | -275.22 | -103.98 | +3.52 | -157.10 |
| STAGE 2026-11-10 | 8 | 8 short | +609.81 | +91.74 | +185.55 | +682.93 (t 4.82) | +609.81 | +73.13 | +3.23 | +386.78 |

(Beta: trailing 120-session close-to-close beta of each positioned name vs SPY, meaned with the anti book's sign. Excess vs beta-matched: anti return minus minus-bias times beta times SPY's overnight return, per position.)

Reading the three comparisons:

- **(a) The plain equal-weight universe.** Taken long on all four nights, the complex returned -170.34bp position-weighted; taken with the anti book's own nightly sign, +272.13bp. The anti book's entire win over a passive long is the sign flip, and the sign came from the study's posture, inverted. Per name, the anti book selected nothing: on TARGET nights it held 21 to 22 of the 29 names, so its subset was most of the universe by construction, and its idio terms there are small (-23.59, +20.21). On STAGE nights the subsets were small (7, 8 names) and the idio terms were large and offsetting (-103.98, +73.13): subset selection noise, netting to nothing.
- **(b) SPY and QQQ.** The complex's overnight moves on these four nights (-546, -62, -275, +610bp) were 3 to 7 times SPY's (-77, +39, -63, +92bp) and opposite-signed on 2026-11-12. The anti book was not harvesting index beta; it was harvesting the complex's own overnight movement, which on this record is mostly idiosyncratic to the complex.
- **(c) The beta-matched basket.** The anti book beat a beta-matched SPY basket by +212.35bp pooled (t 4.74, per-position). That residual is real arithmetic and a false lead: beta-matching to SPY cannot absorb a complex-specific overnight factor, and the residual is exactly that factor (the complex fell overnight far beyond its SPY beta on 11-11 and rose beyond it on 11-10). Within the complex, where selection would have to live, the term is -3.34bp. The beta-matched comparison measures complex-vs-index divergence, not inversion skill.

### 1.4 Concentration

- **By night:** TARGET 2026-11-11 alone contributes 70.4 percent of the pooled net sum. Leave-one-night-out pooled anti means: without 11-11, +124.76bp; without 11-12, +382.87; without 11-09, +357.74; without 11-10, +202.53.
- **By name:** 23 distinct names were positioned. CRWV alone totals +3,204.3bp across 3 positions, 19.5 percent of gross absolute P&L; the top three names (CRWV, AXTI +1,496.2, AAOI +1,183.3) are 35.8 percent of gross. Leave-CRWV-out pooled anti: +225.20bp.
- **The honest unit:** the founding t 4.37 treats 58 positions across 4 nights as independent. Clustered by night, the anti book's nightly means (+522.58, +82.13, -379.20, +682.93) give an equal-weight mean of +227.11bp at **t 0.95 on 4 nights**: the anti book itself does not separate from zero at the night level either. The selection excess at night level: equal-weight +158.73bp on the literal-control basis is the sign artifact above; the idio term's nightly means (-23.59, +20.21, -103.98, +73.13) give t -0.23. Zero at every honest unit.

### 1.5 Verdict

**The control's return is universe beta, in the strict sense that matters: it is the Focus complex's own overnight return with the sign flipped, and the inverted selection adds nothing to it (idio term -3.34bp, t -0.08, hit 0.483).** It is not SPY or QQQ beta; the complex's overnight moves on these nights were largely its own. Nor does the inversion "carry signal" in reverse: the study's per-name conclusions and their negation are equally information-free on this record, because the conclusions were one-signed per night and therefore contained no per-name information to invert. What the founding measurement actually proved is narrower and still valuable: on four extreme nights, being on the opposite side of the study's posture was worth the complex's overnight move, and the standing control line (night study step 11) is the right instrument to keep measuring the excess, which is the only term that can ever convict or clear the study's selection. The forward cohort frozen at the 2026-11-13 close (29 names, 28 short bias) reads overnight Mon 2026-11-16 under that line.

## 2. SEGMENT WIDENING

### 2.1 What the caches honestly support

Lane 3's decomposition ran on the desk 1Min cache: 21 large-cap symbols, 14 sessions. Widening has two different honest answers per segment:

- **Overnight (and open-to-close)** can widen fully: `focus_bars.json` holds SIP split-adjusted daily bars for 29 of the 30 Focus names (SIVE has no bars anywhere in the estate) from each name's first session to 2026-11-13, SPY and QQQ included from 2018-01-02. The basket series (equal-weight per night, nights with at least 10 names present) runs 2,229 nights, 2018-01-03 to 2026-11-13.
- **Intraday segments** (open drive, midday, close hour) cannot widen in time or universe from stored caches: the 1Min cache is the only minute store, covering the same 21 symbols and 14 sessions Lane 3 used, of which 6 are Focus names (AMAT, AMD, AVGO, MU, NVDA, PLTR). The tensor replay hourly bars were checked and rejected for segment work: clock-hour bars do not align to the 10:30 and 15:00 segment boundaries, and they cover 18 small caps, not this universe. So the intraday widening below is the Focus-6 subset on the same 13 return-sessions (14 sessions; overnight and segments computed per symbol-session, first session consumed as the prior close), with Lane 3's 21-symbol universe recomputed beside it.

Earnings-gap contamination: the terminal earnings archive (`realised_moves.json`, 206 recorded events, session dates 2026-10-13 to 2026-11-05) flags only 4 Focus name-nights in the Part A recent window and 3 rows in the Part B window, too few to move any number; it is reported as run. The load-bearing sensitivity is mechanical: a name-night is gap-flagged when its absolute overnight return exceeds 3 times its trailing-60 median absolute overnight return (5555 of 51,970 name-nights, 10.69 percent; flagged nights average +69.0bp, so the flag removes real signal mass, not just noise).

### 2.2 Overnight on the full Focus complex, 2018 to 2026 (daily bars)

| Series | n (nights) | Mean bp | Median bp | Win | t (nights) |
|---|---|---|---|---|---|
| Focus basket overnight | 2,229 | +16.46 | +22.58 | 0.585 | 4.97 |
| First half (to 2022-06-06) | 1,114 | +14.88 | +22.99 | 0.602 | 3.61 |
| Second half | 1,115 | +18.03 | +22.39 | 0.567 | 3.48 |
| Basket ex gap-flagged name-nights | 2,149 | +12.24 | +18.22 | 0.571 | 5.24 |
| Focus basket intraday (open to close) | 2,229 | +0.18 | +0.78 | 0.502 | 0.04 |
| SPY overnight (same nights) | 2,229 | +3.53 | +7.20 | 0.565 | 2.18 |
| QQQ overnight (same nights) | 2,229 | +4.85 | +8.78 | 0.562 | 2.50 |
| Recent window ex earnings (2026-10-13 on) | 24 | -56.31 | -121.41 | 0.417 | -0.79 |

Per-name overnight (sorted; intraday mean shown for contrast):

| Name | From | n | ON mean | ON median | ON win | ON t | Intraday mean |
|---|---|---|---|---|---|---|---|
| SNDK | 2025-02-14 | 440 | +44.10 | +27.64 | 0.545 | 2.43 | +49.65 |
| FCEL | 2018-01-03 | 2229 | +42.03 | +14.31 | 0.509 | 4.22 | -29.39 |
| CRWV | 2025-03-31 | 410 | +41.08 | +42.77 | 0.559 | 2.13 | -10.77 |
| RKLB | 2020-11-25 | 1499 | +31.98 | +24.69 | 0.559 | 4.75 | -6.88 |
| EOSE | 2020-06-04 | 1621 | +29.97 | +5.00 | 0.502 | 3.37 | -13.30 |
| ALAB | 2024-03-21 | 666 | +24.54 | +27.67 | 0.559 | 1.86 | +12.10 |
| BE | 2018-07-26 | 2088 | +22.97 | +15.87 | 0.525 | 3.13 | +4.16 |
| OKLO | 2021-07-09 | 1345 | +20.84 | +0.00 | 0.477 | 3.08 | +0.19 |
| FLNC | 2021-10-29 | 1266 | +20.78 | +9.40 | 0.517 | 2.08 | -17.89 |
| CRDO | 2022-01-28 | 1204 | +18.84 | +5.68 | 0.504 | 2.06 | +15.12 |
| AMD | 2018-01-03 | 2229 | +17.79 | +16.56 | 0.549 | 3.74 | +6.24 |
| AXTI | 2018-01-03 | 2229 | +17.00 | +0.00 | 0.471 | 2.97 | +4.61 |
| MRVL | 2018-01-03 | 2229 | +16.75 | +14.68 | 0.537 | 3.43 | -1.69 |
| CEG | 2022-02-03 | 1200 | +16.62 | +11.81 | 0.557 | 3.43 | +1.87 |
| TSM | 2018-01-03 | 2229 | +15.66 | +11.93 | 0.544 | 4.35 | -2.68 |
| NVDA | 2018-01-03 | 2229 | +15.51 | +20.23 | 0.560 | 3.69 | +5.34 |
| AAOI | 2018-01-03 | 2229 | +14.62 | +2.57 | 0.502 | 2.21 | +6.11 |
| ARM | 2023-09-15 | 795 | +14.60 | +18.87 | 0.542 | 1.44 | +10.02 |
| LITE | 2018-01-03 | 2229 | +14.52 | +11.36 | 0.541 | 3.01 | +3.77 |
| MU | 2018-01-03 | 2229 | +14.48 | +12.51 | 0.534 | 3.08 | +4.09 |
| COHR | 2018-01-03 | 2229 | +13.89 | +12.69 | 0.537 | 2.62 | +0.69 |
| PLTR | 2020-10-01 | 1538 | +13.49 | +6.56 | 0.518 | 2.07 | +15.11 |
| AVGO | 2018-01-03 | 2229 | +13.42 | +11.32 | 0.541 | 3.77 | +1.48 |
| SMH | 2018-01-03 | 2229 | +10.71 | +13.89 | 0.553 | 3.54 | +1.93 |
| VST | 2018-01-03 | 2229 | +10.46 | +8.03 | 0.533 | 3.22 | +2.40 |
| SOXX | 2018-01-03 | 2229 | +9.26 | +12.40 | 0.547 | 3.02 | +2.51 |
| WDC | 2018-01-03 | 2229 | +8.58 | +5.73 | 0.517 | 1.83 | +2.98 |
| AMAT | 2018-01-03 | 2229 | +8.51 | +13.55 | 0.541 | 2.11 | +4.57 |
| XLE | 2018-01-03 | 2229 | +5.33 | +9.50 | 0.537 | 1.98 | -0.90 |

Every one of the 29 names has a positive overnight mean; the five Wave-4 carry names sit at SNDK +44.10, CRWV +41.08, RKLB +31.98, AMD +17.79, NVDA +15.51bp on this daily-bar basis.

### 2.3 Intraday segments on the 1Min cache (13 return-sessions, 2026-10-22 to 2026-11-12)

Replication of Lane 3 first: pooled over the 21 symbols, overnight +12.89 (Lane 3: +15.6), open drive +11.83 (+11.7), midday -33.69 (-28.9), close hour -9.37 (-7.8). The differences are the completeness filter (at least 380 RTH bars and all four segment marks present) and the overnight definition (prior complete in-cache session, 13 returns per symbol, 273 rows, against Lane 3's 294). The shape is identical.

Focus-6 subset, pooled (78 symbol-sessions) and session-clustered (13 session means):

| Segment | Pooled mean bp | Pooled win | Pooled t | Session-mean bp | Session t |
|---|---|---|---|---|---|
| Overnight | +10.61 | 0.513 | 0.20 | +10.61 | 0.10 |
| Open drive | +36.84 | 0.603 | 1.14 | +36.84 | 0.57 |
| Midday | -81.63 | 0.321 | -3.68 | -81.63 | -1.82 |
| Close hour | -14.35 | 0.487 | -1.06 | -14.35 | -0.50 |

All-21 session-clustered: midday -33.69bp at session t -1.53; overnight +12.89 at t 0.31. Excluding the 3 archive-flagged earnings rows changes nothing (all-21 midday -32.30; Focus-6 identical, none of its rows flagged).

Focus-6 per-name midday (13 sessions each): NVDA -111.71 (win 0.077, per-name t -4.29), MU -132.65 (0.231, -2.28), AMAT -111.56 (0.308, -1.88), AVGO -57.65 (0.385, -1.95), AMD -45.73 (0.385, -0.54), PLTR -30.48 (0.538, -0.62). All six negative. Focus-6 per-name overnight in this window is mixed (AMD +102.16, AVGO +104.36, AMAT +37.49, MU +47.17, NVDA -139.84, PLTR -87.67), consistent with the negative recent window in Part A.

Sub-period stability, Focus-6 session means: first half (6 sessions) midday -154.24bp, win 0.000, session t -2.36; second half (7 sessions) midday -19.40bp, win 0.429, session t -0.35. The midday drag in this window is a first-half phenomenon that faded.

### 2.4 Verdicts

- **Overnight: SURVIVES widening, decisively, on the daily-bar basis.** Full Focus complex, 2,229 nights: +16.46bp at night-level t 4.97 (the basket series is already one observation per night, so this t is the clustered t), both halves positive and significant (t 3.61 and 3.48), all 29 names positive, and it survives removing every event-like gap night (+12.24bp, t 5.24), which costs it about a quarter of its mean. SPY and QQQ overnight over the same nights are +3.53 and +4.85bp, so the complex carries roughly 3.5 to 4.7 times the index overnight premium. Two caveats stand exactly as before: this is the daily-bar open basis, not auction prints (the Wave 5 basis problem; the ON falsifier tracker owns the print basis from Mon 2026-11-16), and the most recent five weeks run cold (recent-window basket -56.31bp ex-earnings, t -0.79, 24 nights). The 60-session forward falsifier from 2026-11-16 remains the deciding instrument; nothing here amends it.
- **Midday: corroborated in direction, NOT proven at the honest unit, and sub-period unstable.** On the only intraday data the estate stores, midday is again the only negative segment in both universes, deeper on the Focus subset (-81.63bp pooled, all six names negative), but at session-cluster level it does not clear (t -1.53 all-21, -1.82 Focus-6, 13 sessions), and the Focus-6 effect halves away across the window's two halves (-154.24 to -19.40bp). Lane 3's -28.9bp was a pooled statement over one window; widened and clustered, midday is a live hypothesis with the right sign, awaiting more cached sessions. It does not graduate on this evidence.

## 3. THE DISAGREEMENT SIGNAL, DEEPENED

### 3.1 A correction on the face of it

Lane 8's headline contrast (agreement 0.724 vs deep-disagreement 0.273) mislabels its own cells, and the deepening starts by saying so. Both cells are **exact-agreement** cells: bull_above|bull_above (both stacks bullish-ordered above price) and mixed_below|mixed_below (both stacks in the same mixed-below state). The contrast runs along the agreement diagonal, from joint-bullish posture to joint-below posture. It is not, as stated, an agreement-versus-disagreement contrast. What follows separates the three things the headline mixes: cross-stack distance (true disagreement), joint posture (level), and composition (which calls, on which symbols, in which weeks, land in each cell). Posture scores: bull_above +2, mixed_above +1, mixed_below -1, bear_below -2. Sample: the 135 graded retrospective forecast rows carrying both mechanical axes (base hit rate 0.659).

### 3.2 The full grid, and the two margins

| A05 \ A06 | bull_above | mixed_above | mixed_below | bear_below |
|---|---|---|---|---|
| bull_above | 42/58 = 0.724 | (none) | (none) | (none) |
| mixed_above | 4/7 = 0.571 | 25/44 = 0.568 | 5/5 = 1.000 | (none) |
| mixed_below | (none) | (none) | 3/11 = 0.273 | 5/5 = 1.000 |
| bear_below | (none) | 1/1 = 1.000 | (none) | 4/4 = 1.000 |

**Margin by cross-stack distance d = |s5 - s6| (the disagreement axis):**

| d | n | Hit rate | Wilson 95% |
|---|---|---|---|
| 0 (exact agreement) | 117 | 0.632 | 0.542 to 0.714 |
| 1 | 13 | 0.769 | 0.497 to 0.918 |
| 2 | 5 | 1.000 | 0.566 to 1.000 |
| Any disagreement (d > 0) | 18 | 0.833 | 0.608 to 0.942 |

Disagreement does not predict misses. On this sample it predicts hits, on thin off-diagonal counts. Date-adjusted (outcome minus the leave-one-out mean outcome of the same call date), the distance margin still runs the "wrong" way for the disagreement story: d 0 at -0.031, d 1 at +0.199, d 2 at +0.190.

**Margin by joint posture p = s5 + s6 (the level axis):**

| p | Cells | n | Hit rate |
|---|---|---|---|
| +4 | bull_above|bull_above | 58 | 0.724 |
| +3 | mixed_above|bull_above | 7 | 0.571 |
| +2 | mixed_above|mixed_above | 44 | 0.568 |
| 0 | mixed_above|mixed_below | 5 | 1.000 |
| -2 | mixed_below|mixed_below | 11 | 0.273 |
| -3 | mixed_below|bear_below (+1 reverse) | 6 | 1.000 |
| -4 | bear_below|bear_below | 4 | 1.000 |

The posture margin is not monotone either: the deepest-below cells (p -3, -4) are perfect on n 6 and 4. The entire headline effect is one cell, mixed_below|mixed_below at 0.273, sitting between healthy neighbors. There is no gradient here; there is a single bad cell.

### 3.3 Stability and concentration: the two cells barely coexist

- **Sub-periods** (split at 2026-11-08): AGREE-BULL runs 0.696 in the first half (32/46) and 0.833 in the second (10/12), stable in sign. JOINT-BELOW has 2 rows in the first half (1 hit) and 9 in the second (2/9 = 0.222). The contrast is mostly a between-period comparison, because the cells populate different weeks.
- **Symbols:** the AGREE-BULL cell is MO 17, EW 9, EXPD 6, BKH 6, ELF 6, KDP 5: defensive and consumer names, 44 name calls and 14 Friday bullet calls, concentrated 2026-11-04 to 11-06. The JOINT-BELOW cell is NVDA 6, RKLB 4, ALAB 1: high-beta Focus names, 10 bullet calls and 1 name call, concentrated 2026-11-12 to 11-13. SPY's 31 graded rows never enter either cell (index calls sit in other postures). The two cells hold different universes, different call forms, and different weeks.
- **Date adjustment:** JOINT-BELOW rows score -0.456 against their own dates' other calls, so the cell's weakness is not merely that it sat on bad tape days; within its dates it still underperformed. AGREE-BULL scores +0.050, at its dates' level. This is the one piece of evidence that the JOINT-BELOW cell is more than a calendar artifact, and it rests on 11 rows, 3 symbols, 4 distinct dates.
- **Stance composition (seat-extracted A02, noise floor applies):** AGREE-BULL rows are 33 bullish, 18 bearish, 7 neutral-range stances; JOINT-BELOW rows are 7 bullish, 4 bearish. Stance mix does not separate the cells.

### 3.4 Level effect or selection effect: the answer

Neither clean story survives. It is not a disagreement effect (the distance margin runs the other way). It is not a level effect (the posture margin is non-monotone and the deepest-below cells are perfect). What remains is a **single-cell, composition-confounded observation**: calls made on high-beta names whose price sat below both moving-average stacks while the stacks themselves were in mixed (not bear) order, posed in the 2026-11-12/13 tape, hit 3 of 11, and underperformed their own dates by 45.6 points of hit rate. That is worth exactly one thing: a registered forward candidate with a falsifier, graded on data where the cells coexist by construction. It is not a finding, and no card language may cite it as one until the forward grade lands.

### 3.5 Registered candidate card: JOINT-BELOW STACK CELL

- **Name:** STACK-CELL-JOINT-BELOW-20261115 (A05 x A06 posture-pair cell signal).
- **Exact definition:** for a forecast call on symbol S graded under the book's forecast routine, compute A05 (SMA stack state) and A06 (EMA stack state) mechanically from SIP daily bars at the decision close, using the estate's wave1_bars arithmetic and the four-state vocabulary (bull_above, mixed_above, mixed_below, bear_below). The signal state is the ordered pair. JOINT-BELOW = (mixed_below, mixed_below). Reference cell AGREE-BULL = (bull_above, bull_above). The claim under test: hit rate of JOINT-BELOW calls is materially below the hit rate of all other graded calls, and below AGREE-BULL specifically. This is a forecast-quality marker (a conviction haircut candidate for cards whose underlying sits in the cell), not a trade signal and not a sizing input until graded.
- **Forward accrual route:** Lane 8's GESTALT-AXIS-TAGS wiring (night study step 13, live from Mon 2026-11-16) tags A05 and A06 on every night-study call; the grading session copies the Tags line beside the grade, and the mechanical axes are recomputed from bars at grading so no seat noise enters. Measured retrospective accrual: 12.27 joint rows per night across all sessions, 3.38 per night from the night study alone; JOINT-BELOW share 8.1 percent of joint rows overall (about 1.0 per night all-session, about 0.4 per night night-study-only).
- **Grading gate (the n at which it grades):** the candidate grades when the FORWARD sample reaches all of: at least 150 joint rows, at least 25 JOINT-BELOW rows, at least 20 nights, and each of JOINT-BELOW and AGREE-BULL populated on at least 6 distinct nights (the coexistence condition, written in because the retrospective failure mode was exactly non-coexistence). At measured rates: about 25 nights if the tag schema extends to all five daily sessions (mid-December 2026); about 65 or more nights on night-study wiring alone (February 2027).
- **Falsifier:** at the grading gate, the candidate is dead and the card retired if hit(JOINT-BELOW) is at or above hit(all other forward rows) minus 5 points, or if hit(AGREE-BULL) minus hit(JOINT-BELOW) is under +10 points. If the coexistence condition is still unmet at 40 nights, the verdict is UNGRADABLE-YET on composition grounds, never a pass. Interim reads before the gate are printed with n and Wilson intervals and carry no verdict, per the Lane 8 interim standard.

STATUS: PARTIAL. Proven on the final artifacts, with receipts in `lane9_work/`: Section 1's decomposition is exact and replicates the founding measurement to the basis point (anti +268.80 = universe term +272.13 plus selection term -3.34, t -0.08; the verdict is universe beta, not inversion signal, and at night-cluster level the anti book itself is t 0.95 on 4 nights). Section 2: the overnight effect SURVIVES widening on the daily-bar basis (2,229 nights, t 4.97, both halves significant, ex-gap-flag t 5.24, all 29 names positive); the midday effect is directionally corroborated but does NOT clear session-cluster t on the stored intraday record (t -1.53 all-21, -1.82 Focus-6, 13 sessions) and is sub-period unstable, so it stands as a hypothesis, not a survivor. Section 3: the Lane 8 headline is corrected on its face (a joint-posture cell contrast, not disagreement; distance margin runs the other way; posture margin non-monotone), reduced to one composition-confounded cell, and registered forward as candidate STACK-CELL-JOINT-BELOW-20261115 with its grading gate and falsifier. Named open: SIVE has no bars in any estate cache, so "full Focus 30" is 29 names throughout; intraday segments cannot widen beyond the 1Min cache's 21 symbols and 14 sessions until more sessions accrue in that cache; the earnings archive's coverage (2026-10-13 to 2026-11-05, few Focus names) makes its flag a weak instrument in both widenings, with the mechanical gap flag carrying the sensitivity instead.

EVIDENCE POINTERS: scripts and computed outputs `~/workspace/research_notes/alpha-hunt-chaos-20261115/lane9_work/s1_inversion.py`, `s1_inversion.json`, `s2_segments.py`, `s2_segments.json`, `s3_disagreement.py`, `s3_disagreement.json`; sources `~/workspace/research_notes/decisions-api-leverage-20261114/foundry/c1_anti_midna.py` and `foundry/c1_results.json`, `~/workspace/research_notes/decisions-api-leverage-20261114/conversion/ANTI-MIDNA-CONTROL-LINE-SPEC-2026-11-15.md`, `~/workspace/research_notes/decisions-api-leverage-20261114/keepgoing2/wave3/focus_bars.json`, `~/workspace/muse-desk-v3/cache/bars/<SYM>/1Min.jsonl` (21 symbols), `~/workspace/terminal-lineup/site/earnings-calendar/realised_moves.json`, `~/workspace/research_notes/alpha-hunt-chaos-20261115/retrospective_rows.jsonl` and `gradability_analysis.json`.
