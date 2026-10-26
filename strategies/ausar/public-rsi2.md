# Public RSI(2) pullback (daily)

Buys a liquid ETF in a long-term uptrend after an extreme 2-day RSI pullback and sells on the bounce.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | trader.dev public strategy; StockCharts ChartSchool RSI(2) |
| **Asset** | US ETFs |
| **Timeframe** | 1d |
| **Universe** | SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX |
| **Style** | Mean reversion |
| **Status** | waiting |

## Entry

- Wilder RSI(2) ≤ 5, close > SMA200 and close < SMA5 on the completed day.
- Ranked by lowest RSI(2); buys at the next open within 300 s; at most 10 names.

## Exit

- Close > SMA5, or 10 completed holding bars. No stop.

## Sizing

- floor(min(10% equity, 1% of 20-day dollar volume, cash) / (ask × 1.001)).

## Data

- Yahoo daily bars (252+).

## Code

- **Midna v3**: `desk3/aster_batch1.py`
- **Master desk** (not in this repo): `desk/vendor/ausar/trader_signals.py`, `desk/sleeves/families/ausar_public.py`
