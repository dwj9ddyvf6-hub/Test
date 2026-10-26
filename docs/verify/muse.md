# Verification: Muse

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk), or at `22f3e991c224` where a cite names it (the four recorders converted into books on 2026-10-26); every other path is in this repository.

## [SATY day system (SPY 0DTE)](../../strategies/muse/muse-saty-day.md)

| Rule | Read from |
|---|---|
| Entry: Ladder: anchor = the prior regular-session close, unit = its daily ATR(14); levels at ±23.6, 38.2, 50, 61.8, 78.6 and 100% of the unit. | `sleeves/saty_day.py:115-120`<br>`sleeves/saty_day.py:216-242`<br>`sleeves/saty_day.py:308-313`<br>`sleeves/muse/core/saty_indicators.py:151-152`<br>`sleeves/muse/core/saty_indicators.py:166-167`<br>`sleeves/muse/core/saty_indicators.py:191-201` |
| Entry: Golden Gate: the first 1-minute touch of ±38.2% (or a fresh quote beyond it), taken within 30 minutes. | `sleeves/saty_day.py:132`<br>`sleeves/saty_day.py:603-616`<br>`sleeves/saty_day.py:715-730` |
| Entry: Gates: the last completed 1-hour Phase Oscillator past -61.8 blocks a long (past +61.8 a short) and past +61.8 tags a long Bilbo; the 10-minute Pivot Ribbon Pro fully against (EMA 8 < 21 and 13 < 48) or in chop blocks, except on a gap through the level at the open; QQQ must confirm (its last 10-minute close beyond its own 23.6%, or its 38.2% touched today). | `sleeves/saty_day.py:121`<br>`sleeves/saty_day.py:344-361`<br>`sleeves/saty_day.py:368-386`<br>`sleeves/saty_day.py:524-573`<br>`sleeves/saty_day.py:617-632`<br>`sleeves/muse/core/saty_indicators.py:376-377`<br>`sleeves/muse/core/saty_indicators.py:403-406` |
| Entry: Trigger Box: on a day opening within ±23.6%, the first completed 3-minute close beyond a trigger, within 30 minutes and until 90 minutes before the close; the same ribbon and chop vetoes. | `sleeves/saty_day.py:391-407`<br>`sleeves/saty_day.py:645-687` |
| Entry: Range scalp: once a completed hour shows the day's range ≤ 70% of the unit with its close inside the box (until an hourly range over 90% or a 10-minute close beyond ±61.8%), buys calls on a touch of -38.2% and puts on +38.2%. | `sleeves/saty_day.py:135-136`<br>`sleeves/saty_day.py:409-443`<br>`sleeves/saty_day.py:689-712` |
| Entry: Contract: today's SPY expiry, strike nearest the spot with a two-sided quote, spread ≤ 5% of mid, ≤ 60 s old; a limit at the mid; no same-day expiry is no trade. | `sleeves/saty_day.py:122-123`<br>`sleeves/saty_day.py:130`<br>`sleeves/saty_day.py:245-271`<br>`sleeves/saty_day.py:448-479`<br>`sleeves/saty_day.py:515-519` |
| Entry: Entries from 09:30 to an hour before the close, one position at a time, none once the day is down $10,000. | `sleeves/saty_day.py:131`<br>`sleeves/saty_day.py:1150-1176` |
| Exit: Golden Gate: a 10-minute close back through the 23.6% trigger exits; half at 50%; all at 61.8% unless Bilbo-tagged or the 10-minute ribbon is fully aligned, then half stays on, is halved again at 78.6% and goes at 100%. | `sleeves/saty_day.py:778-803`<br>`sleeves/saty_day.py:919-928`<br>`sleeves/saty_day.py:960-1000` |
| Exit: Trigger Box: a 3-minute close back through the trigger exits; half at 50%; all at 100% unless the ribbon is fully aligned, then half rides. | `sleeves/saty_day.py:892-901`<br>`sleeves/saty_day.py:931-958` |
| Exit: Range scalp: out at the opposite 38.2% level, or on a 10-minute close beyond the 61.8% level past the entry. | `sleeves/saty_day.py:902-918` |
| Exit: Exits are limits at the option's mid; flat from 5 minutes before the close (the bid from 3 minutes, market from 2); a position from an earlier session is sold at once. | `sleeves/saty_day.py:808-817`<br>`sleeves/saty_day.py:837-889` |
| Sizing: 4% of the $10,000 slice in premium (half for a long Golden Gate from 12:00), whole contracts, at least 1. | `sleeves/saty_day.py:124`<br>`sleeves/saty_day.py:481-485`<br>`sleeves/saty_day.py:633-634`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY and QQQ 5-minute bars (about 22,000) and 1-minute bars (1,200), IEX quotes, today's SPY option chain and quotes, the sleeve's own fills. | `sleeves/muse/muse.py:128-131`<br>`sleeves/saty_day.py:295-339`<br>`sleeves/saty_day.py:1029-1056` |
| Daily stop | `sleeves/saty_day.py:131`<br>`sleeves/saty_day.py:1161-1167`<br>`sleeves/muse/muse.py:106` |
| Warnings only | `sleeves/saty_day.py:1003-1027` |
| Desk flat | `sleeves/muse/muse.py:106`<br>`sleeves/muse/muse.py:99`<br>`sleeves/muse/muse.py:197-202`<br>`sleeves/muse/muse.py:517-518`<br>`sleeves/muse/muse.py:608-612` |
| Warmups: 100 daily bars, 250 ribbon and oscillator bars | `sleeves/muse/core/saty_indicators.py:53-54`<br>`sleeves/saty_day.py:1124-1135` |

## [Sol's Saty engine (SPY options)](../../strategies/muse/muse-saty-sol.md)

