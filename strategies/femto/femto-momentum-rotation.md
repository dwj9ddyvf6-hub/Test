# 60-day momentum rotation

Each Monday, holds the five basket names with the best 60-day return at 20% each, and sells any that fall out of the top 10.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1d (weekly) |
| **Universe** | 41-name old-desk basket |
| **Style** | Momentum rotation |
| **Status** | live |

## Entry

- Ranks names with ≥ 66 bars by 60-day return; buys the top 5 not held while fewer than 5 are held or working.
- Rebalances when 7+ days have passed since the last one; the pass runs Monday 09:35 ET.

## Exit

- Sells a held name ranked worse than 10th.
- A 25% disaster stop below the fill. The engine holds the disaster stop, measured from the actual fill.

## Sizing

- 20% of the book a name at the last close, whole shares.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- Split-adjusted daily bars (100).

## Code

- **Master desk**: `sleeves/femto/momentum_rotation.py`
- **Midna v3**: `sleeves/momentum_rotation.py`. A wrapper only: it runs the strategy file through Midna's `_enh2` layer, neither of which is in this repo
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)
