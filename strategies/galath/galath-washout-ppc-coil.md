# Washout and PPC coil

Buys a stock washed out under its 50-day average on a Fib, its 12-day shelf or the 21-day EMA, or coiled tight just under the 50-day, on the next-support plan.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | Galath / GrokBot desk, washout v1.2 and the PPC coil |
| **Asset** | US equities |
| **Timeframe** | 1d (1-minute passes) |
| **Universe** | 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs) |
| **Style** | Washout pullback |
| **Status** | live |

## Entry

- Washout: under the 50-day EMA, RSI(14) < 50, the MACD histogram below zero (or rising and under 0.15), ≥ 8% under the 60-day high, ≤ 6% over the 12-day low unless on the 21-day, on a 50 / 61.8 / 78.6% retrace (within 2.5%), the 12-day shelf (≤ 4% over it) or the 21-day EMA (within 2%), relative volume < 2.2.
- PPC coil (tier S, ranked first): 0-3% under the 50-day EMA, within 2% of the 21-day, RSI 40-52, the histogram rising below zero, a 60-day range ≤ 25%, relative volume ≤ 1.1, within 2.5% of the 50 or 61.8% retrace, and a 78.6% shakeout that held in the last 6 sessions.
- Levels: the next-support plan (the Next-support plan card).
- Buys 09:35-15:45 ET on weekdays: not held, not traded that day, under 6 swings, 10 open names, 16 new buys a day and 2 of one story (semis, software, EV, space ...).
- At the live price, only within 3% of the plan's buy, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil); best tier and R first, at most 6 buys a pass; marketable order.

## Exit

- The plan's stop and target ride as an engine-held bracket.
- Trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI ≥ 68 with a daily bearish divergence after +80%.
- One add when price is back within 2% of the 50- or 200-day EMA after 5 of the prior 16 closes below it.
- A position worth under $75 is sold.

## Sizing

- 1.5% of equity at risk to the stop (2% of price without one), capped at 8% of equity; whole shares.

## Data

- Split-adjusted daily bars (300 sessions) with today's bar from the live quote; live quotes.

## Code

- **Master desk**: `sleeves/galath/galath.py`, `sleeves/galath/levels.py`, `sleeves/galath/paper.py`, `sleeves/galath/wire.py`

## Notes

- The swing manager's other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them.
- The +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share.
- Caps count this sleeve's own book only.
