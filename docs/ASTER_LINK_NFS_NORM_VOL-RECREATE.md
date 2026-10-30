# aster_link_nfs_norm_vol: recreation package

Provenance: Source: Ausar R17/R18 crypto research, run as the R19 native-spot books (existing Test doc strategies/ausar/r19-crypto-breakout.md, Source row). Per-sleeve values below are read from the desk engine SPECS entry in desk3/aster_batch13.py and the desk config/sleeves.json row for aster_link_nfs_norm_vol.

## What this sleeve is

A Binance spot crypto sleeve that buys LINKUSDT on a 4-hour breakout only when perpetual funding is negative (a negative-funding squeeze), and exits when funding normalizes. It is a thin adapter over the desk3/aster_batch13.py engine on a $10,000 slice, evaluated every 4 hours around the clock.

## Full algorithm

Evaluation order in desk3/aster_batch13.py for SPECS entry: kind=crypto, family=negative_funding_squeeze, symbol=LINKUSDT, exit_policy=normalization, capacity=volume1pct, deadline_h=96, ticket=None; fee 10 bp (TSV params recorded in the engine header).
1. Exits first, for an open position: exit when an available funding observation is >= 0 (normalization), or at the 96 h maximum deadline; the deadline fires even when funding is missing. The engine header records the 96 h deadline as an installed assumption (FIDELITY-LEDGER ASTER-B13).
2. Entry, only when flat: a completed 4h close is above the highest high of the prior 20 bars AND an actually available funding observation is < 0.
3. Sizing: capacity volume1pct: the buy is capped at 1% of the volume of the 4h bar (the existing family doc notes the v3 engine reads the bar before the signal bar for this cap), net of the 10 bp fee.
4. Long only, one position per book, no price stop.

## Files in this repo

- This doc: docs/ASTER_LINK_NFS_NORM_VOL-RECREATE.md
- Sleeve module in Test: sleeves/aster_link_nfs_norm_vol.py
- Adapter in Test: adapters3/aster_link_nfs_norm_vol.py (mirrored as integration/aster_link_nfs_norm_vol_adapter.py)
- Shared engine in Test: desk3/aster_batch13.py (evaluate, SPECS, INPUTS_CRYPTO, PRODUCERS)
- Config in Test: config/sleeves.json (row id=aster_link_nfs_norm_vol); also vendored as engines/config/sleeves.json
- Existing family doc in Test: strategies/ausar/r19-crypto-breakout.md

## Configuration

- Universe: LINKUSDT (Binance spot). Timeframe: 4h bars.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 (desk config/sleeves.json row); capacity volume1pct; fee 10 bp.
- Cadence: cadence_s 14400. Session: always. bp_buffer_frac 0.02. flat_by_close false; flatten_time_et null. params: {}. timeout_s null.
- Inputs declared in config: bars, funding, positions.
- Parked: false (parked flag in the desk config row).

## Data inputs

Inputs declared by desk3/aster_batch13.py (INPUTS_CRYPTO = bars, funding, positions):
- bars (producer name: bars): 4h bars for LINKUSDT; freshness SLA 900 s.
- funding: funding observations for the squeeze filter and the normalization exit. The engine file records that no funding producer is registered in v3 yet, so this sleeve is visibly unfed in the registry until that producer lands.
- positions (producer name: broker_readback): freshness SLA 900 s.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Place the files listed in 'Files in this repo' at the same relative paths in a desk3-compatible runtime: the adapter in `adapters3/` imports its engine from `desk3/` by the module path recorded there, so keep the repo directory layout unchanged.
3. Add or confirm the config row for this sleeve id in `config/sleeves.json` with exactly the values in the Configuration section (module, cadence_s, session, slice, bp_buffer_frac, flat_by_close, inputs, parked).
4. Wire the producers named in 'Data inputs' so the runtime view carries the declared inputs at the stated freshness; an absent input must leave the sleeve unfed (no intents), never fake-fed.
5. Entry point: call the adapter module's `evaluate(view, ctx)` function (it delegates to the engine's `evaluate(SLEEVE_ID, view, ctx)`) on the cadence in the Configuration section, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

Behavior checklist (no per-sleeve test file for this sleeve was located in the Test tree; checks derived from the algorithm section):
1. A completed 4h close above the prior 20 bars' highest high with the latest available funding >= 0 produces no entry.
2. The same breakout with an available funding observation < 0 produces one long entry, sized at no more than 1% of the reference 4h bar volume, net of the 10 bp fee.
3. Holding a position, a funding observation >= 0 produces an exit intent.
4. Holding a position for 96 h produces an exit intent even when funding data is missing.
5. With no funding observation available at all, no entry is produced (the entry requires an actually available funding observation < 0).
