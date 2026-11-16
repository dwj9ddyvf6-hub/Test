# KG-13: DECAY-WEIGHTED EXITS (KG-8 VARIATION 3, THE LAST UNRUN VARIATION)

Scope: fit each family's KG-4 phase curve to an exponential decay, extract a per-family half-life, and replay Garleanu-Pedersen partial-adjustment scale-outs on KG-7's exact population and machinery (the 57 Unblock-2 REPLAY-SCORED and REPLAY-INDICATIVE sleeves, 37 distinct entry streams, Unblock-2's Book.path on stored daily closes, close-based, 6bp exit cost inside the path, paired per-trade deltas against each sleeve's base). Arms compared per sleeve and pooled per family: EXIT_BASE, DROP_STOP, WIDEN_STOP_X2, EXTEND_HORIZON_X2, NIGHT1_ONLY, DECAY_SCALEOUT. Evidence class REPLAY on every row. Register: KG-13-REGISTER.jsonl, 376 rows (5 half-life fits, 342 sleeve-variation rows, 17 family arm rows, 12 decay-vs-crude rows), counted back from the final file.

## POTENTIAL EDGE FOUND

The decay schedule itself produces no new armable edge at family level. Its pooled deltas against base are a small positive null in the two arrival families (Aster +52.8bp, t=1.47, n=427; Fires and singles +14.6bp, t=0.26, n=83), a reproduction of the crude night-1 failure in Lazarus/Q07/MN (-177.0bp, t=-2.19, n=1231), and an exact identity with the night-1 arm in Tensor (+2688.9bp on n=5, untestable) and Spec-built (-111.6bp on n=1). What does carry forward, printed at its true strength:

1. **The ADA breakout stream under a gradual exit (Aster, one stream in two mirror sleeves).** aster_breakout_ada_fullcash and aster_breakout_ada_vol1pct (identical stream, DEFAULT_HOLD10 base at -497.3bp) grade +491.0bp paired delta under the decay schedule (to -6.3bp, t=4.62, n=32), against +521.2bp under the crude NIGHT1_ONLY arm (KG-7). The schedule captures 94% of the night-1 gain while exiting over a mean of 7.0 legs with only 25.4% of the position out on night 1, so it keeps three quarters of the position exposed to the tail paths the crude exit abandons. Cheapest forward check: on the forward dispatcher stream, grade this stream's next 20 fires under base, night-1, and the Aster decay schedule side by side; the decay form is worth arming only if it keeps at least the night-1 arm's mean on forward fires, since on replay it is 30.2bp behind it.
2. **aster_etf_qqq_qld_monthly (Aster).** +357.5bp paired delta under the decay schedule (base -450.3bp to -92.8bp, t=2.46, n=15). Same forward check as the ADA stream, at its own first 20 forward fires.
3. **The negative result, which is the lane's main yield.** In both arrival families the decay schedule is dominated by the crudest arm in the set, EXTEND_HORIZON_X2 (Aster +168.0bp, t=3.64; Fires +167.2bp, t=2.22; decay-minus-extend -115.2bp at t=-2.08 in Aster, -152.5bp at t=-1.51 in Fires). Where the phase curves contain any exit-design information at all on this record, it reads as "hold longer", a result KG-7 already produced without any curve fitting. Any future exit-design work on these families should start from horizon extension and the Lazarus stop findings, not from phase-shape weighting in any form.

## THE ENGAGEMENT: WHY A SCALE-OUT COULD DIFFER, STATED BEFORE THE RESULT, THEN GRADED

KG-7's printed verdict was that KG-4's phase means did not transfer to exit design: its night-1-only prediction confirmed in 1 of 4 classified families, and that one (Tensor) on 5 paired trades that cannot carry a confirmation; Lazarus, the deepest family, missed in the opposite direction at -176.6bp (t=-2.18, n=1231). KG-7's own interpretation: the phases are mark-to-market marks on a different population (the live record), a base exit already traverses the earning phase, and an exit rule's marginal value lives in tail paths (target partials, recoveries, post-horizon decay) that phase means do not measure.

