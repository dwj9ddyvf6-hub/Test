# VEIN 2 DIG: GATE ATTRIBUTION OVER THE REMAINING SILENT CLASSES

Scope: every sleeve class that remained silent or gated after the fix program, attributed gate by gate with the operator-as-diagnostic method (one gate dropped at a time, diagnostic only; no production code was changed in this lane). Sources: pass2/UNBLOCK-2-REGISTER.jsonl and its run files, pass2/FIX-PROGRAM-REPORT.md, pass2/FIX-F4-ROUTES.md, pass2/FIX-F1-Q07.md, KG-7 and KG-13 for the exit-side context, and new diagnostic runs and counts produced in pass2/vein2_work/. One scope correction is printed where it belongs: aster_squeeze_ada_fullcash was filed by F4 under BARS-ONLY-SINGLES but its engine is the batch5 negative-funding squeeze, so it is attributed inside the funding class below (28 funding sleeves in total). Q07-ML-GATED (11 sleeves) is included alongside Q07-SMALL because F4 carried it as a remaining gated class. OPTIONS-FEED-ABSENCE and KRAKEN-CURRENT-ONLY are outside the named scope of this dig; their route status stands as printed in FIX-F4-ROUTES.md.

## POTENTIAL EDGE FOUND

**LEAD 1 (the class-level find): the funding-gated Aster family was never gated by its sign legs. It was unfed, and with the input served its streams grade positive.** Unblock 2 served no funding series at all, so all 28 sleeves failed closed for the whole 1749-bar replay. This lane fetched OKX funding-rate-history (ADA-USDT-SWAP and LINK-USDT-SWAP, 292 observations each, 2026-08-10 to 2026-11-15) and re-ran each sleeve's own engine with the series served latest-as-of bar close. With funding served, all 28 of 28 funding sleeves fire (aster_link_nfs_norm_vol needed its scalar serving form corrected mid-lane; it then fired 22). The squeeze streams grade strongly on their own tapes versus QQQ: LINK negative-funding squeeze fixed16 fwd5 excess +535.7bp (n=12, t=2.11); LINK batch13 nfs normalization sleeve fwd5 +609.8bp (n=12, t=2.18); LINK squeeze fixed96 and lost-breakout arms +398.9bp (n=6); LINK normalization-failure arms +621.6bp (n=7, t=1.53); ADA squeeze arms +269.0 to +591.5bp at fwd5. The sign legs blocked almost none of it: sign-drop revealed zero extra entries for 18 of 28 sleeves, and of the 10 sleeves where it revealed entries, 7 revealed entries that grade at or below zero or are unpriceable (the exceptions are Leads 2 and 3, covering 3 sleeves and 2 distinct streams). Cheapest forward check: serve one funding series (the OKX route this lane proved, or the sleeves' live Coinalyze producer) as a shadow producer and grade the first 20 live fires per family. The replay window is short (503 funding-observed bars), so forward grading is the arbiter; the point of the lead is that a whole family of positive-grading streams is dark today for want of one producer, not for want of signal.

**LEAD 2 (MISPRICED gate): the LINK absorption negative-funding sign leg (desk3/aster_b11_crypto.py, rate < 0 exact).** For aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash and its volume1pct sizing twin (one stream, two sleeves): with true funding the stream took 2 entries; forcing the sign to the qualifying side at every funding-observed bar revealed 10 further entries the absorption condition produced and the sign leg refused. The revealed entries grade fwd5 excess +351.6bp (n=5, t=0.82), fwd3 +117.4bp (n=4), fwd1 -175.8bp (n=6), fwd10 -663.7bp (n=3): positive at the sleeve's own 16-hour-hold neighborhood horizons (fwd3, fwd5), negative at fwd1 and fwd10. Cheapest forward check: shadow-grade the next 10 LINK absorption signals that arrive with funding >= 0 beside the taken ones; if the shadow set grades positive at fwd5, the fix program owns a variation with the sign leg widened, registered as a variation, never as an edit to the original.

**LEAD 3 (MISPRICED gate, low n): the ADA absorption negative-funding sign leg on the volume1pct arm (aster_abs_neg_ada_vol1pct, rate < 0 exact).** Sign-drop revealed 3 entries grading fwd1 +570.8bp (n=2), fwd3 +588.9bp (n=2), fwd10 +457.4bp (n=1), fwd5 unpriceable. The fullcash arm of the same signal is the opposite verdict: its sign leg is LOAD-BEARING (21 revealed entries, fwd5 -324.9bp, n=8, t=-1.64). The same sign leg prices differently by sizing arm because the 1% volume cap changes which signals become positions (23 sign-drop entries fullcash versus 5 volume1pct). Cheapest forward check: shadow-grade the next 10 sign-refused ADA absorption signals on the volume1pct arm only.

**LEAD 4 (UNFED input that looks like a producer defect): rule_1h_cyan_raw's smhUp leg.** On the sleeve's own fire set (189 fires, 109 symbols, state/ingest/rule_fires.json), rangeatr >= 2.05 passes 56 fires, wtgap >= 6.88 passes 65, both together 17, and smhUp == 1 passes 0 of 189: the field is constant 0 across the entire drop. Either SMH was never in a weekly uptrend at any cyan fire in 16 months, or the scorer's smhUp field is not being computed. Cheapest forward check: recompute SMH weekly trend directly from SMH daily bars at the 17 jointly-qualifying fire timestamps; if any recompute true, the drop field is defective and a 17-fire historical stream was refused by a dead input.

**UNBLOCK (not graded as edge): ETF-B9 eligibility.** The secondary store already holds 501-session histories for all 14 universe names. The primary cache is the only gap (QQQ 515 sessions; SPY and sector names 179 to 180; SMH and XLU zero). Serve primary histories at secondary depth and the INTERVAL sleeves can run their selection at full eligibility for the first time; their selection logic has never been tested at a 14-name eligible set, so no edge is claimed, only the unblock.

**ANTI-LEAD (printed so nobody chases it): the Tensor ret60 gates are load-bearing.** On the 42 archived fires re-stamped through the desk's native pass, ret60 is the one gate whose single drop reveals fires: dropping ret60 >= 31 reveals all 42 fires for the C1 all-arms and 38 for the C1 hot-arms; dropping ret60 >= 0 reveals 8 fires for the G4 arms (6 for G4 hot). The revealed fires grade negative at fwd1, the only horizon the daily cache prices past 2026-11-12: -366.0bp (n=42), -400.5bp (n=38), -386.1bp (n=8), -507.7bp (n=6). No other single-gate drop reveals a single fire for any consumer group, so the rest of the refusal is joint, not a hidden mispriced gate.

## METHOD

- Funding class: new engine runs in pass2/vein2_work/ (vein2_driver.py, adapted from the KG-6 driver; OKX funding fetched by fetch_okx.py). Three runs or counts per sleeve: original no-funding replay (0 entries), true-funding replay, and a sign-drop run that forces only the funding sign at funding-observed bars (availability intact). Revealed entries are graded on the sleeve's own PF daily stream versus QQQ with Lane 2's grader. Exit-policy variants (normalization, normalization_failure, lost_breakout) also move exit timing under a forced sign, so their entry streams diverge by path; their sign rows carry that note.
- Tensor class: the archived 2026-11-11 and 2026-11-12 bundles were re-served through desk3/tensor_warm._apply_native_pass (the F4 route); all 42 fires gained complete feature cells. Each consumer group's gate set was read from desk3/tensor_native.py r19_passes and desk3/aster_batch14.py, applied per fire, one gate dropped at a time. Revealed fires are graded at fwd1 only: the daily cache ends 2026-11-13, so fwd3 and fwd5 do not exist for these fires yet.
- Q07 classes: Unblock 2's per-filter drop runs (on disk in pass2/work/runs/) were read back per sleeve, and the upstream refusals (band, alt-tag serving) were attributed from FIX-F1-Q07.md's tagged-evidence probe and remainders.
- B9, MN, RSI2, TIMING, REAL-RULE: gate legs were enumerated from the engine code and counted directly on the served data (pass2/vein2_work/vein2_counts.py, conjunction.py, rsi2_counts.py), because for these classes the binding question is leg occurrence on the sleeve's own stream, which a count answers exactly.
- BARS-ONLY-SINGLES: attributed at conjunction level from the full-span Unblock 2 replays plus each module's declared inputs, with named UNFED rows where a declared input series does not exist on this machine. Leg-level occurrence decomposition for these 46 sleeves is a named remainder below, not silently claimed.
- Classification rule, fixed before results were read: MISPRICED requires revealed entries grading positive on the sleeve's own stream (primary horizon fwd5 excess versus QQQ, falling back to fwd10, fwd3, fwd1 by priceable n). LOAD-BEARING covers revealed entries grading at or below zero, entries that would violate the signal's stated logic, and gates whose single drop reveals nothing (classified by elimination and marked as such in the register notes). UNFED names the exact missing input.

