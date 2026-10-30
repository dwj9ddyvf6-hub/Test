# R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FULLCASH: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): type breakout, family negative_funding_squeeze. Algorithm grade PARTIAL in the accounting, with the recorded gap: exit rule not recorded in any consulted source. Alias `ausar_pb63` (status in the accounting: md2_catalog "replaced", ausar_map "present in roster"; the R19 id itself is recorded "present in roster" and deployed "mode=independent_local_paper running=True").
- Accounting parameters for this variant: family negative_funding_squeeze, exit_policy normalization, capacity fullcash, symbol ADAUSDT, fee_bps 10.
- Accounting entry text: a completed four-hour close must exceed the highest high of the prior 20 bars, with an actually available negative funding observation. Data per the accounting: native spot OHLCV, observed funding context and received bid/ask.
- No Test catalog entry in the accounting (test_entries empty). Where the accounting is PARTIAL, everything it holds is written above and the remaining rules below come from the code in this repo (named in Files); gaps the record and code both lack are marked not in the record.
- Code search: the fresh Test tree taken at batch start holds the sleeve wrapper and the shared engine (paths in Files). Silicon, quant-research-backup and Midna trees were searched for this sleeve id and family code; no matching file was found there.

## What this strategy is

A long-only ADAUSDT spot breakout: buy when the last completed 4-hour close breaks the prior 20-bar high while the observed funding rate is negative (a negative-funding squeeze). This variant's exit policy is `normalization` and its sizing capacity is `fullcash` (see Full algorithm).

## Full algorithm

From the sleeve wrapper `sleeves/aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash.py` (SLEEVE_ID `aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash`) delegating to `desk3/aster_crypto.py` `evaluate`, whose SPECS row for this sleeve is exactly: sym ADAUSDT, fam nfs, exit normalization, cap fullcash, hold_h 96. Engine fee constant FEE = 0.001 (10 bps). INPUTS = bars, funding, positions.

Evaluation order in `evaluate`:

1. Load inputs: bars via the view `bars` keys `ADAUSDT|4Hour`, then `ADAUSDT|4h`, then `ADAUSDT|240min`, then `ADAUSDT`, sorted by time; funding via `view.funding[ADAUSDT]` (unwrapping a dict `rate`), else `view.extra.funding_rate`, else None; now from the view or ctx `now` (the code default if absent is 2026-10-24T00:00:00+00:00).
2. Exit handling first. Positions are the view positions with quantity not zero. For each, held hours are (now - opened_at or entry_time) / 3600 when an open time parses, else `age_hours` or 0. Exit rule for this variant: Structural exit: if the observed funding rate is present and >= 0, exit with a funding-normalized reason. Independently, if held hours >= 96, exit at the 96-hour deadline (the structural policies carry the installed 96h maximum deadline in the engine SPECS). An exit intent is `Intent(kind="exit", symbol="ADAUSDT", qty=absolute quantity, price_hint=last bar close if bars exist, side="sell", position_intent="sell_to_close")` with the reason prefixed by the sleeve id. If any exit is produced, or any position remains, return the exits (possibly empty) and evaluate no entry.
3. Entry (no position open), family nfs gates in code order: funding must be observed and negative (funding None or >= 0 means no entry; absent funding is never assumed); at least 21 bars are required; the last bar close must be strictly greater than the maximum high of the prior 20 bars (`bars[-21:-1]`).
4. Sizing: price = last bar close; cash = `view.slice.cash_usd` if present, else 10000. Full-cash quantity = cash x (1 - 0.001) / price. Cap for this variant: fullcash: the quantity is the full-cash quantity above, with no volume cap. Quantity is then floored to a whole unit with `int(qty)`; a result of 0 or less emits nothing.
5. Entry intent: `Intent(kind="enter", symbol="ADAUSDT", qty=quantity, price_hint=price, side="buy", position_intent="buy_to_open")`, reason naming the sleeve id, the nfs family, the close, the funding value and the cap `fullcash`.

Position management beyond the exits above: not in the record and not in the code (no stop, no trailing rule).

## Files in this repo

- This doc: `docs/R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_NORMALIZATION_FULLCASH-RECREATE.md`
- Sleeve code (already in Test): `sleeves/aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash.py`, with identical-purpose copies at `adapters3/aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash.py` and `integration/aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash_adapter.py`.
- Shared engine that runs the logic: `desk3/aster_crypto.py` (SPECS row and `evaluate` for this sleeve).
- Dependency note: `desk3/aster_crypto.py` imports `Intent` from `desk3.contract`; that module was absent from the fresh Test tree taken at batch start. A recreation must supply an `Intent` carrying the fields used above (kind, symbol, qty, price_hint, reason, side, position_intent); its other behaviour is not in the record.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash`.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.

## Configuration

- Sleeve (engine) id: `aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash`; roster module `adapters3.aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash`.
- Universe: ADAUSDT only. Asset: crypto spot. Timeframe: completed UTC 4-hour bars.
- Session 24h; cadence 14400 seconds; slice capital and cash $10,000; `bp_buffer_frac` 0.02; `flat_by_close` false; `flatten_time_et` null; parked false.
- Fee 10 bps (engine FEE 0.001). Maximum hold 96 hours.

## Data inputs

- Completed 4-hour spot bars for ADAUSDT (any of the view keys listed in step 1).
- Observed funding rate for ADAUSDT and positions (broker readback); the slice cash and the current time. The engine header states funding is a declared producer input: absent funding means no entry and the sleeve is unfed in the registry, never fake-fed.

## Install and run

1. Clone the Test repo.
2. Place `desk3/aster_crypto.py` under `desk3/` and supply `desk3/contract.py` with the `Intent` fields named in Files (absent from the Test tree; do not invent its other behaviour).
3. Place the sleeve wrapper as `sleeves/aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash.py` (or the `adapters3/` copy).
4. Register the roster row for `aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash` from `config/sleeves.json` (module `adapters3.aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash`, cadence 14400, session 24h, $10,000 slice, inputs bars/funding/positions, parked false).
5. Wire the view: `bars` under one of the ADAUSDT keys (at least 21 bars for an entry), `funding`, `positions`, a `slice`, and a current time.
6. Call the wrapper's `evaluate(view, ctx)` every 14400 seconds, 24 hours; it delegates to `desk3.aster_crypto.evaluate("aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash", view, ctx)`. First check is the exit scan, then the entry test.
7. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- Entry is blocked when funding is absent or >= 0, when fewer than 21 bars are present, and when the last close is at or below the maximum high of the prior 20 bars.
- Entry quantity equals the whole-unit floor of cash x 0.999 / price, with this variant's cap applied exactly as stated (fullcash); a result of 0 produces no intent.
- A held position blocks a new entry, and this variant's exit rule (normalization) fires exactly as stated in step 2, including the 96-hour deadline; there is no price stop beyond those rules.
