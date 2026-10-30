# s_mn_macd: Recreation package

Provenance: Source row in strategies/midna/mn-macd-cci.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset US equities, timeframe 1d, universe Midna's swing basket, style momentum). The card's Notes state the Midna v3 s_mn_macd trades a plain MACD(12, 26, 9) cross with one slot, no CCI filter or chandelier.

## What this sleeve is
This sleeve trades a single position on a classic MACD(12,26,9) histogram cross on daily closes: it buys the strongest crossing-up name and sells a held name when its histogram crosses down. There is no CCI filter in the v3 module. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_macd.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_macd.py): SLOT_BUDGET = 1000.0, MIN_BARS = 35. CONFIG: sleeve_id s_mn_macd, cadence_s 300.

MACD computation: fast = EMA12 of closes and slow = EMA26 (each EMA seeded at the first close, k = 2/(n+1)); line = fast - slow; signal line = EMA9 of the line; histogram = line - signal line. A cross is evaluated on the last two bars.

Evaluation, in code order:
1. Exits first: for each held name with at least 35 bars, if histogram[-2] >= 0 and histogram[-1] < 0, emit a full-qty sell_to_close exit, price_hint = last close, reason naming the two histogram values.
2. If any exit was emitted or anything is held, return (one slot; no entry while a position is open).
3. Entries: visit symbols in sorted order; a symbol needs at least 35 bars and histogram[-2] <= 0 and histogram[-1] > 0. Apply the cross-stale gate; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated. Among qualifying symbols keep the one with the largest histogram[-1] (ties keep the first in symbol order, because only a strictly larger value replaces the best).
4. Sizing: qty = floor(1000.0 / last close of the chosen symbol); if qty > 0 emit one buy_to_open entry, price_hint = that close, reason naming the histogram value and slot_budget=1000.

Position management: one position at a time; the only exit is the MACD cross down; no stop or target.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_macd.py): `sleeves/s_mn_macd.py`.
- Adapter (desk adapters/s_mn_macd.py): `adapters/s_mn_macd.py`; also present as `integration/s_mn_macd_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-macd-cci.md`.

## Configuration
- Universe: every symbol carried in view bars (Midna's swing basket upstream). Asset: US equities. Timeframe: 1d (daily closes).
- Sizing / slice: capital_usd 1000.0, cash_usd 1000.0 in the roster row; one $1,000 slot in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c}, at least 35 bars per candidate. Producer named bars in the adapter, freshness SLA 900 seconds.
- positions: view["positions"] broker rows, converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.

## Install and run
1. Place the sleeve module at sleeves/s_mn_macd.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_macd.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_macd` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_macd).
3. Wire the producers so every snapshot carries: daily bars for the candidate universe and this sleeve's positions.
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the bar floor: a symbol with 34 bars never enters or exits on a cross; at 35 bars it can.
- Check the crosses: histogram moving from non-positive to positive is an entry cross, from non-negative to negative on a held name is an exit, and a histogram that stays positive produces neither.
- Check selection: with two names crossing up, the larger final histogram wins, an equal histogram keeps the alphabetically first symbol, and a held position suppresses all entries.
- Check sizing and staleness: qty equals floor(1000 / close), and a crossing name whose last bar lags the universe by more than 4 days is refused.
