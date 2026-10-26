# APEX O1: CONVEX

Holds the first 1× of the APEX-50F exposure in QQQ and the rest in 3-month at-the-money calls.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), options study O1 / O1b |
| **Asset** | US ETFs and ETF options |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, BIL; QQQ listed options |
| **Style** | Trend × volatility, convex options |
| **Status** | 2 live |

## Entry

- L* = the APEX-50F target on the last finished session (trend score × min(4, 50% / volatility)).
- Core: QQQ at min(L*, 1) with a 0.20 band.
- Calls for the rest (L* - 1): at the money, the expiry nearest 91 days, delta-sized: want × NAV / (delta × spot) shares.
- O1: re-struck at each month's first session or when the calls' delta exposure is 0.5 off the want (expiry ≥ 45 days, delta > 0.05).
- O1b: opens at a want ≥ 0.5 (expiry ≥ 60 days, at most 99.5% of NAV in premium), then adjusts the held call by whole contracts when 0.5 off.

## Exit

- O1 closes the calls on a re-strike with nothing wanted; O1b rolls under 45 days or outside 0.30-0.85 delta, and adjusts toward 0 when nothing is wanted.

## Sizing

- Options decide once a session in the last 45 minutes (15:15-15:45 ET): the listed QQQ monthly and strike nearest the model's, whole contracts (under one skipped), a structure as one multi-leg package, marketable limits.
- The core trades market-on-close on the equity less the options' value; a $1,000,000 book.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.
- The live QQQ quote and option chain; a model surface from VXN and the VIX 9-day / 3-month / 6-month ratios at today's levels; Black-Scholes with a 0.55% dividend.

## Variants

| Row | Calls | Re-sizing |
|---|---|---|
| `apex_o1_convex` | re-struck monthly or 0.5 off | close and reopen |
| `apex_o1b_convex_incremental` | rolled < 45 days or delta outside 0.30-0.85 | adjust the held call |

## Code

- **Master desk**: `sleeves/apex/apex_options.py`, `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_book.py`, `sleeves/apex/vendor/apex/opt_strategies.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
