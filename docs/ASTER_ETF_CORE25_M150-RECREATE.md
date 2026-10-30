# aster_etf_core25_m150: Recreation Package

## Provenance

Provenance: Ausar R17/R18 ETF research, frozen as the R19 ETF books (Source row in `strategies/ausar/r19-etf.md`).

## What this sleeve is

This sleeve is a monthly R19 ETF rotation using policy CORE25 at gross 1.5: it holds QQQ and / or the 126-session momentum leader of a 14-ETF basket. It is a thin wrapper in `adapters3/aster_etf_core25_m150.py` that delegates to the shared engine `desk3/aster_batch8.py`. Its designed exit is the next monthly selection; there is no price stop or target.

## Full algorithm

Evaluation order in `desk3/aster_batch8.py` _etf(), as applied to ETF_SPECS['aster_etf_core25_m150'] = policy 'CORE25', gross 1.5:

1. Timing: intents are emitted only inside the 09:35-09:40 America/New_York window. Aware clock stamps are converted to ET; naive stamps are read as ET (engine enhancement ENH-ETWIN8, on by default).
2. Monthly guard: when positions are held, no `rebalance_due` flag is set in extra, and every held position was entered in the current month, no intents are emitted.
3. Leader selection: basket = QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. For each symbol with at least 127 daily bars and a positive close 127 bars back, score = close[-1] / close[-127] - 1 (the 126-session return). The leader is the best score; ties break alphabetically.
4. CORE25 weights: 75% of the target portfolio in QQQ plus 25% in the leader; if QQQ is the leader the two portions combine into 100% QQQ.
5. Targets: whole shares, int(gross x equity x weight / price), where equity is account_value or net_value from extra when present, otherwise the slice capital (default $10,000), and price is the last daily close. A target price at or below zero emits nothing. Gross is applied as coded and never silently capped in the sleeve; for gross above 1 the dispatcher buying-power check governs execution.
6. Order of operations: sells first (held above target), then buys (target above held). Intents are market, day; entries are buy_to_open, reductions and full exits are sell_to_close.
7. Exits: no price stop and no price target. A holding above its new target is reduced; a holding with target zero is exited in full at the next monthly selection.

## Files in this repo

- Sleeve module / adapter (same wrapper content in the repo):
- `adapters3/aster_etf_core25_m150.py`
- `sleeves/aster_etf_core25_m150.py`
- `integration/aster_etf_core25_m150_adapter.py`
- Shared engine: `desk3/aster_batch8.py` (desk path `desk3/aster_batch8.py`)
- Config: `config/sleeves.json` and `engines/config/sleeves.json` (row id `aster_etf_core25_m150`)
- Existing family doc: see the Provenance source doc path named in the audit record for this sleeve.

## Configuration

- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. Timeframe: daily bars, monthly rebalance.
- Module: `adapters3.aster_etf_core25_m150`; cadence_s 300; session 'rth'.
- Slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}.
- Inputs declared in config: bars, positions, quotes. Parked: false.
- Engine spec: policy CORE25, gross 1.5.

## Data inputs

Declared inputs: bars, positions, quotes (engine INPUTS_ETF). Producers named in the engine: bars (freshness_sla_s 900), broker_readback (900, outputs positions), quotes (60, outputs quotes).

## Install and run

1. Place the files listed in 'Files in this repo' at their repo paths in a fresh desk tree, keeping `desk3/`, `adapters3/`, `sleeves/` and `integration/` side by side so the wrapper imports resolve exactly as in the repo.
2. Register the config row for `aster_etf_core25_m150` from `config/sleeves.json` (also vendored as `engines/config/sleeves.json`) with the exact values in the Configuration section; do not change cadence, slice or parked state.
3. Wire the producers named in 'Data inputs' so the declared inputs are present in the evaluation `view` at the stated freshness; a missing input must leave the sleeve unfed, never fake-fed.
4. Specific entry point: `from adapters3.aster_etf_core25_m150 import evaluate; intents = evaluate(view, ctx)`, where `view` carries daily `bars` for the basket, `positions`, `quotes`, `now` and `slice` / extra account values.
5. First evaluation: call the wrapper entry point `evaluate(view, ctx)` for this sleeve (see the specific call in the preceding step), confirm no intent is emitted outside the stated window / gates, then let the desk dispatcher call it on its cadence and route returned intents to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Outside the 09:35-09:40 ET window, or when the monthly guard shows this month's rebalance complete, no intents are emitted.
- Given a basket where one non-QQQ symbol has the best 126-session return, targets are 75% QQQ and 25% leader at gross 1.5 of equity, in whole shares rounded down; when QQQ leads, the target is 100% QQQ at that gross.
- Sells are emitted before buys; a holding whose new target is zero is exited in full at the next monthly selection.
- No intent ever carries a price stop or profit target.
- The wrapper delegates to the named shared engine with the exact sleeve id, and no rule, threshold or sizing value differs from the values stated above.
- A missing or stale declared input emits no entry intent.
