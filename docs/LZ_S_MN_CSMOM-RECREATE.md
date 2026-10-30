# lz_s_mn_csmom: Recreation Package

Package grade: INCOMPLETE-CODE. The execution and exit records on file are reproduced below, but no code for this strategy was located in any searched GitHub repo, and the entry/signal rule itself is not in the record, so this package does not claim a faithful recreation.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Midna CS momentum (Midna port)", type momentum, family 1d. Sole alias `lz_s_mn_csmom`, recorded installed, source md2_catalog. Algorithm grade PARTIAL; recorded gap: "sizing not recorded in any consulted source". Algorithm sources per the accounting: md2 catalog entry/exit/strategy text only.
- No Test catalog entry exists for this id (checked in Test `docs/CATALOG.json`: zero occurrences), and no strategy card exists in Test.

## What this strategy is

Per its name and family record: a cross-sectional ("CS") momentum sleeve in the lazarus `s_mn` family, run as a port driven by the Midna signal files. The record holds its order-execution policy and its exit rule (below); it does not hold the ranking/signal rule that selects names, and that rule is not reconstructed here.

## Full algorithm

Everything the record holds, verbatim in substance from the accounting:

- Entry / execution policy (accounting entry field, a policy block): {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}. Read plainly: entries execute as capped limit day orders under the "midna_block" policy, with a maximum delay of 65 minutes, a 5.0% limit band and a 1.0% limit buffer; the stock_red and qqq_red blocks are off; window_sessions and no_chase_mult are null in the record.
- The signal that generates the entries (the cross-sectional momentum ranking: lookback, universe, long/short construction, rebalance rule) is not in the record.
- Exit (accounting exit field): {"rule": "Midna plan: rank exit / circuit -40%", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 63, "rest": "time", "plan_overrides": []}. Read plainly: positions exit per the Midna plan's rank-exit rule with a -40% circuit, holds measured in 1d units from the plan, a nominal stop_pct of 99.0, and a maximum hold of 63 bars.
- Sizing: not in the record.
- Data (accounting filter field): "data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json".

## Files in this repo

- This package: `docs/LZ_S_MN_CSMOM-RECREATE.md`
- Code: NONE FOUND. Searched, at package build time, the full file trees of dwj9ddyvf6-hub/Test (sleeves/, strategies/, packages/, desk3/, laz_sleeves/, adapters/, adapters3/, integration/; filename patterns csmom, cs_mom, cross-sectional, s_mn, lazarus, midna), dwj9ddyvf6-hub/Silicon (research/ and desk trees), dwj9ddyvf6-hub/quant-research-backup (including femto-lean/sleeves/), and dwj9ddyvf6-hub/Midna. The lazarus s_mn sleeves present in Test are s_mn_hedge, s_mn_hourly and s_mn_nostop only; no csmom module exists in any of them. Nothing was vendored for this package.

## Configuration

- Family/timeframe as recorded: family "1d", hold unit 1d, max hold 63 bars.
- Universe, sizing, cadence, state files: not in the record.

## Data inputs

Midna entire-branch signal files plus Yahoo, per the accounting filter text; the named signal file path is `shadow/paper_sleeve/live/midna/midna_fires_v1.json` (a desk runtime path, not a repo path in any searched repo).

## Install and run

This package cannot be installed as a faithful recreation: neither the code nor the entry signal rule is on file in any searched GitHub repo.

1. Recovery would require the md2 catalog's underlying sleeve module (the lazarus s_mn csmom module) or the Midna plan document that defines the rank rule; neither is in Test, Silicon, quant-research-backup, or Midna as searched.
2. The sibling lazarus s_mn sleeves in Test (`sleeves/lazarus/s_mn_hedge.py`, `sleeves/lazarus/s_mn_hourly.py`, `sleeves/lazarus/s_mn_nostop.py`) share the family plumbing but are different strategies; running one of them does not recreate this strategy and must not be reported as doing so.

## Verification

No tests exist in Test for this strategy. Behavior checklist from the recorded fragments (for use if the code is recovered):

- Entries are capped limit day orders under the midna_block policy: max delay 65 minutes, limit band 5.0%, limit buffer 1.0%.
- Exits follow the Midna plan rank-exit rule with a -40% circuit and a 63-bar maximum hold in 1d units.
- Any recreation that invents a momentum lookback, universe, or ranking rule fails this package's standard by construction: those values are not in the record.
