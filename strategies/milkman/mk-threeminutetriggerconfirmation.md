# Three-minute trigger confirmation (SPY)

When SPY opens inside its ±23.6% triggers, trades the first 3-minute close beyond a trigger toward 38.2%.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), 3-Minute Close; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 3m |
| **Universe** | SPY |
| **Style** | Intraday breakout |
| **Status** | waiting |

## Entry

- ATR levels: the prior regular session's close ± x × its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0.
- The open between the two ±0.236 triggers; the first 3-minute close beyond one, at that close (each side once).

## Exit

- Target ±0.382; stop on a 3-minute close back beyond the trigger.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
