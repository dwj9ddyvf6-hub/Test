# s_mn_moonshot: Recreation package

Provenance: Source row in strategies/lazarus/lz-moonshot.md in this repo: MOONSHOT_FROZEN_SPEC v1.0 research, run by Lazarus; Midna's moonshot book (family Lazarus, asset US equities, timeframe 1w, universe tracker universe and Midna's swing basket, style value recovery). The card's Code section states the Midna v3 form in sleeves/s_mn_moonshot.py consuming upstream fires, no stop, 390 sessions.

## What this sleeve is
This sleeve holds a single upstream Midna moonshot pick for 78 weeks (390 sessions) with no stop, sized from a $1,000 budget, described in the module as the 1 percent weight pick on the test book. The pick is generated upstream and arrives as a dated fire; this module is the desk-side fire-consumer. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_moonshot.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_moonshot.py): BUDGET = 1000.0, HOLD_SESSIONS = 390 (78 weeks x 5), MAX_FIRE_AGE_DAYS = 7. CONFIG: sleeve_id s_mn_moonshot, cadence_s 300.

Evaluation, in code order:
1. Exits first: a held position whose sessions held (bars strictly after entry_date) >= 390 exits in full (sell_to_close, price_hint = last close if bars exist), reason hold_complete_78_weeks no_stop. There is no price stop at any point.
2. If any exit was emitted or anything is held, return (one slot).
3. Fresh fire: from context.extra fires, consider only dict fires with sleeve_id exactly "s_mn_moonshot", a symbol and a date, with age = session minus fire date satisfying 0 <= age <= 7; keep the one with the latest date. No fresh fire means no entry (fail closed).
4. The picked symbol needs bars; apply the cross-stale gate; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated. qty = floor(1000.0 / last close); if qty > 0 emit a buy_to_open entry, price_hint = last close, signal_date = the fire date, reason naming the fire date and weight=1pct.

Position management: one position at a time; the only exit is the 390-session hold completion.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_moonshot.py): `sleeves/s_mn_moonshot.py`.
- Adapter (desk adapters/s_mn_moonshot.py): `adapters/s_mn_moonshot.py`; also present as `integration/s_mn_moonshot_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/lazarus/lz-moonshot.md`.

## Configuration
- Universe: the single symbol named by the freshest qualifying upstream fire. Asset: US equities. Timeframe: 1d in the module CONFIG cadence (the pick itself is a weekly pick upstream, per the card's 1w timeframe).
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; $1,000 budget in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions, fires.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c}. Producer named bars in the adapter, freshness SLA 900 seconds.
- positions: view["positions"] broker rows, converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.
- fires: view["fires"] (or view extra fires), ingested upstream pick fires with sleeve_id, symbol and date, from the lazarus_fire_ingest producer named in the adapter header; the upstream signal files are not reachable from the desk. Producer named fires, freshness SLA 900 seconds in the adapter declaration.

## Install and run
1. Place the sleeve module at sleeves/s_mn_moonshot.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_moonshot.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_moonshot` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_moonshot).
3. Wire the producers so every snapshot carries: daily bars, this sleeve's positions, and the ingested moonshot pick fires in view fires.
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check fail-closed behaviour: no fire, a fire for another sleeve, or a fire 8 days old produces no entry; a fire dated today through 7 days ago can enter, and the latest of several fires wins.
- Check the hold: a position held 389 sessions stays through any price fall (no stop); at 390 sessions it exits in full.
- Check the single slot and sizing: a held position suppresses entries, and qty equals floor(1000 / last close).
- Check staleness: a pick whose bars lag the universe latest bar by more than 4 days is refused.
