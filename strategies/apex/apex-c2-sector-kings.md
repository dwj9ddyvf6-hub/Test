# APEX C2: Sector Kings

Each month holds the two strongest uptrending sector SPDRs, volatility-targeted to 25% (at most 2×).

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), round 3 C2 |
| **Asset** | US ETFs |
| **Timeframe** | 1d (monthly picks) |
| **Universe** | XLK, XLF, XLE, XLV, XLP, XLI, XLB, XLU, XLY, BIL |
| **Style** | Sector momentum rotation |
| **Status** | live |

## Entry

- Each month's first session: of the 9 sector SPDRs, the 2 with the best 126-day return among those above their 200-day average, equal weight; none qualifying holds cash.
- Scale: × min(2, 25% / the HAR forecast of the held basket's volatility).
- Each weight moves only on a change of 0.20 or more, a session after the decision.

## Exit

- A sector leaves at the next month's pick; no stop.

## Sizing

- Sector ETFs one for one (up to 2× in all, on margin); idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo adjusted closes of the 9 sector SPDRs and ^IRX.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/round3.py`, `sleeves/femto/vendor/aurelia/features.py`
