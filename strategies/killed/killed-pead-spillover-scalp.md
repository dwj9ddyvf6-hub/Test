# Earnings-day overnight scalp

On a stock's earnings day, buys the close when the day's return beats 0.16%, and sells the next open.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed research studies, forward-tested on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d (overnight) |
| **Universe** | Nasdaq earnings-calendar names |
| **Style** | Earnings overnight |
| **Status** | live |

## Entry

- The day's Nasdaq earnings-calendar names: live price / previous close - 1 - 0.15% > 0.01%; bought market-on-close.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Sold at the next session's open.

## Sizing

- $400 per trade ($100,000 / 250, fractional shares).

## Data

- Nasdaq earnings calendar, the previous session's daily close, live quotes (15:27-15:41 ET).

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/events.py`, `sleeves/killed/common.py`, `sleeves/killed/feedlib/killed_data.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)
