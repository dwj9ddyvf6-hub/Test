# Ten-minute compression release (SPY)

When a 10-minute squeeze releases, enters the next minute in the EMA21/48 direction with the stop at the squeeze's far side, flat by the close.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study, on Saty's compression |
| **Asset** | US ETF |
| **Timeframe** | 10m |
| **Universe** | SPY |
| **Style** | Intraday volatility breakout |
| **Status** | waiting |

## Entry

- Saty's compression on 10-minute candles; the first candle out of a squeeze of ≥ N candles: long when EMA(21) is above EMA(48), short below; enters at the next 1-minute bar's open.

## Exit

- Stop at the squeeze's low (long) or high (short), by touch.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Variants

| Lane | Squeeze ≥ N candles |
|---|---|
| Long | 3 |
| Short | 18 |

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
