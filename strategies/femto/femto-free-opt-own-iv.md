# Own-IV straddle

Buys an at-the-money SPY straddle when its own realized-volatility forecast beats implied volatility by 2 points, for 10 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean |
| **Asset** | ETF options |
| **Timeframe** | 1d (5-minute passes) |
| **Universe** | SPY (SPY / QQQ for the pair) |
| **Style** | Volatility |
| **Status** | waiting |

## Entry

- Straddle on the nearest 21-35 DTE expiry at least 7 days past the 10-session exit, when the HAR realized-vol forecast to expiry exceeds the straddle's mean implied vol by 2 points.
- Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool.

## Exit

- 5 minutes before the close of the 10th session, or expiry; both legs close together.

## Sizing

- 1 straddle; max loss and risk cap = the natural debit.

## Data

- SPY daily closes (760) and the desk's SPY chain with IVs.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_opt_own_iv.py`, `desk/sleeves/femto/free_opt_core.py`, `desk/vendor/aurelia/free_options.py`, `desk/feedlib/free_options_inputs.py`
- **Midna v3**: `sleeves/free_opt_own_iv.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the package must carry the forecast and IV and pass the 2-point test itself.
