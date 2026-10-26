# APEX QQQ benchmark

Holds QQQ at 1× every session: the benchmark of the APEX study, with its baselines recorded beside it.

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), APEX-NDX v1.0 benchmark |
| **Asset** | US ETFs |
| **Timeframe** | 1d |
| **Universe** | QQQ |
| **Style** | Benchmark (buy and hold) |
| **Status** | live |

## Entry

- Nasdaq-100 exposure 1× every session.

## Exit

- None: always fully invested.

## Sizing

- Market-on-close in the next session (orders from the open to 20 minutes before the close): the whole book in QQQ.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close.

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/strategies.py`, `sleeves/femto/vendor/aurelia/features.py`

## Notes

- Each decision also records the baselines: QQQ, 2× and 3× daily reset, SMA200 at 1× and 3×, the trend score at 1× and 3×, and 30% volatility targeting up to 3×.
