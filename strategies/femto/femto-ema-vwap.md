# 20-day VWAP reversion

Buys a basket name that closes more than 2% under its 20-day VWAP and sells it back at the VWAP, +5%, -8% or after 5 days.

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

- A close more than 2% under the 20-day VWAP (typical price × volume); ≥ 31 bars; not on or before the last exit day.
- Checked hourly at :57 in the session; at most 8 positions.

## Exit

- Back at or above the VWAP, +5%, -8%, or 5 weekdays held; a 25% disaster stop.

## Sizing

- 0.25% of the book on the 8% stop, at most 5% of the book a name and 25% for the sleeve.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (120).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/ema_vwap.py`
- **Midna v3**: `sleeves/ema_vwap.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): only entries whose gap back to the VWAP is at least the 8% stop (about 7.4% under the VWAP).
