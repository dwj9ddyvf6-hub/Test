# KG-6: THE ENJ CLASS, CURED BY THE THIRD ROUTE

22 of 22 ENJ sleeves are newly graded in this lane (2 REPLAY-SCORED, 8 REPLAY-INDICATIVE, 12 REPLAY-NO-FIRE, 0 EXECUTION-IMPOSSIBLE), every one of them previously EXECUTION-IMPOSSIBLE in Unblock Lane 2 for a single reason: no ENJ bars existed in any cache on the box, and both of Lane 2's routes needed that same absent series; the third route sourced the series publicly (Kraken public OHLC API, pair ENJUSD, interval 240 (4h), HTTP 200; 720 complete 4H bars, 2026-07-18T16:00Z..2026-11-15T12:00Z), the in-progress candle at fetch time dropped. This is the same Kraken spot ENJ/USD tape the desk's own KrakenProducer serves live under ENJ/USD|4Hour (desk3/crypto_bars.py), so the replay feed's provenance matches the sleeves' live feed. Evidence class is REPLAY on every row; nothing is blended with LIVE-RECORD grades.

## POTENTIAL EDGE FOUND

**The ENJ breakout stream is positive and direction-certified.** aster_r19_enjusdt_breakout_base (both sizing variants, one stream): 11 entries on 10 dates over the served window; fwd10 excess vs QQQ +558.3bp (n=6 priceable at that horizon, t=1.81), inversion -392.8bp. It is the only ENJ stream clearing the REPLAY-SCORED bar and the only positive lead at the n>=5 floor. Cheapest forward check: the sleeve's logic runs on the live Kraken ENJ/USD tape; arm as shadow and grade the first 10 resolved entries.

**The funding sign split the absorption stream exactly.** The r19 absorption base stream fired 4 entries; with OKX funding served, the negative-funding arm took exactly 2 and the nonnegative-funding arm exactly the other 2. The split is an internal consistency proof that the funding input was delivered correctly to the funding-filtered families. In Lane 2 those families could only fail closed for want of any funding series.

**The squeeze family's entry condition is counter-cyclical on this tape (a negative-space finding, printed not buried).** All 10 funding-squeeze sleeves (7 batch8 nfs arms + 3 batch7 r19 arms) executed cleanly and fired zero times: their shared entry conjunction (funding < 0 AND a 20-bar breakout close) occurred 0 times in 420 eval bars. Funding was negative on 74 bars and breakouts occurred on 20, with zero overlap (hand-recounted against the engines' own entry definitions). On a tape where ENJ fell from $0.0276 to $0.0190, breakouts clustered in positive-funding relief moves. The family is not broken; its condition simply never occurred. Its forward check is free: the first live bar where funding prints negative into a 20-bar breakout is its first-ever test.

## ROUTES TRIED

