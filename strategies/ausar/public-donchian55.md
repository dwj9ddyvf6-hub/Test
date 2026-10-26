# Public Donchian 55 trend (daily)

Buys a 55-day breakout above the 200-day average and rides it until a 20-day low or the trend breaks.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | trader.dev public strategy; StockCharts price channels |
| **Asset** | US ETFs |
| **Timeframe** | 1d |
| **Universe** | 15 liquid ETFs (as RSI2) |
| **Style** | Trend breakout |
| **Status** | live |

## Entry

- Close > the prior 55-day high and > SMA200; ranked by (close - prior high) / ATR14; next open.

## Exit

- Close < the prior 20-day low or < SMA200, the 2 × ATR stop, or 126 holding bars.

## Sizing

- Liquidity cap as RSI2, and ≤ 0.5% of equity at risk to the 2 × ATR14 stop.

## Data

- Yahoo daily bars.

## Code

- **Midna v3**: `desk3/aster_batch16.py`
- **Master desk** (not in this repo): `desk/vendor/ausar/trader_signals.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
