# EMA4 rising VWAP

Buys when EMA(4) crosses above a rising 20-session VWAP, and exits on the cross back or a 3-ATR chandelier.

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

- EMA(4) crosses above the 20-session volume-weighted typical price while that VWAP is above its value 5 sessions earlier; alphabetical; up to 4 names.

## Exit

- The cross back, or the 3 × ATR(14) chandelier under the peak.

## Sizing

- One unit = min(floor(1% of equity / ATR14), floor(cash / price)).

## Data

- Completed daily bars.

## Code

- **Midna v3**: `sleeves/s_mn_vwap.py`
- **Master desk**: `sleeves/midna/board.py`, `sleeves/midna/vendor/midna/board_signals.py`

## Notes

- Midna v3's `s_mn_vwap` trades the price crossing a 20-session VWAP, one slot.
- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
