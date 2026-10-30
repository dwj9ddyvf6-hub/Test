# aster_breakout_ada_fullcash: Recreation package

Provenance: Source row in strategies/ausar/r19-crypto-breakout.md in this repo: Ausar R17/R18 crypto research, run as the R19 native-spot books; the sleeve module header in the desk states Aster batch 5, archive r19_crypto.py + absorption/signals.py + crypto_rules.json, engine aster_sleeves._common.

## What this sleeve is
This sleeve is a long-only ADAUSDT crypto spot sleeve on native UTC 4-hour bars, family breakout_base with fullcash sizing and a fixed 16-hour hold. It is a thin module in aster_sleeves/ whose evaluate(view, ctx) calls evaluate_crypto in the shared engine aster_sleeves/_common.py with its own SLEEVE_ID, FAMILY and CAPACITY. All rules below are that engine's rules as applied to this sleeve's family and capacity.

## Full algorithm
Constants in the engine (aster_sleeves/_common.py): SYMBOL = "ADAUSDT", FEE = 0.001 (10 bps each side), HOLD = 16 hours, STEP4 = 4 hours, ENTRY_WINDOW_S = 300.

Exits, evaluated first: for each held position for this sleeve and symbol, the exit deadline is the position exit_due_at when present, otherwise opened_at + 16 hours; a position with neither is never given an invented deadline. At or after the deadline, sell the full held quantity at market, time_in_force gtc, reason `aster_breakout_base_fixed16_deadline`. If any position is held, only exits (if due) are returned and no entry is evaluated. There is no stop, no profit target and no partial exit in this engine.

Entries, in code order:
1. Read 4Hour bars for ADAUSDT, sorted by timestamp; fewer than 22 bars means no entry.
2. The signal bar is bars[-2] and the entry bar is bars[-1]. The entry interval closes at entry bar timestamp + 4 hours. Entry fires only when now minus that close is between 0 and the entry window for this sleeve: 300 seconds only. This sleeve id is NOT listed in the engine WINDOW_SIDS set, so the entry-window enhancement does not apply to it.
3. Fail closed on a native-bar gap: the signal close (signal bar timestamp + 4 hours) must equal the entry close minus 4 hours.
4. Funding (where the family requires it): This family takes no funding input: the engine skips the funding lookup entirely for absorption_base and breakout_base.
5. Trigger: Breakout: boundary is the maximum high of the 20 bars before the signal bar (bars[len-22 : len-2] highs); the trigger is signal bar close > boundary. Revalidation (on by default for breakout_base): the entry bar close must also be above the same boundary, otherwise the entry is refused as a stale breakout and a paired shadow record is written.
6. Revalidation enhancements that are on by default where they apply to this family are stated in the trigger/funding text for this sleeve; no other revalidation applies.
7. Price is the entry bar close; price <= 0 means no entry. Sizing: fullcash: target quantity is the full slice cash divided by (entry price x 1.001), with no volume cap. Quantity is floored to a whole number (math.floor); qty <= 0 means no entry.
8. The entry intent is a market buy, time_in_force gtc, price_hint equal to the entry bar close, reason `aster_breakout_base_fullcash`. One position only in practice, because a held position suppresses entries.

Absorption trigger definition used above (engine _absorption_flags): Decimal arithmetic at precision 34; volume EMA uses the recurrence (2 x v + 19 x prior) / 21 and price EMA uses (2 x c + 49 x prior) / 51, each seeded on the first bar (current-inclusive, spans 20 and 50 in archive terms). A bar is a bearish shock when volume > 2 x volume EMA, close < open and close < price EMA. The next bar confirms when it closes above its open and above the shock bar's midpoint (high + low) / 2. The count is the number of bars advanced; confirmation counts only at count >= 300.

## Files in this repo
- Sleeve module (desk aster_sleeves/aster_breakout_ada_fullcash.py): `aster_sleeves/aster_breakout_ada_fullcash.py`; also present as `sleeves/aster/aster_breakout_ada_fullcash.py` and `integration/aster_breakout_ada_fullcash_adapter.py`.
- Shared engine: `engines/aster_sleeves/_common.py` (desk source aster_sleeves/_common.py, function evaluate_crypto).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/ausar/crypto-absorption.md` for the absorption families, or `strategies/ausar/r19-crypto-breakout.md` for breakout_base.

## Configuration
- Universe: ADAUSDT only (engine SYMBOL). Asset: crypto spot. Timeframe: native UTC 4-hour bars (snapshot key `ADAUSDT|4Hour`).
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; capacity fullcash as defined in the Full algorithm section. Slice cash at runtime is view slice cash_usd, falling back to capital_usd, then 10000.0 in the engine.
- Cadence: 3600 seconds. Session: 24h. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.

## Data inputs
- bars: view["bars"]["ADAUSDT|4Hour"], completed bars with t, o, h, l, c, v. The engine fails closed on absent or stale bars (see the entry-window rule) and on a bar gap.
- positions: view["positions"] rows for this sleeve/symbol with qty, avg_price, opened_at and optionally exit_due_at; broker readback is the producer in the desk snapshot.
- funding (only where listed in the roster inputs for this sleeve): view["funding"] for ADAUSDT; see the funding rule in the Full algorithm section. Where funding is an input and no eligible funding record exists, the sleeve returns no entry - funding is never assumed.

## Install and run
1. Place the engine at aster_sleeves/_common.py in the fresh desk (repo copy: engines/aster_sleeves/_common.py) and the sleeve module at aster_sleeves/aster_breakout_ada_fullcash.py with SLEEVE_ID = "aster_breakout_ada_fullcash", FAMILY = "breakout_base" and CAPACITY = "fullcash".
2. Register the roster row for `aster_breakout_ada_fullcash` exactly as in the Configuration section in config/sleeves.json (module aster_sleeves.aster_breakout_ada_fullcash, cadence 3600, session 24h, $10,000 slice, inputs as listed there).
3. Wire the producers so every snapshot carries completed 4Hour bars for ADAUSDT, this sleeve's positions, and funding where the roster row lists it, plus view now as a timezone-aware timestamp (the engine raises on a naive timestamp).
4. First evaluation: call evaluate(view, ctx) on the sleeve module; it calls evaluate_crypto(view, ctx, "aster_breakout_ada_fullcash", "breakout_base", "fullcash"). Confirm a snapshot with fewer than 22 bars, a bar gap, or (where applicable) no eligible funding returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check that fewer than 22 bars, a signal/entry bar gap, and an evaluation outside this sleeve's stated entry window each produce no entry on identical bars.
- Check the absorption or breakout trigger on fixtures exactly as defined above, including the 300-bar count requirement for absorption and the prior-20-bar high boundary for breakout.
- Check the funding gate (where applicable): no eligible funding record, a rate on the wrong side of zero, and a settlement more than 12 hours before the signal close each produce no entry.
- Check sizing: fullcash quantity equals floor(cash / (price x 1.001)); volume1pct quantity equals floor of the lesser of that quantity and 0.01 x entry bar volume; price_hint equals the entry bar close.
- Check the exit: a held position is sold in full at or after opened_at + 16 hours (or its exit_due_at), never before, and a held position suppresses any new entry.
