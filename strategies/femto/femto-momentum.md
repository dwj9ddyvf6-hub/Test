# Six-month momentum leaders

Holds the top tenth of liquid names by 126-session return, re-ranked every 63 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's momentum sleeve, via Femto-lean; Midna's TypeScript desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 114-name swing basket + SPY · Midna's swing basket |
| **Style** | Momentum |
| **Status** | 1 live · 1 blocked |

## Entry

- Liquid: last completed close ≥ $5 and 20-session mean dollar volume ≥ $1M; SOXL excluded; ranked by 126-session return; the top tenth (at least 1, at most 10) when 10+ names qualify.
- A review every 63 sessions sets the target to the new top tenth; between reviews the book holds.
- Femto: buys wait on a Friday after 14:00 ET, the last 5 sessions of the year, FOMC days and the session before, and when VIX is unknown, stale (> 4 days), above 32 or up 25% on the day, or SPY is down 8% over 20 sessions with VIX rising.
- Trades from 10:00 ET on fresh quotes.

## Exit

- A name leaves at the next review it is not in.
- Femto: a 40% breaker sells a name whose fresh mid is ≤ 60% of its entry.

## Sizing

- Femto: budget = 30% of the book less held and pending notional, split over the review target; whole shares at mid × (1 + 10, 25 or 50 bps by price), at least 1; at most 10 names.
- Midna: equal dollars = equity / names; floor(dollars / (price × (1 + cost))), cost 5-50 bps by price; sells first.
- Both books start at $100,000.

## Data

- Daily bars (~290 sessions), VIX, desk quotes.
- Midna: her daily panel (Yahoo adjusted closes).

## Variants

| Variant | Rows | Sizing | Buy gates | Breaker |
|---|---|---|---|---|
| Old swing desk (Femto-lean) | `femto_momentum`; Midna v3 `momentum` | 30% of the book, ≤ 10 names | calendar, VIX, SPY | 40% |
| Midna TypeScript | `midna_liquid_126_momentum` | the whole book, equal dollars | dropped on the master desk | dropped |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk**: `sleeves/femto/momentum.py`
- **Master desk (Midna's book)**: `sleeves/midna/context.py`, `sleeves/midna/common.py`
- **Midna v3**: `sleeves/momentum.py`. A wrapper only: it runs the strategy file through Midna's `_enh2` layer, neither of which is in this repo
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna's book is the lab cell "liquid names, 126 sessions, skip 0, top 10%, every 63"; the master desk drops her desk-wide gates (the same calendar / VIX / SPY gates, her red-day gate, the 40% breaker).
