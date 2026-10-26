# Verification: Sable

Each card rule was read from the code at these lines. `master-desk` paths are at commit `843ccb53ad15` of the
master desk (branch master-desk); every other path is in this repository.

## [Location-first repair](../../strategies/sable/sable-location-first.md)

| Rule | Read from |
|---|---|
| Entry: Funnel: every stock's 6 months of daily closes; the 48 best under-50-day reads and the 48 best leaders-rest reads (plus SPY, QQQ) are re-read on 400 days of daily OHLC with today's forming bar and the live price. | `sleeves/sable/sable.py:142-160`<br>`sleeves/sable/sable.py:224-243`<br>`sleeves/sable/sable.py:245-283`<br>`sleeves/sable/location_first.py:18`<br>`sleeves/sable/location_first.py:773-786` |
| Entry: Out: price above the 50-day EMA, RSI(14) > 52, the 50-day EMA down > 1.5% over 10 sessions, under $3 with < $2M 20-day dollar volume, or earnings from 12 h before to 48 h ahead. | `sleeves/sable/location_first.py:326-330`<br>`sleeves/sable/location_first.py:338-347`<br>`sleeves/sable/location_first.py:351-352`<br>`sleeves/sable/location_first.py:357-372`<br>`sleeves/sable/sable.py:328-337`<br>`sleeves/sable/runtime.py:218-219` |
| Entry: Shelf: the 21-day EMA within 2%, the 12-day low within 4%, or a 50 / 61.8 / 78.6% retrace of the 60-day swing within 2.5%; the best by weight, confluence and distance; price ≤ 3% above it. | `sleeves/sable/location_first.py:25-31`<br>`sleeves/sable/location_first.py:154-170`<br>`sleeves/sable/location_first.py:179-210`<br>`sleeves/sable/location_first.py:316-325`<br>`sleeves/sable/location_first.py:350` |
| Entry: Repair: RSI 28-52; the ATR-scaled MACD(12, 26, 9) histogram up in 2 of the last 3 sessions with a net lift; ≥ 8% under the 20-day high; today's low above the prior 11 sessions' low × 1.001; ≥ 20 bars with a real range. | `sleeves/sable/location_first.py:303-314`<br>`sleeves/sable/location_first.py:331-337`<br>`sleeves/sable/location_first.py:348`<br>`sleeves/sable/location_first.py:355`<br>`sleeves/sable/location_first.py:387-389` |
| Entry: Grade: S_COIL (on the 21-day, RSI 40-52, MACD up all 3 steps from below zero) at score ≥ 80, or A_WASHOUT at ≥ 68, is a SETUP; the 6 best-scoring SETUP stocks are the hands. | `sleeves/sable/location_first.py:225-240`<br>`sleeves/sable/location_first.py:390-402`<br>`sleeves/sable/location_first.py:430-444`<br>`sleeves/sable/location_first.py:527-553`<br>`sleeves/sable/location_first.py:448-458` |
| Entry: Buys each SETUP hand not held, not sold in the last 8 hours, while under 6 positions (working buys count), in the regular session; free slots fill in the catalog's order. | `sleeves/sable/sable.py:398-412`<br>`sleeves/sable/runtime.py:314-362`<br>`sleeves/sable/runtime.py:400-427`<br>`sleeves/sable/runtime.py:546-576` |
| Entry: Orders: marketable limits (1% through the quote), good for an hour; a working buy is cancelled once its name leaves the hands. | `sleeves/sable/sable.py:417-431`<br>master-desk `desk/contract.py:62-68`<br>`sleeves/sable/runtime.py:474-493` |
| Exit: Stop at fill - 1.6 × ATR, target at fill + 2.8 × ATR (daily ATR(14), at least 1.5% of the fill; both widen if ATR grows), checked on the quote every 5 minutes. | `sleeves/sable/runtime.py:42-66`<br>`sleeves/sable/runtime.py:453-472`<br>`sleeves/sable/sable.py:371-376`<br>`sleeves/sable/sable.py:168` |
| Exit: Time stop: after 15 days if the position is not in profit. | `sleeves/sable/runtime.py:96-102`<br>`sleeves/sable/runtime.py:509-515` |
| Sizing: min(0.5% of equity / (1.6 × ATR), 15% of equity, 98% of cash) in whole shares; a $100,000 book. | `sleeves/sable/runtime.py:32-38`<br>`sleeves/sable/runtime.py:81-93`<br>`sleeves/sable/runtime.py:306-312`<br>`sleeves/sable/sable.py:169` |
| Data: Yahoo spark daily closes (6 months); split-adjusted daily bars with today's forming bar; live quotes; the Nasdaq earnings calendar. | `sleeves/sable/sable.py:166-176`<br>`sleeves/sable/sable.py:186-194`<br>`sleeves/sable/sable.py:576-594` |
| ETFs never bought | `sleeves/sable/location_first.py:438-439`<br>`sleeves/sable/runtime.py:206-207` |
| Removed gates: running state, no Edge, no Tensor sell | `sleeves/sable/runtime.py:34`<br>`sleeves/sable/sable.py:385-388`<br>`sleeves/sable/sable.py:393-394` |
| Breakeven step undone by the floor | `sleeves/sable/runtime.py:105-114`<br>`sleeves/sable/runtime.py:453-472` |
| Version | `sleeves/sable/location_first.py:15` |
| Universe | `sleeves/sable/sable.py:79-103` |
| No leaders-rest fallback | `sleeves/sable/sable.py:325-326` |

