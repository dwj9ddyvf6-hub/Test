# apex-c2-sector-kings: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "APEX C2: Sector Kings", type market timing and rotation, family apex, style "Sector momentum rotation", universe "XLK, XLF, XLE, XLV, XLP, XLI, XLB, XLU, XLY, BIL", asset class US ETFs, timeframe "1d (monthly picks)", creator "APEX research desk (Cursor2), round 3 C2". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `apex-c2-sector-kings` (`docs/CATALOG.json`): card `strategies/apex/apex-c2-sector-kings.md`, status live.
- Alias: `apex_c2_sector_kings`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start and searched by filename for the canonical id, its alias and its distinguishing tokens, across sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, laz_sleeves/, config/ and docs/; the Silicon, quant-research-backup and Midna trees in this run's workspace were searched the same way. The code is already in Test; no distinct code for this strategy was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Each month holds the two strongest uptrending sector SPDRs, volatility-targeted to 25% (at most 2x).

## Full algorithm

From `strategies/apex/apex-c2-sector-kings.md`, in evaluation order:

1. Each month's first session: of the 9 sector SPDRs (XLK, XLF, XLE, XLV, XLP, XLI, XLB, XLU, XLY), take the 2 with the best 126-day return among those above their 200-day average, equal weight; none qualifying holds cash.
2. Scale: x min(2, 25% / the HAR forecast of the held basket's volatility).
3. Each weight moves only on a change of 0.20 or more, a session after the decision.
4. Exit: a sector leaves at the next month's pick; no stop.
5. Sizing: sector ETFs one for one (up to 2x in all, on margin); idle capital in BIL. Shares = floor(weight x book equity / the last close), frozen per decision; debits pay 7.75% a year.

## Files in this repo

- This package: `docs/APEX_C2_SECTOR_KINGS-RECREATE.md`
- Strategy card: `strategies/apex/apex-c2-sector-kings.md`
- Code (already in Test): `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/round3.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: XLK, XLF, XLE, XLV, XLP, XLI, XLB, XLU, XLY, BIL. Timeframe: 1d (monthly picks). Asset class: US ETFs.
- Book: $100,000.

## Data inputs

- Yahoo adjusted closes of the 9 sector SPDRs and ^IRX.

## Install and run

1. Clone the Test repo.
2. Read `strategies/apex/apex-c2-sector-kings.md` and the matching section of `docs/verify/apex.md`.
3. Open the code files listed in Files and locate this strategy's row / study.
4. Provide the data inputs listed above.
5. Run on the recorded cadence and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- Exactly the 2 best 126-day returns among sectors above their 200-day average are held, equal weight; if none qualifies, the book holds cash (BIL).
- The basket scale is exactly min(2, 25% / the HAR forecast of the held basket's volatility) and never exceeds 2x.
- No weight change smaller than 0.20 is traded, and changes take effect a session after the decision.
- A held sector leaves only at the next month's pick; there is no stop.
