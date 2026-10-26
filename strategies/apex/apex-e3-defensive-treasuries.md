# APEX E3 / v1.1: defensive Treasuries

APEX Nasdaq exposure with idle capital in 7-10-year Treasuries while they trend up, else T-bills: E3 at APEX-30, the v1.1 candidate at APEX-50F with a wide band.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), APEX-NDX extension E3 and the v1.1 candidate |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, IEF, BIL |
| **Style** | Trend × volatility targeting |
| **Status** | 2 live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- Exposure = trend score × min(max, target / volatility): E3 is APEX-30 (30%, 3×), v1.1 is APEX-50F (50%, 4×).
- Decided on the last finished session; the held exposure moves to the target only on a change of the band or more, or to 0: E3 0.20, v1.1 0.50.
- Idle capital in IEF while the 7-10-year Treasury total return is above its 200-day average, else BIL.

## Exit

- No stop: exposure follows the target; a trend score of 0 holds only the idle asset.

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX; recomputed after each close.
- IEF's total return; before IEF, a duration model on the 10-year yield (^TNX).

## Variants

| Book | Target volatility | Max exposure | Band | Row |
|---|---|---|---|---|
| E3 | 30% | 3× | 0.20 | `apex_e3_defensive_treasuries` |
| v1.1 candidate | 50% | 4× | 0.50 | `apex_v11_defensive_bond` |

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