## [Support scanner (5-minute)](../../strategies/sable/sable-support-scanner.md)

| Rule | Read from |
|---|---|
| Entry: Deep list: held names, the last scan's buy-side names, SPY / QQQ / IWM, then the best spark screen scores (near the 52-week or day low, down on the day) up to 36 names. | `sleeves/sable/desk_scanner.py:18-19`<br>`sleeves/sable/desk_scanner.py:277-325`<br>`sleeves/sable/sable.py:472-491`<br>`sleeves/sable/sable.py:499-505` |
| Entry: Each gets a quote from the last 5 sessions' completed regular-hours 5-minute bars: support = the 64-bar low, ATR(14), RSI(14), the 12 / 26 EMA gap, VWAP; with the spark's 52-week range. | `sleeves/sable/desk_scanner.py:157-273`<br>`sleeves/sable/sable.py:506-527`<br>`sleeves/sable/sable.py:546-557` |
| Entry: Buy: a SETUP with price ≥ 99.5% of support and ≤ 1.6 ATR above it, RSI 38-68, EMA gap ≥ -0.15, below 88% of the 52-week range; stocks only. | `sleeves/sable/desk_scanner.py:398-419`<br>`sleeves/sable/desk_scanner.py:431-450`<br>`sleeves/sable/desk_scanner.py:461-501`<br>`sleeves/sable/runtime.py:173-195`<br>`sleeves/sable/runtime.py:220-226` |
| Entry: Hands: the first 6 buy-side rows, SETUPs first by score (improving momentum, a tight range, volume and the lowest 30% of the 52-week range add points). | `sleeves/sable/desk_scanner.py:492-494`<br>`sleeves/sable/desk_scanner.py:533-564` |
| Entry: Buys each SETUP hand not held, not sold in the last 8 hours, while under 6 positions (working buys count), in the regular session; free slots fill in the catalog's order. | `sleeves/sable/sable.py:398-412`<br>`sleeves/sable/runtime.py:314-362`<br>`sleeves/sable/runtime.py:400-427`<br>`sleeves/sable/runtime.py:546-576` |
| Entry: Orders: marketable limits (1% through the quote), good for an hour; a working buy is cancelled once its name leaves the hands. | `sleeves/sable/sable.py:417-431`<br>master-desk `desk/contract.py:62-68`<br>`sleeves/sable/runtime.py:474-493` |
| Exit: Stop at fill - 1.6 × ATR, target at fill + 2.8 × ATR (5-minute ATR(14), at least 1.5% of the fill: -2.4% / +4.2% at that floor), checked every 5 minutes. | `sleeves/sable/runtime.py:42-66`<br>`sleeves/sable/runtime.py:453-472`<br>`sleeves/sable/sable.py:371-376`<br>`sleeves/sable/sable.py:425`<br>`sleeves/sable/sable.py:455` |
| Exit: Time stop: after 15 days if the position is not in profit. | `sleeves/sable/runtime.py:96-102`<br>`sleeves/sable/runtime.py:509-515` |
| Sizing: min(0.5% of equity / (1.6 × ATR), 15% of equity, 98% of cash) in whole shares; a $100,000 book. | `sleeves/sable/runtime.py:32-38`<br>`sleeves/sable/runtime.py:81-93`<br>`sleeves/sable/runtime.py:306-312`<br>`sleeves/sable/sable.py:169` |
| Data: Yahoo spark quotes (5-minute closes, day and 52-week range) and Yahoo 5-minute bars (last 5 sessions). | `sleeves/sable/sable.py:454-458`<br>`sleeves/sable/sable.py:576-583` |
| No earnings flag | `sleeves/sable/sable.py:469-470`<br>`sleeves/sable/desk_scanner.py:241-273` |
| No Tensor reads | `sleeves/sable/sable.py:528`<br>`sleeves/sable/desk_scanner.py:421-423` |
| Breakeven step undone by the floor | `sleeves/sable/runtime.py:105-114`<br>`sleeves/sable/runtime.py:453-472` |
| Universe | `sleeves/sable/sable.py:79-103` |