The claim this lane was required to state up front, and did state in its compute script before any decay path was run: a remaining-alpha scale-out is not a threshold rule, so it could succeed where KG-7's crude transfers failed, for three specific reasons. (a) It never bets the whole position on one phase boundary: it holds a declining fraction through the entire path, so the tail paths KG-7 named as load-bearing keep a working stub instead of being exited in full. (b) It monetizes the phase curve continuously, in proportion to fitted remaining alpha each night, rather than converting the curve into a single exit night. (c) It can express a shape no KG-7 arm could: for an arrival family (Fires, whose raw first night is -429.8bp and whose earnings land on nights 2-3) it holds the full position through the negative first night and exits into the plateau, where NIGHT1_ONLY is its exact opposite. The graded prediction that follows: if phase shape carries any exit-design information, the scale-out should beat base in Aster and Fires (where the crude transfer missed by sign on nulls) and should not reproduce Lazarus's crude failure at full strength, because it never fully exits on the phase boundary.

**Verdict: the claim is NOT CONFIRMED as a differentiator, and KG-7's verdict stands, strengthened in a specific way.** Family by family:

- **Lazarus/Q07/MN: the failure is inherited, not avoided.** Pooled decay delta -177.0bp (t=-2.19, n=1231, sleeve signs 4/27/0) against the night-1 arm's -176.6bp (t=-2.18); decay-minus-night1 on the same 1231 trades is -0.4bp (t=-0.68). The mechanism in (a) exists in the design but cannot engage: the fitted Lazarus curve's positive alpha is one night deep (fitted rates +399.9bp on night 1, +18.7bp on night 2, negative thereafter), so remaining-alpha tracking exits 95.5% of every position at the night-1 close and the stub that was supposed to keep the tail paths working carries 4.5% weight (mean legs 2.00, weighted exit night 1.04). The four long-horizon registered sleeves that carried KG-7's miss carry this one at the same size: 1w -1672.9bp (n=28, KG-7 night-1: -1666.5), 1wa -1243.0 (n=34; -1237.2), s_1wlab -559.4 (n=80; -558.9), 1d -305.0 (n=56; -312.2). A schedule that is 95.5% the crude arm reproduces the crude arm's result to within half a basis point pooled. The load-bearing Lazarus lever remains the one KG-7 found and this run reproduces: on the 277 stop-carrying paired trades, DROP_STOP prints +444.1bp (t=2.27) and WIDEN_STOP_X2 +466.6bp (t=2.47) against base, while the decay arm, which keeps the base stop, sits -1198.2bp and -1220.7bp behind them respectively (t=-4.16 and -4.31).
- **Tensor and Spec-built: the schedule degenerates to the crude arm exactly.** The Tensor fit (H=0.240 nights) and the fleet-equity fit used for Spec-built (H=0.805) both put all fitted positive alpha on night 1, so the scale-out exits 100% at the night-1 close on every trade (mean legs 1.00, night-1 exit share 1.000). Decay deltas are identical to the night-1 arm's to the tenth of a basis point (+2688.9bp, n=5; -111.6bp, n=1), and the decay delta equals the night-1 delta exactly on 6 of the 57 sleeves (the 5 Tensor sleeves and coffin_rebuilt). No new arm exists in these families; KG-7's readings are inherited unchanged, including Tensor's untestability at n=5.
- **Aster: the one genuinely new shape, direction as claimed, magnitude inside noise, and dominated anyway.** The Aster schedule is a real scale-out (mean 6.89 legs, 25.4% out on night 1, weighted exit night 2.69) and it prints +52.8bp (t=1.47, n=427, signs 13/4/0) against the night-1 arm's +44.3bp (t=1.04); decay-minus-night1 on common trades is +8.5bp (t=0.57). That is the claimed direction at a size the record cannot distinguish from zero, and EXTEND_HORIZON_X2 beats both at +168.0bp (t=3.64), decay-minus-extend -115.2bp (t=-2.08).
- **Fires and singles: the wait shape works as designed and buys nothing measurable.** The schedule holds through the negative first night (night-1 exit share 20.6% on the sleeves' own horizons, and that share is the fitted curve's plateau share, not an exit into the -429.8bp night; mean 10.87 legs, weighted exit night 4.75) and prints +14.6bp (t=0.26, n=83) against night-1's +13.2bp (t=0.17); decay-minus-night1 is +1.4bp (t=0.05). EXTEND_HORIZON_X2 prints +167.2bp (t=2.22) on the same trades.

