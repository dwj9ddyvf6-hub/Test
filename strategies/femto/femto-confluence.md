# Winner confluence (weekly qualifiers)

Each Friday, buys the week's M2 qualifiers on which at least 2 of 9 frozen confluence rules fire, Monday, and holds 13 weeks.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | The weekly M2 qualifier list |
| **Style** | Weekly signal, confluence |
| **Status** | waiting |

## Entry

- Candidates: the weekly M2 qualifier file (the old desk's Tensor Anna weekly replica with its feature blocks), written after Friday's close.
- Selected: 2+ of the 9 HOLD9 rules fire on the daily bars before the rank day; most rules first.
- Buys Monday from 10:00 ET at a fresh mid; waits on the last 5 sessions of the year, FOMC days and the session before, and unknown or stale VIX; a slot sold that morning can be refilled.

## Exit

- Time exit 91 days (13 weeks) after the fill, sold in a Monday fill at a fresh mid; no stop.

## Sizing

- Budget = 30% of the book less held and working notional, split over the week's selected names; whole shares at mid + 25.5 bps, at least 1; at most 10 positions.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The M2 weekly qualifier file, VIX, desk quotes.

## Code

- **Master desk**: `sleeves/killed/feedlib/m2.py`; not in this repo: `desk/sleeves/femto/confluence.py`, `desk/sleeves/femto/m2_core.py`
- **Midna v3**: `sleeves/confluence.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the two anchored-VWAP rules (R5, R6) count once.
