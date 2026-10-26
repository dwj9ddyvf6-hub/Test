# QLD weekly timing

Holds QLD all-in while QQQ's weekly EMA(12) is above its EMA(26), switching at the open of each week.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | Leveraged ETF |
| **Timeframe** | 1w |
| **Universe** | QLD (QQQ signal) |
| **Style** | Trend filter |
| **Status** | live |

## Entry

- Prior completed QQQ week: EMA(12) above EMA(26) of weekly closes (SMA-seeded, from 1990 adjusted daily history).
- Trades in the first regular-hours pass of the week.

## Exit

- Sells QLD at the open of a week whose prior week shows EMA(12) ≤ EMA(26).

## Sizing

- The whole book: notional = cash / (1 + 0.1%).

## Data

- Yahoo QQQ and QLD daily history.

## Code

- **Master desk**: `sleeves/midna/qld.py`
