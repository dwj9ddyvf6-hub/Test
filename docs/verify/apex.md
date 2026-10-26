# Verification: APEX

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk), or at `22f3e991c224` where a cite names it (the four recorders converted into books on 2026-10-26); every other path is in this repository.

## [APEX-50F Nasdaq trend × volatility](../../strategies/apex/apex-trend-har-tiers.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-50F: exposure = trend score × min(4, 50% / volatility). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109`<br>`sleeves/apex/vendor/apex/strategies.py:70-71`<br>`sleeves/apex/feedlib/apex_rules.py:207-209` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Recorded tiers | `sleeves/apex/feedlib/apex_rules.py:25`<br>`sleeves/apex/feedlib/apex_rules.py:207-209`<br>`sleeves/apex/vendor/apex/strategies.py:66-72` |
| The desk's live tier | `sleeves/apex/apex.py:13-14` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX QQQ benchmark](../../strategies/apex/apex-benchmarks.md)

| Rule | Read from |
|---|---|
| Entry: Nasdaq-100 exposure 1× every session. | `sleeves/apex/vendor/apex/strategies.py:57-58`<br>`sleeves/apex/vendor/apex/engine.py:98-102`<br>`sleeves/apex/feedlib/apex_rules.py:148-149`<br>`sleeves/apex/feedlib/apex_rules.py:212-214` |
| Exit: None: always fully invested. | `sleeves/apex/vendor/apex/engine.py:98-102` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): the whole book in QQQ. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-108`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Recorded baselines | `sleeves/apex/feedlib/apex_rules.py:26`<br>`sleeves/apex/feedlib/apex_rules.py:212-214`<br>`sleeves/apex/vendor/apex/strategies.py:57-65` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX E1: VIX term-structure gate](../../strategies/apex/apex-e1-vix-term-gate.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-30: exposure = trend score × min(3, 30% / volatility), × 0.5 when VIX / VIX3M > 1. | `sleeves/apex/vendor/apex/strategies.py:20-30`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:80-83`<br>`sleeves/apex/feedlib/apex_rules.py:227-230` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^VIX and ^VIX3M; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX E2: Double 7 dip overlay](../../strategies/apex/apex-e2-double7-dip.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-30: exposure = trend score × min(3, 30% / volatility), + 0.5 while the dip is on, at most 3×. | `sleeves/apex/vendor/apex/strategies.py:20-30`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:86-90`<br>`sleeves/apex/feedlib/apex_rules.py:233-235` |
| Entry: Dip: starts on a 7-day closing low of the Nasdaq-100 total return while the trend score is ≥ 0.5; ends on a 7-day closing high. | `sleeves/femto/vendor/aurelia/features.py:87-100`<br>`sleeves/apex/vendor/apex/strategies.py:87-88` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: The extra 0.5× leaves at the 7-day closing high; no stop. | `sleeves/femto/vendor/aurelia/features.py:97-98`<br>`sleeves/apex/vendor/apex/strategies.py:89` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |
| Double 7 is Connors' rule (named so in the Milkman study's code) | `sleeves/milkman/vendor/milkman/dstrats.py:13-14` |

## [APEX E3 / v1.1: defensive Treasuries](../../strategies/apex/apex-e3-defensive-treasuries.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Exposure = trend score × min(max, target / volatility): E3 is APEX-30 (30%, 3×), v1.1 is APEX-50F (50%, 4×). | `sleeves/apex/vendor/apex/strategies.py:20-30`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:99-115`<br>`sleeves/apex/feedlib/apex_rules.py:222-224`<br>`sleeves/apex/feedlib/apex_rules.py:238-240` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of the band or more, or to 0: E3 0.20, v1.1 0.50. | `sleeves/apex/vendor/apex/strategies.py:110`<br>`sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Entry: Idle capital in IEF while the 7-10-year Treasury total return is above its 200-day average, else BIL. | `sleeves/apex/vendor/apex/strategies.py:93-96`<br>`sleeves/apex/feedlib/apex_rules.py:217-219`<br>`sleeves/apex/apex.py:81` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only the idle asset. | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: IEF's total return; before IEF, a duration model on the 10-year yield (^TNX). | `sleeves/apex/vendor/apex/series.py:46-60` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX E4: rolling tail puts](../../strategies/apex/apex-e4-rolling-tail-puts.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Core: APEX-30 exposure = trend score × min(3, 30% / volatility), with its 0.20 band. | `sleeves/apex/vendor/apex/strategies.py:20-30`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex_options.py:79-80`<br>`sleeves/apex/apex_options.py:256`<br>`sleeves/apex/feedlib/apex.py:315-317` |
| Entry: Puts: at a month's first session, while the APEX-30 exposure held after this close is above 1.5, buys QQQ puts 15% under spot, the listed expiry nearest 63 sessions, on exposure × NAV / spot shares (whole contracts). | `sleeves/apex/apex_options.py:59`<br>`sleeves/apex/apex_options.py:220-229`<br>`sleeves/apex/apex_options.py:283-303`<br>`sleeves/apex/vendor/apex/backtest_options.py:77-85` |
| Exit: At each month's first session the held puts are sold before any new ones are bought; between months they are held. | `sleeves/apex/apex_options.py:220-229`<br>`sleeves/apex/apex_options.py:275-282`<br>`sleeves/apex/vendor/apex/backtest_options.py:72-76` |
| Sizing: Puts once a session in the last 45 minutes (15:15-15:45 ET), marketable limits; the core market-on-close on the equity less the puts' value; a $1,000,000 book. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex_options.py:177-189`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and the listed QQQ puts. | `sleeves/apex/feedlib/apex.py:355-362`<br>`sleeves/apex/apex_options.py:237-250` |
| Named divergence: listed QQQ puts at the market | `sleeves/apex/apex_options.py:46-50` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX E5: semiconductor tilt](../../strategies/apex/apex-e5-semis-rs-tilt.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-30: exposure = trend score × min(3, 30% / volatility). | `sleeves/apex/vendor/apex/strategies.py:20-30`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:138` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Entry: Tilt: a third of the exposure in SMH while SMH's 126-day return beats the Nasdaq-100's and SMH is above its 200-day average. | `sleeves/apex/vendor/apex/strategies.py:130-136`<br>`sleeves/apex/feedlib/apex_rules.py:243-247` |
| Exit: The tilt returns to the Nasdaq when either test fails; no stop. | `sleeves/apex/vendor/apex/strategies.py:133-136`<br>`sleeves/apex/feedlib/apex_rules.py:246-247` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), SMH adjusted closes; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682`<br>`sleeves/apex/feedlib/apex_rules.py:244` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX E6: overnight boost](../../strategies/apex/apex-e6-overnight-boost.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-30: exposure = trend score × min(3, 30% / volatility). | `sleeves/apex/vendor/apex/strategies.py:20-30`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:147` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Entry: Boost: +1× QQQ bought market-on-close with the core when the trend score is ≥ 0.5. | `sleeves/apex/vendor/apex/strategies.py:150`<br>`sleeves/apex/feedlib/apex_rules.py:250-260`<br>`sleeves/apex/apex.py:307-313` |
| Exit: The boost is sold at the next session's first pass (09:30-09:40 ET), a marketable order. | `sleeves/apex/apex.py:285`<br>`sleeves/apex/apex.py:287-305` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Boost shares = floor(book equity / the QQQ close). | `sleeves/apex/apex.py:310` |
| Sizing: The core market-on-close, ordered 60 to 20 minutes before the close: Nasdaq up to 1× in QQQ, 1-3× QQQ + TQQQ, idle capital in BIL. | `sleeves/apex/apex.py:285`<br>`sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:98-140` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Named divergence: the boost sale | `sleeves/apex/apex.py:51-52` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX E7: turn-of-month boost](../../strategies/apex/apex-e7-turn-of-month.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-30: exposure = trend score × min(3, 30% / volatility), + 0.5 held over the turn of the month (its last session and the next month's first three) while the trend score is ≥ 0.5, at most 3×. | `sleeves/apex/vendor/apex/strategies.py:20-30`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:160-165`<br>`sleeves/femto/vendor/aurelia/features.py:103-110`<br>`sleeves/apex/feedlib/apex_rules.py:263-271` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: The 0.5× leaves after the month's third session; no stop. | `sleeves/femto/vendor/aurelia/features.py:103-110`<br>`sleeves/apex/vendor/apex/strategies.py:162-163` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX N1: Duration Shield](../../strategies/apex/apex-n1-duration-shield.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-50F: exposure = trend score × min(4, 50% / volatility), × 0.5 when the 10-year yield (^TNX) is up more than 0.50 over 63 sessions. | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109`<br>`sleeves/apex/vendor/apex/inventions.py:57-65`<br>`sleeves/apex/feedlib/apex_rules.py:274-276` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX N2: Silicon Switch](../../strategies/apex/apex-n2-silicon-switch.md)

| Rule | Read from |
|---|---|
| Entry: Switch: to the SOX when its 126-day return beats the Nasdaq-100's by more than 5 points; back when the Nasdaq-100 leads by more than 5. | `sleeves/apex/vendor/apex/inventions.py:69-88`<br>`sleeves/apex/feedlib/apex_rules.py:279-282` |
| Entry: Exposure: APEX-50F of the index held (trend score × min(4, 50% / volatility) from its own votes and HAR forecast). | `sleeves/apex/vendor/apex/inventions.py:89-94`<br>`sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:109` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: No stop: a switch moves the whole exposure between the two indexes. | `sleeves/apex/vendor/apex/inventions.py:93-98`<br>`sleeves/apex/feedlib/apex_rules.py:279-282` |
| Sizing: Nasdaq exposure as QQQ / TQQQ; every other asset one for one in its ETF; idle capital in BIL; anything above the book's capital runs a margin debit. | `sleeves/apex/feedlib/apex.py:38-39`<br>`sleeves/apex/apex.py:98-140` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^SOX and SMH; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The SOX total return: ^SOX + 1% a year until SMH's history starts, then SMH's. | `sleeves/apex/vendor/apex/inventions.py:35-41` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX N3 / N4: PRISM multi-asset trend](../../strategies/apex/apex-n3-prism-classic.md)

| Rule | Read from |
|---|---|
| Entry: Per asset: unit = trend score × min(cap, 20% / HAR volatility), once it has 380 days of history. | `sleeves/apex/vendor/apex/inventions.py:141-155` |
| Entry: The units are averaged over the assets available, then × min(3, 35% / the forecast volatility of that average); caps Nasdaq 4, Treasuries 5, gold 3, oil 2, dollar 4, semiconductors 3, Bitcoin 1; gross ≤ 6. | `sleeves/apex/vendor/apex/inventions.py:136`<br>`sleeves/apex/vendor/apex/inventions.py:156-171` |
| Entry: Each asset's held weight moves only on a change of 0.20 or more, a session after the decision. | `sleeves/apex/vendor/apex/inventions.py:105-121`<br>`sleeves/apex/feedlib/apex_rules.py:285-300` |
| Entry: Assets: N3 the Nasdaq-100, 7-10-year Treasuries (IEF), gold (GLD), oil (USO), the dollar (UUP); N4 the Nasdaq-100, semiconductors (SOX, held as SMH), gold (GLD), Bitcoin. | `sleeves/apex/feedlib/apex_rules.py:413-414`<br>`sleeves/apex/vendor/apex/inventions.py:44-53` |
| Exit: No stop: weights follow the targets; a trend score of 0 takes an asset to 0. | `sleeves/apex/vendor/apex/inventions.py:153`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Nasdaq exposure as QQQ / TQQQ; every other asset one for one in its ETF; idle capital in BIL; anything above the book's capital runs a margin debit. | `sleeves/apex/feedlib/apex.py:38-39`<br>`sleeves/apex/apex.py:98-140` |
| Sizing: N4's Bitcoin trades on Alpaca crypto in the last 10 minutes of the equity session. | `sleeves/apex/apex.py:168-171` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), IEF, GLD, USO, UUP and ^TNX (N3); ^SOX, SMH, GLD and BTC-USD (N4); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: N3's Treasuries: IEF's total return; before IEF, a duration model on the 10-year yield (^TNX). | `sleeves/apex/vendor/apex/series.py:46-60` |
| Data: N4's semiconductors: ^SOX + 1% a year until SMH's history starts, then SMH's total return. | `sleeves/apex/vendor/apex/inventions.py:35-41` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX N5: GESTALT analog engine](../../strategies/apex/apex-n5-gestalt.md)

| Rule | Read from |
|---|---|
| Entry: State: trend score, log volatility and its 21-day change, the 252-day drawdown, the 21-day return, the 63-day change in the 10-year yield, VIX against its 252-day median, and semiconductors' 63-day return over the Nasdaq's. | `sleeves/apex/vendor/apex/inventions.py:183-199`<br>`sleeves/apex/vendor/apex/inventions.py:231-237` |
| Entry: Every 5 sessions from 2001: the 150 nearest past states (z-scored distance) whose forward 21-day excess log return is known; their mean, annualised and shrunk halfway to the all-history mean. | `sleeves/apex/vendor/apex/inventions.py:202-225`<br>`sleeves/apex/vendor/apex/inventions.py:240-243` |
| Entry: Leverage = 0.5 × that mean / max(volatility, 5%)², clipped to 0-4; held between refits. | `sleeves/apex/vendor/apex/inventions.py:226-228` |
| Entry: The held exposure moves to it only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/inventions.py:244-245`<br>`sleeves/apex/vendor/apex/strategies.py:51-52`<br>`sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153` |
| Exit: No stop: a negative analog mean takes the exposure to 0. | `sleeves/apex/vendor/apex/inventions.py:226` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX, ^VIX, ^SOX and SMH; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |
| Run as its research runner did | `sleeves/apex/feedlib/apex_rules.py:355-361` |

## [APEX N6: GESTALT × APEX](../../strategies/apex/apex-n6-gestalt-apex.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Exposure = ½ × (APEX-50F target + GESTALT leverage). | `sleeves/apex/vendor/apex/inventions.py:248-251`<br>`sleeves/apex/feedlib/apex_rules.py:364-369` |
| Entry: GESTALT: half-Kelly on the mean forward 21-day excess return of the 150 most similar past states, refit every 5 sessions, 0-4. | `sleeves/apex/vendor/apex/inventions.py:202-245` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX, ^VIX, ^SOX and SMH; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX N7: OMNI](../../strategies/apex/apex-n7-omni.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Core: APEX-50F exposure = trend score × min(4, 50% / volatility), × 0.5 when the 10-year yield is up more than 0.50 over 63 sessions; 0.20 band. | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109`<br>`sleeves/apex/vendor/apex/inventions.py:57-65`<br>`sleeves/apex/feedlib/apex_rules.py:402-405` |
| Entry: Variance Value, at a month's first session with none held, on the next monthly expiry ≥ 15 days out: at-the-money implied vol / the HAR forecast ≥ 1.25 sells the at-the-money straddle and buys wings 1.5 σ√T out (an iron fly), NAV / spot shares a leg; ≤ 0.95 buys the at-the-money straddle with 2% of NAV. | `sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Exit: Option structures are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:156-170`<br>`sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Variance Value on the whole book's NAV. | `sleeves/apex/feedlib/apex_rules.py:405`<br>`sleeves/apex/apex.py:577-584` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX C2: Sector Kings](../../strategies/apex/apex-c2-sector-kings.md)

