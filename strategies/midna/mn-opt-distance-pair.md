# Listed distance-pair package

Expresses the distance-pair signal with listed options: a call on the cheap leg and a put on the rich leg.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | Equity options |
| **Timeframe** | 1d |
| **Universe** | 40 large caps |
| **Style** | Pairs (options) |
| **Status** | live |

## Entry

- On a listed pair with |z| ≥ 2: call on the cheap leg, put on the rich leg.

## Exit

- Closed when |z| < 0.5, or at expiry.

## Sizing

- Budget = min(cash, equity / 5) per package.

## Data

- Cboe delayed option chains; the pairs signal.

## Code

- **Midna v3**: `sleeves/s_mn_opt_pairs.py`
- **Master desk** (not in this repo): `desk/sleeves/midna/options.py`
- **Rule lines**: [docs/verify/midna.md](../../docs/verify/midna.md)

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
