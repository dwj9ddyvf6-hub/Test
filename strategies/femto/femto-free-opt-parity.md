# SPY put-call parity package

When a conversion or reversal on SPY options and shares locks a positive residual after costs, trades the package and exits when the residual is gone or after five sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean |
| **Asset** | ETF options |
| **Timeframe** | 1d (5-minute passes) |
| **Universe** | SPY (SPY / QQQ for the pair) |
| **Style** | Arbitrage |
| **Status** | waiting |

## Entry

- Residuals from put-call parity on the SPY chain against shares financed at the 3-month T-bill rate; expiries 1-45 days, before the next ex-dividend date, strikes within 5% of spot; costs $0.03 an option leg each way.
- Entry: the pair with the largest positive residual: 100 shares with 1 put and 1 call, each at its side of a synchronized snapshot; the package's unwind cost ≤ 10% of the book.
- Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool.

## Exit

- Residual at or below zero (also the stop), five sessions, or the shared expiry.

## Sizing

- One package; a $100,000 book.

## Data

- The SPY chain (Cboe delayed or Alpaca indicative), SPY quotes, FRED DTB3.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_opt_parity.py`, `desk/vendor/aurelia/free_options.py`
- **Midna v3**: `sleeves/free_opt_parity.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- The source row is a model test with no order; the master desk trades the conversion / reversal its own research tree defines.
- Midna v3 expresses parity as a SPY box spread instead (entry edge $0.30 a share, exit $0.05, 1 box).