## CLASS: FUNDING-GATED ASTER (28 SLEEVES: THE 27 FROM F4 PLUS aster_squeeze_ada_fullcash)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| aster_abs_neg_ada_fullcash | funding_series_availability | 0 | 2 | UNFED |
| aster_abs_neg_ada_fullcash | funding_sign: rate < 0 (exact, aster_sleeves/_common.py) | 2 | 23 | LOAD-BEARING |
| aster_abs_neg_ada_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 2 | n/a | LOAD-BEARING |
| aster_abs_neg_ada_vol1pct | funding_series_availability | 0 | 2 | UNFED |
| aster_abs_neg_ada_vol1pct | funding_sign: rate < 0 (exact, aster_sleeves/_common.py) | 2 | 5 | MISPRICED |
| aster_abs_neg_ada_vol1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 2 | n/a | LOAD-BEARING |
| aster_abs_nonneg_ada_fullcash | funding_series_availability | 0 | 8 | UNFED |
| aster_abs_nonneg_ada_fullcash | funding_sign: rate >= 0 (exact, aster_sleeves/_common.py) | 8 | 9 | LOAD-BEARING |
| aster_abs_nonneg_ada_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 8 | n/a | LOAD-BEARING |
| aster_abs_nonneg_ada_vol1pct | funding_series_availability | 0 | 8 | UNFED |
| aster_abs_nonneg_ada_vol1pct | funding_sign: rate >= 0 (exact, aster_sleeves/_common.py) | 8 | 9 | LOAD-BEARING |
| aster_abs_nonneg_ada_vol1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 8 | n/a | LOAD-BEARING |
| aster_link_nfs_norm_vol | funding_series_availability | 0 | 22 | UNFED |
| aster_link_nfs_norm_vol | funding_sign: rate < 0.00015 (desk3/aster_batch13.py, cured from < 0 in two rounds) | 22 | 8 | LOAD-BEARING |
| aster_link_nfs_norm_vol | bar_signal_condition (breakout20 or absorption shock+confirm) | 22 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct | funding_series_availability | 0 | 12 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 12 | 12 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 12 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash | funding_series_availability | 0 | 7 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 7 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 7 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct | funding_series_availability | 0 | 7 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 7 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 7 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash | funding_series_availability | 0 | 7 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 7 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 7 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct | funding_series_availability | 0 | 7 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 7 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 7 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash | funding_series_availability | 0 | 7 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 7 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 7 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct | funding_series_availability | 0 | 7 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 7 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 7 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash | funding_series_availability | 0 | 16 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 16 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 16 | n/a | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct | funding_series_availability | 0 | 16 | UNFED |
| aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct | funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0) | 16 | 7 | LOAD-BEARING |
| aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 16 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash | funding_series_availability | 0 | 2 | UNFED |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash | funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py) | 2 | 12 | MISPRICED |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 2 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct | funding_series_availability | 0 | 2 | UNFED |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct | funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py) | 2 | 12 | MISPRICED |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 2 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_fullcash | funding_series_availability | 0 | 4 | UNFED |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_fullcash | funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py) | 4 | 5 | LOAD-BEARING |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 4 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct | funding_series_availability | 0 | 4 | UNFED |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct | funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py) | 4 | 5 | LOAD-BEARING |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 4 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash | funding_series_availability | 0 | 19 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 19 | 19 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 19 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_volume1pct | funding_series_availability | 0 | 19 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_volume1pct | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 19 | 19 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 19 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash | funding_series_availability | 0 | 8 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 8 | 8 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 8 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_volume1pct | funding_series_availability | 0 | 8 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_volume1pct | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 8 | 8 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 8 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_fullcash | funding_series_availability | 0 | 8 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_fullcash | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 8 | 8 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 8 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_volume1pct | funding_series_availability | 0 | 8 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_volume1pct | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 8 | 8 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 8 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash | funding_series_availability | 0 | 12 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 12 | 8 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 12 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct | funding_series_availability | 0 | 12 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 12 | 8 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct | bar_signal_condition (breakout20 or absorption shock+confirm) | 12 | n/a | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash | funding_series_availability | 0 | 8 | UNFED |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash | funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds) | 8 | 8 | LOAD-BEARING |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 8 | n/a | LOAD-BEARING |
| aster_squeeze_ada_fullcash | funding_series_availability | 0 | 12 | UNFED |
| aster_squeeze_ada_fullcash | funding_sign: rate < 0.0002 (aster_sleeves/_common.py, cured from < 0) | 12 | 12 | LOAD-BEARING |
| aster_squeeze_ada_fullcash | bar_signal_condition (breakout20 or absorption shock+confirm) | 12 | n/a | LOAD-BEARING |

Gate notes:

- **aster_abs_neg_ada_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_abs_neg_ada_fullcash / funding_sign: rate < 0 (exact, aster_sleeves/_common.py)**: Sign-drop reveals 21 entries grading at or below zero on the sleeve own stream (primary fwd5 excess -324.9bp, n=8).
- **aster_abs_neg_ada_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_abs_neg_ada_vol1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_abs_neg_ada_vol1pct / funding_sign: rate < 0 (exact, aster_sleeves/_common.py)**: Sign-drop reveals 3 entries grading positive on the sleeve own stream (primary fwd10 excess +457.4bp, n=1). LEAD.
- **aster_abs_neg_ada_vol1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_abs_nonneg_ada_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_abs_nonneg_ada_fullcash / funding_sign: rate >= 0 (exact, aster_sleeves/_common.py)**: Sign-drop reveals 3 entries grading at or below zero on the sleeve own stream (primary fwd5 excess -22.0bp, n=1).
- **aster_abs_nonneg_ada_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_abs_nonneg_ada_vol1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_abs_nonneg_ada_vol1pct / funding_sign: rate >= 0 (exact, aster_sleeves/_common.py)**: Sign-drop reveals 3 entries grading at or below zero on the sleeve own stream (primary fwd5 excess -22.0bp, n=1).
- **aster_abs_nonneg_ada_vol1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_link_nfs_norm_vol / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_link_nfs_norm_vol / funding_sign: rate < 0.00015 (desk3/aster_batch13.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_link_nfs_norm_vol / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 1 entries grading at or below zero on the sleeve own stream (primary fwd10 excess -337.5bp, n=1).
- **aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 1 entries grading at or below zero on the sleeve own stream (primary fwd10 excess -337.5bp, n=1).
- **aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct / funding_sign: rate < 0.0002 (desk3/aster_crypto.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash / funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py)**: Sign-drop reveals 10 entries grading positive on the sleeve own stream (primary fwd5 excess +351.6bp, n=5). LEAD.
- **aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct / funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py)**: Sign-drop reveals 10 entries grading positive on the sleeve own stream (primary fwd5 excess +351.6bp, n=5). LEAD.
- **aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_fullcash / funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py)**: Sign-drop reveals 1 entry, none priceable at any horizon (tape ends first); no positive grade exists, so the gate is not counted mispriced.
- **aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct / funding_sign: rate < 0 / rate >= 0 by family (exact, desk3/aster_b11_crypto.py)**: Sign-drop reveals 1 entry, none priceable at any horizon (tape ends first); no positive grade exists, so the gate is not counted mispriced.
- **aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed16_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed16_volume1pct / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed16_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed96_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed96_volume1pct / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_fixed96_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_fullcash / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_volume1pct / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash / funding_sign: rate < 0.00015 (desk3/aster_b12_crypto.py, cured from < 0 in two rounds)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.
- **aster_squeeze_ada_fullcash / funding_series_availability**: Missing input: ADAUSDT/LINKUSDT funding-rate history in the desk caches and a registered v3 funding producer. The OKX route reaches back only to 2026-08-10, so the diagnostic covers the 503 funding-observed eval bars inside the 1749-bar replay; bars before 2026-08-10 still fail closed for want of any print.
- **aster_squeeze_ada_fullcash / funding_sign: rate < 0.0002 (aster_sleeves/_common.py, cured from < 0)**: Sign-drop reveals 0 entries beyond the true-funding stream: on the funding-observed window the sign gate blocked nothing the bar conditions produced. The sleeve silence was availability, not the sign leg.
- **aster_squeeze_ada_fullcash / bar_signal_condition (breakout20 or absorption shock+confirm)**: The bar condition is the signal leg, not a separable gate; it is classified load-bearing under the stated-logic clause.

