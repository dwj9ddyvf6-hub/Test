# Kraken ENJ order-book imbalance (spot)

Buys ENJ when Kraken's book is tight and bid-heavy, and sells on a depth flip, a wide spread or after 24 hours.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) ENJ spot row; order logic designed for Midna's v3 desk |
| **Asset** | Crypto spot |
| **Timeframe** | 1h checks |
| **Universe** | ENJ/USD (Kraken) |
| **Style** | Order-book imbalance |
| **Status** | Midna's desk only |

## Entry

- Long when the spread ≤ 50 bps and the top-10 bid depth ≥ 2× the ask depth; one position.

## Exit

- Sells at the bid when the ask depth ≥ 2× the bid depth, the spread > 200 bps, or 24 hours have passed.

## Sizing

- floor(min(equity, $10,000) / ask), at least 1, at the ask.

## Data

- Kraken ENJ/USD depth (top 10 levels).

## Code

- **Midna v3**: `sleeves/free_kraken_enj_spot.py`. Logic authored to a locked design under the owner's 2026-10-24 ruling

## Notes

- Only Midna's desk trades it; the master desk's ENJ row is a watch row with no orders.
