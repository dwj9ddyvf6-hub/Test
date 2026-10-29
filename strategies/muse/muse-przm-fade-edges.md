# PRZM Fade Edges recreation (SPY)

Recreation of PRZM Zero's Fade Edges state: in a pin regime (spot above the gamma flip), fade the session edges toward the gamma magnet; in a run, stand aside. Parked at install: the desk chain producer serves delta-only rows, so gamma levels cannot be computed.

| | |
|---|---|
| **Family** | Muse |
| **Source** | PRZM (przm.space) public record: Flight Manual V201 and the public client fallback engine, recreated per PRZM-RECREATION-SPEC-2026-10-29 |
| **Asset** | SPY shares, long and short |
| **Timeframe** | 1m |
| **Universe** | SPY |
| **Style** | Gamma regime fade |
| **Status** | Midna's desk only; parked, waiting on gamma and open interest chain data |

## Entry

- Gamma (recreated): per strike GEX = open interest x gamma x 100 x spot, calls positive and puts negative. Magnet: strike of largest absolute net GEX. Flip: strike where cumulative net GEX changes sign.
- Regime (extracted test): pin when spot is above the flip; run otherwise. No substitute regime test is permitted by the spec.
- In a pin: SPY within 0.05% of the session high with that high above the magnet enters short toward the magnet; mirrored at the low. One fade per edge per session, at most two open; entries 09:45 to 15:15 ET, edges first fadeable at 10:00 ET.

## Exit

- Target: the magnet. Invalidation: a 1-minute close 0.15% beyond the faded edge. A regime flip to run exits at once. Flat at 15:45 ET.

## Sizing

- Fixed $2,000 notional per fade (recreated mechanics).

## Data

- Needs chain rows carrying gamma and open interest; the current producer serves delta only (feed indicative). That is the parked reason.

## Code

- **Midna v3**: `sleeves/przm_fade_edges.py`, `adapters3/przm_fade_edges.py`

## Notes

- Catalog provenance: muse-desk-v3 commit bc4fd4421a06268f481713283d9f07e9221e995c, config/sleeves.json row przm_fade_edges (parked), added 2026-10-29 to close the catalog diff of that date.
