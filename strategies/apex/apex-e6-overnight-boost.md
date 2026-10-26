# APEX E6: overnight boost

APEX-30 Nasdaq exposure plus 1× QQQ held from the close to the next open while the trend score is at least 0.5.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), APEX-NDX extension E6 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d (overnight boost) |
| **Universe** | QQQ, TQQQ, BIL |
| **Style** | Trend × volatility targeting, overnight |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- APEX-30: exposure = trend score × min(3, 30% / volatility).
- Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.
- Boost: +1× QQQ bought market-on-close with the core when the trend score is ≥ 0.5.

## Exit

- The boost is sold at the next session's first pass (09:30-09:40 ET), a marketable order.
- No stop: exposure follows the target; a trend score of 0 holds only T-bills (BIL).

## Sizing

- Boost shares = floor(book equity / the QQQ close).
- The core market-on-close, ordered 60 to 20 minutes before the close: Nasdaq up to 1× in QQQ, 1-3× QQQ + TQQQ, idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`

## Notes

- The source's boost ran to the official open; the desk sells at its first pass after the open.
