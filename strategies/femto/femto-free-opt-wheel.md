# SPY 30-delta wheel

Sells a cash-secured 30-delta weekly SPY put; if assigned, sells 30-delta covered calls against the shares.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean |
| **Asset** | ETF options |
| **Timeframe** | 1d (5-minute passes) |
| **Universe** | SPY (SPY / QQQ for the pair) |
| **Style** | Options income |
| **Status** | waiting |

## Entry

- Put: nearest 7-14 DTE expiry, |delta| nearest 0.30, then the strike nearest spot; only when cash covers strike × 100; sold at the bid, once per session.
- After assignment: one call the same way against 100 free shares, once per session.
- Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool.

## Exit

- No early exit: expiry, or assignment (puts) and call assignment (calls).

## Sizing

- 1 contract; cash = the book's cash less the strike value of its short puts.

## Data

- The desk's SPY chain, the book's cash and shares.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_opt_wheel.py`, `desk/sleeves/femto/free_opt_core.py`, `desk/vendor/aurelia/free_options.py`, `desk/feedlib/free_options_inputs.py`
- **Midna v3**: `sleeves/free_opt_wheel.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no covered call below the shares' cost basis.
