# Faber ETF trend (10-month average)

Holds each ETF of a basket while it closes above its 10-month average, else cash: five asset-class ETFs on Midna's book, a 13-ETF basket in equal weights on Griffith's.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk; also the Griffith R4 parallel strategy lab (ETF_SMA10_MONTHLY); Mebane Faber's 10-month rule |
| **Asset** | US ETFs |
| **Timeframe** | 1d (monthly average) |
| **Universe** | SPY, EFA, BND, VNQ, GSG · Griffith: 13 ETFs |
| **Style** | Trend filter |
| **Status** | 2 live |

## Entry

- Midna book: buys a fund whose last close is above the mean of the ten month-end closes before the current month; acts on the session after the signal session, from 10:00 ET.
- Griffith book: at the first pass of each month, on the prior month's last SPY bar, holds every basket ETF whose month-end close is above the mean of the last 10 month-end closes (that one included).
- Griffith basket: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLI, XLP, XLV, XLU, TLT and GLD (the frozen 17 less XLY, XLB, XLRE and IEF, which the tape never carries); each needs a bar on the cutoff day.

## Exit

- Sells a held fund that is no longer above its average (Griffith: at the next month's rebalance).

## Sizing

- Midna book: dollars = min(cash, equity / 5); whole shares at the ask.
- Griffith book: $100,000 in equal weights over the ETFs held, as marketable limits 1% through the quote (30 minutes), re-sent on each of the month's first 5 sessions.

## Data

- Yahoo daily closes, two years.
- Griffith book: Alpaca IEX raw daily bars (the last 550 sessions), Yahoo without keys.

## Variants

| Book | Basket | Decision | Sizing | Rows |
|---|---|---|---|---|
| Midna (the master desk's port) | SPY, EFA, BND, VNQ, GSG | daily, against the ten month-ends before the month | a fifth of equity each | `midna_faber` |
| Midna v3 | SPY, EFA, EEM, VNQ, AGG | daily, against a 210-session average | $600 each of a $3,000 budget | `s_mn_faber` |
| Griffith R4 lab | 13 ETFs | month end, the last 10 month-ends | equal weight over the ETFs held | `griffith_etf_sma10m` |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `sleeves/s_mn_faber.py`
- **Master desk** (not in this repo): `desk/sleeves/midna/quantpedia.py`
- **Master desk (Griffith R4 lab)**: `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py`, `sleeves/griffith/feedlib/griffith.py`

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
