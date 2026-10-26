# Fear premium put spreads (red days)

After a 5%+ down day with RSI(14) under 50, sells a put credit spread about 7% under the price, 25-35 days out, on the highest-beta names.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | SOXL, TQQQ + the 10 highest-beta basket names |
| **Style** | Premium selling |
| **Status** | live |

## Entry

- Universe: SOXL and TQQQ plus the 10 basket names with the highest 60-day beta to QQQ, re-ranked every 7 days.
- Signal: the last completed day closed ≥ 5% down with RSI(14) < 50; no earnings today or in the next 3 days (the ETFs clear).
- Spread: short put nearest 7% under the price, long one width lower (about 10% of the price, on the strike grid), one expiry 25-35 DTE; each leg's spread ≤ 10% of mid; credit ≥ 3% of the capital at risk; at most 5.

## Exit

- Half the credit captured, 8 days since the fill, or 21 days to expiry.

## Sizing

- Contracts = 0.5% of the book / the capital at risk, capped by 25% of the book in short-strike notional.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (90), the desk's 25-35 DTE put chains and quotes, the earnings calendar.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/fear_premium.py`
- **Midna v3**: `sleeves/fear_premium.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the 8-day exit fires only when the spread is flat or losing.
