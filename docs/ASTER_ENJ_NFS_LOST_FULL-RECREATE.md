# aster_enj_nfs_lost_full: Recreation Package

## Provenance

Provenance: Ausar R17/R18 crypto research, run as the R19 native-spot books (Source row in `strategies/ausar/r19-crypto-breakout.md`).

## What this sleeve is

This sleeve trades ENJUSDT spot on 4-hour bars under the negative_funding_squeeze family, with exit_policy 'lost_breakout' and capacity 'fullcash'. It is a thin wrapper in `adapters3/aster_enj_nfs_lost_full.py` that delegates to the shared engine `desk3/aster_batch8.py`. It enters a 20-bar breakout only while funding is negative and exits under its named policy, with a 96-hour maximum deadline for every policy.

## Full algorithm

Evaluation order in `desk3/aster_batch8.py` _crypto(), as applied to CRYPTO_SPECS['aster_enj_nfs_lost_full'] = exit_policy 'lost_breakout', capacity 'fullcash'; symbol ENJUSDT:

1. Exits first. For each held ENJUSDT position: if hours held (from hours_held / age_hours, or bars_held x 4, or opened_at / entry_at) is at or above 96, emit a full market sell exit (day, sell_to_close) for the 96-hour deadline. This deadline fires for every exit policy, even when bars or funding are missing.
2. Structural exit for this policy:
- Lost breakout: exit in full when bars are present, the position carries a stored breakout_level, and the last 4-hour close is below that level.
   No price stop and no price target are part of this sleeve.
3. If any position is held (whether or not an exit fired), return and never evaluate an entry.
4. Entry funding gate: an actually available funding observation must exist and be below 0; missing funding or funding at or above 0 emits nothing. No funding producer is registered in v3 yet, so this sleeve is visibly unfed until that producer lands; missing funding is never assumed.
5. Entry breakout: require at least 21 completed 4-hour bars (keys `ENJUSDT|4Hour`, `ENJUSDT|4H` or `ENJUSDT`); the last bar close must be above the highest high of the prior 20 bars.
6. Entry freshness gate (enhancement, on by default for this exit policy): refuse the entry when the last bar lags `now`, measured from bar close (bar time plus 4 hours), by more than 3600 seconds.
7. Sizing fullcash: quantity = slice cash x 0.999 / price (the 0.999 factor is the 10 bp fee), rounded to 6 decimals. A quantity at or below 0 emits nothing.
8. Entry intent: market buy, day, buy_to_open, quantity as above, price_hint = last bar close, reason naming the breakout close, the funding rate and capacity 'fullcash'.

## Files in this repo

- Sleeve module / adapter (same wrapper content in the repo):
- `adapters3/aster_enj_nfs_lost_full.py`
- `sleeves/aster_enj_nfs_lost_full.py`
- `integration/aster_enj_nfs_lost_full_adapter.py`
- Shared engine: `desk3/aster_batch8.py` (desk path `desk3/aster_batch8.py`)
- Config: `config/sleeves.json` and `engines/config/sleeves.json` (row id `aster_enj_nfs_lost_full`)
- Existing family doc: see the Provenance source doc path named in the audit record for this sleeve.

## Configuration

- Universe and symbol: ENJUSDT spot only. Timeframe: 4-hour bars.
- Module: `adapters3.aster_enj_nfs_lost_full`; cadence_s 3600; session '24h'.
- Slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}.
- Inputs declared in config: bars, funding, positions. Parked: false.
- Engine spec: exit_policy lost_breakout, capacity fullcash.

## Data inputs

Declared inputs: bars, funding, positions (engine INPUTS_CRYPTO). Producers named in the engine: bars (freshness_sla_s 900), broker_readback (900, outputs positions), quotes (60, outputs quotes). The engine notes no funding producer is registered in v3 yet, so the crypto sleeves are visibly unfed in the registry until the funding producer lands.

## Install and run

1. Place the files listed in 'Files in this repo' at their repo paths in a fresh desk tree, keeping `desk3/`, `adapters3/`, `sleeves/` and `integration/` side by side so the wrapper imports resolve exactly as in the repo.
2. Register the config row for `aster_enj_nfs_lost_full` from `config/sleeves.json` (also vendored as `engines/config/sleeves.json`) with the exact values in the Configuration section; do not change cadence, slice or parked state.
3. Wire the producers named in 'Data inputs' so the declared inputs are present in the evaluation `view` at the stated freshness; a missing input must leave the sleeve unfed, never fake-fed.
4. Specific entry point: `from adapters3.aster_enj_nfs_lost_full import evaluate; intents = evaluate(view, ctx)`, where `view` carries 4-hour `bars` for ENJUSDT, a `funding` observation, `positions`, `now` and `slice`.
5. First evaluation: call the wrapper entry point `evaluate(view, ctx)` for this sleeve (see the specific call in the preceding step), confirm no intent is emitted outside the stated window / gates, then let the desk dispatcher call it on its cadence and route returned intents to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- With funding missing or at or above 0, or fewer than 21 bars, or a last close at or below the prior 20-bar high, no entry is emitted.
- With funding below 0 and a qualifying breakout, one entry is emitted with the fullcash quantity stated above.
- A held position exits in full when the last close falls below its stored breakout level, and in any case at 96 hours held.
- The wrapper delegates to the named shared engine with the exact sleeve id, and no rule, threshold or sizing value differs from the values stated above.
- A missing or stale declared input emits no entry intent.
