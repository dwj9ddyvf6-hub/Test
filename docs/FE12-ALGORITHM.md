Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE12 - Liquidity fragility / halt hazard - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE12; it does not duplicate the shared code.
- **Family:** Microstructure
- **Target:** liquidity deterioration (target unit: binary_liquidity_event)
- **Horizon:** intraday-1 session
- **Forecast unit:** risk_score_heuristic
- **Score kind:** risk (uncalibrated_risk_rank_only)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `liquidity` in `catalog.py`; scorer `f_liquidity` in `scorers.py`; edge card `FE12` in `edge_cards.py`

## Inputs

- `spread_z` (unit: z, max age 300s, min quality 0.2)
- `depth_drop_z` (unit: z, max age 300s, min quality 0.2)
- `realized_vol_z` (unit: z, max age 300s, min quality 0.2)
- `volume_concentration` (unit: ratio, max age 300s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_liquidity(x: Mapping[str, float]) -> Signal:
    logit = -1.00 + 0.50 * max(0.0, x["spread_z"]) + 0.50 * max(0.0, x["depth_drop_z"]) + 0.35 * max(0.0, x["realized_vol_z"]) + 0.30 * _clip(x["volume_concentration"], 0.0, 1.0)
    return _risk(logit, spread_z=x["spread_z"], depth_drop_z=x["depth_drop_z"], realized_vol_z=x["realized_vol_z"])
```

Catalog formula note: REA synthesis: Microstructure / liquidity family; vendor report inventory is traceability, not validation.

## Assumptions

- Hazard score is a triage rank; venue/halt definitions must be fixed.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Feed outage, trading halt, or spread/depth units inconsistent across venues.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE12
- **edge_source:** accuracy
- **novel_mechanism:** Rank persistent liquidity impairment from spread widening, depth loss, realized volatility, and volume concentration; no recovery half-life is estimated by this scorer.
- **target_definition:** One if depth remains impaired or spread remains outside the predeclared band by the selected endpoint; otherwise zero.
- **price_aware_baseline:** Spread/depth levels, realized volatility, and volume concentration for the same instrument.
- **payer_hypothesis:** Hypothesis: liquidity demanders pay to avoid crossing into a fragile book.
- **scarcity_or_transfer:** Potential accuracy from recovery dynamics; access is not assumed unless a venue-specific advantage is measured.
- **bad_state:** Halts, limit states, stale quotes, hidden depth, and volatility shocks.
- **holdability_and_co_losses:** Assess exit liquidity for all sleeves holding the instrument; no position may assume the pre-shock depth.
- **execution_net:** Net avoided loss against the identical entry set, including spread widening, partial fills, and no-fill cost.
- **decisive_test:** Define the impaired-depth/spread event before cutoff; compare the composite rank from declared spread, depth, volatility, and concentration inputs to static thresholds.
- **kill_rule:** Kill if the binary impaired-depth/spread event rank does not beat static thresholds or produces excessive false alarms.
- **source_refs:** ('research/rea_teardowns/targets/quant-data.md', 'research/rea_teardowns/targets/cheddar-flow.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
