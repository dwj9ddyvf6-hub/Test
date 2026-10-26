# APEX O6: Variance Value

A 1× QQQ core plus a monthly volatility trade: an iron fly when implied vol is rich, a straddle when it is cheap.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), options study O6 |
| **Asset** | US ETFs and ETF options |
| **Timeframe** | 1d (monthly options) |
| **Universe** | QQQ, TQQQ, BIL; QQQ listed options |
| **Style** | Volatility relative value |
| **Status** | live |

## Entry

- Core: QQQ at 1×.
- Variance Value, at a month's first session with none held, on the next monthly expiry ≥ 15 days out: at-the-money implied vol / the HAR forecast ≥ 1.25 sells the at-the-money straddle and buys wings 1.5 σ√T out (an iron fly), NAV / spot shares a leg; ≤ 0.95 buys the at-the-money straddle with 2% of NAV.

## Exit

- Option structures are held to expiry.

## Sizing

- Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits.
- The core trades market-on-close on the equity less the options' value; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Code

- **Master desk**: `sleeves/apex/apex_options.py`, `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)
