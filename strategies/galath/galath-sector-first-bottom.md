# Sector-first bottom

Buys a cheap, liquid stock basing under its long averages when its sector has turned against SPY, on the next-support plan.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | Galath / GrokBot desk, bottom screen v1.0 |
| **Asset** | US equities |
| **Timeframe** | 1d · 5m session tape |
| **Universe** | 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs) |
| **Style** | Bottom recovery |
| **Status** | waiting |

## Entry

- Bottom screen on the scan's daily bars: single names (no index products), ≥ $8, 20-day dollar volume ≥ $15M, no > 70% 60-day collapse.
- Points: quality (above 45% of the 200-day, no > 45% 60-day drop, ≥ $25M volume), cheap (18-55% off the 52-week high, 3-28% under the 200-day), sector (lagging SPY over 126 days, leading over 20; its ETF turning), structure (a contracting base, a spring), a selling climax, impulse (on the 21-day under the 50-day, the 21-day rising).
- BUY at ≥ 8 points with ≥ 2 turn points (structure, climax, impulse), cheap ≥ 1 and quality ≥ 2; under 9 points it waits while SPY is under its 200-day with a new 20-day low, or the tape is risk-off.
- Sector: waterfall, trend and trough sectors and names without a sector ETF are skipped; cyclicals wait in a risk-off tape.
- Book: up to 20 names by R, on the next-support plan; dropped when RSI ≥ 50 off support; the same 10-minute rebuild and session-tape re-read as the Scanner book swing.
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

- Split-adjusted daily bars (502 sessions) of the universe, SPY and 18 sector / regime ETFs; extended-hours 5-minute bars; live quotes.

## Code

- **Master desk**: `sleeves/galath/galath.py`, `sleeves/galath/book.py`, `sleeves/galath/levels.py`, `sleeves/galath/paper.py`, `sleeves/galath/wire.py`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)

## Notes

- The swing manager's other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them.
- At this catalog's pin the +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share; master-desk commit 6d6ae54e (2026-10-26) makes every trim fire once per position.
- Caps count this sleeve's own book only.
