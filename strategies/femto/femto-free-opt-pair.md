# SPY / QQQ residual option pair

When QQQ's residual against a frozen SPY hedge is beyond 2 sd, buys ATM options on both sides toward the mean for 10 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean |
| **Asset** | ETF options |
| **Timeframe** | 1d (5-minute passes) |
| **Universe** | SPY (SPY / QQQ for the pair) |
| **Style** | Relative value |
| **Status** | waiting |

## Entry

- Hedge from the 61 common completed closes before the latest: beta of QQQ on SPY returns; signal = the latest residual |z| > 2.
- z > 2 buys the QQQ ATM put and SPY ATM calls; z < -2 the reverse; common expiry 30-60 DTE, 7+ days past the exit; SPY contracts = round(|beta| × QQQ spot × delta / (SPY spot × delta)).
- Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool.

## Exit

- 10 sessions; a failed leg closes the filled leg.

## Sizing

- Max loss and risk cap = the legs' total ask.

## Data

- SPY and QQQ completed closes; both chains.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_opt_pair.py`, `desk/sleeves/femto/free_opt_core.py`, `desk/vendor/aurelia/free_options.py`, `desk/feedlib/free_options_inputs.py`
- **Midna v3**: `sleeves/free_opt_pair.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the second leg's size is the rounded hedge ratio.
