# APEX E7: turn-of-month boost

APEX-30 Nasdaq exposure plus 0.5× over each turn of the month while the trend score is at least 0.5.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), APEX-NDX extension E7 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, BIL |
| **Style** | Trend × volatility targeting, calendar |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- APEX-30: exposure = trend score × min(3, 30% / volatility), + 0.5 held over the turn of the month (its last session and the next month's first three) while the trend score is ≥ 0.5, at most 3×.
- Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.

## Exit

- The 0.5× leaves after the month's third session; no stop.

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
