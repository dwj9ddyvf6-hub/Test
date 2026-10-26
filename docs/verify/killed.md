# Verification: Killed studies

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk); every other path is in this repository.

## [Golden cross (SPY)](../../strategies/killed/killed-golden-cross-spy.md)

| Rule | Read from |
|---|---|
| Entry: Long when SPY's 50-day SMA is above its 200-day SMA on the last completed session (a tie keeps the state); bought at the next session's first pass. | `sleeves/killed/daily.py:42-59`<br>`sleeves/killed/daily.py:82-101`<br>`sleeves/killed/common.py:114-123` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Flat when the 50-day is below the 200-day: sold at the next pass. | `sleeves/killed/daily.py:93`<br>`sleeves/killed/daily.py:102-107` |
| Sizing: All of the sleeve's equity; a $100,000 book. | `sleeves/killed/daily.py:100`<br>`sleeves/killed/common.py:32` |
| Data: SPY split-adjusted daily bars (320). | `sleeves/killed/daily.py:71-72` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |

## [Naive 20-day breakout](../../strategies/killed/killed-naive-20d-breakout.md)

| Rule | Read from |
|---|---|
| Entry: A close above the highest close of the prior 20 sessions (a tie is not a breakout) on the completed session; bought at the next session's first pass; a signal during a hold is skipped. | `sleeves/killed/daily.py:185-190`<br>`sleeves/killed/daily.py:206-224` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Sold market-on-close 20 sessions after the signal session. | `sleeves/killed/daily.py:221-224` |
| Sizing: $100,000 / 41 per position (fractional shares long; shorts in whole shares, at least 1). | `sleeves/killed/daily.py:202`<br>`sleeves/killed/daily.py:223`<br>`sleeves/killed/common.py:232-236` |
| Data: Split-adjusted daily bars (60). | `sleeves/killed/daily.py:201` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |
| Basket | `sleeves/killed/daily.py:18-26` |

## [RSI × OBV daily studies](../../strategies/killed/killed-rsiobv-daily.md)