| Rule | Read from |
|---|---|
| Entry: Each month's first session: of the 9 sector SPDRs, the 2 with the best 126-day return among those above their 200-day average, equal weight; none qualifying holds cash. | `sleeves/apex/vendor/apex/round3.py:24`<br>`sleeves/apex/vendor/apex/round3.py:139-159` |
| Entry: Scale: × min(2, 25% / the HAR forecast of the held basket's volatility). | `sleeves/apex/vendor/apex/round3.py:160-165` |
| Entry: Each weight moves only on a change of 0.20 or more, a session after the decision. | `sleeves/apex/vendor/apex/round3.py:28-41`<br>`sleeves/apex/feedlib/apex_rules.py:311-327` |
| Exit: A sector leaves at the next month's pick; no stop. | `sleeves/apex/vendor/apex/round3.py:152-159` |
| Sizing: Sector ETFs one for one (up to 2× in all, on margin); idle capital in BIL. | `sleeves/apex/feedlib/apex.py:38-39`<br>`sleeves/apex/apex.py:111-140`<br>`sleeves/apex/vendor/apex/round3.py:164` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo adjusted closes of the 9 sector SPDRs and ^IRX. | `sleeves/apex/vendor/apex/round3.py:141-143`<br>`sleeves/apex/feedlib/apex.py:33-36` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX C3: Follow-through](../../strategies/apex/apex-c3-follow-through.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-50F: exposure = trend score × min(4, 50% / volatility). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109`<br>`sleeves/apex/vendor/apex/round3.py:80-84` |
| Entry: Follow-through: once the Nasdaq-100 closes 10% under its 63-day high, the first session up ≥ 1.25% that closes at a 10-day high lifts exposure to at least 2× for 20 sessions; one per correction, re-armed after a new 63-day high. | `sleeves/apex/vendor/apex/round3.py:52-77`<br>`sleeves/apex/vendor/apex/round3.py:83`<br>`sleeves/apex/feedlib/apex_rules.py:330-332` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: The boost ends after 20 sessions; no stop. | `sleeves/apex/vendor/apex/round3.py:62-64`<br>`sleeves/apex/vendor/apex/round3.py:72-76` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX C4: Broken Hedge](../../strategies/apex/apex-c4-broken-hedge.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-50F: exposure = trend score × min(4, 50% / volatility), × 0.5 while the Nasdaq's 63-day correlations with both Treasuries and gold are above 0.20. | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109`<br>`sleeves/apex/vendor/apex/round3.py:109-117`<br>`sleeves/apex/vendor/apex/round3.py:130`<br>`sleeves/apex/feedlib/apex_rules.py:335-342` |
| Entry: Idle capital: the most negatively correlated of Treasuries (IEF), gold (GLD) and the dollar index (UUP) when that correlation is below -0.10, else BIL. | `sleeves/apex/vendor/apex/round3.py:118-125`<br>`sleeves/apex/feedlib/apex_rules.py:341`<br>`sleeves/apex/feedlib/apex.py:38-39` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only the idle asset. | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), GC=F, DX-Y.NYB and ^TNX; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: IEF's total return; before IEF, a duration model on the 10-year yield (^TNX). | `sleeves/apex/vendor/apex/series.py:46-60` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX C5: REFLEX](../../strategies/apex/apex-c5-reflex.md)

