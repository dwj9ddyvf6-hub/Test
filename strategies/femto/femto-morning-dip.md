# Morning dip limit

Between 10:00 and 12:00 ET, after a calm 3-minute candle, rests a limit one ATR beyond its close and targets the candle's midpoint: QQQ long on Femto-lean, SPY both ways in the Milkman study.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Milkman Trades' Morning Dip Limit, via the old Alpaca swing desk and Femto-lean; also the Milkman v2 study |
| **Asset** | US ETFs |
| **Timeframe** | 3m |
| **Universe** | QQQ · SPY |
| **Style** | Intraday mean reversion |
| **Status** | 2 live |

## Entry

- A calm 3-minute candle (from 1-minute bars): efficiency ratio over 15 candles ≤ 0.35, in the 10:00-12:00 ET window (Femto-lean: starting in it, the last 16 candles healthy; the Milkman study: ending in it).
- Femto-lean: a DAY limit buy one tick under level = floor(close - ATR(14)), cancelled after 9 minutes; one order or position at a time.
- Milkman study: a limit 1 × ATR(14) beyond the close for 9 minutes, filled when a bar trades a cent through it; the long lane buys below the close, the short lane sells above; one order or position at a time.

## Exit

- Target = the signal candle's midpoint; stop = 1.5 ATR beyond the limit (at least 4 ticks); a 15-minute time stop; flat at 12:00 ET.
- The Milkman study also needs the target ≥ 2 cents past the limit, and counts only the stop in the fill bar.

## Sizing

- Femto-lean: shares = 0.25% of the book / the stop distance.
- Femto-lean: each sleeve trades its own $100,000 book unless its spec row names another.
- Milkman study: $10,000 a trade on a $1,000,000 book, every trade taken.

## Data

- Yahoo 1-minute bars with the extended session (420).
- Milkman study: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Variants

| Book | Symbol | Sides | Size | Rows |
|---|---|---|---|---|
| Femto-lean (master desk; Midna v3 wraps it) | QQQ | long | 0.25% risk | `femto_morning_dip`, `morning_dip` |
| Milkman study (master desk) | SPY | long and short | $10,000 | `mk_morningdiplimitproxy` |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk**: `sleeves/femto/morning_dip.py`
- **Midna v3**: `sleeves/morning_dip.py`. A wrapper only: it runs the strategy file through Midna's `_enh2` layer, neither of which is in this repo
- **Master desk (Milkman study)**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Milkman's rule is on NQ futures; Femto-lean trades it on QQQ, the Milkman study on SPY.
