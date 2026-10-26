# Vomy / iVomy (SPY)

Buys a 10-minute pullback to EMA13 within 3 candles of an EMA8/13 bull flip (iVomy shorts the bear mirror), with the stop at EMA13.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 10m |
| **Universe** | SPY |
| **Style** | Intraday pullback |
| **Status** | 2 waiting |

## Entry

- 10-minute candles: long when EMA(8) is above EMA(13), the bull flip came within the last 3 candles, the candle's low touched EMA(13) and it closed above EMA(8); short mirrored; at the candle's close.

## Exit

- Stop at that candle's EMA(13), on a 10-minute close beyond it.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`

## Notes

- Since master-desk commit 78fd79e5 (2026-10-26, after this catalog's pin) each side runs as its own book: `mk_vomyivomy` long, `mk_vomyivomy_short` short.