| Rule | Read from |
|---|---|
| Entry: State: trend score, log volatility and its 21-day change, the 252-day drawdown, the 21-day return, the 63-day change in the 10-year yield, VIX against its 252-day median, and semiconductors' 63-day return over the Nasdaq's. | `sleeves/apex/vendor/apex/inventions.py:183-199`<br>`sleeves/apex/vendor/apex/inventions.py:231-237` |
| Entry: Every 5 sessions from 2001: leverage = 0.5 × the shrunk mean forward 21-day excess return of the 150 nearest past states / max(volatility, 5%)², clipped to 0-4. | `sleeves/apex/vendor/apex/round3.py:173-196` |
| Entry: Recency: with ≥ 15 of the 150 in the last 1,260 sessions, a negative mean among those while all 150 average positive cuts leverage to a quarter; a recent mean more than 10 points above the 150's raises it 25% (max 4). | `sleeves/apex/vendor/apex/round3.py:197-206` |
| Entry: The held exposure moves to it only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/round3.py:207-209`<br>`sleeves/apex/vendor/apex/strategies.py:51-52`<br>`sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153` |
| Exit: No stop: a negative analog mean takes the exposure to 0. | `sleeves/apex/vendor/apex/round3.py:196` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX, ^VIX, ^SOX and SMH; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |
| Run as its research runner did | `sleeves/apex/feedlib/apex_rules.py:345-347` |

## [APEX C6: SLINGSHOT](../../strategies/apex/apex-c6-slingshot.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: APEX-50F: exposure = trend score × min(4, 50% / volatility). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109`<br>`sleeves/apex/vendor/apex/round3.py:104-106` |
| Entry: Slingshot: trend score ≥ 4 of 6, the 10-year yield up more than 0.50 over 63 sessions and the Nasdaq-100 down ≥ 5% over 10 sessions lift exposure to at least 3× for 10 sessions. | `sleeves/apex/vendor/apex/round3.py:87-106`<br>`sleeves/apex/feedlib/apex_rules.py:350-352` |
| Entry: Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/agents.py:24-28`<br>`sleeves/apex/feedlib/apex_rules.py:142-153`<br>`sleeves/apex/vendor/apex/engine.py:55-62` |
| Exit: The boost ends after 10 sessions; no stop. | `sleeves/apex/vendor/apex/round3.py:95-103` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL. | `sleeves/apex/vendor/apex/agents.py:13-20`<br>`sleeves/apex/apex.py:77-78`<br>`sleeves/apex/apex.py:98-140`<br>`sleeves/apex/apex.py:168-172` |
| Sizing: Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year. | `sleeves/apex/apex.py:76`<br>`sleeves/apex/apex.py:143-156`<br>`sleeves/apex/apex.py:177`<br>`sleeves/apex/apex.py:235-245` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX C7: COUNCIL](../../strategies/apex/apex-c7-council.md)

| Rule | Read from |
|---|---|
| Entry: Nasdaq book: N6, ½ × (APEX-50F target + GESTALT leverage), with the 0.20 band. | `sleeves/apex/feedlib/apex_rules.py:364-369`<br>`sleeves/apex/feedlib/apex_rules.py:376-380`<br>`sleeves/apex/vendor/apex/inventions.py:248-251` |
| Entry: Gold book: gold futures' trend score × min(2, 20% / HAR volatility), 0.20 band, held as GLD. | `sleeves/apex/vendor/apex/round3.py:212-221`<br>`sleeves/apex/feedlib/apex_rules.py:372-373` |
| Entry: Options book: the Variance Value rule (as O6) on its share of the book. | `sleeves/apex/vendor/apex/opt_strategies.py:198-218`<br>`sleeves/apex/apex.py:586-588` |
| Entry: Bitcoin variant: 10% at Bitcoin's trend score × min(1, 20% / HAR volatility), 0.20 band; the other books keep C7's proportions on the remaining 90%. | `sleeves/apex/feedlib/apex_rules.py:383-399` |
| Exit: No stops: each book follows its target; option structures are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:198-218`<br>`sleeves/apex/vendor/apex/strategies.py:46-48` |
| Sizing: Fixed shares of equity, the options book's T-bills = its share less its options' value. | `sleeves/apex/feedlib/apex_rules.py:379`<br>`sleeves/apex/feedlib/apex_rules.py:398`<br>`sleeves/apex/apex.py:590-598` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: Exposure books market-on-close; Bitcoin in the last 10 minutes of the equity session; a $1,000,000 book. | `sleeves/apex/apex.py:168-172`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), GC=F, BTC-USD, ^TNX, ^VIX, ^SOX and SMH; recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Named divergence: the Bitcoin sleeve | `sleeves/apex/apex.py:53-56` |
| Source and vendoring | `sleeves/apex/apex.py:3-9` |

