# Kronos-base TopkDropout

Ranks 24 names by the Kronos-base 10-session forecast and holds the top 4, dropping at most one a cycle.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d (10-session cycle) |
| **Universe** | 24 frozen names |
| **Style** | Model forecast |
| **Status** | live |

## Entry

- Score = forecast close in 10 sessions / last close - 1, rebuilt every 10 sessions.
- TopkDropout: drop the worst held name held ≥ 5 sessions and out of today's top 5, then fill back to 4.

## Exit

- Sold when dropped from the targets.

## Sizing

- Slice = 95% of equity / 4; whole shares at last ± 0.1%.

## Data

- Kronos-base forecasts on daily bars.

## Code

- **Midna v3**: `sleeves/s_mn_kronos.py`. Consumes forecast fires from an upstream producer not in this repo
- **Master desk** (not in this repo): `desk/sleeves/midna/kronos.py`

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
