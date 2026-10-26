# APEX O3: regime put-write

Sells monthly QQQ puts half a standard deviation out of the money while the APEX target is above zero, on up to 3× the book.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), options study O3 |
| **Asset** | US ETFs and ETF options |
| **Timeframe** | 1d (monthly puts) |
| **Universe** | QQQ, TQQQ, BIL; QQQ listed options |
| **Style** | Options income, trend regime |
| **Status** | live |

## Entry

- L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)).
- At a month's first session with L* > 0 and no puts held: sells puts struck spot × e^(-0.5 σ√T) (σ = at-the-money implied vol), the next monthly expiry ≥ 15 days out, on min(L*, 3) × NAV / spot shares.

## Exit

- L* ≤ 0 buys the puts back; otherwise they are held to expiry.

## Sizing

- Core: T-bills (BIL).
- Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits.
- The core trades market-on-close on the equity less the options' value; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Code

- **Master desk**: `sleeves/apex/apex_options.py`, `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)
