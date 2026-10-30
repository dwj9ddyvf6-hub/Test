# 1d: Recreation package

Provenance: Source row in strategies/lazarus/lz-tracker.md in this repo: research (canonical Tensor v698 tracker), run by Lazarus; the per-sleeve algorithm doc docs/1D-ALGORITHM.md states it was derived from the sleeve code on 2026-10-29 (no author spec on file).

## What this sleeve is
This sleeve buys long-only US equity entries driven by Lazarus fires on the daily lane. It is a thin wrapper with no strategy math of its own: its evaluate(view, ctx) delegates to the shared Lazarus fire-consumer engine named below with its own sleeve id. All rules in this package are the engine rules as applied to this sleeve's own SPECS entry and roster row.

## Full algorithm
This sleeve's SPECS entry (desk3/lazarus.py): slots=6, capital=10350.0, cadence_s=300, session="rth", max_age_min=2880 (60 x 48, 48 hours), qqq_down=True, stop_pct=0.15, target_pct=0.20, partial_pct=0.30, horizon_sessions=40. No family, tf, cap_tier, signal_tier, ml_pick, both_red, max_price, deep or min_vix key is set for this sleeve.

Entry specifics for 1d: the QQQ-down gate applies; there is no both-red gate, no family/timeframe/cap-tier/signal-tier filter, and the horizon is the fixed 40 sessions (horizon_from_fire is not set, although a fire horizon_sessions value is still honoured by the engine's horizon expression when present).

Common entry evaluation, in code order: skip a fire that is not a dict, whose sleeve_id (when present) does not match this sleeve, whose symbol is missing or already held, whose side (when present) is not buy/long, or whose fired_at/ts cannot be parsed; reject age < 0 or age > max_age_min. Family, signal-tier and cap-tier filters are enforced only when the fire carries that field (a fire without the field is not rejected on that filter). The QQQ-down gate (where set) uses fire qqq_red/qqq_down when carried, otherwise QQQ bars: last close below the prior close (single bar: close below open); the gate must be exactly True, so missing QQQ-red data means no entry. The both-red gate (where set) applies the same red test to the stock itself. Price: the fire price is the base price; with the fresh-price enhancement on by default (ENH-LAZ-REPRICE-20261024), sizing, stop anchor and price_hint use the freshest completed bar close in the same snapshot when it differs, and the fire price is only the fallback when no bars exist. The bound guard (on by default) refuses an entry whose fresh price is already at or above the fire target_price. Quantity is int(per-slot capital // price); qty < 1 is skipped. Per-slot capital is capital / slots. The sleeve stops when open positions reach slots. On entry the sleeve state records horizon_sessions, the fire target_price and entry_at. Entry intents are market buys, time_in_force day, reason `<id>_tensor_fire`.

Exits are evaluated before entries, in this exact order (desk3/lazarus.py evaluate()):
1. Stop: if stop_pct is set and current price <= entry price x (1 - stop_pct), sell the full qty, reason `<id>_stop15` when stop_pct is 0.15.
2. Stored target price: if the fire target_price saved in sleeve state (laz_state.json) exists and current price >= that target, sell the full qty, reason `<id>_target`.
3. Partial: if partial_pct is set and current price >= entry price x (1 + partial_pct) and qty > 1, sell int(qty)//2, reason `<id>_partial30_trail` (only where partial_pct is stated for this sleeve below).
4. Percent target: if target_pct is set and current price >= entry price x (1 + target_pct), sell the full qty, reason `<id>_target20` when target_pct is 0.20 (checked after the partial rule, so the partial wins when both are true).
5. Time exit: if sessions held (session_dates from the snapshot, else SPY bar dates, else business days) >= horizon_sessions, sell the full qty, reason `<id>_time_exit_<horizon>s`.
If any exit intent is produced, entries are not evaluated that cycle and the state file is saved. Exit intents are market orders, side sell, time_in_force day, no limit or stop price on the intent itself; the entry intent carries stop_price = round(entry price x (1 - stop_pct), 4) when stop_pct is set.

Position management: one position per symbol (already-held symbols are skipped), no pyramiding, no averaging, and no entries once the slot count is filled. Positions are the snapshot positions for this sleeve; holding time is counted in sessions as described in the time-exit rule.

## Files in this repo
- Sleeve wrapper (desk adapters3/laz_1d.py): `adapters3/laz_1d.py`.
- Shared engine: `desk3/lazarus.py` (desk source desk3/lazarus.py, SPECS entry for `1d`).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing per-sleeve algorithm doc: `docs/1D-ALGORITHM.md`; existing family card: see the Provenance line.

## Configuration
- Universe: symbols named by matching Lazarus fires (the tracker's canonical universe, per the family card in this repo); Asset: US equities. Timeframe: the daily fire lane (id 1d); bars are read as 1Day bars by default in the engine.
- Sizing / slice: capital_usd 10350.0, cash_usd 10350.0; slots 6, so per-slot capital is $1,725.00.
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} (empty in the roster row - all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row and the engine INPUTS tuple: lazarus_fires, bars, positions.
- lazarus_fires: a list in view["lazarus_fires"] (or view["extra"]["lazarus_fires"] / view["tensor_fires"] / view["extra"]["fires"]) of records with sleeve_id, symbol, fired_at, price and optional target_price, horizon_sessions, horizon_hours, cap_tier, signal_tier, color/family, ml_pick, qqq_red and stock_red. The engine header states the desk tracker source is unreachable from the desk host, so only ingested fires in the snapshot are consumed. Fail-closed: no fresh matching fire means no entry.
- bars: view["bars"] keyed by `<symbol>|1Day` or by symbol; used for the red tests, the fresh-price reprice, session counting (SPY dates as fallback) and the current price (last bar close, falling back to the fire price).
- positions: view["positions"] rows with symbol, qty, avg_price and opened_at.
- State: ctx state_dir / laz_state.json holds per-symbol horizon_sessions, target_price and entry_at written on entry.

## Install and run
1. Place `desk3/lazarus.py` in the fresh desk at desk3/lazarus.py and the wrapper at adapters3/laz_1d.py with SLEEVE_ID = "1d".
2. Register the roster row for `1d` exactly as in the Configuration section in config/sleeves.json (module adapters3.laz_1d, the cadence, session, slice and inputs stated there).
3. Wire the producers so every evaluation snapshot carries lazarus_fires (ingested fires), bars and positions, plus view now (or ctx now) and ctx state_dir for laz_state.json.
4. First evaluation: call evaluate(view, ctx) on the wrapper; it calls desk3.lazarus.evaluate("1d", view, ctx). Confirm a snapshot with no fresh matching fire returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check that a fire older than this sleeve's max_age_min, a fire for another sleeve_id, an already-held symbol and a non-buy side each produce no entry.
- Check that the QQQ-down gate blocks entry when QQQ is not red and when QQQ-red data is missing, and (where set) that the both-red, family, cap-tier and signal-tier filters behave as stated, including the carries-the-field-only rule.
- Check sizing: qty equals int((capital / slots) // entry price), using the freshest bar close when bars are present and the fire price only when they are not, and that stop_price on the entry intent equals round(price x (1 - stop_pct), 4) where stop_pct is set and is absent where it is not.
- Check exit precedence on fixtures: stop before stored target, stored target before partial, partial before percent target, percent target before time exit, and that any exit suppresses entries in the same evaluation.
- Check the time exit fires exactly when sessions held reaches this sleeve's horizon_sessions, and the partial rule (where set) sells exactly int(qty)//2 and only when qty > 1.
