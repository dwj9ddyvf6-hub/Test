# vix_hedge: Recreation package

Provenance: The old Alpaca swing desk, via Femto-lean (Source row in strategies/femto/femto-vix-hedge.md in this repo).

## What this sleeve is
This sleeve is portfolio tail insurance: when the market is complacent (VIX under 16, or the last VIX close in the bottom quarter of its last 30 closes) it buys one cheap VXX call about 20 percent out of the money and about 90 days out, sized at 1 percent of equity in premium, and sells it on a doubling, a VIX spike over 30, or at 21 days to expiry. It loses money most quarters by design and is deliberately exempt from the drawdown brake. Sources: desk sleeves/vix_hedge.py (VIX_LEVEL_COMPLACENT=16.0, VIX_PCTL_LOOKBACK=30, VIX_PCTL_COMPLACENT=25.0, VIX_EXIT_SPIKE=30.0, HEDGE_UNDERLYING=VXX, DTE_MIN=60, DTE_MAX=110, DTE_TARGET=90, DTE_FLOOR=21, DELTA_STRIKE_OTM=1.20, SPREAD_GATE_FRAC=0.20, HEDGE_RISK_FRACTION=0.01, MAX_HEDGES=1, PROFIT_TARGET_MULT=2.0, BRAKE_EXEMPT=True; CONFIG sleeve_id=vix_hedge, cadence_s=300, universe=(VXX,), risk_pct=0.01) and desk adapters/vix_hedge.py (INPUTS, PRODUCERS, DEFAULT_EQUITY=11000.0).

## Full algorithm
Evaluation order in desk sleeves/vix_hedge.py VixHedge.signal(bars, slice_state, context). This sleeve's roster module is adapters.vix_hedge (not adapters3): the adapter builds vix_closes from the snapshot's VIX / ^VIX bars, chains and quotes from the options input, and sleeve_state from broker positions.
1. Complacency read (fail closed): vix_complacent over extra[vix_closes] (oldest to newest): vix = the last close; percentile = the share of the last 30 closes strictly below the last close, times 100. Complacent iff vix < 16.0 OR percentile < 25.0. No VIX closes means NOT complacent.
2. Adopted-import enhancement (ENH, default ON; OFF via extra[vix_hedge_improve][adopt_imported_position]=False): the broker-imported hedge recorded in the module (ADOPTED_IMPORT: occ VXX261218C00020000, 8 contracts, expiry 2026-12-18, entry_premium 1.10) is completed into, or adopted as, the position of record when the state or extra[vix_hedge_import] carries that OCC.
3. Exits first and never gated: if a position is held with qty > 0, compute its quote mid (when two-sided), its DTE from its expiry vs the session date, and exit_due in this order: (a) profit target: current value (mid x contracts x 100) at or above 2.0 x total debit (total debit = entry_debit / debit, else entry_premium x contracts x 100, with qty standing in for contracts when only qty was recorded) gives profit_target_100pct; (b) vix > 30.0 gives vol_spike_take_profit; (c) DTE at or below 21 gives dte_floor_21. Any due rule emits one full exit Intent on VXX at round(spot, 2), reason naming vix_hedge exit, the rule and the OCC. A held position returns after this check in all cases (max 1 hedge, never add).
4. Entry gate: require complacent, equity > 0 and spot > 0 (spot = the last VXX daily bar close).
5. Vehicle (pick_hedge_call): group the VXX call chain by expiry; keep expiries with DTE in [60, 110]; per expiry take the strike nearest 1.20 x spot (the documented ~25-delta proxy; no Greeks on the chain); order expiries by closeness to 90 DTE; the first candidate with a two-sided quote (bid > 0, ask >= bid) whose (ask - bid) / mid is at or below 0.20 wins. No candidate means no_hedge_vehicle: fail closed, do nothing.
6. Sizing and entry: contracts = floor((equity x 0.01) / (ask x 100) + 1e-9); 0 means no entry. Emit one enter Intent on VXX with that quantity, price_hint = round(spot, 2), and a reason naming vix_hedge long_call with the OCC, strike, expiry, DTE, ask, VIX, percentile, the 60-110 DTE window, the nearest(1.20 x spot) strike rule and brake_exempt=tail_hedge.

## Files in this repo
- Sleeve module: sleeves/vix_hedge.py (strategy logic, CONFIG and all constants above; it carries its own local SleeveConfig / Intent contract, re-expressing the v2 core.sleeve import).
- Adapter: adapters/vix_hedge.py (SLEEVE_ID=vix_hedge, INPUTS=(bars, options, positions), PRODUCERS bars / options / positions each with freshness_sla_s=900, DEFAULT_EQUITY=11000.0). There is no adapters3/vix_hedge.py: the roster module is adapters.vix_hedge.
- Existing strategy doc: strategies/femto/femto-vix-hedge.md.
- Config: engines/config/sleeves.json (row id=vix_hedge, which also carries the producers array), also at config/sleeves.json.

## Configuration
Module adapters.vix_hedge; cadence_s 300; session rth; slice capital_usd 11000.0, cash_usd 11000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, options, positions]; producers bars, options and positions, each freshness_sla_s 900; parked false. Universe: VXX calls only; timeframe daily (VIX closes and VXX spot), with the roster cadence checking every 300 seconds. Source: muse-desk-v3/config/sleeves.json row id=vix_hedge.

## Data inputs
Inputs are bars, options and positions, each with a 900-second freshness SLA in the adapter's PRODUCERS. Via context.extra the sleeve consumes: vix_closes (the ^VIX daily closes, oldest to newest; price-only Yahoo use is the standing desk exception named in the module), chains {VXX: [{symbol, strike, expiration}]} (calls), quotes {OCC: {bid, ask}}, and sleeve_state {VXX: {position}}. Bars supply the VXX spot (last close) and the VIX closes (the adapter reads the VIX / ^VIX bar series from the bars input).

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/, for example engines/desk3/enhance26.py is desk3/enhance26.py on a fresh desk; a sleeves/muse/core/ path is the same path on a fresh desk).
2. Register the config row for `vix_hedge` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters/vix_hedge.py, whose evaluate builds the v2 context and runs sleeves/vix_hedge.py signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- Fixture with VIX closes ending at 15.0, no held position, equity $11,000, VXX spot 20.00 and a 90-DTE expiry carrying a strike at 24.00 (1.20 x spot) quoted 1.00 / 1.10: exactly one enter intent, contracts = floor((11000 x 0.01) / (1.10 x 100) + 1e-9) = 1, reason naming brake_exempt=tail_hedge.
- Fixture with no VIX closes, or with VIX at 20 and its percentile at 50: no entry (not complacent, fail closed).
- Fixture with a held call whose mid values it at twice its total debit: a full profit_target_100pct exit; the same position with VIX above 30 exits as vol_spike_take_profit, and at 21 DTE or less as dte_floor_21, in that precedence.
- Fixture whose only in-window expiries carry spreads wider than 20 percent of mid: no entry (no hedge vehicle).
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
