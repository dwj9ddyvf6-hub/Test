Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE21 - XBRL cash-conversion inflection - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE21; it does not duplicate the shared code.
- **Family:** Fundamentals
- **Target:** cash-conversion change (target unit: cash_flow_quality_change_z)
- **Horizon:** 1-4 quarters
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `xbrl` in `catalog.py`; scorer `f_xbrl` in `scorers.py`; edge card `FE21` in `edge_cards.py`

## Inputs

- `cash_conversion_z` (unit: z, max age 15552000s, min quality 0.2)
- `receivables_growth_gap_z` (unit: z, max age 15552000s, min quality 0.2)
- `deferred_revenue_change_z` (unit: z, max age 15552000s, min quality 0.2)
- `fcf_acceleration_z` (unit: z, max age 15552000s, min quality 0.2)

## Scoring rule (verbatim scorer source)

```python
def f_xbrl(x: Mapping[str, float]) -> Signal:
    acceleration = 0.35 * x["cash_conversion_z"] + 0.20 * x["fcf_acceleration_z"] + 0.25 * x["deferred_revenue_change_z"] - 0.20 * x["receivables_growth_gap_z"]
    return _signed(acceleration, cash_conversion_z=x["cash_conversion_z"], receivables_growth_gap_z=x["receivables_growth_gap_z"], fcf_acceleration_z=x["fcf_acceleration_z"])
```

Catalog formula note: REA synthesis: Fundamentals / xbrl family; vendor report inventory is traceability, not validation.

## Assumptions

- Use filing acceptance/available timestamps, accession IDs, period-end timestamps, and restatement handling.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Amendment/restatement ambiguity, taxonomy mapping break, or non-comparable period.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE21
- **edge_source:** accuracy
- **novel_mechanism:** Combine the declared cash-conversion, receivables-gap, deferred-revenue, and free-cash-flow features into a directional cash-quality change score.
- **target_definition:** Change in cash-conversion measure between the frozen accession vintage and the next comparable filing.
- **price_aware_baseline:** Prior cash conversion, sector seasonality, and a simple cash-flow trend baseline.
- **payer_hypothesis:** Hypothesis: investors with stale accounting screens pay for earlier detection of cash-quality deterioration.
- **scarcity_or_transfer:** Potential accuracy comes from reconstructing filing facts sooner or mapping them better, not from ratios already in price.
- **bad_state:** Restatement, taxonomy change, fiscal-period mismatch, acquisition, or unusual working-capital seasonality.
- **holdability_and_co_losses:** Issuer concentration and sector accounting conventions; no claim that a low ratio implies return direction.
- **execution_net:** For any later equity test, next-open marks, spread, liquidity tier, and short/borrow cost.
- **decisive_test:** Use accession IDs and filing availability; compare the declared four-feature cash-conversion score to lagged cash-flow and sector baselines.
- **kill_rule:** Kill if restatement handling or period alignment fails, or if the next-vintage target is not better predicted.
- **source_refs:** ('research/rea_teardowns/targets/finviz-screener.md', 'research/rea_teardowns/targets/stock-rover.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