| Rule | Read from |
|---|---|
| Entry: Divergence: two price pivots 5-60 bars apart that RSI (8 / 13 / 21) disagrees with (bullish regular: a lower low on a higher RSI low; bearish regular the mirror); STRONG at an RSI under 32 (over 68), SUPERSTRONG under 27 (over 73). | `sleeves/femto/vendor/old_desk_research/rsiobv.py:71-79`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:128-163`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:166-213`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:241-255`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:258-317` |
| Entry: Study A: four buckets per direction (all RSI, RSI and OBV agreeing over the same swings, strong regular RSI, RSI and OBV both in the top / bottom tenth of their 144-bar range), one signal per 20 bars; entry the next open, holds 5 / 10 / 20 sessions. | `sleeves/killed/daily.py:244-271`<br>`sleeves/killed/daily.py:323-334`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:320-360`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:365-420` |
| Entry: Study B: regular RSI divergences confirmed by a trendline break (a close, a wick, or two closes) within 5 bars; entry the next open, holds 5 / 10 / 20. | `sleeves/killed/daily.py:274-320`<br>`sleeves/killed/daily.py:335-348`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:429-458` |
| Entry: Study C: a strict 20-day closing high, alone or with RSI (8, 13 or 21) ≤ 30; long, out at the close 21 sessions after the signal. | `sleeves/killed/daily.py:349-358` |
| Entry: Bullish arms buy, bearish arms sell short. | `sleeves/killed/daily.py:407-409` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Each tranche sells or covers market-on-close at its hold. | `sleeves/killed/daily.py:408` |
| Sizing: $100,000 / 150 per tranche (fractional shares long; shorts in whole shares, at least 1). | `sleeves/killed/daily.py:382`<br>`sleeves/killed/daily.py:408`<br>`sleeves/killed/common.py:232-236` |
| Data: Closed daily bars (520). | `sleeves/killed/daily.py:380`<br>`sleeves/killed/daily.py:395-406` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |
| Long-only rail removed | `sleeves/killed/common.py:36-37` |
| Universe | `sleeves/killed/daily.py:233-234` |

## [Intraday momentum (Gao et al.)](../../strategies/killed/killed-intraday-momentum-gao.md)

| Rule | Read from |
|---|---|
| Entry: First-half-hour return: the 09:55 bar's close over the 09:30 open, minus 1, on 5-minute bars (all six first-window bars, with volume). | `sleeves/killed/intraday.py:25-36` |
| Entry: From 15:30 ET: long when it is positive, short when negative; no trade on half-days or a zero return. | `sleeves/killed/intraday.py:52`<br>`sleeves/killed/intraday.py:67-87` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Out market-on-close the same day. | `sleeves/killed/intraday.py:84` |
| Sizing: $50,000 per symbol, fractional shares on both sides. | `sleeves/killed/intraday.py:54`<br>`sleeves/killed/intraday.py:58`<br>`sleeves/killed/intraday.py:84` |
| Data: 5-minute bars (120) and quotes. | `sleeves/killed/intraday.py:55-56` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |
| Long-only rail removed | `sleeves/killed/common.py:36-37` |

## [RSI × OBV intraday (5-minute)](../../strategies/killed/killed-rsiobv-intraday.md)

| Rule | Read from |
|---|---|
| Entry: Divergence: two price pivots 5-60 bars apart that RSI (8 / 13 / 21) disagrees with (bullish regular: a lower low on a higher RSI low; bearish regular the mirror); STRONG at an RSI under 32 (over 68), SUPERSTRONG under 27 (over 73). | `sleeves/femto/vendor/old_desk_research/rsiobv.py:71-79`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:128-163`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:166-213`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:241-255`<br>`sleeves/femto/vendor/old_desk_research/rsiobv.py:258-317` |
| Entry: Bullish regular RSI divergences, STRONG or SUPERSTRONG, on the last 600 5-minute bars; one per name per 24 h; bought at the next regular-session pass. | `sleeves/killed/intraday.py:91-111`<br>`sleeves/killed/intraday.py:145-185`<br>`sleeves/killed/intraday.py:125` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Three tranches sell after 24, 48 and 96 bars past the signal bar. | `sleeves/killed/intraday.py:92`<br>`sleeves/killed/intraday.py:159-168` |
| Sizing: $100,000 / 24 per tranche (fractional shares). | `sleeves/killed/intraday.py:129`<br>`sleeves/killed/intraday.py:180`<br>`sleeves/killed/common.py:232-236` |
| Data: 5-minute bars (600). | `sleeves/killed/intraday.py:127` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |

## [Six short candidates](../../strategies/killed/killed-short-candidates.md)

