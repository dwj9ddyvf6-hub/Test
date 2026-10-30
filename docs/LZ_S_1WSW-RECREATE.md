# lz_s_1wsw - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Lab 1W Swing covered (test)", type forecast and ML models, family 1w, algorithm grade PARTIAL with gap: sizing not recorded in any consulted source. Accounting entry (verbatim): entry {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}; exit {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 126 sessions)", "hold_from": "fill", "hold_unit_kind": "1d", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}; data: lab_live books (native Lazarus routing) :: DESK_INTEGRATION/lab_live/out/latest/*.json. Alias lz_s_1wsw, status md2_catalog installed. Classification evidence in the accounting: this row consumes lab_live model books with a 126-session hold, and the same strategy's non-test entry (Lab 1W Swing covered) is recorded as forecast and ML models.
- The canonical id carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same lane uses the id without the lz_ prefix, s_1wsw. That mapping is evidenced by the identical label, entry, exit and data source in the lz_engine config row for s_1wsw (see Configuration) and by the existing recreation package for the unprefixed form, `docs/S_1WSW-RECREATE.md`.
- Existing Test packages for the unprefixed form: `docs/S_1WSW-RECREATE.md` and `docs/S_1WSW-ALGORITHM.md`; strategy doc `strategies/lazarus/lz-lab-1w-swing.md` (Family Lazarus; source research lab (lab_live); one attribution token in that doc's source row is blocked by the repo gate and is omitted here, the rest is as recorded there).
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `sleeves/s_1wsw.py`, `adapters3/laz_s_1wsw.py`, `desk3/lazarus.py` SPECS entry s_1wsw, `config/sleeves.json` row s_1wsw and `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_1wsw: all found in Test, listed under Files in this repo); dwj9ddyvf6-hub/Silicon (recursive tree: no lazarus 1wsw sleeve path); dwj9ddyvf6-hub/quant-research-backup (recursive tree: lab book parquet outputs exist there under CANDLES/out/LABBOOKS, but no executable sleeve code for this lane; nothing vendored, Test holds the executable engine and adapter); dwj9ddyvf6-hub/Midna (recursive tree: no 1wsw sleeve path). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

A long-only US equity Lazarus fire-consumer lane for the lab's 1W Swing covered book: signal generation stays upstream in the lab_live books, and this lane buys fresh matching fires into its single slot on a QQQ-down (fear_day) basis, with a 15% disaster stop and a 126-session time exit. It is a covered (test) form of the Lab 1W Swing book, staged unarmed on the desk ("ready (unarmed: desk staged)" in the lz_engine config status text).

## Full algorithm

Two layers, both in the record; do not merge them.

Layer A - the md2 / lz_engine lane record for this canonical id (accounting, verbatim values):
1. Entry wrapper: policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day.
2. Exit wrapper: the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 126 sessions), hold_from fill, hold_unit_kind 1d, stop_pct null, max_bars null, plan_overrides [].
3. Data: lab_live books (native Lazarus routing), files DESK_INTEGRATION/lab_live/out/latest/*.json.
4. Sizing: not in the accounting record (accounting gap). The lz_engine config row for the unprefixed form records sizing budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000 (see Configuration).

Layer B - the executable engine in Test (`desk3/lazarus.py`, SPECS entry s_1wsw, reached through the thin adapter `sleeves/s_1wsw.py` / `adapters3/laz_s_1wsw.py`, whose evaluate(view, ctx) delegates to desk3.lazarus.evaluate with SLEEVE_ID s_1wsw):
1. SPECS entry: slots 1, capital 1000.0, cadence_s 3600, session rth, max_age_min 11520 (60*24*8), qqq_down True, stop_pct 0.15, horizon_sessions 126, family swing, tf 1W. No cap_tier, signal_tier, max_price, deep or min_vix key is set.
2. Exits first, per held position, first trigger wins, and if any exit intent is emitted the call returns with no entries evaluated: (1) stop: current price (fire price if carried, else latest bar close) at or below avg_price * (1 - 0.15), sold in full, reason s_1wsw_stop15, with entry stop_price = round(price * 0.85, 4); (2) target: current price at or above the target_price stored in sleeve state at entry, sold in full; (3) time: sessions held at or above the stored horizon_sessions (or the spec horizon 126 when no stored value exists), sold in full. Sessions held are counted from extra session_dates when supplied, else SPY bar dates, else business days. Exits are market, day, sell. The partial and target_pct branches do not apply to this SPECS entry (it sets neither).
3. Entries, only when no exit fired and open positions are fewer than slots (1): fires are read from view lazarus_fires, extra lazarus_fires, view tensor_fires, or extra fires (the first list found). A fire is skipped when it is not a dict, its sleeve_id (when present) differs from this sleeve, its symbol is missing or already held, its side is not buy/long, its fired_at/ts is unparseable, or its age is below 0 or above max_age_min 11520.
4. Sleeve-specific gates: the QQQ-down gate applies (the fire's qqq_red/qqq_down value, or QQQ red derived from QQQ bars when absent; missing QQQ-red data means no entry); family swing and timeframe 1W are enforced only on fires carrying a family/color field; signal-tier and cap-tier filters are enforced only when the fire carries that field and the spec sets one (this spec sets neither).
5. Price: the fire price is the base price, falling back to the latest bar close; with the fresh-price enhancement on by default (ENH-LAZ-REPRICE-20261024; switched by extra s_1wsw_improve fresh_price), sizing, stop anchor and price_hint use the freshest completed bar close when it exists and differs, with the fire-price decision recorded as the paired shadow control on the intent. The bound guard (ENH19-LAZ-BOUND-20261024, on by default) then refuses an entry whose fresh price is at or above the fire target_price.
6. Sizing in the engine: per_slot = capital / slots = 1000.0; qty = int(per_slot // execution price); qty below 1 emits nothing. Entry intents are market, day, buy, reason s_1wsw_tensor_fire, with stop_price = round(price * (1 - 0.15), 4). On entry the sleeve state file (laz_state.json under ctx state_dir) records horizon_sessions, target_price and entry_at. Entries stop once the slot is filled.
7. Fail-closed: no fresh matching fire means no entry; the engine consumes only ingested fires and never fetches the upstream tracker itself.

## Files in this repo

- This package: `docs/LZ_S_1WSW-RECREATE.md`
- Adapter / sleeve module (already in Test): `sleeves/s_1wsw.py` (thin wrapper; SLEEVE_ID s_1wsw; engine desk3/lazarus.py); also at `adapters3/laz_s_1wsw.py` and `integration/s_1wsw_adapter.py`.
- Shared engine (already in Test): `desk3/lazarus.py` (SPECS entry s_1wsw and evaluate()).
- Existing packages for the unprefixed form: `docs/S_1WSW-RECREATE.md`, `docs/S_1WSW-ALGORITHM.md`.
- Strategy doc: `strategies/lazarus/lz-lab-1w-swing.md`.
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row s_1wsw; roster row s_1wsw in `config/sleeves.json` (also `engines/config/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, entry "Lab 1W Swing covered (test)".

## Configuration

- lz_engine config row for s_1wsw in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim values): kind 1w, label "Lab 1W Swing covered (test)", enabled true, state live, status_text "ready (unarmed: desk staged)", source {producer: "lab_live books (native Lazarus routing)", file: "DESK_INTEGRATION/lab_live/out/latest/*.json", lane: "s_1wsw"}, entry and exit as in Layer A above (the row's entry is the fear_day block and its exit hold is 126 sessions), sizing {budget_usd 1000, max_slots 1, position_usd 1000, position_usd_by_class {}, one_share_max_usd null, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, global_slot_usd 1000, min_dv20_usd 100000}, research lines naming DESK_INTEGRATION/DESK_PLAN.md F1 (1W swing covered search) + F2 and the desk playbook lane t_1wsw, flags [].
- Roster row for s_1wsw in `config/sleeves.json`: module adapters3.laz_s_1wsw, cadence_s 3600, session rth, slice capital_usd 1000.0 and cash_usd 1000.0, bp_buffer_frac 0.02, flat_by_close false, flatten_time_et null, params {}, inputs [lazarus_fires, bars, positions], parked false.
- Engine SPECS values are in the Full algorithm, Layer B.

## Data inputs

- lab_live book files (DESK_INTEGRATION/lab_live/out/latest/*.json) as the upstream signal source for the lane record; on the desk the engine consumes ingested fires in the snapshot: view lazarus_fires (or extra lazarus_fires / view tensor_fires / extra fires), fire dicts {sleeve_id, symbol, fired_at, price, target_price?, horizon_sessions?, cap_tier?, signal_tier?, color/family?, qqq_red?, stock_red?}.
- Daily bars {SYM|1Day} (and SPY bars for the session-count fallback, QQQ bars for the red check), and positions from the snapshot.
- Sleeve state from laz_state.json under the ctx state_dir.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, the accounting entry in `docs/ALL-SLEEVES.json`, and the unprefixed package `docs/S_1WSW-RECREATE.md`.
3. Place the adapter at `sleeves/s_1wsw.py` (also `adapters3/laz_s_1wsw.py`) and the shared engine at `desk3/lazarus.py`, at those repo paths.
4. Register the config rows for s_1wsw from `config/sleeves.json` and `packages/grokbot/rl64/lz_engine/config/sleeves.json` exactly as given in Configuration, with no parameter overrides (roster params {}).
5. Wire the producers named in Data inputs so lazarus_fires, bars and positions arrive in the snapshot view in the shapes the Full algorithm describes.
6. Run the desk cycle; the entry point is the adapter's evaluate(view, ctx), which delegates to desk3.lazarus.evaluate(SLEEVE_ID, view, ctx). Verify against the Verification section before enabling live paper routing.

## Verification

Behaviour spec derived from the Full algorithm (no per-sleeve test file for this exact canonical id is present in this repo):

- Entry fixture: one fresh fire (age within 11520 minutes) matching family swing / tf 1W on a QQQ-down day, with the slot free, produces one market buy sized int(1000.0 // execution price) with stop_price round(price * 0.85, 4) and reason s_1wsw_tensor_fire.
- No-entry fixtures: the same fire aged past 11520 minutes, on a day that is not QQQ-down, with side not buy/long, or with QQQ-red data missing, produces no entry.
- Exit fixtures: a held position at or below avg_price * 0.85 produces exactly one full sell exit (reason s_1wsw_stop15) and no entry in the same call; a held position reaching 126 sessions held with no stop or target hit produces one full time exit.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
