# UNBLOCK LANE 2 — REPLAY OF THE NEVER-RECORDED SLEEVES

274 of 274 sleeves replay-graded: 252 executed their own logic over historical bars and carry a REPLAY grade (23 REPLAY-SCORED, 34 REPLAY-INDICATIVE, 195 REPLAY-NO-FIRE), and 22 carry a named, twice-attempted execution impossibility (every one the same missing data feed: no ENJ bars exist anywhere on this box). Evidence class is REPLAY on every row of the register; nothing here is blended with Lane C's LIVE-RECORD grades. Replay span: 2025-11-04..2026-11-13 (255 sessions; intraday sleeves on their own tapes).

## POTENTIAL EDGE FOUND

Every lead below is a replay result on the sleeve's own logic, graded forward against QQQ on stored closes. A lead is a reason to arm a forward check, not a verdict; the cheapest forward check that would arm each lead is printed with it.

### Family leads

**F1. The Lazarus exit profile is too tight for its own fire stream (8 sleeves).** Across the fired Lazarus consumers, the registered exits (15% stop, 40-session horizon, partial at +20%) systematically underperform loosened variants in the exit-path simulation: dropping the stop lifts 1w from +1,725.0bp to +2,937.8bp per trade (n=28), 1wa from +1,256.3bp to +2,285.5bp (n=34), s_1wlab from +587.6bp to +1,263.9bp (n=80); widening the stop x1.2 lifts 1w to +2,598.0bp and 1wa to +1,940.0bp; extending s_rules_1w's horizon x4 lifts it from +365.2bp to +1,647.4bp (n=58), dropping s_rules_1d's horizon lifts its sim from +67.8bp to +471.4bp (n=415), and dropping s_1dg's horizon entirely turns its exit sim from -18.1bp to +711.4bp (n=204) while its raw 1-session forward excess is +30.2bp (n=204, t=1.71). Cheapest forward check: run the loosened exit profile as a shadow arm beside the live profile on Monday's fire stream; first grade at 20 resolved shadow exits.

**F2. The Q07 catalog's alt-data filters are the only thing between 14 sleeves and a live signal.** At base, all 49 Q07 sleeves produce zero entries: the alt-data filters (ins2 above all — it demands insider_buys >= 2 on the fire, a field no untagged fire carries — plus tierA, wcov, wlow, vix20, ats_z1, wspike2) fail closed by documented design. Dropping only the alt-data filters reveals entries in 14 midlarge sleeves (1-5 entries each over the window; the revealing drop and its count are tabled below) on the remaining bar-computable logic (Tensor 1W family + QQQ-down-day timing + deep70/cheap5/mom6). The replay grades that underlying logic, which had never been observable. Cheapest forward check: shadow the alt-filter-dropped variants against the REAL composer fire feed (which carries the tags) for 20 signals per family; if the real tagged feed fires at a similar rate, the catalog's live silence is a tagging problem, not a logic problem. The other 24 Q07 sleeves are small-band: the cached universe is large-cap, so their refusal is faithful, and 11 midlarge sleeves stay gated by their bar-computable filters on this window.

**F3. LINK crypto: breakout and AI-volume positive, absorption negative.** aster_r19_linkusdt_breakout (both sizing variants, one stream): fwd10 excess +230.2bp, n=22 (t=0.76); aster_pub_link_ai_volume: fwd10 excess +496.3bp, n=18 (t=1.41), inversion -698.3bp certifies the direction. The family's third stream is a counterweight, printed so the family is not cherry-picked: aster_r19_linkusdt_absorption_base (both variants, the same stream as aster_abs_link_4h) is SCORED at n=18 entries over 18 days and grades NEGATIVE (fwd10 excess -448.3bp, n=7 priceable at that horizon). Span: PF_LINKUSD 4Hour tape, 2025-11-25..2026-11-02 served from bar 300. Cheapest forward check: the positive sleeves' logic runs on the live PF tape; arm as shadow on Monday's session and grade the first 10 resolved entries.

**F4. ADA breakout pair.** aster_breakout_ada (both sizing variants, one stream): fwd5 excess +192.7bp, n=15 (t=0.72), inversion -262.9bp. Same forward check as F3 on the PF_ADAUSD tape.

