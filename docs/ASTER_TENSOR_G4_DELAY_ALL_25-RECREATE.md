# aster_tensor_g4_delay_all_25: Recreation package

Provenance: Ausar R17/R18 Tensor research on the archived v615 engine (Source row in strategies/ausar/r19-tensor-g4.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This sleeve buys cheap, deeply drawn-down US stocks on a weekly Tensor buy-green fire and holds each for about 52 weeks. Its capital mode is delay, its volatility cut is all, and it runs 25 slots. It is a thin wrapper delegating to desk3/aster_batch14.py with its own SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch14.py): family="G4", capital_mode="delay", volatility="all", slots=25, ticket=400.0. Engine constant HOLD_SESSIONS=260. Inputs tuple INPUTS=("tensor", "bars", "positions").

Pass gate (_passes in desk3/aster_batch14.py, applied to each Tensor fire in list order; the first passing fire that produces an entry ends the evaluation, so at most one entry per evaluation):
1. Dollar volume: adv = fire adv_usd, else avg_dollar_volume, else dv20; refuse if adv is missing or adv < 2000000.
2. Volatility gate (_vol_ok): volatility="all" imposes no atr_ratio test (a missing atr_ratio does not block).
3. Marker: "buy-green" must be in the fire markers / primary_markers, or the fire signal / event string (lowercased) must contain "green".
4. Price: the fire price must be > 0 and <= 10.
5. depth60 (else depth) must be present and >= 70; ret60 must be present and >= 0; vol20 must be present and >= 0.09. A fire missing any field fails closed.
6. Sleeve filter: a fire carrying a sleeve_id different from "aster_tensor_g4_delay_all_25" is skipped; a fire whose symbol is already held is skipped.

Evaluation order in desk3/aster_batch14.py::evaluate(sid, view, ctx):
1. Exits first, over every non-zero position. A position is due when sessions held >= 260, where sessions held is read from sessions_held / age_sessions / held_sessions, else weeks_held * 5, else 0; or when the position carries exit_at / exit_deadline and the current session date >= that date. A due position exits its whole absolute quantity, reason naming week52_deadline and sessions_held, priced at the last 1Day bar close for the symbol, else avg_price. No stop and no target exist in this engine. If any exit is produced, return only the exits.
2. Slot cap: held symbols count toward slots=25; if the count already reaches the cap, return no entries.
3. Entry-date rule for mode="delay": when the fire carries a date / fire_date / signal_end, refuse until (current session date - fire date).days >= 1; a fire with no date carries no delay check in the code.
3. Execution-price revalidation (ENH-TENSOR14-REPRICE-20261024, switch exec_reprice read from ctx enhance or view extra["aster_tensor_g4_delay_all_25_improve"], default ON): when a current 1Day bar exists for the symbol, refuse the entry if its last close > 10 (the G4 cap re-checked at execution) and otherwise size off that current close instead of the fire price. OFF restores the fire-price rule exactly.
4. Entry sizing: qty = int(ticket // execution price), with ticket = 400.0. Refuse if qty < 1. Entry intent: market, day, buy_to_open, qty as computed, price_hint = execution price, reason naming tensor_g4, mode=delay, vol=all, the ticket and the fire date.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_tensor_g4_delay_all_25.py` (also `sleeves/aster_tensor_g4_delay_all_25.py` and `integration/aster_tensor_g4_delay_all_25_adapter.py`).
- Shared engine: `desk3/aster_batch14.py` (this sleeve's SPECS entry, _passes, _vol_ok and evaluate).
- Contract type: desk3/contract.py, whose repo copy is at `engines/desk3/contract.py` in engines_map.json with status gate_blocked, so that copy was not vendored by the engines pass; the desk original must be supplied from desk3/contract.py to run.
- Existing family card: `strategies/ausar/r19-tensor-g4.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: symbols named by passing Tensor fires; the existing card states the frozen 1,838-name research cohort. Asset: US equities. Timeframe: weekly Tensor fires; 1Day bars for exit and revalidation prices.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; ticket 400.0, slots 25; bp_buffer_frac=0.02.
- Cadence: 86400 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row: tensor, bars, positions. Producers in the engine PRODUCERS tuple: tensor_bundle -> tensor (freshness_sla_s 86400), bars -> bars (900), broker_readback -> positions (900).
- tensor: view["tensor"] as a list of fires, or a dict with a fires list, or view["fires"], or view extra["fires"]; each fire carries symbol, price, markers/primary_markers or signal/event, adv_usd/avg_dollar_volume/dv20, depth60/depth, ret60, vol20, atr_ratio, date/fire_date/signal_end and optionally sleeve_id.
- bars: view["bars"] keyed by `<symbol>|1Day`, `<symbol>|1D` or symbol.
- positions: view["positions"] rows with symbol, qty, avg_price, sessions_held/age_sessions/held_sessions or weeks_held, and exit_at/exit_deadline.
- Session: ctx session if supplied, else the date of view/ctx now.

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_tensor_g4_delay_all_25.py` with SLEEVE_ID = "aster_tensor_g4_delay_all_25" (the repo also carries `sleeves/aster_tensor_g4_delay_all_25.py` and `integration/aster_tensor_g4_delay_all_25_adapter.py` copies).
2. Register the roster row for `aster_tensor_g4_delay_all_25` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_tensor_g4_delay_all_25, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_batch14.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the pass gate on fixtures: each threshold above is individually necessary (dollar volume 2000000, buy-green marker, price 10, depth60 70, ret60 0, vol20 0.09, and the volatility test for this sleeve: volatility="all" imposes no atr_ratio test (a missing atr_ratio does not block).).
- Check that fires are consumed in list order, at most one entry is produced per evaluation, a held symbol is skipped, and the slot cap of 25 blocks entries.
- Check the mode rule stated above for capital_mode=delay.
- Check sizing: qty equals int(400.0 // execution price), with the reprice switch ON sizing off the current close and refusing above 10, and OFF sizing off the fire price.
- Check the only exit is the 260-session / exit_at deadline exit defined above, and that any exit suppresses entries in the same evaluation.
