# ETF 12-month time-series momentum

Each month holds, in equal weight, every ETF of a frozen basket whose 252-session return is positive; cash otherwise.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 parallel strategy lab (ETF_TSMOM_12M) |
| **Asset** | US ETFs |
| **Timeframe** | 1d (monthly) |
| **Universe** | 13 ETFs on the tape of a frozen 17-ETF basket |
| **Style** | Time-series momentum |
| **Status** | live |

## Entry

- Decision: at the first pass of each month, on the prior month's last SPY bar; the month waits until the tape carries 99% of the names it can.
- Basket: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLI, XLP, XLV, XLU, TLT and GLD (the frozen 17 less XLY, XLB, XLRE and IEF, which the tape never carries); each needs a bar on the cutoff day.
- Long when the cutoff close is above the close 252 sessions before (253 bars needed).
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