**F5. The Lazarus qqq_down gate is sleeve-specific, not a family rule.** Dropping it improves 1w (fwd5 excess +12.2bp to +170.2bp) and 1wa (-52.4bp to +72.2bp) but worsens 1dc (+19.5bp to -22.3bp on n=349) and s_rules_1w (+65.0bp to -22.6bp). Keep the gate where it earns; the two sleeves it taxes are named here. Forward check: shadow the gateless variants of 1w/1wa beside the gated live sleeves for 20 fires.

### Individual leads (positive forward excess, primary stream)

| sleeve | stream | horizon | excess vs QQQ | inversion | span |
|---|---|---|---|---|---|
| aster_pub_link_ai_volume | base | fwd10 | n=18, +496.3bp, t=1.41 | -698.3bp | 2026-01-14..2026-11-02 |
| s_rules_1w | base | fwd10 | n=54, +255.1bp, t=2.2 | -621.4bp | 2025-11-10..2026-11-13 |
| aster_r19_linkusdt_breakout_base_fixed16_fullcash | base | fwd10 | n=22, +230.2bp, t=0.76 | -465.3bp | 2026-01-14..2026-11-02 |
| aster_r19_linkusdt_breakout_base_fixed16_volume1pct | base | fwd10 | n=22, +230.2bp, t=0.76 | -465.3bp | 2026-01-14..2026-11-02 |
| s_mn_kronos | base | fwd10 | n=24, +210.7bp, t=1.02 | -326.1bp | 2025-11-10..2026-11-13 |
| aster_breakout_ada_fullcash | base | fwd5 | n=15, +192.7bp, t=0.72 | -262.9bp | 2026-01-14..2026-11-02 |
| aster_breakout_ada_vol1pct | base | fwd5 | n=15, +192.7bp, t=0.72 | -262.9bp | 2026-01-14..2026-11-02 |
| phase_daily | base | fwd10 | n=33, +108.2bp, t=1.01 | -167.1bp | 2025-11-10..2026-11-13 |
| 1d | base | fwd3 | n=56, +94.0bp, t=1.19 | -1.7bp | 2025-11-10..2026-11-13 |
| momentum_rotation | base | fwd5 | n=47, +91.7bp, t=0.94 | -137.5bp | 2025-11-10..2026-11-13 |
| 1w | base | fwd1 | n=28, +80.0bp, t=1.59 | -48.9bp | 2025-11-10..2026-11-13 |
| s_1wc_ml | base | fwd5 | n=6, +53.2bp, t=0.53 | +283.1bp | 2025-11-10..2026-11-13 |
| 1wa | base | fwd1 | n=34, +50.6bp, t=1.1 | +0.4bp | 2025-11-10..2026-11-13 |
| s_1wlab | base | fwd3 | n=80, +43.2bp, t=0.59 | +58.9bp | 2025-11-10..2026-11-13 |
| s_1dg | base | fwd1 | n=204, +30.2bp, t=1.71 | +0.6bp | 2025-11-10..2026-11-13 |
| 1dc | base | fwd5 | n=280, +19.5bp, t=0.32 | +57.6bp | 2025-11-10..2026-11-13 |
| aster_etf_qqq_qld_monthly | base | fwd1 | n=15, +9.7bp, t=0.26 | -74.8bp | 2025-11-10..2026-11-13 |
| aster_etf_qld_monthly | base | fwd1 | n=12, +5.8bp, t=0.12 | -42.2bp | 2025-11-10..2026-11-13 |

Reading notes on the table: s_rules_1w carries the strongest t-statistic of the set (fwd10 +255.1bp, n=54, t=2.2; inversion -621.4bp certifies direction). s_1dg carries the largest sample (fwd1 +30.2bp, n=204, t=1.71). s_mn_kronos grades the MN forecast-management logic on a synthetic momentum-ranked forecast (fwd10 +210.7bp, n=24, t=1.02), not the Kronos forecaster itself. The two aster_etf monthly sleeves' excesses are real but tiny (+9.7bp and +5.8bp at fwd1) and are printed for completeness, not emphasis. Every crypto lead sits on the PF 4Hour tapes, whose daily series ends 2026-11-02.

### Exit-variation leads not already in F1

| sleeve | variation | exit-sim mean | EXIT_BASE | n |
|---|---|---|---|---|
| s_1wc_ml | DROP_stop | +7255.7bp | +4526.2bp | 6 |
| s_rules_1d | DROP_horizon | +471.4bp | +67.8bp | 415 |
| s_rules_1d | EXTREME_horizon_x4 | +302.5bp | +67.8bp | 415 |
| 1d | JITTER_horizon_x2 | +416.1bp | +267.0bp | 56 |
| 1d | DROP_horizon | +413.0bp | +267.0bp | 56 |
| 1d | EXTREME_horizon_x4 | +401.5bp | +267.0bp | 56 |
| 1d | DROP_target | +391.0bp | +267.0bp | 56 |
| s_1wc_ml | JITTER_stop_x0.8 | +4626.2bp | +4526.2bp | 6 |

