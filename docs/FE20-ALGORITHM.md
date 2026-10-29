Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE20 - Alternative-data nowcast with panel-drift control - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE20; it does not duplicate the shared code.
- **Family:** Alternative data
- **Target:** fundamental surprise (target unit: fundamental_surprise_z)
- **Horizon:** 1-3 months
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** EXPERIMENTAL
- **Formula key:** `altdata` in `catalog.py`; scorer `f_altdata` in `scorers.py`; edge card `FE20` in `edge_cards.py`

## Inputs

- `panel_surprise_z` (unit: z, max age 3024000s, min quality 0.2)
- `panel_stability` (unit: ratio, max age 3024000s, min quality 0.2, range (0.0, 1.0))
- `panel_coverage` (unit: ratio, max age 3024000s, min quality 0.2, range (0.0, 1.0))
- `panel_drift_z` (unit: z, max age 3024000s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_altdata(x: Mapping[str, float]) -> Signal:
    stability = _clip(x["panel_stability"], 0.0, 1.0)
    coverage = _clip(x["panel_coverage"], 0.0, 1.0)
    reliability = stability * coverage / (1.0 + abs(x["panel_drift_z"]))
    return _signed(x["panel_surprise_z"] * reliability,
                   panel_reliability=reliability, panel_drift_z=x["panel_drift_z"])
```

Catalog formula note: REA synthesis: Alternative data / altdata family; vendor report inventory is traceability, not validation.

## Assumptions

- Source labels and use rights are approved; panel drift is measurable; source-specific release cadence is documented.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Coverage/selection drift, unclear rights, or source/model revision.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE20
- **edge_source:** access
- **novel_mechanism:** Forecast the panel's own sampling error: distinguish real activity change from who entered, disappeared, or changed reporting behavior in the alternative-data panel.
- **target_definition:** Next-period fundamental surprise z-score using the frozen consensus vintage and standardization population.
- **price_aware_baseline:** Public company fundamentals, price, sector, and a no-panel-change base model.
- **payer_hypothesis:** Hypothesis: data users pay for timely nonpublic-but-authorized measurements with demonstrably stable coverage.
- **scarcity_or_transfer:** Access is only present if rights permit the use and the panel's lead survives public price/fundamental baselines.
- **bad_state:** Provider methodology change, participant churn, coverage drift, privacy/rights restriction, or survivorship.
- **holdability_and_co_losses:** Measure vendor concentration and common panel exposure across sleeves; do not count derived vendor panels as independent.
- **execution_net:** Net any later value against subscription, ingestion, storage, and execution latency.
- **decisive_test:** Freeze covered entities and panel vintages; test incremental forecast value after price, sector, and release-date controls.
- **kill_rule:** Kill on unclear rights, unstable panel lineage, or no incremental out-of-sample value.
- **source_refs:** ('research/rea_teardowns/targets/altindex.md', 'research/rea_teardowns/targets/danelfin.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
