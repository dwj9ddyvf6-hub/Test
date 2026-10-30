# qullamaggie_paper: Recreation package

Provenance: Source row in strategies/qullamaggie/qm-leader-breakout.md in this repo: Kristjan Kullamägi (Qullamaggie), "My 3 timeless setups"; three desk implementations.

## What this sleeve is
This is a paper-only carrier sleeve: an upstream reconstruction engine scans for long breakouts and hands this sleeve accepted proposals, which it carries onto the paper book inside a $100,000 cumulative budget, deduped per session and symbol. The sleeve evaluates no exits in-signal; a filled position exits through the protection stop placed from the proposal's stop. Sources: sleeves/qullamaggie_paper.py and desk3/port_b5/qullamaggie_paper.py on the desk.

## Full algorithm
Constants (sleeves/qullamaggie_paper.py): ACCOUNT qullamaggie_paper, BUDGET_USD 100,000, AURELIA_SYMBOLS {QQQ, TQQQ, GLD}, UNIVERSE (NVDA, AVGO, META, AMZN, AAPL, MSFT, GOOGL, TSLA, AMD, NFLX, COST, LLY, JPM, CAT, GE, PLTR, CRWD, AMAT, MU, PANW). CONFIG: cadence_s 300, universe = UNIVERSE, state_schema {orders}, risk_pct None.
Evaluation order in signal(): with no context.extra["proposals"], emit nothing. For each proposal {symbol, side, setup, quantity, entry, stop}, accept() applies, in order:
1. Malformed symbol or side: refuse (malformed).
2. Long only: side must be 1 and setup must not be parabolic_short (not_a_long_breakout). Episodic pivots without a first-public timestamp stay closed upstream in the engine, not here.
3. QQQ, TQQQ and GLD are refused (aurelia_owns_symbol).
4. Dedupe by client id qulla-{session}-{symbol}-buy against the served order rows: a repeat is refused (duplicate).
5. Missing, unreadable or non-positive stop: refuse (missing_stop). A position that cannot exit must never enter, because this sleeve has no in-signal exit.
6. Enhancement gate (on by default): a stop at or above the entry price is refused (stop_not_below_entry).
7. Budget: entry price must be positive, quantity at least 1, and quantity x entry must fit within $100,000 minus the spent total (the sum of qty x entry over prior order rows with status sent); otherwise blocked_budget.
An accepted proposal emits one enter intent at the proposal quantity, price_hint = entry (2dp), stop = the proposal stop (2dp), and adds its notional to the running spent total for the rest of the pass. The upstream engine (a pandas point-in-time scan) is a core Data / research product and is not part of this sleeve.

## Files in this repo
- Strategy module (desk sleeves/qullamaggie_paper.py, the strategy logic; CONFIG sleeve_id=qullamaggie_paper): the desk module path is sleeves/qullamaggie_paper.py.
- v3 wrapper (desk desk3/port_b5/qullamaggie_paper.py): `desk3/port_b5/qullamaggie_paper.py` in this repo (also copied at sleeves/qullamaggie_paper.py); its evaluate(view, ctx) delegates through the shared context runner.
- v3 adapter / integration copy: `integration/qullamaggie_paper_adapter.py`.
- Shared engine files (engines_map.json): `engines/desk3/port_b5/_ctx.py` (desk desk3/port_b5/_ctx.py, vendored).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=qullamaggie_paper); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module desk3.port_b5.qullamaggie_paper; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['positions', 'qulla']; parked false. Source: muse-desk-v3/config/sleeves.json row id=qullamaggie_paper (repo copy: engines/config/sleeves.json).

## Data inputs
Accepted proposals via context.extra["proposals"] (list of {symbol, side, setup, quantity, entry, stop}) from the upstream reconstruction engine (the qulla producer declared in the roster inputs); sleeve_state {orders: [prior order rows]} via context.extra, used for dedupe and spent math. The bars argument is not used by the acceptance law.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `qullamaggie_paper` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check acceptance order: a short-side or parabolic_short proposal, a QQQ proposal, and a duplicate client id each produce no intent, each for its named reason.
- Check the stop law: a proposal with no stop, a zero stop, and (gate ON) a stop equal to its entry each produce no intent.
- Check the budget: proposals whose cumulative qty x entry would exceed $100,000 against the served sent orders are refused, and an accepted proposal raises the spent total for later proposals in the same pass.
- Check the intent: an accepted proposal emits exactly one enter intent at its quantity, entry price hint and stop.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
