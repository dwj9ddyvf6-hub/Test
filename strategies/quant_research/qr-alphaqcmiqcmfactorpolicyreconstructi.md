# AlphaQCM factor rotation

Every 20 sessions buys the top 20% of a frozen 100-stock roster by AlphaQCM's ten-factor pool, equal weight, and holds until the next decision.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | AlphaQCM (ZhuZhouFan/AlphaQCM), reconstructed in the desk's six-strategy study |
| **Asset** | US equities |
| **Timeframe** | 1d (every 20 sessions) |
| **Universe** | Frozen 100-stock roster (the most traded of 2016-2020) |
| **Style** | Factor model · periodic rebalance |
| **Status** | live |

## Entry

- Score: the ten frozen formula factors of AlphaQCM's validation-selected pool, each evaluated on split-adjusted daily OHLCV and VWAP, masked to the eligible names, z-scored across them by day and summed with its pool weight.
- Eligible: 252 complete prior sessions, a 20-session average dollar volume ≥ $10M and a close ≥ $5.
- Decision: every 20th session from 2023-01-03, on that close; traded from the next session's first pass.
- Pick: the top 20% of the scored names (at least 1), equal weight; with fewer than 10 scored names it holds cash until the next decision.
- Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.

## Exit

- Names outside the next decision's pick are sold at that rebalance; holdings drift in between.

## Sizing

- $1,000,000 book: each weight × NAV (cash plus holdings at the bid) at the ask, fractional shares, fixed at the decision.

## Data

- Split-adjusted daily bars (Alpaca; Yahoo without keys) of the 100 names, the last 300 sessions.

## Code

- **Master desk**: `sleeves/quant_research/alphaqcm.py`, `sleeves/quant_research/alphagen_np.py`, `sleeves/quant_research/common.py`

## Notes

- Its vendored AlphaQCM files (upstream code under its own license) are not copied here.
