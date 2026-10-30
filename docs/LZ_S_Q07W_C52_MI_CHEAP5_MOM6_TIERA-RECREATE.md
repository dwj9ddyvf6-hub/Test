# lz_s_q07w_c52_mi_cheap5_mom6_tierA - Recreation Package

Grade: INCOMPLETE-CODE (code not located; see Provenance)

## Provenance

- ALL-SLEEVES accounting: canonical name "Q07 w_cyan H52 micro cheap5+mom6+tierA (test)", type trend following, family 1w, algorithm grade PARTIAL with gap: sizing not recorded in any consulted source; alias lz_s_q07w_c52_mi_cheap5_mom6_tierA (md2_catalog, status installed). Classification evidence: desk3/q07_engine.py and desk3/lazarus_q07.py: Q07 lanes take the Tensor 1W signal of the named family, apply alt-data filters, buy on a QQQ down day and exit on a 15% stop or horizon.
- Accounting algorithm record (verbatim): entry: {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}; exit: {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}; filters/data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json.
- Existing Test doc for this cell: none. A neighbouring cell package `docs/LZ_S_Q07W_C52_MI_MOM6_TIERA-RECREATE.md` was graded INCOMPLETE-CODE on the same grounds.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated. Content reads included desk3/lazarus_q07.py SPECS (no entry for s_q07w_c52_mi_cheap5_mom6_tierA and no micro/mi band in its band normalisation for this form), desk3/q07_engine.py (no spec for this cell), and the Test tree sleeves/, adapters3/ and integration/ listings (no file for this cell; the c52 files present are for other filter sets).

## What this strategy is

A Lazarus Q07 weekly (1w) fire-consumer cell (test form): family w_cyan (cyan), micro cap band, hold 52 weeks, with alt-data filters cheap5, mom6 and tierA. Universe, asset class and creator: not recorded in consulted sources in the accounting.

## Full algorithm

Everything the record holds (PARTIAL grade; gaps marked):

- Name-encoded cell: family cyan, band micro (mi), hold 52 weeks, filters cheap5 (price < $5), mom6 and tierA, per the canonical name and the Q07 grammar in `strategies/lazarus/lz-q07.md` (tierA = unified tier A; mom6 = 126-day return >= the frozen 67th percentile in that card's glossary).
- Entry (accounting, verbatim): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day.
- Exit (accounting, verbatim): the sleeve feed fire's plan (15% disaster stop / time exit; hold = 52 weeks from fill), hold_from fill, hold_unit_kind 1w.
- Filters / data (accounting, verbatim): sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json. A fire trades only when every tag of its cell is true; a missing input is no fire (general Q07 record in strategies/lazarus/lz-q07.md).
- Sizing: not in the record (accounting gap).
- Evaluation order beyond the entry policy, per-filter fail-closed readings for this cell, order type in an executing engine, and cadence: not in the record.

## Files in this repo

- This package: `docs/LZ_S_Q07W_C52_MI_CHEAP5_MOM6_TIERA-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test: no per-cell code file was located in any searched repo (see Provenance). The shared engines desk3/lazarus_q07.py and desk3/q07_engine.py exist in Test but neither contains a spec, wrapper or config entry for this cell, so neither is claimed as this strategy's code.
- Vendored files: none. Nothing was vendored, because no code for this cell was located.

## Configuration

Kind 1w; entry policy fear_day; max_delay_minutes 65; limit_band_pct 5.0; limit_buffer_pct 1.0; window_sessions 5; no_chase_mult 1.02; stock_red true; qqq_red true; order capped_limit_day; hold 52 weeks from fill. Sizing, universe, cadence and state: not in the record.

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field. Alt-data tags are the filters named for this cell (cheap5, mom6, tierA).

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. STOP: no runnable code for this cell exists in Test. Do not invent a wrapper or a SPECS entry and present it as the original. A recreation can only be built as a new implementation from the record in the Full algorithm section, and it must be labelled as such.
4. Supply the data inputs named above if building such a labelled reconstruction.
5. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this sleeve ID was named in the Test tree; verification is by the behaviour checklist derived only from the record above: (a) with no qualifying fire, no entry; (b) with a qualifying fire and every named filter passing, exactly the entry described above; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching 52 weeks from fill exits in full.
- This package is INCOMPLETE-CODE: no behaviour comparison against original code is possible, because no original code for this cell was located. Any new implementation must be verified only against the accounting record above and labelled a reconstruction.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes.
