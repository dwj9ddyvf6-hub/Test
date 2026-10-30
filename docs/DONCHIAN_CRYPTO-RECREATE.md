# donchian_crypto: Recreation package

Provenance: Source row in strategies/femto/femto-donchian.md in this repo: The old Alpaca swing desk, via Femto-lean (family Femto-lean, asset US equities and crypto (SOL), timeframe 1d and 15m, universe 41-name old-desk basket and SOL/USD, style trend breakout). This package covers the crypto variant; the equity variant is the separate sleeve donchian.

## What this sleeve is
This sleeve runs the Donchian 20/10 breakout on SOL/USD 15-minute bars, the asset and timeframe the spec was validated on: one long position, exiting on the 10-bar low channel or a synthetic 2-ATR trailing stop. There is no time stop and no disaster stop in the validated spec. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/donchian_crypto.py signal(bars, slice_state, context), with entry filtering through desk3/enhance14.py in the adapter path.

## Full algorithm
Constants (sleeves/donchian_crypto.py): SYMBOL = "SOLUSD", ENTRY_CHANNEL = 20, EXIT_CHANNEL = 10, WARMUP_BARS = 40, ATR_PERIOD = 14, ATR_MULT = 2.0, RISK_FRACTION = 0.0025, MAX_POSITIONS = 1, SLEEVE_NOTIONAL_CAP = 0.25, MIN_NOTIONAL = 10.0. CONFIG: cadence_s 900, universe (SYMBOL,), risk_pct RISK_FRACTION. Closed 15-minute bars only; long only.

Entries, in code order:
1. Warmup: at least WARMUP_BARS = 40 closed bars are required.
2. Breakout (detect_breakout): the last close is strictly above max(high of the prior 20 bars) (ties do NOT count) and volume is above 0.
3. Chase gate (ENH-DONCHIAN-CRYPTO-20261024, on by default): an entry is refused when the close is more than 2 x ATR(14) above the breakout level (chase_refused); OFF restores the pre-change rule.
4. Sizing (size_qty): quantity from RISK_FRACTION = 0.25 percent of equity divided by the stop distance 2.0 x ATR(14), capped at SLEEVE_NOTIONAL_CAP = 25 percent notional; a $10 minimum notional floor applies, and the floored quantity is re-checked against both the risk and cap rails (a floored quantity breaching either means no trade). At most MAX_POSITIONS = 1 position.

Exits (check_exit, first trigger wins): the last close is below min(low of the prior 10 bars); or the last low is at or below the trailing stop level (trail_level: the ratcheted highest close since entry minus 2.0 x ATR(14), recomputed purely from bars; crypto has no native broker stops, so the trail is synthetic, core-executed logic expressed in the intent). No time stop and no disaster stop exist in this module.

Position management: single position in SOLUSD, long only, no pyramiding.

## Files in this repo
- Sleeve module (desk sleeves/donchian_crypto.py): `sleeves/donchian_crypto.py`.
- v3 adapter (desk adapters3/donchian_crypto.py): `adapters3/donchian_crypto.py`; also present as `integration/donchian_crypto_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- Shared entry filter in the adapter delegation path: `engines/desk3/enhance14.py` (desk source desk3/enhance14.py, vendored in this repo per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-donchian.md`.

## Configuration
- Universe: SOLUSD only (traded as SOL/USD). Asset: crypto spot. Timeframe: 15m closed bars.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.0025 in CONFIG (0.25 percent of equity per trade on the 2 x ATR stop distance, 25 percent notional cap, $10 minimum).
- Cadence: 900 seconds. Session: 24h. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- bars: 15-minute SOL bars (120 per the card), a core Data product in the lean desk (the module header notes the old desk sourced them from Kraken public OHLC because the broker's crypto market-data endpoints 404); at least 40 closed bars are required.
- sleeve_state position with entry price and quantity arrives through the snapshot context, for trail reconstruction from bars.

## Install and run
1. Place the sleeve module at sleeves/donchian_crypto.py and the adapter at adapters3/donchian_crypto.py (repo copies at the same paths). The adapter uses evaluate_ported from the snapshot glue and the shared filter at desk3/enhance14.py (repo copy at engines/desk3/enhance14.py).
2. Register the roster row for `donchian_crypto` exactly as in the Configuration section in config/sleeves.json (module adapters3.donchian_crypto).
3. Wire the producers so every snapshot carries: 15-minute SOL bars and this sleeve's position; the session is 24h, so no regular-hours gate applies.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch2_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check the breakout: a close tying the prior 20 bars' highest high, volume of 0, or only 39 closed bars each produce no entry; a strict break produces one.
- Check the chase gate: a close more than 2 x ATR above the breakout level is refused with the enhancement on and allowed with it off.
- Check sizing: quantity follows 0.25 percent risk over 2 x ATR, never exceeds 25 percent notional, the $10 floor applies only when the floored quantity still passes both rails, and a second position is refused.
- Check exits: a close below the prior 10 bars' lowest low or a low at or below the ratcheted trail (highest close minus 2 x ATR) exits, and no time-based exit ever fires.
