# lz_s_q07w_s52_ml_ins2_mom6_vix20 - Recreation Package

Grade: INCOMPLETE-CODE (code not located; see Provenance)

## Provenance

- Canonical ID: `lz_s_q07w_s52_ml_ins2_mom6_vix20`
- Canonical name: Q07 w_swing H52 midlarge insider2+mom6+stress_vix20 (test)
- Aliases: lz_s_q07w_s52_ml_ins2_mom6_vix20
- Type: trend following; Family: 1w; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H52 midlarge insider2+mom6+stress_vix20 (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H52 midlarge insider2+mom6+stress_vix20 (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc for this cell: none for this cell (docs/S_Q07W_S52_ML_INS2_MOM6_VIX20-ALGORITHM.md returns 404 in Test)
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (fresh recursive tree taken at batch start, 294,179 bytes of tree listing, plus file reads: sleeves/, sleeves/lazarus/, laz_sleeves/, adapters3/, integration/, desk3/lazarus_q07.py SPECS, desk3/q07_engine.py, laz_sleeves/_common.py (404, not in tree), config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, docs/ ALGORITHM docs); dwj9ddyvf6-hub/Silicon (fresh recursive tree; no q07 path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree; no q07 path); dwj9ddyvf6-hub/Midna (fresh recursive tree; no q07 path).
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s52_ml_ins2_mom6_vix20] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']; exit: ['[lz_s_q07w_s52_ml_ins2_mom6_vix20] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']; filters: ['[lz_s_q07w_s52_ml_ins2_mom6_vix20] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H52 midlarge insider2+mom6+stress_vix20 (test). A Lazarus Q07 weekly (1w) fire-consumer cell: family w_swing, hold 52 weeks, with the filters named in the canonical name. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The canonical ID carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same cell, where one exists, uses the same ID without the lz_ prefix. That mapping is stated per package below and is not assumed for cells where no such file exists.

## Full algorithm

No complete executable algorithm for this cell is present in Test, because the engine module the wrapper delegates to is missing (see Files in this repo). Everything the record holds:

- Wrapper (laz_sleeves/s_q07w_s52_ml_ins2_mom6_vix20.py, verbatim parameters): catalog rule is the Tensor 1W Swing signal, midlarge band, filters ('ins2', 'mom6', 'vix20'); buy only on a QQQ-down day within 5 sessions of the signal; exit 15% stop or 52-week horizon. Source status Disabled, parked in v3 config (evaluates, dispatcher skips entries while parked). Fires arrive via the desk Tensor bundle producer (ledger substitution LAZ-B7). evaluate(view, ctx) calls q07_evaluate(view, ctx, SLEEVE_ID, band="midlarge", horizon_weeks=52, filters=('ins2', 'mom6', 'vix20'), slots=2, slot_usd=1000.0). Declared inputs: bars_1day, positions, tensor_fires, alt_data, vix.
- Entry (accounting, verbatim): ['[lz_s_q07w_s52_ml_ins2_mom6_vix20] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']
- Exit (accounting, verbatim): ['[lz_s_q07w_s52_ml_ins2_mom6_vix20] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']
- Filters / data (accounting, verbatim): ['[lz_s_q07w_s52_ml_ins2_mom6_vix20] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']
- Filter glossary in the general Q07 record (desk3/q07_engine.py header, a different engine than the missing one; stated as glossary only, not as this cell's code): ins2 = insider_buys >= 2; mom6 = positive 6-month momentum (close vs close 126 sessions ago > 0); vix20 = VIX >= 20.
- The internal evaluation order, filter arithmetic, fail-closed readings, sizing beyond slots=2 / slot_usd=1000.0 in the wrapper call, and exit mechanics of q07_evaluate: not in the record, because that function's code was not located in any searched repo.

Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S52_ML_INS2_MOM6_VIX20-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test:
- Wrapper present in Test: `laz_sleeves/s_q07w_s52_ml_ins2_mom6_vix20.py`, `sleeves/lazarus/s_q07w_s52_ml_ins2_mom6_vix20.py`, `integration/s_q07w_s52_ml_ins2_mom6_vix20_adapter.py` (all 848 bytes, identical wrapper). The wrapper imports q07_evaluate from laz_sleeves._common, but NO laz_sleeves/_common.py (or any file defining q07_evaluate) exists in the Test tree taken at batch start, nor in the Silicon, quant-research-backup or Midna trees searched. The actual logic that runs this strategy is therefore NOT present in Test, so this package is INCOMPLETE-CODE: presenting the wrapper as the strategy's code would fail the recreation bar.
- Vendored files: none. Nothing was vendored, because no complete code for this cell was located.

## Configuration

Config row in config/sleeves.json: module laz_sleeves.s_q07w_s52_ml_ins2_mom6_vix20, cadence_s 86400, session rth, slice capital_usd 1984.0 / cash_usd 1984.0, bp_buffer_frac 0.02, flat_by_close false, inputs [bars_1day, positions, tensor_fires, alt_data, vix], parked true. Wrapper call: slots=2, slot_usd=1000.0. Accounting sizing: not in the record (gap listed).

Accounting entry policy for every cell in this batch (verbatim from the accounting entry field): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. Exit in accounting: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 52 weeks from fill). Sizing in accounting: not in the record (gap listed).

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field; plus bars_1day, positions, tensor_fires, alt_data, vix as declared in the wrapper.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. STOP: the runnable logic for this cell (laz_sleeves._common.q07_evaluate) is not in Test. Do not invent that module and present it as the original. A recreation can only be built as a new implementation from the record in the Full algorithm section, and it must be labelled as such.
4. Supply the data inputs named above in the view / ctx shape the code expects.
5. Call evaluate(view, ctx) on the desk cycle cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm record above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) with a qualifying fire and every named filter passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching the stated hold (52 weeks from fill) exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- This package is INCOMPLETE-CODE: no behavior comparison against original complete code is possible, because no complete original code for this cell was located. Any new implementation must be verified only against the record above and labelled a reconstruction.
