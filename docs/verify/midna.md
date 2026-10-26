# Verification: Midna

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk), or at `22f3e991c224` where a cite names it (the four recorders converted into books on 2026-10-26); every other path is in this repository.

## [Faber ETF trend (10-month average)](../../strategies/midna/mn-faber.md)

| Rule | Read from |
|---|---|
| Entry: Midna book: buys a fund whose last close is above the mean of the ten month-end closes before the current month; acts on the session after the signal session, from 10:00 ET. | master-desk `desk/vendor/midna/quantpedia_signals.py:19`<br>master-desk `desk/vendor/midna/quantpedia_signals.py:60-67`<br>master-desk `desk/sleeves/midna/quantpedia.py:96-106`<br>master-desk `desk/sleeves/midna/quantpedia.py:40-47` |
| Entry: Griffith book: at the first pass of each month, on the prior month's last SPY bar, holds every basket ETF whose month-end close is above the mean of the last 10 month-end closes (that one included). | `sleeves/griffith/griffith_factor.py:56`<br>`sleeves/griffith/griffith_factor.py:68-106`<br>`sleeves/griffith/griffith_factor.py:169-202`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:31`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:118-125` |
| Entry: Griffith basket: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLI, XLP, XLV, XLU, TLT and GLD (the frozen 17 less XLY, XLB, XLRE and IEF, which the tape never carries); each needs a bar on the cutoff day. | `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:19-22`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:107-111`<br>`sleeves/griffith/griffith_factor.py:68-74`<br>`sleeves/griffith/feedlib/griffith.py:34-40` |
| Exit: Sells a held fund that is no longer above its average (Griffith: at the next month's rebalance). | master-desk `desk/sleeves/midna/quantpedia.py:96-106`<br>`sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-218` |
| Sizing: Midna book: dollars = min(cash, equity / 5); whole shares at the ask. | master-desk `desk/sleeves/midna/quantpedia.py:30-31`<br>master-desk `desk/sleeves/midna/quantpedia.py:82-94` |
| Sizing: Griffith book: $100,000 in equal weights over the ETFs held, as marketable limits 1% through the quote (30 minutes), re-sent on each of the month's first 5 sessions. | `sleeves/griffith/griffith_factor.py:53`<br>`sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-221`<br>master-desk `desk/contract.py:62-68`<br>master-desk `desk/contract.py:136` |
| Data: Yahoo daily closes, two years. | master-desk `desk/vendor/midna/quantpedia_signals.py:40-58` |
| Data: Griffith book: Alpaca IEX raw daily bars (the last 550 sessions), Yahoo without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |
| Midna v3 reading | `sleeves/s_mn_faber.py:1-20` |

## [Large-cap prior-month reversal](../../strategies/midna/mn-prior-month-reversal.md)

| Rule | Read from |
|---|---|
| Entry: The five worst of the 40 by prior calendar-month return are the targets. | master-desk `desk/vendor/midna/quantpedia_signals.py:69-76`<br>master-desk `desk/sleeves/midna/quantpedia.py:108-123` |
| Exit: A held name that is no longer in the worst five is sold. | master-desk `desk/sleeves/midna/quantpedia.py:108-123` |
| Sizing: dollars = min(cash, equity / 5); whole shares; at most 5 names. | master-desk `desk/sleeves/midna/quantpedia.py:82-94` |
| Data: Yahoo daily closes. | master-desk `desk/vendor/midna/quantpedia_signals.py:40-58` |
| Midna v3 reading | `sleeves/s_mn_reversal.py:1-12` |

## [Distance-pair shares](../../strategies/midna/mn-distance-pair.md)

| Rule | Read from |
|---|---|
| Entry: Pairs: the 20 with the smallest squared distance of normalized prices over 252 sessions. | master-desk `desk/vendor/midna/quantpedia_signals.py:79-91` |
| Entry: Buys the cheaper normalized leg when \|z\| ≥ 2, closest pairs first. | master-desk `desk/vendor/midna/quantpedia_signals.py:92-102`<br>master-desk `desk/sleeves/midna/quantpedia.py:125-146` |
| Exit: Sells the leg once \|z\| < 0.5. | master-desk `desk/sleeves/midna/quantpedia.py:125-137` |
| Sizing: dollars = min(cash, equity / 5); at most 5 names. | master-desk `desk/sleeves/midna/quantpedia.py:82-94` |
| Data: Yahoo daily closes. | master-desk `desk/vendor/midna/quantpedia_signals.py:40-58` |
| Midna v3 reading | `sleeves/s_mn_pairs.py:1-12` |

## [Turtle System 1](../../strategies/midna/mn-turtle.md)

| Rule | Read from |
|---|---|
| Entry: A close above the prior 20-day (or 55-day) high, new today; at most 4 names, alphabetical. | `sleeves/midna/vendor/midna/board_signals.py:120-165`<br>`sleeves/midna/board.py:184-206` |
| Entry: A 20-day breakout right after a winning exit is skipped once; the 55-day one is taken. | `sleeves/midna/board.py:194-202` |
| Entry: Adds a unit at each +0.5N over the last add, up to 4 units. | `sleeves/midna/board.py:159-171` |
| Exit: Stop at entry - 2N (raised with adds), on any regular-hours print; signal exit on a close under the prior 10-day low. | `sleeves/midna/board.py:114-133`<br>`sleeves/midna/board.py:144-157`<br>`sleeves/midna/board.py:225-247` |
| Sizing: Unit = min(floor(1% of equity / N), floor(cash / price)), N = ATR(20). | `sleeves/midna/board.py:34-37`<br>`sleeves/midna/board.py:48-54` |
| Data: Completed daily bars of the swing basket. | `sleeves/midna/vendor/midna/board_signals.py:100-120` |

## [MACD-CCI](../../strategies/midna/mn-macd-cci.md)

| Rule | Read from |
|---|---|
| Entry: MACD(12, 26) crosses above its 9-period signal with CCI(20) > 100; ranked by CCI; up to 4 names. | `sleeves/midna/vendor/midna/board_signals.py:120-165`<br>`sleeves/midna/board.py:208-224` |
| Exit: The cross back down, or the price under the peak since entry - 3 × ATR(14). | `sleeves/midna/board.py:144-157`<br>`sleeves/midna/board.py:225-247` |
| Sizing: One unit = min(floor(1% of equity / ATR14), floor(cash / price)). | `sleeves/midna/board.py:48-54`<br>`sleeves/midna/board.py:220-224` |
| Data: Completed daily bars. | `sleeves/midna/vendor/midna/board_signals.py:100-120` |
| Midna v3 reading | `sleeves/s_mn_macd.py:1-10` |

## [EMA4 rising VWAP](../../strategies/midna/mn-ema4-vwap.md)

| Rule | Read from |
|---|---|
| Entry: EMA(4) crosses above the 20-session volume-weighted typical price while that VWAP is above its value 5 sessions earlier; alphabetical; up to 4 names. | `sleeves/midna/vendor/midna/board_signals.py:120-165`<br>`sleeves/midna/board.py:208-224` |
| Exit: The cross back, or the 3 × ATR(14) chandelier under the peak. | `sleeves/midna/board.py:144-157`<br>`sleeves/midna/board.py:225-247` |
| Sizing: One unit = min(floor(1% of equity / ATR14), floor(cash / price)). | `sleeves/midna/board.py:48-54` |
| Data: Completed daily bars. | `sleeves/midna/vendor/midna/board_signals.py:100-120` |
| Midna v3 reading | `sleeves/s_mn_vwap.py:1-10` |

## [QQQ flip5 TZA hedge](../../strategies/midna/mn-qqq-flip5-tza.md)

| Rule | Read from |
|---|---|
| Entry: flip5: QQQ's slow state turned bearish on one of the last five closed daily bars. | master-desk `desk/feedlib/midna_watch.py:115-130` |
| Entry: With nothing held, flip5 stages a buy for the next session's open. | `sleeves/midna/shadow.py:41-70` |
| Exit: Sells at the next open when flip5 is off or after 20 held sessions. | `sleeves/midna/shadow.py:36`<br>`sleeves/midna/shadow.py:61-66` |
| Sizing: Notional = 30% × $100,000 at the open. | `sleeves/midna/shadow.py:35-37`<br>`sleeves/midna/shadow.py:52` |
| Data: QQQ and TZA daily bars from the hourly watch. | master-desk `desk/feedlib/midna_watch.py:115-130` |

## [QLD weekly timing](../../strategies/midna/mn-qld-weekly-timing.md)

| Rule | Read from |
|---|---|
| Entry: Prior completed QQQ week: EMA(12) above EMA(26) of weekly closes (SMA-seeded, from 1990 adjusted daily history). | `sleeves/midna/qld.py:61-83`<br>`sleeves/midna/qld.py:117-127` |
| Entry: Trades in the first regular-hours pass of the week. | `sleeves/midna/qld.py:141-169` |
| Exit: Sells QLD at the open of a week whose prior week shows EMA(12) ≤ EMA(26). | `sleeves/midna/qld.py:84-116` |
| Sizing: The whole book: notional = cash / (1 + 0.1%). | `sleeves/midna/qld.py:25-26`<br>`sleeves/midna/qld.py:84-116` |
| Data: Yahoo QQQ and QLD daily history. | `sleeves/midna/qld.py:29-60` |

## [Listed Turtle ATM call](../../strategies/midna/mn-opt-turtle.md)

| Rule | Read from |
|---|---|
| Entry: On a 20- or 55-day breakout: the expiry nearest 30 days (14-60) and the strike nearest spot; ask ≥ $0.20, spread ≤ 50% of mid; at most 4 open. | master-desk `desk/sleeves/midna/options.py:45-53`<br>master-desk `desk/sleeves/midna/options.py:211-276` |
| Exit: Closed when the stock trades at or under last - 2 × ATR20, on the 10-day low exit, or at expiry. | master-desk `desk/sleeves/midna/options.py:193-210`<br>master-desk `desk/sleeves/midna/options.py:242-276` |
| Sizing: qty = floor(min(cash, 1% of equity) / (ask × 100)). | master-desk `desk/sleeves/midna/options.py:211-241` |
| Data: Cboe delayed option chains; board signals. | master-desk `desk/sleeves/midna/options.py:96-104` |

## [Listed reversal call spread](../../strategies/midna/mn-opt-reversal.md)

| Rule | Read from |
|---|---|
| Entry: Long the ATM call, short the listed strike nearest 5% above; debit ≥ $0.20; while fewer than five are open. | master-desk `desk/sleeves/midna/options.py:64-85`<br>master-desk `desk/sleeves/midna/options.py:277-330` |
| Exit: Closed when the name leaves the five, or at expiry. | master-desk `desk/sleeves/midna/options.py:309-330` |
| Sizing: qty = floor(min(cash, equity / 5) / debit). | master-desk `desk/sleeves/midna/options.py:277-308` |
| Data: Cboe delayed option chains; the reversal signal. | master-desk `desk/sleeves/midna/options.py:96-104` |

## [Listed distance-pair package](../../strategies/midna/mn-opt-distance-pair.md)

| Rule | Read from |
|---|---|
| Entry: On a listed pair with \|z\| ≥ 2: call on the cheap leg, put on the rich leg. | master-desk `desk/sleeves/midna/options.py:335-397` |
| Exit: Closed when \|z\| < 0.5, or at expiry. | master-desk `desk/sleeves/midna/options.py:369-397` |
| Sizing: Budget = min(cash, equity / 5) per package. | master-desk `desk/sleeves/midna/options.py:358` |
| Data: Cboe delayed option chains; the pairs signal. | master-desk `desk/sleeves/midna/options.py:96-104` |

## [Hyperliquid momentum floor](../../strategies/midna/mn-hyperliquid-floor.md)

| Rule | Read from |
|---|---|
| Entry: Long when up ≥ 1% with funding ≤ 0.004%; short when down ≥ 1% with funding ≥ -0.001%; BTC, ETH, SOL first. | `sleeves/midna/hyperliquid.py:39-44`<br>`sleeves/midna/hyperliquid.py:49-73` |
| Exit: Stop = max(0.6%, 1.2 × the mean hourly range of 8 hours), ≤ 8%; target 2R; closed on a mark through either. | `sleeves/midna/hyperliquid.py:74-79`<br>`sleeves/midna/hyperliquid.py:100-105`<br>`sleeves/midna/hyperliquid.py:120-125` |
| Sizing: Risk 0.5% of equity per trade, single-name cap 20%, gross cap 60%, ≥ $50, at most 3 open. | `sleeves/midna/hyperliquid.py:43-44`<br>`sleeves/midna/hyperliquid.py:80-99` |
| Data: Hyperliquid public market data. | `sleeves/midna/hyperliquid.py:126-172` |

## [Kronos-base TopkDropout](../../strategies/midna/mn-kronos-topk.md)

| Rule | Read from |
|---|---|
| Entry: Score = the forecast close in 10 sessions / the last close - 1, rebuilt every 10 sessions. | master-desk `desk/sleeves/midna/kronos.py:33-37`<br>master-desk `desk/sleeves/quant_research/kronos.py:47-61` |
| Entry: Quant research book: from 2024-07-01, after every 10th session's close, the released Kronos-base model reads each name's last 90 sessions and samples 10 paths 10 sessions ahead (temperature 0.6, top-p 0.9, fixed seeds); the score uses their mean. A name also needs 252 complete prior sessions, a 20-session average dollar volume ≥ $10M and a close ≥ $5. | master-desk `desk/sleeves/quant_research/kronos.py:73-90`<br>master-desk `desk/sleeves/quant_research/kronos.py:97-124`<br>master-desk `desk/sleeves/quant_research/kronos_runner.py:66-86`<br>master-desk `desk/sleeves/quant_research/kronos.py:76-77`<br>`sleeves/quant_research/common.py:186-205` |
| Entry: TopkDropout: drop the worst held name held ≥ 5 sessions and out of today's top 5, then fill back to 4. | master-desk `desk/sleeves/midna/kronos.py:42-70`<br>`sleeves/quant_research/vendor/quant_research/sixai/shared/dropout.py:28-58` |
| Exit: Sold when dropped from the targets. | master-desk `desk/sleeves/midna/kronos.py:80-140`<br>`sleeves/quant_research/vendor/quant_research/sixai/shared/dropout.py:44-55` |
| Sizing: Midna book: slice = 95% of equity / 4 on its own $100,000 book; whole shares at last ± 0.1%. | master-desk `desk/sleeves/midna/kronos.py:36-37`<br>master-desk `desk/sleeves/midna/kronos.py:119` |
| Sizing: Quant research book: $1,000,000; buys share 95% of the cash left after sales (net of 15 bp, buys grossed up 15 bp) equally; every trade ≤ 1% of the name's 20-session dollar volume; fractional shares; marketable limits 1% through the quote, good for 30 minutes, sells first. | master-desk `desk/sleeves/quant_research/kronos.py:155`<br>`sleeves/quant_research/dropout_book.py:27`<br>`sleeves/quant_research/vendor/quant_research/sixai/shared/dropout.py:69-70`<br>`sleeves/quant_research/sixai.py:163-184`<br>`sleeves/quant_research/common.py:78-97` |
| Data: Kronos-base forecasts on daily bars. | master-desk `desk/sleeves/midna/kronos.py:80-90` |
| Data: Quant research book: split-adjusted daily bars of the 24 names; the pinned Kronos-base weights, verified by hash and run by a separate interpreter with torch. | master-desk `desk/sleeves/quant_research/kronos.py:93-94`<br>master-desk `desk/sleeves/quant_research/kronos.py:108`<br>master-desk `desk/sleeves/quant_research/kronos.py:113-116`<br>master-desk `desk/sleeves/quant_research/kronos_runner.py:35-50` |
| Universe: the 24 most liquid eligible names on 2024-06-28 | master-desk `desk/sleeves/quant_research/kronos.py:38-39`<br>master-desk `desk/vendor/quant_research/kronos/registration.json:16-43` |

## [Forward lab accounts (Tensor scan)](../../strategies/midna/mn-forward-lab.md)

| Rule | Read from |
|---|---|
| Entry: Rules: weekly Cyan with dollar-volume, breadth or VIX limits; daily Green $10-20 with dispersion and gap-age limits; weekly Green with skew, SMH-SPY and no FOMC in 5 sessions. | `sleeves/midna/forward_scan.py:689-753` |
| Entry: Up to 6 hits per account, best score first; entry from 10:00 ET on the session after the signal. | `sleeves/midna/forward_scan.py:755-779`<br>`sleeves/midna/forward.py:54-127` |
| Exit: Sells once the hold (21, 126 or 252 sessions) is reached. | `sleeves/midna/forward_scan.py:740-753`<br>`sleeves/midna/forward.py:70-127` |
| Sizing: qty = floor((20,000 / 6) / (price × (1 + cost))), capped by cash. | `sleeves/midna/forward.py:62-69` |
| Data: Midna's daily panel, the Tensor engine and the frozen v4 GBM. | `sleeves/midna/forward_scan.py:781-844` |

## [Hourly Tensor playbook](../../strategies/midna/mn-hourly-playbook.md)

| Rule | Read from |
|---|---|
| Entry: Fire: a gap20, first-of-setup 1H consensus buy; skipped when its unit matches a killed rule, it is not tradeable, or dv20 < $1M. | `sleeves/midna/hourly.py:46-58`<br>`sleeves/midna/hourly.py:164-171`<br>`sleeves/midna/hourly.py:208-260` |
| Entry: Window: the next bar's open + 30 min (1D / 1W: 09:30 + 65 min); price within 3% (1H) or 5% of the fire close. | `sleeves/midna/hourly.py:51-53`<br>`sleeves/midna/hourly.py:112-125` |
| Exit: 1h-basket plan: no stop, time exit 60 bars; otherwise the calibrated stop and max bars. | `sleeves/midna/hourly.py:126-163`<br>`sleeves/midna/hourly.py:172-191` |
| Sizing: $100,000 account, 20 slots of min($5,000, 1% of dv20); lane caps 1h 5 / 1d 5 / 1w 10. | `sleeves/midna/hourly.py:46-53`<br>`sleeves/midna/hourly.py:208-321` |
| Data: The hourly watch's inbox (tensor-watch port). | `sleeves/midna/hourly.py:419-426` |

## [Weekly 8/20/50 pullback](../../strategies/midna/mn-weekly-8-20-50-pullback.md)

| Rule | Read from |
|---|---|
| Entry: Signal, on a completed week (its last session a Friday, else once the next week begins): EMA8 > EMA20 > EMA50 of the weekly closes, the close above EMA50, the week's low at or under EMA8 and the close above the low; at least 60 weeks of history. | `sleeves/midna/monitor/midna_books.py:186-191`<br>`sleeves/midna/monitor/midna_books.py:194-209`<br>`sleeves/midna/monitor/midna_books.py:212-222` |
| Entry: Levels: entry at the week's close, stop = entry - weekly ATR(5), target = entry + ATR, deadline = the last session of the fifth week after. | `sleeves/midna/monitor/midna_books.py:225-254`<br>`sleeves/midna/monitor/midna_books.py:433-440` |
| Entry: Decided after that week's close: at most 10 names held, the week's signals by RSI(14) ascending, then symbol; bought at the book's first pass of the next session, skipped when the price is already at or under the stop. | `sleeves/midna/monitor/midna_books.py:26-30`<br>`sleeves/midna/monitor/midna_books.py:567-586`<br>`sleeves/midna/monitor/midna_books.py:588-603` |
| Exit: Stop at entry - weekly ATR(5), held by the engine on the live price. | `sleeves/midna/monitor/midna_books.py:31-32`<br>`sleeves/midna/monitor/midna_books.py:610-611` |
| Exit: A quarter sold the first time the live price reaches the target; the rest by a market-on-close order on the deadline session. | `sleeves/midna/monitor/midna_books.py:31-33`<br>`sleeves/midna/monitor/midna_books.py:617-635` |
| Sizing: A tenth of equity a name, never more than the cash, divided by 1.001 for the source's cost; $100,000 book. | `sleeves/midna/monitor/midna_books.py:514`<br>`sleeves/midna/monitor/midna_books.py:604-610`<br>master-desk `desk/contract.py:136` at `22f3e991` |
| Data: Yahoo daily bars (1,600 sessions), adjusted as Midna's live board adjusts them (OHLC × adjclose / close), built into weeks. | `sleeves/midna/monitor/midna_books.py:36-37`<br>`sleeves/midna/monitor/midna_books.py:415-430`<br>`sleeves/midna/monitor/midna_books.py:517-521` |
| Primary options | `sleeves/midna/monitor/midna_books.py:139` |
| The nineteen funds | `sleeves/midna/vendor/midna_mon/src/lib/felipe/pullback.ts:13-18` |
| Conversion record | master-desk `docs/research/2026-10-26-recorders/CONVERT.md:57` at `22f3e991`<br>master-desk `docs/research/2026-10-26-recorders/CONVERT.md:63-64` at `22f3e991`<br>master-desk `docs/research/2026-10-26-recorders/CONVERT.md:71-72` at `22f3e991` |

## [TSMOM 12-1 ETF book](../../strategies/midna/mn-tsmom-12-1-etf.md)

| Rule | Read from |
|---|---|
| Entry: Sign 12-1: the adjusted close 21 sessions back over the one 252 sessions before it, minus one, > 0; the panel is aligned to SPY's sessions and a name needs 260 valid sessions. | `sleeves/midna/monitor/midna_books.py:447-459`<br>`sleeves/midna/monitor/midna_books.py:462-486` |
| Entry: Every 21 sessions from the book's first session, in the last 40 to 15 minutes of the session: equal weights over the names with a positive sign, as market-on-close orders. | `sleeves/midna/monitor/midna_books.py:645`<br>`sleeves/midna/monitor/midna_books.py:649-651`<br>`sleeves/midna/monitor/midna_books.py:663-668`<br>`sleeves/midna/monitor/midna_books.py:680-716` |
| Exit: A held name whose sign is no longer positive goes to cash at that rebalance (market-on-close); the weights drift in between; no stop. | `sleeves/midna/monitor/midna_books.py:21-24`<br>`sleeves/midna/monitor/midna_books.py:712-714` |
| Sizing: 1 / N of the book a long; $100,000 book. | `sleeves/midna/monitor/midna_books.py:705-711`<br>master-desk `desk/contract.py:136` at `22f3e991` |
| Data: Yahoo daily bars (600 sessions) of the 30 ETFs on rebalance days, adjusted closes (the close when the provider gives none). | `sleeves/midna/monitor/midna_books.py:43`<br>`sleeves/midna/monitor/midna_books.py:651`<br>`sleeves/midna/monitor/midna_books.py:670-671` |
| The study's ETF book | `sleeves/midna/vendor/midna_mon/scripts/tsmom-forms.ts:331-339` |
| The panel | `sleeves/midna/vendor/midna_mon/scripts/tsmom-forms.ts:22-28` |
| Conversion record | master-desk `docs/research/2026-10-26-recorders/CONVERT.md:58` at `22f3e991`<br>master-desk `docs/research/2026-10-26-recorders/CONVERT.md:65-70` at `22f3e991` |
