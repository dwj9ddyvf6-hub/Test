# legends_ema: Recreation package

Provenance: Source row in strategies/femto/femto-legends-ema.md in this repo: Milkman Trades' Legend's EMA, via the old Alpaca swing desk and Femto-lean; also the Milkman v2 study.

## What this sleeve is
This sleeve trades QQQ intraday mean reversion after a trend day: when the prior session's 15-minute bars never touched their EMA(20) and the session was a strong trend day, it trades the next open back toward that EMA, with a half-ATR stop, and is flat by 15:59 ET. It trades at most one position, in QQQ only.

## Full algorithm
Strategy (desk3/vendor/sleeves/legends_ema.py): SYMBOL = "QQQ"; RISK_FRACTION = 0.0025; EMA_SPAN = 20; WARMUP_SESSIONS = 5 (the served sessions before the setup session warm the EMA); ATR_SESSIONS = 14; STOP_ATR_MULT = 0.5; TREND_Q80 = 0.7686; FLAT_HM = 15:59 ET; entry window 09:30 <= ET time < 09:45. SleeveConfig: cadence_s=300, universe=("QQQ",), state_schema={"position": "dict|None"}, risk_pct=0.0025.
Adapter (desk3/sleeves/legends_ema.py): INPUTS = ('bars:QQQ:15Min', 'bars:QQQ:1Day', 'positions', 'journal:self'); WARMUP_BARS = {"15Min": 200, "1Day": 14}. It fetches 30 daily and 600 15-minute QQQ bars, groups the 15-minute bars by ET session into extra["bars_15m_by_session"] (sessions in date order), sets extra["daily_ranges"] to each daily bar's high - low, derives sleeve_state, serves the persisted legends_ema_exp_journal, runs the strategy class directly so its last_evaluation stamp survives, files a returned experiment journal via ctx.log, and calls the strategy with bars = {"QQQ": daily bars} (price hints only).
Setup (evaluate_setup): the last served session is the setup session; it needs at least 10 bars, and all served bars together at least EMA_SPAN + 2 = 22. EMA(20) is computed over every served bar's close, seeded at the first close with k = 2/21. trend = |session close - session open| / (session high - session low) (0 when the range is 0); trend_day when trend >= 0.7686. no_touch when no setup-session bar's [low, high] range contains its EMA value. ATR14 = the mean of the last 14 daily_ranges; anything other than exactly 14 finite ranges fails closed (no setup). Armed = trend_day AND no_touch. Direction is reversion toward the EMA: sell when the setup close is above the last EMA value, buy when below.
Live exits, evaluated in signal() before any entry, against the last QQQ daily close, side-aware from the position record's exit_rules / stop_px: for a long, close <= stop exits as "stop" and close >= target exits as "target"; for a short the comparisons invert. If neither fires and the position qty is non-zero (either sign) and ET time is >= 15:59, exit the full magnitude as "flat by 15:59 ET". The exit path is not weekday-guarded.
Entries: only Monday-Friday, only in the 09:30-09:45 ET window, only when flat, the setup is armed, equity > 0 and ATR14 is present. Reference price = the last QQQ daily close (falling back to the EMA value). Geometry: target = round(EMA last, 2); stop = round(ref - 0.5 x ATR14, 2) for a buy, round(ref + 0.5 x ATR14, 2) for a sell. Quantity = int((equity x 0.0025) // (0.5 x ATR14)). Entry geometry gate (switch extra["legends_ema_improve"]["entry_geometry_gate"], default ON; an owner ruling of 2026-10-23): refuse when |ref - EMA last| < 0.5 x ATR14 (equality is taken). A quantity below 1 takes no position. The enter intent carries qty_hint, price_hint = round(ref, 2), stop, target, side = the reversion side, position_intent buy_to_open / sell_to_open by side, and exit_rules (stop, target). Every armed setup reaching the gate point is also recorded once per session in the legends_ema_exp/1 experiment journal (paired shadow control run with the same close-based stop/target/flat logic), served and filed by the adapter as described above; the journal never changes live decisions beyond the gate itself.

## Files in this repo
- Sleeve module (desk desk3/sleeves/legends_ema.py): `desk3/sleeves/legends_ema.py`.
- Strategy (desk desk3/vendor/sleeves/legends_ema.py, byte-identical vendored copy loaded by load_strategy): `sleeves/legends_ema.py`.
- Shared bridge: `engines/desk3/port4_bridge.py` (desk desk3/port4_bridge.py).
- Snapshot context: `engines/desk3/port4_context.py` (desk desk3/port4_context.py: evaluate_via and load_strategy).
- Adapter journal helper imported by the desk adapter: adapters/_bridge.py serve_journal (named in the audit as a shared file for this sleeve; it is not in engines_map.json).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (the strategy imports BaseSleeve, Intent and SleeveConfig from core.sleeve).
- Existing per-sleeve card: strategies/femto/femto-legends-ema.md (the Femto-lean / Midna v3 QQQ row).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).

