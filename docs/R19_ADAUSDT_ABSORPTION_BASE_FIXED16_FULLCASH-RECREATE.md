# R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH — Recreation Package

## Provenance

- Type: mean reversion; family: absorption_base; algorithm grade in the accounting: PARTIAL.
- Accounting sources: ausar_map params/variant; md2 catalog entry/exit/strategy text.
- entry: [R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH] ausar variant: Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing
- entry: [ausar_pb47] Requires a confirmed absorption observation with at least 300 indicator bars. This control does not require funding.
- filters: [ausar_pb47] data: Completed spot OHLCV and actual execution quote.
- parameters: {"R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH": {"family": "absorption_base", "exit_policy": "fixed16", "capacity": "fullcash", "symbol": "ADAUSDT", "fee_bps": 10}}
- accounting gap: exit rule not recorded in any consulted source
- variant: Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing :: recorded distinguishing tokens/parameters for this form: Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing (base strategy otherwise as in the algorithm above; token-derived from the sleeve ids and, where present, ausar_map variant text) (aliases: R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH)
- variant: variant not recorded in any source :: sources do not record which variant this alias runs; not guessed (aliases: ausar_pb47)
- alias R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH: md2_ausar_map: present in roster; ausar_deployed: mode=independent_local_paper running=True
- alias ausar_pb47: md2_catalog: replaced; md2_ausar_map: present in roster
- merge evidence (tier A): ausar_map row ausar_pb47 (alias 'Paper book 47', variant 'Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing') lists r19 link R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH

