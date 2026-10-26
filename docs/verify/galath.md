# Verification: Galath / GrokBot

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk), or at `22f3e991c224` where a cite names it (the four recorders converted into books on 2026-10-26); every other path is in this repository.

## [Next-support plan](../../strategies/galath/galath-next-support-plan.md)

| Rule | Read from |
|---|---|
| Entry: Plan (admit-ticker v1.1): buy at the highest support at most 1.5% above the last close (a 38.2-78.6% retrace of the 60-day swing, the 21-day EMA or the 12-day low) when it is under 99.8% of the close, else 1.5% under the close; stop 0.6% under the 12-day low, kept 2.5-3.5% under the buy; target 5R, at least +6% and at most +18%, moved to the 21- or 50-day EMA when one sits in that band. | `sleeves/galath/levels.py:22-27`<br>`sleeves/galath/levels.py:45-99`<br>`sleeves/galath/levels.py:109-112`<br>`sleeves/galath/levels.py:123-172`<br>`sleeves/galath/levels.py:175-217` |
| Entry: The plan is built once a session from the last completed bar. | `sleeves/galath/galath.py:255-264`<br>`sleeves/galath/galath.py:293-310` |
| Entry: Buys 09:35-15:45 ET on weekdays: not held, not traded that day, under 6 swings, 10 open names, 16 new buys a day and 2 of one story (semis, software, EV, space ...). | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:200-218`<br>`sleeves/galath/paper.py:416-434`<br>`sleeves/galath/wire.py:94-120`<br>`sleeves/galath/wire.py:185-205`<br>`sleeves/galath/tensor.py:249-265` |
| Entry: At the live price, only within 3% of the plan's buy, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil); best tier and R first, at most 6 buys a pass; marketable order. | `sleeves/galath/paper.py:53-75`<br>`sleeves/galath/levels.py:190-195`<br>`sleeves/galath/galath.py:283-290`<br>`sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:295-327` |
| Exit: The plan's stop and target ride as an engine-held bracket. | `sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:211-224` |
| Exit: Trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI ≥ 68 with a daily bearish divergence after +80%. | `sleeves/galath/paper.py:480-525`<br>`sleeves/galath/paper.py:543-549`<br>`sleeves/galath/paper.py:597-625`<br>`sleeves/galath/wire.py:238-261`<br>`sleeves/galath/wire.py:276-287` |
| Exit: One add when price is back within 2% of the 50- or 200-day EMA after 5 of the prior 16 closes below it. | `sleeves/galath/paper.py:580-594`<br>`sleeves/galath/paper.py:628-631`<br>`sleeves/galath/wire.py:256-257`<br>`sleeves/galath/wire.py:272-275`<br>`sleeves/galath/paper.py:184-199` |
| Exit: A position worth under $75 is sold. | `sleeves/galath/paper.py:18`<br>`sleeves/galath/wire.py:262-271` |
| Sizing: 1.5% of equity at risk to the stop (2% of price without one), capped at 8% of equity; whole shares. | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:36-50`<br>`sleeves/galath/wire.py:211-216` |
| Data: Split-adjusted daily bars (300 sessions) with today's bar from the live quote; live quotes. | `sleeves/galath/galath.py:177-192`<br>`sleeves/galath/galath.py:219-223` |
| Sell re-judged without bars | `sleeves/galath/wire.py:288-290`<br>`sleeves/galath/paper.py:273-286`<br>`sleeves/galath/paper.py:78-107`<br>`sleeves/galath/paper.py:597-612` |
| Trim recognised by its reason text | `sleeves/galath/wire.py:254-255`<br>`sleeves/galath/paper.py:621-623` |
| Own book | `sleeves/galath/wire.py:82-99` |
| Folio list | `sleeves/galath/galath.py:162-164` |

## [Washout and PPC coil](../../strategies/galath/galath-washout-ppc-coil.md)