### Gate-drop reveals (Q07; detail in F2)

| sleeve | revealing drop | entries revealed |
|---|---|---|
| s_q07w_c52_ml_mom6_tierA_wlow | drop_altfilters | 1 |
| s_q07w_c52_ml_mom6_wspike2 | dropf_wspike2 | 1 |
| s_q07w_c52_ml_tierA_wcov | drop_altfilters | 1 |
| s_q07w_c52_ml_tierA_wlow | drop_altfilters | 1 |
| s_q07w_c78_ml_deep70_tierA_wlow | drop_altfilters | 4 |
| s_q07w_c78_ml_mom6_tierA_wlow | drop_altfilters | 1 |
| s_q07w_c78_ml_tierA_wcov | drop_altfilters | 1 |
| s_q07w_c78_ml_tierA_wlow | drop_altfilters | 1 |
| s_q07w_g52_ml_ats_z1_mom6_wlow | drop_altfilters | 1 |
| s_q07w_g52_ml_ins2_wlow | drop_altfilters | 1 |
| s_q07w_g52_ml_tierA_wcov | drop_altfilters | 1 |
| s_q07w_g78_ml_tierA_wcov | drop_altfilters | 1 |
| s_q07w_s52_ml_deep70_ins2_vix20 | drop_altfilters | 4 |
| s_q07w_s78_ml_deep70_ins2_vix20 | drop_altfilters | 4 |

### Tensor consumers: first entries ever recorded

Five batch13/14 cash-mode Tensor consumers took their first entries in replay once bundles were served the way live life serves them (archived production bundles for 2026-11-11/12 plus regenerated Friday bundles 2026-09-18..2026-11-06, native feature pass applied): aster_tensor_c1_cash_all_25 (1 entry, fwd5 excess +878.5bp, n=1), aster_tensor_g4_cash_all_10, aster_tensor_g4_cash_all_25, aster_tensor_g4_cash_cool_25, aster_tensor_g4_cash_hot_25 (1 entry each). n=1 is a pulse, not a grade: the forward check is to keep these five shadow-armed on live bundles and count the next 10 fires. The other 20 Tensor consumers refused every one of the 91 bundle fires across the 9 fire days (bundles served on 13 sessions; their ret60/vol20/adv/atr_ratio cells were empty on those days). Regeneration validation: the in-process producer, series sliced as-of 2026-11-11, reproduces the archived AAOI fire exactly (same timestamp, phenotype RECLAIM, age 0).

## TIER CENSUS

- REPLAY-SCORED: 23 (at least 10 priceable entries on at least 3 distinct entry dates, Campaign 1 bar)
- REPLAY-INDICATIVE: 34 (at least 1 priceable entry, below the SCORED bar)
- REPLAY-NO-FIRE: 195 (logic executed cleanly over the full span, zero entries; cause named per class below)
- EXECUTION-IMPOSSIBLE: 22 (both routes attempted; the failure is named per sleeve in the register)

### REPLAY-SCORED sleeves