| Rule | Read from |
|---|---|
| Entry: Ladder: anchor = the prior regular-session close, unit = its daily ATR(14); x = the price's distance from the anchor in units, signed with the trade. | `sleeves/saty_sol.py:141-143`<br>`sleeves/saty_sol.py:227-257`<br>`sleeves/muse/core/saty_indicators.py:151-152`<br>`sleeves/muse/core/saty_indicators.py:166-167`<br>`sleeves/muse/core/saty_indicators.py:191-201` |
| Entry: Golden Gate (both sides): armed when the session opens with x < 0.382; the first cross of 0.382 by a 1-minute close or the live quote mid is the one chance; entered only with x still within 0.382-0.412 and the 0.618 target not yet printed. | `sleeves/saty_sol.py:144`<br>`sleeves/saty_sol.py:342-371`<br>`sleeves/saty_sol.py:613-665` |
| Entry: Trigger (calls only): on a session opening inside ±0.236, the first completed 3-minute close above +0.236; entered while price stays above the trigger, below +0.382 and within 0.03 ATR of that close. | `sleeves/saty_sol.py:667-707` |
| Entry: Each event is acted on only by the first pass that sees it (within 2 minutes), then spent; entries 09:35-14:30 and at least 90 minutes before the close; one position or working entry at a time, Golden Gate first. | `sleeves/saty_sol.py:152-158`<br>`sleeves/saty_sol.py:542-574`<br>`sleeves/saty_sol.py:641-646`<br>`sleeves/saty_sol.py:949-984` |
| Entry: Contract: the nearest expiry 2-4 calendar days out (today's in the 0DTE row), strike nearest the spot; its quote two-sided, spread ≤ 5% of mid, ≤ 60 s old; a limit at the ask. | `sleeves/saty_sol.py:146-147`<br>`sleeves/saty_sol.py:156`<br>`sleeves/saty_sol.py:260-285`<br>`sleeves/saty_sol.py:448-488`<br>`sleeves/saty_sol.py:520-540` |
| Exit: Golden Gate: all out at the first mark at x ≥ 0.618, or on a 10-minute close at x < 0.236 after the fill, whichever comes first (a tie is invalidation). | `sleeves/saty_sol.py:805-827` |
| Exit: Trigger: all out at the first mark at or above +0.382, or on a 3-minute close below +0.236 after the fill. | `sleeves/saty_sol.py:794-804`<br>`sleeves/saty_sol.py:817-827` |
| Exit: Exits are limits at the bid; liquidation from 10 minutes before the close (market with no quote); a position from an earlier session is sold at once. | `sleeves/saty_sol.py:155`<br>`sleeves/saty_sol.py:712-722`<br>`sleeves/saty_sol.py:762-788` |
| Sizing: Session premium budget: 0.5% of the $10,000 slice less premium already spent today; floor(budget / (100 × ask)) contracts, which can be 0 (no trade). | `sleeves/saty_sol.py:148`<br>`sleeves/saty_sol.py:303-309`<br>`sleeves/saty_sol.py:589-604`<br>`sleeves/saty_sol.py:881-883`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Sizing: A 1% daily loss (fills plus the open position at the bid) halts new entries for the session. | `sleeves/saty_sol.py:149`<br>`sleeves/saty_sol.py:399-426`<br>`sleeves/saty_sol.py:894-908`<br>`sleeves/saty_sol.py:959-961` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY 5-minute bars (about 22,000) and 1-minute bars (1,200), IEX quotes, the SPY option chain and quotes, the sleeve's own fills. | `sleeves/muse/muse.py:132-137`<br>`sleeves/saty_sol.py:318-340` |
| $50 budget | `sleeves/saty_sol.py:148`<br>`sleeves/saty_sol.py:303-309`<br>`sleeves/saty_sol.py:599-604`<br>`sleeves/muse/muse.py:109` |
| Tag only; experiments off | `sleeves/saty_sol.py:145`<br>`sleeves/saty_sol.py:171-173`<br>`sleeves/saty_sol.py:493-518` |
| 0DTE row | `sleeves/saty_sol_0dte.py:138`<br>`sleeves/saty_sol_0dte.py:467`<br>`sleeves/muse/muse.py:111-112`<br>`sleeves/muse/muse.py:99`<br>`sleeves/muse/muse.py:197-202`<br>`sleeves/muse/muse.py:517-518`<br>`sleeves/muse/muse.py:608-612` |

## [Saty Magnum (SPY shares)](../../strategies/muse/muse-saty-magnum.md)

| Rule | Read from |
|---|---|
| Entry: Ladder: anchor = the prior regular-session close, unit = its daily ATR(14); levels at ±23.6, 38.2, 50, 61.8, 78.6, 100, 123.6 and 200% of the unit. | `sleeves/saty_magnum.py:167-174`<br>`sleeves/saty_magnum.py:257-283`<br>`sleeves/saty_magnum.py:370-375` |
| Entry: Regime: trend up when both Pro ribbon clouds (EMA 8 ≥ 21, EMA 13 ≥ 48) are up on the daily and the 10-minute frames, trend down when all are down. | `sleeves/saty_magnum.py:465-503`<br>`sleeves/muse/core/saty_indicators.py:376-377`<br>`sleeves/muse/core/saty_indicators.py:403-406` |
| Entry: Arm A, Golden Gate: a completed 10-minute close through ±38.2% (cancelled by a 10-minute close back through the 23.6% trigger); within 60 minutes a completed 3-minute bar reaches the zone between the gate and the 10-minute EMA 21 and closes back beyond the gate, with ≥ 55% of its volume split on the trade's side; the regime in trend that way; the 10-minute oscillator not beyond ∓100 and the 1-hour not beyond ∓61.8. | `sleeves/saty_magnum.py:185`<br>`sleeves/saty_magnum.py:193`<br>`sleeves/saty_magnum.py:237-254`<br>`sleeves/saty_magnum.py:603-664`<br>`sleeves/saty_magnum.py:1376-1469`<br>`sleeves/muse/core/saty_indicators.py:109-133` |
| Entry: Arm B, compression release: 2+ consecutive completed 10-minute bars in Phase Oscillator compression, then the first bar out closing beyond the coil's range with the oscillator's colour agreeing; not against both 10-minute clouds or the opposite daily trend. | `sleeves/saty_magnum.py:192`<br>`sleeves/saty_magnum.py:675-723`<br>`sleeves/saty_magnum.py:1333-1371` |
| Entry: Arm C, snap-back (half size): the 3- and 10-minute oscillators below -100 and the 1-hour below -80 (mirror for shorts), the 3-minute oscillator already turning; one entry per episode. | `sleeves/saty_magnum.py:175-177`<br>`sleeves/saty_magnum.py:725-769`<br>`sleeves/saty_magnum.py:1299-1328` |
| Entry: Schedule: from 09:40 to 30 minutes before the close; Arms A and B stand down 11:30-13:30 and once the day's range reaches 90% of the unit; caps 2 Arm A, 1 Arm B, 1 Arm C per episode, 3 entries a session, one position at a time; a -1% session stops entries; events over 30 minutes old are skipped. | `sleeves/saty_magnum.py:183-194`<br>`sleeves/saty_magnum.py:825-834`<br>`sleeves/saty_magnum.py:1250-1294` |
| Entry: Orders: a limit at the ask (long) or bid (short) from an IEX quote ≤ 60 s old. | `sleeves/saty_magnum.py:178`<br>`sleeves/saty_magnum.py:350-365`<br>`sleeves/saty_magnum.py:788-804` |
| Exit: Arm A: a 10-minute close back through the 23.6% trigger exits; a third at 50%, a third at 61.8% (then a 10-minute close back through the entry exits the rest), the rest at 100% (123.6% when the next weekly-ladder level lies beyond it). | `sleeves/saty_magnum.py:878-888`<br>`sleeves/saty_magnum.py:987-1066` |
| Exit: Arm B: a 10-minute close through the coil's midpoint exits; thirds at 50% and 61.8% with the same break-even rule, half the runner at 100%, the rest at 200%. | `sleeves/saty_magnum.py:884-886`<br>`sleeves/saty_magnum.py:987-1066` |
| Exit: Arm C: out when the 10-minute oscillator is back to -23.6 (+23.6 for a short), on a 10-minute close beyond the opposite 23.6% trigger, or after 60 minutes. | `sleeves/saty_magnum.py:191`<br>`sleeves/saty_magnum.py:962-985` |
| Exit: Exits are limits at the bid (long) or ask (short); flat at market 5 minutes before the close; a position from an earlier session is sold at once. | `sleeves/saty_magnum.py:806-820`<br>`sleeves/saty_magnum.py:905-916`<br>`sleeves/saty_magnum.py:945-951` |
| Sizing: Risk 0.5% of the $10,000 slice to the invalidation level (the 23.6% trigger, the coil midpoint, or the opposite trigger for Arm C at half), capped at 25% of the slice in notional; whole shares, none under 1. | `sleeves/saty_magnum.py:181-182`<br>`sleeves/saty_magnum.py:774-786`<br>`sleeves/saty_magnum.py:1318-1319`<br>`sleeves/saty_magnum.py:1361`<br>`sleeves/saty_magnum.py:1460-1461`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY 5-minute bars (about 52,000, for the daily ribbon's warmup) and 1-minute bars (1,200), IEX quotes, ^VIX daily closes, the sleeve's own fills. | `sleeves/muse/muse.py:143-146`<br>`sleeves/muse/muse.py:223-224`<br>`sleeves/saty_magnum.py:292-323` |
| Context only | `sleeves/saty_magnum.py:396-421`<br>`sleeves/saty_magnum.py:1069-1094` |
| Desk numbers | `sleeves/saty_magnum.py:181-194` |
| Stations | `sleeves/saty_magnum.py:878-888` |

## [Saty research system v0.2 (SPY shares)](../../strategies/muse/muse-saty-gpt-v02.md)

| Rule | Read from |
|---|---|
| Entry: Ten setups on completed 10-minute SPY bars, named from Saty's vocabulary: three Vomy ribbon transitions (EMA 13, 48 and 21 rejections), Golden Gate, compression breakout and retest, pivot-ribbon pullback, ATR-level retest, and two countertrend reversals (pivot divergence; the Phase Oscillator leaving ±61.8). | `sleeves/muse/core/saty_gpt_v02/strategies.py:20-24`<br>`sleeves/muse/core/saty_gpt_v02/strategies.py:296-353`<br>`sleeves/muse/core/saty_gpt_v02/strategies.py:382-517`<br>`sleeves/saty_gpt_v02.py:104-115` |
| Entry: Golden Gate: in an EMA 8 > 21 > 48 stack, a close through ±38.2% of the day's ATR ladder, then a pullback to the gate or EMA 21 that holds EMA 48, then a close beyond that bar's extreme and EMA 8; targets 50% and 61.8%. | `sleeves/muse/core/saty_gpt_v02/strategies.py:322-335`<br>`sleeves/muse/core/saty_gpt_v02/strategies.py:489-498` |
| Entry: Every signal: a stop 0.1 ATR beyond its structure; the close within 0.4 ATR of the setup's anchor; net reward to the nearest level ahead ≥ 1.5 × net risk after a 2-cent round trip; good for 6 bars. | `sleeves/muse/core/saty_gpt_v02/strategies.py:230-264`<br>`sleeves/saty_gpt_v02.py:104-115` |
| Entry: Midna's enhancements (on): each setup runs its own lane and the largest net reward wins; refused when the 1-hour stack, phase and day anchor all oppose a reversal, a weaker opposite side, a candidate not from the latest bar, half the room to the first target already used at the quote, a spread over 2 cents, the target out of reach at 1 ATR a bar before the flat, or (down 1R) a trade worse than the day's best. | `sleeves/muse/core/saty_gpt_v02/midna_enhancements2.py:56-71`<br>`sleeves/muse/core/saty_gpt_v02/midna_enhancements2.py:131-153`<br>`sleeves/muse/core/saty_gpt_v02/midna_enhancements2.py:168-291`<br>`sleeves/saty_gpt_v02.py:749-772`<br>`sleeves/saty_gpt_v02.py:855-940` |
| Entry: At the quote (≤ 5 s old): the stop still valid, every target still ahead, chase ≤ 0.4 ATR, adverse gap ≤ 0.15 ATR, net R to the nearest target still ≥ 1.5; a limit at the ask (long) or bid (short). | `sleeves/muse/core/saty_gpt_v02/risk_lots.py:132-165`<br>`sleeves/saty_gpt_v02.py:965-987`<br>`sleeves/saty_gpt_v02.py:1025-1038` |
| Entry: Entries from the open to 20 minutes before the close, one position at a time, after 1,000 completed 10-minute and 1-hour bars. | `sleeves/saty_gpt_v02.py:81`<br>`sleeves/saty_gpt_v02.py:130-139`<br>`sleeves/saty_gpt_v02.py:695-705`<br>`sleeves/saty_gpt_v02.py:848-854`<br>`sleeves/muse/core/saty_gpt_v02/strategies.py:162-165` |
| Exit: Stop: the quote mid (else the last 10-minute close) at or through the stop sells everything. | `sleeves/saty_gpt_v02.py:381-403` |
| Exit: Targets in order: the first sells half the shares, each later one a quarter, keeping one share unless the lot is a single share. | `sleeves/muse/core/saty_gpt_v02/strategies.py:246-250`<br>`sleeves/saty_gpt_v02.py:404-426`<br>`sleeves/muse/core/saty_gpt_v02/risk_lots.py:168-198` |
| Exit: After a profitable partial the stop moves to the entry; after a completed target it trails 1 ATR behind the best price since entry; stops never loosen. | `sleeves/saty_gpt_v02.py:366-380`<br>`sleeves/muse/core/saty_gpt_v02/risk_lots.py:201-236` |
| Exit: Flat 10 minutes before the close; exits are limits at the bid (long) or ask (short). | `sleeves/saty_gpt_v02.py:130-139`<br>`sleeves/saty_gpt_v02.py:276-289`<br>`sleeves/saty_gpt_v02.py:389-394` |
| Sizing: Risk R = 0.25% of the session-start slice ($25 on $10,000) a trade, half for a countertrend setup, less as the day's loss nears 2R; shares = floor(risk / per-share risk), at most 100% of the slice in notional and the quoted size; none after a 2R loss or 3 entries in the session. | `sleeves/muse/core/saty_gpt_v02/risk_lots.py:46-67`<br>`sleeves/muse/core/saty_gpt_v02/risk_lots.py:72-129`<br>`sleeves/saty_gpt_v02.py:841-845`<br>`sleeves/saty_gpt_v02.py:988-995`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY 5-minute regular-session bars (about 34,000, built into 10-minute and 1-hour bars), SPY daily bars (200), IEX quotes ≤ 5 s old, the sleeve's own fills. | `sleeves/muse/muse.py:154-156`<br>`sleeves/saty_gpt_v02.py:211-229`<br>`sleeves/saty_gpt_v02.py:511-570` |
| Enhancement defaults | `sleeves/muse/core/saty_gpt_v02/midna_enhancements2.py:63-84` |
| Warmup | `sleeves/saty_gpt_v02.py:81`<br>`sleeves/saty_gpt_v02.py:695-705` |

## [Saty opportunity engine v0.3 (SPY shares)](../../strategies/muse/muse-saty-gpt-v03.md)

| Rule | Read from |
|---|---|
| Entry: Ten setups on completed 10-minute SPY bars, named from Saty's vocabulary: three Vomy ribbon transitions (EMA 13, 48 and 21 rejections), Golden Gate, compression breakout and retest, pivot-ribbon pullback, ATR-level retest, and two countertrend reversals (pivot divergence; the Phase Oscillator leaving ±61.8). Each family runs independently. | `sleeves/muse/core/saty_gpt_v03/strategies.py:23-27`<br>`sleeves/muse/core/saty_gpt_v03/strategies.py:602-620`<br>`sleeves/muse/core/saty_gpt_v03/strategies.py:695-722`<br>`sleeves/saty_gpt_v03.py:101-112` |
| Entry: Golden Gate: in an EMA 8 > 21 > 48 stack, a close through ±38.2% of the day's ATR ladder, then a pullback to the gate or EMA 21 that holds EMA 48, then a close beyond that bar's extreme and EMA 8; targets 50% and 61.8%. | `sleeves/muse/core/saty_gpt_v03/strategies.py:395-408`<br>`sleeves/muse/core/saty_gpt_v03/strategies.py:571-580` |
| Entry: Every signal: a stop 0.1 ATR beyond its structure; the close within 0.4 ATR of the setup's anchor; net reward to the nearest level ahead ≥ 1.5 × net risk after a 2-cent round trip; good for 6 bars. | `sleeves/muse/core/saty_gpt_v03/strategies.py:290-329`<br>`sleeves/saty_gpt_v03.py:101-112` |
| Entry: Ranking: net reward/risk to the first obstacle, then fit with the SPY / QQQ / IWM path regime (directional for trend setups, choppy for reversals), then chase room left, then age; only the top candidate's direction survives, an exact opposite tie waits. | `sleeves/muse/core/saty_gpt_v03/routing.py:96-128`<br>`sleeves/muse/core/saty_gpt_v03/routing.py:130-174`<br>`sleeves/saty_gpt_v03.py:75`<br>`sleeves/saty_gpt_v03.py:589-656` |
| Entry: At the quote (≤ 5 s old): the stop still valid, every target still ahead, chase ≤ 0.4 ATR, adverse gap ≤ 0.15 ATR, net R to the nearest target still ≥ 1.5; a limit at the ask (long) or bid (short). | `sleeves/muse/core/saty_gpt_v03/risk_lots.py:112-142`<br>`sleeves/saty_gpt_v03.py:754-763`<br>`sleeves/saty_gpt_v03.py:791-809` |
| Entry: Entries from the open to 30 minutes before the close, one position at a time, after 1,000 completed 10-minute and 1-hour bars. | `sleeves/saty_gpt_v03.py:78`<br>`sleeves/saty_gpt_v03.py:130-138`<br>`sleeves/saty_gpt_v03.py:666-673`<br>`sleeves/saty_gpt_v03.py:734-740` |
| Exit: Stop: a completed 10-minute close beyond the stop sells everything. | `sleeves/saty_gpt_v03.py:372-383` |
| Exit: Targets in order: the first sells half the shares, each later one a quarter (a 1-share lot closes whole). | `sleeves/saty_gpt_v03.py:384-405`<br>`sleeves/muse/core/saty_gpt_v03/risk_lots.py:145-158` |
| Exit: After the first scale-out the stop moves to the entry and trails 1 ATR behind the best price since entry; stops never loosen. | `sleeves/saty_gpt_v03.py:360-371`<br>`sleeves/muse/core/saty_gpt_v03/risk_lots.py:161-179` |
| Exit: Exits are limits at the bid (long) or ask (short). | `sleeves/saty_gpt_v03.py:306-319` |
| Sizing: Risk R = 0.25% of the session-start slice ($25 on $10,000) a trade, half for a countertrend setup; shares = floor(risk / per-share risk), at most 100% of the slice in notional; none after a 2R loss or 3 entries in the session. | `sleeves/muse/core/saty_gpt_v03/risk_lots.py:33-54`<br>`sleeves/muse/core/saty_gpt_v03/risk_lots.py:67-109`<br>`sleeves/saty_gpt_v03.py:723-731`<br>`sleeves/saty_gpt_v03.py:764-771`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY, QQQ and IWM 5-minute regular-session bars (about 34,000, built into 10-minute and 1-hour bars), SPY daily bars (200), IEX quotes ≤ 5 s old, the sleeve's own fills. | `sleeves/muse/muse.py:150-153`<br>`sleeves/saty_gpt_v03.py:243-257`<br>`sleeves/saty_gpt_v03.py:589-607` |
| No flat rule | `sleeves/saty_gpt_v03.py:130-138`<br>`sleeves/saty_gpt_v03.py:321-406`<br>`sleeves/muse/muse.py:117-118` |

## [PO10 extreme (QQQ)](../../strategies/muse/muse-po10-qqq.md)

| Rule | Read from |
|---|---|
| Entry: Signal: the first completed 10-minute bar closing between 09:30 and 11:00 ET with the Phase Oscillator above +100 (long) or below -100 (short); the oscillator runs on clock-aligned extended-hours bars (04:00-20:00). | `sleeves/muse/sleeves/po10_qqq.py:99-101`<br>`sleeves/muse/sleeves/po10_qqq.py:130-143`<br>`sleeves/muse/sleeves/po10_qqq.py:168-180`<br>`sleeves/muse/sleeves/po10_qqq.py:213-254` |
| Entry: Acted on within 30 minutes of that close; one entry a session, no re-entry after the exit. | `sleeves/muse/sleeves/po10_qqq.py:110`<br>`sleeves/muse/sleeves/po10_qqq.py:408-442` |
| Entry: A limit at the ask (long) or bid (short). | `sleeves/muse/sleeves/po10_qqq.py:444-476` |
| Exit: The first later 10-minute close beyond the opposite extreme; no stop and no target. | `sleeves/muse/sleeves/po10_qqq.py:183-192`<br>`sleeves/muse/sleeves/po10_qqq.py:275-298` |
| Exit: Flat at 15:59 ET (a minute before an early close); the master desk expires every entry at 15:55 ET first. | `sleeves/muse/sleeves/po10_qqq.py:102`<br>`sleeves/muse/sleeves/po10_qqq.py:120-127`<br>`sleeves/muse/sleeves/po10_qqq.py:294-295`<br>`sleeves/muse/muse.py:113`<br>`sleeves/muse/muse.py:99`<br>`sleeves/muse/muse.py:197-202`<br>`sleeves/muse/muse.py:517-518`<br>`sleeves/muse/muse.py:608-612` |
| Exit: Exits are limits at the bid (long) or ask (short). | `sleeves/muse/sleeves/po10_qqq.py:299-329` |
| Sizing: Two Micro NQ equivalents: shares = round($4 × NQ / QQQ) with NQ taken as QQQ × 41, which is always 164 shares; a $100,000 slice. | `sleeves/muse/sleeves/po10_qqq.py:103-109`<br>`sleeves/muse/sleeves/po10_qqq.py:146-165`<br>`sleeves/muse/sleeves/po10_qqq.py:444-446`<br>`sleeves/muse/muse.py:113` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: QQQ 5-minute bars (4,000) built into 10-minute bars, IEX quotes, the sleeve's own fills. | `sleeves/muse/muse.py:138-139`<br>`sleeves/muse/sleeves/po10_qqq.py:237-270` |
| QQQ for NQ | `sleeves/muse/sleeves/po10_qqq.py:106-109`<br>`sleeves/muse/sleeves/po10_qqq.py:146-148` |

## [Raschke PF3 momentum (SPY)](../../strategies/muse/muse-raschke-pf3.md)

| Rule | Read from |
|---|---|
| Entry: On completed regular-hours SPY 5-minute bars: ROC2 = close - close 2 bars back; Fast = SMA(3) - SMA(10) of closes; Slow = SMA(16) of Fast. | `sleeves/muse/sleeves/raschke_pf3.py:170-190`<br>`sleeves/muse/sleeves/raschke_pf3.py:212-229` |
| Entry: Long when all three rose on the last bar, short when all fell; only the first bar of a new aligned run, begun today, one attempt per run. | `sleeves/muse/sleeves/raschke_pf3.py:238-249`<br>`sleeves/muse/sleeves/raschke_pf3.py:298-319`<br>`sleeves/muse/sleeves/raschke_pf3.py:570-588` |
| Entry: Signal bars closing by 10 minutes before the close; marketable orders. | `sleeves/muse/sleeves/raschke_pf3.py:106`<br>`sleeves/muse/sleeves/raschke_pf3.py:589-593`<br>`sleeves/muse/sleeves/raschke_pf3.py:644-648`<br>`sleeves/muse/muse.py:625-626` |
| Exit: Stop 0.75 ATR(14) and target 1.5 ATR from the signal close, judged on completed-bar closes. | `sleeves/muse/sleeves/raschke_pf3.py:95-96`<br>`sleeves/muse/sleeves/raschke_pf3.py:438-448`<br>`sleeves/muse/sleeves/raschke_pf3.py:619-627` |
| Exit: Out when any of the three slopes turns against the position, or after 10 bars. | `sleeves/muse/sleeves/raschke_pf3.py:97`<br>`sleeves/muse/sleeves/raschke_pf3.py:449-462` |
| Exit: Flat 5 minutes before the close; a position from an earlier session is sold at once. | `sleeves/muse/sleeves/raschke_pf3.py:105`<br>`sleeves/muse/sleeves/raschke_pf3.py:392-410`<br>`sleeves/muse/sleeves/raschke_pf3.py:491-492` |
| Sizing: floor(0.5% of the $10,000 slice / (0.75 × ATR)) shares; none under 1. | `sleeves/muse/sleeves/raschke_pf3.py:99`<br>`sleeves/muse/sleeves/raschke_pf3.py:322-338`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY 5-minute bars (4,000). | `sleeves/muse/muse.py:157-158`<br>`sleeves/muse/sleeves/raschke_pf3.py:500-505` |
| Trend filter off | `sleeves/muse/sleeves/raschke_pf3.py:100`<br>`sleeves/muse/sleeves/raschke_pf3.py:341-349`<br>`sleeves/muse/sleeves/raschke_pf3.py:599-606` |

## [Raschke RRE adaptive desk (SPY)](../../strategies/muse/muse-raschke-rre.md)

| Rule | Read from |
|---|---|
| Entry: Today it trades nothing: the desk has no event calendar, so every bar's context is DATA_BLOCK and the router vetoes every candidate. | `sleeves/raschke_rre.py:141`<br>`sleeves/raschke_rre.py:502-507`<br>`sleeves/raschke_rre.py:534-547`<br>`sleeves/muse/core/raschke_rre/awareness.py:221-230`<br>`sleeves/muse/core/raschke_rre/router.py:111-115` |
| Entry: First cross: the slow line (16-bar average of SMA 3 - SMA 10) changes sign; within 12 bars (65 minutes), after the first pullback of the fast line, the first bar resuming sets a trigger one tick beyond the last pullback bar; a close at the trigger enters; stop 0.1 ATR beyond the pullback's extreme; a second pullback or a wick through the stop cancels. | `sleeves/muse/core/raschke_rre/raschke_core.py:301-310`<br>`sleeves/muse/core/raschke_rre/raschke_engine.py:307-312`<br>`sleeves/muse/core/raschke_rre/raschke_engine.py:362-424` |
| Entry: Failed break: in rotation (slow line within 0.15 ATR of zero, fast slope flipping twice in 6 bars), a bar sweeps a tick through the prior session's low and closes back above it (mirror at the high); VWAP must lie ahead. | `sleeves/muse/core/raschke_rre/raschke_engine.py:429-451` |
| Entry: Attempt: from 30 minutes after the open, the close within 0.2 ATR past the trigger, target = the nearer of 1.5R and the prior high / low / close (and VWAP), net R ≥ 1.2. | `sleeves/muse/core/raschke_rre/raschke_engine.py:453-486` |
| Entry: Admission: one thesis at a time, a 15-minute cooldown after flat, a marketable limit from an IEX quote ≤ 5 s old; longs only (no borrow check on the desk); the baseline RRE1 lane is journaled, never traded. | `sleeves/raschke_rre.py:121-134`<br>`sleeves/raschke_rre.py:360-388`<br>`sleeves/raschke_rre.py:653-674`<br>`sleeves/raschke_rre.py:707-771`<br>`sleeves/muse/core/raschke_rre/admission.py:301` |
| Exit: Quote-triggered stop and target, a 30-minute hold limit from the first fill, flat 5 minutes before the close; exits are limits at the bid. | `sleeves/raschke_rre.py:123`<br>`sleeves/raschke_rre.py:279-335` |
| Sizing: Whole shares, the least of: slice ÷ per-share loss, slice ÷ max(loss, $2), slice ÷ price, and half the quoted size ($10,000 slice); the desk's quotes carry no size, which leaves 0. | `sleeves/raschke_rre.py:134`<br>`sleeves/raschke_rre.py:721-748`<br>`sleeves/muse/core/raschke_rre/admission.py:277-285`<br>`sleeves/muse/core/raschke_rre/admission.py:315-323`<br>`sleeves/muse/muse.py:274-290`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Data: SPY 5-minute regular-session bars (5,000), IEX quotes, the sleeve's own fills. | `sleeves/muse/muse.py:159-161`<br>`sleeves/raschke_rre.py:243-258`<br>`sleeves/raschke_rre.py:405-419` |
| Event gates | `sleeves/raschke_rre.py:141`<br>`sleeves/raschke_rre.py:727-728`<br>`sleeves/muse/core/raschke_rre/admission.py:231-232` |
| Depth record | `sleeves/raschke_rre.py:734-737`<br>`sleeves/muse/core/raschke_rre/admission.py:320-323` |

## [15.87 Rule (SPY 0DTE)](../../strategies/muse/muse-em-1587.md)

| Rule | Read from |
|---|---|
| Entry: Map: EM = the prior SPY close × the prior VIX close / 15.87 %, rounded to 0.1; lines at the close ± EM (walls), ± EM/2 (shelves) and the close (magnet). | `sleeves/muse/core/em_1587.py:66-68`<br>`sleeves/muse/core/em_1587.py:97-135`<br>`sleeves/muse/core/em_1587.py:157-178`<br>`sleeves/em_1587.py:192-236` |
| Entry: Regime from the same VIX close: under 15 fade; 15-18.5 confirm; above 18.5 fast (break only, half size). | `sleeves/muse/core/em_1587.py:74-75`<br>`sleeves/muse/core/em_1587.py:111-119`<br>`sleeves/em_1587.py:563-574`<br>`sleeves/em_1587.py:626` |
| Entry: Break (confirm and fast): SPY and QQQ each close beyond their own 09:30-09:50 box on the same 5-minute bar by ≥ 0.05 × their EM; each box no wider than 0.2 × its EM; room to the next line > 0.8 points and ≥ 1R (the close to the box edge). | `sleeves/muse/core/em_1587.py:69-71`<br>`sleeves/muse/core/em_1587.py:76`<br>`sleeves/muse/core/em_1587.py:181-216`<br>`sleeves/muse/core/em_1587.py:243-308`<br>`sleeves/em_1587.py:114` |
| Entry: Fade (calm): the first bar whose range reaches a wall, long from the lower wall, short from the upper; a bar touching both stands down. | `sleeves/muse/core/em_1587.py:311-350` |
| Entry: Signal closes 09:50-11:05, acted on within 30 minutes; one setup a day. | `sleeves/muse/core/em_1587.py:79-80`<br>`sleeves/muse/core/em_1587.py:238-240`<br>`sleeves/em_1587.py:113`<br>`sleeves/em_1587.py:548-557`<br>`sleeves/em_1587.py:604-607` |
| Entry: Contract: today's SPY expiry, strike nearest the spot; its quote two-sided, spread ≤ 5% of mid, ≤ 60 s old; a limit at the mid. | `sleeves/em_1587.py:110-112`<br>`sleeves/em_1587.py:298-350`<br>`sleeves/em_1587.py:614-629`<br>`sleeves/em_1587.py:664-668` |
| Exit: Break: out when a bar reaches the next line, or on a 5-minute close back inside the SPY box (the target is checked first). | `sleeves/muse/core/em_1587.py:353-372`<br>`sleeves/em_1587.py:442-462` |
| Exit: Fade: out at the magnet, or on a 5-minute close beyond the wall by EM/2 (the stop is checked first). | `sleeves/muse/core/em_1587.py:173`<br>`sleeves/muse/core/em_1587.py:375-397`<br>`sleeves/em_1587.py:463-484` |
| Exit: Hard flat at 11:30 ET: a mid limit, the bid from 11:25, market from 11:28; a position from an earlier day is sold at once. | `sleeves/muse/core/em_1587.py:81`<br>`sleeves/em_1587.py:143-146`<br>`sleeves/em_1587.py:364-407`<br>`sleeves/em_1587.py:430-441` |
| Sizing: 4% of the $10,000 slice in premium (half in fast), whole contracts, at least 1. | `sleeves/em_1587.py:109`<br>`sleeves/em_1587.py:352-358`<br>`sleeves/em_1587.py:626-628`<br>`sleeves/muse/muse.py:105-124`<br>`sleeves/muse/muse.py:218-220`<br>`sleeves/muse/muse.py:403-406` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY and QQQ 5-minute bars (4,000), the prior ^VIX close (Yahoo daily), the SPY option chain with quotes, per-strike open interest. | `sleeves/muse/muse.py:140-142`<br>`sleeves/muse/muse.py:223-224`<br>`sleeves/em_1587.py:179-254` |
| SPX scale | `sleeves/muse/core/em_1587.py:76`<br>`sleeves/em_1587.py:114-115` |
| Open interest logged | `sleeves/em_1587.py:244-253` |

## [Shen first-touch fade (SPY 0DTE)](../../strategies/muse/muse-shen-fade.md)

| Rule | Read from |
|---|---|
| Entry: Levels, fixed at 09:29:30: the prior session's high and low, today's premarket high and low, and the three whole dollars nearest the last premarket close; levels within $0.10 merge. | `sleeves/femto/shen_fade.py:95`<br>`sleeves/femto/shen_fade.py:144-155`<br>`sleeves/femto/shen_fade.py:191-212`<br>`sleeves/femto/shen_fade.py:401-433`<br>`sleeves/femto/shen_fade.py:642-661` |
| Entry: Bias from that reference: above the prior high only puts, below the prior low only calls, otherwise both. | `sleeves/femto/shen_fade.py:158-164`<br>`sleeves/femto/shen_fade.py:180-188`<br>`sleeves/femto/shen_fade.py:763-768` |
| Entry: First touch only: the first completed 1-minute bar reaching a level's ±$0.10 zone burns it; RSI(14) on that bar's close above 70 buys puts, below 30 calls, otherwise nothing. | `sleeves/femto/shen_fade.py:80-81`<br>`sleeves/femto/shen_fade.py:113-141`<br>`sleeves/femto/shen_fade.py:167-177`<br>`sleeves/femto/shen_fade.py:215-219`<br>`sleeves/femto/shen_fade.py:670-683`<br>`sleeves/femto/shen_fade.py:741-762` |
| Entry: Contract: today's SPY expiry, strike nearest the touch bar's close, its quote two-sided, spread ≤ 5% of mid, ≤ 60 s old. | `sleeves/femto/shen_fade.py:83-84`<br>`sleeves/femto/shen_fade.py:328-351`<br>`sleeves/femto/shen_fade.py:365-396`<br>`sleeves/femto/shen_fade.py:771-779` |
| Entry: Order: a limit at the mid, at the ask from 60 seconds, cancelled at 180 seconds or once price leaves the zone or RSI leaves its extreme; entries 09:30-11:10, one position at a time. | `sleeves/femto/shen_fade.py:91-92`<br>`sleeves/femto/shen_fade.py:96`<br>`sleeves/femto/shen_fade.py:241-249`<br>`sleeves/femto/shen_fade.py:725-739`<br>`sleeves/femto/shen_fade.py:785-791`<br>`sleeves/femto/shen_fade.py:821-878` |
| Exit: Take profit: a resting limit at 1.20 × the premium paid; stop: the first pass with the option's mid at or under 0.85 ×, sold at the mid. | `sleeves/femto/shen_fade.py:87-88`<br>`sleeves/femto/shen_fade.py:222-226`<br>`sleeves/femto/shen_fade.py:495-532` |
| Exit: Flat at 11:15: a mid limit, then the bid, then market at 11:17. | `sleeves/femto/shen_fade.py:93-94`<br>`sleeves/femto/shen_fade.py:535-589`<br>`sleeves/femto/shen_fade.py:720-723` |
| Exit: New entries end for the day once realized P&L reaches -1.80% or +2.40% of the slice. | `sleeves/femto/shen_fade.py:89-90`<br>`sleeves/femto/shen_fade.py:425-431`<br>`sleeves/femto/shen_fade.py:700-718`<br>`sleeves/femto/shen_fade.py:731-733` |
| Sizing: 4% of the $10,000 slice in premium, whole contracts, at least 1. | `sleeves/femto/shen_fade.py:86`<br>`sleeves/femto/shen_fade.py:229-238`<br>`sleeves/femto/shen_fade.py:780`<br>`sleeves/muse/muse.py:147`<br>`sleeves/muse/muse.py:218-220` |
| Sizing: The master desk sends no entry costing more than the slice's free cash. | `sleeves/muse/muse.py:485-504` |
| Data: SPY 1-minute bars (2,400: the prior session, the premarket and today), today's SPY option chain with quotes, the sleeve's own fills. | `sleeves/muse/muse.py:147-149`<br>`sleeves/femto/shen_fade.py:610-640` |
| Ladder step 2 | `sleeves/femto/shen_fade.py:241-249` |
| Same-order rule | `sleeves/muse/muse.py:528`<br>`sleeves/muse/muse.py:534-538`<br>`sleeves/muse/muse.py:583-592` |
| Half days | `sleeves/femto/shen_fade.py:101-107`<br>`sleeves/femto/shen_fade.py:606-608` |

## [Band-touch RSI divergence](../../strategies/muse/muse-bb-rsi-divergence.md)

| Rule | Read from |
|---|---|
| Entry: Bars: completed regular-session 1-hour bars; a missing hour among the last 24, or a latest bar over 10 minutes old, blocks the symbol. | `sleeves/bb_rsi_divergence.py:49`<br>`sleeves/bb_rsi_divergence.py:90-128`<br>`sleeves/bb_rsi_divergence.py:569-597` |
| Entry: Setup: a pivot low (3 bars each side) at or below the lower Bollinger Band (20, 2), lower than the previous accepted pivot low 5-60 bars back, with RSI(14) (the lowest within a bar of the pivot) more than 2 points higher; acted on at the confirming bar, 3 bars after the pivot. | `sleeves/bb_rsi_divergence.py:28-40`<br>`sleeves/bb_rsi_divergence.py:131-180`<br>`sleeves/bb_rsi_divergence.py:210-230`<br>`sleeves/bb_rsi_divergence.py:317-398`<br>`pine/BB_RSI_Divergence_Indicator.pine:44-61`<br>`pine/BB_RSI_Divergence_Indicator.pine:94-117` |
| Entry: Order: a limit at the ask, rounded up to the cent, from a quote ≤ 60 s old with a spread ≤ 15 bps. | `sleeves/bb_rsi_divergence.py:47-48`<br>`sleeves/bb_rsi_divergence.py:466-493`<br>`sleeves/bb_rsi_divergence.py:792-803` |
| Entry: Stop = the pivot low - 0.5 ATR(14); target = the band's midline; reward/risk ≥ 1.2; candidates ranked by risk scale, reward/risk, RSI gap, touch depth, spread. | `sleeves/bb_rsi_divergence.py:42-43`<br>`sleeves/bb_rsi_divergence.py:803-841` |
| Exit: A bar's low at the stop (checked first) or high at the target. | `sleeves/bb_rsi_divergence.py:719-725`<br>`sleeves/bb_rsi_divergence.py:893-905` |
| Exit: After 24 hourly bars, or on a bearish upper-band divergence (the mirror setup). | `sleeves/bb_rsi_divergence.py:44`<br>`sleeves/bb_rsi_divergence.py:400-462`<br>`sleeves/bb_rsi_divergence.py:709-735` |
| Exit: Exit orders carry no limit; a working exit blocks new orders. | `sleeves/bb_rsi_divergence.py:670-757` |
| Sizing: 0.25% of equity at risk × a risk scale, capped at 5% of equity in notional; whole shares. | `sleeves/bb_rsi_divergence.py:45-46`<br>`sleeves/bb_rsi_divergence.py:843-855` |
| Sizing: Risk scale = a volatility scale (1 / √(ATR% over its 60-bar median), 0.5-1) × 0.5 when walking the band against the trade (12-bar efficiency ≤ -0.55 with 2 of the last 4 closes beyond the band), at least 0.25. | `sleeves/bb_rsi_divergence.py:243-314` |
| Data: 1-hour bars, latest quotes, the session's fills and orders. | `sleeves/bb_rsi_divergence.py:599-668`<br>`sleeves/bb_rsi_divergence.py:759-777` |
| Indicator outputs | `pine/BB_RSI_Divergence_Indicator.pine:142-165` |
| Expansion switch | `sleeves/bb_rsi_divergence_expanded.py:100-108` |
| Expanded universe | `sleeves/bb_rsi_divergence_expanded.py:38-57` |
| Expanded caps | `sleeves/bb_rsi_divergence_expanded.py:61`<br>`sleeves/bb_rsi_divergence_expanded.py:1079-1103` |
| Expanded shorts | `sleeves/bb_rsi_divergence_expanded.py:543-546`<br>`sleeves/bb_rsi_divergence_expanded.py:1116-1127`<br>`sleeves/bb_rsi_divergence_expanded.py:839-874` |
| Expanded window | `sleeves/bb_rsi_divergence_expanded.py:1084-1114` |
| v2.2 window and one entry a session | `sleeves/bb_rsi_divergence.py:50-51`<br>`sleeves/bb_rsi_divergence.py:759-770`<br>`sleeves/bb_rsi_divergence.py:786-791` |

## [Trullas divergence (QQQ 1-minute)](../../strategies/muse/muse-trullas-divergence.md)

| Rule | Read from |
|---|---|
| Entry: Pivots: a bar strictly highest (or lowest) over 5 bars each side, usable once those 5 bars have closed; regular-session bars with volume. | `sleeves/trullas_divergence.py:43`<br>`sleeves/trullas_divergence.py:98-121`<br>`sleeves/trullas_divergence.py:168-183` |
| Entry: Setup: two consecutive same-kind pivots of one day, 10-120 bars apart, with price diverging from the MACD(12, 26, 9) line (required); RSI(14) divergence and lower volume on the second extreme add to the count (1-3). | `sleeves/trullas_divergence.py:44-47`<br>`sleeves/trullas_divergence.py:124-165`<br>`sleeves/trullas_divergence.py:186-220` |
| Entry: Trigger (bearish): A = the lowest low between the highs, B = the second high; entry when price trades through B - 0.236 × (B - A) - 1 tick; bullish mirrored; the day's newest untraded setup is the one pending. | `sleeves/trullas_divergence.py:48-49`<br>`sleeves/trullas_divergence.py:221-240`<br>`sleeves/trullas_divergence.py:298-320`<br>`sleeves/trullas_divergence.py:352-359` |
| Entry: Cancelled after 30 bars or by a trade more than a tick beyond B; entries 09:30-11:00 ET, at most 5 a day, none after a -0.75% day. | `sleeves/trullas_divergence.py:52-57`<br>`sleeves/trullas_divergence.py:322-350` |
| Exit: Stop one tick beyond B, checked before the targets on the same bar. | `sleeves/trullas_divergence.py:227-228`<br>`sleeves/trullas_divergence.py:237-238`<br>`sleeves/trullas_divergence.py:419-429` |
| Exit: TP1 at 38.2%: half off and the stop to the entry; TP2 at 61.8%: the rest. | `sleeves/trullas_divergence.py:50-51`<br>`sleeves/trullas_divergence.py:430-456` |
| Exit: Flat at 12:00 ET. | `sleeves/trullas_divergence.py:55`<br>`sleeves/trullas_divergence.py:289-296`<br>`sleeves/trullas_divergence.py:411-418` |
| Sizing: Divergence count × 0.25% of the slice at risk to the stop, capped at 25% of the slice in notional; whole shares. | `sleeves/trullas_divergence.py:58-59`<br>`sleeves/trullas_divergence.py:361-368` |
| Data: QQQ 1-minute bars. | `sleeves/trullas_divergence.py:274-275` |
| Not installed on the master desk | `sleeves/muse/muse.py:163-166` |
