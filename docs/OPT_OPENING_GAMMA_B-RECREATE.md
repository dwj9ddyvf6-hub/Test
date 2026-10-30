# OPT_OPENING_GAMMA_B: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Opening-range options - long, 0.5% risk", type options directional, family opening_gamma. Algorithm grade FULL in the accounting. Aliases: `OPT_OPENING_GAMMA_B` (md2_ausar_map "present in roster"; ausar_deployed "mode=independent_local_paper running=False"; femto land-wt "present in roster"), `ausar_pb15` (md2_catalog "replaced", ausar_map "present in roster"; merge tier A: the ausar_map row for ausar_pb15 lists the r19 link OPT_OPENING_GAMMA_B), and `ausar_r19_OPT_OPENING_GAMMA_B` (md2_catalog "blocked"; merge tier C on the identical normalised form and opening_gamma family overlap).
- Accounting parameters for this book: structure long, DTE [7, 14], delta [0.5, 0.65], hold_sessions 1, risk_fraction 0.005, max_premium_spot 0.015, symbols [] (no fixed symbol list in the accounting parameters; the family doc's 42-name R5 list is the universe).
- Accounting entry text: requires actual completed opening bars followed by an ordered breakout; the free variant uses a prior-day return context proxy, without claiming dealer gamma data. Accounting exit text: close the option package at 10:00 ET on the entry day; a missed exit remains due at the next opportunity; earlier expiry or assignment-risk obligations still apply.
- Test family doc: `strategies/ausar/opt-opening-gamma.md` (source: Ausar R18 opening-reversal research, R5 events).
- Code search: the running code was found in Test (paths in Files). Silicon, quant-research-backup and Midna trees were searched for this book id and the open_gamma sleeves; no matching file was found there.

## What this strategy is

An equity-options sleeve that buys short-dated puts on the 42-name R5 list after a hot final two hours of the prior session, when the next morning's first 5-minute bar is red and breaks its low. This is variant B: DTE (7, 14), risk 0.5% of NAV. In Test it runs as `aster_open_gamma_b`, a thin adapter over the opening-gamma kind in `desk3/aster_batch1.py`, on a $10,000 slice, flat by 10:00 ET on the entry day.

## Full algorithm

Evaluation order in `desk3/aster_batch1.py` for the gamma kind, SPECS row for aster_open_gamma_b (book OPT_OPENING_GAMMA_B): risk_fraction 0.005, max_premium_spot 0.015, dte (7, 14), delta (0.50, 0.65), cadence 300 s, session rth:

1. Prior-afternoon setup (causal R5): the last-two-hours return is at or above the 80th percentile of its trailing 252 sessions (at least 126 sessions required, per the family doc).
2. Morning trigger: the completed opening 5-minute bar has return < 0 and price breaks below the first-5-minute low (an ordered breakout of actual completed opening bars; the accounting's free variant uses a prior-day return context proxy and does not claim dealer gamma data).
3. Entry window: 09:35 <= ET < 09:45 only, and only with the opening-event clock causality checks in the engine passing.
4. Contract: long puts, delta 0.50-0.65, DTE in (7, 14); premium per contract must be at most 0.015 of spot.
5. Sizing: risk fraction 0.005 of the $10,000 slice divided by the contract debit.
6. Exit: flat at 10:00 ET on the entry day; a missed exit remains due at the next opportunity; an expiry or assignment-risk obligation can force an earlier exit. No other exit, stop or target is in the record or the code.

## Files in this repo

- This doc: `docs/OPT_OPENING_GAMMA_B-RECREATE.md`
- Sleeve code (already in Test): `sleeves/aster_open_gamma_b.py`, with copies at `adapters3/aster_open_gamma_b.py` and `integration/aster_open_gamma_b_adapter.py`. The wrapper docstring names book OPT_OPENING_GAMMA_B and engine `desk3/aster_batch1.py`.
- Shared engine that runs the logic: `desk3/aster_batch1.py` (evaluate, SPECS, INPUTS_BY_KIND gamma = opening_events, options, positions; PRODUCERS).
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `aster_open_gamma_b`.
- Family doc: `strategies/ausar/opt-opening-gamma.md`; rule lines `docs/verify/ausar.md`.
- An earlier recreation package for the same Test sleeve exists at `docs/ASTER_OPEN_GAMMA_B-RECREATE.md`; this package is the one for the canonical book id OPT_OPENING_GAMMA_B.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.

## Configuration

- Test sleeve id: `aster_open_gamma_b`; roster module `adapters3.aster_open_gamma_b`; cadence 300 seconds; session rth.
- Universe: the 42-name R5 list (family doc). Timeframe: 5-minute opening bar; 30-minute bars for the R5 statistic (family doc).
- Slice capital and cash $10,000; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; parked false.
- Inputs declared in config: opening_events, options, positions. Structure: long puts, delta 0.50-0.65, DTE (7, 14), risk fraction 0.005, premium cap 0.015 of spot.

## Data inputs

- 30-minute bars for the R5 statistic; the first 5-minute bar; OPRA quotes (family doc).
- Declared producers (engine): opening_events (the prior-afternoon R5 event and opening-bar clocks; the engine records clock-chain, prior-afternoon R5 and 5-second break-quote freshness requirements), options_chain (freshness 300 s), broker_readback (freshness 900 s); bars (900 s) and quotes (60 s) producers are also declared in the engine PRODUCERS list. An absent input leaves the sleeve unfed, never fake-fed.

## Install and run

1. Clone the Test repo.
2. Place `desk3/aster_batch1.py` under `desk3/` and the wrapper as `sleeves/aster_open_gamma_b.py` (or the `adapters3/` copy), keeping the repo layout so imports resolve.
3. Register the roster row for `aster_open_gamma_b` from `config/sleeves.json` with the Configuration values above.
4. Wire the producers named in Data inputs so the view carries opening_events, options and positions at the stated freshness.
5. Call the wrapper's `evaluate(view, ctx)` every 300 seconds in RTH (it delegates to `desk3.aster_batch1.evaluate` for this sleeve id); entries only inside 09:35-09:45 ET, exits at 10:00 ET the same day.
6. Verify against the Verification checklist before any live use. Paper only.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- A morning with no qualifying prior-afternoon R5 event produces no entry, even if the first 5-minute bar is red and breaks its low.
- A qualifying R5 event plus a first 5-minute bar with return >= 0, or no break below its low, produces no entry.
- A qualifying setup inside 09:35 <= ET < 09:45 produces a long-put entry with DTE in (7, 14), delta 0.50-0.65, premium at most 0.015 of spot, sized by risk fraction 0.005 of the $10,000 slice over the debit; the same setup at or after 09:45 ET produces no new entry.
- An open position produces an exit intent at 10:00 ET on the entry day (or at the next opportunity if missed, earlier only on an expiry or assignment obligation).
