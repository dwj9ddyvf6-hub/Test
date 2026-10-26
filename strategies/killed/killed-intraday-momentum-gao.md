# Intraday momentum (Gao et al.)

At 15:30 ET goes long or short SPY and QQQ in the direction of the first half hour's return, and exits at the close.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | Gao, Han, Li and Zhou (2018) market intraday momentum; a killed study of the old Alpaca swing desk |
| **Asset** | US ETFs |
| **Timeframe** | 5m |
| **Universe** | SPY, QQQ |
| **Style** | Intraday momentum |
| **Status** | live |

## Entry

- First-half-hour return: the 09:55 bar's close over the 09:30 open, minus 1, on 5-minute bars (all six first-window bars, with volume).
- From 15:30 ET: long when it is positive, short when negative; no trade on half-days or a zero return.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Out market-on-close the same day.

## Sizing

- $50,000 per symbol, fractional shares on both sides.

## Data

- 5-minute bars (120) and quotes.

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/intraday.py`, `sleeves/killed/common.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)

## Notes

- The master desk trades the short side; the old desk's long-only rail is dropped.
