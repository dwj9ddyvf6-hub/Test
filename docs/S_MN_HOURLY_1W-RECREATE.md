# s_mn_hourly_1w: Recreation package

Provenance: Source row in strategies/lazarus/lz-tracker.md in this repo: Tensor v698 tracker research, run by Lazarus (family Lazarus, asset US equities, timeframe 1h, 1d and 1w, universe the tracker's canonical universe, style Tensor signal). The desk adapter header states Lazarus Midna fire-consumer batch 9, engine desk3/lazarus_midna.py.

## What this sleeve is
This sleeve is the weekly Midna fire-consumer lane of the shared Lazarus Midna engine: it holds one fire-named position for up to 260 sessions (52 weeks), with a 15 percent stop, sized from a $1,000 budget. It has no family or price-band gate. The v3 adapter in adapters3/ delegates to desk3/lazarus_midna.py evaluate(SLEEVE_ID, view, ctx); signal generation stays upstream.

## Full algorithm
This sleeve's SPECS entry (desk3/lazarus_midna.py): family=None, tf="1W", hold_sessions=260, stop=0.15, gate=None, budget=1000.0. Maximum 1 open position.

Exits, evaluated first: for each non-zero position, price is the last bar close (keys SYM|1Day, SYM|1D, SYM, SYM|1Week, SYM|1W) or avg_price if no bars; entry is avg_price or entry_px or price; age is read from sessions_held / age_sessions / held_sessions / bars_held, or age_weeks / held_weeks x 5, or counted from entry_date / opened_at against the bars. If entry > 0 and price <= entry x (1 - 0.15), emit a full-qty market sell_to_close exit, reason stop_15pct. Else if age >= 260, emit a full-qty exit, reason time_52_weeks. If any exit is emitted, return it; if any position is held, return no entry.

Entries, in code order:
1. Fires are read from view midna_fires, view fires, extra midna_fires / fires, or the tensor / tensor_bundle value (a list, a dict with a fires/midna_fires list, or a sleeves dict of fire lists). No fires means no entry.
2. A fire is skipped if it is not a dict, its sleeve_id (when present) differs, its timeframe/tf (when present) does not match 1W (1W, W, WEEKLY and WEEK accepted), it has no symbol, or its date/fire_date/ts is after the session or more than 10 days before it. No family filter applies (family=None).
3. Cross-stale gate (ENH20-MN-XSTALE-20261024, on by default; off via extra s_mn_hourly_1w_enh20 xstale_gate=False): refuse when the symbol's last bar date lags the latest bar date across view bars by more than 4 days.
4. Price: ENH19 reprice is on by default (extra s_mn_hourly_1w_enh19 or s_mn_hourly_1w_improve fresh_price): when on and a fresh last close exists, price = that close; otherwise price = the fire price or the fresh close. Price at or below 0 is skipped. A price differing from the fire price attaches an enhance_exp record with control and treatment prices and quantities.
5. Gate: none. Sizing: qty = int(1000.0 // price); qty below 1 is skipped. Emit one market, day, buy_to_open entry, price_hint = price, reason naming tensor_weekly_1W and gate=none, then stop.

Position management: one position at a time; exits are only the 15 percent stop and the 260-session time exit.

## Files in this repo
- Sleeve adapter (desk adapters3/s_mn_hourly_1w.py): `adapters3/s_mn_hourly_1w.py`; also present as `sleeves/s_mn_hourly_1w.py` and `integration/s_mn_hourly_1w_adapter.py`.
- Shared engine: `desk3/lazarus_midna.py` (desk source desk3/lazarus_midna.py, SPECS entry for `s_mn_hourly_1w`).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/lazarus/lz-tracker.md`. Existing per-sleeve algorithm doc: `docs/S_MN_HOURLY_1W-ALGORITHM.md`.

## Configuration
- Universe: symbols named by qualifying fires (the tracker's canonical universe upstream). Asset: US equities. Timeframe: 1W.
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; engine budget 1000.0, 1 slot.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row (all parameters live in the engine SPECS entry).
- Parked: false.
- Roster inputs: tensor, bars, positions.

## Data inputs
- tensor: view["tensor"] / tensor_bundle or the fire channels above, fire rows with sleeve_id, symbol, family, timeframe, date and price. Producer: tensor_bundle, freshness SLA 86400 seconds (engine PRODUCERS in desk3/lazarus_midna.py).
- bars: view["bars"] bars per symbol. Producer: bars, freshness SLA 900 seconds.
- positions: view["positions"] rows with symbol, qty, avg_price and the age/opened fields read by the exit rule. Producer: broker_readback, freshness SLA 900 seconds.

## Install and run
1. Place the engine at desk3/lazarus_midna.py in the fresh desk (repo copy at the same path) and the adapter at adapters3/s_mn_hourly_1w.py with SLEEVE_ID = "s_mn_hourly_1w".
2. Register the roster row for `s_mn_hourly_1w` exactly as in the Configuration section in config/sleeves.json (module adapters3.s_mn_hourly_1w, cadence 300, session rth, $1,000 slice, inputs tensor/bars/positions).
3. Wire the producers so every snapshot carries the Tensor bundle fires, bars, this sleeve's positions, and view/ctx now and session.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.lazarus_midna.evaluate("s_mn_hourly_1w", view, ctx). Confirm a snapshot with no fires or a fire older than 10 days returns no entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the stop and time exits: a position at or below 85 percent of entry exits with stop_15pct; a position aged 260 sessions exits with time_52_weeks; at 259 sessions above the stop it is held.
- Check the fire filters: a fire for another sleeve, a 1D timeframe, a future date, or a date more than 10 days old produces no entry; any family value is accepted.
- Check sizing and the single slot: qty equals int(1000.0 // price), exactly one entry is emitted, and any held position suppresses entries.
- Check price and staleness: with reprice on, sizing uses the fresh close; a symbol lagging the snapshot's latest bar by more than 4 days is refused unless the ENH20 switch is off.
