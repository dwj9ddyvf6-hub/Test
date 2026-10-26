# PEAD price surprise

Buys the top fifth of earnings price surprises two sessions after the report, held 1, 5, 10 and 20 sessions.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed research studies, forward-tested on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d (event) |
| **Universe** | Nasdaq earnings-calendar names |
| **Style** | Earnings drift |
| **Status** | live |

## Entry

- Surprise S: the adjusted close the session after the event over the close the session before, less SPY's same return; the event date from Nasdaq's earnings calendar.
- Cohort: S above the 80th percentile of the previous calendar quarter's surprises; bought at the open two sessions after the event.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Four tranches, out market-on-close after 1, 5, 10 and 20 sessions (the entry session counted).

## Sizing

- $100,000 / 1,500 per tranche (fractional shares).

## Data

- Nasdaq earnings calendar, NASDAQ Trader listings, daily adjusted bars of the names and SPY.

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/events.py`, `sleeves/killed/common.py`, `sleeves/killed/feedlib/killed_data.py`
