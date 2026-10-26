# ATR level cascade (SPY)

Each time SPY first reaches one of its daily ATR levels, trades on toward the next level with the stop at the one before.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), SPX ATR cascade draft; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1m |
| **Universe** | SPY |
| **Style** | Intraday ATR levels |
| **Status** | waiting |

## Entry

- ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0.
- At the first 1-minute bar (not the session's first) that reaches each level from 0.236 to 1.0, either way: long above the prior close, short below, at max(open, level).

## Exit

- Target the next level out; stop the level before (the prior close for 0.236), by touch.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
