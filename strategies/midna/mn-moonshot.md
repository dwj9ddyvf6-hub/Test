# Weekly cyan moonshot

Buys cheap, deeply drawn-down weekly buy-cyan fires with $1,000 each and holds 78 weeks.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Midna's swing basket |
| **Style** | Value recovery |
| **Status** | waiting |

## Entry

- A weekly buy-cyan fire with close ≤ $14.94 and 60-week depth ≥ 70.35, ≤ 10 days old, not seen before; fewer than 10 open.

## Exit

- Closes at the first regular-hours print after its 78th week; no stop.

## Sizing

- floor(min(cash, $1,000) / price).

## Data

- The hourly watch's weekly moonshot fires.

## Code

- **Midna v3**: `sleeves/s_mn_moonshot.py`. Consumes upstream fires; no stop, 390 sessions
- **Master desk**: `sleeves/midna/shadow.py`
