# 52-week-high strength

Each month holds the top decile of the more liquid half of the SCOPE universe by closeness to the 52-week high, in equal weight.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 parallel strategy lab (HIGH52_MONTHLY) |
| **Asset** | US equities |
| **Timeframe** | 1d (monthly) |
| **Universe** | SCOPE universe: 550 US names |
| **Style** | 52-week-high momentum |
| **Status** | live |

## Entry

- Decision: at the first pass of each month, on the prior month's last SPY bar; the month waits until the tape carries 99% of the names it can.
- Score: the cutoff close / the highest high of the last 252 sessions, for names with a bar on the cutoff day and 60 sessions of positive volume; at least 10 names.
- Pick: the top half by 60-day median dollar volume, then its top decile by score (rounded up, at least 1; ties by symbol).
- Orders: each pick at 1/N of the book and the rest to zero, as marketable limits (1% through the quote, 30 minutes), re-sent on each of the month's first 5 sessions.

## Exit

- A name out of the next month's pick is sold at that rebalance; an empty pick is cash.

## Sizing

- $100,000 book in equal weights.

## Data

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys.

## Code

- **Master desk**: `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py`, `sleeves/griffith/feedlib/griffith.py`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)
