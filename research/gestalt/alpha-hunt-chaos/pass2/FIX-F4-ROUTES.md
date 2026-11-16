# FIX LANE F4 — NO-FIRE CAUSE CLASSES, ROUTE-ATTACK PROGRAM

Doctrine applied (owner, binding): a sleeve that does not fire is a ROUTE FAILURE. There is no armed-by-design resting class. Every class below was attacked through genuinely different routes (feed source, serving form, tagging, timeframe, universe, expression surface); the route changes, the signal stays — no core signal logic was rewritten anywhere in this lane, and no fire was manufactured by gutting a signal. Where strictness itself was the remaining blocker, loosened forms were registered as NEW variation sleeves (Addendum 2 / gutting-as-variation ruling), never as edits to the parent. Monitor sleeves were checked for their DESIGNED output occurring.

Scope note on sources: classes are the named causes of Unblock-2's register (UNBLOCK-2-REGISTER.jsonl, 195 REPLAY-NO-FIRE rows), made deterministic by a classifier whose per-sleeve rows are saved at `pass2/f4_work/f4_census.json` (script `f4_work/census.py`). Counts below are recounted from the register by that script. The ENJ 10 funding-squeeze sleeves are NOT part of the 195 (in Unblock-2 they were EXECUTION-IMPOSSIBLE; KG-6 graded them REPLAY-NO-FIRE) — overlap between the ENJ 10 and the 195 is ZERO, stated explicitly per the brief. The other 2 KG-6 NO-FIRE sleeves (free_kraken_enj_spot, fwd_alpaca_enj_iu_body) are likewise outside the 195 and are handled in the ENJ section.

