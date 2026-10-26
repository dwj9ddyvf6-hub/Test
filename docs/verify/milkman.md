# Verification: Milkman

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk); every other path is in this repository.

## [Connors Double 7](../../strategies/milkman/mk-connorsdouble7.md)

| Rule | Read from |
|---|---|
| Entry: Long: the close above its 200-day SMA and the lowest of the last 7 closes; short: below the SMA200 and the highest of 7; at the close. | `sleeves/milkman/rules.py:149-158`<br>`sleeves/milkman/daily.py:65`<br>`sleeves/milkman/vendor/milkman/dstrats.py:14-18` |
| Entry: One trade at a time per symbol and side. | `sleeves/milkman/rules.py:96-98`<br>`sleeves/milkman/rules.py:149` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Exit: At the first close that is the highest of the last 7 (short: the lowest), or after 60 sessions, at the close. | `sleeves/milkman/rules.py:138-148`<br>`sleeves/milkman/vendor/milkman/dlib.py:28-40` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| Connors Double 7 in the study's code | `sleeves/milkman/vendor/milkman/dstrats.py:13-14` |

## [Legend's Buy Day](../../strategies/milkman/mk-legendsbuyday.md)

| Rule | Read from |
|---|---|
| Entry: Overnight leg: after exactly 3 lower closes in a row, buys at the close (short lane: after exactly 3 higher closes, shorts). | `sleeves/milkman/rules.py:172-190`<br>`sleeves/milkman/daily.py:66` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Entry: Day leg (SPY, long only): after exactly 4 sessions that each made a lower low than the one before (the one before them did not), buys the next open if it is under the prior close + 0.15 × ATR (the mean of the last 20 daily ranges) and above the stop. | `sleeves/milkman/rules.py:709-732`<br>`sleeves/milkman/daily.py:168` |
| Exit: Overnight leg: sold at the next open. | `sleeves/milkman/rules.py:165-170` |
| Exit: Day leg: stop one cent under the prior day's low; otherwise sold at that session's close. | `sleeves/milkman/rules.py:717-718`<br>`sleeves/milkman/rules.py:734-746` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| His page and package for the day leg | `sleeves/milkman/rules.py:702-706`<br>`sleeves/milkman/daily.py:156-161` |
| Named divergence: SPY for ES | `sleeves/milkman/daily.py:165-167` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:38` |

## [Weekday open-to-close (Monday)](../../strategies/milkman/mk-weekdayopentocloseproxy.md)

| Rule | Read from |
|---|---|
| Entry: Every Monday: enters at the open of each of the 14 index instruments. | `sleeves/milkman/rules.py:194-205`<br>`sleeves/milkman/daily.py:67`<br>`sleeves/milkman/daily.py:84` |
| Exit: Out at that session's close, market-on-close. | `sleeves/milkman/rules.py:207-212`<br>`sleeves/milkman/daily.py:612-622` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:645-661` |
| Long and short run as separate rows since 2026-10-19 (netted in one sleeve they always cancelled) | `sleeves/milkman/daily.py:176-186` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:68` |

## [Daily Bilbo Box](../../strategies/milkman/mk-dailybilbobox.md)

| Rule | Read from |
|---|---|
| Entry: Squeeze (Saty's compression): the 21-day, 2-sd Bollinger band inside 2 × ATR(14) around EMA(21), not while the gap widens inside 1.854 × ATR. | `sleeves/milkman/vendor/milkman/mlib.py:19-27`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Entry: Box: the high and low of a squeeze's first 5 bars (fewer if it ends sooner), locked at the 5th bar or at its end. | `sleeves/milkman/rules.py:287-318`<br>`sleeves/milkman/rules.py:336-340`<br>`sleeves/milkman/daily.py:68` |
| Entry: For 20 bars after the lock: buys when the high reaches the box high with the prior close above EMA(21) (short: the low through the box low, the prior close below EMA21), at max(open, box high); void once the other side is reached first. | `sleeves/milkman/rules.py:219-260`<br>`sleeves/milkman/rules.py:325-326` |
| Entry: One trade at a time per symbol and side. | `sleeves/milkman/rules.py:217`<br>`sleeves/milkman/rules.py:254` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Exit: Stop at the box's other side, ratcheted each bar to the prior bar's EMA(50), never back; the entry bar stops only on a close through it; out after 250 bars. | `sleeves/milkman/rules.py:222-228`<br>`sleeves/milkman/rules.py:262-285`<br>`sleeves/milkman/rules.py:327-333` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| Saty's indicators, ported from his public scripts | `sleeves/milkman/vendor/milkman/mlib.py:1-2`<br>`sleeves/milkman/vendor/milkman/mlib.py:20` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:43` |

