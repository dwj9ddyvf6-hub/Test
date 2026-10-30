# s_q07w_g52_sm_ins2_wcov: Recreation package

Provenance: research lab (Q07 confluence cells), run by Lazarus (Source row in strategies/lazarus/lz-q07.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Q07 alt-data confluence sleeve in the green family, small (sm) band, with a 52-week horizon and the filters ins2, wcov. It buys one $1,000 slot only on a QQQ-down day within 5 sessions of a Tensor 1W fire that passes every named filter, and exits on a 15 percent stop or at the 52-week horizon. Sources: desk adapters3/s_q07w_g52_sm_ins2_wcov.py (inline SPEC) and desk3/q07_engine.py.

## Full algorithm
This sleeve is a thin wrapper authored for v3 (Lazarus Q07 batch 6, no v2 source): adapters3/s_q07w_g52_sm_ins2_wcov.py evaluate(view, ctx) delegates to desk3/q07_engine.py evaluate_q07(SPEC, view, ctx), with the SPEC written inline in the adapter, not in an engine SPECS table. Wrapper note (desk adapters3/s_q07w_g52_sm_ins2_wcov.py): Tensor 1W green signal, sm cap band, filters ('ins2', 'wcov'); buy only on a QQQ-down day within 5 sessions of the signal; exit on a 15% stop or at the 52-week horizon; 1 slot at $1,000; CSV status sleeve_feed composer (tracker ledger + alt-data tags).

SPEC (desk adapters3/s_q07w_g52_sm_ins2_wcov.py): id="s_q07w_g52_sm_ins2_wcov", family="green", horizon_wk=52, band="sm", filters=('ins2', 'wcov'). Engine constants in desk3/q07_engine.py: SLOT_USD=1000.0, STOP_PCT=0.15, MAX_SIGNAL_AGE_SESSIONS=5, WIKI_LOW_MAX_VIEWS=1000, MOM6_SESSIONS=126, DEEP70_HIGH_SESSIONS=252, CAP_BANDS_USD sm = (300000000.0, 2000000000.0). Inputs declared in the adapter: sleeve_fires, bars_1day, vix, positions.

Evaluation order in desk3/q07_engine.py evaluate_q07():
1. Exits first. For each held position with qty above 0: price is the last close of that symbol's bars (view bars key "<sym>|1day", sorted by t). If avg_price is above 0 and price is at or below avg_price times (1 - 0.15), emit an exit Intent, kind exit, side sell, position_intent sell_to_close, full qty, reason "q07_stop15". Otherwise, if opened_at parses and the age in weeks (today minus opened_at, in days divided by 7.0) is at least horizon_wk=52, emit the same full exit with reason "q07_horizon_exit".
2. Entries: if any position is held, return only the exits (1 slot, occupied). QQQ bars are view bars key "QQQ|1day"; fewer than 2 QQQ bars returns only exits. QQQ-down means the last QQQ close is below the prior QQQ close; if QQQ is not down, return only exits.
3. Fires are read from view extra "sleeve_fires" (view["extra"], merged with view["params"]["extra"]). A fire is eligible only if fire["sleeve"] equals this sleeve id, it has a symbol not already held, its cap_band (when carried) equals "sm", its mcap_usd (when carried) lies in the sm CAP_BANDS_USD range (300000000.0, 2000000000.0), it carries a signal_date, and its signal age in QQQ sessions (sessions in (signal_date, today] counted on QQQ bar dates) is between 0 and 5 inclusive. The symbol must have daily bars.
4. Stale-bars guard (ENH25-Q07-STALEBARS-20261024, default ON via extra["q07_enh"][id]["fresh_bars"]; OFF enters on the stale close as pre-change): a symbol whose last bar date is more than 5 QQQ sessions before today is refused.
5. Freshest-first (ENH-Q07FRESH-20261024, default ON via extra["q07_enh"][id]["fresh_first"]; OFF restores producer list order): eligible fires are tried in ascending signal-age order.
6. Filters, all must pass: ins2: int(fire insider_buys or 0) must be at least 2; wcov: float(fire wiki_views_30d or 0) must be above 0; no Wikipedia coverage evidence fails closed.
7. Sizing: price is the last close of the symbol bars; qty = int(1000.0 // price); qty below 1 emits nothing. Emit one Intent, kind enter, side buy, position_intent buy_to_open, qty as computed, price_hint equal to that close, stop = round(price times (1 - 0.15), 4), exit_rules (stop at that stop price, time_bars at horizon_wk times 5 = 260.0), reason naming q07_green_tensor1w_sm, the filters, the signal date and the age in sessions, then break (one entry only).

## Files in this repo
- Adapter: adapters3/s_q07w_g52_sm_ins2_wcov.py (SLEEVE_ID=s_q07w_g52_sm_ins2_wcov; inline SPEC as given in the Full algorithm section; INPUTS=["sleeve_fires", "bars_1day", "vix", "positions"]; evaluate(view, ctx) delegates to desk3/q07_engine.evaluate_q07).
- Shared engine file: desk3/q07_engine.py (evaluate_q07, _filters_pass, cap-band table and constants).
- Shared engine dependency NOT in this repo: desk3/contract.py (the engine imports ExitRule and Intent from desk3.contract; desk3/contract.py is absent from the repo tree checked at batch start and is listed gate-blocked in the engines map, so a recreation must supply Intent and ExitRule with the fields used in the Full algorithm section from the desk source). No other engine file is delegated to by this sleeve.
- Existing strategy doc: strategies/lazarus/lz-q07.md. Per-sleeve algorithm doc in this repo: docs/S_Q07W_G52_SM_INS2_WCOV-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_q07w_g52_sm_ins2_wcov), also at config/sleeves.json.

## Configuration
Module adapters3.s_q07w_g52_sm_ins2_wcov; cadence_s 300; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [sleeve_fires, bars_1day, vix, positions]; parked false; timeout_s null. Universe: Tensor 1W fires for this sleeve id in the green family and small (sm) band that pass the named filters (cap-band market-cap range (300000000.0, 2000000000.0) USD when mcap_usd is carried); timeframe 1W (weekly fires, 1day bars). Source: muse-desk-v3/config/sleeves.json row id=s_q07w_g52_sm_ins2_wcov.

## Data inputs
Inputs are sleeve_fires, bars_1day, vix and positions. Fires arrive in the cycle snapshot extra under the key sleeve_fires (the sleeve_feed composer, tracker ledger plus alt-data tags, publishing sleeve_fires_v1.json in the source system), one fire row per sleeve carrying sleeve, symbol, signal_date, cap_band, mcap_usd, insider_buys and wiki_views_30d (and wiki_low where carried); bars_1day gives daily bars per symbol under keys "<sym>|1day" with t and c (QQQ bars drive both the QQQ-down gate and session-age counting); vix is the snapshot extra vix value (declared as an input; this sleeve's filters do not read it); positions is the broker readback with qty, avg_price and opened_at. No matching fire means no entry.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/sleeves/laz8_common.py is sleeves/laz8_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_q07w_g52_sm_ins2_wcov` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_q07w_g52_sm_ins2_wcov.py, whose evaluate(view, ctx) calls desk3/q07_engine.evaluate_q07(SPEC, view, ctx). Supply desk3/contract.py (Intent, ExitRule) from the desk source as noted under Files in this repo before the first evaluation, since that file is not in this repo.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture on a QQQ-down day with a fire for this sleeve aged 0 to 5 QQQ sessions that passes every filter (ins2, wcov), no held position and fresh symbol bars: exactly one buy_to_open entry (Intent kind enter), qty int(1000.0 // last close), stop round(last close times 0.85, 4), exit_rules stop at that price and time_bars 260.0, reason naming q07_green_tensor1w_sm and the filters.
- Fixture on a day that is not QQQ-down, or with any one named filter failing, or with the fire aged more than 5 sessions, or with the symbol's last bar more than 5 sessions old: no entry.
- Fixture with any held position: no entry in the same call (1 slot occupied).
- Fixture with a held position whose last close is at or below avg_price times 0.85: exactly one sell_to_close exit for the full quantity, reason q07_stop15. Fixture with a held position opened at least 52 weeks before today and no stop hit: exactly one sell_to_close exit, reason q07_horizon_exit.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
