# s_mn_d_green_band: Recreation package

Provenance: Source row in strategies/midna/mn-forward-lab.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset US equities, timeframe 1d and 1w, universe Midna's daily panel, style Tensor signal + filters). The desk adapter header states Lazarus Midna fire-consumer batch 9, engine desk3/lazarus_midna.py.

## What this sleeve is
This sleeve is a fire-consumer: it buys one name on a daily Green Tensor fire whose price lies in the $10 to $20 band, sized from a $1,000 budget, and holds it for 21 sessions with no price stop. Signal generation stays upstream; the desk engine desk3/lazarus_midna.py owns position management. The v3 adapter in adapters3/ delegates to that engine's evaluate(SLEEVE_ID, view, ctx).

## Full algorithm
This sleeve's SPECS entry (desk3/lazarus_midna.py): family="green", tf="1D", hold_sessions=21, stop=None, gate="band", budget=1000.0. Maximum 1 open position.

Exits, evaluated first: for each non-zero position, price is the last bar close for the symbol (keys SYM|1Day, SYM|1D, SYM, SYM|1Week, SYM|1W) or avg_price if no bars; age is read from sessions_held / age_sessions / held_sessions / bars_held, or age_weeks / held_weeks x 5, or counted from entry_date / opened_at against the bars. No stop applies (stop=None). If age >= 21, emit a full-qty market sell_to_close exit, reason time_21_sessions. If any exit is emitted, return it; if any position is held, return no entry (max 1 slot).

Entries, in code order:
1. Fires are read from view midna_fires, view fires, extra midna_fires / fires, or the tensor / tensor_bundle value (a list, a dict with a fires/midna_fires list, or a sleeves dict of fire lists). No fires means no entry.
2. A fire is skipped if it is not a dict, its sleeve_id (when present) differs, its family/kind/signal text does not contain "green", its timeframe/tf (when present) does not match 1D (1D, D, DAILY and DAY accepted), it has no symbol, or its date/fire_date/ts is after the session or more than 10 days before it.
3. Cross-stale gate (ENH20-MN-XSTALE-20261024, on by default; off via extra s_mn_d_green_band_enh20 xstale_gate=False): refuse when the symbol's last bar date lags the latest bar date across view bars by more than 4 days.
4. Price: ENH19 reprice is on by default (extra s_mn_d_green_band_enh19 or s_mn_d_green_band_improve fresh_price controls it): when on and a fresh last close exists, price = that close; otherwise price = the fire price or the fresh close. Price at or below 0 is skipped. When the price differs from the fire price, the intent carries an enhance_exp record with control (fire) and treatment (fresh) prices and quantities.
5. Band gate: refuse unless 10.0 <= price <= 20.0.
6. Sizing and intent: qty = int(1000.0 // price); qty below 1 is skipped. Emit one market, day, buy_to_open entry, price_hint = price, reason naming tensor_green_1D, the fire date and gate=band, then stop (one entry only).

Position management: one position at a time, no pyramiding, no stop.

## Files in this repo
- Sleeve adapter (desk adapters3/s_mn_d_green_band.py): `adapters3/s_mn_d_green_band.py`; also present as `sleeves/s_mn_d_green_band.py` and `integration/s_mn_d_green_band_adapter.py`.
- Shared engine: `desk3/lazarus_midna.py` (desk source desk3/lazarus_midna.py, SPECS entry for `s_mn_d_green_band`).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-forward-lab.md`. Existing per-sleeve algorithm doc: `docs/S_MN_D_GREEN_BAND-ALGORITHM.md`.

## Configuration
- Universe: symbols named by qualifying Green fires (Midna's daily panel upstream). Asset: US equities. Timeframe: 1D.
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; engine budget 1000.0, 1 slot.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row (all parameters live in the engine SPECS entry).
- Parked: false.
- Roster inputs: tensor, bars, positions.

## Data inputs
- tensor: view["tensor"] / tensor_bundle or the fire channels above, fire rows with sleeve_id, symbol, family, timeframe, date and price. Producer: tensor_bundle, freshness SLA 86400 seconds (engine PRODUCERS in desk3/lazarus_midna.py).
- bars: view["bars"] daily (or weekly-keyed) bars per symbol. Producer: bars, freshness SLA 900 seconds.
- positions: view["positions"] rows with symbol, qty, avg_price and the age/opened fields read by the exit rule. Producer: broker_readback, freshness SLA 900 seconds.

## Install and run
1. Place the engine at desk3/lazarus_midna.py in the fresh desk (repo copy at the same path) and the adapter at adapters3/s_mn_d_green_band.py with SLEEVE_ID = "s_mn_d_green_band".
2. Register the roster row for `s_mn_d_green_band` exactly as in the Configuration section in config/sleeves.json (module adapters3.s_mn_d_green_band, cadence 300, session rth, $1,000 slice, inputs tensor/bars/positions).
3. Wire the producers so every snapshot carries the Tensor bundle fires, daily bars, this sleeve's positions, and view/ctx now and session.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.lazarus_midna.evaluate("s_mn_d_green_band", view, ctx). Confirm a snapshot with no fires, a fire older than 10 days, or a fire price outside $10 to $20 returns no entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the fire filters: a fire for another sleeve, a non-green family, a mismatched timeframe, a future date, or a date more than 10 days old produces no entry.
- Check the band and price: a fresh close of $9.99 or $20.01 produces no entry; $10.00 and $20.00 can enter; with reprice on, sizing uses the fresh close, not the fire price.
- Check sizing and the single slot: qty equals int(1000.0 // price), exactly one entry is emitted, and any held position suppresses entries.
- Check the exit: a position aged 20 sessions is held, at 21 sessions it exits in full, and no price move alone exits it.
- Check the cross-stale gate: a symbol whose last bar lags the snapshot's latest bar by more than 4 days is refused, and setting the ENH20 switch off restores the entry.
