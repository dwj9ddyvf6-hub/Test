# LEAPS momentum with covered calls

Holds a deep in-the-money LEAPS call on each name of the six-month momentum book and sells ~25-delta calls against it (a poor man's covered call).

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | Equity options |
| **Timeframe** | 1d (hourly checks) |
| **Universe** | The momentum book's names (114-name swing basket) |
| **Style** | Momentum (options) |
| **Status** | blocked |

## Entry

- Follows the Femto momentum book (fresh within 7 days): one LEAPS per held name, at most 8.
- LEAPS: the nearest expiry ≥ 365 days, the strike nearest 0.80 × spot; spread ≤ 5% of mid; a limit at the ask.
- Short call: the nearest 25-38 DTE expiry, the first strike ≥ max(spot × (1 + 0.67 × 30-day vol), LEAPS breakeven × 1.02); spread ≤ 5%; sold at the bid.

## Exit

- LEAPS: the name leaves the momentum book, ≤ 60 DTE, or the mid 30% under the premium paid.
- Short call: rolled at ≤ 21 DTE or when the stock trades within 3% of its strike.

## Sizing

- 1 contract per 100 shares of the momentum position (at least 1), premium ≤ 5% of the book.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The momentum sleeve's book, split-adjusted daily bars (35), LEAPS (365-1,500 DTE) and 25-38 DTE call chains, option quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/leaps_momentum.py`
- **Midna v3**: `sleeves/leaps_momentum.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): it walks the expiry's strikes nearest first until one passes the quote gate.