Repo state caveat: this lane started at HEAD 87a3956; sibling lanes landed work during the run (HEAD is now e76b920 including this lane's three commits). One named defect from the brief — iron_condor's vix 4-tuple — was cured by the sibling F2 lane before this lane reached it (commit 5dbc57c, F2-SHIM-TYPES-20261115, blocker + BUGLOG in tree; verified in the final tree at desk3/sleeves/iron_condor.py line 89: `derived["vix"] = float(_vb[-1]["c"])`). This lane does not duplicate it; iron_condor's remaining blocker is its options-feed class (below).

## CENSUS — the 195 by named cause (sums to 195)

| class | count | one-line cause |
|---|---|---|
| BARS-ONLY-SINGLES | 46 | logic executed over the full span; the signal condition never occurred on the served series |
| FUNDING-GATED-CRYPTO | 27 | funding-filtered Aster crypto (ADA/LINK nfs/squeeze/absorption arms); replay served no funding history, sleeves fail closed by documented design |
| OPTIONS-FEED-ABSENCE | 24 | entries require historical option chains / IV history; none exists on this box |
| Q07-SMALL | 24 | synthetic + real fire pools are large-cap stamped band ml; small-band specs refuse by their own band rule — their universe is not in the cache |
| TENSOR-REFUSAL | 20 | Tensor variant consumers refused all bundle fires (diagnosis deepened below: values, not just cells) |
| Q07-ML-GATED | 11 | with alt-data filters dropped, bar-computable filters or QQQ-down timing still refused every fire on this window |
| MN-NO-REBALANCE | 9 | forecast-management logic over the synthetic momentum-ranked forecast produced no qualifying rebalance |
| RSI2-NO-RECOVERY | 9 | recovery conditions never occurred on the served ADA tapes |
| ETF-B9-ELIGIBILITY | 8 | b9 selection path produced no selection on any of 255 sessions; most sector secondary histories carry ~180 sessions against the engine's 252-session eligibility floor |
| TIMING-STREAM | 8 | r19 timing sleeves; the timing_signals drop is research-lane, 1-day freshness, and ages out (see Class 1) |
| KRAKEN-CURRENT-ONLY | 6 | cache/kraken/inputs.json is a current snapshot; no Kraken history was served in replay |
| REAL-RULE-SPARSE | 3 | the real GBM rule-fire drop carried no usable fires for these sleeves' symbols in the window |

Cross-cut by the Lane-C upstream datum (the brief's Class 1 framing): 49 of the 195 name an upstream stream that produced no recorded entry — fires 23, tensor_fires 8, sleeve_fires 7, timing_signals 4, lazarus_fires 2, rule_fires 2, midna_signals 2, rule_fires_1h 1 — and 146 record no upstream (bars-driven logic, no own event stream). 49 + 146 = 195.

## CLASS 1 — UPSTREAM STREAMS (49 named + the live drops behind them)

Diagnosis, per stream, from the live system of record (state/ingest drops, state/dispatcher.jsonl, cache/tensor bundles) on 2026-11-15:

- **fires (23, all Q07)** — the live drop EXISTS: state/ingest/fires.json carries 52 fires (generated 2026-11-14T22:10Z) and the producer route is wired (desk3/producers3.py ingest, fail-closed on stale/malformed). The sleeves' silence is not an empty stream; it is band/filter gating downstream (Q07 classes below). Producer verdict: running, writing to the path the consumer reads.
- **sleeve_fires (7, all Q07)** — same composer drop family; same verdict as fires.
- **tensor_fires (8: 5 Q07 s_ml/s_mi + 3 r19 G4 tensor)** — the bundle route is the Tensor class below. The Q07 five additionally need Tensor fires carrying alt-data tags (ins2 family); the bundle fires carry no insider tags, so even a fired Tensor week cannot pass ins2 — a TAGGING gap, named: no producer on this box stamps insider data onto Tensor fires; the alt_data drop (130 items, 2026-11-14) is a separate channel the Q07 engine reads for its own fires, not for tensor_fires.
- **timing_signals (4)** — drop EXISTS (41 signals, generated 2026-11-14T19:52Z) but the producer's freshness SLA is 1 day (desk3/producers3.py TimingSignalsProducer, max_age_days=1): by the next session the drop is stale and consumers fail closed. The producer is a research-lane ingest (v625 swing report, unreachable from this box); v3 never executes research code. Route verdict: the plumbing is correct and fail-closed by design; the route failure is drop CADENCE on the research side, outside this repo's rails to cure. Replay-side, the archived drops (state/ingest/archive/2026-11-14 and 2026-11-15) are the honest historical surface and are what any forward replay must serve.
- **lazarus_fires (2: 1h, s_1wsw_stress)** — the live drop is EMPTY (state/ingest/lazarus_fires.json: fires list length 0, generated 2026-11-14T22:10Z, bundle_session-stamped). Recursing one level, as the brief orders: the drop derives from the Tensor bundle, whose fires channel was [] on the 2026-11-13/14/15 bundles while carrying 21 fires on 11-11 and 11-12. The Tensor engine's confirmed-swing output was empty for those three sessions — producer's own gate never passing on those sessions, not a plumbing break (the same channel delivered 21 fires two sessions earlier; producers.py TensorBundleFile serves a present-but-empty list as a live-but-empty channel per the 2026-11-03 ruling). In replay, SYNTH-LAZ served a full synthetic fire stream and both sleeves still refused on their own gates (1h: drop_both_red and drop_qqq_down variation runs also 0 entries — the gate conjunction itself never occurred on the served stream, counted in Unblock-2's runs).
- **rule_fires (2) + rule_fires_1h (1)** — the live drop EXISTS and is large (state/ingest/rule_fires.json: 624 nested items incl. rule_fires_1h, generated 2026-11-14). REAL-RULE replay verdict stands: these three sleeves' symbols carried no usable fires in the window (a fourth rule sleeve fired once). Producer verdict: running; the sparsity is in the GBM scorer's output for these symbols, one level up, research-lane side.
- **midna_signals (2: s_mn_hourly, s_mn_nostop)** — drop EXISTS and is fresh (158 signals, generated 2026-11-15T18:53Z). The sleeves are in the MN class below; the stream is not the blocker.

Cures in this class: none at the producer/plumbing level — every named stream's producer is running and writing where its consumer reads, except lazarus_fires (empty because its own producer's output was empty, engine-truth for those sessions) and timing_signals (cadence owned by the unreachable research lane; the fail-closed read is the designed behavior). Both are printed here as diagnosed, not fenced: lazarus_fires emptiness recurses into the Tensor engine's session output, and timing cadence is an external dependency with its archive route named.

ROUTES TRIED (this class): (1) live-drop census — every stream's current drop read at its consumer path, counts above; (2) archive-drop route — state/ingest/archive holds dated drops for 2026-11-12..15, the honest replay surface for the research-lane streams; (3) recursion into the Tensor bundle for lazarus_fires (counts above). Result: no plumbing defect found to cure; the 49 resolve into their downstream classes (Q07 35 of them by unit, Tensor 3, MN 2, timing 4, rule 3, Lazarus-gates 2).

## CLASS 2 — TENSOR-REFUSAL (20)

Diagnosis (deepened past Unblock-2's "cells were empty"): Unblock-2 served 91 fires (49 regenerated Friday bundles 2026-09-18..11-06 + 42 archived production fires 2026-11-11/12). The archived pair are OLD-FORM bundles (keys: session, generated_at, sleeves, fires — no tensor_analysis at all), so their fires carried no feature cells. This lane re-served those 42 fires through the desk's OWN native pass (desk3/tensor_warm._apply_native_pass, as-of warm-cache daily bars; script `f4_work/tensor_route.py`, output `f4_work/tensor_route_out.json`):

- Feature completeness: **0/42 → 42/42** fires gained complete ret60/vol20/adv/atr_ratio cells. The serving cure works mechanically.
- Gate values after stamping: ret60>=31 on **0/42**, ret60>=0 on 2/42, vol20>=.07 on 42/42, adv>=2e6 on 42/42, buy-cyan markers on 0/42, buy-green on 0/42, atr<=1 on 4/42. The archived fires are RECLAIM/TRANSITION phenotypes from a falling tape (e.g. NBIS ret60 −37.7, markers []; LITE markers [sell-magenta]). The consumers gate on the WEEKLY engine's buy markers plus ret60 strength; on those two sessions the weekly product produced no buy markers for the fired symbols, so the gates refuse on VALUES, correctly, once cells exist.
- The 5 consumers that fired in Unblock-2 (aster_tensor_c1_cash_all_25, aster_tensor_g4_cash_all_10, aster_tensor_g4_cash_all_25, aster_tensor_g4_cash_cool_25, aster_tensor_g4_cash_hot_25, 1 entry each) fired on regenerated Friday bundles where symbol-weeks DID carry the weekly product. Per-consumer result after this lane's serving cure, on the archived pair: all 25 consumers (the 20 here plus the 5) take **0 entries** from the 42 archived fires — the refusal is value-faithful, not a serving defect. On the regen set the split stands as Unblock-2 printed it (5 fired, 20 refused).
- One real serving defect WAS found and cured: the warmer's analysis universe was the producer memo's rows only, so a fire whose symbol sat outside the memo got no analysis record and permanently empty cells (regen evidence: VELO/WYFI fires unstamped on 2026-09-18/25 and 2026-10-02 while sibling fires were stamped). Cure FIX-F4-20261115-B (commit 36a78ec): universe = memo UNION bundle fire symbols. Blocker: TensorWarmUniverse test; fail direction proven on the preserved pre-cure copy (captured universe ['AAA'] only).

ROUTES TRIED: (1) serving form — archived bundles re-served with the live native pass: cells 0→42/42, entries still 0 (values refuse); (2) universe route — memo-union cure above, removes the one structural starvation; (3) timeframe/expression — the consumers' gates ARE the weekly product's expression of the Tensor signal; the swing-channel fires that lack weekly buy markers cannot pass without rewriting the consumers' signal definition, which the rails forbid; (4) variation route — 2 _varpx variations registered (ret60 floor 31→0): at the loosened floor, 2 of the 42 stamped fires pass the C1 numeric profile (vs 0 at the parent floor); registered with falsifiers in config/f4_variations_20261115.json, parents untouched. Class census after: 20 still not firing on their own logic, routes (1)–(3) exhausted in print, route (4) spawned and registered.

## CLASS 3 — THE ENJ 10 FUNDING-SQUEEZE SLEEVES (outside the 195; overlap ZERO)

Base recount (route 0, this lane's own script `f4_work/enj_routes.py`, funding as-of at the bar-close instant, prints at the close included — KG-6's serving convention): on the 420-bar eval window, funding negative on 74 bars, 20-bar breakouts on 20, conjunction **0** — KG-6's count recounted exactly. (An earlier draft of this lane's script used as-of at close−1s and produced a phantom conjunction at bar 607; the discrepancy was traced to the OKX print timestamped exactly at that bar's close and the script was corrected — the engines' serving convention is the close instant.)

ROUTES TRIED, each printed with its conjunction count (conjunction = funding<0 AND close > max high of prior 20 bars, the engines' own definition; signal definition never changed):

- **(a) 1H tape** — Kraken public OHLC ENJUSD interval 60, HTTP 200, error [], 721 candles (720 complete after dropping the in-progress candle), 2026-10-16T19:00Z..2026-11-15T18:00Z (Kraken's 720-candle cap makes the 1H tape 30 days against the 4H tape's 120). Conjunction at 1H resolution: **4** occurrences (warmup 20, 700 eval bars; bars 266, 373, 565, 566) and **3** at the 420-bar warmup-300 convention (373, 565, 566). Funding negative on 160 eval bars, breakouts on 33.
- **(b) different funding series** — the KG-6 series is OKX's ENJ-USDT-SWAP realized funding-rate history (584 obs). Alternatives attempted live in this lane: Binance fapi fundingRate ENJUSDT → HTTP 451 (geo-restricted, same block KG-6 recorded); Bybit v5 funding history → HTTP 403 (CloudFront geo-block); Hyperliquid public fundingHistory for ENJ → returned null (no series); OKX ENJ-USD-SWAP (coin-margined) → code 51001, instrument does not exist. The sleeves' LIVE funding producer is Coinalyze (desk CoinalyzeFundingProducer, snapshot channel): it serves current prints, and no historical Coinalyze archive exists on this box, so a Coinalyze-form historical series is NOT obtainable — named as the series gap. Route (b) verdict: exhausted with the archive gap named; OKX remains the only obtainable historical series, and routes (a)/(c) were therefore evaluated on it.
- **(c) intrabar evaluation surfaces (4H tape, 420 eval bars)** — (c1) breakout on bar HIGH vs prior-20 max high, funding as-of close: breakouts 30, conjunction **1** (bar 455); (c2) close breakout, funding = any print inside the bar's window negative: conjunction **1** (bar 607, the boundary print); (c3) both intrabar: conjunction **1** (bar 607). On the 1H tape, high+anyprint: conjunction 2 (373, 565).
- **(d) window route (found by the engine drive)** — at the engines' minimal warmup (21 bars) over the FULL 720-bar 4H tape, the conjunction occurs **1** time (bar 192, 2026-08-19T16:00Z bar): KG-6's zero is a property of its 300-bar warmup convention, not of the tape. All 10 sleeves' engines take that entry when driven over the full tape.

ENGINE REPLAY ON ROUTE (a) — the sleeves' OWN engines driven bar-by-bar over the 1H tape, funding latest-as-of bar close (script `f4_work/enj_engine_drive.py`, output `f4_work/enj_engine_drive_out.json`). A serving-form defect was found and cured first: batch7's ENH freshness gate hardcoded the 4H bar duration, so on the 1H tape every signal read −3h old and the 3 r19 arms refused all 4 conjunction bars (batch8's arms, whose freshness fails open on short tapes, fired). Cure FIX-F4-20261115-A (commit 20baa09): both batch7 and batch8 freshness gates derive bar duration from the served bars' own spacing (bit-identical on the native 4H tape; 900s window, switch, and all signal logic untouched). Post-cure entries on the 1H tape: aster_enj_nfs_fixed96_vol 3 (2026-10-27T21:00Z, 2026-11-09T08:00Z, 2026-11-09T09:00Z); aster_enj_nfs_lost_full 4 (+2026-11-01T08:00Z); aster_enj_nfs_lost_vol 3; aster_enj_nfs_norm_full 4; aster_enj_nfs_norm_vol 3; aster_enj_nfs_normfail_full 4; aster_enj_nfs_normfail_vol 3; aster_r19_enjusdt_negative_funding_squeeze_fixed16_fullcash 4; aster_r19_enjusdt_negative_funding_squeeze_fixed16_volume1pct 3; aster_r19_enjusdt_negative_funding_squeeze_fixed96_fullcash 4. On the full 4H tape every one of the 10 also takes the bar-192 entry. **Class census after: 10 of 10 firing on their own logic on route (a) (and on the full-tape 4H route); 0 remaining.** The 1H serving form is a replay-route result: live serving remains the native 4H tape, and the forward falsifier is unchanged — the first live 4H bar where funding prints negative into a 20-bar breakout is the family's first live test; the 1H route is the armed alternative expression surface if the desk chooses to serve it.

The other 2 KG-6 NO-FIRE sleeves:
- **free_kraken_enj_spot** — entries require the Kraken top-10 book (spread <= 50bp, bid/ask depth ratio >= 2.0) from view extra["book"] / kraken_inputs book channel. Routes tried: (1) historical book archive — none exists on this box and no public route archives historical Kraken book depth (the inputs snapshot carries TODAY's book only: cache/kraken/inputs.json sleeves.free_kraken_enj_spot.book with bids/asks); serving today's book across historical bars would fabricate the input, refused. (2) forward-collection route — the live snapshot channel already refreshes the current book; the honest cure is time: dated book snapshots accumulate from the live producer forward, after which replay becomes possible. Route exhausted with the archive gap named exactly: historical order-book depth is not a bar series and no honest source archives it.
- **fwd_alpaca_enj_iu_body** — monitor by design. Designed output = a `monitor_status` journal record on EVERY evaluation carrying the provider-proven status (ENJ/USD unlisted at Alpaca, LIST_ERROR; proof/enj-provider-2026-10-24.json), while its signal returns [] unconditionally. Designed-output check at the destination: state/fwd_alpaca_enj_iu_body/journal.jsonl carries **80 monitor_status records** — the designed output occurs. Under the owner doctrine's monitor clause this sleeve is NOT a route failure: its designed output fires; its entries are empty by the source ruling it preserves. Routes tried: (1) designed-output verification (above, occurs); (2) alternate venue expression — refused as a route: the sleeve's identity is the Alpaca forward port; re-venueing it would create a different sleeve, and the ENJ spot expression already exists live as free_kraken_enj_spot and the aster ENJ family.

## CLASS 4 — Q07-SMALL (24) and Q07-ML-GATED (11)

Diagnosis: Q07 sleeves consume Tensor 1W fires in a named cap band with alt-data filters, buying on QQQ-down days. The replay fire pool (synthetic + the 46 real composer fires) is the cached large-cap universe stamped band ml. Small-band specs refuse it by their own band rule — faithful refusal, universe absent. The 11 midlarge sleeves survive the alt-filter drop but their bar-computable filters (deep70/cheap5/mom6) or QQQ-down timing refused every fire on this window.

ROUTES TRIED: (1) tagging route — Unblock-2 served per-sleeve fires stamped with the sleeve's own id under extra['sleeve_fires'] plus the 46 real composer fires (which carry real alt tags): small-band still refused on band, midlarge-gated still refused on bar-computable gates; (2) universe route — the small-band universe is not in the box's cache (cache/bars: 151 files, large-cap); no honest small-cap fire pool exists to serve, and stamping large-cap fires as small-band would fabricate the band, refused — route exhausted with the universe gap named; (3) gate-drop route (Unblock-2's own replays) — dropping alt filters revealed entries in 14 midlarge sleeves (23 entries total) and in ZERO small-band sleeves (band is not an alt filter). Precision on those 14: they sit OUTSIDE the 195 — the register grades them REPLAY-INDICATIVE on the revealed stream, while their BASE runs produced 0 entries; the Q07 catalog totals 49 sleeves = 24 small + 25 midlarge (14 revealed + the 11 ML-GATED below). (4) variation route (this lane, Addendum 2) — those 14 sleeves, whose own registered logic has never produced an entry, gained registered _vargd variations (alt filters dropped, bar-computable kept), replay counts and falsifiers in config/f4_variations_20261115.json; the parents are untouched (blocker test asserts each parent's catalog filters still equal the registry's record). Of the 11 ML-GATED in the 195, none was revealed even by the full alt-drop, so no variation was spawned for them — their blocker is bar-computable strictness on this window, and a further loosening would drop the signal's own bar-computable identity (deep70/cheap5/mom6 ARE the catalog's bar-side definition), which is a new-signal decision, not a route. Class census after: Q07-SMALL 24 still not firing, routes exhausted in print (universe gap named); Q07-ML-GATED 11 still not firing, routes exhausted in print; the 14 variation parents are outside the 195 and are not in the remainder tables.

## CLASS 5 — OPTIONS-FEED-ABSENCE (24)

Diagnosis: entries require historical option chains and IV history. The box's options cache is 65 symbol directories × one current chain.json each — snapshots, no dated history; IV history exists only as the warm-time ledger for the iron_condor family's watchlist symbols (runtime/options_warm.py maintains current + history[-260:] per symbol going forward). iron_condor additionally carried the vix defect, cured by sibling lane F2 (commit 5dbc57c); its entries still require the absent chains.

ROUTES TRIED: (1) cache route — full census of cache/options (above): no dated chains exist to serve; (2) forward-collection route — the options warmer already writes current chains and IV history forward; dated chain archiving is the accumulation route and its first usable replay window is a season of accumulated snapshots, named as the gap (a route needing data no honest source archives is exhausted, per the brief — historical chains for 2025-11..2026-11 cannot be backfilled honestly); (3) underlying-only expression route — refused as fabrication-adjacent: these sleeves' signals ARE option-structure signals (condor credits, PEAD verticals, XSP put-credit spreads, gamma); expressing them on underlyings would rewrite the signal, outside the rails. Class census after: 24 still not firing, routes exhausted in print with the archive gap named (historical option chains / IV history).

## CLASS 6 — FUNDING-GATED-CRYPTO (27, ADA/LINK arms)

Diagnosis: the ADA/LINK analogues of the ENJ class — funding-filtered nfs/squeeze/absorption arms whose replay served no funding history at all (Lane 2 documented fail-closed design), plus the ADA absorption funding arms (4) whose base stream fired but whose funding-split arms could not be served.

ROUTES TRIED: (1) the ENJ-proven public route, transferred — Kraken public OHLC serves ADA/LINK spot and PF_ tapes (the ADA/LINK 4H tapes already exist on the box: 2,049 bars each per Unblock-2's cache state) and OKX public funding-rate-history is venue-identical in form for ADA-USDT-SWAP / LINK-USDT-SWAP; this lane proved the full pattern end-to-end on ENJ (tape fetch + OKX funding + engine drive + freshness cure). The ADA/LINK engine drives on that pattern were NOT re-run in this lane — stated plainly: the route is proven as a pattern, the per-sleeve ADA/LINK replay counts are still owed, and this class is the lane's largest named remainder. (2) live-series route — live, the sleeves ARE fed: the Coinalyze snapshot funding producer serves current prints (desk3/aster_batch8.py header: funding served since 2026-11-14), so the live route failure is only the historical-replay gap, same shape as ENJ before KG-6. Class census after: 27 still not firing in replay, route (1) proven-by-pattern with per-sleeve drives named as the owed next step.

## CLASS 7 — ETF-B9-ELIGIBILITY (8)

Diagnosis: the b9 interval/leader arms' selection produced no selection on any of 255 sessions. desk3/aster_etf_b9.py carries MIN_SESSIONS = 252 (minimum_valid_post_inception_sessions); most sector secondary histories in the cache carry ~180 sessions, below the floor, so the eligible set is empty on most sessions.

ROUTES TRIED: (1) history-widening route — Lane 1 already widened cache/bars (149 daily symbols, longest series preferred); the secondaries remain ~180 sessions because their listed history in the served caches is what it is; the floor is the engine's own eligibility rule, and lowering it would rewrite a signal-side constant — outside this lane's rails (it is a strategy decision for the desk, named here as the exact decision: either accept ~180-session secondaries by a ruled MIN_SESSIONS change, or wait for the caches to season past 252). (2) universe route — restricting selection to the long-history names changes the sleeve's universe definition (the arms are sector-rotation sleeves; their universe is the point), refused as a route. Class census after: 8 still not firing, routes exhausted in print with the ruled-decision gap named.

## CLASS 8 — RSI2-NO-RECOVERY (9), MN-NO-REBALANCE (9), REAL-RULE-SPARSE (3), KRAKEN-CURRENT-ONLY (6), TIMING-STREAM (8), BARS-ONLY-SINGLES (46)

- **RSI2 (9)** — after Unblock-2's timezone cure the set evaluated cleanly; their recovery conditions (RSI2 oversold + recovery confirmation on the PF_ADAUSD / equity tapes) never occurred on the served tapes. Routes: (1) tape route — served on the full PF 4H ADA tape (2,049 bars) and equity daily tapes in Unblock-2; occurrence count of the full condition: 0 (the sleeves' own evals, 255 sessions / 4H evals per register runs); (2) universe route — the recovery arms are symbol-fixed by catalog (ADA + the fixed/touch equity pairs); no alternate universe exists for them. Census: 9 still not firing, routes exhausted in print.
- **MN (9)** — forecast-management logic over SYNTH-MN (momentum-ranked synthetic forecast) produced no qualifying rebalance entries; the Kronos sibling fired (26 entries) on the same feed, proving the feed route works and the refusal is these sleeves' rebalance thresholds on this forecast. Routes: (1) feed route — synthetic forecast served, sibling fired (above); (2) the real-forecast route — the live midna_signals drop is fresh (158 signals) so live serving is not blocked; the replay-grade route for the real forecast does not exist historically (drops archived only from 2026-11-12). Census: 9 still not firing in replay, routes exhausted in print.
- **REAL-RULE (3)** — see Class 1 rule_fires: the drop is live and large; these symbols carried no usable fires. Routes: (1) live-drop route (exists, counted); (2) archive route (drops 2026-11-12..15 exist). The scorer is research-lane; symbol coverage is its output, not plumbing. Census: 3 still not firing, routes exhausted in print.
- **KRAKEN-CURRENT-ONLY (6)** — replay served only the current snapshot. Routes: (1) public-history route — cache/kraken/inputs.json itself proves the desk's Kraken producer aligns 721-bar spot/perp histories (free_kraken_ada_basis and free_kraken_link_basis payloads carry 721/721 aligned series, decision READY, generated 2026-11-02): the historical series EXIST in the producer's own evidence channel, so a replay serving those aligned histories is an honest route; the per-sleeve replay drives on it were not run in this lane (named remainder, same pattern as Class 6). (2) snapshot route — Unblock-2's KRAKEN-CURRENT serving: evaluated, no fire on a single snapshot (a basis/crowded signal cannot form on one print). Census: 6 still not firing in replay, route (1) identified with its evidence channel named.
- **TIMING-STREAM (8)** — the 4 timing_hour arms are Class 1's timing_signals (drop cadence, research-lane owned); the 2 timing_cloud and 2 timing_overnight arms are bars-driven and refused on their own conditions over 255 sessions. Routes: (1) drop-archive route for the hour arms (archived drops exist); (2) bars route for cloud/overnight (full-span evals, 0 occurrences). Census: 8 still not firing, routes exhausted in print.
- **BARS-ONLY-SINGLES (46)** — the remainder class: each sleeve's logic executed cleanly over its full span (evals per sleeve in the tables) and its condition never occurred on the served series. Routes per sleeve were the Unblock-2 base replay plus its variation runs (gate drops / exit sims where the stream existed); this lane adds: (1) span route — Lane 1's cache widening already extended the served spans to the longest series on the box (149 daily symbols; PF tapes 2,049 bars); no longer honest span exists on this box; (2) the class is heterogeneous by construction (Saty, Trullas, spec singles, fwd ports, Lazarus singles) — no single serving defect is shared, and none was found in this lane's census of their feeds. Census: 46 still not firing, routes exhausted in print per sleeve below. This is the class where the owner's variation option remains widest open: no variations were spawned here in this lane because no per-sleeve near-miss evidence (a gate that almost passed) exists in the register to aim a loosening at; spawning un-aimed loosenings would be manufacturing, not routing.

## CURES LANDED IN THIS LANE (with proof)

| cure | commit | blocker | proof |
|---|---|---|---|
| FIX-F4-20261115-A: batch7/batch8 freshness gates derive bar duration from served bars (was hardcoded 4h) | 20baa09 | tests/test_f4_routes_20261115_blockers.py Batch7Freshness×3 + Batch8Freshness×1 | fail direction proven on preserved pre-cure copies (f4_work/fail_direction.py: pre-cure 1H age −10500 vs want 300; pre-cure entries 0 on 1H and on 1D-spaced tapes; native-4H entry passes pre and post); post-cure engine drive: all 10 ENJ squeeze sleeves fire on the 1H tape |
| FIX-F4-20261115-B: tensor_warm analysis universe = memo ∪ fire symbols | 36a78ec | TensorWarmUniverse | fail direction proven pre-cure (universe ['AAA'] only, fire symbol absent); existing tensor test files still green (27 passed across 6 files) |
| FIX-F4-20261115-C: 16 variations registered, parents untouched | e76b920 | VariationRegistry | registry asserts parent filters equal live catalog; Q07 _vargd replay counts from Unblock-2 (23 revealed entries), Tensor _varpx fire-level read 2/42 vs 0/42 |

BUGLOG: BUGLOG_2026-11-15.md entries FIX-F4-20261115-A/B/C (the repo keeps BUGLOGs at the repo root; there is no desk/ directory in muse-desk-v3). Regression gate spot-runs after the cures: batch7+batch8+f4 blockers 54 passed; edge batch13/14 (Tensor consumers) 35 passed; six tensor warmer/native/archive test files 27 passed. Existing roster unchanged (339) — no sleeves.json rows were added or edited by this lane.

## CLASS CENSUS AFTER

- Firing on own logic: ENJ squeeze 10 of 10 (route A 1H + full-tape 4H; outside the 195). Q07 variations: 14 NEW variation sleeves registered with firing replay reads (23 entries) — variations of parents whose base logic produced 0 entries (register-graded INDICATIVE on the revealed stream, outside the 195), not cures of the parents.
- Still not firing, routes exhausted in print: all 195 of the register classes (per-sleeve rows below), plus free_kraken_enj_spot (book-depth archive gap). fwd_alpaca_enj_iu_body is excluded from the failure census: its designed monitor output occurs (80 journal records).
- Named owed work (not silent): Class 6 ADA/LINK per-sleeve engine drives on the proven ENJ pattern (27 sleeves); Class 7's MIN_SESSIONS ruling-or-seasoning decision (8); Class 5's dated chain accumulation (24, time route); Class 8 Kraken aligned-history replay drives (6).


## PER-SLEEVE REMAINDER ROWS — every sleeve still not firing (195)


### Q07-SMALL (24)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| s_q07w_c52_sm_cheap5_ins2_mom6 | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_c52_sm_cheap5_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_c52_sm_deep70_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_c52_sm_tierA_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_c78_sm_deep70_ins2_vix20 | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_c78_sm_deep70_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_c78_sm_ins2_mom6_vix20 | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_c78_sm_tierA_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_g52_sm_deep70_ins2_vix20 | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_g52_sm_deep70_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_g52_sm_ins2_wcov | Q07 catalog | SYNTH-Q07 | 255 | sleeve_fires |
| s_q07w_g52_sm_tierA_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_g78_sm_cheap5_ins2 | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_g78_sm_deep70_ins2 | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_g78_sm_deep70_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_g78_sm_tierA_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_s52_sm_cheap5_deep70_ins2 | Q07 catalog | SYNTH-Q07 | 255 | sleeve_fires |
| s_q07w_s52_sm_cheap5_ins2_vix20 | Q07 catalog | SYNTH-Q07 | 255 | sleeve_fires |
| s_q07w_s52_sm_cheap5_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_s52_sm_deep70_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_s78_sm_cheap5_ins2_vix20 | Q07 catalog | SYNTH-Q07 | 255 | sleeve_fires |
| s_q07w_s78_sm_cheap5_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_s78_sm_deep70_ins2 | Q07 catalog | SYNTH-Q07 | 255 | sleeve_fires |
| s_q07w_s78_sm_deep70_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |

### Q07-ML-GATED (11)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| s_q07w_g78_mi_cheap5_deep70_ins2 | Q07 catalog | SYNTH-Q07 | 255 | sleeve_fires |
| s_q07w_s52_ml_deep70_vix20_wlow | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_s52_ml_deep70_wlow | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_s52_ml_ins2_mom6_vix20 | Q07 catalog | SYNTH-Q07 | 255 | tensor_fires |
| s_q07w_s52_ml_ins2_mom6_wlow | Q07 catalog | SYNTH-Q07 | 255 | tensor_fires |
| s_q07w_s78_mi_ats_z1_cheap5 | Q07 catalog | SYNTH-Q07 | 255 | tensor_fires |
| s_q07w_s78_mi_ats_z1_mom6 | Q07 catalog | SYNTH-Q07 | 255 | tensor_fires |
| s_q07w_s78_mi_cheap5_ins2_mom6 | Q07 catalog | SYNTH-Q07 | 255 | sleeve_fires |
| s_q07w_s78_ml_deep70_glow_ins2 | Q07 catalog | SYNTH-Q07 | 255 | tensor_fires |
| s_q07w_s78_ml_deep70_mom6_wlow | Q07 catalog | SYNTH-Q07 | 255 | fires |
| s_q07w_s78_ml_deep70_wcov | Q07 catalog | SYNTH-Q07 | 255 | fires |

### TENSOR-REFUSAL (20)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| aster_r19_tensor_g4_hot_delay_25 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | tensor_fires |
| aster_r19_tensor_g4_hot_reserve_25 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | tensor_fires |
| aster_r19_tensor_g4_red_timeout_25 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | tensor_fires |
| aster_tensor_beta_cash_all_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_cash_cool_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_cash_hot_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_delay_all_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_delay_cool_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_delay_hot_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_reserve_all_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_reserve_cool_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_c1_reserve_hot_25 | Tensor batch13 C1/beta consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_g4_delay_all_25 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_g4_delay_cool_25 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_g4_reserve_all_10 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_g4_reserve_all_25 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_g4_reserve_cool_25 | Tensor batch14/15 G4 consumers | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_leaps_a | Tensor D20/H1 model sleeves | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_leaps_b | Tensor D20/H1 model sleeves | TENSOR-ARCHIVE | 255 | none-recorded |
| aster_tensor_w1_recovery | Tensor D20/H1 model sleeves | TENSOR-ARCHIVE | 255 | none-recorded |

### MN-NO-REBALANCE (9)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| s_mn_d_green_band | MN catalog | SYNTH-MN | 255 | none-recorded |
| s_mn_hedge | MN catalog | SYNTH-MN | 255 | none-recorded |
| s_mn_hourly | MN catalog | SYNTH-MN | 255 | midna_signals |
| s_mn_nostop | MN catalog | SYNTH-MN | 255 | midna_signals |
| s_mn_opt_pairs | MN catalog | SYNTH-MN | 255 | none-recorded |
| s_mn_opt_reversal | MN catalog | SYNTH-MN | 255 | none-recorded |
| s_mn_w_cyan_breadth | MN catalog | SYNTH-MN | 255 | none-recorded |
| s_mn_w_cyan_vix | MN catalog | SYNTH-MN | 255 | none-recorded |
| s_mn_w_green_smh | MN catalog | SYNTH-MN | 255 | none-recorded |

### REAL-RULE-SPARSE (3)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| rule_1d_green_tom | ChartsLector fire consumers (rule_*) | REAL-RULE | 255 | rule_fires |
| rule_1h_cyan_raw | ChartsLector fire consumers (rule_*) | REAL-RULE | 255 | rule_fires_1h |
| rule_1w_swing_beta_wt | ChartsLector fire consumers (rule_*) | REAL-RULE | 255 | rule_fires |

### KRAKEN-CURRENT-ONLY (6)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| free_kraken_ada_basis | Free Kraken family | KRAKEN-CURRENT | 1749 | none-recorded |
| free_kraken_ada_breakdown | Free Kraken family | KRAKEN-CURRENT | 1749 | none-recorded |
| free_kraken_ada_crowded | Free Kraken family | KRAKEN-CURRENT | 1749 | none-recorded |
| free_kraken_link_basis | Free Kraken family | KRAKEN-CURRENT | 1749 | none-recorded |
| free_kraken_link_breakdown | Free Kraken family | KRAKEN-CURRENT | 1749 | none-recorded |
| free_kraken_link_crowded | Free Kraken family | KRAKEN-CURRENT | 1749 | none-recorded |

### OPTIONS-FEED-ABSENCE (24)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| aster_open_gamma_a | Aster opening gamma | NONE | 255 | none-recorded |
| aster_open_gamma_b | Aster opening gamma | NONE | 255 | none-recorded |
| aster_pead_long_a | Aster PEAD options | NONE | 255 | none-recorded |
| aster_pead_long_b | Aster PEAD options | NONE | 255 | none-recorded |
| aster_pead_vertical_a | Aster PEAD options | NONE | 255 | none-recorded |
| aster_pead_vertical_b | Aster PEAD options | NONE | 255 | none-recorded |
| aster_xsp_pcs_calm_a | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_xsp_pcs_calm_b | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_xsp_pcs_graded_a | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_xsp_pcs_graded_b | Aster other batch sleeves | NONE | 255 | none-recorded |
| bilbo_options | Fires singles | NONE | 255 | none-recorded |
| capitulation_options | Fires singles | NONE | 255 | none-recorded |
| ema_vwap_options | Fires singles | NONE | 255 | none-recorded |
| fear_premium | Fires singles | NONE | 255 | none-recorded |
| free_opt_own_iv | Free opt family | NONE | 255 | none-recorded |
| free_opt_pair | Free opt family | NONE | 255 | none-recorded |
| free_opt_parity | Free opt family | NONE | 255 | none-recorded |
| free_opt_release | Free opt family | NONE | 255 | none-recorded |
| free_opt_tail | Free opt family | NONE | 255 | none-recorded |
| free_opt_wheel | Free opt family | NONE | 255 | none-recorded |
| iron_condor | Fires singles | NONE | 202 | none-recorded |
| mk_zerodte_spx | Fires singles | NONE | 255 | none-recorded |
| spx_premium | Fires singles | NONE | 255 | none-recorded |
| vix_hedge | Fires singles | NONE | 255 | none-recorded |

### FUNDING-GATED-CRYPTO (27)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| aster_abs_neg_ada_fullcash | Aster absorption | NONE | 1749 | none-recorded |
| aster_abs_neg_ada_vol1pct | Aster absorption | NONE | 1749 | none-recorded |
| aster_abs_nonneg_ada_fullcash | Aster absorption | NONE | 1749 | none-recorded |
| aster_abs_nonneg_ada_vol1pct | Aster absorption | NONE | 1749 | none-recorded |
| aster_link_nfs_norm_vol | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_fixed96_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_lost_breakout_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_absorption_nonnegative_funding_fixed16_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_fixed16_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_fixed96_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_lost_breakout_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |

### ETF-B9-ELIGIBILITY (8)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| aster_etf_interval1_c098 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |
| aster_etf_interval1_m150 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |
| aster_etf_interval_core25_c098 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |
| aster_etf_interval_core25_m150 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |
| aster_etf_interval_drift1_c098 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |
| aster_etf_interval_drift1_m150 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |
| aster_etf_smh_hold_c098 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |
| aster_etf_smh_hold_m150 | Aster ETF arms c098/m150 | NONE | 255 | none-recorded |

### RSI2-NO-RECOVERY (9)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| aster_pub_rsi2_ada | Aster RSI2 recovery/core | NONE | 1749 | none-recorded |
| aster_rec_rsi2_long_fixed_a | Aster RSI2 recovery/core | NONE | 255 | none-recorded |
| aster_rec_rsi2_long_fixed_b | Aster RSI2 recovery/core | NONE | 255 | none-recorded |
| aster_rec_rsi2_long_touch_a | Aster RSI2 recovery/core | NONE | 255 | none-recorded |
| aster_rec_rsi2_long_touch_b | Aster RSI2 recovery/core | NONE | 255 | none-recorded |
| aster_rec_rsi2_vertical_fixed_a | Aster RSI2 recovery/core | NONE | 255 | none-recorded |
| aster_rec_rsi2_vertical_fixed_b | Aster RSI2 recovery/core | NONE | 255 | none-recorded |
| aster_rec_rsi2_vertical_touch_a | Aster RSI2 recovery/core | NONE | 255 | none-recorded |
| aster_rec_rsi2_vertical_touch_b | Aster RSI2 recovery/core | NONE | 255 | none-recorded |

### TIMING-STREAM (8)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| aster_r19_timing_cloud_aggressive | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_r19_timing_cloud_base | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_r19_timing_hour_floor0_delay0 | Aster other batch sleeves | NONE | 255 | timing_signals |
| aster_r19_timing_hour_floor0_delay1 | Aster other batch sleeves | NONE | 255 | timing_signals |
| aster_r19_timing_hour_floor1_delay0 | Aster other batch sleeves | NONE | 255 | timing_signals |
| aster_r19_timing_hour_floor1_delay1 | Aster other batch sleeves | NONE | 255 | timing_signals |
| aster_r19_timing_overnight_25bp | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_r19_timing_overnight_5bp | Aster other batch sleeves | NONE | 255 | none-recorded |

### BARS-ONLY-SINGLES (46)

| sleeve | unit | feed | evals | upstream (Lane-C) |
|---|---|---|---|---|
| 1h | Lazarus fire consumers | SYNTH-LAZ | 255 | lazarus_fires |
| aster_native_eth_sma200 | Aster native SMA200 crypto | NONE | 255 | none-recorded |
| aster_rec_vwap20_long_fixed_a | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_rec_vwap20_long_fixed_b | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_rec_vwap20_long_touch_a | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_rec_vwap20_long_touch_b | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_rec_vwap20_vert_fixed_a | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_rec_vwap20_vert_fixed_b | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_rec_vwap20_vert_touch_a | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_rec_vwap20_vert_touch_b | Aster other batch sleeves | NONE | 255 | none-recorded |
| aster_squeeze_ada_fullcash | Aster other batch sleeves | NONE | 1749 | none-recorded |
| aurelia_gold | Spec singles | NONE | 255 | none-recorded |
| aurelia_ndx | Spec singles | NONE | 255 | none-recorded |
| bb_rsi_divergence | Fires singles | NONE | 255 | none-recorded |
| daily_cyan_gbm | Fires singles | NONE | 255 | none-recorded |
| donchian_crypto | Fires singles | NONE | 255 | none-recorded |
| earnings_buyback | Fires singles | NONE | 255 | none-recorded |
| free_etf | Fires singles | NONE | 255 | none-recorded |
| fwd_alpaca_ada_rsi2 | Fwd port sleeves | NONE | 1749 | none-recorded |
| fwd_alpaca_link_ai_volume | Fwd port sleeves | NONE | 1749 | none-recorded |
| fwd_coinbase_sma200 | Fwd port sleeves | NONE | 255 | none-recorded |
| gate_1h | Fires singles | NONE | 255 | none-recorded |
| grok_sr_spy | Spec singles | NONE | 255 | none-recorded |
| leader_d | Fires singles | NONE | 255 | none-recorded |
| leader_sc | Fires singles | NONE | 255 | none-recorded |
| legends_ema | Fires singles | NONE | 255 | none-recorded |
| phoenix | Fires singles | NONE | 255 | none-recorded |
| przm_fade_edges | Spec singles | NONE | 255 | none-recorded |
| przm_zero | Spec singles | NONE | 255 | none-recorded |
| qullamaggie_paper | Fires singles | NONE | 255 | none-recorded |
| raschke_pf3 | Fires singles | NONE | 255 | none-recorded |
| raschke_rre | Spec singles | NONE | 255 | none-recorded |
| s_1wsw_stress | Lazarus catalog singles | SYNTH-LAZ | 255 | lazarus_fires |
| s_cl_qm_small | Lazarus catalog singles | SYNTH-LAZ | 255 | none-recorded |
| saty_day | Saty family | NONE | 255 | none-recorded |
| saty_gpt_v02 | Saty family | NONE | 255 | none-recorded |
| saty_gpt_v03 | Saty family | NONE | 255 | none-recorded |
| saty_magnum | Saty family | NONE | 255 | none-recorded |
| shen_fade | Spec singles | NONE | 255 | none-recorded |
| snapback | Fires singles | NONE | 255 | none-recorded |
| soxl_pm_breakout | Fires singles | NONE | 255 | none-recorded |
| teddy_orb_spy | Spec singles | NONE | 255 | none-recorded |
| trullas_v03 | Trullas family | NONE | 255 | none-recorded |
| trullas_v06 | Trullas family | NONE | 255 | none-recorded |
| trullas_v07 | Trullas family | NONE | 255 | none-recorded |
| trullas_v08 | Trullas family | NONE | 255 | none-recorded |

## STATUS

STATUS: PARTIAL — proven on the final tree: the ENJ funding-squeeze class is cured (10 of 10 sleeves fire on their own logic on the 1H route and on the full 4H tape, after the batch7/batch8 freshness-duration cure, commits 20baa09/36a78ec/e76b920, blockers 6/6 with fail direction proven on preserved pre-cure copies); the Tensor serving route is cured of its one structural defect (memo-union universe) with the refusal re-diagnosed as value-faithful (0/42 archived fires pass the weekly-product gates even with complete cells); 16 variations are registered with replay counts and falsifiers, parents hash-verified untouched by the blocker test; every one of the 195 register sleeves is classed, diagnosed, and route-attacked in print above with per-sleeve remainder rows. Still open, named: Q07-SMALL (24, small-band universe gap), Q07-ML-GATED (11, bar-computable strictness), TENSOR-REFUSAL (20, weekly-product values on the served fires), OPTIONS-FEED-ABSENCE (24, historical chains archive gap; dated accumulation is the route), FUNDING-GATED-CRYPTO (27, per-sleeve ADA/LINK drives on the proven ENJ pattern still owed), ETF-B9-ELIGIBILITY (8, MIN_SESSIONS ruling or cache seasoning), RSI2-NO-RECOVERY (9), MN-NO-REBALANCE (9), REAL-RULE-SPARSE (3), KRAKEN-CURRENT-ONLY (6, aligned-history replay drives owed), TIMING-STREAM (8, research-lane drop cadence), BARS-ONLY-SINGLES (46, no shared defect; per-sleeve conditions never occurred on the longest honest spans), free_kraken_enj_spot (historical book-depth archive gap). Evidence pointers: f4_work/census.py + f4_census.json (class census), f4_work/enj_routes.py + enj_routes_out.json (conjunction counts per route), f4_work/enj_engine_drive.py + enj_engine_drive_out.json (per-sleeve engine entries), f4_work/tensor_route.py + tensor_route_out.json (serving-route counts), f4_work/fail_direction.py (fail-direction proof), config/f4_variations_20261115.json (variation registry), tests/test_f4_routes_20261115_blockers.py (blockers), BUGLOG_2026-11-15.md FIX-F4-20261115-A/B/C.

