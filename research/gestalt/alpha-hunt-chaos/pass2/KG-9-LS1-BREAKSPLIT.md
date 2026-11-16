# KG-9: LS1 BREAK-SPLIT RERUN (KG-8 variation 2)

## 1. DISPOSITION (leads first)

**LS1 is a post-May-2022 object. It is not an eight-year object, and it is not a down-leg-only object.**

- **Before May 2022 the conditioner does not exist.** Era 1 (225 weekend legs, 2018-01-08 to 2022-04-25): BTC-up legs +10.36bp (t vs 0 = 0.86; t vs the unconditional weekend mean = −0.26), BTC-down legs +2.80bp (t vs 0 = 0.14; t vs unconditional = −0.53, the wrong sign entirely). The era spread is 7.56bp (Welch t 0.32). Neither leg differs from the unconditional weekend mean (+13.47bp) or from its own era's mean (+6.97bp) by anything. The pooled 62.3bp spread is carried entirely by the 237 post-May-2022 legs, whose own spread is 114.46bp (Welch t 4.96).
- **After May 2022 both legs are real, against every benchmark.** Pooled May 2022 onward (237 legs): up leg +73.26bp (n=126, t vs 0 = 5.05, t vs global unconditional = 4.12, t vs the post-2022 era's own unconditional of +19.65bp = 3.70); down leg −41.20bp (n=111, t vs 0 = −2.29, t vs global unconditional = −3.04, t vs era unconditional = −3.39). Mourey, Shahrour and Soiman's (Finance Research Letters 86, 2025) predicted asymmetry, a down leg with a null up leg, does **not** hold on this basket and this leg: the up leg is the larger and more significant of the two.
- **The object strengthens again at the second break.** Era 3 (Jan 2024 onward, 150 legs) is the decisive mass: up leg +98.26bp (n=84, t vs 0 = 5.02, t vs its own era's unconditional +32.97bp = 3.34, median +80.25bp, win 0.738, so the up leg is broad-based, not tail-carried); down leg −50.13bp (n=66, t vs its own era's unconditional = −2.92). Era 2 (May 2022 to Dec 2023, 87 legs) is the transitional shape closest to Mourey's: the down leg leads (−28.12bp, t vs the global unconditional = −2.72) while the up leg is positive but insignificant (+23.25bp, t vs 0 = 1.38) at n=42.
- **One character difference between the legs, printed so it cannot be smoothed over:** in Era 3 the down leg's mean (−50.13bp) is tail-carried. Its median is +8.51bp and its win rate is 0.545; the typical BTC-down weekend in the ETF era was mildly positive overnight, and the negative mean comes from large down weekends. In Era 2 the down leg is broad-based (median −28.24bp, win 0.356). Any forward grade of the down leg that reads only its mean will misread which of these two objects it is accruing.

**Re-registration:** LS1's registered form changes from "weekend crypto conditioner, 2018-2026" to "weekend crypto conditioner, post-May-2022 regime, decisive mass post-Jan-2024; up leg dominant and broad-based in the current era; down leg real against the unconditional mean in both post-2022 eras, broad-based in 2022-2023 and tail-carried in 2024 onward." The 225 pre-May-2022 legs are retired as supporting evidence. The forward check is re-registered accordingly in section 5.

**Agreement and disagreement with the literature, one line each.** Dating: full agreement, twice over (nothing before the May 2022 LUNA break; strongest after the late-2023/2024 break the arXiv weekend-volatility study dates). Asymmetry: disagreement. Mourey's null up leg is an index-level result; on the 29-name Focus basket's Friday-close-to-Monday-open leg the up leg is the strongest single cell in this rerun. That disagreement is now a measured property of the object, not an open question.

## 2. REPRODUCTION PROOF

The rerun operates on the stacking lane's own working file, `pass2/stack_work/nights.json` (the rows `run_stacks.py` built from `focus_bars.json` and the Coinbase BTC daily closes; BTC weekend move = Friday close to Sunday close; up = move > 0, down = move <= 0, per run_stacks.py tests N3/N4). The basket and leg definitions were not rebuilt. Recomputed pooled values reproduce LEAD-STACKING.md's LS1 to the printed digit:

| Object | Published | This rerun |
|---|---|---|
| Weekend legs, unconditional | +13.47bp, t 1.64, n=462 | +13.47bp, t 1.64, n=462 |
| BTC-up legs | +42.06bp, t 4.36, n=250, win 0.632 | +42.06bp, t 4.36, n=250, win 0.632 |
| BTC-down legs | −20.24bp, t −1.50, n=212, win 0.509 | −20.24bp, t −1.50, n=212, win 0.509 |
| Carry-5 up / down | +47.37 (t 4.03) / −12.74 | +47.37 (t 4.03) / −12.74 |
| Rest-of-basket up / down | +41.03 (t 4.31) / −21.33 | +41.03 (t 4.31) / −21.33 |
| Spread | 62.30bp | 62.30bp (Welch t 3.76) |

## 3. (a) EACH LEG AGAINST THE UNCONDITIONAL WEEKEND MEAN, POOLED

The unconditional weekend-leg mean is +13.47bp. Displacements are leg mean minus +13.47bp; t vs unconditional is a one-sample t of the leg against that mean.

| Leg | n | Mean | Displacement | t vs 0 | t vs unconditional (p) |
|---|---|---|---|---|---|
| BTC-up | 250 | +42.06bp | +28.59bp | 4.36 | 2.97 (0.0033) |
| BTC-down | 212 | −20.24bp | −33.71bp | −1.50 | −2.50 (0.0130) |

Pooled, both legs sit significantly off the unconditional mean, in opposite directions. The down leg's pooled significance comes from the unconditional comparison, not from zero (t vs 0 = −1.50): a BTC-down weekend does not make the basket fall overnight on the pooled span, it removes the weekend premium and then some. That distinction is exactly why KG-8 specified this test.

## 4. (b) THE THREE ERAS, LEGS SEPARATE THROUGHOUT

Era boundaries are the literature's dates, fixed before the rerun: E1 before 2022-05-01, E2 2022-05-01 to 2023-12-31, E3 from 2024-01-01, dated by the Monday session of each leg. Era leg counts sum to 462 (225 + 87 + 150).

### E1: pre-May-2022 (2018-01-08 to 2022-04-25), era unconditional weekend mean +6.97bp

| Leg | n | Mean | Median | Win | t vs 0 | t vs global uncond | t vs era uncond |
|---|---|---|---|---|---|---|---|
| BTC-up | 124 | +10.36bp | +21.37 | 0.573 | 0.86 | −0.26 | 0.28 |
| BTC-down | 101 | +2.80bp | +14.14 | 0.554 | 0.14 | −0.53 | −0.21 |

Spread 7.56bp (Welch t 0.32, p 0.747). Subsets agree: carry-5 up +12.63 / down +8.96; rest up +9.97 / down +1.62, no t anywhere above 0.86. **No conditioner.**

### E2: May 2022 to Dec 2023 (2022-05-02 to 2023-12-26), era unconditional weekend mean −3.32bp

| Leg | n | Mean | Median | Win | t vs 0 | t vs global uncond | t vs era uncond |
|---|---|---|---|---|---|---|---|
| BTC-up | 42 | +23.25bp | +16.13 | 0.595 | 1.38 | 0.58 | 1.58 |
| BTC-down | 45 | −28.12bp | −28.24 | 0.356 | −1.84 | −2.72 (p 0.0092) | −1.62 |

Spread 51.37bp (Welch t 2.26, p 0.027). Note the era itself: weekend legs averaged negative in E2, so the down leg's cleanest statement is against the global unconditional (−41.59bp displacement); against its own depressed era mean it is marginal (t −1.62). Subsets: carry-5 down −26.60 (t vs uncond −2.05), rest down −28.31 (t vs uncond −2.78); up legs positive on both subsets, neither significant. **The down leg arrives first; the up leg is present in sign only.**

### E3: Jan 2024 onward (2024-01-02 to 2026-11-09), era unconditional weekend mean +32.97bp

| Leg | n | Mean | Median | Win | t vs 0 | t vs global uncond | t vs era uncond |
|---|---|---|---|---|---|---|---|
| BTC-up | 84 | +98.26bp | +80.25 | 0.738 | 5.02 | 4.34 | 3.34 (p 0.0013) |
| BTC-down | 66 | −50.13bp | +8.51 | 0.545 | −1.76 | −2.24 (p 0.0286) | −2.92 (p 0.0047) |

Spread 148.39bp (Welch t 4.30). The up leg beats even its own era's strong weekend premium by +65.29bp, on both subsets (carry-5 +107.10, t vs uncond 4.26; rest +96.26, t vs uncond 4.25). The down leg separates from the era mean by −83.10bp but, as section 1 flags, its median is positive: the separation is in the left tail. **Both legs live; the up leg is the era's dominant object.**

## 5. FALSIFIER TRACKER DESIGN NOTE: WHAT CHANGES

The forward check as registered in LEAD-STACKING.md (falsifier tracker logs per-night auction prints from Mon 2026-11-16; add the BTC weekend state to the same ledger row; the conditioned split grades at 20 accrued weekend legs) changes in four ways under this rerun:

1. **The hypothesis under test is restated.** The tracker is no longer accruing evidence for an eight-year conditioner. It accrues in the post-2024 regime only, which is where the object's decisive mass already sits, so the accrual mechanics and the 20-weekend-leg grading point stand unchanged; what changes is the registered claim the grade reads against: post-May-2022 conditioner, up leg dominant. A forward failure now falsifies the current-regime object, and no pre-2022 history may be cited in its defence.
2. **The legs grade separately against the running unconditional weekend mean, never only as a spread.** Two pre-registered partial-failure states are named in advance: if the accrued up leg fails against the unconditional mean while the down leg holds, LS1 collapses to Mourey's down-leg-only shape and any long-weekend expression built on the up leg dies with it; if the down leg fails while the up leg holds, LS1 survives as an up-leg conditioner only. A spread-only grade could pass while one leg is already dead, and is refused.
3. **The down leg carries a median and win-rate line beside its mean.** Its Era 3 mean is tail-carried (mean −50.13bp, median +8.51bp). If the forward down leg prints a negative mean with a positive median, it is accruing the tail object; if both go negative together, it has become the broad-based Era 2 object. The tracker row needs the BTC weekend move's magnitude as well as its sign, so the tail question (does the down leg scale with the size of the weekend fall?) can be graded at the same 20-leg point; sign alone cannot answer it.
4. **No change to the trial accounting.** This rerun is KG-8's one registered variation on LS1, split at dates the literature fixed in advance; it is not a new search and adds no trials to the NIGHT family count of 21. Its result narrows LS1's claim rather than multiplying it.

## 6. METHOD AND FILES

- Script: `pass2/kg9_breaksplit.py`; full numeric output: `pass2/kg9_breaksplit.json` (every figure in this file is read from it).
- Input: `pass2/stack_work/nights.json` only. No basket rebuild, no new BTC series, no new legs.
- Tests: one-sample t of each leg against 0, against the global unconditional weekend mean (+13.47bp), and against its own era's unconditional weekend mean; Welch t for spreads, printed for completeness and never reported alone.
- Caveat carried from LS1 itself: legs are daily-bar close-to-open (the auction-print basis is what the forward tracker measures from Mon 2026-11-16), and weekend legs within an era share calendar clustering the plain t does not model; Era 2's n (42 up / 45 down) is the smallest base any claim here rests on, and its up leg is reported as sign-only for that reason.

STATUS: GREEN. The rerun is proven on the final artifact: LS1 reproduced to the printed digit from the stacking lane's own rows, both legs tested against the unconditional mean pooled and in all three eras (462 of 462 legs accounted for, era counts 225 + 87 + 150), the disposition printed (post-May-2022 object, both legs, up leg dominant post-2024; not eight-year, not down-leg-only), and the falsifier tracker design note states the four changes the re-registration makes.