## Configuration
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the strategy's own virtual book / pool amounts are stated in the Full algorithm section where they differ (several of these strategies size off a $100,000 virtual book, not the $10,000 roster slice).
- Cadence: 300 seconds. Session: rth.
- flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; timeout_s: null; params: {} (empty in the roster row; all parameters live in the strategy code stated above).
- Parked: false.
- Inputs declared in the roster row: bars:QQQ:15Min, bars:QQQ:1Day, positions, journal:self.

## Data inputs
- The adapter's evaluate(view, ctx) runs through desk3/port4_context.evaluate_via, which serves the snapshot inputs declared in the module INPUTS tuple into an old-style context; the strategy then reads context.extra, context.equity, context.session and context.now.
- Bars are fetched through the port4 bridge from the snapshot bar cache at the sizes stated per sleeve in the Full algorithm section; positions arrive as the snapshot positions, from which the bridge derives held quantities and sleeve_state.
- context.extra["bars_15m_by_session"] (grouped by the adapter), ["daily_ranges"], ["sleeve_state"] and ["legends_ema_exp_journal"] as stated in the Full algorithm section; the bars argument is QQQ daily bars only.

## Install and run
1. Place the sleeve module, the strategy file and every shared engine file listed in 'Files in this repo' at the same repo paths in a fresh desk (desk paths are the repo paths with any leading `engines/` stripped for engine files).
2. Register the roster row for `legends_ema` exactly as in the Configuration section in config/sleeves.json, with the module path stated in 'Files in this repo'.
3. Wire the producers so every evaluation snapshot carries the inputs listed in 'Data inputs', plus the snapshot `now` / session date and the sleeve's served position / sleeve_state records.
4. First evaluation: call the module's `evaluate(view, ctx)`; it builds the old context from the snapshot and calls the strategy `signal(...)`. Confirm a snapshot with no qualifying signal returns no entry intents (fail-closed), then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo; the desk's port blocker tests pin the vendored strategy files by sha256):

- Check the setup math: EMA(20) seeded at the first close with k = 2/21; a session bar whose range merely touches its EMA value breaks no_touch; trend exactly 0.7686 is a trend day.
- Check fail-closed ATR: 13 daily ranges, or a non-finite range, produce no setup and no entry.
- Check direction: an armed up day (close above EMA) enters sell_to_open, an armed down day buy_to_open, never the continuation side.
- Check the entry window and weekday guard: 09:29 and 09:45 ET produce no entry, 09:30 does; a Saturday 09:35 pass produces no entry but a held position still flattens at 15:59.
- Check sizing and geometry: at equity 100,000 and ATR14 4.00, qty = int(250 // 2.00) = 125, the stop is exactly 0.5 x ATR14 from the reference and the target is the rounded EMA.
- Check the geometry gate: |ref - EMA| exactly equal to 0.5 x ATR14 is taken; one cent less is refused with the gate ON and taken with it OFF.
- Check exits are close-based and side-aware: a wick through the stop that recovers before the evaluation close produces no exit; a close at the stop does, for both long and short, before the 15:59 flatten.