## CLASS: TENSOR-REFUSAL CONSUMERS (20 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| aster_r19_tensor_g4_hot_delay_25 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_delay_25 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_delay_25 | ret60>=0 | 0 | 6 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_delay_25 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_delay_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_delay_25 | atr>1 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_reserve_25 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_reserve_25 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_reserve_25 | ret60>=0 | 0 | 6 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_reserve_25 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_reserve_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_hot_reserve_25 | atr>1 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_red_timeout_25 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_red_timeout_25 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_red_timeout_25 | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_r19_tensor_g4_red_timeout_25 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_r19_tensor_g4_red_timeout_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_all_25 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_all_25 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_all_25 | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_tensor_g4_delay_all_25 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_all_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_cool_25 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_cool_25 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_cool_25 | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_tensor_g4_delay_cool_25 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_cool_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_delay_cool_25 | atr<=1.5 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_10 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_10 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_10 | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_10 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_10 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_25 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_25 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_25 | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_25 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_all_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_cool_25 | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_cool_25 | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_cool_25 | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_tensor_g4_reserve_cool_25 | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_cool_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_g4_reserve_cool_25 | atr<=1.5 | 0 | 0 | LOAD-BEARING |
| aster_tensor_beta_cash_all_25 | ret60>=31 | 0 | 42 | LOAD-BEARING |
| aster_tensor_beta_cash_all_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_beta_cash_all_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_cool_25 | marker buy-cyan | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_cool_25 | close<=5 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_cool_25 | ret60>=31 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_cool_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_cool_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_cool_25 | atr<=1.0 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_hot_25 | ret60>=31 | 0 | 38 | LOAD-BEARING |
| aster_tensor_c1_cash_hot_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_hot_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_hot_25 | atr>1 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_all_25 | ret60>=31 | 0 | 42 | LOAD-BEARING |
| aster_tensor_c1_cash_all_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_cash_all_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_all_25 | ret60>=31 | 0 | 42 | LOAD-BEARING |
| aster_tensor_c1_delay_all_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_all_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_cool_25 | marker buy-cyan | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_cool_25 | close<=5 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_cool_25 | ret60>=31 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_cool_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_cool_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_cool_25 | atr<=1.0 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_hot_25 | ret60>=31 | 0 | 38 | LOAD-BEARING |
| aster_tensor_c1_delay_hot_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_hot_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_delay_hot_25 | atr>1 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_all_25 | ret60>=31 | 0 | 42 | LOAD-BEARING |
| aster_tensor_c1_reserve_all_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_all_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_cool_25 | marker buy-cyan | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_cool_25 | close<=5 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_cool_25 | ret60>=31 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_cool_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_cool_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_cool_25 | atr<=1.0 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_hot_25 | ret60>=31 | 0 | 38 | LOAD-BEARING |
| aster_tensor_c1_reserve_hot_25 | vol20>=0.07 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_hot_25 | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_c1_reserve_hot_25 | atr>1 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_a | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_a | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_a | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_tensor_leaps_a | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_a | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_b | close<=10 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_b | depth60>=70 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_b | ret60>=0 | 0 | 8 | LOAD-BEARING |
| aster_tensor_leaps_b | vol20>=0.09 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_b | dv20>=2e6 | 0 | 0 | LOAD-BEARING |
| aster_tensor_leaps_a | options_chain_for_leaps_expression (DTE 540-720, delta 0.6-0.8) | 0 | n/a | UNFED |
| aster_tensor_leaps_b | options_chain_for_leaps_expression (DTE 540-720, delta 0.6-0.8) | 0 | n/a | UNFED |
| aster_tensor_w1_recovery | weekly_state_repair_trigger (damaged position state in the WSTATE feed) | 0 | n/a | LOAD-BEARING |

Gate notes:

