# Verification: Griffith

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk), or at `22f3e991c224` where a cite names it (the four recorders converted into books on 2026-10-26); every other path is in this repository.

## [Leaders Rest](../../strategies/griffith/griffith-leaders-rest.md)

| Rule | Read from |
|---|---|
| Entry: Decision: once a trading day before the open (else at the session's first pass), on the last completed bars, through the source's orchestrator over the universe. | `sleeves/griffith/griffith.py:159-162`<br>`sleeves/griffith/griffith.py:172-187`<br>`sleeves/griffith/griffith.py:335-345` |
| Entry: Leader: ≥ 253 sessions; price ≥ $10 or 20-day dollar volume ≥ $20M; within 25% of the 52-week high; EMA 50 rising over 10 sessions; 12-1 momentum above SPY's; price above EMA 50 (or above EMA 21 with EMA 50 rising); SPY not below a falling EMA 50, and SPY's 12-1 momentum not under -4% while SPY is under its EMA 200 or its EMA 50 is falling. | `sleeves/griffith/vendor/griffith/strategy_system.py:133-161`<br>`sleeves/griffith/vendor/griffith/strategy_orchestrator.py:95-103` |
| Entry: SETUP: resting (3-12% under the 20-day high, or the last 15 days' range ≤ 60% of the prior 20 days' with 2-18% off the 52-week high) and RSI(14) 48-68. | `sleeves/griffith/vendor/griffith/strategy_system.py:162-179` |
| Entry: Order: a GTC buy limit at the decision close, armed 5 days. | `sleeves/griffith/vendor/griffith/strategy_execution.py:76-83`<br>`sleeves/griffith/griffith.py:239-243`<br>`sleeves/griffith/griffith.py:268-269`<br>`sleeves/griffith/griffith.py:284-289` |
| Entry: Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit. | `sleeves/griffith/griffith.py:259-275`<br>`sleeves/griffith/griffith.py:292-326`<br>`sleeves/griffith/griffith.py:348`<br>master-desk `desk/vendor/griffith/config.json:21` |
| Exit: Bracket: stop at the limit - 1.6 ATR, target at the limit + 2.8 ATR (ATR(14), at least 1.5% of price). | `sleeves/griffith/vendor/griffith/strategy_execution.py:77-83`<br>`sleeves/griffith/griffith.py:264-266` |
| Sizing: Risk 0.5% of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power; a held name is not added to; $100,000 book. | `sleeves/griffith/vendor/griffith/strategy_execution.py:83`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:203-241`<br>master-desk `desk/vendor/griffith/config.json:179-190`<br>`sleeves/griffith/griffith.py:135-138`<br>`sleeves/griffith/griffith.py:189-212`<br>`sleeves/griffith/griffith.py:249-252`<br>master-desk `desk/contract.py:136` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |
| Bracket only | `sleeves/griffith/griffith.py:264-266` |
| Champion version only | `sleeves/griffith/griffith.py:233-248`<br>master-desk `desk/vendor/griffith/config.json:84-89` |

## [Parallax](../../strategies/griffith/griffith-parallax.md)

| Rule | Read from |
|---|---|
| Entry: Decision: once a trading day before the open (else at the session's first pass), on the last completed bars, through the source's orchestrator over the universe. | `sleeves/griffith/griffith.py:159-162`<br>`sleeves/griffith/griffith.py:172-187`<br>`sleeves/griffith/griffith.py:335-345` |
| Entry: Field: each sector ETF against SPY (10-, 20- and 126-day relative strength, its 126-day percentile among the sectors, the EMA 50 slope) reads WATERFALL, TURN, TROUGH or TREND; names outside the sector map read TURN; a WATERFALL or unreadable field gives no decision. | `sleeves/griffith/vendor/griffith/strategy_orchestrator.py:34-50`<br>`sleeves/griffith/vendor/griffith/strategy_orchestrator.py:92-99`<br>`sleeves/griffith/vendor/griffith/strategy_system.py:254-255` |
| Entry: Regime: across the universe, the median day, the share up over 20 days, the median ATR% and the spread of 20-day returns give PANIC, REFLEXIVE_REBOUND, HIGH_VOLATILITY_DELEVERAGING, ORDERLY_RISK_ON, NARROW_RISK_ON or RANGE_BOUND; the medians of 5-, 20- and 60-day returns are the benchmark. | `sleeves/griffith/vendor/griffith/strategy_orchestrator.py:53-74`<br>`sleeves/griffith/vendor/griffith/strategy_orchestrator.py:91` |
| Entry: Engines, 0-100 on returns over that benchmark: DRIFT (20- and 60-day residuals, 20-day path efficiency, above EMA 50, not stretched), DISLOCATION (a 5-day shock against ATR, close location, RSI < 45, MACD turning up), COMPRESSION (a low 20-day range percentile near the 20-day high), RECLAIM (yesterday under the 20-day low, today back above it in the top 45% of the range); TREND allows drift or compression, TURN dislocation, reclaim or compression, TROUGH dislocation or reclaim; the field's own engine gets +6. | `sleeves/griffith/vendor/griffith/strategy_system.py:256-286` |
| Entry: BUY: opportunity = the engine score less penalties (ATR over 4%, thin or heavy volume, a large shock, a stretch over EMA 20) ≥ 48; relative volume ≥ 2.8 is AVOID; a PANIC or HIGH_VOLATILITY_DELEVERAGING regime or a TROUGH field is WAIT. | `sleeves/griffith/vendor/griffith/strategy_system.py:287-292` |
| Entry: Orders: DRIFT, RECLAIM, DISLOCATION a GTC limit at the decision close, armed 2 days; COMPRESSION a stop-limit at the 20-day high + 0.05 ATR (limit + 0.20 ATR), armed 7 days. | `sleeves/griffith/vendor/griffith/strategy_execution.py:110-113`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:153-165`<br>`sleeves/griffith/griffith.py:239-243` |
| Entry: Conditional paper lane: the 8 best WAITs a run of the challenger version with an allowed engine and score ≥ 70 arm stop-limits above the close (the trigger 0.20-0.35 ATR over it by engine, or the 20-day high + 0.05 ATR for compression; the limit at least 0.10 ATR higher), armed 3 days (compression 5). | `sleeves/griffith/griffith.py:221-232`<br>`sleeves/griffith/griffith.py:246-248`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:101-152`<br>master-desk `desk/vendor/griffith/config.json:93-101` |
| Entry: Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit. | `sleeves/griffith/griffith.py:259-275`<br>`sleeves/griffith/griffith.py:292-326`<br>`sleeves/griffith/griffith.py:348`<br>master-desk `desk/vendor/griffith/config.json:21` |
| Exit: Brackets: DRIFT -1.5 / +2.5 ATR, RECLAIM -1.25 / +2.25 ATR, DISLOCATION -1.5 / +2.25 ATR; COMPRESSION a stop 0.25 ATR under the compression low and a target 2.5 × the risk; the conditional lane keeps those stops with a target 2.5 × the risk. | `sleeves/griffith/vendor/griffith/strategy_execution.py:118-142`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:153-165`<br>`sleeves/griffith/griffith.py:264-266` |
| Sizing: Risk 0.35% (the conditional lane 0.5%) of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power; a held name is not added to; $100,000 book. | `sleeves/griffith/vendor/griffith/strategy_execution.py:146`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:165`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:203-241`<br>master-desk `desk/vendor/griffith/config.json:179-190`<br>`sleeves/griffith/griffith.py:135-138`<br>`sleeves/griffith/griffith.py:189-212`<br>`sleeves/griffith/griffith.py:249-252`<br>master-desk `desk/contract.py:136` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |
| Sector ETFs off the tape | `sleeves/griffith/vendor/griffith/strategy_orchestrator.py:15`<br>`sleeves/griffith/vendor/griffith/strategy_orchestrator.py:20-21`<br>`sleeves/griffith/vendor/griffith/strategy_orchestrator.py:93-99`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/vendor/griffith/strategy_system.py:254-255` |
| Bracket only | `sleeves/griffith/griffith.py:264-266` |

## [Cross-sectional momentum (12-1 / 6-1)](../../strategies/griffith/griffith-xs-momentum.md)

| Rule | Read from |
|---|---|
| Entry: Decision: at the first pass of each month, on the prior month's last SPY bar; the month waits until the tape carries 99% of the names it can. | `sleeves/griffith/griffith_factor.py:56`<br>`sleeves/griffith/griffith_factor.py:68-106`<br>`sleeves/griffith/griffith_factor.py:169-202` |
| Entry: Score: the close 21 sessions before the cutoff / the close 252 (12-1) or 126 (6-1) sessions before - 1, for names with a bar on the cutoff day and 60 sessions of positive volume; at least 10 names. | `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:27-28`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:63-70`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:77-94` |
| Entry: Pick: the top half by 60-day median dollar volume, then its top decile by score (rounded up, at least 1; ties by symbol). | `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:95-99` |
| Entry: Orders: each pick at 1/N of the book and the rest to zero, as marketable limits (1% through the quote, 30 minutes), re-sent on each of the month's first 5 sessions. | `sleeves/griffith/griffith_factor.py:53`<br>`sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-221`<br>master-desk `desk/contract.py:62-68` |
| Exit: A name out of the next month's pick is sold at that rebalance; an empty pick is cash. | `sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-218` |
| Sizing: $100,000 book in equal weights. | `sleeves/griffith/griffith_factor.py:189`<br>master-desk `desk/contract.py:136` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |

## [52-week-high strength](../../strategies/griffith/griffith-52w-high-rs.md)

| Rule | Read from |
|---|---|
| Entry: Decision: at the first pass of each month, on the prior month's last SPY bar; the month waits until the tape carries 99% of the names it can. | `sleeves/griffith/griffith_factor.py:56`<br>`sleeves/griffith/griffith_factor.py:68-106`<br>`sleeves/griffith/griffith_factor.py:169-202` |
| Entry: Score: the cutoff close / the highest high of the last 252 sessions, for names with a bar on the cutoff day and 60 sessions of positive volume; at least 10 names. | `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:29`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:71-80`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:83-94` |
| Entry: Pick: the top half by 60-day median dollar volume, then its top decile by score (rounded up, at least 1; ties by symbol). | `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:95-99` |
| Entry: Orders: each pick at 1/N of the book and the rest to zero, as marketable limits (1% through the quote, 30 minutes), re-sent on each of the month's first 5 sessions. | `sleeves/griffith/griffith_factor.py:53`<br>`sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-221`<br>master-desk `desk/contract.py:62-68` |
| Exit: A name out of the next month's pick is sold at that rebalance; an empty pick is cash. | `sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-218` |
| Sizing: $100,000 book in equal weights. | `sleeves/griffith/griffith_factor.py:189`<br>master-desk `desk/contract.py:136` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |

## [ETF 12-month time-series momentum](../../strategies/griffith/griffith-etf-tsmom12.md)

| Rule | Read from |
|---|---|
| Entry: Decision: at the first pass of each month, on the prior month's last SPY bar; the month waits until the tape carries 99% of the names it can. | `sleeves/griffith/griffith_factor.py:56`<br>`sleeves/griffith/griffith_factor.py:68-106`<br>`sleeves/griffith/griffith_factor.py:169-202` |
| Entry: Basket: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLI, XLP, XLV, XLU, TLT and GLD (the frozen 17 less XLY, XLB, XLRE and IEF, which the tape never carries); each needs a bar on the cutoff day. | `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:19-22`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:107-111`<br>`sleeves/griffith/griffith_factor.py:68-74`<br>`sleeves/griffith/feedlib/griffith.py:34-40` |
| Entry: Long when the cutoff close is above the close 252 sessions before (253 bars needed). | `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:30`<br>`sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py:112-117` |
| Entry: Orders: each pick at 1/N of the book and the rest to zero, as marketable limits (1% through the quote, 30 minutes), re-sent on each of the month's first 5 sessions. | `sleeves/griffith/griffith_factor.py:53`<br>`sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-221`<br>master-desk `desk/contract.py:62-68` |
| Exit: A name out of the next month's pick is sold at that rebalance; an empty pick is cash. | `sleeves/griffith/griffith_factor.py:189-191`<br>`sleeves/griffith/griffith_factor.py:204-218` |
| Sizing: $100,000 book in equal weights. | `sleeves/griffith/griffith_factor.py:189`<br>master-desk `desk/contract.py:136` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |

## [Simple daily trend cohorts](../../strategies/griffith/griffith-simple-daily-trend.md)

| Rule | Read from |
|---|---|
| Entry: Observation: each session, every name with close > SMA 200 and SMA 50 > SMA 200 on its last completed bar (253 bars needed). | `sleeves/griffith/vendor/griffith/strategy_tournament.py:54-66`<br>`sleeves/griffith/griffith_factor.py:239-253`<br>`sleeves/griffith/griffith_factor.py:261-268` |
| Entry: Entry: at the session's first pass with a live quote, a fixed slot of $100,000 / 550 (about $182) as a marketable limit good for an hour; one cohort per name, none while it is held or working. | `sleeves/griffith/griffith_factor.py:55`<br>`sleeves/griffith/griffith_factor.py:261-281`<br>master-desk `desk/contract.py:62-68` |
| Exit: Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1). | `sleeves/griffith/griffith_factor.py:54`<br>`sleeves/griffith/griffith_factor.py:282-289` |
| Sizing: A fixed $182 slot per cohort. | `sleeves/griffith/griffith_factor.py:269`<br>master-desk `desk/contract.py:136` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |

## [Liquid momentum trend cohorts](../../strategies/griffith/griffith-liquid-momentum-trend.md)

| Rule | Read from |
|---|---|
| Entry: Observation: each session, every name with close > SMA 200 and SMA 50 > SMA 200 on its last completed bar (253 bars needed), 12-1 momentum (the close 21 sessions back / the close 252 back - 1) > 0 and a 20-day average dollar volume ≥ $20M. | `sleeves/griffith/vendor/griffith/strategy_tournament.py:54-73`<br>`sleeves/griffith/griffith_factor.py:239-253`<br>`sleeves/griffith/griffith_factor.py:261-268` |
| Entry: Entry: at the session's first pass with a live quote, a fixed slot of $100,000 / 550 (about $182) as a marketable limit good for an hour; one cohort per name, none while it is held or working. | `sleeves/griffith/griffith_factor.py:55`<br>`sleeves/griffith/griffith_factor.py:261-281`<br>master-desk `desk/contract.py:62-68` |
| Exit: Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1). | `sleeves/griffith/griffith_factor.py:54`<br>`sleeves/griffith/griffith_factor.py:282-289` |
| Sizing: A fixed $182 slot per cohort. | `sleeves/griffith/griffith_factor.py:269`<br>master-desk `desk/contract.py:136` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |

## [Positive earnings surprise drift](../../strategies/griffith/griffith-pead-sue.md)

| Rule | Read from |
|---|---|
| Entry: Events: Nasdaq's earnings calendar for the SCOPE names outside the ETF basket (reported EPS, consensus, release time), refreshed at each session's open. | `sleeves/griffith/event_research.py:49-51`<br>`sleeves/griffith/event_research.py:84-95` |
| Entry: Trigger: the latest report's surprise (actual - consensus) / \|consensus\| > 0 (a zero consensus is skipped). | `sleeves/griffith/event_research.py:54-58`<br>`sleeves/griffith/event_research.py:111-116` |
| Entry: Entry: the open of the first session that can trade the report (a pre-market report that day, otherwise the next session); one event per name at a time. | `sleeves/griffith/event_research.py:76-81`<br>`sleeves/griffith/event_research.py:166-189` |
| Entry: Book: every active event at 1/N of the book, re-targeted at each session's first pass. | `sleeves/griffith/event_research.py:158-164`<br>`sleeves/griffith/event_research.py:190-202` |
| Exit: Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1). | `sleeves/griffith/event_research.py:34`<br>`sleeves/griffith/event_research.py:203-209` |
| Sizing: $100,000 book in equal calendar-time weights. | `sleeves/griffith/event_research.py:195-201`<br>master-desk `desk/contract.py:136` |
| Data: Nasdaq's archived earnings calendar pages and live quotes. | `sleeves/griffith/event_research.py:84-95`<br>`sleeves/griffith/event_research.py:134-139` |

## [Top-decile SUE drift](../../strategies/griffith/griffith-top-decile-sue.md)

| Rule | Read from |
|---|---|
| Entry: Events: Nasdaq's earnings calendar for the SCOPE names outside the ETF basket (reported EPS, consensus, release time), refreshed at each session's open. | `sleeves/griffith/event_research.py:49-51`<br>`sleeves/griffith/event_research.py:84-95` |
| Entry: Trigger: SUE = (actual - consensus) / the sample SD of the name's 8 prior surprises, at or above the 90th percentile of the universe's SUEs public within the trailing 91 days (at least 10). | `sleeves/griffith/event_research.py:35-37`<br>`sleeves/griffith/event_research.py:61-73`<br>`sleeves/griffith/event_research.py:103-110`<br>`sleeves/griffith/event_research.py:119-127` |
| Entry: Entry: the open of the first session that can trade the report (a pre-market report that day, otherwise the next session); one event per name at a time. | `sleeves/griffith/event_research.py:76-81`<br>`sleeves/griffith/event_research.py:166-189` |
| Entry: Book: every active event at 1/N of the book, re-targeted at each session's first pass. | `sleeves/griffith/event_research.py:158-164`<br>`sleeves/griffith/event_research.py:190-202` |
| Exit: Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1). | `sleeves/griffith/event_research.py:34`<br>`sleeves/griffith/event_research.py:203-209` |
| Sizing: $100,000 book in equal calendar-time weights. | `sleeves/griffith/event_research.py:195-201`<br>master-desk `desk/contract.py:136` |
| Data: Nasdaq's archived earnings calendar pages and live quotes. | `sleeves/griffith/event_research.py:84-95`<br>`sleeves/griffith/event_research.py:134-139` |

## [Momentum plus earnings drift](../../strategies/griffith/griffith-momentum-pead.md)