## [APEX O1: CONVEX](../../strategies/apex/apex-o1-convex.md)

| Rule | Read from |
|---|---|
| Entry: L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)). | `sleeves/apex/vendor/apex/opt_strategies.py:43-47`<br>`sleeves/apex/vendor/apex/opt_strategies.py:96`<br>`sleeves/apex/feedlib/apex.py:279`<br>`sleeves/apex/feedlib/apex.py:322`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109` |
| Entry: Core: QQQ at min(L*, 1) with a 0.20 band. | `sleeves/apex/vendor/apex/opt_strategies.py:67-69`<br>`sleeves/apex/apex_options.py:83-88` |
| Entry: Calls for the rest (L* - 1): at the money, the expiry nearest 91 days, delta-sized: want × NAV / (delta × spot) shares. | `sleeves/apex/vendor/apex/opt_strategies.py:77-86`<br>`sleeves/apex/vendor/apex/opt_strategies.py:291-293` |
| Entry: O1: re-struck at each month's first session or when the calls' delta exposure is 0.5 off the want (expiry ≥ 45 days, delta > 0.05). | `sleeves/apex/vendor/apex/opt_strategies.py:79-86` |
| Entry: O1b: opens at a want ≥ 0.5 (expiry ≥ 60 days, at most 99.5% of NAV in premium), then adjusts the held call by whole contracts when 0.5 off. | `sleeves/apex/vendor/apex/opt_strategies.py:289-300`<br>`sleeves/apex/feedlib/apex_book.py:88-102` |
| Exit: O1 closes the calls on a re-strike with nothing wanted; O1b rolls under 45 days or outside 0.30-0.85 delta, and adjusts toward 0 when nothing is wanted. | `sleeves/apex/vendor/apex/opt_strategies.py:79-81`<br>`sleeves/apex/vendor/apex/opt_strategies.py:282-287`<br>`sleeves/apex/vendor/apex/opt_strategies.py:297-300` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |

## [APEX O2: LEAPS-APEX](../../strategies/apex/apex-o2-leaps.md)

| Rule | Read from |
|---|---|
| Entry: L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)). | `sleeves/apex/vendor/apex/opt_strategies.py:43-47`<br>`sleeves/apex/vendor/apex/opt_strategies.py:96`<br>`sleeves/apex/feedlib/apex.py:279`<br>`sleeves/apex/feedlib/apex.py:322`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109` |
| Entry: Calls: the expiry nearest 365 days (≥ 300), the strike for 0.80 delta. | `sleeves/apex/vendor/apex/opt_strategies.py:244-245` |
| Entry: O2: calls = L* × NAV / (max(delta, 0.5) × spot) shares, re-struck when none are held, under 183 days, or 0.5 off L*. | `sleeves/apex/vendor/apex/opt_strategies.py:96-112` |
| Entry: O2b: calls = L* × NAV / (delta × spot), at most 99.5% of NAV in premium; adjusted by whole contracts when 0.5 off. | `sleeves/apex/vendor/apex/opt_strategies.py:243-256`<br>`sleeves/apex/feedlib/apex_book.py:88-102` |
| Exit: L* ≤ 0 sells the calls; O2b rolls under 183 days or outside 0.60-0.95 delta. | `sleeves/apex/vendor/apex/opt_strategies.py:104-106`<br>`sleeves/apex/vendor/apex/opt_strategies.py:232-242` |
| Sizing: Core: T-bills (BIL). | `sleeves/apex/apex_options.py:89` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Core: T-bills | `sleeves/apex/apex_options.py:314-316` |

