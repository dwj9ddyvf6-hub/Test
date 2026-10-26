# Legend's EMA (QQQ trend-day fade)

After a QQQ trend day that never touched its 15-minute EMA(20), trades at the next open toward that EMA, with a half-ATR stop, flat by the close.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US ETF |
| **Timeframe** | 15m · 1d |
| **Universe** | QQQ |
| **Style** | Intraday mean reversion |
| **Status** | waiting |

## Entry

- Setup: the prior regular session was a trend day (|close - open| / range ≥ 0.7686) whose 15-minute bars never touched EMA(20) (warmed over the 5 sessions before).
- Entry 09:30-09:45 ET at the open print, toward the EMA: short when the open is above it, long when below; one trade a session; unfilled after 240 s, cancelled.

## Exit

- Take-profit at the EMA (refreshed once it moves $0.20); stop 0.5 × ATR(14) of daily ranges from the fill; flat at 15:59 ET (5 minutes before an early close).

## Sizing

- Shares = 0.25% of the book / (0.5 × ATR14).
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Yahoo 15-minute bars (260), split-adjusted daily bars (40), the open print.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/legends_ema.py`
- **Midna v3**: `sleeves/legends_ema.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no entry when the open is less than the half-ATR stop away from the EMA.
