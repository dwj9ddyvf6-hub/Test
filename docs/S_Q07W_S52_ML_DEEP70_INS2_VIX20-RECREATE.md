# s_q07w_s52_ml_deep70_ins2_vix20: Recreation package

Provenance: research lab (Q07 confluence cells), run by Lazarus (Source row in strategies/lazarus/lz-q07.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Q07 alt-data confluence sleeve in the swing family, ml cap band, with a 52-week horizon and the filters deep70, ins2, vix20. It buys one $1,000 slot only on a QQQ-down day within 5 sessions of a Tensor 1W signal that passes every named filter, and exits on a 15 percent stop or at the horizon. Sources: desk adapters3/s_q07w_s52_ml_deep70_ins2_vix20.py (SPEC inline) and desk3/q07_engine.py.

## Full algorithm
This sleeve is a thin wrapper: adapters3/<id>.py evaluate(view, ctx) calls desk3/q07_engine.py evaluate_q07(SPEC, view, ctx), with the SPEC dict carried inline in the wrapper. Wrapper note (desk adapters3/<id>.py): Tensor 1W swing signal, ml cap band, filters ('deep70', 'ins2', 'vix20'); buy only on a QQQ-down day within 5 sessions of the signal; exit on a 15% stop or at the 52-week horizon; 1 slot at $1,000 (batch 6, authored for v3; no v2 source exists). CSV status: sleeve_feed composer (tracker ledger + alt-data tags).

SPEC (inline in adapters3/<id>.py): id=<id>, family="swing", band="ml", horizon_wk=52, filters=("deep70", "ins2", "vix20"). Engine constants in desk3/q07_engine.py: SLOT_USD=1000.0, STOP_PCT=0.15, MAX_SIGNAL_AGE_SESSIONS=5, WIKI_LOW_MAX_VIEWS=1000, MOM6_SESSIONS=126, DEEP70_HIGH_SESSIONS=252. Cap bands in the engine (CAP_BANDS_USD): ml = 2,000,000,000 USD and above (this sleeve's band). Inputs declared in the wrapper: sleeve_fires, bars_1day, vix, positions.

Evaluation order in desk3/q07_engine.py evaluate_q07():
1. Exits first. For each held position (qty above 0), last price is the last close of the symbol's daily bars (view bars key "<sym>|1day", sorted by t). If avg_price is above 0 and the last price is at or below avg_price times (1 - 0.15), sell the full quantity, reason "q07_stop15". Otherwise, if opened_at is present and the age in weeks ((today minus opened_at) in days / 7.0) is at least horizon_wk=52, sell the full quantity, reason "q07_horizon_exit". Exits are Intent objects, side sell, position_intent sell_to_close.
2. Entries are blocked entirely while any position is held (the 1 slot is occupied).
3. A QQQ-down day is required: at least 2 QQQ daily bars and the last QQQ close below the prior close; otherwise return only any exits.
4. Fires are read from view extra["sleeve_fires"] (keys from view params extra are merged in with setdefault). A fire is skipped if its sleeve field differs from the SPEC id, it has no symbol, its symbol is held, its cap_band (when carried) differs from "ml", its mcap_usd (when carried) falls outside the CAP_BANDS_USD range for "ml", it has no signal_date, its signal age (QQQ sessions in (signal_date, today]) is below 0 or above 5, or it has no daily bars.
5. Freshest-first (ENH-Q07FRESH-20261024, default ON; OFF restores producer list order): eligible fires are ordered by signal age ascending.
6. Stale bars (ENH25-Q07-STALEBARS-20261024, default ON): a fire whose symbol's last bar date is more than 5 QQQ sessions before today is refused.
7. Filters, all must pass and a filter with no evidence fails closed: deep70: at least 20 daily bars are present and the last close is at or below 0.70 times the maximum high over the trailing 252 sessions (DEEP70_HIGH_SESSIONS=252); ins2: insider_buys on the fire is at least 2; a missing value counts as 0 and fails; vix20: the snapshot vix value is present and at least 20.0.
8. Sizing: qty = int(SLOT_USD // price) = int(1000.0 // price), where price is the symbol's last daily close; qty below 1 emits nothing. Emit one Intent, kind enter, side buy, position_intent buy_to_open, price_hint equal to that close, stop = round(price times (1 - 0.15), 4), exit_rules of a stop ExitRule at that price plus a time_bars ExitRule of horizon_wk times 5 (260), signal_date set to the fire's signal date, and reason "q07_swing_tensor1w_ml filters=<filters joined by +> signal=<signal_date> age_sessions=<age>", then break (one entry only).

## Files in this repo
- Adapter: adapters3/s_q07w_s52_ml_deep70_ins2_vix20.py (SLEEVE_ID=s_q07w_s52_ml_deep70_ins2_vix20; SPEC dict inline; evaluate(view, ctx) calls desk3.q07_engine.evaluate_q07(SPEC, view, ctx); INPUTS declared in the wrapper).
- Shared engine file: desk3/q07_engine.py (evaluate_q07, _filters_pass, cap bands and engine constants).
- Shared engine dependency: engines/desk3/contract.py (desk desk3/contract.py: ExitRule and Intent imported by desk3/q07_engine.py). Recorded gap: in engines_map.json this file's vendoring status is gate_blocked, and it is absent from the fresh repo tree taken at batch start; a recreation must supply desk3/contract.py with the ExitRule and Intent shapes the engine uses, as described in the Full algorithm section.
- Existing strategy doc: strategies/lazarus/lz-q07.md. Per-sleeve algorithm doc in this repo: docs/S_Q07W_S52_ML_DEEP70_INS2_VIX20-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_q07w_s52_ml_deep70_ins2_vix20), also at config/sleeves.json.

## Configuration
Module adapters3.s_q07w_s52_ml_deep70_ins2_vix20; cadence_s 300; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; timeout_s null; params {}; inputs [sleeve_fires, bars_1day, vix, positions]; parked true. Universe: Tensor 1W swing fires in the ml cap band (ml = 2,000,000,000 USD and above) that pass the named filters; timeframe 1W signals on daily bars. Source: muse-desk-v3/config/sleeves.json row id=s_q07w_s52_ml_deep70_ins2_vix20.

## Data inputs
Inputs are sleeve_fires, bars_1day, vix and positions. Fires arrive via the sleeve_feed composer (tracker ledger plus alt-data tags) as the producer key sleeve_fires in the cycle snapshot view extra (view params extra keys are merged in), one fire row per sleeve carrying sleeve, symbol, signal_date, cap_band, mcap_usd, insider_buys and wiki fields; bars are daily bars in view bars under the key "<sym>|1day" with t, h and c (QQQ bars drive both the QQQ-down gate and session counting); vix is the snapshot extra vix value; positions is the broker readback with qty, avg_price and opened_at. No fresh fires means no entry, and a filter with no evidence fails closed.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (a desk3/ path is the same path on a fresh desk; an engines/ path maps back to the desk path after engines/). The desk3/contract.py gap recorded under Files in this repo must be closed by supplying that file; do not invent a different Intent or ExitRule shape.
2. Register the config row for `s_q07w_s52_ml_deep70_ins2_vix20` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_q07w_s52_ml_deep70_ins2_vix20.py, whose evaluate(view, ctx) calls desk3.q07_engine.evaluate_q07(SPEC, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture on a QQQ-down day with a swing / ml fire aged at most 5 QQQ sessions that passes every filter (deep70, ins2, vix20), no held position and a last close giving qty above 0: exactly one enter Intent, qty int(1000.0 // price), stop round(price times 0.85, 4), exit_rules stop at that price plus time_bars 260, reason starting q07_swing_tensor1w_ml — subject to the roster parked state in the Configuration section (parked true: the dispatcher skips entries while parked, exits still managed).
- Fixture on a day that is not QQQ-down, or with any one named filter failing, or with the fire aged more than 5 sessions, or with the symbol's last bar more than 5 sessions old: no entry.
- Fixture with a held position whose last close is at or below avg_price times 0.85: exactly one sell_to_close exit for the full quantity, reason q07_stop15, and no entry in the same call.
- Fixture with a held position aged at least 52 weeks (opened_at) and no stop hit: exactly one sell_to_close exit, reason q07_horizon_exit.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
