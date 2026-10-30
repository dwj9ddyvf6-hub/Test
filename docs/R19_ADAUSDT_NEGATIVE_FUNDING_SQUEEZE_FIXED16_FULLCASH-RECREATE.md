# R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_FULLCASH: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Negative-funding breakout · ADAUSDT, 16-hour hold, available-cash sizing", type breakout, family negative_funding_squeeze. Algorithm grade PARTIAL, with the recorded gap: exit rule not recorded in any consulted source. Alias `ausar_pb55` (status in the accounting: md2_catalog "replaced", ausar_map "present in roster"; the R19 id itself is recorded "present in roster" and deployed "mode=independent_local_paper running=True").
- Accounting parameters for this variant: family negative_funding_squeeze, exit_policy fixed16, capacity fullcash, symbol ADAUSDT, fee_bps 10.
- Accounting entry text: a completed four-hour close must exceed the highest high of the prior 20 bars, with an actually available negative funding observation. Data per the accounting: native spot OHLCV, observed funding context and received bid/ask.
- No Test catalog entry in the accounting (test_entries empty). The exit rule the accounting lacked is held in the code in this repo (see Full algorithm); nothing beyond the record and that code is claimed.
- Code search: Test tree at batch start (fresh tree taken for this batch) holds the batch-5 sleeve and its shared engine (paths in Files). Silicon, quant-research-backup and Midna trees were searched for this sleeve id and family code; no matching file was found there.

## What this strategy is

A long-only ADAUSDT spot breakout: buy when a completed 4-hour bar breaks the prior 20-bar high while the observed perpetual funding rate is negative (a negative-funding squeeze), sized with all available cash net of the 10 bp fee, and exit at a fixed 16-hour deadline.

## Full algorithm

From `sleeves/aster/aster_squeeze_ada_fullcash.py` (SLEEVE_ID `aster_squeeze_ada_fullcash`, FAMILY `negative_funding_squeeze`, CAPACITY `fullcash`, INPUTS bars/positions/funding, CADENCE_S 3600) delegating to `evaluate_crypto` in `aster_sleeves/_common.py` (identical copy at `engines/aster_sleeves/_common.py`). Engine constants: SYMBOL ADAUSDT, FEE 0.001 (10 bps each side), HOLD 16 hours, STEP4 4 hours, ENTRY_WINDOW_S 300.

Evaluation order:

1. Exit first. Held positions are the view positions whose sleeve_id is absent or this sleeve, symbol ADAUSDT, quantity not zero. For each, the deadline is the position's saved `exit_due_at` if present, else `opened_at` + 16 hours; a position with neither is skipped (no deadline is invented). If now >= deadline, emit an exit intent: quantity = absolute held quantity, price_hint = average price or 1.0, market, good-till-cancelled, reason `aster_negative_funding_squeeze_fixed16_deadline`. If any position is held, return the exits (possibly empty) and evaluate no entry.
2. Bars: completed bars under the view key `ADAUSDT|4Hour`, sorted by time; fewer than 22 bars means no entry. The signal bar is the second-to-last bar and the entry bar is the last bar. The entry bar's close time is its timestamp + 4 hours; entry fires only when now is between 0 and 300 seconds after that close (this sleeve is not in the engine's cadence-window treatment set, so the archive 300-second window applies exactly). If the signal bar's close time is not exactly one 4-hour step before the entry bar's close, fail closed (native-bar gap).
3. Funding at the signal bar: the latest eligible funding receipt whose settlement is at or before the signal close, whose receipt is between settlement and now, and whose settlement is within 12 hours of the signal close; a simple `{rate: x}` observation with no clocks is accepted as already qualified. If no eligible rate exists, no entry (funding is never assumed).
4. Breakout: boundary = the maximum high of the 20 bars immediately before the signal bar. Trigger requires signal bar close strictly greater than the boundary AND the funding rate from step 3 strictly negative.
5. Funding revalidation (this sleeve only, enhancement ENH-B11 in the engine, default on): the funding rate known at the entry bar's close must also exist and be strictly negative; if funding normalized during the 4-hour delay, no entry.
6. Sizing: price = entry bar close (must be positive). Quantity target = cash / (price x 1.001), where cash is the slice `cash_usd`, else `capital_usd`, else 10000. Fullcash capacity: no volume cap. Quantity is floored to a whole ADA unit; a result of 0 or less emits nothing.
7. Entry intent: a dict intent with kind entry, symbol ADAUSDT, side buy, market, good-till-cancelled, price_hint = entry bar close, reason `aster_negative_funding_squeeze_fullcash`, intent_id built from the sleeve id, symbol and signal bar hour.

Position management beyond the deadline exit: not in the record and not in the code (no stop, no trailing rule).

## Files in this repo

- This doc: `docs/R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_FULLCASH-RECREATE.md`
- Sleeve code (already in Test): `sleeves/aster/aster_squeeze_ada_fullcash.py` and its identical copy `aster_sleeves/aster_squeeze_ada_fullcash.py`; adapter copy `integration/aster_squeeze_ada_fullcash_adapter.py`; `adapters3/aster_squeeze_1d.py` is a different sleeve and is not this strategy.
- Shared engine that runs the logic: `aster_sleeves/_common.py` and its identical copy `engines/aster_sleeves/_common.py` (function `evaluate_crypto`).
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `aster_squeeze_ada_fullcash`.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.

## Configuration

- Sleeve (engine) id: `aster_squeeze_ada_fullcash`; roster module `aster_sleeves.aster_squeeze_ada_fullcash`.
- Universe: ADAUSDT only. Asset: crypto spot. Timeframe: native UTC 4-hour completed bars.
- Session 24h; cadence 3600 seconds; slice capital and cash $10,000; `bp_buffer_frac` 0.02; `flat_by_close` false; parked false.
- Fee 10 bps each side (engine FEE 0.001). Hold 16 hours. Entry window 300 seconds after the entry bar closes.

## Data inputs

- Completed 4-hour spot bars for ADAUSDT (view key `ADAUSDT|4Hour`).
- Observed funding records for ADAUSDT with settlement and receipt times (or a simple rate observation).
- Positions (broker readback) and the slice cash; the current time in the view (`now`, timezone required).

## Install and run

1. Clone the Test repo.
2. Place `aster_sleeves/_common.py` and `aster_sleeves/aster_squeeze_ada_fullcash.py` (or the `sleeves/aster/` copy of the sleeve) in a fresh desk preserving those paths.
3. Register the roster row for `aster_squeeze_ada_fullcash` from `config/sleeves.json` (module `aster_sleeves.aster_squeeze_ada_fullcash`, cadence 3600, session 24h, $10,000 slice, inputs bars/positions/funding, parked false).
4. Wire the view: `bars` with at least 22 completed `ADAUSDT|4Hour` bars, `funding` records, `positions`, `slice`, and a timezone-aware `now`.
5. Call the sleeve's `evaluate(view, ctx)` every 3600 seconds; the first check is the 16-hour deadline exit, then the entry test in the order above.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- No entry when funding is absent, when the eligible funding rate is 0 or positive at the signal bar, or when it is 0 or positive at the entry bar close.
- No entry with fewer than 22 bars, with a gap between the signal and entry bars, or more than 300 seconds after the entry bar closes.
- No entry when the signal close equals (does not exceed) the highest high of the 20 bars before it.
- Entry quantity equals floor of cash / (entry close x 1.001); a held position blocks entry and is exited at its saved deadline or opened_at + 16 hours, never on an invented deadline.
