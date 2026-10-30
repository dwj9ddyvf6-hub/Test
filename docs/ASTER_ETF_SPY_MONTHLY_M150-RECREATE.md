# aster_etf_spy_monthly_m150: recreation package

Provenance: Source: Ausar R17/R18 ETF research, frozen as the R19 ETF books (existing Test doc strategies/ausar/r19-etf.md, Source row). Per-sleeve values below are read from the desk engine SPECS entry in desk3/aster_etf.py (SPY sleeves: the ETF_SPECS entry in desk3/aster_batch11.py, which registers into desk3/aster_etf.py SPECS) and the desk config/sleeves.json row for this sleeve id.

## What this sleeve is

An Aster R19 ETF control book that holds {"SPY": 1.0} under policy SPY_MONTHLY at gross 1.5, rebalanced monthly. It runs on the shared desk3/aster_etf.py engine as a thin adapter sleeve on a $10,000 slice. It is one of the fixed-weight ETF books that run beside the momentum leader rotation as controls.

## Full algorithm

This is a MONTHLY sleeve: it acts only on initial allocation (flat book) or when a holding's entry month differs from the session month. Evaluation order in desk3/aster_etf.py evaluate(): (1) read this sleeve's SPECS entry; (2) check the time gate: the primary window is 09:35-09:40 ET (aware timestamps are converted to America/New_York; naive stamps are read as ET); a monthly sleeve whose rebalance is due may also execute the same targets later the same session, 09:40-15:55 ET, under the default-on catch-up enhancement (extra["aster_etf_enh"] {"catchup": true}); (3) compute targets; (4) emit sells before buys.
- Policy: SPY_MONTHLY. Frequency: MONTHLY. Gross: 1.5. Weights: {"SPY": 1.0}.
- Target sizing: whole shares, floor(weight x gross x equity / price) per symbol, where equity is the sleeve slice; sells are emitted before buys.
- No price stop and no profit target. The 15 bps per side figure (cost_bps 15) is source-book accounting, not an order field.
- Exit rules: monthly sleeves sell whatever has left the target before buying the new target; a symbol no longer in the weights is sold in full at rebalance.

## Files in this repo

- This doc: docs/ASTER_ETF_SPY_MONTHLY_M150-RECREATE.md
- Sleeve module in Test: sleeves/aster_etf_spy_monthly_m150.py
- Adapter in Test: adapters3/aster_etf_spy_monthly_m150.py (mirrored as integration/aster_etf_spy_monthly_m150_adapter.py)
- Shared engine in Test: desk3/aster_etf.py (evaluate, SPECS, INPUTS, PRODUCERS)
- Additional engine in Test: desk3/aster_batch11.py (ETF_SPECS for the SPY sleeves, registered into desk3/aster_etf.py SPECS). Audit note: the audit record for this sleeve lists desk3/contract.py in its transitive engine set; engines_map.json records desk3/contract.py with repo path engines/desk3/contract.py and status gate_blocked, so that file is not present in the repo under desk3/.
- Config in Test: config/sleeves.json (row id=aster_etf_spy_monthly_m150); also vendored as engines/config/sleeves.json
- Existing family doc in Test: strategies/ausar/r19-etf.md

## Configuration

- Universe / weights: {"SPY": 1.0} (policy SPY_MONTHLY).
- Timeframe: 1d bars; rebalance frequency MONTHLY.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 (desk config/sleeves.json row); target shares = floor(weight x gross x equity / price), gross 1.5.
- Cadence: cadence_s 300. Session: rth. bp_buffer_frac 0.02. flat_by_close false; flatten_time_et null. params: {}.
- Inputs declared in config: bars, positions, quotes.
- Parked: false (parked flag in the desk config row).

## Data inputs

Producers declared by desk3/aster_etf.py PRODUCERS, consumed through the runtime view:
- bars (producer name: bars): daily bars keyed as `<SYM>|1Day`, `<SYM>|1D`, or `<SYM>`; freshness SLA 900 s. Absent bars means no intents (unfed upstream).
- positions (producer name: broker_readback): current holdings for this sleeve; freshness SLA 900 s.
- quotes (producer name: quotes): freshness SLA 60 s.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Place the files listed in 'Files in this repo' at the same relative paths in a desk3-compatible runtime: the adapter in `adapters3/` imports its engine from `desk3/` by the module path recorded there, so keep the repo directory layout unchanged.
3. Add or confirm the config row for this sleeve id in `config/sleeves.json` with exactly the values in the Configuration section (module, cadence_s, session, slice, bp_buffer_frac, flat_by_close, inputs, parked).
4. Wire the producers named in 'Data inputs' so the runtime view carries the declared inputs at the stated freshness; an absent input must leave the sleeve unfed (no intents), never fake-fed.
5. Entry point: call the adapter module's `evaluate(view, ctx)` function (it delegates to the engine's `evaluate(SLEEVE_ID, view, ctx)`) on the cadence in the Configuration section, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

Behavior checklist (no per-sleeve test file for this sleeve was located in the Test tree; checks derived from the algorithm section):
1. Outside 09:35-09:40 ET, with no monthly rebalance due under the catch-up rule, evaluate returns no intents.
2. In the 09:35-09:40 ET window on a session where a monthly rebalance is due, evaluate returns intents targeting floor(1.0 x 1.5 x equity / price) whole SPY shares.
3. When the book already holds exactly the target SPY share count in the current month, evaluate returns no intents.
4. With bars absent for a target symbol, evaluate returns no intents for that symbol (unfed, not an error fill).
5. Sells are emitted before buys in the same evaluation, quantities are whole shares, and no price stop or target is attached to any intent.