| Rule | Read from |
|---|---|
| Entry: Washout: under the 50-day EMA, RSI(14) < 50, the MACD histogram below zero (or rising and under 0.15), ≥ 8% under the 60-day high, ≤ 6% over the 12-day low unless on the 21-day, on a 50 / 61.8 / 78.6% retrace (within 2.5%), the 12-day shelf (≤ 4% over it) or the 21-day EMA (within 2%), relative volume < 2.2. | `sleeves/galath/levels.py:221-222`<br>`sleeves/galath/levels.py:238-296` |
| Entry: PPC coil (tier S, ranked first): 0-3% under the 50-day EMA, within 2% of the 21-day, RSI 40-52, the histogram rising below zero, a 60-day range ≤ 25%, relative volume ≤ 1.1, within 2.5% of the 50 or 61.8% retrace, and a 78.6% shakeout that held in the last 6 sessions. | `sleeves/galath/levels.py:223-224`<br>`sleeves/galath/levels.py:299-350`<br>`sleeves/galath/levels.py:353-360`<br>`sleeves/galath/galath.py:332-333` |
| Entry: Levels: the next-support plan (the Next-support plan card). | `sleeves/galath/galath.py:319-336`<br>`sleeves/galath/levels.py:175-217` |
| Entry: Buys 09:35-15:45 ET on weekdays: not held, not traded that day, under 6 swings, 10 open names, 16 new buys a day and 2 of one story (semis, software, EV, space ...). | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:200-218`<br>`sleeves/galath/paper.py:416-434`<br>`sleeves/galath/wire.py:94-120`<br>`sleeves/galath/wire.py:185-205`<br>`sleeves/galath/tensor.py:249-265` |
| Entry: At the live price, only within 3% of the plan's buy, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil); best tier and R first, at most 6 buys a pass; marketable order. | `sleeves/galath/paper.py:53-75`<br>`sleeves/galath/levels.py:190-195`<br>`sleeves/galath/galath.py:283-290`<br>`sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:295-327` |
| Exit: The plan's stop and target ride as an engine-held bracket. | `sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:211-224` |
| Exit: Trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI ≥ 68 with a daily bearish divergence after +80%. | `sleeves/galath/paper.py:480-525`<br>`sleeves/galath/paper.py:543-549`<br>`sleeves/galath/paper.py:597-625`<br>`sleeves/galath/wire.py:238-261`<br>`sleeves/galath/wire.py:276-287` |
| Exit: One add when price is back within 2% of the 50- or 200-day EMA after 5 of the prior 16 closes below it. | `sleeves/galath/paper.py:580-594`<br>`sleeves/galath/paper.py:628-631`<br>`sleeves/galath/wire.py:256-257`<br>`sleeves/galath/wire.py:272-275`<br>`sleeves/galath/paper.py:184-199` |
| Exit: A position worth under $75 is sold. | `sleeves/galath/paper.py:18`<br>`sleeves/galath/wire.py:262-271` |
| Sizing: 1.5% of equity at risk to the stop (2% of price without one), capped at 8% of equity; whole shares. | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:36-50`<br>`sleeves/galath/wire.py:211-216` |
| Data: Split-adjusted daily bars (300 sessions) with today's bar from the live quote; live quotes. | `sleeves/galath/galath.py:177-192`<br>`sleeves/galath/galath.py:219-223` |
| Sell re-judged without bars | `sleeves/galath/wire.py:288-290`<br>`sleeves/galath/paper.py:273-286`<br>`sleeves/galath/paper.py:78-107`<br>`sleeves/galath/paper.py:597-612` |
| Trim recognised by its reason text | `sleeves/galath/wire.py:254-255`<br>`sleeves/galath/paper.py:621-623` |
| Own book | `sleeves/galath/wire.py:82-99` |
| Universe | `sleeves/galath/galath.py:159-161` |

## [Komar momentum breakout](../../strategies/galath/galath-komar-momentum.md)

| Rule | Read from |
|---|---|
| Entry: Screen after the close (≥ 80 sessions): close > $5, 50-day dollar volume ≥ $20M, 20-day ADR ≥ 4%, ≥ 70% above the 52-week low, close above the 65-day EMA, the 8-day EMA above the 21-day. | `sleeves/galath/komar.py:8-14`<br>`sleeves/galath/komar.py:182-213`<br>`sleeves/galath/galath.py:396-404` |
| Entry: Setup within 18% of the 52-week high: tight breakout (10-day range ≤ 55% of the 40-day, 5-day volume ≤ 80% of the 50-day, within 6% of the 20-day high) or large base (10-day range ≤ 70% of the 40-day, within 10%); ready when within 2% of the 20-day high after fewer than 3 straight up days. | `sleeves/galath/komar.py:172-179`<br>`sleeves/galath/komar.py:214-226`<br>`sleeves/galath/galath.py:407-411` |
| Entry: Market: Nasdaq Composite proxy B from the prior session (8-day EMA over the 21-day with both rising over 5 sessions = green; under with both falling = red); red blocks entries; green with strong reads is tier A, the rest tier B; both trade. | `sleeves/galath/komar.py:108-134`<br>`sleeves/galath/komar.py:248-268`<br>`sleeves/galath/galath.py:370-382`<br>`sleeves/galath/galath.py:408` |
| Entry: Entry: the next session, a day buy-stop at the 20-day high; skipped when open risk would pass 5% of equity. | `sleeves/galath/galath.py:342`<br>`sleeves/galath/galath.py:412-417`<br>`sleeves/galath/galath.py:456-474` |
| Exit: Stop at the 10-day low, engine-held. | `sleeves/galath/komar.py:222-223`<br>`sleeves/galath/galath.py:416`<br>`sleeves/galath/galath.py:467-469` |
| Exit: A close under the 21-day EMA sells at the next session. | `sleeves/galath/galath.py:418-429`<br>`sleeves/galath/galath.py:434-435`<br>`sleeves/galath/galath.py:444-449` |
| Exit: After 10 sessions, a close at or under the entry sells at the next session. | `sleeves/galath/galath.py:343`<br>`sleeves/galath/galath.py:425-431` |
| Exit: A close back under the 20-day-high pivot sells half at the next session, once. | `sleeves/galath/galath.py:432-433`<br>`sleeves/galath/galath.py:450-455` |
| Sizing: 0.5% of equity at risk to the 10-day low, capped at 35% of equity; whole shares. | `sleeves/galath/komar.py:12-14`<br>`sleeves/galath/komar.py:272-284`<br>`sleeves/galath/galath.py:412` |
| Data: Split-adjusted daily bars (504 sessions), Nasdaq Composite daily bars, live quotes. | `sleeves/galath/galath.py:351-354` |
| Ranking: tier then score | `sleeves/galath/komar.py:287-292`<br>`sleeves/galath/galath.py:404` |

