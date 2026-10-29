Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE13 - Order-flow-imbalance adverse selection - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE13; it does not duplicate the shared code.
- **Family:** Microstructure
- **Target:** short-horizon price pressure (target unit: forward_return_fraction)
- **Horizon:** seconds-30 minutes
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `ofi` in `catalog.py`; scorer `f_ofi` in `scorers.py`; edge card `FE13` in `edge_cards.py`

## Inputs

- `ofi_z` (unit: z, max age 30s, min quality 0.2)
- `depth_z` (unit: z, max age 30s, min quality 0.2)
- `depth_replenishment_ratio` (unit: ratio, max age 30s, min quality 0.2, range (0.0, 1.0))
- `historical_post_fill_drift_z` (unit: z, max age 30s, min quality 0.2)
- `trade_condition_quality` (unit: ratio, max age 30s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_ofi(x: Mapping[str, float]) -> Signal:
    quality = _clip(x["trade_condition_quality"], 0.0, 1.0)
    depth = max(0.0, x["depth_z"])
    replenishment = _clip(x["depth_replenishment_ratio"], 0.0, 1.0)
    replenishment_damp = 1.0 - 0.65 * replenishment
    score = ((0.65 * x["ofi_z"] + 0.35 * x["historical_post_fill_drift_z"])
             * quality * replenishment_damp / (1.0 + 0.25 * depth))
    return _signed(score, quality=quality, normalized_depth=depth,
                   replenishment=replenishment, replenishment_damp=replenishment_damp,
                   historical_post_fill_drift_z=x["historical_post_fill_drift_z"])
```

Catalog formula note: REA synthesis: Microstructure / ofi family; vendor report inventory is traceability, not validation.

## Assumptions

- Positive OFI and historical markout mean upward pressure; visible depth replenishment is a [0, 1] fraction and attenuates that pressure. Historical post-fill drift must use only fills completed and markouts available before as_of; never use the candidate signal's future fill/markout.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Quote/trade clock misalignment, low condition coverage, or markout timestamp after as_of.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE13
- **edge_source:** accuracy
- **novel_mechanism:** Blend normalized order-flow imbalance with only pre-as-of historical post-fill drift, then attenuate it for visible depth and depth replenishment.
- **target_definition:** Midquote return from the first eligible post-signal quote to the selected fixed elapsed-time endpoint.
- **price_aware_baseline:** Depth-normalized OFI, historical prior-fill drift, and a no-OFI price baseline.
- **payer_hypothesis:** Hypothesis: passive liquidity providers pay to avoid adverse selection from informed aggressors.
- **scarcity_or_transfer:** Negative-selection avoidance is the edge claim; raw trade direction or flow volume is not intent.
- **bad_state:** Quote/trade timestamp mismatch, hidden liquidity, venue mix shift, or high toxicity.
- **holdability_and_co_losses:** Include fill-conditioned co-loss with market-making and options-flow positions.
- **execution_net:** Use realized post-fill markouts at 1s/1m/5m and real queue/fill assumptions; do not credit unfilled quote edge.
- **decisive_test:** Use same-clock quote/trade windows; score the fixed-endpoint midquote return and compare OFI-only with replenishment-adjusted forecasts on a locked cohort. Keep execution markouts separate.
- **kill_rule:** Kill if fixed-endpoint midquote-return forecasts do not improve over OFI-only or quote/trade clock uncertainty exceeds the capture interval.
- **source_refs:** ('research/rea_teardowns/targets/quant-data.md', 'research/rea_teardowns/targets/cheddar-flow.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
