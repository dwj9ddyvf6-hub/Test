# High-IV iron condor

Sells a 16-delta iron condor 30-45 days out on 13 high-volatility names when IV rank ≥ 50 and VIX ≤ 35, with no earnings due within 45 days.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | 13 high-volatility names |
| **Style** | Premium selling |
| **Status** | waiting |

## Entry

- IV rank ≥ 50 on the at-the-money call IV (30-45 DTE) over its last 252 stored readings (60 needed); VIX ≤ 35; no earnings in the next 45 days on a fresh calendar; at most 3 condors.
- Condor: one 30-45 DTE expiry; shorts nearest 0.16 Black-Scholes delta, wings nearest 0.05 beyond; all four legs two-sided within 10% of mid; net credit > 0; max loss on the wider wing.

## Exit

- Half the credit captured, a loss of 2× the credit, ≤ 7 DTE, 21 days held, a short leg deep in the money, or earnings entering the window.

## Sizing

- 1% of the book on the max loss, at most 25 contracts.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars, the desk's 30-45 DTE chains and quotes, the earnings calendar, VIX, stored IV history.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/iron_condor.py`
- **Midna v3**: `sleeves/iron_condor.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the loss stop is the smaller of 2× the credit and half the condor's max loss.
