# OPT_PEAD_VERTICAL_B: Recreation package

## Provenance

- Canonical id: `OPT_PEAD_VERTICAL_B`; canonical name: Post-earnings response · vertical, 0.5% risk; aliases: OPT_PEAD_VERTICAL_B, ausar_pb19, ausar_r19_OPT_PEAD_VERTICAL_B.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type options directional, family pead, algorithm grade PARTIAL; accounting gaps: exit rule not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Post-earnings response · vertical, 0.5% risk" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; matching material only as noted in Provenance); dwj9ddyvf6-hub/Midna (recursive tree; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/aster_pead_vertical_b.py + desk3/aster_b2.py. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Post-earnings response (PEAD) options sleeve, vertical structure, 0.5% risk variant: after a weak earnings reaction it buys puts or put spreads three sessions later to ride the drift. Accounting grade PARTIAL: the accounting recorded no exit rule; the code's fixed exit rule is stated below, and the code is the truth.

## Full algorithm

From `desk3/aster_b2.py` SPECS entry: book="OPT_PEAD_VERTICAL_B", family="pead", structure="vertical", risk=0.005, dte=(21,35), delta=(0.5,0.65), hold=10, max_debit_width=0.45, max_premium_spot=0.02, exit_rule="fixed". Engine SLICE is 10000.0 and FEE_PER_CONTRACT is 0.65.

1. Event qualification (producer-built PEAD event, per `strategies/ausar/opt-pead.md` in this repo): surprise = the stock's return minus SPY's from the session before to the session after the event; trades when surprise is at or below the 20th percentile of at least 200 prior events (prior four quarters), price >= $5, and 20-day dollar volume >= $1M. The accounting entry text adds: an observed earnings occurrence and a causal subsequent price response are required; a future calendar date alone cannot trigger an entry.
Timing: today must equal the entry session, event_date + 3 sessions. Entry window 09:35-09:40 ET; under the default-on PEAD catch-up enhancement in the engine (ENH-B5-PEAD-CATCHUP-20261024), the same qualified event may still enter later the same session, 09:40-15:55 ET, with every other gate unchanged.
2. Contract selection: put verticals with DTE 21-35 and delta 0.5-0.65 on the long leg, chosen by minimum (expiry, |delta - band mid|, |strike - spot|); the short leg is the strike nearest spot x 0.95 (family card).
3. Sizing: risk_budget = 0.005 x $10,000 slice; qty = floor(risk_budget / per-contract cash debit including the $0.65 per-contract fee), capped by displayed size. The family card phrases the same cap as risk = min(NAV x 0.5%, the 5% reserve, cash) / package debit. An entry also requires debit / (spot x 100) <= 0.02 (max_premium_spot).
4. Exit (exit_rule "fixed"): planned exit on the 10th session counting the entry day (hold=10); pre-expiry guard exits on the session before expiry if that comes first. No stop or profit target is recorded in the code for this book.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve wrapper (already in Test): `sleeves/aster_pead_vertical_b.py` (also `adapters3/aster_pead_vertical_b.py`, `integration/aster_pead_vertical_b_adapter.py`); delegating to `desk3/aster_b2.evaluate`, with INPUTS = INPUTS_COMMON + ("earnings_events",) and PRODUCERS_PEAD.
- Shared engine (already in Test): `desk3/aster_b2.py` (SPECS entry book=OPT_PEAD_VERTICAL_B).
- Existing family card (already in Test): `strategies/ausar/opt-pead.md`; existing recreation doc for the aster id: `docs/ASTER_PEAD_VERTICAL_B-RECREATE.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical name.

## Configuration

- Universe: names with published earnings events passing the qualification gates. Timeframe: 1d (event and entry sessions).
- Structure vertical, DTE 21-35, delta 0.5-0.65, hold 10 sessions, risk_fraction 0.005, max_premium_spot 0.02, max_debit_width 0.45.
- Slice capital_usd 10000.0 / cash_usd 10000.0; engine SLICE 10000.0; cadence_s 300; session rth; bp_buffer_frac 0.02; flat_by_close false; params {}; inputs bars, options, positions, earnings_events; parked false (per the aster recreation doc's roster reading for this family).

## Data inputs

Producers declared by `desk3/aster_b2.py` (PRODUCERS_PEAD = PRODUCERS + earnings_events): bars (900 s SLA; stock and SPY daily bars behind the surprise and dollar-volume gates), options_chain (900 s), broker_readback positions (900 s), earnings_events (86400 s; producer-built PEAD events with first-publication times). The engine header records that the options chain and earnings_events are not produced by v3 producers, leaving the sleeve unfed when they are absent, never fake-fed. Earnings calendar with first-publication times; SIP daily bars of the stock and SPY (family card).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / registry inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (cash, core, or no intent), never fake-fed.
5. Call the module's evaluate / signal entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- An event with surprise above the 20th-percentile threshold of its prior-event set, or with fewer than 200 prior events, produces no entry.
- A qualified event evaluated on any session other than event_date + 3 produces no entry.
- A qualified event with spot < 5 or mean 20-day dollar volume < $1M produces no entry.
- A qualified event on its entry session in the entry window produces a vertical entry with DTE 21-35, delta 0.5-0.65, debit / (spot x 100) <= 0.02, and qty = floor(0.005 x 10000 / per-contract debit including the $0.65 fee), capped by displayed size.
- An open position produces an exit intent on the 10th session counting the entry day, or on the session before expiry if that is earlier.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
