# Naive 20-day breakout

Buys a strict new 20-day closing high on 41 names and holds it 20 sessions.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed research studies, forward-tested on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 41-name old-desk basket |
| **Style** | Breakout |
| **Status** | live |

## Entry

- A close above the highest close of the prior 20 sessions (a tie is not a breakout) on the completed session; bought at the next session's first pass; a signal during a hold is skipped.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Sold market-on-close 20 sessions after the signal session.

## Sizing

- $100,000 / 41 per position (fractional shares long; shorts in whole shares, at least 1).

## Data

- Split-adjusted daily bars (60).

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/daily.py`, `sleeves/killed/common.py`
