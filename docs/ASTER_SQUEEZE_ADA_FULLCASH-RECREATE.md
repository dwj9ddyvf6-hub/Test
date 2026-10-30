# aster_squeeze_ada_fullcash - RECREATE

Provenance: Ausar R17/R18 crypto research, run as the R19 native-spot books (Source row of the existing Test doc `strategies/ausar/r19-crypto-breakout.md`); desk module header in `aster_sleeves/aster_squeeze_ada_fullcash.py` describes batch 5 as the negative-funding squeeze on ADAUSDT with a 16-hour hold and fullcash sizing, sourced from the staged archive r19_crypto.py, absorption signals and crypto_rules.json, with the engine in `aster_sleeves._common`.

## What this sleeve is

This sleeve buys ADAUSDT crypto spot when a completed 4-hour bar breaks above the prior 20-bar high while the latest known perpetual funding rate is negative. It holds for a fixed 16 hours and sizes with the full slice cash, net of the 10 bps fee. It is a thin wrapper over the shared crypto engine in `aster_sleeves/_common.py`.

## Full algorithm

Delegation and spec: the module `aster_sleeves/aster_squeeze_ada_fullcash.py` sets `SLEEVE_ID="aster_squeeze_ada_fullcash"`, `FAMILY="negative_funding_squeeze"`, `CAPACITY="fullcash"`, `INPUTS=('bars', 'positions', 'funding')`, `CADENCE_S=3600`, and delegates to `aster_sleeves._common.evaluate_crypto(view, ctx, SLEEVE_ID, FAMILY, CAPACITY)`. Engine constants in `_common.py`: `SYMBOL="ADAUSDT"`, `FEE=Decimal("0.001")` (10 bps each side), `HOLD=timedelta(hours=16)`, `STEP4=timedelta(hours=4)`, `ENTRY_WINDOW_S=300`. This sleeve is not in the engine `WINDOW_SIDS` set, so its entry window stays 300 seconds (the cadence-length window extension in the engine applies only to the five absorption sleeves named there).

Evaluation order in `evaluate_crypto`:

1. Current time is `view["now"]` parsed as a timezone-aware UTC timestamp. Held positions are view `positions` rows for this sleeve id (or no sleeve id) with symbol ADAUSDT and non-zero quantity.
2. Exit handling first, for each held position: the deadline is the position `exit_due_at` when present, else `opened_at` plus 16 hours; a position with neither is never given an invented deadline and is skipped. If now is at or after the deadline, emit an exit for the full absolute quantity at price hint the position average price (or 1.0 when absent), reason `aster_negative_funding_squeeze_fixed16_deadline`. If any position is held at all, return the exits (possibly empty) and do not evaluate an entry. There is no stop, no funding-normalisation exit and no other exit for this sleeve.
3. Entry bars: completed 4-hour bars from view `bars` key `ADAUSDT|4Hour`, sorted by bar time. Fewer than 22 bars returns nothing. The entry bar is the last bar and the signal bar is the second-last bar. The entry interval close time is the entry bar time plus 4 hours; the lag of now after that close must be between 0 and 300 seconds inclusive, otherwise nothing. The signal bar close time (its time plus 4 hours) must equal the entry close time minus 4 hours; a native-bar gap fails closed.
4. Funding: the known funding rate at the signal close is required. `known_funding_rate` takes the latest eligible funding record for ADAUSDT: a record flagged `observed_public_endpoint` False is excluded; a record with settlement and receipt clocks is eligible only when settlement is at or before the signal close and receipt is between settlement and now; the chosen settlement must be within 12 hours of the signal close. A simple record with only a `rate` is accepted as an already-qualified receipt. If no rate is known, no entry: funding is never assumed.
5. Signal: the breakout boundary is the maximum high of the 20 bars ending just before the signal bar (with `i = len(bars) - 2`, the maximum high of `bars[i-20:i]`). Triggered requires the signal bar close strictly greater than that boundary AND the known funding rate < 0.
6. Funding revalidation enhancement for this sleeve only (engine batch 11, switch default ON via `_enh_on` key `funding_revalidation`, read from `ctx["<sid>_enhance"]` or `view.extra["<sid>_enhance"]`; OFF restores the signal-time-only rule): the known funding rate is re-read at the entry interval close; if it is missing or >= 0, the entry is refused because the squeeze premise is gone, and a paired shadow record (control enter, treatment refuse) is written.
7. Sizing: price is the entry bar close; a non-positive price returns nothing. Target quantity in Decimal (precision 34) is slice cash divided by (price times (1 + FEE)), where slice cash is `view.slice.cash_usd`, falling back to `capital_usd`, then 10000.0. Capacity `fullcash` applies no volume cap. Quantity is floored to whole ADA units; a floored quantity of 0 or less returns nothing.
8. Entry intent (engine `_intent` dict): intent id `aster_squeeze_ada_fullcash-ADAUSDT-<signal bar time, hour precision>-entry`, kind entry, symbol ADAUSDT, side buy, quantity the floored quantity, order type market, time in force gtc, price hint the entry bar close, reason `aster_negative_funding_squeeze_fullcash`. Exit intents use the same shape with kind exit and side sell.

