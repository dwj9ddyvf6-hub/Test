# TSMOM 12-1 ETF book

Every 21 sessions holds, in equal weights, each of 30 diversified ETFs whose 12-1 month return is positive; cash otherwise.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TSMOM forms study (scripts/tsmom-forms.ts), its ETF 12-1 book, ported line for line; a recorder made a book by the owner's D32 |
| **Asset** | US ETFs |
| **Timeframe** | 1d (every 21 sessions) |
| **Universe** | 30 diversified ETFs (equity, sector, bond, commodity, currency) |
| **Style** | Time-series momentum |
| **Status** | waiting |

## Entry

- Sign 12-1: the adjusted close 21 sessions back over the one 252 sessions before it, minus one, > 0; the panel is aligned to SPY's sessions and a name needs 260 valid sessions.
- Every 21 sessions from the book's first session, in the last 40 to 15 minutes of the session: equal weights over the names with a positive sign, as market-on-close orders.

## Exit

- A held name whose sign is no longer positive goes to cash at that rebalance (market-on-close); the weights drift in between; no stop.

## Sizing

- 1 / N of the book a long; $100,000 book.

## Data

- Yahoo daily bars (600 sessions) of the 30 ETFs on rebalance days, adjusted closes (the close when the provider gives none).

## Code

- **Master desk**: `sleeves/midna/monitor/midna_books.py`, `sleeves/midna/monitor/midna_mon.py`, `sleeves/galath/monitor.py`
- **Midna's TypeScript source**: `sleeves/midna/vendor/midna_mon/scripts/tsmom-forms.ts`, `sleeves/midna/vendor/midna_mon/src/lib/research/tsmom.ts`
- **Rule lines**: [docs/verify/midna.md](../../docs/verify/midna.md)

## Notes

- The recorder read seven momentum forms on this panel; Midna's study trades only its primary 12-1 form on it, so the row is converted as that book.
- A recorder until the owner's ruling D32 (2026-10-26) funded it as a paper book; its first live signal is pending.
