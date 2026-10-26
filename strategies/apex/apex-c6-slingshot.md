# APEX C6: SLINGSHOT

APEX-50F Nasdaq exposure, lifted to 3× for 10 sessions after a 5% dip in a strong trend while yields rise.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), round 3 C6 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, BIL |
| **Style** | Trend × volatility targeting, dip boost |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- APEX-50F: exposure = trend score × min(4, 50% / volatility).
- Slingshot: trend score ≥ 4 of 6, the 10-year yield up more than 0.50 over 63 sessions and the Nasdaq-100 down ≥ 5% over 10 sessions lift exposure to at least 3× for 10 sessions.
- Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.

## Exit

- The boost ends after 10 sessions; no stop.
- No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL).

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/round3.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)
