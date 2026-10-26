# Three-minute compression drift (SPY)

After a 3-minute squeeze of 8+ candles that drifts one way, enters on the first candle out of it that closes past the squeeze's late midpoint, with a 1-ATR stop.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study, on Saty's compression |
| **Asset** | US ETF |
| **Timeframe** | 3m |
| **Universe** | SPY |
| **Style** | Intraday volatility breakout |
| **Status** | waiting |

## Entry

- A squeeze of ≥ 8 three-minute candles in one session (one-candle breaks allowed); drift up = its later candles' high ≥ the first 5's high + 0.5 ATR and their low ≥ the first 5's low - 0.25 ATR (down mirrored).
- The first candle out of the squeeze closing beyond the last 5 candles' midpoint the drift's way; enters at the next 1-minute bar's open when the 3-minute ATR is ≥ 0.045% of price.

## Exit

- Stop 1 × the 3-minute ATR from entry, by touch.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