## [Anna seven-vote printer](../../strategies/galath/galath-anna-seven-vote-printer.md)

| Rule | Read from |
|---|---|
| Entry: Seven daily votes: StochRSI K vs D, Aroon up vs down, +DI vs -DI, the 5-bar OBV slope, squeeze momentum, the 8- vs 21-day EMA, WaveTrend; the gate needs all 7, ≥ 5 bullish and bulls - bears ≥ 4. | `sleeves/galath/anna.py:329-334`<br>`sleeves/galath/anna.py:360-385`<br>`sleeves/galath/anna.py:429-432` |
| Entry: CYAN buy: the UT Bot (ATR 10) flips up with the gate. GREEN buy: the 8-day EMA crosses over the 21-day within 6 bars of a UT Bot up flip, with the gate. | `sleeves/galath/anna.py:149-176`<br>`sleeves/galath/anna.py:418-451` |
| Entry: Buys at the next session's first pass while the signal is buy; names need 200 bars. | `sleeves/galath/anna.py:13`<br>`sleeves/galath/galath.py:503-522`<br>`sleeves/galath/galath.py:528-542` |
| Exit: RED sell: the UT Bot flips down. MAGENTA: the 8-day EMA crosses under the 21-day within 6 bars of a UT Bot down flip. A sell wins a same-bar clash. | `sleeves/galath/anna.py:433-457` |
| Exit: A buy signal also ends when the close falls below the 200-day EMA. | `sleeves/galath/anna.py:497-506` |
| Exit: A sell within 2 bars of a buy flip is ignored while price is ≥ 94% of the 200-day EMA, unless the bar is a failed euphoria or an extended failure. | `sleeves/galath/anna.py:217-219`<br>`sleeves/galath/anna.py:290-299`<br>`sleeves/galath/anna.py:322-325` |
| Exit: Sold at the next session's first pass. | `sleeves/galath/galath.py:518-521`<br>`sleeves/galath/galath.py:543-545` |
| Sizing: An equal slot: equity / 13 per name. | `sleeves/galath/galath.py:533`<br>`sleeves/galath/galath.py:541` |
| Data: Split-adjusted daily bars (500 sessions), live quotes. | `sleeves/galath/galath.py:491-493` |
| Squeeze epochs | `sleeves/galath/anna.py:22-29`<br>`sleeves/galath/anna.py:35-44`<br>`sleeves/galath/anna.py:345-346` |
| Watchlist | `sleeves/galath/galath.py:165-167` |

## [Echo swing](../../strategies/galath/galath-echo-swing.md)

