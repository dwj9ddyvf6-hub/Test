# s_q07w_s78_ml_deep70_glow_ins2: Recreation package

Provenance: research lab (Q07 confluence cells), run by Lazarus (Source row in strategies/lazarus/lz-q07.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Q07 fire-consumer sleeve in the swing family, midlarge band, with a 78-week horizon and the filters deep70, glow, ins2. It buys one $1,000 slot only on a QQQ-down day within the fire window that passes every named filter, and exits on a 15 percent stop or at the horizon. The roster row is parked, so the dispatcher skips entries while parked. Sources: desk laz_sleeves/s_q07w_s78_ml_deep70_glow_ins2.py and laz_sleeves/_common.py q07_evaluate.

## Full algorithm
This sleeve is a v3-native module: laz_sleeves/<id>.py evaluate(view, ctx) calls q07_evaluate(view, ctx, SLEEVE_ID, band="midlarge", horizon_weeks=78, filters=('deep70', 'glow', 'ins2'), slots=1, slot_usd=1000.0) in laz_sleeves/_common.py. Module header (desk laz_sleeves/<id>.py): Lazarus Q07 swing lane, v3-native build. Catalog rule (section 4.1 family rule + lane row): Tensor 1W Swing signal, midlarge band, filters (deep70, glow, ins2); buy only on a QQQ-down day within 5 sessions of the signal; exit 15% stop or 78-week horizon. Source status Disabled, so parked in v3 config (evaluates, dispatcher skips entries while parked). Fires arrive via the desk Tensor bundle producer (ledger substitution LAZ-B7).

Evaluation order in laz_sleeves/_common.py q07_evaluate():
1. Session: sess is the date from view now; if it cannot be parsed, return no intents.
2. Exits, for each of this sleeve's non-zero positions (a position with another sleeve_id is ignored; bars are view bars under <sym>|1Day, and a position with no bars is skipped): last is the last daily close, entry is avg_price. If entry above 0 and last at or below entry times 0.85, emit a full-qty market day exit dict, reason q07_stop15. Else if sessions held (daily bars strictly after opened_at) are at least horizon_weeks times 5 = 390, emit a full-qty exit, reason q07_time_horizon.
3. Entry gates: if the number held is at least slots=1, or QQQ is not down (QQQ bars under QQQ|1Day, at least 2 rows, last close below prior close), return only the exits.
4. Fires are read from view tensor_fires, a dict {symbol: {family, date}} visited in sorted symbol order, skipping held symbols. A fire is skipped if its family is not exactly "swing", its date cannot be parsed, or its calendar age (sess minus fire date, in days) is below 0 or above 7 (the code comment states this window as within 5 sessions of the signal).
5. Alt-data band gate: alt_data[symbol] mcap_band must equal "midlarge" exactly, otherwise the fire is skipped. The symbol needs daily bars under <sym>|1Day.
6. Filters, all must pass (each reads alt_data[symbol] tags or the daily bars): deep70: as coded in laz_sleeves/_common.py, the last close is at or below 0.30 times the maximum high over the last 252 daily bars (highs list must be non-empty); glow: alt_data gamma_low is exactly True; ins2: int(alt_data insider_buys or 0) is at least 2.
7. Stale-bar gate (ENH24-LAZB7-Q07STALE-20261024, default ON; OFF via extra <id>_enh24 stale_gate=False): refuse the entry when the symbol's last bar date is more than 4 calendar days before the session, with a paired record to extra enh24_journal when that journal is a list. Exits are never gated.
8. Sizing and intent: qty = int(1000.0 // last); qty at or below 0 is skipped. Emit one market, day entry dict with price_hint = last and reason "q07_deep70_glow_ins2". Slot guard (ENH-Q07SLOT-20261024, default ON via extra <id>_enh23 slot_guard): stop after the entry that makes held plus entries emitted reach slots=1.

## Files in this repo
- Sleeve module (desk laz_sleeves/s_q07w_s78_ml_deep70_glow_ins2.py): laz_sleeves/s_q07w_s78_ml_deep70_glow_ins2.py; also present as sleeves/lazarus/s_q07w_s78_ml_deep70_glow_ins2.py and integration/s_q07w_s78_ml_deep70_glow_ins2_adapter.py.
- Shared engine (desk laz_sleeves/_common.py, q07_evaluate and its helpers _session, _bars, _positions, _sessions_held, _intent, _qty_for, _qqq_down, _mom6, _bar_stale): engines/laz_sleeves/_common.py in engines_map.json with status gate_blocked, so that exact repo copy is not present and must be taken from the desk source tree.
- Existing strategy doc: strategies/lazarus/lz-q07.md. No per-sleeve ALGORITHM doc is present in this repo for this sleeve (checked at batch start); the Full algorithm section in this package is derived directly from laz_sleeves/_common.py and the module as cited there.
- Config: engines/config/sleeves.json (row id=s_q07w_s78_ml_deep70_glow_ins2), also at config/sleeves.json.

## Configuration
Module laz_sleeves.s_q07w_s78_ml_deep70_glow_ins2; cadence_s 86400; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars_1day, positions, tensor_fires, alt_data, vix]; parked true. Universe: symbols carried by Tensor fires in the swing family whose alt_data mcap_band equals midlarge; timeframe 1W (weekly fires, 1Day bars). Source: muse-desk-v3/config/sleeves.json row id=s_q07w_s78_ml_deep70_glow_ins2.

## Data inputs
Inputs are bars_1day, positions, tensor_fires, alt_data and vix (the module INPUTS tuple). tensor_fires is view tensor_fires {symbol: {family, date}}, the desk Tensor bundle producer output (the shared engine header records it as the substitution for the unreachable composer fire file, ledger LAZ-B7); alt_data is view alt_data {symbol: {insider_buys, wiki, gamma_low, ats_z, mcap_band}}; bars are view bars under <sym>|1Day with t, h, c including QQQ; positions rows carry symbol, qty, avg_price, opened_at and sleeve_id; vix is declared as an input although q07_evaluate reads it only for a vix20 filter, which this sleeve does not carry. No fresh fires means no entry.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/laz_sleeves/_common.py is laz_sleeves/_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_q07w_s78_ml_deep70_glow_ins2` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the module laz_sleeves/s_q07w_s78_ml_deep70_glow_ins2.py, whose evaluate(view, ctx) calls laz_sleeves._common.q07_evaluate with this sleeve's band, horizon and filters.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture on a QQQ-down day with a swing fire aged 0 to 7 calendar days, alt_data mcap_band equal to midlarge, fresh daily bars, and every filter (deep70, glow, ins2) passing, with nothing held: exactly one entry dict, qty int(1000.0 // last close), reason q07_deep70_glow_ins2 (subject to the roster parked state at the dispatcher).
- Fixture on a day that is not QQQ-down, with a non-swing family, a mismatched mcap_band, a fire aged above 7 days, or any one named filter failing: no entry.
- Fixture with a held position whose last close is at or below avg_price times 0.85: exactly one exit for the full quantity, reason q07_stop15.
- Fixture with a held position held for at least 390 sessions (bars strictly after opened_at) and no stop hit: exactly one exit, reason q07_time_horizon.
- Fixture whose entry symbol's last bar is more than 4 calendar days before the session: no entry (ENH24 stale gate) and a journal record when enh24_journal is a list; an exit in the same state is still emitted.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
