# RSI(2) pullback call spreads

On the RSI(2) pullback signal, buys an 8%-wide call debit spread 14-30 days out and exits at half its max profit, 7 DTE or RSI(2) > 70.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | 41-name old-desk basket |
| **Style** | Mean reversion (options) |
| **Status** | waiting |

## Entry

- Signal on completed closes: RSI(2) < 10 and close > SMA200 (200+ bars).
- Spread: the nearest expiry 14-30 days out; long = the last strike ≤ the close, short = the first strike ≥ long × 1.08; long-leg spread ≤ 10% of mid; debit > 0; at most 5.

## Exit

- Value - debit ≥ 50% of max profit, ≤ 7 DTE, or RSI(2) > 70.

## Sizing

- Contracts = 0.25% of the book / (debit × 100).
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (260), the desk's 14-30 DTE call chains and quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/rsi_meanrev_options.py`, `desk/sleeves/femto/rsi_meanrev.py`
- **Midna v3**: `sleeves/rsi_meanrev_options.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no spread whose debit is over half its width.