## [Swing Golden Gate (monthly ATR)](../../strategies/milkman/mk-swinggoldengatemonthly.md)

| Rule | Read from |
|---|---|
| Entry: Levels from last month's close (PC) and the monthly ATR(14): gate PC ± 0.382 ATR, entry ± 0.618, target ± 1.0, stop PC. | `sleeves/milkman/vendor/milkman/dstrats.py:78-86`<br>`sleeves/milkman/rules.py:360-370`<br>`sleeves/milkman/daily.py:69` |
| Entry: The month's first gate touch decides: it arms only with ≥ 4 sessions left in the month, the prior close on the other side of EMA(21) (below it for a long, above for a short) and the liquidity gate. | `sleeves/milkman/rules.py:372-381`<br>`sleeves/milkman/rules.py:403-407` |
| Entry: Armed: a resting stop entry at the 61.8% level until the month's last session. | `sleeves/milkman/rules.py:408-416` |
| Exit: Target or stop by touch (on the entry bar the stop counts only on a close through it); otherwise flat at the month's last close. | `sleeves/milkman/rules.py:384-399`<br>`sleeves/milkman/rules.py:417-434` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:42`<br>master-desk `docs/research/2026-10-19-milkman/REVIEW.md:53` |

## [Multi-day Golden Gate (weekly ATR)](../../strategies/milkman/mk-multidaygoldengateweekly.md)

| Rule | Read from |
|---|---|
| Entry: Levels from last week's close (PC) and the weekly ATR(14): entry at the gate, PC ± 0.382 ATR; target ± 0.618; stop PC. | `sleeves/milkman/vendor/milkman/dstrats.py:78-86`<br>`sleeves/milkman/rules.py:360-370`<br>`sleeves/milkman/daily.py:70-71` |
| Entry: The week's first gate touch decides: it trades only with the prior bar's Phase Oscillator above 61.8 (long) or below -61.8 (short) and the liquidity gate. | `sleeves/milkman/rules.py:372-381`<br>`sleeves/milkman/rules.py:403-416` |
| Entry: Phase Oscillator = EMA(3) of (close - EMA21) / (3 × ATR14) × 100. | `sleeves/milkman/vendor/milkman/mlib.py:16-18` |
| Exit: Target or stop by touch (on the entry bar the stop counts only on a close through it); otherwise flat at the week's last close. | `sleeves/milkman/rules.py:384-399`<br>`sleeves/milkman/rules.py:417-434` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:58` |

## [EMA21 deviation reversion](../../strategies/milkman/mk-ema21deviationreversion.md)

| Rule | Read from |
|---|---|
| Entry: Deviation = (close - EMA21) / ATR(14); long when it first reaches -k or below (short: +k or above), at the close; ≥ 30 bars. | `sleeves/milkman/rules.py:464-479`<br>`sleeves/milkman/vendor/milkman/dstrats.py:125-129` |
| Entry: One trade at a time per symbol and lane. | `sleeves/milkman/rules.py:450`<br>`sleeves/milkman/rules.py:472` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Exit: At a touch of the prior bar's EMA21 (or the open beyond it), else at the close after the hold. | `sleeves/milkman/rules.py:452-471`<br>`sleeves/milkman/rules.py:481-484` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| Cells: the study's plateau picks | `sleeves/milkman/daily.py:76-78` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:62` |

## [Phase Oscillator zone exit](../../strategies/milkman/mk-phaseoscillatorzoneexit.md)

| Rule | Read from |
|---|---|
| Entry: Phase Oscillator = EMA(3) of (close - EMA21) / (3 × ATR14) × 100. | `sleeves/milkman/vendor/milkman/mlib.py:16-18` |
| Entry: Accumulation: crosses up through -61.8 (short: down through +61.8); extreme: through -100 (+100); at the close; ≥ 30 bars. | `sleeves/milkman/rules.py:502-512`<br>`sleeves/milkman/vendor/milkman/dstrats.py:138-142` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Exit: At the close after the hold. | `sleeves/milkman/rules.py:496-501` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| Cells: the study's plateau picks | `sleeves/milkman/daily.py:76-80` |
| Saty's Phase Oscillator | `sleeves/milkman/vendor/milkman/mlib.py:16-18` |

## [Pivot Ribbon 13/48 cross](../../strategies/milkman/mk-pivotribbon1348cross.md)

| Rule | Read from |
|---|---|
| Entry: Long when EMA(13) crosses above EMA(48) (short: below), at the close; ≥ 60 bars. | `sleeves/milkman/rules.py:520-545`<br>`sleeves/milkman/vendor/milkman/dstrats.py:149-152`<br>`sleeves/milkman/daily.py:72` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Exit: At the opposite cross or after 120 sessions, at the close. | `sleeves/milkman/rules.py:522-538` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| The Pivot Ribbon's conviction arrow | `sleeves/milkman/vendor/milkman/dstrats.py:148-149` |

## [Daily compression expansion](../../strategies/milkman/mk-dailycompressionexpansion.md)

| Rule | Read from |
|---|---|
| Entry: Squeeze (Saty's compression): the 21-day, 2-sd Bollinger band inside 2 × ATR(14) around EMA(21), not while the gap widens inside 1.854 × ATR. | `sleeves/milkman/vendor/milkman/mlib.py:19-27`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Entry: Signal: the first bar out of a squeeze of ≥ N bars, with EMA(21) above EMA(48) for a long (below for a short); ≥ 60 bars. | `sleeves/milkman/rules.py:572-588`<br>`sleeves/milkman/vendor/milkman/dstrats.py:167-173` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Entry: Enters at the next open. | `sleeves/milkman/rules.py:552-561` |
| Exit: At the close H sessions after the signal bar. | `sleeves/milkman/rules.py:563-570` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:62`<br>`sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661`<br>`sleeves/milkman/vendored.py:56-60` |
| Cells: the study's plateau picks | `sleeves/milkman/daily.py:76-82` |

