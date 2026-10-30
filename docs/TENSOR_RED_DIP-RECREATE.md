# tensor_red_dip: Recreation package

Provenance: The old Alpaca swing desk, via Femto-lean (Source row in strategies/femto/femto-tensor-red-dip.md in this repo).

## What this sleeve is
This sleeve buys Tensor swing signals on fear days: when QQQ is down at least 1.5 percent on the day, it buys confidence-7-or-better Tensor signals whose own symbol is also red (and, under the default enhancement, down at least 1.5 percent itself), risking 0.25 percent per trade against an 8 percent stop, at most 5 positions, exiting at +3 percent, -8 percent or the third trading day. Sources: desk sleeves/tensor_red_dip.py (FEAR_QQQ_PCT=-1.5, MIN_CONF=7, RISK_FRACTION=0.0025, STOP_LOSS_PCT=0.08, STRENGTH_TARGET_PCT=0.03, HOLD_DAYS=3, MAX_POSITIONS=5; CONFIG cadence_s=300, risk_pct=0.0025) and desk3/enhance26.py (tensor_red_dip exec_price_reprice gate). The Tensor engine itself runs only inside core Data's vendored canonical door; this sleeve never imports it and receives engine output as data via context.extra.

## Full algorithm
Evaluation order in desk sleeves/tensor_red_dip.py TensorRedDip.signal(bars, slice_state, context).
1. Exits first, in this precedence per held position (exit_reason): if the last close is at or above entry_px x 1.03, exit strength_target; else if at or below entry_px x 0.92, exit stop_loss; else if trading days held (weekdays minus the NYSE holidays supplied in extra[nyse_holidays], entry day = 0) reach 3, exit time_stop. Each exit is the full held quantity at the last close, reason naming tensor_red_dip exit and the rule.
2. Fear-day gate (fail closed): qqq_day_return from extra must be present; if it is None, no entries. If qqq_day_return x 100 > -1.5, it is not a fear day and there are no entries. Equity at or below 0 also blocks entries.
3. Signal filter (filter_signals): from extra[tensor_signals], keep dicts with a symbol and an integer confidence at least 7; de-dupe by symbol, first wins. No raw signals or no qualified signals means no entries.
4. Room: room = 5 - (number of held positions); if room is at or below 0, no entries.
5. Per candidate, in filtered order: skip if already held; the symbol's own day return (extra[day_returns]) must be present and below 0 (the symbol itself must be red); ENH fear-magnitude gate (default ON; OFF via extra[tensor_red_dip_improve][fear_magnitude_gate]=False restores admitting any red print): the symbol's day return must also be at or below -1.5 percent (a shallower red print is refused as dip_too_shallow); skip if the symbol has no bars.
6. Sizing and entry: price = the last bar close; qty = floor((equity x 0.0025) / (price x 0.08)), at least 1 when the floor is at least 1, else 0 (skip). Emit an enter Intent with price_hint = round(price, 2), stop = round(price x 0.92, 2), ExitRules for that stop, a target at round(price x 1.03, 2) and time_bars 3, and a reason naming the fear-day QQQ percent, confidence, phenotype and the symbol's red percent. Decrement room per entry.
7. Adapter-layer gate (desk3/enhance26.py, ENH-B26-20261024, default ON; switch extra[tensor_red_dip_improve2][exec_price_reprice]): each entry is repriced at close x (1 + day_return) (the executable intraday estimate) and quantity, stop and target are re-derived from that price with the sleeve's own 0.25 percent / 8 percent rule. Exits are never filtered. Every evaluation also stamps telemetry (QQQ return vs the gate, signals seen and qualified, and the reason no entry was emitted when silent).

## Files in this repo
- Sleeve module: sleeves/tensor_red_dip.py (strategy logic and CONFIG).
- v3 adapter: adapters3/tensor_red_dip.py (SLEEVE_ID=tensor_red_dip; evaluate(view, ctx) rebuilds the v2 SleeveContext via adapters3/_snapshot_ctx.SnapshotSleeveContext, delegates to adapters/tensor_red_dip.py, then applies desk3/enhance26.filter_entries; the _snapshot_ctx glue itself is not in this repo at its canonical path, as the audit record notes).
- v2 adapter mirror: integration/tensor_red_dip_adapter.py in this repo (the adapters/tensor_red_dip.py evaluate it mirrors).
- Shared engine file: engines/desk3/enhance26.py (desk desk3/enhance26.py: ENH-B26-20261024 adapter-layer gates, default ON per sleeve).
- Existing strategy doc: strategies/femto/femto-tensor-red-dip.md.
- Config: engines/config/sleeves.json (row id=tensor_red_dip), also at config/sleeves.json.

## Configuration
Module adapters3.tensor_red_dip; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, tensor]; parked false. Universe: symbols carried by fresh Tensor swing signals in the snapshot (the existing doc names the 41-name old-desk basket as the signal universe); timeframe intraday with 1h Tensor signals. Source: muse-desk-v3/config/sleeves.json row id=tensor_red_dip.

## Data inputs
Inputs are bars and tensor. Via context.extra the sleeve consumes: tensor_signals [{symbol, decision, confidence, phenotype}] (engine output via core Data only, already in read_fresh_signals shape), qqq_day_return (fraction; None fails closed), day_returns {SYM: fraction}, nyse_holidays [YYYY-MM-DD] (core Data calendar product) and sleeve_state {SYM: {position {entry_px, entry_date, qty}}}. Bars give the last close per symbol for exits and entry pricing.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `tensor_red_dip` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/tensor_red_dip.py, whose evaluate(view, ctx) delegates to adapters/tensor_red_dip.py, which runs sleeves/tensor_red_dip.py signal(bars, slice_state, context), after which desk3/enhance26.filter_entries is applied.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with QQQ day return -0.02, a Tensor signal at confidence 7 whose symbol's day return is -0.02, no held positions and bars present: exactly one entry, qty floor((equity x 0.0025) / (price x 0.08)) at the last close before the adapter reprice, stop round(price x 0.92, 2), target round(price x 1.03, 2).
- Fixture with QQQ day return -0.01, or qqq_day_return missing, or the symbol's day return -0.005 under the default fear-magnitude gate: no entry.
- Fixture with a held position whose last close is at or above entry x 1.03: a full strength_target exit (checked before the stop and time rules); at or below entry x 0.92: a stop_loss exit; on the third trading day after entry with neither price rule hit: a time_stop exit.
- Fixture with 5 positions held: no entries regardless of signals.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