- **aster_r19_tensor_g4_hot_delay_25 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_delay_25 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_delay_25 / ret60>=0**: Single-gate drop reveals 6 fires on the 42-fire stamped set; revealed fires grade -507.7bp excess at fwd1 (n=6), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_r19_tensor_g4_hot_delay_25 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_delay_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_delay_25 / atr>1**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_reserve_25 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_reserve_25 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_reserve_25 / ret60>=0**: Single-gate drop reveals 6 fires on the 42-fire stamped set; revealed fires grade -507.7bp excess at fwd1 (n=6), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_r19_tensor_g4_hot_reserve_25 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_reserve_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_hot_reserve_25 / atr>1**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_red_timeout_25 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_red_timeout_25 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_red_timeout_25 / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_r19_tensor_g4_red_timeout_25 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_r19_tensor_g4_red_timeout_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_all_25 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_all_25 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_all_25 / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_g4_delay_all_25 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_all_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_cool_25 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_cool_25 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_cool_25 / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_g4_delay_cool_25 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_cool_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_delay_cool_25 / atr<=1.5**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_10 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_10 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_10 / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_g4_reserve_all_10 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_10 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_25 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_25 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_25 / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_g4_reserve_all_25 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_all_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_cool_25 / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_cool_25 / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_cool_25 / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_g4_reserve_cool_25 / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_cool_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_g4_reserve_cool_25 / atr<=1.5**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_beta_cash_all_25 / ret60>=31**: Single-gate drop reveals 42 fires on the 42-fire stamped set; revealed fires grade -366.0bp excess at fwd1 (n=42), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_beta_cash_all_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_beta_cash_all_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_cool_25 / marker buy-cyan**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_cool_25 / close<=5**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_cool_25 / ret60>=31**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_cool_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_cool_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_cool_25 / atr<=1.0**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_hot_25 / ret60>=31**: Single-gate drop reveals 38 fires on the 42-fire stamped set; revealed fires grade -400.5bp excess at fwd1 (n=38), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_c1_cash_hot_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_hot_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_hot_25 / atr>1**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_all_25 / ret60>=31**: Single-gate drop reveals 42 fires on the 42-fire stamped set; revealed fires grade -366.0bp excess at fwd1 (n=42), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_c1_cash_all_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_cash_all_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_all_25 / ret60>=31**: Single-gate drop reveals 42 fires on the 42-fire stamped set; revealed fires grade -366.0bp excess at fwd1 (n=42), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_c1_delay_all_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_all_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_cool_25 / marker buy-cyan**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_cool_25 / close<=5**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_cool_25 / ret60>=31**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_cool_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_cool_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_cool_25 / atr<=1.0**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_hot_25 / ret60>=31**: Single-gate drop reveals 38 fires on the 42-fire stamped set; revealed fires grade -400.5bp excess at fwd1 (n=38), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_c1_delay_hot_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_hot_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_delay_hot_25 / atr>1**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_all_25 / ret60>=31**: Single-gate drop reveals 42 fires on the 42-fire stamped set; revealed fires grade -366.0bp excess at fwd1 (n=42), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_c1_reserve_all_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_all_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_cool_25 / marker buy-cyan**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_cool_25 / close<=5**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_cool_25 / ret60>=31**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_cool_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_cool_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_cool_25 / atr<=1.0**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_hot_25 / ret60>=31**: Single-gate drop reveals 38 fires on the 42-fire stamped set; revealed fires grade -400.5bp excess at fwd1 (n=38), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_c1_reserve_hot_25 / vol20>=0.07**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_hot_25 / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_c1_reserve_hot_25 / atr>1**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_a / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_a / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_a / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_leaps_a / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_a / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_b / close<=10**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_b / depth60>=70**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_b / ret60>=0**: Single-gate drop reveals 8 fires on the 42-fire stamped set; revealed fires grade -386.1bp excess at fwd1 (n=8), the only horizon the daily cache prices past 2026-11-12 (cache ends 2026-11-13). The gate is load-bearing on the priceable evidence.
- **aster_tensor_leaps_b / vol20>=0.09**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_b / dv20>=2e6**: Single-gate drop reveals 0 of 42 stamped fires: this gate is not individually binding on the archived set; the refusal is joint. Classification is by elimination (the one gate whose drop reveals fires, ret60, reveals negative-grading fires), not by a positive test of this gate.
- **aster_tensor_leaps_a / options_chain_for_leaps_expression (DTE 540-720, delta 0.6-0.8)**: Missing input: historical LEAPS options chains (contracts with DTE 540-720 and delta 0.6-0.8) for the G4 event symbols
- **aster_tensor_leaps_b / options_chain_for_leaps_expression (DTE 540-720, delta 0.6-0.8)**: Missing input: historical LEAPS options chains (contracts with DTE 540-720 and delta 0.6-0.8) for the G4 event symbols
- **aster_tensor_w1_recovery / weekly_state_repair_trigger (damaged position state in the WSTATE feed)**: Trigger condition never occurred on the served state feed; classified load-bearing under the stated-logic clause.

## CLASS: Q07-SMALL (24 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| s_q07w_c52_sm_cheap5_ins2_mom6 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c52_sm_cheap5_ins2_mom6 | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_cheap5_ins2_mom6 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_cheap5_ins2_mom6 | drop filter mom6 | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_cheap5_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c52_sm_cheap5_wcov | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_cheap5_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_deep70_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c52_sm_deep70_wcov | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_deep70_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_tierA_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c52_sm_tierA_wcov | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_tierA_wcov | drop filter tierA | 0 | 0 | LOAD-BEARING |
| s_q07w_c52_sm_tierA_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_deep70_ins2_vix20 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c78_sm_deep70_ins2_vix20 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_deep70_ins2_vix20 | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_deep70_ins2_vix20 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_deep70_ins2_vix20 | drop filter vix20 | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_deep70_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c78_sm_deep70_wcov | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_deep70_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_ins2_mom6_vix20 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c78_sm_ins2_mom6_vix20 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_ins2_mom6_vix20 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_ins2_mom6_vix20 | drop filter mom6 | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_ins2_mom6_vix20 | drop filter vix20 | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_tierA_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_c78_sm_tierA_wcov | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_tierA_wcov | drop filter tierA | 0 | 0 | LOAD-BEARING |
| s_q07w_c78_sm_tierA_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_deep70_ins2_vix20 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g52_sm_deep70_ins2_vix20 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_deep70_ins2_vix20 | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_deep70_ins2_vix20 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_deep70_ins2_vix20 | drop filter vix20 | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_deep70_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g52_sm_deep70_wcov | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_deep70_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_ins2_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g52_sm_ins2_wcov | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_ins2_wcov | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_ins2_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_tierA_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g52_sm_tierA_wcov | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_tierA_wcov | drop filter tierA | 0 | 0 | LOAD-BEARING |
| s_q07w_g52_sm_tierA_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_cheap5_ins2 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g78_sm_cheap5_ins2 | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_cheap5_ins2 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_deep70_ins2 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g78_sm_deep70_ins2 | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_deep70_ins2 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_deep70_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g78_sm_deep70_wcov | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_deep70_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_tierA_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g78_sm_tierA_wcov | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_tierA_wcov | drop filter tierA | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_sm_tierA_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_deep70_ins2 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s52_sm_cheap5_deep70_ins2 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_deep70_ins2 | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_deep70_ins2 | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_deep70_ins2 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_ins2_vix20 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s52_sm_cheap5_ins2_vix20 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_ins2_vix20 | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_ins2_vix20 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_ins2_vix20 | drop filter vix20 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s52_sm_cheap5_wcov | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_cheap5_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_deep70_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s52_sm_deep70_wcov | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_sm_deep70_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_cheap5_ins2_vix20 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s78_sm_cheap5_ins2_vix20 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_cheap5_ins2_vix20 | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_cheap5_ins2_vix20 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_cheap5_ins2_vix20 | drop filter vix20 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_cheap5_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s78_sm_cheap5_wcov | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_cheap5_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_deep70_ins2 | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s78_sm_deep70_ins2 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_deep70_ins2 | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_deep70_ins2 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_deep70_wcov | band==sm (small) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s78_sm_deep70_wcov | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_sm_deep70_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |

Gate notes:

- **s_q07w_c52_sm_cheap5_ins2_mom6 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c52_sm_cheap5_ins2_mom6 / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_cheap5_ins2_mom6 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_cheap5_ins2_mom6 / drop filter mom6**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_cheap5_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c52_sm_cheap5_wcov / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_cheap5_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_deep70_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c52_sm_deep70_wcov / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_deep70_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_tierA_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c52_sm_tierA_wcov / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_tierA_wcov / drop filter tierA**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c52_sm_tierA_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_deep70_ins2_vix20 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c78_sm_deep70_ins2_vix20 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_deep70_ins2_vix20 / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_deep70_ins2_vix20 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_deep70_ins2_vix20 / drop filter vix20**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_deep70_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c78_sm_deep70_wcov / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_deep70_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_ins2_mom6_vix20 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c78_sm_ins2_mom6_vix20 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_ins2_mom6_vix20 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_ins2_mom6_vix20 / drop filter mom6**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_ins2_mom6_vix20 / drop filter vix20**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_tierA_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_c78_sm_tierA_wcov / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_tierA_wcov / drop filter tierA**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_c78_sm_tierA_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_deep70_ins2_vix20 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g52_sm_deep70_ins2_vix20 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_deep70_ins2_vix20 / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_deep70_ins2_vix20 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_deep70_ins2_vix20 / drop filter vix20**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_deep70_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g52_sm_deep70_wcov / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_deep70_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_ins2_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g52_sm_ins2_wcov / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_ins2_wcov / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_ins2_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_tierA_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g52_sm_tierA_wcov / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_tierA_wcov / drop filter tierA**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g52_sm_tierA_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_cheap5_ins2 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g78_sm_cheap5_ins2 / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_cheap5_ins2 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_deep70_ins2 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g78_sm_deep70_ins2 / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_deep70_ins2 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_deep70_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g78_sm_deep70_wcov / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_deep70_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_tierA_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g78_sm_tierA_wcov / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_tierA_wcov / drop filter tierA**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_sm_tierA_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_deep70_ins2 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s52_sm_cheap5_deep70_ins2 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_deep70_ins2 / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_deep70_ins2 / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_deep70_ins2 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_ins2_vix20 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s52_sm_cheap5_ins2_vix20 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_ins2_vix20 / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_ins2_vix20 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_ins2_vix20 / drop filter vix20**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s52_sm_cheap5_wcov / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_cheap5_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_deep70_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s52_sm_deep70_wcov / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_sm_deep70_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_cheap5_ins2_vix20 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s78_sm_cheap5_ins2_vix20 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_cheap5_ins2_vix20 / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_cheap5_ins2_vix20 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_cheap5_ins2_vix20 / drop filter vix20**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_cheap5_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s78_sm_cheap5_wcov / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_cheap5_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_deep70_ins2 / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s78_sm_deep70_ins2 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_deep70_ins2 / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_deep70_ins2 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_deep70_wcov / band==sm (small) (universe gate)**: Missing input: a sm (small) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s78_sm_deep70_wcov / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_sm_deep70_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.

