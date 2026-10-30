# s_q07w_s78_ml_deep70_ins2_vix20: Recreation package

Provenance: research lab (Q07 confluence cells), run by Lazarus (Source row in strategies/lazarus/lz-q07.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Q07 fire-consumer sleeve in the swing family, ml cap band, with a 78-week horizon and the filters deep70, ins2, vix20. It buys one $1,000 slot only on a QQQ-down day within 5 sessions of a Tensor 1W fire that passes every named filter, and exits on a 15 percent stop or at the horizon. The roster row is parked, so entries stay disabled at the desk level while the engine rules below define the sleeve. Sources: desk adapters3/s_q07w_s78_ml_deep70_ins2_vix20.py (its own SPEC) and desk3/q07_engine.py.

## Full algorithm
This sleeve's adapter carries its own SPEC and delegates to desk3/q07_engine.py evaluate_q07(SPEC, view, ctx). Adapter note (desk adapters3/<id>.py): Lazarus Q07 alt-data confluence lane (batch 6, authored for v3; no v2 source exists). Catalog section 4.1: Tensor 1W swing signal, ml cap band, filters (deep70, ins2, vix20); buy only on a QQQ-down day within 5 sessions of the signal; exit on a 15% stop or at the 78-week horizon; 1 slot at $1,000. CSV status: sleeve_feed composer (tracker ledger + alt-data tags). Logic lives in desk3/q07_engine.py.

SPEC (in the adapter module): id=<id>, family="swing", horizon_wk=78, band="ml", filters=('deep70', 'ins2', 'vix20'). Engine constants (desk3/q07_engine.py): SLOT_USD=1000.0, STOP_PCT=0.15, MAX_SIGNAL_AGE_SESSIONS=5, MOM6_SESSIONS=126, DEEP70_HIGH_SESSIONS=252. Inputs: sleeve_fires, bars_1day, vix, positions. The engine imports desk3/contract.py (ExitRule, Intent).

Evaluation order in desk3/q07_engine.py evaluate_q07():
1. Exits first. For each held position (qty above 0): avg is avg_price, px is the last close from bars under the key <sym>|1day. If avg above 0 and px exists and px is at or below avg times (1 - 0.15), the exit reason is q07_stop15. Otherwise, if opened_at is present and the age in weeks ((today minus opened date) in days / 7.0) is at least horizon_wk=78, the exit reason is q07_horizon_exit. A reasoned exit is a full-qty Intent, kind exit, side sell, position_intent sell_to_close, price_hint px.
2. Slot gate: if anything is held, return only the exits (1 slot). QQQ gate: QQQ daily bars (key QQQ|1day) need at least 2 rows and the last QQQ close must be below the prior close (QQQ-down day); otherwise return only the exits.
3. Candidate fires are read from extra sleeve_fires (view extra, merged with params extra). A fire is kept only if fire sleeve equals this sleeve id, it has a symbol not already held, its cap_band (when present) equals "ml", and its mcap_usd (when present) lies in the engine CAP_BANDS_USD range for this band (ml is [2000000000, infinity) dollars).
4. Signal age: sessions in (signal_date, today] counted on QQQ bar dates must be at least 0 and at most 5. The symbol needs daily bars. Stale-bar rule (ENH25-Q07-STALEBARS-20261024, default ON via extra q07_enh[<id>] fresh_bars): a symbol whose last bar date is more than 5 sessions before today (counted on QQQ dates) is refused, with a paired journal record.
5. Freshest-first (ENH-Q07FRESH-20261024, default ON via extra q07_enh[<id>] fresh_first): eligible fires are tried in ascending signal-age order; OFF restores producer list order.
6. Filters, all must pass (fail closed on missing evidence): deep70: the last close exists, at least 20 daily bars are present, and the close is at or below 0.70 times the maximum high over the last 252 bars; ins2: int(fire insider_buys or 0) is at least 2; vix20: the snapshot vix value (extra vix) exists and is at least 20.0. The wlow evidence switch (ENH-Q07WLOW-20261024) does not affect this sleeve because wlow is not among its filters.
7. Sizing: px is the last daily close; qty = int(1000.0 // px); qty below 1 is skipped. Emit one Intent, kind enter, side buy, position_intent buy_to_open, price_hint px, stop = round(px times (1 - 0.15), 4), exit_rules (stop at that stop price, time_bars at 78 times 5 = 390), reason naming q07_swing_tensor1w_ml, the filters joined with +, the signal date and the age in sessions, then break (one entry only).

## Files in this repo
- Adapter: adapters3/s_q07w_s78_ml_deep70_ins2_vix20.py (SLEEVE_ID=s_q07w_s78_ml_deep70_ins2_vix20; SPEC carried in the module; evaluate(view, ctx) calls desk3.q07_engine.evaluate_q07(SPEC, view, ctx); INPUTS declared in the module). Also present as sleeves/s_q07w_s78_ml_deep70_ins2_vix20.py and integration/s_q07w_s78_ml_deep70_ins2_vix20_adapter.py.
- Shared engine file: desk3/q07_engine.py (evaluate_q07, _filters_pass, CAP_BANDS_USD).
- Engine dependency: desk3/contract.py (ExitRule, Intent imported by desk3/q07_engine.py); its repo copy engines/desk3/contract.py is listed as gate_blocked in engines_map.json, so that exact repo copy is not present and must be taken from the desk source tree.
- Existing strategy doc: strategies/lazarus/lz-q07.md. Per-sleeve algorithm doc in this repo: docs/S_Q07W_S78_ML_DEEP70_INS2_VIX20-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_q07w_s78_ml_deep70_ins2_vix20), also at config/sleeves.json.

## Configuration
Module adapters3.s_q07w_s78_ml_deep70_ins2_vix20; cadence_s 300; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [sleeve_fires, bars_1day, vix, positions]; parked true; timeout_s null. Universe: Tensor 1W fires in the swing family and ml cap band that pass the named filters; timeframe 1W (weekly fires, daily bars for prices and QQQ). Source: muse-desk-v3/config/sleeves.json row id=s_q07w_s78_ml_deep70_ins2_vix20.

## Data inputs
Inputs are sleeve_fires, bars_1day, vix and positions. sleeve_fires arrive in view extra as sleeve_fires rows {sleeve, symbol, signal_date, cap_band, mcap_usd, insider_buys, wiki_views_30d} from the sleeve_feed composer (tracker ledger + alt-data tags, per the adapter header and the engine header); bars are view bars under <sym>|1day with t, h, c (including QQQ bars for the down gate and the session count); vix is view extra vix; positions is the broker readback with symbol, qty, avg_price and opened_at. No fresh fires means no entry, and a filter with no evidence fails closed.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/laz_sleeves/_common.py is laz_sleeves/_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_q07w_s78_ml_deep70_ins2_vix20` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_q07w_s78_ml_deep70_ins2_vix20.py, whose evaluate(view, ctx) calls desk3.q07_engine.evaluate_q07(SPEC, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture on a QQQ-down day with a swing / ml fire aged at most 5 sessions that passes every filter (deep70, ins2, vix20), no held position and a latest close giving qty above 0: exactly one enter intent, qty int(1000.0 // price), stop round(price times 0.85, 4), exit_rules stop plus time_bars 390, reason naming q07_swing_tensor1w_ml and the filters.
- Fixture on a day that is not QQQ-down, or with any one named filter lacking positive evidence, or with the fire aged more than 5 sessions, or with the symbol's last bar more than 5 sessions stale: no entry.
- Fixture with a held position whose last price is at or below avg_price times 0.85: exactly one sell_to_close exit for the full quantity, reason q07_stop15.
- Fixture with a held position aged at least 78 weeks and no stop hit: exactly one sell_to_close exit, reason q07_horizon_exit.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
