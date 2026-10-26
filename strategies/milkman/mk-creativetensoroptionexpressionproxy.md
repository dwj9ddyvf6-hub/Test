# Tensor fires as calls

Expresses tier-A weekly Tensor Cyan / Green fires with one-year at-the-money calls, $1,000 of premium each, sold after 52 weeks.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Galath research lab, TENSOR_CREATIVE option study |
| **Asset** | Equity options |
| **Timeframe** | 1w |
| **Universe** | 1,822 US stocks (the store_v1 survivors), their listed calls |
| **Style** | Tensor signal, options |
| **Status** | live |

## Entry

- Weekly fire: a closed weekly Tensor bar with a buy-cyan or buy-green marker (bar ≥ 60).
- Tier A: at least 2 of (close ≤ $14.94; that and a 60-day return ≥ 31%; ≥ 70% under the 252-day high; an SMH-sector name), not XLF, XLB, XLRE or XLU; 60-day realised volatility 5-400%; 20-day dollar volume ≥ $100,000.
- The listed call with the expiry nearest 52 weeks (≥ 75% of it) and the strike nearest the fire close, two-sided, bought the session after the fire week with a limit 2% over the ask for an hour; ask ≥ 2% of spot.

## Exit

- After 52 weeks (or the expiry's last session if sooner), a marketable order that session.

## Sizing

- Contracts = floor($1,000 / (ask × 100)), at least 1 unless one contract costs over $2,000; a $1,000,000 book.

## Data

- Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes).
- The desk's call chains, 250-800 days out.

## Code

- **Master desk**: `sleeves/milkman/galath.py`, `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)

## Notes

- The study priced the calls by Black-Scholes on realised volatility; the desk buys listed calls.
- The Tensor engine these lanes run (desk/vendor/galath_engine/) is not published in this repo.
