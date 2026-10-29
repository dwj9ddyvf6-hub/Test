# PRZM Zero recreation (SPY)

Recreation of the PRZM Zero engine from the public record only: signed SPY options prints are weighted and combined into a five-driver score with hysteresis entries. Parked at install: no desk producer serves a signed same-day SPY options print tape, so the sleeve ledgers the price driver only and trades nothing.

| | |
|---|---|
| **Family** | Muse |
| **Source** | PRZM (przm.space) public record: Flight Manual V201 and the public client fallback engine, recreated per PRZM-RECREATION-SPEC-2026-10-29 |
| **Asset** | SPY shares (signal engine) |
| **Timeframe** | 1m |
| **Universe** | SPY |
| **Style** | Options flow score |
| **Status** | Midna's desk only; parked, waiting on a signed print tape route |

## Entry

- Print weights: 0 mid or no flag; 0.15 lottery wings; 0.2 insurance; 0.5 deep in the money; else 1. Multipliers: sweep x1.35, opening x1.25, closing x0.7; chasing x0.55 and contrarian x1.25 when the 5-candle move exceeds 0.8 vol units.
- Score: F = 0.3 SES + 0.4 30M + 0.22 10M + 0.08 5M, persistence and price-agreement adjustments, pin and run adjustments.
- Hysteresis: entry at absolute score 25 or more, flip at opposing 35 or more, drop below 8 plus 600,000 ms; window 09:45 to 15:45 ET (recreated hard gate).

## Exit

- Per the hysteresis rules above; sign-only 30-minute grading counts right and wrong calls.

## Sizing

- Parked: no positions are taken in the waiting state.

## Data

- Needs a signed same-day SPY options print tape (bull, sweep and opening flags). That route does not exist on this desk yet; that is the parked reason.

## Code

- **Midna v3**: `sleeves/przm_zero.py`, `adapters3/przm_zero.py`

## Notes

- Provenance labels per rule (extracted, inferred, recreated) are frozen in the desk spec; no PRZM performance figure is used anywhere.
- Catalog provenance: muse-desk-v3 commit bc4fd4421a06268f481713283d9f07e9221e995c, config/sleeves.json row przm_zero (parked), added 2026-10-29 to close the catalog diff of that date.
