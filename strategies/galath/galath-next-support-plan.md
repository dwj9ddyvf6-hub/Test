# Next-support plan

Each morning plans a buy at the next support under the last close for 30 names, and buys when the price trades within 3% of it.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | Galath / GrokBot desk, admit-ticker v1.1 |
| **Asset** | US equities |
| **Timeframe** | 1d (1-minute passes) |
| **Universe** | 30-name Galath folio list |
| **Style** | Support pullback |
| **Status** | live |

## Entry

- Plan (admit-ticker v1.1): buy at the highest support at most 1.5% above the last close (a 38.2-78.6% retrace of the 60-day swing, the 21-day EMA or the 12-day low) when it is under 99.8% of the close, else 1.5% under the close; stop 0.6% under the 12-day low, kept 2.5-3.5% under the buy; target 5R, at least +6% and at most +18%, moved to the 21- or 50-day EMA when one sits in that band.
- The plan is built once a session from the last completed bar.
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
