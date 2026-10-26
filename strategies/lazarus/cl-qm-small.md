# ChartsLector breakout leaders (small caps)

Buys small caps the day they enter ChartsLector's Qullamaggie screen, unless stretched more than 4 ATR above the 50-day, and holds 90 sessions.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | ChartsLector (his Qullamaggie TradingView screen), via Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Tracker universe, small band ($300M-$2B) |
| **Style** | Breakout |
| **Status** | live |

## Entry

- Screen: ADR(14) ≥ 4%, EMA10 ≥ EMA20 ≥ SMA50 ≥ SMA150, close ≥ EMA20, 60-day volume > 300k; it turns on today.
- Then (close - SMA50) / ATR14 < 4, close ≥ $5, dv20 ≥ $100k, not an ETF, band small.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 90 sessions.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position, 14 slots, $14,491.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- The tracker engine's daily store; PIT SEC shares for the band.

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Midna v3 (lane file)**: `sleeves/lazarus/s_cl_qm_small.py`. Calls `laz_sleeves._common`, which is not in this repo
- **Rule lines**: [docs/verify/lazarus.md](../../docs/verify/lazarus.md)

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
- Midna v3's `s_cl_qm_small` is a simpler reading: a 20-day high breakout, close ≤ 1.25 × SMA20, the small-cap tag and the QQQ-down rule.
