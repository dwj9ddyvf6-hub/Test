# APEX E5: semiconductor tilt

APEX-30 Nasdaq exposure with a third of it moved to SMH while semiconductors lead the Nasdaq and trend up.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), APEX-NDX extension E5 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, SMH, BIL |
| **Style** | Trend × volatility targeting, sector tilt |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- APEX-30: exposure = trend score × min(3, 30% / volatility).
- Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.
- Tilt: a third of the exposure in SMH while SMH's 126-day return beats the Nasdaq-100's and SMH is above its 200-day average.

## Exit

- The tilt returns to the Nasdaq when either test fails; no stop.

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), SMH adjusted closes; recomputed after each close.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)
