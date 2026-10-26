# 12-month momentum top decile (monthly)

On the first trading day of each month, holds the top tenth of liquid genome names by 12-month return in equal weight, with a 25% cap per known sector.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1d (monthly) |
| **Universe** | 1,838-name genome |
| **Style** | Momentum |
| **Status** | waiting |

## Entry

- Eligible: 253+ completed bars, median 63-day dollar volume ≥ $1M, no bankruptcy-artifact month; ranked by close / close 252 sessions back; the top 10% (rounded up).
- A known sector (semis, leveraged ETFs, biotech, software, energy, financials) may hold at most 25% of the names; the lowest-ranked are trimmed.
- Rebalances on the month's first trading day from 10:00 ET once most names carry the previous session (any data by 15:30).

## Exit

- A name out of the new decile is sold at the rebalance; no stop.

## Sizing

- Equal weight: 95% of the book / the decile's size, whole shares (at least 1) at a fresh mid.
- Cost modeled at 75 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars of the genome (400, cached), desk quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/ts_momentum_decile.py`
- **Midna v3**: `sleeves/ts_momentum_decile.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the sector cap is enforced again on the sized dollar values.
