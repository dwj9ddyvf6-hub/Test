# KG-10: The Closing-Imbalance Conditioner (KG-8 variation 1)

Test: the Focus overnight premium conditioned on the day's closing order imbalance, crossed two-by-two with LS2's prior intraday sign. Source framework: Boyarchenko, Larsen and Whelan's inventory pricing (expected overnight return = closing order imbalance x variance / liquidity-provider risk capacity), whose signed-volume sorts predict **negative closing imbalance (a sell-pressure close) is followed by positive overnight returns**. Data: the estate's 1Min cache, RTH basis, the only span it covers for Focus names.

## POTENTIAL EDGE FOUND

**No cell separates.** On the full span the 1Min cache honestly covers for Focus names (6 of 30 names x 12 nights, named below), no cell in either cross reaches |t| 1.7 with the night as the clustering unit, and the unconditional overnight premium over this window is itself negative (-39.96bp, t -0.38): this window is the premium's known cold stretch (Lane 9 measured the last five weeks into 2026-11-13 at -56bp ex-earnings), so the conditioner is being read on a window where the phenomenon it would condition is switched off. That is the headline and it is not buried.

**The lead that survives, stated at its true strength:** inside the down-day row only, the inventory-theory ordering appears under both proxies and at both levels of aggregation, and nowhere else.

- Signed-volume cross, down-day row: sell-pressure close **+60.73bp** (n=15 name-nights, 9 nights, t 0.334) against buy-pressure close **+13.92bp** (n=28, 10 nights, t -0.259). Spread +46.81bp in the theory's direction.
- Close-location cross, down-day row: close in the bottom half of the final hour's range **+175.66bp** (n=24, 9 nights, t 0.216) against close in the top half **-153.43bp** (n=19, 7 nights, t -1.643, the largest |t| in either cross). Spread +329.09bp in the theory's direction.
- Basket level: the down-day x sell-close cell is the **only positive basket cell, +409.48bp** (2 nights, t 1.487). Two nights is an anecdote, printed as one.
- Weekday-only sensitivity keeps the sign: down-day x sell-close +110.49bp (n=12, 7 nights, t 0.518).
- The up-day row runs the other way under both proxies (signed-volume spread -111.87bp; close-location spread -158.96bp): if the conditioner is real, it is a down-day phenomenon, the absorbed-inventory case, not a symmetric flow effect.

