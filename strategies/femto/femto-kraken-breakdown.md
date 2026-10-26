# Kraken breakdown short (ADA / LINK)

Shorts the perpetual when a 4-hour close breaks below the prior 20 bars' lows, entering two bars later, and covers 16 hours after entry.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | Aurelia (Agentic-Trading-Desk) Kraken research books, via Femto-lean |
| **Asset** | Crypto perpetual |
| **Timeframe** | 4h |
| **Universe** | ADA, LINK (Kraken) |
| **Style** | Breakdown short |
| **Status** | 2 live |

## Entry

- Signal: a completed 4h candle whose close is below the lowest low of the 20 bars before it; ≥ 22 bars.
- Entry: short 1 contract at the live bid once open(i+2) (8 hours after the signal opened) has arrived; one short at a time.

## Exit

- Covers at the live ask 16 hours after the entry was due.

## Sizing

- 1 contract (1 token), within 10% of a $100,000 budget.

## Data

- Kraken public 4h perpetual candles and the live ticker.

## Variants

| Coin | Rows |
|---|---|
| ADA | `femto_free_kraken_ada_breakdown`; Midna v3 `free_kraken_ada_breakdown` |
| LINK | `femto_free_kraken_link_breakdown`; Midna v3 `free_kraken_link_breakdown` |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/free_kraken_ada_breakdown.py`, `desk/sleeves/femto/free_kraken_link_breakdown.py`, `desk/vendor/aurelia/kraken_clock.py`
- **Midna v3**: `sleeves/free_kraken_ada_breakdown.py`
- **Midna v3 (LINK)**: `sleeves/free_kraken_link_breakdown.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): no short once the live bid is back at or above the prior 20-bar low.
