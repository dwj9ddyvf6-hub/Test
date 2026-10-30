# gate_1h: Recreation package

Provenance: Source row in strategies/femto/femto-leader-d.md in this repo: The old Alpaca swing desk's Leader-1d research, via Femto-lean; its killed study, forward-tested.

## What this sleeve is
This sleeve is the hourly variant of the Leader-1d event family: after a gated daily leader event on a basket name, it enters at the open of the first regular-hours hourly bar after the event date and holds 20 hourly bars. It is a strategy named Gate 1H, not a core chart gate.

## Full algorithm
The event itself is a core Data / research-frame product served as extra["leader_events"] = {symbol: event date}: the existing card states the frame (a closed daily bar scoring at least 3 of 5: close >= 8% over EMA(21); RSI(12) >= 60; volume >= 1.2 x its 20-day mean; 20-day path efficiency >= 0.30; at least 4 of 7 trend votes; plus a gate: a UT Bot buy flip (cyan) or an EMA 8/21 cross after a recent flip (green)). The strategy files in this repo consume the served event; they do not recompute the score.
Strategy (desk3/vendor/sleeves/gate_1h.py): HOLD_BARS = 20, DEOVERLAP_BARS = 20, MIN_BARS = 252, MAX_POSITIONS = 10, DISASTER_STOP = 0.25, COST_BPS_SIDE = 0.001 (10 bps per side, a paper cost reference). SleeveConfig: cadence_s=300, universe=(), state_schema={"position": "dict|None", "last_event": "dict", "last_entry_bar": "dict"}, risk_pct=None.
Adapter (desk3/sleeves/gate_1h.py): INPUTS = ('bars:*:1Day', 'bars:*:1Hour', 'positions', 'journal:self'); WARMUP_BARS = {"1Day": 252, "1Hour": 22}. It fetches 300 daily and 200 hourly bars for the candidate symbols, filters the hourly bars to the RTH-only grid (bar-start hour 13 <= UTC hour < 20) before serving them as extra["bars_1h"], derives sleeve_state from positions, serves last_event from the journal's leader_last_event records (last 4000 lines) and last_entry_bar from each position's entry_bar_t, and after translation files a leader_last_event journal record for each entry intent whose reason carries an event date.
Exits first, per held symbol: find the entry bar index in the RTH hourly grid (the first bar with t >= entry_bar_t; if the position record has only entry_date, the first RTH bar on/after that date). When (last index - entry index) >= 20, exit the full qty at the last hourly close (rounded to 2), reason "gate_1h hold complete". The 25% disaster stop rides the entry intent as an ExitRule (below), not an in-signal check.
Entries, for event symbols in sorted order, while open positions < 10: skip held symbols; require at least 252 daily bars for the symbol; skip when last_event[symbol] equals this event date (dedupe); require at least 22 hourly bars (HOLD_BARS + 2); let b0 = the first RTH hourly bar whose UTC date is strictly after the event date, and skip when none. ENH stale-entry refusal (switch extra["gate_1h_enhance"]["enabled"], default ON): skip when b0 is not the latest served hourly bar (b0 < len(h1) - 1); a refusal does not consume the event. De-overlap: when last_entry_bar[symbol] exists, find the last hourly bar at or before that stamp and skip when b0 - that index < 20. Price = the open of bar b0; skip when <= 0. Quantity = int((equity x 0.01) // price); a quantity below 1 takes no position (no forced floor). Emit an enter intent with price_hint = round(price, 2), stop = round(price x 0.75, 2), exit_rules=(ExitRule("stop", stop),), reason naming the event date and bar index. Entries require equity > 0 (exits are computed before that check).

## Files in this repo
- Sleeve module (desk desk3/sleeves/gate_1h.py): `desk3/sleeves/gate_1h.py`.
- Strategy (desk desk3/vendor/sleeves/gate_1h.py, byte-identical vendored copy loaded by load_strategy): `sleeves/gate_1h.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Journal runtime used by the adapter to serve and file leader_last_event records: `engines/desk3/vendor/runtime/journal.py` (desk desk3/vendor/runtime/journal.py).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/femto/femto-leader-d.md (the Hourly variant row; the card's basket is the 41-name basket, SIVEF excluded by the old basket reader per the strategy header).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:*:1Day, bars:*:1Hour, positions, journal:self.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["leader_events"], ["bars_1h"] (RTH-filtered by the adapter), ["sleeve_state"], ["last_event"] and ["last_entry_bar"] as stated in the Full algorithm section; daily bars (300 fetched) are the strategy's bars argument, used for the 252-bar minimum.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `gate_1h` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the RTH grid: hourly bars starting before 13:00Z or at/after 20:00Z are excluded before any hold or de-overlap counting.
- Check the entry bar: b0 is the first hourly bar whose UTC date is strictly after the event date, and the entry price is that bar's open.
- Check the ENH stale rule: when b0 is not the latest hourly bar, no entry with the switch ON and an entry (subject to de-overlap) with it OFF; the event is not consumed by a refusal.
- Check de-overlap: a new b0 fewer than 20 bars after the last entry bar's index is skipped.
- Check sizing and stop: at equity 100,000 and open 40.00, qty is exactly 25 and stop is 30.00; at a price above 1% of equity, qty is 0 and no position is taken.
- Check the exit: exactly 20 hourly bars after the entry index exits the full qty at the last hourly close; 19 does not.
- Check dedupe (last_event equal to the event) and the 252-daily-bar and 22-hourly-bar minimums each block entry.
