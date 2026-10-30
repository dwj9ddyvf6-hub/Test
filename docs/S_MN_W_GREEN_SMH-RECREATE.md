# s_mn_w_green_smh: Recreation package

Provenance: Midna's TypeScript desk (equity books), ported line for line to the master desk (Source row in strategies/midna/mn-forward-lab.md in this repo).

## What this sleeve is
This is a long-only weekly Midna fire-consumer sleeve: it buys one Tensor green 1W fire only when SMH is calm over the last 20 sessions, and holds it for 126 sessions with no price stop. Signal generation stays upstream in the fire producer; this sleeve only consumes fires and manages the position. Sources: desk adapters3/s_mn_w_green_smh.py and desk3/lazarus_midna.py SPECS.

## Full algorithm
This sleeve is a thin wrapper: adapters3/<id>.py evaluate(view, ctx) delegates to desk3/lazarus_midna.py evaluate(SLEEVE_ID, view, ctx). The engine rules below are as applied with this sleeve's SPEC.

SPEC (desk3/lazarus_midna.py SPECS): family="green", tf="1W", hold_sessions=126, stop=None, gate="smh_calm", budget=1000.0
Inputs: tensor, bars, positions. The engine holds at most 1 open position.

Evaluation order in desk3/lazarus_midna.py evaluate():
1. Exits first. For each non-zero position, price is the last bar close for the symbol (bars keys tried: <sym>|1Day, <sym>|1D, <sym>, <sym>|1Week, <sym>|1W), falling back to avg_price. Stop is None for this sleeve, so no price-stop exit applies. Time exit: if age in sessions is at least 126, sell the full quantity, market, day, sell_to_close, reason naming the sleeve, exit: time_<hold>_sessions (age read from sessions_held / age_sessions / held_sessions / bars_held, else age_weeks / held_weeks times 5, else counted from entry_date / opened_at against the symbol bars). If any exit is emitted, return only the exits.
2. If any position is already held, return no entry (max 1 slot).
3. Fires: read from view["midna_fires"], view["fires"], extra["midna_fires"] / extra["fires"], or view["tensor"] / view["tensor_bundle"] (a list, a dict with a fires / midna_fires list, or a sleeves dict of fire lists). No fires means no entry. A fire is skipped if its sleeve_id differs from this sleeve, its family / kind / signal does not contain the SPEC family, its timeframe / tf does not match the SPEC timeframe (1W accepts 1W, WEEKLY, W, WEEK; 1D accepts 1D, DAILY, D, DAY), it has no symbol, or its date / fire_date / ts is before the session by more than 10 days or after the session.
4. Cross-stale refusal (ENH20-MN-XSTALE-20261024, default ON; OFF via extra["<id>_enh20"]["xstale_gate"]=False): refuse a symbol whose last bar date lags the latest bar date across all snapshot bars by more than 4 days.
5. Price: ENH19 reprice is default ON, so when a fresh last bar close exists the gate and sizing use that fresh close; otherwise the fire price is used. A price at or below zero is skipped.
6. Gate for this sleeve: SMH must be calm: extra smh_calm, when present, must be truthy; otherwise with at least 21 SMH bars the absolute 20-session return (last close divided by the close 21 bars back, minus 1) must be at most 0.05; with fewer than 21 SMH bars and no smh_calm value the fire is skipped (fail closed).
7. Sizing: qty = int(1000.0 // price); qty below 1 emits nothing. Emit one market, day, buy_to_open entry intent with price_hint equal to the chosen price and a reason naming the sleeve, its family / timeframe, the fire date and the gate, then stop (break after the first entry).

## Files in this repo
- Adapter: adapters3/s_mn_w_green_smh.py (SLEEVE_ID=s_mn_w_green_smh; evaluate(view, ctx) delegates to desk3/lazarus_midna.evaluate, with INPUTS and PRODUCERS imported from that engine).
- Shared engine file: desk3/lazarus_midna.py (SPECS entry for s_mn_w_green_smh, evaluate, gate logic, ENH19 reprice and ENH20 cross-stale refusal).
- Existing strategy doc: strategies/midna/mn-forward-lab.md. Per-sleeve algorithm doc in this repo: docs/S_MN_W_GREEN_SMH-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_mn_w_green_smh), also at config/sleeves.json.

## Configuration
Module adapters3.s_mn_w_green_smh; cadence_s 300; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [tensor, bars, positions]; parked false. Universe: symbols carried by qualifying Tensor / Midna fires in the snapshot; timeframe 1W (SPEC tf). Source: muse-desk-v3/config/sleeves.json row id=s_mn_w_green_smh.

## Data inputs
Inputs are tensor, bars and positions. Producers named in desk3/lazarus_midna.py PRODUCERS: tensor_bundle (outputs tensor, freshness_sla_s 86400), bars (freshness_sla_s 900) and broker_readback (outputs positions, freshness_sla_s 900). Fires are consumed via the Tensor bundle channel as described in the Full algorithm section; bars give daily / weekly closes per symbol (and VIX / SMH bars for the gates that need them); positions is the broker readback of held positions. Fail-closed if fires are absent or stale.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/sleeves/laz8_common.py is sleeves/laz8_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_mn_w_green_smh` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_mn_w_green_smh.py, whose evaluate(view, ctx) calls desk3/lazarus_midna.evaluate(SLEEVE_ID, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with no held position, a qualifying family="green", tf="1W", hold_sessions=126, stop=None, gate="smh_calm", budget=1000.0 fire dated within 10 days of the session, a fresh last bar, and the gate condition satisfied: exactly one market buy_to_open entry, qty int(1000.0 // price), price_hint equal to the fresh close when one exists.
- Fixture with the gate condition not satisfied or with no gate evidence: no entry.
- Fixture with a held position aged at least 126 sessions: exactly one market sell_to_close exit for the full quantity, and no entry in the same call.
- Fixture with a held position aged below 126 sessions: no exit and no new entry (max 1 slot).
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
