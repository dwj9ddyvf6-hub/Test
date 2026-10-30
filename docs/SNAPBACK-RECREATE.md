# snapback: Recreation package

Provenance: The old Alpaca swing desk, via Femto-lean (Source row in strategies/femto/femto-snapback.md in this repo).

## What this sleeve is
This is a weekly mean-reversion sleeve over the thinnest-traded tenth of the genome universe: it flags names with wide daily ranges after a 13-week drop of at least 20 percent that are not pinned at their 52-week low, buys them at 1 percent of equity each (at most 10 positions), and holds 91 days. Sources: desk sleeves/snapback.py (BAND_FRAC=0.10, HOLD_DAYS=91, COST_BPS_SIDE=0.015 as a study parameter kept as data, MAX_POSITIONS=10; CONFIG cadence_s=300) and desk3/enhance26.py (snapback fresh_price_reprice gate).

## Full algorithm
Evaluation order in desk sleeves/snapback.py Snapback.signal(bars, slice_state, context); bars are the DAILY bars and context.extra carries weekly bars, sleeve_state and last_exit.
1. Time exits first: for each held position with an entry_date, if (today - entry_date).days >= 91 and qty > 0, emit an exit Intent for the full quantity at the last daily close, reason naming snapback time exit with the held days. There is no price stop.
2. If equity is at or below 0 or no weekly bars are supplied, return only the exits.
3. Signal week: the week ending the most recent Friday on or before today. compute_flags(weekly, daily, friday): weekly bars are bucketed by Monday; a name needs at least 52 prior Mondays (widx >= 51); its trailing-52-week mean weekly dollar volume is sum(close x volume over the 52 weeks) / 52. Candidates sort ascending by that mean and the band is the bottom max(9, int(n x 0.10)) names.
4. Features per band name (the name must have a bar in the signal week's Monday bucket): spread = 20-day mean of (high - low) / close over the daily bars up to the signal week; beat_run13 = the 13-week return (close vs the close 13 weeks earlier) is at or below -0.20; near_low = (close - 52-week low close) / 52-week low close over the trailing 52 weekly closes.
5. Flag rule (tercile_flags: sorted values split into lo / mid / hi thirds, empty if fewer than 3 names): a name is flagged only if its spread tercile is hi AND beat_run13 is true AND its near_low tercile is NOT lo. Flagged names rank by spread descending.
6. Entries: skip names already held; skip a name whose last_exit is less than 91 days ago (rebuy de-overlap); price is the signal week's weekly close; qty = int((equity x 0.01) // price); qty below 1 emits nothing (no forced floor). The entry Intent carries ExitRule time_bars 91 and a reason naming the flag values (spread, ret13, near_low, wkvol).
7. ENH position cap (ENH-SNAPBACK-20261024, default ON; OFF via extra[snapback_enhance][position_cap]=False restores taking every flagged name): count the open book plus this pass's entries; flagged names beyond MAX_POSITIONS=10 are not taken, in spread-descending order.
8. Adapter-layer gate (desk3/enhance26.py, ENH-B26-20261024, default ON; switch extra[snapback_enhance2][fresh_price_reprice]): the v3 adapter reprices each entry at the symbol's latest daily close and re-sizes with the sleeve's own 1 percent rule; a budget that buys nothing at the fresh price takes no position. Exits are never filtered.

## Files in this repo
- Sleeve module: sleeves/snapback.py (strategy logic and CONFIG).
- v3 adapter: adapters3/snapback.py (SLEEVE_ID=snapback; evaluate(view, ctx) rebuilds the v2 SleeveContext via adapters3/_snapshot_ctx.SnapshotSleeveContext, delegates to adapters/snapback.py, then applies desk3/enhance26.filter_entries; the _snapshot_ctx glue itself is not in this repo at its canonical path, as the audit record notes).
- v2 adapter mirror: integration/snapback_adapter.py in this repo (the adapters/snapback.py evaluate it mirrors).
- Shared engine file: engines/desk3/enhance26.py (desk desk3/enhance26.py: ENH-B26-20261024 adapter-layer gates, default ON per sleeve).
- Existing strategy doc: strategies/femto/femto-snapback.md.
- Config: engines/config/sleeves.json (row id=snapback), also at config/sleeves.json.

## Configuration
Module adapters3.snapback; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars]; parked false. Universe: the genome names present in the bars snapshot, banded to the bottom tenth by trailing-52-week mean weekly dollar volume (at least 9 names); timeframes weekly (signal) and daily (spread and pricing). Source: muse-desk-v3/config/sleeves.json row id=snapback. Note the existing strategy doc's $100,000-book fill law is the master-desk sizing; the v3 sleeve and roster slice above govern this recreation.

## Data inputs
Inputs are bars (the roster input). The sleeve consumes daily bars {t,o,h,l,c,v} ascending per symbol plus, via context.extra, weekly bars per symbol, sleeve_state {SYM: {position}} and last_exit {SYM: date}. The existing doc's Data section names split-adjusted daily bars of the genome (300, cached) and desk quotes on the master desk. Fewer than 52 weekly bars for a name, or no weekly input at all, means that name cannot be flagged (fail closed).

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `snapback` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/snapback.py, whose evaluate(view, ctx) delegates to adapters/snapback.py, which runs sleeves/snapback.py signal(bars, slice_state, context), after which desk3/enhance26.filter_entries is applied.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture whose band contains a name with top-tercile spread, a 13-week return at or below -20 percent and near_low outside the bottom tercile, with no held position and no exit in the last 91 days: exactly one entry for that name, qty int(0.01 x equity // weekly close) before the adapter reprice, ranked ahead of lower-spread flagged names.
- Fixture with 10 positions already open (counting this pass's entries): no further entries under the default cap; the same fixture with the cap switched OFF takes every flagged name.
- Fixture with a held position entered 91 or more days ago: exactly one full exit, and no stop-based exit exists at any price.
- Fixture with a flagged name exited 30 days ago: no re-entry for that name.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
