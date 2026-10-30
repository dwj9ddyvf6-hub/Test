# s_rules_1d: Recreation package

Provenance: research lab (frozen rules), run by Lazarus (Source row in strategies/lazarus/lz-lab-rules.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only daily Lazarus fire-consumer sleeve for the lab's frozen rules: it buys qualifying lab fires in up to 44 slots at $1,000 per slot from a $44,000 slice, with no price stop, exiting at a stored target or at each rule's horizon plus one session. Signal generation stays upstream; this engine consumes only ingested fires. Sources: desk adapters3/s_rules_1d.py and desk3/lazarus.py SPECS (wrapper note: Lab rule 1D, 43 frozen rules, CSV ON, Live).

## Full algorithm
This sleeve is a thin wrapper: adapters3/<id>.py evaluate(view, ctx) delegates to desk3/lazarus.py evaluate(SLEEVE_ID, view, ctx). Wrapper note (desk adapters3/<id>.py): v3 Lazarus fire-consumer sleeve s_rules_1d (batch 2). Engine: desk3/lazarus.py. Lab rule 1D - 43 frozen rules (CSV ON, Live). Catalog rule in desk3.lazarus SPECS + FIDELITY-LEDGER LAZ2.

SPEC (desk3/lazarus.py SPECS): slots=44, capital=44000.0, cadence_s=300, session="rth", max_age_min=2880, stop_pct=None, horizon_sessions=22, horizon_from_fire=True, horizon_plus_one=True. qqq_down is not set for this SPEC (so no QQQ-down entry gate in the engine for this sleeve), Inputs: lazarus_fires, bars, positions. Per-slot budget is capital / slots = 1000.0.

Evaluation order in desk3/lazarus.py evaluate():
1. Exits first. For each held position: current price is read from the snapshot bars / price helper and entry is avg_price; horizon is the horizon stored in the sleeve state at entry (laz_state) or the SPEC default 22; target is the target_price stored at entry; sessions held are counted from extra session_dates when supplied, else SPY bar dates, else business days. In order: if stop_pct applies and current price is at or below entry times (1 - stop_pct), exit in full, reason s_rules_1d_stop15 (this branch applies only where stop_pct is set); else if a stored target_price exists and current price reaches it, exit in full, reason s_rules_1d_target; else the partial and target_pct branches do not apply to this SPEC (it sets neither); else if sessions held reach the stored horizon, exit in full, reason s_rules_1d_time_exit_<horizon>s. Exits are market, day, sell. If any exit is emitted, state is saved and no entry is evaluated in the same call.
2. Entries: if the number of held positions is at least slots=44, return nothing.
3. Freshest-first (ENH25-RULES-FRESH-20261024, default ON for the two rules lanes; OFF restores producer list order): for this sleeve, candidate fires for this sleeve id are reordered freshest fired_at first (stable) when 2 or more candidates exist, with a paired journal record.
4. Fires are read from view["lazarus_fires"], view["extra"]["lazarus_fires"], view["tensor_fires"] or view["extra"]["fires"] (the first list found). A fire is skipped if its sleeve_id differs, its symbol is already held, its side is not buy / long, it has no parseable fired_at / ts, or its age is below 0 minutes or above max_age_min=2880 minutes.
5. Family / tier / cap filters are enforced only when the SPEC names them; this SPEC sets no family, signal_tier or cap_tier, and no max_price, deep60, deep or min_vix, so none of those checks filter this sleeve. The qqq_down check applies only where the SPEC sets it (see the SPEC line above): where it applies, the fire's qqq_red / qqq_down value is used, else the QQQ red check from bars, and it must be exactly True.
6. Execution price: ENH-LAZ-REPRICE-20261024 is default ON, so when a fresh bar close exists and differs from the fire price, sizing, stop and price_hint use the fresh close and the fire-price decision is recorded as the paired shadow control on the entry intent; OFF restores the fire-price rule exactly.
7. Bound guard (ENH19-LAZ-BOUND-20261024, default ON): refuse an entry whose fresh price is at or above the fire target_price; the max_price bound does not apply to this SPEC (it sets no max_price).
8. Sizing and state: qty = int(per_slot // execution price) = int(1000.0 // price); qty below 1 emits nothing. Emit a market, day, buy entry with stop_price = round(price times (1 - stop_pct), 4) where stop_pct is set and None otherwise, price_hint equal to the execution price, reason s_rules_1d_tensor_fire, and record in state the horizon (the fire's horizon_sessions when present, because horizon_from_fire is set, otherwise 22; plus 1 when the fire carried a horizon, because horizon_plus_one is set), target_price and entry_at. Stop once held plus entries reach slots=44.

## Files in this repo
- Adapter: adapters3/s_rules_1d.py (SLEEVE_ID=s_rules_1d; evaluate(view, ctx) delegates to desk3/lazarus.evaluate, INPUTS imported from that engine). Also present as sleeves/s_rules_1d.py and integration/s_rules_1d_adapter.py.
- Shared engine file: desk3/lazarus.py (SPECS entry for s_rules_1d, evaluate, reprice, bound-guard and freshest-first logic).
- Existing strategy doc: strategies/lazarus/lz-lab-rules.md. Per-sleeve algorithm doc in this repo: docs/S_RULES_1D-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_rules_1d), also at config/sleeves.json.

## Configuration
Module adapters3.s_rules_1d; cadence_s 300; session rth; slice capital_usd 44000.0, cash_usd 44000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [lazarus_fires, bars, positions]; parked false; timeout_s null. Universe: symbols carried by qualifying Lazarus lab-rule fires; timeframe 1D. Source: muse-desk-v3/config/sleeves.json row id=s_rules_1d.

## Data inputs
Inputs are lazarus_fires, bars and positions, declared in desk3/lazarus.py INPUTS. Fires arrive via the snapshot keys listed in the Full algorithm section with symbol, side, fired_at / ts, price, horizon_sessions and any target_price; bars give the current / fresh close per symbol (and SPY bars for session counting); positions is the broker readback of held positions with avg_price and opened_at; sleeve state (horizon and target per symbol) is kept in laz_state.json under the ctx state_dir. No fresh matching fire means no entry.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/laz_sleeves/_common.py is laz_sleeves/_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_rules_1d` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_rules_1d.py, whose evaluate(view, ctx) calls desk3/lazarus.evaluate(SLEEVE_ID, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with a qualifying fire aged within 2880 minutes (48 hours), no held positions and no fresher different close: entries are computed with qty int(1000.0 // price) and stop_price None, reason s_rules_1d_tensor_fire, up to 44 slots.
- Fixture with the same fire aged above 2880 minutes, with side not buy / long, or with a fresh price at or above the fire target_price: no entry.
- Fixture with a held position whose stored target_price is reached: exactly one sell exit for the full quantity, reason s_rules_1d_target, and no entry in the same call.
- Fixture with a held position held for at least its stored horizon in sessions (the fire horizon plus 1 when the fire carried one, otherwise 22) and no target hit: exactly one sell exit, reason naming s_rules_1d_time_exit. No price move alone exits this sleeve (stop_pct is None).
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
