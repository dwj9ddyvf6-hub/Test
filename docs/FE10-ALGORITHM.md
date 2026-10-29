Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE10 - Volatility and correlation regime transition - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE10; it does not duplicate the shared code.
- **Family:** Regime
- **Target:** regime-change risk (target unit: binary_regime_change)
- **Horizon:** 5-20 sessions
- **Forecast unit:** risk_score_heuristic
- **Score kind:** risk (uncalibrated_risk_rank_only)
- **Maturity:** EXPERIMENTAL
- **Formula key:** `regime` in `catalog.py`; scorer `f_regime` in `scorers.py`; edge card `FE10` in `edge_cards.py`

## Inputs

- `change_point_score` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))
- `vol_of_vol_z` (unit: z, max age 172800s, min quality 0.2)
- `cross_asset_dispersion_z` (unit: z, max age 172800s, min quality 0.2)
- `correlation_shift_z` (unit: z, max age 172800s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_regime(x: Mapping[str, float]) -> Signal:
    logit = -0.40 + 1.10 * _clip(x["change_point_score"], 0.0, 1.0) + 0.30 * abs(x["vol_of_vol_z"]) + 0.25 * abs(x["cross_asset_dispersion_z"]) + 0.30 * abs(x["correlation_shift_z"])
    return _risk(logit, change_point_score=x["change_point_score"], vol_of_vol_z=x["vol_of_vol_z"], correlation_shift_z=x["correlation_shift_z"])
```

Catalog formula note: REA synthesis: Regime / regime family; vendor report inventory is traceability, not validation.

## Assumptions

- Transition score is not a calibrated probability.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Feature revisions or repeated regime flips make transition state indeterminate.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE10
- **edge_source:** accuracy
- **novel_mechanism:** Rank near-term regime-change risk from change-point evidence, vol-of-vol, cross-asset dispersion, and correlation shifts without assigning transition direction.
- **target_definition:** One if the predeclared volatility/correlation regime transition occurs by the selected window end; otherwise zero.
- **price_aware_baseline:** Fixed rolling-vol/correlation threshold and current regime persistence.
- **payer_hypothesis:** Hypothesis: risk-budget committees pay for earlier evidence that diversification is about to fail.
- **scarcity_or_transfer:** Potential accuracy is warning lead time beyond a static threshold; no market-access claim.
- **bad_state:** False transition alarms, clustered shocks, or repeated state flips.
- **holdability_and_co_losses:** Measure margin and joint book losses in transition states; volatility, options, and trend sleeves co-load.
- **execution_net:** Measure alert value as avoided loss net of de-risk turnover, hedge cost, and whipsaw.
- **decisive_test:** Freeze the binary transition criterion and horizon; compare event ranking and false-alarm burden to fixed rolling-volatility/correlation thresholds. Score transition direction separately.
- **kill_rule:** Retire if warning lead vanishes after false alarms and transaction costs or is driven by one crisis.
- **source_refs:** ('research/rea_teardowns/targets/squeezemetrics.md', 'research/rea_teardowns/targets/spotgamma.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