## CLASS: Q07-ML-GATED (11 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| s_q07w_g78_mi_cheap5_deep70_ins2 | band==mi (micro) (universe gate) | 0 | n/a | UNFED |
| s_q07w_g78_mi_cheap5_deep70_ins2 | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_g78_mi_cheap5_deep70_ins2 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_mi_cheap5_deep70_ins2 | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_mi_cheap5_deep70_ins2 | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_g78_mi_cheap5_deep70_ins2 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_ml_deep70_vix20_wlow | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s52_ml_deep70_vix20_wlow | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_ml_deep70_vix20_wlow | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_ml_deep70_vix20_wlow | drop filter vix20 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_ml_deep70_vix20_wlow | drop filter wlow | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_ml_deep70_wlow | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s52_ml_deep70_wlow | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_ml_deep70_wlow | drop filter wlow | 0 | 0 | LOAD-BEARING |
| s_q07w_s52_ml_ins2_mom6_vix20 | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s52_ml_ins2_mom6_wlow | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s78_mi_ats_z1_cheap5 | band==mi (micro) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s78_mi_ats_z1_cheap5 | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s78_mi_ats_z1_mom6 | band==mi (micro) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s78_mi_ats_z1_mom6 | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s78_mi_cheap5_ins2_mom6 | band==mi (micro) (universe gate) | 0 | n/a | UNFED |
| s_q07w_s78_mi_cheap5_ins2_mom6 | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s78_mi_cheap5_ins2_mom6 | drop all alt filters jointly | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_mi_cheap5_ins2_mom6 | drop filter cheap5 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_mi_cheap5_ins2_mom6 | drop filter ins2 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_mi_cheap5_ins2_mom6 | drop filter mom6 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_ml_deep70_glow_ins2 | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s78_ml_deep70_mom6_wlow | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s78_ml_deep70_mom6_wlow | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_ml_deep70_mom6_wlow | drop filter mom6 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_ml_deep70_mom6_wlow | drop filter wlow | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_ml_deep70_wcov | alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags) | 0 | n/a | UNFED |
| s_q07w_s78_ml_deep70_wcov | drop filter deep70 | 0 | 0 | LOAD-BEARING |
| s_q07w_s78_ml_deep70_wcov | drop filter wcov | 0 | 0 | LOAD-BEARING |

Gate notes:

- **s_q07w_g78_mi_cheap5_deep70_ins2 / band==mi (micro) (universe gate)**: Missing input: a mi (micro) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_g78_mi_cheap5_deep70_ins2 / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_g78_mi_cheap5_deep70_ins2 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_mi_cheap5_deep70_ins2 / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_mi_cheap5_deep70_ins2 / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_g78_mi_cheap5_deep70_ins2 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_ml_deep70_vix20_wlow / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s52_ml_deep70_vix20_wlow / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_ml_deep70_vix20_wlow / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_ml_deep70_vix20_wlow / drop filter vix20**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_ml_deep70_vix20_wlow / drop filter wlow**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_ml_deep70_wlow / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s52_ml_deep70_wlow / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_ml_deep70_wlow / drop filter wlow**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s52_ml_ins2_mom6_vix20 / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s52_ml_ins2_mom6_wlow / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s78_mi_ats_z1_cheap5 / band==mi (micro) (universe gate)**: Missing input: a mi (micro) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s78_mi_ats_z1_cheap5 / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s78_mi_ats_z1_mom6 / band==mi (micro) (universe gate)**: Missing input: a mi (micro) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s78_mi_ats_z1_mom6 / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s78_mi_cheap5_ins2_mom6 / band==mi (micro) (universe gate)**: Missing input: a mi (micro) universe on this machine: small/micro-cap daily bars in the desk cache and composer fires stamped with the sleeve band
- **s_q07w_s78_mi_cheap5_ins2_mom6 / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s78_mi_cheap5_ins2_mom6 / drop all alt filters jointly**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_mi_cheap5_ins2_mom6 / drop filter cheap5**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_mi_cheap5_ins2_mom6 / drop filter ins2**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_mi_cheap5_ins2_mom6 / drop filter mom6**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_ml_deep70_glow_ins2 / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s78_ml_deep70_mom6_wlow / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s78_ml_deep70_mom6_wlow / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_ml_deep70_mom6_wlow / drop filter mom6**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_ml_deep70_mom6_wlow / drop filter wlow**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_ml_deep70_wcov / alt_tag_serving_on_real_fires (wiki/tier/ats/insider tags)**: Missing input: per-fire alt-data tags (wiki coverage/low, tierA, ats_z1, insider ins2 as the sleeve SPEC requires) stamped on the production composer drop; gamma_low for s_q07w_s78_ml_deep70_glow_ins2 has no producer anywhere on the desk
- **s_q07w_s78_ml_deep70_wcov / drop filter deep70**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.
- **s_q07w_s78_ml_deep70_wcov / drop filter wcov**: Drop behind the intact upstream refusal reveals 0: this filter is not the binding constraint on any stream this machine can serve to the sleeve; its own-stream test does not exist here. Classified load-bearing by elimination, not by a positive test.

## CLASS: ETF-B9-ELIGIBILITY (8 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| aster_etf_interval1_c098 | MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores) | 0 | n/a | UNFED |
| aster_etf_interval1_c098 | provider_eligibility_agreement (INTERVAL select: set(other)==set(own)) | 0 | 0 | LOAD-BEARING |
| aster_etf_interval1_m150 | MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores) | 0 | n/a | UNFED |
| aster_etf_interval1_m150 | provider_eligibility_agreement (INTERVAL select: set(other)==set(own)) | 0 | 0 | LOAD-BEARING |
| aster_etf_interval_core25_c098 | MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores) | 0 | n/a | UNFED |
| aster_etf_interval_core25_c098 | provider_eligibility_agreement (INTERVAL select: set(other)==set(own)) | 0 | 0 | LOAD-BEARING |
| aster_etf_interval_core25_m150 | MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores) | 0 | n/a | UNFED |
| aster_etf_interval_core25_m150 | provider_eligibility_agreement (INTERVAL select: set(other)==set(own)) | 0 | 0 | LOAD-BEARING |
| aster_etf_interval_drift1_c098 | MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores) | 0 | n/a | UNFED |
| aster_etf_interval_drift1_c098 | provider_eligibility_agreement (INTERVAL select: set(other)==set(own)) | 0 | 0 | LOAD-BEARING |
| aster_etf_interval_drift1_m150 | MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores) | 0 | n/a | UNFED |
| aster_etf_interval_drift1_m150 | provider_eligibility_agreement (INTERVAL select: set(other)==set(own)) | 0 | 0 | LOAD-BEARING |
| aster_etf_smh_hold_c098 | SMH 252-session primary history (desk3/aster_etf.py _scores eligibility) | 0 | n/a | UNFED |
| aster_etf_smh_hold_m150 | SMH 252-session primary history (desk3/aster_etf.py _scores eligibility) | 0 | n/a | UNFED |

