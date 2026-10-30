# s_mn_nostop: Recreation package

Provenance: Source row in strategies/midna/mn-hourly-playbook.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset US equities, timeframe 1h, universe Midna's swing basket, style Tensor signal). The card's Variants table lists the Lazarus lane midna_nostop as no stop, 60 hour bars; its Code section states the v3 forms in sleeves/lazarus/s_mn_hourly.py and sleeves/lazarus/s_mn_nostop.py calling laz_sleeves._common.

## What this sleeve is
This sleeve is the no-stop variant of the hourly Midna signal sleeve: it buys one name flagged by the desk Tensor-bundle hourly signal at $1,000 and exits only after more than 60 hourly bars, with no price stop. It is a v3-native thin module in laz_sleeves/ that delegates to mn_hourly_evaluate in laz_sleeves/_common.py with stop=False and slots=1.

## Full algorithm
Module (laz_sleeves/s_mn_nostop.py): SLEEVE_ID = "s_mn_nostop", INPUTS = ("bars_1hour", "positions", "midna_signals"); evaluate returns mn_hourly_evaluate(view, ctx, "s_mn_nostop", stop=False, slots=1) with the shared defaults slot_usd=1000.0 and time_bars=60.

Shared evaluation (laz_sleeves/_common.py mn_hourly_evaluate), in code order:
1. Session: sess = the date from view now; unparseable means no intents.
2. Exit, for this sleeve's non-zero position: bars are view bars under "SYM|1Hour"; with no bars the position is skipped. The stop branch is disabled for this sleeve (stop=False), so no price fall exits it. If bars held (hourly bars with t after opened_at) > 60, emit a full-qty exit, reason mn_time_bars.
3. Slot gate: if 1 position is held, return the exit only.
4. Entries: signals = view midna_signals {symbol: {signal: bool}}; symbols are visited in sorted order, skipping the held symbol and symbols whose signal is falsy, and symbols with no hourly bars.
5. Cross-stale gate (ENH20, on by default; off via extra s_mn_nostop_enh20 xstale_gate=False): refuse when the symbol's last 1Hour bar lags the latest 1Hour bar among signalled symbols by more than 4 hours, with a paired journal record to extra enh20_journal.
6. Sizing and intent: qty = int(1000.0 // last hourly close); qty at or below 0 is skipped. Emit a market, day entry, price_hint = last, reason mn_hourly_signal. ENH19 slot guard (on by default; extra s_mn_nostop_enh19 slot_guard) stops entries once held + entries emitted reaches 1.

Position management: one position, $1,000; the only exit is the 60-bar time exit.

## Files in this repo
- Sleeve module (desk laz_sleeves/s_mn_nostop.py): `laz_sleeves/s_mn_nostop.py`; also present as `sleeves/lazarus/s_mn_nostop.py` and `integration/s_mn_nostop_adapter.py`.
- Shared engine (desk laz_sleeves/_common.py, mn_hourly_evaluate): `engines/laz_sleeves/_common.py` in engines_map.json with status gate_blocked, so that exact repo copy is not present.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-hourly-playbook.md`.

## Configuration
- Universe: symbols flagged in midna_signals (Midna's swing basket upstream). Asset: US equities. Timeframe: 1h (bars_1hour, 1Hour bars).
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; 1 slot x $1,000 in the module call.
- Cadence: 3600 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars_1hour, positions, midna_signals.

## Data inputs
- bars_1hour: view["bars"] under "SYM|1Hour", bars with t, c. Producer: the desk hourly-bars producer for the snapshot.
- positions: view["positions"] rows with symbol, qty, avg_price, opened_at and sleeve_id.
- midna_signals: view["midna_signals"] {symbol: {signal: bool}}, the desk Tensor-bundle hourly signal product (shared _common.py header); the upstream fire file is unreachable from the desk, and this bundle product is the recorded substitution.

## Install and run
1. Place the module at laz_sleeves/s_mn_nostop.py and its shared engine at laz_sleeves/_common.py in the fresh desk (repo copies: `laz_sleeves/s_mn_nostop.py` for the module; the _common repo copy is gate_blocked in engines_map.json, so take _common.py from the desk source tree).
2. Register the roster row for `s_mn_nostop` exactly as in the Configuration section in config/sleeves.json (module laz_sleeves.s_mn_nostop, cadence 3600, session rth, $1,000 slice, inputs bars_1hour/positions/midna_signals).
3. Wire the producers so every snapshot carries 1Hour bars, this sleeve's position, view midna_signals, and view now.
4. First evaluation: call evaluate(view, ctx) on the module. Confirm an empty midna_signals map returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the no-stop rule: a position down 30 percent with 60 or fewer bars held produces no exit.
- Check the time exit: a position with 61 hourly bars after opened_at exits with reason mn_time_bars; at exactly 60 it does not.
- Check entries and the single slot: the first signalled symbol in sorted order enters at int(1000 // last), a held position suppresses all entries, and unflagged symbols never enter.
- Check the cross-stale gate: a signalled symbol whose last hourly bar lags the universe latest by more than 4 hours is refused and journaled; turning the ENH20 switch off restores it.
