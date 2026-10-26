# MACD-CCI

Buys a MACD cross up when CCI(20) is above 100, strongest CCI first, and exits on the cross down or a 3-ATR chandelier.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Midna's swing basket |
| **Style** | Momentum |
| **Status** | waiting |

## Entry

- MACD(12, 26) crosses above its 9-period signal with CCI(20) > 100; ranked by CCI; up to 4 names.

## Exit

- The cross back down, or the price under the peak since entry - 3 × ATR(14).

## Sizing

- One unit = min(floor(1% of equity / ATR14), floor(cash / price)).

## Data

- Completed daily bars.

## Code

- **Midna v3**: `sleeves/s_mn_macd.py`
- **Master desk**: `sleeves/midna/board.py`, `sleeves/midna/vendor/midna/board_signals.py`

## Notes

- Midna v3's `s_mn_macd` trades a plain MACD(12, 26, 9) cross with one slot, no CCI filter or chandelier.
- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
