# Call-to-put reversal (SPY)

Before noon, after SPY tags one trigger and closes back through the prior close, trades the run to the opposite trigger on toward 38.2%.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), Call to Put reversal; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1m |
| **Universe** | SPY |
| **Style** | Intraday reversal |
| **Status** | waiting |

## Entry

- ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0.
- Before 12:00 ET: the high reaches +0.236, then a close below the prior close, then the low reaches -0.236: short at min(open, trigger); the mirror buys.

## Exit

- Target ±0.382; stop on a 10-minute close back beyond the prior close.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