## Files in this repo

- Sleeve module (repo copies): `aster_sleeves/aster_squeeze_ada_fullcash.py`, `sleeves/aster/aster_squeeze_ada_fullcash.py`, and `integration/aster_squeeze_ada_fullcash_adapter.py`. Desk original: `aster_sleeves/aster_squeeze_ada_fullcash.py`, delegating to `aster_sleeves._common.evaluate_crypto`.
- Shared engine that runs the logic: `engines/aster_sleeves/_common.py` (desk `aster_sleeves/_common.py`; contains `evaluate_crypto`, `known_funding_rate` and the constants above; engines map status vendored).
- Existing family card: `strategies/ausar/r19-crypto-breakout.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_squeeze_ada_fullcash`).

## Configuration

- Sleeve id: `aster_squeeze_ada_fullcash`; module: `aster_sleeves.aster_squeeze_ada_fullcash` (roster row in desk `config/sleeves.json`).
- Universe: ADAUSDT only (engine `SYMBOL`). Asset: crypto spot. Timeframe: 4h (completed 4-hour bars). Session: `24h`. Cadence: 3600 seconds (`cadence_s=3600`).
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; capacity `fullcash` and fee 0.001 as in the sizing step above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false (`parked=false`). Note: the roster row declares the `funding` input; the audit records that no v3 funding producer serves it yet, so the sleeve lands UNFED live until that producer exists. That is a data state, not a different algorithm.

## Data inputs

Inputs declared in the roster row and the module (`INPUTS = ('bars', 'positions', 'funding')`): `bars`, `positions`, `funding`.

The engine declares no producer tuple with freshness SLAs in `aster_sleeves/_common.py` or the module, so no SLA is stated here. The existing card lists the underlying data as Binance spot 4h klines and Binance USD-M funding history; the v3 function itself reads only the 4-hour bars, funding records and positions supplied in the view, plus the slice cash and `view["now"]`. At least 22 completed 4-hour bars are needed for any entry.

## Install and run

1. Place the shared engine as `aster_sleeves/_common.py` in a fresh desk (copy the repo file `engines/aster_sleeves/_common.py` to that desk path).
2. Place the module as `aster_sleeves/aster_squeeze_ada_fullcash.py` (copy any repo copy listed above).
3. Register the roster row for `aster_squeeze_ada_fullcash` from `config/sleeves.json` (module `aster_sleeves.aster_squeeze_ada_fullcash`, cadence 3600, session 24h, $10,000 slice, inputs bars/positions/funding, parked false).
4. Wire inputs so the view contains `bars` under `ADAUSDT|4Hour` (at least 22 completed bars), `funding` records for ADAUSDT with rates and, when carried, settlement and receipt clocks, `positions` from broker readback, a `slice`, and a timezone-aware `now`.
5. First evaluation: call `aster_sleeves.aster_squeeze_ada_fullcash.evaluate(view, ctx)`; it delegates to `evaluate_crypto` with family `negative_funding_squeeze` and capacity `fullcash`. Run every 3600 seconds, 24 hours; the first check is the 16-hour deadline exit scan, then the entry test inside the 300-second window after an entry bar closes.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist, each check derived from the algorithm above:

- Check the deadline exit: a position at or past `opened_at` plus 16 hours (or its `exit_due_at`) exits in full even when funding is absent, a position with no deadline on record is not exited, and any held position blocks a new entry.
- Check the entry window: an evaluation more than 300 seconds after the entry bar close, or before it, produces no entry on identical bars and funding; this sleeve does not get the cadence-length window extension.
- Check the signal: a signal bar close at or below the maximum high of the prior 20 bars blocks entry, as do fewer than 22 bars and a gap between the signal and entry bars.
- Check funding: absent funding, a funding record settled more than 12 hours before the signal close, and a known rate >= 0 each block entry; with the revalidation switch ON, funding that turns non-negative by the entry close also blocks entry, and with it OFF the signal-time rate alone decides.
- Check sizing: quantity equals floor(cash / (price times 1.001)) in whole ADA units with no volume cap, and a floored quantity of 0 produces no intent.
- Check intent shape: symbol ADAUSDT, market order, time in force gtc, side buy for entry and sell for exit, price hint the entry bar close for entries.
