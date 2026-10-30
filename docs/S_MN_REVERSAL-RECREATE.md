# s_mn_reversal: Recreation package

Provenance: Source row in strategies/midna/mn-prior-month-reversal.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset US equities, timeframe 1d (monthly), universe 40 large caps, style mean reversion). The card's Notes state the Midna v3 s_mn_reversal ranks by the prior 21 sessions, holds 3 names and rotates after 21 sessions.

## What this sleeve is
This sleeve buys the 3 worst prior-21-session performers in the snapshot's large-cap universe at $1,000 each and holds each for 21 sessions, rotating at that point and refilling from a fresh ranking. Mid-hold it does not churn. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_reversal.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_reversal.py): SLOTS = 3, PER_SLOT = 1000.0, LOOKBACK = 21, HOLD = 21. CONFIG: sleeve_id s_mn_reversal, cadence_s 300.

Ranking: return21 for a symbol = last close / close 21 bars earlier - 1, requiring at least 22 bars; worst_names sorts all scored symbols by (return, symbol) ascending and takes the first 3, excluding any symbols named in the exclude set.

Evaluation, in code order:
1. Exits first: a held name whose sessions held (bars strictly after entry_date) >= 21 exits in full (sell_to_close, price_hint = last close if bars exist), reason monthly_rotation_21_sessions, and marks this pass as rotating.
2. If anything is held and no position is rotating, return the (empty) exits: mid-hold, no entries and no re-ranking.
3. Refill: open_slots = 3 - (held count - exits emitted); if open_slots is at or below 0, return. Visit worst_names(bars, exclude = currently held symbols) in ranked order while slots remain: apply the cross-stale gate; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated. qty = floor(1000.0 / last close); if qty > 0 emit a buy_to_open entry, price_hint = last close, reason naming ret21, and consume one slot.

Position management: at most 3 names, $1,000 each; the only exit is the 21-session rotation; no stop or target.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_reversal.py): `sleeves/s_mn_reversal.py`.
- Adapter (desk adapters/s_mn_reversal.py): `adapters/s_mn_reversal.py`; also present as `integration/s_mn_reversal_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-prior-month-reversal.md`.

## Configuration
- Universe: every symbol carried in view bars (producer-defined large-cap set; the catalog names no tickers). Asset: US equities. Timeframe: 1d.
- Sizing / slice: capital_usd 3000.0, cash_usd 3000.0 in the roster row; 3 slots x $1,000 in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c}, at least 22 bars per scored candidate. Producer named bars, freshness SLA 900 seconds.
- positions: view["positions"] broker rows, converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.

## Install and run
1. Place the sleeve module at sleeves/s_mn_reversal.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_reversal.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_reversal` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_reversal).
3. Wire the producers so every snapshot carries: daily bars for the large-cap universe and this sleeve's positions.
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the ranking: entries are the lowest prior-21-session returns (ties by symbol order), a symbol with 21 bars is not scored, and held symbols are excluded from the refill ranking.
- Check the rotation: a name held 20 sessions blocks all refills; at 21 sessions it exits and the same pass refills the freed slots from the new ranking.
- Check sizing and limits: qty equals floor(1000 / close) and the book never exceeds 3 names.
- Check staleness: a worst-ranked name whose last bar lags the universe by more than 4 days is skipped for the next ranked name.
