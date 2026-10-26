# Weekly 8/20/50 pullback

Buys an ETF whose completed week pulled back to its 8-week EMA inside an 8 > 20 > 50 uptrend; a weekly-ATR stop, a quarter off at one ATR, the rest out five weeks later.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk: the weekly 8/20/50 pullback, ported line for line; a recorder made a book by the owner's D32 |
| **Asset** | US ETFs |
| **Timeframe** | 1w signal · 1d management |
| **Universe** | 19 ETFs (the funds of the public Portfolio T page) |
| **Style** | Trend pullback |
| **Status** | waiting |

## Entry

- Signal, on a completed week (its last session a Friday, else once the next week begins): EMA8 > EMA20 > EMA50 of the weekly closes, the close above EMA50, the week's low at or under EMA8 and the close above the low; at least 60 weeks of history.
- Levels: entry at the week's close, stop = entry - weekly ATR(5), target = entry + ATR, deadline = the last session of the fifth week after.
- Decided after that week's close: at most 10 names held, the week's signals by RSI(14) ascending, then symbol; bought at the book's first pass of the next session, skipped when the price is already at or under the stop.

## Exit

- Stop at entry - weekly ATR(5), held by the engine on the live price.
- A quarter sold the first time the live price reaches the target; the rest by a market-on-close order on the deadline session.

## Sizing

- A tenth of equity a name, never more than the cash, divided by 1.001 for the source's cost; $100,000 book.

## Data

- Yahoo daily bars (1,600 sessions), adjusted as Midna's live board adjusts them (OHLC × adjclose / close), built into weeks.

## Code

- **Master desk**: `sleeves/midna/monitor/midna_books.py`, `sleeves/midna/monitor/midna_mon.py`, `sleeves/galath/monitor.py`
- **Midna's TypeScript source**: `sleeves/midna/vendor/midna_mon/src/lib/felipe/pullback.ts`
- **Rule lines**: [docs/verify/midna.md](../../docs/verify/midna.md)

## Notes

- Midna's own study left this book unfunded (a performance verdict); D32 funds it to forward-test it.
- Her file's QLD trend book is a separate rule with no row of its own; it is not converted.
- A recorder until the owner's ruling D32 (2026-10-26) funded it as a paper book; its first live signal is pending.
