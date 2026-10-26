# APEX O8: FEAR put spread

APEX-50F Nasdaq exposure plus a monthly short 90/80 QQQ put spread when fear is high and the trend weak.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), options study O8 |
| **Asset** | US ETFs and ETF options |
| **Timeframe** | 1d (monthly options) |
| **Universe** | QQQ, TQQQ, BIL; QQQ listed options |
| **Style** | Trend × volatility + options income |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- Core: APEX-50F Nasdaq exposure with its 0.20 band, in QQQ / TQQQ.
- FEAR: at a month's first session when 30-day implied vol is at or above its 252-day 80th percentile and the trend score is ≤ 2 of 6, sells the 90% put and buys the 80% put, the expiry nearest 61 days (≥ 45), NAV / spot shares.

## Exit

- Held to expiry.
- No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL).

## Sizing

- Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits.
- The core trades market-on-close on the equity less the options' value; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Code

- **Master desk**: `sleeves/apex/apex_options.py`, `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
