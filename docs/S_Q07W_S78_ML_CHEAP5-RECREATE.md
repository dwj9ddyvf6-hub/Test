# s_q07w_s78_ml_cheap5 - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_q07w_s78_ml_cheap5", type trend following, family unrecorded, algorithm grade FULL from the lz_engine config (entry/exit/sizing), and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". Description in the accounting: "No strategy description recorded in consulted sources." Universe, asset class, timeframe and creator are not recorded in the accounting. Alias s_q07w_s78_ml_cheap5, status md2_lz_engine live. Classification note in the accounting (2026-10-30 repair): the Q07 family is one type, trend following; vix20 is a gate and ml is a cap band per desk3/q07_engine.py.
- Accounting algorithm record (verbatim): entry "[s_q07w_s78_ml_cheap5] lz_engine entry config: {policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day}"; exit "[s_q07w_s78_ml_cheap5] lz_engine exit config: {rule: the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit)), hold_from fill, hold_unit_kind 1w, stop_pct null, max_bars null, rest null, plan_overrides []}"; sizing "[s_q07w_s78_ml_cheap5] lz_engine sizing: {budget_usd 1000, max_slots 1, position_usd 1000, position_usd_by_class {}, one_share_max_usd null, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000}".
- lz_engine config row in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_q07w_s78_ml_cheap5, label "Q07 w_swing H78 midlarge cheap5 (test)", with the identical entry, exit and sizing blocks, and research lines: the Q07 price-family params row for Q07-w_swing-H78-midlarge-cheap5 (CONFIRMED; K 20; exit: close of last NYSE session <= D + 546 calendar days; entry red (Q07 'red')); the confluence-cell record (cheap5, w_swing, H78, midlarge, red band: n 124, names 28, edge +81.0 [36.1, 136.3], q_fam 0.00779, CONFIRMED; px pool 38.427 UNPROVEN (positive n.s., underpowered)); and the tag definitions from the corpus audit code (tierA = tier_noliq A / dv20 >= $100k; deep70 = c_depth60 >= 70; mom6 = ret126 >= pre-2020 q67; cheap5 = px_fire < 5; PIT SEC bands). Flags in the row: Research Lab Q07 price-family cell; 1 slot x $1k, outside the L-146 scale solve.
- A separate accounting entry exists for the lz_-prefixed form of the same cell (lz_s_q07w_s78_ml_cheap5, "Q07 w_swing H78 midlarge cheap5 (test)", PARTIAL, data sleeve_feed composer); it is a different canonical strategy in the accounting and is not merged into this package.
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads: `desk3/lazarus_q07.py` SPECS has no entry for this cell, `desk3/q07_engine.py` is a generic engine whose caller-supplied spec for this cell is not in the record, there is no wrapper file sleeves/s_q07w_s78_ml_cheap5.py, adapters3/ or laz_sleeves/ file for this cell - the s78 ml files present are the deep70 forms only - `config/sleeves.json` has no row for this cell, and `packages/grokbot/rl64/lz_engine/config/sleeves.json` has the config row above); dwj9ddyvf6-hub/Silicon (recursive tree: no q07 path); dwj9ddyvf6-hub/quant-research-backup (recursive tree: no q07 sleeve code path for this cell); dwj9ddyvf6-hub/Midna (recursive tree: no q07 path); the local desk source muse-desk-v3 was also grepped for the cell id and holds no code for it. No executable code for this cell was located in any searched repo, so nothing was vendored; the package status follows the accounting, unresolved_built, not a claim of executable completeness.

## What this strategy is

A Q07 weekly cell: family w_swing, hold 78 weeks, midlarge cap band (ml), with the single alt-data filter cheap5 named in the canonical name. It consumes Tensor 1W fires composed by the sleeve_feed composer and, under the fear_day (red) entry policy, trades the fires priced under $5. The accounting holds a FULL entry/exit/sizing config for this cell but no strategy description, which is why the accounting marks it UNRESOLVED: the cell's own signal rule upstream of the fire, and any module docstring or catalog description that would settle it, are not in the record.

## Full algorithm

Everything the record holds; gaps are marked 'not in the record'.