## [Big down-day response](../../strategies/milkman/mk-bigdowndayresponse.md)

| Rule | Read from |
|---|---|
| Entry: A close ≤ 2% below the prior close; enters at the close. | `sleeves/milkman/rules.py:595-606`<br>`sleeves/milkman/daily.py:73` |
| Exit: At the close 10 sessions later. | `sleeves/milkman/rules.py:599-602` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:645-661` |
| Long and short run as separate rows since 2026-10-19 (netted in one sleeve they always cancelled) | `sleeves/milkman/daily.py:176-186` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:55` |

## [O'Neil follow-through-day race](../../strategies/milkman/mk-oneilfollowthroughdayrace.md)

| Rule | Read from |
|---|---|
| Entry: Correction: a close 10% under the highest close of the last 63; the lowest low since is the correction low. | `sleeves/milkman/rules.py:664-673`<br>`sleeves/milkman/daily.py:74` |
| Entry: Rally: the first up close is day 1; a low under day 1's low restarts the count; from day 4, a close up ≥ 1.25% on higher volume than the day before is the follow-through day; enters at its close. | `sleeves/milkman/rules.py:674-687` |
| Entry: A close back within 0.1% of the 63-day high resets it. | `sleeves/milkman/rules.py:688-689` |
| Exit: Long: target close + (close - correction low), stop the correction low. Short: target the correction low, stop close + the same distance. From the next bar, stop first; else out at the close after 120 sessions. | `sleeves/milkman/rules.py:615-646` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Sizing: Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote. | `sleeves/milkman/daily.py:281-284`<br>`sleeves/milkman/daily.py:610-618`<br>`sleeves/milkman/daily.py:623` |
| Data: Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far. | `sleeves/milkman/daily.py:58-59`<br>`sleeves/milkman/daily.py:645-661` |
| O'Neil's follow-through day in the study's code | `sleeves/milkman/vendor/milkman/dstrats.py:187-188` |
| Long and short run as separate rows since 2026-10-19 (netted in one sleeve they always cancelled) | `sleeves/milkman/daily.py:176-186` |

## [Milkman daily rules on crypto-linked stocks](../../strategies/milkman/mk-milkmancryptolinkedstockvariant.md)

| Rule | Read from |
|---|---|
| Entry: Rules: Connors Double 7 (7, SMA200), Legend's Buy Day overnight (3), Daily Bilbo Box (5, EMA50 trail), Swing and Multi-day Golden Gates, EMA21 deviation (2 ATR, 10 sessions), Phase Oscillator accumulation (20 sessions), Pivot Ribbon 13/48, compression expansion (10 bars, 5 sessions); each long and short. | `sleeves/milkman/daily.py:126-132`<br>`sleeves/milkman/daily.py:149-153` |
| Entry: Names: the crypto-linked stock list's symbols among the 1,822 stocks (134). | `sleeves/milkman/daily.py:139-146` |
| Entry: Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3. | `sleeves/milkman/vendor/milkman/dlib.py:23-26`<br>`sleeves/milkman/vendor/milkman/dstrats.py:5-10` |
| Exit: Each rule exits by its own rule: a 7-day closing extreme, the next open, the EMA50 trail, a gate target, stop or period end, an EMA21 touch, a fixed hold, the opposite cross. | `sleeves/milkman/rules.py:752`<br>`sleeves/milkman/daily.py:149-153` |
| Sizing: Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. | `sleeves/milkman/daily.py:241-252`<br>`sleeves/milkman/daily.py:389-477`<br>`sleeves/milkman/daily.py:479-554`<br>`sleeves/milkman/daily.py:612-623` |
| Sizing: $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. | `sleeves/milkman/daily.py:60-61`<br>`sleeves/milkman/daily.py:590-611` |
| Data: The desk's split-adjusted daily bars (≥ 260 since 2016) and live quotes. | `sleeves/milkman/daily.py:194-226`<br>`sleeves/milkman/daily.py:645-661` |
| The crypto-linked list | `sleeves/milkman/daily.py:126-128`<br>`sleeves/milkman/daily.py:133-136` |

