# momentum_rotation: Recreation package

Provenance: Source row in strategies/femto/femto-momentum-rotation.md in this repo: The old Alpaca swing desk, via Femto-lean.

## What this sleeve is
This is a weekly momentum-rotation equity sleeve: it ranks its universe by 60-day total return, holds the top 5 at 20 percent equal weight, and sells held names that fall out of the top 10 at the weekly rebalance. A 2026-10-23 improvement buys a top-5 name only when its 60-day momentum is strictly positive. Sources: sleeves/momentum_rotation.py and desk3/port_b5/momentum_rotation.py on the desk.

## Full algorithm
Constants (sleeves/momentum_rotation.py): MOMENTUM_DAYS 60, TOP_HOLD 5, SELL_RANK_CUTOFF 10, REBALANCE_DAYS 7, TARGET_WEIGHT 0.20, DISASTER_STOP 0.25, WARMUP_BARS 65 (60+5). CONFIG: cadence_s 300, universe (), state_schema {position, meta.last_rebalance}, risk_pct None.
Evaluation order in signal():
1. Stamp the experiment journal first (adopted from context.extra only on exp_id + version + fingerprint match for EXP_ID IMP3-MOMROT-20261023); if equity <= 0, return no intents.
2. Rebalance gate: do nothing unless rebalance_due(last_rebalance, today): no last_rebalance, an unparseable date, or at least 7 calendar days since the last rebalance.
3. Ranks: compute_ranks over daily bars: momentum_60d = close[-1] / close[-61] - 1 (None with fewer than 61 bars or a non-positive base close); rank 1 is the highest momentum.
4. Sells first, for every booked holding (ranked or not): disaster stop first (last close <= entry_px x 0.75), then any holding whose rank is worse than 10 or which is unranked, exited at the last close.
5. Buys: the top 5 by rank, computed once (rank 6 and below are never promoted), skipping held names. Absolute-momentum floor (switch context.extra["momentum_rotation_improve"]["abs_mom_floor"], default ON): a top-5 name with mom60 <= 0 is refused and its slot stays cash, with no renormalisation of the others. Quantity = floor(equity x 0.20 / last close); quantity below 1 skips. Entry intent carries a disaster stop at entry x 0.75 as its only ExitRule.
6. Each due rebalance also records a selection cohort and two return-space books in the experiment journal: a control book running the pre-change rule (no floor) and a treatment book running the floor.

## Files in this repo
- Strategy module (desk sleeves/momentum_rotation.py, the strategy logic; CONFIG sleeve_id=momentum_rotation): the desk module path is sleeves/momentum_rotation.py.
- v3 wrapper (desk desk3/port_b5/momentum_rotation.py): `desk3/port_b5/momentum_rotation.py` in this repo (also copied at sleeves/momentum_rotation.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/momentum_rotation_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored) and `engines/desk3/port_b5/_enh2.py` (desk desk3/port_b5/_enh2.py, vendored; the ENH2 experiment layer this wrapper runs through).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=momentum_rotation); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.momentum_rotation; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars', 'positions', 'journal']; parked false. Source: muse-desk-v3/config/sleeves.json row id=momentum_rotation (repo copy: engines/config/sleeves.json).

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending) for the universe symbols (context.extra universe override, else the bars keys); sleeve_state {SYM: {position: {entry_px, entry_date, qty}}} and last_rebalance (extra or extra.meta) from the desk's persisted sleeve state; equity from the slice; the momentum_rotation_exp_journal served back by core. No data is fetched during evaluation.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `momentum_rotation` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the rebalance gate: a pass 6 calendar days after the last rebalance emits nothing; at 7 days it rebalances.
- Check ranks and sells: a holding ranked 11 or unranked is sold, a holding at rank 10 is kept, and a holding whose close is at or below 0.75 x entry is sold first by the disaster stop.
- Check the floor: with the floor ON a top-5 name with mom60 of exactly 0.0 is refused and rank 6 is not promoted; with the switch OFF that name is bought.
- Check sizing: a bought name gets floor(equity x 0.20 / close) shares and a stop at 0.75 x entry.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