- Name-encoded cell (from the canonical name, the config label and the Q07 cell grammar): family w_swing (swing), hold 78 weeks, cap band midlarge, filter cheap5.
- Filter reading (from the config research lines for this cell, verbatim): cheap5 = px_fire < 5. Cap bands are PIT SEC bands; the generic Q07 engine in Test (`desk3/q07_engine.py`) records its cap-band dollar bounds as ml (midlarge) = $2,000,000,000 and above, sm (small) = $300,000,000 to $2,000,000,000, mi (micro) = under $300,000,000 - that reading is the generic engine's, recorded here as the only band definition on file; whether it governed this cell's config is not stated in the accounting.
- Entry (lz_engine config, verbatim): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. The config research line adds: entry red (Q07 'red').
- Exit (lz_engine config, verbatim): the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit)), hold_from fill, hold_unit_kind 1w, stop_pct null, max_bars null, plan_overrides []. The config research line adds the params-row exit reading: close of last NYSE session <= D + 546 calendar days.
- Sizing (lz_engine config, verbatim): budget_usd 1000, max_slots 1, position_usd 1000, position_usd_by_class {}, one_share_max_usd null, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000.
- Data (from the lz_-form accounting entry for the same cell and the config source block): sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json.
- Evaluation order beyond the entry policy above, per-filter fail-closed readings in an executing engine for this cell, order mechanics in the executing engine, cadence, universe, asset class and timeframe: not in the record. The shared engines desk3/lazarus_q07.py and desk3/q07_engine.py exist in Test, but neither contains a spec, wrapper or config entry for this cell, so neither is claimed as this strategy's code.

## Files in this repo

- This package: `docs/S_Q07W_S78_ML_CHEAP5-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`, UNRESOLVED entry for s_q07w_s78_ml_cheap5 (and the separate lz_-form entry, not merged).
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_q07w_s78_ml_cheap5.
- Family strategy card: `strategies/lazarus/lz-q07.md`.
- Shared engines present in Test but NOT containing this cell (not claimed as its code): `desk3/lazarus_q07.py`, `desk3/q07_engine.py`.
- Vendored files: none. Nothing was vendored, because no code for this cell was located.

## Configuration

- Full lz_engine config row for s_q07w_s78_ml_cheap5 in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim values): kind 1w, label "Q07 w_swing H78 midlarge cheap5 (test)", enabled true, state live, status_text "ready (md2 RL64 2026-10-24, Trader t181u)", source {producer: "sleeve_feed composer (tracker ledger + alt-data tags)", file: "shadow/paper_sleeve/live/sleeve_fires_v1.json", lane: "s_q07w_s78_ml_cheap5"}, entry, exit and sizing as in the Full algorithm, research and flags as in Provenance.
- Any further configuration: not in the record.

## Data inputs

- Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, with the cheap5 tag reading (px_fire < 5) and the fire's price.
- Any further data inputs: not in the record.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc, the UNRESOLVED accounting entry for s_q07w_s78_ml_cheap5 in `docs/ALL-SLEEVES.json`, and the config row in `packages/grokbot/rl64/lz_engine/config/sleeves.json`.
3. STOP on executable completeness: no runnable code for this cell exists in Test. Do not invent a wrapper or a SPECS entry and present it as the original. A recreation can only be built as a new implementation from the config record in the Full algorithm and Configuration sections, and it must be labelled as such.
4. Supply the data inputs named above in the shape the record describes (fires with price and tags).
5. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve id was found in the searched trees; verification is by the behaviour checklist below, derived only from the records above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) a fire priced at or above $5 does not satisfy this cell's cheap5 filter; (c) a held position at or below entry x 0.85 (the 15% disaster stop in the fire's plan) exits in full; (d) a held position reaching the stated hold (78 weeks from fill; params-row reading: close of last NYSE session <= D + 546 calendar days) exits in full; (e) the lane never holds more than 1 slot of $1,000 under its config sizing, and never enters outside the capped_limit_day wrapper with max delay 65 minutes and window 5 sessions.
- This package is UNRESOLVED in the accounting: no behaviour comparison against original code is possible, because no original code for this cell was located in Test, Silicon, quant-research-backup or Midna (searched locations listed in Provenance).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