| Rule | Read from |
|---|---|
| Entry: Every 3 minutes the account's RSS mirrors are read; a new post saying he bought, or a starter, is a BUY of the named ticker; "I added" is an ADD; recaps, reposts, old fills, plans and "never bought" are skipped. | `sleeves/galath/echo.py:24-46`<br>`sleeves/galath/echo.py:78-115`<br>`sleeves/galath/echo.py:172-174`<br>`sleeves/galath/galath.py:1119-1158`<br>`sleeves/galath/galath.py:1216-1232` |
| Entry: BUY: 09:35-15:45 ET on a weekday, not held or bought that day, not a chase (5-day return ≤ 8% and ≤ 4% above the 21-day EMA), under 6 swings, 10 open names and 16 new buys a day. | `sleeves/galath/echo.py:119-123`<br>`sleeves/galath/echo.py:147-168`<br>`sleeves/galath/paper.py:184-199`<br>`sleeves/galath/galath.py:1161-1175`<br>`sleeves/galath/galath.py:1265-1282` |
| Entry: ADD: only at support (-5% to +2% of the 21-day EMA, or a 5-day return ≤ 0). | `sleeves/galath/echo.py:135-144`<br>`sleeves/galath/echo.py:160-163` |
| Entry: Marketable order at the live price; a post read outside those hours, or in the first sweep, is not traded. | `sleeves/galath/galath.py:1218-1229`<br>`sleeves/galath/galath.py:1242-1255`<br>`sleeves/galath/wire.py:134-142` |
| Exit: Bracket: stop 2% under the price, target +5%, engine-held. | `sleeves/galath/paper.py:110-126`<br>`sleeves/galath/galath.py:1280-1282`<br>`sleeves/galath/wire.py:211-224` |
| Exit: Trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI ≥ 68 with a daily bearish divergence after +80%. | `sleeves/galath/paper.py:480-525`<br>`sleeves/galath/paper.py:543-549`<br>`sleeves/galath/paper.py:597-625`<br>`sleeves/galath/wire.py:238-261`<br>`sleeves/galath/wire.py:276-287` |
| Exit: One add when price is back within 2% of the 50- or 200-day EMA after 5 of the prior 16 closes below it. | `sleeves/galath/paper.py:580-594`<br>`sleeves/galath/paper.py:628-631`<br>`sleeves/galath/wire.py:256-257`<br>`sleeves/galath/wire.py:272-275`<br>`sleeves/galath/paper.py:184-199` |
| Exit: A position worth under $75 is sold. | `sleeves/galath/paper.py:18`<br>`sleeves/galath/wire.py:262-271` |
| Sizing: 1.5% of equity at risk to the 2% stop, capped at 8% of equity (so 8%); whole shares. | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:36-50`<br>`sleeves/galath/wire.py:211-216` |
| Data: @EchoAnalysis posts from Nitter and xcancel RSS mirrors; daily bars; live quotes. | `sleeves/galath/galath.py:1119-1121`<br>`sleeves/galath/galath.py:1182-1186`<br>`sleeves/galath/echo.py:172-174` |
| Sell re-judged without bars | `sleeves/galath/wire.py:288-290`<br>`sleeves/galath/paper.py:273-286`<br>`sleeves/galath/paper.py:78-107`<br>`sleeves/galath/paper.py:597-612` |
| Trim recognised by its reason text | `sleeves/galath/wire.py:254-255`<br>`sleeves/galath/paper.py:621-623` |

## [Scanner book swing](../../strategies/galath/galath-scanner-book-swing.md)

| Rule | Read from |
|---|---|
| Entry: Scan: the nine Signal Prism engines (Vector, Meridian, Cascade, Threshold, Fissure, Dread, Reverb, Zenith, Strata) on the last completed session, SPY the bench; once a session. | `sleeves/galath/galath.py:559-561`<br>`sleeves/galath/galath.py:575-627`<br>`sleeves/galath/prism.py:1415-1483` |
| Entry: Candidate: an S/A-grade or first-defense event, not contradicted, developing or expired; the selection read must say BUY (a coil, a washout, or a held level with two confirmations) and the name needs a washout, a coil, a bottom-screen buy or an RSI/MACD curl. | `sleeves/galath/book.py:1576-1630`<br>`sleeves/galath/book.py:730-812` |
| Entry: Sector: the name's sector ETF must be turning against SPY; waterfall, trend and trough sectors and names without a sector ETF are skipped, cyclicals wait in a risk-off tape. | `sleeves/galath/book.py:848-851`<br>`sleeves/galath/book.py:900-923`<br>`sleeves/galath/book.py:958-1005`<br>`sleeves/galath/book.py:1743-1755` |
| Entry: Book: the Prism candidates (S tier and curl first), then the bottom screen's buys, up to 20, on the next-support plan; dropped when RSI ≥ 50 off support. | `sleeves/galath/book.py:64-66`<br>`sleeves/galath/book.py:1687-1731`<br>`sleeves/galath/book.py:1759-1778`<br>`sleeves/galath/book.py:539-551`<br>`sleeves/galath/galath.py:596-606` |
| Entry: Rebuilt every 10 minutes; outside 11:25-11:55 and 14:10-14:50 ET each name is re-read on the 5-minute session tape: dropped when 3% through the buy, at its stop or within 1% of its target, and the plan rebased to the last print. | `sleeves/galath/galath.py:561`<br>`sleeves/galath/galath.py:644-656`<br>`sleeves/galath/galath.py:689-734`<br>`sleeves/galath/book.py:1871-1885`<br>`sleeves/galath/book.py:1889-1896`<br>`sleeves/galath/book.py:1999-2023`<br>`sleeves/galath/book.py:2099-2144` |
| Entry: Buys 09:35-15:45 ET on weekdays: not held, not traded that day, under 6 swings, 10 open names, 16 new buys a day and 2 of one story (semis, software, EV, space ...). | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:200-218`<br>`sleeves/galath/paper.py:416-434`<br>`sleeves/galath/wire.py:94-120`<br>`sleeves/galath/wire.py:185-205`<br>`sleeves/galath/tensor.py:249-265` |
| Entry: At the live price, only within 3% of the plan's buy, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil); best tier and R first, at most 6 buys a pass; marketable order. | `sleeves/galath/paper.py:53-75`<br>`sleeves/galath/levels.py:190-195`<br>`sleeves/galath/galath.py:283-290`<br>`sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:295-327` |
| Exit: The plan's stop and target ride as an engine-held bracket. | `sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:211-224` |
| Exit: Trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI ≥ 68 with a daily bearish divergence after +80%. | `sleeves/galath/paper.py:480-525`<br>`sleeves/galath/paper.py:543-549`<br>`sleeves/galath/paper.py:597-625`<br>`sleeves/galath/wire.py:238-261`<br>`sleeves/galath/wire.py:276-287` |
| Exit: One add when price is back within 2% of the 50- or 200-day EMA after 5 of the prior 16 closes below it. | `sleeves/galath/paper.py:580-594`<br>`sleeves/galath/paper.py:628-631`<br>`sleeves/galath/wire.py:256-257`<br>`sleeves/galath/wire.py:272-275`<br>`sleeves/galath/paper.py:184-199` |
| Exit: A position worth under $75 is sold. | `sleeves/galath/paper.py:18`<br>`sleeves/galath/wire.py:262-271` |
| Sizing: 1.5% of equity at risk to the stop (2% of price without one), capped at 8% of equity; whole shares. | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:36-50`<br>`sleeves/galath/wire.py:211-216` |
| Data: Split-adjusted daily bars (502 sessions), extended-hours 5-minute bars with the forming bar, live quotes. | `sleeves/galath/galath.py:559`<br>`sleeves/galath/galath.py:580`<br>`sleeves/galath/galath.py:659-672`<br>`sleeves/galath/galath.py:746-751` |
| Sell re-judged without bars | `sleeves/galath/wire.py:288-290`<br>`sleeves/galath/paper.py:273-286`<br>`sleeves/galath/paper.py:78-107`<br>`sleeves/galath/paper.py:597-612` |
| Trim recognised by its reason text | `sleeves/galath/wire.py:254-255`<br>`sleeves/galath/paper.py:621-623` |
| Own book | `sleeves/galath/wire.py:82-99` |

## [Sector-first bottom](../../strategies/galath/galath-sector-first-bottom.md)

| Rule | Read from |
|---|---|
| Entry: Bottom screen on the scan's daily bars: single names (no index products), ≥ $8, 20-day dollar volume ≥ $15M, no > 70% 60-day collapse. | `sleeves/galath/book.py:1146-1168`<br>`sleeves/galath/book.py:1233-1253`<br>`sleeves/galath/book.py:1339-1343` |
| Entry: Points: quality (above 45% of the 200-day, no > 45% 60-day drop, ≥ $25M volume), cheap (18-55% off the 52-week high, 3-28% under the 200-day), sector (lagging SPY over 126 days, leading over 20; its ETF turning), structure (a contracting base, a spring), a selling climax, impulse (on the 21-day under the 50-day, the 21-day rising). | `sleeves/galath/book.py:1177-1230`<br>`sleeves/galath/book.py:1254-1290`<br>`sleeves/galath/book.py:1347-1383` |
| Entry: BUY at ≥ 8 points with ≥ 2 turn points (structure, climax, impulse), cheap ≥ 1 and quality ≥ 2; under 9 points it waits while SPY is under its 200-day with a new 20-day low, or the tape is risk-off. | `sleeves/galath/book.py:1293-1316`<br>`sleeves/galath/book.py:958-971`<br>`sleeves/galath/book.py:1382-1383` |
| Entry: Sector: waterfall, trend and trough sectors and names without a sector ETF are skipped; cyclicals wait in a risk-off tape. | `sleeves/galath/book.py:848-851`<br>`sleeves/galath/book.py:988-1005`<br>`sleeves/galath/book.py:1361-1368`<br>`sleeves/galath/book.py:1385-1386` |
| Entry: Book: up to 20 names by R, on the next-support plan; dropped when RSI ≥ 50 off support; the same 10-minute rebuild and session-tape re-read as the Scanner book swing. | `sleeves/galath/book.py:1527-1547`<br>`sleeves/galath/book.py:1783-1805`<br>`sleeves/galath/galath.py:606-608`<br>`sleeves/galath/galath.py:703-734` |
| Entry: Buys 09:35-15:45 ET on weekdays: not held, not traded that day, under 6 swings, 10 open names, 16 new buys a day and 2 of one story (semis, software, EV, space ...). | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:200-218`<br>`sleeves/galath/paper.py:416-434`<br>`sleeves/galath/wire.py:94-120`<br>`sleeves/galath/wire.py:185-205`<br>`sleeves/galath/tensor.py:249-265` |
| Entry: At the live price, only within 3% of the plan's buy, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil); best tier and R first, at most 6 buys a pass; marketable order. | `sleeves/galath/paper.py:53-75`<br>`sleeves/galath/levels.py:190-195`<br>`sleeves/galath/galath.py:283-290`<br>`sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:295-327` |
| Exit: The plan's stop and target ride as an engine-held bracket. | `sleeves/galath/wire.py:134-142`<br>`sleeves/galath/wire.py:211-224` |
| Exit: Trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI ≥ 68 with a daily bearish divergence after +80%. | `sleeves/galath/paper.py:480-525`<br>`sleeves/galath/paper.py:543-549`<br>`sleeves/galath/paper.py:597-625`<br>`sleeves/galath/wire.py:238-261`<br>`sleeves/galath/wire.py:276-287` |
| Exit: One add when price is back within 2% of the 50- or 200-day EMA after 5 of the prior 16 closes below it. | `sleeves/galath/paper.py:580-594`<br>`sleeves/galath/paper.py:628-631`<br>`sleeves/galath/wire.py:256-257`<br>`sleeves/galath/wire.py:272-275`<br>`sleeves/galath/paper.py:184-199` |
| Exit: A position worth under $75 is sold. | `sleeves/galath/paper.py:18`<br>`sleeves/galath/wire.py:262-271` |
| Sizing: 1.5% of equity at risk to the stop (2% of price without one), capped at 8% of equity; whole shares. | `sleeves/galath/paper.py:14-18`<br>`sleeves/galath/paper.py:36-50`<br>`sleeves/galath/wire.py:211-216` |
| Data: Split-adjusted daily bars (502 sessions) of the universe, SPY and 18 sector / regime ETFs; extended-hours 5-minute bars; live quotes. | `sleeves/galath/galath.py:559-561`<br>`sleeves/galath/galath.py:575-612`<br>`sleeves/galath/book.py:816`<br>`sleeves/galath/book.py:856` |
| Sell re-judged without bars | `sleeves/galath/wire.py:288-290`<br>`sleeves/galath/paper.py:273-286`<br>`sleeves/galath/paper.py:78-107`<br>`sleeves/galath/paper.py:597-612` |
| Trim recognised by its reason text | `sleeves/galath/wire.py:254-255`<br>`sleeves/galath/paper.py:621-623` |
| Own book | `sleeves/galath/wire.py:82-99` |
| Own lane key | `sleeves/galath/galath.py:1298-1300` |

