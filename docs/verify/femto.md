# Verification: Femto-lean

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk); every other path is in this repository.

## [R4 blowoff (daily / hourly)](../../strategies/femto/femto-blowoff.md)

| Rule | Read from |
|---|---|
| Entry: Signal: Wilder RSI(14) and OBV both ≥ their trailing 144-bar min + 90% of the range; the first bar of each run. | `sleeves/femto/vendor/old_desk_research/rsiobv.py:368-420`<br>`sleeves/femto/vendor/old_desk_research/run_r4_blowoff_standalone.py:38-77` |
| Entry: Daily: the edge on the latest closed bar, ≥ 252 bars, ≥ 20 sessions after the name's last signal, only while SPY's 60-session return is ≤ 0; ranked from 16:30 ET, bought from 10:30 ET the next session. | `sleeves/femto/blowoff_d.py:20-25`<br>`sleeves/femto/blowoff_d.py:34-52`<br>`sleeves/femto/blowoff_d.py:55-103`<br>`sleeves/femto/feedlib/blowoff.py:40-55` |
| Entry: Hourly: an edge in the last 5 closed regular-hours bars, ≥ 160 bars, ≥ 20 bars after the last signal; scans at :10, buys at :40, 10:00-15:59 ET. | `sleeves/femto/blowoff_1h.py:20-58`<br>`sleeves/femto/blowoff_1h.py:29-33`<br>`sleeves/femto/blowoff_1h.py:61-112` |
| Exit: Daily: sold once 19 bars have closed after entry (the 20th session); backstop 28 days. No stop. | `sleeves/femto/blowoff_d.py:83-99`<br>`sleeves/femto/sleeve_core.py:117-145` |
| Exit: Hourly: sold 20 hourly bars after the bar that follows the signal; backstop 4 days. No stop. | `sleeves/femto/blowoff_1h.py:84-105`<br>`sleeves/femto/blowoff_1h.py:115-123` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 10 bps a side. | `sleeves/femto/blowoff_d.py:23`<br>`sleeves/femto/blowoff_1h.py:23` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Daily split-adjusted bars (600, cached) with the genome job's last-close blowoff rows; regular-hours hourly bars (400); desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:293-319` |
| Provenance: killed on the old desk, forward test here | `sleeves/femto/blowoff_d.py:1-9`<br>`sleeves/femto/blowoff_1h.py:1-9` |
| Detector credit | `sleeves/femto/vendor/old_desk_research/rsiobv.py:1-6` |

## [Six-month momentum leaders](../../strategies/femto/femto-momentum.md)

