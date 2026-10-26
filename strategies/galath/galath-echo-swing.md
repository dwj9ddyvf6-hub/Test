# Echo swing

Buys a stock when @EchoAnalysis posts that he bought it, or adds when he adds at support, with a 2% stop and a 5% target.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | Echo (@EchoAnalysis on X); the Galath / GrokBot desk's Echo sidecar |
| **Asset** | US equities |
| **Timeframe** | Posts (3-minute sweeps) · 1d |
| **Universe** | Names in @EchoAnalysis's buy posts |
| **Style** | Social signal swing |
| **Status** | waiting |

## Entry

- Every 3 minutes the account's RSS mirrors are read; a new post saying he bought, or a starter, is a BUY of the named ticker; "I added" is an ADD; recaps, reposts, old fills, plans and "never bought" are skipped.
- BUY: 09:35-15:45 ET on a weekday, not held or bought that day, not a chase (5-day return ≤ 8% and ≤ 4% above the 21-day EMA), under 6 swings, 10 open names and 16 new buys a day.
- ADD: only at support (-5% to +2% of the 21-day EMA, or a 5-day return ≤ 0).
- Marketable order at the live price; a post read outside those hours, or in the first sweep, is not traded.

## Exit

- Bracket: stop 2% under the price, target +5%, engine-held.
- Trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI ≥ 68 with a daily bearish divergence after +80%.
- One add when price is back within 2% of the 50- or 200-day EMA after 5 of the prior 16 closes below it.
- A position worth under $75 is sold.

## Sizing

- 1.5% of equity at risk to the 2% stop, capped at 8% of equity (so 8%); whole shares.

## Data

- @EchoAnalysis posts from Nitter and xcancel RSS mirrors; daily bars; live quotes.

## Code

- **Master desk**: `sleeves/galath/galath.py`, `sleeves/galath/echo.py`, `sleeves/galath/paper.py`, `sleeves/galath/wire.py`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)

## Notes

- The swing manager's other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them.
- The +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share.