## [APEX O3: regime put-write](../../strategies/apex/apex-o3-regime-putwrite.md)

| Rule | Read from |
|---|---|
| Entry: L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)). | `sleeves/apex/vendor/apex/opt_strategies.py:43-47`<br>`sleeves/apex/vendor/apex/opt_strategies.py:96`<br>`sleeves/apex/feedlib/apex.py:279`<br>`sleeves/apex/feedlib/apex.py:322`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109` |
| Entry: At a month's first session with L* > 0 and no puts held: sells puts struck spot × e^(-0.5 σ√T) (σ = at-the-money implied vol), the next monthly expiry ≥ 15 days out, on min(L*, 3) × NAV / spot shares. | `sleeves/apex/vendor/apex/opt_strategies.py:118-135` |
| Exit: L* ≤ 0 buys the puts back; otherwise they are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:125-127` |
| Sizing: Core: T-bills (BIL). | `sleeves/apex/apex_options.py:89` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Core: T-bills | `sleeves/apex/apex_options.py:319-320` |

## [APEX O4: PHOENIX](../../strategies/apex/apex-o4-phoenix.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ. | `sleeves/apex/apex_options.py:76-80`<br>`sleeves/apex/feedlib/apex.py:311-314` |
| Entry: PHOENIX: when the Nasdaq-100 is ≥ 15% under its 252-day high, 30-day implied vol (VXN) is at or above its 252-day 80th percentile and the level is at or above the prior 10-day high, buys at-the-money calls, the expiry nearest 91 days (≥ 60), premium 5% of NAV; one position at a time. | `sleeves/apex/vendor/apex/opt_strategies.py:139-153`<br>`sleeves/apex/vendor/apex/opt_strategies.py:48-52` |
| Exit: PHOENIX calls are sold with 30 days or less to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:141-144` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Overlay on the APEX-50F core | `sleeves/apex/apex_options.py:321-322`<br>`sleeves/apex/vendor/apex/opt_strategies.py:186-194` |

## [APEX O5: CHOP HARVEST](../../strategies/apex/apex-o5-chop-harvest.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ. | `sleeves/apex/apex_options.py:76-80`<br>`sleeves/apex/feedlib/apex.py:311-314` |
| Entry: CHOP: at a month's first session when the trend score is 2, 3 or 4 of 6 votes, sells the call and put 1 σ√T out and buys wings 2 σ√T out (an iron condor), NAV / spot shares a leg, the next monthly expiry ≥ 15 days out. | `sleeves/apex/vendor/apex/opt_strategies.py:156-170` |
| Exit: Option structures are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:156-170`<br>`sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Overlay on the APEX-50F core | `sleeves/apex/apex_options.py:323-324`<br>`sleeves/apex/vendor/apex/opt_strategies.py:186-194` |

## [APEX O6: Variance Value](../../strategies/apex/apex-o6-variance-value.md)

| Rule | Read from |
|---|---|
| Entry: Core: QQQ at 1×. | `sleeves/apex/apex_options.py:81-82` |
| Entry: Variance Value, at a month's first session with none held, on the next monthly expiry ≥ 15 days out: at-the-money implied vol / the HAR forecast ≥ 1.25 sells the at-the-money straddle and buys wings 1.5 σ√T out (an iron fly), NAV / spot shares a leg; ≤ 0.95 buys the at-the-money straddle with 2% of NAV. | `sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Exit: Option structures are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:156-170`<br>`sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Rule on a QQQ core | `sleeves/apex/apex_options.py:331-332`<br>`sleeves/apex/vendor/apex/opt_strategies.py:221-223` |