| Rule | Read from |
|---|---|
| Entry: Events: Nasdaq's earnings calendar for the SCOPE names outside the ETF basket (reported EPS, consensus, release time), refreshed at each session's open. | `sleeves/griffith/event_research.py:49-51`<br>`sleeves/griffith/event_research.py:84-95` |
| Entry: Trigger: a positive surprise (actual - consensus) / \|consensus\| on a name whose last completed daily bar passes the liquid momentum trend rule: close > SMA 200, SMA 50 > SMA 200, 12-1 momentum > 0 and a 20-day dollar volume ≥ $20M. | `sleeves/griffith/event_research.py:111-116`<br>`sleeves/griffith/event_research.py:172-180`<br>`sleeves/griffith/vendor/griffith/strategy_tournament.py:54-73` |
| Entry: Entry: the open of the first session that can trade the report (a pre-market report that day, otherwise the next session); one event per name at a time. | `sleeves/griffith/event_research.py:76-81`<br>`sleeves/griffith/event_research.py:166-189` |
| Entry: Book: every active event at 1/N of the book, re-targeted at each session's first pass. | `sleeves/griffith/event_research.py:158-164`<br>`sleeves/griffith/event_research.py:190-202` |
| Exit: Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1). | `sleeves/griffith/event_research.py:34`<br>`sleeves/griffith/event_research.py:203-209` |
| Sizing: $100,000 book in equal calendar-time weights. | `sleeves/griffith/event_research.py:195-201`<br>master-desk `desk/contract.py:136` |
| Data: Nasdaq's archived earnings calendar pages and live quotes. | `sleeves/griffith/event_research.py:84-95`<br>`sleeves/griffith/event_research.py:134-139` |
| Data: Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys. | `sleeves/griffith/feedlib/griffith.py:25-29`<br>`sleeves/griffith/feedlib/griffith.py:34-40`<br>`sleeves/griffith/feedlib/griffith.py:65-95`<br>`sleeves/griffith/feedlib/griffith.py:98-118` |

## [Auditable 20/50 trend (SPY)](../../strategies/griffith/griffith-auditable-20-50-trend.md)

| Rule | Read from |
|---|---|
| Entry: Every 15 minutes on SPY's last 50 completed 5-minute bars, only on a new newest bar and never while an order works: buy when flat and SMA 20 > SMA 50 × 1.001. | `sleeves/griffith/griffith_intraday.py:431-448`<br>`sleeves/griffith/griffith_intraday.py:455`<br>`sleeves/griffith/griffith_intraday.py:461-486`<br>master-desk `desk/vendor/griffith/config.json:11-18` |
| Entry: Order: round($100 / price, 6) shares as a DAY limit at the price × 1.001. | `sleeves/griffith/griffith_intraday.py:445`<br>`sleeves/griffith/griffith_intraday.py:489-496`<br>master-desk `desk/vendor/griffith/config.json:193` |
| Exit: Sold when SMA 20 < SMA 50 while long, a DAY limit at the price × 0.999. | `sleeves/griffith/griffith_intraday.py:446-447`<br>`sleeves/griffith/griffith_intraday.py:489-496` |
| Sizing: $100 a trade. | master-desk `desk/vendor/griffith/config.json:18`<br>`sleeves/griffith/griffith_intraday.py:445` |
| Data: SPY's IEX 5-minute bars, the last 51. | `sleeves/griffith/griffith_intraday.py:466-470`<br>master-desk `desk/vendor/griffith/config.json:14` |

## [Momentum breakout (legacy setup)](../../strategies/griffith/griffith-momentum-breakout.md)

