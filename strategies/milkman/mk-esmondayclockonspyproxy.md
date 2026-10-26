# ES Monday clock (SPY)

Times SPY from 06:00 to 16:00 ET each Monday, long and short; recorded only, as its entry falls outside the desk's trading session.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), ES Monday; the Milkman v2 study |
| **Asset** | US ETF |
| **Timeframe** | 1m (06:00-16:00 ET) |
| **Universe** | SPY |
| **Style** | Calendar |
| **Status** | off |

## Entry

- Each Monday with a full session: SPY at the open of the first 1-minute bar at or after 06:00 ET (within 5 minutes); a long and a short lane.

## Exit

- At the open of the first bar at or after 16:00 ET.

## Sizing

- Both legs are recorded as observations: the desk routes equities in the regular session only (the two lanes would net flat).

## Data

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Code

- **Master desk**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
