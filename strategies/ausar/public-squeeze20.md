# Public BB/KC squeeze (daily)

Buys when Bollinger Bands expand out of the Keltner Channel with rising positive momentum and a 20-day breakout.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | trader.dev public strategy; LazyBear squeeze momentum; StockCharts TTM squeeze |
| **Asset** | US ETFs |
| **Timeframe** | 1d |
| **Universe** | 15 liquid ETFs (as RSI2) |
| **Style** | Volatility breakout |
| **Status** | waiting |

## Entry

- Prior bar BB(20, 2) inside KC(20, 1.5 ATR), current bar not; momentum (linear-regression endpoint) > 0 and rising; close > the prior 20-day high.

## Exit

- Close < EMA20, momentum ≤ 0, the 2 × ATR stop, or 20 holding bars.

## Sizing

- Liquidity cap and 0.5% risk to the stop, as Donchian 55.

## Data

- Yahoo daily bars.

## Code

- **Midna v3**: `desk3/aster_batch1.py`
- **Master desk** (not in this repo): `desk/vendor/ausar/trader_signals.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
