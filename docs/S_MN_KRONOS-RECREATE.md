# s_mn_kronos: Recreation package

Provenance: Source row in strategies/midna/mn-kronos-topk.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk; also Kronos-base (shiyu-coder/Kronos; NeoQuasar/Kronos-base weights), reconstructed in the desk's six-strategy study (family Midna, asset US equities, timeframe 1d (10-session cycle), universe 24 frozen names, style model forecast, TopkDropout). The card's Code section states the Midna v3 form in sleeves/s_mn_kronos.py consuming forecast fires from an upstream producer not in this repo.

## What this sleeve is
This sleeve holds the top 4 names of the upstream Kronos time-series forecast at $500 each, rebalancing when the forecast changes, with a 5-session minimum hold for names that drop out. The forecast model runs upstream and arrives as dated fires carrying a rank or score; this module is the desk-side fire-consumer. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_kronos.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_kronos.py): TOP_N = 4, PER_NAME = 500.0, MIN_HOLD = 5, MAX_FIRE_AGE_DAYS = 7. CONFIG: sleeve_id s_mn_kronos, cadence_s 300.

Forecast resolution (_forecast), in code order:
1. Fires come from context.extra fires; only dict fires with sleeve_id exactly "s_mn_kronos", a symbol, and a date are considered. Age = session date minus fire date must satisfy 0 <= age <= 7.
2. No qualifying fire at all means the forecast is None: the sleeve returns no intents at all (fail closed: no entries and no churn, existing positions are simply held).
3. Only fires on the latest qualifying date are kept. If every kept fire has a rank, they are sorted by rank ascending (int); otherwise they are sorted by score descending (missing score counts as 0.0). The top list is the first 4 symbols.

Evaluation:
4. Exits first: a held name not in the top list exits in full (sell_to_close, price_hint = last close if bars exist) only when sessions held (bars strictly after entry_date) >= 5; otherwise it is kept. Reason: forecast_changed min_hold_met.
5. Entries: slots = 4 - (held count - exits emitted). For each top-list symbol not held, in forecast order, while slots remain: skip if it has no bars; apply the cross-stale gate; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated. qty = floor(500.0 / last close); if qty > 0, emit a buy_to_open entry (reason kronos_forecast_top4) and consume one slot.

Position management: at most 4 names, $500 each; no price stop; the only exit is dropping out of a fresh top-4 after the 5-session minimum hold.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_kronos.py): `sleeves/s_mn_kronos.py`.
- Adapter (desk adapters/s_mn_kronos.py): `adapters/s_mn_kronos.py`; also present as `integration/s_mn_kronos_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-kronos-topk.md`.

## Configuration
- Universe: the symbols named by the latest fresh Kronos forecast fires (24 frozen names upstream, per the card). Asset: US equities. Timeframe: 1d.
- Sizing / slice: capital_usd 2000.0, cash_usd 2000.0 in the roster row; 4 names x $500 in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions, fires.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c}. Producer named bars in the adapter, freshness SLA 900 seconds.
- positions: view["positions"] broker rows, converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.
- fires: view["fires"] (or view extra fires), ingested forecast fires with sleeve_id, symbol, date, rank and/or score, from the lazarus_fire_ingest producer named in the adapter header; the upstream Kronos model and its signal files are not reachable from the desk. Producer named fires, freshness SLA 900 seconds in the adapter declaration.

## Install and run
1. Place the sleeve module at sleeves/s_mn_kronos.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_kronos.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_kronos` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_kronos).
3. Wire the producers so every snapshot carries: daily bars, this sleeve's positions, and the ingested Kronos forecast fires in view fires.
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check fail-closed behaviour: no fire within 7 days (or an unparseable session) produces zero intents, including no exits.
- Check forecast resolution: with two fire dates present only the latest is used; rank-bearing fires sort by rank ascending, score-only fires by score descending; only the first 4 are targets.
- Check the minimum hold: a dropped name held 4 sessions stays; at 5 sessions it exits in full.
- Check entries and sizing: a new top-4 name enters at floor(500 / close), entries stop when the book reaches 4 names counting kept positions, and a cross-stale name (last bar more than 4 days behind the universe) is refused.