## [APEX O7: skew risk reversal](../../strategies/apex/apex-o7-skew-risk-reversal.md)

| Rule | Read from |
|---|---|
| Entry: Core: QQQ at 1×. | `sleeves/apex/apex_options.py:81-82` |
| Entry: At a month's first session when the trend score is ≥ 5 of 6 and the HAR volatility is under 25% (none held): sells the 25-delta put and buys the 25-delta call, 2 × NAV / spot shares each, the next monthly expiry ≥ 15 days out. | `sleeves/apex/vendor/apex/opt_strategies.py:309-321` |
| Exit: Closed when the trend score drops below 4 of 6; otherwise held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:312-314` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Rule on a QQQ core | `sleeves/apex/apex_options.py:333-334`<br>`sleeves/apex/vendor/apex/opt_strategies.py:305-307` |

## [APEX O8: FEAR put spread](../../strategies/apex/apex-o8-fear-put-spread.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ. | `sleeves/apex/apex_options.py:76-80`<br>`sleeves/apex/feedlib/apex.py:311-314` |
| Entry: FEAR: at a month's first session when 30-day implied vol is at or above its 252-day 80th percentile and the trend score is ≤ 2 of 6, sells the 90% put and buys the 80% put, the expiry nearest 61 days (≥ 45), NAV / spot shares. | `sleeves/apex/vendor/apex/opt_strategies.py:173-183` |
| Exit: Held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:173-183` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Overlay on the APEX-50F core | `sleeves/apex/apex_options.py:325-326`<br>`sleeves/apex/vendor/apex/opt_strategies.py:186-194` |

