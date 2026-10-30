# aster_tensor_g4_cash_all_10 - RECREATE

Provenance: Ausar R17/R18 Tensor research on the archived v615 engine (Source row of the existing Test doc `strategies/ausar/r19-tensor-g4.md`, with the family-name token in that row omitted here because repo files must not carry it); desk engine header in `desk3/aster_batch14.py` states the G4 gates were read directly from the archive r19_tensor passes function and tensor RULES.json.

## What this sleeve is

This sleeve is a long-only US equity Tensor sleeve in family `G4` with capital mode `cash` and volatility cut `all`. It consumes Tensor bundle fires, applies this sleeve's own gates, buys one $1000 ticket per passing evaluation into at most 10 distinct symbols, and holds each position to a 260-session (52-week) deadline. It is a thin wrapper: all logic lives in the shared engine `desk3/aster_batch14.py`.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_tensor_g4_cash_all_10.py` sets `SLEEVE_ID="aster_tensor_g4_cash_all_10"`, takes `INPUTS` and `PRODUCERS` from `desk3/aster_batch14.py`, and delegates to `desk3.aster_batch14.evaluate(SLEEVE_ID, view, ctx)`. The SPECS row in that engine for this sleeve is exactly: `family="G4", capital_mode="cash", volatility="all", slots=10, ticket=1000.0`. Engine constant: `HOLD_SESSIONS=260`. Inputs `INPUTS=("tensor", "bars", "positions")`. The Tensor engine itself is untouched; signal generation is the Tensor bundle's, and this sleeve implements only fire gating, sizing and exits.

Evaluation order in the engine `evaluate` for this sleeve:

1. Exits first. Position age in sessions is read from the position fields `sessions_held`, else `age_sessions`, else `held_sessions`, else `weeks_held` times 5, else 0. For each non-zero position (in reserve mode the QQQ reserve leg is skipped here; it exits only to fund a ticket): the position is due when age >= 260, or when the session date is at or after the position `exit_at` or `exit_deadline` date when one is carried. A due position exits in full at the latest daily bar close (bars keys `SYM|1Day`, `SYM|1D`, then `SYM`), falling back to the position average price, with reason naming the sleeve and `week52_deadline`. If any exit is emitted, return it and evaluate no entry. There is no price stop and no profit target.
2. Slot gate: held symbols are the distinct position symbols (excluding the QQQ reserve leg in reserve mode). If 10 or more distinct symbols are held, return nothing.
3. Fire scan, in bundle order. Fires come from `view["tensor"]` as a list or as a dict with a `fires` list, else `view["fires"]`, else `view.extra["fires"]`. A fire is skipped when it is not a dict, when it carries a `sleeve_id` different from this sleeve, when its symbol is missing or already held, or when its price is missing or <= 0.
4. Family gates for this sleeve:
   - G4 gates, all required (engine `_passes`): average dollar volume (fire `adv_usd`, else `avg_dollar_volume`, else `dv20`) present and >= 2000000; the volatility test in the next bullet passes; `buy-green` appears in the fire markers (fire `markers`, else `primary_markers`) or `green` appears in the fire signal text (fire `signal`, else `event`, lowercased); fire price <= 10; depth (fire `depth60`, else `depth`) present and >= 70; fire `ret60` present and >= 0; fire `vol20` present and >= 0.09.
   - Volatility cut for this sleeve: `all`: no atr_ratio split is applied.
