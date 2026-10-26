# Large-cap prior-month reversal

Each month, buys the five large caps that fell most last calendar month.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d (monthly) |
| **Universe** | 40 large caps |
| **Style** | Mean reversion |
| **Status** | live |

## Entry

- The five worst of the 40 by prior calendar-month return are the targets.

## Exit

- A held name that is no longer in the worst five is sold.

## Sizing

- dollars = min(cash, equity / 5); whole shares; at most 5 names.

## Data

- Yahoo daily closes.

## Code

- **Midna v3**: `sleeves/s_mn_reversal.py`
- **Master desk** (not in this repo): `desk/sleeves/midna/quantpedia.py`
- **Rule lines**: [docs/verify/midna.md](../../docs/verify/midna.md)

## Notes

- Midna v3's `s_mn_reversal` ranks by the prior 21 sessions, holds 3 names and rotates after 21 sessions.
- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
