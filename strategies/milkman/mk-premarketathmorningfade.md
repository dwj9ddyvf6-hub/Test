# Premarket all-time-high fade (SPY)

Shorts SPY's open when its premarket high tops every prior session's high, unless the 10-minute Phase Oscillator is already overbought, and covers at noon.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), premarket ATH fade draft; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1m · 10m Phase Oscillator |
| **Universe** | SPY |
| **Style** | Opening fade |
| **Status** | waiting |

## Entry

- The 04:00-09:29 ET high above the highest high of every prior session; the 10-minute Phase Oscillator at 09:30 under 61.8; shorts the open.

## Exit

- Out at the last bar before 12:00 ET; no stop.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.
- The all-time-high reference: Yahoo daily highs plus the clock-hour and 1-minute highs it serves.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
