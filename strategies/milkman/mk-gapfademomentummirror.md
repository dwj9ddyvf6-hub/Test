# Gap fade / momentum mirror (SPY)

Trades SPY's opening gap by size: fades it toward the prior close, or rides it half an ATR, by the lane's gap bucket.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), gap midpoint fills; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1d gap · 1m exits |
| **Universe** | SPY |
| **Style** | Opening gap |
| **Status** | waiting |

## Entry

- Gap = the open against the prior close. In the lane's bucket: the fade trades toward the prior close (stop 0.5 ATR beyond the open); the mirror trades the gap's way (target 0.5 ATR, stop the prior close); at the open.

## Exit

- Target and stop by touch.
- Otherwise out at the close.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Variants

| Lane | Gap | Trades |
|---|---|---|
| Long | 0-0.1% | gap down: fade long to the prior close; gap up: mirror long, +0.5 ATR |
| Short | 0.25-0.5% | gap up: fade short to the prior close; gap down: mirror short, -0.5 ATR |

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