## [CCI correction pullback](../../strategies/galath/galath-cci-correction.md)

| Rule | Read from |
|---|---|
| Entry: Close ≥ $5 and 20-day average dollar volume ≥ $20M; close above the 200-day SMA and the 50-day above the 200-day. | `sleeves/galath/vendor/cci_correction/cci_correction.py:8-12`<br>`sleeves/galath/vendor/cci_correction/cci_correction.py:25-32` |
| Entry: Regime: SPY above its 200-day SMA and VIX under 30. | `sleeves/galath/vendor/cci_correction/cci_correction.py:35-39`<br>`sleeves/galath/grokbot.py:145-148` |
| Entry: Correction: the lowest CCI(27) of the last 18 sessions < -100. | `sleeves/galath/vendor/cci_correction/cci_correction.py:14-18`<br>`sleeves/galath/vendor/cci_correction/cci_correction.py:30` |
| Entry: Trigger: CCI crosses back above -100, or the close tops the prior high while CCI rises and is still below 0. | `sleeves/galath/vendor/cci_correction/cci_correction.py:33-34`<br>`sleeves/galath/vendor/cci_correction/cci_correction.py:40` |
| Entry: Decided pre-market (from 07:00 ET) on the completed session; bought 09:30-09:35 ET with marketable orders, lowest CCI first, up to 10 positions. | `sleeves/galath/grokbot.py:86-88`<br>`sleeves/galath/grokbot.py:168-170`<br>`sleeves/galath/grokbot.py:213`<br>`sleeves/galath/grokbot.py:247-261`<br>`sleeves/galath/grokbot.py:402-460`<br>master-desk `desk/schedule.py:35-37` |
| Exit: Stop 2 × ATR(14) under the fill, target the fill + 3R (6 ATR), engine-held. | `sleeves/galath/vendor/cci_correction/cci_correction.py:20-23`<br>`sleeves/galath/grokbot.py:370-392`<br>`sleeves/galath/grokbot.py:446-452` |
| Exit: Trail: the highest close since entry - 3 ATR, ratcheting up only. | `sleeves/galath/grokbot.py:182-192`<br>`sleeves/galath/grokbot.py:346-351`<br>`sleeves/galath/grokbot.py:382-385` |
| Exit: A close below the 200-day SMA sells at the next open. | `sleeves/galath/grokbot.py:195-204`<br>`sleeves/galath/grokbot.py:352-355`<br>`sleeves/galath/grokbot.py:393-398` |
| Exit: Time stop: 20 sessions counting the entry session. | `sleeves/galath/grokbot.py:413-414`<br>`sleeves/galath/grokbot.py:452` |
| Sizing: 0.5% of equity / (entry - stop), at most 15% of equity, whole shares; skipped when cash is short; a $100,000 book. | `sleeves/galath/vendor/cci_correction/cci_correction.py:11`<br>`sleeves/galath/vendor/cci_correction/cci_correction.py:43-46`<br>`sleeves/galath/grokbot.py:83`<br>`sleeves/galath/grokbot.py:177-179`<br>`sleeves/galath/grokbot.py:424-445` |
| Data: Genome split-adjusted daily bars (260 sessions, cached), SPY, VIX daily, opening quotes. | `sleeves/galath/grokbot.py:84-85`<br>`sleeves/galath/grokbot.py:211-218`<br>`sleeves/galath/grokbot.py:270-280` |
| Reference parameters | `sleeves/galath/vendor/cci_correction/cci_correction.py:6-12`<br>`sleeves/galath/grokbot.py:82` |