5. Capital mode for this sleeve: cash: no extra-session delay; a passing fire may enter in the evaluation session.
6. Execution-price revalidation (ENH-TENSOR14-REPRICE-20261024, default ON; switch `ctx["enhance"][sid]["exec_reprice"]` or `view.extra["<sid>_improve"]["exec_reprice"]`, OFF restores the fire-price rule exactly): when a current daily bar exists for the symbol, the family price cap (<= 10) is revalidated against the latest close; a current close above the cap refuses the entry and is recorded as a paired shadow record, and sizing uses the latest close instead of the fire price.
7. Sizing and entry: quantity = int(1000 // execution price); quantity < 1 skips the fire. In reserve mode, before the entry, if a QQQ position is held, emit a QQQ funding exit selling min(absolute QQQ quantity, int(1000 // QQQ price) or 1) shares at the latest QQQ bar close (fallback the QQQ average price), reason naming `qqq_reserve_funding` and the ticket. The entry intent is then emitted and the evaluation returns: at most one entry per evaluation.
8. Intent shape (engine dict): intent id `aster_tensor_g4_cash_all_10-<timestamp>-<n>`, kind entry or exit, symbol, side buy or sell, quantity, order type market, limit price None, stop price None, time in force day, position intent `buy_to_open` for entries and `sell_to_close` for exits, price hint the execution price. Entry reason names the sleeve, the family, the capital mode, the volatility cut and the ticket.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_tensor_g4_cash_all_10.py`, `sleeves/aster_tensor_g4_cash_all_10.py`, and `integration/aster_tensor_g4_cash_all_10_adapter.py`. Desk original: `adapters3/aster_tensor_g4_cash_all_10.py`, delegating to `desk3.aster_batch14.evaluate`.
- Shared engine that runs the logic: `desk3/aster_batch14.py` (contains the SPECS row for this sleeve, `_passes`, `_vol_ok` and `evaluate`; engines map status already_present).
- Existing family card: `strategies/ausar/r19-tensor-g4.md`. Existing per-sleeve behaviour doc: `docs/ASTER_TENSOR_G4_CASH_ALL_10-ALGORITHM.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_tensor_g4_cash_all_10`).

## Configuration

- Sleeve id: `aster_tensor_g4_cash_all_10`; module: `adapters3.aster_tensor_g4_cash_all_10` (roster row in desk `config/sleeves.json`).
- Universe: US equities named by Tensor bundle fires (the family card universe is the frozen 1,838-name research cohort). Timeframe: weekly Tensor fires, evaluated on a daily cadence in v3. Session: `rth`. Cadence: 86400 seconds (`cadence_s=86400`).
- Sizing / slice: $10,000 capital and $10,000 cash in the roster slice; the engine ticket is $1000 per entry with at most 10 distinct symbols held. `bp_buffer_frac=0.02`.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false (`parked=false`).

## Data inputs

Inputs declared in the roster row and the engine (`INPUTS = ("tensor", "bars", "positions")`): `tensor`, `bars`, `positions`.

Producers declared in `desk3/aster_batch14.py` (`PRODUCERS`): `tensor_bundle` (outputs tensor, freshness SLA 86400s), `bars` (outputs bars, 900s), `broker_readback` (outputs positions, 900s). The v3 function reads the fires from the tensor bundle, the latest daily bars for exit and revalidation pricing, and the positions, plus the session date from ctx `session` or the view or ctx `now`.

## Install and run

1. Place `desk3/aster_batch14.py` in a fresh desk under `desk3/` (copy the repo file of that path).
2. Place the adapter as `adapters3/aster_tensor_g4_cash_all_10.py` (copy any repo copy listed above).
3. Register the roster row for `aster_tensor_g4_cash_all_10` from `config/sleeves.json` (module `adapters3.aster_tensor_g4_cash_all_10`, cadence 86400, session rth, $10,000 slice, inputs tensor/bars/positions, parked false).
4. Wire inputs so the view contains a `tensor` bundle (or `fires`) with fire dicts carrying symbol, price, markers or signal text and the gate fields named in the algorithm, `bars` with the latest daily closes, `positions` from broker readback, and a session date in ctx or a current time in the view or ctx.
5. First evaluation: call `adapters3.aster_tensor_g4_cash_all_10.evaluate(view, ctx)`; it delegates to `desk3.aster_batch14.evaluate("aster_tensor_g4_cash_all_10", view, ctx)`. Run every 86400 seconds in the rth session; the first check is the 260-session deadline exit scan, then the fire scan for at most one entry.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist, each check derived from the algorithm above:

- Check the deadline exit: a position with 260 or more sessions held (including via weeks held times 5), or whose exit_at or exit_deadline date has been reached, exits in full with the week52 deadline reason, and any exit in a pass blocks entries in that pass; in reserve mode a QQQ position is not deadline-exited.
- Check the slot gate: with 10 distinct symbols held, a fully passing fire produces no entry.
- Check this sleeve's family gates exactly as stated in step 4, each gate failing independently blocks the entry, and a fire for a different sleeve id or an already held symbol is ignored.
- Check the capital mode timing in step 5 exactly.
- Check sizing and repricing: quantity equals int(1000 // execution price), the execution price is the latest daily bar close when the revalidation switch is ON and a bar exists (with a current close above 10 refusing the entry), and the fire price when it is OFF or no bar exists; at most one entry is emitted per evaluation.
- Check intent shape: market order, time in force day, position intent buy_to_open for entries and sell_to_close for exits, no limit or stop price.
