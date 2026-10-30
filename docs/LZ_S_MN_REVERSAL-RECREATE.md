# lz_s_mn_reversal — Recreation Package

## Provenance

- Type: mean reversion; family: 1d; algorithm grade in the accounting: PARTIAL.
- Accounting sources: md2 catalog entry/exit/strategy text.
- entry: [lz_s_mn_reversal] {"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}
- exit: [lz_s_mn_reversal] {"rule": "Midna plan: reversal time/rotation exit", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 21, "rest": "time", "plan_overrides": []}
- filters: [lz_s_mn_reversal] data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json
- accounting gap: sizing not recorded in any consulted source
- variant: base form (variant zero) :: base strategy as documented; no distinct variant recorded (aliases: lz_s_mn_reversal)
- alias lz_s_mn_reversal: md2_catalog: installed

- Accounting entry: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json`, strategy entry "Midna Reversal (Midna port)" (also `docs/ALL-SLEEVES.md`).
- Code status: INCOMPLETE-CODE. The strategy's own module is in this repo (`sleeves/s_mn_reversal.py`), but the shared helper module it imports, `sleeves/laz8_common.py` (Intent, SleeveConfig, closes, held_positions, qty_for, xstale_refused, sessions_held), is not in this repo (direct read of `sleeves/laz8_common.py` returned 404) and was not found in dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup or dwj9ddyvf6-hub/Midna (repo trees searched at batch start). The module's own docstring and logic are reproduced in evidence below; the helper functions' internals are not in the record and are not reconstructed here.

## What this strategy is

A 1-day-family mean-reversion rotation (the Midna port): rank the traded universe by prior-21-session return, buy the 3 worst performers at $1,000 each, and exit each position after 21 sessions (the monthly rotation), re-ranking and refilling at that evaluation.

## Full algorithm

From `sleeves/s_mn_reversal.py` in this repo (constants: SLOTS = 3, PER_SLOT = 1000.0, LOOKBACK = 21, HOLD = 21; CONFIG cadence_s = 300, state_schema {"position": "dict|None"}):

1. Compute held positions from sleeve state.
2. Exit check, per held symbol: sessions held (sessions_held over that symbol's bars from its entry_date) >= 21 → emit an exit intent: sell, sell_to_close, full held quantity, price hint = last close, reason "monthly_rotation_21_sessions". Any such exit marks this evaluation as a rotation.
3. If positions are held and none is rotating, return: no entries mid-hold (no churn until the rotation date).
4. Open slots = 3 − (held count − exits fired). If none, stop.
5. Candidate ranking (worst_names): for every symbol in the snapshot bars, excluding held symbols, with at least 22 bars, ret21 = close[-1] / close[-22] − 1. Sort ascending by ret21 and take the first 3.
6. Per candidate, in rank order, while slots remain: skip if xstale_refused(context, sleeve, bars, symbol) (the ENH20 stale-data refusal in the imported helper; its internals are not in the record); quantity = qty_for(1000.0, last close) (helper; the accounting records the $1,000 per-slot budget, the helper's rounding is not in the record); if qty > 0 emit an enter intent: buy, buy_to_open, price hint = last close, reason recording ret21.

Accounting entry policy (Provenance): policy midna_block, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, order capped_limit_day. Accounting exit record: "Midna plan: reversal time/rotation exit", hold_from plan, max_bars 21, stop_pct 99.0 (effectively no price stop; the code implements the 21-session time exit only). Accounting gap: sizing not recorded in any consulted source (the code's $1,000 per slot / 3 slots above is from the module in this repo).

## Files in this repo

- This package: `docs/LZ_S_MN_REVERSAL-RECREATE.md`
- Strategy module: `sleeves/s_mn_reversal.py`
- Adapters: `adapters/s_mn_reversal.py`, `integration/s_mn_reversal_adapter.py`
- MISSING dependency: `sleeves/laz8_common.py` (not in this repo; see Provenance)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Signal data named in the accounting: sleeve_midna signal files (`shadow/paper_sleeve/live/midna/midna_fires_v1.json` path as recorded) plus Yahoo bars; the desk3 module instead reads the snapshot bars the producer carries (per its docstring, the producer-defined large-cap set; the catalog names no tickers).

## Configuration

- Sleeve id s_mn_reversal; cadence_s 300; slots 3; per-slot budget $1,000 (book $3,000); lookback 21 sessions; hold 21 sessions.
- Universe: US large caps as carried in the snapshot bars (producer-defined; no ticker list in the record).
- Timeframe: daily bars (family 1d in the accounting).

## Data inputs

- Daily bars (at least 22 sessions per symbol) for the universe, sleeve state (held positions with entry_date and qty), and the evaluation context used by the stale-data refusal.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. BLOCKER: obtain `sleeves/laz8_common.py` from a source outside the searched GitHub repos; without it the module does not import and this package is graded INCOMPLETE-CODE.
3. Register `sleeves/s_mn_reversal.py` (CONFIG cadence_s 300) with the desk3 sleeve layer, with daily bars and positions in the snapshot view.
4. Run the desk3 cycle; the sleeve emits enter/exit intents per the algorithm above.

## Verification

Behavior checklist (from the algorithm above; no dedicated test file for this sleeve id was found in the Test tree searched at batch start):
- With 22+ sessions of bars and no held positions, exactly the 3 lowest ret21 symbols receive buy intents sized from the $1,000 per-slot budget.
- A position held 20 sessions produces no exit and no new entries; at 21 sessions it produces a full-quantity sell exit and the freed slot refills from the new ranking, excluding still-held symbols.
- A symbol with fewer than 22 bars is never ranked.
