# Top-decile SUE drift

Buys SCOPE stocks whose standardized earnings surprise ranks in the top tenth of the last 91 days' at the first open after the report and holds them 20 sessions, in equal weight.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 parallel lab registration PEAD_SUE_20D_1_0_0, on Nasdaq's public earnings calendar |
| **Asset** | US equities |
| **Timeframe** | 1d (20-session hold) |
| **Universe** | SCOPE stocks (ETF basket excluded) |
| **Style** | Earnings drift |
| **Status** | live |

## Entry

- Events: Nasdaq's earnings calendar for the SCOPE names outside the ETF basket (reported EPS, consensus, release time), refreshed at each session's open.
- Trigger: SUE = (actual - consensus) / the sample SD of the name's 8 prior surprises, at or above the 90th percentile of the universe's SUEs public within the trailing 91 days (at least 10).
- Entry: the open of the first session that can trade the report (a pre-market report that day, otherwise the next session); one event per name at a time.
- Book: every active event at 1/N of the book, re-targeted at each session's first pass.

## Exit

- Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1).

## Sizing

- $100,000 book in equal calendar-time weights.

## Data

- Nasdaq's archived earnings calendar pages and live quotes.

## Code

- **Master desk**: `sleeves/griffith/event_research.py`, `sleeves/griffith/feedlib/griffith_earnings.py`
