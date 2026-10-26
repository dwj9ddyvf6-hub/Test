# Gap-up pre-noon continuation (SPY)

When SPY opens above the prior close and trades 1% above it before noon, buys the next bar and holds to the close.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1m |
| **Universe** | SPY |
| **Style** | Intraday momentum |
| **Status** | waiting |

## Entry

- The open above the prior close and a high ≥ prior close × 1.01 before 12:00 ET; buys the next 1-minute bar's open.

## Exit

- Out at the close; no stop or target.

## Sizing

- Each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close.
- $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
