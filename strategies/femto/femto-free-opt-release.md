# Release straddle (CPI, jobs, FOMC)

On a session before a verified CPI, jobs report or FOMC statement, buys an ATM SPY straddle and exits the session after.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean |
| **Asset** | ETF options |
| **Timeframe** | 1d (5-minute passes) |
| **Universe** | SPY (SPY / QQQ for the pair) |
| **Style** | Event volatility |
| **Status** | waiting |

## Entry

- A verified public event dated to today's session (CPI and the Employment Situation from FRED's release calendar, the FOMC statement from the Fed's calendar).
- Straddle on the nearest expiry after the session that follows the event, within 45 days.
- Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool.

## Exit

- 5 minutes after the open of the session after the event, or expiry.

## Sizing

- 1 straddle; max loss and risk cap = the natural debit.

## Data

- The release calendar job (FRED and Fed calendars), the desk's SPY chain.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_opt_release.py`, `desk/sleeves/femto/free_opt_core.py`, `desk/vendor/aurelia/free_options.py`, `desk/feedlib/free_options_inputs.py`
- **Midna v3**: `sleeves/free_opt_release.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): both legs must pass the family's package-integrity tests.
