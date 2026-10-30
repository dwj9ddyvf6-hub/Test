# aster_tensor_c1_cash_cool_25 - RECREATE

Provenance: Ausar R17/R18 Tensor research on the archived v615 engine (Source row of the existing Test doc `strategies/ausar/r19-tensor-c1.md`, with the family-name token in that row omitted here because repo files must not carry it); desk engine headers in `desk3/aster_batch13.py` and `desk3/aster_batch14.py` describe the Tensor rows as consuming canonical Tensor v698 products at the sleeve layer.

## What this sleeve is

This sleeve is a long-only US equity Tensor sleeve in family `C1` with capital mode `cash` and volatility cut `cool`. It consumes Tensor bundle fires, applies this sleeve's own gates, buys one $400 ticket per passing evaluation, and holds each position to a 260-session (52-week) deadline. It is a thin wrapper: all logic lives in the shared engine `desk3/aster_batch13.py`.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_tensor_c1_cash_cool_25.py` sets `SLEEVE_ID="aster_tensor_c1_cash_cool_25"`, takes `INPUTS = INPUTS_TENSOR` and `PRODUCERS` from `desk3/aster_batch13.py`, and delegates to `desk3.aster_batch13.evaluate(SLEEVE_ID, view, ctx)`. The SPECS row in that engine for this sleeve is exactly: `kind="tensor", family="C1", capital_mode="cash", volatility="cool"`. Engine constants for all batch 13 tensor rows: `TICKET=400.0`, `SLOTS=25`, `HOLD_SESSIONS=260`. Inputs `INPUTS_TENSOR=("tensor", "bars", "positions")`. The Tensor engine itself is untouched; signal generation is the Tensor bundle's, and this sleeve implements only fire gating, sizing and exits. With no tensor key in the snapshot the registry marks the sleeve UNFED, never fake-fed.

Evaluation order in the engine `_tensor` for this sleeve:

1. Exits first. Position age in sessions is read from the position fields `sessions_held`, else `age_sessions`, else `held_sessions`, else `weeks_held` times 5, else `age_weeks` times 5, else 0. For each non-zero position (in reserve mode the QQQ reserve leg is skipped here; it exits only to fund a ticket): if age >= 260, emit a full exit at the latest bar close for that symbol (bars keys `SYM|4Hour`, `SYM|4H`, `SYM|1Day`, `SYM|1D`, then `SYM`), falling back to the position average price, with reason naming the sleeve and `week52_deadline`. If any exit is emitted, return it and evaluate no entry. There is no price stop and no profit target.
2. Slot gate: held symbols are the distinct position symbols (excluding the QQQ reserve leg in reserve mode). If 25 or more distinct symbols are held, return nothing.
3. Fire scan, in bundle order. Fires come from `view["fires"]` when it is a list, else `view["tensor"]` as a list or as a dict with a `fires` list, else `view.extra["fires"]`. A fire is skipped when it is not a dict, when it carries a `sleeve_id` different from this sleeve, when its symbol is missing or already held, or when its price is missing or <= 0.
4. Family gates for this sleeve:
   - C1 gates, all required: the fire signal text (fire `signal`, else `event`, else `family`, lowercased) contains `cyan`; fire price <= 5; fire `ret60` present and >= 31; fire `vol20` present and >= 0.07; average dollar volume (fire `adv_usd`, else `avg_dollar_volume`) present and >= 2000000.
   - Volatility cut for this sleeve: `cool: fire `atr_ratio` must be present and <= 1 (the test is (atr_ratio <= 1) equals (volatility is cool), so exactly 1.0 is cool)."""
5. Capital mode for this sleeve: cash: a passing fire may enter in the evaluation session, funded from sleeve cash; no extra-session delay and no reserve leg.
   - Fire-age enhancement (ENH-B11-TENSOR-FIREAGE-20261024, applies to this cash sleeve, default ON; switch `ctx["enhance"][sid]["fire_age"]` or `view.extra["<sid>_improve"]["fire_age"]`, OFF restores the any-age rule): a fire dated more than 1 day before the session date, or future-dated, is refused as stale and recorded as a paired shadow record.
6. Execution-price revalidation (ENH-TENSOR13-REPRICE-20261024, default ON; switch `ctx["enhance"][sid]["exec_reprice"]` or `view.extra["<sid>_improve"]["exec_reprice"]`, OFF restores the fire-price rule exactly): when a current bar exists for the symbol, the C1 price cap is revalidated: a current close > 5 refuses the entry, and the execution price becomes the latest close; the fire-price decision is kept as a paired shadow record on the entry intent.
7. Sizing and entry: quantity = int(400 // execution price); quantity < 1 skips the fire. In reserve mode, before the entry, if a QQQ position is held, emit a QQQ funding exit selling min(absolute QQQ quantity, int(400 // QQQ price) or 1) shares at the latest QQQ bar close (fallback the QQQ average price), reason naming `qqq_reserve_funding`. The entry intent is then emitted and the evaluation returns: at most one entry per evaluation.
8. Intent shape (engine dict): intent id `aster_tensor_c1_cash_cool_25-<timestamp>-<n>`, kind entry or exit, symbol, side buy or sell, quantity, order type market, limit price None, stop price None, time in force day, position intent `buy_to_open` for entries and `sell_to_close` for exits, price hint the execution price. Entry reason names the sleeve, the family, the capital mode, the volatility cut, ticket 400 and the fire date.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_tensor_c1_cash_cool_25.py`, `sleeves/aster_tensor_c1_cash_cool_25.py`, and `integration/aster_tensor_c1_cash_cool_25_adapter.py`. Desk original: `adapters3/aster_tensor_c1_cash_cool_25.py`, delegating to `desk3.aster_batch13.evaluate`.
- Shared engine that runs the logic: `desk3/aster_batch13.py` (contains the SPECS row for this sleeve, `_tensor`, `_age_sessions` and `evaluate`; engines map status already_present).
- Existing family card: `strategies/ausar/r19-tensor-c1.md`. Existing per-sleeve behaviour doc: `docs/ASTER_TENSOR_C1_CASH_COOL_25-ALGORITHM.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_tensor_c1_cash_cool_25`).

