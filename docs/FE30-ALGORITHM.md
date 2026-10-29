Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE30 - Crypto liquidity/crowding squeeze risk - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE30; it does not duplicate the shared code.
- **Family:** Crypto
- **Target:** liquidation/squeeze risk (target unit: binary_squeeze_event)
- **Horizon:** intraday-5 sessions
- **Forecast unit:** risk_score_heuristic
- **Score kind:** risk (uncalibrated_risk_rank_only)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `crypto` in `catalog.py`; scorer `f_crypto` in `scorers.py`; edge card `FE30` in `edge_cards.py`

## Inputs

- `funding_z` (unit: z, max age 3600s, min quality 0.2)
- `open_interest_change_z` (unit: z, max age 3600s, min quality 0.2)
- `depth_drop_z` (unit: z, max age 300s, min quality 0.2)
- `onchain_flow_z` (unit: z, max age 86400s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_crypto(x: Mapping[str, float]) -> Signal:
    funding = abs(x["funding_z"])
    oi = abs(x["open_interest_change_z"])
    depth = max(0.0, x["depth_drop_z"])
    onchain = abs(x["onchain_flow_z"])
    logit = -0.65 + 0.35 * funding + 0.30 * oi + 0.45 * depth + 0.15 * onchain
    return _risk(logit, funding_extreme=funding, open_interest_change=oi, depth_drop=depth, onchain_flow=onchain)
```

Catalog formula note: REA synthesis: Crypto / crypto family; vendor report inventory is traceability, not validation.

## Assumptions

- Venue, custody, chain labels, and timestamps are distinct evidence fields.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Venue outage, depeg, liquidation-data gap, or on-chain label uncertainty.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE30
- **edge_source:** accuracy
- **novel_mechanism:** Rank venue-specific squeeze risk from funding extremes, open-interest change, depth loss, and absolute on-chain flow; cross-venue cascade propagation is outside this scorer.
- **target_definition:** One if a venue-specific liquidation/depth squeeze event occurs by the selected endpoint; otherwise zero.
- **price_aware_baseline:** Per-venue realized volatility, funding, and depth-only hazard without cross-venue propagation.
- **payer_hypothesis:** Hypothesis: market makers and collateral-constrained traders pay for early identification of forced-flow cascades.
- **scarcity_or_transfer:** Potential speed/access must survive venue-specific clocks and cannot be inferred from a pooled price feed.
- **bad_state:** Exchange outage, withdrawal freeze, depeg, mislabeled on-chain flow, or funding/mark-index divergence.
- **holdability_and_co_losses:** Measure venue custody, liquidation margin, cross-venue basis, and aggregate crypto co-loss before any position test.
- **execution_net:** Price each venue separately with fees, funding, liquidation, withdrawal, and latency; no atomicity assumption.
- **decisive_test:** Replay venue-synchronized events; compare to single-venue depth/funding baselines with incident-blocked holdouts.
- **kill_rule:** Kill if event lineage or venue clock is uncertain, or cascade forecasts do not beat the single-venue baseline.
- **source_refs:** ('research/rea_teardowns/targets/nansen.md', 'research/rea_teardowns/targets/arkham-intelligence.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
