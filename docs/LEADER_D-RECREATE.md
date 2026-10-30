# leader_d: Recreation package

Provenance: Source row in strategies/femto/femto-leader-d.md in this repo: The old Alpaca swing desk's Leader-1d research, via Femto-lean; its killed study, forward-tested.

## What this sleeve is
This sleeve is the daily Leader-1d variant on the genome universe: it buys a stock on a gated daily leader event, but only while SPY is in a down regime, and sells about 20 sessions later. Positions are capped at 10 with a 25% disaster stop.

## Full algorithm
The event itself is a core Data / research-frame product served as extra["leader_events"] = {symbol: event date}: the existing card states the frame (a closed daily bar scoring at least 3 of 5: close >= 8% over EMA(21); RSI(12) >= 60; volume >= 1.2 x its 20-day mean; 20-day path efficiency >= 0.30; at least 4 of 7 trend votes; plus a gate: a UT Bot buy flip (cyan) or an EMA 8/21 cross after a recent flip (green)). The strategy files in this repo consume the served event; they do not recompute the score.
Strategy (desk3/vendor/sleeves/leader_d.py): HOLD_BARS = 20, MIN_BARS = 252, MAX_POSITIONS = 10, DISASTER_STOP = 0.25, COST_BPS_SIDE = 0.0005 (5 bps per side, paper cost reference). SleeveConfig: cadence_s=300, universe=(), state_schema={"position": "dict|None", "last_event": "dict"}, risk_pct=None.
Adapter (desk3/sleeves/leader_d.py): INPUTS = ('bars:*:1Day', 'positions', 'journal:self'); WARMUP_BARS = {"1Day": 252}. It fetches 300 daily bars for the candidate symbols, derives sleeve_state from positions, serves last_event from the journal's leader_last_event records, and files a leader_last_event record for each entry intent whose reason carries an event date. The SPY down-regime flag (extra["spy_down_regime"]) is a core Data product; the existing card states the daily variant's regime as SPY's 60-session return <= 0.
Exits first, per held symbol: sell_due counts daily bar dates (bar t + 4 h, as UTC dates) strictly after the position's entry_date; when that count >= 19 (HOLD_BARS - 1, staging the sell so the exit lands on the 20th session), exit the full qty at the last daily close (rounded to 2), reason "leader_d hold complete: bars_after_entry >= 19".
Entries require equity > 0 AND extra["spy_down_regime"] true, else exits only. For event symbols in sorted order, while open positions < 10: skip SPY itself and held symbols; require at least 252 daily bars; skip when last_event[symbol] equals this event date. ENH stale-event refusal (switch extra["leader_d_enhance"]["enabled"], default ON): skip when the event date is not the date of the latest served daily bar; a refusal does not consume the event. Price = the last daily close; skip when <= 0. Quantity = int((equity x 0.01) // price); below 1 takes no position. Emit an enter intent with price_hint = round(price, 2), stop = round(price x 0.75, 2), exit_rules=(ExitRule("stop", stop), ExitRule("time_bars", 20)), reason naming the event and the SPY down regime.

## Files in this repo
- Sleeve module (desk desk3/sleeves/leader_d.py): `desk3/sleeves/leader_d.py`.
- Strategy (desk desk3/vendor/sleeves/leader_d.py, byte-identical vendored copy loaded by load_strategy): `sleeves/leader_d.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Journal runtime used by the adapter to serve and file leader_last_event records: `engines/desk3/vendor/runtime/journal.py` (desk desk3/vendor/runtime/journal.py).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/femto/femto-leader-d.md (the Daily variant row; universe the 1,838-name genome per the card).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:*:1Day, positions, journal:self.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["leader_events"], ["spy_down_regime"], ["sleeve_state"] and ["last_event"] as stated in the Full algorithm section; daily bars (300 fetched) are the strategy's bars argument.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `leader_d` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the regime gate: with spy_down_regime false or missing, exits still evaluate but no entry fires.
- Check SPY itself is never entered, held symbols are skipped, and the 10-position cap holds.
- Check the ENH stale rule: an event date older than the latest daily bar date produces no entry with the switch ON and an entry with it OFF; dedupe by last_event blocks a consumed event in both modes.
- Check sizing and stop: at equity 100,000 and close 40.00, qty is exactly 25, stop 30.00, and the entry carries both the stop and the 20-bar time exit rule.
- Check the exit staging: 18 bars strictly after entry_date does not exit; 19 does, at the last close.