Gate notes:

- **aster_etf_interval1_c098 / MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores)**: Missing input: primary daily history of at least 252 sessions for the 13 non-QQQ universe names (SPY, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLV, XLY at 179-180 served; SMH and XLU absent)
- **aster_etf_interval1_c098 / provider_eligibility_agreement (INTERVAL select: set(other)==set(own))**: Stated-logic rule; dropping it would let the sleeve select on a one-name primary set against a 14-name secondary set, which the archive rule exists to prevent.
- **aster_etf_interval1_m150 / MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores)**: Missing input: primary daily history of at least 252 sessions for the 13 non-QQQ universe names (SPY, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLV, XLY at 179-180 served; SMH and XLU absent)
- **aster_etf_interval1_m150 / provider_eligibility_agreement (INTERVAL select: set(other)==set(own))**: Stated-logic rule; dropping it would let the sleeve select on a one-name primary set against a 14-name secondary set, which the archive rule exists to prevent.
- **aster_etf_interval_core25_c098 / MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores)**: Missing input: primary daily history of at least 252 sessions for the 13 non-QQQ universe names (SPY, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLV, XLY at 179-180 served; SMH and XLU absent)
- **aster_etf_interval_core25_c098 / provider_eligibility_agreement (INTERVAL select: set(other)==set(own))**: Stated-logic rule; dropping it would let the sleeve select on a one-name primary set against a 14-name secondary set, which the archive rule exists to prevent.
- **aster_etf_interval_core25_m150 / MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores)**: Missing input: primary daily history of at least 252 sessions for the 13 non-QQQ universe names (SPY, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLV, XLY at 179-180 served; SMH and XLU absent)
- **aster_etf_interval_core25_m150 / provider_eligibility_agreement (INTERVAL select: set(other)==set(own))**: Stated-logic rule; dropping it would let the sleeve select on a one-name primary set against a 14-name secondary set, which the archive rule exists to prevent.
- **aster_etf_interval_drift1_c098 / MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores)**: Missing input: primary daily history of at least 252 sessions for the 13 non-QQQ universe names (SPY, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLV, XLY at 179-180 served; SMH and XLU absent)
- **aster_etf_interval_drift1_c098 / provider_eligibility_agreement (INTERVAL select: set(other)==set(own))**: Stated-logic rule; dropping it would let the sleeve select on a one-name primary set against a 14-name secondary set, which the archive rule exists to prevent.
- **aster_etf_interval_drift1_m150 / MIN_SESSIONS=252 on primary bars (desk3/aster_etf_b9.py _scores)**: Missing input: primary daily history of at least 252 sessions for the 13 non-QQQ universe names (SPY, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLV, XLY at 179-180 served; SMH and XLU absent)
- **aster_etf_interval_drift1_m150 / provider_eligibility_agreement (INTERVAL select: set(other)==set(own))**: Stated-logic rule; dropping it would let the sleeve select on a one-name primary set against a 14-name secondary set, which the archive rule exists to prevent.
- **aster_etf_smh_hold_c098 / SMH 252-session primary history (desk3/aster_etf.py _scores eligibility)**: Missing input: SMH daily bars in the primary bars cache (0 rows served; 501 sessions exist only in bars_secondary)
- **aster_etf_smh_hold_m150 / SMH 252-session primary history (desk3/aster_etf.py _scores eligibility)**: Missing input: SMH daily bars in the primary bars cache (0 rows served; 501 sessions exist only in bars_secondary)

## CLASS: MN-NO-REBALANCE (9 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| s_mn_d_green_band | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_d_green_band | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_hedge | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_hedge | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_hourly | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_hourly | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_nostop | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_nostop | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_opt_pairs | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_opt_pairs | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_opt_reversal | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_opt_reversal | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_w_cyan_breadth | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_w_cyan_breadth | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_w_cyan_vix | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_w_cyan_vix | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |
| s_mn_w_green_smh | kronos_forecast_history (the sleeve own forecast feed) | 0 | n/a | UNFED |
| s_mn_w_green_smh | qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds) | 0 | n/a | LOAD-BEARING |

Gate notes:

- **s_mn_d_green_band / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_d_green_band / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_hedge / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_hedge / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_hourly / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_hourly / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_nostop / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_nostop / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_opt_pairs / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_opt_pairs / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_opt_reversal / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_opt_reversal / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_w_cyan_breadth / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_w_cyan_breadth / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_w_cyan_vix / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_w_cyan_vix / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).
- **s_mn_w_green_smh / kronos_forecast_history (the sleeve own forecast feed)**: Missing input: archived Kronos MN forecast fires (the sleeve own forecast history)
- **s_mn_w_green_smh / qualifying_rebalance_event (sleeve rebalance/min-hold/band thresholds)**: Classified load-bearing on substitute-feed evidence only; the Kronos-feed test does not exist on this machine (row above).

## CLASS: RSI2-NO-RECOVERY (9 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| aster_pub_rsi2_ada | ADA/USD 1Hour bar series (evaluate_rsi2 reads _bars(view, "1Hour")) | 0 | n/a | UNFED |
| aster_pub_rsi2_ada | decision_window_300s_after_completed_1h_bar | 0 | n/a | LOAD-BEARING |
| aster_rec_rsi2_long_fixed_a | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_long_fixed_a | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |
| aster_rec_rsi2_long_fixed_b | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_long_fixed_b | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |
| aster_rec_rsi2_long_touch_a | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_long_touch_a | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |
| aster_rec_rsi2_long_touch_b | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_long_touch_b | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_fixed_a | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_fixed_a | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_fixed_b | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_fixed_b | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_touch_a | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_touch_a | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_touch_b | native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars) | 0 | n/a | UNFED |
| aster_rec_rsi2_vertical_touch_b | options_chain_for_recovery_expression (book DTE/delta/premium caps) | 0 | n/a | UNFED |

Gate notes:

- **aster_pub_rsi2_ada / ADA/USD 1Hour bar series (evaluate_rsi2 reads _bars(view, "1Hour"))**: Missing input: ADA/USD 1Hour bars (the sleeve native frame); the box holds PF_ADAUSD 4Hour only
- **aster_pub_rsi2_ada / decision_window_300s_after_completed_1h_bar**: Archive rule as written; whether it is mispriced cannot be tested until the 1Hour tape exists.
- **aster_rec_rsi2_long_fixed_a / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_long_fixed_a / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands
- **aster_rec_rsi2_long_fixed_b / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_long_fixed_b / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands
- **aster_rec_rsi2_long_touch_a / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_long_touch_a / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands
- **aster_rec_rsi2_long_touch_b / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_long_touch_b / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands
- **aster_rec_rsi2_vertical_fixed_a / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_vertical_fixed_a / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands
- **aster_rec_rsi2_vertical_fixed_b / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_vertical_fixed_b / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands
- **aster_rec_rsi2_vertical_touch_a / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_vertical_touch_a / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands
- **aster_rec_rsi2_vertical_touch_b / native_bar_envelope (session / complete / usable_after stamps on IWM/QQQ/SPY bars)**: Missing input: native-session-stamped bars (session, complete, usable_after fields) for IWM/QQQ/SPY in the replay cache, and at least 200 sessions of SPY and IWM daily history (180 served)
- **aster_rec_rsi2_vertical_touch_b / options_chain_for_recovery_expression (book DTE/delta/premium caps)**: Missing input: historical options chains/quotes for IWM/QQQ/SPY at the book DTE and delta bands

