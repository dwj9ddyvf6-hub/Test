# Opening range breakout (SPY)

Trades the first 5-minute close outside SPY's opening range, with the stop at the range's midpoint, flat by the close.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1m (5-minute closes) |
| **Universe** | SPY |
| **Style** | Intraday breakout |
| **Status** | waiting |

## Entry

- Range: the first 5 (long lane) or 10 (short lane) minutes' high and low; the first 5-minute close beyond it sets the side; enters at that close.
- Long lane also needs the last 10-minute EMA(8) above EMA(21) and the close above the session VWAP.

## Exit

- Stop at the range's midpoint, by touch.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Variants

| Lane | Range | Filter |
|---|---|---|
| Long | 5 minutes | 10-minute EMA8 > EMA21, close above VWAP |
| Short | 10 minutes | none |

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
