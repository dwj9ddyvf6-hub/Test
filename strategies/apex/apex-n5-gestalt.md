# APEX N5: GESTALT analog engine

Sets Nasdaq leverage from the 150 most similar past market states: half-Kelly on their average forward 21-day excess return, up to 4×.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), invention N5 |
| **Asset** | US ETFs (incl. 3× leveraged) |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, BIL |
| **Style** | Analog (nearest-neighbour) forecast |
| **Status** | live |

## Entry

- State: trend score, log volatility and its 21-day change, the 252-day drawdown, the 21-day return, the 63-day change in the 10-year yield, VIX against its 252-day median, and semiconductors' 63-day return over the Nasdaq's.
- Every 5 sessions from 2001: the 150 nearest past states (z-scored distance) whose forward 21-day excess log return is known; their mean, annualised and shrunk halfway to the all-history mean.
- Leverage = 0.5 × that mean / max(volatility, 5%)², clipped to 0-4; held between refits.
- The held exposure moves to it only on a change of 0.20 or more, or to 0.

## Exit

- No stop: a negative analog mean takes the exposure to 0.

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): Nasdaq exposure up to 1× is QQQ, 1-3× is QQQ + TQQQ (QQQ + 3 × TQQQ = L), above 3× TQQQ alone at L / 3 on margin; idle capital in BIL.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), ^TNX, ^VIX, ^SOX and SMH; recomputed after each close.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/inventions.py`, `sleeves/apex/vendor/apex/strategies.py`
- **Rule lines**: [docs/verify/apex.md](../../docs/verify/apex.md)
