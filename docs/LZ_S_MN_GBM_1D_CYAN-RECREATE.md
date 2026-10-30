# lz_s_mn_gbm_1d_cyan - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna Daily cyan trees (Midna port)", type forecast and ML models, family 1d, algorithm grade PARTIAL with gap: sizing not recorded in any consulted source. Accounting entry (verbatim): entry {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}; exit {"rule": "Midna plan: no stop / time exit 21 sessions", "hold_from": "fill", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 21, "rest": "time", "plan_overrides": []}; data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json. Alias lz_s_mn_gbm_1d_cyan, status md2_catalog installed. Classification evidence in the accounting: entries require an external frozen GBM model score at or above the 90th percentile cut, price and dv20 filters, exit at the 21st session close.
- The canonical id carries the lz_ prefix from the md2 catalog record; the lz_engine config row for the same lane uses the id without the lz_ prefix, s_mn_gbm_1d_cyan, with the identical label, entry, exit and producer (see Configuration). The selection code for the lane is the daily cyan GBM sleeve in Test, `sleeves/daily_cyan_gbm.py`. No standalone code file named for this exact canonical id exists in any searched repo; the lane runs from the lz_engine config row plus that selection code, and both are in Test.
- Existing Test packages for the related forms: `docs/S_MN_GBM_1D_CYAN-RECREATE.md` (the unprefixed form, UNRESOLVED in the accounting on its own entry) and `docs/DAILY_CYAN_GBM-RECREATE.md` (the roster sleeve).
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `sleeves/daily_cyan_gbm.py`, `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_mn_gbm_1d_cyan and the two existing packages above: all found in Test, listed under Files in this repo); dwj9ddyvf6-hub/Silicon (recursive tree: no daily cyan GBM sleeve path); dwj9ddyvf6-hub/quant-research-backup (recursive tree plus the port report: `femto-lean/sleeves/daily_cyan_gbm.py` is an earlier port and `femto-lean/ports/daily_cyan_gbm.md` its report; Test holds the fuller restored version of the same sleeve, so nothing was vendored from there); dwj9ddyvf6-hub/Midna (recursive tree: GBM model and freeze files for the upstream scorer exist there, but no executable sleeve for this lane id). Because the executable selection code is already in Test, no vendoring was performed.

## What this strategy is

The Midna daily cyan trees lane, in its md2 (test) form: each day it takes the daily Tensor Cyan fires that carry a frozen gradient-boosted-model (GBM) score in the top tier, filters them on price and dollar volume, buys them in score order up to the lane's slot limit, and holds each name 21 sessions with no price stop at the lane level. The GBM score itself is produced upstream by an external frozen scorer; this lane never computes it.

## Full algorithm

Two layers, both in the record; do not merge them.

Layer A - the md2 / lz_engine lane record for this canonical id (accounting, verbatim values):
1. Entry wrapper: policy midna_block, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions null, no_chase_mult null, stock_red false, qqq_red false, order capped_limit_day.
2. Exit wrapper: "Midna plan: no stop / time exit 21 sessions", hold_from fill, hold_unit_kind 1d, stop_pct 99.0 (the record's no-stop marker), max_bars 21, rest time, plan_overrides [].
3. Data: sleeve_midna producer (Midna entire-branch signal files + Yahoo), file shadow/paper_sleeve/live/midna/midna_fires_v1.json.
4. Sizing: not in the accounting record (accounting gap). The lz_engine config row for the unprefixed form records sizing budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000, with flags: runs side by side with Main 1dc as a separate experiment, and L-146 scaled x0.611 ($2,000 -> $1,000 / 1 slot); start FLAT, upstream positions are reference only.

Layer B - the selection code in Test (`sleeves/daily_cyan_gbm.py`, class DailyCyanGbm), evaluation order in signal(bars, slice_state, context):
1. Constants: HOLD_BARS 21, SCORE_CUT 0.00208 (the 2026-10-05 recalibration: 90th percentile of scores, kept as the experiment control), MIN_PX 5.0, MIN_DV20 1,000,000, MAX_POSITIONS 10, NOTIONAL_FRACTION 0.01, DISASTER_STOP 0.25. CONFIG: sleeve_id daily_cyan_gbm, cadence_s 300, universe (), state_schema {"position": "dict|None"}, risk_pct None.
2. Exits first: for each held position, sessions_since (bars dated strictly after the entry date) at or above HOLD_BARS - 1 (20) stages an exit for the full held quantity at the last close, reason naming the sessions held and the staged-early 21-session law, so the next-session fill lands on the 21st close.
3. Score cut: with the enhancement on by default (ENH-DCG-20261024, switch extra daily_cyan_gbm_improve percentile90, default ON), the bar is the session's own 90th percentile of the delivered finite scores (linear interpolation); with the switch OFF the bar is the absolute SCORE_CUT 0.00208 exactly. A paired journal record (extra daily_cyan_gbm_exp_journal) records p90, the control cut, and the control and treatment eligible sets.
4. Candidate filter: scores arrive as context.extra dcg_scores {SYM: score}; non-numeric, boolean, NaN or infinite scores are skipped (the old BC14A-12 guard); candidates are ranked by score descending; a symbol already held is skipped; capacity is tested before append against MAX_POSITIONS 10 counting the book; the signal-day close must be at least $5; dv20 (mean 20-session dollar volume over the last 20 bars; fewer than 20 bars gives no value) must be at least $1,000,000.
5. Entry sizing in the code: qty = int((equity * 0.01) // last close); qty below 1 emits nothing (no forced floor). The enter intent carries price_hint = last close, a disaster stop at round(px * (1 - 0.25), 2), and exit rules (stop at that price, time_bars 21). This 25% disaster stop is a property of the selection code (restored 2026-10-16 from the old source); the lane record in Layer A states no price stop for the lane wrapper - both statements are recorded here as written in their own layers.
6. Fail-closed: no scores in extra means no entries (a stale score feed must deliver no scores at all); equity at or below 0 returns exits only.

## Files in this repo

- This package: `docs/LZ_S_MN_GBM_1D_CYAN-RECREATE.md`
- Selection code (already in Test): `sleeves/daily_cyan_gbm.py` (DailyCyanGbm; see Layer B).
- Adapters (already in Test): `adapters3/daily_cyan_gbm.py`, `integration/daily_cyan_gbm_adapter.py`.
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_mn_gbm_1d_cyan (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`).
- Existing packages for the related forms: `docs/S_MN_GBM_1D_CYAN-RECREATE.md`, `docs/DAILY_CYAN_GBM-RECREATE.md`.
- Strategy card: `strategies/femto/femto-daily-cyan-gbm.md`.
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, entry "Midna Daily cyan trees (Midna port)".
- Earlier port outside Test (read only, not vendored; Test holds the fuller version): quant-research-backup `femto-lean/sleeves/daily_cyan_gbm.py` and `femto-lean/ports/daily_cyan_gbm.md`.

