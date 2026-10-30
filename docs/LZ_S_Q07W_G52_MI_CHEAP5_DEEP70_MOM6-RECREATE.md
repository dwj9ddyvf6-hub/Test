# lz_s_q07w_g52_mi_cheap5_deep70_mom6 - Recreation Package

Grade: INCOMPLETE-CODE (code not located; see Provenance)

## Provenance

- Canonical ID: `lz_s_q07w_g52_mi_cheap5_deep70_mom6`
- Canonical name: Q07 w_green H52 micro cheap5+deep70+mom6 (test)
- Aliases: lz_s_q07w_g52_mi_cheap5_deep70_mom6
- Type: trend following; Family: 1w; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_green H52 micro cheap5+deep70+mom6 (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_green H52 micro cheap5+deep70+mom6 (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc for this cell: none for this cell
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken at batch start, 4,400 entries, plus file reads: sleeves/, adapters3/, integration/, desk3/lazarus_q07.py SPECS, desk3/q07_engine.py, config/sleeves.json, docs/ ALGORITHM docs, strategies/lazarus/lz-q07.md); dwj9ddyvf6-hub/Silicon (recursive tree, 21,196 entries; no q07 path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no q07 path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no q07 path).
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_g52_mi_cheap5_deep70_mom6] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']; exit: ['[lz_s_q07w_g52_mi_cheap5_deep70_mom6] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']; filters: ['[lz_s_q07w_g52_mi_cheap5_deep70_mom6] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_green H52 micro cheap5+deep70+mom6 (test). A Lazarus Q07 weekly (1w) fire-consumer cell: family w_green, micro cap band, hold 52 weeks, with the alt-data filters named in the canonical name. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The canonical ID carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same cell, where one exists, uses the same ID without the lz_ prefix. That mapping is stated per package below and is not assumed for cells where no such file exists.

## Full algorithm

No executable algorithm description beyond the accounting record exists on file for this cell. Everything the record holds:

- Name-encoded cell (from the canonical name and the Q07 cell grammar in strategies/lazarus/lz-q07.md): family w_green (green), hold 52 weeks, cap band micro, filters: cheap5, deep70, mom6.
- Entry (accounting, verbatim): ['[lz_s_q07w_g52_mi_cheap5_deep70_mom6] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']
- Exit (accounting, verbatim): ['[lz_s_q07w_g52_mi_cheap5_deep70_mom6] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']
- Filters / data (accounting, verbatim): ['[lz_s_q07w_g52_mi_cheap5_deep70_mom6] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']
- Filter glossary in the Test strategy card strategies/lazarus/lz-q07.md (general Q07 record, not per-cell code): tierA = unified tier A; deep70 = 60-week depth >= 70; cheap5 = close < $5; mom6 = 126-day return >= the frozen 67th percentile; wiki_cov = Wikipedia attention coverage. A fire trades only when every tag of its cell is true; a missing input is no fire.
- Sizing: not in the record (accounting gap: sizing not recorded in any consulted source).
- Evaluation order beyond the entry policy above, per-filter fail-closed readings for this cell, order type in the executing engine, and cadence: not in the record.

Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_G52_MI_CHEAP5_DEEP70_MOM6-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test:
- No per-cell code file was located in any searched repo (see Provenance search record). The shared engines desk3/lazarus_q07.py and desk3/q07_engine.py exist in Test, but neither contains a spec, wrapper, or config entry for this cell: SPECS in desk3/lazarus_q07.py has no entry for it (its band normalisation table has no micro band at all), config/sleeves.json has no entry for it, and no sleeves/, adapters3/ or integration/ file for it exists in the Test tree. Presenting either engine as this strategy's code would be a reconstruction, so none is claimed.
- Vendored files: none. Nothing was vendored, because no code for this cell was located.

## Configuration

Configuration as recorded in the accounting entry policy: kind 1w; entry policy fear_day; max_delay_minutes 65; limit_band_pct 5.0; limit_buffer_pct 1.0; window_sessions 5; no_chase_mult 1.02; stock_red true; qqq_red true; order capped_limit_day; hold 52 weeks. Universe, timeframe, sizing, cadence and state: not in the record, except timeframe family 1w and the data line in the Full algorithm section.

Accounting entry policy for every cell in this batch (verbatim from the accounting entry field): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. Exit in accounting: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 52 weeks from fill). Sizing in accounting: not in the record (gap listed).

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field. Alt-data tags are the filters named for this cell.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. STOP: no runnable code for this cell exists in Test. Do not invent a wrapper or a SPECS entry and present it as the original. A recreation can only be built as a new implementation from the accounting record in the Full algorithm section, and it must be labelled as such.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions).
5. Call evaluate(view, ctx) on the desk cycle cadence; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm record above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) with a qualifying fire and every named filter passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching the stated hold (52 weeks from fill) exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- This package is INCOMPLETE-CODE: no behavior comparison against original code is possible, because no original code for this cell was located. Any new implementation must be verified only against the accounting record above and labelled a reconstruction.
