# Beaten-down weekly qualifiers

Each Friday, takes the week's M2 qualifiers at least 20% under their 52-week high, ranks them by how many of 9 frozen confluence rules fire, buys Monday and holds 13 weeks.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | The weekly M2 qualifier list |
| **Style** | Weekly signal, value |
| **Status** | waiting |

## Entry

- Candidates: the weekly M2 qualifier file (the old desk's Tensor Anna weekly replica with its feature blocks), written after Friday's close.
- Selected: close ≤ 80% of the 52-week high (weekly closes); ranked by how many HOLD9 rules fire (each a 3-feature confluence).
- Buys Monday from 10:20 ET at a fresh mid while the desk fear composite is ≥ 55 (it fails open); waits on the last 5 sessions of the year, FOMC days and the session before, and unknown or stale VIX.

## Exit

- Time exit 91 days (13 weeks) after the fill, sold in a Monday fill at a fresh mid; no stop.

## Sizing

- Budget = 30% of the book less held and working notional, split over the week's selected names; whole shares at mid + 25.5 bps, at least 1; at most 10 positions.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The M2 weekly qualifier file, VIX, the fear composite, desk quotes.

## Code

- **Master desk**: `sleeves/killed/feedlib/m2.py`; not in this repo: `desk/sleeves/femto/beatendown.py`, `desk/sleeves/femto/m2_core.py`
- **Midna v3**: `sleeves/beatendown.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): a candidate with no HOLD9 rule firing is skipped.
