# fwd_coinbase_sma200: Recreation package

Provenance: Source row in strategies/ausar/coinbase-sma200.md in this repo: Ausar R14/R15 Coinbase research.

## What this sleeve is
This sleeve makes one BTC-USD decision a day in the first five minutes of the UTC day: with the strategy switch on (the default), it buys 0.01 BTC when flat and the just-closed daily close is strictly above its 200-day average, and sells the full holding when the close is strictly below it. Equality on either side is a no-trade point.

## Full algorithm
Adapter (desk3/sleeves/fwd_coinbase_sma200.py): INPUTS = ('bars:BTC-USD:1Day', 'positions', 'journal:self'); WARMUP_BARS = {"1Day": 200}. It fetches 260 1Day bars for BTC-USD (falling back to BTC/USD), discards the decision-day (forming) bar, and builds extra["history"] as [{date, close, complete: True, forming: False}] for completed days, plus extra["quote"] = {as_of: now, bid: last completed close, ask: last completed close}. It copies held_qty / sleeve_state / sleeve_state_flat from build_extra, serves the persisted coinbase_sma200_exp_journal, runs the strategy class directly, logs last_evaluation and any returned experiment journal, and translates the intents.
Strategy (desk3/vendor/sleeves/fwd_coinbase_sma200.py): ACCOUNT = "fwd_coinbase_sma200_v1", BUDGET_USD = 100,000.0, MAX_EXPOSURE = 0.10, VERSION = "coinbase-daily-v1", PRODUCT = "BTC-USD", WINDOW = 5 minutes, QTY_BTC = 0.01. SleeveConfig: cadence_s=300, universe=("BTC-USD",), state_schema={"decisions": "dict"}, risk_pct=None, parked=False.
decide() gates, in order: the decision id is ACCOUNT|VERSION|PRODUCT|day; an id already in extra["decisions"] returns duplicate and nothing fires. prepare() requires at least 200 completed, non-forming history rows whose last 200 dates are consecutive calendar days (a gap returns not ready). The moment must be inside 00:00-00:05 UTC (outside-window otherwise). A fresh native quote is required: as_of present with a timezone, age <= 30 s and not in the future. The history's last completed day must be exactly the day before the decision day (just-closed), else blocked. Passing all gates returns status executable with close = the just-closed close.
signal() treatment (switch extra["coinbase_sma200"]["strategy"], default ON; OFF restores the pre-change rule, which buys QTY_BTC on every executable day with no SMA test and no exit): SMA200 = the mean of exactly the last 200 completed closes prepare() proved; any non-finite or non-positive close in that window blocks. Held state: extra["sleeve_state_flat"]["BTC-USD"]["qty"] wins, else extra["held_qty"]; a claimed held qty that is not a valid positive price-like number blocks. Flat and close > SMA200: enter QTY_BTC at the quote ask (price_hint rounded to 2), blocked if 0.01 x ask > 0.10 x 100,000. Flat and close <= SMA200: nothing. Held and close >= SMA200: hold. Held and close < SMA200: exit the full held qty at the quote bid (price_hint rounded to 2). Every executable decision also files a paired shadow-control record (the pre-change rule scored with the treatment's exit logic, plus a raw accumulation count) on last_evaluation and into the served coinbase_sma200_exp_journal when one is served.

## Files in this repo
- Sleeve module (desk desk3/sleeves/fwd_coinbase_sma200.py): `desk3/sleeves/fwd_coinbase_sma200.py`.
- Strategy (desk desk3/vendor/sleeves/fwd_coinbase_sma200.py, byte-identical vendored copy loaded by load_strategy): `sleeves/fwd_coinbase_sma200.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Journal runtime used by the adapter's journal serving: `engines/desk3/vendor/runtime/journal.py` (desk desk3/vendor/runtime/journal.py).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/ausar/coinbase-sma200.md (the Aurelia forward variant row).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: 24h.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:BTC-USD:1Day, positions, journal:self.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["history"], ["quote"], ["decisions"], ["held_qty"] / ["sleeve_state_flat"], and ["coinbase_sma200_exp_journal"] are built by the adapter as stated in the Full algorithm section; the strategy consumes only those extra keys.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `fwd_coinbase_sma200` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the window: an otherwise-valid decision at 00:05 UTC or later returns outside-window and no intent; at 00:00-00:04 UTC it can fire.
- Check prepare(): 199 completed days, and 200 days with one calendar gap, each block; a forming row is not counted as completed.
- Check the just-closed rule: history ending two days before the decision day blocks even with 200 consecutive days.
- Check quote freshness: a quote 31 s old, a future quote, and a timezone-less quote stamp each block.
- Check duplicate suppression: the same decision id in extra["decisions"] never re-fires.
- Check the SMA partition: flat with close exactly equal to SMA200 does nothing; flat above enters exactly 0.01 BTC; held with close exactly equal holds; held below exits the full held qty at the bid.
- Check the switch OFF path buys 0.01 BTC on an executable day regardless of the SMA comparison and never exits.
