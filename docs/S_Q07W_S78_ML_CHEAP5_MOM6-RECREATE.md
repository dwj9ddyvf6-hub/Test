# s_q07w_s78_ml_cheap5_mom6 - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting: canonical name "s_q07w_s78_ml_cheap5_mom6", type trend following, family unrecorded, algorithm grade FULL from the lz_engine config (entry/exit/sizing below), and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". Universe, asset class, timeframe and creator are "not recorded in consulted sources". Alias s_q07w_s78_ml_cheap5_mom6 (md2_lz_engine, status live). It is in the census missing_unresolved_flagged_ids list.
- Accounting algorithm record (verbatim): entry: lz_engine entry config {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}; exit: lz_engine exit config {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}; sizing: lz_engine sizing {"budget_usd": 1000, "max_slots": 1, "position_usd": 1000, "position_usd_by_class": {}, "one_share_max_usd": null, "cap_pct_of_dv20": 1.0, "min_slot_fraction": 0.9, "global_slot_usd": 1000, "min_dv20_usd": 100000}; filters: [] in the accounting (the filter names are carried in the canonical id: cheap5, mom6); parameters: {}.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated. Content reads included desk3/lazarus_q07.py SPECS and desk3/q07_engine.py in the desk source and in Test: neither contains an entry for s_q07w_s78_ml_cheap5_mom6 (neighbouring s78 ml entries carry different filter sets), and no sleeves/, adapters3/ or integration/ file for this cell exists in the Test tree. The desk source grep in this run likewise found no occurrence of this id in muse-desk-v3/desk3/.

## What this strategy is

No strategy description is recorded in consulted sources (accounting, verbatim). The canonical id encodes a Q07 weekly cell: swing family (s), hold 78 weeks, mid/large cap band (ml), with filters cheap5 and mom6, run as a live lz_engine lane. That decoding is from the Q07 cell grammar in `strategies/lazarus/lz-q07.md` and does not settle the unresolved accounting ambiguity.

## Full algorithm

Everything the record holds (the accounting grades this FULL from the config; the package does not claim a complete algorithm because the strategy is UNRESOLVED):

- Entry (accounting, verbatim config): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day.
- Exit (accounting, verbatim config): the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 78 weeks, calendar weeks after the fire week, desk weekly time exit), hold_from fill, hold_unit_kind 1w, stop_pct null, max_bars null, plan_overrides [].
- Sizing (accounting, verbatim): budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000.
- Filters: the accounting filters field is empty; the canonical id names cheap5 (price < $5) and mom6, per the Q07 glossary in strategies/lazarus/lz-q07.md (mom6 = 126-day return >= the frozen 67th percentile in that card). Whether this lane's fires carried those tags, and the upstream signal rule, are not in the record.
- Signal generation, evaluation order beyond the entry policy, and cadence: not in the record.

## Files in this repo

- This package: `docs/S_Q07W_S78_ML_CHEAP5_MOM6-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md` (UNRESOLVED section entry for this canonical id)
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test: no per-cell code file was located in any searched repo (see Provenance). The shared engines desk3/lazarus_q07.py and desk3/q07_engine.py exist in Test but contain no spec for this cell, so neither is claimed as this strategy's code.
- Vendored files: none.

## Configuration

Full lz_engine config as in the Full algorithm section: entry fear_day / 65 / 5.0 / 1.0 / 5 / 1.02 / stock_red true / qqq_red true / capped_limit_day; hold 78 weeks from fill; sizing budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000. Universe, timeframe beyond the 1w hold unit, and creator: not in the record.

## Data inputs

Sleeve feed fires, per the Q07 family record in strategies/lazarus/lz-q07.md (the accounting's own data line for this cell is not recorded; its exit/entry config is an lz_engine sleeve_feed lane). File in the family record: shadow/paper_sleeve/live/sleeve_fires_v1.json.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and the UNRESOLVED accounting entry for s_q07w_s78_ml_cheap5_mom6 in `docs/ALL-SLEEVES.json`.
3. STOP: no runnable code for this cell exists in Test and the accounting is UNRESOLVED. Do not invent a wrapper or a SPECS entry and present it as the original.
4. A recreation can only be built as a new implementation from the config record in the Full algorithm section, and it must be labelled as such.
5. Do not change parameter values: use exactly the values recorded. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- Behaviour checklist derived only from the config record: (a) with no qualifying fire, no entry; (b) an entry, if built as a labelled reconstruction, uses the fear_day capped-limit config and the $1,000 single-slot sizing exactly; (c) a held position exits on the 15% disaster stop or at 78 weeks from fill.
- This package is an UNRESOLVED package: no behaviour comparison against original code is possible, because no original code for this cell was located and the accounting ambiguity is unresolved.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes.
