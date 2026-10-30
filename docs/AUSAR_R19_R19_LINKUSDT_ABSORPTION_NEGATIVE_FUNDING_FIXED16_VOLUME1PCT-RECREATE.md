# ausar_r19_R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT — Recreation Package

## Provenance

- Type: mean reversion; family: absorption_negative_funding; algorithm grade in the accounting: PARTIAL.
- Accounting sources: md2 catalog entry/exit/strategy text.
- entry: [ausar_r19_R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT] Requires confirmed absorption with at least 300 indicator bars and an observed funding rate below zero.
- filters: [ausar_r19_R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT] data: posted r19 data adapters
- accounting gap: exit rule not recorded in any consulted source
- accounting gap: sizing not recorded in any consulted source
- variant: fixed16 · volume1pct · vol · negative_funding · neg · absorption :: recorded distinguishing tokens/parameters for this form: fixed16 · volume1pct · vol · negative_funding · neg · absorption (base strategy otherwise as in the algorithm above; token-derived from the sleeve ids and, where present, ausar_map variant text) (aliases: ausar_r19_R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT)
- alias ausar_r19_R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT: md2_catalog: installed

- Accounting entry: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json`, strategy entry "Absorption with negative funding · LINKUSDT, 16-hour hold, 1% volume cap" (also `docs/ALL-SLEEVES.md`).
- Strategy card in this repo: `strategies/ausar/crypto-absorption.md` ("Crypto confirmed absorption (4h)"), which records the universe ADAUSDT, ENJUSDT, LINKUSDT, timeframe 4h, asset crypto spot, style mean reversion.
- Code status: the full logic is present in this repo (engine named in Files). Grade: built.

## What this strategy is

A confirmed-absorption mean-reversion book on LINKUSDT 4h bars: it buys the bar that closes back above the midpoint of a high-volume down (shock) bar, with family absorption_negative_funding (confirmed absorption plus an observed funding rate below zero), and sells 16 hours later. Capacity arm: volume1pct (1% volume cap).

## Full algorithm

Evaluation order in the v3 engine in this repo (per-symbol, completed 4h bars):

1. Exit first: for each open position on the symbol, if held time >= 16 h (fixed16), emit a sell exit intent for the full quantity at the latest close. The deadline is checked before bar validation and survives missing bars or funding.
2. If any position on the symbol is open and no exit fired, stop: no new entry (no pyramiding).
3. Absorption signal (needs at least 300 completed bars): the second-to-last completed 4h bar is the shock bar: volume > 2 x EMA20(volume) (EMA inclusive of the bar, seeded at the first bar), close < open, and close < EMA50(close) (inclusive, seeded at the first bar). The last completed bar confirms: close > open and close > (shock bar high + shock bar low) / 2.
4. Funding gate (this variant): the latest actually-observed funding rate must be < 0; if funding is missing or >= 0, no entry. Missing funding is never assumed to be zero.
5. Freshness gate (engine enhancement, on by default): an entry is refused when the signal bar closed more than one bar interval (4 h) before now (batch-11 stale-signal gate, on by default)..
6. Sizing: price = last completed bar close. fullcash quantity = slice cash x (1 - 0.001 fee) / price; volume1pct: quantity = min(fullcash quantity, 1% of the preceding 4h bar's volume).. Quantity rounded to 8 decimals in the engine; if qty <= 0, no entry.
7. Entry intent: buy, buy_to_open, at the signal close as price hint.

Original archive books (recorded in strategies/ausar/crypto-absorption.md, for contrast): R19 books enter 4 h after the confirmation bar closes, in a 5-minute window, and sell 16 h after the entry time; the original (non-R19) ENJ/LINK books buy at the ask within 300 s of the confirmation close and sell at the bid from 16 h after the confirmation close. No stop, no pyramiding in either form. Fee 10 bps (fee_bps 10 in the accounting parameters).

Accounting gaps carried, not filled: exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Where the accounting graded the algorithm PARTIAL, the engine and card text above are the record in this repo; anything not stated there is not in the record.

## Files in this repo

- This package: `docs/AUSAR_R19_R19_LINKUSDT_ABSORPTION_NEGATIVE_FUNDING_FIXED16_VOLUME1PCT-RECREATE.md`
- Strategy card: `strategies/ausar/crypto-absorption.md`
- Sleeve wrapper: `sleeves/aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct.py` (delegates to the engine)
- Adapters: `adapters3/aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct.py`, `integration/aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct_adapter.py`
- Engine (the logic): `desk3/aster_b11_crypto.py` (SPECS entry `aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct`: sym LINKUSDT, fam absorption_negative_funding, cap volume1pct, hold_h 16)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Symbol LINKUSDT; timeframe 4h; exit policy fixed16 (16-hour hold); capacity volume1pct (1% volume cap); fee_bps 10.
- v3 config row (engine `config_rows()`): module `adapters3.aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct`, cadence_s 300, session always, slice capital_usd 10000.0 / cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close False, parked False, params {family, exit_policy fixed16, capacity, symbol, fee_bps 10}.
- Inputs: bars, positions, funding (funding-filtered sleeves are UNFED without a funding input, never fake-fed).

## Data inputs

- Completed Binance spot 4h OHLCV bars for LINKUSDT (at least 300 for indicator warmup), actual execution quote, and (funding variants) the latest actually-observed funding rate. Accounting filter text: see Provenance.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Locate the sleeve wrapper `aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct` under `sleeves/`, `adapters3/` and `integration/` and its engine (Files section).
3. Register the config row from the engine's `config_rows()` for this sleeve id in the desk3 sleeve registry, with the inputs listed under Configuration.
4. Provide the data inputs above through the desk3 snapshot producers (bars keyed `LINKUSDT|4Hour` or `LINKUSDT|4h`).
5. Run the desk3 cycle; the sleeve evaluates on each pass (cadence_s 300) and emits enter/exit intents.

## Verification

Behavior checklist (from the algorithm above; no dedicated test file for this sleeve id was found in the Test tree searched at batch start):
- A shock bar (volume > 2 x EMA20 volume, close < open, close < EMA50 close) followed by a confirmation bar (close > open, close > shock midpoint) with >= 300 bars of history produces exactly one buy intent; the same bars with < 300 bars of history produce none.
- Funding variant only: the same signal with funding >= 0 (or funding absent) produces no entry; with funding < 0 it enters.
- Sizing: fullcash quantity equals the engine formula on slice cash; volume1pct quantity never exceeds 1% of the shock bar's volume.
- A position held >= 16 h produces a sell exit intent even when bars or funding are missing; a position held < 16 h produces no exit and blocks new entries.