Net reading, labeled as interpretation: phase means do not transfer to exit design in threshold form (KG-7) or in continuous remaining-alpha form (this lane). The two forms agree family by family to within noise everywhere the comparison is powered, which closes the "the crude form was the problem" hypothesis that KG-8's variation was designed to test. KG-8's literature prediction for this variation (decay-weighted exits beat base and the crude variants, gain concentrated in Lazarus, near zero in Fires) fails on its headline: Lazarus is where the decay arm does worst, tied with the night-1 arm as the family's worst arm; the Fires near-zero prediction holds (+14.6bp) but is vacuous, since every arm except EXTEND is near zero there.

## THE HALF-LIFE TABLE

Fit procedure, fixed before any replay was run. KG-4's phase cells are per-phase increments of excess return against QQQ (N1 = exc(1); N2-3 = exc(3)-exc(1); N4-5 = exc(5)-exc(3); N4+ = exc(10)-exc(3), per kg4_compute.py), converted to per-night rates at bucket midpoints: (1, N1), (2.5, (N2-3)/2), (4.5, (N4-5)/2), (7, (N4+)/7). Model r(t) = r_inf + A * 2^(-(t-1)/H), fit by grid search over H with linear least squares for (r_inf, A). Degeneracy rule, also fixed in advance: if R2 < 0.5 or H lands on either grid boundary, refit on the post-peak segment (points from the argmax bucket onward, decay clock starting at that bucket's midpoint) and extend the fitted curve flat at its peak value before the peak. The fleet curve is KG-4's FLEET-EQUITY split (the FLEET-ALL cells are option-contract contaminated, per KG-4's own basis warning). Spec-built sleeves take the fleet-equity fit, labeled FLEET_PROXY, because KG-7 left Spec-built UNCLASSIFIED and the fleet curve is the only all-family curve KG-4 published on the equity basis.

| Fit family | Segment | Half-life H (nights) | r_inf (bp/night) | A (bp) | R2 | RMSE (bp) | g = 1 - 2^(-1/H) |
|---|---|---|---|---|---|---|---|
| Fleet (equity) | FULL | 0.805 | -127.9 | 172.0 | 0.9902 | 6.8 | 0.5774 |
| Tensor | FULL | 0.240 | -119.9 | 148.9 | 0.9999 | 0.7 | 0.9446 |
| Lazarus/Q07/MN | FULL | 0.906 | -312.9 | 712.8 | 0.9194 | 83.0 | 0.5348 |
| Aster | POST_PEAK | 3.528 | -170.6 | 420.8 | 1.0000 (0 dof) | 0.0 | 0.1784 |
| Fires and singles | POST_PEAK | 0.564 | 144.4 | 544.7 | 1.0000 (0 dof) | 0.1 | 0.7071 |

Fitted per-night rates, nights 1 to 10 (bp): Fleet: 44.1, -55.2, -97.2, -114.9, -122.4, -125.6, -126.9, -127.5, -127.7, -127.8. Tensor: 29.0, -111.6, -119.4, then -119.9 flat. Lazarus: 399.9, 18.7, -158.6, -241.1, -279.5, -297.4, -305.7, -309.5, -311.3, -312.2. Aster: 250.3, 250.3 (flat extension before the peak bucket), 210.9, 142.9, 87.0, 41.0, 3.3, -27.7, -53.2, -74.1. Fires: 689.1, 689.1 (flat extension), 439.2, 230.7, 169.7, 151.8, 146.6, 145.0, 144.6, 144.5.

