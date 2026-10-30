# aster_r19_tensor_g4_red_timeout_25: Recreation package

Provenance: Ausar R17/R18 Tensor research on the archived v615 engine (Source row in strategies/ausar/r19-tensor-g4.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This sleeve buys cheap, deeply drawn-down US stocks on a weekly Tensor buy-green fire and holds each for about 52 weeks. Its mode is red_timeout and its volatility cut is all. It is a thin wrapper delegating to desk3/aster_batch15.py with its own SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch15.py): family="G4", mode="red_timeout", volatility="all", slots=25, ticket=400.0, inputs=("tensor_fires", "bars", "positions"), cadence_s=86400. Slice constant SLICE=10000.0.

G4 pass gate (g4_passes, applied to each Tensor fire's feature record): markers include "buy-green" AND native_close <= 10 AND depth60 >= 70 AND ret60 >= 0 AND vol20 >= 0.09 AND dv20 >= 2000000 AND the volatility test: volatility="all" imposes no atr_ratio test. A fire missing any required field fails closed.

Evaluation order in desk3/aster_batch15.py::_eval_g4:
1. Exits first: the 52-week scheduled exit is the only G4 exit. For each non-zero position (except QQQ in reserve mode, see below), compute the exit session as the last session of the week that is 51 weeks after the Monday of the entry week, using the session calendar from the snapshot; if today >= that exit session, exit the whole quantity with reason `52_week_scheduled_exit`. If the calendar does not extend past the target week, no exit date is formed. If any exit is produced, return only exits. No stop and no target.
2. If there is no session calendar, entries refuse (sessions are never invented).
3. Pending housekeeping: a pending candidate whose symbol is now held becomes owned; a pending candidate whose entry_date or wait_expires is before today becomes expired_unfilled.
4. New candidates: fires passing g4_passes, with a signal_end date, not already seen or pending, sorted by dv20 descending then symbol. Skip a candidate whose symbol or issuer_id is already held (issuer_already_owned) and skip when occupied positions plus pending reach slots=25 (slot_limit).
5. Entry-date rule for mode="red_timeout": at least 6 following sessions are required; the candidate pends with wait_sessions = following[:6], wait_expires = following[5] and no entry_date yet.
6. Red-timeout trigger scan (before entries, in the entry window logic): for each pending candidate without an entry_date, scan its first 5 wait sessions in order; for a session with both the stock's and QQQ's daily bars and a prior QQQ session, red = QQQ close < prior QQQ close AND stock close <= 1.02 * signal_close. On the first red session, or at the 5th scanned session (i == 4, the timeout), set entry_date to the next session after that session and record wait_trigger as "red" or "timeout". A missing bar breaks the scan for that candidate.
5. Entry window: 09:30 <= ET time < 09:35, extended to < 10:30 by the execution-window grace enhancement (switch enhance_window_grace, default ON; OFF restores the 09:35 rule exactly), with the price guards re-checked at entry in grace.
6. Entry sizing: price is the buy quote, else the last 1Day close. Fee schedule _fee_bps_price: 30 bps if price < 5, 15 bps if price < 20, else 10 bps. units = floor(min(ticket=400.0, cash) / (price * (1 + fee))). Refuse if units <= 0. Cash is view.slice.cash_usd or 10000.0 and is decremented per entry in the same evaluation. Entry intent is a market day buy_to_open with price_hint = price and reason naming frozen_weekly_G4 and mode=red_timeout.

Position management: at most 25 slots, one position per issuer, no pyramiding in this evaluation logic.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_r19_tensor_g4_red_timeout_25.py` (also `sleeves/aster_r19_tensor_g4_red_timeout_25.py` and `integration/aster_r19_tensor_g4_red_timeout_25_adapter.py`).
- Shared engine: `desk3/aster_batch15.py` (this sleeve's SPECS entry, g4_passes and _eval_g4).
- Existing family card: `strategies/ausar/r19-tensor-g4.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: symbols named by passing Tensor fires; the existing card states the frozen 1,838-name research cohort. Asset: US equities. Timeframe: weekly Tensor fires; 1Day bars for prices and the session calendar.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; ticket 400.0, slots 25; bp_buffer_frac=0.02.
- Cadence: 86400 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row: tensor_fires, bars, positions. Producers in the engine PRODUCERS tuple: tensor_bundle -> tensor_fires (freshness_sla_s 93600), bars -> bars (900), broker_readback -> positions (900), quotes -> quotes (60).
- tensor_fires: view["tensor_fires"] or view["extra"]["tensor_fires"]; each fire carries symbol, issuer_id, signal_end, markers/primaryMarkers, native_close, depth60, ret60, vol20, dv20 and atr_ratio.
- bars: view["bars"] keyed by `<symbol>|1Day` or symbol; also supplies the session calendar (extra session_dates, else SPY/QQQ bar dates).
- positions: view["positions"] rows with symbol, qty, opened_at and issuer_id.
- State: ctx state_dir / aster_batch15_state.json holds pending, seen and (in reserve mode) funding_targets and reserve_week per sleeve.

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_r19_tensor_g4_red_timeout_25.py` with SLEEVE_ID = "aster_r19_tensor_g4_red_timeout_25" (the repo also carries `sleeves/aster_r19_tensor_g4_red_timeout_25.py` and `integration/aster_r19_tensor_g4_red_timeout_25_adapter.py` copies).
2. Register the roster row for `aster_r19_tensor_g4_red_timeout_25` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_r19_tensor_g4_red_timeout_25, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_batch15.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check g4_passes on fixtures: each threshold above is individually necessary (buy-green marker, close 10, depth60 70, ret60 0, vol20 0.09, dv20 2000000, and the volatility test for this sleeve: volatility="all" imposes no atr_ratio test).
- Check candidate ranking is dv20 descending then symbol, the 25-slot cap, and the one-per-issuer skip.
- Check the mode-specific entry-date rule stated in the Full algorithm section for mode=red_timeout, and that no entry occurs outside the entry window (09:35 cutoff with grace OFF, 10:30 with grace ON).
- Check sizing: units equal floor(min(400.0, cash) / (price * (1 + fee))) with the 30/15/10 bps price fee schedule.
- Check the only exit is the 52-week scheduled exit as defined above, and that it suppresses entries in the same evaluation.