- Accounting entry: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json`, strategy entry "Confirmed absorption control · ADAUSDT, 16-hour hold, available-cash sizing" (also `docs/ALL-SLEEVES.md`).
- Strategy card in this repo: `strategies/ausar/crypto-absorption.md` ("Crypto confirmed absorption (4h)"), which records the universe ADAUSDT, ENJUSDT, LINKUSDT, timeframe 4h, asset crypto spot, style mean reversion.
- Code status: INCOMPLETE-CODE. The wrapper is in this repo but the engine it calls (`aster_sleeves._common`) is in no GitHub repo searched (Test, Silicon, quant-research-backup, Midna). This package records the algorithm from the accounting, the strategy card, and the same-family engines in this repo, and does not present reconstructed code as the original.

## What this strategy is

A confirmed-absorption mean-reversion book on ADAUSDT 4h bars: it buys the bar that closes back above the midpoint of a high-volume down (shock) bar, with family absorption_base (confirmed absorption control; this control does not require funding), and sells 16 hours later. Capacity arm: fullcash (available-cash sizing).

## Full algorithm

Evaluation order in the v3 engine in this repo (per-symbol, completed 4h bars):

1. Exit first: for each open position on the symbol, if held time >= 16 h (fixed16), emit a sell exit intent for the full quantity at the latest close. The deadline is checked before bar validation and survives missing bars or funding.
2. If any position on the symbol is open and no exit fired, stop: no new entry (no pyramiding).
3. Absorption signal (needs at least 300 completed bars): the second-to-last completed 4h bar is the shock bar: volume > 2 x EMA20(volume) (EMA inclusive of the bar, seeded at the first bar), close < open, and close < EMA50(close) (inclusive, seeded at the first bar). The last completed bar confirms: close > open and close > (shock bar high + shock bar low) / 2.
4. Funding gate (this variant): no funding gate: absorption_base is the funding-off control, and a funding outage cannot veto it. Missing funding is never assumed to be zero.
5. Freshness gate (engine enhancement, on by default): not in the record for the missing ADA engine (the ENJ and LINK engines in this repo each carry a freshness gate; whether the ADA engine carried the same gate is not in the record).
6. Sizing: price = last completed bar close. fullcash quantity = slice cash / (price x (1 + 0.001 fee)) per the in-repo ENJ engine's recorded formula for this family — stated from the family record, not from this sleeve's missing engine. Quantity rounded to 8 decimals in the engine; if qty <= 0, no entry.
7. Entry intent: buy, buy_to_open, at the signal close as price hint.

Original archive books (recorded in strategies/ausar/crypto-absorption.md, for contrast): R19 books enter 4 h after the confirmation bar closes, in a 5-minute window, and sell 16 h after the entry time; the original (non-R19) ENJ/LINK books buy at the ask within 300 s of the confirmation close and sell at the bid from 16 h after the confirmation close. No stop, no pyramiding in either form. Fee 10 bps (fee_bps 10 in the accounting parameters).

Accounting gaps carried, not filled: exit rule not recorded in any consulted source. Where the accounting graded the algorithm PARTIAL, the engine and card text above are the record in this repo; anything not stated there is not in the record.

## Files in this repo

- This package: `docs/R19_ADAUSDT_ABSORPTION_BASE_FIXED16_FULLCASH-RECREATE.md`
- Strategy card: `strategies/ausar/crypto-absorption.md`
- Sleeve wrappers present in this repo: `sleeves/aster/aster_abs_base_ada_fullcash.py` and `aster_sleeves/aster_abs_base_ada_fullcash.py` (SLEEVE_ID aster_abs_base_ada_fullcash, FAMILY absorption_base, CAPACITY fullcash, INPUTS ('bars', 'positions'), CADENCE_S 3600; both delegate to `aster_sleeves._common.evaluate_crypto`)
- ENGINE MISSING: `aster_sleeves/_common.py` is not in this repo (the strategy card states this plainly) and was not found in dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup or dwj9ddyvf6-hub/Midna (repo trees searched at batch start). The same-family engines that ARE in this repo, `desk3/aster_batch7.py` (ENJUSDT) and `desk3/aster_b11_crypto.py` (LINKUSDT), implement the identical recorded rules for their symbols and are the closest in-repo evidence of the algorithm; they are not this sleeve's code and are not presented as it.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Symbol ADAUSDT; timeframe 4h; exit policy fixed16 (16-hour hold); capacity fullcash (available-cash sizing); fee_bps 10.
- v3 config row (engine `config_rows()`): module `adapters3.aster_abs_base_ada_fullcash`, cadence_s 300, session always, slice capital_usd 10000.0 / cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close False, parked False, params {family, exit_policy fixed16, capacity, symbol, fee_bps 10}.
- Inputs: bars, positions (funding-filtered sleeves are UNFED without a funding input, never fake-fed).

## Data inputs

- Completed Binance spot 4h OHLCV bars for ADAUSDT (at least 300 for indicator warmup), actual execution quote, and (funding variants) the latest actually-observed funding rate. Accounting filter text: see Provenance.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Locate the sleeve wrapper `aster_abs_base_ada_fullcash` under `sleeves/`, `adapters3/` and `integration/` and its engine (Files section).
3. Register the config row from the engine's `config_rows()` for this sleeve id in the desk3 sleeve registry, with the inputs listed under Configuration.
4. Provide the data inputs above through the desk3 snapshot producers (bars keyed `ADAUSDT|4Hour` or `ADAUSDT|4h`).
5. Run the desk3 cycle; the sleeve evaluates on each pass (cadence_s 300) and emits enter/exit intents.

## Verification

Behavior checklist (from the algorithm above; no dedicated test file for this sleeve id was found in the Test tree searched at batch start):
- A shock bar (volume > 2 x EMA20 volume, close < open, close < EMA50 close) followed by a confirmation bar (close > open, close > shock midpoint) with >= 300 bars of history produces exactly one buy intent; the same bars with < 300 bars of history produce none.
- Funding variant only: the same signal with funding >= 0 (or funding absent) produces no entry; with funding < 0 it enters.
- Sizing: fullcash quantity equals the engine formula on slice cash; volume1pct quantity never exceeds 1% of the shock bar's volume.
- A position held >= 16 h produces a sell exit intent even when bars or funding are missing; a position held < 16 h produces no exit and blocks new entries.
