# Tensor ratio-chart signals

Runs the weekly Tensor engine on each stock's price relative to SPY and buys the stock on a Cyan or Green ratio fire, holding 252 sessions.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Galath research lab, TENSOR_CREATIVE ratio-chart study |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | 1,822 US stocks (the store_v1 survivors) |
| **Style** | Relative strength (Tensor) |
| **Status** | live |

## Entry

- Ratio bars: the stock's adjusted open, high, low and close over SPY's (high = the largest of the four ratios, low = the smallest), the stock's volume, in Friday weeks.
- A closed weekly ratio bar with a buy-cyan or buy-green marker; 20-day dollar volume ≥ $100,000.
- Bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask.

## Exit

- 252 sessions after the fire week, sold market-on-close on that session.

## Sizing

- $1,000 a fire; a $3,000,000 book.

## Data

- Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes).

## Code

- **Master desk**: `sleeves/milkman/galath.py`, `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`
