# 20-day VWAP reversion call spreads

On the same VWAP signal, buys a call debit spread 14-30 days out and exits at half its max profit, the VWAP, 7 DTE or 21 days.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | 41-name old-desk basket |
| **Style** | Mean reversion (options) |
| **Status** | live |

## Entry

- The stock sleeve's signal: a close more than 2% under the 20-day VWAP.
- Spread: the nearest expiry 14-30 days out; long = the highest strike ≤ spot × 1.02, short = the first strike ≥ long × 1.06; long-leg spread ≤ 10% of mid; re-quoted debit > 0; at most 5 live.

## Exit

- Value (long bid - short ask) - debit ≥ 50% of max profit, ≤ 7 DTE, the close back at the VWAP, or 21 days since the fill; closed at the natural price.

## Sizing

- Contracts = 0.25% of the book / (debit × 100).
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars, the desk's 14-30 DTE call chains and option quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/ema_vwap_options.py`, `desk/sleeves/femto/ema_vwap.py`
- **Midna v3**: `sleeves/ema_vwap_options.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the VWAP exit fires only when the spread is worth at least its debit.
