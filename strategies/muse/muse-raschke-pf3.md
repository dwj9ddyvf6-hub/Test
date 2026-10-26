# Raschke PF3 momentum (SPY)

Trades SPY long or short at the first 5-minute bar where ROC2 and the 3-10 oscillator's fast and slow lines all turn the same way, with a 0.75 ATR stop and 1.5 ATR target.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Linda Raschke's PF3 momentum method, as designed into an algorithm by Grok (for ES 5-minute futures) |
| **Asset** | SPY shares, long and short |
| **Timeframe** | 5m |
| **Universe** | SPY |
| **Style** | Momentum |
| **Status** | waiting |

## Entry

- On completed regular-hours SPY 5-minute bars: ROC2 = close - close 2 bars back; Fast = SMA(3) - SMA(10) of closes; Slow = SMA(16) of Fast.
- Long when all three rose on the last bar, short when all fell; only the first bar of a new aligned run, begun today, one attempt per run.
- Signal bars closing by 10 minutes before the close; marketable orders.

## Exit

- Stop 0.75 ATR(14) and target 1.5 ATR from the signal close, judged on completed-bar closes.
- Out when any of the three slopes turns against the position, or after 10 bars.
- Flat 5 minutes before the close; a position from an earlier session is sold at once.

## Sizing

- floor(0.5% of the $10,000 slice / (0.75 × ATR)) shares; none under 1.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- SPY 5-minute bars (4,000).

## Code

- **Master desk**: `sleeves/muse/sleeves/raschke_pf3.py`, `sleeves/muse/muse.py`. Vendored from Midna v3
- **Midna v3**: `sleeves/raschke_pf3.py`, `integration/raschke_pf3_adapter.py`. A wrapper only; the strategy file is not in this repo

## Notes

- The optional ADX(14) > 20 trend filter is off.
