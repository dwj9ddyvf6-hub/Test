# Microcap snapback (weekly)

Each Friday, ranks the genome's thinnest tenth for wide daily ranges after a 20%+ 13-week drop away from the 52-week low, buys Monday and holds 91 days.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities (microcaps) |
| **Timeframe** | 1w · 1d |
| **Universe** | Bottom tenth of the 1,838-name genome by weekly dollar volume |
| **Style** | Mean reversion |
| **Status** | live |

## Entry

- Band: the bottom 10% of the genome by trailing 52-week mean weekly dollar volume (at least 9 names).
- Flagged: 20-day mean daily range / close in the band's top third, a 13-week return ≤ -20%, and distance from the 52-week low not in the bottom third; widest range first.
- Ranks Friday after 16:35 ET once most names carry the day's bar; buys Monday from 10:35 ET; not a name exited within 91 days.

## Exit

- Sold 91 days after the Monday fill; no stop.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 150 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars of the genome (300, cached), desk quotes.

## Code

- **Master desk**: `sleeves/femto/sleeve_core.py`; not in this repo: `desk/sleeves/femto/snapback.py`
- **Midna v3**: `sleeves/snapback.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): at most 10 positions.
