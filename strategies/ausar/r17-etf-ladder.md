# R17 ETF ladder rules

Six monthly ETF selection rules (relative strength, acceleration, repair, volatility-adjusted) that put unused slots in QQQ.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17 ETF research |
| **Asset** | US ETFs |
| **Timeframe** | 1d, monthly |
| **Universe** | QQQ, SPY, SMH and the 11 sector SPDRs |
| **Style** | Momentum rotation |
| **Status** | 6 live |

## Entry

- Month-end decision; signals: 126- and 21-day log returns, 63-day volatility, 200-day MA, 20-day drawdown.
- LEADER3: top 3 by 126-day return. RELATIVE3: top 3 beating QQQ. VOLADJ3: relative strength / volatility. ACCEL3: (21-day - 126-day/6) / volatility, above the 200-day MA. REPAIR3: beating QQQ, 2-10% off the 20-day high, up 3 days, above the 200-day MA. ESCAPE1: best positive 126-day return above the 200-day MA.
- Unfilled slots go to QQQ (ESCAPE1 stays in cash).

## Exit

- Held to the next month-end decision; sells first at the open.

## Sizing

- Equal weights × gross 0.98; each fund capped at 0.1% of its prior-day dollar volume; 15 bps per side.

## Data

- Total-return daily closes and raw dollar volume.

## Variants

| Rule | Slots |
|---|---|
| LEADER3 · RELATIVE3 · VOLADJ3 · ACCEL3 · REPAIR3 | 3 |
| ESCAPE1 | 1 |

Rows: 6 on the master desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk**: `sleeves/ausar/r17_etf.py`, `sleeves/ausar/vendor/quant_r17/run_ladder.py`, `sleeves/ausar/vendor/quant_r17/EXPERIMENT_PROTOCOL.json`