## CLASS: TIMING-STREAM (8 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| aster_r19_timing_cloud_aggressive | 10Min bar series (>=30 bars) and 1Hour (>=53) for cloud_signal | 0 | n/a | UNFED |
| aster_r19_timing_cloud_base | 10Min bar series (>=30 bars) and 1Hour (>=53) for cloud_signal | 0 | n/a | UNFED |
| aster_r19_timing_hour_floor0_delay0 | timing_signals_history (v625 swing report series) | 0 | n/a | UNFED |
| aster_r19_timing_hour_floor0_delay0 | actionable_window_5min_after_actionable_at (15min with enhance grace) | 0 | n/a | LOAD-BEARING |
| aster_r19_timing_hour_floor0_delay1 | timing_signals_history (v625 swing report series) | 0 | n/a | UNFED |
| aster_r19_timing_hour_floor0_delay1 | actionable_window_5min_after_actionable_at (15min with enhance grace) | 0 | n/a | LOAD-BEARING |
| aster_r19_timing_hour_floor1_delay0 | timing_signals_history (v625 swing report series) | 0 | n/a | UNFED |
| aster_r19_timing_hour_floor1_delay0 | actionable_window_5min_after_actionable_at (15min with enhance grace) | 0 | n/a | LOAD-BEARING |
| aster_r19_timing_hour_floor1_delay1 | timing_signals_history (v625 swing report series) | 0 | n/a | UNFED |
| aster_r19_timing_hour_floor1_delay1 | actionable_window_5min_after_actionable_at (15min with enhance grace) | 0 | n/a | LOAD-BEARING |
| aster_r19_timing_overnight_25bp | 30Min bar series (>=252 bars) for overnight_signal | 0 | n/a | UNFED |
| aster_r19_timing_overnight_5bp | 30Min bar series (>=252 bars) for overnight_signal | 0 | n/a | UNFED |

Gate notes:

- **aster_r19_timing_cloud_aggressive / 10Min bar series (>=30 bars) and 1Hour (>=53) for cloud_signal**: Missing input: 10Min bars for the UNIVERSE42 names (no 10Min series exists in any cache on this machine)
- **aster_r19_timing_cloud_base / 10Min bar series (>=30 bars) and 1Hour (>=53) for cloud_signal**: Missing input: 10Min bars for the UNIVERSE42 names (no 10Min series exists in any cache on this machine)
- **aster_r19_timing_hour_floor0_delay0 / timing_signals_history (v625 swing report series)**: Missing input: a historical timing_signals series (daily v625 swing reports per symbol) for any replay window; only the 2026-11-14 snapshot exists
- **aster_r19_timing_hour_floor0_delay0 / actionable_window_5min_after_actionable_at (15min with enhance grace)**: Archive clock rule as written; mispricing cannot be tested until a signals series exists.
- **aster_r19_timing_hour_floor0_delay1 / timing_signals_history (v625 swing report series)**: Missing input: a historical timing_signals series (daily v625 swing reports per symbol) for any replay window; only the 2026-11-14 snapshot exists
- **aster_r19_timing_hour_floor0_delay1 / actionable_window_5min_after_actionable_at (15min with enhance grace)**: Archive clock rule as written; mispricing cannot be tested until a signals series exists.
- **aster_r19_timing_hour_floor1_delay0 / timing_signals_history (v625 swing report series)**: Missing input: a historical timing_signals series (daily v625 swing reports per symbol) for any replay window; only the 2026-11-14 snapshot exists
- **aster_r19_timing_hour_floor1_delay0 / actionable_window_5min_after_actionable_at (15min with enhance grace)**: Archive clock rule as written; mispricing cannot be tested until a signals series exists.
- **aster_r19_timing_hour_floor1_delay1 / timing_signals_history (v625 swing report series)**: Missing input: a historical timing_signals series (daily v625 swing reports per symbol) for any replay window; only the 2026-11-14 snapshot exists
- **aster_r19_timing_hour_floor1_delay1 / actionable_window_5min_after_actionable_at (15min with enhance grace)**: Archive clock rule as written; mispricing cannot be tested until a signals series exists.
- **aster_r19_timing_overnight_25bp / 30Min bar series (>=252 bars) for overnight_signal**: Missing input: 30Min bars for the UNIVERSE42 names (no 30Min series exists in any cache on this machine)
- **aster_r19_timing_overnight_5bp / 30Min bar series (>=252 bars) for overnight_signal**: Missing input: 30Min bars for the UNIVERSE42 names (no 30Min series exists in any cache on this machine)

## CLASS: REAL-RULE-SPARSE (3 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| rule_1d_green_tom | disp_band [0.02076, 0.02862] (rule V4-1D-GREEN-RAW condition) | 0 | n/a | LOAD-BEARING |
| rule_1w_swing_beta_wt | ribbons >= 0.0094819 (rule V2-1W-SWING condition) | 0 | n/a | LOAD-BEARING |
| rule_1h_cyan_raw | smhUp == 1 (SMH weekly uptrend, from the 1H scorer drop) | 0 | 17 | UNFED |
| rule_1h_cyan_raw | rangeatr >= 2.05 and wtgap >= 6.88 | 0 | n/a | LOAD-BEARING |

Gate notes:

- **rule_1d_green_tom / disp_band [0.02076, 0.02862] (rule V4-1D-GREEN-RAW condition)**: The band is a defining condition of the mined rule (tier A, extracted verbatim); dropping it manufactures a different rule. Classified load-bearing under the stated-logic clause, with the occurrence count printed.
- **rule_1w_swing_beta_wt / ribbons >= 0.0094819 (rule V2-1W-SWING condition)**: Defining condition of the extracted rule; classified load-bearing under the stated-logic clause, with occurrence counts printed.
- **rule_1h_cyan_raw / smhUp == 1 (SMH weekly uptrend, from the 1H scorer drop)**: Missing input: a varying smhUp series from the 1H scorer: the drop carries smhUp=0 on 189 of 189 fires, so the SMH-weekly-uptrend input does not exist in usable form on this machine
- **rule_1h_cyan_raw / rangeatr >= 2.05 and wtgap >= 6.88**: Defining conditions of the extracted rule; not individually binding on the served fire set.

## CLASS: BARS-ONLY-SINGLES (46 SLEEVES)

| sleeve | gate | before | after | classification |
|---|---|---|---|---|
| 1h | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| 1h | drop drop_qqq_down | 0 | 0 | LOAD-BEARING |
| 1h | drop drop_both_red | 0 | 0 | LOAD-BEARING |
| aster_native_eth_sma200 | declared_input_series | 0 | n/a | UNFED |
| aster_rec_vwap20_long_fixed_a | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aster_rec_vwap20_long_fixed_b | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aster_rec_vwap20_long_touch_a | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aster_rec_vwap20_long_touch_b | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aster_rec_vwap20_vert_fixed_a | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aster_rec_vwap20_vert_fixed_b | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aster_rec_vwap20_vert_touch_a | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aster_rec_vwap20_vert_touch_b | native_bar_envelope (session / complete / usable_after stamps) | 0 | n/a | UNFED |
| aurelia_gold | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| aurelia_ndx | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| bb_rsi_divergence | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| daily_cyan_gbm | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| donchian_crypto | declared_input_series | 0 | n/a | UNFED |
| earnings_buyback | declared_input_series | 0 | n/a | UNFED |
| free_etf | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| fwd_alpaca_ada_rsi2 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| fwd_alpaca_link_ai_volume | declared_input_series | 0 | n/a | UNFED |
| fwd_coinbase_sma200 | declared_input_series | 0 | n/a | UNFED |
| gate_1h | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| grok_sr_spy | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| leader_d | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| leader_sc | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| legends_ema | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| phoenix | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| przm_fade_edges | declared_input_series | 0 | n/a | UNFED |
| przm_zero | declared_input_series | 0 | n/a | UNFED |
| qullamaggie_paper | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| raschke_pf3 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| raschke_rre | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| s_1wsw_stress | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| s_cl_qm_small | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| saty_day | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| saty_gpt_v02 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| saty_gpt_v03 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| saty_magnum | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| shen_fade | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| snapback | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| soxl_pm_breakout | declared_input_series | 0 | n/a | UNFED |
| teddy_orb_spy | declared_input_series | 0 | n/a | UNFED |
| trullas_v03 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| trullas_v06 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| trullas_v07 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |
| trullas_v08 | entry_conjunction (the sleeve own signal condition, legs in its module) | 0 | n/a | LOAD-BEARING |

