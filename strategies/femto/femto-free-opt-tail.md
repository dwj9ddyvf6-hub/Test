# Tail put after a -3% day

When SPY is down 3% or more on the session, buys one SPY put (delta 0.50-0.65, 21-35 days) and exits in five sessions or at half the premium.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) free-paper option descendants, via Femto-lean |
| **Asset** | ETF options |
| **Timeframe** | 1d (5-minute passes) |
| **Universe** | SPY (SPY / QQQ for the pair) |
| **Style** | Tail hedge |
| **Status** | blocked |

## Entry

- SPY's session return (live mid over the last close) ≤ -3%.
- The put with |delta| 0.50-0.65, 21-35 DTE, expiring 7+ days past the 5-session exit; nearest expiry, then delta nearest 0.575; 1 contract at the ask, once per session.
- Sent only while the market is open, on fresh indicative quotes (source ≤ 90 s, receipt ≤ 30 s); a package's max loss must fit its risk cap and the shared $100,000 pool.

## Exit

- Five sessions, or the mark at half the fill; sold at the bid.

## Sizing

- 1 contract.

## Data

- SPY's last close and live quote, the desk's SPY put chain.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_opt_tail.py`, `desk/sleeves/femto/free_opt_core.py`, `desk/vendor/aurelia/free_options.py`, `desk/feedlib/free_options_inputs.py`
- **Midna v3**: `sleeves/free_opt_tail.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): refuses a put expiring on or before the entry session.
