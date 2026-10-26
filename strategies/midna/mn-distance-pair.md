# Distance-pair shares

Among the 20 closest large-cap pairs, buys the cheap leg when the spread is two standard deviations wide.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 40 large caps |
| **Style** | Pairs |
| **Status** | live |

## Entry

- Pairs: the 20 with the smallest squared distance of normalized prices over 252 sessions.
- Buys the cheaper normalized leg when |z| ≥ 2, closest pairs first.

## Exit

- Sells the leg once |z| < 0.5.

## Sizing

- dollars = min(cash, equity / 5); at most 5 names.

## Data

- Yahoo daily closes.

## Code

- **Midna v3**: `sleeves/s_mn_pairs.py`
- **Master desk** (not in this repo): `desk/sleeves/midna/quantpedia.py`

## Notes

- Midna v3's `s_mn_pairs` uses declared pairs and a 60-session z, trades both legs and exits at |z| ≤ 0.25.
- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
