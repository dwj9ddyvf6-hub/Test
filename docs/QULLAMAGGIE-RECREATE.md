# qullamaggie: Recreation package

Provenance: Source row in strategies/qullamaggie/qm-leader-breakout.md in this repo: Kristjan Kullamägi (Qullamaggie), "My 3 timeless setups"; three desk implementations.

## What this sleeve is
This is a daily leader-breakout equity sleeve over the genome universe: names in the top 2 percent of trailing returns that have impulsed at least 30 percent and based tightly for 10 sessions are staged for entry only when the desk's intraday core supplies a 5-minute opening-range trigger. It scales out a third after 3 profitable days and trails the rest against the 10-day (or 20-day when extended) moving average. Sources: sleeves/qullamaggie.py and desk3/port_b5/qullamaggie.py on the desk.

## Full algorithm
Constants (sleeves/qullamaggie.py): RISK_FRACTION 0.0035, MAX_NAME_NOTIONAL_PCT 0.20, MAX_ADV_PARTICIPATION 0.01, MAX_POSITIONS 10, LEADER_PCT 0.98, LEADER_HORIZONS (21, 63, 126), IMPULSE_MIN 0.30, BASE_WINDOW 10, BASE_WIDTH_MAX 0.28, TIGHTENING_MAX 1.0, LOW_SLOPE_MIN 0.0, MA_SUPPORT_MIN 0.70, MA_TOL 0.97, OR_MINUTES 5, MAX_STOP_ATR 1.0, ADV_MIN 5,000,000 (20-day dollar ADV), SCALE_DAYS 3, SCALE_FRACTION 1/3, TRAIL_HELD_MIN 3, EXTENSION_ATR 1.5, GAP_QUANTILE 0.95, SLIP_BPS 2.0, COMM_BPS 1.0. CONFIG: cadence_s 1800, universe (), risk_pct 0.0035.
Evaluation order in signal():
1. Manage held positions first (exits never gated; at least 20 bars required): exit the full qty when the last close is below the position's stop (the recorded stop, with the stop_px fallback). Else, once only, sell 1/3 (at least 1 share, qty at least 3 required) when held at least 3 sessions and the close is above entry; the residual stop moves to breakeven. Else exit the full qty when held at least 3 sessions and the close is below the trail average: SMA10, or SMA20 when the name is extended more than 1.5 x ATR(20) above SMA10.
2. Leader screen: trailing returns over 21, 63 and 126 sessions for every non-held symbol; a leader's maximum tie-aware percentile rank across the horizons is at least 0.98. Leaders are considered in descending leader score, symbol tiebreak.
3. Setup (compute_features): impulse = max high of the last 63 sessions / close 64 sessions back - 1, at least 0.30; a 10-session base with width (max high - min low) / last close at most 0.28; late-half range tightening ratio at most 1.0; slope of base lows at least 0; at least 70 percent of base closes at or above 0.97 x SMA10 or 0.97 x SMA20; SMA10 and SMA20 rising versus 3 bars ago; 20-day dollar ADV at least $5,000,000.
4. Trigger: entries stage only from a core-supplied intraday trigger in context.extra["trigger"] {SYM: {entry_px, stop, minute}} (the 5-minute opening range; trigger = max(OR high, pivot); the strategy file does not compute it and stages nothing without it, fail closed). Refuse when entry_px <= stop, or when entry - stop exceeds 1.0 x ATR(20).
5. Sizing: 0.35 percent of equity risk on the stressed loss per share (stop distance + 95th-percentile adverse overnight gap + 2 bp slippage + 1 bp commission), capped at 20 percent name notional and 1 percent of ADV participation. At most 10 positions.

## Files in this repo
- Strategy module (desk sleeves/qullamaggie.py, the strategy logic; CONFIG sleeve_id=qullamaggie): the desk module path is sleeves/qullamaggie.py.
- v3 wrapper (desk desk3/port_b5/qullamaggie.py): `desk3/port_b5/qullamaggie.py` in this repo (also copied at sleeves/qullamaggie.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/qullamaggie_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored) and `engines/desk3/port_b5/_enh2.py` (desk desk3/port_b5/_enh2.py, vendored; the ENH2 experiment layer this wrapper runs through).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=qullamaggie); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.qullamaggie; cadence_s 1800; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars', 'positions']; parked false. Source: muse-desk-v3/config/sleeves.json row id=qullamaggie (repo copy: engines/config/sleeves.json).

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending) for the genome universe; sleeve_state {SYM: {position: {entry_px, entry_date, qty, stop, scaled_third}}}; the core-supplied intraday trigger {SYM: {entry_px, stop, minute}} via context.extra["trigger"]; equity from the slice.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `qullamaggie` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the leader screen: a name below the 0.98 maximum percentile in all three horizons is not considered, however strong its base.
- Check the setup: impulse of 0.29, base width of 0.29, and 20-day ADV of $4,900,000 each fail; a name passing all setup rules but with no core trigger stages no entry.
- Check the stop width: a trigger whose entry - stop exceeds 1.0 x ATR(20) is skipped.
- Check management: a close below the recorded stop exits in full; at 3 or more held sessions and profitable, exactly one 1/3 scale fires (never twice); a close below the trail average after 3 sessions exits the residual.
- Check caps: the 11th position is refused and sizing never exceeds 20 percent name notional or 1 percent of ADV.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
