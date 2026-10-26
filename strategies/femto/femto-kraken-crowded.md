# Kraken crowded-long failure short (ADA / LINK)

Takes the breakdown short only when funding is crowded: positive and above its 90-day 75th percentile.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean |
| **Asset** | Crypto perpetual |
| **Timeframe** | 4h |
| **Universe** | ADA, LINK (Kraken) |
| **Style** | Breakdown short (funding filter) |
| **Status** | 2 live |

## Entry

- The breakdown signal (a 4h close under the prior 20 lows, entry at open(i+2)).
- Funding: ≥ 30 prints in 90 days; the latest > 0 and > the 90-day 75th percentile.

## Exit

- Covers at the live ask 16 hours after the entry was due.

## Sizing

- 1 contract (1 token), within 10% of a $100,000 budget.

## Data

- Kraken public 4h perpetual candles, hourly funding prints, the live ticker.

## Variants

| Coin | Rows |
|---|---|
| ADA | `femto_free_kraken_ada_crowded`; Midna v3 `free_kraken_ada_crowded` |
| LINK | `femto_free_kraken_link_crowded`; Midna v3 `free_kraken_link_crowded` |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_kraken_ada_crowded.py`, `desk/sleeves/femto/free_kraken_link_crowded.py`, `desk/vendor/aurelia/kraken.py`
- **Midna v3**: `sleeves/free_kraken_ada_crowded.py`
- **Midna v3 (LINK)**: `sleeves/free_kraken_link_crowded.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no entry when the latest funding print is more than 2 hours old.
