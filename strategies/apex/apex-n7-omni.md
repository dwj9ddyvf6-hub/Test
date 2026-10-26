# APEX N7: OMNI

N1's Duration Shield Nasdaq exposure plus a monthly Variance Value options trade on the whole book.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), invention N7 |
| **Asset** | US ETFs and ETF options |
| **Timeframe** | 1d (monthly options) |
| **Universe** | QQQ, TQQQ, BIL; QQQ listed options |
| **Style** | Trend × volatility targeting + volatility options |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- Core: APEX-50F exposure = trend score × min(4, 50% / volatility), × 0.5 when the 10-year yield is up more than 0.50 over 63 sessions; 0.20 band.
- Variance Value, at a month's first session with none held, on the next monthly expiry ≥ 15 days out: at-the-money implied vol / the HAR forecast ≥ 1.25 sells the at-the-money straddle and buys wings 1.5 σ√T out (an iron fly), NAV / spot shares a leg; ≤ 0.95 buys the at-the-money straddle with 2% of NAV.

## Exit

- Option structures are held to expiry.
- No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL).

## Sizing

- Variance Value on the whole book's NAV.
- Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits.
- The core trades market-on-close on the equity less the options' value; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`, `sleeves/apex/vendor/apex/inventions.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
