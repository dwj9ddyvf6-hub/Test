# UNBLOCK LANE 1: REPRICE ON THE WIDENED CACHE, EXIT-ONLY RECONSTRUCTION, AND THE FULL SLEEVE CENSUS

17 sleeves are newly graded in this lane (12 SCORED, 5 INDICATIVE), on a bar cache widened from 51 to 154 symbols (103 symbols added: 85 equities, 19 option contracts, and the crypto pairs, with ENJ/USD returning zero bars from Alpaca), the newly fetched equity series carrying 53 daily bars each spanning 2026-09-01 to 2026-11-13, and stored benchmark series such as SPY extended past their old 2026-10-31 end to 2026-11-13.

Register: UNBLOCK-1-REGISTER.jsonl, 60 rows. Every number below is read from that register, from Lane C's register (PASS2-C-REGISTER.jsonl), from Unblock Lane 2's register, from KG-6's register, or from this lane's work files in work/unblock1/ (cache_census.json, fetch_census.json, reprice_results.json, null_extension_results.json, reconstruction_results.json). Evidence class for everything in sections 1 to 5 is LIVE-RECORD (the sleeves' own recorded fills), except the exit-only reconstruction in section 4, whose basis is stated on its face.

## What the lane did

- Cache widening: 51 to 154 symbols. 104 series were mirrored from stored bars and 103 symbols are new (fetch census: 85 equities, 19 OCC option contracts, crypto attempted for 6 pairs; ADA/USD, BTC/USD and LINK/USD were already held as perp series and skipped for mirroring). ENJ/USD returned zero bars on this route; the 22 ENJ sleeves were later graded by KG-6 on the Kraken route (see the census, section 6).
- Reprice: 42 sleeves were repriced on the widened cache (reprice_results.json). 36 of them carry entries in the register and reprice 6,688 recorded entries, 6,688 priceable forward on the widened cache. 18 were already graded by Lane C and are re-based here; 6 more (aster_core_rsi2_long, aster_core_rsi2_vertical, bta_onebar_qqq, bta_onebar_rth, morning_dip, s_cl_vmr_qqq) were repriced in the lane's work and kept their Lane C INDICATIVE tiers unchanged, so they do not appear in the register.
- Full-record extension: Lane C's loader had dropped unstamped recorded buys. Restoring them adds 548 buys to aster_native_btc_eth_sma200 (26 stamped entries become 574), 145 to tensor_swing (3,633 become 3,778), and 1 each to red_day_reversal (164 become 165) and aster_abs_base_ada_fullcash (0 become 1). Full-record profiles are printed where they differ from the stamped basis.
- Broker pull for the exit-only attack: the complete broker order history, 8,961 filled or partially filled orders spanning 2026-10-20 to 2026-11-15, with 0 of the 7,678 dispatcher-referenced fill order ids missing from the pull.

## POTENTIAL EDGE FOUND

Each lead carries its numbers and the cheapest forward check that would arm it. Forward accrual below means the forward stream on the cured intent records from Mon 2026-11-16, graded on the same hold profile.

1. **aster_trader_donchian55 (newly SCORED; 42 entries, 3 entry dates).** Positive at every horizon: fwd1 +126.0bp (excess +287.6), fwd3 +1,621.7 (excess +2,171.6), fwd5 +2,166.0 (excess +2,739.2), fwd10 +1,659.3 (excess +2,132.1), all n=42; the inversion reads −2,166.0 at fwd5, certifying direction. Limit: 3 entry dates, so the 42 fills are 3 clusters. Cheapest forward check: grade its next 10 forward fires on this profile; the lead dies if forward fwd5 excess is not positive.
2. **The Tensor D20 pair (both newly SCORED).** aster_tensor_d20_tensor: 684 entries, 7 dates, fwd1 +560.7 (excess +413.0), fwd3 +713.8 (excess +364.8), fwd5 +753.1 (excess +240.6, n=463). aster_tensor_d20_pv: 420 entries, 7 dates, fwd1 +570.3 (excess +443.0), fwd5 +641.1 (excess +157.8, n=267). Pooled unit (1,104 entries): fwd1 +564.3 (excess +424.4), fwd5 +712.2 (excess +210.3). These are the sleeves Lane C could not price at all (684 entries on uncached names was the single largest block in the population). Cheapest forward check: the first 20 forward fires per sleeve on this profile, plus the night-1-only shadow exit KG-4's phase shape predicts for Tensor.
3. **aster_etf_leader1_m150 (newly SCORED; 18 entries, 8 dates).** A rising profile: fwd1 +59.9 (excess +78.5), fwd3 +287.0 (excess +212.2, n=10), fwd5 +768.0 (excess +749.3, n=8), fwd10 +2,192.8 (excess +2,530.8, n=2). Time-of-day split at fwd5: AM +1,471.9 (n=4) against PM +64.1 (n=4). Cheapest forward check: forward fires split AM/PM at fwd5; the conditioner lead dies if the AM excess does not survive 10 forward AM fires.
4. **beatendown (INDICATIVE to SCORED on re-base; 17 entries, 3 dates).** fwd3 +998.1 (excess +1,522.9), fwd5 +1,312.0 (excess +1,845.9), fwd10 +1,559.5 (excess +2,083.8), all n=17, every entry AM. The strongest Fires-family profile on live records. Cheapest forward check: its next 10 forward fires at fwd5; clustering (3 dates) is the named limit until then.
5. **The Fires shape, now on live records (capitulation, confluence, donchian, momentum, rsi_meanrev, ts_momentum_decile; all INDICATIVE, re-based).** One shape six times: fwd1 negative (−16.3 to −768.4bp), fwd5 excess +1,256.6 to +1,939.0, fwd10 excess +2,144.2 to +2,605.0 (n=7 to 17 each, 1 to 2 entry dates each). This is KG-4's Fires phase shape (lose night 1, earn nights 2 to 3 and beyond) reproduced on the sleeves' own fills at the wider cache. Cheapest forward check: pooled forward fires across the six, graded by hold phase; the shape lead dies if pooled forward N2-3 excess is not positive after 20 fires.
6. **s_mn_hourly_1w (newly SCORED; 184 entries, 4 dates).** A night-1 spike that decays through zero: fwd1 +749.1 (excess +694.5), fwd3 −96.5 (excess +320.5), fwd5 −1,897.7 (excess −1,412.1), fwd10 −3,035.2 (excess −2,390.6); inversion at fwd5 reads +1,897.7. The lead is the hold-length mismatch, not the raw signal: this stream earns in the first night and pays it back over the hold. Cheapest forward check: a shadow night-1 exit on its forward fires against the sleeve's own exit rule, 20 fires.
7. **The Aster ETF monthly arms (aster_etf_spy_monthly_c098 newly SCORED, 53 entries, 10 dates; aster_etf_qqq_monthly_c098 and m150 already SCORED, re-based at 49 and 15 entries).** spy c098: fwd5 +273.1 (excess +69.4, n=28), with an AM/PM split at fwd5 of AM +624.8 (n=9) against PM +106.5 (n=19). qqq arms pooled (64 entries): fwd5 +453.6 (excess +351.4); AM splits +781.2 (c098, n=9) and +1,793.7 (m150, n=3) against PM +125.7 and +310.2. The time-of-day conditioner is the lead; the pooled fwd5 excess is the supporting read. Cheapest forward check: next 10 forward fires per arm, split AM/PM.
8. **s_mn_macd (INDICATIVE to SCORED on re-base; 177 entries, 5 dates).** Excess-positive at every horizon: fwd1 +162.5 raw (+108.1 excess), fwd3 +54.1 (+471.2), fwd5 +36.4 (+526.7), fwd10 −442.1 raw (+199.7 excess). A benchmark-relative lead: the stream beats QQQ at every horizon while losing raw at fwd10. Cheapest forward check: 20 forward fires graded on excess only.
9. **tensor_swing, the inversion read (INDICATIVE to SCORED on evidence volume; 3,633 stamped entries, 3,778 on the full record, 10 dates).** Negative at every horizon on both bases: full record fwd1 −101.7 (excess −87.0), fwd5 −676.6 (excess −469.4), fwd10 −1,994.5 (excess −1,349.9). The tier rose because the Campaign 1 bar grades evidence, not sign. The lead is the inversion: INVERT_SIGNAL at fwd5 reads +696.1 on the stamped basis and +676.6 on the full record, on the largest live-record stream in the fleet. Cheapest forward check: Campaign 2's inversion arm on its forward fires (the mutation funnel already carries this operator).
10. **aster_native_btc_eth_sma200 (newly SCORED), and the record itself was the find.** On the stamped 26 entries the profile is mixed (fwd10 −582.2, excess −751.0). On the full record, 574 entries including the 548 unstamped buys Lane C's loader dropped, it is negative at every horizon (fwd1 −130.2, fwd5 −397.2 with excess −725.0, fwd10 −1,504.0 with excess −980.3), and the inversion reads +397.2 at fwd5. The desk's recorded history of this sleeve was understated by a factor of 22 before this lane. Disposition: an inversion/avoidance candidate for Campaign 2, not a long lead.
11. **The DMAC family (all four variants newly SCORED; 1,015 entries pooled).** Basis stated plainly: these entries are option-contract fills priced on the contracts' own stored closes, the basis class KG-4 flagged, so the bp magnitudes are contract-price moves, not underlying moves. Shape: fwd1 deeply negative (−3,413.2 to −8,933.8 across variants), fwd3 positive on three variants (+512.2 to +638.8), fwd5 negative again (−2,401.0 to −2,444.2 where priced), inversion at fwd5 +2,401.0 to +2,444.2. investandbefree_dmac_intraday prices only to fwd3 (−4,751.6). No clean lead is claimed on this basis; the family's deciding check is first-touch grading of forward fires through the resolver, not close marks.
12. **Small-n leads, printed at their n.** ema_vwap (newly INDICATIVE, n=2, 1 date): fwd5 +1,535.4 (excess +2,034.1). s_mn_vwap (newly INDICATIVE, 6 entries, 3 dates): fwd5 +1,066.7 (excess +1,788.4, n=4). s_mn_reversal (newly SCORED, 23 entries, 3 dates): fwd1 +55.9 (excess +131.9) then negative, inversion +582.2 at fwd5. aster_etf_drift1_c098 (newly INDICATIVE, n=1): excess positive at fwd1/3/5 (+72.0/+177.1/+98.8) on a single fill. qqq_put_ladder (newly INDICATIVE, n=1, contract basis): −16,956.5 at fwd1 to +4,565.2 at fwd5 on one fill; the datum is that it prices at all, no lead claimed. aster_etf_spy_monthly_m150 (newly INDICATIVE, 5 entries): excess negative at fwd3 and fwd5 (−63.0, −160.9); no lead.
13. **Re-based negatives that close questions.** red_day_reversal (INDICATIVE to SCORED, 165 entries full record): negative through fwd5 (−722.0, excess −615.8), fwd10 +1,987.4 on n=8 only; its registered exit profile grades mean −39.3bp, win 52.7%, over 165 exits (78 stop, 87 horizon). t_cci_corr (INDICATIVE to SCORED, 27 entries): negative raw and excess at fwd1/3/5, inversion +226.0; avoidance side only. aster_saty_research (INDICATIVE, 7 entries, 1 date): negative at every horizon (fwd5 −2,565.1, excess −1,610.5), inversion +2,565.1. bta_onebar_basket (INDICATIVE to SCORED, 12 entries): fwd5 excess −458.9, consistent with the onebar family's negative-expectancy read in Program B. aster_etf_core25_c098 and m150 (INDICATIVE, 2 entries each): mixed, excess positive at fwd3/5 on n=2; no lead claimed. leaps_momentum (INDICATIVE, 16 entries): only fwd1 prices (+66.5, excess +160.1, n=15); its contracts carry no stored forward series past fwd1 on this cache.

## The 17 newly graded, register summary

| Sleeve | New tier | Entries | Dates | Headline profile (raw bp; excess in the register) |
|---|---|---|---|---|
| aster_trader_donchian55 | SCORED | 42 | 3 | fwd5 +2,166.0 |
| aster_tensor_d20_tensor | SCORED | 684 | 7 | fwd5 +753.1 |
| aster_tensor_d20_pv | SCORED | 420 | 7 | fwd5 +641.1 |
| aster_etf_leader1_m150 | SCORED | 18 | 8 | fwd5 +768.0 |
| aster_etf_spy_monthly_c098 | SCORED | 53 | 10 | fwd5 +273.1 |
| aster_native_btc_eth_sma200 | SCORED | 26 (574 full) | 4 (9 full) | fwd10 −582.2 stamped; −1,504.0 full |
| investandbefree_dmac | SCORED | 280 | 4 | fwd3 +613.5 (contract basis) |
| investandbefree_dmac_dailyonly | SCORED | 279 | 4 | fwd3 +638.8 (contract basis) |
| investandbefree_dmac_intraday | SCORED | 179 | 3 | fwd3 −4,751.6 (contract basis) |
| investandbefree_dmac_premacd | SCORED | 277 | 4 | fwd3 +512.2 (contract basis) |
| s_mn_hourly_1w | SCORED | 184 | 4 | fwd1 +749.1, fwd10 −3,035.2 |
| s_mn_reversal | SCORED | 23 | 3 | fwd1 +55.9 |
| aster_etf_drift1_c098 | INDICATIVE | 1 | 1 | fwd5 −54.7, excess +98.8 |
| aster_etf_spy_monthly_m150 | INDICATIVE | 5 | 4 | fwd5 +48.5, excess −160.9 |
| ema_vwap | INDICATIVE | 2 | 1 | fwd5 +1,535.4 |
| qqq_put_ladder | INDICATIVE | 1 | 1 | fwd5 +4,565.2 (contract basis) |
| s_mn_vwap | INDICATIVE | 6 | 3 | fwd5 +1,066.7 |

## The 18 previously graded, re-based on the widened cache

Tier moves: beatendown, bta_onebar_basket, red_day_reversal, s_mn_macd, t_cci_corr and tensor_swing move INDICATIVE to SCORED (in each case the wider cache and the full record raised priceable entries past the Campaign 1 bar; tensor_swing's move is on evidence volume, its profile is negative, see lead 9). aster_etf_qqq_monthly_c098 and aster_etf_qqq_monthly_m150 stay SCORED with larger entry counts (49 and 15). aster_etf_core25_c098, aster_etf_core25_m150, aster_saty_research, capitulation, confluence, donchian, leaps_momentum, momentum, rsi_meanrev and ts_momentum_decile stay INDICATIVE with re-based profiles (the Fires six are lead 5; the rest are in leads 13 and the register).

## The 23 exit-only sleeves: what the FIFO reconstruction could and could not attribute

Method: one global FIFO lot pass over all 8,961 filled broker orders, in filled_at order per symbol; every lot carries its entry order's sleeve (from the client_order_id), and a sleeve's recovered round trips are the closings whose exit order is attributed to it. The 23 sleeves' dispatcher records carry exit fills only.

What the FIFO could attribute, in total: 100% of the 23 sleeves' recorded exit quantity was recovered to pooled account lots (unrecovered quantity 0.0 for every sleeve), producing 2,691 account-level round trips whose exits these sleeves placed, each with an entry price, an exit price, and the entry sleeve that opened the lot. The recovered entry streams were then run through Lane C's variation set on the widened cache (the register's profile column), and the round trips themselves grade the pooled stream each sleeve's exits drew from (rt mean, qty-weighted mean, win rate, and a stream tier in the register).

What it could not attribute, for every one of the 23: any round trip to the sleeve's own entries. Own-entry trips are 0 for all 23. No entry fills exist in the dispatcher history, no entry orders exist under the sleeve's own client id in the complete broker history, no fills exist in the desk fill ledger, and no entry records exist in the femto-lean evaluation ledger. The single exception class is stray buys: 8 of the 23 have filled buy orders under their own client id in the broker history that the dispatcher never recorded as entry fills (16 orders: aster_squeeze_1d 4, rsi_meanrev_options 4, po10_qqq 2, trullas_v04 2, rule_1w_cyan_mom_adx 1, s_mn_opt_turtle 1, trullas_divergence 1, trullas_v02 1). Those lots entered the pooled FIFO under the sleeve's name, but none of the sleeve's own exits closed them in the pass, so they fund no own-entry grade either. The FIFO grades therefore measure the pooled stream the exits drew from, never the sleeve's own signal, and all 23 stay UNGRADABLE-BLOCKED on the live-record basis with that exact gap.

Per sleeve (exits = dispatcher exit fills; qty = exit quantity, fully recovered in every case; trips = FIFO round trips closed by this sleeve's exits; rt = round-trip mean bp / qty-weighted bp / win %; stream tier = the tier the recovered entry stream earns on the variation set, printed in the register as fifo_stream_tier; entries from = the sleeves whose lots the exits closed):

| Sleeve | Exits | Qty | Trips | RT mean / qw / win% | Stream tier | Entries from |
|---|---|---|---|---|---|---|
| aster_etf_drift1_m150 | 24 | 14,333 | 512 | −94.5 / −35.3 / 38.7 | INDICATIVE | d20_pv, d20_tensor, dmac x3, red_day_reversal, s_mn_hourly_1w, s_mn_macd, s_mn_reversal, tensor_swing |
| aster_etf_exsmh1_c098 | 1 | 1 | 1 | +14.6 / +14.6 / 100.0 | INDICATIVE | d20_tensor |
| aster_etf_exsmh1_m150 | 11 | 1,225 | 235 | −591.8 / −22.3 / 7.2 | INDICATIVE | d20_pv, d20_tensor, dmac x4, t_cci_corr |
| aster_rsi2_1d | 8 | 93 | 8 | +36.5 / +42.2 / 62.5 | INDICATIVE | qqq c098/m150, spy c098, bta_onebar_basket |
| aster_squeeze_1d | 13 | 82 | 13 | −10.4 / −6.8 / 15.4 | SCORED | leader1_m150, qqq c098/m150, spy c098/m150, bta_onebar_basket, leaps_momentum, s_cl_vmr_qqq |
| em_1587 | 3 | 32 | 3 | +5.3 / +6.4 / 66.7 | INDICATIVE | leader1_m150, spy c098 |
| investandbefree_dmac_deep | 4 | 259 | 259 | −1,640.6 / −1,640.6 / 0.4 | INDICATIVE | dmac x4 (the family's own lots) |
| po10_qqq | 3 | 41 | 4 | +59.6 / +44.4 / 100.0 | INDICATIVE | qqq m150, capitulation |
| qullamaggie | 69 | 1,932 | 1,186 | −92.4 / −37.8 / 33.5 | SCORED | 15 sleeves incl. tensor_swing, d20_tensor, the monthly arms |
| rsi_meanrev_options | 17 | 38 | 17 | −75.6 / −37.5 / 0.0 | SCORED | spy c098, leaps_momentum, tensor_swing |
| rule_1w_cyan_mom_adx | 3 | 12 | 3 | +90.7 / +22.2 / 66.7 | INDICATIVE | leaps_momentum, tensor_swing |
| s_mn_faber | 1 | 31 | 2 | +5.6 / +5.6 / 100.0 | INDICATIVE | spy c098/m150 |
| s_mn_opt_turtle | 15 | 48 | 38 | −313.2 / −366.7 / 28.9 | INDICATIVE | dmac x4, qqq_put_ladder |
| saty_sol | 13 | 358 | 349 | −1,736.8 / −1,713.0 / 4.6 | SCORED | dmac x4 (the family's own lots) |
| saty_sol_0dte | 5 | 15 | 15 | +137.2 / +137.2 / 40.0 | INDICATIVE | dmac x3 |
| tensor_red_dip | 18 | 1,513 | 26 | +135.4 / +311.3 / 80.8 | SCORED | core25 c098, drift1 c098, spy c098, d20_pv, d20_tensor, bta_onebar_basket, tensor_swing |
| trullas_divergence | 3 | 176 | 8 | −58.1 / −69.7 / 0.0 | INDICATIVE | qqq c098/m150, beatendown, confluence, donchian, momentum, morning_dip, ts_momentum_decile |
| trullas_v01 | 1 | 7 | 1 | +8.3 / +8.3 / 100.0 | INDICATIVE | qqq m150 |
| trullas_v02 | 4 | 23 | 4 | −24.6 / −6.1 / 25.0 | INDICATIVE | qqq c098, leaps_momentum |
| trullas_v04 | 2 | 55 | 4 | +7.9 / +8.0 / 100.0 | INDICATIVE | bta_onebar_basket/qqq/rth, leaps_momentum |
| trullas_v05 | 1 | 7 | 1 | −1.4 / −1.4 / 0.0 | INDICATIVE | qqq m150 |
| trullas_v09 | 1 | 14 | 1 | +7.2 / +7.2 / 100.0 | INDICATIVE | qqq c098 |
| trullas_v10 | 1 | 5 | 1 | −86.3 / −86.3 / 0.0 | INDICATIVE | qqq c098 |

The strongest FIFO stream is tensor_red_dip's: its 18 exits closed pooled lots at rt mean +135.4bp, qty-weighted +311.3, win 80.8% over 26 trips, stream tier SCORED. That grades the lots its exits happened to close (opened by seven other sleeves), not tensor_red_dip's own entries, and it is printed here as a stream read only.

## The 25 still blocked in this register, each with its exact remaining datum

- The 23 exit-only sleeves above: the missing datum is the sleeve's own entry record (entry fills or entry orders under its own client id). It does not exist in the dispatcher history, the complete broker order history of 8,961 orders, the desk fill ledger, or the femto-lean evaluation ledger. Nothing on this machine can supply it; the block is a record gap, not a data-access gap. The 8 stray-buy sleeves (aster_squeeze_1d, rsi_meanrev_options, po10_qqq, trullas_v04, rule_1w_cyan_mom_adx, s_mn_opt_turtle, trullas_divergence, trullas_v02) additionally carry broker-side buys under their own client id that no desk record explains.
- aster_tensor_h1_recovery: 14 entry fills, all dated 2026-11-13, the final completed session in every stored series. The missing datum is any forward bar after 2026-11-13; it lands with the 2026-11-16 session bars, at which point the sleeve prices mechanically.
- aster_abs_base_ada_fullcash: Lane C's "no fills of any kind" datum was wrong. The full dispatcher record carries exactly 1 fill, an unstamped ADA/USD buy at the end of the stored series. The missing datum is a forward bar after that fill (end-of-series class). Its best evidence class is REPLAY (Unblock Lane 2 graded it REPLAY-INDICATIVE); see the census overlap note.

## Full sleeve census reconciliation: all 339 sleeves by best evidence class and tier

Arithmetic, verified from the four registers (Lane C, Unblock 1, Unblock 2, KG-6):

- Lane C graded 24 of 339 on live records (2 SCORED, 22 INDICATIVE) and left 315 UNGRADABLE-BLOCKED.
- Unblock Lane 1 attacked 60 of the 339: 42 of Lane C's blocked (17 newly graded, 23 exit-only, aster_tensor_h1_recovery, aster_abs_base_ada_fullcash) and 18 of Lane C's graded (re-based; 6 tier upgrades). 6 further Lane C graded sleeves were repriced in the lane's work files and kept their tiers.
- Unblock Lane 2 replay-graded 274 sleeves, all of them Lane C blocked, none of them live-record graded. Its tiers on delivery: 23 REPLAY-SCORED, 34 REPLAY-INDICATIVE, 195 REPLAY-NO-FIRE, 22 EXECUTION-IMPOSSIBLE.
- KG-6 re-graded exactly those 22 EXECUTION-IMPOSSIBLE sleeves (all ENJ, on the Kraken route): 2 REPLAY-SCORED, 8 REPLAY-INDICATIVE, 12 REPLAY-NO-FIRE, 0 impossible. The impossible class is empty.
- Overlaps, named: the only sleeve appearing in both Unblock 1's register and Unblock 2's register is aster_abs_base_ada_fullcash (Lane C's no-fills class put it in Lane 2's 274; Unblock 1's datum correction keeps it blocked on the live-record basis, so its best evidence class is REPLAY). KG-6's 22 are a proper subset of Unblock 2's 274. Unblock 1's 60 and Unblock 2's 274 are otherwise disjoint, and 60 + 274 + the 6 untouched Lane C graded sleeves account for the population with the blocked remainder below: 41 + 274 + 24 = 339.

Final census, best evidence class per sleeve (LIVE-RECORD outranks REPLAY; a sleeve graded on both bases is counted once, at LIVE-RECORD; no sleeve is in that position today except as noted):

| Evidence class | Tier | Sleeves |
|---|---|---|
| LIVE-RECORD | SCORED | 20 |
| LIVE-RECORD | INDICATIVE | 21 |
| REPLAY | REPLAY-SCORED | 25 |
| REPLAY | REPLAY-INDICATIVE | 42 |
| REPLAY | REPLAY-NO-FIRE | 207 |
| UNGRADABLE-BLOCKED (no basis) | UNGRADABLE-BLOCKED | 24 |
| **Total** | | **339** |

Composition of the final classes: LIVE-RECORD 41 = Lane C's 24 (of which 18 re-based by Unblock 1, 6 untouched) + Unblock 1's 17 newly graded; its tiers are 20 SCORED (12 newly + 6 upgrades + 2 held) and 21 INDICATIVE (5 newly + 16 held). REPLAY 274 = Unblock 2's population with KG-6's re-grades folded in (25 SCORED = 23 + 2; 42 INDICATIVE = 34 + 8; 207 NO-FIRE = 195 + 12). UNGRADABLE-BLOCKED 24 = the 23 exit-only sleeves + aster_tensor_h1_recovery, whose forward bars land with the 2026-11-16 session.

Reading of the census: 315 of 339 sleeves (92.9%) now carry a grade on some evidence basis; 41 carry one on their own live records, up from 24 before this lane; 274 carry a replay grade on their own logic; 207 of the replay grades are NO-FIRE (the logic executed cleanly over its full span and produced no entries, cause named per sleeve in Unblock 2's register); 24 remain blocked, 23 of them on a record gap no route on this machine can fill, 1 on the calendar.

STATUS: PARTIAL. Unblock Lane 1's deliverable and the census are proven on the final registers (60 register rows recounted; 17 newly graded = 12 SCORED + 5 INDICATIVE; census 41 + 274 + 24 = 339 with the single cross-lane overlap named); the PARTIAL names the remainders: 23 exit-only sleeves blocked on an entry record that exists nowhere on this machine, aster_tensor_h1_recovery blocked until the 2026-11-16 session bars land, and every lead above is an in-sample profile whose forward check is named in its entry and not yet run.