## [APEX O9: OMEGA](../../strategies/apex/apex-o9-omega.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ. | `sleeves/apex/apex_options.py:76-80`<br>`sleeves/apex/feedlib/apex.py:311-314` |
| Entry: PHOENIX: when the Nasdaq-100 is ≥ 15% under its 252-day high, 30-day implied vol (VXN) is at or above its 252-day 80th percentile and the level is at or above the prior 10-day high, buys at-the-money calls, the expiry nearest 91 days (≥ 60), premium 5% of NAV; one position at a time. | `sleeves/apex/vendor/apex/opt_strategies.py:139-153`<br>`sleeves/apex/vendor/apex/opt_strategies.py:48-52` |
| Entry: CHOP: at a month's first session when the trend score is 2, 3 or 4 of 6 votes, sells the call and put 1 σ√T out and buys wings 2 σ√T out (an iron condor), NAV / spot shares a leg, the next monthly expiry ≥ 15 days out. | `sleeves/apex/vendor/apex/opt_strategies.py:156-170` |
| Entry: FEAR: at a month's first session when 30-day implied vol is at or above its 252-day 80th percentile and the trend score is ≤ 2 of 6, sells the 90% put and buys the 80% put, the expiry nearest 61 days (≥ 45), NAV / spot shares. | `sleeves/apex/vendor/apex/opt_strategies.py:173-183` |
| Exit: PHOENIX calls are sold with 30 days or less to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:141-144` |
| Exit: The CHOP condor and FEAR spread are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:156-183` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Each overlay sizes on the whole book's NAV. | `sleeves/apex/apex_options.py:327-328`<br>`sleeves/apex/vendor/apex/opt_strategies.py:186-194` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |

## [APEX O10: LEAPS + Variance Value](../../strategies/apex/apex-o10-leaps-vv.md)

| Rule | Read from |
|---|---|
| Entry: L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)). | `sleeves/apex/vendor/apex/opt_strategies.py:43-47`<br>`sleeves/apex/vendor/apex/opt_strategies.py:96`<br>`sleeves/apex/feedlib/apex.py:279`<br>`sleeves/apex/feedlib/apex.py:322`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109` |
| Entry: Calls: the expiry nearest 365 days (≥ 300), the strike for 0.80 delta. | `sleeves/apex/vendor/apex/opt_strategies.py:244-245` |
| Entry: Calls = L* × NAV / (delta × spot), at most 99.5% of NAV in premium; adjusted by whole contracts when 0.5 off. | `sleeves/apex/vendor/apex/opt_strategies.py:243-256` |
| Entry: Variance Value, at a month's first session with none held, on the next monthly expiry ≥ 15 days out: at-the-money implied vol / the HAR forecast ≥ 1.25 sells the at-the-money straddle and buys wings 1.5 σ√T out (an iron fly), NAV / spot shares a leg; ≤ 0.95 buys the at-the-money straddle with 2% of NAV. | `sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Exit: L* ≤ 0 sells the calls; rolled under 183 days or outside 0.60-0.95 delta; the Variance Value structures are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:232-242`<br>`sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Sizing: Core: T-bills (BIL). | `sleeves/apex/apex_options.py:89` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| O2b plus the Variance Value rule | `sleeves/apex/apex_options.py:317-318`<br>`sleeves/apex/vendor/apex/opt_strategies.py:259-267` |

