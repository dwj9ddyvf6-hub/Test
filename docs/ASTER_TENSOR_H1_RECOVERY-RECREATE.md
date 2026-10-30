# aster_tensor_h1_recovery: Recreation package

Provenance: Ausar R11 Tensor state research (Source row in strategies/ausar/tensor-state-repair.md in this repo).

## What this sleeve is
This sleeve buys US stocks whose seven Tensor vote channels have repaired over the last four 1h panel bars and sells each position 20 native bars after entry. This book reads the 1h frame (1Hour bars). It is a thin wrapper delegating to desk3/aster_batch1.py with its own SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch1.py): kind="tensor", frame="1h", tf="1Hour", cadence_s=3600, session="rth". Engine constants: VOTE_NAMES=("stoch", "aroon", "di", "obv", "squeeze", "pivot", "wave"); TENSOR_EXCLUDED={SPY, QQQ, B, GOLD}; slots are enforced as free = 10 - number of held positions (10 slots).

Evaluation order in desk3/aster_batch1.py::_eval_tensor (reached from evaluate):
1. Exits first, over held positions with qty > 0, symbols in sorted order. Held bars are computed, in preference order: (a) current panel bar_index/index minus the position's entry_bar_index; (b) the position's bars_held / sessions_held / held_bars field, else the count of 1Hour bars timestamped after opened_at/entry_at; (c) the sleeve state file's entry_bar_index or entry_at for that symbol, used the same two ways. If held >= 20 native bars, exit the whole quantity (int when integral), reason naming hold_20_native_bars, priced at the last 1Hour bar close when available, and remove the symbol from state. If any exit is produced, save state and return only the exits. No stop and no target.
2. Slot cap: if 10 - len(positions) <= 0, return no entries (positions here counts every non-zero position row, long or short).
3. Candidate scan over the Tensor panels for frame "1h" (panels whose stated frame does not match this frame are ignored). Skip symbols in TENSOR_EXCLUDED, symbols already held, and panels with fewer than 4 rows. Use the last 4 rows (the current bar and the bar 3 bars earlier are the endpoints):
   a. total_votes must equal 7 at both endpoint rows (total_votes field, else the count of non-null votes among the 7 channels).
   b. native_status / status, when present on the current row, must equal "ready".
   c. Current row fields: close >= 5, dollar_volume20 >= 1000000, atr14 > 0; any missing or non-numeric field fails the candidate closed.
   d. Repair: balance(current) - balance(first) >= 2, where balance is the row balance field, else bullish_votes - bearish_votes, else (count of votes == 1) - (count of votes == -1) over the 7 channels.
   e. Rising channels: at least 2 of the 7 vote channels must strictly increase across at least one adjacent transition within the 4 rows.
   f. Warming: when the current row carries bar_index/index, refuse if index + 1 < 234.
   g. Cooldown: refuse if the current index is below next_eligible_bar_index for the symbol, taken from the sleeve state file, overridden per-symbol by view extra["next_eligible_bar_index"] when that dict is supplied. Entries set next_eligible_bar_index = entry index + 20.
   h. Score = repair + 0.01 * balance(current) + 0.001 * clip(obv_slope5 / volume, -10, 10), with the ratio taken as 0 when volume <= 0 (obv_slope5 defaults to 0.0, volume to 0.0).
