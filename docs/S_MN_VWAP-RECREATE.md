# s_mn_vwap: Recreation package

Provenance: Midna's TypeScript desk (equity books), ported line for line to the master desk (Source row in strategies/midna/mn-ema4-vwap.md in this repo).

## What this sleeve is
This is a long-only daily equity sleeve that trades the price cross itself against a 20-session rolling VWAP: it enters when price crosses above that VWAP and exits when price crosses back below it. It holds at most one position at a $1,000 slot budget. Sources: desk sleeves/s_mn_vwap.py (strategy), adapters/s_mn_vwap.py (adapter), sleeves/laz8_common.py (shared helpers).

## Full algorithm
Evaluation order in desk sleeves/s_mn_vwap.py signal(bars, slice_state, context), with CONFIG sleeve_id=s_mn_vwap, cadence_s=300, WINDOW=20, SLOT_BUDGET=1000.0:
1. Rolling VWAP definition: for bar index i, if fewer than 20 bars are available return None; otherwise over the last 20 bars compute sum(typical price times volume) / sum(volume), where typical price is (high + low + close) / 3. Any bar in the window with volume at or below zero makes the VWAP None.
2. Cross definition (_cross, on the last two closed bars): needs at least WINDOW+1 = 21 bars. Up cross: previous close at or below previous VWAP and last close above last VWAP. Down cross: previous close at or above previous VWAP and last close below last VWAP. If either VWAP is None, both flags are False.
3. Exits first: for each held position (held_positions from slice_state), if its symbol shows a down cross, emit an exit Intent, kind exit, side sell, position_intent sell_to_close, qty_hint equal to the full held quantity, price_hint equal to the last close, reason "s_mn_vwap exit: price_cross_below_vwap20". If any exit was emitted, or any position is held, return without entering.
4. Entries: iterate symbols in sorted(bars) order. For the first symbol with an up cross, first apply the cross-stale refusal from sleeves/laz8_common.py xstale_refused (ENH20-LAZ8-XSTALE-20261024, default ON): refuse the entry when that symbol's last bar lags the universe's latest bar by more than 4 calendar days. If not refused, price is the last close, qty is qty_for(1000.0, price) = floor(1000.0 / price); if qty is above 0 emit one enter Intent, side buy, position_intent buy_to_open, price_hint equal to that close, reason "s_mn_vwap entry: price_cross_above_vwap20 slot_budget=1000", then break (one entry only, one slot).
There is no price stop, target or time exit in this sleeve module; the only exit rule is the down cross above.

## Files in this repo
- Sleeve module: sleeves/s_mn_vwap.py (strategy logic, CONFIG, WINDOW and SLOT_BUDGET).
- Adapter: adapters/s_mn_vwap.py (SLEEVE_ID, INPUTS=('bars', 'positions'), PRODUCERS with freshness_sla_s=900 for each input, DEFAULT_EQUITY=1000.0, evaluate = make_evaluate from adapters.laz8_common).
- Shared engine / helper files: engines/sleeves/laz8_common.py (desk sleeves/laz8_common.py: Intent, SleeveConfig, held_positions, qty_for, xstale_refused) and engines/adapters/laz8_common.py (desk adapters/laz8_common.py: make_evaluate used by the adapter).
- Existing strategy doc: strategies/midna/mn-ema4-vwap.md. Per-sleeve algorithm evidence is in the sleeve module itself; the existing doc's Notes section states the v3 rule (price crossing a 20-session VWAP, one slot).
- Config: engines/config/sleeves.json (row id=s_mn_vwap), also at config/sleeves.json.

## Configuration
Module adapters.s_mn_vwap; cadence_s 300; session rth; slice capital_usd 1000.0, cash_usd 1000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, positions]; parked false. Universe: the symbols present in the bars snapshot (iterated in sorted order for entries); timeframe 1D daily bars (20-session rolling VWAP). Source: muse-desk-v3/config/sleeves.json row id=s_mn_vwap.

## Data inputs
Inputs are bars and positions. The adapter declares a producer for each input with freshness_sla_s 900: bars (daily bars with h, l, c, v and t for each symbol, at least 21 closed bars for a cross) and positions (broker readback / slice state giving held positions with qty). The sleeve module reads held state through held_positions(slice_state). No fresh bars means no VWAP and no intent.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/sleeves/laz8_common.py is sleeves/laz8_common.py on a fresh desk; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `s_mn_vwap` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters/s_mn_vwap.py, whose evaluate is make_evaluate(SLEEVE_ID, DEFAULT_EQUITY=1000.0) from adapters.laz8_common; it delegates to sleeves/s_mn_vwap.py signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with 21 daily bars where the previous close is at or below the previous 20-session VWAP and the last close is above the last VWAP, and no held position: exactly one buy_to_open entry for the alphabetically first such symbol, qty floor(1000 / last close), reason containing price_cross_above_vwap20.
- Fixture with a held position and a down cross on its symbol: exactly one sell_to_close exit for the full held quantity, reason containing price_cross_below_vwap20, and no entry in the same call.
- Fixture with fewer than 21 bars, or a zero-volume bar inside a VWAP window: no intent.
- Fixture where the entry symbol's last bar lags the universe latest bar by more than 4 days: no entry for that symbol (cross-stale refusal).
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
