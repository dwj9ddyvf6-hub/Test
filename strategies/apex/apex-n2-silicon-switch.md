# APEX N2: Silicon Switch

Holds whichever of the Nasdaq-100 and the semiconductor index leads by 5 points over 126 days, at that index's own APEX-50F exposure.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), invention N2 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, SMH, BIL |
| **Style** | Trend × volatility targeting, relative strength switch |
| **Status** | live |

## Entry

- Switch: to the SOX when its 126-day return beats the Nasdaq-100's by more than 5 points; back when the Nasdaq-100 leads by more than 5.
- Exposure: APEX-50F of the index held (trend score × min(4, 50% / volatility) from its own votes and HAR forecast).
- Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.

## Exit

- No stop: a switch moves the whole exposure between the two indexes.

## Sizing

- Nasdaq exposure as QQQ / TQQQ; every other asset one for one in its ETF; idle capital in BIL; anything above the book's capital runs a margin debit.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^SOX and SMH; recomputed after each close.
- The SOX total return: ^SOX + 1% a year until SMH's history starts, then SMH's.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/inventions.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)
