# Listed reversal call spread

Buys a call spread on each of the five worst prior-month large caps.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | Equity options |
| **Timeframe** | 1d (monthly) |
| **Universe** | 40 large caps |
| **Style** | Mean reversion (options) |
| **Status** | live |

## Entry

- Long the ATM call, short the listed strike nearest 5% above; debit ≥ $0.20; while fewer than five are open.

## Exit

- Closed when the name leaves the five, or at expiry.

## Sizing

- qty = floor(min(cash, equity / 5) / debit).

## Data

- Cboe delayed option chains; the reversal signal.

## Code

- **Midna v3**: `sleeves/s_mn_opt_reversal.py`
- **Master desk** (not in this repo): `desk/sleeves/midna/options.py`

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
