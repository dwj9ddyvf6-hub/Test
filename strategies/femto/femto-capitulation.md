# Capitulation reversal (hourly)

Buys the first green hourly bar after an RSI(14) < 20 volume-climax flush into the 200-day EMA, half size first, the rest once the 5/20-day EMAs turn up.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1h · 1d filters |
| **Universe** | 41-name old-desk basket |
| **Style** | Mean reversion |
| **Status** | waiting |

## Entry

- Signal on the last closed hourly bar: green, RSI(14) rising from below 20; the prior bar's volume > 2× its 20-bar average and its low within 2% of the 200-day EMA.
- Daily ATR(14) > 5% of the close; buys wait while the desk fear composite is below 55.
- Half the size first; the other half once the 5-day EMA is above the 20-day, within 5 sessions.
- Scans hourly at :27; a signal after hours fills at the next open.

## Exit

- Back to the session VWAP, +5%, -8%, or 3 trading days; a 25% disaster stop.

## Sizing

- Full size = 0.25% of the book / an 8% stop; at most 5 positions.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Daily bars (260) and regular-hours hourly bars (15 days).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/capitulation.py`
- **Midna v3**: `sleeves/capitulation.py`

## Notes

- Midna v3 adds a 3-day pre-earnings veto, and an Edge-IMPROVE change (2026-10-24, on by default): no entry when the close is already at or above the session VWAP.