## [Tensor 2 washout / reclaim printer](../../strategies/galath/galath-tensor2-washout-reclaim.md)

| Rule | Read from |
|---|---|
| Entry: Read once per completed canonical hour for each of the 13 names (SATL, SKYQ, RDW, INDI, SPY, QQQ, NVDA, MU, AAPL, AMD, TSLA, WULF, POET), once the frame holds 200 bars (the source's authority). | `sleeves/galath/monitor/galath_tensor_mon.py:4-8`<br>`sleeves/galath/monitor/galath_tensor_mon.py:45-53`<br>`sleeves/galath/monitor/galath_tensor_mon.py:56-73`<br>master-desk `desk/vendor/galath_mon/src/lib/desk-store.ts:7-25` at `22f3e991`<br>`sleeves/galath/monitor/printer_books.py:39`<br>`sleeves/galath/monitor/printer_books.py:146-161` |
| Entry: Washout: within the last 9 hours, a bar's low at the 12-hour swing low with RSI(14) ≤ 42. | master-desk `desk/vendor/galath_mon/src/lib/tensor/engine.ts:169-176` at `22f3e991` |
| Entry: Green buy, on the hour: no buy signal held and no green buy in the last 12 hours; a washout; the bar closes at or above its open; RSI(14) rising from a 9-hour trough ≤ 48 and still under 58, with the MACD histogram rising; at most 0.8 ATR(14) above EMA21; the close reclaiming EMA21 or at a reclaim or launch-pad location, never extended (over 1.2 ATR above it). | master-desk `desk/vendor/galath_mon/src/lib/tensor/engine.ts:163-168` at `22f3e991`<br>master-desk `desk/vendor/galath_mon/src/lib/tensor/engine.ts:177-187` at `22f3e991`<br>master-desk `desk/vendor/galath_mon/src/lib/tensor/engine.ts:189-230` at `22f3e991` |
| Entry: Orders: each decision once, at the book's next pass in the session (from 5 minutes after the open): a market buy of one slot while the signal is buy and the name is not held, a market sell once it is no longer buy; a decision unsent by the close of the session after its bar lapses, and a name without a live equity quote is not bought. | `sleeves/galath/monitor/printer_books.py:16-27`<br>`sleeves/galath/monitor/printer_books.py:37`<br>`sleeves/galath/monitor/printer_books.py:113-135` |
| Exit: Out when the signal ends: an hour that closes below EMA21 on a red bar (the magenta sell); sold at the book's next pass in the session. No stop of its own. | master-desk `desk/vendor/galath_mon/src/lib/tensor/engine.ts:240-241` at `22f3e991`<br>master-desk `desk/vendor/galath_mon/src/lib/tensor/engine.ts:255-259` at `22f3e991`<br>`sleeves/galath/monitor/printer_books.py:131-133` |
| Sizing: An equal slot of the book's equity / 13 a name; $100,000 book. | `sleeves/galath/monitor/printer_books.py:115`<br>master-desk `desk/contract.py:136` at `22f3e991` |
| Data: Yahoo 60-minute bars (the desk's canonical 1H series, a year, regular session) and daily bars (2 years); the producer job runs 2-11 minutes after each completed hour, and a read older than 90 minutes is not used. | `sleeves/galath/monitor/galath_tensor_mon.py:4-8`<br>`sleeves/galath/monitor/galath_tensor_mon.py:17-26`<br>`sleeves/galath/monitor/galath_tensor_mon.py:38-53` |
| The Galath printer convention | `sleeves/galath/monitor/printer_books.py:16-19`<br>master-desk `docs/research/2026-10-26-recorders/CONVERT.md:48-52` at `22f3e991` |
| Converted rows | `sleeves/galath/monitor.py:1-12` |
| Conversion record | master-desk `docs/research/2026-10-26-recorders/CONVERT.md:59` at `22f3e991` |

## [Anna PhD location printer](../../strategies/galath/galath-anna-phd-printer.md)

| Rule | Read from |
|---|---|
| Entry: Votes on each completed daily bar: Stoch RSI K over D, Aroon up over down, +DI over -DI, OBV's 5-bar slope, squeeze momentum, EMA8 over EMA21, WaveTrend 1 over 2; the buy gate needs all seven readable, at least 5 bullish and 4 more than bearish. | master-desk `desk/vendor/galath_gospel/scripts/anna-phd-replay.mjs:472-518` at `22f3e991`<br>master-desk `desk/vendor/galath_gospel/scripts/anna-phd-replay.mjs:634-637` at `22f3e991` |
| Entry: Prints: a UT Bot buy flip through the gate is cyan; an EMA 8/21 cross up within 6 bars of a UT buy flip, through the gate, is green; a UT sell flip is red; an EMA 8/21 cross down within 6 bars of a UT sell flip is magenta. | master-desk `desk/vendor/galath_gospel/scripts/anna-phd-replay.mjs:604-651` at `22f3e991` |
| Entry: Location re-prints: a red or magenta print deep under EMA200 (the close at most 65% of it) with at least 5 bullish votes turns cyan; an EMA200 reclaim inside the band, a confirmed gold warning, a launch-pad sequence and a support bounce print cyan; a failed euphoria or an extended failure prints magenta. | master-desk `desk/vendor/galath_gospel/scripts/anna-phd-replay.mjs:678-829` at `22f3e991` |
| Entry: Read after each close by the producer job (the replay under Node over the census names); the session's decision trades at the book's first pass of the next session. | `sleeves/galath/monitor/galath_phd_mon.py:1-12`<br>`sleeves/galath/monitor/galath_phd_mon.py:105-115`<br>`sleeves/galath/monitor/printer_books.py:168-198`<br>`sleeves/galath/monitor/printer_books.py:209-212` |
| Entry: Orders: each decision once, at the book's next pass in the session (from 5 minutes after the open): a market buy of one slot while the signal is buy and the name is not held, a market sell once it is no longer buy; a decision unsent by the close of the session after its bar lapses, and a name without a live equity quote is not bought. | `sleeves/galath/monitor/printer_books.py:16-27`<br>`sleeves/galath/monitor/printer_books.py:37`<br>`sleeves/galath/monitor/printer_books.py:113-135` |
| Exit: Out when the signal turns sell: a red or magenta print, or, while long, a close crossing below EMA200. No stop of its own. | master-desk `desk/vendor/galath_gospel/scripts/anna-phd-replay.mjs:833-846` at `22f3e991`<br>`sleeves/galath/monitor/printer_books.py:131-133` |
| Sizing: An equal slot of the book's equity / 115 a name; $100,000 book. | `sleeves/galath/monitor/printer_books.py:115`<br>master-desk `desk/contract.py:136` at `22f3e991` |
| Data: Yahoo daily bars (2 years; Nasdaq or Cboe while Yahoo refuses), completed sessions only. | `sleeves/galath/monitor/galath_phd_mon.py:14-18`<br>`sleeves/galath/monitor/galath_phd_mon.py:37`<br>`sleeves/galath/monitor/galath_phd_mon.py:77-86` |
| The Galath printer convention | `sleeves/galath/monitor/printer_books.py:16-19`<br>master-desk `docs/research/2026-10-26-recorders/CONVERT.md:48-52` at `22f3e991` |
| Converted rows | `sleeves/galath/monitor.py:1-12` |
| Census names | `sleeves/galath/monitor/galath_phd_mon.py:52-71` |
| Conversion record | master-desk `docs/research/2026-10-26-recorders/CONVERT.md:60` at `22f3e991` |
