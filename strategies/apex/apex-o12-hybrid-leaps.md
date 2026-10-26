# APEX O12: hybrid LEAPS + QQQ trim

1-year 0.80-delta QQQ calls for 75% of the APEX-50F exposure, with the rest as a QQQ share trim.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), options study O12 |
| **Asset** | US ETFs and ETF options |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, BIL; QQQ listed options |
| **Style** | Trend × volatility in LEAPS |
| **Status** | live |

## Entry

- L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)).
- Calls: the expiry nearest 365 days (≥ 300), the strike for 0.80 delta.
- Calls for 75% of L*: 0.75 × L* × NAV / (delta × spot), at most 99.5% of NAV in premium, opened when none are held and L* > 0; after an L* ≤ 0 exit, only at a month's first session.
- Trim: QQQ shares (long or short) for L* less the calls' delta exposure, traded on a change of 0.20 or more, or to 0.

## Exit

- L* ≤ 0 sells the calls; they roll under 183 days or outside 0.60-0.95 delta.

## Sizing

- Core: T-bills (BIL).
- Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits.
- The core trades market-on-close on the equity less the options' value; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Code

- **Master desk**: `sleeves/apex/apex_options.py`, `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`

## Notes

- The source's trim was a futures position; the desk trades it in QQQ shares.
