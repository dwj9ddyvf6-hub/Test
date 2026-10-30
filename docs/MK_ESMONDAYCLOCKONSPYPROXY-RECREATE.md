# mk-esmondayclockonspyproxy: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "ES Monday clock (SPY)", type market timing and rotation, family milkman, style "Calendar", universe "SPY", asset class US ETF, timeframe "1m (06:00-16:00 ET)", creator "Milkman Trades (milkmantrades.com), ES Monday; the Milkman v2 study". Algorithm grade PARTIAL, gaps as for QLD above; filled here from the Test card and code.
- Test catalog entry `mk-esmondayclockonspyproxy`: card `strategies/milkman/mk-esmondayclockonspyproxy.md`, status off: 1.
- Alias: `mk_esmondayclockonspyproxy`.
- Code search (this package): fresh trees at batch start for Test (sleeves/, strategies/, packages/, adapters/, adapters3/, desk3/, integration/), Silicon, quant-research-backup and Midna were searched for the canonical id, its aliases and family terms. 

## What this strategy is

Times SPY from 06:00 to 16:00 ET each Monday, long and short; recorded only, as its entry falls outside the desk's trading session.

## Full algorithm

From `strategies/milkman/mk-esmondayclockonspyproxy.md`, in evaluation order:

1. Each Monday with a full session: at the open of the first 1-minute SPY bar at or after 06:00 ET (within 5 minutes), record a long lane and a short lane entry.
2. Exit: at the open of the first bar at or after 16:00 ET, both lanes.
3. Sizing / routing: both legs are recorded as observations only; the desk routes equities in the regular session only and the two lanes would net flat. No traded size is recorded on the card: traded sizing is not in the record.

## Files in this repo

- This doc: `docs/MK_ESMONDAYCLOCKONSPYPROXY-RECREATE.md`
- Strategy card: `strategies/milkman/mk-esmondayclockonspyproxy.md`
- Code (already in Test): `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: SPY. Timeframe: 1m (06:00-16:00 ET). Asset: US ETF.
- Status in catalog: off. No traded book size is recorded for this recorded-only lane.

## Data inputs

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Install and run

1. Clone the Test repo.
2. Read this doc and the strategy card named in Files.
3. Open the code files listed in Files and locate this strategy's sleeve / row.
4. Provide the data inputs listed below.
4a. Keep the sleeve off / recorded-only unless the desk's regular-session routing rule changes; do not route the 06:00 entry as a live equity order.
5. Run as described in Configuration / Full algorithm and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- On a full-session Monday, entries are timestamped at the first 1-minute bar at or after 06:00 ET (within 5 minutes), one long and one short.
- Exits are timestamped at the first bar at or after 16:00 ET.
- No live equity order is produced by this lane.
