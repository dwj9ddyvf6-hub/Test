# Scanner book swing

Buys the Signal Prism scan's best S/A-grade events at support in a turning sector, on the next-support plan.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | Galath / GrokBot desk, the scanner book (desk-scan + buy-desk) |
| **Asset** | US equities |
| **Timeframe** | 1d · 5m session tape |
| **Universe** | 411-stock Galath universe (Signal Prism US 413 without its two crypto pairs) |
| **Style** | Structural swing |
| **Status** | waiting |

## Entry

- Scan: the nine Signal Prism engines (Vector, Meridian, Cascade, Threshold, Fissure, Dread, Reverb, Zenith, Strata) on the last completed session, SPY the bench; once a session.
- Candidate: an S/A-grade or first-defense event, not contradicted, developing or expired; the selection read must say BUY (a coil, a washout, or a held level with two confirmations) and the name needs a washout, a coil, a bottom-screen buy or an RSI/MACD curl.
- Sector: the name's sector ETF must be turning against SPY; waterfall, trend and trough sectors and names without a sector ETF are skipped, cyclicals wait in a risk-off tape.
- Book: the Prism candidates (S tier and curl first), then the bottom screen's buys, up to 20, on the next-support plan; dropped when RSI ≥ 50 off support.
- Rebuilt every 10 minutes; outside 11:25-11:55 and 14:10-14:50 ET each name is re-read on the 5-minute session tape: dropped when 3% through the buy, at its stop or within 1% of its target, and the plan rebased to the last print.
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

- Split-adjusted daily bars (502 sessions), extended-hours 5-minute bars with the forming bar, live quotes.

## Code

- **Master desk**: `sleeves/galath/galath.py`, `sleeves/galath/book.py`, `sleeves/galath/prism.py`, `sleeves/galath/levels.py`, `sleeves/galath/paper.py`, `sleeves/galath/wire.py`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)

## Notes

- The swing manager's other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them.
- At this catalog's pin the +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share; master-desk commit 6d6ae54e (2026-10-26) makes every trim fire once per position.
- Caps count this sleeve's own book only.
