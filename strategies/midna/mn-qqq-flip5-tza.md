# QQQ flip5 TZA hedge

When QQQ's slow Tensor state has turned bearish within five sessions, buys TZA at 30% of $100,000 for up to 20 sessions.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | Leveraged ETF |
| **Timeframe** | 1d |
| **Universe** | TZA (QQQ signal) |
| **Style** | Hedge |
| **Status** | waiting |

## Entry

- flip5: QQQ's slow state turned bearish on one of the last five closed daily bars.
- With nothing held, flip5 stages a buy for the next session's open.

## Exit

- Sells at the next open when flip5 is off or after 20 held sessions.

## Sizing

- Notional = 30% × $100,000 at the open.

## Data

- QQQ and TZA daily bars from the hourly watch.

## Code

- **Midna v3**: `sleeves/lazarus/s_mn_hedge.py`. Reads a `hedge_signal` input with no producer in this repo; $300 of a $1,000 budget
- **Master desk**: `sleeves/midna/shadow.py`
