# qqq_put_ladder: Recreation package

Provenance: Source row in strategies/femto/femto-qqq-put-ladder.md in this repo: A public options campaign, run by Aurelia (Agentic-Trading-Desk), via Femto-lean; Midna's variant.

## What this sleeve is
This is a cash-secured QQQ short-put ladder: it sells 3 puts per layer at roughly 45 DTE and delta 0.05 to 0.08, adds at most one new layer per ISO week, and manages each layer by rolling up, rolling out and down, or buying it back as expiry approaches. Its book state is the layer list itself, in the virtual ledger account named in the module. Sources: sleeves/qqq_put_ladder.py and desk3/port_b5/qqq_put_ladder.py on the desk.

## Full algorithm
Constants (sleeves/qqq_put_ladder.py): UNDERLYING QQQ, ACCOUNT qqq_put_ladder, LAYER_QTY 3, DELTA_LO 0.05, DELTA_HI 0.08, TARGET_DELTA 0.05, DTE_LO 38, DTE_HI 52, TARGET_DTE 45, MANAGE_DTE 21, CLOSE_DTE 5, MAX_CONTRACTS 12, CHALLENGED_DELTA 0.20, CHALLENGED_SPOT 1.03, DECAY_RATIO 0.50, WEEK_LOOKBACK 5, MIN_BID 0.05. CONFIG: cadence_s 900, universe (QQQ,), state_schema {layers}. Cash required per layer = (strike - bid) x 100 x qty; the sleeve's budget check is context.extra["buying_power"] (no fixed budget).
decide() evaluation order, per session (spot from context.extra["spot"], else the last QQQ bar close; no spot means no actions):
1. Manage open layers (status working or open), oldest expiration first. A layer with no live quote: at or inside 5 DTE it still emits an unpriced buy-to-close; otherwise it is skipped and flags missing_quote.
2. Buy back: a layer at or inside 5 DTE is bought back (buy_close at the ask).
3. Challenged (ENH, switch context.extra["qqq_put_ladder_improve"]["challenged_any_dte"], default ON): a challenged layer (live |delta| >= 0.20, or spot <= strike x 1.03) at any DTE, not already rolled today, rolls out-and-down to a later qualifying put at a strike at or below the current strike (same pick rules) when one exists and posture is not stand_down; otherwise it is bought back. With the switch OFF this branch runs only inside the 21-DTE manage gate below.
4. Manage gate: layers with more than 21 DTE remaining, or already rolled today, are otherwise left alone.
5. Roll up (inside 21 DTE): when posture is normal, the layer is not challenged, spot is above the layer's entry spot, and the live ask is at most 0.50 x the entry credit, roll up in the SAME expiration to a higher strike whose bid exceeds the current ask.
6. Challenged inside 21 DTE: roll out-and-down as in step 3, else buy back.
7. New layer (one per ISO week): blocked when posture is not normal; when QQQ price data is unavailable; when price_fell (last QQQ close below the close 5 sessions earlier; None when too few closes); when any open layer is challenged; when open contracts + 3 would exceed 12; when a layer was already opened this ISO week; when no qualifying contract exists; or when buying_power is below the candidate's cash_required. The candidate excludes expirations already used by open layers and is picked by pick_short_put: DTE 38 to 52, |delta| 0.05 to 0.08, strike below spot, bid at least 0.05, ask above bid, and spread at most max(0.10, 25 percent of mid); candidates sort by distance to 45 DTE, then distance to 0.05 delta, then spread, then strike.
8. Action mapping: sell_open becomes an enter intent (sell_to_open at the bid), buy_close becomes an exit intent (buy_to_close at the ask), and a roll becomes the exit leg plus the enter leg.

## Files in this repo
- Strategy module (desk sleeves/qqq_put_ladder.py, the strategy logic; CONFIG sleeve_id=qqq_put_ladder): the desk module path is sleeves/qqq_put_ladder.py.
- v3 wrapper (desk desk3/port_b5/qqq_put_ladder.py): `desk3/port_b5/qqq_put_ladder.py` in this repo (also copied at sleeves/qqq_put_ladder.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/qqq_put_ladder_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=qqq_put_ladder); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.qqq_put_ladder; cadence_s 900; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars', 'positions', 'options']; parked false. Source: muse-desk-v3/config/sleeves.json row id=qqq_put_ladder (repo copy: engines/config/sleeves.json).

## Data inputs
Option quote dicts {symbol, expiration, strike, delta, bid, ask} via context.extra["quotes"]; the layer book via context.extra["layers"]; spot via context.extra["spot"] or the last QQQ daily bar close; posture, qqq_closes (for price_fell), buying_power, equity_pending and week_opened via context.extra; positions via the snapshot.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `qqq_put_ladder` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the candidate pick: a quote at 30 DTE or at delta 0.09 is not a candidate; a 45-DTE, 0.05-delta, tradable quote is, and expirations already used by open layers are excluded.
- Check the weekly add blocks: posture not normal, QQQ down on the 5-session lookback, an already-opened ISO week, 10 or more open contracts, and buying_power below cash_required each block the new layer with no intent.
- Check management: a layer at 5 DTE is bought back (including unpriced when its quote is missing); a layer above 21 DTE that is not challenged is left alone.
- Check the challenged rule: a layer with |delta| 0.20 or spot at or below 1.03 x strike rolls out-and-down (or closes when no later contract qualifies or posture is stand_down).
- Check roll-up: inside 21 DTE, with spot above entry spot and the ask at or below half the entry credit, the layer rolls up only within the same expiration.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
