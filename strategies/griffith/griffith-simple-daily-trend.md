# Simple daily trend cohorts

Each session, every SCOPE name closing above its 200-day average with the 50-day above the 200-day opens a 20-session cohort in a fixed slot.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 strategy tournament (SIMPLE_TREND_1_0_0) |
| **Asset** | US equities |
| **Timeframe** | 1d (20-session cohorts) |
| **Universe** | SCOPE universe: 550 US names |
| **Style** | Trend |
| **Status** | blocked |

## Entry

- Observation: each session, every name with close > SMA 200 and SMA 50 > SMA 200 on its last completed bar (253 bars needed).
- Entry: at the session's first pass with a live quote, a fixed slot of $100,000 / 550 (about $182) as a marketable limit good for an hour; one cohort per name, none while it is held or working.

## Exit

- Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1).

## Sizing

- A fixed $182 slot per cohort.

## Data

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys.

## Code

- **Master desk**: `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/strategy_tournament.py`, `sleeves/griffith/feedlib/griffith.py`