| Rule | Read from |
|---|---|
| Entry: Scan, every 15 minutes: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names; price $5-1,000 and spread ≤ 0.6%; score = 0.8 × \|gap\| + \|intraday move\| + min(relative volume, 5) + log10(dollar volume) / 3. | `sleeves/griffith/griffith_intraday.py:46-47`<br>`sleeves/griffith/griffith_intraday.py:215-239`<br>`sleeves/griffith/griffith_intraday.py:254-285`<br>`sleeves/griffith/griffith_intraday.py:312-325`<br>master-desk `desk/vendor/griffith/config.json:26-28` |
| Entry: The 15 best get a headline score (positive less negative words, + 0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars. | `sleeves/griffith/griffith_intraday.py:130-149`<br>`sleeves/griffith/griffith_intraday.py:325-341`<br>master-desk `desk/vendor/griffith/config.json:24-25` |
| Entry: Setup: price ≥ 99.9% of the 20-bar high, relative volume ≥ 1.5 and RSI(14) < 78 (+3 points). | `sleeves/griffith/griffith_intraday.py:163-165` |
| Entry: BUY: scan + headline + setup points ≥ 5, price not over EMA 20 + 2.5 × max(ATR, 0.2% of price), and the SPY / QQQ / IWM average day not under -0.6%. | `sleeves/griffith/griffith_intraday.py:162`<br>`sleeves/griffith/griffith_intraday.py:175-184`<br>`sleeves/griffith/griffith_intraday.py:242-250` |
| Entry: Order: $100 (round(100 / price, 6) shares) as a DAY limit at the price × 1.001; at most 30 positions, never a held or working name. | `sleeves/griffith/griffith_intraday.py:396-420`<br>master-desk `desk/vendor/griffith/config.json:23`<br>master-desk `desk/vendor/griffith/config.json:29-30`<br>master-desk `desk/vendor/griffith/config.json:193` |
| Exit: Stop 1.5% under the entry, target 3% over it. | `sleeves/griffith/griffith_intraday.py:414-415`<br>master-desk `desk/vendor/griffith/config.json:31-32` |
| Sizing: $100 a trade. | master-desk `desk/vendor/griffith/config.json:30`<br>`sleeves/griffith/griffith_intraday.py:407-408` |
| Data: Alpaca IEX snapshots, news and 1-minute bars (on Yahoo quotes without keys the spread filter passes). | `sleeves/griffith/griffith_intraday.py:225-226`<br>`sleeves/griffith/griffith_intraday.py:312-342` |

## [VWAP pullback (legacy setup)](../../strategies/griffith/griffith-vwap-pullback.md)

| Rule | Read from |
|---|---|
| Entry: Scan, every 15 minutes: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names; price $5-1,000 and spread ≤ 0.6%; score = 0.8 × \|gap\| + \|intraday move\| + min(relative volume, 5) + log10(dollar volume) / 3. | `sleeves/griffith/griffith_intraday.py:46-47`<br>`sleeves/griffith/griffith_intraday.py:215-239`<br>`sleeves/griffith/griffith_intraday.py:254-285`<br>`sleeves/griffith/griffith_intraday.py:312-325`<br>master-desk `desk/vendor/griffith/config.json:26-28` |
| Entry: The 15 best get a headline score (positive less negative words, + 0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars. | `sleeves/griffith/griffith_intraday.py:130-149`<br>`sleeves/griffith/griffith_intraday.py:325-341`<br>master-desk `desk/vendor/griffith/config.json:24-25` |
| Entry: Setup, when not a breakout: EMA 9 > EMA 20 and price within 0.4% of VWAP with RSI(14) < 68 (+2 points). | `sleeves/griffith/griffith_intraday.py:163-169` |
| Entry: BUY: scan + headline + setup points ≥ 5, price not over EMA 20 + 2.5 × max(ATR, 0.2% of price), and the SPY / QQQ / IWM average day not under -0.6%. | `sleeves/griffith/griffith_intraday.py:162`<br>`sleeves/griffith/griffith_intraday.py:175-184`<br>`sleeves/griffith/griffith_intraday.py:242-250` |
| Entry: Order: $100 (round(100 / price, 6) shares) as a DAY limit at the price × 1.001; at most 30 positions, never a held or working name. | `sleeves/griffith/griffith_intraday.py:396-420`<br>master-desk `desk/vendor/griffith/config.json:23`<br>master-desk `desk/vendor/griffith/config.json:29-30`<br>master-desk `desk/vendor/griffith/config.json:193` |
| Exit: Stop 1.5% under the entry, target 3% over it. | `sleeves/griffith/griffith_intraday.py:414-415`<br>master-desk `desk/vendor/griffith/config.json:31-32` |
| Sizing: $100 a trade. | master-desk `desk/vendor/griffith/config.json:30`<br>`sleeves/griffith/griffith_intraday.py:407-408` |
| Data: Alpaca IEX snapshots, news and 1-minute bars (on Yahoo quotes without keys the spread filter passes). | `sleeves/griffith/griffith_intraday.py:225-226`<br>`sleeves/griffith/griffith_intraday.py:312-342` |

## [Gap continuation (legacy setup)](../../strategies/griffith/griffith-gap-continuation.md)

| Rule | Read from |
|---|---|
| Entry: Scan, every 15 minutes: SPY, QQQ, IWM, the SCOPE radar's top 100 (Parallax challenger, Leaders Rest and Location-First BUY / SETUP / WATCH decisions, by score) and held names; price $5-1,000 and spread ≤ 0.6%; score = 0.8 × \|gap\| + \|intraday move\| + min(relative volume, 5) + log10(dollar volume) / 3. | `sleeves/griffith/griffith_intraday.py:46-47`<br>`sleeves/griffith/griffith_intraday.py:215-239`<br>`sleeves/griffith/griffith_intraday.py:254-285`<br>`sleeves/griffith/griffith_intraday.py:312-325`<br>master-desk `desk/vendor/griffith/config.json:26-28` |
| Entry: The 15 best get a headline score (positive less negative words, + 0.5 for a catalyst word); the 8 best are judged on their last 200 completed 1-minute bars. | `sleeves/griffith/griffith_intraday.py:130-149`<br>`sleeves/griffith/griffith_intraday.py:325-341`<br>master-desk `desk/vendor/griffith/config.json:24-25` |
| Entry: Setup, when neither a breakout nor a VWAP pullback: a gap ≥ 2%, price above VWAP and EMA 9 > EMA 20 (+2 points). | `sleeves/griffith/griffith_intraday.py:163-172` |
| Entry: BUY: scan + headline + setup points ≥ 5, price not over EMA 20 + 2.5 × max(ATR, 0.2% of price), and the SPY / QQQ / IWM average day not under -0.6%. | `sleeves/griffith/griffith_intraday.py:162`<br>`sleeves/griffith/griffith_intraday.py:175-184`<br>`sleeves/griffith/griffith_intraday.py:242-250` |
| Entry: Order: $100 (round(100 / price, 6) shares) as a DAY limit at the price × 1.001; at most 30 positions, never a held or working name. | `sleeves/griffith/griffith_intraday.py:396-420`<br>master-desk `desk/vendor/griffith/config.json:23`<br>master-desk `desk/vendor/griffith/config.json:29-30`<br>master-desk `desk/vendor/griffith/config.json:193` |
| Exit: Stop 1.5% under the entry, target 3% over it. | `sleeves/griffith/griffith_intraday.py:414-415`<br>master-desk `desk/vendor/griffith/config.json:31-32` |
| Sizing: $100 a trade. | master-desk `desk/vendor/griffith/config.json:30`<br>`sleeves/griffith/griffith_intraday.py:407-408` |
| Data: Alpaca IEX snapshots, news and 1-minute bars (on Yahoo quotes without keys the spread filter passes). | `sleeves/griffith/griffith_intraday.py:225-226`<br>`sleeves/griffith/griffith_intraday.py:312-342` |

## [20-minute opening range breakout](../../strategies/griffith/griffith-orb20.md)

| Rule | Read from |
|---|---|
| Entry: Qualify, after 09:51 ET: the four completed 5-minute bars of 09:30-09:50, with that window's volume ≥ 2 × the median of the same window over the prior 20 complete sessions. | `sleeves/griffith/griffith_intraday.py:508`<br>`sleeves/griffith/griffith_intraday.py:512-537`<br>`sleeves/griffith/griffith_intraday.py:595-605` |
| Entry: Entry: the first completed 5-minute bar after the range closing above its high, while the ask is above the range low; a marketable limit good for 10 minutes, once per name a day. | `sleeves/griffith/griffith_intraday.py:540-546`<br>`sleeves/griffith/griffith_intraday.py:606-625`<br>master-desk `desk/contract.py:62-68` |
| Exit: Stop at the range low; flat from 15:55 ET. | `sleeves/griffith/griffith_intraday.py:589-594`<br>`sleeves/griffith/griffith_intraday.py:619-620` |
| Sizing: A fixed slot of $100,000 / 550 (about $182) per name. | `sleeves/griffith/griffith_intraday.py:611`<br>master-desk `desk/contract.py:136` |
| Data: 5-minute bars of the universe (Alpaca; Yahoo without keys), about 22 sessions. | `sleeves/griffith/griffith_intraday.py:572-578`<br>`sleeves/griffith/griffith_intraday.py:599`<br>master-desk `desk/data/hub.py:170-171` |

## [Tensor HTF conditional holdout (H1-H8)](../../strategies/griffith/griffith-htf-conditional-h1-h8.md)

| Rule | Read from |
|---|---|
| Entry: Universe: the roster's operating companies (current metadata). | `sleeves/tensor_research/tensor_research.py:357-359` |
| Entry: Labels: H1 a weekly buy-cyan with an annualized 20-bar volatility ≥ 60% and a 20-bar median dollar volume of $20-100M; H2 a weekly buy-cyan above a rising EMA 200; H3 a weekly buy-cyan with the fast and slow states bullish; H4 a daily buy-green above a rising EMA 200 with a 20/60-bar range ratio ≤ 0.75 and a 20-bar breakout; H5 a daily bounce buy above a rising EMA 200; H6 a daily buy-green with a participation footprint active; H7 a fresh daily participation footprint; H8 a weekly bounce buy while consensus-sell is active. | `sleeves/griffith/vendor/griffith/tensor_htf_holdout_spec.json:8-17`<br>`sleeves/tensor_research/feedlib/tensor_features.py:82-129`<br>`sleeves/tensor_research/feedlib/tensor_features.py:242-278`<br>`sleeves/tensor_research/tensor_research.py:362-375` |
| Entry: Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. | `sleeves/tensor_research/tensor_research.py:183-186`<br>`sleeves/tensor_research/tensor_research.py:590-595`<br>`sleeves/tensor_research/tensor_research.py:626-635`<br>`sleeves/tensor_research/feedlib/tensor_research.py:491-493`<br>`sleeves/tensor_research/feedlib/tensor_research.py:564-565` |
| Entry: Entry: the next session's open, a market order within that session; skipped once it has passed. | `sleeves/tensor_research/tensor_research.py:722-746`<br>`sleeves/tensor_research/tensor_research.py:840-868`<br>`sleeves/tensor_research/feedlib/tensor_research.py:307-317` |
| Exit: Close of bar 20 (daily) or week 12 (weekly), market-on-close. | `sleeves/griffith/vendor/griffith/tensor_htf_holdout_spec.json:18`<br>`sleeves/tensor_research/tensor_research.py:374-375`<br>`sleeves/tensor_research/tensor_research.py:870-879`<br>`sleeves/tensor_research/feedlib/tensor_research.py:320-330` |
| Sizing: One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side. | `sleeves/tensor_research/tensor_research.py:671-676`<br>`sleeves/tensor_research/tensor_research.py:722-738`<br>`sleeves/tensor_research/tensor_research.py:845-862`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Weekly annualizer | `sleeves/tensor_research/feedlib/tensor_features.py:89`<br>`sleeves/tensor_research/feedlib/tensor_features.py:118`<br>`sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/tensor_research.py:198-205` |
| Book | `sleeves/tensor_research/tensor_research.py:1047-1048` |

## [Tensor weekly cyan confirmation (CY01-CY18)](../../strategies/griffith/griffith-weekly-cyan-confirmation.md)

| Rule | Read from |
|---|---|
| Entry: Universe: the roster's operating companies (current metadata). | `sleeves/tensor_research/tensor_research.py:357-359` |
| Entry: Hypotheses: CY01-CY18 on the fresh weekly buy-cyan (listed below); each match is a sub-lot. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json:13-32`<br>`sleeves/tensor_research/feedlib/tensor_features.py:376-435`<br>`sleeves/tensor_research/tensor_research.py:378-391` |
| Entry: Purge: a hypothesis takes a name again only 84 days after its last event there. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json:9`<br>`sleeves/tensor_research/feedlib/tensor_features.py:438-442`<br>`sleeves/tensor_research/tensor_research.py:917-933` |
| Entry: Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. | `sleeves/tensor_research/tensor_research.py:183-186`<br>`sleeves/tensor_research/tensor_research.py:590-595`<br>`sleeves/tensor_research/tensor_research.py:626-635`<br>`sleeves/tensor_research/feedlib/tensor_research.py:491-493`<br>`sleeves/tensor_research/feedlib/tensor_research.py:564-565` |
| Entry: Entry: the next session's open, a market order within that session; skipped once it has passed. | `sleeves/tensor_research/tensor_research.py:722-746`<br>`sleeves/tensor_research/tensor_research.py:840-868`<br>`sleeves/tensor_research/feedlib/tensor_research.py:307-317` |
| Exit: Close of week 12, market-on-close. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json:8`<br>`sleeves/tensor_research/tensor_research.py:390-391`<br>`sleeves/tensor_research/tensor_research.py:870-879`<br>`sleeves/tensor_research/feedlib/tensor_research.py:320-330` |
| Sizing: One slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side. | `sleeves/tensor_research/tensor_research.py:671-676`<br>`sleeves/tensor_research/tensor_research.py:722-738`<br>`sleeves/tensor_research/tensor_research.py:845-862`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Negative controls traded | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json:30-31`<br>`sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json:43-46`<br>`sleeves/tensor_research/tensor_research.py:387` |
| Book | `sleeves/tensor_research/tensor_research.py:1049-1050` |

## [Tensor weekly green / cyan deep confirmation (WG / WC)](../../strategies/griffith/griffith-weekly-green-cyan-deep-confirmation.md)

| Rule | Read from |
|---|---|
| Entry: Universe: the roster's operating companies (current metadata). | `sleeves/tensor_research/tensor_research.py:357-359` |
| Entry: Candidates: WG01-WG10 on a fresh weekly buy-green and WC01-WC14 on a fresh weekly buy-cyan, each passing all its conditions (listed below); each match is a sub-lot. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json:12-36`<br>`sleeves/tensor_research/feedlib/tensor_features.py:151-234`<br>`sleeves/tensor_research/feedlib/tensor_features.py:286-359`<br>`sleeves/tensor_research/tensor_research.py:394-417`<br>`sleeves/tensor_research/tensor_research.py:217-229` |
| Entry: Purge: a candidate takes a name again only 84 days after its last event there. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json:7`<br>`sleeves/tensor_research/feedlib/tensor_features.py:438-442`<br>`sleeves/tensor_research/tensor_research.py:917-933` |
| Entry: Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. | `sleeves/tensor_research/tensor_research.py:183-186`<br>`sleeves/tensor_research/tensor_research.py:590-595`<br>`sleeves/tensor_research/tensor_research.py:626-635`<br>`sleeves/tensor_research/feedlib/tensor_research.py:491-493`<br>`sleeves/tensor_research/feedlib/tensor_research.py:564-565` |
| Entry: Entry: the next session's open, a market order within that session; skipped once it has passed. | `sleeves/tensor_research/tensor_research.py:722-746`<br>`sleeves/tensor_research/tensor_research.py:840-868`<br>`sleeves/tensor_research/feedlib/tensor_research.py:307-317` |
| Exit: Close of week 12, market-on-close. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json:6`<br>`sleeves/tensor_research/tensor_research.py:414-416`<br>`sleeves/tensor_research/tensor_research.py:870-879`<br>`sleeves/tensor_research/feedlib/tensor_research.py:320-330` |
| Sizing: One slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side. | `sleeves/tensor_research/tensor_research.py:671-676`<br>`sleeves/tensor_research/tensor_research.py:722-738`<br>`sleeves/tensor_research/tensor_research.py:845-862`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Book | `sleeves/tensor_research/tensor_research.py:1051-1053` |

## [Tensor weekly color forward shadow (FG / FC)](../../strategies/griffith/griffith-weekly-color-forward-shadow.md)

| Rule | Read from |
|---|---|
| Entry: Universe: the roster's operating companies (current metadata). | `sleeves/tensor_research/tensor_research.py:357-359` |
| Entry: Candidates: FG01-FG03 on a fresh weekly buy-green and FC01-FC06 on a fresh weekly buy-cyan, each passing both its conditions (listed below); each match is a sub-lot; no purge. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_forward_spec.json:11-20`<br>`sleeves/tensor_research/feedlib/tensor_features.py:151-234`<br>`sleeves/tensor_research/feedlib/tensor_features.py:286-359`<br>`sleeves/tensor_research/tensor_research.py:401-417`<br>`sleeves/tensor_research/tensor_research.py:554-555` |
| Entry: Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. | `sleeves/tensor_research/tensor_research.py:183-186`<br>`sleeves/tensor_research/tensor_research.py:590-595`<br>`sleeves/tensor_research/tensor_research.py:626-635`<br>`sleeves/tensor_research/feedlib/tensor_research.py:491-493`<br>`sleeves/tensor_research/feedlib/tensor_research.py:564-565` |
| Entry: Entry: the next session's open, a market order within that session; skipped once it has passed. | `sleeves/tensor_research/tensor_research.py:722-746`<br>`sleeves/tensor_research/tensor_research.py:840-868`<br>`sleeves/tensor_research/feedlib/tensor_research.py:307-317` |
| Exit: Close of week 12, market-on-close. | `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json:6`<br>`sleeves/tensor_research/tensor_research.py:414`<br>`sleeves/tensor_research/tensor_research.py:870-879`<br>`sleeves/tensor_research/feedlib/tensor_research.py:320-330` |
| Sizing: One slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side. | `sleeves/tensor_research/tensor_research.py:671-676`<br>`sleeves/tensor_research/tensor_research.py:722-738`<br>`sleeves/tensor_research/tensor_research.py:845-862`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Book | `sleeves/tensor_research/tensor_research.py:1054-1055` |

## [Tensor HTF relay (T1-T7)](../../strategies/griffith/griffith-htf-relay.md)

| Rule | Read from |
|---|---|
| Entry: Arms: T1 a daily buy-green; T4 one inside an active weekly bull episode (the latest fresh weekly green or cyan with no weekly sell since); T5 a T4 with consensus-buy or lifecycle P active; T6 a daily bounce buy inside a weekly bull episode; T7 the first daily green of each weekly episode; T2 a weekly buy-green; T3 a weekly buy-cyan; each arm is a sub-lot. | `sleeves/tensor_research/tensor_research.py:420-459`<br>`sleeves/tensor_research/tensor_research.py:940-948` |
| Entry: Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. | `sleeves/tensor_research/tensor_research.py:183-186`<br>`sleeves/tensor_research/tensor_research.py:590-595`<br>`sleeves/tensor_research/tensor_research.py:626-635`<br>`sleeves/tensor_research/feedlib/tensor_research.py:491-493`<br>`sleeves/tensor_research/feedlib/tensor_research.py:564-565` |
| Entry: Entry: the next session's open, a market order within that session; skipped once it has passed. | `sleeves/tensor_research/tensor_research.py:722-746`<br>`sleeves/tensor_research/tensor_research.py:840-868`<br>`sleeves/tensor_research/feedlib/tensor_research.py:307-317` |
| Exit: The next session's open after the first completed daily or weekly sell-red / sell-magenta after the entry bar, at the market. | `sleeves/tensor_research/tensor_research.py:950-963`<br>`sleeves/tensor_research/tensor_research.py:886-887` |
| Sizing: One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; the desk's own fees. | `sleeves/tensor_research/tensor_research.py:671-676`<br>`sleeves/tensor_research/tensor_research.py:722-738`<br>`sleeves/tensor_research/tensor_research.py:845-862`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Book | `sleeves/tensor_research/tensor_research.py:1056-1057` |

## [Tensor edge v0.1 (G1 / G2 / C1)](../../strategies/griffith/griffith-tensor-edge-v01.md)

| Rule | Read from |
|---|---|
| Entry: G1, a daily buy-green: above a rising EMA 200, a 20/60-bar range ratio ≤ 0.75, a 20-bar breakout, under 15% over EMA 21, and an up-volume share ≥ 50% or a rising OBV or A/D line. | `sleeves/tensor_research/tensor_research.py:470-481` |
| Entry: G2, a weekly buy-green: a long base (range ratio ≤ 0.75 or ≥ 30% under the 52-week high), the 13-week return above SPY's (or the 13-week relative strength above the 26-week), 4-week volume ≥ the 20-week, under 15% over EMA 21. | `sleeves/tensor_research/tensor_research.py:482-487` |
| Entry: C1, a weekly buy-cyan: 13- and 26-week returns above SPY's, a 13-week return of 25-60%, RSI 55-72, an up-volume share ≥ 55%, the 4-week range ≤ 75% of the 13-week; none when exhausted (RSI ≥ 75, a 13-week return ≥ 100%, or an extension warning). | `sleeves/tensor_research/tensor_research.py:488-499`<br>`sleeves/tensor_research/tensor_research.py:971-973` |
| Entry: Entry: a buy-stop at the signal bar's high, resting through the next bar (session or week). | `sleeves/tensor_research/tensor_research.py:500-502`<br>`sleeves/tensor_research/tensor_research.py:975-1011` |
| Entry: Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. | `sleeves/tensor_research/tensor_research.py:183-186`<br>`sleeves/tensor_research/tensor_research.py:590-595`<br>`sleeves/tensor_research/tensor_research.py:626-635`<br>`sleeves/tensor_research/feedlib/tensor_research.py:491-493`<br>`sleeves/tensor_research/feedlib/tensor_research.py:564-565` |
| Exit: Stop: the bid at or under the signal bar's low, at the market. | `sleeves/tensor_research/tensor_research.py:502`<br>`sleeves/tensor_research/tensor_research.py:880-883` |
| Exit: The next session's open after the frame's completed sell-red / sell-magenta. | `sleeves/tensor_research/tensor_research.py:1013-1016` |
| Sizing: One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; the desk's own fees. | `sleeves/tensor_research/tensor_research.py:671-676`<br>`sleeves/tensor_research/tensor_research.py:722-738`<br>`sleeves/tensor_research/tensor_research.py:845-862`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Book | `sleeves/tensor_research/tensor_research.py:1058-1059` |

## [Tensor frozen phenotypes v4](../../strategies/griffith/griffith-frozen-phenotypes-v4.md)

| Rule | Read from |
|---|---|
| Entry: Phenotypes, on the market-scan context (the last 420 daily or 260 weekly bars), only on bars after the registry's late-August 2026 freeze: a daily buy-green passing the base-expansion test (above a rising EMA 200, a range ratio ≤ 0.75, a 20-bar breakout, under 15% over EMA 21, constructive participation); a weekly buy-green early markup out of a recovery; a weekly buy-cyan accumulation out of a recovery; a weekly buy-cyan early markup; the weekly three each READY with bullish-aligned energy, deep normal participation and a consensus-buy enrichment. | `sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json:27-70`<br>`sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json:72-135`<br>`sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json:137-200`<br>`sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json:202-265`<br>`sleeves/tensor_research/feedlib/tensor_features.py:543-555`<br>`sleeves/tensor_research/feedlib/tensor_features.py:630-646`<br>`sleeves/tensor_research/tensor_research.py:505-532`<br>`sleeves/tensor_research/feedlib/tensor_research.py:47` |
| Entry: Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. | `sleeves/tensor_research/tensor_research.py:183-186`<br>`sleeves/tensor_research/tensor_research.py:590-595`<br>`sleeves/tensor_research/tensor_research.py:626-635`<br>`sleeves/tensor_research/feedlib/tensor_research.py:491-493`<br>`sleeves/tensor_research/feedlib/tensor_research.py:564-565` |
| Entry: Entry: the next session's open, a market order within that session; skipped once it has passed. | `sleeves/tensor_research/tensor_research.py:722-746`<br>`sleeves/tensor_research/tensor_research.py:840-868`<br>`sleeves/tensor_research/feedlib/tensor_research.py:307-317` |
| Exit: Three equal sub-lots at the close of bars 4, 13 and 26, market-on-close. | `sleeves/tensor_research/tensor_research.py:525`<br>`sleeves/tensor_research/tensor_research.py:870-879`<br>`sleeves/tensor_research/feedlib/tensor_research.py:320-330` |
| Sizing: One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 15 bp a side. | `sleeves/tensor_research/tensor_research.py:671-676`<br>`sleeves/tensor_research/tensor_research.py:722-738`<br>`sleeves/tensor_research/tensor_research.py:845-862`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Book | `sleeves/tensor_research/tensor_research.py:1060-1061` |

## [Tensor phenotype experiment (HIGH_BREAK_4)](../../strategies/griffith/griffith-tensor-phenotype-experiment.md)

| Rule | Read from |
|---|---|
| Entry: Predictions: the frozen v4 phenotype events, at most 25 a cycle, oldest first, each once. | `sleeves/tensor_research/tensor_research.py:1069`<br>`sleeves/tensor_research/tensor_research.py:1143-1153` |
| Entry: Plan: trigger = the event bar's high, ceiling = trigger + 0.10 ATR(14), stop = its close - 2 ATR(14), target = the ceiling × 1.10 (daily) or × 1.25 (weekly). | `sleeves/tensor_research/feedlib/tensor_features.py:711-737` |
| Entry: Order: the planner hands the ceiling (rounded to 8 places) to the overlay as the ask, so the trigger always reads as crossed: when that rounding went up the prediction gets no plan; otherwise a GTC buy limit at the ceiling, armed 7 days (daily) or 28 (weekly), which fills at once while the market is under it. | `sleeves/griffith/griffith.py:239-243`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:166-187`<br>`sleeves/tensor_research/feedlib/tensor_features.py:738`<br>`sleeves/tensor_research/feedlib/tensor_features.py:747-749` |
| Entry: Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit. | `sleeves/griffith/griffith.py:259-275`<br>`sleeves/griffith/griffith.py:292-326`<br>`sleeves/griffith/griffith.py:348`<br>master-desk `desk/vendor/griffith/config.json:21` |
| Exit: Bracket: the plan's stop and target. | `sleeves/griffith/griffith.py:264-266` |
| Sizing: Risk 1% of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power; a held name is not added to; $100,000 book. | `sleeves/griffith/vendor/griffith/strategy_execution.py:186`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:203-241`<br>master-desk `desk/vendor/griffith/config.json:179-190`<br>`sleeves/griffith/griffith.py:135-138`<br>`sleeves/griffith/griffith.py:189-212`<br>`sleeves/griffith/griffith.py:249-252`<br>master-desk `desk/contract.py:136` |
| Data: Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698. | `sleeves/tensor_research/feedlib/tensor_research.py:46`<br>`sleeves/tensor_research/feedlib/tensor_research.py:171-172`<br>`sleeves/tensor_research/feedlib/tensor_research.py:444-499`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:20-25`<br>`sleeves/tensor_research/feedlib/tensor_research.mjs:133-203` |
| Ceiling as the ask | `sleeves/griffith/griffith.py:239-243`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:170`<br>`sleeves/griffith/vendor/griffith/strategy_execution.py:177-181`<br>`sleeves/tensor_research/feedlib/tensor_features.py:738` |
| Bracket only | `sleeves/griffith/griffith.py:264-266` |
| Book | `sleeves/tensor_research/tensor_research.py:1131-1166` |
