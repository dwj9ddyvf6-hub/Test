# APEX C4: Broken Hedge

APEX-50F Nasdaq exposure, halved when Treasuries and gold stop hedging it, with idle capital in whichever of Treasuries, gold and the dollar hedges best.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), round 3 C4 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, IEF, GLD, UUP, BIL |
| **Style** | Trend × volatility targeting, correlation hedge |
| **Status** | live |

## Entry

- Trend score = the share of 6 bullish votes on the Nasdaq-100 total return (above its 50-, 100- and 200-day averages; up over 63, 126 and 252 days); volatility = a walk-forward HAR forecast of the next 5 days.
- APEX-50F: exposure = trend score × min(4, 50% / volatility), × 0.5 while the Nasdaq's 63-day correlations with both Treasuries and gold are above 0.20.
- Idle capital: the most negatively correlated of Treasuries (IEF), gold (GLD) and the dollar index (UUP) when that correlation is below -0.10, else BIL.
- Decided on the last finished session; the held exposure moves to the target only on a change of 0.20 or more, or to 0.

## Exit

- No stop: exposure follows the target; a trend score of 0 holds only the idle asset.

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), GC=F, DX-Y.NYB and ^TNX; recomputed after each close.
- IEF's total return; before IEF, a duration model on the 10-year yield (^TNX).

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/round3.py`, `sleeves/apex/vendor/apex/inventions.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)
