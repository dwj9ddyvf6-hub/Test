# Teddy opening range breakout (SPY)

Trades SPY after a volume-qualified break of the 30-minute opening range, entering on a lower-volume pullback and a trigger bar, flat by 14:00 ET.

| | |
|---|---|
| **Family** | Muse |
| **Source** | X post by @ThiccTeddy, strategy from his posted video, installed by owner order 2026-10-28 |
| **Asset** | SPY shares, long and short |
| **Timeframe** | 5m (aggregated from 1m) |
| **Universe** | SPY |
| **Style** | Opening range breakout |
| **Status** | Midna's desk only |

## Entry

- Opening range: the first six 5-minute regular-session bars (09:30 to 10:00 ET); high and low fixed at 10:00 and never repainted.
- Qualification: a 5-minute bar closes beyond the range on volume at least 1.5x the mean opening-range bar volume, by 12:00 ET. Qualification alone does not enter.
- Entry: a pullback of 1 to 6 bars toward the broken edge, no bar closing back inside the range and every pullback bar below the breakout bar's volume, then a trigger bar above the last pullback bar's volume; triggers must start before 12:30 ET.

## Exit

- Stop beyond the pullback extreme; target the measured move or 2R, whichever is closer.
- A post-entry close back inside the range exits; hard flat at 14:00 ET.

## Sizing

- 0.25% of slice equity at risk per trade, 25% notional cap; whole shares.

## Data

- SPY 1-minute SIP bars aggregated deterministically into 5-minute bars (a bucket is emitted only when all 5 minutes are present).

## Code

- **Midna v3**: `sleeves/teddy_orb_spy.py`, `adapters3/teddy_orb_spy.py`

## Notes

- Edge unproven by design: the live paper record is the test; no backtest is claimed.
- Catalog provenance: muse-desk-v3 commit bc4fd4421a06268f481713283d9f07e9221e995c, config/sleeves.json row teddy_orb_spy, added 2026-10-29 to close the catalog diff of that date.
