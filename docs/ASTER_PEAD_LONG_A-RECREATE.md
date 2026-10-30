# aster_pead_long_a: recreation package

Provenance: Source: Ausar R17/R18 options research (existing Test doc strategies/ausar/opt-pead.md, Source row). Per-sleeve values below are read from the desk engine SPECS entry in desk3/aster_b2.py and the desk config/sleeves.json row for aster_pead_long_a.

## What this sleeve is

An earnings-drift (PEAD) options sleeve that buys long puts three sessions after a weak earnings reaction, to ride the post-earnings drift for 10 sessions. It is a thin adapter over the desk3/aster_b2.py engine, book OPT_PEAD_LONG_A, on a $10,000 slice.

## Full algorithm

Evaluation order in desk3/aster_b2.py for SPECS entry: book=OPT_PEAD_LONG_A, family=pead, structure=long, risk=0.02, dte=(21,35), delta=(0.5,0.65), hold=10, max_debit_width=0.6, max_premium_spot=0.04, exit_rule=fixed. SLICE is 10000.0 and FEE_PER_CONTRACT is 0.65 in the engine.
1. Event qualification (producer-built PEAD event): surprise <= the 20th-percentile threshold of at least 200 prior events, spot >= 5, and mean 20-day dollar volume >= $1M. Surprise is the stock's return minus SPY's from the session before to the session after the event (existing family doc).
2. Timing: today must equal the entry session, event_date + 3 sessions. Entry window 09:35-09:40 ET; under the default-on PEAD catch-up enhancement in the engine, the same qualified event may still enter later the same session, 09:40-15:55 ET, with every other gate unchanged.
3. Contract selection: long puts with DTE 21-35 and delta 0.5-0.65, chosen by minimum (expiry, |delta - band mid|, |strike - spot|).
4. Sizing: risk_budget = 0.02 x $10,000 slice; qty = floor(risk_budget / per-contract cash debit including fees), capped by displayed size. A long entry also requires debit / (spot x 100) <= 0.04.
5. Exit (exit_rule fixed): planned exit on the 10th session counting the entry day (hold=10); pre-expiry guard exits on the session before expiry if that comes first. No stop or profit target.

## Files in this repo

- This doc: docs/ASTER_PEAD_LONG_A-RECREATE.md
- Sleeve module in Test: sleeves/aster_pead_long_a.py
- Adapter in Test: adapters3/aster_pead_long_a.py (mirrored as integration/aster_pead_long_a_adapter.py)
- Shared engine in Test: desk3/aster_b2.py (evaluate, SPECS, INPUTS_COMMON, PRODUCERS, PRODUCERS_PEAD)
- Config in Test: config/sleeves.json (row id=aster_pead_long_a); also vendored as engines/config/sleeves.json
- Existing family doc in Test: strategies/ausar/opt-pead.md

## Configuration

- Universe: names with published earnings events that pass the qualification gates below. Timeframe: 1d (event and entry sessions).
- Structure: long puts, DTE 21-35, delta 0.5-0.65, hold 10 sessions, risk fraction 0.02, premium cap 0.04 of spot (max_premium_spot), max_debit_width 0.6 (recorded in the SPECS entry; the binding long-structure cap in the engine is max_premium_spot).
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 (desk config/sleeves.json row); engine SLICE 10000.0.
- Cadence: cadence_s 300. Session: rth. bp_buffer_frac 0.02. flat_by_close false; flatten_time_et null. params: {}.
- Inputs declared in config: bars, options, positions, earnings_events.
- Parked: false (parked flag in the desk config row).

## Data inputs

Producers declared by desk3/aster_b2.py (PRODUCERS_PEAD = PRODUCERS + earnings_events):
- bars (producer name: bars): freshness SLA 900 s; the stock and SPY daily bars behind the surprise and dollar-volume gates.
- options (producer name: options_chain): freshness SLA 900 s.
- positions (producer name: broker_readback): freshness SLA 900 s.
- earnings_events (producer name: earnings_events): freshness SLA 86400 s; the producer-built PEAD events with first-publication times. The engine header records that options chain and earnings_events are not produced by v3 producers, leaving the sleeve unfed in the registry when they are absent, never fake-fed.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Place the files listed in 'Files in this repo' at the same relative paths in a desk3-compatible runtime: the adapter in `adapters3/` imports its engine from `desk3/` by the module path recorded there, so keep the repo directory layout unchanged.
3. Add or confirm the config row for this sleeve id in `config/sleeves.json` with exactly the values in the Configuration section (module, cadence_s, session, slice, bp_buffer_frac, flat_by_close, inputs, parked).
4. Wire the producers named in 'Data inputs' so the runtime view carries the declared inputs at the stated freshness; an absent input must leave the sleeve unfed (no intents), never fake-fed.
5. Entry point: call the adapter module's `evaluate(view, ctx)` function (it delegates to the engine's `evaluate(SLEEVE_ID, view, ctx)`) on the cadence in the Configuration section, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

Behavior checklist (no per-sleeve test file for this sleeve was located in the Test tree; checks derived from the algorithm section):
1. An event with surprise above the 20th-percentile threshold of its prior-event set, or with fewer than 200 prior events, produces no entry.
2. A qualified event evaluated on any session other than event_date + 3 produces no entry.
3. A qualified event with spot < 5 or mean 20-day dollar volume < $1M produces no entry.
4. A qualified event on its entry session in the entry window produces a long-put entry with DTE 21-35, delta 0.5-0.65, debit / (spot x 100) <= 0.04, and qty = floor(0.02 x 10000 / per-contract debit including the $0.65 per-contract fee), capped by displayed size.
5. An open position produces an exit intent on the 10th session counting the entry day, or on the session before expiry if that is earlier.