Bars, in the task's order: (1) Kraken public OHLC API, LANDED, HTTP 200, error field [], 721 candles returned (720 complete). CoinGecko, Binance klines and Coinbase candles were not needed and were not called; the order was to stop at the first landed route. Funding (the Aster engines' declared second input; Lane 2 had no funding series at all): (1) Binance fapi fundingRate?symbol=ENJUSDT, HTTP 451, restricted location (the same block the desk's vendor file records for this sleeve family); (2) Bybit v5 funding history, HTTP 403, CloudFront geo-block; (3) OKX public funding-rate-history, ENJ-USDT-SWAP, LANDED, HTTP 200, 584 observations 2026-08-10T12:00Z..2026-11-15T16:00Z after one pagination step, served latest-as-of each bar's close. OKX coverage starts 2026-08-10, before the first eval bar (2026-09-06), so every eval carried an observed funding rate; 124 of 584 observations are negative.

## TIER CENSUS

- REPLAY-SCORED: 2
- REPLAY-INDICATIVE: 8
- REPLAY-NO-FIRE: 12
- EXECUTION-IMPOSSIBLE: 0

Tier bar (Lane 2 / Campaign 1, pre-registered): >=10 priceable entries on >=3 distinct entry dates = REPLAY-SCORED; any priceable entry below it = REPLAY-INDICATIVE; a clean run with zero entries = REPLAY-NO-FIRE; a run that could not execute = EXECUTION-IMPOSSIBLE. Every sleeve ran 420 evaluations (bars 300..719 of the served series, Lane 2's warmup convention) with zero evaluation errors and no fatal.

## PER-SLEEVE GRADES (primary stream: base)

| sleeve | tier | entries | dates | fwd1 excess | fwd3 excess | fwd5 excess | fwd10 excess |
|---|---|---|---|---|---|---|---|
| aster_abs_enj_4h | REPLAY-INDICATIVE | 4 | 4 | +161.4bp (n=2, t=0.49) | -257.9bp (n=2, t=-0.57) | +615.7bp (n=1, t=None) | +32.2bp (n=1, t=None) |
| aster_enj_nfs_fixed96_vol | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_enj_nfs_lost_full | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_enj_nfs_lost_vol | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_enj_nfs_norm_full | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_enj_nfs_norm_vol | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_enj_nfs_normfail_full | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_enj_nfs_normfail_vol | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_pub_enj_iu_body | REPLAY-INDICATIVE | 3 | 3 | -37.7bp (n=2, t=-10.35) | -1191.5bp (n=1, t=None) | -492.7bp (n=1, t=None) | n/a |
| aster_r19_enjusdt_absorption_base_fixed16_fullcash | REPLAY-INDICATIVE | 4 | 4 | +161.4bp (n=2, t=0.49) | -257.9bp (n=2, t=-0.57) | +615.7bp (n=1, t=None) | +32.2bp (n=1, t=None) |
| aster_r19_enjusdt_absorption_base_fixed16_volume1pct | REPLAY-INDICATIVE | 4 | 4 | +161.4bp (n=2, t=0.49) | -257.9bp (n=2, t=-0.57) | +615.7bp (n=1, t=None) | +32.2bp (n=1, t=None) |
| aster_r19_enjusdt_absorption_negative_funding_fixed16_fullcash | REPLAY-INDICATIVE | 2 | 2 | -168.4bp (n=1, t=None) | n/a | n/a | n/a |
| aster_r19_enjusdt_absorption_negative_funding_fixed16_volume1pct | REPLAY-INDICATIVE | 2 | 2 | -168.4bp (n=1, t=None) | n/a | n/a | n/a |
| aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_fullcash | REPLAY-INDICATIVE | 2 | 2 | +491.2bp (n=1, t=None) | -257.9bp (n=2, t=-0.57) | +615.7bp (n=1, t=None) | +32.2bp (n=1, t=None) |
| aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_volume1pct | REPLAY-INDICATIVE | 2 | 2 | +491.2bp (n=1, t=None) | -257.9bp (n=2, t=-0.57) | +615.7bp (n=1, t=None) | +32.2bp (n=1, t=None) |
| aster_r19_enjusdt_breakout_base_fixed16_fullcash | REPLAY-SCORED | 11 | 10 | -211.6bp (n=7, t=-1.36) | +8.7bp (n=7, t=0.04) | -528.8bp (n=6, t=-3.11) | +558.3bp (n=6, t=1.81) |
| aster_r19_enjusdt_breakout_base_fixed16_volume1pct | REPLAY-SCORED | 11 | 10 | -211.6bp (n=7, t=-1.36) | +8.7bp (n=7, t=0.04) | -528.8bp (n=6, t=-3.11) | +558.3bp (n=6, t=1.81) |
| aster_r19_enjusdt_negative_funding_squeeze_fixed16_fullcash | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_r19_enjusdt_negative_funding_squeeze_fixed16_volume1pct | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| aster_r19_enjusdt_negative_funding_squeeze_fixed96_fullcash | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| free_kraken_enj_spot | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |
| fwd_alpaca_enj_iu_body | REPLAY-NO-FIRE | 0 | 0 | n/a | n/a | n/a | n/a |

Sizing variants of one stream (fullcash / volume1pct) print identical grades where the stream is identical; they are two register rows because they are two sleeves, and the stream is counted once in the leads. Grades are forward returns on the daily resample of the served 4H tape vs QQQ daily closes, Lane C's machinery (unblock2_grade), horizons in days.

## NO-FIRE CAUSES (12)

- **Funding-squeeze conjunction never occurred (10: the 7 aster_enj_nfs_* arms + the 3 r19 squeeze arms).** See the negative-space finding above; hand-verified against both engines' entry code.
- **free_kraken_enj_spot (1).** Executed cleanly on the served bars. Its entries require the Kraken top-10 order book (spread <= 50bp and bid/ask depth ratio >= 2.0), a live snapshot input that no public route archives historically. No book was served: serving today's book across 420 historical bars would fabricate the input. The remaining gap is named exactly: historical book depth, which is not a bar series and is outside this lane's third route.
- **fwd_alpaca_enj_iu_body (1).** Monitor by design: the vendor signal returns [] unconditionally, preserving the source ruling (ENJ/USD unlisted at Alpaca, provider-proven 2026-10-24; LIST_ERROR carried verbatim in the sleeve). Executed cleanly; NO-FIRE is its designed state, not a data gap.

## METHOD AND HONESTY NOTES

- Harness: Lane 2's replay driver, adapted only in the BAR4H branch (ENJ series mapping, alias set ENJUSDT|4Hour / ENJ/USD|4Hour / ENJUSD|4Hour / ENJUSD|240Min, funding view key, provenance stamp). Positions fed back from a simulated book; the sleeves' own modules and exit logic produced every entry and exit (breakout 11 of 11 entries also exited in-replay, batch1 absorption 4 of 4, pub 3 of 3; the r19 absorption base stream closed 3 of 4 with one position open at the tape's end the engines' fixed-horizon exits, not grader inventions). Lane C's register carries no exit params for these 22 sleeves, so grade_stream produced no exit-path sims for them; the variation set in each register row is base + inversion + time-of-day, the same stream-level set Lane 2 graded.
- Provenance differences vs the ADA/LINK replay, printed: the ADA/LINK tapes were Kraken perp (PF_) series; the ENJ series is Kraken SPOT, which is the ENJ sleeves' actual live feed (crypto_bars.py deliberately refuses PF_ series as spot signal bars). The funding series is OKX's ENJ-USDT-SWAP print; the sleeves' live funding producer is Coinalyze. The funding filters consume only the rate's sign and the squeeze entry only its negativity, so venue basis in the rate's magnitude does not enter any grade; the substitution is named here rather than silently blended.
- Span limit: Kraken's public OHLC returns at most 720 candles per pair/interval, so the ENJ tape covers 120 days against the ADA/LINK tapes' ~342. Grades rest on 420 eval bars (2026-09-06..2026-11-15). fwd10 is priceable for 6 of the breakout stream's 11 entries; later entries run off the tape's end, the same truncation Lane 2 printed for its streams.
- Excess benchmark is QQQ daily closes, Lane C's convention for every replay stream including the PF crypto streams; the raw (non-excess) profiles are in the register beside the excess ones.

STATUS: GREEN. 22 of 22 formerly EXECUTION-IMPOSSIBLE ENJ sleeves carry a REPLAY grade in KG-6-REGISTER.jsonl (recounted from the register: 2 REPLAY-SCORED, 8 REPLAY-INDICATIVE, 12 REPLAY-NO-FIRE, 0 EXECUTION-IMPOSSIBLE), every run 420 clean evaluations on the Kraken spot series whose fetch is recorded above; the one input this lane could not source, historical Kraken book depth for free_kraken_enj_spot, is named in its row and above, and fwd_alpaca_enj_iu_body's NO-FIRE is its designed monitor state. The unproven portion is forward validity: every grade is a replay result on a 120-day tape, and the breakout lead's arming check is the named shadow run.
