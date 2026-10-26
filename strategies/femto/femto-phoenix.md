# Phoenix breakout (red-day entry)

After a strict 20-day closing high in a weak tape (SPY down over 60 sessions), buys the first red day within five sessions at 15:55 ET and holds 20 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities and ETFs |
| **Timeframe** | 1d |
| **Universe** | 19 frozen names (with SPY and QQQ) |
| **Style** | Breakout pullback |
| **Status** | waiting |

## Entry

- Signal: a close above each of the prior 20 closes (ties do not count), volume > 0, SPY's 60-session return ≤ 0, ≥ 61 bars.
- Entry: the first red day (last < the day's open at 15:55 ET) in the 5 sessions after the signal, not on or before the last exit day.
- Entries pause after 3 disaster stops in the trailing 20 closed trades, until a ruling clears it.

## Exit

- Time stop at the close of the 20th session after entry; a 25% disaster stop below the fill.

## Sizing

- 1% of the book in notional (0.25% risk / 25% stop), at least 1 share; at most 8 positions and 25% of the book.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (400) and the 15:55 forming bar.

## Code

- **Master desk**: `sleeves/femto/phoenix.py`
- **Midna v3**: `sleeves/phoenix.py`. A wrapper only; the strategy file is not in this repo
