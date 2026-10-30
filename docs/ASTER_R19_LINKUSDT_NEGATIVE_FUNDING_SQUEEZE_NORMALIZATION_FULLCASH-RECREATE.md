# aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash: Recreation package

Provenance: Ausar R17/R18 crypto research, run as the R19 native-spot books (Source row in strategies/ausar/r19-crypto-breakout.md in this repo).

## What this sleeve is
This sleeve is a Binance spot LINKUSDT breakout sleeve that only enters when the latest observed perpetual funding rate is negative. It holds a single spot position and exits when funding normalizes to zero or above, with a 96-hour deadline as backstop. It is a thin wrapper delegating to desk3/aster_b12_crypto.py with its own SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_b12_crypto.py): sym="LINKUSDT", fam="nfs" (negative_funding_squeeze), exit="normalization", cap="fullcash", hold_h=96. Fee constant FEE=0.001 (10 bps) in both aster_b12_crypto.py and aster_b11_crypto.py.

Evaluation order in desk3/aster_b12_crypto.py::evaluate(sid, view, ctx):
1. Exits first, over every non-zero position whose symbol matches LINKUSDT (or is None / contains LINKUSDT). held = hours from opened_at/entry_time to now, else age_hours. If held >= 96, exit the whole absolute quantity, reason `aster_deadline_normalization_96h`. This deadline branch is checked first and fires even when bars or funding are missing (price hint falls back to avg_price).
2. Normalization exit (only if the deadline did not fire): if exit="normalization", the latest observed funding rate is not None and funding >= 0, and the trigger is executable, exit the whole quantity with reason `aster_funding_normalized rate=<funding>`. Trigger executable means the latest 4h bar's open time t satisfies now >= t + 8h (the bar closes at t+4h and the archive executes no earlier than close+4h).
3. If any exit was produced, or any matching position exists at all, return the exits / empty list: no entry while a position is held (one position per book).
4. Entry breakout gate (helper _breakout in desk3/aster_b11_crypto.py): at least 21 completed 4h bars and the last bar's close > the highest high of the prior 20 bars (bars[-21:-1]).
5. Funding gate: for fam="nfs", refuse entry if funding is None or funding >= 0. Missing funding is never assumed; the sleeve is UNFED with no funding producer wired.
6. Stale-signal gate (ENH-B8 in desk3/aster_b11_crypto.py, switch extra["aster_edge"][sid]["stale_signal_gate"], default ON): refuse entry when the signal bar closed more than 4.0 hours before now. OFF restores the pre-change rule exactly. Exits are untouched by this gate.
7. Sizing (fullcash): qty = cash * (1 - 0.001) / last close, where cash is view.slice.cash_usd or 10000.0. No volume cap applies to this sleeve (that is the volume1pct arm). Refuse if qty <= 0. Entry intent: kind="enter", side="buy", position_intent="buy_to_open", qty rounded to 8 decimals, price_hint = last close, reason naming fam, breakout close, funding and cap=fullcash.

No stop and no target beyond the rules above.

## Files in this repo
- Sleeve wrapper: `adapters3/aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash.py` (also `sleeves/aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash.py` and `integration/aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash_adapter.py`).
- Shared engines: `desk3/aster_b12_crypto.py` (this sleeve's SPECS entry and evaluate) and `desk3/aster_b11_crypto.py` (shared _bars, _funding, _now, _ts, _breakout, _stale_blocked helpers).
- Contract type: desk3/contract.py, whose repo copy is at `engines/desk3/contract.py` in engines_map.json with status gate_blocked, so that copy was not vendored by the engines pass; the desk original must be supplied from desk3/contract.py to run.
- Existing family card: `strategies/ausar/r19-crypto-breakout.md`.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Universe: LINKUSDT only (Binance spot, fixed in the SPECS entry). Timeframe: 4h bars.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0; fullcash sizing as above; bp_buffer_frac=0.02.
- Cadence: 14400 seconds. Session: 24h.
- flat_by_close: false; flatten_time_et: null; params: {} (empty in the roster row; all parameters live in the engine SPECS entry above).
- Parked: false.

## Data inputs
- Inputs declared in the roster row and the engine INPUTS tuple: bars, funding, positions.
- bars: view["bars"] keyed by `LINKUSDT|4Hour`, `LINKUSDT|4h`, `LINKUSDT|240min` or LINKUSDT, sorted by t; the code consumes completed 4h bars (at least 21 for the breakout).
- funding: view["funding"] for LINKUSDT (a rate value or a dict with rate), falling back to view["extra"]["funding_rate"]; the engine header states no v3 funding producer is wired yet, so this sleeve lands visibly UNFED, never fake-fed.
- positions: view["positions"] rows with symbol, qty, opened_at/entry_time or age_hours, and avg_price.

## Install and run
1. Place the engine file(s) listed above in a fresh desk at their desk paths and the wrapper at `adapters3/aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash.py` with SLEEVE_ID = "aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash" (the repo also carries `sleeves/aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash.py` and `integration/aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash_adapter.py` copies).
2. Register the roster row for `aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash, the cadence, session, slice and inputs stated there).
3. Wire the producers named in the Data inputs section so every evaluation snapshot carries the declared inputs, view now (or ctx now), and, where the engine uses it, ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the wrapper, which calls desk3.aster_b12_crypto.evaluate(SLEEVE_ID, view, ctx). Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the breakout gate: with 20 prior bars, no entry; with 21 bars and last close at or below the prior 20-bar high, no entry; with last close above it and funding < 0 and a fresh signal bar, exactly one entry.
- Check the funding gate: funding None and funding >= 0 each produce no entry even on a valid breakout.
- Check sizing: entry qty equals round(cash * 0.999 / last close, 8) with cash 10000.0 by default, and no volume cap is applied.
- Check exits: at held >= 96h the deadline exit fires even with no bars and no funding; before 96h, funding >= 0 produces the normalization exit only when now >= last bar open + 8h, and funding < 0 produces no exit.
- Check that any held position suppresses entries, and that a signal bar closed more than 4h before now is refused with the stale gate ON and allowed (subject to the other gates) with it OFF.
