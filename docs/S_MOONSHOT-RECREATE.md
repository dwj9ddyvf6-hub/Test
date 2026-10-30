# s_moonshot: Recreation package

Provenance: research (MOONSHOT_FROZEN_SPEC v1.0), run by Lazarus; Midna's moonshot book (Source row in strategies/lazarus/lz-moonshot.md in this repo; the codename token in that row is omitted here under the repo PII rule).

## What this sleeve is
This is a long-only weekly Lazarus fire-consumer sleeve for cheap, deeply pulled-back cyan names: it buys qualifying Tensor 1W fires priced at or below $14.94 with a deep60 tag, in up to 10 slots from a $2,581 slice, with a 15 percent stop and a 252-session horizon. Signal generation stays upstream; this engine consumes only ingested fires. Sources: desk adapters3/s_moonshot.py and desk3/lazarus.py SPECS (wrapper note: Moonshot, CSV off, Shadow).

## Full algorithm
This sleeve is a thin wrapper: adapters3/s_moonshot.py evaluate(view, ctx) delegates to desk3/lazarus.py evaluate(SLEEVE_ID, view, ctx), with INPUTS taken from that engine.

SPEC (desk3/lazarus.py SPECS): slots=10, capital=2581.0, cadence_s=3600, session="rth", max_age_min=11520 (60*24*8, 8 days), qqq_down is not set for this SPEC (so no QQQ-down entry gate in the engine for this sleeve), stop_pct=0.15, horizon_sessions=252, family="cyan", tf="1W", max_price=14.94, max_price_inclusive=True, deep60=True. Inputs: lazarus_fires, bars, positions.

Evaluation order in desk3/lazarus.py evaluate():
1. Exits first. For each held position, current price is read from the snapshot bars / price helper and entry is avg_price. In order: if stop_pct applies and current price is at or below entry times (1 - 0.15), exit in full, reason s_moonshot_stop15; else if a target_price stored at entry exists and current price reaches it, exit in full, reason s_moonshot_target; else the partial and target_pct branches do not apply to this SPEC (it sets neither partial_pct nor target_pct); else if sessions held (counted from session_dates when supplied, else SPY bar dates, else business days) reach the stored horizon (or the SPEC horizon 252), exit in full, reason s_moonshot_time_exit_252s. Exits are market, day, sell. If any exit is emitted, state is saved and no entry is evaluated in the same call.
2. Entries: if the number of held positions is at least slots=10, return nothing. Per-slot budget is capital / slots = 2581.0 / 10 = 258.10.
3. Fires are read from view["lazarus_fires"], view["extra"]["lazarus_fires"], view["tensor_fires"] or view["extra"]["fires"] (the first list found). A fire is skipped if its sleeve_id differs, its symbol is already held, its side is not buy / long, it has no parseable fired_at / ts, or its age is below 0 minutes or above max_age_min=11520 minutes.
4. Family / tier / cap filters are enforced only when the fire carries that field: a carried family / color must contain "cyan"; this SPEC sets no signal_tier or cap_tier, so those checks do not filter this sleeve.
5. Max price, inclusive: the price read from the snapshot (falling back to the fire) must be at or below 14.94; exactly 14.94 passes, above it is skipped. Deep60 gate: the fire or its tags must carry deep60 or deep_pullback60, otherwise the fire is skipped.
6. Execution price: ENH-LAZ-REPRICE-20261024 is default ON, so when a fresh bar close exists and differs from the fire price, sizing, stop and price_hint use the fresh close and the fire-price decision is recorded as the paired shadow control on the entry intent; OFF restores the fire-price rule exactly.
7. Bound guard (ENH19-LAZ-BOUND-20261024, default ON): refuse an entry whose fresh price is at or above the fire target_price, or above the SPEC max_price (inclusive cap, so only above 14.94 is refused on that bound).
8. Sizing: qty = int(per_slot // execution price) = int(258.10 // price); qty below 1 emits nothing. Emit a market, day, buy entry with stop_price = round(price times (1 - 0.15), 4), price_hint equal to the execution price, reason s_moonshot_tensor_fire, and record horizon_sessions (the fire's own horizon when the engine's horizon-from-fire conditions apply, otherwise 252), target_price and entry_at in the sleeve state.

## Files in this repo
- Adapter: adapters3/s_moonshot.py (SLEEVE_ID=s_moonshot; evaluate(view, ctx) delegates to desk3/lazarus.evaluate, INPUTS imported from that engine).
- Shared engine file: desk3/lazarus.py (SPECS entry for s_moonshot, evaluate, reprice and bound-guard logic).
- Existing strategy doc: strategies/lazarus/lz-moonshot.md. Per-sleeve algorithm doc in this repo: docs/S_MOONSHOT-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=s_moonshot), also at config/sleeves.json.

## Configuration
Module adapters3.s_moonshot; cadence_s 3600; session rth; slice capital_usd 2581.0, cash_usd 2581.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [lazarus_fires, bars, positions]; parked true; timeout_s null. Universe: symbols carried by qualifying Lazarus fires (family cyan, timeframe 1W, price at or below $14.94, deep60); timeframe 1W. Source: muse-desk-v3/config/sleeves.json row id=s_moonshot. Note the roster parked state is true and the wrapper describes the lane as CSV off, Shadow, even though the engine SPEC itself carries no parked flag.

## Data inputs
Inputs are lazarus_fires, bars and positions, declared in desk3/lazarus.py INPUTS. Fires arrive via the snapshot keys listed in the Full algorithm section with symbol, side, fired_at / ts, family, price and tags (including deep60 / deep_pullback60 and any target_price); bars give the current / fresh close per symbol (and SPY bars for session counting); positions is the broker readback of held positions with avg_price and opened_at. No fresh matching fire means no entry.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/sleeves/laz8_common.py is sleeves/laz8_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_moonshot` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/s_moonshot.py, whose evaluate(view, ctx) calls desk3/lazarus.evaluate(SLEEVE_ID, view, ctx). Respect the parked true roster state in step 5 below.
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with a qualifying cyan fire aged within 11520 minutes, priced at exactly 14.94 with a deep60 tag, no held positions and no fresher different close: an entry is computed with qty int(258.10 // 14.94) and stop_price round(14.94 times 0.85, 4), subject to the roster parked state.
- Fixture with the same fire priced above 14.94, or without deep60 / deep_pullback60 evidence: no entry.
- Fixture with a held position whose current price is at or below avg_price times 0.85: exactly one sell exit for the full quantity, reason s_moonshot_stop15, and no entry in the same call.
- Fixture with a held position held for at least 252 sessions and no stop or target hit: exactly one sell exit, reason s_moonshot_time_exit_252s.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
