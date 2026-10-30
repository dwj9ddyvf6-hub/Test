# s_mn_hourly: Recreation package

Provenance: Source row in strategies/midna/mn-hourly-playbook.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset US equities, timeframe 1h, universe Midna's swing basket, style Tensor signal). The card's Code section states the Midna v3 forms in sleeves/lazarus/s_mn_hourly.py and sleeves/lazarus/s_mn_nostop.py calling laz_sleeves._common.

## What this sleeve is
This sleeve buys names flagged by the desk Tensor-bundle hourly Midna signal, up to 12 slots at $1,000 each, exiting on a 15 percent stop or after more than 60 hourly bars. It is a v3-native thin module in laz_sleeves/ that delegates to mn_hourly_evaluate in laz_sleeves/_common.py with stop=True and slots=12. Signal generation stays upstream in the Tensor bundle.

## Full algorithm
Module (laz_sleeves/s_mn_hourly.py): SLEEVE_ID = "s_mn_hourly", INPUTS = ("bars_1hour", "positions", "midna_signals"); evaluate returns mn_hourly_evaluate(view, ctx, "s_mn_hourly", stop=True, slots=12) with the shared defaults slot_usd=1000.0 and time_bars=60.

Shared evaluation (laz_sleeves/_common.py mn_hourly_evaluate), in code order:
1. Session: sess = the date from view now; unparseable means no intents.
2. Exits, for each of this sleeve's non-zero positions: bars are view bars under "SYM|1Hour"; with no bars the position is skipped. last = the last hourly close; entry = avg_price. If stop is on (this sleeve) and entry > 0 and last <= entry x 0.85, emit a full-qty exit, reason mn_stop15. Else if bars held (hourly bars with t after opened_at) > 60, emit a full-qty exit, reason mn_time_bars.
3. Slot gate: if the number held is at least 12, return the exits only.
4. Entries: signals = view midna_signals {symbol: {signal: bool}}; symbols are visited in sorted order, skipping held symbols and symbols whose signal is falsy, and symbols with no hourly bars.
5. Cross-stale gate (ENH20, on by default; off via extra s_mn_hourly_enh20 xstale_gate=False): refuse when the symbol's last 1Hour bar lags the latest 1Hour bar among signalled symbols by more than 4 hours, with a paired journal record to extra enh20_journal.
6. Sizing and intent: qty = int(1000.0 // last); qty at or below 0 is skipped. Emit a market, day entry, price_hint = last, reason mn_hourly_signal. ENH19 slot guard (on by default; extra s_mn_hourly_enh19 slot_guard): stop after the entry that makes held + entries emitted reach 12; with the guard off, the pre-change test (held + 1 >= slots) applies.

Position management: at most 12 positions, $1,000 each; exits are only the 15 percent stop and the 60-bar time exit.

## Files in this repo
- Sleeve module (desk laz_sleeves/s_mn_hourly.py): repo copy at `sleeves/lazarus/s_mn_hourly.py` (561 bytes in the tree); also present as `integration/s_mn_hourly_adapter.py`. The desk path laz_sleeves/s_mn_hourly.py itself is not in the repo tree.
- Shared engine (desk laz_sleeves/_common.py, mn_hourly_evaluate): `engines/laz_sleeves/_common.py` in engines_map.json with status gate_blocked, so that exact repo copy is not present.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-hourly-playbook.md`.

## Configuration
- Universe: symbols flagged in midna_signals (Midna's swing basket upstream). Asset: US equities. Timeframe: 1h (bars_1hour, 1Hour bars).
- Sizing / slice: capital_usd 12000.0, cash_usd 12000.0 in the roster row; 12 slots x $1,000 in the module call.
- Cadence: 3600 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars_1hour, positions, midna_signals.

## Data inputs
- bars_1hour: view["bars"] under "SYM|1Hour", bars with t, c. Producer: the desk hourly-bars producer for the snapshot.
- positions: view["positions"] rows with symbol, qty, avg_price, opened_at and sleeve_id.
- midna_signals: view["midna_signals"] {symbol: {signal: bool}}, the desk Tensor-bundle hourly signal product (shared _common.py header); the upstream fire file is unreachable from the desk, and this bundle product is the recorded substitution.

## Install and run
1. Place the module at laz_sleeves/s_mn_hourly.py and its shared engine at laz_sleeves/_common.py in the fresh desk (repo copies: `sleeves/lazarus/s_mn_hourly.py` for the module; the _common repo copy is gate_blocked in engines_map.json, so take _common.py from the desk source tree).
2. Register the roster row for `s_mn_hourly` exactly as in the Configuration section in config/sleeves.json (module laz_sleeves.s_mn_hourly, cadence 3600, session rth, $12,000 slice, inputs bars_1hour/positions/midna_signals).
3. Wire the producers so every snapshot carries 1Hour bars, this sleeve's positions, view midna_signals, and view now.
4. First evaluation: call evaluate(view, ctx) on the module. Confirm an empty midna_signals map returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the stop: a position at or below 85 percent of its average price exits with reason mn_stop15; at 86 percent with 60 or fewer bars held it does not exit.
- Check the time exit: a position with 61 hourly bars after opened_at exits with reason mn_time_bars; at exactly 60 it does not.
- Check entries and slots: signalled, unheld symbols enter in sorted order at int(1000 // last) shares, entries stop when held + emitted reaches 12, and a full book of 12 emits exits only.
- Check the cross-stale gate: a signalled symbol whose last hourly bar lags the universe latest by more than 4 hours is refused and journaled; turning the ENH20 switch off restores it.
