# mn-qld-weekly-timing: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "QLD weekly timing", type market timing and rotation, family midna, style "Trend filter", universe "QLD (QQQ signal)", asset class Leveraged ETF, timeframe "1w", creator "Midna's TypeScript desk (equity books), ported line for line to the master desk". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `mn-qld-weekly-timing` (`docs/CATALOG.json`): card `strategies/midna/mn-qld-weekly-timing.md`, status live: 1.
- Alias: `midna_qld_weekly_timing`.
- Code search (this package): fresh trees at batch start for Test (sleeves/, strategies/, packages/, adapters/, adapters3/, desk3/, integration/), Silicon, quant-research-backup and Midna were searched for the canonical id, its aliases and family terms. 

## What this strategy is

Holds QLD all-in while QQQ's weekly EMA(12) is above its EMA(26), switching at the open of each week.

## Full algorithm

From `strategies/midna/mn-qld-weekly-timing.md` and `sleeves/midna/qld.py`, in evaluation order:

1. Build QQQ weekly bars from adjusted daily history from 1990 (OHLC scaled by adjclose / close); a week is completed only as recorded in `completed_weeks` in the code.
2. Compute SMA-seeded EMA(12) and EMA(26) of weekly closes.
3. Decision: in the first regular-hours pass of each week (once per week; sleeve cadence 300s, schedule rth, state records the week decided), read the prior completed week: on = EMA(12) > EMA(26).
4. Entry: if on and QLD is not held, enter QLD at the live quote (ask or last), notional = cash / (1 + 0.1%); cost parameter COST = 0.001; book capital in code NAV = 100,000.
5. Exit: if not on (EMA(12) <= EMA(26)) and QLD is held, sell QLD at bid or last in that first pass of the week.
6. No other entry, exit, stop or target is in the code.

## Files in this repo

- This doc: `docs/MN_QLD_WEEKLY_TIMING-RECREATE.md`
- Strategy card: `strategies/midna/mn-qld-weekly-timing.md`
- Code (already in Test): `sleeves/midna/qld.py` (class QldWeeklyTiming, sleeve_id `midna_qld_weekly_timing`, params fast 12, slow 26, cost 0.001), plus `sleeves/midna/common.py`
- Rule lines: `docs/verify/midna.md` (QLD section, lines citing qld.py)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: QLD (QQQ signal). Timeframe: 1w. Asset: Leveraged ETF.
- Capital in code: 100,000. Cadence 300s, schedule rth, needs quotes for QLD and feed `midna_qld_daily`.
- State schema in code: week, on.

## Data inputs

- Yahoo QQQ and QLD daily history (adjusted, from 1990-01-01 as fetched by the producer feed in the code docstring).

## Install and run

1. Clone the Test repo.
2. Read this doc and the strategy card named in Files.
3. Open the code files listed in Files and locate this strategy's sleeve / row.
4. Provide the data inputs listed below.
4a. Ensure the `midna_qld_daily` producer feed is refreshed (the code docstring records a 12-hour refresh).
5. Run as described in Configuration / Full algorithm and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- EMA(12) > EMA(26) on the prior completed QQQ week produces exactly one QLD entry in the first regular-hours pass of the week, sized cash / 1.001.
- EMA(12) <= EMA(26) with QLD held produces an exit in that pass; with no holding it produces no order.
- A second pass in the same week produces no further decision (week state gate).
- EMAs are SMA-seeded as in `ema()` in qld.py.
