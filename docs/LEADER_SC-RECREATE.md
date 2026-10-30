# leader_sc: Recreation package

Provenance: Source row in strategies/femto/femto-leader-d.md in this repo: The old Alpaca swing desk's Leader-1d research, via Femto-lean; its killed study, forward-tested.

## What this sleeve is
This sleeve is the small-cap Leader-1d variant: the same gated daily leader events, restricted to the bottom decile of names by trailing 52-week mean weekly dollar volume, with an added volume cap on position size. It otherwise shares the daily variant's 20-session hold and 25% disaster stop.

## Full algorithm
The event itself is a core Data / research-frame product served as extra["leader_events"] = {symbol: event date}: the existing card states the frame (a closed daily bar scoring at least 3 of 5: close >= 8% over EMA(21); RSI(12) >= 60; volume >= 1.2 x its 20-day mean; 20-day path efficiency >= 0.30; at least 4 of 7 trend votes; plus a gate: a UT Bot buy flip (cyan) or an EMA 8/21 cross after a recent flip (green)). The strategy files in this repo consume the served event; they do not recompute the score.
Strategy (desk3/vendor/sleeves/leader_sc.py): HOLD_BARS = 20, MIN_BARS = 252, BAND_FRAC = 0.10, MAX_POSITIONS = 10, DISASTER_STOP = 0.25, COST_BPS_SIDE = 0.015 (150 bps per side, paper cost reference). SleeveConfig: cadence_s=300, universe=(), state_schema={"position": "dict|None", "last_event": "dict"}, risk_pct=None.
Band (band_symbols, verbatim): group each symbol's served weekly input by Monday (volume accumulates across the week's bars, the last close of the week is kept); a symbol needs at least 52 completed weeks before the current week's Monday (index >= 51); its band value is the mean over the trailing 52 weeks of close x accumulated weekly volume. The band is the lowest max(9, int(candidate_count x 0.10)) symbols by that mean.
Adapter (desk3/sleeves/leader_sc.py): INPUTS = ('bars:*:1Day', 'bars:*:1Week', 'positions', 'journal:self'); WARMUP_BARS = {"1Day": 252, "1Week": 52}. It fetches 300 daily and 120 weekly bars; when no 1Week cache exists the daily bars serve as the weekly input (the strategy groups them by Monday itself). It derives sleeve_state, serves last_event from the journal, and files leader_last_event records as in leader_d.
Exits first: identical staging to leader_d (bars strictly after entry_date >= 19 exits the full qty at the last daily close, reason "leader_sc hold complete").
Entries require equity > 0, extra["spy_down_regime"] true, and a non-empty weekly input, else exits only (the strategy code gates on spy_down_regime for this sleeve as written). For event symbols in sorted order, while open positions < 10: skip SPY, held symbols, and any symbol not in the band; require at least 252 daily bars; skip a consumed event (last_event equal). Price = last daily close (> 0 required). Base quantity = int((equity x 0.01) // price); below 1 takes no position. ENH volume cap (switch extra["leader_sc_enhance"]["enabled"], default ON): cap the quantity at int((trailing-52-week mean weekly dollar volume / 5) // price); when the capped quantity is below 1 the entry is refused. OFF restores the flat 1% sizing exactly. Emit an enter intent with price_hint = round(price, 2), stop = round(price x 0.75, 2), exit_rules=(ExitRule("stop", stop), ExitRule("time_bars", 20)), reason naming the event, the SPY down regime and the small-cap band.

## Files in this repo
- Sleeve module (desk desk3/sleeves/leader_sc.py): `desk3/sleeves/leader_sc.py`.
- Strategy (desk desk3/vendor/sleeves/leader_sc.py, byte-identical vendored copy loaded by load_strategy): `sleeves/leader_sc.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Journal runtime used by the adapter to serve and file leader_last_event records: `engines/desk3/vendor/runtime/journal.py` (desk desk3/vendor/runtime/journal.py).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/femto/femto-leader-d.md (the Small caps variant row).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:*:1Day, bars:*:1Week, positions, journal:self.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["leader_events"], ["spy_down_regime"], ["weekly"], ["sleeve_state"] and ["last_event"] as stated in the Full algorithm section; daily bars (300 fetched) are the strategy's bars argument and the fallback weekly input.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `leader_sc` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the band: a symbol with only 51 completed weeks is excluded; weekly volume is the sum across the week's bars, not the last day's; the band holds exactly max(9, int(candidates x 0.10)) names, the lowest by trailing mean.
- Check that a non-band event symbol, SPY, and a held symbol each produce no entry, and that missing weekly input or a false spy_down_regime leaves exits only.
- Check the ENH cap: the treatment quantity is min(base qty, int((mean weekly dollar volume / 5) // price)); with mean weekly dollar volume 4,000, price 40.00 and equity 100,000 the base qty is 25 and the capped qty is int(800 // 40.00) = 20; when the cap computes below 1 share the entry is refused with the switch ON and taken at base qty with it OFF.
- Check exit staging (19 bars after entry) and the entry stop / time-exit rules exactly as for leader_d.