Gate notes:

- **1h / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **1h / drop drop_qqq_down**: Drop reveals 0 entries: the dropped filter is not the binding constraint on the served fire pool.
- **1h / drop drop_both_red**: Drop reveals 0 entries: the dropped filter is not the binding constraint on the served fire pool.
- **aster_native_eth_sma200 / declared_input_series**: Missing input: ETH daily spot bars: the replay daily cache (149 symbols) holds no ETH series, and no PF_ETH tape exists in the PF store
- **aster_rec_vwap20_long_fixed_a / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aster_rec_vwap20_long_fixed_b / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aster_rec_vwap20_long_touch_a / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aster_rec_vwap20_long_touch_b / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aster_rec_vwap20_vert_fixed_a / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aster_rec_vwap20_vert_fixed_b / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aster_rec_vwap20_vert_touch_a / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aster_rec_vwap20_vert_touch_b / native_bar_envelope (session / complete / usable_after stamps)**: Missing input: native-session-stamped bars for IWM/QQQ/SPY in the replay cache, plus historical options chains for the book expression
- **aurelia_gold / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **aurelia_ndx / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **bb_rsi_divergence / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **daily_cyan_gbm / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **donchian_crypto / declared_input_series**: Missing input: a crypto daily tape for the sleeve symbols in the replay cache: the PF store holds ADA, LINK and ENJ tapes only
- **earnings_buyback / declared_input_series**: Missing input: a served earnings-date calendar joined to the sleeve universe in replay: the replay view carried an empty earnings map on every eval
- **free_etf / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **fwd_alpaca_ada_rsi2 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **fwd_alpaca_link_ai_volume / declared_input_series**: Missing input: the AI-volume signal series named by the vendor sleeve: no such series exists in any cache or drop on this machine
- **fwd_coinbase_sma200 / declared_input_series**: Missing input: a Coinbase-sourced daily tape in the replay cache for the sleeve symbol: the replay served the generic daily cache only and the sleeve vendor logic found no qualifying series
- **gate_1h / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **grok_sr_spy / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **leader_d / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **leader_sc / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **legends_ema / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **phoenix / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **przm_fade_edges / declared_input_series**: Missing input: the options_chain producer series named in the sleeve own docstring (PRZM recreation spec): no historical options chain archive exists on this machine
- **przm_zero / declared_input_series**: Missing input: the signed PRZM options tape named in the sleeve own docstring (PRZM-TAPE-20261114): no historical options tape exists on this machine
- **qullamaggie_paper / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **raschke_pf3 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **raschke_rre / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **s_1wsw_stress / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **s_cl_qm_small / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **saty_day / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **saty_gpt_v02 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **saty_gpt_v03 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **saty_magnum / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **shen_fade / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **snapback / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **soxl_pm_breakout / declared_input_series**: Missing input: SOXL premarket bars: the hourly cache holds 27 equity/ETF names and no SOXL, and no premarket tape exists in any cache
- **teddy_orb_spy / declared_input_series**: Missing input: SPY opening-range intraday bars (1Min/5Min for the 09:30 opening range): the cache holds SPY 1Hour only
- **trullas_v03 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **trullas_v06 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **trullas_v07 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.
- **trullas_v08 / entry_conjunction (the sleeve own signal condition, legs in its module)**: No separable non-signal gate was found in the module: every leg of the entry condition is a signal leg, and dropping the conjunction manufactures entries that are not the signal. Leg-level occurrence decomposition for this sleeve is named as a remainder in VEIN2-DIG.md.

## REMAINDERS (NAMED, NOT SILENT)

- BARS-ONLY-SINGLES leg-level decomposition: 46 sleeves are attributed at conjunction level (full-span replay, zero eval errors, condition never occurred) plus named UNFED input rows for 17 of them (9 declared-input rows, 8 VWAP20 recovery envelope rows). A per-leg occurrence count for the remaining 29 sleeves' individual signal legs is the next dig on this vein for this class.
- MN single-threshold drops: no per-threshold drop runs exist for the 9 MN sleeves; their rebalance thresholds are classified on substitute-feed evidence with the control sleeve (s_mn_kronos, 26 entries on the identical feed) as the comparison. The Kronos-feed test cannot exist until a forecast history is archived.
- Q07 downstream filters: every per-filter drop for Q07-SMALL and Q07-ML-GATED was run behind an intact upstream refusal (band or alt-tag absence) and revealed 0, so no filter in these classes has an own-stream test on this machine. The first real test arrives with either a small-cap universe in the cache or alt tags stamped on production fires (the F1 probe showed 20 of 21 midlarge sleeves firing once tags exist).
- Funding window: the OKX route reaches back only to 2026-08-10. The funding sleeves' behavior on the 2026-01-14 to 2026-08-09 stretch of their own tapes is still untested; a longer funding history (Coinalyze archive or a venue with deeper history) is the unblocker.
- Tensor grading horizon: revealed-fire grades rest on fwd1 only because the daily cache ends 2026-11-13. The ret60 verdict should be re-read at fwd5 once the cache extends past 2026-11-19; the register rows carry the stamped fire set so the re-grade is a recount, not a rebuild.
- TIMING actionable window: the 5-minute actionable window (15 with enhance grace) is classified load-bearing as written, but its mispricing is untestable until a timing_signals history exists to replay against intraday evaluation clocks.
- Exit-side gates: KG-7 and KG-13 already attributed the exit-profile gates on the streams that exist (stop and horizon variations graded per stream in KG-7-REGISTER.jsonl and KG-13-REGISTER.jsonl). This dig covers entry-side silence; the exit rows of sleeves that remain silent have no stream to grade, which is the same absence recorded in their entry rows.

## CENSUS

Register rows: 421 sleeve-gate pairs in VEIN2-REGISTER.jsonl. By class: BARS-ONLY-SINGLES 47, ETF-B9-ELIGIBILITY 14, FUNDING-GATED-CRYPTO 84, MN-NO-REBALANCE 18, Q07-ML-GATED 34, Q07-SMALL 91, REAL-RULE-SPARSE 4, RSI2-NO-RECOVERY 18, TENSOR-REFUSAL 99, TIMING-STREAM 12. By classification: LOAD-BEARING 289, UNFED 129, MISPRICED 3 (3 rows, 2 distinct streams: the LINK absorption pair shares one stream).

STATUS: PARTIAL. Proven on the final artifacts: the funding class is fully attributed with new engine runs (28 sleeves x 3 gate rows, OKX route), the Tensor refusal is fully decomposed per gate on the re-stamped 42-fire set, and B9, RSI2, TIMING and REAL-RULE are attributed with leg counts computed on the sleeves' own streams; Q07 classes are attributed from the on-disk drop runs plus the F1 probe, and MN on substitute-feed evidence with its control. The bounded remainder is named above: BARS-ONLY-SINGLES is attributed at conjunction level with leg-level decomposition still owed for 29 sleeves, MN has no per-threshold drop runs, Q07 downstream filters have no own-stream test on this machine, the funding diagnostic window starts 2026-08-10, and Tensor revealed-fire grades rest on fwd1 only. Evidence pointer: pass2/VEIN2-REGISTER.jsonl (421 rows, recounted) and pass2/vein2_work/ (driver, fetch, run outputs, counts).