## [ATR level cascade (SPY)](../../strategies/milkman/mk-atrlevelcascade.md)

| Rule | Read from |
|---|---|
| Entry: ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0. | `sleeves/milkman/intraday.py:67`<br>`sleeves/milkman/intraday.py:216-246`<br>`sleeves/milkman/intraday.py:326-334` |
| Entry: At the first 1-minute bar (not the session's first) that reaches each level from 0.236 to 1.0, either way: long above the prior close, short below, at max(open, level). | `sleeves/milkman/intraday.py:434-445`<br>`sleeves/milkman/intraday.py:71` |
| Exit: Target the next level out; stop the level before (the prior close for 0.236), by touch. | `sleeves/milkman/intraday.py:445`<br>`sleeves/milkman/intraday.py:583-592` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:61`<br>master-desk `docs/research/2026-10-19-milkman/REVIEW.md:62` |

## [Day Golden Gate (SPY)](../../strategies/milkman/mk-daygoldengate.md)

| Rule | Read from |
|---|---|
| Entry: ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0. | `sleeves/milkman/intraday.py:67`<br>`sleeves/milkman/intraday.py:216-246`<br>`sleeves/milkman/intraday.py:326-334` |
| Entry: The first 1-minute bar to reach ±0.382, when the session opened short of it, at max(open, level). | `sleeves/milkman/intraday.py:341-347`<br>`sleeves/milkman/intraday.py:353-356`<br>`sleeves/milkman/intraday.py:74` |
| Exit: Target ±0.618; stop on a 10-minute close back beyond ±0.236. | `sleeves/milkman/intraday.py:356`<br>`sleeves/milkman/intraday.py:593-595` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:46` |

## [Bilbo Golden Gate (SPY)](../../strategies/milkman/mk-bilbogoldengate.md)

| Rule | Read from |
|---|---|
| Entry: ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0. | `sleeves/milkman/intraday.py:67`<br>`sleeves/milkman/intraday.py:216-246`<br>`sleeves/milkman/intraday.py:326-334` |
| Entry: The first 1-minute bar to reach ±0.382, when the session opened short of it, at max(open, level). | `sleeves/milkman/intraday.py:341-347`<br>`sleeves/milkman/intraday.py:353-355` |
| Entry: Filter: the last completed hourly Phase Oscillator above 61.8 and rising (short: below -61.8 and falling). | `sleeves/milkman/intraday.py:348-352`<br>`sleeves/milkman/intraday.py:361-362`<br>`sleeves/milkman/intraday.py:72` |
| Exit: Target ±0.618; stop on a 10-minute close back beyond ±0.236. | `sleeves/milkman/intraday.py:362`<br>`sleeves/milkman/intraday.py:593-595` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:50`<br>master-desk `docs/research/2026-10-19-milkman/REVIEW.md:63` |

## [Call-to-put reversal (SPY)](../../strategies/milkman/mk-calltoputputtocallreversal.md)

| Rule | Read from |
|---|---|
| Entry: ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0. | `sleeves/milkman/intraday.py:67`<br>`sleeves/milkman/intraday.py:216-246`<br>`sleeves/milkman/intraday.py:326-334` |
| Entry: Before 12:00 ET: the high reaches +0.236, then a close below the prior close, then the low reaches -0.236: short at min(open, trigger); the mirror buys. | `sleeves/milkman/intraday.py:386-401`<br>`sleeves/milkman/intraday.py:73` |
| Exit: Target ±0.382; stop on a 10-minute close back beyond the prior close. | `sleeves/milkman/intraday.py:402`<br>`sleeves/milkman/intraday.py:593-595` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:48` |

## [Directional trigger box (SPY)](../../strategies/milkman/mk-directionaltriggerbox.md)

| Rule | Read from |
|---|---|
| Entry: ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0. | `sleeves/milkman/intraday.py:67`<br>`sleeves/milkman/intraday.py:216-246`<br>`sleeves/milkman/intraday.py:326-334` |
| Entry: The open between the prior close and the ±0.236 trigger; every 10-minute close of the first hour inside that box; then the first 10-minute close beyond the trigger, at that close. | `sleeves/milkman/intraday.py:373-384`<br>`sleeves/milkman/intraday.py:75` |
| Exit: Target ±0.382; stop on a 10-minute close back beyond the trigger. | `sleeves/milkman/intraday.py:384`<br>`sleeves/milkman/intraday.py:593-595` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:47` |

## [Gap fade / momentum mirror (SPY)](../../strategies/milkman/mk-gapfademomentummirror.md)

| Rule | Read from |
|---|---|
| Entry: Gap = the open against the prior close. In the lane's bucket: the fade trades toward the prior close (stop 0.5 ATR beyond the open); the mirror trades the gap's way (target 0.5 ATR, stop the prior close); at the open. | `sleeves/milkman/intraday.py:404-414`<br>`sleeves/milkman/intraday.py:76-77` |
| Exit: Target and stop by touch. | `sleeves/milkman/intraday.py:583-592` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:57` |

## [Opening range breakout (SPY)](../../strategies/milkman/mk-openingrangebreakout.md)

| Rule | Read from |
|---|---|
| Entry: Range: the first 5 (long lane) or 10 (short lane) minutes' high and low; the first 5-minute close beyond it sets the side; enters at that close. | `sleeves/milkman/intraday.py:415-433`<br>`sleeves/milkman/intraday.py:78` |
| Entry: Long lane also needs the last 10-minute EMA(8) above EMA(21) and the close above the session VWAP. | `sleeves/milkman/intraday.py:416`<br>`sleeves/milkman/intraday.py:425-431` |
| Exit: Stop at the range's midpoint, by touch. | `sleeves/milkman/intraday.py:433`<br>`sleeves/milkman/intraday.py:583-587` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |

## [Ten-minute compression release (SPY)](../../strategies/milkman/mk-tenminutecompressionrelease.md)

| Rule | Read from |
|---|---|
| Entry: Saty's compression on 10-minute candles; the first candle out of a squeeze of ≥ N candles: long when EMA(21) is above EMA(48), short below; enters at the next 1-minute bar's open. | `sleeves/milkman/intraday.py:494-505`<br>`sleeves/milkman/vendor/milkman/mlib.py:19-27`<br>`sleeves/milkman/intraday.py:79` |
| Exit: Stop at the squeeze's low (long) or high (short), by touch. | `sleeves/milkman/intraday.py:497-505`<br>`sleeves/milkman/intraday.py:583-587` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |

## [Three-minute compression drift (SPY)](../../strategies/milkman/mk-threeminutecompressiondrift.md)

| Rule | Read from |
|---|---|
| Entry: A squeeze of ≥ 8 three-minute candles in one session (one-candle breaks allowed); drift up = its later candles' high ≥ the first 5's high + 0.5 ATR and their low ≥ the first 5's low - 0.25 ATR (down mirrored). | `sleeves/milkman/intraday.py:528-552`<br>`sleeves/milkman/intraday.py:565-567` |
| Entry: The first candle out of the squeeze closing beyond the last 5 candles' midpoint the drift's way; enters at the next 1-minute bar's open when the 3-minute ATR is ≥ 0.045% of price. | `sleeves/milkman/intraday.py:553-564`<br>`sleeves/milkman/intraday.py:80` |
| Exit: Stop 1 × the 3-minute ATR from entry, by touch. | `sleeves/milkman/intraday.py:563`<br>`sleeves/milkman/intraday.py:583-587` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |

## [Three-minute trigger confirmation (SPY)](../../strategies/milkman/mk-threeminutetriggerconfirmation.md)

| Rule | Read from |
|---|---|
| Entry: ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0. | `sleeves/milkman/intraday.py:67`<br>`sleeves/milkman/intraday.py:216-246`<br>`sleeves/milkman/intraday.py:326-334` |
| Entry: The open between the two ±0.236 triggers; the first 3-minute close beyond one, at that close (each side once). | `sleeves/milkman/intraday.py:365-371`<br>`sleeves/milkman/intraday.py:81` |
| Exit: Target ±0.382; stop on a 3-minute close back beyond the trigger. | `sleeves/milkman/intraday.py:371`<br>`sleeves/milkman/intraday.py:593-595` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:45` |

## [Vomy / iVomy (SPY)](../../strategies/milkman/mk-vomyivomy.md)

| Rule | Read from |
|---|---|
| Entry: 10-minute candles: long when EMA(8) is above EMA(13), the bull flip came within the last 3 candles, the candle's low touched EMA(13) and it closed above EMA(8); short mirrored; at the candle's close. | `sleeves/milkman/intraday.py:449-464`<br>`sleeves/milkman/intraday.py:482-493`<br>`sleeves/milkman/intraday.py:82` |
| Exit: Stop at that candle's EMA(13), on a 10-minute close beyond it. | `sleeves/milkman/intraday.py:491-493`<br>`sleeves/milkman/intraday.py:593-595` |
| Exit: Otherwise out at the close. | `sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |

## [ES Monday clock (SPY)](../../strategies/milkman/mk-esmondayclockonspyproxy.md)

| Rule | Read from |
|---|---|
| Entry: Each Monday with a full session: SPY at the open of the first 1-minute bar at or after 06:00 ET (within 5 minutes); a long and a short lane. | `sleeves/milkman/intraday.py:804-822`<br>`sleeves/milkman/intraday.py:85`<br>`sleeves/milkman/intraday.py:1120-1132` |
| Exit: At the open of the first bar at or after 16:00 ET. | `sleeves/milkman/intraday.py:1133-1136` |
| Sizing: Both legs are recorded as observations: the desk routes equities in the regular session only (the two lanes would net flat). | `sleeves/milkman/intraday.py:1024`<br>`sleeves/milkman/intraday.py:1137-1143` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:68` |

## [Premarket all-time-high fade (SPY)](../../strategies/milkman/mk-premarketathmorningfade.md)

| Rule | Read from |
|---|---|
| Entry: The 04:00-09:29 ET high above the highest high of every prior session; the 10-minute Phase Oscillator at 09:30 under 61.8; shorts the open. | `sleeves/milkman/intraday.py:825-882`<br>`sleeves/milkman/intraday.py:891-895`<br>`sleeves/milkman/intraday.py:86` |
| Exit: Out at the last bar before 12:00 ET; no stop. | `sleeves/milkman/intraday.py:883-895` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Data: The all-time-high reference: Yahoo daily highs plus the clock-hour and 1-minute highs it serves. | `sleeves/milkman/intraday.py:834-851` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:62` |

## [Four-hour Phase Oscillator OpEx rollover (SPY)](../../strategies/milkman/mk-fourhourpoopexrollover.md)

| Rule | Read from |
|---|---|
| Entry: A 4-hour candle's Phase Oscillator under 80 after one at ≥ 80, the first per day, on the session on or after the third Friday or the 5 after it. | `sleeves/milkman/intraday.py:913-943` |
| Entry: Stretch: the 4-hour close ≥ 0.618 ATR above the prior completed week's or month's close (the greater; their ATR14). | `sleeves/milkman/intraday.py:899-911`<br>`sleeves/milkman/intraday.py:941`<br>`sleeves/milkman/intraday.py:1100`<br>`sleeves/milkman/intraday.py:87` |
| Entry: Shorts at the market at the next pass (at the next regular open when the candle closes outside the session). | `sleeves/milkman/intraday.py:1092-1108` |
| Exit: At the close of the 10th full session after the signal day, market-on-close. | `sleeves/milkman/intraday.py:1004-1011`<br>`sleeves/milkman/intraday.py:1107-1108`<br>`sleeves/milkman/intraday.py:1060-1066` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Milkman's page for it (the desk's map of his site) | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:65` |

## [Gap-up pre-noon continuation (SPY)](../../strategies/milkman/mk-gapupprenooncontinuation.md)

| Rule | Read from |
|---|---|
| Entry: The open above the prior close and a high ≥ prior close × 1.01 before 12:00 ET; buys the next 1-minute bar's open. | `sleeves/milkman/intraday.py:946-963`<br>`sleeves/milkman/intraday.py:88` |
| Exit: Out at the close; no stop or target. | `sleeves/milkman/intraday.py:963`<br>`sleeves/milkman/intraday.py:596-598` |
| Sizing: Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. | `sleeves/milkman/intraday.py:65`<br>`sleeves/milkman/intraday.py:1048-1066`<br>`sleeves/milkman/intraday.py:1069-1090`<br>`sleeves/milkman/intraday.py:1146-1175` |
| Sizing: $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |

## [Tensor breadth timing (IWM)](../../strategies/milkman/mk-creativetensorbreadthtiming.md)

| Rule | Read from |
|---|---|
| Entry: Breadth: the share of the 1,822 names whose closed weekly Tensor bar has ≥ 5 bullish votes (weeks with ≥ 500 names). | `sleeves/milkman/galath.py:279-289`<br>`sleeves/milkman/galath.py:642-646` |
| Entry: In when the latest week's breadth is at or below the median of the weeks to 2023-09-29 (at least 20 of them). | `sleeves/milkman/galath.py:84`<br>`sleeves/milkman/galath.py:648-655` |
| Entry: Decided once the week's scan is in; trades the next session at the market. | `sleeves/milkman/galath.py:657-681` |
| Exit: To cash when breadth is above the median. | `sleeves/milkman/galath.py:654-655`<br>`sleeves/milkman/galath.py:677-681` |
| Sizing: The whole $100,000 book in IWM, or none. | `sleeves/milkman/galath.py:631`<br>`sleeves/milkman/galath.py:677` |
| Data: Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes). | `sleeves/milkman/galath.py:200-215`<br>`sleeves/milkman/galath.py:259-277`<br>`sleeves/milkman/galath.py:414-444`<br>`sleeves/milkman/milkman.py:28-31` |
| Study | `sleeves/milkman/galath.py:15-17` |

## [Tensor ratio-chart signals](../../strategies/milkman/mk-creativetensorratiochartsignals.md)

| Rule | Read from |
|---|---|
| Entry: Ratio bars: the stock's adjusted open, high, low and close over SPY's (high = the largest of the four ratios, low = the smallest), the stock's volume, in Friday weeks. | `sleeves/milkman/galath.py:322-354` |
| Entry: A closed weekly ratio bar with a buy-cyan or buy-green marker; 20-day dollar volume ≥ $100,000. | `sleeves/milkman/galath.py:357-382`<br>`sleeves/milkman/galath.py:85`<br>`sleeves/milkman/galath.py:697-704` |
| Entry: Bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask. | `sleeves/milkman/galath.py:547-548`<br>`sleeves/milkman/galath.py:554-566`<br>`sleeves/milkman/galath.py:579-583`<br>`sleeves/milkman/galath.py:592-599` |
| Exit: 252 sessions after the fire week, sold market-on-close on that session. | `sleeves/milkman/galath.py:707`<br>`sleeves/milkman/galath.py:543-546`<br>`sleeves/milkman/galath.py:568-577` |
| Sizing: $1,000 a fire; a $3,000,000 book. | `sleeves/milkman/galath.py:691-692`<br>`sleeves/milkman/galath.py:706-707` |
| Data: Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes). | `sleeves/milkman/galath.py:200-215`<br>`sleeves/milkman/galath.py:259-277`<br>`sleeves/milkman/galath.py:414-444`<br>`sleeves/milkman/milkman.py:28-31` |
| Study | `sleeves/milkman/galath.py:18-20` |

## [Tensor fires as calls](../../strategies/milkman/mk-creativetensoroptionexpressionproxy.md)

| Rule | Read from |
|---|---|
| Entry: Weekly fire: a closed weekly Tensor bar with a buy-cyan or buy-green marker (bar ≥ 60). | `sleeves/milkman/galath.py:292-296` |
| Entry: Tier A: at least 2 of (close ≤ $14.94; that and a 60-day return ≥ 31%; ≥ 70% under the 252-day high; an SMH-sector name), not XLF, XLB, XLRE or XLU; 60-day realised volatility 5-400%; 20-day dollar volume ≥ $100,000. | `sleeves/milkman/galath.py:237-242`<br>`sleeves/milkman/galath.py:728-740` |
| Entry: The listed call with the expiry nearest 52 weeks (≥ 75% of it) and the strike nearest the fire close, two-sided, bought the session after the fire week with a limit 2% over the ask for an hour; ask ≥ 2% of spot. | `sleeves/milkman/galath.py:750-785`<br>`sleeves/milkman/galath.py:789-805` |
| Exit: After 52 weeks (or the expiry's last session if sooner), a marketable order that session. | `sleeves/milkman/galath.py:779-780`<br>`sleeves/milkman/galath.py:543-546`<br>`sleeves/milkman/galath.py:568-577` |
| Sizing: Contracts = floor($1,000 / (ask × 100)), at least 1 unless one contract costs over $2,000; a $1,000,000 book. | `sleeves/milkman/galath.py:716-717`<br>`sleeves/milkman/galath.py:772-778` |
| Data: Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes). | `sleeves/milkman/galath.py:200-215`<br>`sleeves/milkman/galath.py:259-277`<br>`sleeves/milkman/galath.py:414-444`<br>`sleeves/milkman/milkman.py:28-31` |
| Data: The desk's call chains, 250-800 days out. | `sleeves/milkman/galath.py:808-816` |
| Named divergence: listed calls | `sleeves/milkman/galath.py:44-45` |

## [Big Winners weekly Tensor sleeve](../../strategies/milkman/mk-bigwinners.md)

| Rule | Read from |
|---|---|
| Entry: Weekly fire: a closed weekly Tensor bar with a buy-cyan or buy-green marker (bar ≥ 60). | `sleeves/milkman/galath.py:292-296` |
| Entry: Stream: 20-day dollar volume ≥ $1M; not avoided (price ≥ $100; Cyan within 5% of the 52-week high; XLF, XLB, XLRE; Cyan in XLU; Green within 13 weeks of the name's last fire); calibrated (Cyan: ≤ $14.94 or a 60-week depth ≥ 70.35%; Green: ≤ $13.15 with a 20-week standard deviation of weekly returns ≥ 0.08896). | `sleeves/milkman/galath.py:820-841`<br>`sleeves/milkman/galath.py:297-306` |
| Entry: Order: the desk score (5.5, plus up to 1 for the calibration boosts when dollar volume ≥ $2M), then dollar volume; one position per name. | `sleeves/milkman/galath.py:836-841`<br>`sleeves/milkman/galath.py:854-886` |
| Entry: Budget: open cost basis ≤ $50,000 less realised losses. | `sleeves/milkman/galath.py:848`<br>`sleeves/milkman/galath.py:867-895` |
| Entry: Bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask. | `sleeves/milkman/galath.py:547-548`<br>`sleeves/milkman/galath.py:554-566`<br>`sleeves/milkman/galath.py:579-583`<br>`sleeves/milkman/galath.py:592-599` |
| Exit: At the close of the 52nd week after the fire week, market-on-close. | `sleeves/milkman/galath.py:899-900`<br>`sleeves/milkman/galath.py:496-498`<br>`sleeves/milkman/galath.py:543-546` |
| Sizing: Whole shares = floor($1,000 / the live ask); a $100,000 book. | `sleeves/milkman/galath.py:847-848`<br>`sleeves/milkman/galath.py:887-891` |
| Sizing: Paced row: a weekly token bucket (starts at 1, refills $50,000 / (52 × $1,000) a week, holds at most 3), one token an entry. | `sleeves/milkman/galath.py:872-878`<br>`sleeves/milkman/galath.py:885-886`<br>`sleeves/milkman/galath.py:897-898`<br>`sleeves/milkman/galath.py:930-933` |
| Data: Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes). | `sleeves/milkman/galath.py:200-215`<br>`sleeves/milkman/galath.py:259-277`<br>`sleeves/milkman/galath.py:414-444`<br>`sleeves/milkman/milkman.py:28-31` |
| Study and config | `sleeves/milkman/galath.py:24-29` |

## [Milkman filters on Tensor lanes](../../strategies/milkman/mk-milkmanlaneaddonfilters.md)

| Rule | Read from |
|---|---|
| Entry: Lanes: weekly Cyan and Green (a closed weekly bar with the marker, bar ≥ 60); daily Green (bar ≥ 250); daily Swing (a green bar within 3 bars of its setup square). | `sleeves/milkman/galath.py:292-296`<br>`sleeves/milkman/galath.py:425-437` |
| Entry: Weekly Cyan unless EMA13 crossed above EMA48 in the last 10 days; weekly Green unless the fire day closed exactly 3 lower closes. | `sleeves/milkman/galath.py:948-960`<br>`sleeves/milkman/galath.py:404-409` |
| Entry: Daily Green unless the Phase Oscillator is ≥ 61.8; daily Swing at double size after a compression release up in the last 5 days. | `sleeves/milkman/galath.py:961-980`<br>`sleeves/milkman/galath.py:404-409` |
| Entry: 20-day dollar volume ≥ $100,000. | `sleeves/milkman/galath.py:953`<br>`sleeves/milkman/galath.py:964` |
| Entry: Bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask. | `sleeves/milkman/galath.py:547-548`<br>`sleeves/milkman/galath.py:554-566`<br>`sleeves/milkman/galath.py:579-583`<br>`sleeves/milkman/galath.py:592-599` |
| Exit: Held 78 weeks (weekly lanes), 60 sessions (daily Green) or 40 (daily Swing), then sold market-on-close. | `sleeves/milkman/galath.py:959`<br>`sleeves/milkman/galath.py:969`<br>`sleeves/milkman/galath.py:973`<br>`sleeves/milkman/galath.py:979`<br>`sleeves/milkman/galath.py:543-546` |
| Sizing: $1,000 a fire ($2,000 for a boosted Swing); a $5,000,000 book. | `sleeves/milkman/galath.py:940-941`<br>`sleeves/milkman/galath.py:973` |
| Data: Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes). | `sleeves/milkman/galath.py:200-215`<br>`sleeves/milkman/galath.py:259-277`<br>`sleeves/milkman/galath.py:414-444`<br>`sleeves/milkman/milkman.py:28-31` |
| The study's REAL rules on the lanes | `sleeves/milkman/galath.py:30-33` |