4. Ranking and entries: candidates are sorted by score descending, then symbol ascending, and filled in that order until the free slots are used. For each:
   a. Execution-price revalidation (ENH-B13-TENSORREC-REPRICE-20261024, switch exec_reprice under extra/ctx key aster_tensor_rec_enh, default ON): when a current 1Hour bar exists, refuse if its last close < 5 and otherwise size off that current close instead of the panel close. OFF restores the panel-close rule exactly.
   b. Sizing: budget = min(0.10 * equity, 0.01 * dollar_volume20, cash), where equity is slice capital_usd (else ctx/view equity, default 10000.0) and cash is slice cash_usd (else equity). shares = int(budget // (execution close * 1.001)); refuse if shares < 1. Cash is decremented by shares * execution close * 1.001 per entry in the same evaluation.
   c. Entry intent: market order, time_in_force "day" for equity symbols, qty = shares, price_hint = execution close, reason naming state_repair; the intent carries no legs, so no position_intent field is set by this engine's intent builder. State is recorded for the symbol (entry_bar_index, next_eligible_bar_index = index + 20, entry_at = now) and saved when any entry or exit is produced.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_tensor_h1_recovery.py` (also `sleeves/aster_tensor_h1_recovery.py` and `integration/aster_tensor_h1_recovery_adapter.py`); the wrapper exposes INPUTS = inputs_for(SLEEVE_ID) from the engine.
- Shared engine: `desk3/aster_batch1.py` (this sleeve's SPECS entry, _tensor_panels, _eval_tensor and evaluate).
- Contract type: desk3/contract.py, whose repo copy is at `engines/desk3/contract.py` in engines_map.json with status gate_blocked, so that copy was not vendored by the engines pass; the desk original must be supplied from desk3/contract.py to run.
- Existing family card: `strategies/ausar/tensor-state-repair.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: 1,820 hourly names per the existing card, minus the engine exclusions SPY, QQQ, B and GOLD. Asset: US equities. Timeframe: 1h Tensor panels; 1Hour bars.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; budget and share formula in the Full algorithm section; 10 slots; bp_buffer_frac=0.02.
- Cadence: 3600 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row and by inputs_for for kind="tensor": tensor, bars, positions. Producers in the engine PRODUCERS tuple: bars -> bars (freshness_sla_s 900), tensor_bundle -> tensor (86400), broker_readback -> positions (900); the tuple also declares quotes (60), options_chain (300) and opening_events (300) for other kinds in the same engine, not used by this sleeve.
- tensor: view["tensor"] as a dict keyed by symbol (rows as a list, a dict with a features list, or a single votes/balance row) or a list of rows grouped by symbol; each row carries the 7 votes (votes dict/list or vote_<name> fields), balance or bullish/bearish votes, total_votes, native_status/status, close/price, atr14, dollar_volume20, volume, obv_slope5, bar_index/index and frame. The engine header states that with no tensor key in the snapshot the sleeve is UNFED, never fake-fed.
- bars: view["bars"] keyed by `<symbol>|1Hour` or symbol, in the bar row shape the engine normalises (o/h/l/c/v or open/high/low/close/volume, t/timestamp).
- positions: view["positions"] rows with symbol, qty, entry_bar_index, bars_held/sessions_held/held_bars, opened_at/entry_at.
- State: ctx state_dir / aster_b1_aster_tensor_h1_recovery.json holds per-symbol entry_bar_index, next_eligible_bar_index and entry_at.

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_tensor_h1_recovery.py` with SLEEVE_ID = "aster_tensor_h1_recovery" (the repo also carries `sleeves/aster_tensor_h1_recovery.py` and `integration/aster_tensor_h1_recovery_adapter.py` copies).
2. Register the roster row for `aster_tensor_h1_recovery` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_tensor_h1_recovery, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_batch1.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the panel gates on fixtures: fewer than 4 rows, total_votes other than 7 at either endpoint, a non-ready status, close below 5, dollar_volume20 below 1000000, atr14 at or below 0, repair below 2, and fewer than 2 rising channels each produce no entry.
- Check the excluded symbols SPY, QQQ, B and GOLD never enter, and that a held symbol is skipped.
- Check ranking is score descending then symbol ascending, with the score formula stated above, and that entries stop at 10 held positions.
- Check the warming rule (index + 1 < 234 refuses) and the cooldown rule (index below next_eligible refuses; an entry sets next_eligible to entry index + 20).
- Check sizing: shares equal int(min(0.10 * equity, 0.01 * dollar_volume20, cash) // (execution close * 1.001)), with the reprice switch ON using the current 1Hour close and refusing below 5, and OFF using the panel close.
- Check the only exit fires at held >= 20 native bars by each of the held-count routes stated above, removes the symbol from state, and suppresses entries in the same evaluation.
