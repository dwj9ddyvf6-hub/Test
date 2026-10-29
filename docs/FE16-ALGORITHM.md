Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE16 - Options-flow response with intent uncertainty - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE16; it does not duplicate the shared code.
- **Family:** Options
- **Target:** underlying response conditional on flow (target unit: forward_return_fraction)
- **Horizon:** intraday-5 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** EXPERIMENTAL
- **Formula key:** `options_flow` in `catalog.py`; scorer `f_options_flow` in `scorers.py`; edge card `FE16` in `edge_cards.py`

## Inputs

- `customer_signed_delta_flow_z` (unit: z, max age 3600s, min quality 0.2)
- `sweep_quality` (unit: ratio, max age 3600s, min quality 0.2, range (0.0, 1.0))
- `open_close_confidence` (unit: ratio, max age 3600s, min quality 0.2, range (0.0, 1.0))
- `aggressor_side_confidence` (unit: ratio, max age 3600s, min quality 0.2, range (0.0, 1.0))
- `quote_condition_quality` (unit: ratio, max age 3600s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_options_flow(x: Mapping[str, float]) -> Signal:
    sweep = _clip(x["sweep_quality"], 0.0, 1.0)
    intent = _clip(x["open_close_confidence"], 0.0, 1.0)
    aggressor = _clip(x["aggressor_side_confidence"], 0.0, 1.0)
    quote_quality = _clip(x["quote_condition_quality"], 0.0, 1.0)
    score = x["customer_signed_delta_flow_z"] * sweep * intent * aggressor * quote_quality
    return _signed(score, sweep_quality=sweep, open_close_confidence=intent,
                   aggressor_side_confidence=aggressor, quote_quality=quote_quality)
```

Catalog formula note: REA synthesis: Options / options_flow family; vendor report inventory is traceability, not validation.

## Assumptions

- customer_signed_delta_flow_z is signed by aggressor-initiated customer delta-equivalent flow (positive means net bullish delta demand); call/put volume imbalance alone cannot establish buyer/seller initiation or direction. Open/close, aggressor-side, sweep, and quote-quality confidences each lie in [0, 1].
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Intent classifier drift, weak aggressor-side confidence, quote condition ambiguity, or non-independent confirmation.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE16
- **edge_source:** accuracy
- **novel_mechanism:** Use as-of confidence over open/close, aggressor side, sweep, and quote condition to forecast the subsequent underlying response; confirmation is an outcome, never an input.
- **target_definition:** Underlying residual return from the classified flow event to the selected fixed endpoint.
- **price_aware_baseline:** Underlying momentum, contemporaneous quote/mid, and a no-intent baseline.
- **payer_hypothesis:** Hypothesis: slower analysts pay for correctly classified flow that is not already reflected in the underlying.
- **scarcity_or_transfer:** Information advantage must survive quote-condition uncertainty and shared-vendor tape dependence.
- **bad_state:** Closing trades, spreads crossing stale NBBO, multi-leg prints, and systematic flag drift.
- **holdability_and_co_losses:** Co-loss with dealer-gamma, tail, and cross-venue flow sleeves; never count multiple vendor labels as independent.
- **execution_net:** Use actual consolidated quote at event time, spread, delay capture, and next executable mark.
- **decisive_test:** Reclassify a frozen sample with quote context; compare to price-only baseline and count source-lineage clusters once.
- **kill_rule:** Kill if intent posterior is uncalibrated or flow adds no incremental net forecast value.
- **source_refs:** ('research/rea_teardowns/targets/cheddar-flow.md', 'research/rea_teardowns/targets/unusual-whales-original.md', 'research/rea_teardowns/targets/trade-echo.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