**Cheapest forward check (the arming step):** the overnight falsifier tracker starts Monday 2026-11-16 and pulls every session's bars nightly for 60 sessions on auction prints. Appending each name-night's final-30-minute signed volume share (and the day's intraday sign) to the tracker rows costs one field per name-night, needs no new machinery, and grades this exact cross at the falsifier's own 60-session mark on the auction-print basis instead of the bar basis used here. The Decisions seat's strongest action read in this lane lands on exactly that check (below).

## THE FOUR CELLS

Primary cross: final-30-minute tick-rule signed volume share sign (buy-pressure close SVS30 > 0; sell-pressure close SVS30 <= 0) x full-day intraday sign (close vs session open). Overnight return: session close to next complete session's open, 1Min-bar basis. t is night-clustered: per-night cell means, t over the nights populating the cell.

| Cell | n (name-nights) | Nights | Mean overnight | t (clustered) | Weekend name-nights |
|---|---|---|---|---|---|
| Up day x buy-pressure close | 12 | 9 | -78.49bp | -0.159 | 2 |
| Up day x sell-pressure close | 17 | 7 | -190.36bp | -1.368 | 1 |
| Down day x buy-pressure close | 28 | 10 | +13.92bp | -0.259 | 6 |
| Down day x sell-pressure close | 15 | 9 | **+60.73bp** | 0.334 | 3 |

Single-conditioner reads on the same span, for orientation: LS2's split alone inverts against its full-span read (up-day name-nights -144.07bp, n=29, 9 nights, t -1.232; down-day +30.25bp, n=43, 11 nights, t -0.125; full-span LS2 was +26.93bp after up days vs +5.82bp after down days over 2,229 nights). Imbalance alone: buy-pressure closes -13.80bp (n=40, 12 nights, t 0.224); sell-pressure closes -72.66bp (n=32, 11 nights, t -0.380). Neither conditioner carries anything alone on this window; the down-row ordering exists only in the cross.

Companion cross (close-location in the final hour's range, split at 0.5):

| Cell | n | Nights | Mean overnight | t (clustered) |
|---|---|---|---|---|
| Up day x close top half | 14 | 7 | -61.85bp | -0.355 |
| Up day x close bottom half | 15 | 6 | -220.81bp | -0.844 |
| Down day x close top half | 19 | 7 | -153.43bp | -1.643 |
| Down day x close bottom half | 24 | 9 | **+175.66bp** | 0.216 |

Basket level (per-night equal-weight means of the 6 names; 12 nights): up-day x buy-close cell is **empty**, because on all 5 basket-up nights the basket's mean SVS30 was negative; up-day x sell-close 5 nights, -115.72bp, t -0.763; down-day x buy-close 5 nights, -143.98bp, t -1.039; down-day x sell-close 2 nights, **+409.48bp**, t 1.487.

## SEAT LENS (Decisions API, gpt-6-luna; lens only, seats set no grades)

5 objects, 45 questions, 45 answers, $0.002615, no 429 hit. Seven-lens panel means are p(claim true); ADV is the adversarial p(entirely artifact).

| Object | Lens mean | Widest disagreement | ADV | Action read |
|---|---|---|---|---|
| SVS30 cross: down-row ordering is a real inventory effect | 0.214 | DATA 0.18 vs SWING/PREDMKT 0.24 | 0.79 | 20-40 band at 0.84 (forward log line only) |
| CL60 cross: two proxies agreeing is a shared flow signal | 0.294 | DATA 0.24 vs PREDMKT 0.35 | 0.79 | 20-40 band at 0.77 |
| Basket level: inventory cell + empty up x buy cell carry forward information | 0.250 | DATA 0.20 vs SWING 0.30 | 0.84 | 20-40 band at 0.83 |
| Cold-window null: no cell here has forward content; log and read at 60 sessions | 0.681 | GAME/PREDMKT 0.65 vs SWING 0.71 | 0.77 | 20-40 band at 0.90 |
| Forward check: grade the cross on the falsifier's 60 sessions | 0.469 | PREDMKT/DATA 0.38 vs HFM/QUANT 0.53 | 0.58 | **40-60 band at 0.78 (worth a registered forward check)** |

The seat agrees with the statistics: it prices the cell patterns as probably artifact (adversarials 0.79 to 0.84), prices the cold-window null as the most likely single read (0.681), and puts its only material action probability on the cheap forward check. No tier in this file was set or moved by a seat.

## METHOD AND THE PROXY'S STATED LIMITS

**The proxy, exactly.** The cache holds OHLCV minute aggregates only: no trade direction, no bid/ask, no closing-auction flag. A true signed order imbalance cannot be constructed from it. The primary proxy is the strongest signed proxy the cache supports, a **tick-rule signed volume share over the final 30 RTH minutes** (bar-start stamps 15:30 to 15:59 ET): SVS30 = sum over those 30 bars of sign(c_i - c_{i-1}) x v_i, divided by the sum of v_i, where c_{i-1} is the previous RTH bar's close (the 15:29 close for the 15:30 bar) and zero-move bars contribute zero signed volume. Range [-1, +1]; the cross splits at 0 (40 buy-pressure vs 32 sell-pressure name-nights). The companion proxy is **close-location within the final hour's range**: (session close - min low over 15:00-15:59) / (max high - min low over the same bars), split at 0.5. The tick rule misclassifies direction on bars whose net move disagrees with their internal flow, and neither proxy isolates the closing auction print itself; both measure final-minutes pressure, not auction imbalance. The BLW variable is end-of-day relative signed volume from trade-level data; this is an inference of it, one layer removed, and every read above carries that removal.

**Span and coverage, printed.** 1Min files exist for 21 symbols in the whole cache; the Focus-30 intersection is exactly 6 names: NVDA, AVGO, AMD, AMAT, MU, PLTR. Each carries exactly 14 complete RTH sessions (390 of 390 bars): 2026-10-21, 22, 23, 29, 30 and 2026-11-02 through 06, 09 through 12. The cache has a three-session hole (2026-10-26, 27, 28 absent for every name): the 2026-10-23 to 2026-10-29 leg spans it, is a six-day hold rather than an overnight leg, and is **excluded** from every read (6 name-legs). Primary span: 72 name-nights over 12 nights, 2026-10-21 to 2026-11-12, of which 12 name-nights (2 nights) are Friday-to-Monday weekend legs, flagged per cell. The other 24 Focus names have no 1Min file at all (1Day only or nothing), so nothing here speaks for the full basket; the carry names SNDK, CRWV and RKLB are among the unmeasured.

**Price basis.** Overnight return uses the last RTH 1Min bar's close and the next session's first RTH bar open. This is the bar basis Lane 9 flagged (the daily bar's open is not the opening auction print; Wave 5 measured per-name biases up to +28.8bp on CRWV, unmeasured for these 6 names at minute resolution). The forward check above re-grades on the tracker's auction prints, which is the basis the falsifier owns.

**Clustering.** Twelve nights is the binding constraint everywhere: night means inside cells swing from -758.59bp to +765.41bp, so cell means are carried by a handful of nights and the clustered t values printed are the honest ones. Name-night t values (unclustered) would be larger and are not printed as evidence anywhere in this file.

**What the method did differently (autopsy line, per the standing rule).** The default would have crossed the imbalance proxy against the full-day sign on the pooled name-nights and read the pooled means. Three deviations produced the honest read instead: the conditioner was built at the mechanism's own timescale (final 30 minutes, not the day), the hole-spanning legs were refused rather than silently counted as overnights, and every t was computed on night means so the 12-night reality could not be laundered into 72 observations. Reusable rule: a conditioner is tested at its mechanism's timescale, on legs that are actually the phenomenon, with the independent unit as the denominator.

Working files: kg10_census.py (session table, kg10_sessions.json), kg10_analysis.py (legs and cells, kg10_legs.json, kg10_cells.json), kg10_seats.py (kg10_seat_runs.json), all in this directory.

STATUS: PARTIAL. The test is complete and proven on the final artifacts (72 name-nights over 12 nights recomputed from the cache, both crosses and the basket read printed with night-clustered t, seat lens 45 of 45); the PARTIAL names the remainders: no cell separates on the only span the cache covers, the span is 6 of 30 Focus names inside the premium's cold window, and the conditioner's deciding read is the named forward check on the falsifier tracker's 60 sessions from Mon 2026-11-16, not yet run.
