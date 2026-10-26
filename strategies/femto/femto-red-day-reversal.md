# Red-day washout reversal

Buys a basket name above its 200-day average after a 3%+ down day with RSI(2) ≤ 10, and sells at +4%, -2% or after 3 days.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | 41-name old-desk basket |
| **Style** | Mean reversion |
| **Status** | live |

## Entry

- Signal on the last completed day: close ≥ 3% down, RSI(2) ≤ 10, close > SMA200 (202+ bars).
- No earnings within 5 days (the index and leveraged ETFs clear); in regular hours only; a limit at the last close until the close; at most 8 positions.

## Exit

- +4% (a limit), -2% (market) on a fresh intraday mark, or 3 days after the fill.

## Sizing

- 0.25% of the book on the 2% stop, at most 25% of the book in notional.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (220), intraday marks, the earnings calendar.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/red_day_reversal.py`
- **Midna v3**: `sleeves/red_day_reversal.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no entry when the washout day's range is wider than the 4% target.
