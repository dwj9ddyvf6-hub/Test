# Legend's EMA (trend-day fade)

After a trend day whose 15-minute bars never touched their EMA(20), trades at the next open back toward that EMA, flat by the close: QQQ with a half-ATR stop on Femto-lean, SPY without a stop in the Milkman study.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Milkman Trades' Legend's EMA, via the old Alpaca swing desk and Femto-lean; also the Milkman v2 study |
| **Asset** | US ETFs |
| **Timeframe** | 15m · 1d |
| **Universe** | QQQ · SPY |
| **Style** | Intraday mean reversion |
| **Status** | 2 waiting |

## Entry

- Setup: the prior regular session's 15-minute bars all above (or all below) their EMA(20) without touching it, and |close - open| / range at least 0.7686 (Femto-lean) or its 2000-2012 80th percentile (the Milkman study).
- At the open, toward the EMA: short when the open is above it, long when below; one trade a session. Femto-lean enters 09:30-09:45 ET at the open print and cancels after 240 s unfilled.

## Exit

- Femto-lean: take-profit at the EMA (refreshed once it moves $0.20); stop 0.5 × ATR(14) of daily ranges from the fill; flat at 15:59 ET (5 minutes before an early close).
- Milkman study: out at the first touch of the latest completed 15-minute bar's EMA, else at the close; no stop.

## Sizing

- Femto-lean: shares = 0.25% of the book / (0.5 × ATR14).
- Femto-lean: each sleeve trades its own $100,000 book unless its spec row names another.
- Milkman study: $10,000 a trade on a $1,000,000 book, every trade taken.

## Data

- Yahoo 15-minute bars (260), split-adjusted daily bars (40), the open print.
- Milkman study: Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Variants

| Book | Symbol | Trend day | Stop | Size | Rows |
|---|---|---|---|---|---|
| Femto-lean (master desk) | QQQ | ≥ 0.7686 | 0.5 × ATR | 0.25% risk | `femto_legends_ema` |
| Midna v3 | QQQ | ≥ 0.7686 | 0.5 × ATR | 0.25% risk | `legends_ema` |
| Milkman study (master desk) | SPY | ≥ the 2000-2012 80th percentile | none | $10,000 | `mk_legendsemaintradayproxy` |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/legends_ema.py`
- **Midna v3**: `sleeves/legends_ema.py`
- **Master desk (Milkman study)**: `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no entry when the open is less than the half-ATR stop away from the EMA.
- Milkman's rule is on NQ futures; Femto-lean trades it on QQQ, the Milkman study on SPY.