## [APEX O11: APEX + Variance Value](../../strategies/apex/apex-o11-apex-vv.md)

| Rule | Read from |
|---|---|
| Entry: Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days. | `sleeves/femto/vendor/aurelia/features.py:11-25`<br>`sleeves/femto/vendor/aurelia/features.py:40-80`<br>`sleeves/apex/vendor/apex/strategies.py:41-43` |
| Entry: Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ. | `sleeves/apex/apex_options.py:76-80`<br>`sleeves/apex/feedlib/apex.py:311-314` |
| Entry: Variance Value, at a month's first session with none held, on the next monthly expiry ≥ 15 days out: at-the-money implied vol / the HAR forecast ≥ 1.25 sells the at-the-money straddle and buys wings 1.5 σ√T out (an iron fly), NAV / spot shares a leg; ≤ 0.95 buys the at-the-money straddle with 2% of NAV. | `sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Exit: Option structures are held to expiry. | `sleeves/apex/vendor/apex/opt_strategies.py:156-170`<br>`sleeves/apex/vendor/apex/opt_strategies.py:198-218` |
| Exit: No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL). | `sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/apex.py:136-139` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Overlay on the APEX-50F core | `sleeves/apex/apex_options.py:329-330`<br>`sleeves/apex/vendor/apex/opt_strategies.py:186-194` |

## [APEX O12: hybrid LEAPS + QQQ trim](../../strategies/apex/apex-o12-hybrid-leaps.md)

| Rule | Read from |
|---|---|
| Entry: L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)). | `sleeves/apex/vendor/apex/opt_strategies.py:43-47`<br>`sleeves/apex/vendor/apex/opt_strategies.py:96`<br>`sleeves/apex/feedlib/apex.py:279`<br>`sleeves/apex/feedlib/apex.py:322`<br>`sleeves/apex/vendor/apex/strategies.py:46-48`<br>`sleeves/apex/vendor/apex/strategies.py:109` |
| Entry: Calls: the expiry nearest 365 days (≥ 300), the strike for 0.80 delta. | `sleeves/apex/vendor/apex/opt_strategies.py:352-353` |
| Entry: Calls for 75% of L*: 0.75 × L* × NAV / (delta × spot), at most 99.5% of NAV in premium, opened when none are held and L* > 0; after an L* ≤ 0 exit, only at a month's first session. | `sleeves/apex/vendor/apex/opt_strategies.py:344-347`<br>`sleeves/apex/vendor/apex/opt_strategies.py:351-357` |
| Entry: Trim: QQQ shares (long or short) for L* less the calls' delta exposure, traded on a change of 0.20 or more, or to 0. | `sleeves/apex/vendor/apex/opt_strategies.py:358-363`<br>`sleeves/apex/apex_options.py:91-105`<br>`sleeves/apex/apex_options.py:216-217` |
| Exit: L* ≤ 0 sells the calls; they roll under 183 days or outside 0.60-0.95 delta. | `sleeves/apex/vendor/apex/opt_strategies.py:340-350` |
| Sizing: Core: T-bills (BIL). | `sleeves/apex/apex_options.py:89` |
| Sizing: Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits. | `sleeves/apex/apex.py:79-80`<br>`sleeves/apex/feedlib/apex_book.py:46-81`<br>`sleeves/apex/feedlib/apex.py:233-256`<br>`sleeves/apex/apex.py:433-500`<br>`sleeves/apex/apex_options.py:159-170` |
| Sizing: The core trades market-on-close on the equity less the options' value; a $1,000,000 book. | `sleeves/apex/apex_options.py:94-105`<br>`sleeves/apex/apex.py:372-391`<br>`sleeves/apex/apex.py:519` |
| Data: Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. | `sleeves/apex/feedlib/apex.py:34-36`<br>`sleeves/apex/vendor/apex/series.py:17-38`<br>`sleeves/apex/feedlib/apex.py:157-185`<br>`sleeves/apex/apex.py:682` |
| Data: The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend. | `sleeves/apex/feedlib/apex.py:206-209`<br>`sleeves/apex/feedlib/apex.py:259-276`<br>`sleeves/apex/feedlib/apex.py:290-325`<br>`sleeves/apex/vendor/apex/surface.py:55-98`<br>`sleeves/apex/vendor/apex/sim.py:79-90` |
| Options study: pre-registered, on QQQ with the VXN-calibrated surface | `sleeves/apex/apex_options.py:3-6` |
| Named divergence: the futures trim as QQQ shares | `sleeves/apex/apex_options.py:46` |