| Rule | Read from |
|---|---|
| Entry: Liquid: last completed close ≥ $5 and 20-session mean dollar volume ≥ $1M; SOXL excluded; ranked by 126-session return; the top tenth (at least 1, at most 10) when 10+ names qualify. | `sleeves/femto/momentum.py:34-41`<br>`sleeves/femto/momentum.py:73-104`<br>`sleeves/midna/context.py:116-122`<br>`sleeves/midna/context.py:139-178` |
| Entry: A review every 63 sessions sets the target to the new top tenth; between reviews the book holds. | `sleeves/femto/momentum.py:194-219`<br>`sleeves/midna/context.py:44`<br>`sleeves/midna/context.py:198-206` |
| Entry: Femto: buys wait on a Friday after 14:00 ET, the last 5 sessions of the year, FOMC days and the session before, and when VIX is unknown, stale (> 4 days), above 32 or up 25% on the day, or SPY is down 8% over 20 sessions with VIX rising. | `sleeves/femto/momentum.py:42-54`<br>`sleeves/femto/momentum.py:125-182` |
| Entry: Trades from 10:00 ET on fresh quotes. | `sleeves/femto/momentum.py:273-274`<br>`sleeves/femto/momentum.py:318-320` |
| Exit: A name leaves at the next review it is not in. | `sleeves/femto/momentum.py:215-216`<br>`sleeves/femto/momentum.py:279-287`<br>`sleeves/midna/context.py:207-235` |
| Exit: Femto: a 40% breaker sells a name whose fresh mid is ≤ 60% of its entry. | `sleeves/femto/momentum.py:42`<br>`sleeves/femto/momentum.py:288-299` |
| Sizing: Femto: budget = 30% of the book less held and pending notional, split over the review target; whole shares at mid × (1 + 10, 25 or 50 bps by price), at least 1; at most 10 names. | `sleeves/femto/momentum.py:37-38`<br>`sleeves/femto/momentum.py:185-191`<br>`sleeves/femto/momentum.py:305-329` |
| Sizing: Midna: equal dollars = equity / names; floor(dollars / (price × (1 + cost))), cost 5-50 bps by price; sells first. | `sleeves/midna/context.py:190-197`<br>`sleeves/midna/context.py:207-235` |
| Sizing: Both books start at $100,000. | master-desk `desk/sleeves/families/femto.py:95`<br>`sleeves/midna/context.py:42` |
| Data: Daily bars (~290 sessions), VIX, desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:134-144` |
| Data: Midna: her daily panel (Yahoo adjusted closes). | `sleeves/midna/context.py:139-150` |
| Midna's book: lab cell and the gates the master desk removed | `sleeves/midna/context.py:1-29` |
| Midna v3 wrapper | `sleeves/momentum.py:1-13` |

## [QQQ weekly put ladder](../../strategies/femto/femto-qqq-put-ladder.md)

| Rule | Read from |
|---|---|
| Entry: A new layer at most once per ISO week: the 38-52 DTE put with delta 0.05-0.08, nearest 45 DTE, then delta 0.05, then the tightest spread; bid ≥ $0.05, spread ≤ max($0.10, 25% of mid), strike below spot, not in an expiration already held. | `sleeves/femto/vendor/aurelia/put_ladder.py:26-41`<br>`sleeves/femto/vendor/aurelia/put_ladder.py:87-136` |
| Entry: Blocked when the posture is not normal (VIX ≥ 25 or a Nasdaq day ≤ -5% is cautious; VIX ≥ 40 or ≤ -8% stands down), QQQ is down over 5 sessions, a put is challenged, 12 contracts are open, a layer was sold this week, or the cash does not secure it. | `sleeves/femto/vendor/aurelia/put_ladder.py:147-175`<br>`sleeves/femto/vendor/aurelia/judgment.py:10-38`<br>`sleeves/femto/qqq_put_ladder.py:177-181` |
| Entry: Midna's variant: a new layer once per ISO week when QQQ is not down and VIX not up on the day, nothing is challenged and the chain is fresh; nearest 45 days (38-52); delta 0.05-0.08, nearest 0.065. | `sleeves/midna/ladder.py:47-63`<br>`sleeves/midna/ladder.py:384-423` |
| Exit: ≤ 5 DTE: bought back. | `sleeves/femto/vendor/aurelia/put_ladder.py:35`<br>`sleeves/femto/vendor/aurelia/put_ladder.py:205-207` |
| Exit: ≤ 21 DTE: rolled up in the same expiration when the posture is normal, the put is not challenged, QQQ is above the entry spot and the ask ≤ half the credit; a challenged put (\|delta\| ≥ 0.20 or spot ≤ strike × 1.03) rolls out and down to the band put at or below its strike unless standing down, else is bought back. | `sleeves/femto/vendor/aurelia/put_ladder.py:34-39`<br>`sleeves/femto/vendor/aurelia/put_ladder.py:81-84`<br>`sleeves/femto/vendor/aurelia/put_ladder.py:208-245` |
| Exit: Midna's variant: bought back when severe (QQQ ≤ strike, ask ≥ 3× credit or delta ≥ 0.35) or at ≤ 7 DTE; 8-21 DTE rolls up (ask ≤ half the credit) or down and out when challenged (ask ≥ 2× credit, delta ≥ 0.20 or QQQ ≤ strike). | `sleeves/midna/ladder.py:226-249`<br>`sleeves/midna/ladder.py:299-379` |
| Sizing: 3 contracts a layer, at most 12 open; each secured by (strike - bid) × 100 × 3 of the book's cash; sales at the bid, buy-backs at the ask, day limits; a $1,000,000 book. | `sleeves/femto/vendor/aurelia/put_ladder.py:27`<br>`sleeves/femto/vendor/aurelia/put_ladder.py:36`<br>`sleeves/femto/vendor/aurelia/put_ladder.py:60-62`<br>`sleeves/femto/vendor/aurelia/put_ladder.py:185-187`<br>`sleeves/femto/qqq_put_ladder.py:160-174`<br>master-desk `desk/sleeves/families/femto_specs.py:653` |
| Sizing: Midna's variant: 3 contracts a layer on a $1,000,000 book; each sale cash-secured. | `sleeves/midna/ladder.py:47-48`<br>`sleeves/midna/ladder.py:257-268` |
| Data: The desk's QQQ put chain with deltas (0-52 DTE), the live QQQ quote, QQQ daily closes, and the Aurelia tape (VIX, Nasdaq day) for the posture. | master-desk `desk/sleeves/families/femto_specs.py:647-665`<br>`sleeves/femto/qqq_put_ladder.py:117-137` |
| Data: Midna's variant: Cboe delayed QQQ option quotes (the option-marks producer). | `sleeves/midna/ladder.py:195-203` |
| Midna v3 wrapper | `sleeves/qqq_put_ladder.py:1-12` |

## [60-day momentum rotation](../../strategies/femto/femto-momentum-rotation.md)

| Rule | Read from |
|---|---|
| Entry: Ranks names with ≥ 66 bars by 60-day return; buys the top 5 not held while fewer than 5 are held or working. | `sleeves/femto/momentum_rotation.py:22-28`<br>`sleeves/femto/momentum_rotation.py:42-65`<br>`sleeves/femto/momentum_rotation.py:95-127` |
| Entry: Rebalances when 7+ days have passed since the last one; the pass runs Monday 09:35 ET. | `sleeves/femto/momentum_rotation.py:68-79`<br>`sleeves/femto/momentum_rotation.py:92-93`<br>master-desk `desk/sleeves/families/femto_specs.py:127` |
| Exit: Sells a held name ranked worse than 10th. | `sleeves/femto/momentum_rotation.py:24`<br>`sleeves/femto/momentum_rotation.py:102-114` |
| Exit: A 25% disaster stop below the fill. The engine holds the disaster stop, measured from the actual fill. | `sleeves/femto/momentum_rotation.py:27`<br>`sleeves/femto/momentum_rotation.py:135-138`<br>master-desk `desk/sleeves/families/femto_specs.py:130-131` |
| Sizing: 20% of the book a name at the last close, whole shares. | `sleeves/femto/momentum_rotation.py:26`<br>`sleeves/femto/momentum_rotation.py:128-133` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (100). | master-desk `desk/sleeves/families/femto_specs.py:123-133` |
| Midna v3 wrapper | `sleeves/momentum_rotation.py:1-13` |

## [Morning dip limit](../../strategies/femto/femto-morning-dip.md)

| Rule | Read from |
|---|---|
| Entry: A calm 3-minute candle (from 1-minute bars): efficiency ratio over 15 candles ≤ 0.35, in the 10:00-12:00 ET window (Femto-lean: starting in it, the last 16 candles healthy; the Milkman study: ending in it). | `sleeves/femto/morning_dip.py:39-45`<br>`sleeves/femto/morning_dip.py:64-78`<br>`sleeves/femto/morning_dip.py:117-135`<br>`sleeves/femto/morning_dip.py:164-176`<br>`sleeves/milkman/intraday.py:702-725`<br>`sleeves/milkman/intraday.py:84` |
| Entry: Femto-lean: a DAY limit buy one tick under level = floor(close - ATR(14)), cancelled after 9 minutes; one order or position at a time. | `sleeves/femto/morning_dip.py:41`<br>`sleeves/femto/morning_dip.py:81-95`<br>`sleeves/femto/morning_dip.py:162-163`<br>`sleeves/femto/morning_dip.py:183-186` |
| Entry: Milkman study: a limit 1 × ATR(14) beyond the close for 9 minutes, filled when a bar trades a cent through it; the long lane buys below the close, the short lane sells above; one order or position at a time. | `sleeves/milkman/intraday.py:739-771`<br>`sleeves/milkman/intraday.py:772-801` |
| Exit: Target = the signal candle's midpoint; stop = 1.5 ATR beyond the limit (at least 4 ticks); a 15-minute time stop; flat at 12:00 ET. | `sleeves/femto/morning_dip.py:42`<br>`sleeves/femto/morning_dip.py:90-97`<br>`sleeves/femto/morning_dip.py:155-161`<br>`sleeves/femto/morning_dip.py:183-186`<br>master-desk `desk/sleeves/families/femto_specs.py:228`<br>`sleeves/milkman/intraday.py:759-796` |
| Exit: The Milkman study also needs the target ≥ 2 cents past the limit, and counts only the stop in the fill bar. | `sleeves/milkman/intraday.py:759-796` |
| Sizing: Femto-lean: shares = 0.25% of the book / the stop distance. | `sleeves/femto/morning_dip.py:37`<br>`sleeves/femto/morning_dip.py:84`<br>`sleeves/femto/morning_dip.py:96-98` |
| Sizing: Femto-lean: each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Sizing: Milkman study: $10,000 a trade on a $1,000,000 book, every trade taken. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo 1-minute bars with the extended session (420). | master-desk `desk/sleeves/families/femto_specs.py:219-229` |
| Data: Milkman study: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Midna v3 wrapper | `sleeves/morning_dip.py:1-13` |
| Milkman's rule, named in the port | `sleeves/femto/morning_dip.py:3-4`<br>master-desk `docs/research/2026-10-19-milkman/REVIEW.md:36` |

## [Phase compression breakout (daily)](../../strategies/femto/femto-phase-daily.md)

| Rule | Read from |
|---|---|
| Entry: Squeeze (grey): the 21-period, 2-sd Bollinger band inside the 2 × ATR(14) Keltner band around EMA(21), unless the gap is widening inside the 1.854 × ATR zone. | `sleeves/femto/phase_daily.py:102-130` |
| Entry: K5: once 5 grey days lock a box, a DAY buy-stop rests at the box high before each open while the prior close is above EMA(21), for 20 bars, until the box low or high is touched. | `sleeves/femto/phase_daily.py:39-40`<br>`sleeves/femto/phase_daily.py:133-168`<br>`sleeves/femto/phase_daily.py:210-231`<br>`sleeves/femto/phase_daily.py:451-466` |
| Entry: NC: on episodes K5 cannot trade, buys when yesterday was grey, today's forming bar nowcasts not grey, its high crosses the episode high and the prior close is above EMA(21), with a confirmed earnings date not today or tomorrow. | `sleeves/femto/phase_daily.py:234-238`<br>`sleeves/femto/phase_daily.py:467-506` |
| Entry: One trade per episode; ≥ 80 bars; new entries need a fresh earnings calendar. | `sleeves/femto/phase_daily.py:195`<br>`sleeves/femto/phase_daily.py:289-303`<br>`sleeves/femto/phase_daily.py:443-450` |
| Exit: Stop at the box low (K5) or the episode low (NC), ratcheted up to the prior day's EMA(50) before each open; sold at the open when that trail reaches the prior close. | `sleeves/femto/phase_daily.py:306-324`<br>`sleeves/femto/phase_daily.py:369-373`<br>`sleeves/femto/phase_daily.py:457-460`<br>`sleeves/femto/phase_daily.py:498-500` |
| Exit: Sold at the open if the prior close is back below the entry reference within 3 sessions. | `sleeves/femto/phase_daily.py:194`<br>`sleeves/femto/phase_daily.py:374-380` |
| Exit: Flattens in the last 5 minutes before an earnings report today or next session; re-enters the session after the report when price is above the trail. | `sleeves/femto/phase_daily.py:385-395`<br>`sleeves/femto/phase_daily.py:396-405`<br>`sleeves/femto/phase_daily.py:429-442` |
| Sizing: 0.25% of the book risked from entry to stop, capped at 25% notional; at most 10 positions. | `sleeves/femto/phase_daily.py:41-43`<br>`sleeves/femto/phase_daily.py:201-207`<br>`sleeves/femto/phase_daily.py:452-456` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (500), the forming daily bar, earnings dates. | master-desk `desk/sleeves/families/femto_specs.py:187-201` |
| Midna v3 wrapper | `sleeves/phase_daily.py:1-12` |
| Milkman's rule, named in the port | `sleeves/femto/phase_daily.py:3-4` |

## [Phoenix breakout (red-day entry)](../../strategies/femto/femto-phoenix.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a close above each of the prior 20 closes (ties do not count), volume > 0, SPY's 60-session return ≤ 0, ≥ 61 bars. | `sleeves/femto/phoenix.py:62-69`<br>`sleeves/femto/phoenix.py:119-157` |
| Entry: Entry: the first red day (last < the day's open at 15:55 ET) in the 5 sessions after the signal, not on or before the last exit day. | `sleeves/femto/phoenix.py:69`<br>`sleeves/femto/phoenix.py:184-189`<br>`sleeves/femto/phoenix.py:204-214`<br>`sleeves/femto/phoenix.py:329`<br>`sleeves/femto/phoenix.py:405-429` |
| Entry: Entries pause after 3 disaster stops in the trailing 20 closed trades, until a ruling clears it. | `sleeves/femto/phoenix.py:263-282`<br>`sleeves/femto/phoenix.py:417-418`<br>`sleeves/femto/phoenix.py:505-523` |
| Exit: Time stop at the close of the 20th session after entry; a 25% disaster stop below the fill. | `sleeves/femto/phoenix.py:70-71`<br>`sleeves/femto/phoenix.py:172-181`<br>`sleeves/femto/phoenix.py:356-387`<br>`sleeves/femto/phoenix.py:440-444`<br>master-desk `desk/sleeves/families/femto_specs.py:184-185` |
| Sizing: 1% of the book in notional (0.25% risk / 25% stop), at least 1 share; at most 8 positions and 25% of the book. | `sleeves/femto/phoenix.py:72-74`<br>`sleeves/femto/phoenix.py:192-201`<br>`sleeves/femto/phoenix.py:435-439` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (400) and the 15:55 forming bar. | master-desk `desk/sleeves/families/femto_specs.py:176-186` |
| Midna v3 wrapper | `sleeves/phoenix.py:1-12` |

## [Aurelia Nasdaq + gold allocation](../../strategies/femto/femto-aurelia.md)

| Rule | Read from |
|---|---|
| Entry: Per asset (Nasdaq-100 total return, gold futures): unit = trend score (the share of 6 votes: above the 50/100/200-day SMA, positive 63/126/252-day return) × min(cap, 20% / the HAR volatility forecast). | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-47`<br>`sleeves/femto/vendor/aurelia/prism.py:56-69` |
| Entry: The units are averaged and scaled to 35% portfolio volatility (at most 3×), capped per asset (Nasdaq 4, gold 3) and at 6× in total; Femto-lean then cuts the Nasdaq target to 3×. | `sleeves/femto/vendor/aurelia/prism.py:51`<br>`sleeves/femto/vendor/aurelia/prism.py:56-57`<br>`sleeves/femto/vendor/aurelia/prism.py:70-86`<br>`sleeves/femto/feedlib/aurelia.py:159-182` |
| Entry: Band: a held target changes only when the signal moves 0.20, or goes flat. | `sleeves/femto/vendor/aurelia/session.py:17`<br>`sleeves/femto/vendor/aurelia/session.py:93-120` |
| Entry: Posture (Femto-lean): VIX ≥ 25 or a Nasdaq day ≤ -5% caps Nasdaq at 1×; VIX ≥ 40 or ≤ -8% caps it at 0.5×; gold is not cut. APEX C1 has no posture cut. | `sleeves/femto/vendor/aurelia/judgment.py:10-51`<br>`sleeves/femto/aurelia_ndx.py:106-107`<br>`sleeves/apex/vendor/apex/round3.py:233-236` |
| Exit: Positions follow the targets: market-on-close orders on a later session, sent until 15 minutes before the close (APEX C1: the next session, until 20 minutes before). | `sleeves/femto/vendor/aurelia/session.py:15`<br>`sleeves/femto/vendor/aurelia/session.py:77-92`<br>`sleeves/femto/aurelia_ndx.py:153-167`<br>`sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78` |
| Sizing: Femto-lean: Nasdaq = QQQ + 3 × TQQQ within 100% of NAV; gold = GLD one for one; capital used ≤ 180% (both scaled together); idle weight ≥ 2% in BIL; a $500,000 margin book. | `sleeves/femto/vendor/aurelia/allocate.py:15-53`<br>master-desk `desk/sleeves/families/femto_specs.py:636`<br>master-desk `desk/sleeves/families/femto_specs.py:644` |
| Sizing: APEX C1: Nasdaq as QQQ / TQQQ, gold in GLD, idle capital in BIL; above the book's capital a margin debit at 7.75% a year; shares = floor(weight × equity / the last close); a $100,000 book. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo daily history of ^NDX, QQQ, GC=F and ^VIX. | `sleeves/femto/feedlib/aurelia.py:159-190` |
| Data: APEX C1: QQQ's adjusted returns and gold futures (GC=F), with ^IRX for T-bills. | `sleeves/apex/feedlib/apex_rules.py:303-308`<br>`sleeves/apex/feedlib/apex.py:34-39` |
| One book on the master desk | master-desk `desk/sleeves/families/femto_specs.py:630-634` |
| APEX C1 runs the same PRISM excerpt | `sleeves/apex/vendor/apex/round3.py:233-236`<br>`sleeves/apex/vendor/apex/inventions.py:136-179`<br>`sleeves/femto/vendor/aurelia/prism.py:50` |
| Midna v3 first-evaluation freeze | `sleeves/aurelia_ndx.py:263-280`<br>`sleeves/aurelia_ndx.py:297-314` |

## [Beaten-down weekly qualifiers](../../strategies/femto/femto-beatendown.md)