Three fit disclosures. First, the two post-peak fits have 3 points and 3 effective parameters (H, A, r_inf), so R2 = 1.0000 is mechanical with zero degrees of freedom; the half-lives are exact interpolations of three bucket rates, not measurements with residual support. Second, the full fits that triggered the degeneracy rule: Aster's full fit landed on the grid's upper boundary (H=137.831, R2=0.2418) because its rate curve is humped (67.8, 250.3, 113.5, 3.3) and no monotone decay fits it; Fires' full fit landed on the grid's lower boundary (H=0.050, R2=0.7113) because its curve is a level shift (a -429.8bp first night, then a positive plateau) and the least-squares optimum is an instantaneous step. Third, KG-8's verbal half-life guesses grade as follows: "Lazarus, fitted half-life near one night" is confirmed (0.906). "Fires slow" is confirmed in schedule effect but not in the deviation half-life: the fitted deviation from the plateau decays fast (H=0.564), yet the plateau itself is +144.4bp per night, so remaining alpha stays high for many nights and the resulting schedule is the slowest in the run (weighted exit night 4.75, against Lazarus's 1.04). The half-life of the deviation and the duration of the remaining-alpha mass are different quantities, and only the second one drives a remaining-alpha exit.

In-pass correction, disclosed: the first compute pass implemented the degeneracy rule's boundary check one-sidedly (upper edge only), so the Fires full fit at the grid floor stood and produced a Fires decay delta of +19.9bp (t=0.48, n=83) under a step-function schedule (no night-1 exit, then a linear bleed). The stated rule is two-sided; the code was corrected to match it, every number in this deliverable and in the register comes from the corrected run, and the superseded figure is named here so nothing is hidden. The correction does not change any verdict: the two Fires schedules print +19.9bp and +14.6bp against the night-1 arm's +13.2bp, the same small positive null.

## THE SCALE-OUT RULE AS RUN

DECAY_SCALEOUT keeps the sleeve's base stop, target, and horizon unchanged. RA+(k) = sum over j=k..h of max(r_fit(j), 0), over the sleeve's base horizon h, r_fit the family's fitted per-night rate at integer nights. At each night (Book.path indexing, last = min(i+h, len-1)): stop and target are checked first on the cumulative close return exactly as Book.path checks them, and a trigger exits all remaining at the trigger level. Otherwise the position is brought down to the desired remaining share RA+(k+1)/RA+(1) of the original, the leg contributing frac * (r_k - EXIT_COST), so every exited unit pays the same 6bp cost convention as every other arm. At the last available night all remaining exits. Realized schedule shapes, means over each family's graded sleeves: Aster 6.89 legs, night-1 exit share 0.254, weighted exit night 2.69; Fires 10.87 legs, 0.206, 4.75; Lazarus 2.00 legs, 0.955, 1.04; Tensor 1.00 leg, 1.000, 1.00; Spec-built 1.00 leg, 1.000, 1.00.

Machinery verification: the base and crude arms were recomputed from scratch in this lane's script, and all 197 GRADED KG-7 sleeve-variation rows reproduce KG-7-REGISTER.jsonl exactly (status, base mean, paired delta, n_paired), as do all 88 NOT_APPLICABLE stop rows (identical sleeves, arms, and reason strings). The decay arm is defined on every base, so it grades on all 57 sleeves with no NOT_APPLICABLE rows of its own.

## PER-FAMILY PAIRED DELTAS, EVERY ARM

