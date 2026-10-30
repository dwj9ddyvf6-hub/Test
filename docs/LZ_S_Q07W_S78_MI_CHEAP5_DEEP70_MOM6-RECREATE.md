# lz_s_q07w_s78_mi_cheap5_deep70_mom6 - Recreation Package

Grade: INCOMPLETE-CODE (code not located; see Provenance)

## Provenance

- Canonical ID: `lz_s_q07w_s78_mi_cheap5_deep70_mom6`
- Canonical name: Q07 w_swing H78 micro cheap5+deep70+mom6 (test)
- Aliases: lz_s_q07w_s78_mi_cheap5_deep70_mom6
- Type: trend following; Family: 1w; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H78 micro cheap5+deep70+mom6 (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H78 micro cheap5+deep70+mom6 (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc for this cell: none for this cell
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken at batch start, 4,430 entries, plus file reads: laz_sleeves/, sleeves/, sleeves/lazarus/, adapters3/, integration/ wrappers for each cell, engines/laz_sleeves/_common.py, desk3/lazarus_q07.py SPECS, desk3/q07_engine.py, config/sleeves.json, packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, docs/ ALGORITHM docs, strategies/lazarus/lz-q07.md); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no q07 or wait_q14 path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no q07 or wait_q14 path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no q07 or wait_q14 path).
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s78_mi_cheap5_deep70_mom6] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']; exit: ['[lz_s_q07w_s78_mi_cheap5_deep70_mom6] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']; filters: ['[lz_s_q07w_s78_mi_cheap5_deep70_mom6] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H78 micro cheap5+deep70+mom6 (test). A Lazarus Q07 weekly (1w) fire-consumer cell: family w_swing, with the alt-data filters named in the canonical name, hold 78 weeks. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The canonical ID carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same cell, where one exists, uses the same ID without the lz_ prefix. That mapping is stated per package below and is not assumed for cells where no such file exists.

## Full algorithm

No executable algorithm description beyond the accounting and md2 catalog config records exists on file for this cell. Everything the record holds:

- Name-encoded cell (from the canonical name and the Q07 cell grammar in strategies/lazarus/lz-q07.md): family w_swing (swing), hold 78 weeks (n/a for lz_s_wait_q14, whose hold is recorded as n/a), cap band micro, filters: cheap5, deep70, mom6.
- Entry (accounting, verbatim): ['[lz_s_q07w_s78_mi_cheap5_deep70_mom6] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']
- Exit (accounting, verbatim): ['[lz_s_q07w_s78_mi_cheap5_deep70_mom6] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']
- Filters / data (accounting, verbatim): ['[lz_s_q07w_s78_mi_cheap5_deep70_mom6] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']
- md2 catalog config entry in Test (packages/grokbot/rl64/lz_engine/config/sleeves.json, verbatim): {"id": "s_q07w_s78_mi_cheap5_deep70_mom6", "account": "TEST", "broker_account": "TEST_MWJW", "kind": "1w", "label": "Q07 w_swing H78 micro cheap5+deep70+mom6 (test)", "enabled": true, "state": "live", "status_text": "ready (md2 RL64 2026-10-24, Trader t181u)", "source": {"producer": "sleeve_feed composer (tracker ledger + alt-data tags)", "file": "shadow/paper_sleeve/live/sleeve_fires_v1.json", "lane": "s_q07w_s78_mi_cheap5_deep70_mom6"}, "entry": {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}, "exit": {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}, "sizing": {"budget_usd": 1000, "max_slots": 1, "position_usd": 1000, "position_usd_by_class": {}, "one_share_max_usd": null, "cap_pct_of_dv20": 1.0, "min_slot_fraction": 0.9, "global_slot_usd": 1000, "min_dv20_usd": 100000}, "research": ["DESK_INTEGRATION/Q07_PRICE_FAMILY_PARAMS.csv Q07-w_swing-H78-micro-cheap5+deep70+mom6 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 546 calendar days; entry red (Q07 'red'))", "CORPUS_AUDIT/out/Q07_confluence_cells.csv cheap5+deep70+mom6 w_swing H78 micro red band: n 945, names 279, edge +101.3 [76.7, 126.6], q_fam 8.41e-11, CONFIRMED; px pool 26.878 UNPROVEN (positive n.s.,", "CORPUS_AUDIT/code/ctx_feats.py tags() + ca_lib.load_weekly (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands)"], "flags": ["md2 RL64 2026-10-24 (Trader t181u): Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve (existing budgets unchanged)"]}
- Filter glossary in the md2 config research lines and the Test strategy card strategies/lazarus/lz-q07.md (general Q07 record, not per-cell code): cheap5 = px_fire < 5; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; tierA = tier_noliq A / dv20 >= $100k; PIT SEC bands. A fire trades only when every tag of its cell is true; a missing input is no fire.
- Sizing in the accounting: not in the record (accounting gap: sizing not recorded in any consulted source). Sizing in the md2 config entry above is part of that verbatim record.
- Evaluation order beyond the entry policy above, per-filter fail-closed readings for this cell in an executing engine, and cadence in an executing engine: not in the record.

Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S78_MI_CHEAP5_DEEP70_MOM6-RECREATE.md`
- md2 catalog config: `packages/grokbot/rl64/lz_engine/config/sleeves.json` (entry for this cell; config only, not code)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test:
- No per-cell code file was located in any searched repo (see Provenance search record). No sleeves/, laz_sleeves/, sleeves/lazarus/, adapters3/ or integration/ file for this cell exists in the Test tree, desk3/lazarus_q07.py SPECS has no entry for it, desk3/q07_engine.py carries no per-cell spec for it, and config/sleeves.json has no row for it. An md2 catalog config entry for this cell does exist in Test at packages/grokbot/rl64/lz_engine/config/sleeves.json (and, for lz_s_wait_q14 only, also at packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json); a config entry is not executable sleeve code, so none is claimed as this strategy's code.
- Vendored files: none. Nothing was vendored, because no code for this cell was located.

## Configuration

md2 catalog config entry (verbatim, in the Full algorithm section): entry policy fear_day; max_delay_minutes 65; limit_band_pct 5.0; limit_buffer_pct 1.0; window_sessions 5; no_chase_mult 1.02; stock_red true; qqq_red true; order capped_limit_day. config/sleeves.json row for this cell: not in the record (no row in the Test tree copy read at batch start).

Accounting entry policy for every cell in this batch (verbatim from the accounting entry field): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. Exit in accounting: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 78 weeks from fill). Sizing in accounting: not in the record (gap listed).

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field. Alt-data tags are the filters named for this cell.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. STOP: no runnable code for this cell exists in Test. Do not invent a wrapper or a SPECS entry and present it as the original. A recreation can only be built as a new implementation from the accounting and config records in the Full algorithm section, and it must be labelled as such.
4. Supply the data inputs named above in the view / ctx shape the code expects.
5. Call evaluate(view, ctx) on the desk cycle cadence; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm record above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) with a qualifying fire and every named filter passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching the stated hold exits in full where a hold is recorded; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- This package is INCOMPLETE-CODE: no behavior comparison against original code is possible, because no original code for this cell was located. Any new implementation must be verified only against the accounting and config records above and labelled a reconstruction.