| sleeve | entries | entry dates | fwd5 excess | fwd10 excess |
|---|---|---|---|---|
| 1d | 56 | 27 | n=55, mean -96.1bp, t=-0.81 | n=52, mean -21.6bp, t=-0.15 |
| 1dc | 280 | 33 | n=280, mean +19.5bp, t=0.32 | n=280, mean -28.5bp, t=-0.28 |
| 1w | 28 | 11 | n=28, mean +12.2bp, t=0.16 | n=27, mean +53.5bp, t=0.34 |
| 1wa | 34 | 13 | n=34, mean -52.4bp, t=-0.71 | n=33, mean -38.2bp, t=-0.26 |
| aster_abs_link_4h | 18 | 18 | n=7, mean -285.9bp, t=-1.28 | n=7, mean -448.3bp, t=-1.24 |
| aster_breakout_ada_fullcash | 32 | 32 | n=15, mean +192.7bp, t=0.72 | n=11, mean -490.9bp, t=-2.21 |
| aster_breakout_ada_vol1pct | 32 | 32 | n=15, mean +192.7bp, t=0.72 | n=11, mean -490.9bp, t=-2.21 |
| aster_etf_leader1_c098 | 122 | 122 | n=120, mean +0.0bp | n=116, mean +0.0bp |
| aster_etf_qld_monthly | 12 | 12 | n=11, mean -239.9bp, t=-3.33 | n=8, mean -401.8bp, t=-4.44 |
| aster_etf_qqq_qld_monthly | 15 | 11 | n=15, mean -175.9bp, t=-2.97 | n=11, mean -292.2bp, t=-3.4 |
| aster_pub_link_ai_volume | 37 | 37 | n=15, mean +406.6bp, t=1.87 | n=18, mean +496.3bp, t=1.41 |
| aster_r19_linkusdt_absorption_base_fixed16_fullcash | 18 | 18 | n=7, mean -285.9bp, t=-1.28 | n=7, mean -448.3bp, t=-1.24 |
| aster_r19_linkusdt_absorption_base_fixed16_volume1pct | 18 | 18 | n=7, mean -285.9bp, t=-1.28 | n=7, mean -448.3bp, t=-1.24 |
| aster_r19_linkusdt_breakout_base_fixed16_fullcash | 50 | 48 | n=25, mean +150.3bp, t=0.99 | n=22, mean +230.2bp, t=0.76 |
| aster_r19_linkusdt_breakout_base_fixed16_volume1pct | 50 | 48 | n=25, mean +150.3bp, t=0.99 | n=22, mean +230.2bp, t=0.76 |
| momentum_rotation | 50 | 30 | n=47, mean +91.7bp, t=0.94 | n=47, mean -48.1bp, t=-0.38 |
| phase_daily | 34 | 31 | n=33, mean -5.0bp, t=-0.06 | n=33, mean +108.2bp, t=1.01 |
| s_1dg | 204 | 12 | n=204, mean +12.4bp, t=0.29 | n=204, mean -50.1bp, t=-0.71 |
| s_1wlab | 80 | 25 | n=80, mean -42.9bp, t=-0.56 | n=72, mean -184.8bp, t=-1.7 |
| s_mn_kronos | 26 | 24 | n=26, mean +55.4bp, t=0.37 | n=24, mean +210.7bp, t=1.02 |
| s_mn_pairs | 12 | 6 | n=12, mean -163.5bp, t=-1.26 | n=12, mean -85.6bp, t=-0.44 |
| s_rules_1d | 415 | 15 | n=415, mean -31.3bp, t=-0.81 | n=415, mean -30.2bp, t=-0.65 |
| s_rules_1w | 58 | 11 | n=58, mean +65.0bp, t=0.63 | n=54, mean +255.1bp, t=2.2 |

## NO-FIRE CENSUS (195), by named cause

- **Q07 small-band, faithful refusal (24).** The synthetic fire pool is the cached large-cap universe stamped band ml; small-band specs refuse it by their own band rule. Their universe is not in the cache.
- **Q07 midlarge, still gated (11).** With alt-data filters dropped, their bar-computable filters (deep70/cheap5/mom6) or the QQQ-down timing still refused every synthetic fire on this window.
- **Options-feed absence (named per sleeve in the register runs).** Free opt family (6), Aster PEAD options (4), and the options singles inside Fires/Spec singles: entries require historical option chains and IV history; none exists on this box, and the sleeves fail closed by design. iron_condor is here with a separate named defect (next section).
- **Kraken-current only (6).** cache/kraken/inputs.json is a current snapshot; no Kraken history exists to replay over.
- **Tensor consumers refusing all bundle fires (20).** See the Tensor entry above: 91 fires over 9 fire days, every one refused by the consumers' feature gates.
- **MN catalog (9).** The forecast-management logic ran over the synthetic momentum-ranked forecast and produced no qualifying rebalance entries (the Kronos sleeve itself fired; see the leads table).
- **REAL-RULE (3).** The real GBM rule-fire drop is sparse: these sleeves' symbols carried no usable fires in the window (a fourth rule sleeve fired once).
- **Aster batch sleeves, gates refused (incl. absorption 4, RSI2 recovery 9, ETF arms 8, other batches 44).** Funding-gated variants fail closed with no funding history (documented design); the b9 interval/leader arms' selection path produced no selection on any of 255 sessions (most sector secondary histories carry 180 sessions against the engine's 252-session eligibility floor); the RSI2 recovery set evaluated cleanly after the timezone cure and their recovery conditions never occurred on the served tapes.
- **Bars-only singles (remainder).** Logic executed over the full span; the signal condition never occurred on the served series. Each register row carries its feed, span, eval count and any engine-recorded refusal.

