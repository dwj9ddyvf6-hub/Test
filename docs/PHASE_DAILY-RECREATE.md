# phase_daily: Recreation package

Provenance: Source row in strategies/femto/femto-phase-daily.md in this repo: Milkman Trades' Daily Bilbo Boxes, via the old Alpaca swing desk and Femto-lean.

## What this sleeve is
This is a daily compression-breakout equity sleeve: it finds multi-day volatility-compression boxes on daily bars, buys a break of the box high under a K5 trigger rule with the box low as the stop, and then trails the stop up with the 50-day EMA. An enhancement arm flattens a held position ahead of its earnings print and re-enters after it. Sources: sleeves/phase_daily.py and desk3/port_b5/phase_daily.py on the desk.

## Full algorithm
Constants (sleeves/phase_daily.py): BOX_DAYS 5, K5_WINDOW_BARS 20, RISK_FRACTION 0.0025, MAX_POSITIONS 10, NOTIONAL_CAP 0.25, FLATTEN_ARM_HM 15:55 ET. CONFIG: cadence_s 300, universe (), risk_pct 0.0025. At least 60 daily bars are required per symbol.
Compression (phase_compression_daily): a day is grey (compression) when the 21-period Bollinger band (EMA21 pivot plus/minus 2 x rolling sample stdev of closes, 21) sits inside the 2 x ATR14 Keltner band, except when the band gap is not shrinking and price is already inside the 1.854 x ATR expansion zone.
Box (detect_episodes): the box is the high and low of the FIRST 5 grey days (fewer when the squeeze ends early, locking at the close of the first non-grey day).
Evaluation order in signal(), per symbol (universe override, else the bars keys):
1. Held position: trail = the EMA50 ratchet recomputed from the bars since entry (each day's candidate is the prior bar's EMA50, never down, floored at the stored trail and the recorded initial stop). Exit the full qty when the last close is below the trail.
2. Earnings flatten (ENH arm, switch context.extra["phase_daily_enhance"]["earnings_flatten_arm"], default ON): when the position's next earnings print falls on the coming session, exit the whole position at the 15:55 ET evaluation of the flatten session (the earnings session itself for an after-hours print, otherwise the last served session before the earnings date), booking the surviving box/trail record for re-entry. A stale or unserved calendar fails the arm closed (the position rides through). After the print, re-enter at the first post-print session's close at the flattened qty under the surviving trail, unless that close is below the trail, in which case the name stays flat.
3. Entry (K5): only for the latest episode, and only once per episode (episode_key). Within 20 trading days after the box locks, the first bar whose high reaches the box high, gated on the prior close being above the daily EMA21, is the trigger, and only when it is the last bar; a box-low touch before that kills the trade. Initial stop = box low. Quantity = floor(equity x 0.0025 / (box high - box low)), capped at floor(equity x 0.25 / box high); quantity below 1 skips, with no 1-share floor. At most 10 open positions.

## Files in this repo
- Strategy module (desk sleeves/phase_daily.py, the strategy logic; CONFIG sleeve_id=phase_daily): the desk module path is sleeves/phase_daily.py.
- v3 wrapper (desk desk3/port_b5/phase_daily.py): `desk3/port_b5/phase_daily.py` in this repo (also copied at sleeves/phase_daily.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/phase_daily_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=phase_daily); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.phase_daily; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars', 'positions', 'earnings', 'journal']; parked false. Source: muse-desk-v3/config/sleeves.json row id=phase_daily (repo copy: engines/config/sleeves.json).

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending) for the universe; sleeve_state {SYM: {position: {entry_px, entry_date, qty, trail}, episode_key, earnings_flat}}; earnings, earnings_time ({SYM: 'pre'|'after'|None}) and earnings_fresh, served by the adapter from the warm-time earnings producer's cache (Nasdaq calendar, produced by runtime/earnings_warm.py); equity from the slice.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `phase_daily` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check box formation: five grey days lock a box at their high/low; an early squeeze end locks at the first non-grey close.
- Check the K5 trigger: a high reaching the box high with the prior close at or below EMA21 does not trigger; a box-low touch before the trigger kills the episode; a trigger after 20 trading days does not fire.
- Check sizing and stop: qty equals floor(equity x 0.0025 / box range) capped at 25 percent notional, and the entry stop equals the box low.
- Check the trail exit: a close below the ratcheted EMA50 trail exits; the trail never moves down.
- Check the earnings arm: with the arm ON and a fresh calendar, a position flattens at the 15:55 evaluation ahead of its print and re-enters after it above the trail; with a stale calendar it rides through.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