## Configuration

- Sleeve id: `aster_tensor_c1_cash_cool_25`; module: `adapters3.aster_tensor_c1_cash_cool_25` (roster row in desk `config/sleeves.json`).
- Universe: US equities named by Tensor bundle fires (the family card universe is the frozen 1,838-name research cohort). Timeframe: weekly Tensor fires, evaluated on a daily cadence in v3. Session: `rth`. Cadence: 86400 seconds (`cadence_s=86400`).
- Sizing / slice: $10,000 capital and $10,000 cash in the roster slice; the engine ticket is $400 per entry with at most 25 distinct symbols held. `bp_buffer_frac=0.02`.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false (`parked=false`).

## Data inputs

Inputs declared in the roster row and the engine (`INPUTS_TENSOR = ("tensor", "bars", "positions")`): `tensor`, `bars`, `positions`.

Producers declared in `desk3/aster_batch13.py` (`PRODUCERS`): `bars` (outputs bars, freshness SLA 900s), `tensor_bundle` (outputs tensor, 86400s), `broker_readback` (outputs positions, 900s). The v3 function reads the fires from the tensor bundle, the latest bars for exit and revalidation pricing, and the positions, plus the session date from ctx `session` or the view or ctx `now`.

## Install and run

1. Place `desk3/aster_batch13.py` in a fresh desk under `desk3/` (copy the repo file of that path).
2. Place the adapter as `adapters3/aster_tensor_c1_cash_cool_25.py` (copy any repo copy listed above).
3. Register the roster row for `aster_tensor_c1_cash_cool_25` from `config/sleeves.json` (module `adapters3.aster_tensor_c1_cash_cool_25`, cadence 86400, session rth, $10,000 slice, inputs tensor/bars/positions, parked false).
4. Wire inputs so the view contains a `tensor` bundle (or `fires`) with fire dicts carrying symbol, price, signal text and the gate fields named in the algorithm, `bars` with the latest closes, `positions` from broker readback, and a session date in ctx or a current time in the view or ctx.
5. First evaluation: call `adapters3.aster_tensor_c1_cash_cool_25.evaluate(view, ctx)`; it delegates to `desk3.aster_batch13.evaluate("aster_tensor_c1_cash_cool_25", view, ctx)`. Run every 86400 seconds in the rth session; the first check is the 260-session deadline exit scan, then the fire scan for at most one entry.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist, each check derived from the algorithm above:

- Check the deadline exit: a position with 260 or more sessions held (including via weeks held times 5) exits in full with the week52 deadline reason, and any exit in a pass blocks entries in that pass; in reserve mode a QQQ position is not deadline-exited.
- Check the slot gate: with 25 distinct symbols held, a fully passing fire produces no entry.
- Check this sleeve's family gates exactly as stated in step 4, each gate failing independently blocks the entry, and a fire for a different sleeve id or an already held symbol is ignored.
- Check the capital mode timing in step 5 exactly, including any fire-age refusal that applies to this sleeve.
- Check sizing and repricing: quantity equals int(400 // execution price), the execution price is the latest bar close when the revalidation switch is ON and a bar exists (with the cap refusal stated in step 6), and the fire price when it is OFF or no bar exists; at most one entry is emitted per evaluation.
- Check intent shape: market order, time in force day, position intent buy_to_open for entries and sell_to_close for exits, no limit or stop price.
