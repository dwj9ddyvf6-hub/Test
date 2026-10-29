Algorithm derived from the code on 2026-10-29 (source: Silicon branch codex/forecast-engines-2026-10-29, research/forecast_engines/).

# FE27 - Macro surprise reaction function by vintage - Algorithm

- **Origin track:** Created by Ausar (Codex track)
- **Package:** This engine's code is shared Lab code, shipped once in Test under `packages/ausar/forecast-engines-lab/` (files: `catalog.py`, `scorers.py`, `edge_cards.py`, `engine.py`, `cli.py`). This document is the per-engine algorithm record for FE27; it does not duplicate the shared code.
- **Family:** Macro/rates
- **Target:** cross-asset response (target unit: forward_return_fraction)
- **Horizon:** intraday-5 sessions
- **Forecast unit:** signed_score
- **Score kind:** signed (uncalibrated_signed_score_orientation)
- **Maturity:** CONDITIONAL-DATA
- **Formula key:** `macro` in `catalog.py`; scorer `f_macro` in `scorers.py`; edge card `FE27` in `edge_cards.py`

## Inputs

- `release_surprise_z` (unit: z, max age 172800s, min quality 0.2)
- `cycle_reaction_sign` (unit: signed_ratio, max age 172800s, min quality 0.2, range (-1.0, 1.0))
- `market_pricing_z` (unit: z, max age 172800s, min quality 0.2)
- `regime_confidence` (unit: ratio, max age 172800s, min quality 0.2, range (0.0, 1.0))

## Scoring rule (verbatim scorer source)

```python
def f_macro(x: Mapping[str, float]) -> Signal:
    regime = _clip(x["regime_confidence"], 0.0, 1.0)
    surprise = x["release_surprise_z"] - 0.35 * x["market_pricing_z"]
    reaction_sign = _clip(x["cycle_reaction_sign"], -1.0, 1.0)
    return _signed(surprise * reaction_sign * regime,
                   unpriced_surprise=surprise, cycle_reaction_sign=reaction_sign, regime_confidence=regime)
```

Catalog formula note: REA synthesis: Macro/rates / macro family; vendor report inventory is traceability, not validation.

## Assumptions

- Use ALFRED/release vintages and market pricing before the release. cycle_reaction_sign is bounded [-1, 1]: positive means a positive unpriced surprise lifts the target instrument, negative means it lowers it, and zero means no directional response is asserted.
- Output is a research estimate, not a calibrated probability or trade instruction.

## Kill conditions / abstention

- Revision/vintage mismatch, event-feed delay, or reaction function whipsaw.
- Any point-in-time, quality, rights, or provenance failure forces abstention.
## Edge card

- **engine_id:** FE27
- **edge_source:** accuracy
- **novel_mechanism:** Estimate the conditional reaction coefficient to macro surprise; the sign can flip with policy pricing, cycle state, and the exact release vintage.
- **target_definition:** Return of the declared cross-asset instrument from the first executable post-release mark to 30 minutes after release.
- **price_aware_baseline:** Surprise-only regression, market-implied policy path, and asset's own event history.
- **payer_hypothesis:** Hypothesis: macro hedgers pay for faster, better mapping from a release surprise into the current reaction function.
- **scarcity_or_transfer:** Speed matters only if consensus and release vintages are aligned and usable before the price response.
- **bad_state:** Revised release, policy shock, simultaneous headline, wrong consensus timestamp, or reaction sign whipsaw.
- **holdability_and_co_losses:** Duration, FX, credit, and equity positions can co-lose; test joint stress and funding needs.
- **execution_net:** Include event spread, slippage, fill latency, and delayed execution; no hypothetical release-time mid fills.
- **decisive_test:** Use release-by-release vintages; compare conditional reaction to a fixed surprise coefficient on untouched events.
- **kill_rule:** Kill if the sign is unstable out of sample or release/consensus clocks are not proven.
- **source_refs:** ('research/rea_teardowns/targets/finviz-screener.md', 'research/rea_teardowns/targets/market-chameleon.md')
- **status:** HYPOTHESIS

## Provenance

Parameters in the catalog are starter hypotheses, not fitted estimates (catalog module docstring). The catalog, scorers and edge cards were verified present in the fetched Lab source for this packaging pass: `catalog.py` defines the spec above, `scorers.py` contains its scorer, and `edge_cards.py` contains its edge card.
