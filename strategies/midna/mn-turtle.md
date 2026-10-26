# Turtle System 1

Buys 20- or 55-day closing breakouts with Turtle unit sizing and pyramiding, and exits on a 2N stop or a 10-day low.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Midna's swing basket |
| **Style** | Breakout |
| **Status** | live |

## Entry

- A close above the prior 20-day (or 55-day) high, new today; at most 4 names, alphabetical.
- A 20-day breakout right after a winning exit is skipped once; the 55-day one is taken.
- Adds a unit at each +0.5N over the last add, up to 4 units.

## Exit

- Stop at entry - 2N (raised with adds), on any regular-hours print; signal exit on a close under the prior 10-day low.

## Sizing

- Unit = min(floor(1% of equity / N), floor(cash / price)), N = ATR(20).

## Data

- Completed daily bars of the swing basket.

## Code

- **Master desk**: `sleeves/midna/board.py`, `sleeves/midna/vendor/midna/board_signals.py`, `sleeves/midna/common.py`

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
