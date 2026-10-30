# fwd_alpaca_ada_rsi2: Recreation package

Provenance: Source row in strategies/ausar/public-rsi2.md in this repo: Larry Connors' RSI(2), via trader.dev, StockCharts and Tomazetti's Pine script; the old swing desk via Femto-lean.

## What this sleeve is
This sleeve is the Alpaca forward test of the Tomazetti RSI(2) recipe on ADA/USD hourly bars: it buys an extreme RSI(2) dip in an uptrend and sells when price closes back above its 5-bar average. The recipe features themselves are fenced: they must be served as a data product, and without them the sleeve reports BLOCKED and emits nothing.

## Full algorithm
Adapter (desk3/sleeves/fwd_alpaca_ada_rsi2.py): INPUTS = ('bars:ADA/USD:1Hour', 'positions'); WARMUP_BARS = {"1Hour": 200}. It fetches 400 1Hour bars for ADA/USD, builds extra via the port4 bridge, and calls the strategy signal with old_context.
Strategy (desk3/vendor/sleeves/fwd_alpaca_ada_rsi2.py): SPEC = {id: FWD_ALPACA_ADA_RSI2_V1, preserves: PUBLIC_TOMAZETTI_RSI2_SPOT100, strategy: tomazetti_rsi2, symbol: ADA/USD, timeframe: 1Hour, step_seconds: 3600, warmup: 200, listed: True}. ACCOUNT = "fwd_alpaca_ada_rsi2_v1", BUDGET_USD = 100,000, MAX_EXPOSURE = 0.10, MAX_SPREAD_BPS = 100, DECISION_SECONDS = 300. SleeveConfig: cadence_s=3600, universe=("ADA/USD",), state_schema={"position": "dict|None"}, risk_pct=None. The existing card states the recipe the served features encode: RSI(2) < 10, close above the 200-bar average and below the 5-bar average, and the 4-bar mean of RSI(2) < 30 for an entry (features["long_signal"]); the close exit is features["long_close_signal"] (close back above the 5-bar average). No stop (the source stop is off).
decide() evaluation order: (1) Bars None means BLOCKED, orders disabled. (2) Drop bars that have not completed (bar open + 3600 s > now). (3) Compute due exits before the warmup gate: the close-signal exit (features present, long_close_signal true, held > 0) and the ENH trend exit (below). (4) Fewer than 200 completed bars and no due exit means BLOCKED with the bar count. (5) Entry timing: age of the last completed bar's close must be within 0..300 s, unless a due exit exists (a due exit fires on any pass, still quote-gated). Outside the window with no due exit: ACTIVE/OUTSIDE WINDOW, no order. (6) Features None and no due exit: BLOCKED with the fence reason (the recipe source is in the excluded archive; features are fenced). (7) Entry requires features["long_signal"] true and held <= 0 (long only, no pyramid); otherwise ACTIVE/AWAITING SIGNAL.
ENH trend exit (switch extra["fwd_alpaca_ada_rsi2_enhance"]["enabled"], default ON): while held, a completed bar closing below the served features["long_ma"] (the 200-bar average) is a due exit on the next pass under the same quote gates. OFF restores exit only on long_close_signal.
Quote and sizing gates (for both entry and due exit): a quote is required, with bid, ask and exchange_at present; bid > 0, ask >= bid, quote stamp not in the future and no more than 10 s old, and (ask-bid)/ask x 10000 <= 100 bps, else BLOCKED. Side is sell when held > 0 else buy; price is the bid for a sell and the ask for a buy. Buy quantity = floor to 8 decimals of (100,000 x 0.10 / price); a buy whose qty x price exceeds the 10% cap plus $0.01 is BLOCKED. Sell quantity is the full held quantity (the cap does not gate exits). A PAPER-ACTIVE row becomes one Intent: kind enter/exit by side, qty = the order quantity, limit_price and price_hint (rounded to 6 places) = the order price, reason naming the side, qty, bar close, strategy and account.

## Files in this repo
- Sleeve module (desk desk3/sleeves/fwd_alpaca_ada_rsi2.py): `desk3/sleeves/fwd_alpaca_ada_rsi2.py`.
- Strategy (desk desk3/vendor/sleeves/fwd_alpaca_ada_rsi2.py, byte-identical vendored copy loaded by load_strategy): `sleeves/fwd_alpaca_ada_rsi2.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/ausar/public-rsi2.md (the ADA 1h / Alpaca forward variant row).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 3600 seconds (1 hour). Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:ADA/USD:1Hour, positions.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["features"]: the fenced recipe product {long_signal, long_close_signal, long_ma}; absent features means BLOCKED, never an entry.
- context.extra["quote"]: {bid, ask, exchange_at}; context.extra["held_qty"] and context.extra["entry_close_at"] come from the served positions (the adapter derives held_qty / entry_close_at from a held LINK-style position record only where the adapter code does so; for this sleeve held state arrives via build_extra).

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `fwd_alpaca_ada_rsi2` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the fence: with 200+ completed bars, a fresh quote and features=None, the result is BLOCKED with the fence reason and no intent.
- Check warmup: 199 completed bars and no due exit is BLOCKED; an uncompleted (still-forming) hourly bar is dropped before counting.
- Check the decision window: an entry signal 301 s after the last completed bar close produces no entry, while a due close-signal exit at the same age still fires if the quote passes.
- Check quote gates: a quote 11 s old, a future quote stamp, a crossed quote, and a spread of 101 bps each block both entry and exit.
- Check sizing: at ask 2.00 the buy quantity is exactly 5000.00000000 ADA (10% of $100,000 / 2.00, floored to 8 decimals), and a sell exits the full held quantity even after price appreciation.
- Check the ENH exit: held, last close below features["long_ma"] exits with the switch ON and does not exit (absent long_close_signal) with extra["fwd_alpaca_ada_rsi2_enhance"]["enabled"]=false.