Pooled paired trades per family (KG-7's pooling convention: trades pooled across sleeves, not sleeve means averaged). Base means differ across arms inside a family because each arm pairs on the trades priceable under both it and base (the stop arms pair only on the 277 stop-carrying Lazarus trades). DROP_STOP and WIDEN_STOP_X2 exist only for Lazarus because the union's other families carry no stops on their bases (the 88 NOT_APPLICABLE rows, identical to KG-7).

| Family | Arm | Base mean | Arm mean | Paired delta | t | n | Sleeve signs (+/-/0) |
|---|---|---|---|---|---|---|---|
| Aster | EXTEND_HORIZON_X2 | -74.5 | 93.4 | 168.0 | 3.64 | 427 | 12/5/0 |
| Aster | NIGHT1_ONLY | -74.5 | -30.2 | 44.3 | 1.04 | 427 | 12/5/0 |
| Aster | DECAY_SCALEOUT | -74.5 | -21.7 | 52.8 | 1.47 | 427 | 13/4/0 |
| Fires and singles | EXTEND_HORIZON_X2 | 20.3 | 187.4 | 167.2 | 2.22 | 83 | 2/0/1 |
| Fires and singles | NIGHT1_ONLY | 20.3 | 33.5 | 13.2 | 0.17 | 83 | 2/1/0 |
| Fires and singles | DECAY_SCALEOUT | 20.3 | 34.9 | 14.6 | 0.26 | 83 | 2/1/0 |
| Lazarus/Q07/MN | DROP_STOP | 802.7 | 1246.8 | 444.1 | 2.27 | 277 | 6/2/5 |
| Lazarus/Q07/MN | WIDEN_STOP_X2 | 802.7 | 1269.3 | 466.6 | 2.47 | 277 | 6/2/5 |
| Lazarus/Q07/MN | EXTEND_HORIZON_X2 | 201.4 | 96.6 | -104.8 | -2.04 | 1231 | 10/20/1 |
| Lazarus/Q07/MN | NIGHT1_ONLY | 201.4 | 24.8 | -176.6 | -2.18 | 1231 | 4/27/0 |
| Lazarus/Q07/MN | DECAY_SCALEOUT | 201.4 | 24.4 | -177.0 | -2.19 | 1231 | 4/27/0 |
| Spec-built | EXTEND_HORIZON_X2 | 114.5 | -46.2 | -160.7 | None | 1 | 0/1/0 |
| Spec-built | NIGHT1_ONLY | 114.5 | 2.9 | -111.6 | None | 1 | 0/1/0 |
| Spec-built | DECAY_SCALEOUT | 114.5 | 2.9 | -111.6 | None | 1 | 0/1/0 |
| Tensor | EXTEND_HORIZON_X2 | -3280.8 | -3280.8 | 0.0 | None | 5 | 0/0/5 |
| Tensor | NIGHT1_ONLY | -3280.8 | -591.9 | 2688.9 | 3.21 | 5 | 4/1/0 |
| Tensor | DECAY_SCALEOUT | -3280.8 | -591.9 | 2688.9 | 3.21 | 5 | 4/1/0 |

## DECAY AGAINST EACH CRUDE ARM, COMMON TRADES

| Family | Crude arm | Decay mean | Crude mean | Decay minus crude | t | Common n |
|---|---|---|---|---|---|---|
| Aster | EXTEND_HORIZON_X2 | -21.7 | 93.4 | -115.2 | -2.08 | 427 |
| Aster | NIGHT1_ONLY | -21.7 | -30.2 | 8.5 | 0.57 | 427 |
| Fires and singles | EXTEND_HORIZON_X2 | 34.9 | 187.4 | -152.5 | -1.51 | 83 |
| Fires and singles | NIGHT1_ONLY | 34.9 | 33.5 | 1.4 | 0.05 | 83 |
| Lazarus/Q07/MN | DROP_STOP | 48.6 | 1246.8 | -1198.2 | -4.16 | 277 |
| Lazarus/Q07/MN | EXTEND_HORIZON_X2 | 24.4 | 96.6 | -72.2 | -0.91 | 1231 |
| Lazarus/Q07/MN | NIGHT1_ONLY | 24.4 | 24.8 | -0.4 | -0.68 | 1231 |
| Lazarus/Q07/MN | WIDEN_STOP_X2 | 48.6 | 1269.3 | -1220.7 | -4.31 | 277 |
| Spec-built | EXTEND_HORIZON_X2 | 2.9 | -46.2 | 49.1 | None | 1 |
| Spec-built | NIGHT1_ONLY | 2.9 | 2.9 | 0.0 | None | 1 |
| Tensor | EXTEND_HORIZON_X2 | -591.9 | -3280.8 | 2688.9 | 3.21 | 5 |
| Tensor | NIGHT1_ONLY | -591.9 | -591.9 | 0.0 | None | 5 |

## SLEEVE-LEVEL DECAY MOVERS (n >= 15)

Positive (3 rows over 2 distinct streams):

| Sleeve | Family | Base mean | Decay mean | Delta | t | n | Mirror of |
|---|---|---|---|---|---|---|---|
| aster_breakout_ada_fullcash | Aster | -497.3 | -6.3 | 491.0 | 4.62 | 32 | aster_breakout_ada_vol1pct |
| aster_breakout_ada_vol1pct | Aster | -497.3 | -6.3 | 491.0 | 4.62 | 32 | aster_breakout_ada_fullcash |
| aster_etf_qqq_qld_monthly | Aster | -450.3 | -92.8 | 357.5 | 2.46 | 15 | None |

Negative (4 rows, all Lazarus, the same sleeves that carried KG-7's night-1 miss):

| Sleeve | Family | Base mean | Decay mean | Delta | t | n | Mirror of |
|---|---|---|---|---|---|---|---|
| 1w | Lazarus/Q07/MN | 1725.0 | 52.1 | -1672.9 | -1.59 | 28 | None |
| 1wa | Lazarus/Q07/MN | 1256.3 | 13.3 | -1243.0 | -1.4 | 34 | None |
| s_1wlab | Lazarus/Q07/MN | 587.6 | 28.2 | -559.4 | -1.11 | 80 | None |
| 1d | Lazarus/Q07/MN | 267.0 | -37.9 | -305.0 | -1.79 | 56 | None |

## NAMED REMAINDERS

- Every number here is replay evidence on stored daily closes. The arming check for the two sleeve-level leads is the forward shadow run named in POTENTIAL EDGE FOUND; it has not been executed, here or in KG-7.
- The phase curves themselves rest on KG-4's cells, whose cluster counts run from 12 dates (fleet N1) down to 1 date (Tensor N4+), and they were measured on the live dispatcher record while the replay grades a different population of streams. That population mismatch is KG-7's named interpretation for the original non-transfer, and it applies to this lane unchanged; nothing in the continuous form repairs it.
- The two post-peak half-lives (Aster 3.528, Fires 0.564) are zero-degree-of-freedom interpolations of three bucket rates each, printed as such in the table.
- 34 of the 57 union sleeves carry no registered exit params and were varied against the DEFAULT_HOLD10 convention, inherited from KG-7; their decay schedules are schedules against a convention, not against their own exits.
- Tensor's family cells rest on 5 paired trades from 5 single-entry sleeves and Spec-built's on 1 trade; neither can carry a verdict in either direction.
- With this lane, all three KG-8 variations have now been run (closing-imbalance conditioning as KG-10, the LS1 break-split as KG-9, decay-weighted exits here). No KG-8 variation remains open.

STATUS: PARTIAL. Proven on the final artifacts: the half-life table (5 fits, degeneracy rule applied as stated, the one-sided-check correction disclosed with its superseded figure named), the decay arm graded on all 57 union sleeves with KG-7's machinery verified by exact reproduction of all 197 graded and 88 not-applicable KG-7 rows, per-family paired deltas for every arm, and the engagement verdict graded against the claim stated before the run: NOT CONFIRMED as a differentiator, with KG-7's non-transfer verdict strengthened to cover the continuous form. The PARTIAL names what the record cannot carry: the two sleeve-level leads are replay results whose forward shadow check has not run; the Tensor and Spec-built family cells are untestable at n=5 and n=1; and the post-peak half-lives are interpolations, not measurements.