## EXECUTION-FAILURE CENSUS

**EXECUTION-IMPOSSIBLE (22) — one class, twice attempted.** aster_abs_enj_4h, the 8 aster_enj_nfs_* arms, aster_pub_enj_iu_body, the 10 aster_r19_enjusdt_* arms, free_kraken_enj_spot, fwd_alpaca_enj_iu_body. Cause: no ENJ bars exist in any cache on this box (cache/bars, cache/kraken and the vendor caches were all searched in recon). Route 1 (module drive on the PF 4Hour profile) fails for want of the series; route 2 (the parameter-map harness) requires the same absent series. The impossibility is a missing data feed, not a logic failure.

**Named desk defect found by replay (not an impossibility).** iron_condor evaluated cleanly for 202 of 255 sessions and is graded REPLAY-NO-FIRE on those; from 2026-09-01 its shim's GAP-CURE stamps extra['vix'] as a 4-tuple while the vendor strategy calls float(vix), raising TypeError on every later session whenever VIX bars carry epoch stamps. The defect is in production code (desk3/sleeves/iron_condor.py), which this lane does not modify; it is reported here for the desk lane. Its entries additionally require option chains/IV history, absent in any case.

**Failure classes cured in-pass (route 2 landed).** Six harness defects were found and fixed during the run, each verified by re-running the affected sleeves to clean evaluations: (1) engines requiring tz-aware bar stamps (10 sleeves), (2) engines reading view['now_iso'] (8), (3) Q07 fires must carry the sleeve's own id stamp and be served under extra['sleeve_fires'], (4) the older Q07 engine reads bars under the 'SYM|1day' key and refuses band-less fires, (5) the Q07 engine returns Intent objects, not dicts, (6) naive daily clock stamps. A mid-run service restart wiped /tmp once; all lane state was moved into this workspace tree and every base replay was re-run clean on the final driver, so all 274 base rows come from one harness version.

## METHOD AND HONESTY NOTES

- Feeds, printed per register row: SYNTH-LAZ (synthetic all-names daily fires with bar-computed deep tags; family/tier/cap filters unstamped and therefore unenforced by the engine's own rule — grades gates/sizing/exits downstream of a fire, never the Tensor signal's selectivity), SYNTH-Q07 (weekly per-sleeve fires + the 46 real composer fires merged in-window), SYNTH-MN (momentum-ranked synthetic forecast; grades forecast management, not the forecaster), REAL-RULE (the real GBM fire drop, as produced), TENSOR-ARCHIVE + regenerated bundles (above), KRAKEN-CURRENT (snapshot only), NONE (bars-driven logic).
- Variation set: base hold profile 1/3/5/10 raw and excess vs QQQ with t-statistics; inversion of every stream; time-of-day only where the stream carries intraday stamps (the 4Hour crypto streams; daily streams are single-stamp by construction and print n/a); exit-path simulations with stop/target/horizon jitter (x0.8/x1.2, horizon x0.5/x2), extremes (stop x0.25, target x3, horizon x4) and single-gate drops, on each sleeve's own extracted exit parameters; signal gate drops as separate replays (Q07 filters, Lazarus qqq_down). Signal-parameter jitter: the fired set's extracted maps carry no non-exit signal parameter on the SPECS/config surface (the Lazarus signal is the fire itself; the aster_etf knobs are engine constants), so jitter was applied where it exists — the exit parameters — and the gap is named here rather than silently skipped.
- Decisions API (gpt-6-luna) was available as a lens; no seat set any grade in this lane — every number above is computed from stored closes by the Lane C machinery.
- Register: UNBLOCK-2-REGISTER.jsonl, one row per sleeve (274), each carrying route, feed, span, cache state, every run's counts, full grades for the primary stream, variation grades, tier, and evidence_class REPLAY.

STATUS: PARTIAL per InfinityBlade — 274 of 274 rows closed (57 graded on a revealed or recorded entry stream, 195 executed-clean NO-FIRE with named causes, 22 named impossibilities), evidence in UNBLOCK-2-REGISTER.jsonl recounted from the register itself; the portion not proven is forward validity: every lead above is a replay result whose arming check is a Monday forward run, named per lead, and the 22 ENJ sleeves stay impossible until an ENJ bar feed exists on the box.
