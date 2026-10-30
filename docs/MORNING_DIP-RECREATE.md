# morning_dip: Recreation package

Provenance: Source row in strategies/femto/femto-morning-dip.md in this repo: Milkman Trades' Morning Dip Limit, via the old Alpaca swing desk and Femto-lean; also the Milkman v2 study.

## What this sleeve is
This is a single-symbol intraday sleeve on QQQ: on 3-minute candles inside the 10:00 to 12:00 ET window, when the morning is directionally efficient it rests a buy limit one tick below a level one ATR under the signal close, with the signal candle midpoint as target. It holds at most one position and is flat at 12:00 ET. Sources: sleeves/morning_dip.py and desk3/port_b5/morning_dip.py (the wrapper passes a 180-second 3-minute timeframe hint) on the desk.

## Full algorithm
Constants (sleeves/morning_dip.py): SYMBOL QQQ, RISK_FRACTION 0.0025, TICK 0.01, WINDOW_START 10:00 ET, WINDOW_END 12:00 ET, ARM_CANCEL_MIN 9, TIME_STOP_MIN 15, ER_MAX 0.35, ATR_LEN 14, ER_CANDLES 15. CONFIG: cadence_s 180, universe (QQQ,), risk_pct 0.0025.
Evaluation order in signal():
1. Held position first: read the position's own stop and target from its recorded exit_rules (stop_px fallback). On the last 3-minute close, exit the full qty when the close is at or below the stop, else at or above the target, else when at least 15 minutes have elapsed since the first fill (fill_t; legacy records fall back to entry_t). If none fires and the time is at or after 12:00 ET, exit flat at window end.
2. No position: outside the 10:00-12:00 ET window, emit nothing.
3. Indicators on closed 3-minute candles arriving via context.extra["candles_3min"]: need at least 16 candles and all of the last 16 healthy, else no signal. ATR is the simple mean of the last 14 true ranges; ER (efficiency ratio) over the last 16 candles is |close[-1] - close[0]| divided by the sum of absolute close-to-close moves (1.0 when the denominator is 0).
4. ER gate: ER above 0.35 does not arm (only a clean directional morning arms).
5. Arm plan (arm_plan, verbatim): level = floor to the tick of (signal close - 1.0 x ATR); refuse when the close is less than 1 tick above the level. Reward = ceil to the tick of (signal candle midpoint (h+l)/2 - level); refuse when reward is under 2 ticks. Target = level + reward; limit = level - 1 tick; stop distance = max(4 ticks, ceil(1.5 x ATR to the tick)); stop = limit - stop distance. Quantity = floor(equity x 0.0025 / stop distance); below 1 refuses. Refuse when target <= limit.
6. Enhancement gate (switch context.extra["morning_dip_improve"]["rr_geometry_gate"], default ON): refuse the arm when (target - limit) is smaller than (limit - stop), that is reward-to-risk below 1 on the plan's own values.
7. Entry intent: buy limit at the plan limit, qty as above, with ExitRule stop and ExitRule target; the reason names the 9-minute unfilled cancel and the 15-minute time stop, which are core timers. The sleeve emits the unclamped strategy quantity; the desk cap clamp is core Risk's.

## Files in this repo
- Strategy module (desk sleeves/morning_dip.py, the strategy logic; CONFIG sleeve_id=morning_dip): the desk module path is sleeves/morning_dip.py.
- v3 wrapper (desk desk3/port_b5/morning_dip.py): `desk3/port_b5/morning_dip.py` in this repo (also copied at sleeves/morning_dip.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/morning_dip_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored) and `engines/desk3/port_b5/_enh2.py` (desk desk3/port_b5/_enh2.py, vendored; the ENH2 experiment layer this wrapper runs through).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=morning_dip); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.morning_dip; cadence_s 180; session rth; slice capital_usd 20000.0, cash_usd 20000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars', 'positions']; parked false. Source: muse-desk-v3/config/sleeves.json row id=morning_dip (repo copy: engines/config/sleeves.json).

## Data inputs
Closed 3-minute QQQ candle dicts {t, o, h, l, c, healthy} via context.extra["candles_3min"] (a core Data product); sleeve_state {QQQ: {position}} from the desk's position records; the bars argument is unused for the signal; equity from the slice; evaluation time from context.now (ET window checks).

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `morning_dip` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the window: a qualifying signal at 09:57 ET or at 12:00 ET produces no arm; at 10:00 ET it does.
- Check the ER gate: ER of 0.36 produces no arm; ER of 0.35 arms (subject to the plan rules).
- Check the plan math on a fixture candle: level, limit (level - 0.01), target (level + reward), stop distance max(0.04, ceil(1.5 x ATR)) and qty floor(equity x 0.0025 / stop distance) match the formulas above; a plan with reward under 2 ticks or reward-to-risk below 1 (gate ON) is refused.
- Check exits: a held position exits on its recorded stop, on its target, at 15 minutes from fill_t, and flat at 12:00 ET, in that order.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
