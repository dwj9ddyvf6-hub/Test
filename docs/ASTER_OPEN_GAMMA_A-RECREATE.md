# aster_open_gamma_a: recreation package

Provenance: Source: Ausar R18 opening-reversal research (R5 events) (existing Test doc strategies/ausar/opt-opening-gamma.md, Source row). Per-sleeve values below are read from the desk engine SPECS entry in desk3/aster_batch1.py and the desk config/sleeves.json row for this sleeve id.

## What this sleeve is

An equity options sleeve that buys puts on the 42-name R5 list after a hot prior afternoon, when the next morning's first 5-minute bar is red and breaks its low. It is a thin adapter over the desk3/aster_batch1.py opening-gamma engine on a $10,000 slice, and it is flat by 10:00 ET on the entry day.

## Full algorithm

Evaluation order in desk3/aster_batch1.py for the gamma kind (SPECS: risk_fraction=0.02, max_premium_spot=0.025, dte=(0, 2), cadence_s=300, session=rth):
1. Prior-afternoon setup (causal R5): the last-two-hours return is at or above the 80th percentile of its trailing 252 sessions (at least 126 sessions required, per the existing family doc).
2. Morning trigger: the completed opening 5-minute bar has return < 0 and price breaks below the first-5-minute low.
3. Entry window: 09:35 <= ET < 09:45 only, and only with the opening-event clock causality checks in the engine passing.
4. Contract: long puts, delta 0.50-0.65, DTE in (0, 2); premium per contract must be <= 0.025 of spot.
5. Sizing: risk fraction 0.02 of the $10,000 slice divided by the contract debit (the family doc states risk / debit sizing).
6. Exit: flat at 10:00 ET on the entry day (or later if that exit is missed; an expiry obligation can force an earlier exit). No other exit, stop, or target.

## Files in this repo

- This doc: docs/ASTER_OPEN_GAMMA_A-RECREATE.md
- Sleeve module in Test: sleeves/aster_open_gamma_a.py
- Adapter in Test: adapters3/aster_open_gamma_a.py (mirrored as integration/aster_open_gamma_a_adapter.py)
- Shared engine in Test: desk3/aster_batch1.py (evaluate, SPECS, INPUTS_BY_KIND gamma = opening_events, options, positions; PRODUCERS)
- Config in Test: config/sleeves.json (row id=aster_open_gamma_a); also vendored as engines/config/sleeves.json
- Existing family doc in Test: strategies/ausar/opt-opening-gamma.md

## Configuration

- Universe: the 42-name R5 list (existing family doc). Timeframe: 5m opening bar; 30-minute bars for the R5 statistic (family doc).
- Structure: long puts, delta 0.50-0.65, DTE (0, 2). Risk fraction 0.02 of the slice; premium cap 0.025 of spot.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 (desk config/sleeves.json row).
- Cadence: cadence_s 300. Session: rth. bp_buffer_frac 0.02. flat_by_close false; flatten_time_et null. params: {}.
- Inputs declared in config: opening_events, options, positions.
- Parked: false (parked flag in the desk config row).

## Data inputs

Producers declared by desk3/aster_batch1.py PRODUCERS for the gamma kind:
- opening_events: the prior-afternoon R5 event and the opening-bar clocks; the engine records clock-chain, prior-afternoon R5, and 5-second break-quote freshness requirements.
- options (producer name: options_chain): freshness SLA 300 s.
- positions (producer name: broker_readback): freshness SLA 900 s.
- bars and quotes producers are also declared in the engine PRODUCERS list (bars freshness SLA 900 s; quotes 60 s).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Place the files listed in 'Files in this repo' at the same relative paths in a desk3-compatible runtime: the adapter in `adapters3/` imports its engine from `desk3/` by the module path recorded there, so keep the repo directory layout unchanged.
3. Add or confirm the config row for this sleeve id in `config/sleeves.json` with exactly the values in the Configuration section (module, cadence_s, session, slice, bp_buffer_frac, flat_by_close, inputs, parked).
4. Wire the producers named in 'Data inputs' so the runtime view carries the declared inputs at the stated freshness; an absent input must leave the sleeve unfed (no intents), never fake-fed.
5. Entry point: call the adapter module's `evaluate(view, ctx)` function (it delegates to the engine's `evaluate(SLEEVE_ID, view, ctx)`) on the cadence in the Configuration section, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

Behavior checklist (no per-sleeve test file for this sleeve was located in the Test tree; checks derived from the algorithm section):
1. A morning with no qualifying prior-afternoon R5 event produces no entry, even if the first 5-minute bar is red and breaks its low.
2. A qualifying R5 event plus a first 5-minute bar with return >= 0, or no break below its low, produces no entry.
3. A qualifying setup inside 09:35 <= ET < 09:45 produces a long-put entry with DTE in (0, 2), delta 0.50-0.65, premium <= 0.025 of spot, and size set by risk fraction 0.02 of the $10,000 slice over the debit.
4. The same setup evaluated at or after 09:45 ET produces no new entry.
5. An open position produces an exit intent at 10:00 ET on the entry day.
