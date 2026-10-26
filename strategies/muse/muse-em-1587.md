# 15.87 Rule (SPY 0DTE)

Draws the day's expected-move map from the VIX (prior close ± (VIX ÷ 15.87)%), then buys same-day SPY calls or puts on a confirmed SPY and QQQ break of the opening box, or fades a wall toward the close.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Azrael's 15.87 Rule, reverse-engineered from his worksheet |
| **Asset** | SPY options (0DTE) |
| **Timeframe** | 5m |
| **Universe** | SPY (QQQ confirms) |
| **Style** | Expected-move levels |
| **Status** | waiting |

## Entry

- Map: EM = the prior SPY close × the prior VIX close / 15.87 %, rounded to 0.1; lines at the close ± EM (walls), ± EM/2 (shelves) and the close (magnet).
- Regime from the same VIX close: under 15 fade; 15-18.5 confirm; above 18.5 fast (break only, half size).
- Break (confirm and fast): SPY and QQQ each close beyond their own 09:30-09:50 box on the same 5-minute bar by ≥ 0.05 × their EM; each box no wider than 0.2 × its EM; room to the next line > 0.8 points and ≥ 1R (the close to the box edge).
- Fade (calm): the first bar whose range reaches a wall, long from the lower wall, short from the upper; a bar touching both stands down.
- Signal closes 09:50-11:05, acted on within 30 minutes; one setup a day.
- Contract: today's SPY expiry, strike nearest the spot; its quote two-sided, spread ≤ 5% of mid, ≤ 60 s old; a limit at the mid.

## Exit

- Break: out when a bar reaches the next line, or on a 5-minute close back inside the SPY box (the target is checked first).
- Fade: out at the magnet, or on a 5-minute close beyond the wall by EM/2 (the stop is checked first).
- Hard flat at 11:30 ET: a mid limit, the bid from 11:25, market from 11:28; a position from an earlier day is sold at once.

## Sizing

- 4% of the $10,000 slice in premium (half in fast), whole contracts, at least 1.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- SPY and QQQ 5-minute bars (4,000), the prior ^VIX close (Yahoo daily), the SPY option chain with quotes, per-strike open interest.

## Code

- **Master desk**: `sleeves/muse/core/em_1587.py`, `sleeves/muse/muse.py`; not in this repo: `desk/sleeves/muse/sleeves/em_1587.py`. The strategy file is Midna v3's `sleeves/em_1587.py`
- **Midna v3**: `sleeves/em_1587.py`, `integration/em_1587_adapter.py`
- **Rule lines**: [docs/verify/muse.md](../../docs/verify/muse.md)

## Notes

- SPX is read as SPY: the map is drawn in SPY prices and SPX points convert at 10 to 1.
- Open-interest strikes are compared with the map and logged; they never gate.
