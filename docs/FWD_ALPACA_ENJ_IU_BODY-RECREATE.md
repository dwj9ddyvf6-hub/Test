# fwd_alpaca_enj_iu_body: Recreation package

Provenance: Source row in strategies/ausar/iu-body.md in this repo: IU Big Body Bar (TradingView Pine), adapted by Ausar.

## What this sleeve is
This sleeve is a permanently blocked monitor: the ENJ/USD pair it would forward-test is not listed at Alpaca, so it never emits an intent and exists to journal that blocked status on every evaluation. The underlying IU big-body recipe (from the existing card) is stated for context, but no part of it runs in this sleeve.

## Full algorithm
Adapter (desk3/sleeves/fwd_alpaca_enj_iu_body.py): INPUTS = ('bars:ENJ/USD:1Min',); WARMUP_BARS = {}. On every evaluation it first logs a monitor_status record from the strategy's status() (ctx.log("monitor_status", **strat.status())), then fetches 10 1Min bars for ENJ/USD, builds the old context, and translates the strategy signal, which is always empty.
Strategy (desk3/vendor/sleeves/fwd_alpaca_enj_iu_body.py): SleeveConfig sleeve_id="fwd_alpaca_enj_iu_body", cadence_s=300, universe=("ENJ/USD",), monitor_only=True, state_schema={}, risk_pct=None. signal() returns [] unconditionally. status() returns {id: FWD_ALPACA_ENJ_IU_BODY_V1, preserves: PUBLIC_IU_BODY_SPOT100, status: BLOCKED, orders_disabled: True, reason: LIST_ERROR}, where LIST_ERROR states that Alpaca GET /v2/assets/ENJ/USD returned HTTP 404 asset not found, ENJ/USDT is also absent, the original ENJUSDT sleeve stays blocked on Binance HTTP 451, and no other ticker is substituted. There is no account and no sizing while unlisted. If the venue ever lists the pair, unblocking requires a new ruling, not a code default.
The fenced recipe (existing card, strategies/ausar/iu-body.md; it does NOT run here): on Binance ENJUSDT 5-minute bars, enter when a bar's body is more than 4 x the 20-bar average body (21 bars inclusive) and the bar closes up, sized at 100% of book cash including 10 bps, lot-floored; exit on a trailing stop starting at entry - 2 x ATR14 and raised to close - 2 x ATR14, hit by the observed bid.

## Files in this repo
- Sleeve module (desk desk3/sleeves/fwd_alpaca_enj_iu_body.py): `desk3/sleeves/fwd_alpaca_enj_iu_body.py`.
- Strategy (desk desk3/vendor/sleeves/fwd_alpaca_enj_iu_body.py, byte-identical vendored copy loaded by load_strategy): `sleeves/fwd_alpaca_enj_iu_body.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/ausar/iu-body.md.
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:ENJ/USD:1Min.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- The only data actually consumed is the 1Min ENJ/USD bar fetch (10 bars) in the adapter, which does not affect the always-empty signal; the journaled monitor_status record is the sleeve's output.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `fwd_alpaca_enj_iu_body` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check that signal() returns [] for every input, including a perfect IU big-body bar series.
- Check that every adapter evaluation logs one monitor_status record with status BLOCKED, orders_disabled true, id FWD_ALPACA_ENJ_IU_BODY_V1 and the LIST_ERROR reason naming the Alpaca 404 and the Binance 451.
- Check the config: monitor_only=True, universe exactly ("ENJ/USD",), and no substitute symbol appears anywhere.