| Rule | Read from |
|---|---|
| Entry: Candidates: the weekly M2 qualifier file (the old desk's Tensor Anna weekly replica with its feature blocks), written after Friday's close. | master-desk `desk/sleeves/femto/m2_core.py:61-92`<br>master-desk `desk/sleeves/families/femto_specs.py:1206` |
| Entry: Selected: close ≤ 80% of the 52-week high (weekly closes); ranked by how many HOLD9 rules fire (each a 3-feature confluence). | master-desk `desk/sleeves/femto/beatendown.py:38-51`<br>master-desk `desk/sleeves/femto/beatendown.py:66-86`<br>master-desk `desk/sleeves/femto/beatendown.py:142-147`<br>master-desk `desk/sleeves/femto/m2_core.py:77-92` |
| Entry: Buys Monday from 10:20 ET at a fresh mid while the desk fear composite is ≥ 55 (it fails open); waits on the last 5 sessions of the year, FOMC days and the session before, and unknown or stale VIX. | master-desk `desk/sleeves/femto/beatendown.py:100-139`<br>master-desk `desk/sleeves/femto/beatendown.py:150`<br>master-desk `desk/sleeves/femto/m2_core.py:95-170`<br>master-desk `desk/sleeves/families/femto_specs.py:1174-1176`<br>master-desk `desk/feedlib/sentiment.py:93-96` |
| Exit: Time exit 91 days (13 weeks) after the fill, sold in a Monday fill at a fresh mid; no stop. | master-desk `desk/sleeves/femto/m2_core.py:24`<br>master-desk `desk/sleeves/femto/m2_core.py:124-142`<br>master-desk `desk/sleeves/femto/m2_core.py:178-188` |
| Sizing: Budget = 30% of the book less held and working notional, split over the week's selected names; whole shares at mid + 25.5 bps, at least 1; at most 10 positions. | master-desk `desk/sleeves/femto/m2_core.py:23-26`<br>master-desk `desk/sleeves/femto/m2_core.py:146-169` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The M2 weekly qualifier file, VIX, the fear composite, desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:452-464` |
| Midna v3 change | `sleeves/beatendown.py:180-190`<br>`sleeves/beatendown.py:225-238` |

## [Winner confluence (weekly qualifiers)](../../strategies/femto/femto-confluence.md)

| Rule | Read from |
|---|---|
| Entry: Candidates: the weekly M2 qualifier file (the old desk's Tensor Anna weekly replica with its feature blocks), written after Friday's close. | master-desk `desk/sleeves/femto/m2_core.py:61-92`<br>master-desk `desk/sleeves/families/femto_specs.py:1206` |
| Entry: Selected: 2+ of the 9 HOLD9 rules fire on the daily bars before the rank day; most rules first. | master-desk `desk/sleeves/femto/confluence.py:34-47`<br>master-desk `desk/sleeves/femto/confluence.py:62-68`<br>master-desk `desk/sleeves/femto/confluence.py:122-127`<br>master-desk `desk/sleeves/femto/m2_core.py:77-92` |
| Entry: Buys Monday from 10:00 ET at a fresh mid; waits on the last 5 sessions of the year, FOMC days and the session before, and unknown or stale VIX; a slot sold that morning can be refilled. | master-desk `desk/sleeves/femto/confluence.py:81-119`<br>master-desk `desk/sleeves/femto/confluence.py:130`<br>master-desk `desk/sleeves/femto/confluence.py:142-143`<br>master-desk `desk/sleeves/femto/m2_core.py:146-169` |
| Exit: Time exit 91 days (13 weeks) after the fill, sold in a Monday fill at a fresh mid; no stop. | master-desk `desk/sleeves/femto/m2_core.py:24`<br>master-desk `desk/sleeves/femto/m2_core.py:124-142`<br>master-desk `desk/sleeves/femto/m2_core.py:178-188` |
| Sizing: Budget = 30% of the book less held and working notional, split over the week's selected names; whole shares at mid + 25.5 bps, at least 1; at most 10 positions. | master-desk `desk/sleeves/femto/m2_core.py:23-26`<br>master-desk `desk/sleeves/femto/m2_core.py:146-169` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The M2 weekly qualifier file, VIX, desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:439-451` |
| Midna v3 change | `sleeves/confluence.py:204-225` |

## [Bilbo Box calls](../../strategies/femto/femto-bilbo-options.md)

| Rule | Read from |
|---|---|
| Entry: Box: hourly bars with extended hours in Saty Phase compression (Bollinger inside Keltner); its high and low widen over the first 5 grey bars; live for 10 days. | master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:57-59`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:92-137`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:147-217` |
| Entry: Trigger: the first hourly bar out of compression closes above the box high, closing 10:00-15:00 ET on a weekday, with spot above the daily 21 EMA. | master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:72`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:147-217`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:218-248`<br>master-desk `desk/sleeves/femto/bilbo_options.py:281-305` |
| Entry: Contract: the nearest expiry 21-37 days out, the strike nearest spot + 0.75 × the prior day's ATR(14); spread ≤ 5% of mid; a limit at the mid, cancelled after 60 minutes; at most 5 open. | master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:68-70`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:249-286`<br>master-desk `desk/sleeves/femto/bilbo_options.py:75`<br>master-desk `desk/sleeves/femto/bilbo_options.py:82`<br>master-desk `desk/sleeves/femto/bilbo_options.py:233-250`<br>master-desk `desk/sleeves/femto/bilbo_options.py:306-334` |
| Entry: Scans hourly at :22 (10:22-15:22 ET) on bars closed ≥ 20 minutes. | master-desk `desk/sleeves/femto/bilbo_options.py:76`<br>master-desk `desk/sleeves/femto/bilbo_options.py:83`<br>master-desk `desk/sleeves/femto/bilbo_options.py:200-207` |
| Exit: On 5-minute regular-hours bars: a close under the box low; or, once the stock has run 1.25 ATR, a close at or below entry + 25% of the peak gain; or 10 trading days after entry. | master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:60-67`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:304-361` |
| Exit: Sold at ≤ 5 days to expiry regardless; exits are limits at the mid, re-priced each pass. | master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:61`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:304-327`<br>master-desk `desk/sleeves/femto/bilbo_options.py:393-420` |
| Sizing: 4% of the book in premium a trade, at least 1 contract. | master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:71`<br>master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:287-303` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Yahoo 5-minute bars (60 days), the desk's call chains (0-60 DTE) and option quotes. | master-desk `desk/sleeves/families/femto_specs.py:465-482` |
| Credit: Milkman's Bilbo Box v2 replication | master-desk `desk/vendor/old_desk_research/bilbo_options_signals.py:1-20` |
| Midna v3 change | `sleeves/bilbo_options.py:58-74` |

## [Capitulation reversal (hourly)](../../strategies/femto/femto-capitulation.md)

| Rule | Read from |
|---|---|
| Entry: Signal on the last closed hourly bar: green, RSI(14) rising from below 20; the prior bar's volume > 2× its 20-bar average and its low within 2% of the 200-day EMA. | master-desk `desk/sleeves/femto/capitulation.py:42-47`<br>master-desk `desk/sleeves/femto/capitulation.py:150-189` |
| Entry: Daily ATR(14) > 5% of the close; buys wait while the desk fear composite is below 55. | master-desk `desk/sleeves/femto/capitulation.py:49-50`<br>master-desk `desk/sleeves/femto/capitulation.py:192-195`<br>master-desk `desk/sleeves/femto/capitulation.py:318-324`<br>master-desk `desk/sleeves/families/femto_specs.py:153` |
| Entry: Half the size first; the other half once the 5-day EMA is above the 20-day, within 5 sessions. | master-desk `desk/sleeves/femto/capitulation.py:59-62`<br>master-desk `desk/sleeves/femto/capitulation.py:116-123`<br>master-desk `desk/sleeves/femto/capitulation.py:293-314`<br>master-desk `desk/sleeves/femto/capitulation.py:325-340` |
| Entry: Scans hourly at :27; a signal after hours fills at the next open. | master-desk `desk/sleeves/families/femto_specs.py:151`<br>master-desk `desk/sleeves/families/femto_specs.py:156` |
| Exit: Back to the session VWAP, +5%, -8%, or 3 trading days; a 25% disaster stop. | master-desk `desk/sleeves/femto/capitulation.py:51-54`<br>master-desk `desk/sleeves/femto/capitulation.py:227-255`<br>master-desk `desk/sleeves/families/femto_specs.py:154-155` |
| Sizing: Full size = 0.25% of the book / an 8% stop; at most 5 positions. | master-desk `desk/sleeves/femto/capitulation.py:55-56`<br>master-desk `desk/sleeves/femto/capitulation.py:217-224`<br>master-desk `desk/sleeves/femto/capitulation.py:316` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Daily bars (260) and regular-hours hourly bars (15 days). | master-desk `desk/sleeves/families/femto_specs.py:145-157` |
| Midna v3 changes | `sleeves/capitulation.py:265-279`<br>`sleeves/capitulation.py:355-369`<br>`sleeves/capitulation.py:395-401` |

## [Capitulation reversal calls (0-7 DTE)](../../strategies/femto/femto-capitulation-options.md)

| Rule | Read from |
|---|---|
| Entry: The capitulation signal (hourly RSI(14) < 20 volume climax into the 200-day EMA, daily ATR > 5%), while the desk fear composite is ≥ 55. | master-desk `desk/sleeves/femto/capitulation_options.py:76-82`<br>master-desk `desk/sleeves/femto/capitulation_options.py:239-241`<br>master-desk `desk/sleeves/femto/capitulation.py:150-195` |
| Entry: Contract: the nearest expiry 0-7 days out, the first strike ≥ spot × 1.02; ask > 0 and spread ≤ 15% of mid; a DAY limit at the ask; at most 5 live. | master-desk `desk/sleeves/femto/capitulation_options.py:61-67`<br>master-desk `desk/sleeves/femto/capitulation_options.py:107-143`<br>master-desk `desk/sleeves/femto/capitulation_options.py:237`<br>master-desk `desk/sleeves/femto/capitulation_options.py:250-253` |
| Entry: Scans hourly at :31 in the session. | master-desk `desk/sleeves/families/femto_specs.py:167` |
| Exit: Premium +75%, 1 day to expiry, or the stock 3% under its entry price; sold with a DAY limit at the bid; no stop. | master-desk `desk/sleeves/femto/capitulation_options.py:64-66`<br>master-desk `desk/sleeves/femto/capitulation_options.py:153-166`<br>master-desk `desk/sleeves/femto/capitulation_options.py:217-225`<br>master-desk `desk/sleeves/families/femto_specs.py:174` |
| Sizing: Premium ≤ 0.10% of the book a trade. | master-desk `desk/sleeves/femto/capitulation_options.py:60`<br>master-desk `desk/sleeves/femto/capitulation_options.py:146-150` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Daily (260) and hourly bars, the desk's 0-7 DTE call chains and quotes. | master-desk `desk/sleeves/families/femto_specs.py:158-175` |
| Midna v3 changes | `sleeves/capitulation_options.py:139`<br>`sleeves/capitulation_options.py:209-225`<br>`sleeves/capitulation_options.py:325-331` |

## [Donchian 20/10 breakout](../../strategies/femto/femto-donchian.md)

| Rule | Read from |
|---|---|
| Entry: A close above the highest high of the prior 20 bars, with volume > 0. | master-desk `desk/sleeves/femto/donchian.py:27`<br>master-desk `desk/sleeves/femto/donchian.py:64-76`<br>master-desk `desk/sleeves/femto/donchian_crypto.py:37`<br>master-desk `desk/sleeves/femto/donchian_crypto.py:67-79` |
| Entry: Equities: checked daily at 10:32 ET, at most 8 positions. SOL: every closed 15-minute bar, one position. | master-desk `desk/sleeves/families/femto_specs.py:65`<br>master-desk `desk/sleeves/femto/donchian.py:35`<br>master-desk `desk/sleeves/femto/donchian.py:167`<br>master-desk `desk/sleeves/families/femto_specs.py:327`<br>master-desk `desk/sleeves/femto/donchian_crypto.py:43`<br>master-desk `desk/sleeves/femto/donchian_crypto.py:159` |
| Exit: A close below the lowest low of the prior 10 bars, or the low touching a trail that ratchets to close - 2 × ATR(14) and never loosens. | master-desk `desk/sleeves/femto/donchian.py:28-31`<br>master-desk `desk/sleeves/femto/donchian.py:79-87`<br>master-desk `desk/sleeves/femto/donchian.py:103-118`<br>master-desk `desk/sleeves/femto/donchian.py:151-156`<br>master-desk `desk/sleeves/femto/donchian_crypto.py:38-41`<br>master-desk `desk/sleeves/femto/donchian_crypto.py:82-106` |
| Exit: Equities also: a 20-session time stop and a 25% disaster stop. | master-desk `desk/sleeves/femto/donchian.py:32-33`<br>master-desk `desk/sleeves/femto/donchian.py:154-159`<br>master-desk `desk/sleeves/families/femto_specs.py:68-69` |
| Sizing: Equities: 0.25% of the book on the 25% disaster-stop distance (1% notional); the sleeve at most 25% of the book. | master-desk `desk/sleeves/femto/donchian.py:33-36`<br>master-desk `desk/sleeves/femto/donchian.py:90-100`<br>master-desk `desk/sleeves/femto/donchian.py:172` |
| Sizing: SOL: 0.25% of the book on 2 × ATR, at most 25% notional; at least $10 when that still fits both caps. | master-desk `desk/sleeves/femto/donchian_crypto.py:42-45`<br>master-desk `desk/sleeves/femto/donchian_crypto.py:109-130` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (160); Kraken public 15-minute SOL bars (120), traded as SOL/USD. | master-desk `desk/sleeves/families/femto_specs.py:61-70`<br>master-desk `desk/sleeves/families/femto_specs.py:320-330` |
| Midna v3 changes | `sleeves/donchian.py:271-288`<br>`sleeves/donchian_crypto.py:84-97` |

## [20-day VWAP reversion](../../strategies/femto/femto-ema-vwap.md)

| Rule | Read from |
|---|---|
| Entry: A close more than 2% under the 20-day VWAP (typical price × volume); ≥ 31 bars; not on or before the last exit day. | master-desk `desk/sleeves/femto/ema_vwap.py:24`<br>master-desk `desk/sleeves/femto/ema_vwap.py:33-34`<br>master-desk `desk/sleeves/femto/ema_vwap.py:47-80`<br>master-desk `desk/sleeves/femto/ema_vwap.py:131-134`<br>master-desk `desk/sleeves/femto/ema_vwap.py:159-163` |
| Entry: Checked hourly at :57 in the session; at most 8 positions. | master-desk `desk/sleeves/families/femto_specs.py:96`<br>master-desk `desk/sleeves/femto/ema_vwap.py:29`<br>master-desk `desk/sleeves/femto/ema_vwap.py:159` |
| Exit: Back at or above the VWAP, +5%, -8%, or 5 weekdays held; a 25% disaster stop. | master-desk `desk/sleeves/femto/ema_vwap.py:25-27`<br>master-desk `desk/sleeves/femto/ema_vwap.py:83-90`<br>master-desk `desk/sleeves/femto/ema_vwap.py:105-112`<br>master-desk `desk/sleeves/femto/ema_vwap.py:147-157`<br>master-desk `desk/sleeves/families/femto_specs.py:99-100` |
| Sizing: 0.25% of the book on the 8% stop, at most 5% of the book a name and 25% for the sleeve. | master-desk `desk/sleeves/femto/ema_vwap.py:28-31`<br>master-desk `desk/sleeves/femto/ema_vwap.py:93-102`<br>master-desk `desk/sleeves/femto/ema_vwap.py:164-166` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (120). | master-desk `desk/sleeves/families/femto_specs.py:92-101` |
| Midna v3 change | `sleeves/ema_vwap.py:122-136` |

## [20-day VWAP reversion call spreads](../../strategies/femto/femto-ema-vwap-options.md)

| Rule | Read from |
|---|---|
| Entry: The stock sleeve's signal: a close more than 2% under the 20-day VWAP. | master-desk `desk/sleeves/femto/ema_vwap_options.py:53`<br>master-desk `desk/sleeves/femto/ema_vwap_options.py:324-325` |
| Entry: Spread: the nearest expiry 14-30 days out; long = the highest strike ≤ spot × 1.02, short = the first strike ≥ long × 1.06; long-leg spread ≤ 10% of mid; re-quoted debit > 0; at most 5 live. | master-desk `desk/sleeves/femto/ema_vwap_options.py:57-67`<br>master-desk `desk/sleeves/femto/ema_vwap_options.py:75-146`<br>master-desk `desk/sleeves/femto/ema_vwap_options.py:156-174`<br>master-desk `desk/sleeves/femto/ema_vwap_options.py:311-346` |
| Exit: Value (long bid - short ask) - debit ≥ 50% of max profit, ≤ 7 DTE, the close back at the VWAP, or 21 days since the fill; closed at the natural price. | master-desk `desk/sleeves/femto/ema_vwap_options.py:62-64`<br>master-desk `desk/sleeves/femto/ema_vwap_options.py:177-208`<br>master-desk `desk/sleeves/femto/ema_vwap_options.py:298-306` |
| Sizing: Contracts = 0.25% of the book / (debit × 100). | master-desk `desk/sleeves/femto/ema_vwap_options.py:149-153`<br>master-desk `desk/sleeves/femto/ema_vwap_options.py:334` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars, the desk's 14-30 DTE call chains and option quotes. | master-desk `desk/sleeves/families/femto_specs.py:102-114` |
| Midna v3 change | `sleeves/ema_vwap_options.py:279-290` |

## [Buyback before earnings (call spreads)](../../strategies/femto/femto-earnings-buyback.md)

| Rule | Read from |
|---|---|
| Entry: Signal: an 8-K repurchase announcement of ≥ 5% of the shares, filed 15-30 days before the earnings date; the weekday EDGAR scan no older than 8 days. | master-desk `desk/sleeves/femto/earnings_buyback.py:74-76`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:91`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:179-214`<br>`sleeves/quant_research/feedlib/edgar_buyback.py:163` |
| Entry: Entry 8-15 days before earnings on a fresh calendar; stock ≥ $10; at most 4 positions, 2 per sector. | master-desk `desk/sleeves/femto/earnings_buyback.py:75`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:79`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:87-88`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:217-240`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:582-600` |
| Entry: Structure: a call debit spread in the nearest 30-45 DTE expiry (long = highest strike ≤ spot, short = the first strike ≥ long × 1.10, debit 30-45% of the width, long-leg spread ≤ 10%); else a call ≥ 2% out of the money (spread ≤ 15%); both must expire after earnings. | master-desk `desk/sleeves/femto/earnings_buyback.py:77`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:81-85`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:111-118`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:275-354`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:366-384` |
| Exit: 15 trading days after earnings, +50% or -50% on the debit, or 5 days to expiry. | master-desk `desk/sleeves/femto/earnings_buyback.py:78`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:80`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:89-90`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:388-413` |
| Sizing: 0.5% of the book in debit a trade. | master-desk `desk/sleeves/femto/earnings_buyback.py:86`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:358-363`<br>master-desk `desk/sleeves/femto/earnings_buyback.py:375-381` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The EDGAR buyback scan (8-K text), the earnings calendar, 30-45 DTE call chains and quotes, sector map. | master-desk `desk/sleeves/families/femto_specs.py:602-616`<br>master-desk `desk/sleeves/families/femto_specs.py:1246-1252` |
| Credit: Quantpedia #0271 (Amini & Singal) | `sleeves/quant_research/feedlib/edgar_buyback.py:1-2` |
| SEC contact ruling | master-desk `AGENTS.md:56-57` |
| Midna v3 change | `sleeves/earnings_buyback.py:60-80` |

## [Fear premium put spreads (red days)](../../strategies/femto/femto-fear-premium.md)

| Rule | Read from |
|---|---|
| Entry: Universe: SOXL and TQQQ plus the 10 basket names with the highest 60-day beta to QQQ, re-ranked every 7 days. | master-desk `desk/sleeves/femto/fear_premium.py:40-43`<br>master-desk `desk/sleeves/femto/fear_premium.py:89-130`<br>master-desk `desk/sleeves/femto/fear_premium.py:310-335` |
| Entry: Signal: the last completed day closed ≥ 5% down with RSI(14) < 50; no earnings today or in the next 3 days (the ETFs clear). | master-desk `desk/sleeves/femto/fear_premium.py:44-46`<br>master-desk `desk/sleeves/femto/fear_premium.py:133-145`<br>master-desk `desk/sleeves/femto/fear_premium.py:287-307` |
| Entry: Spread: short put nearest 7% under the price, long one width lower (about 10% of the price, on the strike grid), one expiry 25-35 DTE; each leg's spread ≤ 10% of mid; credit ≥ 3% of the capital at risk; at most 5. | master-desk `desk/sleeves/femto/fear_premium.py:47-54`<br>master-desk `desk/sleeves/femto/fear_premium.py:148-238` |
| Exit: Half the credit captured, 8 days since the fill, or 21 days to expiry. | master-desk `desk/sleeves/femto/fear_premium.py:48`<br>master-desk `desk/sleeves/femto/fear_premium.py:56-57`<br>master-desk `desk/sleeves/femto/fear_premium.py:252-262`<br>master-desk `desk/sleeves/femto/fear_premium.py:348-362` |
| Sizing: Contracts = 0.5% of the book / the capital at risk, capped by 25% of the book in short-strike notional. | master-desk `desk/sleeves/femto/fear_premium.py:53-55`<br>master-desk `desk/sleeves/femto/fear_premium.py:241-249` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (90), the desk's 25-35 DTE put chains and quotes, the earnings calendar. | master-desk `desk/sleeves/families/femto_specs.py:558-568` |
| Midna v3 change | `sleeves/fear_premium.py:281-300` |

## [Kraken basis repair (ADA / LINK)](../../strategies/femto/femto-kraken-basis.md)

| Rule | Read from |
|---|---|
| Entry: Basis on aligned completed 4h spot and perpetual candles; needs 181 consecutive bars. | master-desk `desk/vendor/aurelia/kraken.py:22-24`<br>master-desk `desk/vendor/aurelia/kraken.py:58-107` |
| Entry: Fires when the signal bar's basis > 0 and > the prior 180-bar mean + 2 sd, and the latest known funding (rate and relative rate) is positive. | master-desk `desk/vendor/aurelia/kraken.py:108-157` |
| Entry: Package: buy 1 token spot at the ask and short 1 contract at the bid, once per signal candle, both quoted and uncrossed; no overlapping package. | master-desk `desk/sleeves/femto/free_kraken_ada_basis.py:68`<br>master-desk `desk/sleeves/femto/free_kraken_ada_basis.py:158-210` |
| Exit: Unwinds both legs when the basis is back at or below the entry mean, or 42 completed 4h candles after the signal; a leg left alone is closed. | master-desk `desk/sleeves/femto/free_kraken_ada_basis.py:71`<br>master-desk `desk/sleeves/femto/free_kraken_ada_basis.py:165-184` |
| Sizing: 1 token a leg, each within 10% of a $100,000 budget. | master-desk `desk/sleeves/femto/free_kraken_ada_basis.py:68-70`<br>master-desk `desk/sleeves/femto/free_kraken_ada_basis.py:146-147` |
| Data: Kraken public 4h spot and perpetual candles, funding prints and the instrument list. | master-desk `desk/sleeves/families/femto_specs.py:856-885` |

## [Kraken breakdown short (ADA / LINK)](../../strategies/femto/femto-kraken-breakdown.md)

| Rule | Read from |
|---|---|
| Entry: Signal: a completed 4h candle whose close is below the lowest low of the 20 bars before it; ≥ 22 bars. | master-desk `desk/vendor/aurelia/kraken_clock.py:10-13`<br>master-desk `desk/vendor/aurelia/kraken_clock.py:47-73` |
| Entry: Entry: short 1 contract at the live bid once open(i+2) (8 hours after the signal opened) has arrived; one short at a time. | master-desk `desk/vendor/aurelia/kraken_clock.py:12`<br>master-desk `desk/vendor/aurelia/kraken_clock.py:25-35`<br>master-desk `desk/sleeves/femto/free_kraken_ada_breakdown.py:45-48` |
| Exit: Covers at the live ask 16 hours after the entry was due. | master-desk `desk/vendor/aurelia/kraken_clock.py:13`<br>master-desk `desk/vendor/aurelia/kraken_clock.py:27-28`<br>master-desk `desk/sleeves/femto/free_kraken_ada_breakdown.py:111-116` |
| Sizing: 1 contract (1 token), within 10% of a $100,000 budget. | master-desk `desk/sleeves/femto/free_kraken_ada_breakdown.py:45-47` |
| Data: Kraken public 4h perpetual candles and the live ticker. | master-desk `desk/sleeves/families/femto_specs.py:800-812` |
| Midna v3 change | `sleeves/free_kraken_ada_breakdown.py:36-41`<br>`sleeves/free_kraken_ada_breakdown.py:181-190` |

## [Kraken crowded-long failure short (ADA / LINK)](../../strategies/femto/femto-kraken-crowded.md)

| Rule | Read from |
|---|---|
| Entry: The breakdown signal (a 4h close under the prior 20 lows, entry at open(i+2)). | master-desk `desk/vendor/aurelia/kraken.py:159-162`<br>master-desk `desk/vendor/aurelia/kraken_clock.py:47-73` |
| Entry: Funding: ≥ 30 prints in 90 days; the latest > 0 and > the 90-day 75th percentile. | master-desk `desk/vendor/aurelia/kraken.py:163-176` |
| Exit: Covers at the live ask 16 hours after the entry was due. | master-desk `desk/sleeves/femto/free_kraken_ada_crowded.py:120`<br>master-desk `desk/vendor/aurelia/kraken_clock.py:13` |
| Sizing: 1 contract (1 token), within 10% of a $100,000 budget. | master-desk `desk/sleeves/femto/free_kraken_ada_crowded.py:50-52` |
| Data: Kraken public 4h perpetual candles, hourly funding prints, the live ticker. | master-desk `desk/sleeves/families/femto_specs.py:826-851` |
| Midna v3 change | `sleeves/free_kraken_ada_crowded.py:29-35` |

## [Kraken ENJ order-book imbalance (spot)](../../strategies/femto/femto-free-kraken-enj-spot.md)

| Rule | Read from |
|---|---|
| Entry: Long when the spread ≤ 50 bps and the top-10 bid depth ≥ 2× the ask depth; one position. | `sleeves/free_kraken_enj_spot.py:45-51`<br>`sleeves/free_kraken_enj_spot.py:85-107`<br>`sleeves/free_kraken_enj_spot.py:136-156` |
| Exit: Sells at the bid when the ask depth ≥ 2× the bid depth, the spread > 200 bps, or 24 hours have passed. | `sleeves/free_kraken_enj_spot.py:201-219` |
| Sizing: floor(min(equity, $10,000) / ask), at least 1, at the ask. | `sleeves/free_kraken_enj_spot.py:229-240` |
| Data: Kraken ENJ/USD depth (top 10 levels). | `sleeves/free_kraken_enj_spot.py:74-82` |
| Master desk: watch row, no orders | master-desk `desk/sleeves/femto/free_kraken_enj_spot.py:83-84`<br>master-desk `desk/sleeves/families/femto_specs.py:892-901` |

## [Own-IV straddle](../../strategies/femto/femto-free-opt-own-iv.md)

| Rule | Read from |
|---|---|
| Entry: Straddle on the nearest 21-35 DTE expiry at least 7 days past the 10-session exit, when the HAR realized-vol forecast to expiry exceeds the straddle's mean implied vol by 2 points. | master-desk `desk/feedlib/free_options_inputs.py:49-53`<br>master-desk `desk/feedlib/free_options_inputs.py:145-162`<br>master-desk `desk/feedlib/free_options_inputs.py:178-205`<br>master-desk `desk/vendor/aurelia/free_options.py:86-95` |
| Entry: Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool. | master-desk `desk/sleeves/femto/free_opt_core.py:26`<br>master-desk `desk/sleeves/femto/free_opt_core.py:58-82`<br>master-desk `desk/sleeves/femto/free_opt_core.py:95-149`<br>master-desk `desk/vendor/aurelia/free_options.py:48-57` |
| Exit: 5 minutes before the close of the 10th session, or expiry; both legs close together. | master-desk `desk/feedlib/free_options_inputs.py:51`<br>master-desk `desk/feedlib/free_options_inputs.py:88-92`<br>master-desk `desk/feedlib/free_options_inputs.py:197-198`<br>master-desk `desk/sleeves/femto/free_opt_core.py:176-191` |
| Sizing: 1 straddle; max loss and risk cap = the natural debit. | master-desk `desk/feedlib/free_options_inputs.py:163-176` |
| Data: SPY daily closes (760) and the desk's SPY chain with IVs. | master-desk `desk/sleeves/families/femto_specs.py:672-690` |
| Midna v3 change | `sleeves/free_opt_own_iv.py:37-42` |

## [SPY / QQQ residual option pair](../../strategies/femto/femto-free-opt-pair.md)

| Rule | Read from |
|---|---|
| Entry: Hedge from the 61 common completed closes before the latest: beta of QQQ on SPY returns; signal = the latest residual \|z\| > 2. | master-desk `desk/feedlib/aurelia_options.py:21-46` |
| Entry: z > 2 buys the QQQ ATM put and SPY ATM calls; z < -2 the reverse; common expiry 30-60 DTE, 7+ days past the exit; SPY contracts = round(\|beta\| × QQQ spot × delta / (SPY spot × delta)). | master-desk `desk/feedlib/free_options_inputs.py:53`<br>master-desk `desk/feedlib/free_options_inputs.py:236-268` |
| Entry: Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool. | master-desk `desk/sleeves/femto/free_opt_core.py:26`<br>master-desk `desk/sleeves/femto/free_opt_core.py:58-82`<br>master-desk `desk/sleeves/femto/free_opt_core.py:95-149`<br>master-desk `desk/vendor/aurelia/free_options.py:48-57` |
| Exit: 10 sessions; a failed leg closes the filled leg. | master-desk `desk/feedlib/free_options_inputs.py:51`<br>master-desk `desk/sleeves/femto/free_opt_core.py:176-191` |
| Sizing: Max loss and risk cap = the legs' total ask. | master-desk `desk/feedlib/free_options_inputs.py:262-265` |
| Data: SPY and QQQ completed closes; both chains. | master-desk `desk/feedlib/aurelia_options.py:18-24` |
| Midna v3 change | `sleeves/free_opt_pair.py:32-37` |

## [Release straddle (CPI, jobs, FOMC)](../../strategies/femto/femto-free-opt-release.md)

| Rule | Read from |
|---|---|
| Entry: A verified public event dated to today's session (CPI and the Employment Situation from FRED's release calendar, the FOMC statement from the Fed's calendar). | master-desk `desk/feedlib/free_options_inputs.py:207-212`<br>master-desk `desk/vendor/aurelia/free_options.py:96-106` |
| Entry: Straddle on the nearest expiry after the session that follows the event, within 45 days. | master-desk `desk/feedlib/free_options_inputs.py:56`<br>master-desk `desk/feedlib/free_options_inputs.py:213-229` |
| Entry: Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool. | master-desk `desk/sleeves/femto/free_opt_core.py:26`<br>master-desk `desk/sleeves/femto/free_opt_core.py:58-82`<br>master-desk `desk/sleeves/femto/free_opt_core.py:95-149`<br>master-desk `desk/vendor/aurelia/free_options.py:48-57` |
| Exit: 5 minutes after the open of the session after the event, or expiry. | master-desk `desk/feedlib/free_options_inputs.py:55`<br>master-desk `desk/feedlib/free_options_inputs.py:223-224` |
| Sizing: 1 straddle; max loss and risk cap = the natural debit. | master-desk `desk/feedlib/free_options_inputs.py:163-176` |
| Data: The release calendar job (FRED and Fed calendars), the desk's SPY chain. | master-desk `desk/feedlib/free_options_inputs.py:207-212` |
| Midna v3 change | `sleeves/free_opt_release.py:20-27` |

## [Tail put after a -3% day](../../strategies/femto/femto-free-opt-tail.md)

| Rule | Read from |
|---|---|
| Entry: SPY's session return (live mid over the last close) ≤ -3%. | master-desk `desk/vendor/aurelia/free_options.py:80-85` |
| Entry: The put with \|delta\| 0.50-0.65, 21-35 DTE, expiring 7+ days past the 5-session exit; nearest expiry, then delta nearest 0.575; 1 contract at the ask, once per session. | master-desk `desk/feedlib/free_options_inputs.py:51-54`<br>master-desk `desk/feedlib/free_options_inputs.py:278-290` |
| Entry: Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool. | master-desk `desk/sleeves/femto/free_opt_core.py:26`<br>master-desk `desk/sleeves/femto/free_opt_core.py:58-82`<br>master-desk `desk/sleeves/femto/free_opt_core.py:95-149`<br>master-desk `desk/vendor/aurelia/free_options.py:48-57` |
| Exit: Five sessions, or the mark at half the fill; sold at the bid. | master-desk `desk/sleeves/femto/free_opt_tail.py:53-54`<br>master-desk `desk/sleeves/femto/free_opt_tail.py:76-84` |
| Sizing: 1 contract. | master-desk `desk/vendor/aurelia/free_options.py:80-85` |
| Data: SPY's last close and live quote, the desk's SPY put chain. | master-desk `desk/sleeves/families/femto_specs.py:742-759` |
| Midna v3 change | `sleeves/free_opt_tail.py:23-28` |

## [SPY 30-delta wheel](../../strategies/femto/femto-free-opt-wheel.md)

| Rule | Read from |
|---|---|
| Entry: Put: nearest 7-14 DTE expiry, \|delta\| nearest 0.30, then the strike nearest spot; only when cash covers strike × 100; sold at the bid, once per session. | master-desk `desk/feedlib/free_options_inputs.py:53-54`<br>master-desk `desk/feedlib/free_options_inputs.py:292-296`<br>master-desk `desk/vendor/aurelia/free_options.py:120-133` |
| Entry: After assignment: one call the same way against 100 free shares, once per session. | master-desk `desk/feedlib/free_options_inputs.py:292-296`<br>master-desk `desk/sleeves/femto/free_opt_wheel.py:69-97` |
| Entry: Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool. | master-desk `desk/sleeves/femto/free_opt_core.py:26`<br>master-desk `desk/sleeves/femto/free_opt_core.py:58-82`<br>master-desk `desk/sleeves/femto/free_opt_core.py:95-149`<br>master-desk `desk/vendor/aurelia/free_options.py:48-57` |
| Exit: No early exit: expiry, or assignment (puts) and call assignment (calls). | master-desk `desk/vendor/aurelia/free_options.py:37-40` |
| Sizing: 1 contract; cash = the book's cash less the strike value of its short puts. | master-desk `desk/vendor/aurelia/free_options.py:120-133` |
| Data: The desk's SPY chain, the book's cash and shares. | master-desk `desk/sleeves/families/femto_specs.py:760-775` |
| Midna v3 change | `sleeves/free_opt_wheel.py:44-50` |

## [SPY put-call parity package](../../strategies/femto/femto-free-opt-parity.md)

| Rule | Read from |
|---|---|
| Entry: Residuals from put-call parity on the SPY chain against shares financed at the 3-month T-bill rate; expiries 1-45 days, before the next ex-dividend date, strikes within 5% of spot; costs $0.03 an option leg each way. | master-desk `desk/sleeves/femto/free_opt_parity.py:78-87`<br>master-desk `desk/sleeves/femto/free_opt_parity.py:102-145` |
| Entry: Entry: the pair with the largest positive residual: 100 shares with 1 put and 1 call, each at its side of a synchronized snapshot; the package's unwind cost ≤ 10% of the book. | master-desk `desk/sleeves/femto/free_opt_parity.py:151-173`<br>master-desk `desk/sleeves/femto/free_opt_parity.py:197-305` |
| Entry: Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool. | master-desk `desk/sleeves/femto/free_opt_core.py:26`<br>master-desk `desk/sleeves/femto/free_opt_core.py:58-82`<br>master-desk `desk/sleeves/femto/free_opt_core.py:95-149`<br>master-desk `desk/vendor/aurelia/free_options.py:48-57` |
| Exit: Residual at or below zero (also the stop), five sessions, or the shared expiry. | master-desk `desk/sleeves/femto/free_opt_parity.py:83`<br>master-desk `desk/sleeves/femto/free_opt_parity.py:197-305` |
| Sizing: One package; a $100,000 book. | master-desk `desk/sleeves/femto/free_opt_parity.py:82`<br>master-desk `desk/sleeves/families/femto_specs.py:690-741` |
| Data: The SPY chain (Cboe delayed or Alpaca indicative), SPY quotes, FRED DTB3. | master-desk `desk/sleeves/femto/free_opt_parity.py:31-60` |
| Midna v3 change | `sleeves/free_opt_parity.py:13-25` |

## [Leader-1d event](../../strategies/femto/femto-leader-d.md)

| Rule | Read from |
|---|---|
| Entry: Event on a closed daily bar: score ≥ 3 of 5 (close ≥ 8% over EMA(21); RSI(12) ≥ 60; volume ≥ 1.2× its 20-day mean; 20-day path efficiency ≥ 0.30; ≥ 4 of 7 trend votes) and a gate: a UT Bot buy flip (cyan) or an EMA 8/21 cross after a recent flip (green), each with the votes lined up. | master-desk `desk/vendor/old_desk_research/leader1d_long_fulluniverse_2026-10-02.py:135-183`<br>master-desk `desk/vendor/old_desk_research/leader1d_long_fulluniverse_2026-10-02.py:236-284`<br>master-desk `desk/feedlib/leader.py:56-57` |
| Entry: Daily: the last close's event ranks after 16:40 ET (≥ 252 bars, once per event) and buys from 10:40 ET the next session; the Femto daily variant only while SPY's 60-session return ≤ 0. | master-desk `desk/sleeves/femto/leader_core.py:26-50`<br>master-desk `desk/sleeves/femto/leader_d.py:63-98`<br>master-desk `desk/sleeves/femto/leader_d.py:104-117` |
| Entry: Small caps: the bottom tenth of the genome by trailing 52-week mean weekly dollar volume (at least 9 names); no regime filter. | master-desk `desk/sleeves/femto/leader_sc.py:28`<br>master-desk `desk/sleeves/femto/leader_sc.py:54-86`<br>master-desk `desk/sleeves/femto/leader_sc.py:118-126` |
| Entry: Hourly (basket): the first regular-hours hourly bar after the event date, at least 20 hourly bars after the last entry. | master-desk `desk/sleeves/femto/gate_1h.py:29-30`<br>master-desk `desk/sleeves/femto/gate_1h.py:48-55`<br>master-desk `desk/sleeves/femto/gate_1h.py:80-110` |
| Exit: Daily: sold once 19 bars have closed after entry (the 20th session); backstop 32 days; a 25% disaster stop. | master-desk `desk/sleeves/femto/leader_core.py:12`<br>master-desk `desk/sleeves/femto/leader_core.py:20-23`<br>master-desk `desk/sleeves/femto/leader_core.py:51-52`<br>master-desk `desk/sleeves/families/femto_specs.py:256-257` |
| Exit: Hourly: sold 20 hourly bars after the entry bar; backstop 4 days; 25% stop. | master-desk `desk/sleeves/femto/gate_1h.py:111-121`<br>master-desk `desk/sleeves/femto/gate_1h.py:135-137`<br>master-desk `desk/sleeves/families/femto_specs.py:289-290` |
| Exit: Killed study: in at the next open, out at the close of the 20th session; one hold per name. | `sleeves/killed/daily.py:111-154` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Modeled cost a side: 5 bps (daily), 150 bps (small caps), 10 bps (hourly). | master-desk `desk/sleeves/families/femto_specs.py:258`<br>master-desk `desk/sleeves/families/femto_specs.py:272`<br>master-desk `desk/sleeves/families/femto_specs.py:291` |
| Sizing: Killed study: $100,000 / 300 a name long (genome), / 41 short (basket). | `sleeves/killed/daily.py:155-180`<br>`sleeves/killed/common.py:32` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The genome job's daily leader-event rows; split-adjusted daily bars (600); hourly bars for the hourly variant. | master-desk `desk/sleeves/families/femto_specs.py:245-292` |
| Midna v3 changes | `sleeves/leader_d.py:48-56`<br>`sleeves/gate_1h.py:48-56` |

## [High-IV iron condor](../../strategies/femto/femto-iron-condor.md)

| Rule | Read from |
|---|---|
| Entry: IV rank ≥ 50 on the at-the-money call IV (30-45 DTE) over its last 252 stored readings (60 needed); VIX ≤ 35; no earnings in the next 45 days on a fresh calendar; at most 3 condors. | master-desk `desk/sleeves/femto/iron_condor.py:59-74`<br>master-desk `desk/sleeves/femto/iron_condor.py:137-153`<br>master-desk `desk/sleeves/femto/iron_condor.py:270-320`<br>master-desk `desk/sleeves/femto/iron_condor.py:483-502` |
| Entry: Condor: one 30-45 DTE expiry; shorts nearest 0.16 Black-Scholes delta, wings nearest 0.05 beyond; all four legs two-sided within 10% of mid; net credit > 0; max loss on the wider wing. | master-desk `desk/sleeves/femto/iron_condor.py:60-62`<br>master-desk `desk/sleeves/femto/iron_condor.py:157-245` |
| Exit: Half the credit captured, a loss of 2× the credit, ≤ 7 DTE, 21 days held, a short leg deep in the money, or earnings entering the window. | master-desk `desk/sleeves/femto/iron_condor.py:63-65`<br>master-desk `desk/sleeves/femto/iron_condor.py:72`<br>master-desk `desk/sleeves/femto/iron_condor.py:376-422`<br>master-desk `desk/sleeves/femto/iron_condor.py:466-470` |
| Sizing: 1% of the book on the max loss, at most 25 contracts. | master-desk `desk/sleeves/femto/iron_condor.py:66`<br>master-desk `desk/sleeves/femto/iron_condor.py:71`<br>master-desk `desk/sleeves/femto/iron_condor.py:258-263` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars, the desk's 30-45 DTE chains and quotes, the earnings calendar, VIX, stored IV history. | master-desk `desk/sleeves/families/femto_specs.py:569-588` |
| Midna v3 change | `sleeves/iron_condor.py:263-282` |

## [VXX call tail hedge](../../strategies/femto/femto-vix-hedge.md)

| Rule | Read from |
|---|---|
| Entry: Complacent: VIX < 16 or below the 25th percentile of its last 30 closes (35+ closes needed). | master-desk `desk/sleeves/femto/vix_hedge.py:35-37`<br>master-desk `desk/sleeves/femto/vix_hedge.py:55-71` |
| Entry: The call: per expiry 60-110 days out the strike nearest 1.20 × spot; the expiry nearest 90 days first; two-sided within 20% of mid; a limit at the ask; one hedge at a time. | master-desk `desk/sleeves/femto/vix_hedge.py:39-46`<br>master-desk `desk/sleeves/femto/vix_hedge.py:74-126`<br>master-desk `desk/sleeves/femto/vix_hedge.py:187-205` |
| Exit: Value 2× the debit, VIX > 30, or ≤ 21 days to expiry; sold at the mid. | master-desk `desk/sleeves/femto/vix_hedge.py:38`<br>master-desk `desk/sleeves/femto/vix_hedge.py:42`<br>master-desk `desk/sleeves/femto/vix_hedge.py:47`<br>master-desk `desk/sleeves/femto/vix_hedge.py:136-147`<br>master-desk `desk/sleeves/femto/vix_hedge.py:162-186` |
| Sizing: Premium ≤ 1% of the book. | master-desk `desk/sleeves/femto/vix_hedge.py:45`<br>master-desk `desk/sleeves/femto/vix_hedge.py:129-133` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Yahoo ^VIX daily closes (130), the desk's 60-110 DTE VXX call chain and quotes. | master-desk `desk/sleeves/families/femto_specs.py:589-601` |

## [LEAPS momentum with covered calls](../../strategies/femto/femto-leaps-momentum.md)

| Rule | Read from |
|---|---|
| Entry: Follows the Femto momentum book (fresh within 7 days): one LEAPS per held name, at most 8. | master-desk `desk/sleeves/femto/leaps_momentum.py:66`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:68`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:83-96`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:350-396` |
| Entry: LEAPS: the nearest expiry ≥ 365 days, the strike nearest 0.80 × spot; spread ≤ 5% of mid; a limit at the ask. | master-desk `desk/sleeves/femto/leaps_momentum.py:58`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:65`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:69`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:99-135`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:396-402` |
| Entry: Short call: the nearest 25-38 DTE expiry, the first strike ≥ max(spot × (1 + 0.67 × 30-day vol), LEAPS breakeven × 1.02); spread ≤ 5%; sold at the bid. | master-desk `desk/sleeves/femto/leaps_momentum.py:61-62`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:160-221`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:434-441` |
| Exit: LEAPS: the name leaves the momentum book, ≤ 60 DTE, or the mid 30% under the premium paid. | master-desk `desk/sleeves/femto/leaps_momentum.py:59-60`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:148-157` |
| Exit: Short call: rolled at ≤ 21 DTE or when the stock trades within 3% of its strike. | master-desk `desk/sleeves/femto/leaps_momentum.py:63-64`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:224-234`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:418-428` |
| Sizing: 1 contract per 100 shares of the momentum position (at least 1), premium ≤ 5% of the book. | master-desk `desk/sleeves/femto/leaps_momentum.py:67`<br>master-desk `desk/sleeves/femto/leaps_momentum.py:138-145` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The momentum sleeve's book, split-adjusted daily bars (35), LEAPS (365-1,500 DTE) and 25-38 DTE call chains, option quotes. | master-desk `desk/sleeves/families/femto_specs.py:542-557` |
| Midna v3 change | `sleeves/leaps_momentum.py:84-110` |

## [Legend's EMA (trend-day fade)](../../strategies/femto/femto-legends-ema.md)

| Rule | Read from |
|---|---|
| Entry: Setup: the prior regular session's 15-minute bars all above (or all below) their EMA(20) without touching it, and \|close - open\| / range at least 0.7686 (Femto-lean) or its 2000-2012 80th percentile (the Milkman study). | master-desk `desk/sleeves/femto/legends_ema.py:38-42`<br>master-desk `desk/sleeves/femto/legends_ema.py:63-90`<br>master-desk `desk/sleeves/femto/legends_ema.py:150-163`<br>`sleeves/milkman/intraday.py:629-669` |
| Entry: At the open, toward the EMA: short when the open is above it, long when below; one trade a session. Femto-lean enters 09:30-09:45 ET at the open print and cancels after 240 s unfilled. | master-desk `desk/sleeves/femto/legends_ema.py:44-45`<br>master-desk `desk/sleeves/femto/legends_ema.py:225-249`<br>`sleeves/milkman/intraday.py:670-680` |
| Exit: Femto-lean: take-profit at the EMA (refreshed once it moves $0.20); stop 0.5 × ATR(14) of daily ranges from the fill; flat at 15:59 ET (5 minutes before an early close). | master-desk `desk/sleeves/femto/legends_ema.py:41`<br>master-desk `desk/sleeves/femto/legends_ema.py:43`<br>master-desk `desk/sleeves/femto/legends_ema.py:93-98`<br>master-desk `desk/sleeves/femto/legends_ema.py:104-106`<br>master-desk `desk/sleeves/femto/legends_ema.py:166-198`<br>master-desk `desk/sleeves/femto/legends_ema.py:219-224` |
| Exit: Milkman study: out at the first touch of the latest completed 15-minute bar's EMA, else at the close; no stop. | `sleeves/milkman/intraday.py:684-699` |
| Sizing: Femto-lean: shares = 0.25% of the book / (0.5 × ATR14). | master-desk `desk/sleeves/femto/legends_ema.py:37`<br>master-desk `desk/sleeves/femto/legends_ema.py:238-244` |
| Sizing: Femto-lean: each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Sizing: Milkman study: $10,000 a trade on a $1,000,000 book, every trade taken. | `sleeves/milkman/intraday.py:59-60`<br>`sleeves/milkman/intraday.py:1088`<br>`sleeves/milkman/intraday.py:1146-1147` |
| Data: Yahoo 15-minute bars (260), split-adjusted daily bars (40), the open print. | master-desk `desk/sleeves/families/femto_specs.py:202-218` |
| Data: Milkman study: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only. | `sleeves/milkman/intraday.py:98-99`<br>`sleeves/milkman/intraday.py:178-214`<br>`sleeves/milkman/intraday.py:1182-1190` |
| Midna v3 change | `sleeves/legends_ema.py:99-112` |
| Milkman's page for it | master-desk `docs/research/2026-10-19-milkman/REVIEW.md:39` |

## [Red-day washout reversal](../../strategies/femto/femto-red-day-reversal.md)

| Rule | Read from |
|---|---|
| Entry: Signal on the last completed day: close ≥ 3% down, RSI(2) ≤ 10, close > SMA200 (202+ bars). | master-desk `desk/sleeves/femto/red_day_reversal.py:27-30`<br>master-desk `desk/sleeves/femto/red_day_reversal.py:78-94` |
| Entry: No earnings within 5 days (the index and leveraged ETFs clear); in regular hours only; a limit at the last close until the close; at most 8 positions. | master-desk `desk/sleeves/femto/red_day_reversal.py:36-38`<br>master-desk `desk/sleeves/femto/red_day_reversal.py:115-119`<br>master-desk `desk/sleeves/femto/red_day_reversal.py:141-152`<br>master-desk `desk/sleeves/femto/red_day_reversal.py:190-210` |
| Exit: +4% (a limit), -2% (market) on a fresh intraday mark, or 3 days after the fill. | master-desk `desk/sleeves/femto/red_day_reversal.py:32`<br>master-desk `desk/sleeves/femto/red_day_reversal.py:34-35`<br>master-desk `desk/sleeves/femto/red_day_reversal.py:122-138` |
| Sizing: 0.25% of the book on the 2% stop, at most 25% of the book in notional. | master-desk `desk/sleeves/femto/red_day_reversal.py:31-33`<br>master-desk `desk/sleeves/femto/red_day_reversal.py:105-112` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (220), intraday marks, the earnings calendar. | master-desk `desk/sleeves/families/femto_specs.py:113-122` |
| Midna v3 change | `sleeves/red_day_reversal.py:130-139`<br>`sleeves/red_day_reversal.py:188-199` |

## [RSI(2) pullback call spreads](../../strategies/femto/femto-rsi-meanrev-options.md)

| Rule | Read from |
|---|---|
| Entry: Signal on completed closes: RSI(2) < 10 and close > SMA200 (200+ bars). | master-desk `desk/sleeves/femto/rsi_meanrev_options.py:52-55`<br>master-desk `desk/sleeves/femto/rsi_meanrev_options.py:70-84` |
| Entry: Spread: the nearest expiry 14-30 days out; long = the last strike ≤ the close, short = the first strike ≥ long × 1.08; long-leg spread ≤ 10% of mid; debit > 0; at most 5. | master-desk `desk/sleeves/femto/rsi_meanrev_options.py:57-62`<br>master-desk `desk/sleeves/femto/rsi_meanrev_options.py:106-168` |
| Exit: Value - debit ≥ 50% of max profit, ≤ 7 DTE, or RSI(2) > 70. | master-desk `desk/sleeves/femto/rsi_meanrev_options.py:54`<br>master-desk `desk/sleeves/femto/rsi_meanrev_options.py:60-61`<br>master-desk `desk/sleeves/femto/rsi_meanrev_options.py:202-215` |
| Sizing: Contracts = 0.25% of the book / (debit × 100). | master-desk `desk/sleeves/femto/rsi_meanrev_options.py:56`<br>master-desk `desk/sleeves/femto/rsi_meanrev_options.py:171-177` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars (260), the desk's 14-30 DTE call chains and quotes. | master-desk `desk/sleeves/families/femto_specs.py:82-91` |
| Midna v3 change | `sleeves/rsi_meanrev_options.py:50-60` |

## [Daily Cyan GBM](../../strategies/femto/femto-daily-cyan-gbm.md)

| Rule | Read from |
|---|---|
| Entry: A daily cyan fire with the frozen GBM score ≥ 0.00208; close ≥ $5 and 20-day dollar volume ≥ $1M; best score first. Midna's lab account uses the training 90th-percentile cut. | master-desk `desk/sleeves/femto/daily_cyan_gbm.py:28-30`<br>master-desk `desk/sleeves/femto/daily_cyan_gbm.py:63-78`<br>`sleeves/midna/forward_scan.py:741`<br>`sleeves/midna/forward_scan.py:755-766` |
| Entry: Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law. | master-desk `desk/sleeves/femto/dcg_core.py:23-33`<br>master-desk `desk/sleeves/femto/dcg_core.py:40-55`<br>master-desk `desk/sleeves/femto/dcg_core.py:83-100` |
| Exit: Hold 21 sessions; a 25% disaster stop (Femto). | master-desk `desk/sleeves/femto/daily_cyan_gbm.py:28`<br>master-desk `desk/sleeves/femto/daily_cyan_gbm.py:62`<br>master-desk `desk/sleeves/families/femto_specs.py:359-360` |
| Exit: Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days. | master-desk `desk/sleeves/femto/dcg_core.py:56-67` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 10 bps a side. | master-desk `desk/sleeves/femto/daily_cyan_gbm.py:61` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Sizing: Midna's lab account: floor(($20,000 / 6) / (price × (1 + cost))); up to 6 hits; entry from 10:00 ET the next session. | `sleeves/midna/forward.py:54-127` |
| Data: The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:347-362` |
| Midna v3 change | `sleeves/daily_cyan_gbm.py:51-56` |

## [Daily Cyan small-cap rule](../../strategies/femto/femto-rule-1d-cyan-smallcap.md)

| Rule | Read from |
|---|---|
| Entry: A daily cyan fire with the scorer's pxn = 2 and DI between -10.59 and 12.56; close $5-10, 20-day dollar volume ≥ $1M, EDGAR log market cap ≤ 9.38. | master-desk `desk/sleeves/femto/rule_1d_cyan_smallcap.py:35-47`<br>master-desk `desk/sleeves/femto/rule_1d_cyan_smallcap.py:106-126` |
| Entry: Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law. | master-desk `desk/sleeves/femto/dcg_core.py:23-33`<br>master-desk `desk/sleeves/femto/dcg_core.py:40-55`<br>master-desk `desk/sleeves/femto/dcg_core.py:83-100` |
| Exit: Hold 21 sessions; no stop. | master-desk `desk/sleeves/femto/rule_1d_cyan_smallcap.py:35`<br>master-desk `desk/sleeves/families/femto_specs.py:375` |
| Exit: Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days. | master-desk `desk/sleeves/femto/dcg_core.py:56-67` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 10 bps a side. | master-desk `desk/sleeves/femto/daily_cyan_gbm.py:61` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:363-377` |
| Midna v3 change | `sleeves/rule_1d_cyan_smallcap.py:40-46` |

## [Daily Green turn-of-month rule](../../strategies/femto/femto-rule-1d-green-tom.md)

| Rule | Read from |
|---|---|
| Entry: A daily green fire with 12-1 momentum ≥ 0.65, dispersion 0.0208-0.0286 and a turn-of-month day (the last trading day or the first 3 of the month, NYSE calendar); close ≥ $5, 20-day dollar volume ≥ $1M. | master-desk `desk/sleeves/femto/rule_1d_green_tom.py:40-52`<br>master-desk `desk/sleeves/femto/rule_1d_green_tom.py:123-145`<br>master-desk `desk/sleeves/femto/rule_1d_green_tom.py:192-210` |
| Entry: Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law. | master-desk `desk/sleeves/femto/dcg_core.py:23-33`<br>master-desk `desk/sleeves/femto/dcg_core.py:40-55`<br>master-desk `desk/sleeves/femto/dcg_core.py:83-100` |
| Exit: Hold 63 sessions; no stop. | master-desk `desk/sleeves/femto/rule_1d_green_tom.py:40`<br>master-desk `desk/sleeves/femto/rule_1d_green_tom.py:222` |
| Exit: Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days. | master-desk `desk/sleeves/femto/dcg_core.py:56-67` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 10 bps a side. | master-desk `desk/sleeves/femto/daily_cyan_gbm.py:61` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:378-392` |
| Midna v3 change | `sleeves/rule_1d_green_tom.py:171-175` |

## [Weekly Cyan momentum ADX rule](../../strategies/femto/femto-rule-1w-cyan-mom-adx.md)

| Rule | Read from |
|---|---|
| Entry: A weekly cyan fire with log10 dollar volume ≤ 7.35, 126-day return ≥ 44.5% and ADX ≥ 25.8; close ≥ $5, 20-day dollar volume ≥ $1M. | master-desk `desk/sleeves/femto/rule_1w_cyan_mom_adx.py:26-37`<br>master-desk `desk/sleeves/femto/rule_1w_cyan_mom_adx.py:96-112`<br>`sleeves/midna/forward_scan.py:731-737`<br>`sleeves/midna/forward_scan.py:750-751` |
| Entry: Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law. | master-desk `desk/sleeves/femto/dcg_core.py:23-33`<br>master-desk `desk/sleeves/femto/dcg_core.py:40-55`<br>master-desk `desk/sleeves/femto/dcg_core.py:83-100` |
| Exit: Hold 126 sessions; no stop. | master-desk `desk/sleeves/femto/rule_1w_cyan_mom_adx.py:26`<br>`sleeves/midna/forward_scan.py:750-751` |
| Exit: Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days. | master-desk `desk/sleeves/femto/dcg_core.py:56-67` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 10 bps a side. | master-desk `desk/sleeves/femto/daily_cyan_gbm.py:61` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Sizing: Midna's lab account: floor(($20,000 / 6) / (price × (1 + cost))); up to 6 hits; entry from 10:00 ET the next session. | `sleeves/midna/forward.py:54-127` |
| Data: The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:393-407` |
| Midna v3 change | `sleeves/rule_1w_cyan_mom_adx.py:31-35` |

## [Weekly swing high-beta WaveTrend rule](../../strategies/femto/femto-rule-1w-swing-beta-wt.md)

| Rule | Read from |
|---|---|
| Entry: A weekly swing fire with beta to SPY ≥ 1.355, WaveTrend wt1 ≥ 25.93 and ribbons ≥ 0.0095; close ≥ $5, 20-day dollar volume ≥ $1M. | master-desk `desk/sleeves/femto/rule_1w_swing_beta_wt.py:25-36`<br>master-desk `desk/sleeves/femto/rule_1w_swing_beta_wt.py:95-111` |
| Entry: Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law. | master-desk `desk/sleeves/femto/dcg_core.py:23-33`<br>master-desk `desk/sleeves/femto/dcg_core.py:40-55`<br>master-desk `desk/sleeves/femto/dcg_core.py:83-100` |
| Exit: Hold 126 sessions; no stop. | master-desk `desk/sleeves/femto/rule_1w_swing_beta_wt.py:25`<br>master-desk `desk/sleeves/femto/rule_1w_swing_beta_wt.py:124` |
| Exit: Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days. | master-desk `desk/sleeves/femto/dcg_core.py:56-67` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 10 bps a side. | master-desk `desk/sleeves/femto/daily_cyan_gbm.py:61` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:408-422` |
| Midna v3 change | `sleeves/rule_1w_swing_beta_wt.py:30-34` |

## [Hourly Cyan range-expansion rule](../../strategies/femto/femto-rule-1h-cyan-raw.md)

| Rule | Read from |
|---|---|
| Entry: An hourly cyan fire on the latest closed regular-hours bar with range/ATR ≥ 2.05, WaveTrend gap ≥ 6.88 and SMH up; close ≥ $5; 20-day dollar volume ≥ $1M; 100+ hourly bars. | master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:42-48`<br>master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:78-94`<br>master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:97-114`<br>master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:139-157` |
| Entry: Scans hourly at :26 and buys at the next :04 pass, 10:00-15:59 ET, through the fill law. | master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:120-125`<br>master-desk `desk/sleeves/families/femto_specs.py:431` |
| Exit: Sold 7 hourly bars after entry; backstop 2 days; no stop. | master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:42`<br>master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:183-188`<br>master-desk `desk/sleeves/families/femto_specs.py:436` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 10 bps a side. | master-desk `desk/sleeves/femto/rule_1h_cyan_raw.py:117` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The hourly DCG fire file, regular-hours hourly bars (1,000), daily bars for dollar volume. | master-desk `desk/sleeves/families/femto_specs.py:423-438` |
| Midna v3 change | `sleeves/rule_1h_cyan_raw.py:44-48` |

## [12-month momentum top decile (monthly)](../../strategies/femto/femto-ts-momentum-decile.md)

| Rule | Read from |
|---|---|
| Entry: Eligible: 253+ completed bars, median 63-day dollar volume ≥ $1M, no bankruptcy-artifact month; ranked by close / close 252 sessions back; the top 10% (rounded up). | master-desk `desk/sleeves/femto/ts_momentum_decile.py:56-59`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:114-150`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:187-214` |
| Entry: A known sector (semis, leveraged ETFs, biotech, software, energy, financials) may hold at most 25% of the names; the lowest-ranked are trimmed. | master-desk `desk/sleeves/femto/ts_momentum_decile.py:62`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:70-101`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:153-184` |
| Entry: Rebalances on the month's first trading day from 10:00 ET once most names carry the previous session (any data by 15:30). | master-desk `desk/sleeves/femto/ts_momentum_decile.py:64-66`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:221-250`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:257-275` |
| Exit: A name out of the new decile is sold at the rebalance; no stop. | master-desk `desk/sleeves/femto/ts_momentum_decile.py:273`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:309-316`<br>master-desk `desk/sleeves/families/femto_specs.py:344` |
| Sizing: Equal weight: 95% of the book / the decile's size, whole shares (at least 1) at a fresh mid. | master-desk `desk/sleeves/femto/ts_momentum_decile.py:60`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:278-289`<br>master-desk `desk/sleeves/femto/ts_momentum_decile.py:318-333` |
| Sizing: Cost modeled at 75 bps a side. | master-desk `desk/sleeves/families/femto_specs.py:345` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars of the genome (400, cached), desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:331-346` |
| Midna v3 change | `sleeves/ts_momentum_decile.py:163-180` |

## [Tensor 1H swing flagship](../../strategies/femto/femto-tensor-swing.md)

| Rule | Read from |
|---|---|
| Entry: Signal: the newest confirmed swing of the Tensor v698 engine on canonical 1H bars, at most 3 bars and 6 clock hours old, not acted on before. | master-desk `desk/sleeves/femto/tensor_swing.py:61-66`<br>master-desk `desk/sleeves/femto/tensor_swing.py:115-135`<br>master-desk `desk/sleeves/femto/tensor_swing.py:271-294` |
| Entry: Trade at confidence ≥ 8 (6-7 is watch only); not extended; the latest bar's low still above the planned stop; not held; at most 10 positions, 3 per sector. | master-desk `desk/sleeves/femto/tensor_swing.py:75-77`<br>master-desk `desk/sleeves/femto/tensor_swing.py:242-247`<br>master-desk `desk/sleeves/femto/tensor_swing.py:295-328`<br>master-desk `desk/sleeves/femto/tensor_swing.py:421-437` |
| Entry: Order: a GTC bracket limit at the signal close, take-profit at the engine's target, stop at its invalidation. | master-desk `desk/sleeves/femto/tensor_swing.py:314-341`<br>master-desk `desk/sleeves/families/femto_specs.py:518` |
| Exit: The bracket's stop or target; a bearish trigger on either of the last two closed bars (bearish conflict, more bear than bull votes, consensus-sell); or more than 20 closed bars held. | master-desk `desk/sleeves/femto/tensor_swing.py:67`<br>master-desk `desk/sleeves/femto/tensor_swing.py:351-401`<br>master-desk `desk/sleeves/femto/tensor_swing.py:483` |
| Sizing: 1% of the book risked on entry - stop, × 0.75 when a held name's 1H-return correlation ≥ 0.65 (× 0.5 at 0.80); notional ≤ 50% of the book. | master-desk `desk/sleeves/femto/tensor_swing.py:63`<br>master-desk `desk/sleeves/femto/tensor_swing.py:68-72`<br>master-desk `desk/sleeves/femto/tensor_swing.py:219-236`<br>master-desk `desk/sleeves/femto/tensor_swing.py:329-338` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The canonical Tensor feed (1H), split-adjusted daily bars (300). | master-desk `desk/sleeves/families/femto_specs.py:509-521` |
| Midna v3 change | `sleeves/tensor_swing.py:108-115`<br>`sleeves/tensor_swing.py:230-232` |

## [Tensor red-dip buys on fear days](../../strategies/femto/femto-tensor-red-dip.md)

| Rule | Read from |
|---|---|
| Entry: Fear day: QQQ's live price ≤ -1.5% vs the prior close (unknown fails closed). | master-desk `desk/sleeves/femto/tensor_red_dip.py:58`<br>master-desk `desk/sleeves/femto/tensor_red_dip.py:182-191`<br>master-desk `desk/sleeves/femto/tensor_red_dip.py:244-250` |
| Entry: Candidates: today's fresh flagship signals with confidence ≥ 7, one per name; bought while the name is red on the day; at most 5. | master-desk `desk/sleeves/femto/tensor_red_dip.py:59`<br>master-desk `desk/sleeves/femto/tensor_red_dip.py:64`<br>master-desk `desk/sleeves/femto/tensor_red_dip.py:72-94`<br>master-desk `desk/sleeves/femto/tensor_red_dip.py:251-266`<br>master-desk `desk/sleeves/families/femto_specs.py:1036-1043` |
| Exit: +3% target, -8% stop (engine-held from the fill), or the 3rd trading day. | master-desk `desk/sleeves/femto/tensor_red_dip.py:61-63`<br>master-desk `desk/sleeves/femto/tensor_red_dip.py:106-137`<br>master-desk `desk/sleeves/families/femto_specs.py:538-540` |
| Sizing: 0.25% of the book on the 8% stop, at least 1 share. | master-desk `desk/sleeves/femto/tensor_red_dip.py:60-61`<br>master-desk `desk/sleeves/femto/tensor_red_dip.py:97-103` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: The Tensor swing flagship's fresh signals, live quotes, prior closes. | master-desk `desk/sleeves/families/femto_specs.py:522-541` |
| Midna v3 change | `sleeves/tensor_red_dip.py:69-76`<br>`sleeves/tensor_red_dip.py:208-212` |

## [Microcap snapback (weekly)](../../strategies/femto/femto-snapback.md)

| Rule | Read from |
|---|---|
| Entry: Band: the bottom 10% of the genome by trailing 52-week mean weekly dollar volume (at least 9 names). | master-desk `desk/sleeves/femto/snapback.py:28`<br>master-desk `desk/sleeves/femto/snapback.py:59-93` |
| Entry: Flagged: 20-day mean daily range / close in the band's top third, a 13-week return ≤ -20%, and distance from the 52-week low not in the bottom third; widest range first. | master-desk `desk/sleeves/femto/snapback.py:94-142`<br>master-desk `desk/sleeves/femto/snapback.py:43-52` |
| Entry: Ranks Friday after 16:35 ET once most names carry the day's bar; buys Monday from 10:35 ET; not a name exited within 91 days. | master-desk `desk/sleeves/femto/snapback.py:151`<br>master-desk `desk/sleeves/femto/snapback.py:186-228`<br>master-desk `desk/sleeves/families/femto_specs.py:237` |
| Exit: Sold 91 days after the Monday fill; no stop. | master-desk `desk/sleeves/femto/snapback.py:29`<br>master-desk `desk/sleeves/femto/snapback.py:221`<br>master-desk `desk/sleeves/families/femto_specs.py:242` |
| Sizing: Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions. | `sleeves/femto/sleeve_core.py:26-28`<br>`sleeves/femto/sleeve_core.py:146-170` |
| Sizing: Cost modeled at 150 bps a side. | master-desk `desk/sleeves/femto/snapback.py:30`<br>master-desk `desk/sleeves/families/femto_specs.py:243` |
| Sizing: Each sleeve trades its own $100,000 book unless its spec row names another. | master-desk `desk/sleeves/families/femto.py:95` |
| Data: Split-adjusted daily bars of the genome (300, cached), desk quotes. | master-desk `desk/sleeves/families/femto_specs.py:230-244` |
| Midna v3 change | `sleeves/snapback.py:23-30`<br>`sleeves/snapback.py:42` |
