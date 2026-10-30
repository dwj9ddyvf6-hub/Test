# fwd_alpaca_link_ai_volume: Recreation package

Provenance: Source row in strategies/ausar/ai-volume.md in this repo: AI Volume Strategy (TradingView Pine), adapted by Ausar.

## What this sleeve is
This sleeve is the Alpaca forward test of the AI-volume recipe on LINK/USD 4-hour bars: it buys a volume-spike bar that closes up and above its price EMA, and exits flat on the fifth bar of the position. As with the ADA forward sleeve, the recipe features are fenced and must be served; without them it reports BLOCKED and emits nothing.

## Full algorithm
Adapter (desk3/sleeves/fwd_alpaca_link_ai_volume.py): INPUTS = ('bars:LINK/USD:4Hour', 'positions'); WARMUP_BARS = {"4Hour": 60}. It fetches 300 4Hour bars for LINK/USD; if LINK/USD is held it derives extra["held_qty"] from the held map and extra["entry_close_at"] from the position's opened_at. A quote product is not in the cache; extra may carry one in params, and absent it decide() returns its QUOTE / BLOCKED outcomes with no intent.
Strategy (desk3/vendor/sleeves/fwd_alpaca_link_ai_volume.py): SPEC = {id: FWD_ALPACA_LINK_AI_VOLUME_V1, preserves: PUBLIC_AI_VOLUME_SPOT100, strategy: ai_volume, symbol: LINK/USD, timeframe: 4Hour, step_seconds: 14400, warmup: 60, listed: True}. ACCOUNT = "fwd_alpaca_link_ai_volume_v1", BUDGET_USD = 100,000, MAX_EXPOSURE = 0.10, MAX_SPREAD_BPS = 100, DECISION_SECONDS = 300. SleeveConfig: cadence_s=14400, universe=("LINK/USD",), state_schema={"position": "dict|None"}, risk_pct=None. The existing card states the recipe the served features encode: volume > 2 x EMA20(volume), close > EMA50(price) and close > open for an entry (features["long_signal"]); opposite-spike / close-signal handling rides features["long_close_signal"]. No stop in the source recipe.
decide() evaluation order: (1) Bars None means BLOCKED. (2) Drop uncompleted bars (open + 14400 s > now). (3) Compute due exits before the warmup gate: the timed exit (held > 0 and at least 5 completed bars with close_at >= the entry bar's close instant, counting by instant not string order; an unparseable entry anchor fails closed) and the ENH EMA exit (below). (4) Fewer than 60 completed bars and no due exit means BLOCKED. (5) Entry timing: last completed bar close age within 0..300 s unless a due exit exists. (6) Features None and no due exit: BLOCKED with the fence reason. (7) Entry requires long_signal true and held <= 0 (long only, no pyramid).
ENH EMA exit (switch extra["fwd_alpaca_link_ai_volume_enhance"]["enabled"], default ON): while held, a completed bar closing below the served features["price_ema"] is a due exit on the next pass under the same quote gates; the fifth-bar timed exit remains the outer bound. OFF restores the fifth-bar-only exit.
Quote and sizing gates are identical in form to the ADA forward sleeve: quote with bid, ask, exchange_at required; bid > 0, ask >= bid, stamp not future and <= 10 s old, spread <= 100 bps. Buy price = ask, quantity = floor to 8 decimals of (100,000 x 0.10 / price), buy notional capped at the 10% cap plus $0.01; sell price = bid, quantity = the full held quantity. A PAPER-ACTIVE row becomes one Intent with qty, limit_price and price_hint (6 places) as in the ADA sleeve, reason naming strategy ai_volume and this account.

## Files in this repo
- Sleeve module (desk desk3/sleeves/fwd_alpaca_link_ai_volume.py): `desk3/sleeves/fwd_alpaca_link_ai_volume.py`.
- Strategy (desk desk3/vendor/sleeves/fwd_alpaca_link_ai_volume.py, byte-identical vendored copy loaded by load_strategy): `sleeves/fwd_alpaca_link_ai_volume.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/ausar/ai-volume.md (the Alpaca forward row).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 14400 seconds (4 hours). Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:LINK/USD:4Hour, positions.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["features"]: {long_signal, long_close_signal, price_ema}; absent features means BLOCKED, never an entry.
- context.extra["quote"]: {bid, ask, exchange_at}, when a producer supplies one; context.extra["held_qty"] and ["entry_close_at"] derived by the adapter from the held LINK/USD position.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `fwd_alpaca_link_ai_volume` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the fence, warmup (59 completed bars blocks, 60 passes the gate), completed-bar dropping and the 300 s entry window exactly as for the ADA forward sleeve, with step_seconds 14400.
- Check the timed exit: with entry_close_at at the first of 5 completed bars at/after entry, the exit is due; with only 4 it is not; an unparseable entry anchor produces no timed exit.
- Check the ENH exit: held, last close below features["price_ema"] exits before the fifth bar with the switch ON and not with it OFF.
- Check sizing at ask 20.00 is exactly 500.00000000 LINK and that a sell exits the full held quantity.
- Check quote gates: 11 s old, future, crossed, or 101 bps spread each block.
