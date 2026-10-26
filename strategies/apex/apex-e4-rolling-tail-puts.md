# APEX E4: rolling tail puts

APEX-30 Nasdaq exposure plus QQQ puts 15% out of the money, bought each month while the exposure is above 1.5×.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), APEX-NDX extension E4 |
| **Asset** | US ETFs and ETF options |
| **Timeframe** | 1d (monthly puts) |
| **Universe** | QQQ, TQQQ, BIL; QQQ listed options |
| **Style** | Trend × volatility targeting, tail hedge |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- Core: APEX-30 exposure = trend score × min(3, 30% / volatility), with its 0.20 band.
- Puts: at a month's first session, while the APEX-30 exposure held after this close is above 1.5, buys QQQ puts 15% under spot, the listed expiry nearest 63 sessions, on exposure × NAV / spot shares (whole contracts).

## Exit

- At each month's first session the held puts are sold before any new ones are bought; between months they are held.

## Sizing

- Puts once a session in the last 45 minutes (15:15-15:45 ET), marketable limits; the core market-on-close on the equity less the puts' value; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.
- The live QQQ quote and the listed QQQ puts.

## Code

- **Master desk**: `sleeves/apex/apex_options.py`, `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`, `sleeves/apex/vendor/apex/backtest_options.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)

## Notes

- The source priced its puts with Black-Scholes, a 0.7-point skew and a 5% spread on the Nasdaq-100 level; the desk buys listed QQQ puts at the market.
