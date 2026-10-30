# s_q07w_s52_ml_ins2_mom6_vix20: Recreation package

Provenance: research lab (Q07 confluence cells), run by Lazarus (Source row in strategies/lazarus/lz-q07.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Q07 fire-consumer sleeve in the swing family, midlarge band, with a 52-week horizon, the filters ins2, mom6, vix20, and 2 slot(s) at $1,000 per slot. It buys only on a QQQ-down day within 5 sessions of a Tensor 1W swing fire that passes every named filter, and exits on a 15 percent stop or at the horizon. Sources: desk laz_sleeves/s_q07w_s52_ml_ins2_mom6_vix20.py and laz_sleeves/_common.py q07_evaluate.

## Full algorithm
This sleeve is a module in laz_sleeves/: laz_sleeves/<id>.py evaluate(view, ctx) calls laz_sleeves/_common.py q07_evaluate(view, ctx, SLEEVE_ID, band="midlarge", horizon_weeks=52, filters=(ins2, mom6, vix20), slots=2, slot_usd=1000.0). Module note (desk laz_sleeves/<id>.py): Tensor 1W Swing signal, midlarge band, filters ('ins2', 'mom6', 'vix20'); buy only on a QQQ-down day within 5 sessions of the signal; exit 15% stop or 52-week horizon. Source status Disabled -> parked in v3 config (evaluates, dispatcher skips entries while parked). Fires arrive via the desk Tensor bundle producer (ledger substitution LAZ-B7).

Inputs declared in the module: bars_1day, positions, tensor_fires, alt_data, vix.

Evaluation order in laz_sleeves/_common.py q07_evaluate():
1. Session: the session date is parsed from view now (first 10 characters); if it does not parse, return no intents.
2. Exits first, over this sleeve's own positions only (positions whose sleeve_id is absent or equal to this sleeve, qty non-zero). For each held symbol with daily bars (view bars key "<sym>|1Day"): last is the last bar close and entry is avg_price. If entry is above 0 and last is at or below entry times 0.85, emit an exit for the full absolute quantity at that price, reason "q07_stop15". Else, if the sessions held (daily bars dated strictly after opened_at) reach horizon_weeks times 5 = 260 sessions, emit an exit for the full quantity, reason "q07_time_horizon". Exits are intent dicts: kind exit, side sell, order_type market, time_in_force day, price_hint equal to last, intent_id "<sid>-<sym>-<session>-exit".
3. Entries are refused when the number of held positions is at least slots=2, or when QQQ is not down (QQQ 1Day bars: at least 2 bars and the last close below the prior close).
4. Fires are read from view tensor_fires, a dict keyed by symbol, iterated in sorted symbol order. A fire is skipped if its symbol is held, its family is not exactly "swing", its date does not parse, or its calendar age in days is below 0 or above 7 (the code's reading of "within 5 sessions of the signal").
5. Alt-data tags are read from view alt_data for the symbol. A fire is skipped when tags mcap_band is not exactly "midlarge".
6. The symbol must have daily bars. Filters, all must pass: ins2: int(tags insider_buys or 0) is at least 2, read from view alt_data for the symbol; mom6: _mom6(closes) is not None and above 0, where _mom6 needs at least 127 closes and returns last close / close 126 sessions back minus 1; vix20: view vix is present and at least 20.0.
7. Stale-bar refusal (ENH24-LAZB7-Q07STALE-20261024, default ON; OFF via extra["<id>_enh24"]["stale_gate"]=False): refuse the entry when the symbol's last daily bar is more than 4 calendar days before the session (a Monday-after-Friday bar at 3 days and a Tuesday-after-Monday-holiday bar at 4 days both pass). Exits are never gated by this check.
8. Sizing: qty = int(1000.0 // last close); qty at or below 0 emits nothing. Emit an entry intent dict: kind entry, side buy, order_type market, time_in_force day, price_hint equal to the last close, reason "q07_" plus the filters joined by underscores ("q07_ins2_mom6_vix20"), intent_id "<sid>-<sym>-<session>-entry".
9. Slot guard (ENH-Q07SLOT-20261024, default ON; OFF via extra["<id>_enh23"]["slot_guard"]=False): stop after entries emitted this pass plus held positions reach slots=2; the pre-change OFF rule breaks on the fixed held count instead.

## Files in this repo
- Sleeve module: laz_sleeves/s_q07w_s52_ml_ins2_mom6_vix20.py (SLEEVE_ID=s_q07w_s52_ml_ins2_mom6_vix20; INPUTS declared in the module; evaluate(view, ctx) calls laz_sleeves._common.q07_evaluate with band, horizon, filters, slots and slot_usd as given in the Full algorithm section). The same module is also present in this repo under sleeves/lazarus/s_q07w_s52_ml_ins2_mom6_vix20.py per the audit record.
- Shared engine file: engines/laz_sleeves/_common.py (desk laz_sleeves/_common.py: q07_evaluate and its helpers). Recorded gap: in engines_map.json this file's vendoring status is gate_blocked, and it is absent from the fresh repo tree taken at batch start; the Full algorithm section in this package states its q07_evaluate rules in full so the engine can be recreated from this package.
- Existing strategy doc: strategies/lazarus/lz-q07.md (shared family card; it does not state this sleeve's own parameters, which are stated here from the desk module). No per-sleeve ALGORITHM doc exists in this repo for this sleeve (checked at batch start).
- Config: engines/config/sleeves.json (row id=s_q07w_s52_ml_ins2_mom6_vix20), also at config/sleeves.json.

## Configuration
Module laz_sleeves.s_q07w_s52_ml_ins2_mom6_vix20; cadence_s 86400; session rth; slice capital_usd 1984.0, cash_usd 1984.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars_1day, positions, tensor_fires, alt_data, vix]; parked true. Universe: Tensor 1W swing fires whose alt_data mcap_band is midlarge and that pass the named filters; timeframe 1W signals on 1Day bars. Sizing note: the module calls q07_evaluate with slots=2 and slot_usd=1000.0, while the roster slice is 1984.0; both values are recorded as found. Source: muse-desk-v3/config/sleeves.json row id=s_q07w_s52_ml_ins2_mom6_vix20 and desk laz_sleeves/s_q07w_s52_ml_ins2_mom6_vix20.py.

## Data inputs
Inputs are bars_1day, positions, tensor_fires, alt_data and vix, as declared in the module. tensor_fires is the desk Tensor bundle producer output, a dict {SYM: {family, date}} substituting for the sleeve_fires composer file; alt_data is {SYM: {insider_buys, wiki, gamma_low, ats_z, mcap_band}}; bars are in view bars under "<sym>|1Day" with t and c (QQQ 1Day bars drive the QQQ-down gate); vix is a float (^VIX close); positions carry symbol, qty, avg_price, opened_at and sleeve_id. No fresh fires means no entry, and a filter with no evidence fails closed.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (a desk3/ path is the same path on a fresh desk; an engines/ path maps back to the desk path after engines/). The laz_sleeves/_common.py gap recorded under Files in this repo must be closed by recreating that engine from the Full algorithm section; do not substitute a different Q07 engine, because its filter readings differ (for example its deep70 and age rules are not used here, and its mom6 and wlow readings are as stated above).
2. Register the config row for `s_q07w_s52_ml_ins2_mom6_vix20` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the module laz_sleeves/s_q07w_s52_ml_ins2_mom6_vix20.py, whose evaluate(view, ctx) calls laz_sleeves._common.q07_evaluate(view, ctx, SLEEVE_ID, band="midlarge", horizon_weeks=52, filters=('ins2', 'mom6', 'vix20'), slots=2, slot_usd=1000.0). Respect the parked true roster state in step 5 below.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture on a QQQ-down day with a swing tensor fire dated 0 to 7 calendar days before the session, alt_data mcap_band midlarge, every filter (ins2, mom6, vix20) passing, a fresh last daily bar (at most 4 calendar days old) and no held positions: entry intents are computed with qty int(1000.0 // last close) and reason q07_ins2_mom6_vix20, up to 2 entries — subject to the roster parked state (parked true: the dispatcher skips entries while parked, exits still managed).
- Fixture on a day that is not QQQ-down, or with family not exactly swing, or mcap_band not midlarge, or any one named filter failing, or the fire dated more than 7 calendar days back, or the symbol's last bar more than 4 calendar days old: no entry.
- Fixture with a held position (this sleeve's sleeve_id) whose last close is at or below avg_price times 0.85: exactly one exit dict for the full quantity, reason q07_stop15.
- Fixture with a held position held for at least 260 sessions in its daily bars and no stop hit: exactly one exit dict, reason q07_time_horizon.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
