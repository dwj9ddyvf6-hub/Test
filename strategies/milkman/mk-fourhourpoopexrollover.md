# Four-hour Phase Oscillator OpEx rollover (SPY)

In the week after monthly options expiry, shorts SPY when its 4-hour Phase Oscillator rolls over from 80 while price is stretched above last week's or month's close, and holds 10 sessions.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), 4h PO × OpEx; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 4h |
| **Universe** | SPY |
| **Style** | Oscillator reversal |
| **Status** | waiting |

## Entry

- A 4-hour candle's Phase Oscillator under 80 after one at ≥ 80, the first per day, on the session on or after the third Friday or the 5 after it.
- Stretch: the 4-hour close ≥ 0.618 ATR above the prior completed week's or month's close (the greater; their ATR14).
- Shorts at the market at the next pass (at the next regular open when the candle closes outside the session).

## Exit

- At the close of the 10th full session after the signal day, market-on-close.

## Sizing

- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
