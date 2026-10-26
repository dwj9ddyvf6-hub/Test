# Golden cross (SPY)

Holds SPY while its 50-day average is above the 200-day, and goes flat when it is below.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | QuantifiedStrat's golden cross, a killed study of the old Alpaca swing desk, forward-tested |
| **Asset** | US ETF |
| **Timeframe** | 1d |
| **Universe** | SPY |
| **Style** | Trend (moving-average cross) |
| **Status** | live |

## Entry

- Long when SPY's 50-day SMA is above its 200-day SMA on the last completed session (a tie keeps the state); bought at the next session's first pass.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Flat when the 50-day is below the 200-day: sold at the next pass.

## Sizing

- All of the sleeve's equity; a $100,000 book.

## Data

- SPY split-adjusted daily bars (320).

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/daily.py`, `sleeves/killed/common.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)