## Configuration

- lz_engine config row for s_mn_gbm_1d_cyan in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim values): kind 1d, label "Midna Daily cyan trees (Midna port)", enabled true, state live, status_text "ready (Midna port; start FLAT; Midna positions are reference only)", source {producer: "sleeve_midna (Midna entire-branch signal files + Yahoo)", file: "shadow/paper_sleeve/live/midna/midna_fires_v1.json", lane: "s_mn_gbm_1d_cyan"}, entry and exit as in Layer A, sizing as in Layer A item 4, research lines naming the Midna forward spec (FORWARD_SPECS id gbm-1d-cyan, ruleId V4-GBM-1D-CYAN-ALL, FORWARD_NAV 20000, FORWARD_SLOTS 6) and the reference-positions comparison file, flags as in Layer A item 4.
- Selection-code configuration: SleeveConfig and constants in Layer B item 1; enhancement switch extra daily_cyan_gbm_improve percentile90, default ON.
- Roster row for the underlying sleeve daily_cyan_gbm in `config/sleeves.json`: module adapters3.daily_cyan_gbm, cadence_s 300, session rth, slice capital_usd 10000.0 and cash_usd 10000.0, parked false, params {}, inputs [bars, positions].

## Data inputs

- context.extra dcg_scores: {SYM: score} from the external frozen GBM scorer for the session, delivered through the sleeve_midna producer file shadow/paper_sleeve/live/midna/midna_fires_v1.json at the lane layer.
- Daily bars per symbol {t, o, h, l, c, v} ascending, for the price, dv20 and sessions-since-entry computations.
- context.extra sleeve_state: {SYM: {"position": {entry_px, entry_date, qty} | None}}; context equity for sizing.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, the accounting entry in `docs/ALL-SLEEVES.json`, and the related packages `docs/S_MN_GBM_1D_CYAN-RECREATE.md` and `docs/DAILY_CYAN_GBM-RECREATE.md`.
3. Confirm `sleeves/daily_cyan_gbm.py` is present at that path and the lz_engine config row for s_mn_gbm_1d_cyan matches Configuration.
4. Wire the sleeve_midna producer so each session's evaluation carries dcg_scores, sleeve_state, daily bars and equity in the shapes the Full algorithm describes; a missing or stale score feed must deliver no scores.
5. Run the desk cycle with the lane enabled from a flat start; the selection entry point is DailyCyanGbm.signal(bars, slice_state, context) in `sleeves/daily_cyan_gbm.py`.
6. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm (no per-sleeve test file for this exact canonical id is present in this repo):

- A candidate with a non-finite or boolean score, a score below the session bar (90th percentile with the enhancement on, 0.00208 with it off), a close under $5, or dv20 under $1,000,000 produces no entry.
- With 10 positions already held, no further entry is emitted even for a top score (capacity tested before append).
- Sizing: an entry's quantity is int((equity * 0.01) // last close); a budget that buys less than one share emits nothing.
- Exit: a position held 20 sessions since entry is staged for exit at the last close; at 19 sessions it is not.
- The lane wrapper never enters outside the capped_limit_day wrapper with max delay 65 minutes, and never holds more than its config sizing of 1 slot of $1,000 at the lane layer.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
