# Bilbo Golden Gate (SPY)

Trades SPY's first touch of its daily Golden Gate when the hourly Phase Oscillator is in its extreme zone and rising, targeting 61.8%.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), Bilbo Golden Gate; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1m · 1h Phase Oscillator |
| **Universe** | SPY |
| **Style** | Intraday ATR levels |
| **Status** | waiting |

## Entry

- ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0.
- The first 1-minute bar to reach ±0.382, when the session opened short of it, at max(open, level).
- Filter: the last completed hourly Phase Oscillator above 61.8 and rising (short: below -61.8 and falling).

## Exit

- Target ±0.618; stop on a 10-minute close back beyond ±0.236.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
