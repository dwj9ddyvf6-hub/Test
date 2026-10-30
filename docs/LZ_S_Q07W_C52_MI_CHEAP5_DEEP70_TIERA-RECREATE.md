# lz_s_q07w_c52_mi_cheap5_deep70_tierA - Recreation Package

Grade: INCOMPLETE-CODE (code not located; see Provenance)

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Q07 w_cyan H52 micro cheap5+deep70+tierA (test)", type trend following, family 1w, algorithm grade PARTIAL with gap: sizing not recorded in any consulted source. Accounting entry (verbatim): entry {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}; exit {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}; data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json. Alias lz_s_q07w_c52_mi_cheap5_deep70_tierA, status md2_catalog installed. Universe, asset class, timeframe and creator are not recorded in the accounting.
- lz_engine config record in Test for the same cell under the id without the lz_ prefix: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_q07w_c52_mi_cheap5_deep70_tierA, label "Q07 w_cyan H52 micro cheap5+deep70+tierA (test)", with the identical entry and exit blocks, sizing (see Configuration), and research lines: the Q07 price-family params row for Q07-w_cyan-H52-micro-cheap5+deep70+tierA (CONFIRMED; K 20; exit: close of last NYSE session <= D + 364 calendar days; entry red), the confluence-cell record (cheap5+deep70+tierA, w_cyan, H52, micro, red band: n 38, names 26, edge +258.9 [131.9, 416.0], q_fam 0.00427, CONFIRMED), and the tag definitions from the corpus audit code (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands).
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads: `desk3/lazarus_q07.py` SPECS has no entry for this cell, `desk3/q07_engine.py` is a generic engine whose caller-supplied spec for this cell is not in the record, `config/sleeves.json` has no row for this cell, `packages/grokbot/rl64/lz_engine/config/sleeves.json` has the config row above for the unprefixed form only, and there is no wrapper file sleeves/s_q07w_c52_mi_cheap5_deep70_tierA.py, adapters3/ or laz_sleeves/ file for this cell); dwj9ddyvf6-hub/Silicon (recursive tree: no q07 path); dwj9ddyvf6-hub/quant-research-backup (recursive tree: no q07 sleeve code path for this cell); dwj9ddyvf6-hub/Midna (recursive tree: no q07 path); the local desk source muse-desk-v3 was also grepped for the cell id and holds no code for it (the config record above is its only trace, via the Test copy). No executable code for this cell was located in any searched repo, so nothing was vendored and this package is graded INCOMPLETE-CODE.

## What this strategy is

A Lazarus Q07 weekly (1w) fire-consumer cell: family w_cyan, hold 52 weeks, micro cap band, with the alt-data filters cheap5, deep70 and tierA named in the canonical name. It consumes Tensor 1W fires composed by the sleeve_feed composer and trades only the fires whose tags satisfy every named filter, on the fear_day (red) entry policy. The cell's own signal rule upstream of the fire is not in the record.

## Full algorithm

Everything the record holds; gaps are marked 'not in the record'.

- Name-encoded cell (from the canonical name and the Q07 cell grammar): family w_cyan (cyan), hold 52 weeks, cap band micro, filters cheap5, deep70, tierA.
- Filter readings (from the lz_engine config research lines for this cell, verbatim): cheap5 = px_fire < 5; deep70 = c_depth60 >= 70; tierA = tier_noliq A / dv20 >= $100k; cap bands are PIT SEC bands, and micro is the band named in the cell (its dollar bounds for this cell: not in the record).
- Entry (accounting, verbatim): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. The config research line adds: entry red (Q07 'red').
- Exit (accounting, verbatim): the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit)), hold_from fill, hold_unit_kind 1w, stop_pct null, max_bars null, plan_overrides []. The config research line adds the params-row exit reading: close of last NYSE session <= D + 364 calendar days.
- Filters / data (accounting, verbatim): sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json.
- Sizing: not in the accounting record (accounting gap). The lz_engine config row for the unprefixed form records sizing budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000 (see Configuration); whether that row's sizing governed this lz_ form is not stated in the accounting, so it is recorded here as the config record for the same cell, not as the accounting's sizing.
- Evaluation order beyond the entry policy above, per-filter fail-closed readings in an executing engine for this cell, order mechanics in the executing engine, and cadence: not in the record. The shared engines desk3/lazarus_q07.py and desk3/q07_engine.py exist in Test, but neither contains a spec, wrapper or config entry for this cell, so neither is claimed as this strategy's code.

## Files in this repo

- This package: `docs/LZ_S_Q07W_C52_MI_CHEAP5_DEEP70_TIERA-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`, entry "Q07 w_cyan H52 micro cheap5+deep70+tierA (test)".
- Config record for the same cell (unprefixed form, already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_q07w_c52_mi_cheap5_deep70_tierA.
- Family strategy card: `strategies/lazarus/lz-q07.md`.
- Shared engines present in Test but NOT containing this cell (not claimed as its code): `desk3/lazarus_q07.py`, `desk3/q07_engine.py`.
- Vendored files: none. Nothing was vendored, because no code for this cell was located.

## Configuration

- Accounting entry policy: kind 1w; entry policy fear_day; max_delay_minutes 65; limit_band_pct 5.0; limit_buffer_pct 1.0; window_sessions 5; no_chase_mult 1.02; stock_red true; qqq_red true; order capped_limit_day; hold 52 weeks. Universe, sizing, cadence and state in the accounting: not in the record (sizing gap listed).
- lz_engine config row for s_q07w_c52_mi_cheap5_deep70_tierA in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim values): kind 1w, enabled true, state live, status_text "ready (md2 RL64 2026-10-24, Trader t181u)", source {producer: "sleeve_feed composer (tracker ledger + alt-data tags)", file: "shadow/paper_sleeve/live/sleeve_fires_v1.json", lane: "s_q07w_c52_mi_cheap5_deep70_tierA"}, entry and exit as in the Full algorithm, sizing {budget_usd 1000, max_slots 1, position_usd 1000, position_usd_by_class {}, one_share_max_usd null, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000}, flags: the cell is a Research Lab Q07 price-family cell, 1 slot x $1k, outside the L-146 scale solve.

## Data inputs

- Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field. Alt-data tags are the filters named for this cell (cheap5, deep70, tierA), with the readings in the Full algorithm.
- Any further data inputs: not in the record.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record, and the config row in `packages/grokbot/rl64/lz_engine/config/sleeves.json` for the unprefixed form.
3. STOP: no runnable code for this cell exists in Test. Do not invent a wrapper or a SPECS entry and present it as the original. A recreation can only be built as a new implementation from the accounting and config records in the Full algorithm and Configuration sections, and it must be labelled as such.
4. Supply the data inputs named above in the shape the record describes (fires with the named tags).
5. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve id was found in the searched trees; verification is by the behaviour checklist below, derived only from the records above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) a fire whose price is at or above $5, whose depth tag fails deep70, or whose tier fails tierA does not satisfy this cell's filters; (c) a held position at or below entry x 0.85 (the 15% disaster stop in the fire's plan) exits in full; (d) a held position reaching the stated hold (52 weeks from fill; params-row reading: close of last NYSE session <= D + 364 calendar days) exits in full.
- This package is INCOMPLETE-CODE: no behaviour comparison against original code is possible, because no original code for this cell was located in Test, Silicon, quant-research-backup or Midna (searched locations listed in Provenance). Any new implementation must be verified only against the records above and labelled a reconstruction.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
