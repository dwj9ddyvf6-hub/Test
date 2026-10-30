# donchian: Recreation package

Provenance: Source row in strategies/femto/femto-donchian.md in this repo: The old Alpaca swing desk, via Femto-lean (family Femto-lean, asset US equities and crypto (SOL), timeframe 1d and 15m, universe 41-name old-desk basket and SOL/USD, style trend breakout). This package covers the equity variant; the SOL variant is the separate sleeve donchian_crypto.

## What this sleeve is
This sleeve buys a daily close above the prior 20 bars' highs in the 41-name basket and exits on a close below the prior 10 bars' lows, a 2-ATR trailing stop, a 20-session time stop or a 25 percent disaster stop. It is the equity Donchian 20/10 breakout. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/donchian.py signal(bars, slice_state, context), with entry filtering through desk3/enhance14.py in the adapter path recorded in the audit chain.

## Full algorithm
Constants (sleeves/donchian.py): ENTRY_CHANNEL = 20, EXIT_CHANNEL = 10, WARMUP_BARS = 25, ATR_PERIOD = 14, ATR_MULT = 2.0, HOLD_DAYS = 20, DISASTER_STOP = 0.25, RISK_FRACTION = 0.0025, MAX_POSITIONS = 8, SLEEVE_NOTIONAL_CAP = 0.25. CONFIG: cadence_s 300, universe (), risk_pct RISK_FRACTION. Bars are daily dicts {t, o, h, l, c, v} ascending; the universe is the bars keys (the desk basket) unless context.extra universe overrides it.

Entries, in code order:
1. Warmup: at least WARMUP_BARS = 25 daily bars are required (entry_signal also needs the 20 prior bars for the channel).
2. Breakout: the last close is strictly above max(high of the prior 20 bars) (entry_signal); the card adds volume above 0 on the breakout bar.
3. Capacity and sizing: at most MAX_POSITIONS = 8 positions and SLEEVE_NOTIONAL_CAP = 25 percent of equity; size_qty gives quantity from RISK_FRACTION = 0.25 percent of equity divided by the disaster-stop distance (25 percent of entry price, i.e. about 1 percent notional per trade per the card).

Exits, in code order (first trigger wins in the module's check order):
1. Exit channel: the last close is below min(low of the prior 10 bars) (exit_channel_hit).
2. ATR trailing stop: the trail level ratchets to the highest close since entry minus ATR_MULT = 2.0 x ATR(14) and never loosens (atr_trail_level); a low touching the level exits (atr_trail_hit).
3. Time stop: at HOLD_DAYS = 20 sessions since entry, with the enhancement (ENH-DONCHIAN-20261024, on by default) it fires only when the last close is at or below the position's entry price (time_stop_fires with the profit gate); a profitable position lives under the channel and trail exits. With the gate off the time stop fires unconditionally at 20 sessions.
4. Disaster stop: -25 percent from entry, carried as the desk GTC disaster-stop law (DISASTER_STOP = 0.25).

Position management: at most 8 positions, 25 percent sleeve notional cap, long only, no pyramiding.

## Files in this repo
- Sleeve module (desk sleeves/donchian.py): `sleeves/donchian.py`.
- v3 adapter (desk adapters3/donchian.py): `adapters3/donchian.py`; also present as `integration/donchian_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- Shared entry filter in the adapter delegation path: `engines/desk3/enhance14.py` (desk source desk3/enhance14.py, vendored in this repo per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-donchian.md`.

## Configuration
- Universe: the 41-name old-desk basket (served as the bars keys; CONFIG universe is (), overridable via extra universe). Asset: US equities. Timeframe: 1d (checked daily at 10:32 ET per the card).
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.0025 in CONFIG (0.25 percent of equity per trade on the 25 percent disaster-stop distance).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- bars: split-adjusted daily bars (160 per the card; the module requires at least 25 and uses the last 21 for channels and ATR(14)) per basket symbol.
- sleeve_state: context.extra["sleeve_state"] {symbol: {"position": {entry_px, entry_date, qty, atr}}} for trail, time-stop and session counting.

## Install and run
1. Place the sleeve module at sleeves/donchian.py and the adapter at adapters3/donchian.py (repo copies at the same paths). The adapter path also places the shared filter at desk3/enhance14.py (repo copy at engines/desk3/enhance14.py).
2. Register the roster row for `donchian` exactly as in the Configuration section in config/sleeves.json (module adapters3.donchian).
3. Wire the producers so every snapshot carries: daily bars per basket symbol and this sleeve's positions in extra sleeve_state with entry price, entry date and ATR.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check the breakout: a close equal to (not above) the prior 20 bars' highest high produces no entry; a close above it with volume above 0 and fewer than 8 positions produces one, sized at 0.25 percent risk over the 25 percent stop distance.
- Check the channel exit: a close below the prior 10 bars' lowest low exits, and a close equal to it does not.
- Check the trail: the level only ratchets up (highest close minus 2 x ATR(14)) and a low touching it exits.
- Check the time stop: at 20 sessions a position at or below its entry price exits with the enhancement on, a profitable position does not, and with the gate off both exit.
