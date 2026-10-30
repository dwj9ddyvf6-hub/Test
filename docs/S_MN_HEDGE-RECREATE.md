# s_mn_hedge: Recreation package

Provenance: Source row in strategies/midna/mn-qqq-flip5-tza.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset leveraged ETF, timeframe 1d, universe TZA (QQQ signal), style hedge). The card's Code section states the Midna v3 form in sleeves/lazarus/s_mn_hedge.py reading a hedge_signal input, $300 of a $1,000 budget.

## What this sleeve is
This sleeve is a QQQ hedge: when the upstream hedge_signal is on, it holds TZA (the 3x inverse small-cap ETF) at 30 percent of its $1,000 budget, in a single slot. It exits when the signal turns off or after 20 sessions. It is a v3-native module in laz_sleeves/ whose evaluate(view, ctx) runs directly on the snapshot view using the shared laz_sleeves/_common.py helpers.

## Full algorithm
Module constants (laz_sleeves/s_mn_hedge.py): BUDGET_USD = 1000.0, WEIGHT = 0.30, MAX_SESSIONS = 20. SLEEVE_ID = "s_mn_hedge", INPUTS = ("bars_1day", "positions", "hedge_signal").

Evaluation, in code order:
1. Session: sess = the date from view now; if it cannot be parsed, return no intents.
2. Held positions are this sleeve's non-zero positions from view positions (a position with another sleeve_id is ignored); bars are view bars under the key "TZA|1Day"; on = (view hedge_signal is exactly True).
3. Exits, for each held position (skipped if there are no TZA bars): last = the last TZA close. If the signal is not on, emit a full-qty exit, reason mn_hedge_signal_off. Else if sessions held (daily bars strictly after opened_at) >= 20, emit a full-qty exit, reason mn_hedge_max20.
4. Entry gate: if anything is held, or the signal is not on, or there are no TZA bars, return the exits only (single slot).
5. ENH19 stale-bar gate (on by default; switch extra s_mn_hedge_enh19 stale_gate): if the last TZA bar's date is more than 4 calendar days before the session, refuse the entry and journal a paired record (exp ENH19-LAZB7-20261024) to extra enh19_journal. Exits are untouched.
6. Sizing and intent: qty = int((1000.0 x 0.30) // last) = int(300.0 // last); qty at or below 0 returns nothing. Emit one market, day entry for TZA, price_hint = last, reason mn_hedge_signal_on.

Position management: one TZA position only; no price stop; the only exits are signal-off and the 20-session cap.

## Files in this repo
- Sleeve module (desk laz_sleeves/s_mn_hedge.py): `laz_sleeves/s_mn_hedge.py`; also present as `sleeves/lazarus/s_mn_hedge.py` and `integration/s_mn_hedge_adapter.py`.
- Shared engine (desk laz_sleeves/_common.py): `engines/laz_sleeves/_common.py` in engines_map.json with status gate_blocked, so that exact repo copy is not present; the module's helpers (_session, _bars, _positions, _sessions_held, _intent, _qty_for, _bar_stale, _enh19_on, _journal19) are the ones named in the module import.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-qqq-flip5-tza.md`.

## Configuration
- Universe: TZA only (the signal is QQQ-based, upstream). Asset: leveraged ETF. Timeframe: 1d (bars_1day).
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; entry notional is 30 percent of $1,000 = $300 in the module.
- Cadence: 86400 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars_1day, positions, hedge_signal.

## Data inputs
- bars_1day: view["bars"] under "TZA|1Day", bars with t and c. Producer: the desk daily-bars producer for the snapshot (the module declares the input name bars_1day).
- positions: view["positions"] rows with symbol, qty, opened_at and sleeve_id.
- hedge_signal: view["hedge_signal"], a boolean from the Midna signal product (QQQ hedge signal, per the shared _common.py header); the card notes it has no producer in this repo, so an absent signal means the sleeve stays flat or exits a held position.

## Install and run
1. Place the sleeve module at laz_sleeves/s_mn_hedge.py and its shared helpers at laz_sleeves/_common.py in the fresh desk (repo copies: `laz_sleeves/s_mn_hedge.py` for the module; the _common repo copy is gate_blocked in engines_map.json, so take _common.py from the desk source tree).
2. Register the roster row for `s_mn_hedge` exactly as in the Configuration section in config/sleeves.json (module laz_sleeves.s_mn_hedge, cadence 86400, session rth, $1,000 slice, inputs bars_1day/positions/hedge_signal).
3. Wire the producers so every snapshot carries TZA daily bars, this sleeve's positions, view hedge_signal, and view now.
4. First evaluation: call evaluate(view, ctx) on the module. Confirm hedge_signal absent or false with nothing held returns no intents, and hedge_signal true with fresh TZA bars returns one TZA entry, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the signal gate: hedge_signal missing, false, or a truthy non-boolean value produces no entry; exactly True is required.
- Check sizing: at a TZA close of $15.00 the entry quantity is int(300 // 15) = 20 shares; a close above $300 produces no entry.
- Check the exits: a held position exits the first evaluation the signal is off, and exits at 20 sessions held even with the signal still on; at 19 sessions with the signal on it is held.
- Check the single slot and the stale gate: a held position suppresses new entries, and a TZA bar more than 4 calendar days old refuses an entry (journaled) but never an exit.
