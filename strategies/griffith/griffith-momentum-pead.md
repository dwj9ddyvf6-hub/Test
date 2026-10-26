# Momentum plus earnings drift

Buys a SCOPE stock that beats its consensus EPS while in a liquid momentum uptrend at the first open after the report and holds it 20 sessions, in equal weight.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 tournament registration MOMENTUM_PEAD_COMBINATION_1_0_0, on Nasdaq's public earnings calendar |
| **Asset** | US equities |
| **Timeframe** | 1d (20-session hold) |
| **Universe** | SCOPE stocks (ETF basket excluded) |
| **Style** | Earnings drift + momentum |
| **Status** | blocked |

## Entry

- Events: Nasdaq's earnings calendar for the SCOPE names outside the ETF basket (reported EPS, consensus, release time), refreshed at each session's open.
- Trigger: a positive surprise (actual - consensus) / |consensus| on a name whose last completed daily bar passes the liquid momentum trend rule: close > SMA 200, SMA 50 > SMA 200, 12-1 momentum > 0 and a 20-day dollar volume ≥ $20M.
- Entry: the open of the first session that can trade the report (a pre-market report that day, otherwise the next session); one event per name at a time.
- Book: every active event at 1/N of the book, re-targeted at each session's first pass.

## Exit

- Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1).

## Sizing

- $100,000 book in equal calendar-time weights.

## Data

- Nasdaq's archived earnings calendar pages and live quotes.
- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys.

## Code

- **Master desk**: `sleeves/griffith/event_research.py`, `sleeves/griffith/vendor/griffith/strategy_tournament.py`, `sleeves/griffith/feedlib/griffith_earnings.py`, `sleeves/griffith/feedlib/griffith.py`
