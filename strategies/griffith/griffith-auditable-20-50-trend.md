# Auditable 20/50 trend (SPY)

Trades SPY on its 5-minute 20/50 average cross: $100 in when the 20 is above the 50, out when it drops below.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith / Ledge desk app, the auditable TrendAgent |
| **Asset** | US ETF (SPY) |
| **Timeframe** | 5m |
| **Universe** | SPY |
| **Style** | Moving-average trend |
| **Status** | waiting |

## Entry

- Every 15 minutes on SPY's last 50 completed 5-minute bars, only on a new newest bar and never while an order works: buy when flat and SMA 20 > SMA 50 × 1.001.
- Order: round($100 / price, 6) shares as a DAY limit at the price × 1.001.

## Exit

- Sold when SMA 20 < SMA 50 while long, a DAY limit at the price × 0.999.

## Sizing

- $100 a trade.

## Data

- SPY's IEX 5-minute bars, the last 51.

## Code

- **Master desk**: `sleeves/griffith/griffith_intraday.py`; not in this repo: `desk/vendor/griffith/config.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)
