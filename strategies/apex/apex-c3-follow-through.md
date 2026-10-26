# APEX C3: Follow-through

APEX-50F Nasdaq exposure, lifted to at least 2× for 20 sessions after a follow-through day out of a 10% correction.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), round 3 C3 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, BIL |
| **Style** | Trend × volatility targeting, follow-through boost |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- APEX-50F: exposure = trend score × min(4, 50% / volatility).
- Follow-through: once the Nasdaq-100 closes 10% under its 63-day high, the first session up ≥ 1.25% that closes at a 10-day high lifts exposure to at least 2× for 20 sessions; one per correction, re-armed after a new 63-day high.
- Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.

## Exit

- The boost ends after 20 sessions; no stop.
- No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL).

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/round3.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