| Rule | Read from |
|---|---|
| Entry: C1: the return since 14:00 (live price over the 13:30 bar's close) in the name's top fifth of the last 252 days (≥ 63 days): short market-on-close; cover at the next close (a) or the next open (b). | `sleeves/killed/intraday.py:205-227`<br>`sleeves/killed/intraday.py:374-393` |
| Entry: C2: the return since 15:00 in its top fifth: short market-on-close, cover at the next close. | `sleeves/killed/intraday.py:394-396` |
| Entry: C3: the close in the top 5% of its 20-day range and above the 20-day mean + 1.5 ATR(14): short market-on-close; cover at the close 3 sessions later (a), or at the first touch of the 20-day mean (b). | `sleeves/killed/intraday.py:230-263`<br>`sleeves/killed/intraday.py:368-372`<br>`sleeves/killed/intraday.py:397-413` |
| Entry: C4: two closes in a row in the top 20% of their day's range: short at the next open, cover at the close of the session after. | `sleeves/killed/intraday.py:266-268`<br>`sleeves/killed/intraday.py:340-348` |
| Entry: C5: a gap up ≥ 2% opening within 2% of the 252-day high: short at the open; cover at the end of the first 30 minutes, or earlier at the prior close (a). | `sleeves/killed/intraday.py:349-367` |
| Entry: C6: bearish regular RSI divergences, STRONG or SUPERSTRONG, on 30-minute bars, one per name per day: buy at the next pass, sell after 4, 8 or 16 bars. | `sleeves/killed/intraday.py:414-459` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Each arm's exit above; touch exits trade at the market when the live price reaches the level. | `sleeves/killed/intraday.py:358-372`<br>`sleeves/killed/common.py:226-229` |
| Sizing: $1,000 per tranche (fractional shares long; shorts in whole shares, at least 1). | `sleeves/killed/intraday.py:295`<br>`sleeves/killed/intraday.py:337`<br>`sleeves/killed/common.py:232-236` |
| Data: Regular-session 30-minute bars (3,400), split-adjusted daily bars (260), live quotes. | `sleeves/killed/intraday.py:292-294` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |
| Long-only rail removed | `sleeves/killed/common.py:36-37` |

## [Distance pairs](../../strategies/killed/killed-pairs-distance-coint.md)

| Rule | Read from |
|---|---|
| Entry: Formation, each half-year: listings with bars on ≥ 240/252 of the 12 formation months' sessions, median dollar volume ≥ $1M, median price ≥ $5 and every day present after bad-tick cleaning; the 20 pairs with the smallest sum of squared distances of normalized prices. | `sleeves/killed/feedlib/killed_data.py:286-291`<br>`sleeves/killed/feedlib/killed_data.py:294-303`<br>`sleeves/killed/feedlib/killed_data.py:306-355`<br>`sleeves/killed/feedlib/killed_data.py:370-399` |
| Entry: z = the normalized spread less its formation mean, over its formation σ, on the live prices once a day, 30-11 minutes before the close; \|z\| > 2 (V1: 2.5) buys the cheap leg and shorts the rich one, market-on-close. | `sleeves/killed/pairs.py:20-28`<br>`sleeves/killed/pairs.py:38-46`<br>`sleeves/killed/pairs.py:84-127`<br>`sleeves/killed/pairs.py:142-207`<br>`sleeves/killed/pairs.py:209-213`<br>`sleeves/killed/common.py:126-128` |
| Entry: V1 opens only when neither leg has a news item, an earnings date or an ex-dividend date from 5 sessions back to today. | `sleeves/killed/pairs.py:38-46`<br>`sleeves/killed/pairs.py:155-158`<br>`sleeves/killed/pairs.py:191-195`<br>`sleeves/killed/feedlib/killed_data.py:440-493`<br>`sleeves/killed/killed_studies.py:48` |
| Exit: \|z\| < 0.5 (converged), market-on-close; the base book also stops at \|z\| beyond 4 against the trade, V1 after 10 sessions; every pair closes on the window's last session; pairs may reopen. | `sleeves/killed/pairs.py:29-35`<br>`sleeves/killed/pairs.py:47-51`<br>`sleeves/killed/pairs.py:186-203`<br>`sleeves/killed/pairs.py:215-220` |
| Sizing: $5,000 per pair, $2,500 a leg; whole shares on the short leg. | `sleeves/killed/pairs.py:16-17`<br>`sleeves/killed/pairs.py:210-213`<br>`sleeves/killed/common.py:232-236` |
| Data: Daily adjusted closes (420) of the legs; NASDAQ Trader symbol directories. | `sleeves/killed/pairs.py:238`<br>`sleeves/killed/feedlib/killed_data.py:378-379` |
| Data: V1: Alpaca news (Yahoo RSS headlines without keys); Nasdaq earnings and dividend calendars. | `sleeves/killed/feedlib/killed_data.py:408-476` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |
| Long-only rail removed | `sleeves/killed/common.py:36-37` |
| Engle-Granger arm recorded only | `sleeves/killed/feedlib/killed_data.py:354-357`<br>`sleeves/killed/feedlib/killed_data.py:366` |
| Warm start for the base book only | `sleeves/killed/pairs.py:175-183` |

## [PEAD price surprise](../../strategies/killed/killed-pead-price-surprise.md)

| Rule | Read from |
|---|---|
| Entry: Surprise S: the adjusted close the session after the event over the close the session before, less SPY's same return; the event date from Nasdaq's earnings calendar. | `sleeves/killed/feedlib/killed_data.py:122-137`<br>`sleeves/killed/feedlib/killed_data.py:184-207` |
| Entry: Cohort: S above the 80th percentile of the previous calendar quarter's surprises; bought at the open two sessions after the event. | `sleeves/killed/feedlib/killed_data.py:157-164`<br>`sleeves/killed/feedlib/killed_data.py:213-249`<br>`sleeves/killed/events.py:33-42` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Four tranches, out market-on-close after 1, 5, 10 and 20 sessions (the entry session counted). | `sleeves/killed/events.py:8`<br>`sleeves/killed/events.py:39-42` |
| Sizing: $100,000 / 1,500 per tranche (fractional shares). | `sleeves/killed/events.py:25`<br>`sleeves/killed/events.py:41` |
| Data: Nasdaq earnings calendar, NASDAQ Trader listings, daily adjusted bars of the names and SPY. | `sleeves/killed/feedlib/killed_data.py:99-118`<br>`sleeves/killed/feedlib/killed_data.py:184-199` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |

## [Earnings-day overnight scalp](../../strategies/killed/killed-pead-spillover-scalp.md)

| Rule | Read from |
|---|---|
| Entry: The day's Nasdaq earnings-calendar names: live price / previous close - 1 - 0.15% > 0.01%; bought market-on-close. | `sleeves/killed/events.py:9`<br>`sleeves/killed/events.py:66-87`<br>`sleeves/killed/feedlib/killed_data.py:252-282`<br>`sleeves/killed/killed_studies.py:46` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Sold at the next session's open. | `sleeves/killed/events.py:77`<br>`sleeves/killed/events.py:84` |
| Sizing: $400 per trade ($100,000 / 250, fractional shares). | `sleeves/killed/events.py:59`<br>`sleeves/killed/events.py:84` |
| Data: Nasdaq earnings calendar, the previous session's daily close, live quotes (15:27-15:41 ET). | `sleeves/killed/feedlib/killed_data.py:252-282`<br>`sleeves/killed/killed_studies.py:46` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |

## [Small-cap high-beta beaten-down (52 weeks)](../../strategies/killed/killed-smcap-beta-52w.md)

| Rule | Read from |
|---|---|
| Entry: BEAT: the weekly close ≤ 80% of the 52-week high, or a 13-week return ≤ -20%. | `sleeves/killed/feedlib/killed_data.py:528-532` |
| Entry: SMALL: the bottom third of the week's qualifiers by 52-week mean weekly dollar volume. | `sleeves/killed/feedlib/killed_data.py:533`<br>`sleeves/killed/feedlib/killed_data.py:544-551` |
| Entry: HIBETA: the 52-week weekly beta > 1.2 (≥ 40 weeks). | `sleeves/killed/feedlib/killed_data.py:534-541`<br>`sleeves/killed/vendor/midna_research/run_smcap_beta_52w.py:66-74` |
| Entry: All three: bought at the next session's open. | `sleeves/killed/feedlib/killed_data.py:552-553`<br>`sleeves/killed/smcap.py:48-58` |
| Entry: Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close. | `sleeves/killed/common.py:33`<br>`sleeves/killed/common.py:126-133`<br>`sleeves/killed/common.py:238-286`<br>`sleeves/killed/common.py:346-347` |
| Exit: Sold market-on-close on the Friday 52 weeks later (the session before, on a holiday). | `sleeves/killed/smcap.py:10-15`<br>`sleeves/killed/smcap.py:57` |
| Sizing: $10,000 per name (fractional shares). | `sleeves/killed/smcap.py:39`<br>`sleeves/killed/smcap.py:57` |
| Data: The desk's weekly M2 qualifier file and merged weekly bars, SPY weekly. | `sleeves/killed/feedlib/killed_data.py:501-514`<br>`sleeves/killed/feedlib/killed_data.py:557-577` |
| Killed-study provenance | `sleeves/killed/common.py:29-31` |
| Beta orientation | `sleeves/killed/feedlib/killed_data.py:538-540`<br>`sleeves/killed/vendor/midna_research/run_smcap_beta_52w.py:66-74` |
